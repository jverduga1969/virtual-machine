from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from typing import List, Dict, Optional
import logging
from pathlib import Path
import time
import os
import threading

from services.vm_repository import VMRepository
from services.host_adapter import HostAdapter
from services.vm_runner import VMRunner

log = logging.getLogger(__name__)

class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level in ("warning", "warn"): level = "warn"
            elif level in ("error", "critical"): level = "error"
            else: level = "info"
            self.signal.emit(level, msg)
        except Exception: pass

class AppContext(QObject):
    vm_selection_changed = pyqtSignal(str)
    vm_state_changed = pyqtSignal(str, str)
    log_message = pyqtSignal(str, str)
    process_started = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        settings = QSettings()
        default_dir = Path.home() / ".local" / "share" / "virtual-machine"
        self.data_dir = Path(settings.value("paths/base_dir", str(default_dir)))
        self.vms_dir = Path(settings.value("paths/vms_dir", str(self.data_dir / "vms")))
        self.isos_dir = Path(settings.value("paths/isos_dir", str(self.data_dir / "isos")))
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vms_dir.mkdir(parents=True, exist_ok=True)
        self.isos_dir.mkdir(parents=True, exist_ok=True)
        
        self.vm_repo = VMRepository(self.data_dir)
        self.host = HostAdapter()
        self.runner = VMRunner(self.host, self.data_dir)
        
        self._selected_vm_id: Optional[str] = None
        self._log_handler = QtLogHandler(self.log_message)
        self._log_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(self._log_handler)
        logging.getLogger().setLevel(logging.INFO)
        log.info("AppContext iniciado")

    def tr(self, text: str) -> str: return text

    def get_vms(self) -> List[Dict]:
        vms = self.vm_repo.get_all()
        changed = False
        for vm in vms:
            if vm.get("state") == "Running" and vm["id"] not in self.runner.active_processes:
                vm["state"] = "Apagada"
                self.vm_repo.update(vm["id"], {"state": "Apagada"})
                changed = True
        if changed: self.vm_repo.save()
        return vms

    def get_vm(self, vm_id: str) -> Optional[Dict]: return self.vm_repo.get(vm_id)

    def start_vm(self, vm_id: str):
        vm = self.get_vm(vm_id)
        if not vm: return
        if vm.get("state") == "Paused": return self.resume_vm(vm_id)
        if vm.get("state") in ("Running", "Apagando..."): return

        log.info(f"==> Iniciando VM: {vm.get('name')}")
        try:
            process = self.runner.start_vm(vm)
            self.vm_repo.update(vm_id, {"state": "Running"})
            self.vm_state_changed.emit(vm_id, "Running")
            self.process_started.emit(vm_id, process)
        except Exception as e:
            log.error(f"Error al arrancar VM: {e}")
            self.vm_state_changed.emit(vm_id, "Error")

    def change_iso(self, vm_id: str, iso_path: str):
        if self.runner.change_iso(vm_id, iso_path):
            log.info(f"ISO cambiada con éxito en {vm_id}.")
            self.vm_repo.update(vm_id, {"iso_path": iso_path})
        else:
            log.error(f"Fallo al cambiar la ISO de {vm_id}.")

    def stop_vm(self, vm_id: str):
        if not self.get_vm(vm_id): return
        self.vm_repo.update(vm_id, {"state": "Apagando..."})
        self.vm_state_changed.emit(vm_id, "Apagando...")
        def _do_stop():
            self.runner.stop_vm(vm_id)
            self.vm_repo.update(vm_id, {"state": "Apagada"})
            self.vm_state_changed.emit(vm_id, "Apagada")
        threading.Thread(target=_do_stop, daemon=True).start()

    def pause_vm(self, vm_id: str):
        self.runner.pause_vm(vm_id)
        self.vm_repo.update(vm_id, {"state": "Paused"})
        self.vm_state_changed.emit(vm_id, "Paused")

    def resume_vm(self, vm_id: str):
        self.runner.resume_vm(vm_id)
        self.vm_repo.update(vm_id, {"state": "Running"})
        self.vm_state_changed.emit(vm_id, "Running")

    def force_stop_vm(self, vm_id: str):
        self.runner.force_stop_vm(vm_id)
        self.vm_repo.update(vm_id, {"state": "Apagada"})
        self.vm_state_changed.emit(vm_id, "Apagada")

    def reboot_vm(self, vm_id: str):
        self.stop_vm(vm_id)
        time.sleep(1)
        self.start_vm(vm_id)

    def delete_vm(self, vm_id: str):
        if vm_id in self.runner.active_processes: self.stop_vm(vm_id)
        self.vm_repo.delete(vm_id)
        self.vm_state_changed.emit(vm_id, "Deleted")

    def log(self, level: str, message: str):
        log.info(f"[{level}] {message}")
        self.log_message.emit(level, message)