"""Arranque headless de plugins y ventana principal (Fase 0)."""

import logging

import pytest

from conftest import ROOT

pytestmark = pytest.mark.gui


def test_carga_de_plugins_y_ventana(qapp, isolated_settings):
    from core import AppContext, PluginManager
    from main_window import MainWindow

    ctx = AppContext()
    manager = PluginManager(ctx, ROOT / "plugins")
    manager.load_all()
    window = MainWindow(ctx, manager)
    try:
        assert len(manager.plugins) == 8
        assert window.tabs.count() == 8
        assert window._settings is ctx.settings
    finally:
        window.close()
        manager.unload_all()
        # AppContext instala un handler global de logs: retirarlo antes de que
        # el QObject se destruya para no dejar señales colgando en otros tests.
        logging.getLogger().removeHandler(ctx._log_handler)


def test_pestanas_vm_se_habilitan_con_otro_idioma(qapp, isolated_settings):
    from core import AppContext, PluginManager, i18n
    from main_window import MainWindow

    class Settings:
        def value(self, key, default=""):
            return "English" if key == "ui/language" else default

    anterior = dict(i18n._current)
    i18n.install(Settings())
    ctx = AppContext()
    manager = PluginManager(ctx, ROOT / "plugins")
    manager.load_all()
    window = MainWindow(ctx, manager)
    try:
        assert window.tabs.tabText(1) == "VM Settings"
        window._update_tabs_state(True)
        assert window.tabs.isTabEnabled(1)
        assert window._goto_tab("Configuración VM")
        assert window.tabs.currentIndex() == 1
        # Los botones y sus menús deben seguir traducidos tras cambiar de estado.
        assert window.btn_iniciar.text() == "▶ Start"
        assert [a.text() for a in window.menu_apagar.actions()] == [
            "⏹ Shut down (ACPI)", "⏻ Force shutdown",
            "🔄 Restart", "⟲ Force restart"]
        # Los resultados del diagnóstico del host también deben estar traducidos.
        from PyQt6.QtWidgets import QLabel
        textos = [lbl.text() for lbl in window.findChildren(QLabel)]
        assert "Not installed" in textos or any("Not installed" in t for t in textos)
        assert any("Host audio" in t for t in textos)
    finally:
        window.close()
        manager.unload_all()
        logging.getLogger().removeHandler(ctx._log_handler)
        i18n._current = anterior


def test_tema_unico(qapp):
    from core.theme import DEFAULT_THEME, apply_theme

    apply_theme("Oscuro", qapp)
    assert "#2b2b2b" in qapp.styleSheet()

    apply_theme(DEFAULT_THEME, qapp)
    assert qapp.styleSheet() == ""
