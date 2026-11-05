import os
import shutil
import logging

log = logging.getLogger(__name__)

class HostAdapter:
    """
    Abstracción del sistema operativo subyacente.
    Detecta dependencias y prepara el entorno.
    """
    def __init__(self):
        self.qemu_path = self._find_binary("qemu-system-x86_64")
        self.qemu_img_path = self._find_binary("qemu-img")
        self.kvm_available = self._check_kvm()

    def _find_binary(self, name: str) -> str | None:
        path = shutil.which(name)
        if not path:
            log.warning(f"Dependencia no encontrada en el sistema: {name}")
        return path

    def _check_kvm(self) -> bool:
        has_kvm = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
        if not has_kvm:
            log.warning("KVM no disponible. La aceleración por hardware está desactivada.")
        return has_kvm

    def get_status(self) -> dict:
        return {
            "qemu": bool(self.qemu_path),
            "qemu_img": bool(self.qemu_img_path),
            "kvm": self.kvm_available
        }
