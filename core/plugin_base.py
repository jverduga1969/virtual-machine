from abc import ABC
from PyQt6.QtWidgets import QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_context import AppContext

class PluginBase(ABC):
    """
    Interfaz base para todos los plugins de la aplicación.
    Cada plugin debe heredar de esta clase e implementar 'get_tabs' si desea mostrar algo.
    """
    name: str = "unnamed"
    version: str = "0.1.0"
    description: str = ""

    def __init__(self, app: "AppContext"):
        self.app = app

    def on_load(self) -> None:
        """Se llama cuando el plugin se carga por primera vez."""
        pass

    def on_unload(self) -> None:
        """Se llama cuando la aplicación se cierra."""
        pass

    def on_vm_selected(self, vm_id: str) -> None:
        """Se llama cuando el usuario selecciona una VM en la lista."""
        pass

    def get_tabs(self) -> list[tuple[str, QWidget]]:
        """
        Devuelve una lista de tuplas (nombre_pestaña, widget).
        El MainWindow las añadirá al QTabWidget principal.
        """
        return []

    def get_right_panels(self) -> list[tuple[str, QWidget]]:
        """
        Devuelve widgets para el panel derecho (ej: Uso de recursos).
        """
        return []
