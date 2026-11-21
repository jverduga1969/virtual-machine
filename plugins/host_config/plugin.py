import os
import platform
import subprocess
import shutil
import glob
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QComboBox, QCheckBox, QLineEdit,
    QFormLayout, QGroupBox, QMessageBox, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt
from core.plugin_base import PluginBase
from core.i18n import available_languages, install as install_translations, translate_widgets
from core.theme import DEFAULT_THEME, apply_theme
from services import host_passthrough
from services.host_diagnostics import (
    HostDiagnostics, OVMF_LINUX_DIRS, OVMF_SECBOOT_CODE_PATTERNS, OVMF_VARS_PATTERNS,
)
from services.osx_kvm_updater import OSXKVMUpdater

class Plugin(PluginBase):
    name = "HostConfig"
    version = "1.1.0"  # Subimos la versión
    description = "Configuración general y de diagnóstico del host."

    def __init__(self, app):
        super().__init__(app)
        self.diag = HostDiagnostics()
        self.general_pages_added = False
        self._diag_start_index = 0  # índice fijo donde empiezan las pestañas de diagnóstico

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
        saved_theme = self.app.settings.value("ui/theme", DEFAULT_THEME)
        self.combo_theme.setCurrentText(saved_theme)
        self.combo_theme.currentTextChanged.connect(self._on_theme_changed)
        form_theme.addRow("Tema de la aplicación:", self.combo_theme)
        layout_app.addWidget(group_theme)

        group_lang = QGroupBox("Idioma")
        form_lang = QFormLayout(group_lang)
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(available_languages())
        saved_lang = self.app.settings.value("ui/language", "Español")
        self.combo_lang.setCurrentText(saved_lang)
        self.combo_lang.currentTextChanged.connect(self._on_lang_changed)
        form_lang.addRow("Selecciona el idioma:", self.combo_lang)
        form_lang.addRow(QLabel("El idioma se aplica al instante a toda la aplicación."))
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

        # 5. Rutas de almacenamiento (VMs, ISOs, Biblioteca de medios)
        page_paths = QWidget()
        layout_paths = QVBoxLayout(page_paths)
        group_paths = QGroupBox("Rutas de almacenamiento de la aplicación")
        form_paths = QFormLayout(group_paths)

        def _browse(field):
            d = QFileDialog.getExistingDirectory(self.app.parent(), "Seleccionar carpeta", field.text())
            if d:
                field.setText(d)

        self.e_base_dir = QLineEdit()
        self.e_base_dir.setPlaceholderText("Ej: /home/usuario/.local/share/virtual-machine")
        self.e_base_dir.setToolTip("Carpeta raíz donde se guardan VMs, ISOs y la biblioteca de medios.")
        row_base = QHBoxLayout(); row_base.addWidget(self.e_base_dir)
        btn_base = QPushButton("📁"); btn_base.clicked.connect(lambda: _browse(self.e_base_dir))
        row_base.addWidget(btn_base)
        form_paths.addRow("Directorio base de datos:", row_base)

        self.e_vms_dir = QLineEdit()
        self.e_vms_dir.setPlaceholderText("Ej: /home/usuario/.local/share/virtual-machine/vms")
        self.e_vms_dir.setToolTip("Carpeta donde se almacenan los archivos de disco y configuración de las VMs.")
        row_vms = QHBoxLayout(); row_vms.addWidget(self.e_vms_dir)
        btn_vms = QPushButton("📁"); btn_vms.clicked.connect(lambda: _browse(self.e_vms_dir))
        row_vms.addWidget(btn_vms)
        form_paths.addRow("Directorio de VMs:", row_vms)

        self.e_isos_dir = QLineEdit()
        self.e_isos_dir.setPlaceholderText("Ej: /home/usuario/.local/share/virtual-machine/isos")
        self.e_isos_dir.setToolTip("Carpeta donde se descargan y guardan las imágenes ISO.")
        row_isos = QHBoxLayout(); row_isos.addWidget(self.e_isos_dir)
        btn_isos = QPushButton("📁"); btn_isos.clicked.connect(lambda: _browse(self.e_isos_dir))
        row_isos.addWidget(btn_isos)
        form_paths.addRow("Directorio de ISOs:", row_isos)

        self.e_media_dir = QLineEdit()
        self.e_media_dir.setPlaceholderText("Ej: /home/usuario/.local/share/virtual-machine/MediaLibrary")
        self.e_media_dir.setToolTip("Carpeta de la biblioteca central de medios (ISOs, discos QCOW2, etc.).")
        row_media = QHBoxLayout(); row_media.addWidget(self.e_media_dir)
        btn_media = QPushButton("📁"); btn_media.clicked.connect(lambda: _browse(self.e_media_dir))
        row_media.addWidget(btn_media)
        form_paths.addRow("Biblioteca de medios:", row_media)

        self.e_qemu_dir = QLineEdit()
        self.e_qemu_dir.setPlaceholderText(r"Ej: C:\Program Files\qemu")
        self.e_qemu_dir.setToolTip(
            "Carpeta que contiene qemu-img.exe y qemu-system-x86_64.exe. "
            "Se usa en Windows cuando QEMU no está en el PATH.")
        row_qemu = QHBoxLayout(); row_qemu.addWidget(self.e_qemu_dir)
        btn_qemu = QPushButton("📁"); btn_qemu.clicked.connect(lambda: _browse(self.e_qemu_dir))
        row_qemu.addWidget(btn_qemu)
        form_paths.addRow("Directorio de QEMU (qemu-img.exe):", row_qemu)

        btn_save_paths = QPushButton("💾 Guardar rutas")
        btn_save_paths.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_save_paths.clicked.connect(self._save_paths)
        form_paths.addRow(btn_save_paths)

        info_paths = QLabel(
            "Las rutas se leen al iniciar la aplicación. Cambiarlas aquí las guarda para el próximo inicio.\n"
            "Si cambias la ubicación mientras la app está abierta, reinicia para que surtan efecto en todos los módulos."
        )
        info_paths.setWordWrap(True)
        info_paths.setStyleSheet("color: #888; font-size: 11px;")
        layout_paths.addWidget(group_paths)
        layout_paths.addWidget(info_paths)
        layout_paths.addStretch()

        # Añadir al menú
        items = [
            ("🎨 Apariencia", page_appearance),
            ("🔌 API REST", page_api),
            ("🍎 Soporte macOS", page_macos),
            ("🛠️ Reparar OVMF", page_ovmf),
            ("📁 Rutas de almacenamiento", page_paths),
        ]
        for name, widget in items:
            self.list_menu.addItem(QListWidgetItem(name))
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            self.stack.addWidget(scroll)

        self._load_paths()
        self.general_pages_added = True
        # Guardar cuántas páginas generales hay para que refresh_diagnostics
        # siempre limpie desde el índice correcto, sin importar cuántas veces se llame.
        self._diag_start_index = self.list_menu.count()

    # ==========================================
    # RUTAS DE ALMACENAMIENTO
    # ==========================================
    def _load_paths(self):
        settings = self.app.settings
        default_base = str(Path.home() / ".local" / "share" / "virtual-machine")
        base = settings.value("paths/base_dir", default_base)
        vms = settings.value("paths/vms_dir", str(Path(base) / "vms"))
        isos = settings.value("paths/isos_dir", str(Path(base) / "isos"))
        media = settings.value("paths/media_dir", str(Path(base) / "MediaLibrary"))
        qemu = settings.value("paths/qemu_dir", "")
        self.e_base_dir.setText(str(base))
        self.e_vms_dir.setText(str(vms))
        self.e_isos_dir.setText(str(isos))
        self.e_media_dir.setText(str(media))
        self.e_qemu_dir.setText(str(qemu))

    def _save_paths(self):
        base = self.e_base_dir.text().strip()
        vms = self.e_vms_dir.text().strip()
        isos = self.e_isos_dir.text().strip()
        media = self.e_media_dir.text().strip()
        qemu = self.e_qemu_dir.text().strip()
        if not base or not vms or not isos or not media:
            QMessageBox.warning(self.app.parent(), "Error", "Todas las rutas son obligatorias.")
            return
        settings = self.app.settings
        settings.setValue("paths/base_dir", base)
        settings.setValue("paths/vms_dir", vms)
        settings.setValue("paths/isos_dir", isos)
        settings.setValue("paths/media_dir", media)
        settings.setValue("paths/qemu_dir", qemu)
        # Que surta efecto sin reiniciar.
        from services.qemu_paths import set_qemu_dir
        set_qemu_dir(qemu)
        QMessageBox.information(
            self.app.parent(), "Guardado",
            "Rutas guardadas.\nReinicia la aplicación para que todos los módulos usen las nuevas ubicaciones."
        )

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
        # Misma lista que usa el diagnóstico y VMRunner._find_ovmf().
        system_dirs = list(OVMF_LINUX_DIRS)

        project_root = Path(__file__).parent.parent.parent
        osx_dir = project_root / "OSX-KVM"
        osx_dir.mkdir(exist_ok=True)
        system_dirs.append(str(osx_dir))

        code_src = None
        vars_src = None

        for d in system_dirs:
            if not os.path.isdir(d): continue
            # CODE de Secure Boot (incluye los .bin de openSUSE).
            if not code_src:
                for pattern in OVMF_SECBOOT_CODE_PATTERNS:
                    candidatos = sorted(glob.glob(os.path.join(d, pattern)))
                    if candidatos:
                        code_src = candidatos[0]
                        break
            # VARS normal: compatible con Secure Boot.
            if not vars_src:
                for pattern in OVMF_VARS_PATTERNS:
                    candidatos = sorted(glob.glob(os.path.join(d, pattern)))
                    if candidatos:
                        vars_src = candidatos[0]
                        break
            if code_src and vars_src: break

        if not code_src:
            self.lbl_ovmf_status.setText("❌ No se encontró OVMF_CODE de Secure Boot. Instala 'ovmf', 'edk2-ovmf' o 'qemu-ovmf-x86_64'.")
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
        start_index = self._diag_start_index  # siempre el mismo valor fijo

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

        icons = {"Virtualización": "🖥️", "Python": "🐍", "Consola": "🌐", "Compartición": "📂", "Passthrough": "🔌"}

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
                "Rutas de almacenamiento" in title
            )
            self.btn_refresh.setVisible(not is_general)
            self.btn_repair.setVisible(not is_general)

    def _on_theme_changed(self, theme):
        self.app.settings.setValue("ui/theme", theme)
        apply_theme(theme)  # misma implementación que usa main.py

    def _on_lang_changed(self, lang):
        self.app.settings.setValue("ui/language", lang)
        install_translations(self.app.settings)
        ventana = self.app.parent()
        if ventana is not None:
            translate_widgets(ventana)

    def _run_postinstall(self):
        # Resolver desde el paquete, no desde el directorio de trabajo: el
        # .desktop o el instalador pueden lanzar la app desde cualquier cwd.
        if platform.system() == "Windows":
            self._run_postinstall_windows()
            return

        script_path = Path(__file__).resolve().parents[2] / "scripts" / "postinstall.sh"
        if not script_path.is_file() and getattr(sys, "frozen", False):
            script_path = Path(getattr(sys, "_MEIPASS", ".")) / "scripts" / "postinstall.sh"
        if not script_path.is_file():
            QMessageBox.critical(self.app.parent(), "Error", f"No se encontró {script_path}")
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

    def _scripts_dir_windows(self) -> Path:
        """Directorio con los scripts del paquete (o del repo al depurar)."""
        if getattr(sys, "frozen", False):
            candidato = Path(getattr(sys, "_MEIPASS", ".")) / "scripts"
            if (candidato / "postinstall.ps1").is_file():
                return candidato
        return Path(__file__).resolve().parents[2] / "scripts"

    def _run_postinstall_windows(self):
        """Eleva con UAC y espera a que termine el reparador de Windows."""
        script_path = self._scripts_dir_windows() / "postinstall.ps1"
        if not script_path.is_file():
            QMessageBox.critical(self.app.parent(), "Error",
                                 "No se encontró scripts/postinstall.ps1")
            return

        # Start-Process -Verb RunAs muestra el prompt de UAC aunque la app se
        # haya iniciado como usuario normal. -Wait permite mostrar el resultado.
        comando = (
            "Start-Process -FilePath 'powershell.exe' "
            "-ArgumentList '-NoProfile','-ExecutionPolicy','Bypass',"
            f"'-File','\"{script_path}\"' "
            "-Verb RunAs -Wait; "
            "Write-Host ''; Write-Host 'Pulsa ENTER para cerrar...'; "
            "$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
        )
        try:
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-Command", comando],
                shell=False, cwd=str(script_path.parent),
            )
            QMessageBox.information(
                self.app.parent(), "Reparación iniciada",
                "Se ha lanzado el reparador con permisos de administrador.")
        except Exception as e:
            QMessageBox.critical(self.app.parent(), "Error", str(e))