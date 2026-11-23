"""Regresiones de la Fase A: diagnóstico honesto y reparación verificable."""

import types
from pathlib import Path

from conftest import ROOT


# ----------------------------------------------------------------------
# Diagnóstico
# ----------------------------------------------------------------------

def test_qemu_img_se_diagnostica_en_ambos_sistemas(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "find_qemu_binary", lambda nombre: f"/fake/{nombre}")
    monkeypatch.setattr(hd, "_windows_accel_status", lambda binario: ("ok", "WHPX"))

    for sistema in (True, False):
        monkeypatch.setattr(hd, "IS_WINDOWS", sistema)
        monkeypatch.setattr(hd, "IS_LINUX", not sistema)
        checks = hd.HostDiagnostics().run_all()
        qemu_img = [c for c in checks if c["name"] == "qemu-img"]
        assert len(qemu_img) == 1
        assert qemu_img[0]["st"] == "ok"
        assert qemu_img[0]["desc"] == "/fake/qemu-img"


def test_qemu_img_faltante_marca_error(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "find_qemu_binary",
                        lambda nombre: "/fake/qemu-system-x86_64" if "system" in nombre else None)
    checks = [c for c in hd.HostDiagnostics().run_all() if c["name"] == "qemu-img"]
    assert checks[0]["st"] == "err"
    assert checks[0]["desc"] == "No instalado"


def test_el_diagnostico_usa_el_mismo_resolvedor_que_el_runner(monkeypatch):
    """Con paths/qemu_dir configurado y sin PATH, QEMU no es un falso negativo."""
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "shutil", types.SimpleNamespace(which=lambda nombre: None))
    monkeypatch.setattr(hd, "find_qemu_binary",
                        lambda nombre: fr"C:\qemu\{nombre}.exe")
    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    monkeypatch.setattr(hd, "IS_LINUX", False)
    monkeypatch.setattr(hd, "_windows_accel_status", lambda binario: ("ok", "WHPX"))

    qemu = [c for c in hd.HostDiagnostics().run_all() if c["name"] == "QEMU"][0]
    assert qemu["st"] == "ok"
    assert qemu["desc"] == r"C:\qemu\qemu-system-x86_64.exe"


def test_ovmf_vars_y_secure_boot_se_comprueban(tmp_path, monkeypatch):
    import services.host_diagnostics as hd

    (tmp_path / "OVMF_CODE.secboot.fd").write_bytes(b"C" * (1024 * 1024 + 1))
    vars_file = tmp_path / "OVMF_VARS.fd"
    vars_file.write_bytes(b"V" * (10 * 1024 + 1))
    monkeypatch.setattr(hd, "IS_LINUX", True)
    monkeypatch.setattr(hd, "IS_WINDOWS", False)
    monkeypatch.setattr(hd, "OVMF_LINUX_DIRS", (str(tmp_path),))
    monkeypatch.setattr(hd, "OVMF_EXTRA_DIRS", ())

    checks = {c["name"]: c for c in hd.HostDiagnostics().run_all()}
    assert checks["OVMF VARS"]["st"] == "ok"
    assert checks["OVMF VARS"]["desc"] == str(vars_file)
    assert checks["OVMF Secure Boot"]["st"] == "ok"


