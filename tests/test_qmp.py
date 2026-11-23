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
    # La validación va antes de makedirs: no debe crear ningún directorio.
    assert list(tmp_path.iterdir()) == []


def test_pause_y_resume_devuelven_si_qmp_acepto(runner, monkeypatch):
    class Proc:
        def poll(self): return None

        def send_signal(self, sig): raise AssertionError("no debe haber fallback")

    runner.active_processes["vm1"] = Proc()
    respuestas = [{"return": {}}, {"error": {"desc": "no"}}]
    monkeypatch.setattr(runner, "_qmp_call", lambda *a, **k: respuestas.pop(0))

    assert runner.pause_vm("vm1") is True
    assert runner.resume_vm("vm1") is False


def test_monitor_processo_avisa_de_apagado_del_invitado(runner, monkeypatch):
    class Proc:
        def wait(self): return 0

    proc = Proc()
    runner.active_processes["vm1"] = proc
    runner._qmp_sockets["vm1"] = "tcp:127.0.0.1:4444"
    vistos = []
    runner.on_process_finished = lambda vid, code: vistos.append((vid, code))
    limpiezas = []
    monkeypatch.setattr(runner, "_kill_external_viewer",
                        lambda vid: limpiezas.append(("viewer", vid)))
    monkeypatch.setattr(runner, "_kill_virtiofsd",
                        lambda vid: limpiezas.append(("virtiofsd", vid)))
    monkeypatch.setattr(runner, "_cleanup_gvtg_vgpu",
                        lambda vid: limpiezas.append(("gvtg", vid)))

    runner._monitor_process("vm1", proc)

    assert vistos == [("vm1", 0)]
    assert "vm1" not in runner.active_processes
    assert "vm1" not in runner._qmp_sockets
    assert [nombre for nombre, _ in limpiezas] == ["viewer", "virtiofsd", "gvtg"]


def test_monitor_antiguo_no_apaga_la_vm_reiniciada(runner, monkeypatch):
    nuevo = object()

    class ProcViejo:
        def wait(self):
            runner.active_processes["vm1"] = nuevo
            return 0

    viejo = ProcViejo()
    runner.active_processes["vm1"] = viejo
    avisos = []
    runner.on_process_finished = lambda vid, code: avisos.append((vid, code))
    monkeypatch.setattr(runner, "_kill_external_viewer", lambda vid: pytest.fail("nueva VM"))
    monkeypatch.setattr(runner, "_kill_virtiofsd", lambda vid: None)
    monkeypatch.setattr(runner, "_cleanup_gvtg_vgpu", lambda vid: None)

    runner._monitor_process("vm1", viejo)

    assert avisos == []
    assert runner.active_processes["vm1"] is nuevo


def test_hotplug_usb_windows_usa_vendorid_y_productid(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_get_qmp_socket_path",
                        lambda vm_id: "tcp:127.0.0.1:4444")
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(vr.time, "sleep", lambda *_: None)
    llamadas = []

    def fake_call(sock, comando, argumentos=None):
        llamadas.append((comando, argumentos))
        if comando == "qom-list" and argumentos.get("path") == "/machine/peripheral":
            return {"return": [{"name": "xhci"}]}
        return {"return": []}

    monkeypatch.setattr(runner, "_qmp_call", fake_call)

    ok, msg = runner.hotplug_usb_vid_pid("vm1", "0781", "5583")

    assert ok is True
    assert msg == "USB conectado."
    device_add = [args for cmd, args in llamadas if cmd == "device_add"]
    assert device_add == [{
        "driver": "usb-host",
        "id": "usb_0781_5583",
        "bus": "xhci.0",
        "vendorid": 0x0781,
        "productid": 0x5583,
    }]


