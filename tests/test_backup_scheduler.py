"""Snapshots y backups programados: lógica aislada de Qt."""

from datetime import datetime, timedelta

from services.backup_scheduler import BackupScheduler, snapshot_tag


class FakeSettings:
    def __init__(self):
        self.datos = {}

    def value(self, key, default=""):
        return self.datos.get(key, default)

    def setValue(self, key, value):
        self.datos[key] = value


class FakeSnapMgr:
    def __init__(self, nombres=()):
        self.nombres = list(nombres)
        self.creados = []
        self.borrados = []

    def create_snapshot(self, vm, name, desc=""):
        self.creados.append(name)
        self.nombres.append(name)
        return True, "ok"

    def list_snapshots(self, vm):
        return [{"name": n} for n in self.nombres]

    def delete_snapshot(self, vm, name):
        self.borrados.append(name)
        if name in self.nombres:
            self.nombres.remove(name)
        return True, "ok"


def _scheduler(tmp_path, settings=None, snaps=None):
    settings = settings or FakeSettings()
    snaps = snaps or FakeSnapMgr()
    return BackupScheduler(settings, tmp_path, snaps), settings, snaps


def test_snapshot_tag_es_ordenable():
    a = snapshot_tag(datetime(2026, 1, 2, 3, 4, 5))
    b = snapshot_tag(datetime(2026, 11, 20, 10, 0, 0))
    assert a == "auto_20260102_030405"
    assert a < b


def test_programacion_se_guarda_y_se_recupera(tmp_path):
    scheduler, settings, _ = _scheduler(tmp_path)

    assert scheduler.get_schedule("vm1") == {
        "enabled": False, "freq": "Semanal", "keep": 5,
        "backup": False, "last_run": "",
    }

    scheduler.set_schedule("vm1", True, "Diario", 12, backup=True)
    assert scheduler.get_schedule("vm1")["enabled"] is True
    assert scheduler.get_schedule("vm1")["freq"] == "Diario"
    assert scheduler.get_schedule("vm1")["keep"] == 12
    assert scheduler.get_schedule("vm1")["backup"] is True

    # Los valores se guardan en las claves que usará la UI.
    assert settings.value("schedules/vm1/enabled") == "true"
    assert scheduler.get_schedule("otra")["enabled"] is False


def test_is_due_respeta_activacion_y_frecuencia(tmp_path):
    scheduler, _, _ = _scheduler(tmp_path)
    ahora = datetime(2026, 11, 20, 12, 0, 0)

    assert scheduler.is_due("vm1", ahora) is False  # desactivada
    scheduler.set_schedule("vm1", True, "Semanal", 5)
    assert scheduler.is_due("vm1", ahora) is True   # nunca ejecutada

    scheduler.mark_run("vm1", ahora - timedelta(days=3))
    assert scheduler.is_due("vm1", ahora) is False  # 3 < 7 días

    scheduler.mark_run("vm1", ahora - timedelta(days=8))
    assert scheduler.is_due("vm1", ahora) is True

    scheduler.set_schedule("vm1", True, "Diario", 5)
    scheduler.mark_run("vm1", ahora - timedelta(days=2))
    assert scheduler.is_due("vm1", ahora) is True


def test_backup_copia_config_y_disco_con_vm_apagada(tmp_path):
    scheduler, _, _ = _scheduler(tmp_path)
    disco = tmp_path / "disco.qcow2"
    disco.write_bytes(b"qemu image")
    vm = {"id": "vm1", "name": "Prueba", "state": "Apagada", "disk_path": str(disco)}
    momento = datetime(2026, 11, 20, 10, 30, 0)

    resultado = scheduler.create_backup(vm, momento)

    assert resultado["disk"] is True
    destino = tmp_path / "backups" / "vm1" / "20261120_103000"
    assert (destino / "vm.json").exists()
    assert (destino / "disco.qcow2").read_bytes() == b"qemu image"


def test_backup_con_vm_encendida_solo_guarda_config(tmp_path):
    scheduler, _, _ = _scheduler(tmp_path)
    disco = tmp_path / "disco.qcow2"
    disco.write_bytes(b"qemu image")
    vm = {"id": "vm1", "name": "Prueba", "state": "Running", "disk_path": str(disco)}

    resultado = scheduler.create_backup(vm, datetime(2026, 11, 20, 10, 30, 0))

    assert resultado["disk"] is False
    assert "VM encendida" in resultado["note"]
    assert not (tmp_path / "backups" / "vm1" / "20261120_103000" / "disco.qcow2").exists()


def test_prune_deja_solo_los_backups_mas_recientes(tmp_path):
    scheduler, _, _ = _scheduler(tmp_path)
    base = tmp_path / "backups" / "vm1"
    for dia in (1, 2, 3, 4, 5):
        (base / f"2026110{dia}_100000").mkdir(parents=True)

    borrados = scheduler.prune("vm1", 2)

    assert sorted(borrados) == ["20261101_100000", "20261102_100000",
                                "20261103_100000"]
    assert len(scheduler.list_backups("vm1")) == 2
    assert scheduler.list_backups("vm1")[0].name == "20261105_100000"


def test_run_crea_snapshot_backup_y_aplica_retencion(tmp_path):
    snaps = FakeSnapMgr(["auto_20260101_000000", "auto_20260102_000000",
                         "auto_20260103_000000", "manual"])
    scheduler, settings, snaps = _scheduler(tmp_path, snaps=snaps)
    disco = tmp_path / "disco.qcow2"
    disco.write_bytes(b"img")
    vm = {"id": "vm1", "name": "Prueba", "state": "Apagada", "disk_path": str(disco)}
    scheduler.set_schedule("vm1", True, "Diario", 2, backup=True)
    momento = datetime(2026, 11, 20, 10, 0, 0)

    resultado = scheduler.run(vm, momento)

    assert resultado["snapshot"] is True
    assert snaps.creados == ["auto_20261120_100000"]
    assert "auto_" in " ".join(snaps.borrados)
    assert "manual" not in snaps.borrados
    assert resultado["backup"]["disk"] is True
    assert len(scheduler.list_backups("vm1")) == 1
    assert scheduler.parse_last_run(settings.value("schedules/vm1/last_run")) == momento
    assert scheduler.is_due("vm1", momento + timedelta(hours=1)) is False


def test_run_due_solo_ejecuta_las_vms_programadas(tmp_path):
    scheduler, _, snaps = _scheduler(tmp_path)
    vm1 = {"id": "vm1", "name": "Uno", "state": "Apagada", "disk_path": ""}
    vm2 = {"id": "vm2", "name": "Dos", "state": "Apagada", "disk_path": ""}
    scheduler.set_schedule("vm1", True, "Diario", 3)

    resultados = scheduler.run_due([vm1, vm2], datetime(2026, 11, 20, 10, 0, 0))

    assert len(resultados) == 1
    assert resultados[0]["vm"] == "Uno"
    assert snaps.creados == ["auto_20261120_100000"]


def test_run_registra_errores_sin_lanzar_excepciones(tmp_path):
    class SnapQueFalla:
        def create_snapshot(self, vm, name, desc=""):
            return False, "qemu-img no encontrado"

        def list_snapshots(self, vm):
            return []

        def delete_snapshot(self, vm, name):
            return False, "no"

    scheduler, _, _ = _scheduler(tmp_path, snaps=SnapQueFalla())
    resultado = scheduler.run({"id": "vm1", "name": "Uno", "state": "Apagada"})

    assert resultado["snapshot"] is False
    assert "qemu-img" in resultado["errors"][0]
