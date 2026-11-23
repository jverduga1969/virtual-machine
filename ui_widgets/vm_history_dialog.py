"""Diálogo para consultar y restaurar versiones anteriores de una VM."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDialogButtonBox,
    QMessageBox, QTextEdit,
)
from PyQt6.QtCore import Qt
from core.i18n import tr


CAMPOS_RESULTADOS = (
    ("name", "Nombre"), ("so", "Sistema operativo"),
    ("cores", "Nucleos"), ("ram", "RAM (MB)"),
    ("disk_path", "Disco"), ("iso_path", "ISO"),
    ("firmware_idx", "Firmware"), ("secure_boot", "Secure Boot"),
)


class VMHistoryDialog(QDialog):
    def __init__(self, repo, vm_id, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.vm_id = vm_id
        self.versiones = repo.get_history(vm_id)
        self.setWindowTitle(tr("Historial de {}").format(self._nombre_vm()))
        self.resize(720, 460)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Cada cambio de configuración guarda una versión. "
            "Selecciona una y pulsa <b>Restaurar</b> para volver a ella."))

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["#", "Fecha", "Motivo"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._mostrar_detalle)
        layout.addWidget(self.tabla, 1)

        self.detalle = QTextEdit()
        self.detalle.setReadOnly(True)
        self.detalle.setMaximumHeight(150)
        layout.addWidget(self.detalle)

        botones = QHBoxLayout()
        btn_restaurar = QPushButton("↩ Restaurar versión seleccionada")
        btn_restaurar.clicked.connect(self._restaurar)
        botones.addWidget(btn_restaurar)
        botones.addStretch()
        cerrar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        cerrar.rejected.connect(self.reject)
        botones.addWidget(cerrar)
        layout.addLayout(botones)

        self._cargar()

    def _nombre_vm(self):
        vm = self.repo.get(self.vm_id) or {}
        return vm.get("name", self.vm_id)

    def _cargar(self):
        self.tabla.setRowCount(0)
        for indice, entrada in enumerate(self.versiones):
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(len(self.versiones) - indice)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(self._fecha(entrada)))
            self.tabla.setItem(fila, 2, QTableWidgetItem(entrada.get("reason", "-")))
            self.tabla.item(fila, 0).setData(Qt.ItemDataRole.UserRole, indice)
        if self.tabla.rowCount():
            self.tabla.selectRow(0)
        else:
            self.detalle.setText("Todavía no hay versiones guardadas.")

    @staticmethod
    def _fecha(entrada):
        try:
            return datetime.fromisoformat(entrada["timestamp"]).strftime("%d/%m/%Y %H:%M:%S")
        except (KeyError, ValueError, TypeError):
            return str(entrada.get("timestamp", "-"))

    def _mostrar_detalle(self):
        filas = self.tabla.selectedItems()
        if not filas:
            return
        indice = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        vm = self.versiones[indice].get("vm", {})
        lineas = []
        for clave, etiqueta in CAMPOS_RESULTADOS:
            if clave in vm:
                lineas.append(f"<b>{etiqueta}:</b> {vm[clave]}")
        self.detalle.setHtml("<br>".join(lineas) or "Sin detalles.")

    def _restaurar(self):
        filas = self.tabla.selectedItems()
        if not filas:
            QMessageBox.warning(self, "Aviso", "Selecciona una versión.")
            return
        indice = self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        fecha = self.tabla.item(filas[0].row(), 1).text()
        respuesta = QMessageBox.question(
            self, "Restaurar configuración",
            f"¿Restaurar la versión del {fecha}?\n\n"
            "La configuración actual se guardará como otra versión, "
            "así que podrás deshacer esta restauración.")
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        if self.repo.restore(self.vm_id, indice):
            QMessageBox.information(self, "Restaurado", "Configuración restaurada.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo restaurar la versión.")
