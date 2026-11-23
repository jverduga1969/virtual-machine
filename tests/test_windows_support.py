"""Regresiones de la fase 1 de portabilidad a Windows.

Simulan Windows con monkeypatch: no necesitan ni Windows ni QEMU reales.
"""

import json
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
    # 7-Zip usa `\\` en Windows y `/` en Linux.
    normalizado = listado.stdout.replace("\\", "/")
    assert "linux/install-qga-debian.sh" in normalizado
    assert "windows/install-qga.bat" in normalizado

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


def test_ovmf_windows_no_hace_glob_recursivo(tmp_path, monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", True)
    monkeypatch.setattr(hd.glob, "glob",
                        lambda *a, **k: pytest.fail("No debe buscar en todo Program Files"))
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        monkeypatch.setenv(variable, str(tmp_path))

    fd = tmp_path / "qemu" / "share" / "qemu" / "OVMF.fd"
    fd.parent.mkdir(parents=True)
    fd.write_bytes(b"F" * (1024 * 1024 + 1))

    assert hd.find_ovmf_windows() == str(fd)


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


def test_config_vm_windows_oculta_passthrough(qapp, app_ctx, monkeypatch):
    import plugins.config_vm.plugin as cp

    monkeypatch.setattr(cp, "IS_WINDOWS", True)
    plugin = cp.Plugin(app_ctx)
    _, widget = plugin.get_tabs()[0]
    menu = [plugin.list_menu.item(i).text()
            for i in range(plugin.list_menu.count())]

    assert not any("Passthrough" in texto for texto in menu)
    assert not hasattr(plugin, "tree_passthrough")


def test_config_vm_linux_conserva_passthrough(qapp, app_ctx, monkeypatch):
    import plugins.config_vm.plugin as cp

    monkeypatch.setattr(cp, "IS_WINDOWS", False)
    plugin = cp.Plugin(app_ctx)
    _, widget = plugin.get_tabs()[0]
    menu = [plugin.list_menu.item(i).text()
            for i in range(plugin.list_menu.count())]

    assert any("Passthrough" in texto for texto in menu)
    assert hasattr(plugin, "tree_passthrough")


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
    monkeypatch.setattr(vr.VMRunner, "_wait_for_tcp_port",
                        staticmethod(lambda port, timeout=15.0: True))
    proc = runner._launch_external_viewer("vm-test", info)
    assert proc is not None
    assert comandos[0] == [
        "C:/qemu/remote-viewer.exe", "--hotkeys", "release-cursor=ctrl+alt",
        f"spice://127.0.0.1:{info['port']}"]


def test_varios_monitores_abren_un_remote_viewer_por_head(monkeypatch):
    import types

    import services.vm_runner as vr

    monkeypatch.setattr(vr, "find_qemu_binary", lambda nombre: "C:/qemu/remote-viewer.exe")
    runner = vr.VMRunner.__new__(vr.VMRunner)
    runner.active_viewers = {}
    runner._active_viewer_info = {}

    comandos = []

    def fake_popen(cmd, **kwargs):
        comandos.append(cmd)
        return types.SimpleNamespace(poll=lambda: None, terminate=lambda: None,
                                     wait=lambda timeout: None)

    monkeypatch.setattr(vr.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(vr.VMRunner, "_wait_for_tcp_port",
                        staticmethod(lambda port, timeout=15.0: True))
    procs = runner._launch_external_viewer("vm1", {
        "type": "multi",
        "heads": [
            {"type": "spice_tcp", "port": 5930, "title": "Mint · Monitor 1"},
            {"type": "spice_tcp", "port": 5931, "title": "Mint · Monitor 2"},
        ],
    })

    assert len(procs) == 2
    assert comandos[0][1:5] == ["--hotkeys", "release-cursor=ctrl+alt",
                                "--title", "Mint · Monitor 1"]
    assert comandos[1][1:5] == ["--hotkeys", "release-cursor=ctrl+alt",
                                "--title", "Mint · Monitor 2"]
    assert comandos[0][5] == "spice://127.0.0.1:5930"
    assert comandos[1][5] == "spice://127.0.0.1:5931"

    runner.active_viewers["vm1"] = procs
    runner._kill_external_viewer("vm1")
    assert "vm1" not in runner.active_viewers


def test_visor_no_se_abre_si_el_puerto_spice_no_aparece(monkeypatch):
    import types

    import services.vm_runner as vr

    monkeypatch.setattr(vr, "find_qemu_binary", lambda nombre: "C:/qemu/remote-viewer.exe")
    monkeypatch.setattr(vr.VMRunner, "_wait_for_tcp_port",
                        staticmethod(lambda port, timeout=15.0: False))
    lanzados = []
    monkeypatch.setattr(vr.subprocess, "Popen",
                        lambda cmd, **kwargs: lanzados.append(cmd))

    runner = vr.VMRunner.__new__(vr.VMRunner)
    proc = runner._launch_external_viewer(
        "vm1", {"type": "spice_tcp", "port": 5931})

    assert proc is None
    assert lanzados == []


def test_vnc_multimonitor_abre_un_viewer_por_head(monkeypatch):
    import types

    import services.vm_runner as vr

    monkeypatch.setattr(vr, "find_qemu_binary", lambda nombre: "C:/qemu/remote-viewer.exe")
    runner = vr.VMRunner.__new__(vr.VMRunner)
    runner.active_viewers = {}
    runner._active_viewer_info = {}

    comandos = []

    def fake_popen(cmd, **kwargs):
        comandos.append(cmd)
        return types.SimpleNamespace(poll=lambda: None, terminate=lambda: None,
                                     wait=lambda timeout: None)

    monkeypatch.setattr(vr.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(vr.VMRunner, "_wait_for_tcp_port",
                        staticmethod(lambda port, timeout=15.0: True))

    procs = runner._launch_external_viewer("vm1", {
        "type": "multi",
        "heads": [
            {"type": "vnc", "port": 5900, "title": "Mint · Monitor 1"},
            {"type": "vnc", "port": 5901, "title": "Mint · Monitor 2"},
        ],
    })

    assert len(procs) == 2
    assert comandos[0][1:6] == ["--hotkeys", "release-cursor=ctrl+alt",
                                "--title", "Mint · Monitor 1",
                                "vnc://127.0.0.1:5900"]
    assert comandos[1][1:6] == ["--hotkeys", "release-cursor=ctrl+alt",
                                "--title", "Mint · Monitor 2",
                                "vnc://127.0.0.1:5901"]


def test_reabrir_ventana_cerrada_sin_reiniciar_vm(monkeypatch):
    import types

    import services.vm_runner as vr

    runner = vr.VMRunner.__new__(vr.VMRunner)
    qemu = types.SimpleNamespace(poll=lambda: None)
    cerrado = types.SimpleNamespace(poll=lambda: 0)
    runner.active_processes = {"vm1": qemu}
    runner.active_viewers = {"vm1": cerrado}
    info = {"type": "spice_tcp", "port": 5931}
    runner._active_viewer_info = {"vm1": info}

    lanzados = []
    nuevo = types.SimpleNamespace(poll=lambda: None)

    def fake_launch(self, vm_id, data):
        lanzados.append((vm_id, data))
        return nuevo

    monkeypatch.setattr(vr.VMRunner, "_launch_external_viewer", fake_launch)

    assert runner.reopen_viewer("vm1") is True
    assert lanzados == [("vm1", info)]
    assert runner.active_viewers["vm1"] is nuevo
    assert runner.active_processes["vm1"] is qemu
    assert runner._active_viewer_info["vm1"] is info


def test_reabrir_ventana_no_duplica_si_sigue_abierta(monkeypatch):
    import types

    import services.vm_runner as vr

    runner = vr.VMRunner.__new__(vr.VMRunner)
    vivo = types.SimpleNamespace(poll=lambda: None)
    runner.active_processes = {"vm1": types.SimpleNamespace(poll=lambda: None)}
    runner.active_viewers = {"vm1": vivo}
    runner._active_viewer_info = {"vm1": {"type": "spice_tcp", "port": 5930}}

    llamadas = []
    monkeypatch.setattr(
        vr.VMRunner, "_launch_external_viewer",
        lambda self, vm_id, data: llamadas.append((vm_id, data)))

    assert runner.reopen_viewer("vm1") is True
    assert llamadas == []
    assert runner.active_viewers["vm1"] is vivo


def test_reabrir_ventana_requiere_vm_encendida_y_visor(monkeypatch):
    import types

    import services.vm_runner as vr

    runner = vr.VMRunner.__new__(vr.VMRunner)
    runner.active_processes = {}
    runner.active_viewers = {}
    runner._active_viewer_info = {}
    assert runner.reopen_viewer("vm1") is False

    runner.active_processes = {"vm1": types.SimpleNamespace(poll=lambda: None)}
    assert runner.reopen_viewer("vm1") is False


def test_app_context_solo_ofrece_reabrir_con_vm_encendida_y_visor():
    from core.app_context import AppContext

    ctx = AppContext.__new__(AppContext)
    ctx.runner = types.SimpleNamespace(has_external_viewer=lambda vm_id: True)
    ctx.get_vm = lambda vm_id: {"id": vm_id, "state": "Running"}

    assert ctx.can_reopen_window("vm1") is True
    ctx.get_vm = lambda vm_id: {"id": vm_id, "state": "Apagada"}
    assert ctx.can_reopen_window("vm1") is False
    ctx.get_vm = lambda vm_id: {"id": vm_id, "state": "Running"}
    ctx.runner = types.SimpleNamespace(has_external_viewer=lambda vm_id: False)
    assert ctx.can_reopen_window("vm1") is False


def test_macos_bajo_whpx_no_usa_flags_kvm_incompatibles(tmp_path, monkeypatch):
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    host = types.SimpleNamespace(
        qemu_path="C:/qemu/qemu-system-x86_64.exe",
        acceleration="whpx",
        get_accel_args=lambda: ["-accel", "whpx"],
    )
    runner = vr.VMRunner(host, tmp_path, tmp_path / "vms")
    runner._find_free_vnc_port = lambda exclude=None: 5901

    proyecto = tmp_path / "OSX-KVM" / "OpenCore"
    proyecto.mkdir(parents=True)
    (proyecto / "OpenCore.qcow2").write_bytes(b"oc")

    vm = {
        "id": "mac1",
        "name": "macOS",
        "platform": "macOS",
        "version": "Sonoma",
        "ram": 4096,
        "cores": 4,
        "disk_path": str(tmp_path / "mac.qcow2"),
    }
    cmd = runner.build_command(vm)
    unido = " ".join(str(x) for x in cmd)

    assert "-accel whpx" in unido
    assert "kernel_irqchip=off" in unido
    assert "-cpu Penryn,vendor=GenuineIntel,check" in unido
    assert "-device VGA" in unido or "-device VGA," in unido
    assert "e1000-82545em,netdev=net0" in unido
    assert "kvm=on" not in unido
    assert "+invtsc" not in unido
    assert "hle" not in unido
    assert "rtm" not in unido
    assert "vmware-cpuid-freq=on" not in unido


def test_macos_bajo_whpx_lleva_los_mismos_fixes_de_arranque(tmp_path, monkeypatch):
    """ Los fixes que arreglaron macOS en Linux aplican tambien en Windows:
    EHCI (no xHCI), VGA con 128MB, teclado/tablet en ehci.0 y el global
    ICH9-LPC que mantiene el bridge PCIe del controlador USB. """
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    host = types.SimpleNamespace(
        qemu_path="C:/qemu/qemu-system-x86_64.exe",
        acceleration="whpx",
        get_accel_args=lambda: ["-accel", "whpx"],
    )
    runner = vr.VMRunner(host, tmp_path, tmp_path / "vms")
    runner._find_free_hostfwd_port = lambda p: 2222
    runner._find_free_vnc_port = lambda exclude=None: 5900
    runner._get_qmp_socket_path = lambda vm_id: "C:/tmp/qemu.sock"
    (tmp_path / "OSX-KVM" / "OpenCore").mkdir(parents=True)
    (tmp_path / "OSX-KVM" / "OpenCore" / "OpenCore.qcow2").write_bytes(b"oc")

    vm = {"id": "mac1", "name": "Sonoma", "platform": "macOS",
          "version": "Sonoma (14)", "ram": 4096, "cores": 2,
          "graphics_idx": 5, "vram_idx": 0,
          "initial_resolution": "2560x1440"}
    cmd = runner.build_command(vm)
    unido = " ".join(str(x) for x in cmd)

    # Graficos: se respeta el dispositivo experimental elegido (VMware SVGA),
    # con 128 MB de VRAM. VGA sigue siendo el recomendado por defecto.
    assert "vmware-svga,vgamem_mb=128" in unido
    assert "VGA,vgamem_mb=" not in unido
    # Teclado/tablet por EHCI (USB 2.0), como en la version que funcionaba.
    assert "usb-ehci,id=ehci" in unido
    assert "usb-kbd,bus=ehci.0" in unido
    assert "usb-tablet,bus=ehci.0" in unido
    assert "qemu-xhci" not in unido
    # El global ICH9-LPC es imprescindible bajo WHPX tambien.
    assert "ICH9-LPC.acpi-pci-hotplug-with-bridge-support=off" in unido
    # Sin keymap del host que desalinee el menu de OpenCore.
    assert "keymap=" not in unido


def test_macos_bajo_kvm_conserva_perfil_kvm(tmp_path, monkeypatch):
    import services.vm_runner as vr

    monkeypatch.setattr(vr, "IS_WINDOWS", False)
    host = types.SimpleNamespace(
        qemu_path="/usr/bin/qemu-system-x86_64",
        acceleration="kvm",
        get_accel_args=lambda: ["-accel", "kvm"],
    )
    runner = vr.VMRunner(host, tmp_path, tmp_path / "vms")
    runner._find_free_vnc_port = lambda exclude=None: 5901
    proyecto = tmp_path / "OSX-KVM" / "OpenCore"
    proyecto.mkdir(parents=True)
    (proyecto / "OpenCore.qcow2").write_bytes(b"oc")

    vm = {"id": "mac1", "name": "macOS", "platform": "macOS",
          "version": "Sonoma", "ram": 4096, "cores": 4,
          "disk_path": str(tmp_path / "mac.qcow2")}
    cmd = " ".join(str(x) for x in runner.build_command(vm))

    assert "kvm=on" in cmd
    assert "vendor=GenuineIntel" in cmd
    assert "vmware-cpuid-freq=on" in cmd
    assert "+invtsc" not in cmd
    assert "qemu64" not in cmd
    assert "VGA,vgamem_mb=" in cmd
    assert "vmware-svga" not in cmd


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
    assert "tags: ['v*']" in workflow
    assert "softprops/action-gh-release@v2" in workflow


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


def test_vnc_teclado_windows_usa_keysyms_clasicos(qapp, monkeypatch):
    import vnc_widget.qvncwidget as qv

    monkeypatch.setattr(qv.platform, "system", lambda: "Windows")
    widget = qv.QVNCWidget(None, host="127.0.0.1", port=5900)
    widget.ext_key_event_supported = True
    enviados = []
    widget.extKeyEvent = lambda *args: enviados.append(("ext", args))
    widget.keyEvent = lambda sym, down=1: enviados.append(("key", sym, down))

    class Tecla:
        def key(self): return 0

        def text(self): return "a"

        def nativeScanCode(self): return 30

    widget._send_key(Tecla(), 1)
    widget._vnc_keepalive_timer.stop()

    assert enviados == [("key", ord("a"), 1)]


def test_vnc_teclado_linux_usa_keysyms_clasicos(qapp, monkeypatch):
    """ Restaurado de main @ 2c7748f: el puerto a Windows anadio Extended
    Key Event con keycodes evdev que rompen el menu de OpenCore en macOS. """
    import vnc_widget.qvncwidget as qv

    monkeypatch.setattr(qv.platform, "system", lambda: "Linux")
    widget = qv.QVNCWidget(None, host="127.0.0.1", port=5900)
    widget.ext_key_event_supported = True
    enviados = []
    widget.extKeyEvent = lambda *args: enviados.append(("ext", args))
    widget.keyEvent = lambda sym, down=1: enviados.append(("key", sym, down))

    class Tecla:
        def key(self): return 0

        def text(self): return "a"

        def nativeScanCode(self): return 30  # X11: evdev(22) + 8

    widget._send_key(Tecla(), 1)
    widget._vnc_keepalive_timer.stop()

    assert enviados == [("key", ord("a"), 1)]


def test_scan_usb_windows_extrae_vid_pid_con_nombre_amigable(monkeypatch):
    import plugins.config_vm.plugin as cp

    salida = json.dumps([
        {
            "Name": "USB Mass Storage Device", "Class": "USB", "Status": "OK",
            "InstanceId": r"USB\VID_0781&PID_5583\12345",
        },
        {
            "Name": "USB Root Hub", "Class": "USB", "Status": "OK",
            "InstanceId": r"USB\ROOT_HUB30\1",
        },
    ])
    comandos = []

    def fake_run(cmd, **kwargs):
        comandos.append(cmd)
        return types.SimpleNamespace(returncode=0, stdout=salida, stderr="")

    monkeypatch.setattr(cp, "IS_WINDOWS", True)
    monkeypatch.setattr(cp.subprocess, "run", fake_run)

    devices = cp.scan_usb_devices()

    assert len(devices) == 1
    assert devices[0]["id"] == "0781:5583"
    assert devices[0]["vid_did"] == "0781:5583"
    assert devices[0]["mode"] == "vidpid"
    assert devices[0]["desc"] == "💾 Almacenamiento SanDisk (0781:5583)"
    assert "USB Mass Storage Device" in devices[0]["detalle"]
    assert any("Get-PnpDevice" in parte for parte in comandos[0])


def test_scan_usb_windows_agrupa_nodos_hij_y_usa_categoria(monkeypatch):
    import plugins.config_vm.plugin as cp

    salida = json.dumps([
        {
            "Name": "HID Keyboard Device", "Class": "Keyboard", "Status": "OK",
            "InstanceId": r"HID\VID_0458&PID_6001&MI_00\7&1",
        },
        {
            "Name": "HID-compliant mouse", "Class": "Mouse", "Status": "OK",
            "InstanceId": r"HID\VID_0458&PID_6001&MI_01\7&2",
        },
        {
            "Name": "HP Integrated Webcam", "Class": "Camera", "Status": "OK",
            "InstanceId": r"USB\VID_05C8&PID_0230&MI_00\6&3",
        },
        {
            "Name": "USB Composite Device", "Class": "USB", "Status": "OK",
            "InstanceId": r"USB\VID_05C8&PID_0230\200901010001",
        },
    ])
    monkeypatch.setattr(cp, "IS_WINDOWS", True)
    monkeypatch.setattr(cp.subprocess, "run",
                        lambda *a, **k: types.SimpleNamespace(
                            returncode=0, stdout=salida, stderr=""))

    devices = cp.scan_usb_devices()

    assert len(devices) == 2  # los 4 nodos PnP son solo 2 USB físicos
    por_id = {d["id"]: d for d in devices}
    assert por_id["0458:6001"]["desc"] == "⌨️🖱️ Teclado y ratón Genius (0458:6001)"
    assert "HID Keyboard Device" in por_id["0458:6001"]["detalle"]
    assert "HID-compliant mouse" in por_id["0458:6001"]["detalle"]
    assert por_id["05C8:0230"]["desc"] == (
        "📷 Cámara · HP Integrated Webcam (05C8:0230)")


def test_hotplug_dialog_windows_conecta_y_desconecta_por_vid_pid(qapp, monkeypatch):
    import ui_widgets.hotplug_dialog as hd

    monkeypatch.setattr(hd.os, "name", "nt")
    monkeypatch.setattr(hd, "scan_usb_devices", lambda: [{
        "id": "0781:5583",
        "desc": "Pendrive [0781:5583]",
        "mode": "vidpid",
    }])
    llamadas = []

    class Runner:
        def get_connected_usb_devices(self, vm_id):
            return []

        def hotplug_usb_vid_pid(self, vm_id, vid, pid):
            llamadas.append(("connect", vid, pid))
            return True, "USB conectado."

        def remove_usb_by_id(self, vm_id, usb_id):
            llamadas.append(("disconnect", usb_id))
            return True, "USB desconectado."

    app = types.SimpleNamespace(
        get_vm=lambda vm_id: {"id": vm_id, "optical_drives": []},
        runner=Runner(),
    )
    monkeypatch.setattr(hd.QMessageBox, "information",
                        staticmethod(lambda *a, **k: None))
    dlg = hd.HotplugDialog(app, "vm1")
    dlg.list_usb.setCurrentRow(0)

    dlg._connect_usb()
    dlg._disconnect_usb()

    assert llamadas == [
        ("connect", "0781", "5583"),
        ("disconnect", "usb_0781_5583"),
    ]


def test_resolucion_inicial_detecta_monitores_del_host(qapp, monkeypatch):
    from PyQt6.QtCore import QSize

    import plugins.config_vm.plugin as cp

    class Geometry:
        def __init__(self, ancho, alto):
            self._size = QSize(ancho, alto)

        def size(self):
            return self._size

    class Screen:
        def __init__(self, ancho, alto):
            self._geo = Geometry(ancho, alto)

        def geometry(self):
            return self._geo

        def availableGeometry(self):
            return self._geo

    monkeypatch.setattr(
        cp.QGuiApplication, "screens",
        staticmethod(lambda: [Screen(1366, 768), Screen(1920, 1080)]),
    )

    resoluciones = cp._host_resolutions()

    assert [tam for tam, _ in resoluciones] == [(1920, 1080), (1366, 768)]
    assert resoluciones[0][1] == "1920×1080 (monitor 2)"
    assert resoluciones[1][1] == "1366×768 (monitor 1)"
