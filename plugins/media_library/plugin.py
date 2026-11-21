import os
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QComboBox, QFormLayout, QDialog, QDialogButtonBox, 
    QToolButton, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from core.plugin_base import PluginBase
from core.i18n import original_key, tr
from services.media_library import MediaLibraryManager
from ui_widgets.download_iso_dialog import DownloadISODialog  # <-- NUEVO IMPORT
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
        self.input_name.setToolTip("Nombre con el que se identificará el medio en la biblioteca")
        form.addRow("Nombre:", self.input_name)
        self.combo_type = QComboBox()
        self.combo_type.setToolTip("Tipo de archivo de medio (disco duro o imagen ISO)")
        for texto, valor in (("Disco duro QCOW2 (recomendado)", "qcow2"),
                             ("Disco duro RAW", "raw"),
                             ("Disco duro VDI", "vdi"),
                             ("Disco duro VMDK", "vmdk")):
            self.combo_type.addItem(texto, valor)
        form.addRow("Tipo:", self.combo_type)
        self.combo_prealloc = QComboBox()
        self.combo_prealloc.setToolTip("Expandible: crece según se usa. Fijo: ocupa todo el espacio desde el inicio")
        for texto in ("Expandible (dinámico)", "Fijo (preasignado)"):
            self.combo_prealloc.addItem(texto, texto)
        form.addRow("Preasignación:", self.combo_prealloc)
        self.input_size = QLineEdit("40G")
        self.input_size.setToolTip("Tamaño del disco o imagen (ej: 40G, 100G)")
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
        self.btn_advanced.setText(tr("▼ Avanzado (rendimiento e I/O)" if v else "▶ Avanzado (rendimiento e I/O)"))

