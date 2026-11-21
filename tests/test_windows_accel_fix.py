"""El aviso de TCG en Windows debe hablar de WHPX, no de KVM."""

import subprocess

import services.host_adapter as ha


def _host(qemu="C:/qemu/qemu-system-x86_64.exe"):
    host = object.__new__(ha.HostAdapter)
    host.qemu_path = qemu
    return host


def test_whpx_se_comprueba_con_qemu_no_con_sc(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    llamadas = []

    def fake_run(cmd, **kwargs):
        llamadas.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _host()._check_whpx() is True
    assert llamadas[0][:3] == ["C:/qemu/qemu-system-x86_64.exe", "-accel", "whpx"]
    assert "none" in llamadas[0]
    assert not any(str(arg).lower() == "sc" for arg in llamadas[0])


def test_whpx_rechazado_por_qemu(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, 1, "", "qemu-system-x86_64: WHPX is not available")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _host()._check_whpx() is False


def test_whpx_con_aviso_pero_codigo_cero_tambien_falla(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "", "WHPX is not available")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _host()._check_whpx() is False


def test_sin_qemu_no_intenta_detectar_acelerador(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    assert _host(qemu=None)._check_whpx() is False


def test_aviso_consola_windows_habla_de_whpx(qapp, app_ctx, monkeypatch):
    from PyQt6.QtWidgets import QLabel
    from plugins.console.plugin import Plugin

    monkeypatch.setattr(app_ctx, "tr", lambda texto: texto)
    app_ctx.host.acceleration = "tcg"
    app_ctx.host.is_windows = True

    _, widget = Plugin(app_ctx).get_tabs()[0]
    avisos = [l.text() for l in widget.findChildren(QLabel) if "TCG" in l.text()]
    assert len(avisos) == 1
    assert "WHPX" in avisos[0]
    assert "KVM" not in avisos[0]
    assert "hipervisor de Windows" in avisos[0]


def test_aviso_consola_linux_sigue_hablando_de_kvm(qapp, app_ctx, monkeypatch):
    from PyQt6.QtWidgets import QLabel
    from plugins.console.plugin import Plugin

    monkeypatch.setattr(app_ctx, "tr", lambda texto: texto)
    app_ctx.host.acceleration = "tcg"
    app_ctx.host.is_windows = False

    _, widget = Plugin(app_ctx).get_tabs()[0]
    avisos = [l.text() for l in widget.findChildren(QLabel) if "TCG" in l.text()]
    assert len(avisos) == 1
    assert "KVM" in avisos[0]
    assert "WHPX" not in avisos[0]
