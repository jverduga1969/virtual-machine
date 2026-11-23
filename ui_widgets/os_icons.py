"""Iconos del listado de VMs según el sistema operativo invitado.

Se dibujan con QPainter para no depender de archivos de imagen ni de fuentes
con emoji (que no están garantizadas en todos los hosts).
"""

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap

_CACHE = {}

_COLORES = {
    "linux": "#2f6fed",
    "windows": "#0078d4",
    "macos": "#4a4a4a",
    "android": "#3ddc84",
    "other": "#607d8b",
}


def normalize_platform(valor) -> str:
    """Normaliza el texto de la UI (o de vms.json) a una clave corta."""
    texto = (valor or "").strip().lower()
    if not texto:
        return "other"
    if any(k in texto for k in ("macos", "mac os", "apple", "os x", "darwin")):
        return "macos"
    if "win" in texto:
        return "windows"
    if "android" in texto:
        return "android"
    if "linux" in texto or "gnu" in texto:
        return "linux"
    return "other"


def _dibujar_windows(p, size):
    cell = max(3, int(size * 0.18))
    gap = max(2, int(size * 0.06))
    x0 = (size - (2 * cell + gap)) // 2
    y0 = x0
    for dx in (0, cell + gap):
        for dy in (0, cell + gap):
            p.fillRect(x0 + dx, y0 + dy, cell, cell, Qt.GlobalColor.white)


def _dibujar_linux(p, size):
    fuente = QFont()
    fuente.setBold(True)
    fuente.setPointSize(max(8, int(size * 0.42)))
    p.setFont(fuente)
    p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, ">_")


def _dibujar_macos(p, size):
    fuente = QFont()
    fuente.setBold(True)
    fuente.setPointSize(max(7, int(size * 0.30)))
    p.setFont(fuente)
    p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "mac")


def _dibujar_android(p, size, color_fondo):
    ancho = max(8, int(size * 0.46))
    alto = max(6, int(size * 0.34))
    x = (size - ancho) // 2
    y = int(size * 0.36)

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(Qt.GlobalColor.white))
    p.drawRoundedRect(x, y, ancho, alto, max(2, alto // 3), max(2, alto // 3))

    ojo = max(2, int(size * 0.05))
    p.setBrush(QBrush(QColor(color_fondo)))
    p.drawEllipse(x + ancho // 3 - ojo // 2, y + alto // 2 - ojo // 2, ojo, ojo)
    p.drawEllipse(x + 2 * ancho // 3 - ojo // 2, y + alto // 2 - ojo // 2, ojo, ojo)

    p.setPen(QPen(Qt.GlobalColor.white, max(1, size // 16)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(x + ancho // 4, y, x + ancho // 5, y - int(size * 0.13))
    p.drawLine(x + 3 * ancho // 4, y, x + 4 * ancho // 5, y - int(size * 0.13))


def _dibujar_otro(p, size):
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(Qt.GlobalColor.white, max(1, size // 16)))
    x, y = int(size * 0.18), int(size * 0.22)
    w, h = int(size * 0.64), int(size * 0.44)
    p.drawRoundedRect(x, y, w, h, 3, 3)
    p.drawLine(size // 2, y + h, size // 2, y + h + int(size * 0.10))
    p.drawLine(int(size * 0.36), y + h + int(size * 0.12),
               int(size * 0.64), y + h + int(size * 0.12))

    fuente = QFont()
    fuente.setBold(True)
    fuente.setPointSize(max(7, int(size * 0.28)))
    p.setFont(fuente)
    p.drawText(QRect(x, y, w, h), Qt.AlignmentFlag.AlignCenter, "?")


def os_icon(plataforma, size: int = 32) -> QIcon:
    """Devuelve el QIcon cacheado para la plataforma indicada."""
    clave = normalize_platform(plataforma)
    cache_key = (clave, size)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    color_fondo = _COLORES[clave]
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(color_fondo)))
    p.setPen(QPen(QColor("#ffffff"), 1.2))
    p.drawRoundedRect(QRect(1, 1, size - 2, size - 2),
                      int(size * 0.22), int(size * 0.22))

    p.setPen(QPen(Qt.GlobalColor.white))
    if clave == "windows":
        _dibujar_windows(p, size)
    elif clave == "linux":
        _dibujar_linux(p, size)
    elif clave == "macos":
        _dibujar_macos(p, size)
    elif clave == "android":
        _dibujar_android(p, size, color_fondo)
    else:
        _dibujar_otro(p, size)
    p.end()

    icono = QIcon(pixmap)
    _CACHE[cache_key] = icono
    return icono
