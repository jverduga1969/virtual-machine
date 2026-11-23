"""Regresiones de la Fase B: reparadores Windows, IOMMU, TPM, Fido y API REST."""

import json
import types
import urllib.error
import urllib.request
from pathlib import Path

from conftest import ROOT

SCRIPT_WIN = ROOT / "scripts" / "postinstall.ps1"
SCRIPT_LINUX = ROOT / "scripts" / "postinstall.sh"
UNINSTALL_WIN = ROOT / "scripts" / "uninstall.ps1"
INSTALLER = ROOT / "installer.iss"


# ----------------------------------------------------------------------
# Windows: WHPX, firewall acotado e instalador
# ----------------------------------------------------------------------

def test_postinstall_activa_whpx_con_dism():
    texto = SCRIPT_WIN.read_text(encoding="utf-8")
    assert "Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform" in texto
    assert "Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform" in texto
    assert "-NoRestart" in texto
    # Si falla la activación se avisa, pero no se aborta el resto del reparador.
    assert "No se pudo habilitar WHPX" in texto


def test_firewall_ya_no_abre_rangos_de_puertos():
    texto = SCRIPT_WIN.read_text(encoding="utf-8")
    codigo = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))
    assert "5900-6000" not in codigo
    assert "5930-6000" not in codigo
    assert "VM-Manager VNC" in codigo         # se eliminan las reglas viejas
    assert "VM-Manager QEMU local" in texto   # regla nueva por ejecutable
    assert "-Program $qemuExe" in texto
    assert "-Profile Private" in texto
    assert "-RemoteAddress LocalSubnet" in texto


def test_add_error_no_lanza_excepcion_y_scripts_son_ascii():
    texto = SCRIPT_WIN.read_text(encoding="utf-8")
    assert "[Console]::Error.WriteLine" in texto
    assert "Write-Error $Mensaje" not in texto
    for script in (SCRIPT_WIN, UNINSTALL_WIN):
        contenido = script.read_text(encoding="utf-8")
        assert all(ord(c) < 128 for c in contenido), script


def test_instalador_ejecuta_postinstall_tambien_en_silencioso():
    texto = INSTALLER.read_text(encoding="utf-8")
    codigo = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith(";"))
    assert "skipifsilent" not in codigo
    assert "[UninstallRun]" in texto
    assert "scripts\\uninstall.ps1" in texto
    assert "postinstall.ps1" in texto


def test_uninstall_retira_solo_el_path_guardado():
    texto = UNINSTALL_WIN.read_text(encoding="utf-8")
    assert "postinstall-paths.txt" in texto
    assert 'SetEnvironmentVariable("Path", $limpio, "User")' in texto
    assert "VM-Manager QEMU local" in texto
    # No debe borrar datos de VMs ni desinstalar QEMU.
    assert "Remove-Item" in texto
    assert "dataDir" in texto


def test_postinstall_guarda_las_rutas_de_path_que_anadio():
    texto = SCRIPT_WIN.read_text(encoding="utf-8")
    assert "$pathDirs += $qemuDir" in texto
    assert "$pathDirs += $viewerDir" in texto
    assert "postinstall-paths.txt" in texto


# ----------------------------------------------------------------------
# Linux: dependencias de apoyo y IOMMU desde la UI
# ----------------------------------------------------------------------

def test_postinstall_instala_utilidades_de_apoyo():
    texto = SCRIPT_LINUX.read_text(encoding="utf-8")
    for utilidad in ("lsof", "git", "tar", "xdg-utils", "libnotify-bin", "libnotify-tools"):
        assert utilidad in texto
    assert "instalar_opcional" in texto
    assert 'ERRORES="$antes"' in texto


