# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Backends de consola gráfica para QEMU: VNC y SPICE, embebidos o externos.

Módulo puramente utilitario (no depende de PyQt ni de GTK). Expone:
  - Constantes de protocolo y modo.
  - Rutas de los sockets por VM.
  - Construcción de los argumentos QEMU correspondientes.
  - Detección de visores externos instalados en el host.
"""
import os
import shutil
import urllib.parse

# i18n_tanda2d2b: import opcional de QCoreApplication para traducir
# los textos de describe_requirements(). El modulo se diseno como
# 'puro' (sin PyQt); este import es barato y solo se usa para i18n.
try:
    from PyQt6.QtCore import QCoreApplication as _QCA
except Exception:
    _QCA = None

# Silenciar el aviso benigno de GTK al inicializarse en sesiones
# Wayland/KDE sin appmenu-gtk-module instalado:
#   Gtk-Message: Failed to load module "appmenu-gtk-module"
# No es un error; solo falta el módulo de menús globales, irrelevante
# aquí. Se limpia GTK_MODULES antes de que GTK lo lea.
os.environ.setdefault("GTK_MODULES", "")

# --- Protocolos --------------------------------------------------------------
PROTOCOL_VNC = "vnc"
PROTOCOL_SPICE = "spice"
ALL_PROTOCOLS = (PROTOCOL_VNC, PROTOCOL_SPICE)

# --- Modos de presentación ---------------------------------------------------
MODE_EMBEDDED = "embedded"   # widget dentro de la pestaña "Consola Gráfica"
MODE_EXTERNAL = "external"   # visor del sistema en ventana aparte
MODE_NATIVE = "native"       # ventana nativa de QEMU (-display gtk/sdl)
MODE_HYBRID = "hybrid"       # VNC embebido + SPICE externo a la vez
MODE_HYBRID_GL = "hybrid_gl" # VNC embebido (2D) + ventana GL propia de QEMU (3D)
ALL_MODES = (MODE_EMBEDDED, MODE_EXTERNAL, MODE_NATIVE, MODE_HYBRID, MODE_HYBRID_GL)

DEFAULT_PROTOCOL = PROTOCOL_VNC
DEFAULT_MODE = MODE_EMBEDDED


# --- Sockets por VM ----------------------------------------------------------
def vnc_socket_path(vm_dir: str) -> str:
    return os.path.join(vm_dir, "qemu.vnc.sock")


def spice_socket_path(vm_dir: str) -> str:
    return os.path.join(vm_dir, "qemu.spice.sock")


def socket_path(vm_dir: str, protocol: str) -> str:
    return spice_socket_path(vm_dir) if protocol == PROTOCOL_SPICE else vnc_socket_path(vm_dir)


# --- Argumentos QEMU ---------------------------------------------------------
def qemu_console_args(vm_dir: str, protocol: str, mode: str) -> tuple:
    """Devuelve (args_qemu, info) para el protocolo/modo elegidos.

    info = {"protocol": ..., "mode": ..., "socket": ...}

    Reglas:
      - MODE_NATIVE: sin args aquí. Los pone workers._graphics_args() como
        -display gtk/sdl. Devuelve ("", info).
      - MODE_EMBEDDED y MODE_EXTERNAL son idénticos en QEMU (mismo socket);
        la diferencia es quién se conecta: el widget o un visor externo.
    """
    info = {"protocol": protocol, "mode": mode, "socket": ""}

    if mode == MODE_NATIVE:
        return "", info

    if mode == MODE_HYBRID:
        # VNC embebido + SPICE externo, ambos en la misma VM.
        # QEMU permite exponer VNC y SPICE a la vez; no son
        # mutuamente excluyentes.
        vnc_sock = vnc_socket_path(vm_dir)
        port, port_note = _pick_free_port_with_log("SPICE+híbrido")
        if port is None:
            raise RuntimeError(
                "No hay puertos libres en el rango 5930-6199 para SPICE. "
                "Cierra VMs que no estés usando o reinicia el sistema si "
                "el rango está bloqueado por procesos residuales."
            )
        info["socket"] = vnc_sock
        info["vnc_socket"] = vnc_sock
        info["port"] = port
        info["uri"] = spice_uri_for_port(port)
        if port_note:
            info["port_note"] = port_note
        args = (
            f'-vnc unix:"{vnc_sock}" '
            f'-spice port={port},addr=127.0.0.1,ipv4=on,ipv6=off,disable-ticketing=on '
            f'-display none'
        )
        return args, info

    if mode == MODE_HYBRID_GL:
        vnc_sock = vnc_socket_path(vm_dir)
        info["socket"] = vnc_sock
        info["vnc_socket"] = vnc_sock
        info["gl_window"] = True
        args = f'-vnc unix:"{vnc_sock}"'
        return args, info

    if protocol == PROTOCOL_VNC:
        sock = vnc_socket_path(vm_dir)
        info["socket"] = sock
        # -display none: sin ventana local de QEMU; el único display
        # visible es el socket VNC.
        return f'-display none -vnc unix:"{sock}"', info

    if protocol == PROTOCOL_SPICE:
        # TCP en 127.0.0.1 en vez de socket Unix. Los visores
        # (spicy, remote-viewer) parsean las URIs y se rompen con
        # rutas que contienen espacios; un puerto local evita todo
        # eso. Además sigue siendo local-only: 127.0.0.1 no es
        # accesible desde otras máquinas de la red.
        port, port_note = _pick_free_port_with_log("SPICE")
        if port is None:
            raise RuntimeError(
                "No hay puertos libres en el rango 5930-5999 para SPICE."
            )
        info["port"] = port
        info["uri"] = spice_uri_for_port(port)
        info["socket"] = info["uri"]  # compatibilidad
        if port_note:
            info["port_note"] = port_note
        args = (
            f'-spice port={port},addr=127.0.0.1,disable-ticketing=on '
            f'-display none'
        )
        return args, info


    return "", info


def _pick_free_port(lo=5930, hi=6199):
    """Devuelve el primer puerto TCP libre en [lo, hi], o None.

    Es una comprobación "best effort": entre el momento en que devolvemos
    el puerto y QEMU se enlaza pasan unos milisegundos; si otro proceso lo
    ocupa, QEMU fallará y el usuario verá el error claro en el log. Para el
    caso normal (una o dos VMs corriendo a la vez) nunca colisiona.
    """
    import socket
    for port in range(lo, hi + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            try:
                s.close()
            except Exception:
                pass
            continue
    return None


def _pick_free_port_with_log(verbose_label=""):
    """Igual que _pick_free_port pero devuelve un motivo si el puerto no
    es el primero del rango.

    Devuelve (port, nota) donde nota es "" si el puerto es 5930 (el
    preferido) o un mensaje explicativo si otro proceso lo estaba
    usando. verbose_label se incluye en el mensaje para distinguir el
    origen en el log (por ejemplo "SPICE" o "SPICE+híbrido").
    """
    port = _pick_free_port()
    if port is None:
        return None, ""
    if port != 5930:
        label = (verbose_label + ": ") if verbose_label else ""
        return port, (
            f"{label}el puerto preferido 5930 estaba ocupado; se usará {port}."
        )
    return port, ""


def spice_uri_for_port(port: int) -> str:
    """URI SPICE para un puerto local: spice://127.0.0.1:NNNN."""
    return f"spice://127.0.0.1:{int(port)}"


