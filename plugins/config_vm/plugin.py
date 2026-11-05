import uuid
import os
import subprocess
import shutil
import time
import requests
import re
import logging
from pathlib import Path
from urllib.parse import urlparse, unquote
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QStackedWidget, QComboBox, QCheckBox, QLineEdit,
    QFormLayout, QSlider, QSpinBox, QScrollArea, QMessageBox, QDialog,
    QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QFileDialog, QRadioButton, QToolButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QGroupBox,
    QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEventLoop
from core.plugin_base import PluginBase
from services.host_profile import HostProfile
from services.vm_profiles import get_vm_profiles
from services.os_catalog import OS_CATALOG
from services import iso_versions
from services import iso_sources
from services import host_passthrough
from ui_widgets.media_library_dialog import MediaLibraryDialog

log = logging.getLogger(__name__)

class DownloadISOThread(QThread):
    progress = pyqtSignal(int, str)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self._is_cancelled = False

    def stop(self):
        self._is_cancelled = True
        
    def run(self):
        try:
            dest_path = Path(self.dest_path)
            part_path = Path(str(dest_path) + ".part")
            if part_path.exists(): part_path.unlink()
            if dest_path.exists(): dest_path.unlink()
            
            filename = dest_path.name
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) VirtualMachine/1.0'}
            session = requests.Session()
            session.headers.update(headers)
            
            real_url = self.url
            try:
                r = session.get(self.url, stream=True, timeout=(15, 60))
                if "text/html" in r.headers.get("Content-Type", ""):
                    html = r.text
                    match = re.search(r'url=(https?://[^"\']+)', html) or re.search(r'(https://downloads\.sourceforge\.net/[^"\']+)', html)
                    if match: real_url = match.group(1)
                else:
                    real_url = r.url
                r.close()
            except: pass
            
            response = session.get(real_url, stream=True, timeout=(15, 120))
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            
            if total > 0 and total < 5000000:
                raise Exception(f"El archivo es demasiado pequeño ({total} bytes). Probablemente sea un HTML de error.")
            
            with open(part_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if self._is_cancelled:
                        part_path.unlink()
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        mb_dl = downloaded / (1024 * 1024)
                        if total > 0:
                            mb_total = total / (1024 * 1024)
                            pct = min(100, int((downloaded / total) * 100))
                            text = f"Descargando {filename}\n{mb_dl:.1f} MB de {mb_total:.1f} MB"
                        else:
                            pct = 0
                            text = f"Descargando {filename}\n{mb_dl:.1f} MB descargados"
                        self.progress.emit(pct, text)
                        
            if downloaded < 5000000:
                raise Exception(f"La descarga falló o es un archivo inválido. Tamaño: {downloaded} bytes.")
            if total > 0 and downloaded < total:
                raise Exception("La descarga se interrumpió antes de terminar.")
                
            part_path.rename(dest_path)
            self.finished_ok.emit(str(dest_path))
        except Exception as e:
            if 'part_path' in locals() and part_path.exists():
                try: part_path.unlink()
                except: pass
            if not self._is_cancelled:
                self.error.emit(str(e))

def scan_pci_devices():
    devices = []
    pci_path = "/sys/bus/pci/devices"
    if not os.path.exists(pci_path): return devices
    for bdf in os.listdir(pci_path):
        dev_dir = os.path.join(pci_path, bdf)
        try:
            with open(os.path.join(dev_dir, "vendor"), "r") as f: vendor = f.read().strip()
            with open(os.path.join(dev_dir, "device"), "r") as f: device = f.read().strip()
            with open(os.path.join(dev_dir, "class"), "r") as f: dev_class = f.read().strip()

            is_vga = dev_class.startswith("0x03")
            is_audio = dev_class.startswith("0x04")
            vid_did = f"{vendor.replace('0x','')}:{device.replace('0x','')}"

            iommu = "Sin grupo IOMMU"
            if os.path.exists(os.path.join(dev_dir, "iommu_group")):
                try:
                    group_num = os.path.basename(os.readlink(os.path.join(dev_dir, "iommu_group")))
                    iommu = f"Grupo {group_num}"
                except: pass

            driver = "Ninguno"
            driver_link = os.path.join(dev_dir, "driver")
            if os.path.exists(driver_link):
                try: driver = os.path.basename(os.readlink(driver_link))
                except: pass

            if driver == "vfio-pci": status = "Listo"
            elif iommu == "Sin grupo IOMMU": status = "Falta IOMMU"
            else: status = f"Necesita vfio-pci (driver: {driver})"

            kind = "GPU" if is_vga else ("Audio" if is_audio else "PCI")
            devices.append({"type": "PCI", "id": bdf, "vid_did": vid_did, "desc": f"{kind} {bdf} [{vid_did}]", "iommu": iommu, "driver": driver, "is_vga": is_vga, "is_audio": is_audio, "status": status})
        except: continue
    return devices

def scan_usb_devices():
    devices = []
    usb_path = "/sys/bus/usb/devices"
    if not os.path.exists(usb_path): return devices
    for dev_id in os.listdir(usb_path):
        dev_dir = os.path.join(usb_path, dev_id)
        try:
            v_path = os.path.join(dev_dir, "idVendor")
            p_path = os.path.join(dev_dir, "idProduct")
            b_path = os.path.join(dev_dir, "busnum")
            n_path = os.path.join(dev_dir, "devnum")
            if not all(os.path.exists(x) for x in (v_path, p_path, b_path, n_path)): continue

            with open(v_path, "r") as f: vendor = f.read().strip()
            with open(p_path, "r") as f: product = f.read().strip()
            with open(b_path, "r") as f: busnum = f.read().strip()
            with open(n_path, "r") as f: devnum = f.read().strip()

            name = "Dispositivo USB"
            name_path = os.path.join(dev_dir, "product")
            if os.path.exists(name_path):
                with open(name_path, "r") as f: name = f.read().strip()

            vid_pid = f"{vendor}:{product}"
            devices.append({"type": "USB", "id": f"{busnum}:{devnum}", "vid_did": vid_pid, "desc": f"{name} [{vid_pid}] bus {busnum} addr {devnum}", "iommu": "N/A", "status": "Listo"})
        except: continue
    return devices

class DiskDialog(QDialog):
    def __init__(self, parent=None, disk_data=None, default_dir=None, app=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(600, 550)
        self.layout = QVBoxLayout(self)
        self.default_dir = default_dir
        
        form = QFormLayout()
        form.addRow(QLabel("<b>💽 Disco Duro / SATA</b>"))
        
        self.input_name = QLineEdit("datos")
        self.input_name.textChanged.connect(self._update_path)
        form.addRow("Nombre del archivo:", self.input_name)
        
        origen_layout = QHBoxLayout()
        self.radio_new = QRadioButton("Crear nuevo")
        self.radio_existing = QRadioButton("Usar archivo existente")
        self.radio_new.setChecked(True)
        self.radio_new.toggled.connect(self._toggle_mode)
        origen_layout.addWidget(self.radio_new); origen_layout.addWidget(self.radio_existing)
        form.addRow("Origen:", origen_layout)
        
        self.widget_new = QWidget()
        lay_new = QFormLayout(self.widget_new)
        lay_new.setContentsMargins(0,0,0,0)
        
        self.input_size = QLineEdit("40G")
        lay_new.addRow("Tamaño:", self.input_size)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Expandible (dinámico)", "Fijo (preasignado)"])
        lay_new.addRow("Tipo:", self.combo_type)
        
        self.combo_format = QComboBox()
        self.combo_format.addItems(["QCOW2", "IMG (RAW)", "VDI", "VMDK", "VHD", "VHDX"])
        self.combo_format.currentIndexChanged.connect(self._update_path)
        lay_new.addRow("Formato:", self.combo_format)
        
        form.addRow(self.widget_new)

        self.combo_bus = QComboBox()
        self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "NVMe", "IDE", "SCSI (emulado)", "VirtIO-BLK", "VirtIO-SCSI"])
        form.addRow("Bus del disco:", self.combo_bus)
        
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Ruta completa del disco...")
        self.input_path.setReadOnly(True)
        self.btn_browse_path = QPushButton("📁")
        self.btn_browse_path.clicked.connect(self._browse_path)
        
        self.path_widget = QWidget()
        path_layout = QHBoxLayout(self.path_widget)
        path_layout.setContentsMargins(0,0,0,0)
        path_layout.addWidget(self.input_path)
        path_layout.addWidget(self.btn_browse_path)
        form.addRow("Ubicación del disco:", self.path_widget)
        
        self.widget_existing = QWidget()
        lay_exist = QHBoxLayout(self.widget_existing)
        lay_exist.setContentsMargins(0,0,0,0)
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.clicked.connect(self._browse_existing)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.clicked.connect(self._browse_library)
        lay_exist.addWidget(self.input_file); lay_exist.addWidget(self.btn_browse); lay_exist.addWidget(self.btn_lib)
        form.addRow("Archivo existente:", self.widget_existing)
        self.widget_existing.setVisible(False)
        
        self.layout.addLayout(form)
        
        self.btn_advanced = QToolButton()
        self.btn_advanced.setText("▶ Avanzado (rendimiento e I/O)")
        self.btn_advanced.setCheckable(True)
        self.btn_advanced.clicked.connect(self._toggle_advanced)
        self.layout.addWidget(self.btn_advanced)
        
        self.widget_advanced = QWidget()
        lay_adv = QFormLayout(self.widget_advanced)
        lay_adv.setContentsMargins(10, 0, 0, 0)
        self.combo_cache = QComboBox()
        self.combo_cache.addItems(["Automático (writeback)", "none", "writeback", "writethrough"])
        lay_adv.addRow("Caché (cache=):", self.combo_cache)
        self.combo_io = QComboBox()
        self.combo_io.addItems(["Automático (threads)", "threads", "native", "io_uring"])
        lay_adv.addRow("Backend I/O (io=):", self.combo_io)
        self.combo_discard = QComboBox()
        self.combo_discard.addItems(["Automático (ignore)", "unmap", "ignore"])
        lay_adv.addRow("Discard:", self.combo_discard)
        self.combo_detect_zeros = QComboBox()
        self.combo_detect_zeros.addItems(["Automático (off)", "on", "off", "unmap"])
        lay_adv.addRow("Detect zeros:", self.combo_detect_zeros)
        self.combo_aio = QComboBox()
        self.combo_aio.addItems(["Automático (threads)", "threads", "native"])
        lay_adv.addRow("AIO:", self.combo_aio)
        self.layout.addWidget(self.widget_advanced)
        self.widget_advanced.setVisible(False)
        
        self.layout.addStretch()
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        self.layout.addWidget(btns)
        
        if disk_data:
            self.input_name.setText(disk_data.get("name", ""))
            self.input_file.setText(disk_data.get("path", ""))
            self.input_size.setText(disk_data.get("size", "40G"))
            if disk_data.get("format"): self.combo_format.setCurrentText(disk_data.get("format"))
            if disk_data.get("type"): self.combo_type.setCurrentText(disk_data.get("type"))
            if disk_data.get("bus"): self.combo_bus.setCurrentText(disk_data.get("bus"))
            self.radio_existing.setChecked(True)
        else:
            self._update_path()

    def _update_path(self):
        if self.radio_existing.isChecked(): return
        name = self.input_name.text().strip() or "datos"
        fmt_text = self.combo_format.currentText()
        ext = "qcow2"
        if "IMG" in fmt_text: ext = "img"
        elif "VDI" in fmt_text: ext = "vdi"
        elif "VMDK" in fmt_text: ext = "vmdk"
        elif "VHD" in fmt_text and "VHDX" not in fmt_text: ext = "vhd"
        elif "VHDX" in fmt_text: ext = "vhdx"
        filename = f"{name}.{ext}"
        if self.default_dir:
            self.input_path.setText(str(self.default_dir / filename))
        else:
            self.input_path.setText(filename)

    def _toggle_mode(self):
        is_new = self.radio_new.isChecked()
        self.widget_new.setVisible(is_new)
        self.path_widget.setVisible(is_new)
        self.widget_existing.setVisible(not is_new)
        if is_new: self._update_path()

    def _toggle_advanced(self):
        v = self.btn_advanced.isChecked()
        self.widget_advanced.setVisible(v)
        self.btn_advanced.setText("▼ Avanzado (rendimiento e I/O)" if v else "▶ Avanzado (rendimiento e I/O)")

    def _browse_path(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para el disco")
        if d:
            filename = os.path.basename(self.input_path.text())
            self.input_path.setText(os.path.join(d, filename))

    def _browse_existing(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar disco", "", "Discos (*.qcow2 *.img *.raw *.vdi *.vmdk *.vhd *.vhdx)")
        if p: self.input_file.setText(p)

    def _browse_library(self):
        dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.qcow2', '.img', '.raw', '.vdi', '.vmdk', '.vhd', '.vhdx'])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.input_file.setText(dlg.selected_path)

    def accept(self):
        if self.radio_new.isChecked() and not self.input_path.text():
            QMessageBox.warning(self, "Error", "Debes especificar una ruta para el nuevo disco.")
            return
        super().accept()

class CDDVDDialog(QDialog):
    def __init__(self, parent=None, cd_data=None, default_dir=None, app=None):
        super().__init__(parent)
        self.default_dir = default_dir
        self.app = app
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>📀 Unidad CD / DVD</b>"))
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(["Mantener vacío", "Usar ISO/IMG/DMG existente", "Descargar"])
        self.combo_source.currentIndexChanged.connect(self._toggle_source)
        layout.addRow("Fuente del medio:", self.combo_source)
        
        self.input_name = QLineEdit("CD/DVD")
        layout.addRow("Nombre:", self.input_name)
        
        self.combo_bus = QComboBox()
        self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "IDE", "SCSI (emulado)", "USB"])
        layout.addRow("Bus del CD/DVD:", self.combo_bus)
        
        self.media_widget = QWidget()
        h = QHBoxLayout(self.media_widget)
        h.setContentsMargins(0,0,0,0)
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.clicked.connect(self._browse_library)
        h.addWidget(self.input_file); h.addWidget(self.btn_browse); h.addWidget(self.btn_lib)
        layout.addRow("Medio:", self.media_widget)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)
        
        if cd_data: 
            self.input_file.setText(cd_data.get("path", ""))
            if cd_data.get("bus"): self.combo_bus.setCurrentText(cd_data.get("bus"))
            if cd_data.get("path"): self.combo_source.setCurrentText("Usar ISO/IMG/DMG existente")
        
        self._toggle_source()

    def _toggle_source(self):
        is_existing = (self.combo_source.currentText() == "Usar ISO/IMG/DMG existente")
        self.media_widget.setVisible(is_existing)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes (*.iso *.img *.dmg)")
        if p: self.input_file.setText(p)
        
    def _browse_library(self):
        dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.input_file.setText(dlg.selected_path)

