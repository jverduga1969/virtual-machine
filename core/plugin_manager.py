import importlib
import logging
from pathlib import Path
from typing import List
from .plugin_base import PluginBase
from .app_context import AppContext

log = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, app: AppContext, plugins_dir: Path):
        self.app = app
        self.plugins_dir = plugins_dir
        self.plugins: List[PluginBase] = []

    def load_all(self) -> List[PluginBase]:
        if not self.plugins_dir.exists():
            log.warning(f"El directorio de plugins no existe: {self.plugins_dir}")
            return []

        # Asegurar que el paquete 'plugins' sea importable
        init_file = self.plugins_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue
            if not (entry / "plugin.py").exists():
                continue

            try:
                # Importación dinámica
                module_name = f"plugins.{entry.name}.plugin"
                mod = importlib.import_module(module_name)
                
                # Buscar la clase Plugin
                if not hasattr(mod, "Plugin"):
                    log.error(f"El plugin {entry.name} no tiene una clase 'Plugin'")
                    continue
                
                plugin_instance = mod.Plugin(self.app)
                
                # Conectar señales automáticamente
                self.app.vm_selection_changed.connect(plugin_instance.on_vm_selected)
                
                # Inicializar plugin
                plugin_instance.on_load()
                self.plugins.append(plugin_instance)
                log.info(f"Plugin cargado: {plugin_instance.name} v{plugin_instance.version}")
                
            except Exception as e:
                log.exception(f"Error al cargar el plugin {entry.name}: {e}")

        return self.plugins

    def unload_all(self):
        for plugin in self.plugins:
            try:
                plugin.on_unload()
            except Exception as e:
                log.error(f"Error al descargar {plugin.name}: {e}")
        self.plugins.clear()