def console_uri(protocol: str, sock: str) -> str:
    """URI que entienden los visores externos.

    Para SPICE, sock puede ser:
      • una URI completa "spice://127.0.0.1:NNNN" (lo normal ahora), o
      • un puerto como entero/string ("5937"), o
      • una ruta de socket Unix (legado; no recomendado por los espacios).
    """
    if protocol == PROTOCOL_SPICE:
        s = str(sock or "").strip()
        if s.startswith("spice://"):
            return s
        if s.isdigit():
            return spice_uri_for_port(int(s))
        # Legado (socket Unix): devolvemos URI con path encoded por si acaso.
        enc = urllib.parse.quote(s, safe="/")
        return f"spice+unix://{enc}"
    return sock


def build_viewer_args(template, sock, uri, port=None):
    """Sustituye marcadores en la plantilla del visor.

    Marcadores disponibles:
      • {sock} → ruta del socket Unix (VNC) o URI (SPICE; preferir {uri}).
      • {uri}  → URI completa, p. ej. "spice://127.0.0.1:5930".
      • {port} → número de puerto (solo SPICE).
      • {host} → hostname (siempre "127.0.0.1" para SPICE local).

    port es opcional: si la plantilla no usa {port}, no pasa nada por
    pasarlo. Si la plantilla SÍ usa {port} pero port es None, se deja el
    marcador intacto para que el error sea visible.
    """
    out = []
    for a in template:
        s = str(a).replace("{sock}", sock or "")
        s = s.replace("{uri}", uri or "")
        s = s.replace("{host}", "127.0.0.1")
        if port is not None:
            s = s.replace("{port}", str(port))
        out.append(s)
    return out


