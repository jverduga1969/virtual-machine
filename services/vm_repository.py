import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from services.json_store import atomic_write_json, quarantine, read_json

log = logging.getLogger(__name__)

# Campos de ejecución, no de configuración: no deben generar entradas en el
# historial cada vez que se enciende o se apaga una VM.
TRANSIENT_FIELDS = frozenset({
    "state", "qmp_socket", "vnc_port", "vnc_heads", "spice_port", "status",
})
MAX_HISTORY = 30

class VMRepository:
    """
    Gestiona la persistencia de las VMs en un archivo JSON.
    No sabe nada de PyQt ni de QEMU, solo lee y escribe datos.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.db_file = self.data_dir / "vms.json"
        self._vms: List[Dict] = []
        # Apagar/borrar VMs ocurre en hilos secundarios: proteger el JSON.
        self._lock = threading.RLock()
        self._ensure_storage()
        self.load()

    def _ensure_storage(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.db_file.exists():
            atomic_write_json(self.db_file, [])
        (self.data_dir / "history").mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------- historial
    @staticmethod
    def _configurable(vm: Dict) -> Dict:
        return {k: v for k, v in vm.items() if k not in TRANSIENT_FIELDS}

    def _history_file(self, vm_id: str) -> Path:
        seguro = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(vm_id))
        return self.data_dir / "history" / f"{seguro}.json"

    def _load_history(self, vm_id: str) -> List[Dict]:
        path = self._history_file(vm_id)
        datos = read_json(path, None)
        if not isinstance(datos, list):
            if path.exists():
                quarantine(path)
            return []
        return datos

    def _append_history(self, vm_id: str, vm: Dict, reason: str):
        historial = self._load_history(vm_id)
        historial.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "reason": reason,
            "vm": self._configurable(vm),
        })
        atomic_write_json(self._history_file(vm_id), historial[-MAX_HISTORY:])

    def get_history(self, vm_id: str) -> List[Dict]:
        """Versiones guardadas, de más reciente a más antigua."""
        with self._lock:
            return list(reversed(self._load_history(vm_id)))

    def restore(self, vm_id: str, index: int) -> bool:
        """Restaura la versión ``index`` de :meth:`get_history`.

        La configuración actual se guarda antes, así que la restauración
        también se puede deshacer.
        """
        with self._lock:
            # Mismo orden que get_history(): el índice 0 es la versión más reciente.
            historial = list(reversed(self._load_history(vm_id)))
            if index < 0 or index >= len(historial):
                return False
            entrada = historial[index]
            vm = next((v for v in self._vms if v.get("id") == vm_id), None)
            if vm is None:
                return False
            self._append_history(vm_id, vm, "Antes de restaurar")
            restaurada = dict(entrada.get("vm") or {})
            for campo in TRANSIENT_FIELDS:
                if campo in vm:
                    restaurada[campo] = vm[campo]
            vm.clear()
            vm.update(restaurada)
            self._append_history(vm_id, vm, f"Restaurada ({entrada.get('reason', 'versión')})")
            self.save()
            return True

    def load(self):
        raw = read_json(self.db_file, None)
        if raw is None or not isinstance(raw, list):
            dest = quarantine(self.db_file)
            log.error(
                "Base de datos de VMs corrupta%s; se arranca con la lista vacía.",
                f" (copia en {dest})" if dest else "",
            )
            self._vms = []
            return
        self._vms = raw
        log.info(f"Cargadas {len(self._vms)} VMs desde {self.db_file}")

    def save(self):
        with self._lock:
            atomic_write_json(self.db_file, self._vms)

    def get_all(self) -> List[Dict]:
        # Copia de la lista: los plugins no pueden reordenarla sin guardar.
        with self._lock:
            return list(self._vms)

    def get(self, vm_id: str) -> Optional[Dict]:
        with self._lock:
            return next((vm for vm in self._vms if vm.get("id") == vm_id), None)

    def add(self, vm_data: Dict):
        with self._lock:
            self._vms.append(vm_data)
            self._append_history(vm_data.get("id", "unknown"), vm_data, "VM creada")
            self.save()

    def update(self, vm_id: str, vm_data: Dict, reason: str = "Cambio de configuración"):
        with self._lock:
            for vm in self._vms:
                if vm.get("id") == vm_id:
                    anterior = self._configurable(vm)
                    vm.update(vm_data)
                    if anterior != self._configurable(vm):
                        self._append_history(vm_id, vm, reason)
                    self.save()
                    return True
        return False

    def delete(self, vm_id: str):
        with self._lock:
            eliminada = next((vm for vm in self._vms if vm.get("id") == vm_id), None)
            if eliminada is None:
                return False
            self._append_history(vm_id, eliminada, "VM eliminada")
            self._vms = [vm for vm in self._vms if vm.get("id") != vm_id]
            self.save()
            return True
