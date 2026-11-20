"""Diálogo para personalizar los atajos de teclado."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QScrollArea,
    QWidget, QPushButton, QDialogButtonBox, QMessageBox, QKeySequenceEdit,
)
from PyQt6.QtGui import QKeySequence

from services.shortcuts import COMMAND_LABELS, DEFAULT_SHORTCUTS


class ShortcutSettingsDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Atajos de teclado")
        self.resize(520, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Pulsa la combinación que quieras usar. Los cambios se aplican al aceptar."))

        area = QScrollArea()
        area.setWidgetResizable(True)
        contenedor = QWidget()
        formulario = QFormLayout(contenedor)
        self.edits = {}
        for nombre, etiqueta in COMMAND_LABELS.items():
            editor = QKeySequenceEdit()
            editor.setKeySequence(QKeySequence(store.get(nombre)))
            editor.setToolTip(f"Atajo por defecto: {DEFAULT_SHORTCUTS[nombre]}")
            self.edits[nombre] = editor
            formulario.addRow(etiqueta + ":", editor)
        area.setWidget(contenedor)
        layout.addWidget(area, 1)

        botones = QHBoxLayout()
        btn_reset = QPushButton("Restablecer valores")
        btn_reset.clicked.connect(self._restablecer)
        botones.addWidget(btn_reset)
        botones.addStretch()
        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText("Guardar")
        caja.accepted.connect(self._guardar)
        caja.rejected.connect(self.reject)
        botones.addWidget(caja)
        layout.addLayout(botones)

    def _restablecer(self):
        for nombre, editor in self.edits.items():
            editor.setKeySequence(QKeySequence(DEFAULT_SHORTCUTS[nombre]))

    def _guardar(self):
        # QKeySequenceEdit puede capturar varias secuencias separadas por coma.
        # Nos quedamos con la primera para mantener un atajo por acción.
        secuencias = {}
        for nombre, editor in self.edits.items():
            texto = editor.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
            secuencias[nombre] = texto.split(",")[0].strip()

        vistos = {}
        for nombre, texto in secuencias.items():
            if not texto:
                continue
            clave = texto.lower()
            if clave in vistos:
                QMessageBox.warning(
                    self, "Atajo duplicado",
                    f"'{texto}' está asignado a <b>{COMMAND_LABELS[vistos[clave]]}</b> "
                    f"y a <b>{COMMAND_LABELS[nombre]}</b>.")
                return
            vistos[clave] = nombre

        for nombre, texto in secuencias.items():
            self.store.set(nombre, texto)
        self.accept()
