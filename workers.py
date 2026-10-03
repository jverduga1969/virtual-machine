# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Hilos de trabajo (QThread) que hacen el trabajo pesado fuera de la UI:
construir y lanzar el comando de QEMU (InstallWorker), operaciones de
snapshot (SnapshotOperationWorker), y un worker genérico para llamadas
bloqueantes al Guest Agent u otras esperas con timeout (_BackgroundCallThread).

InstallWorker es, con diferencia, la pieza más grande y más probada de todo
el proyecto: arma el script bash completo (firmware, red, gráficos,
clipboard, carpetas compartidas, TPM) y lo ejecuta.
"""
import os
import re
import json
import shutil
import shlex
import glob
import subprocess
import uuid
import time
import threading
import configparser
from datetime import date, timedelta
import requests
from packaging import version
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer

from vm_config import load_vm_config
from iso_sources import get_latest_iso_url, get_latest_windows_iso_url
import iso_versions
import vm_paths  # portable_paths_v1
from network_utils import network_interface_exists, sanitize_tap_name
from host_deps import find_ovmf_files
from shared_folders import bash_squote, find_virtiofsd
from console_backend import (
    PROTOCOL_VNC, PROTOCOL_SPICE, MODE_EMBEDDED, MODE_EXTERNAL, MODE_NATIVE,
    MODE_HYBRID, MODE_HYBRID_GL,
    DEFAULT_PROTOCOL, DEFAULT_MODE, qemu_console_args, socket_path as _cb_socket_path,
)


class DownloadCancelled(Exception):
    """Cancelación voluntaria de una descarga."""


class InstallWorker(QThread):
    log_signal = pyqtSignal(str)
    # Progreso de descarga de medios de instalación (Windows/Linux).
    # -1 significa progreso indeterminado.
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(int)

    def _log_exc(self, e, context, level="AVISO"):
        """Deja rastro en la consola de una excepción que antes se descartaba
        en silencio (except Exception: pass). No relanza nada: solo informa,
        para que un fallo no quede invisible cuando algo salga mal."""
        try:
            self.log_signal.emit(f"[{level}] {context}: {e}")
        except Exception:
            pass

    def __init__(self, os_type, ram, cores, disk_size, disk_type, disk_format, disk_ext,
                 firmware, secure_boot, tpm, boot_device, network_model, audio_device, network_mode, network_interface, network_count, graphics_mode, graphics_vram, extra_params, vm_dir, disk_path, skip_disk_create=False, boot_order=None, network_devices=None, passthrough_devices=None):
        super().__init__()
        self._cancel_event = threading.Event()
        self.os_type = os_type
        self.ram = ram
        self.cores = cores
        self.disk_size = disk_size
        self.disk_type = disk_type
        self.disk_format = disk_format
        self.disk_ext = disk_ext
        self.firmware = firmware
        self.secure_boot = bool(secure_boot)
        self.tpm = bool(tpm)
        self.boot_device = boot_device
        self.boot_order = boot_order or ["cdrom", "disk", "network"]
        self.network_model = network_model or "virtio-net-pci"
        self.audio_device = audio_device or "intel-hda"
        self.network_mode = network_mode or "nat"
        self.network_interface = network_interface or ""
        try:
            self.network_count = max(1, min(4, int(network_count)))
        except (TypeError, ValueError):
            self.network_count = 1
        self.extra_params = extra_params or {}
        self.cpu_model = str(self.extra_params.get("cpu_model", "auto") or "auto")
        chipset = (self.extra_params or {}).get('chipset', 'pc')
        if self.secure_boot:
            # Secure Boot (OVMF) exige SMM, disponible solo en el chipset Q35 --
            # se fuerza sin importar lo elegido en el combo, para no dejar una
            # combinación inválida (i440fx + Secure Boot no arranca).
            chipset = "q35,smm=on"
        self.chipset_args = f"-machine {chipset}"
        self.vm_dir = vm_dir
        self.disk_path = disk_path
        self.skip_disk_create = skip_disk_create
        self.graphics_mode = graphics_mode or "auto"
        self.graphics_vram = graphics_vram or "256M"
        # Consola VNC embebida: cuando está activa, forzamos gráficos SIN
        # aceleración OpenGL (VNC no soporta GL) y QEMU usa -vnc unix:socket
        # como único backend de display.
        self.vnc_embedded = bool((self.extra_params or {}).get("vnc_embedded", True))
        # Nuevo modelo: protocolo (vnc/spice) x modo (embedded/external/native).
        # Se deriva del vnc_embedded legado si el usuario aún no lo tocó.
        self.console_protocol = str(
            (self.extra_params or {}).get("console_protocol")
            or DEFAULT_PROTOCOL
        ).lower()
        self.console_mode = str(
            (self.extra_params or {}).get("console_mode")
            or (MODE_EMBEDDED if self.vnc_embedded else MODE_NATIVE)
        ).lower()
        self.network_devices = network_devices if isinstance(network_devices, list) and network_devices else [{"name":"Red 1","model":self.network_model,"mode":self.network_mode,"interface":self.network_interface,"mac":""}]
        self.passthrough_devices = passthrough_devices if isinstance(passthrough_devices, list) else []
        self.shared_folders = (extra_params or {}).get("shared_folders", []) if isinstance((extra_params or {}).get("shared_folders", []), list) else []
        self._smb_share_host = ""
        self._smb_share_readonly = False

    def _cpu_args(self):
        if self.cpu_model.lower() in ("", "auto"):
            return "host"
        return self.cpu_model

    def _qemu_chardev_supports(self, chardev_name):
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            return False
        try:
            r = subprocess.run([qemu, "-chardev", "help"], capture_output=True, text=True, timeout=5)
            txt = (r.stdout or "") + "\n" + (r.stderr or "")
            return re.search(r"\b" + re.escape(chardev_name) + r"\b", txt) is not None
        except Exception:
            return False

    def _clipboard_enabled(self):
        cfg = (self.extra_params or {}).get("clipboard", {})
        if not isinstance(cfg, dict):
            return False
        return str(cfg.get("mode", "disabled")) != "disabled"

    def _clipboard_qemu_args(self):
        if not self._clipboard_enabled() or self.os_type == "macos":
            return "", ""
        if not self._qemu_chardev_supports("qemu-vdagent"):
            raise RuntimeError("Este QEMU no ofrece qemu-vdagent; no se puede activar el clipboard integrado.")
        return (
            '-chardev qemu-vdagent,id=vdagent0,name=vdagent,clipboard=on,mouse=off '
            '-device virtio-serial -device virtserialport,chardev=vdagent0,name=com.redhat.spice.0',
            "Clipboard: QEMU vdagent activo (bidireccional). El guest necesita spice-vdagent/SPICE Guest Tools."
        )

    def _qemu_supports_audiodev(self, backend_name):
        """¿QEMU del host soporta el backend -audiodev <backend_name>?

        Se consulta una sola vez por backend y se guarda en una caché
        a nivel de instancia (`self._audiodev_cache`) para no pagar el
        coste de `-audiodev help` en cada arranque.
        """
        cache = getattr(self, "_audiodev_cache", None)
        if cache is None:
            cache = {}
            self._audiodev_cache = cache
        if backend_name in cache:
            return cache[backend_name]
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            cache[backend_name] = False
            return False
        try:
            r = subprocess.run(
                [qemu, "-audiodev", "help"],
                capture_output=True, text=True, timeout=5,
            )
            txt = (r.stdout or "") + "\n" + (r.stderr or "")
            # La salida es una lista de nombres válidos; basta con
            # buscar el backend como palabra suelta.
            ok_ = re.search(
                r"\b" + re.escape(backend_name) + r"\b", txt
            ) is not None
            cache[backend_name] = ok_
            return ok_
        except Exception:
            cache[backend_name] = False
            return False

    def _detect_audio_backend(self):
        """Elige el mejor backend de audio disponible en el host.

        Marcador: audio_pipewire_v1

        Orden de preferencia:
          1. PipeWire nativo (QEMU >= 7 y pipewire en el host).
          2. PulseAudio (o pipewire-pulse, que responde a pactl).
          3. ALSA (/dev/snd).

        La elección se valida contra `qemu-system-x86_64 -audiodev help`
        para no mandar a QEMU un backend que no conoce. Devuelve el
        nombre del backend o None si no hay ninguno disponible.
        """
        # 1) PipeWire nativo.
        if self._qemu_supports_audiodev("pipewire") and shutil.which("pipewire"):
            # Comprobación rápida: pw-cli info 0 responde solo si el
            # servidor PipeWire del usuario está corriendo.
            if shutil.which("pw-cli"):
                try:
                    r = subprocess.run(
                        ["pw-cli", "info", "0"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                    )
                    if r.returncode == 0:
                        return "pipewire"
                except Exception:
                    pass
            else:
                # Sin pw-cli no podemos verificar; confiamos en pipewire.
                return "pipewire"

        # 2) PulseAudio (pactl funciona también con pipewire-pulse).
        if self._qemu_supports_audiodev("pa") and shutil.which("pactl"):
            try:
                r = subprocess.run(
                    ["pactl", "info"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
                if r.returncode == 0:
                    return "pa"
            except Exception:
                pass

        # 3) ALSA.
        if (self._qemu_supports_audiodev("alsa")
                and (shutil.which("aplay") or os.path.exists("/dev/snd"))):
            return "alsa"

        return None

    def _audio_args(self):
        """Crea la tarjeta de sonido QEMU con el mejor backend del host.

        Marcador: audio_pipewire_v1

        Preferencia de backend: PipeWire → PulseAudio → ALSA.
        El combo de la UI sigue eligiendo el MODELO de tarjeta
        (intel-hda / ac97 / sb16 / none); el backend es transparente
        y solo se refleja en el log.
        """
        backend = self._detect_audio_backend()
        if backend is None:
            raise RuntimeError(
                "No se encontró un backend de audio utilizable. "
                "Se necesita PipeWire (pipewire+pw-cli), PulseAudio "
                "(pactl) o ALSA (/dev/snd) en el host, y que el QEMU "
                "instalado anuncie el backend correspondiente en "
                "'-audiodev help'."
            )
        if self.audio_device in ("none", "off", "disabled"):
            return "none", ""
        device_map = {
            "intel-hda": "-device intel-hda -device hda-duplex,audiodev=audio0",
            "ac97": "-device AC97,audiodev=audio0",
            "sb16": "-device sb16,audiodev=audio0",
        }
        device_args = device_map.get(self.audio_device, device_map["intel-hda"])
        if backend == "pipewire":
            return "pipewire", f"-audiodev pipewire,id=audio0 {device_args}"
        if backend == "pa":
            return "pa", f"-audiodev pa,id=audio0 {device_args}"
        return "alsa", f"-audiodev alsa,id=audio0 {device_args}"

    def _qemu_supports(self, device_name):
        """Comprueba de forma segura si el QEMU del host conoce un dispositivo."""
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            return False
        try:
            r = subprocess.run([qemu, "-device", "help"], capture_output=True, text=True, timeout=5)
            return r.returncode == 0 and device_name in r.stdout
        except Exception:
            return False

    def _virgl_available(self):
        """Detecta virglrenderer sin asumir una ruta concreta de la distribución."""
        if shutil.which("ldconfig"):
            try:
                r = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True, timeout=5)
                if "libvirglrenderer" in r.stdout:
                    return True
            except Exception:
                pass
        for root in ("/usr/lib", "/usr/lib64", "/lib", "/lib64"):
            if os.path.isdir(root):
                try:
                    for name in os.listdir(root):
                        if name.startswith("libvirglrenderer") and ".so" in name:
                            return True
                except Exception:
                    pass
        return False

    def _display_opengl_args(self):
        """Devuelve un backend de pantalla con OpenGL activado si QEMU lo ofrece.

        virtio-gpu-gl necesita que el backend de display de QEMU tenga GL=on;
        detectar solo libvirglrenderer no es suficiente.
        """
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            return "", False
        try:
            r = subprocess.run([qemu, "-display", "help"], capture_output=True, text=True, timeout=5)
            text = (r.stdout or "") + (r.stderr or "")
            # GTK y SDL son los backends gráficos más comunes. QEMU documenta
            # gl=on para ambos; preferimos GTK cuando está disponible.
            if re.search(r"\bgtk\b", text, re.IGNORECASE):
                return "-display gtk,gl=on", True
            if re.search(r"\bsdl\b", text, re.IGNORECASE):
                return "-display sdl,gl=on", True
        except Exception:
            pass
        return "", False

    def _graphics_args(self):
        """Selecciona gráficos seguros según SO, QEMU y capacidades del host."""
        # Modo compatibilidad de snapshots (marcador snapshot_compat_v1):
        # red de seguridad por si el .ini trae VirGL/Venus con el flag
        # activo (editado a mano o de una versión anterior). La UI ya
        # los deshabilita, pero aquí forzamos 2D para garantizar que
        # savevm/snapshot-save funcionen.
        if bool((self.extra_params or {}).get("snapshot_compat")) \
                and self.graphics_mode in ("virgl", "venus"):
            self.log_signal.emit(
                "==> Modo compatibilidad de snapshots: se ignora "
                f"'{self.graphics_mode}' y se usa VirtIO-GPU 2D "
                "(la GPU del host impide snapshots completos)."
            )
            self.graphics_mode = "virtio"

        if self.os_type == "macos":
            return "", "macOS/OpenCore: gráficos gestionados por OSX-KVM"

        if self.graphics_mode in ("none", "off", "disabled"):
            return "-display none -vga none", "Sin video (headless)"

        # VNC embedded: cuando está activo, forzamos gráficos sin GL.
        # VNC no soporta contextos OpenGL, así que un backend con GL fallaría
        # con "Display vnc is incompatible with the GL context".
        # Forzamos el modo 'virtio' (VGA compatible, sin GL) si el usuario
        # tenía seleccionado uno de los modos GL incompatibles.
        # Cuando la consola usa VNC o SPICE (embedded o external), no
        # queremos que QEMU abra una ventana local ni use GL: el
        # display server es el socket, y GL obliga a -display gtk/sdl,
        # que entra en conflicto con -display none.
        # VNC y SPICE exponen la pantalla por socket/puerto y obligan
        # a -display none. VirGL y Venus necesitan un backend con
        # gl=on, así que son incompatibles con cualquiera de estos
        # modos (embedded, external, hybrid).
        _console_uses_socket = self.console_mode in (
            MODE_EMBEDDED, MODE_EXTERNAL, MODE_HYBRID,
        )
        # Híbrida 3D: el widget VNC sigue embebido (2D), pero la
        # ventana GL propia de QEMU se encarga del render 3D. En
        # este modo NO se rebaja graphics_mode a virtio: necesitamos
        # VirGL/Venus activos para que la ventana GL sirva de algo.
        _is_hybrid_gl = (self.console_mode == MODE_HYBRID_GL)
        # Windows con graphics_mode="auto" resuelve a VGA std (no
        # GL), así que no hay conflicto con -display none: no lo
        # rebajamos a virtio.
        _is_windows_auto = (
            self.os_type == "windows" and self.graphics_mode == "auto"
        )
        if (_console_uses_socket and not _is_windows_auto
                and self.graphics_mode in ("virgl", "venus", "auto")):
            self.log_signal.emit(
                f"==> Consola {self.console_protocol.upper()} ({self.console_mode}): "
                "sin aceleración OpenGL y sin ventana local de QEMU."
            )
            self.graphics_mode = "virtio"
        elif _is_hybrid_gl and self.graphics_mode in ("virgl", "venus", "auto"):
            self.log_signal.emit(
                "==> Híbrida 3D: el widget VNC muestra la VM en 2D; "
                "la ventana GL de QEMU mostrará el render 3D "
                "(VirGL/Venus). El 3D NO se ve dentro de la app."
            )

        # hostmem es una ventana de memoria del dispositivo, no VRAM clásica.
        try:
            raw = str(self.graphics_vram).strip().upper()
            if not re.fullmatch(r"\d+[MG]", raw):
                raw = "256M"
            n = int(raw[:-1])
            unit = raw[-1]
            hostmem = max(256, n) if unit == "M" else max(256, n * 1024)
            hostmem = f"{hostmem}M"
        except Exception:
            hostmem = "256M"

        mode = self.graphics_mode or "auto"
        clipboard_on = self._clipboard_enabled() and self.os_type in ("linux", "windows")
        display_gl_args, display_gl_ok = self._display_opengl_args()
        if clipboard_on:
            if display_gl_args.startswith("-display gtk"):
                display_gl_args = re.sub(r"-display gtk(?:,([^ ]+))?", lambda m: "-display gtk," + ((m.group(1) + ",") if m.group(1) else "") + "clipboard=on", display_gl_args, count=1)
            else:
                display_gl_args = "-display gtk,clipboard=on"
                display_gl_ok = True
        virgl_ok = (self._qemu_supports("virtio-vga-gl") and
                    self._virgl_available() and display_gl_ok)
        # Venus is an optional Vulkan path. Do not expose it as usable merely
        # because virglrenderer exists: the host also needs a working Vulkan
        # stack. The stable automatic mode remains VirGL/OpenGL.
        host_vulkan_ok = bool(shutil.which("vulkaninfo"))
        if host_vulkan_ok:
            try:
                vr = subprocess.run(["vulkaninfo", "--summary"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7)
                host_vulkan_ok = vr.returncode == 0
            except Exception:
                host_vulkan_ok = False
        venus_ok = virgl_ok and host_vulkan_ok
        virtio_ok = self._qemu_supports("virtio-vga")

        # Windows: priorizamos un VGA estándar porque funciona sin instalar drivers VirtIO.
        if self.os_type == "windows" and mode == "auto":
            return (f"{display_gl_args} -vga std" if clipboard_on else "-vga std"), "Windows: VGA estándar (máxima compatibilidad)"

        # Android-x86 9.0 (kernel 4.9) no trae driver VirtIO-GPU: al arrancar
        # se queda en "Detecting Android-x86..." y cae a un shell de
        # rescate (console:/ #). Red Hat QXL 2D funciona en todas las
        # versiones de Android-x86 / Bliss OS probadas. El usuario que
        # sepa que su ISO usa kernel 5.10+ (o Bliss OS 15+) puede elegir
        # VirtIO-GPU 2D explícitamente; ver _update_graphics_compat_hint.
        if self.os_type == "android" and mode == "auto":
            if self._qemu_supports("qxl"):
                return "-vga qxl", "Android: Red Hat QXL 2D (recomendado)"
            return "-vga std", "Android: VGA estándar (QXL no disponible)"

        if mode == "virgl" and virgl_ok:
            extra = ""
            return f"{display_gl_args} -device virtio-vga-gl,hostmem={hostmem},blob=true{extra}".strip(), (
                "VirtIO-GPU + VirGL 3D (OpenGL host)"
            )

        if mode == "venus" and venus_ok:
            extra = ",venus=true"
            return f"{display_gl_args} -device virtio-vga-gl,hostmem={hostmem},blob=true{extra}".strip(), "VirtIO-GPU + Venus/Vulkan 3D"

        if mode in ("virgl", "venus") and not (virgl_ok if mode == "virgl" else venus_ok):
            if mode == "venus" and virgl_ok and not venus_ok:
                self.log_signal.emit("==> VirGL está disponible, pero Vulkan del host no está disponible; se usa VirGL/OpenGL o VirtIO-GPU 2D.")
            elif self._virgl_available() and not display_gl_ok:
                self.log_signal.emit("==> VirGL está instalado, pero QEMU no ofrece un backend de pantalla con OpenGL activo; se usa un modo gráfico compatible.")
            else:
                self.log_signal.emit("==> Aceleración 3D solicitada pero no disponible; se usa un modo gráfico compatible.")

        if mode == "auto" and self.os_type == "linux":
            if virgl_ok:
                return f"{display_gl_args} -device virtio-vga-gl,hostmem={hostmem},blob=true".strip(), "VirtIO-GPU + VirGL 3D (OpenGL host)"
            if virtio_ok:
                return (f"{display_gl_args} -device virtio-vga" if clipboard_on else "-device virtio-vga"), "VirtIO-GPU 2D"
            return (display_gl_args if clipboard_on else ""), "QEMU VGA estándar"

        if mode == "qxl":
            if self.firmware == "uefi":
                self.log_signal.emit(
                    "[AVISO] QXL con firmware UEFI puede no mostrar nada durante el arranque "
                    "(OVMF no siempre trae driver GOP para QXL). Si la pantalla queda en negro, "
                    "prueba 'Automático' o 'VirtIO-GPU 2D'."
                )
            if self._qemu_supports("qxl"):
                return (f"{display_gl_args} -vga qxl" if clipboard_on else "-vga qxl"), "Red Hat QXL 2D (sin 3D; snapshot compatible)"
            return "-vga std", "QXL no disponible; VGA estándar"

        if mode in ("vmware", "vmware-svga"):
            if self.firmware == "uefi":
                self.log_signal.emit(
                    "[AVISO] VMware SVGA con firmware UEFI puede no mostrar nada durante el arranque "
                    "(OVMF no siempre trae driver GOP para este dispositivo). Si la pantalla queda en negro, "
                    "prueba 'Automático' o 'VirtIO-GPU 2D'."
                )
            # QEMU expone este dispositivo como VMware SVGA II compatible.
            return (f"{display_gl_args} -vga vmware" if clipboard_on else "-vga vmware"), "VMware SVGA II compatible (sin 3D acelerado; snapshot compatible)"

        if mode == "virtio":
            if virtio_ok:
                return "-device virtio-vga", "VirtIO-GPU 2D (VGA compatible)"
            return "", "QEMU VGA estándar (VirtIO-GPU no disponible)"

        if mode == "auto":
            if virgl_ok:
                return f"{display_gl_args} -device virtio-vga-gl,hostmem={hostmem},blob=true".strip(), "VirtIO-GPU + VirGL 3D (OpenGL host)"
            if virtio_ok:
                return "-device virtio-vga", "VirtIO-GPU 2D (VGA compatible)"
            return "", "QEMU VGA estándar"

        # Fallback universal: dejar que QEMU use su VGA por defecto.
        return "", "QEMU VGA estándar"

    def _uefi_args(self):
        if self.firmware != "uefi":
            return ""
        code, vars_template = find_ovmf_files(secure_boot=self.secure_boot)
        if not code or not vars_template:
            mode = "Secure Boot" if self.secure_boot else "UEFI"
            if not self.secure_boot:
                raise RuntimeError(
                    f"No se encontró OVMF compatible con {mode}. "
                    "Se revisaron las rutas del sistema y la carpeta OSX-KVM."
                )
            raise RuntimeError(
                "No se encontró una plantilla OVMF con Secure Boot. "
                "Instala el firmware OVMF/edk2-ovmf con soporte Secure Boot."
            )
        vars_path = os.path.join(self.vm_dir, "OVMF_VARS.fd")
        if not os.path.isfile(vars_path):
            shutil.copy2(vars_template, vars_path)
        if self.secure_boot:
            # Secure Boot de OVMF requiere SMM/Q35 (ya forzado en self.chipset_args).
            # Además, el CODE seguro debe arrancar como firmware de solo lectura y
            # el VARS ser propio de la VM.
            return (
                f'-global driver=cfi.pflash01,property=secure,value=on '
                f'-drive if=pflash,format=raw,readonly=on,file="{code}" '
                f'-drive if=pflash,format=raw,file="{vars_path}"'
            )
        return f'-drive if=pflash,format=raw,readonly=on,file="{code}" -drive if=pflash,format=raw,file="{vars_path}"'

    def _tpm_args(self):
        if not self.tpm:
            return "", ""
        if shutil.which("swtpm") is None:
            raise RuntimeError("Se solicitó TPM 2.0, pero 'swtpm' no está instalado. Instálalo con el paquete swtpm de tu distribución.")
        tpm_dir = os.path.join(self.vm_dir, "swtpm")
        socket_path = os.path.join(self.vm_dir, "swtpm.sock")
        os.makedirs(tpm_dir, exist_ok=True)
        try:
            if os.path.exists(socket_path):
                os.remove(socket_path)
        except OSError:
            pass
        tpm_cmd = f'swtpm socket --tpm2 --tpmstate dir="{tpm_dir}" --ctrl type=unixio,path="{socket_path}" --daemon'
        qemu_tpm = f'-chardev socket,id=chrtpm,path="{socket_path}" -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0'
        return tpm_cmd, qemu_tpm

    def _network_model_for_guest(self):
        # macOS suele tener mejor compatibilidad con el modelo Intel e1000-82545em.
        if self.os_type == "macos" and self.network_model == "e1000":
            return "e1000-82545em"
        return self.network_model

    def _insert_pre_qmp_args(self, script_content, pre_qmp):
        """Inserta argumentos extra de QEMU (VirtioFS, Guest Agent) justo antes
        de '-qmp unix:' en el script generado. Devuelve (script, encontrado):
        si el marcador no existe (el template cambió de formato), encontrado
        es False y el llamador decide cómo abortar en vez de continuar con un
        comando de QEMU incompleto en silencio."""
        marker = "    -qmp unix:"
        if marker not in script_content:
            return script_content, False
        return script_content.replace(marker, "    " + pre_qmp + " -qmp unix:", 1), True

    def _insert_cleanup_trap(self, script_content, cleanup_text):
        """Añade la limpieza de recursos auxiliares (sockets VirtioFS, qga.sock,
        etc.) al trap EXIT del script generado.

        IMPORTANTE: no se modifica solo el prefijo `trap 'rm -f`, porque las
        rutas de la VM pueden contener espacios; en ese caso el texto
        insertado podría quedar fuera de las comillas simples del trap y Bash
        terminaría interpretando fragmentos de la ruta como nombres de señales.
        Por eso el cuerpo completo se escapa con bash_squote() antes de insertarlo.

        Si el trap original no calza con el patrón esperado (p. ej. porque el
        template cambió de formato en el futuro), no se pierde la limpieza en
        silencio: se agrega un trap propio de respaldo justo tras 'set -e' y
        se deja constancia explícita en el log.
        """
        cleanup_text_for_trap = bash_squote(cleanup_text)
        trap_pattern = re.compile(r"(?m)^(\s*)trap '(rm -f .*?)' EXIT\s*$")
        match = trap_pattern.search(script_content)
        if match:
            indent, trap_body = match.groups()
            new_trap = f"{indent}trap '{trap_body}; {cleanup_text_for_trap}' EXIT"
            return script_content[:match.start()] + new_trap + script_content[match.end():]
        self.log_signal.emit(
            "[AVISO] El trap de limpieza original no tiene el formato esperado; "
            "se agrega un trap de respaldo propio para no dejar sockets/procesos huérfanos."
        )
        return script_content.replace(
            "set -e\n",
            f"set -e\ntrap '{cleanup_text_for_trap}' EXIT\n",
            1,
        )

    def _backup_existing_run_script(self, exec_path, keep=5):
        """Guarda una copia con timestamp del run_temp.sh anterior.

        Se llama antes de sobrescribir exec_path en cada arranque. Si
        QEMU falla justo después, este backup permite inspeccionar
        exactamente qué script se ejecutó.

        Se conservan solo los `keep` más recientes para no llenar la
        carpeta de la VM con decenas de backups.
        """
        import glob as _glob
        import time as _time
        if not os.path.isfile(exec_path):
            return
        try:
            stamp = _time.strftime("%Y%m%d_%H%M%S")
            backup_path = f"{exec_path}.bak_{stamp}"
            shutil.copy2(exec_path, backup_path)
        except OSError as e:
            self.log_signal.emit(f"[AVISO] No se pudo respaldar run_temp.sh: {e}")
            return
        # Purgar backups antiguos.
        try:
            pattern = f"{exec_path}.bak_*"
            existing = sorted(_glob.glob(pattern))
            for old in existing[:-keep]:
                try:
                    os.remove(old)
                except OSError:
                    pass
        except Exception:
            pass

    def _build_launch_command(self, exec_path):
        """Construye el comando real que lanza el script de arranque.

        Cuando el host tiene systemd, envuelve el lanzamiento en
        `systemd-inhibit --what=sleep:idle` para que la máquina no se
        suspenda/duerma mientras la VM está corriendo. En hosts sin systemd
        (o sin systemd-inhibit en PATH) se ejecuta igual, simplemente sin esa
        protección: no es un requisito para arrancar, solo una mejora cuando
        está disponible.
        """
        inhibit_bin = shutil.which("systemd-inhibit")
        if not inhibit_bin:
            return [exec_path]
        vm_name = os.path.basename(self.vm_dir)
        self.log_signal.emit(f"==> Suspensión del host bloqueada mientras '{vm_name}' esté corriendo (systemd-inhibit).")
        return [
            inhibit_bin, "--what=sleep:idle",
            f"--why=Máquina virtual '{vm_name}' en ejecución",
            "--mode=block", exec_path,
        ]

    def _shared_folder_devices(self):
        out=[]
        for i,item in enumerate(self.shared_folders[:8]):
            if not isinstance(item,dict): continue
            host=os.path.abspath(str(item.get("host") or "").strip()) if item.get("host") else ""
            guest=str(item.get("guest") or f"share{i}").strip()
            method=str(item.get("method") or "auto").lower()
            readonly=bool(item.get("readonly",False))
            if not host or not os.path.isdir(host):
                self.log_signal.emit(f"[WARN] Carpeta compartida omitida: no existe en el host: {host}"); continue
            if method=="auto": method="virtiofs" if self.os_type=="linux" and find_virtiofsd() else ("9p" if self.os_type=="linux" else "smb")
            out.append({"host":host,"guest":guest,"method":method,"readonly":readonly})
        return out

    def _shared_folder_args(self):
        """Construye los argumentos de carpetas compartidas sin introducir saltos de línea ambiguos en QEMU."""
        self._smb_share_host = ""
        self._smb_share_readonly = False
        folders = self._shared_folder_devices()
        qemu = []
        start = []
        cleanup = []
        # VirtioFS usa vhost-user y necesita que la RAM de la VM sea compartida
        # con el proceso virtiofsd. Sin memoria share=on el dispositivo puede
        # aparecer en el guest, pero el montaje termina con "wrong fs type /
        # bad superblock" o el tag no llega a funcionar correctamente.
        has_virtiofs = any(x.get("method") == "virtiofs" for x in folders)
        if has_virtiofs:
            qemu.append(
                f"-object memory-backend-memfd,id=memfs,size={self.ram},share=on "
                f"-numa node,memdev=memfs"
            )
            # Acumulador en bash: cada carpeta VirtioFS que arranque bien añade
            # aquí su -chardev/-device. Si una carpeta falla, simplemente no se
            # agrega nada y la VM sigue sin ella, en vez de abortar el arranque
            # completo (antes un solo virtiofsd roto tumbaba toda la VM).
            start.append('EXTRA_FS_ARGS=()')
            # Se expande al final de la línea de QEMU vía "${EXTRA_FS_ARGS[@]}",
            # que bash resuelve en tiempo de ejecución con los elementos reales.
            qemu.append('"${EXTRA_FS_ARGS[@]}"')
        for i, f in enumerate(folders):
            host = f["host"]
            guest = re.sub(r"[^A-Za-z0-9_.-]", "_", f["guest"])[:40] or f"share{i}"
            method = f["method"]
            ro = ",readonly=on" if f["readonly"] else ""
            host_q = shlex.quote(host)
            if method == "9p":
                # Todo el argumento queda en una sola línea y el path va correctamente escapado.
                qemu.append(f"-virtfs local,path={host_q},mount_tag={guest},security_model=none{ro},id=share{i}")
            elif method == "virtiofs":
                virtiofsd_bin = find_virtiofsd()
                if not virtiofsd_bin:
                    self.log_signal.emit(
                        f"[AVISO] Carpeta '{guest}' omitida: no se encontró virtiofsd en el host. "
                        "Instálalo desde Compartir carpetas → Dependencias del host. La VM continuará sin esta carpeta."
                    )
                    continue
                sock = os.path.join(self.vm_dir, f"virtiofs-{i}.sock")
                pidfile = os.path.join(self.vm_dir, f"virtiofs-{i}.pid")
                log_path = os.path.join(self.vm_dir, f"virtiofsd_{i}.log")
                try:
                    if os.path.exists(sock):
                        os.remove(sock)
                except OSError as e:
                    self._log_exc(e, f"No se pudo limpiar el socket VirtioFS previo de {guest}")
                sock_q = shlex.quote(sock)
                pidfile_q = shlex.quote(pidfile)
                # Escapado seguro (comillas simples) para insertar la ruta dentro
                # de un literal bash, igual que en el trap de limpieza más abajo.
                sock_sq = bash_squote(sock)
                chardev_elem = f"socket,id=charfs{i},path={sock_sq}"
                device_elem = f"vhost-user-fs-pci,chardev=charfs{i},tag={guest},queue-size=1024"
                # 1) Si quedó un virtiofsd huérfano de un intento anterior (p. ej.
                #    porque la VM se mató a la fuerza y el trap EXIT no llegó a
                #    correr), lo detectamos por el PID que guardamos nosotros
                #    mismos la última vez y lo matamos antes de intentar de nuevo.
                #    Sin esto, el nuevo virtiofsd choca con el lock del viejo y
                #    muere al instante con "Resource temporarily unavailable".
                # 2) Un fallo aquí NUNCA aborta el script (no hay 'exit 1'): solo
                #    se avisa y esa carpeta concreta queda fuera de la VM.
                start.append(
                    f'if [ -f {pidfile_q} ]; then\n'
                    f'  _old_pid_{i}=$(cat {pidfile_q} 2>/dev/null || true)\n'
                    f'  if [ -n "$_old_pid_{i}" ] && kill -0 "$_old_pid_{i}" 2>/dev/null; then\n'
                    f'    echo "[AVISO] Deteniendo virtiofsd huérfano (PID $_old_pid_{i}) de un intento anterior para {guest}..."\n'
                    f'    kill "$_old_pid_{i}" 2>/dev/null || true\n'
                    f'    for _k_{i} in $(seq 1 20); do kill -0 "$_old_pid_{i}" 2>/dev/null || break; sleep 0.1; done\n'
                    f'    kill -9 "$_old_pid_{i}" 2>/dev/null || true\n'
                    f'  fi\n'
                    f'fi\n'
                    f'rm -f {sock_q} {pidfile_q}\n'
                    f'echo "==> Iniciando VirtioFS: {guest}..."\n'
                    f'{shlex.quote(virtiofsd_bin)} --socket-path={sock_q} --shared-dir={host_q} --log-level=info >"{log_path}" 2>&1 &\n'
                    f'VIRTIOFS_PID_{i}=$!\n'
                    f'echo "$VIRTIOFS_PID_{i}" > {pidfile_q}\n'
                    f'VIRTIOFS_OK_{i}=0\n'
                    f'for _vfs_wait in $(seq 1 100); do '
                    f'if [ -S {sock_q} ]; then VIRTIOFS_OK_{i}=1; break; fi; '
                    f'if ! kill -0 "${{VIRTIOFS_PID_{i}}}" 2>/dev/null; then break; fi; '
                    f'sleep 0.05; done\n'
                    f'if [ "$VIRTIOFS_OK_{i}" = "1" ]; then\n'
                    f'  echo "==> VirtioFS listo: {guest}"\n'
                    f'  EXTRA_FS_ARGS+=(-chardev \'{chardev_elem}\' -device \'{device_elem}\')\n'
                    f'else\n'
                    f'  echo "[AVISO] VirtioFS no disponible para {guest}; la VM continuará SIN esta carpeta compartida. Detalle: {log_path}"\n'
                    f'  rm -f {pidfile_q}\n'
                    f'fi'
                )
                cleanup.append(
                    f'kill "${{VIRTIOFS_PID_{i}:-0}}" 2>/dev/null || true; '
                    f'rm -f {sock_q} {pidfile_q}'
                )
            elif method == "smb":
                if not self._smb_share_host:
                    self._smb_share_host = host
                    self._smb_share_readonly = f["readonly"]
                    self.log_signal.emit(f"==> Carpeta compartida SMB: {host}")
                else:
                    self.log_signal.emit(f"[WARN] SMB admite una sola carpeta por NIC NAT; se omitió: {host}")
        return (" ".join(qemu), "\n".join(start), "\n".join(cleanup))
    # ==================================================================
    # Validación de red contra lista blanca
    # ==================================================================
    # Antes de insertar cualquier valor de vm_config.ini en la línea de
    # QEMU, se valida contra una lista blanca. Cierra el vector de
    # inyección de shell si el usuario edita vm_config.ini a mano.

    _VALID_NET_MODELS = {
        "virtio-net-pci", "e1000", "e1000e", "e1000-82545em",
        "rtl8139", "vmxnet3", "i82550", "i82557b", "i82559er",
        "ne2k_pci", "pcnet", "virtio-net-device", "virtio-net",
    }
    _VALID_NET_MODES = {"nat", "bridge", "tap"}
    _IFACE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,15}$")
    _MAC_RE = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")

    def _validate_network_device(self, idx, cfg):
        """Valida un dict de red y devuelve una tupla limpia.

        Lanza RuntimeError con un mensaje concreto si algo no encaja.
        El mensaje incluye el índice del adaptador y el campo que falló,
        para que el usuario sepa exactamente qué corregir.
        """
        if not isinstance(cfg, dict):
            raise RuntimeError(f"Adaptador de red {idx+1}: no es un objeto válido.")

        model = str(cfg.get("model") or "virtio-net-pci").strip()
        if model not in self._VALID_NET_MODELS:
            raise RuntimeError(
                f"Adaptador de red {idx+1}: modelo '{model}' no reconocido. "
                f"Válidos: {', '.join(sorted(self._VALID_NET_MODELS))}."
            )

        mode = str(cfg.get("mode") or "nat").strip().lower()
        if mode not in self._VALID_NET_MODES:
            raise RuntimeError(
                f"Adaptador de red {idx+1}: modo '{mode}' no válido. "
                f"Válidos: {', '.join(sorted(self._VALID_NET_MODES))}."
            )

        interface = str(cfg.get("interface") or "").strip()
        if interface and not self._IFACE_NAME_RE.match(interface):
            raise RuntimeError(
                f"Adaptador de red {idx+1}: interfaz '{interface}' no válida. "
                "Debe tener 1-15 caracteres alfanuméricos, punto, guion o "
                "guion bajo (regla del kernel para nombres de interfaz)."
            )

        mac = str(cfg.get("mac") or "").strip()
        if mac and not self._MAC_RE.match(mac):
            raise RuntimeError(
                f"Adaptador de red {idx+1}: MAC '{mac}' no válida. "
                "Formato esperado: 52:54:00:xx:xx:xx."
            )

        # Reglas de reenvío de puertos NAT. Solo aplican con mode=nat.
        # Se validan aquí para no inyectar nada raro si el vm_config.ini
        # se edita a mano.
        raw_rules = cfg.get("hostfwd") or []
        if not isinstance(raw_rules, list):
            raw_rules = []
        hostfwd = []
        seen_rules = set()
        for ri, r in enumerate(raw_rules):
            if not isinstance(r, dict):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}, regla NAT {ri+1}: no es un objeto válido."
                )
            proto = str(r.get("protocol") or "tcp").strip().lower()
            if proto not in ("tcp", "udp"):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}, regla NAT {ri+1}: protocolo "
                    f"'{proto}' no válido (usa tcp o udp)."
                )
            try:
                hp = int(r.get("host_port"))
                gp = int(r.get("guest_port"))
            except (TypeError, ValueError):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}, regla NAT {ri+1}: puertos "
                    f"inválidos (host={r.get('host_port')!r}, guest={r.get('guest_port')!r})."
                )
            if not (1 <= hp <= 65535):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}, regla NAT {ri+1}: puerto host "
                    f"{hp} fuera de rango (1-65535)."
                )
            if not (1 <= gp <= 65535):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}, regla NAT {ri+1}: puerto guest "
                    f"{gp} fuera de rango (1-65535)."
                )
            key = (proto, hp)
            if key in seen_rules:
                raise RuntimeError(
                    f"Adaptador de red {idx+1}: regla NAT duplicada para "
                    f"el puerto host {hp} ({proto.upper()})."
                )
            seen_rules.add(key)
            hostfwd.append({"host_port": hp, "guest_port": gp, "protocol": proto})

        if hostfwd and mode != "nat":
            raise RuntimeError(
                f"Adaptador de red {idx+1}: hay reglas de reenvío de puertos "
                "pero el modo no es NAT (usa bridge/tap en su lugar)."
            )

        # Bridge: comprobación adicional contra /sys.
        if mode == "bridge":
            if not interface:
                raise RuntimeError(
                    f"Adaptador de red {idx+1}: modo bridge sin interfaz. "
                    "Indica un bridge existente en el host."
                )
            bridge_dir = os.path.join("/sys/class/net", interface, "bridge")
            if not os.path.isdir(bridge_dir):
                raise RuntimeError(
                    f"Adaptador de red {idx+1}: el bridge '{interface}' no "
                    f"existe en el host (no hay {bridge_dir})."
                )

        # Normalizar el dict: devolvemos solo las claves permitidas.
        return {
            "name": str(cfg.get("name") or f"Red {idx+1}").strip()[:60],
            "model": model,
            "mode": mode,
            "interface": interface,
            "mac": mac,
            "hostfwd": hostfwd,
        }

    def _validate_all_network_devices(self):
        """Valida TODOS los adaptadores antes de generar la línea de QEMU.

        Se llama al inicio de _network_args. Si algún adaptador falla,
        lanza RuntimeError y QEMU no se arranca con una línea
        potencialmente insegura.
        """
        raw = self.network_devices or []
        if not isinstance(raw, list):
            raise RuntimeError("network_devices no es una lista.")
        # Fallback al dispositivo legacy si no hay lista.
        if not raw:
            raw = [{
                "name": "Red 1",
                "model": self.network_model,
                "mode": self.network_mode,
                "interface": self.network_interface,
                "mac": "",
            }]
        return [self._validate_network_device(i, cfg) for i, cfg in enumerate(raw)]

    def _network_args(self, boot_index=None):
        """Construye múltiples NICs independientes; cada una puede tener modelo/modo/objetivo distinto.

        IMPORTANTE: antes de tocar la línea de QEMU, se validan
        TODOS los adaptadores contra listas blancas (modelo, modo,
        interfaz, MAC) para evitar inyección si vm_config.ini se
        edita a mano. Un valor inválido aborta el arranque con un
        mensaje claro en lugar de generar una línea peligrosa.
        """
        if getattr(self, "shared_folders", None) and not getattr(self, "_smb_share_host", ""):
            self._shared_folder_devices()
        devices = self._validate_all_network_devices()
        args = []
        for i, cfg in enumerate(devices[:8]):
            model = cfg.get("model", "virtio-net-pci") or "virtio-net-pci"
            if self.os_type == "macos" and model == "e1000":
                model = "e1000-82545em"
            mode = cfg.get("mode", "nat") or "nat"
            interface = cfg.get("interface", "") or ""
            netid = f"net{i}"
            mac = cfg.get("mac", "") or ""
            macarg = f",mac={mac}" if mac else ""
            bootarg = f",bootindex={boot_index}" if boot_index and i == 0 else ""
            if mode == "bridge":
                bridge = interface
                if not network_interface_exists(bridge) or not os.path.isdir(os.path.join("/sys/class/net", bridge, "bridge")):
                    raise RuntimeError(f"El bridge '{bridge}' no existe en el host.")
                args.append(f'-netdev bridge,id={netid},br={bridge} -device {model},netdev={netid},id={netid}{macarg}{bootarg}')
            elif mode == "tap":
                tap = interface or sanitize_tap_name(os.path.basename(self.vm_dir))
                if i > 0 and not interface:
                    tap = f"{tap[:13]}{i}"[:15]
                args.append(f'-netdev tap,id={netid},ifname={tap},script=no,downscript=no -device {model},netdev={netid},id={netid}{macarg}{bootarg}')
            else:
                smbarg = f',smb="{self._smb_share_host}"' if i == 0 and getattr(self, '_smb_share_host', '') else ''
                # Reglas de reenvío de puertos NAT (hostfwd). Se emiten como
                # una lista separada por comas dentro del propio -netdev user.
                # El dict ya viene validado por _validate_network_device.
                _rules = cfg.get("hostfwd") or []
                hfwd = ""
                if _rules:
                    _parts = []
                    for r in _rules:
                        _proto = str(r.get("protocol", "tcp")).lower()
                        _hp = int(r.get("host_port"))
                        _gp = int(r.get("guest_port"))
                        _parts.append(f"hostfwd={_proto}::{_hp}-:{_gp}")
                    hfwd = "," + ",".join(_parts)
                # netdev_user_dns_v1: forzamos dns=10.0.2.3 explícitamente.
                # Algunos guests (macOS High Sierra, Mojave, Ventura)
                # ignoran el DNS que QEMU sirve por DHCP interno y quedan
                # sin resolver nombres aunque la red funcione. Forzarlo aquí
                # es lo que usan las guías de OSX-KVM.
                args.append(f'-netdev user,id={netid},dns=10.0.2.3{smbarg}{hfwd} -device {model},netdev={netid},id={netid}{macarg}{bootarg}')
        return (" " + "\\\n    ").join(args)


    def _pci_group_members(self, group):
        if group is None:
            return []
        base=f"/sys/kernel/iommu_groups/{int(group)}/devices"
        if not os.path.isdir(base):
            return []
        return sorted(os.path.basename(x) for x in glob.glob(os.path.join(base, "*")))

    def _pci_current_driver(self, addr):
        link=os.path.join("/sys/bus/pci/devices", addr, "driver")
        if os.path.islink(link):
            return os.path.basename(os.path.realpath(link))
        return ""

    def _pci_group(self, addr):
        link=os.path.join("/sys/bus/pci/devices", addr, "iommu_group")
        try:
            if os.path.islink(link):
                return int(os.path.basename(os.path.realpath(link)))
        except Exception:
            pass
        return None

    def _run_pkexec_script(self, script, label):
        """Ejecuta una operación sysfs privilegiada de forma no persistente."""
        if shutil.which("pkexec") is None:
            raise RuntimeError("pkexec no está instalado; no se puede preparar PCI de forma automática.")
        # Aviso si no hay entorno gráfico y el prompt podría no aparecer.
        import os as _os_w
        if (not (_os_w.environ.get("DISPLAY") or _os_w.environ.get("WAYLAND_DISPLAY"))
                and _os_w.geteuid() != 0):
            self.log_signal.emit(
                "[AVISO] pkexec sin entorno gráfico: si no aparece "
                "el diálogo de contraseña en 3-5 s, cancela y usa "
                "sudo en una terminal con entorno gráfico."
            )
        try:
            r=subprocess.run(["pkexec", "sh", "-c", script], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Tiempo agotado durante la operación administrativa: {label}")
        if r.returncode != 0:
            detail=(r.stderr or r.stdout or "operación rechazada").strip()
            raise RuntimeError(f"{label}: {detail}")
        return r.stdout.strip()

    def _qemu_setcap_line_if_needed(self):
        """Devuelve la línea de shell para otorgar CAP_IPC_LOCK a qemu-system-x86_64
        si hace falta (o None si ya la tiene o no se puede determinar). No ejecuta
        nada por sí misma -- se agrega al script combinado de _prepare_pci_passthrough
        para que todo se autentique con un solo pkexec."""
        qemu_path = shutil.which("qemu-system-x86_64")
        if not qemu_path:
            return None
        qemu_path = os.path.realpath(qemu_path)
        if shutil.which("getcap"):
            try:
                r = subprocess.run(["getcap", qemu_path], capture_output=True, text=True, timeout=5)
                if "cap_ipc_lock" in (r.stdout or "").lower():
                    return None  # ya la tiene
            except Exception:
                pass
        if not shutil.which("setcap"):
            raise RuntimeError(
                "No se encontró 'setcap' (paquete libcap/libcap2-bin). "
                "Instálalo o sube RLIMIT_MEMLOCK manualmente en /etc/security/limits.conf."
            )
        return f"setcap cap_ipc_lock+ep {shlex.quote(qemu_path)}"

    def _prepare_pci_passthrough(self, selected):
        """Desliga temporalmente el driver del host y liga el PCI a vfio-pci."""
        if not selected:
            return []
        if not shutil.which("lspci"):
            raise RuntimeError("lspci no está instalado.")
        # Verificar que cada dispositivo tenga grupo y que no comparta el grupo con otro PCI.
        prepared=[]
        seen_groups=set()
        for d in selected:
            addr=str(d.get("address") or "").strip()
            if not addr:
                raise RuntimeError("Dispositivo PCI seleccionado sin dirección.")
            group=self._pci_group(addr)
            if group is None:
                raise RuntimeError(f"{addr}: no tiene grupo IOMMU; no se puede usar VFIO con seguridad.")
            members=self._pci_group_members(group)
            others=[x for x in members if x != addr]
            if others:
                raise RuntimeError(f"{addr}: comparte el grupo IOMMU {group} con {', '.join(others)}. No se hará un bind automático del grupo completo.")
            if group in seen_groups:
                continue
            seen_groups.add(group)
            driver=self._pci_current_driver(addr)
            if driver == "vfio-pci":
                prepared.append({"address":addr,"group":group,"original_driver":"vfio-pci","changed":False})
                continue
            prepared.append({"address":addr,"group":group,"original_driver":driver,"changed":False})

        # Cargar vfio-pci, hacer bind, y dar acceso al nodo /dev/vfio/GROUP resultante --
        # todo en UN SOLO script bajo un único pkexec, para pedir la contraseña una sola vez
        # (antes se hacía en dos llamadas separadas a pkexec, y PolicyKit pedía autenticación
        # dos veces seguidas para la misma operación).
        user=os.environ.get("USER") or str(os.getuid())
        setcap_line = self._qemu_setcap_line_if_needed()
        script_parts=["set -e", "modprobe vfio-pci"]
        if setcap_line:
            script_parts.append(setcap_line)
        for item in prepared:
            addr=item["address"]
            driver=item["original_driver"]
            if driver == "vfio-pci":
                continue
            dev=f"/sys/bus/pci/devices/{addr}"
            if driver:
                script_parts.append(f"echo {shlex.quote(addr)} > {shlex.quote(dev + '/driver/unbind')}")
            script_parts.append(f"echo vfio-pci > {shlex.quote(dev + '/driver_override')}")
            script_parts.append(f"echo {shlex.quote(addr)} > /sys/bus/pci/drivers/vfio-pci/bind")
        for item in prepared:
            node=f"/dev/vfio/{item['group']}"
            # Idempotente: si el nodo ya existe y/o el usuario ya tiene acceso, no hace daño repetirlo.
            script_parts.append(
                f"if [ -e {shlex.quote(node)} ]; then setfacl -m u:{shlex.quote(user)}:rw {shlex.quote(node)} || true; fi"
            )
        self._run_pkexec_script("; ".join(script_parts), "No se pudo preparar el PCI para vfio-pci")

        # Verificación final (sin más privilegios: solo lectura de /sys y os.access).
        for item in prepared:
            addr=item["address"]; group=item["group"]
            current=self._pci_current_driver(addr)
            if current != "vfio-pci":
                # Intentar restaurar cualquier cambio parcial antes de informar del fallo.
                self._restore_pci_passthrough(prepared)
                raise RuntimeError(f"{addr}: no quedó ligado a vfio-pci (driver actual: {current or 'sin driver'}).")
            node=f"/dev/vfio/{group}"
            if not (os.path.exists(node) and os.access(node, os.R_OK | os.W_OK)):
                self._restore_pci_passthrough(prepared)
                raise RuntimeError(f"{addr}: {node} no quedó accesible tras aplicar el ACL.")
        for item in prepared:
            item["changed"]=item["original_driver"] != "vfio-pci"
            item["acl_user"]=user
        # Actualizar el snapshot de configuración en memoria para el comando generado.
        for item in prepared:
            for d in selected:
                if d.get("address") == item["address"]:
                    d["driver"]="vfio-pci"
        return prepared

    def _restore_pci_passthrough(self, prepared):
        if not prepared:
            return
        script_parts=["set -e"]
        # Primero desligamos de vfio-pci, limpiamos override y luego devolvemos el driver original.
        for item in reversed(prepared):
            addr=item["address"]; original=item.get("original_driver") or ""; dev=f"/sys/bus/pci/devices/{addr}"
            if original == "vfio-pci":
                continue
            script_parts.append(f"if [ -e {shlex.quote('/sys/bus/pci/drivers/vfio-pci/' + addr)} ]; then echo {shlex.quote(addr)} > /sys/bus/pci/drivers/vfio-pci/unbind || true; fi")
            script_parts.append(f"if [ -e {shlex.quote(dev + '/driver_override')} ]; then echo '' > {shlex.quote(dev + '/driver_override')}; fi")
            if original:
                script_parts.append(f"if [ -e {shlex.quote('/sys/bus/pci/drivers/' + original)} ]; then echo {shlex.quote(addr)} > {shlex.quote('/sys/bus/pci/drivers/' + original + '/bind')} || true; fi")
            if item.get("acl_user"):
                node=f"/dev/vfio/{item['group']}"
                script_parts.append(f"if command -v setfacl >/dev/null 2>&1 && [ -e {shlex.quote(node)} ]; then setfacl -x u:{shlex.quote(item['acl_user'])} {shlex.quote(node)} || true; fi")
        self._run_pkexec_script("; ".join(script_parts), "No se pudieron restaurar los dispositivos PCI")
        for item in prepared:
            if item.get("original_driver") and item.get("original_driver") != "vfio-pci":
                # Releer para el estado final; si el driver tarda en reaparecer no marcamos error aquí.
                pass

    def _pointer_args(self):
        """Emite los dispositivos de señalización (ratón/teclado) para QEMU.

        Marcador: macos_pointer_ehci_v1

        Reglas:
          • macOS + auto → EHCI (USB 2.0) + usb-kbd + usb-tablet + hotplug off.
            High Sierra (y otras versiones) no inicializan bien el XHCI de
            QEMU: el cursor queda quieto en (0,0) y el teclado no responde
            aunque OpenCore sí los detecte. OSX-KVM usa EHCI por defecto
            por esta misma razón. La directiva acpi-pci-hotplug-with-bridge-
            support=off evita que macOS pierda el bridge PCIe donde vive el
            controlador USB tras el arranque del kernel.
          • Otros + auto → vacío (PS/2 por defecto de QEMU, como hasta ahora).
          • Modos explícitos: usb-tablet, usb-mouse, usb-kbd-tablet,
            virtio-tablet, ps2, none. En macOS todos los USB van por EHCI.
        """
        mode = str((self.extra_params or {}).get("pointer_device") or "auto").lower()
        if mode in ("", "none"):
            return ""

        is_macos = (self.os_type == "macos")
        if is_macos:
            bus = "ehci.0"
            controller = "usb-ehci,id=ehci"
            extra_global = "-global ICH9-LPC.acpi-pci-hotplug-with-bridge-support=off"
        else:
            bus = None
            controller = None
            extra_global = ""

        def _usb_dev(name):
            if bus:
                return f"-device {name},bus={bus}"
            return f"-device {name}"

        if mode == "auto":
            if is_macos:
                return (
                    "-device usb-ehci,id=ehci "
                    "-device usb-kbd,bus=ehci.0 "
                    "-device usb-tablet,bus=ehci.0 "
                    "-global ICH9-LPC.acpi-pci-hotplug-with-bridge-support=off"
                )
            return ""

        parts = []
        if controller:
            parts.append(f"-device {controller}")

        if mode == "usb-tablet":
            parts.append(_usb_dev("usb-tablet"))
        elif mode == "usb-mouse":
            parts.append(_usb_dev("usb-mouse"))
        elif mode == "usb-kbd-tablet":
            parts.append(_usb_dev("usb-kbd"))
            parts.append(_usb_dev("usb-tablet"))
        elif mode == "virtio-tablet":
            if is_macos:
                self.log_signal.emit(
                    "[AVISO] macOS: virtio-tablet no es viable aquí; se usa usb-tablet."
                )
                parts.append(_usb_dev("usb-tablet"))
            elif self._qemu_supports("virtio-tablet-pci"):
                parts.append("-device virtio-tablet-pci")
            else:
                self.log_signal.emit(
                    "[AVISO] virtio-tablet-pci no está disponible; se usa usb-tablet."
                )
                parts.append(_usb_dev("usb-tablet"))
        elif mode == "ps2":
            # macOS no tiene PS/2 nativo: si el usuario elige ps2 en una VM
            # macOS, dejamos el EHCI con tablet igualmente para no dejarla
            # sin entrada.
            if is_macos:
                parts.append(_usb_dev("usb-kbd"))
                parts.append(_usb_dev("usb-tablet"))
            else:
                parts = []

        if is_macos and extra_global and extra_global not in parts:
            parts.append(extra_global)

        return " ".join(parts)
    def _serial_args(self):
        """Devuelve el flag -serial file:<vm_dir>/serial.log si la VM lo
        tiene activado en extra.serial_to_file.

        Marcador: serial_to_file_v1

        Util para diagnosticar problemas de arranque cuando la consola
        grafica no muestra nada: la BIOS/OVMF, el cargador de arranque
        y el kernel suelen volcar su progreso al puerto serie del
        guest.

        El archivo se escribe en la carpeta de la VM y se TRUNCA en
        cada arranque (comportamiento por defecto de QEMU con file:).
        Solo conserva, por tanto, la ultima sesion.
        """
        if not bool((self.extra_params or {}).get("serial_to_file", False)):
            return ""
        log_path = os.path.join(self.vm_dir, "serial.log")
        return f'-serial file:"{log_path}"'

    def _passthrough_args(self):
        # Modo compatibilidad de snapshots (marcador snapshot_compat_v1):
        # los dispositivos PCI/USB son hardware físico sin vmstate
        # posible. Con el flag activo se omiten completamente.
        if bool((self.extra_params or {}).get("snapshot_compat")) \
                and self.passthrough_devices:
            self.log_signal.emit(
                "[AVISO] Modo compatibilidad de snapshots: el passthrough "
                "PCI/USB queda deshabilitado para permitir snapshots "
                "completos. Los dispositivos seleccionados NO se añaden "
                "a esta VM."
            )
            return ""
        args=[]
        usb_used=False
        pci_selected=[d for d in self.passthrough_devices[:16] if d.get("kind")=="pci"]
        if pci_selected:
            not_bound=[d.get("address", "?") for d in pci_selected if str(d.get("driver", "")).strip() != "vfio-pci"]
            # El run() wrapper prepara los dispositivos antes de llegar aquí.
            # Este guard solo evita generar una orden inconsistente si algo cambió.
            if not_bound:
                raise RuntimeError("Passthrough PCI: el dispositivo no quedó ligado a vfio-pci: " + ", ".join(not_bound))
        for d in self.passthrough_devices[:16]:
            kind=d.get("kind")
            if kind == "pci":
                addr=d.get("address", "").strip()
                if addr:
                    args.append(f'-device vfio-pci,host={addr}')
            elif kind == "usb":
                bus=str(d.get("bus") or "").strip()
                addr=str(d.get("addr") or "").strip()
                vid=str(d.get("vendorid") or "").strip().lower()
                pid=str(d.get("productid") or "").strip().lower()
                if (bus and addr) or (vid and pid):
                    usb_used=True
                    # Con XHCI usamos explícitamente qemu-xhci.0; si se omite el bus,
                    # QEMU puede intentar resolver usb-bus.0 y fallar con "No 'usb-bus' bus found".
                    if vid and pid:
                        args.append(f'-device usb-host,bus=usbpass.0,vendorid=0x{vid},productid=0x{pid}')
                    else:
                        args.append(f'-device usb-host,hostbus={bus},hostaddr={addr}')
        # Siempre creamos un controlador XHCI dedicado. Así el botón de hotplug puede
        # usar de forma estable el bus usbpass.0 incluso cuando la VM arrancó sin USB
        # guardados en passthrough.
        args.insert(0, '-device qemu-xhci,id=usbpass')
        return (" " + "\\\n    ").join(args)


    def _prepare_tap_interfaces(self):
        """Crea TAPs necesarios para los adaptadores configurados individualmente."""
        # Reutilizamos la validación: si algún adaptador tiene un
        # nombre de interfaz inválido, no llegamos a ejecutar `ip`.
        validated = self._validate_all_network_devices()
        taps=[]
        for i,cfg in enumerate(validated):
            if cfg.get("mode") != "tap":
                continue
            tap=cfg.get("interface") or sanitize_tap_name(os.path.basename(self.vm_dir))
            if not cfg.get("interface"):
                tap=f"{tap[:13]}{i}"[:15] if i>0 else tap[:15]
            taps.append(tap)
        created=[]
        for tap in taps:
            if network_interface_exists(tap):
                continue
            cmd=["ip","tuntap","add","dev",tap,"mode","tap","user",str(os.getuid())]
            try:
                result=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
            except Exception as e:
                raise RuntimeError(f"No se pudo crear la interfaz TAP '{tap}': {e}")
            if result.returncode!=0:
                detail=result.stderr.strip() or result.stdout.strip() or "permiso insuficiente"
                raise RuntimeError(f"No se pudo crear la interfaz TAP '{tap}'. {detail}")
            created.append(tap)
        return created

    def _prepare_macos_ovmf_files(self, vm_dir):
        """Prepara OVMF para macOS sin copiar la carpeta OSX-KVM.

        OVMF CODE se comparte desde el firmware del host. OVMF VARS sí es
        estado de la VM y por eso se crea una copia privada dentro de vm_dir.
        """
        os.makedirs(vm_dir, exist_ok=True)
        code_src, vars_src = find_ovmf_files(secure_boot=False)
        if not code_src or not vars_src:
            raise RuntimeError("No se encontró una pareja OVMF válida (CODE/VARS) para macOS. Instala OVMF/edk2-ovmf y vuelve a intentarlo.")
        vars_dst=os.path.join(vm_dir,"OVMF_VARS-1920x1080.fd")
        if not os.path.isfile(vars_dst) or os.path.getsize(vars_dst)==0:
            shutil.copy2(vars_src,vars_dst)
            self.log_signal.emit(f"==> OVMF VARS creado para esta VM: {os.path.basename(vars_dst)}")
        if not os.path.isfile(code_src) or os.path.getsize(code_src)==0:
            raise RuntimeError(f"OVMF CODE no quedó disponible: {code_src}")
        if not os.path.isfile(vars_dst) or os.path.getsize(vars_dst)==0:
            raise RuntimeError(f"OVMF VARS no quedó disponible: {vars_dst}")
        self.log_signal.emit("==> Firmware OVMF de macOS verificado: CODE compartido + VARS privado.")
        return code_src, vars_dst

    def _boot_token_label(self, token):
        """Etiqueta legible para el log del worker, sin depender de métodos de la UI."""
        if token == "network":
            return "Red/PXE"
        if token == "cdrom":
            return "CD/DVD"
        if token.startswith("cdrom:"):
            ident = token.split(":", 1)[1]
            for d in self._storage_devices_from_config():
                if str(d.get("id", "")) == ident and d.get("device") == "cdrom":
                    path = d.get("path") or ""
                    name = d.get("name") or "CD/DVD"
                    return f"CD/DVD: {name} — {os.path.basename(path) if path else 'vacío'}"
            return "CD/DVD"
        if token == "disk":
            return "Disco principal"
        if token.startswith("disk:"):
            ident = token.split(":", 1)[1]
            for d in self._storage_devices_from_config():
                if str(d.get("id", "")) == ident:
                    name = d.get("name") or ident
                    typ = d.get("device", "sata")
                    if typ == "nvme":
                        return "NVMe — " + name
                    if typ == "floppy":
                        return "Floppy — " + name
                    return "SATA — " + name
            return "SATA — " + ident
        return token

    def _boot_arg(self):
        # Compatibilidad con configuraciones antiguas. El orden nuevo usa bootindex.
        return {"disk": "c", "cdrom": "d", "network": "n"}.get(self.boot_device, "d")

    def _storage_devices_from_config(self):
        try:
            cfg = load_vm_config(self.vm_dir)
            devices = (cfg.get("extra") or {}).get("storage_devices", [])
            if not isinstance(devices, list):
                return []
            # portable_paths_v1: resolver paths relativos a absolutos.
            return vm_paths.resolve_storage_devices(self.vm_dir, devices)
        except Exception:
            return []

    def _vm_disk_files(self):
        """Devuelve discos locales + discos existentes adjuntados por el usuario, sin duplicados."""
        files = []
        if self.disk_path and os.path.isfile(self.disk_path):
            files.append(self.disk_path)
        # Dispositivos registrados en almacenamiento, en el orden configurado.
        for d in self._storage_devices_from_config():
            if d.get("device") == "cdrom":
                continue
            path = d.get("path", "")
            if path and os.path.isfile(path) and path not in files:
                files.append(path)
        try:
            for name in sorted(os.listdir(self.vm_dir)):
                if not name.startswith(("disk_", "sata_", "nvme_", "hd_", "floppy_", "vm_disk.")):
                    continue
                path = os.path.join(self.vm_dir, name)
                if os.path.isfile(path) and path not in files:
                    files.append(path)
        except Exception:
            pass
        return files

    def _device_type_for_path(self, path):
        ap=os.path.abspath(path)
        for d in self._storage_devices_from_config():
            if os.path.abspath(d.get("path", "")) == ap:
                return d.get("device", "sata")
        base=os.path.basename(path).lower()
        return "nvme" if base.startswith("nvme_") else ("floppy" if base.startswith("floppy_") else "sata")

    def _boot_index_for(self, token):
        try:
            return self.boot_order.index(token) + 1
        except ValueError:
            return None

    def _chipset_is_q35(self):
        """True si el chipset configurado para esta VM es Q35.

        Se mira self.chipset_args (construido en __init__ a partir de
        extra_params["chipset"]) para no depender del orden en que
        self.extra_params esté relleno. Q35 trae el controlador AHCI
        del ICH9 con los puertos ide.0..ide.5; i440FX (pc) sólo
        tiene ide.0 e ide.1 y falla con bus=ide.2.
        """
        args = str(getattr(self, "chipset_args", "") or "")
        # -machine q35, -machine q35,smm=on, etc. Basta con buscar "q35"
        # como palabra suelta tras -machine.
        import re as _re
        return bool(_re.search(r"-machine\s+q35(?:\b|,)", args))

    def _resolve_disk_bus_for_os(self, devtype):
        """Decide qué bus usar para un disco duro según el SO invitado.

        Marcador interno: nvme_default_all_modern_os

        Reglas:
          • device="nvme" explícito → siempre NVMe (respetado).
          • device="floppy" / "cdrom" → no aplica.
          • device="sata" (disco duro genérico):
              - macOS              → "sata_ahci" (OpenCore/OSX-KVM usan SATA)
              - Windows XP / 2000  → "ide"       (sin drivers AHCI)
              - Windows Vista / 7  → "sata_ahci" (sin driver NVMe nativo)
              - Windows 8.1+ / 10 / 11 → "nvme"
              - Linux (moderno)    → "nvme"
              - Otros              → "nvme" (fallback)
        """
        if devtype == "nvme":
            return "nvme"
        if devtype in ("floppy", "cdrom"):
            return devtype
        # A partir de aquí, devtype == "sata" (disco duro genérico).
        if self.os_type == "macos":
            return "sata_ahci"
        if self.os_type == "windows":
            win_ver = str((self.extra_params or {}).get("win_ver") or "").lower()
            if "xp" in win_ver or "2000" in win_ver:
                return "ide"
            if "vista" in win_ver or "windows 7" in win_ver:
                return "sata_ahci"
            return "nvme"
        if self.os_type == "linux":
            return "nvme"
        if self.os_type == "android":
            # Android-x86 / Bliss OS se instalan y arrancan mejor en
            # AHCI: el instalador particiona y monta sin necesitar
            # drivers NVMe específicos del kernel Android-x86.
            # AHCI (ide.0..ide.5) sólo existe en Q35; si el chipset
            # guardado es i440FX (pc), el bus ide.2 no existe y QEMU
            # falla con "Bus 'ide.2' not found". En ese caso se
            # degrada a IDE heredado, que sí funciona en ambos.
            return "sata_ahci" if self._chipset_is_q35() else "ide"
        return "nvme"

    def _disk_runtime_args(self):
        """Construye los argumentos de disco para QEMU.

        El bus real se decide con _resolve_disk_bus_for_os(), que traduce
        el "device" lógico (sata/nvme/floppy) al bus QEMU adecuado según
        el sistema operativo invitado:

          • NVMe            → -device nvme,...
          • SATA AHCI       → -device ide-hd,bus=ide.N (AHCI del Q35)
          • IDE heredado    → -device ide-hd (sin bus explícito)
          • Floppy          → -device floppy,...

        Marcador: nvme_default_all_modern_os
        """
        args = []
        devices = [
            d for d in self._storage_devices_from_config()
            if d.get("device") in ("sata", "nvme", "floppy")
            and d.get("path") and os.path.isfile(d.get("path"))
        ]
        if not devices:
            disk_files = self._vm_disk_files()
            devices = [
                {"id": None, "name": os.path.basename(p),
                 "path": p, "device": self._device_type_for_path(p)}
                for p in disk_files
            ]

        sata_ahci_port = 0
        for idx, d in enumerate(devices):
            path = d.get("path")
            devtype = d.get("device", "sata")
            bus = self._resolve_disk_bus_for_os(devtype)
            ident = d.get("id")
            token = f"disk:{ident}" if ident else f"disk:{os.path.basename(path)}"
            boot_index = self._boot_index_for(token)
            if boot_index is None and idx == 0:
                boot_index = self._boot_index_for("disk")
            drive_id = f"disk{idx}"

            try:
                info = subprocess.run(
                    ["qemu-img", "info", "--output=json", path],
                    capture_output=True, text=True, timeout=10, check=True,
                )
                fmt = json.loads(info.stdout).get(
                    "format", "raw" if bus == "floppy" else "qcow2"
                )
            except Exception:
                fmt = ("raw" if bus == "floppy"
                       else (self.disk_format if idx == 0 else "qcow2"))

            if bus == "nvme":
                args.append(f'-drive file="{path}",format={fmt},if=none,id={drive_id}')
                dev = f'-device nvme,drive={drive_id},serial={idx:08d}'
                if boot_index:
                    dev += f',bootindex={boot_index}'
                args.append(dev)

            elif bus == "floppy":
                args.append(f'-drive file="{path}",format=raw,if=none,id={drive_id}')
                if boot_index:
                    args.append(f'-device floppy,drive={drive_id},bootindex={boot_index}')
                else:
                    args.append(f'-device floppy,drive={drive_id}')

            elif bus == "sata_ahci":
                args.append(f'-drive file="{path}",format={fmt},if=none,id={drive_id}')
                # Discos SATA empiezan en ide.2: los primeros
                # puertos del AHCI (ide.0, ide.1) están reservados para CDs.
                port = 2 + sata_ahci_port
                sata_ahci_port += 1
                dev = (f'-device ide-hd,drive={drive_id},id={drive_id},'
                       f'bus=ide.{port},unit=0')
                if boot_index:
                    dev += f',bootindex={boot_index}'
                args.append(dev)

            else:  # "ide" — IDE heredado para Windows XP/2000
                args.append(f'-drive file="{path}",format={fmt},if=none,id={drive_id}')
                dev = f'-device ide-hd,drive={drive_id},id={drive_id}'
                if boot_index:
                    dev += f',bootindex={boot_index}'
                args.append(dev)

        # Log informativo del bus elegido.
        try:
            buses = {self._resolve_disk_bus_for_os(d.get("device", "sata"))
                     for d in devices if d.get("device") in ("sata", "nvme")}
            if buses:
                self.log_signal.emit(
                    f"==> Disco(s) duro(s): bus {', '.join(sorted(buses))} "
                    f"(según SO invitado)."
                )
        except Exception:
            pass

        return " \\\n    ".join(args)


    def _console_args(self):
        """Devuelve los argumentos -vnc/-spice según protocolo y modo.

        Si el modo es 'native' devuelve '' (QEMU usará -display gtk/sdl).
        En embedded/external siempre se emite un socket Unix; la diferencia
        es quién se conecta (widget Qt o visor externo).
        """
        args, info = qemu_console_args(
            self.vm_dir, self.console_protocol, self.console_mode
        )
        return args, info

    def _cdrom_runtime_args(self, iso_path):
        """Construye las unidades ópticas por SATA AHCI.

        Marcador: cdrom_sata_ahci_v1

        Antes se conectaban por virtio-scsi, para el que Windows Setup no
        tiene drivers nativos. Eso hacía que Windows arrancara pero no
        pudiera leer más archivos del CD, con lo que no detectaba discos
        ni podía cargar drivers adicionales.

        Ahora van por el AHCI del chipset Q35, que Windows sí reconoce
        nativamente. Los CDs se colocan en ide.0 e ide.1 (los primeros
        puertos del AHCI) para que los discos SATA puedan empezar en
        ide.2 sin colisión.
        """
        devices = [d for d in self._storage_devices_from_config()
                   if d.get("device") == "cdrom"]
        if not devices:
            legacy_path = iso_path if iso_path and iso_path != "$ISO_FINAL" else ""
            devices = ([{"id": "dev_legacy0", "name": "CD/DVD 1", "path": legacy_path}]
                       if legacy_path else [])
        if not devices:
            return ""

        parts = []
        max_units = 4  # ide.0..ide.3 para CDs (raro tener más de 2, pero por si acaso)
        for idx, d in enumerate(devices[:max_units]):
            raw_id = str(d.get("id") or f"cd{idx}")
            safe_id = _qemu_safe_identifier(raw_id, "cd")
            drive_id = f"cdrom_{idx}"
            path = d.get("path", "") or ""

            drive = f'-drive if=none,id={drive_id},media=cdrom,readonly=on'
            if path and path != "$ISO_FINAL":
                if os.path.isfile(path):
                    drive += f',file="{path}"'
            elif path == "$ISO_FINAL":
                drive += ',file="$ISO_FINAL"'
            parts.append(drive)

            boot_index = self._boot_index_for(f"cdrom:{d.get('id')}")
            if boot_index is None and idx == 0:
                boot_index = self._boot_index_for("cdrom")

            # Conectar al puerto N del AHCI del Q35.
            dev = (f'-device ide-cd,drive={drive_id},bus=ide.{idx},unit=0,'
                   f'id={safe_id}')
            if boot_index:
                dev += f',bootindex={boot_index}'
            parts.append(dev)

        return " \\\n    ".join(parts)


    def _boot_token_label(self, token):
        if token == "network":
            return "Red/PXE"
        if token == "cdrom":
            return "CD/DVD"
        if token.startswith("cdrom:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_from_config() if str(d.get("id")) == ident), None)
            if dev:
                path=dev.get("path") or ""
                return f"CD/DVD — {dev.get('name') or 'CD/DVD'}" + (f" ({os.path.basename(path)})" if path else " (vacío)")
            return "CD/DVD"
        if token == "disk":
            return "Disco principal"
        if token.startswith("disk:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_from_config() if str(d.get("id")) == ident), None)
            if dev:
                typ=dev.get("device", "sata")
                prefix={"nvme":"NVMe", "floppy":"Disquete"}.get(typ, "SATA")
                return f"{prefix} — {dev.get('name') or os.path.basename(dev.get('path',''))}"
            return f"Disco — {ident}"
        return str(token)

    def request_cancel(self):
        self._cancel_event.set()

    def _check_cancelled(self):
        if self._cancel_event.is_set():
            raise DownloadCancelled("Descarga cancelada por el usuario.")

    def _installer_cdrom_devices(self):
        """Devuelve solo los CD/DVD que realmente necesitan descargar un instalador.

        Una configuración antigua puede conservar source=installer después de que la
        ISO ya se haya descargado. Si existe una ruta local válida, no debe abrirse la
        ventana de descarga ni volver a consultar la URL.
        """
        pending = []
        for d in self._storage_devices_from_config():
            if d.get("device") != "cdrom" or d.get("source") != "installer":
                continue
            path = os.path.abspath(str(d.get("path") or "").strip()) if d.get("path") else ""
            if path and os.path.isfile(path) and os.path.getsize(path) > 0:
                continue
            pending.append(d)
        return pending

    def _download_installer_at_start(self, os_type, win_ver="", distro="", distro_version=""):
        """Descarga el instalador seleccionado justo antes de arrancar QEMU.

        La descarga ocurre dentro de InstallWorker para no bloquear la interfaz.
        El medio queda guardado en la carpeta de la VM y la unidad CD/DVD se
        actualiza en vm_config.ini antes de construir la orden de QEMU.
        """
        devices = self._installer_cdrom_devices()
        if not devices:
            return ""

        # linux_installer_guard_v1: si la distro Linux no tiene
        # descarga automatica, limpiar el source="installer" de
        # esas unidades para que no vuelvan a aparecer en el
        # proximo arranque. Se emite un aviso claro y se sigue.
        if os_type == "linux":
            try:
                import iso_versions as _iv
                _distro_name = (distro or "").strip()
                if _distro_name and not _iv.supports_auto_download(_distro_name):
                    self.log_signal.emit(
                        f"[AVISO] La distro '{_distro_name}' no tiene "
                        "descarga automatica desde los espejos "
                        "oficiales. Se convertira la unidad CD/DVD "
                        "en vacia y la VM arrancara sin ISO. Anade su "
                        "ISO manualmente con la opcion "
                        "'Usar ISO/IMG/DMG existente'."
                    )
                    _all_devs = self._storage_devices_from_config()
                    _changed = False
                    for _d in _all_devs:
                        if (_d.get("device") == "cdrom"
                                and _d.get("source") == "installer"):
                            _d.pop("source", None)
                            _d["path"] = ""
                            _changed = True
                    if _changed:
                        self._write_storage_devices(_all_devs)
                    return ""
            except Exception as _guard_err:
                self.log_signal.emit(
                    "[AVISO] linux_installer_guard: " + str(_guard_err)
                )

        if os_type == "windows":
            url = get_latest_windows_iso_url(win_ver or "Windows 11")
            filename = os.path.join(
                self.vm_dir,
                "installer_" + re.sub(r"[^A-Za-z0-9_.-]", "_", (win_ver or "Windows 11").lower()) + ".iso"
            )
            label = f"Descargando instalador de {win_ver or 'Windows'}"
        else:
            url = iso_versions.get_iso_url(distro or "Linux", distro_version)
            filename = os.path.join(
                self.vm_dir,
                "installer_" + re.sub(r"[^A-Za-z0-9_.-]", "_", (distro or "Linux").lower())
                + iso_versions.iso_filename_tag(distro_version) + ".iso"
            )
            label = f"Descargando instalador de {distro or 'Linux'}" + (f" {distro_version}" if distro_version else "")

        self.log_signal.emit(f"==> {label} al iniciar la VM...")
        self.log_signal.emit(f"==> URL detectada: {url}")

        # Si ya existe una descarga completa, no volvemos a descargarla.
        if os.path.isfile(filename) and os.path.getsize(filename) > 0:
            self.progress_signal.emit(100, f"{label}\nMedio existente — 100%")
            self.log_signal.emit(f"==> ISO ya disponible: {filename}")
        else:
            self._download_file_with_progress(url, filename, label)

        devices = self._storage_devices_from_config()
        changed = False
        for d in devices:
            if d.get("device") == "cdrom" and d.get("source") == "installer":
                d["path"] = os.path.abspath(filename)
                changed = True
        if changed:
            self._write_storage_devices(devices)
        self.log_signal.emit(f"==> Instalador listo: {os.path.basename(filename)}")
        return filename

    def _download_file_with_progress(self, url, filename, label):
        """Descarga con progreso y cancelación segura desde la interfaz."""
        tmp = filename + ".part"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        r = None
        try:
            self._check_cancelled()
            self.progress_signal.emit(0, label + "\nConectando…")
            r = requests.get(url, stream=True, timeout=(15, 30))
            r.raise_for_status()
            total = int(r.headers.get("content-length", "0") or 0)
            done = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    self._check_cancelled()
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total > 0:
                        pct = max(0, min(100, int(done * 100 / total)))
                        self.progress_signal.emit(pct, f"{label}\n{pct}% — {done / (1024 ** 3):.2f} GB / {total / (1024 ** 3):.2f} GB")
                    else:
                        self.progress_signal.emit(-1, f"{label}\n{done / (1024 ** 3):.2f} GB descargados")
            self._check_cancelled()
            if total > 0 and done < total:
                raise RuntimeError(f"La descarga quedó incompleta ({done} de {total} bytes).")
            os.replace(tmp, filename)
            self.progress_signal.emit(100, f"{label}\n100% — {done / (1024 ** 3):.2f} GB")
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            raise
        finally:
            if r is not None:
                try:
                    r.close()
                except Exception:
                    pass

    def _write_storage_devices(self, devices):
        """Guarda storage_devices desde el hilo de arranque de la VM."""
        cfg_path = os.path.join(self.vm_dir, "vm_config.ini")
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("extra"):
            cfg.add_section("extra")
        try:
            extra = json.loads(cfg["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        # portable_paths_v1: guardar paths relativos si están dentro de
        # la carpeta de la VM.
        try:
            devices = vm_paths.normalize_storage_devices(self.vm_dir, devices)
        except Exception:
            pass
        extra["storage_devices"] = devices
        extra["cdrom_path"] = ""
        cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            cfg.write(f)

    def _write_extra_extra_keys(self, **kwargs):
        """Actualiza extra.data en vm_config.ini con las claves indicadas.

        Se usa desde la rama macOS para persistir la MAC asignada
        (macos_mac_uniqueness_v1) y desde cualquier otra rama que
        necesite guardar valores en extra sin reescribir todo el bloque.
        Pasar None como valor borra la clave.
        """
        if not kwargs:
            return
        cfg_path = os.path.join(self.vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("extra"):
            cfg.add_section("extra")
        try:
            extra = json.loads(cfg["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        for k, v in kwargs.items():
            if v is None:
                extra.pop(k, None)
            else:
                extra[k] = v
        cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            cfg.write(f)

    def run(self):
        """Ejecuta la VM y gestiona el passthrough PCI temporalmente."""
        pci_prepared = []
        try:
            # Modo compatibilidad de snapshots (marcador snapshot_compat_v1):
            # no tocamos los drivers del host para passthrough, porque los
            # dispositivos no se van a añadir a la VM.
            _sc_active = bool((self.extra_params or {}).get("snapshot_compat"))
            pci_selected = []
            if not _sc_active:
                pci_selected = [d for d in (self.passthrough_devices or [])[:16] if d.get("kind") == "pci"]
            if pci_selected:
                self.log_signal.emit("==> Preparando PCI para VFIO (modo temporal)...")
                pci_prepared = self._prepare_pci_passthrough(pci_selected)
                self.log_signal.emit(f"==> {len(pci_prepared)} dispositivo(s) PCI preparado(s) para VFIO.")
            return self._run_impl()
        except DownloadCancelled:
            self.log_signal.emit("[CANCELADO] Descarga cancelada por el usuario. La máquina virtual no se iniciará.")
            self.finished_signal.emit(2)
            return
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Arranque de la máquina virtual: {e}")
            self.finished_signal.emit(1)
            return
        finally:
            if pci_prepared:
                try:
                    self.log_signal.emit("==> Restaurando drivers PCI del host...")
                    self._restore_pci_passthrough(pci_prepared)
                    self.log_signal.emit("==> Drivers PCI del host restaurados.")
                except Exception as e:
                    self.log_signal.emit(f"[AVISO] No se pudieron restaurar todos los drivers PCI: {e}")

    def _run_impl(self):
        filename = self.disk_path  # ruta absoluta, dentro de la carpeta de la VM
        if self.skip_disk_create:
            disk_cmd = f'echo "==> Reutilizando disco existente: {filename}"'
        else:
            prealloc_arg = "-o preallocation=full" if self.disk_type == "fixed" and self.disk_format in ["qcow2", "raw", "vmdk"] else ""
            disk_cmd = f'qemu-img create -f {self.disk_format} {prealloc_arg} "{filename}" {self.disk_size}'

        if self.os_type == "macos":
            os_choice = self.extra_params.get("os_choice", "7")
            use_custom = self.extra_params.get("mac_use_custom", False)
            custom_image = vm_paths.to_absolute(
                self.vm_dir, self.extra_params.get("mac_custom_image", "") or ""
            )
            # macOS usa OSX-KVM como fuente de OpenCore, pero NO se copia la carpeta
            # OSX-KVM dentro de cada VM. El administrador construye directamente la
            # línea QEMU y solo conserva en la VM el estado que realmente es propio
            # de ella (disco, NVRAM OVMF y recovery).
            osx_kvm_source = self.extra_params.get("osx_kvm_source") or ""
            # osx_kvm_pkg_paths_v1: si falta o ya no existe (p. ej. VM importada
            # con una ruta de /usr/lib), usar la ruta que decide vm_config.
            if not osx_kvm_source or not os.path.isdir(osx_kvm_source):
                import vm_config as _vmc
                osx_kvm_source = _vmc.OSX_KVM_DIR
            source_opencore = os.path.join(osx_kvm_source, "OpenCore", "OpenCore.qcow2")
            if not os.path.isfile(source_opencore) or os.path.getsize(source_opencore) == 0:
                raise RuntimeError(
                    "No se encontró OpenCore/OpenCore.qcow2 en la instalación maestra de OSX-KVM.\n"
                    f"Ruta esperada: {source_opencore}\n\n"
                    "No se copiará OSX-KVM dentro de la VM; instala o selecciona una copia válida de OSX-KVM."
                )

            source_opencore_script = os.path.join(osx_kvm_source, "OpenCore-Boot.sh")
            if os.path.isfile(source_opencore_script):
                self.log_signal.emit("==> OSX-KVM/OpenCore detectado como plantilla maestra; no se copiará a la VM.")
            else:
                self.log_signal.emit("==> Aviso: OpenCore-Boot.sh no está en la plantilla; se usará el lanzador interno del administrador.")

            code_path, vars_path = self._prepare_macos_ovmf_files(self.vm_dir)
            # Recovery es un recurso propio de la VM y se guarda directamente en su raíz.
            # Compatibilidad: si una VM antigua todavía lo tiene dentro de OSX-KVM,
            # podemos usarlo allí sin copiar la carpeta completa.
            base_system = os.path.join(self.vm_dir, "BaseSystem.img")
            legacy_base_system = os.path.join(self.vm_dir, "OSX-KVM", "BaseSystem.img")
            if (not os.path.isfile(base_system) or os.path.getsize(base_system) == 0) and os.path.isfile(legacy_base_system) and os.path.getsize(legacy_base_system) > 0:
                base_system = legacy_base_system
                self.log_signal.emit("==> Recovery heredado detectado dentro de OSX-KVM; se usará directamente, sin copiar OSX-KVM.")
            if use_custom:
                ext = os.path.splitext(custom_image)[1].lower()
                if not custom_image or not os.path.isfile(custom_image):
                    raise RuntimeError(f"No se encontró la imagen personalizada de macOS: {custom_image}")
                if ext == ".dmg":
                    dmg2img = shutil.which("dmg2img")
                    if not dmg2img:
                        import system_deps
                        dmg2img = system_deps.ensure_dmg2img(self.log_signal.emit)
                    if not dmg2img:
                        raise RuntimeError("Para usar una imagen .dmg personalizada se necesita dmg2img y no se pudo instalar automáticamente "
                                           "(en Arch/CachyOS: paru -S dmg2img).")
                    self.log_signal.emit("==> Convirtiendo imagen personalizada .dmg a BaseSystem.img...")
                    result = subprocess.run([dmg2img, custom_image, base_system], capture_output=True, text=True, timeout=900)
                    if result.returncode != 0:
                        raise RuntimeError(result.stderr.strip() or "dmg2img no pudo convertir la imagen.")
                else:
                    shutil.copy2(custom_image, base_system)
                    self.log_signal.emit("==> Imagen personalizada de macOS preparada como BaseSystem.img.")
            # macos_recovery_optional_v1: BaseSystem.img solo es
            # obligatorio si el usuario configuro una unidad de
            # System Recovery. Si tiene un medio propio o el sistema
            # ya esta instalado, se permite arrancar sin el.
            _recovery_unit_configured = any(
                d.get("device") == "cdrom"
                and str(d.get("source") or "") == "recovery"
                for d in self._storage_devices_from_config()
            )
            _has_base_system = (
                os.path.isfile(base_system)
                and os.path.getsize(base_system) > 0
            )
            if (not _has_base_system and not use_custom
                    and _recovery_unit_configured):
                raise RuntimeError(
                    "No existe BaseSystem.img y hay una unidad System "
                    "Recovery configurada. Descarga el Recovery o "
                    "quita esa unidad.\n"
                    f"Ruta esperada: {base_system}"
                )

            try:
                audio_backend, audio_args = self._audio_args()
                self._prepare_tap_interfaces()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Audio/Red macOS: {e}")
                self.finished_signal.emit(1)
                return

            # macos_nic_per_version_v1
            # High Sierra (10.13) y Mojave (10.14) no traen driver
            # virtio-net en el instalador: el kernel ve la interfaz
            # pero no obtiene IP ni responde ARP ("No route to host").
            # El propio OSX-KVM recomienda vmxnet3 para High Sierra.
            # Catalina (10.15) y posteriores sí traen virtio-net.
            _os_choice_nic = str(self.extra_params.get("os_choice", "7"))
            if _os_choice_nic in ("1", "2"):
                _mac_nic = "vmxnet3"
                _mac_nic_note = "vmxnet3 (High Sierra/Mojave: sin driver virtio-net)"
            else:
                _mac_nic = "virtio-net-pci"
                _mac_nic_note = "virtio-net-pci"
            self.log_signal.emit(
                f"==> macOS: red NAT con {_mac_nic_note}."
            )
            # netdev_user_dns_v1: forzamos dns=10.0.2.3 explícitamente.
            # Algunos guests ignoran el DNS que QEMU sirve por DHCP
            # interno de slirp y quedan sin resolver nombres aunque
            # la red funcione.
            # macos_mac_uniqueness_v1: MAC unica y persistente por VM.
            # La MAC fija 52:54:00:c9:18:27 chocaba si varias VMs
            # macOS corrian en la misma LAN slirp/bridge. Se guarda en
            # extra["macos_nic_mac"] y se reutiliza en cada arranque.
            _mac_mac = str(self.extra_params.get("macos_nic_mac") or "").strip()
            _mac_valid = bool(re.match(
                r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", _mac_mac
            ))
            if not _mac_valid:
                _u = uuid.uuid4().bytes
                _mac_mac = "52:54:00:%02x:%02x:%02x" % (_u[0], _u[1], _u[2])
                try:
                    self._write_extra_extra_keys(macos_nic_mac=_mac_mac)
                    self.log_signal.emit(
                        f"==> macOS: MAC nueva asignada y guardada: {_mac_mac}"
                    )
                except Exception as _mac_err:
                    self.log_signal.emit(
                        f"[AVISO] macOS: no se pudo persistir la MAC "
                        f"({_mac_err}); se usara solo en este arranque."
                    )
            else:
                self.log_signal.emit(
                    f"==> macOS: MAC recuperada de la config: {_mac_mac}"
                )
            network_args = (
                f"-netdev user,id=net0,dns=10.0.2.3 "
                f"-device {_mac_nic},netdev=net0,id=net0,mac={_mac_mac}"
            )
            # macos_pcap_debug_v1: con MACOS_PCAP_DEBUG=1 se guarda el trafico de la VM
            # en /tmp/vm-net.pcap (diagnostico de red; desactivado por defecto).
            import os as _os_pcap
            if _os_pcap.environ.get("MACOS_PCAP_DEBUG") == "1":
                network_args += (
                    " -object filter-dump,id=fdump0,netdev=net0,"
                    "file=/tmp/vm-net.pcap"
                )
            # NO activar +invtsc: QEMU lo expone como un dispositivo CPU no migrable
            # y bloquea los snapshots completos (savevm/snapshot-save) con:
            # "State blocked by non-migratable CPU device (invtsc flag)".
            # vmware-cpuid-freq mantiene la presentación de frecuencia esperada por macOS.
            # macos_cpu_model_v1: respetar la eleccion del usuario en
            # Configuracion -> Procesador. En "auto" se mantiene el
            # modelo recomendado por OSX-KVM segun la version (Penryn
            # para las antiguas, Skylake-Client para Sequoia/Tahoe).
            _auto_cpu_macos = (
                "Skylake-Client,-hle,-rtm,kvm=on,vendor=GenuineIntel,vmware-cpuid-freq=on"
                if str(os_choice) in ("8", "9")
                else "Penryn,kvm=on,vendor=GenuineIntel,vmware-cpuid-freq=on"
            )
            _user_cpu = str(self.extra_params.get("cpu_model") or "auto").strip()
            if not _user_cpu or _user_cpu.lower() == "auto":
                cpu_model = _auto_cpu_macos
            elif _user_cpu.lower() == "host":
                cpu_model = "host,kvm=on"
                self.log_signal.emit(
                    "==> macOS: CPU = host (maximo rendimiento, no "
                    "portable a otros hosts con CPU distinta)."
                )
            else:
                cpu_model = _user_cpu
                self.log_signal.emit(
                    f"==> macOS: CPU elegida por el usuario: {cpu_model}"
                )
            my_options = "+ssse3,+sse4.2,+popcnt,+avx,+aes,+xsave,+xsaveopt,check"
            qmp_path = os.path.join(self.vm_dir, "qemu.qmp")
            pid_path = os.path.join(self.vm_dir, "qemu.pid")

            # macos_graphics_guard_v1
            # 1) VirGL y Venus requieren un backend de display con
            #    gl=on (gtk/sdl). En macOS no lo usamos (VNC embebido
            #    o ventana nativa sin GL). Si el .ini trae virgl/venus
            #    se degrada a auto con aviso claro, en lugar de
            #    mandar a QEMU un -device virtio-vga-gl sin display GL
            #    que abortaria el arranque.
            mode = self.graphics_mode or "auto"
            if mode in ("virgl", "venus"):
                self.log_signal.emit(
                    f"[AVISO] macOS: '{mode}' no es compatible "
                    "(necesita un backend de pantalla con OpenGL "
                    "activo, y macOS no lo usa). Se arrancara con "
                    "'auto'."
                )
                mode = "auto"

            # 2) VRAM: usar el valor del combo grafico si es un tamano
            #    valido. macOS/OpenCore se comporta mejor en 128 MB;
            #    el rango seguro es 32..512 MB.
            try:
                _vram_txt = str(self.graphics_vram or "").strip().upper()
                if _vram_txt.endswith("M"):
                    _vram_mb = int(_vram_txt[:-1])
                elif _vram_txt.endswith("G"):
                    _vram_mb = int(_vram_txt[:-1]) * 1024
                else:
                    _vram_mb = int(_vram_txt)
            except Exception:
                _vram_mb = 128
            _vram_mb = max(32, min(512, _vram_mb))

            if mode == "none":
                mac_graphics = "-vga none -display none"
            elif mode == "qxl":
                mac_graphics = "-vga qxl"
            elif mode in ("vmware", "vmware-svga"):
                mac_graphics = "-device vmware-svga"
            elif mode == "virtio":
                mac_graphics = "-device virtio-vga"
            else:
                # auto o cualquier otro valor -> VGA de OSX-KVM.
                mac_graphics = f"-device VGA,vgamem_mb={_vram_mb}"

            self.log_signal.emit(f"==> macOS: CPU {cpu_model.split(',')[0]}, RAM {self.ram}, {self.cores} CPU(s).")
            if self._clipboard_enabled():
                self.log_signal.emit("==> macOS: clipboard pendiente de integración SPICE específica; no se fuerza en este arranque.")
            self.log_signal.emit(f"==> macOS: gráficos: {mode} (gestionados directamente por el administrador).")
            self.log_signal.emit(f"==> macOS: audio: {audio_backend.upper()}.")
            self.log_signal.emit("==> macOS: red NAT + VirtIO.")
            self.log_signal.emit("==> OVMF listo: CODE compartido + VARS exclusiva de esta VM.")
            self.log_signal.emit("==> OpenCore.qcow2: usando la imagen maestra en modo snapshot (sin copiarla).")

            # macos_basesystem_check_conditional_v1: el check del
            # script bash solo exige BaseSystem.img si el usuario
            # configuro la unidad de Recovery (o si hay un custom
            # image, que ya se verifico arriba). En el resto de
            # casos no se exige porque se arranca sin InstallMedia.
            if _has_base_system or _recovery_unit_configured or use_custom:
                _basesystem_check = (
                    f'if [ ! -s "{base_system}" ]; then '
                    f'echo "ERROR: BaseSystem.img no esta disponible: {base_system}"; '
                    f'exit 1; fi'
                )
            else:
                _basesystem_check = (
                    '# BaseSystem.img no requerido: se arranca sin InstallMedia.'
                )

            mac_disk = filename
            script_content = f'''#!/bin/bash
set -e
ulimit -l unlimited 2>/dev/null || true

echo "==> Creando/verificando disco virtual de macOS..."
{disk_cmd}

if [ ! -s "{code_path}" ]; then echo "ERROR: OVMF CODE no está disponible: {code_path}"; exit 1; fi
if [ ! -s "{vars_path}" ]; then echo "ERROR: OVMF VARS no está disponible: {vars_path}"; exit 1; fi
if [ ! -s "{source_opencore}" ]; then echo "ERROR: OpenCore.qcow2 no está disponible: {source_opencore}"; exit 1; fi
{_basesystem_check}

trap 'rm -f "{qmp_path}" "{pid_path}"' EXIT

echo "==> Lanzando macOS mediante QEMU interno del administrador..."
qemu-system-x86_64 \
    -enable-kvm \
    -m {self.ram} \
    -cpu {cpu_model},"{my_options}" \
    -machine q35 \
    {self._pointer_args()} \
    -smp {self.cores},cores={self.cores},threads=1,sockets=1 \
    -device isa-applesmc,osk="ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc" \
    -drive if=pflash,format=raw,readonly=on,file="{code_path}" \
    -drive if=pflash,format=raw,file="{vars_path}" \
    -smbios type=2 \
    {audio_args} {self._serial_args()} \
    -device ich9-ahci,id=sata \
    -drive id=OpenCoreBoot,if=none,snapshot=on,format=qcow2,file="{source_opencore}" \
    -device ide-hd,bus=sata.2,drive=OpenCoreBoot \
    -drive id=InstallMedia,if=none,file="{base_system}",format=raw \
    -device ide-hd,bus=sata.3,drive=InstallMedia \
    -drive id=MacHDD,if=none,file="{mac_disk}",format=qcow2 \
    -device ide-hd,bus=sata.4,drive=MacHDD \
    {network_args} \
    {mac_graphics} \
    {self._passthrough_args()} \
    -monitor stdio \
    -qmp unix:"{qmp_path}",server=on,wait=off &
QEMU_PID=$!
echo $QEMU_PID > "{pid_path}"
wait $QEMU_PID
'''

            # --- macos_extras_v1 ---
            # 1) Si no hay BaseSystem.img y no hay unidad de Recovery,
            #    quitar el bloque InstallMedia del comando QEMU.
            if not _has_base_system:
                script_content = script_content.replace(
                    f'-drive id=InstallMedia,if=none,file="{base_system}",format=raw',
                    '',
                )
                script_content = script_content.replace(
                    '-device ide-hd,bus=sata.3,drive=InstallMedia',
                    '',
                )
                self.log_signal.emit(
                    "==> macOS: BaseSystem.img no existe y no hay unidad "
                    "de Recovery configurada; se arranca sin InstallMedia."
                )

            # 2) Extras: CDs y discos adicionales del usuario.
            #    Van a un segundo controlador AHCI (id=sataext) para no
            #    chocar con los 3 puertos fijos de OSX-KVM (sata.2/3/4).
            _extras_parts = []
            # macos_extras_filter_v1: mismo filtro para los CDs;
            # BaseSystem.img ya vive en InstallMedia y no debe
            # adjuntarse por segunda vez.
            _reserved_paths_cd = set()
            for _rp in (mac_disk, base_system, source_opencore):
                if _rp:
                    try:
                        _reserved_paths_cd.add(os.path.abspath(_rp))
                    except Exception:
                        pass
            _cd_devs = [
                d for d in self._storage_devices_from_config()
                if d.get("device") == "cdrom"
                and str(d.get("source") or "") != "recovery"
                and d.get("path") and os.path.isfile(d.get("path"))
                and os.path.abspath(d.get("path")) not in _reserved_paths_cd
            ]
            # macos_extras_filter_v1: excluir de los extras cualquier
            # archivo que ya forme parte del bloque fijo de OSX-KVM
            # (OpenCore.qcow2, BaseSystem.img, mac_hdd_ng.qcow2). Si se
            # adjuntan dos veces, QEMU falla con 'Failed to get write
            # lock' (el InstallMedia ya abre BaseSystem.img).
            _reserved_paths = set()
            for _rp in (mac_disk, base_system, source_opencore):
                if _rp:
                    try:
                        _reserved_paths.add(os.path.abspath(_rp))
                    except Exception:
                        pass
            _extra_disks = [
                d for d in self._storage_devices_from_config()
                if d.get("device") in ("sata", "nvme")
                and d.get("path") and os.path.isfile(d.get("path"))
                and os.path.abspath(d.get("path")) not in _reserved_paths
            ]
            if _cd_devs or _extra_disks:
                _extras_parts.append("-device ich9-ahci,id=sataext")
                for _i, _d in enumerate(_cd_devs[:4]):
                    _cpath = _d["path"]
                    _cdrv = f"maccd{_i}"
                    _csafe = _qemu_safe_identifier(
                        _d.get("id") or f"mac_cd{_i}", "mac_cd"
                    )
                    _extras_parts.append(
                        f'-drive if=none,id={_cdrv},media=cdrom,'
                        f'readonly=on,file="{_cpath}"'
                    )
                    _extras_parts.append(
                        f'-device ide-cd,drive={_cdrv},'
                        f'bus=sataext.{_i},unit=0,id={_csafe}'
                    )
                _base_port = 4
                for _i, _d in enumerate(_extra_disks[:4]):
                    _dpath = _d["path"]
                    try:
                        _dinfo = subprocess.run(
                            ["qemu-img", "info", "--output=json", _dpath],
                            capture_output=True, text=True,
                            timeout=10, check=True,
                        )
                        _dfmt = json.loads(_dinfo.stdout).get("format", "qcow2")
                    except Exception:
                        _dfmt = "qcow2"
                    _ddrv = f"macextra{_i}"
                    _dsafe = _qemu_safe_identifier(
                        _d.get("id") or f"mac_extra{_i}", "mac_extra"
                    )
                    _extras_parts.append(
                        f'-drive file="{_dpath}",format={_dfmt},'
                        f'if=none,id={_ddrv}'
                    )
                    _extras_parts.append(
                        f'-device ide-hd,drive={_ddrv},id={_dsafe},'
                        f'bus=sataext.{_base_port + _i},unit=0'
                    )
                if _extras_parts:
                    _extras_text = " ".join(_extras_parts)
                    _machdd_anchor = '-device ide-hd,bus=sata.4,drive=MacHDD'
                    if _machdd_anchor in script_content:
                        script_content = script_content.replace(
                            _machdd_anchor,
                            _machdd_anchor + ' ' + _extras_text,
                            1,
                        )
                        self.log_signal.emit(
                            f"==> macOS: a\u00f1adidos {len(_cd_devs[:4])} "
                            f"CD(s) y {len(_extra_disks[:4])} disco(s) extra."
                        )
        elif self.os_type == "windows":
            cpu_arg = self._cpu_args()
            win_ver = self.extra_params.get("win_ver", "Windows 11")
            iso_path = vm_paths.to_absolute(
                self.vm_dir, self.extra_params.get("iso_path", "") or ""
            )
            auto_detect = self.extra_params.get("auto_detect", False)

            # Si el CD/DVD está configurado para instalador automático, la
            # descarga se realiza AHORA, al pulsar Iniciar, con barra de progreso.
            installer_path = self._download_installer_at_start("windows", win_ver=win_ver)
            if installer_path:
                iso_path = installer_path
                auto_detect = False

            if auto_detect:
                self.log_signal.emit(f"==> Buscando la última ISO retail de {win_ver} vía Fido...")
                try:
                    iso_path = get_latest_windows_iso_url(win_ver)
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] No se pudo detectar la ISO de {win_ver}: {e}")
                    self.finished_signal.emit(1)
                    return
                self.log_signal.emit(f"==> URL detectada: {iso_path}")

            iso_local = iso_path
            if auto_detect:
                # Compatibilidad con la opción antigua de autodetección: también
                # descarga dentro del worker, con la misma barra de progreso.
                url = iso_path
                iso_local = os.path.join(self.vm_dir, "windows_downloaded.iso")
                if not (os.path.isfile(iso_local) and os.path.getsize(iso_local) > 0):
                    self._download_file_with_progress(
                        url, iso_local, f"Descargando instalador de {win_ver}"
                    )
                self.log_signal.emit(f"==> ISO de Windows lista: {iso_local}")
            download_block = ""

            try:
                firmware_args = self._uefi_args()
                tpm_cmd, tpm_args = self._tpm_args()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] {e}")
                self.finished_signal.emit(1)
                return
            boot_index_network = self._boot_index_for("network")
            disk_args = self._disk_runtime_args()
            cdrom_args = self._cdrom_runtime_args(iso_local)
            self.log_signal.emit("==> Orden de arranque: " + " → ".join(self._boot_token_label(x) for x in self.boot_order))
            try:
                audio_backend, audio_args = self._audio_args()
                graphics_args, graphics_note = self._graphics_args()
                self._prepare_tap_interfaces()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Audio/Gráficos: {e}")
                self.finished_signal.emit(1)
                return
            self.log_signal.emit(f"==> Gráficos: {graphics_note}")
            self.log_signal.emit(f"==> Audio: backend {audio_backend.upper()}.")
            secure_note = " + Secure Boot" if self.secure_boot else ""
            tpm_note = " + TPM 2.0" if self.tpm else ""
            socket_path = os.path.join(self.vm_dir, "swtpm.sock")
            qmp_path = os.path.join(self.vm_dir, "qemu.qmp")
            pid_path = os.path.join(self.vm_dir, "qemu.pid")
            clipboard_args, clipboard_note = self._clipboard_qemu_args()
            if clipboard_note:
                self.log_signal.emit("==> " + clipboard_note)
            script_content = f'''#!/bin/bash
ulimit -l unlimited 2>/dev/null || true
set -e
{download_block}
echo "==> Creando disco virtual para {win_ver}..."
{disk_cmd}
{tpm_cmd}
trap 'rm -f "{socket_path}" "{qmp_path}" "{pid_path}"' EXIT
echo "==> Iniciando QEMU para Windows ({self.firmware.upper()}{secure_note}{tpm_note})..."
qemu-system-x86_64 -enable-kvm {self.chipset_args} -m {self.ram} -smp {self.cores} \
    -cpu {cpu_arg} -smp cores={self.cores},threads=1 \
    {disk_args} \
    {firmware_args} {tpm_args} {audio_args} {graphics_args} {clipboard_args} {self._passthrough_args()} \
    {self._serial_args()} {cdrom_args} {self._network_args(boot_index_network)} \
    -qmp unix:"{qmp_path}",server=on,wait=off &
QEMU_PID=$!
echo $QEMU_PID > "{pid_path}"
wait $QEMU_PID
'''
        elif self.os_type == "android":
            # Android-x86 / Bliss OS — flujo simplificado:
            #   • BIOS + Q35 (arranca sin problemas con GRUB del instalador).
            #   • Disco SATA/AHCI (lo resuelve _resolve_disk_bus_for_os).
            #   • Red e1000 en NAT (compatible sin drivers extra).
            #   • Gráficos VirtIO-GPU 2D (lo resuelve _graphics_args).
            #   • La ISO de instalación viene del CD/DVD Principal que el
            #     usuario configuró en Almacenamiento.
            android_iso = vm_paths.to_absolute(
                self.vm_dir, str(self.extra_params.get("android_iso") or "").strip()
            )
            if not android_iso or not os.path.isfile(android_iso):
                self.log_signal.emit(
                    "[ERROR] Android: no hay ISO configurada. Ve a "
                    "Configuración → Almacenamiento y añade la ISO de "
                    "Android-x86 o Bliss OS como unidad CD/DVD, o "
                    "selecciónala en Plataforma → Android."
                )
                self.finished_signal.emit(1)
                return

            try:
                firmware_args = self._uefi_args() if self.firmware == "uefi" else ""
                tpm_cmd, tpm_args = ("", "")  # Android no usa TPM
            except Exception as e:
                self.log_signal.emit(f"[ERROR] {e}")
                self.finished_signal.emit(1)
                return

            boot_index_network = self._boot_index_for("network")
            disk_args = self._disk_runtime_args()
            # El CD/DVD con la ISO de Android: reutilizamos el mismo
            # constructor que Linux/Windows, pasando la ISO como path
            # directo por si la unidad Principal no la tiene registrada.
            cdrom_args = self._cdrom_runtime_args(android_iso)
            self.log_signal.emit(
                "==> Orden de arranque: "
                + " → ".join(self._boot_token_label(x) for x in self.boot_order)
            )
            try:
                audio_backend, audio_args = self._audio_args()
                graphics_args, graphics_note = self._graphics_args()
                self._prepare_tap_interfaces()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Audio/Gráficos: {e}")
                self.finished_signal.emit(1)
                return
            self.log_signal.emit(f"==> Gráficos: {graphics_note}")
            self.log_signal.emit(f"==> Audio: backend {audio_backend.upper()}.")
            self.log_signal.emit(f"==> Android: ISO de instalación: {os.path.basename(android_iso)}")

            socket_path = os.path.join(self.vm_dir, "swtpm.sock")
            qmp_path = os.path.join(self.vm_dir, "qemu.qmp")
            pid_path = os.path.join(self.vm_dir, "qemu.pid")
            cpu_arg = self._cpu_args()
            clipboard_args, clipboard_note = self._clipboard_qemu_args()
            if clipboard_note:
                self.log_signal.emit("==> " + clipboard_note)
            script_content = f'''#!/bin/bash
ulimit -l unlimited 2>/dev/null || true
set -e
echo "==> Creando disco virtual para Android..."
{disk_cmd}
{tpm_cmd}
trap 'rm -f "{socket_path}" "{qmp_path}" "{pid_path}"' EXIT
echo "==> Iniciando QEMU para Android ({self.firmware.upper()})..."
qemu-system-x86_64 -enable-kvm {self.chipset_args} -m {self.ram} -smp {self.cores} \\
    -cpu {cpu_arg} {disk_args} \\
    {firmware_args} {tpm_args} {audio_args} {graphics_args} {clipboard_args} {self._passthrough_args()} \\
    {self._serial_args()} {cdrom_args} {self._network_args(boot_index_network)} \\
    -qmp unix:"{qmp_path}",server=on,wait=off &
QEMU_PID=$!
echo $QEMU_PID > "{pid_path}"
wait $QEMU_PID
'''
        else:  # Linux
            distro = self.extra_params.get("distro", "Linux")
            # La ISO se administra exclusivamente como dispositivo CD/DVD.
            # Si la unidad está marcada como "installer", se descarga al iniciar.
            installer_path = self._download_installer_at_start(
                "linux", distro=distro, distro_version=self.extra_params.get("distro_version", ""))
            iso_handling_script = 'ISO_FINAL=""'

            try:
                firmware_args = self._uefi_args()
                tpm_cmd, tpm_args = self._tpm_args()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] {e}")
                self.finished_signal.emit(1)
                return
            boot_index_network = self._boot_index_for("network")
            disk_args = self._disk_runtime_args()
            cdrom_args = self._cdrom_runtime_args("$ISO_FINAL")
            self.log_signal.emit("==> Orden de arranque: " + " → ".join(self._boot_token_label(x) for x in self.boot_order))
            try:
                audio_backend, audio_args = self._audio_args()
                graphics_args, graphics_note = self._graphics_args()
                self._prepare_tap_interfaces()
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Audio/Gráficos: {e}")
                self.finished_signal.emit(1)
                return
            self.log_signal.emit(f"==> Gráficos: {graphics_note}")
            self.log_signal.emit(f"==> Audio: backend {audio_backend.upper()}.")
            secure_note = " + Secure Boot" if self.secure_boot else ""
            tpm_note = " + TPM 2.0" if self.tpm else ""
            socket_path = os.path.join(self.vm_dir, "swtpm.sock")
            qmp_path = os.path.join(self.vm_dir, "qemu.qmp")
            pid_path = os.path.join(self.vm_dir, "qemu.pid")
            cpu_arg = self._cpu_args()
            clipboard_args, clipboard_note = self._clipboard_qemu_args()
            if clipboard_note:
                self.log_signal.emit("==> " + clipboard_note)
            script_content = f'''#!/bin/bash
ulimit -l unlimited 2>/dev/null || true
set -e
{iso_handling_script}
echo "==> Creando disco virtual para {distro}..."
{disk_cmd}
{tpm_cmd}
trap 'rm -f "{socket_path}" "{qmp_path}" "{pid_path}"' EXIT
echo "==> Iniciando QEMU para {distro} ({self.firmware.upper()}{secure_note}{tpm_note})..."
qemu-system-x86_64 -enable-kvm {self.chipset_args} -m {self.ram} -smp {self.cores} \
    -cpu {cpu_arg} {disk_args} \
    {firmware_args} {tpm_args} {audio_args} {graphics_args} {clipboard_args} {self._passthrough_args()} \
    {self._serial_args()} {self._cdrom_runtime_args("$ISO_FINAL")} {self._network_args(boot_index_network)} \
    -qmp unix:"{qmp_path}",server=on,wait=off &
QEMU_PID=$!
echo $QEMU_PID > "{pid_path}"
wait $QEMU_PID
'''

        # QEMU Guest Agent: se habilita desde Integración Host ↔ Guest o automáticamente
        # cuando una carpeta compartida solicita montaje al iniciar. El socket lo atiende QEMU
        # y qemu-guest-agent debe estar instalado y ejecutándose en el sistema invitado.
        qga_path = os.path.join(self.vm_dir, "qga.sock")
        qga_enabled = bool((self.extra_params or {}).get("guest_agent_enabled", False))
        qga_needed = qga_enabled or (self.os_type == "linux" and any(
            isinstance(d, dict) and str(d.get("mount_mode","manual")).lower()=="auto_start"
            and str(d.get("method") or "auto").lower() in ("auto","virtiofs")
            for d in self.shared_folders
        ))
        # Construimos todos los argumentos auxiliares antes de tocar la línea de QEMU.
        # Importante: QGA y VirtioFS deben insertarse juntos delante de -qmp. Si se
        # hacen reemplazos consecutivos sobre el mismo marcador, el primer reemplazo
        # elimina el marcador y el segundo (VirtioFS) nunca llega al comando QEMU.
        qga_args = ""
        if qga_needed:
            qga_args = (
                f'-chardev socket,id=qga0,path="{qga_path}",server=on,wait=off '
                '-device virtio-serial -device virtserialport,chardev=qga0,name=org.qemu.guest_agent.0'
            )

        try:
            shared_qemu, shared_start, shared_cleanup = self._shared_folder_args()
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Carpetas compartidas: {e}")
            self.finished_signal.emit(1)
            return

        # Consola gráfica: VNC o SPICE, embebida o externa.
        # Siempre usamos socket Unix (más seguro que TCP; solo usuarios
        # locales con permisos sobre el socket pueden conectarse).
        console_args, console_info = self._console_args()
        vnc_socket = console_info.get("socket") or _cb_socket_path(
            self.vm_dir, self.console_protocol
        )
        if console_args:
            self.log_signal.emit(
                f"==> Consola gráfica: {self.console_protocol.upper()} "
                f"({self.console_mode}) en {vnc_socket}."
            )
            # Si el puerto SPICE no fue el preferido 5930, avisar.
            _note = console_info.get("port_note")
            if _note:
                self.log_signal.emit(f"==> {_note}")
        pre_qmp = " ".join(x for x in (shared_qemu, qga_args, console_args) if x)
        if pre_qmp:
            script_content, ok = self._insert_pre_qmp_args(script_content, pre_qmp)
            if not ok:
                self.log_signal.emit("[ERROR] No se encontró el punto de inserción de QEMU (-qmp).")
                self.finished_signal.emit(1)
                return

        if shared_start:
            script_content = script_content.replace("set -e\n", "set -e\n" + shared_start + "\n", 1)

        cleanup_parts = []
        if shared_cleanup:
            cleanup_parts.append(shared_cleanup)
        if qga_needed:
            cleanup_parts.append(f'rm -f "{qga_path}"')
        # Socket VNC: se elimina siempre al cerrar QEMU, para que la próxima
        # ejecución no encuentre un socket huérfano bloqueando el arranque.
        cleanup_parts.append(f'rm -f "{vnc_socket}"')
        # SPICE también deja su socket si alguna vez se usó; limpiar ambos.
        cleanup_parts.append(f'rm -f {shlex.quote(os.path.join(self.vm_dir, "qemu.spice.sock"))}')
        if cleanup_parts:
            script_content = self._insert_cleanup_trap(script_content, "; ".join(cleanup_parts))
        exec_path = os.path.join(self.vm_dir, "run_temp.sh")
        # Antes de sobrescribir, guardar el anterior con timestamp.
        # Si QEMU falla justo después, este backup permite ver qué
        # script se ejecutó exactamente.
        self._backup_existing_run_script(exec_path)
        with open(exec_path, "w") as f:
            f.write(script_content)
        os.chmod(exec_path, 0o755)

        launch_cmd = self._build_launch_command(exec_path)
        process = subprocess.Popen(launch_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            self.log_signal.emit(line.strip())
        process.wait()
        self.finished_signal.emit(process.returncode)




def _qemu_safe_identifier(value: str, prefix: str = "dev") -> str:
    """Return an identifier accepted by QEMU: starts with a letter and then uses A-Z/a-z/0-9/_/-."""
    raw = str(value or "")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", raw)
    if not safe:
        safe = prefix
    if not safe[0].isalpha():
        safe = prefix + "_" + safe
    return safe[:127]


class SnapshotOperationWorker(QThread):
    """Ejecuta snapshot-save/load fuera del hilo de la interfaz para que la GUI no se congele."""
    log_signal = pyqtSignal(str)
    success_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, app, vm_dir, command, arguments, operation_label, timeout=900, parent=None):
        super().__init__(parent)
        self.app = app
        self.vm_dir = vm_dir
        self.command = command
        self.arguments = arguments
        self.operation_label = operation_label
        self.timeout = timeout

    def run(self):
        try:
            result = self.app._qmp_launch_snapshot_job(
                self.vm_dir, self.command, self.arguments, self.operation_label,
                timeout=self.timeout, log_callback=self.log_signal.emit
            )
            self.success_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class _BackgroundCallThread(QThread):
    """Ejecuta una función potencialmente bloqueante fuera del hilo de la UI.

    La función recibe `log_emit(str)` y opcionalmente `is_cancelled()` y
    `progress_emit(int, str)` si acepta más argumentos. Consulta
    is_cancelled() en puntos seguros (bucles de descarga, conversiones) para
    abortar cooperativamente. Usa progress_emit(pct, texto) para reflejar el
    avance en el diálogo.
    """
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)
    done_signal = pyqtSignal(object, object)  # (result, error)

    def __init__(self, func, parent=None):
        super().__init__(parent)
        self._func = func
        self._cancel_flag = threading.Event()

    def request_cancel(self):
        self._cancel_flag.set()

    def is_cancelled(self):
        return self._cancel_flag.is_set()

    def run(self):
        try:
            try:
                result = self._func(self.log_signal.emit, self.is_cancelled, self.progress_signal.emit)
            except TypeError:
                try:
                    result = self._func(self.log_signal.emit, self.is_cancelled)
                except TypeError:
                    result = self._func(self.log_signal.emit)
            self.done_signal.emit(result, None)
        except Exception as e:
            self.done_signal.emit(None, e)

