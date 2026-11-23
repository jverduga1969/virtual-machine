"""Consola y teclado de las VMs macOS."""

import types

import services.vm_runner as vr


class FakeHost:
    qemu_path = "/usr/bin/qemu-system-x86_64"
    acceleration = "kvm"
    is_windows = False

    def get_accel_args(self):
        return ["-accel", "kvm"]


def _command(vm, tmp_path, monkeypatch):
    runner = vr.VMRunner(FakeHost(), tmp_path, tmp_path)
    monkeypatch.setattr(runner, "_find_free_hostfwd_port", lambda start=2222, attempts=200: 2222)
    monkeypatch.setattr(runner, "_find_free_vnc_port", lambda exclude=None: 5900)
    monkeypatch.setattr(runner, "_vnc_target", lambda port, head=None: f"127.0.0.1:{port - 5900}")
    monkeypatch.setattr(runner, "_find_free_port", lambda start=5930, end=6000, exclude=None: start)
    monkeypatch.setattr(runner, "_get_tmp_socket_path",
                        lambda vid, prefix="qemu": str(tmp_path / f"{prefix}-{vid}.sock"))
    monkeypatch.setattr(runner, "_get_qmp_socket_path", lambda vid: str(tmp_path / "qmp.sock"))
    return runner.build_command(vm)


def _vm(**kwargs):
    vm = {"id": "mac-test", "name": "macOS", "platform": "macOS"}
    vm.update(kwargs)
    return vm


def test_graficos_macos_usan_vga_osxkvm(tmp_path, monkeypatch):
    """ Sin eleccion explicita, macOS usa la VGA de OSX-KVM (recomendada). """
    cmd = _command(_vm(), tmp_path, monkeypatch)
    assert any(a.startswith("VGA,vgamem_mb=") for a in cmd)
    assert "-vga" not in cmd
    assert "vmware-svga" not in cmd


def test_graficos_macos_respeta_dispositivo_experimental(tmp_path, monkeypatch):
    """ La UI permite elegir otros devices; el runner respeta la eleccion. """
    casos = {
        0: "virtio-vga", 1: "virtio-vga", 2: "virtio-vga", 3: "virtio-vga",
        4: "qxl-vga", 5: "vmware-svga,vgamem_mb=128",
        6: "VGA,vgamem_mb=128", 7: "VGA,vgamem_mb=128",
    }
    for idx, esperado in casos.items():
        cmd = _command(_vm(graphics_idx=idx), tmp_path, monkeypatch)
        assert any(a.startswith(esperado) for a in cmd), (idx, cmd)


def test_cpu_macos_automatico_no_cuelga_en_la_manzana(tmp_path, monkeypatch):
    """ main @ 2c7748f: Penryn + vmware-cpuid-freq, sin +invtsc/qemu64. """
    cmd = _command(_vm(version="Sonoma (14)"), tmp_path, monkeypatch)
    cpu = " ".join(cmd)
    assert "Penryn,kvm=on,vendor=GenuineIntel,vmware-cpuid-freq=on" in cpu
    assert "qemu64" not in cpu
    assert "+invtsc" not in cpu


def test_vram_macos_minimo_128mb(tmp_path, monkeypatch):
    """ OpenCore necesita al menos 128 MB de VRAM. """
    cmd = _command(_vm(vram_idx=0), tmp_path, monkeypatch)
    assert "VGA,vgamem_mb=128" in cmd


def test_resolucion_inicial_del_monitor_se_aplica_a_la_vga(tmp_path, monkeypatch):
    """El campo de la UI (resoluciones reales del host) llega a macOS."""
    cmd = _command(_vm(initial_resolution="3840x2160"), tmp_path, monkeypatch)
    assert "VGA,vgamem_mb=128,xres=3840,yres=2160" in cmd


def test_1600x900_se_pasa_tal_cual(tmp_path, monkeypatch):
    """Sin conversiones silenciosas: lo elegido es lo que recibe QEMU."""
    cmd = _command(_vm(initial_resolution="1600x900"), tmp_path, monkeypatch)
    assert "VGA,vgamem_mb=128,xres=1600,yres=900" in cmd


def test_2560x1440_se_pasa_tal_cual(tmp_path, monkeypatch):
    """2560x1440 es el modo natural del iMac19,1 que emula OpenCore."""
    cmd = _command(_vm(initial_resolution="2560x1440"), tmp_path, monkeypatch)
    assert "VGA,vgamem_mb=128,xres=2560,yres=1440" in cmd


def test_resolucion_inicial_invalida_no_anade_xres(tmp_path, monkeypatch):
    cmd = _command(_vm(initial_resolution="no-valida"), tmp_path, monkeypatch)
    unido = " ".join(cmd)
    assert "VGA,vgamem_mb=128" in unido
    assert "xres=" not in unido
    assert "yres=" not in unido


def test_teclado_macos_va_en_ehci(tmp_path, monkeypatch):
    """ Restaurado de main @ 2c7748f: macOS/OpenCore necesita EHCI. """
    cmd = _command(_vm(), tmp_path, monkeypatch)
    assert "usb-kbd,bus=ehci.0" in cmd
    assert "usb-tablet,bus=ehci.0" in cmd
    assert "usb-ehci,id=ehci" in cmd
    assert "qemu-xhci,id=xhci" not in cmd


