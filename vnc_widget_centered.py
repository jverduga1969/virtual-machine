# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""CenteredVNCWidget: envoltorio sobre vnc_widget.QVNCWidget.

Añade sobre el widget base dos modos de presentación:

1. "Ajustar a la ventana" (por defecto):
   escala el framebuffer manteniendo la relación de aspecto y lo centra
   dentro del widget. La VM se ve entera, sin barras; si la relación de
   aspecto no coincide con la del widget, aparecen bandas negras a los
   lados.

2. "Zoom manual":
   el widget adopta el tamaño EXACTO del framebuffer multiplicado por un
   factor (vncWidth*pct/100 × vncHeight*pct/100) y dibuja el backbuffer
   escalado a ese tamaño. Pensado para vivir dentro de un QScrollArea
   que añade barras de desplazamiento cuando no cabe. El "tamaño real"
   (1:1, sin reescalado) es el caso particular pct=100.

Se alterna entre ambos modos con:

    widget.set_zoom(None)   → ajustar a la ventana.
    widget.set_zoom(150)    → zoom al 150% del framebuffer.
    widget.set_zoom(100)    → tamaño real 1:1.

Por compatibilidad con el código anterior, set_fit_to_window(True/False)
sigue existiendo como alias:

    set_fit_to_window(True)  == set_zoom(None)
    set_fit_to_window(False) == set_zoom(100)
