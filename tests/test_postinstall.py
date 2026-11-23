"""El postinstall de Linux cubre lo que Configuración Host comprueba."""

import os
import shutil
import subprocess

import pytest

from conftest import ROOT

SCRIPT = ROOT / "scripts" / "postinstall.sh"
SCRIPT_WIN = ROOT / "scripts" / "postinstall.ps1"
PLUGIN = ROOT / "plugins" / "host_config" / "plugin.py"
DIAG = ROOT / "services" / "host_diagnostics.py"
PASSTHROUGH = ROOT / "services" / "host_passthrough.py"


def test_script_valido_y_sin_restos_del_antiguo_modo_kiosco():
    texto = SCRIPT.read_text(encoding="utf-8")

    # `bash` en Windows suele ser Git Bash, que no entiende las rutas D:\...
    if os.name == "posix" and shutil.which("bash"):
        proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr

    # El cabecero los menciona para explicar que ya NO se instalan.
    codigo = "\n".join(linea for linea in texto.splitlines()
                       if not linea.lstrip().startswith("#"))
    for obsoleto in ("Xwrapper.config", "sudoers.d", "virtual-machine-desktop",
                     "matchbox-window-manager", "xorg-x11-server-Xorg"):
        assert obsoleto not in codigo


def test_paquetes_clave_en_todos_los_gestores():
    texto = SCRIPT.read_text(encoding="utf-8")

    # QEMU con GUI (sdl/gtk), hashing, audio y binding spice que da `spicy`.
    for paquete in ("qemu-system-gui", "python3-psutil", "spice-client-gtk",
                    "pulseaudio-utils", "policykit-1", "util-linux"):
        assert paquete in texto
    # setxkbmap lo usa vm_runner.py para detectar el layout del teclado.
    for gestor in ("x11-xkb-utils", "xorg-x11-xkb-utils", "xorg-setxkbmap", "setxkbmap"):
        assert gestor in texto
    # Gestores añadidos en esta revisión.
    for gestor in ("dnf5", "yum", "apk"):
        assert f'echo {gestor}' in texto or f'command -v {gestor}' in texto


def test_postinstall_windows_anade_qemu_al_path_y_comprueba_qemu_img():
    texto = SCRIPT_WIN.read_text(encoding="utf-8")

    assert 'SetEnvironmentVariable("Path"' in texto
    assert "qemu-img.exe" in texto


def test_postinstall_windows_es_ascii_y_anade_visor_al_path():
    """PowerShell 5.1 lee UTF-8 sin BOM como ANSI; un '?' rompe el script."""
    texto = SCRIPT_WIN.read_text(encoding="utf-8")

    assert all(ord(caracter) < 128 for caracter in texto)
    assert "VirtViewer*" in texto
    assert "winget list --exact --id" in texto


def test_reglas_udev_coinciden_con_el_diagnostico():
    fuentes = [SCRIPT.read_text(encoding="utf-8"),
               DIAG.read_text(encoding="utf-8"),
               PASSTHROUGH.read_text(encoding="utf-8")]

    for nombre in ("60-virtual-machine-udmabuf.rules", "50-vm-manager-usb.rules"):
        assert all(nombre in fuente for fuente in fuentes)


def test_el_boton_repara_resuelve_el_script_desde_el_paquete():
    texto = PLUGIN.read_text(encoding="utf-8")

    assert 'Path("scripts/postinstall.sh")' not in texto
    assert "Path(__file__).resolve().parents[2]" in texto


def test_ovmf_de_opensuse_se_detecta_en_diagnostico_y_runner(tmp_path, monkeypatch):
    import services.host_diagnostics as hd
    import services.vm_runner as vr

    code = tmp_path / "ovmf-x86_64-code.bin"
    vars_ = tmp_path / "ovmf-x86_64-vars.bin"
    code.write_bytes(b"C" * (1024 * 1024 + 1))
    vars_.write_bytes(b"V" * (10 * 1024 + 1))

    monkeypatch.setattr(hd, "IS_LINUX", True)
    monkeypatch.setattr(hd, "OVMF_LINUX_DIRS", (str(tmp_path),))
    assert hd.find_ovmf_code() == str(code)

    ovmf_check = [c for c in hd.HostDiagnostics().run_all()
                  if c["name"] == "Firmware UEFI (OVMF)"][0]
    assert ovmf_check["st"] == "ok"
    assert ovmf_check["desc"] == str(code)

    monkeypatch.setattr(vr, "IS_LINUX", True)
    monkeypatch.setattr(vr, "OVMF_LINUX_DIRS", (str(tmp_path),))
    # Aislar también el OSX-KVM real del repositorio.
    monkeypatch.setattr(vr, "__file__", str(tmp_path / "services" / "vm_runner.py"))
    runner = vr.VMRunner.__new__(vr.VMRunner)
    runner.data_dir = tmp_path
    runner.host = None
    assert runner._find_ovmf() == (str(code), str(vars_))
