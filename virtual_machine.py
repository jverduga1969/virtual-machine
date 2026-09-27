# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

import sys
import os
import re
import json
import shutil
import shlex
import glob
import zipfile
import configparser
import threading
import subprocess
import uuid
from datetime import date, timedelta
import time
from pathlib import Path
import requests
from packaging import version
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, 
    QLineEdit, QComboBox, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QPlainTextEdit, QMessageBox, QGroupBox,
    QStackedWidget, QRadioButton, QButtonGroup, QFileDialog, QCheckBox, QListWidget, QListWidgetItem, QInputDialog, QTabWidget, QSplitter, QDialog, QFormLayout, QGridLayout, QFrame, QSlider, QTreeWidget, QTreeWidgetItem, QScrollArea, QSizePolicy, QProgressBar, QProgressDialog, QSpinBox, QToolButton, QMenu
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QSettings, QSize, QObject
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QPixmap, QAction

# Combinaciones ofrecidas para salir de la pantalla completa de la consola VNC.
# Cada tupla es (etiqueta visible, valor guardado). El valor "RCTRL" es un
# caso especial: no es una combinación de QKeySequence sino la tecla física
# Control derecha SOLA (igual que la "tecla anfitriona" por defecto de
# VirtualBox) — se detecta aparte, por scancode, porque Qt no distingue
# Ctrl izquierdo de Ctrl derecho dentro de un QKeySequence. El resto de
# valores sí son cadenas válidas de QKeySequence.
# Se evita como valor por defecto cualquier tecla que la VM invitada suela
# necesitar recibir (Escape, F11...), por eso el default es RCTRL.
FULLSCREEN_EXIT_SHORTCUTS = [
    ("Ctrl derecho (como VirtualBox)", "RCTRL"),
    ("Ctrl+F11", "Ctrl+F11"),
    ("Ctrl+Alt+Intro", "Ctrl+Alt+Return"),
    ("Meta+Escape", "Meta+Escape"),
    ("Escape", "Escape"),
]
DEFAULT_FULLSCREEN_EXIT_SHORTCUT = FULLSCREEN_EXIT_SHORTCUTS[0][1]

# Carpeta base donde se guarda cada máquina virtual en su propia subcarpeta,
# dentro del mismo directorio desde donde se ejecuta el programa.
# --- Módulos extraídos (Fase 1 de modularización) ---
# Cada uno es autocontenido (sin PyQt) y puede probarse/importarse por separado;
# aquí se re-exportan sus nombres para no tener que tocar el resto del archivo.
import vm_config
from vm_config import list_existing_vms, get_os_profile, save_vm_config, load_vm_config
from iso_sources import SUPPORTED_AUTODETECT, get_latest_iso_url, get_latest_windows_iso_url
import iso_versions
import principal_cdrom
from network_utils import (
    list_host_network_interfaces, list_host_bridges,
    network_interface_exists, sanitize_tap_name,
)
from host_deps import (
    ensure_osx_kvm_present, detect_linux_package_manager, find_ovmf_files,
    ovmf_available, detect_host_graphics, prewarm_host_capabilities,
    get_virtualization_dependency_status, ensure_virtualization_dependencies,
    pci_preflight_host,
)
from shared_folders import (
    bash_squote, find_virtiofsd, get_shared_folder_dependency_status,
    ensure_shared_folder_dependencies,
)
from guest_tools_iso import (
    GUEST_TOOLS_ISO_NAME, GUEST_TOOLS_WINDOWS_URLS,
    build_simple_iso9660, create_guest_tools_iso,
)

# --- Módulos extraídos (Fase 2 de modularización) ---
from workers import (
    DownloadCancelled, InstallWorker, _qemu_safe_identifier,
    SnapshotOperationWorker, _BackgroundCallThread,
)
from dialogs import RealtimePerformanceGraph, NetworkDeviceDialog, DiskCreationDialog

# --- Módulos extraídos (Fase 3 de modularización) ---
from snapshots_mixin import SnapshotsMixin
from network_config_mixin import NetworkConfigMixin
from performance_mixin import PerformanceMixin
from diagnostics_mixin import DiagnosticsMixin
from mac_recovery_mixin import MacRecoveryMixin
from guest_integration_mixin import GuestIntegrationMixin
from passthrough_mixin import PassthroughMixin
from storage_mixin import StorageMixin
from vm_lifecycle_mixin import VmLifecycleMixin
from install_flow_mixin import InstallFlowMixin
from suggestions_mixin import SuggestionsMixin
from async_ui_mixin import AsyncUiMixin
from snapshots_graph import SnapshotsGraphView
from console_ui_mixin import ConsoleUiMixin
from console_backend import (
    PROTOCOL_VNC, PROTOCOL_SPICE, MODE_EMBEDDED, MODE_EXTERNAL, MODE_NATIVE,
    MODE_HYBRID, MODE_HYBRID_GL,
    DEFAULT_PROTOCOL, DEFAULT_MODE, describe_requirements,
    find_viewer, console_uri, socket_path as _cb_socket_path,
)
try:
    from spice_widget import SpiceConsoleWidget
    _HAS_SPICE_WIDGET = True
except Exception as _spice_exc:
    SpiceConsoleWidget = None
    _HAS_SPICE_WIDGET = False
    _SPICE_WIDGET_ERROR = _spice_exc

# Widget VNC embebido: si el import falla, intentamos arreglarlo
# automáticamente con bootstrap_vnc (instala qvncwidget + python-xlib
# y regenera la carpeta local vnc_widget/ si falta). Si aun así no
# está disponible, guardamos el motivo para mostrarlo en la consola
# de progreso en cuanto la ventana principal esté lista.
_VNC_IMPORT_ERROR = None
try:
    from vnc_widget import QVNCWidget
    _HAS_VNC_WIDGET = True
except Exception as _vnc_import_exc:
    _HAS_VNC_WIDGET = False
    QVNCWidget = None
    _VNC_IMPORT_ERROR = _vnc_import_exc
    try:
        from bootstrap_vnc import ensure_vnc_available
        _boot_ok, _boot_err = ensure_vnc_available()
    except Exception as _boot_exc:
        _boot_ok, _boot_err = False, str(_boot_exc)
    if _boot_ok:
        try:
            from vnc_widget import QVNCWidget
            _HAS_VNC_WIDGET = True
            _VNC_IMPORT_ERROR = None
        except Exception as _retry_exc:
            _VNC_IMPORT_ERROR = _retry_exc
    else:
        _VNC_IMPORT_ERROR = _boot_err or _vnc_import_exc


# --- Estilo estructural (respeta el tema claro/oscuro del sistema operativo) ---
# A propósito NO se fijan background-color/color generales: eso lo decide el
# tema del SO (Qt ya sigue el tema del sistema en la mayoría de escritorios).
# Solo se dan acentos de color (selección, hover, pestaña activa) que se ven
# bien tanto en temas claros como oscuros, y estructura (bordes redondeados,
# espaciado) que la maqueta mostraba independientemente del tema.
APP_QSS = """
QGroupBox {
    border: 1px solid palette(mid);
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QListWidget {
    border: 1px solid palette(mid);
    border-radius: 8px;
    outline: none;
}
QListWidget::item {
    padding: 8px;
    border-radius: 6px;
    margin: 2px;
}
QListWidget::item:selected {
    background-color: palette(highlight);
    border: 1px solid #2e6fd6;
}
QTabWidget::pane {
    border: 1px solid palette(mid);
    border-radius: 8px;
}
QTabBar::tab {
    padding: 8px 16px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    border-bottom: 2px solid #2e6fd6;
    font-weight: bold;
}
QPushButton {
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover {
    border: 1px solid #2e6fd6;
}
QLineEdit, QComboBox, QSpinBox, QTreeWidget {
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px 6px;
}
QComboBox::drop-down {
    border: none;
}
QTextEdit#consoleBox {
    background-color: #0a0e17;
    color: #4ade80;
    font-family: monospace;
    border: 1px solid #232b40;
}

/* Estilo de la sidebar de Configuración (secciones tipo asistente). */
QListWidget#configSidebar {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 8px;
    padding: 6px;
    outline: none;
}
QListWidget#configSidebar::item {
    padding: 10px 12px;
    border-radius: 6px;
    margin: 1px;
    color: palette(text);
}
QListWidget#configSidebar::item:hover:!selected {
    background: palette(alternate-base);
}
QListWidget#configSidebar::item:selected {
    background: #1e40af;
    color: white;
    font-weight: bold;
}
QFrame#configInfoBox {
    background: rgba(30, 64, 175, 40);
    border: 1px solid rgba(59, 130, 246, 120);
    border-radius: 8px;
}
"""


class _LinVersionsBridge(QObject):
    """Entrega al hilo de la interfaz el resultado de la consulta de versiones.

    La consulta corre en un hilo daemon de Python (no en un QThread): si se cierra
    la ventana mientras un espejo tarda en responder, el hilo simplemente muere con
    el proceso, en lugar de provocar "QThread: Destroyed while thread is still
    running"."""
    done = pyqtSignal(int, str, object, object)  # token, distro, versiones, error


