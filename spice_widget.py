# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Widget SPICE embebido en Qt, con respaldo en visor externo.

Estrategia:
1. Si spice-gtk tiene binding Python y estamos en X11, creamos un
   Gtk.Window con un SpiceDisplay, obtenemos su XID y lo embebemos con
   QWindow.fromWinId() + createWindowContainer().
2. Si no, lanzamos un visor externo (spicy/remote-viewer) y el widget
   muestra un placeholder con instrucciones.

El bucle de eventos de GTK se procesa desde un QTimer: GTK no necesita su
propio main loop, se intercala con el de Qt.
"""
import os
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from console_backend import (
    PROTOCOL_SPICE, console_uri, find_spice_viewer, build_viewer_args,
)


def _gtk_spice():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("SpiceClientGLib", "2.0")
        gi.require_version("SpiceClientGtk", "3.0")
        from gi.repository import Gtk, SpiceClientGLib, SpiceClientGtk
        return Gtk, SpiceClientGLib, SpiceClientGtk
    except Exception:
        return None, None, None


def _is_x11():
    if os.environ.get("XDG_SESSION_TYPE", "").strip().lower() == "x11":
        return True
    if os.environ.get("WAYLAND_DISPLAY"):
        return False
    return bool(os.environ.get("DISPLAY"))


class SpiceConsoleWidget(QWidget):
    """Contenedor para la consola SPICE de una VM.

    Parámetros:
        parent: widget padre Qt.
        socket_path: socket SPICE que expone QEMU (-spice unix=on,addr=...).
        vm_name: solo para mensajes.
        log_func: función opcional para escribir en la consola de progreso.
    """

    def __init__(self, parent=None, socket_path="", vm_name="", log_func=None):
        super().__init__(parent)
        self._socket_path = socket_path
        self._vm_name = vm_name
        self._log = log_func or (lambda msg: None)

        self._gtk_window = None
        self._gtk_display = None
        self._gtk_timer = None
        self._embedded = False
        self._external_proc = None
        self._qt_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._layout = layout

        self._placeholder = QLabel("Preparando consola SPICE…")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._placeholder.setStyleSheet(
            "background: #1e1e1e; color: #ccc; padding: 20px; font-size: 12px;"
        )
        layout.addWidget(self._placeholder, 1)

        self._try_embed()

    # ------------------------------------------------------------------ embed

    def _try_embed(self):
        Gtk, SpiceGLib, SpiceGtk = _gtk_spice()
        if Gtk is None:
            self._log("[SPICE] spice-gtk no tiene binding Python; se usará visor externo.")
            self._fallback_external("spice-gtk (gi.repository.SpiceClientGtk) no disponible")
            return
        if not _is_x11():
            self._log("[SPICE] Sesión no X11; XEmbed no funciona. Se usará visor externo.")
            self._fallback_external("Sesión no X11 (Wayland puro)")
            return
        if not self._socket_path or not os.path.exists(self._socket_path):
            # El socket lo crea QEMU al arrancar; si aún no está, reintentamos.
            self._placeholder.setText("Esperando socket SPICE de QEMU…")
            QTimer.singleShot(400, self._try_embed)
            return

        try:
            # 1) Sesión SPICE y su conexión al socket de QEMU.
            session = SpiceGLib.SpiceSession()
            session.set_property("uri", f"spice+unix://{self._socket_path}")

            # 2) Widget SpiceDisplay dentro de un Gtk.Window embebible.
            win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            win.set_title(f"SPICE — {self._vm_name or 'VM'}")
            win.set_default_size(800, 600)
            display = SpiceGtk.SpiceDisplay()
            display.set_property("session", session)
            display.set_property("resize-guest", True)
            display.set_property("scaling", True)
            win.add(display)
            win.realize()          # asigna el XID nativo
            win.show_all()
            win.hide()             # solo queremos su XID

            # 3) XID del Gtk.Window.
            gdk_window = win.get_window()
            if gdk_window is None:
                raise RuntimeError("Gtk.Window.get_window() devolvió None")
            from gi.repository import GdkX11
            xid = int(GdkX11.X11Window.get_xid(gdk_window))

            # 4) Embeber en Qt.
            self._qt_window = QWindow.fromWinId(xid)
            container = QWidget.createWindowContainer(self._qt_window, self)
            container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self._layout.replaceWidget(self._placeholder, container)
            self._placeholder.hide()

            # 5) Conectar la sesión (algunas versiones lo exigen explícitamente).
            try:
                session.connect_to_uri(
                    f"spice+unix://{self._socket_path}", None, 0
                )
            except Exception as e:
                self._log(f"[SPICE] connect_to_uri: {e}")

            # 6) Bombear eventos GTK desde un QTimer (no usamos Gtk.main()).
            self._gtk_timer = QTimer(self)
            self._gtk_timer.setInterval(15)
            self._gtk_timer.timeout.connect(self._pump_gtk)
            self._gtk_timer.start()

            self._gtk_window = win
            self._gtk_display = display
            self._embedded = True
            self._log(f"[SPICE] Consola embebida lista ({self._socket_path}).")

        except Exception as e:
            self._log(f"[SPICE] No se pudo embeber: {e}")
            self._fallback_external(f"Error al embeber: {e}")

    def _pump_gtk(self):
        try:
            from gi.repository import Gtk
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
        except Exception:
            pass

    # --------------------------------------------------------------- fallback

    def _fallback_external(self, reason):
        viewer, template = find_spice_viewer()
        if not viewer or not self._socket_path:
            self._placeholder.setText(
                f"Consola SPICE no disponible.\n\nMotivo: {reason}.\n\n"
                "Para embeber SPICE instala:\n"
                "  • Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0\n"
                "  • Arch:          python-gobject spice-gtk\n\n"
                "Para ventana externa instala:\n"
                "  • spicy (spice-gtk) o remote-viewer (virt-viewer)"
            )
            return
        try:
            uri = console_uri(PROTOCOL_SPICE, self._socket_path)
            # {sock} se sustituye con la ruta CRUDA (spicy no URL-
            # decode); {uri} con la versión encoded (remote-viewer).
            args = [viewer] + build_viewer_args(
                template, self._socket_path, uri
            )
            self._external_proc = subprocess.Popen(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self._placeholder.setText(
                f"SPICE abierto en ventana externa con {os.path.basename(viewer)}.\n\n"
                f"Motivo por el que no se embebió: {reason}.\n\n"
                "Si prefieres la consola dentro de la app, instala el binding "
                "Python de spice-gtk."
            )
            self._log(f"[SPICE] Visor externo: {' '.join(args)}")
        except Exception as e:
            self._placeholder.setText(f"No se pudo lanzar visor externo: {e}")
            self._log(f"[SPICE] Fallo al lanzar visor externo: {e}")

    # -------------------------------------------------------------------- API

    def stop(self):
        if self._gtk_timer is not None:
            self._gtk_timer.stop(); self._gtk_timer = None
        if self._gtk_window is not None:
            try: self._gtk_window.destroy()
            except Exception: pass
            self._gtk_window = None
        if self._external_proc is not None:
            try: self._external_proc.terminate()
            except Exception: pass
            self._external_proc = None