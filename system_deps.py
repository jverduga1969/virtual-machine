#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""system_deps.py — dependencias de SISTEMA que hacen falta antes de arrancar
la app (QEMU, pip, librerías xcb de Qt6, virtiofsd).

Solo usa la librería estándar a propósito: run.sh lo ejecuta ANTES de instalar
nada con pip (requests/PyQt6 todavía no existen en una instalación limpia).

Uso:
    python3 system_deps.py --check     # informa; código 1 si falta algo obligatorio
    python3 system_deps.py --install   # instala lo que falte (pide privilegios)

Gestores soportados:
    apt     Ubuntu 22.04+, Debian 12+, Linux Mint 21+, Pop!_OS, ...
    dnf     Fedora 36+ (y derivadas RHEL: qemu-kvm)
    pacman  Arch, CachyOS, Manjaro, EndeavourOS
En otras distribuciones solo informa de lo que falta.

Variable de entorno (la lee run.sh): VM_SKIP_SYSDEPS=1 omite este paso.
"""
import ctypes.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VIRTIOFSD_PATHS = (
    "/usr/lib/virtiofsd",
    "/usr/libexec/virtiofsd",
    "/usr/local/libexec/virtiofsd",
    "/usr/lib/qemu/virtiofsd",      # Ubuntu 22.04 / algunos Debian (qemu-system-common)
)

STATE_FILE = Path.home() / ".cache" / "virtual-machine" / "sysdeps_optional.json"


# ---------------------------------------------------------------- detección --
def _read_os_release():
    info = {}
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        info[k] = v.strip().strip('"')
            break
        except OSError:
            continue
    return info


def detect_manager():
    """Devuelve (gestor|None, info_os_release)."""
    info = _read_os_release()
    ids = {info.get("ID", "").lower()}
    ids.update(x.lower() for x in info.get("ID_LIKE", "").split())
    families = (
        ("apt", "apt-get", {"debian", "ubuntu", "linuxmint", "pop", "elementary", "zorin", "raspbian", "kali"}),
        ("dnf", "dnf", {"fedora", "rhel", "centos", "rocky", "almalinux"}),
        ("pacman", "pacman", {"arch", "manjaro", "cachyos", "endeavouros"}),
    )
    for manager, binary, fam in families:
        if ids & fam and shutil.which(binary):
            return manager, info
    for manager, binary, _ in families:
        if shutil.which(binary):
            return manager, info
    return None, info


def _has_lib(stem, soname):
    ldconfig = shutil.which("ldconfig") or next(
        (p for p in ("/sbin/ldconfig", "/usr/sbin/ldconfig") if os.path.exists(p)), None)
    if ldconfig:
        try:
            out = subprocess.run([ldconfig, "-p"], capture_output=True, text=True, timeout=15).stdout
            if soname in out:
                return True
        except Exception:
            pass
    return bool(ctypes.util.find_library(stem))


def _have_pip():
    try:
        return subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, timeout=30).returncode == 0
    except Exception:
        return False


def _have_virtiofsd():
    if shutil.which("virtiofsd"):
        return True
    return any(os.path.isfile(p) and os.access(p, os.X_OK) for p in VIRTIOFSD_PATHS)


def _have_any_vnc_viewer():
    """True si hay algún visor VNC instalado en el host."""
    return any(shutil.which(n) for n in
               ("gvncviewer", "vncviewer", "tigervnc-viewer"))


def _have_any_spice_viewer():
    """True si hay algún visor SPICE instalado en el host."""
    return any(shutil.which(n) for n in
               ("remote-viewer", "spicy"))


# (clave, descripción, obligatorio, detector, {gestor: [paquetes]})
# Para los NO obligatorios la lista son alternativas: se prueba una a una.
ITEMS = (
    ("pip", "pip de Python", True, _have_pip,
     {"apt": ["python3-pip"], "dnf": ["python3-pip"], "pacman": ["python-pip"]}),
    ("qemu", "QEMU (qemu-system-x86_64)", True,
     lambda: bool(shutil.which("qemu-system-x86_64")),
     {"apt": ["qemu-system-x86"], "dnf": ["qemu-kvm"], "pacman": ["qemu-desktop"]}),
    ("qemu-img", "qemu-img", True,
     lambda: bool(shutil.which("qemu-img")),
     {"apt": ["qemu-utils"], "dnf": ["qemu-img"], "pacman": ["qemu-desktop"]}),
    ("xcb-cursor", "libxcb-cursor (Qt6 / xcb)", True,
     lambda: _has_lib("xcb-cursor", "libxcb-cursor.so.0"),
     {"apt": ["libxcb-cursor0"], "dnf": ["xcb-util-cursor"], "pacman": ["xcb-util-cursor"]}),
    ("xkbcommon-x11", "libxkbcommon-x11 (Qt6 / xcb)", True,
     lambda: _has_lib("xkbcommon-x11", "libxkbcommon-x11.so.0"),
     {"apt": ["libxkbcommon-x11-0"], "dnf": ["libxkbcommon-x11"], "pacman": ["libxkbcommon-x11"]}),
    ("virtiofsd", "virtiofsd (carpetas compartidas VirtioFS)", False, _have_virtiofsd,
     {"apt": ["virtiofsd"], "dnf": ["virtiofsd", "qemu-virtiofsd"], "pacman": ["virtiofsd"]}),
    ("vnc-viewer", "visor VNC externo (gvncviewer / tigervnc)", False,
     _have_any_vnc_viewer,
     {"apt": ["gvncviewer", "tigervnc-viewer"],
      "dnf": ["gvncviewer", "tigervnc"],
      "pacman": ["gtk-vnc", "tigervnc"]}),
    ("spice-viewer", "visor SPICE externo (spicy / remote-viewer)", False,
     _have_any_spice_viewer,
     {"apt": ["spice-client-gtk", "virt-viewer"],
      "dnf": ["spice-gtk-tools", "virt-viewer"],
      "pacman": ["spice-gtk", "virt-viewer"]}),
)


def missing_items():
    req, opt = [], []
    for key, desc, required, detect, pkgs in ITEMS:
        try:
            ok = detect()
        except Exception:
            ok = False
        if not ok:
            (req if required else opt).append((key, desc, pkgs))
    return req, opt


# ---------------------------------------------------------------- instalación --
def _install_cmd(manager, packages):
    if manager == "apt":
        return ["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y"] + packages
    if manager == "dnf":
        return ["dnf", "install", "-y"] + packages
    if manager == "pacman":
        # --needed sin -y: evita actualizaciones parciales (no soportadas en Arch).
        return ["pacman", "-S", "--needed", "--noconfirm"] + packages
    raise ValueError(manager)


def _priv_prefix(prefer_gui=False):
    """Prefijo para ejecutar como root. Desde terminal (run.sh) se prefiere sudo;
    desde la GUI (prefer_gui=True) se prefiere pkexec, que abre un diálogo
    gráfico y no depende de una terminal para escribir la contraseña."""
    if os.geteuid() == 0:
        return []
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if prefer_gui and has_display and shutil.which("pkexec"):
        return ["pkexec"]
    if sys.stdin.isatty() and shutil.which("sudo"):
        return ["sudo"]
    if shutil.which("pkexec"):
        return ["pkexec"]
    if shutil.which("sudo"):
        return ["sudo"]
    return None


def _run(prefix, cmd):
    return subprocess.run(prefix + cmd).returncode == 0


def _aur_helper():
    for helper in ("paru", "yay"):
        if shutil.which(helper):
            return helper
    return None


def ensure_dmg2img(log=print, prefer_gui=True):
    """Devuelve la ruta de dmg2img, instalándolo si falta (o None si no se pudo).

    Se usa al preparar el recovery de macOS. Estado por gestor:
      apt / dnf : paquete 'dmg2img' de los repositorios.
      pacman    : solo está en el AUR; se prueba pacman por si el repositorio
                  de la distro lo trae y, si no, paru/yay (necesita terminal
                  para la contraseña de sudo).
    """
    found = shutil.which("dmg2img")
    if found:
        return found

    manager, _ = detect_manager()
    log("==> dmg2img no está instalado; intentando instalarlo...")
    if manager is None:
        log("==> No reconozco el gestor de paquetes; instala 'dmg2img' manualmente.")
        return None

    prefix = _priv_prefix(prefer_gui)
    if manager in ("apt", "dnf"):
        if prefix is None:
            log("==> No hay sudo ni pkexec; instala 'dmg2img' con root.")
            return None
        if manager == "apt":
            _run(prefix, ["apt-get", "update"])
        if not _run(prefix, _install_cmd(manager, ["dmg2img"])):
            log("==> No se pudo instalar dmg2img con el gestor de paquetes.")
    else:  # pacman
        # ¿Lo trae algún repositorio configurado (p. ej. el de CachyOS)? Se
        # consulta sin root para no pedir contraseña si solo está en el AUR.
        in_repos = subprocess.run(["pacman", "-Si", "dmg2img"], capture_output=True).returncode == 0
        if in_repos and prefix is not None:
            _run(prefix, _install_cmd("pacman", ["dmg2img"]))
        if not shutil.which("dmg2img"):
            helper = _aur_helper()
            if helper and os.geteuid() != 0 and sys.stdin.isatty():
                log(f"==> dmg2img está en el AUR; usando {helper} "
                    "(escribe tu contraseña en la terminal si la pide)...")
                subprocess.run([helper, "-S", "--needed", "--noconfirm", "dmg2img"])
            else:
                log("==> En Arch/CachyOS dmg2img está en el AUR. Instálalo con: "
                    "paru -S dmg2img   (o yay -S dmg2img)")

    found = shutil.which("dmg2img")
    log("==> dmg2img instalado." if found else "==> dmg2img sigue sin estar disponible.")
    return found


def _load_state():
    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_state(keys):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(sorted(keys)), encoding="utf-8")
    except OSError:
        pass


def _fmt(items):
    return ", ".join(desc for _, desc, _ in items)


def main(argv):
    mode = "--install" if "--install" in argv else "--check"
    req, opt = missing_items()
    if not req and not opt:
        return 0

    manager, info = detect_manager()
    distro = info.get("PRETTY_NAME") or info.get("ID") or "Linux"

    if req:
        print(f"==> Faltan dependencias de sistema obligatorias ({distro}): {_fmt(req)}")
    if opt:
        print(f"==> Faltan dependencias opcionales: {_fmt(opt)}")

    if mode == "--check":
        return 1 if req else 0

    if manager is None:
        print("==> No reconozco el gestor de paquetes de esta distribución; instala esos paquetes a mano.")
        return 1 if req else 0

    # Opcionales: se intentan UNA sola vez (si tu distro no las empaqueta, no
    # queremos pedir la contraseña en cada arranque).
    tried = _load_state()
    opt_now = [it for it in opt if it[0] not in tried]

    if not req and not opt_now:
        return 0

    prefix = _priv_prefix()
    if prefix is None:
        print("==> No hay sudo ni pkexec para instalar paquetes; hazlo manualmente con root.")
        return 1 if req else 0

    if req:
        pkgs = []
        for _, _, p in req:
            for name in p.get(manager, []):
                if name not in pkgs:
                    pkgs.append(name)
        if manager == "apt":
            _run(prefix, ["apt-get", "update"])      # un update fallido no debe bloquear
        print("==> Instalando: " + " ".join(pkgs))
        if not _run(prefix, _install_cmd(manager, pkgs)):
            print("==> La instalación falló o se canceló.")
            return 1

    for key, desc, p in opt_now:
        installed = False
        for name in p.get(manager, []):
            print(f"==> Probando paquete opcional: {name}")
            if _run(prefix, _install_cmd(manager, [name])):
                installed = True
                break
        tried.add(key)
        if not installed:
            print(f"==> No se pudo instalar {desc}; esa función quedará desactivada.")
    _save_state(tried)

    req_after, _ = missing_items()
    if req_after:
        print(f"==> Siguen faltando: {_fmt(req_after)}")
        return 1
    print("==> Dependencias de sistema listas.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