def test_boton_de_reparar_pasa_enable_iommu(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp
    from PyQt6.QtWidgets import QMessageBox

    script = tmp_path / "scripts" / "postinstall.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    comandos = []

    class Proceso:
        returncode = 0

        def poll(self):
            return 0

        def communicate(self):
            return "", ""

    monkeypatch.setattr(hp, "__file__", str(tmp_path / "plugins" / "host_config" / "plugin.py"))
    monkeypatch.setattr(hp.platform, "system", lambda: "Linux")
    monkeypatch.setattr(hp.shutil, "which", lambda nombre: "/usr/bin/pkexec")
    monkeypatch.setattr(hp.os, "chmod", lambda *a, **k: None)
    monkeypatch.setattr(hp.subprocess, "Popen",
                        lambda args, **kw: (comandos.append(args), Proceso())[1])
    monkeypatch.setattr(hp.QTimer, "singleShot", staticmethod(lambda ms, cb: cb()))
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: None))

    plugin = object.__new__(hp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None)
    plugin.refresh_diagnostics = lambda: None
    plugin.cb_iommu = types.SimpleNamespace(isChecked=lambda: True)
    plugin._run_postinstall()

    assert comandos[0][-1] == "--enable-iommu"


# ----------------------------------------------------------------------
# Diagnóstico: TPM, Fido, soporte y driver USB
# ----------------------------------------------------------------------

