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
import time

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
        # spice_embedded_tcp_v1: aceptamos tanto una ruta de socket Unix
        # (tradicional) como una URI "spice://host:port" o
        # "spice+unix:///path" o un puerto suelto ("5930"). El backend
        # console_backend.qemu_console_args emite SPICE por TCP
        # 127.0.0.1:PORT (info["socket"] = info["uri"] =
        # "spice://127.0.0.1:PORT"); antes el widget solo entendia
        # paths de archivo y se quedaba esperando un socket que nunca
        # aparecia.
        self._socket_path = socket_path
        self._endpoint = self._classify_endpoint(socket_path)
        self._vm_name = vm_name
        self._log = log_func or (lambda msg: None)

        self._gtk_window = None
        self._gtk_display = None
        self._gtk_timer = None
        self._embedded = False
        self._external_proc = None   # legacy: ya no se usa
        self._qt_window = None

        # spice_widget_no_spawn_v1: el widget declara el resultado
        # del intento de embed sin lanzar procesos externos. El
        # mixin (vm_lifecycle_mixin._sync_spice_widget) consulta
        # estos atributos y, si no pudo embeber, llama a
        # _sync_external_viewer, que registra el PID y aplica el
        # anti-bucle.
        self.embed_available = True
        self.embed_failure_reason = ""

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

    # ------------------------------------------------------------ endpoints

    @staticmethod
    def _classify_endpoint(raw):
        """Clasifica el destino SPICE a partir del string recibido.

        Marcador: spice_embedded_tcp_v1.

        Acepta:
          - ""                          -> sin destino.
          - "spice://host:port"         -> TCP.
          - "spice+unix:///path/sock"   -> Unix (URI).
          - "5930" (solo digitos)       -> TCP 127.0.0.1:5930.
          - "/path/sock" (ruta cruda)   -> Unix (archivo).

        Devuelve dict con:
          - kind: "empty" | "tcp_uri" | "unix_uri" | "unix_path"
          - uri:  URI lista para SpiceSession.set_property("uri", ...)
          - path: (solo unix) ruta del archivo de socket
          - port: (solo tcp por numero suelto) puerto entero
        """
        import urllib.parse as _up
        s = str(raw or "").strip()
        if not s:
            return {"kind": "empty", "uri": "", "path": ""}
        if s.startswith("spice+unix://"):
            path = _up.unquote(s[len("spice+unix://"):])
            return {"kind": "unix_uri", "uri": s, "path": path}
        if s.startswith("spice://"):
            return {"kind": "tcp_uri", "uri": s, "path": ""}
        if s.isdigit():
            port = int(s)
            return {"kind": "tcp_uri",
                    "uri": f"spice://127.0.0.1:{port}",
                    "path": "", "port": port}
        return {"kind": "unix_path",
                "uri": f"spice+unix://{s}", "path": s}

    def _endpoint_uri(self):
        return self._endpoint.get("uri") or ""

    def _extract_port(self):
        """Puerto TCP del endpoint, o None si no aplica."""
        if self._endpoint.get("kind") != "tcp_uri":
            return None
        import urllib.parse as _up
        u = _up.urlparse(self._endpoint["uri"])
        return u.port or self._endpoint.get("port")

    def _endpoint_ready(self):
        """True si el destino parece listo para intentar la conexion.

        - TCP: se prueba una conexion rapida al host:puerto (0.25 s).
        - Unix: se comprueba que el archivo de socket existe.
        """
        kind = self._endpoint.get("kind")
        if kind in (None, "empty"):
            return False
        if kind in ("unix_path", "unix_uri"):
            p = self._endpoint.get("path") or ""
            return bool(p) and os.path.exists(p)
        if kind == "tcp_uri":
            import socket as _s
            import urllib.parse as _up
            u = _up.urlparse(self._endpoint["uri"])
            host = u.hostname or "127.0.0.1"
            port = u.port or self._endpoint.get("port")
            if not port:
                return False
            s = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            s.settimeout(0.25)
            try:
                s.connect((host, int(port)))
                return True
            except Exception:
                return False
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return False

    # ------------------------------------------------------------------ embed

    def _try_embed(self):
        """Punto de entrada del intento de embed.

        Marcador: spice_embed_abandon_v1.

        HISTORICO (2026-10-14):
        Se intento embeber la consola SPICE dentro de la app usando
        QWidget.createWindowContainer + QWindow.fromWinId con la
        GdkWindow del SpiceDisplay. Se hicieron siete iteraciones
        sucesivas validando:
          - Nombres de clase de spice-gtk 0.42 (Session vs SpiceSession,
            Display vs SpiceDisplay).
          - Constructor de SpiceDisplay con session= en lugar de
            set_property("session", ...).
          - GtkSession para clipboard y auto-resize.
          - session.connect() + main_channel.connect() en dos pasos
            (el segundo dispara la creacion de los canales Display,
            Inputs y Cursor).
          - Espera bloqueante al SpiceDisplayChannel antes del XEmbed.
          - XEmbed del display.get_window() y no del win.get_window().
          - Gtk.Window sin show_all() para no dejar una ventana blanca
            flotante.

        Resultado final: el XID del SpiceDisplay (0x4a00046) queda
        como HERMANO de la ventana principal de la app en la raiz del
        X server, no como HIJO del contenedor Qt (0x4a0004a). Qt6
        crea un QWindow sobre el XID recibido y lo reparenta, pero
        deja la ventana original fuera, rellenando el contenedor con
        restos del framebuffer (mosaico de pestañas). No hay forma
        limpia de evitarlo con las APIs publicas de Qt6.

        Qt6 elimino QX11EmbedContainer (la clase de Qt5 que hacia
        esto bien). No hay equivalente oficial. La via correcta seria
        implementar XEmbed a mano con python-xlib (reparent,
        resize, eventos de teclado/raton, foco), que es un proyecto
        aparte de varias horas. Se deja documentado como pendiente
        futuro (marcador spice_embed_via_xlib_v1).

        DECISION: usar spicy externo como camino oficial. Es estable,
        ya funciona, y el boton "Ventana externa" lo abre bien. Esta
        funcion va directa al fallback sin intentar embed.
        """
        # spice_widget_no_spawn_v1: NO lanzamos el visor externo
        # desde aqui. Solo declaramos que el embed no es posible.
        # El mixin se encarga del visor externo.
        self._mark_no_embed(
            "embed deshabilitado (Qt6 + XEmbed incompatible; "
            "ver marcador spice_embed_abandon_v1)"
        )
        return

        # ---- Codigo historico del embed (2026-10-14) ----
        # Se deja aqui como referencia para una futura implementacion
        # via python-xlib. NO se ejecuta.
        #
        # Gtk, SpiceGLib, SpiceGtk = _gtk_spice()
        # if Gtk is None:
        #     self._fallback_external("spice-gtk sin binding Python")
        #     return
        # if not _is_x11():
        #     self._fallback_external("Sesion no X11 (Wayland puro)")
        #     return
        # if not self._endpoint_ready():
        #     QTimer.singleShot(400, self._try_embed)
        #     return
        #
        # SessionCls = (getattr(SpiceGLib, "Session", None)
        #               or getattr(SpiceGLib, "SpiceSession", None))
        # DisplayCls = (getattr(SpiceGtk, "Display", None)
        #               or getattr(SpiceGtk, "SpiceDisplay", None))
        # GtkSessionCls = getattr(SpiceGtk, "GtkSession", None)
        # ...
        # (ver script scripts/fix_spice_embed_v1.sh,
        #  fix_spice_embed_v2.sh, fix_spice_embed_v3.sh para el flujo
        #  completo que se probo)

    def _pump_gtk(self):
        try:
            from gi.repository import Gtk
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
        except Exception:
            pass

    # --------------------------------------------------------------- fallback

    def _mark_no_embed(self, reason):
        """Declara que el embed no es posible. NO lanza procesos.

        Marcador: spice_widget_no_spawn_v1.

        El mixin consulta self.embed_available / embed_failure_reason
        tras crear el widget y decide qué hacer (lanzar visor
        externo, marcar _spice_embed_disabled, etc.). El widget solo
        actualiza su placeholder y sus atributos.
        """
        self.embed_available = False
        self.embed_failure_reason = str(reason or "")
        self._log(f"[SPICE] No se puede embeber: {reason}")
        # Placeholder honesto: el widget NO se ha embebido. El mixin
        # sobrescribira este texto o lanzara el visor externo, pero si
        # alguien lo deja suelto, al menos no miente.
        self._placeholder.setText(
            "Consola SPICE no embebida en la app.\n\n"
            f"Motivo: {reason}.\n\n"
            "Se abrirá en ventana externa (spicy / remote-viewer)."
        )

    def stop(self):
        if self._gtk_timer is not None:
            self._gtk_timer.stop(); self._gtk_timer = None
        if self._gtk_window is not None:
            try: self._gtk_window.destroy()
            except Exception: pass
            self._gtk_window = None
        # spice_widget_no_spawn_v1: el widget ya no gestiona
        # procesos externos. El visor externo lo controla el mixin
        # (vm_lifecycle_mixin._external_viewers). Este stop() solo
        # limpia recursos GTK/Qt.
        # El antiguo _external_proc queda como atributo legacy.

# spice_embedded_tcp_v1

# spice_embed_v1_applied

# spice_embed_v2_applied

# spice_embed_v3_applied

# spice_embed_abandon_v1_applied

# spice_widget_no_spawn_v1

# spice_widget_no_spawn_1b