"""
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtWidgets import QSizePolicy

from vnc_widget import QVNCWidget


class CenteredVNCWidget(QVNCWidget):
    """QVNCWidget con dos modos de presentación (ver docstring del módulo)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # None = ajustar a ventana. int = zoom manual en porcentaje.
        self._zoom_percent = None
        # Al conocer la resolución real de la VM (handshake RFB),
        # reaplicar el tamaño correspondiente al modo actual.
        self.onInitialResize.connect(
            lambda _size: self._apply_size_for_mode()
        )

    # ------------------------------------------------------------------
    # Modo de presentación
    # ------------------------------------------------------------------

    def set_zoom(self, percent):
        """Cambia el modo de presentación.

        percent=None → ajustar a la ventana.
        percent=int  → zoom manual al porcentaje indicado (1..n).
        """
        if percent is None:
            self._zoom_percent = None
        else:
            try:
                pct = int(percent)
            except (TypeError, ValueError):
                pct = 100
            self._zoom_percent = max(1, pct)
        self._apply_size_for_mode()

    def set_fit_to_window(self, enabled: bool):
        """Alias de compatibilidad con la versión anterior del wrapper.

        Preferir set_zoom() en el código nuevo.
        """
        self.set_zoom(None if enabled else 100)

    def zoom_percent(self):
        """None si estamos en modo ajustar; int si estamos en zoom manual."""
        return self._zoom_percent

    # ------------------------------------------------------------------
    # Cálculo del tamaño
    # ------------------------------------------------------------------

    def _target_pixel_size(self):
        """Tamaño en píxeles del widget en modo zoom manual, o None.

        Devuelve None si estamos en modo ajustar, o si todavía no se
        conoce la resolución real de la VM (vncWidth/vncHeight aún son 0
        antes del handshake RFB).
        """
        if self._zoom_percent is None:
            return None
        vw = int(getattr(self, "vncWidth", 0) or 0)
        vh = int(getattr(self, "vncHeight", 0) or 0)
        if vw <= 0 or vh <= 0:
            return None
        tw = max(1, int(round(vw * self._zoom_percent / 100.0)))
        th = max(1, int(round(vh * self._zoom_percent / 100.0)))
        return (tw, th)

    def _apply_size_for_mode(self):
        """Aplica el tamaño adecuado según el modo actual.

        - Modo ajustar: sin mínimo ni máximo, SizePolicy.Ignored; el
          QScrollArea (widgetResizable=True) estira el widget al
          viewport.
        - Modo zoom: tamaño fijo = vncWidth*pct/100 × vncHeight*pct/100,
          SizePolicy.Fixed. El QScrollArea (widgetResizable=False) añade
          barras si no cabe.

        Además de fijar min/max, se llama a resize() explícitamente.
        Dentro de un QScrollArea con widgetResizable(False), min/max
        solos NO cambian el tamaño actual del widget: el widget sigue
        midiendo lo que midiera (por ejemplo el viewport), hasta que un
        layout pass lo reajuste. Sin resize() explícito el zoom no se
        ve.
        """
        target = self._target_pixel_size()

        if target is None:
            # Modo ajustar (o zoom manual antes del handshake RFB:
            # en ese caso volveremos aquí en onInitialResize).
            try:
                self.setSizePolicy(
                    QSizePolicy.Policy.Ignored,
                    QSizePolicy.Policy.Ignored,
                )
            except Exception:
                pass
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16_777_215, 16_777_215)
        else:
            tw, th = target
            try:
                self.setSizePolicy(
                    QSizePolicy.Policy.Fixed,
                    QSizePolicy.Policy.Fixed,
                )
            except Exception:
                pass
            self.setMinimumSize(tw, th)
            self.setMaximumSize(tw, th)
            try:
                self.resize(tw, th)
            except Exception:
                pass

        try:
            self.updateGeometry()
        except Exception:
            pass
        self.update()

    # ------------------------------------------------------------------
    # sizeHint / minimumSizeHint
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:
        target = self._target_pixel_size()
        if target is not None:
            return QSize(*target)
        # Modo ajustar: devolver algo pequeño para que el scroll area
        # estire el widget al viewport.
        return QSize(320, 240)

    def minimumSizeHint(self) -> QSize:
        target = self._target_pixel_size()
        if target is not None:
            return QSize(*target)
        return QSize(1, 1)

    def resizeEvent(self, event):
        """Fuerza repaint al cambiar de tamaño.

        Sin esto, el framebuffer puede quedar dibujado al tamaño anterior
        hasta el siguiente frame del VNC.
        """
        super().resizeEvent(event)
        self.update()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------

    def paintEvent(self, a0):
        """Dibuja el framebuffer del guest.

        Defensivo: se lee backbuffer con getattr porque Qt puede llamar a
        paintEvent durante la construcción del widget, antes de que
        super().__init__() termine.
        """
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.GlobalColor.black)

        backbuffer = getattr(self, "backbuffer", None)
        if backbuffer is None:
            painter.end()
            return

        target = self._target_pixel_size()
        if target is not None:
            # Zoom manual: pintar el backbuffer escalado a (tw, th)
            # exactos desde (0, 0). El widget ya tiene ese tamaño fijo,
            # así que no hay márgenes.
            tw, th = target
            try:
                scaled = backbuffer.scaled(
                    tw, th,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                try:
                    self.frontbuffer = scaled
                except Exception:
                    pass
                painter.drawImage(0, 0, scaled)
            except Exception:
                pass
        else:
            # Ajustar a ventana: escalar respetando aspecto y centrar.
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
                pass

        painter.end()

    def _scaled_rect(self):
        """Compatibilidad: rect donde se pinta la imagen en modo ajustar."""
        if getattr(self, "backbuffer", None) is None:
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

    # ------------------------------------------------------------------
    # Ratón
    # ------------------------------------------------------------------

    def _getRemoteRel(self, ev: QMouseEvent) -> tuple:
        # QMouseEvent.position() en PyQt6 moderno; localPos() por
        # compatibilidad con bindings más viejos.
        if hasattr(ev, "position"):
            pos = ev.position()
        else:
            pos = ev.localPos()

        vw = int(getattr(self, "vncWidth", 0) or 0)
        vh = int(getattr(self, "vncHeight", 0) or 0)
        if vw <= 0 or vh <= 0:
            return 0, 0

        target = self._target_pixel_size()
        if target is not None:
            # Zoom manual: 1 píxel del guest = scale píxeles del widget.
            # El QScrollArea ya entrega `pos` en coordenadas del widget
            # completo (no del viewport recortado), así que no hay que
            # compensar el scroll.
            scale = self._zoom_percent / 100.0
            gx = int(pos.x() / scale) if scale > 0 else 0
            gy = int(pos.y() / scale) if scale > 0 else 0
            gx = min(max(gx, 0), vw - 1)
            gy = min(max(gy, 0), vh - 1)
            return gx, gy

        # Modo ajustar: como la versión anterior.
        if getattr(self, "backbuffer", None) is None:
            return 0, 0
        scaled = self.backbuffer.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x_off = (self.width() - scaled.width()) // 2
        y_off = (self.height() - scaled.height()) // 2
        local_x = min(max(pos.x() - x_off, 0), scaled.width())
        local_y = min(max(pos.y() - y_off, 0), scaled.height())
        gx = int((local_x / scaled.width()) * vw) if scaled.width() else 0
        gy = int((local_y / scaled.height()) * vh) if scaled.height() else 0
        gx = min(max(gx, 0), vw - 1)
        gy = min(max(gy, 0), vh - 1)
        return gx, gy
