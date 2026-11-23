"""Fase D: host macOS Intel (HVF, rutas Homebrew y diagnóstico honesto).

Los tests fuerzan las constantes de plataforma con monkeypatch para poder
validar las ramas macOS desde Linux/Windows. No se toca ninguna configuración
real ni se lanza QEMU.
"""

import sys
import types
from pathlib import Path

from PyQt6.QtWidgets import QLabel

ROOT = Path(__file__).resolve().parents[1]


def _host(ha, qemu="/usr/local/bin/qemu-system-x86_64"):
    host = object.__new__(ha.HostAdapter)
    host.qemu_path = qemu
    host.qemu_img_path = "/usr/local/bin/qemu-img"
    host.is_windows = False
    host.is_mac = True
    return host


# ----------------------------------------------------------------------
# Aceleración HVF
# ----------------------------------------------------------------------

def test_detecta_hvf_en_macos(monkeypatch):
    import services.host_adapter as ha

    monkeypatch.setattr(ha, "IS_WINDOWS", False)
    monkeypatch.setattr(ha, "IS_MAC", True)
    monkeypatch.setattr(ha, "qemu_accepts_accel",
                        lambda ruta, accel: accel == "hvf")

    assert _host(ha)._detect_acceleration() == "hvf"


def test_sin_hvf_cae_a_tcg_en_macos(monkeypatch):
    import services.host_adapter as ha

    monkeypatch.setattr(ha, "IS_WINDOWS", False)
    monkeypatch.setattr(ha, "IS_MAC", True)
    monkeypatch.setattr(ha, "qemu_accepts_accel", lambda ruta, accel: False)

    assert _host(ha)._detect_acceleration() == "tcg"


def test_argumentos_de_aceleracion_hvf(monkeypatch):
    import services.host_adapter as ha

    host = _host(ha)
    host.acceleration = "hvf"
    assert host.get_accel_args() == ["-accel", "hvf"]
    assert host.get_status()["is_mac"] is True


def test_aviso_de_consola_en_macos_habla_de_hvf(qapp, app_ctx):
    from plugins.console.plugin import Plugin

    app_ctx.host.acceleration = "tcg"
    app_ctx.host.is_windows = False
    app_ctx.host.is_mac = True

    _, widget = Plugin(app_ctx).get_tabs()[0]
    avisos = [l.text() for l in widget.findChildren(QLabel) if "TCG" in l.text()]
    assert len(avisos) == 1
    assert "HVF" in avisos[0]
    assert "brew install qemu" in avisos[0]
    assert "KVM" not in avisos[0]
    assert "WHPX" not in avisos[0]


# ----------------------------------------------------------------------
# Resolución de QEMU lanzado desde Finder (sin PATH de Terminal)
# ----------------------------------------------------------------------

def test_qemu_de_homebrew_se_encuentra_sin_path(tmp_path, monkeypatch):
    import services.qemu_paths as qp

    binario = tmp_path / "qemu-system-x86_64"
    binario.write_text("")

    monkeypatch.setattr(qp, "IS_WINDOWS", False)
    monkeypatch.setattr(qp, "IS_MAC", True)
    monkeypatch.setattr(qp, "_dir_override", str(tmp_path))
    monkeypatch.setattr(qp.shutil, "which", lambda nombre: None)

    assert qp.find_qemu_binary("qemu-system-x86_64") == str(binario)


def test_linux_no_usa_el_directorio_configurado(monkeypatch):
    """La rama macOS no debe filtrarse en Linux."""
    import services.qemu_paths as qp

    monkeypatch.setattr(qp, "IS_WINDOWS", False)
    monkeypatch.setattr(qp, "IS_MAC", False)
    monkeypatch.setattr(qp, "_dir_override", "/ruta/Que/no/existe")
    monkeypatch.setattr(qp.shutil, "which", lambda nombre: None)

    assert qp.find_qemu_binary("qemu-system-x86_64") is None


# ----------------------------------------------------------------------
# RAM del host y semáforo
# ----------------------------------------------------------------------

def test_ram_de_macos_viene_de_psutil(monkeypatch):
    import services.host_profile as hp

    monkeypatch.setattr(hp, "IS_WINDOWS", False)
    monkeypatch.setattr(hp, "IS_MAC", True)
    modulo_psutil = types.ModuleType("psutil")
    modulo_psutil.virtual_memory = lambda: types.SimpleNamespace(total=4096 * 1024 * 1024)
    monkeypatch.setitem(sys.modules, "psutil", modulo_psutil)

    perfil = hp.HostProfile()
    assert perfil.total_ram_mb == 4096


