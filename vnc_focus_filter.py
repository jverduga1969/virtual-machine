# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Filtro de foco y captura de teclado para el widget VNC embebido.

## Qué problema resuelve

En una VM, las teclas "especiales" (Meta/Super, Ctrl+Alt+F1..F12, Alt+Tab,
etc.) suelen ser interceptadas ANTES de que la aplicación las vea:

  - El gestor de ventanas registra grabs pasivos (XGrabKey) para sus
    atajos globales.
  - El servidor X11 maneja directamente Ctrl+Alt+F1..F12 (cambio de VT).
  - En Wayland, el compositor se reserva Meta/Super por diseño de seguridad.

Hay dos capas donde hay que intervenir:

  1. Dentro de Qt: `QWidget.grabKeyboard()` reroutea TODAS las teclas al
     widget, incluso si otro widget de la app tiene el foco. Esto basta
     para teclas que la app ya recibe, pero NO evita que el WM/compositor
     robe las teclas antes.

  2. A nivel X11: `XGrabKeyboard` sobre la ventana top-level hace que el
     servidor X envíe TODO el teclado a nuestra ventana, ignorando los
     grabs pasivos del WM. Por protocolo, un XGrabKeyboard activo tiene
     prioridad sobre los XGrabKey pasivos.

## Estrategia

- Al recibir `FocusIn` en el widget VNC → activar captura:
    * grabKeyboard() a nivel Qt
    * XGrabKeyboard sobre la ventana top-level
    * Instalar un filtro a nivel de QApplication que bloquee
      ShortcutOverride mientras la captura está activa (evita que atajos
      internos de la app consuman teclas destinadas a la VM).

- Al recibir `FocusOut` → liberar todo.

- Al recibir clic con botón izquierdo y el widget no tiene foco → setFocus.

## Limitación conocida: Wayland

