# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: configuración de dispositivos de red de la VM (agregar, editar,
quitar tarjetas de red; elegir bridge/TAP/interfaz según el modo de red).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox, QDialog

from network_utils import list_host_bridges, sanitize_tap_name
from dialogs import NetworkDeviceDialog


class NetworkConfigMixin:
    def update_network_options(self, preferred_interface=""):
        """Actualiza la selección de bridge/TAP/interfaz según el modo de red."""
        if not hasattr(self, "combo_network_interface"):
            return
        mode = self.combo_network_mode.currentData()
        self.combo_network_interface.blockSignals(True)
        self.combo_network_interface.clear()
        if mode == "bridge":
            bridges = list_host_bridges()
            for name, members in bridges:
                suffix = f" ({', '.join(members)})" if members else ""
                self.combo_network_interface.addItem(f"{name}{suffix}", name)
            self.label_network_target.setText("Bridge:")
            if preferred_interface:
                idx = self.combo_network_interface.findData(preferred_interface)
                if idx >= 0:
                    self.combo_network_interface.setCurrentIndex(idx)
            if self.combo_network_interface.count() == 0:
                self.combo_network_interface.addItem("No hay bridges Linux", "")
        elif mode == "tap":
            default_tap = sanitize_tap_name(self.input_vm_name.text().strip() if hasattr(self, "input_vm_name") else "vm")
            self.combo_network_interface.addItem(f"TAP automática: {default_tap}", default_tap)
            self.label_network_target.setText("TAP:")
            if preferred_interface:
                idx = self.combo_network_interface.findData(preferred_interface)
                if idx < 0:
                    self.combo_network_interface.addItem(preferred_interface, preferred_interface)
                    idx = self.combo_network_interface.findData(preferred_interface)
                self.combo_network_interface.setCurrentIndex(idx)
        else:
            self.combo_network_interface.addItem("Automático (NAT)", "")
            self.label_network_target.setText("Interfaz:")
        self.combo_network_interface.blockSignals(False)
        self.combo_network_interface.setEnabled(mode != "nat")
        self.combo_network_count.setEnabled(self.combo_main_os.currentData() != "macos")

    def _network_devices(self):
        return [self.network_device_data(i) for i in range(self.network_devices_list.count())]

    def network_device_data(self, index):
        item=self.network_devices_list.item(index)
        return item.data(Qt.ItemDataRole.UserRole) or {}

    def refresh_network_devices_ui(self, devices=None):
        devices = devices if isinstance(devices,list) and devices else [{"name":"Red 1","model":"virtio-net-pci","mode":"nat","interface":"","mac":""}]
        self.network_devices_list.clear()
        for i,d in enumerate(devices,1):
            d=dict(d); d.setdefault("name",f"Red {i}")
            mode={"nat":"NAT","bridge":"Bridge","tap":"TAP"}.get(d.get("mode"),d.get("mode","NAT"))
            label=f'{d.get("name")} — {d.get("model","virtio-net-pci")} — {mode}'
            if d.get("interface"): label += f' [{d.get("interface")}]'
            if d.get("mac"): label += f' — MAC {d.get("mac")}'
            _rules = d.get("hostfwd") or []
            if _rules:
                label += f' — 🔀 {len(_rules)} regla(s) NAT'
            it=QListWidgetItem(label); it.setData(Qt.ItemDataRole.UserRole,d); self.network_devices_list.addItem(it)

    def add_network_device(self):
        d=NetworkDeviceDialog(self).values() if False else None
        dlg=NetworkDeviceDialog(self, {"name":f"Red {self.network_devices_list.count()+1}","model":"virtio-net-pci","mode":"nat"})
        if dlg.exec()==QDialog.DialogCode.Accepted:
            self.network_devices_list.addItem(QListWidgetItem())
            item=self.network_devices_list.item(self.network_devices_list.count()-1); val=dlg.values(); item.setData(Qt.ItemDataRole.UserRole,val); self._render_network_item(item,val); self._update_vm_summary(); self._save_hardware_lists() if self.current_vm_dir else None; self._save_hardware_lists() if self.current_vm_dir else None

    def _render_network_item(self,item,d):
        mode={"nat":"NAT","bridge":"Bridge","tap":"TAP"}.get(d.get("mode"),d.get("mode","NAT"))
        txt=f'{d.get("name","Red")} — {d.get("model","virtio-net-pci")} — {mode}'
        if d.get("interface"): txt += f' [{d.get("interface")}]'
        if d.get("mac"): txt += f' — MAC {d.get("mac")}'
        _rules = d.get("hostfwd") or []
        if _rules:
            txt += f' — 🔀 {len(_rules)} regla(s) NAT'
        item.setText(txt)

    def edit_network_device(self):
        item=self.network_devices_list.currentItem()
        if not item: return
        dlg=NetworkDeviceDialog(self,item.data(Qt.ItemDataRole.UserRole) or {})
        if dlg.exec()==QDialog.DialogCode.Accepted:
            val=dlg.values(); item.setData(Qt.ItemDataRole.UserRole,val); self._render_network_item(item,val); self._update_vm_summary(); self._save_hardware_lists() if self.current_vm_dir else None

    def remove_network_device(self):
        row=self.network_devices_list.currentRow()
        if row>=0:
            self.network_devices_list.takeItem(row); self._update_vm_summary(); self._save_hardware_lists() if self.current_vm_dir else None
        if self.network_devices_list.count()==0: self.refresh_network_devices_ui()