def find_vnc_viewer():
    """Devuelve (ruta, plantilla_args) o (None, None).

    Plantilla con marcadores {sock} y {uri}. VNC no usa URI:
    todos los visores aceptan el path del socket tal cual.
    """
    for name in ("gvncviewer", "vncviewer", "tigervnc-viewer"):
        path = shutil.which(name)
        if path:
            return path, ["{sock}"]
    return None, None


def find_spice_viewer():
    """Devuelve (ruta, plantilla_args) o (None, None).

    Marcadores: {sock}, {uri}, {host}, {port}.

    spicy NO acepta URIs en --host: espera un hostname y un puerto en
    opciones separadas (--host, --port). Pasarle "spice://127.0.0.1:5930"
    lo pone tal cual en el campo Hostname del diálogo y no conecta.

    remote-viewer, en cambio, SÍ acepta la URI spice:// completa como
    argumento posicional.

    Preferimos spicy si está (más ligero, parte de spice-gtk) y caemos a
    remote-viewer si no.
    """
    path = shutil.which("spicy")
    if path:
        # spicy: hostname + puerto separados. Host fijo 127.0.0.1 (SPICE
        # siempre se expone en loopback por seguridad).
        return path, ["--host=127.0.0.1", "--port={port}"]
    path = shutil.which("remote-viewer")
    if path:
        return path, ["{uri}"]
    return None, None


def find_viewer(protocol: str):
    if protocol == PROTOCOL_VNC:
        return find_vnc_viewer()
    if protocol == PROTOCOL_SPICE:
        return find_spice_viewer()
    return None, None


# --- Capacidades del host ----------------------------------------------------
def embedded_spice_available() -> bool:
    """True si spice-gtk tiene binding Python (gi.repository.SpiceClientGtk)."""
    try:
        import gi
        gi.require_version("SpiceClientGtk", "3.0")
        from gi.repository import SpiceClientGtk  # noqa: F401
        return True
    except Exception:
        return False


