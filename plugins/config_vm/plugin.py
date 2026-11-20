import uuid
import os
import platform
import sys
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
    QApplication, QProgressDialog, QAbstractItemView
)
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEventLoop
from core.plugin_base import PluginBase
from core.i18n import original_key, tr
from services.host_profile import HostProfile
from services.vm_profiles import get_vm_profiles
from services.os_catalog import OS_CATALOG
from services import iso_versions
from services import iso_sources
from services import host_passthrough
from services.download_utils import HashTracker, save_checksum
from ui_widgets.media_library_dialog import MediaLibraryDialog

IS_WINDOWS = platform.system() == "Windows"

# Claves estables para el tipo de dispositivo. El texto visible se traduce,
# pero la lógica nunca debe comparar textos traducidos.
TIPO_DISCO = "Disco Duro"
TIPO_OPTICO = "Unidad óptica"
TIPO_DISQUETE = "Disquetera"

# Orígenes canónicos de una unidad óptica (se guardan siempre en español).
SOURCE_EMPTY = "Mantener vacío"
SOURCE_EXISTING = "Usar ISO/IMG/DMG existente"
SOURCE_DOWNLOAD = "Descargar"


def _combo_value(combo):
    """Valor estable de un combo, aunque su texto esté traducido."""
    dato = combo.currentData()
    if isinstance(dato, str) and dato:
        return dato
    return original_key(combo.currentText())


def _set_combo_value(combo, value):
    """Selecciona un valor canónico en un combo traducido."""
    if not value:
        return
    indice = combo.findData(value)
    if indice < 0:
        indice = combo.findText(tr(value))
    if indice >= 0:
        combo.setCurrentIndex(indice)


log = logging.getLogger(__name__)


