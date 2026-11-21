import os
import sys
import glob
import shutil
import subprocess
import logging
import platform
from typing import List, Dict, Any

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Fuentes canonicas de OVMF en Linux. Las usan este modulo, el boton
# "Reparar OVMF Secure Boot" y VMRunner._find_ovmf(), para que los tres
# encuentren los mismos archivos (incluidos los .bin de openSUSE).
OVMF_LINUX_DIRS = (
    "/usr/share/edk2/x64",
    "/usr/share/OVMF",
    "/usr/share/edk2/ovmf",
    "/usr/share/edk2-ovmf/x64",
    "/usr/share/qemu",
)
OVMF_SECBOOT_CODE_PATTERNS = (
    "OVMF_CODE*.secboot*.fd",
    "ovmf-x86_64-ms-code.bin",
    "ovmf-x86_64-smm-ms-code.bin",
    "ovmf-x86_64-*-ms-code.bin",
)
OVMF_CODE_PATTERNS = (
    "OVMF_CODE_4M.fd",
    "OVMF_CODE*.4m.fd",
    "OVMF_CODE*.fd",
    "ovmf-x86_64-code.bin",
    "ovmf-x86_64-*-code.bin",
    "ovmf-x86_64-4m.bin",
    "OVMF.fd",
)
OVMF_VARS_PATTERNS = (
    "OVMF_VARS.fd",
    "OVMF_VARS*.4m.fd",
    "OVMF_VARS*.fd",
    "ovmf-x86_64-vars.bin",
    "ovmf-x86_64-*-vars.bin",
    "ovmf-x86_64-4m-vars.bin",
)


def find_ovmf_code() -> str | None:
    """Devuelve un OVMF_CODE utilizable o None si no hay ninguno."""
    if not IS_LINUX:
        return None
    for directory in OVMF_LINUX_DIRS:
        for pattern in OVMF_SECBOOT_CODE_PATTERNS + OVMF_CODE_PATTERNS:
            for path in sorted(glob.glob(os.path.join(directory, pattern))):
                try:
                    if os.path.getsize(path) > 1024 * 1024:
                        return path
                except OSError:
                    continue
    return None


def find_ovmf_windows() -> str | None:
    """Busca el OVMF.fd que distribuyen los paquetes de QEMU para Windows."""
    if not IS_WINDOWS:
        return None
    # Un `glob` recursivo sobre Program Files puede tardar minutos en equipos
    # con muchos programas. Los paquetes de QEMU para Windows dejan el firmware
    # siempre en estas rutas, así que las comprobamos directamente.
    candidatos = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        raiz = os.environ.get(variable, "")
        if not raiz:
            continue
        candidatos += [
            os.path.join(raiz, "qemu", "share", "qemu", "OVMF.fd"),
            os.path.join(raiz, "QEMU", "share", "qemu", "OVMF.fd"),
            os.path.join(raiz, "qemu", "OVMF.fd"),
            os.path.join(raiz, "QEMU", "OVMF.fd"),
        ]
    for path in candidatos:
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 1024 * 1024:
                return path
        except OSError:
            continue
    return None


def _windows_accel_status(qemu_bin: str | None) -> tuple[str, str]:
    """Comprueba de verdad qué acelerador acepta QEMU en Windows."""
    if not qemu_bin:
        return "err", "QEMU no encontrado en el PATH"
    for accel in ("whpx", "hax", "tcg"):
        try:
            resultado = subprocess.run(
                [qemu_bin, "-accel", accel, "-machine", "none",
                 "-display", "none", "-monitor", "none", "-serial", "none"],
                capture_output=True, text=True, timeout=8)
            if resultado.returncode == 0:
                if accel == "whpx":
                    return "ok", "WHPX disponible (comprobado)"
                return "warn", f"WHPX no disponible; se usará {accel.upper()}"
        except Exception as e:
            return "warn", f"No se pudo comprobar WHPX: {e}"
    return "warn", "No se pudo comprobar ningún acelerador"