def describe_requirements(protocol: str, mode: str) -> str:
    """Texto de ayuda segun protocolo/modo (i18n_tanda2d2b)."""
    if mode == MODE_NATIVE:
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "QEMU abre su propia ventana (GTK/SDL). No hace falta visor "
            "externo ni cliente; a cambio, la VM no aparece dentro de la app.") \
            if _QCA else ("QEMU abre su propia ventana (GTK/SDL). No hace falta visor "
                          "externo ni cliente; a cambio, la VM no aparece dentro de la app.")
    if mode == MODE_HYBRID:
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "Híbrida: VNC se muestra dentro de la app (funciona en "
            "Wayland y X11) y SPICE se abre en una ventana externa "
            "con spicy o remote-viewer. Lo mejor de ambos: "
            "embebido para tenerlo a mano, SPICE para rendimiento y "
            "clipboard avanzado.") \
            if _QCA else ("Híbrida: VNC se muestra dentro de la app (funciona en "
                          "Wayland y X11) y SPICE se abre en una ventana externa "
                          "con spicy o remote-viewer. Lo mejor de ambos: "
                          "embebido para tenerlo a mano, SPICE para rendimiento y "
                          "clipboard avanzado.")
    if protocol == PROTOCOL_VNC and mode == MODE_EMBEDDED:
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "VNC embebido en la app. Sin dependencias adicionales.") \
            if _QCA else "VNC embebido en la app. Sin dependencias adicionales."
    if protocol == PROTOCOL_VNC and mode == MODE_EXTERNAL:
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "VNC en ventana externa. Necesitas vncviewer (tigervnc), "
            "gvncviewer o remmina instalado.") \
            if _QCA else ("VNC en ventana externa. Necesitas vncviewer (tigervnc), "
                          "gvncviewer o remmina instalado.")
    if protocol == PROTOCOL_SPICE and mode == MODE_EMBEDDED:
        if embedded_spice_available():
            return _QCA.translate(
                "VirtualMachineManagerApp",
                "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). "
                "Requiere sesión X11; en Wayland cae a visor externo.") \
                if _QCA else ("SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). "
                              "Requiere sesión X11; en Wayland cae a visor externo.")
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "SPICE embebido solicitado, pero spice-gtk no tiene binding "
            "Python. Se usará visor externo como respaldo. Instala "
            "python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o "
            "python-gobject + spice-gtk (Arch).") \
            if _QCA else ("SPICE embebido solicitado, pero spice-gtk no tiene binding "
                          "Python. Se usará visor externo como respaldo. Instala "
                          "python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o "
                          "python-gobject + spice-gtk (Arch).")
    if protocol == PROTOCOL_SPICE and mode == MODE_EXTERNAL:
        return _QCA.translate(
            "VirtualMachineManagerApp",
            "SPICE en ventana externa. Necesitas spicy (spice-gtk) o "
            "remote-viewer (virt-viewer).") \
            if _QCA else ("SPICE en ventana externa. Necesitas spicy (spice-gtk) o "
                          "remote-viewer (virt-viewer).")
    return ""

# ---------------------------------------------------------------------------
# Detección de capacidades para elegir entre embed y visor externo
# ---------------------------------------------------------------------------
def is_x11_session() -> bool:
    """True si la sesión gráfica actual es X11 (no Wayland).

    Se comprueba primero XDG_SESSION_TYPE; si no está definida, se mira
    WAYLAND_DISPLAY (Wayland) y DISPLAY (X11/Xwayland) como respaldo.
    """
    st = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
    if st == "x11":
        return True
    if st == "wayland":
        return False
    if os.environ.get("WAYLAND_DISPLAY"):
        return False
    return bool(os.environ.get("DISPLAY"))


def embedded_spice_available() -> bool:
    """True si spice-gtk tiene binding Python (gi.repository.SpiceClientGtk)."""
    try:
        import gi
        gi.require_version("SpiceClientGtk", "3.0")
        from gi.repository import SpiceClientGtk  # noqa: F401
        return True
    except Exception:
        return False


def can_embed_spice() -> bool:
    """True si podemos embeber SPICE dentro de la app.

    Requiere:
      • Sesión X11 (XEmbed no funciona en Wayland).
      • Binding Python de spice-gtk.

    Cuando es False, el llamador debe usar visor externo directamente, sin
    construir SpiceConsoleWidget. Esto evita el bug anterior: el widget
    intentaba embeber, fallaba, y su propio __init__ lanzaba un visor
    externo, duplicando el lanzamiento que hacía el dispatcher.
    """
    if not is_x11_session():
        return False
    return embedded_spice_available()