class FloppyDialog(QDialog):
    def __init__(self, parent=None, default_dir=None, app=None):
        super().__init__(parent)
        self.default_dir = default_dir
        self.app = app
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>💾 Disquetera (FDC)</b>"))
        
        self.input_name = QLineEdit("floppy")
        layout.addRow("Nombre:", self.input_name)
        
        orig = QHBoxLayout()
        self.radio_new = QRadioButton("Crear nuevo"); self.radio_exist = QRadioButton("Usar archivo existente")
        self.radio_new.setChecked(True)
        orig.addWidget(self.radio_new); orig.addWidget(self.radio_exist)
        layout.addRow("Origen:", orig)
        
        self.combo_size = QComboBox()
        self.combo_size.addItems(["720 KB", "1.44 MB", "2.88 MB"]); self.combo_size.setCurrentText("1.44 MB")
        layout.addRow("Tamaño:", self.combo_size)
        
        self.input_format = QLineEdit("RAW"); self.input_format.setReadOnly(True)
        layout.addRow("Formato:", self.input_format)
        
        h_file = QHBoxLayout()
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.clicked.connect(self._browse_library)
        h_file.addWidget(self.input_file); h_file.addWidget(self.btn_browse); h_file.addWidget(self.btn_lib)
        layout.addRow("Archivo:", h_file)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar", "", "Imágenes (*.img *.raw)")
        if p: self.input_file.setText(p)
        
    def _browse_library(self):
        dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.img', '.raw', '.iso'])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.input_file.setText(dlg.selected_path)

class NetworkAdapterDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Adaptador de red virtual")
        self.resize(500, 500)
        self._data = data or {}
        self._nat_rules = list(self._data.get("nat_rules", []))
        
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>🌐 Adaptador de red virtual</b>"))
        
        self.input_name = QLineEdit(self._data.get("name", "Red 1"))
        layout.addRow("Nombre:", self.input_name)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(["VirtIO", "Intel E1000", "Realtek", "VMware VMXNET3"])
        idx = self.combo_model.findText(self._data.get("model", "VirtIO"))
        if idx >= 0: self.combo_model.setCurrentIndex(idx)
        layout.addRow("Modelo:", self.combo_model)
        
        self.combo_backend = QComboBox()
        self.combo_backend.addItems(["NAT / Internet", "Bridge existente", "TAP"])
        idx = self.combo_backend.findText(self._data.get("backend", "NAT / Internet"))
        if idx >= 0: self.combo_backend.setCurrentIndex(idx)
        self.combo_backend.currentTextChanged.connect(self._on_backend_changed)
        layout.addRow("Backend:", self.combo_backend)
        
        self.input_bridge = QLineEdit()
        self.input_bridge.setPlaceholderText("Nombre del bridge o TAP...")
        self.input_bridge.setText(self._data.get("bridge", ""))
        layout.addRow("Bridge / TAP:", self.input_bridge)
        
        self.input_mac = QLineEdit()
        self.input_mac.setPlaceholderText("Opcional: 52:54:00:xx:xx:xx")
        self.input_mac.setText(self._data.get("mac", ""))
        layout.addRow("MAC:", self.input_mac)
        
        self.btn_nat = QPushButton("📋 Reglas NAT...")
        self.btn_nat.clicked.connect(self._open_nat)
        layout.addRow("", self.btn_nat)
        
        self.lbl_nat_summary = QLabel("")
        self.lbl_nat_summary.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_nat_summary.setWordWrap(True)
        layout.addRow("", self.lbl_nat_summary)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)
        
        self._on_backend_changed(self.combo_backend.currentText())
        self._update_nat_summary()

    def _on_backend_changed(self, t):
        is_nat = (t == "NAT / Internet")
        self.input_bridge.setEnabled(not is_nat)
        self.btn_nat.setEnabled(is_nat)

    def _update_nat_summary(self):
        if not self._nat_rules:
            self.lbl_nat_summary.setText("Sin reglas de reenvío configuradas.")
        else:
            lines = []
            for r in self._nat_rules:
                lines.append(f"  • {r.get('proto', 'TCP')} host:{r.get('host', '?')} → guest:{r.get('guest', '?')}")
            self.lbl_nat_summary.setText("Reglas de reenvío:\n" + "\n".join(lines))

    def _open_nat(self):
        dlg = NatRulesDialog(self, self._nat_rules)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._nat_rules = dlg.get_rules()
            self._update_nat_summary()

    def get_data(self):
        backend = self.combo_backend.currentText()
        return {
            "name": self.input_name.text().strip() or "Red",
            "model": self.combo_model.currentText(),
            "backend": backend,
            "bridge": self.input_bridge.text().strip() if backend != "NAT / Internet" else "",
            "mac": self.input_mac.text().strip(),
            "nat_rules": self._nat_rules if backend == "NAT / Internet" else [],
        }

class NatRulesDialog(QDialog):
    def __init__(self, parent=None, rules=None):
        super().__init__(parent)
        self.setWindowTitle("Reglas de reenvío de puertos NAT")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        info = QLabel("Redirige puertos del host al guest a través del NAT de QEMU.")
        info.setWordWrap(True); layout.addWidget(info)
        h = QHBoxLayout()
        self.input_host = QLineEdit(); self.input_host.setPlaceholderText("Puerto host")
        self.input_guest = QLineEdit(); self.input_guest.setPlaceholderText("Puerto guest")
        self.combo_proto = QComboBox(); self.combo_proto.addItems(["TCP", "UDP"])
        btn_add = QPushButton("➕ Añadir"); btn_add.clicked.connect(self._add)
        h.addWidget(self.input_host); h.addWidget(self.input_guest); h.addWidget(self.combo_proto); h.addWidget(btn_add)
        layout.addLayout(h)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Puerto host", "Puerto guest", "Protocolo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        for r in (rules or []):
            self._insert_row(r.get("host", ""), r.get("guest", ""), r.get("proto", "TCP"))
        h_btns = QHBoxLayout()
        btn_del = QPushButton("🗑 Eliminar seleccionada")
        btn_del.clicked.connect(self._del_selected)
        h_btns.addWidget(btn_del); h_btns.addStretch()
        layout.addLayout(h_btns)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _insert_row(self, host, guest, proto):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(str(host)))
        self.table.setItem(r, 1, QTableWidgetItem(str(guest)))
        self.table.setItem(r, 2, QTableWidgetItem(proto))

    def _add(self):
        if self.input_host.text().strip() and self.input_guest.text().strip():
            self._insert_row(self.input_host.text().strip(), self.input_guest.text().strip(), self.combo_proto.currentText())
            self.input_host.clear(); self.input_guest.clear()

    def _del_selected(self):
        r = self.table.currentRow()
        if r >= 0: self.table.removeRow(r)

    def get_rules(self):
        rules = []
        for i in range(self.table.rowCount()):
            host = self.table.item(i, 0).text() if self.table.item(i, 0) else ""
            guest = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
            proto = self.table.item(i, 2).text() if self.table.item(i, 2) else "TCP"
            if host and guest:
                rules.append({"host": host, "guest": guest, "proto": proto})
        return rules

class SharedFolderDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Carpeta compartida")
        self.resize(500, 350)
        layout = QFormLayout(self)
        h_host = QHBoxLayout()
        self.input_host = QLineEdit(); self.btn_browse = QPushButton("📁")
        self.btn_browse.clicked.connect(self._browse)
        h_host.addWidget(self.input_host); h_host.addWidget(self.btn_browse)
        layout.addRow("Carpeta del host:", h_host)
        self.input_label = QLineEdit("share")
        layout.addRow("Etiqueta / guest:", self.input_label)
        self.combo_method = QComboBox(); self.combo_method.addItems(["Automático", "VirtioFS", "9p", "SMB"])
        layout.addRow("Método:", self.combo_method)
        self.combo_mount = QComboBox(); self.combo_mount.addItems(["Manual", "Automático al iniciar SO", "Automático bajo demanda"])
        layout.addRow("Montaje en el guest:", self.combo_mount)
        self.check_ro = QCheckBox("Solo lectura")
        layout.addRow("Acceso:", self.check_ro)
        info = QLabel("La política de montaje es la misma para todos los SO.")
        info.setWordWrap(True); info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if p: self.input_host.setText(p)

