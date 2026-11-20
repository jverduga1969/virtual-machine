"""Regresiones de Almacenamiento y Medios con idioma distinto de español."""

import pytest

from core import i18n


class _Settings:
    def __init__(self, lang):
        self.lang = lang

    def value(self, key, default=""):
        return self.lang if key == "ui/language" else default


@pytest.fixture(autouse=True)
def _restaurar_idioma():
    anterior = dict(i18n._current)
    yield
    i18n._current = anterior


def test_claves_de_dialogos_en_todos_los_idiomas():
    claves = (
        "Configurar dispositivo de almacenamiento",
        "Modificar disco duro",
        "Fuente del medio:",
        "Bus del CD/DVD:",
        "Origen:",
        "Usar archivo existente",
        "Tipo:",
        "Tags:",
        "▼ Avanzado (rendimiento e I/O)",
        "Compactado con éxito.",
        "Solo se pueden compactar discos QCOW2.",
        "Montar ISO en el host",
        "Desmontar ISO del host",
        "Expulsar ISO de la VM",
        "Insertar ISO en la VM",
        "Añadir medios",
    )
    for nombre, codigo in i18n.LANGUAGES.items():
        catalogo = i18n.load_translations(codigo)
        if codigo == "es":
            continue
        for clave in claves:
            assert clave in catalogo, f"Falta {clave!r} en {nombre}"
            assert catalogo[clave].strip(), f"Traducción vacía de {clave!r} en {nombre}"


def test_origen_de_cd_usa_valores_estables_en_ingles(qapp):
    from plugins.config_vm import plugin as modulo
    from PyQt6.QtWidgets import QComboBox

    i18n.install(_Settings("English"))
    dlg = modulo.CDDVDDialog(allow_download=True)
    i18n.translate_widgets(dlg)

    assert dlg.combo_source.itemText(1) == "Use existing ISO/IMG/DMG"
    modulo._set_combo_value(dlg.combo_source, modulo.SOURCE_EXISTING)
    assert dlg.combo_source.currentData() == modulo.SOURCE_EXISTING
    assert modulo._combo_value(dlg.combo_source) == modulo.SOURCE_EXISTING
    assert dlg.media_widget.isVisible() is True or dlg.media_widget.isHidden() is False

    modulo._set_combo_value(dlg.combo_source, modulo.SOURCE_DOWNLOAD)
    assert modulo._combo_value(dlg.combo_source) == modulo.SOURCE_DOWNLOAD
    assert dlg.media_widget.isHidden()

    # Un combo sin itemData (por ejemplo el de formato) también funciona.
    combo = QComboBox()
    combo.addItems(["QCOW2", "IMG (RAW)"])
    i18n.translate_widgets(combo)
    assert modulo._combo_value(combo) == "QCOW2"
    modulo._set_combo_value(combo, "IMG (RAW)")
    assert modulo._combo_value(combo) == "IMG (RAW)"


def test_dialogo_de_medios_se_traduce_al_mostrarse(qapp):
    from plugins.config_vm.plugin import CDDVDDialog

    i18n.install(_Settings("English"))
    dlg = CDDVDDialog(allow_download=True)
    assert dlg.windowTitle() == "Configurar dispositivo de almacenamiento"

    dlg.show()
    assert dlg.windowTitle() == "Configure storage device"
    assert dlg.combo_source.itemText(1) == "Use existing ISO/IMG/DMG"
    dlg.close()


def test_tipo_de_dispositivo_se_reconoce_con_texto_traducido(qapp):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
    from plugins.config_vm.plugin import Plugin, TIPO_DISCO, TIPO_OPTICO

    i18n.install(_Settings("English"))
    plugin = object.__new__(Plugin)
    plugin.tree_storage = QTreeWidget()
    item = QTreeWidgetItem(plugin.tree_storage)
    item.setText(0, "Optical drive")

    assert plugin._storage_type(item) == TIPO_OPTICO
    item.setData(0, Qt.ItemDataRole.UserRole, TIPO_DISCO)
    assert plugin._storage_type(item) == TIPO_DISCO
    assert plugin._boot_label(f"{TIPO_OPTICO} — /tmp/caso.iso").startswith("Optical drive")
    assert plugin._boot_label("Red/PXE") == "Network/PXE"
    assert plugin._boot_key("Optical drive — /tmp/caso.iso") == f"{TIPO_OPTICO} — /tmp/caso.iso"
    assert plugin._boot_key("Network/PXE") == "Red/PXE"


