# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Jimmy Verduga

"""vm_profile_widget.py — Barra superior de perfiles, candado y diálogo de Diff.

Marcador: vm_profile_widget_v1
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QToolButton, 
    QMessageBox, QDialog, QVBoxLayout, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
import vm_profiles

class ProfileDiffDialog(QDialog):
    """Diálogo modal que muestra los cambios exactos antes de aplicar un perfil."""
    def __init__(self, parent, profile_id, os_type, current_data, new_data):
        super().__init__(parent)
        self.setWindowTitle("Previsualización de Cambios del Perfil")
        self.resize(550, 400)
        
        prof_info = vm_profiles.PROFILES.get(profile_id, {})
        prof_label = prof_info.get("label", profile_id)
        prof_icon = prof_info.get("icon", "")

        layout = QVBoxLayout(self)

        title_lbl = QLabel(f"<h3>Aplicar perfil: {prof_icon} {prof_label}</h3>")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel("Se aplicarán los siguientes ajustes de hardware y rendimiento para tu sistema operativo:")
        layout.addWidget(desc_lbl)

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Parámetro", "Valor Actual", "Nuevo Valor (Perfil)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        fields = [
            ("ram", "Memoria RAM"),
            ("cores", "Núcleos CPU"),
            ("disk_gb", "Disco Principal (GB)"),
            ("graphics_mode", "Modo Gráfico"),
            ("vram", "VRAM"),
            ("nested_virt", "Virtualización Anidada"),
            ("snapshot_compatible", "Snapshots Completos"),
            ("clipboard", "Portapapeles"),
        ]

        changes = []
        for key, name in fields:
            curr_val = str(current_data.get(key, "N/A"))
            new_val = str(new_data.get(key, "N/A"))
            if curr_val != new_val:
                changes.append((name, curr_val, f"<b>{new_val}</b>"))
            else:
                changes.append((name, curr_val, new_val))

        self.table.setRowCount(len(changes))
        for row, (name, cur, nxt) in enumerate(changes):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(cur.replace("<b>","").replace("</b>","")))
            item_new = QTableWidgetItem()
            item_new.setData(Qt.ItemDataRole.DisplayRole, nxt.replace("<b>","").replace("</b>",""))
            if cur != nxt:
                item_new.setBackground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, item_new)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class VMProfileHeaderWidget(QWidget):
    """Barra superior con Selector de Perfil, Candado y Estado (Fijo / Personalizado)."""
    profileChanged = pyqtSignal(str)
    lockToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("<b>Perfil de Uso:</b>"))

        self.combo_profile = QComboBox()
        for pid in vm_profiles.all_profile_ids():
            lbl = vm_profiles.profile_label(pid)
            icon = vm_profiles.profile_icon(pid)
            self.combo_profile.addItem(f"{icon}  {lbl}", pid)
        self.combo_profile.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo_profile)

        self.status_lbl = QLabel("🔒 Perfil Fijo")
        self.status_lbl.setStyleSheet("color: green; font-weight: bold; margin-left: 10px;")
        layout.addWidget(self.status_lbl)

        self.lock_btn = QToolButton()
        self.lock_btn.setText("🔓 Desbloquear")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(False)
        self.lock_btn.clicked.connect(self._toggle_lock)
        layout.addWidget(self.lock_btn)

        layout.addStretch()

        self._is_locked = True

    def _toggle_lock(self, checked):
        self._is_locked = not checked
        if self._is_locked:
            self.lock_btn.setText("🔓 Desbloquear")
            self.status_lbl.setText("🔒 Perfil Fijo")
            self.status_lbl.setStyleSheet("color: green; font-weight: bold; margin-left: 10px;")
        else:
            self.lock_btn.setText("🔒 Bloquear")
            self.status_lbl.setText("✏️ Personalizado")
            self.status_lbl.setStyleSheet("color: orange; font-weight: bold; margin-left: 10px;")
        
        self.lockToggled.emit(self._is_locked)

    def _on_combo_changed(self, index):
        pid = self.combo_profile.currentData()
        if pid:
            self.profileChanged.emit(pid)

    def set_locked(self, locked: bool):
        self._is_locked = locked
        self.lock_btn.setChecked(not locked)
        self._toggle_lock(locked)

    def set_current_profile(self, profile_id: str):
        idx = self.combo_profile.findData(profile_id)
        if idx >= 0:
            self.combo_profile.blockSignals(True)
            self.combo_profile.setCurrentIndex(idx)
            self.combo_profile.blockSignals(False)
