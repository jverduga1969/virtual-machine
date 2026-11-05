import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QComboBox, QFormLayout, QDialog, QDialogButtonBox, 
    QToolButton, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from core.plugin_base import PluginBase
from services.media_library import MediaLibraryManager
import logging
log = logging.getLogger(__name__)




class MediaWidget(QWidget):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def showEvent(self, event):
        super().showEvent(event)
        self.plugin._load_table()

class CreateDiskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear medio nuevo")
        self.resize(500, 450)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.input_name = QLineEdit("nuevo_medio")
        form.addRow("Nombre:", self.input_name)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Disco duro QCOW2 (recomendado)", "Disco duro RAW", "Disco duro VDI", "Disco duro VMDK"])
        form.addRow("Tipo:", self.combo_type)
        self.combo_prealloc = QComboBox()
        self.combo_prealloc.addItems(["Expandible (dinámico)", "Fijo (preasignado)"])
        form.addRow("Preasignación:", self.combo_prealloc)
        self.input_size = QLineEdit("40G")
        form.addRow("Tamaño:", self.input_size)
        layout.addLayout(form)
        self.btn_advanced = QToolButton()
        self.btn_advanced.setText("▶ Avanzado (rendimiento e I/O)")
        self.btn_advanced.setCheckable(True)
        self.btn_advanced.clicked.connect(self._toggle_advanced)
        layout.addWidget(self.btn_advanced)
        self.widget_advanced = QWidget()
        self.widget_advanced.setVisible(False)
        layout.addWidget(self.widget_advanced)
        layout.addStretch()
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _toggle_advanced(self):
        v = self.btn_advanced.isChecked()
        self.widget_advanced.setVisible(v)
        self.btn_advanced.setText("▼ Avanzado (rendimiento e I/O)" if v else "▶ Avanzado (rendimiento e I/O)")

class ModifyMediaDialog(QDialog):
    def __init__(self, parent, media):
        super().__init__(parent)
        self.setWindowTitle(f"Modificar: {media['name']}")
        self.resize(400, 400)
        self.media = media
        layout = QFormLayout(self)
        self.input_name = QLineEdit(media["name"])
        layout.addRow("Nombre:", self.input_name)
        self.combo_os = QComboBox()
        self.combo_os.addItems(["Linux", "Windows", "macOS", "Android", "Other"])
        self.combo_os.setCurrentText(media.get("os", "Other"))
        layout.addRow("SO:", self.combo_os)
        self.input_version = QLineEdit(media.get("version", ""))
        layout.addRow("Versión:", self.input_version)
        self.input_size = None
        if media.get("type") == "Disco duro":
            layout.addRow(QLabel(f"<i>Tamaño actual: {media.get('size_vm', '?')}</i>"))
            self.input_size = QLineEdit(media.get("size_vm", ""))
            self.input_size.setPlaceholderText("Ej. 60G (solo se puede aumentar)")
            layout.addRow("Nuevo tamaño:", self.input_size)
        self.input_tags = QLineEdit(media.get("tags", ""))
        layout.addRow("Tags:", self.input_tags)
        self.input_notes = QTextEdit(media.get("notes", ""))
        self.input_notes.setMaximumHeight(60)
        layout.addRow("Notas:", self.input_notes)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