def test_modificar_una_unidad_optica_abre_el_dialogo_en_ingles(qapp, monkeypatch):
    from PyQt6.QtWidgets import QComboBox, QTreeWidget, QTreeWidgetItem
    from plugins.config_vm import plugin as modulo

    i18n.install(_Settings("English"))
    abiertos = []

    class FakeDialog:
        def __init__(self, parent, cd_data=None, **kwargs):
            abiertos.append((cd_data, kwargs))
            self.combo_source = QComboBox()
            self.combo_source.addItem(modulo.SOURCE_EXISTING, modulo.SOURCE_EXISTING)
            self.combo_bus = QComboBox()
            self.combo_bus.addItem("SATA/AHCI", "SATA/AHCI")
            self.input_file = None

        def exec(self):
            from PyQt6.QtWidgets import QDialog
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(modulo, "CDDVDDialog", FakeDialog)
    plugin = object.__new__(modulo.Plugin)
    plugin.tree_storage = QTreeWidget()
    item = QTreeWidgetItem(plugin.tree_storage)
    from PyQt6.QtCore import Qt
    item.setData(0, Qt.ItemDataRole.UserRole, modulo.TIPO_OPTICO)
    item.setText(0, "Optical drive")
    item.setText(2, "/tmp/caso.iso")
    item.setText(3, "SATA/AHCI")
    item.setData(3, Qt.ItemDataRole.UserRole, "SATA/AHCI")
    item.setData(3, Qt.ItemDataRole.UserRole + 1, "SATA/AHCI")
    plugin.tree_storage.setCurrentItem(item)
    combo_so = QComboBox()
    combo_so.addItem("Windows 10")
    plugin.combo_so = combo_so
    plugin.app = type("App", (), {
        "parent": lambda self: None,
        "isos_dir": "/tmp/isos",
    })()
    plugin._sync_boot = lambda: None
    plugin._register_media = lambda *a, **k: None

    plugin._modify_media()

    assert len(abiertos) == 1
    assert abiertos[0][0]["bus"] == "SATA/AHCI"
    assert abiertos[0][0]["path"] == "/tmp/caso.iso"


def test_compactar_llama_a_la_compactacion_real(qapp, monkeypatch):
    from pathlib import Path
    from PyQt6.QtWidgets import QMessageBox, QTreeWidget, QTreeWidgetItem
    from plugins.config_vm import plugin as modulo

    i18n.install(_Settings("English"))
    llamadas = []

    class FakeManager:
        def __init__(self, data_dir, settings):
            pass

        def compact_disk(self, path):
            llamadas.append(path)
            return True, "ok"

    monkeypatch.setattr("services.media_library.MediaLibraryManager", FakeManager)
    monkeypatch.setattr(QMessageBox, "question",
                        staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: None))

    plugin = object.__new__(modulo.Plugin)
    plugin.tree_storage = QTreeWidget()
    disco = QTreeWidgetItem(plugin.tree_storage)
    from PyQt6.QtCore import Qt
    disco.setData(0, Qt.ItemDataRole.UserRole, modulo.TIPO_DISCO)
    disco.setText(0, "Hard disk")
    disco.setText(2, "/tmp/disco.qcow2")
    disco.setText(3, "20G")
    plugin.tree_storage.setCurrentItem(disco)
    plugin.app = type("App", (), {
        "parent": lambda self: None,
        "data_dir": Path("/tmp"),
        "settings": None,
    })()
    plugin._update_media_size = lambda *a: None

    plugin._compact_media()

    assert llamadas == ["/tmp/disco.qcow2"]