# ----------------------------------------------------------------------
# Diagnóstico
# ----------------------------------------------------------------------

def test_diagnostico_macos_no_muestra_whpx_ni_zadig(monkeypatch):
    import services.host_diagnostics as hd

    monkeypatch.setattr(hd, "IS_WINDOWS", False)
    monkeypatch.setattr(hd, "IS_LINUX", False)
    monkeypatch.setattr(hd, "IS_MAC", True)
    monkeypatch.setattr(hd, "find_qemu_binary",
                        lambda nombre: "/usr/local/bin/qemu-system-x86_64")
    monkeypatch.setattr(hd, "_macos_accel_status",
                        lambda ruta: ("ok", "HVF disponible"))
    monkeypatch.setattr(hd, "qemu_supports_tpm", lambda ruta: False)
    monkeypatch.setattr(hd, "check_fido", lambda: ("ok", "Fido.ps1"))
    monkeypatch.setattr(hd.shutil, "which", lambda nombre: None)

    checks = hd.HostDiagnostics().run_all()
    textos = [f"{c['name']} {c['desc']}" for c in checks]

    assert any("HVF" in texto for texto in textos)
    assert not any("WHPX" in texto for texto in textos)
    assert not any("Zadig" in texto for texto in textos)
    assert not any("no disponible en Windows" in texto for texto in textos)
    assert not any("UAC" in texto for texto in textos)


# ----------------------------------------------------------------------
# Runner: CPU y firmware bajo HVF
# ----------------------------------------------------------------------

def test_cpu_de_macos_guest_bajo_hvf_sin_flag_de_kvm():
    from services.vm_runner import VMRunner

    runner = object.__new__(VMRunner)
    runner.host = types.SimpleNamespace(acceleration="hvf")

    assert runner._build_macos_cpu_args({"cpu_type_idx": 1}) == ["host"]
    assert runner._build_macos_cpu_args({"cpu_model": "Penryn"}) == ["Penryn"]


def test_firmware_de_homebrew_se_usa_en_hvf(tmp_path, monkeypatch):
    from services.vm_runner import VMRunner
    import services.vm_runner as vr

    firmware = tmp_path / "share" / "qemu"
    firmware.mkdir(parents=True)
    code = firmware / "edk2-x86_64-code.fd"
    vars_fd = firmware / "edk2-i386-vars.fd"
    code.write_bytes(b"x" * (2 * 1024 * 1024))
    vars_fd.write_bytes(b"x" * (128 * 1024))

    monkeypatch.setattr(vr, "IS_MAC", True)
    monkeypatch.setattr(vr, "IS_LINUX", False)
    monkeypatch.setattr(vr, "OVMF_MACOS_DIRS", (str(firmware),))
    # Evitar que el OSX-KVM del repo (OVMF_CODE_4M.fd) gane en el orden de
    # búsqueda: simulamos que el módulo vive bajo tmp_path.
    monkeypatch.setattr(vr, "__file__", str(tmp_path / "services" / "vm_runner.py"))

    runner = object.__new__(VMRunner)
    runner.host = types.SimpleNamespace(qemu_path=None)
    runner.data_dir = tmp_path / "datos"

    assert runner._find_ovmf() == (str(code), str(vars_fd))


# ----------------------------------------------------------------------
# Empaquetado y CI
# ----------------------------------------------------------------------

def test_spec_genera_bundle_en_macos():
    spec = (ROOT / "virtualmachine.spec").read_text(encoding="utf-8")
    assert "es_macos = sys.platform == \"darwin\"" in spec
    assert "BUNDLE(" in spec
    assert "CFBundleName" in spec


def test_ci_prueba_macos_intel():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "macos-15-intel" in workflow
    assert "build-macos:" in workflow


def test_ayuda_y_guia_cubren_macos():
    from plugins.help.plugin import TOPICS

    cuerpo = dict((clave, html) for clave, _titulo, html in TOPICS)["requisitos"]
    assert "macOS Intel" in cuerpo
    assert "HVF" in cuerpo

    guia = (ROOT / "INSTALL_MAC.md").read_text(encoding="utf-8")
    assert "brew install qemu" in guia
    assert "Hypervisor.framework" in guia
    assert "clic derecho" in guia
