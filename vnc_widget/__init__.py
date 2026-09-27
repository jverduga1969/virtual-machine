"""Cliente VNC embebido para PyQt6.

Basado en https://github.com/zocker-160/pyQVNCWidget (MIT).
Adaptado localmente para usar PyQt6 en lugar de PyQt5.
"""
from .qvncwidget import QVNCWidget
from .rfb import RFBClient

__all__ = ["QVNCWidget", "RFBClient"]