class VirtualMachineManagerApp(SnapshotsMixin, NetworkConfigMixin, PerformanceMixin, DiagnosticsMixin, MacRecoveryMixin, GuestIntegrationMixin, PassthroughMixin, StorageMixin, VmLifecycleMixin, InstallFlowMixin, AsyncUiMixin, SuggestionsMixin, ConsoleUiMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtual.Machine 38.1 • Administrador QEMU/KVM")
        # Ventana redimensionable: tamaño inicial cómodo, sin bloquear al usuario.
        self.current_vm_dir = None
        self.disk_size_setting = "128G"
        self.disk_type_setting = "dynamic"
        self.disk_format_setting = "qcow2"
        self.disk_ext_setting = "qcow2"
        self.setMinimumSize(760, 600)
        self.resize(1080, 760)
        os.makedirs(vm_config.BASE_VM_DIR, exist_ok=True)
        self.init_hardware_info()
        self.init_ui()

    def init_hardware_info(self):
        self.physical_ram_gb = 8
        mem_available_kb = None
        mem_total_kb = None
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        mem_total_kb = int(line.split()[1])
                        self.physical_ram_gb = mem_total_kb // (1024 * 1024)
                    elif line.startswith('MemAvailable'):
                        mem_available_kb = int(line.split()[1])
        except:
            pass

        self.mem_total_gb = round(mem_total_kb / (1024 * 1024), 1) if mem_total_kb else float(self.physical_ram_gb)
        if mem_available_kb is not None and mem_total_kb:
            self.mem_free_gb = round(mem_available_kb / (1024 * 1024), 1)
            self.mem_used_gb = round(self.mem_total_gb - self.mem_free_gb, 1)
        else:
            self.mem_free_gb = self.mem_used_gb = 0.0

        self.physical_cores = os.cpu_count() or 4

        self.cpu_model = "Desconocido"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.lower().startswith('model name'):
                        self.cpu_model = line.split(':', 1)[1].strip()
                        break
        except:
            pass

        self.board_name = "Desconocido"
        for path in ('/sys/devices/virtual/dmi/id/board_name', '/sys/class/dmi/id/board_name'):
            try:
                with open(path, 'r') as f:
                    val = f.read().strip()
                    if val:
                        self.board_name = val
                        break
            except:
                continue

        self.has_avx2 = True
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'avx2' not in f.read():
                    self.has_avx2 = False
        except:
            pass

    def init_ui(self):
        """Punto de entrada de la construcción de la UI.

        Delega en métodos pequeños para mantener el archivo legible.
        Durante el refactor, cada _build_* sin poblar delega al legacy;
        una vez migrado un bloque, se elimina su delegación.
        """
        self._setup_window_state()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        self._build_toolbar(main_layout)
        self._build_header(main_layout)
        self._build_hw_info(main_layout)
        self._build_name_and_platform(main_layout)
        self._build_hardware_group(main_layout)
        self._build_storage_group(main_layout)
        self._build_deps_group(main_layout)

        self._build_main_container(main_layout)
        self._wire_signals()
        self._apply_initial_state()

    def _setup_window_state(self):
        """Configura estado inicial de la ventana y atributos de la clase.
        Este método debe ejecutarse ANTES que cualquier _build_*."""
        self.setWindowTitle("Virtual.Machine 38.1 • Administrador QEMU/KVM")
        self.setMinimumSize(760, 600)
        self.resize(1080, 760)
        self.current_vm_dir = None
        self.disk_size_setting = "128G"
        self.disk_type_setting = "dynamic"
        self.disk_format_setting = "qcow2"
        self.disk_ext_setting = "qcow2"
        os.makedirs(vm_config.BASE_VM_DIR, exist_ok=True)
        self.init_hardware_info()
        # Los histogramas de rendimiento se inicializan aquí para evitar
        # AttributeError si algún _build_* los usa antes de tiempo.
        self._perf_cpu_hist = []
        self._perf_ram_hist = []
        self._perf_disk_hist = []
        self._perf_net_hist = []
        self._perf_prev_net = None
        self._perf_prev_io = None
        self._perf_prev_time = None
        # Estado para pantalla completa del widget VNC (ventana temporal).
        self._vnc_fullscreen_window = None
        self._vnc_original_layout = None
        # Seguimiento de a qué VM está conectado cada widget de consola.
        # Al cambiar de VM en la lista lateral se comparan estos valores
        # con self.current_vm_dir para decidir si hay que reconectar.
        self._vnc_widget_vm_dir = None
        self._spice_widget_vm_dir = None
        # Un visor externo POR VM. Cambiar de VM en la lista no cierra
        # los visores de las otras VMs.
        self._external_viewers = {}
        # Seguimiento de a qué VM está conectado cada widget de consola.
        # Al cambiar de VM en la lista lateral, se comparan estos
        # valores con self.current_vm_dir y se destruye el widget
        # obsoleto antes de crear uno nuevo.
        self._vnc_widget_vm_dir = None
        self._spice_widget_vm_dir = None
        self._external_viewer_vm_dir = None
        # Watchdog de QEMU: estado anterior por VM y flags de
        # muertes inesperadas sin atender.
        self._vm_last_state = {}
        self._vm_death_flag = set()

    def _build_toolbar(self, main_layout):
        """La barra superior de Configuración ya no se usa: el buscador de
        VMs se movió al panel izquierdo (visible desde cualquier pestaña)
        y los botones de acciones de VM viven en 'Resumen'.

        Se deja este método como no-op para preservar la llamada en
        init_ui() sin tener que tocar más código.
        """
        pass


    def _build_header(self, main_layout):
        """Cabecera: ya no muestra estado ni botones (era redundante con la
        sección 'Virtualización'). Se conservan los atributos para que las
        llamadas externas (refresh_dependency_status, _set_dependency_status_unchecked)
        sigan funcionando sin AttributeError."""
        # Widgets que otras partes del código siguen referenciando.
        # No se añaden al layout: la información vive ahora en la sección
        # 'Virtualización' de Configuración.
        self.header_host_status = QLabel("")
        self.header_host_status.setVisible(False)
        self.btn_check_deps_header = QPushButton("🔄")
        self.btn_check_deps_header.setVisible(False)
        self.btn_repair_deps_header = QPushButton("🛠️")
        self.btn_repair_deps_header.setVisible(False)


    def _build_hw_info(self, main_layout):
        """Línea informativa con hardware del host."""
        hw_info_text = QLabel(
            f"🖥️ {self.board_name} | ⚙️ {self.cpu_model} | 🧵 {self.physical_cores} hilos | "
            f"📊 RAM {self.mem_total_gb} GB (libre {self.mem_free_gb} GB)"
        )
        hw_info_text.setWordWrap(True)
        hw_info_text.setMinimumWidth(0)
        hw_info_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        hw_info_text.setStyleSheet("background-color: palette(alternate-base); padding: 5px 8px; border-radius: 4px; font-size: 10px;")
        main_layout.addWidget(hw_info_text)

    def _build_name_and_platform(self, main_layout):
        """Fila superior: Nombre de VM · Plataforma · Versión de SO.

        Orden de operaciones importante:
          1. Crear el stack de versiones (con los combos dentro).
          2. Guardarlo como self.version_selector_stack y self.stack_pages.
          3. Añadirlo al layout.
        Este orden evita el error histórico de 'se llamó al método antes
        de que el stack existiera'.
        """
        name_label = QLabel("<b>Nombre de VM:</b>")
        name_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.input_vm_name = QLineEdit()
        self.input_vm_name.setMinimumWidth(90)
        self.input_vm_name.setMaximumWidth(180)
        self.input_vm_name.setPlaceholderText("ej. mi-ubuntu")
        self.input_vm_name.setEnabled(False)

        # Barra de acciones rápidas de la VM seleccionada.
        vm_actions = QHBoxLayout()
        self.btn_vm_summary = QPushButton("📋 Resumen")
        self.btn_vm_folder = QPushButton("📂 Carpeta")
        self.btn_vm_clone = QPushButton("🧬 Clonar")
        self.btn_vm_delete = QPushButton("🗑️ Eliminar")
        for btn in (self.btn_vm_summary, self.btn_vm_folder, self.btn_vm_clone, self.btn_vm_delete):
            btn.setMinimumHeight(30)
            vm_actions.addWidget(btn)
        vm_actions.addStretch()
        # vm_actions NO se añade a main_layout: sus botones están
        # ocultos y solo dejaban una franja vacía entre la info de
        # hardware y el nombre de la VM. Los slots siguen conectados
        # más abajo (self.btn_vm_summary.clicked.connect...).
        self.btn_vm_summary.clicked.connect(self.show_vm_summary)
        self.btn_vm_folder.clicked.connect(self.open_vm_folder)
        self.btn_vm_clone.clicked.connect(self.clone_current_vm)
        self.btn_vm_delete.clicked.connect(self.delete_current_vm)

        self.vm_status_label = QLabel("● Nueva VM")
        self.vm_status_label.setStyleSheet("color: #757575; font-weight: bold; padding: 2px 6px;")
        # self.vm_status_label tampoco se añade al layout: el estado
        # de la VM ya se muestra en el panel derecho 'Información general'.

        # Fila superior: Nombre · Plataforma · Versión de SO.
        h_main_os = QHBoxLayout()
        h_main_os.setSpacing(8)
        h_main_os.addWidget(name_label)
        h_main_os.addWidget(self.input_vm_name)
        h_main_os.addSpacing(14)
        h_main_os.addWidget(QLabel("<b>Plataforma:</b>"))
        self.combo_main_os = QComboBox()
        self.combo_main_os.addItem("macOS", "macos")
        self.combo_main_os.addItem("Microsoft Windows", "windows")
        self.combo_main_os.addItem("GNU / Linux", "linux")
        self.combo_main_os.setMaximumWidth(200)
        self.combo_main_os.currentIndexChanged.connect(self.change_os_panel)
        self.combo_main_os.currentIndexChanged.connect(self.maybe_autofill_vm_name)
        self.combo_main_os.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        h_main_os.addWidget(self.combo_main_os)
        h_main_os.addSpacing(14)
        h_main_os.addWidget(QLabel("<b>Versión de SO:</b>"))

        # 1) Construir el stack con los combos dentro.
        # 2) Guardarlo.
        # 3) Añadirlo al layout.
        self.version_selector_stack = self._build_version_selector_contents()
        self.stack_pages = self.version_selector_stack
        h_main_os.addWidget(self.version_selector_stack)

        # Versión de la ISO a descargar (solo GNU / Linux). Se rellena en segundo plano.
        h_main_os.addSpacing(14)
        self.label_lin_version = QLabel("<b>Versión ISO:</b>")
        self.combo_lin_version = QComboBox()
        self.combo_lin_version.setMinimumWidth(210)
        self.combo_lin_version.setMaximumWidth(300)
        for _txt, _val in self._lin_version_base_items():
            self.combo_lin_version.addItem(_txt, _val)
        h_main_os.addWidget(self.label_lin_version)
        h_main_os.addWidget(self.combo_lin_version)
        self.btn_lin_iso_browse = QPushButton("📁")
        self.btn_lin_iso_browse.setMaximumWidth(34)
        self.btn_lin_iso_browse.setToolTip("Elegir el archivo ISO de tu computador")
        self.btn_lin_iso_browse.setVisible(False)
        self.btn_lin_iso_browse.clicked.connect(self._browse_lin_own_iso)
        h_main_os.addWidget(self.btn_lin_iso_browse)
        self.label_lin_version.setVisible(False)
        self.combo_lin_version.setVisible(False)
        self._lin_ver_bridge = _LinVersionsBridge(self)
        self._lin_ver_bridge.done.connect(self._on_lin_versions_ready)
        self.combo_lin_distro.currentIndexChanged.connect(self._refresh_lin_versions)
        self.combo_main_os.currentIndexChanged.connect(self._refresh_lin_versions)
        self.combo_lin_version.currentIndexChanged.connect(self._on_lin_version_picked)
        h_main_os.addStretch()
        main_layout.addLayout(h_main_os)


    def _build_hardware_group(self, main_layout):
        # Asegurar que los combos de versión (macOS/Windows/Linux) existan.
        # Idempotente: el método tiene un guard interno que evita recrearlos.
        """Configuración estilo asistente: sidebar de secciones + stack de páginas.

        Todos los widgets conservan el mismo nombre que en la versión anterior
        (combo_firmware, check_secure_boot, slider_ram, etc.), por lo que el
        resto del código (aplicar perfil de SO, guardar/cargar config, señales)
        sigue funcionando sin cambios.
        """

        container = QWidget()
        shell = QHBoxLayout(container)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(10)

        # --- Sidebar de secciones ---
        # IMPORTANTE: NO usar emoji en el texto de los items. Kvantum
        # (el motor de estilo de KDE) segfaulta al medir QListWidgetItems
        # cuyo texto contiene emoji, en QTextEngine::itemize. Los iconos
        # van por setIcon() con QStyle.StandardPixmap: son iconos
        # vectoriales nativos y Kvantum los maneja sin problema.
        self.config_sidebar = QListWidget()
        self.config_sidebar.setObjectName("configSidebar")
        self.config_sidebar.setFixedWidth(200)
        self.config_sidebar.setFrameShape(QListWidget.Shape.NoFrame)
        self.config_sidebar.setSpacing(2)
        self.config_sidebar.setIconSize(QSize(18, 18))
        from PyQt6.QtWidgets import QStyle as _QStyle
        _sections = [
            (_QStyle.StandardPixmap.SP_ComputerIcon, "Sistema"),
            (_QStyle.StandardPixmap.SP_ComputerIcon, "Procesador"),
            (_QStyle.StandardPixmap.SP_DriveHDIcon, "Memoria"),
            (_QStyle.StandardPixmap.SP_DesktopIcon, "Pantalla"),
            (_QStyle.StandardPixmap.SP_DriveHDIcon, "Almacenamiento"),
            (_QStyle.StandardPixmap.SP_DriveNetIcon, "Red"),
            (_QStyle.StandardPixmap.SP_DriveFDIcon, "Dispositivos"),
            (_QStyle.StandardPixmap.SP_FileDialogDetailedView, "Virtualización"),
        ]
        _style = self.style()
        for pixmap_enum, label in _sections:
            it = QListWidgetItem("  " + label)
            it.setIcon(_style.standardIcon(pixmap_enum))
            it.setData(Qt.ItemDataRole.UserRole, label)
            self.config_sidebar.addItem(it)

        # --- Stack de páginas ---
        self.config_stack = QStackedWidget()
        self.config_stack.setObjectName("configStack")
        self.config_sidebar.currentRowChanged.connect(self.config_stack.setCurrentIndex)
        self.config_sidebar.setCurrentRow(0)

        shell.addWidget(self.config_sidebar)
        shell.addWidget(self.config_stack, 1)
        main_layout.addWidget(container)
        # Empujar el contenido hacia arriba: sin este addStretch, el
        # QVBoxLayout reparte el espacio sobrante entre los ítems
        # y deja huecos visibles entre las secciones.
        main_layout.addStretch(1)

        # Crear páginas vacías en el orden de _sections.
        self._config_page_layouts = {}
        for _, label in _sections:
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setContentsMargins(22, 18, 22, 18)
            lay.setSpacing(14)
            self.config_stack.addWidget(page)
            self._config_page_layouts[label] = lay

        # Poblar cada página.
        self._populate_config_sistema()
        self._populate_config_procesador()
        self._populate_config_memoria()
        self._populate_config_pantalla()
        # Almacenamiento: se rellena desde _build_storage_group.
        self._populate_config_red()
        self._populate_config_dispositivos()
        self._populate_config_otros()

        # Ahora que TODOS los widgets existen (firmware, chipset, cpu,
        # graphics, secure_boot, tpm, etc.), aplicar el perfil del SO
        # seleccionado una sola vez. Antes de este punto, llamar a
        # apply_os_profile_defaults fallaba porque combo_cpu_model y
        # combo_graphics aún no se habían creado.
        try:
            self.apply_os_profile_defaults()
        except Exception as _profile_err:
            # No abortar la UI si el perfil no se puede aplicar: el usuario
            # siempre puede configurarlo a mano.
            import sys as _sys
            print(f"[AVISO] No se pudo aplicar el perfil del SO al arrancar: {_profile_err}", file=_sys.stderr)

        self.config_sidebar.currentRowChanged.connect(self._on_config_section_changed)

    def _config_section_title(self, text, subtitle=""):
        """Devuelve un widget con título + subtítulo para la parte superior
        de cada sección. Se usa desde los _populate_*."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(2)
        title = QLabel(f"<b style='font-size:16px;'>{text}</b>")
        lay.addWidget(title)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setWordWrap(True)
            sub.setStyleSheet("color:#888; font-size:11px;")
            lay.addWidget(sub)
        return w

    def _on_config_section_changed(self, row):
        """Se llama al cambiar de sección. Aprovechamos para asegurar que la
        sección de almacenamiento se muestre correctamente aunque su contenido
        se rellene desde otro método."""
        pass

    def _populate_config_sistema(self):
        lay = self._config_page_layouts["Sistema"]
        lay.addWidget(self._config_section_title(
            "Sistema",
            "Plataforma, firmware y opciones de bajo nivel del hardware virtual.",
        ))

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)

        # Firmware (antes se llamaba 'Plataforma' aquí dentro; se renombra
        # para no confundirlo con la 'Plataforma' de la fila superior, que
        # es en realidad el tipo de SO: macOS / Windows / Linux).
        grid.addWidget(QLabel("<b>Firmware</b>"), 0, 0)
        self.combo_firmware = QComboBox()
        self.combo_firmware.addItem("BIOS (tradicional)", "bios")
        self.combo_firmware.addItem("UEFI (OVMF)", "uefi")
        self.combo_firmware.setMinimumWidth(180)
        self.combo_firmware.currentIndexChanged.connect(self.update_firmware_options_visibility)
        self.combo_firmware.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        grid.addWidget(self.combo_firmware, 1, 0)

        # Chipset (sube a la columna derecha, antes ocupada por 'Versión').
        grid.addWidget(QLabel("<b>Chipset</b>"), 0, 1)
        self.combo_chipset = QComboBox()
        self.combo_chipset.addItem("i440FX (clásico)", "pc")
        self.combo_chipset.addItem("Q35 (moderno, PCIe)", "q35")
        self.combo_chipset.setToolTip(
            "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\n"
            "Q35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\n"
            "passthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica."
        )
        self.combo_chipset.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        grid.addWidget(self.combo_chipset, 1, 1)

        # Secure Boot / TPM como toggles (checkboxes estilizadas)
        grid.addWidget(QLabel("<b>Seguridad</b>"), 4, 0, 1, 2)
        self.security_options_widget = QWidget()
        sec_layout = QHBoxLayout(self.security_options_widget)
        sec_layout.setContentsMargins(0, 0, 0, 0)
        sec_layout.setSpacing(24)

        self.check_secure_boot = QCheckBox("Secure Boot")
        self.check_secure_boot.setProperty("toggleSwitch", True)
        self.check_secure_boot.stateChanged.connect(lambda *_: self._update_vm_summary())
        sec_layout.addWidget(self.check_secure_boot)

        self.check_tpm = QCheckBox("TPM 2.0")
        self.check_tpm.setProperty("toggleSwitch", True)
        self.check_tpm.stateChanged.connect(lambda *_: self._update_vm_summary())
        sec_layout.addWidget(self.check_tpm)
        sec_layout.addStretch()
        grid.addWidget(self.security_options_widget, 5, 0, 1, 2)

        lay.addLayout(grid)

        # Perfiles del sistema (caja informativa azul, como en el mockup)
        profile_box = QFrame()
        profile_box.setObjectName("configInfoBox")
        profile_lay = QVBoxLayout(profile_box)
        profile_lay.setContentsMargins(14, 12, 14, 12)
        profile_lay.setSpacing(4)
        ptitle = QLabel("<b>Perfiles del sistema</b>")
        profile_lay.addWidget(ptitle)
        self.profile_hint_label = QLabel(
            "Configuración optimizada para el sistema operativo seleccionado. "
            "Puede modificar los valores según sus necesidades."
        )
        self.profile_hint_label.setWordWrap(True)
        profile_lay.addWidget(self.profile_hint_label)
        lay.addWidget(profile_box)

        # Opciones avanzadas
        adv_title = QLabel("<b>Opciones avanzadas</b>")
        lay.addWidget(adv_title)
        adv_grid = QGridLayout()
        adv_grid.setHorizontalSpacing(20)
        adv_grid.setVerticalSpacing(6)

        self.check_acpi = QCheckBox("Habilitar ACPI")
        self.check_acpi.setChecked(True)
        self.check_apic = QCheckBox("Habilitar APIC")
        self.check_apic.setChecked(True)
        self.check_iommu = QCheckBox("Habilitar IOMMU")
        self.check_pcie_root = QCheckBox("PCIe Root Port")

        adv_grid.addWidget(self.check_acpi, 0, 0)
        adv_grid.addWidget(self.check_apic, 1, 0)
        adv_grid.addWidget(self.check_iommu, 0, 1)
        adv_grid.addWidget(self.check_pcie_root, 1, 1)
        lay.addLayout(adv_grid)
        lay.addStretch()

    def _build_version_selector_contents(self):
        """Construye y DEVUELVE un QStackedWidget ya relleno con los tres
        selectores de versión (macOS / Windows / Linux).

        Importante: este método NO usa self.version_selector_stack para
        nada. Lo construye desde cero y lo devuelve. El llamador se
        encarga de asignarlo y añadirlo al layout. Esto elimina de raíz
        el problema del 'se llamó antes de que el stack existiera' que
        rompía la UI anteriormente.

        Los combos se guardan como atributos de instancia
        (combo_macos_ver / combo_win_ver / combo_lin_distro) porque el
        resto del código (open_vm, change_os_panel, guardar/cargar
        configuración) los usa directamente.
        """
        stack = QStackedWidget()
        stack.setMinimumWidth(180)
        stack.setMaximumWidth(280)

        # --- macOS ---
        page_macos = QWidget()
        v_mac = QVBoxLayout(page_macos)
        v_mac.setContentsMargins(0, 0, 0, 0)
        self.combo_macos_ver = QComboBox()
        self.os_options = [
            ("High Sierra (10.13)", "1"), ("Mojave (10.14)", "2"), ("Catalina (10.15)", "3"),
            ("Big Sur (11.7)", "4"), ("Monterey (12.6)", "5"), ("Ventura (13)", "6"),
            ("Sonoma (14)", "7"), ("Sequoia (15)", "8"), ("Tahoe", "9")
        ]
        rec_idx = 7 if self.has_avx2 and self.physical_ram_gb >= 16 else 5
        for i, (name, _) in enumerate(self.os_options):
            self.combo_macos_ver.addItem(name + (" ⭐ [ÓPTIMO]" if i == rec_idx else ""))
        # Bloquear señales: apply_os_profile_defaults usa widgets que se
        # crean más adelante (combo_cpu_model, combo_graphics). Se llamará
        # una vez al final de _build_hardware_group.
        self.combo_macos_ver.blockSignals(True)
        self.combo_macos_ver.setCurrentIndex(rec_idx)
        self.combo_macos_ver.blockSignals(False)
        self.combo_macos_ver.currentIndexChanged.connect(self.maybe_autofill_vm_name)
        self.combo_macos_ver.currentIndexChanged.connect(self.apply_os_profile_defaults)
        v_mac.addWidget(self.combo_macos_ver)

        # Campos ocultos de macOS (compatibilidad con configs antiguas).
        self.radio_mac_recovery = QRadioButton("Usar System Recovery")
        self.radio_mac_custom = QRadioButton("Usar imagen existente")
        self.mac_mode_group = QButtonGroup(self)
        self.mac_mode_group.addButton(self.radio_mac_recovery)
        self.mac_mode_group.addButton(self.radio_mac_custom)
        self.radio_mac_recovery.setChecked(True)
        self.input_mac_custom_iso = QLineEdit()
        self.btn_mac_browse = QPushButton("📁")
        self.btn_mac_browse.setMaximumWidth(40)
        self.btn_mac_browse.clicked.connect(lambda: self.browse_iso(self.input_mac_custom_iso))
        self.radio_mac_recovery.toggled.connect(self.toggle_mac_iso_mode)
        for _w in (self.radio_mac_recovery, self.radio_mac_custom,
                   self.input_mac_custom_iso, self.btn_mac_browse):
            _w.setVisible(False)
        stack.addWidget(page_macos)

        # --- Windows ---
        page_win = QWidget()
        v_win = QVBoxLayout(page_win)
        v_win.setContentsMargins(0, 0, 0, 0)
        self.combo_win_ver = QComboBox()
        for v in ("Windows 11", "Windows 10", "Windows 7",
                  "Windows Vista", "Windows XP", "Windows 2000"):
            self.combo_win_ver.addItem(v)
        self.combo_win_ver.currentIndexChanged.connect(self.maybe_autofill_vm_name)
        self.combo_win_ver.currentIndexChanged.connect(self.apply_windows11_defaults)
        self.combo_win_ver.currentIndexChanged.connect(self.apply_os_profile_defaults)
        v_win.addWidget(self.combo_win_ver)

        self.input_win_iso = QLineEdit()
        self.check_win_auto = QCheckBox("Auto-detectar y descargar la última ISO retail")
        self.check_win_auto.toggled.connect(self.toggle_win_iso_mode)
        for _w in (self.input_win_iso, self.check_win_auto):
            _w.setVisible(False)
        stack.addWidget(page_win)

        # --- Linux ---
        page_linux = QWidget()
        v_lin = QVBoxLayout(page_linux)
        v_lin.setContentsMargins(0, 0, 0, 0)
        self.combo_lin_distro = QComboBox()
        self.combo_lin_distro.addItems([
            "Linux Mint", "MX Linux", "Ubuntu", "Debian", "Manjaro Linux",
            "Fedora", "Pop!_OS", "Zorin OS", "elementary OS", "openSUSE",
            "Arch Linux", "EndeavourOS", "Kali Linux", "AlmaLinux", "Rocky Linux",
            "CachyOS", "Solus", "antiX", "Alpine Linux", "Void Linux"
        ])
        self.combo_lin_distro.currentIndexChanged.connect(self.maybe_autofill_vm_name)
        self.combo_lin_distro.currentIndexChanged.connect(self.apply_os_profile_defaults)
        v_lin.addWidget(self.combo_lin_distro)
        stack.addWidget(page_linux)

        return stack


    # ------------------------------------------------------------------
    # Selector de versión de la distro Linux (ISO que se descargará)
    # ------------------------------------------------------------------
    _LIN_LATEST_TEXT = "Más reciente (automático)"
    _LIN_NONE_TEXT = "Ninguna (elegir mi propia ISO)"

    def _lin_version_base_items(self):
        return [(self._LIN_LATEST_TEXT, ""), (self._LIN_NONE_TEXT, principal_cdrom.CHOICE_NONE)]

    def _selected_lin_version(self):
        """Id de la versión de ISO elegida ('' = la más reciente).

        Mientras la lista se está cargando se devuelve la versión que se quiere
        conservar (p. ej. la guardada en la VM), para que guardar en ese momento
        no la pierda."""
        if getattr(self, "_lin_ver_loading", False):
            return getattr(self, "_lin_ver_keep", "") or ""
        combo = getattr(self, "combo_lin_version", None)
        return (combo.currentData() or "") if combo is not None else ""

    def _refresh_lin_versions(self, *_args, select=None):
        """Rellena combo_lin_version con las versiones de la distro elegida.

        La consulta a los espejos va en un hilo para no congelar la interfaz.
        `select` es el id que debe quedar seleccionado al terminar (al abrir una
        VM, el guardado); si es None se conserva la selección actual."""
        combo = getattr(self, "combo_lin_version", None)
        if combo is None:
            return
        is_linux = self.combo_main_os.currentData() == "linux"
        self.label_lin_version.setVisible(is_linux)
        combo.setVisible(is_linux)
        if not is_linux:
            return  # no se consulta la red si no se está configurando una VM Linux

        distro = self.combo_lin_distro.currentText()
        # 'select' solo llega al ABRIR una VM guardada; un cambio de distro hecho
        # a mano por el usuario siempre debe resetear a 'Más reciente', nunca
        # arrastrar la versión que tenía seleccionada la distro anterior.
        keep = select if select is not None else ""
        self._lin_ver_token = getattr(self, "_lin_ver_token", 0) + 1
        token = self._lin_ver_token

        combo.blockSignals(True)
        combo.clear()
        for _txt, _val in self._lin_version_base_items():
            combo.addItem(_txt, _val)
        combo.blockSignals(False)
        self._update_lin_iso_browse_visibility()

        if not iso_versions.supports_auto_download(distro):
            self._lin_ver_loading = False
            combo.setItemText(0, "Sin descarga automática")
            combo.setEnabled(False)
            combo.setToolTip(f"{distro} no tiene descarga automática: añade tu propia ISO en la unidad CD/DVD.")
            return
        if not iso_versions.supports_versions(distro):
            self._lin_ver_loading = False
            combo.setEnabled(False)
            combo.setToolTip(f"Para {distro} solo está disponible la versión más reciente.")
            return

        self._lin_ver_loading = True
        self._lin_ver_keep = keep
        combo.setItemText(0, "Buscando versiones...")
        combo.setEnabled(False)
        combo.setToolTip("Consultando los espejos oficiales...")

        bridge = self._lin_ver_bridge

        def _fetch():
            try:
                versions, err = iso_versions.list_distro_versions(distro), None
            except Exception as e:  # red caída, espejo cambiado, etc.
                versions, err = [], e
            try:
                bridge.done.emit(token, distro, versions, err)
            except RuntimeError:
                pass  # la ventana ya se cerró

        threading.Thread(target=_fetch, name="lin-versions", daemon=True).start()

    def _on_lin_versions_ready(self, token, distro, versions, error):
        if token != getattr(self, "_lin_ver_token", None):
            return  # el usuario cambió de distro o de plataforma mientras tanto
        self._apply_lin_versions(distro, versions or [], error, getattr(self, "_lin_ver_keep", ""))

    def _apply_lin_versions(self, distro, versions, error, keep):
        combo = self.combo_lin_version
        self._lin_ver_loading = False
        if self.combo_lin_distro.currentText() != distro:
            return
        combo.blockSignals(True)
        combo.clear()
        for _txt, _val in self._lin_version_base_items():
            combo.addItem(_txt, _val)
        for v in versions:
            combo.addItem(v["label"], v["id"])
        if keep and keep != principal_cdrom.CHOICE_NONE and combo.findData(keep) < 0:
            # Versión guardada que ya no aparece en el espejo (o no hubo red): se
            # conserva para que abrir y guardar la VM no la cambie sin avisar.
            combo.addItem(f"{keep} (guardada)", keep)
        combo.setCurrentIndex(max(0, combo.findData(keep)) if keep else 0)
        combo.blockSignals(False)
        combo.setEnabled(True)
        if error is not None:
            combo.setToolTip("No se pudieron consultar las versiones ("
                             + str(error)[:140] + "). Se usará la más reciente o la guardada.")
        else:
            combo.setToolTip(f"{len(versions)} versiones disponibles de {distro}.")
        self._update_lin_iso_browse_visibility()

    def _update_lin_iso_browse_visibility(self):
        is_none = self._selected_lin_version() == principal_cdrom.CHOICE_NONE
        self.btn_lin_iso_browse.setVisible(is_none)

    def _own_lin_iso_path(self):
        """Ruta de la ISO propia ya elegida (para no perderla al reabrir el diálogo)."""
        if not self.current_vm_dir:
            return ""
        devices = self._storage_devices_all(self.current_vm_dir)
        p = principal_cdrom.find_principal(devices)
        return (p.get("path") or p.get("own_iso") or "") if p else ""

    def _browse_lin_own_iso(self):
        from PyQt6.QtWidgets import QFileDialog
        start_dir = os.path.dirname(self._own_lin_iso_path())
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen ISO", start_dir,
            "Imágenes de disco (*.iso *.img);;Todos los archivos (*)")
        if not path:
            return
        if not self._ensure_storage_target_vm():
            return
        self._apply_lin_principal_choice(own_iso=path)
        self.log_message(f"==> ISO propia seleccionada para Principal: {os.path.basename(path)}")

    def _on_lin_version_picked(self, *_args):
        self._update_lin_iso_browse_visibility()
        if self._selected_lin_version() == principal_cdrom.CHOICE_NONE and not self._own_lin_iso_path():
            self._browse_lin_own_iso()
            return
        # Cualquier elección (incluida 'Más reciente' o una versión concreta) debe
        # quedar reflejada ya en Almacenamiento: si la VM todavía no existe en
        # disco (una VM nueva), se crea de forma provisional, igual que hace
        # Almacenamiento al añadir el primer dispositivo.
        if self.current_vm_dir or self._ensure_storage_target_vm():
            self._apply_lin_principal_choice()

    def _apply_lin_principal_choice(self, own_iso=""):
        """Crea/actualiza la unidad 'Principal' según lo elegido en Versión ISO.

        Requiere self.current_vm_dir (una VM ya guardada, aunque sea provisional)."""
        if not self.current_vm_dir:
            return
        devices = self._storage_devices_all(self.current_vm_dir)
        changed = principal_cdrom.apply_choice(
            devices, "linux", self._selected_lin_version(),
            profile=self.combo_lin_distro.currentText(), own_iso=own_iso)
        if changed:
            self._write_storage_devices(devices)
            # _ensure_storage_target_vm ya pudo haber colapsado el orden de
            # arranque a solo ["network"] (se refresca antes de crear ningún
            # dispositivo). Se fuerza aquí también, no solo al pulsar Iniciar,
            # para que Almacenamiento ya muestre la Principal primera.
            order = principal_cdrom.boot_first(self._current_boot_order_tokens(), devices)
            self._save_boot_order(order)
            if hasattr(self, "storage_tree"):
                self.refresh_storage_ui()
            self.refresh_boot_order_choices()

    def _populate_config_procesador(self):
        lay = self._config_page_layouts["Procesador"]
        lay.addWidget(self._config_section_title(
            "Procesador",
            "Modelo de CPU y número de núcleos asignados a la máquina virtual.",
        ))

        lay.addWidget(QLabel("<b>Tipo de procesador</b>"))
        self.combo_cpu_model = QComboBox()
        self.combo_cpu_model.addItem("Automático (recomendado)", "auto")
        self.combo_cpu_model.addItem("Host (máximo rendimiento)", "host")
        self.combo_cpu_model.addItem("QEMU x86-64 (compatibilidad)", "qemu64")
        for m in ("Skylake-Client", "Haswell", "Broadwell", "SandyBridge", "Penryn"):
            self.combo_cpu_model.addItem(m, m)
        self.combo_cpu_model.setToolTip(
            "Automático usa el perfil del SO. Host ofrece el máximo rendimiento "
            "pero reduce la portabilidad de la VM."
        )
        self.combo_cpu_model.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        lay.addWidget(self.combo_cpu_model)

        lay.addWidget(QLabel("<b>Núcleos</b>"))
        h = QHBoxLayout()
        self.slider_cores = QSlider(Qt.Orientation.Horizontal)
        max_cores_even = max(2, (int(self.physical_cores) // 2) * 2)
        self.slider_cores.setMinimum(2)
        self.slider_cores.setMaximum(max_cores_even)
        self.slider_cores.setSingleStep(2)
        self.slider_cores.setPageStep(2)
        self.slider_cores.setTickInterval(2)
        self.slider_cores.setTickPosition(QSlider.TickPosition.TicksBelow)
        def_cores = min(max_cores_even, max(2, (max_cores_even // 2) if max_cores_even >= 4 else 2))
        if def_cores % 2:
            def_cores -= 1
        self.slider_cores.setValue(max(2, def_cores))
        self.label_cores_value = QLabel(f"{self.slider_cores.value()} núcleos")
        self.label_cores_value.setStyleSheet("font-weight:bold;")
        self.label_cores_value.setMinimumWidth(90)
        h.addWidget(self.slider_cores, 1)
        h.addWidget(self.label_cores_value)
        lay.addLayout(h)
        self.slider_cores.valueChanged.connect(
            lambda v: (self.label_cores_value.setText(f"{v} núcleos"), self._update_vm_summary())
        )

        hint = QLabel(
            "El número de núcleos se ajusta al par más cercano al valor "
            "elegido, hasta la mitad de los hilos del host."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:11px;")
        lay.addWidget(hint)
        lay.addStretch()

    def _populate_config_memoria(self):
        lay = self._config_page_layouts["Memoria"]
        lay.addWidget(self._config_section_title(
            "Memoria",
            "Cantidad de memoria RAM asignada a la máquina virtual.",
        ))

        lay.addWidget(QLabel("<b>RAM asignada</b>"))
        h = QHBoxLayout()
        self.slider_ram = QSlider(Qt.Orientation.Horizontal)
        max_ram_even = max(2, (int(self.physical_ram_gb) // 2) * 2)
        self.slider_ram.setMinimum(2)
        self.slider_ram.setMaximum(max_ram_even)
        self.slider_ram.setSingleStep(2)
        self.slider_ram.setPageStep(2)
        self.slider_ram.setTickInterval(2)
        self.slider_ram.setTickPosition(QSlider.TickPosition.TicksBelow)
        def_ram = min(max_ram_even, 16 if max_ram_even >= 32 else (8 if max_ram_even >= 16 else 2))
        self.slider_ram.setValue(def_ram)
        self.label_ram_value = QLabel(f"{def_ram} GB")
        self.label_ram_value.setStyleSheet("font-weight:bold;")
        self.label_ram_value.setMinimumWidth(70)
        h.addWidget(self.slider_ram, 1)
        h.addWidget(self.label_ram_value)
        lay.addLayout(h)
        self.slider_ram.valueChanged.connect(
            lambda v: (self.label_ram_value.setText(f"{v} GB"), self._update_vm_summary())
        )

        free_lbl = QLabel(f"RAM del host: {self.mem_total_gb} GB (libre: {self.mem_free_gb} GB)")
        free_lbl.setStyleSheet("color:#888; font-size:11px;")
        lay.addWidget(free_lbl)

        hint = QLabel(
            "Asignar más de la mitad de la RAM del host puede provocar uso "
            "intensivo de swap. La sugerencia es dejar al menos "
            "2 GB para el sistema anfitrión."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:11px;")
        lay.addWidget(hint)
        lay.addStretch()

    def _populate_config_pantalla(self):
        lay = self._config_page_layouts["Pantalla"]
        lay.addWidget(self._config_section_title(
            "Pantalla",
            "Controlador gráfico virtual y memoria de video.",
        ))

        lay.addWidget(QLabel("<b>Gráficos / GPU</b>"))
        self.combo_graphics = QComboBox()
        self.combo_graphics.addItem("Automático (recomendado)", "auto")
        self.combo_graphics.addItem("VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)", "virtio")
        self.combo_graphics.addItem("VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)", "virgl")
        self.combo_graphics.addItem("VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)", "venus")
        self.combo_graphics.addItem("Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)", "qxl")
        self.combo_graphics.addItem("VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)", "vmware")
        self.combo_graphics.addItem("Sin video / Headless", "none")
        self.combo_graphics.setToolTip(
"Automático detecta las capacidades del host y usa aceleración 3D "
            "cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\n"
            "Snapshots:\n"
            "  • VirtIO-GPU 2D → solo snap. de discos.\n"
            "  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n"
            "  • VirGL / Venus → no soportan ningún tipo de snapshot."
        )
        self.combo_graphics.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        self.combo_graphics.currentIndexChanged.connect(self.update_graphics_options)
        lay.addWidget(self.combo_graphics)

        lay.addWidget(QLabel("<b>Memoria de video (VRAM)</b>"))
        self.combo_graphics_vram = QComboBox()
        for v in ("128M", "256M", "512M", "1G", "2G", "4G"):
            self.combo_graphics_vram.addItem(v, v)
        self.combo_graphics_vram.setCurrentIndex(1)
        self.combo_graphics_vram.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        lay.addWidget(self.combo_graphics_vram)

        self.label_graphics_host = QLabel("Host GPU: detectando…")
        self.label_graphics_host.setStyleSheet("font-size:11px; color:#888;")
        self.label_graphics_host.setWordWrap(True)
        lay.addWidget(self.label_graphics_host)

        self.label_graphics_compat = QLabel("")
        self.label_graphics_compat.setStyleSheet("font-size:11px; color:#b36b00; font-weight:bold;")
        self.label_graphics_compat.setWordWrap(True)
        self.label_graphics_compat.setVisible(False)
        lay.addWidget(self.label_graphics_compat)

        self.check_vnc_embedded = QCheckBox("🖼️ Mostrar la VM dentro de la app (consola VNC embebida)")
        # Sustituido por los combos de protocolo/modo; se conserva el
        # objeto por compatibilidad con código antiguo pero no se muestra.
        self.check_vnc_embedded.setVisible(False)
        self.check_vnc_embedded.setToolTip(
            "Cuando está activo, la VM se muestra dentro de la app.\n"
            "Fuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\n"
            "Si lo desactivas, la VM se abre en una ventana externa y puedes\n"
            "elegir modos con aceleración 3D (VirGL, Venus)."
        )
        self.check_vnc_embedded.setChecked(True)
        self.check_vnc_embedded.stateChanged.connect(self._on_vnc_embedded_changed)
        lay.addWidget(self.check_vnc_embedded)

        # Disparar detección inicial de gráficos.
        self.combo_main_os.currentIndexChanged.connect(self.update_graphics_options)
        self.combo_graphics.currentIndexChanged.connect(lambda *_: self._update_graphics_compat_hint())
        self.combo_firmware.currentIndexChanged.connect(lambda *_: self._update_graphics_compat_hint())
        # ------------------------------------------------------------------
        # Consola remota (VNC / SPICE). Cómo se expone la pantalla de la
        # VM: dentro de la app, en un visor externo, o en la ventana
        # nativa de QEMU.
        # ------------------------------------------------------------------
        console_group = QGroupBox("Consola remota")
        console_form = QFormLayout(console_group)

        self.combo_console_protocol = QComboBox()
        self.combo_console_protocol.addItem("VNC (compatible con cualquier gráfico)", PROTOCOL_VNC)
        self.combo_console_protocol.addItem("SPICE (mejor rendimiento en local)", PROTOCOL_SPICE)
        self.combo_console_protocol.setToolTip(
            "VNC: cliente ligero, funciona con cualquier dispositivo de video.\n"
            "SPICE: mejor rendimiento en local, requiere un visor spice-gtk.\n"
            "Con cualquiera de los dos, QEMU no abre ventana local: solo el socket."
        )
        console_form.addRow("Protocolo:", self.combo_console_protocol)

        self.combo_console_mode = QComboBox()
        self.combo_console_mode.addItem("Embebida en la app", MODE_EMBEDDED)
        self.combo_console_mode.addItem("Ventana externa (visor del sistema)", MODE_EXTERNAL)
        self.combo_console_mode.addItem("Ventana nativa de QEMU", MODE_NATIVE)
        self.combo_console_mode.addItem(
            "Híbrida (VNC embebido + SPICE externo)", MODE_HYBRID
        )
        self.combo_console_mode.setToolTip(
            "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\n"
            "Ventana externa: se lanza el visor del sistema (vncviewer / spicy).\n"
            "Nativa QEMU: QEMU abre su propia ventana (comportamiento clásico)."
        )
        console_form.addRow("Modo:", self.combo_console_mode)

        self.label_console_requirements = QLabel("")
        self.label_console_requirements.setWordWrap(True)
        self.label_console_requirements.setStyleSheet("color:#888; font-size:11px;")
        console_form.addRow("", self.label_console_requirements)
        # ------------------------------------------------------------------
        # Bloque de ayuda: explica las limitaciones reales de cada modo.
        # Se actualiza dinámicamente para que cada usuario vea lo que aplica
        # a su sesión (Wayland vs X11) sin ambigüedad.
        # ------------------------------------------------------------------
        self.label_console_help = QLabel("")
        self.label_console_help.setWordWrap(True)
        self.label_console_help.setStyleSheet(
            "color:#666; font-size:11px; background: palette(alternate-base);"
            " border: 1px solid palette(mid); border-radius: 6px;"
            " padding: 8px; line-height: 1.4;"
        )
        self.label_console_help.setTextFormat(Qt.TextFormat.RichText)
        self.label_console_help.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        console_form.addRow("", self.label_console_help)

        # Rellenar la ayuda según la sesión actual.
        try:
            self._refresh_console_help()
        except Exception:
            pass
        try:
            self._refresh_console_status_banner()
        except Exception:
            pass
        try:
            self._refresh_console_combo_tooltips()
        except Exception:
            pass
        try:
            self._refresh_console_status_banner()
        except Exception:
            pass

        self.combo_console_protocol.currentIndexChanged.connect(self._on_console_config_changed)
        self.combo_console_mode.currentIndexChanged.connect(self._on_console_config_changed)

        lay.addWidget(console_group)

        # Inicializar la pista de requisitos según la elección actual.
        try:
            _proto0, _mode0 = self._current_console_choice()
            self.label_console_requirements.setText(describe_requirements(_proto0, _mode0))
        except Exception:
            pass

        self.update_graphics_options()
        self._update_graphics_compat_hint()
        lay.addStretch()

    def _populate_config_red(self):
        lay = self._config_page_layouts["Red"]
        lay.addWidget(self._config_section_title(
            "Red",
            "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.",
        ))

        group = QGroupBox("Adaptadores")
        gl = QVBoxLayout(group)
        self.network_devices_list = QListWidget()
        self.network_devices_list.setMinimumHeight(110)
        gl.addWidget(self.network_devices_list)
        row = QHBoxLayout()
        self.btn_network_add = QPushButton("➕ Agregar adaptador")
        self.btn_network_edit = QPushButton("✏ Editar")
        self.btn_network_remove = QPushButton("🗑 Eliminar")
        self.btn_network_add.clicked.connect(self.add_network_device)
        self.btn_network_edit.clicked.connect(self.edit_network_device)
        self.btn_network_remove.clicked.connect(self.remove_network_device)
        for b in (self.btn_network_add, self.btn_network_edit, self.btn_network_remove):
            row.addWidget(b)
        row.addStretch()
        gl.addLayout(row)
        lay.addWidget(group)

        self.check_no_network = QCheckBox("Sin red (ningún adaptador virtual)")
        self.check_no_network.toggled.connect(lambda checked: (
            self.network_devices_list.setEnabled(not checked),
            self.btn_network_add.setEnabled(not checked),
            self.btn_network_edit.setEnabled(not checked),
            self.btn_network_remove.setEnabled(not checked),
            self._update_vm_summary(),
            self._save_hardware_lists() if self.current_vm_dir else None,
        ))
        lay.addWidget(self.check_no_network)

        # Controles legacy ocultos (combo_network_*, label_network_target): se
        # mantienen para cargar configs antiguas, pero no se muestran.
        self.combo_network_mode = QComboBox()
        self.combo_network_mode.addItem("NAT / Internet (recomendado)", "nat")
        self.combo_network_mode.addItem("Bridge existente", "bridge")
        self.combo_network_mode.addItem("TAP", "tap")
        self.combo_network = QComboBox()
        self.combo_network.addItem("VirtIO (recomendado)", "virtio-net-pci")
        self.combo_network.addItem("Intel E1000", "e1000")
        self.combo_network.addItem("Realtek RTL8139", "rtl8139")
        self.combo_network.addItem("VMware VMXNET3", "vmxnet3")
        self.combo_network_count = QComboBox()
        for n in range(1, 5):
            self.combo_network_count.addItem(str(n), n)
        self.label_network_target = QLabel("Interfaz/Bridge:")
        self.combo_network_interface = QComboBox()
        for _w in (self.combo_network_mode, self.combo_network, self.combo_network_count,
                   self.label_network_target, self.combo_network_interface):
            _w.setVisible(False)
        self.combo_network_mode.currentIndexChanged.connect(self.update_network_options)
        self.combo_network_mode.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        self.combo_network.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        self.combo_network_count.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        self.update_network_options()
        self.refresh_network_devices_ui([])
        lay.addStretch()

    def _populate_config_dispositivos(self):
        lay = self._config_page_layouts["Dispositivos"]
        lay.addWidget(self._config_section_title(
            "Dispositivos",
            "Audio y otros dispositivos integrados de la máquina virtual.",
        ))

        lay.addWidget(QLabel("<b>Audio</b>"))
        self.combo_audio = QComboBox()
        self.combo_audio.addItem("Intel HDA (recomendado)", "intel-hda")
        self.combo_audio.addItem("AC97", "ac97")
        self.combo_audio.addItem("Sound Blaster 16", "sb16")
        self.combo_audio.addItem("Sin sonido", "none")
        self.combo_audio.currentIndexChanged.connect(lambda *_: self._update_vm_summary())
        lay.addWidget(self.combo_audio)

        note = QLabel(
            "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña "
            "<b>Dispositivos</b> de la parte superior de la ventana."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#888; font-size:11px; padding-top:8px;")
        lay.addWidget(note)
        lay.addStretch()

    def _populate_config_otros(self):
        lay = self._config_page_layouts["Virtualización"]
        lay.addWidget(self._config_section_title(
            "Virtualización",
            "Diagnóstico del sistema de virtualización y opciones misceláneas.",
        ))

        # Panel de estado de dependencias (antes era un QGroupBox invisible en
        # main_layout). Ahora vive aquí y se hace visible por defecto.
        deps_group = QGroupBox("Estado del sistema de virtualización")
        deps_layout = QVBoxLayout(deps_group)

        self.label_host_distro = QLabel("Distribución: comprobando...")
        self.label_host_manager = QLabel("Gestor de paquetes: comprobando...")
        deps_layout.addWidget(self.label_host_distro)
        deps_layout.addWidget(self.label_host_manager)

        # Grid de 3 columnas con wrap: en ventanas estrechas las
        # etiquetas se reparten en varias líneas en vez de solaparse.
        self.status_qemu = QLabel()
        self.status_kvm = QLabel()
        self.status_ovmf = QLabel()
        self.status_swtpm = QLabel()
        self.status_secure = QLabel()
        self.status_virtio = QLabel()
        self.status_audio = QLabel()
        status_grid = QGridLayout()
        status_grid.setHorizontalSpacing(18)
        status_grid.setVerticalSpacing(6)
        for i, lbl in enumerate((self.status_qemu, self.status_kvm, self.status_ovmf,
                                 self.status_swtpm, self.status_secure,
                                 self.status_virtio, self.status_audio)):
            lbl.setMinimumWidth(0)
            lbl.setWordWrap(True)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            status_grid.addWidget(lbl, i // 3, i % 3)
        deps_layout.addLayout(status_grid)

        deps_buttons = QHBoxLayout()
        self.btn_check_deps = QPushButton("🔄 Comprobar dependencias")
        self.btn_repair_deps = QPushButton("🛠️ Comprobar/Reparar dependencias")
        self.btn_check_deps.clicked.connect(self.refresh_dependency_status)
        self.btn_repair_deps.clicked.connect(self.repair_dependency_status)
        deps_buttons.addWidget(self.btn_check_deps)
        deps_buttons.addWidget(self.btn_repair_deps)
        deps_buttons.addStretch()
        deps_layout.addLayout(deps_buttons)
        lay.addWidget(deps_group)
        lay.addStretch()

    def _build_storage_group(self, main_layout):
        """Bloque de almacenamiento. Vive DENTRO de la sección
        "Almacenamiento" de Configuración, con dos subsecciones apiladas:
          1. Controladores y dispositivos (arriba, ancho completo).
          2. Orden de arranque (abajo, ancho completo).
        """
        # --- Contenedor principal del bloque ---
        storage_group = QGroupBox("Almacenamiento")
        storage_layout = QVBoxLayout(storage_group)
        storage_layout.setSpacing(12)
        storage_layout.setContentsMargins(12, 12, 12, 12)

        # --- 1) Controladores y dispositivos ---
        ctrl_group = QGroupBox("Controladores y dispositivos")
        ctrl_layout = QVBoxLayout(ctrl_group)
        self.storage_tree = QTreeWidget()
        self.storage_tree.setHeaderLabels(["Dispositivo", "Tipo / archivo"])
        self.storage_tree.setColumnWidth(0, 360)
        self.storage_tree.setMinimumHeight(180)
        self.storage_tree.setAlternatingRowColors(True)
        self.storage_tree.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Preferred)
        ctrl_layout.addWidget(self.storage_tree)

        add_row = QHBoxLayout()
        # UI simplificada: el "Disco Duro" se registra internamente
        # como sata y workers.py decide el bus real (NVMe/AHCI/IDE)
        # según el sistema operativo invitado.
        for label, devtype in (("📀 CD / DVD", "cdrom"),
                               ("💽 Disco Duro", "sata"),
                               ("💾 Disquete", "floppy")):
            b = QPushButton(label)
            b.setMinimumHeight(30)
            b.clicked.connect(lambda _, t=devtype: self.create_storage_device(t))
            add_row.addWidget(b)
        self.btn_storage_modify_device = QPushButton("✏ Modificar")
        self.btn_storage_modify_device.setMinimumHeight(30)
        self.btn_storage_modify_device.clicked.connect(self.modify_storage_device)
        add_row.addWidget(self.btn_storage_modify_device)
        self.btn_storage_delete_device = QPushButton("🗑 Eliminar")
        self.btn_storage_delete_device.setMinimumHeight(30)
        self.btn_storage_delete_device.clicked.connect(self.delete_storage_device)
        add_row.addWidget(self.btn_storage_delete_device)
        add_row.addStretch()
        ctrl_layout.addLayout(add_row)
        storage_layout.addWidget(ctrl_group)

        # --- 2) Orden de arranque ---
        boot_group = QGroupBox("Orden de arranque")
        boot_layout = QVBoxLayout(boot_group)
        self.storage_list = QListWidget()
        self.storage_list.setMinimumHeight(110)
        self.storage_list.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Preferred)
        self.storage_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.storage_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.storage_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.storage_list.model().rowsMoved.connect(
            lambda *args: self._boot_order_from_list()
        )
        boot_layout.addWidget(self.storage_list)

        boot_row = QHBoxLayout()
        self.btn_storage_up = QPushButton("⬆ Subir")
        self.btn_storage_down = QPushButton("⬇ Bajar")
        self.btn_storage_remove = QPushButton("🗑 Quitar")
        self.btn_storage_up.clicked.connect(lambda: self.move_storage_boot(-1))
        self.btn_storage_down.clicked.connect(lambda: self.move_storage_boot(1))
        self.btn_storage_remove.clicked.connect(self.remove_storage_device)
        for b in (self.btn_storage_up, self.btn_storage_down, self.btn_storage_remove):
            boot_row.addWidget(b)
        boot_row.addStretch()
        boot_layout.addLayout(boot_row)
        storage_layout.addWidget(boot_group)

        # --- 3) Añadir a la sección "Almacenamiento" de Configuración ---
        target_layout = None
        try:
            target_layout = self._config_page_layouts.get("Almacenamiento")
        except Exception:
            target_layout = None

        if target_layout is None:
            # Sin rediseño: añadir al layout principal como antes.
            main_layout.addWidget(storage_group)
        else:
            # Con rediseño: título de sección + bloque, dentro de su página.
            if not getattr(self, "_storage_section_title_added", False):
                target_layout.addWidget(self._config_section_title(
                    "Almacenamiento",
                    "Discos, unidades ópticas y orden de arranque de la máquina virtual.",
                ))
                self._storage_section_title_added = True
            target_layout.addWidget(storage_group)
            target_layout.addStretch()


    def _build_deps_group(self, main_layout):
        """Ya no se usa: el panel de dependencias vive ahora en la sección
        'Otros' de la pestaña Configuración (creado por _populate_config_otros).
        Se deja el método como no-op para conservar compatibilidad con
        cualquier llamada existente."""
        pass


    def _build_main_container(self, main_layout):
        """Panel izquierdo (lista de VMs) + centro (tabs) + derecho (recursos).
        Al final monta el QWidget contenedor y lo pone como central."""
        # Centro de control estilo VirtualBox: lista única a la izquierda + área principal.
        left_panel = QWidget()
        # Solo un mínimo: el QSplitter decide el máximo real.
        left_panel.setMinimumWidth(160)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)

        left_title = QLabel("<b>MÁQUINAS VIRTUALES</b>")
        left_title.setStyleSheet("font-size: 11px; padding: 4px 2px;")
        left_layout.addWidget(left_title)

        # Buscador de VMs (antes vivía en el toolbar de Configuración
        # y solo se veía en esa pestaña). Ahora siempre visible.
        self.input_vm_search = QLineEdit()
        self.input_vm_search.setPlaceholderText("🔍 Buscar máquinas...")
        self.input_vm_search.setMinimumWidth(0)
        self.input_vm_search.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.input_vm_search.textChanged.connect(self._filter_vm_list)
        left_layout.addWidget(self.input_vm_search)

        # Fila de acciones: [➕ Nueva VM] [🔌 USB]
        new_row = QHBoxLayout()
        new_row.setSpacing(4)
        self.btn_new_vm = QPushButton("➕ Nueva VM")
        self.btn_new_vm.setMinimumHeight(36)
        self.btn_new_vm.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.btn_new_vm.clicked.connect(self.new_vm)
        new_row.addWidget(self.btn_new_vm, 1)

        # Botón USB compacto: abre el menú de USB conectados al host.
        # Está aquí (no en la fila Iniciar/Pausar/Apagar) porque esa
        # fila es demasiado estrecha para cuatro botones.
        self.btn_vm_usb = QToolButton()
        self.btn_vm_usb.setText("💿")
        self.btn_vm_usb.setToolTip(
            "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
            "Cambia ISO en caliente, expulsa medios y conecta/desconecta\n"
            "USB sin reiniciar la máquina. Atajo: Ctrl+M."
        )
        self.btn_vm_usb.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_vm_usb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.btn_vm_usb.setMinimumHeight(36)
        self.btn_vm_usb.setMaximumWidth(52)
        self.btn_vm_usb.setStyleSheet(
            "QToolButton { background-color: #1976d2; color: white; "
            "font-weight: bold; border: 1px solid #0d47a1; "
            "border-radius: 6px; padding: 4px 6px; }"
            "QToolButton:hover { background-color: #0d47a1; }"
            "QToolButton:disabled { background-color: #bdbdbd; color: #eeeeee; }"
        )
        self.menu_vm_usb = QMenu(self.btn_vm_usb)
        self.menu_vm_usb.aboutToShow.connect(self._refresh_media_menu)
        self.btn_vm_usb.setMenu(self.menu_vm_usb)
        new_row.addWidget(self.btn_vm_usb)

        left_layout.addLayout(new_row)

        self.vm_list = QListWidget()
        self.vm_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.vm_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.vm_list.setMinimumHeight(120)
        self.vm_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.vm_list.setToolTip("Selecciona una máquina virtual")
        self.vm_list.setStyleSheet(
            "QListWidget { border: 1px solid #c9c9c9; border-radius: 5px; padding: 2px; }"
            "QListWidget::item { padding: 8px 6px; }"
            "QListWidget::item:selected { background: #dbeafe; color: #111; }"
        )
        # Tamaño de los iconos del SO (Ubuntu, Windows, macOS…) que
        # se muestran a la izquierda de cada VM en la lista.
        self.vm_list.setIconSize(QSize(28, 28))
        self.vm_list.currentTextChanged.connect(self.on_vm_list_changed)
        # itemClicked dispara incluso si el usuario pulsa sobre la VM
        # ya seleccionada. Sirve para re-elevar el visor externo o
        # volver a la consola cuando el usuario se había movido a
        # otra pestaña.
        self.vm_list.itemClicked.connect(self.on_vm_list_item_clicked)
        left_layout.addWidget(self.vm_list, 1)

        self.vm_control_status = QLabel("● Sin VM seleccionada")
        self.vm_control_status.setStyleSheet("font-weight:bold; color:#757575; padding:4px;")
        left_layout.addWidget(self.vm_control_status)


        control_row = QHBoxLayout()
        self.btn_vm_start = QPushButton("▶ Iniciar")
        self.btn_vm_pause = QToolButton()
        self.btn_vm_pause.setText("⏸ Pausar")
        self.btn_vm_pause.setToolTip(
            "Pausar la VM. Usa la flecha para más opciones:\n"
            "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
            "• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n"
            "• Reanudar: vuelve a ejecutar la VM pausada."
        )
        self.btn_vm_pause.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_vm_pause.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        # "Apagar" es un QToolButton con menú desplegable en vez de un botón
        # simple: agrupa Apagado/Forzar Apagado/Reiniciar/Forzar Reinicio,
        # igual que el botón de cierre de VirtualBox. Clic normal = Apagado
        # (ACPI, la opción más segura); el menú da acceso a las demás.
        self.btn_vm_poweroff = QToolButton()
        self.btn_vm_poweroff.setText("⏹ Apagar")
        self.btn_vm_poweroff.setToolTip("Apagado (ACPI): pide a la VM que se apague de forma ordenada.")
        self.btn_vm_poweroff.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_vm_poweroff.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self.menu_vm_poweroff = QMenu(self.btn_vm_poweroff)
        self.action_vm_shutdown = QAction("⏹ Apagado (ACPI)", self)
        self.action_vm_shutdown.setToolTip(
            "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\n"
            "encendido en un equipo real. El sistema operativo invitado decide cuándo\n"
            "y cómo cerrar. Puede tardar unos segundos o no responder si está colgado."
        )
        self.action_vm_force_shutdown = QAction("⏻ Forzar apagado", self)
        self.action_vm_force_shutdown.setToolTip(
            "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\n"
            "como desenchufar un equipo real. Puede causar pérdida de datos no\n"
            "guardados; úsalo solo si la VM no responde al apagado normal."
        )
        self.action_vm_reboot = QAction("⟳ Reiniciar", self)
        self.action_vm_reboot.setToolTip(
            "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\n"
            "No es un apagado ordenado del sistema operativo invitado: simplemente\n"
            "reinicia el hardware virtual."
        )
        self.action_vm_force_reboot = QAction("⟲ Forzar reinicio", self)
        self.action_vm_force_reboot.setToolTip(
            "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\n"
            "al sistema operativo invitado. Úsalo solo si la VM no responde ni al\n"
            "apagado ni al reinicio normales."
        )
        for action in (
            self.action_vm_shutdown,
            self.action_vm_force_shutdown,
            self.action_vm_reboot,
            self.action_vm_force_reboot,
        ):
            self.menu_vm_poweroff.addAction(action)
        self.btn_vm_poweroff.setMenu(self.menu_vm_poweroff)

        # Menú del botón Pausar (mismo patrón que Detener): clic directo
        # ejecuta la acción contextual (pausar si corre, reanudar si pausada);
        # la flecha despliega las alternativas.
        #
        # Orden del menú Pausa: Pausar → Reanudar → Snapshot
        #   - Pausar (rápido): acción más frecuente, va primero.
        #   - Reanudar: alternativa contextual, va segundo.
        #   - Tomar Snapshot: opción menos frecuente, va tercero.
        self.menu_vm_pause = QMenu(self.btn_vm_pause)
        self.action_vm_pause = QAction("⏸ Pausar (rápido)", self)
        self.action_vm_pause.setToolTip(
            "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\n"
            "el estado (RAM y dispositivos) se pierde si el host se reinicia."
        )
        self.action_vm_resume = QAction("▶ Reanudar", self)
        self.action_vm_resume.setToolTip(
            "Reanuda la ejecución de la VM pausada."
        )
        self.action_vm_pause_save = QAction("📸 Tomar Snapshot", self)
        self.action_vm_pause_save.setToolTip(
            "Guarda la RAM y el estado de los dispositivos a disco (como un\n"
            "snapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\n"
            "El snapshot aparecerá en la pestaña Snapshots y su captura de\n"
            "pantalla en el panel 'Último snapshot'."
        )
        # Orden de inserción: Pausar → Reanudar → Tomar Snapshot.
        for _a in (self.action_vm_pause, self.action_vm_resume, self.action_vm_pause_save):
            self.menu_vm_pause.addAction(_a)
        self.btn_vm_pause.setMenu(self.menu_vm_pause)

        for b, tip, color, hover in (
            (self.btn_vm_start, "Iniciar VM", "#2e7d32", "#1b5e20"),
            (self.btn_vm_pause, "Pausar/Reanudar VM", "#f9a825", "#f57f17"),
            (self.btn_vm_poweroff, "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\nUsa la flecha para más opciones (forzar, reiniciar).", "#c62828", "#8e0000"),
        ):
            # Todos los botones deben tener EXACTAMENTE la misma política de
            # tamaño para que crezcan/decrezcan juntos al redimensionar el
            # panel izquierdo. QPushButton y QToolButton no comparten
            # defaults, así que lo forzamos aquí.
            b.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            b.setMinimumHeight(36)
            b.setMinimumWidth(48)
            b.setToolTip(tip)
            b.setStyleSheet(
                f"QToolButton, QPushButton {{ background-color: {color}; color: white; font-weight: bold; "
                f"border: 1px solid {hover}; border-radius: 6px; padding: 5px 8px; }}"
                f"QToolButton:hover, QPushButton:hover {{ background-color: {hover}; }}"
                "QToolButton:disabled, QPushButton:disabled { background-color: #bdbdbd; color: #eeeeee; }"
            )
            # Stretch 1 en cada botón: reparto equitativo del ancho
            # disponible. Sin esto, Qt usa el "preferred width" de cada
            # texto y solo el más ancho se estira.
            control_row.addWidget(b, 1)
        left_layout.addLayout(control_row)
        self.btn_vm_start.clicked.connect(self.control_start_vm)
        self.btn_vm_pause.clicked.connect(self.control_pause_vm)
        self.action_vm_pause.triggered.connect(self.control_pause_vm_simple)
        self.action_vm_pause_save.triggered.connect(self.control_pause_vm_with_snapshot)
        self.action_vm_resume.triggered.connect(self.control_resume_vm)
        # Clic directo en el botón (no en la flecha) = apagado normal, el
        # comportamiento que ya existía antes de agregar el menú.
        self.btn_vm_poweroff.clicked.connect(self.control_poweroff_vm)
        self.action_vm_shutdown.triggered.connect(self.control_poweroff_vm)
        self.action_vm_force_shutdown.triggered.connect(self.control_force_poweroff_vm)
        self.action_vm_reboot.triggered.connect(self.control_reboot_vm)
        self.action_vm_force_reboot.triggered.connect(self.control_force_reboot_vm)

        left_hint = QLabel("Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.")
        left_hint.setWordWrap(True)
        left_hint.setStyleSheet("color:#666; font-size:9px; padding:4px 2px;")
        left_layout.addWidget(left_hint)

        # Área de trabajo derecha.
        details_page = QWidget()
        details_layout = QVBoxLayout(details_page)
        details_layout.setContentsMargins(12, 10, 12, 10)
        details_layout.setSpacing(8)

        self.manager_vm_title = QLabel("Nueva máquina virtual")
        self.manager_vm_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        details_layout.addWidget(self.manager_vm_title)

        self.manager_vm_state = QLabel("● Nueva VM")
        self.manager_vm_state.setStyleSheet("font-weight:bold; color:#757575;")
        details_layout.addWidget(self.manager_vm_state)

        # Acciones secundarias. Los controles de Iniciar/Pausar/Apagar están únicamente
        # debajo de la lista de VMs, tal como solicitaste.
        # Fila de acciones de Resumen: Clonar · Importar · Exportar · Eliminar.
        # Son las operaciones "de VM" más habituales; las menos frecuentes
        # (Crear) viven en la lista lateral izquierda.
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        for attr, text, slot, tip in (
            ("manager_btn_clone", "🧬 Clonar",
             self.clone_current_vm,
             "Crea una copia completa de esta VM en una carpeta nueva."),
            ("manager_btn_import", "⇪ Importar",
             self.import_vm,
             "Importar una VM desde una carpeta (con vm_config.ini) o desde\n"
             "un archivo .tar.gz / .zip exportado previamente."),
            ("manager_btn_export", "⇩ Exportar",
             self.export_vm,
             "Exportar esta VM como carpeta, .tar.gz o .zip portable.\n"
             "Se omiten los archivos de runtime (pids, sockets, logs)."),
            ("manager_btn_delete", "🗑️ Eliminar",
             self.delete_current_vm,
             "Elimina esta VM (con opción de conservar los discos)."),
        ):
            b = QPushButton(text)
            b.setMinimumHeight(34)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            setattr(self, attr, b)
            toolbar.addWidget(b)
        toolbar.addStretch()
        details_layout.addLayout(toolbar)

        # Tarjeta con la configuración textual de la VM.
        info_box = QGroupBox("Resumen de Configuración")
        info_layout = QVBoxLayout(info_box)
        self.manager_details_label = QLabel()
        self.manager_details_label.setWordWrap(True)
        self.manager_details_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.manager_details_label.setStyleSheet(
            "background: palette(alternate-base); border:1px solid palette(mid); border-radius:6px; padding:12px; font-size:11px;"
        )
        info_layout.addWidget(self.manager_details_label)
        info_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        details_scroll_content = QWidget()
        details_scroll_layout = QVBoxLayout(details_scroll_content)
        details_scroll_layout.setContentsMargins(0, 0, 6, 0)
        details_scroll_layout.addStretch(1)
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        details_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        details_scroll.setWidget(details_scroll_content)
        details_layout.addWidget(details_scroll, 1)
        self._perf_cpu_hist = []
        self._perf_ram_hist = []
        self._perf_disk_hist = []
        self._perf_net_hist = []
        self._perf_prev_net = None
        self._perf_prev_io = None
        self._perf_prev_time = None

        self.manager_quick_hint = QLabel("Selecciona una máquina virtual en la lista de la izquierda.")
        self.manager_quick_hint.setStyleSheet("color:#666; padding:4px;")
        details_layout.addWidget(self.manager_quick_hint)
        details_layout.addStretch()

        # La configuración completa vive en una pestaña separada; así la pantalla
        # principal queda limpia, como en VirtualBox.
        # Administración de snapshots en una pestaña propia, estilo VirtualBox.
        snapshots_page = QWidget()
        snap_layout = QVBoxLayout(snapshots_page)
        snap_layout.setContentsMargins(10, 10, 10, 10)
        snap_title = QLabel("<b>Snapshots de la máquina virtual</b>")
        snap_layout.addWidget(snap_title)
        snap_info = QLabel("Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.")
        snap_info.setWordWrap(True)
        snap_info.setStyleSheet("color:#555; padding-bottom:4px;")
        snap_layout.addWidget(snap_info)

        # Fila de acciones (arriba de la lista de discos).
        snap_buttons = QHBoxLayout()
        self.btn_snapshot_refresh = QPushButton("🔄 Actualizar")
        self.btn_snapshot_create = QPushButton("➕ Crear")
        self.btn_snapshot_restore = QPushButton("↩ Restaurar")
        self.btn_snapshot_rename = QPushButton("✏ Cambiar nombre")
        self.btn_snapshot_delete = QPushButton("🗑 Eliminar")
        for b, slot in ((self.btn_snapshot_refresh, self.refresh_snapshot_page), (self.btn_snapshot_create, self.create_snapshot_from_page), (self.btn_snapshot_restore, self.restore_snapshot_from_page), (self.btn_snapshot_rename, self.rename_snapshot_from_page), (self.btn_snapshot_delete, self.delete_snapshot_from_page)):
            b.clicked.connect(slot); snap_buttons.addWidget(b)
        snap_buttons.addStretch(1)
        snap_layout.addLayout(snap_buttons)

        self.snapshot_disk_status = QTreeWidget()
        self.snapshot_disk_status.setHeaderLabels(["Dispositivo", "Formato", "Tamaño virtual", "Tamaño archivo", "Libre host", "Escritura", "Snapshot"])
        self.snapshot_disk_status.setRootIsDecorated(False)
        self.snapshot_disk_status.setAlternatingRowColors(True)
        self.snapshot_disk_status.setMaximumHeight(95)
        self.snapshot_disk_status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        snap_layout.addWidget(self.snapshot_disk_status)

        self.snapshot_space_label = QLabel("")
        self.snapshot_space_label.setWordWrap(True)
        self.snapshot_space_label.setStyleSheet("padding:4px;")
        snap_layout.addWidget(self.snapshot_space_label)

        self.snapshot_progress_label = QLabel("Sin operación de snapshot")
        self.snapshot_progress_label.setStyleSheet("padding:2px; font-weight:bold;")
        # Barra inline deshabilitada: el diálogo de progreso del
        # snapshot la sustituye. Se conserva el widget oculto por
        # compatibilidad con código que todavía lo referencia.
        self.snapshot_progress_label.setVisible(False)
        self.snapshot_progress_bar = QProgressBar()
        self.snapshot_progress_bar.setRange(0, 100)
        self.snapshot_progress_bar.setValue(0)
        self.snapshot_progress_bar.setTextVisible(True)
        self.snapshot_progress_bar.setVisible(False)

        self.snapshot_list_widget = QTreeWidget()
        self.snapshot_list_widget.setHeaderLabels(["ID", "Nombre", "Tamaño VM", "Fecha", "Reloj VM"])
        self.snapshot_list_widget.setRootIsDecorated(False)
        self.snapshot_list_widget.setAlternatingRowColors(True)
        self.snapshot_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.snapshot_list_widget.itemSelectionChanged.connect(self._update_snapshot_preview)

        # Selector de vista: radio buttons (uno siempre activo).
        toggle_row = QHBoxLayout()
        toggle_row.addWidget(QLabel("Vista:"))
        self.radio_snap_view_list = QRadioButton("📋 Lista")
        self.radio_snap_view_list.setChecked(True)
        self.radio_snap_view_graph = QRadioButton("🌳 Organigrama")
        self.snap_view_group = QButtonGroup(self)
        self.snap_view_group.addButton(self.radio_snap_view_list, 0)
        self.snap_view_group.addButton(self.radio_snap_view_graph, 1)
        self.snap_view_group.idClicked.connect(self._on_snap_view_toggled)
        toggle_row.addWidget(self.radio_snap_view_list)
        toggle_row.addWidget(self.radio_snap_view_graph)
        toggle_row.addStretch()
        snap_layout.addLayout(toggle_row)

        # Stack con las dos vistas.
        self.snap_view_stack = QStackedWidget()
        self.snap_view_stack.addWidget(self.snapshot_list_widget)
        self.snapshot_graph_view = SnapshotsGraphView()
        self.snapshot_graph_view.setMinimumHeight(260)
        self.snap_view_stack.addWidget(self.snapshot_graph_view)
        self.snap_view_stack.setCurrentIndex(0)
        snap_layout.addWidget(self.snap_view_stack, 1)
        # Contenedor del preview con zoom + scroll.
        self.snapshot_preview_container = QWidget()
        preview_layout = QVBoxLayout(self.snapshot_preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)

        preview_zoom_row = QHBoxLayout()
        preview_zoom_row.addWidget(QLabel("Zoom:"))
        self.btn_preview_zoom_out = QPushButton("🔍−")
        self.btn_preview_zoom_out.setMaximumWidth(44)
        self.btn_preview_zoom_out.setToolTip("Alejar la miniatura")
        self.btn_preview_zoom_in = QPushButton("🔍+")
        self.btn_preview_zoom_in.setMaximumWidth(44)
        self.btn_preview_zoom_in.setToolTip("Acercar la miniatura")
        self.btn_preview_zoom_reset = QPushButton("↺ Ajustar")
        self.btn_preview_zoom_reset.setMaximumWidth(90)
        self.btn_preview_zoom_reset.setToolTip("Ajustar al tamaño original")
        self.snapshot_preview_zoom_label = QLabel("100%")
        self.snapshot_preview_zoom_label.setMinimumWidth(50)
        self.snapshot_preview_zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._snapshot_preview_zoom = 1.0
        self.btn_preview_zoom_in.clicked.connect(lambda: self._change_preview_zoom(1.25))
        self.btn_preview_zoom_out.clicked.connect(lambda: self._change_preview_zoom(0.8))
        self.btn_preview_zoom_reset.clicked.connect(self._reset_preview_zoom)
        preview_zoom_row.addWidget(self.btn_preview_zoom_out)
        preview_zoom_row.addWidget(self.btn_preview_zoom_in)
        preview_zoom_row.addWidget(self.btn_preview_zoom_reset)
        preview_zoom_row.addStretch()
        preview_zoom_row.addWidget(self.snapshot_preview_zoom_label)
        preview_layout.addLayout(preview_zoom_row)

        self.snapshot_preview_scroll = QScrollArea()
        self.snapshot_preview_scroll.setWidgetResizable(False)
        self.snapshot_preview_scroll.setFrameShape(QScrollArea.Shape.StyledPanel)
        self.snapshot_preview_scroll.setMinimumHeight(180)
        self.snapshot_preview_scroll.setMaximumHeight(220)
        self.snapshot_preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.snapshot_preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.snapshot_preview_label = QLabel("Sin captura de pantalla")
        self.snapshot_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.snapshot_preview_label.setMinimumSize(320, 180)
        self.snapshot_preview_label.setStyleSheet("background: #1e1e1e; color: #888; padding: 4px;")
        self.snapshot_preview_scroll.setWidget(self.snapshot_preview_label)
        preview_layout.addWidget(self.snapshot_preview_scroll)
        snap_layout.addWidget(self.snapshot_preview_container)
        snap_scroll = QScrollArea()
        snap_scroll.setWidgetResizable(True)
        snap_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        snap_scroll.setWidget(snapshots_page)

        # Integración Host ↔ Guest: Compartir (carpetas + clipboard).
        shared_page=QWidget(); shared_outer_layout=QVBoxLayout(shared_page)
        shared_info=QLabel("Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).")
        shared_info.setWordWrap(True); shared_info.setStyleSheet("color:#555; padding:6px;"); shared_outer_layout.addWidget(shared_info)

        self.shared_subtabs = QTabWidget()
        self.shared_subtabs.setDocumentMode(True)

        # --- Subpestaña: Compartir Carpetas ---
        shared_folders_page=QWidget(); sf_layout=QVBoxLayout(shared_folders_page)
        sf_info=QLabel("Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.")
        sf_info.setWordWrap(True); sf_info.setStyleSheet("color:#555; padding:6px;"); sf_layout.addWidget(sf_info)

        sf_dep_group=QGroupBox("Dependencias del host")
        sf_dep_layout=QVBoxLayout(sf_dep_group)
        self.sf_dep_virtiofsd=QLabel("VirtioFS: SIN COMPROBAR")
        self.sf_dep_9p=QLabel("9p: SIN COMPROBAR")
        self.sf_dep_smb=QLabel("SMB: SIN COMPROBAR")
        dep_status_row=QHBoxLayout()
        for lab in (self.sf_dep_virtiofsd,self.sf_dep_9p,self.sf_dep_smb):
            lab.setMinimumWidth(180); dep_status_row.addWidget(lab)
        sf_dep_layout.addLayout(dep_status_row)
        sf_dep_note=QLabel("9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.")
        sf_dep_note.setWordWrap(True); sf_dep_note.setStyleSheet("color:#666;"); sf_dep_layout.addWidget(sf_dep_note)
        sf_dep_buttons=QHBoxLayout()
        self.btn_sf_check_deps=QPushButton("🔄 Comprobar")
        self.btn_sf_install_deps=QPushButton("🛠️ Instalar faltantes")
        self.btn_sf_check_deps.clicked.connect(self.refresh_shared_folder_dependencies)
        self.btn_sf_install_deps.clicked.connect(self.install_shared_folder_dependencies)
        sf_dep_buttons.addWidget(self.btn_sf_check_deps); sf_dep_buttons.addWidget(self.btn_sf_install_deps); sf_dep_buttons.addStretch()
        sf_dep_layout.addLayout(sf_dep_buttons)
        sf_layout.addWidget(sf_dep_group)

        self.shared_folders_tree=QTreeWidget()
        self.shared_folders_tree.setHeaderLabels(["Host","Guest / etiqueta","Método","Montaje en el guest","Acceso"])
        self.shared_folders_tree.setRootIsDecorated(False); self.shared_folders_tree.setAlternatingRowColors(True)
        sf_layout.addWidget(self.shared_folders_tree,1)
        sf_buttons=QHBoxLayout()
        self.btn_shared_add=QPushButton("➕ Agregar"); self.btn_shared_edit=QPushButton("✏ Modificar"); self.btn_shared_delete=QPushButton("🗑 Eliminar"); self.btn_shared_apply=QPushButton("💾 Guardar")
        self.btn_shared_add.clicked.connect(self.add_shared_folder); self.btn_shared_edit.clicked.connect(self.edit_shared_folder); self.btn_shared_delete.clicked.connect(self.delete_shared_folder); self.btn_shared_apply.clicked.connect(self.save_shared_folders)
        for b in (self.btn_shared_add,self.btn_shared_edit,self.btn_shared_delete,self.btn_shared_apply): sf_buttons.addWidget(b)
        sf_buttons.addStretch(); sf_layout.addLayout(sf_buttons)

        # --- Subpestaña: Guest Tools ---
        guest_tools_page=QWidget(); gt_layout=QVBoxLayout(guest_tools_page)
        gt_info=QLabel("Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.")
        gt_info.setWordWrap(True); gt_info.setStyleSheet("color:#555; padding:6px;"); gt_layout.addWidget(gt_info)
        gt_group=QGroupBox("QEMU Guest Agent")
        gt_form=QFormLayout(gt_group)
        self.guest_agent_enabled=QCheckBox("Activar canal QEMU Guest Agent al iniciar la VM")
        self.guest_agent_enabled.setChecked(False)
        self.guest_agent_enabled.stateChanged.connect(lambda _state: self.save_guest_tools_settings())
        gt_form.addRow("Canal:",self.guest_agent_enabled)
        self.guest_agent_status_label=QLabel("Estado: no comprobado")
        self.guest_agent_status_label.setWordWrap(True); gt_form.addRow("Estado:",self.guest_agent_status_label)
        gt_buttons=QHBoxLayout()
        self.btn_guest_agent_test=QPushButton("🔎 Probar conexión")
        self.btn_guest_tools_iso=QPushButton("💿 Crear / actualizar ISO Guest Tools")
        self.btn_guest_tools_attach=QPushButton("🧰 Adjuntar a esta VM")
        self.btn_guest_tools_attach.setToolTip("Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.")
        self.btn_guest_tools_open=QPushButton("📂 Abrir carpeta de Guest Tools")
        self.btn_guest_agent_test.clicked.connect(self.test_guest_agent)
        self.btn_guest_tools_iso.clicked.connect(self.create_guest_tools_iso_ui)
        self.btn_guest_tools_attach.clicked.connect(self.attach_guest_tools_iso)
        self.btn_guest_tools_open.clicked.connect(self.open_guest_tools_folder)
        gt_buttons.addWidget(self.btn_guest_agent_test); gt_buttons.addWidget(self.btn_guest_tools_iso); gt_buttons.addWidget(self.btn_guest_tools_attach); gt_buttons.addWidget(self.btn_guest_tools_open); gt_buttons.addStretch()
        gt_form.addRow("Acciones:",gt_buttons)
        gt_layout.addWidget(gt_group)
        gt_note=QLabel("Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.")
        gt_note.setWordWrap(True); gt_note.setStyleSheet("color:#666;"); gt_layout.addWidget(gt_note)
        gt_layout.addStretch(1)

        # --- Subpestaña: Clipboard ---
        clipboard_page=QWidget(); cb_layout=QVBoxLayout(clipboard_page)
        cb_group=QGroupBox("Compartir clipboard")
        cb_form=QFormLayout(cb_group)
        self.clipboard_mode=QComboBox()
        self.clipboard_mode.addItem("Desactivado","disabled")
        self.clipboard_mode.addItem("Host → SO invitado","host_to_guest")
        self.clipboard_mode.addItem("SO invitado → Host","guest_to_host")
        self.clipboard_mode.addItem("Bidireccional","bidirectional")
        cb_form.addRow("Dirección:",self.clipboard_mode)
        cb_note=QLabel("Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.")
        cb_note.setWordWrap(True); cb_note.setStyleSheet("color:#666;"); cb_form.addRow("",cb_note)
        cb_buttons=QHBoxLayout()
        self.btn_clipboard_save=QPushButton("💾 Guardar configuración")
        self.btn_clipboard_save.clicked.connect(self.save_clipboard_settings)
        cb_buttons.addWidget(self.btn_clipboard_save); cb_buttons.addStretch()
        cb_form.addRow("",cb_buttons)
        cb_layout.addWidget(cb_group)
        cb_status=QGroupBox("Estado")
        cb_status_lay=QVBoxLayout(cb_status)
        self.clipboard_status_label=QLabel("Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.")
        self.clipboard_status_label.setWordWrap(True); cb_status_lay.addWidget(self.clipboard_status_label)
        cb_layout.addWidget(cb_status)
        cb_layout.addStretch(1)

        self.shared_subtabs.addTab(shared_folders_page,"Compartir Carpetas")
        self.shared_subtabs.addTab(guest_tools_page,"Guest Tools")
        self.shared_subtabs.addTab(clipboard_page,"Clipboard")
        shared_outer_layout.addWidget(self.shared_subtabs,1)
        shared_scroll=QScrollArea(); shared_scroll.setWidgetResizable(True); shared_scroll.setFrameShape(QScrollArea.Shape.NoFrame); shared_scroll.setWidget(shared_page)
        self.refresh_shared_folder_dependencies()

        # Passthrough de dispositivos del host (PCI/USB).
        passthrough_page = QWidget()
        pt_layout = QVBoxLayout(passthrough_page)
        pt_info = QLabel("Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.")
        pt_info.setWordWrap(True)
        pt_info.setStyleSheet("color:#555; padding:6px;")
        pt_layout.addWidget(pt_info)

        vfio_group = QGroupBox("Diagnóstico PCI / VFIO")
        vfio_lay = QVBoxLayout(vfio_group)
        self.vfio_diag_label = QLabel("Comprobando Intel VT-d / IOMMU...")
        self.vfio_diag_label.setWordWrap(True)
        self.vfio_diag_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        vfio_lay.addWidget(self.vfio_diag_label)
        vfio_btns = QHBoxLayout()
        self.btn_vfio_refresh = QPushButton("🔄 Comprobar IOMMU / VFIO")
        self.btn_vfio_refresh.clicked.connect(self.refresh_vfio_diagnostics)
        self.btn_vfio_details = QPushButton("ℹ Ver diagnóstico detallado")
        self.btn_vfio_details.clicked.connect(self.vfio_diagnostic_details)
        self.btn_vfio_prepare = QPushButton("🛠 Preparar intel_iommu=on")
        self.btn_vfio_prepare.clicked.connect(self.prepare_iommu_from_ui)
        self.btn_vfio_firmware = QPushButton("⚙ Abrir UEFI/BIOS")
        self.btn_vfio_firmware.clicked.connect(self.open_firmware_setup)
        vfio_btns.addWidget(self.btn_vfio_refresh)
        vfio_btns.addWidget(self.btn_vfio_details)
        vfio_btns.addWidget(self.btn_vfio_prepare)
        vfio_btns.addWidget(self.btn_vfio_firmware)
        vfio_btns.addStretch()
        vfio_lay.addLayout(vfio_btns)
        pt_layout.addWidget(vfio_group)

        # --- Permisos USB (regla udev) ---
        # Se comprueba si existe la regla que permite el passthrough USB
        # sin pedir contraseña cada vez. Si falta, se puede instalar aquí
        # mismo con un solo clic (usa pkexec).
        usb_perm_group = QGroupBox("Permisos USB del host")
        usb_perm_layout = QVBoxLayout(usb_perm_group)

        usb_perm_info = QLabel(
            "Para poder pasar memorias o discos USB a la VM sin pedir "
            "contraseña cada vez, el sistema necesita una regla udev que "
            "conceda acceso al usuario activo. Puedes instalarla aquí con "
            "un clic; solo se aplica a esta categoría de dispositivos."
        )
        usb_perm_info.setWordWrap(True)
        usb_perm_info.setStyleSheet("color:#666; font-size: 11px;")
        usb_perm_layout.addWidget(usb_perm_info)

        usb_perm_row = QHBoxLayout()
        self.usb_perm_status_label = QLabel("Comprobando…")
        self.usb_perm_status_label.setStyleSheet("font-weight: bold;")
        usb_perm_row.addWidget(self.usb_perm_status_label)
        usb_perm_row.addStretch()

        self.btn_usb_perm_check = QPushButton("🔄 Comprobar")
        self.btn_usb_perm_check.clicked.connect(self.refresh_usb_permissions_status)
        usb_perm_row.addWidget(self.btn_usb_perm_check)

        self.btn_usb_perm_install = QPushButton("🔧 Configurar permisos USB")
        self.btn_usb_perm_install.setToolTip(
            "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\n"
            "que permite el acceso a los dispositivos USB al usuario activo.\n"
            "Solo se toca este archivo; el resto de la configuración USB\n"
            "del sistema no se modifica."
        )
        self.btn_usb_perm_install.clicked.connect(self.install_usb_permissions)
        usb_perm_row.addWidget(self.btn_usb_perm_install)
        usb_perm_layout.addLayout(usb_perm_row)

        pt_layout.addWidget(usb_perm_group)

        self.passthrough_tree = QTreeWidget()
        self.passthrough_tree.setHeaderLabels(["Usar", "Tipo", "Dispositivo", "IOMMU / Driver", "Estado"] )
        self.passthrough_tree.setColumnWidth(0, 55)
        self.passthrough_tree.setColumnWidth(1, 55)
        self.passthrough_tree.setColumnWidth(3, 170)
        pt_layout.addWidget(self.passthrough_tree, 1)
        pt_buttons = QHBoxLayout()
        self.btn_passthrough_refresh = QPushButton("🔄 Detectar dispositivos")
        self.btn_passthrough_apply = QPushButton("💾 Guardar selección")
        self.btn_passthrough_refresh.clicked.connect(self.refresh_passthrough_tree)
        self.btn_passthrough_apply.clicked.connect(self.save_passthrough_selection)
        self.btn_passthrough_hotplug = QPushButton("🔌 Conectar USB en caliente")
        self.btn_passthrough_hotplug.clicked.connect(self.passthrough_usb_hotplug)
        self.btn_passthrough_unplug = QPushButton("⏏ Desconectar USB")
        self.btn_passthrough_unplug.clicked.connect(self.passthrough_usb_unplug)
        pt_buttons.addWidget(self.btn_passthrough_refresh)
        pt_buttons.addWidget(self.btn_passthrough_apply)
        pt_buttons.addWidget(self.btn_passthrough_hotplug)
        pt_buttons.addWidget(self.btn_passthrough_unplug)
        pt_buttons.addStretch()
        pt_layout.addLayout(pt_buttons)
        # La población del árbol de Passthrough (lspci, lsusb, dmesg,
        # journalctl) se difiere hasta que el usuario abra la pestaña
        # Passthrough por primera vez. Antes se ejecutaba en cada
        # arranque y sumaba medio segundo aunque el usuario no fuera
        # a usar Passthrough en esa sesión.
        self._passthrough_tree_needs_first_populate = True
        # El estado de los permisos USB es barato (un stat) y conviene
        # tenerlo listo, pero tampoco bloquea nada crítico.
        try:
            self.refresh_usb_permissions_status()
        except Exception:
            pass

        pt_scroll = QScrollArea()
        pt_scroll.setWidgetResizable(True)
        pt_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        pt_scroll.setWidget(passthrough_page)

        config_page = QWidget()
        config_page.setMinimumWidth(0)
        config_page.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        config_page.setLayout(main_layout)
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        config_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        config_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        config_scroll.setWidget(config_page)
        self.config_scroll = config_scroll

        self.main_tabs = QTabWidget()
        # El panel central debe poder encogerse cuando el usuario
        # arrastra el handle del splitter. Sin esto, sus tabs fuerzan
        # un ancho mínimo alto y el splitter redistribuye hacia los
        # laterales, que es el bug que estamos corrigiendo.
        self.main_tabs.setMinimumWidth(200)
        self.main_tabs.setUsesScrollButtons(True)
        try:
            self.main_tabs.tabBar().setUsesScrollButtons(True)
            self.main_tabs.tabBar().setExpanding(False)
        except Exception:
            pass
        self.main_tabs.setDocumentMode(True)
        self.main_tabs.addTab(details_page, "Resumen")
        self.main_tabs.addTab(config_scroll, "Configuración")
        # Passthrough pertenece al bloque de hardware y va inmediatamente después de Configuración.
        self.main_tabs.addTab(pt_scroll, "Passthrough")
        self._passthrough_tab_index = 2
        self.main_tabs.addTab(shared_scroll, "Carpetas compartidas")
        self._shared_tab_index = 3
        self.main_tabs.addTab(snap_scroll, "Snapshots")
        self._snapshots_tab_index = 4

        # Pestaña "Consola": VNC embebido para ver la VM dentro de la app.
        # Solo se muestra si el widget VNC está disponible.
        if _HAS_VNC_WIDGET:
            self.console_page = QWidget()
            console_layout = QVBoxLayout(self.console_page)
            console_layout.setContentsMargins(6, 6, 6, 6)

            # Barra superior con acciones de la consola gráfica.
            console_toolbar = QHBoxLayout()
            # --- Banner de estado de consola ---
            # Muestra en una línea el estado actual de la elección:
            # verde si se aplica, ámbar si hay adaptación, rojo si falla.
            self.label_console_status = QLabel("")
            self.label_console_status.setWordWrap(False)
            self.label_console_status.setStyleSheet(
                "font-size:11px; padding:2px 6px; border-radius:4px;"
            )
            console_toolbar.addWidget(self.label_console_status)
            console_toolbar.addSpacing(8)
            self.vnc_label_status = QLabel("La VM no está corriendo.")
            self.vnc_label_status.setStyleSheet("color:#666; padding:4px;")
            console_toolbar.addWidget(self.vnc_label_status)
            console_toolbar.addStretch(1)

            # Las opciones de protocolo y modo viven en
            # Configuración → Pantalla. Aquí solo dejamos acciones.
            self.btn_console_launch_external = QPushButton("↗ Abrir en ventana externa")
            self.btn_console_launch_external.setToolTip(
                "Lanza el visor externo del protocolo configurado en Pantalla,\n"
                "aunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez."
            )
            self.btn_console_launch_external.clicked.connect(
                self._launch_external_console
            )
            console_toolbar.addWidget(self.btn_console_launch_external)

            # Checkbox: abrir el visor externo en pantalla completa.
            # Solo aplica al modo 'external' o al botón 'Abrir en ventana\n            # externa'; el widget embebido no se ve afectado.
            self.chk_external_fullscreen = QCheckBox("Pantalla completa")
            self.chk_external_fullscreen.setToolTip(
                "Cuando está marcado, los visores externos se lanzan\n"
                "ocupando toda la pantalla. La combinación para salir\n"
                "la gestiona cada visor (habitualmente F11, Escape o\n"
                "Ctrl+Q según el visor)."
            )
            self.chk_external_fullscreen.setChecked(
                QSettings().value("console/external_fullscreen", False, type=bool)
            )
            self.chk_external_fullscreen.toggled.connect(
                self._on_external_fullscreen_toggled
            )
            console_toolbar.addWidget(self.chk_external_fullscreen)
            console_toolbar.addSpacing(12)
            console_toolbar.addWidget(QLabel("Salir con:"))
            self.combo_fullscreen_exit = QComboBox()
            for label, seq_str in FULLSCREEN_EXIT_SHORTCUTS:
                self.combo_fullscreen_exit.addItem(label, seq_str)
            self.combo_fullscreen_exit.setToolTip(
                "Combinación de teclas para salir de la pantalla completa de la consola VNC.\n"
                "Evita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\n"
                "usar Escape o F11 dentro del sistema invitado, no la uses aquí)."
            )
            saved_seq = QSettings().value(
                "console/fullscreen_exit_shortcut", DEFAULT_FULLSCREEN_EXIT_SHORTCUT
            )
            idx = self.combo_fullscreen_exit.findData(saved_seq)
            self.combo_fullscreen_exit.setCurrentIndex(idx if idx >= 0 else 0)
            self.combo_fullscreen_exit.currentIndexChanged.connect(
                self._on_fullscreen_exit_shortcut_changed
            )
            console_toolbar.addWidget(self.combo_fullscreen_exit)

            # "Tamaño real": alternativa a escalar la imagen cuando la
            # resolución de la VM no coincide con la del monitor. En vez de
            # reescalar (lo que puede dejar la imagen recortada o
            # demasiado pequeña si la VM usa una resolución mayor que la
            # pantalla), muestra la VM a resolución 1:1 y agrega barras de
            # desplazamiento —tanto aquí como en pantalla completa— para
            # moverse por el resto de la imagen.
            self.chk_vnc_real_size = QCheckBox("Tamaño real (con scroll)")
            self.chk_vnc_real_size.setToolTip(
                "Si la resolución de la VM no coincide con la de tu monitor (por ejemplo,\n"
                "una VM a 1920x1080 en un monitor más pequeño), esta opción evita reescalar\n"
                "la imagen: la muestra a su tamaño real y aparecen barras de desplazamiento\n"
                "para ver el resto. Aplica tanto aquí como en pantalla completa."
            )
            self.chk_vnc_real_size.setChecked(
                QSettings().value("console/vnc_real_size", False, type=bool)
            )
            self.chk_vnc_real_size.toggled.connect(self._on_vnc_real_size_toggled)
            console_toolbar.addWidget(self.chk_vnc_real_size)

            # Botón de refresco manual: recrea el backbuffer y
            # fuerza un frame completo desde el servidor VNC.
            # Útil si tras un cambio de resolución del guest la
            # pantalla no se ha redibujado correctamente.
            self.btn_vnc_refresh = QPushButton("🔄 Reconectar")
            self.btn_vnc_refresh.setToolTip(
                "Reconectar el widget VNC.\n"
                "Útil si cambiaste la resolución del guest y la imagen\n"
                "quedó recortada o mal escalada. El cliente VNC básico\n"
                "no puede cambiar el tamaño de su framebuffer sin\n"
                "reconectar.\n\n"
                "Atajo: Ctrl+R."
            )
            self.btn_vnc_refresh.setMinimumWidth(130)
            self.btn_vnc_refresh.clicked.connect(self._manual_refresh_vnc)
            console_toolbar.addWidget(self.btn_vnc_refresh)

            self.btn_vnc_fullscreen = QPushButton("⛶ Pantalla completa")
            self.btn_vnc_fullscreen.setEnabled(False)  # se activa cuando hay VM
            self.btn_vnc_fullscreen.clicked.connect(self._toggle_vnc_fullscreen)
            console_toolbar.addWidget(self.btn_vnc_fullscreen)
            self._update_fullscreen_button_tooltip()

            console_layout.addLayout(console_toolbar)

            # Placeholder para el widget VNC (se crea al conectar)
            self.vnc_widget = None
            self.vnc_placeholder = QLabel("")
            self.vnc_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vnc_placeholder.setStyleSheet(
                "background: #1e1e1e; color: #888; font-size: 14px; border: 1px solid palette(mid);"
            )
            self.vnc_placeholder.setMinimumHeight(200)
            self.vnc_placeholder.setText("Esperando conexión de la VM...")
            console_layout.addWidget(self.vnc_placeholder, 1)

            self.main_tabs.addTab(self.console_page, "🖥️ Consola Gráfica")
            self._console_tab_index = 5
        else:
            self._console_tab_index = -1
            self.btn_vnc_fullscreen = None
            self.combo_fullscreen_exit = None
            self.chk_vnc_real_size = None

        # La Consola de Progreso vive ahora como pestaña, al lado de
        # 'Consola Gráfica'. Antes estaba en el panel central inferior
        # y robaba altura a las pestañas principales.
        console_group = QWidget()
        console_layout = QVBoxLayout(console_group)
        console_layout.setContentsMargins(6, 6, 6, 6)
        console_header = QHBoxLayout()
        self.btn_vm_health = QPushButton("🩺 Salud de la VM")
        self.btn_vm_health.setToolTip("Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.")
        self.btn_vm_health.clicked.connect(self.show_vm_health_check)
        console_header.addWidget(self.btn_vm_health)
        self.btn_clean_orphans = QPushButton("🧹 Limpiar procesos huérfanos")
        self.btn_clean_orphans.setToolTip("Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.")
        self.btn_clean_orphans.clicked.connect(self.clean_orphan_processes)
        console_header.addWidget(self.btn_clean_orphans)
        # --- Filtros y opciones de la consola ---
        # Nivel mínimo: filtra las líneas que se muestran sin perder
        # el historial (se puede volver a subir el nivel y reaparecen).
        console_header.addWidget(QLabel("Nivel:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("Todo", "info")
        self.log_level_combo.addItem("Avisos+", "warn")
        self.log_level_combo.addItem("Errores", "error")
        self.log_level_combo.setCurrentIndex(0)
        self.log_level_combo.setToolTip(
            "Muestra solo las líneas con este nivel o superior.\n"
            "El historial completo se conserva: al bajar el nivel se\n"
            "vuelven a mostrar las líneas anteriores."
        )
        self.log_level_combo.currentIndexChanged.connect(self._on_log_level_changed)
        self._log_min_level = "info"
        console_header.addWidget(self.log_level_combo)

        # Buscador: filtra por texto contenido en la línea.
        self.log_search_box = QLineEdit()
        self.log_search_box.setPlaceholderText("🔍 Filtrar...")
        self.log_search_box.setFixedWidth(160)
        self.log_search_box.setToolTip(
            "Muestra solo las líneas que contengan este texto.\n"
            "No distingue mayúsculas de minúsculas."
        )
        self.log_search_box.textChanged.connect(self._on_log_search_changed)
        self._log_filter_text = ""
        console_header.addWidget(self.log_search_box)

        # Auto-scroll: si está marcado, la consola baja sola al
        # añadirse líneas nuevas (como una terminal).
        self.log_autoscroll_cb = QCheckBox("Auto-scroll")
        self.log_autoscroll_cb.setChecked(True)
        self.log_autoscroll_cb.setToolTip(
            "Si está marcado, la consola baja automáticamente al\n"
            "recibir líneas nuevas. Desmárcalo para inspeccionar el\n"
            "historial sin que se mueva solo."
        )
        self.log_autoscroll_cb.stateChanged.connect(self._on_log_autoscroll_changed)
        self._log_autoscroll = True
        console_header.addWidget(self.log_autoscroll_cb)

        console_header.addStretch(1)
        self.btn_view_full_log = QPushButton("📄 Ver log completo")
        self.btn_view_full_log.setToolTip("Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.")
        self.btn_view_full_log.clicked.connect(self.show_full_log)
        console_header.addWidget(self.btn_view_full_log)
        self.btn_export_log = QPushButton("💾 Exportar log")
        self.btn_export_log.setToolTip("Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.")
        self.btn_export_log.clicked.connect(self.export_full_log)
        console_header.addWidget(self.btn_export_log)
        self.btn_clear_console = QPushButton("Limpiar consola")
        self.btn_clear_console.setToolTip("Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').")
        self.btn_clear_console.clicked.connect(self._clear_log_console)
        console_header.addWidget(self.btn_clear_console)
        console_layout.addLayout(console_header)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(90)
        self.console.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.console.setObjectName("consoleBox")
        self.console.setAcceptRichText(True)
        console_layout.addWidget(self.console)
        self.main_tabs.addTab(console_group, "📋 Consola de Progreso")
        self._progress_console_tab_index = self.main_tabs.count() - 1

        # --- Pestaña Ayuda ---
        # Contenido de la ayuda como pestaña final (antes era un corner
        # widget). Se construye una vez y no se actualiza.
        self.help_page = QWidget()
        help_outer = QVBoxLayout(self.help_page)
        help_outer.setContentsMargins(16, 16, 16, 16)
        help_outer.setSpacing(8)

        help_title = QLabel("<h2>Ayuda de Virtual.Machine</h2>")
        help_outer.addWidget(help_title)

        # Boton para abrir la guia completa de la consola.
        help_top_row = QHBoxLayout()
        self.btn_help_console_guide = QPushButton(
            "Guia completa de la consola (VNC / SPICE)"
        )
        self.btn_help_console_guide.setMinimumHeight(32)
        self.btn_help_console_guide.setToolTip(
            "Abre README_console.md con el visor del sistema.\n"
            "Contiene el diagrama de decision, dependencias por\n"
            "sistema y troubleshooting completo."
        )
        self.btn_help_console_guide.clicked.connect(self._open_console_guide)
        help_top_row.addWidget(self.btn_help_console_guide)
        help_top_row.addStretch(1)
        help_outer.addLayout(help_top_row)

        help_text = QLabel()
        help_text.setWordWrap(True)
        help_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        help_text.setText(
            "<p><b>Virtual.Machine</b> es un asistente gráfico para crear y "
            "administrar máquinas virtuales con QEMU/KVM.</p>"
            "<h3>Primeros pasos</h3>"
            "<ul>"
            "  <li>Pulsa <b>Nueva VM</b> en el panel izquierdo para crear una "
            "      máquina virtual desde cero.</li>"
            "  <li>Selecciona una VM en la lista para ver su estado y configurarla.</li>"
            "  <li>Usa el botón <b>Iniciar</b> para arrancarla y el botón "
            "      <b>Apagar</b> para detenerla.</li>"
            "</ul>"
            "<h3>Panel derecho</h3>"
            "<ul>"
            "  <li><b>Uso de recursos</b>: CPU, RAM, disco y red de la VM en vivo.</li>"
            "  <li><b>Información general</b>: estado, PID, IP, MAC, discos, "
            "      snapshots y estado de la integración con el guest.</li>"
            "  <li><b>Último snapshot</b>: vista previa del snapshot más reciente.</li>"
            "  <li><b>Sugerencias</b>: avisos y recomendaciones según el estado "
            "      de la VM.</li>"
            "</ul>"
            "<h3>Pestañas de la máquina virtual</h3>"
            "<ul>"
            "  <li><b>Resumen</b>: acciones sobre la VM (Clonar, Importar, "
            "      Exportar, Eliminar).</li>"
            "  <li><b>Configuración</b>: hardware, almacenamiento, red, "
            "      dispositivos y opciones avanzadas.</li>"
            "  <li><b>Passthrough</b>: pasar hardware físico (PCI/USB) a la VM.</li>"
            "  <li><b>Carpetas compartidas</b>: integrar el guest con el host.</li>"
            "  <li><b>Snapshots</b>: crear, restaurar y eliminar instantáneas.</li>"
            "  <li><b>Consola Gráfica</b>: ver la VM dentro de la app (si está "
            "      disponible).</li>"
            "  <li><b>Consola de Progreso</b>: log detallado de la aplicación.</li>"
            "</ul>"
            "<h3>Atajos de teclado</h3>"
            "<ul>"
            "  <li><b>Ctrl+M</b>: abrir el menú de Medios (CD/DVD, USB).</li>"
            "  <li>Dentro del widget VNC: hacer clic dentro para capturar "
            "      el teclado. Clic fuera para liberarlo.</li>"
            "  <li>En pantalla completa del VNC: la combinación configurada "
            "      en la barra de la Consola Gráfica (por defecto Ctrl derecho).</li>"
            "</ul>"
            "<h3>Problemas frecuentes</h3>"
            "<ul>"
            "  <li><b>La VM no arranca</b>: revisa la Consola de Progreso. "
            "      Pulsa <b>Salud de la VM</b> para diagnóstico.</li>"
            "  <li><b>Sin salida gráfica</b>: prueba a cambiar el modo en "
            "      Configuración → Pantalla.</li>"
            "  <li><b>USB no se conecta</b>: comprueba los permisos en "
            "      Passthrough → Permisos USB.</li>"
            "  <li><b>Teclas especiales no llegan al guest</b>: en Wayland, "
            "      Meta/Super y Ctrl+Alt+F* no se pueden capturar por diseño. "
            "      Inicia sesión en X11 si las necesitas.</li>"
            "</ul>"
            "<hr>"
            "<p style='color:#888; font-size:11px;'>"
            "Virtual.Machine — Asistente Multi-VM QEMU/KVM. "
            "</p>"
        )
        help_scroll = QScrollArea()
        help_scroll.setWidgetResizable(True)
        help_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        help_container = QWidget()
        help_container_layout = QVBoxLayout(help_container)
        help_container_layout.setContentsMargins(0, 0, 0, 0)
        help_container_layout.addWidget(help_text)
        help_container_layout.addStretch(1)
        help_scroll.setWidget(help_container)
        help_outer.addWidget(help_scroll, 1)

        self.main_tabs.addTab(self.help_page, "❓ Ayuda")
        self._help_tab_index = self.main_tabs.count() - 1

        self.main_tabs.setCurrentIndex(0)
        self.main_tabs.currentChanged.connect(self._on_main_tab_changed)
        self._performance_timer = QTimer(self)
        self._performance_timer.setInterval(1000)
        self._performance_timer.timeout.connect(self._update_realtime_performance)
        self._performance_timer.stop()

        # Mantener ocultos dentro de Configuración los controles duplicados que ahora
        # están en la barra estilo VirtualBox, pero conservar sus referencias y señales.
        for w in (self.btn_vm_summary, self.btn_vm_folder, self.btn_vm_clone, self.btn_vm_delete, self.vm_status_label):
            w.hide()

        right_panel = QWidget()
        # Mínimo bajo: el panel central es el que absorbe los
        # cambios del splitter. Si esto fuera alto, los laterales
        # se verían afectados al arrastrar (bug original).
        right_panel.setMinimumWidth(200)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(self.main_tabs, 1)


        # --- Panel de recursos (con botón de fijar) ---
        # El panel puede alternar entre dos ubicaciones con el botón
        # "📌 Fijar" de su cabecera:
        #   1. Dentro de la pestaña Resumen (por defecto).
        #   2. Como tercera columna del splitter (siempre visible).
        # El estado se guarda en QSettings entre sesiones.
        self._resources_panel = QWidget()
        self._resources_panel.setObjectName("resourcesPanel")
        resources_layout = QVBoxLayout(self._resources_panel)
        resources_layout.setContentsMargins(0, 0, 0, 0)
        resources_layout.setSpacing(10)

        _resources_header = QHBoxLayout()
        _resources_header.addStretch(1)
        self.btn_pin_resources = QPushButton("📌 Fijar")
        self.btn_pin_resources.setToolTip(
            "Fija este panel como columna derecha de la ventana, siempre visible.\n"
            "Útil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\n"
            "Vuelve a pulsar para devolverlo a Resumen."
        )
        self.btn_pin_resources.setMaximumWidth(140)
        self.btn_pin_resources.clicked.connect(
            lambda _checked=False: self._apply_resources_pinned(
                not getattr(self, "_resources_pinned", False)
            )
        )
        _resources_header.addWidget(self.btn_pin_resources)
        resources_layout.addLayout(_resources_header)

        # Guardar la referencia al layout del scroll de Resumen: allí vive
        # el panel cuando NO está fijado.
        self._details_scroll_layout = details_scroll_layout
        self._resources_pinned = False

        usage_box = QGroupBox("📊 Uso de recursos")
        usage_layout = QVBoxLayout(usage_box)
        self.perf_cpu_graph = RealtimePerformanceGraph("CPU (VM)", "%", 100)
        self.perf_cpu_graph.setToolTip(
            "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n"
            "100% = el proceso usa el equivalente a todos los hilos del host.\n"
            "Si el host tiene 8 hilos y QEMU usa 4, verás 50%."
        )
        self.perf_ram_graph = RealtimePerformanceGraph("RAM (QEMU)", "%", 100)
        self.perf_ram_graph.setToolTip(
            "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\n"
            "realmente en el sistema anfitrión), como porcentaje de la RAM\n"
            "total del host. No es la RAM que 've' el sistema invitado."
        )
        self.perf_disk_graph = RealtimePerformanceGraph("Disco (VM)", "MB/s", 100)
        self.perf_disk_graph.setToolTip(
            "I/O de disco generado por el proceso QEMU para esta VM, según\n"
            "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
            "Es el tráfico real a los archivos de disco de la VM en el host."
        )
        self.perf_net_graph = RealtimePerformanceGraph("Red (VM)", "MB/s", 100)
        self.perf_net_graph.setToolTip(
            "Tráfico de red de esta VM.\n"
            "• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n"
            "  asociada en el host (exacto).\n"
            "• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n"
            "  el host, así que no se puede medir sin Guest Agent.\n"
            "  El gráfico mostrará 'NAT (sin medida)'."
        )
        for g in (self.perf_cpu_graph, self.perf_ram_graph, self.perf_disk_graph, self.perf_net_graph):
            g.setMinimumHeight(70)
            usage_layout.addWidget(g)
        resources_layout.addWidget(usage_box)

        info_general_box = QGroupBox("ℹ️ Información general")
        info_general_layout = QFormLayout(info_general_box)
        self.info_estado_label = QLabel("● Sin VM seleccionada")
        self.info_uptime_label = QLabel("—")
        self.info_procesos_label = QLabel("—")
        self.info_ip_label = QLabel("—")
        self.info_mac_label = QLabel("—")
        info_general_layout.addRow("Estado:", self.info_estado_label)
        info_general_layout.addRow("Tiempo activo:", self.info_uptime_label)
        info_general_layout.addRow("Procesos:", self.info_procesos_label)
        info_general_layout.addRow("Dirección IP:", self.info_ip_label)
        info_general_layout.addRow("Dirección MAC:", self.info_mac_label)

        # --- Estado de la integración con el guest ---
        # Antes vivían en el panel izquierdo, bajo el estado de la VM.
        # Ahora están aquí porque son información de la VM, no acciones.
        self.label_live_guest_agent = QLabel("Guest Agent: —")
        self.label_live_guest_agent.setStyleSheet("font-size:11px; color:#757575;")
        info_general_layout.addRow("Guest Agent:", self.label_live_guest_agent)

        self.label_live_shared_folders = QLabel("Carpetas: —")
        self.label_live_shared_folders.setStyleSheet("font-size:11px; color:#757575;")
        info_general_layout.addRow("Carpetas:", self.label_live_shared_folders)

        self.label_live_clipboard = QLabel("Clipboard: —")
        self.label_live_clipboard.setStyleSheet("font-size:11px; color:#757575;")
        info_general_layout.addRow("Clipboard:", self.label_live_clipboard)

        self.label_live_vdagent = QLabel("spice-vdagent: —")
        self.label_live_vdagent.setStyleSheet("font-size:11px; color:#757575;")
        self.label_live_vdagent.setToolTip(
            "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\n"
            "Cuando está activo, el clipboard bidireccional y la\n"
            "resolución automática funcionan."
        )
        info_general_layout.addRow("spice-vdagent:", self.label_live_vdagent)

        # --- Campos adicionales (actualizados en _refresh_general_info_extra) ---
        self.info_pid_label = QLabel("—")
        info_general_layout.addRow("PID QEMU:", self.info_pid_label)

        self.info_cpu_host_label = QLabel("—")
        self.info_cpu_host_label.setToolTip(
            "Uso de CPU del proceso QEMU expresado como porcentaje del total\n"
            "de hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\n"
            "valor mostrado es 50%."
        )
        info_general_layout.addRow("CPU (VM):", self.info_cpu_host_label)

        self.info_ram_host_label = QLabel("—")
        self.info_ram_host_label.setToolTip(
            "Memoria RAM libre del host, respecto al total."
        )
        info_general_layout.addRow("RAM host:", self.info_ram_host_label)

        self.info_disk_size_label = QLabel("—")
        self.info_disk_size_label.setToolTip(
            "Tamaño del archivo de disco principal de la VM y su tamaño\n"
            "virtual (lo que ve el sistema invitado)."
        )
        info_general_layout.addRow("Disco:", self.info_disk_size_label)

        self.info_snapshots_label = QLabel("—")
        self.info_snapshots_label.setToolTip(
            "Número de snapshots registrados y antigüedad del último."
        )
        info_general_layout.addRow("Snapshots:", self.info_snapshots_label)

        # Panel del último snapshot: miniatura + restaurar en un clic.
        # Vive en el panel derecho (siempre visible) para que el usuario
        # no tenga que cambiar a la pestaña Snapshots solo para verlo.
        last_snap_box = QGroupBox("🖼️ Último snapshot")
        last_snap_layout = QVBoxLayout(last_snap_box)
        last_snap_layout.setContentsMargins(8, 8, 8, 8)
        last_snap_layout.setSpacing(6)

        self.last_snap_thumbnail = QLabel("Sin VM seleccionada")
        self.last_snap_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_snap_thumbnail.setMinimumHeight(120)
        self.last_snap_thumbnail.setMaximumHeight(140)
        self.last_snap_thumbnail.setStyleSheet(
            "background: palette(alternate-base); border: 1px solid palette(mid); "
            "border-radius: 6px; color: #888; font-size: 11px;"
        )
        last_snap_layout.addWidget(self.last_snap_thumbnail)

        self.last_snap_name_label = QLabel("—")
        self.last_snap_name_label.setWordWrap(True)
        self.last_snap_name_label.setStyleSheet("font-size: 11px; color: #666; padding: 0 2px;")
        last_snap_layout.addWidget(self.last_snap_name_label)

        # Fecha y hora del snapshot (mtime del PNG). Se rellena en
        # _refresh_last_snapshot_thumbnail().
        self.last_snap_time_label = QLabel("")
        self.last_snap_time_label.setWordWrap(False)
        self.last_snap_time_label.setStyleSheet(
            "font-size: 10px; color: #888; padding: 0 2px 2px 2px;"
        )
        last_snap_layout.addWidget(self.last_snap_time_label)

        self.btn_last_snap_restore = QPushButton("↩ Restaurar este snapshot")
        self.btn_last_snap_restore.setToolTip(
            "Restaura el snapshot más reciente de esta VM.\n"
            "Si la VM está corriendo, se restaura en caliente (snapshot-load).\n"
            "Si está apagada, se restauran los discos QCOW2 internos."
        )
        self.btn_last_snap_restore.clicked.connect(self._restore_last_snapshot)
        self.btn_last_snap_restore.setEnabled(False)
        last_snap_layout.addWidget(self.btn_last_snap_restore)

        suggestions_box = self._build_suggestions_panel()
        resources_layout.addStretch(1)

        # --- Montaje de Resumen ---
        # Distribución:
        #   (0,0) Resumen de Configuración | (0,1) Información general
        #   (1,0) Uso de recursos (📌)     | (1,1) Último snapshot
        #   (2,0..1) Sugerencias
        #
        # El bloque "Uso de recursos + Información general" se puede sacar
        # de aquí con el botón 📌 Fijar: al fijarse se van juntos a la
        # columna derecha del splitter (ver _apply_resources_pinned).

        self._resumen_grid = QGridLayout()
        self._resumen_grid.setHorizontalSpacing(10)
        self._resumen_grid.setVerticalSpacing(10)
        self._resumen_grid.addWidget(info_box, 0, 0)
        self._resumen_grid.addWidget(info_general_box, 0, 1)
        self._resumen_grid.addWidget(self._resources_panel, 1, 0)
        self._resumen_grid.addWidget(last_snap_box, 1, 1)
        self._resumen_grid.addWidget(suggestions_box, 2, 0, 1, 2)
        self._resumen_grid.setColumnStretch(0, 1)
        self._resumen_grid.setColumnStretch(1, 1)

        # Guardamos referencias para el toggle (performance_mixin las usa).
        self._info_general_card = info_general_box
        self._last_snap_card = last_snap_box
        self._suggestions_card = suggestions_box

        details_scroll_layout.addLayout(self._resumen_grid)
        details_scroll_layout.addStretch(1)
        self._refresh_suggestions()


        # QSplitter permite arrastrar los divisores entre los tres paneles.
        # setChildrenCollapsible(False) evita que un arrastre accidental
        # esconda por completo un panel (el usuario tendría que volver a
        # arrastrar para recuperarlo, algo incómodo y poco evidente).
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        # ------------------------------------------------------------------
        # Envolver los paneles laterales en QScrollArea.
        # ------------------------------------------------------------------
        # Así, si el contenido del panel no cabe verticalmente (ventana
        # pequeña, o muchos elementos en el panel derecho), aparece una
        # barra de scroll en lugar de apretujar o recortar el contenido.
        # En el ancho NO hay scroll: el panel se ajusta al tamaño del
        # splitter (el usuario lo redimensiona arrastrando el handle).
        def _wrap_in_scroll(content_widget, min_width=0):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            if min_width:
                scroll.setMinimumWidth(min_width)
            scroll.setWidget(content_widget)
            return scroll

        # Extraer el ancho mínimo previo del panel izquierdo.
        _left_min = left_panel.minimumWidth() or 160

        # Los paneles ya no necesitan el mínimo: lo lleva el scroll externo.
        # Así el contenido puede ser más estrecho si el usuario arrastra
        # el splitter, sin forzar un ancho mínimo incómodo.
        left_panel.setMinimumWidth(0)

        self._left_scroll = _wrap_in_scroll(left_panel, min_width=_left_min)

        # Splitter de 2 paneles: [lista de VMs] [tabs].
        # El panel de recursos vive ahora dentro de la pestaña Resumen
        # (o como tercera columna si el usuario pulsa 'Fijar').
        splitter.addWidget(self._left_scroll)
        splitter.addWidget(right_panel)
        # ------------------------------------------------------------------
        # Cómo se reparte el espacio al arrastrar un handle.
        # ------------------------------------------------------------------
        # QSplitter reparte el cambio SOLO entre los dos paneles adyacentes
        # al handle que se arrastra, PERO si el panel afectado ya está en su
        # ancho mínimo, no puede encogerse más y el splitter termina
        # encogiendo el panel del otro lado. Para evitarlo:
        #
        # 1. El centro es el único panel flexible (política Ignored):
        #    absorbe cualquier cambio de tamaño sin forzar a los laterales.
        # 2. Los laterales son Preferred: crecen/decrecen cuando el usuario
        #    los arrastra, pero no absorben cambios ajenos.
        # 3. Bloqueamos el colapso de los laterales para que no se puedan
        #    "esconder" arrastrando el handle.
        #
        # Los mínimos se ajustan más abajo, tras crear los paneles.
        _policy_pref = QSizePolicy(QSizePolicy.Policy.Preferred,
                                    QSizePolicy.Policy.Expanding)
        _policy_flex = QSizePolicy(QSizePolicy.Policy.Ignored,
                                    QSizePolicy.Policy.Expanding)
        try:
            self._left_scroll.setSizePolicy(_policy_pref)
            right_panel.setSizePolicy(_policy_flex)
        except Exception:
            pass

        # Stretch factor 0 en laterales y 1 en el centro: al redimensionar
        # la ventana (no al arrastrar el handle), todo el "extra" va al
        # centro. Los laterales mantienen el ancho elegido por el usuario.
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Evitar que un arrastre accidental esconda los laterales.
        try:
            splitter.setCollapsible(0, False)
        except Exception:
            pass

        # Tamaños iniciales razonables para una ventana de 1080px.
        # Se restauran los últimos tamaños usados si el usuario ya redimensionó.
        saved = QSettings().value("layout/main_splitter_sizes")
        if isinstance(saved, list) and len(saved) == 3:
            try:
                splitter.setSizes([int(x) for x in saved])
            except (TypeError, ValueError):
                splitter.setSizes([210, 600, 300])
        else:
            splitter.setSizes([210, 600, 300])

        def _on_splitter_moved(_pos, _index):
            # Guardar tamaños en la clave correspondiente al estado
            # actual del panel de recursos (fijado o no).
            _key = ("layout/main_splitter_sizes_pinned"
                    if getattr(self, "_resources_pinned", False)
                    else "layout/main_splitter_sizes")
            QSettings().setValue(_key, splitter.sizes())

        splitter.splitterMoved.connect(_on_splitter_moved)
        self._main_splitter = splitter

        # Restaurar el estado del panel de recursos (fijado o no)
        # ANTES de montar el container central, para que todo esté
        # en su sitio desde el primer frame.
        try:
            _pinned_saved = bool(QSettings().value(
                "layout/resources_pinned", False, type=bool))
            if _pinned_saved:
                self._resources_pinned = False  # estado base antes del toggle
                self._apply_resources_pinned(True, save=False)
        except Exception:
            pass

        container = QWidget()
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(0)
        root_layout.addWidget(splitter)
        self.setCentralWidget(container)


    def _wire_signals(self):
        """Conexión de todas las señales a sus slots. Debe ejecutarse
        DESPUÉS de que todos los widgets existan."""
        pass  # Los connect() actuales siguen en el legacy.

    def _open_console_guide(self):
        """Abre README_console.md con el visor del sistema."""
        import shutil as _sh
        import subprocess as _sp
        import os as _os
        path = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)),
            "README_console.md",
        )
        if not _os.path.isfile(path):
            QMessageBox.information(
                self, "Guia de consola",
                "No se encontro el archivo:\n" + path + "\n\n"
                "Crea README_console.md en la raiz del proyecto."
            )
            return
        try:
            if _sh.which("xdg-open"):
                _sp.Popen(["xdg-open", path],
                          stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            else:
                QMessageBox.information(
                    self, "Guia de consola", "Archivo:\n" + path
                )
        except Exception as e:
            QMessageBox.warning(
                self, "Guia de consola",
                "No se pudo abrir el archivo:\n\n" + str(e)
            )

    def _apply_initial_state(self):
        """Timers, listas, estado inicial, etc."""
        self.btn_start = QPushButton("Iniciar Máquina Virtual")
        self.btn_start.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.start_installation)
        self.btn_start.setVisible(False)

        self.update_firmware_options_visibility()
        # No hacer diagnósticos pesados al arrancar. La ventana debe aparecer
        # inmediatamente; las comprobaciones completas se ejecutan al pulsar
        # "Comprobar dependencias" o cuando son realmente necesarias al iniciar una VM.
        self.refresh_boot_order_choices()
        self._set_dependency_status_unchecked()

        # La consola de progreso permanece fuera de Configuración para no consumir
        # espacio dentro del formulario. Se muestra en la zona inferior del administrador.

        self.setStyleSheet(APP_QSS)

        self._vm_status_timer = QTimer(self)
        self._vm_status_timer.timeout.connect(self.refresh_vm_runtime_status)
        self._vm_status_timer.start(1500)

        # Atajos de teclado globales.
        try:
            from PyQt6.QtGui import QShortcut as _QSC, QKeySequence as _QKS
            # Ctrl+M → menú de Medios (CD/DVD, USB).
            self._shortcut_media = _QSC(_QKS("Ctrl+M"), self)
            self._shortcut_media.activated.connect(self._show_media_menu_at_cursor)
            # Ctrl+R → reconectar el widget VNC.
            self._shortcut_vnc_reconnect = _QSC(_QKS("Ctrl+R"), self)
            self._shortcut_vnc_reconnect.activated.connect(self._manual_refresh_vnc)
            # Ctrl+Alt+C → alternar entre Consola Gráfica y la anterior.
            self._shortcut_console_toggle = _QSC(_QKS("Ctrl+Alt+C"), self)
            self._shortcut_console_toggle.activated.connect(self._toggle_console_tab)
        except Exception as _sc_err:
            try:
                print(f"[AVISO] No se pudieron registrar los atajos: {_sc_err}")
            except Exception:
                pass
            self._shortcut_media = None
            self._shortcut_vnc_reconnect = None
        self._live_integration_timer = QTimer(self)
        self._live_integration_timer.timeout.connect(self._refresh_live_integration_status)
        self._live_integration_timer.start(6000)
        # Liberar el teclado X11 si cerramos la app con el foco en el VNC.
        try:
            app = QApplication.instance()
            if app is not None and hasattr(self, "_release_vnc_keyboard_on_close"):
                app.aboutToQuit.connect(self._release_vnc_keyboard_on_close)
        except Exception:
            pass
        # Si la Consola Gráfica no está disponible incluso tras el
        # bootstrap automático, decírselo al usuario en la consola de
        # progreso (con el motivo exacto), en vez de ocultar la
        # pestaña en silencio.
        if not _HAS_VNC_WIDGET and _VNC_IMPORT_ERROR is not None:
            self.log_message(
                "[AVISO] La Consola Gráfica no está disponible. Motivo: "
                f"{_VNC_IMPORT_ERROR}. Ejecuta ./run.sh o ./setup_console.sh "
                "para reintentar la instalación."
            )
        self.refresh_vm_list()
        self._update_manager_details()

    def _vm_is_selected(self):
        return bool(self.current_vm_dir and os.path.isdir(self.current_vm_dir))

    def _selected_disk_path(self):
        if not self._vm_is_selected():
            return None
        vm_dir = self.current_vm_dir
        cfg = os.path.join(vm_dir, "vm_config.ini")
        if os.path.isfile(cfg):
            try:
                data = load_vm_config(vm_dir)
                ext = data.get("disk_ext", "qcow2")
                path = os.path.join(vm_dir, f"vm_disk.{ext}")
                if os.path.isfile(path):
                    return path
            except Exception:
                pass
        for name in os.listdir(vm_dir):
            if name.startswith("vm_disk."):
                return os.path.join(vm_dir, name)
        return None

    def _filter_vm_list(self, text):
        """Oculta en la lista lateral las VMs cuyo nombre no calza con el
        texto del buscador de la barra superior."""
        text = (text or "").strip().lower()
        for i in range(self.vm_list.count()):
            item = self.vm_list.item(i)
            name = self._vm_name_from_list_text(item.text())
            item.setHidden(bool(text) and text not in name.lower())

    def _show_selectable_error(self, title, message):
        """Muestra errores técnicos en un cuadro cuyo texto puede seleccionarse y copiarse."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(820, 420)
        layout = QVBoxLayout(dlg)
        label = QLabel("Puedes seleccionar y copiar el texto del error:")
        layout.addWidget(label)
        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setPlainText(str(message))
        edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        layout.addWidget(edit, 1)
        buttons = QHBoxLayout()
        copy_btn = QPushButton("Copiar")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(edit.toPlainText()))
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dlg.accept)
        buttons.addWidget(copy_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)
        dlg.exec()





    def closeEvent(self, event):
        # Garantiza que el teclado X11 quede libre aunque el cierre se
        # produzca por la X de la ventana y no por QApplication.quit().
        try:
            if hasattr(self, "_release_vnc_keyboard_on_close"):
                self._release_vnc_keyboard_on_close()
        except Exception:
            pass
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("MaquinaVirtual")
    app.setApplicationName("VirtualMachineManagerApp")
    prewarm_host_capabilities()  # sondas de GPU/QEMU en segundo plano

    def _launch_main_window():
        window = VirtualMachineManagerApp()
        window.show()
        app._main_window_ref = window  # evita que el garbage collector la recoja

    if not os.path.isdir(os.path.join(os.getcwd(), "OSX-KVM")):
        wait_msg = QMessageBox()
        wait_msg.setWindowTitle("Preparando OSX-KVM")
        wait_msg.setText("No se encontró la carpeta 'OSX-KVM'.\nDescargando desde GitHub, por favor espera...")
        wait_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        wait_msg.show()

        # La descarga corre en un hilo real (no bloquea el hilo principal), para
        # que el bucle de eventos de Qt siga repintando la ventana con
        # normalidad durante todo el proceso. Antes esto se hacía de forma
        # síncrona con un solo processEvents() al inicio: la ventana quedaba
        # congelada mientras duraba la descarga, y cerrarla justo antes de
        # crear la ventana principal parece haber sido la causa del
        # "Violación de segmento" reportado la primera vez que se ejecuta.
        download_result = {}

        def _do_download():
            try:
                ensure_osx_kvm_present(print)
            except Exception as e:
                download_result["error"] = e

        download_thread = threading.Thread(target=_do_download, daemon=True)
        download_thread.start()

        def _check_download_done():
            if download_thread.is_alive():
                QTimer.singleShot(150, _check_download_done)
                return
            wait_msg.close()
            wait_msg.deleteLater()
            if "error" in download_result:
                QMessageBox.critical(
                    None, "Error al descargar OSX-KVM",
                    f"No se pudo descargar/descomprimir OSX-KVM automáticamente: {download_result['error']}\n\n"
                    "Puedes clonarlo manualmente con:\n"
                    "git clone https://github.com/kholia/OSX-KVM.git"
                )
            _launch_main_window()

        QTimer.singleShot(150, _check_download_done)
    else:
        _launch_main_window()

    sys.exit(app.exec())
