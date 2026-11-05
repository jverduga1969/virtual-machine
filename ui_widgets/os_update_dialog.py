from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from services import iso_versions
import logging
log = logging.getLogger(__name__)




class UpdateThread(QThread):
    progress_msg = pyqtSignal(str)
    finished_ok = pyqtSignal()
    
    def run(self):
        from services import iso_sources
        from services.os_catalog import OS_CATALOG
        
        # Obtener TODAS las distros de Linux del catálogo estático
        all_distros = sorted(list(OS_CATALOG.get("GNU / Linux", {}).keys()))
        
        for distro in all_distros:
            self.progress_msg.emit(f"Consultando {distro}...")
            try:
                if distro in iso_versions.VERSION_LISTERS:
                    iso_versions.list_distro_versions(distro, force=True)
                elif distro in iso_sources.SUPPORTED_AUTODETECT:
                    # Probar la última versión para verificar que el servidor responde
                    iso_sources.get_latest_iso_url(distro)
                else:
                    self.progress_msg.emit(f"ℹ️ {distro} requiere descarga manual (desde navegador).")
            except Exception as e:
                self.progress_msg.emit(f"⚠️ Error en {distro}: {e}")
                
        self.finished_ok.emit()

class OSUpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizando catálogo de SO")
        self.resize(550, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.lbl = QLabel("Conectando con los espejos oficiales...")
        layout.addWidget(self.lbl)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setEnabled(False)
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)
        
        self.thread = UpdateThread()
        self.thread.progress_msg.connect(self._on_msg)
        self.thread.finished_ok.connect(self._on_finished)
        self.thread.start()
        
    def _on_msg(self, msg):
        self.lbl.setText(msg)
        self.log.append(msg)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())
        
    def _on_finished(self):
        self.lbl.setText("¡Catálogo actualizado con éxito!")
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.btn_close.setEnabled(True)