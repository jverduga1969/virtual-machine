import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from core import AppContext, PluginManager
from core.i18n import install as install_translations
from core.theme import DEFAULT_THEME, apply_theme
from main_window import MainWindow

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

def apply_saved_theme(app, settings):
    """Lee el tema guardado en QSettings y lo aplica a toda la app."""
    apply_theme(settings.value("ui/theme", DEFAULT_THEME), app)

def main():
    setup_logging()

    # 1. Configurar la aplicación
    app = QApplication(sys.argv)
    app.setOrganizationName("VirtualMachine")
    app.setApplicationName("VirtualMachineApp")

    # 2. Crear el contexto: expone un único QSettings compartido por toda la app
    ctx = AppContext()

    # 3. Aplicar tema e idioma guardados ANTES de crear la ventana
    apply_saved_theme(app, ctx.settings)
    install_translations(ctx.settings)

    # 4. Cargar plugins
    plugins_dir = Path(__file__).parent / "plugins"
    manager = PluginManager(ctx, plugins_dir)
    manager.load_all()

    # 5. Crear ventana principal
    window = MainWindow(ctx, manager)
    window.show()

    # 6. Ejecutar
    exit_code = app.exec()
    manager.unload_all()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
