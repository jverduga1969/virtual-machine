"""Tema global de la aplicación.

Un único lugar donde se definen los estilos para que ``main.py`` y el plugin
de configuración del host apliquen exactamente lo mismo.
"""

from PyQt6.QtWidgets import QApplication

DEFAULT_THEME = "Sistema (predeterminado)"

_STYLESHEETS = {
    "Oscuro": (
        "QWidget { background-color: #2b2b2b; color: white; } "
        "QLineEdit, QComboBox { background-color: #3b3b3b; color: white; }"
    ),
    "Claro": "QWidget { background-color: #f0f0f0; color: black; }",
    DEFAULT_THEME: "",
}


def apply_theme(theme: str, app=None) -> None:
    """Aplica ``theme`` a la instancia actual de QApplication."""
    app = app or QApplication.instance()
    if app is None:
        return
    app.setStyleSheet(_STYLESHEETS.get(theme, _STYLESHEETS[DEFAULT_THEME]))