class DownloadISOThread(QThread):
    progress = pyqtSignal(int, str)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path, expected_sha256=None):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self._is_cancelled = False
        self.sha256 = ""
        self._tracker = HashTracker("sha256", expected_sha256)

    def stop(self):
        self._is_cancelled = True

    def run(self):
        part_path = None
        try:
            dest_path = Path(self.dest_path)
            part_path = Path(str(dest_path) + ".part")

            if part_path.exists(): part_path.unlink()
            if dest_path.exists(): dest_path.unlink()

            filename = dest_path.name
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            session = requests.Session()
            session.headers.update(headers)

            real_url = self.url
            try:
                r = session.get(self.url, stream=True, timeout=(10, 30))
                if "text/html" in r.headers.get("Content-Type", ""):
                    html = r.text
                    match = re.search(r'url=(https?://[^"\']+)', html) or re.search(r'(https://downloads\.sourceforge\.net/[^"\']+)', html)
                    if match: real_url = match.group(1)
                else:
                    real_url = r.url
                r.close()
            except: pass

            response = session.get(real_url, stream=True, timeout=(15, 60))
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))

            if total > 0 and total < 5000000:
                raise Exception(f"El archivo es demasiado pequeño ({total} bytes). Probablemente sea un HTML de error.")

            downloaded = 0
            start_time = time.time()
            last_update_time = start_time

            with open(part_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if self._is_cancelled:
                        f.close()
                        part_path.unlink(missing_ok=True)
                        return
                    if chunk:
                        f.write(chunk)
                        self._tracker.update(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update_time > 0.5:
                            elapsed = now - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            mb_dl = downloaded / (1024 * 1024)
                            speed_mb = speed / (1024 * 1024)

                            if total > 0:
                                mb_total = total / (1024 * 1024)
                                pct = min(100, int((downloaded / total) * 100))
                                remaining_bytes = total - downloaded
                                eta_sec = int(remaining_bytes / speed) if speed > 0 else 0
                                eta_text = f"{eta_sec // 60}m {eta_sec % 60}s" if eta_sec > 0 else "..."
                                text = f"Descargando {filename}\n{mb_dl:.1f} MB de {mb_total:.1f} MB ({speed_mb:.1f} MB/s) - Restan: {eta_text}"
                            else:
                                pct = 0
                                text = f"Descargando {filename}\n{mb_dl:.1f} MB ({speed_mb:.1f} MB/s)"
                            self.progress.emit(pct, text)
                            last_update_time = now

            if self._is_cancelled:
                part_path.unlink(missing_ok=True)
                return

            if downloaded < 5000000:
                raise Exception(f"La descarga falló o es un archivo inválido. Tamaño: {downloaded} bytes.")
            if total > 0 and downloaded < total:
                raise Exception("La descarga se interrumpió antes de terminar.")

            self.sha256 = self._tracker.verify()
            part_path.replace(dest_path)
            save_checksum(dest_path, self.sha256)
            self.finished_ok.emit(str(dest_path))
        except Exception as e:
            if part_path and part_path.exists():
                try: part_path.unlink(missing_ok=True)
                except: pass
            if not self._is_cancelled:
                self.error.emit(str(e))


def scan_pci_devices():
    if IS_WINDOWS:
        return []
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
    if IS_WINDOWS:
        return []
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
        self.input_name.setToolTip("Nombre del archivo de disco duro virtual (se usará para generar el nombre del archivo)")
        self.input_name.textChanged.connect(self._update_path)
        form.addRow("Nombre del archivo:", self.input_name)

        origen_layout = QHBoxLayout()
        self.radio_new = QRadioButton("Crear nuevo")
        self.radio_new.setToolTip("Crear un disco duro virtual nuevo y vacío")
        self.radio_existing = QRadioButton("Usar archivo existente")
        self.radio_existing.setToolTip("Reutilizar un archivo de disco duro virtual que ya tengas")
        self.radio_new.setChecked(True)
        self.radio_new.toggled.connect(self._toggle_mode)
        origen_layout.addWidget(self.radio_new); origen_layout.addWidget(self.radio_existing)
        form.addRow("Origen:", origen_layout)

        self.widget_new = QWidget()
        lay_new = QFormLayout(self.widget_new)
        lay_new.setContentsMargins(0,0,0,0)

        self.input_size = QLineEdit("40G")
        self.input_size.setToolTip("Tamaño del disco duro virtual (ej: 40G, 100G)")
        lay_new.addRow("Tamaño:", self.input_size)

        self.combo_type = QComboBox()
        self.combo_type.setToolTip("Expandible: crece según se usa. Fijo: ocupa todo el espacio desde el inicio")
        for tipo in ("Expandible (dinámico)", "Fijo (preasignado)"):
            self.combo_type.addItem(tipo, tipo)
        lay_new.addRow("Tipo:", self.combo_type)

        self.combo_format = QComboBox()
        self.combo_format.setToolTip("Formato del archivo de disco. QCOW2 es el recomendado por esta aplicación")
        self.combo_format.addItems(["QCOW2", "IMG (RAW)", "VDI", "VMDK", "VHD", "VHDX"])
        self.combo_format.currentIndexChanged.connect(self._update_path)
        lay_new.addRow("Formato:", self.combo_format)

        form.addRow(self.widget_new)

        # Solo visible al MODIFICAR un disco existente: permite agrandarlo.
        self.widget_resize = QWidget()
        lay_resize = QFormLayout(self.widget_resize)
        lay_resize.setContentsMargins(0, 0, 0, 0)
        self.lbl_cur_size = QLabel("-")
        self.lbl_cur_size.setToolTip("Tamaño actual del disco. Nunca se puede reducir.")
        lay_resize.addRow("Tamaño actual:", self.lbl_cur_size)
        self.input_resize = QLineEdit()
        self.input_resize.setToolTip("Nuevo tamaño del disco. Debe ser igual o mayor que el tamaño actual (ej: 60G, 100M).")
        lay_resize.addRow("Nuevo tamaño:", self.input_resize)
        form.addRow(self.widget_resize)
        self.widget_resize.setVisible(False)

        self.combo_bus = QComboBox()
        self.combo_bus.setToolTip("Bús de conexión del disco al controlador de almacenamiento virtual")
        for bus in ("Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "NVMe", "IDE",
                    "SCSI (emulado)", "VirtIO-BLK", "VirtIO-SCSI"):
            self.combo_bus.addItem(bus, bus)
        form.addRow("Bus del disco:", self.combo_bus)

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Ruta completa del disco...")
        self.input_path.setReadOnly(True)
        self.input_path.setToolTip("Ruta completa donde se guardará el archivo de disco")
        self.btn_browse_path = QPushButton("📁")
        self.btn_browse_path.setToolTip("Seleccionar carpeta donde guardar el disco")
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
        self.btn_lib.setToolTip("Elegir un disco desde la biblioteca de medios")
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
            self._editing_disk = True
            self.setWindowTitle("Modificar disco duro")
            self._original_size = disk_data.get("size", "20G")
            self.input_name.setText(disk_data.get("name", ""))
            self.input_file.setText(disk_data.get("path", ""))
            self.input_size.setText(disk_data.get("size", "40G"))
            if disk_data.get("format"): _set_combo_value(self.combo_format, disk_data.get("format"))
            if disk_data.get("type"): _set_combo_value(self.combo_type, disk_data.get("type"))
            if disk_data.get("bus"): _set_combo_value(self.combo_bus, disk_data.get("bus"))
            self.radio_existing.setChecked(True)

            # --- Modo modificar: no se permite tocar nombre, origen ni ubicación ---
            self.input_name.setReadOnly(True)
            self.input_name.setToolTip("El nombre del archivo no se puede modificar.")
            self.radio_new.setEnabled(False)
            self.radio_existing.setEnabled(False)
            self.input_file.setReadOnly(True)
            self.input_file.setToolTip("La ubicación del archivo no se puede modificar.")
            self.btn_browse.setEnabled(False)
            self.btn_lib.setEnabled(False)
            self.btn_browse_path.setEnabled(False)
            self.btn_browse_path.setToolTip("La ubicación del disco no se puede modificar.")

            # El tamaño de creación (widget_new) no aplica: solo se permite agrandar.
            self.widget_new.setVisible(False)
            self.widget_resize.setVisible(True)
            self.lbl_cur_size.setText(str(self._original_size))
            self.input_resize.setText(str(self._original_size))
        else:
            self._editing_disk = False
            self._original_size = None
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
        self.btn_advanced.setText(tr("▼ Avanzado (rendimiento e I/O)" if v else "▶ Avanzado (rendimiento e I/O)"))

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

    @property
    def effective_size(self):
        """Tamaño que se debe aplicar (creación o agrandado según el modo)."""
        if self._editing_disk:
            return self.input_resize.text().strip()
        return self.input_size.text().strip()

    @staticmethod
    def _parse_size(text):
        """Convierte '40G', '100M', '512K', '2T'... a bytes. None si no es válido."""
        if text is None:
            return None
        s = str(text).strip().upper().replace(" ", "")
        if not s:
            return None
        units = {
            "B": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4,
            "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4,
            "KIB": 1024, "MIB": 1024 ** 2, "GIB": 1024 ** 3, "TIB": 1024 ** 4,
        }
        i = 0
        while i < len(s) and (s[i].isdigit() or s[i] == "."):
            i += 1
        num_part, unit = s[:i], s[i:]
        if not num_part:
            return None
        try:
            value = float(num_part)
        except ValueError:
            return None
        if not unit:
            unit = "B"
        if unit not in units:
            return None
        return int(value * units[unit])

    def accept(self):
        if self._editing_disk:
            new_bytes = self._parse_size(self.input_resize.text())
            orig_bytes = self._parse_size(self._original_size)
            if new_bytes is None:
                QMessageBox.warning(
                    self, "Tamaño inválido",
                    "Escribe un tamaño válido, por ejemplo 60G, 100M o 512K.")
                return
            if orig_bytes is not None and new_bytes < orig_bytes:
                QMessageBox.warning(
                    self, "Tamaño no permitido",
                    f"El nuevo tamaño ({self.input_resize.text().strip()}) es menor "
                    f"que el tamaño actual ({self._original_size}).\n\n"
                    "Un disco solo puede crecer, nunca reducirse.")
                return
        if self.radio_new.isChecked() and not self.input_path.text():
            QMessageBox.warning(self, "Error", "Debes especificar una ruta para el nuevo disco.")
            return
        super().accept()


class CDDVDDialog(QDialog):
    """Diálogo para configurar una unidad óptica.

    allow_download=False deshabilita la opción "Descargar" en el combo de fuente
    y muestra un tooltip explicativo (la descarga automática no está soportada
    para el SO actual).
    """

    def __init__(self, parent=None, cd_data=None, default_dir=None, app=None, allow_download=True):
        super().__init__(parent)
        self.default_dir = default_dir
        self.app = app
        self.allow_download = allow_download
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>📀 Unidad CD / DVD</b>"))

        self.combo_source = QComboBox()
        self.combo_source.setToolTip("Origen del medio para la unidad de CD/DVD")
        # El dato siempre es la clave española: el texto visible se traduce.
        self.combo_source.addItem(SOURCE_EMPTY, SOURCE_EMPTY)
        self.combo_source.addItem(SOURCE_EXISTING, SOURCE_EXISTING)
        self.combo_source.addItem(SOURCE_DOWNLOAD, SOURCE_DOWNLOAD)
        self.combo_source.currentIndexChanged.connect(self._toggle_source)
        layout.addRow("Fuente del medio:", self.combo_source)

        if not self.allow_download:
            self._disable_download_item()

        self.input_name = QLineEdit("CD/DVD")
        self.input_name.setToolTip("Nombre de la unidad de CD/DVD")
        layout.addRow("Nombre:", self.input_name)

        self.combo_bus = QComboBox()
        self.combo_bus.setToolTip("Bús de conexión de la unidad de CD/DVD")
        for bus in ("Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "IDE",
                    "SCSI (emulado)", "USB"):
            self.combo_bus.addItem(bus, bus)
        layout.addRow("Bus del CD/DVD:", self.combo_bus)

        self.media_widget = QWidget()
        h = QHBoxLayout(self.media_widget)
        h.setContentsMargins(0,0,0,0)
        self.input_file = QLineEdit()
        self.input_file.setToolTip("Ruta del archivo ISO/IMG/DMG")
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.setToolTip("Buscar un archivo ISO/IMG/DMG en el disco")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.setToolTip("Elegir una imagen desde la biblioteca de medios")
        self.btn_lib.clicked.connect(self._browse_library)
        h.addWidget(self.input_file); h.addWidget(self.btn_browse); h.addWidget(self.btn_lib)
        layout.addRow("Medio:", self.media_widget)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

        if cd_data:
            path = cd_data.get("path", "")
            if cd_data.get("bus"):
                _set_combo_value(self.combo_bus, cd_data.get("bus"))
            if path in ("Descargar automáticamente", tr("Descargar automáticamente")):
                if self.allow_download:
                    _set_combo_value(self.combo_source, SOURCE_DOWNLOAD)
                # Si no se permite descarga, mantenemos "Mantener vacío" (index 0)
            elif path and path not in ("Vacío", tr("Vacío"), "Mantener vacío"):
                self.input_file.setText(path)
                _set_combo_value(self.combo_source, SOURCE_EXISTING)

        self._toggle_source()

    def _disable_download_item(self):
        """Deshabilita el ítem 'Descargar' del combo y añade un tooltip."""
        idx = self.combo_source.findData(SOURCE_DOWNLOAD)
        if idx < 0:
            return
        model = self.combo_source.model()
        if isinstance(model, QStandardItemModel):
            item = model.item(idx)
            if item is not None:
                item.setEnabled(False)
        self.combo_source.setItemData(
            idx,
            "La descarga automática no está disponible para este SO.\n"
            "Selecciona un ISO local o descarga la imagen manualmente\n"
            "y vuelve a cargarla con 'Usar ISO/IMG/DMG existente'.",
            Qt.ItemDataRole.ToolTipRole,
        )

    def _toggle_source(self):
        source = _combo_value(self.combo_source)
        # Salvaguarda: si "Descargar" está deshabilitado pero por alguna razón
        # quedó seleccionado, volvemos a "Mantener vacío".
        if source == SOURCE_DOWNLOAD and not self.allow_download:
            self.combo_source.setCurrentIndex(0)
            source = _combo_value(self.combo_source)
        self.media_widget.setVisible(source == SOURCE_EXISTING)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes (*.iso *.img *.dmg)")
        if p: self.input_file.setText(p)

    def _browse_library(self):
        dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.input_file.setText(dlg.selected_path)


class FloppyDialog(QDialog):
    def __init__(self, parent=None, default_dir=None, app=None, floppy_data=None):
        super().__init__(parent)
        self.default_dir = default_dir
        self.app = app
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>💾 Disquetera (FDC)</b>"))

        self.input_name = QLineEdit("floppy")
        self.input_name.setToolTip("Nombre del archivo de imagen de disquete")
        layout.addRow("Nombre:", self.input_name)

        orig = QHBoxLayout()
        self.radio_new = QRadioButton("Crear nuevo"); self.radio_exist = QRadioButton("Usar archivo existente")
        self.radio_new.setToolTip("Crear una imagen de disquete nueva y vacía")
        self.radio_exist.setToolTip("Reutilizar una imagen de disquete que ya tengas")
        self.radio_new.setChecked(True)
        orig.addWidget(self.radio_new); orig.addWidget(self.radio_exist)
        layout.addRow("Origen:", orig)

        self.combo_size = QComboBox()
        self.combo_size.setToolTip("Capacidad de la imagen de disquete")
        self.combo_size.addItems(["720 KB", "1.44 MB", "2.88 MB"]); self.combo_size.setCurrentText("1.44 MB")
        layout.addRow("Tamaño:", self.combo_size)

        self.input_format = QLineEdit("RAW"); self.input_format.setReadOnly(True)
        self.input_format.setToolTip("Formato de la imagen de disquete (solo RAW disponible)")
        layout.addRow("Formato:", self.input_format)

        h_file = QHBoxLayout()
        self.input_file = QLineEdit()
        self.input_file.setToolTip("Ruta del archivo de imagen de disquete")
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.setToolTip("Buscar un archivo de imagen de disquete en el disco")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.setToolTip("Elegir una imagen de disquete desde la biblioteca de medios")
        self.btn_lib.clicked.connect(self._browse_library)
        h_file.addWidget(self.input_file); h_file.addWidget(self.btn_browse); h_file.addWidget(self.btn_lib)
        layout.addRow("Archivo:", h_file)

        if floppy_data:
            self.setWindowTitle(tr("Modificar disquetera"))
            self.input_name.setText(floppy_data.get("name") or "floppy")
            self.input_file.setText(floppy_data.get("path") or "")
            if floppy_data.get("size"):
                _set_combo_value(self.combo_size, floppy_data["size"])
            self.radio_exist.setChecked(True)

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
        self.input_name.setToolTip("Nombre identificador de esta conexión de red")
        layout.addRow("Nombre:", self.input_name)

        self.combo_model = QComboBox()
        self.combo_model.setToolTip("Modelo de tarjeta de red virtual que verá el sistema invitado")
        self.combo_model.addItems(["VirtIO", "Intel E1000", "Realtek", "VMware VMXNET3"])
        idx = self.combo_model.findText(self._data.get("model", "VirtIO"))
        if idx >= 0: self.combo_model.setCurrentIndex(idx)
        layout.addRow("Modelo:", self.combo_model)

        self.combo_backend = QComboBox()
        self.combo_backend.setToolTip("Tipo de conexión de red: NAT (internet compartido), Bridge (red física) o TAP")
        self.combo_backend.addItems(["NAT / Internet", "Bridge existente", "TAP"])
        idx = self.combo_backend.findText(self._data.get("backend", "NAT / Internet"))
        if idx >= 0: self.combo_backend.setCurrentIndex(idx)
        self.combo_backend.currentTextChanged.connect(self._on_backend_changed)
        layout.addRow("Backend:", self.combo_backend)

        self.input_bridge = QLineEdit()
        self.input_bridge.setPlaceholderText("Nombre del bridge o TAP...")
        self.input_bridge.setToolTip("Nombre de la interfaz bridge o TAP del host (solo para Bridge/TAP)")
        self.input_bridge.setText(self._data.get("bridge", ""))
        layout.addRow("Bridge / TAP:", self.input_bridge)

        self.input_mac = QLineEdit()
        self.input_mac.setPlaceholderText("Opcional: 52:54:00:xx:xx:xx")
        self.input_mac.setToolTip("Dirección MAC opcional para la tarjeta de red virtual")
        self.input_mac.setText(self._data.get("mac", ""))
        layout.addRow("MAC:", self.input_mac)

        self.btn_nat = QPushButton("📋 Reglas NAT...")
        self.btn_nat.setToolTip("Configurar reglas de reenvío de puertos del host al guest (solo NAT)")
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
        self.input_host.setToolTip("Puerto en el host anfitrión")
        self.input_guest = QLineEdit(); self.input_guest.setPlaceholderText("Puerto guest")
        self.input_guest.setToolTip("Puerto en la máquina virtual invitada")
        self.combo_proto = QComboBox(); self.combo_proto.addItems(["TCP", "UDP"])
        self.combo_proto.setToolTip("Protocolo de red para la regla de reenvío")
        btn_add = QPushButton("➕ Añadir"); btn_add.setToolTip("Añadir esta regla de reenvío de puertos"); btn_add.clicked.connect(self._add)
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
        self.data = data or {}
        layout = QFormLayout(self)
        h_host = QHBoxLayout()
        self.input_host = QLineEdit(); self.btn_browse = QPushButton("📁")
        self.input_host.setToolTip("Ruta de la carpeta en el host anfitrión que se compartirá")
        self.btn_browse.setToolTip("Seleccionar carpeta del host")
        self.btn_browse.clicked.connect(self._browse)
        h_host.addWidget(self.input_host); h_host.addWidget(self.btn_browse)
        layout.addRow("Carpeta del host:", h_host)
        self.input_label = QLineEdit("share")
        self.input_label.setToolTip("Etiqueta con la que se accederá a la carpeta desde el guest")
        layout.addRow("Etiqueta / guest:", self.input_label)
        self.combo_method = QComboBox(); self.combo_method.addItems(["Automático", "VirtioFS", "9p", "SMB"])
        self.combo_method.setToolTip("Protocolo usado para compartir la carpeta")
        layout.addRow("Método:", self.combo_method)
        self.combo_mount = QComboBox(); self.combo_mount.addItems(["Manual", "Automático al iniciar SO", "Automático bajo demanda"])
        self.combo_mount.setToolTip("Cuándo se monta la carpeta compartida en el guest")
        layout.addRow("Montaje en el guest:", self.combo_mount)
        self.check_ro = QCheckBox("Solo lectura")
        self.check_ro.setToolTip("Si está activo, el guest solo podrá leer la carpeta compartida")
        layout.addRow("Acceso:", self.check_ro)
        info = QLabel("La política de montaje es la misma para todos los SO.")
        info.setWordWrap(True); info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

        if self.data:
            self.input_host.setText(self.data.get("host", ""))
            if self.data.get("guest"): self.input_label.setText(self.data.get("guest"))
            idx = self.combo_method.findText(self.data.get("method", "Automático"))
            if idx >= 0: self.combo_method.setCurrentIndex(idx)
            idx = self.combo_mount.findText(self.data.get("mount", "Manual"))
            if idx >= 0: self.combo_mount.setCurrentIndex(idx)
            self.check_ro.setChecked(self.data.get("ro", False))

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if p: self.input_host.setText(p)

    def accept(self):
        host = self.input_host.text().strip()
        if not host:
            QMessageBox.warning(self, "Error", "Debes seleccionar una carpeta del host.")
            return
        if not os.path.exists(host):
            QMessageBox.warning(self, "Error", f"La carpeta seleccionada no existe:\n{host}")
            return
        super().accept()


class Plugin(PluginBase):
    name = "ConfiguracionVM"
    version = "20.7.0"

    def __init__(self, app):
        super().__init__(app)
        self.current_vm_id = None
        self.host = HostProfile()
        self._network_data = []

    # ------------------------------------------------------------------
    # Almacenamiento: identificadores estables (nunca texto traducido)
    # ------------------------------------------------------------------
    def _storage_type(self, item):
        tipo = item.data(0, Qt.ItemDataRole.UserRole)
        if tipo in (TIPO_DISCO, TIPO_OPTICO, TIPO_DISQUETE):
            return tipo
        texto = item.text(0)
        for clave in (TIPO_DISCO, TIPO_OPTICO, TIPO_DISQUETE):
            if texto == clave or texto == tr(clave):
                return clave
        return texto

    def _storage_bus(self, item):
        return (item.data(3, Qt.ItemDataRole.UserRole + 1)
                or item.data(3, Qt.ItemDataRole.UserRole)
                or item.text(3))

    def _retranslate_storage(self):
        """Actualiza celdas generadas dinámicamente al cambiar de idioma."""
        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            tipo = self._storage_type(item)
            item.setText(0, tr(tipo))
            if tipo == TIPO_OPTICO:
                item.setText(1, tr("CD/DVD"))
                source = item.data(2, Qt.ItemDataRole.UserRole) or SOURCE_EMPTY
                if source == SOURCE_DOWNLOAD:
                    item.setText(2, tr("Descargar automáticamente"))
                elif source in (SOURCE_EMPTY, "Vacío") and not os.path.exists(item.text(2)):
                    item.setText(2, tr("Vacío"))
                bus = self._storage_bus(item)
                if bus:
                    item.setData(3, Qt.ItemDataRole.UserRole, bus)
                    item.setData(3, Qt.ItemDataRole.UserRole + 1, bus)
                    item.setText(3, tr(bus))
            elif tipo == TIPO_DISQUETE:
                item.setText(1, "FDC")
            path = item.text(2)
            self._apply_mount_marker(item, path if os.path.exists(path) else "")

    def get_tabs(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Nombre:</b>"))
        self.input_name = QLineEdit()
        self.input_name.setFixedWidth(150)
        self.input_name.setToolTip("Nombre identificador de la máquina virtual")
        top_bar.addWidget(self.input_name)

        top_bar.addWidget(QLabel("<b>Plataforma:</b>"))
        self.combo_platform = QComboBox()
        self.combo_platform.blockSignals(True)
        self.combo_platform.addItems(list(OS_CATALOG.keys()))
        self.combo_platform.blockSignals(False)
        self.combo_platform.setToolTip("Familia de sistema operativo que se instalará en la VM")
        # Lambda con True: el cambio de plataforma SIEMPRE debe consultar
        # versiones dinámicas al cambiar (el usuario lo pidió explícitamente).
        self.combo_platform.currentIndexChanged.connect(lambda _: self._on_platform_changed(True))
        top_bar.addWidget(self.combo_platform)

        self.lbl_so = QLabel("<b>SO:</b>")
        top_bar.addWidget(self.lbl_so)
        self.combo_so = QComboBox()
        self.combo_so.setToolTip("Distribución o versión específica del sistema operativo")
        self.combo_so.currentIndexChanged.connect(lambda _: self._on_so_changed(True))
        top_bar.addWidget(self.combo_so)

        self.lbl_ver = QLabel("<b>Versión de SO:</b>")
        top_bar.addWidget(self.lbl_ver)
        self.combo_version = QComboBox()
        self.combo_version.setToolTip("Versión concreta de la imagen de instalación")
        top_bar.addWidget(self.combo_version)

        top_bar.addWidget(QLabel("<b>Perfil:</b>"))
        self.combo_profile = QComboBox()
        self.combo_profile.setToolTip("Configuración predefinida de hardware (RAM, CPU, firmware...)")
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
        """Rellena combo_version.

        Si trigger_fetch es True, intenta primero obtener la lista dinámica
        desde internet (iso_versions.get_available_versions). Si falla o el
        SO no la soporta, cae al catálogo estático OS_CATALOG.

        El data de cada ítem es el `id` de versión (v["id"]) para versiones
        dinámicas, o el propio texto de la versión para las estáticas. Así
        `combo_version.currentData()` siempre devuelve algo utilizable.
        """
        p = self.combo_platform.currentText()
        so = self.combo_so.currentText()
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.setEnabled(False)
        self.lbl_ver.setToolTip("")
        if not so:
            self.combo_version.blockSignals(False)
            return

        loaded_dynamic = False
        if trigger_fetch:
            try:
                dynamic = iso_versions.get_available_versions(so)
            except Exception as e:
                log.warning(f"No se pudieron obtener versiones dinámicas para {so}: {e}")
                dynamic = None
            if dynamic:
                for v in dynamic:
                    label = v.get("label") or str(v.get("id", ""))
                    vid = v.get("id") or label
                    self.combo_version.addItem(label, vid)
                loaded_dynamic = True
                self.lbl_ver.setToolTip("Versiones obtenidas en línea desde el mirror oficial.")

        if not loaded_dynamic:
            static_versions = OS_CATALOG.get(p, {}).get(so, ["Automático"])
            for v in static_versions:
                self.combo_version.addItem(v, v)
            if trigger_fetch:
                self.lbl_ver.setToolTip(
                    "No se pudo consultar internet; se muestra el catálogo local."
                )

        self.combo_version.setEnabled(True)
        self.combo_version.blockSignals(False)

        # #7 Autocompletar nombre: solo si el campo está vacío o tiene el nombre
        # genérico anterior (evita sobreescribir un nombre que el usuario ya escribió)
        so = self.combo_so.currentText()
        if so:
            current_name = self.input_name.text().strip()
            # Detectar si es un nombre autogenerado o está vacío
            is_auto = (not current_name or
                       current_name in list(OS_CATALOG.get(self.combo_platform.currentText(), {}).keys()) or
                       any(current_name == s
                           for sos in OS_CATALOG.values()
                           for s in sos.keys()))
            if is_auto:
                self.input_name.setText(so)

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

        # Bloqueamos señales para evitar dobles fetches; llamamos explícitamente.
        idx = self.combo_platform.findText(prof["platform"])
        if idx >= 0:
            self.combo_platform.blockSignals(True)
            self.combo_platform.setCurrentIndex(idx)
            self.combo_platform.blockSignals(False)
        self._on_platform_changed(False)

        idx = self.combo_so.findText(prof["os"])
        if idx >= 0:
            self.combo_so.blockSignals(True)
            self.combo_so.setCurrentIndex(idx)
            self.combo_so.blockSignals(False)
        self._on_so_changed(True)

        self.combo_profile.setCurrentIndex(0)
        QMessageBox.information(self.app.parent(), "Perfil aplicado", f"El perfil '{prof['name']}' ha sido aplicado.")

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE PÁGINAS
    # ------------------------------------------------------------------
    def _build_pages(self):
        p1 = QWidget(); l1 = QVBoxLayout(p1)
        self.combo_firmware = QComboBox()
        self.combo_firmware.setToolTip("Tipo de firmware: BIOS (tradicional) o UEFI (OVMF, requerido para discos GPT y Secure Boot)")
        self.combo_firmware.addItems(["BIOS (tradicional)", "UEFI (OVMF)"])
        l1.addWidget(QLabel("<b>Firmware</b>")); l1.addWidget(self.combo_firmware)
        self.combo_chipset = QComboBox()
        self.combo_chipset.setToolTip("Chipset de la placa base virtual: i440FX (clásico) o Q35 (moderno, PCIe)")
        self.combo_chipset.addItems(["i440FX (clásico)", "Q35 (moderno, PCIe)"])
        l1.addWidget(QLabel("<b>Chipset</b>")); l1.addWidget(self.combo_chipset)
        sec_layout = QHBoxLayout()
        self.check_secure_boot = QCheckBox("Secure Boot")
        self.check_secure_boot.setToolTip("Arranque seguro UEFI (requiere firmware UEFI y sistema operativo compatible)")
        self.check_tpm = QCheckBox("TPM 2.0")
        self.check_tpm.setToolTip("Módulo de plataforma confiable virtual (requerido por Windows 11)")
        sec_layout.addWidget(self.check_secure_boot); sec_layout.addWidget(self.check_tpm); sec_layout.addStretch()
        l1.addWidget(QLabel("<b>Seguridad</b>")); l1.addLayout(sec_layout); l1.addStretch()

        p2 = QWidget(); l2 = QVBoxLayout(p2)
        self.combo_cpu_type = QComboBox()
        self.combo_cpu_type.setToolTip("Modelo de CPU virtual expuesta al sistema invitado")
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
        self.check_cpu_topology.setToolTip("Define manualmente la distribución de sockets, cores y threads por vCPU")
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
        self.check_hyperv.setToolTip("En VMs Windows estas optimizaciones se aplican siempre.")
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
        self.check_hugepages.setToolTip("Usa páginas de memoria grandes del host para mejorar el rendimiento")
        self.check_prealloc = QCheckBox("Reservar toda la RAM al arrancar (prealloc)")
        self.check_prealloc.setToolTip("Reserva toda la memoria RAM asignada al iniciar la VM")
        self.check_memfd = QCheckBox("Bloquear la RAM de la VM (memfd-lock)")
        self.check_memfd.setToolTip("Impide que el host intercambie a disco la memoria de la VM")
        l3.addWidget(self.check_hugepages); l3.addWidget(self.check_prealloc); l3.addWidget(self.check_memfd)

        self.check_free_page_reporting = QCheckBox("Devolver RAM no usada al host (Free Page Reporting)")
        self.check_free_page_reporting.setToolTip("Permite al invitado devolver dinámicamente la RAM que no usa al sistema anfitrión.")
        l3.addWidget(self.check_free_page_reporting)
        l3.addStretch()

        p4 = QWidget(); l4 = QVBoxLayout(p4)

        self.combo_console_proto = QComboBox()
        self.combo_console_proto.setToolTip("Protocolo usado para ver la consola gráfica de la VM")
        self.combo_console_proto.addItems([
            "VNC",
            "SPICE (Local 3D)",
            "SPICE (Remoto - Red)"
        ])
        self.combo_console_proto.currentIndexChanged.connect(self._update_display_options)
        l4.addWidget(QLabel("<b>Protocolo de consola</b>"))
        l4.addWidget(self.combo_console_proto)

        self.combo_console_mode = QComboBox()
        self.combo_console_mode.setToolTip("Dónde se muestra la ventana de consola de la VM")
        self.combo_console_mode.addItems([
            "Embebida en la app",
            "Ventana externa",
            "Híbrida (VNC widget + SPICE externo)",
            "Pantalla completa",
            "Pantalla completa (embebida)",
        ])
        self.combo_console_mode.currentIndexChanged.connect(self._update_display_options)
        l4.addWidget(QLabel("<b>Modo de consola</b>"))
        l4.addWidget(self.combo_console_mode)

        self.combo_graphics = QComboBox()
        self.combo_graphics.setToolTip("Dispositivo gráfico virtual. 3D (VirGL/Venus) requiere remote-viewer con soporte OpenGL; si la ventana SPICE queda en negro, usa 'VirtIO-GPU 2D (compatible)' o 'Automático'.")
        self.combo_graphics.addItems([
            "Automático (recomendado) → VirtIO-GPU 2D",
            "VirtIO-GPU 2D (compatible)",
            "VirtIO-GPU + VirGL 3D",
            "VirtIO-GPU + Venus/Vulkan 3D",
            "Red Hat QXL 2D",
            "VMware SVGA II",
            "VGA estándar",
            "Sin video / Headless"
        ])
        l4.addWidget(QLabel("<b>Gráficos / GPU</b>"))
        l4.addWidget(self.combo_graphics)

        self.combo_vram = QComboBox(); self.combo_vram.setToolTip("Memoria de video (VRAM) asignada a la tarjeta gráfica virtual")
        self.combo_vram.addItems(["64 MB", "128 MB", "256 MB", "512 MB"])
        l4.addWidget(QLabel("<b>Memoria de video</b>"))
        l4.addWidget(self.combo_vram)

        lbl_hint = QLabel(
            "F11 alterna pantalla completa · Ctrl+Alt+F sale · Ctrl+Alt+G libera el teclado del guest.\n"
            "SPICE no se puede mostrar embebido en la app; si eliges SPICE se forzará ventana externa.\n"
            "⚠️ 3D (VirGL/Venus) también requiere un remote-viewer con soporte OpenGL; si la ventana sale en negro, usa VirtIO-GPU 2D."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #888; font-size: 11px;")
        l4.addWidget(lbl_hint)

        # Campos informativos de compatibilidad
        self.lbl_clipboard_info = QLabel("")
        self.lbl_clipboard_info.setWordWrap(True)
        self.lbl_clipboard_info.setStyleSheet("color: #666; font-size: 11px;")
        l4.addWidget(self.lbl_clipboard_info)

        self.lbl_snapshot_info = QLabel("")
        self.lbl_snapshot_info.setWordWrap(True)
        self.lbl_snapshot_info.setStyleSheet("color: #666; font-size: 11px;")
        l4.addWidget(self.lbl_snapshot_info)

        l4.addStretch()

        p5 = QWidget(); l5 = QVBoxLayout(p5)
        self.tree_storage = QTreeWidget(); self.tree_storage.setHeaderLabels(["Dispositivo", "Bus", "Tipo / archivo", "Tamaño", "Estado"])
        self.tree_storage.setColumnWidth(0, 150); self.tree_storage.setSortingEnabled(True)
        self.tree_storage.setToolTip("Lista de dispositivos de almacenamiento de la VM (discos, CD/DVD, disquetes)")
        self.tree_storage._nvm_retranslate = self._retranslate_storage
        l5.addWidget(self.tree_storage)
        b5 = QHBoxLayout()
        for label, func in [("📀 CD/DVD", self._add_cd), ("💽 Disco Duro", self._add_hdd), ("💾 Disquete", self._add_floppy), ("✏ Modificar", self._modify_media), ("🗜 Compactar", self._compact_media), ("🗑 Eliminar", self._delete_media), ("🔌 Montar/Desmontar", self._mount_eject_media)]:
            btn = QPushButton(label); btn.clicked.connect(func); b5.addWidget(btn)
        b5.addStretch(); l5.addLayout(b5)
        l5.addWidget(QLabel("<b>Orden de arranque (drag & drop)</b>"))
        self.list_boot = QListWidget(); self.list_boot.setMaximumHeight(120)
        self.list_boot.setToolTip("Orden en que la VM intenta arrancar desde cada dispositivo")
        self.list_boot.setDragEnabled(True)
        self.list_boot.setAcceptDrops(True)
        self.list_boot.setDropIndicatorShown(True)
        self.list_boot.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_boot._nvm_retranslate = self._retranslate_boot
        l5.addWidget(self.list_boot)
        b_boot = QHBoxLayout()
        up_btn = QPushButton("⬆ Subir"); up_btn.setToolTip("Mover el dispositivo seleccionado arriba en el orden de arranque"); up_btn.clicked.connect(lambda: self._move_boot(-1))
        dn_btn = QPushButton("⬇ Bajar"); dn_btn.setToolTip("Mover el dispositivo seleccionado abajo en el orden de arranque"); dn_btn.clicked.connect(lambda: self._move_boot(1))
        b_boot.addWidget(up_btn); b_boot.addWidget(dn_btn); b_boot.addStretch(); l5.addLayout(b_boot); l5.addStretch()

        p6 = QWidget(); l6 = QVBoxLayout(p6)
        self.list_net = QListWidget()
        self.list_net.setToolTip("Lista de adaptadores de red virtuales de la VM")
        l6.addWidget(QLabel("<b>Adaptadores</b>")); l6.addWidget(self.list_net)
        b6 = QHBoxLayout()
        btn_net_add = QPushButton("➕ Agregar"); btn_net_add.setToolTip("Añadir un nuevo adaptador de red a la VM"); btn_net_add.clicked.connect(self._add_net)
        btn_net_edit = QPushButton("✏ Editar"); btn_net_edit.setToolTip("Modificar el adaptador de red seleccionado"); btn_net_edit.clicked.connect(self._edit_net)
        btn_net_del = QPushButton("🗑 Eliminar"); btn_net_del.setToolTip("Eliminar el adaptador de red seleccionado"); btn_net_del.clicked.connect(self._del_net)
        b6.addWidget(btn_net_add); b6.addWidget(btn_net_edit); b6.addWidget(btn_net_del); b6.addStretch(); l6.addLayout(b6); l6.addStretch()

        p7 = QWidget(); l7 = QVBoxLayout(p7)
        self.combo_audio = QComboBox(); self.combo_audio.setToolTip("Dispositivo de audio virtual de la VM")
        self.combo_audio.addItems(["Intel HDA (recomendado)", "AC97", "Sound Blaster", "Ninguno"])
        self.combo_pointer = QComboBox(); self.combo_pointer.setToolTip("Dispositivo de señalización (ratón/teclado) virtual de la VM")
        self.combo_pointer.addItems(["Automático (recomendado)", "USB Tablet", "USB Mouse", "USB Keyboard + Tablet", "VirtIO Tablet", "PS/2", "Ninguno"])
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
        warn_sh = QLabel("⚠ Para montaje automático en el guest, instala QEMU Guest Agent dentro del SO invitado (ej. qemu-guest-agent en Linux).")
        warn_sh.setWordWrap(True); warn_sh.setStyleSheet("color: #b00020; font-size: 11px; font-weight: bold;")
        l9.addWidget(warn_sh)
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
        btn_gt = QPushButton("🛠️ Crear/Montar ISO de Guest Tools")
        btn_gt.setToolTip("Crea un ISO con los instaladores de QEMU Guest Agent y lo monta en un CD/DVD de la VM")
        btn_gt.clicked.connect(self._create_guest_tools_iso)
        lt.addWidget(btn_gt)
        lt.addStretch()

        tab_clip = QWidget(); lc = QVBoxLayout(tab_clip)
        group_clip = QGroupBox("Compartir portapapeles")
        lcl = QVBoxLayout(group_clip)

        self.chk_clipboard = QCheckBox("Activar compartición de portapapeles")
        self.chk_clipboard.setChecked(True)
        lcl.addWidget(self.chk_clipboard)

        lbl_clip_hint = QLabel("Nota: Es recomendable usar el protocolo SPICE para un mejor funcionamiento del portapapeles.")
        lbl_clip_hint.setWordWrap(True)
        lbl_clip_hint.setStyleSheet("color: #888; font-size: 11px;")
        lcl.addWidget(lbl_clip_hint)

        lc.addWidget(group_clip); lc.addStretch()
        self.tabs_sharing.addTab(tab_clip, "Clipboard")

        l9.addWidget(self.tabs_sharing)

        pages = [("🖥️ Sistema", p1), ("⚙️ Procesador", p2), ("🧠 Memoria", p3), ("🖼️ Pantalla", p4), ("💾 Almacenamiento", p5), ("🌐 Red", p6), ("🎛️ Dispositivos", p7), ("🔌 Passthrough", p8), ("📂 Compartición", p9)]
        for name, w in pages:
            self.list_menu.addItem(QListWidgetItem(name))
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(w)
            self.stack.addWidget(scroll)

    def _update_display_options(self):
        proto_idx = self.combo_console_proto.currentIndex()

        model_mode = self.combo_console_mode.model()
        if proto_idx in (1, 2):
            model_mode.item(0).setEnabled(False)
            model_mode.item(3).setEnabled(False)
            model_mode.item(4).setEnabled(False)
            if self.combo_console_mode.currentIndex() in (0, 3, 4):
                self.combo_console_mode.setCurrentIndex(1)
        else:
            for i in range(model_mode.rowCount()):
                model_mode.item(i).setEnabled(True)

        # Si se selecciona Pantalla completa (embebida), forzar protocolo VNC
        if self.combo_console_mode.currentIndex() == 4:
            self.combo_console_proto.setCurrentIndex(0)

        model_gfx = self.combo_graphics.model()
        if proto_idx in (0, 2):
            model_gfx.item(2).setEnabled(False)
            model_gfx.item(3).setEnabled(False)
            if self.combo_graphics.currentIndex() in (2, 3):
                self.combo_graphics.setCurrentIndex(1)
        elif proto_idx == 1:
            for i in range(model_gfx.rowCount()):
                model_gfx.item(i).setEnabled(True)

    def _update_cores_label(self, val): self.lbl_cores.setText(f"{val} {tr('núcleos')}")
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

    # ------------------------------------------------------------------
    # Helpers para saber si un SO soporta descarga automática
    # ------------------------------------------------------------------
    def _so_supports_download(self, so: str) -> bool:
        """Devuelve True si el SO actual soporta descarga automática de ISO."""
        return bool(
            iso_sources.supports_auto_download(so)
            or iso_versions.supports_versions(so)
            or so in ["Windows 10", "Windows 11"]
        )

    # ------------------------------------------------------------------
    # BIBLIOTECA DE MEDIOS: registrar lo que se crea/modifica desde
    # esta pestaña para que aparezca también en "Medios".
    # ------------------------------------------------------------------
    def _register_media(self, path, name, size, fmt, media_type="Disco duro", os_type="Other"):
        """Registra un archivo en la biblioteca de medios central.

        No falla si la biblioteca no está disponible (sandbox, etc.).
        """
        if not path:
            return
        try:
            from services.media_library import MediaLibraryManager
            mgr = MediaLibraryManager(self.app.data_dir, self.app.settings)
            if not os.path.exists(path):
                return
            mgr.add_media(name, str(path), media_type, "-", size_vm=size, fmt=fmt.upper(), os_type=os_type)
        except Exception as e:
            log.debug(f"No se pudo registrar medio '{path}' en la biblioteca: {e}")

    def _update_media_size(self, path, size_vm):
        """Actualiza el tamaño virtual registrado de un medio en la biblioteca."""
        try:
            from services.media_library import MediaLibraryManager
            mgr = MediaLibraryManager(self.app.data_dir, self.app.settings)
            if os.path.exists(path):
                mgr.update_media_size(path, size_vm)
        except Exception as e:
            log.debug(f"No se pudo actualizar tamaño del medio '{path}' en la biblioteca: {e}")

    # ------------------------------------------------------------------
    # ALMACENAMIENTO: añadir / modificar medios
    # ------------------------------------------------------------------
    def _add_cd(self):
        so = self.combo_so.currentText()
        can_download = self._so_supports_download(so)
        dlg = CDDVDDialog(
            self.app.parent(),
            default_dir=self.app.isos_dir,
            app=self.app,
            allow_download=can_download,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            source_type = _combo_value(dlg.combo_source)
            bus = _combo_value(dlg.combo_bus)
            item.setData(0, Qt.ItemDataRole.UserRole, TIPO_OPTICO)
            item.setText(0, tr(TIPO_OPTICO)); item.setText(1, tr("CD/DVD"))
            item.setText(2, dlg.input_file.text() if source_type == SOURCE_EXISTING else (
                tr("Descargar automáticamente") if source_type == SOURCE_DOWNLOAD else tr("Vacío")))
            item.setText(3, tr(bus))
            item.setData(2, Qt.ItemDataRole.UserRole, source_type)
            item.setData(3, Qt.ItemDataRole.UserRole, bus)
            item.setData(3, Qt.ItemDataRole.UserRole + 1, bus)
            # Registrar la ISO elegida en la biblioteca de medios
            if source_type == SOURCE_EXISTING and dlg.input_file.text() and os.path.exists(dlg.input_file.text()):
                self._register_media(
                    dlg.input_file.text(),
                    os.path.basename(dlg.input_file.text()),
                    "-",
                    "iso",
                    media_type="ISO",
                )
            self._sync_boot()

    def _add_hdd(self):
        vm_dir = self.app.vms_dir / self.current_vm_id if self.current_vm_id else self.app.vms_dir
        dlg = DiskDialog(self.app.parent(), default_dir=vm_dir, app=self.app)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            bus = _combo_value(dlg.combo_bus)
            item.setData(0, Qt.ItemDataRole.UserRole, TIPO_DISCO)
            item.setText(0, tr(TIPO_DISCO)); item.setText(1, tr(bus))
            if dlg.radio_new.isChecked():
                item.setText(2, dlg.input_path.text())
                item.setText(3, dlg.effective_size)
                item.setData(2, Qt.ItemDataRole.UserRole, "NEW")
                item.setData(2, Qt.ItemDataRole.UserRole + 1, _combo_value(dlg.combo_format))
                item.setData(2, Qt.ItemDataRole.UserRole + 2, _combo_value(dlg.combo_type))
                item.setData(2, Qt.ItemDataRole.UserRole + 3, _combo_value(dlg.combo_cache))
                item.setData(2, Qt.ItemDataRole.UserRole + 4, _combo_value(dlg.combo_io))
                item.setData(2, Qt.ItemDataRole.UserRole + 5, _combo_value(dlg.combo_discard))
                item.setData(2, Qt.ItemDataRole.UserRole + 6, _combo_value(dlg.combo_detect_zeros))
                item.setData(2, Qt.ItemDataRole.UserRole + 7, _combo_value(dlg.combo_aio))
            else:
                item.setText(2, dlg.input_file.text()); item.setText(3, "-")
                item.setData(2, Qt.ItemDataRole.UserRole, "EXISTING")
                # Registrar el disco existente en la biblioteca de medios
                if dlg.input_file.text() and os.path.exists(dlg.input_file.text()):
                    self._register_media(
                        dlg.input_file.text(),
                        os.path.basename(dlg.input_file.text()),
                        "-",
                        os.path.splitext(dlg.input_file.text())[1].lstrip('.').upper() or "qcow2",
                        media_type="Disco duro",
                    )
            item.setData(2, Qt.ItemDataRole.UserRole + 8, bus)
            self._sync_boot()

    def _add_floppy(self):
        dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir, app=self.app)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = QTreeWidgetItem(self.tree_storage)
            item.setData(0, Qt.ItemDataRole.UserRole, TIPO_DISQUETE)
            item.setText(0, tr(TIPO_DISQUETE)); item.setText(1, "FDC")
            if dlg.radio_new.isChecked():
                item.setText(2, dlg.input_name.text()); item.setText(3, dlg.combo_size.currentText())
            else:
                item.setText(2, dlg.input_file.text()); item.setText(3, "-")
            self._sync_boot()

    def _create_guest_tools_iso(self):
        import subprocess, os, shutil, tempfile
        from pathlib import Path
        from services.iso_writer import create_iso

        iso_dir = Path(self.app.isos_dir) if hasattr(self.app, 'isos_dir') else Path.home() / ".local" / "share" / "nvm" / "isos"
        iso_dir.mkdir(parents=True, exist_ok=True)
        iso_path = iso_dir / "guest-tools.iso"

        staging = Path(tempfile.gettempdir()) / "guest-tools-staging"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)

        linux_dir = staging / "linux"
        linux_dir.mkdir()

        (linux_dir / "install-qga-debian.sh").write_text("""#!/bin/bash
set -e
echo "==> Instalando QEMU Guest Agent, Spice VDagent y Autocutsel (para VNC)..."
sudo apt update && sudo apt install -y qemu-guest-agent spice-vdagent autocutsel

echo "==> Configurando autocutsel para que arranque con el escritorio..."
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
mkdir -p "$REAL_HOME/.config/autostart"
cat <<EOF > "$REAL_HOME/.config/autostart/autocutsel.desktop"
[Desktop Entry]
Type=Application
Name=Autocutsel
Exec=autocutsel -fork
X-GNOME-Autostart-enabled=true
EOF
chown -R "$REAL_USER:$REAL_USER" "$REAL_HOME/.config/autostart"

echo "==> Configurando módulos del kernel para VirtIO, Carpetas y Clipboard..."
echo -e "virtio_pci\\nvirtio_console\\n9p\\n9pnet_virtio" | sudo tee /etc/modules-load.d/nvm-virtio.conf > /dev/null

echo "==> Cargando módulos ahora mismo..."
sudo modprobe virtio_pci 2>/dev/null || true
sudo modprobe virtio_console 2>/dev/null || true
sudo modprobe 9pnet_virtio 2>/dev/null || true

echo "==> Habilitando y arrancando servicios..."
unit=$(systemctl show -p FragmentPath --value qemu-guest-agent 2>/dev/null || true)
if [ -n "$unit" ] && [ -f "$unit" ]; then
    sudo mkdir -p /etc/systemd/system/multi-user.target.wants
    sudo ln -sf "$unit" /etc/systemd/system/multi-user.target.wants/qemu-guest-agent.service
fi
sudo systemctl start qemu-guest-agent || true
sudo systemctl enable --now spice-vdagentd 2>/dev/null || sudo systemctl enable --now spice-vdagent 2>/dev/null || true

echo -n "qemu-guest-agent: "
systemctl is-active qemu-guest-agent || true
echo "==> ¡Listo! Carpetas, SPICE y VNC (portapapeles) configurados."
echo "Por favor, reinicia la máquina virtual."
read -p "Presiona Enter para cerrar..."
""")

        (linux_dir / "install-qga-rhel.sh").write_text("""#!/bin/bash
set -e
echo "==> Instalando QEMU Guest Agent, Spice VDagent y Autocutsel (para VNC)..."
sudo dnf install -y qemu-guest-agent spice-vdagent autocutsel

echo "==> Configurando autocutsel para que arranque con el escritorio..."
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
mkdir -p "$REAL_HOME/.config/autostart"
cat <<EOF > "$REAL_HOME/.config/autostart/autocutsel.desktop"
[Desktop Entry]
Type=Application
Name=Autocutsel
Exec=autocutsel -fork
X-GNOME-Autostart-enabled=true
EOF
chown -R "$REAL_USER:$REAL_USER" "$REAL_HOME/.config/autostart"

echo "==> Configurando módulos del kernel..."
echo -e "virtio_pci\\nvirtio_console\\n9p\\n9pnet_virtio" | sudo tee /etc/modules-load.d/nvm-virtio.conf > /dev/null
sudo modprobe virtio_pci 2>/dev/null || true
sudo modprobe virtio_console 2>/dev/null || true
sudo modprobe 9pnet_virtio 2>/dev/null || true

echo "==> Habilitando servicios..."
unit=$(systemctl show -p FragmentPath --value qemu-guest-agent 2>/dev/null || true)
if [ -n "$unit" ] && [ -f "$unit" ]; then
    sudo mkdir -p /etc/systemd/system/multi-user.target.wants
    sudo ln -sf "$unit" /etc/systemd/system/multi-user.target.wants/qemu-guest-agent.service
fi
sudo systemctl start qemu-guest-agent || true
sudo systemctl enable --now spice-vdagentd 2>/dev/null || sudo systemctl enable --now spice-vdagent 2>/dev/null || true

echo "==> ¡Listo! Carpetas, SPICE y VNC (portapapeles) configurados."
echo "Por favor, reinicia la máquina virtual."
read -p "Presiona Enter para cerrar..."
""")

        (linux_dir / "install-qga-arch.sh").write_text("""#!/bin/bash
set -e
echo "==> Instalando QEMU Guest Agent, Spice VDagent y Autocutsel (para VNC)..."
sudo pacman -S --noconfirm qemu-guest-agent spice-vdagent autocutsel

echo "==> Configurando autocutsel para que arranque con el escritorio..."
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
mkdir -p "$REAL_HOME/.config/autostart"
cat <<EOF > "$REAL_HOME/.config/autostart/autocutsel.desktop"
[Desktop Entry]
Type=Application
Name=Autocutsel
Exec=autocutsel -fork
X-GNOME-Autostart-enabled=true
EOF
chown -R "$REAL_USER:$REAL_USER" "$REAL_HOME/.config/autostart"

echo "==> Configurando módulos del kernel..."
echo -e "virtio_pci\\nvirtio_console\\n9p\\n9pnet_virtio" | sudo tee /etc/modules-load.d/nvm-virtio.conf > /dev/null
sudo modprobe virtio_pci 2>/dev/null || true
sudo modprobe virtio_console 2>/dev/null || true
sudo modprobe 9pnet_virtio 2>/dev/null || true

echo "==> Habilitando servicios..."
sudo systemctl enable --now qemu-guest-agent.service || true
sudo systemctl enable --now spice-vdagentd.service 2>/dev/null || true

echo "==> ¡Listo! Carpetas, SPICE y VNC (portapapeles) configurados."
echo "Por favor, reinicia la máquina virtual."
read -p "Presiona Enter para cerrar..."
""")
        if not IS_WINDOWS:
            for f in linux_dir.glob("*.sh"):
                f.chmod(0o755)

        win_dir = staging / "windows"
        win_dir.mkdir()
        (win_dir / "install-qga.bat").write_text("""@echo off
echo Descargando virtio-win para Windows...
powershell -Command "Invoke-WebRequest -Uri 'https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/virtio-win.iso' -OutFile '%TEMP%\\virtio-win.iso'"
echo Instala manualmente desde %TEMP%\\virtio-win.iso -> virtio-win-gt-x64.msi
pause
""")

        created = False
        for mk in ["mkisofs", "genisoimage", "xorriso"]:
            if shutil.which(mk):
                try:
                    cmd = [mk, "-o", str(iso_path), "-V", "GUEST_TOOLS", "-r", str(staging)]
                    if mk == "xorriso":
                        cmd = [mk, "-as", "mkisofs", "-o", str(iso_path), "-V", "GUEST_TOOLS", "-r", str(staging)]
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    created = True
                    break
                except Exception:
                    continue

        if not created:
            # Windows no trae mkisofs: generamos un ISO 9660/Joliet con Python.
            try:
                create_iso(staging, iso_path)
                created = True
            except Exception as e:
                log.warning(f"No se pudo crear el ISO de Guest Tools: {e}")

        if not created:
            QMessageBox.warning(self.app.parent(), "Herramienta faltante",
                "No se encontró mkisofs/genisoimage/xorriso en el sistema.\n"
                "Instala uno de ellos para crear el ISO de Guest Tools.\n"
                f"Los archivos de instalador están en: {staging}")
            return

        if not iso_path.exists() or iso_path.stat().st_size == 0:
            QMessageBox.critical(self.app.parent(), "Error", "No se pudo crear el ISO de Guest Tools.")
            return

        empty_cd = None
        source_type = SOURCE_EXISTING
        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            if self._storage_type(item) == TIPO_OPTICO:
                st = item.data(2, Qt.ItemDataRole.UserRole)
                path = item.text(2)
                if st in (SOURCE_EMPTY, "Vacío") or not path or path.strip() == "":
                    empty_cd = item
                    break

        if empty_cd:
            empty_cd.setText(2, str(iso_path))
            empty_cd.setText(3, empty_cd.text(3) or tr("SATA/AHCI"))
            empty_cd.setData(2, Qt.ItemDataRole.UserRole, source_type)
            QMessageBox.information(self.app.parent(), "ISO montado",
                f"ISO de Guest Tools montado en unidad óptica existente:\n{iso_path}")
        else:
            item = QTreeWidgetItem(self.tree_storage)
            item.setData(0, Qt.ItemDataRole.UserRole, TIPO_OPTICO)
            item.setText(0, tr(TIPO_OPTICO))
            item.setText(1, tr("CD/DVD"))
            item.setText(2, str(iso_path))
            item.setText(3, tr("SATA/AHCI"))
            item.setData(2, Qt.ItemDataRole.UserRole, source_type)
            item.setData(3, Qt.ItemDataRole.UserRole, "SATA/AHCI")
            item.setData(3, Qt.ItemDataRole.UserRole + 1, "SATA/AHCI")
            self._sync_boot()
            QMessageBox.information(self.app.parent(), "ISO creado y montado",
                f"ISO de Guest Tools creado y montado en nueva unidad óptica:\n{iso_path}")

    def _modify_media(self):
        item = self.tree_storage.currentItem()
        if not item:
            return
        tipo = self._storage_type(item)

        if tipo == TIPO_DISCO:
            disk_data = {
                "name": os.path.basename(item.text(2)),
                "path": item.text(2),
                "size": item.text(3),
                "format": item.data(2, Qt.ItemDataRole.UserRole + 1),
                "type": item.data(2, Qt.ItemDataRole.UserRole + 2),
                "bus": item.data(2, Qt.ItemDataRole.UserRole + 8) or original_key(item.text(1)),
            }
            dlg = DiskDialog(self.app.parent(), disk_data, default_dir=self.app.vms_dir, app=self.app)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_size = dlg.effective_size
                old_size = disk_data.get("size") or "-"
                disk_path = dlg.input_path.text() or dlg.input_file.text()

                # Si el tamaño cambió y el archivo ya existe, agrandarlo de verdad.
                if new_size != old_size and disk_path and os.path.exists(disk_path):
                    try:
                        progress = QProgressDialog(
                            tr("Redimensionando disco..."), None, 0, 0, self.app.parent())
                        progress.setWindowModality(Qt.WindowModality.WindowModal)
                        progress.setCancelButton(None)
                        progress.show()
                        proc = subprocess.Popen(
                            ["qemu-img", "resize", disk_path, new_size],
                            stderr=subprocess.PIPE, text=True)
                        while proc.poll() is None:
                            QApplication.processEvents(); time.sleep(0.1)
                        progress.close()
                        if proc.returncode != 0:
                            raise Exception(proc.stderr.read())
                    except Exception as e:
                        QMessageBox.critical(
                            self.app.parent(), tr("Error"),
                            f"{tr('No se pudo agrandar el disco:')}\n{e}")
                        return

                    self._update_media_size(disk_path, new_size)

                bus = _combo_value(dlg.combo_bus)
                item.setText(1, tr(bus))
                item.setText(2, disk_path)
                item.setText(3, new_size)
                item.setData(2, Qt.ItemDataRole.UserRole + 1, _combo_value(dlg.combo_format))
                item.setData(2, Qt.ItemDataRole.UserRole + 2, _combo_value(dlg.combo_type))
                item.setData(2, Qt.ItemDataRole.UserRole + 3, _combo_value(dlg.combo_cache))
                item.setData(2, Qt.ItemDataRole.UserRole + 4, _combo_value(dlg.combo_io))
                item.setData(2, Qt.ItemDataRole.UserRole + 5, _combo_value(dlg.combo_discard))
                item.setData(2, Qt.ItemDataRole.UserRole + 6, _combo_value(dlg.combo_detect_zeros))
                item.setData(2, Qt.ItemDataRole.UserRole + 7, _combo_value(dlg.combo_aio))
                item.setData(2, Qt.ItemDataRole.UserRole + 8, bus)
                self._sync_boot()
            return

        if tipo == TIPO_OPTICO:
            so = self.combo_so.currentText()
            can_download = self._so_supports_download(so)
            source_type = item.data(2, Qt.ItemDataRole.UserRole) or SOURCE_EMPTY
            cd_data = {
                "path": item.text(2),
                "bus": self._storage_bus(item) or "SATA/AHCI",
            }
            dlg = CDDVDDialog(
                self.app.parent(),
                cd_data,
                default_dir=self.app.isos_dir,
                app=self.app,
                allow_download=can_download,
            )
            if dlg.exec() == QDialog.DialogCode.Accepted:
                source_type = _combo_value(dlg.combo_source)
                bus = _combo_value(dlg.combo_bus)
                item.setText(2, dlg.input_file.text() if source_type == SOURCE_EXISTING else (
                    tr("Descargar automáticamente") if source_type == SOURCE_DOWNLOAD else tr("Vacío")))
                item.setText(3, tr(bus))
                item.setData(2, Qt.ItemDataRole.UserRole, source_type)
                item.setData(3, Qt.ItemDataRole.UserRole, bus)
                item.setData(3, Qt.ItemDataRole.UserRole + 1, bus)
                self._sync_boot()
            return

        if tipo == TIPO_DISQUETE:
            dlg = FloppyDialog(
                self.app.parent(),
                default_dir=self.app.isos_dir,
                app=self.app,
                floppy_data={
                    "name": os.path.basename(item.text(2)) or item.text(2),
                    "path": item.text(2),
                    "size": item.text(3) if item.text(3) != "-" else "1.44 MB",
                },
            )
            if dlg.exec() == QDialog.DialogCode.Accepted:
                item.setText(2, dlg.input_file.text() if dlg.radio_exist.isChecked()
                             else dlg.input_name.text())
                item.setText(3, tr(dlg.combo_size.currentText())
                             if dlg.radio_new.isChecked() else "-")
                self._sync_boot()

    def _compact_media(self):
        """Compacta el disco QCOW2 seleccionado en Almacenamiento."""
        item = self.tree_storage.currentItem()
        if not item:
            QMessageBox.information(
                self.app.parent(), tr("Compactar"),
                tr("Selecciona un dispositivo en la lista."))
            return

        path = item.text(2)
        if self._storage_type(item) != TIPO_DISCO or not path.lower().endswith(".qcow2"):
            QMessageBox.warning(
                self.app.parent(), tr("Compactar"),
                tr("Solo se pueden compactar discos QCOW2."))
            return

        nombre = os.path.basename(path)
        resp = QMessageBox.question(
            self.app.parent(), tr("Compactar"),
            f"{tr('¿Compactar el disco seleccionado?')}\n\n{nombre}")
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            from services.media_library import MediaLibraryManager
            mgr = MediaLibraryManager(self.app.data_dir, self.app.settings)
            success, msg = mgr.compact_disk(path)
        except Exception as e:
            success, msg = False, str(e)

        if success:
            self._update_media_size(path, item.text(3))
            QMessageBox.information(self.app.parent(), tr("Compactar"), tr("Compactado con éxito."))
        else:
            QMessageBox.critical(self.app.parent(), tr("Error"), msg)

    def _delete_media(self):
        item = self.tree_storage.currentItem()
        if not item:
            QMessageBox.information(self.app.parent(), "Eliminar", "Selecciona un dispositivo en la lista.")
            return

        device_type = self._storage_type(item)
        path = item.text(2) if device_type in (TIPO_DISCO, TIPO_OPTICO, TIPO_DISQUETE) else ""

        delete_file = False
        if path and os.path.exists(path):
            resp = QMessageBox.question(
                self.app.parent(), "Eliminar dispositivo",
                f"¿Eliminar '{device_type}' de la configuración?\n\nArchivo: {path}\n\n"
                "Selecciona 'Sí' para eliminar solo de la configuración, "
                "'No' para eliminar también el archivo físico del disco.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if resp == QMessageBox.StandardButton.Cancel:
                return
            delete_file = (resp == QMessageBox.StandardButton.No)
        else:
            resp = QMessageBox.question(
                self.app.parent(), "Eliminar dispositivo",
                f"¿Eliminar '{device_type}' de la configuración?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if resp == QMessageBox.StandardButton.Cancel:
                return

        idx = self.tree_storage.indexOfTopLevelItem(item)
        self.tree_storage.takeTopLevelItem(idx)
        self._sync_boot()

        if delete_file and path and os.path.exists(path):
            try:
                os.remove(path)
                QMessageBox.information(
                    self.app.parent(), "Eliminado",
                    f"Dispositivo y archivo eliminados:\n{path}")
            except Exception as e:
                QMessageBox.critical(
                    self.app.parent(), "Error al eliminar archivo",
                    f"No se pudo eliminar el archivo:\n{path}\n\n{e}")

    def _host_mount_unavailable(self):
        """Aviso claro en Windows: no hay mount/qemu-nbd de Linux."""
        QMessageBox.information(
            self.app.parent(), tr("Montar/Desmontar"),
            tr("El montaje de imágenes en el host no está disponible en Windows."))

    def _open_in_file_manager(self, path):
        """Abre una carpeta con el explorador del sistema operativo."""
        try:
            if IS_WINDOWS:
                os.startfile(str(path))  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self.app.parent(), tr("Error"), str(e))

    def _mount_eject_media(self):
        """Montar/Desmontar ISO en la unidad óptica o disco virtual seleccionado."""
        item = self.tree_storage.currentItem()
        if not item:
            QMessageBox.information(self.app.parent(), "Montar/Desmontar", "Selecciona una unidad en la lista.")
            return
        
        vm = self.app.get_vm(self.current_vm_id)
        if not vm:
            QMessageBox.warning(self.app.parent(), "Error", "No se encontró la VM.")
            return
        
        device_type = self._storage_type(item)

        if device_type == TIPO_OPTICO:
            self._mount_eject_cdrom(item, vm)
        elif device_type == TIPO_DISCO:
            self._mount_eject_disk(item, vm)
        else:
            QMessageBox.information(self.app.parent(), "Montar/Desmontar", "Esta opción solo funciona para unidades ópticas y discos duros.")

    def _mount_eject_cdrom(self, item, vm):
        """Menú para unidad óptica: insertar/expulsar de la VM o montar el ISO en el host."""
        current_path = item.text(2)
        current_source = item.data(2, Qt.ItemDataRole.UserRole) or SOURCE_EMPTY
        has_iso = (current_source == SOURCE_EXISTING
                   and current_path and os.path.exists(current_path))

        from PyQt6.QtWidgets import QInputDialog

        options = []
        if has_iso:
            if not IS_WINDOWS:
                options.append("Montar ISO en el host" if not self._get_mount_info(current_path) else "Desmontar ISO del host")
            options.append("Expulsar ISO de la VM")
        else:
            options.append("Insertar ISO en la VM")
            if not IS_WINDOWS:
                options.append("Montar ISO en el host")

        visibles = [tr(opcion) for opcion in options]
        choice, ok = QInputDialog.getItem(
            self.app.parent(), tr("Unidad óptica"),
            tr("¿Qué deseas hacer?"), visibles, 0, False)
        if not ok or not choice:
            return
        # Comparar siempre la clave original, aunque la lista esté traducida.
        accion = options[visibles.index(choice)] if choice in visibles else choice

        if accion == "Montar ISO en el host":
            iso_path = current_path if has_iso else None
            if not iso_path:
                iso_path, _ = QFileDialog.getOpenFileName(
                    self.app.parent(), "Seleccionar ISO para montar en el host", "",
                    "Imágenes (*.iso *.img *.dmg)")
            if iso_path and os.path.exists(iso_path):
                self._mount_iso_host(iso_path, item, vm)
        elif accion == "Desmontar ISO del host":
            info = self._get_mount_info(current_path)
            if info:
                self._unmount_iso_host(info.get("mount_point"), current_path, item)
        elif accion == "Expulsar ISO de la VM":
            self._eject_iso_from_vm(item, vm)
        elif accion == "Insertar ISO en la VM":
            self._insert_iso_into_vm(item, vm)

    def _eject_iso_from_vm(self, item, vm):
        """Expulsa el ISO actual de la unidad óptica de la VM."""
        cdrom_index = 0
        for i in range(self.tree_storage.topLevelItemCount()):
            if self.tree_storage.topLevelItem(i) == item:
                cdrom_index = i
                break
        cdrom_id = f"cdrom{cdrom_index}"
        current_path = item.text(2)

        resp = QMessageBox.question(
            self.app.parent(), "Expulsar ISO",
            f"Expulsar el ISO de la unidad óptica de la VM?\n\n{current_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return

        if vm.get("state") == "Running":
            ok, msg = self.app.runner.eject_cdrom(self.current_vm_id, cdrom_id)
            if ok:
                QMessageBox.information(self.app.parent(), "Expulsado", msg)
                item.setText(2, "Vacío")
                item.setData(2, Qt.ItemDataRole.UserRole, "Mantener vacío")
                self._sync_boot()
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)
        else:
            item.setText(2, "Vacío")
            item.setData(2, Qt.ItemDataRole.UserRole, "Mantener vacío")
            self._sync_boot()
            QMessageBox.information(self.app.parent(), "Expulsado", "ISO quitada de la unidad (la VM está apagada).")

    def _insert_iso_into_vm(self, item, vm):
        """Selecciona e inserta un ISO en la unidad óptica de la VM."""
        cdrom_index = 0
        for i in range(self.tree_storage.topLevelItemCount()):
            if self.tree_storage.topLevelItem(i) == item:
                cdrom_index = i
                break
        cdrom_id = f"cdrom{cdrom_index}"

        p, _ = QFileDialog.getOpenFileName(
            self.app.parent(), "Seleccionar ISO para insertar en la VM", "",
            "Imágenes (*.iso *.img *.dmg)")
        if not p:
            return

        if vm.get("state") == "Running":
            ok, msg = self.app.runner.hotplug_cdrom(self.current_vm_id, cdrom_id, p)
            if ok:
                QMessageBox.information(self.app.parent(), "Insertado", msg)
                item.setText(2, p)
                item.setData(2, Qt.ItemDataRole.UserRole, "Usar ISO/IMG/DMG existente")
                self._sync_boot()
                self._apply_mount_marker(item, p)
            else:
                QMessageBox.critical(self.app.parent(), "Error", msg)
        else:
            item.setText(2, p)
            item.setData(2, Qt.ItemDataRole.UserRole, "Usar ISO/IMG/DMG existente")
            self._sync_boot()
            self._apply_mount_marker(item, p)
            QMessageBox.information(self.app.parent(), "Insertado", f"ISO configurada para próximo arranque:\n{p}")

    def _mount_iso_host(self, iso_path, item, vm):
        """Monta un ISO/imagen óptica en el host con mount -o loop (solo lectura si la VM está encendida)."""
        import subprocess, tempfile, uuid, shutil, os as _os

        if IS_WINDOWS:
            self._host_mount_unavailable()
            return

        sudo = shutil.which("sudo")
        if not sudo:
            QMessageBox.critical(self.app.parent(), "Error montando",
                "No se encontró 'sudo'. No se puede montar sin privilegios de root.")
            return

        def run_priv(cmd_args, timeout=60):
            return subprocess.run(["sudo"] + list(cmd_args),
                                  capture_output=True, text=True, timeout=timeout)

        # Punto de montaje como usuario
        mount_base = Path(tempfile.gettempdir()) / "vm-disk-mounts"
        mount_base.mkdir(parents=True, exist_ok=True)
        mount_point = mount_base / f"iso_{uuid.uuid4().hex[:8]}"
        mount_point.mkdir(parents=True, exist_ok=True)

        # La VM encendida puede tener el ISO abierto: forzar solo lectura
        vm_running = bool(vm and vm.get("state") == "Running")
        read_only = vm_running

        resp = QMessageBox.question(
            self.app.parent(), "Montar ISO en el host",
            f"Montar el ISO en el host?\n\n{iso_path}\n\n"
            + ("La VM está encendida, se montará en SOLO LECTURA.\n\n" if vm_running else "")
            + "Se abrirá el explorador de archivos en el punto de montaje.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            try:
                _os.rmdir(mount_point)
            except Exception:
                pass
            return

        def _try_mount(ro):
            opts = "loop,ro" if ro else "loop"
            return run_priv(["mount", "-o", opts, iso_path, str(mount_point)], timeout=30)

        r = _try_mount(read_only)
        if r.returncode != 0 and not read_only:
            # Fallback: reintentar en solo lectura (ISO con metadatos raros, permisos, etc.)
            r = _try_mount(True)
            if r.returncode == 0:
                read_only = True

        if r.returncode != 0:
            QMessageBox.critical(self.app.parent(), "Error montando",
                (r.stderr or r.stdout or "mount falló").strip())
            try:
                _os.rmdir(mount_point)
            except Exception:
                pass
            return

        # Registrar montaje persistente y marcar la fila
        mount_info = {
            "mount_point": str(mount_point),
            "selected_dev": iso_path,
            "mount_type": "iso",
            "base_device": iso_path,
            "read_only": bool(read_only),
        }
        self._register_mount(iso_path, mount_info)
        self._apply_mount_marker(item, iso_path)

        self._open_in_file_manager(mount_point)

        QMessageBox.information(
            self.app.parent(), "ISO Montado",
            "ISO montado en:\n" + str(mount_point) + "\n\n"
            + ("Montado en SOLO LECTURA (la VM está encendida).\n\n" if read_only else "")
            + "Pulsa 'Montar/Desmontar' de nuevo para desmontar.")

    def _unmount_iso_host(self, mount_point, iso_path, item):
        """Desmonta un ISO montado en el host."""
        import subprocess, shutil, os as _os

        if IS_WINDOWS:
            self._host_mount_unavailable()
            return

        sudo = shutil.which("sudo")
        if not sudo:
            QMessageBox.critical(self.app.parent(), "Error desmontando", "No se encontró 'sudo'.")
            return

        try:
            subprocess.run(["sudo", "umount", str(mount_point)],
                           capture_output=True, text=True, timeout=30)
        except Exception as e:
            log.warning(f"umount ISO falló: {e}")

        try:
            _os.rmdir(mount_point)
        except Exception:
            pass

        self._unregister_mount(iso_path)
        try:
            self._apply_mount_marker(item, iso_path)
        except Exception:
            pass

        QMessageBox.information(self.app.parent(), "Desmontado", "ISO desmontado correctamente del host.")

    def _mount_eject_disk(self, item, vm):
        """Montar/Desmontar disco virtual en el HOST usando qemu-nbd/losetup."""
        import subprocess

        if IS_WINDOWS:
            self._host_mount_unavailable()
            return

        current_path = item.text(2)
        disk_data = item.data(2, Qt.ItemDataRole.UserRole) or "EXISTING"
        
        # Verificar si ya está montado (registro persistente + comprobación real)
        mount_info = self._get_mount_info(current_path) if current_path else None
        
        if mount_info:
            # YA MONTADO -> DESMONTAR
            mount_point = mount_info.get("mount_point", "")
            resp = QMessageBox.question(
                self.app.parent(), "Desmontar Disco",
                f"Desmontar el disco del host?\n\nPunto de montaje: {mount_point}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._unmount_disk_image(mount_point, current_path, item, mount_info)
            return
        
        # NO MONTADO -> MONTAR
        if not current_path or not os.path.exists(current_path):
            QMessageBox.warning(self.app.parent(), "Montar Disco", "Selecciona un archivo de disco válido primero (botón Modificar).")
            return
        
        # Verificar si la VM está usando este disco (bloqueo de escritura de QEMU)
        vm = self.app.get_vm(self.current_vm_id) if hasattr(self, 'current_vm_id') else None
        if vm and vm.get("state") == "Running":
            QMessageBox.critical(
                self.app.parent(), "Disco en uso",
                "No se puede montar el disco en el host porque la VM está en ejecución.\n\n"
                "QEMU mantiene un bloqueo de escritura sobre la imagen.\n"
                "Apaga la VM primero e inténtalo de nuevo."
            )
            return

        # Preguntar modo de montaje
        resp = QMessageBox.question(
            self.app.parent(), "Montar Disco",
            f"Montar imagen de disco en el host?\n\n{current_path}\n\nSe abrirá el explorador de archivos en el punto de montaje.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        
        self._mount_disk_image(current_path, item)

    def _mount_disk_image(self, disk_path, item):
        """Monta una imagen de disco en el host usando sudo (root) para qemu-nbd/losetup+mount."""
        import subprocess, tempfile, uuid, shutil, os as _os
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox, QCheckBox

        if IS_WINDOWS:
            self._host_mount_unavailable()
            return

        sudo = shutil.which("sudo")
        if not sudo:
            QMessageBox.critical(self.app.parent(), "Error montando",
                "No se encontró 'sudo'. No se puede montar discos sin privilegios de root.")
            return

        def run_priv(cmd_args, timeout=60):
            """Ejecuta una lista de argumentos con sudo (cada comando usa su entrada sudoers)."""
            try:
                r = subprocess.run(["sudo"] + list(cmd_args),
                                   capture_output=True, text=True, timeout=timeout)
                return r
            except Exception as e:
                raise RuntimeError(f"No se pudo ejecutar con privilegios: {e}")

        def run_priv_shell(script_text, timeout=60):
            """Ejecuta un script shell con sudo bash (requiere que bash esté en sudoers)."""
            tmp_script = tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False)
            tmp_script.write(script_text)
            tmp_script.close()
            _os.chmod(tmp_script.name, 0o755)
            try:
                r = subprocess.run(["sudo", "bash", tmp_script.name],
                                   capture_output=True, text=True, timeout=timeout)
                return r
            finally:
                try:
                    _os.unlink(tmp_script.name)
                except Exception:
                    pass

        ext = _os.path.splitext(disk_path)[1].lower().lstrip(".")

        # Mapear extensiones a formatos reconocidos por qemu-nbd.
        nbd_formats = {
            "qcow2": "qcow2", "qcow": "qcow",
            "vdi": "vdi", "vmdk": "vmdk",
            "vhd": "vpc", "vhdx": "vhdx", "vpc": "vpc",
        }
        fmt = nbd_formats.get(ext)

        # Crear punto de montaje como usuario (no necesita root)
        mount_base = Path(tempfile.gettempdir()) / "vm-disk-mounts"
        mount_base.mkdir(parents=True, exist_ok=True)
        mount_point = mount_base / f"disk_{uuid.uuid4().hex[:8]}"
        mount_point.mkdir(parents=True, exist_ok=True)

        # Escapar comillas simples para el script shell
        disk_q = disk_path.replace("'", "'\\''")
        mp_q = str(mount_point).replace("'", "'\\''")
        fmt_q = fmt.replace("'", "'\\''") if fmt else ""

        # Paso 1: Conectar el dispositivo
        device = None
        mount_type = None
        partitions = []
        base_fstype = ""

        try:
            if fmt is not None:
                # Desconectar nbds previos que tengan esta misma imagen
                for i in range(16):
                    nbd_check = f"/dev/nbd{i}"
                    if not _os.path.exists(nbd_check):
                        continue
                    r_list_check = run_priv(["qemu-nbd", "--list", nbd_check], timeout=5)
                    if disk_q.strip("'") in (r_list_check.stdout or ""):
                        run_priv(["qemu-nbd", "--disconnect", nbd_check], timeout=15)

                # Cargar módulo nbd si es necesario
                run_priv(["modprobe", "nbd", "max_part=16"], timeout=15)

                # Conectar al primer nbd libre que funcione
                connected = False
                last_err = ""
                for i in range(16):
                    cand = f"/dev/nbd{i}"
                    if not _os.path.exists(cand):
                        continue
                    if _os.path.exists(f"/sys/block/nbd{i}/pid"):
                        continue  # nbd con proceso activo
                    r_try = run_priv(["qemu-nbd", "--connect=" + cand,
                                      "--format=" + fmt_q, disk_path], timeout=60)
                    if r_try.returncode == 0:
                        device = cand
                        mount_type = "nbd"
                        connected = True
                        break
                    last_err = (r_try.stderr or r_try.stdout or "").strip()

                if not connected:
                    raise RuntimeError("No se pudo conectar el NBD: " + last_err)

                # Esperar a que el kernel detecte las particiones
                import time as _time
                _time.sleep(1.5)

                # Listar particiones en formato lista (sin caracteres de árbol)
                r_parts = subprocess.run(
                    ["lsblk", "-l", "-n", "-o", "NAME,SIZE,TYPE,FSTYPE", device],
                    capture_output=True, text=True, timeout=15)
                for line in r_parts.stdout.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == "part":
                        dev_path = "/dev/" + parts[0]
                        size = parts[1]
                        fstype = parts[3] if len(parts) >= 4 else ""
                        partitions.append((dev_path, size, fstype))
                    elif len(parts) >= 3 and parts[2] == "disk":
                        # FSTYPE del disco base (vacío si contiene una tabla de particiones)
                        base_fstype = parts[3] if len(parts) >= 4 else ""

            elif ext in ("raw", "img", "dd"):
                # Loop device
                r_loop = run_priv(["losetup", "-f", "--show", disk_path], timeout=60)
                if r_loop.returncode != 0:
                    raise RuntimeError((r_loop.stderr or r_loop.stdout or "losetup falló").strip())
                device = r_loop.stdout.strip().splitlines()[-1].strip()
                mount_type = "loop"

                # Escanear particiones
                run_priv(["partprobe", device], timeout=15)
                import time as _time
                _time.sleep(0.5)

                r_parts = subprocess.run(
                    ["lsblk", "-l", "-n", "-o", "NAME,SIZE,TYPE,FSTYPE", device],
                    capture_output=True, text=True, timeout=15)
                for line in r_parts.stdout.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == "part":
                        dev_path = "/dev/" + parts[0]
                        size = parts[1]
                        fstype = parts[3] if len(parts) >= 4 else ""
                        partitions.append((dev_path, size, fstype))
                    elif len(parts) >= 3 and parts[2] == "disk":
                        base_fstype = parts[3] if len(parts) >= 4 else ""
            else:
                QMessageBox.critical(self.app.parent(), "Error montando",
                    f"Formato no soportado para montaje en host: {ext}")
                self._cleanup_failed_mount(item)
                return

        except Exception as e:
            QMessageBox.critical(self.app.parent(), "Error conectando", str(e))
            self._cleanup_failed_mount(item)
            return

        # Paso 2: Mostrar diálogo para seleccionar partición (o disco entero)
        dlg = QDialog(self.app.parent())
        dlg.setWindowTitle("Seleccionar partición a montar")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        lbl = QLabel("Selecciona la partición que deseas montar en el host:\n" + disk_path)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        combo = QComboBox()
        # Opción "disco entero" solo si el dispositivo base tiene un filesystem propio
        # (si contiene una tabla de particiones, montarlo como bloque falla)
        if base_fstype:
            combo.addItem("Disco entero (" + device + ", " + base_fstype + ")", device)
        # Opciones: particiones (omitir las sin filesystem, no son montables)
        for dev_path, size, fstype in partitions:
            if not fstype:
                continue
            label = dev_path + "  (" + size + ", " + fstype + ")"
            combo.addItem(label, dev_path)
        if combo.count() == 0:
            QMessageBox.warning(
                self.app.parent(), "Sin particiones montables",
                "No se encontraron particiones con un sistema de archivos reconocible "
                "que puedan montarse en el host.")
            try:
                if mount_type == "nbd":
                    run_priv(["qemu-nbd", "--disconnect", device], timeout=15)
                elif mount_type == "loop":
                    run_priv(["losetup", "-d", device], timeout=15)
            except Exception:
                pass
            try:
                _os.rmdir(mount_point)
            except Exception:
                pass
            return
        layout.addWidget(combo)

        ro_check = QCheckBox("Montar en solo lectura (seguro si Windows no se apagó limpiamente)")
        ro_check.setChecked(False)
        layout.addWidget(ro_check)
        layout.addWidget(QLabel(
            "Si el disco NTFS está 'sucio' (Windows en hibernación/inicio rápido), "
            "el montaje de lectura-escritura fallará. Marca la casilla para montarlo en solo lectura."))

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            # Usuario canceló: desconectar y limpiar
            try:
                if mount_type == "nbd":
                    run_priv(["qemu-nbd", "--disconnect", device], timeout=15)
                elif mount_type == "loop":
                    run_priv(["losetup", "-d", device], timeout=15)
            except Exception:
                pass
            try:
                _os.rmdir(mount_point)
            except Exception:
                pass
            return

        selected_dev = combo.currentData()
        want_ro = ro_check.isChecked()

        # Paso 3: Montar la selección elegida (con fallback automático a solo lectura)
        def _try_mount(read_only):
            args = ["mount"]
            if read_only:
                args += ["-o", "ro"]
            args += [selected_dev, str(mount_point)]
            return run_priv(args, timeout=30)

        r_mount = _try_mount(want_ro)
        if r_mount.returncode != 0 and not want_ro:
            # Fallback automático: reintentar en solo lectura (NTFS sucio, etc.)
            r_mount = _try_mount(True)
            if r_mount.returncode == 0:
                want_ro = True

        if r_mount.returncode != 0:
            QMessageBox.critical(self.app.parent(), "Error montando",
                (r_mount.stderr or r_mount.stdout or "mount falló").strip())
            # Desconectar el dispositivo ya que falló el mount
            try:
                if mount_type == "nbd":
                    run_priv(["qemu-nbd", "--disconnect", device], timeout=15)
                elif mount_type == "loop":
                    run_priv(["losetup", "-d", device], timeout=15)
            except Exception:
                pass
            try:
                _os.rmdir(mount_point)
            except Exception:
                pass
            self._cleanup_failed_mount(item)
            return

        # Guardar info persistente para desmontar y marcar la fila
        mount_info = {
            "mount_point": str(mount_point),
            "selected_dev": selected_dev,
            "mount_type": mount_type,
            "base_device": device,
            "read_only": bool(want_ro),
        }
        self._register_mount(disk_path, mount_info)
        item.setData(2, Qt.ItemDataRole.UserRole + 10, str(mount_point))
        item.setData(2, Qt.ItemDataRole.UserRole + 11, selected_dev)
        item.setData(2, Qt.ItemDataRole.UserRole + 12, mount_type)
        item.setData(2, Qt.ItemDataRole.UserRole + 13, device)
        self._apply_mount_marker(item, disk_path)

        # Abrir explorador de archivos
        self._open_in_file_manager(mount_point)

        QMessageBox.information(
            self.app.parent(), "Disco Montado",
            "Imagen montada en:\n" + str(mount_point) + "\n\n"
            + ("Montado en SOLO LECTURA (el disco estaba 'sucio').\n\n" if want_ro else "")
            + "Pulsa 'Montar/Desmontar' de nuevo para desmontar."
        )

    def _unmount_disk_image(self, mount_point, disk_path, item, mount_info=None):
        """Desmonta y limpia recursos usando sudo (root) para umount/qemu-nbd/losetup."""
        import subprocess, shutil, os as _os

        if IS_WINDOWS:
            self._host_mount_unavailable()
            return

        sudo = shutil.which("sudo")
        if not sudo:
            QMessageBox.critical(self.app.parent(), "Error desmontando",
                "No se encontró 'sudo'.")
            return

        def run_priv(cmd_args, timeout=30):
            """Ejecuta una lista de argumentos con sudo."""
            try:
                return subprocess.run(["sudo"] + list(cmd_args),
                                       capture_output=True, text=True, timeout=timeout)
            except Exception as e:
                raise RuntimeError(f"No se pudo ejecutar con privilegios: {e}")

        mount_info = mount_info or {}
        mount_type = mount_info.get("mount_type") or item.data(2, Qt.ItemDataRole.UserRole + 12) or ""
        device = mount_info.get("selected_dev") or item.data(2, Qt.ItemDataRole.UserRole + 11) or ""
        base_device = mount_info.get("base_device") or item.data(2, Qt.ItemDataRole.UserRole + 13) or ""
        mp_q = str(mount_point)

        # Desmontar
        try:
            run_priv(["umount", mp_q], timeout=30)
        except Exception as e:
            log.warning(f"sudo umount falló: {e}")

        # Desconectar dispositivo base (nbd o loop)
        if base_device:
            try:
                if mount_type == "nbd":
                    run_priv(["qemu-nbd", "--disconnect", base_device], timeout=15)
                elif mount_type == "loop":
                    run_priv(["losetup", "-d", base_device], timeout=15)
            except Exception as e:
                log.warning(f"sudo disconnect falló: {e}")

        # Limpiar directorio como usuario
        try:
            _os.rmdir(mount_point)
        except Exception:
            pass

        # Limpiar registro persistente y marca visual
        self._unregister_mount(disk_path)
        try:
            self._apply_mount_marker(item, disk_path)
        except Exception:
            pass

        # Limpiar datos del item
        item.setData(2, Qt.ItemDataRole.UserRole + 10, "")
        item.setData(2, Qt.ItemDataRole.UserRole + 11, "")
        item.setData(2, Qt.ItemDataRole.UserRole + 12, "")
        item.setData(2, Qt.ItemDataRole.UserRole + 13, "")

        QMessageBox.information(self.app.parent(), "Desmontado", "Disco desmontado correctamente del host.")
    def _find_free_nbd(self):
        """Encuentra un dispositivo NBD libre (/dev/nbdX)."""
        for i in range(16):
            nbd = f"/dev/nbd{i}"
            if not os.path.exists(nbd):
                continue
            # Verificar si está en uso
            result = subprocess.run(["qemu-nbd", "--list", nbd], capture_output=True, text=True)
            if "in use" not in result.stdout.lower() and "connected" not in result.stdout.lower():
                return nbd
        return None

    def _find_free_loop(self):
        """Encuentra un loop device libre."""
        result = subprocess.run(["losetup", "-f"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None

    def _ensure_nbd_module(self):
        """Intenta cargar el módulo del kernel nbd con privilegios de root (sudo)."""
        import subprocess, time
        sudo = shutil.which("sudo")
        if not sudo:
            log.warning("sudo no está disponible; no se puede cargar el módulo nbd automáticamente.")
            return
        cmds = [
            ["sudo", "modprobe", "nbd", "max_part=16"],
        ]
        for cmd in cmds:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    # Esperar a que aparezcan los dispositivos /dev/nbdX
                    for _ in range(10):
                        if any(Path(f"/dev/nbd{i}").exists() for i in range(16)):
                            return
                        time.sleep(0.5)
                    return
            except FileNotFoundError:
                continue
            except Exception:
                continue
        log.warning("No se pudo cargar el módulo nbd automáticamente (se requieren privilegios de root).")

    def _list_partitions(self, device):
        """Lista particiones de un dispositivo bloque."""
        result = subprocess.run(["lsblk", "-n", "-o", "NAME", device], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().split('\n')
        # El primer dispositivo es el padre, los siguientes son particiones
        partitions = [f"/dev/{line.strip()}" for line in lines[1:] if line.strip()]
        return partitions

    def _cleanup_failed_mount(self, item):
        """Limpia recursos si el montaje falló."""
        mount_point = item.data(2, Qt.ItemDataRole.UserRole + 10) or ""
        device = item.data(2, Qt.ItemDataRole.UserRole + 11) or ""
        mount_type = item.data(2, Qt.ItemDataRole.UserRole + 12) or ""
        if mount_point:
            subprocess.run(["umount", "-f", mount_point], check=False, capture_output=True)
            try:
                os.rmdir(mount_point)
            except:
                pass
        if device:
            if mount_type == "nbd":
                subprocess.run(["qemu-nbd", "--disconnect", device], check=False)
            elif mount_type == "loop":
                subprocess.run(["losetup", "-d", device], check=False)
        
        item.setData(2, Qt.ItemDataRole.UserRole + 10, "")
        item.setData(2, Qt.ItemDataRole.UserRole + 11, "")
        item.setData(2, Qt.ItemDataRole.UserRole + 12, "")

    def _mount_registry_path(self):
        """Ruta del JSON que recuerda los discos montados en el host."""
        try:
            base = self.app.data_dir
        except Exception:
            base = Path.home() / ".local" / "share" / "virtual-machine"
        return Path(base) / "host_mounts.json"

    def _load_mount_registry(self):
        """Carga el registro persistente de discos montados (dict path -> info)."""
        import json
        p = self._mount_registry_path()
        try:
            if p.exists():
                return json.loads(p.read_text())
        except Exception as e:
            log.warning(f"No se pudo leer el registro de montajes: {e}")
        return {}

    def _save_mount_registry(self, data):
        import json
        p = self._mount_registry_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning(f"No se pudo guardar el registro de montajes: {e}")

    def _register_mount(self, disk_path, info):
        reg = self._load_mount_registry()
        reg[disk_path] = info
        self._save_mount_registry(reg)

    def _unregister_mount(self, disk_path):
        reg = self._load_mount_registry()
        if disk_path in reg:
            del reg[disk_path]
            self._save_mount_registry(reg)

    def _get_mount_info(self, disk_path):
        """Devuelve info de montaje si el disco sigue realmente montado."""
        reg = self._load_mount_registry()
        info = reg.get(disk_path)
        if not info:
            return None
        mp = info.get("mount_point", "")
        if mp and os.path.ismount(mp):
            return info
        reg.pop(disk_path, None)
        self._save_mount_registry(reg)
        return None

    def _detect_image_format(self, path):
        """Detecta el formato real de una imagen de disco usando qemu-img info."""
        import subprocess
        try:
            r = subprocess.run(["qemu-img", "info", path],
                               capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                for line in r.stdout.splitlines():
                    if line.lower().startswith("file format:"):
                        fmt = line.split(":", 1)[1].strip().lower()
                        # Mapear nombres de qemu-img a los usados por QEMU -drive -format
                        mapping = {"vpc": "vpc", "vhd": "vpc", "qcow2": "qcow2",
                                   "qcow": "qcow", "raw": "raw", "vdi": "vdi",
                                   "vmdk": "vmdk", "vhdx": "vhdx"}
                        return mapping.get(fmt, fmt)
        except Exception as e:
            log.warning(f"No se pudo detectar formato de {path}: {e}")
        # Fallback: inferir por extensión
        ext = os.path.splitext(path)[1].lower()
        return {"img":"raw", "vdi":"vdi", "vmdk":"vmdk", "vhd":"vpc", "vhdx":"vhdx"}.get(ext, "qcow2")

    def _apply_mount_marker(self, item, disk_path):
        """Marca visualmente en la fila si el disco está montado en el host."""
        info = self._get_mount_info(disk_path) if disk_path else None
        if info:
            mp = info.get("mount_point", "")
            mode = tr(" (solo lectura)") if info.get("read_only") else ""
            item.setText(4, tr("🔌 Montado") + mode)
            item.setToolTip(4, tr("Montado en el host:") + " " + mp)
            from PyQt6.QtGui import QBrush, QColor
            for col in range(5):
                item.setBackground(col, QBrush(QColor(198, 239, 206)))
        else:
            item.setText(4, "")
            item.setToolTip(4, "")

    def _boot_label(self, clave):
        """Etiqueta visible de una entrada de arranque con clave canónica."""
        if " — " in clave:
            tipo, resto = clave.split(" — ", 1)
            return f"{tr(tipo)} — {resto}"
        return tr(clave)

    def _boot_key(self, entrada):
        """Clave canónica de una entrada guardada, incluso si está traducida."""
        if " — " in entrada:
            tipo, resto = entrada.split(" — ", 1)
            for clave in (TIPO_DISCO, TIPO_OPTICO, TIPO_DISQUETE):
                if tipo == clave or tipo == tr(clave):
                    return f"{clave} — {resto}"
        return original_key(entrada)

    def _retranslate_boot(self):
        for i in range(self.list_boot.count()):
            entrada = self.list_boot.item(i)
            clave = entrada.data(Qt.ItemDataRole.UserRole)
            if clave:
                entrada.setText(self._boot_label(clave))

    def _sync_boot(self):
        self.list_boot.clear()
        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            tipo = self._storage_type(item)
            entrada = QListWidgetItem(f"{tr(tipo)} — {item.text(2)}")
            # El dato guardado siempre usa la clave española estable.
            entrada.setData(Qt.ItemDataRole.UserRole, f"{tipo} — {item.text(2)}")
            self.list_boot.addItem(entrada)
        entrada = QListWidgetItem(tr("Red/PXE"))
        entrada.setData(Qt.ItemDataRole.UserRole, "Red/PXE")
        self.list_boot.addItem(entrada)

    def _move_boot(self, d):
        r = self.list_boot.currentRow()
        if r >= 0 and 0 <= r + d < self.list_boot.count():
            it = self.list_boot.takeItem(r); self.list_boot.insertItem(r + d, it); self.list_boot.setCurrentRow(r + d)

    def _rebuild_net_list(self):
        self.list_net.clear()
        for net in self._network_data:
            extra = ""
            if net.get("backend") != "NAT / Internet" and net.get("bridge"): extra = f" [{net['bridge']}]"
            elif net.get("nat_rules"): extra = f" ({len(net['nat_rules'])} {tr('reglas NAT')})"
            if net.get("mac"): extra += f" MAC:{net['mac']}"
            self.list_net.addItem(f"{tr(net.get('name', 'Red 1'))} — {net.get('model', 'VirtIO')} — {net.get('backend', 'NAT / Internet')}{extra}")

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
            item.setText(3, tr(d.get("iommu", "N/A")))
            item.setText(4, tr(d.get("status", "")))
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

        # Bloqueamos señales para evitar dobles fetches al cargar la VM.
        idx = self.combo_platform.findText(vm.get("platform", "GNU / Linux"))
        if idx >= 0:
            self.combo_platform.blockSignals(True)
            self.combo_platform.setCurrentIndex(idx)
            self.combo_platform.blockSignals(False)
        self._on_platform_changed(False)

        idx = self.combo_so.findText(vm.get("so", ""))
        if idx >= 0:
            self.combo_so.blockSignals(True)
            self.combo_so.setCurrentIndex(idx)
            self.combo_so.blockSignals(False)
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

        self.check_free_page_reporting.setChecked(vm.get("free_page_reporting", True))

        self.combo_console_proto.setCurrentIndex(vm.get("console_proto_idx", 0))
        self.combo_console_mode.setCurrentIndex(vm.get("console_mode_idx", 0))
        self.combo_graphics.setCurrentIndex(vm.get("graphics_idx", 0))
        self.combo_vram.setCurrentIndex(vm.get("vram_idx", 0))

        self._update_display_options()

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
            it.setData(0, Qt.ItemDataRole.UserRole, TIPO_DISCO)
            it.setText(0, tr(TIPO_DISCO))
            bus_type = vm.get("disk_bus", "sata").lower()
            if "virtio" in bus_type: it.setText(1, tr("VirtIO-BLK"))
            elif "nvme" in bus_type: it.setText(1, tr("NVMe"))
            else: it.setText(1, tr("SATA/AHCI"))
            it.setText(2, vm["disk_path"])
            it.setText(3, vm.get("disk_size", "20G"))
            self._apply_mount_marker(it, vm["disk_path"])

        optical_drives = vm.get("optical_drives") or []
        if not optical_drives and (vm.get("iso_path") or vm.get("iso_source_type")):
            optical_drives = [{
                "path": vm.get("iso_path") or "",
                "source_type": vm.get("iso_source_type", "Usar ISO/IMG/DMG existente"),
                "bus": vm.get("cdrom_bus", "SATA/AHCI"),
            }]
        known_paths = {d.get("path") for d in optical_drives}
        prefijo_optico = f"{TIPO_OPTICO} — "
        for entry in (vm.get("boot_order") or []):
            clave_entrada = self._boot_key(entry)
            if clave_entrada.startswith(prefijo_optico):
                p = clave_entrada[len(prefijo_optico):]
                if p and p not in known_paths and p not in ("Descargar automáticamente", "Vacío"):
                    exists = os.path.exists(p)
                    optical_drives.append({
                        "path": p if exists else "",
                        "source_type": SOURCE_EXISTING if exists else SOURCE_EMPTY,
                        "bus": vm.get("cdrom_bus", "SATA/AHCI"),
                    })
                    known_paths.add(p)
        for drive in optical_drives:
            it = QTreeWidgetItem(self.tree_storage)
            it.setData(0, Qt.ItemDataRole.UserRole, TIPO_OPTICO)
            it.setText(0, tr(TIPO_OPTICO))
            it.setText(1, tr("CD/DVD"))
            path = drive.get("path", "")
            source_type = original_key(drive.get("source_type", SOURCE_EMPTY))
            if path and os.path.exists(path):
                it.setText(2, path)
            elif source_type == SOURCE_DOWNLOAD:
                it.setText(2, tr("Descargar automáticamente"))
            else:
                it.setText(2, tr("Vacío"))
            bus = original_key(drive.get("bus", "SATA/AHCI"))
            it.setText(3, tr(bus))
            it.setData(3, Qt.ItemDataRole.UserRole, bus)
            it.setData(3, Qt.ItemDataRole.UserRole + 1, bus)
            it.setData(2, Qt.ItemDataRole.UserRole, source_type)
            self._apply_mount_marker(it, path if path else "")

        if vm.get("floppy_path"):
            it = QTreeWidgetItem(self.tree_storage)
            it.setData(0, Qt.ItemDataRole.UserRole, TIPO_DISQUETE)
            it.setText(0, tr(TIPO_DISQUETE)); it.setText(1, "FDC")
            it.setText(2, vm["floppy_path"]); it.setText(3, "-")

        self._sync_boot()

        boot_order = vm.get("boot_order")
        if boot_order:
            self.list_boot.clear()
            for entry in boot_order:
                clave = self._boot_key(entry)
                entrada = QListWidgetItem(self._boot_label(clave))
                entrada.setData(Qt.ItemDataRole.UserRole, clave)
                self.list_boot.addItem(entrada)

        self.tree_shared.clear()
        for sh in vm.get("shared_folders", []):
            item = QTreeWidgetItem(self.tree_shared)
            item.setText(0, sh.get("host", "")); item.setText(1, sh.get("guest", "")); item.setText(2, tr(sh.get("method", "Automático"))); item.setText(3, tr(sh.get("mount", "Manual"))); item.setText(4, tr("Solo lectura") if sh.get("ro") else tr("Lectura/Escritura"))

        self.chk_clipboard.setChecked(vm.get("share_clipboard", True))
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

    # ------------------------------------------------------------------
    # DESCARGA DE ISO
    # ------------------------------------------------------------------
    def _download_iso_sync(self):
        """Descarga (síncrona con QEventLoop) la ISO del SO/versión actuales.

        Usa combo_version.currentData() (con fallback a currentText()) para
        obtener el id de versión. Muestra QMessageBox.warning si el SO no
        soporta descarga automática o si falla la resolución de la URL.
        """
        so = self.combo_so.currentText()
        ver_id = self.combo_version.currentData() or self.combo_version.currentText()

        if not self._so_supports_download(so):
            QMessageBox.warning(
                self.app.parent(),
                "Descarga no disponible",
                f"La descarga automática de ISO no está soportada para «{so}».\n\n"
                "Descarga la imagen manualmente y cárgala con la opción\n"
                "«Usar ISO/IMG/DMG existente»."
            )
            return None

        url = None
        try:
            if so in ["Windows 10", "Windows 11"]:
                url = iso_sources.get_latest_windows_iso_url(so)
            elif iso_versions.supports_versions(so):
                url = iso_versions.get_iso_url(so, ver_id)
            elif iso_sources.supports_auto_download(so):
                url = iso_sources.get_latest_iso_url(so)
        except Exception as e:
            QMessageBox.warning(
                self.app.parent(),
                "Error al obtener la URL",
                f"No se pudo resolver la URL de descarga para «{so}»\n"
                f"versión «{ver_id}».\n\nDetalle: {e}"
            )
            return None

        if not url:
            QMessageBox.warning(
                self.app.parent(),
                "URL no disponible",
                f"No se obtuvo ninguna URL para «{so}» versión «{ver_id}».\n"
                "Puede que el mirror haya cambiado o no haya conexión a internet."
            )
            return None

        iso_dir = self.app.isos_dir
        iso_dir.mkdir(parents=True, exist_ok=True)

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
            thread.stop()
            loop.quit()

        thread.progress.connect(on_progress)
        thread.finished_ok.connect(on_finish)
        thread.error.connect(on_err)
        progress.canceled.connect(on_cancel)

        thread.start()
        loop.exec()

        if result["error"]:
            QMessageBox.warning(self.app.parent(), "Error al descargar", f"Fallo al descargar la ISO:\n{result['error']}")
            return None

        return result["path"]

    # ------------------------------------------------------------------
    # GUARDAR
    # ------------------------------------------------------------------
    def _save_config(self):
        if not self.current_vm_id: return

        proto_idx = self.combo_console_proto.currentIndex()
        mode_idx = self.combo_console_mode.currentIndex()

        if proto_idx in (1, 2) and mode_idx in (0, 3):
            self.combo_console_mode.setCurrentIndex(1)
            mode_idx = 1

        shared_folders = []
        for i in range(self.tree_shared.topLevelItemCount()):
            item = self.tree_shared.topLevelItem(i)
            shared_folders.append({"host": item.text(0), "guest": item.text(1), "method": original_key(item.text(2)), "mount": original_key(item.text(3)), "ro": original_key(item.text(4)) == "Solo lectura"})

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
            entrada = self.list_boot.item(i)
            boot_order.append(entrada.data(Qt.ItemDataRole.UserRole) or entrada.text())

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
            "free_page_reporting": self.check_free_page_reporting.isChecked(),
            "graphics_idx": self.combo_graphics.currentIndex(),
            "vram_idx": self.combo_vram.currentIndex(),
            "console_proto_idx": self.combo_console_proto.currentIndex(),
            "console_mode_idx": self.combo_console_mode.currentIndex(),
            "shared_folders": shared_folders,
            "share_clipboard": self.chk_clipboard.isChecked(),
            "guest_agent": self.check_ga.isChecked(),
            "passthrough_devices": pt_devices,
            "network_adapters": self._network_data,
            "audio": self.combo_audio.currentText(),
            "pointer": self.combo_pointer.currentText(),
            "boot_order": boot_order,
            "disk_path": None, "iso_path": None, "floppy_path": None,
            "disk_bus": "sata", "optical_drives": []
        }

        current_vm = self.app.get_vm(self.current_vm_id)
        existing_iso = current_vm.get("iso_path") if current_vm else None
        vm_has_disk = bool(current_vm.get("disk_path")) if current_vm else False
        optical_drives = []

        for i in range(self.tree_storage.topLevelItemCount()):
            item = self.tree_storage.topLevelItem(i)
            tipo = self._storage_type(item)
            if tipo == TIPO_DISCO:
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
                            is_fixed = "Fijo" in original_key(disk_type)

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
                        data["disk_format"] = self._detect_image_format(path)
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
            elif tipo == TIPO_OPTICO:
                source_type = original_key(item.data(2, Qt.ItemDataRole.UserRole) or SOURCE_EMPTY)
                bus_text = (item.data(3, Qt.ItemDataRole.UserRole + 1) or item.text(3) or "SATA").lower()
                if "ide" in bus_text: cd_bus = "ide"
                elif "scsi" in bus_text: cd_bus = "scsi"
                elif "usb" in bus_text: cd_bus = "usb"
                else: cd_bus = "sata"
                drive_path = ""
                if source_type == SOURCE_DOWNLOAD:
                    existing_version = current_vm.get("version_id") if current_vm else None
                    current_version_id = self.combo_version.currentData() or self.combo_version.currentText()
                    same_version = (not existing_version) or (existing_version == current_version_id)

                    can_reuse = (
                        existing_iso
                        and os.path.exists(existing_iso)
                        and os.path.getsize(existing_iso) > 5000000
                        and same_version
                    )
                    if can_reuse:
                        drive_path = existing_iso
                    else:
                        downloaded_path = self._download_iso_sync()
                        if downloaded_path:
                            drive_path = downloaded_path
                            item.setText(2, downloaded_path)
                        else:
                            return
                elif item.text(2) and os.path.exists(item.text(2)):
                    drive_path = item.text(2)
                optical_drives.append({"path": drive_path, "source_type": source_type, "bus": cd_bus})
                if not optical_drives or len(optical_drives) == 1:
                    data["iso_source_type"] = source_type
                    data["cdrom_bus"] = cd_bus
                    if drive_path:
                        data["iso_path"] = drive_path
                if drive_path and not data.get("iso_path"):
                    data["iso_path"] = drive_path
            elif tipo == TIPO_DISQUETE:
                if item.text(2):
                    data["floppy_path"] = item.text(2)

        data["optical_drives"] = optical_drives

        # Registrar disco y CD/DVD de esta VM en la biblioteca de medios
        if data.get("disk_path") and os.path.exists(data["disk_path"]):
            self._register_media(
                data["disk_path"],
                os.path.basename(data["disk_path"]),
                data.get("disk_size", "-"),
                data.get("disk_format", "qcow2"),
                media_type="Disco duro",
            )
        if data.get("iso_path") and os.path.exists(data["iso_path"]):
            self._register_media(
                data["iso_path"],
                os.path.basename(data["iso_path"]),
                "-",
                "iso",
                media_type="ISO",
            )

        self.app.vm_repo.update(self.current_vm_id, data)
        QMessageBox.information(self.app.parent(), "Guardado", "Configuración guardada.")
