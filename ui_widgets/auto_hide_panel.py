from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent, QPropertyAnimation, QEasingCurve

class AutoHidePanel(QWidget):
    """
    Un panel que se puede colapsar. Si el ratón se acerca al borde,
    se expande automáticamente.
    """
    def __init__(self, content_widget: QWidget, expanded_width: int = 250, collapsed_width: int = 5, parent=None):
        super().__init__(parent)
        self.expanded_width = expanded_width
        self.collapsed_width = collapsed_width
        self.is_expanded = True
        self.is_pinned = True
        
        self.setFixedWidth(expanded_width)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_widget)
        
        # Animación
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation2 = QPropertyAnimation(self, b"maximumWidth")
        self.animation2.setDuration(200)
        self.animation2.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setMouseTracking(True)
        self.installEventFilter(self)
        content_widget.setMouseTracking(True)
        content_widget.installEventFilter(self)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.expand()
        else:
            self.collapse()

    def expand(self):
        if not self.is_expanded:
            self.is_expanded = True
            self._animate(self.expanded_width)

    def collapse(self):
        if self.is_expanded and not self.is_pinned:
            self.is_expanded = False
            self._animate(self.collapsed_width)

    def _animate(self, target_width):
        self.animation.setEndValue(target_width)
        self.animation2.setEndValue(target_width)
        self.animation.start()
        self.animation2.start()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self.expand()
        elif event.type() == QEvent.Type.Leave:
            # Verificar si el ratón realmente salió del widget
            if not self.rect().contains(self.mapFromGlobal(self.cursor().pos())):
                self.collapse()
        return super().eventFilter(obj, event)
