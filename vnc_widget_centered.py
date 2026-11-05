from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtWidgets import QSizePolicy
from vnc_widget import QVNCWidget

class CenteredVNCWidget(QVNCWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom_percent = None
        self.onInitialResize.connect(lambda _size: self._apply_size_for_mode())

    def set_zoom(self, percent):
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
        self.set_zoom(None if enabled else 100)

    def _target_pixel_size(self):
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
        target = self._target_pixel_size()
        if target is None:
            try:
                self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            except Exception:
                pass
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16_777_215, 16_777_215)
        else:
            tw, th = target
            try:
                self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
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

    def sizeHint(self) -> QSize:
        target = self._target_pixel_size()
        if target is not None:
            return QSize(*target)
        return QSize(320, 240)

    def minimumSizeHint(self) -> QSize:
        target = self._target_pixel_size()
        if target is not None:
            return QSize(*target)
        return QSize(1, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.GlobalColor.black)
        backbuffer = getattr(self, "backbuffer", None)
        if backbuffer is None:
            painter.end()
            return
        target = self._target_pixel_size()
        if target is not None:
            tw, th = target
            try:
                scaled = backbuffer.scaled(tw, th, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                try:
                    self.frontbuffer = scaled
                except Exception:
                    pass
                painter.drawImage(0, 0, scaled)
            except Exception:
                pass
        else:
            try:
                scaled = backbuffer.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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

    def _getRemoteRel(self, ev: QMouseEvent) -> tuple:
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
            scale = self._zoom_percent / 100.0
            gx = int(pos.x() / scale) if scale > 0 else 0
            gy = int(pos.y() / scale) if scale > 0 else 0
            gx = min(max(gx, 0), vw - 1)
            gy = min(max(gy, 0), vh - 1)
            return gx, gy
        if getattr(self, "backbuffer", None) is None:
            return 0, 0
        scaled = self.backbuffer.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x_off = (self.width() - scaled.width()) // 2
        y_off = (self.height() - scaled.height()) // 2
        local_x = min(max(pos.x() - x_off, 0), scaled.width())
        local_y = min(max(pos.y() - y_off, 0), scaled.height())
        gx = int((local_x / scaled.width()) * vw) if scaled.width() else 0
        gy = int((local_y / scaled.height()) * vh) if scaled.height() else 0
        gx = min(max(gx, 0), vw - 1)
        gy = min(max(gy, 0), vh - 1)
        return gx, gy