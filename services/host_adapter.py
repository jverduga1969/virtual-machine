import os
import sys
import re
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

    def _qemu_accepts_accel(self, accel: str) -> bool:
        """Pregunta al propio QEMU si acepta un acelerador.

        `sc query WHvSvc` no sirve: WHPX es una característica opcional de
        Windows, no un servicio con ese nombre. La única comprobación fiable es
        arrancar QEMU con `-accel <accel> -machine none` y mirar el resultado.
        """
        if not self.qemu_path:
            return False
        try:
            import subprocess
            resultado = subprocess.run(
                [self.qemu_path, "-accel", accel, "-machine", "none",
                 "-display", "none", "-monitor", "none", "-serial", "none"],
                capture_output=True, text=True, timeout=10,
            )
            salida = f"{resultado.stdout or ''}\n{resultado.stderr or ''}"
            if resultado.returncode != 0:
                log.info("QEMU no acepta %s: %s", accel, salida.strip()[:300])
                return False
            # Algunas versiones devuelven 0 pero avisan de que el acelerador
            # no está disponible; no damos el acelerador por bueno en ese caso.
            if re.search(
                rf"{accel}.*(not available|not supported|no disponible|"
                rf"failed|error)", salida, re.IGNORECASE,
            ):
                log.info("QEMU avisa de que %s no está disponible", accel)
                return False
            return True
        except Exception as e:
            log.warning("No se pudo comprobar %s con QEMU: %s", accel, e)
            return False

    def _check_whpx(self) -> bool:
        """Comprueba de verdad si QEMU acepta WHPX en Windows."""
        if not IS_WINDOWS:
            return False
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
        else:
            return ["-accel", "tcg"]

    def get_status(self) -> dict:
        return {
            "qemu": bool(self.qemu_path),
            "qemu_img": bool(self.qemu_img_path),
            "acceleration": self.acceleration,
            "is_windows": self.is_windows,
        }