def test_hotplug_usb_windows_avisa_si_no_hay_xhci(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_get_qmp_socket_path",
                        lambda vm_id: "tcp:127.0.0.1:4444")
    runner.active_processes["vm1"] = object()
    monkeypatch.setattr(runner, "_qmp_call",
                        lambda *a, **k: {"return": [{"name": "virtio0"}]})

    ok, msg = runner.hotplug_usb_vid_pid("vm1", "0781", "5583")

    assert ok is False
    assert "XHCI" in msg


def test_hotplug_usb_windows_da_pista_de_zadig_si_libusb_falla(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_get_qmp_socket_path",
                        lambda vm_id: "tcp:127.0.0.1:4444")
    runner.active_processes["vm1"] = object()

    def fake_call(sock, comando, argumentos=None):
        if comando == "qom-list" and argumentos.get("path") == "/machine/peripheral":
            return {"return": [{"name": "xhci"}]}
        if comando == "device_add":
            return {"error": {"desc": "usb-host: failed to open device (libusb)"}}
        return {"return": {}}

    monkeypatch.setattr(runner, "_qmp_call", fake_call)

    ok, msg = runner.hotplug_usb_vid_pid("vm1", "0781", "5583")

    assert ok is False
    assert "Zadig" in msg
    assert "WinUSB" in msg


def test_hotplug_usb_windows_requiere_vm_encendida(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_qmp_call",
                        lambda *a, **k: pytest.fail("no debe hablar con QMP"))

    ok, msg = runner.hotplug_usb_vid_pid("vm1", "0781", "5583")

    assert ok is False
    assert msg == "La VM no está en ejecución."


def test_remove_usb_by_id_envia_device_del(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_get_qmp_socket_path",
                        lambda vm_id: "tcp:127.0.0.1:4444")
    runner.active_processes["vm1"] = object()
    vistos = []

    def fake_call(sock, comando, argumentos=None):
        vistos.append((comando, argumentos))
        if comando == "device_del":
            return {"return": {}}
        return {"return": []}

    monkeypatch.setattr(runner, "_qmp_call", fake_call)

    ok, msg = runner.remove_usb_by_id("vm1", "usb_0781_5583")

    assert ok is True
    assert ("device_del", {"id": "usb_0781_5583"}) in vistos


def test_resolucion_inicial_virtio_pasa_xres_yres(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)

    args = runner._build_graphics_device_args({
        "graphics_idx": 0, "console_proto_idx": 1, "console_mode_idx": 1,
        "initial_resolution": "1920x1080",
    })

    assert args[:2] == ["-device", "virtio-vga,xres=1920,yres=1080"]
    assert not any("virtio-vga.xres=" in a for a in args)
    assert args[-2:] == ["-display", "none"]


def test_resolucion_inicial_qxl_pasa_xres_yres(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)

    args = runner._build_graphics_device_args({
        "graphics_idx": 4, "vram_idx": 1,
        "console_proto_idx": 1, "console_mode_idx": 1,
        "initial_resolution": "2560×1440",
    })

    assert "qxl-vga.vgamem_mb=128" in args
    assert "qxl-vga.xres=2560" in args
    assert "qxl-vga.yres=1440" in args


def test_resolucion_inicial_invalida_no_anade_nada(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)

    args = runner._build_graphics_device_args({
        "graphics_idx": 1, "console_proto_idx": 0, "console_mode_idx": 0,
        "initial_resolution": "no-valido",
    })

    assert not any("xres" in arg or "yres" in arg for arg in args)


def test_resolucion_inicial_en_gpu_3d_va_en_el_device(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)

    args = runner._build_graphics_device_args({
        "graphics_idx": 2, "console_proto_idx": 1, "console_mode_idx": 1,
        "initial_resolution": "3840x2160",
    })

    assert "virtio-vga-gl,xres=3840,yres=2160" in args


def test_varios_monitores_virtio_anade_max_outputs(runner):
    args = runner._build_graphics_device_args({
        "graphics_idx": 0, "console_proto_idx": 0, "console_mode_idx": 0,
        "monitor_count": 3,
    })

    assert args[0:2] == ["-device", "virtio-vga,max_outputs=3"]


