# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Diálogo unificado de progreso para tareas largas: descargas de ISOs,
conversión de imágenes con dmg2img, esperas del Guest Agent, etc.

Antes convivían 3 estilos distintos: QProgressDialog suelto en
install_flow_mixin, otro en mac_recovery_mixin, y QMessageBox para QGA.
Este widget centraliza barra + estado + consola + botón cancelar.

No conoce nada del dominio (QEMU, ISOs, workers). Solo recibe señales
genéricas: set_progress(percent, text), append_log(line), finish(...).
"""
import time
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QPlainTextEdit, QSizePolicy,
)


class TaskProgressDialog(QDialog):
    """Diálogo de progreso reutilizable.

    Uso:
        dlg = TaskProgressDialog("Descargando Ubuntu 24.04", self)
        worker.progress_signal.connect(dlg.set_progress)
        worker.log_signal.connect(dlg.append_log)
        worker.finished_signal.connect(lambda c: dlg.finish(c == 0, "..."))
        dlg.canceled.connect(worker.request_cancel)
        dlg.show()
    """
    canceled = pyqtSignal()

    def __init__(self, title, parent=None, cancelable=True, show_log=True, subtitle=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.setMinimumWidth(560)
        self.resize(620, 340 if show_log else 200)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self._cancelable = cancelable
        self._finished = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._title_label = QLabel(f"<b>{title}</b>")
        self._title_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._title_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#666; font-size: 11px;")
            sub.setWordWrap(True)
            layout.addWidget(sub)

        self._status_label = QLabel("Iniciando…")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self._status_label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setMinimumHeight(22)
        layout.addWidget(self._bar)

        self._log_edit = None
        if show_log:
            self._log_edit = QPlainTextEdit()
            self._log_edit.setReadOnly(True)
            self._log_edit.setMaximumBlockCount(500)
            self._log_edit.setStyleSheet(
                "background:#0d1117; color:#7ee787; font-family:monospace; "
                "font-size:11px; border:1px solid #232b40; border-radius:6px;"
            )
            self._log_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._log_edit.setMinimumHeight(90)
            layout.addWidget(self._log_edit, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.setVisible(cancelable)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        buttons.addWidget(self._cancel_btn)
        self._close_btn = QPushButton("Cerrar")
        self._close_btn.setVisible(False)
        self._close_btn.clicked.connect(self.accept)
        buttons.addWidget(self._close_btn)
        layout.addLayout(buttons)

    # ------------------------------------------------------------------ API

    def set_progress(self, percent, text=""):
        """percent < 0 → indeterminado. 0..100 → determinado."""
        self._finished = False
        self._close_btn.setVisible(False)
        self._cancel_btn.setVisible(self._cancelable)
        if percent < 0:
            if not (self._bar.minimum() == 0 and self._bar.maximum() == 0):
                self._bar.setRange(0, 0)
            self._bar.setTextVisible(False)
        else:
            if self._bar.minimum() == 0 and self._bar.maximum() == 0:
                self._bar.setRange(0, 100)
            self._bar.setTextVisible(True)
            self._bar.setValue(max(0, min(100, int(percent))))
        if text:
            self._status_label.setText(text)
        if not self.isVisible():
            self.show()
            self.raise_()
            self.activateWindow()

    def append_log(self, line):
        if self._log_edit is not None and line:
            self._log_edit.appendPlainText(str(line))

    def finish(self, success, message=""):
        """Cierra con éxito, o deja visible el error para que el usuario lo lea."""
        self._finished = True
        self._cancel_btn.setVisible(False)
        if success:
            self._bar.setRange(0, 100)
            self._bar.setValue(100)
            self._status_label.setText(message or "Completado.")
            self._close_btn.setVisible(True)
            self.accept()
        else:
            self._bar.setRange(0, 100)
            self._status_label.setText(
                f"<span style='color:#c62828;'><b>Error:</b> {message or 'La tarea falló.'}</span>"
            )
            self._close_btn.setVisible(True)

    def _on_cancel_clicked(self):
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("Cancelando…")
        self._status_label.setText("Cancelando, esperando al trabajador…")
        self.canceled.emit()

    def closeEvent(self, event):
        if not self._finished and self._cancelable and self._cancel_btn.isEnabled():
            self.canceled.emit()
        super().closeEvent(event)