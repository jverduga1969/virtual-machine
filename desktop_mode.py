#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
"""
Desktop Mode para Virtual.Machine  (marcador: desktop_mode_v1)

Arranca una VM Linux a pantalla completa sobre un TTY dedicado usando:

    openvt -> setpriv -> seatd -> cage -m last -> QEMU -> guest

Uso normal (desde KDE, en tu terminal habitual):

    python3 desktop_mode.py --vm "Linux Mint"
    python3 desktop_mode.py --vm "Linux Mint" --tty 3 --monitor last
    python3 desktop_mode.py --vm "Linux Mint" --dry-run
    python3 desktop_mode.py --vm "Linux Mint" --snapshot

Modo interno (lo invoca el wrapper sudo desde dentro de cage):

    python3 desktop_mode.py --inside-cage --vm-dir "/path/al/vm_dir"

El script NO modifica virtual_machine.py ni la configuración de la app.
Reutiliza InstallWorker de workers.py con console_mode=native para que
QEMU abra su ventana GTK/SDL en lugar de -display none + VNC socket.

Requiere:
  - /usr/local/bin/virtual-machine-desktop (wrapper sudo, ver README)
  - /etc/sudoers.d/virtual-machine-desktop con NOPASSWD al wrapper
  - seatd.service corriendo (systemctl start seatd)
  - grupo 'seat' existente en el sistema
"""

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# --- Localizar el repo por si el script se mueve ---
REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))


# --- Constantes de la cadena Desktop ---
SUDO_WRAPPER = "/usr/local/bin/virtual-machine-desktop"
DEFAULT_TTY = 3
DEFAULT_MONITOR = "last"
VALID_MONITORS = ("last", "extend")


# ----------------------------------------------------------------------
# Modo interno: ejecutado DENTRO de cage
# ----------------------------------------------------------------------
def _ensure_qcore_app():
    """Crea un QCoreApplication mínimo si no existe.

    InstallWorker es un QThread y sus señales funcionan sin bucle de
    eventos (conexiones directas), pero PyQt6 espera que exista una
    instancia de QCoreApplication para inicializar correctamente el
    runtime interno. NO llamamos a exec(): solo la creamos.
    """
    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv[:1])
    return app


def _find_system_disk(vm_dir, storage_devices):
    """Devuelve la ruta absoluta del disco de sistema de la VM.

    Prioriza el primer storage_device con device en (sata,nvme,floppy).
    Si no hay, cae a buscar hd_*.qcow2 / disk_*.qcow2 en la carpeta.
    """
    for d in storage_devices or []:
        if d.get("device") in ("sata", "nvme", "floppy"):
            p = d.get("path") or ""
            if not p:
                continue
            if not os.path.isabs(p):
                p = os.path.join(str(vm_dir), p)
            if os.path.isfile(p):
                return p
    # Fallback: patrón de nombre.
    for f in sorted(os.listdir(vm_dir)):
        if f.startswith(("hd_", "disk_", "vm_disk.")) and \
           f.endswith((".qcow2", ".img", ".raw")):
            return os.path.join(str(vm_dir), f)
    return None


def _build_worker_kwargs(cfg, extra, vm_dir, snapshot=False):
    """Mapea vm_config.ini + extra al constructor de InstallWorker.

    Fuerza console_mode=native para que QEMU abra ventana GTK/SDL
    en lugar de -display none + -vnc unix:...

    El flag `snapshot` NO se pasa como kwarg a InstallWorker (no lo
    conoce). Se pasa via extra["_qemu_snapshot"], que el wrapper
    post-proceso del script usará para añadir -snapshot. Como aquí
    NO hacemos post-proceso (dejamos que InstallWorker ejecute QEMU
    directo), el snapshot se aplica parcheando el script generado
    justo antes de que InstallWorker lo ejecute... pero eso es feo.

    Mejor: dejar que el usuario que quiera probar con -snapshot
    lo haga con un alias temporal de qemu-system-x86_64 en PATH.
    Ver _install_qemu_snapshot_alias() más abajo.
    """
    extra = dict(extra)  # copia: NO mutamos el dict del .ini
    extra["console_mode"] = "native"
    # clipboard_desktop_spice_v1: Desktop Mode usa SPICE via
    # remote-viewer, NO VNC. Declararlo "spice" hace que el
    # chardev de clipboard (parcheado abajo) sea spicevmc y no
    # qemu-vdagent, que solo sirve para VNC.
    extra["console_protocol"] = "spice"
    extra["vnc_embedded"] = False
    extra["chipset"] = cfg.get("chipset", "q35")

    disk_path = _find_system_disk(vm_dir, extra.get("storage_devices", []))
    if not disk_path:
        raise SystemExit(
            f"[ERROR] No se encontró disco de sistema en {vm_dir}."
        )

    return {
        "os_type":          cfg.get("os_type", "linux"),
        "ram":              cfg.get("ram", "4G"),
        "cores":            int(cfg.get("cores", 2)),
        "disk_size":        cfg.get("disk_size", "60G"),
        "disk_type":        cfg.get("disk_type", "dynamic"),
        "disk_format":      cfg.get("disk_format", "qcow2"),
        "disk_ext":         cfg.get("disk_ext", "qcow2"),
        "firmware":         cfg.get("firmware", "uefi"),
        "secure_boot":      bool(cfg.get("secure_boot", False)),
        "tpm":              bool(cfg.get("tpm", False)),
        "boot_device":      cfg.get("boot_device", "disk"),
        "network_model":    cfg.get("network_model", "virtio-net-pci"),
        "audio_device":     cfg.get("audio_device", "intel-hda"),
        "network_mode":     cfg.get("network_mode", "nat"),
        "network_interface": cfg.get("network_interface", ""),
        "network_count":    int(cfg.get("network_count", 1)),
        "graphics_mode":    cfg.get("graphics_mode", "auto"),
        "graphics_vram":    cfg.get("graphics_vram", "256M"),
        "extra_params":     extra,
        "vm_dir":           str(vm_dir),
        "disk_path":        disk_path,
        "skip_disk_create": True,
        "boot_order":       cfg.get("boot_order", ["disk", "cdrom", "network"]),
        "network_devices":  cfg.get("network_devices", []),
        "passthrough_devices": cfg.get("passthrough_devices", []),
    }