def test_varios_monitores_qxl_anade_max_outputs(runner):
    args = runner._build_graphics_device_args({
        "graphics_idx": 4, "vram_idx": 1,
        "console_proto_idx": 1, "console_mode_idx": 0,
        "monitor_count": 2,
    })

    assert "qxl-vga.max_outputs=2" in args
    assert "qxl-vga.vgamem_mb=128" in args


def test_un_monitor_no_anade_max_outputs(runner):
    args = runner._build_graphics_device_args({
        "graphics_idx": 0, "console_proto_idx": 0, "console_mode_idx": 0,
        "monitor_count": 1,
    })

    assert args[:2] == ["-device", "virtio-vga"]
    assert not any("max_outputs" in arg for arg in args)


def test_vnc_no_hace_probe_de_qemu_ni_anade_keymap(runner, monkeypatch):
    """El layout del host nunca se usa y no se paga un timeout=3 en Windows."""
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    llamadas = []
    monkeypatch.setattr(vr.subprocess, "run",
                        lambda *a, **k: llamadas.append((a, k)))
    monkeypatch.setattr(runner, "_find_free_vnc_port", lambda exclude=None: 5900)

    vm = {"id": "vm1", "console_proto_idx": 0, "console_mode_idx": 0,
          "share_clipboard": False}
    args, _ = runner._build_display_protocol_args(vm)

    assert "127.0.0.1:0,head=0" in args
    assert not any("keymap=" in arg for arg in args)
    assert llamadas == []


def test_start_vm_no_espera_el_sleep_fijo_de_2_5s(runner, monkeypatch):
    """La consola aparece en cuanto QEMU publica el puerto, no a los 2,5 s."""
    class _Proc:
        stdout = None

        def poll(self):
            return None

    class _Hilo:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

    runner.active_viewers = {}
    runner._active_viewer_info = {}
    runner.on_process_finished = lambda *a: None
    monkeypatch.setattr(runner, "build_command", lambda vm: ["qemu"])
    monkeypatch.setattr(vr.subprocess, "Popen", lambda *a, **k: _Proc())
    monkeypatch.setattr(vr.threading, "Thread", _Hilo)
    monkeypatch.setattr(runner, "_tcp_port_open", lambda port: True)

    dormidos = []
    sleep_real = vr.time.sleep
    monkeypatch.setattr(vr.time, "sleep", lambda s: dormidos.append(s) or sleep_real(s))

    runner.start_vm({"id": "rapido", "vnc_port": 5900})
    assert all(s < 1 for s in dormidos), dormidos


