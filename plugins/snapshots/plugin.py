import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit,
    QGroupBox, QComboBox, QCheckBox, QSpinBox, QRadioButton, 
    QStackedWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsLineItem, QStyle,
    QToolButton, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor, QIcon, QFont
from core.plugin_base import PluginBase
from services.snapshot_manager import SnapshotManager
from services.backup_scheduler import BackupScheduler
import logging
log = logging.getLogger(__name__)




# ==========================================
# VISTA DE ORGANIGRAMA (QGraphicsView)
# ==========================================
class SnapshotGraphView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#2b2b2b")))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.zoom_level = 100

    def load_snapshots(self, snapshots):
        self.scene.clear()
        if not snapshots: return

        y_offset = 20
        x_offset = 20
        prev_rect = None

        for snap in snapshots:
            rect = QGraphicsRectItem(0, 0, 180, 120)
            rect.setPos(x_offset, y_offset)
            rect.setBrush(QBrush(QColor("#333333")))
            rect.setPen(QPen(QColor("#555555")))
            rect.setFlags(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
            rect.setData(0, snap["name"])
            
            thumb_path = snap.get("thumbnail", "")
            if thumb_path and os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
            else:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
                pixmap = icon.pixmap(160, 80)

            pixmap = pixmap.scaled(160, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap_item = QGraphicsPixmapItem(pixmap, rect)
            pixmap_item.setPos(10, 10)

            text_item = QGraphicsTextItem(snap["name"], rect)
            text_item.setDefaultTextColor(QColor("#ffffff"))
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            text_item.setFont(font)
            text_item.setPos(10, 95)

            self.scene.addItem(rect)

            if prev_rect:
                line = QGraphicsLineItem(
                    prev_rect.pos().x() + 90, prev_rect.pos().y() + 120,
                    rect.pos().x() + 90, rect.pos().y()
                )
                line.setPen(QPen(QColor("#3b82f6"), 2))
                self.scene.addItem(line)
                line.setZValue(-1)

            prev_rect = rect
            y_offset += 160

        self.setSceneRect(self.scene.itemsBoundingRect())
        self.fit_in_view()

    def zoom_in(self):
        self.zoom_level += 10
        self.scale(1.1, 1.1)

    def zoom_out(self):
        self.zoom_level -= 10
        if self.zoom_level < 10: self.zoom_level = 10
        self.scale(0.9, 0.9)

    def reset_zoom(self):
        self.zoom_level = 100
        self.resetTransform()

    def fit_in_view(self):
        self.zoom_level = 100
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

# ==========================================
# DIÁLOGO DE NUEVO SNAPSHOT
# ==========================================
class NewSnapshotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Snapshot")
        self.resize(400, 300)
        layout = QFormLayout(self)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Ej. Antes de instalar drivers")
        layout.addRow("Nombre:", self.input_name)
        self.input_desc = QTextEdit()
        self.input_desc.setPlaceholderText("Descripción opcional...")
        self.input_desc.setMaximumHeight(100)
        layout.addRow("Descripción:", self.input_desc)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

# ==========================================
# WIDGET PRINCIPAL
# ==========================================
class SnapshotWidget(QWidget):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def showEvent(self, event):
        super().showEvent(event)
        self.plugin.refresh_all()

class Plugin(PluginBase):
    name = "Snapshots"
    version = "1.8.2"

    def __init__(self, app):
        super().__init__(app)
        self.snap_mgr = SnapshotManager(app.data_dir, getattr(app, 'vms_dir', None))
        self.current_vm_id = None
        self.scheduler = BackupScheduler(
            getattr(app, "settings", None), app.data_dir, self.snap_mgr)

        # Comprueba las programaciones aunque el usuario no visite esta pestaña.
        # PluginBase no es QObject: el dueño del timer es AppContext.
        self._timer = QTimer(self.app)
        self._timer.setInterval(self.scheduler.check_interval_ms)
        self._timer.timeout.connect(self._run_schedules)
        self._timer.start()

    def get_tabs(self):
        main_widget = SnapshotWidget(self)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("<b>Snapshots de la máquina virtual</b>")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Los snapshots en caliente guardan RAM y estado. Los snapshots en frío solo discos.")
        info.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info)

        toolbar = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setToolTip("Refrescar la lista de snapshots y el estado del disco")
        self.btn_create = QPushButton("➕ Crear")
        self.btn_create.setToolTip("Crear un nuevo punto de restauración de la VM")
        self.btn_restore = QPushButton("↩ Restaurar")
        self.btn_restore.setToolTip("Restaurar la VM al snapshot seleccionado")
        self.btn_delete = QPushButton("🗑 Eliminar")
        self.btn_delete.setToolTip("Eliminar el snapshot seleccionado")
        self.btn_refresh.clicked.connect(self.refresh_all)
        self.btn_create.clicked.connect(self._create_snapshot)
        self.btn_restore.clicked.connect(self._restore_snapshot)
        self.btn_delete.clicked.connect(self._delete_snapshot)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_create)
        toolbar.addWidget(self.btn_restore)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table_disk = QTableWidget(0, 7)
        self.table_disk.setHorizontalHeaderLabels(["Dispositivo", "Formato", "Tamaño virtual", "Tamaño archivo", "Libre host", "Escritura", "Snapshot"])
        self.table_disk.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_disk.setMaximumHeight(60)
        layout.addWidget(self.table_disk)

        self.lbl_warning = QLabel("")
        self.lbl_warning.setStyleSheet("color: #c62828; font-weight: bold; margin: 5px 0;")
        layout.addWidget(self.lbl_warning)

        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("Vista:"))
        self.radio_list = QRadioButton("📋 Lista")
        self.radio_list.setToolTip("Ver snapshots en forma de tabla")
        self.radio_list.setChecked(True)
        self.radio_tree = QRadioButton("🌳 Organigrama")
        self.radio_tree.setToolTip("Ver snapshots en forma de árbol jerárquico")
        self.radio_list.toggled.connect(self._toggle_view)
        self.radio_tree.toggled.connect(self._toggle_view)
        view_layout.addWidget(self.radio_list)
        view_layout.addWidget(self.radio_tree)
        view_layout.addStretch()
        layout.addLayout(view_layout)

        self.toolbar_graph = QWidget()
        toolbar_graph_layout = QHBoxLayout(self.toolbar_graph)
        toolbar_graph_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_zoom_out = QPushButton("🔍−")
        self.btn_zoom_out.setToolTip("Alejar el zoom del organigrama")
        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setToolTip("Acercar el zoom del organigrama")
        self.btn_fit = QPushButton("⊞ Ajustar")
        self.btn_fit.setToolTip("Ajustar el organigrama al panel")
        self.btn_real = QPushButton("1:1")
        self.btn_real.setToolTip("Tamaño real del organigrama")
        
        self.btn_zoom_out.clicked.connect(lambda: self.graph_view.zoom_out())
        self.btn_zoom_in.clicked.connect(lambda: self.graph_view.zoom_in())
        self.btn_fit.clicked.connect(lambda: self.graph_view.fit_in_view())
        self.btn_real.clicked.connect(lambda: self.graph_view.reset_zoom())
        
        toolbar_graph_layout.addWidget(QLabel("Zoom:"))
        toolbar_graph_layout.addWidget(self.btn_zoom_out)
        toolbar_graph_layout.addWidget(self.btn_zoom_in)
        toolbar_graph_layout.addWidget(self.btn_fit)
        toolbar_graph_layout.addWidget(self.btn_real)
        toolbar_graph_layout.addStretch()
        
        self.toolbar_graph.setVisible(False)
        layout.addWidget(self.toolbar_graph)

        self.stack_views = QStackedWidget()
        
        self.table_snaps = QTableWidget(0, 5)
        self.table_snaps.setHorizontalHeaderLabels(["ID", "Nombre", "Tamaño VM", "Fecha", "Reloj VM"])
        self.table_snaps.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_snaps.horizontalHeader().setStretchLastSection(True)
        self.table_snaps.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_snaps.itemSelectionChanged.connect(self._on_snap_selected)
        self.stack_views.addWidget(self.table_snaps)

        self.graph_view = SnapshotGraphView()
        self.graph_view.scene.selectionChanged.connect(self._on_graph_selected)
        self.stack_views.addWidget(self.graph_view)

        layout.addWidget(self.stack_views, 1)

        self.preview_group = QGroupBox("Previsualización")
        preview_layout = QVBoxLayout(self.preview_group)
        
        self.preview_label = QLabel("Sin captura de pantalla")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #1e1e1e; color: #888; border: 1px solid #333;")
        self.preview_label.setMinimumHeight(150)
        preview_layout.addWidget(self.preview_label)
        
        self.lbl_details = QLabel("")
        self.lbl_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_details.setStyleSheet("color: #aaa; font-size: 12px; padding: 5px;")
        preview_layout.addWidget(self.lbl_details)
        
        layout.addWidget(self.preview_group)

        group_sched = QGroupBox("Snapshots y backups programados (por VM)")
        sched_layout = QFormLayout(group_sched)
        self.check_sched = QCheckBox("Activar programación automática")
        self.check_sched.setToolTip("Crear snapshots de esta VM según la frecuencia elegida")
        sched_layout.addRow("", self.check_sched)
        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["Diario", "Semanal", "Mensual"])
        self.combo_freq.setCurrentText("Semanal")
        self.combo_freq.setToolTip("Cada cuánto se ejecutará la programación")
        sched_layout.addRow("Frecuencia:", self.combo_freq)
        self.spin_keep = QSpinBox()
        self.spin_keep.setRange(1, 50)
        self.spin_keep.setValue(5)
        self.spin_keep.setToolTip("Número de snapshots y backups a conservar")
        sched_layout.addRow("Conservar:", self.spin_keep)

        self.check_backup = QCheckBox("Copiar también el disco (solo con la VM apagada)")
        self.check_backup.setToolTip("Guarda una copia de la configuración y del disco en la carpeta de backups")
        sched_layout.addRow("", self.check_backup)

        dir_layout = QHBoxLayout()
        self.lbl_backup_dir = QLabel(self.scheduler.get_backup_dir())
        self.lbl_backup_dir.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_backup_dir.setWordWrap(True)
        btn_backup_dir = QToolButton()
        btn_backup_dir.setText("…")
        btn_backup_dir.setToolTip("Elegir la carpeta de backups")
        btn_backup_dir.clicked.connect(self._choose_backup_dir)
        btn_backup_now = QPushButton("💾 Backup ahora")
        btn_backup_now.setToolTip("Crear un backup inmediato de la VM seleccionada")
        btn_backup_now.clicked.connect(self._backup_now)
        dir_layout.addWidget(self.lbl_backup_dir, 1)
        dir_layout.addWidget(btn_backup_dir)
        dir_layout.addWidget(btn_backup_now)
        sched_layout.addRow("Carpeta:", dir_layout)

        self.lbl_sched_status = QLabel("Selecciona una VM para ver su programación.")
        self.lbl_sched_status.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_sched_status.setWordWrap(True)
        sched_layout.addRow("", self.lbl_sched_status)

        self.check_sched.toggled.connect(self._save_schedule)
        self.combo_freq.currentIndexChanged.connect(self._save_schedule)
        self.spin_keep.valueChanged.connect(self._save_schedule)
        self.check_backup.toggled.connect(self._save_schedule)
        layout.addWidget(group_sched)

        self.app.vm_selection_changed.connect(self._on_vm_selected)
        # Si la pestaña se crea después de seleccionar una VM, tomar el id actual.
        initial = (getattr(self.app.parent(), "_last_selected_id", None)
                   or getattr(self.app, "_selected_vm_id", None))
        if initial:
            self.current_vm_id = initial
            self._load_schedule()
        return [("Snapshots", main_widget)]

    def _on_vm_selected(self, vm_id: str):
        self.current_vm_id = vm_id
        self._load_schedule()
        self.refresh_all()

    # ------------------------------------------------------------ programación
    def _load_schedule(self):
        if not self.current_vm_id:
            self.lbl_sched_status.setText("Selecciona una VM para ver su programación.")
            return
        sched = self.scheduler.get_schedule(self.current_vm_id)
        # Bloquear señales mientras se cargan los valores guardados.
        for control in (self.check_sched, self.combo_freq, self.spin_keep, self.check_backup):
            control.blockSignals(True)
        self.check_sched.setChecked(sched["enabled"])
        self.combo_freq.setCurrentText(sched["freq"])
        self.spin_keep.setValue(sched["keep"])
        self.check_backup.setChecked(sched["backup"])
        for control in (self.check_sched, self.combo_freq, self.spin_keep, self.check_backup):
            control.blockSignals(False)
        self.lbl_backup_dir.setText(self.scheduler.get_backup_dir())
        self._update_sched_status()

    def _save_schedule(self, *_args):
        if not self.current_vm_id:
            return
        self.scheduler.set_schedule(
            self.current_vm_id,
            self.check_sched.isChecked(),
            self.combo_freq.currentText(),
            self.spin_keep.value(),
            self.check_backup.isChecked(),
        )
        self._update_sched_status()

    def _update_sched_status(self):
        if not self.current_vm_id:
            return
        sched = self.scheduler.get_schedule(self.current_vm_id)
        if not sched["enabled"]:
            self.lbl_sched_status.setText("Programación desactivada para esta VM.")
            return
        last = self.scheduler.parse_last_run(sched["last_run"])
        ultimo = last.strftime("%d/%m/%Y %H:%M") if last else "nunca"
        backups = len(self.scheduler.list_backups(self.current_vm_id))
        self.lbl_sched_status.setText(
            f"Última ejecución: {ultimo} · Frecuencia: {sched['freq'].lower()} · "
            f"Backups guardados: {backups}")

    def _choose_backup_dir(self):
        actual = self.scheduler.get_backup_dir()
        elegido = QFileDialog.getExistingDirectory(
            self.app.parent(), "Carpeta de backups", actual)
        if elegido:
            self.scheduler.set_backup_dir(elegido)
            self.lbl_backup_dir.setText(elegido)

    def _backup_now(self):
        if not self.current_vm_id:
            QMessageBox.warning(self.app.parent(), "Aviso", "Selecciona una VM.")
            return
        vm = self.app.get_vm(self.current_vm_id)
        if not vm:
            return
        resultado = self.scheduler.create_backup(vm, repo=self.app.vm_repo)
        self.scheduler.prune(self.current_vm_id, self.scheduler.get_schedule(self.current_vm_id)["keep"])
        self._update_sched_status()
        detalle = resultado["note"] or (
            "Se copiaron la configuración y el disco." if resultado["disk"]
            else "Se guardó la configuración.")
        QMessageBox.information(
            self.app.parent(), "Backup creado",
            f"{detalle}\n\nUbicación: {resultado['path']}")

    def _run_schedules(self):
        """Disparado por el QTimer; no muestra diálogos para no molestar."""
        vms = self.app.get_vms() if hasattr(self.app, "get_vms") else []
        resultados = self.scheduler.run_due(vms)
        if not resultados:
            return
        for resultado in resultados:
            log.info("Programación ejecutada: %s", resultado)
        if self.current_vm_id:
            self._update_sched_status()
            self.refresh_all()

    def _toggle_view(self):
        if self.radio_list.isChecked():
            self.stack_views.setCurrentIndex(0)
            self.preview_group.setVisible(True)
            self.toolbar_graph.setVisible(False)
        else:
            self.stack_views.setCurrentIndex(1)
            self.preview_group.setVisible(False)
            self.toolbar_graph.setVisible(True)

    def refresh_all(self):
        self.table_disk.setRowCount(0)
        self.table_snaps.setRowCount(0)
        self.lbl_warning.setText("")
        self.preview_label.setText("Sin captura de pantalla")
        self.preview_label.setPixmap(QPixmap())
        self.lbl_details.setText("")

        if not self.current_vm_id: return
        vm = self.app.get_vm(self.current_vm_id)
        if not vm: return

        disk_info = self.snap_mgr.get_disk_info(vm)
        if disk_info:
            row = self.table_disk.rowCount()
            self.table_disk.insertRow(row)
            self.table_disk.setItem(row, 0, QTableWidgetItem(disk_info["device"]))
            self.table_disk.setItem(row, 1, QTableWidgetItem(disk_info["format"]))
            self.table_disk.setItem(row, 2, QTableWidgetItem(disk_info["virtual_size"]))
            self.table_disk.setItem(row, 3, QTableWidgetItem(disk_info["file_size"]))
            self.table_disk.setItem(row, 4, QTableWidgetItem(disk_info["host_free"]))
            self.table_disk.setItem(row, 5, QTableWidgetItem(disk_info["writable"]))
            self.table_disk.setItem(row, 6, QTableWidgetItem(disk_info["snapshot_capable"]))

        snapshots = self.snap_mgr.list_snapshots(vm)
        
        for snap in snapshots:
            row = self.table_snaps.rowCount()
            self.table_snaps.insertRow(row)
            self.table_snaps.setItem(row, 0, QTableWidgetItem(str(snap["id"])))
            
            item_name = QTableWidgetItem(snap["name"])
            if snap.get("desc"): item_name.setToolTip(snap["desc"])
            self.table_snaps.setItem(row, 1, item_name)
            
            self.table_snaps.setItem(row, 2, QTableWidgetItem(snap["size"]))
            self.table_snaps.setItem(row, 3, QTableWidgetItem(snap["date"]))
            self.table_snaps.setItem(row, 4, QTableWidgetItem(snap["vm_clock"]))
            
            self.table_snaps.item(row, 0).setData(Qt.ItemDataRole.UserRole, snap)

        self.graph_view.load_snapshots(snapshots)

    def _on_snap_selected(self):
        items = self.table_snaps.selectedItems()
        if not items: return
        snap_data = self.table_snaps.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        self._update_preview(snap_data)

    def _on_graph_selected(self):
        items = self.graph_view.scene.selectedItems()
        if not items: return
        snap_name = items[0].data(0)
        
        for row in range(self.table_snaps.rowCount()):
            if self.table_snaps.item(row, 1).text() == snap_name:
                snap_data = self.table_snaps.item(row, 0).data(Qt.ItemDataRole.UserRole)
                self._update_preview(snap_data)
                break

    def _update_preview(self, snap_data):
        if not snap_data: return
        
        thumb_path = snap_data.get("thumbnail", "")
        if thumb_path and os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.width(), self.preview_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.preview_label.setText("Sin captura de pantalla")
            self.preview_label.setPixmap(QPixmap())
            
        self.lbl_details.setText(f"<b>{snap_data['name']}</b> | {snap_data['date']} | Reloj VM: {snap_data['vm_clock']}")

    def _create_snapshot(self):
        if not self.current_vm_id: return
        dlg = NewSnapshotDialog(self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.input_name.text().strip()
            desc = dlg.input_desc.toPlainText().strip()
            if not name: return
            
            vm = self.app.get_vm(self.current_vm_id)
            success, msg = self.snap_mgr.create_snapshot(vm, name, desc)
            if success:
                QMessageBox.information(self.app.parent(), "Éxito", msg)
                self.refresh_all()
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)

    def _restore_snapshot(self):
        if not self.current_vm_id: return
        
        snap_name = None
        if self.radio_list.isChecked():
            row = self.table_snaps.currentRow()
            if row >= 0: snap_name = self.table_snaps.item(row, 1).text()
        else:
            items = self.graph_view.scene.selectedItems()
            if items: snap_name = items[0].data(0)

        if not snap_name:
            QMessageBox.warning(self.app.parent(), "Aviso", "Selecciona un snapshot.")
            return

        resp = QMessageBox.question(self.app.parent(), "Restaurar", f"¿Restaurar '{snap_name}'?")
        if resp == QMessageBox.StandardButton.Yes:
            vm = self.app.get_vm(self.current_vm_id)
            success, msg = self.snap_mgr.restore_snapshot(vm, snap_name)
            if success:
                QMessageBox.information(self.app.parent(), "Éxito", msg)
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)

    def _delete_snapshot(self):
        if not self.current_vm_id: return
        
        snap_name = None
        if self.radio_list.isChecked():
            row = self.table_snaps.currentRow()
            if row >= 0: snap_name = self.table_snaps.item(row, 1).text()
        else:
            items = self.graph_view.scene.selectedItems()
            if items: snap_name = items[0].data(0)

        if not snap_name:
            QMessageBox.warning(self.app.parent(), "Aviso", "Selecciona un snapshot.")
            return

        resp = QMessageBox.question(self.app.parent(), "Eliminar", f"¿Eliminar '{snap_name}'?")
        if resp == QMessageBox.StandardButton.Yes:
            vm = self.app.get_vm(self.current_vm_id)
            success, msg = self.snap_mgr.delete_snapshot(vm, snap_name)
            if success:
                QMessageBox.information(self.app.parent(), "Éxito", msg)
                self.refresh_all()
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)