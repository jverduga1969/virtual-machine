import os
import subprocess
import shutil
import glob
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QStackedWidget, QComboBox, QCheckBox, QLineEdit,
    QFormLayout, QGroupBox, QApplication, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSettings
from core.plugin_base import PluginBase
from services import host_passthrough
from services.host_diagnostics import HostDiagnostics
from services.osx_kvm_updater import OSXKVMUpdater
from ui_widgets.os_update_dialog import OSUpdateDialog  # <-- IMPORT AÑADIDO

class Plugin(PluginBase):
    name = "HostConfig"
    version = "1.1.0"  # Subimos la versión
    description = "Configuración general y de diagnóstico del host."

    def __init__(self, app):
        super().__init__(app)
        self.diag = HostDiagnostics()
        self.general_pages_added = False

    def get_tabs(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panel lateral
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setAutoFillBackground(True)
        sidebar.setStyleSheet("border-right: 1px solid palette(mid);")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)

        self.list_menu = QListWidget()
        self.list_menu.setStyleSheet('''
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { padding: 10px; }
            QListWidget::item:selected { background-color: #2e7d32; color: white; }
        ''')
        self.list_menu.currentRowChanged.connect(self._on_menu_changed)
        sidebar_layout.addWidget(self.list_menu)
        main_layout.addWidget(sidebar)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_title = QLabel("")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        right_layout.addWidget(self.lbl_title)
        
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)
        
        # Botones de acción inferiores (solo visibles en diagnóstico)
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Comprobar de nuevo")
        self.btn_refresh.setStyleSheet("background-color: #1976d2; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_refresh.clicked.connect(self.refresh_diagnostics)
        
        self.btn_repair = QPushButton("🛠️ Reparar lo que falte")
        self.btn_repair.setStyleSheet("background-color: #f9a825; color: black; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_repair.clicked.connect(self._run_postinstall)
        
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_repair)
        right_layout.addLayout(btn_layout)
        
        main_layout.addWidget(right_panel)

        self._build_pages()
        return [("Configuración Host", main_widget)]

    def _build_pages(self):
        self._add_general_pages()
        self.refresh_diagnostics()
        if self.list_menu.count() > 0:
            self.list_menu.setCurrentRow(0)

    def _add_general_pages(self):
        if self.general_pages_added: return

        # 1. Apariencia
        page_appearance = QWidget()
        layout_app = QVBoxLayout(page_appearance)
        
        group_theme = QGroupBox("Tema")
        form_theme = QFormLayout(group_theme)
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Sistema (predeterminado)", "Claro", "Oscuro"])
        saved_theme = QSettings().value("ui/theme", "Sistema (predeterminado)")
        self.combo_theme.setCurrentText(saved_theme)
        self.combo_theme.currentTextChanged.connect(self._on_theme_changed)
        form_theme.addRow("Tema de la aplicación:", self.combo_theme)
        layout_app.addWidget(group_theme)
        
        group_lang = QGroupBox("Idioma")
        form_lang = QFormLayout(group_lang)
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Español", "English", "Português (BR)", "Deutsch", "Français", "Italiano"])
        saved_lang = QSettings().value("ui/language", "Español")
        self.combo_lang.setCurrentText(saved_lang)
        self.combo_lang.currentTextChanged.connect(self._on_lang_changed)
        form_lang.addRow("Selecciona el idioma:", self.combo_lang)
        form_lang.addRow(QLabel("Al cambiar el idioma, la aplicación ofrecerá reiniciar para aplicar la traducción."))
        layout_app.addWidget(group_lang)
        layout_app.addStretch()

        # 2. API REST
        page_api = QWidget()
        layout_api = QVBoxLayout(page_api)
        group_api = QGroupBox("API REST local")
        form_api = QFormLayout(group_api)
        form_api.addRow(QLabel("Expone una API HTTP mínima para controlar VMs desde scripts."))
        self.cb_api = QCheckBox("Activar API REST local")
        form_api.addRow(self.cb_api)
        self.e_port = QLineEdit("8730")
        form_api.addRow("Puerto:", self.e_port)
        layout_api.addWidget(group_api)
        layout_api.addStretch()

        # 3. Soporte macOS (OSX-KVM)
        page_macos = QWidget()
        layout_macos = QVBoxLayout(page_macos)
        group_macos = QGroupBox("Soporte macOS (OSX-KVM)")
        layout_group = QVBoxLayout(group_macos)
        
        updater = OSXKVMUpdater(Path(__file__).parent.parent.parent)
        
        self.lbl_macos_version = QLabel(f"Versión actual: {updater.get_current_version()}")
        layout_group.addWidget(self.lbl_macos_version)
        
        btn_update_macos = QPushButton("🔄 Actualizar OSX-KVM desde GitHub")
        btn_update_macos.setStyleSheet("background-color: #1976d2; color: white; padding: 5px;")
        btn_update_macos.clicked.connect(self._update_macos)
        layout_group.addWidget(btn_update_macos)
        
        info_macos = QLabel("OSX-KVM se usa para el arranque de macOS. Se recomienda mantenerlo actualizado para compatibilidad con las últimas versiones de OpenCore.")
        info_macos.setWordWrap(True)
        info_macos.setStyleSheet("color: #888; font-size: 11px;")
        layout_group.addWidget(info_macos)
        
        layout_macos.addWidget(group_macos)
        layout_macos.addStretch()

        # 4. Reparar OVMF Secure Boot
        page_ovmf = QWidget()
        layout_ovmf = QVBoxLayout(page_ovmf)
        group_ovmf = QGroupBox("OVMF Secure Boot")
        lay_ovmf = QVBoxLayout(group_ovmf)
        
        info_ovmf = QLabel("Arch Linux incluye OVMF_CODE.secboot.4m.fd pero no el VARS.secboot. Para Windows 11, basta con usar el CODE secboot del sistema + el VARS normal. Usa este botón para copiar los archivos a la carpeta OSX-KVM/.")
        info_ovmf.setWordWrap(True)
        info_ovmf.setStyleSheet("color: #888; font-size: 11px;")
        lay_ovmf.addWidget(info_ovmf)
        
        btn_fix_ovmf = QPushButton("🛠️ Reparar OVMF Secure Boot")
        btn_fix_ovmf.setStyleSheet("background-color: #f9a825; color: black; padding: 8px; font-weight: bold;")
        btn_fix_ovmf.clicked.connect(self._fix_ovmf_secure_boot)
        lay_ovmf.addWidget(btn_fix_ovmf)
        
        self.lbl_ovmf_status = QLabel("")
        self.lbl_ovmf_status.setStyleSheet("color: #888; font-size: 11px; padding-top: 5px;")
        self.lbl_ovmf_status.setWordWrap(True)
        lay_ovmf.addWidget(self.lbl_ovmf_status)
        
        layout_ovmf.addWidget(group_ovmf)
        layout_ovmf.addStretch()

        # 5. Actualizar Catálogo de SO (NUEVO)
        page_os_updater = QWidget()
        layout_os_up = QVBoxLayout(page_os_updater)
        group_os = QGroupBox("Catálogo de versiones de SO")
        lay_os = QVBoxLayout(group_os)
        
        info_os = QLabel(
            "Consulta los servidores oficiales de Ubuntu, Debian, Fedora, Linux Mint y Pop!_OS "
            "para obtener las últimas versiones disponibles.\n\n"
            "Si no actualizas este catálogo, la aplicación usará una lista de versiones básica predefinida."
        )
        info_os.setWordWrap(True)
        info_os.setStyleSheet("color: #888; font-size: 11px;")
        lay_os.addWidget(info_os)
        
        self.btn_update_os = QPushButton("🔄 Actualizar versiones de SO")
        self.btn_update_os.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_update_os.clicked.connect(self._on_update_os)
        lay_os.addWidget(self.btn_update_os)
        
        layout_os_up.addWidget(group_os)
        layout_os_up.addStretch()

        # Añadir al menú
        items = [
            ("🎨 Apariencia", page_appearance),
            ("🔌 API REST", page_api),
            ("🍎 Soporte macOS", page_macos),
            ("🛠️ Reparar OVMF", page_ovmf),
            ("📋 Catálogo de SO", page_os_updater),  # <-- NUEVO ITEM
        ]
        for name, widget in items:
            self.list_menu.addItem(QListWidgetItem(name))
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            self.stack.addWidget(scroll)
        
        self.general_pages_added = True

    # ==========================================
    # NUEVA FUNCIÓN PARA EL CATÁLOGO DE SO
    # ==========================================
    def _on_update_os(self):
        dlg = OSUpdateDialog(self.app.parent())
        dlg.exec()

    # ==========================================
    # FUNCIONES EXISTENTES
    # ==========================================
    def _update_macos(self):
        updater = OSXKVMUpdater(Path(__file__).parent.parent.parent)
        success, msg = updater.update_from_git()
        if success:
            self.lbl_macos_version.setText(f"Versión actual: {updater.get_current_version()}")
            QMessageBox.information(self.app.parent(), "Actualizado", msg)
        else:
            QMessageBox.critical(self.app.parent(), "Error", msg)

    def _fix_ovmf_secure_boot(self):
        system_dirs = [
            "/usr/share/edk2/x64/",
            "/usr/share/OVMF/",
            "/usr/share/edk2/ovmf/",
            "/usr/share/edk2-ovmf/x64/",
        ]
        
        project_root = Path(__file__).parent.parent.parent
        osx_dir = project_root / "OSX-KVM"
        osx_dir.mkdir(exist_ok=True)
        
        code_src = None
        vars_src = None
        
        for d in system_dirs:
            if not os.path.exists(d): continue
            # Buscar CODE secboot
            code_candidates = glob.glob(os.path.join(d, "OVMF_CODE*.secboot*.fd"))
            if code_candidates:
                code_src = code_candidates[0]
            # Buscar VARS normal (compatible con secboot)
            vars_candidates = glob.glob(os.path.join(d, "OVMF_VARS*.4m.fd")) or glob.glob(os.path.join(d, "OVMF_VARS*.fd"))
            if vars_candidates:
                vars_src = vars_candidates[0]
            if code_src and vars_src: break
        
        if not code_src:
            self.lbl_ovmf_status.setText("❌ No se encontró OVMF_CODE.secboot en el sistema. Instala 'edk2-ovmf'.")
            self.lbl_ovmf_status.setStyleSheet("color: #c62828; font-size: 11px;")
            return
        
        if not vars_src:
            self.lbl_ovmf_status.setText("❌ No se encontró OVMF_VARS en el sistema.")
            self.lbl_ovmf_status.setStyleSheet("color: #c62828; font-size: 11px;")
            return
        
        try:
            dest_code = osx_dir / "OVMF_CODE.secboot.4m.fd"
            dest_vars = osx_dir / "OVMF_VARS.secboot.4m.fd"
            
            # Borrar vacíos si existen
            for f in (dest_code, dest_vars):
                if f.exists() and f.stat().st_size == 0:
                    f.unlink()
            
            shutil.copy2(code_src, dest_code)
            shutil.copy2(vars_src, dest_vars)
            
            self.lbl_ovmf_status.setText(
                f"✅ Archivos copiados:\n"
                f"  - CODE: {os.path.basename(code_src)} ({os.path.getsize(code_src) // 1024} KB)\n"
                f"  - VARS: {os.path.basename(vars_src)} ({os.path.getsize(vars_src) // 1024} KB)\n"
                f"  (El VARS normal es compatible con Secure Boot)"
            )
            self.lbl_ovmf_status.setStyleSheet("color: #2e7d32; font-size: 11px;")
            self.refresh_diagnostics()
        except Exception as e:
            self.lbl_ovmf_status.setText(f"❌ Error copiando: {e}")
            self.lbl_ovmf_status.setStyleSheet("color: #c62828; font-size: 11px;")

    def refresh_diagnostics(self):
        start_index = self.list_menu.count()
        
        # Limpiar
        while self.stack.count() > start_index:
            widget = self.stack.widget(start_index)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        while self.list_menu.count() > start_index:
            self.list_menu.takeItem(start_index)

        results = self.diag.run_all()
        categories = {}
        for r in results:
            categories.setdefault(r["cat"], []).append(r)

        icons = {"Virtualización": "🖥️", "Python": "🐍", "Consola": "🌐", "Compartición": "📂", "Passthrough": "🔌", "Modo Kiosco": "🖥️"}

        for cat_name, items in categories.items():
            icon = icons.get(cat_name, "📁")
            self.list_menu.addItem(QListWidgetItem(f"{icon} {cat_name}"))
            scroll_w = QWidget()
            v_layout = QVBoxLayout(scroll_w)
            
            for check in items:
                row = QWidget()
                h_layout = QHBoxLayout(row)
                h_layout.setContentsMargins(0, 5, 0, 5)
                
                st_icon = "✅" if check["st"] == "ok" else ("⚠️" if check["st"] == "warn" else "❌")
                color = "#2e7d32" if check["st"] == "ok" else ("#f9a825" if check["st"] == "warn" else "#c62828")
                
                lbl_icon = QLabel(st_icon)
                lbl_name = QLabel(f"<b>{check['name']}</b>")
                lbl_name.setFixedWidth(200)
                lbl_desc = QLabel(check["desc"])
                lbl_desc.setStyleSheet(f"color: {color};")
                
                h_layout.addWidget(lbl_icon); h_layout.addWidget(lbl_name); h_layout.addWidget(lbl_desc); h_layout.addStretch()
                v_layout.addWidget(row)
            v_layout.addStretch()
            self.stack.addWidget(scroll_w)

    def _on_menu_changed(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
            title = self.list_menu.item(index).text().split(" ", 1)[-1]
            self.lbl_title.setText(title)
            is_general = (
                "Apariencia" in title or 
                "API REST" in title or 
                "Soporte macOS" in title or 
                "Reparar OVMF" in title or
                "Catálogo de SO" in title  # <-- Añadido para ocultar los botones de diagnóstico
            )
            self.btn_refresh.setVisible(not is_general)
            self.btn_repair.setVisible(not is_general)

    def _on_theme_changed(self, theme):
        QSettings().setValue("ui/theme", theme)
        app = QApplication.instance()
        if theme == "Oscuro":
            app.setStyleSheet("QWidget { background-color: #2b2b2b; color: white; } QLineEdit, QComboBox { background-color: #3b3b3b; color: white; }")
        elif theme == "Claro":
            app.setStyleSheet("QWidget { background-color: #f0f0f0; color: black; }")
        else:
            app.setStyleSheet("")

    def _on_lang_changed(self, lang):
        QSettings().setValue("ui/language", lang)

    def _run_postinstall(self):
        script_path = Path("scripts/postinstall.sh")
        if not script_path.exists():
            QMessageBox.critical(self.app.parent(), "Error", f"No se encontró {script_path.absolute()}")
            return
        if not shutil.which("pkexec"):
            QMessageBox.critical(self.app.parent(), "Error", "No se encontró 'pkexec'.")
            return
        try:
            os.chmod(script_path, 0o755)
            subprocess.Popen(["pkexec", "bash", str(script_path.absolute())])
            QMessageBox.information(self.app.parent(), "Reparación iniciada", "Se ha lanzado el script de reparación.")
        except Exception as e:
            QMessageBox.critical(self.app.parent(), "Error", str(e))