def test_spice_en_macos_usa_spice_real_y_sin_vdagent(tmp_path, monkeypatch):
    """SPICE transporta VGA estandar sin driver QXL (manual oficial).

    Pero macOS no tiene spice-vdagent: no se debe crear el canal de
    portapapeles com.redhat.spice.0.
    """
    vm = _vm(console_proto_idx=1, console_mode_idx=1)
    cmd = _command(vm, tmp_path, monkeypatch)
    unido = " ".join(cmd)
    assert "-spice" in unido
    assert "-vnc" not in unido
    assert "com.redhat.spice.0" not in unido
    assert "-display" in cmd and cmd[cmd.index("-display") + 1] == "none"
    assert vm["_pending_external_viewer"]["type"] == "spice_unix"
    assert vm["_pending_external_viewer"]["head"] == 0


def test_spice_remoto_en_macos(tmp_path, monkeypatch):
    vm = _vm(console_proto_idx=2, console_mode_idx=1)
    cmd = _command(vm, tmp_path, monkeypatch)
    assert "-spice" in cmd
    assert vm["_pending_external_viewer"]["type"] == "spice_remote"


def test_carpetas_compartidas_en_macos_van_por_smb(tmp_path, monkeypatch):
    """9p/VirtioFS no tienen driver en macOS: solo SMB es factible."""
    shared = tmp_path / "share"
    shared.mkdir()
    vm = _vm(shared_folders=[{"host": str(shared), "guest": "docs",
                              "method": "9p", "mount": "Manual", "ro": False}],
             guest_agent=True)
    monkeypatch.setattr(vr.shutil, "which", lambda name: "/usr/sbin/smbd" if name == "smbd" else None)
    cmd = _command(vm, tmp_path, monkeypatch)
    unido = " ".join(cmd)
    assert f"smb={shared}" in unido
    assert "e1000-82545em,netdev=smb0" in unido
    assert "virtio-9p-pci" not in unido
    assert "vhost-user-fs-pci" not in unido
    assert "org.qemu.guest_agent.0" not in unido


def test_sin_smbd_la_carpeta_se_omite_sin_romper_qemu(tmp_path, monkeypatch):
    """QEMU no arranca si smbd no existe: se omite la carpeta con aviso."""
    shared = tmp_path / "share"
    shared.mkdir()
    vm = _vm(shared_folders=[{"host": str(shared), "guest": "docs",
                              "method": "SMB", "mount": "Manual", "ro": False}])
    monkeypatch.setattr(vr.shutil, "which", lambda name: None)
    cmd = _command(vm, tmp_path, monkeypatch)
    unido = " ".join(cmd)
    assert "smb=" not in unido
    assert "-vnc" in unido  # la VM sigue arrancando con normalidad


def test_hibrida_en_macos_tambien_levanta_visor_externo(tmp_path, monkeypatch):
    """Hibrida = VNC embebido + SPICE en remote-viewer (tambien en macOS)."""
    vm = _vm(console_proto_idx=0, console_mode_idx=2)
    cmd = _command(vm, tmp_path, monkeypatch)
    assert "-vnc" in cmd
    assert "-spice" in cmd
    assert vm["_pending_external_viewer"]["type"] == "spice_unix"


def test_vnc_embedida_no_lanza_visor(tmp_path, monkeypatch):
    vm = _vm(console_proto_idx=0, console_mode_idx=0)
    cmd = _command(vm, tmp_path, monkeypatch)
    assert "-vnc" in cmd
    assert vm["_pending_external_viewer"] is None
    assert "-display" not in cmd


def test_pantalla_completa_sdl_en_macos(tmp_path, monkeypatch):
    vm = _vm(console_proto_idx=0, console_mode_idx=4)
    cmd = _command(vm, tmp_path, monkeypatch)
    assert ["-display", "sdl,full-screen=on"] == cmd[cmd.index("-display"):cmd.index("-display") + 2]
    assert vm["_pending_external_viewer"] is None


def test_campos_none_de_vms_json_antiguas_se_normalizan(tmp_path, monkeypatch):
    """ Las VMs creadas antes de estos campos tienen None, no 0. """
    vm = _vm(console_proto_idx=None, console_mode_idx=None)
    cmd = _command(vm, tmp_path, monkeypatch)
    assert "-vnc" in cmd
    assert vm["_pending_external_viewer"] is None
    assert "-display" not in cmd


def test_modo_externo_con_proto_none_levanta_visor(tmp_path, monkeypatch):
    vm = _vm(console_proto_idx=None, console_mode_idx=1)
    _command(vm, tmp_path, monkeypatch)
    assert vm["_pending_external_viewer"] == {"type": "vnc", "port": 5900}


def test_foco_del_visor_se_reclama(qapp, app_ctx, monkeypatch):
    import plugins.console.plugin as cp

    focos = []
    monkeypatch.setattr(cp.QTimer, "singleShot",
                        staticmethod(lambda ms, cb: cb()))
    plugin = cp.Plugin(app_ctx)
    plugin.vnc_widget = types.SimpleNamespace(
        setFocus=lambda reason: focos.append(reason))

    plugin._focus_vnc_widget()

    assert len(focos) == 1