En sesiones Wayland (KDE Plasma 6, GNOME, Sway, etc.) `XGrabKeyboard` no
aplica: el compositor se reserva Meta/Super por seguridad y no hay API
estándar para que una app se lo salte. Si el usuario necesita esas teclas
dentro de la VM, la única solución fiable es iniciar sesión en X11. El
filtro lo detecta y lo reporta en la consola para que el usuario lo sepa.
"""
import os
import time

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QApplication


class VNCFocusKeyboardFilter(QObject):
    """Captura el teclado cuando el widget VNC gana foco; lo libera al perderlo."""

    def __init__(self, app, vnc_widget):
        super().__init__(vnc_widget)
        self._app = app
        self._vnc = vnc_widget
        self._qt_grabbed = False
        self._x11_grabbed = False
        self._active = False
        self._app_filter_installed = False

    # ------------------------------------------------------------------ utils

    def _log(self, msg):
        try:
            self._app.log_message(msg)
        except Exception:
            pass

    # ---------------------------------------------------------------- activate

    def _activate(self):
        if self._active:
            return
        self._active = True
        self._install_app_filter()
        self._do_qt_grab()
        # El grab X11 necesita la ventana ya mapeada. Cuando llega FocusIn
        # normalmente ya lo está, pero por si acaso reintentamos un par de
        # veces con un pequeño retardo.
        self._try_x11_grab(attempts=3)

    def _deactivate(self):
        if not self._active:
            return
        self._active = False
        self._do_qt_ungrab()
        self._do_x11_ungrab()
        self._remove_app_filter()

    # ------------------------------------------------------------------ grabs

    def _do_qt_grab(self):
        try:
            self._vnc.grabKeyboard()
            self._qt_grabbed = True
        except Exception as e:
            self._qt_grabbed = False
            self._log(f"[VNC] No se pudo aplicar grabKeyboard(): {e}")

    def _do_qt_ungrab(self):
        if not self._qt_grabbed:
            return
        try:
            self._vnc.releaseKeyboard()
        except Exception:
            pass
        self._qt_grabbed = False

    def _try_x11_grab(self, attempts=3):
        try:
            import x11_keyboard_grab
        except ImportError:
            self._log(
                "[VNC] python-xlib no está instalado; no se puede capturar el "
                "teclado a nivel X11 (Meta/Super y atajos del WM seguirán "
                "interceptándose). Instala con: pip install python-xlib"
            )
            return False

        session = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
        if session and session != "x11":
            self._log(
                f"[VNC] Sesión '{session}' (no X11): las teclas que el compositor "
                "se reserva (Meta/Super, cambio de VT, atajos globales) NO pueden "
                "capturarse desde una aplicación. Es una limitación del protocolo "
                "Wayland, no un bug. Si necesitas esas teclas dentro de la VM, "
                "inicia sesión en X11."
            )
            return False

        # Usamos la ventana TOP-LEVEL, no el winId del widget hijo: Qt suele
        # usar una sola ventana nativa por top-level y el winId de un QWidget
        # hijo puede devolver la del padre o forzar la creación de una nueva.
        try:
            top = self._vnc.window()
            win_id = int(top.winId()) if top is not None else int(self._vnc.winId())
        except Exception as e:
            self._log(f"[VNC] No se pudo obtener el winId de la ventana: {e}")
            return False

        for i in range(max(1, attempts)):
            if x11_keyboard_grab.grab_keyboard(win_id):
                self._x11_grabbed = True
                self._log(
                    f"[VNC] XGrabKeyboard activo (winId=0x{win_id:x}). "
                    "Las teclas especiales se envían a la VM; "
                    "haz clic fuera del widget para liberar el teclado."
                )
                return True
            if i < attempts - 1:
                # Retardo corto: la ventana puede estar terminando de mapearse.
                time.sleep(0.1)

        self._log(
            "[VNC] XGrabKeyboard falló repetidamente. Si estás en X11 y tienes "
            "python-xlib instalado, prueba a hacer clic sobre el widget VNC "
            "una vez más — a veces el primer intento ocurre antes de que el "
            "WM termine de mapear la ventana."
        )
        return False

    def _do_x11_ungrab(self):
        if not self._x11_grabbed:
            return
        try:
            import x11_keyboard_grab
            x11_keyboard_grab.ungrab_keyboard()
        except Exception:
            pass
        self._x11_grabbed = False
        self._log("[VNC] Teclado liberado; atajos del host restaurados.")

    # ---------------------------------------------------------- app-level filter

    def _install_app_filter(self):
        if self._app_filter_installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
            self._app_filter_installed = True

    def _remove_app_filter(self):
        if not self._app_filter_installed:
            return
        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except Exception:
                pass
        self._app_filter_installed = False

    # ------------------------------------------------------------------ events

    def eventFilter(self, obj, event):
        # --- Eventos que llegan al propio widget VNC ---
        if obj is self._vnc:
            etype = event.type()
            if etype == QEvent.Type.FocusIn:
                self._activate()
                return False
            if etype == QEvent.Type.FocusOut:
                self._deactivate()
                return False
            if etype == QEvent.Type.MouseButtonPress:
                if not self._vnc.hasFocus():
                    self._vnc.setFocus()
                return False
            # NO interceptamos KeyPress/KeyRelease aquí: el widget los recibirá
            # por el flujo normal de Qt (gracias a grabKeyboard + foco) y su
            # propio event()/keyPressEvent los procesará como fue diseñado.
            return False

        # --- Eventos a nivel de QApplication ---
        if self._active:
            etype = event.type()
            # ShortcutOverride: Qt pide permiso antes de disparar un atajo de
            # la app. Si lo aceptamos, el atajo NO se dispara y la tecla
            # sigue su curso hacia el widget con el foco (nuestro VNC).
            if etype == QEvent.Type.ShortcutOverride:
                event.accept()
                return True
        return False

    # ------------------------------------------------------------------ cleanup

    def detach(self):
        """Libera cualquier captura pendiente. Llamar antes de destruir el widget."""
        self._deactivate()
