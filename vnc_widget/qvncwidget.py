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
# QOpenGLWidget vive en PyQt6.QtOpenGLWidgets (no en QtWidgets) desde Qt6.
# Lo importamos por separado; si no está disponible, la clase GL queda desactivada.

from vnc_widget.rfb import RFBClient
from vnc_widget.rfbhelpers import RFBPixelformat, RFBInput

log = logging.getLogger("QVNCWidget")

class QVNCWidget(QWidget, RFBClient):

    onInitialResize = pyqtSignal(QSize)

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

        # vnc_desktopsize_v4: health check + keepalive cada 300 ms.
        #
        # Health check: si el hilo RFB murio (deadlock, conexion rota,
        # etc.), se relanza automaticamente. Antes habia que pulsar
        # "Forzar reconexion" a mano cada vez que el hilo moria.
        #
        # Keepalive: QEMU solo responde a requests NO-incrementales.
        # Los incrementales que envia el main loop tras cada frame se
        # quedan sin respuesta, dejando el widget congelado en el
        # ultimo frame. Con un keepalive de 300ms aseguramos que el
        # frame se refresca 3 veces por segundo, suficiente para ver
        # la progresion de arranque fluida.
        self._vnc_keepalive_timer = QTimer(self)
        # vnc_desktopsize_v5: 500ms en vez de 300ms. Menos carga y
        # menos parpadeo por exceso de full refreshes.
        self._vnc_keepalive_timer.setInterval(500)
        self._vnc_keepalive_timer.timeout.connect(self._vnc_health_tick)
        self._vnc_keepalive_timer.start()
        self._vnc_last_reconnect = 0.0
        self._vnc_reconnecting = False

    def _vnc_health_tick(self):
        """vnc_desktopsize_v4: health check + keepalive.

        1. Si el hilo RFB murio, relanzar la conexion.
        2. Si esta vivo y conectado, pedir un full refresh para
           asegurar que el frame no se quede congelado por falta de
           respuestas incrementales de QEMU.
        """
        # vnc_desktopsize_v8: si el widget ya fue destruido (PyQt
        # mantiene el objeto Python pero el C++ subyacente puede
        # estar borrado), parar el timer y salir. Sin esto, cualquier
        # acceso (self.update, emit, etc.) lanza RuntimeError.
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
            # PyQt6 sin sip expuesto; continuar sin la comprobacion.
            pass
        except Exception:
            pass

        import time as _t
        # vnc_desktopsize_v5: guard contra reconexiones superpuestas.
        # Si ya estamos reconectando, no hacer nada. Ademas, el
        # FileNotFoundError que salia al final del log (socket Unix
        # ya no existe porque la VM se apago) se captura y no deja
        # el flag colgado.
        if getattr(self, "_vnc_reconnecting", False):
            return
        # 1) Health check.
        try:
            if hasattr(self, "is_alive") and not self.is_alive():
                now = _t.monotonic()
                # Guardar contra tormentas: no reconectar mas de una
                # vez por segundo.
                if now - getattr(self, "_vnc_last_reconnect", 0.0) > 1.0:
                    self._vnc_last_reconnect = now
                    self._vnc_reconnecting = True
                    log.warning("RFB thread muerto; reconectando")
                    try:
                        self.reconnect()
                    except FileNotFoundError:
                        # Socket ya no existe (VM apagada). Silencioso:
                        # no es un error, el widget simplemente ya no
                        # tiene a donde conectarse.
                        log.info("Socket VNC no existe (¿VM apagada?)")
                    except Exception as e:
                        log.error(f"reconnect fallo: {e}")
                    finally:
                        self._vnc_reconnecting = False
                return
        except Exception:
            pass
        # 2) Keepalive: pedir full refresh.
        if not getattr(self, "_connected", False):
            return
        try:
            self.framebufferUpdateRequest(incremental=False)
        except Exception:
            pass

    def _vnc_force_full_refresh(self):
        """vnc_desktopsize_v3 (compat): pide un framebuffer update
        completo. Se conserva por si algun codigo externo lo invoca.
        """
        if not getattr(self, "_connected", False):
            return
        try:
            self.framebufferUpdateRequest(incremental=False)
        except Exception:
            pass

    def closeEvent(self, event):
        """vnc_desktopsize_v8: cierre ordenado del widget.

        Para el keepalive y cierra la conexion antes de que PyQt
        destruya el objeto C++. Sin esto, el hilo RFB puede seguir
        vivo un instante y llamar a metodos del widget ya borrado,
        lanzando RuntimeError.
        """
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

        # vnc_desktopsize_v6: NO tocar el backbuffer aqui. Recrearlo
        # (o rellenarlo de negro) causaba un flash visible durante
        # el handshake. Lo dejamos con el contenido anterior y lo
        # recreamos de forma lazy en el primer onRectangleUpdate con
        # el tamano nuevo (ver ahi abajo). El usuario ve la imagen
        # anterior estirada hasta que llegue el primer frame nuevo.
        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))

    def onDesktopResize(self, width: int, height: int):
        """Llamado cuando el servidor VNC notifica un cambio de resolución.

        vnc_desktopsize_v6: solo actualizamos las dimensiones. El
        backbuffer se recrea de forma lazy en el proximo
        onRectangleUpdate, rellenandolo con el frame anterior
        escalado como placeholder. Antes se recreaba aqui y se veia
        negro un instante durante cada cambio de resolucion.
        """
        log.info(f"Desktop resize: {width}x{height}")
        self.vncWidth = width
        self.vncHeight = height
        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))
        # NO recrear backbuffer, NO self.update() (el proximo rect
        # que llegue hara todo).

    def onRectangleUpdate(self,
            x: int, y: int, width: int, height: int, data: bytes):

        # vnc_desktopsize_v6: recreacion lazy del backbuffer.
        #   * Si es None: crear uno nuevo negro (primera conexion).
        #   * Si tiene dimensiones distintas a las actuales: crear
        #     uno del tamano nuevo, pero rellenandolo con el frame
        #     anterior escalado como placeholder. Asi no hay flash
        #     negro mientras llegan todos los rects del frame
        #     completo (que es lo que se veia antes).
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
        #log.debug("Paint event")
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
        # Dar foco al widget al hacer clic: así los eventos de teclado
        # llegan al widget y no a otros widgets de la app.
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
    # vnc_keysym_fix_v1: traduccion correcta Qt.Key -> keysym X11.
    #
    # Sin este mapa, las teclas especiales se enviaban con su codigo
    # de Qt (rango 0x01000000+) que en RFB significa "keysym Unicode"
    # (los 24 bits bajos son el codepoint). Por eso Ctrl se enviaba
    # como '!' (U+0021), Alt como '#' (U+0023), Meta como '"' (U+0022)
    # y Tab/Backspace/Flechas como codepoints invalidos.
    #
    # El mapa cubre solo teclas que NO son ASCII imprimible. Para el
    # resto (letras, digitos, simbolos) se usa ev.text(), que ya trae
    # el caracter tras aplicar la distribucion de teclado del host.
    _QT_KEY_TO_X11_KEYSYM = {
        Qt.Key.Key_Shift:     0xFFE1,  # Shift_L
        Qt.Key.Key_Control:   0xFFE3,  # Control_L
        Qt.Key.Key_Alt:       0xFFE9,  # Alt_L
        Qt.Key.Key_Meta:      0xFFEB,  # Super_L
        Qt.Key.Key_AltGr:     0xFFEA,  # Alt_R
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
        """Convierte un QKeyEvent al keysym X11 que espera RFB.

        vnc_keysym_fix_v1.
        """
        try:
            k = ev.key()
        except Exception:
            return 0
        # 1) Teclas especiales: mapa explicito.
        m = self._QT_KEY_TO_X11_KEYSYM.get(k)
        if m is not None:
            return m
        # 2) Caracteres imprimibles: usar el texto (ya aplicada la
        #    distribucion del host). El codepoint ASCII coincide con
        #    el keysym X11; para >127 se usa el rango Unicode keysym.
        try:
            text = ev.text()
        except Exception:
            text = ""
        if text:
            cp = ord(text[0])
            # Descartar caracteres de control (Ctrl+A da '\x01'): esos
            # NO son el keysym del caracter, son el efecto del modificador.
            # En ese caso caemos al ev.key() crudo (que para Ctrl+A es
            # 'A' = 0x41, el keysym correcto).
            if cp >= 0x20 and cp != 0x7F:
                if cp < 0x80:
                    return cp
                if cp <= 0x10FFFF:
                    return 0x01000000 + cp
        # 3) Fallback: devolver el codigo de Qt tal cual.
        try:
            return int(k)
        except Exception:
            return k if isinstance(k, int) else 0

    def focusNextPrevChild(self, _next: bool) -> bool:
        """vnc_keysym_fix_v1: bloquear la navegacion por Tab.

        Qt intercepta Tab/Backtab ANTES de keyPressEvent para mover el
        foco entre widgets. Devolviendo False aqui, le decimos que NO
        mueva el foco, y el evento sigue su curso hasta keyPressEvent,
        donde lo enviamos a la VM.
        """
        return False

    def keyPressEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return
        self.keyEvent(self._qt_key_to_keysym(ev), down=1)

    def keyReleaseEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return
        self.keyEvent(self._qt_key_to_keysym(ev), down=0)


# vnc_desktopsize_v3_qvnc_applied


# vnc_desktopsize_v4_qvnc_applied


# vnc_desktopsize_v5_qvnc_applied


# vnc_desktopsize_v6_qvnc_applied


# vnc_desktopsize_v8_qvnc_applied