def test_tpm_windows_se_verifica_con_qemu(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    monkeypatch.setattr(hd, "IS_LINUX", False)
    monkeypatch.setattr(hd, "find_qemu_binary", lambda nombre: r"C:\qemu\qemu-system-x86_64.exe")
    monkeypatch.setattr(hd, "_windows_accel_status", lambda binario: ("ok", "WHPX"))
    monkeypatch.setattr(hd, "check_fido", lambda: ("ok", "Fido.ps1"))
    monkeypatch.setattr(hd, "qemu_supports_tpm", lambda ruta: True)

    tpm = [c for c in hd.HostDiagnostics().run_all() if c["name"] == "TPM 2.0"][0]
    assert tpm["st"] == "ok"
    assert "verificado" in tpm["desc"]

    monkeypatch.setattr(hd, "qemu_supports_tpm", lambda ruta: False)
    tpm = [c for c in hd.HostDiagnostics().run_all() if c["name"] == "TPM 2.0"][0]
    assert tpm["st"] == "warn"


def test_qemu_supports_tpm_pregunta_al_binario(monkeypatch):
    import services.host_adapter as ha

    llamadas = []

    class Resultado:
        stdout = "Available TPM backends:\n  emulator\n"
        stderr = ""

    monkeypatch.setattr(ha.subprocess, "run",
                        lambda cmd, **kw: (llamadas.append(cmd), Resultado())[1])
    assert ha.qemu_supports_tpm("/usr/bin/qemu-system-x86_64") is True
    assert llamadas[0][1:3] == ["-tpmdev", "help"]


def test_check_fido_valida_version_y_parche(tmp_path, monkeypatch):
    import services.host_diagnostics as hd
    import services.iso_sources as fuente

    fido = tmp_path / "Fido.ps1"
    fido.write_text("Fido v1.71\n# --- patched-for-linux ---\n", encoding="utf-8")
    monkeypatch.setattr(fuente, "_resolve_fido_path", lambda ruta, download=True: str(fido))
    assert hd.check_fido() == ("ok", str(fido))

    fido.write_text("Fido v1.70\n", encoding="utf-8")
    assert hd.check_fido() == ("warn", "Versión antigua (se espera v1.71)")

    fido.write_text("Fido v1.71\n", encoding="utf-8")
    assert hd.check_fido() == ("warn", "Falta el parche multiplataforma")

    monkeypatch.setattr(fuente, "_resolve_fido_path", lambda ruta, download=True: "")
    assert hd.check_fido() == ("err", "No encontrado")


def test_diagnostico_no_descarga_fido(monkeypatch):
    import services.iso_sources as fuente

    def no_descargar(*args, **kwargs):
        raise AssertionError("el diagnóstico no debe descargar Fido")

    monkeypatch.setattr(fuente._session, "get", no_descargar)

    # Con la copia canónica junto al repo, no se descarga nada.
    assert fuente._resolve_fido_path("Fido.ps1", download=False) == str(ROOT / "Fido.ps1")


def test_utilidades_y_driver_usb_se_diagnostican(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", False)
    monkeypatch.setattr(hd, "IS_LINUX", True)
    monkeypatch.setattr(hd.shutil, "which", lambda nombre: f"/usr/bin/{nombre}")
    checks = {c["name"]: c for c in hd.HostDiagnostics().run_all()}
    assert checks["Utilidades de apoyo"]["st"] == "ok"

    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    monkeypatch.setattr(hd, "IS_LINUX", False)
    monkeypatch.setattr(hd, "find_qemu_binary", lambda nombre: None)
    monkeypatch.setattr(hd, "_windows_accel_status", lambda binario: ("warn", "TCG"))
    monkeypatch.setattr(hd, "check_fido", lambda: ("err", "No encontrado"))
    checks = {c["name"]: c for c in hd.HostDiagnostics().run_all()}
    usb = checks["Driver USB (WinUSB/libusbK)"]
    assert usb["st"] == "warn"
    assert "Zadig" in usb["desc"]


def test_ui_ofrece_abrir_zadig(qapp, monkeypatch):
    from plugins.host_config import plugin as hp

    abiertas = []
    monkeypatch.setattr(hp.QDesktopServices, "openUrl",
                        lambda url: abiertas.append(url.toString()))
    plugin = object.__new__(hp.Plugin)
    plugin._open_zadig()
    assert abiertas == ["https://zadig.akeo.ie/"]


# ----------------------------------------------------------------------
# API REST real
# ----------------------------------------------------------------------

def test_api_rest_arranca_autentica_y_se_detiene():
    from services import rest_api

    eventos = []

    class AppFalsa:
        def get_vms(self):
            return [{"id": "vm1", "name": "Mint", "state": "Apagada"}]

        def get_vm(self, vm_id):
            return {"id": vm_id, "name": "Mint"} if vm_id == "vm1" else None

        def start_vm(self, vm_id):
            eventos.append(("start", vm_id))

        def stop_vm(self, vm_id):
            eventos.append(("stop", vm_id))

    ok, _ = rest_api.start(AppFalsa(), 0, "token-de-prueba")
    assert ok is True
    servidor = rest_api._servidor
    puerto = servidor.server_address[1]
    base = f"http://127.0.0.1:{puerto}"

    def pedir(ruta, metodo="GET", token=None):
        cabeceras = {}
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        peticion = urllib.request.Request(base + ruta, headers=cabeceras, method=metodo)
        try:
            with urllib.request.urlopen(peticion, timeout=3) as respuesta:
                return respuesta.status, json.loads(respuesta.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        assert pedir("/health")[0] == 401
        codigo, datos = pedir("/health", token="token-de-prueba")
        assert codigo == 200 and datos["ok"] is True
        codigo, datos = pedir("/vms", token="token-de-prueba")
        assert datos["vms"][0]["id"] == "vm1"
        assert pedir("/vms/vm1/start", "POST")[0] == 401
        assert pedir("/vms/vm1/start", "POST", "token-de-prueba")[0] == 202
        assert pedir("/vms/otro/start", "POST", "token-de-prueba")[0] == 404
        assert eventos == [("start", "vm1")]
    finally:
        assert rest_api.stop()[0] is True
    assert rest_api.is_running() is False


def test_api_rest_enlazada_solo_a_localhost():
    codigo = (ROOT / "services" / "rest_api.py").read_text(encoding="utf-8")
    assert '("127.0.0.1", puerto)' in codigo
    assert "Authorization" in codigo
    assert "compare_digest" in codigo
    assert "services.rest_api" in (ROOT / "virtualmachine.spec").read_text(encoding="utf-8")


def test_checkbox_api_valida_el_puerto(qapp, monkeypatch):
    import plugins.host_config.plugin as hp
    from PyQt6.QtWidgets import QMessageBox

    avisos = []
    monkeypatch.setattr(QMessageBox, "warning",
                        staticmethod(lambda *a, **k: avisos.append(a[2])))
    plugin = object.__new__(hp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None, settings=types.SimpleNamespace(
        value=lambda *a: "8730", setValue=lambda *a: None))
    plugin.e_port = types.SimpleNamespace(text=lambda: "70000")
    plugin.e_token = types.SimpleNamespace(text=lambda: "token")
    plugin.lbl_api_status = types.SimpleNamespace(setText=lambda texto: None,
                                                  setStyleSheet=lambda estilo: None)

    from PyQt6.QtWidgets import QCheckBox

    plugin.cb_api = QCheckBox()
    plugin.cb_api.setChecked(True)
    plugin._on_api_toggled(True)
    assert plugin.cb_api.isChecked() is False
    assert avisos and "1024" in avisos[0]