def test_ovmf_vars_windows_se_buscan_junto_al_code(tmp_path, monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    code = tmp_path / "OVMF_CODE.fd"
    code.write_bytes(b"C" * (1024 * 1024 + 1))
    vars_file = tmp_path / "OVMF_VARS.fd"
    vars_file.write_bytes(b"V" * (10 * 1024 + 1))
    assert hd.find_ovmf_vars_windows(str(code)) == str(vars_file)


def test_iommu_deja_de_ser_texto_fijo(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_LINUX", True)
    monkeypatch.setattr(hd, "IS_WINDOWS", False)
    monkeypatch.setattr("services.host_passthrough.check_iommu",
                        lambda: {"in_cmdline": True, "groups": 3,
                                 "needs_reboot": False, "enabled": True})
    checks = {c["name"]: c for c in hd.HostDiagnostics().run_all()}
    assert checks["IOMMU en Kernel"]["st"] == "ok"
    assert checks["IOMMU en Kernel"]["desc"] == "Activo"
    assert checks["Grupos IOMMU"]["desc"] == "Con grupos visibles"


def test_vnc_embedido_se_verifica(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "_module_available", lambda nombre: False)
    checks = [c for c in hd.HostDiagnostics().run_all()
              if c["name"] == "Cliente VNC embebido"]
    assert checks[0]["st"] == "err"


# ----------------------------------------------------------------------
# Reparación verificada
# ----------------------------------------------------------------------

def _fake_plugin(monkeypatch, hp, returncode,stdout="", stderr=""):
    class Proceso:
        def __init__(self):
            self.returncode = returncode

        def poll(self):
            return returncode

        def communicate(self):
            return stdout, stderr

    comandos = []
    monkeypatch.setattr(hp.subprocess, "Popen",
                        lambda args, **kw: (comandos.append(args), Proceso())[1])
    monkeypatch.setattr(hp.QTimer, "singleShot", staticmethod(lambda ms, cb: cb()))
    plugin = object.__new__(hp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None)
    refrescado = []
    plugin.refresh_diagnostics = lambda: refrescado.append(True)
    return plugin, comandos, refrescado


def test_reparacion_linux_espera_y_refresca(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp
    from PyQt6.QtWidgets import QMessageBox

    script = tmp_path / "scripts" / "postinstall.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    monkeypatch.setattr(hp, "__file__", str(tmp_path / "plugins" / "host_config" / "plugin.py"))
    monkeypatch.setattr(hp.platform, "system", lambda: "Linux")
    monkeypatch.setattr(hp.shutil, "which", lambda nombre: "/usr/bin/pkexec")
    monkeypatch.setattr(hp.os, "chmod", lambda *a, **k: None)
    mensajes = []
    criticales = []
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: mensajes.append((a[1], a[2]))))
    monkeypatch.setattr(QMessageBox, "critical",
                        staticmethod(lambda *a, **k: criticales.append(a[2])))
    plugin, comandos, refrescado = _fake_plugin(monkeypatch, hp, 0)

    plugin._run_postinstall()

    assert comandos[0][0] == "pkexec"
    assert str(script) in comandos[0][2]
    assert mensajes[0][0] == "Reparación completada"
    assert not criticales
    assert refrescado


def test_reparacion_con_error_muestra_el_log_y_no_refresca(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp
    from PyQt6.QtWidgets import QMessageBox

    script = tmp_path / "scripts" / "postinstall.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    monkeypatch.setattr(hp, "__file__", str(tmp_path / "plugins" / "host_config" / "plugin.py"))
    monkeypatch.setattr(hp.platform, "system", lambda: "Linux")
    monkeypatch.setattr(hp.shutil, "which", lambda nombre: "/usr/bin/pkexec")
    monkeypatch.setattr(hp.os, "chmod", lambda *a, **k: None)
    errores = []
    informativos = []
    monkeypatch.setattr(QMessageBox, "critical",
                        staticmethod(lambda *a, **k: errores.append((a[1], a[2]))))
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: informativos.append(a[2])))
    plugin, _, refrescado = _fake_plugin(monkeypatch, hp, 1, stderr="qemu-img no encontrado\n")

    plugin._run_postinstall()

    assert errores[0][0] == "Error en la reparación"
    assert "qemu-img no encontrado" in errores[0][1]
    assert not informativos
    assert not refrescado


def test_postinstallers_devuelven_codigo_de_error():
    linux = (ROOT / "scripts" / "postinstall.sh").read_text(encoding="utf-8")
    windows = (ROOT / "scripts" / "postinstall.ps1").read_text(encoding="utf-8")
    assert "set -o pipefail" in linux
    assert "fallo " in linux
    assert '"$ERRORES" -gt 0' in linux
    assert "Add-Error" in windows
    assert "exit 1" in windows
    assert 'Add-Error "No se encontro qemu-img.exe' in windows


# ----------------------------------------------------------------------
# OVMF: reparación con data_dir y Windows
# ----------------------------------------------------------------------

def _label():
    class Label:
        def __init__(self):
            self.texto = ""

        def setText(self, texto):
            self.texto = texto

        def setStyleSheet(self, estilo):
            pass

    return Label()


