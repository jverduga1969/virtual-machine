import logging
import os
import requests
import time
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QSplitter, QTabWidget, QLabel, QPushButton,
    QToolButton, QMessageBox, QMenu, QMenuBar,
    QLineEdit, QComboBox, QStyle, QListView, QStackedWidget, QSizePolicy,
    QDialog, QProgressDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon, QKeySequence, QAction
from core import AppContext, PluginManager
from core.i18n import translate_widgets
from ui_widgets.resource_monitor import ResourceMonitor
from ui_widgets.quick_vm_dialog import QuickVMDialog
from ui_widgets.hotplug_dialog import HotplugDialog
from services import iso_versions
from services import iso_sources
from services.download_utils import HashTracker, expected_hash
from services.macos_recovery import MacOSDownloader
from services.shortcuts import ShortcutStore, COMMAND_LABELS
from ui_widgets.os_icons import os_icon

log = logging.getLogger(__name__)

# ============================================================
# HILO PARA DESCARGAR ISO AL ARRANCAR LA VM
# ============================================================
class DownloadStartThread(QThread):
    progress = pyqtSignal(int, str)
    # No sobrescribir QThread.finished: señal nativa reservada para limpieza.
    download_finished = pyqtSignal(str)
    download_canceled = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, vm, isos_dir):
        super().__init__()
        self.vm = vm
        self.isos_dir = Path(isos_dir)
        self._is_cancelled = False
        self.sha256 = ""  # rellenado al terminar; lo consume la GUI
        algo, digest = expected_hash(vm)
        self._tracker = HashTracker(algo or "sha256", digest)

    def stop(self):
        self._is_cancelled = True

    def run(self):
        part_path = None
        try:
            so = self.vm.get("so", "")
            ver_id = self.vm.get("version_id", "")

            url = None
            if so in ["Windows 10", "Windows 11"]:
                url = iso_sources.get_latest_windows_iso_url(so)
            elif iso_versions.supports_versions(so):
                url = iso_versions.get_iso_url(so, ver_id)
            elif iso_sources.supports_auto_download(so):
                url = iso_sources.get_latest_iso_url(so)

            if not url:
                self.error.emit(f"No se encontró URL válida para {so}")
                return

            iso_dir = self.isos_dir
            iso_dir.mkdir(parents=True, exist_ok=True)

            parsed = urlparse(url)
            path_segments = [s for s in parsed.path.split("/") if s]

            if path_segments and path_segments[-1] == "download":
                filename = path_segments[-2] if len(path_segments) >= 2 else "imagen.iso"
            else:
                filename = path_segments[-1] if path_segments else "imagen.iso"

            # El nombre viene de una URL remota: quedarse solo con el nombre
            # base evita %2f..%2f y escrituras fuera del directorio de ISOs.
            filename = Path(unquote(filename)).name
            if not re.fullmatch(r"[A-Za-z0-9._() -]{1,180}", filename):
                raise ValueError(f"Nombre de ISO no seguro: {filename!r}")
            if not filename.lower().endswith((".iso", ".img", ".dmg")):
                filename += ".iso"

            dest_path = iso_dir / filename
            part_path = iso_dir / (filename + ".part")

            if part_path.exists():
                try: part_path.unlink()
                except OSError as e: log.debug("No se pudo borrar .part previo: %s", e)
            # No borrar la ISO existente: replace() la sustituye solo si la
            # descarga nueva terminó correctamente.

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            session = requests.Session()
            session.headers.update(headers)

            # Manejo de SourceForge / Redirecciones HTML
            real_url = url
            try:
                r = session.get(url, stream=True, timeout=(10, 30))
                if "text/html" in r.headers.get("Content-Type", ""):
                    html = r.text
                    match = re.search(r'url=(https?://[^"\']+)', html) or re.search(r'(https://downloads\.sourceforge\.net/[^"\']+)', html)
                    if match:
                        real_url = match.group(1)
                else:
                    real_url = r.url
                r.close()
            except Exception:
                pass

            response = session.get(real_url, stream=True, timeout=(15, 60))
            response.raise_for_status()

            total = int(response.headers.get('content-length', 0))
            if total > 0 and total < 5000000:
                raise Exception(f"El archivo pesa muy poco ({total} bytes). Probablemente sea un HTML de error.")

            downloaded = 0
            start_time = time.time()
            last_update_time = start_time

            with open(part_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if self._is_cancelled:
                        f.close()
                        part_path.unlink(missing_ok=True)
                        self.download_canceled.emit()
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
                self.download_canceled.emit()
                return

            if downloaded < 5000000:
                raise Exception(f"La descarga falló. Archivo demasiado pequeño ({downloaded} bytes).")

            if total > 0 and downloaded < total:
                raise Exception("La conexión se interrumpió antes de terminar.")

            # Verificar antes de reemplazar: si la fuente anunció hash y no
            # coincide, el .part se borra y la ISO anterior queda intacta.
            self.sha256 = self._tracker.verify()
            log.info("ISO descargada %s (sha256=%s)", filename, self.sha256)
            part_path.replace(dest_path)
            self.download_finished.emit(str(dest_path))

        except Exception as e:
            if part_path and part_path.exists():
                try: part_path.unlink()
                except OSError as err: log.debug("No se pudo limpiar .part: %s", err)
            if not self._is_cancelled:
                self.error.emit(str(e))

# ============================================================
# Estilos
# ============================================================
BTN_STYLE_INICIAR = """
    QToolButton { background-color: #2e7d32; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }
    QToolButton:disabled { background-color: #4a4a4a; color: #8a8a8a; border: 1px solid #3a3a3a; }
    QToolButton:hover:!disabled { background-color: #388e3c; }
"""
BTN_STYLE_PAUSA = """
    QToolButton { background-color: #f9a825; color: black; padding: 5px; font-weight: bold; border-radius: 3px; }
    QToolButton:disabled { background-color: #4a4a4a; color: #8a8a8a; border: 1px solid #3a3a3a; }
    QToolButton:hover:!disabled { background-color: #fbc02d; }
"""
BTN_STYLE_APAGAR = """
    QToolButton { background-color: #c62828; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }
    QToolButton:disabled { background-color: #4a4a4a; color: #8a8a8a; border: 1px solid #3a3a3a; }
    QToolButton:hover:!disabled { background-color: #d32f2f; }
"""
BTN_STYLE_REABRIR = """
    QToolButton { background-color: #455a64; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }
    QToolButton:disabled { background-color: #4a4a4a; color: #8a8a8a; border: 1px solid #3a3a3a; }
    QToolButton:hover:!disabled { background-color: #546e7a; }
"""

class MainWindow(QMainWindow):
    def __init__(self, app: AppContext, plugin_manager: PluginManager):
        super().__init__()
        self.app = app
        self.plugin_manager = plugin_manager
        self.plugins = plugin_manager.plugins

        self._settings = app.settings  # único QSettings de la aplicación
        self._left_saved_width = int(self._settings.value("layout/left_width", 300))
        self._right_saved_width = int(self._settings.value("layout/right_width", 300))
        self._left_collapsed = self._settings.value("layout/left_collapsed", False, type=bool)
        self._right_collapsed = self._settings.value("layout/right_collapsed", False, type=bool)
        self._left_auto_shown = False
        self._right_auto_shown = False
        self._last_selected_id = None
        # Mantener vivos los QThread de descarga hasta su finished nativo.
        self._active_download_threads = set()
        self._vm_dependent_tabs = ["Configuración VM", "Snapshots", "Consola Gráfica"]
        # Los títulos visibles cambian con el idioma: guardamos los nombres
        # originales para identificar las pestañas de forma estable.
        self._tab_names = []

        self.setWindowTitle(self.app.tr("Virtual Machine • Administrador QEMU/KVM"))
        self.resize(1400, 900)

        self._build_ui()
        self._load_plugin_ui()
        self._restore_layout_state()
        self._update_tabs_state(False)
        self._setup_shortcuts()
        translate_widgets(self)

        self.app.vm_state_changed.connect(self._refresh_vm_list)
        self.app.vm_state_changed.connect(self._on_state_changed)
        self.app.vm_state_changed.connect(self._on_state_changed_spinner)

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(120)
        self._hover_timer.timeout.connect(self._hover_tick)
        # Solo arrancar si algún panel ya está colapsado al abrir la app
        if self._left_collapsed or self._right_collapsed:
            self._hover_timer.start()

    def closeEvent(self, event):
        self._hover_timer.stop()
        for thread in list(self._active_download_threads):
            if thread.isRunning():
                thread.stop()
                thread.wait(2000)

        for plugin in self.plugins:
            if hasattr(plugin, 'closeEvent'):
                plugin.closeEvent(event)

        super().closeEvent(event)

    def _build_ui(self):
        # Los paneles laterales ya tienen scroll propio: no hace falta que la
        # ventana imponga la altura mínima de todos los widgets internos.
        self.setMinimumHeight(420)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(6)
        self.main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(self.main_splitter)

        # ====== PANEL IZQUIERDO ======
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        header = QHBoxLayout()
        header.addWidget(QLabel(self.app.tr("MÁQUINAS VIRTUALES")))
        header.addStretch()
        self.btn_collapse_left = QToolButton()
        self.btn_collapse_left.setText("📌")
        self.btn_collapse_left.setAutoRaise(True)
        self.btn_collapse_left.setToolTip("Ocultar/mostrar el panel de máquinas virtuales")
        self.btn_collapse_left.clicked.connect(self._toggle_left_panel)
        header.addWidget(self.btn_collapse_left)
        left_layout.addLayout(header)

        self.left_stack = QStackedWidget()

        self.page_list = QWidget()
        pl_layout = QVBoxLayout(self.page_list)
        pl_layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Buscar máquinas...")
        self.input_search.setToolTip("Escribe parte del nombre de una máquina para filtrar la lista")
        self.input_search.textChanged.connect(self._filter_vm_list)
        search_layout.addWidget(self.input_search)

        self.btn_toggle_view = QToolButton()
        self.btn_toggle_view.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        self.btn_toggle_view.setToolTip("Alternar entre vista de lista y vista de tarjetas para las máquinas virtuales")
        self.btn_toggle_view.clicked.connect(self._toggle_vm_view)
        search_layout.addWidget(self.btn_toggle_view)
        pl_layout.addLayout(search_layout)

        self.combo_order = QComboBox()
        self.combo_order.addItems(["Ordenar: Nombre (A-Z)", "Ordenar: Estado"])
        self.combo_order.setToolTip("Ordenar la lista de máquinas por nombre alfabético o por estado")
        self.combo_order.currentIndexChanged.connect(self._sort_vm_list)
        pl_layout.addWidget(self.combo_order)

        self.combo_group = QComboBox()
        self.combo_group.addItem("Todos los grupos")
        self.combo_group.setToolTip("Filtrar máquinas por grupo")
        pl_layout.addWidget(self.combo_group)

        self.list_vms = QListWidget()
        self.list_vms.setIconSize(QSize(30, 30))
        # Altura mínima para que, en pantallas bajas, aparezca la barra de
        # desplazamiento del panel en vez de superponer los combos y botones.
        self.list_vms.setMinimumHeight(240)
        self.list_vms.currentItemChanged.connect(self._on_vm_selected)
        self.list_vms.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_vms.customContextMenuRequested.connect(self._show_vm_context_menu)
        pl_layout.addWidget(self.list_vms)

        btn_layout = QHBoxLayout()
        self.btn_new_vm = QPushButton(self.app.tr("➕ Nueva VM"))
        self.btn_new_vm.setToolTip("Crear una nueva máquina virtual desde cero")
        self.btn_new_vm.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; font-weight: bold; padding: 5px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #1565c0; }"
        )
        self.btn_new_vm.clicked.connect(self._create_new_vm)
        btn_layout.addWidget(self.btn_new_vm)
        pl_layout.addLayout(btn_layout)

        control_layout = QHBoxLayout()
        estilo_menu = """
            QMenu { background-color: palette(window); color: palette(text); border: 1px solid palette(mid); }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background-color: palette(highlight); color: palette(highlighted-text); }
        """

        self.btn_iniciar = QToolButton()
        self.btn_iniciar.setText(self.app.tr("▶ Iniciar"))
        self.btn_iniciar.setToolTip("Iniciar la máquina virtual seleccionada")
        self.btn_iniciar.setStyleSheet(BTN_STYLE_INICIAR)
        self.btn_iniciar.clicked.connect(self._action_start)

        self.btn_pausa = QToolButton()
        self.btn_pausa.setText(self.app.tr("⏸ Pausar"))
        self.btn_pausa.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_pausa.setStyleSheet(BTN_STYLE_PAUSA)
        self.btn_pausa.setToolTip("Pausar o reanudar la máquina virtual seleccionada")
        self.menu_pausa = QMenu(self.btn_pausa)
        self.menu_pausa.setStyleSheet(estilo_menu)
        self._accion_pausar = self.menu_pausa.addAction("⏸ Pausar", self._action_pause)
        self._accion_reanudar = self.menu_pausa.addAction("▶ Reanudar", self._action_resume)
        self.btn_pausa.setMenu(self.menu_pausa)
        self.btn_pausa.clicked.connect(self._action_pause)

        self.btn_apagar = QToolButton()
        self.btn_apagar.setText(self.app.tr("⏹ Apagar"))
        self.btn_apagar.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_apagar.setStyleSheet(BTN_STYLE_APAGAR)
        self.btn_apagar.setToolTip("Apagar, forzar apagado o reiniciar la máquina virtual seleccionada")
        self.menu_apagar = QMenu(self.btn_apagar)
        self.menu_apagar.setStyleSheet(estilo_menu)
        self._accion_apagar = self.menu_apagar.addAction("⏹ Apagar (ACPI)", self._action_stop)
        self._accion_forzar_apagar = self.menu_apagar.addAction("⏻ Forzar apagado", self._action_force_stop)
        self._accion_reiniciar = self.menu_apagar.addAction("🔄 Reiniciar", self._action_reboot)
        self._accion_forzar_reiniciar = self.menu_apagar.addAction("⟲ Forzar reinicio", self._action_force_reboot)
        self.btn_apagar.setMenu(self.menu_apagar)
        self.btn_apagar.clicked.connect(self._action_stop)

        self.btn_reabrir = QToolButton()
        self.btn_reabrir.setText("🖥")
        self.btn_reabrir.setToolTip(
            "Volver a abrir la ventana de la VM si se cerró por error (sin reiniciarla)"
        )
        self.btn_reabrir.setStyleSheet(BTN_STYLE_REABRIR)
        self.btn_reabrir.clicked.connect(self._action_reopen_window)

        btn_group = QWidget()
        btn_group_layout = QHBoxLayout(btn_group)
        btn_group_layout.setContentsMargins(0, 0, 0, 0)
        btn_group_layout.setSpacing(8)
        for btn in (self.btn_iniciar, self.btn_pausa, self.btn_apagar):
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            btn.setMinimumHeight(36)
            btn_group_layout.addWidget(btn)
        # Botón compacto: los otros tres necesitan espacio para sus etiquetas.
        self.btn_reabrir.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        self.btn_reabrir.setMinimumWidth(40)
        self.btn_reabrir.setMinimumHeight(36)
        btn_group_layout.addWidget(self.btn_reabrir)
        control_layout.addWidget(btn_group)
        pl_layout.addLayout(control_layout)

        self.page_welcome = QWidget()
        pw_layout = QVBoxLayout(self.page_welcome)
        pw_layout.setContentsMargins(10, 20, 10, 20)
        pw_layout.setSpacing(10)
        pw_layout.addStretch()

        icons_layout = QHBoxLayout()
        icons_layout.addStretch()
        for emoji in ["🐧", "🪟", "🍎", "🤖"]:
            lbl = QLabel(emoji)
            lbl.setStyleSheet("font-size: 40px;")
            icons_layout.addWidget(lbl)
        icons_layout.addStretch()
        pw_layout.addLayout(icons_layout)

        title = QLabel("Bienvenido a Virtual.Machine")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pw_layout.addWidget(title)

        subtitle = QLabel("Todavía no tienes máquinas virtuales.\nCrea una nueva o importa una existente para empezar.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: palette(mid); font-size: 13px;")
        pw_layout.addWidget(subtitle)

        pw_layout.addSpacing(20)

        btn_welcome_create = QPushButton("➕ Crear una VM nueva")
        btn_welcome_create.setMinimumHeight(50)
        btn_welcome_create.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32; color: white; font-weight: bold;
                font-size: 14px; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #1b5e20; }
        """)
        btn_welcome_create.clicked.connect(self._create_new_vm)
        pw_layout.addWidget(btn_welcome_create)
        pw_layout.addStretch()

        # El panel izquierdo se desplaza entero cuando la ventana es baja:
        # así ningún campo queda tapado por los botones inferiores.
        self.left_scroll = QScrollArea()
        self.left_scroll.setObjectName("left_panel_scroll")
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.left_scroll.setWidget(self.page_list)

        self.left_stack.addWidget(self.left_scroll)
        self.left_stack.addWidget(self.page_welcome)
        left_layout.addWidget(self.left_stack)

        self.left_strip = QWidget()
        self.left_strip.setFixedWidth(16)
        strip_layout = QVBoxLayout(self.left_strip)
        strip_layout.setContentsMargins(0, 5, 0, 5)
        self.btn_expand_left = QToolButton()
        self.btn_expand_left.setText("📌")
        self.btn_expand_left.setAutoRaise(True)
        self.btn_expand_left.setFixedSize(16, 16)
        self.btn_expand_left.clicked.connect(self._toggle_left_panel)
        strip_layout.addWidget(self.btn_expand_left, alignment=Qt.AlignmentFlag.AlignTop)
        strip_layout.addStretch()
        self.left_strip.setVisible(False)

        self.left_wrapper = QWidget()
        self.left_wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        wrapper_layout = QHBoxLayout(self.left_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(self.left_panel)
        wrapper_layout.addWidget(self.left_strip)
        self.main_splitter.addWidget(self.left_wrapper)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.tabs.setMinimumWidth(400)
        self.main_splitter.addWidget(self.tabs)

        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(250)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)

        right_header = QHBoxLayout()
        right_header.addWidget(QLabel(self.app.tr("Uso de recursos")))
        right_header.addStretch()
        self.btn_collapse_right = QToolButton()
        self.btn_collapse_right.setText("📌")
        self.btn_collapse_right.setAutoRaise(True)
        self.btn_collapse_right.setToolTip("Ocultar/mostrar el panel de uso de recursos")
        self.btn_collapse_right.clicked.connect(self._toggle_right_panel)
        right_header.addWidget(self.btn_collapse_right)
        right_layout.addLayout(right_header)

        self.resource_monitor = ResourceMonitor(self.app)
        # El monitor tiene 8 gráficos con altura mínima: en pantallas bajas
        # debe poder desplazarse en vez de recortarse.
        self.right_scroll = QScrollArea()
        self.right_scroll.setObjectName("right_panel_scroll")
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.right_scroll.setWidget(self.resource_monitor)
        right_layout.addWidget(self.right_scroll)

        self.right_strip = QWidget()
        self.right_strip.setFixedWidth(16)
        r_strip_layout = QVBoxLayout(self.right_strip)
        r_strip_layout.setContentsMargins(0, 5, 0, 5)
        self.btn_expand_right = QToolButton()
        self.btn_expand_right.setText("📌")
        self.btn_expand_right.setAutoRaise(True)
        self.btn_expand_right.setFixedSize(16, 16)
        self.btn_expand_right.clicked.connect(self._toggle_right_panel)
        r_strip_layout.addWidget(self.btn_expand_right, alignment=Qt.AlignmentFlag.AlignTop)
        r_strip_layout.addStretch()
        self.right_strip.setVisible(False)

        self.right_wrapper = QWidget()
        self.right_wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        rw_layout = QHBoxLayout(self.right_wrapper)
        rw_layout.setContentsMargins(0, 0, 0, 0)
        rw_layout.addWidget(self.right_strip)
        rw_layout.addWidget(self.right_panel)
        self.main_splitter.addWidget(self.right_wrapper)

        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)
        self._refresh_vm_list()
        self._update_buttons_state()

    def _restore_layout_state(self):
        if self._left_collapsed:
            self.left_panel.setVisible(False)
            self.left_strip.setVisible(True)
        if self._right_collapsed:
            self.right_panel.setVisible(False)
            self.right_strip.setVisible(True)
        self._apply_splitter_sizes()

    def _apply_splitter_sizes(self):
        sizes = self.main_splitter.sizes()
        total = sum(sizes) if sizes and sum(sizes) > 0 else max(self.width(), 800)
        left_visible = (not self._left_collapsed) or self._left_auto_shown
        right_visible = (not self._right_collapsed) or self._right_auto_shown
        left = self._left_saved_width if left_visible else 16
        right = self._right_saved_width if right_visible else 16
        middle = max(400, total - left - right)
        self.main_splitter.setSizes([left, middle, right])

    def _on_splitter_moved(self, pos, index):
        sizes = self.main_splitter.sizes()
        if len(sizes) >= 3:
            if sizes[0] > 16 and not self._left_collapsed and not self._left_auto_shown:
                self._left_saved_width = sizes[0]
                self._settings.setValue("layout/left_width", self._left_saved_width)
            if sizes[2] > 16 and not self._right_collapsed and not self._right_auto_shown:
                self._right_saved_width = sizes[2]
                self._settings.setValue("layout/right_width", self._right_saved_width)

    def _set_vm_action_states(self, state: str):
        """Los menús desplegables siguen al estado real de la VM."""
        acciones = {
            self._accion_pausar: state == "Running",
            self._accion_reanudar: state == "Paused",
            self._accion_apagar: state in ("Running", "Paused", "Apagando..."),
            self._accion_forzar_apagar: state in ("Running", "Paused", "Apagando..."),
            self._accion_reiniciar: state in ("Running", "Paused"),
            self._accion_forzar_reiniciar: state in ("Running", "Paused"),
        }
        for accion, habilitada in acciones.items():
            accion.setEnabled(habilitada)

    def _update_buttons_state(self):
        current = self.list_vms.currentItem()
        if not current:
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(False)
            self.btn_apagar.setEnabled(False)
            self.btn_reabrir.setEnabled(False)
            self._set_vm_action_states("Apagada")
            return

        vm_id = current.data(Qt.ItemDataRole.UserRole)
        vm = self.app.get_vm(vm_id)
        if not vm:
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(False)
            self.btn_apagar.setEnabled(False)
            self.btn_reabrir.setEnabled(False)
            self._set_vm_action_states("Apagada")
            return

        state = vm.get("state", "Apagada")
        # Solo se puede reabrir si hay una ventana externa asociada a una VM
        # encendida. Con VNC embebido el botón queda desactivado.
        self.btn_reabrir.setEnabled(self.app.can_reopen_window(vm_id))

        if state == "Apagando...":
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(False)
            self.btn_pausa.setText(self.app.tr("⏸ Pausar"))
            self.btn_apagar.setEnabled(False)
        elif state == "Running":
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(True)
            self.btn_pausa.setText(self.app.tr("⏸ Pausar"))
            self.btn_apagar.setEnabled(True)
        elif state == "Paused":
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(True)
            self.btn_pausa.setText(self.app.tr("▶ Reanudar"))
            self.btn_apagar.setEnabled(True)
        else:
            self.btn_iniciar.setEnabled(True)
            self.btn_pausa.setEnabled(False)
            self.btn_pausa.setText(self.app.tr("⏸ Pausar"))
            self.btn_apagar.setEnabled(False)
        self._set_vm_action_states(state)

    def _on_state_changed(self, vm_id: str, state: str):
        self._update_buttons_state()

    def _reset_start_button(self):
        """Único punto de salida del estado '⏳ Iniciando…'."""
        self.btn_iniciar.setText(self.app.tr("▶ Iniciar"))
        self.btn_iniciar.setStyleSheet(BTN_STYLE_INICIAR)
        self._update_buttons_state()

    def _on_state_changed_spinner(self, vm_id: str, state: str):
        """Restaura el botón Iniciar cuando la VM termina de arrancar o falla."""
        current_id = self._get_current_vm_id()
        if vm_id != current_id:
            return
        if state in ("Running", "Paused", "Apagada", "Error"):
            self._reset_start_button()

    def _update_tabs_state(self, has_selection: bool):
        for i in range(self.tabs.count()):
            nombre = self._tab_names[i] if i < len(self._tab_names) else self.tabs.tabText(i)
            if nombre in self._vm_dependent_tabs:
                self.tabs.setTabEnabled(i, has_selection)
                if not has_selection and self.tabs.currentIndex() == i:
                    self.tabs.setCurrentIndex(0)

    def _show_vm_context_menu(self, pos):
        item = self.list_vms.itemAt(pos)
        if not item: return

        menu = QMenu(self.list_vms)
        estilo_menu = """
            QMenu { background-color: palette(window); color: palette(text); border: 1px solid palette(mid); }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background-color: palette(highlight); color: palette(highlighted-text); }
        """
        menu.setStyleSheet(estilo_menu)

        vm_id = item.data(Qt.ItemDataRole.UserRole)
        vm = self.app.get_vm(vm_id)
        if not vm:
            return

        state = vm.get("state", "Apagada")

        if state == "Paused":
            action_resume = menu.addAction("▶ Reanudar")
            action_resume.triggered.connect(self._action_resume)

            if self.app.can_reopen_window(vm_id):
                action_reabrir = menu.addAction("🖥 Reabrir ventana de la VM")
                action_reabrir.triggered.connect(lambda: self._reopen_window(vm_id))

            action_hotplug = menu.addAction("🔌 Conectar Hardware (Hotplug)")
            action_hotplug.triggered.connect(lambda: self._open_hotplug(vm_id))

            menu.addSeparator()

            action_stop = menu.addAction("⏹ Apagar (ACPI)")
            action_stop.triggered.connect(self._action_stop)

            action_force_stop = menu.addAction("⏻ Forzar apagado")
            action_force_stop.triggered.connect(self._action_force_stop)

            menu.addSeparator()

        elif state == "Running":
            action_pause = menu.addAction("⏸ Pausar")
            action_pause.triggered.connect(self._action_pause)

            if self.app.can_reopen_window(vm_id):
                action_reabrir = menu.addAction("🖥 Reabrir ventana de la VM")
                action_reabrir.triggered.connect(lambda: self._reopen_window(vm_id))

            action_hotplug = menu.addAction("🔌 Conectar Hardware (Hotplug)")
            action_hotplug.triggered.connect(lambda: self._open_hotplug(vm_id))

            menu.addSeparator()

            action_stop = menu.addAction("⏹ Apagar (ACPI)")
            action_stop.triggered.connect(self._action_stop)

            action_force_stop = menu.addAction("⏻ Forzar apagado")
            action_force_stop.triggered.connect(self._action_force_stop)

            action_reboot = menu.addAction("🔄 Reiniciar")
            action_reboot.triggered.connect(self._action_reboot)

            action_force_reboot = menu.addAction("⟲ Forzar reinicio")
            action_force_reboot.triggered.connect(self._action_force_reboot)

            menu.addSeparator()
        else:
            action_start = menu.addAction("▶ Iniciar")
            action_start.triggered.connect(self._action_start)


            menu.addSeparator()

        action_delete = menu.addAction("🗑 Eliminar VM")
        action_delete.triggered.connect(self._action_delete_vm)

        translate_widgets(menu)
        menu.exec(self.list_vms.mapToGlobal(pos))

    def _open_hotplug(self, vm_id):
        dlg = HotplugDialog(self.app, vm_id, self)
        dlg.exec()

    def _open_hotplug_current(self):
        vm_id = self._get_current_vm_id()
        if vm_id:
            self._open_hotplug(vm_id)
        else:
            QMessageBox.warning(self, "Sin selección", "Selecciona una VM primero.")

    def _reopen_window(self, vm_id):
        if not vm_id:
            QMessageBox.warning(self, "Sin selección", "Selecciona una VM primero.")
            return
        if not self.app.reopen_vm_window(vm_id):
            QMessageBox.information(
                self, "No se puede reabrir",
                "La VM no está encendida o no tiene una ventana externa "
                "(SPICE/VNC) asociada."
            )

    def _action_reopen_window(self):
        self._reopen_window(self._get_current_vm_id())

    def _action_delete_vm(self):
        current = self.list_vms.currentItem()
        if not current: return
        vm_id = current.data(Qt.ItemDataRole.UserRole)
        vm = self.app.get_vm(vm_id)
        vm_name = vm.get("name", "Desconocida") if vm else "Desconocida"
        resp = QMessageBox.question(
            self, "Eliminar VM",
            f"¿Eliminar '{vm_name}'?\n\nEsto borrará la configuración y los discos asociados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            # AppContext espera a que QEMU termine antes de borrar los archivos.
            self.app.delete_vm(vm_id)

    def _toggle_left_panel(self):
        self._left_collapsed = not self._left_collapsed
        self._settings.setValue("layout/left_collapsed", self._left_collapsed)
        self._update_left_visibility()
        self._update_hover_timer()

    def _update_left_visibility(self):
        show_panel = (not self._left_collapsed) or self._left_auto_shown
        self.left_panel.setVisible(show_panel)
        self.left_strip.setVisible(not show_panel)
        self._apply_splitter_sizes()

    def _toggle_right_panel(self):
        self._right_collapsed = not self._right_collapsed
        self._settings.setValue("layout/right_collapsed", self._right_collapsed)
        self._update_right_visibility()
        self._update_hover_timer()

    def _update_right_visibility(self):
        show_panel = (not self._right_collapsed) or self._right_auto_shown
        self.right_panel.setVisible(show_panel)
        self.right_strip.setVisible(not show_panel)
        self._apply_splitter_sizes()

    def _update_hover_timer(self):
        """Arranca el timer solo cuando al menos un panel está colapsado."""
        needs_hover = self._left_collapsed or self._right_collapsed
        if needs_hover and not self._hover_timer.isActive():
            self._hover_timer.start()
        elif not needs_hover and self._hover_timer.isActive():
            self._hover_timer.stop()

    def _hover_tick(self):
        pos = self.mapFromGlobal(QCursor.pos())
        if self._left_collapsed:
            if pos.x() < 5:
                if not self._left_auto_shown:
                    self._left_auto_shown = True
                    self._update_left_visibility()
            else:
                if self._left_auto_shown and pos.x() > self.left_panel.width():
                    self._left_auto_shown = False
                    self._update_left_visibility()
        if self._right_collapsed:
            if pos.x() > self.width() - 5:
                if not self._right_auto_shown:
                    self._right_auto_shown = True
                    self._update_right_visibility()
            else:
                if self._right_auto_shown and pos.x() < self.width() - self.right_panel.width():
                    self._right_auto_shown = False
                    self._update_right_visibility()

    def _refresh_vm_list(self):
        vms = self.app.get_vms()
        if not vms:
            self.left_stack.setCurrentIndex(1)
            self.list_vms.blockSignals(True)
            self.list_vms.clear()
            self.list_vms.blockSignals(False)
            self._update_buttons_state()
            self._update_tabs_state(False)
            return
        else:
            self.left_stack.setCurrentIndex(0)

        current_id = None
        if self.list_vms.currentItem():
            current_id = self.list_vms.currentItem().data(Qt.ItemDataRole.UserRole)
        elif self._last_selected_id:
            current_id = self._last_selected_id

        mode = self.combo_order.currentIndex() if hasattr(self, "combo_order") else 0
        if mode == 0:
            vms.sort(key=lambda x: x["name"].lower())
        elif mode == 1:
            order = {"Running": 0, "Paused": 1, "Apagada": 2}
            vms.sort(key=lambda x: order.get(x.get("state", "Apagada"), 3))

        self.list_vms.blockSignals(True)
        try:
            self.list_vms.clear()
            for vm in vms:
                if self.list_vms.viewMode() == QListView.ViewMode.ListMode:
                    item_text = f"{vm['name']} [{self.app.tr(vm.get('state', 'Apagada'))}]"
                else:
                    item_text = vm["name"]
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, vm["id"])
                item.setData(Qt.ItemDataRole.UserRole + 1, vm["name"].lower())
                item.setData(Qt.ItemDataRole.UserRole + 2, vm.get("state", "Apagada"))
                item.setIcon(os_icon(vm.get("platform")))
                if vm.get("state") == "Running":
                    item.setForeground(Qt.GlobalColor.green)
                self.list_vms.addItem(item)

            if current_id:
                for i in range(self.list_vms.count()):
                    if self.list_vms.item(i).data(Qt.ItemDataRole.UserRole) == current_id:
                        self.list_vms.setCurrentRow(i)
                        break
        finally:
            self.list_vms.blockSignals(False)

        if hasattr(self, "input_search"):
            self._filter_vm_list(self.input_search.text())
        self._update_buttons_state()

        has_selection = self.list_vms.currentItem() is not None
        self._update_tabs_state(has_selection)

    def _filter_vm_list(self, text):
        text = text.lower()
        for i in range(self.list_vms.count()):
            item = self.list_vms.item(i)
            name = item.data(Qt.ItemDataRole.UserRole + 1)
            item.setHidden(text not in name)

    def _sort_vm_list(self):
        self._refresh_vm_list()

    def _toggle_vm_view(self):
        if self.list_vms.viewMode() == QListView.ViewMode.ListMode:
            self.list_vms.setViewMode(QListView.ViewMode.IconMode)
            self.list_vms.setGridSize(QSize(140, 90))
            self.list_vms.setIconSize(QSize(48, 48))
            self.list_vms.setWordWrap(True)
            self.btn_toggle_view.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        else:
            self.list_vms.setViewMode(QListView.ViewMode.ListMode)
            self.list_vms.setIconSize(QSize(32, 32))
            self.btn_toggle_view.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        self._refresh_vm_list()

    def _create_new_vm(self):
        dlg = QuickVMDialog(self.app, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_vm_list()
            vms = self.app.get_vms()
            if vms:
                new_id = vms[-1]["id"]
                for i in range(self.list_vms.count()):
                    if self.list_vms.item(i).data(Qt.ItemDataRole.UserRole) == new_id:
                        self.list_vms.setCurrentRow(i)
                        break

    def _on_vm_selected(self, current, previous):
        if not current:
            self._last_selected_id = None
            self._update_buttons_state()
            self._update_tabs_state(False)
            return
        vm_id = current.data(Qt.ItemDataRole.UserRole)
        changed = (vm_id != self._last_selected_id)
        self._last_selected_id = vm_id

        self.app.vm_selection_changed.emit(vm_id)
        if hasattr(self, "resource_monitor"):
            self.resource_monitor.set_vm(vm_id)
        self._update_buttons_state()
        self._update_tabs_state(True)

        if changed:
            self.tabs.setCurrentIndex(0)

    def _get_current_vm_id(self):
        current = self.list_vms.currentItem()
        return current.data(Qt.ItemDataRole.UserRole) if current else None

    # ============================================================
    # LÓGICA DE ARRANQUE CON VALIDACIÓN DE ISO Y SINGLE GPU
    # ============================================================
    def _action_start(self):
        vm_id = self._get_current_vm_id()
        if not vm_id: return

        vm = self.app.get_vm(vm_id)
        if not vm: return

        # Mostrar spinner inmediatamente para dar feedback visual mientras QEMU arranca
        self.btn_iniciar.setText(self.app.tr("⏳ Iniciando…"))
        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setStyleSheet(
            "QToolButton { background-color: #4a4a4a; color: #aaaaaa; "
            "padding: 5px; font-weight: bold; border-radius: 3px; }"
        )
        so = vm.get("so", "")
        iso_path = vm.get("iso_path")
        iso_source_type = vm.get("iso_source_type", "")

        versiones_antiguas = ["Windows 8.1", "Windows 8", "Windows 7", "Windows Vista", "Windows XP"]
        if so in versiones_antiguas:
            QMessageBox.critical(self, "No soportado", f"Microsoft ya no distribuye ISOs de {so}.")
            self._reset_start_button()
            return

        needs_download = False
        vm_has_disk = bool(vm.get("disk_path"))

        if iso_source_type == "Descargar" and not vm_has_disk:
            needs_download = True

        try:
            iso_valida = bool(
                iso_path and os.path.isfile(iso_path)
                and iso_path.lower().endswith((".iso", ".img", ".dmg"))
                and os.path.getsize(iso_path) >= 100 * 1024 * 1024
            )
        except OSError as e:
            log.warning("No se pudo comprobar la ISO %s: %s", iso_path, e)
            iso_valida = False

        if not iso_valida and not vm_has_disk and iso_sources.supports_auto_download(so):
            needs_download = True

        if iso_valida:
            needs_download = False

        # La ISO anterior se conserva hasta que la nueva descarga termine:
        # DownloadStartThread la sustituye con replace() atómico.
        if needs_download:
            if vm.get("platform") == "macOS":
                self._download_macos_and_start(vm_id, vm)
            else:
                self._download_and_start(vm_id, vm)
            return

        self.app.start_vm(vm_id)
        mode_idx = vm.get("console_mode_idx") or 0
        if mode_idx != 4:
            self._goto_tab("Consola Gráfica")

    def _download_macos_and_start(self, vm_id, vm):
        self.progress_dlg = QProgressDialog("Preparando descarga de macOS...", "Cancelar", 0, 0, self)
        self.progress_dlg.setWindowTitle(f"macOS {vm.get('version', '')}")
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        self.progress_dlg.show()

        dest_dir = self.app.isos_dir / "macos"
        version_label = vm.get("version_id") or vm.get("version") or "Ventura (13) ⭐ [ÓPTIMO]"
        self.macos_downloader = MacOSDownloader(version_label, dest_dir, self.app.data_dir)

        def on_progress(msg):
            if "\n" in msg:
                parts = msg.split("\n", 1)
                self.progress_dlg.setWindowTitle(parts[0])
                self.progress_dlg.setLabelText(parts[1])
            else:
                self.progress_dlg.setLabelText(msg)

        def on_finished(path):
            self.progress_dlg.setValue(100)
            self.progress_dlg.close()
            self._reset_start_button()
            self.app.vm_repo.update(vm_id, {"iso_path": path})
            self.app.start_vm(vm_id)
            self._goto_tab("Consola Gráfica")

        def on_error(err):
            self.progress_dlg.close()
            self._reset_start_button()
            QMessageBox.critical(self, "Error", f"Fallo al descargar macOS:\n{err}")

        self.macos_downloader.progress.connect(on_progress)
        self.macos_downloader.finished.connect(on_finished)
        self.macos_downloader.error.connect(on_error)

        self.progress_dlg.canceled.connect(self.macos_downloader.process.kill)

        self.macos_downloader.start()

    def _download_and_start(self, vm_id, vm):
        vm_name = vm.get('name', 'VM')
        so = vm.get('so', '')
        ver = vm.get('version', '')
        dlg = self.progress_dlg = QProgressDialog(
            f"Preparando descarga para {so} {ver}...", "Cancelar", 0, 100, self)
        dlg.setWindowTitle(self.app.tr("Descargando {}").format(vm_name))
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setAutoClose(False)
        dlg.show()  # antes no se mostraba: no había feedback de progreso

        # Capturamos dlg/thread en closures: una descarga posterior no debe
        # actualizar el diálogo de la anterior.
        thread = self.dl_thread = DownloadStartThread(vm, self.app.isos_dir)
        self._active_download_threads.add(thread)
        thread.finished.connect(
            lambda t=thread: self._active_download_threads.discard(t))

        def on_progress(pct, text):
            if pct > 0:
                dlg.setRange(0, 100)
                dlg.setValue(pct)
            else:
                dlg.setRange(0, 0)
            if "\n" in text:
                parts = text.split("\n", 1)
                dlg.setWindowTitle(parts[0])
                dlg.setLabelText(parts[1])
            else:
                dlg.setWindowTitle(text)
                dlg.setLabelText("")

        def on_finished(path):
            dlg.setValue(100)
            dlg.close()
            self._reset_start_button()
            self.app.vm_repo.update(vm_id, {
                "iso_path": path,
                "iso_sha256": thread.sha256,
            })
            self.app.start_vm(vm_id)
            self._goto_tab("Consola Gráfica")

        def on_error(err):
            dlg.close()
            self._reset_start_button()
            if "Windows" in so:
                msg = QMessageBox(self)
                msg.setWindowTitle("Descarga manual necesaria")
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setText(
                    "<b>Microsoft está bloqueando la descarga automática.</b><br><br>"
                    "Descarga la ISO manualmente desde la web de Microsoft."
                )
                msg.exec()
            else:
                QMessageBox.critical(self, "Error de descarga", f"No se pudo descargar la ISO:\n{err}")

        def on_canceled():
            dlg.close()
            self._reset_start_button()

        thread.progress.connect(on_progress)
        thread.download_finished.connect(on_finished)
        thread.error.connect(on_error)
        thread.download_canceled.connect(on_canceled)
        dlg.canceled.connect(thread.stop)
        thread.start()

    def _action_pause(self):
        vm_id = self._get_current_vm_id()
        if not vm_id: return
        vm = self.app.get_vm(vm_id)
        if vm and vm.get("state") == "Paused":
            self.app.resume_vm(vm_id)
        else:
            self.app.pause_vm(vm_id)

    def _action_resume(self):
        vm_id = self._get_current_vm_id()
        if vm_id: self.app.resume_vm(vm_id)

    def _action_stop(self):
        vm_id = self._get_current_vm_id()
        if vm_id: self.app.stop_vm(vm_id)

    def _action_force_stop(self):
        vm_id = self._get_current_vm_id()
        if vm_id: self.app.force_stop_vm(vm_id)

    def _action_reboot(self):
        vm_id = self._get_current_vm_id()
        if vm_id: self.app.reboot_vm(vm_id)

    def _action_force_reboot(self):
        vm_id = self._get_current_vm_id()
        if vm_id: self.app.force_reboot_vm(vm_id)

    # -------------------------------------------------- atajos y comandos
    def _setup_shortcuts(self):
        self._shortcuts = ShortcutStore(self._settings)
        self._shortcut_actions = {}
        menu = self.menuBar().addMenu("&Herramientas")
        for comando in self._shortcut_commands():
            accion = QAction(comando["label"], self)
            if comando["shortcut"]:
                accion.setShortcut(QKeySequence(comando["shortcut"]))
            accion.triggered.connect(comando["callback"])
            # Registrar en la ventana para que funcionen aunque el menú esté oculto.
            self.addAction(accion)
            menu.addAction(accion)
            self._shortcut_actions[comando["id"]] = accion

    def _shortcut_commands(self):
        store = getattr(self, "_shortcuts", ShortcutStore(self._settings))

        def cmd(nombre, callback):
            return {"id": nombre, "label": COMMAND_LABELS[nombre],
                    "shortcut": store.get(nombre), "callback": callback}

        return [
            cmd("command_palette", self._show_command_palette),
            cmd("new_vm", self._create_new_vm),
            cmd("start_vm", self._action_start),
            cmd("stop_vm", self._action_stop),
            cmd("reopen_window", self._action_reopen_window),
            cmd("history", lambda: self._call_plugin("Dashboard", "_show_history")),
            cmd("from_template", lambda: self._call_plugin("Dashboard", "_new_from_template")),
            cmd("save_template", lambda: self._call_plugin("Dashboard", "_save_as_template")),
            cmd("go_media", lambda: self._goto_tab("Medios")),
            cmd("go_snapshots", lambda: self._goto_tab("Snapshots")),
            cmd("shortcut_settings", self._show_shortcut_settings),
        ]

    def _apply_shortcuts(self):
        for comando in self._shortcut_commands():
            accion = self._shortcut_actions.get(comando["id"])
            if accion is not None:
                accion.setShortcut(QKeySequence(comando["shortcut"])
                                   if comando["shortcut"] else QKeySequence())

    def _call_plugin(self, nombre, metodo):
        for plugin in self.plugins:
            if getattr(plugin, "name", None) == nombre:
                callback = getattr(plugin, metodo, None)
                if callback:
                    callback()
                return

    def _show_command_palette(self):
        from ui_widgets.command_palette import CommandPalette

        dlg = CommandPalette(self._shortcut_commands(), self)
        dlg.exec()

    def _show_shortcut_settings(self):
        from ui_widgets.shortcut_settings import ShortcutSettingsDialog

        dlg = ShortcutSettingsDialog(self._shortcuts, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._apply_shortcuts()

    def _goto_tab(self, name: str) -> bool:
        for i in range(self.tabs.count()):
            nombre = self._tab_names[i] if i < len(self._tab_names) else self.tabs.tabText(i)
            if nombre == name:
                self.tabs.setTabEnabled(i, True)
                self.tabs.setCurrentIndex(i)
                return True
        return False

    def _load_plugin_ui(self):
        all_tabs = []
        for plugin in self.plugins:
            for tab_name, widget in plugin.get_tabs():
                all_tabs.append((tab_name, widget))

        order_map = {
            "Resumen": 10, "Configuración VM": 20, "Configuración Host": 30,
            "Snapshots": 40, "Medios": 50, "Consola Gráfica": 60,
            "Consola de Progreso": 70, "Ayuda": 80
        }
        icon_map = {
            "Resumen": "SP_FileDialogInfoView", "Configuración VM": "SP_ComputerIcon",
            "Configuración Host": "SP_DriveHDIcon", "Snapshots": "SP_DialogSaveButton",
            "Medios": "SP_DirIcon", "Consola Gráfica": "SP_DesktopIcon",
            "Consola de Progreso": "SP_MessageBoxInformation", "Ayuda": "SP_DialogHelpButton"
        }

        all_tabs.sort(key=lambda t: order_map.get(t[0], 99))

        for tab_name, widget in all_tabs:
            if tab_name == "Consola Gráfica":
                wrapper = QWidget()
                w_layout = QVBoxLayout(wrapper)
                w_layout.setContentsMargins(0, 0, 0, 0)
                w_layout.setSpacing(0)

                tb = QHBoxLayout()
                tb.setContentsMargins(5, 5, 5, 5)
                btn_hotplug = QPushButton("🔌 Conectar Hardware (Hotplug)")
                btn_hotplug.setStyleSheet(
                    "QPushButton { padding: 6px 12px; font-weight: bold; background-color: #1976d2; color: white; border-radius: 3px; }"
                    "QPushButton:hover { background-color: #1565c0; }"
                )
                btn_hotplug.clicked.connect(self._open_hotplug_current)
                tb.addWidget(btn_hotplug)
                tb.addStretch()
                w_layout.addLayout(tb)

                w_layout.addWidget(widget)
                widget = wrapper

            icon_name = icon_map.get(tab_name, "")
            icon = QIcon()
            if icon_name:
                icon = self.style().standardIcon(getattr(QStyle.StandardPixmap, icon_name, QStyle.StandardPixmap.SP_FileIcon))
            self.tabs.addTab(widget, icon, tab_name)
            self._tab_names.append(tab_name)

        if "Ayuda" not in [t[0] for t in all_tabs]:
            help_widget = QWidget()
            help_layout = QVBoxLayout(help_widget)
            help_layout.setContentsMargins(20, 20, 20, 20)
            help_layout.addWidget(QLabel("<h2>Ayuda de Virtual.Machine</h2>"))
            help_layout.addWidget(QLabel("Versión 1.0 - Documentación próximamente."))
            help_layout.addStretch()
            icon_help = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton)
            self.tabs.addTab(help_widget, icon_help, "Ayuda")
            self._tab_names.append("Ayuda")