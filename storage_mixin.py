# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: gestión de almacenamiento — discos (crear/redimensionar/
eliminar), CD/DVD, y orden de arranque. Incluye dos pares de métodos
duplicados heredados del archivo original (_get_cdrom_path,
configure_boot_order, _save_boot_order aparecen dos veces): Python usa la
segunda definición y descarta la primera silenciosamente. Se conserva tal
cual para no cambiar comportamiento; es candidato a limpieza aparte.
"""
import os
import re
import json
import subprocess
import uuid
import configparser
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QFileDialog, QInputDialog, QListWidgetItem,
    QLineEdit, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QFormLayout,
)

import vm_config
from vm_config import load_vm_config, save_vm_config
from dialogs import DiskCreationDialog
from workers import _qemu_safe_identifier


class StorageMixin:
    def manage_disks(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Discos", "Selecciona una máquina virtual.")
            return
        vm_dir = self.current_vm_dir
        state = self._runtime_state(os.path.basename(vm_dir))
        disks = self._get_vm_disk_entries(vm_dir)
        lines = [f"{i}. {d['name']} — {d['format']} — {d['size']}" for i, d in enumerate(disks, 1)]
        text = "Discos de esta VM:\n\n" + ("\n".join(lines) if lines else "No hay discos registrados.")
        box = QMessageBox(self)
        box.setWindowTitle("💾 Administrador de discos")
        box.setText(text)
        create_btn = box.addButton("➕ Crear disco", QMessageBox.ButtonRole.AcceptRole)
        resize_btn = box.addButton("↔ Redimensionar", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == create_btn:
            if state != "stopped":
                QMessageBox.warning(self, "Discos", "Apaga la VM antes de crear discos nuevos.")
                return
            self.create_vm_disk()
        elif clicked == resize_btn:
            self.resize_vm_disk()

    def _get_vm_disk_entries(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        entries = []
        try:
            cfg = load_vm_config(vm_dir)
            primary_ext = cfg.get("disk_ext", "qcow2")
        except Exception:
            primary_ext = "qcow2"
        candidates = []
        primary = os.path.join(vm_dir, f"vm_disk.{primary_ext}")
        if os.path.isfile(primary):
            candidates.append(primary)
        for name in sorted(os.listdir(vm_dir)):
            if name.startswith(("disk_", "sata_", "nvme_", "hd_", "floppy_")) and os.path.isfile(os.path.join(vm_dir, name)):
                candidates.append(os.path.join(vm_dir, name))
        for path in candidates:
            try:
                result = subprocess.run(["qemu-img", "info", "--output=json", path], capture_output=True, text=True, timeout=10, check=True)
                info = json.loads(result.stdout)
                virtual = info.get("virtual-size", 0)
                size = f"{virtual / 1024**3:.1f} GiB" if virtual else "?"
                fmt = info.get("format", os.path.splitext(path)[1].lstrip("."))
            except Exception:
                size = "?"
                fmt = os.path.splitext(path)[1].lstrip(".")
            entries.append({"name": os.path.basename(path), "path": path, "format": fmt, "size": size})
        return entries

    def create_vm_disk(self):
        vm_dir = self.current_vm_dir
        if not vm_dir:
            QMessageBox.information(self, "Disco", "Primero selecciona una máquina virtual.")
            return

        # Una sola ventana para todos los datos del nuevo disco.
        dialog = DiskCreationDialog(self, "sata")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        self._create_virtual_disk_from_values(vm_dir, values, "sata")
        self.refresh_boot_order_choices()

    def _create_virtual_disk_from_values(self, vm_dir, values, devtype="sata"):
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", values["name"] or "datos")
        # Prefijo neutro para el archivo del disco. Coherente con la
        # interfaz: el usuario ve "Disco Duro", no "SATA".
        prefix = {"sata": "hd_", "nvme": "hd_", "floppy": "floppy_"}.get(devtype, "disk_")
        if not name.startswith(prefix):
            name = prefix + name
        size = values["size"]
        fmt = values["format"]
        disk_type = values["type"]
        if devtype == "floppy":
            fmt = "raw"
            size = size or "1.44M"
            disk_type = "fixed"
        ext = "img" if fmt == "raw" else fmt
        path = os.path.abspath(os.path.join(vm_dir, name + "." + ext))

        # Evitar dos registros físicos para el mismo dispositivo.
        try:
            for existing_name, existing_type, existing_path in self._storage_entries_with_types(vm_dir):
                if os.path.abspath(existing_path) == path or existing_name == os.path.basename(path):
                    QMessageBox.warning(self, "Dispositivo existente", f"Ese dispositivo ya está registrado:\n\n{existing_name}")
                    return
        except Exception:
            pass
        if os.path.exists(path):
            QMessageBox.warning(self, "Existe", f"Ya existe ese dispositivo:\n{os.path.basename(path)}")
            return

        cmd = ["qemu-img", "create", "-f", fmt]
        # Expandible = sin preasignación. Fijo = preasignación completa.
        if disk_type == "fixed":
            cmd += ["-o", "preallocation=full"]
        elif fmt == "qcow2":
            cmd += ["-o", "preallocation=off"]
        cmd += [path, size]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
            self.log_message(f"==> Dispositivo {devtype.upper()} creado: {os.path.basename(path)} ({size}, {disk_type}, {fmt.upper()})")
            self._register_storage_device(os.path.basename(path), path, devtype)
            # Crear un dispositivo de almacenamiento siempre actualiza también el orden de arranque.
            self.refresh_boot_order_choices()
            QMessageBox.information(
                self, "Dispositivo creado",
                f"Se creó correctamente:\n\n{os.path.basename(path)}\n\n"
                f"Tamaño virtual: {size}\nTipo: {'Fijo' if disk_type == 'fixed' else 'Expandible'}\nFormato: {fmt.upper()}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Crear dispositivo", f"No se pudo crear el dispositivo.\n\n{e}")

    def resize_vm_disk(self):
        disks = self._get_vm_disk_entries()
        if not disks:
            QMessageBox.information(self, "Discos", "No hay discos para redimensionar.")
            return
        names = [d["name"] for d in disks]
        name, ok = QInputDialog.getItem(self, "Redimensionar disco", "Selecciona el disco:", names, 0, False)
        if not ok:
            return
        disk = next(d["path"] for d in disks if d["name"] == name)
        new_size, ok = QInputDialog.getText(self, "Redimensionar disco", "Nuevo tamaño (ej. 120G, 200G, 1T):", QLineEdit.EchoMode.Normal, "")
        if not ok or not new_size.strip():
            return
        try:
            subprocess.run(["qemu-img", "resize", disk, new_size.strip()], check=True, capture_output=True, text=True, timeout=30)
            QMessageBox.information(self, "Disco", "Disco redimensionado correctamente.\n\nSi aumentaste el disco, amplía también la partición/volumen dentro del sistema invitado.")
        except Exception as e:
            QMessageBox.critical(self, "Redimensionar", f"No se pudo redimensionar el disco.\n\n{e}")

    def refresh_boot_order_choices(self):
        # El orden de arranque se administra exclusivamente desde Almacenamiento.
        # Ya no existe un control separado/redundante en la configuración.
        if hasattr(self, "storage_list"):
            self.refresh_storage_ui()

    def _storage_devices_all(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        try:
            data = load_vm_config(vm_dir)
            extra = data.get("extra") or {}
            devices = extra.get("storage_devices", [])
            devices = devices if isinstance(devices, list) else []
        except Exception:
            data, extra, devices = {}, {}, []

        changed = False
        # Migra dispositivos sin ID y normaliza IDs antiguos para que QEMU los acepte.
        for d in devices:
            current_id = str(d.get("id") or "")
            normalized_id = _qemu_safe_identifier(current_id, "dev") if current_id else "dev_" + uuid.uuid4().hex[:12]
            if current_id != normalized_id:
                d["id"] = normalized_id
                changed = True

        # Descubre discos que ya existen en la carpeta de la VM pero no quedaron registrados
        # en storage_devices. Esto corrige VMs creadas con versiones anteriores y mantiene
        # el árbol de almacenamiento consistente con Información.
        registered_paths={os.path.abspath(d.get("path","")) for d in devices if d.get("path")}
        try:
            for name in sorted(os.listdir(vm_dir)):
                path=os.path.join(vm_dir, name)
                if not os.path.isfile(path) or os.path.abspath(path) in registered_paths:
                    continue
                low=name.lower()
                if not low.endswith((".qcow2", ".qcow", ".img", ".raw", ".vdi", ".vmdk", ".vhd", ".vhdx")):
                    continue
                if low.startswith("nvme_"):
                    typ="nvme"
                elif low.startswith("floppy_"):
                    typ="floppy"
                else:
                    # "hd_", "sata_", "disk_" y cualquier otro → sata
                    typ="sata"
                devices.append({"id":"dev_" + uuid.uuid4().hex[:12], "name":name, "path":os.path.abspath(path), "device":typ})
                registered_paths.add(os.path.abspath(path))
                changed=True
        except Exception:
            pass

        # Migra una configuración antigua con cdrom_path a una unidad óptica real.
        legacy_cd = extra.get("cdrom_path", "")
        if legacy_cd and not any(d.get("device") == "cdrom" for d in devices):
            devices.append({"id":"dev_" + uuid.uuid4().hex[:12], "name":"CD/DVD 1", "path":os.path.abspath(legacy_cd), "device":"cdrom"})
            changed=True

        if changed and vm_dir == self.current_vm_dir:
            self._write_storage_devices(devices)
        return devices

    def _write_storage_devices(self, devices):
        if not self.current_vm_dir:
            return
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        cfg = configparser.ConfigParser(interpolation=None); cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("extra"):
            cfg.add_section("extra")
        try:
            extra = json.loads(cfg["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        extra["storage_devices"] = devices
        # Nueva estructura: ya no dependemos de un único cdrom_path.
        extra["cdrom_path"] = ""
        cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f: cfg.write(f)

    def _current_boot_order_tokens(self):
        if not self.current_vm_dir or not os.path.isdir(self.current_vm_dir):
            return ["network"]
        try:
            data = load_vm_config(self.current_vm_dir)
            saved = data.get("boot_order") or []
        except Exception:
            saved = []
        devices = self._storage_devices_all(self.current_vm_dir)
        disk_tokens = []
        cd_tokens = []
        for d in devices:
            ident = d.get("id")
            typ = d.get("device")
            path = d.get("path") or ""
            if typ in ("sata", "nvme", "floppy") and ident and path:
                if typ == "floppy" or os.path.isfile(path):
                    disk_tokens.append(f"disk:{ident}")
            elif typ == "cdrom" and ident:
                # Una unidad óptica existe aunque esté vacía; puede quedar en el orden
                # de arranque y recibir un medio más tarde.
                cd_tokens.append(f"cdrom:{ident}")
        # Los dispositivos NUEVOS (sin token previo guardado) se anteponen como
        # CD/DVD antes que discos: en una VM recién creada, el CD/DVD de
        # instalación debe quedar primero en el orden de arranque.
        available = cd_tokens + disk_tokens + ["network"]

        # Migra tokens genéricos de versiones antiguas a los dispositivos reales.
        legacy_disk = disk_tokens[0] if disk_tokens else None
        legacy_cd = cd_tokens[0] if cd_tokens else None
        normalized = []
        for t in saved:
            if t == "cdrom":
                if legacy_cd and legacy_cd not in normalized:
                    normalized.append(legacy_cd)
            elif t == "disk":
                if legacy_disk and legacy_disk not in normalized:
                    normalized.append(legacy_disk)
            elif t in available and t not in normalized:
                normalized.append(t)

        # Conserva el orden guardado y agrega al final cualquier dispositivo nuevo.
        order = [t for t in normalized if t in available]
        order += [t for t in available if t not in order]
        # Siempre debe existir Red/PXE como último recurso.
        if "network" not in order:
            order.append("network")

        # Persiste la versión canónica cuando ha cambiado. Esto evita que el orden
        # quede solo en la memoria de la interfaz y se pierda al reiniciar el programa.
        if order != saved and getattr(self, "current_vm_dir", None):
            try:
                self._save_boot_order(order)
            except Exception:
                pass
        return order

    def _boot_token_label(self, token):
        if token == "network": return "Red/PXE"
        if token == "cdrom": return "CD/DVD"
        if token.startswith("cdrom:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident), None)
            if dev:
                source = str(dev.get("source") or "")
                path=dev.get("path") or ""
                if source == "installer":
                    media = "🌐 descargar instalador al iniciar"
                elif source == "recovery":
                    media = "🌐 descargar System Recovery al iniciar"
                else:
                    media = os.path.basename(path) if path else "vacío"
                return f"CD/DVD — {dev.get('name') or 'CD/DVD'} — {media}"
            return "CD/DVD"
        if token == "disk": return "Disco principal"
        if token.startswith("disk:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident or os.path.basename(d.get("path",""))==ident), None)
            name=(dev.get("name") if dev else ident) or ident
            low=name.lower()
            typ=dev.get("device") if dev else "sata"
            if typ == "nvme":
                return "NVMe — " + name
            if typ == "floppy":
                return "Floppy — " + name
            return "SATA — " + name
        return token

    def _storage_entries_with_types(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        result = []
        seen = set()
        try:
            cfg = load_vm_config(vm_dir)
            devices = (cfg.get("extra") or {}).get("storage_devices", [])
        except Exception:
            devices = []
        for d in devices if isinstance(devices, list) else []:
            path = d.get("path", "")
            if not path or not os.path.isfile(path) or d.get("device") == "cdrom":
                continue
            typ = d.get("device", "sata")
            name = d.get("name") or os.path.basename(path)
            result.append((name, typ, path)); seen.add(os.path.abspath(path))
        # Compatibilidad con discos creados por versiones anteriores.
        for name in sorted(os.listdir(vm_dir)):
            low = name.lower(); path = os.path.join(vm_dir, name)
            if not os.path.isfile(path) or os.path.abspath(path) in seen:
                continue
            if low.startswith(("disk_", "sata_", "nvme_", "hd_", "floppy_", "vm_disk.")):
                if low.startswith("nvme_"): typ = "nvme"
                elif low.startswith("floppy_"): typ = "floppy"
                else: typ = "sata"
                result.append((name, typ, path))
        return result

    def refresh_storage_ui(self):
        if hasattr(self, "storage_tree"):
            self.storage_tree.clear()
            # UI simplificada: SATA y NVMe comparten un solo grupo
            # visual ("Disco Duro"). El bus real lo decide workers.py
            # según el SO invitado.
            groups = {
                "sata": QTreeWidgetItem(["💽 Disco Duro", "Disco"]),
                "nvme": None,  # se muestra dentro del grupo "sata"
                "floppy": QTreeWidgetItem(["💾 Disquetera", "FDC"]),
                "cdrom": QTreeWidgetItem(["📀 Unidades ópticas", "CD/DVD"]),
            }
            for d in self._storage_devices_all(self.current_vm_dir):
                typ=d.get("device","sata"); name=d.get("name") or os.path.basename(d.get("path","")) or typ.upper()
                path=d.get("path","")
                if typ == "cdrom":
                    source = str(d.get("source") or "")
                    if source == "installer":
                        media_label = "🌐 Descargar instalador de Internet al iniciar"
                        detail_label = "🌐 Instalador por Internet (se descargará al iniciar)"
                    elif source == "recovery":
                        media_label = "🌐 Descargar System Recovery al iniciar"
                        detail_label = "🌐 System Recovery (se descargará al iniciar)"
                    else:
                        media_label = os.path.basename(path) if path else "vacío"
                        detail_label = path or "Sin medio"
                    label=f"{name} — {media_label}"
                    item=QTreeWidgetItem([label, detail_label])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"kind":"cdrom","id":d.get("id"),"path":path,"source":source})
                    groups["cdrom"].addChild(item)
                elif typ in groups or typ == "nvme":
                    group_key = "sata" if typ == "nvme" else typ
                    item=QTreeWidgetItem([name, path])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"kind":"disk","id":d.get("id"),"path":path,"device":typ})
                    groups[group_key].addChild(item)
            for key in ("sata","nvme","floppy","cdrom"):
                root=groups.get(key)
                # Algunos grupos pueden ser None tras fusiones
                # (por ejemplo, "nvme" se muestra bajo "sata").
                if root is None:
                    continue
                if root.childCount() or key=="cdrom":
                    self.storage_tree.addTopLevelItem(root); root.setExpanded(True)

        if not hasattr(self, "storage_list"):
            return
        self.storage_list.blockSignals(True); self.storage_list.clear()
        for token in self._current_boot_order_tokens():
            item=QListWidgetItem(self._boot_token_label(token)); item.setData(Qt.ItemDataRole.UserRole, token); self.storage_list.addItem(item)
        if self.storage_list.count(): self.storage_list.setCurrentRow(0)
        self.storage_list.blockSignals(False)

    def _boot_order_from_list(self):
        if not getattr(self, "current_vm_dir", None) or not hasattr(self, "storage_list"):
            return
        order = [self.storage_list.item(k).data(Qt.ItemDataRole.UserRole) for k in range(self.storage_list.count())]
        self._save_boot_order(order)

    def _get_cdrom_path(self):
        if not self.current_vm_dir:
            return ""
        try:
            data = load_vm_config(self.current_vm_dir)
            extra = data.get("extra") or {}
            return extra.get("cdrom_path", "")
        except Exception:
            return ""

    def move_storage_boot(self, delta):
        if not hasattr(self, "storage_list") or not self.current_vm_dir:
            return
        i = self.storage_list.currentRow(); j = i + delta
        if i < 0 or j < 0 or j >= self.storage_list.count():
            return
        item = self.storage_list.takeItem(i)
        self.storage_list.insertItem(j, item)
        self.storage_list.setCurrentRow(j)
        self._boot_order_from_list()

    def remove_storage_device(self):
        if not hasattr(self, "storage_list"): return
        item=self.storage_list.currentItem()
        if not item: return
        token=item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(self,"Almacenamiento","Para quitar un dispositivo usa el botón 🗑 Eliminar del árbol de Almacenamiento. El orden de arranque solo controla prioridad.")

    def delete_storage_device(self):
        if not self.current_vm_dir or not hasattr(self, "storage_tree"):
            QMessageBox.information(self, "Almacenamiento", "Selecciona una máquina virtual y un dispositivo."); return
        item=self.storage_tree.currentItem(); meta=item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(meta, dict) or not meta.get("kind"):
            QMessageBox.information(self,"Almacenamiento","Selecciona un dispositivo concreto, no el controlador."); return
        devices=self._storage_devices_all(self.current_vm_dir)
        dev=next((d for d in devices if d.get("id")==meta.get("id")),None)
        if not dev:
            QMessageBox.warning(self,"Almacenamiento","No se encontró el dispositivo seleccionado."); return
        typ=dev.get("device")
        path=os.path.abspath(dev.get("path")) if dev.get("path") else ""
        if typ == "cdrom":
            msg=f"¿Quitar la unidad {dev.get('name','CD/DVD')} de la VM?\n\nEl medio no se eliminará del host."
            if QMessageBox.question(self,"Eliminar CD/DVD",msg,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes: return
            devices=[d for d in devices if d.get("id")!=dev.get("id")]
            self._write_storage_devices(devices)
        else:
            if not path or not os.path.isfile(path):
                QMessageBox.warning(self,"Dispositivo","El archivo seleccionado ya no existe en el host."); return
            box=QMessageBox(self); box.setWindowTitle("Eliminar dispositivo"); box.setText(f"¿Qué deseas hacer con '{os.path.basename(path)}'?")
            box.addButton("Quitar de la VM",QMessageBox.ButtonRole.AcceptRole); delb=box.addButton("Eliminar también el archivo",QMessageBox.ButtonRole.DestructiveRole); cancel=box.addButton("Cancelar",QMessageBox.ButtonRole.RejectRole); box.exec()
            if box.clickedButton()==cancel: return
            devices=[d for d in devices if d.get("id")!=dev.get("id")]; self._write_storage_devices(devices)
            if box.clickedButton()==delb: os.remove(path)
        # elimina el token correspondiente del orden guardado y vuelve a sincronizar ambos paneles
        old=[t for t in self._current_boot_order_tokens() if t != (f"cdrom:{dev.get('id')}" if typ=="cdrom" else f"disk:{dev.get('id')}" )]
        self._save_boot_order(old)
        self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()

    def _unregister_storage_path(self, path):
        devices=self._storage_devices_all(self.current_vm_dir)
        devices=[d for d in devices if os.path.abspath(d.get("path","")) != os.path.abspath(path)]
        self._write_storage_devices(devices)

    def _ensure_storage_target_vm(self):
        """Crea/guarda una VM provisional cuando el usuario está en Nueva VM y quiere añadir almacenamiento."""
        if self._vm_is_selected():
            return True
        name = self.input_vm_name.text().strip() if hasattr(self, "input_vm_name") else ""
        if not name:
            name, ok = QInputDialog.getText(self, "Nueva máquina virtual", "Nombre de la máquina virtual:")
            if not ok or not name.strip():
                return False
            name = name.strip()
            self.input_vm_name.setText(name)
        safe = vm_config.vm_folder_name(name)
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, safe)
        if os.path.exists(vm_dir):
            QMessageBox.warning(self, "Nueva máquina virtual", f"Ya existe una máquina virtual con ese nombre:\n\n{safe}\n\nSelecciona esa VM o elige otro nombre.")
            return False
        try:
            os.makedirs(vm_dir, exist_ok=False)
            os_type = self.combo_main_os.currentData() if hasattr(self, "combo_main_os") else "linux"
            ram = f"{self.slider_ram.value()}G" if hasattr(self, "slider_ram") else "4G"
            cores = self.slider_cores.value() if hasattr(self, "slider_cores") else 2
            firmware = self.combo_firmware.currentData() if hasattr(self, "combo_firmware") else "bios"
            secure = self.check_secure_boot.isChecked() if hasattr(self, "check_secure_boot") else False
            tpm = self.check_tpm.isChecked() if hasattr(self, "check_tpm") else False
            save_vm_config(
                vm_dir, name, os_type, ram, cores, "40G", "dynamic", "qcow2", "qcow2", {"cpu_model": self.combo_cpu_model.currentData() if hasattr(self, "combo_cpu_model") else "auto"},
                firmware=firmware, secure_boot=secure, tpm=tpm, boot_device="cdrom",
                network_model=(self.combo_network.currentData() if hasattr(self, "combo_network") else "virtio-net-pci"),
                audio_device=(self.combo_audio.currentData() if hasattr(self, "combo_audio") else "intel-hda"),
                network_mode=(self.combo_network_mode.currentData() if hasattr(self, "combo_network_mode") else "nat"),
                network_interface="", network_count=1,
                graphics_mode=(self.combo_graphics.currentData() if hasattr(self, "combo_graphics") else "auto"),
                graphics_vram=(self.combo_graphics_vram.currentData() if hasattr(self, "combo_graphics_vram") else "256M"),
                boot_order=["cdrom", "disk", "network"],
                network_devices=(self._network_devices() if hasattr(self, "_network_devices") else []),
                passthrough_devices=getattr(self, "_passthrough_saved", []),
                chipset=(self.combo_chipset.currentData() if hasattr(self, "combo_chipset") else "pc"),
            )
            self.current_vm_dir = vm_dir
            self._set_vm_status("saved")
            self.refresh_vm_list()
            self.refresh_storage_ui()
            self._update_manager_details()
            self.log_message(f"==> VM creada provisionalmente para administrar almacenamiento: {name}")
            return True
        except Exception as e:
            try:
                if os.path.isdir(vm_dir) and not os.listdir(vm_dir):
                    os.rmdir(vm_dir)
            except Exception:
                pass
            QMessageBox.critical(self, "Nueva máquina virtual", f"No se pudo preparar la máquina virtual.\n\n{e}")
            return False

    def create_storage_device(self, devtype):
        if not self._ensure_storage_target_vm():
            return
        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        if state != "stopped":
            QMessageBox.warning(self, "Almacenamiento", "Apaga la VM antes de modificar sus dispositivos de almacenamiento.")
            return

        os_type = self.combo_main_os.currentData() if hasattr(self, "combo_main_os") else "linux"
        os_version = ""
        distro = ""
        win_ver = "Windows 11"
        try:
            if os_type == "macos":
                os_version = self.os_options[self.combo_macos_ver.currentIndex()][0]
            elif os_type == "windows":
                win_ver = self.combo_win_ver.currentText()
            else:
                distro = self.combo_lin_distro.currentText()
        except Exception:
            pass

        dialog = DiskCreationDialog(self, devtype, os_type, os_version, distro, win_ver)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()

        if devtype == "cdrom":
            mode = values.get("cd_mode", "empty")
            try:
                path = ""
                if mode == "existing":
                    path = values.get("path", "")
                elif mode == "installer":
                    # Igual que macOS Recovery: no descargamos al crear la unidad.
                    # Se marca el medio y la descarga comenzará al pulsar Iniciar.
                    path = ""
                elif mode == "recovery":
                    # El Recovery se descarga al iniciar la VM, no al crear la unidad óptica.
                    path = ""
                source = mode if mode in ("installer", "recovery") else ""
                ident = self._register_cdrom_device(values.get("name") or "CD/DVD", path, source=source)
                self.log_message(f"==> Unidad CD/DVD creada: {values.get('name') or 'CD/DVD'}")
                self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
            except Exception as e:
                QMessageBox.critical(self, "CD/DVD", f"No se pudo configurar la unidad óptica.\n\n{e}")
                return
            return

        if values.get("existing"):
            self._attach_existing_storage(values, devtype)
        else:
            self._create_virtual_disk_from_values(self.current_vm_dir, values, devtype)
        self.refresh_boot_order_choices()

    def _register_storage_device(self, name, path, devtype):
        devices=self._storage_devices_all(self.current_vm_dir)
        ap=os.path.abspath(path) if path else ""
        # Evita duplicados por ruta solo para discos; CD/DVD pueden tener el mismo ISO en varias unidades.
        if devtype != "cdrom":
            devices=[d for d in devices if os.path.abspath(d.get("path","")) != ap]
        devices.append({"id":"dev_" + uuid.uuid4().hex[:12],"name":name,"path":ap,"device":devtype})
        self._write_storage_devices(devices)

    def _register_cdrom_device(self, name, path="", source=""):
        devices=self._storage_devices_all(self.current_vm_dir)
        base=name or "CD/DVD"
        names={str(d.get("name") or "") for d in devices if d.get("device")=="cdrom"}
        final_name=base
        n=2
        while final_name in names:
            final_name=f"{base} {n}"
            n+=1
        entry={"id":"dev_" + uuid.uuid4().hex[:12],"name":final_name,"path":os.path.abspath(path) if path else "","device":"cdrom"}
        if source:
            entry["source"] = source
        devices.append(entry)
        self._write_storage_devices(devices)
        return entry["id"]

    def _update_cdrom_device(self, ident, path, source=None):
        """Actualiza una unidad CD/DVD y mantiene sincronizada la fuente del medio.

        Si el usuario cambia de un instalador por Internet a un ISO/IMG/DMG
        existente, hay que quitar explícitamente source=installer; de lo contrario
        el arranque volvería a considerar la unidad como un instalador pendiente
        y descargaría otra ISO aunque ya tenga una ruta válida.
        """
        devices=self._storage_devices_all(self.current_vm_dir)
        for d in devices:
            if d.get("id")==ident:
                d["path"]=os.path.abspath(path) if path else ""
                if source is not None:
                    if source:
                        d["source"] = source
                    else:
                        d.pop("source", None)
                break
        self._write_storage_devices(devices)

    def _get_cdrom_path(self):
        for d in self._storage_devices_all(self.current_vm_dir):
            if d.get("device")=="cdrom": return d.get("path","")
        return ""

    def _save_cdrom_path(self, path):
        # Compatibilidad: actualiza la primera unidad óptica existente; si no existe, crea una.
        devices=self._storage_devices_all(self.current_vm_dir)
        cd=next((d for d in devices if d.get("device")=="cdrom"),None)
        if cd:
            cd["path"]=os.path.abspath(path) if path else ""
        else:
            devices.append({"id":"dev_" + uuid.uuid4().hex[:12],"name":"CD/DVD 1","path":os.path.abspath(path) if path else "","device":"cdrom"})
        self._write_storage_devices(devices)

    def configure_boot_order(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Arranque", "Primero crea o selecciona una máquina virtual."); return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        tokens=self._current_boot_order_tokens(); dialog=QDialog(self); dialog.setWindowTitle("⚙ Orden de dispositivos de arranque"); dialog.resize(500,380)
        layout=QVBoxLayout(dialog); layout.addWidget(QLabel("El primero será el dispositivo que QEMU/UEFI intentará arrancar primero."))
        lst=QListWidget(); layout.addWidget(lst,1)
        for token in tokens:
            it=QListWidgetItem(self._boot_token_label(token)); it.setData(Qt.ItemDataRole.UserRole,token); lst.addItem(it)
        row=QHBoxLayout(); up=QPushButton("⬆ Subir"); down=QPushButton("⬇ Bajar"); row.addWidget(up); row.addWidget(down); row.addStretch(); layout.addLayout(row)
        def move(delta):
            i=lst.currentRow(); j=i+delta
            if i<0 or j<0 or j>=lst.count(): return
            item=lst.takeItem(i); lst.insertItem(j,item); lst.setCurrentRow(j)
        up.clicked.connect(lambda: move(-1)); down.clicked.connect(lambda: move(1))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel); layout.addWidget(buttons); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        if dialog.exec()!=QDialog.DialogCode.Accepted: return
        self._save_boot_order([lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(lst.count())]); self.refresh_storage_ui()

    def _save_boot_order(self, order):
        if not self.current_vm_dir: return
        cfg_path=os.path.join(self.current_vm_dir,"vm_config.ini"); cfg=configparser.ConfigParser(interpolation=None); cfg.read(cfg_path,encoding="utf-8")
        if not cfg.has_section("hardware"): cfg.add_section("hardware")
        cfg.set("hardware","boot_order",json.dumps(order)); first=order[0] if order else "disk"
        cfg.set("hardware","boot_device","cdrom" if first.startswith("cdrom") else ("network" if first=="network" else "disk"))
        with open(cfg_path,"w",encoding="utf-8") as f: cfg.write(f)

    def configure_boot_order(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Arranque", "Primero crea o selecciona una máquina virtual.")
            return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        tokens = self._current_boot_order_tokens()
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ Orden de dispositivos de arranque")
        dialog.resize(430, 360)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("El primero será el dispositivo que QEMU/UEFI intentará arrancar primero."))
        lst = QListWidget()
        layout.addWidget(lst, 1)
        for token in tokens:
            lst.addItem(self._boot_token_label(token))
            lst.item(lst.count() - 1).setData(Qt.ItemDataRole.UserRole, token)
        row = QHBoxLayout()
        up = QPushButton("⬆ Subir")
        down = QPushButton("⬇ Bajar")
        row.addWidget(up)
        row.addWidget(down)
        row.addStretch()
        layout.addLayout(row)
        def move(delta):
            i = lst.currentRow()
            j = i + delta
            if i < 0 or j < 0 or j >= lst.count():
                return
            item = lst.takeItem(i)
            lst.insertItem(j, item)
            lst.setCurrentRow(j)
        up.clicked.connect(lambda: move(-1))
        down.clicked.connect(lambda: move(1))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_order = [lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(lst.count())]
        self._save_boot_order(new_order)
        self.refresh_boot_order_choices()

    def _save_boot_order(self, order):
        if not self.current_vm_dir:
            return
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("hardware"):
            cfg.add_section("hardware")
        cfg.set("hardware", "boot_order", json.dumps(order))
        first = order[0] if order else "disk"
        cfg.set("hardware", "boot_device", "cdrom" if str(first).startswith("cdrom") else ("network" if first == "network" else "disk"))
        with open(cfg_path, "w", encoding="utf-8") as f:
            cfg.write(f)
        self.log_message("==> Orden de arranque guardado: " + " → ".join(self._boot_token_label(x) for x in order))

    def manage_cdrom(self):
        if not self._vm_is_selected():
            QMessageBox.information(self,"CD / DVD","Selecciona una máquina virtual."); return
        cds=[d for d in self._storage_devices_all(self.current_vm_dir) if d.get("device")=="cdrom"]
        if not cds:
            QMessageBox.information(self,"CD / DVD","Esta VM no tiene unidades CD/DVD."); return
        names=[f"{d.get('name','CD/DVD')} — {os.path.basename(d.get('path','')) if d.get('path') else 'vacío'}" for d in cds]
        name,ok=QInputDialog.getItem(self,"Unidad CD/DVD","Selecciona la unidad:",names,0,False)
        if not ok:return
        cd=cds[names.index(name)]; ident=cd.get('id'); state=self._runtime_state(os.path.basename(self.current_vm_dir))
        device_id=f"cd{cds.index(cd)}"
        if state=="stopped":
            dialog=DiskCreationDialog(self,"cdrom",os_type=self.combo_main_os.currentData() if hasattr(self,'combo_main_os') else 'linux',initial_path=cd.get('path',''), initial_name=cd.get('name','CD/DVD'))
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            v=dialog.values(); mode=v.get('cd_mode','empty')
            try:
                path=''
                if mode=='existing':
                    path=v.get('path','')
                    # Un ISO indicado manualmente deja de ser un instalador
                    # automático: limpiar source evita una descarga al arrancar.
                    self._update_cdrom_device(ident, path, source='')
                elif mode=='installer':
                    # La descarga se realiza al iniciar la VM.
                    self._update_cdrom_device(ident, '', source='installer')
                elif mode=='recovery':
                    # Recovery mantiene su flujo de descarga al iniciar.
                    self._update_cdrom_device(ident, '', source='recovery')
                self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
            except Exception as e: QMessageBox.critical(self,'CD/DVD',str(e))
            return
        current=cd.get('path','')
        if QMessageBox.question(self,"CD / DVD",f"¿Expulsar el medio de '{cd.get('name','CD/DVD')}'?\n\nEl archivo no se borrará.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            try:
                self._qmp_hmp(self.current_vm_dir,f"eject -f {device_id}"); QMessageBox.information(self,"CD/DVD","Medio expulsado.")
            except Exception as e: QMessageBox.warning(self,"CD/DVD",str(e))
            return
        iso,_=QFileDialog.getOpenFileName(self,"Seleccionar ISO","","Imágenes ISO (*.iso *.img *.dmg);;Todos los archivos (*)")
        if not iso:return
        try:
            self._qmp_hmp(self.current_vm_dir,f"change {device_id} {iso}"); self._update_cdrom_device(ident,iso); self.refresh_storage_ui(); self._update_manager_details(); QMessageBox.information(self,"CD/DVD","Medio cambiado en caliente.")
        except Exception as e: QMessageBox.critical(self,"CD/DVD",str(e))

    def modify_storage_device(self):
        if not self._ensure_storage_target_vm() or not hasattr(self, 'storage_tree'):
            QMessageBox.information(self, 'Almacenamiento', 'Selecciona o crea una máquina virtual.')
            return
        if self._runtime_state(os.path.basename(self.current_vm_dir)) != 'stopped':
            QMessageBox.warning(self, 'Almacenamiento', 'Apaga la VM antes de modificar un dispositivo de almacenamiento.')
            return
        item = self.storage_tree.currentItem()
        if not item or not item.data(0, Qt.ItemDataRole.UserRole):
            QMessageBox.information(self, 'Modificar dispositivo', 'Selecciona un dispositivo concreto en el árbol.')
            return
        meta = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(meta, dict) and meta.get("kind") == "cdrom":
            ident = meta.get("id")
            cd = next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident), None)
            if not cd:
                QMessageBox.information(self,'Modificar dispositivo','No se encontró la unidad CD/DVD seleccionada.'); return
            dialog = DiskCreationDialog(self, 'cdrom',
                                        os_type=self.combo_main_os.currentData() if hasattr(self, 'combo_main_os') else 'linux',
                                        initial_path=cd.get('path',''), initial_name=cd.get('name','CD/DVD'))
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = dialog.values()
            if values.get('cd_mode') == 'existing':
                # Al elegir manualmente un archivo existente, se cancela cualquier
                # marca anterior de descarga automática.
                self._update_cdrom_device(ident, values.get('path', ''), source='')
            elif values.get('cd_mode') == 'empty':
                self._update_cdrom_device(ident, '', source='')
            elif values.get('cd_mode') in ('installer', 'recovery'):
                # No descargamos al modificar: la descarga queda programada para
                # el próximo arranque, igual que al crear la unidad.
                source = values['cd_mode']
                self._update_cdrom_device(ident, '', source=source)
            devices=self._storage_devices_all(self.current_vm_dir)
            for d in devices:
                if d.get('id')==ident: d['name']=values.get('name') or d.get('name','CD/DVD')
            self._write_storage_devices(devices)
            self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details(); return

        path = meta.get("path") if isinstance(meta, dict) else item.data(0, Qt.ItemDataRole.UserRole)
        info = None
        for name, typ, dpath in self._storage_entries_with_types(self.current_vm_dir):
            if os.path.abspath(dpath) == os.path.abspath(path):
                info = (name, typ, dpath); break
        if not info:
            QMessageBox.information(self, 'Modificar dispositivo', 'No se encontró la información del dispositivo seleccionado.')
            return
        old_name, devtype, old_path = info
        dialog = QDialog(self)
        dialog.setWindowTitle('✏ Modificar dispositivo de almacenamiento')
        dialog.resize(620, 300)
        lay = QVBoxLayout(dialog)
        form = QFormLayout()
        name_edit = QLineEdit(old_name)
        path_edit = QLineEdit(old_path)
        browse = QPushButton('📁 Buscar…')
        row = QHBoxLayout(); row.addWidget(path_edit, 1); row.addWidget(browse)
        form.addRow('Nombre:', name_edit)
        form.addRow('Dispositivo:', QLabel(devtype.upper()))
        form.addRow('Archivo:', row)
        size_edit = QLineEdit('')
        size_edit.setPlaceholderText('Vacío = no cambiar; ejemplo: 120G')
        form.addRow('Nuevo tamaño:', size_edit)
        lay.addLayout(form)
        hint = QLabel('Puedes cambiar el archivo asociado y aumentar el tamaño del disco. El redimensionado no reduce el disco automáticamente.')
        hint.setWordWrap(True); hint.setStyleSheet('color:#666;')
        lay.addWidget(hint)
        buttons = QHBoxLayout(); buttons.addStretch(); cancel=QPushButton('Cancelar'); ok=QPushButton('Aplicar')
        cancel.clicked.connect(dialog.reject); ok.clicked.connect(dialog.accept); buttons.addWidget(cancel); buttons.addWidget(ok); lay.addLayout(buttons)
        def browse_path():
            fp, _ = QFileDialog.getOpenFileName(self, 'Seleccionar disco existente', os.path.dirname(old_path), 'Imágenes de disco (*.qcow2 *.img *.raw *.vdi *.vmdk);;Todos los archivos (*)')
            if fp: path_edit.setText(fp)
        browse.clicked.connect(browse_path)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_path = os.path.abspath(path_edit.text().strip())
        new_name = name_edit.text().strip() or os.path.basename(new_path)
        try:
            if not os.path.isfile(new_path):
                raise RuntimeError('El archivo seleccionado no existe.')
            if os.path.abspath(new_path) != os.path.abspath(old_path):
                self._unregister_storage_path(old_path)
                self._register_storage_device(new_name, new_path, devtype)
            else:
                # Actualizar nombre manteniendo ruta
                self._unregister_storage_path(old_path)
                self._register_storage_device(new_name, old_path, devtype)
            if size_edit.text().strip():
                if devtype == 'floppy':
                    raise RuntimeError('El tamaño de una disquetera se modifica recreando la imagen; aquí no se redimensiona.')
                subprocess.run(['qemu-img', 'resize', new_path, size_edit.text().strip()], check=True, capture_output=True, text=True, timeout=60)
            self.refresh_storage_ui(); self._update_manager_details()
            QMessageBox.information(self, 'Dispositivo modificado', 'El dispositivo se modificó correctamente.')
        except Exception as e:
            QMessageBox.critical(self, 'Modificar dispositivo', f'No se pudo modificar el dispositivo.\n\n{e}')