class Plugin(PluginBase):
    name = "MediaLibrary"
    version = "1.5.0"

    def __init__(self, app):
        super().__init__(app)
        self.media_mgr = MediaLibraryManager(app.data_dir)
        self.all_media = []

    def get_tabs(self):
        main_widget = MediaWidget(self)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("<b>Biblioteca de Medios</b>")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        filter_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Buscar por nombre, distro, tag...")
        self.input_search.textChanged.connect(self._filter_table)
        filter_layout.addWidget(self.input_search)

        self.combo_os = QComboBox()
        self.combo_os.addItems(["SO: Todos", "Linux", "Windows", "macOS", "Android", "Other"])
        self.combo_os.currentIndexChanged.connect(self._filter_table)
        filter_layout.addWidget(self.combo_os)

        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["Formato: Todos", "ISO", "QCOW2", "RAW", "VDI", "VMDK", "IMG"])
        self.combo_fmt.currentIndexChanged.connect(self._filter_table)
        filter_layout.addWidget(self.combo_fmt)
        layout.addLayout(filter_layout)

        toolbar_layout = QHBoxLayout()
        btn_add = QPushButton("Añadir archivo(s)"); btn_add.clicked.connect(self._add_files)
        btn_create = QPushButton("➕ Crear disco"); btn_create.clicked.connect(self._create_disk)
        btn_scan_dir = QPushButton("Escanear carpeta"); btn_scan_dir.clicked.connect(self._scan_folder)
        btn_scan_vms = QPushButton("Escanear VMs"); btn_scan_vms.clicked.connect(self._scan_vms)
        btn_refresh = QPushButton("🔄 Refrescar"); btn_refresh.clicked.connect(self._load_table)
        for b in (btn_add, btn_create, btn_scan_dir, btn_scan_vms, btn_refresh): toolbar_layout.addWidget(b)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Tipo", "SO", "Versión", "Arq.", 
            "Tamaño real", "Tamaño VM", "Usada por", "Estado", "Último uso"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table, 1)

        actions_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Modificar")
        self.btn_compact = QPushButton("Compactar")
        btn_verify = QPushButton("Verificar")
        btn_sha = QPushButton("Calcular SHA256")
        btn_delete = QPushButton("Eliminar")
        btn_open = QPushButton("Abrir carpeta")
        
        self.btn_edit.clicked.connect(self._modify_selected)
        self.btn_compact.clicked.connect(self._compact_selected)
        btn_verify.clicked.connect(self._verify_selected)
        btn_sha.clicked.connect(self._sha_selected)
        btn_delete.clicked.connect(self._delete_selected)
        btn_open.clicked.connect(self._open_folder_selected)

        for b in (self.btn_edit, self.btn_compact, btn_verify, btn_sha, btn_delete, btn_open):
            actions_layout.addWidget(b)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self._load_table()
        return [("Medios", main_widget)]

    def _load_table(self):
        self.all_media = self.media_mgr.get_all()
        self._refresh_table()

    def _refresh_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        search_txt = self.input_search.text().lower()
        os_filter = self.combo_os.currentText().replace("SO: ", "")
        fmt_filter = self.combo_fmt.currentText().replace("Formato: ", "")

        for media in self.all_media:
            if search_txt and search_txt not in media["name"].lower() and search_txt not in media.get("tags", "").lower(): continue
            if os_filter != "Todos" and media.get("os", "") != os_filter: continue
            if fmt_filter != "Todos" and media.get("format", "") != fmt_filter: continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            item_name = QTableWidgetItem(media["name"])
            item_name.setData(Qt.ItemDataRole.UserRole, media["id"])
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(media.get("type", "-")))
            self.table.setItem(row, 2, QTableWidgetItem(media.get("os", "Other")))
            self.table.setItem(row, 3, QTableWidgetItem(media.get("version", "-")))
            self.table.setItem(row, 4, QTableWidgetItem(media.get("arch", "-")))
            self.table.setItem(row, 5, QTableWidgetItem(media.get("size_real", "-")))
            self.table.setItem(row, 6, QTableWidgetItem(media.get("size_vm", "-")))
            self.table.setItem(row, 7, QTableWidgetItem(media.get("used_by", "-")))
            
            status_item = QTableWidgetItem(media.get("status", "OK"))
            if media.get("status") == "huérfano": status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 8, status_item)
            self.table.setItem(row, 9, QTableWidgetItem(media.get("last_used", "-")))

        self.table.setSortingEnabled(True)

    def _filter_table(self):
        self._refresh_table()

    def _get_selected_media(self):
        items = self.table.selectedItems()
        if not items: return None
        media_id = self.table.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return next((m for m in self.all_media if m["id"] == media_id), None)

    def _on_row_selected(self):
        media = self._get_selected_media()
        if media:
            self.btn_edit.setEnabled(True)
            self.btn_compact.setEnabled(media.get("format") == "QCOW2")
        else:
            self.btn_edit.setEnabled(False)
            self.btn_compact.setEnabled(False)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self.app.parent(), "Añadir medios", "", "Imágenes (*.iso *.img *.qcow2 *.raw *.vdi *.vmdk)")
        for f in files:
            name = os.path.basename(f)
            fmt = name.split('.')[-1].upper()
            m_type = "ISO" if fmt in ("ISO", "IMG") else "Disco duro"
            self.media_mgr.add_media(name, f, m_type, "-", fmt=fmt)
        self._load_table()

    def _create_disk(self):
        dlg = CreateDiskDialog(self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fmt_map = {"QCOW2": "qcow2", "RAW": "raw", "VDI": "vdi", "VMDK": "vmdk"}
            fmt = fmt_map.get(dlg.combo_type.currentText().split()[2], "qcow2")
            success, result = self.media_mgr.create_disk(dlg.input_name.text(), dlg.input_size.text(), fmt)
            if success:
                QMessageBox.information(self.app.parent(), "Éxito", f"Disco creado en:\n{result}")
                self._load_table()
            else:
                QMessageBox.critical(self.app.parent(), "Error", f"No se pudo crear el disco:\n{result}")

    def _scan_folder(self):
        folder = QFileDialog.getExistingDirectory(self.app.parent(), "Escanear carpeta")
        if folder:
            added = self.media_mgr.scan_directory(folder)
            QMessageBox.information(self.app.parent(), "Escaneo", f"Se han añadido {added} medios nuevos.")
            self._load_table()

    def _scan_vms(self):
        vms_dir = self.app.data_dir / "vms"
        added = self.media_mgr.scan_vms(vms_dir)
        QMessageBox.information(self.app.parent(), "Escanear VMs", f"Se han añadido {added} discos de VMs a la biblioteca.")
        self._load_table()

    def _modify_selected(self):
        media = self._get_selected_media()
        if not media: return
        dlg = ModifyMediaDialog(self.app.parent(), media)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.input_size and dlg.input_size.text() != media.get("size_vm"):
                success, msg = self.media_mgr.resize_disk(media["path"], dlg.input_size.text())
                if not success:
                    QMessageBox.critical(self.app.parent(), "Error al redimensionar", msg)
                    return
                else:
                    media["size_vm"] = self.media_mgr.get_virtual_size(media["path"])

            for m in self.all_media:
                if m["id"] == media["id"]:
                    m["name"] = dlg.input_name.text()
                    m["os"] = dlg.combo_os.currentText()
                    m["version"] = dlg.input_version.text()
                    m["tags"] = dlg.input_tags.text()
                    m["notes"] = dlg.input_notes.toPlainText()
                    break
            self.media_mgr.save()
            self._load_table()

    def _compact_selected(self):
        media = self._get_selected_media()
        if not media: return
        resp = QMessageBox.question(self.app.parent(), "Compactar", f"¿Compactar '{media['name']}'?")
        if resp == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self.app.parent(), "Procesando", "Compactando disco...")
            success, msg = self.media_mgr.compact_disk(media["path"])
            if success:
                QMessageBox.information(self.app.parent(), "Éxito", msg)
                self._load_table()
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)

    def _verify_selected(self):
        media = self._get_selected_media()
        if not media: return
        if os.path.exists(media["path"]):
            QMessageBox.information(self.app.parent(), "Verificar", "El archivo existe y es accesible.")
        else:
            QMessageBox.warning(self.app.parent(), "Verificar", "El archivo NO se encuentra en la ruta especificada.")

    def _sha_selected(self):
        media = self._get_selected_media()
        if not media: return
        QMessageBox.information(self.app.parent(), "Calculando...", "Calculando SHA256...")
        sha = self.media_mgr.get_sha256(media["path"])
        QMessageBox.information(self.app.parent(), "SHA256", f"Hash:\n{sha}")

    def _delete_selected(self):
        media = self._get_selected_media()
        if not media: return
        resp = QMessageBox.question(self.app.parent(), "Eliminar", f"¿Eliminar '{media['name']}' de la biblioteca?")
        if resp == QMessageBox.StandardButton.Yes:
            self.media_mgr.delete_media(media["id"])
            self._load_table()

    def _open_folder_selected(self):
        media = self._get_selected_media()
        if not media: return
        folder = os.path.dirname(media["path"])
        subprocess.Popen(["xdg-open", folder])