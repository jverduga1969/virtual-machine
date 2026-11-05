import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QDialogButtonBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from services.media_library import MediaLibraryManager

class MediaLibraryDialog(QDialog):
    def __init__(self, parent=None, app=None, file_filters=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar desde la Biblioteca de Medios")
        self.resize(700, 450)
        self.selected_path = None
        self.app = app
        self.file_filters = file_filters or []
        
        # Conectar directamente con la base de datos de la biblioteca
        self.media_mgr = MediaLibraryManager(app.data_dir) if app else None

        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "SO", "Tamaño"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.accept)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.clicked.connect(self._load_files)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Seleccionar")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_layout.addWidget(btn_box)
        
        layout.addLayout(btn_layout)
        
        self._load_files()

    def _load_files(self):
        self.table.setRowCount(0)
        if not self.media_mgr:
            return

        # Obtener todos los medios registrados en la Biblioteca
        all_media = self.media_mgr.get_all()

        for media in all_media:
            path = media.get("path", "")
            if not path:
                continue

            # Filtrar por extensión si se solicitó (ej: solo .iso)
            ext = os.path.splitext(path)[1].lower()
            if self.file_filters and ext not in self.file_filters:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Nombre del archivo (o el nombre lógico que le hayas puesto en la biblioteca)
            display_name = media.get("name", os.path.basename(path))
            self.table.setItem(row, 0, QTableWidgetItem(display_name))
            
            # Tipo (ISO, Disco duro, etc.)
            self.table.setItem(row, 1, QTableWidgetItem(media.get("type", "-")))
            
            # SO
            self.table.setItem(row, 2, QTableWidgetItem(media.get("os", "Other")))
            
            # Tamaño real
            size_str = media.get("size_real", "")
            if not size_str:
                try:
                    size_bytes = os.path.getsize(path)
                    if size_bytes > 1024 * 1024 * 1024:
                        size_str = f"{size_bytes / (1024*1024*1024):.2f} GB"
                    else:
                        size_str = f"{size_bytes / (1024*1024):.1f} MB"
                except Exception:
                    size_str = "?"
            self.table.setItem(row, 3, QTableWidgetItem(size_str))
            
            # Guardar la ruta real oculta
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, path)

    def accept(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            super().accept()
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, selecciona un archivo de la lista.")