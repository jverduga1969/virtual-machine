"""Regresiones de la fase 1 de portabilidad a Windows.

Simulan Windows con monkeypatch: no necesitan ni Windows ni QEMU reales.
"""

import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

from core.i18n import tr


def test_fido_en_windows_no_se_parchea_y_usa_powershell(tmp_path, monkeypatch):
    import services.iso_sources as fuente

    fido = tmp_path / "Fido.ps1"
    original = "$winver = Get-Platform-Version\n"
    fido.write_text(original, encoding="utf-8")

    monkeypatch.setattr(fuente, "IS_WINDOWS", True)
    monkeypatch.setattr(fuente, "_resolve_fido_path", lambda p: str(fido))

    def no_parchar(path):
        raise AssertionError("Fido.ps1 no debe parchearse en Windows")

    monkeypatch.setattr(fuente, "_patch_fido_for_linux", no_parchar)

    llamadas = []

    class Respuesta:
        returncode = 0
        stdout = "https://example.com/Win11.iso\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        llamadas.append(cmd)
        return Respuesta()

    monkeypatch.setattr(fuente.subprocess, "run", fake_run)

    url = fuente.get_latest_windows_iso_url("Windows 11")

    assert url == "https://example.com/Win11.iso"
    assert llamadas[0][0] == "powershell.exe"
    assert fido.read_text(encoding="utf-8") == original


def test_fido_se_resuelve_desde_el_paquete_empaquetado(tmp_path, monkeypatch):
    import services.iso_sources as fuente

    fido = tmp_path / "Fido.ps1"
    fido.write_text("empaquetado", encoding="utf-8")
    monkeypatch.setattr(fuente, "IS_WINDOWS", True)
    monkeypatch.setattr(fuente.sys, "frozen", True, raising=False)
    monkeypatch.setattr(fuente.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert fuente._resolve_fido_path("Fido-inexistente.ps1") == str(fido)


def test_macos_usa_el_interprete_de_la_app_y_no_inyecta_term(qapp, tmp_path,
                                                            monkeypatch):
    import services.macos_recovery as mr

    script = tmp_path / "OSX-KVM" / "fetch-macOS-v2.py"
    script.parent.mkdir()
    script.write_text("print('hola')\n", encoding="utf-8")

    class Env(dict):
        def insert(self, clave, valor):
            self[clave] = valor

    class EnvFactory:
        @staticmethod
        def systemEnvironment():
            return Env()

    class FakeSignal:
        def connect(self, callback):
            return None

    class FakeProcess:
        class ProcessChannelMode:
            MergedChannels = object()

        def __init__(self, parent=None):
            self.entorno = None
            self.arranque = None

        def setProcessChannelMode(self, modo):
            pass

        def setWorkingDirectory(self, directorio):
            pass

        def setProcessEnvironment(self, entorno):
            self.entorno = entorno

        readyReadStandardOutput = FakeSignal()
        finished = FakeSignal()

        def start(self, ejecutable, argumentos):
            self.arranque = (ejecutable, argumentos)

        def waitForStarted(self, espera):
            return True

        def write(self, datos):
            pass

    monkeypatch.setattr(mr, "IS_WINDOWS", True)
    monkeypatch.setattr(mr, "QProcess", FakeProcess)
    monkeypatch.setattr(mr, "QProcessEnvironment", EnvFactory)
    monkeypatch.setattr(mr, "sys", types.SimpleNamespace(
        executable="C:/Python/python.exe", frozen=False))

    descargador = mr.MacOSDownloader("Tahoe", tmp_path / "dest", tmp_path)
    descargador.start()

    assert descargador.process.arranque[0] == "C:/Python/python.exe"
    assert "TERM" not in descargador.process.entorno
    assert descargador.process.arranque[1][0].endswith("fetch-macOS-v2.py")


def test_ram_de_windows_no_se_cuenta_dos_veces(monkeypatch):
    import services.host_profile as hp

    monkeypatch.setattr(hp, "IS_WINDOWS", True)
    falso_psutil = types.ModuleType("psutil")
    falso_psutil.virtual_memory = lambda: types.SimpleNamespace(total=16 * 1024 ** 3)
    monkeypatch.setitem(sys.modules, "psutil", falso_psutil)

    perfil = hp.HostProfile()
    assert perfil.total_ram_mb == 16 * 1024


def test_ram_de_windows_con_wmi_suma_solo_los_modulos(monkeypatch):
    import services.host_profile as hp

    monkeypatch.setattr(hp, "IS_WINDOWS", True)
    roto = types.ModuleType("psutil")

    def fallar():
        raise RuntimeError("psutil no disponible")

    roto.virtual_memory = fallar
    monkeypatch.setitem(sys.modules, "psutil", roto)

    class Memoria:
        Capacity = 8 * 1024 ** 3

    class WMI:
        def Win32_PhysicalMemory(self):
            return [Memoria(), Memoria()]

    falso_wmi = types.ModuleType("wmi")
    falso_wmi.WMI = WMI
    monkeypatch.setitem(sys.modules, "wmi", falso_wmi)

    assert hp.HostProfile().total_ram_mb == 16 * 1024


@pytest.mark.skipif(shutil.which("7z") is None, reason="7z no disponible")
def test_generador_iso_funciona_sin_herramientas_externas(tmp_path):
    from services.iso_writer import create_iso

    origen = tmp_path / "staging"
    (origen / "linux").mkdir(parents=True)
    (origen / "windows").mkdir()
    (origen / "linux" / "install-qga-debian.sh").write_text("#!/bin/bash\necho hola\n",
                                                             encoding="utf-8")
    (origen / "windows" / "install-qga.bat").write_text("echo hola\r\n",
                                                        encoding="utf-8")

    iso = create_iso(origen, tmp_path / "guest-tools.iso")
    listado = subprocess.run(["7z", "l", str(iso)], capture_output=True,
                             text=True, timeout=30)
    assert listado.returncode == 0
    assert "linux/install-qga-debian.sh" in listado.stdout
    assert "windows/install-qga.bat" in listado.stdout

    salida = tmp_path / "extraido"
    salida.mkdir()
    extraido = subprocess.run(["7z", "x", f"-o{salida}", str(iso)],
                              capture_output=True, text=True, timeout=30)
    assert extraido.returncode == 0
    assert (salida / "linux" / "install-qga-debian.sh").read_text(
        encoding="utf-8").startswith("#!/bin/bash")


def test_graficos_3d_no_usan_dev_dri_en_windows(monkeypatch):
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    runner = vr.VMRunner.__new__(vr.VMRunner)
    for indice in (2, 3):
        args = runner._build_graphics_device_args({
            "graphics_idx": indice, "console_proto_idx": 1, "vram_idx": 0,
        })
        combinado = " ".join(args)
        assert "/dev/dri" not in combinado
        assert "virtio-vga-gl" not in combinado
        assert "-display" in args


def test_diagnostico_windows_comprueba_acelerador_y_admin(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    monkeypatch.setattr(hd, "IS_LINUX", False)
    monkeypatch.setattr(hd, "_windows_accel_status",
                        lambda binario: ("ok", "WHPX disponible (comprobado)"))
    monkeypatch.setattr(hd, "_is_windows_admin", lambda: True)
    monkeypatch.setattr(hd.shutil, "which",
                        lambda nombre: "C:/qemu/qemu-system-x86_64.exe"
                        if "qemu" in nombre else None)

    checks = {c["name"]: c for c in hd.HostDiagnostics().run_all()}
    assert checks["WHPX (Windows Hypervisor)"]["desc"] == "WHPX disponible (comprobado)"
    assert checks["Administrador"]["st"] == "ok"
    assert checks["Firmware UEFI (OVMF)"]["st"] == "warn"


def test_montaje_de_imagenes_aviso_en_windows(qapp, monkeypatch):
    import plugins.config_vm.plugin as cp
    from PyQt6.QtWidgets import QMessageBox

    mensajes = []
    monkeypatch.setattr(cp, "IS_WINDOWS", True)
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: mensajes.append(
                            a[2] if len(a) > 2 else "")))

    plugin = object.__new__(cp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None)
    plugin._host_mount_unavailable()
    plugin._mount_eject_disk(None, None)

    esperado = tr("El montaje de imágenes en el host no está disponible en Windows.")
    assert mensajes == [esperado, esperado]


