# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_grid_delegate.py — delegate para pintar las VMs como tarjetas.

Marcador: vm_grid_view_v2_card.

Dibuja cada item del QListWidget como una tarjeta con:
  - Recuadro redondeado (radio 10).
  - Borde de 1–2 px según estado (normal / hover / seleccionada).
  - Fondo: palette(base) normal, palette(alternate-base) en hover,
    #dbeafe en seleccionada, o el color de grupo (alfa 80) si existe.
  - Icono 96×96 centrado arriba.
  - Nombre (elidido si es muy largo) + punto de estado con color.

El delegate lee los datos del item:
  - UserRole     → nombre de la VM.
  - UserRole+1   → estado ("running" | "paused" | "stopped").
  - UserRole+2   → color de grupo (hex "#rrggbb") o "".

No toca ni señales ni comportamiento: solo pinta.
"""
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle


_VM_USER_ROLE      = 256
_VM_STATE_ROLE     = 257
_VM_COLOR_ROLE     = 258


class VmCardDelegate(QStyledItemDelegate):
    """Pinta cada VM como una tarjeta con recuadro."""

    CARD_MARGIN     = 6
    CARD_RADIUS     = 10
    ICON_SIZE       = 96
    PADDING_TOP     = 8
    PADDING_BOTTOM  = 8
    LINE_GAP        = 4

    STATE_COLOR = {
        "running": "#2e7d32",
        "paused":  "#f57c00",
        "stopped": "#9e9e9e",
    }
    STATE_LABEL = {
        "running": "Encendida",
        "paused":  "Pausada",
        "stopped": "Apagada",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        # Cachear una fuente en negrita para el nombre de la VM.
        self._bold = QFont()
        self._bold.setBold(True)

    # ------------------------------------------------------------------
    # sizeHint: Qt lo usa para calcular el tamaño de cada celda.
    # ------------------------------------------------------------------
    def sizeHint(self, option, index):
        return QSize(170, 190)

    # ------------------------------------------------------------------
    # paint
    # ------------------------------------------------------------------
    def paint(self, painter, option, index):
        painter.save()
        try:
            self._paint_card(painter, option, index)
        finally:
            painter.restore()

    def _paint_card(self, painter, option, index):
        # --- Geometría del recuadro ---
        r = option.rect.adjusted(
            self.CARD_MARGIN, self.CARD_MARGIN,
            -self.CARD_MARGIN, -self.CARD_MARGIN,
        )
        if r.width() < 60 or r.height() < 60:
            return

        # --- Datos del item ---
        name = str(index.data(_VM_USER_ROLE) or "")
        state = str(index.data(_VM_STATE_ROLE) or "stopped")
        group_color = str(index.data(_VM_COLOR_ROLE) or "")

        # --- Estado de selección / hover ---
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered  = bool(option.state & QStyle.StateFlag.State_MouseOver)

        # --- Paleta base ---
        pal = option.palette
        base       = pal.color(pal.ColorRole.Base)
        alt_base   = pal.color(pal.ColorRole.AlternateBase)
        mid        = pal.color(pal.ColorRole.Mid)
        text_col   = pal.color(pal.ColorRole.Text)

        # --- Colores del recuadro ---
        if selected:
            bg     = QColor("#dbeafe")
            border = QColor("#1e40af")
            border_w = 2
        elif hovered:
            bg     = alt_base
            border = QColor("#2e6fd6")
            border_w = 2
        elif group_color and group_color.startswith("#") and len(group_color) == 7:
            # Fondo con el color del grupo alfa 80 (más suave que el 150 de la lista).
            gc = QColor(group_color)
            gc.setAlpha(80)
            bg     = gc
            border = mid
            border_w = 1
        else:
            bg     = base
            border = mid
            border_w = 1

        # --- Pintar el recuadro ---
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(border)
        pen.setWidth(border_w)
        painter.setPen(pen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(
            r.adjusted(0, 0, -1, -1), self.CARD_RADIUS, self.CARD_RADIUS,
        )

        # --- Icono (96×96) ---
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_y = r.top() + self.PADDING_TOP
        icon_x = r.left() + (r.width() - self.ICON_SIZE) // 2
        icon_rect = QRect(icon_x, icon_y, self.ICON_SIZE, self.ICON_SIZE)
        if icon is not None and not icon.isNull():
            icon.paint(painter, icon_rect)
        else:
            # Placeholder si no hay icono.
            painter.setPen(QPen(mid))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(icon_rect, 6, 6)

        # --- Nombre (línea 1) ---
        text_top = icon_rect.bottom() + self.LINE_GAP + 2
        name_rect = QRect(
            r.left() + 6, text_top,
            r.width() - 12, 20,
        )
        painter.setPen(QPen(text_col))
        painter.setFont(self._bold)
        fm = QFontMetrics(self._bold)
        name_elided = fm.elidedText(name, Qt.TextElideMode.ElideRight, name_rect.width())
        painter.drawText(
            name_rect,
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            name_elided,
        )

        # --- Estado (línea 2): punto de color + etiqueta ---
        state_text = self.STATE_LABEL.get(state, "Apagada")
        state_col  = QColor(self.STATE_COLOR.get(state, "#9e9e9e"))

        # Fuente normal (no bold) para el estado.
        normal_font = QFont(option.font)
        painter.setFont(normal_font)
        fm2 = QFontMetrics(normal_font)

        state_y = name_rect.bottom() + 2
        # Ancho total = punto (8) + separación (4) + texto.
        dot_size = 8
        text_w   = fm2.horizontalAdvance(state_text)
        total_w  = dot_size + 4 + text_w
        start_x  = r.left() + (r.width() - total_w) // 2

        # Punto de color.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(state_col))
        painter.drawEllipse(
            start_x, state_y + (fm2.height() - dot_size) // 2,
            dot_size, dot_size,
        )

        # Etiqueta del estado.
        painter.setPen(QPen(state_col))
        state_rect = QRect(
            start_x + dot_size + 4, state_y,
            text_w + 2, fm2.height(),
        )
        painter.drawText(
            state_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            state_text,
        )