def test_varios_monitores_vnc_crea_un_puerto_por_head(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", False)
    puertos = iter([5900, 5901, 5902])
    monkeypatch.setattr(runner, "_find_free_vnc_port",
                        lambda exclude=None: next(puertos))

    vm = {"id": "vm1", "console_proto_idx": 0, "console_mode_idx": 0,
          "monitor_count": 3, "share_clipboard": False}
    args, info = runner._build_display_protocol_args(vm)

    assert [a for a in args if a == "-vnc"] == ["-vnc"] * 3
    assert "127.0.0.1:0,head=0" in args
    assert "127.0.0.1:1,head=1" in args
    assert "127.0.0.1:2,head=2" in args
    assert vm["vnc_port"] == 5900
    assert vm["vnc_heads"] == {"head_0": 5900, "head_1": 5901, "head_2": 5902}
    assert info is None


def test_vnc_ventana_externa_abre_un_visor_por_monitor(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    puertos = iter([5900, 5901])
    monkeypatch.setattr(runner, "_find_free_vnc_port",
                        lambda exclude=None: next(puertos))

    vm = {"id": "vm1", "name": "Mint", "console_proto_idx": 0,
          "console_mode_idx": 1, "monitor_count": 2, "share_clipboard": False}
    args, info = runner._build_display_protocol_args(vm)

    assert args.count("-vnc") == 2
    assert info["type"] == "multi"
    assert [h["port"] for h in info["heads"]] == [5900, 5901]
    assert [h["title"] for h in info["heads"]] == [
        "Mint · Monitor 1", "Mint · Monitor 2"]


def test_spice_multimonitor_convierte_tablet_en_usb_mouse(runner):
    args = runner._build_pointer_args({
        "pointer": "Automático (recomendado)",
        "console_proto_idx": 1, "console_mode_idx": 1, "monitor_count": 2,
    })

    assert "usb-mouse,bus=xhci.0" in args
    assert not any("tablet" in arg for arg in args)


def test_spice_multimonitor_convierte_virtio_tablet_en_usb_mouse(runner):
    args = runner._build_pointer_args({
        "pointer": "VirtIO Tablet",
        "console_proto_idx": 2, "console_mode_idx": 0, "monitor_count": 3,
    })

    assert "usb-mouse,bus=xhci.0" in args
    assert "virtio-tablet-pci" not in args


def test_spice_multimonitor_con_teclado_conserva_el_teclado(runner):
    args = runner._build_pointer_args({
        "pointer": "USB Keyboard + Tablet",
        "console_proto_idx": 1, "console_mode_idx": 2, "monitor_count": 2,
    })

    assert "usb-kbd,bus=xhci.0" in args
    assert "usb-mouse,bus=xhci.0" in args
    assert "usb-tablet,bus=xhci.0" not in args


def test_spice_multimonitor_no_toca_usb_mouse_ps2_ni_ninguno(runner):
    base = {"console_proto_idx": 1, "console_mode_idx": 0, "monitor_count": 2}

    assert "usb-mouse,bus=xhci.0" in runner._build_pointer_args(
        dict(base, pointer="USB Mouse"))
    assert runner._build_pointer_args(dict(base, pointer="PS/2")) == []
    assert runner._build_pointer_args(dict(base, pointer="Ninguno")) == []


def test_vnc_multimonitor_no_convierte_el_tablet(runner):
    args = runner._build_pointer_args({
        "pointer": "USB Tablet",
        "console_proto_idx": 0, "console_mode_idx": 0, "monitor_count": 4,
    })

    assert "usb-tablet,bus=xhci.0" in args
    assert "usb-mouse,bus=xhci.0" not in args


def test_un_monitor_spice_no_desactiva_el_raton_de_agente(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    monkeypatch.setattr(runner, "_find_free_port",
                        lambda start, end, exclude=None: 5930)

    args, info = runner._build_display_protocol_args({
        "id": "vm1", "console_proto_idx": 1, "console_mode_idx": 0,
        "monitor_count": 1, "share_clipboard": False,
    })

    assert "agent-mouse=off" not in args[args.index("-spice") + 1]
    assert info["type"] == "spice_tcp"


def test_varios_monitores_spice_crea_un_servidor_por_head(runner, monkeypatch):
    monkeypatch.setattr(vr, "IS_WINDOWS", True)
    puertos = iter([5930, 5931])
    monkeypatch.setattr(runner, "_find_free_port",
                        lambda start, end, exclude=None: next(puertos))

    vm = {"id": "vm1", "name": "Mint", "console_proto_idx": 1,
          "console_mode_idx": 0, "monitor_count": 2, "share_clipboard": False}
    args, info = runner._build_display_protocol_args(vm)

    assert args.count("-spice") == 2
    assert any("head=0" in a for a in args)
    assert any("head=1" in a for a in args)
    assert all("agent-mouse=off" in a for a in args if a.startswith("port="))
    assert info["type"] == "multi"
    assert [h["title"] for h in info["heads"]] == ["Mint · Monitor 1", "Mint · Monitor 2"]
