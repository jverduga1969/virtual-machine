# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""quick_create_dialog.py — dialogo del Modo Rapido.

Marcador: quick_create_v1_dialog_v3 (con Android)
"""
import os

from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QRadioButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget,
)

import vm_profiles


class _VersionsSignals(QObject):
    finished = pyqtSignal(str, list)
    failed   = pyqtSignal(str, str)


class _VersionsLoader(QRunnable):
    def __init__(self, distro):
        super().__init__()
        self.distro = distro
        self.signals = _VersionsSignals()

    def run(self):
        try:
            import iso_versions
            vers = iso_versions.list_distro_versions(self.distro)
            self.signals.finished.emit(self.distro, vers)
        except Exception as e:
            self.signals.failed.emit(self.distro, str(e))


class _ProfileCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, profile_id, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self._selected = False
        self._disabled_reason = None
        prof = vm_profiles.PROFILES[profile_id]

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(135, 105)
        self.setMaximumWidth(180)

        v = QVBoxLayout(self)
        v.setContentsMargins(6, 8, 6, 8)
        v.setSpacing(2)

        self.icon_label = QLabel(prof["icon"])
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont(); f.setPointSize(22)
        self.icon_label.setFont(f)

        self.name_label = QLabel(prof["label"])
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nf = QFont(); nf.setBold(True); nf.setPointSize(9)
        self.name_label.setFont(nf)
        self.name_label.setWordWrap(True)

        self.summary_label = QLabel("")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setStyleSheet("color: #888; font-size: 10px;")

        v.addWidget(self.icon_label)
        v.addWidget(self.name_label)
        v.addWidget(self.summary_label)
        v.addStretch(1)
        self._update_style()

    def mousePressEvent(self, event):
        if self._disabled_reason is None:
            self.clicked.emit(self.profile_id)
        else:
            QMessageBox.information(self, "Perfil no disponible",
                                    self._disabled_reason)

    def set_selected(self, selected):
        self._selected = bool(selected)
        self._update_style()

    def is_selected(self):
        return self._selected

    def set_disabled_reason(self, reason):
        self._disabled_reason = reason
        self.setToolTip(reason or "")
        self._update_style()

    def set_summary(self, text):
        self.summary_label.setText(text or "")

    def _update_style(self):
        if self._disabled_reason is not None:
            self.setStyleSheet(
                "QFrame { background: #f0f0f0; border: 1px solid #ccc;"
                " border-radius: 6px; color: #999; }")
            self.icon_label.setStyleSheet("color: #bbb;")
            self.name_label.setStyleSheet("color: #999;")
        elif self._selected:
            self.setStyleSheet(
                "QFrame { background: #e3f2fd; border: 2px solid #1976d2;"
                " border-radius: 6px; }")
            self.icon_label.setStyleSheet("")
            self.name_label.setStyleSheet("")
        else:
            self.setStyleSheet(
                "QFrame { background: #fafafa; border: 1px solid #ddd;"
                " border-radius: 6px; }"
                "QFrame:hover { background: #f0f7ff; border: 1px solid #90caf9; }")
            self.icon_label.setStyleSheet("")
            self.name_label.setStyleSheet("")


LINUX_SOS = [
    "Ubuntu", "Debian", "Fedora", "Linux Mint", "openSUSE",
    "Arch Linux", "AlmaLinux", "Rocky Linux", "Pop!_OS", "Manjaro Linux",
]
WINDOWS_SOS = ["Windows 11", "Windows 10"]
ANDROID_SOS = ["Android-x86 / Bliss OS"]


class QuickCreateDialog(QDialog):
    def __init__(self, parent=None, host_ram_mb=8192, host_cores=4,
                 macos_versions=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Crear VM rapida"))
        self.setModal(True)
        self.setMinimumWidth(640)

        self._host_ram_mb = host_ram_mb
        self._host_cores = max(2, host_cores)
        self._host_ram_gb = max(2, host_ram_mb // 1024)
        self._macos_versions = macos_versions or [
            "High Sierra (10.13)", "Mojave (10.14)", "Catalina (10.15)",
            "Big Sur (11.7)", "Monterey (12.6)", "Ventura (13)",
            "Sonoma (14)", "Sequoia (15)", "Tahoe",
        ]

        self._current_profile = vm_profiles.DEFAULT_PROFILE
        self._cards = {}
        self._pending_version_loader = None

        self._build_ui()
        self._on_platform_changed()
        self._on_profile_clicked(vm_profiles.DEFAULT_PROFILE)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        gb_profile = QGroupBox(self.tr("Perfil de uso"))
        h = QHBoxLayout(gb_profile)
        h.setSpacing(8)
        for pid in vm_profiles.all_profile_ids():
            card = _ProfileCard(pid, self)
            card.clicked.connect(self._on_profile_clicked)
            h.addWidget(card)
            self._cards[pid] = card
        h.addStretch(1)
        root.addWidget(gb_profile)

        gb_data = QGroupBox(self.tr("Datos basicos"))
        self.form_basicos = QFormLayout(gb_data)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(self.tr("Mi maquina virtual"))
        self.form_basicos.addRow(self.tr("Nombre:"), self.input_name)

        self.combo_platform = QComboBox()
        self.combo_platform.addItem(self.tr("Linux"),   "linux")
        self.combo_platform.addItem(self.tr("Windows"), "windows")
        self.combo_platform.addItem(self.tr("macOS"),   "macos")
        self.combo_platform.addItem(self.tr("Android"), "android")
        self.form_basicos.addRow(self.tr("Plataforma:"), self.combo_platform)

        self.combo_os = QComboBox()
        self.form_basicos.addRow(self.tr("Sistema operativo:"), self.combo_os)

        self.combo_version = QComboBox()
        self.combo_version.setMinimumWidth(200)
        self.form_basicos.addRow(self.tr("Version:"), self.combo_version)
        root.addWidget(gb_data)

        gb_hw = QGroupBox(self.tr("Hardware"))
        hw = QFormLayout(gb_hw)

        h_cores = QHBoxLayout()
        self.slider_cores = QSlider(Qt.Orientation.Horizontal)
        self.slider_cores.setMinimum(2)
        self.slider_cores.setMaximum(self._host_cores)
        self.slider_cores.setSingleStep(2)
        self.slider_cores.setPageStep(2)
        self.slider_cores.setTickInterval(2)
        self.slider_cores.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_cores.setValue(2)
        self.label_cores_value = QLabel("2 nucleos")
        self.label_cores_value.setStyleSheet("font-weight:bold;")
        self.label_cores_value.setMinimumWidth(90)
        h_cores.addWidget(self.slider_cores, 1)
        h_cores.addWidget(self.label_cores_value)
        w_cores = QWidget(); w_cores.setLayout(h_cores)
        hw.addRow(self.tr("Procesador:"), w_cores)

        h_ram = QHBoxLayout()
        self.slider_ram = QSlider(Qt.Orientation.Horizontal)
        self.slider_ram.setMinimum(2)
        self.slider_ram.setMaximum(self._host_ram_gb)
        self.slider_ram.setSingleStep(2)
        self.slider_ram.setPageStep(2)
        self.slider_ram.setTickInterval(2)
        self.slider_ram.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_ram.setValue(min(4, self._host_ram_gb))
        self.label_ram_value = QLabel(f"{self.slider_ram.value()} GB")
        self.label_ram_value.setStyleSheet("font-weight:bold;")
        self.label_ram_value.setMinimumWidth(70)
        h_ram.addWidget(self.slider_ram, 1)
        h_ram.addWidget(self.label_ram_value)
        w_ram = QWidget(); w_ram.setLayout(h_ram)
        hw.addRow(self.tr("Memoria RAM:"), w_ram)

        self.spin_disk = QSpinBox()
        self.spin_disk.setRange(5, 2000)
        self.spin_disk.setSuffix(" GB")
        hw.addRow(self.tr("Disco duro:"), self.spin_disk)

        self.hint_hw = QLabel("")
        self.hint_hw.setStyleSheet("color: #b71c1c; font-size: 10px;")
        self.hint_hw.setWordWrap(True)
        hw.addRow("", self.hint_hw)

        self.slider_cores.valueChanged.connect(
            lambda v: self.label_cores_value.setText(
                self.tr("{0} nucleos").format(v)))
        self.slider_ram.valueChanged.connect(
            lambda v: self.label_ram_value.setText(f"{v} GB"))

        root.addWidget(gb_hw)

        gb_iso = QGroupBox(self.tr("Medio de instalacion"))
        iso_v = QVBoxLayout(gb_iso)

        self.radio_iso_none = QRadioButton(self.tr("No, la selecciono luego"))
        self.radio_iso_dl   = QRadioButton(self.tr("Descargar automaticamente"))
        self.radio_iso_file = QRadioButton(self.tr("Seleccionar un archivo ISO"))
        self.radio_iso_dl.setChecked(True)

        self.iso_group = QButtonGroup(self)
        for rb in (self.radio_iso_none, self.radio_iso_dl, self.radio_iso_file):
            iso_v.addWidget(rb)
            self.iso_group.addButton(rb)

        self.row_file = QWidget()
        rf = QHBoxLayout(self.row_file)
        rf.setContentsMargins(20, 0, 0, 0)
        self.input_iso_path = QLineEdit()
        self.input_iso_path.setReadOnly(True)
        self.btn_browse_iso = QPushButton(self.tr("Examinar..."))
        self.btn_browse_iso.clicked.connect(self._on_browse_iso)
        self.btn_pick_library = QPushButton(self.tr("Biblioteca"))
        self.btn_pick_library.clicked.connect(self._on_pick_from_library)
        rf.addWidget(self.input_iso_path, 1)
        rf.addWidget(self.btn_browse_iso)
        rf.addWidget(self.btn_pick_library)
        iso_v.addWidget(self.row_file)

        self.hint_iso = QLabel("")
        self.hint_iso.setStyleSheet("color: #666; font-size: 10px;")
        self.hint_iso.setWordWrap(True)
        iso_v.addWidget(self.hint_iso)
        root.addWidget(gb_iso)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            self.tr("Crear ->"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self.tr("Cancelar"))
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.combo_platform.currentIndexChanged.connect(self._on_platform_changed)
        self.combo_os.currentIndexChanged.connect(self._on_os_changed)
        self.radio_iso_dl.toggled.connect(self._on_iso_radio_changed)
        self.radio_iso_none.toggled.connect(self._on_iso_radio_changed)
        self.radio_iso_file.toggled.connect(self._on_iso_radio_changed)
        self._on_iso_radio_changed()

    def _on_profile_clicked(self, profile_id):
        os_type = self.combo_platform.currentData() or "linux"
        if not vm_profiles.is_supported(profile_id, os_type):
            return
        self._current_profile = profile_id
        for pid, card in self._cards.items():
            card.set_selected(pid == profile_id)
        self._apply_profile_values()

    def _apply_profile_values(self):
        os_type = self.combo_platform.currentData() or "linux"
        os_ver = self._current_os_version_label()
        vals = vm_profiles.profile_defaults(
            self._current_profile, os_type, os_ver, self._host_ram_mb)
        if vals is None:
            return
        c = int(vals["cores"])
        if c % 2: c += 1
        c = max(self.slider_cores.minimum(),
                min(self.slider_cores.maximum(), c))
        self.slider_cores.setValue(c)
        want_gb = int(vals["ram"].rstrip("G"))
        if want_gb % 2: want_gb += 1
        want_gb = max(self.slider_ram.minimum(),
                      min(self.slider_ram.maximum(), want_gb))
        self.slider_ram.setValue(want_gb)
        self.spin_disk.setValue(int(vals["disk_gb"]))
        if os_type == "macos":
            self.spin_disk.setValue(128)
            self.spin_disk.setEnabled(False)
        else:
            self.spin_disk.setEnabled(True)
        _raw = int(vals["ram"].rstrip("G"))
        if _raw > self._host_ram_gb:
            self.hint_hw.setText(self.tr(
                "Este perfil recomienda {0} GB y tu host tiene {1} GB. "
                "Se ha bajado al maximo disponible."
            ).format(_raw, self._host_ram_gb))
        else:
            self.hint_hw.setText("")
        self._refresh_card_summaries()

    def _refresh_card_summaries(self):
        os_type = self.combo_platform.currentData() or "linux"
        os_ver = self._current_os_version_label()
        for pid, card in self._cards.items():
            if vm_profiles.is_supported(pid, os_type):
                card.set_disabled_reason(None)
                v = vm_profiles.profile_defaults(pid, os_type, os_ver,
                                                 self._host_ram_mb)
                if v:
                    card.set_summary(f"{v['ram']} · {v['cores']} vCPU · {v['disk_gb']}GB")
            else:
                reason = vm_profiles.reason_unsupported(pid, os_type)
                card.set_disabled_reason(reason)
                card.set_summary("")
                card.set_selected(False)

    def _on_platform_changed(self):
        platform = self.combo_platform.currentData() or "linux"
        self.combo_os.blockSignals(True)
        self.combo_os.clear()
        if platform == "linux":
            for s in LINUX_SOS:
                self.combo_os.addItem(s, s)
        elif platform == "windows":
            for s in WINDOWS_SOS:
                self.combo_os.addItem(s, s)
        elif platform == "macos":
            for s in self._macos_versions:
                self.combo_os.addItem(s, s)
        elif platform == "android":
            for s in ANDROID_SOS:
                self.combo_os.addItem(s, s)
        self.combo_os.blockSignals(False)
        self._on_os_changed()

    def _toggle_version_row(self, visible):
        lbl = self.form_basicos.labelForField(self.combo_version)
        if lbl is not None:
            lbl.setVisible(visible)
        self.combo_version.setVisible(visible)

    def _update_iso_availability(self, platform):
        """En macOS y Android no hay descarga automatica de ISO."""
        no_auto = platform in ("macos", "android")
        self.radio_iso_dl.setEnabled(not no_auto)
        if no_auto:
            self.radio_iso_dl.setToolTip(self.tr(
                "Este SO no tiene descarga automatica. "
                "Selecciona una ISO de tu equipo o de la Biblioteca."))
            if self.radio_iso_dl.isChecked():
                self.radio_iso_none.setChecked(True)
        else:
            self.radio_iso_dl.setToolTip("")

    def _on_os_changed(self):
        platform = self.combo_platform.currentData() or "linux"
        os_name = self.combo_os.currentData() or ""
        self._refresh_card_summaries()
        self._toggle_version_row(platform not in ("macos", "android"))
        self._update_iso_availability(platform)
        if platform == "linux":
            self._load_linux_versions_async(os_name)
        elif platform == "windows":
            self._fill_versions_windows(os_name)
        elif platform == "macos":
            self._fill_versions_macos(os_name)
        elif platform == "android":
            self._fill_versions_android(os_name)
        if not vm_profiles.is_supported(self._current_profile, platform):
            self._on_profile_clicked("general")
        else:
            self._apply_profile_values()

    def _fill_versions_windows(self, os_name):
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItem("Ultima disponible", "")
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(False)
        self.hint_iso.setText(self.tr(
            "Windows se descarga la ultima version retail desde Microsoft."))

    def _fill_versions_macos(self, os_name):
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItem(os_name, os_name)
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(False)
        self.hint_iso.setText(self.tr(
            "macOS descarga el Recovery de Apple al iniciar la VM."))

    def _fill_versions_android(self, os_name):
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItem("N/A", "")
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(False)
        self.hint_iso.setText(self.tr(
            "Android-x86/Bliss OS no tiene descarga automatica. "
            "Usa 'Seleccionar un archivo ISO' o la Biblioteca."))

    def _load_linux_versions_async(self, distro):
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItem(self.tr("Cargando..."), "")
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(False)
        self.hint_iso.setText(self.tr("Consultando versiones disponibles..."))
        loader = _VersionsLoader(distro)
        loader.signals.finished.connect(self._on_versions_loaded)
        loader.signals.failed.connect(self._on_versions_failed)
        self._pending_version_loader = loader
        QThreadPool.globalInstance().start(loader)

    def _on_versions_loaded(self, distro, versions):
        if distro != (self.combo_os.currentData() or ""):
            return
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        if not versions:
            self.combo_version.addItem(self.tr("Ultima disponible"), "")
        else:
            for v in versions:
                self.combo_version.addItem(v["label"], v["id"])
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(bool(versions))
        self.hint_iso.setText(self.tr(
            "La ISO se descargara al pulsar Iniciar VM."))

    def _on_versions_failed(self, distro, err):
        if distro != (self.combo_os.currentData() or ""):
            return
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItem(self.tr("Ultima disponible"), "")
        self.combo_version.blockSignals(False)
        self.combo_version.setEnabled(False)
        self.hint_iso.setText(self.tr(
            "No se pudo consultar el catalogo. Se usara la ultima disponible."))

    def _current_os_version_label(self):
        platform = self.combo_platform.currentData()
        if platform in ("windows", "macos", "android"):
            return self.combo_os.currentData() or ""
        return self.combo_version.currentData() or ""

    def _on_iso_radio_changed(self):
        self.row_file.setVisible(self.radio_iso_file.isChecked())
        if self.radio_iso_dl.isChecked():
            self.hint_iso.setText(self.tr(
                "La ISO se descargara al pulsar Iniciar VM."))
        elif self.radio_iso_none.isChecked():
            self.hint_iso.setText(self.tr(
                "Podras anadir una ISO despues desde Configuracion -> Almacenamiento."))
        elif self.radio_iso_file.isChecked():
            self.hint_iso.setText(self.tr(
                "Selecciona un archivo ISO/IMG/DMG de tu equipo o de la Biblioteca."))

    def _on_browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Seleccionar ISO"),
            os.path.expanduser("~"),
            self.tr("Imagenes de disco (*.iso *.img *.dmg);;Todos los archivos (*)"))
        if path:
            self.input_iso_path.setText(path)

    def _on_pick_from_library(self):
        try:
            from dialogs import MediaPickerDialog
        except Exception:
            try:
                from media_library_mixin import MediaPickerDialog
            except Exception as e:
                QMessageBox.warning(
                    self, self.tr("Biblioteca no disponible"),
                    self.tr("No se pudo abrir la Biblioteca: {0}").format(e))
                return
        try:
            os_type = self.combo_platform.currentData() or ""
            dlg = MediaPickerDialog(
                self, filter_os_type=os_type, filter_media_type="iso")
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            chosen = dlg.chosen()
            if not chosen or not chosen.get("path"):
                return
            self.input_iso_path.setText(chosen["path"])
            self.radio_iso_file.setChecked(True)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Error"),
                self.tr("No se pudo obtener el medio: {0}").format(e))

    # ------------------------------------------------------------------
    # Validacion de nombre duplicado
    # ------------------------------------------------------------------
    def _suggest_alternative(self, name, existing):
        """Sugiere 'nombre-2', 'nombre-3', ... hasta encontrar uno libre."""
        try:
            import vm_config
            base = name
            i = 1
            while i < 1000:
                i += 1
                cand = f"{base}-{i}"
                folder = vm_config.vm_folder_name(cand)
                if (folder not in existing
                        and not os.path.exists(
                            os.path.join(vm_config.BASE_VM_DIR, folder))):
                    return cand
            return f"{base}-nuevo"
        except Exception:
            return f"{name}-2"

    def _check_name_not_taken(self):
        """Comprueba si el nombre ya existe. Si lo esta, ofrece usar
        una alternativa, cambiar o cancelar.

        Devuelve True si el dialogo puede continuar (nombre libre o el
        usuario acepto la alternativa sugerida)."""
        try:
            import vm_config
            raw = self.input_name.text().strip()
            folder = vm_config.vm_folder_name(raw)
            existing = set(vm_config.list_existing_vms())
            taken = (folder in existing
                     or os.path.exists(
                         os.path.join(vm_config.BASE_VM_DIR, folder)))
            if not taken:
                return True
            suggested = self._suggest_alternative(raw, existing)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(self.tr("Nombre en uso"))
            box.setText(self.tr(
                "El nombre '{0}' ya esta en uso por otra VM.").format(raw))
            box.setInformativeText(self.tr(
                "Puedes usar '{0}' o cambiar el nombre.").format(suggested))
            btn_use = box.addButton(
                self.tr("Usar '{0}'").format(suggested),
                QMessageBox.ButtonRole.AcceptRole)
            btn_change = box.addButton(
                self.tr("Cambiar nombre"),
                QMessageBox.ButtonRole.ActionRole)
            box.addButton(
                self.tr("Cancelar"),
                QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_use)
            box.exec()
            clicked = box.clickedButton()
            if clicked is btn_use:
                self.input_name.setText(suggested)
                return True
            if clicked is btn_change:
                self.input_name.setFocus()
                self.input_name.selectAll()
                return False
            return False
        except Exception:
            # Fallback: dejar pasar. _create_from_form volvera a validar.
            return True

    # ------------------------------------------------------------------
    def _on_accept(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr("Nombre requerido"),
                                self.tr("Escribe un nombre para la VM."))
            self.input_name.setFocus()
            return
        if self.radio_iso_file.isChecked() and not self.input_iso_path.text().strip():
            QMessageBox.warning(self, self.tr("ISO requerida"),
                                self.tr("Selecciona un archivo ISO o cambia a otra opcion."))
            return
        # Validar nombre duplicado antes de aceptar.
        if not self._check_name_not_taken():
            return
        self.accept()

    def result_data(self):
        platform = self.combo_platform.currentData() or "linux"
        os_name = self.combo_os.currentData() or ""
        os_version = self._current_os_version_label()
        if self.radio_iso_none.isChecked():
            iso_choice = "none"
            iso_path = ""
        elif self.radio_iso_file.isChecked():
            iso_choice = "none"
            iso_path = self.input_iso_path.text().strip()
        else:
            iso_choice = self.combo_version.currentData() or ""
            iso_path = ""

        # vm_optimizer_v1_dialog: fusionar 'values' + 'advanced' en un
        # dict PLANO. Se mantienen las claves planas que ya consumia el
        # mixin (graphics_mode, graphics_vram, ram, cores, disk_gb) y
        # se anaden las del bloque avanzado. El mixin se encarga de
        # volcarlas a los widgets y de persistirlas en vm_config.ini.
        graphics_mode = "auto"
        graphics_vram = "256M"
        advanced = {}
        try:
            vals = vm_profiles.profile_defaults(
                self._current_profile, platform, os_version,
                self._host_ram_mb)
            if vals:
                graphics_vram = vals.get("vram", "256M")
        except Exception:
            pass
        try:
            adv = vm_profiles.profile_advanced(
                self._current_profile, platform)
            if adv:
                advanced = dict(adv)
                # graphics_mode viaja como clave plana por compatibilidad
                # con el flujo anterior; el resto se anade tal cual.
                graphics_mode = advanced.pop("graphics_mode", "auto")
        except Exception:
            pass

        out = {
            "profile_id": self._current_profile,
            "profile": self._current_profile,   # alias legacy
            "name": self.input_name.text().strip(),
            "platform": platform,
            "os_type": platform,
            "os_name": os_name,
            "os_version": os_version,
            "cores": self.slider_cores.value(),
            "ram": f"{self.slider_ram.value()}G",
            "disk_gb": self.spin_disk.value(),
            "graphics_mode": graphics_mode,
            "graphics_vram": graphics_vram,
            "iso_choice": iso_choice,
            "iso_path": iso_path,
        }
        out.update(advanced)
        return out
    # vm_optimizer_v1_dialog