def _check_tmp_space_for_snapshot(min_gb=3):
    """Avisa si /var/tmp (o TMPDIR) tiene poco espacio para -snapshot.

    QEMU en modo -snapshot escribe los bloques modificados a archivos
    temporales en TMPDIR (por defecto /var/tmp). Con poco espacio,
    la VM aborta con "No space left on device".

    Devuelve True si hay espacio suficiente, False si conviene abortar.
    """
    import shutil as _sh
    import os as _os
    tmpdir = _os.environ.get("TMPDIR") or "/var/tmp"
    try:
        free = _sh.disk_usage(tmpdir).free
    except Exception:
        return True
    free_gb = free / (1024 ** 3)
    if free_gb < min_gb:
        print(
            f"[AVISO] -snapshot escribira los cambios en {tmpdir}, que "
            f"solo tiene {free_gb:.1f} GB libres.\n"
            f"        Si la VM escribe mas de eso, QEMU abortara con "
            f"'No space left on device'.\n"
            f"        Puedes cambiar TMPDIR a un disco con mas espacio "
            f"o hacer una copia de seguridad del qcow2 en su lugar.",
            flush=True,
        )
        return False
    print(
        f"==> Desktop Mode: -snapshot usara {tmpdir} "
        f"({free_gb:.1f} GB libres).",
        flush=True,
    )
    return True


