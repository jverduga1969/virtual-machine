"""El ejecutable PyInstaller no tiene plugins/ en disco: se importan por nombre."""

from pathlib import Path

import core.plugin_manager as pm


def test_modo_congelado_carga_los_ocho_plugins(qapp, app_ctx, monkeypatch):
    monkeypatch.setattr(pm.sys, "frozen", True, raising=False)

    # Un directorio inexistente no debe importar: en el EXE no existe.
    manager = pm.PluginManager(app_ctx, Path("no-existe"))
    plugins = manager.load_all()

    assert len(plugins) == 8
    assert {type(p).__module__ for p in plugins} == set(pm.PLUGIN_MODULES)
    manager.unload_all()
