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
        config_vm = next(p for p in manager.plugins if p.name == "ConfiguracionVM")
        assert config_vm.combo_resolution.itemData(0) == ""
        assert config_vm.combo_resolution.count() >= 2
        assert config_vm.combo_monitors.count() == 4
        # La ventana cerrada por error se puede recuperar sin reiniciar QEMU.
        assert "volver a abrir" in window.btn_reabrir.toolTip().lower()
        assert "reopen_window" in window._shortcut_actions
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


def test_botones_y_menus_siguen_el_estado_de_la_vm(qapp, isolated_settings):
    from core import AppContext, PluginManager
    from main_window import MainWindow

    ctx = AppContext()
    manager = PluginManager(ctx, ROOT / "plugins")
    manager.load_all()
    window = MainWindow(ctx, manager)
    try:
        ctx.vm_repo.add({"id": "vm1", "name": "Estado", "state": "Running"})
        ctx.runner.active_processes["vm1"] = object()
        window._refresh_vm_list()
        window.list_vms.setCurrentRow(0)

        assert window.btn_iniciar.isEnabled() is False
        assert window.btn_pausa.isEnabled() is True
        assert window.btn_apagar.isEnabled() is True
        assert window._accion_pausar.isEnabled() is True
        assert window._accion_reanudar.isEnabled() is False

        ctx.vm_repo.update("vm1", {"state": "Paused"})
        ctx.vm_state_changed.emit("vm1", "Paused")
        assert window.btn_pausa.text() == "▶ Reanudar"
        assert window._accion_pausar.isEnabled() is False
        assert window._accion_reanudar.isEnabled() is True

        ctx.vm_repo.update("vm1", {"state": "Apagada"})
        ctx.vm_state_changed.emit("vm1", "Apagada")
        assert window.btn_iniciar.isEnabled() is True
        assert window.btn_pausa.isEnabled() is False
        assert window.btn_apagar.isEnabled() is False
        assert not any(accion.isEnabled() for accion in window.menu_apagar.actions())
    finally:
        window.close()
        manager.unload_all()
        logging.getLogger().removeHandler(ctx._log_handler)


def test_paneles_laterales_tienen_scroll_para_pantallas_bajas(qapp, isolated_settings):
    from core import AppContext, PluginManager
    from main_window import MainWindow
    from PyQt6.QtWidgets import QScrollArea
    from PyQt6.QtCore import Qt

    ctx = AppContext()
    manager = PluginManager(ctx, ROOT / "plugins")
    manager.load_all()
    window = MainWindow(ctx, manager)
    try:
        assert isinstance(window.left_stack.widget(0), QScrollArea)
        assert window.left_scroll.widget() is window.page_list
        assert window.left_scroll.widgetResizable() is True
        assert (window.left_scroll.verticalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        assert (window.left_scroll.horizontalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        assert window.list_vms.minimumHeight() >= 200

        assert window.right_scroll.widget() is window.resource_monitor
        assert window.right_scroll.widgetResizable() is True
        assert (window.right_scroll.verticalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        assert (window.right_scroll.horizontalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Los 8 gráficos del monitor imponen una altura mínima real.
        assert window.resource_monitor.minimumSizeHint().height() >= 400

        # Con una ventana baja, ambos paneles deben tener recorrido vertical.
        # Sin VMs se muestra la página de bienvenida, así que fuerzo la lista.
        window.left_stack.setCurrentIndex(0)
        window.resize(900, 360)
        window.show()
        qapp.processEvents()
        assert window.left_scroll.verticalScrollBar().maximum() > 0
        assert window.right_scroll.verticalScrollBar().maximum() > 0
    finally:
        window.close()
        manager.unload_all()
        logging.getLogger().removeHandler(ctx._log_handler)


def test_tema_unico(qapp):
    from core.theme import DEFAULT_THEME, apply_theme

    apply_theme("Oscuro", qapp)
    assert "#2b2b2b" in qapp.styleSheet()

    apply_theme(DEFAULT_THEME, qapp)
    assert qapp.styleSheet() == ""