def test_filtros_de_medios_no_dependen_del_idioma(qapp):
    from PyQt6.QtWidgets import QComboBox, QLineEdit, QTableWidget
    from plugins.media_library.plugin import Plugin

    i18n.install(_Settings("English"))
    plugin = object.__new__(Plugin)
    plugin.input_search = QLineEdit()
    plugin.combo_os = QComboBox()
    for texto in ("SO: Todos", "Linux", "Windows"):
        plugin.combo_os.addItem(texto, "Todos" if "Todos" in texto else texto)
    plugin.combo_fmt = QComboBox()
    for texto in ("Formato: Todos", "ISO", "QCOW2", "RAW"):
        plugin.combo_fmt.addItem(texto, "Todos" if "Todos" in texto else texto)
    plugin.table = QTableWidget(0, 10)
    plugin.all_media = [
        {"id": "1", "name": "linux.qcow2", "type": "Disco duro", "os": "Linux",
         "format": "QCOW2", "status": "OK"},
        {"id": "2", "name": "windows.raw", "type": "Disco duro", "os": "Windows",
         "format": "RAW", "status": "OK"},
    ]

    # "OS: All" debe mostrarlo todo aunque el texto esté traducido.
    i18n.translate_widgets(plugin.combo_os)
    i18n.translate_widgets(plugin.combo_fmt)
    plugin._refresh_table()
    assert plugin.table.rowCount() == 2

    plugin.combo_os.setCurrentIndex(plugin.combo_os.findData("Windows"))
    plugin._refresh_table()
    assert plugin.table.rowCount() == 1
    assert plugin.table.item(0, 0).text() == "windows.raw"

    plugin.combo_os.setCurrentIndex(0)
    plugin.combo_fmt.setCurrentIndex(plugin.combo_fmt.findData("RAW"))
    plugin._refresh_table()
    assert plugin.table.rowCount() == 1
    assert plugin.table.item(0, 0).text() == "windows.raw"


def test_botones_inferiores_avisan_si_no_hay_seleccion(qapp, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox, QTableWidget
    from plugins.media_library.plugin import Plugin

    i18n.install(_Settings("English"))
    mensajes = []
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: mensajes.append(a[2] if len(a) > 2 else "")))

    plugin = object.__new__(Plugin)
    plugin.table = QTableWidget(0, 10)
    plugin.all_media = []
    plugin.app = type("App", (), {"parent": lambda self: None})()

    for accion in ("_modify_selected", "_compact_selected", "_verify_selected",
                   "_sha_selected", "_delete_selected", "_open_folder_selected"):
        getattr(plugin, accion)()

    assert len(mensajes) == 6
    assert all(m == "Select a media item in the table." for m in mensajes)


def test_la_seleccion_sobrevive_al_refresco_de_la_tabla(qapp):
    from PyQt6.QtWidgets import QComboBox, QLineEdit, QTableWidget
    from plugins.media_library.plugin import Plugin

    plugin = object.__new__(Plugin)
    plugin.input_search = QLineEdit()
    plugin.combo_os = QComboBox()
    plugin.combo_os.addItem("OS: All", "Todos")
    plugin.combo_fmt = QComboBox()
    plugin.combo_fmt.addItem("Format: All", "Todos")
    plugin.table = QTableWidget(0, 10)
    plugin.all_media = [
        {"id": "1", "name": "disco.qcow2", "type": "Disco duro", "os": "Linux",
         "format": "QCOW2", "status": "OK"},
    ]

    plugin._refresh_table()
    plugin.table.selectRow(0)
    assert plugin._get_selected_media()["id"] == "1"

    # Esto es lo que ocurre al cambiar de idioma o al volver a mostrar la pestaña.
    plugin._refresh_table()

    assert plugin._get_selected_media() is not None
    assert plugin._get_selected_media()["id"] == "1"


def test_formato_de_crear_disco_no_depende_del_idioma(qapp):
    from plugins.media_library.plugin import CreateDiskDialog

    i18n.install(_Settings("English"))
    dlg = CreateDiskDialog()
    assert dlg.combo_type.currentData() == "qcow2"
    dlg.combo_type.setCurrentIndex(1)
    assert dlg.combo_type.currentData() == "raw"
