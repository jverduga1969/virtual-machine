"""Diálogos para guardar y usar plantillas de VM."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QTextEdit, QDialogButtonBox, QListWidget, QListWidgetItem,
    QMessageBox,
)

from services.vm_templates import ICONOS
from core.i18n import tr


class SaveTemplateDialog(QDialog):
    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guardar como plantilla")
        self.resize(440, 320)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_name = QLineEdit(f"{vm.get('name', 'VM')} — plantilla")
        self.input_name.setToolTip("Nombre con el que aparecerá la plantilla")
        form.addRow("Nombre:", self.input_name)

        self.combo_icon = QComboBox()
        self.combo_icon.addItems(ICONOS)
        self.combo_icon.setToolTip("Icono de la plantilla")
        form.addRow("Icono:", self.combo_icon)

        self.input_desc = QTextEdit()
        self.input_desc.setPlaceholderText("Ej. Ubuntu de desarrollo con 4 núcleos y 8 GB")
        self.input_desc.setMaximumHeight(90)
        form.addRow("Descripción:", self.input_desc)
        layout.addLayout(form)

        aviso = QLabel(
            "Se guardarán los ajustes de hardware (CPU, RAM, firmware, red, audio...). "
            "El disco y el nombre de la VM no se incluyen.")
        aviso.setWordWrap(True)
        aviso.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(aviso)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Guardar")
        botones.accepted.connect(self._validar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _validar(self):
        if not self.input_name.text().strip():
            QMessageBox.warning(self, "Aviso", "Ponle un nombre a la plantilla.")
            return
        self.accept()

    @property
    def template_name(self):
        return self.input_name.text().strip()

    @property
    def template_icon(self):
        return self.combo_icon.currentText()

    @property
    def template_description(self):
        return self.input_desc.toPlainText().strip()


class TemplatePickerDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Nueva VM desde plantilla")
        self.resize(560, 420)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Elige una plantilla y ponle nombre a la nueva VM:"))

        self.lista = QListWidget()
        self.lista.setToolTip("Plantillas guardadas")
        for plantilla in manager.list_templates():
            item = QListWidgetItem(
                f"{plantilla.get('icon', '📋')}  {plantilla['name']}")
            item.setToolTip(plantilla.get("description", ""))
            item.setData(0x0100, plantilla["id"])
            self.lista.addItem(item)
        if self.lista.count():
            self.lista.setCurrentRow(0)
        layout.addWidget(self.lista, 1)

        form = QFormLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre de la nueva VM")
        self.input_name.textChanged.connect(self._actualizar_placeholder)
        form.addRow("Nombre:", self.input_name)
        self.lbl_detalle = QLabel("Selecciona una plantilla.")
        self.lbl_detalle.setWordWrap(True)
        self.lbl_detalle.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", self.lbl_detalle)
        layout.addLayout(form)
        self.lista.itemSelectionChanged.connect(self._mostrar_detalle)
        self._mostrar_detalle()

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Crear VM")
        botones.accepted.connect(self._validar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _mostrar_detalle(self):
        actual = self.lista.currentItem()
        if not actual:
            self.lbl_detalle.setText("No hay plantillas guardadas.")
            return
        plantilla = self.manager.get_template(actual.data(0x0100))
        if plantilla:
            config = plantilla.get("config", {})
            self.lbl_detalle.setText(tr(
                "{} · {} núcleos · {} MB · Disco {}").format(
                    plantilla.get('description', ''),
                    config.get('cores', '?'),
                    config.get('ram', '?'),
                    config.get('disk_size', '?')))
        self._actualizar_placeholder()

    def _actualizar_placeholder(self, *_args):
        actual = self.lista.currentItem()
        if actual and not self.input_name.text().strip():
            plantilla = self.manager.get_template(actual.data(0x0100))
            if plantilla:
                self.input_name.setPlaceholderText(
                    tr("VM desde {}").format(plantilla['name']))

    def _validar(self):
        if not self.lista.currentItem():
            QMessageBox.warning(self, "Aviso", "No hay plantillas. Guarda una primero.")
            return
        self.accept()

    @property
    def selected_id(self):
        actual = self.lista.currentItem()
        return actual.data(0x0100) if actual else None

    @property
    def vm_name(self):
        return self.input_name.text().strip()