def test_reparar_ovmf_usa_data_dir(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp

    src = tmp_path / "firmware"
    src.mkdir()
    (src / "OVMF_CODE.secboot.fd").write_bytes(b"C" * (1024 * 1024 + 1))
    (src / "OVMF_VARS.fd").write_bytes(b"V" * (10 * 1024 + 1))
    monkeypatch.setattr(hp, "__file__", str(tmp_path / "plugins" / "host_config" / "plugin.py"))
    monkeypatch.setattr(hp, "OVMF_LINUX_DIRS", (str(src),))
    monkeypatch.setattr(hp, "platform", types.SimpleNamespace(system=lambda: "Linux"))
    monkeypatch.setattr(hp, "find_ovmf_windows", lambda: None)
    monkeypatch.setattr(hp, "find_qemu_binary", lambda nombre: None)

    plugin = object.__new__(hp.Plugin)
    plugin.app = types.SimpleNamespace(data_dir=tmp_path / "datos")
    plugin.lbl_ovmf_status = _label()
    refrescado = []
    plugin.refresh_diagnostics = lambda: refrescado.append(True)
    plugin._fix_ovmf_secure_boot()

    destino = tmp_path / "OSX-KVM"
    assert (destino / "OVMF_CODE.secboot.4m.fd").is_file()
    assert (destino / "OVMF_VARS.secboot.4m.fd").is_file()
    assert refrescado


def test_reparar_ovmf_en_windows_copia_al_data_dir(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp

    src = tmp_path / "qemu"
    src.mkdir()
    code = src / "OVMF_CODE.fd"
    code.write_bytes(b"C" * (1024 * 1024 + 1))
    (src / "OVMF_VARS.fd").write_bytes(b"V" * (10 * 1024 + 1))
    monkeypatch.setattr(hp, "__file__", str(tmp_path / "plugins" / "host_config" / "plugin.py"))
    monkeypatch.setattr(hp, "platform", types.SimpleNamespace(system=lambda: "Windows"))
    monkeypatch.setattr(hp, "find_ovmf_windows", lambda: str(code))
    monkeypatch.setattr(hp, "find_qemu_binary", lambda nombre: None)

    plugin = object.__new__(hp.Plugin)
    datos = tmp_path / "datos"
    plugin.app = types.SimpleNamespace(data_dir=datos)
    plugin.lbl_ovmf_status = _label()
    plugin.refresh_diagnostics = lambda: None
    plugin._fix_ovmf_secure_boot()

    assert (datos / "OVMF_CODE.secboot.4m.fd").is_file()
    assert (datos / "OVMF_VARS.secboot.4m.fd").is_file()


# ----------------------------------------------------------------------
# Rutas por defecto y Fido
# ----------------------------------------------------------------------

def test_default_base_dir_coincide_con_la_app(monkeypatch):
    import core.app_context as ctx

    monkeypatch.setattr(ctx, "IS_WINDOWS", True)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\prueba\AppData\Local")
    assert ctx.default_base_dir() == Path(r"C:\Users\prueba\AppData\Local") / "VirtualMachine"
    monkeypatch.setattr(ctx, "IS_WINDOWS", False)
    monkeypatch.setattr(ctx, "IS_MAC", False)
    assert ctx.default_base_dir() == Path.home() / ".local" / "share" / "virtual-machine"
    monkeypatch.setattr(ctx, "IS_MAC", True)
    assert ctx.default_base_dir() == Path.home() / "Library" / "Application Support" / "VirtualMachine"


def test_fido_es_una_sola_copia_v171_con_parche():
    import re

    texto = (ROOT / "Fido.ps1").read_text(encoding="utf-8-sig")
    assert "Fido v1.71" in texto
    assert "# --- patched-for-linux ---" in texto
    assert "26H2 (Build 26300.9457" in texto
    assert not (ROOT / "services" / "Fido.ps1").exists()


def test_parche_fido_no_escribe_sobre_el_original(tmp_path, monkeypatch):
    import services.iso_sources as fuente

    original = tmp_path / "Fido.ps1"
    original.write_text("$winver = Get-Platform-Version\n", encoding="utf-8")
    monkeypatch.setattr(fuente.tempfile, "gettempdir", lambda: str(tmp_path))

    parcheado = fuente._patch_fido_for_linux(str(original))

    assert parcheado != str(original)
    assert "patched-for-linux" in Path(parcheado).read_text(encoding="utf-8")
    assert original.read_text(encoding="utf-8") == "$winver = Get-Platform-Version\n"
    # Idempotente: la copia ya marcada se reutiliza.
    assert fuente._patch_fido_for_linux(parcheado) == parcheado


def test_linux_pasa_la_copia_parcheada_a_powershell(tmp_path, monkeypatch):
    import services.iso_sources as fuente

    original = tmp_path / "Fido.ps1"
    original.write_text("$winver = Get-Platform-Version\n", encoding="utf-8")
    monkeypatch.setattr(fuente.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(fuente, "IS_WINDOWS", False)
    monkeypatch.setattr(fuente, "_resolve_fido_path", lambda p: str(original))
    monkeypatch.setattr(fuente, "get_host_language", lambda: "English")
    comandos = []

    class Respuesta:
        returncode = 0
        stdout = "https://example.com/Win11.iso\n"
        stderr = ""

    def fake_run(cmd, **kw):
        comandos.append(cmd)
        return Respuesta()

    monkeypatch.setattr(fuente.subprocess, "run", fake_run)
    url = fuente.get_latest_windows_iso_url("Windows 11")

    assert url == "https://example.com/Win11.iso"
    assert "-File" in comandos[0]
    assert comandos[0][comandos[0].index("-File") + 1] != str(original)
