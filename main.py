import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from core import AppContext, PluginManager
from main_window import MainWindow

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

def apply_saved_theme(app):
    """Lee el tema guardado en QSettings y lo aplica a toda la app."""
    theme = QSettings().value("ui/theme", "Sistema (predeterminado)")
    if theme == "Oscuro":
        app.setStyleSheet("QWidget { background-color: #2b2b2b; color: white; } QLineEdit, QComboBox { background-color: #3b3b3b; color: white; }")
    elif theme == "Claro":
        app.setStyleSheet("QWidget { background-color: #f0f0f0; color: black; }")
    else:
        app.setStyleSheet("") # Sistema

def main():
    setup_logging()
    
    # 1. Configurar la aplicación
    app = QApplication(sys.argv)
    app.setOrganizationName("VirtualMachine")
    app.setApplicationName("VirtualMachineApp")
    
    # 2. Aplicar el tema guardado ANTES de crear la ventana
    apply_saved_theme(app)
    
    # 3. Crear contexto y cargar plugins
    ctx = AppContext()
    
    plugins_dir = Path(__file__).parent / "plugins"
    manager = PluginManager(ctx, plugins_dir)
    manager.load_all()
    
    # 4. Crear ventana principal
    window = MainWindow(ctx, manager)
    window.show()
    
    # 5. Ejecutar
    exit_code = app.exec()
    manager.unload_all()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
