# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""CenteredVNCWidget: envoltorio sobre vnc_widget.QVNCWidget (el paquete que
genera setup_vnc_widget.py a partir de qvncwidget, portado a PyQt6).

QVNCWidget ya escala el framebuffer de la VM manteniendo la relación de
aspecto para que quepa dentro del widget (Qt.AspectRatioMode.KeepAspectRatio),
pero lo dibuja siempre anclado en la esquina superior izquierda (drawImage en
0,0). Cuando la relación de aspecto de la VM no coincide con la del widget
(por ejemplo una VM a 1280x720 dentro de un panel más alto, o la ventana de
pantalla completa de un monitor con otra proporción), el resultado queda
descentrado, con la franja "sobrante" siempre del mismo lado.

Esta subclase añade dos cosas sin tocar el código generado/portado:

1. Centrado del dibujo escalado (modo "ajustar a la ventana", el de
   siempre): paintEvent y _getRemoteRel centran la imagen y ajustan el
   mapeo del mouse en consecuencia.

2. Modo "tamaño real" (sin escalar): pensado para usarse dentro de un
   QScrollArea. El widget adopta el tamaño EXACTO del framebuffer de la VM
   (setFixedSize) y dibuja 1:1, sin ningún reescalado. Si eso no cabe en el
   viewport visible, es el QScrollArea contenedor quien añade barras de
   desplazamiento — nada de esto se resuelve "recortando" ni "encogiendo"
   la imagen, así que sirve como alternativa cuando la VM usa una
   resolución que no cabe en la pantalla del host y no se puede/quiere
   reescalar (por ejemplo, para verla a resolución nativa 1:1).

