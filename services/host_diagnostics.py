import os
import sys
import glob
import shutil
import subprocess
import logging
import platform
from pathlib import Path
from typing import List, Dict, Any

from .qemu_paths import find_qemu_binary
from .host_adapter import qemu_supports_tpm

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

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

# Homebrew/MacPorts dejan el firmware junto a los binarios de QEMU. En Intel,
# `brew install qemu` instala en /usr/local/share/qemu.
OVMF_MACOS_DIRS = (
    "/usr/local/share/qemu",
    "/opt/homebrew/share/qemu",
    "/opt/local/share/qemu",
)
OVMF_MACOS_SECBOOT_PATTERNS = (
    "edk2-x86_64-secure-code.fd",
    "OVMF_CODE*.secboot*.fd",
)
OVMF_MACOS_CODE_PATTERNS = (
    "edk2-x86_64-code.fd",
    "OVMF_CODE*.fd",
    "OVMF.fd",
)
OVMF_MACOS_VARS_PATTERNS = (
    "edk2-i386-vars.fd",
    "edk2-x86_64-vars.fd",
    "OVMF_VARS*.fd",
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

# La UI añade aquí el data_dir de la app, para que diagnóstico, reparación y
# VMRunner busquen exactamente en los mismos sitios.
OVMF_EXTRA_DIRS: tuple[str, ...] = ()


def _ovmf_dirs() -> tuple[str, ...]:
    dirs = list(OVMF_LINUX_DIRS) + list(OVMF_EXTRA_DIRS)
    if IS_MAC:
        dirs.extend(OVMF_MACOS_DIRS)
    proyecto = Path(__file__).resolve().parents[1] / "OSX-KVM"
    dirs.append(str(proyecto))
    return tuple(dict.fromkeys(dirs))


def _find_ovmf(patterns, min_bytes: int = 1024 * 1024) -> str | None:
    for directory in _ovmf_dirs():
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.join(directory, pattern))):
                try:
                    if os.path.getsize(path) > min_bytes:
                        return path
                except OSError:
                    continue
    return None


def find_ovmf_code() -> str | None:
    """Devuelve un OVMF_CODE utilizable o None si no hay ninguno."""
    if not IS_LINUX and not IS_MAC:
        return None
    patrones = (OVMF_MACOS_SECBOOT_PATTERNS + OVMF_MACOS_CODE_PATTERNS
                if IS_MAC else OVMF_SECBOOT_CODE_PATTERNS + OVMF_CODE_PATTERNS)
    return _find_ovmf(patrones)


def find_ovmf_vars() -> str | None:
    """Devuelve un OVMF_VARS utilizable o None si no hay ninguno."""
    if not IS_LINUX and not IS_MAC:
        return None
    # Los VARS son mucho más pequeños que el CODE: 10 KB basta para descartar
    # ficheros vacíos sin rechazar los que distribuyen las distros.
    patrones = OVMF_MACOS_VARS_PATTERNS if IS_MAC else OVMF_VARS_PATTERNS
    return _find_ovmf(patrones, min_bytes=10 * 1024)


def find_ovmf_secboot_code() -> str | None:
    """Solo el CODE con Secure Boot, que es lo que exige Windows 11."""
    if not IS_LINUX and not IS_MAC:
        return None
    patrones = OVMF_MACOS_SECBOOT_PATTERNS if IS_MAC else OVMF_SECBOOT_CODE_PATTERNS
    return _find_ovmf(patrones)


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


def find_ovmf_vars_windows(code_path: str | None) -> str | None:
    """Busca el VARS junto al CODE de Windows devuelto por find_ovmf_windows()."""
    if not IS_WINDOWS or not code_path:
        return None
    directorio = os.path.dirname(code_path)
    nombres = (
        "OVMF_VARS.fd", "OVMF_VARS_4M.fd", "OVMF_VARS.4m.fd",
        "ovmf-x86_64-vars.bin", os.path.basename(code_path).replace("CODE", "VARS"),
    )
    for nombre in dict.fromkeys(nombres):
        candidato = os.path.join(directorio, nombre)
        try:
            if os.path.isfile(candidato) and os.path.getsize(candidato) > 10 * 1024:
                return candidato
        except OSError:
            continue
    return None


def _windows_accel_status(qemu_bin: str | None) -> tuple[str, str]:
    """Comprueba de verdad qué acelerador hay disponible en Windows."""
    from services.host_adapter import qemu_accepts_accel, windows_whpx_available

    # `-machine none` no sirve para sondear WHPX en QEMU x86: termina con un
    # assert antes de inicializar el acelerador. Preguntar a WinHV es fiable.
    if windows_whpx_available():
        return "ok", "WHPX disponible (comprobado)"
    if not qemu_bin:
        return "err", "QEMU no encontrado en el PATH"
    if qemu_accepts_accel(qemu_bin, "hax"):
        return "warn", "WHPX no disponible; se usará HAX"
    return "warn", "WHPX no disponible; se usará TCG (emulación lenta)"