class Plugin(PluginBase):
    name = "ConfiguracionVM"
    version = "20.3.0"

    def __init__(self, app):
        super().__init__(app)
        self.current_vm_id = None
        self.host = HostProfile()
        self._network_data = []

    def get_tabs(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Nombre:</b>"))
        self.input_name = QLineEdit()
        self.input_name.setFixedWidth(150)
        top_bar.addWidget(self.input_name)

        top_bar.addWidget(QLabel("<b>Plataforma:</b>"))
        self.combo_platform = QComboBox()
        self.combo_platform.blockSignals(True)
        self.combo_platform.addItems(list(OS_CATALOG.keys()))
        self.combo_platform.blockSignals(False)
        self.combo_platform.currentIndexChanged.connect(self._on_platform_changed)
        top_bar.addWidget(self.combo_platform)

        self.lbl_so = QLabel("<b>SO:</b>")
        top_bar.addWidget(self.lbl_so)
        self.combo_so = QComboBox()
        self.combo_so.currentIndexChanged.connect(self._on_so_changed)
        top_bar.addWidget(self.combo_so)

        self.lbl_ver = QLabel("<b>Versión de SO:</b>")
        top_bar.addWidget(self.lbl_ver)
        self.combo_version = QComboBox()
        top_bar.addWidget(self.combo_version)

        top_bar.addWidget(QLabel("<b>Perfil:</b>"))
        self.combo_profile = QComboBox()
        self.combo_profile.addItem("Seleccionar perfil...", -1)
        profiles = get_vm_profiles()
        for i, prof in enumerate(profiles):
            self.combo_profile.addItem(f"{prof['icon']} {prof['name']}", i)
        self.combo_profile.currentIndexChanged.connect(self._on_profile_selected_from_combo)
        top_bar.addWidget(self.combo_profile)

        top_bar.addStretch()
        self.btn_save = QPushButton("💾 Guardar configuración")
        self.btn_save.setStyleSheet("background-color: #2e7d32; color: white; padding: 6px; font-weight: bold; border-radius: 4px;")
        self.btn_save.clicked.connect(self._save_config)
        self.btn_save.setEnabled(False)
        top_bar.addWidget(self.btn_save)
        main_layout.addLayout(top_bar)

        content = QHBoxLayout()
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sl = QVBoxLayout(sidebar)
        self.list_menu = QListWidget()
        self.list_menu.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { padding: 10px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #1e40af; color: white; }
        """)
        self.list_menu.currentRowChanged.connect(self._on_menu_changed)
        sl.addWidget(self.list_menu)
        content.addWidget(sidebar)

        right = QWidget()
        rl = QVBoxLayout(right)
        self.lbl_title = QLabel("Configuración VM")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        rl.addWidget(self.lbl_title)
        self.stack = QStackedWidget()
        rl.addWidget(self.stack)
        content.addWidget(right, 1)
        main_layout.addLayout(content, 1)

        self._build_pages()
        self._on_platform_changed(trigger_fetch=False)
        return [("Configuración VM", main_widget)]

    def _on_platform_changed(self, trigger_fetch=True):
        self.combo_so.blockSignals(True)
        self.combo_version.blockSignals(True)
        p = self.combo_platform.currentText()
        self.combo_so.clear()
        self.combo_version.clear()
        if p in OS_CATALOG:
            ordered_sos = sorted(list(OS_CATALOG[p].keys()), key=str.lower)
            self.combo_so.addItems(ordered_sos)
        self.combo_so.blockSignals(False)
        self.combo_version.blockSignals(False)
        self._on_so_changed(trigger_fetch)

    def _on_so_changed(self, trigger_fetch=True):
        p = self.combo_platform.currentText()
        so = self.combo_so.currentText()
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.setEnabled(False)
        self.lbl_ver.setToolTip("")
        if not so:
            self.combo_version.blockSignals(False)
            return
        static_versions = OS_CATALOG.get(p, {}).get(so, ["Automático"])
        self.combo_version.addItems(static_versions)
        self.combo_version.setEnabled(True)
        self.combo_version.blockSignals(False)

    def _on_profile_selected_from_combo(self, index):
        if index <= 0: return
        profiles = get_vm_profiles()
        prof = profiles[index - 1]
        
        ram_gb = max(1, prof["ram"] // 1024)
        self.slider_ram.setValue(ram_gb)
        
        cores = prof["cores"]
        if cores % 2 != 0: cores += 1
        self.slider_cores.setValue(cores)
        
        self.check_cpu_topology.setChecked(False)
        self.widget_topology.setVisible(False)
        
        self.combo_firmware.setCurrentIndex(prof["firmware_idx"])
        self.combo_chipset.setCurrentIndex(prof["chipset_idx"])
        self.combo_graphics.setCurrentIndex(prof["graphics_idx"])
        self.check_secure_boot.setChecked(prof["secure_boot"])
        self.check_tpm.setChecked(prof["tpm"])
        
        idx = self.combo_platform.findText(prof["platform"])
        if idx >= 0: self.combo_platform.setCurrentIndex(idx)
        self._on_platform_changed(True)
        idx = self.combo_so.findText(prof["os"])
        if idx >= 0: self.combo_so.setCurrentIndex(idx)
        self._on_so_changed(True)
        self.combo_profile.setCurrentIndex(0)
        QMessageBox.information(self.app.parent(), "Perfil aplicado", f"El perfil '{prof['name']}' ha sido aplicado.")

    def _build_pages(self):
        p1 = QWidget(); l1 = QVBoxLayout(p1)
        self.combo_firmware = QComboBox()
        self.combo_firmware.addItems(["BIOS (tradicional)", "UEFI (OVMF)"])
        l1.addWidget(QLabel("<b>Firmware</b>")); l1.addWidget(self.combo_firmware)
        self.combo_chipset = QComboBox()
        self.combo_chipset.addItems(["i440FX (clásico)", "Q35 (moderno, PCIe)"])
        l1.addWidget(QLabel("<b>Chipset</b>")); l1.addWidget(self.combo_chipset)
        sec_layout = QHBoxLayout()
        self.check_secure_boot = QCheckBox("Secure Boot")
        self.check_tpm = QCheckBox("TPM 2.0")
        sec_layout.addWidget(self.check_secure_boot); sec_layout.addWidget(self.check_tpm); sec_layout.addStretch()
        l1.addWidget(QLabel("<b>Seguridad</b>")); l1.addLayout(sec_layout); l1.addStretch()

        p2 = QWidget(); l2 = QVBoxLayout(p2)
        self.combo_cpu_type = QComboBox()
        self.combo_cpu_type.addItems(["Automático (recomendado)", "Host (máximo rendimiento)", "QEMU x86-64 (compatibilidad)", "Skylake-Client", "Haswell", "Broadwell", "SandyBridge", "Penryn"])
        l2.addWidget(QLabel("<b>Tipo de procesador</b>")); l2.addWidget(self.combo_cpu_type)
        
        self.slider_cores = QSlider(Qt.Orientation.Horizontal)
        self.slider_cores.setRange(2, 32)
        self.slider_cores.setSingleStep(2)
        self.slider_cores.setValue(2)
        self.slider_cores.setTickInterval(2)
        self.slider_cores.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.lbl_cores = QLabel("2 núcleos"); self.lbl_cores.setStyleSheet("font-weight: bold;")
        self.slider_cores.valueChanged.connect(self._update_cores_label)
        l2.addWidget(QLabel("<b>Núcleos lógicos (vCPU)</b>"))
        l2.addWidget(self.slider_cores)
        l2.addWidget(self.lbl_cores)
        
        self.check_cpu_topology = QCheckBox("Configurar la topología manualmente (sockets / cores / threads)")
        self.check_cpu_topology.toggled.connect(self._toggle_cpu_topology)
        l2.addWidget(self.check_cpu_topology)
        
        self.widget_topology = QWidget()
        topo_form = QFormLayout(self.widget_topology)
        topo_form.setContentsMargins(20, 0, 0, 0)
        
        self.spin_sockets = QSpinBox()
        self.spin_sockets.setRange(1, 4)
        self.spin_sockets.setValue(1)
        topo_form.addRow("Sockets:", self.spin_sockets)
        
        self.spin_cores_per_socket = QSpinBox()
        self.spin_cores_per_socket.setRange(1, 16)
        self.spin_cores_per_socket.setValue(2)
        topo_form.addRow("Cores por socket:", self.spin_cores_per_socket)
        
        self.spin_threads_per_core = QSpinBox()
        self.spin_threads_per_core.setRange(1, 2)
        self.spin_threads_per_core.setValue(1)
        topo_form.addRow("Threads por core:", self.spin_threads_per_core)
        
        self.lbl_topology_summary = QLabel("")
        self.lbl_topology_summary.setStyleSheet("color: #888; font-size: 11px;")
        topo_form.addRow("", self.lbl_topology_summary)
        
        self.spin_sockets.valueChanged.connect(self._update_topology_summary)
        self.spin_cores_per_socket.valueChanged.connect(self._update_topology_summary)
        self.spin_threads_per_core.valueChanged.connect(self._update_topology_summary)
        
        self.widget_topology.setVisible(False)
        l2.addWidget(self.widget_topology)
        
        self.check_nested_virt = QCheckBox("Virtualización anidada (VT-x / AMD-V)")
        self.check_hyperv = QCheckBox("Optimizaciones Hyper-V")
        l2.addWidget(self.check_nested_virt); l2.addWidget(self.check_hyperv)
        l2.addStretch()

        p3 = QWidget(); l3 = QVBoxLayout(p3)
        self.slider_ram = QSlider(Qt.Orientation.Horizontal)
        self.slider_ram.setRange(1, 128)
        self.slider_ram.setSingleStep(1)
        self.slider_ram.setValue(4)
        self.slider_ram.setTickInterval(4)
        self.slider_ram.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.lbl_ram = QLabel("4 GB"); self.lbl_ram.setStyleSheet("font-weight: bold;")
        self.slider_ram.valueChanged.connect(self._update_ram_label)
        l3.addWidget(QLabel("<b>RAM asignada (GB)</b>"))
        l3.addWidget(self.slider_ram)
        l3.addWidget(self.lbl_ram)
        self.check_hugepages = QCheckBox("Usar hugepages del host")
        self.check_prealloc = QCheckBox("Reservar toda la RAM al arrancar (prealloc)")
        self.check_memfd = QCheckBox("Bloquear la RAM de la VM (memfd-lock)")
        l3.addWidget(self.check_hugepages); l3.addWidget(self.check_prealloc); l3.addWidget(self.check_memfd)
        l3.addStretch()

        p4 = QWidget(); l4 = QVBoxLayout(p4)
        self.combo_graphics = QComboBox()
        self.combo_graphics.addItems(["Automático (recomendado) → VirtIO-GPU 2D", "VirtIO-GPU 2D (compatible)", "VirtIO-GPU + VirGL 3D", "VirtIO-GPU + Venus/Vulkan 3D", "Red Hat QXL 2D", "VMware SVGA II", "VGA estándar", "Sin video / Headless"])
        l4.addWidget(QLabel("<b>Gráficos / GPU</b>")); l4.addWidget(self.combo_graphics)
        self.combo_vram = QComboBox(); self.combo_vram.addItems(["64 MB", "128 MB", "256 MB", "512 MB"])
        l4.addWidget(QLabel("<b>Memoria de video</b>")); l4.addWidget(self.combo_vram)

        self.combo_console_proto = QComboBox()
        self.combo_console_proto.addItems(["VNC", "SPICE"])
        l4.addWidget(QLabel("<b>Protocolo de consola</b>"))
        l4.addWidget(self.combo_console_proto)

        self.combo_console_mode = QComboBox()
        self.combo_console_mode.addItems([
            "Embebida en la app",
            "Ventana externa",
            "Híbrida (VNC widget + SPICE externo)",
            "Pantalla completa",
        ])
        l4.addWidget(QLabel("<b>Modo de consola</b>"))
        l4.addWidget(self.combo_console_mode)

        lbl_hint = QLabel(
            "F11 alterna pantalla completa · Ctrl+Alt+F sale · Ctrl+Alt+G libera el teclado del guest.\n"
            "SPICE no se puede mostrar embebido en la app; si eliges SPICE se forzará ventana externa."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #888; font-size: 11px;")
        l4.addWidget(lbl_hint)
        l4.addStretch()

        p5 = QWidget(); l5 = QVBoxLayout(p5)
        self.tree_storage = QTreeWidget(); self.tree_storage.setHeaderLabels(["Dispositivo", "Bus", "Tipo / archivo", "Tamaño"])
        self.tree_storage.setColumnWidth(0, 150); self.tree_storage.setSortingEnabled(True)
        l5.addWidget(self.tree_storage)
        b5 = QHBoxLayout()
        for label, func in [("📀 CD/DVD", self._add_cd), ("💽 Disco Duro", self._add_hdd), ("💾 Disquete", self._add_floppy), ("✏ Modificar", self._modify_media), ("🗜 Compactar", self._compact_media), ("🗑 Eliminar", self._delete_media)]:
            btn = QPushButton(label); btn.clicked.connect(func); b5.addWidget(btn)
        b5.addStretch(); l5.addLayout(b5)
        l5.addWidget(QLabel("<b>Orden de arranque (drag & drop)</b>"))
        self.list_boot = QListWidget(); self.list_boot.setMaximumHeight(120); l5.addWidget(self.list_boot)
        b_boot = QHBoxLayout()
        up_btn = QPushButton("⬆ Subir"); dn_btn = QPushButton("⬇ Bajar")
        up_btn.clicked.connect(lambda: self._move_boot(-1)); dn_btn.clicked.connect(lambda: self._move_boot(1))
        b_boot.addWidget(up_btn); b_boot.addWidget(dn_btn); b_boot.addStretch(); l5.addLayout(b_boot); l5.addStretch()

        p6 = QWidget(); l6 = QVBoxLayout(p6)
        self.list_net = QListWidget()
        l6.addWidget(QLabel("<b>Adaptadores</b>")); l6.addWidget(self.list_net)
        b6 = QHBoxLayout()
        btn_net_add = QPushButton("➕ Agregar"); btn_net_edit = QPushButton("✏ Editar"); btn_net_del = QPushButton("🗑 Eliminar")
        btn_net_add.clicked.connect(self._add_net); btn_net_edit.clicked.connect(self._edit_net); btn_net_del.clicked.connect(self._del_net)
        b6.addWidget(btn_net_add); b6.addWidget(btn_net_edit); b6.addWidget(btn_net_del); b6.addStretch(); l6.addLayout(b6); l6.addStretch()

        p7 = QWidget(); l7 = QVBoxLayout(p7)
        self.combo_audio = QComboBox(); self.combo_audio.addItems(["Intel HDA (recomendado)", "AC97", "Sound Blaster", "Ninguno"])
        self.combo_pointer = QComboBox(); self.combo_pointer.addItems(["Automático (recomendado)", "USB Tablet", "USB Mouse", "USB Keyboard + Tablet", "VirtIO Tablet", "PS/2", "Ninguno"])
        l7.addWidget(QLabel("<b>Audio</b>")); l7.addWidget(self.combo_audio)
        l7.addWidget(QLabel("<b>Señalización</b>")); l7.addWidget(self.combo_pointer)
        l7.addStretch()

        p8 = QWidget(); l8 = QVBoxLayout(p8)
        info_pt = QLabel("Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI.")
        info_pt.setStyleSheet("color: #888; font-size: 11px;"); info_pt.setWordWrap(True)
        l8.addWidget(info_pt)
        self.tree_passthrough = QTreeWidget()
        self.tree_passthrough.setHeaderLabels(["Usar", "Tipo", "Dispositivo", "IOMMU / Driver", "Estado"])
        l8.addWidget(self.tree_passthrough)
        b8 = QHBoxLayout()
        btn_pt_detect = QPushButton("🔍 Detectar dispositivos")
        btn_pt_detect.clicked.connect(self._detect_passthrough)
        b8.addWidget(btn_pt_detect); b8.addStretch(); l8.addLayout(b8); l8.addStretch()

        p9 = QWidget(); l9 = QVBoxLayout(p9)
        info_sh = QLabel("Integración Host ↔ Guest.")
        info_sh.setWordWrap(True); info_sh.setStyleSheet("color: #888; font-size: 11px;")
        l9.addWidget(info_sh)
        self.tabs_sharing = QTabWidget()
        tab_folders = QWidget(); lf = QVBoxLayout(tab_folders)
        self.tree_shared = QTreeWidget()
        self.tree_shared.setHeaderLabels(["Host", "Guest / etiqueta", "Método", "Montaje", "Acceso"])
        lf.addWidget(self.tree_shared)
        bf = QHBoxLayout()
        btn_sh_add = QPushButton("➕ Agregar"); btn_sh_mod = QPushButton("✏ Modificar"); btn_sh_del = QPushButton("🗑 Eliminar")
        btn_sh_add.clicked.connect(self._add_shared); btn_sh_mod.clicked.connect(self._mod_shared); btn_sh_del.clicked.connect(self._del_shared)
        for b in (btn_sh_add, btn_sh_mod, btn_sh_del): bf.addWidget(b)
        bf.addStretch(); lf.addLayout(bf)
        self.tabs_sharing.addTab(tab_folders, "Compartir Carpetas")
        tab_tools = QWidget(); lt = QVBoxLayout(tab_tools)
        group_ga = QGroupBox("QEMU Guest Agent")
        lg = QFormLayout(group_ga)
        self.check_ga = QCheckBox("Activar canal QEMU Guest Agent al iniciar la VM")
        lg.addRow("Canal:", self.check_ga)
        lt.addWidget(group_ga); lt.addStretch()
        self.tabs_sharing.addTab(tab_tools, "Guest Tools")
        tab_clip = QWidget(); lc = QVBoxLayout(tab_clip)
        group_clip = QGroupBox("Compartir clipboard")
        lcl = QFormLayout(group_clip)
        self.combo_clipboard = QComboBox(); self.combo_clipboard.addItems(["Desactivado", "Host → SO invitado", "SO invitado → Host", "Bidireccional"])
        lcl.addRow("Dirección:", self.combo_clipboard)
        lc.addWidget(group_clip); lc.addStretch()
        self.tabs_sharing.addTab(tab_clip, "Clipboard")
        l9.addWidget(self.tabs_sharing)

        pages = [("🖥️ Sistema", p1), ("⚙️ Procesador", p2), ("🧠 Memoria", p3), ("🖼️ Pantalla", p4), ("💾 Almacenamiento", p5), ("🌐 Red", p6), ("🎛️ Dispositivos", p7), ("🔌 Passthrough", p8), ("📂 Compartición", p9)]
        for name, w in pages:
            self.list_menu.addItem(QListWidgetItem(name))
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(w)
            self.stack.addWidget(scroll)

    def _update_cores_label(self, val): self.lbl_cores.setText(f"{val} núcleos")
    def _update_ram_label(self, val): self.lbl_ram.setText(f"{val} GB")

    def _toggle_cpu_topology(self, checked):
        self.widget_topology.setVisible(checked)
        if not checked:
            total = self.spin_sockets.value() * self.spin_cores_per_socket.value() * self.spin_threads_per_core.value()
            if 2 <= total <= 32 and total % 2 == 0:
                self.slider_cores.setValue(total)
        else:
            self._update_topology_summary()

    def _update_topology_summary(self):
        s = self.spin_sockets.value()
        c = self.spin_cores_per_socket.value()
        t = self.spin_threads_per_core.value()
        total = s * c * t
        self.lbl_topology_summary.setText(f"Total vCPUs: {total} ({s} sockets × {c} cores × {t} threads)")
        if 2 <= total <= 32 and total % 2 == 0:
            self.slider_cores.blockSignals(True)
            self.slider_cores.setValue(total)
            self.slider_cores.blockSignals(False)

    def _add_cd(self):
        dlg = CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir, app=self.app)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            source_type = dlg.combo_source.currentText()
            item.setText(0, "Unidad óptica"); item.setText(1, "CD/DVD")
            item.setText(2, dlg.input_file.text() if source_type == "Usar ISO/IMG/DMG existente" else ("Descargar automáticamente" if source_type == "Descargar" else "Vacío"))
            item.setText(3, dlg.combo_bus.currentText())
            item.setData(2, Qt.ItemDataRole.UserRole, source_type)
            item.setData(3, Qt.ItemDataRole.UserRole, dlg.combo_bus.currentText())
            self._sync_boot()

    def _add_hdd(self):
        vm_dir = self.app.vms_dir / self.current_vm_id if self.current_vm_id else self.app.vms_dir
        dlg = DiskDialog(self.app.parent(), default_dir=vm_dir, app=self.app)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            item.setText(0, "Disco Duro"); item.setText(1, dlg.combo_bus.currentText())
            if dlg.radio_new.isChecked():
                item.setText(2, dlg.input_path.text())
                item.setText(3, dlg.input_size.text())
                item.setData(2, Qt.ItemDataRole.UserRole, "NEW")
                item.setData(2, Qt.ItemDataRole.UserRole + 1, dlg.combo_format.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 2, dlg.combo_type.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 3, dlg.combo_cache.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 4, dlg.combo_io.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 5, dlg.combo_discard.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 6, dlg.combo_detect_zeros.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 7, dlg.combo_aio.currentText())
            else:
                item.setText(2, dlg.input_file.text()); item.setText(3, "-")
                item.setData(2, Qt.ItemDataRole.UserRole, "EXISTING")
            item.setData(2, Qt.ItemDataRole.UserRole + 8, dlg.combo_bus.currentText())
            self._sync_boot()

    def _add_floppy(self):
        dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir, app=self.app)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            item.setText(0, "Disquetera"); item.setText(1, "FDC")
            if dlg.radio_new.isChecked():
                item.setText(2, dlg.input_name.text()); item.setText(3, dlg.combo_size.currentText())
            else:
                item.setText(2, dlg.input_file.text()); item.setText(3, "-")
            self._sync_boot()

    def _modify_media(self):
        item = self.tree_storage.currentItem()
        if not item: return
        if item.text(0) == "Disco Duro":
            disk_data = {
                "name": os.path.basename(item.text(2)),
                "path": item.text(2),
                "size": item.text(3),
                "format": item.data(2, Qt.ItemDataRole.UserRole + 1),
                "type": item.data(2, Qt.ItemDataRole.UserRole + 2),
                "bus": item.data(2, Qt.ItemDataRole.UserRole + 8) or item.text(1)
            }
            dlg = DiskDialog(self.app.parent(), disk_data, default_dir=self.app.vms_dir, app=self.app)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                item.setText(1, dlg.combo_bus.currentText())
                item.setText(2, dlg.input_path.text() or dlg.input_file.text())
                item.setText(3, dlg.input_size.text())
                item.setData(2, Qt.ItemDataRole.UserRole + 1, dlg.combo_format.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 2, dlg.combo_type.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 3, dlg.combo_cache.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 4, dlg.combo_io.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 5, dlg.combo_discard.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 6, dlg.combo_detect_zeros.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 7, dlg.combo_aio.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole + 8, dlg.combo_bus.currentText())
                self._sync_boot()
        elif item.text(0) == "Unidad óptica":
            source_type = item.data(2, Qt.ItemDataRole.UserRole)
            cd_data = {
                "path": item.text(2),
                "bus": item.data(3, Qt.ItemDataRole.UserRole + 1) or item.text(3)
            }
            dlg = CDDVDDialog(self.app.parent(), cd_data, default_dir=self.app.isos_dir, app=self.app)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                source_type = dlg.combo_source.currentText()
                item.setText(2, dlg.input_file.text() if source_type == "Usar ISO/IMG/DMG existente" else ("Descargar automáticamente" if source_type == "Descargar" else "Vacío"))
                item.setText(3, dlg.combo_bus.currentText())
                item.setData(2, Qt.ItemDataRole.UserRole, source_type)
                item.setData(3, Qt.ItemDataRole.UserRole + 1, dlg.combo_bus.currentText())
                self._sync_boot()
    def _compact_media(self): QMessageBox.information(self.app.parent(), "Compactar", "Función en desarrollo.")
    def _delete_media(self):
        item = self.tree_storage.currentItem()
        if item:
            self.tree_storage.takeTopLevelItem(self.tree_storage.indexOfTopLevelItem(item))
            self._sync_boot()

    def _sync_boot(self):
        self.list_boot.clear()
        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            self.list_boot.addItem(f"{item.text(0)} — {item.text(2)}")
        self.list_boot.addItem("Red/PXE")

    def _move_boot(self, d):
        r = self.list_boot.currentRow()
        if r >= 0 and 0 <= r + d < self.list_boot.count():
            it = self.list_boot.takeItem(r); self.list_boot.insertItem(r + d, it); self.list_boot.setCurrentRow(r + d)

    def _rebuild_net_list(self):
        self.list_net.clear()
        for net in self._network_data:
            extra = ""
            if net.get("backend") != "NAT / Internet" and net.get("bridge"): extra = f" [{net['bridge']}]"
            elif net.get("nat_rules"): extra = f" ({len(net['nat_rules'])} reglas NAT)"
            if net.get("mac"): extra += f" MAC:{net['mac']}"
            self.list_net.addItem(f"{net.get('name', 'Red')} — {net.get('model', 'VirtIO')} — {net.get('backend', 'NAT / Internet')}{extra}")

    def _add_net(self):
        dlg = NetworkAdapterDialog(self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._network_data.append(dlg.get_data())
            self._rebuild_net_list()

    def _edit_net(self):
        idx = self.list_net.currentRow()
        if idx < 0 or idx >= len(self._network_data): return
        dlg = NetworkAdapterDialog(self.app.parent(), self._network_data[idx])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._network_data[idx] = dlg.get_data()
            self._rebuild_net_list()

    def _del_net(self):
        idx = self.list_net.currentRow()
        if idx >= 0 and idx < len(self._network_data):
            del self._network_data[idx]
            self._rebuild_net_list()

    def _add_shared(self):
        dlg = SharedFolderDialog(self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_shared)
            item.setText(0, dlg.input_host.text()); item.setText(1, dlg.input_label.text()); item.setText(2, dlg.combo_method.currentText()); item.setText(3, dlg.combo_mount.currentText()); item.setText(4, "Solo lectura" if dlg.check_ro.isChecked() else "Lectura/Escritura")

    def _mod_shared(self):
        item = self.tree_shared.currentItem()
        if item:
            dlg = SharedFolderDialog(self.app.parent(), {"host": item.text(0)})
            if dlg.exec() == QDialog.DialogCode.Accepted:
                item.setText(0, dlg.input_host.text()); item.setText(1, dlg.input_label.text()); item.setText(2, dlg.combo_method.currentText()); item.setText(3, dlg.combo_mount.currentText()); item.setText(4, "Solo lectura" if dlg.check_ro.isChecked() else "Lectura/Escritura")

    def _del_shared(self):
        item = self.tree_shared.currentItem()
        if item: self.tree_shared.takeTopLevelItem(self.tree_shared.indexOfTopLevelItem(item))

    def _detect_passthrough(self):
        self.tree_passthrough.clear()
        for d in (scan_pci_devices() + scan_usb_devices()):
            item = QTreeWidgetItem(self.tree_passthrough)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setText(1, d["type"])
            item.setText(2, d["desc"])
            item.setText(3, d.get("iommu", "N/A"))
            item.setText(4, d.get("status", ""))
            item.setData(2, Qt.ItemDataRole.UserRole, d)

    def _on_menu_changed(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
            self.lbl_title.setText(self.list_menu.item(index).text().split(" ", 1)[-1])

    def on_vm_selected(self, vm_id: str):
        if not vm_id: return
        self.current_vm_id = vm_id
        vm = self.app.get_vm(vm_id)
        if not vm: return
        self.btn_save.setEnabled(True)

        self.input_name.setText(vm.get("name", ""))
        idx = self.combo_platform.findText(vm.get("platform", "GNU / Linux"))
        if idx >= 0: self.combo_platform.setCurrentIndex(idx)
        self._on_platform_changed(False)
        idx = self.combo_so.findText(vm.get("so", ""))
        if idx >= 0: self.combo_so.setCurrentIndex(idx)
        self._on_so_changed(False)

        self.combo_firmware.setCurrentIndex(vm.get("firmware_idx", 0))
        self.combo_chipset.setCurrentIndex(vm.get("chipset_idx", 0))
        self.check_secure_boot.setChecked(vm.get("secure_boot", False))
        self.check_tpm.setChecked(vm.get("tpm", False))
        self.combo_cpu_type.setCurrentIndex(vm.get("cpu_type_idx", 0))
        
        cores = vm.get("cores", 2)
        if cores % 2 != 0: cores += 1
        self.slider_cores.setValue(cores)
        
        topo = vm.get("cpu_topology", False)
        self.check_cpu_topology.setChecked(topo)
        self.widget_topology.setVisible(topo)
        self.spin_sockets.setValue(vm.get("cpu_sockets", 1))
        self.spin_cores_per_socket.setValue(vm.get("cpu_cores_per_socket", vm.get("cores", 2)))
        self.spin_threads_per_core.setValue(vm.get("cpu_threads_per_core", 1))
        self._update_topology_summary()
        
        self.check_nested_virt.setChecked(vm.get("nested_virt", False))
        self.check_hyperv.setChecked(vm.get("hyperv", False))
        
        ram_mb = vm.get("ram", 4096)
        ram_gb = max(1, ram_mb // 1024)
        self.slider_ram.setValue(ram_gb)
        
        self.check_hugepages.setChecked(vm.get("hugepages", False))
        self.check_prealloc.setChecked(vm.get("prealloc", False))
        self.check_memfd.setChecked(vm.get("memfd", False))
        self.combo_graphics.setCurrentIndex(vm.get("graphics_idx", 0))
        self.combo_vram.setCurrentIndex(vm.get("vram_idx", 0))
        self.combo_console_proto.setCurrentIndex(vm.get("console_proto_idx", 0))
        self.combo_console_mode.setCurrentIndex(vm.get("console_mode_idx", 0))

        self._network_data = []
        for net in vm.get("network_adapters", []):
            self._network_data.append({
                "name": net.get("name", "Red"),
                "model": net.get("model", "VirtIO"),
                "backend": net.get("backend", "NAT / Internet"),
                "bridge": net.get("bridge", ""),
                "mac": net.get("mac", ""),
                "nat_rules": net.get("nat_rules", []),
            })
        self._rebuild_net_list()

        self.combo_audio.setCurrentText(vm.get("audio", "Intel HDA (recomendado)"))
        self.combo_pointer.setCurrentText(vm.get("pointer", "Automático (recomendado)"))

        self.tree_storage.clear()
        if vm.get("disk_path"):
            it = QTreeWidgetItem(self.tree_storage)
            it.setText(0, "Disco Duro")
            bus_type = vm.get("disk_bus", "sata").lower()
            if "virtio" in bus_type: it.setText(1, "VirtIO-BLK")
            elif "nvme" in bus_type: it.setText(1, "NVMe")
            else: it.setText(1, "SATA/AHCI")
            it.setText(2, vm["disk_path"])
            it.setText(3, vm.get("disk_size", "20G"))
            
        if vm.get("iso_source_type") == "Descargar" or vm.get("iso_path"):
            it = QTreeWidgetItem(self.tree_storage)
            it.setText(0, "Unidad óptica")
            it.setText(1, "CD/DVD")
            it.setText(2, vm.get("iso_path", "Descargar automáticamente"))
            it.setText(3, vm.get("cdrom_bus", "SATA/AHCI"))
            it.setData(3, Qt.ItemDataRole.UserRole, vm.get("cdrom_bus", "SATA/AHCI"))
            it.setData(2, Qt.ItemDataRole.UserRole, vm.get("iso_source_type", "Usar ISO/IMG/DMG existente"))
            
        if vm.get("floppy_path"):
            it = QTreeWidgetItem(self.tree_storage)
            it.setText(0, "Disquetera"); it.setText(1, "FDC")
            it.setText(2, vm["floppy_path"]); it.setText(3, "-")
        
        self._sync_boot()
        
        boot_order = vm.get("boot_order")
        if boot_order:
            self.list_boot.clear()
            for entry in boot_order:
                self.list_boot.addItem(entry)

        self.tree_shared.clear()
        for sh in vm.get("shared_folders", []):
            item = QTreeWidgetItem(self.tree_shared)
            item.setText(0, sh.get("host", "")); item.setText(1, sh.get("guest", "")); item.setText(2, sh.get("method", "Automático")); item.setText(3, sh.get("mount", "Manual")); item.setText(4, "Solo lectura" if sh.get("ro") else "Lectura/Escritura")

        self.combo_clipboard.setCurrentText(vm.get("clipboard", "Desactivado"))
        self.check_ga.setChecked(vm.get("guest_agent", False))

        self._detect_passthrough()
        saved_pt = vm.get("passthrough_devices", [])
        if saved_pt:
            for i in range(self.tree_passthrough.topLevelItemCount()):
                item = self.tree_passthrough.topLevelItem(i)
                d = item.data(2, Qt.ItemDataRole.UserRole) or {}
                dev_id = d.get("id", "")
                vid_did = d.get("vid_did", "")
                for saved in saved_pt:
                    if saved.get("id") == dev_id:
                        item.setCheckState(0, Qt.CheckState.Checked)
                        break
                    if vid_did and saved.get("vid_did") == vid_did:
                        item.setCheckState(0, Qt.CheckState.Checked)
                        break
                    if vid_did and saved.get("id") == vid_did:
                        item.setCheckState(0, Qt.CheckState.Checked)
                        break

    def _download_iso_sync(self):
        platform = self.combo_platform.currentText()
        so = self.combo_so.currentText()
        ver_id = self.combo_version.currentData() or self.combo_version.currentText()
        
        url = None
        try:
            if so in ["Windows 10", "Windows 11"]: url = iso_sources.get_latest_windows_iso_url(so)
            elif iso_versions.supports_versions(so): url = iso_versions.get_iso_url(so, ver_id)
            elif iso_sources.supports_auto_download(so): url = iso_sources.get_latest_iso_url(so)
            else: 
                QMessageBox.warning(self.app.parent(), "Descarga no soportada", f"La descarga automática no está disponible para {so}.")
                return None
        except Exception as e: 
            QMessageBox.critical(self.app.parent(), "Error de descarga", f"No se pudo obtener la URL: {e}")
            return None
            
        if not url: return None
        
        iso_dir = self.app.data_dir / "isos"
        iso_dir.mkdir(exist_ok=True)
        
        parsed = urlparse(url)
        path_segments = [s for s in parsed.path.split("/") if s]
        if path_segments and path_segments[-1] == "download": 
            filename = path_segments[-2] if len(path_segments) >= 2 else "imagen.iso"
        else: 
            filename = path_segments[-1] if path_segments else "imagen.iso"
            
        filename = unquote(filename)
        if not filename.lower().endswith((".iso", ".img", ".dmg")): filename += ".iso"
        
        dest_path = iso_dir / filename
        
        if dest_path.exists() and dest_path.stat().st_size > 5000000:
            resp = QMessageBox.question(self.app.parent(), "ISO existente", f"La ISO '{filename}' ya existe en la biblioteca.\n\n¿Deseas usar esa ISO o descargarla de nuevo?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if resp == QMessageBox.StandardButton.Yes: return str(dest_path)
            else: dest_path.unlink()
        
        thread = DownloadISOThread(url, str(dest_path))
        loop = QEventLoop()
        result = {"path": None, "error": None}
        
        progress = QProgressDialog(f"Descargando {filename}...", "Cancelar", 0, 100, self.app.parent())
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        def on_progress(pct, text):
            if pct > 0: 
                progress.setRange(0, 100); progress.setValue(pct)
            else: 
                progress.setRange(0, 0)
            if "\n" in text: 
                parts = text.split("\n"); progress.setWindowTitle(parts[0]); progress.setLabelText(parts[1])
            else: 
                progress.setWindowTitle(text); progress.setLabelText("")
                
        def on_finish(path): 
            result["path"] = path; progress.close(); loop.quit()
            
        def on_err(err): 
            result["error"] = err; progress.close(); loop.quit()
            
        def on_cancel(): 
            thread.stop(); thread.wait(); loop.quit()
            
        thread.progress.connect(on_progress)
        thread.finished_ok.connect(on_finish)
        thread.error.connect(on_err)
        progress.canceled.connect(on_cancel)
        
        thread.start()
        loop.exec()
        
        if result["error"]: 
            QMessageBox.critical(self.app.parent(), "Error", f"Fallo al descargar: {result['error']}")
            return None
            
        return result["path"]

    def _save_config(self):
        if not self.current_vm_id: return

        proto_idx = self.combo_console_proto.currentIndex()
        mode_idx = self.combo_console_mode.currentIndex()
        if proto_idx == 1 and mode_idx in (0, 3):
            QMessageBox.warning(
                self.app.parent(),
                "Modo no soportado",
                "SPICE no puede mostrarse embebido ni en pantalla completa dentro de la app.\n\n"
                "Se cambiará automáticamente a 'Ventana externa'.\n"
                "Se intentará lanzar remote-viewer → virt-viewer → spicy, "
                "en ese orden, al arrancar la VM."
            )
            self.combo_console_mode.setCurrentIndex(1)
            mode_idx = 1

        if proto_idx == 0 and mode_idx == 2:
            log.info("Modo Híbrida con protocolo VNC: se tratará como Embebida.")

        shared_folders = []
        for i in range(self.tree_shared.topLevelItemCount()):
            item = self.tree_shared.topLevelItem(i)
            shared_folders.append({"host": item.text(0), "guest": item.text(1), "method": item.text(2), "mount": item.text(3), "ro": item.text(4) == "Solo lectura"})

        # Auto-seleccionar audio de la GPU si se ha marcado una
        checked_vga_groups = set()
        for i in range(self.tree_passthrough.topLevelItemCount()):
            item = self.tree_passthrough.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                d = item.data(2, Qt.ItemDataRole.UserRole) or {}
                if d.get("type") == "PCI" and d.get("is_vga"):
                    iommu_str = d.get("iommu", "")
                    if "Grupo" in iommu_str:
                        checked_vga_groups.add(iommu_str)

        for i in range(self.tree_passthrough.topLevelItemCount()):
            item = self.tree_passthrough.topLevelItem(i)
            d = item.data(2, Qt.ItemDataRole.UserRole) or {}
            
            if item.checkState(0) != Qt.CheckState.Checked:
                if d.get("type") == "PCI" and d.get("is_audio"):
                    if any(d.get("iommu") == grp for grp in checked_vga_groups):
                        item.setCheckState(0, Qt.CheckState.Checked)
                        log.info(f"Auto-seleccionando dispositivo de audio {d.get('id')} para GPU passthrough.")

        pt_devices = []
        for i in range(self.tree_passthrough.topLevelItemCount()):
            item = self.tree_passthrough.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                d = item.data(2, Qt.ItemDataRole.UserRole) or {}
                pt_devices.append({
                    "type": d.get("type", item.text(1)),
                    "id": d.get("id", ""),
                    "desc": d.get("desc", item.text(2)),
                    "vid_did": d.get("vid_did", ""),
                    "is_vga": d.get("is_vga", False),
                })
        
        for d in pt_devices:
            if d["type"] == "PCI" and d.get("vid_did"):
                host_passthrough.add_pci_udev_rule(d["vid_did"])

        boot_order = []
        for i in range(self.list_boot.count()):
            boot_order.append(self.list_boot.item(i).text())

        ram_gb = self.slider_ram.value()
        ram_mb = ram_gb * 1024
        
        cpu_topology = self.check_cpu_topology.isChecked()
        sockets = self.spin_sockets.value()
        cores_per_socket = self.spin_cores_per_socket.value()
        threads_per_core = self.spin_threads_per_core.value()
        
        if cpu_topology:
            total_cores = sockets * cores_per_socket * threads_per_core
        else:
            total_cores = self.slider_cores.value()
        
        data = {
            "name": self.input_name.text(),
            "platform": self.combo_platform.currentText(),
            "so": self.combo_so.currentText(),
            "version": self.combo_version.currentText(),
            "version_id": self.combo_version.currentData() or "",
            "firmware_idx": self.combo_firmware.currentIndex(),
            "chipset_idx": self.combo_chipset.currentIndex(),
            "secure_boot": self.check_secure_boot.isChecked(),
            "tpm": self.check_tpm.isChecked(),
            "cpu_type_idx": self.combo_cpu_type.currentIndex(),
            "cores": total_cores,
            "cpu_topology": cpu_topology,
            "cpu_sockets": sockets,
            "cpu_cores_per_socket": cores_per_socket,
            "cpu_threads_per_core": threads_per_core,
            "nested_virt": self.check_nested_virt.isChecked(),
            "hyperv": self.check_hyperv.isChecked(),
            "ram": ram_mb,
            "hugepages": self.check_hugepages.isChecked(),
            "prealloc": self.check_prealloc.isChecked(),
            "memfd": self.check_memfd.isChecked(),
            "graphics_idx": self.combo_graphics.currentIndex(),
            "vram_idx": self.combo_vram.currentIndex(),
            "console_proto_idx": self.combo_console_proto.currentIndex(),
            "console_mode_idx": self.combo_console_mode.currentIndex(),
            "shared_folders": shared_folders,
            "clipboard": self.combo_clipboard.currentText(),
            "guest_agent": self.check_ga.isChecked(),
            "passthrough_devices": pt_devices,
            "network_adapters": self._network_data,
            "audio": self.combo_audio.currentText(),
            "pointer": self.combo_pointer.currentText(),
            "boot_order": boot_order,
            "disk_path": None, "iso_path": None, "floppy_path": None,
            "disk_bus": "sata"
        }

        current_vm = self.app.get_vm(self.current_vm_id)
        existing_iso = current_vm.get("iso_path") if current_vm else None

        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            if item.text(0) == "Disco Duro":
                path = item.text(2)
                bus_text = item.text(1).lower()
                if "virtio-blk" in bus_text: data["disk_bus"] = "virtio"
                elif "virtio-scsi" in bus_text: data["disk_bus"] = "virtio-scsi"
                elif "nvme" in bus_text: data["disk_bus"] = "nvme"
                elif "scsi" in bus_text: data["disk_bus"] = "scsi"
                elif "ide" in bus_text: data["disk_bus"] = "ide"
                else: data["disk_bus"] = "sata"

                if path:
                    if not os.path.exists(path):
                        try:
                            ext = os.path.splitext(path)[1].lower()
                            fmt = {"img":"raw", "vdi":"vdi", "vmdk":"vmdk", "vhd":"vpc", "vhdx":"vhdx"}.get(ext, "qcow2")
                            data["disk_format"] = fmt
                            data["disk_cache"] = item.data(2, Qt.ItemDataRole.UserRole + 3) or "Automático (writeback)"
                            data["disk_io"] = item.data(2, Qt.ItemDataRole.UserRole + 4) or "Automático (threads)"
                            data["disk_discard"] = item.data(2, Qt.ItemDataRole.UserRole + 5) or "Automático (ignore)"
                            data["disk_detect_zeros"] = item.data(2, Qt.ItemDataRole.UserRole + 6) or "Automático (off)"
                            data["disk_aio"] = item.data(2, Qt.ItemDataRole.UserRole + 7) or "Automático (threads)"
                            
                            size_str = item.text(3) or "20G"
                            disk_type = item.data(2, Qt.ItemDataRole.UserRole + 2) or "Expandible (dinámico)"
                            is_fixed = "Fijo" in disk_type
                            
                            cmd = ["qemu-img", "create", "-f", fmt]
                            if is_fixed:
                                if fmt in ["vpc", "vhdx"]: cmd.extend(["-o", "subformat=fixed"])
                                elif fmt == "qcow2": cmd.extend(["-o", "preallocation=full"])
                            cmd.extend([path, size_str])
                            
                            progress = QProgressDialog("Creando disco...", None, 0, 0, self.app.parent())
                            progress.setWindowModality(Qt.WindowModality.WindowModal)
                            progress.setCancelButton(None)
                            progress.show()
                            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
                            while process.poll() is None:
                                QApplication.processEvents(); time.sleep(0.1)
                            progress.close()
                            if process.returncode != 0:
                                raise Exception(process.stderr.read())
                                
                            data["disk_path"] = path
                            data["disk_size"] = size_str
                        except Exception as e:
                            QMessageBox.critical(self.app.parent(), "Error", f"No se pudo crear el disco: {e}")
                            return
                    else:
                        ext = os.path.splitext(path)[1].lower()
                        data["disk_format"] = {"img":"raw", "vdi":"vdi", "vmdk":"vmdk", "vhd":"vpc", "vhdx":"vhdx"}.get(ext, "qcow2")
                        data["disk_size"] = item.text(3) if item.text(3) != "-" else "20G"
                        data["disk_cache"] = item.data(2, Qt.ItemDataRole.UserRole + 3) or "Automático (writeback)"
                        data["disk_io"] = item.data(2, Qt.ItemDataRole.UserRole + 4) or "Automático (threads)"
                        data["disk_discard"] = item.data(2, Qt.ItemDataRole.UserRole + 5) or "Automático (ignore)"
                        data["disk_detect_zeros"] = item.data(2, Qt.ItemDataRole.UserRole + 6) or "Automático (off)"
                        data["disk_aio"] = item.data(2, Qt.ItemDataRole.UserRole + 7) or "Automático (threads)"
                        
                        vm_dir = self.app.vms_dir / self.current_vm_id
                        vm_dir.mkdir(parents=True, exist_ok=True)
                        
                        if not str(path).startswith(str(vm_dir)):
                            resp = QMessageBox.question(self.app.parent(), "Disco externo",
                                f"El disco está fuera de la carpeta de la VM.\n¿Copiarlo a la carpeta?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
                            if resp == QMessageBox.StandardButton.Cancel: return
                            elif resp == QMessageBox.StandardButton.Yes:
                                new_path = vm_dir / os.path.basename(path)
                                if not new_path.exists(): shutil.copy2(path, new_path)
                                data["disk_path"] = str(new_path)
                                item.setText(2, str(new_path))
                            else:
                                data["disk_path"] = path
                        else:
                            data["disk_path"] = path
            elif item.text(0) == "Unidad óptica":
                source_type = item.data(2, Qt.ItemDataRole.UserRole)
                data["iso_source_type"] = source_type
                bus_text = (item.data(3, Qt.ItemDataRole.UserRole + 1) or item.text(3) or "SATA").lower()
                if "ide" in bus_text: data["cdrom_bus"] = "ide"
                elif "scsi" in bus_text: data["cdrom_bus"] = "scsi"
                elif "usb" in bus_text: data["cdrom_bus"] = "usb"
                else: data["cdrom_bus"] = "sata"
                if source_type == "Descargar":
                    if existing_iso and os.path.exists(existing_iso) and os.path.getsize(existing_iso) > 5000000:
                        data["iso_path"] = existing_iso
                    else:
                        downloaded_path = self._download_iso_sync()
                        if downloaded_path:
                            data["iso_path"] = downloaded_path
                            item.setText(2, downloaded_path)
                        else:
                            return
                elif item.text(2) and os.path.exists(item.text(2)):
                    data["iso_path"] = item.text(2)
            elif item.text(0) == "Disquetera":
                if item.text(2):
                    data["floppy_path"] = item.text(2)

        self.app.vm_repo.update(self.current_vm_id, data)
        QMessageBox.information(self.app.parent(), "Guardado", "Configuración guardada.")