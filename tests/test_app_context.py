"""QSettings compartido y apagado/reinicio/borrado asíncronos (Fase 0)."""

import time

from PyQt6.QtCore import QSettings

from conftest import FakeRunner


def _esperar(predicado, timeout=3.0):
    from PyQt6.QtWidgets import QApplication

    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        QApplication.processEvents()
        if predicado():
            return True
        time.sleep(0.01)
    return predicado()


def test_app_context_usa_unicos_qsettings(app_ctx):
    assert isinstance(app_ctx.settings, QSettings)
    assert app_ctx.vm_repo.data_dir == app_ctx.data_dir


def test_reinicio_espera_a_que_la_vm_se_apague(app_ctx, monkeypatch):
    runner = FakeRunner()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Reiniciar", "state": "Running"})

    app_ctx.reboot_vm("vm1")

    assert _esperar(lambda: ("start", "vm1") in runner.calls)
    assert ("stop", "vm1") in runner.calls
    assert runner.calls.index(("stop", "vm1")) < runner.calls.index(("start", "vm1"))
    assert app_ctx.get_vm("vm1")["state"] == "Running"
    assert not app_ctx._pending_after_stop


def test_fallo_al_apagar_no_dispara_el_reinicio(app_ctx, monkeypatch):
    class RunnerQueFalla(FakeRunner):
        def stop_vm(self, vm_id):
            raise RuntimeError("QEMU no responde")

        def force_stop_vm(self, vm_id):
            raise RuntimeError("ni a la fuerza")

    monkeypatch.setattr(app_ctx, "runner", RunnerQueFalla())
    app_ctx.vm_repo.add({"id": "vm1", "name": "Falla", "state": "Running"})

    app_ctx.reboot_vm("vm1")

    assert _esperar(
        lambda: app_ctx.get_vm("vm1")["state"] == "Error"
        and not app_ctx._pending_after_stop)


def test_delete_de_vm_en_ejecucion_espera_y_borra(app_ctx, monkeypatch):
    runner = FakeRunner()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Borrar", "state": "Running"})
    vm_dir = app_ctx.vms_dir / "vm1"
    vm_dir.mkdir(parents=True)
    (vm_dir / "disco.qcow2").write_bytes(b"x")

    assert app_ctx.delete_vm("vm1") is True
    assert app_ctx.get_vm("vm1") is not None  # todavía está apagándose
    assert _esperar(lambda: app_ctx.get_vm("vm1") is None)

    assert not vm_dir.exists()
    assert ("stop", "vm1") in runner.calls


def test_delete_de_vm_apagada_es_inmediato(app_ctx, monkeypatch):
    monkeypatch.setattr(app_ctx, "runner", FakeRunner())
    app_ctx.vm_repo.add({"id": "vm1", "name": "Apagada", "state": "Apagada"})

    assert app_ctx.delete_vm("vm1") is True
    assert app_ctx.get_vm("vm1") is None


def test_force_stop_cancela_un_borrado_pendiente(app_ctx, monkeypatch):
    runner = FakeRunner()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Cancelar", "state": "Running"})

    app_ctx.delete_vm("vm1")
    app_ctx.force_stop_vm("vm1")

    assert "vm1" not in app_ctx._pending_after_stop
    assert _esperar(lambda: app_ctx.get_vm("vm1") is not None)
    assert app_ctx.get_vm("vm1")["state"] == "Apagada"
