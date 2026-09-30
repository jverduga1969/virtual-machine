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
    QTreeWidget, QTreeWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QPixmap, QColor

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
            #
            # linux_installer_guard_v1: la opcion "installer" solo tiene
            # sentido si la app sabe resolver la URL de la distro. Si no
            # (MX Linux, Solus, etc.), se anade DESHABILITADA con un texto
            # explicativo, para que el usuario vea que existe pero entienda
            # por que no puede usarla.
            # linux_installer_guard_v2_dialogs: la opción "installer"
            # SOLO se añade si la app sabe resolver la URL de la
            # distro. Si no (MX Linux, Solus, etc.), no se añade — es
            # más limpio que mostrarla gris: el usuario no ve una
            # opción que nunca podrá usar.
            if self.os_type == "windows":
                installer_label = "Descargar instalador de Windows automáticamente"
                self.cd_mode.addItem(installer_label, "installer")
            else:
                _installer_label = "Descargar instalador de Linux automáticamente"
                _installer_ok = False
                try:
                    import iso_versions as _iv
                    _distro_name = (self.distro or "").strip()
                    if _distro_name:
                        _installer_ok = bool(
                            _iv.supports_auto_download(_distro_name)
                        )
                    else:
                        # Sin distro conocida, permitir la opción
                        # (el flujo Linux de la ventana principal
                        # siempre pasa un distro concreto).
                        _installer_ok = True
                except Exception:
                    _installer_ok = True
                if _installer_ok:
                    self.cd_mode.addItem(_installer_label, "installer")
                else:
                    # Registrar el motivo en el widget para que
                    # _update_cd_mode pueda mostrarlo si el usuario
                    # abre el diálogo con initial_path de una ISO
                    # ya descargada (raro, pero por si acaso).
                    self._installer_unsupported_reason = (
                        f"{_distro_name} no tiene descarga "
                        "automática desde los espejos oficiales."
                    )
        self.cd_mode.currentIndexChanged.connect(self._update_cd_mode)
        form.addRow("Fuente del medio:", self.cd_mode)

        self.input_name = QLineEdit(self.initial_name or "CD/DVD")
        form.addRow("Nombre:", self.input_name)
        self.input_path = QLineEdit(self.initial_path or "")
        self.input_path.setPlaceholderText("Selecciona una ISO / IMG / DMG…")
        self.btn_browse = QPushButton("📁 Buscar…")
        self.btn_browse.clicked.connect(self._browse_medium)
        # media_library_picker_v1: boton para elegir de la biblioteca.
        self.btn_library = QPushButton("📚 Biblioteca…")
        self.btn_library.setToolTip(
            "Elegir un medio de la biblioteca central (MediaLibrary/).\n"
            "Se reutiliza entre todas las VMs."
        )
        self.btn_library.clicked.connect(self._pick_from_library)
        path_widget = QWidget()
        row = QHBoxLayout(path_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.input_path, 1)
        row.addWidget(self.btn_browse)
        row.addWidget(self.btn_library)
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

        # media_library_device_picker_v1_B: selector crear/existente
        # disponible tambien para floppy.
        mode_row = QHBoxLayout()
        self.source_radio = QRadioButton("Crear nuevo")
        self.existing_radio = QRadioButton("Usar archivo existente")
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


        # media_library_device_picker_v1_B: campo Archivo + botones
        # compartidos por los 3 tipos.
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Ruta del archivo existente…")
        self.btn_browse = QPushButton("📁 Buscar…")
        self.btn_browse.clicked.connect(self._browse_existing)
        self.btn_library_disk = QPushButton("📚 Biblioteca…")
        self.btn_library_disk.setToolTip(
            "Elegir un archivo ya registrado en la Biblioteca de Medios.\n"
            "Se filtra por el tipo del dispositivo."
        )
        self.btn_library_disk.clicked.connect(self._pick_from_library)
        self.path_widget = QWidget()
        row = QHBoxLayout(self.path_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.input_path, 1)
        row.addWidget(self.btn_browse)
        row.addWidget(self.btn_library_disk)
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
        # El boton de biblioteca esta siempre disponible: si el usuario
        # lo pulsa desde "vacio" o "descargar instalador", pasamos el
        # modo a "existing" (la eleccion de biblioteca implica archivo).
        if getattr(self, "btn_library", None) is not None:
            self.btn_library.setEnabled(True)
            self.btn_library.setVisible(True)
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
        if getattr(self, "btn_library_disk", None) is not None:
            self.btn_library_disk.setEnabled(not create_mode)
        if hasattr(self, "path_widget"):
            self.path_widget.setVisible(not create_mode)

    def _browse_existing(self):
        if self.devtype == "floppy":
            filter_str = ("Imágenes de disquete (*.img *.raw)"
                          ";;Todos los archivos (*)")
        else:
            filter_str = ("Discos virtuales "
                          "(*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx)"
                          ";;Todos los archivos (*)")
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo existente", "", filter_str
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

    def _pick_from_library(self):
        """Abre el selector de la biblioteca y rellena el campo de medio.

        Marcador: media_library_picker_v1.
        """
        # media_library_device_picker_v1: filtro por tipo de dispositivo.
        if self.devtype == "floppy":
            media_type = "floppy"
        elif self.devtype == "cdrom":
            media_type = "iso"
        else:
            media_type = "disk"
        dlg = MediaPickerDialog(
            self,
            filter_os_type=self.os_type,
            filter_media_type=media_type,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        chosen = dlg.chosen()
        if not chosen or not chosen.get("path"):
            return
        if self.devtype == "cdrom":
            if self.cd_mode.currentData() != "existing":
                idx = self.cd_mode.findData("existing")
                if idx >= 0:
                    self.cd_mode.blockSignals(True)
                    self.cd_mode.setCurrentIndex(idx)
                    self.cd_mode.blockSignals(False)
            self.input_path.setText(chosen["path"])
            self._update_cd_mode()
        else:
            if (getattr(self, "existing_radio", None) is not None
                    and not self.existing_radio.isChecked()):
                self.existing_radio.setChecked(True)
            self.input_path.setText(chosen["path"])
            self._update_disk_mode()

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

        existing = bool(getattr(self, "existing_radio", None)
                        and self.existing_radio.isChecked())
        if existing:
            path = self.input_path.text().strip()
            if not path or not os.path.isfile(path):
                QMessageBox.warning(self, "Archivo inválido",
                                    "Selecciona un archivo existente válido.")
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
        existing = bool(getattr(self, "existing_radio", None)
                        and self.existing_radio.isChecked())
        return {
            "name": self.input_name.text().strip(),
            "size": self.input_size.currentData() if self.devtype == "floppy" else self.input_size.text().strip(),
            "type": "fixed" if self.devtype == "floppy" else self.combo_type.currentData(),
            "format": self.combo_format.currentData(),
            "path": self.input_path.text().strip() if existing else "",
            "device": self.devtype,
            "existing": existing,
        }


# media_library_picker_sort_v1: item con orden numerico real en la
# columna "Tamano" (indice 4) del arbol del selector de medios.
class _PickerTreeItem(QTreeWidgetItem):
    _NUMERIC_COL = 5  # media_library_picker_filter_type_v1

    def __lt__(self, other):
        tree = self.treeWidget()
        if tree is None:
            return super().__lt__(other)
        col = tree.sortColumn()
        if col == self._NUMERIC_COL:
            try:
                a = self.data(self._NUMERIC_COL,
                              Qt.ItemDataRole.UserRole)
                b = other.data(self._NUMERIC_COL,
                               Qt.ItemDataRole.UserRole)
                return int(a or 0) < int(b or 0)
            except Exception:
                pass
        try:
            return self.text(col) < other.text(col)
        except Exception:
            return super().__lt__(other)


# media_library_create_v1: sub-dialogo para crear un disco nuevo
# (QCOW2/RAW) o un disquete (IMG) directamente en MediaLibrary/.
class _CreateMediumDialog(QDialog):
    """Pequeno dialogo para crear un medio con qemu-img create."""

    def __init__(self, parent=None, default_type="qcow2"):
        super().__init__(parent)
        self.setWindowTitle("Crear medio nuevo")
        self.setModal(True)
        self.resize(520, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_name = QLineEdit("nuevo_medio")
        self.input_name.setPlaceholderText("Ej: disco_ubuntu_datos")
        form.addRow("Nombre:", self.input_name)

        self.combo_type = QComboBox()
        self.combo_type.addItem("Disco duro QCOW2 (recomendado)", "qcow2")
        self.combo_type.addItem("Disco duro RAW", "raw")
        self.combo_type.addItem("Disquete IMG (RAW)", "img")
        idx = self.combo_type.findData(default_type)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Tipo:", self.combo_type)

        self.combo_size = QComboBox()
        self.combo_size.setEditable(True)
        self.combo_size.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        form.addRow("Tamaño:", self.combo_size)

        layout.addLayout(form)

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.hint)
        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Crear")
        ok.setDefault(True)
        ok.clicked.connect(self._validate_and_accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

        self._on_type_changed()

    def _on_type_changed(self, *_):
        t = self.combo_type.currentData() or "qcow2"
        self.combo_size.blockSignals(True)
        self.combo_size.clear()
        if t == "img":
            for s in ("720K", "1.44M", "2.88M"):
                self.combo_size.addItem(s, s)
            self.combo_size.setCurrentIndex(1)  # 1.44M
            self.hint.setText(
                "Disquete formateado como RAW. Se registra como tipo "
                "'Disquete' en la biblioteca. Tamaños típicos: 720 KB, "
                "1.44 MB, 2.88 MB."
            )
        else:
            for s in ("10G", "20G", "40G", "80G", "128G", "256G",
                      "512G", "1T"):
                self.combo_size.addItem(s, s)
            self.combo_size.setCurrentIndex(2)  # 40G
            if t == "qcow2":
                self.hint.setText(
                    "Disco virtual expandible (recomendado). El archivo "
                    "en el host crece solo según se usa en el guest."
                )
            else:
                self.hint.setText(
                    "Disco RAW (imagen plana). Ocupa el tamaño completo "
                    "en el host desde el momento de su creación."
                )
        self.combo_size.blockSignals(False)

    def _validate_and_accept(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Nombre requerido",
                                "Escribe un nombre para el medio.")
            return
        if re.search(r'[\\/:*?"<>|]', name):
            QMessageBox.warning(
                self, "Nombre inválido",
                "El nombre no puede contener \\ / : * ? \" < > |"
            )
            return
        size = (self.combo_size.currentData()
                or self.combo_size.currentText().strip())
        if not size or not re.fullmatch(
                r"(?:\d+(?:\.\d+)?)(?:[KMGTP]i?B?|B)?",
                size, re.IGNORECASE):
            QMessageBox.warning(
                self, "Tamaño inválido",
                "Usa un tamaño como 40G, 512M o 1T."
            )
            return
        self.accept()

    def values(self):
        t = self.combo_type.currentData() or "qcow2"
        ext = {"qcow2": ".qcow2", "raw": ".raw", "img": ".img"}.get(t, ".qcow2")
        fmt = "qcow2" if t == "qcow2" else "raw"
        return {
            "name": self.input_name.text().strip(),
            "type": t,
            "extension": ext,
            "format": fmt,
            "kind": ("img" if t == "img" else t),
            "size": (self.combo_size.currentData()
                     or self.combo_size.currentText().strip()),
        }


class MediaPickerDialog(QDialog):
    """Selector de un medio de la biblioteca central.

    Marcador: media_library_picker_v1.

    Muestra una tabla compacta de las entradas de la biblioteca
    (opcionalmente filtradas por SO) y permite elegir una. La entrada
    elegida se devuelve con chosen() como dict {"id": ..., "path": ...}
    donde path es la ruta absoluta del archivo.

    Si el archivo de la entrada ya no existe en disco, se marca como
    "(huerfano)" y no se puede elegir.
    """

    def __init__(self, parent=None, filter_os_type="", filter_media_type=""):
        super().__init__(parent)
        self.setWindowTitle("Elegir medio de la biblioteca")
        self.setModal(True)
        self.resize(820, 500)

        self._lib = None
        self._chosen = None
        self._filter_os_type = (filter_os_type or "").lower()
        # media_library_picker_filter_type_v1: 'disk' / 'iso' / 'floppy' / ''.
        self._filter_media_type = (filter_media_type or "").lower()

        layout = QVBoxLayout(self)

        info = QLabel(
            "Elige una ISO/IMG/DMG de la biblioteca central.<br>"
            "La biblioteca vive en <code>MediaLibrary/</code>, al mismo "
            "nivel que <code>VirtualMachines/</code>. Se reutiliza entre "
            "todas las VMs."
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        filt = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar...")
        self.search.textChanged.connect(self._refresh)
        filt.addWidget(self.search, 1)
        filt.addWidget(QLabel("SO:"))
        self.cmb_os = QComboBox()
        self.cmb_os.addItem("Todos", "")
        self.cmb_os.addItem("Linux", "linux")
        self.cmb_os.addItem("Windows", "windows")
        self.cmb_os.addItem("macOS", "macos")
        self.cmb_os.addItem("Android", "android")
        self.cmb_os.addItem("Guest Tools", "guest-tools")
        idx = self.cmb_os.findData(self._filter_os_type)
        if idx >= 0:
            self.cmb_os.setCurrentIndex(idx)
        self.cmb_os.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self.cmb_os)

        # media_library_picker_filter_type_v1: filtro por tipo de medio.
        filt.addWidget(QLabel("Tipo:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItem("Todos", "")
        self.cmb_type.addItem("Disco duro", "disk")
        self.cmb_type.addItem("ISO", "iso")
        self.cmb_type.addItem("Disquete", "floppy")
        idx_t = self.cmb_type.findData(self._filter_media_type)
        if idx_t >= 0:
            self.cmb_type.setCurrentIndex(idx_t)
        self.cmb_type.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self.cmb_type)
        layout.addLayout(filt)

        self.table = QTreeWidget()
        # media_library_picker_sort_v1: orden por cabecera (con orden
        # numerico real en "Tamano").
        self.table.setHeaderLabels(
            ["Nombre", "Tipo", "SO", "Version", "Arq.", "Tamano",
             "Usada por", "Ruta"]
        )
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(4, 65)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 140)
        self.table.setColumnWidth(7, 160)
        self.table.setSortingEnabled(True)
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(
            QTreeWidget.SelectionMode.SingleSelection
        )
        self.table.itemDoubleClicked.connect(
            lambda *_: self._accept_selected()
        )
        self.table.itemSelectionChanged.connect(
            self._on_selection_changed
        )
        layout.addWidget(self.table, 1)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Anadir archivo a la biblioteca...")
        self.btn_add.setToolTip(
            "Registrar una ISO nueva sin salir de este dialogo."
        )
        self.btn_add.clicked.connect(self._add_new_file)
        btns.addWidget(self.btn_add)

        # media_library_create_v1: crear un disco nuevo en la biblioteca
        # sin salir del selector.
        self.btn_create = QPushButton("Crear disco...")
        self.btn_create.setToolTip(
            "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
            "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
            "sobre MediaLibrary/<nombre>.<ext>."
        )
        self.btn_create.clicked.connect(self._create_new_medium)
        btns.addWidget(self.btn_create)

        self.btn_open_folder = QPushButton("Abrir carpeta")
        self.btn_open_folder.setToolTip(
            "Abre MediaLibrary/ en el explorador del sistema."
        )
        self.btn_open_folder.clicked.connect(self._open_library_folder)
        btns.addWidget(self.btn_open_folder)

        btns.addStretch(1)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        self.btn_ok = QPushButton("Elegir")
        self.btn_ok.setDefault(True)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self._accept_selected)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self._load_library()
        self._refresh()

    def _load_library(self):
        try:
            import media_library as _ml
            self._lib = _ml.MediaLibrary()
        except Exception:
            self._lib = None

    def _entry_abs_path(self, entry):
        if self._lib is None:
            return ""
        return self._lib.resolve_path(entry)

    def _refresh(self, *_):
        if self.table is None:
            return
        _sort_was = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.clear()
        if self._lib is None:
            return

        query = (self.search.text() or "").strip()
        os_filter = self.cmb_os.currentData() or ""

        try:
            entries = self._lib.list_all()
            if query:
                q = query.lower()
                entries = [e for e in entries if q in " ".join([
                    str(e.get("name") or ""),
                    str(e.get("distro") or ""),
                    str(e.get("filename") or ""),
                    str(e.get("version") or ""),
                    " ".join(e.get("tags") or []),
                ]).lower()]
            if os_filter:
                entries = [e for e in entries
                           if str(e.get("os_type") or "").lower() == os_filter]
            type_filter = ""
            try:
                type_filter = self.cmb_type.currentData() or ""
            except Exception:
                type_filter = ""
            if type_filter:
                try:
                    import media_library as _ml
                    entries = [e for e in entries
                               if _ml.media_type_key(e) == type_filter]
                except Exception:
                    pass
        except Exception:
            entries = []

        for e in entries:
            eid = str(e.get("id") or "")
            name = str(e.get("name") or e.get("filename") or "?")
            os_txt = str(e.get("os_type") or "").capitalize()
            ver = str(e.get("version") or "")
            arch = str(e.get("arch") or "")
            size_txt = ""
            try:
                import media_library as _ml
                size_txt = _ml._human_bytes(e.get("size") or 0)
            except Exception:
                pass
            path_abs = self._entry_abs_path(e)
            exists = bool(path_abs and os.path.isfile(path_abs))
            if not exists:
                name = name + "   (huerfano)"
            # media_library_picker_columns_v1: "Usada por" y "Ruta".
            used_by = list(e.get("used_by") or [])
            if not used_by:
                used_by_txt = "\u2014"
            elif len(used_by) <= 3:
                used_by_txt = ", ".join(used_by)
            else:
                used_by_txt = (f"{used_by[0]}, {used_by[1]} "
                               f"(+{len(used_by) - 2})")
            stored_path = str(e.get("path") or "")
            if os.path.isabs(stored_path) and len(stored_path) > 40:
                path_txt = "\u2026" + stored_path[-37:]
            else:
                path_txt = stored_path or "(sin archivo)"
            try:
                import media_library as _ml
                tipo_txt = _ml.media_type_label(e)
            except Exception:
                tipo_txt = ""
            row = _PickerTreeItem([
                name, tipo_txt, os_txt, ver, arch, size_txt,
                used_by_txt, path_txt,
            ])
            row.setData(0, Qt.ItemDataRole.UserRole, eid)
            try:
                row.setData(5, Qt.ItemDataRole.UserRole,
                            int(e.get("size") or 0))
            except Exception:
                row.setData(5, Qt.ItemDataRole.UserRole, 0)
            row.setToolTip(0, path_abs or "(sin archivo)")
            row.setToolTip(6, ("\n".join(used_by) if used_by
                               else "No la usa ninguna VM."))
            row.setToolTip(7, stored_path or "(sin archivo)")
            if not exists:
                try:
                    from PyQt6.QtGui import QColor as _QC
                    row.setForeground(0, QBrush(_QC("#b71c1c")))
                except Exception:
                    pass
            self.table.addTopLevelItem(row)

        # media_library_picker_sort_v1: reactivar sorting y reordenar.
        self.table.setSortingEnabled(bool(_sort_was))
        try:
            hdr = self.table.header()
            if hdr is not None and hdr.sortIndicatorSection() >= 0:
                self.table.sortByColumn(
                    hdr.sortIndicatorSection(),
                    hdr.sortIndicatorOrder(),
                )
        except Exception:
            pass

    def _selected_entry(self):
        it = self.table.currentItem()
        if it is None:
            return None
        eid = it.data(0, Qt.ItemDataRole.UserRole)
        if not eid:
            return None
        return self._lib.get(eid) if self._lib else None

    def _on_selection_changed(self):
        e = self._selected_entry()
        ok = False
        if e is not None:
            path_abs = self._entry_abs_path(e)
            ok = bool(path_abs and os.path.isfile(path_abs))
        self.btn_ok.setEnabled(ok)

    def _accept_selected(self):
        e = self._selected_entry()
        if e is None:
            return
        path_abs = self._entry_abs_path(e)
        if not path_abs or not os.path.isfile(path_abs):
            QMessageBox.warning(
                self, "Archivo no disponible",
                "El archivo de esta entrada ya no existe en el disco.\n\n"
                f"Ruta esperada:\n{path_abs}"
            )
            return
        self._chosen = {"id": str(e.get("id") or ""), "path": path_abs}
        try:
            self._lib.mark_used(e.get("id"))
        except Exception:
            pass
        self.accept()

    def _create_new_medium(self):
        """Crea un disco/disquete nuevo con qemu-img y lo registra.

        Marcador: media_library_create_v1.
        """
        if self._lib is None:
            QMessageBox.warning(
                self, "Biblioteca no disponible",
                "La biblioteca de medios no está disponible."
            )
            return

        # Preseleccionar el tipo segun el filtro activo del picker.
        default_type = {
            "disk": "qcow2",
            "floppy": "img",
        }.get(self._filter_media_type, "qcow2")

        dlg = _CreateMediumDialog(self, default_type=default_type)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.values()

        fname = v["name"] + v["extension"]
        target = os.path.join(self._lib.base_dir, fname)

        # No sobrescribir: si existe, avisar.
        if os.path.exists(target):
            QMessageBox.warning(
                self, "Ya existe",
                f"Ya existe un archivo con ese nombre en la biblioteca:\n\n"
                f"{target}\n\n"
                "Elige otro nombre o bórralo desde la pestaña Medios."
            )
            return

        # Crear con qemu-img.
        try:
            cmd = ["qemu-img", "create", "-f", v["format"],
                   target, v["size"]]
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=120)
            if proc.returncode != 0:
                raise RuntimeError(
                    (proc.stderr or proc.stdout or "qemu-img falló").strip()
                )
        except FileNotFoundError:
            QMessageBox.critical(
                self, "Crear medio",
                "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
                "en Debian/Ubuntu, qemu-img en Arch) para crear discos."
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Crear medio",
                f"No se pudo crear el medio.\n\n{e}"
            )
            return

        # Registrar en el índice.
        entry_id = None
        try:
            entry = self._lib.add(target)
            if isinstance(entry, dict) and entry.get("id"):
                entry_id = entry["id"]
                # Preservar el kind elegido por el usuario (auto_detect
                # puede haber decidido otro segun el nombre).
                self._lib.update(
                    entry_id,
                    kind=v["kind"],
                    notes=(f"Creado con qemu-img create. "
                           f"Tamaño: {v['size']}."),
                )
                self._lib.mark_used(entry_id)
        except Exception as e:
            QMessageBox.warning(
                self, "Crear medio",
                "El archivo se creó correctamente pero no se pudo\n"
                f"registrar en la biblioteca:\n\n{e}"
            )

        # Refrescar y seleccionar la entrada nueva.
        self._refresh()
        if entry_id:
            for i in range(self.table.topLevelItemCount()):
                it = self.table.topLevelItem(i)
                if it.data(0, Qt.ItemDataRole.UserRole) == entry_id:
                    self.table.setCurrentItem(it)
                    break

        QMessageBox.information(
            self, "Medio creado",
            f"Se creó el medio correctamente.\n\n"
            f"Archivo: {fname}\n"
            f"Tamaño: {v['size']}\n"
            f"Formato: {v['format'].upper()}"
        )

    def _add_new_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Anadir a la biblioteca", os.path.expanduser("~"),
            "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)"
        )
        if not paths or self._lib is None:
            return
        for p in paths:
            try:
                self._lib.add(os.path.abspath(p))
            except Exception:
                pass
        self._refresh()

    def _open_library_folder(self):
        if self._lib is None:
            return
        folder = self._lib.base_dir
        if not os.path.isdir(folder):
            return
        try:
            if shutil.which("xdg-open"):
                subprocess.Popen(
                    ["xdg-open", folder],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

    def chosen(self):
        return self._chosen


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

