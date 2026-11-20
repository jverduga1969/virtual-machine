import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt

from plugins.config_vm.plugin import scan_usb_devices


class HotplugDialog(QDialog):
    def __init__(self, app, vm_id, parent=None):
        super().__init__(parent)
        self.app = app
        self.vm_id = vm_id
        self.setWindowTitle("Conexión en Caliente (Hotplug)")
        self.resize(600, 450)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # --- Pestaña CD/DVD ---
        tab_cd = QWidget()
        l_cd = QVBoxLayout(tab_cd)
        l_cd.addWidget(QLabel("<b>Selecciona una unidad para gestionar su ISO:</b>"))

        self.list_cd = QListWidget()
        self.list_cd.setToolTip("Unidades de CD/DVD configuradas en la VM")
        self._refresh_cd_list()

        l_cd.addWidget(self.list_cd)

        b_cd_box = QHBoxLayout()
        btn_insert = QPushButton("📀 Insertar ISO...")
        btn_insert.setToolTip("Insertar una imagen ISO en la unidad de CD/DVD seleccionada")
        btn_insert.clicked.connect(self._insert_iso)
        btn_eject = QPushButton("⏏ Expulsar")
        btn_eject.setToolTip("Expulsar la imagen ISO de la unidad seleccionada")
        btn_eject.clicked.connect(self._eject_iso)
        b_cd_box.addWidget(btn_insert)
        b_cd_box.addWidget(btn_eject)
        l_cd.addLayout(b_cd_box)
        tabs.addTab(tab_cd, "CD / DVD")

        # --- Pestaña USB ---
        tab_usb = QWidget()
        l_usb = QVBoxLayout(tab_usb)
        l_usb.addWidget(QLabel("<b>Selecciona un dispositivo USB físico para pasar a la VM:</b>"))

        self.list_usb = QListWidget()
        self.list_usb.setToolTip("Dispositivos USB disponibles para conectar a la VM")
        self._refresh_usb()
        l_usb.addWidget(self.list_usb)

        btn_refresh = QPushButton("🔄 Refrescar lista USB")
        btn_refresh.setToolTip("Volver a escanear los dispositivos USB del host")
        btn_refresh.clicked.connect(self._refresh_usb)
        l_usb.addWidget(btn_refresh)

        b_usb_box = QHBoxLayout()
        btn_usb_connect = QPushButton("🔌 Conectar")
        btn_usb_connect.setToolTip("Conectar el dispositivo USB seleccionado a la VM")
        btn_usb_connect.clicked.connect(self._connect_usb)
        btn_usb_disconnect = QPushButton("✂ Desconectar")
        btn_usb_disconnect.setToolTip("Desconectar el dispositivo USB seleccionado de la VM")
        btn_usb_disconnect.clicked.connect(self._disconnect_usb)
        b_usb_box.addWidget(btn_usb_connect)
        b_usb_box.addWidget(btn_usb_disconnect)
        l_usb.addLayout(b_usb_box)
        tabs.addTab(tab_usb, "Dispositivos USB")

        layout.addWidget(tabs)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    # ---------- CD/DVD ----------

    def _get_current_drives(self, vm):
        drives = list(vm.get("optical_drives") or [])
        if not drives and vm.get("iso_path"):
            drives = [{"path": vm.get("iso_path"), "bus": vm.get("cdrom_bus", "sata"), "source_type": vm.get("iso_source_type", "Usar ISO/IMG/DMG existente")}]
        return drives

    def _refresh_cd_list(self):
        self.list_cd.clear()
        vm = self.app.get_vm(self.vm_id)
        optical_drives = self._get_current_drives(vm)

        if not optical_drives:
            item = QListWidgetItem("No hay unidades ópticas configuradas en esta VM.")
            self.list_cd.addItem(item)
            self.list_cd.setEnabled(False)
        else:
            self.list_cd.setEnabled(True)
            for i, drive in enumerate(optical_drives):
                path = drive.get('path', '')
                iso_name = os.path.basename(path) if path else "[Vacío]"
                item = QListWidgetItem(f"Unidad {i} ({drive.get('bus', 'sata')}) → {iso_name}")
                item.setData(Qt.ItemDataRole.UserRole, f"cdrom{i}")
                self.list_cd.addItem(item)

    def _insert_iso(self):
        item = self.list_cd.currentItem()
        if not item or not self.list_cd.isEnabled(): return
        cdrom_id = item.data(Qt.ItemDataRole.UserRole)
        if not cdrom_id: return

        iso_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes (*.iso *.img)")
        if iso_path:
            ok, msg = self.app.runner.hotplug_cdrom(self.vm_id, cdrom_id, iso_path)
            if ok:
                vm = self.app.get_vm(self.vm_id)
                idx = int(cdrom_id.replace("cdrom", ""))
                optical_drives = self._get_current_drives(vm)

                if not optical_drives:
                    optical_drives = [{"path": "", "bus": "sata"}]

                if idx < len(optical_drives):
                    optical_drives[idx]["path"] = iso_path
                    optical_drives[idx]["source_type"] = "Usar ISO/IMG/DMG existente"
                else:
                    optical_drives.append({"path": iso_path, "bus": "sata", "source_type": "Usar ISO/IMG/DMG existente"})

                updates = {
                    "optical_drives": optical_drives, 
                    "iso_path": iso_path,
                    "iso_source_type": "Usar ISO/IMG/DMG existente"
                }
                self.app.vm_repo.update(self.vm_id, updates)
                if isinstance(vm, dict):
                    vm.update(updates)

                QMessageBox.information(self, "Éxito", msg)
                self._refresh_cd_list()
            else:
                QMessageBox.critical(self, "Error", msg)

    def _eject_iso(self):
        item = self.list_cd.currentItem()
        if not item or not self.list_cd.isEnabled(): return
        cdrom_id = item.data(Qt.ItemDataRole.UserRole)
        if not cdrom_id: return

        ok, msg = self.app.runner.eject_cdrom(self.vm_id, cdrom_id)
        if ok:
            vm = self.app.get_vm(self.vm_id)
            idx = int(cdrom_id.replace("cdrom", ""))
            optical_drives = self._get_current_drives(vm)

            if idx < len(optical_drives):
                optical_drives[idx]["path"] = ""
                optical_drives[idx]["source_type"] = "Mantener vacío"

            updates = {
                "optical_drives": optical_drives,
                "iso_path": None,
                "iso_source_type": "Mantener vacío"
            }
            self.app.vm_repo.update(self.vm_id, updates)
            if isinstance(vm, dict):
                vm.update(updates)

            QMessageBox.information(self, "Éxito", msg)
            self._refresh_cd_list()
        else:
            QMessageBox.critical(self, "Error", msg)

    # ---------- USB ----------

    def _refresh_usb(self):
        self.list_usb.clear()
        devices = scan_usb_devices()
        try:
            connected = self.app.runner.get_connected_usb_devices(self.vm_id)
        except Exception:
            connected = []
        
        for d in devices:
            bus_addr = d.get("id", "")
            if not bus_addr: continue
            
            desc = d["desc"]
            if bus_addr in connected:
                desc = "🟢 [CONECTADO] " + desc
                
            item = QListWidgetItem(desc)
            item.setData(Qt.ItemDataRole.UserRole, bus_addr)
            self.list_usb.addItem(item)

    def _connect_usb(self):
        item = self.list_usb.currentItem()
        if not item: return
        bus_addr = item.data(Qt.ItemDataRole.UserRole)
        bus, addr = bus_addr.split(":")

        ok, msg = self.app.runner.hotplug_usb(self.vm_id, bus, addr)

        if ok:
            QMessageBox.information(self, "Éxito", msg)
            self._refresh_usb()
            return

        is_perm_error = (
            "failed to open" in msg.lower()
            or "permission denied" in msg.lower()
            or "access" in msg.lower()
            or "no materializ" in msg.lower()
        )
        is_busy_error = "busy" in msg.lower() or "in use" in msg.lower()

        if is_perm_error or is_busy_error:
            resp = QMessageBox.question(
                self, "Dispositivo ocupado / sin permisos",
                f"El dispositivo '{item.text()}' no pudo abrirse desde QEMU.\n\n"
                "Esto suele deberse a que el host (CachyOS) mantiene el dispositivo "
                "con permisos de root o lo tiene montado.\n\n"
                "¿Quieres intentar conceder acceso al device node con pkexec?\n"
                "(No se desvincula del host; solo se dan permisos al usuario.)\n\n"
                "⚠ Si es un pendrive montado, la VM podrá verlo pero podrías tener "
                "conflictos de escritura con el host. Cierra archivos antes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if resp == QMessageBox.StandardButton.Yes:
                detach_ok, detach_msg = self.app.runner._grant_usb_access(bus, addr)
                if not detach_ok:
                    QMessageBox.critical(
                        self, "Error",
                        f"No se pudo conceder acceso al USB:\n{detach_msg}"
                    )
                    return

                ok, msg = self.app.runner.hotplug_usb(self.vm_id, bus, addr)
                if ok:
                    QMessageBox.information(self, "Éxito", "Dispositivo conectado a la VM.")
                    self._refresh_usb()
                else:
                    QMessageBox.critical(
                        self, "Error",
                        f"Se concedió acceso al device node, pero QEMU sigue fallando:\n{msg}\n\n"
                        "Revisa el log de QEMU (busca '[QEMU ...]' en los logs de la app) "
                        "para ver el error real de libusb."
                    )
            return

        QMessageBox.critical(self, "Error", msg)

    def _disconnect_usb(self):
        item = self.list_usb.currentItem()
        if not item: return
        bus_addr = item.data(Qt.ItemDataRole.UserRole)
        bus, addr = bus_addr.split(":")

        ok, msg = self.app.runner.remove_usb(self.vm_id, bus, addr)
        if ok: 
            QMessageBox.information(self, "Éxito", msg)
            self._refresh_usb()
        else: 
            QMessageBox.critical(self, "Error", msg)