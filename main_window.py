import logging
import uuid
import shutil
import os
import requests
import threading
from pathlib import Path
from urllib.parse import urlparse, unquote
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QSplitter, QTabWidget, QLabel, QPushButton, 
    QScrollArea, QToolButton, QInputDialog, QMessageBox, QMenu,
    QLineEdit, QComboBox, QStyle, QListView, QStackedWidget, QSizePolicy,
    QDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, QSize, QSettings, QThread, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from core import AppContext, PluginManager
from ui_widgets.resource_monitor import ResourceMonitor
from ui_widgets.quick_vm_dialog import QuickVMDialog
from services import iso_versions
from services import iso_sources
from services.macos_recovery import MacOSDownloader

log = logging.getLogger(__name__)

# ============================================================
# HILO PARA DESCARGAR ISO AL ARRANCAR LA VM
# ============================================================
class DownloadStartThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, vm, data_dir):
        super().__init__()
        self.vm = vm
        self.data_dir = data_dir
        
    def run(self):
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
                self.error.emit(f"No se encontró URL para {so}")
                return
                
            iso_dir = self.data_dir / "isos"
            iso_dir.mkdir(exist_ok=True)
            
            # Extraer nombre del archivo (SourceForge termina en /download)
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
            part_path = iso_dir / (filename + ".part")
            
            if part_path.exists():
                try: part_path.unlink()
                except: pass
            if dest_path.exists():
                try: dest_path.unlink()
                except: pass

            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) VirtualMachine/1.0'}
            
            response = requests.get(url, stream=True, headers=headers, timeout=(15, 120))
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            
            with open(part_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
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
            
            if total > 0 and downloaded < total:
                raise Exception("La descarga se interrumpió antes de terminar.")
                
            part_path.rename(dest_path)
            self.finished.emit(str(dest_path))
        except Exception as e:
            if 'part_path' in locals() and part_path.exists():
                try: part_path.unlink()
                except: pass
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

class MainWindow(QMainWindow):
    def __init__(self, app: AppContext, plugin_manager: PluginManager):
        super().__init__()
        self.app = app
        self.plugin_manager = plugin_manager
        self.plugins = plugin_manager.plugins

        self._settings = QSettings("VirtualMachine", "VirtualMachine")
        self._left_saved_width = int(self._settings.value("layout/left_width", 300))
        self._right_saved_width = int(self._settings.value("layout/right_width", 300))
        self._left_collapsed = self._settings.value("layout/left_collapsed", False, type=bool)
        self._right_collapsed = self._settings.value("layout/right_collapsed", False, type=bool)
        self._left_auto_shown = False
        self._right_auto_shown = False
        self._last_selected_id = None
        self._vm_dependent_tabs = ["Configuración VM", "Snapshots", "Consola Gráfica"]

        self.setWindowTitle(self.app.tr("Virtual Machine • Administrador QEMU/KVM"))
        self.resize(1400, 900)

        self._build_ui()
        self._load_plugin_ui()
        self._restore_layout_state()
        self._update_tabs_state(False)

        self.app.vm_state_changed.connect(self._refresh_vm_list)
        self.app.vm_state_changed.connect(self._on_state_changed)

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(120)
        self._hover_timer.timeout.connect(self._hover_tick)
        self._hover_timer.start()

    def closeEvent(self, event):
        self._hover_timer.stop()
        if hasattr(self, 'dl_thread') and self.dl_thread.isRunning():
            self.dl_thread.quit()
            self.dl_thread.wait(2000)
        
        for plugin in self.plugins:
            if hasattr(plugin, 'closeEvent'):
                plugin.closeEvent(event)
                
        super().closeEvent(event)

    def _build_ui(self):
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
        self.input_search.textChanged.connect(self._filter_vm_list)
        search_layout.addWidget(self.input_search)

        self.btn_toggle_view = QToolButton()
        self.btn_toggle_view.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        self.btn_toggle_view.setToolTip("Alternar entre vista de lista y tarjetas")
        self.btn_toggle_view.clicked.connect(self._toggle_vm_view)
        search_layout.addWidget(self.btn_toggle_view)
        pl_layout.addLayout(search_layout)

        self.combo_order = QComboBox()
        self.combo_order.addItems(["Ordenar: Nombre (A-Z)", "Ordenar: Estado"])
        self.combo_order.currentIndexChanged.connect(self._sort_vm_list)
        pl_layout.addWidget(self.combo_order)

        self.combo_group = QComboBox()
        self.combo_group.addItem("Todos los grupos")
        pl_layout.addWidget(self.combo_group)

        self.list_vms = QListWidget()
        self.list_vms.currentItemChanged.connect(self._on_vm_selected)
        self.list_vms.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_vms.customContextMenuRequested.connect(self._show_vm_context_menu)
        pl_layout.addWidget(self.list_vms)

        btn_layout = QHBoxLayout()
        self.btn_new_vm = QPushButton(self.app.tr("➕ Nueva VM"))
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
        self.btn_iniciar.setText("▶ Iniciar")
        self.btn_iniciar.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_iniciar.setStyleSheet(BTN_STYLE_INICIAR)
        self.menu_iniciar = QMenu(self.btn_iniciar)
        self.menu_iniciar.setStyleSheet(estilo_menu)
        self.menu_iniciar.addAction("▶ Iniciar", self._action_start)
        self.menu_iniciar.addAction("🖥️ Iniciar en pantalla completa", self._action_start_fullscreen)
        self.btn_iniciar.setMenu(self.menu_iniciar)
        self.btn_iniciar.clicked.connect(self._action_start)

        self.btn_pausa = QToolButton()
        self.btn_pausa.setText("⏸ Pausar")
        self.btn_pausa.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_pausa.setStyleSheet(BTN_STYLE_PAUSA)
        self.menu_pausa = QMenu(self.btn_pausa)
        self.menu_pausa.setStyleSheet(estilo_menu)
        self.menu_pausa.addAction("⏸ Pausar", self._action_pause)
        self.menu_pausa.addAction("▶ Reanudar", self._action_resume)
        self.btn_pausa.setMenu(self.menu_pausa)
        self.btn_pausa.clicked.connect(self._action_pause)

        self.btn_apagar = QToolButton()
        self.btn_apagar.setText("⏹ Apagar")
        self.btn_apagar.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_apagar.setStyleSheet(BTN_STYLE_APAGAR)
        self.menu_apagar = QMenu(self.btn_apagar)
        self.menu_apagar.setStyleSheet(estilo_menu)
        self.menu_apagar.addAction("⏹ Apagar (ACPI)", self._action_stop)
        self.menu_apagar.addAction("⏻ Forzar apagado", self._action_force_stop)
        self.menu_apagar.addAction("🔄 Reiniciar", self._action_reboot)
        self.menu_apagar.addAction("⟲ Forzar reinicio", self._action_force_reboot)
        self.btn_apagar.setMenu(self.menu_apagar)
        self.btn_apagar.clicked.connect(self._action_stop)

        control_layout.addWidget(self.btn_iniciar)
        control_layout.addWidget(self.btn_pausa)
        control_layout.addWidget(self.btn_apagar)
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

        self.left_stack.addWidget(self.page_list)
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
        self.btn_collapse_right.clicked.connect(self._toggle_right_panel)
        right_header.addWidget(self.btn_collapse_right)
        right_layout.addLayout(right_header)

        self.resource_monitor = ResourceMonitor(self.app)
        right_layout.addWidget(self.resource_monitor)

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

    def _update_buttons_state(self):
        current = self.list_vms.currentItem()
        if not current:
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(False)
            self.btn_apagar.setEnabled(False)
            return

        vm_id = current.data(Qt.ItemDataRole.UserRole)
        vm = self.app.get_vm(vm_id)
        if not vm:
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(False)
            self.btn_apagar.setEnabled(False)
            return

        state = vm.get("state", "Apagada")
        if state == "Running":
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(True)
            self.btn_pausa.setText("⏸ Pausar")
            self.btn_apagar.setEnabled(True)
        elif state == "Paused":
            self.btn_iniciar.setEnabled(False)
            self.btn_pausa.setEnabled(True)
            self.btn_pausa.setText("▶ Reanudar")
            self.btn_apagar.setEnabled(True)
        else:
            self.btn_iniciar.setEnabled(True)
            self.btn_pausa.setEnabled(False)
            self.btn_pausa.setText("⏸ Pausar")
            self.btn_apagar.setEnabled(False)

    def _on_state_changed(self, vm_id: str, state: str):
        self._update_buttons_state()
        
    def _update_tabs_state(self, has_selection: bool):
        for i in range(self.tabs.count()):
            tab_text = self.tabs.tabText(i)
            if tab_text in self._vm_dependent_tabs:
                self.tabs.setTabEnabled(i, has_selection)
                if not has_selection and self.tabs.currentIndex() == i:
                    self.tabs.setCurrentIndex(0)

    def _show_vm_context_menu(self, pos):
        item = self.list_vms.itemAt(pos)
        if not item: return
        menu = QMenu(self.list_vms)
        menu.setStyleSheet("""
            QMenu { background-color: palette(window); color: palette(text); border: 1px solid palette(mid); }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background-color: palette(highlight); color: palette(highlighted-text); }
        """)
        action_start = menu.addAction("▶ Iniciar")
        action_start.triggered.connect(self._action_start)
        action_delete = menu.addAction("🗑 Eliminar VM")
        action_delete.triggered.connect(self._action_delete_vm)
        menu.exec(self.list_vms.mapToGlobal(pos))

    def _action_delete_vm(self):
        current = self.list_vms.currentItem()
        if not current: return
        vm_id = current.data(Qt.ItemDataRole.UserRole)
        vm = self.app.get_vm(vm_id)
        vm_name = vm.get("name", "Desconocida") if vm else "Desconocida"
        resp = QMessageBox.question(
            self, "Eliminar VM", f"¿Eliminar '{vm_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.app.delete_vm(vm_id)
            vm_dir = self.app.data_dir / "vms" / vm_id
            if vm_dir.exists():
                try: shutil.rmtree(vm_dir)
                except Exception: pass

    def _toggle_left_panel(self):
        self._left_collapsed = not self._left_collapsed
        self._settings.setValue("layout/left_collapsed", self._left_collapsed)
        self._update_left_visibility()

    def _update_left_visibility(self):
        show_panel = (not self._left_collapsed) or self._left_auto_shown
        self.left_panel.setVisible(show_panel)
        self.left_strip.setVisible(not show_panel)
        self._apply_splitter_sizes()

    def _toggle_right_panel(self):
        self._right_collapsed = not self._right_collapsed
        self._settings.setValue("layout/right_collapsed", self._right_collapsed)
        self._update_right_visibility()

    def _update_right_visibility(self):
        show_panel = (not self._right_collapsed) or self._right_auto_shown
        self.right_panel.setVisible(show_panel)
        self.right_strip.setVisible(not show_panel)
        self._apply_splitter_sizes()

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
                item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
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
    # LÓGICA DE ARRANQUE CON VALIDACIÓN DE ISO
    # ============================================================
    def _action_start(self):
        vm_id = self._get_current_vm_id()
        if not vm_id: return
        
        vm = self.app.get_vm(vm_id)
        if not vm: return
        
        so = vm.get("so", "")
        iso_path = vm.get("iso_path")
        iso_source_type = vm.get("iso_source_type", "")
        
        # Validación para Windows antiguos
        versiones_antiguas = ["Windows 8.1", "Windows 8", "Windows 7", "Windows Vista", "Windows XP"]
        if so in versiones_antiguas:
            QMessageBox.critical(self, "No soportado", f"Microsoft ya no distribuye ISOs de {so}.")
            return
        
        # Determinar si necesitamos descargar
        needs_download = False
        
        if iso_source_type == "Descargar":
            needs_download = True
        
        # Si no hay ISO o no es válida (tamaño, extensión), forzar descarga si se soporta
        iso_valida = (iso_path and os.path.exists(iso_path) 
                      and iso_path.lower().endswith((".iso", ".img", ".dmg"))
                      and os.path.getsize(iso_path) >= 100 * 1024 * 1024)
        
        if not iso_valida and iso_sources.supports_auto_download(so):
            needs_download = True
        
        # Si hay ISO válida, no descargar (aunque iso_source_type sea "Descargar")
        if iso_valida:
            needs_download = False
        
        # Limpiar archivo inválido si vamos a descargar
        if needs_download and iso_path and os.path.exists(iso_path):
            try:
                os.remove(iso_path)
            except:
                pass
        
        if needs_download:
            if vm.get("platform") == "macOS":
                self._download_macos_and_start(vm_id, vm)
            else:
                self._download_and_start(vm_id, vm)
            return
            
        self.app.start_vm(vm_id)
        self._goto_tab("Consola Gráfica")

    def _download_macos_and_start(self, vm_id, vm):
        self.progress_dlg = QProgressDialog("Preparando descarga de macOS...", "Cancelar", 0, 0, self)
        self.progress_dlg.setWindowTitle(f"macOS {vm.get('version', '')}")
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        self.progress_dlg.show()

        dest_dir = self.app.isos_dir / "macos"
        self.macos_downloader = MacOSDownloader(vm.get("version", "Ventura (13) ⭐ [ÓPTIMO]"), dest_dir, self.app.data_dir)
        
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
            self.app.vm_repo.update(vm_id, {"iso_path": path})
            self.app.start_vm(vm_id)
            self._goto_tab("Consola Gráfica")
            
        def on_error(err):
            self.progress_dlg.close()
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
        self.progress_dlg = QProgressDialog(f"Preparando descarga para {so} {ver}...", "Cancelar", 0, 100, self)
        self.progress_dlg.setWindowTitle(f"Descargando {vm_name}")
        self.progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dlg.setAutoClose(False)
        
        self.dl_thread = DownloadStartThread(vm, self.app.data_dir)
        
        def on_progress(pct, text):
            if pct > 0:
                self.progress_dlg.setRange(0, 100)
                self.progress_dlg.setValue(pct)
            else:
                self.progress_dlg.setRange(0, 0)
            if "\n" in text:
                parts = text.split("\n")
                self.progress_dlg.setWindowTitle(parts[0])
                self.progress_dlg.setLabelText(parts[1])
            else:
                self.progress_dlg.setWindowTitle(text)
                self.progress_dlg.setLabelText("")
                
        def on_finished(path):
            self.progress_dlg.setValue(100)
            self.progress_dlg.close()
            self.app.vm_repo.update(vm_id, {"iso_path": path})
            self.app.start_vm(vm_id)
            self._goto_tab("Consola Gráfica")
            
        def on_error(err):
            self.progress_dlg.close()
            if "Windows" in so:
                msg = QMessageBox(self)
                msg.setWindowTitle("Descarga manual necesaria")
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setText(
                    f"<b>Microsoft está bloqueando la descarga automática.</b><br><br>"
                    f"Descarga la ISO manualmente desde la web de Microsoft."
                )
                msg.exec()
            else:
                QMessageBox.critical(self, "Error de descarga", f"No se pudo descargar la ISO:\n{err}")
            
        self.dl_thread.progress.connect(on_progress)
        self.dl_thread.finished.connect(on_finished)
        self.dl_thread.error.connect(on_error)
        
        self.progress_dlg.canceled.connect(self.dl_thread.quit)
        
        self.dl_thread.start()

    def _action_start_fullscreen(self):
        QMessageBox.information(self, "Pantalla completa", "Función en desarrollo.")

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

    def _goto_tab(self, name: str) -> bool:
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
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
            icon_name = icon_map.get(tab_name, "")
            icon = QIcon()
            if icon_name:
                icon = self.style().standardIcon(getattr(QStyle.StandardPixmap, icon_name, QStyle.StandardPixmap.SP_FileIcon))
            self.tabs.addTab(widget, icon, tab_name)

        if "Ayuda" not in [t[0] for t in all_tabs]:
            help_widget = QWidget()
            help_layout = QVBoxLayout(help_widget)
            help_layout.setContentsMargins(20, 20, 20, 20)
            help_layout.addWidget(QLabel("<h2>Ayuda de Virtual.Machine</h2>"))
            help_layout.addWidget(QLabel("Versión 1.0 - Documentación próximamente."))
            help_layout.addStretch()
            icon_help = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton)
            self.tabs.addTab(help_widget, icon_help, "Ayuda")