# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Diagnostico y reparacion de los requisitos de Desktop Mode.

Marcador: desktop_mode_host_check_v2

Modulo PURO (sin PyQt): devuelve dicts con el estado de cada
requisito y ofrece una funcion de reparacion que ejecuta los cambios
con privilegios via pkexec/sudo. La GUI (DesktopModeMixin) se encarga
de mostrarlo y de invocar la reparacion.

Cadena de Desktop Mode (marcador desktop_mode_xorg_vt_v12):
    setpriv -> xinit -> Xorg :N vtN -> matchbox -> QEMU GTK

Requisitos comprobados:
  * 'xinit' en PATH.
  * 'matchbox-window-manager' en PATH.
  * Xorg (/usr/bin/Xorg o /usr/lib/xorg/Xorg).
  * Usuario en el grupo 'tty' (para abrir /dev/ttyN en r/w).
  * /etc/X11/Xwrapper.config con allowed_users=anybody.
  * Wrapper /usr/local/bin/virtual-machine-desktop instalado.
  * /etc/virtual-machine.conf presente (lo escribe install-wrapper.sh).
  * Regla /etc/sudoers.d/virtual-machine-desktop presente.
  * Launcher desktop_mode.py en el repo.
  * TTY grafico actual (informativo).

Soporta Arch, Debian/Ubuntu/Mint y Fedora (gestores
pacman/apt/dnf/zypper/apk).
"""

import os
import shutil
import subprocess
import tempfile

WRAPPER_PATH = "/usr/local/bin/virtual-machine-desktop"
SUDOERS_PATH = "/etc/sudoers.d/virtual-machine-desktop"
CONF_PATH = "/etc/virtual-machine.conf"
XWRAPPER_CONFIG = "/etc/X11/Xwrapper.config"

# Nombres de paquete por gestor.
#   xinit: mismo nombre en todas las distros.
#   matchbox: mismo nombre en Debian/Ubuntu/Mint y Arch; en Fedora
#             no esta empaquetado, se instala via fuente (raro);
#             en openSUSE esta como 'matchbox-window-manager'.
_PKG_NAMES = {
    "apt":    {"xinit": "xinit",
               "matchbox": "matchbox-window-manager"},
    "dnf":    {"xinit": "xorg-x11-xinit",
               "matchbox": "matchbox-window-manager"},
    "pacman": {"xinit": "xorg-xinit",
               "matchbox": "matchbox-window-manager"},
    "zypper": {"xinit": "xinit",
               "matchbox": "matchbox-window-manager"},
    "apk":    {"xinit": "xinit",
               "matchbox": "matchbox-window-manager"},
}


# ---------------------------------------------------------------------------
# Sondas individuales
# ---------------------------------------------------------------------------

def _current_user():
    try:
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        return os.environ.get("USER") or ""


def _user_in_tty_group(user):
    """True si el usuario pertenece al grupo 'tty'.

    Marcador: desktop_mode_host_check_v2_tty.

    Necesario porque /dev/ttyN es crw--w---- root:tty. Sin
    pertenencia al grupo, Xorg no puede abrir la VT y falla con
    'xf86OpenConsole: Cannot open virtual console N'.
    """
    if not user:
        return False
    try:
        import grp
        g = grp.getgrnam("tty")
        return user in g.gr_mem
    except KeyError:
        return False
    except Exception:
        return False


def _xwrapper_config_ok():
    """True si /etc/X11/Xwrapper.config permite allowed_users=anybody."""
    if not os.path.isfile(XWRAPPER_CONFIG):
        return False
    try:
        with open(XWRAPPER_CONFIG, "r", encoding="utf-8",
                  errors="replace") as f:
            content = f.read()
    except Exception:
        return False
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "allowed_users" and v.strip() == "anybody":
                return True
    return False


def _find_xorg():
    """Ruta del primer binario de Xorg disponible, o ''."""
    for p in ("/usr/bin/Xorg", "/usr/lib/xorg/Xorg", "/usr/libexec/Xorg"):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return ""


def _user_in_seat_group_unused(user):
    """(Reservado por compatibilidad historica; ya no se usa.)"""
    return True


def detect_graphical_tty():
    """TTY de la sesion grafica activa, o None."""
    try:
        from desktop_mode import _detect_graphical_tty as _impl
        tty = _impl()
        if tty:
            return tty
    except Exception:
        pass
    try:
        vt = os.environ.get("XDG_VTNR")
        if vt and vt.isdigit() and int(vt) > 0:
            return int(vt)
    except Exception:
        pass
    return None


def _find_wrapper_source(repo_dir):
    """Ubicaciones donde puede vivir el wrapper sin instalar."""
    candidates = [
        os.path.join(repo_dir, "virtual-machine-desktop"),
        os.path.join(repo_dir, "desktop_mode_wrapper.sh"),
        os.path.join(repo_dir, "packaging", "virtual-machine-desktop"),
        os.path.join(repo_dir, "packaging", "desktop_mode_wrapper.sh"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


def _sudoers_rule_installed():
    """Detecta la regla NOPASSWD sin necesitar leer /etc/sudoers.d."""
    if os.geteuid() == 0:
        return os.path.isfile(SUDOERS_PATH)
    if shutil.which("sudo") and os.path.isfile(WRAPPER_PATH):
        try:
            r = subprocess.run(
                ["sudo", "-n", "-l", WRAPPER_PATH],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
        except Exception:
            pass
    try:
        with open(SUDOERS_PATH, "rb"):
            return True
    except FileNotFoundError:
        return False
    except PermissionError:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Deteccion agregada
# ---------------------------------------------------------------------------

def get_desktop_mode_status(repo_dir):
    """Estado completo de los requisitos de Desktop Mode."""
    try:
        from host_deps import detect_linux_package_manager
        manager, info = detect_linux_package_manager()
    except Exception:
        manager, info = None, {}
    distro = (info or {}).get("PRETTY_NAME") \
        or (info or {}).get("ID") or "Linux"

    xinit_path = shutil.which("xinit") or ""
    matchbox_path = shutil.which("matchbox-window-manager") or ""
    xorg_path = _find_xorg()
    user = _current_user()
    wrapper_ok = os.path.isfile(WRAPPER_PATH)
    launcher_path = os.path.join(repo_dir, "desktop_mode.py")
    conf_ok = os.path.isfile(CONF_PATH)

    return {
        "distro": distro,
        "package_manager": manager or "",
        "xinit_installed": bool(xinit_path),
        "xinit_path": xinit_path,
        "matchbox_installed": bool(matchbox_path),
        "matchbox_path": matchbox_path,
        "xorg_installed": bool(xorg_path),
        "xorg_path": xorg_path,
        "user_in_tty_group": _user_in_tty_group(user),
        "xwrapper_config_ok": _xwrapper_config_ok(),
        "xwrapper_config_path": XWRAPPER_CONFIG,
        "wrapper_installed": wrapper_ok,
        "wrapper_source": _find_wrapper_source(repo_dir),
        "conf_present": conf_ok,
        "conf_path": CONF_PATH,
        "sudoers_installed": _sudoers_rule_installed(),
        "launcher_path": launcher_path,
        "launcher_installed": os.path.isfile(launcher_path),
        "graphical_tty": detect_graphical_tty(),
        "current_user": user,
    }


# ---------------------------------------------------------------------------
# Reparacion (una sola autenticacion con pkexec/sudo)
# ---------------------------------------------------------------------------

def _build_repair_script(status):
    """Devuelve (script_body, actions, tmp_files) para ejecutar con root."""
    actions = []
    tmp_files = []
    script = ["set -e", "export DEBIAN_FRONTEND=noninteractive"]

    # 1) Paquetes: xinit + matchbox.
    need_xinit = not status.get("xinit_installed")
    need_matchbox = not status.get("matchbox_installed")
    if need_xinit or need_matchbox:
        manager = status.get("package_manager") or ""
        if manager not in _PKG_NAMES:
            raise RuntimeError(
                "No se pudo detectar el gestor de paquetes. Instala "
                "'xinit' y 'matchbox-window-manager' a mano y vuelve "
                "a comprobar."
            )
        pkgs = []
        if need_xinit:
            pkgs.append(_PKG_NAMES[manager]["xinit"])
        if need_matchbox:
            pkgs.append(_PKG_NAMES[manager]["matchbox"])
        pkgs_s = " ".join(pkgs)
        if manager == "apt":
            script.append("apt-get update -qq || true")
            script.append(f"apt-get install -y {pkgs_s}")
        elif manager == "dnf":
            script.append(f"dnf install -y {pkgs_s}")
        elif manager == "pacman":
            script.append(f"pacman -S --noconfirm --needed {pkgs_s}")
        elif manager == "zypper":
            script.append(f"zypper --non-interactive install {pkgs_s}")
        elif manager == "apk":
            script.append(f"apk add {pkgs_s}")
        actions.append("packages:" + pkgs_s)

    # 2) Grupo tty.
    user = status.get("current_user") or ""
    if user and not status.get("user_in_tty_group"):
        script.append(f"usermod -aG tty {user} || true")
        actions.append("tty_group_add:" + user)

    # 3) Xwrapper.config.
    if not status.get("xwrapper_config_ok"):
        script.append(f"mkdir -p /etc/X11")
        script.append(
            f"printf 'allowed_users=anybody\\nneeds_root_rights=yes\\n' "
            f"> {XWRAPPER_CONFIG}"
        )
        script.append(f"chmod 0644 {XWRAPPER_CONFIG}")
        actions.append("xwrapper_config")

    # 4) Wrapper.
    if not status.get("wrapper_installed"):
        src = status.get("wrapper_source") or ""
        if not src:
            raise RuntimeError(
                "El wrapper no esta instalado y no se encontro su archivo "
                "fuente en el repo. Coloca 'virtual-machine-desktop' en la "
                "raiz del proyecto (o en packaging/) y vuelve a intentarlo."
            )
        script.append(f"install -m 0755 '{src}' {WRAPPER_PATH}")
        actions.append("wrapper")

    # 5) /etc/virtual-machine.conf (lo escribe install-wrapper.sh; si
    #    el wrapper no esta instalado, se acaba de instalar y hay que
    #    regenerarlo).
    if not status.get("conf_present") or "wrapper" in actions:
        repo_dir = os.path.dirname(os.path.abspath(
            status.get("launcher_path") or "/tmp/x"))
        script.append(
            f"printf 'REPO_DIR=%s\\n' '{repo_dir}' > {CONF_PATH}"
        )
        script.append(f"chmod 0644 {CONF_PATH}")
        actions.append("conf")

    # 6) Regla sudoers (validada con visudo antes de activarla).
    if not status.get("sudoers_installed") and user:
        content = (
            "# Generado por Virtual.Machine - Desktop Mode\n"
            f"{user} ALL=(root) NOPASSWD: {WRAPPER_PATH}\n"
        )
        fd, tmp_sudoers = tempfile.mkstemp(
            prefix="vm-sudoers-", suffix=".new")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.chmod(tmp_sudoers, 0o644)
        tmp_files.append(tmp_sudoers)
        script.append(f"visudo -c -f '{tmp_sudoers}' >/dev/null")
        script.append(
            f"install -m 0440 -o root -g root '{tmp_sudoers}' "
            f"{SUDOERS_PATH}"
        )
        actions.append("sudoers")

    return "\n".join(script), actions, tmp_files


def _run_root_script(script_body, log_func):
    """Ejecuta el script con privilegios. Prefiere pkexec, luego sudo."""
    if os.geteuid() == 0:
        argv = ["bash", "-c", script_body]
    elif shutil.which("pkexec"):
        argv = ["pkexec", "bash", "-c", script_body]
    elif shutil.which("sudo"):
        argv = ["sudo", "bash", "-c", script_body]
    else:
        raise RuntimeError(
            "No hay pkexec ni sudo disponibles para aplicar los cambios."
        )
    log_func("==> Ejecutando reparacion (una sola autenticacion).")
    r = subprocess.run(argv, text=True, capture_output=True)
    for line in (r.stdout or "").splitlines():
        log_func("[root] " + line)
    for line in (r.stderr or "").splitlines():
        log_func("[root] " + line)
    if r.returncode != 0:
        raise RuntimeError(
            f"La reparacion fallo (codigo {r.returncode}). "
            "Revisa la Consola de Progreso."
        )


def repair_desktop_mode(repo_dir, log_func=print):
    """Instala/activa lo que falte. Una sola autenticacion."""
    status = get_desktop_mode_status(repo_dir)

    if (status["xinit_installed"]
            and status["matchbox_installed"]
            and status["xorg_installed"]
            and status.get("user_in_tty_group", False)
            and status.get("xwrapper_config_ok", False)
            and status["wrapper_installed"]
            and status.get("conf_present", False)
            and status["sudoers_installed"]
            and status["launcher_installed"]):
        return {"ok": True,
                "details": ["Todo estaba ya instalado."],
                "status": status}

    tmp_files = []
    actions = []
    try:
        script_body, actions, tmp_files = _build_repair_script(status)
        for line in script_body.splitlines():
            log_func("    " + line)
        _run_root_script(script_body, log_func)
    finally:
        for tf in tmp_files:
            try:
                os.remove(tf)
            except OSError:
                pass

    new_status = get_desktop_mode_status(repo_dir)
    all_ok = all([
        new_status["xinit_installed"],
        new_status["matchbox_installed"],
        new_status["xorg_installed"],
        new_status.get("user_in_tty_group", False),
        new_status.get("xwrapper_config_ok", False),
        new_status["wrapper_installed"],
        new_status.get("conf_present", False),
        new_status["sudoers_installed"],
        new_status["launcher_installed"],
    ])
    _details = []
    if all_ok:
        _details.append("Acciones ejecutadas: " + ", ".join(actions))
        if "tty_group_add:" in " ".join(actions):
            _details.append(
                "IMPORTANTE: se anadio el usuario al grupo 'tty'. "
                "Cierra sesion completa y vuelve a entrar para que "
                "los cambios surtan efecto."
            )
    else:
        _details.append(
            "Algunos requisitos siguen pendientes. Revisa el detalle."
        )
    return {
        "ok": all_ok,
        "details": _details,
        "status": new_status,
    }
