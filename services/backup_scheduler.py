"""Programación de snapshots y backups de VMs.

La lógica es independiente de Qt: solo necesita un objeto ``settings`` con
``value()``/``setValue()`` (el QSettings compartido por AppContext). El timer
que dispara las comprobaciones vive en el plugin de Snapshots.
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from services.json_store import atomic_write_json, read_json

log = logging.getLogger(__name__)

FREQ_LABELS = ("Diario", "Semanal", "Mensual")
FREQ_DAYS = {"Diario": 1, "Semanal": 7, "Mensual": 30}
SNAPSHOT_PREFIX = "auto_"


def snapshot_tag(moment: datetime) -> str:
    """Nombre válido para qemu-img/QMP y ordenable por fecha."""
    return f"{SNAPSHOT_PREFIX}{moment.strftime('%Y%m%d_%H%M%S')}"


class BackupScheduler:
    def __init__(self, settings, data_dir, snapshot_manager=None):
        self.settings = settings
        self.data_dir = Path(data_dir)
        self.snap_mgr = snapshot_manager
        self.check_interval_ms = 60_000

    # ------------------------------------------------------------------ config
    @staticmethod
    def _key(vm_id, name):
        return f"schedules/{vm_id}/{name}"

    def get_schedule(self, vm_id):
        """Devuelve la programación guardada, con valores por defecto."""
        get = self.settings.value
        return {
            "enabled": str(get(self._key(vm_id, "enabled"), "false")).lower() == "true",
            "freq": get(self._key(vm_id, "freq"), "Semanal") or "Semanal",
            "keep": int(get(self._key(vm_id, "keep"), 5) or 5),
            "backup": str(get(self._key(vm_id, "backup"), "false")).lower() == "true",
            "last_run": get(self._key(vm_id, "last_run"), "") or "",
        }

    def set_schedule(self, vm_id, enabled, freq, keep, backup=False):
        if freq not in FREQ_LABELS:
            freq = "Semanal"
        send = self.settings.setValue
        send(self._key(vm_id, "enabled"), "true" if enabled else "false")
        send(self._key(vm_id, "freq"), freq)
        send(self._key(vm_id, "keep"), max(1, min(50, int(keep))))
        send(self._key(vm_id, "backup"), "true" if backup else "false")

    def get_backup_dir(self):
        return str(self.settings.value(
            "backups/dir", str(self.data_dir / "backups")) or self.data_dir / "backups")

    def set_backup_dir(self, path):
        self.settings.setValue("backups/dir", str(path))

    def mark_run(self, vm_id, moment):
        self.settings.setValue(
            self._key(vm_id, "last_run"), moment.isoformat(timespec="seconds"))

    # ------------------------------------------------------------------ fechas
    @staticmethod
    def parse_last_run(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

    def is_due(self, vm_id, now=None):
        now = now or datetime.now()
        sched = self.get_schedule(vm_id)
        if not sched["enabled"]:
            return False
        last = self.parse_last_run(sched["last_run"])
        if last is None:
            return True
        return now - last >= timedelta(days=FREQ_DAYS.get(sched["freq"], 7))

    # ------------------------------------------------------------------ backups
    def backup_path(self, vm_id, moment):
        return Path(self.get_backup_dir()) / vm_id / moment.strftime("%Y%m%d_%H%M%S")

    def create_backup(self, vm, moment=None, repo=None):
        """Copia la configuración y, si la VM está apagada, su disco."""
        moment = moment or datetime.now()
        dest = self.backup_path(vm.get("id", "unknown"), moment)
        dest.mkdir(parents=True, exist_ok=True)

        atomic_write_json(dest / "vm.json", vm)
        resultado = {"path": str(dest), "config": True, "disk": False, "note": ""}

        disk = vm.get("disk_path")
        if not disk or not Path(disk).is_file():
            resultado["note"] = "Sin disco configurado; solo se guardó la configuración."
        elif vm.get("state") in ("Running", "Paused", "Apagando..."):
            resultado["note"] = "VM encendida: se hizo snapshot, pero no se copió el disco."
        else:
            try:
                shutil.copy2(disk, dest / Path(disk).name)
                resultado["disk"] = True
            except OSError as exc:
                resultado["note"] = f"No se pudo copiar el disco: {exc}"

        if repo is not None and not resultado["disk"]:
            # El backup sigue siendo útil: al menos permite recuperar la config.
            log.warning("Backup sin disco de %s: %s", vm.get("name"), resultado["note"])
        return resultado

    def list_backups(self, vm_id):
        base = Path(self.get_backup_dir()) / vm_id
        if not base.is_dir():
            return []
        return sorted((p for p in base.iterdir() if p.is_dir()),
                      key=lambda p: p.name, reverse=True)

    def prune(self, vm_id, keep):
        """Conserva solo los ``keep`` backups más recientes."""
        borrados = []
        for viejo in self.list_backups(vm_id)[max(1, int(keep)):]:
            try:
                shutil.rmtree(viejo)
                borrados.append(viejo.name)
            except OSError as exc:
                log.warning("No se pudo borrar backup %s: %s", viejo, exc)
        return borrados

    # ------------------------------------------------------------------ getting
    def prune_snapshots(self, vm, keep):
        if not self.snap_mgr:
            return []
        try:
            snaps = self.snap_mgr.list_snapshots(vm)
        except Exception as exc:
            log.warning("No se pudieron listar snapshots: %s", exc)
            return []
        auto = sorted((s for s in snaps if s.get("name", "").startswith(SNAPSHOT_PREFIX)),
                      key=lambda s: s["name"], reverse=True)
        borrados = []
        for viejo in auto[max(1, int(keep)):]:
            ok, _msg = self.snap_mgr.delete_snapshot(vm, viejo["name"])
            if ok:
                borrados.append(viejo["name"])
        return borrados

    def run(self, vm, moment=None, repo=None):
        """Ejecuta snapshot (+ backup opcional) para una VM y aplica retención."""
        moment = moment or datetime.now()
        sched = self.get_schedule(vm.get("id", "unknown"))
        tag = snapshot_tag(moment)
        resultado = {"vm": vm.get("name", vm.get("id", "VM")),
                     "snapshot": False, "backup": None,
                     "pruned_snapshots": [], "pruned_backups": [], "errors": []}

        if self.snap_mgr:
            try:
                ok, msg = self.snap_mgr.create_snapshot(
                    vm, tag, "Snapshot automático programado")
                resultado["snapshot"] = ok
                if not ok:
                    resultado["errors"].append(msg)
            except Exception as exc:
                resultado["errors"].append(f"Snapshot: {exc}")
        else:
            resultado["errors"].append("Sin gestor de snapshots disponible.")

        if sched["backup"]:
            try:
                resultado["backup"] = self.create_backup(vm, moment, repo)
            except Exception as exc:
                resultado["errors"].append(f"Backup: {exc}")

        resultado["pruned_snapshots"] = self.prune_snapshots(vm, sched["keep"])
        if sched["backup"]:
            resultado["pruned_backups"] = self.prune(vm.get("id", "unknown"), sched["keep"])

        self.mark_run(vm.get("id", "unknown"), moment)
        return resultado

    def run_due(self, vms, now=None):
        now = now or datetime.now()
        resultados = []
        for vm in vms or []:
            if self.is_due(vm.get("id", "unknown"), now):
                resultados.append(self.run(vm, now))
        return resultados
