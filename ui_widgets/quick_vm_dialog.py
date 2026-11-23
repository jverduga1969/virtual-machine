import os
import uuid
import subprocess
import threading
import requests
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QRadioButton, QButtonGroup, QFileDialog, 
    QDialogButtonBox, QFormLayout, QGroupBox, QWidget, QMessageBox,
    QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from services.vm_profiles import get_vm_profiles
from services.os_catalog import OS_CATALOG
from services import iso_versions
from services import iso_sources
from services.download_utils import HashTracker, save_checksum
from services.qemu_paths import qemu_cmd
from services.macos_recovery import MacOSDownloader
from ui_widgets.media_library_dialog import MediaLibraryDialog


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
        try:
            dest_path = Path(self.dest_path)
            part_path = Path(str(dest_path) + ".part")
            
            if part_path.exists():
                try: part_path.unlink()
                except: pass
            if dest_path.exists():
                try: dest_path.unlink()
                except: pass
            
            filename = dest_path.name
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) VirtualMachine/1.0'}
            
            session = requests.Session()
            session.headers.update(headers)
            
            real_url = self.url
            try:
                r = session.get(self.url, stream=True, timeout=(15, 60))
                content_type = r.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    html = r.text
                    match = re.search(r'url=(https?://[^"\']+)', html)
                    if not match:
                        match = re.search(r'(https://downloads\.sourceforge\.net/[^"\']+)', html)
                    if match:
                        real_url = match.group(1)
                else:
                    real_url = r.url
                r.close()
            except Exception:
                pass
            
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
                        self._tracker.update(chunk)
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
                
            self.sha256 = self._tracker.verify()
            part_path.replace(dest_path)
            save_checksum(dest_path, self.sha256)
            self.finished_ok.emit(str(dest_path))
        except Exception as e:
            if 'part_path' in locals() and part_path.exists():
                try: part_path.unlink()
                except: pass
            if not self._is_cancelled:
                self.error.emit(str(e))


class QuickVMDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Crear VM rápida")
        self.resize(650, 750)
        
        pal = QApplication.palette()
        bg, base, text, mid = pal.window().color().name(), pal.base().color().name(), pal.text().color().name(), pal.mid().color().name()
        highlight, highlighted_text = pal.highlight().color().name(), pal.highlightedText().color().name()
        placeholder, button, button_text = pal.placeholderText().color().name(), pal.button().color().name(), pal.buttonText().color().name()

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {text}; }}
            QLabel, QRadioButton, QCheckBox {{ color: {text}; background-color: transparent; }}
            QGroupBox {{ font-weight: bold; border: 1px solid {mid}; border-radius: 6px; margin-top: 10px; padding-top: 15px; background-color: transparent; color: {text}; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: {text}; }}
            QLineEdit, QComboBox {{ background-color: {base}; color: {text}; border: 1px solid {mid}; border-radius: 4px; padding: 4px; }}
            QComboBox:disabled {{ background-color: {bg}; color: {mid}; border: 1px dashed {mid}; }}
            QComboBox QAbstractItemView {{ background-color: {base}; color: {text}; }}
            QPushButton {{ background-color: {button}; color: {button_text}; border: 1px solid {mid}; border-radius: 4px; padding: 4px 8px; }}
            QPushButton:hover {{ background-color: {highlight}; color: {highlighted_text}; }}
            QPushButton#ProfileCard {{ background-color: {base}; border: 2px solid {mid}; border-radius: 8px; }}
            QPushButton#ProfileCard:hover {{ border: 2px solid {highlight}; }}
            QPushButton#ProfileCard:checked {{ border: 2px solid {highlight}; background-color: {highlight}; }}
            QPushButton#ProfileCard QLabel {{ background: transparent; color: {text}; }}
            QPushButton#ProfileCard:checked QLabel {{ color: {highlighted_text}; }}
            QPushButton#ProfileCard QLabel#LblIcon {{ font-size: 24px; }}
            QPushButton#ProfileCard QLabel#LblName {{ font-size: 14px; font-weight: bold; }}
            QPushButton#ProfileCard QLabel#LblDesc {{ font-size: 10px; color: {placeholder}; }}
            QPushButton#ProfileCard:checked QLabel#LblDesc {{ color: {highlighted_text}; }}
        """)
        
        self.profiles = get_vm_profiles()
        self.selected_profile = self.profiles[0]
        self.iso_path = ""

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        group_profiles = QGroupBox("Perfil de uso")
        lay_profiles = QHBoxLayout(group_profiles)
        lay_profiles.setSpacing(10)
        
        self.profile_group = QButtonGroup(self)
        self.profile_buttons = []
        
        for i, prof in enumerate(self.profiles):
            btn = QPushButton()
            btn.setObjectName("ProfileCard")
            btn.setCheckable(True)
            btn.setFixedSize(140, 110)
            
            btn_layout = QVBoxLayout(btn)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_layout.setSpacing(2)
            
            lbl_icon = QLabel(prof["icon"])
            lbl_icon.setObjectName("LblIcon")
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_name = QLabel(prof["name"])
            lbl_name.setObjectName("LblName")
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_hw = QLabel(f"{prof['ram']//1024}G · {prof['cores']} vCPU · {prof['disk_size']}")
            lbl_hw.setObjectName("LblDesc")
            lbl_hw.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_layout.addWidget(lbl_icon)
            btn_layout.addWidget(lbl_name)
            btn_layout.addWidget(lbl_hw)
            
            self.profile_group.addButton(btn, i)
            self.profile_buttons.append(btn)
            lay_profiles.addWidget(btn)
            
        self.profile_buttons[0].setChecked(True)
        self.profile_group.idClicked.connect(self._on_profile_selected)
        main_layout.addWidget(group_profiles)

        group_basic = QGroupBox("Datos básicos")
        form_basic = QFormLayout(group_basic)
        
        self.input_name = QLineEdit("Mi máquina virtual")
        self.input_name.setToolTip("Nombre identificador de la nueva máquina virtual")
        
        self.combo_platform = QComboBox()
        self.combo_platform.setToolTip("Familia de sistema operativo que se instalará")
        self.combo_platform.addItems(list(OS_CATALOG.keys()))
        self.combo_platform.currentIndexChanged.connect(self._on_platform_changed)
        
        self.combo_so = QComboBox()
        self.combo_so.setToolTip("Distribución o versión específica del sistema operativo")
        self.combo_so.currentIndexChanged.connect(self._on_so_changed)
        
        self.combo_version = QComboBox()
        self.combo_version.setToolTip("Versión concreta de la imagen de instalación")
        self.lbl_ver = QLabel("Versión:")
        
        form_basic.addRow("Nombre:", self.input_name)
        form_basic.addRow("Plataforma:", self.combo_platform)
        form_basic.addRow("Sistema operativo:", self.combo_so)
        form_basic.addRow(self.lbl_ver, self.combo_version)
        main_layout.addWidget(group_basic)

        group_media = QGroupBox("Medio de instalación")
        lay_media = QVBoxLayout(group_media)
        
        self.radio_no_iso = QRadioButton("No, la selecciono luego")
        self.radio_no_iso.setToolTip("No asignar ninguna ISO al crear la VM")
        self.radio_download = QRadioButton("Descargar automáticamente")
        self.radio_download.setToolTip("Descargar la ISO de instalación desde internet")
        self.radio_file = QRadioButton("Seleccionar un archivo ISO")
        self.radio_file.setToolTip("Usar un archivo ISO que ya tienes en el disco")
        self.radio_no_iso.setChecked(True)
        
        radio_group = QButtonGroup(self)
        radio_group.addButton(self.radio_no_iso)
        radio_group.addButton(self.radio_download)
        radio_group.addButton(self.radio_file)
        
        lay_media.addWidget(self.radio_no_iso)
        lay_media.addWidget(self.radio_download)
        lay_media.addWidget(self.radio_file)
        
        file_layout = QHBoxLayout()
        self.input_iso = QLineEdit()
        self.input_iso.setPlaceholderText("Ruta al archivo ISO...")
        self.input_iso.setEnabled(False)
        self.input_iso.setToolTip("Ruta al archivo de imagen ISO de instalación")
        
        self.btn_browse = QPushButton("Examinar...")
        self.btn_browse.setEnabled(False)
        self.btn_browse.setToolTip("Buscar un archivo ISO en el disco")
        self.btn_browse.clicked.connect(self._browse_iso)
        
        self.btn_library = QPushButton("Biblioteca")
        self.btn_library.setEnabled(False)
        self.btn_library.setToolTip("Elegir una imagen desde la biblioteca de medios")
        self.btn_library.clicked.connect(self._browse_library)
        
        file_layout.addWidget(self.input_iso)
        file_layout.addWidget(self.btn_browse)
        file_layout.addWidget(self.btn_library)
        lay_media.addLayout(file_layout)
        
        self.radio_file.toggled.connect(self._on_iso_source_changed)
        main_layout.addWidget(group_media)

        main_layout.addStretch()
        self.btns = QDialogButtonBox()
        self.btn_create = self.btns.addButton("✓ Crear ->", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_create.setToolTip("Crear la máquina virtual con los datos configurados")
        self.btn_create.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.btn_cancel = self.btns.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        
        self.btns.accepted.connect(self._create_vm)
        self.btns.rejected.connect(self.reject)
        main_layout.addWidget(self.btns)

        self._on_profile_selected(0)

    def _on_profile_selected(self, index):
        self.selected_profile = self.profiles[index]
        self.combo_platform.blockSignals(True); self.combo_so.blockSignals(True); self.combo_version.blockSignals(True)
        plat_idx = self.combo_platform.findText(self.selected_profile["platform"])
        if plat_idx >= 0: self.combo_platform.setCurrentIndex(plat_idx)
        self._populate_os_list()
        so_idx = self.combo_so.findText(self.selected_profile["os"])
        if so_idx >= 0: self.combo_so.setCurrentIndex(so_idx)
        self.combo_platform.blockSignals(False); self.combo_so.blockSignals(False); self.combo_version.blockSignals(False)
        self._on_so_changed()

    def _on_platform_changed(self):
        self.combo_so.blockSignals(True)
        self._populate_os_list()
        self.combo_so.blockSignals(False)
        self._on_so_changed()

    def _on_so_changed(self):
        """Rellena combo_version con versiones dinámicas si hay internet.

        Orden:
          1. iso_versions.get_available_versions(so)  -> dinámicas (label/id)
          2. OS_CATALOG[platform][so]                 -> estáticas (fallback)
          3. "Automático"                              -> último recurso
        El data de cada ítem es el id de versión (v["id"]) para las dinámicas,
        o el propio texto para las estáticas.
        """
        platform = self.combo_platform.currentText()
        so = self.combo_so.currentText()
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.setEnabled(False)
        self.lbl_ver.setToolTip("")
        if not so:
            self.combo_version.blockSignals(False)
            return

        if platform == "macOS":
            self.selected_profile["firmware_idx"] = 1
            self.selected_profile["chipset_idx"] = 1
            self.selected_profile["secure_boot"] = False
            self.selected_profile["tpm"] = False
            self.selected_profile["graphics_idx"] = 5
            self.selected_profile["cores"] = 4
            self.selected_profile["ram"] = 8192

        # 1) Versiones dinámicas (consulta a internet)
        loaded_dynamic = False
        try:
            dynamic = iso_versions.get_available_versions(so)
        except Exception:
            dynamic = None
        if dynamic:
            for v in dynamic:
                label = v.get("label") or str(v.get("id", ""))
                vid = v.get("id") or label
                self.combo_version.addItem(label, vid)
            loaded_dynamic = True
            self.lbl_ver.setToolTip("Versiones obtenidas en línea desde el mirror oficial.")

        # 2) Fallback al catálogo estático
        if not loaded_dynamic:
            static_versions = OS_CATALOG.get(platform, {}).get(so, [])
            if static_versions:
                for sv in static_versions:
                    self.combo_version.addItem(sv, sv)
            else:
                self.combo_version.addItem("Automático", "Automático")

        self.combo_version.setEnabled(True)
        self.combo_version.blockSignals(False)

        # 3) Preseleccionar la versión del perfil (si existe).
        #    Con versiones dinámicas el texto cambia (ej. perfil "24.04 LTS"
        #    vs ítem "Ubuntu 24.04.1"), así que probamos texto -> data -> prefijo.
        profile_ver = self.selected_profile.get("version", "")
        if profile_ver:
            idx = self.combo_version.findText(profile_ver)
            if idx < 0:
                idx = self.combo_version.findData(profile_ver)
            if idx < 0:
                m = re.match(r'(\d+(?:\.\d+)*)', profile_ver)
                if m:
                    prefix = m.group(1)
                    for i in range(self.combo_version.count()):
                        data = str(self.combo_version.itemData(i) or "")
                        if data.startswith(prefix):
                            idx = i
                            break
            if idx >= 0:
                self.combo_version.setCurrentIndex(idx)

    def _populate_os_list(self):
        platform = self.combo_platform.currentText()
        self.combo_so.clear()
        if platform in OS_CATALOG:
            ordered_sos = sorted(list(OS_CATALOG[platform].keys()), key=str.lower)
            self.combo_so.addItems(ordered_sos)

    def _on_iso_source_changed(self, checked):
        self.input_iso.setEnabled(checked)
        self.btn_browse.setEnabled(checked)
        self.btn_library.setEnabled(checked)

    def _browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes (*.iso *.img *.dmg)")
        if path:
            self.input_iso.setText(path)
            self.iso_path = path
            
    def _browse_library(self):
        dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.input_iso.setText(dlg.selected_path)
            self.iso_path = dlg.selected_path

    def _create_vm(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        vm_id = str(uuid.uuid4())
        disk_name = "disco_principal.qcow2"
        vm_dir = self.app.vms_dir / vm_id
        vm_dir.mkdir(parents=True, exist_ok=True)
        disk_path = vm_dir / disk_name

        try:
            subprocess.run(
                qemu_cmd("qemu-img", "create", "-f", "qcow2", str(disk_path), self.selected_profile["disk_size"]),
                check=True, capture_output=True
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el disco: {e}")
            return

        iso_path = self.input_iso.text() if self.radio_file.isChecked() else None
        
        if self.radio_download.isChecked():
            iso_source_type = "Descargar"
        elif self.radio_file.isChecked():
            iso_source_type = "Usar ISO/IMG/DMG existente"
        else:
            iso_source_type = "Mantener vacío"

        if self.radio_download.isChecked():
            self._start_iso_download(vm_id, disk_path, iso_source_type)
            return

        self._finalize_creation(vm_id, disk_path, iso_path, iso_source_type)

    def _start_iso_download(self, vm_id, disk_path, iso_source_type):
        platform = self.combo_platform.currentText()
        so = self.combo_so.currentText()
        ver_id = self.combo_version.currentData() or self.combo_version.currentText()

        if platform == "macOS":
            self._start_macos_download(vm_id, disk_path, ver_id or so)
            return

        url = None
        try:
            if so in ["Windows 10", "Windows 11"]:
                QMessageBox.information(self, "Windows", "Se usará Fido para obtener la URL oficial. Esto puede tardar unos segundos...")
                url = iso_sources.get_latest_windows_iso_url(so)
            elif iso_versions.supports_versions(so):
                try:
                    url = iso_versions.get_iso_url(so, ver_id)
                except Exception:
                    if so in ["Pop!_OS", "Garuda Linux", "elementary OS", "Kali Linux"]:
                        url = iso_sources.get_latest_iso_url(so)
                    else:
                        raise
            elif iso_sources.supports_auto_download(so):
                url = iso_sources.get_latest_iso_url(so)
            else:
                QMessageBox.warning(self, "Descarga no soportada", f"La descarga automática no está disponible para {so}.\n\nPor favor, descarga la ISO manualmente y usa 'Seleccionar un archivo ISO'.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error de descarga", f"No se pudo obtener la URL: {e}")
            return

        if not url: return

        iso_dir = self.app.isos_dir
        iso_dir.mkdir(parents=True, exist_ok=True)
        
        parsed = urlparse(url)
        path_segments = [s for s in parsed.path.split("/") if s]
        if path_segments and path_segments[-1] == "download":
            filename = path_segments[-2] if len(path_segments) >= 2 else "imagen.iso"
        else:
            filename = path_segments[-1] if path_segments else "imagen.iso"
        
        filename = unquote(filename)
        if not filename.lower().endswith((".iso", ".img", ".dmg")):
            filename += ".iso"
        
        dest_path = iso_dir / filename

        if dest_path.exists() and dest_path.stat().st_size > 5000000:
            resp = QMessageBox.question(
                self, "ISO existente",
                f"La ISO '{filename}' ya existe en la biblioteca ({dest_path.stat().st_size / (1024*1024):.1f} MB).\n\n"
                "¿Deseas usar esa ISO o descargarla de nuevo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._finalize_creation(vm_id, disk_path, str(dest_path), iso_source_type)
                return
            else:
                try: dest_path.unlink()
                except: pass

        self.progress_dlg = QProgressDialog(
            self.app.tr("Descargando {}...").format(filename), "Cancelar", 0, 100, self)
        self.progress_dlg.setWindowTitle(
            self.app.tr("Descargando {}").format(filename))
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        
        self.download_thread = DownloadISOThread(url, str(dest_path))
        
        def update_progress(pct, text):
            if pct > 0:
                self.progress_dlg.setRange(0, 100); self.progress_dlg.setValue(pct)
            else:
                self.progress_dlg.setRange(0, 0)
            if "\n" in text:
                parts = text.split("\n")
                self.progress_dlg.setWindowTitle(parts[0]); self.progress_dlg.setLabelText(parts[1])
            else:
                self.progress_dlg.setWindowTitle(text); self.progress_dlg.setLabelText("")
                
        def on_finished(path):
            self.progress_dlg.setValue(100); self.progress_dlg.close()
            self._finalize_creation(vm_id, disk_path, path, iso_source_type)
            
        def on_error(err):
            self.progress_dlg.close()
            QMessageBox.critical(self, "Error", f"Fallo al descargar: {err}")
            
        def on_cancel():
            if hasattr(self, 'download_thread') and self.download_thread.isRunning():
                self.download_thread.stop()
                self.download_thread.wait()
            
        self.download_thread.progress.connect(update_progress)
        self.download_thread.finished_ok.connect(on_finished)
        self.download_thread.error.connect(on_error)
        self.progress_dlg.canceled.connect(on_cancel)
        self.download_thread.start()

    def _start_macos_download(self, vm_id, disk_path, version_label):
        self.progress_dlg = QProgressDialog("Preparando descarga de macOS...", "Cancelar", 0, 0, self)
        self.progress_dlg.setWindowTitle(f"macOS {version_label}")
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        self.progress_dlg.show()

        dest_dir = self.app.isos_dir / "macos"
        self.macos_downloader = MacOSDownloader(version_label, dest_dir, self.app.data_dir)
        
        def on_progress(msg):
            if "\n" in msg:
                parts = msg.split("\n", 1)
                self.progress_dlg.setWindowTitle(parts[0]); self.progress_dlg.setLabelText(parts[1])
            else:
                self.progress_dlg.setLabelText(msg)
                
        def on_finished(path):
            self.progress_dlg.setValue(100); self.progress_dlg.close()
            self._finalize_creation(vm_id, disk_path, path, "Descargar")
            
        def on_error(err):
            self.progress_dlg.close()
            QMessageBox.critical(self, "Error", f"Fallo al descargar macOS:\n{err}")

        self.macos_downloader.progress.connect(on_progress)
        self.macos_downloader.finished.connect(on_finished)
        self.macos_downloader.error.connect(on_error)
        self.progress_dlg.canceled.connect(self.macos_downloader.process.kill)
        self.macos_downloader.start()

    def _finalize_creation(self, vm_id, disk_path, iso_path, iso_source_type):
        new_vm = {
            "id": vm_id,
            "name": self.input_name.text().strip(),
            "state": "Apagada",
            "platform": self.combo_platform.currentText(),
            "so": self.combo_so.currentText(),
            "version": self.combo_version.currentText(),
            "version_id": self.combo_version.currentData() or "",
            "cores": self.selected_profile["cores"],
            "ram": self.selected_profile["ram"],
            "firmware_idx": self.selected_profile["firmware_idx"],
            "chipset_idx": self.selected_profile["chipset_idx"],
            "graphics_idx": self.selected_profile["graphics_idx"],
            "initial_resolution": "",
            "monitor_count": 1,
            "secure_boot": self.selected_profile["secure_boot"],
            "tpm": self.selected_profile["tpm"],
            "disk_path": str(disk_path),
            "disk_bus": "sata",
            "iso_path": iso_path,
            "iso_source_type": iso_source_type,
            "network_adapters": [{"name": "Red 1", "model": "VirtIO", "backend": "NAT / Internet"}],
            "audio": "Intel HDA (recomendado)",
            "pointer": "USB Tablet",
            "clipboard": "Desactivado",
        }
        self.app.vm_repo.add(new_vm)
        self.accept()