# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Diálogos y widgets autocontenidos de la ventana principal:
RealtimePerformanceGraph (gráfico de CPU/RAM en vivo), NetworkDeviceDialog
(alta de un dispositivo de red) y DiskCreationDialog (alta de un disco/CD).
Cada uno se usa y se descarta; no guardan estado entre aperturas.
"""
import os
import re
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QDialog, QFormLayout, QSpinBox,
    QRadioButton, QButtonGroup, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTreeWidget, QTreeWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QBrush

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
        self.setWindowTitle(self.tr("Adaptador de red virtual"))
        self.setModal(True); self.resize(520, 300)
        data=data or {}
        form=QFormLayout(self)
        self.name=QLineEdit(data.get("name", self.tr("Red 1")))
        self.model=QComboBox()
        for label,val in (("VirtIO", "virtio-net-pci"),("Intel E1000","e1000"),("Realtek RTL8139","rtl8139"),("VMware VMXNET3","vmxnet3")):
            self.model.addItem(label,val)
        i=self.model.findData(data.get("model","virtio-net-pci")); self.model.setCurrentIndex(max(0,i))
        self.mode=QComboBox()
        for label,val in ((self.tr("NAT / Internet"),"nat"),(self.tr("Bridge existente"),"bridge"),("TAP","tap")):
            self.mode.addItem(label,val)
        i=self.mode.findData(data.get("mode","nat")); self.mode.setCurrentIndex(max(0,i))
        self.target=QComboBox(); self.target.setEditable(True)
        self.mac=QLineEdit(data.get("mac","")); self.mac.setPlaceholderText(self.tr("Opcional: 52:54:00:xx:xx:xx"))
        # Reglas de reenvío de puertos NAT (solo aplican al backend NAT).
        # El usuario las edita desde el botón "🔀 Reglas NAT…" que aparece
        # cuando el modo es NAT. Se persisten en network_devices[i]["hostfwd"].
        self._hostfwd = [dict(r) for r in (data.get("hostfwd") or []) if isinstance(r, dict)]
        self.mode.currentIndexChanged.connect(self.update_target)
        form.addRow(self.tr("Nombre:"), self.name); form.addRow(self.tr("Modelo:"), self.model); form.addRow(self.tr("Backend:"), self.mode); form.addRow(self.tr("Bridge / TAP:"), self.target); form.addRow(self.tr("MAC:"), self.mac)
        self.btn_nat_rules = QPushButton(self.tr("🔀 Reglas NAT…"))
        self.btn_nat_rules.setToolTip(self.tr(
            "Redirigir puertos del host al guest a través del NAT de QEMU\n"
            "(hostfwd). Solo aplica cuando el backend es NAT."
        ))
        self.btn_nat_rules.clicked.connect(self._open_nat_rules)
        form.addRow("", self.btn_nat_rules)
        buttons=QHBoxLayout(); buttons.addStretch(); ok=QPushButton(self.tr("Aceptar")); cancel=QPushButton(self.tr("Cancelar")); ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); buttons.addWidget(cancel); buttons.addWidget(ok); form.addRow(buttons)
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
            btn.setText(self.tr("🔀 Reglas NAT… ({0})").format(n) if n else self.tr("🔀 Reglas NAT…"))

    def _open_nat_rules(self):
        """Abre el sub-diálogo de reenvío de puertos NAT."""
        dlg = NatPortForwardDialog(self, getattr(self, "_hostfwd", []))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._hostfwd = dlg.values()
            self.update_target()
    def values(self):
        return {
            "name": self.name.text().strip() or self.tr("Red"),
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
        self.setWindowTitle(self.tr("Configurar dispositivo de almacenamiento"))
        self.setModal(True)
        self.setMinimumWidth(640)
        self.resize(700, 430)

        layout = QVBoxLayout(self)
        title_map = {
            "sata": self.tr("💽 Disco SATA"), "nvme": self.tr("⚡ Disco NVMe"),
            "floppy": self.tr("💾 Disquetera"), "cdrom": self.tr("📀 Unidad CD / DVD"),
        }
        title = QLabel(title_map.get(devtype, self.tr("Dispositivo de almacenamiento")))
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
        cancel = QPushButton(self.tr("Cancelar"))
        accept = QPushButton(self.tr("Aceptar"))
        accept.setDefault(True)
        cancel.clicked.connect(self.reject)
        accept.clicked.connect(self._validate_and_accept)
        buttons.addWidget(cancel)
        buttons.addWidget(accept)
        layout.addLayout(buttons)

    def _build_cdrom(self, layout):
        form = QFormLayout()
        self.cd_mode = QComboBox()
        self.cd_mode.addItem(self.tr("Mantener vacío"), "empty")
        self.cd_mode.addItem(self.tr("Usar ISO/IMG/DMG existente"), "existing")
        if self.os_type == "macos":
            self.cd_mode.addItem(self.tr("System Recovery de macOS (descargar al iniciar)"), "recovery")
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
                installer_label = self.tr("Descargar instalador de Windows automáticamente")
                self.cd_mode.addItem(installer_label, "installer")
            else:
                _installer_label = self.tr("Descargar instalador de Linux automáticamente")
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
        form.addRow(self.tr("Fuente del medio:"), self.cd_mode)

        self.input_name = QLineEdit(self.initial_name or "CD/DVD")
        form.addRow(self.tr("Nombre:"), self.input_name)
        self.input_path = QLineEdit(self.initial_path or "")
        self.input_path.setPlaceholderText(self.tr("Selecciona una ISO / IMG / DMG…"))
        self.btn_browse = QPushButton(self.tr("📁 Buscar…"))
        self.btn_browse.clicked.connect(self._browse_medium)
        # media_library_picker_v1: boton para elegir de la biblioteca.
        self.btn_library = QPushButton(self.tr("📚 Biblioteca…"))
        self.btn_library.setToolTip(self.tr(
            "Elegir un medio de la biblioteca central (MediaLibrary/).\n"
            "Se reutiliza entre todas las VMs."
        ))
        self.btn_library.clicked.connect(self._pick_from_library)
        path_widget = QWidget()
        row = QHBoxLayout(path_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.input_path, 1)
        row.addWidget(self.btn_browse)
        row.addWidget(self.btn_library)
        form.addRow(self.tr("Medio:"), path_widget)
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
        form.addRow(self.tr("Nombre:"), self.input_name)

        # media_library_device_picker_v1_B: selector crear/existente
        # disponible tambien para floppy.
        mode_row = QHBoxLayout()
        self.source_radio = QRadioButton(self.tr("Crear nuevo"))
        self.existing_radio = QRadioButton(self.tr("Usar archivo existente"))
        self.source_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.source_radio)
        group.addButton(self.existing_radio)
        mode_row.addWidget(self.source_radio)
        mode_row.addWidget(self.existing_radio)
        mode_row.addStretch()
        form.addRow(self.tr("Origen:"), mode_row)
        self.source_radio.toggled.connect(self._update_disk_mode)

        if self.devtype == "floppy":
            self.input_size = QComboBox()
            for label, val in (("720 KB", "720K"), ("1.44 MB", "1.44M"), ("2.88 MB", "2.88M")):
                self.input_size.addItem(label, val)
            self.input_size.setCurrentIndex(1)
            form.addRow(self.tr("Tamaño:"), self.input_size)
            self.combo_format = QComboBox()
            self.combo_format.addItem("RAW", "raw")
            form.addRow(self.tr("Formato:"), self.combo_format)
        else:
            self.input_size = QLineEdit("40G")
            self.input_size.setPlaceholderText(self.tr("Ej.: 40G, 100G, 1T"))
            form.addRow(self.tr("Tamaño:"), self.input_size)
            self.combo_type = QComboBox()
            self.combo_type.addItem(self.tr("Expandible (dinámico)"), "dynamic")
            self.combo_type.addItem(self.tr("Fijo (preasignado)"), "fixed")
            form.addRow(self.tr("Tipo:"), self.combo_type)
            self.combo_format = QComboBox()
            for label, value in (("QCOW2", "qcow2"), ("RAW", "raw"), ("VDI", "vdi"), ("VMDK", "vmdk")):
                self.combo_format.addItem(label, value)
            form.addRow(self.tr("Formato:"), self.combo_format)


        # media_library_device_picker_v1_B: campo Archivo + botones
        # compartidos por los 3 tipos.
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText(self.tr("Ruta del archivo existente…"))
        self.btn_browse = QPushButton(self.tr("📁 Buscar…"))
        self.btn_browse.clicked.connect(self._browse_existing)
        self.btn_library_disk = QPushButton(self.tr("📚 Biblioteca…"))
        self.btn_library_disk.setToolTip(self.tr(
            "Elegir un archivo ya registrado en la Biblioteca de Medios.\n"
            "Se filtra por el tipo del dispositivo."
        ))
        self.btn_library_disk.clicked.connect(self._pick_from_library)
        self.path_widget = QWidget()
        row = QHBoxLayout(self.path_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.input_path, 1)
        row.addWidget(self.btn_browse)
        row.addWidget(self.btn_library_disk)
        form.addRow(self.tr("Archivo:"), self.path_widget)

        layout.addLayout(form)
        hint_text = (
            self.tr("Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.")
            if self.devtype == "floppy" else
            self.tr("Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. También puedes adjuntar un disco existente.")
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
            "empty": self.tr("La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida."),
            "existing": self.tr("Selecciona un ISO/IMG/DMG que ya exista en tu equipo."),
            "recovery": self.tr("Para macOS se descargará System Recovery automáticamente al iniciar la VM y se asociará a esta unidad óptica."),
            "installer": self.tr(
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
            filter_str = self.tr("Imágenes de disquete (*.img *.raw)"
                                 ";;Todos los archivos (*)")
        else:
            filter_str = self.tr("Discos virtuales "
                                 "(*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx)"
                                 ";;Todos los archivos (*)")
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Seleccionar archivo existente"), "", filter_str
        )
        if path:
            self.input_path.setText(path)

    def _browse_medium(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Seleccionar medio óptico"), "",
            self.tr("Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)")
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
                    QMessageBox.warning(self, self.tr("Medio inválido"), self.tr("Selecciona un ISO/IMG/DMG válido."))
                    return
            self.accept()
            return

        existing = bool(getattr(self, "existing_radio", None)
                        and self.existing_radio.isChecked())
        if existing:
            path = self.input_path.text().strip()
            if not path or not os.path.isfile(path):
                QMessageBox.warning(self, self.tr("Archivo inválido"),
                                    self.tr("Selecciona un archivo existente válido."))
                return
            self.accept()
            return

        name = self.input_name.text().strip()
        size = self.input_size.currentData() if self.devtype == "floppy" else self.input_size.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Nombre requerido"), self.tr("Indica un nombre para el dispositivo."))
            return
        if self.devtype != "floppy" and not re.fullmatch(r"(?:\d+(?:\.\d+)?)(?:[KMGTP]i?B?|B)?", size, re.IGNORECASE):
            QMessageBox.warning(self, self.tr("Tamaño inválido"), self.tr("Usa un tamaño como 40G, 512M o 1T."))
            return
        self.accept()

    def values(self):
        if self.devtype == "cdrom":
            mode = self.cd_mode.currentData()
            return {
                "name": self.input_name.text().strip() or self.tr("CD/DVD"),
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
        self.setWindowTitle(self.tr("Crear medio nuevo"))
        self.setModal(True)
        self.resize(520, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_name = QLineEdit("nuevo_medio")
        self.input_name.setPlaceholderText(self.tr("Ej: disco_ubuntu_datos"))
        form.addRow(self.tr("Nombre:"), self.input_name)

        # media_library_create_disk_v1_dialogs: tipos ampliados.
        # QEMU llama "vpc" al formato VHD; el mapeo se hace en values().
        self.combo_type = QComboBox()
        self.combo_type.addItem(
            self.tr("Disco duro QCOW2 (recomendado)"), "qcow2")
        self.combo_type.addItem(
            self.tr("Disco duro RAW"), "raw")
        self.combo_type.addItem(
            self.tr("Disco duro VMDK (VirtualBox / VMware)"), "vmdk")
        self.combo_type.addItem(
            self.tr("Disco duro VDI (VirtualBox nativo)"), "vdi")
        self.combo_type.addItem(
            self.tr("Disco duro VHD (Hyper-V antiguo)"), "vhd")
        self.combo_type.addItem(
            self.tr("Disco duro VHDX (Hyper-V moderno)"), "vhdx")
        self.combo_type.addItem(
            self.tr("Disquete IMG (RAW)"), "img")
        idx = self.combo_type.findData(default_type)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow(self.tr("Tipo:"), self.combo_type)

        # media_library_create_disk_v1_prealloc: combo de preasignacion.
        # Solo aplica a QCOW2, VDI y VHD. En el resto se oculta.
        self.label_prealloc = QLabel(self.tr("Preasignación:"))
        self.combo_prealloc = QComboBox()
        self.combo_prealloc.addItem(
            self.tr("Expandible (dinámico)"), "dynamic")
        self.combo_prealloc.addItem(
            self.tr("Fijo (preasignado)"), "fixed")
        self.combo_prealloc.setCurrentIndex(0)
        self.combo_prealloc.setToolTip(self.tr(
            "Expandible: el archivo crece solo según se usa (recomendado).\n"
            "Fijo: reserva todo el espacio en disco desde el momento de\n"
            "su creación. Tarda más y ocupa más, pero el rendimiento de\n"
            "escritura es más predecible."))
        form.addRow(self.label_prealloc, self.combo_prealloc)

        self.combo_size = QComboBox()
        self.combo_size.setEditable(True)
        self.combo_size.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        form.addRow(self.tr("Tamaño:"), self.combo_size)

        layout.addLayout(form)

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.hint)
        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        cancel.clicked.connect(self.reject)
        ok = QPushButton(self.tr("Crear"))
        ok.setDefault(True)
        ok.clicked.connect(self._validate_and_accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

        self._on_type_changed()

    def _on_type_changed(self, *_):
        t = self.combo_type.currentData() or "qcow2"
        # media_library_create_disk_v1_prealloc: mostrar el combo de
        # preasignacion solo donde aplica.
        try:
            _show = t in ("qcow2", "vdi", "vhd")
            self.label_prealloc.setVisible(_show)
            self.combo_prealloc.setVisible(_show)
            if t == "qcow2":
                self.combo_prealloc.setToolTip(self.tr(
                    "Expandible: preallocation=off (recomendado).\n"
                    "Fijo: preallocation=full. Reserva todo el espacio\n"
                    "en el host desde el momento de su creación."))
            elif t == "vdi":
                self.combo_prealloc.setToolTip(self.tr(
                    "Expandible: VDI dinámico (recomendado).\n"
                    "Fijo: static=on. Reserva todo el espacio en el host."))
            elif t == "vhd":
                self.combo_prealloc.setToolTip(self.tr(
                    "Expandible: VHD dynamic (recomendado).\n"
                    "Fijo: subformat=fixed. Reserva todo el espacio."))
        except Exception:
            pass
        self.combo_size.blockSignals(True)
        self.combo_size.clear()
        if t == "img":
            for s in ("720K", "1.44M", "2.88M"):
                self.combo_size.addItem(s, s)
            self.combo_size.setCurrentIndex(1)  # 1.44M
            self.hint.setText(self.tr(
                "Disquete formateado como RAW. Se registra como tipo "
                "'Disquete' en la biblioteca. Tamaños típicos: 720 KB, "
                "1.44 MB, 2.88 MB."
            ))
        else:
            for s in ("10G", "20G", "40G", "80G", "128G", "256G",
                      "512G", "1T"):
                self.combo_size.addItem(s, s)
            self.combo_size.setCurrentIndex(2)  # 40G
            # media_library_create_disk_v1_dialogs: hints especificos.
            if t == "qcow2":
                self.hint.setText(self.tr(
                    "Disco virtual expandible (recomendado). El archivo "
                    "en el host crece solo según se usa en el guest."
                ))
            elif t == "raw":
                self.hint.setText(self.tr(
                    "Disco RAW (imagen plana). Ocupa el tamaño completo "
                    "en el host desde el momento de su creación."
                ))
            elif t == "vmdk":
                self.hint.setText(self.tr(
                    "Formato VMDK monolithicSparse (compatible con "
                    "VirtualBox y VMware). El archivo crece según se "
                    "usa; las snapshots internas de QEMU no aplican."
                ))
            elif t == "vdi":
                self.hint.setText(self.tr(
                    "Formato VDI nativo de VirtualBox. El archivo crece "
                    "según se usa."
                ))
            elif t == "vhd":
                self.hint.setText(self.tr(
                    "Formato VHD (Hyper-V hasta Windows 2008 R2). "
                    "Compatible con la mayoría de hipervisores. QEMU lo "
                    "llama internamente 'vpc'."
                ))
            elif t == "vhdx":
                self.hint.setText(self.tr(
                    "Formato VHDX (Hyper-V moderno, desde Windows 2012). "
                    "Soporta discos de hasta 64 TB y bloques de 4 KB."
                ))
            else:
                self.hint.setText(self.tr(
                    "Disco virtual expandible."
                ))
        self.combo_size.blockSignals(False)

    def _validate_and_accept(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Nombre requerido"),
                                self.tr("Escribe un nombre para el medio."))
            return
        if re.search(r'[\\/:*?"<>|]', name):
            QMessageBox.warning(
                self, self.tr("Nombre inválido"),
                self.tr("El nombre no puede contener \\ / : * ? \" < > |")
            )
            return
        # media_library_create_disk_v1_size_fix: el combo es editable.
        # Priorizar SIEMPRE currentText() (lo que el usuario ve, sea
        # del desplegable o tecleado). currentData() se usa solo como
        # respaldo si el texto está vacío.
        size = (self.combo_size.currentText().strip()
                or str(self.combo_size.currentData() or ""))
        if not size or not re.fullmatch(
                r"(?:\d+(?:\.\d+)?)(?:[KMGTP]i?B?|B)?",
                size, re.IGNORECASE):
            QMessageBox.warning(
                self, self.tr("Tamaño inválido"),
                self.tr("Usa un tamaño como 40G, 512M o 1T.")
            )
            return
        self.accept()

    def values(self):
        t = self.combo_type.currentData() or "qcow2"
        # media_library_create_disk_v1_dialogs: mapeo tipo -> (ext, qemu
        # format, kind en la biblioteca).
        #   * QEMU llama "vpc" al formato VHD.
        #   * IMG es RAW con extension distinta.
        _map = {
            "qcow2": (".qcow2", "qcow2", "qcow2"),
            "raw":   (".raw",   "raw",   "raw"),
            "vmdk":  (".vmdk",  "vmdk",  "vmdk"),
            "vdi":   (".vdi",   "vdi",   "vdi"),
            "vhd":   (".vhd",   "vpc",   "vhd"),
            "vhdx":  (".vhdx",  "vhdx",  "vhdx"),
            "img":   (".img",   "raw",   "img"),
        }
        ext, fmt, kind = _map.get(t, (".qcow2", "qcow2", "qcow2"))
        # media_library_create_disk_v1_prealloc: valor de preasignacion.
        # Si el combo esta oculto (formato que no aplica), se calcula el
        # default segun el tipo: RAW e IMG son siempre "fijos" por
        # naturaleza; VMDK y VHDX son siempre "expandibles".
        try:
            if t in ("qcow2", "vdi", "vhd"):
                prealloc = self.combo_prealloc.currentData() or "dynamic"
            elif t in ("raw", "img"):
                prealloc = "fixed"
            else:  # vmdk, vhdx
                prealloc = "dynamic"
        except Exception:
            prealloc = "dynamic"
        # media_library_create_disk_v1_size_fix: priorizar currentText()
        # (lo que el usuario ve, sea del desplegable o tecleado).
        _size_txt = self.combo_size.currentText().strip()
        if not _size_txt:
            _size_txt = str(self.combo_size.currentData() or "")
        return {
            "name": self.input_name.text().strip(),
            "type": t,
            "extension": ext,
            "format": fmt,
            "kind": kind,
            "prealloc": prealloc,
            "size": _size_txt,
        }

    @staticmethod
    def build_qemu_create_cmd(values, target_path):
        """Construye la lista de argumentos de 'qemu-img create'.

        Marcador: media_library_create_disk_v1_prealloc.
        Aplica las opciones de preasignacion segun el tipo:
          QCOW2 + fixed   -> -o preallocation=full
          QCOW2 + dynamic -> -o preallocation=off
          VDI   + fixed   -> -o static=on
          VHD   + fixed   -> -o subformat=fixed
        El resto de combinaciones se dejan con los defaults de QEMU.
        """
        cmd = ["qemu-img", "create", "-f", str(values.get("format") or "qcow2")]
        t = str(values.get("type") or "")
        p = str(values.get("prealloc") or "dynamic")
        if t == "qcow2":
            if p == "fixed":
                cmd += ["-o", "preallocation=full"]
            else:
                cmd += ["-o", "preallocation=off"]
        elif t == "vdi":
            if p == "fixed":
                cmd += ["-o", "static=on"]
        elif t == "vhd":
            if p == "fixed":
                cmd += ["-o", "subformat=fixed"]
        cmd += [target_path, str(values.get("size") or "")]
        return cmd


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
        self.setWindowTitle(self.tr("Elegir medio de la biblioteca"))
        self.setModal(True)
        self.resize(820, 500)

        self._lib = None
        self._chosen = None
        self._filter_os_type = (filter_os_type or "").lower()
        # media_library_picker_filter_type_v1: 'disk' / 'iso' / 'floppy' / ''.
        self._filter_media_type = (filter_media_type or "").lower()

        layout = QVBoxLayout(self)

        info = QLabel(self.tr(
            "Elige una ISO/IMG/DMG de la biblioteca central.<br>"
            "La biblioteca vive en <code>MediaLibrary/</code>, al mismo "
            "nivel que <code>VirtualMachines/</code>. Se reutiliza entre "
            "todas las VMs."
        ))
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        filt = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.tr("Buscar..."))
        self.search.textChanged.connect(self._refresh)
        filt.addWidget(self.search, 1)
        filt.addWidget(QLabel(self.tr("SO:")))
        self.cmb_os = QComboBox()
        self.cmb_os.addItem(self.tr("Todos"), "")
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
        filt.addWidget(QLabel(self.tr("Tipo:")))
        self.cmb_type = QComboBox()
        self.cmb_type.addItem(self.tr("Todos"), "")
        self.cmb_type.addItem(self.tr("Disco duro"), "disk")
        self.cmb_type.addItem("ISO", "iso")
        self.cmb_type.addItem(self.tr("Disquete"), "floppy")
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
            [self.tr("Nombre"), self.tr("Tipo"), self.tr("SO"),
             self.tr("Version"), self.tr("Arq."), self.tr("Tamano"),
             self.tr("Usada por"), self.tr("Ruta")]
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
        self.btn_add = QPushButton(self.tr("Anadir archivo a la biblioteca..."))
        self.btn_add.setToolTip(self.tr(
            "Registrar una ISO nueva sin salir de este dialogo."
        ))
        self.btn_add.clicked.connect(self._add_new_file)
        btns.addWidget(self.btn_add)

        # media_library_create_v1: crear un disco nuevo en la biblioteca
        # sin salir del selector.
        self.btn_create = QPushButton(self.tr("Crear disco..."))
        self.btn_create.setToolTip(self.tr(
            "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
            "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
            "sobre MediaLibrary/<nombre>.<ext>."
        ))
        self.btn_create.clicked.connect(self._create_new_medium)
        btns.addWidget(self.btn_create)

        self.btn_open_folder = QPushButton(self.tr("Abrir carpeta"))
        self.btn_open_folder.setToolTip(self.tr(
            "Abre MediaLibrary/ en el explorador del sistema."
        ))
        self.btn_open_folder.clicked.connect(self._open_library_folder)
        btns.addWidget(self.btn_open_folder)

        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        self.btn_ok = QPushButton(self.tr("Elegir"))
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
                name = self.tr("{0}   (huerfano)").format(name)
            # media_library_picker_columns_v1: "Usada por" y "Ruta".
            used_by = list(e.get("used_by") or [])
            if not used_by:
                used_by_txt = "\u2014"
            elif len(used_by) <= 3:
                used_by_txt = ", ".join(used_by)
            else:
                used_by_txt = self.tr("{0}, {1} (+{2})").format(
                    used_by[0], used_by[1], len(used_by) - 2)
            stored_path = str(e.get("path") or "")
            if os.path.isabs(stored_path) and len(stored_path) > 40:
                path_txt = "\u2026" + stored_path[-37:]
            else:
                path_txt = stored_path or self.tr("(sin archivo)")
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
            row.setToolTip(0, path_abs or self.tr("(sin archivo)"))
            row.setToolTip(6, ("\n".join(used_by) if used_by
                               else self.tr("No la usa ninguna VM.")))
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
                self, self.tr("Archivo no disponible"),
                self.tr("El archivo de esta entrada ya no existe en el disco.\n\n"
                        "Ruta esperada:\n{0}").format(path_abs)
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
                self, self.tr("Biblioteca no disponible"),
                self.tr("La biblioteca de medios no está disponible.")
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
                self, self.tr("Ya existe"),
                self.tr("Ya existe un archivo con ese nombre en la biblioteca:\n\n"
                        "{0}\n\n"
                        "Elige otro nombre o bórralo desde la pestaña Medios.").format(target)
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
                self, self.tr("Crear medio"),
                self.tr("No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
                        "en Debian/Ubuntu, qemu-img en Arch) para crear discos.")
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Crear medio"),
                self.tr("No se pudo crear el medio.\n\n{0}").format(e)
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
                    notes=self.tr("Creado con qemu-img create. "
                                  "Tamaño: {0}.").format(v['size']),
                )
                self._lib.mark_used(entry_id)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Crear medio"),
                self.tr("El archivo se creó correctamente pero no se pudo\n"
                        "registrar en la biblioteca:\n\n{0}").format(e)
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
            self, self.tr("Medio creado"),
            self.tr("Se creó el medio correctamente.\n\n"
                    "Archivo: {0}\n"
                    "Tamaño: {1}\n"
                    "Formato: {2}").format(fname, v['size'], v['format'].upper())
        )

    def _add_new_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Anadir a la biblioteca"), os.path.expanduser("~"),
            self.tr("Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)")
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
        self.setWindowTitle(self.tr("Reglas de reenvío de puertos NAT"))
        self.setModal(True)
        self.resize(580, 400)

        self._rules = [dict(r) for r in (rules or []) if isinstance(r, dict)]

        layout = QVBoxLayout(self)

        info = QLabel(self.tr(
            "Redirige puertos del host al guest a través del NAT de QEMU "
            "(<code>-netdev user,hostfwd=...</code>). Cada regla conecta "
            "<b>localhost:puerto_host</b> del anfitrión con "
            "<b>puerto_guest</b> dentro del sistema invitado.<br><br>"
            "Ejemplo: host 2222 → guest 22 reenvía SSH; luego entra con "
            "<code>ssh -p 2222 usuario@localhost</code>."
        ))
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        # --- Fila de alta ---
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel(self.tr("Puerto host:")))
        self.sp_host = QSpinBox()
        self.sp_host.setRange(1, 65535)
        self.sp_host.setValue(2222)
        self.sp_host.setToolTip(self.tr("Puerto en el host (donde tú te conectas)."))
        add_row.addWidget(self.sp_host)
        add_row.addSpacing(10)
        add_row.addWidget(QLabel(self.tr("Puerto guest:")))
        self.sp_guest = QSpinBox()
        self.sp_guest.setRange(1, 65535)
        self.sp_guest.setValue(22)
        self.sp_guest.setToolTip(self.tr("Puerto dentro de la VM (a donde se reenvía)."))
        add_row.addWidget(self.sp_guest)
        add_row.addSpacing(10)
        add_row.addWidget(QLabel(self.tr("Protocolo:")))
        self.cmb_proto = QComboBox()
        self.cmb_proto.addItem("TCP", "tcp")
        self.cmb_proto.addItem("UDP", "udp")
        add_row.addWidget(self.cmb_proto)
        add_row.addStretch()
        self.btn_add = QPushButton(self.tr("➕ Añadir regla"))
        self.btn_add.clicked.connect(self._add_rule)
        add_row.addWidget(self.btn_add)
        layout.addLayout(add_row)

        # --- Tabla ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            [self.tr("Puerto host"), self.tr("Puerto guest"),
             self.tr("Protocolo")]
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
        self.btn_remove = QPushButton(self.tr("🗑 Quitar seleccionada"))
        self.btn_remove.clicked.connect(self._remove_selected)
        bottom.addWidget(self.btn_remove)
        bottom.addStretch()
        btn_cancel = QPushButton(self.tr("Cancelar"))
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_cancel)
        btn_ok = QPushButton(self.tr("Aceptar"))
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
                    self, self.tr("Regla duplicada"),
                    self.tr("Ya existe una regla para el puerto host {0} "
                            "({1}).\n\nElige otro puerto host o "
                            "cambia el protocolo.").format(hp, proto.upper()),
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



# media_library_create_disk_v1_dialogs


# media_library_create_disk_v1_prealloc


# media_library_create_disk_v1_size_fix
