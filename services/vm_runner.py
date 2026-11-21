import subprocess
import logging
import os
import time
import socket
import shutil
import glob
import json
import re
import threading
import uuid
import platform
from pathlib import Path
from typing import Dict
from .host_adapter import HostAdapter, IS_WINDOWS, IS_LINUX
from .host_diagnostics import (
    OVMF_LINUX_DIRS, OVMF_CODE_PATTERNS, OVMF_SECBOOT_CODE_PATTERNS, OVMF_VARS_PATTERNS,
)

log = logging.getLogger(__name__)

class VMRunner:
    def __init__(self, host: HostAdapter, data_dir: Path, vms_dir: Path | None = None):
        self.host = host
        self.data_dir = Path(data_dir)
        self.vms_dir = Path(vms_dir) if vms_dir else self.data_dir / "vms"
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.active_viewers: Dict[str, subprocess.Popen] = {}
        self.virtiofsd_procs: Dict[str, list] = {}
        self.gvtg_uuids: Dict[str, str] = {}
        # QMP: el puerto se elige UNA vez por VM. Antes se recalculaba en cada
        # llamada, así que stop/pause/change_iso conectaban a otro puerto.
        self._qmp_sockets: Dict[str, str] = {}
        self._vnc_keymap = None
        self._intel_host = None

    def _is_windows_guest(self, vm: dict) -> bool:
        return "windows" in str(vm.get("platform", "")).lower()

    def _host_is_intel(self) -> bool:
        if self._intel_host is not None:
            return self._intel_host
        result = False
        try:
            if IS_LINUX:
                with open("/proc/cpuinfo", "r", errors="ignore") as f:
                    result = "GenuineIntel" in f.read()
            else:
                result = "intel" in platform.processor().lower()
        except Exception:
            result = False
        self._intel_host = result
        return result

    def _mlock_possible(self, ram_mb: int) -> bool:
        if IS_WINDOWS:
            return False
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_MEMLOCK)
            ram_bytes = ram_mb * 1024 * 1024
            limit = ram_bytes + 1
            best = float("inf")
            for v in (soft, hard):
                if v != resource.RLIM_INFINITY:
                    best = min(best, v)
            if best == float("inf"):
                return True
            return best >= ram_bytes
        except Exception:
            return False

    def _hugepages_free(self):
        """Devuelve (tamaño_kB, libres) del host o None si no se pudo leer."""
        try:
            hp_size = 2048
            free = None
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("Hugepagesize:"):
                        hp_size = int(line.split()[1])
                    elif line.startswith("HugePages_Free:"):
                        free = int(line.split()[1])
            if free is None:
                return None
            return hp_size, free
        except Exception:
            return None

    def _prepare_gvtg_vgpu(self, vm_id: str, profile: str = "i915-GVTg_V5_4") -> str | None:
        """GVT-g solo está disponible en Linux. En Windows se omite."""
        if IS_WINDOWS:
            log.warning("GVT-g no soportado en Windows. Se omite.")
            return None
        pci_addr = "0000:00:02.0"
        create_path = f"/sys/bus/pci/devices/{pci_addr}/mdev_supported_types/{profile}/create"

        if not os.path.exists(create_path):
            log.error(f"Perfil GVT-g no encontrado en {create_path}")
            return None

        vgpu_uuid = str(uuid.uuid4())
        script = (
            f"echo {vgpu_uuid} > {create_path} || exit 1; "
            f"chown -R {os.getuid()}:{os.getgid()} "
            f"/sys/bus/mdev/devices/{vgpu_uuid} 2>/dev/null || true"
        )
        try:
            subprocess.run(["pkexec", "sh", "-c", script], check=True, capture_output=True)
            log.info(f"vGPU GVT-g creada con UUID: {vgpu_uuid} (perfil: {profile})")
            return vgpu_uuid
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if e.stderr else str(e)
            log.error(f"Error al crear la vGPU mdev: {err}")
            return None

    def _cleanup_gvtg_vgpu(self, vm_id: str):
        if IS_WINDOWS:
            return
        vgpu_uuid = self.gvtg_uuids.pop(vm_id, None)
        if not vgpu_uuid:
            return
        remove_path = f"/sys/bus/mdev/devices/{vgpu_uuid}/remove"
        try:
            subprocess.run(["pkexec", "sh", "-c", f"echo 1 > {remove_path}"], check=False)
            log.info(f"vGPU GVT-g {vgpu_uuid} destruida.")
        except Exception as e:
            log.warning(f"No se pudo destruir la vGPU {vgpu_uuid}: {e}")

    def _ensure_virtiofsd(self, vm_id: str, sock_path: str, host_path: str):
        if os.path.exists(sock_path):
            try: os.remove(sock_path)
            except OSError: pass
        bin_path = None
        for cand in [shutil.which("virtiofsd"), "/usr/lib/virtiofsd",
                     "/usr/libexec/virtiofsd", "/usr/local/libexec/virtiofsd",
                     "/usr/lib/qemu/virtiofsd"]:
            if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                bin_path = cand
                break
        if not bin_path:
            return False
        attempts = [
            [bin_path, "--socket-path", sock_path, "--shared-dir", host_path, "--sandbox", "none", "--cache", "always"],
            [bin_path, "--socket-path", sock_path, "-o", f"source={host_path}", "--sandbox=none"],
        ]
        for cmd in attempts:
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            except Exception:
                continue
            for _ in range(40):
                if os.path.exists(sock_path):
                    self.virtiofsd_procs.setdefault(vm_id, []).append(proc)
                    log.info(f"virtiofsd iniciado (pid {proc.pid}) para {sock_path}")
                    return True
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
            if proc.poll() is None:
                try: proc.terminate()
                except Exception: pass
        return False

    def _virtiofsd_available(self):
        """True si virtiofsd está disponible sin lanzarlo (usado para elegir el método Automático)."""
        for cand in [shutil.which("virtiofsd"), "/usr/lib/virtiofsd",
                     "/usr/libexec/virtiofsd", "/usr/local/libexec/virtiofsd",
                     "/usr/lib/qemu/virtiofsd"]:
            if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                return True
        return False

    def _kill_virtiofsd(self, vm_id: str):
        for proc in self.virtiofsd_procs.pop(vm_id, []):
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try: proc.wait(timeout=2)
                    except subprocess.TimeoutExpired: proc.kill()
            except Exception: pass

    def _detect_vnc_keymap(self) -> str:
        qemu_keymaps = {"es", "de", "fr", "it", "nl", "da", "fi", "hu", "is", "sl",
                        "sv", "tr", "no", "ja", "ko", "en-gb", "en-us"}
        if IS_WINDOWS:
            # En Windows no existe setxkbmap; usar solo locale
            try:
                import locale
                loc = locale.getlocale()[0]
                if loc:
                    lang = loc.replace("-", "_").split("_")[0].lower()
                    if lang in qemu_keymaps:
                        return lang
                    if lang == "pt":
                        return "pt-br"
                    if lang == "en":
                        return "en-us"
            except Exception:
                pass
            return ""
        if self.host.qemu_path:
            try:
                out = subprocess.run([self.host.qemu_path, "-vnc", "help"],
                                     capture_output=True, text=True, timeout=3)
                help_text = out.stdout + out.stderr
                if "keymap" not in help_text:
                    return ""
            except Exception:
                return ""
        try:
            out = subprocess.run(["setxkbmap", "-query"], capture_output=True, text=True, timeout=2)
            for line in out.stdout.splitlines():
                if line.startswith("layout:"):
                    lay = line.split(":", 1)[1].strip().split(",")[0].strip()
                    if lay in qemu_keymaps:
                        return lay
                    if lay == "pt":
                        return "pt-br"
        except Exception:
            pass
        try:
            import locale
            loc = locale.getlocale()[0]
            if loc:
                lang = loc.replace("-", "_").split("_")[0].lower()
                if lang in qemu_keymaps:
                    return lang
                if lang == "pt":
                    return "pt-br"
                if lang == "en":
                    return "en-us"
        except Exception:
            pass
        return ""

    def _vnc_target(self, vnc_port: int) -> str:
        if self._vnc_keymap is None:
            self._vnc_keymap = self._detect_vnc_keymap()
        target = f"127.0.0.1:{vnc_port - 5900}"
        if self._vnc_keymap:
            target += f",keymap={self._vnc_keymap}"
        return target

    def _find_free_port(self, start: int = 5900, end: int = 6000, exclude: set = None) -> int:
        exclude = exclude or set()
        for port in range(start, end):
            if port in exclude:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        raise RuntimeError(f"No hay puertos libres entre {start} y {end}.")

    def _find_free_vnc_port(self, exclude: set = None) -> int:
        return self._find_free_port(5900, 6000, exclude=exclude)

    def _find_ovmf(self, secure_boot=False):
        project_root = Path(__file__).parent.parent
        search_dirs = [
            project_root / "OSX-KVM", self.data_dir / "OSX-KVM",
        ]
        if IS_LINUX:
            # Misma lista que usa Configuracion Host para el diagnostico.
            search_dirs.extend([Path(d) for d in OVMF_LINUX_DIRS])
            search_dirs.append(self.data_dir)
        else:
            # Windows: buscar en Program Files y junto al ejecutable de QEMU
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            search_dirs.extend([
                Path(program_files) / "qemu",
                Path(program_files) / "QEMU",
                Path(self.host.qemu_path).parent if self.host.qemu_path else Path("."),
                self.data_dir
            ])

        def _is_valid_code(path):
            try: return os.path.exists(path) and os.path.getsize(path) > 1024 * 1024
            except: return False
        def _is_valid_vars(path):
            try: return os.path.exists(path) and os.path.getsize(path) > 10 * 1024
            except: return False

        if secure_boot:
            for d in search_dirs:
                if not d.exists(): continue
                code_candidates = []
                for code_pat in OVMF_SECBOOT_CODE_PATTERNS:
                    code_candidates.extend(glob.glob(str(d / code_pat)))
                valid_codes = [p for p in code_candidates if _is_valid_code(p)]
                if not valid_codes: continue
                code_path = valid_codes[0]
                valid_vars = []
                for vars_pat in ("OVMF_VARS*.secboot*.fd",) + OVMF_VARS_PATTERNS:
                    candidatos = glob.glob(str(d / vars_pat))
                    valid_vars = [p for p in candidatos if _is_valid_vars(p)]
                    if valid_vars: break
                if valid_vars: return code_path, valid_vars[0]

        for d in search_dirs:
            if not d.exists(): continue
            for code_pat in OVMF_CODE_PATTERNS:
                matches = glob.glob(str(d / code_pat))
                valid = [p for p in matches if _is_valid_code(p)]
                if valid:
                    code_path = valid[0]
                    break
            else: continue
            for vars_pat in OVMF_VARS_PATTERNS:
                matches = glob.glob(str(d / vars_pat))
                valid = [p for p in matches if _is_valid_vars(p)]
                if valid: return code_path, valid[0]
        return None, None

    def _kill_orphan_qemu(self, disk_path, vm_id=None):
        """Cierra un QEMU previo que aún tenga abierto este disco.

        Nunca se usa ``taskkill /IM``: eso mataría TODAS las VMs de QEMU del
        sistema, incluidas las que no tienen nada que ver con este disco.
        """
        if not disk_path or not os.path.exists(disk_path):
            return
        if IS_WINDOWS:
            proc = self.active_processes.get(vm_id) if vm_id else None
            if proc is None or proc.poll() is not None:
                return
            log.info("Cerrando QEMU huérfano de %s (pid=%s)", vm_id, proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            self.active_processes.pop(vm_id, None)
            return
        try:
            result = subprocess.run(
                ["lsof", "-t", disk_path], capture_output=True, text=True, timeout=3)
            own_pid = self.active_processes[vm_id].pid if vm_id in self.active_processes else None
            for pid in result.stdout.strip().split():
                if own_pid is not None and int(pid) == own_pid:
                    continue
                try:
                    os.kill(int(pid), 9)
                except (ValueError, ProcessLookupError, PermissionError):
                    pass
        except Exception as e:
            log.debug("No se pudo liberar %s: %s", disk_path, e)

    def _setup_tpm(self, vm: dict, q35: bool) -> list[str]:
        if IS_WINDOWS:
            # En Windows, swtpm puede no estar disponible. QEMU puede emular TPM internamente
            tpm_device = "tpm-crb" if q35 else "tpm-tis"
            return ["-tpmdev", "emulator,id=tpm0", "-device", f"{tpm_device},tpmdev=tpm0"]
        vm_id = vm["id"]
        # pkill -f interpreta el patrón como regex: un vm_id con metacaracteres
        # podría matar procesos ajenos. Validar ANTES de crear nada: en Windows
        # los caracteres prohibidos hacen que makedirs falle primero.
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(vm_id)):
            raise ValueError(f"ID de VM inválido para swtpm: {vm_id!r}")
        tpm_dir = os.path.join(str(self.vms_dir), vm_id, "tpm")
        os.makedirs(tpm_dir, exist_ok=True)
        sock_path = f"/tmp/swtpm-{vm_id}.sock"
        try:
            subprocess.run(
                ["pkill", "-9", "-f", rf"swtpm.*{re.escape(vm_id)}"],
                check=False, timeout=2)
            time.sleep(0.3)
        except Exception as e:
            log.debug("No se pudo limpiar swtpm previo de %s: %s", vm_id, e)
        if os.path.exists(sock_path):
            try: os.remove(sock_path)
            except: pass
        for f in ["tpm2-00.permall", "tpm-00.permall"]:
            p = os.path.join(tpm_dir, f)
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        swtpm_cmd = ["swtpm", "socket", "--tpmstate", f"dir={tpm_dir}", "--ctrl", f"type=unixio,path={sock_path}", "--tpm2", "--daemon", "--log", f"file={tpm_dir}/swtpm.log,level=5"]
        try: subprocess.run(swtpm_cmd, check=True)
        except FileNotFoundError: raise RuntimeError("swtpm no instalado.")
        start = time.time()
        while not os.path.exists(sock_path):
            if time.time() - start > 3.0: raise RuntimeError("Timeout esperando a swtpm.")
            time.sleep(0.1)
        tpm_device = "tpm-crb" if q35 else "tpm-tis"
        return ["-chardev", f"socket,id=chrtpm,path={sock_path}", "-tpmdev", "emulator,id=tpm0,chardev=chrtpm", "-device", f"{tpm_device},tpmdev=tpm0"]

    def _build_cpu_args(self, vm: dict) -> list[str]:
        cpu_idx = vm.get("cpu_type_idx", 0)
        base_map = {0: None, 1: "host", 2: "qemu64", 3: "Skylake-Client", 4: "Haswell", 5: "Broadwell", 6: "SandyBridge", 7: "Penryn"}
        base = base_map.get(cpu_idx, None) or ("host" if self.host.acceleration in ("kvm", "whpx", "hax") else "qemu64")
        flags = []
        if vm.get("nested_virt"): flags.append("vmx=on")
        if vm.get("hyperv") or self._is_windows_guest(vm):
            # Optimizaciones de Hyper-V / paravirtualización para invitados Windows
            flags.extend([
                "hv_relaxed=on", "hv_spinlocks=0x1fff", "hv_vapic=on", "hv_time=on",
                "hv_vpindex=on", "hv_runtime=on", "hv_synic=on",
                "hv_stimer=on", "hv_stimer_direct=on", "hv_ipi=on",
            ])
        if self.host.acceleration == "kvm" and base == "host" and self._host_is_intel():
            # TSC invariante: timer estable y barato para el invitado (solo hosts Intel)
            flags.append("+invtsc")
        return [f"{base}," + ",".join(flags)] if flags else [base]

    def _build_memory_args(self, vm: dict, ram_mb: int, hugepages: bool, prealloc: bool) -> list[str]:
        """Construye el backend de memoria (hugepages/prealloc).
        Si el host no tiene hugepages suficientes, cae a RAM normal sin romper el arranque."""
        size_arg = f"size={ram_mb}M"
        if hugepages:
            info = self._hugepages_free() if IS_LINUX else None
            if info:
                hp_kb, hp_free = info
                needed = (ram_mb * 1024 + hp_kb - 1) // hp_kb
                if hp_free >= needed:
                    arg = f"memory-backend-memfd,id=mem0,{size_arg},hugepages=on"
                    if prealloc:
                        arg += ",prealloc=on"
                    log.info(f"Hugepages activadas: {needed} x {hp_kb} kB (libres: {hp_free}).")
                    return ["-object", arg, "-numa", "node,memdev=mem0"]
                log.warning(
                    f"Hugepages solicitadas pero insuficientes "
                    f"(libres: {hp_free}, necesarias: {needed}). Usando RAM normal.")
            else:
                log.warning("No se pudieron leer los hugepages del host; usando RAM normal.")
        backend = "memory-backend-memfd" if IS_LINUX else "memory-backend-ram"
        arg = f"{backend},id=mem0,{size_arg}"
        if prealloc:
            arg += ",prealloc=on"
            log.info("Prealloc de RAM activado (las páginas se reservan al arrancar).")
        else:
            log.info("Backend de memoria memfd activado.")
        return ["-object", arg, "-numa", "node,memdev=mem0"]

    def _build_pointer_args(self, vm: dict) -> list[str]:
        choice = str(vm.get("pointer", "Automático (recomendado)") or "").lower()
        xhci = ["-device", "qemu-xhci,id=xhci"]
        if not choice or "automático" in choice:
            return xhci + ["-device", "usb-tablet,bus=xhci.0"]
        if "usb keyboard" in choice and "tablet" in choice:
            return xhci + ["-device", "usb-kbd,bus=xhci.0", "-device", "usb-tablet,bus=xhci.0"]
        if "virtio tablet" in choice:
            # Ratón/teclado tablet paravirtual (no necesita bus USB)
            return ["-device", "virtio-tablet-pci"]
        if "usb tablet" in choice:
            return xhci + ["-device", "usb-tablet,bus=xhci.0"]
        if "usb mouse" in choice:
            return xhci + ["-device", "usb-mouse,bus=xhci.0"]
        if "ps/2" in choice or "ps2" in choice or "ps-2" in choice:
            return []  # PS/2 es el bus por defecto de QEMU
        if "ninguno" in choice or "none" in choice:
            return []
        return xhci + ["-device", "usb-tablet,bus=xhci.0"]

    def _build_audio_args(self, vm: dict) -> list[str]:
        choice = str(vm.get("audio", "Intel HDA (recomendado)") or "").lower()
        if "ninguno" in choice or "none" in choice:
            return []
        if "ac97" in choice:
            return ["-device", "ac97"]
        if "sound blaster" in choice or "sb16" in choice:
            return ["-device", "sb16"]
        return ["-device", "intel-hda", "-device", "hda-duplex"]

    def _build_graphics_device_args(self, vm: dict) -> list[str]:
        if vm.get("gvtg_enabled", False):
            return ["-vga", "none"]

        gfx_idx = vm.get("graphics_idx", 0)
        proto_idx = vm.get("console_proto_idx", 0)
        mode_idx = vm.get("console_mode_idx", 0)
        vram_mb = [64, 128, 256, 512][vm.get("vram_idx", 0)]

        if IS_WINDOWS and gfx_idx in (2, 3):
            # VirGL/Venus usan /dev/dri/renderD*, que no existe en Windows.
            log.warning("3D (VirGL/Venus) no disponible en Windows; usando gráficos básicos.")
            gfx_idx = 0

        # Detectar el primer rendernode disponible para egl-headless (Linux).
        _rendernode = None
        if not IS_WINDOWS:
            import glob as _glob
            _rendernodes = sorted(_glob.glob("/dev/dri/renderD*"))
            _rendernode = _rendernodes[0] if _rendernodes else "/dev/dri/renderD128"
        
        if any(d.get("is_vga", False) and d.get("type") == "PCI" for d in vm.get("passthrough_devices", [])):
            return ["-vga", "none"]
        
        # Pantalla completa embebida: SDL en pantalla completa dentro de la ventana de la app
        if mode_idx == 4:
            return ["-vga", "virtio", "-display", "sdl,full-screen=on"]

        if proto_idx in (1, 2) and gfx_idx == 3:
            # Venus/Vulkan 3D con SPICE.
            # egl-headless hace que QEMU renderice en GPU sin abrir ventana.
            # SPICE transmite los frames SIN gl=on (sin DMA-BUF), evitando
            # el conflicto de contextos EGL entre QEMU y remote-viewer.
            return ["-device", "virtio-vga-gl,venus=on,blob=on,hostmem=512M",
                    "-display", f"egl-headless,rendernode={_rendernode}"]
        if proto_idx in (1, 2) and gfx_idx == 2:
            # VirGL 3D con SPICE: mismo esquema.
            return ["-device", "virtio-vga-gl",
                    "-display", f"egl-headless,rendernode={_rendernode}"]
            
        if proto_idx == 0 and gfx_idx in (2, 3):
            return ["-vga", "virtio", "-display", "gtk,gl=on"]

        graphics_map = {
            0: ["-vga", "virtio"], 1: ["-vga", "virtio"],
            4: ["-vga", "qxl", "-global", f"qxl-vga.vgamem_mb={vram_mb}"],
            5: ["-vga", "vmware"], 6: ["-vga", "std"], 7: ["-vga", "none"],
        }
        args = list(graphics_map.get(gfx_idx, graphics_map[0]))
        # Con SPICE (proto 1 o 2), QEMU no debe abrir un display GTK propio.
        if proto_idx in (1, 2):
            args += ["-display", "none"]
        return args

    def _build_display_protocol_args(self, vm: dict, exclude_ports: set = None, gvtg_active: bool = False):
        exclude_ports = exclude_ports or set()
        proto_idx, mode_idx = vm.get("console_proto_idx", 0), vm.get("console_mode_idx", 0)
        args, external_info = [], None
        share_clipboard = vm.get("share_clipboard", True)

        if gvtg_active:
            log.info("GVT-g activo: forzando SPICE con OpenGL (gl=on) para evitar problemas de VNC.")
            spice_port = self._find_free_port(5930, 6000, exclude=exclude_ports)
            exclude_ports.add(spice_port); vm["spice_port"] = spice_port
            args.extend(["-spice", f"port={spice_port},addr=127.0.0.1,disable-ticketing=on,gl=on"])

            if share_clipboard:
                args.extend(["-device", "virtio-serial-pci", "-chardev", "spicevmc,id=vdagent,name=vdagent", "-device", "virtserialport,chardev=vdagent,name=com.redhat.spice.0"])

            return args, {"type": "spice", "port": spice_port}

        # Modo Híbrida (VNC widget embebido + SPICE en ventana externa):
        # QEMU debe exponer AMBOS servidores a la vez.
        hybrid = (mode_idx == 2)
        need_vnc = hybrid or proto_idx == 0
        need_spice = hybrid or proto_idx in (1, 2)

        if need_vnc:
            vnc_port = self._find_free_vnc_port(exclude=exclude_ports)
            exclude_ports.add(vnc_port); vm["vnc_port"] = vnc_port
            args.extend(["-vnc", self._vnc_target(vnc_port)])
            if hybrid:
                log.info("Híbrida: servidor VNC embebido en el puerto %s", vnc_port)
            elif mode_idx == 1: external_info = {"type": "vnc", "port": vnc_port}
            elif mode_idx == 4: external_info = {"type": "sdl_fullscreen", "port": vnc_port}

        if not need_spice:
            return args, external_info

        # QEMU para Windows no compila SPICE_ADDR_FLAG_UNIX_ONLY: `unix=on`
        # simplemente no existe. En ese caso el "SPICE local" se sirve por TCP
        # en el loopback, que es el equivalente funcional (nunca 0.0.0.0).
        remote_spice = (proto_idx == 2 or IS_WINDOWS)
        gfx_idx = vm.get("graphics_idx", 0)
        gl_ok = gfx_idx in (2, 3) and not IS_WINDOWS

        if remote_spice:
            spice_port = self._find_free_port(5930, 6000, exclude=exclude_ports)
            exclude_ports.add(spice_port); vm["spice_port"] = spice_port
            # En Windows el servidor solo se expone en 127.0.0.1; el modo
            # "Remoto" sigue using 0.0.0.0 porque el usuario lo eligió así.
            addr = "127.0.0.1" if IS_WINDOWS and proto_idx != 2 else "0.0.0.0"
            if gl_ok:
                # Con egl-headless en _build_graphics_args, QEMU ya tiene su contexto GL.
                # SPICE NO debe llevar gl=on (causaría "already has an OpenGL context").
                # La aceleración 3D ocurre en egl-headless; SPICE solo transporta los frames.
                spice_args = f"port={spice_port},addr={addr},disable-ticketing=on"
                log.info("SPICE Remoto con aceleración 3D (VirGL) activada (egl-headless).")
            else:
                spice_args = f"port={spice_port},addr={addr},disable-ticketing=on"
            external_info = {"type": "spice_remote" if proto_idx == 2 else "spice_tcp",
                             "port": spice_port}
        else:  # SPICE Local (socket unix)
            sock_path = self._get_tmp_socket_path(vm.get("id", "vm"), "qemu-spice")
            if os.path.exists(sock_path):
                try: os.remove(sock_path)
                except: pass
            if gl_ok:
                # Con egl-headless en _build_graphics_args, QEMU ya tiene su contexto GL.
                # SPICE NO debe llevar gl=on (causaría "already has an OpenGL context").
                # La aceleración 3D ocurre en egl-headless; SPICE solo transporta los frames.
                spice_args = f"unix=on,addr={sock_path},disable-ticketing=on"
                log.info("SPICE Local con aceleración 3D (VirGL) activada (egl-headless).")
            else:
                spice_args = f"unix=on,addr={sock_path},disable-ticketing=on"
                if gfx_idx not in (0, 1):
                    log.info(f"Gráfico {gfx_idx} no es 3D; SPICE se lanzará sin OpenGL.")
            external_info = {"type": "spice_unix", "path": sock_path}

        args.extend(["-spice", spice_args])
        if share_clipboard:
            args.extend(["-device", "virtio-serial-pci", "-chardev", "spicevmc,id=vdagent,name=vdagent", "-device", "virtserialport,chardev=vdagent,name=com.redhat.spice.0"])

        if hybrid:
            log.info("Híbrida: servidor SPICE externo y ventana remote-viewer se abrirán.")

        return args, external_info

    def _build_guest_agent_args(self, vm: dict) -> list[str]:
        shared = vm.get("shared_folders", []) or []
        auto_mount = any(sh.get("mount", "").startswith("Automático") for sh in shared)
        if not auto_mount and not vm.get("guest_agent", False):
            return []
        return [
            "-device", "virtio-serial-pci",
            "-chardev", f"socket,id=chrgagent,path={self._get_tmp_socket_path(vm.get('id', 'vm'), 'qemu-ga')},server=on,wait=off",
            "-device", "virtserialport,chardev=chrgagent,name=org.qemu.guest_agent.0",
        ]

    def _build_shared_folder_args(self, vm: dict) -> list[str]:
        args = []
        shared_folders = vm.get("shared_folders", []) or []
        smb_net_index = 0
        for sh in shared_folders:
            host_path = sh.get("host", "").strip()
            tag = sh.get("guest", "share").strip() or "share"
            method = sh.get("method", "Automático").strip()
            mount = sh.get("mount", "Manual").strip()
            ro = sh.get("ro", False)

            if not host_path or not os.path.exists(host_path):
                log.warning(f"Carpeta compartida omitida (ruta inválida): {host_path}")
                continue

            safe_tag = tag.replace(" ", "_").replace("/", "_")
            effective_method = method if method and method != "Automático" else ("VirtioFS" if self._virtiofsd_available() else "9p")

            if effective_method == "9p":
                security_model = "passthrough" if not ro else "readonly"
                args.extend([
                    "-fsdev", f"local,id=fsdev_{safe_tag},path={host_path},security_model={security_model}",
                    "-device", f"virtio-9p-pci,fsdev=fsdev_{safe_tag},mount_tag={safe_tag}",
                ])
                log.info(f"Shared folder 9p: {host_path} -> tag {safe_tag} (ro={ro})")

            elif effective_method == "VirtioFS":
                sock_path = f"/tmp/virtiofs-{vm.get('id', 'vm')}-{safe_tag}.sock"
                if self._ensure_virtiofsd(vm.get("id", "vm"), sock_path, host_path):
                    args.extend([
                        "-chardev", f"socket,id=char_virtiofs_{safe_tag},path={sock_path}",
                        "-device", f"vhost-user-fs-pci,chardev=char_virtiofs_{safe_tag},tag={safe_tag}",
                    ])
                    log.info(f"Shared folder VirtioFS: {host_path} -> tag {safe_tag} (sock={sock_path})")
                else:
                    log.warning(f"virtiofsd no disponible; usando 9p como fallback para {host_path}")
                    security_model = "passthrough" if not ro else "readonly"
                    args.extend([
                        "-fsdev", f"local,id=fsdev_{safe_tag},path={host_path},security_model={security_model}",
                        "-device", f"virtio-9p-pci,fsdev=fsdev_{safe_tag},mount_tag={safe_tag}",
                    ])

            elif method == "SMB":
                smb_id = f"smb{smb_net_index}"
                smb_net_index += 1
                args.extend([
                    "-netdev", f"user,id={smb_id},smb={host_path}",
                    "-device", "virtio-net-pci,netdev=" + smb_id,
                ])
                log.info(f"Shared folder SMB: {host_path} -> netdev {smb_id}")

        return args

    def _build_passthrough_args(self, vm: dict) -> list[str]:
        args = []
        if IS_WINDOWS:
            # Passthrough de PCI/USB via vfio no disponible en Windows
            log.warning("PCI/USB passthrough no soportado en Windows.")
            return args
        from . import host_passthrough
        for dev in vm.get("passthrough_devices", []):
            dtype = dev.get("type", "")

            if dtype == "PCI":
                did = dev.get("id", "")
                is_bdf = did.count(":") == 2 and "." in did
                if is_bdf:
                    driver_path = f"/sys/bus/pci/devices/{did}/driver"
                    current_driver = ""
                    if os.path.exists(driver_path):
                        try: current_driver = os.path.basename(os.readlink(driver_path))
                        except: pass

                    if current_driver != "vfio-pci":
                        log.info(f"Vinculando {did} a vfio-pci (driver: {current_driver})...")
                        if not host_passthrough.dynamic_bind_vfio(did):
                            raise RuntimeError(f"Cancelado o fallido al enlazar {did} a vfio-pci. Abortando arranque de VM para evitar crash.")
                        time.sleep(1.5)

                    opts = [f"host={did}"]
                    if dev.get("is_vga", False):
                        opts.append("x-vga=on")
                        opts.append("multifunction=on")
                    args.extend(["-device", "vfio-pci," + ",".join(opts)])
                else:
                    log.error(f"PCI passthrough con id inválido '{did}'. Se omite.")

            elif dtype == "USB":
                vid_did = dev.get("vid_did", "")
                if ":" in vid_did:
                    vid, pid = vid_did.split(":", 1)
                    args.extend(["-device", f"usb-host,bus=xhci.0,vendorid=0x{vid},productid=0x{pid}"])
                else:
                    did = dev.get("id", "")
                    if did.count(":") == 1:
                        bus, addr = did.split(":", 1)
                        args.extend(["-device", f"usb-host,bus=xhci.0,hostbus={bus},hostaddr={addr}"])
                    else:
                        log.error(f"USB passthrough con id inválido '{did}'. Se omite.")
        return args

    def _launch_external_viewer(self, vm_id: str, info: dict):
        if not info: return None
        vtype = info.get("type")
        
        if vtype == "vnc":
            cmd = ["remote-viewer", f"vnc://127.0.0.1:{info['port']}"]
        elif vtype == "spice_unix":
            cmd = ["remote-viewer", f"spice+unix://{info['path']}"]
        elif vtype in ("spice_remote", "spice_tcp"):
            # Windows/named-pipe no existe en el servidor SPICE de QEMU: el
            # transporte local equivalente es TCP en el loopback.
            cmd = ["remote-viewer", f"spice://127.0.0.1:{info['port']}"]
        else:
            cmd = ["remote-viewer", f"spice://127.0.0.1:{info.get('port', 5930)}"]

        if not shutil.which(cmd[0]): 
            log.warning(f"{cmd[0]} no encontrado.")
            return None

        # Con SPICE gl=on sobre socket Unix, QEMU pasa el DMA-BUF fd
        # mediante sendfd(). start_new_session=True aísla al hijo en una
        # nueva sesión sin herencia de fds, lo que provoca
        # "dup: Bad file descriptor" / "sendfd: Bad file descriptor" y
        # deja la ventana en negro. Se omite start_new_session en ese caso.
        uses_gl_unix = (vtype == "spice_unix")
        
        # Si es socket Unix con GL, esperamos a que el socket exista
        # (hasta 5 s) para que QEMU haya terminado de inicializar el
        # contexto EGL antes de que remote-viewer se conecte.
        if uses_gl_unix:
            sock_path = info["path"]
            deadline = time.time() + 5.0
            while not os.path.exists(sock_path) and time.time() < deadline:
                time.sleep(0.1)
            if not os.path.exists(sock_path):
                log.warning(f"Socket SPICE no apareció en 5 s: {sock_path}")
            
        try:
            kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not uses_gl_unix:
                kwargs["start_new_session"] = True
            # glycin (cargador de imágenes de GTK4) usa bwrap para sandboxear.
            # En kernels que no permiten user namespaces, bwrap falla con
            # "Operation not permitted" y remote-viewer crashea al arrancar.
            # GLYCIN_DISABLE_SANDBOX desactiva el sandbox y lo evita.
            env = os.environ.copy()
            env["GLYCIN_DISABLE_SANDBOX"] = "1"
            kwargs["env"] = env
            proc = subprocess.Popen(cmd, **kwargs)
            log.info(f"Viewer externo '{cmd[0]}' lanzado para {vm_id}")
            return proc
        except Exception as e: 
            log.warning(f"Fallo lanzando '{cmd[0]}': {e}")
        return None

    def _kill_external_viewer(self, vm_id: str):
        viewer = self.active_viewers.pop(vm_id, None)
        if viewer and viewer.poll() is None:
            viewer.terminate()
            try: viewer.wait(timeout=3)
            except: viewer.kill()

    def _get_optical_drives(self, vm: dict) -> list:
        drives = list(vm.get("optical_drives") or [])
        iso_path = vm.get("iso_path")
        source_type = vm.get("iso_source_type", "")
        if not drives and (iso_path or source_type):
            drives = [{
                "path": iso_path or "",
                "source_type": source_type or "Usar ISO/IMG/DMG existente",
                "bus": vm.get("cdrom_bus", "SATA/AHCI"),
            }]
        known_paths = {d.get("path") for d in drives}
        for entry in (vm.get("boot_order") or []):
            if entry.startswith("Unidad óptica — "):
                p = entry[len("Unidad óptica — "):]
                if p and p not in known_paths and p not in ("Descargar automáticamente", "Vacío"):
                    exists = os.path.exists(p)
                    drives.append({
                        "path": p if exists else "",
                        "source_type": "Usar ISO/IMG/DMG existente" if exists else "Mantener vacío",
                        "bus": vm.get("cdrom_bus", "SATA/AHCI"),
                    })
                    known_paths.add(p)
        return drives

    def _assign_boot_indices(self, vm: dict, n_cdroms: int) -> dict:
        boot_order = vm.get("boot_order") or []
        drives = self._get_optical_drives(vm)
        cdrom_paths = [d.get("path", "") for d in drives][:n_cdroms]
        result = {"disk": None, "cdroms": [None] * n_cdroms, "net": None}
        idx = 1
        for entry in boot_order:
            if entry.startswith("Unidad óptica"):
                path = entry.split(" — ", 1)[1] if " — " in entry else ""
                ci = None
                if path:
                    for i, p in enumerate(cdrom_paths):
                        if p == path and result["cdroms"][i] is None:
                            ci = i
                            break
                if ci is None:
                    for i in range(n_cdroms):
                        if result["cdroms"][i] is None:
                            ci = i
                            break
                if ci is not None:
                    result["cdroms"][ci] = idx
                    idx += 1
            elif entry.startswith("Disco Duro") and result["disk"] is None:
                result["disk"] = idx
                idx += 1
            elif entry.startswith("Red/PXE") and result["net"] is None:
                result["net"] = idx
                idx += 1
        for i in range(n_cdroms):
            if result["cdroms"][i] is None:
                result["cdroms"][i] = idx
                idx += 1
        if result["disk"] is None:
            result["disk"] = idx
            idx += 1
        if result["net"] is None:
            result["net"] = idx
        return result

    def _build_cdrom_args(self, vm: dict, q35: bool) -> list[str]:
        drives = self._get_optical_drives(vm)
        if not drives:
            return []
        boot_indices = self._assign_boot_indices(vm, len(drives))
        args = []
        
        has_disk = bool(vm.get("disk_path") and os.path.exists(vm.get("disk_path")))
        
        ahci_idx = 1 if has_disk else 0
        ahci_ctrl = 0
        
        scsi_created = False
        usb_idx = 0
        
        for idx, drive in enumerate(drives):
            iso_path = drive.get("path", "")
            cdrom_bus = drive.get("bus", "SATA/AHCI" if q35 else "IDE")
            if iso_path and os.path.exists(iso_path) and os.path.getsize(iso_path) > 0:
                file_opt = f"file={iso_path},format=raw"
            else:
                file_opt = ""
            drive_id = f"cdrom{idx}"
            args.extend(["-drive", f"id={drive_id},if=none,media=cdrom,{file_opt}".rstrip(",")])
            boot_idx = boot_indices["cdroms"][idx]
            boot_opt = f",bootindex={boot_idx}" if boot_idx else ""
            b = cdrom_bus.lower()
            
            if "sata" in b or "auto" in b:
                if ahci_idx > 5:
                    ahci_ctrl += 1
                    args.extend(["-device", f"ahci,id=ahci{ahci_ctrl}"])
                    ahci_idx = 0
                
                ctrl_name = f"ahci{ahci_ctrl}" if ahci_ctrl > 0 else "ahci"
                
                if ahci_ctrl == 0 and ahci_idx == 0 and not has_disk:
                    args.extend(["-device", "ahci,id=ahci"])
                
                args.extend(["-device", f"ide-cd,drive={drive_id},bus={ctrl_name}.{ahci_idx}{boot_opt}"])
                ahci_idx += 1
            elif "scsi" in b:
                if not scsi_created:
                    args.extend(["-device", "lsi53c895a,id=scsi0"])
                    scsi_created = True
                args.extend(["-device", f"scsi-cd,drive={drive_id},bus=scsi0.{idx}{boot_opt}"])
            elif "usb" in b:
                args.extend(["-device", f"usb-storage,drive={drive_id},id=usbcd{usb_idx}{boot_opt}"])
                usb_idx += 1
            else:
                args.extend(["-device", f"ide-cd,drive={drive_id},bus=ide.{idx}{boot_opt}"])
                
        return args

    def _build_boot_args(self, vm: dict) -> list[str]:
        boot_order = vm.get("boot_order", []) or []
        has_iso = any(d.get("path") for d in self._get_optical_drives(vm))
        order_map = [("Disco Duro", "c"), ("Unidad óptica", "d"), ("CD/DVD", "d"), ("Red/PXE", "n")]
        qemu_order = ""
        for entry in boot_order:
            for key, letter in order_map:
                if entry.startswith(key) and letter not in qemu_order:
                    qemu_order += letter
                    break
        if qemu_order:
            return ["-boot", f"order={qemu_order},menu=on"]
        if has_iso and not vm.get("disk_path"):
            return ["-boot", "order=d,menu=on"]
        return []

    def build_command(self, vm: Dict) -> list[str]:
        if not self.host.qemu_path: raise RuntimeError("QEMU no instalado.")
        disk_path = vm.get("disk_path")
        disk_format = vm.get("disk_format", "qcow2")

        if disk_path:
            # Respetar el formato detectado y guardado en la configuracion.
            # Solo usar la extension como fallback si no hay disco_format valido.
            ext = os.path.splitext(disk_path)[1].lower().lstrip(".")
            ext_fmt = {"img": "raw", "raw": "raw", "vdi": "vdi", "vmdk": "vmdk",
                       "vhd": "vpc", "vhdx": "vhdx", "qcow2": "qcow2", "qcow": "qcow"}.get(ext)
            if not disk_format or disk_format not in ("qcow2","qcow","raw","vdi","vmdk","vpc","vhdx","vhd"):
                disk_format = ext_fmt or disk_format
            self._kill_orphan_qemu(disk_path, vm.get("id"))

        gvtg_vgpu_uuid = None
        if vm.get("gvtg_enabled", False):
            profile = vm.get("gvtg_profile", "i915-GVTg_V5_4")
            gvtg_vgpu_uuid = self._prepare_gvtg_vgpu(vm["id"], profile)
            if gvtg_vgpu_uuid:
                self.gvtg_uuids[vm["id"]] = gvtg_vgpu_uuid
            else:
                log.error("Fallo al crear la vGPU. Se usará el video virtual estándar.")
                vm = dict(vm)
                vm["gvtg_enabled"] = False

        is_macos = (vm.get("platform", "") == "macOS")
        q35 = True if is_macos else (vm.get("chipset_idx", 0) == 1)
        machine_type = "q35" if q35 else "pc"

        cmd = [self.host.qemu_path, "-machine", machine_type] + self.host.get_accel_args()
        if not is_macos and self._is_windows_guest(vm):
            # Windows cuenta en hora local; sincronizar con clock del host
            cmd.extend(["-rtc", "base=localtime,clock=host"])
            if self.host.acceleration == "kvm":
                # Descarta ticks perdidos del PIT: menos latencia de timer en Windows
                cmd.extend(["-global", "kvm-pit.lost_tick_policy=discard"])
        cmd.extend(["-cpu"] + (["Skylake-Client,-hle,-rtm,kvm=on,vendor=GenuineIntel,+invtsc,vmware-cpuid-freq=on,+ssse3,+sse4.2,+popcnt,+avx,+aes,+xsave,+xsaveopt,check"] if is_macos else self._build_cpu_args(vm)))

        ram_mb = ((vm.get("ram", 4096) + 1023) // 1024) * 1024 if is_macos else vm.get("ram", 4096)
        cmd.extend(["-m", str(ram_mb)])

        hugepages = bool(vm.get("hugepages"))
        prealloc = bool(vm.get("prealloc"))
        if hugepages or prealloc:
            cmd.extend(self._build_memory_args(vm, ram_mb, hugepages, prealloc))

        total_cores = vm.get("cores", 2)
        if vm.get("cpu_topology", False):
            s, c, t = vm.get("cpu_sockets", 1), vm.get("cpu_cores_per_socket", 2), vm.get("cpu_threads_per_core", 1)
            cmd.extend(["-smp", f"{s*c*t},sockets={s},cores={c},threads={t}"])
        else:
            cmd.extend(["-smp", str(total_cores)])

        if vm.get("firmware_idx", 0) == 1:
            code_path, vars_path = self._find_ovmf(vm.get("secure_boot", False))
            if code_path and vars_path:
                vm_dir = os.path.join(str(self.vms_dir), vm["id"])
                os.makedirs(vm_dir, exist_ok=True)
                local_vars = os.path.join(vm_dir, "OVMF_VARS.fd")
                if not os.path.exists(local_vars) or os.path.getsize(local_vars) != os.path.getsize(vars_path):
                    shutil.copy(vars_path, local_vars)
                cmd.extend(["-drive", f"if=pflash,format=raw,readonly=on,file={code_path}", "-drive", f"if=pflash,format=raw,file={local_vars}"])

        if vm.get("tpm", False) and not is_macos:
            cmd.extend(self._setup_tpm(vm, q35))

        if is_macos:
            cmd.extend(["-device", "ich9-ahci,id=sata"])
            project_root = Path(__file__).parent.parent
            opencore_candidates = [project_root / "OSX-KVM" / "OpenCore" / "OpenCore.qcow2", self.data_dir / "OSX-KVM" / "OpenCore" / "OpenCore.qcow2"]
            opencore_path = next((p for p in opencore_candidates if p.exists()), None)
            if not opencore_path: raise RuntimeError("No se encontró OpenCore.qcow2.")

            cmd.extend(["-drive", f"id=OpenCoreBoot,if=none,snapshot=on,format=qcow2,file={opencore_path}", "-device", "ide-hd,bus=sata.2,drive=OpenCoreBoot"])
            osk = "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
            cmd.extend(["-device", f"isa-applesmc,osk=\"{osk}\"", "-smbios", "type=2"])
            cmd.extend(["-global", "ICH9-LPC.disable_s3=1", "-global", "ICH9-LPC.disable_s4=1"])
            cmd.extend(["-device", "usb-ehci,id=ehci"])

            if disk_path and os.path.exists(disk_path):
                cmd.extend(["-drive", f"id=MacHDD,if=none,file={disk_path},format={disk_format}", "-device", "ide-hd,bus=sata.4,drive=MacHDD"])
            iso_path = vm.get("iso_path")
            if iso_path and os.path.exists(iso_path):
                cmd.extend(["-drive", f"id=InstallMedia,if=none,file={iso_path},format=raw", "-device", "ide-hd,bus=sata.3,drive=InstallMedia"])

            cmd.extend(["-device", "ich9-intel-hda", "-device", "hda-duplex", "-device", "vmware-svga"])
            cmd.extend(["-netdev", "user,id=net0,hostfwd=tcp::2222-:22"])
            if any(v in vm.get("version", "") for v in ["High Sierra", "Mojave", "Catalina"]):
                cmd.extend(["-device", "vmxnet3,netdev=net0,id=net0,mac=52:54:00:c9:18:27"])
            else:
                cmd.extend(["-device", "virtio-net-pci,netdev=net0,id=net0,mac=52:54:00:c9:18:27"])

            cmd.extend(["-device", "qemu-xhci,id=xhci", "-device", "usb-kbd,bus=xhci.0", "-device", "usb-tablet,bus=xhci.0", "-boot", "menu=on"])
            qmp_socket = self._get_qmp_socket_path(vm["id"])
            if IS_WINDOWS:
                cmd.extend(["-qmp", f"{qmp_socket},server=on,wait=off"])
            else:
                if os.path.exists(qmp_socket):
                    try: os.remove(qmp_socket)
                    except: pass
                vm["qmp_socket"] = qmp_socket
                cmd.extend(["-qmp", f"unix:{qmp_socket},server=on,wait=off"])

            vnc_port = self._find_free_vnc_port()
            vm["vnc_port"] = vnc_port
            cmd.extend(["-vnc", self._vnc_target(vnc_port)])
            vm["_pending_external_viewer"] = None
            return cmd

        if disk_path and os.path.exists(disk_path):
            disk_bus = vm.get("disk_bus", "sata").lower()
            opts = [f"file={disk_path},format={disk_format}"]

            # Caché de disco (UI: Automático (writeback) | none | writeback | writethrough)
            disk_cache = str(vm.get("disk_cache", "") or "").lower()
            for cand in ("none", "writethrough", "writeback"):
                if cand in disk_cache:
                    opts.append(f"cache={cand}")
                    break

            # Backend AIO (UI "Backend I/O (io=)": Automático (threads) | threads | native | io_uring)
            # y compatibilidad con la clave antigua "disk_aio" (threads | native)
            disk_io = str(vm.get("disk_io", "") or "").lower()
            disk_aio = str(vm.get("disk_aio", "") or "").lower()
            aio_selected = ""
            if "io_uring" in disk_io: aio_selected = "io_uring"
            elif "native" in disk_io: aio_selected = "native"
            elif "threads" in disk_io: aio_selected = "threads"
            elif "native" in disk_aio: aio_selected = "native"
            elif "threads" in disk_aio: aio_selected = "threads"
            if aio_selected:
                opts.append(f"aio={aio_selected}")

            # Discard (TRIM) y detect-zeros para crecimiento dinámico/compactación
            disk_discard = str(vm.get("disk_discard", "") or "").lower()
            if "unmap" in disk_discard:
                opts.append("discard=unmap")
            disk_dz = str(vm.get("disk_detect_zeros", "") or "").lower()
            if disk_dz == "on":
                opts.append("detect-zeros=on")
            elif "unmap" in disk_dz:
                opts.append("detect-zeros=unmap")

            # El hilo de I/O se añade en el DISPOSITIVO virtio (virtio-blk/virtio-scsi lo soportan, SATA/IDE/NVMe no)
            use_iothread = ("virtio-scsi" in disk_bus or "virtio" in disk_bus)
            iothread_suffix = ""
            if use_iothread:
                cmd.extend(["-object", "iothread,id=iothread0"])
                iothread_suffix = ",iothread=iothread0"

            opts_str = ",".join(opts)

            boot_indices = self._assign_boot_indices(vm, len(self._get_optical_drives(vm)))
            disk_boot = f",bootindex={boot_indices['disk']}" if boot_indices["disk"] else ""

            if "nvme" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", f"nvme,serial=1234,drive=disk0{disk_boot}"])
            elif "virtio-scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", f"virtio-scsi-pci,id=scsi0{iothread_suffix}", "-device", f"scsi-hd,drive=disk0,bus=scsi0.0{disk_boot}"])
            elif "virtio" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", f"virtio-blk-pci,drive=disk0{iothread_suffix}{disk_boot}"])
            elif "scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "lsi53c895a,id=scsi0", "-device", f"scsi-hd,drive=disk0,bus=scsi0.0{disk_boot}"])
            elif "ide" in disk_bus and not q35:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", f"ide-hd,drive=disk0,bus=ide.0{disk_boot}"])
            else:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "ahci,id=ahci", "-device", f"ide-hd,drive=disk0,bus=ahci.0{disk_boot}"])
        else:
            boot_indices = self._assign_boot_indices(vm, len(self._get_optical_drives(vm)))

        cmd.extend(self._build_cdrom_args(vm, q35))
        cmd.extend(self._build_boot_args(vm))

        for i, net in enumerate(vm.get("network_adapters", []) or [{"model": "VirtIO"}]):
            dev_model = "virtio-net-pci"
            if "e1000" in net.get("model", "").lower(): dev_model = "e1000"
            elif "vmxnet3" in net.get("model", "").lower(): dev_model = "vmxnet3"
            net_boot = ""
            if i == 0 and boot_indices.get("net"):
                net_boot = f",bootindex={boot_indices['net']}"
            cmd.extend(["-netdev", f"user,id=net{i}", "-device", f"{dev_model},netdev=net{i}{net_boot}"])

        # --- MEMLOCK ("Bloquear RAM"): mlockall de la RAM de la VM en el host ---
        if vm.get("memfd"):
            if self._mlock_possible(ram_mb):
                cmd.extend(["-overcommit", "mem-lock=on"])
                log.info("Bloqueo de RAM (mem-lock) activado.")
            else:
                log.warning(
                    "Bloqueo de RAM solicitado pero RLIMIT_MEMLOCK es insuficiente; "
                    "omitiendo. Aumenta ulimit -l o ejecuta la app con privilegios.")

        # Free Page Reporting: incompatible útil con prealloc/hugepages/mem-lock (la RAM ya está reservada)
        free_page_reporting = bool(vm.get("free_page_reporting", True))
        if free_page_reporting and (hugepages or prealloc or vm.get("memfd")):
            log.info("Free Page Reporting desactivado: prealloc/hugepages/mem-lock en uso.")
            free_page_reporting = False

        # --- SOPORTE PARA FREE PAGE REPORTING ---
        if free_page_reporting:
            cmd.extend(["-device", "virtio-balloon-pci,free-page-reporting=on"])
            log.info("Free Page Reporting habilitado.")

        cmd.extend(self._build_graphics_device_args(vm))

        proto_args, external_info = self._build_display_protocol_args(vm, gvtg_active=bool(gvtg_vgpu_uuid))
        cmd.extend(proto_args)
        vm["_pending_external_viewer"] = external_info

        # Entropía para el invitado (acelera arranque y getrandom(): systemd, SSL, LUKS...)
        if IS_WINDOWS:
            cmd.extend(["-object", "rng-builtin,id=rng0", "-device", "virtio-rng-pci,rng=rng0"])
        else:
            cmd.extend(["-object", "rng-random,id=rng0,filename=/dev/urandom", "-device", "virtio-rng-pci,rng=rng0"])

        # Ratón/teclado y audio según configuración de la VM
        cmd.extend(self._build_pointer_args(vm))
        cmd.extend(self._build_audio_args(vm))

        if gvtg_vgpu_uuid:
            cmd.extend([
                "-device",
                f"vfio-pci-nohotplug,sysfsdev=/sys/bus/mdev/devices/{gvtg_vgpu_uuid},"
                f"display=off,x-igd-opregion=on,ramfb=on"
            ])
        else:
            cmd.extend(self._build_passthrough_args(vm))

        cmd.extend(self._build_shared_folder_args(vm))
        cmd.extend(self._build_guest_agent_args(vm))

        qmp_socket = self._get_qmp_socket_path(vm["id"])
        if IS_WINDOWS:
            cmd.extend(["-qmp", f"{qmp_socket},server=on,wait=off"])
        else:
            if os.path.exists(qmp_socket):
                try: os.remove(qmp_socket)
                except: pass
            vm["qmp_socket"] = qmp_socket
            cmd.extend(["-qmp", f"unix:{qmp_socket},server=on,wait=off"])

        return cmd

    def start_vm(self, vm: Dict) -> subprocess.Popen:
        vm_id = vm.get("id", "unknown")
        if vm_id in self.active_processes: return self.active_processes[vm_id]
        try:
            cmd = self.build_command(vm)
            log.info(f"Comando QEMU: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)

            def _drain_output(proc, vid):
                try:
                    for line in proc.stdout:
                        line = line.rstrip()
                        if line:
                            log.info(f"[QEMU {vid}] {line}")
                except Exception:
                    pass
            threading.Thread(target=_drain_output, args=(process, vm_id), daemon=True).start()

            time.sleep(2.5)
            if process.poll() is not None:
                stdout, _ = process.communicate()
                raise RuntimeError(f"QEMU falló al arrancar: {stdout.strip()}")
            self.active_processes[vm_id] = process
            ext_info = vm.pop("_pending_external_viewer", None)
            if ext_info:
                viewer = self._launch_external_viewer(vm_id, ext_info)
                if viewer: self.active_viewers[vm_id] = viewer

            shared = vm.get("shared_folders", []) or []
            auto_mount = any(sh.get("mount", "").startswith("Automático") for sh in shared)
            if auto_mount:
                threading.Thread(
                    target=self._auto_mount_shared_folders,
                    args=(vm_id, shared), daemon=True
                ).start()

            return process
        except Exception as e:
            log.error(f"Error lanzando QEMU: {e}")
            self._cleanup_gvtg_vgpu(vm_id)
            raise

    def _get_qmp_socket_path(self, vm_id: str) -> str:
        """Devuelve el socket QMP asignado a esta VM (estable durante su vida)."""
        if vm_id in self._qmp_sockets:
            return self._qmp_sockets[vm_id]
        if IS_WINDOWS:
            # Un puerto libre distinto por VM: "libre" no implica "no usado
            # por otra VM arrancada en este proceso", así que lo evitamos.
            used = set(self._qmp_sockets.values())
            endpoint = ""
            for _ in range(64):
                candidate = f"tcp:127.0.0.1:{self._find_free_port(4444, 4500)}"
                if candidate not in used:
                    endpoint = candidate
                    break
            if not endpoint:
                raise RuntimeError("No hay puertos QMP libres para la VM")
        else:
            safe_id = "".join(ch for ch in str(vm_id)
                              if ch.isalnum() or ch in "-_")[:64] or "vm"
            endpoint = f"/tmp/qemu-{safe_id}-qmp.sock"
        self._qmp_sockets[vm_id] = endpoint
        return endpoint

    def _get_tmp_socket_path(self, vm_id: str, prefix: str = "qemu") -> str:
        """Ruta de socket temporal multiplataforma."""
        if IS_WINDOWS:
            tmp = os.environ.get("TEMP", "C:\\Temp")
            return f"{tmp}\\{prefix}-{vm_id}.sock"
        return f"/tmp/{prefix}-{vm_id}.sock"

    @staticmethod
    def _qmp_read_line(sock, buffer):
        """Lee una línea del stream QMP conservando el sobrante en ``buffer``."""
        while b"\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                return None, buffer
            buffer += chunk
        line, buffer = buffer.split(b"\n", 1)
        return line, buffer

    def _qmp_call(self, qmp_sock: str, command: str, arguments: dict = None):
        """Ejecuta un comando QMP sobre Unix socket o TCP (Windows).

        Un único lector con buffer evita que un solo ``recv()`` se coma el
        banner, la respuesta de capabilities y la del comando a la vez.
        """
        try:
            if IS_WINDOWS:
                # qmp_sock = "tcp:127.0.0.1:PORT"
                _, host, port_str = qmp_sock.split(":")
                address = (host, int(port_str))
                family = socket.AF_INET
            else:
                if not os.path.exists(qmp_sock):
                    return None
                address = qmp_sock
                family = socket.AF_UNIX

            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect(address)
                buffer = b""

                _, buffer = self._qmp_read_line(s, buffer)  # banner
                s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode() + b"\n")
                line, buffer = self._qmp_read_line(s, buffer)
                if line:
                    try:
                        caps = json.loads(line.decode(errors="replace"))
                        if caps.get("error"):
                            return caps
                    except json.JSONDecodeError:
                        pass

                payload = {"execute": command}
                if arguments:
                    payload["arguments"] = arguments
                s.sendall(json.dumps(payload).encode() + b"\n")

                while True:
                    line, buffer = self._qmp_read_line(s, buffer)
                    if line is None:
                        return None
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line.decode(errors="replace"))
                    except json.JSONDecodeError:
                        continue
                    if "event" in msg:
                        continue
                    if "return" in msg or "error" in msg:
                        return msg
        except Exception as e:
            log.debug("QMP %s falló: %s", command, e)
            return None

    def _auto_mount_shared_folders(self, vm_id: str, shared_folders: list):
        import shlex
        if IS_WINDOWS:
            log.info("Montaje automático de carpetas compartidas no soportado en Windows (requiere Guest Agent Linux).")
            return
        qmp_sock = self._get_qmp_socket_path(vm_id)

        def _guest_exec(cmdline: str, timeout: int = 60):
            resp = self._qmp_call(qmp_sock, "guest-exec", {
                "path": "/bin/sh", "arg": ["-c", cmdline], "capture-output": True,
            })
            if not isinstance(resp, dict) or "pid" not in resp:
                return False, f"guest-exec no aceptó el comando: {resp}"
            pid = resp["pid"]
            for _ in range(max(1, int(timeout / 2))):
                st = self._qmp_call(qmp_sock, "guest-exec-status", {"pid": pid})
                if isinstance(st, dict) and st.get("return", {}).get("exited"):
                    code = st["return"].get("exitcode", -1)
                    if code == 0:
                        return True, "ok"
                    detail = f"exit={code}"
                    err = st["return"].get("err-data")
                    if err:
                        import base64
                        try:
                            detail += " " + base64.b64decode(err).decode(errors="replace").strip()[:300]
                        except Exception:
                            pass
                    return False, detail
                time.sleep(2)
            return False, "timeout esperando guest-exec-status"

        log.info("Esperando al Guest Agent del invitado para montar carpetas compartidas...")
        agent_ready = False
        start = time.time()
        last_log = start
        channel_seen = False
        while True:
            elapsed = time.time() - start
            if os.path.exists(qmp_sock):
                channel_seen = True
                resp = self._qmp_call(qmp_sock, "guest-ping")
                if isinstance(resp, dict) and "return" in resp:
                    agent_ready = True
                    break
            elif channel_seen and elapsed > 5:
                log.info("La VM se apagó durante la espera del Guest Agent.")
                return
            if elapsed >= 180:
                log.warning(
                    f"El Guest Agent no respondió en 180s en {vm_id}: montaje automático "
                    "omitido. Instala e inicia qemu-guest-agent en el guest (Compartición → Guest Tools)."
                )
                return
            if time.time() - last_log >= 30:
                log.info(f"Esperando al Guest Agent del invitado ({int(elapsed)} s)...")
                last_log = time.time()
            time.sleep(3)
        log.info("Guest Agent listo; configurando montajes.")

        q = shlex.quote
        for sh in shared_folders:
            mount = sh.get("mount", "Manual").strip()
            if not mount.startswith("Automático"):
                continue

            tag = sh.get("guest", "share").strip() or "share"
            method = sh.get("method", "Automático").strip()
            ro = sh.get("ro", False)
            safe_tag = tag.replace(" ", "_").replace("/", "_")
            mount_point = f"/media/{safe_tag}"
            rw_flag = "ro" if ro else "rw"

            effective_method = method if method and method != "Automático" else ("VirtioFS" if self._virtiofsd_available() else "9p")
            if effective_method == "9p":
                fstype, fs_opts, source = "9p", f"trans=virtio,version=9p2000.L,{rw_flag}", tag
            elif effective_method == "VirtioFS":
                fstype, fs_opts, source = "virtiofs", rw_flag, tag
            elif effective_method == "SMB":
                fstype, fs_opts, source = "cifs", f"guest,{rw_flag}", f"//localhost/{tag}"
            else:
                continue
            mount_opts = f"nofail,x-gvfs-show,{fs_opts}"
            fstab_line = f"{source} {mount_point} {fstype} {mount_opts} 0 0"

            bookmark_uri = "file://" + mount_point
            script = "\n".join([
                "set -e",
                f"mkdir -p {q(mount_point)}",
                "touch /etc/fstab",
                f"awk -v mp={q(mount_point)} '$2!=mp' /etc/fstab > /tmp/.fstab.vmfix",
                "cat /tmp/.fstab.vmfix > /etc/fstab",
                "rm -f /tmp/.fstab.vmfix",
                f"printf '%s\\n' {q(fstab_line)} >> /etc/fstab",
                "systemctl daemon-reload",
                f"umount {q(mount_point)} 2>/dev/null || true",
                f"UNIT=$(systemd-escape -p --suffix=mount {q(mount_point)})",
                'systemctl start "$UNIT"',
                f"grep -q ' {mount_point} ' /proc/mounts",
                f"BM_URI={q(bookmark_uri)}",
                f"BM_LABEL={q(safe_tag)}",
                "for _u in $(getent passwd | awk -F: '$3>=1000 && $3<60000 && $7!~/nologin|false/ {print $1}'); do",
                "  _h=$(getent passwd \"$_u\" | awk -F: '{print $6}')",
                "  [ -n \"$_h\" ] && [ -d \"$_h\" ] || continue",
                "  _bd=\"$_h/.config/gtk-3.0\"",
                "  mkdir -p \"$_bd\"",
                "  _bf=\"$_bd/bookmarks\"",
                "  touch \"$_bf\"",
                "  _bl=\"$BM_URI $BM_LABEL\"",
                "  grep -Fqx -- \"$_bl\" \"$_bf\" || echo \"$_bl\" >> \"$_bf\"",
                "  chown \"$_u:\" \"$_bd\" 2>/dev/null || true",
                "  chown \"$_u:\" \"$_bf\" 2>/dev/null || true",
                "done",
            ])
            log.info(f"Configurando montaje automático (antes del login) en {mount_point} [{fstype}]...")
            ok, detail = _guest_exec(script, timeout=60)
            if ok:
                log.info(f"✓ Montado en {mount_point} ({'solo lectura' if ro else 'lectura/escritura'}); "
                         "visible en el panel del explorador.")
            else:
                log.warning(f"Fallo el montaje de {mount_point}: {detail}")

    def _qmp_command(self, vm_id, command, arguments=None):
        """Envía un comando simple usando el cliente QMP compartido.

        La implementación anterior usaba una variable ``qmp_sock`` inexistente
        en Windows y una segunda copia del protocolo que nunca leía la
        respuesta real. Aquí reutilizamos ``_qmp_call``, que ya funciona en
        Unix y TCP.
        """
        resp = self._qmp_call(
            self._get_qmp_socket_path(vm_id), command, arguments)
        if isinstance(resp, dict) and "error" in resp:
            log.warning("QMP %s en %s rechazado: %s", command, vm_id,
                        resp["error"])
            return False
        return isinstance(resp, dict) and "return" in resp

    def change_iso(self, vm_id: str, iso_path: str) -> bool:
        """Sustituye la ISO del lector de CD/DVD de una VM en ejecución."""
        if not iso_path or not os.path.isfile(iso_path):
            log.warning("No se puede cambiar la ISO: %r no existe", iso_path)
            return False

        cdrom_id = None
        resp = self._qmp_call(self._get_qmp_socket_path(vm_id), "query-block")
        if isinstance(resp, dict) and "return" in resp:
            for block in resp["return"]:
                device = str(block.get("device", ""))
                if "cdrom" in device.lower() or "ide" in device.lower():
                    cdrom_id = device
                    break
        if not cdrom_id:
            log.warning("No se encontró lector de CD en %s; se usa cdrom0", vm_id)
            cdrom_id = "cdrom0"

        ok, msg = self.hotplug_cdrom(vm_id, cdrom_id, iso_path)
        if not ok:
            log.warning("change_iso en %s falló: %s", vm_id, msg)
        return ok

    def stop_vm(self, vm_id: str):
        self._kill_external_viewer(vm_id)
        process = self.active_processes.get(vm_id)
        if process:
            if not self._qmp_command(vm_id, "system_powerdown"): process.terminate()
            try: process.wait(timeout=15)
            except: process.kill()
            del self.active_processes[vm_id]
        self._qmp_sockets.pop(vm_id, None)

        self._kill_virtiofsd(vm_id)
        self._cleanup_gvtg_vgpu(vm_id)

    def force_stop_vm(self, vm_id: str):
        self._kill_external_viewer(vm_id)
        process = self.active_processes.get(vm_id)
        if process:
            process.kill()
            del self.active_processes[vm_id]
        self._qmp_sockets.pop(vm_id, None)

        self._kill_virtiofsd(vm_id)
        self._cleanup_gvtg_vgpu(vm_id)

    def pause_vm(self, vm_id: str):
        if not self._qmp_command(vm_id, "stop"):
            if not IS_WINDOWS:
                if process := self.active_processes.get(vm_id): process.send_signal(19)

    def resume_vm(self, vm_id: str):
        if not self._qmp_command(vm_id, "cont"):
            if not IS_WINDOWS:
                if process := self.active_processes.get(vm_id): process.send_signal(18)

    # --- HOTPLUG: CD/DVD ---

    def hotplug_cdrom(self, vm_id: str, cdrom_id: str, iso_path: str) -> tuple[bool, str]:
        if not os.path.exists(iso_path):
            return False, "El archivo ISO no existe."

        qmp_socket = self._get_qmp_socket_path(vm_id)
        if IS_WINDOWS:
            # En Windows no podemos verificar existencia del socket TCP fácilmente
            pass
        elif not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."

        self._qmp_call(qmp_socket, "blockdev-close-tray", {"device": cdrom_id})

        args = {"device": cdrom_id, "filename": iso_path, "format": "raw"}
        resp = self._qmp_call(qmp_socket, "blockdev-change-medium", args)
        log.info(f"QMP blockdev-change-medium[{cdrom_id}] -> {resp}")

        if resp and "return" in resp:
            log.info(f"ISO insertada en caliente en {cdrom_id}: {iso_path}")
            return True, "ISO insertada correctamente."

        err = resp.get("error", {}).get("desc", "Error desconocido") if resp else "Sin respuesta"
        return False, f"Error de QEMU: {err}"

    def eject_cdrom(self, vm_id: str, cdrom_id: str) -> tuple[bool, str]:
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."

        # 1. Engañar al guest cambiando el medio a /dev/null.
        # Esto envía un evento SCSI de "medio cambiado" que obliga al sistema de archivos a soltar el ISO.
        self._qmp_call(qmp_socket, "blockdev-change-medium", {
            "device": cdrom_id,
            "filename": "/dev/null",
            "format": "raw"
        })

        # 2. Ejecutar umount dentro del guest (por si acaso el paso 1 dejó algo colgado)
        guest_cmd = "for d in /dev/sr*; do umount -l \"$d\" 2>/dev/null; umount -f \"$d\" 2>/dev/null; done"
        if not IS_WINDOWS:
            self._qmp_call(qmp_socket, "guest-exec", {
                "path": "/bin/sh", "arg": ["-c", guest_cmd], "capture-output": True
            })

        # 3. Expulsar físicamente (Abrir bandeja)
        self._qmp_call(qmp_socket, "blockdev-open-tray", {"device": cdrom_id, "force": True})

        # 4. Retirar el medio de QEMU
        self._qmp_call(qmp_socket, "blockdev-remove-medium", {"device": cdrom_id})

        # 5. Verificar en QEMU que realmente está vacío
        state = self._qmp_call(qmp_socket, "query-block")
        if state and "return" in state:
            for bd in state["return"]:
                if bd.get("device") == cdrom_id:
                    if "inserted" in bd:
                        # Si aún hay medio (muy raro), forzamos device_del como último recurso
                        log.warning(f"El CD {cdrom_id} sigue bloqueado. Forzando desconexión...")
                        self._qmp_call(qmp_socket, "device_del", {"id": cdrom_id})
                        return True, "Medio expulsado forzosamente (unidad reiniciada)."

        return True, "Medio expulsado correctamente."

    # --- HOTPLUG: USB ---

    def _grant_usb_access(self, bus: str, addr: str) -> tuple[bool, str]:
        if IS_WINDOWS:
            # USB passthrough no soportado en Windows
            return False, "USB passthrough no soportado en Windows."
        try:
            dev_node = f"/dev/bus/usb/{int(bus):03d}/{int(addr):03d}"
        except ValueError:
            return False, f"bus/addr inválidos: {bus}/{addr}"

        if not os.path.exists(dev_node):
            return False, f"No existe {dev_node}"

        st = os.stat(dev_node)
        if st.st_uid == os.getuid() and (st.st_mode & 0o600) == 0o600:
            return True, "Acceso ya concedido"

        uid, gid = os.getuid(), os.getgid()
        try:
            subprocess.run(
                ["pkexec", "sh", "-c",
                 f"chown {uid}:{gid} {dev_node} && chmod 660 {dev_node}"],
                check=True, capture_output=True, text=True, timeout=10
            )
            log.info(f"Permisos concedidos sobre {dev_node}")
            return True, "Acceso concedido"
        except subprocess.CalledProcessError as e:
            return False, f"pkexec falló: {(e.stderr or str(e)).strip()}"
        except subprocess.TimeoutExpired:
            return False, "pkexec timeout (¿polkit-agent activo?)"

    def get_connected_usb_devices(self, vm_id: str) -> list[str]:
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return []
        
        resp = self._qmp_call(qmp_socket, "qom-list", {"path": "/machine/peripheral"})
        connected = []
        if resp and "return" in resp:
            for item in resp["return"]:
                name = item.get("name", "")
                if name.startswith("usb_"):
                    parts = name.split("_")
                    if len(parts) == 3:
                        connected.append(f"{parts[1]}:{parts[2]}")
        return connected

    def hotplug_usb(self, vm_id: str, hostbus: str, hostaddr: str) -> tuple[bool, str]:
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."

        usb_id = f"usb_{hostbus}_{hostaddr}"
        args = {
            "driver": "usb-host",
            "id": usb_id,
            "bus": "xhci.0",
            "hostbus": int(hostbus),
            "hostaddr": int(hostaddr),
        }

        resp = self._qmp_call(qmp_socket, "device_add", args)
        log.info(f"QMP device_add {usb_id} -> {resp}")

        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            return False, f"Error al conectar USB: {err}"

        time.sleep(0.6)
        check = self._qmp_call(qmp_socket, "qom-list",
                               {"path": f"/machine/peripheral/{usb_id}"})
        log.info(f"QMP qom-list[/machine/peripheral/{usb_id}] -> {check}")

        if not (check and "return" in check):
            try:
                self._qmp_call(qmp_socket, "device_del", {"id": usb_id})
            except Exception:
                pass
            return False, (
                "QEMU no materializó el USB (fallo silencioso al abrirlo). "
                "Causas típicas: sin permisos sobre /dev/bus/usb, o dispositivo ocupado por el host."
            )

        rz = self._qmp_call(qmp_socket, "qom-get",
                            {"path": f"/machine/peripheral/{usb_id}",
                             "property": "realized"})
        log.info(f"QMP qom-get realized[{usb_id}] -> {rz}")
        if rz and "return" in rz and rz["return"] is not True:
            return False, "El USB quedó registrado pero no se realizó (realized=false)."

        log.info(f"Dispositivo USB (bus {hostbus}, addr {hostaddr}) conectado en caliente.")
        return True, "USB conectado."

    def remove_usb(self, vm_id: str, hostbus: str, hostaddr: str) -> tuple[bool, str]:
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."

        usb_id = f"usb_{hostbus}_{hostaddr}"
        args = {"id": usb_id}
        resp = self._qmp_call(qmp_socket, "device_del", args)
        log.info(f"QMP device_del {usb_id} -> {resp}")

        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            if "not found" in err.lower() or "not exist" in err.lower():
                return True, "El USB ya estaba desconectado."
            return False, f"Error al desconectar USB: {err}"

        for _ in range(20):
            time.sleep(0.1)
            check = self._qmp_call(qmp_socket, "qom-list",
                                   {"path": f"/machine/peripheral/{usb_id}"})
            if not (check and "return" in check):
                return True, "USB desconectado."
        return True, "USB desconectado (confirmación asíncrona pendiente)."

    # --- HOTPLUG: DISCOS DUROS VIRTUALES ---
    
    def hotplug_disk(self, vm_id: str, disk_path: str, disk_format: str = None, 
                     bus_type: str = "virtio", disk_id: str = None, 
                     readonly: bool = False, discard: str = "unmap") -> tuple[bool, str]:
        """Conecta un disco virtual en caliente a la VM."""
        if not os.path.exists(disk_path):
            return False, "El archivo de disco no existe."
        
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."
        
        # Detectar formato por extensión si no se especifica
        if disk_format is None:
            ext = os.path.splitext(disk_path)[1].lower().lstrip(".")
            disk_format = {"img": "raw", "raw": "raw", "vdi": "vdi", "vmdk": "vmdk", 
                          "vhd": "vpc", "vhdx": "vhdx", "qcow2": "qcow2"}.get(ext, "qcow2")
        
        # Generar ID único para el disco
        if disk_id is None:
            import uuid
            disk_id = f"hotplug_disk_{uuid.uuid4().hex[:8]}"
        
        drive_id = f"drive_{disk_id}"
        
        # 1. Añadir el drive (blockdev-add)
        blockdev_args = {
            "driver": "file",
            "filename": disk_path,
            "node-name": f"file_{disk_id}",
            "auto-read-only": readonly,
            "aio": "threads"
        }
        
        resp = self._qmp_call(qmp_socket, "blockdev-add", blockdev_args)
        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            return False, f"Error al añadir archivo de disco: {err}"
        
        # 2. Añadir el controlador de formato (qcow2, raw, etc.)
        format_args = {
            "driver": disk_format,
            "node-name": f"fmt_{disk_id}",
            "file": f"file_{disk_id}"
        }
        
        if readonly:
            format_args["read-only"] = True
        if discard in ("unmap", "on"):
            format_args["discard"] = discard
        
        resp = self._qmp_call(qmp_socket, "blockdev-add", format_args)
        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            # Limpiar el archivo
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": f"file_{disk_id}"})
            return False, f"Error al añadir formato de disco: {err}"
        
        # 3. Conectar el dispositivo (device_add) según el bus
        device_id = f"device_{disk_id}"
        
        if bus_type == "virtio":
            device_args = {
                "driver": "virtio-blk-pci",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "bus": "pci.0"
            }
        elif bus_type == "virtio-scsi":
            device_args = {
                "driver": "scsi-hd",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "bus": "scsi0.0"
            }
        elif bus_type == "scsi":
            device_args = {
                "driver": "scsi-hd",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "bus": "scsi0.0"
            }
        elif bus_type == "sata" or bus_type == "ahci":
            device_args = {
                "driver": "ide-hd",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "bus": "ahci.0"
            }
        elif bus_type == "nvme":
            device_args = {
                "driver": "nvme",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "serial": disk_id[:20]
            }
        else:
            # Por defecto virtio-blk
            device_args = {
                "driver": "virtio-blk-pci",
                "drive": f"fmt_{disk_id}",
                "id": device_id,
                "bus": "pci.0"
            }
        
        if readonly:
            device_args["readonly"] = True
        
        resp = self._qmp_call(qmp_socket, "device_add", device_args)
        log.info(f"QMP device_add {device_id} -> {resp}")
        
        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            # Limpiar blockdevs
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": f"fmt_{disk_id}"})
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": f"file_{disk_id}"})
            return False, f"Error al conectar dispositivo de disco: {err}"
        
        # Verificar que se materializó
        time.sleep(0.5)
        check = self._qmp_call(qmp_socket, "qom-list",
                               {"path": f"/machine/peripheral/{device_id}"})
        if not (check and "return" in check):
            # Limpiar
            self._qmp_call(qmp_socket, "device_del", {"id": device_id})
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": f"fmt_{disk_id}"})
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": f"file_{disk_id}"})
            return False, "QEMU no materializó el disco (fallo silencioso)."
        
        log.info(f"Disco virtual {disk_path} conectado en caliente como {device_id}")
        return True, f"Disco conectado como {device_id}"

    def remove_disk(self, vm_id: str, device_id: str) -> tuple[bool, str]:
        """Desconecta un disco virtual en caliente."""
        qmp_socket = self._get_qmp_socket_path(vm_id)
        if not IS_WINDOWS and not os.path.exists(qmp_socket):
            return False, "La VM no está en ejecución."
        
        # 1. Desconectar el dispositivo
        resp = self._qmp_call(qmp_socket, "device_del", {"id": device_id})
        log.info(f"QMP device_del {device_id} -> {resp}")
        
        if not (resp and "return" in resp):
            err = (resp or {}).get("error", {}).get("desc", "Sin respuesta")
            if "not found" in err.lower() or "not exist" in err.lower():
                # El dispositivo ya no existe, limpiar blockdevs si existen
                pass
            else:
                return False, f"Error al desconectar disco: {err}"
        
        # Esperar a que se desmaterialice
        for _ in range(20):
            time.sleep(0.1)
            check = self._qmp_call(qmp_socket, "qom-list",
                                   {"path": f"/machine/peripheral/{device_id}"})
            if not (check and "return" in check):
                break
        
        # 2. Limpiar blockdevs (intentamos eliminar ambos posibles nombres)
        # Intentamos deducir los nombres de los blockdevs del device_id
        disk_id = device_id.replace("device_", "") if device_id.startswith("device_") else device_id
        
        for node_name in [f"fmt_{disk_id}", f"file_{disk_id}", f"drive_{disk_id}"]:
            self._qmp_call(qmp_socket, "blockdev-del", {"node-name": node_name})
        
        log.info(f"Disco virtual {device_id} desconectado en caliente")
        return True, "Disco desconectado."

    def force_detach_usb(self, bus: str, addr: str) -> tuple[bool, str]:
        if IS_WINDOWS:
            return False, "force_detach_usb no soportado en Windows."
        base = "/sys/bus/usb/devices"
        dev_name = None
        for d in os.listdir(base):
            if ":" in d:
                continue
            try:
                if (open(os.path.join(base, d, "busnum")).read().strip() == str(int(bus))
                        and open(os.path.join(base, d, "devnum")).read().strip() == str(int(addr))):
                    dev_name = d
                    break
            except Exception:
                continue

        if not dev_name:
            return False, "Dispositivo no encontrado en /sys/bus/usb."

        script = ""
        safe_name = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
        safe_driver = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
        for d in os.listdir(base):
            if not d.startswith(f"{dev_name}:") or not safe_name.fullmatch(d):
                continue
            link = os.path.join(base, d, "driver")
            if not os.path.exists(link):
                continue
            drv = os.path.basename(os.readlink(link))
            if not safe_driver.fullmatch(drv):
                log.warning("Driver USB con nombre inesperado: %r", drv)
                continue
            script += f"echo {d} > /sys/bus/usb/drivers/{drv}/unbind 2>/dev/null || true; "

        if not script:
            return True, "Ya sin drivers en las interfaces."

        try:
            subprocess.run(["pkexec", "sh", "-c", script],
                           check=True, capture_output=True, text=True, timeout=10)
            log.info(f"Interfaces del USB {dev_name} liberadas.")
            return True, "Interfaces liberadas."
        except subprocess.CalledProcessError as e:
            return False, f"pkexec falló: {(e.stderr or str(e)).strip()}"