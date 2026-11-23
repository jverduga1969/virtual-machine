"""Valores obligatorios de macOS en la UI de Configuración VM.

macOS necesita Q35 + VRAM >= 128 MB. VGA estándar es el gráfico recomendado,
pero el usuario puede elegir otros dispositivos como opción experimental
(aviso visible en la UI). El plugin deshabilita lo que no aplica en macOS:
portapapeles, multimonitor, agente invitado y métodos de carpeta compartida
distintos de SMB. SPICE y VNC si aplican.
"""

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLabel, QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget

from plugins.config_vm.plugin import Plugin


def _plugin_con_commos(qapp, plataforma):
    """Plugin minimo con los combos que toca _apply_macos_mandatory."""
    plugin = object.__new__(Plugin)

    plugin.combo_platform = QComboBox()
    plugin.combo_platform.addItems(["GNU / Linux", "Windows 11", "macOS", "Android"])
    plugin.combo_platform.setCurrentText(plataforma)

    plugin.combo_chipset = QComboBox()
    plugin.combo_chipset.addItems(["i440FX (clásico)", "Q35 (moderno, PCIe)"])

    plugin.combo_console_proto = QComboBox()
    plugin.combo_console_proto.addItems(["VNC", "SPICE (Local 3D)", "SPICE (Remoto - Red)"])

    plugin.combo_console_mode = QComboBox()
    plugin.combo_console_mode.addItems([
        "Embebida en la app", "Ventana externa",
        "Híbrida (VNC widget + SPICE externo)", "Pantalla completa",
        "Pantalla completa (embebida)",
    ])

    plugin.combo_graphics = QComboBox()
    plugin.combo_graphics.addItems([
        "Automático (recomendado) → VirtIO-GPU 2D", "VirtIO-GPU 2D (compatible)",
        "VirtIO-GPU + VirGL 3D", "VirtIO-GPU + Venus/Vulkan 3D",
        "Red Hat QXL 2D", "VMware SVGA II", "VGA estándar", "Sin video / Headless",
    ])

    plugin.lbl_graphics_macos = QLabel()
    plugin.combo_vram = QComboBox()
    plugin.combo_vram.addItems(["64 MB", "128 MB", "256 MB", "512 MB"])

    plugin.combo_monitors = QComboBox()
    plugin.combo_monitors.addItems(["1 monitor", "2 monitores", "3 monitores", "4 monitores"])
    plugin.combo_monitors.setCurrentIndex(2)

    plugin.chk_clipboard = QCheckBox()
    plugin.chk_clipboard.setChecked(True)
    plugin.check_ga = QCheckBox()
    plugin.check_ga.setChecked(True)
    plugin.tree_shared = QTreeWidget()
    plugin.tabs_sharing = QTabWidget()
    plugin.tabs_sharing.addTab(QWidget(), "Compartir Carpetas")
    item = QTreeWidgetItem(plugin.tree_shared)
    item.setText(0, "/tmp/share")
    item.setText(1, "docs")
    item.setText(2, "9p")

    # Estado inicial "malo" que una VM anterior pudo dejar guardado.
    plugin.combo_chipset.setCurrentIndex(0)
    plugin.combo_graphics.setCurrentIndex(5)  # VMware SVGA elegido explicitamente
    plugin._macos_graphics_opt_in = True
    plugin.combo_vram.setCurrentIndex(0)      # 64 MB
    plugin.combo_console_proto.setCurrentIndex(1)  # SPICE (ahora permitido)
    return plugin


