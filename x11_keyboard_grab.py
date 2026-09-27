# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Captura exclusiva de teclado a nivel X11 para la consola VNC en pantalla
completa.

## Por qué hace falta

`QWidget.grabKeyboard()` (lo que ya usa `_open_vnc_fullscreen`) solo cambia
a QUÉ WIDGET DENTRO DE LA APP se le entregan los eventos de teclado que Qt
ya recibió. No impide que el escritorio (KDE, GNOME, XFCE, el propio
gestor de ventanas...) intercepte una combinación ANTES de que le llegue a
cualquier aplicación. Meta/Super (para abrir el lanzador o el "Overview"),
Ctrl+Alt+F2 (cambiar de TTY), Alt+Tab, etc. suelen estar registrados como
atajos globales directamente en el servidor X11 mediante `XGrabKey`, en una
capa por debajo de cualquier cosa que Qt pueda controlar. Por eso, aunque el
widget VNC tenga el foco de Qt, esas teclas "se activan en el host" en vez
de llegar a la VM.

La única forma de evitarlo es pedirle al propio servidor X11 que, mientras
dure la pantalla completa, mande TODO el teclado a nuestra ventana sin
excepción: eso es exactamente `XGrabKeyboard`. Por protocolo X11, una
captura activa (`XGrabKeyboard`) tiene prioridad sobre las capturas pasivas
por tecla (`XGrabKey`) que el escritorio haya registrado, así que mientras
el grab esté activo esos atajos globales simplemente no se disparan.

## Límites conocidos

- Solo funciona en sesiones X11 (Xorg, o Xwayland en los casos donde la app
  corre como cliente X11 clásico). Bajo Wayland "puro" no existe un
  equivalente al que una aplicación normal pueda acceder: el propio
  protocolo se lo reserva al compositor por motivos de seguridad. En ese
  caso todas las funciones de este módulo son no-ops seguros y se sigue
  dependiendo únicamente del grab de Qt (mejor que nada, pero no evita que
  el compositor robe Meta/Super).
- Requiere el paquete `python-xlib` (`pip install python-xlib`). Si no está
  instalado, también se vuelve no-op en vez de fallar.
- El grab solo puede pedirse cuando la ventana ya está mapeada en pantalla;
  por eso quien llama a `grab_keyboard` debe hacerlo con un pequeño retraso
  después de `showFullScreen()` (ver vm_lifecycle_mixin.py).
"""
import os
import logging

log = logging.getLogger("X11KeyboardGrab")

_display = None
_warned_missing_xlib = False


def is_x11_session() -> bool:
    """True solo si esta sesión de escritorio es X11 propiamente dicho.

    Se usa XDG_SESSION_TYPE en vez de solo comprobar la variable DISPLAY,
    porque Xwayland también expone DISPLAY en sesiones Wayland y ahí un
    XGrabKeyboard normalmente no sirve para nada (el compositor Wayland no
    lo respeta salvo que la app corra explícitamente vía Xwayland).
    """
    return os.environ.get("XDG_SESSION_TYPE", "").strip().lower() == "x11"


def grab_keyboard(window_id: int) -> bool:
    """Intenta una captura exclusiva de teclado sobre la ventana nativa
    `window_id` (el winId() de un QWidget ya mostrado en pantalla).

    Devuelve True si el grab se aplicó. Devuelve False —sin lanzar
    excepción— si no es una sesión X11, falta python-xlib, o el grab
    falló por cualquier otro motivo; en ese caso el llamador debe seguir
    funcionando igual, solo que sin esta protección extra.
    """
    global _display, _warned_missing_xlib

    if not is_x11_session():
        return False

    try:
        from Xlib import X
        from Xlib.display import Display
    except ImportError:
        if not _warned_missing_xlib:
            _warned_missing_xlib = True
            log.warning(
                "python-xlib no está instalado (pip install python-xlib): "
                "no se puede hacer una captura exclusiva de teclado a nivel "
                "X11. Meta/Super y combinaciones que el escritorio "
                "intercepta globalmente seguirán sin llegar a la VM."
            )
        return False

    try:
        if _display is None:
            _display = Display()
        window = _display.create_resource_object("window", window_id)
        result = window.grab_keyboard(
            owner_events=True,
            pointer_mode=X.GrabModeAsync,
            keyboard_mode=X.GrabModeAsync,
            time=X.CurrentTime,
        )
        _display.sync()
        if result != 0:  # 0 == GrabSuccess
            log.warning(f"XGrabKeyboard no tuvo éxito (código {result}).")
            return False
        log.debug("Captura exclusiva de teclado X11 activada.")
        return True
    except Exception:
        log.exception("Fallo al intentar la captura de teclado X11.")
        return False


def ungrab_keyboard():
    """Libera la captura exclusiva, si estaba activa. Seguro de llamar
    aunque nunca se haya logrado un grab (no-op en ese caso)."""
    global _display

    if _display is None:
        return
    try:
        from Xlib import X
        _display.ungrab_keyboard(X.CurrentTime)
        _display.sync()
        log.debug("Captura exclusiva de teclado X11 liberada.")
    except Exception:
        log.exception("Fallo al liberar la captura de teclado X11.")
    finally:
        try:
            _display.close()
        except Exception:
            pass
        _display = None
