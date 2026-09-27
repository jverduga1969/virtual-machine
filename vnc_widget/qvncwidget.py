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
    pyqtSignal,
    QSemaphore
)
from PyQt6.QtGui import (
    QImage,
    QPaintEvent,
    QPainter,
    QColor,
    QBrush,
    QPixmap,
    QResizeEvent,
    QKeyEvent,
    QMouseEvent
)

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
)
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

    def start(self):
        self.startConnection()

    def stop(self):
        self.closeConnection()

    def onConnectionMade(self):
        log.info("VNC handshake done")

        self.setPixelFormat(RFBPixelformat.getRGB32())
        self.PIX_FORMAT = QImage.Format.Format_RGB32

        #self.setPixelFormat(RFBPixelformat.getRGB24())
        #self.PIX_FORMAT = QImage.Format.Format_RGB888

        #self.setPixelFormat(RFBPixelformat.getRGB16())
        #self.PIX_FORMAT = QImage.Format.Format_RGB16

        self.backbuffer = QImage(self.vncWidth, self.vncHeight, self.PIX_FORMAT)
        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))

    def onDesktopResize(self, width: int, height: int):
        """Llamado cuando el servidor VNC notifica un cambio de resolución.

        Recrea el backbuffer al nuevo tamaño para que los frames siguientes
        encajen. Sin esto, un cambio de resolución dentro de la VM (p. ej.
        al cambiar a pantalla completa) cortaría la imagen.
        """
        log.info(f"Desktop resize: {width}x{height}")
        self.vncWidth = width
        self.vncHeight = height
        self.backbuffer = QImage(self.vncWidth, self.vncHeight, self.PIX_FORMAT)
        self.onInitialResize.emit(QSize(self.vncWidth, self.vncHeight))
        self.update()

    def onRectangleUpdate(self,
            x: int, y: int, width: int, height: int, data: bytes):

        if self.backbuffer is None:
            log.warning("backbuffer is None")
            return
        else:
            log.debug("drawing backbuffer")

        #with open(f"{width}x{height}.data", "wb") as f:
        #    f.write(data)

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

    def keyPressEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return
        self.keyEvent(RFBInput.fromQKeyEvent(ev.key(), ev.text()), down=1)

    def keyReleaseEvent(self, ev: QKeyEvent):
        if self.readOnly:
            return
        self.keyEvent(RFBInput.fromQKeyEvent(ev.key(), ev.text()), down=0)

