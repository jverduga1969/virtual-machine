import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFormLayout, QDialog, QTextEdit, QDialogButtonBox, QMessageBox, 
    QFrame, QScrollArea, QToolButton
)
from PyQt6.QtCore import Qt, QTimer
from core.plugin_base import PluginBase
import platform
import subprocess
import os
import shutil

from services.host_system_info import (
    get_host_info, invalidate_cache, fmt_cpu, fmt_memory
)

log = logging.getLogger(__name__)

class NotesDialog(QDialog):
    def __init__(self, current_notes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notas de la VM")
        self.resize(400, 300)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setText(current_notes)
        layout.addWidget(self.text)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

class Plugin(PluginBase):
    name = "Dashboard"
    version = "1.3.2"

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
        self.btn_import = QPushButton("⇩ Importar")
        self.btn_export = QPushButton("⇪ Exportar")
        self.btn_notes = QPushButton("📝 Notas")
        self.btn_delete = QPushButton("🗑 Eliminar VM")

        self.btn_clone.clicked.connect(self._clone_vm)
        self.btn_import.clicked.connect(self._import_vm)
        self.btn_export.clicked.connect(self._export_vm)
        self.btn_notes.clicked.connect(self._edit_notes)
        self.btn_delete.clicked.connect(self._delete_vm)

        toolbar.addWidget(self.btn_clone)
        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_notes)
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
        self.lbl_vm_state = QLabel("—")
        self.lbl_vm_platform = QLabel("—")
        self.lbl_vm_os = QLabel("—")
        self.lbl_vm_firmware = QLabel("—")
        self.lbl_vm_chipset = QLabel("—")
        self.lbl_vm_cpu = QLabel("—")
        self.lbl_vm_ram = QLabel("—")
        self.lbl_vm_graphics = QLabel("—")
        self.lbl_vm_vram = QLabel("—")
        self.lbl_vm_disk = QLabel("—")
        self.lbl_vm_iso = QLabel("—")
        self.lbl_vm_net = QLabel("—")
        self.lbl_vm_net.setWordWrap(True)
        self.lbl_vm_passthrough = QLabel("—")
        self.lbl_vm_shared = QLabel("—")
        self.lbl_vm_clipboard = QLabel("—")
        self.lbl_vm_notes = QLabel("—")
        self.lbl_vm_notes.setWordWrap(True)

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
        self.lbl_host_de = QLabel("—")
        self.lbl_host_de_extra = QLabel("—")
        self.lbl_host_qt = QLabel("—")
        self.lbl_host_kernel = QLabel("—")
        self.lbl_host_gfx = QLabel("—")

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
        self.lbl_host_cpu.setWordWrap(True)
        self.lbl_host_ram = QLabel("—")
        self.lbl_host_ram.setWordWrap(True)
        self.lbl_host_gpu = QLabel("—")
        self.lbl_host_gpu.setWordWrap(True)
        self.lbl_host_vendor = QLabel("—")
        self.lbl_host_model = QLabel("—")
        self.lbl_host_serial = QLabel("—")
        self.lbl_host_kvm = QLabel("—")
        self.lbl_host_qemu = QLabel("—")

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
        self.lbl_host_ram.setText(fmt_memory(info))

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

        self.lbl_host_cpu.setText(fmt_cpu(info))
        self.lbl_host_ram.setText(fmt_memory(info))
        self.lbl_host_gpu.setText(info.get("gpu") or "—")
        self.lbl_host_vendor.setText(info.get("manufacturer") or "—")
        self.lbl_host_model.setText(info.get("product_name") or "—")
        self.lbl_host_serial.setText(info.get("serial_number") or "—")
        self.lbl_host_kvm.setText("✅ Sí" if os.path.exists("/dev/kvm") else "❌ No")
        self.lbl_host_qemu.setText(self._get_qemu_version() or "No instalado")

    def _get_qemu_version(self):
        try:
            out = subprocess.check_output(["qemu-system-x86_64", "--version"], text=True)
            return out.splitlines()[0].split("version")[1].strip().split()[0]
        except Exception:
            return "No instalado"

    def _on_vm_selected(self, vm_id):
        self.current_vm_id = vm_id
        vm = self.app.get_vm(vm_id)
        if not vm: return

        self.lbl_vm_name.setText(vm.get("name", "—"))
        self.lbl_vm_state.setText(vm.get("state", "Apagada"))
        self.lbl_vm_platform.setText(vm.get("platform", "—"))

        so = vm.get("so", "")
        ver = vm.get("version", "")
        self.lbl_vm_os.setText(f"{so} {ver}".strip() or "—")

        fw_idx = vm.get("firmware_idx", 0)
        fw_text = "UEFI (OVMF)" if fw_idx == 1 else "BIOS (tradicional)"
        self.lbl_vm_firmware.setText(fw_text)

        chip_idx = vm.get("chipset_idx", 0)
        chip_text = "Q35 (moderno, PCIe)" if chip_idx == 1 else "i440FX (clásico)"
        self.lbl_vm_chipset.setText(chip_text)

        self.lbl_vm_cpu.setText(f"{vm.get('cores', '?')} núcleos")
        self.lbl_vm_ram.setText(f"{vm.get('ram', '?')} MB")

        gfx_idx = vm.get("graphics_idx", 0)
        gfx_list = ["Automático", "VirtIO-GPU 2D", "VirtIO-GPU + VirGL 3D",
                    "VirtIO-GPU + Venus", "QXL 2D", "VMware SVGA II",
                    "VGA estándar", "Headless"]
        self.lbl_vm_graphics.setText(gfx_list[gfx_idx] if gfx_idx < len(gfx_list) else "—")

        vram_idx = vm.get("vram_idx", 0)
        vram_list = ["64 MB", "128 MB", "256 MB", "512 MB"]
        self.lbl_vm_vram.setText(vram_list[vram_idx] if vram_idx < len(vram_list) else "—")

        disk = vm.get("disk_path")
        self.lbl_vm_disk.setText(os.path.basename(disk) if disk else "Sin disco configurado")

        iso = vm.get("iso_path")
        self.lbl_vm_iso.setText(os.path.basename(iso) if iso else "Sin ISO montada")

        nets = vm.get("network_adapters", [])
        if not nets:
            self.lbl_vm_net.setText("Sin red configurada")
        elif len(nets) == 1:
            n = nets[0]
            self.lbl_vm_net.setText(f"{n.get('name', 'Red')} ({n.get('model', 'VirtIO')}, {n.get('backend', 'NAT')})")
        else:
            self.lbl_vm_net.setText(f"{len(nets)} adaptadores")

        pt_count = len(vm.get("passthrough_devices", []))
        self.lbl_vm_passthrough.setText(f"{pt_count} dispositivos" if pt_count > 0 else "Ninguno")

        shared = vm.get("shared_folders", [])
        self.lbl_vm_shared.setText(f"{len(shared)} carpetas" if shared else "Ninguna")

        self.lbl_vm_clipboard.setText(vm.get("clipboard", "Desactivado"))

        notes = vm.get("notes", "")
        if notes:
            self.lbl_vm_notes.setText(notes)
            self.lbl_vm_notes.setStyleSheet("color: #f9a825; font-style: italic;")
        else:
            self.lbl_vm_notes.setText("Sin notas")
            self.lbl_vm_notes.setStyleSheet("color: #888; font-style: italic;")

        if not hasattr(self, 'btn_change_iso'):
            from PyQt6.QtWidgets import QPushButton, QFileDialog
            self.btn_change_iso = QPushButton("📀 Cambiar ISO")
            self.btn_change_iso.clicked.connect(self._hot_swap_iso)
            # Buscar un layout para añadirlo (asumiendo que existe self.buttons_layout o similar)
            if hasattr(self, 'buttons_layout'):
                self.buttons_layout.addWidget(self.btn_change_iso)

    def _hot_swap_iso(self):
        if not self.current_vm_id: return
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
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
            self.app.delete_vm(self.current_vm_id)
            vm_dir = self.app.data_dir / "vms" / self.current_vm_id
            if vm_dir.exists():
                try: shutil.rmtree(vm_dir)
                except: pass
            self.app.vm_state_changed.emit(self.current_vm_id, "Deleted")

    def _clone_vm(self):
        QMessageBox.information(self.app.parent(), "Clonar", "Función en desarrollo.")
    def _import_vm(self):
        QMessageBox.information(self.app.parent(), "Importar", "Función en desarrollo.")
    def _export_vm(self):
        QMessageBox.information(self.app.parent(), "Exportar", "Función en desarrollo.")