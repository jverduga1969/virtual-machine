import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
from core.plugin_base import PluginBase
import logging
log = logging.getLogger(__name__)




class QEMUReaderThread(QThread):
    """Hilo que lee la salida de QEMU línea a línea sin bloquear la UI."""
    new_line = pyqtSignal(str, str) # nivel, texto

    def __init__(self, process):
        super().__init__()
        self.process = process

    def run(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                
                # Clasificar el nivel según el texto
                level = "info"
                lower = line.lower()
                if "error" in lower or "failed" in lower or "fatal" in lower:
                    level = "error"
                elif "warning" in lower or "warn" in lower:
                    level = "warn"
                    
                self.new_line.emit(level, line)
        except Exception:
            pass
        finally:
            self.new_line.emit("info", "--- Proceso QEMU finalizado ---")

class Plugin(PluginBase):
    name = "ProgressConsole"
    version = "1.0.0"

    def __init__(self, app):
        super().__init__(app)
        self.all_logs = [] # Lista de tuplas (nivel, texto)
        self.reader_threads = [] # Para mantener referencia y evitar GC

    def get_tabs(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Barra de Herramientas ---
        toolbar = QHBoxLayout()
        
        # Filtro de Nivel
        toolbar.addWidget(QLabel("Nivel:"))
        self.combo_level = QComboBox()
        self.combo_level.addItems(["Todo", "Avisos+", "Errores"])
        self.combo_level.currentIndexChanged.connect(self._refresh_view)
        toolbar.addWidget(self.combo_level)

        # Buscador
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Filtrar...")
        self.input_search.setFixedWidth(150)
        self.input_search.textChanged.connect(self._refresh_view)
        toolbar.addWidget(self.input_search)

        # Auto-scroll
        self.check_autoscroll = QCheckBox("Auto-scroll")
        self.check_autoscroll.setChecked(True)
        toolbar.addWidget(self.check_autoscroll)

        toolbar.addStretch()

        # Botones
        btn_clear = QPushButton("Limpiar consola")
        btn_clear.clicked.connect(self._clear_console)
        toolbar.addWidget(btn_clear)
        
        btn_export = QPushButton("💾 Exportar log")
        btn_export.clicked.connect(self._export_log)
        toolbar.addWidget(btn_export)

        layout.addLayout(toolbar)

        # --- Área de Texto ---
        self.text_console = QTextEdit()
        self.text_console.setReadOnly(True)
        self.text_console.setStyleSheet("""
            QTextEdit {
                background-color: #0a0e17; 
                color: #4ade80; 
                font-family: monospace; 
                font-size: 12px;
                border: 1px solid #232b40;
            }
        """)
        layout.addWidget(self.text_console)

        # --- Conexiones ---
        # Escuchar los logs internos de la app
        self.app.log_message.connect(self._append_log)
        # Escuchar cuando se inicia un proceso QEMU
        self.app.process_started.connect(self._on_process_started)

        return [("Consola de Progreso", main_widget)]

    def _on_process_started(self, vm_id, process):
        # Añadir mensaje de sistema
        vm = self.app.get_vm(vm_id)
        vm_name = vm.get("name", "Desconocida") if vm else "Desconocida"
        self._append_log("info", f"--- Iniciando proceso QEMU para: {vm_name} ---")

        # Lanzar el hilo lector
        thread = QEMUReaderThread(process)
        thread.new_line.connect(self._append_log)
        thread.start()
        self.reader_threads.append(thread)

    def _append_log(self, level, text):
        # Añadir timestamp
        timestamp = time.strftime("[%H:%M:%S]")
        formatted_text = f"{timestamp} {text}"
        
        self.all_logs.append((level, formatted_text))
        
        # Si pasa el filtro actual, lo mostramos
        if self._matches_filter(level, formatted_text):
            self._append_to_ui(level, formatted_text)

    def _matches_filter(self, level, text):
        # Filtro de nivel
        idx = self.combo_level.currentIndex()
        if idx == 1 and level == "info": return False # Avisos+
        if idx == 2 and level != "error": return False # Errores
        
        # Filtro de texto
        search_text = self.input_search.text().lower()
        if search_text and search_text not in text.lower():
            return False
            
        return True

    def _append_to_ui(self, level, text):
        # Configurar color según nivel
        cursor = self.text_console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        fmt = QTextCharFormat()
        if level == "error":
            fmt.setForeground(QColor("#ef4444"))
        elif level == "warn":
            fmt.setForeground(QColor("#f59e0b"))
        else:
            fmt.setForeground(QColor("#4ade80"))
            
        cursor.insertText(text + "\n", fmt)
        
        if self.check_autoscroll.isChecked():
            self.text_console.setTextCursor(cursor)
            self.text_console.ensureCursorVisible()

    def _refresh_view(self):
        """Reconstruye la vista cuando cambia un filtro."""
        self.text_console.clear()
        for level, text in self.all_logs:
            if self._matches_filter(level, text):
                self._append_to_ui(level, text)

    def _clear_console(self):
        self.all_logs.clear()
        self.text_console.clear()

    def _export_log(self):
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QDateTime
        default_name = f"log_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.txt"
        path, _ = QFileDialog.getSaveFileName(self.app.parent(), "Exportar log", default_name, "Archivos de texto (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    for level, text in self.all_logs:
                        f.write(f"[{level.upper()}] {text}\n")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self.app.parent(), "Error", f"No se pudo guardar el log: {e}")