# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Diálogos y widgets autocontenidos de la ventana principal:
RealtimePerformanceGraph (gráfico de CPU/RAM en vivo), NetworkDeviceDialog
(alta de un dispositivo de red) y DiskCreationDialog (alta de un disco/CD).
Cada uno se usa y se descarta; no guardan estado entre aperturas.
"""
import os
import re
import json
import shutil
import shlex
import glob
import subprocess
import uuid
import time
from datetime import date, timedelta
import requests
from packaging import version
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox,
    QFileDialog, QCheckBox, QDialog, QFormLayout, QSpinBox,
    QRadioButton, QButtonGroup, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QPixmap

from network_utils import list_host_bridges


class RealtimePerformanceGraph(QWidget):
    """Gráfica ligera tipo Administrador de tareas, sin dependencias externas."""
    def __init__(self, title, unit="%", max_value=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_value = float(max_value) if max_value else 100.0
        self.values = []
        self.setMinimumHeight(105)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_values(self, values):
        self.values = list(values)[-60:]
        self.update()

    def add_value(self, value):
        try:
            v = max(0.0, min(float(value), self.max_value))
        except Exception:
            v = 0.0
        self.values.append(v)
        self.values = self.values[-60:]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(8, 6, -8, -8)
        p.setPen(QPen(self.palette().mid().color(), 1))
        p.setBrush(QBrush(self.palette().base().color()))
        p.drawRoundedRect(rect, 5, 5)
        p.setPen(QPen(self.palette().text().color(), 1))
        p.drawText(rect.adjusted(10, 5, -10, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                   f"{self.title}   {self.values[-1]:.1f} {self.unit}" if self.values else self.title)

        chart = rect.adjusted(10, 25, -10, -18)
        # rejilla tipo Task Manager
        grid_pen = QPen(self.palette().mid().color(), 1)
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        p.setPen(grid_pen)
        for i in range(1, 5):
            y = chart.top() + i * chart.height() / 5.0
            p.drawLine(int(chart.left()), int(y), int(chart.right()), int(y))
        for i in range(1, 10):
            x = chart.left() + i * chart.width() / 10.0
            p.drawLine(int(x), int(chart.top()), int(x), int(chart.bottom()))

        if not self.values:
            p.setPen(QPen(self.palette().mid().color(), 1))
            p.drawText(chart, Qt.AlignmentFlag.AlignCenter, "Esperando datos…")
            return

        pen = QPen(self.palette().highlight().color(), 2)
        p.setPen(pen)
        pts = []
        n = max(1, len(self.values) - 1)
        for i, value in enumerate(self.values):
            x = chart.left() + chart.width() * i / n
            y = chart.bottom() - chart.height() * (value / self.max_value)
            pts.append((int(x), int(y)))
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a[0], a[1], b[0], b[1])


class NetworkDeviceDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Adaptador de red virtual")
        self.setModal(True); self.resize(520, 300)
        data=data or {}
        form=QFormLayout(self)
        self.name=QLineEdit(data.get("name", "Red 1"))
        self.model=QComboBox()
        for label,val in (("VirtIO", "virtio-net-pci"),("Intel E1000","e1000"),("Realtek RTL8139","rtl8139"),("VMware VMXNET3","vmxnet3")):
            self.model.addItem(label,val)
        i=self.model.findData(data.get("model","virtio-net-pci")); self.model.setCurrentIndex(max(0,i))
        self.mode=QComboBox()
        for label,val in (("NAT / Internet","nat"),("Bridge existente","bridge"),("TAP","tap")):
            self.mode.addItem(label,val)
        i=self.mode.findData(data.get("mode","nat")); self.mode.setCurrentIndex(max(0,i))
        self.target=QComboBox(); self.target.setEditable(True)
        self.mac=QLineEdit(data.get("mac","")); self.mac.setPlaceholderText("Opcional: 52:54:00:xx:xx:xx")
        # Reglas de reenvío de puertos NAT (solo aplican al backend NAT).
        # El usuario las edita desde el botón "🔀 Reglas NAT…" que aparece
        # cuando el modo es NAT. Se persisten en network_devices[i]["hostfwd"].
        self._hostfwd = [dict(r) for r in (data.get("hostfwd") or []) if isinstance(r, dict)]
        self.mode.currentIndexChanged.connect(self.update_target)
        form.addRow("Nombre:", self.name); form.addRow("Modelo:", self.model); form.addRow("Backend:", self.mode); form.addRow("Bridge / TAP:", self.target); form.addRow("MAC:", self.mac)
        self.btn_nat_rules = QPushButton("🔀 Reglas NAT…")
        self.btn_nat_rules.setToolTip(
            "Redirigir puertos del host al guest a través del NAT de QEMU\n"
            "(hostfwd). Solo aplica cuando el backend es NAT."
        )
        self.btn_nat_rules.clicked.connect(self._open_nat_rules)
        form.addRow("", self.btn_nat_rules)
        buttons=QHBoxLayout(); buttons.addStretch(); ok=QPushButton("Aceptar"); cancel=QPushButton("Cancelar"); ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); buttons.addWidget(cancel); buttons.addWidget(ok); form.addRow(buttons)
        self._load_targets(data.get("interface","")); self.update_target()
    def _load_targets(self, preferred=""):
        self.target.blockSignals(True); self.target.clear()
        for name,_ in list_host_bridges(): self.target.addItem(name,name)
        if preferred and self.target.findData(preferred)<0: self.target.addItem(preferred,preferred)
        if preferred and self.target.findData(preferred)>=0: self.target.setCurrentIndex(self.target.findData(preferred))
        self.target.blockSignals(False)
    def update_target(self,*_):
        mode=self.mode.currentData(); self.target.setEnabled(mode!="nat")
        if mode=="tap" and not self.target.currentText(): self.target.setEditText("qvm-net")
        if mode=="nat": self.target.setEditText("")
        # El botón "Reglas NAT…" solo tiene sentido con backend NAT.
        btn = getattr(self, "btn_nat_rules", None)
        if btn is not None:
            is_nat = (mode == "nat")
            btn.setVisible(is_nat)
            n = len(getattr(self, "_hostfwd", []) or [])
            btn.setText(f"🔀 Reglas NAT… ({n})" if n else "🔀 Reglas NAT…")

    def _open_nat_rules(self):
        """Abre el sub-diálogo de reenvío de puertos NAT."""
        dlg = NatPortForwardDialog(self, getattr(self, "_hostfwd", []))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._hostfwd = dlg.values()
            self.update_target()
    def values(self):
        return {
            "name": self.name.text().strip() or "Red",
            "model": self.model.currentData(),
            "mode": self.mode.currentData(),
            "interface": self.target.currentData() or self.target.currentText().strip(),
            "mac": self.mac.text().strip(),
            "hostfwd": list(getattr(self, "_hostfwd", []) or []),
        }

class DiskCreationDialog(QDialog):
    """Dialogo único para crear/adjuntar almacenamiento o configurar CD/DVD."""
    def __init__(self, parent=None, devtype="sata", os_type="linux", os_version="", distro="", win_ver="Windows 11", initial_path="", initial_name=""):
        super().__init__(parent)
        self.devtype = devtype
        self.os_type = os_type
        self.os_version = os_version
        self.distro = distro
        self.win_ver = win_ver
        self.initial_path = initial_path
        self.initial_name = initial_name
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.setModal(True)
        self.setMinimumWidth(640)
        self.resize(700, 430)

        layout = QVBoxLayout(self)
        title_map = {
            "sata": "💽 Disco SATA", "nvme": "⚡ Disco NVMe",
            "floppy": "💾 Disquetera", "cdrom": "📀 Unidad CD / DVD",
        }
        title = QLabel(title_map.get(devtype, "Dispositivo de almacenamiento"))
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        self.input_name = None
        self.input_size = None
        self.combo_type = None
        self.combo_format = None
        self.input_path = None
        self.btn_browse = None
        self.source_radio = None
        self.existing_radio = None

        if devtype == "cdrom":
            self._build_cdrom(layout)
        else:
            self._build_disk(layout)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancelar")
        accept = QPushButton("Aceptar")
        accept.setDefault(True)
        cancel.clicked.connect(self.reject)
        accept.clicked.connect(self._validate_and_accept)
        buttons.addWidget(cancel)
        buttons.addWidget(accept)
        layout.addLayout(buttons)

    def _build_cdrom(self, layout):
        form = QFormLayout()
        self.cd_mode = QComboBox()
        self.cd_mode.addItem("Mantener vacío", "empty")
        self.cd_mode.addItem("Usar ISO/IMG/DMG existente", "existing")
        if self.os_type == "macos":
            self.cd_mode.addItem("System Recovery de macOS (descargar al iniciar)", "recovery")
        elif self.os_type == "android":
            # Android-x86 / Bliss OS se instalan siempre desde una ISO
            # que aporta el usuario. No hay descarga automática porque
            # los mirrors cambian de ubicación con frecuencia y no hay
            # una URL estable equivalente a la de Microsoft o los
            # espejos de las distros Linux. Se ofrecen solo las dos
            # opciones generales: unidad vacía o ISO existente.
            pass
        else:
            # Windows/Linux recuperan la opción de las versiones anteriores:
            # descargar automáticamente el instalador y dejarlo conectado al CD/DVD.
            if self.os_type == "windows":
                installer_label = "Descargar instalador de Windows automáticamente"
            else:
                installer_label = "Descargar instalador de Linux automáticamente"
            self.cd_mode.addItem(installer_label, "installer")
        self.cd_mode.currentIndexChanged.connect(self._update_cd_mode)
        form.addRow("Fuente del medio:", self.cd_mode)

        self.input_name = QLineEdit(self.initial_name or "CD/DVD")
        form.addRow("Nombre:", self.input_name)
        self.input_path = QLineEdit(self.initial_path or "")
        self.input_path.setPlaceholderText("Selecciona una ISO / IMG / DMG…")
        self.btn_browse = QPushButton("📁 Buscar…")
        self.btn_browse.clicked.connect(self._browse_medium)
        path_widget = QWidget()
        row = QHBoxLayout(path_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.input_path, 1)
        row.addWidget(self.btn_browse)
        form.addRow("Medio:", path_widget)
        layout.addLayout(form)

        self.cd_hint = QLabel()
        self.cd_hint.setWordWrap(True)
        self.cd_hint.setStyleSheet("color:#666;")
        layout.addWidget(self.cd_hint)
        self._update_cd_mode()

    def _build_disk(self, layout):
        form = QFormLayout()
        if self.devtype == "floppy":
            self.input_name = QLineEdit("floppy")
        else:
            default = "datos" if self.devtype == "sata" else "nvme_datos"
            self.input_name = QLineEdit(default)
        form.addRow("Nombre:", self.input_name)

        if self.devtype in ("sata", "nvme"):
            mode_row = QHBoxLayout()
            self.source_radio = QRadioButton("Crear nuevo")
            self.existing_radio = QRadioButton("Usar disco existente")
            self.source_radio.setChecked(True)
            group = QButtonGroup(self)
            group.addButton(self.source_radio)
            group.addButton(self.existing_radio)
            mode_row.addWidget(self.source_radio)
            mode_row.addWidget(self.existing_radio)
            mode_row.addStretch()
            form.addRow("Origen:", mode_row)
            self.source_radio.toggled.connect(self._update_disk_mode)

        if self.devtype == "floppy":
            self.input_size = QComboBox()
            for label, val in (("720 KB", "720K"), ("1.44 MB", "1.44M"), ("2.88 MB", "2.88M")):
                self.input_size.addItem(label, val)
            self.input_size.setCurrentIndex(1)
            form.addRow("Tamaño:", self.input_size)
            self.combo_format = QComboBox()
            self.combo_format.addItem("RAW", "raw")
            form.addRow("Formato:", self.combo_format)
        else:
            self.input_size = QLineEdit("40G")
            self.input_size.setPlaceholderText("Ej.: 40G, 100G, 1T")
            form.addRow("Tamaño:", self.input_size)
            self.combo_type = QComboBox()
            self.combo_type.addItem("Expandible (dinámico)", "dynamic")
            self.combo_type.addItem("Fijo (preasignado)", "fixed")
            form.addRow("Tipo:", self.combo_type)
            self.combo_format = QComboBox()
            for label, value in (("QCOW2", "qcow2"), ("RAW", "raw"), ("VDI", "vdi"), ("VMDK", "vmdk")):
                self.combo_format.addItem(label, value)
            form.addRow("Formato:", self.combo_format)

            self.input_path = QLineEdit()
            self.input_path.setPlaceholderText("Ruta del disco existente…")
            self.btn_browse = QPushButton("📁 Buscar…")
            self.btn_browse.clicked.connect(self._browse_existing)
            self.path_widget = QWidget()
            row = QHBoxLayout(self.path_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(self.input_path, 1)
            row.addWidget(self.btn_browse)
            form.addRow("Archivo:", self.path_widget)

        layout.addLayout(form)
        hint_text = (
            "Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB."
            if self.devtype == "floppy" else
            "Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. También puedes adjuntar un disco existente."
        )
        hint = QLabel(hint_text)
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666;")
        layout.addWidget(hint)
        if self.devtype in ("sata", "nvme"):
            self._update_disk_mode()

    def _update_cd_mode(self):
        mode = self.cd_mode.currentData()
        use_path = mode == "existing"
        self.input_path.setEnabled(use_path)
        self.btn_browse.setEnabled(use_path)
        self.input_path.setVisible(use_path)
        self.btn_browse.setVisible(use_path)
        hints = {
            "empty": "La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.",
            "existing": "Selecciona un ISO/IMG/DMG que ya exista en tu equipo.",
            "recovery": "Para macOS se descargará System Recovery automáticamente al iniciar la VM y se asociará a esta unidad óptica.",
            "installer": (
                "El instalador se descargará automáticamente al iniciar la VM, "
                "mostrando una barra de porcentaje, y quedará conectado a esta unidad CD/DVD."
            ),
        }
        self.cd_hint.setText(hints.get(mode, ""))

    def _update_disk_mode(self, *_):
        create_mode = bool(self.source_radio.isChecked()) if self.source_radio else True
        for w in (self.input_name, self.input_size, self.combo_type, self.combo_format):
            if w is not None:
                w.setEnabled(create_mode)
        if self.input_path is not None:
            self.input_path.setEnabled(not create_mode)
        if self.btn_browse is not None:
            self.btn_browse.setEnabled(not create_mode)
        if hasattr(self, "path_widget"):
            self.path_widget.setVisible(not create_mode)

    def _browse_existing(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar disco virtual existente", "",
            "Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)"
        )
        if path:
            self.input_path.setText(path)

    def _browse_medium(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar medio óptico", "",
            "Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)"
        )
        if path:
            self.input_path.setText(path)

    def _validate_and_accept(self):
        if self.devtype == "cdrom":
            mode = self.cd_mode.currentData()
            if mode == "existing":
                path = self.input_path.text().strip()
                if not path or not os.path.isfile(path):
                    QMessageBox.warning(self, "Medio inválido", "Selecciona un ISO/IMG/DMG válido.")
                    return
            self.accept()
            return

        existing = self.devtype in ("sata", "nvme") and self.existing_radio.isChecked()
        if existing:
            path = self.input_path.text().strip()
            if not path or not os.path.isfile(path):
                QMessageBox.warning(self, "Disco inválido", "Selecciona un archivo de disco existente válido.")
                return
            self.accept()
            return

        name = self.input_name.text().strip()
        size = self.input_size.currentData() if self.devtype == "floppy" else self.input_size.text().strip()
        if not name:
            QMessageBox.warning(self, "Nombre requerido", "Indica un nombre para el dispositivo.")
            return
        if self.devtype != "floppy" and not re.fullmatch(r"(?:\d+(?:\.\d+)?)(?:[KMGTP]i?B?|B)?", size, re.IGNORECASE):
            QMessageBox.warning(self, "Tamaño inválido", "Usa un tamaño como 40G, 512M o 1T.")
            return
        self.accept()

    def values(self):
        if self.devtype == "cdrom":
            mode = self.cd_mode.currentData()
            return {
                "name": self.input_name.text().strip() or "CD/DVD",
                "size": "",
                "type": "",
                "format": "iso",
                "path": self.input_path.text().strip() if mode == "existing" else "",
                "device": self.devtype,
                "existing": mode == "existing",
                "cd_mode": mode,
            }
        existing = self.devtype in ("sata", "nvme") and self.existing_radio.isChecked()
        return {
            "name": self.input_name.text().strip(),
            "size": self.input_size.currentData() if self.devtype == "floppy" else self.input_size.text().strip(),
            "type": "fixed" if self.devtype == "floppy" else self.combo_type.currentData(),
            "format": self.combo_format.currentData(),
            "path": self.input_path.text().strip() if existing else "",
            "device": self.devtype,
            "existing": existing,
        }


class NatPortForwardDialog(QDialog):
    """Editor de reglas de reenvío de puertos NAT (-netdev user,hostfwd=...).

    Cada regla redirige puerto_host:localhost → puerto_guest:guest a través
    del backend NAT de QEMU. Solo se permiten TCP y UDP, puertos 1-65535 y
    no se admiten dos reglas con el mismo (protocolo, puerto host).
    """

    def __init__(self, parent=None, rules=None):
        super().__init__(parent)
        self.setWindowTitle("Reglas de reenvío de puertos NAT")
        self.setModal(True)
        self.resize(580, 400)

        self._rules = [dict(r) for r in (rules or []) if isinstance(r, dict)]

        layout = QVBoxLayout(self)

        info = QLabel(
            "Redirige puertos del host al guest a través del NAT de QEMU "
            "(<code>-netdev user,hostfwd=...</code>). Cada regla conecta "
            "<b>localhost:puerto_host</b> del anfitrión con "
            "<b>puerto_guest</b> dentro del sistema invitado.<br><br>"
            "Ejemplo: host 2222 → guest 22 reenvía SSH; luego entra con "
            "<code>ssh -p 2222 usuario@localhost</code>."
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        # --- Fila de alta ---
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Puerto host:"))
        self.sp_host = QSpinBox()
        self.sp_host.setRange(1, 65535)
        self.sp_host.setValue(2222)
        self.sp_host.setToolTip("Puerto en el host (donde tú te conectas).")
        add_row.addWidget(self.sp_host)
        add_row.addSpacing(10)
        add_row.addWidget(QLabel("Puerto guest:"))
        self.sp_guest = QSpinBox()
        self.sp_guest.setRange(1, 65535)
        self.sp_guest.setValue(22)
        self.sp_guest.setToolTip("Puerto dentro de la VM (a donde se reenvía).")
        add_row.addWidget(self.sp_guest)
        add_row.addSpacing(10)
        add_row.addWidget(QLabel("Protocolo:"))
        self.cmb_proto = QComboBox()
        self.cmb_proto.addItem("TCP", "tcp")
        self.cmb_proto.addItem("UDP", "udp")
        add_row.addWidget(self.cmb_proto)
        add_row.addStretch()
        self.btn_add = QPushButton("➕ Añadir regla")
        self.btn_add.clicked.connect(self._add_rule)
        add_row.addWidget(self.btn_add)
        layout.addLayout(add_row)

        # --- Tabla ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Puerto host", "Puerto guest", "Protocolo"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # --- Botones inferiores ---
        bottom = QHBoxLayout()
        self.btn_remove = QPushButton("🗑 Quitar seleccionada")
        self.btn_remove.clicked.connect(self._remove_selected)
        bottom.addWidget(self.btn_remove)
        bottom.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_cancel)
        btn_ok = QPushButton("Aceptar")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        bottom.addWidget(btn_ok)
        layout.addLayout(bottom)

        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        for r in self._rules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0,
                               QTableWidgetItem(str(r.get("host_port", ""))))
            self.table.setItem(row, 1,
                               QTableWidgetItem(str(r.get("guest_port", ""))))
            self.table.setItem(row, 2,
                               QTableWidgetItem(
                                   str(r.get("protocol", "tcp")).upper()))

    def _add_rule(self):
        hp = int(self.sp_host.value())
        gp = int(self.sp_guest.value())
        proto = self.cmb_proto.currentData() or "tcp"

        # Mismo (protocolo, puerto_host) → duplicado exacto, no permitir.
        for r in self._rules:
            if (int(r.get("host_port", 0)) == hp
                    and str(r.get("protocol", "tcp")).lower() == proto):
                QMessageBox.warning(
                    self, "Regla duplicada",
                    f"Ya existe una regla para el puerto host {hp} "
                    f"({proto.upper()}).\n\nElige otro puerto host o "
                    "cambia el protocolo.",
                )
                return

        self._rules.append(
            {"host_port": hp, "guest_port": gp, "protocol": proto}
        )
        self._refresh_table()

    def _remove_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._rules):
            return
        del self._rules[row]
        self._refresh_table()

    def values(self):
        return [dict(r) for r in self._rules]

