import os
import sys
import re
import shutil
import subprocess
import logging
import platform
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"


# WHV_CAPABILITY_CODE_WHV_CAPABILITY_CODE_HYPERVISOR_PRESENT
_WHV_CAPABILITY_HYPERVISOR_PRESENT = 0


def windows_whpx_available() -> bool:
    """Consulta a Windows si la plataforma de hipervisor (WHPX) está activa.

    `qemu -accel whpx -machine none` no sirve como prueba: en QEMU x86 moderno
    `none` no es una máquina x86 y el proceso termina con un assert antes de
    llegar a inicializar WHPX. La API WinHV es la misma que usa QEMU por dentro.
    """
    if not IS_WINDOWS:
        return False
    try:
        import ctypes

        api = ctypes.WinDLL("WinHVPlatform.dll")
        get_capability = api.WHvGetCapability
        get_capability.argtypes = [
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        get_capability.restype = ctypes.c_int32
        buffer = ctypes.create_string_buffer(16)
        written = ctypes.c_uint32()
        hr = get_capability(
            _WHV_CAPABILITY_HYPERVISOR_PRESENT,
            buffer,
            len(buffer),
            ctypes.byref(written),
        )
        if hr < 0 or written.value < 4:
            return False
        return bool(int.from_bytes(buffer.raw[:4], "little"))
    except Exception as exc:
        log.info("No se pudo consultar WHPX con WinHVPlatform.dll: %s", exc)
        return False


def qemu_accepts_accel(qemu_path: str | None, accel: str, timeout: float = 3.0) -> bool:
    """Pregunta al propio QEMU si acepta un acelerador.

    Se usa `-machine pc`: `none` provoca un assert en QEMU x86 antes de
    inicializar el acelerador. Si el proceso sigue vivo pasado el timeout sin
    avisos de «not available», el acelerador arrancó correctamente.
    """
    if not qemu_path:
        return False

    def _rechazado(salida: str) -> bool:
        return bool(re.search(
            rf"{accel}.*(not available|not supported|no disponible|"
            rf"failed|error)", salida, re.IGNORECASE,
        ))

    cmd = [
        qemu_path, "-accel", accel, "-machine", "pc",
        "-display", "none", "-monitor", "none", "-serial", "none",
    ]
    try:
        resultado = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        salida = f"{resultado.stdout or ''}\n{resultado.stderr or ''}"
        if resultado.returncode != 0:
            log.info("QEMU no acepta %s: %s", accel, salida.strip()[:300])
            return False
        if _rechazado(salida):
            log.info("QEMU avisa de que %s no está disponible", accel)
            return False
        return True
    except subprocess.TimeoutExpired as exc:
        salida = ""
        for parte in (exc.stdout, exc.stderr):
            if isinstance(parte, bytes):
                salida += parte.decode("utf-8", "replace")
            elif parte:
                salida += parte
        if _rechazado(salida):
            log.info("QEMU avisa de que %s no está disponible", accel)
            return False
        return True
    except Exception as exc:
        log.warning("No se pudo comprobar %s con QEMU: %s", accel, exc)
        return False


def qemu_supports_tpm(qemu_path: str | None, timeout: float = 3.0) -> bool:
    """Comprueba si el QEMU instalado ofrece el backend de TPM 'emulator'.

    En Windows el runner usa `-tpmdev emulator` directamente; en Linux usa
    swtpm + el mismo backend. Preguntar al propio QEMU evita dar por bueno
    un TPM que luego falla al arrancar la VM.
    """
    if not qemu_path:
        return False
    try:
        resultado = subprocess.run(
            [qemu_path, "-tpmdev", "help"],
            capture_output=True, text=True, timeout=timeout,
        )
        salida = f"{resultado.stdout or ''}\n{resultado.stderr or ''}".lower()
        return "emulator" in salida
    except Exception as exc:
        log.info("No se pudo sondear el soporte de TPM en QEMU: %s", exc)
        return False


class HostAdapter:
    """
    Abstracción del sistema operativo subyacente.
    Detecta dependencias y prepara el entorno.
    Soporta Linux (KVM), Windows (WHPX/HAX) y macOS Intel (HVF).
    """
    def __init__(self):
        self.qemu_path = self._find_binary("qemu-system-x86_64")
        self.qemu_img_path = self._find_binary("qemu-img")
        self.acceleration = self._detect_acceleration()
        self.is_windows = IS_WINDOWS
        self.is_mac = IS_MAC

    def _find_binary(self, name: str) -> Optional[str]:
        """Busca un binario en PATH y en rutas comunes de Windows."""
        from services.qemu_paths import find_qemu_binary

        path = find_qemu_binary(name)
        if not path:
            log.warning(f"Dependencia no encontrada en el sistema: {name}")
        return path

    def _detect_acceleration(self) -> str:
        """Detecta el acelerador disponible según el SO."""
        if IS_WINDOWS:
            # En Windows probar WHPX primero, luego HAXM, finalmente TCG
            if self._check_whpx():
                return "whpx"
            if self._check_haxm():
                return "hax"
            log.warning("Ningún acelerador de hardware detectado en Windows. Usando TCG (emulación pura, lenta).")
            return "tcg"
        if IS_MAC:
            # macOS: Hypervisor.framework. HAXM esta descatalogado; HVF es el
            # equivalente a WHPX/KVM y lo trae el QEMU de Homebrew firmado.
            if self._qemu_accepts_accel("hvf"):
                return "hvf"
            log.warning("HVF no disponible. Usando TCG (emulación pura, lenta).")
            return "tcg"
        # Linux: KVM
        if self._check_kvm():
            return "kvm"
        log.warning("KVM no disponible. Usando TCG (emulación pura, lenta).")
        return "tcg"

    def _check_kvm(self) -> bool:
        """Comprueba si KVM está disponible (solo Linux)."""
        if IS_WINDOWS:
            return False
        return os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)

    def _qemu_accepts_accel(self, accel: str) -> bool:
        """Sondeo de QEMU; `windows_whpx_available()` es la vía preferida."""
        return qemu_accepts_accel(self.qemu_path, accel)

    def _check_whpx(self) -> bool:
        """Comprueba si WHPX está disponible en Windows."""
        if not IS_WINDOWS:
            return False
        if windows_whpx_available():
            return True
        # La API puede faltar en instalaciones antiguas: probar también QEMU.
        return self._qemu_accepts_accel("whpx")

    def _check_haxm(self) -> bool:
        """Comprueba si Intel HAXM está instalado (Windows)."""
        if not IS_WINDOWS:
            return False
        # HAXM se instala como servicio o driver
        haxm_paths = [
            r"C:\Program Files\intel\haxm",
            r"C:\Program Files (x86)\intel\haxm",
        ]
        for p in haxm_paths:
            if os.path.exists(p):
                return True
        return False

    def get_accel_args(self) -> list:
        """Devuelve los argumentos de aceleración para QEMU."""
        if self.acceleration == "kvm":
            return ["-accel", "kvm"]
        elif self.acceleration == "whpx":
            return ["-accel", "whpx"]
        elif self.acceleration == "hax":
            return ["-accel", "hax"]
        elif self.acceleration == "hvf":
            return ["-accel", "hvf"]
        else:
            return ["-accel", "tcg"]

    def get_status(self) -> dict:
        return {
            "qemu": bool(self.qemu_path),
            "qemu_img": bool(self.qemu_img_path),
            "acceleration": self.acceleration,
            "is_windows": self.is_windows,
            "is_mac": self.is_mac,
        }