class ModifyMediaDialog(QDialog):
    def __init__(self, parent, media):
        super().__init__(parent)
        self.setWindowTitle(f"{tr('Modificar:')} {media['name']}")
        self.resize(400, 400)
        self.media = media
        layout = QFormLayout(self)
        self.input_name = QLineEdit(media["name"])
        layout.addRow("Nombre:", self.input_name)
        self.combo_os = QComboBox()
        for so in ("Linux", "Windows", "macOS", "Android", "Other"):
            self.combo_os.addItem(so, so)
        valor_os = original_key(media.get("os", "Other"))
        indice = self.combo_os.findData(valor_os)
        if indice >= 0:
            self.combo_os.setCurrentIndex(indice)
        layout.addRow("SO:", self.combo_os)
        self.input_version = QLineEdit(media.get("version", ""))
        layout.addRow("Versión:", self.input_version)
        self.input_size = None
        if original_key(media.get("type", "")) == "Disco duro":
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
    version = "1.6.0" # Versión actualizada

    def __init__(self, app):
        super().__init__(app)
        self.media_mgr = MediaLibraryManager(app.data_dir, app.settings)
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
        self.input_search.setToolTip("Buscar medios por nombre, distribución o etiqueta")
        self.input_search.textChanged.connect(self._filter_table)
        filter_layout.addWidget(self.input_search)

        self.combo_os = QComboBox()
        self.combo_os.setToolTip("Filtrar medios por sistema operativo")
        for texto in ("SO: Todos", "Linux", "Windows", "macOS", "Android", "Other"):
            valor = "Todos" if texto == "SO: Todos" else texto
            self.combo_os.addItem(texto, valor)
        self.combo_os.currentIndexChanged.connect(self._filter_table)
        filter_layout.addWidget(self.combo_os)

        self.combo_fmt = QComboBox()
        self.combo_fmt.setToolTip("Filtrar medios por formato de archivo")
        for texto in ("Formato: Todos", "ISO", "QCOW2", "RAW", "VDI", "VMDK", "IMG"):
            valor = "Todos" if texto == "Formato: Todos" else texto
            self.combo_fmt.addItem(texto, valor)
        self.combo_fmt.currentIndexChanged.connect(self._filter_table)
        filter_layout.addWidget(self.combo_fmt)
        layout.addLayout(filter_layout)

        toolbar_layout = QHBoxLayout()
        btn_add = QPushButton("Añadir archivo(s)")
        btn_add.setToolTip("Añadir archivos de imagen (ISO, QCOW2, RAW, VDI, VMDK) existentes a la biblioteca")
        btn_add.clicked.connect(self._add_files)
        btn_create = QPushButton("➕ Crear disco")
        btn_create.setToolTip("Crear un nuevo disco duro virtual en la biblioteca")
        btn_create.clicked.connect(self._create_disk)
        
        # NUEVO BOTÓN DE DESCARGA
        btn_download_iso = QPushButton("⬇️ Descargar ISO")
        btn_download_iso.setToolTip("Descargar una imagen ISO desde internet a la biblioteca")
        btn_download_iso.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_download_iso.clicked.connect(self._download_iso)
        
        btn_scan_dir = QPushButton("Escanear carpeta")
        btn_scan_dir.setToolTip("Escanear una carpeta en busca de imágenes de disco e ISOs")
        btn_scan_dir.clicked.connect(self._scan_folder)
        btn_scan_vms = QPushButton("Escanear VMs")
        btn_scan_vms.setToolTip("Escanear los directorios de las VMs en busca de discos")
        btn_scan_vms.clicked.connect(self._scan_vms)
        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setToolTip("Quitar medios que ya no existen y añadir los archivos nuevos de la biblioteca y la carpeta de ISOs")
        btn_refresh.clicked.connect(self._refresh_library)
        
        btn_rebuild = QPushButton("🔧 Reconstruir desde VMs")
        btn_rebuild.setToolTip("Actualizar la biblioteca: quitar medios huérfanos y agregar los referenciados por las VMs. Marca la hora exacta.")
        btn_rebuild.clicked.connect(self._rebuild_from_vms)
        
        for b in (btn_add, btn_create, btn_download_iso, btn_scan_dir, btn_scan_vms, btn_refresh, btn_rebuild): 
            toolbar_layout.addWidget(b)
            
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
        self.table._nvm_retranslate = self._refresh_table
        self.table.setStyleSheet(
            "QTableWidget::item:selected { background-color: #1976d2; color: white; }")
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

    # NUEVO MÉTODO
    def _download_iso(self):
        dlg = DownloadISODialog(self.app, self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Si la descarga terminó con éxito (el diálogo se acepta), recargamos la tabla
            self._load_table()

    def _load_table(self):
        self.media_mgr.load()
        repo = getattr(self.app, "vm_repo", None)
        if repo is not None:
            self.media_mgr.sync_usage(repo.get_all())
        self.all_media = self.media_mgr.get_all()
        self._refresh_table()

    def _refresh_library(self):
        """Sincroniza la biblioteca con los archivos realmente presentes."""
        self.media_mgr.load()
        extras = []
        isos_dir = getattr(self.app, "isos_dir", None)
        if isos_dir:
            extras.append(isos_dir)
        resultado = self.media_mgr.reconcile(extra_dirs=extras)
        self._load_table()

        eliminados = resultado["removed"]
        anadidos = resultado["added"]
        if eliminados or anadidos:
            QMessageBox.information(
                self.app.parent(), "Biblioteca actualizada",
                f"Medios eliminados (ya no existen): {eliminados}\n"
                f"Medios añadidos (encontrados en disco): {anadidos}"
            )
        else:
            QMessageBox.information(
                self.app.parent(), "Biblioteca actualizada",
                "No hay cambios: la biblioteca ya estaba sincronizada."
            )

    def _rebuild_from_vms(self):
        """Rebuild the media library from VM repository data.

        Calls the MediaLibraryManager.rebuild_from_vms() method and then
        reloads the table.
        """
        repo = getattr(self.app, "vm_repo", None)
        if repo is None:
            QMessageBox.warning(self.app.parent(), "Sin repositorio",
                "No se puede reconstruir: no hay repositorio de VMs disponible.")
            return
        try:
            self.media_mgr.rebuild_from_vms(repo)
            QMessageBox.information(
                self.app.parent(), "Biblioteca reconstruida",
                "La biblioteca de medios ha sido reconstruida desde la configuración de las VMs."
            )
            self._load_table()
        except Exception as e:
            log.error(f"Error al reconstruir biblioteca desde VMs: {e}")
            QMessageBox.critical(
                self.app.parent(), "Error",
                f"Error al reconstruir la biblioteca:\n{e}"
            )

    def _refresh_table(self):
        # Conservar la fila seleccionada aunque la tabla se recargue (cambio de
        # idioma, showEvent, filtros...). Si no, los botones parecen no responder.
        selected_id = None
        actual = self._get_selected_media()
        if actual:
            selected_id = actual.get("id")

        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        fila_restaurada = -1
        search_txt = self.input_search.text().lower()
        os_filter = self.combo_os.currentData() or "Todos"
        fmt_filter = self.combo_fmt.currentData() or "Todos"

        for media in self.all_media:
            if search_txt and search_txt not in media["name"].lower() and search_txt not in media.get("tags", "").lower(): continue
            if os_filter != "Todos" and media.get("os", "") != os_filter: continue
            if fmt_filter != "Todos" and media.get("format", "") != fmt_filter: continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            if selected_id is not None and media.get("id") == selected_id:
                fila_restaurada = row
            item_name = QTableWidgetItem(media["name"])
            item_name.setData(Qt.ItemDataRole.UserRole, media["id"])
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(tr(media.get("type", "-"))))
            self.table.setItem(row, 2, QTableWidgetItem(tr(media.get("os", "Other"))))
            self.table.setItem(row, 3, QTableWidgetItem(media.get("version", "-")))
            self.table.setItem(row, 4, QTableWidgetItem(media.get("arch", "-")))
            self.table.setItem(row, 5, QTableWidgetItem(media.get("size_real", "-")))
            self.table.setItem(row, 6, QTableWidgetItem(media.get("size_vm", "-")))
            self.table.setItem(row, 7, QTableWidgetItem(media.get("used_by", "-")))
            
            status_item = QTableWidgetItem(tr(media.get("status", "OK")))
            if media.get("status") == "huérfano": status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 8, status_item)
            self.table.setItem(row, 9, QTableWidgetItem(media.get("last_used", "-")))

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        if fila_restaurada >= 0:
            self.table.selectRow(fila_restaurada)
        self._on_row_selected()

    def _filter_table(self):
        self._refresh_table()

    def _get_selected_media(self):
        items = self.table.selectedItems()
        if not items: return None
        item = self.table.item(items[0].row(), 0)
        if item is None: return None
        media_id = item.data(Qt.ItemDataRole.UserRole)
        return next((m for m in self.all_media if m["id"] == media_id), None)

    def _selected_or_warn(self):
        """Media seleccionada o aviso visible: los botones nunca quedan mudos."""
        media = self._get_selected_media()
        if media is None:
            QMessageBox.information(
                self.app.parent(), tr("Medios"),
                tr("Selecciona un medio en la tabla."))
        return media

    def _on_row_selected(self):
        # Se mantienen activos para que, sin selección, expliquen qué pasa.
        for boton in (getattr(self, "btn_edit", None),
                      getattr(self, "btn_compact", None)):
            if boton is not None:
                boton.setEnabled(True)

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
            fmt = dlg.combo_type.currentData() or "qcow2"
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
        vms_dir = self.app.vms_dir
        added = self.media_mgr.scan_vms(vms_dir)
        QMessageBox.information(self.app.parent(), "Escanear VMs", f"Se han añadido {added} discos de VMs a la biblioteca.")
        self._load_table()

    def _modify_selected(self):
        media = self._selected_or_warn()
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
                    m["os"] = dlg.combo_os.currentData() or dlg.combo_os.currentText()
                    m["version"] = dlg.input_version.text()
                    m["tags"] = dlg.input_tags.text()
                    m["notes"] = dlg.input_notes.toPlainText()
                    break
            self.media_mgr.save()
            self._load_table()

    def _compact_selected(self):
        media = self._selected_or_warn()
        if not media: return
        if media.get("format") != "QCOW2":
            QMessageBox.warning(
                self.app.parent(), tr("Compactar"),
                tr("Solo se pueden compactar discos QCOW2."))
            return
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
        media = self._selected_or_warn()
        if not media: return
        if os.path.exists(media["path"]):
            QMessageBox.information(self.app.parent(), "Verificar", "El archivo existe y es accesible.")
        else:
            QMessageBox.warning(self.app.parent(), "Verificar", "El archivo NO se encuentra en la ruta especificada.")

    def _sha_selected(self):
        media = self._selected_or_warn()
        if not media: return
        QMessageBox.information(self.app.parent(), "Calculando...", "Calculando SHA256...")
        sha = self.media_mgr.get_sha256(media["path"])
        QMessageBox.information(self.app.parent(), "SHA256", f"Hash:\n{sha}")

    def _delete_selected(self):
        media = self._selected_or_warn()
        if not media: return
        resp = QMessageBox.question(self.app.parent(), "Eliminar", f"¿Eliminar '{media['name']}' de la biblioteca?")
        if resp == QMessageBox.StandardButton.Yes:
            self.media_mgr.delete_media(media["id"])
            self._load_table()

    def _open_folder_selected(self):
        media = self._selected_or_warn()
        if not media: return
        folder = os.path.dirname(media["path"]) or str(Path.home())
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            QMessageBox.critical(self.app.parent(), tr("Error"), str(e))