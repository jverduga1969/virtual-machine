# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""config_host_deps.py - Catalogo unico de requisitos del host.

Marcador: config_host_deps_v1

Fuente unica de verdad de:
  * Que requisitos necesita la app para funcionar.
  * Como comprobar cada uno: check() -> (ok: bool, detalle: str).
  * Como repararlos todos de golpe: packaging/postinstall.sh con pkexec.

NO importa PyQt6. Se puede probar desde terminal:

    python3 config_host_deps.py --check
    python3 config_host_deps.py --check --level basic
    python3 config_host_deps.py --check --level advanced

Los paneles de Configuracion Host de la app leen esta lista y la
pintan como semaforos. El boton "Reparar lo que falte" ejecuta
packaging/postinstall.sh (que es idempotente y hace TODO lo que
requiere root: deps del sistema, grupos, udev, wrapper sudo).
"""

import os
import shutil
import subprocess
import sys
import importlib
from pathlib import Path


REPO_DIR       = Path(__file__).resolve().parent
POSTINSTALL_SH = REPO_DIR / "packaging" / "postinstall.sh"


# Categorias para agrupar la lista en la UI.
CATEGORIES = [
    ("virtualizacion", "Virtualizacion"),
    ("permisos",       "Permisos del usuario"),
    ("python",         "Dependencias Python"),
    ("udev",           "Reglas udev"),
    ("consola",        "Consola (VNC / SPICE)"),
    ("comparticion",   "Comparticion y archivos"),
    ("vfio",           "Passthrough PCI / VFIO"),
    ("kiosco",         "Modo kiosco (Desktop Mode)"),
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _which(name):
    return shutil.which(name)


def _exists(p):
    try:
        return os.path.exists(p)
    except Exception:
        return False


def _read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _user_in_group(group):
    try:
        import grp, pwd
        uid = os.getuid()
        try:
            g = grp.getgrnam(group)
        except KeyError:
            return False
        try:
            u = pwd.getpwuid(uid)
        except KeyError:
            return False
        if u.pw_gid == g.gr_gid:
            return True
        return u.pw_name in g.gr_mem
    except Exception:
        return False


def _module_available(name):
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------
# Checks individuales - Basicos
# ----------------------------------------------------------------------

def _check_qemu():
    p = _which("qemu-system-x86_64")
    return bool(p), (p or "no encontrado en PATH")


def _check_kvm():
    if not _exists("/dev/kvm"):
        return False, "no existe /dev/kvm"
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        return False, "/dev/kvm existe pero el usuario no tiene acceso (grupo kvm)"
    return True, "/dev/kvm accesible"


def _check_ovmf():
    # fix_ovmf_check_v1: lista ampliada para cubrir todas las distros.
    # En Arch/CachyOS moderno los archivos llevan sufijo .4m.fd.
    candidates = [
        # Debian / Ubuntu
        "/usr/share/OVMF/OVMF_CODE.fd",
        "/usr/share/OVMF/OVMF_CODE_4M.fd",
        "/usr/share/OVMF/OVMF_CODE.secboot.fd",
        # Arch / CachyOS (actual)
        "/usr/share/edk2/x64/OVMF_CODE.4m.fd",
        "/usr/share/edk2/x64/OVMF_CODE.secboot.4m.fd",
        "/usr/share/edk2/x64/OVMF_CODE.fd",
        # Arch (antiguo)
        "/usr/share/edk2-ovmf/x64/OVMF_CODE.4m.fd",
        "/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",
        # Fedora / openSUSE / otros
        "/usr/share/qemu/OVMF.fd",
        "/usr/share/OVMF/OVMF_CODE.secboot.4m.fd",
    ]
    for c in candidates:
        if _exists(c):
            return True, c
    return False, ("no se encontro OVMF en las rutas habituales. "
                   "Instala 'edk2-ovmf' (Arch), 'ovmf' (Debian) "
                   "o 'edk2-ovmf' (Fedora).")


def _check_swtpm():
    p = _which("swtpm")
    return bool(p), (p or "no encontrado en PATH")


def _check_virtio():
    """Comprueba si el kernel soporta virtio (built-in o como modulo).

    No miramos /sys/module/virtio ni lsmod: en kernels modernos los
    modulos virtio* no se cargan hasta que QEMU los pide, asi que un
    sistema valido sale como "no detectado" si aun no se ha arrancado
    ninguna VM. La pregunta correcta es si el kernel LOS TIENE
    disponibles, no si estan cargados ahora mismo.
    """
    import platform
    import glob as _glob

    if _exists("/sys/bus/virtio"):
        return True, "/sys/bus/virtio presente"

    rel = platform.release()
    patterns = [
        f"/lib/modules/{rel}/kernel/drivers/virtio/*.ko",
        f"/lib/modules/{rel}/kernel/drivers/virtio/*.ko.zst",
        f"/usr/lib/modules/{rel}/kernel/drivers/virtio/*.ko",
        f"/usr/lib/modules/{rel}/kernel/drivers/virtio/*.ko.zst",
    ]
    for pat in patterns:
        if _glob.glob(pat):
            return True, f"modulos virtio presentes en /lib/modules/{rel}/"

    if _glob.glob("/sys/module/virtio*"):
        return True, "modulo virtio cargado"

    return False, f"kernel {rel} no expone virtio en /lib/modules ni en /sys"


def _check_audio():
    for exe, name in (("pactl", "PulseAudio/PipeWire"),
                      ("pw-cli", "PipeWire"),
                      ("aplay", "ALSA")):
        if _which(exe):
            return True, f"{name} ({exe})"
    return False, "ni PipeWire, ni PulseAudio, ni ALSA detectados"


def _check_polkit():
    p = _which("pkexec")
    return bool(p), (p or "no encontrado (paquete 'polkit')")


def _check_udev():
    p = _which("udevadm")
    return bool(p), (p or "no encontrado")


def _check_pyqt6():
    try:
        import PyQt6
        v = getattr(PyQt6, "__version__", "?")
        return True, f"PyQt6 {v}"
    except Exception as e:
        return False, f"no importable: {e}"


def _check_requests():
    try:
        import requests
        return True, f"requests {requests.__version__}"
    except Exception as e:
        return False, f"no importable: {e}"


def _check_packaging():
    try:
        import packaging
        return True, f"packaging {packaging.__version__}"
    except Exception as e:
        return False, f"no importable: {e}"


_UDMABUF_RULE = "/etc/udev/rules.d/60-virtual-machine-udmabuf.rules"
_USB_RULE     = "/etc/udev/rules.d/50-vm-manager-usb.rules"


def _check_udmabuf_udev():
    if not _exists(_UDMABUF_RULE):
        return False, f"falta {_UDMABUF_RULE}"
    txt = _read(_UDMABUF_RULE)
    if 'KERNEL=="udmabuf"' in txt and "uaccess" in txt:
        return True, "regla udev instalada"
    return False, "archivo presente pero sin la regla esperada"


def _check_usb_udev():
    if not _exists(_USB_RULE):
        return False, f"falta {_USB_RULE}"
    txt = _read(_USB_RULE)
    if 'SUBSYSTEM=="usb"' in txt and "uaccess" in txt:
        return True, "regla udev instalada"
    return False, "archivo presente pero sin la regla esperada"


def _check_user_kvm_group():
    if _user_in_group("kvm"):
        return True, "usuario en el grupo kvm"
    return False, "usuario NO esta en el grupo kvm"


def _check_vnc_widget():
    p = REPO_DIR / "vnc_widget"
    if not p.is_dir():
        return False, "no existe vnc_widget/ en el repo"
    if _module_available("vnc_widget"):
        return True, "vnc_widget importable"
    return False, "vnc_widget existe pero no es importable (revisa python-xlib)"


def _check_spice_gtk():
    try:
        import gi
        gi.require_version("SpiceClientGtk", "3.0")
        from gi.repository import SpiceClientGtk  # noqa
        return True, "spice-gtk binding disponible"
    except Exception as e:
        return False, f"no disponible: {e}"


def _check_vnc_viewer():
    for exe in ("vncviewer", "tigervnc-viewer", "gvncviewer"):
        p = _which(exe)
        if p:
            return True, p
    return False, "ningun visor VNC externo en PATH"


def _check_spice_viewer():
    for exe in ("remote-viewer", "spicy", "virt-viewer"):
        p = _which(exe)
        if p:
            return True, p
    return False, "ningun visor SPICE externo en PATH"


# ----------------------------------------------------------------------
# Checks individuales - Avanzados
# ----------------------------------------------------------------------

def _check_virtiofsd():
    p = _which("virtiofsd")
    if not p:
        for c in ("/usr/lib/qemu/virtiofsd",
                  "/usr/libexec/virtiofsd",
                  "/usr/lib/virtiofsd"):
            if _exists(c):
                p = c
                break
    if not p:
        return False, "virtiofsd no encontrado (paquete virtiofsd / qemu-virtiofsd)"
    # postinstall_uidmap_v1_deps: virtiofsd (Rust) configura un sandbox
    # de user namespace con newuidmap/newgidmap. Sin el paquete 'uidmap'
    # aborta al arrancar con un error opaco (log de virtiofsd vacío,
    # QEMU con Connection refused). El postinstall lo instala; este check
    # detecta el caso de un usuario que actualizo a mano sin pasar por
    # 'Reparar'.
    uidmap = _which("newuidmap") or ("/usr/bin/newuidmap" if _exists("/usr/bin/newuidmap") else "")
    if not uidmap:
        return False, (p + " presente, pero newuidmap no encontrado "
                       "(paquete 'uidmap'; el postinstall lo instala)")
    return True, p


def _check_smbd():
    p = _which("smbd")
    return bool(p), (p or "smbd no encontrado (paquete 'samba')")


def _check_iommu_on():
    txt = _read("/proc/cmdline")
    if "intel_iommu=on" in txt or "amd_iommu=on" in txt or "iommu=on" in txt:
        return True, txt.strip()
    return False, "no aparece intel_iommu=on en /proc/cmdline"


def _check_iommu_groups():
    try:
        import glob
        groups = glob.glob("/sys/kernel/iommu_groups/[0-9]*")
        if groups:
            return True, f"{len(groups)} grupos IOMMU"
        return False, "sin grupos IOMMU visibles"
    except Exception as e:
        return False, f"error: {e}"


def _check_iommu_dmar():
    for c in ("/sys/firmware/acpi/tables/DMAR",
              "/sys/firmware/acpi/tables/data/DMAR"):
        if _exists(c):
            return True, c
    return False, "tabla ACPI DMAR no presente"


def _check_kiosk_xorg():
    for exe in ("Xorg", "X"):
        p = _which(exe)
        if p:
            return True, p
    return False, "Xorg no encontrado"


def _check_kiosk_xinit():
    p = _which("xinit")
    return bool(p), (p or "xinit no encontrado")


def _check_kiosk_matchbox():
    p = _which("matchbox-window-manager")
    return bool(p), (p or "matchbox-window-manager no encontrado")


def _check_kiosk_wrapper():
    p = "/usr/local/bin/virtual-machine-desktop"
    return _exists(p), (p if _exists(p) else "no instalado")


def _check_kiosk_conf():
    p = "/etc/virtual-machine.conf"
    return _exists(p), (p if _exists(p) else "no existe")


def _check_kiosk_sudoers():
    # fix_sudoers_check_v2: en Arch/CachyOS, si el usuario esta en el
    # grupo 'wheel', ya tiene '(ALL) ALL' en sudoers. En ese caso,
    # 'sudo -n -l <cmd>' NO expande las reglas NOPASSWD especificas
    # para ese comando (limitacion conocida de sudo). Hay que usar
    # 'sudo -l' completo y buscar el patron NOPASSWD en la salida.
    import subprocess as _sp

    wrapper = "/usr/local/bin/virtual-machine-desktop"
    conf = "/etc/virtual-machine.conf"

    # 1) Verificacion funcional: 'sudo -l' completo.
    #    Requiere contraseña si no hay NOPASSWD para 'sudo -l' (que
    #    no lo hay: solo para el wrapper). Asi que primero intentamos
    #    con -n, y si falla, no pasa nada: seguimos al fallback.
    try:
        r = _sp.run(
            ["sudo", "-n", "-l"],
            capture_output=True, text=True, timeout=3,
        )
        out = (r.stdout or "") + (r.stderr or "")
        # Buscamos la linea exacta del wrapper con NOPASSWD.
        if "NOPASSWD:" in out and wrapper in out:
            return True, f"regla NOPASSWD activa para {wrapper}"
    except Exception:
        pass

    # 2) Fallback indirecto: si el wrapper y el conf estan instalados,
    #    es muy probable que el sudoers tambien (el postinstall los
    #    instala juntos, y visudo -c los valida).
    if _exists(wrapper) and _exists(conf):
        return True, (f"{wrapper} y {conf} instalados "
                      "(sudoers no comprobable sin root)")
    return False, "no existe (ni wrapper ni conf instalados)"


def _check_kiosk_tty_group():
    if _user_in_group("tty"):
        return True, "usuario en el grupo tty"
    return False, "usuario NO esta en el grupo tty"


def _check_kiosk_xwrapper():
    p = "/etc/X11/Xwrapper.config"
    txt = _read(p).replace(" ", "")
    if "allowed_users=anybody" in txt:
        return True, p
    return False, f"falta allowed_users=anybody en {p}"


# ----------------------------------------------------------------------
# Catalogo
# ----------------------------------------------------------------------

REQUIREMENTS = [
    # --- Virtualizacion ---
    {"key": "qemu",   "label": "QEMU",
     "desc": "Emulador. Sin QEMU no arranca ninguna VM.",
     "level": "basic", "category": "virtualizacion", "check": _check_qemu},
    {"key": "kvm",    "label": "KVM (/dev/kvm)",
     "desc": "Aceleracion por hardware. Sin KVM, QEMU emula (lento).",
     "level": "basic", "category": "virtualizacion", "check": _check_kvm},
    {"key": "ovmf",   "label": "Firmware UEFI (OVMF)",
     "desc": "VMs con UEFI y Secure Boot.",
     "level": "basic", "category": "virtualizacion", "check": _check_ovmf},
    {"key": "swtpm",  "label": "TPM 2.0 (swtpm)",
     "desc": "TPM virtual. Windows 11 lo exige.",
     "level": "basic", "category": "virtualizacion", "check": _check_swtpm},
    {"key": "virtio", "label": "Modulos VirtIO",
     "desc": "Dispositivos paravirtualizados (red, disco, GPU).",
     "level": "basic", "category": "virtualizacion", "check": _check_virtio},
    {"key": "audio",  "label": "Audio del host",
     "desc": "PipeWire, PulseAudio o ALSA. Para el sonido de la VM.",
     "level": "basic", "category": "virtualizacion", "check": _check_audio},

    # --- Permisos ---
    {"key": "kvm_group", "label": "Usuario en el grupo 'kvm'",
     "desc": "Acceso a /dev/kvm sin sudo. Requiere logout/login.",
     "level": "basic", "category": "permisos", "check": _check_user_kvm_group},

    # --- Python ---
    {"key": "pyqt6",     "label": "PyQt6",
     "desc": "Interfaz grafica.",
     "level": "basic", "category": "python", "check": _check_pyqt6},
    {"key": "requests",  "label": "requests",
     "desc": "Descarga de ISOs, versiones, Recovery de macOS.",
     "level": "basic", "category": "python", "check": _check_requests},
    {"key": "packaging", "label": "packaging",
     "desc": "Comparacion de versiones.",
     "level": "basic", "category": "python", "check": _check_packaging},
    {"key": "polkit",    "label": "polkit / pkexec",
     "desc": "Dialogo grafico de contrasena para 'Reparar'.",
     "level": "basic", "category": "python", "check": _check_polkit},
    {"key": "udevadm",   "label": "udev / udevadm",
     "desc": "Recarga de reglas tras el postinstall.",
     "level": "basic", "category": "python", "check": _check_udev},

    # --- udev ---
    {"key": "udmabuf_udev", "label": "Regla udev: udmabuf",
     "desc": "Acceso a /dev/udmabuf para VirGL (3D).",
     "level": "basic", "category": "udev", "check": _check_udmabuf_udev},
    {"key": "usb_udev",     "label": "Regla udev: USB",
     "desc": "Passthrough USB sin pedir contrasena cada vez.",
     "level": "basic", "category": "udev", "check": _check_usb_udev},

    # --- Consola ---
    {"key": "vnc_widget",   "label": "Cliente VNC embebido",
     "desc": "Consola Grafica dentro de la app.",
     "level": "basic", "category": "consola", "check": _check_vnc_widget},
    {"key": "spice_gtk",    "label": "spice-gtk (binding Python)",
     "desc": "Consola SPICE embebida en la app.",
     "level": "basic", "category": "consola", "check": _check_spice_gtk},
    {"key": "vnc_viewer",   "label": "Visor VNC externo",
     "desc": "vncviewer / tigervnc / gvncviewer.",
     "level": "basic", "category": "consola", "check": _check_vnc_viewer},
    {"key": "spice_viewer", "label": "Visor SPICE externo",
     "desc": "remote-viewer / spicy.",
     "level": "basic", "category": "consola", "check": _check_spice_viewer},

    # --- Comparticion (avanzado) ---
    {"key": "virtiofsd", "label": "virtiofsd",
     "desc": "Compartir carpetas con Linux (VirtioFS).",
     "level": "advanced", "category": "comparticion", "check": _check_virtiofsd},
    {"key": "smbd",      "label": "Samba (smbd)",
     "desc": "Compartir carpetas con Windows y macOS.",
     "level": "advanced", "category": "comparticion", "check": _check_smbd},

    # --- VFIO (avanzado) ---
    {"key": "iommu_on",     "label": "IOMMU activado en el kernel",
     "desc": "intel_iommu=on o amd_iommu=on en /proc/cmdline.",
     "level": "advanced", "category": "vfio", "check": _check_iommu_on},
    {"key": "iommu_dmar",   "label": "Firmware ACPI DMAR (VT-d)",
     "desc": "VT-d expuesto por el firmware. Se activa en BIOS/UEFI.",
     "level": "advanced", "category": "vfio", "check": _check_iommu_dmar},
    {"key": "iommu_groups", "label": "Grupos IOMMU visibles",
     "desc": "Necesarios para passthrough PCI estable.",
     "level": "advanced", "category": "vfio", "check": _check_iommu_groups},

    # --- Modo kiosco (avanzado) ---
    {"key": "kiosk_xorg",     "label": "Xorg",
     "desc": "Servidor X para la VT dedicada del Modo kiosco.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_xorg},
    {"key": "kiosk_xinit",    "label": "xinit",
     "desc": "Registra una sesion logind virtual en la VT.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_xinit},
    {"key": "kiosk_matchbox", "label": "matchbox-window-manager",
     "desc": "WM minimo para la VT del Modo kiosco.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_matchbox},
    {"key": "kiosk_wrapper",  "label": "Wrapper sudo de Modo kiosco",
     "desc": "/usr/local/bin/virtual-machine-desktop con NOPASSWD.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_wrapper},
    {"key": "kiosk_conf",     "label": "/etc/virtual-machine.conf",
     "desc": "Ruta del repo para el wrapper.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_conf},
    {"key": "kiosk_sudoers",  "label": "Regla sudoers del Modo kiosco",
     "desc": "/etc/sudoers.d/virtual-machine-desktop.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_sudoers},
    {"key": "kiosk_tty_group","label": "Usuario en el grupo 'tty'",
     "desc": "Acceso a /dev/ttyN. Requiere logout/login completo.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_tty_group},
    {"key": "kiosk_xwrapper", "label": "Xwrapper.config",
     "desc": "allowed_users=anybody + needs_root_rights=yes.",
     "level": "advanced", "category": "kiosco", "check": _check_kiosk_xwrapper},
]


def check_one(req):
    try:
        ok, detail = req["check"]()
        return bool(ok), str(detail)
    except Exception as e:
        return False, f"error al comprobar: {e}"


def check_all():
    return {r["key"]: check_one(r) for r in REQUIREMENTS}


def requirements_by_level(level):
    return [r for r in REQUIREMENTS if r["level"] == level]


def summarize():
    results = check_all()
    missing = []
    ok = 0
    for r in REQUIREMENTS:
        o, _d = results[r["key"]]
        if o:
            ok += 1
        else:
            missing.append(r["key"])
    return ok, len(REQUIREMENTS), missing


# ----------------------------------------------------------------------
# postinstall
# ----------------------------------------------------------------------

def postinstall_available():
    return POSTINSTALL_SH.is_file() and os.access(POSTINSTALL_SH, os.X_OK)


def run_postinstall(log_func=None, timeout=300):
    """Ejecuta packaging/postinstall.sh con pkexec. Idempotente.

    Devuelve dict {"ok": bool, "returncode": int,
                   "stdout": str, "stderr": str}.
    """
    if not POSTINSTALL_SH.is_file():
        return {"ok": False, "returncode": -1, "stdout": "",
                "stderr": f"no existe {POSTINSTALL_SH}"}
    pkexec = shutil.which("pkexec")
    if not pkexec:
        return {"ok": False, "returncode": -1, "stdout": "",
                "stderr": "pkexec no encontrado"}

    _stdbuf = shutil.which("stdbuf")
    if _stdbuf:
        argv = [pkexec, _stdbuf, "-oL", "-eL",
                "bash", str(POSTINSTALL_SH)]
    else:
        argv = [pkexec, "bash", str(POSTINSTALL_SH)]
    if on_progress:
        try:
            on_progress(1, "Lanzando pkexec. Si aparece un "
                           "dialogo de contrasena, introducela.")
        except Exception:
            pass
    if log_func:
        try:
            log_func("==> Reparando requisitos del host (postinstall.sh)...")
            log_func("    " + " ".join(argv))
        except Exception:
            pass
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": str(e)}

    out = r.stdout or ""
    err = r.stderr or ""
    if log_func:
        for line in out.splitlines():
            try:
                log_func("    " + line)
            except Exception:
                pass
        for line in err.splitlines():
            try:
                log_func("    " + line)
            except Exception:
                pass
    return {"ok": r.returncode == 0,
            "returncode": r.returncode,
            "stdout": out, "stderr": err}



# ----------------------------------------------------------------------
# Streaming (barra de progreso) - config_host_progress_v1
# ----------------------------------------------------------------------

_PROGRESS_PHASES = [
    (r"Postinstall .* iniciado",          3),
    (r"Gestor de paquetes detectado",     4),
    (r"Actualizando indices",             6),
    (r": instalando ",                   20),
    (r"ya instalado",                    30),
    (r"Ajustando grupos",                60),
    (r"Instalando reglas udev",          72),
    (r"udev recargado",                  78),
    (r"Configurando /etc/X11/Xwrapper",  82),
    (r"Xwrapper.config listo",           85),
    (r"Instalando wrapper sudo",         88),
    (r"wrapper instalado",               91),
    (r"regla sudoers instalada",         94),
    (r"Postinstall .* completado",       98),
]


def run_postinstall_streaming(on_line=None, on_progress=None, timeout=600):
    """Ejecuta postinstall.sh con pkexec leyendo stdout en streaming.

    Callbacks (ambos opcionales):
      on_line(line: str)                   -> una linea de salida
      on_progress(pct: int, phase: str)    -> % y texto de la fase

    Devuelve dict {"ok": bool, "returncode": int, "output": str}.
    """
    import re as _re
    if not POSTINSTALL_SH.is_file():
        return {"ok": False, "returncode": -1,
                "output": "no existe " + str(POSTINSTALL_SH)}
    pkexec = shutil.which("pkexec")
    if not pkexec:
        return {"ok": False, "returncode": -1,
                "output": "pkexec no encontrado"}

    argv = [pkexec, "bash", str(POSTINSTALL_SH)]
    lines = []
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
        )
    except Exception as e:
        return {"ok": False, "returncode": -1, "output": str(e)}

    try:
        for raw in iter(proc.stdout.readline, ""):
            line = raw.rstrip()
            lines.append(line)
            if on_line:
                try:
                    on_line(line)
                except Exception:
                    pass
            if on_progress and line:
                for pat, pct in _PROGRESS_PHASES:
                    if _re.search(pat, line):
                        try:
                            on_progress(pct, line)
                        except Exception:
                            pass
                        break
        proc.wait(timeout=timeout)
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        lines.append("[ERROR] " + str(e))
        return {"ok": False, "returncode": -1,
                "output": chr(10).join(lines)}

    rc = proc.returncode
    if on_progress and rc == 0:
        try:
            on_progress(100, "Completado.")
        except Exception:
            pass
    return {"ok": rc == 0, "returncode": rc,
            "output": chr(10).join(lines)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Estado de los requisitos del host")
    ap.add_argument("--check", action="store_true", help="Comprobar todos y salir")
    ap.add_argument("--level", choices=["basic", "advanced", "all"], default="all")
    args = ap.parse_args()

    if args.check:
        ok, total, missing = summarize()
        print(f"OK {ok}/{total}")
        for r in REQUIREMENTS:
            if args.level != "all" and r["level"] != args.level:
                continue
            o, d = check_one(r)
            mark = "\u2705" if o else "\u274c"
            print(f"  {mark} {r['label']:38s}  {d}")
        if missing:
            print("Faltan:", ", ".join(missing))
        sys.exit(0 if not missing else 1)


# config_host_deps_v1_rev2

# config_host_progress_v1


# config_host_progress_v2
