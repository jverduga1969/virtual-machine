"""QMP estable, lector con buffer y sustitución de ISO (Fase 2)."""

import json

import pytest

import services.vm_runner as vr


@pytest.fixture
def runner():
    r = vr.VMRunner.__new__(vr.VMRunner)
    r._qmp_sockets = {}
    r.active_processes = {}
    return r


def test_socket_qmp_windows_es_estable_y_unico(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    puertos = iter([4444, 4445, 4446])
    monkeypatch.setattr(runner, "_find_free_port", lambda a, b: next(puertos))

    primero = runner._get_qmp_socket_path("vm1")

    assert runner._get_qmp_socket_path("vm1") == primero == "tcp:127.0.0.1:4444"
    assert runner._get_qmp_socket_path("vm2") == "tcp:127.0.0.1:4445"


def test_socket_qmp_linux_sanea_el_id(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)

    assert runner._get_qmp_socket_path("vm/../raro") == "/tmp/qemu-vmraro-qmp.sock"


class _FakeSocket:
    """Socket que devuelve el payload en trozos, como un recv() real."""

    def __init__(self, payload):
        self.payload = payload
        self.sent = []

    def settimeout(self, timeout):
        pass

    def connect(self, address):
        pass

    def sendall(self, data):
        self.sent.append(json.loads(data.decode("utf-8")))

    def recv(self, size):
        trozo, self.payload = self.payload[:size], self.payload[size:]
        return trozo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_qmp_call_lee_banner_y_respuesta_en_un_solo_recv(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    mensajes = [
        {"QMP": {"version": "8.0"}},
        {"return": {}},
        {"event": "SHUTDOWN"},
        {"return": {"ok": True}},
    ]
    payload = b"".join(json.dumps(m).encode() + b"\n" for m in mensajes)
    fake = _FakeSocket(payload)
    monkeypatch.setattr(vr.socket, "socket", lambda *a, **k: fake)

    respuesta = runner._qmp_call("tcp:127.0.0.1:4444", "system_powerdown")

    assert respuesta == {"return": {"ok": True}}
    assert [m["execute"] for m in fake.sent] == ["qmp_capabilities", "system_powerdown"]


def test_qmp_command_interpreta_return_y_error(runner, monkeypatch):
    respuesta = {"return": {}}
    monkeypatch.setattr(runner, "_qmp_call", lambda *a, **k: respuesta)
    assert runner._qmp_command("vm1", "stop") is True

    respuesta = {"error": {"desc": "no hay VM"}}
    assert runner._qmp_command("vm1", "stop") is False


def test_change_iso_descubre_el_lector_real(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    iso = tmp_path / "disco.iso"
    iso.write_bytes(b"iso")
    vistos = []

    def fake_call(sock, comando, argumentos=None):
        vistos.append((comando, argumentos))
        if comando == "query-block":
            return {"return": [{"device": "drive0"}, {"device": "ide-cd0"}]}
        return {"return": {}}

    monkeypatch.setattr(runner, "_qmp_call", fake_call)

    assert runner.change_iso("vm1", str(iso)) is True
    cambios = [args for cmd, args in vistos if cmd == "blockdev-change-medium"]
    assert cambios and cambios[0]["device"] == "ide-cd0"
    assert runner.change_iso("vm1", str(tmp_path / "no-existe.iso")) is False


def test_kill_orphan_no_mata_todas_las_vms(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    disco = tmp_path / "disco.qcow2"
    disco.write_bytes(b"x")

    class _Proc:
        pid = 4242

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            return 0

    proc = _Proc()
    runner.active_processes["vm1"] = proc
    monkeypatch.setattr(
        vr.subprocess, "run",
        lambda *a, **k: pytest.fail("taskkill no debe ejecutarse"))

    runner._kill_orphan_qemu(str(disco), "vm1")

    assert proc.terminated
    assert "vm1" not in runner.active_processes


def test_setup_tpm_rechaza_vm_id_con_metacaracteres(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)
    monkeypatch.setattr(vr.subprocess, "run", lambda *a, **k: pytest.fail("pkill"))
    runner.vms_dir = tmp_path

    with pytest.raises(ValueError, match="ID de VM inválido"):
        runner._setup_tpm({"id": "vm; rm -rf /"}, q35=True)
