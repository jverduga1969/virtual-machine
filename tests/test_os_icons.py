"""Iconos por sistema operativo en el listado de VMs."""

import logging

import pytest

from conftest import ROOT
from ui_widgets.os_icons import normalize_platform, os_icon


pytestmark = pytest.mark.gui


def test_normaliza_plataformas():
    assert normalize_platform("Windows 11") == "windows"
    assert normalize_platform("GNU / Linux") == "linux"
    assert normalize_platform("macOS") == "macos"
    assert normalize_platform("Android") == "android"
    assert normalize_platform("Otro") == "other"
    assert normalize_platform(None) == "other"


def test_iconos_son_distintos_y_cacheados(qapp):
    claves = {}
    for plataforma in ("Windows 11", "GNU / Linux", "macOS", "Android", "Otro"):
        icono = os_icon(plataforma)
        assert not icono.isNull()
        assert icono.pixmap(32, 32).width() == 32
        claves[plataforma] = icono.cacheKey()
        assert os_icon(plataforma).cacheKey() == icono.cacheKey()

    assert len(set(claves.values())) == len(claves)


def test_listado_usa_icono_segun_so(qapp, isolated_settings):
    from PyQt6.QtCore import Qt
    from core import AppContext, PluginManager
    from main_window import MainWindow

    ctx = AppContext()
    manager = PluginManager(ctx, ROOT / "plugins")
    manager.load_all()
    window = MainWindow(ctx, manager)
    try:
        ctx.vm_repo.add({"id": "w1", "name": "A Windows", "state": "Apagada",
                         "platform": "Windows 11"})
        ctx.vm_repo.add({"id": "l1", "name": "B Linux", "state": "Apagada",
                         "platform": "GNU / Linux"})
        window._refresh_vm_list()

        items = [window.list_vms.item(i) for i in range(window.list_vms.count())]
        nombres = [item.data(Qt.ItemDataRole.UserRole + 1) for item in items]
        win = items[nombres.index("a windows")]
        lin = items[nombres.index("b linux")]

        assert win.icon().cacheKey() == os_icon("Windows 11").cacheKey()
        assert lin.icon().cacheKey() == os_icon("GNU / Linux").cacheKey()
        assert win.icon().cacheKey() != lin.icon().cacheKey()
    finally:
        window.close()
        manager.unload_all()
        logging.getLogger().removeHandler(ctx._log_handler)
