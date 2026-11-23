from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from typing import List, Dict, Optional
import logging
from pathlib import Path
import os
import shutil
import threading
import platform

from .i18n import tr as translate_text
from services.vm_repository import VMRepository
from services.host_adapter import HostAdapter, IS_WINDOWS, IS_MAC
from services.vm_runner import VMRunner
from services.qemu_paths import set_qemu_dir

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


def default_base_dir() -> Path:
    """Directorio de datos por defecto, compartido con Configuración Host."""
    if IS_WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VirtualMachine"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "VirtualMachine"
    return Path.home() / ".local" / "share" / "virtual-machine"


class AppContext(QObject):
    vm_selection_changed = pyqtSignal(str)
    vm_state_changed = pyqtSignal(str, str)
    log_message = pyqtSignal(str, str)
    process_started = pyqtSignal(str, object)
    # Se emite desde el hilo que apaga la VM; se entrega siempre en el hilo GUI.
    vm_stopped = pyqtSignal(str, bool)
    # QEMU puede terminar sin que nadie pulse Apagar (shutdown desde el
    # invitado, crash...). El monitor de VMRunner lo emite desde su hilo.
    vm_process_finished = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        # Instancia compartida: main.py ya fijó organization/application name,
        # así que todos los módulos leerán y escribirán el mismo archivo.
        self.settings = QSettings()
        settings = self.settings
        # Directorio de QEMU configurable (útil en Windows sin PATH).
        set_qemu_dir(settings.value("paths/qemu_dir", ""))
        default_dir = default_base_dir()
        self.data_dir = Path(settings.value("paths/base_dir", str(default_dir)))
        self.vms_dir = Path(settings.value("paths/vms_dir", str(self.data_dir / "vms")))
        self.isos_dir = Path(settings.value("paths/isos_dir", str(self.data_dir / "isos")))

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vms_dir.mkdir(parents=True, exist_ok=True)
        self.isos_dir.mkdir(parents=True, exist_ok=True)

        self.vm_repo = VMRepository(self.data_dir)
        self.host = HostAdapter()
        self.runner = VMRunner(
            self.host, self.data_dir, self.vms_dir,
            on_process_finished=self.vm_process_finished.emit)
        self.vm_process_finished.connect(self._on_qemu_process_finished)

        self._selected_vm_id: Optional[str] = None
        # Operaciones pendientes tras apagar una VM: reboot / force_reboot / delete
        self._pending_after_stop: Dict[str, str] = {}
        self._stopping: set[str] = set()
        self._stop_threads: set[threading.Thread] = set()
        self._state_lock = threading.Lock()
        self.vm_stopped.connect(self._on_stop_finished)

        self._log_handler = QtLogHandler(self.log_message)
        self._log_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(self._log_handler)
        logging.getLogger().setLevel(logging.INFO)
        log.info("AppContext iniciado")

    def tr(self, text: str) -> str: return translate_text(text)

    def get_vms(self) -> List[Dict]:
        vms = self.vm_repo.get_all()
        changed = False
        for vm in vms:
            if vm.get("state") in ("Running", "Apagando...") and vm["id"] not in self.runner.active_processes:
                vm["state"] = "Apagada"
                self.vm_repo.update(vm["id"], {"state": "Apagada"})
                changed = True
        if changed: self.vm_repo.save()
        return vms

    def get_vm(self, vm_id: str) -> Optional[Dict]: return self.vm_repo.get(vm_id)

    def start_vm(self, vm_id: str):
        vm = self.get_vm(vm_id)
        if not vm: return
        if vm.get("state") == "Paused" and vm_id in self.runner.active_processes:
            return self.resume_vm(vm_id)
        # Estado "Paused" sin proceso = estado huérfano tras un reinicio de la
        # app; se arranca de cero en vez de intentar reanudar un QEMU muerto.
        if vm.get("state") == "Paused":
            self.vm_repo.update(vm_id, {"state": "Apagada"})
        if vm.get("state") == "Running" and vm_id in self.runner.active_processes: return
        # Si el estado dice "Apagando..." pero no hay proceso real, es un estado huérfano: corregir
        if vm.get("state") == "Apagando...":
            if vm_id in self.runner.active_processes:
                return
            self.vm_repo.update(vm_id, {"state": "Apagada"})

        log.info(f"==> Iniciando VM: {vm.get('name')}")
        try:
            process = self.runner.start_vm(vm)
            self.vm_repo.update(vm_id, {"state": "Running"})
            self.vm_state_changed.emit(vm_id, "Running")
            self.process_started.emit(vm_id, process)
            self._notify_desktop(vm.get("name", "VM"), "está encendida y lista.")
        except Exception as e:
            log.error(f"Error al arrancar VM: {e}")
            self.vm_state_changed.emit(vm_id, "Error")

    def can_reopen_window(self, vm_id: str) -> bool:
        """La opción solo tiene sentido con una VM encendida y visor externo."""
        vm = self.get_vm(vm_id)
        return bool(vm and vm.get("state") in ("Running", "Paused")
                    and self.runner.has_external_viewer(vm_id))

    def reopen_vm_window(self, vm_id: str) -> bool:
        """Reabre la ventana SPICE/VNC que el usuario cerró por error."""
        if not self.can_reopen_window(vm_id):
            log.warning("No se puede reabrir la ventana: %s no está encendida o no usa visor externo.", vm_id)
            return False
        ok = self.runner.reopen_viewer(vm_id)
        if ok:
            log.info("Ventana de %s reabierta.", (self.get_vm(vm_id) or {}).get("name", vm_id))
        return ok

    def change_iso(self, vm_id: str, iso_path: str):
        if self.runner.change_iso(vm_id, iso_path):
            log.info(f"ISO cambiada con éxito en {vm_id}.")
            self.vm_repo.update(vm_id, {"iso_path": iso_path})
        else:
            log.error(f"Fallo al cambiar la ISO de {vm_id}.")

    def stop_vm(self, vm_id: str, follow_up: str = None):
        """Apaga la VM en segundo plano.

        ``follow_up`` permite encadenar ``reboot``/``force_reboot``/``delete``
        sin ``sleep`` ni carreras con el hilo de apagado.
        """
        if follow_up:
            with self._state_lock:
                self._pending_after_stop[vm_id] = follow_up
        vm = self.get_vm(vm_id)
        if not vm:
            return
        with self._state_lock:
            if vm_id in self._stopping:
                return
            self._stopping.add(vm_id)

        self.vm_repo.update(vm_id, {"state": "Apagando..."})
        self.vm_state_changed.emit(vm_id, "Apagando...")

        def _do_stop():
            ok = False
            try:
                self.runner.stop_vm(vm_id)
                ok = True
            except Exception as e:
                log.error(f"Error deteniendo VM {vm_id}: {e}")
                try:
                    self.runner.force_stop_vm(vm_id)
                    ok = True
                except Exception as e2:
                    log.error(f"Error en force_stop de {vm_id}: {e2}")
            finally:
                # No mentir sobre el estado: si fallaron ambas vías, es Error.
                state = "Apagada" if ok else "Error"
                self.vm_repo.update(vm_id, {"state": state})
                self.vm_state_changed.emit(vm_id, state)
                with self._state_lock:
                    self._stopping.discard(vm_id)
                    self._stop_threads.discard(threading.current_thread())
                self.vm_stopped.emit(vm_id, ok)

        thread = threading.Thread(target=_do_stop, daemon=True, name=f"stop-{vm_id}")
        with self._state_lock:
            self._stop_threads.add(thread)
        thread.start()

    def _on_stop_finished(self, vm_id: str, ok: bool):
        """Se ejecuta en el hilo GUI: continúa la acción que estaba pendiente."""
        with self._state_lock:
            action = self._pending_after_stop.pop(vm_id, None)
        if not action:
            return
        if not ok:
            log.error(f"No se puede '{action}' {vm_id}: el apagado falló")
            return
        if action in ("reboot", "force_reboot"):
            self.start_vm(vm_id)
        elif action == "delete":
            self._delete_vm_files(vm_id)

    def _delete_vm_files(self, vm_id: str):
        with self._state_lock:
            self._pending_after_stop.pop(vm_id, None)
        self.vm_repo.delete(vm_id)
        vm_dir = (self.vms_dir / str(vm_id)).resolve()
        vms_root = self.vms_dir.resolve()
        if vm_dir != vms_root and vms_root in vm_dir.parents and vm_dir.exists():
            try:
                shutil.rmtree(vm_dir)
            except OSError as e:
                log.error(f"No se pudo borrar el directorio de {vm_id}: {e}")
        self.vm_state_changed.emit(vm_id, "Deleted")

    def pause_vm(self, vm_id: str) -> bool:
        vm = self.get_vm(vm_id)
        if not vm:
            return False
        if vm.get("state") != "Running":
            log.warning("No se puede pausar %s: estado actual '%s'",
                        vm_id, vm.get("state"))
            return False
        if vm_id not in self.runner.active_processes:
            self._mark_stopped(vm_id)
            return False
        try:
            ok = bool(self.runner.pause_vm(vm_id))
        except Exception as e:
            log.error(f"Error pausando VM {vm_id}: {e}")
            ok = False
        if not ok:
            log.error(f"QEMU rechazó la pausa de {vm_id}; se mantiene el estado.")
            return False
        self.vm_repo.update(vm_id, {"state": "Paused"})
        self.vm_state_changed.emit(vm_id, "Paused")
        return True

    def resume_vm(self, vm_id: str) -> bool:
        vm = self.get_vm(vm_id)
        if not vm:
            return False
        if vm.get("state") != "Paused":
            log.warning("No se puede reanudar %s: estado actual '%s'",
                        vm_id, vm.get("state"))
            return False
        if vm_id not in self.runner.active_processes:
            self._mark_stopped(vm_id)
            return False
        try:
            ok = bool(self.runner.resume_vm(vm_id))
        except Exception as e:
            log.error(f"Error reanudando VM {vm_id}: {e}")
            ok = False
        if not ok:
            log.error(f"QEMU rechazó la reanudación de {vm_id}; se mantiene el estado.")
            return False
        self.vm_repo.update(vm_id, {"state": "Running"})
        self.vm_state_changed.emit(vm_id, "Running")
        return True

    def _mark_stopped(self, vm_id: str):
        """Estado canónico cuando sabemos que QEMU ya no está vivo."""
        self.vm_repo.update(vm_id, {"state": "Apagada"})
        self.vm_state_changed.emit(vm_id, "Apagada")

    def _on_qemu_process_finished(self, vm_id: str, code: int):
        """Slot GUI: QEMU salió por su cuenta (apagado del invitado o crash)."""
        with self._state_lock:
            if vm_id in self._stopping:
                return  # el hilo de stop_vm ya actualizará el estado
        vm = self.get_vm(vm_id)
        if not vm or vm_id in self.runner.active_processes:
            return
        if vm.get("state") not in ("Running", "Paused", "Apagando..."):
            return
        log.info(f"QEMU de {vm_id} terminó (código {code}); VM marcada como Apagada.")
        self._mark_stopped(vm_id)

    def force_stop_vm(self, vm_id: str):
        if not self.get_vm(vm_id):
            return
        with self._state_lock:
            self._pending_after_stop.pop(vm_id, None)  # cancelar reinicio/borrado previo
            if vm_id in self._stopping:
                return  # ya hay un apagado en curso; que termine él
            self._stopping.add(vm_id)
        try:
            self.runner.force_stop_vm(vm_id)
            state = "Apagada"
        except Exception as e:
            log.error(f"Error en force_stop de {vm_id}: {e}")
            state = "Error"
        finally:
            with self._state_lock:
                self._stopping.discard(vm_id)
        self.vm_repo.update(vm_id, {"state": state})
        self.vm_state_changed.emit(vm_id, state)

    def reboot_vm(self, vm_id: str, force: bool = False):
        if not self.get_vm(vm_id):
            return
        self.stop_vm(vm_id, follow_up="force_reboot" if force else "reboot")

    def force_reboot_vm(self, vm_id: str):
        self.reboot_vm(vm_id, force=True)

    def delete_vm(self, vm_id: str) -> bool:
        """Elimina la VM solo cuando QEMU ya no está usando sus archivos."""
        if not self.get_vm(vm_id):
            return False
        with self._state_lock:
            self._pending_after_stop[vm_id] = "delete"
            already_stopping = vm_id in self._stopping
        if already_stopping:
            return True
        if vm_id in self.runner.active_processes:
            self.stop_vm(vm_id)
            return True
        self._delete_vm_files(vm_id)
        return True

    def log(self, level: str, message: str):
        log.info(f"[{level}] {message}")
        self.log_message.emit(level, message)

    def _notify_desktop(self, vm_name: str, body: str):
        """Envía una notificación de escritorio usando notify-send (Linux) o
        la API de Windows. Falla silenciosamente si no está disponible."""
        try:
            if IS_WINDOWS:
                # Windows: usar PowerShell toast si está disponible.
                # El texto viaja por variables de entorno: interpolalo en el
                # -Command permitiría inyectar código con un nombre de VM que
                # contenga una comilla simple.
                import subprocess as _sp
                env = os.environ.copy()
                env["VM_NOTIFY_TITLE"] = "Virtual Machine"
                env["VM_NOTIFY_TEXT"] = f"{vm_name} {body}"
                script = (
                    "[void][Windows.UI.Notifications.ToastNotificationManager, "
                    "Windows.UI.Notifications, ContentType=WindowsRuntime]; "
                    "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0); "
                    "$t.GetElementsByTagName('text')[0].AppendChild("
                    "$t.CreateTextNode($env:VM_NOTIFY_TITLE)); "
                    "$t.GetElementsByTagName('text')[1].AppendChild("
                    "$t.CreateTextNode($env:VM_NOTIFY_TEXT)); "
                    "[Windows.UI.Notifications.ToastNotificationManager]"
                    "::CreateToastNotifier('VirtualMachineApp').Show($t)"
                )
                _sp.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden",
                     "-Command", script],
                    env=env, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
                )
            else:
                import shutil as _sh, subprocess as _sp
                if _sh.which("notify-send"):
                    _sp.Popen(
                        ["notify-send",
                         "--icon=computer",
                         "--app-name=Virtual Machine",
                         f"🖥️ {vm_name}",
                         body],
                        stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
                    )
        except Exception:
            pass  # La notificación es opcional; nunca debe romper el flujo