def _patch_installworker_for_snapshot(InstallWorker):
    """Monkey-patch _build_launch_command para inyectar -snapshot.

    Marcador: desktop_mode_snapshot_v1

    InstallWorker._run_impl() escribe run_temp.sh y LUEGO llama a
    _build_launch_command(exec_path) para construir el argv que lo
    ejecutara. En ese hueco, leemos el script, insertamos -snapshot
    en la linea de qemu-system-x86_64 y lo guardamos.
    """
    _orig = InstallWorker._build_launch_command

    def _build_launch_command_snapshot(self, exec_path):
        import re as _re
        try:
            with open(exec_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content, n = _re.subn(
                r"(?m)^(\s*qemu-system-x86_64\s+)",
                r"\1-snapshot ",
                content,
                count=1,
            )
            if n == 0:
                self.log_signal.emit(
                    "[AVISO] --snapshot solicitado pero no se encontro "
                    "la linea 'qemu-system-x86_64' en run_temp.sh. "
                    "Se arrancara SIN -snapshot."
                )
            else:
                with open(exec_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.log_signal.emit(
                    "==> Desktop Mode: -snapshot inyectado en run_temp.sh. "
                    "Los cambios en los discos se descartaran al salir."
                )
        except Exception as e:
            self.log_signal.emit(
                f"[AVISO] --snapshot: no se pudo parchear run_temp.sh: {e}"
            )
        return _orig(self, exec_path)

    InstallWorker._build_launch_command = _build_launch_command_snapshot


def _patch_installworker_for_desktop(InstallWorker):
    """Monkey-patch de _graphics_args para forzar pantalla completa.

    Marcador: desktop_mode_xorg_vt_v1

    Comportamiento segun la variable de entorno VM_DESKTOP_MODE_FULLSCREEN:
      - "1": -display sdl  (Xorg dedicado).
        No hay WM, asi que QEMU puede pedir fullscreen sin romper nada.
      - sin definir: -display sdl (cage nested windowed, comportamiento
        heredado; pedir fullscreen ahi rompia la conexion Wayland de GTK).

    NO se modifica workers.py: el patch es solo en runtime.
    """
    # desktop_mode_xorg_vt_v11: fullscreen SOLO cuando hay un WM
    # dentro del Xorg :1 (matchbox). Sin WM, GTK cae a un camino
    # alternativo que pide un VT switch y logind mata Xorg. Con WM,
    # GTK negocia _NET_WM_STATE_FULLSCREEN con el WM y no toca la VT.
    _orig = InstallWorker._graphics_args

    def _graphics_args_desktop(self):
        # desktop_mode_spice_v1: en Desktop Mode usamos SPICE, no VNC.
        # Ventajas frente a VNC:
        #   - remote-viewer reescala automaticamente cuando cambia la
        #     resolucion del guest (vncviewer 1.13.1 no tiene escalado
        #     y deja bordes negros).
        #   - Clipboard bidireccional con spice-vdagent en el guest.
        #   - Funciona por socket Unix, igual que VNC.
        # Ademas evitamos el bug de QEMU 8.2 con backends GTK/SDL (el
        # main loop se congela y QMP deja de responder).
        #
        # desktop_mode_edid_guest_res_v1: pasamos la resolucion de la
        # VT al guest via EDID (xres/yres de virtio-vga). Asi el guest
        # arranca ya a la misma resolucion que la VT.
        #
        # IMPORTANTE: el path de la VM puede tener espacios
        # ("Linux Mint"). QEMU parsea la coma como separador de
        # opciones dentro de -spice, asi que las comillas dobles deben
        # envolver TODO el argumento, no solo el path:
        #   -spice "unix=on,addr=/path con espacios/qemu.spice.sock,..."
        import re as _re
        args, note = _orig(self)
        # Quitar -display X (gtk/sdl/none) que pudiera venir del worker.
        args = _re.sub(r"-display\s+\S+", "", args).strip()
        # Quitar -vnc (por si el worker lo emitiera por defecto).
        args = _re.sub(r"-vnc\s+\S+", "", args).strip()
        # EDID: inyectar xres/yres en virtio-vga (o virtio-vga-gl).
        _xres = os.environ.get("VM_DESKTOP_XRES", "")
        _yres = os.environ.get("VM_DESKTOP_YRES", "")
        if _xres and _yres and "xres=" not in args:
            if "-device virtio-vga-gl" in args:
                args = args.replace(
                    "-device virtio-vga-gl",
                    "-device virtio-vga-gl,xres=" + _xres + ",yres=" + _yres,
                    1,
                )
            elif "-device virtio-vga" in args:
                args = args.replace(
                    "-device virtio-vga",
                    "-device virtio-vga,xres=" + _xres + ",yres=" + _yres,
                    1,
                )
        spice_sock = os.path.join(self.vm_dir, "qemu.spice.sock")
        args = ("-display none -spice \"unix=on,addr=" + spice_sock
                + ",disable-ticketing=on\" " + args).strip()
        return args, note + " [desktop: SPICE en socket local, EDID a VT]"

    # desktop_mode_spice_audio_v1: cuando corremos en Desktop Mode con
    # SPICE, el audio tambien debe ir por SPICE (no por PipeWire/Pulse
    # del host). Asi remote-viewer reproduce el sonido del guest en el
    # host sin depender de que PipeWire/PulseAudio este corriendo ni
    # de que el backend del host lo soporte.
    #
    # Sintaxis: -audiodev spice,id=audio0 + tarjeta HDA del guest.
    # remote-viewer abre un canal de audio SPICE y lo reproduce.
    _orig_audio = InstallWorker._audio_args

    def _audio_args_desktop(self):
        # desktop_mode_audio_dmix_v1_12
        #
        # QEMU escribe al plugin dmix de ALSA, que COMPARTE el
        # hardware con cualquier otro cliente (PipeWire incluido).
        #
        # Por que dmix y no plughw/pa/pipewire:
        #   - plughw: bloquea el hardware. Cinnamon se queda sin
        #     audio mientras la VM esta en Desktop Mode.
        #   - pa/pipewire: WirePlumber reasigna el stream al Dummy
        #     Output cuando la VT activa no es la del escritorio,
        #     y no podemos evitarlo desde QEMU.
        #   - dmix: escribe directo al device ALSA compartido. No
        #     pasa por PipeWire, asi que no le afecta su politica
        #     de sesion. Y no bloquea: PipeWire puede seguir
        #     escribiendo a dmix en paralelo.
        #
        # Sintaxis QEMU: las comas internas del device se escapan
        # con doble coma (,,). dmix:CARD=PCH,DEV=0 ->
        # dmix:CARD=PCH,,DEV=0.
        if str(getattr(self, "audio_device", "")).lower() in (
                "none", "off", "disabled"):
            return "none", ""
        device_args = "-device AC97,audiodev=audio0"
        return "alsa", (
            "-audiodev alsa,id=audio0,out.dev=dmix:CARD=PCH,,DEV=0 "
            + device_args
        )

    InstallWorker._audio_args = _audio_args_desktop

    # clipboard_desktop_spice_v1: el display real en Desktop Mode es
    # SPICE (lo arma _graphics_args_desktop con -display none -spice
    # unix:...). El chardev correcto de clipboard es por tanto
    # spicevmc, no qemu-vdagent. Como _clipboard_qemu_args de
    # workers solo conoce console_mode=native (que devuelve "" para
    # no interferir con -display gtk), lo sustituimos aqui por una
    # version que siempre emite spicevmc cuando el clipboard esta
    # activo.
    def _clipboard_qemu_args_desktop(self):
        if not self._clipboard_enabled():
            return "", ""
        if self.os_type == "macos":
            return "", (
                "[AVISO] Clipboard: macOS no soporta clipboard SPICE "
                "(no existe spice-vdagent para macOS). Se omite el canal."
            )
        if self.os_type == "android":
            return "", (
                "[AVISO] Clipboard: Android no soporta clipboard SPICE. "
                "Se omite el canal."
            )
        return (
            '-chardev spicevmc,id=vdagent0,name=vdagent '
            '-device virtio-serial '
            '-device virtserialport,chardev=vdagent0,name=com.redhat.spice.0',
            "==> Clipboard: SPICE vdagent en Desktop Mode. El guest "
            "necesita spice-vdagent instalado (Linux) o SPICE Guest "
            "Tools (Windows).",
        )

    InstallWorker._clipboard_qemu_args = _clipboard_qemu_args_desktop

    InstallWorker._graphics_args = _graphics_args_desktop


def _detect_graphical_tty():
    """Numero de TTY de la sesion grafica del host (KDE/GNOME), o None.

    Marcador: desktop_mode_tty_guard_v1

    Busca la primera sesion de logind con TTY asignada y Type distinto
    de 'tty' (wayland/x11/mir). Es la VT del escritorio; elegirla
    destruiria la sesion grafica al hacer openvt -f.
    """
    import subprocess as _sp
    try:
        r = _sp.run(
            ["loginctl", "list-sessions", "--no-legend"],
            capture_output=True, text=True, timeout=3,
        )
    except Exception:
        return None
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if not parts:
            continue
        sid = parts[0]
        try:
            tty_r = _sp.run(
                ["loginctl", "show-session", sid, "-p", "TTY", "--value"],
                capture_output=True, text=True, timeout=2,
            )
            type_r = _sp.run(
                ["loginctl", "show-session", sid, "-p", "Type", "--value"],
                capture_output=True, text=True, timeout=2,
            )
        except Exception:
            continue
        tty = (tty_r.stdout or "").strip()
        typ = (type_r.stdout or "").strip()
        if (tty.startswith("tty") and typ and typ not in ("tty", "unspecified")):
            try:
                return int(tty[3:])
            except ValueError:
                continue
    return None


# ----------------------------------------------------------------------
# Desktop Mode: cliente VNC en la VT (marcador desktop_mode_vnc_viewer_v1)
# ----------------------------------------------------------------------
# QEMU arranca en Desktop Mode con -display none -vnc unix:"..." (evita
# el bug de QEMU 8.2 con backends GTK/SDL que congela el main loop y
# bloquea QMP). Para que el usuario vea la VM, lanzamos vncviewer en
# fullscreen apuntando a ese socket. Cuando vncviewer termina, matamos
# QEMU para devolver la VT al escritorio.

# ----------------------------------------------------------------------
# Resolucion dinamica para Desktop Mode (marcador
# desktop_mode_dyn_resolution_v1)
# ----------------------------------------------------------------------
# El Xorg de la VT arranca a su resolucion por defecto (p.ej. 1600x900)
# mientras el guest puede estar a otra (p.ej. 1280x800). vncviewer
# centra la imagen sin escalar -> aparecen bordes negros.
#
# Solucion: leer width/height del guest desde el ServerInit del
# protocolo RFB (~40 lineas de Python puro, sin dependencias) y ajustar
# el Xorg de la VT con xrandr a esa misma resolucion. Si el modo no
# esta en la lista del driver, se crea con cvt + xrandr --newmode.

def _get_xrandr_current_resolution():
    """Resolucion (w, h) actual de la salida activa del Xorg actual.

    marcador: desktop_mode_edid_guest_res_v1. Se usa para pasarle a
    QEMU los parametros xres/yres de virtio-vga y que envie un EDID
    al guest con esa resolucion exacta. Sin esto, un guest Linux
    arranca a 640x480 cuando QEMU corre sin backend grafico local
    (-display none): no hay EDID que anunciar.
    """
    import subprocess as _sp
    import re as _re
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return None, None
    try:
        r = _sp.run([xrandr, "--query"], capture_output=True,
                    text=True, timeout=5)
    except Exception:
        return None, None
    lines = (r.stdout or "").splitlines()
    for line in lines:
        if " connected" in line and " primary " in line:
            m = _re.search(r"(\d+)x(\d+)\+", line)
            if m:
                return int(m.group(1)), int(m.group(2))
    for line in lines:
        if " connected" in line:
            m = _re.search(r"(\d+)x(\d+)\+", line)
            if m:
                return int(m.group(1)), int(m.group(2))
    return None, None


def _read_guest_resolution_from_vnc(sock_path, timeout=3.0):
    """Lee (width, height) del guest desde el handshake RFB.

    Handshake minimo para QEMU -vnc sin password:
      1. Server envia banner (12 bytes, "RFB 003.00X\n").
      2. Cliente devuelve el mismo banner.
      3. Server envia security-types (1 byte count + N bytes).
      4. Cliente elige type 1 (None).
      5. Server envia SecurityResult (4 bytes OK=0).
      6. Cliente envia ClientInit (1 byte shared=1).
      7. Server envia ServerInit: 2 width + 2 height + 16 pixfmt
         + 4 name-len + name.

    Devuelve (w, h) o lanza excepcion.
    """
    import socket as _socket
    import struct as _struct
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(sock_path)
        banner = b""
        while len(banner) < 12:
            chunk = s.recv(12 - len(banner))
            if not chunk:
                raise RuntimeError("VNC cerro antes del banner")
            banner += chunk
        s.sendall(banner)
        count_b = s.recv(1)
        if not count_b:
            raise RuntimeError("VNC cerro antes de security types")
        count = count_b[0]
        if count == 0:
            # Motivo de rechazo: 4 bytes length + reason
            rl = s.recv(4)
            if len(rl) < 4:
                raise RuntimeError("VNC cerro sin motivo")
            n = _struct.unpack(">I", rl)[0]
            reason = s.recv(n).decode(errors="replace")
            raise RuntimeError("VNC rechaza conexion: " + reason)
        types = s.recv(count)
        if 1 not in types:
            raise RuntimeError(
                "VNC requiere autenticacion (types=%r)" % list(types))
        s.sendall(b"\x01")  # elegir type 1 = None
        result = s.recv(4)
        if len(result) < 4:
            raise RuntimeError("VNC cerro antes de SecurityResult")
        if _struct.unpack(">I", result)[0] != 0:
            raise RuntimeError("VNC rechazo conexion (auth fallo)")
        s.sendall(b"\x01")  # shared=1
        head = b""
        while len(head) < 24:
            chunk = s.recv(24 - len(head))
            if not chunk:
                raise RuntimeError("VNC cerro antes de ServerInit")
            head += chunk
        width, height = _struct.unpack(">HH", head[:4])
        return int(width), int(height)
    finally:
        s.close()


def _adjust_vt_resolution(width, height):
    """Ajusta la resolucion del Xorg actual a WxH.

    Devuelve True si lo consiguio, False si no. Nunca lanza: cualquier
    fallo se registra y se sigue adelante (vncviewer mostrara bordes).
    """
    import subprocess as _sp
    xrandr = shutil.which("xrandr")
    if not xrandr:
        print("[AVISO] xrandr no disponible; la imagen mostrara bordes. "
              "Instala x11-xserver-utils (Debian/Ubuntu/Mint), "
              "xorg-xrandr (Arch/CachyOS) o xorg-x11-server-utils "
              "(Fedora).", flush=True)
        return False
    env = os.environ.copy()
    # Asegurar que xrandr hable con el Xorg de la VT, no con el del host.
    if not env.get("DISPLAY"):
        print("[AVISO] DISPLAY no definido; no se ajusta la VT.",
              flush=True)
        return False
    try:
        r = _sp.run([xrandr, "--query"], capture_output=True,
                    text=True, timeout=5, env=env)
    except Exception as e:
        print("[AVISO] xrandr --query fallo: %s" % e, flush=True)
        return False
    output = None
    connected = []
    for line in (r.stdout or "").splitlines():
        if " connected " in line:
            name = line.split()[0]
            connected.append(name)
            if " primary " in line:
                output = name
                break
    if output is None and connected:
        output = connected[0]
    if output is None:
        print("[AVISO] no se encontro output X activo", flush=True)
        return False

    mode = "%dx%d" % (width, height)
    try:
        r2 = _sp.run([xrandr, "--output", output, "--mode", mode],
                     capture_output=True, text=True, timeout=5, env=env)
    except Exception as e:
        print("[AVISO] xrandr --mode %s fallo: %s" % (mode, e), flush=True)
        return False
    if r2.returncode == 0:
        print("==> Desktop Mode: VT ajustada a %s (%s)." % (mode, output),
              flush=True)
        return True

    # El modo no esta en la lista: crearlo con cvt + xrandr.
    cvt = shutil.which("cvt")
    if not cvt:
        print("[AVISO] xrandr rechaza %s y no hay cvt. Instala "
              "x11-xserver-utils (Debian/Ubuntu/Mint), xorg-xrandr "
              "(Arch/CachyOS) o xorg-x11-server-utils (Fedora)."
              % mode, flush=True)
        return False
    try:
        rc = _sp.run([cvt, str(width), str(height)],
                     capture_output=True, text=True, timeout=5, env=env)
        modeline = None
        for ln in (rc.stdout or "").splitlines():
            if ln.strip().startswith("Modeline"):
                modeline = ln.split("Modeline", 1)[1].strip()
                break
        if not modeline:
            print("[AVISO] cvt no produjo modeline para %s" % mode,
                  flush=True)
            return False
        newmode = "%dx%d_60.00" % (width, height)
        parts = modeline.replace('"', " ").split()
        # parts[0] es el nombre entrecomillado; el resto son los valores.
        vals = parts[1:]
        _sp.run([xrandr, "--newmode", newmode] + vals,
                capture_output=True, text=True, timeout=5, env=env)
        _sp.run([xrandr, "--addmode", output, newmode],
                capture_output=True, text=True, timeout=5, env=env)
        r3 = _sp.run([xrandr, "--output", output, "--mode", newmode],
                     capture_output=True, text=True, timeout=5, env=env)
        if r3.returncode == 0:
            print("==> Desktop Mode: VT ajustada a %s (%s)."
                  % (newmode, output), flush=True)
            return True
    except Exception as e:
        print("[AVISO] cvt+xrandr fallo: %s" % e, flush=True)
    print("[AVISO] no se pudo ajustar la VT a %s; se mantiene la "
          "resolucion actual." % mode, flush=True)
    return False


def _launch_remote_viewer_for_desktop(vm_dir, viewer_holder):
    """Espera el socket VNC, lanza vncviewer -FullScreen y vigila.

    viewer_holder es un dict mutable compartido con el llamador:
      {"proc": None}  -> se rellena con el Popen de vncviewer.

    Cuando vncviewer termina por su cuenta (usuario pulsa F8 -> Exit),
    envia SIGTERM al QEMU de la VM para que la VT vuelva al escritorio.
    """
    sock = os.path.join(str(vm_dir), "qemu.spice.sock")
    # Esperar a que QEMU cree el socket SPICE (max ~20 s).
    for _ in range(200):
        if os.path.exists(sock):
            break
        time.sleep(0.1)
    else:
        print("[AVISO] Desktop Mode: no aparecio el socket SPICE en 20 s.",
              flush=True)
        return
    # Margen extra: QEMU acaba de bind() pero puede no estar en listen().
    time.sleep(0.3)

    # No hace falta leer la resolucion del guest: se la anunciamos
    # via EDID (xres/yres) desde _graphics_args_desktop, asi que ya
    # coincide con la VT. remote-viewer reescala solo si el guest
    # cambia a otra resolucion despues.

    viewer = shutil.which("remote-viewer")
    if not viewer:
        print("[AVISO] Desktop Mode: remote-viewer no esta instalado. "
              "La VM corre headless; instala virt-viewer para verla.",
              flush=True)
        return

    # desktop_mode_spice_symlink_v1: remote-viewer 1.4.43 no maneja
    # bien URIs con %20 en el path (falla con "No se pudo conectar al
    # servidor grafico" aunque el socket exista). Solucion: crear un
    # symlink SIN espacios en /tmp y pasarle ese path limpio a
    # remote-viewer. Asi no hay encoding ni comillas raras.
    import tempfile as _tmpfile
    sock_link = os.path.join(
        _tmpfile.gettempdir(),
        "vm-desktop-%d.spice.sock" % os.getpid(),
    )
    try:
        if os.path.islink(sock_link) or os.path.exists(sock_link):
            os.remove(sock_link)
        os.symlink(sock, sock_link)
    except Exception as _le:
        print(f"[AVISO] Desktop Mode: no se pudo crear symlink "
              f"{sock_link}: {_le}. Se intentara con el path original.",
              flush=True)
        sock_link = sock

    uri = "spice+unix://" + sock_link
    # desktop_mode_spice_audio_sink_v1: forzar el sink de GStreamer
    # que usa spice-gtk para reproducir el audio del guest. Sin esto,
    # en algunos sistemas (Linux Mint 22 / Ubuntu 24.04 con
    # gstreamer 1.24) spice-gtk no selecciona autoaudiosink y el
    # canal de audio queda deshabilitado en remote-viewer.
    #
    # Preferimos "pulsesink" porque pipewire-pulse expone una API
    # compatible con PulseAudio. Si no estuviera disponible, se
    # podria usar "pipewiresink" o "autoaudiosink".
    env = os.environ.copy()
    env.setdefault("SPICE_GST_AUDIO_SINK", "pulsesink")
    # desktop_mode_pipewire_session_v1: PipeWire/WirePlumber envian al
    # sink "auto_null" (silencio) a cualquier cliente que no tenga
    # DBUS_SESSION_BUS_ADDRESS y XDG_SESSION_ID. remote-viewer hereda
    # un env reducido del wrapper/xinit, asi que hay que reconstruir
    # esas dos variables con el uid del usuario y loginctl.
    _uid = os.getuid()
    _runtime = env.get("XDG_RUNTIME_DIR") or f"/run/user/{_uid}"
    env.setdefault("XDG_RUNTIME_DIR", _runtime)
    env.setdefault("DBUS_SESSION_BUS_ADDRESS",
                   f"unix:path={_runtime}/bus")
    env.setdefault("PULSE_SERVER",
                   f"unix:{_runtime}/pulse/native")
    if "XDG_SESSION_ID" not in env:
        try:
            import subprocess as _sp
            _user = os.environ.get("USER") or str(_uid)
            _r = _sp.run(["loginctl", "show-user", _user,
                          "--property=Display", "--value"],
                         capture_output=True, text=True, timeout=3)
            _sid = (_r.stdout or "").strip()
            if _sid:
                env["XDG_SESSION_ID"] = _sid
        except Exception:
            pass
    try:
        proc = subprocess.Popen(
            [viewer, "-f", uri],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    except Exception as e:
        print(f"[AVISO] Desktop Mode: no se pudo lanzar remote-viewer: {e}",
              flush=True)
        return

    viewer_holder["proc"] = proc
    print(f"==> Desktop Mode: remote-viewer lanzado (PID {proc.pid}). "
          f"Cierra la ventana para volver al escritorio.",
          flush=True)

    # Esperar a que remote-viewer termine.
    proc.wait()

    # Si QEMU sigue vivo, mandarle SIGTERM. El wrapper trap EXIT
    # limpiara sockets y devolvera la VT.
    pid_path = os.path.join(str(vm_dir), "qemu.pid")
    try:
        if os.path.isfile(pid_path):
            with open(pid_path, encoding="utf-8") as f:
                qpid = int(f.read().strip())
            print("==> Desktop Mode: remote-viewer cerrado; terminando QEMU...",
                  flush=True)
            import signal as _sig
            os.kill(qpid, _sig.SIGTERM)
    except Exception:
        pass


def _detect_real_sink_for_desktop():
    """Devuelve el primer sink NO-Dummy de pactl, o None.

    Marcador: desktop_mode_audio_pin_sink_v1

    Se usa para fijar PULSE_SINK antes de arrancar QEMU y evitar
    que WirePlumber reasigne el stream al Dummy Output cuando la
    VT activa no es la sesion del escritorio.
    """
    import shutil as _sh
    import subprocess as _sp
    pactl = _sh.which("pactl")
    if not pactl:
        return None
    try:
        r = _sp.run([pactl, "list", "short", "sinks"],
                    capture_output=True, text=True, timeout=3)
    except Exception:
        return None
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            name = parts[1]
            if "Dummy" not in name and "auto_null" not in name:
                return name
    return None


def _run_qemu_inside_cage(vm_dir, snapshot=False):
    """Ejecutado DENTRO de cage. Lanza QEMU y espera."""
    _ensure_qcore_app()

    import vm_config
    from workers import InstallWorker

    # desktop_mode_audio_pin_sink_v1: fijar el sink real como
    # PULSE_SINK para que QEMU no siga al default sink cuando
    # WirePlumber lo cambia a Dummy Output al cambiar de VT.
    _real_sink = _detect_real_sink_for_desktop()
    if _real_sink:
        os.environ["PULSE_SINK"] = _real_sink
        print(f"==> Desktop Mode: audio fijado a {_real_sink}", flush=True)
    else:
        print("[AVISO] Desktop Mode: no se encontro sink real; "
              "QEMU usara el sink por defecto.", flush=True)

    _patch_installworker_for_desktop(InstallWorker)

    if snapshot:
        _check_tmp_space_for_snapshot(min_gb=3)
        _patch_installworker_for_snapshot(InstallWorker)

    cfg = vm_config.load_vm_config(str(vm_dir))
    extra = cfg.get("extra", {}) if isinstance(cfg.get("extra"), dict) else {}

    kwargs = _build_worker_kwargs(cfg, extra, vm_dir, snapshot=snapshot)

    # desktop_mode_nested_gfx_v1: forzar 2D cuando QEMU corre dentro
    # de cage con WLR_RENDERER=pixman. Pixman no expone OpenGL a los
    # clientes, asi que VirGL/Venus fallarian con:
    #   qemu-system-x86_64: OpenGL is not supported by the display
    # VirtIO-GPU 2D funciona con cualquier backend de pantalla.
    kwargs["graphics_mode"] = "virtio"
    # desktop_mode_xorg_vt_nodisplay_test_v1: TEST headless.
    # Si QMP responde aqui pero no con sdl/gtk, el bug esta en
    # la integracion display <-> BQL. Si tampoco, es QMP mismo.
    extra["graphics_mode"] = "virtio"

    # desktop_mode_edid_guest_res_v1: leer la resolucion actual de la
    # VT y pasarsela a QEMU para que la anuncie al guest via EDID.
    # Asi el guest arranca directamente a la misma resolucion que la
    # VT y vncviewer llena la pantalla sin bordes.
    _vw, _vh = _get_xrandr_current_resolution()
    if _vw and _vh:
        os.environ["VM_DESKTOP_XRES"] = str(_vw)
        os.environ["VM_DESKTOP_YRES"] = str(_vh)
        print("==> Desktop Mode: VT a %dx%d; se anunciara esa "
              "resolucion al guest via EDID." % (_vw, _vh), flush=True)

    worker = InstallWorker(**kwargs)

    # Señales a stdout. Las conexiones son directas (mismo hilo,
    # sin event loop), así que la lambda se ejecuta en el momento.
    worker.log_signal.connect(lambda s: print(s, flush=True))
    worker.progress_signal.connect(
        lambda pct, msg: print(
            f"[{pct}%] {msg}" if pct >= 0 else msg, flush=True
        )
    )

    print(f"==> Desktop Mode: lanzando QEMU desde {vm_dir}...", flush=True)

    # desktop_mode_vnc_viewer_v1: lanzar en paralelo un watcher que
    # espera el socket VNC y arranca vncviewer -FullScreen en la VT.
    # worker.run() sigue siendo bloqueante y en el hilo principal, para
    # que las señales directas (log_signal) sigan funcionando.
    viewer_holder = {"proc": None}
    watcher = threading.Thread(
        target=_launch_remote_viewer_for_desktop,
        args=(vm_dir, viewer_holder),
        daemon=True,
    )
    watcher.start()

    try:
        worker.run()  # bloquea hasta que QEMU termina
    finally:
        # Si QEMU termino antes que vncviewer, cerrar vncviewer.
        proc = viewer_holder.get("proc")
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    print("==> Desktop Mode: QEMU finalizado. Saliendo de cage...", flush=True)


# ----------------------------------------------------------------------
# Modo usuario: construye el comando sudo y lo ejecuta
# ----------------------------------------------------------------------
def _find_repo_vm_dir(vm_name):
    """Localiza la carpeta de la VM dentro de VirtualMachines/."""
    import vm_config
    base = Path(vm_config.BASE_VM_DIR).resolve()
    candidate = base / vm_name
    if not candidate.is_dir():
        raise SystemExit(
            f"[ERROR] No se encontró la VM '{vm_name}' en {base}."
        )
    return candidate


def _build_sudo_argv(vm_name, tty, monitor, snapshot):
    """Construye el argv del wrapper sudo.

    Todos los parámetros van como POSICIONALES: sudo limpia el
    entorno con env_reset y permitir SETENV abriría un agujero
    (LD_PRELOAD contra setpriv). El wrapper los valida uno a uno.
    """
    return [
        "sudo", SUDO_WRAPPER,
        vm_name, str(tty),
        monitor, "1" if snapshot else "0",
    ]


def _print_dry_run(argv):
    print("Comando a ejecutar:")
    print("  " + " ".join(shlex.quote(a) for a in argv))


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _parse_args():
    ap = argparse.ArgumentParser(
        prog="desktop_mode",
        description=(
            "Desktop Mode para Virtual.Machine: arranca una VM a "
            "pantalla completa sobre un TTY dedicado con cage."
        ),
    )
    ap.add_argument("--vm",
                    help="Nombre de la VM (carpeta dentro de VirtualMachines/).")
    ap.add_argument("--tty", type=int, default=DEFAULT_TTY,
                    help=f"TTY destino (default {DEFAULT_TTY}).")
    ap.add_argument("--monitor", choices=VALID_MONITORS,
                    default=DEFAULT_MONITOR,
                    help=f"cage -m (default {DEFAULT_MONITOR}).")
    ap.add_argument("--snapshot", action="store_true",
                    help="Arrancar QEMU con -snapshot (los cambios no "
                         "se guardan al disco). Útil para pruebas.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo imprimir el comando, no ejecutarlo.")

    # Flags internos (usados por el wrapper sudo desde dentro de cage).
    ap.add_argument("--inside-cage", action="store_true",
                    help=argparse.SUPPRESS)
    ap.add_argument("--vm-dir", help=argparse.SUPPRESS)
    return ap.parse_args()


def main():
    args = _parse_args()

    # --- Modo interno: ya estamos dentro de cage ---
    if args.inside_cage:
        if not args.vm_dir:
            raise SystemExit("--inside-cage requiere --vm-dir")
        vm_dir = Path(args.vm_dir).resolve()
        snapshot = bool(args.snapshot)
        try:
            _run_qemu_inside_cage(vm_dir, snapshot=snapshot)
            return 0
        except KeyboardInterrupt:
            print("\n==> Desktop Mode: interrumpido por el usuario.", flush=True)
            return 130
        except Exception as e:
            print(f"[ERROR] Desktop Mode: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Pausa para que se lea el error antes de que cage cierre.
            try:
                input("Pulsa Intro para salir de cage...")
            except Exception:
                pass
            return 1

    # --- Modo usuario ---
    if not args.vm:
        raise SystemExit(
            "Uso: desktop_mode.py --vm <nombre> [--tty N] [--monitor last|extend]\n"
            "Consulta --help para más opciones."
        )

    if not (2 <= args.tty <= 12):
        raise SystemExit(f"--tty debe estar entre 2 y 12 (recibido: {args.tty}).")

    # Guard: no permitir el TTY de la sesion grafica.
    _graphical_tty = _detect_graphical_tty()
    if _graphical_tty is not None and args.tty == _graphical_tty:
        raise SystemExit(
            f"[ERROR] tty{_graphical_tty} es la sesion grafica del host "
            f"(KDE/Wayland).\n"
            f"        Elegir esa VT destruiria el escritorio.\n"
            f"        Usa una VT libre, por ejemplo tty{_graphical_tty + 1}."
        )

    # Validar que la VM existe (fail-fast en el lado usuario).
    _find_repo_vm_dir(args.vm)

    # Validar que el wrapper sudo existe.
    if not os.path.isfile(SUDO_WRAPPER):
        raise SystemExit(
            f"[ERROR] No existe el wrapper sudo: {SUDO_WRAPPER}\n"
            "Instálalo primero (ver README de Desktop Mode)."
        )

    argv = _build_sudo_argv(args.vm, args.tty, args.monitor, args.snapshot)

    if args.dry_run:
        _print_dry_run(argv)
        return 0

    print(f"==> Desktop Mode: arrancando '{args.vm}' en tty{args.tty} "
          f"(monitor={args.monitor}).", flush=True)
    print("==> Para volver a KDE al terminar, el wrapper cambiará la VT "
          "automáticamente.", flush=True)
    proc = subprocess.run(argv)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

# clipboard_desktop_spice_v1
