import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QDialog, QTextEdit, QDialogButtonBox, QMessageBox,
    QFrame, QScrollArea, QToolButton, QFileDialog, QInputDialog,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from core.plugin_base import PluginBase
import platform
import subprocess
import os
import io
import json
import tarfile
import tempfile
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from services.host_system_info import (
    get_host_info, invalidate_cache, fmt_cpu, fmt_memory, IS_WINDOWS
)
from services import ovf_io

log = logging.getLogger(__name__)

class NotesDialog(QDialog):
    def __init__(self, current_notes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notas de la VM")
        self.resize(400, 300)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setText(current_notes)
        self.text.setToolTip("Escribe notas personales sobre esta máquina virtual (configuración, propósito, observaciones...)")
        layout.addWidget(self.text)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

class OpThread(QThread):
    """Ejecuta una operación de larga duración (clonar/exportar/importar) sin
    bloquear la UI. Devuelve el resultado por `done` o el error por `error`."""
    done = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.done.emit(self._fn())
        except Exception as e:
            log.error(f"Operación fallida: {e}", exc_info=True)
            self.error.emit(str(e))


class Plugin(PluginBase):
    name = "Dashboard"
    version = "1.4.0"

    def __init__(self, app):
        super().__init__(app)
        self.current_vm_id = None

    def get_tabs(self):
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- BOTONES DE ACCIÓN ---
        toolbar = QHBoxLayout()
        self.btn_clone = QPushButton("🧬 Clonar")
        self.btn_clone.setToolTip("Crear una copia completa de la VM seleccionada (configuración y disco)")
        self.btn_import = QPushButton("⇩ Importar")
        self.btn_import.setToolTip("Importar una VM desde un archivo OVA, OVF o paquete NVM")
        self.btn_export = QPushButton("⇪ Exportar")
        self.btn_export.setToolTip("Exportar la VM seleccionada a OVA (VirtualBox/VMware) o paquete NVM")
        self.btn_history = QPushButton("🕘 Historial")
        self.btn_history.setToolTip("Ver versiones anteriores de la configuración y restaurar una")
        self.btn_notes = QPushButton("📝 Notas")
        self.btn_notes.setToolTip("Editar notas personales de la VM seleccionada")
        self.btn_change_iso = QPushButton("📀 Cambiar ISO")
        self.btn_change_iso.setToolTip("Cambiar la imagen ISO montada en la unidad de CD/DVD de la VM")
        self.btn_save_template = QPushButton("💾 Plantilla")
        self.btn_save_template.setToolTip("Guardar los ajustes de hardware de esta VM como plantilla reutilizable")
        self.btn_from_template = QPushButton("📋 Desde plantilla")
        self.btn_from_template.setToolTip("Crear una VM nueva a partir de una plantilla guardada")
        self.btn_delete = QPushButton("🗑 Eliminar VM")
        self.btn_delete.setToolTip("Eliminar permanentemente la VM seleccionada y sus discos asociados")

        self.btn_clone.clicked.connect(self._clone_vm)
        self.btn_import.clicked.connect(self._import_vm)
        self.btn_export.clicked.connect(self._export_vm)
        self.btn_history.clicked.connect(self._show_history)
        self.btn_notes.clicked.connect(self._edit_notes)
        self.btn_change_iso.clicked.connect(self._hot_swap_iso)
        self.btn_save_template.clicked.connect(self._save_as_template)
        self.btn_from_template.clicked.connect(self._new_from_template)
        self.btn_delete.clicked.connect(self._delete_vm)

        toolbar.addWidget(self.btn_clone)
        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_history)
        toolbar.addWidget(self.btn_notes)
        toolbar.addWidget(self.btn_change_iso)
        toolbar.addWidget(self.btn_save_template)
        toolbar.addWidget(self.btn_from_template)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_delete)
        main_layout.addLayout(toolbar)

        # --- TARJETAS ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        card_style = """
            QFrame#CardFrame {
                background-color: transparent;
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            QFrame#CardFrame QLabel {
                background-color: transparent;
            }
            QFrame#CardFrame QScrollArea {
                background-color: transparent;
                border: none;
            }
            QFrame#CardFrame QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """

        # === TARJETA 1: Info de la VM ===
        self.card_vm = QFrame()
        self.card_vm.setObjectName("CardFrame")
        self.card_vm.setStyleSheet(card_style)
        lay_vm = QVBoxLayout(self.card_vm)

        title_vm = QLabel("<b>Información de la Máquina Virtual</b>")
        title_vm.setStyleSheet("font-size: 16px; padding: 10px;")
        lay_vm.addWidget(title_vm)

        form_vm = QFormLayout()
        form_vm.setContentsMargins(10, 0, 10, 10)
        form_vm.setSpacing(8)

        self.lbl_vm_name = QLabel("—")
        self.lbl_vm_name.setToolTip("Nombre identificador de la máquina virtual")
        self.lbl_vm_state = QLabel("—")
        self.lbl_vm_state.setToolTip("Estado actual: Apagada, Running, Paused, Apagando...")
        self.lbl_vm_platform = QLabel("—")
        self.lbl_vm_platform.setToolTip("Plataforma del sistema operativo invitado")
        self.lbl_vm_os = QLabel("—")
        self.lbl_vm_os.setToolTip("Sistema operativo y versión instalados en la VM")
        self.lbl_vm_firmware = QLabel("—")
        self.lbl_vm_firmware.setToolTip("Tipo de firmware: BIOS (tradicional) o UEFI (OVMF)")
        self.lbl_vm_chipset = QLabel("—")
        self.lbl_vm_chipset.setToolTip("Chipset de la placa base virtual: i440FX o Q35")
        self.lbl_vm_cpu = QLabel("—")
        self.lbl_vm_cpu.setToolTip("Número de CPUs virtuales asignadas")
        self.lbl_vm_ram = QLabel("—")
        self.lbl_vm_ram.setToolTip("Memoria RAM asignada en MB")
        self.lbl_vm_graphics = QLabel("—")
        self.lbl_vm_graphics.setToolTip("Dispositivo gráfico virtual usado por la VM")
        self.lbl_vm_vram = QLabel("—")
        self.lbl_vm_vram.setToolTip("Memoria de video (VRAM) asignada en MB")
        self.lbl_vm_disk = QLabel("—")
        self.lbl_vm_disk.setToolTip("Ruta del disco duro virtual de la VM")
        self.lbl_vm_iso = QLabel("—")
        self.lbl_vm_iso.setToolTip("Imagen ISO montada en la unidad de CD/DVD")
        self.lbl_vm_net = QLabel("—")
        self.lbl_vm_net.setToolTip("Configuración de red: nombre, modelo y backend del adaptador")
        self.lbl_vm_passthrough = QLabel("—")
        self.lbl_vm_passthrough.setToolTip("Dispositivos USB/PCI passthrough conectados a la VM")
        self.lbl_vm_shared = QLabel("—")
        self.lbl_vm_shared.setToolTip("Carpetas compartidas entre el host y la VM")
        self.lbl_vm_clipboard = QLabel("—")
        self.lbl_vm_clipboard.setToolTip("Portapapeles compartido entre host y VM")
        self.lbl_vm_notes = QLabel("—")
        self.lbl_vm_notes.setToolTip("Notas personales de la máquina virtual")

        form_vm.addRow("<b>Nombre:</b>", self.lbl_vm_name)
        form_vm.addRow("<b>Estado:</b>", self.lbl_vm_state)
        form_vm.addRow("<b>Plataforma:</b>", self.lbl_vm_platform)
        form_vm.addRow("<b>SO:</b>", self.lbl_vm_os)
        form_vm.addRow("<b>Firmware:</b>", self.lbl_vm_firmware)
        form_vm.addRow("<b>Chipset:</b>", self.lbl_vm_chipset)
        form_vm.addRow("<b>CPU:</b>", self.lbl_vm_cpu)
        form_vm.addRow("<b>RAM:</b>", self.lbl_vm_ram)
        form_vm.addRow("<b>Gráficos:</b>", self.lbl_vm_graphics)
        form_vm.addRow("<b>VRAM:</b>", self.lbl_vm_vram)
        form_vm.addRow("<b>Disco:</b>", self.lbl_vm_disk)
        form_vm.addRow("<b>ISO:</b>", self.lbl_vm_iso)
        form_vm.addRow("<b>Red:</b>", self.lbl_vm_net)
        form_vm.addRow("<b>Passthrough:</b>", self.lbl_vm_passthrough)
        form_vm.addRow("<b>Carpetas compartidas:</b>", self.lbl_vm_shared)
        form_vm.addRow("<b>Clipboard:</b>", self.lbl_vm_clipboard)
        form_vm.addRow("<b>Notas:</b>", self.lbl_vm_notes)

        scroll_vm = QScrollArea()
        scroll_vm.setWidgetResizable(True)
        scroll_vm.setFrameShape(QFrame.Shape.NoFrame)
        scroll_vm_content = QWidget()
        scroll_vm_content.setLayout(form_vm)
        scroll_vm.setWidget(scroll_vm_content)
        lay_vm.addWidget(scroll_vm)

        cards_layout.addWidget(self.card_vm, 1)

        # === TARJETA 2: Info del Host ===
        self.card_host = QFrame()
        self.card_host.setObjectName("CardFrame")
        self.card_host.setStyleSheet(card_style)
        lay_host = QVBoxLayout(self.card_host)

        host_header = QHBoxLayout()
        title_host = QLabel("<b>Información del Host (Anfitrión)</b>")
        title_host.setStyleSheet("font-size: 16px; padding: 10px;")
        host_header.addWidget(title_host)
        host_header.addStretch()
        self.btn_host_refresh = QToolButton()
        self.btn_host_refresh.setText("🔄")
        self.btn_host_refresh.setToolTip("Actualizar información del host")
        self.btn_host_refresh.setAutoRaise(True)
        self.btn_host_refresh.clicked.connect(self._refresh_host_info_forced)
        host_header.addWidget(self.btn_host_refresh)
        lay_host.addLayout(host_header)

        # ---- Bloque Software ----
        lbl_sw = QLabel("<b>Software</b>")
        lbl_sw.setStyleSheet("padding: 0 10px; margin-top: 4px;")
        lay_host.addWidget(lbl_sw)

        form_sw = QFormLayout()
        form_sw.setContentsMargins(10, 0, 10, 6)
        form_sw.setSpacing(6)

        self.lbl_host_os = QLabel("—")
        self.lbl_host_os.setToolTip("Sistema operativo del equipo anfitrión")
        self.lbl_host_de = QLabel("—")
        self.lbl_host_de.setToolTip("Entorno de escritorio del host (GNOME, KDE, etc.)")
        self.lbl_host_de_extra = QLabel("—")
        self.lbl_host_de_extra.setToolTip("Componentes extra del entorno de escritorio")
        self.lbl_host_qt = QLabel("—")
        self.lbl_host_qt.setToolTip("Versión del framework Qt usado por la aplicación")
        self.lbl_host_kernel = QLabel("—")
        self.lbl_host_kernel.setToolTip("Versión del kernel de Linux del host")
        self.lbl_host_gfx = QLabel("—")
        self.lbl_host_gfx.setToolTip("Plataforma gráfica del host (X11, Wayland)")

        form_sw.addRow("<b>Sistema Operativo:</b>", self.lbl_host_os)
        form_sw.addRow("<b>Entorno de escritorio:</b>", self.lbl_host_de)
        form_sw.addRow("<b>Componentes extra:</b>", self.lbl_host_de_extra)
        form_sw.addRow("<b>Versión de Qt:</b>", self.lbl_host_qt)
        form_sw.addRow("<b>Kernel:</b>", self.lbl_host_kernel)
        form_sw.addRow("<b>Plataforma gráfica:</b>", self.lbl_host_gfx)
        lay_host.addLayout(form_sw)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: palette(mid); margin: 4px 10px;")
        lay_host.addWidget(sep)

        # ---- Bloque Hardware ----
        lbl_hw = QLabel("<b>Hardware</b>")
        lbl_hw.setStyleSheet("padding: 0 10px; margin-top: 4px;")
        lay_host.addWidget(lbl_hw)

        form_hw = QFormLayout()
        form_hw.setContentsMargins(10, 0, 10, 6)
        form_hw.setSpacing(6)

        self.lbl_host_cpu = QLabel("—")
        self.lbl_host_cpu.setToolTip("Modelo del procesador del host")
        self.lbl_host_cpu.setWordWrap(True)
        self.lbl_host_ram = QLabel("—")
        self.lbl_host_ram.setToolTip("Memoria RAM total instalada en el host")
        self.lbl_host_ram.setWordWrap(True)
        self.lbl_host_gpu = QLabel("—")
        self.lbl_host_gpu.setToolTip("Procesador gráfico (GPU) del host")
        self.lbl_host_gpu.setWordWrap(True)
        self.lbl_host_vendor = QLabel("—")
        self.lbl_host_vendor.setToolTip("Fabricante del equipo anfitrión")
        self.lbl_host_model = QLabel("—")
        self.lbl_host_model.setToolTip("Nombre del producto/modelo del equipo")
        self.lbl_host_serial = QLabel("—")
        self.lbl_host_serial.setToolTip("Número de serie del equipo anfitrión")
        self.lbl_host_kvm = QLabel("—")
        self.lbl_host_kvm.setToolTip("Indica si el host tiene soporte para virtualización KVM (/dev/kvm)")
        self.lbl_host_qemu = QLabel("—")
        self.lbl_host_qemu.setToolTip("Versión instalada de QEMU en el host")

        form_hw.addRow("<b>Procesador:</b>", self.lbl_host_cpu)
        form_hw.addRow("<b>Memoria RAM:</b>", self.lbl_host_ram)
        form_hw.addRow("<b>Procesador gráfico:</b>", self.lbl_host_gpu)
        form_hw.addRow("<b>Fabricante:</b>", self.lbl_host_vendor)
        form_hw.addRow("<b>Nombre del producto:</b>", self.lbl_host_model)
        form_hw.addRow("<b>Número de serie:</b>", self.lbl_host_serial)
        form_hw.addRow("<b>Soporte KVM:</b>", self.lbl_host_kvm)
        form_hw.addRow("<b>Versión QEMU:</b>", self.lbl_host_qemu)
        lay_host.addLayout(form_hw)

        scroll_host = QScrollArea()
        scroll_host.setWidgetResizable(True)
        scroll_host.setFrameShape(QFrame.Shape.NoFrame)
        scroll_host_content = QWidget()
        scroll_host_content.setLayout(lay_host)
        scroll_host.setWidget(scroll_host_content)

        container_host = QVBoxLayout()
        container_host.setContentsMargins(0, 0, 0, 0)
        container_host.addWidget(scroll_host)
        self.card_host.setLayout(container_host)

        cards_layout.addWidget(self.card_host, 1)
        main_layout.addLayout(cards_layout)

        self.app.vm_selection_changed.connect(self._on_vm_selected)
        self._refresh_host_info_forced()

        self._host_timer = QTimer()
        self._host_timer.setInterval(3000)
        self._host_timer.timeout.connect(self._maybe_refresh_host)
        self._host_timer.start()

        return [("Resumen", self.main_widget)]

    def _refresh_host_info_forced(self):
        invalidate_cache()
        self._refresh_host_info()

    def _maybe_refresh_host(self):
        if not self.main_widget.isVisible(): return
        info = get_host_info()
        self.lbl_host_ram.setText(fmt_memory(info, self.app.tr))

    def _refresh_host_info(self):
        info = get_host_info()

        self.lbl_host_os.setText(info.get("distro_name") or "—")

        de_name = info.get("de_name", "—")
        de_version = info.get("de_version", "")
        de_extra = info.get("de_extra", "")

        self.lbl_host_de.setText(f"{de_name} {de_version}".strip())
        self.lbl_host_de_extra.setText(de_extra or "—")

        self.lbl_host_qt.setText(info.get("qt_version") or "—")
        self.lbl_host_kernel.setText(info.get("kernel") or "—")
        self.lbl_host_gfx.setText(info.get("graphics_platform") or "—")

        self.lbl_host_cpu.setText(fmt_cpu(info, self.app.tr))
        self.lbl_host_ram.setText(fmt_memory(info, self.app.tr))
        self.lbl_host_gpu.setText(info.get("gpu") or "—")
        self.lbl_host_vendor.setText(info.get("manufacturer") or "—")
        self.lbl_host_model.setText(info.get("product_name") or "—")
        self.lbl_host_serial.setText(info.get("serial_number") or "—")
        if IS_WINDOWS:
            self.lbl_host_kvm.setText("N/A (Windows)")
            self.lbl_host_kvm.setStyleSheet("color: #888;")
        elif os.path.exists("/dev/kvm"):
            self.lbl_host_kvm.setText("✅ Sí")
            self.lbl_host_kvm.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.lbl_host_kvm.setText("❌ No — las VMs correrán en TCG (emulación)")
            self.lbl_host_kvm.setStyleSheet("color: #c62828; font-weight: bold;")
        self.lbl_host_qemu.setText(self._get_qemu_version() or "No instalado")

    def _get_qemu_version(self):
        try:
            qemu_bin = "qemu-system-x86_64.exe" if IS_WINDOWS else "qemu-system-x86_64"
            out = subprocess.check_output([qemu_bin, "--version"], text=True)
            return out.splitlines()[0].split("version")[1].strip().split()[0]
        except Exception:
            return "No instalado"

    def _on_vm_selected(self, vm_id):
        self.current_vm_id = vm_id
        vm = self.app.get_vm(vm_id)
        if not vm: return

        self.lbl_vm_name.setText(vm.get("name", "—"))
        self.lbl_vm_state.setText(self.app.tr(vm.get("state", "Apagada")))
        self.lbl_vm_platform.setText(vm.get("platform", "—"))

        so = vm.get("so", "")
        ver = vm.get("version", "")
        self.lbl_vm_os.setText(f"{so} {ver}".strip() or "—")

        fw_idx = vm.get("firmware_idx", 0)
        fw_text = self.app.tr("UEFI (OVMF)") if fw_idx == 1 else self.app.tr("BIOS (tradicional)")
        self.lbl_vm_firmware.setText(fw_text)

        chip_idx = vm.get("chipset_idx", 0)
        chip_text = self.app.tr("Q35 (moderno, PCIe)") if chip_idx == 1 else self.app.tr("i440FX (clásico)")
        self.lbl_vm_chipset.setText(chip_text)

        self.lbl_vm_cpu.setText(f"{vm.get('cores', '?')} {self.app.tr('núcleos')}")
        self.lbl_vm_ram.setText(f"{vm.get('ram', '?')} MB")

        gfx_idx = vm.get("graphics_idx", 0)
        gfx_list = ["Automático", "VirtIO-GPU 2D", "VirtIO-GPU + VirGL 3D",
                    "VirtIO-GPU + Venus", "QXL 2D", "VMware SVGA II",
                    "VGA estándar", "Headless"]
        self.lbl_vm_graphics.setText(
            self.app.tr(gfx_list[gfx_idx]) if gfx_idx < len(gfx_list) else "—")

        vram_idx = vm.get("vram_idx", 0)
        vram_list = ["64 MB", "128 MB", "256 MB", "512 MB"]
        self.lbl_vm_vram.setText(vram_list[vram_idx] if vram_idx < len(vram_list) else "—")

        disk = vm.get("disk_path")
        self.lbl_vm_disk.setText(os.path.basename(disk) if disk else self.app.tr("Sin disco configurado"))

        iso = vm.get("iso_path")
        self.lbl_vm_iso.setText(os.path.basename(iso) if iso else self.app.tr("Sin ISO montada"))

        nets = vm.get("network_adapters", [])
        if not nets:
            self.lbl_vm_net.setText(self.app.tr("Sin red configurada"))
        elif len(nets) == 1:
            n = nets[0]
            self.lbl_vm_net.setText(
                f"{self.app.tr(n.get('name', 'Red 1'))} ({n.get('model', 'VirtIO')}, {n.get('backend', 'NAT')})")
        else:
            self.lbl_vm_net.setText(f"{len(nets)} {self.app.tr('adaptadores')}")

        pt_count = len(vm.get("passthrough_devices", []))
        self.lbl_vm_passthrough.setText(
            f"{pt_count} {self.app.tr('dispositivos')}" if pt_count > 0 else self.app.tr("Ninguno"))

        shared = vm.get("shared_folders", [])
        self.lbl_vm_shared.setText(
            f"{len(shared)} {self.app.tr('carpetas')}" if shared else self.app.tr("Ninguna"))

        self.lbl_vm_clipboard.setText(self.app.tr(vm.get("clipboard", "Desactivado")))

        notes = vm.get("notes", "")
        if notes:
            self.lbl_vm_notes.setText(notes)
            self.lbl_vm_notes.setStyleSheet("color: #f9a825; font-style: italic;")
        else:
            self.lbl_vm_notes.setText(self.app.tr("Sin notas"))
            self.lbl_vm_notes.setStyleSheet("color: #888; font-style: italic;")

    def _hot_swap_iso(self):
        if not self.current_vm_id: return
        iso_path, _ = QFileDialog.getOpenFileName(self.app.parent(), "Seleccionar nueva ISO", self.app.isos_dir.as_posix(), "Imágenes (*.iso *.img)")
        if iso_path:
            self.app.change_iso(self.current_vm_id, iso_path)
            QMessageBox.information(self.app.parent(), "Hot-Swap", "ISO cambiada correctamente.")

    def _edit_notes(self):
        if not self.current_vm_id: return
        vm = self.app.get_vm(self.current_vm_id)
        dlg = NotesDialog(vm.get("notes", ""), self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.app.vm_repo.update(self.current_vm_id, {"notes": dlg.text.toPlainText()})
            self._on_vm_selected(self.current_vm_id)

    def _show_history(self):
        if not self.current_vm_id:
            return
        from ui_widgets.vm_history_dialog import VMHistoryDialog

        dlg = VMHistoryDialog(self.app.vm_repo, self.current_vm_id, self.app.parent())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._on_vm_selected(self.current_vm_id)

    def _save_as_template(self):
        if not self.current_vm_id:
            return
        vm = self.app.get_vm(self.current_vm_id)
        if not vm:
            return
        from services.vm_templates import TemplateManager
        from ui_widgets.vm_template_dialogs import SaveTemplateDialog

        dlg = SaveTemplateDialog(vm, self.app.parent())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        mgr = TemplateManager(self.app.data_dir)
        mgr.save_template(dlg.template_name, vm, dlg.template_icon,
                          dlg.template_description)
        log.info("Plantilla guardada: %s", dlg.template_name)
        QMessageBox.information(
            self.app.parent(), "Plantilla guardada",
            f"'{dlg.template_name}' ya está disponible en <b>📋 Desde plantilla</b>.")

    def _new_from_template(self):
        from services.media_library import MediaLibraryManager
        from services.vm_templates import TemplateManager
        from ui_widgets.vm_template_dialogs import TemplatePickerDialog

        mgr = TemplateManager(self.app.data_dir)
        if not mgr.list_templates():
            QMessageBox.information(
                self.app.parent(), "Sin plantillas",
                "Todavía no hay plantillas. Selecciona una VM y pulsa <b>💾 Plantilla</b> primero.")
            return

        dlg = TemplatePickerDialog(mgr, self.app.parent())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        config = mgr.create_vm_config(dlg.selected_id, dlg.vm_name)
        nombre = config["name"]

        # La plantilla define el tamaño; el disco siempre es nuevo y propio.
        media = MediaLibraryManager(self.app.data_dir, getattr(self.app, "settings", None))
        ok, resultado = media.create_disk(nombre, config.get("disk_size") or "40G", "qcow2")
        if ok:
            config["disk_path"] = resultado
        else:
            QMessageBox.warning(
                self.app.parent(), "Disco no creado",
                f"No se pudo crear el disco ({resultado}).\n"
                "La VM se creará sin disco: añádelo desde Configuración VM.")

        self.app.vm_repo.add(config)
        self.app.vm_state_changed.emit(config["id"], "Apagada")
        QMessageBox.information(
            self.app.parent(), "VM creada",
            f"'{nombre}' ya aparece en la lista de VMs.")

    def _delete_vm(self):
        if not self.current_vm_id: return
        vm = self.app.get_vm(self.current_vm_id)
        name = vm.get("name", "Desconocida")
        resp = QMessageBox.question(
            self.app.parent(), "Eliminar VM",
            f"¿Estás seguro de eliminar la VM '{name}'?\n\nEsto borrará la configuración y los discos asociados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            # AppContext se encarga de apagar primero y borrar después.
            self.app.delete_vm(self.current_vm_id)

    def _require_vm_off(self, accion: str):
        """Devuelve la VM si está apagada; si no, muestra aviso y devuelve None."""
        if not self.current_vm_id:
            return None
        vm = self.app.get_vm(self.current_vm_id)
        if not vm:
            return None
        encendida = vm.get("state") in ("Running", "Paused", "Apagando...") or \
            self.current_vm_id in self.app.runner.active_processes
        if encendida:
            QMessageBox.warning(
                self.app.parent(), "VM encendida",
                f"No se puede {accion} una VM mientras está encendida.\n\nApaga '{vm.get('name')}' e inténtalo de nuevo."
            )
            return None
        return vm

    def _run_op(self, progress_text, fn, on_success):
        """Ejecuta `fn` en un thread con diálogo de progreso indeterminado."""
        progress = QProgressDialog(progress_text, None, 0, 0, self.app.parent())
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(False)

        progress.show()

        thread = OpThread(fn, self.app.parent())
        self._op_thread = thread  # mantener referencia viva

        def _done(result):
            progress.close()
            try:
                on_success(result)
            except Exception as e:
                log.error(f"Error al finalizar operación: {e}", exc_info=True)
                QMessageBox.critical(self.app.parent(), "Error", str(e))

        def _fail(err):
            progress.close()
            QMessageBox.critical(self.app.parent(), "Error de la operación", err)

        thread.done.connect(_done)
        thread.error.connect(_fail)
        thread.start()

    def _add_imported_vm(self, nuevo_vm, mensaje):
        """Registra una VM nueva (clon/import) en el repositorio y refresca la lista."""
        self.app.vm_repo.add(nuevo_vm)
        self.app.vm_state_changed.emit(nuevo_vm["id"], "Apagada")
        log.info(f"✓ {mensaje}: {nuevo_vm.get('name')}")
        QMessageBox.information(
            self.app.parent(), "Listo",
            f"{mensaje}:\n\n'{nuevo_vm.get('name')}'\n\nYa aparece en la lista de VMs."
        )

    def _clone_vm(self):
        vm = self._require_vm_off("clonar")
        if not vm:
            return

        nombre, ok = QInputDialog.getText(
            self.app.parent(), "Clonar VM",
            "Nombre de la copia:", text=f"{vm.get('name', 'VM')} (copia)"
        )
        if not ok:
            return
        nombre = nombre.strip() or f"{vm.get('name', 'VM')} (copia)"

        vm_dir = self.app.vms_dir / vm["id"]
        if not vm_dir.is_dir():
            QMessageBox.critical(
                self.app.parent(), "Error",
                f"No se encontró el directorio de la VM:\n{vm_dir}"
            )
            return

        nuevo_id = str(uuid.uuid4())
        destino = self.app.vms_dir / nuevo_id

        def _work():
            shutil.copytree(vm_dir, destino)
            nuevo = dict(vm)
            nuevo["id"] = nuevo_id
            nuevo["name"] = nombre
            nuevo["state"] = "Apagada"
            # Reapuntar el disco al nuevo directorio (si estaba dentro de vm_dir
            # copytree ya lo copió; si estaba fuera, copiarlo aparte)
            disco = vm.get("disk_path")
            if disco:
                d = Path(disco)
                nuevo["disk_path"] = str(destino / d.name)
                if d.is_file() and not str(d.resolve()).startswith(str(vm_dir.resolve())):
                    shutil.copy2(d, destino / d.name)
            # OVMF_VARS vive en el directorio y se re-resuelve por id en el runner
            return nuevo

        self._run_op(
            f"Clonando '{vm.get('name')}'... (puede tardar si el disco es grande)",
            _work,
            lambda nuevo: self._add_imported_vm(nuevo, "VM clonada")
        )

    def _export_vm(self):
        vm = self._require_vm_off("exportar")
        if not vm:
            return

        default_name = (vm.get("name") or "vm").replace(" ", "_")
        ruta, seleccion = QFileDialog.getSaveFileName(
            self.app.parent(), "Exportar VM",
            str(Path.home() / "Descargas" / default_name),
            "OVA - VirtualBox/VMware (*.ova);;Paquete NVM (*.tar.gz *.nvm.tar.gz)"
        )
        if not ruta:
            return
        if not ruta.endswith((".ova", ".tar.gz")):
            ruta += ".ova" if str(seleccion).startswith("OVA") else ".tar.gz"

        vm_dir = self.app.vms_dir / vm["id"]
        if not vm_dir.is_dir():
            QMessageBox.critical(
                self.app.parent(), "Error",
                f"No se encontró el directorio de la VM:\n{vm_dir}"
            )
            return

        if ruta.endswith(".ova"):
            disco = vm.get("disk_path")
            if not disco or not Path(disco).is_file():
                QMessageBox.critical(
                    self.app.parent(), "Error",
                    "La VM no tiene disco configurado para exportar."
                )
                return
            # Chequeo de espacio: la conversión a VMDK + el OVA final
            # necesitan ~2× el tamaño real del disco en el destino
            real = Path(disco).stat().st_size
            ok, _free, msg = ovf_io.check_ovf_space(ruta, int(real * 2))
            if not ok:
                QMessageBox.warning(self.app.parent(), "Espacio insuficiente", msg)
                return
            if ok is None:
                resp = QMessageBox.question(
                    self.app.parent(), "Espacio justo", msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return
            self._run_op(
                f"Exportando '{vm.get('name')}' a OVA (convirtiendo disco a VMDK)...",
                lambda: self._export_ova_impl(vm, ruta),
                lambda ruta_ok: self._export_done(ruta_ok, "OVA listo para VirtualBox y VMware.")
            )
        else:
            self._run_op(
                f"Exportando '{vm.get('name')}'...",
                lambda: self._export_nvm(vm, vm_dir, ruta),
                lambda ruta_ok: self._export_done(ruta_ok, "Paquete NVM exportado.")
            )

    def _export_done(self, ruta_ok, detalle):
        log.info(f"✓ VM exportada: {ruta_ok}")
        QMessageBox.information(
            self.app.parent(), "Exportar VM",
            f"VM exportada correctamente.\n\n{detalle}\n\n{ruta_ok}"
        )

    def _export_nvm(self, vm, vm_dir, ruta):
        """Exporta en el paquete nativo NVM (config + disco en tar.gz)."""
        manifest = json.dumps(
            {"format": "nvm-export-v1", "vm": vm}, ensure_ascii=False, indent=2
        ).encode("utf-8")
        with tarfile.open(ruta, "w:gz") as tar:
            info = tarfile.TarInfo("manifest.json")
            info.size = len(manifest)
            tar.addfile(info, io.BytesIO(manifest))
            tar.add(vm_dir, arcname="files")
            disco = vm.get("disk_path")
            if disco:
                d = Path(disco)
                if d.is_file() and not str(d.resolve()).startswith(str(vm_dir.resolve())):
                    tar.add(d, arcname=f"disk/{d.name}")
        return ruta

    @staticmethod
    def _qemu_img(args):
        exe = shutil.which("qemu-img")
        if not exe:
            raise RuntimeError("No se encontró qemu-img. Instala 'qemu-img' (paquete qemu-utils).")
        r = subprocess.run([exe] + list(args), capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"qemu-img falló: {(r.stderr or r.stdout or '').strip()}")
        return r.stdout

    def _export_ova_impl(self, vm, ruta):
        """Exporta a OVA con services/ovf_io (módulo probado de la v38):
        VMDK streamOptimized + descriptor OVF con fixes VBox/VMware +
        manifest SHA1 + metadata propia (.virtmachine.json)."""
        disco = Path(vm["disk_path"])
        parent = Path(ruta).resolve().parent
        # Temporal junto al destino (no en /tmp): el VMDK pesa lo mismo
        # que el disco real y /tmp puede ser un tmpfs pequeño
        work = tempfile.mkdtemp(prefix=".ovf_export_", dir=str(parent))
        try:
            vmdk = Path(work) / (disco.stem + ".vmdk")
            ovf_io.convert_to_vmdk_stream_optimized(str(disco), str(vmdk))

            info = json.loads(self._qemu_img(["info", "--output=json", str(disco)]))
            cap_gb = max(1, int(int(info.get("virtual-size") or 0) / (1024 ** 3)))

            nets = []
            for n in (vm.get("network_adapters") or [{"model": "VirtIO"}]):
                m = (n.get("model") or "VirtIO").lower()
                if "e1000" in m:
                    vbox_model = "E1000"
                elif "vmxnet" in m:
                    vbox_model = "VMXNET3"
                elif "virtio" in m:
                    vbox_model = "virtio"
                else:
                    vbox_model = "E1000"
                nets.append({"name": "nat", "model": vbox_model})

            os_type = (vm.get("platform") or "linux").lower()
            if os_type not in ("linux", "windows", "macos", "android"):
                os_type = "linux"
            distro = (vm.get("so") or vm.get("version") or "").strip()
            firmware = "uefi" if vm.get("firmware_idx", 0) == 1 else "bios"

            ovf_text = ovf_io.build_ovf_xml(
                vm_name=vm.get("name") or "VM",
                os_type=os_type,
                distro_or_version=distro,
                cpus=int(vm.get("cores", 2) or 2),
                memory_mb=int(vm.get("ram", 2048) or 2048),
                disks=[{"file": vmdk.name, "capacity_gb": cap_gb,
                        "format": "", "disk_id": "vmdisk1"}],
                networks=nets,
                vbox_ostype=ovf_io.map_vm_to_ostype(os_type, distro),
                cdroms=[],
                firmware=firmware,
            )
            # Metadata propia: config completa de la VM para reimportar
            # tal cual (los hipervisores de terceros la ignoran)
            meta = {
                "schema": "nvm-1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "vm": dict(vm),
            }
            ovf_io.pack_ova(ovf_text, [str(vmdk)], ruta, extra_meta=meta)
            return ruta
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _import_vm(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self.app.parent(), "Importar VM", str(Path.home() / "Descargas"),
            "OVF/OVA (*.ova *.ovf);;Paquete NVM (*.tar.gz *.nvm.tar.gz *.tar);;Todos los archivos (*)"
        )
        if not ruta:
            return

        # Nombres existentes (para evitar duplicados) — leer en el hilo principal
        existentes = {v.get("name") for v in self.app.vm_repo.get_all()}
        vms_dir = self.app.vms_dir

        def _work():
            low = ruta.lower()
            if low.endswith(".ova"):
                return self._import_ova(ruta, existentes, vms_dir)
            if low.endswith(".ovf"):
                return self._import_ovf_dir(Path(ruta), existentes, vms_dir)
            # Tar genérico: paquete NVM o OVA comprimido
            with tarfile.open(ruta, "r:*") as tar:
                nombres = tar.getnames()
            if "manifest.json" in nombres:
                return self._import_nvm(ruta, vms_dir, existentes)
            if any(n.lower().endswith(".ovf") for n in nombres):
                return self._import_ova(ruta, existentes, vms_dir)
            raise RuntimeError(
                "Formato no reconocido: no contiene manifest.json (NVM) ni un .ovf (OVF/OVA)."
            )

        self._run_op(
            "Importando VM...",
            _work,
            lambda nuevo: self._add_imported_vm(nuevo, "VM importada")
        )

    def _import_nvm(self, ruta, vms_dir, existentes):
        """Importa un paquete NVM (.nvm.tar.gz)."""
        with tarfile.open(ruta, "r:*") as tar:
            try:
                mf = tar.extractfile("manifest.json")
            except KeyError:
                mf = None
            if mf is None:
                raise RuntimeError(
                    "No es un paquete válido: falta manifest.json."
                )
            data = json.loads(mf.read().decode("utf-8"))
            if data.get("format") != "nvm-export-v1":
                raise RuntimeError(
                    f"Formato de paquete no soportado: {data.get('format')}"
                )
            vm = dict(data.get("vm") or {})
            if not vm:
                raise RuntimeError("El paquete no contiene configuración de VM.")

            nuevo_id = str(uuid.uuid4())
            destino = vms_dir / nuevo_id
            destino.mkdir(parents=True, exist_ok=False)

            # Extraer con protección contra path traversal
            base = destino.resolve()
            for m in tar.getmembers():
                if m.name == "manifest.json":
                    continue
                if not (m.name == "files" or m.name.startswith("files/")
                        or m.name == "disk" or m.name.startswith("disk/")):
                    continue
                target = (destino / m.name).resolve()
                if not str(target).startswith(str(base) + os.sep) and target != base:
                    raise RuntimeError(f"Ruta insegura en el paquete: {m.name}")
            for m in tar.getmembers():
                if m.name == "manifest.json":
                    continue
                if not (m.name == "files" or m.name.startswith("files/")
                        or m.name == "disk" or m.name.startswith("disk/")):
                    continue
                try:
                    tar.extract(m, destino, filter="data")
                except TypeError:  # Python < 3.12 sin soporte de filter
                    tar.extract(m, destino)

            # Normalizar: disco dentro de files/
            files_dir = destino / "files"
            disco_dir = destino / "disk"
            if disco_dir.is_dir():
                files_dir.mkdir(exist_ok=True)
                for f in disco_dir.iterdir():
                    shutil.move(str(f), str(files_dir / f.name))
                shutil.rmtree(disco_dir, ignore_errors=True)

            nuevo = vm
            nuevo["id"] = nuevo_id
            nuevo["state"] = "Apagada"
            disco = vm.get("disk_path")
            if disco:
                nombre_disco = Path(disco).name
                nuevo["disk_path"] = str(files_dir / nombre_disco)
            nombre = nuevo.get("name") or "VM importada"
            if nombre in existentes:
                nombre = f"{nombre} (importada)"
            nuevo["name"] = nombre
            return nuevo

    def _import_ova(self, ruta, existentes, vms_dir):
        """Importa un .ova/.tar con descriptor .ovf usando services/ovf_io."""
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(ruta, "r:*") as tar:
                for m in tar.getmembers():
                    if m.name.startswith("/") or ".." in Path(m.name).parts:
                        raise RuntimeError(f"Ruta insegura en el paquete: {m.name}")
                try:
                    tar.extractall(tmp, filter="data")
                except TypeError:
                    tar.extractall(tmp)
            ovfs = sorted(Path(tmp).rglob("*.ovf"))
            if not ovfs:
                raise RuntimeError("El paquete no contiene ningún descriptor .ovf.")
            meta = next(iter(Path(tmp).rglob(".virtmachine.json")), None)
            return self._vm_desde_ovf_dir(
                ovfs[0], existentes, vms_dir,
                origen=Path(ruta).name, meta_path=meta,
            )

    def _import_ovf_dir(self, ovf_path, existentes, vms_dir):
        """Importa un .ovf suelto (los discos van al lado)."""
        return self._vm_desde_ovf_dir(
            ovf_path, existentes, vms_dir,
            origen=ovf_path.name, meta_path=None,
        )

    def _vm_desde_ovf_dir(self, ovf_path, existentes, vms_dir, origen="", meta_path=None):
        """Parsea un OVF con ovf_io, convierte el disco a qcow2 y arma la VM."""
        ovf_text = ovf_path.read_text(encoding="utf-8", errors="replace")
        data = ovf_io.parse_ovf_xml(ovf_text)

        # Archivo de disco referenciado por el OVF
        disco_orig = None
        for d in data.get("disks", []):
            href = d.get("file") or ""
            if not href:
                continue
            cand = ovf_path.parent / href
            if not cand.is_file():
                cand = ovf_path.parent / Path(href).name
            if cand.is_file():
                disco_orig = cand
                break
        if disco_orig is None:
            for ext in ("*.vmdk", "*.qcow2", "*.vdi", "*.img", "*.raw", "*.vhdx", "*.vhd"):
                cands = sorted(ovf_path.parent.rglob(ext))
                if cands:
                    disco_orig = cands[0]
                    break
        if disco_orig is None:
            raise RuntimeError("El paquete no contiene ningún archivo de disco.")

        # Metadata propia del export NVM: config completa si está presente
        meta = ovf_io.load_virtmachine_meta(str(meta_path)) if meta_path else None
        vm_meta = None
        if isinstance(meta, dict) and meta.get("schema") == "nvm-1" \
                and isinstance(meta.get("vm"), dict):
            vm_meta = meta["vm"]

        # Nombre único
        nombre = (vm_meta or {}).get("name") or data.get("name") or "VM importada"
        if nombre in existentes:
            nombre = f"{nombre} (importada)"

        # Convertir disco a qcow2 (formato de la app)
        nuevo_id = str(uuid.uuid4())
        destino = vms_dir / nuevo_id
        files_dir = destino / "files"
        files_dir.mkdir(parents=True, exist_ok=False)
        disco_nuevo = files_dir / "Sistema.qcow2"
        ovf_io.convert_to_qcow2(str(disco_orig), str(disco_nuevo))

        if vm_meta:
            nuevo = dict(vm_meta)
        else:
            # Sin metadata propia: reconstruir la config desde el OVF
            os_type = data.get("os_type") or "linux"
            nets_ovf = data.get("networks") or []
            modelo = "e1000"
            if nets_ovf:
                sub = (nets_ovf[0].get("model") or "").lower()
                if "virtio" in sub:
                    modelo = "VirtIO"
                elif "vmxnet" in sub:
                    modelo = "vmxnet3"
                elif "e1000" in sub:
                    modelo = "e1000"
            distro = data.get("distro") or ""
            nuevo = {
                "platform": {"linux": "Linux", "windows": "Windows",
                             "macos": "macOS", "android": "Android"}.get(os_type, "Linux"),
                "so": distro if os_type == "linux" else "",
                "version": data.get("win_ver") or "",
                "version_id": "",
                "cores": int(data.get("cpus") or 2),
                "ram": int(data.get("memory_mb") or 2048),
                "firmware_idx": 1 if data.get("firmware") == "uefi" else 0,
                "chipset_idx": 1,
                "graphics_idx": 0,
                "secure_boot": False,
                "tpm": False,
                "disk_bus": "sata",
                "iso_path": None,
                "iso_source_type": None,
                "network_adapters": [{"name": "Red 1", "model": modelo,
                                      "backend": "NAT / Internet"}],
                "audio": "Intel HDA (recomendado)",
                "pointer": "USB Tablet",
                "clipboard": "Desactivado",
            }
        nuevo.update({
            "id": nuevo_id,
            "name": nombre,
            "state": "Apagada",
            "disk_path": str(disco_nuevo),
        })
        if not nuevo.get("notes"):
            nuevo["notes"] = f"Importada desde {origen}" if origen else ""
        return nuevo