Se alterna entre ambos modos con set_fit_to_window(True/False).
"""
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtWidgets import QSizePolicy

from vnc_widget import QVNCWidget


class CenteredVNCWidget(QVNCWidget):
    """QVNCWidget con dos modos de presentación:

    - Ajustar a la ventana (por defecto): escala manteniendo proporción y
      centra el resultado dentro del widget.
    - Tamaño real: sin escalar, a resolución 1:1; pensado para vivir dentro
      de un QScrollArea que aporte las barras de desplazamiento cuando el
      framebuffer de la VM no quepa en el espacio visible.

    En todo lo demás (teclado, conexión, RFB) se comporta igual que
    QVNCWidget.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fit_to_window = True
        # En cuanto se conoce la resolución real de la VM (tras el
        # handshake RFB), hay que volver a aplicar el modo actual: en modo
        # "tamaño real" es cuando recién se puede fijar el tamaño exacto del
        # widget (antes de eso vncWidth/vncHeight todavía son 0).
        self.onInitialResize.connect(
            lambda _size: self.set_fit_to_window(
                getattr(self, "_fit_to_window", True)
            )
        )

    def set_fit_to_window(self, enabled: bool):
        """Cambia entre "ajustar a la ventana" (enabled=True) y "tamaño
        real" (enabled=False, pensado para un QScrollArea).

        IMPORTANTE: este método puede llamarse ANTES de que el handshake
        RFB haya completado. En ese momento el widget heredado todavía no
        tiene los atributos vncWidth / vncHeight (los crea
        QVNCWidget.initDisplay() cuando el servidor envía el tamaño del
        framebuffer). Por eso leemos esos atributos con getattr: si aún
        no existen, simplemente no fijamos tamaño y esperamos a la señal
        onInitialResize, que volverá a llamar a este método.
        """
        self._fit_to_window = enabled

        # Lectura defensiva: si aún no hay handshake, los valores son 0.
        vw = int(getattr(self, "vncWidth", 0) or 0)
        vh = int(getattr(self, "vncHeight", 0) or 0)

        if enabled:
            # Modo ajustar: sin mínimo ni máximo. El scroll area
            # (widgetResizable=True) estira el widget al viewport.
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16_777_215, 16_777_215)  # QWIDGETSIZE_MAX
            try:
                self.setSizePolicy(
                    QSizePolicy.Policy.Ignored,
                    QSizePolicy.Policy.Ignored,
                )
            except Exception:
                pass
        else:
            # Modo tamaño real: fijamos el widget al framebuffer del guest
            # SOLO si ya conocemos sus dimensiones. Si no, no hacemos nada
            # y esperamos a que llegue el handshake RFB.
            if vw > 0 and vh > 0:
                self.setMinimumSize(vw, vh)
                self.setMaximumSize(vw, vh)

        # Forzar al layout padre a reevaluar.
        try:
            self.updateGeometry()
        except Exception:
            pass
        self.update()


    def _scaled_rect(self):
        """Rectángulo (en coordenadas del widget) donde se dibuja la imagen
        de la VM ya escalada y centrada. None si aún no hay framebuffer."""
        if self.backbuffer is None:
            return None
        scaled = self.backbuffer.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.frontbuffer = scaled
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        return QRect(x, y, scaled.width(), scaled.height())

    def sizeHint(self) -> QSize:
        """Tamaño sugerido del widget.

        En modo 'ajustar a ventana' devolvemos un valor pequeño para que
        el QScrollArea (con widgetResizable=True) estire el widget hasta
        el viewport. En modo 'tamaño real' devolvemos el tamaño del
        framebuffer del guest, para que el scroll area muestre barras.

        Se leen los atributos con getattr porque Qt puede llamar a este
        método durante la construcción del widget, antes de que __init__
        termine de asignar _fit_to_window y vncWidth/vncHeight.
        """
        fit = getattr(self, "_fit_to_window", True)
        vw = int(getattr(self, "vncWidth", 0) or 0)
        vh = int(getattr(self, "vncHeight", 0) or 0)
        if not fit and vw > 0 and vh > 0:
            return QSize(vw, vh)
        return QSize(320, 240)

    def minimumSizeHint(self) -> QSize:
        """Tamaño mínimo del widget.

        Mismo tratamiento defensivo que sizeHint(): leer con getattr
        para tolerar llamadas durante la construcción.
        """
        fit = getattr(self, "_fit_to_window", True)
        vw = int(getattr(self, "vncWidth", 0) or 0)
        vh = int(getattr(self, "vncHeight", 0) or 0)
        if not fit and vw > 0 and vh > 0:
            return QSize(vw, vh)
        return QSize(1, 1)


    def resizeEvent(self, event):
        """Fuerza un repaint cuando el widget cambia de tamaño.

        Sin esto, el framebuffer puede quedar dibujado al tamaño
        anterior hasta el siguiente frame del VNC, lo que produce
        el efecto de 'imagen grande/pequeña' durante el cambio de
        resolución del guest.
        """
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, a0):
        """Dibuja el framebuffer del guest en el widget.

        Defensivo: se leen los atributos con getattr porque Qt puede
        llamar a paintEvent DURANTE la construcción del widget, antes
        de que super().__init__() termine de asignar backbuffer y
        frontbuffer. Sin esto, Qt lanza AttributeError en el primer
        intento de pintar y el widget nunca llega a mostrarse.
        """
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.GlobalColor.black)

        backbuffer = getattr(self, "backbuffer", None)
        if backbuffer is None:
            painter.end()
            return

        fit = getattr(self, "_fit_to_window", True)

        if fit:
            # Modo ajustar: reescalar y centrar.
            try:
                scaled = backbuffer.scaled(
                    self.width(), self.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                try:
                    self.frontbuffer = scaled
                except Exception:
                    pass
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawImage(x, y, scaled)
            except Exception:
                painter.end()
                return
        else:
            # Modo tamaño real: dibujar 1:1.
            try:
                self.frontbuffer = backbuffer
            except Exception:
                pass
            painter.drawImage(0, 0, backbuffer)

        painter.end()


    def _getRemoteRel(self, ev: QMouseEvent) -> tuple:
        # QMouseEvent.localPos() ya no existe en versiones recientes de
        # PyQt6 (fue reemplazado por position(), que devuelve QPointF en
        # coordenadas del widget). Se intenta position() primero y se cae a
        # localPos() solo por compatibilidad con bindings más viejos.
        if hasattr(ev, "position"):
            pos = ev.position()
        else:
            pos = ev.localPos()

        if not self._fit_to_window:
            # Tamaño real: mapeo directo, 1 píxel del widget = 1 píxel de
            # la VM. QScrollArea ya se encarga de que `pos` venga en
            # coordenadas del widget completo (no del viewport recortado),
            # así que no hace falta compensar el scroll aquí.
            max_x = max(self.vncWidth - 1, 0)
            max_y = max(self.vncHeight - 1, 0)
            x = min(max(pos.x(), 0), max_x)
            y = min(max(pos.y(), 0), max_y)
            return int(x), int(y)

        rect = self._scaled_rect()
        if rect is None or rect.width() == 0 or rect.height() == 0:
            return 0, 0

        # Posición del clic relativa al área realmente dibujada (restando el
        # margen que la centra), recortada a los límites de esa área para
        # que un clic justo en el borde/franja no se traduzca fuera de
        # rango.
        local_x = min(max(pos.x() - rect.x(), 0), rect.width())
        local_y = min(max(pos.y() - rect.y(), 0), rect.height())

        xPos = (local_x / rect.width()) * self.vncWidth
        yPos = (local_y / rect.height()) * self.vncHeight

        return int(xPos), int(yPos)