def _macos_accel_status(qemu_bin: str | None) -> tuple[str, str]:
    """Comprueba de verdad si QEMU en macOS puede usar Hypervisor.framework."""
    from services.host_adapter import qemu_accepts_accel

    if not qemu_bin:
        return "err", "QEMU no encontrado (instala con `brew install qemu`)"
    if qemu_accepts_accel(qemu_bin, "hvf"):
        return "ok", "HVF disponible (Hypervisor.framework, comprobado)"
    return "warn", "HVF no disponible; se usará TCG (emulación lenta)"


def check_fido() -> tuple[str, str]:
    """Verifica la copia canónica de Fido sin descargar nada de la red."""
    from services.iso_sources import _resolve_fido_path

    ruta = _resolve_fido_path("Fido.ps1", download=False)
    if not ruta or not os.path.isfile(ruta):
        return "err", "No encontrado"
    try:
        texto = Path(ruta).read_text(encoding="utf-8-sig")
    except OSError:
        return "err", "No legible"
    if "Fido v1.71" not in texto:
        return "warn", "Versión antigua (se espera v1.71)"
    if "# --- patched-for-linux ---" not in texto:
        return "warn", "Falta el parche multiplataforma"
    return "ok", ruta


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
        # Usar el mismo resolvedor que el runner: si el usuario configuró
        # paths/qemu_dir sin PATH, el diagnóstico no debe dar un falso negativo.
        qemu_bin = find_qemu_binary("qemu-system-x86_64")
        checks.append({"cat": "Virtualización", "name": "QEMU", "st": "ok" if qemu_bin else "err", "desc": qemu_bin or "No instalado"})

        qemu_img = find_qemu_binary("qemu-img")
        checks.append({"cat": "Virtualización", "name": "qemu-img", "st": "ok" if qemu_img else "err", "desc": qemu_img or "No instalado"})

        if IS_LINUX:
            checks.append({"cat": "Virtualización", "name": "KVM (/dev/kvm)", "st": "ok" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "err", "desc": "/dev/kvm accesible" if os.path.exists("/dev/kvm") else "No existe"})
            ovmf_code = find_ovmf_code()
            checks.append({
                "cat": "Virtualización", "name": "Firmware UEFI (OVMF)",
                "st": "ok" if ovmf_code else "warn",
                "desc": ovmf_code or "No encontrado (ovmf / edk2-ovmf / qemu-ovmf-x86_64)",
            })
            ovmf_vars = find_ovmf_vars()
            checks.append({
                "cat": "Virtualización", "name": "OVMF VARS",
                "st": "ok" if ovmf_vars else "warn",
                "desc": ovmf_vars or "No encontrado",
            })
            ovmf_secboot = find_ovmf_secboot_code()
            checks.append({
                "cat": "Virtualización", "name": "OVMF Secure Boot",
                "st": "ok" if ovmf_secboot else "warn",
                "desc": ovmf_secboot or "No encontrado",
            })
            swtpm = shutil.which("swtpm")
            if swtpm and qemu_supports_tpm(qemu_bin):
                tpm_st, tpm_desc = "ok", swtpm
            elif swtpm:
                tpm_st, tpm_desc = "warn", "QEMU sin backend emulator"
            else:
                tpm_st, tpm_desc = "warn", "No instalado"
            checks.append({"cat": "Virtualización", "name": "TPM 2.0 (swtpm)",
                           "st": tpm_st, "desc": tpm_desc})
            checks.append({"cat": "Virtualización", "name": "Módulos VirtIO", "st": "ok" if os.path.exists("/sys/module/virtio") else "warn", "desc": "Presentes" if os.path.exists("/sys/module/virtio") else "No cargados"})
            checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "ok" if shutil.which("pactl") or shutil.which("pipewire") else "warn", "desc": "PulseAudio/PipeWire detectado"})
        elif IS_MAC:
            hvf_st, hvf_desc = _macos_accel_status(qemu_bin)
            checks.append({"cat": "Virtualización", "name": "HVF (Hypervisor.framework)", "st": hvf_st, "desc": hvf_desc})
            ovmf_code = find_ovmf_code()
            checks.append({
                "cat": "Virtualización", "name": "Firmware UEFI (OVMF)",
                "st": "ok" if ovmf_code else "warn",
                "desc": ovmf_code or "No encontrado (brew install qemu instala OVMF en /usr/local/share/qemu)",
            })
            ovmf_vars = find_ovmf_vars()
            checks.append({
                "cat": "Virtualización", "name": "OVMF VARS",
                "st": "ok" if ovmf_vars else "warn",
                "desc": ovmf_vars or "No encontrado",
            })
            # En macOS el runner usa `-tpmdev emulator` dentro de QEMU, igual
            # que en Windows. Preguntamos a QEMU si ofrece ese backend.
            if qemu_supports_tpm(qemu_bin):
                tpm_st, tpm_desc = "ok", "Emulado por QEMU (verificado)"
            else:
                tpm_st, tpm_desc = "warn", "QEMU sin soporte de TPM verificado"
            checks.append({"cat": "Virtualización", "name": "TPM 2.0", "st": tpm_st, "desc": tpm_desc})
            checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "ok", "desc": "CoreAudio (nativo de macOS)"})
        else:
            whpx_st, whpx_desc = _windows_accel_status(qemu_bin)
            checks.append({"cat": "Virtualización", "name": "WHPX (Windows Hypervisor)", "st": whpx_st, "desc": whpx_desc})
            ovmf_win = find_ovmf_windows()
            checks.append({"cat": "Virtualización", "name": "Firmware UEFI (OVMF)",
                           "st": "ok" if ovmf_win else "warn",
                           "desc": ovmf_win or "No encontrado (instala QEMU con OVMF)"})
            ovmf_win_vars = find_ovmf_vars_windows(ovmf_win)
            checks.append({"cat": "Virtualización", "name": "OVMF VARS",
                           "st": "ok" if ovmf_win_vars else "warn",
                           "desc": ovmf_win_vars or "No encontrado"})
            # En Windows el runner usa `-tpmdev emulator` dentro de QEMU.
            # Preguntamos a QEMU si ofrece ese backend antes de marcarlo ok.
            if qemu_supports_tpm(qemu_bin):
                tpm_st, tpm_desc = "ok", "Emulado por QEMU (verificado)"
            else:
                tpm_st, tpm_desc = "warn", "QEMU sin soporte de TPM verificado"
            checks.append({"cat": "Virtualización", "name": "TPM 2.0", "st": tpm_st, "desc": tpm_desc})
            checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "warn", "desc": "Usar audio de Windows nativo"})

        fido_st, fido_desc = check_fido()
        checks.append({"cat": "Virtualización", "name": "Fido (ISOs Windows)",
                       "st": fido_st, "desc": fido_desc})
        if IS_MAC:
            # Fido.ps1 se ejecuta con PowerShell 7 en macOS/Linux.
            checks.append({"cat": "Python", "name": "PowerShell 7 (pwsh)",
                           "st": "ok" if shutil.which("pwsh") else "warn",
                           "desc": shutil.which("pwsh") or
                                   "Necesario para Fido: brew install --cask powershell"})

        if IS_LINUX:
            faltan = [h for h in ("lsof", "notify-send", "xdg-open", "git", "tar")
                      if not shutil.which(h)]
            checks.append({"cat": "Python", "name": "Utilidades de apoyo",
                           "st": "ok" if not faltan else "warn",
                           "desc": "Disponibles" if not faltan else "Faltan: " + ", ".join(faltan)})

        # --- 2. Python Dependencies ---
        for modulo in ("PyQt6", "requests", "packaging"):
            disponible = _module_available(modulo)
            checks.append({"cat": "Python", "name": modulo,
                           "st": "ok" if disponible else "err",
                           "desc": "Instalado" if disponible else "No instalado"})

        if IS_LINUX:
            checks.append({"cat": "Python", "name": "polkit / pkexec", "st": "ok" if shutil.which("pkexec") else "warn", "desc": shutil.which("pkexec") or "No instalado"})
            checks.append({"cat": "Python", "name": "udev / udevadm", "st": "ok" if shutil.which("udevadm") else "warn", "desc": shutil.which("udevadm") or "No instalado"})
        elif IS_MAC:
            # HVF no requiere elevación ni permisos especiales: el QEMU de
            # Homebrew ya trae el entitlement para Hypervisor.framework.
            checks.append({"cat": "Python", "name": "Homebrew",
                           "st": "ok" if shutil.which("brew") else "warn",
                           "desc": shutil.which("brew") or "No encontrado (brew.sh)"})
        else:
            admin = _is_windows_admin()
            checks.append({"cat": "Python", "name": "Administrador",
                           "st": "ok" if admin else "warn",
                           "desc": "Elevación de UAC activa" if admin else "Sin elevación: algunas reparaciones fallarán"})

        # --- 3. Consola (VNC / SPICE) ---
        vnc_embed = _module_available("vnc_widget")
        checks.append({"cat": "Consola", "name": "Cliente VNC embebido",
                       "st": "ok" if vnc_embed else "err",
                       "desc": "vnc_widget importable" if vnc_embed else "No instalado"})

        if IS_LINUX:
            checks.append({"cat": "Consola", "name": "Spice-gtk (binding Python)", "st": "ok" if shutil.which("spicy") else "warn", "desc": "Disponible" if shutil.which("spicy") else "No instalado"})
            checks.append({"cat": "Consola", "name": "Visor VNC externo", "st": "ok" if shutil.which("vncviewer") else "warn", "desc": shutil.which("vncviewer") or "No instalado"})
            checks.append({"cat": "Consola", "name": "Visor SPICE externo", "st": "ok" if shutil.which("remote-viewer") else "warn", "desc": shutil.which("remote-viewer") or "No instalado"})
        elif IS_MAC:
            checks.append({"cat": "Consola", "name": "Visor VNC externo",
                           "st": "ok" if shutil.which("vncviewer") else "warn",
                           "desc": shutil.which("vncviewer") or "Opcional: se usa el cliente VNC embebido"})
            checks.append({"cat": "Consola", "name": "Visor SPICE externo",
                           "st": "warn", "desc": "SPICE en macOS sin portapapeles: usar VNC embebido"})
        else:
            vnc = find_qemu_binary("vncviewer")
            spice = find_qemu_binary("remote-viewer")
            checks.append({"cat": "Consola", "name": "Visor VNC externo",
                           "st": "ok" if vnc else "warn", "desc": vnc or "TigerVNC para Windows"})
            checks.append({"cat": "Consola", "name": "Visor SPICE externo",
                           "st": "ok" if spice else "warn", "desc": spice or "virt-viewer para Windows"})

        # --- 4. Compartición ---
        if IS_LINUX:
            checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "ok" if shutil.which("virtiofsd") else "warn", "desc": shutil.which("virtiofsd") or "No instalado"})
            checks.append({"cat": "Compartición", "name": "Samba (smbd)", "st": "ok" if shutil.which("smbd") else "warn", "desc": shutil.which("smbd") or "No instalado"})
        elif IS_MAC:
            checks.append({"cat": "Compartición", "name": "Samba (smbd)",
                           "st": "ok" if shutil.which("smbd") else "warn",
                           "desc": shutil.which("smbd") or "SMB requiere smbd (macOS lo trae; activar en Compartir archivo)"})
            checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "warn", "desc": "No disponible nativamente en macOS"})
        else:
            checks.append({"cat": "Compartición", "name": "Samba (SMB)", "st": "warn", "desc": "SMB requiere smbd en el host; no disponible en Windows"})
            checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "warn", "desc": "No disponible nativamente en Windows"})

        # --- 5. Passthrough ---
        if IS_LINUX:
            # Antes eran dos textos fijos. Ahora se lee /proc/cmdline y
            # /sys/kernel/iommu_groups con la misma función que usa la UI.
            from services import host_passthrough
            iommu = host_passthrough.check_iommu()
            grupos = iommu["groups"]
            if iommu["enabled"]:
                iommu_st, iommu_desc = "ok", "Activo"
            elif iommu["needs_reboot"]:
                iommu_st, iommu_desc = "warn", "Requiere reinicio"
            else:
                iommu_st, iommu_desc = "warn", "No activado en /proc/cmdline"
            checks.append({"cat": "Passthrough", "name": "IOMMU en Kernel", "st": iommu_st, "desc": iommu_desc})
            checks.append({"cat": "Passthrough", "name": "Grupos IOMMU",
                           "st": "ok" if grupos else "warn",
                           "desc": "Con grupos visibles" if grupos else "Sin grupos visibles"})
            checks.append({"cat": "Passthrough", "name": "Regla udev udmabuf", "st": "ok" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "Falta"})
            checks.append({"cat": "Passthrough", "name": "Regla udev USB", "st": "ok" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "Falta"})
        elif IS_MAC:
            checks.append({"cat": "Passthrough", "name": "PCI/USB Passthrough",
                           "st": "warn", "desc": "No soportado en macOS (HVF no expone IOMMU al invitado)"})
        else:
            checks.append({"cat": "Passthrough", "name": "PCI/USB Passthrough", "st": "warn", "desc": "No soportado en Windows"})
            # QEMU usb-host usa libusb en Windows: sin WinUSB/libusbK el
            # device_add falla aunque el dispositivo aparezca en el sistema.
            checks.append({"cat": "Passthrough", "name": "Driver USB (WinUSB/libusbK)",
                           "st": "warn", "desc": "Instalar con Zadig para usb-host"})

        return checks
