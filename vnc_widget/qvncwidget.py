"""
Qt Widget for displaying VNC framebuffer using RFB protocol

(c) zocker-160 2024
licensed under GPLv3
"""

import logging
import time

from PyQt6.QtCore import (
    QSize,
    Qt,
    QTimer,
    pyqtSignal
)
from PyQt6.QtGui import (
    QImage,
    QPaintEvent,
    QPainter,
    QKeyEvent,
    QMouseEvent
)

from PyQt6.QtWidgets import QWidget

from vnc_widget.rfb import RFBClient
from vnc_widget.rfbhelpers import RFBPixelformat, RFBInput

log = logging.getLogger("QVNCWidget")

class QVNCWidget(QWidget, RFBClient):

    onInitialResize = pyqtSignal(QSize)
    # vnc_fullscreen_v2: el widget ya NO intenta fullscreenearse a sí
    # mismo. En su lugar emite señales y el host (console plugin)
    # decide cómo entrar/salir de pantalla completa, típicamente
    # reparentando el widget a una ventana fullscreen dedicada.
    fullscreen_toggle_requested = pyqtSignal()   # F11
    fullscreen_exit_requested = pyqtSignal()     # Ctrl+Alt+F
    fullscreen_changed = pyqtSignal(bool)        # informativo (retrocompat)

    def __init__(self, parent: QWidget,
                 host: str, port = 5900, password: str = None,
                 readOnly = False):
        super().__init__(
            parent=parent,
            host=host, port=port, password=password
        )
        self.readOnly = readOnly

        self.backbuffer: QImage = None
        self.frontbuffer: QImage = None

        self.setMouseTracking(not self.readOnly)
        self.setMinimumSize(1, 1) # make window scalable

        self.mouseButtonMask = 0

        # Buffer de teclas consumidas por atajos del host (F11,
        # Ctrl+Alt+F, Ctrl+Alt+G). Evita reenviar el release al guest
        # cuando el press fue absorbido.
        self._consumed_keys: set = set()

        self._vnc_keepalive_timer = QTimer(self)
        self._vnc_keepalive_timer.setInterval(500)
        self._vnc_keepalive_timer.timeout.connect(self._vnc_health_tick)
        self._vnc_keepalive_timer.start()
        self._vnc_last_reconnect = 0.0
        self._vnc_reconnecting = False

    # ------------------------------------------------------------------
    # API legacy: cualquier código que llame toggle_fullscreen() sigue
    # funcionando (emite la señal de toggle, el host decide).
    # ------------------------------------------------------------------
    def toggle_fullscreen(self):
        self.fullscreen_toggle_requested.emit()

    def _vnc_health_tick(self):
        try:
            from PyQt6 import sip as _sip
            if _sip.isdeleted(self):
                log.info("Widget destruido; parando keepalive")
                try:
                    self._vnc_keepalive_timer.stop()
                except Exception:
                    pass
                return
        except ImportError:
            pass
        except Exception:
            pass

        import time as _t
        if getattr(self, "_vnc_reconnecting", False):
            return
        try:
            if hasattr(self, "is_alive") and not self.is_alive():
                now = _t.monotonic()
                if now - getattr(self, "_vnc_last_reconnect", 0.0) > 1.0:
                    self._vnc_last_reconnect = now
                    self._vnc_reconnecting = True
                    log.warning("RFB thread muerto; reconectando")
                    try:
                        self.reconnect()
                    except FileNotFoundError:
                        log.info("Socket VNC no existe (¿VM apagada?)")
                    except Exception as e:
                        log.error(f"reconnect fallo: {e}")
                    finally:
                        self._vnc_reconnecting = False
                return
        except Exception:
            pass
        if not getattr(self, "_connected", False):
            return
        try:
            self.framebufferUpdateRequest(incremental=False)
        except Exception:
            pass

    def _vnc_force_full_refresh(self):
        if not getattr(self, "_connected", False):
            return
        try:
            self.framebufferUpdateRequest(incremental=False)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self._vnc_keepalive_timer.stop()
        except Exception:
            pass
        try:
            self.closeConnection()
        except Exception:
            pass
        try:
            super().closeEvent(event)
        except Exception:
            pass

    def start(self):
        self.startConnection()

    def stop(self):
        self.closeConnection()

    def onConnectionMade(self):
        log.info("VNC handshake done")

        self.setPixelFormat(RFBPixelformat.getRGB32())
        self.PIX_FORMAT = QImage.Format.Format_RGB32

        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))

    def onDesktopResize(self, width: int, height: int):
        log.info(f"Desktop resize: {width}x{height}")
        self.vncWidth = width
        self.vncHeight = height
        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))

    def onRectangleUpdate(self,
            x: int, y: int, width: int, height: int, data: bytes):

        if self.backbuffer is None:
            self.backbuffer = QImage(
                self.vncWidth, self.vncHeight, self.PIX_FORMAT)
            self.backbuffer.fill(0)
        elif (self.backbuffer.width() != self.vncWidth
              or self.backbuffer.height() != self.vncHeight):
            _old = self.backbuffer
            _scaled = _old.scaled(
                self.vncWidth, self.vncHeight,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self.backbuffer = QImage(
                self.vncWidth, self.vncHeight, self.PIX_FORMAT)
            _p = QPainter(self.backbuffer)
            _p.drawImage(0, 0, _scaled)
            _p.end()

        log.debug("drawing backbuffer")

        t1 = time.time()

        painter = QPainter(self.backbuffer)
        painter.drawImage(x, y, QImage(data, width, height, self.PIX_FORMAT))
        painter.end()

        log.debug(f"painting took: {(time.time() - t1)*1e3} ms")

        del painter
        del data

    def onFramebufferUpdateFinished(self):
        log.debug("FB Update finished")
        self.update()

    def paintEvent(self, a0: QPaintEvent):
        painter = QPainter(self)

        if self.backbuffer is None:
            log.debug("backbuffer is None")
            painter.fillRect(0, 0, self.width(), self.height(), Qt.GlobalColor.black)

        else:
            self.frontbuffer = self.backbuffer.scaled(
                    self.width(), self.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            painter.drawImage(0, 0, self.frontbuffer)

        painter.end()

    # Mouse events

    def mousePressEvent(self, ev: QMouseEvent):
        self.setFocus()
        if self.readOnly or not self.frontbuffer:
            return
        self.mouseButtonMask = RFBInput.fromQMouseEvent(ev, True, self.mouseButtonMask)
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if self.readOnly or not self.frontbuffer:
            return
        self.mouseButtonMask = RFBInput.fromQMouseEvent(ev, False, self.mouseButtonMask)
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self.readOnly or not self.frontbuffer:
            return
        self.pointerEvent(*self._getRemoteRel(ev), self.mouseButtonMask)

    def _getRemoteRel(self, ev: QMouseEvent) -> tuple:
        xPos = (ev.position().x() / self.frontbuffer.width()) * self.vncWidth
        yPos = (ev.position().y() / self.frontbuffer.height()) * self.vncHeight
        return int(xPos), int(yPos)

    # Key events
    _QT_KEY_TO_X11_KEYSYM = {
        Qt.Key.Key_Shift:     0xFFE1,
        Qt.Key.Key_Control:   0xFFE3,
        Qt.Key.Key_Alt:       0xFFE9,
        Qt.Key.Key_Meta:      0xFFEB,
        Qt.Key.Key_AltGr:     0xFFEA,
        Qt.Key.Key_CapsLock:  0xFFE5,
        Qt.Key.Key_Tab:       0xFF09,
        Qt.Key.Key_Backtab:   0xFE20,
        Qt.Key.Key_Backspace: 0xFF08,
        Qt.Key.Key_Return:    0xFF0D,
        Qt.Key.Key_Enter:     0xFF8D,
        Qt.Key.Key_Escape:    0xFF1B,
        Qt.Key.Key_Delete:    0xFFFF,
        Qt.Key.Key_Insert:    0xFF63,
        Qt.Key.Key_Home:      0xFF50,
        Qt.Key.Key_End:       0xFF57,
        Qt.Key.Key_PageUp:    0xFF55,
        Qt.Key.Key_PageDown:  0xFF56,
        Qt.Key.Key_Left:      0xFF51,
        Qt.Key.Key_Up:        0xFF52,
        Qt.Key.Key_Right:     0xFF53,
        Qt.Key.Key_Down:      0xFF54,
        Qt.Key.Key_Print:     0xFF61,
        Qt.Key.Key_ScrollLock:0xFF14,
        Qt.Key.Key_Pause:     0xFF13,
        Qt.Key.Key_Menu:      0xFF67,
        Qt.Key.Key_Help:      0xFF6A,
        Qt.Key.Key_F1:  0xFFBE,
        Qt.Key.Key_F2:  0xFFBF,
        Qt.Key.Key_F3:  0xFFC0,
        Qt.Key.Key_F4:  0xFFC1,
        Qt.Key.Key_F5:  0xFFC2,
        Qt.Key.Key_F6:  0xFFC3,
        Qt.Key.Key_F7:  0xFFC4,
        Qt.Key.Key_F8:  0xFFC5,
        Qt.Key.Key_F9:  0xFFC6,
        Qt.Key.Key_F10: 0xFFC7,
        Qt.Key.Key_F11: 0xFFC8,
        Qt.Key.Key_F12: 0xFFC9,
    }

    def _qt_key_to_keysym(self, ev: QKeyEvent) -> int:
        try:
            k = ev.key()
        except Exception:
            return 0
        m = self._QT_KEY_TO_X11_KEYSYM.get(k)
        if m is not None:
            return m
        try:
            text = ev.text()
        except Exception:
            text = ""
        if text:
            cp = ord(text[0])
            if cp >= 0x20 and cp != 0x7F:
                # Latin-1 (acentos, ñ, ¿, ¡...): keysym directo < 0x100,
                # que es como QEMU espera recibirlos. Unicode solo para > 0xFF.
                if cp < 0x100:
                    return cp
                if cp <= 0x10FFFF:
                    return 0x01000000 + cp
        try:
            return int(k)
        except Exception:
            return k if isinstance(k, int) else 0

    def _qt_key_to_evdev(self, ev: QKeyEvent) -> int:
        """Keycode evdev (Linux) de un evento Qt.
        En Linux, nativeScanCode() es el keycode X11 (evdev + 8). Devuelve 0 si no disponible."""
        try:
            sc = int(ev.nativeScanCode())
        except Exception:
            return 0
        if sc > 8:
            return sc - 8
        return 0

    def _send_key(self, ev: QKeyEvent, down: int):
        """Envia la tecla usando QEMU Extended Key Event (keycode evdev directo,
        si el server lo soporta) o fallback a keysyms RFB clasicos."""
        keysym = self._qt_key_to_keysym(ev)
        if getattr(self, "ext_key_event_supported", False):
            keycode = self._qt_key_to_evdev(ev)
            if keycode:
                self.extKeyEvent(down, keysym, keycode)
                return
        self.keyEvent(keysym, down=down)

    def focusNextPrevChild(self, _next: bool) -> bool:
        return False

    def keyPressEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return

        key = ev.key()
        mods = ev.modifiers()
        is_ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        is_alt = bool(mods & Qt.KeyboardModifier.AltModifier)

        # F11: toggle pantalla completa (via señal, host decide)
        if key == Qt.Key.Key_F11 and not is_ctrl and not is_alt:
            self.fullscreen_toggle_requested.emit()
            self._consumed_keys.add(int(key))
            ev.accept()
            return

        # Ctrl+Alt+F: salir de pantalla completa
        if is_ctrl and is_alt and key == Qt.Key.Key_F:
            self.fullscreen_exit_requested.emit()
            self._consumed_keys.add(int(key))
            ev.accept()
            return

        # Ctrl+Alt+G: liberar teclado del guest (no-op, solo log)
        if is_ctrl and is_alt and key == Qt.Key.Key_G:
            log.info("Teclado liberado del guest (Ctrl+Alt+G)")
            self._consumed_keys.add(int(key))
            ev.accept()
            return

        self._send_key(ev, 1)

    def keyReleaseEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return

        key = int(ev.key())
        if key in self._consumed_keys:
            self._consumed_keys.discard(key)
            ev.accept()
            return

        self._send_key(ev, 0)
