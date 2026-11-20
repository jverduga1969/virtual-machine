import os
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests
import re
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QFormLayout, QMessageBox, QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from services.os_catalog import OS_CATALOG
from services import iso_versions
from services import iso_sources
from services.download_utils import HashTracker, save_checksum

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
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) VirtualMachine/1.0'}
            
            session = requests.Session()
            session.headers.update(headers)
            
            real_url = self.url
            try:
                r = session.get(self.url, stream=True, timeout=(15, 60))
                if "text/html" in r.headers.get("Content-Type", ""):
                    html = r.text
                    match = re.search(r'url=(https?://[^"\']+)', html)
                    if match: real_url = match.group(1)
                else:
                    real_url = r.url
                r.close()
            except Exception:
                pass
            
            response = session.get(real_url, stream=True, timeout=(15, 120))
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            
            if total > 0 and total < 5000000:
                raise Exception(f"El archivo es muy pequeño. Posible error HTML.")
            
            downloaded = 0
            start_time = time.time()
            last_update = start_time
            
            with open(part_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if self._is_cancelled:
                        part_path.unlink(missing_ok=True)
                        return
                    if chunk:
                        f.write(chunk)
                        self._tracker.update(chunk)
                        downloaded += len(chunk)
                        
                        now = time.time()
                        if now - last_update > 0.5:
                            speed = downloaded / (now - start_time)
                            mb_dl = downloaded / (1024 * 1024)
                            speed_mb = speed / (1024 * 1024)
                            
                            if total > 0:
                                mb_total = total / (1024 * 1024)
                                pct = min(100, int((downloaded / total) * 100))
                                eta_sec = int((total - downloaded) / speed) if speed > 0 else 0
                                eta_text = f"{eta_sec // 60}m {eta_sec % 60}s"
                                text = f"Descargando {filename}\n{mb_dl:.1f} MB de {mb_total:.1f} MB ({speed_mb:.1f} MB/s) - Restan: {eta_text}"
                            else:
                                pct = 0
                                text = f"Descargando {filename}\n{mb_dl:.1f} MB ({speed_mb:.1f} MB/s)"
                            
                            self.progress.emit(pct, text)
                            last_update = now
                            
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


class DownloadISODialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Descargar Imagen ISO")
        self.resize(450, 250)
        
        layout = QFormLayout(self)
        
        self.combo_platform = QComboBox()
        self.combo_platform.setToolTip("Familia de sistema operativo")
        self.combo_platform.addItems(list(OS_CATALOG.keys()))
        self.combo_platform.currentIndexChanged.connect(self._on_platform_changed)
        
        self.combo_so = QComboBox()
        self.combo_so.setToolTip("Distribución o versión específica del sistema operativo")
        self.combo_so.currentIndexChanged.connect(self._on_so_changed)
        
        self.combo_version = QComboBox()
        self.combo_version.setToolTip("Versión concreta de la imagen ISO")
        
        layout.addRow("Plataforma:", self.combo_platform)
        layout.addRow("Sistema Operativo:", self.combo_so)
        layout.addRow("Versión:", self.combo_version)
        
        self.btn_download = QPushButton("⬇️ Iniciar Descarga")
        self.btn_download.setToolTip("Descargar la imagen ISO seleccionada")
        self.btn_download.setStyleSheet("background-color: #1e40af; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_download.clicked.connect(self._start_download)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_download)
        btn_layout.addStretch()
        layout.addRow("", btn_layout)
        
        self._on_platform_changed()

    def _on_platform_changed(self):
        self.combo_so.clear()
        p = self.combo_platform.currentText()
        if p in OS_CATALOG:
            sos = sorted(list(OS_CATALOG[p].keys()), key=str.lower)
            self.combo_so.addItems(sos)
        self._on_so_changed()

    def _on_so_changed(self):
        self.combo_version.clear()
        so = self.combo_so.currentText()
        if not so: return
        
        # Intentar versiones dinámicas
        loaded = False
        try:
            dynamic = iso_versions.get_available_versions(so)
            if dynamic:
                for v in dynamic:
                    self.combo_version.addItem(v["label"], v["id"])
                loaded = True
        except Exception:
            pass
            
        # Fallback a estáticas
        if not loaded:
            p = self.combo_platform.currentText()
            statics = OS_CATALOG.get(p, {}).get(so, ["Automático"])
            for s in statics:
                self.combo_version.addItem(s, s)

    def _start_download(self):
        so = self.combo_so.currentText()
        ver_id = self.combo_version.currentData() or self.combo_version.currentText()
        
        can_download = (
            iso_sources.supports_auto_download(so) or 
            iso_versions.supports_versions(so) or 
            so in ["Windows 10", "Windows 11"]
        )
        
        if not can_download:
            QMessageBox.warning(self, "No disponible", f"La descarga automática no está disponible para {so}.")
            return

        url = None
        try:
            if so in ["Windows 10", "Windows 11"]:
                url = iso_sources.get_latest_windows_iso_url(f"{so} {ver_id}")
            elif iso_versions.supports_versions(so):
                url = iso_versions.get_iso_url(so, ver_id)
            elif iso_sources.supports_auto_download(so):
                url = iso_sources.get_latest_iso_url(so)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la URL:\n{e}")
            return

        if not url: return

        # Generar nombre de archivo
        parsed = urlparse(url)
        path_segments = [s for s in parsed.path.split("/") if s]
        filename = path_segments[-1] if path_segments else "imagen.iso"
        if path_segments and path_segments[-1] == "download":
            filename = path_segments[-2] if len(path_segments) >= 2 else "imagen.iso"
        
        filename = unquote(filename)
        if not filename.lower().endswith((".iso", ".img", ".dmg")):
            filename += ".iso"
            
        iso_dir = self.app.isos_dir
        iso_dir.mkdir(parents=True, exist_ok=True)
        dest_path = iso_dir / filename

        if dest_path.exists():
            resp = QMessageBox.question(self, "Ya existe", f"El archivo {filename} ya existe.\n¿Sobrescribir?")
            if resp == QMessageBox.StandardButton.No:
                return

        # Iniciar descarga
        self.progress_dlg = QProgressDialog(f"Descargando {filename}...", "Cancelar", 0, 100, self)
        self.progress_dlg.setWindowTitle("Descargando ISO")
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        
        self.thread = DownloadISOThread(url, str(dest_path))
        
        def update_ui(pct, text):
            if pct > 0:
                self.progress_dlg.setRange(0, 100)
                self.progress_dlg.setValue(pct)
            else:
                self.progress_dlg.setRange(0, 0)
            if "\n" in text:
                parts = text.split("\n")
                self.progress_dlg.setWindowTitle(parts[0])
                self.progress_dlg.setLabelText(parts[1])
                
        def on_done(path):
            self.progress_dlg.close()
            QMessageBox.information(self, "Completado", f"ISO descargada en:\n{path}")
            self.accept()
            
        def on_err(err):
            self.progress_dlg.close()
            QMessageBox.critical(self, "Error", f"Fallo al descargar:\n{err}")
            
        def on_cancel():
            self.thread.stop()
            
        self.thread.progress.connect(update_ui)
        self.thread.finished_ok.connect(on_done)
        self.thread.error.connect(on_err)
        self.progress_dlg.canceled.connect(on_cancel)
        self.thread.start()