def test_macos_fija_valores_obligatorios(qapp):
    plugin = _plugin_con_commos(qapp, "macOS")
    plugin._apply_macos_mandatory()

    assert plugin.combo_chipset.currentIndex() == 1          # Q35
    # El usuario eligió VMware SVGA (5) antes de cambiar a macOS: se respeta,
    # pero con un aviso de que VGA estándar es el recomendado.
    assert plugin.combo_graphics.currentIndex() == 5
    assert plugin.lbl_graphics_macos.isVisible()
    assert "experimental" in plugin.lbl_graphics_macos.text().lower()
    assert "VGA estándar" in plugin.lbl_graphics_macos.text()
    assert plugin.combo_vram.currentIndex() >= 1             # >= 128 MB
    assert plugin.combo_console_proto.currentIndex() == 1    # SPICE se respeta
    assert plugin.combo_monitors.currentIndex() == 0         # 1 monitor
    assert not plugin.chk_clipboard.isChecked()              # sin vdagent
    assert not plugin.check_ga.isChecked()                   # sin qemu-ga
    assert plugin.tree_shared.topLevelItem(0).text(2) == "SMB"


def test_macos_nueva_usa_vga_recomendada_por_defecto(qapp):
    """Sin eleccion explicita, una VM macOS arranca con VGA estandar."""
    plugin = _plugin_con_commos(qapp, "macOS")
    plugin.combo_graphics.setCurrentIndex(0)  # default generico (VirtIO)
    plugin._macos_graphics_opt_in = False
    plugin._apply_macos_mandatory()

    assert plugin.combo_graphics.currentIndex() == 6
    assert "recomendado" in plugin.lbl_graphics_macos.text().lower()


def test_macos_deshabilita_opciones_inaplicables(qapp):
    plugin = _plugin_con_commos(qapp, "macOS")
    plugin._apply_macos_mandatory()

    chip = plugin.combo_chipset.model()
    assert not chip.item(0).isEnabled()          # i440FX deshabilitado
    assert chip.item(1).isEnabled()              # Q35 disponible

    gfx = plugin.combo_graphics.model()
    # VMware SVGA, QXL y VirtIO 2D son experimentales; VGA (6) es la
    # recomendada. 3D (2,3) y sin video (7) no aplican en macOS.
    for i in (0, 1, 4, 5, 6):
        assert gfx.item(i).isEnabled(), f"grafico {i} deberia estar disponible"
    for i in (2, 3, 7):
        assert not gfx.item(i).isEnabled(), f"grafico {i} no deberia estar disponible"

    vram = plugin.combo_vram.model()
    assert not vram.item(0).isEnabled()          # 64 MB deshabilitado
    assert vram.item(1).isEnabled()              # 128 MB disponible

    proto = plugin.combo_console_proto.model()
    assert proto.item(0).isEnabled()             # VNC disponible
    assert proto.item(1).isEnabled()             # SPICE local disponible
    assert proto.item(2).isEnabled()             # SPICE remoto disponible

    assert not plugin.combo_monitors.isEnabled() # multimonitor no aplica
    assert not plugin.chk_clipboard.isEnabled()  # portapapeles no aplica
    assert not plugin.check_ga.isEnabled()       # agente invitado no aplica


def test_salir_de_macos_rehabilita_opciones(qapp):
    plugin = _plugin_con_commos(qapp, "macOS")
    plugin._apply_macos_mandatory()

    plugin.combo_platform.setCurrentText("GNU / Linux")
    plugin._apply_macos_mandatory()

    chip = plugin.combo_chipset.model()
    assert chip.item(0).isEnabled()              # i440FX vuelve a estar disponible
    vram = plugin.combo_vram.model()
    assert vram.item(0).isEnabled()              # 64 MB vuelve a estar disponible
    assert plugin.combo_monitors.isEnabled()
    assert plugin.chk_clipboard.isEnabled()
    assert plugin.check_ga.isEnabled()

    # Las opciones que macOS bloqueaba vuelven, salvo el 3D (indices 2,3)
    # que _update_display_options deshabilita por usar protocolo VNC.
    gfx = plugin.combo_graphics.model()
    for i in (0, 1, 4, 5, 6, 7):
        assert gfx.item(i).isEnabled(), f"grafico {i} no rehabilitado"
