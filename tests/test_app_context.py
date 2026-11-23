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


def test_apagado_desde_invitado_actualiza_estado(app_ctx, monkeypatch):
    runner = FakeRunner()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Apagado interno", "state": "Running"})

    # El monitor de VMRunner retira el proceso antes de emitir la señal.
    runner.active_processes.clear()
    app_ctx.vm_process_finished.emit("vm1", 0)

    assert _esperar(lambda: app_ctx.get_vm("vm1")["state"] == "Apagada")


def test_pausa_y_reanuda_actualizan_estado_solo_si_qmp_acepta(app_ctx, monkeypatch):
    runner = FakeRunner()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Pausas", "state": "Running"})

    assert app_ctx.pause_vm("vm1") is True
    assert app_ctx.get_vm("vm1")["state"] == "Paused"
    assert app_ctx.pause_vm("vm1") is False  # ya está pausada
    assert runner.calls.count(("pause", "vm1")) == 1

    assert app_ctx.resume_vm("vm1") is True
    assert app_ctx.get_vm("vm1")["state"] == "Running"
    assert app_ctx.resume_vm("vm1") is False
    assert runner.calls.count(("resume", "vm1")) == 1


def test_pausa_rechazada_no_cambia_estado(app_ctx, monkeypatch):
    class RunnerQueRechaza(FakeRunner):
        def pause_vm(self, vm_id):
            return False

    runner = RunnerQueRechaza()
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Pausa fallida", "state": "Running"})

    assert app_ctx.pause_vm("vm1") is False
    assert app_ctx.get_vm("vm1")["state"] == "Running"


def test_apagar_sin_proceso_no_queda_en_apagando(app_ctx, monkeypatch):
    monkeypatch.setattr(app_ctx, "runner", FakeRunner())
    app_ctx.vm_repo.add({"id": "vm1", "name": "Huerfana", "state": "Running"})

    app_ctx.stop_vm("vm1")

    assert _esperar(lambda: app_ctx.get_vm("vm1")["state"] == "Apagada")
    assert "vm1" not in app_ctx._stopping


def test_iniciar_estado_paused_huerfano_arranca_de_cero(app_ctx, monkeypatch):
    runner = FakeRunner()
    monkeypatch.setattr(app_ctx, "runner", runner)
    app_ctx.vm_repo.add({"id": "vm1", "name": "Pausada muerta", "state": "Paused"})

    app_ctx.start_vm("vm1")

    assert ("start", "vm1") in runner.calls
    assert ("resume", "vm1") not in runner.calls
    assert app_ctx.get_vm("vm1")["state"] == "Running"