def test_menu_optico_windows_no_ofrece_montaje_en_host(qapp, tmp_path, monkeypatch):
    import plugins.config_vm.plugin as cp
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QInputDialog

    iso = tmp_path / "disco.iso"
    iso.write_bytes(b"iso")
    opciones = []

    def fake_getItem(parent, titulo, etiqueta, items, *args, **kwargs):
        opciones.extend(items)
        return "", False

    monkeypatch.setattr(cp, "IS_WINDOWS", True)
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(fake_getItem))

    item = types.SimpleNamespace(
        text=lambda columna: str(iso),
        data=lambda columna, rol: (cp.SOURCE_EXISTING
                                   if rol == Qt.ItemDataRole.UserRole else None),
    )
    plugin = object.__new__(cp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None)
    plugin._get_mount_info = lambda path: None

    plugin._mount_eject_cdrom(item, {"state": "Stopped"})

    assert tr("Expulsar ISO de la VM") in opciones
    assert tr("Montar ISO en el host") not in opciones
    assert tr("Desmontar ISO del host") not in opciones


def test_spice_local_en_windows_usa_tcp_loopback(monkeypatch):
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    runner = vr.VMRunner.__new__(vr.VMRunner)
    args, info = runner._build_display_protocol_args(
        {"id": "vm-test", "console_proto_idx": 1, "console_mode_idx": 0,
         "graphics_idx": 0, "share_clipboard": True})

    spice = " ".join(args[args.index("-spice") + 1].split())
    assert "unix=on" not in spice
    assert "addr=127.0.0.1" in spice
    assert info["type"] == "spice_tcp"
    assert 5930 <= info["port"] < 6000

    comandos = []
    # El lanzador real comprobaría `remote-viewer`; simulamos esa búsqueda.
    monkeypatch.setattr(vr.shutil, "which", lambda nombre: "C:/qemu/remote-viewer.exe")

    def fake_popen(cmd, **kwargs):
        comandos.append(cmd)
        return types.SimpleNamespace(poll=lambda: None, terminate=lambda: None,
                                     wait=lambda timeout: None)

    monkeypatch.setattr(vr.subprocess, "Popen", fake_popen)
    proc = runner._launch_external_viewer("vm-test", info)
    assert proc is not None
    assert comandos[0][1].startswith(f"spice://127.0.0.1:{info['port']}")


