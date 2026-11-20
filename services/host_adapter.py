import os
import sys
import shutil
import logging
import platform
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


class HostAdapter:
    """
    Abstracción del sistema operativo subyacente.
    Detecta dependencias y prepara el entorno.
    Soporta Linux y Windows.
    """
    def __init__(self):
        self.qemu_path = self._find_binary("qemu-system-x86_64")
        self.qemu_img_path = self._find_binary("qemu-img")
        self.acceleration = self._detect_acceleration()
        self.is_windows = IS_WINDOWS

    def _find_binary(self, name: str) -> Optional[str]:
        """Busca un binario en PATH y en rutas comunes de Windows."""
        # En Windows, QEMU puede venir con .exe
        candidates = [name]
        if IS_WINDOWS:
            if not name.lower().endswith(".exe"):
                candidates.append(name + ".exe")
            # Rutas comunes de instalación de QEMU en Windows
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            qemu_common_dirs = [
                Path(program_files) / "qemu",
                Path(program_files) / "QEMU",
                Path(program_files) / "qemu-64-bit",
                Path(os.environ.get("LOCALAPPDATA", "")) / "qemu",
            ]
            for d in qemu_common_dirs:
                for cand in candidates:
                    p = d / cand
                    if p.exists():
                        return str(p)

        path = shutil.which(name)
        if not path:
            for cand in candidates:
                p = shutil.which(cand)
                if p:
                    path = p
                    break
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
        else:
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

    def _check_whpx(self) -> bool:
        """Comprueba si WHPX está disponible (Windows)."""
        if not IS_WINDOWS:
            return False
        # WHPX se detecta intentando arrancar qemu con -accel whpx o comprobando
        # la presencia del controlador. Aquí hacemos una comprobación ligera.
        try:
            import subprocess
            result = subprocess.run(
                ["sc", "query", "WHvSvc"],
                capture_output=True, text=True, timeout=3
            )
            return "RUNNING" in result.stdout.upper()
        except Exception:
            return False

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
        else:
            return ["-accel", "tcg"]

    def get_status(self) -> dict:
        return {
            "qemu": bool(self.qemu_path),
            "qemu_img": bool(self.qemu_img_path),
            "acceleration": self.acceleration,
            "is_windows": self.is_windows,
        }
