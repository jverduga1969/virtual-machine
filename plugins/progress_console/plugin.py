import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QKeySequence, QTextDocument, QShortcut
from core.plugin_base import PluginBase
import logging
log = logging.getLogger(__name__)


def _find_flag_case():
    """Devuelve el flag FindCaseSensitively de QTextDocument."""
    return QTextDocument.FindFlag.FindCaseSensitively


def QTextDocument_FindFlags(case_sensitive: bool):
    """Helper — devuelve los flags de búsqueda según opciones."""
    return QTextDocument.FindFlag.FindCaseSensitively if case_sensitive else QTextDocument.FindFlag(0)




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
        self.combo_level.setToolTip("Filtrar mensajes por nivel de severidad")
        self.combo_level.addItems(["Todo", "Avisos+", "Errores"])
        self.combo_level.currentIndexChanged.connect(self._refresh_view)
        toolbar.addWidget(self.combo_level)

        # Auto-scroll
        self.check_autoscroll = QCheckBox("Auto-scroll")
        self.check_autoscroll.setChecked(True)
        self.check_autoscroll.setToolTip("Seguir automáticamente la última línea del registro")
        toolbar.addWidget(self.check_autoscroll)

        toolbar.addStretch()

        # Botones
        btn_clear = QPushButton("Limpiar consola")
        btn_clear.setToolTip("Borrar todo el registro de mensajes")
        btn_clear.clicked.connect(self._clear_console)
        toolbar.addWidget(btn_clear)
        
        btn_export = QPushButton("💾 Exportar log")
        btn_export.setToolTip("Guardar el registro de mensajes en un archivo de texto")
        btn_export.clicked.connect(self._export_log)
        toolbar.addWidget(btn_export)

        layout.addLayout(toolbar)

        # --- Barra de búsqueda con navegación (Ctrl+F) ---
        self._search_bar = QWidget()
        search_layout = QHBoxLayout(self._search_bar)
        search_layout.setContentsMargins(0, 2, 0, 2)
        search_layout.setSpacing(4)

        search_layout.addWidget(QLabel("Buscar:"))

        self._input_find = QLineEdit()
        self._input_find.setPlaceholderText("Texto a buscar…")
        self._input_find.setFixedWidth(200)
        self._input_find.returnPressed.connect(self._find_next)
        self._input_find.textChanged.connect(self._find_highlight)
        search_layout.addWidget(self._input_find)

        self._btn_prev = QPushButton("▲ Anterior")
        self._btn_prev.setToolTip("Ir a la ocurrencia anterior (Shift+F3)")
        self._btn_prev.setFixedWidth(90)
        self._btn_prev.clicked.connect(self._find_prev)
        search_layout.addWidget(self._btn_prev)

        self._btn_next = QPushButton("▼ Siguiente")
        self._btn_next.setToolTip("Ir a la siguiente ocurrencia (F3 / Enter)")
        self._btn_next.setFixedWidth(90)
        self._btn_next.clicked.connect(self._find_next)
        search_layout.addWidget(self._btn_next)

        self._lbl_match = QLabel("")
        self._lbl_match.setStyleSheet("color: #94a3b8; min-width: 80px;")
        search_layout.addWidget(self._lbl_match)

        self._check_case = QCheckBox("Aa")
        self._check_case.setToolTip("Distinguir mayúsculas/minúsculas")
        self._check_case.stateChanged.connect(self._find_highlight)
        search_layout.addWidget(self._check_case)

        btn_close_search = QPushButton("✕")
        btn_close_search.setToolTip("Limpiar búsqueda")
        btn_close_search.setFixedWidth(28)
        btn_close_search.clicked.connect(self._close_search_bar)
        search_layout.addWidget(btn_close_search)

        search_layout.addStretch()
        self._search_bar.setVisible(True)   # siempre visible
        layout.addWidget(self._search_bar)

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

        # Atajos de teclado
        QShortcut(QKeySequence("Ctrl+F"),   main_widget).activated.connect(self._focus_search)
        QShortcut(QKeySequence("F3"),       main_widget).activated.connect(self._find_next)
        QShortcut(QKeySequence("Shift+F3"), main_widget).activated.connect(self._find_prev)

        # Estado interno de búsqueda
        self._find_positions = []   # lista de posiciones (int) de ocurrencias
        self._find_current  = -1    # índice actual en _find_positions

        # --- Conexiones ---
        self.app.log_message.connect(self._append_log)
        self.app.process_started.connect(self._on_process_started)

        return [("Consola de Progreso", main_widget)]

    # ------------------------------------------------------------------ #
    # Búsqueda con navegación                                              #
    # ------------------------------------------------------------------ #
    def _focus_search(self):
        self._input_find.setFocus()
        self._input_find.selectAll()

    # _open_search_bar y _close_search_bar ya no se usan (barra siempre visible)
    def _open_search_bar(self):
        self._focus_search()

    def _close_search_bar(self):
        self._find_positions = []
        self._find_current   = -1
        self._lbl_match.setText("")
        self._clear_highlights()
        self.text_console.setFocus()

    def _find_highlight(self):
        """Resalta todas las ocurrencias y actualiza la lista de posiciones."""
        self._clear_highlights()
        self._find_positions = []
        self._find_current   = -1
        self._lbl_match.setText("")

        query = self._input_find.text()
        if not query:
            return

        doc   = self.text_console.document()
        case_sensitive = self._check_case.isChecked()
        flags = QTextDocument.FindFlag.FindCaseSensitively if case_sensitive else QTextDocument.FindFlag(0)

        # Color de resaltado
        hi_fmt = QTextCharFormat()
        hi_fmt.setBackground(QColor("#facc15"))   # amarillo
        hi_fmt.setForeground(QColor("#0a0e17"))   # texto oscuro

        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            cursor = doc.find(query, cursor, flags)
            if cursor.isNull():
                break
            self._find_positions.append(cursor.anchor())
            cursor.mergeCharFormat(hi_fmt)

        total = len(self._find_positions)
        self._lbl_match.setText(f"0 / {total}" if total else "Sin resultados")
        self._lbl_match.setStyleSheet(
            "color: #94a3b8;" if total else "color: #ef4444;"
        )
        if total:
            self._find_current = 0
            self._scroll_to_match(0)

    def _find_next(self):
        if not self._find_positions:
            self._find_highlight()
            return
        self._find_current = (self._find_current + 1) % len(self._find_positions)
        self._scroll_to_match(self._find_current)

    def _find_prev(self):
        if not self._find_positions:
            self._find_highlight()
            return
        self._find_current = (self._find_current - 1) % len(self._find_positions)
        self._scroll_to_match(self._find_current)

    def _scroll_to_match(self, idx):
        query = self._input_find.text()
        pos   = self._find_positions[idx]
        doc   = self.text_console.document()

        # Resaltado activo (naranja) sobre el actual, amarillo en el resto
        active_fmt  = QTextCharFormat()
        active_fmt.setBackground(QColor("#f97316"))  # naranja
        active_fmt.setForeground(QColor("#ffffff"))

        normal_fmt  = QTextCharFormat()
        normal_fmt.setBackground(QColor("#facc15"))  # amarillo
        normal_fmt.setForeground(QColor("#0a0e17"))

        for i, p in enumerate(self._find_positions):
            c = QTextCursor(doc)
            c.setPosition(p)
            c.setPosition(p + len(query), QTextCursor.MoveMode.KeepAnchor)
            c.mergeCharFormat(active_fmt if i == idx else normal_fmt)

        # Mover el cursor visible a la posición activa
        c = QTextCursor(doc)
        c.setPosition(pos)
        c.setPosition(pos + len(query), QTextCursor.MoveMode.KeepAnchor)
        self.text_console.setTextCursor(c)
        self.text_console.ensureCursorVisible()

        self._lbl_match.setText(f"{idx + 1} / {len(self._find_positions)}")

    def _clear_highlights(self):
        """Elimina todos los resaltados de búsqueda restaurando el color por nivel."""
        self.text_console.blockSignals(True)
        self._refresh_view()          # reconstruye el texto con colores originales
        self.text_console.blockSignals(False)

    def _on_process_started(self, vm_id, process):
        # Limpiar hilos terminados para que la lista no crezca indefinidamente
        self.reader_threads = [t for t in self.reader_threads if t.isRunning()]

        vm = self.app.get_vm(vm_id)
        vm_name = vm.get("name", "Desconocida") if vm else "Desconocida"
        self._append_log("info", f"--- Iniciando proceso QEMU para: {vm_name} ---")

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
        if idx == 1 and level == "info": return False
        if idx == 2 and level != "error": return False
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