def test_spice_remoto_en_linux_sigue_en_0_0_0_0(monkeypatch):
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", False)
    runner = vr.VMRunner.__new__(vr.VMRunner)
    args, info = runner._build_display_protocol_args(
        {"id": "vm-test", "console_proto_idx": 2, "console_mode_idx": 0,
         "graphics_idx": 0, "share_clipboard": False})
    spice = args[args.index("-spice") + 1]
    assert "addr=0.0.0.0" in spice
    assert info["type"] == "spice_remote"


def test_reparar_en_windows_lanza_postinstall_ps1(qapp, tmp_path, monkeypatch):
    import plugins.host_config.plugin as hp
    from PyQt6.QtWidgets import QMessageBox

    (tmp_path / "scripts").mkdir()
    script = tmp_path / "scripts" / "postinstall.ps1"
    script.write_text("Write-Host 'ok'\n", encoding="utf-8")
    comandos = []
    mensajes = []
    monkeypatch.setattr(hp.platform, "system", lambda: "Windows")
    monkeypatch.setattr(hp.Plugin, "_scripts_dir_windows", lambda self: tmp_path / "scripts",
                        raising=False)
    monkeypatch.setattr(hp.subprocess, "Popen",
                        lambda args, **kw: comandos.append((args, kw)))
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: mensajes.append(a[2])))

    plugin = object.__new__(hp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None)
    plugin._run_postinstall()

    assert comandos[0][0][0] == "powershell.exe"
    unidos = " ".join(comandos[0][0])
    assert "-Verb RunAs" in unidos
    assert "postinstall.ps1" in unidos
    assert "ExecutionPolicy" in unidos
    assert mensajes


def test_instalador_y_spec_incluyen_el_reparador_win(monkeypatch):
    from conftest import ROOT

    iss = (ROOT / "installer.iss").read_text(encoding="utf-8")
    spec = (ROOT / "virtualmachine.spec").read_text(encoding="utf-8")

    seccion_archivos = iss.split("[Files]")[1].split("[Icons]")[0]
    seccion_run = iss.split("[Run]")[1]
    assert "postinstall.ps1" in seccion_archivos
    assert "postinstall.ps1" in seccion_run
    assert '("scripts", "scripts")' in spec
    assert '("Fido.ps1", ".")' in spec
    assert '("i18n", "i18n")' in spec
    assert "icon.icn" not in spec
    assert "services.iso_writer" in spec


def test_postinstall_windows_usa_ids_reales_de_winget():
    from conftest import ROOT

    texto = (ROOT / "scripts" / "postinstall.ps1").read_text(encoding="utf-8")
    assert "SoftwareFreedomConservancy.QEMU" in texto
    assert "RedHat.VirtViewer" in texto
    # Python/PyQt6 ya van dentro del ejecutable; no se instalan por separado.
    for obsoleto in ("python.pyqt6", '"python"', '"tightvnc"'):
        assert obsoleto not in texto
    assert "New-NetFirewallRule" in texto


def test_ci_compila_instalador_en_windows():
    from conftest import ROOT

    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "build-windows" in workflow
    assert "windows-latest" in workflow
    assert "ISCC.exe" in workflow
    assert "virtualmachine.spec" in workflow
    assert "upload-artifact" in workflow


def test_guest_tools_usa_generador_python_sin_mkisofs(qapp, tmp_path, monkeypatch):
    import plugins.config_vm.plugin as cp
    from PyQt6.QtWidgets import QMessageBox, QTreeWidget

    llamadas = []

    def fake_create_iso(origen, destino):
        llamadas.append((Path(origen), Path(destino)))
        Path(destino).write_bytes(b"ISO")
        return Path(destino)

    monkeypatch.setattr(cp.shutil, "which", lambda nombre: None)
    monkeypatch.setattr("services.iso_writer.create_iso", fake_create_iso)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(QMessageBox, "warning",
                        staticmethod(lambda *a, **k: pytest.fail("No debía avisar")))
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))

    plugin = object.__new__(cp.Plugin)
    plugin.app = types.SimpleNamespace(parent=lambda: None,
                                       isos_dir=str(tmp_path / "isos"))
    plugin.tree_storage = QTreeWidget()
    plugin._sync_boot = lambda: None

    plugin._create_guest_tools_iso()

    assert llamadas
    assert llamadas[0][1] == tmp_path / "isos" / "guest-tools.iso"
    assert (tmp_path / "isos" / "guest-tools.iso").read_bytes() == b"ISO"
