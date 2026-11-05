import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

log = logging.getLogger(__name__)

class VMRepository:
    """
    Gestiona la persistencia de las VMs en un archivo JSON.
    No sabe nada de PyQt ni de QEMU, solo lee y escribe datos.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.db_file = self.data_dir / "vms.json"
        self._vms: List[Dict] = []
        self._ensure_storage()
        self.load()

    def _ensure_storage(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.db_file.exists():
            self.db_file.write_text("[]", encoding="utf-8")

    def load(self):
        try:
            content = self.db_file.read_text(encoding="utf-8")
            self._vms = json.loads(content)
            log.info(f"Cargadas {len(self._vms)} VMs desde {self.db_file}")
        except Exception as e:
            log.error(f"Error cargando base de datos de VMs: {e}")
            self._vms = []

    def save(self):
        try:
            self.db_file.write_text(json.dumps(self._vms, indent=4), encoding="utf-8")
        except Exception as e:
            log.error(f"Error guardando base de datos de VMs: {e}")

    def get_all(self) -> List[Dict]:
        return self._vms

    def get(self, vm_id: str) -> Optional[Dict]:
        return next((vm for vm in self._vms if vm.get("id") == vm_id), None)

    def add(self, vm_data: Dict):
        self._vms.append(vm_data)
        self.save()

    def update(self, vm_id: str, vm_data: Dict):
        for i, vm in enumerate(self._vms):
            if vm.get("id") == vm_id:
                self._vms[i].update(vm_data)
                self.save()
                break

    def delete(self, vm_id: str):
        self._vms = [vm for vm in self._vms if vm.get("id") != vm_id]
        self.save()