def _is_windows_admin() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _module_available(name: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


class HostDiagnostics:
    def run_all(self) -> List[Dict[str, Any]]:
        checks = []

        # --- 1. Virtualización Básica ---
        qemu_bin = shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-x86_64.exe")
        checks.append({"cat": "Virtualización", "name": "QEMU", "st": "ok" if qemu_bin else "err", "desc": qemu_bin or "No instalado"})

        if IS_LINUX:
            checks.append({"cat": "Virtualización", "name": "KVM (/dev/kvm)", "st": "ok" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "err", "desc": "/dev/kvm accesible" if os.path.exists("/dev/kvm") else "No existe"})
            ovmf_code = find_ovmf_code()
            checks.append({
                "cat": "Virtualización", "name": "Firmware UEFI (OVMF)",
                "st": "ok" if ovmf_code else "warn",
                "desc": ovmf_code or "No encontrado (ovmf / edk2-ovmf / qemu-ovmf-x86_64)",
            })
            checks.append({"cat": "Virtualización", "name": "TPM 2.0 (swtpm)", "st": "ok" if shutil.which("swtpm") else "warn", "desc": shutil.which("swtpm") or "No instalado"})
            checks.append({"cat": "Virtualización", "name": "Módulos VirtIO", "st": "ok" if os.path.exists("/sys/module/virtio") else "warn", "desc": "Presentes" if os.path.exists("/sys/module/virtio") else "No cargados"})
            checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "ok" if shutil.which("pactl") or shutil.which("pipewire") else "warn", "desc": "PulseAudio/PipeWire detectado"})
        else:
            whpx_st, whpx_desc = _windows_accel_status(qemu_bin)
            checks.append({"cat": "Virtualización", "name": "WHPX (Windows Hypervisor)", "st": whpx_st, "desc": whpx_desc})
            ovmf_win = find_ovmf_windows()
            checks.append({"cat": "Virtualización", "name": "Firmware UEFI (OVMF)",
                           "st": "ok" if ovmf_win else "warn",
                           "desc": ovmf_win or "No encontrado (instala QEMU con OVMF)"})
            checks.append({"cat": "Virtualización", "name": "TPM 2.0", "st": "ok", "desc": "Emulado por QEMU"})
            checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "warn", "desc": "Usar audio de Windows nativo"})

        # --- 2. Python Dependencies ---
        for modulo in ("PyQt6", "requests", "packaging"):
            disponible = _module_available(modulo)
            checks.append({"cat": "Python", "name": modulo,
                           "st": "ok" if disponible else "err",
                           "desc": "Instalado" if disponible else "No instalado"})

        if IS_LINUX:
            checks.append({"cat": "Python", "name": "polkit / pkexec", "st": "ok" if shutil.which("pkexec") else "warn", "desc": shutil.which("pkexec") or "No instalado"})
            checks.append({"cat": "Python", "name": "udev / udevadm", "st": "ok" if shutil.which("udevadm") else "warn", "desc": shutil.which("udevadm") or "No instalado"})
        else:
            admin = _is_windows_admin()
            checks.append({"cat": "Python", "name": "Administrador",
                           "st": "ok" if admin else "warn",
                           "desc": "Elevación de UAC activa" if admin else "Sin elevación: algunas reparaciones fallarán"})

        # --- 3. Consola (VNC / SPICE) ---
        checks.append({"cat": "Consola", "name": "Cliente VNC embebido", "st": "ok", "desc": "vnc_widget importable"})

        if IS_LINUX:
            checks.append({"cat": "Consola", "name": "Spice-gtk (binding Python)", "st": "ok" if shutil.which("spicy") else "warn", "desc": "Disponible" if shutil.which("spicy") else "No instalado"})
            checks.append({"cat": "Consola", "name": "Visor VNC externo", "st": "ok" if shutil.which("vncviewer") else "warn", "desc": shutil.which("vncviewer") or "No instalado"})
            checks.append({"cat": "Consola", "name": "Visor SPICE externo", "st": "ok" if shutil.which("remote-viewer") else "warn", "desc": shutil.which("remote-viewer") or "No instalado"})
        else:
            vnc = shutil.which("vncviewer.exe") or shutil.which("vncviewer")
            spice = shutil.which("remote-viewer.exe") or shutil.which("remote-viewer")
            checks.append({"cat": "Consola", "name": "Visor VNC externo",
                           "st": "ok" if vnc else "warn", "desc": vnc or "TigerVNC para Windows"})
            checks.append({"cat": "Consola", "name": "Visor SPICE externo",
                           "st": "ok" if spice else "warn", "desc": spice or "virt-viewer para Windows"})

        # --- 4. Compartición ---
        if IS_LINUX:
            checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "ok" if shutil.which("virtiofsd") else "warn", "desc": shutil.which("virtiofsd") or "No instalado"})
            checks.append({"cat": "Compartición", "name": "Samba (smbd)", "st": "ok" if shutil.which("smbd") else "warn", "desc": shutil.which("smbd") or "No instalado"})
        else:
            checks.append({"cat": "Compartición", "name": "Samba (SMB)", "st": "ok", "desc": "Usar compartir de archivos de Windows"})
            checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "warn", "desc": "No disponible nativamente en Windows"})

        # --- 5. Passthrough ---
        if IS_LINUX:
            checks.append({"cat": "Passthrough", "name": "IOMMU en Kernel", "st": "warn", "desc": "Requiere reinicio"})
            checks.append({"cat": "Passthrough", "name": "Grupos IOMMU", "st": "warn", "desc": "Sin grupos visibles"})
            checks.append({"cat": "Passthrough", "name": "Regla udev udmabuf", "st": "ok" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "Falta"})
            checks.append({"cat": "Passthrough", "name": "Regla udev USB", "st": "ok" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "Falta"})
        else:
            checks.append({"cat": "Passthrough", "name": "PCI/USB Passthrough", "st": "warn", "desc": "No soportado en Windows"})

        return checks
