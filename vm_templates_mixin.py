# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: plantillas de VM (sin discos).

Marcador: vm_templates_v1

- Botón "💾 Plantilla" en el Resumen: guarda la configuración actual
  (hardware + perfil del SO) como plantilla reutilizable.
- Botón "➕ Nueva VM": si hay plantillas, muestra un menú con
  "Nueva VM en blanco" + cada plantilla.
- Al crear desde plantilla: se copia el .ini sanitizado, se cambia el
  nombre, se generan MACs nuevas y se abre la VM en Configuración →
  Almacenamiento para que el usuario añada disco + medio.

Las plantillas viven en BASE_VM_DIR/_templates/<nombre>.ini. Al ser
archivos .ini sueltos (no carpetas con vm_config.ini), no aparecen en
list_existing_vms() y por tanto no contaminan la lista lateral.
"""
import os
import re
import json
import shutil
import random
import configparser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QInputDialog, QLineEdit, QMenu, QMessageBox,
)

import vm_config


TEMPLATES_SUBDIR = "_templates"


class VmTemplatesMixin:

    # ------------------------------------------------------------------
    # Rutas
    # ------------------------------------------------------------------
    def _templates_dir(self):
        return os.path.join(vm_config.BASE_VM_DIR, TEMPLATES_SUBDIR)

    def _ensure_templates_dir(self):
        d = self._templates_dir()
        os.makedirs(d, exist_ok=True)
        return d

    def _list_templates(self):
        """Devuelve [(nombre_legible, ruta_ini), ...] ordenada."""
        d = self._templates_dir()
        if not os.path.isdir(d):
            return []
        out = []
        for f in sorted(os.listdir(d)):
            if not f.endswith(".ini"):
                continue
            display = f[:-4]
            out.append((display, os.path.join(d, f)))
        return out

    def _template_slug(self, display_name):
        """Nombre de archivo saneado para una plantilla."""
        return re.sub(r'[\\/:*?"<>|]', "_", str(display_name or "")).strip() or "plantilla"

    # ------------------------------------------------------------------
    # Sanitización
    # ------------------------------------------------------------------
    _TPL_DROP_EXTRA = (
        "storage_devices",
        "cdrom_path",
        "android_iso",
        "iso_path",
        "shared_folders",
        "notes",
        "autostart_on_launch",
        "group",
        "color",
    )

    def _sanitize_extra(self, extra):
        if not isinstance(extra, dict):
            return {}
        clean = dict(extra)
        for k in self._TPL_DROP_EXTRA:
            clean.pop(k, None)
        return clean

    def _sanitize_network_devices(self, devices):
        if not isinstance(devices, list):
            return []
        out = []
        for d in devices:
            if not isinstance(d, dict):
                continue
            nd = dict(d)
            nd.pop("mac", None)
            nd.pop("uuid", None)
            nd.pop("hostfwd", None)
            out.append(nd)
        return out

    def _new_mac(self):
        """MAC local unicast con el prefijo de QEMU (52:54:00:...)."""
        return ":".join(
            f"{b:02x}"
            for b in (0x52, 0x54, 0x00,
                      random.randint(0, 255),
                      random.randint(0, 255),
                      random.randint(0, 255))
        )

    # ------------------------------------------------------------------
    # Guardar plantilla desde la VM actual
    # ------------------------------------------------------------------
    def save_current_vm_as_template(self):
        if not self._vm_is_selected():
            QMessageBox.information(
                self, self.tr("Guardar como plantilla"),
                self.tr("Selecciona primero una máquina virtual."),
            )
            return

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            QMessageBox.warning(
                self, self.tr("Guardar como plantilla"),
                self.tr("Esta VM no tiene vm_config.ini todavía.\n\n"
                        "Configúrala y guárdala primero."),
            )
            return

        default_name = f"{vm_name} (plantilla)"
        tpl_name, ok = QInputDialog.getText(
            self, "Guardar como plantilla",
            f"Nombre para la plantilla basada en '{vm_name}':\n\n"
            "Se conservarán: hardware (CPU, RAM, chipset, firmware,\n"
            "gráficos, audio, red, consola, señalización), opciones\n"
            "avanzadas y perfil del SO.\n\n"
            "Se omitirán: discos, ISOs, carpetas compartidas, notas,\n"
            "MACs y reglas NAT. Al crear una VM desde la plantilla,\n"
            "esos datos se piden de nuevo.",
            QLineEdit.EchoMode.Normal,
            default_name,
        )
        if not ok or not tpl_name.strip():
            return
        tpl_name = tpl_name.strip()
        safe = self._template_slug(tpl_name)

        self._ensure_templates_dir()
        tpl_path = os.path.join(self._templates_dir(), f"{safe}.ini")

        if os.path.exists(tpl_path):
            resp = QMessageBox.question(
                self, self.tr("Ya existe"),
                self.tr("Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?").format(safe),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        try:
            cfg = configparser.ConfigParser(interpolation=None)
            cfg.read(cfg_path, encoding="utf-8")

            if cfg.has_section("general"):
                cfg.set("general", "name", tpl_name)

            if cfg.has_section("hardware"):
                try:
                    net_devs = json.loads(
                        cfg["hardware"].get("network_devices", "[]"))
                except Exception:
                    net_devs = []
                net_devs = self._sanitize_network_devices(net_devs)
                cfg.set("hardware", "network_devices",
                        json.dumps(net_devs, ensure_ascii=False))
                cfg.set("hardware", "passthrough_devices", "[]")
                cfg.set("hardware", "network_interface", "")
                # Reset boot_order: los IDs que lleva (p. ej.
                # "cdrom:dev_f0b8d2cb1a9d") apuntan a los storage_devices
                # de la VM original, que acabamos de limpiar de extra[].
                # Dejar esos IDs en la plantilla produciría un orden de
                # arranque con dispositivos inexistentes en la VM nueva.
                cfg.set("hardware", "boot_order",
                        json.dumps(["cdrom", "disk", "network"]))

            if cfg.has_section("extra"):
                try:
                    extra = json.loads(cfg["extra"].get("data", "{}"))
                except Exception:
                    extra = {}
                extra = self._sanitize_extra(extra)
                cfg.set("extra", "data",
                        json.dumps(extra, ensure_ascii=False))

            with open(tpl_path, "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Guardar como plantilla"),
                self.tr("No se pudo escribir la plantilla.\n\n{0}").format(e),
            )
            return

        try:
            self.log_message(f"==> Plantilla '{safe}' guardada en {tpl_path}")
        except Exception:
            pass

        QMessageBox.information(
            self, self.tr("Plantilla guardada"),
            self.tr("Plantilla '{0}' creada correctamente.\n\n"
                    "Aparecerá en el menú del botón '➕ Nueva VM'.").format(safe),
        )

    # ------------------------------------------------------------------
    # Botón "Nueva VM": muestra menú si hay plantillas
    # ------------------------------------------------------------------
    def _on_new_vm_clicked(self, checked=False, btn=None):
        tpls = self._list_templates()
        if not tpls:
            self.new_vm()
            return

        menu = QMenu(self)
        act_blank = QAction(self.tr("🆕 Nueva VM en blanco"), self)
        act_blank.triggered.connect(self.new_vm)
        menu.addAction(act_blank)
        menu.addSeparator()

        header = QAction(self.tr("Desde plantilla:"), self)
        header.setEnabled(False)
        menu.addAction(header)

        for disp, _path in tpls:
            a = QAction(f"📋 {disp}", self)
            a.triggered.connect(
                lambda _checked=False, n=disp: self.create_vm_from_template(n)
            )
            menu.addAction(a)

        target = btn if btn is not None else getattr(self, "btn_new_vm", None)
        try:
            if target is not None:
                pos = target.mapToGlobal(target.rect().bottomLeft())
                menu.exec(pos)
            else:
                menu.exec()
        except Exception:
            try:
                menu.exec()
            except Exception:
                self.new_vm()

    # ------------------------------------------------------------------
    # Crear VM desde plantilla
    # ------------------------------------------------------------------
    def create_vm_from_template(self, template_display_name):
        safe = self._template_slug(template_display_name)
        tpl_path = os.path.join(self._templates_dir(), f"{safe}.ini")
        if not os.path.isfile(tpl_path):
            QMessageBox.warning(
                self, self.tr("Crear desde plantilla"),
                self.tr("No encuentro la plantilla '{0}'.").format(template_display_name),
            )
            return

        # Sugerir nombre
        suggested = template_display_name
        if suggested.endswith(" (plantilla)"):
            suggested = suggested[: -len(" (plantilla)")]
        suggested = suggested.strip() or "VM"
        name = suggested
        existing = set(vm_config.list_existing_vms())
        i = 1
        while (name in existing
               or os.path.exists(os.path.join(
                   vm_config.BASE_VM_DIR,
                   vm_config.vm_folder_name(name)))):
            i += 1
            name = f"{suggested}-{i}"

        name, ok = QInputDialog.getText(
            self, "Crear VM desde plantilla",
            f"Nombre para la nueva VM (basada en la plantilla "
            f"'{template_display_name}'):",
            QLineEdit.EchoMode.Normal,
            name,
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        folder = vm_config.vm_folder_name(name)
        target_dir = os.path.join(vm_config.BASE_VM_DIR, folder)

        if os.path.exists(target_dir):
            resp = QMessageBox.question(
                self, self.tr("Ya existe"),
                self.tr("Ya existe una carpeta para '{0}'.\n\n"
                        "¿Reemplazarla? (se eliminará la existente)").format(name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                QMessageBox.warning(
                    self, self.tr("Crear desde plantilla"),
                    self.tr("No se pudo eliminar la carpeta existente.\n\n{0}").format(e),
                )
                return

        try:
            os.makedirs(target_dir, exist_ok=True)
            cfg = configparser.ConfigParser(interpolation=None)
            cfg.read(tpl_path, encoding="utf-8")

            if cfg.has_section("general"):
                cfg.set("general", "name", name)

            if cfg.has_section("hardware"):
                try:
                    net_devs = json.loads(
                        cfg["hardware"].get("network_devices", "[]"))
                except Exception:
                    net_devs = []
                for nd in net_devs:
                    if isinstance(nd, dict):
                        nd["mac"] = self._new_mac()
                cfg.set("hardware", "network_devices",
                        json.dumps(net_devs, ensure_ascii=False))

            with open(os.path.join(target_dir, "vm_config.ini"),
                      "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception as e:
            try:
                shutil.rmtree(target_dir)
            except Exception:
                pass
            QMessageBox.warning(
                self, self.tr("Crear desde plantilla"),
                self.tr("No se pudo crear la VM.\n\n{0}").format(e),
            )
            return

        try:
            if hasattr(self, "_invalidate_vm_config_cache"):
                self._invalidate_vm_config_cache(target_dir)
        except Exception:
            pass

        try:
            self.log_message(
                f"==> VM '{name}' creada desde plantilla "
                f"'{template_display_name}'."
            )
        except Exception:
            pass

        try:
            self.refresh_vm_list(select_name=folder)
            self.open_vm(folder)
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] No se pudo abrir la nueva VM: {e}")
            except Exception:
                pass

        # Ir a Configuración → Almacenamiento
        try:
            sidebar = getattr(self, "config_sidebar", None)
            if sidebar is not None:
                for i in range(sidebar.count()):
                    it = sidebar.item(i)
                    if it is None:
                        continue
                    if it.data(Qt.ItemDataRole.UserRole) == "Almacenamiento":
                        sidebar.setCurrentRow(i)
                        break
            if hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(1)
        except Exception:
            pass

        QMessageBox.information(
            self, self.tr("VM creada"),
            self.tr("VM '{0}' creada desde la plantilla "
                    "'{1}'.\n\n"
                    "Se ha abierto en Configuración → Almacenamiento para que\n"
                    "añadas el disco y el medio de instalación. La MAC de red se\n"
                    "ha regenerado para evitar conflictos con otras VMs.").format(name, template_display_name),
        )
