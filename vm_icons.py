# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_icons.py — iconos de SO embebidos como SVG.

Estos iconos NO dependen del tema del sistema (Kvantum, Breeze, Adwaita…),
así que se ven igual en cualquier escritorio. Cada uno se renderiza a
partir de un SVG minimalista con el logo reconocible del sistema.

Uso:
    from vm_icons import icon_for_vm
    icon = icon_for_vm(os_type="linux", distro="Linux Mint")
    item.setIcon(icon)
"""
from functools import lru_cache

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


# --- SVG sources (24x24 viewBox) -------------------------------------

_SVG_MACOS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<path fill="#e8e8e8" d="M16.6 12.8c0-2.4 2-3.6 2.1-3.6-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.6.9-.8 0-1.9-.9-3.1-.8-1.6 0-3.1.9-3.9 2.4-1.7 2.9-.4 7.2 1.2 9.5.8 1.2 1.7 2.4 3 2.4 1.2 0 1.7-.8 3.1-.8 1.4 0 1.9.8 3.1.8 1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.8 1.3-2.9-.1 0-2.7-1-2.7-3.6zM14.4 5.5c.7-.8 1.1-2 1-3.2-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.3-.6 2.9-1.3z"/>
</svg>"""

_SVG_WINDOWS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<path fill="#00A4EF" d="M3 5.5l7.5-1v7.25H3V5.5zm8.5-1.17L21 3v8.75h-9.5V4.33zM3 12.75h7.5V20L3 19V12.75zm8.5 0H21V21l-9.5-1.32v-6.93z"/>
</svg>"""

_SVG_UBUNTU = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="9" fill="none" stroke="#E95420" stroke-width="1.6"/>
<circle cx="12" cy="12" r="2.6" fill="#E95420"/>
<circle cx="12" cy="4.4" r="1.9" fill="#E95420"/>
<circle cx="18.5" cy="16.1" r="1.9" fill="#E95420"/>
<circle cx="5.5" cy="16.1" r="1.9" fill="#E95420"/>
</svg>"""

_SVG_DEBIAN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#D70A53"/>
<path d="M16.5 8.5 Q13 6.5 9.5 10 Q6.5 13.5 11 17.5 Q17 18 17.5 13" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round"/>
</svg>"""

_SVG_FEDORA = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#51A2DA"/>
<path fill="#fff" d="M13 6h3v3h-2v3h2v3h-2v3h-3v-3H9v-3h2V9H9V6h4zm0 3v3h-1v3h3v-3h2v-3h-4z" opacity="0.9"/>
<text x="12" y="17.3" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle" fill="#fff">f</text>
</svg>"""

_SVG_ARCH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<path fill="#1793D1" d="M12 2 L2 22 L8 22 L12 14 L16 22 L22 22 Z"/>
<path fill="#1793D1" d="M12 14 L9 20 L12 18 L15 20 Z" opacity="0.5"/>
</svg>"""

_SVG_MINT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#87CF3E"/>
<path fill="#ffffff" d="M17 7 Q10 7 8 12 Q12 10 15 12 Q18 14 17 7 Z"/>
<path fill="#2e7d32" d="M14 9 Q11 9 10 12 Q12 10 14 12 Z" opacity="0.6"/>
</svg>"""

_SVG_OPENSUSE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#73BA25"/>
<circle cx="12" cy="12" r="4" fill="none" stroke="#fff" stroke-width="1.6"/>
<circle cx="12" cy="4.5" r="1.4" fill="#fff"/>
<circle cx="19.5" cy="12" r="1.4" fill="#fff"/>
<circle cx="12" cy="19.5" r="1.4" fill="#fff"/>
<circle cx="4.5" cy="12" r="1.4" fill="#fff"/>
</svg>"""

_SVG_KALI = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#367BF0"/>
<path fill="#fff" d="M8 8 L10 16 L12 10 L14 16 L16 8 L14 8 L13 13 L12 9 L11 13 L10 8 Z"/>
</svg>"""

_SVG_LINUX = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<ellipse cx="12" cy="15" rx="5.5" ry="6.5" fill="#333"/>
<ellipse cx="12" cy="8.5" rx="4" ry="4" fill="#333"/>
<ellipse cx="10.5" cy="7.5" rx="0.55" ry="0.75" fill="#fff"/>
<ellipse cx="13.5" cy="7.5" rx="0.55" ry="0.75" fill="#fff"/>
<path d="M10.5 10 L12 11.5 L13.5 10" stroke="#F5A623" stroke-width="0.9" fill="none" stroke-linecap="round"/>
<path d="M7 21 Q7 18 9 18 M17 21 Q17 18 15 18" stroke="#F5A623" stroke-width="0.9" fill="none"/>
</svg>"""

_SVG_GENERIC = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
<rect x="3" y="4" width="18" height="13" rx="1.5" fill="#607D8B"/>
<rect x="4.5" y="5.5" width="15" height="10" fill="#263238"/>
<rect x="9" y="18" width="6" height="2" fill="#607D8B"/>
<rect x="6" y="20" width="12" height="1.5" fill="#607D8B"/>
</svg>"""


_SVG_BY_KEY = {
    "macos":   _SVG_MACOS,
    "windows": _SVG_WINDOWS,
    "ubuntu":  _SVG_UBUNTU,
    "debian":  _SVG_DEBIAN,
    "fedora":  _SVG_FEDORA,
    "arch":    _SVG_ARCH,
    "mint":    _SVG_MINT,
    "opensuse": _SVG_OPENSUSE,
    "kali":    _SVG_KALI,
    "linux":   _SVG_LINUX,
    "generic": _SVG_GENERIC,
}


_DISTRO_ALIASES = (
    ("linux mint", "mint"),
    ("mint",       "mint"),
    ("ubuntu",     "ubuntu"),
    ("debian",     "debian"),
    ("fedora",     "fedora"),
    ("arch",       "arch"),
    ("manjaro",    "arch"),
    ("endeavour",  "arch"),
    ("cachyos",    "arch"),
    ("opensuse",   "opensuse"),
    ("suse",       "opensuse"),
    ("kali",       "kali"),
)


def _render_svg(svg_text, size=32):
    """Renderiza un SVG a QPixmap del tamaño pedido."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    painter = QPainter(pix)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    return pix


@lru_cache(maxsize=64)
def _icon_cached(key, size=32):
    svg = _SVG_BY_KEY.get(key) or _SVG_BY_KEY["generic"]
    return QIcon(_render_svg(svg, size))


def icon_for_vm(os_type="", distro="", size=32):
    """Devuelve un QIcon para la VM según os_type y (si linux) distro.

    os_type: "linux" | "windows" | "macos" | "" (desconocido)
    distro:  etiqueta visible, ej. "Linux Mint", "Ubuntu", "Fedora"…
    """
    os_type = (os_type or "").strip().lower()
    if os_type == "macos":
        return _icon_cached("macos", size)
    if os_type == "windows":
        return _icon_cached("windows", size)
    if os_type == "linux":
        d = (distro or "").strip().lower()
        for needle, key in _DISTRO_ALIASES:
            if needle in d:
                return _icon_cached(key, size)
        return _icon_cached("linux", size)
    return _icon_cached("generic", size)
