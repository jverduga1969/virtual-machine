"""Detección de WHPX en Windows y aviso de TCG (nunca hablar de KVM)."""

import ctypes
import subprocess

import services.host_adapter as ha


def _host(qemu="C:/qemu/qemu-system-x86_64.exe"):
    host = object.__new__(ha.HostAdapter)
    host.qemu_path = qemu
    return host


def test_whpx_se_detecta_con_la_api_de_windows(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: True)

    def no_debe_llamar_a_qemu(*args, **kwargs):
        raise AssertionError("Si WinHV dice que hay WHPX, no hace falta QEMU")

    monkeypatch.setattr(subprocess, "run", no_debe_llamar_a_qemu)
    assert _host()._check_whpx() is True


def test_whpx_sin_api_prueba_qemu_con_machine_pc(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: False)
    llamadas = []

    def fake_run(cmd, **kwargs):
        llamadas.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _host()._check_whpx() is True
    assert llamadas[0][:3] == ["C:/qemu/qemu-system-x86_64.exe", "-accel", "whpx"]
    assert llamadas[0][llamadas[0].index("-machine") + 1] == "pc"
    assert not any(str(arg).lower() == "sc" for arg in llamadas[0])


def test_whpx_rechazado_por_qemu(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: False)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, 1, "", "qemu-system-x86_64: WHPX is not available")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _host()._check_whpx() is False


def test_whpx_con_aviso_pero_codigo_cero_tambien_falla(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: False)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "", "WHPX is not available")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _host()._check_whpx() is False


def test_whpx_timeout_sin_error_cuenta_como_disponible(monkeypatch):
    """QEMU se queda vivo cuando el acelerador arranca bien."""
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: False)

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 3, output="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _host()._check_whpx() is True


def test_api_de_windows_sin_dll_no_rompe_la_deteccion(monkeypatch):
    class SinWinDLL:
        def __call__(self, *args, **kwargs):
            raise OSError("WinHVPlatform.dll no instalada")

    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ctypes, "WinDLL", SinWinDLL(), raising=False)
    assert ha.windows_whpx_available() is False


def test_sin_qemu_no_intenta_detectar_acelerador(monkeypatch):
    monkeypatch.setattr(ha, "IS_WINDOWS", True)
    monkeypatch.setattr(ha, "windows_whpx_available", lambda: False)
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


def test_consola_cambia_de_monitor_vnc(qapp, app_ctx, monkeypatch):
    from PyQt6.QtWidgets import QWidget
    from plugins.console import plugin as cp

    creados = []

    class FakeVNC(QWidget):
        def __init__(self, parent=None, host=None, port=None):
            super().__init__(parent)
            self.port = port
            creados.append(self)

        def start(self):
            pass

        def stop(self):
            pass

        def set_zoom(self, value):
            pass

    monkeypatch.setattr(cp, "CenteredVNCWidget", FakeVNC)
    plugin = cp.Plugin(app_ctx)
    _, widget = plugin.get_tabs()[0]

    vm = {"id": "vm1", "name": "Mint", "state": "Running",
          "console_proto_idx": 0, "console_mode_idx": 0,
          "vnc_port": 5900, "vnc_heads": {"head_0": 5900, "head_1": 5901}}
    monkeypatch.setattr(app_ctx, "get_vm", lambda vm_id: vm)
    plugin.current_vm_id = "vm1"
    plugin._try_connect_vnc()

    assert creados[-1].port == 5900
    assert plugin.lbl_monitor.text() == "1/2"
    assert not plugin.btn_next_monitor.isHidden()

    plugin._switch_monitor(1)

    assert creados[-1].port == 5901
    assert plugin.lbl_monitor.text() == "2/2"
    widget.close()
