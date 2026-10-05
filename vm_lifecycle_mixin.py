# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: ciclo de vida de la VM — lista lateral, abrir/clonar/eliminar,
iniciar/pausar/apagar, resumen de la VM, y el wizard de "Nueva VM"
(perfiles de SO, firmware, gráficos, red por defecto).
"""
import os
import re
import json
import uuid
import shutil
import subprocess
import time
import configparser
from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QInputDialog, QLineEdit,
    QSizePolicy, QWidget, QDialog, QCheckBox,
    QTreeWidgetItem as _QTreeWidgetItemBase,  # vm_history_v1 E3b
)
# vm_config_save_cancel_v1_actions: Qt a nivel de módulo. Antes
# cada función que lo necesitaba hacía 'from PyQt6.QtCore import
# Qt as _Qt' local; eso funciona pero fragmenta el estilo y hace
# fácil tropezar como pasó en on_vm_list_changed.
from PyQt6.QtCore import Qt

import vm_config
import vm_paths  # portable_paths_v1
from vm_grid_delegate import VmCardDelegate  # vm_grid_view_v2_card_fix1
import ovf_io  # ovf_ova_io_v1
from vm_config import load_vm_config, get_os_profile, list_existing_vms
from host_deps import detect_host_graphics, qemu_graphics_capabilities
from workers import _BackgroundCallThread
# Import defensivo del widget SPICE (opcional: solo si spice-gtk tiene
# binding Python). Se hace aquí, al inicio del módulo, porque el mixin
# lo usa en _sync_spice_widget; antes vivía por error solo en
# virtual_machine.py, provocando NameError al llegar a SPICE.
try:
    from spice_widget import SpiceConsoleWidget
    _HAS_SPICE_WIDGET = True
    _SPICE_WIDGET_ERROR = None
except Exception as _spice_exc:
    SpiceConsoleWidget = None
    _HAS_SPICE_WIDGET = False
    _SPICE_WIDGET_ERROR = _spice_exc

from console_backend import (
    PROTOCOL_VNC, PROTOCOL_SPICE, MODE_EMBEDDED, MODE_EXTERNAL, MODE_NATIVE,
    MODE_HYBRID, MODE_HYBRID_GL,
    socket_path as _cb_socket_path,
    find_viewer, console_uri, build_viewer_args,
    can_embed_spice, describe_requirements,
)
import principal_cdrom

_VM_USER_ROLE = 256


class _ExportOvfDialog(QDialog):
    """Dialogo de exportacion OVF/OVA.

    Marcador ovf_auto_compress_v1: compresion automatica QCOW2.
    Marcador ovf_export_destino_v1: selector explicito de destino
    (VMware / VirtualBox / Virtual.Machine).
    """

    def __init__(self, parent, vm_name, is_macos):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Exportar como OVF/OVA - {0}").format(vm_name))
        self.setModal(True)
        self.resize(620, 660)

        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup,
            QCheckBox, QPushButton, QGroupBox,
        )

        self._result = None
        self._is_macos = bool(is_macos)

        layout = QVBoxLayout(self)

        info = QLabel(
            self.tr("Exporta <b>{0}</b> como OVA (un solo archivo) "
                    "o como OVF (carpeta con descriptor + discos sueltos).").format(vm_name)
        )
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        # --- Destino ---
        dest_group = QGroupBox(self.tr("Destino de la exportación"))
        dest_lay = QVBoxLayout(dest_group)

        self.radio_dest_vmware = QRadioButton(
            self.tr("VMware Workstation / ESXi")
        )
        self.radio_dest_vmware.setToolTip(self.tr(
            "Emite un descriptor OVF con VirtualSystemType=vmx-14 y "
            "disco VMDK stream-optimized. Es el único formato que "
            "VMware acepta."
        ))
        dest_lay.addWidget(self.radio_dest_vmware)

        self.radio_dest_vbox = QRadioButton(self.tr("VirtualBox"))
        self.radio_dest_vbox.setChecked(True)
        self.radio_dest_vbox.setToolTip(self.tr(
            "Descriptor orientado a VirtualBox. Elige abajo el formato "
            "de disco: QCOW2 (recomendado) o VMDK."
        ))
        dest_lay.addWidget(self.radio_dest_vbox)

        self.radio_dest_vm = QRadioButton(
            self.tr("Virtual.Machine (QEMU/KVM en Linux)")
        )
        self.radio_dest_vm.setToolTip(self.tr(
            "Descriptor optimizado para reimportar en esta misma app "
            "u otro host Linux con QEMU/KVM. Disco QCOW2 aplanado y "
            "comprimido."
        ))
        dest_lay.addWidget(self.radio_dest_vm)

        self._dest_group = QButtonGroup(self)
        self._dest_group.addButton(self.radio_dest_vmware)
        self._dest_group.addButton(self.radio_dest_vbox)
        self._dest_group.addButton(self.radio_dest_vm)

        layout.addWidget(dest_group)

        # --- Formato del disco (solo relevante para VirtualBox) ---
        self.fmt_group = QGroupBox(self.tr("Formato del disco"))
        fmt_lay = QVBoxLayout(self.fmt_group)

        self.radio_qcow2 = QRadioButton(
            self.tr("QCOW2 (recomendado) - instantáneo y comprimido")
        )
        self.radio_qcow2.setChecked(True)
        self.radio_qcow2.setToolTip(self.tr(
            "El disco se aplana (descartando snapshots internos) y se "
            "comprime con zlib."
        ))
        fmt_lay.addWidget(self.radio_qcow2)

        self.radio_vmdk = QRadioButton(
            self.tr("VMDK stream-optimized")
        )
        self.radio_vmdk.setToolTip(self.tr(
            "Requiere conversión previa con qemu-img. VMDK "
            "stream-optimized ya descarta snapshots por diseño."
        ))
        fmt_lay.addWidget(self.radio_vmdk)

        self._fmt_group = QButtonGroup(self)
        self._fmt_group.addButton(self.radio_qcow2)
        self._fmt_group.addButton(self.radio_vmdk)

        layout.addWidget(self.fmt_group)

        # --- Aviso contextual ---
        self.lbl_destino_info = QLabel("")
        self.lbl_destino_info.setTextFormat(_Qt.TextFormat.RichText)
        self.lbl_destino_info.setWordWrap(True)
        self.lbl_destino_info.setStyleSheet(
            "color: #0d3c7a; background: #e3f2fd; "
            "border: 1px solid #90caf9; border-radius: 6px; "
            "padding: 8px; font-size: 11px;"
        )
        layout.addWidget(self.lbl_destino_info)

        # --- Opciones adicionales ---
        opt_group = QGroupBox(self.tr("Opciones adicionales"))
        opt_lay = QVBoxLayout(opt_group)

        if self._is_macos:
            self.chk_iso = QCheckBox(
                self.tr("Incluir medio de instalación (BaseSystem.img)")
            )
        else:
            self.chk_iso = QCheckBox(self.tr("Incluir archivos ISO en el OVA"))
        self.chk_iso.setChecked(False)
        opt_lay.addWidget(self.chk_iso)
        layout.addWidget(opt_group)

        # Conexiones
        self.radio_dest_vmware.toggled.connect(self._on_dest_changed)
        self.radio_dest_vbox.toggled.connect(self._on_dest_changed)
        self.radio_dest_vm.toggled.connect(self._on_dest_changed)
        self.radio_qcow2.toggled.connect(self._on_fmt_changed)
        self.radio_vmdk.toggled.connect(self._on_fmt_changed)
        self._on_dest_changed()

        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        ok = QPushButton(self.tr("Exportar"))
        ok.setDefault(True)
        ok.clicked.connect(self._accept)
        btns.addWidget(ok)
        layout.addLayout(btns)

    def _destino(self):
        if self.radio_dest_vmware.isChecked():
            return "vmware"
        if self.radio_dest_vm.isChecked():
            return "virtmachine"
        return "virtualbox"

    def _on_dest_changed(self, *_):
        """Habilita o deshabilita el combo de formato segun el destino y
        actualiza el texto del aviso contextual.
        """
        destino = self._destino()

        if destino == "vmware":
            self.radio_vmdk.setChecked(True)
            self.radio_vmdk.setEnabled(False)
            self.radio_qcow2.setEnabled(False)
            self.fmt_group.setEnabled(False)
            info_text = self.tr(
                "Se emitirá un descriptor OVF con "
                "<b>VirtualSystemType=vmx-14</b>, disco "
                "<b>VMDK stream-optimized</b> y NIC E1000. "
                "Es el formato que VMware acepta."
            )
            if self._is_macos:
                info_text += self.tr(
                    "<br><br><b>⚠ macOS:</b> la VM resultante en VMware "
                    "<b>no arrancará macOS</b>. La cadena OpenCore+OSX-KVM "
                    "no es compatible con VMware. Este OVA sirve para "
                    "reimportar en Virtual.Machine u otro Linux con QEMU, "
                    "no para migrar a VMware."
                )
        elif destino == "virtmachine":
            self.radio_qcow2.setChecked(True)
            self.radio_qcow2.setEnabled(False)
            self.radio_vmdk.setEnabled(False)
            self.fmt_group.setEnabled(False)
            info_text = self.tr(
                "Descriptor orientado a <b>QEMU/KVM</b>. Disco "
                "<b>QCOW2 aplanado y comprimido con zlib</b> "
                "(descarta snapshots internos). Es el formato ideal "
                "para reimportar en esta misma app u otro host Linux."
            )
        else:  # virtualbox
            self.radio_qcow2.setEnabled(True)
            self.radio_vmdk.setEnabled(True)
            self.fmt_group.setEnabled(True)
            if self.radio_vmdk.isChecked():
                info_text = self.tr(
                    "Destino <b>VirtualBox</b>. Disco "
                    "<b>VMDK stream-optimized</b>: descarta snapshots "
                    "internos por diseño."
                )
            else:
                info_text = self.tr(
                    "Destino <b>VirtualBox</b>. Disco <b>QCOW2 "
                    "aplanado y comprimido</b>: se descartan los "
                    "snapshots internos y se aplica compresión zlib "
                    "(reduce el OVA entre un 40% y un 60%)."
                )
        self.lbl_destino_info.setText(info_text)

    def _on_fmt_changed(self, *_):
        """Redibuja el aviso contextual al cambiar el formato de disco
        (solo relevante en destino VirtualBox).
        """
        if self._destino() == "virtualbox":
            self._on_dest_changed()

    def _accept(self):
        destino = self._destino()
        if destino == "vmware":
            to_vmdk = True
        elif destino == "virtmachine":
            to_vmdk = False
        else:
            to_vmdk = bool(self.radio_vmdk.isChecked())
        self._result = {
            "destino": destino,
            "to_vmdk": to_vmdk,
            "include_iso": bool(self.chk_iso.isChecked()),
        }
        self.accept()

    def values(self):
        return self._result


class _OvfImportPreviewDialog(QDialog):
    """Dialogo de previsualizacion al importar OVF/OVA (ovf_ova_io_v1).

    Muestra lo que se ha detectado en el descriptor (os_type, RAM, CPUs,
    discos) y permite corregir os_type/distro antes de importar. Incluye
    un checkbox para importar solo la configuracion (sin discos).
    """

    def __init__(self, parent, ovf_data, suggested_name):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Importar OVF/OVA"))
        self.setModal(True)
        self.resize(640, 540)
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import (
            QFormLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
            QComboBox, QCheckBox, QPushButton, QFrame,
        )

        self._ovf_data = ovf_data or {}
        self._result = None
        layout = QVBoxLayout(self)

        info = QLabel(
            self.tr("Se ha le\u00eddo el descriptor OVF. Revisa los datos "
                    "detectados y corrige lo que haga falta antes de importar."
                    "<br><br><i>El sistema operativo detectado puede ser "
                    "ambiguo: aj\u00fastalo si el original no coincide.</i>")
        )
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        detected = QFrame()
        detected.setStyleSheet(
            "QFrame { background: palette(alternate-base); "
            "border: 1px solid palette(mid); border-radius: 6px; "
            "padding: 8px; }"
        )
        det_lay = QVBoxLayout(detected)
        detected_os = self._ovf_data.get("os_type") or self.tr("(desconocido)")
        detected_ver = (self._ovf_data.get("distro")
                        or self._ovf_data.get("win_ver")
                        or self._ovf_data.get("macos_ver") or "")
        detected_cpus = self._ovf_data.get("cpus") or 0
        detected_mem = self._ovf_data.get("memory_mb") or 0
        disks = self._ovf_data.get("disks") or []
        disks_txt = ", ".join(
            f"{d.get('file') or self.tr('(sin nombre)')} "
            f"({d.get('capacity_gb') or 0} GiB)"
            for d in disks
        ) or self.tr("(sin discos)")
        det_lbl = QLabel(
            self.tr("<b>Detectado en el OVF:</b><br>"
                    "SO: {0} {1}<br>"
                    "CPUs: {2} &nbsp; RAM: {3} MB<br>"
                    "Discos: {4} \u2014 {5}").format(
                        detected_os, detected_ver, detected_cpus,
                        detected_mem, len(disks), disks_txt)
        )
        det_lbl.setTextFormat(_Qt.TextFormat.RichText)
        det_lbl.setWordWrap(True)
        det_lay.addWidget(det_lbl)
        layout.addWidget(detected)

        form = QFormLayout()
        self.input_name = QLineEdit(suggested_name)
        form.addRow(self.tr("Nombre de la VM:"), self.input_name)

        self.combo_os = QComboBox()
        self.combo_os.addItem(self.tr("GNU / Linux"), "linux")
        self.combo_os.addItem(self.tr("Microsoft Windows"), "windows")
        self.combo_os.addItem(self.tr("macOS"), "macos")
        self.combo_os.addItem(self.tr("Android (Android-x86 / Bliss OS)"), "android")
        idx = self.combo_os.findData(self._ovf_data.get("os_type") or "linux")
        if idx >= 0:
            self.combo_os.setCurrentIndex(idx)
        self.combo_os.currentIndexChanged.connect(self._on_os_changed)
        form.addRow(self.tr("Plataforma:"), self.combo_os)

        self.label_version = QLabel(self.tr("Distribuci\u00f3n / versi\u00f3n:"))
        self.combo_version = QComboBox()
        self.combo_version.setEditable(True)
        form.addRow(self.label_version, self.combo_version)

        self.chk_config_only = QCheckBox(
            self.tr("Importar solo la configuraci\u00f3n (sin copiar los discos)")
        )
        self.chk_config_only.setToolTip(self.tr(
            "Si est\u00e1 marcado, se importan solo los datos del descriptor "
            "(CPU, RAM, red, sistema operativo) y NO se convierten ni "
            "copian los discos. \u00datil para reutilizar una configuraci\u00f3n "
            "sin duplicar gigabytes de disco."
        ))
        form.addRow("", self.chk_config_only)

        layout.addLayout(form)
        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        cancel.clicked.connect(self.reject)
        ok = QPushButton(self.tr("Importar"))
        ok.setDefault(True)
        ok.clicked.connect(self._accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

        # Poblar el combo de version para el SO detectado inicialmente.
        self._on_os_changed()

    def _on_os_changed(self, *_):
        os_type = self.combo_os.currentData() or "linux"
        self.combo_version.clear()
        if os_type == "linux":
            self.label_version.setText(self.tr("Distribuci\u00f3n:"))
            for d in ("Linux Mint", "Ubuntu", "Debian", "Manjaro Linux",
                      "Fedora", "Pop!_OS", "Zorin OS", "elementary OS",
                      "openSUSE", "Arch Linux", "EndeavourOS", "Kali Linux",
                      "AlmaLinux", "Rocky Linux", "CachyOS", "Solus",
                      "antiX", "MX Linux", "Alpine Linux", "Void Linux"):
                self.combo_version.addItem(d, d)
            want = self._ovf_data.get("distro") or ""
            if want:
                i = self.combo_version.findData(want)
                if i < 0:
                    self.combo_version.addItem(want, want)
                    i = self.combo_version.findData(want)
                if i >= 0:
                    self.combo_version.setCurrentIndex(i)
        elif os_type == "windows":
            self.label_version.setText(self.tr("Versi\u00f3n de Windows:"))
            for v in ("Windows 11", "Windows 10", "Windows 7",
                      "Windows Vista", "Windows XP", "Windows 2000"):
                self.combo_version.addItem(v, v)
            want = self._ovf_data.get("win_ver") or "Windows 10"
            i = self.combo_version.findData(want)
            if i >= 0:
                self.combo_version.setCurrentIndex(i)
        elif os_type == "macos":
            self.label_version.setText(self.tr("Versi\u00f3n de macOS:"))
            for v in ("High Sierra (10.13)", "Mojave (10.14)",
                      "Catalina (10.15)", "Big Sur (11.7)",
                      "Monterey (12.6)", "Ventura (13)", "Sonoma (14)",
                      "Sequoia (15)", "Tahoe"):
                self.combo_version.addItem(v, v)
            want = self._ovf_data.get("macos_ver") or ""
            if want:
                i = self.combo_version.findData(want)
                if i >= 0:
                    self.combo_version.setCurrentIndex(i)
        else:  # android
            self.label_version.setText(self.tr("Distribuci\u00f3n Android:"))
            for v in ("Android-x86", "Bliss OS"):
                self.combo_version.addItem(v, v)

    def _accept(self):
        name = (self.input_name.text() or "").strip()
        if not name:
            from PyQt6.QtWidgets import QMessageBox as _QMB
            _QMB.warning(self, self.tr("Nombre inv\u00e1lido"),
                         self.tr("Debes escribir un nombre para la VM importada."))
            return
        name = re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "VM-importada"
        os_type = self.combo_os.currentData() or "linux"
        version = (self.combo_version.currentText() or "").strip()
        self._result = {
            "name": name,
            "os_type": os_type,
            "distro_or_version": version,
            "config_only": bool(self.chk_config_only.isChecked()),
        }
        self.accept()

    def values(self):
        return self._result


# vm_history_v1 — E3b: item de árbol para el diálogo de historial.
# Sobrescribe __lt__ para que QTreeWidget ordene por el valor guardado
# en Qt.UserRole de la columna activa, en vez de por el texto mostrado
# ("2 min 12 s" no ordena como 212; una fecha formateada no ordena
# como ISO). Sin esta clase, ordenar por "Duración" daría un orden
# alfabético sin sentido.
class _HistoryTreeItem(_QTreeWidgetItemBase):
    def __lt__(self, other):
        try:
            tw = self.treeWidget()
            col = tw.sortColumn() if tw is not None else 0
        except Exception:
            col = 0
        try:
            from PyQt6.QtCore import Qt as _Qt2
            role = _Qt2.ItemDataRole.UserRole
        except Exception:
            role = 256  # Qt.ItemDataRole.UserRole
        a = self.data(col, role)
        b = (other.data(col, role) if other is not None else None)
        try:
            if a is None:
                return True
            if b is None:
                return False
            return a < b
        except Exception:
            try:
                return str(a) < str(b)
            except Exception:
                return False


class VmLifecycleMixin:
    # ==================================================================
    # Sistema de "cambios pendientes" (vm_config_save_cancel_v1_dirty)
    # ==================================================================
    # La pestaña "Configuración VM" muestra dos botones:
    #   💾 Guardar configuración  — persiste los cambios.
    #   ↺ Descartar cambios       — recarga desde el .ini.
    #
    # Solo el "Grupo A" de widgets entra en este modelo:
    #   nombre, plataforma (solo creación), versión de SO, RAM,
    #   núcleos, CPU model, chipset, firmware, secure boot, TPM,
    #   gráficos, VRAM, audio, auto-inicio, snapshot_compat, red,
    #   passthrough, orden de arranque, notas, grupo/color,
    #   guest agent, clipboard.
    #
    # El "Grupo B" sigue auto-guardándose:
    #   discos, CD/DVD, disquetes (crear/modificar/eliminar),
    #   puntero, serial a archivo.

    def _collect_config_from_ui(self):
        """Devuelve un dict con los valores del Grupo A que hay en
        los widgets ahora mismo. NO toca el .ini.

        Solo incluye los campos que tienen widget asociado, para
        evitar falsos positivos por campos que no son editables
        (disk_size, disk_type, etc.).
        """
        out = {}
        try:
            out["name"] = (self.input_vm_name.text() or "").strip()
        except Exception:
            out["name"] = ""
        # Plataforma: solo cuenta en modo creación.
        try:
            out["_os_type"] = self.combo_main_os.currentData() or ""
        except Exception:
            out["_os_type"] = ""
        # Versión de SO (según plataforma).
        try:
            _os = out.get("_os_type") or ""
            if _os == "macos":
                out["_os_ver"] = self.combo_macos_ver.currentText()
            elif _os == "windows":
                out["_os_ver"] = self.combo_win_ver.currentText()
            elif _os == "linux":
                out["_os_ver"] = self.combo_lin_distro.currentText()
                try:
                    out["_iso_choice"] = self._selected_lin_version()
                except Exception:
                    out["_iso_choice"] = ""
            else:
                out["_os_ver"] = ""
        except Exception:
            out["_os_ver"] = ""
        # RAM, núcleos, CPU.
        try:
            out["ram"] = f"{self.slider_ram.value()}G"
        except Exception:
            out["ram"] = ""
        try:
            out["cores"] = str(self.slider_cores.value())
        except Exception:
            out["cores"] = ""
        try:
            out["cpu_model"] = self.combo_cpu_model.currentData() or "auto"
        except Exception:
            out["cpu_model"] = "auto"
        # Chipset, firmware.
        try:
            out["chipset"] = self.combo_chipset.currentData() or "pc"
        except Exception:
            out["chipset"] = "pc"
        try:
            out["firmware"] = self.combo_firmware.currentData() or "bios"
        except Exception:
            out["firmware"] = "bios"
        # Secure Boot, TPM.
        try:
            out["secure_boot"] = bool(self.check_secure_boot.isChecked())
        except Exception:
            out["secure_boot"] = False
        try:
            out["tpm"] = bool(self.check_tpm.isChecked())
        except Exception:
            out["tpm"] = False
        # Gráficos.
        try:
            out["graphics_mode"] = self.combo_graphics.currentData() or "auto"
        except Exception:
            out["graphics_mode"] = "auto"
        try:
            out["graphics_vram"] = self.combo_graphics_vram.currentData() or "256M"
        except Exception:
            out["graphics_vram"] = "256M"
        # Audio.
        try:
            out["audio_device"] = self.combo_audio.currentData() or "intel-hda"
        except Exception:
            out["audio_device"] = "intel-hda"
        # Auto-inicio, snapshot_compat.
        try:
            out["autostart_on_launch"] = bool(
                self.check_autostart_on_launch.isChecked())
        except Exception:
            out["autostart_on_launch"] = False
        try:
            out["snapshot_compat"] = bool(
                self.check_snapshot_compat.isChecked())
        except Exception:
            out["snapshot_compat"] = False
        # vm_config_save_cancel_v1_dirty_2b1: red y passthrough.
        try:
            out["network_devices"] = json.loads(json.dumps(
                self._network_devices() or []))
        except Exception:
            out["network_devices"] = []
        try:
            out["no_network"] = bool(self.check_no_network.isChecked())
        except Exception:
            out["no_network"] = False
        try:
            out["passthrough_devices"] = json.loads(json.dumps(
                getattr(self, "_passthrough_saved", []) or []))
        except Exception:
            out["passthrough_devices"] = []
        try:
            out["boot_order"] = list(self._current_boot_order_tokens())
        except Exception:
            out["boot_order"] = []
        return out

    def _load_config_comparable(self, vm_dir):
        """Carga la parte COMPARABLE del .ini (mismos campos que
        _collect_config_from_ui). Devuelve un dict homogéneo."""
        if not vm_dir:
            return {}
        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception:
            return {}
        extra = data.get("extra") or {}
        os_type = data.get("os_type") or ""
        os_ver = ""
        if os_type == "macos":
            os_ver = extra.get("os_choice", "")
            # El .ini guarda el id ("1", "2", …), pero el combo
            # muestra el texto ("High Sierra (10.13)", …). Es un
            # mismatch estructural: comparamos por texto del combo
            # contra un texto derivado, no por id.
            try:
                for _name, _val in self.os_options:
                    if _val == os_ver:
                        os_ver = _name
                        break
            except Exception:
                pass
        elif os_type == "windows":
            os_ver = extra.get("win_ver", "Windows 11")
        elif os_type == "linux":
            os_ver = extra.get("distro", "")
        out = {
            "name": data.get("name", ""),
            "_os_type": os_type,
            "_os_ver": os_ver,
            "ram": data.get("ram", ""),
            "cores": str(data.get("cores", "")),
            "cpu_model": extra.get("cpu_model", "auto"),
            "chipset": data.get("chipset", "pc"),
            "firmware": data.get("firmware", "bios"),
            "secure_boot": bool(data.get("secure_boot", False)),
            "tpm": bool(data.get("tpm", False)),
            "graphics_mode": data.get("graphics_mode", "auto"),
            "graphics_vram": data.get("graphics_vram", "256M"),
            "audio_device": data.get("audio_device", "intel-hda"),
            "autostart_on_launch": bool(
                extra.get("autostart_on_launch", False)),
            "snapshot_compat": bool(extra.get("snapshot_compat", False)),
        }
        # vm_config_save_cancel_v1_dirty_2b1: red y passthrough.
        try:
            out["network_devices"] = data.get("network_devices") or []
        except Exception:
            out["network_devices"] = []
        try:
            out["no_network"] = (not out["network_devices"])
        except Exception:
            out["no_network"] = False
        try:
            out["passthrough_devices"] = (data.get("passthrough_devices") or [])
        except Exception:
            out["passthrough_devices"] = []
        try:
            out["boot_order"] = list(data.get("boot_order") or [])
        except Exception:
            out["boot_order"] = []
        # El ISO choice no lo comparamos (es dinámico y ruidoso).
        return out

    def _has_pending_changes(self):
        """True si hay cambios sin guardar en el Grupo A.

        Modo creación (no hay current_vm_dir + _new_vm_mode):
        devuelve True en cuanto hay nombre, para que el botón
        Guardar se active y _create_from_form() pueda ejecutarse.

        Modo edición: compara el formulario contra el .ini.
        """
        # vm_config_save_cancel_v1_create_from_form_gating:
        # en modo creación el botón Guardar se activa en cuanto el
        # usuario escribe un nombre. Sin esto, el botón quedaba
        # deshabilitado y _create_from_form() nunca se invocaba.
        if not getattr(self, "current_vm_dir", None):
            if getattr(self, "_new_vm_mode", False):
                try:
                    return bool((self.input_vm_name.text() or "").strip())
                except Exception:
                    return False
            return False
        try:
            ui = self._collect_config_from_ui()
            ini = self._load_config_comparable(self.current_vm_dir)
        except Exception:
            return False
        # Comparar campo por campo, ignorando los que no coinciden
        # por razones estructurales (por ejemplo, _os_ver con valores
        # por defecto distintos entre UI y .ini).
        for k in ("name", "ram", "cores", "cpu_model", "chipset",
                  "firmware", "secure_boot", "tpm",
                  "graphics_mode", "graphics_vram", "audio_device",
                  "autostart_on_launch", "snapshot_compat",
                  # vm_config_save_cancel_v1_dirty_2b1:
                  "network_devices", "no_network",
                  "passthrough_devices", "boot_order"):
            a = ui.get(k)
            b = ini.get(k)
            # Normalizar ram por si "8G" vs "8G" o "8192M".
            if k == "ram":
                a = self._normalize_ram(a)
                b = self._normalize_ram(b)
            if a != b:
                return True
        return False

    @staticmethod
    def _normalize_ram(v):
        """Normaliza '8G' / '8G' / '8192M' a un entero de GB."""
        if not v:
            return 0
        s = str(v).strip().upper()
        try:
            if s.endswith("G"):
                return int(float(s[:-1]))
            if s.endswith("M"):
                return int(float(s[:-1]) / 1024)
        except Exception:
            return 0
        try:
            return int(s)
        except Exception:
            return 0

    def _update_config_dirty_state(self):
        """Actualiza la UI (botones, indicador, asterisco) según el
        estado actual de cambios pendientes.

        Modo creación (_new_vm_mode):
          • Guardar → habilitado si _has_pending_changes() (nombre).
          • Descartar → habilitado siempre (equivale a limpiar el
            formulario llamando a new_vm()).
        Modo edición: ambos dependen de _has_pending_changes().
        """
        if not hasattr(self, "btn_config_save"):
            return
        try:
            dirty = self._has_pending_changes()
        except Exception:
            dirty = False
        # vm_config_save_cancel_v1_create_from_form_gating:
        # en modo creación el botón Descartar siempre está
        # disponible, aunque no haya nombre escrito, para que el
        # usuario pueda resetear el formulario sin tener que
        # seleccionar otra VM.
        new_mode = bool(getattr(self, "_new_vm_mode", False))
        try:
            self.btn_config_save.setEnabled(dirty)
        except Exception:
            pass
        try:
            self.btn_config_discard.setEnabled(dirty or new_mode)
        except Exception:
            pass
        try:
            self.config_bar_dirty_label.setText(
                self.tr("\u25cf cambios sin guardar") if dirty else ""
            )
            self.config_bar_dirty_label.setVisible(dirty)
        except Exception:
            pass
        # Asterisco en el título de la pestaña (índice 1).
        try:
            if hasattr(self, "main_tabs") and self.main_tabs.count() > 1:
                base = self.tr("Configuración VM")
                self.main_tabs.setTabText(
                    1, base + (" *" if dirty else "")
                )
        except Exception:
            pass

    def _wire_config_dirty_signals(self):
        """Conecta las señales de los widgets del Grupo A a
        _on_config_dirty. Idempotente: si ya están conectadas,
        PyQt permite duplicar; para evitarlo, se hace solo una vez
        (flag en self).
        """
        if getattr(self, "_dirty_signals_wired", False):
            return
        self._dirty_signals_wired = True
        slot = self._on_config_dirty
        pairs = [
            ("input_vm_name", "textChanged"),
            ("slider_ram", "valueChanged"),
            ("slider_cores", "valueChanged"),
            ("combo_cpu_model", "currentIndexChanged"),
            ("combo_chipset", "currentIndexChanged"),
            ("combo_firmware", "currentIndexChanged"),
            ("check_secure_boot", "stateChanged"),
            ("check_tpm", "stateChanged"),
            ("combo_graphics", "currentIndexChanged"),
            ("combo_graphics_vram", "currentIndexChanged"),
            ("combo_audio", "currentIndexChanged"),
            ("combo_macos_ver", "currentIndexChanged"),
            ("combo_win_ver", "currentIndexChanged"),
            ("combo_lin_distro", "currentIndexChanged"),
            ("combo_lin_version", "currentIndexChanged"),
            ("check_autostart_on_launch", "stateChanged"),
            ("check_snapshot_compat", "stateChanged"),
        ]
        for attr, sig in pairs:
            w = getattr(self, attr, None)
            if w is None:
                continue
            try:
                getattr(w, sig).connect(slot)
            except Exception:
                pass

    def _on_config_dirty(self, *_args):
        """Slot que se conecta a las señales de los widgets del Grupo A.

        No guarda nada: solo recalcula si hay cambios pendientes y
        actualiza la UI.
        """
        try:
            self._update_config_dirty_state()
        except Exception:
            pass

    # ==================================================================
    # Persistencia real: Guardar / Descartar (marcador
    # vm_config_save_cancel_v1_actions)
    # ==================================================================

    # ==================================================================
    # Crear VM desde el formulario (marcador
    # vm_config_save_cancel_v1_create_from_form)
    # ==================================================================
    # Este método es el que se ejecuta cuando el usuario está en modo
    # "Nueva VM" (sin current_vm_dir) y pulsa "💾 Guardar configuración".
    #
    # Flujo:
    #   1. Leer los widgets del formulario (_collect_config_from_ui).
    #   2. Validar nombre (no vacío, saneado, no reservado, no duplicado).
    #   3. Forzar coherencias por SO (macOS → uefi/q35; Win11 → uefi+sb+tpm;
    #      Android → bios/q35).
    #   4. Crear la carpeta de la VM.
    #   5. Escribir vm_config.ini con save_vm_config().
    #   6. Actualizar current_vm_dir, apagar _new_vm_mode, refrescar lista.
    #
    # Almacenamiento: NO se crea ningún disco. El usuario lo añade después
    # desde Configuración → Almacenamiento (mismo camino que el workaround
    # antiguo, pero ya sin necesitar el "truco" de tocar Almacenamiento).

    _RESERVED_VM_NAMES = (".", "..", "Nueva Máquina Virtual", "_templates")

    def _create_from_form(self):
        """Crea una VM nueva a partir del formulario."""
        # Si por alguna razón ya hay VM seleccionada, delegar.
        if self.current_vm_dir:
            return self._save_config_from_ui()

        if not getattr(self, "_new_vm_mode", False):
            QMessageBox.information(
                self, self.tr("Guardar configuración"),
                self.tr("No hay ninguna máquina virtual seleccionada."),
            )
            return False

        try:
            ui = self._collect_config_from_ui()
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudieron leer los datos del formulario.\n\n{0}").format(e),
            )
            return False

        # --- 1. Nombre ---
        raw_name = (ui.get("name") or "").strip()
        if not raw_name:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("El nombre de la máquina virtual no puede quedar vacío."),
            )
            return False

        if raw_name in self._RESERVED_VM_NAMES:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("El nombre '{0}' está reservado. Elige otro.").format(raw_name),
            )
            return False

        folder = vm_config.vm_folder_name(raw_name)

        existing = set()
        try:
            existing = set(list_existing_vms())
        except Exception:
            pass
        if folder in existing or os.path.exists(os.path.join(vm_config.BASE_VM_DIR, folder)):
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("Ya existe una máquina virtual llamada '{0}'.\n\n"
                        "Elige otro nombre.").format(folder),
            )
            return False

        target_dir = os.path.join(vm_config.BASE_VM_DIR, folder)

        # --- 2. OS + versión ---
        os_type = ui.get("_os_type") or "linux"
        os_ver = (ui.get("_os_ver") or "").strip()

        # Forzar coherencias por SO (con aviso si corregimos algo).
        firmware = ui.get("firmware") or "bios"
        chipset = ui.get("chipset") or "pc"
        secure_boot = bool(ui.get("secure_boot"))
        tpm = bool(ui.get("tpm"))

        def _force(field, want, current):
            if current == want:
                return current, False
            return want, True

        if os_type == "macos":
            firmware, c1 = _force("firmware", "uefi", firmware)
            chipset, c2 = _force("chipset", "q35", chipset)
            if secure_boot:
                secure_boot = False; c3 = True
            else:
                c3 = False
            if tpm:
                tpm = False; c4 = True
            else:
                c4 = False
            if c1 or c2 or c3 or c4:
                try:
                    self.log_message(
                        "==> macOS: ajustado firmware=uefi, chipset=q35, "
                        "secure_boot=False, tpm=False (reglas de macOS)."
                    )
                except Exception:
                    pass
        elif os_type == "windows":
            is_win11 = (os_ver == "Windows 11")
            if is_win11:
                firmware, c1 = _force("firmware", "uefi", firmware)
                if not secure_boot:
                    secure_boot = True; c2 = True
                else:
                    c2 = False
                if not tpm:
                    tpm = True; c3 = True
                else:
                    c3 = False
                if c1 or c2 or c3:
                    try:
                        self.log_message(
                            "==> Windows 11: ajustado firmware=uefi, "
                            "secure_boot=True, tpm=True."
                        )
                    except Exception:
                        pass
        elif os_type == "android":
            firmware, c1 = _force("firmware", "bios", firmware)
            chipset, c2 = _force("chipset", "q35", chipset)
            if secure_boot:
                secure_boot = False; c3 = True
            else:
                c3 = False
            if tpm:
                tpm = False; c4 = True
            else:
                c4 = False
            if c1 or c2 or c3 or c4:
                try:
                    self.log_message(
                        "==> Android: ajustado firmware=bios, chipset=q35, "
                        "secure_boot=False, tpm=False."
                    )
                except Exception:
                    pass

        # --- 3. Red por defecto si el formulario no trae ninguna ---
        networks = ui.get("network_devices") or []
        if not isinstance(networks, list) or not networks:
            try:
                _mac = self._new_qemu_mac()
            except Exception:
                _mac = ""
            networks = [{
                "name": "Red 1",
                "model": "virtio-net-pci",
                "mode": "nat",
                "interface": "",
                "mac": _mac,
            }]
            try:
                self.log_message(
                    "==> VM nueva: creado adaptador de red por defecto "
                    "(NAT + virtio-net-pci)."
                )
            except Exception:
                pass

        # --- 4. Extra ---
        # Mapear versión del formulario a la clave real que espera cada SO.
        extra = {
            "cpu_model": ui.get("cpu_model") or "auto",
            "autostart_on_launch": bool(ui.get("autostart_on_launch", False)),
            "snapshot_compat": bool(ui.get("snapshot_compat", False)),
            "pointer_device": "auto",
            "serial_to_file": False,
            "storage_devices": [],
            "cdrom_path": "",
            "notes": "",
            "group": "",
            "color": "",
        }

        # Dispositivo de señalización: leer del combo si existe.
        try:
            _ptr = getattr(self, "combo_pointer", None)
            if _ptr is not None:
                extra["pointer_device"] = _ptr.currentData() or "auto"
        except Exception:
            pass

        # Captura del puerto serie: leer del checkbox si existe.
        try:
            _ser = getattr(self, "check_serial_to_file", None)
            if _ser is not None:
                extra["serial_to_file"] = bool(_ser.isChecked())
        except Exception:
            pass

        # Versión del SO a la clave correcta de extra.
        if os_type == "macos":
            # En macOS el .ini guarda el id ("1", "2", …), no el texto.
            _mac_id = os_ver
            try:
                for _name, _val in self.os_options:
                    if _name == os_ver:
                        _mac_id = _val
                        break
            except Exception:
                pass
            extra["os_choice"] = _mac_id or os_ver or ""
        elif os_type == "windows":
            extra["win_ver"] = os_ver or "Windows 11"
        elif os_type == "linux":
            extra["distro"] = os_ver or ""
            # La elección de ISO de Linux (si el usuario la había dejado
            # fijada) se conserva como metadato, pero no persiste aquí
            # como widget propio: la unidad CD/DVD "Principal" es la
            # única fuente de verdad.
        # android: sin clave de versión.

        # --- 5. Crear carpeta ---
        try:
            os.makedirs(target_dir, exist_ok=False)
        except FileExistsError:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("La carpeta destino ya existe:\n\n{0}").format(target_dir),
            )
            return False
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudo crear la carpeta de la VM.\n\n{0}").format(e),
            )
            return False

        # --- 6. Escribir vm_config.ini con rollback si algo falla ---
        try:
            vm_config.save_vm_config(
                target_dir,
                folder,
                os_type,
                ui.get("ram") or "4G",
                int(ui.get("cores") or 2),
                getattr(self, "disk_size_setting", "128G"),
                getattr(self, "disk_type_setting", "dynamic"),
                getattr(self, "disk_format_setting", "qcow2"),
                getattr(self, "disk_ext_setting", "qcow2"),
                extra,
                firmware=firmware,
                secure_boot=secure_boot,
                tpm=tpm,
                boot_device="cdrom",
                network_model="virtio-net-pci",
                audio_device=ui.get("audio_device") or "intel-hda",
                network_mode="nat",
                network_interface="",
                network_count=1,
                graphics_mode=ui.get("graphics_mode") or "auto",
                graphics_vram=ui.get("graphics_vram") or "256M",
                boot_order=["cdrom", "disk", "network"],
                network_devices=networks,
                passthrough_devices=ui.get("passthrough_devices") or [],
                chipset=chipset,
                log_func=self.log_message,
            )
        except Exception as e:
            # Rollback: borrar la carpeta recién creada.
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception:
                pass
            QMessageBox.critical(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudo guardar la configuración de la VM.\n\n"
                        "La carpeta creada se ha eliminado para no dejar "
                        "datos a medias.\n\n{0}").format(e),
            )
            return False

        # --- 7. Actualizar estado de la app ---
        self.current_vm_dir = target_dir
        self._new_vm_mode = False

        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(target_dir)

        try:
            self.refresh_vm_list(select_name=folder)
        except Exception:
            pass
        try:
            self._update_manager_details()
        except Exception:
            pass
        try:
            self._update_config_dirty_state()
        except Exception:
            pass
        try:
            self._update_config_tab_gating()
        except Exception:
            pass

        try:
            self.log_message(
                f"==> VM '{folder}' creada. Añade un disco en "
                f"Configuración → Almacenamiento antes de arrancarla."
            )
        except Exception:
            pass

        QMessageBox.information(
            self, self.tr("VM creada"),
            self.tr("La máquina virtual '{0}' se ha creado correctamente.\n\n"
                    "Antes de arrancarla, añade al menos un disco en "
                    "Configuración → Almacenamiento y elige el medio de "
                    "instalación en la unidad CD/DVD 'Principal'.").format(folder),
        )
        return True

    def _save_config_from_ui(self):
        """Persiste el Grupo A en vm_config.ini."""
        if not self.current_vm_dir:
            if getattr(self, "_new_vm_mode", False):
                # vm_config_save_cancel_v1_create_from_form:
                # en modo creación el botón Guardar crea la VM
                # desde el formulario en vez de avisar de "no
                # implementado".
                return self._create_from_form()
            QMessageBox.information(
                self, self.tr("Guardar configuración"),
                self.tr("No hay ninguna máquina virtual seleccionada."),
            )
            return False

        try:
            ui = self._collect_config_from_ui()
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudieron leer los cambios de la interfaz.\n\n{0}").format(e),
            )
            return False

        vm_dir = self.current_vm_dir
        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudo leer la configuración actual.\n\n{0}").format(e),
            )
            return False

        new_name = (ui.get("name") or "").strip()
        if not new_name:
            QMessageBox.warning(
                self, self.tr("Guardar configuración"),
                self.tr("El nombre de la máquina virtual no puede quedar vacío."),
            )
            return False

        # --- Extra: partir del .ini y sobrescribir SOLO Grupo A ---
        extra = dict(data.get("extra") or {})
        if "cpu_model" in ui:
            extra["cpu_model"] = ui["cpu_model"]
        if "autostart_on_launch" in ui:
            extra["autostart_on_launch"] = bool(ui["autostart_on_launch"])
        if "snapshot_compat" in ui:
            extra["snapshot_compat"] = bool(ui["snapshot_compat"])
        try:
            if data.get("os_type") == "macos" and ui.get("_os_ver"):
                _want = ui["_os_ver"]
                for _name, _val in self.os_options:
                    if _name == _want:
                        extra["os_choice"] = _val
                        break
            elif data.get("os_type") == "windows" and ui.get("_os_ver"):
                extra["win_ver"] = ui["_os_ver"]
        except Exception:
            pass

        # --- Llamar a save_vm_config ---
        try:
            import vm_config as _vc
            _vc.save_vm_config(
                vm_dir,
                new_name,
                data.get("os_type") or "linux",
                ui.get("ram") or data.get("ram") or "4G",
                int(ui.get("cores") or data.get("cores") or 2),
                data.get("disk_size") or "128G",
                data.get("disk_type") or "dynamic",
                data.get("disk_format") or "qcow2",
                data.get("disk_ext") or "qcow2",
                extra,
                firmware=ui.get("firmware") or data.get("firmware") or "bios",
                secure_boot=bool(ui.get("secure_boot")),
                tpm=bool(ui.get("tpm")),
                boot_device=data.get("boot_device") or "cdrom",
                network_model=data.get("network_model") or "virtio-net-pci",
                audio_device=ui.get("audio_device") or data.get("audio_device") or "intel-hda",
                network_mode=data.get("network_mode") or "nat",
                network_interface=data.get("network_interface") or "",
                network_count=int(data.get("network_count") or 1),
                graphics_mode=ui.get("graphics_mode") or "auto",
                graphics_vram=ui.get("graphics_vram") or "256M",
                boot_order=data.get("boot_order") or ["cdrom", "disk", "network"],
                network_devices=ui.get("network_devices") or data.get("network_devices") or [],
                passthrough_devices=ui.get("passthrough_devices") or data.get("passthrough_devices") or [],
                chipset=ui.get("chipset") or data.get("chipset") or "pc",
                log_func=self.log_message,
            )
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Guardar configuración"),
                self.tr("No se pudo guardar la configuración.\n\n{0}").format(e),
            )
            return False

        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(vm_dir)

        try:
            self.refresh_vm_list(select_name=os.path.basename(vm_dir))
        except Exception:
            pass
        try:
            self._update_manager_details()
        except Exception:
            pass
        try:
            self._update_config_dirty_state()
        except Exception:
            pass

        try:
            self.log_message(f"==> Configuración guardada para '{new_name}'.")
        except Exception:
            pass
        return True

    def _discard_config_changes(self):
        """Descarta los cambios pendientes recargando desde disco."""
        if not self.current_vm_dir:
            if getattr(self, "_new_vm_mode", False):
                self.new_vm()
            return
        vm_name = os.path.basename(self.current_vm_dir)
        try:
            self.log_message(
                f"==> Cambios descartados para '{vm_name}' (recargando desde disco)."
            )
        except Exception:
            pass
        self.open_vm(vm_name)


    # ==================================================================
    # Habilitación de la pestaña "Configuración VM" (config_tab_gating_v1)
    # ==================================================================
    # La pestaña solo se puede usar si:
    #   • hay una VM seleccionada (self.current_vm_dir), o
    #   • estamos en modo creación de VM nueva (self._new_vm_mode).
    #
    # Si la pestaña estaba seleccionada y pasa a deshabilitarse, se
    # salta a Resumen (índice 0).

    def _update_config_tab_gating(self):
        """Habilita/deshabilita la pestaña "Configuración VM" (índice 1)."""
        if not hasattr(self, "main_tabs"):
            return
        try:
            has_vm = bool(getattr(self, "current_vm_dir", None))
            new_mode = bool(getattr(self, "_new_vm_mode", False))
            enabled = has_vm or new_mode
            # Índice 1 = "Configuración VM" (Resumen = 0).
            idx = 1
            if idx >= self.main_tabs.count():
                return
            self.main_tabs.setTabEnabled(idx, enabled)
            # Si estaba seleccionada y se deshabilita, saltar a Resumen.
            if not enabled and self.main_tabs.currentIndex() == idx:
                self.main_tabs.setCurrentIndex(0)
        except Exception as e:
            try:
                if hasattr(self, "log_message"):
                    self.log_message(
                        f"[AVISO] config_tab_gating_v1: {e}"
                    )
            except Exception:
                pass

    # ==================================================================
    # Aviso legal de macOS (marcador macos_eula_notice_v1)
    # ==================================================================
    # macOS es software propietario de Apple Inc. Este gestor permite
    # instalarlo sobre QEMU/KVM con fines de ESTUDIO, INVESTIGACIÓN o
    # USO PERSONAL, tal como se describe en la licencia de Apple para
    # sistemas operativos. No se permite el uso comercial, la
    # redistribución, ni la instalación en hardware que no sea Apple.
    #
    # Se avisa al usuario:
    #   1. Al seleccionar macOS como plataforma (aviso breve, una vez
    #      por sesión).
    #   2. Al arrancar una VM macOS por primera vez (modal, persistente
    #      en extra["macos_eula_acknowledged"]).

    _MACOS_EULA_LINK = "https://www.apple.com/legal/sla/"

    def _macos_eula_short_text(self):
        """Texto breve del aviso al crear una VM macOS."""
        return self.tr(
            "macOS es una marca registrada y software propietario de "
            "Apple Inc.\n\n"
            "Este gestor te permite instalar macOS sobre QEMU/KVM con "
            "fines exclusivamente de estudio, investigación o uso "
            "personal. No se permite el uso comercial, la redistribución "
            "ni la instalación en hardware que no sea Apple."
        )

    def _macos_eula_full_text(self):
        """Texto completo del modal al arrancar por primera vez."""
        return self.tr(
            "Antes de arrancar esta máquina virtual macOS, lee y acepta "
            "el siguiente aviso legal:\n\n"
            "macOS es una marca registrada y software propietario de "
            "Apple Inc.\n\n"
            "Esta aplicación permite instalar macOS sobre QEMU/KVM con "
            "fines EXCLUSIVAMENTE de estudio, investigación o uso "
            "personal, tal como se describe en la licencia de software "
            "de Apple para sistemas operativos.\n\n"
            "NO se permite:\n"
            "  • el uso comercial,\n"
            "  • la redistribución de la VM resultante,\n"
            "  • la instalación en hardware que no sea Apple.\n\n"
            "Al continuar, confirmas que aceptas estos términos. Si no "
            "estás de acuerdo, cancela el arranque.\n\n"
            "Más información: {0}"
        ).format(self._MACOS_EULA_LINK)

    def _macos_eula_already_acknowledged(self, vm_dir):
        """True si el usuario ya aceptó el aviso para esta VM."""
        if not vm_dir:
            return False
        try:
            data = self._load_vm_config_cached(vm_dir)
            return bool((data.get("extra") or {}).get(
                "macos_eula_acknowledged", False))
        except Exception:
            return False

    def _macos_eula_mark_acknowledged(self, vm_dir):
        """Persiste extra["macos_eula_acknowledged"] = True en el .ini."""
        if not vm_dir:
            return False
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return False
        try:
            import json as _json, configparser as _cfg
            c = _cfg.ConfigParser(interpolation=None)
            c.read(cfg_path, encoding="utf-8")
            if not c.has_section("extra"):
                c.add_section("extra")
            try:
                extra = _json.loads(c["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["macos_eula_acknowledged"] = True
            c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
            with open(cfg_path, "w", encoding="utf-8") as f:
                c.write(f)
            if hasattr(self, "_invalidate_vm_config_cache"):
                self._invalidate_vm_config_cache(vm_dir)
            return True
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] No se pudo guardar la aceptación del "
                    f"aviso de macOS: {e}"
                )
            except Exception:
                pass
            return False

    def _show_macos_eula_modal(self, vm_dir, vm_name):
        """Modal de aceptación. Devuelve True si el usuario acepta.

        Se muestra solo si no estaba ya aceptado para esta VM.
        """
        from PyQt6.QtWidgets import QMessageBox
        if self._macos_eula_already_acknowledged(vm_dir):
            return True
        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Aviso legal — macOS"))
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(self.tr("Aviso legal antes de arrancar macOS"))
        box.setInformativeText(self._macos_eula_full_text())
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        yes_btn = box.button(QMessageBox.StandardButton.Yes)
        if yes_btn is not None:
            yes_btn.setText(self.tr("Acepto y continúo"))
        cancel_btn = box.button(QMessageBox.StandardButton.Cancel)
        if cancel_btn is not None:
            cancel_btn.setText(self.tr("Cancelar"))
        box.exec()
        clicked = box.clickedButton()
        if clicked is yes_btn:
            self._macos_eula_mark_acknowledged(vm_dir)
            try:
                self.log_message(
                    f"==> Aviso legal de macOS aceptado para '{vm_name}'."
                )
            except Exception:
                pass
            return True
        try:
            self.log_message(
                f"==> Arranque de '{vm_name}' cancelado: aviso legal de "
                f"macOS no aceptado."
            )
        except Exception:
            pass
        return False

    def _maybe_show_macos_create_notice(self, *_args):
        """Aviso breve al seleccionar macOS como plataforma.

        Se muestra UNA vez por sesión (flag en memoria, no persistente).
        No bloquea: es un QMessageBox.information informativo.
        """
        # config_tab_gating_v2: si estamos abriendo una VM existente
        # (open_vm), no mostramos el aviso breve. Solo aplica a la
        # creación de VMs nuevas.
        if getattr(self, "_opening_vm", False):
            return
        try:
            os_type = self.combo_main_os.currentData()
        except Exception:
            return
        if os_type != "macos":
            return
        if getattr(self, "_macos_notice_shown_this_session", False):
            return
        self._macos_notice_shown_this_session = True
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                self.tr("Aviso legal — macOS"),
                self._macos_eula_short_text(),
            )
        except Exception:
            pass

    # ==================================================================
    # Pantalla de bienvenida (marcador welcome_screen_v1)
    # ==================================================================
    # Cuando no existe ninguna VM, el panel izquierdo muestra una
    # pantalla de bienvenida en vez de la lista vacía. La comprobación
    # se hace al final de refresh_vm_list, que es el punto por el que
    # pasa cualquier cambio en el conjunto de VMs (crear, importar,
    # borrar, clonar).

    def _update_vm_list_stack(self):
        """Decide qué página del vm_area_stack mostrar.

        Página 0 → lista de VMs (comportamiento normal).
        Página 1 → bienvenida (cuando list_existing_vms() == []).

        También deshabilita el buscador, el combo de orden, el combo
        de grupo y el toggle de vista cuando la bienvenida está visible:
        sin VMs no tienen sentido y su estado deshabilitado evita
        confusión visual.
        """
        stack = getattr(self, "vm_area_stack", None)
        if stack is None:
            return
        try:
            vms = list_existing_vms()
        except Exception:
            vms = []
        has_vms = bool(vms)
        try:
            stack.setCurrentIndex(0 if has_vms else 1)
        except Exception:
            pass
        # Deshabilitar los controles del panel izquierdo si no hay VMs.
        for attr in ("input_vm_search", "combo_vm_order",
                     "combo_vm_group", "btn_toggle_vm_view"):
            w = getattr(self, attr, None)
            if w is None:
                continue
            try:
                w.setEnabled(has_vms)
            except Exception:
                pass
        # El botón "Nueva VM" sigue siempre habilitado: sin él no se
        # podría crear la primera VM si por algún motivo no se quiere
        # usar el botón grande de la bienvenida.
        # config_tab_gating_v1: reevaluar la habilitación de la
        # pestaña "Configuración VM" cuando cambia el conjunto de VMs.
        try:
            self._update_config_tab_gating()
        except Exception:
            pass

    def _welcome_create_vm(self, *_args):
        """Botón 'Crear una VM nueva' de la bienvenida."""
        try:
            self.new_vm()
        except Exception as e:
            try:
                self.log_message(f"[AVISO] welcome: {e}")
            except Exception:
                pass

    def _welcome_import_vm(self, *_args):
        """Botón 'Importar desde OVA/OVF…' de la bienvenida."""
        try:
            self.import_vm()
        except Exception as e:
            try:
                self.log_message(f"[AVISO] welcome: {e}")
            except Exception:
                pass

    def _welcome_open_media(self, *_args):
        """Botón 'Abrir Biblioteca de Medios' de la bienvenida."""
        try:
            idx = getattr(self, "_media_tab_index", -1)
            if idx is not None and idx >= 0 and hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass

    def _welcome_open_help(self, *_args):
        """Botón 'Ver la Ayuda' de la bienvenida."""
        try:
            idx = getattr(self, "_help_tab_index", -1)
            if idx is not None and idx >= 0 and hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass

    # ==================================================================
    # Vista de lista / tarjetas (marcador vm_grid_view_v1)
    # ==================================================================
    # Un solo QListWidget con dos modos:
    #   • "list" (por defecto) → QListView.ViewMode.ListMode.
    #   • "grid"               → QListView.ViewMode.IconMode.
    #
    # Al cambiar de modo hay que reajustar:
    #   - iconSize del widget.
    #   - gridSize (solo aplica en IconMode).
    #   - sizeHint de cada item (QSize(0,36) en lista, QSize(160,180) en grid).
    #   - resizeMode (Adjust en grid, Fixed en lista).
    # Después, doItemsLayout() fuerza el re-layout: sin esta llamada, Qt
    # no repinta el widget al cambiar viewMode en runtime.
    #
    # El modo se persiste en QSettings("layout/vm_view_mode").

    _VM_VIEW_MODES = ("list", "grid")

    def _vm_view_mode(self):
        """Devuelve 'list' o 'grid'. Default: 'list'."""
        try:
            from PyQt6.QtCore import QSettings
            m = str(QSettings().value("layout/vm_view_mode", "list") or "list")
        except Exception:
            m = "list"
        return m if m in self._VM_VIEW_MODES else "list"

    def _vm_view_is_grid(self):
        return self._vm_view_mode() == "grid"

    def _apply_vm_view_mode(self, mode):
        """Aplica `mode` ('list' | 'grid') al vm_list y ajusta los items.

        Idempotente: se puede llamar tantas veces como se quiera.
        """
        if mode not in self._VM_VIEW_MODES:
            mode = "list"
        w = getattr(self, "vm_list", None)
        if w is None:
            return
        try:
            from PyQt6.QtWidgets import QListView, QListWidget
            from PyQt6.QtCore import QSize
        except Exception:
            return

        if mode == "grid":
            w.setViewMode(QListView.ViewMode.IconMode)
            w.setIconSize(QSize(96, 96))
            w.setGridSize(QSize(180, 200))
            w.setResizeMode(QListView.ResizeMode.Adjust)
            w.setMovement(QListView.Movement.Static)
            w.setWordWrap(True)
            w.setSpacing(6)
            new_hint = QSize(170, 190)
        else:
            w.setViewMode(QListView.ViewMode.ListMode)
            w.setIconSize(QSize(28, 28))
            w.setGridSize(QSize())   # 0×0 = sin grid en ListMode
            w.setResizeMode(QListView.ResizeMode.Fixed)
            w.setMovement(QListView.Movement.Static)
            w.setWordWrap(False)
            w.setSpacing(0)
            new_hint = QSize(0, 36)

        # Reajustar el sizeHint de cada item para que Qt recalcule las
        # celdas. Sin esto, las tarjetas se ven con el alto de la lista
        # (36 px), es decir, aplastadas.
        for i in range(w.count()):
            it = w.item(i)
            if it is None:
                continue
            try:
                it.setSizeHint(new_hint)
            except Exception:
                pass

        # Forzar el re-layout. Sin doItemsLayout(), cambiar viewMode en
        # runtime no repinta nada hasta el próximo resize.
        try:
            w.doItemsLayout()
        except Exception:
            pass

        # vm_grid_view_v2_card: instalar el delegate solo en modo tarjeta.
        # En modo lista se quita y se vuelve al pintado estándar de Qt.
        try:
            if mode == "grid":
                if getattr(self, "_vm_card_delegate", None) is None:
                    self._vm_card_delegate = VmCardDelegate(w)
                w.setItemDelegate(self._vm_card_delegate)
            else:
                from PyQt6.QtWidgets import QStyledItemDelegate as _SID
                w.setItemDelegate(_SID(w))
        except Exception as _e:
            try:
                print(f"[AVISO] vm_grid_view_v2_card: {_e}")
                if hasattr(self, "log_message"):
                    self.log_message(f"[AVISO] vm_grid_view_v2_card: {_e}")
            except Exception:
                pass
        # Actualizar el botón toggle (muestra la ACCIÓN, no el estado).
        self._update_vm_view_toggle_button()

    def _update_vm_view_toggle_button(self):
        """Ajusta texto y tooltip del botón toggle al modo actual."""
        btn = getattr(self, "btn_toggle_vm_view", None)
        if btn is None:
            return
        mode = self._vm_view_mode()
        try:
            if mode == "grid":
                # La acción al pulsar es "pasar a lista".
                btn.setText("\U0001f4cb")  # 📋
                btn.setToolTip(self.tr("Cambiar a vista de lista."))
            else:
                # La acción al pulsar es "pasar a tarjetas".
                btn.setText("\U0001f5c2")  # 🗂
                btn.setToolTip(self.tr("Cambiar a vista de tarjetas."))
        except Exception:
            pass

    def _on_toggle_vm_view(self, *_args):
        """Slot del botón 📋/🗂: alterna el modo y lo persiste."""
        cur = self._vm_view_mode()
        new = "grid" if cur == "list" else "list"
        try:
            from PyQt6.QtCore import QSettings
            QSettings().setValue("layout/vm_view_mode", new)
        except Exception:
            pass
        # Refrescar la lista ANTES de aplicar el modo: refresh_vm_list
        # recrea los items con el sizeHint de lista por defecto, así que
        # hay que aplicar el modo nuevo DESPUÉS.
        try:
            self.refresh_vm_list()
        except Exception:
            pass
        self._apply_vm_view_mode(new)

    def _vm_view_size_hint(self):
        """Devuelve el QSize que corresponde al modo actual."""
        try:
            from PyQt6.QtCore import QSize
        except Exception:
            return None
        if self._vm_view_is_grid():
            return QSize(170, 190)
        return QSize(0, 36)

    # ------------------------------------------------------------------
    # Notas contextuales por SO
    # ------------------------------------------------------------------
    # Texto mostrado en la caja informativa debajo de Nombre/Plataforma/
    # Versión de SO. La caja solo aparece si hay entrada para el SO elegido.
    # Se usan caracteres Unicode (no emoji del sistema) para que se vean
    # igual en cualquier tema de escritorio.
    # i18n_tanda2e3_os_notes: los avisos por SO viven en notes/<os>_<lang>.md
    # (Markdown). Se cargan segun el idioma activo con _load_localized_md().
    # Editar esos .md NO requiere tocar codigo ni recompilar traducciones.
    _OS_NOTES = {"linux", "windows", "macos", "android"}

# ------------------------------------------------------------------
    # Caché de load_vm_config (marcador vm_config_cache_v1)
    # ------------------------------------------------------------------
    # self._load_vm_config_cached() hace configparser.read + json.loads en cada llamada.
    # Al cambiar de VM en la lista lateral, open_vm + _update_manager_details
    # encadenan 4-5 lecturas del mismo vm_config.ini. Cacheamos por
    # (ruta, mtime): si el archivo no ha cambiado, devolvemos el dict ya
    # parseado. Cualquier escritura (propia o de otro hilo) cambia el
    # mtime, así que la próxima lectura lo detecta sin invalidación
    # explícita. Las escrituras propias además llaman a
    # _invalidate_vm_config_cache como red de seguridad, por si el
    # sistema de archivos tiene resolución de mtime baja.

    def _load_vm_config_cached(self, vm_dir):
        """Lee vm_config.ini con caché por (ruta, mtime)."""
        if not vm_dir:
            return {}
        cache = getattr(self, "_vm_config_cache", None)
        if cache is None:
            cache = {}
            try:
                self._vm_config_cache = cache
            except Exception:
                try:
                    return vm_config.load_vm_config(vm_dir)
                except Exception:
                    return {}
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        try:
            mtime = os.path.getmtime(cfg_path)
        except OSError:
            cache.pop(vm_dir, None)
            try:
                return vm_config.load_vm_config(vm_dir)
            except Exception:
                return {}
        entry = cache.get(vm_dir)
        if entry is not None and entry[0] == mtime:
            return entry[1]
        try:
            data = vm_config.load_vm_config(vm_dir)
        except Exception:
            return {}
        cache[vm_dir] = (mtime, data)
        return data

    def _invalidate_vm_config_cache(self, vm_dir=None):
        """Invalida la caché de vm_config.ini (toda o solo una VM)."""
        cache = getattr(self, "_vm_config_cache", None)
        if not cache:
            return
        if vm_dir is None:
            cache.clear()
        else:
            cache.pop(vm_dir, None)


    # ------------------------------------------------------------------
    # Grupos y colores de VM (marcador vm_label_v1)
    # ------------------------------------------------------------------
    # Cada VM puede pertenecer a un grupo (etiqueta textual libre) y
    # tener un color asociado. Se guardan en extra["group"] y
    # extra["color"] dentro de vm_config.ini.
    #
    # El grupo es texto libre: el usuario puede crear grupos nuevos
    # escribiendo un nombre que no existía. La lista de grupos
    # existentes se calcula al vuelo recorriendo todas las VMs.

    _VM_LABEL_COLORS = [
        ("Rojo",       "#e53935"),
        ("Naranja",    "#fb8c00"),
        ("Ámbar",      "#fdd835"),
        ("Verde",      "#43a047"),
        ("Verde azul", "#00897b"),
        ("Azul",       "#1e88e5"),
        ("Índigo",     "#3949ab"),
        ("Violeta",    "#8e24aa"),
        ("Rosa",       "#d81b60"),
        ("Gris",       "#757575"),
    ]

    def _load_vm_group(self, vm_dir):
        if not vm_dir:
            return ""
        try:
            data = self._load_vm_config_cached(vm_dir)
            return str((data.get("extra") or {}).get("group") or "")
        except Exception:
            return ""

    def _load_vm_color(self, vm_dir):
        if not vm_dir:
            return ""
        try:
            data = self._load_vm_config_cached(vm_dir)
            return str((data.get("extra") or {}).get("color") or "")
        except Exception:
            return ""

    def _save_vm_label(self, vm_dir, group, color):
        """Guarda grupo y color en extra[]. Cadena vacía → borra la clave."""
        if not vm_dir:
            return
        import json as _json, configparser as _cfg
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        c = _cfg.ConfigParser(interpolation=None)
        c.read(cfg_path, encoding="utf-8")
        if not c.has_section("extra"):
            c.add_section("extra")
        try:
            extra = _json.loads(c["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        group = (group or "").strip()
        color = (color or "").strip()
        if group:
            extra["group"] = group
        else:
            extra.pop("group", None)
        if color:
            extra["color"] = color
        else:
            extra.pop("color", None)
        c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(vm_dir)

    def _all_vm_groups(self):
        """Devuelve el conjunto de grupos existentes en todas las VMs."""
        groups = set()
        try:
            import vm_config as _vc
            for name in _vc.list_existing_vms():
                d = os.path.join(_vc.BASE_VM_DIR, name)
                g = self._load_vm_group(d)
                if g:
                    groups.add(g)
        except Exception:
            pass
        return sorted(groups)

        # vm_config_save_cancel_v1_grupo_b_doc:
        # Este campo forma parte del "Grupo B" y se auto-guarda a
        # proposito: NO pasa por el modelo Guardar/Descartar del
        # "Grupo A" (vm_config_save_cancel_v1_*). Motivos:
        #   1. No tiene widget persistente en la pestana Configuracion
        #      VM (este ajuste vive en su propio dialogo o su propio
        #      panel).
        #   2. El usuario espera que un cambio aqui se aplique ya, sin
        #      un paso extra de "Guardar configuracion".
        #   3. Coherente con guest_agent_enabled y clipboard_mode, que
        #      estan en el mismo caso.
        # Si en el futuro se quisiera integrar en el modelo dirty,
        # habria que:
        #   - Darle un widget persistente en la pestana Configuracion VM,
        #   - Anadirlo a _collect_config_from_ui() y _load_config_comparable(),
        #   - Engancharlo a _wire_config_dirty_signals(),
        #   - Anadirlo a la lista de claves comparadas en _has_pending_changes().
    def edit_vm_label(self):
        """Abre el diálogo de grupo + color para la VM seleccionada."""
        if not self._vm_is_selected():
            QMessageBox.information(
                self, self.tr("Etiqueta de la VM"),
                self.tr("Selecciona primero una máquina virtual."),
            )
            return
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
            QLabel, QComboBox, QPushButton, QGridLayout, QWidget,
        )
        from PyQt6.QtGui import QColor, QPixmap, QIcon

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)
        cur_group = self._load_vm_group(vm_dir)
        cur_color = self._load_vm_color(vm_dir)

        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Etiqueta - {0}").format(vm_name))
        dlg.setModal(True)
        dlg.resize(520, 400)
        layout = QVBoxLayout(dlg)

        info = QLabel(
            self.tr("Grupo y color para <b>{0}</b>. El grupo es texto "
                    "libre: escribe uno nuevo para crearlo. El color se aplica "
                    "como fondo suave del ítem en la lista lateral.").format(vm_name)
        )
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        cmb = QComboBox()
        cmb.setEditable(True)
        cmb.addItem("", "")
        for g in self._all_vm_groups():
            cmb.addItem(g, g)
        if cur_group:
            idx = cmb.findData(cur_group)
            if idx < 0:
                cmb.addItem(cur_group, cur_group)
                idx = cmb.findData(cur_group)
            cmb.setCurrentIndex(idx)
        else:
            cmb.setCurrentIndex(0)
        cmb.lineEdit().setPlaceholderText(self.tr("(sin grupo)"))
        form.addRow(self.tr("Grupo:"), cmb)
        layout.addLayout(form)

        layout.addWidget(QLabel(self.tr("<b>Color:</b>")))
        selected = {"color": cur_color}

        grid_wrap = QWidget()
        grid = QGridLayout(grid_wrap)
        grid.setSpacing(6)

        btns = []

        def _swatch_icon(hex_color):
            pm = QPixmap(24, 24)
            pm.fill(QColor(hex_color))
            return QIcon(pm)

        none_btn = QPushButton(self.tr("Sin color"))
        none_btn.setCheckable(True)
        none_btn.setChecked(not cur_color)
        none_btn.setIcon(_swatch_icon("#ffffff"))
        grid.addWidget(none_btn, 0, 0, 1, 5)
        btns.append(("", none_btn))

        for i, (label, hex_c) in enumerate(self._VM_LABEL_COLORS):
            row = 1 + i // 5
            col = i % 5
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(cur_color.lower() == hex_c.lower())
            b.setIcon(_swatch_icon(hex_c))
            grid.addWidget(b, row, col)
            btns.append((hex_c, b))

        def _apply_swatch_style():
            """Marca visualmente el botón del color elegido.

            setChecked() solo cambia el estado interno; con el QSS global
            de la app no se aprecia diferencia. Aquí forzamos un borde
            azul grueso y un fondo suave en el botón seleccionado.
            """
            cur = (selected.get("color") or "").lower()
            for h, b in btns:
                is_sel = (h.lower() == cur)
                b.setChecked(is_sel)
                if is_sel:
                    b.setStyleSheet(
                        "QPushButton { border: 3px solid #1976d2; "
                        "border-radius: 6px; padding: 4px 10px; "
                        "font-weight: bold; background: #e3f2fd; }"
                    )
                else:
                    b.setStyleSheet(
                        "QPushButton { border: 1px solid palette(mid); "
                        "border-radius: 6px; padding: 6px 10px; }"
                    )

        def _on_pick(hex_c):
            selected["color"] = hex_c
            _apply_swatch_style()
            try:
                self.log_message(
                    f"[DIAG] Etiqueta: color elegido = "
                    f"{hex_c or '(sin color)'}"
                )
            except Exception:
                pass

        none_btn.clicked.connect(lambda: _on_pick(""))
        for hex_c, b in btns:
            if hex_c:
                b.clicked.connect(lambda _checked=False, h=hex_c: _on_pick(h))

        # Aplicar el estado visual inicial tras crear todos los botones.
        _apply_swatch_style()

        layout.addWidget(grid_wrap)
        layout.addStretch(1)

        bottom = QHBoxLayout()
        clear_btn = QPushButton(self.tr("Quitar etiqueta"))
        cancel_btn = QPushButton(self.tr("Cancelar"))
        save_btn = QPushButton(self.tr("Guardar"))
        save_btn.setDefault(True)
        clear_btn.clicked.connect(lambda: (cmb.setCurrentIndex(0), _on_pick("")))
        cancel_btn.clicked.connect(dlg.reject)

        def _save():
            g = (cmb.currentText() or "").strip()
            try:
                self._save_vm_label(vm_dir, g, selected["color"])
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(
                    self, self.tr("Etiqueta"),
                    self.tr("No se pudo guardar la etiqueta.\n\n{0}").format(e),
                )

        save_btn.clicked.connect(_save)
        bottom.addWidget(clear_btn)
        bottom.addStretch(1)
        bottom.addWidget(cancel_btn)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.refresh_vm_list()
                self._update_manager_details()
                self.log_message(f"==> Etiqueta guardada para '{vm_name}'.")
            except Exception:
                pass


    # ==================================================================
    # Historial — diálogo completo (marcador vm_history_v1, E3b)
    # ==================================================================

    def _show_history_dialog(self):
        """Abre el diálogo modal con la tabla completa de sesiones."""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
            QFileDialog, QMessageBox,
        )
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtGui import QColor, QBrush

        if not self.current_vm_dir:
            QMessageBox.information(
                self, self.tr("Historial"),
                self.tr("Selecciona primero una máquina virtual."),
            )
            return

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)
        data = self._history_load(vm_dir)
        sessions = data.get("sessions") or []

        dlg = QDialog(self)
        dlg.setWindowTitle(
            self.tr("Historial de uso — {0}").format(vm_name)
        )
        dlg.setModal(True)
        dlg.resize(820, 540)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        info = QLabel(self.tr(
            "Todas las sesiones registradas de esta máquina virtual.<br>"
            "Haz clic en el título de una columna para ordenar "
            "(ascendente / descendente)."
        ))
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels([
            self.tr("Inicio"),
            self.tr("Fin"),
            self.tr("Duración"),
            self.tr("Motivo"),
        ])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(False)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setSortingEnabled(True)
        tree.setUniformRowHeights(True)

        header = tree.header()
        header.setSectionsClickable(True)
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )

        # Colores por motivo del cierre.
        _colores = {
            "acpi":    QColor("#e8f5e9"),  # verde claro
            "forced":  QColor("#fff3e0"),  # ámbar claro
            "crash":   QColor("#ffebee"),  # rojo claro
            "unknown": QColor("#f5f5f5"),  # gris claro
        }
        _etiquetas_motivo = {
            "acpi":    self.tr("ACPI (apagado ordenado)"),
            "forced":  self.tr("Forzado (por el usuario)"),
            "crash":   self.tr("Cierre anómalo"),
            "unknown": self.tr("Desconocido"),
        }

        for s in sessions:
            start_iso = s.get("start") or ""
            end_iso = s.get("end")
            dur = s.get("duration_sec")
            reason = (s.get("stop_reason") or "unknown")

            it = _HistoryTreeItem()
            # Columna 0 — Inicio
            it.setText(0, self._format_history_datetime(start_iso))
            it.setData(0, _Qt.ItemDataRole.UserRole, start_iso)
            # Columna 1 — Fin
            it.setText(1, self._format_history_datetime(end_iso)
                       if end_iso else self.tr("(en curso)"))
            it.setData(1, _Qt.ItemDataRole.UserRole, end_iso or "")
            # Columna 2 — Duración
            it.setText(2, self._format_history_duration(dur)
                       if dur is not None else "—")
            try:
                it.setData(2, _Qt.ItemDataRole.UserRole, int(dur or 0))
            except Exception:
                it.setData(2, _Qt.ItemDataRole.UserRole, 0)
            # Columna 3 — Motivo
            it.setText(3, _etiquetas_motivo.get(reason, reason))
            it.setData(3, _Qt.ItemDataRole.UserRole,
                       _etiquetas_motivo.get(reason, reason))

            # Fondo por motivo.
            bg = _colores.get(reason)
            if bg is not None:
                brush = QBrush(bg)
                for c in range(4):
                    it.setBackground(c, brush)

            tree.addTopLevelItem(it)

        # Orden por defecto: Inicio descendente (lo más reciente arriba).
        # Lo dejamos en desc porque es lo que un usuario quiere ver.
        try:
            tree.sortItems(0, _Qt.SortOrder.DescendingOrder)
        except Exception:
            pass

        # Guardar estado de ordenación por si el usuario hace clic.
        self._history_sort_col = 0
        self._history_sort_asc = False

        def _on_header_clicked(col):
            # Alternar asc/desc si es la misma columna; si es otra,
            # empezar por ascendente (excepto si es "Inicio"/"Fin",
            # donde ascendente tiene poco sentido).
            if col == getattr(self, "_history_sort_col", 0):
                asc = not getattr(self, "_history_sort_asc", False)
            else:
                asc = (col not in (0, 1))  # fechas: empezar por desc
            self._history_sort_col = col
            self._history_sort_asc = asc
            order = (_Qt.SortOrder.AscendingOrder if asc
                     else _Qt.SortOrder.DescendingOrder)
            tree.sortItems(col, order)

        try:
            header.sectionClicked.connect(_on_header_clicked)
        except Exception:
            pass

        layout.addWidget(tree, 1)

        # --- Resumen al pie ---
        summary = self._history_summary(vm_dir)
        total = int(summary.get("total") or 0)
        uptime = int(summary.get("total_uptime") or 0)
        if summary.get("current_open"):
            uptime += int(summary.get("current_uptime") or 0)
        foot = QLabel(self.tr(
            "<b>Total:</b> {0} sesiones · "
            "<b>Uptime acumulado:</b> {1}"
        ).format(total, self._format_history_duration(uptime)))
        foot.setTextFormat(_Qt.TextFormat.RichText)
        layout.addWidget(foot)

        # --- Botones ---
        row = QHBoxLayout()

        btn_csv = QPushButton(self.tr("\U0001f4c4 Exportar a CSV"))
        btn_csv.setToolTip(self.tr(
            "Guarda el historial completo como archivo CSV para "
            "abrilo con LibreOffice, Excel o cualquier hoja de cálculo."
        ))
        row.addWidget(btn_csv)

        btn_clear = QPushButton(self.tr("\U0001f5d1 Borrar historial"))
        btn_clear.setToolTip(self.tr(
            "Elimina TODO el historial de esta VM. La acción no se "
            "puede deshacer."
        ))
        row.addWidget(btn_clear)

        row.addStretch(1)

        btn_close = QPushButton(self.tr("Cerrar"))
        btn_close.setDefault(True)
        row.addWidget(btn_close)

        layout.addLayout(row)

        # --- Callbacks ---
        def _refresh_dialog():
            """Recarga el historial (tras un borrado o cambio)."""
            try:
                new_data = self._history_load(vm_dir)
                new_sessions = new_data.get("sessions") or []
                tree.clear()
                for s2 in new_sessions:
                    start_iso2 = s2.get("start") or ""
                    end_iso2 = s2.get("end")
                    dur2 = s2.get("duration_sec")
                    reason2 = (s2.get("stop_reason") or "unknown")

                    it2 = _HistoryTreeItem()
                    it2.setText(0, self._format_history_datetime(start_iso2))
                    it2.setData(0, _Qt.ItemDataRole.UserRole, start_iso2)
                    it2.setText(1, self._format_history_datetime(end_iso2)
                                if end_iso2 else self.tr("(en curso)"))
                    it2.setData(1, _Qt.ItemDataRole.UserRole, end_iso2 or "")
                    it2.setText(2, self._format_history_duration(dur2)
                                if dur2 is not None else "—")
                    try:
                        it2.setData(2, _Qt.ItemDataRole.UserRole,
                                    int(dur2 or 0))
                    except Exception:
                        it2.setData(2, _Qt.ItemDataRole.UserRole, 0)
                    it2.setText(3, _etiquetas_motivo.get(reason2, reason2))
                    it2.setData(3, _Qt.ItemDataRole.UserRole,
                                _etiquetas_motivo.get(reason2, reason2))
                    bg2 = _colores.get(reason2)
                    if bg2 is not None:
                        brush2 = QBrush(bg2)
                        for c in range(4):
                            it2.setBackground(c, brush2)
                    tree.addTopLevelItem(it2)
                # Reaplicar el orden actual.
                try:
                    order = (_Qt.SortOrder.AscendingOrder
                             if getattr(self, "_history_sort_asc", False)
                             else _Qt.SortOrder.DescendingOrder)
                    tree.sortItems(getattr(self, "_history_sort_col", 0),
                                   order)
                except Exception:
                    pass
                # Actualizar resumen al pie.
                new_summary = self._history_summary(vm_dir)
                _t = int(new_summary.get("total") or 0)
                _u = int(new_summary.get("total_uptime") or 0)
                if new_summary.get("current_open"):
                    _u += int(new_summary.get("current_uptime") or 0)
                foot.setText(self.tr(
                    "<b>Total:</b> {0} sesiones · "
                    "<b>Uptime acumulado:</b> {1}"
                ).format(_t, self._format_history_duration(_u)))
            except Exception:
                pass

        def _on_export_csv():
            try:
                suggested = os.path.join(
                    os.path.expanduser("~"),
                    f"{vm_name}-historial.csv",
                )
                path, _ = QFileDialog.getSaveFileName(
                    dlg, self.tr("Guardar historial como CSV"),
                    suggested,
                    self.tr("Archivos CSV (*.csv);;Todos los archivos (*)"),
                )
                if not path:
                    return
                if not path.lower().endswith(".csv"):
                    path += ".csv"
                import csv as _csv
                with open(path, "w", newline="", encoding="utf-8") as f:
                    w = _csv.writer(f)
                    w.writerow([
                        "inicio", "fin", "duracion_seg",
                        "duracion_texto", "motivo", "start_reason",
                    ])
                    for s3 in (self._history_load(vm_dir).get("sessions") or []):
                        w.writerow([
                            s3.get("start") or "",
                            s3.get("end") or "",
                            s3.get("duration_sec") or 0,
                            self._format_history_duration(
                                s3.get("duration_sec") or 0),
                            s3.get("stop_reason") or "unknown",
                            s3.get("start_reason") or "user",
                        ])
                QMessageBox.information(
                    dlg, self.tr("Exportar CSV"),
                    self.tr("Historial guardado en:\n\n{0}").format(path),
                )
            except Exception as e:
                QMessageBox.warning(
                    dlg, self.tr("Exportar CSV"),
                    self.tr("No se pudo guardar el CSV.\n\n{0}").format(e),
                )

        def _on_clear():
            resp = QMessageBox.question(
                dlg, self.tr("Borrar historial"),
                self.tr(
                    "Se eliminará TODO el historial de '{0}'.\n\n"
                    "Esta acción no se puede deshacer.\n\n"
                    "¿Continuar?"
                ).format(vm_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
            try:
                empty = {"version": self._HISTORY_VERSION, "sessions": []}
                self._history_save(vm_dir, empty)
                # Invalidar la caché del resumen.
                cache = getattr(self, "_history_cache", None)
                if cache is not None:
                    cache.pop(vm_dir, None)
                _refresh_dialog()
                # Refrescar también la sección compacta del Resumen.
                if hasattr(self, "_refresh_history_summary"):
                    try:
                        self._refresh_history_summary()
                    except Exception:
                        pass
                QMessageBox.information(
                    dlg, self.tr("Historial borrado"),
                    self.tr("El historial de '{0}' se ha borrado.").format(vm_name),
                )
            except Exception as e:
                QMessageBox.warning(
                    dlg, self.tr("Borrar historial"),
                    self.tr("No se pudo borrar el historial.\n\n{0}").format(e),
                )

        btn_csv.clicked.connect(_on_export_csv)
        btn_clear.clicked.connect(_on_clear)
        btn_close.clicked.connect(dlg.accept)

        dlg.exec()

    # ==================================================================
    # Historial — UI compacta (marcador vm_history_v1, E3a)
    # ==================================================================

    def _history_summary_cached(self, vm_dir):
        """Envuelve _history_summary con caché por (vm_dir, mtime).

        refresh_vm_runtime_status corre cada 1.5 s. Sin caché, leeríamos
        el history.json del disco ~40 veces por minuto por cada VM
        abierta. Con la caché, solo se re-lee si el archivo cambió.

        OJO: `current_uptime` NO se cachea. Mientras la VM está encendida,
        el history.json no cambia (la sesión abierta tiene end:null y no
        se reescribe), pero `current_uptime` depende de la hora actual.
        Cachearlo dejaba el contador clavado en el valor del primer tick
        (bug detectado el 2026-10-04 con la VM recién arrancada: se
        quedaba en "hace 1 s"). Solución: cachear solo lo que viene del
        archivo; recalcular el "uptime en vivo" en cada llamada.
        """
        if not vm_dir:
            return None
        cache = getattr(self, "_history_cache", None)
        if cache is None:
            cache = {}
            try:
                self._history_cache = cache
            except Exception:
                pass
        path = self._history_path(vm_dir)
        try:
            mtime = os.path.getmtime(path) if path else 0
        except OSError:
            mtime = 0
        entry = cache.get(vm_dir)
        if entry is not None and entry[0] == mtime:
            data = dict(entry[1])
        else:
            data = self._history_summary(vm_dir)
            cache[vm_dir] = (mtime, dict(data))
        # Recalcular SIEMPRE el uptime en vivo, si hay sesión abierta.
        if data.get("current_open"):
            from datetime import datetime as _dt
            try:
                t0 = _dt.fromisoformat(data.get("current_start") or "")
                data["current_uptime"] = int(
                    (_dt.now() - t0).total_seconds()
                )
            except Exception:
                data["current_uptime"] = 0
        return data

    @staticmethod
    def _format_history_duration(seconds):
        """Formatea una duración en segundos: '45 s', '5 min 12 s',
        '1 h 22 min', '2 d 3 h 5 min'."""
        try:
            s = int(seconds or 0)
        except Exception:
            return "—"
        if s < 0:
            s = 0
        if s < 60:
            return f"{s} s"
        mins, sec = divmod(s, 60)
        if mins < 60:
            if sec:
                return f"{mins} min {sec} s"
            return f"{mins} min"
        hours, mins = divmod(mins, 60)
        if hours < 24:
            if mins:
                return f"{hours} h {mins} min"
            return f"{hours} h"
        days, hours = divmod(hours, 24)
        if hours:
            return f"{days} d {hours} h"
        return f"{days} d"

    @staticmethod
    def _format_history_datetime(iso):
        """ISO → '04 oct 2026 13:44'."""
        if not iso:
            return "—"
        try:
            from datetime import datetime as _dt
            d = _dt.fromisoformat(iso)
            _meses = ("ene", "feb", "mar", "abr", "may", "jun",
                      "jul", "ago", "sep", "oct", "nov", "dic")
            return (f"{d.day:02d} {_meses[d.month - 1]} {d.year} "
                    f"{d.hour:02d}:{d.minute:02d}")
        except Exception:
            return str(iso)

    @staticmethod
    def _format_history_relative(iso):
        """ISO → 'hace 2 h', 'hace 5 min', 'hace 3 d'."""
        if not iso:
            return "—"
        try:
            from datetime import datetime as _dt
            d = _dt.fromisoformat(iso)
            delta = _dt.now() - d
            secs = int(delta.total_seconds())
            if secs < 0:
                return "en el futuro"
            if secs < 60:
                return f"hace {secs} s"
            mins = secs // 60
            if mins < 60:
                return f"hace {mins} min"
            hours = mins // 60
            if hours < 24:
                return f"hace {hours} h"
            days = hours // 24
            return f"hace {days} d"
        except Exception:
            return "—"

    def _refresh_history_summary(self):
        """Actualiza los 4 labels de la sección 'Historial de uso'.

        Se llama desde refresh_vm_runtime_status (cada tick), open_vm y
        new_vm. Si no hay VM seleccionada, limpia los labels.
        """
        if not hasattr(self, "history_total_label"):
            return
        vm_dir = self.current_vm_dir

        # Sin VM: todo a "—".
        if not vm_dir:
            self.history_total_label.setText(
                f"<b>{self.tr('Arranques totales')}:</b> \u2014"
            )
            self.history_uptime_label.setText(
                f"<b>{self.tr('Uptime acumulado')}:</b> \u2014"
            )
            self.history_last_label.setText(
                f"<b>{self.tr('Última sesión')}:</b> \u2014"
            )
            self.history_current_label.setText("")
            return

        try:
            s = self._history_summary_cached(vm_dir) or {}
        except Exception:
            s = {}

        total = int(s.get("total") or 0)
        uptime = int(s.get("total_uptime") or 0)

        # Uptime "en vivo" si hay una sesión abierta ahora mismo:
        # sumamos también el tiempo que lleva la sesión actual.
        if s.get("current_open"):
            uptime += int(s.get("current_uptime") or 0)

        self.history_total_label.setText(
            f"<b>{self.tr('Arranques totales')}:</b> {total}"
        )
        self.history_uptime_label.setText(
            f"<b>{self.tr('Uptime acumulado')}:</b> "
            f"{self._format_history_duration(uptime)}"
        )

        # Última sesión cerrada.
        last_end = s.get("last_end")
        last_dur = s.get("last_duration")
        if last_end:
            self.history_last_label.setText(
                f"<b>{self.tr('Última sesión')}:</b> "
                f"{self._format_history_relative(last_end)} "
                f"({self._format_history_duration(last_dur)})"
            )
        else:
            self.history_last_label.setText(
                f"<b>{self.tr('Última sesión')}:</b> \u2014"
            )

        # Estado actual.
        if s.get("current_open"):
            up = int(s.get("current_uptime") or 0)
            self.history_current_label.setText(
                "<span style=\"color:#2e7d32;font-weight:bold;\">"
                f"\u25cf {self.tr('Encendida')}</span> "
                f"{self.tr('desde hace')} "
                f"{self._format_history_duration(up)}"
            )
        else:
            self.history_current_label.setText(
                "<span style=\"color:#9e9e9e;\">"
                f"\u25cb {self.tr('Apagada')}</span>"
            )

    # ==================================================================
    # Historial de arranques / uptime (marcador vm_history_v1)
    # ==================================================================
    # Archivo por VM: <vm_dir>/history.json
    #
    # Modelo:
    #   {
    #     "version": 1,
    #     "sessions": [
    #       {"start": ISO8601, "end": ISO8601 | null,
    #        "duration_sec": int | null,
    #        "stop_reason": "acpi"|"forced"|"crash"|"unknown" | null,
    #        "start_reason": "user"|"autostart"|"force_reboot"}
    #     ]
    #   }
    #
    # Si la última sesión tiene "end": null, la VM está encendida
    # ahora mismo. Solo puede haber una sesión abierta a la vez.
    #
    # Rotación: máximo _HISTORY_MAX_SESSIONS (500). Al superarlo se
    # eliminan las más antiguas. La sesión abierta (si la hay) nunca
    # se elimina.

    _HISTORY_MAX_SESSIONS = 500
    _HISTORY_VERSION = 1

    def _history_path(self, vm_dir):
        """Ruta al history.json de la VM (o None si vm_dir está vacío)."""
        if not vm_dir:
            return None
        return os.path.join(vm_dir, "history.json")

    def _history_load(self, vm_dir):
        """Carga el historial de la VM. Devuelve siempre un dict válido.

        Si el archivo no existe o está corrupto, devuelve un historial
        vacío (con versión actual). Nunca lanza excepción: el historial
        es informativo, no crítico.
        """
        empty = {"version": self._HISTORY_VERSION, "sessions": []}
        path = self._history_path(vm_dir)
        if not path or not os.path.isfile(path):
            return empty
        try:
            import json as _json
            with open(path, "r", encoding="utf-8") as f:
                data = _json.load(f)
            if not isinstance(data, dict):
                return empty
            sessions = data.get("sessions")
            if not isinstance(sessions, list):
                sessions = []
            # Validar mínimamente cada entrada (no petar si el JSON
            # fue editado a mano con campos raros).
            clean = []
            for s in sessions:
                if not isinstance(s, dict):
                    continue
                entry = {
                    "start": s.get("start") or "",
                    "end": s.get("end"),
                    "duration_sec": s.get("duration_sec"),
                    "stop_reason": s.get("stop_reason"),
                    "start_reason": s.get("start_reason") or "user",
                }
                clean.append(entry)
            return {"version": self._HISTORY_VERSION, "sessions": clean}
        except Exception as e:
            # El historial es prescindible: si falla, se empieza limpio.
            try:
                if hasattr(self, "log_message"):
                    self.log_message(
                        f"[AVISO] Historial de '{os.path.basename(vm_dir)}' "
                        f"ilegible; se reinicia. Detalle: {e}"
                    )
            except Exception:
                pass
            return empty

    def _history_save(self, vm_dir, data):
        """Guarda el historial con escritura atómica.

        Usa tempfile + os.replace. Si falla, no rompe nada: solo
        loguea y sigue. El historial no es información crítica.
        """
        path = self._history_path(vm_dir)
        if not path:
            return False
        try:
            import json as _json, tempfile as _tmp
            dirn = os.path.dirname(path) or "."
            fd, tmp = _tmp.mkstemp(
                prefix=".history_", suffix=".json.tmp", dir=dirn,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    _json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, path)
            except Exception:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
                raise
            return True
        except Exception as e:
            try:
                if hasattr(self, "log_message"):
                    self.log_message(
                        f"[AVISO] No se pudo guardar el historial de "
                        f"'{os.path.basename(vm_dir)}': {e}"
                    )
            except Exception:
                pass
            return False

    def _history_rotate(self, sessions):
        """Recorta `sessions` a _HISTORY_MAX_SESSIONS.

        Nunca elimina la última si está abierta (end == None): esa
        sesión representa el estado actual de la VM. Si la lista está
        llena y la última está abierta, se eliminan las más antiguas
        dejando espacio para la abierta.
        """
        if not isinstance(sessions, list):
            return []
        maxn = self._HISTORY_MAX_SESSIONS
        if len(sessions) <= maxn:
            return sessions
        # Reservar 1 hueco si la última está abierta.
        last_open = bool(sessions and sessions[-1].get("end") is None)
        keep_n = maxn - (1 if last_open else 0)
        if keep_n < 1:
            keep_n = 1
        return sessions[-keep_n:]

    def _history_start(self, vm_dir, reason="user"):
        """Registra el arranque de una VM.

        Añade una nueva sesión con `end=null`. Si ya había una sesión
        abierta (arranque sin cierre previo registrado — caso típico
        tras un cierre de la app con la VM aún corriendo), la cierra
        como `stop_reason="unknown"` antes de añadir la nueva.
        """
        if not vm_dir or not os.path.isdir(vm_dir):
            return
        from datetime import datetime as _dt
        data = self._history_load(vm_dir)
        sessions = data.get("sessions") or []

        # Cerrar sesión abierta previa, si la hay.
        if sessions and sessions[-1].get("end") is None:
            try:
                prev_start = sessions[-1].get("start") or ""
                t0 = _dt.fromisoformat(prev_start) if prev_start else None
            except Exception:
                t0 = None
            now = _dt.now()
            sessions[-1]["end"] = now.isoformat(timespec="seconds")
            sessions[-1]["stop_reason"] = "unknown"
            if t0 is not None:
                try:
                    sessions[-1]["duration_sec"] = int(
                        (now - t0).total_seconds()
                    )
                except Exception:
                    sessions[-1]["duration_sec"] = None

        # Añadir la nueva sesión abierta.
        sessions.append({
            "start": _dt.now().isoformat(timespec="seconds"),
            "end": None,
            "duration_sec": None,
            "stop_reason": None,
            "start_reason": reason or "user",
        })
        sessions = self._history_rotate(sessions)
        data["sessions"] = sessions
        data["version"] = self._HISTORY_VERSION
        self._history_save(vm_dir, data)

    def _history_end(self, vm_dir, stop_reason="unknown"):
        """Cierra la última sesión abierta del historial de la VM.

        Si no hay ninguna abierta, no hace nada (es idempotente:
        evita duplicar cierres si el watchdog pasa varias veces por
        el mismo estado transitorio).
        """
        if not vm_dir or not os.path.isdir(vm_dir):
            return
        from datetime import datetime as _dt
        data = self._history_load(vm_dir)
        sessions = data.get("sessions") or []
        if not sessions:
            return
        last = sessions[-1]
        if last.get("end") is not None:
            return  # ya cerrada
        now = _dt.now()
        try:
            t0 = _dt.fromisoformat(last.get("start") or "")
        except Exception:
            t0 = None
        last["end"] = now.isoformat(timespec="seconds")
        last["stop_reason"] = stop_reason or "unknown"
        if t0 is not None:
            try:
                last["duration_sec"] = int((now - t0).total_seconds())
            except Exception:
                last["duration_sec"] = None
        data["sessions"] = sessions
        self._history_save(vm_dir, data)

    def _history_on_transition(self, vm_name, prev_state, new_state):
        """Se llama desde el watchdog al detectar un cambio de estado.

        Solo actúa cuando la VM pasa de "running"/"paused" a "stopped".
        El `stop_reason` se deduce así:

          1. Si el usuario pulsó Apagar (ACPI): self._vm_stop_intent
             tiene "acpi" → stop_reason="acpi".
          2. Si forzó apagado/reinicio: "forced" → stop_reason="forced".
          3. Si el watchdog detectó pid huérfano: "crash".
          4. En cualquier otro caso: "unknown".

        El flag de intención se limpia tras usarlo (una sola vez).
        """
        if not vm_name:
            return
        if prev_state not in ("running", "paused"):
            return
        if new_state != "stopped":
            return
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
        if not os.path.isdir(vm_dir):
            return

        # Prioridad 1: intención explícita del usuario.
        intents = getattr(self, "_vm_stop_intent", None) or {}
        reason = intents.pop(vm_name, None)
        if reason not in ("acpi", "forced", "crash"):
            # Prioridad 2: el watchdog ya distinguió "muerte inesperada".
            try:
                if self._watchdog_detect_death(vm_name):
                    reason = "crash"
            except Exception:
                pass
        if not reason:
            # vm_history_v1 — fix1: si no hay intención explícita
            # del usuario, no lo dejamos como "unknown": la VM se
            # detuvo sin que la app lo pidiera, y eso es más útil
            # marcarlo como "crash". Cubre:
            #   - kill -9 externo al proceso de QEMU.
            #   - cierre del host con la VM corriendo.
            #   - apagado iniciado desde dentro del guest.
            # El pid huérfano ya no es necesario para detectar el
            # caso: si no hay intención, es anómalo por definición.
            reason = "crash"
        try:
            self._vm_stop_intent = intents
        except Exception:
            pass
        self._history_end(vm_dir, stop_reason=reason)

    def _history_summary(self, vm_dir):
        """Devuelve los datos que muestra la sección de Resumen.

        Claves:
          - total:          nº de sesiones registradas
          - total_uptime:   segundos totales
          - last_start:     ISO de la última sesión (o None)
          - last_end:       ISO del último cierre (o None)
          - last_duration:  duración de la última sesión cerrada (s) | None
          - current_open:   True si hay una sesión abierta ahora
          - current_start:  ISO de la sesión abierta (o None)
          - current_uptime: segundos desde el inicio de la sesión abierta
        """
        out = {
            "total": 0, "total_uptime": 0,
            "last_start": None, "last_end": None, "last_duration": None,
            "current_open": False, "current_start": None,
            "current_uptime": 0,
        }
        if not vm_dir:
            return out
        data = self._history_load(vm_dir)
        sessions = data.get("sessions") or []
        out["total"] = len(sessions)
        for s in sessions:
            try:
                out["total_uptime"] += int(s.get("duration_sec") or 0)
            except Exception:
                pass
        if sessions:
            last = sessions[-1]
            out["last_start"] = last.get("start")
            out["last_end"] = last.get("end")
            out["last_duration"] = last.get("duration_sec")
            if last.get("end") is None:
                out["current_open"] = True
                out["current_start"] = last.get("start")
                from datetime import datetime as _dt
                try:
                    t0 = _dt.fromisoformat(last.get("start") or "")
                    out["current_uptime"] = int(
                        (_dt.now() - t0).total_seconds()
                    )
                except Exception:
                    out["current_uptime"] = 0
        return out

    # ==================================================================
    # Menú contextual + doble clic en la lista de VMs (vm_context_menu_v1)
    # ==================================================================
    # Clic derecho sobre una VM → menú con las acciones más usadas.
    # Doble clic sobre una VM → salta a la pestaña Resumen.
    #
    # El menú se construye a partir del estado REAL de la VM en el
    # momento del clic derecho (running/paused/stopped, es clon
    # enlazado o no, etc.), así siempre muestra la acción correcta.

    def _vm_context_menu_state(self, vm_dir):
        """Devuelve un dict con el estado de la VM para el menú.

        Claves:
          - state:          "running" | "paused" | "stopped"
          - is_linked:      True si es clon enlazado
          - linked_enabled: True si se puede desenlazar (clon + apagada)
        """
        out = {"state": "stopped", "is_linked": False, "linked_enabled": False}
        if not vm_dir:
            return out
        try:
            name = os.path.basename(vm_dir)
            out["state"] = self._runtime_state(name)
        except Exception:
            pass
        try:
            data = self._load_vm_config_cached(vm_dir)
            extra = (data.get("extra") or {})
            out["is_linked"] = bool(extra.get("linked_clone"))
            out["linked_enabled"] = out["is_linked"] and out["state"] == "stopped"
        except Exception:
            pass
        return out

    def _on_vm_item_double_clicked(self, item):
        """Doble clic: abre la pestaña Resumen de la VM.

        Un solo clic ya selecciona y abre la VM (on_vm_list_changed →
        open_vm). El doble clic solo añade "vuelve a la pestaña Resumen",
        útil cuando el usuario estaba en Config VM / Snapshots / Medios.
        """
        if item is None:
            return
        try:
            if hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(0)
        except Exception:
            pass

    def _show_vm_context_menu(self, pos):
        """Slot de customContextMenuRequested en self.vm_list.

        `pos` es un QPoint en coordenadas del widget. Se convierte a
        globales para el popup.
        """
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        from PyQt6.QtCore import QPoint

        # Averiguar sobre qué item se ha hecho clic derecho.
        try:
            item = self.vm_list.itemAt(pos)
        except Exception:
            item = None
        if item is None:
            # Clic en zona vacía: no mostramos menú.
            return

        # Seleccionar el item para que el resto de la app coincida con
        # lo que el usuario está viendo en el menú.
        try:
            self.vm_list.setCurrentItem(item)
        except Exception:
            pass

        name = self._vm_name_from_item(item)
        if not name:
            return
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, name)
        if not os.path.isdir(vm_dir):
            return

        info = self._vm_context_menu_state(vm_dir)
        state = info["state"]
        running = state in ("running", "paused")

        menu = QMenu(self.vm_list)

        # --- Cabecera (nombre de la VM, deshabilitada como acción) ---
        head = menu.addAction(name)
        head.setEnabled(False)
        menu.addSeparator()

        # --- Iniciar / Apagar ---
        act_start = menu.addAction(self.tr("▶ Iniciar"))
        act_start.setEnabled(state == "stopped")
        act_start.triggered.connect(self.control_start_vm)

        act_pause = menu.addAction(
            self.tr("▶ Reanudar") if state == "paused" else self.tr("⏸ Pausar")
        )
        act_pause.setEnabled(running)
        act_pause.triggered.connect(
            self.control_resume_vm if state == "paused" else self.control_pause_vm
        )

        act_stop = menu.addAction(self.tr("⏹ Apagar"))
        act_stop.setEnabled(running)
        act_stop.triggered.connect(self.control_poweroff_vm)

        menu.addSeparator()

        # --- Medios / Carpeta / Clonar / Desenlazar ---
        act_media = menu.addAction(self.tr("💿 Medios…"))
        act_media.triggered.connect(
            lambda _checked=False, p=pos:
                self._show_media_menu_at_cursor(
                    pos_global=self.vm_list.mapToGlobal(p)
                )
        )

        act_folder = menu.addAction(self.tr("📂 Abrir carpeta"))
        act_folder.triggered.connect(self.open_vm_folder)

        act_clone = menu.addAction(self.tr("🧬 Clonar"))
        act_clone.triggered.connect(self.clone_current_vm)

        if info["is_linked"]:
            act_unlink = menu.addAction(self.tr("🧬 Desenlazar"))
            act_unlink.setEnabled(info["linked_enabled"])
            act_unlink.triggered.connect(self.unlink_linked_clone)

        menu.addSeparator()

        # --- Metadatos ---
        act_notes = menu.addAction(self.tr("📝 Notas"))
        act_notes.triggered.connect(self.edit_vm_notes)

        act_label = menu.addAction(self.tr("🏷 Etiqueta"))
        act_label.triggered.connect(self.edit_vm_label)

        act_cmp = menu.addAction(self.tr("⚖ Comparar con defaults"))
        act_cmp.triggered.connect(self.compare_config_with_defaults)

        menu.addSeparator()

        # --- Eliminar (destructivo, al final) ---
        act_del = menu.addAction(self.tr("🗑️ Eliminar"))
        act_del.triggered.connect(self.delete_current_vm)

        # Mostrar el menú en la posición global del cursor.
        try:
            menu.exec(self.vm_list.mapToGlobal(pos))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Ver comando QEMU (run_temp.sh)
    # ------------------------------------------------------------------
    # run_temp.sh se regenera en cada arranque. El boton del Resumen
    # abre un dialogo con su contenido y un boton para copiarlo al
    # portapapeles. Muy util para depurar, comparar con la documentacion
    # de QEMU o reportar un problema.

    def show_qemu_command(self):
        """Muestra el contenido de run_temp.sh: el comando exacto con el
        que QEMU esta ejecutando (o ejecuto por ultima vez) esta VM.
        """
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QPlainTextEdit, QApplication,
        )

        if not self._vm_is_selected():
            QMessageBox.information(
                self, self.tr("Comando QEMU"),
                self.tr("Selecciona primero una maquina virtual."),
            )
            return

        vm_name = os.path.basename(self.current_vm_dir)
        run_sh = os.path.join(self.current_vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            QMessageBox.information(
                self, self.tr("Comando QEMU"),
                self.tr("La VM '{0}' todavia no se ha arrancado.\n\n"
                        "El comando QEMU se genera al pulsar Iniciar; vuelve a "
                        "intentarlo despues del primer arranque.").format(vm_name),
            )
            return

        try:
            with open(run_sh, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Comando QEMU"),
                self.tr("No se pudo leer run_temp.sh.\n\n{0}").format(e),
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Comando QEMU - {0}").format(vm_name))
        dlg.resize(920, 560)
        layout = QVBoxLayout(dlg)
        info = QLabel(
            self.tr("Contenido de <code>run_temp.sh</code> para "
                    "<b>{0}</b>.<br>"
                    "Este es el comando exacto con el que QEMU esta ejecutando "
                    "(o ejecuto por ultima vez) la VM.").format(vm_name)
        )
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setPlainText(content)
        edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        try:
            from PyQt6.QtGui import QFont as _QFont
            _mono = _QFont("monospace")
            _mono.setStyleHint(_QFont.StyleHint.TypeWriter)
            edit.setFont(_mono)
        except Exception:
            pass
        layout.addWidget(edit, 1)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton(self.tr("Copiar al portapapeles"))
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(content)
        )
        folder_btn = QPushButton(self.tr("Abrir carpeta de la VM"))
        folder_btn.setToolTip(
            self.tr("Abre la carpeta que contiene run_temp.sh, launch.log y los discos.")
        )
        try:
            folder_btn.clicked.connect(self.open_vm_folder)
        except Exception:
            pass
        close_btn = QPushButton(self.tr("Cerrar"))
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(folder_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    # ------------------------------------------------------------------
    # Notas libres por VM
    # ------------------------------------------------------------------
    # Se guardan en extra["notes"] dentro de vm_config.ini. Aparecen como
    # aviso amarillo debajo del estado en la pestana Resumen. Son solo
    # texto plano; el preview escapa el HTML para evitar inyecciones y
    # trunca a 400 chars.

    def _load_vm_notes(self, vm_dir):
        """Devuelve las notas guardadas para la VM, o '' si no hay."""
        if not vm_dir:
            return ""
        try:
            data = self._load_vm_config_cached(vm_dir)
            return (data.get("extra") or {}).get("notes", "") or ""
        except Exception:
            return ""

    def _save_vm_notes(self, vm_dir, text):
        """Guarda (o borra) las notas de la VM en vm_config.ini.

        Si el texto queda vacio tras strip(), la clave 'notes' se elimina
        de extra para no dejar rastro.
        """
        if not vm_dir:
            return
        import json as _json, configparser as _cfg
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        c = _cfg.ConfigParser(interpolation=None)
        c.read(cfg_path, encoding="utf-8")
        if not c.has_section("extra"):
            c.add_section("extra")
        try:
            extra = _json.loads(c["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        text = (text or "").strip()
        if text:
            extra["notes"] = text
        else:
            extra.pop("notes", None)
        c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(vm_dir)

        # vm_config_save_cancel_v1_grupo_b_doc:
        # Este campo forma parte del "Grupo B" y se auto-guarda a
        # proposito: NO pasa por el modelo Guardar/Descartar del
        # "Grupo A" (vm_config_save_cancel_v1_*). Motivos:
        #   1. No tiene widget persistente en la pestana Configuracion
        #      VM (este ajuste vive en su propio dialogo o su propio
        #      panel).
        #   2. El usuario espera que un cambio aqui se aplique ya, sin
        #      un paso extra de "Guardar configuracion".
        #   3. Coherente con guest_agent_enabled y clipboard_mode, que
        #      estan en el mismo caso.
        # Si en el futuro se quisiera integrar en el modelo dirty,
        # habria que:
        #   - Darle un widget persistente en la pestana Configuracion VM,
        #   - Anadirlo a _collect_config_from_ui() y _load_config_comparable(),
        #   - Engancharlo a _wire_config_dirty_signals(),
        #   - Anadirlo a la lista de claves comparadas en _has_pending_changes().
    def edit_vm_notes(self):
        """Abre el dialogo para editar las notas de la VM seleccionada."""
        if not self._vm_is_selected():
            QMessageBox.information(
                self, self.tr("Notas de la VM"),
                self.tr("Selecciona primero una maquina virtual."),
            )
            return
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel as _QLabel,
            QPlainTextEdit, QPushButton as _QPushButton,
        )

        vm_name = os.path.basename(self.current_vm_dir)
        current = self._load_vm_notes(self.current_vm_dir)

        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Notas - {0}").format(vm_name))
        dlg.resize(640, 440)
        layout = QVBoxLayout(dlg)

        info = _QLabel(
            self.tr("Notas libres sobre <b>{0}</b>. Se guardan en "
                    "<code>vm_config.ini</code> como <code>extra.notes</code> "
                    "y aparecen como aviso amarillo en la pestana Resumen.").format(vm_name)
        )
        info.setTextFormat(_Qt.TextFormat.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        edit = QPlainTextEdit()
        edit.setPlainText(current)
        edit.setPlaceholderText(
            self.tr("Ej.: instalado con VirtIO, probar snapshots tras actualizar "
                    "los drivers; puerto 8080 redirigido al 80 del guest...")
        )
        layout.addWidget(edit, 1)

        btn_row = QHBoxLayout()
        clear_btn = _QPushButton(self.tr("Borrar notas"))
        cancel_btn = _QPushButton(self.tr("Cancelar"))
        save_btn = _QPushButton(self.tr("Guardar"))
        save_btn.setDefault(True)
        clear_btn.clicked.connect(lambda: edit.setPlainText(""))
        cancel_btn.clicked.connect(dlg.reject)

        def _save():
            try:
                self._save_vm_notes(self.current_vm_dir, edit.toPlainText())
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(
                    self, self.tr("Notas"),
                    self.tr("No se pudieron guardar las notas.\n\n{0}").format(e),
                )

        save_btn.clicked.connect(_save)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._update_manager_details()
                self.log_message(f"==> Notas guardadas para '{vm_name}'.")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Orden de la lista de VMs
    # ------------------------------------------------------------------
    # El combo "combo_vm_order" (en virtual_machine.py) elige entre tres
    # modos. La eleccion se guarda en QSettings; aqui solo se aplica.

    _VM_ORDER_MODES = ("name", "state", "last_used")

    def _vm_order_mode(self):
        """Devuelve el modo actual ('name' | 'state' | 'last_used')."""
        combo = getattr(self, "combo_vm_order", None)
        if combo is not None:
            data = combo.currentData()
            if data in self._VM_ORDER_MODES:
                return data
        try:
            from PyQt6.QtCore import QSettings
            saved = QSettings().value("layout/vm_order", "name") or "name"
            if saved in self._VM_ORDER_MODES:
                return saved
        except Exception:
            pass
        return "name"

    def _apply_vm_order(self, names):
        """Devuelve `names` reordenada segun el modo actual.

        Los dos primeros modos son estables y triviales; el modo
        'last_used' usa mtime del vm_config.ini (no guarda nada en la VM,
        porque ya se actualiza cada vez que la VM se configura o se le
        anaden notas).
        """
        mode = self._vm_order_mode()
        names = list(names or [])

        if mode == "name":
            return sorted(names, key=lambda n: n.lower())

        if mode == "state":
            # Running (0) -> paused (1) -> stopped (2). Dentro de cada
            # grupo, alfabetico.
            _rank = {"running": 0, "paused": 1, "stopped": 2}
            def _key(n):
                try:
                    st = self._runtime_state(n)
                except Exception:
                    st = "stopped"
                return (_rank.get(st, 3), n.lower())
            return sorted(names, key=_key)

        if mode == "last_used":
            import os as _os
            def _key(n):
                cfg = _os.path.join(vm_config.BASE_VM_DIR, n, "vm_config.ini")
                try:
                    return -_os.path.getmtime(cfg)
                except OSError:
                    return 0.0
            return sorted(names, key=_key)

        # Modo desconocido: no tocar.
        return names

    def _on_vm_order_changed(self, *_args):
        """Slot del combo de orden: guarda la eleccion y refresca la lista."""
        combo = getattr(self, "combo_vm_order", None)
        if combo is None:
            return
        mode = combo.currentData() or "name"
        try:
            from PyQt6.QtCore import QSettings
            QSettings().setValue("layout/vm_order", mode)
        except Exception:
            pass
        # Refrescar la lista. Preservamos la VM seleccionada.
        current = None
        if self.current_vm_dir:
            try:
                current = os.path.basename(self.current_vm_dir)
            except Exception:
                current = None
        try:
            self.refresh_vm_list(select_name=current)
        except Exception:
            pass


    # ------------------------------------------------------------------
    # Auto-inicio de VMs al abrir la app
    # ------------------------------------------------------------------
    # Cada VM puede llevar extra["autostart_on_launch"] = true. Al
    # arrancar la app, _auto_start_marked_vms() recorre la lista, filtra
    # las marcadas que NO esten ya corriendo y las arranca en cola,
    # separadas por un pequeño retardo entre arranques.

    _AUTOSTART_INITIAL_DELAY_MS = 1500   # tras el 2 s que pone la UI
    _AUTOSTART_BETWEEN_DELAY_MS = 4000   # entre una VM y la siguiente

    def _on_autostart_changed(self, checked):
        """Slot del checkbox: marca cambios pendientes.

        vm_config_save_cancel_v1_dirty: ya NO guarda directamente.
        El autoguardado de este flag se retira: ahora se guarda
        solo al pulsar "💾 Guardar configuración".

        Si no hay VM seleccionada, no hace nada. Solo se aplica al
        vm_config.ini de la VM actual.
        """
        if not self.current_vm_dir:
            return
        # vm_config_save_cancel_v1_dirty_2b1: ya NO guarda directamente.
        # El checkbox forma parte del Grupo A; se persiste al pulsar
        # "💾 Guardar configuración".
        try:
            self._on_config_dirty()
            self.log_message(
                "==> Auto-inicio "
                + ("marcado para ACTIVAR al guardar." if checked
                   else "marcado para desactivar al guardar.")
            )
        except Exception as e:
            try:
                self.log_message(f"[AVISO] Auto-inicio: {e}")
            except Exception:
                pass

    def _auto_start_marked_vms(self):
        """Arranca en cola las VMs marcadas para auto-inicio.

        Se programa desde _apply_initial_state (2 s tras crear la
        ventana). Reutiliza open_vm + start_installation, así el camino
        es idéntico al del botón Iniciar.
        """
        try:
            from PyQt6.QtCore import QTimer
        except Exception:
            return

        try:
            vms = list_existing_vms()
        except Exception:
            return

        pending = []
        for name in vms:
            try:
                vm_dir = os.path.join(vm_config.BASE_VM_DIR, name)
                data = self._load_vm_config_cached(vm_dir)
                if not (data.get("extra") or {}).get("autostart_on_launch"):
                    continue
                if self._runtime_state(name) in ("running", "paused"):
                    continue
                pending.append(name)
            except Exception:
                continue

        if not pending:
            return

        self.log_message(
            f"==> Auto-inicio: {len(pending)} VM(s) marcadas para arrancar."
        )

        # linked_clone_behavior_fix_v1: silenciar el aviso de clon
        # enlazado con original corriendo durante el auto-arranque.
        self._auto_starting = True

        state = {"idx": 0, "total": len(pending), "queue": pending}

        def _next():
            if state["idx"] >= state["total"]:
                self.log_message("==> Auto-inicio: cola terminada.")
                self._auto_starting = False
                return
            name = state["queue"][state["idx"]]
            state["idx"] += 1

            # Re-verificar por si el usuario la arrancó a mano mientras
            # corría el temporizador.
            try:
                if self._runtime_state(name) in ("running", "paused"):
                    self.log_message(
                        f"==> Auto-inicio: '{name}' ya está corriendo, se salta."
                    )
                    QTimer.singleShot(200, _next)
                    return
            except Exception:
                pass

            self.log_message(
                f"==> Auto-inicio: arrancando '{name}' "
                f"({state['idx']}/{state['total']})."
            )
            try:
                self.open_vm(name)
            except Exception as e:
                self.log_message(
                    f"[AVISO] Auto-inicio: no se pudo abrir '{name}': {e}"
                )
                QTimer.singleShot(200, _next)
                return
            try:
                self.start_installation()
            except Exception as e:
                self.log_message(
                    f"[AVISO] Auto-inicio: no se pudo arrancar '{name}': {e}"
                )
            QTimer.singleShot(self._AUTOSTART_BETWEEN_DELAY_MS, _next)

        # Pequeña espera antes de la primera, por si la UI aún estaba
        # asentándose. Después de esto, se encadena con 4 s entre VMs.
        QTimer.singleShot(self._AUTOSTART_INITIAL_DELAY_MS, _next)


    def _update_manager_details(self):
        """Actualiza el panel principal de detalles sin ejecutar diagnósticos pesados."""
        # Aviso de notas: por defecto oculto. Se muestra mas abajo si la
        # VM seleccionada tiene notas guardadas en extra["notes"].
        if hasattr(self, "manager_vm_notes"):
            self.manager_vm_notes.setVisible(False)
        try:
            name = os.path.basename(self.current_vm_dir) if self.current_vm_dir else self.input_vm_name.text().strip()
            if not name:
                self.manager_vm_title.setText(self.tr("Nueva máquina virtual"))
                self.manager_vm_state.setText(self.tr("● Nueva VM"))
                self.manager_details_label.setText(self.tr(
                    "No hay una máquina virtual seleccionada.\n\n"
                    "Pulsa 'Nueva máquina virtual' para comenzar."))
                self.manager_quick_hint.setText(self.tr(
                    "Configura el sistema en la pestaña 'Configuración'."))
                return
            state = self._runtime_state(name) if self.current_vm_dir else "stopped"
            state_map = {
                "running": (self.tr("● Ejecutándose"), "#2e7d32"),
                "paused": (self.tr("● Pausada"), "#f57c00"),
                "stopped": (self.tr("● Apagada"), "#757575"),
            }
            state_text, state_color = state_map.get(
                state, (self.tr("● Nueva VM"), "#757575"))
            self.manager_vm_title.setText(name)
            self.manager_vm_state.setText(state_text)
            self.manager_vm_state.setStyleSheet(f"font-weight:bold; color:{state_color};")
            if self.current_vm_dir:
                data = self._load_vm_config_cached(self.current_vm_dir)
                # Aviso de notas de la VM (si tiene).
                if hasattr(self, "manager_vm_notes"):
                    _notes = (data.get("extra") or {}).get("notes", "") or ""
                    if _notes.strip():
                        import html as _html
                        _preview = _notes.strip()
                        if len(_preview) > 400:
                            _preview = _preview[:400].rstrip() + "\u2026"
                        _safe = _html.escape(_preview).replace("\n", "<br>")
                        self.manager_vm_notes.setText(
                            "<b>\U0001f4dd " + self.tr("Notas:") + "</b><br>" + _safe
                        )
                        self.manager_vm_notes.setVisible(True)
                os_type = data.get("os_type", "")
                system = "macOS" if os_type == "macos" else (data.get("extra", {}).get("win_ver", "Windows") if os_type == "windows" else data.get("extra", {}).get("distro", "Linux"))
                firmware = data.get("firmware", "bios").upper()
                sb = self.tr("Sí") if data.get("secure_boot") else self.tr("No")
                tpm = self.tr("Sí") if data.get("tpm") else self.tr("No")
                gpu = data.get("graphics_mode", "auto")
                audio = data.get("audio_device", "intel-hda")
                # En Detalles, red/almacenamiento/arranque son solo información.
                net_devices = data.get("network_devices") or []
                if not isinstance(net_devices, list):
                    net_devices = []
                if not net_devices:
                    net_devices = [{
                        "name": self.tr("Red 1"),
                        "model": data.get("network_model", "virtio-net-pci"),
                        "mode": data.get("network_mode", "nat"),
                        "interface": data.get("network_interface", ""),
                        "mac": "",
                    }]
                net_lines = []
                for nd in net_devices:
                    mode = {"nat": "NAT", "bridge": "Bridge", "tap": "TAP"}.get(nd.get("mode"), nd.get("mode", "NAT"))
                    line = f"{nd.get('name', 'Red')} — {nd.get('model', 'virtio-net-pci')} — {mode}"
                    if nd.get("interface"):
                        line += f" [{nd.get('interface')}]"
                    net_lines.append(line)
                net_info = "<br>".join(net_lines) if net_lines else self.tr("Sin adaptadores configurados")

                storage_lines = []
                for s_name, s_type, s_path in self._storage_entries_with_types(self.current_vm_dir):
                    # Etiqueta neutra: SATA y NVMe se muestran como
                    # "Disco Duro" (el bus real lo decide workers).
                    icon = {"sata": "💽", "nvme": "💽", "floppy": "💾"}.get(s_type, "💽")
                    label = {"sata": self.tr("Disco Duro"),
                             "nvme": self.tr("Disco Duro")}.get(
                        s_type, s_type.upper())
                    storage_lines.append(f"{icon} {label} — {s_name}")
                cd_devices = [d for d in self._storage_devices_all(self.current_vm_dir) if d.get("device") == "cdrom"]
                for cd in cd_devices:
                    cd_path = cd.get("path", "")
                    storage_lines.append(
                        "📀 " + self.tr("CD/DVD") + " — "
                        + cd.get('name', self.tr('CD/DVD')) + " — "
                        + (os.path.basename(cd_path) if cd_path
                           else self.tr('vacío')))
                storage_info = "<br>".join(storage_lines) if storage_lines else self.tr("Sin dispositivos")
                boot_info = " → ".join(self._boot_token_label(tok) for tok in self._current_boot_order_tokens())

                self.manager_details_label.setText(
                    f"<b>{self.tr('Sistema:')}</b> {system}<br>"
                    f"<b>{self.tr('CPU:')}</b> {data.get('cores', '-')} {self.tr('núcleos')} &nbsp;&nbsp; <b>{self.tr('RAM:')}</b> {data.get('ram', '-')}<br>"
                    f"<b>{self.tr('Firmware:')}</b> {firmware} &nbsp;&nbsp; <b>{self.tr('Secure Boot:')}</b> {sb} &nbsp;&nbsp; <b>{self.tr('TPM:')}</b> {tpm}<br>"
                    f"<b>{self.tr('Gráficos:')}</b> {gpu}<br>"
                    f"<b>{self.tr('Audio:')}</b> {audio}<br>"
                    f"<b>{self.tr('Red:')}</b><br>{net_info}<br>"
                    f"<b>{self.tr('Almacenamiento:')}</b><br>{storage_info}<br>"
                    f"<b>{self.tr('Orden de arranque:')}</b> {boot_info}<br>"
                    f"<b>{self.tr('Ubicación:')}</b> {self.current_vm_dir}"
                )
                self.manager_quick_hint.setText(self.tr(
                    "Usa 'Configuración' para modificar hardware y opciones avanzadas."))
            else:
                self.manager_details_label.setText(self.tr(
                    "VM nueva: todavía no se ha guardado una configuración."))
                self.manager_quick_hint.setText(self.tr(
                    "Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio."))
            # Actualizar visibilidad del botón "🧬 Desenlazar" según
            # si la VM actual es un clon enlazado (linked_clone_v1).
            try:
                _st = self._runtime_state(os.path.basename(self.current_vm_dir)) if self.current_vm_dir else "stopped"
                if hasattr(self, "_update_linked_clone_buttons_state"):
                    self._update_linked_clone_buttons_state(_st)
            except Exception:
                pass
        except Exception as e:
            if hasattr(self, "manager_details_label"):
                self.manager_details_label.setText(f"No se pudo cargar el resumen: {e}")

    def _update_vm_summary(self):
        """Compatibilidad con señales antiguas: el resumen vive ahora en Detalles."""
        return

    def _set_vm_status(self, state="new"):
        styles = {
            "new": (self.tr("● Nueva VM"), "#757575"),
            "saved": (self.tr("● Configurada"), "#1565c0"),
            "running": (self.tr("● Ejecutándose"), "#2e7d32"),
            "error": (self.tr("● Error"), "#c62828"),
        }
        text, color = styles.get(state, styles["new"])
        self.vm_status_label.setText(text)
        self.vm_status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 2px 6px;")

    def open_vm_folder(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Carpeta"), self.tr("Primero selecciona una máquina virtual existente."))
            return
        folder = os.path.abspath(self.current_vm_dir)
        try:
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                QMessageBox.information(self, self.tr("Carpeta de la VM"), folder)
        except Exception as e:
            QMessageBox.warning(self, self.tr("Carpeta"), self.tr("No se pudo abrir la carpeta.\n\n{0}\n\n{1}").format(folder, e))

    def show_vm_summary(self):
        if not self.input_vm_name.text().strip():
            QMessageBox.information(self, self.tr("Resumen"), self.tr("No hay una máquina virtual seleccionada todavía."))
            return
        QMessageBox.information(self, self.tr("Resumen de la máquina virtual"), self._build_vm_summary_text())

    def _build_vm_summary_text(self):
        os_type = self.combo_main_os.currentData()
        if os_type == "macos":
            sistema = self.combo_macos_ver.currentText()
        elif os_type == "windows":
            sistema = self.combo_win_ver.currentText()
        elif os_type == "android":
            _iso = ""
            if hasattr(self, "input_android_iso"):
                _iso = os.path.basename(self.input_android_iso.text().strip())
            sistema = "Android" + (f" ({_iso})" if _iso else "")
        else:
            sistema = self.combo_lin_distro.currentText()
            _ver = self._selected_lin_version() if hasattr(self, "_selected_lin_version") else ""
            if _ver:
                sistema = f"{sistema} {_ver}"
        return (
            f"Nombre: {self.input_vm_name.text().strip()}\n"
            f"Sistema: {sistema}\n"
            f"CPU: {self.slider_cores.value()} núcleos / {self.combo_cpu_model.currentText() if hasattr(self, 'combo_cpu_model') else 'Automático'}\n"
            f"RAM: {self.slider_ram.value()} GB\n"
            f"Firmware: {self.combo_firmware.currentText()}\n"
            f"Secure Boot: {'Sí' if self.check_secure_boot.isChecked() else 'No'}\n"
            f"TPM 2.0: {'Sí' if self.check_tpm.isChecked() else 'No'}\n"
            f"GPU: {self.combo_graphics.currentText()} / {self.combo_graphics_vram.currentData()}\n"
            f"Redes: {len(self._network_devices()) if hasattr(self, 'network_devices_list') else 1} adaptador(es)\n"
            f"Audio: {self.combo_audio.currentText()}"
        )

    # ==================================================================
    # Importar / Exportar VM
    # ==================================================================
    # Archivos de runtime que NO se exportan: son específicos de la sesión
    # en la que se creó la VM. Si se copian tal cual, la VM importada
    # arrastraría pids/sockets muertos que confunden a QEMU o a la propia
    # aplicación. run_temp.sh se regenera en cada arranque. launch.log se
    # omite porque puede crecer sin control y no es necesario para que la
    # VM funcione.
    _VM_EXPORT_EXCLUDED_NAMES = (
        "qemu.pid", "qemu.qmp", "qemu.vnc.sock", "qga.sock", "swtpm.sock",
        "run_temp.sh", "launch.log",
    )
    _VM_EXPORT_EXCLUDED_SUFFIXES = (".sock", ".pid", ".qmp")
    _VM_EXPORT_EXCLUDED_DIRS = ("__pycache__",)

    @classmethod
    def _is_export_excluded(cls, path):
        """True si el path (archivo o carpeta) debe omitirse al exportar."""
        name = os.path.basename(path)
        if name in cls._VM_EXPORT_EXCLUDED_NAMES:
            return True
        if any(name.endswith(s) for s in cls._VM_EXPORT_EXCLUDED_SUFFIXES):
            return True
        if name in cls._VM_EXPORT_EXCLUDED_DIRS:
            return True
        return False

    def _walk_vm_files(self, vm_dir):
        """Devuelve lista de (abs_path, rel_path, size) omitiendo excluidos."""
        out = []
        vm_dir = os.path.abspath(vm_dir)
        for root, dirs, files in os.walk(vm_dir):
            # Filtrar directorios in-place para que os.walk no entre.
            dirs[:] = [d for d in dirs if not self._is_export_excluded(os.path.join(root, d))]
            for f in files:
                ab = os.path.join(root, f)
                if self._is_export_excluded(ab):
                    continue
                try:
                    sz = os.path.getsize(ab)
                except OSError:
                    sz = 0
                rel = os.path.relpath(ab, vm_dir)
                out.append((ab, rel, sz))
        return out

    def export_vm(self):
        """Exporta la VM seleccionada. Ver cabecera del módulo."""
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Exportar VM"), self.tr("Primero selecciona una máquina virtual."))
            return

        vm_name = os.path.basename(self.current_vm_dir)
        state = self._runtime_state(vm_name)
        if state != "stopped":
            resp = QMessageBox.warning(
                self, self.tr("Exportar VM"),
                self.tr("La VM '{0}' está {1}.\n\n"
                        "Se recomienda apagarla antes de exportar: si está corriendo, "
                        "los discos pueden estar en un estado inconsistente (cambios "
                        "sin sincronizar a disco, locks activos…).\n\n"
                        "¿Continuar de todos modos?").format(vm_name, state),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        # Formato.
        formats = [
            (self.tr("Copia de carpeta (más rápido, editable)"), "folder"),
            (self.tr("Archivo .tar.gz (comprimido, portable)"), "tar.gz"),
            (self.tr("Archivo .zip (compatible con Windows)"), "zip"),
            (self.tr("Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)"), "ova"),
            (self.tr("Descriptor .ovf + discos sueltos (carpeta)"), "ovf"),
        ]
        labels = [f[0] for f in formats]
        item, ok_choice = QInputDialog.getItem(
            self, self.tr("Exportar VM"),
            self.tr("Formato para exportar '{0}':").format(vm_name),
            labels, 0, False,
        )
        if not ok_choice:
            return
        fmt = dict(zip(labels, [f[1] for f in formats]))[item]

        # ovf_ova_io_v1: los formatos OVF/OVA usan un flujo especifico
        # (descriptor XML + conversion opcional a VMDK). Se despachan
        # a su propio metodo antes de seguir con la rama normal.
        if fmt in ("ova", "ovf"):
            return self._export_vm_as_ova(fmt, vm_name)

        # Calcular tamaño aproximado (para el warning en el diálogo).
        try:
            files = self._walk_vm_files(self.current_vm_dir)
            total_bytes = sum(sz for _, _, sz in files)
            total_txt = self._format_bytes_iexport(total_bytes)
            file_count = len(files)
        except Exception:
            total_bytes = 0
            total_txt = "?"
            file_count = 0

        # Destino.
        if fmt == "folder":
            dest_parent = QFileDialog.getExistingDirectory(
                self, self.tr("Elige la carpeta donde crear la copia"),
                os.path.expanduser("~"),
            )
            if not dest_parent:
                return
            dest_path = os.path.join(dest_parent, vm_name)
            if os.path.exists(dest_path):
                resp = QMessageBox.question(
                    self, self.tr("Ya existe"),
                    self.tr("En la carpeta destino ya existe '{0}'.\n\n"
                            "¿Sobrescribir? (se borrará la carpeta destino existente)").format(vm_name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return
        else:
            ext = ".tar.gz" if fmt == "tar.gz" else ".zip"
            suggested = os.path.join(os.path.expanduser("~"), f"{vm_name}{ext}")
            dest_path, _ = QFileDialog.getSaveFileName(
                self, self.tr("Guardar archivo de exportación"),
                suggested,
                self.tr("Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)") if fmt == "tar.gz"
                else self.tr("Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)"),
            )
            if not dest_path:
                return
            if not dest_path.endswith(ext):
                dest_path += ext
            if os.path.exists(dest_path):
                resp = QMessageBox.question(
                    self, self.tr("Ya existe"),
                    self.tr("El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?").format(dest_path),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return

        # Confirmación final con resumen.
        confirm = QMessageBox.question(
            self, self.tr("Confirmar exportación"),
            self.tr("Exportar '{0}' como:\n\n"
                    "  • Formato: {1}\n"
                    "  • Contenido: {2} archivo(s), {3}\n"
                    "  • Destino: {4}\n\n"
                    "Los archivos de bloqueo (pids, sockets) y logs se omitirán.").format(vm_name, item, file_count, total_txt, dest_path),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        vm_dir = self.current_vm_dir
        fmt_key = fmt

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit(f"==> Iniciando exportación de '{vm_name}' → {dest_path}")
            return self._export_vm_impl(
                vm_dir, vm_name, fmt_key, dest_path,
                log_emit, is_cancelled, progress_emit,
            )

        self.run_async(
            _work,
            f"Exportando VM '{vm_name}'",
            on_success=lambda result: self._on_export_success(result, vm_name),
            on_error=lambda e: self._show_selectable_error(
                self.tr("Exportar VM"), self.tr("No se pudo completar la exportación.\n\n{0}").format(e)
            ),
            cancelable=True,
            show_log=True,
            subtitle=self.tr("{0} archivo(s), {1} en total").format(file_count, total_txt),
        )

    def _export_vm_impl(self, vm_dir, vm_name, fmt, dest_path,
                        log_emit, is_cancelled, progress_emit):
        """Cuerpo de la exportación. Corre en hilo de fondo.

        El progreso se reporta con percent=-1 (barra indeterminada, animación
        continua) para que el usuario sepa que la operación sigue viva aunque
        cada archivo tarde lo suyo. El texto de estado muestra el número
        de archivo actual y su nombre:

            [N/M] nombre_del_archivo
        """
        import shutil as _sh
        import tarfile as _tar
        import zipfile as _zip

        log_emit(f"==> Exportando '{vm_name}' como {fmt} → {dest_path}")

        files = self._walk_vm_files(vm_dir)
        total_files = len(files)
        total_bytes = sum(sz for _, _, sz in files) or 1
        total_txt = self._format_bytes_iexport(total_bytes)

        log_emit(
            f"==> {total_files} archivo(s) a procesar, {total_txt} en total."
        )

        # Nombre amigable para el log según el modo.
        _verb = {"folder": "Copiando", "tar.gz": "Comprimiendo", "zip": "Comprimiendo"}.get(fmt, "Procesando")

        # Índice del archivo actual (1-based para mostrar).
        state = {"idx": 0}

        def _tick(rel, size):
            """Avanza el contador y emite progreso indeterminado con info."""
            state["idx"] += 1
            i = state["idx"]
            # Texto compacto: "[12/47] BaseSystem.img" — truncamos el nombre
            # si es muy largo para que la barra no se estire.
            name = rel if len(rel) <= 60 else ("…" + rel[-57:])
            progress_emit(-1, f"[{i}/{total_files}] {name}")

        if fmt == "folder":
            # Copia recursiva preservando permisos y sin seguir symlinks.
            if os.path.exists(dest_path):
                _sh.rmtree(dest_path)
            os.makedirs(dest_path, exist_ok=True)
            for ab, rel, sz in files:
                if is_cancelled():
                    raise RuntimeError(self.tr("Exportación cancelada por el usuario."))
                _tick(rel, sz)
                dest_file = os.path.join(dest_path, rel)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                _sh.copy2(ab, dest_file, follow_symlinks=False)

        elif fmt == "tar.gz":
            if os.path.exists(dest_path):
                os.remove(dest_path)
            with _tar.open(dest_path, "w:gz", dereference=False) as tar:
                for ab, rel, sz in files:
                    if is_cancelled():
                        raise RuntimeError(self.tr("Exportación cancelada por el usuario."))
                    _tick(rel, sz)
                    arcname = os.path.join(vm_name, rel)
                    tar.add(ab, arcname=arcname, recursive=False)

        elif fmt == "zip":
            if os.path.exists(dest_path):
                os.remove(dest_path)
            with _zip.ZipFile(dest_path, "w", _zip.ZIP_DEFLATED) as zf:
                for ab, rel, sz in files:
                    if is_cancelled():
                        raise RuntimeError(self.tr("Exportación cancelada por el usuario."))
                    _tick(rel, sz)
                    arcname = os.path.join(vm_name, rel)
                    zf.write(ab, arcname=arcname)
        else:
            raise RuntimeError(self.tr("Formato de exportación desconocido: {0}").format(fmt))

        # Al terminar: barra determinada a 100%.
        progress_emit(100, self.tr("Exportación completada ({0} archivo(s)).").format(total_files))

        # Tamaño final del resultado.
        try:
            if os.path.isfile(dest_path):
                size_out = os.path.getsize(dest_path)
            else:
                size_out = sum(
                    os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(dest_path) for f in fs
                )
        except Exception:
            size_out = 0

        log_emit(
            f"==> Exportación terminada: {total_files} archivo(s), "
            f"{self._format_bytes_iexport(size_out)} en el destino."
        )
        return dest_path


    def _on_export_ova_success(self, dest_path, vm_name, t_start,
                                destino, to_vmdk, include_iso,
                                is_macos=False):
        """ovf_export_summary_v1: dialogo final con resumen de la
        exportacion OVF/OVA (duracion, destino, formato, tamano).

        ovf_export_summary_v1_safe: el cuerpo va envuelto en try/except
        para que cualquier fallo al construir el resumen no deje al
        usuario sin feedback: se loguea el traceback y se muestra un
        dialogo minimo de exito.
        """
        import traceback as _tb
        try:
            self._show_export_ova_summary(
                dest_path, vm_name, t_start,
                destino, to_vmdk, include_iso, is_macos,
            )
        except Exception as _e:
            _trace = _tb.format_exc()
            try:
                self.log_message(
                    f"[ERROR] _on_export_ova_success: {_e}"
                )
                for _ln in _trace.splitlines():
                    self.log_message("    " + _ln)
            except Exception:
                pass
            try:
                _msg = (
                    f"'{vm_name}' exportada correctamente.\n\n"
                    f"Archivo: {dest_path}\n\n"
                    f"(No se pudo construir el resumen detallado: {_e})"
                )
                QMessageBox.information(
                    self, self.tr("Exportar OVF/OVA"), _msg
                )
            except Exception:
                pass

    def _show_export_ova_summary(self, dest_path, vm_name, t_start,
                                  destino, to_vmdk, include_iso,
                                  is_macos=False):
        """ovf_export_summary_v1: construye y muestra el resumen."""
        import time as _tm
        try:
            duration = max(0.0, _tm.monotonic() - t_start)
        except Exception:
            duration = 0.0

        if duration < 60:
            dur_txt = f"{duration:.0f} s"
        else:
            _m = int(duration // 60)
            _s = int(duration - _m * 60)
            dur_txt = f"{_m} min {_s} s"

        size_txt = "-"
        try:
            if os.path.isfile(dest_path):
                size_txt = self._format_bytes_iexport(
                    os.path.getsize(dest_path)
                )
            else:
                _d = os.path.dirname(dest_path)
                _total = 0
                for _f in os.listdir(_d):
                    try:
                        _total += os.path.getsize(os.path.join(_d, _f))
                    except OSError:
                        pass
                if _total > 0:
                    size_txt = self._format_bytes_iexport(_total)
        except Exception:
            pass

        _dest_map = {
            "vmware": "VMware Workstation / ESXi",
            "virtualbox": "VirtualBox",
            "virtmachine": "Virtual.Machine (QEMU/KVM)",
        }
        dest_txt = _dest_map.get(destino, str(destino))

        if to_vmdk:
            fmt_txt = "VMDK stream-optimized"
        else:
            fmt_txt = "QCOW2 aplanado + comprimido (zlib)"

        iso_txt = "incluidas" if include_iso else "no incluidas"

        _notas = []
        if destino == "vmware":
            if is_macos:
                _notas.append(
                    "Notas para VMware: la VM resultante NO arrancara "
                    "macOS. La cadena OpenCore+OSX-KVM no es compatible "
                    "con VMware."
                )
            else:
                _notas.append(
                    "Notas para VMware: si el disco original era GPT+EFI, "
                    "activa UEFI manualmente en la VM tras importarla. "
                    "El flag de firmware no se transmite en el OVF."
                )
        elif destino == "virtualbox":
            _notas.append(
                "Compatible con VirtualBox y con Virtual.Machine."
            )
        else:
            _notas.append(
                "Reimportable en esta app: se conservara grupo, "
                "color, notas y configuracion completa."
            )

        _msg = (
            f"'{vm_name}' exportada correctamente.\n\n"
            f"  Archivo:   {dest_path}\n"
            f"  Tamano:    {size_txt}\n"
            f"  Duracion:  {dur_txt}\n\n"
            f"  Destino:   {dest_txt}\n"
            f"  Disco:     {fmt_txt}\n"
            f"  ISOs:      {iso_txt}\n"
        )
        for _n in _notas:
            _msg += f"\n{_n}"

        QMessageBox.information(self, self.tr("Exportar OVF/OVA"), _msg)


    def _on_export_success(self, dest_path, vm_name):
        QMessageBox.information(
            self, self.tr("Exportar VM"),
            self.tr("'{0}' exportada correctamente.\n\n"
                    "Destino: {1}").format(vm_name, dest_path),
        )

    @staticmethod
    def _format_bytes_iexport(n):
        try:
            n = float(n)
        except (TypeError, ValueError):
            return "—"
        for u in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or u == "TB":
                return f"{n:.1f} {u}" if u != "B" else f"{int(n)} B"
            n /= 1024.0

    def import_vm(self):
        """Importa una VM desde una carpeta o un archivo comprimido."""
        # 1. Elegir carpeta o archivo.
        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Importar VM"))
        box.setText(
            self.tr("¿Cómo quieres importar la máquina virtual?\n\n"
                    "  • Desde carpeta: selecciona una carpeta que contenga "
                    "vm_config.ini.\n"
                    "  • Desde archivo: selecciona un .ova o .ovf (formato estándar "
                    "OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip "
                    "exportado previamente desde otra instalación de Virtual.Machine.")
        )
        btn_folder = box.addButton(self.tr("📁 Desde carpeta…"), QMessageBox.ButtonRole.AcceptRole)
        btn_archive = box.addButton(self.tr("🗜️ Desde archivo…"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(self.tr("Cancelar"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == btn_folder:
            source = QFileDialog.getExistingDirectory(
                self, self.tr("Selecciona la carpeta de la VM a importar"),
                os.path.expanduser("~"),
            )
            if not source:
                return
            is_archive = False
        elif clicked == btn_archive:
            source, _ = QFileDialog.getOpenFileName(
                self, self.tr("Selecciona el archivo a importar"),
                os.path.expanduser("~"),
                self.tr("OVF/OVA (*.ova *.ovf);;"
                        "Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;"
                        "Todos los archivos (*)"),
            )
            if not source:
                return
            is_archive = True
        else:
            return

        # 2. Validación previa rápida para dar feedback temprano.
        if is_archive:
            low = source.lower()
            if not (low.endswith(".tar.gz") or low.endswith(".tgz")
                    or low.endswith(".tar") or low.endswith(".zip")
                    or low.endswith(".ova") or low.endswith(".ovf")):
                QMessageBox.warning(
                    self, self.tr("Importar VM"),
                    self.tr("Formato de archivo no reconocido. Usa .tar.gz, .tgz, "
                            ".tar, .zip, .ova o .ovf."),
                )
                return
            # ovf_ova_io_v1: despachar a la rama OVF/OVA. Tiene su propio
            # flujo con dialogo de previsualizacion y conversion de discos.
            if low.endswith(".ova") or low.endswith(".ovf"):
                return self._import_vm_from_ova(source)
        else:
            cfg = os.path.join(source, "vm_config.ini")
            if not os.path.isfile(cfg):
                QMessageBox.warning(
                    self, self.tr("Importar VM"),
                    self.tr("La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\n"
                            "Asegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.").format(source),
                )
                return

        # 3. Nombre destino.
        if is_archive:
            base = os.path.basename(source)
            for ext in (".tar.gz", ".tgz", ".tar", ".zip"):
                if base.lower().endswith(ext):
                    base = base[: -len(ext)]
                    break
            suggested_name = base or "VM-importada"
        else:
            suggested_name = os.path.basename(os.path.abspath(source))

        # Sanear.
        suggested_name = re.sub(r'[\\/:*?"<>|]', "_", suggested_name).strip() or "VM-importada"

        # Ajustar si ya existe.
        existing = set(list_existing_vms())
        name = suggested_name
        i = 2
        while name in existing or os.path.exists(os.path.join(vm_config.BASE_VM_DIR, name)):
            name = f"{suggested_name}-{i}"
            i += 1

        name, ok_name = QInputDialog.getText(
            self, self.tr("Importar VM"),
            self.tr("Nombre para la VM importada:\n\n"
                    "(se importará desde {0})").format(os.path.basename(source)),
            QLineEdit.EchoMode.Normal,
            name,
        )
        if not ok_name or not name.strip():
            return
        name = re.sub(r'[\\/:*?"<>|]', "_", name.strip())
        if not name:
            QMessageBox.warning(self, self.tr("Importar VM"), self.tr("Nombre inválido."))
            return

        # 4. Confirmar si colisiona.
        target_dir = os.path.join(vm_config.BASE_VM_DIR, name)
        if os.path.exists(target_dir):
            resp = QMessageBox.question(
                self, self.tr("Ya existe"),
                self.tr("Ya existe una VM llamada '{0}'.\n\n"
                        "¿Reemplazarla? (se eliminará la existente)").format(name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        # 5. Ejecutar en segundo plano.
        def _work(log_emit, is_cancelled, progress_emit):
            return self._import_vm_impl(
                source, is_archive, name, target_dir,
                log_emit, is_cancelled, progress_emit,
            )

        self.run_async(
            _work,
            f"Importando VM '{name}'",
            on_success=lambda result: self._on_import_success(result),
            on_error=lambda e: self._show_selectable_error(
                "Importar VM", f"No se pudo completar la importación.\n\n{e}"
            ),
            cancelable=True,
            show_log=True,
            subtitle=self.tr("Copiando/desempaquetando en el sistema de archivos "
                             "del destino (no en /tmp)…"),
        )

    def _import_vm_impl(self, source, is_archive, name, target_dir,
                        log_emit, is_cancelled, progress_emit):
        """Cuerpo de la importación. Corre en hilo de fondo."""
        import shutil as _sh
        import tarfile as _tar
        import zipfile as _zip
        import tempfile as _tmp

        log_emit(f"==> Importando desde: {source}")
        log_emit(f"==> Destino: {target_dir}")

        extracted_root = None

        try:
            # --- 1. Obtener una carpeta fuente con vm_config.ini dentro ---
            if not is_archive:
                src_vm_dir = source
            else:
                progress_emit(0, self.tr("Desempaquetando archivo…"))
                # NO usar /tmp: en la mayoría de sistemas /tmp es un tmpfs
                # pequeño (5-8 GB aquí) que no puede contener una VM completa.
                # Extraemos en el mismo sistema de archivos que el destino para
                # no llenar /tmp y para que el 'move' final sea un rename
                # instantáneo (mismo FS, sin duplicar espacio).
                os.makedirs(vm_config.BASE_VM_DIR, exist_ok=True)
                _parent_fs_dir = os.path.dirname(os.path.abspath(vm_config.BASE_VM_DIR))
                tmp_extract = _tmp.mkdtemp(prefix=".vm_import_", dir=_parent_fs_dir)

                extracted_root = tmp_extract

                low = source.lower()
                if low.endswith(".zip"):
                    with _zip.ZipFile(source, "r") as zf:
                        names = zf.namelist()
                        total = len(names) or 1
                        for i, n in enumerate(names):
                            if is_cancelled():
                                raise RuntimeError("Importación cancelada por el usuario.")
                            zf.extract(n, tmp_extract)
                            if i % 20 == 0:
                                progress_emit(
                                    int(i * 100 / total),
                                    self.tr("Extrayendo {0}/{1}…").format(i+1, total),
                                )
                elif low.endswith(".tar.gz") or low.endswith(".tgz") or low.endswith(".tar"):
                    mode = "r:gz" if (low.endswith(".tar.gz") or low.endswith(".tgz")) else "r:"
                    with _tar.open(source, mode) as tar:
                        members = tar.getmembers()
                        total = len(members) or 1
                        for i, m in enumerate(members):
                            if is_cancelled():
                                raise RuntimeError("Importación cancelada por el usuario.")
                            tar.extract(m, tmp_extract)
                            if i % 20 == 0:
                                progress_emit(
                                    int(i * 100 / total),
                                    self.tr("Extrayendo {0}/{1}…").format(i+1, total),
                                )
                else:
                    raise RuntimeError(f"Formato no soportado: {source}")

                # Localizar la carpeta con vm_config.ini.
                candidates = []
                for root, dirs, files in os.walk(tmp_extract):
                    if "vm_config.ini" in files:
                        candidates.append(root)
                if not candidates:
                    raise RuntimeError(
                        self.tr("El archivo no contiene ninguna VM válida "
                                "(no se encontró vm_config.ini).")
                    )
                # Si hay varias, elegir la más "superficial".
                candidates.sort(key=lambda p: p.count(os.sep))
                src_vm_dir = candidates[0]
                log_emit(f"==> VM localizada en: {src_vm_dir}")

            # --- 2. Validar contenido ---
            cfg_in = os.path.join(src_vm_dir, "vm_config.ini")
            if not os.path.isfile(cfg_in):
                raise RuntimeError("La fuente no contiene vm_config.ini.")

            # --- 3. Preparar destino ---
            if os.path.exists(target_dir):
                log_emit(f"==> Eliminando VM existente '{os.path.basename(target_dir)}'…")
                _sh.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            # --- 4. Copiar archivos (sin excluidos) ---
            files = self._walk_vm_files(src_vm_dir)
            total_bytes = sum(sz for _, _, sz in files) or 1
            done = 0
            for ab, rel, sz in files:
                if is_cancelled():
                    raise RuntimeError("Importación cancelada por el usuario.")
                dest_file = os.path.join(target_dir, rel)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                _sh.copy2(ab, dest_file, follow_symlinks=False)
                done += sz
                if done and (done % (5 * 1024 * 1024) < sz or rel == files[-1][1]):
                    pct = min(99, int(done * 100 / total_bytes))
                    progress_emit(pct, self.tr("Copiando {0}").format(rel))

            # --- 5. Ajustar el nombre interno en vm_config.ini si cambió ---
            try:
                import configparser as _cfg
                c = _cfg.ConfigParser()
                c.read(os.path.join(target_dir, "vm_config.ini"), encoding="utf-8")
                if c.has_section("general"):
                    old = c.get("general", "name", fallback="")
                    if old != name:
                        c.set("general", "name", name)
                        with open(os.path.join(target_dir, "vm_config.ini"),
                                  "w", encoding="utf-8") as f:
                            c.write(f)
                        log_emit(f"==> Nombre interno actualizado: '{old}' → '{name}'.")
            except Exception as e:
                log_emit(f"[AVISO] No se pudo actualizar el nombre interno: {e}")

            progress_emit(100, "Importación completada.")
            log_emit(f"==> Importación terminada: {target_dir}")
            return target_dir

        finally:
            # Limpiar el directorio temporal de extracción, si lo hubo.
            if extracted_root and os.path.isdir(extracted_root):
                try:
                    import shutil as _sh2
                    _sh2.rmtree(extracted_root, ignore_errors=True)
                except Exception:
                    pass

    def _on_import_success(self, target_dir):
        name = os.path.basename(target_dir)
        self.refresh_vm_list(select_name=name)
        try:
            self.open_vm(name)
        except Exception:
            pass
        QMessageBox.information(
            self, self.tr("Importar VM"),
            self.tr("VM '{0}' importada correctamente.\n\n"
                    "Revisa su configuración en la pestaña Configuración antes de "
                    "arrancarla, especialmente si la importaste desde otro host: "
                    "puede referenciar rutas que no existan aquí (carpetas compartidas, "
                    "ISOs externas, dispositivos de passthrough).").format(name),
        )


    # ==================================================================
    # Clonar VM — completo y enlazado (marcador linked_clone_v1)
    # ==================================================================
    # El botón "🧬 Clonar" abre un menú con dos modos:
    #
    #   • Clon completo  → copia recursiva (comportamiento clásico).
    #                      Independiente del original; ocupa el espacio
    #                      completo de los discos.
    #   • Clon enlazado  → disco base compartido vía backing file QCOW2.
    #                      La nueva VM solo guarda deltas. Ocupa muy
    #                      poco pero DEPENDE del original: si se borra
    #                      o se mueve, el clon se rompe.
    #
    # El backing file se guarda con RUTA RELATIVA a la carpeta del clon
    # para que la estructura VirtualMachines/ sea portable: se puede
    # copiar o mover entera a otro host sin romper los clones. El resto
    # de discos secundarios se copian físicamente al clon para no
    # compartir estado escribible. Los CD/DVD mantienen su ruta.

    @staticmethod
    def _new_qemu_mac():
        """MAC con el prefijo estándar QEMU/KVM 52:54:00:..."""
        import uuid as _uuid
        u = _uuid.uuid4().bytes
        return "52:54:00:%02x:%02x:%02x" % (u[0], u[1], u[2])

    def _regenerate_network_macs_and_storage_ids(self, parser):
        """Regenera MACs de red e IDs de storage_devices en un
        ConfigParser ya leído. Reescribe también los tokens del boot_order
        que referencian los IDs antiguos para no dejarlos huérfanos.

        Se llama al crear CUALQUIER clon (completo o enlazado). Corrige
        un bug latente del clon completo antiguo: dos VMs con la misma
        MAC pueden chocar en la LAN slirp / bridge del host.
        """
        import uuid as _uuid
        if parser.has_section("hardware"):
            try:
                nets = json.loads(parser["hardware"].get("network_devices", "[]"))
            except Exception:
                nets = []
            if isinstance(nets, list):
                for n in nets:
                    if isinstance(n, dict):
                        n["mac"] = self._new_qemu_mac()
                parser.set("hardware", "network_devices",
                           json.dumps(nets, ensure_ascii=False))

        if parser.has_section("extra"):
            try:
                extra = json.loads(parser["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            devices = extra.get("storage_devices") or []
            id_map = {}
            if isinstance(devices, list):
                for d in devices:
                    if not isinstance(d, dict):
                        continue
                    old = d.get("id")
                    new = "dev_" + _uuid.uuid4().hex[:12]
                    if old:
                        id_map[old] = new
                    d["id"] = new
            extra["storage_devices"] = devices
            parser.set("extra", "data", json.dumps(extra, ensure_ascii=False))

            if parser.has_section("hardware") and id_map:
                try:
                    order = json.loads(parser["hardware"].get("boot_order", "[]"))
                except Exception:
                    order = []
                new_order = []
                for tok in (order or []):
                    if isinstance(tok, str) and ":" in tok:
                        prefix, ident = tok.split(":", 1)
                        if ident in id_map:
                            new_order.append(f"{prefix}:{id_map[ident]}")
                            continue
                    new_order.append(tok)
                if new_order:
                    parser.set("hardware", "boot_order",
                               json.dumps(new_order))

    def _prompt_clone_name(self, base_name):
        """Pide al usuario un nombre válido para el clon. None si cancela."""
        existing = set(list_existing_vms())
        while True:
            clone_name, ok = QInputDialog.getText(
                self, self.tr("Clonar máquina virtual"),
                self.tr("Nombre para el clon de '{0}':").format(base_name),
                QLineEdit.EchoMode.Normal,
                f"{base_name}-copia",
            )
            if not ok:
                return None
            clone_name = (clone_name or "").strip()
            if not clone_name:
                QMessageBox.warning(self, self.tr("Nombre inválido"),
                                    self.tr("Debes escribir un nombre para el clon."))
                continue
            if (clone_name in existing
                    or os.path.exists(os.path.join(vm_config.BASE_VM_DIR, clone_name))):
                QMessageBox.warning(
                    self, self.tr("Nombre ya existente"),
                    self.tr("La máquina virtual '{0}' ya existe en el listado.\n\n"
                            "Elige otro nombre para el clon.").format(clone_name)
                )
                continue
            if clone_name in ("Nueva Máquina Virtual", ".", ".."):
                QMessageBox.warning(self, self.tr("Nombre inválido"),
                                    self.tr("Ese nombre no puede utilizarse para una máquina virtual."))
                continue
            return clone_name

    def clone_current_vm(self):
        """Punto de entrada del botón "🧬 Clonar".

        Pregunta al usuario qué tipo de clon quiere (completo o enlazado)
        y despacha al método correspondiente."""
        from PyQt6.QtCore import Qt as _Qt
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Clonar VM"),
                                    self.tr("Primero selecciona una máquina virtual existente."))
            return

        source = self.current_vm_dir
        base_name = os.path.basename(source)

        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Clonar máquina virtual"))
        box.setIcon(QMessageBox.Icon.Question)
        box.setTextFormat(_Qt.TextFormat.RichText)
        box.setText(
            self.tr("¿Qué tipo de clon quieres crear a partir de "
                    "<b>{0}</b>?<br><br>"
                    "<b>Clon completo</b><br>"
                    "Copia íntegra de todos los discos. Totalmente independiente "
                    "del original; ocupa el mismo espacio que la VM original.<br><br>"
                    "<b>Clon enlazado</b><br>"
                    "El disco base se comparte mediante un <i>backing file</i> QCOW2. "
                    "La nueva VM solo guarda los cambios, así que ocupa muy poco. "
                    "<b>Depende del original</b>: si se borra o se mueve el original, "
                    "el clon se rompe.<br>"
                    "El backing se guarda con <b>ruta relativa</b> para que puedas "
                    "mover o copiar la carpeta <code>VirtualMachines/</code> entera "
                    "a otro host sin romper nada.<br><br>"
                    "<b>Importante:</b> una vez que el clon arranque por primera vez, "
                    "los cambios que hagas DESPUÉS en el original <b>NO se verán</b> "
                    "en el clon: la vista de su sistema de archivos queda anclada al "
                    "estado del primer arranque (los bloques que el clon ya escribió "
                    "no vuelven a consultarse en el backing). Trata el original como "
                    "de solo lectura mientras el clon exista, o desenlaza el clon con "
                    "<b>🧬 Desenlazar</b> para independizarlo.").format(base_name)
        )
        btn_full = box.addButton(self.tr("Clon completo"), QMessageBox.ButtonRole.AcceptRole)
        btn_linked = box.addButton(self.tr("Clon enlazado"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(self.tr("Cancelar"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(btn_full)
        box.exec()
        clicked = box.clickedButton()
        if clicked is None or clicked not in (btn_full, btn_linked):
            return
        linked = (clicked == btn_linked)

        clone_name = self._prompt_clone_name(base_name)
        if not clone_name:
            return
        destination = os.path.join(vm_config.BASE_VM_DIR, clone_name)

        if linked:
            ok = self._clone_current_vm_linked(source, clone_name, destination)
        else:
            ok = self._clone_current_vm_full(source, clone_name, destination)

        if ok:
            self.refresh_vm_list(select_name=clone_name)
            try:
                self.open_vm(clone_name)
            except Exception:
                pass
            try:
                self._set_vm_status("saved")
            except Exception:
                pass
            try:
                self.log_message(
                    f"==> VM clonada ({'enlazada' if linked else 'completa'}): "
                    f"'{base_name}' → '{clone_name}'"
                )
            except Exception:
                pass

    def _check_linked_clone_original_running(self, vm_dir, data=None):
        """Avisa si abrimos un clon enlazado cuyo original está corriendo.

        Marcador: linked_clone_behavior_fix_v1

        Arrancar original y clon a la vez puede dar resultados
        impredecibles: el clon lee del disco del original los bloques
        que no ha modificado, así que si el original escribe algo
        mientras el clon corre, el clon puede leer estados intermedios
        del sistema de archivos. Se avisa una sola vez por sesión y VM.
        """
        if not vm_dir:
            return
        if data is None:
            try:
                data = self._load_vm_config_cached(vm_dir)
            except Exception:
                return
        extra = (data or {}).get("extra") or {}
        if not extra.get("linked_clone"):
            return
        original_name = str(extra.get("linked_original") or "").strip()
        if not original_name:
            return
        warned = getattr(self, "_linked_clone_warned", None)
        if warned is None:
            warned = set()
            self._linked_clone_warned = warned
        if vm_dir in warned:
            return
        try:
            state = self._runtime_state(original_name)
        except Exception:
            return
        if state not in ("running", "paused"):
            return
        warned.add(vm_dir)
        try:
            self.log_message(
                f"[AVISO] Clon enlazado: el original '{original_name}' está "
                "corriendo. Arrancar los dos a la vez puede dar resultados "
                "impredecibles."
            )
        except Exception:
            pass
        QMessageBox.warning(
            self, self.tr("Clon enlazado con original en ejecución"),
            self.tr("El original de este clon ('{0}') está corriendo.\n\n"
                    "Arrancar original y clon a la vez puede dar resultados "
                    "impredecibles:\n\n"
                    "  • El clon lee del disco del original los bloques que no ha "
                    "modificado. Si el original escribe algo mientras el clon corre, "
                    "el clon puede leer estados intermedios.\n"
                    "  • La vista del sistema de archivos del clon ya está anclada al "
                    "estado de su primer arranque para los bloques de metadatos, así "
                    "que los cambios nuevos del original probablemente no se vean, "
                    "pero el riesgo de lectura inconsistente sigue ahí.\n\n"
                    "Recomendaciones:\n"
                    "  • Apaga el original antes de arrancar el clon (o al revés).\n"
                    "  • O desenlaza el clon con '🧬 Desenlazar' para que sea "
                    "totalmente independiente.\n\n"
                    "Este aviso no volverá a aparecer para esta VM en esta sesión.").format(original_name)
        )

    def _check_linked_clone_backing_intact(self, vm_dir, data=None):
        """Avisa si un clon enlazado apunta a un backing file que ya no
        existe en el host.

        Marcador: linked_clone_broken_detection_v1

        Caso típico: el usuario movió SOLO la carpeta del clon (sin
        llevarse también la del original). La cabecera QCOW2 del clon
        sigue apuntando a un archivo relativo que ya no existe en su
        nueva ubicación. QEMU falla al arrancar con:

            Could not open backing file: No such file or directory

        Se avisa una sola vez por sesión y VM, y se sigue adelante: la VM
        se abre para que el usuario vea la configuración y pueda intentar
        '🧬 Desenlazar' (que puede fallar si el backing ya no está), o
        mover también la VM original.
        """
        if not vm_dir:
            return
        if data is None:
            try:
                data = self._load_vm_config_cached(vm_dir)
            except Exception:
                return
        extra = (data or {}).get("extra") or {}
        if not extra.get("linked_clone"):
            return

        warned = getattr(self, "_linked_clone_broken_warned", None)
        if warned is None:
            warned = set()
            self._linked_clone_broken_warned = warned
        if vm_dir in warned:
            return

        # Determinar el backing esperado. Preferimos extra.linked_backing_rel
        # (lo escribimos al crear el clon). Si no está, leemos la cabecera
        # QCOW2 del disco principal: ahí está la fuente de verdad.
        backing_rel = str(extra.get("linked_backing_rel") or "").strip()
        primary_abs, _ptype = self._primary_disk_path(vm_dir)
        if not backing_rel and primary_abs and os.path.isfile(primary_abs):
            try:
                r = subprocess.run(
                    ["qemu-img", "info", "--output=json", primary_abs],
                    capture_output=True, text=True, timeout=10, check=True,
                )
                backing_rel = str(
                    json.loads(r.stdout).get("backing-filename") or ""
                ).strip()
            except Exception:
                backing_rel = ""

        if not backing_rel:
            # Sin backing declarado, no podemos verificar. No avisamos.
            return

        backing_abs = vm_paths.to_absolute(vm_dir, backing_rel)
        if backing_abs and os.path.isfile(backing_abs):
            return

        warned.add(vm_dir)
        original_name = str(extra.get("linked_original") or "").strip() or "(desconocido)"
        try:
            self.log_message(
                f"[AVISO] Clon enlazado: el backing file del clon "
                f"'{os.path.basename(vm_dir)}' no existe en {backing_abs}. "
                f"QEMU no podrá arrancar esta VM hasta que el original "
                f"('{original_name}') vuelva a estar accesible."
            )
        except Exception:
            pass
        QMessageBox.warning(
            self, self.tr("Clon enlazado con backing roto"),
            self.tr("Este clon enlazado espera el backing en:\n\n"
                    "    {0}\n\n"
                    "Resuelto contra su carpeta queda en:\n\n"
                    "    {1}\n\n"
                    "Ese archivo no existe. La VM original "
                    "('{2}') probablemente se movió o se borró.\n\n"
                    "QEMU fallará al arrancar con:\n"
                    "    Could not open backing file: No such file or directory\n\n"
                    "Opciones:\n"
                    "  • Mueve también la VM original de vuelta a su carpeta, o\n"
                    "  • Copia la carpeta 'VirtualMachines/' entera (con original\n"
                    "    y clon juntos) a la nueva ubicación, o\n"
                    "  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n"
                    "    para independizar este clon (puede fallar si el backing\n"
                    "    ya no está disponible).\n\n"
                    "Este aviso no volverá a aparecer para esta VM en esta sesión.").format(backing_rel, backing_abs, original_name)
        )

    def _clone_current_vm_full(self, source_dir, clone_name, destination):
        """Clon completo: copia recursiva + MACs e IDs nuevos."""
        try:
            shutil.copytree(source_dir, destination)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Clonar VM"),
                                 self.tr("No se pudo copiar la carpeta de la VM.\n\n{0}").format(e))
            return False

        try:
            cfg = os.path.join(destination, "vm_config.ini")
            if os.path.isfile(cfg):
                parser = configparser.ConfigParser(interpolation=None)
                parser.read(cfg, encoding="utf-8")
                if parser.has_section("general"):
                    parser.set("general", "name", clone_name)
                try:
                    self._regenerate_network_macs_and_storage_ids(parser)
                except Exception as _regen_err:
                    try:
                        self.log_message(
                            f"[AVISO] No se pudieron regenerar MACs/IDs del clon: "
                            f"{_regen_err}"
                        )
                    except Exception:
                        pass
                with open(cfg, "w", encoding="utf-8") as f:
                    parser.write(f)
            if hasattr(self, "_invalidate_vm_config_cache"):
                self._invalidate_vm_config_cache(destination)
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Clonar VM"),
                self.tr("La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}").format(e)
            )
            return False

        QMessageBox.information(
            self, self.tr("Clon creado"),
            self.tr("La máquina virtual '{0}' fue clonada correctamente "
                    "(clon completo).\n\n"
                    "Se han regenerado las direcciones MAC y los IDs internos de "
                    "los discos para que no choquen con la VM original.").format(clone_name)
        )
        return True

    def _clone_current_vm_linked(self, source_dir, clone_name, destination):
        """Clon enlazado: disco principal como backing file QCOW2.

        El backing se guarda con RUTA RELATIVA a la carpeta del clon para
        que la estructura VirtualMachines/ sea portable. El resto de
        discos secundarios se COPIAN físicamente al clon. Los CD/DVD
        mantienen su ruta original (son de solo lectura).
        """
        # 1. Localizar el disco principal del original.
        primary_abs, _ptype = self._primary_disk_path(source_dir)
        if not primary_abs or not os.path.isfile(primary_abs):
            QMessageBox.warning(
                self, self.tr("Clon enlazado"),
                self.tr("No se pudo determinar el disco principal de la VM original.\n\n"
                        "El clon enlazado necesita un disco base QCOW2 sobre el que\n"
                        "crear el backing file. Si la VM no tiene discos, usa\n"
                        "'Clon completo'.")
            )
            return False

        # 2. Verificar formato QCOW2.
        try:
            r = subprocess.run(
                ["qemu-img", "info", "--output=json", primary_abs],
                capture_output=True, text=True, timeout=10, check=True,
            )
            info = json.loads(r.stdout)
            fmt = (info.get("format") or "").lower()
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Clon enlazado"),
                self.tr("No se pudo inspeccionar el disco original.\n\n{0}").format(e)
            )
            return False
        if fmt != "qcow2":
            QMessageBox.warning(
                self, self.tr("Clon enlazado"),
                self.tr("El disco principal de la VM original está en formato "
                        "{0}.\n\n"
                        "El clon enlazado solo funciona con QCOW2 (necesita backing\n"
                        "file). Usa 'Clon completo' si quieres copiar el disco tal cual.").format(fmt.upper())
            )
            return False

        # 3. Crear carpeta del clon.
        try:
            os.makedirs(destination, exist_ok=False)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Clon enlazado"),
                self.tr("No se pudo crear la carpeta del clon.\n\n{0}").format(e)
            )
            return False

        # 4. Backing relativo y delta QCOW2.
        backing_rel = os.path.relpath(primary_abs, start=destination)
        clone_disk_name = os.path.basename(primary_abs)
        clone_disk_abs = os.path.join(destination, clone_disk_name)

        try:
            subprocess.run(
                ["qemu-img", "create",
                 "-f", "qcow2",
                 "-b", backing_rel,
                 "-F", "qcow2",
                 clone_disk_name],
                cwd=destination, check=True,
                capture_output=True, text=True, timeout=30,
            )
        except subprocess.CalledProcessError as e:
            try:
                shutil.rmtree(destination)
            except Exception:
                pass
            QMessageBox.critical(
                self, self.tr("Clon enlazado"),
                self.tr("qemu-img create falló.\n\n{0}").format(e.stderr or e)
            )
            return False
        except Exception as e:
            try:
                shutil.rmtree(destination)
            except Exception:
                pass
            QMessageBox.critical(self, self.tr("Clon enlazado"),
                                 self.tr("No se pudo crear el delta QCOW2.\n\n{0}").format(e))
            return False

        # 5. Verificación defensiva: el backing guardado debe ser RELATIVO.
        try:
            r = subprocess.run(
                ["qemu-img", "info", "--output=json", clone_disk_abs],
                capture_output=True, text=True, timeout=10, check=True,
            )
            info = json.loads(r.stdout)
            backing_stored = str(info.get("backing-filename") or "")
            if backing_stored.startswith("/") or backing_stored.startswith("\\\\"):
                try:
                    os.remove(clone_disk_abs)
                    os.rmdir(destination)
                except Exception:
                    pass
                QMessageBox.warning(
                    self, self.tr("Clon enlazado"),
                    self.tr("El backing file quedó guardado como ruta ABSOLUTA, "
                            "lo que haría el clon no portable.\n\n"
                            "Se ha abortado la operación para no dejar un clon "
                            "defectuoso. Reporta esto como bug.")
                )
                return False
        except Exception as _ver_err:
            try:
                self.log_message(
                    f"[AVISO] No se pudo verificar la portabilidad del "
                    f"backing file: {_ver_err}"
                )
            except Exception:
                pass

        # 6. Copiar el resto de archivos EXCLUYENDO el disco principal.
        try:
            files = self._walk_vm_files(source_dir)
            primary_abs_norm = os.path.abspath(primary_abs)
            for ab, rel, sz in files:
                if os.path.abspath(ab) == primary_abs_norm:
                    continue
                dest_file = os.path.join(destination, rel)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(ab, dest_file, follow_symlinks=False)
        except Exception as e:
            try:
                shutil.rmtree(destination)
            except Exception:
                pass
            QMessageBox.critical(
                self, self.tr("Clon enlazado"),
                self.tr("No se pudieron copiar los archivos auxiliares.\n\n{0}").format(e)
            )
            return False

        # 7. Reescribir vm_config.ini del clon.
        try:
            cfg_path = os.path.join(destination, "vm_config.ini")
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(cfg_path, encoding="utf-8")
            if parser.has_section("general"):
                parser.set("general", "name", clone_name)

            self._regenerate_network_macs_and_storage_ids(parser)

            if not parser.has_section("extra"):
                parser.add_section("extra")
            try:
                extra = json.loads(parser["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["linked_clone"] = True
            extra["linked_backing_rel"] = backing_rel
            extra["linked_original"] = os.path.basename(source_dir)

            _devices = extra.get("storage_devices") or []
            primary_abs_norm = os.path.abspath(primary_abs)
            source_dir_abs = os.path.abspath(source_dir)
            for d in _devices:
                if not isinstance(d, dict):
                    continue
                old_path = d.get("path") or ""
                if not old_path:
                    continue
                # portable_paths_v1: los paths guardados en el original
                # pueden ser relativos a source_dir. Resolverlos contra
                # source_dir antes de comparar con primary_abs, y al
                # reescribir en el clon, guardarlos relativos a
                # destination (to_portable) para que el clon siga
                # siendo portable a otro host.
                old_abs = vm_paths.to_absolute(source_dir, old_path)
                if old_abs == primary_abs_norm:
                    d["path"] = vm_paths.to_portable(destination, clone_disk_abs)
                elif old_abs.startswith(source_dir_abs + os.sep):
                    rel_p = os.path.relpath(old_abs, source_dir_abs)
                    new_p = os.path.join(destination, rel_p)
                    if os.path.isfile(new_p):
                        d["path"] = vm_paths.to_portable(destination, new_p)
            extra["storage_devices"] = _devices
            parser.set("extra", "data", json.dumps(extra, ensure_ascii=False))

            with open(cfg_path, "w", encoding="utf-8") as f:
                parser.write(f)
            if hasattr(self, "_invalidate_vm_config_cache"):
                self._invalidate_vm_config_cache(destination)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Clon enlazado"),
                self.tr("El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n"
                        "{0}\n\n"
                        "Revisa manualmente el archivo antes de usar la VM.").format(e)
            )
            return False

        QMessageBox.information(
            self, self.tr("Clon creado"),
            self.tr("La máquina virtual '{0}' fue clonada correctamente "
                    "(clon enlazado).\n\n"
                    "El disco base se comparte con el original mediante un backing\n"
                    "file QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\n"
                    "pero DEPENDE del original:\n\n"
                    "  • Si borras o mueves la VM original, el clon se rompe.\n"
                    "  • Una vez que el clon arranque por primera vez, los cambios\n"
                    "    que hagas DESPUÉS en el original NO se verán en el clon:\n"
                    "    la vista del sistema de archivos queda anclada al estado\n"
                    "    del primer arranque. Trata el original como de solo lectura\n"
                    "    mientras el clon exista.\n"
                    "  • Los snapshots completos (RAM) no funcionarán en este clon\n"
                    "    — solo de disco. QEMU no puede restaurar (loadvm) un\n"
                    "    snapshot completo sobre un QCOW2 con backing file.\n"
                    "  • Los snapshots del clon no son reproducibles mientras el\n"
                    "    original pueda cambiar: al restaurar, se mezcla el delta\n"
                    "    guardado con el estado ACTUAL del backing.\n"
                    "  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n"
                    "    apagado.\n\n"
                    "Para mover o copiar la estructura completa a otro host,\n"
                    "llévate la carpeta 'VirtualMachines/' entera.").format(clone_name)
        )
        return True

    def unlink_linked_clone(self):
        """Convierte un clon enlazado en un QCOW2 autónomo
        (marcador linked_clone_unlink_v1).

        Ejecuta 'qemu-img convert -O qcow2' sobre el disco principal,
        reemplaza el archivo atómicamente y borra los flags linked_*.
        Mismo patrón que compact_vm_disk.
        """
        from PyQt6.QtCore import Qt as _Qt
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Desenlazar clon"),
                                    self.tr("Selecciona primero una máquina virtual."))
            return

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)

        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception:
            data = {}
        extra = data.get("extra") or {}
        if not extra.get("linked_clone"):
            QMessageBox.information(
                self, self.tr("Desenlazar clon"),
                self.tr("Esta VM no es un clon enlazado, no hay nada que desenlazar.")
            )
            return

        state = self._runtime_state(vm_name)
        if state != "stopped":
            QMessageBox.warning(
                self, self.tr("Desenlazar clon"),
                self.tr("La VM '{0}' está encendida.\n\n"
                        "Apágala antes de desenlazarla: con QEMU activo el archivo\n"
                        "está bloqueado y el convert no puede reemplazarlo.").format(vm_name)
            )
            return

        primary_abs, _ptype = self._primary_disk_path(vm_dir)
        if not primary_abs or not os.path.isfile(primary_abs):
            QMessageBox.warning(
                self, self.tr("Desenlazar clon"),
                self.tr("No se encontró el disco principal del clon.")
            )
            return

        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Desenlazar clon"))
        box.setIcon(QMessageBox.Icon.Warning)
        box.setTextFormat(_Qt.TextFormat.RichText)
        box.setText(
            self.tr("Se convertirá el disco principal del clon "
                    "<b>{0}</b> en un QCOW2 "
                    "<b>autónomo</b>.<br><br>"
                    "Después de esto, el clon deja de depender del original y "
                    "puede moverse o copiarse por separado.<br><br>"
                    "<b>Requiere:</b><br>"
                    "&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>"
                    "&nbsp;&nbsp;• La VM apagada (ya lo está).<br>"
                    "&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>"
                    "El resultado se verifica como QCOW2 válido y se reemplaza "
                    "atómicamente. Si algo falla a mitad, el archivo original "
                    "del clon queda intacto.").format(os.path.basename(primary_abs))
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        tmp_path = primary_abs + ".unlinked.qcow2"
        try:
            orig_size = os.path.getsize(primary_abs)
        except OSError:
            orig_size = 0

        def _work(log_emit, is_cancelled, progress_emit):
            import subprocess as _sp
            log_emit(f"==> Desenlazando clon '{vm_name}'…")
            log_emit(f"    Disco:    {primary_abs}")
            log_emit(f"    Temporal: {tmp_path}")

            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            try:
                proc = _sp.Popen(
                    ["qemu-img", "convert", "-p", "-O", "qcow2",
                     primary_abs, tmp_path],
                    stdout=_sp.PIPE, stderr=_sp.STDOUT,
                    text=True, bufsize=1,
                )
            except FileNotFoundError:
                raise RuntimeError("qemu-img no está en el PATH.")

            last_pct = -1
            if proc.stdout is not None:
                for line in iter(proc.stdout.readline, ""):
                    if is_cancelled():
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                        if os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except OSError:
                                pass
                        raise RuntimeError(self.tr("Desenlazado cancelado por el usuario."))
                    if not line:
                        continue
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                    if m:
                        pct = int(float(m.group(1)))
                        if pct != last_pct:
                            last_pct = pct
                            progress_emit(pct, f"Desenlazando… {pct}%")
                    else:
                        progress_emit(-1, "Desenlazando…")

            proc.wait()
            if proc.returncode != 0:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                raise RuntimeError(
                    f"qemu-img convert terminó con código {proc.returncode}."
                )

            try:
                r = _sp.run(
                    ["qemu-img", "info", "--output=json", tmp_path],
                    capture_output=True, text=True, timeout=10, check=True,
                )
                import json as _json
                info = _json.loads(r.stdout)
                if info.get("format") != "qcow2":
                    raise RuntimeError(
                        f"El temporal no es QCOW2 (formato: {info.get('format')})."
                    )
                if info.get("backing-filename"):
                    raise RuntimeError("El resultado sigue teniendo backing file.")
            except Exception as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                raise RuntimeError(f"No se pudo verificar el resultado: {e}")

            try:
                os.replace(tmp_path, primary_abs)
            except OSError as e:
                raise RuntimeError(
                    f"No se pudo reemplazar el disco original: {e}\n"
                    f"El convert quedó en: {tmp_path}"
                )

            try:
                new_size = os.path.getsize(primary_abs)
            except OSError:
                new_size = 0
            log_emit(
                f"==> Desenlazado terminado: {orig_size} → {new_size} bytes."
            )
            return {"orig": orig_size, "new": new_size}

        def _on_success(result):
            try:
                cfg_path = os.path.join(vm_dir, "vm_config.ini")
                parser = configparser.ConfigParser(interpolation=None)
                parser.read(cfg_path, encoding="utf-8")
                if parser.has_section("extra"):
                    extra = json.loads(parser["extra"].get("data", "{}"))
                    extra.pop("linked_clone", None)
                    extra.pop("linked_backing_rel", None)
                    extra.pop("linked_original", None)
                    parser.set("extra", "data", json.dumps(extra, ensure_ascii=False))
                    with open(cfg_path, "w", encoding="utf-8") as f:
                        parser.write(f)
                if hasattr(self, "_invalidate_vm_config_cache"):
                    self._invalidate_vm_config_cache(vm_dir)
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] El disco se desenlazó pero no se pudo "
                        f"limpiar vm_config.ini: {e}"
                    )
                except Exception:
                    pass

            try:
                fmt_o = self._format_bytes_iexport(result["orig"])
                fmt_n = self._format_bytes_iexport(result["new"])
            except Exception:
                fmt_o, fmt_n = str(result["orig"]), str(result["new"])

            QMessageBox.information(
                self, self.tr("Desenlazado"),
                self.tr("El clon '{0}' ya es autónomo.\n\n"
                        "Tamaño antes: {1}\n"
                        "Tamaño después: {2}\n\n"
                        "Puedes mover la VM sin llevarte la original.").format(vm_name, fmt_o, fmt_n)
            )
            try:
                self._update_manager_details()
            except Exception:
                pass
            try:
                if hasattr(self, "refresh_storage_ui"):
                    self.refresh_storage_ui()
            except Exception:
                pass
            try:
                self._update_linked_clone_buttons_state(
                    self._runtime_state(vm_name)
                )
            except Exception:
                pass

        def _on_error(e):
            QMessageBox.critical(
                self, self.tr("Desenlazar clon"),
                self.tr("No se pudo desenlazar el clon.\n\n{0}").format(e)
            )

        self.run_async(
            _work,
            f"Desenlazando '{vm_name}'",
            on_success=_on_success,
            on_error=_on_error,
            cancelable=True,
            show_log=True,
            subtitle=self.tr("Convirtiendo el clon en un QCOW2 autónomo…"),
        )

    def _update_linked_clone_buttons_state(self, state=None):
        """Muestra y habilita el botón '🧬 Desenlazar' solo cuando la VM
        seleccionada es un clon enlazado Y está apagada."""
        btn = getattr(self, "manager_btn_unlink", None)
        if btn is None:
            return
        try:
            is_linked = False
            if self.current_vm_dir:
                data = self._load_vm_config_cached(self.current_vm_dir)
                is_linked = bool((data.get("extra") or {}).get("linked_clone"))
            btn.setVisible(bool(is_linked))
            btn.setEnabled(bool(is_linked) and state == "stopped")
        except Exception:
            try:
                btn.setVisible(False)
                btn.setEnabled(False)
            except Exception:
                pass


    def delete_current_vm(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Eliminar VM"), self.tr("Primero selecciona una máquina virtual existente."))
            return
        vm_dir = os.path.abspath(self.current_vm_dir)
        name = os.path.basename(vm_dir)

        # Los medios adjuntados desde otras ubicaciones nunca se borran.
        external_media = []
        try:
            data = self._load_vm_config_cached(vm_dir)
            for d in (data.get("extra") or {}).get("storage_devices", []):
                # portable_paths_v1: el path guardado puede ser relativo a
                # vm_dir; resolverlo contra vm_dir antes de comparar con
                # commonpath, para no confundir un disco interno con un
                # medio externo (ni al reves).
                _stored = d.get("path", "") or ""
                path = vm_paths.to_absolute(vm_dir, _stored) if _stored else ""
                if path and os.path.exists(path) and os.path.commonpath([vm_dir, path]) != vm_dir:
                    external_media.append(path)
            _cd_stored = (data.get("extra") or {}).get("cdrom_path", "") or ""
            cd_path = vm_paths.to_absolute(vm_dir, _cd_stored) if _cd_stored else ""
            if cd_path and os.path.exists(cd_path) and os.path.commonpath([vm_dir, cd_path]) != vm_dir:
                external_media.append(cd_path)
        except Exception:
            pass

        # Comprobar clones enlazados que dependen de esta VM (linked_clone_v1).
        dependent_clones = []
        try:
            for _other_name in list_existing_vms():
                if _other_name == name:
                    continue
                _other_dir = os.path.join(vm_config.BASE_VM_DIR, _other_name)
                try:
                    _other_data = self._load_vm_config_cached(_other_dir)
                except Exception:
                    continue
                _oe = _other_data.get("extra") or {}
                if (_oe.get("linked_clone")
                        and _oe.get("linked_original") == name):
                    dependent_clones.append(_other_name)
        except Exception:
            pass

        details = self.tr("Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n").format(vm_dir)
        if external_media:
            details += self.tr("Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n") + "\n".join(f"• {p}" for p in sorted(set(external_media))) + "\n\n"
        if dependent_clones:
            details += (
                self.tr("⚠ ESTA VM ES EL ORIGINAL DE {0} "
                        "CLON(ES) ENLAZADO(S):\n").format(len(dependent_clones))
                + "\n".join(f"  • {c}" for c in dependent_clones)
                + self.tr("\n\nSi continúas, esos clones quedarán inutilizables "
                          "(su backing file ya no existirá).\n\n"
                          "Se recomienda desenlazarlos primero: selecciona cada clon "
                          "y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n")
            )
        details += self.tr("¿Deseas continuar?")
        resp = QMessageBox.warning(
            self, self.tr("Eliminar máquina virtual"), details,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            shutil.rmtree(vm_dir)
            self.current_vm_dir = None
            # config_tab_gating_v1: salir del modo creación y
            # reevaluar la habilitación de la pestaña.
            self._new_vm_mode = False
            self.refresh_vm_list()
            self.new_vm()
            self.log_message(f"==> VM eliminada: '{name}'. Los medios externos fueron conservados.")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Eliminar VM"), self.tr("No se pudo eliminar '{0}'.\n\n{1}").format(name, e))

    def change_os_panel(self, index):
        """Cambia la página activa del selector de versión (macOS/Windows/Linux).

        Defensivo: usa stack_pages si existe, version_selector_stack como
        respaldo, y si ninguno existe no falla — simplemente evita tocar
        widgets que aún no se han creado. Esto permite que la app siga
        funcionando aunque la construcción de la UI haya quedado a medias
        por un error previo.
        """
        stack = getattr(self, "stack_pages", None)
        if stack is None:
            stack = getattr(self, "version_selector_stack", None)
        if stack is not None:
            # version_stack_index_v1: mapear por data ("linux",
            # "windows", "macos", "android") en vez de por indice
            # del combo. Al reordenar combo_main_os (Linux primero
            # en macos_eula_order_fix_v1), el indice del combo
            # dejo de coincidir con el indice del stack.
            _os_data = None
            try:
                _os_data = self.combo_main_os.itemData(index)
            except Exception:
                _os_data = None
            _stack_idx = None
            if _os_data is not None:
                _map = getattr(self, "_version_stack_index", None)
                if isinstance(_map, dict):
                    _stack_idx = _map.get(_os_data)
            if _stack_idx is None:
                # Fallback (por si el mapeo no existe todavia):
                # usar el indice del combo tal cual, como antes.
                _stack_idx = index
            try:
                stack.setCurrentIndex(int(_stack_idx))
            except Exception:
                pass
        # Aplicar defaults del perfil del SO solo si los widgets necesarios
        # ya existen.
        try:
            self.apply_os_profile_defaults()
        except Exception as e:
            import sys as _sys
            print(f"[AVISO] apply_os_profile_defaults: {e}", file=_sys.stderr)
        try:
            self.update_firmware_options_visibility()
        except Exception:
            pass
        # Re-aplicar la UI del modo compatibilidad de snapshots: si el
        # SO es macOS, el checkbox queda deshabilitado con tooltip.
        try:
            self._refresh_snapshot_compat_ui_on_os_change()
        except Exception:
            pass


    def apply_os_profile_defaults(self, *args):
        os_type = self.combo_main_os.currentData()
        if os_type == "macos":
            version_name = self.combo_macos_ver.currentText()
        elif os_type == "windows":
            version_name = self.combo_win_ver.currentText()
        elif os_type == "android":
            # Android no tiene combo de versión: la versión de Android
            # la decide la ISO que el usuario aporta. Usamos la ruta
            # para que el label del perfil sea informativo.
            version_name = "Android-x86 / Bliss OS"
        else:
            version_name = self.combo_lin_distro.currentText()
        profile = get_os_profile(os_type, version_name, version_name if os_type == "linux" else "")

        def set_combo(combo, value):
            idx = combo.findData(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        set_combo(self.combo_chipset, profile.get("chipset", "q35"))
        set_combo(self.combo_firmware, profile.get("firmware", "uefi"))
        if hasattr(self, "combo_cpu_model"):
            set_combo(self.combo_cpu_model, "auto")
        set_combo(self.combo_graphics, "auto")
        is_win11 = os_type == "windows" and version_name == "Windows 11"
        self.check_secure_boot.setChecked(bool(profile.get("secure_boot", False) or is_win11))
        self.check_tpm.setChecked(bool(profile.get("tpm", False) or is_win11))
        self.update_firmware_options_visibility()
        self._update_vm_summary()

    def update_firmware_options_visibility(self, *args):
        os_type = self.combo_main_os.currentData()
        is_macos = os_type == "macos"
        is_uefi = self.combo_firmware.currentData() == "uefi"
        is_win11 = os_type == "windows" and self.combo_win_ver.currentText() == "Windows 11"

        if is_macos or is_win11:
            idx = self.combo_firmware.findData("uefi")
            if idx >= 0 and self.combo_firmware.currentIndex() != idx:
                self.combo_firmware.blockSignals(True)
                self.combo_firmware.setCurrentIndex(idx)
                self.combo_firmware.blockSignals(False)
            self.combo_firmware.setEnabled(False)
            is_uefi = True
        else:
            self.combo_firmware.setEnabled(True)

        if is_macos:
            q35_idx = self.combo_chipset.findData("q35")
            if q35_idx >= 0 and self.combo_chipset.currentIndex() != q35_idx:
                self.combo_chipset.blockSignals(True)
                self.combo_chipset.setCurrentIndex(q35_idx)
                self.combo_chipset.blockSignals(False)
            self.combo_chipset.setEnabled(False)
        else:
            self.combo_chipset.setEnabled(True)

        if is_macos:
            nat_idx = self.combo_network_mode.findData("nat")
            if nat_idx >= 0:
                self.combo_network_mode.setCurrentIndex(nat_idx)
            self.combo_network_mode.setEnabled(False)
            self.combo_network_count.setCurrentIndex(self.combo_network_count.findData(1))
            self.combo_network_count.setEnabled(False)
            self.update_network_options()
        else:
            self.combo_network_mode.setEnabled(True)
            self.combo_network_count.setEnabled(True)

        show_security = is_uefi and not is_macos
        self.security_options_widget.setVisible(show_security)
        if not show_security:
            self.check_secure_boot.setChecked(False)
            self.check_tpm.setChecked(False)

        if is_win11:
            self.check_secure_boot.setChecked(True)
            self.check_tpm.setChecked(True)

    def _vm_name_from_item(self, item):
        """Nombre real de la VM de un QListWidgetItem.

        Prefiere el UserRole (guardado por refresh_vm_list). Cae al
        parser de texto si el UserRole no está (items creados por
        código antiguo, tests, etc.).
        """
        if item is None:
            return ""
        try:
            name = item.data(_VM_USER_ROLE)
            if name:
                return str(name)
        except Exception:
            pass
        try:
            return self._vm_name_from_list_text(item.text())
        except Exception:
            return ""

    @staticmethod
    def _vm_name_from_list_text(text):
        name = text.split("  ", 1)[-1].strip()
        # Quitar el prefijo "[Grupo] " si lo hubiera.
        if name.startswith("["):
            close = name.find("]")
            if close > 0:
                name = name[close + 1:].strip()
        while name.endswith(" ⚠️"):
            name = name[: -len(" ⚠️")].strip()
        return name

    def _vm_has_shared_folder_issue(self, vm_dir):
        try:
            cfg = self._load_vm_config_cached(vm_dir)
            folders = (cfg.get("extra") or {}).get("shared_folders", [])
            folders = folders if isinstance(folders, list) else []
        except Exception:
            return False
        for i, f in enumerate(folders):
            if not isinstance(f, dict) or str(f.get("method", "")).lower() != "virtiofs":
                continue
            pidfile = os.path.join(vm_dir, f"virtiofs-{i}.pid")
            try:
                with open(pidfile, encoding="utf-8") as fh:
                    pid = int(fh.read().strip())
                os.kill(pid, 0)
            except Exception:
                return True
        return False

    def _detect_spice_vdagent(self, vm_dir):
        """Devuelve True/False/None según si spice-vdagent responde.

        None → no se pudo determinar (VM apagada, sin QGA, etc.).
        """
        try:
            data = self._load_vm_config_cached(vm_dir)
            os_type = (data.get("os_type") or "linux").lower()
        except Exception:
            os_type = "linux"

        if os_type == "windows":
            # tasklist devuelve línea con "spice-vdagent.exe" si existe.
            try:
                r = self._qga_request({
                    "execute": "guest-exec",
                    "arguments": {
                        "path": "cmd.exe",
                        "arg": ["/c", "tasklist", "/FI", "IMAGENAME eq spice-vdagent.exe"],
                        "capture-output": True,
                    },
                }, timeout=4)
                pid = (r.get("return") or {}).get("pid")
                if not pid:
                    return None
                import time as _t
                for _ in range(10):
                    _t.sleep(0.15)
                    r2 = self._qga_request({
                        "execute": "guest-exec-status",
                        "arguments": {"pid": pid},
                    }, timeout=3)
                    status = r2.get("return") or {}
                    if status.get("exited"):
                        # out-data viene base64-encoded.
                        import base64
                        out = base64.b64decode(status.get("out-data") or "").decode("utf-8", "ignore")
                        return "spice-vdagent.exe" in out.lower()
                return None
            except Exception:
                return None
        else:
            # Linux: pgrep -f spice-vdagentd (o spice-vdagent para sesiones).
            for pattern in ("spice-vdagentd", "spice-vdagent"):
                try:
                    r = self._qga_request({
                        "execute": "guest-exec",
                        "arguments": {
                            "path": "/bin/sh",
                            "arg": ["-c", f"pgrep -f {pattern} >/dev/null 2>&1 && echo YES || echo NO"],
                            "capture-output": True,
                        },
                    }, timeout=4)
                    pid = (r.get("return") or {}).get("pid")
                    if not pid:
                        continue
                    import time as _t
                    for _ in range(10):
                        _t.sleep(0.15)
                        r2 = self._qga_request({
                            "execute": "guest-exec-status",
                            "arguments": {"pid": pid},
                        }, timeout=3)
                        status = r2.get("return") or {}
                        if status.get("exited"):
                            import base64
                            out = base64.b64decode(status.get("out-data") or "").decode("utf-8", "ignore").strip()
                            if out.endswith("YES"):
                                return True
                            # Si el patrón es "spice-vdagentd" y no está,
                            # probamos "spice-vdagent" antes de dar NO.
                            break
                except Exception:
                    continue
            return False

    def _compute_live_integration_status(self, vm_dir):
        result = {"guest_agent": False, "shared_folders": True,
                  "clipboard": None, "spice_vdagent": None}
        try:
            qga_result = self._qga_request({"execute": "guest-info"}, timeout=2)
            result["guest_agent"] = "return" in (qga_result or {})
        except Exception:
            result["guest_agent"] = False

        # Detección de spice-vdagent dentro del guest.
        if result["guest_agent"]:
            try:
                result["spice_vdagent"] = self._detect_spice_vdagent(vm_dir)
            except Exception:
                result["spice_vdagent"] = None

        result["shared_folders"] = not self._vm_has_shared_folder_issue(vm_dir)

        try:
            cfg = self._load_vm_config_cached(vm_dir)
            mode = (cfg.get("extra") or {}).get("clipboard", {}).get("mode", "disabled")
        except Exception:
            mode = "disabled"
        result["clipboard"] = mode if mode != "disabled" else None
        return result

    def _refresh_live_integration_status(self):
        if not hasattr(self, "label_live_guest_agent"):
            return
        off_color = "#9e9e9e"
        if not self.current_vm_dir:
            self.label_live_guest_agent.setText(self.tr("Guest Agent: —"))
            self.label_live_shared_folders.setText(self.tr("Carpetas: —"))
            self.label_live_clipboard.setText(self.tr("Clipboard: —"))
            if hasattr(self, "label_live_vdagent"):
                self.label_live_vdagent.setText(self.tr("spice-vdagent: —"))
            for lbl in (self.label_live_guest_agent, self.label_live_shared_folders, self.label_live_clipboard):
                lbl.setStyleSheet(f"font-size:11px; color:{off_color};")
            return
        vm_name = os.path.basename(self.current_vm_dir)
        if self._runtime_state(vm_name) != "running":
            self.label_live_guest_agent.setText(self.tr("Guest Agent: apagado"))
            self.label_live_shared_folders.setText(self.tr("Carpetas: apagado"))
            self.label_live_clipboard.setText(self.tr("Clipboard: apagado"))
            if hasattr(self, "label_live_vdagent"):
                self.label_live_vdagent.setText(self.tr("spice-vdagent: apagado"))
            for lbl in (self.label_live_guest_agent, self.label_live_shared_folders, self.label_live_clipboard):
                lbl.setStyleSheet(f"font-size:11px; color:{off_color};")
            return
        if getattr(self, "_live_integration_thread", None) is not None and self._live_integration_thread.isRunning():
            return
        vm_dir = self.current_vm_dir

        def _work(_log_emit):
            return self._compute_live_integration_status(vm_dir)

        thread = _BackgroundCallThread(_work, parent=self)

        def _on_done(result, error):
            self._live_integration_thread = None
            if error is not None or result is None or self.current_vm_dir != vm_dir:
                return
            ok_color, bad_color = "#2e7d32", "#c62828"
            ga_ok = result.get("guest_agent")
            self.label_live_guest_agent.setText(self.tr("Guest Agent: {0}").format(self.tr("activo") if ga_ok else self.tr("sin respuesta")))
            self.label_live_guest_agent.setStyleSheet(f"font-size:11px; color:{ok_color if ga_ok else bad_color};")
            sf_ok = result.get("shared_folders")
            self.label_live_shared_folders.setText(self.tr("Carpetas: {0}").format(self.tr("OK") if sf_ok else self.tr("con problemas")))
            self.label_live_shared_folders.setStyleSheet(f"font-size:11px; color:{ok_color if sf_ok else bad_color};")
            if result.get("clipboard"):
                self.label_live_clipboard.setText(self.tr("Clipboard: activo"))
                self.label_live_clipboard.setStyleSheet(f"font-size:11px; color:{ok_color};")
            else:
                self.label_live_clipboard.setText(self.tr("Clipboard: desactivado"))
                self.label_live_clipboard.setStyleSheet(f"font-size:11px; color:{off_color};")

            # spice-vdagent: activo / no detectado / —
            vd = result.get("spice_vdagent")
            if hasattr(self, "label_live_vdagent"):
                if vd is True:
                    self.label_live_vdagent.setText(self.tr("spice-vdagent: activo"))
                    self.label_live_vdagent.setStyleSheet(
                        f"font-size:11px; color:{ok_color};")
                elif vd is False:
                    self.label_live_vdagent.setText(
                        self.tr("spice-vdagent: no detectado"))
                    self.label_live_vdagent.setStyleSheet(
                        f"font-size:11px; color:{off_color};")
                else:
                    self.label_live_vdagent.setText(self.tr("spice-vdagent: —"))
                    self.label_live_vdagent.setStyleSheet(
                        f"font-size:11px; color:{off_color};")

        thread.done_signal.connect(_on_done)
        self._live_integration_thread = thread
        thread.start()

    def _vm_os_icon(self, vm_name):
        """Devuelve el QIcon correspondiente al SO de la VM `vm_name`.

        Usa iconos SVG embebidos (vm_icons.py), por lo que NO depende del
        tema del sistema: se ven igual en KDE, GNOME, XFCE, etc., y no hay
        que instalar ningún paquete de iconos adicional.
        """
        from vm_icons import icon_for_vm

        try:
            cfg_path = os.path.join(vm_config.BASE_VM_DIR, vm_name, "vm_config.ini")
            if not os.path.isfile(cfg_path):
                return icon_for_vm("", "")
            cfg = self._load_vm_config_cached(os.path.join(vm_config.BASE_VM_DIR, vm_name))
        except Exception:
            return icon_for_vm("", "")

        os_type = cfg.get("os_type") or ""
        extra = cfg.get("extra") or {}
        distro = extra.get("distro") or ""

        try:
            return icon_for_vm(os_type, distro, size=32)
        except Exception:
            return icon_for_vm("", "")



    # ------------------------------------------------------------------
    # Filtro por grupo en la lista lateral (marcador vm_group_filter_v1)
    # ------------------------------------------------------------------
    # El combo "Grupo:" del panel izquierdo se rellena con los grupos
    # existentes al vuelo (recorriendo vm_config.ini de cada VM). Opciones
    # especiales: "" = todos, "__none__" = VMs sin grupo.

    _VM_GROUP_NONE = "__none__"

    def _populate_vm_group_filter(self):
        """Rellena combo_vm_group con los grupos existentes."""
        combo = getattr(self, "combo_vm_group", None)
        if combo is None:
            return
        cur = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr("Todos los grupos"), "")
        combo.addItem(self.tr("Sin grupo"), self._VM_GROUP_NONE)
        for g in self._all_vm_groups():
            combo.addItem(g, g)
        idx = combo.findData(cur)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _apply_vm_group_filter(self, group_key=None):
        """Muestra u oculta los items de la lista según el grupo elegido.

        Combina con el filtro de texto del buscador: se aplican ambos.
        """
        if group_key is None:
            combo = getattr(self, "combo_vm_group", None)
            group_key = combo.currentData() if combo is not None else ""
        search = ""
        try:
            sb = getattr(self, "input_vm_search", None)
            search = (sb.text() if sb is not None else "").strip().lower()
        except Exception:
            search = ""
        for i in range(self.vm_list.count()):
            item = self.vm_list.item(i)
            name = self._vm_name_from_item(item)
            vm_dir = os.path.join(vm_config.BASE_VM_DIR, name)
            try:
                g = self._load_vm_group(vm_dir)
            except Exception:
                g = ""
            match_group = (
                group_key == ""
                or (group_key == self._VM_GROUP_NONE and not g)
                or (group_key == g)
            )
            match_search = (not search) or (search in name.lower())
            item.setHidden(not (match_group and match_search))

    def _on_vm_group_filter_changed(self, *_args):
        self._apply_vm_group_filter()


    def _vm_list_label(self, name, state):
        """Etiqueta de la VM en la lista lateral.

        Los avisos (carpeta compartida caída, muerte inesperada detectada
        por el watchdog) se marcan con ⚠️ — un solo símbolo, sin duplicar
        aunque las dos condiciones se cumplan a la vez.

        Si la VM tiene grupo (extra["group"]), se antepone "[Grupo] " al
        nombre. El color (extra["color"]) lo aplica refresh_vm_list como
        fondo del ítem (no aquí).
        """
        icon = "●" if state == "running" else ("◐" if state == "paused" else "○")
        warning = False
        if state == "running" and self._vm_has_shared_folder_issue(
                os.path.join(vm_config.BASE_VM_DIR, name)):
            warning = True
        if name in getattr(self, "_vm_death_flag", set()):
            warning = True
        suffix = " ⚠️" if warning else ""
        _group = ""
        try:
            _g = self._load_vm_group(os.path.join(vm_config.BASE_VM_DIR, name))
            if _g:
                _group = f"[{_g}] "
        except Exception:
            _group = ""
        return f"{icon}  {_group}{name}{suffix}"


    def refresh_vm_list(self, select_name=None):
        vms = list_existing_vms()
        # Ordenar la lista segun la preferencia del usuario. Se hace
        # antes del bucle que crea los items para que el orden sea el
        # final; seleccionar la VM activa al final funciona igual.
        try:
            if hasattr(self, "_apply_vm_order"):
                vms = self._apply_vm_order(vms)
        except Exception:
            pass
        if select_name is None:
            select_name = os.path.basename(self.current_vm_dir) if self.current_vm_dir else None
        self.vm_list.blockSignals(True)
        self.vm_list.clear()
        from PyQt6.QtWidgets import QListWidgetItem as _QListWidgetItem
        for name in vms:
            state = self._runtime_state(name)
            # Creamos el item explícitamente para poder asignarle un
            # icono por SO (setIcon). El texto del item sigue llevando
            # el símbolo de estado (● / ◐ / ○) más el nombre.
            item = _QListWidgetItem(self._vm_list_label(name, state))
            try:
                item.setData(_VM_USER_ROLE, name)
            except Exception:
                pass
            # vm_grid_view_v2_card: datos extra para el delegate de tarjetas.
            try:
                item.setData(257, state)  # _VM_STATE_ROLE
            except Exception:
                pass
            try:
                _gcolor = self._load_vm_color(os.path.join(vm_config.BASE_VM_DIR, name))
                if _gcolor:
                    item.setData(258, _gcolor)  # _VM_COLOR_ROLE
            except Exception:
                pass
            # Tooltip extendido en modo tarjeta (y también en lista, no molesta).
            try:
                _grp = self._load_vm_group(os.path.join(vm_config.BASE_VM_DIR, name))
                _tips = [name]
                if _grp:
                    _tips.append("Grupo: " + _grp)
                try:
                    _data = self._load_vm_config_cached(
                        os.path.join(vm_config.BASE_VM_DIR, name))
                    _ram = _data.get("ram") or ""
                    _cores = _data.get("cores") or ""
                    _os = _data.get("os_type") or ""
                    if _os:
                        _tips.append("SO: " + str(_os))
                    if _ram:
                        _tips.append("RAM: " + str(_ram))
                    if _cores:
                        _tips.append("Nucleos: " + str(_cores))
                except Exception:
                    pass
                _tips.append("")
                _tips.append("Doble clic para abrir. Boton derecho para mas opciones.")
                item.setToolTip("\n".join(_tips))
            except Exception:
                pass
            # Padding del ítem. Antes lo hacía el QSS (::item { padding }),
            # pero eso bloqueaba el BackgroundRole del ítem.
            # vm_grid_view_v1: el sizeHint depende del modo de vista
            # (0×36 en lista, 170×190 en tarjetas).
            try:
                _hint = self._vm_view_size_hint()
                if _hint is not None:
                    item.setSizeHint(_hint)
            except Exception:
                pass
            try:
                icon = self._vm_os_icon(name)
                if icon is not None and not icon.isNull():
                    item.setIcon(icon)
            except Exception:
                pass
            # Fondo suave según extra["color"], si lo hay.
            # Fondo suave según extra["color"], si lo hay.
            # Requiere que QListWidget NO tenga reglas ::item en QSS
            # (ni en APP_QSS ni en el stylesheet local): con QSS ::item,
            # Qt ignora setBackground() por completo.
            try:
                _c = self._load_vm_color(os.path.join(vm_config.BASE_VM_DIR, name))
                if _c and _c.startswith("#") and len(_c) == 7:
                    from PyQt6.QtGui import QColor as _QColor, QBrush as _QBrush
                    _qcol = _QColor(_c)
                    _qcol.setAlpha(150)
                    item.setBackground(_QBrush(_qcol))
            except Exception:
                pass
            self.vm_list.addItem(item)
        if select_name:
            for i in range(self.vm_list.count()):
                if self._vm_name_from_list_text(self.vm_list.item(i).text()) == select_name:
                    self.vm_list.setCurrentRow(i)
                    break
        self.vm_list.blockSignals(False)
        # Rellenar el combo de filtro por grupo (idempotente) y aplicar
        # el filtro activo, si lo hay.
        try:
            if hasattr(self, "_populate_vm_group_filter"):
                self._populate_vm_group_filter()
            if hasattr(self, "_apply_vm_group_filter") and hasattr(self, "combo_vm_group"):
                self._apply_vm_group_filter(self.combo_vm_group.currentData())
        except Exception:
            pass
        # welcome_screen_v1: mostrar la bienvenida si no hay VMs.
        if hasattr(self, "_update_vm_list_stack"):
            try:
                self._update_vm_list_stack()
            except Exception:
                pass
        self.refresh_vm_runtime_status()

    def on_vm_list_item_clicked(self, item):
        """Re-enfoca la consola de la VM clicada, aunque ya estuviera
        seleccionada.

        currentTextChanged solo dispara cuando cambia la selección.
        itemClicked dispara siempre. Solo actuamos si el ítem clicado ES
        la VM ya seleccionada (el cambio en sí lo maneja
        on_vm_list_changed → open_vm → _focus_console_for_vm).
        """
        if item is None:
            return
        name = self._vm_name_from_item(item)
        if not name or not self.current_vm_dir:
            return
        if os.path.basename(self.current_vm_dir) != name:
            return  # es un cambio: lo cubre on_vm_list_changed
        if hasattr(self, "_focus_console_for_vm"):
            try:
                self._focus_console_for_vm(name)
            except Exception:
                pass

    def on_vm_list_changed(self, text):
        # vm_config_save_cancel_v1_actions: si hay cambios pendientes, preguntar.
        if (self.current_vm_dir and text
                and getattr(self, "_has_pending_changes", None)
                and self._has_pending_changes()):
            _cur_name = os.path.basename(self.current_vm_dir)
            _new_name = self._vm_name_from_list_text(text) if hasattr(self, "_vm_name_from_list_text") else ""
            if _new_name and _new_name != _cur_name:
                box = QMessageBox(self)
                box.setWindowTitle(self.tr("Cambios sin guardar"))
                box.setIcon(QMessageBox.Icon.Question)
                box.setTextFormat(Qt.TextFormat.RichText)
                box.setText(
                    self.tr("La VM <b>{0}</b> tiene cambios sin guardar.").format(_cur_name)
                )
                box.setInformativeText(
                    self.tr("¿Qué quieres hacer antes de cambiar a '{0}'?").format(_new_name)
                )
                btn_save = box.addButton(
                    self.tr("💾 Guardar y cambiar"),
                    QMessageBox.ButtonRole.AcceptRole,
                )
                btn_discard = box.addButton(
                    self.tr("↺ Descartar y cambiar"),
                    QMessageBox.ButtonRole.DestructiveRole,
                )
                btn_cancel = box.addButton(
                    self.tr("Cancelar"),
                    QMessageBox.ButtonRole.RejectRole,
                )
                box.setDefaultButton(btn_save)
                box.exec()
                clicked = box.clickedButton()
                if clicked is btn_cancel:
                    try:
                        for _i in range(self.vm_list.count()):
                            _it = self.vm_list.item(_i)
                            if self._vm_name_from_item(_it) == _cur_name:
                                self.vm_list.blockSignals(True)
                                self.vm_list.setCurrentRow(_i)
                                self.vm_list.blockSignals(False)
                                break
                    except Exception:
                        pass
                    return
                if clicked is btn_save:
                    if not self._save_config_from_ui():
                        return

        if not text:
            self.current_vm_dir = None
            self.vm_control_status.setText(self.tr("● Sin VM seleccionada"))
            return
        # Preferir el currentItem para usar el UserRole (a prueba de
        # prefijos [Grupo] y sufijos ⚠️ en el texto).
        item = None
        try:
            item = self.vm_list.currentItem()
        except Exception:
            item = None
        if item is not None:
            name = self._vm_name_from_item(item)
        else:
            name = self._vm_name_from_list_text(text)
        if name in list_existing_vms():
            self.open_vm(name)

    def _runtime_paths(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir:
            return None, None
        return os.path.join(vm_dir, "qemu.pid"), os.path.join(vm_dir, "qemu.qmp")

    def _runtime_state(self, vm_name):
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
        pid_path, qmp_path = self._runtime_paths(vm_dir)
        if not pid_path or not os.path.isfile(pid_path):
            return "stopped"
        try:
            with open(pid_path, encoding="utf-8") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
        except Exception:
            return "stopped"
        try:
            result = self._qmp_command(vm_dir, {"execute":"query-status"})
            status = (result.get("return") or {}).get("status", "running")
            return "paused" if status in ("paused", "prelaunch", "inmigrate") else "running"
        except Exception:
            return "running"

    def _qmp_command(self, vm_dir, payload):
        import socket, json as _json, time
        qmp = os.path.join(vm_dir, "qemu.qmp")
        if not os.path.exists(qmp):
            raise RuntimeError("El monitor QMP de la VM no está disponible.")

        def recv_json_message(sock, buffer):
            while True:
                pos = buffer.find(b"\r\n")
                if pos >= 0:
                    raw, buffer = buffer[:pos], buffer[pos + 2:]
                    if not raw:
                        continue
                    try:
                        return _json.loads(raw.decode()), buffer
                    except Exception:
                        continue
                chunk = sock.recv(4096)
                if not chunk:
                    raise RuntimeError("QMP cerró la conexión antes de responder.")
                buffer += chunk
                if len(buffer) > 524288:
                    raise RuntimeError("Respuesta QMP demasiado grande.")

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(4.0)
        buffer = b""
        try:
            sock.connect(qmp)
            _hello, buffer = recv_json_message(sock, buffer)

            cap = {"execute": "qmp_capabilities", "id": "capabilities"}
            sock.sendall((_json.dumps(cap) + "\r\n").encode())
            while True:
                msg, buffer = recv_json_message(sock, buffer)
                if msg.get("id") == "capabilities":
                    if "error" in msg:
                        raise RuntimeError(str(msg["error"]))
                    break

            command_id = f"cmd_{int(time.time() * 1000000)}"
            request = dict(payload)
            request["id"] = command_id
            sock.sendall((_json.dumps(request) + "\r\n").encode())

            deadline = time.monotonic() + 4.0
            while time.monotonic() < deadline:
                msg, buffer = recv_json_message(sock, buffer)
                if msg.get("id") != command_id:
                    continue
                if "error" in msg:
                    err = msg.get("error") or {}
                    desc = err.get("desc") if isinstance(err, dict) else str(err)
                    raise RuntimeError(desc or str(err))
                return msg
            raise RuntimeError("QMP agotó el tiempo de espera para la respuesta.")
        finally:
            sock.close()

    def _qmp_hmp(self, vm_dir, command_line):
        result = self._qmp_command(vm_dir, {"execute":"human-monitor-command", "arguments":{"command-line":command_line}})
        text = str(result.get("return") or "")
        low = text.lower()
        if any(token in low for token in ("error:", "failed", "cannot", "could not", "not found", "invalid")):
            raise RuntimeError(text.strip())
        return result

    def _get_fullscreen_exit_value(self):
        from PyQt6.QtCore import QSettings
        from virtual_machine import DEFAULT_FULLSCREEN_EXIT_SHORTCUT

        combo = getattr(self, "combo_fullscreen_exit", None)
        if combo is not None:
            value = combo.currentData()
        else:
            value = None
        if not value:
            value = QSettings().value(
                "console/fullscreen_exit_shortcut", DEFAULT_FULLSCREEN_EXIT_SHORTCUT
            )
        return value

    def _fullscreen_exit_display_text(self):
        value = self._get_fullscreen_exit_value()
        if value == "RCTRL":
            return self.tr("Ctrl derecho")
        from PyQt6.QtGui import QKeySequence
        return QKeySequence(value).toString()

    def _event_matches_fullscreen_exit(self, event):
        value = self._get_fullscreen_exit_value()

        if value == "RCTRL":
            from PyQt6.QtCore import Qt as _Qt
            if event.key() != _Qt.Key.Key_Control:
                return False
            try:
                if event.nativeScanCode() == 105:
                    return True
            except Exception:
                pass
            try:
                if event.nativeVirtualKey() == 0xFFE4:
                    return True
            except Exception:
                pass
            return False

        from PyQt6.QtGui import QKeySequence
        combo = event.keyCombination() if hasattr(event, "keyCombination") else None
        if combo is None:
            return False
        return QKeySequence(combo) == QKeySequence(value)

    def _on_fullscreen_exit_shortcut_changed(self, _index):
        from PyQt6.QtCore import QSettings

        combo = getattr(self, "combo_fullscreen_exit", None)
        if combo is None:
            return
        value = combo.currentData()
        QSettings().setValue("console/fullscreen_exit_shortcut", value)
        self._update_fullscreen_button_tooltip()

    def _update_fullscreen_button_tooltip(self):
        btn = getattr(self, "btn_vnc_fullscreen", None)
        if btn is None:
            return
        btn.setToolTip(self.tr(
            "Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\n"
            "completa en una ventana propia. NO afecta al visor externo:\n"
            "para ese, usa el checkbox 'Externos en pantalla completa'\n"
            "de la fila de estado.\n\n"
            "Pulsa {0} para salir."
        ).format(self._fullscreen_exit_display_text()))

    def _toggle_vnc_fullscreen(self):
        if getattr(self, "vnc_widget", None) is None:
            return
        if getattr(self, "_vnc_fullscreen_window", None) is not None:
            self._close_vnc_fullscreen()
        else:
            self._open_vnc_fullscreen()

    def _open_vnc_fullscreen(self):
        from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
        from PyQt6.QtCore import Qt, QEvent, QObject

        self._vnc_fullscreen_container = getattr(self, "vnc_scroll_area", None) or self.vnc_widget
        self._vnc_original_layout = self.console_page.layout()
        self._vnc_original_layout.removeWidget(self._vnc_fullscreen_container)
        self._vnc_fullscreen_container.setParent(None)

        self.vnc_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._vnc_fullscreen_window = QMainWindow()
        vm_name = os.path.basename(self.current_vm_dir) if self.current_vm_dir else "VM"
        self._vnc_fullscreen_window.setWindowTitle(f"Consola Gráfica — {vm_name}")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._vnc_fullscreen_container)
        self._vnc_fullscreen_window.setCentralWidget(central)

        class _FullscreenKeyFilter(QObject):
            def __init__(self, mixin_self):
                super().__init__()
                self._m = mixin_self

            def _matches_exit(self, event):
                return self._m._event_matches_fullscreen_exit(event)

            def eventFilter(self, obj, event):
                etype = event.type()

                if etype == QEvent.Type.ShortcutOverride:
                    event.accept()
                    return True

                if etype == QEvent.Type.KeyPress:
                    if self._matches_exit(event):
                        self._m._close_vnc_fullscreen()
                        event.accept()
                        return True
                    if self._m.vnc_widget is not None:
                        self._m.vnc_widget.keyPressEvent(event)
                    return True

                if etype == QEvent.Type.KeyRelease:
                    if self._matches_exit(event):
                        event.accept()
                        return True
                    if self._m.vnc_widget is not None:
                        self._m.vnc_widget.keyReleaseEvent(event)
                    return True

                return False

        self._vnc_fullscreen_filter = _FullscreenKeyFilter(self)
        self.vnc_widget.installEventFilter(self._vnc_fullscreen_filter)

        self._vnc_fullscreen_window.showFullScreen()
        self.vnc_widget.setFocus()
        self.vnc_widget.grabKeyboard()

        from PyQt6.QtCore import QTimer as _QTimer
        import x11_keyboard_grab as _x11kb

        def _try_x11_grab(attempts_left, delay_ms):
            if getattr(self, "_vnc_fullscreen_window", None) is None:
                return
            ok = _x11kb.grab_keyboard(int(self._vnc_fullscreen_window.winId()))
            if not ok and attempts_left > 0:
                _QTimer.singleShot(
                    delay_ms, lambda: _try_x11_grab(attempts_left - 1, delay_ms)
                )

        _QTimer.singleShot(150, lambda: _try_x11_grab(3, 200))

        if getattr(self, "btn_vnc_fullscreen", None) is not None:
            self.btn_vnc_fullscreen.setText("⛶ Salir de pantalla completa")

    def _close_vnc_fullscreen(self):
        if getattr(self, "_vnc_fullscreen_window", None) is None:
            return

        import x11_keyboard_grab as _x11kb
        _x11kb.ungrab_keyboard()

        vnc_filter = getattr(self, "_vnc_fullscreen_filter", None)
        if self.vnc_widget is not None:
            self.vnc_widget.releaseKeyboard()
            if vnc_filter is not None:
                self.vnc_widget.removeEventFilter(vnc_filter)
        self._vnc_fullscreen_filter = None

        container = getattr(self, "_vnc_fullscreen_container", None) or self.vnc_widget
        if container is not None:
            container.setParent(None)

        self._vnc_fullscreen_window.close()
        self._vnc_fullscreen_window.deleteLater()
        self._vnc_fullscreen_window = None

        if container is not None and self._vnc_original_layout is not None:
            self._vnc_original_layout.addWidget(container, 1)
            container.show()
        if self.vnc_widget is not None:
            self.vnc_widget.setFocus()
        self._vnc_fullscreen_container = None

        if getattr(self, "btn_vnc_fullscreen", None) is not None:
            self.btn_vnc_fullscreen.setText("⛶ Pantalla completa del visor")

    def _start_vnc_resize_watcher(self):
        """Arranca un watcher ligero que reajusta el widget VNC cuando el
        framebuffer del guest cambia de tamaño.

        Esto ocurre por ejemplo al restaurar un snapshot creado con otra
        resolución: el widget VNC recibía el nuevo framebuffer pero quedaba
        con el tamaño de la resolución anterior, y se veía "muy grande" o
        descentrado. En vez de depender de una señal del widget (que puede
        emitirse solo en el handshake inicial), comprobamos periódicamente
        las dimensiones del framebuffer y reaplicamos el modo de visualización.
        """
        from PyQt6.QtCore import QTimer as _QTimer
        if not hasattr(self, "_vnc_resize_timer"):
            self._vnc_resize_timer = _QTimer(self)
            self._vnc_resize_timer.setInterval(300)
            self._vnc_resize_timer.timeout.connect(self._check_vnc_guest_resolution)
        self._vnc_last_size = (0, 0)
        self._vnc_resize_timer.start()

    def _recreate_vnc_backbuffer(self, w):
        """Recrea el QImage backbuffer del widget VNC con las dimensiones
        actuales del framebuffer remoto.

        Se llama cuando detectamos que el guest cambió de resolución. El
        QVNCWidget original no recrea su backbuffer en ese caso: sigue
        escribiendo sobre un QImage del tamaño anterior. Al recrearlo
        (y pedir al servidor un frame completo), la parte "nueva" de la
        pantalla por fin se dibuja.

        Es seguro llamarlo aunque el atributo no exista: se registra en
        el log y se sigue con el resto del flujo.
        """
        try:
            from PyQt6.QtGui import QImage
        except Exception:
            return
        try:
            vw = int(getattr(w, "vncWidth", 0) or 0)
            vh = int(getattr(w, "vncHeight", 0) or 0)
            if vw <= 0 or vh <= 0:
                return

            # Recrear el backbuffer con el mismo formato que usa el widget.
            fmt = getattr(w, "PIX_FORMAT", None)
            if fmt is None:
                fmt = QImage.Format.Format_RGB32
            new_back = QImage(vw, vh, fmt)
            new_back.fill(0)

            # Asignar y limpiar referencias al frontbuffer anterior.
            try:
                w.backbuffer = new_back
            except Exception:
                pass
            try:
                w.frontbuffer = None
            except Exception:
                pass

            # Forzar al servidor VNC a enviarnos un frame completo.
            # El QVNCWidget original no expone un método público para
            # esto, pero internamente RFBClient tiene uno. Probamos los
            # nombres habituales.
            requested = False
            for attr in ("requestFullFrame", "request_full_update",
                         "requestFramebufferUpdate", "requestUpdate",
                         "refresh", "forceRefresh"):
                fn = getattr(w, attr, None)
                if callable(fn):
                    try:
                        fn()
                        requested = True
                        break
                    except Exception:
                        continue
            # Si no hay método directo, probamos sobre el hilo RFB.
            if not requested:
                for child_attr in ("connectionThread", "_rfb",
                                   "rfbClient", "_client"):
                    child = getattr(w, child_attr, None)
                    if child is None:
                        continue
                    for attr in ("requestFullFrame", "request_full_update",
                                 "requestFramebufferUpdate", "requestUpdate",
                                 "refresh"):
                        fn = getattr(child, attr, None)
                        if callable(fn):
                            try:
                                fn()
                                requested = True
                                break
                            except Exception:
                                continue
                    if requested:
                        break

            # Limpiar también el caché interno de updates si existe.
            for attr in ("updateRect", "lastUpdateRect", "dirtyRect"):
                try:
                    if hasattr(w, attr):
                        setattr(w, attr, None)
                except Exception:
                    pass

            self.log_message(
                f"==> VNC: nueva resolución detectada "
                f"({vw}x{vh}); backbuffer recreado"
                + (" y frame completo solicitado." if requested
                   else " (sin método de refresco disponible en el cliente).")
            )
        except Exception as e:
            try:
                self.log_message(f"[AVISO] VNC: error al recrear backbuffer: {e}")
            except Exception:
                pass

    def _check_vnc_guest_resolution(self):
        """Watcher del framebuffer del guest con reconexión automática.

        Detecta cambios de resolución del guest y, tras un periodo de
        estabilidad (debounce), reconecta el widget VNC para que el
        cliente obtenga un ServerInit actualizado.

        Por qué reconectar: el protocolo VNC básico fija el tamaño en el
        ServerInit. Tras el handshake, los cambios de resolución del
        guest NO son compatibles con el framebuffer del cliente (aunque
        pyQVNCWidget actualice vncWidth/vncHeight, los datos gráficos
        siguen llegando con el tamaño original). Un reconnect obtiene un
        ServerInit nuevo con la resolución actual.

        Por qué con debounce: durante el arranque del guest la
        resolución cambia varias veces (BIOS → bootloader → kernel →
        sesión de usuario). Si reconectáramos en cada cambio, tendríamos
        parpadeo continuo. En su lugar, un timer se REINICIA con cada
        cambio. Solo cuando la resolución se mantiene estable ~1.5 s se
        dispara una única reconexión.
        """
        w = getattr(self, "vnc_widget", None)
        if w is None:
            timer = getattr(self, "_vnc_resize_timer", None)
            if timer is not None:
                timer.stop()
            return
        try:
            size = (int(getattr(w, "vncWidth", 0) or 0),
                    int(getattr(w, "vncHeight", 0) or 0))
        except Exception:
            return
        if size == (0, 0):
            return

        last = getattr(self, "_vnc_last_size", (0, 0))
        if size == last:
            return

        is_initial = (last == (0, 0))
        self._vnc_last_size = size

        if is_initial:
            # Handshake inicial: no tocar el backbuffer, solo registrar.
            try:
                self.log_message(
                    f"==> VNC: framebuffer inicial {size[0]}x{size[1]}."
                )
            except Exception:
                pass
            try:
                self._apply_vnc_display_mode()
            except Exception:
                pass
            return

        # Cambio real de resolución del guest: programar reconexión con
        # debounce (se reinicia con cada cambio siguiente).
        try:
            self.log_message(
                f"==> VNC: cambio de resolución del guest: "
                f"{size[0]}x{size[1]} (reconexión tras estabilizar)."
            )
        except Exception:
            pass
        self._schedule_vnc_reconnect(
            1500, reason=f"cambio de resolución a {size[0]}x{size[1]}"
        )

    def _schedule_vnc_reconnect(self, delay_ms, reason=""):
        """Programa una reconexión del widget VNC con debounce.

        Si ya había un timer pendiente, lo REINICIA. Así, si el guest
        cambia de resolución varias veces seguidas (típico durante el
        arranque), solo se reconecta una vez al final, cuando la
        resolución se mantiene estable.
        """
        try:
            from PyQt6.QtCore import QTimer
        except Exception:
            return
        timer = getattr(self, "_vnc_reconnect_debounce", None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self._do_scheduled_vnc_reconnect)
            self._vnc_reconnect_debounce = timer
        self._vnc_reconnect_reason = reason
        timer.start(int(delay_ms))

    def _auto_reconnect_vnc_late(self):
        """Reconexión diferida tardía (8 s tras arranque).

        Cubre el caso de guests lentos (Windows, macOS con OpenCore) que
        tardan más de 3.5 s en establecer su resolución final. Solo
        reconecta si sigue habiendo una VM activa y si no ha habido ya
        una reconexión automática reciente (flag compartido con
        _do_scheduled_vnc_reconnect).
        """
        if not self._vm_is_selected():
            return
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
        except Exception:
            return
        if state not in ("running", "paused"):
            return
        w = getattr(self, "vnc_widget", None)
        if w is None:
            return
        # Si el usuario ya reconectó manualmente hace poco, no molestar.
        last = getattr(self, "_vnc_last_manual_reconnect_ts", 0)
        import time as _t
        if (_t.monotonic() - last) < 6:
            return
        try:
            self.log_message(
                "==> VNC: reconexión tardía (8 s) para asegurar la "
                "resolución final del guest."
            )
        except Exception:
            pass
        self._manual_refresh_vnc()

    def _do_scheduled_vnc_reconnect(self):
        """Ejecuta la reconexión diferida, si sigue habiendo VM activa."""
        w = getattr(self, "vnc_widget", None)
        if w is None:
            return
        if not self._vm_is_selected():
            return
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
        except Exception:
            return
        if state not in ("running", "paused"):
            return
        reason = getattr(self, "_vnc_reconnect_reason", "")
        try:
            self.log_message(f"==> VNC: reconectando ({reason}).")
        except Exception:
            pass
        self._manual_refresh_vnc()


    def _force_widget_relayout(self):
        """Reajusta el widget VNC y su scroll area al modo de zoom actual.

        Delega en _apply_vnc_display_mode(), que ya conoce los tres modos
        (fit / manual) y aplica el tamaño y las políticas correctas.
        Después fuerza un updateGeometry para que el scroll area calcule
        las barras inmediatamente sin esperar al siguiente resize.
        """
        try:
            self._apply_vnc_display_mode()
        except Exception:
            pass
        w = getattr(self, "vnc_widget", None)
        if w is not None:
            try:
                w.updateGeometry()
                w.update()
            except Exception:
                pass
        scroll = getattr(self, "vnc_scroll_area", None)
        if scroll is not None:
            try:
                scroll.updateGeometry()
                scroll.viewport().update()
            except Exception:
                pass



    def _manual_refresh_vnc(self):
        """Reconecta el widget VNC.

        En lugar de solo pedir un repaint (que no arregla nada si el
        framebuffer del cliente quedó desincronizado respecto al guest),
        se destruye el widget actual y se vuelve a crear. Eso fuerza un
        nuevo handshake y, si el guest tiene otra resolución ahora, la
        nueva conexión recogerá el tamaño correcto.
        """
        w = getattr(self, "vnc_widget", None)
        if w is None:
            return
        try:
            self.log_message("==> VNC: reconectando el widget (refresco solicitado).")
        except Exception:
            pass

        # Forzamos que _sync_vnc_widget considere que hay que reconectar.
        # La forma más limpia: destruir el widget aquí mismo y dejar que el
        # timer de estado lo vuelva a crear en la próxima pasada.
        try:
            # Detach del filtro de foco si existe.
            focus_filter = getattr(self, "_vnc_focus_filter", None)
            if focus_filter is not None:
                try:
                    focus_filter.detach()
                    w.removeEventFilter(focus_filter)
                except Exception:
                    pass
                self._vnc_focus_filter = None

            # Destruir el widget y su scroll area (igual que en _sync_vnc_widget
            # cuando el estado pasa a "stopped").
            layout = self.console_page.layout()
            scroll_area = getattr(self, "vnc_scroll_area", None)
            if layout is not None and scroll_area is not None:
                layout.replaceWidget(scroll_area, self.vnc_placeholder)
            if scroll_area is not None:
                scroll_area.takeWidget()
                scroll_area.deleteLater()
            w.deleteLater()
        except Exception as e:
            try:
                self.log_message(f"[AVISO] VNC: error al destruir el widget: {e}")
            except Exception:
                pass

        self.vnc_widget = None
        self.vnc_scroll_area = None
        self._vnc_last_size = (0, 0)

        try:
            self.vnc_placeholder.show()
            self.vnc_placeholder.setText("Reconectando…")
            self.vnc_label_status.setText("Reconectando al socket VNC…")
        except Exception:
            pass

        # La próxima pasada del timer de estado (1.5 s) detectará que la VM
        # sigue corriendo y llamará a _sync_vnc_widget, que creará un widget
        # nuevo. Si queremos que sea inmediato, forzamos esa comprobación:
        try:
            from PyQt6.QtCore import QTimer as _QTimer
            _QTimer.singleShot(200, self.refresh_vm_runtime_status)
        except Exception:
            pass

        # Restaurar el modo de visualización cuando el widget esté creado.
        try:
            from PyQt6.QtCore import QTimer as _QTimer2
            _QTimer2.singleShot(
                600,
                lambda: self._apply_vnc_display_mode()
                if getattr(self, "vnc_widget", None) is not None else None,
            )
        except Exception:
            pass


    def _release_vnc_keyboard_on_close(self):
        """Libera cualquier captura de teclado VNC pendiente.

        Sin esto, si el usuario cierra la app mientras el widget VNC tiene
        el foco, el XGrabKeyboard queda activo y el escritorio se queda sin
        teclado hasta que el usuario cierre sesión.
        """
        focus_filter = getattr(self, "_vnc_focus_filter", None)
        if focus_filter is not None:
            try:
                focus_filter.detach()
            except Exception:
                pass
        try:
            import x11_keyboard_grab
            x11_keyboard_grab.ungrab_keyboard()
        except Exception:
            pass

    def _toggle_console_tab(self):
        """Atajo Ctrl+Alt+C: alterna entre Consola Gráfica y la pestaña anterior.

        Guarda la pestaña actual antes de saltar a Consola Gráfica, para
        poder volver a ella. Si ya estamos en Consola Gráfica, salta al
        índice guardado (por defecto, Resumen).
        """
        tabs = getattr(self, "main_tabs", None)
        console_idx = getattr(self, "_console_tab_index", -1)
        if tabs is None or console_idx < 0:
            return
        current = tabs.currentIndex()
        if current == console_idx:
            target = getattr(self, "_console_prev_tab", 0)
            try:
                tabs.setCurrentIndex(int(target))
            except Exception:
                tabs.setCurrentIndex(0)
        else:
            self._console_prev_tab = current
            tabs.setCurrentIndex(console_idx)

    def _focus_console_tab(self):
        """Cambia a la pestaña Consola Gráfica si existe.

        Se llama UNA vez por arranque de VM, justo cuando se acaba de crear
        el widget de consola. Así el usuario ve la pantalla inmediatamente
        sin tener que buscar la pestaña a mano.
        """
        try:
            idx = getattr(self, "_console_tab_index", -1)
            if idx is not None and idx >= 0 and hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass

    def _apply_console_choice_from_vm(self, data):
        """Vuelca la elección de consola guardada en la VM a los combos.

        Se llama al abrir una VM. Sin esto, los combos conservaban el
        valor del último VM abierto: si abrías Linux Mint (SPICE) y luego
        Win11 (VNC), el combo seguía mostrando SPICE aunque la VM B
        estuviera configurada con VNC.
        """
        if not hasattr(self, "combo_console_protocol"):
            return
        extra = (data or {}).get("extra") or {}
        proto = str(extra.get("console_protocol") or PROTOCOL_VNC).lower()
        mode = str(extra.get("console_mode") or "").lower()
        if not mode:
            # Compatibilidad con VMs guardadas antes del cambio al modelo
            # protocolo/modo.
            mode = MODE_EMBEDDED if extra.get("vnc_embedded", True) else MODE_NATIVE
        try:
            self._apply_console_choice_to_ui(proto, mode)
        except Exception:
            pass
        # Refrescar el texto de ayuda y la pista de requisitos.
        try:
            self._refresh_console_help()
        except Exception:
            pass
        try:
            hint = describe_requirements(proto, mode)
            if hasattr(self, "label_console_requirements"):
                self.label_console_requirements.setText(hint)
        except Exception:
            pass

    def _destroy_embedded_console_widget(self):
        """Destruye el widget embebido actual (VNC o SPICE) si existe.

        Se llama cuando el usuario cambia de VM en la lista lateral: el
        widget actual está conectado al socket de la VM anterior, no de
        la nueva. Destruirlo deja el camino libre para que
        _sync_console_widget cree uno nuevo con la VM actual.

        Nota: NO toca el visor externo (spicy/remote-viewer). Los visores
        externos son persistentes por VM, gestionados aparte en
        _external_viewers.
        """
        # --- VNC embebido ---
        w = getattr(self, "vnc_widget", None)
        if w is not None:
            try:
                focus_filter = getattr(self, "_vnc_focus_filter", None)
                if focus_filter is not None:
                    try:
                        focus_filter.detach()
                        w.removeEventFilter(focus_filter)
                    except Exception:
                        pass
                    self._vnc_focus_filter = None
                if getattr(self, "_vnc_fullscreen_window", None) is not None:
                    try:
                        self._close_vnc_fullscreen()
                    except Exception:
                        pass
                layout = self.console_page.layout()
                scroll_area = getattr(self, "vnc_scroll_area", None)
                if layout is not None and scroll_area is not None:
                    layout.replaceWidget(scroll_area, self.vnc_placeholder)
                if scroll_area is not None:
                    scroll_area.takeWidget()
                    scroll_area.deleteLater()
                w.deleteLater()
            except Exception:
                pass
            self.vnc_widget = None
            self.vnc_scroll_area = None
            self._vnc_widget_vm_dir = None
            try:
                self.vnc_placeholder.show()
                self.vnc_placeholder.setText("Esperando conexión de la VM…")
            except Exception:
                pass

        # --- SPICE embebido ---
        sw = getattr(self, "spice_widget", None)
        if sw is not None:
            try:
                if hasattr(sw, "stop"):
                    sw.stop()
                layout = self.console_page.layout()
                if layout is not None:
                    layout.replaceWidget(sw, self.vnc_placeholder)
                sw.deleteLater()
            except Exception:
                pass
            self.spice_widget = None
            self._spice_widget_vm_dir = None
            try:
                self.vnc_placeholder.show()
                self.vnc_placeholder.setText("Esperando conexión de la VM…")
            except Exception:
                pass

    def _refresh_console_combo_tooltips(self):
        """Rellena los tooltips de cada item de los combos de consola.

        El texto refleja el estado actual de la sesión: X11 vs Wayland,
        spice-gtk con binding Python o no, visores externos disponibles.
        """
        try:
            from console_backend import (
                is_x11_session, embedded_spice_available,
                find_vnc_viewer, find_spice_viewer,
            )
            x11 = bool(is_x11_session())
            spice_gtk_ok = bool(embedded_spice_available())
            vnc_viewer, _ = find_vnc_viewer()
            spice_viewer, _ = find_spice_viewer()
        except Exception:
            x11, spice_gtk_ok = True, False
            vnc_viewer = spice_viewer = None

        session_note = "Sesión X11." if x11 else "Sesión Wayland."
        spice_embed_note = (
            "spice-gtk con binding Python disponible."
            if spice_gtk_ok
            else "spice-gtk sin binding Python: SPICE embebida caería a externo."
        )
        vnc_viewer_name = vnc_viewer.rsplit("/", 1)[-1] if vnc_viewer else "ninguno"
        spice_viewer_name = spice_viewer.rsplit("/", 1)[-1] if spice_viewer else "ninguno"

        # --- Protocolo ---
        combo_proto = getattr(self, "combo_console_protocol", None)
        if combo_proto is not None:
            for i in range(combo_proto.count()):
                data = combo_proto.itemData(i)
                if data == "vnc":
                    combo_proto.setItemData(
                        i,
                        "VNC: protocolo ligero, funciona con cualquier "
                        "dispositivo de video.\n"
                        "\n"
                        "Se puede embeber dentro de la app incluso en Wayland.\n"
                        "El visor externo disponible es: " + vnc_viewer_name + ".",
                        3,  # Qt.ItemDataRole.ToolTipRole
                    )
                elif data == "spice":
                    combo_proto.setItemData(
                        i,
                        "SPICE: mejor rendimiento en local (streaming de video,\n"
                        "clipboard bidireccional, audio remoto).\n"
                        "\n"
                        + session_note + "\n"
                        + spice_embed_note + "\n"
                        + "Visor externo disponible: " + spice_viewer_name + ".",
                        3,
                    )

        # --- Modo ---
        combo_mode = getattr(self, "combo_console_mode", None)
        if combo_mode is not None:
            for i in range(combo_mode.count()):
                data = combo_mode.itemData(i)
                if data == "embedded":
                    extra = (
                        "Se puede embeber dentro de la app (VNC y SPICE en X11)."
                        if x11
                        else "En Wayland solo VNC puede embeber; SPICE caería a externa."
                    )
                    combo_mode.setItemData(
                        i,
                        "Embebida: la pantalla vive dentro de la app.\n"
                        "\n"
                        + extra + "\n"
                        "\n"
                        "Para más detalle, mira el bloque de ayuda debajo de los combos.",
                        3,
                    )
                elif data == "external":
                    combo_mode.setItemData(
                        i,
                        "Ventana externa: se abre el visor del sistema.\n"
                        "Funciona en X11 y Wayland.\n"
                        "\n"
                        "VNC: " + vnc_viewer_name + ".\n"
                        "SPICE: " + spice_viewer_name + ".",
                        3,
                    )
                elif data == "native":
                    combo_mode.setItemData(
                        i,
                        "Ventana nativa de QEMU: QEMU abre su propia ventana\n"
                        "(GTK o SDL). Único modo compatible con VirGL y Venus.",
                        3,
                    )
                elif data == "hybrid":
                    combo_mode.setItemData(
                        i,
                        "Híbrida: VNC embebido + SPICE externo a la vez.\n"
                        "\n"
                        "VNC se ve dentro de la app (funciona en Wayland).\n"
                        "SPICE se abre en ventana externa para rendimiento.\n"
                        + ("" if spice_viewer else
                           "\nATENCIÓN: no hay visor SPICE instalado."),
                        3,
                    )

    def _refresh_console_status_banner(self):
        """Actualiza el banner de estado de la consola.

        Mira la elección actual (protocolo + modo) y el estado del host
        (sesión gráfica, visores disponibles) para decidir qué mostrar.
        """
        label = getattr(self, "label_console_status", None)
        if label is None:
            return
        try:
            protocol, mode = self._current_console_choice()
        except Exception:
            label.setText("")
            return

        # Paleta de colores y estado por defecto.
        # Ámbar: elección pedida ≠ lo que se aplicará.
        # Verde: sin cambios.
        # Rojo: no hay visor para hacer nada.
        text = ""
        style = (
            "font-size:11px; padding:2px 6px; border-radius:4px; "
            "background: transparent; color: #757575;"
        )

        # ¿Tenemos VM seleccionada?
        vm_selected = self._vm_is_selected()

        # ¿Es Linux Wayland/X11?  Solo importa para SPICE embebida.
        try:
            from console_backend import is_x11_session, embedded_spice_available
            x11 = bool(is_x11_session())
            spice_gtk_ok = bool(embedded_spice_available())
        except Exception:
            x11 = True
            spice_gtk_ok = False

        if protocol == "spice" and mode == "embedded":
            if not x11:
                text = "⚠ SPICE embebida no soporta Wayland: se usará visor externo."
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #fff3cd; color: #7a5b00; font-weight:bold;"
                )
            elif not spice_gtk_ok:
                text = ("⚠ Falta spice-gtk (binding Python): "
                        "SPICE embebida se abrirá como visor externo.")
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #fff3cd; color: #7a5b00; font-weight:bold;"
                )
            else:
                text = "SPICE embebida: la pantalla se verá dentro de la app."
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #e6f4ea; color: #1e7e34;"
                )
        elif protocol == "spice" and mode in ("external", "hybrid"):
            try:
                from console_backend import find_spice_viewer
                viewer, _tpl = find_spice_viewer()
            except Exception:
                viewer = None
            if viewer:
                text = f"SPICE externa: se usará {viewer.rsplit('/', 1)[-1]}."
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #e6f4ea; color: #1e7e34;"
                )
            else:
                text = ("⚠ No hay visor SPICE instalado "
                        "(spicy o remote-viewer).")
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #fdecea; color: #b71c1c; font-weight:bold;"
                )
        elif protocol == "vnc" and mode == "embedded":
            text = "VNC embebida: la pantalla se verá dentro de la app."
            style = (
                "font-size:11px; padding:2px 6px; border-radius:4px; "
                "background: #e6f4ea; color: #1e7e34;"
            )
        elif protocol == "vnc" and mode in ("external", "hybrid"):
            try:
                from console_backend import find_vnc_viewer
                viewer, _tpl = find_vnc_viewer()
            except Exception:
                viewer = None
            if viewer:
                text = f"VNC externa: se usará {viewer.rsplit('/', 1)[-1]}."
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #e6f4ea; color: #1e7e34;"
                )
            else:
                text = "⚠ No hay visor VNC instalado."
                style = (
                    "font-size:11px; padding:2px 6px; border-radius:4px; "
                    "background: #fdecea; color: #b71c1c; font-weight:bold;"
                )
        elif mode == "native":
            text = "Ventana nativa de QEMU: la VM abre su propia ventana."
            style = (
                "font-size:11px; padding:2px 6px; border-radius:4px; "
                "background: transparent; color: #757575;"
            )

        if not vm_selected:
            text = ""
            style = (
                "font-size:11px; padding:2px 6px; border-radius:4px; "
                "background: transparent; color: #757575;"
            )

        label.setText(text)
        label.setStyleSheet(style)

    def _sync_console_widget(self, state):
        """Despacha a VNC o SPICE según la elección guardada en la VM.

        Modos soportados:
          • native   → nada: QEMU abre su ventana.
          • embedded → widget embebido (VNC o SPICE; SPICE cae a externo en Wayland).
          • external → visor externo del sistema.
          • hybrid   → widget VNC embebido + visor SPICE externo en paralelo.

        Además: si el modo actual NO necesita visor externo, mata el que
        hubiera (por ejemplo al cambiar de hybrid a embedded VNC).
        """
        protocol = PROTOCOL_VNC
        mode = MODE_EMBEDDED
        if self.current_vm_dir:
            try:
                cfg = self._load_vm_config_cached(self.current_vm_dir)
                _extra = cfg.get("extra") or {}
                protocol = str(_extra.get("console_protocol") or PROTOCOL_VNC).lower()
                mode = str(_extra.get("console_mode") or "").lower()
                if not mode:
                    mode = MODE_EMBEDDED if _extra.get("vnc_embedded", True) else MODE_NATIVE
            except Exception:
                pass

        if mode == MODE_NATIVE:
            return

        if mode == MODE_HYBRID:
            # Widget VNC embebido (funciona en Wayland y X11) + visor SPICE
            # externo (spicy o remote-viewer). QEMU expone ambos a la vez.
            self._sync_embedded_vnc(state)
            self._sync_external_viewer(state, PROTOCOL_SPICE)
            return

        if mode == MODE_EXTERNAL:
            self._sync_external_viewer(state, protocol)
            return

        # mode == MODE_EMBEDDED
        if protocol == PROTOCOL_VNC:
            # Antes de mostrar el widget VNC, matar cualquier visor externo
            # que hubiera (por si el usuario cambió de hybrid a embedded).
            proc = getattr(self, "_external_viewer_proc", None)
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
                self._external_viewer_proc = None
            self._sync_embedded_vnc(state)
        else:
            self._sync_spice_widget(state, mode)


    def _kill_stale_spice_viewers(self):
        """Mata cualquier spicy/remote-viewer huérfano de intentos previos.

        Es útil sobre todo durante el desarrollo: si el flag se quedó mal y
        se lanzaron varios visores seguidos, al arrancar limpiamos. En
        producción el bucle está evitado por el flag _external_viewer_proc
        + ventana de gracia.
        """
        import shutil as _sh
        import subprocess as _sp
        for name in ("spicy", "remote-viewer"):
            binary = _sh.which(name)
            if not binary:
                continue
            try:
                _sp.run(["pkill", "-f", binary], check=False,
                        stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, timeout=2)
            except Exception:
                pass

    def _viewer_popen_env(self):
        """Env para lanzar el visor externo con backend X11.

        En sesiones Wayland, GTK 3/4 prefiere el backend Wayland. Eso
        hace que wmctrl (herramienta X11) no pueda ver la ventana, y por
        tanto no se pueda subir al frente al seleccionar la VM en la
        lista. Forzamos GDK_BACKEND=x11 para que corra a través de
        Xwayland: visualmente igual, pero visible por wmctrl.

        También forzamos QT_QPA_PLATFORM=xcb por si algún visor es Qt.
        """
        import os as _os
        env = _os.environ.copy()
        env["GDK_BACKEND"] = "x11"
        env["QT_QPA_PLATFORM"] = "xcb"
        return env

    def _on_external_fullscreen_toggled(self, checked):
        """Guarda la elección y la aplica al próximo lanzamiento."""
        from PyQt6.QtCore import QSettings
        QSettings().setValue("console/external_fullscreen", bool(checked))

    def _external_fullscreen_args(self, viewer_path):
        """Devuelve la lista de argumentos para pantalla completa del visor.

        No todos los visores aceptan la misma bandera; probamos la más
        habitual por orden de preferencia y, si no, devolvemos vacío
        (el visor se abrirá en ventana normal).
        """
        chk = getattr(self, "chk_external_fullscreen", None)
        if chk is None or not chk.isChecked():
            return []
        import os as _os
        name = _os.path.basename(str(viewer_path or "")).lower()
        if "remote-viewer" in name:
            return ["-f"]
        if "spicy" in name:
            return ["--full-screen"]
        if "vncviewer" in name or "tigervnc" in name:
            return ["-FullScreen"]
        if "gvncviewer" in name:
            # gvncviewer no soporta fullscreen por CLI de forma fiable.
            return []
        return []

    def _sync_external_viewer(self, state, protocol):
        """Gestiona el visor externo DEL VM ACTUAL.

        Estructura:
          • self._external_viewers = {vm_dir: {
                "proc": Popen,
                "protocol": "vnc" | "spice",
                "last_launch": float,
            }}
          • Cada VM tiene su propio visor. Cambiar de VM en la lista
            lateral NO cierra el visor de las otras VMs.
          • Cuando una VM se apaga, se cierra SU visor.
          • Cuando vuelves a una VM que ya tenía su visor abierto, no se
            relanza: el visor se queda como estaba.

        Anti-bucle: si el visor de ESTA VM murió hace <30 s, no se
        relanza por sí solo. El usuario puede forzar con el botón
        "Abrir en ventana externa".
        """
        if not self.current_vm_dir:
            return

        import time as _time
        if not hasattr(self, "_external_viewers"):
            self._external_viewers = {}

        vm_dir = self.current_vm_dir

        # --- Detener: cerrar SOLO el visor de esta VM ---
        if state != "running":
            entry = self._external_viewers.pop(vm_dir, None)
            if entry:
                p = entry.get("proc")
                try:
                    if p is not None and p.poll() is None:
                        p.terminate()
                except Exception:
                    pass
            return

        # --- Corriendo: decidir si hay que lanzar ---
        entry = self._external_viewers.get(vm_dir)
        if entry is not None:
            p = entry.get("proc")
            same_proto = entry.get("protocol") == protocol
            alive = p is not None and p.poll() is None

            # ¿Vivo y con el mismo protocolo? → no relanzar.
            if alive and same_proto:
                return

            # ¿Vivo pero con OTRO protocolo? → cerrar el viejo y relanzar.
            if alive and not same_proto:
                try:
                    p.terminate()
                except Exception:
                    pass
                self._external_viewers.pop(vm_dir, None)

            # ¿Muerto hace poco? → respetar ventana de gracia (30 s).
            elif not alive:
                last = entry.get("last_launch", 0.0)
                if _time.monotonic() - last < 30.0:
                    return
                self._external_viewers.pop(vm_dir, None)

        # --- Resolver sock / viewer / template ---
        _spice_port = None
        if protocol == PROTOCOL_SPICE:
            _spice_port = self._spice_port_from_runtime()
            if _spice_port is None:
                try:
                    self.vnc_label_status.setText("Iniciando SPICE… esperando puerto")
                    self.log_message("==> SPICE: aún no encuentro el puerto en run_temp.sh.")
                except Exception:
                    pass
                return
            sock = f"spice://127.0.0.1:{_spice_port}"
        else:
            sock = _cb_socket_path(vm_dir, protocol)
            if not os.path.exists(sock):
                try:
                    self.vnc_label_status.setText(
                        f"Iniciando {protocol.upper()}… esperando socket"
                    )
                    self.log_message(
                        f"==> {protocol.upper()}: aún no existe el socket {sock}."
                    )
                except Exception:
                    pass
                return

        viewer, template = find_viewer(protocol)
        if not viewer:
            try:
                self.vnc_label_status.setText(
                    f"{protocol.upper()} externo: instala un visor"
                )
                self.log_message(
                    f"[AVISO] {protocol.upper()} externo solicitado, pero no "
                    "hay visor instalado."
                )
            except Exception:
                pass
            return

        try:
            import subprocess as _sp
            uri = console_uri(protocol, sock)
            args = [viewer] + build_viewer_args(
                template, sock, uri, port=_spice_port
            )
            args += self._external_fullscreen_args(viewer)
            self.log_message(
                f"[DIAG] {protocol.upper()} externo: "
                f"viewer={viewer}, target={sock}, "
                f"args={' '.join(args)}"
            )
            proc = _sp.Popen(
                args, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                start_new_session=True,
                env=self._viewer_popen_env(),
            )
            self._register_external_viewer(vm_dir, proc, protocol)
            try:
                self.vnc_label_status.setText(
                    f"{protocol.upper()} en ventana externa "
                    f"({os.path.basename(viewer)})"
                )
                self.log_message(
                    f"==> {protocol.upper()}: visor externo lanzado: "
                    + " ".join(args)
                )
                self._focus_console_tab()
            except Exception:
                pass
        except Exception as e:
            try:
                self.log_message(f"[AVISO] {protocol.upper()} externo: {e}")
            except Exception:
                pass


    def _spice_port_from_runtime(self):
        """Extrae el puerto SPICE que QEMU está usando realmente.

        Lee run_temp.sh (el script que lanzó QEMU) y busca el argumento
        -spice port=NNNN. Es más fiable que adivinar: el puerto se eligió
        en el momento de construir los args y ahí quedó registrado.
        """
        if not self.current_vm_dir:
            return None
        run_sh = os.path.join(self.current_vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return None
        try:
            with open(run_sh, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return None
        m = re.search(r"-spice\s+port=(\d+)", content)
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    def _sync_spice_widget(self, state, mode):
        """Conecta SPICE embebido o lanza/mata el visor externo.

        Como ahora SPICE va por TCP local, no comprobamos la existencia de
        un archivo de socket: en su lugar leemos el puerto real desde
        run_temp.sh (que QEMU usa). Si no lo encontramos, esperamos.
        """
        if not hasattr(self, "vnc_placeholder"):
            return
        if getattr(self, "_console_tab_index", -1) < 0:
            return

        # --- Detener: matar visor y limpiar widget ---
        if state != "running":
            proc = getattr(self, "_external_viewer_proc", None)
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
                self._external_viewer_proc = None
            sw = getattr(self, "spice_widget", None)
            if sw is not None:
                try:
                    if hasattr(sw, "stop"):
                        sw.stop()
                    layout = self.console_page.layout()
                    if layout is not None:
                        layout.replaceWidget(sw, self.vnc_placeholder)
                    sw.deleteLater()
                except Exception:
                    pass
                self.spice_widget = None
                self._spice_widget_vm_dir = None
                try:
                    self.vnc_placeholder.show()
                    self.vnc_placeholder.setText("Esperando conexión de la VM…")
                    self.vnc_label_status.setText("La VM no está corriendo.")
                except Exception:
                    pass
            return

        # --- Corriendo ---
        if not self.current_vm_dir:
            return

        # Si el widget SPICE está conectado a OTRA VM, destruirlo.
        sw = getattr(self, "spice_widget", None)
        widget_vm = getattr(self, "_spice_widget_vm_dir", None)
        if sw is not None and widget_vm and widget_vm != self.current_vm_dir:
            try:
                self.log_message(
                    "==> SPICE: cambio de VM en la lista; reconectando la consola embebida."
                )
            except Exception:
                pass
            self._destroy_embedded_console_widget()

        port = self._spice_port_from_runtime()
        if port is None:
            try:
                self.vnc_label_status.setText("Iniciando SPICE… esperando puerto")
                self.log_message(
                    "==> SPICE: aún no encuentro el puerto en run_temp.sh."
                )
            except Exception:
                pass
            return

        if mode == MODE_EXTERNAL:
            self._sync_external_viewer(state, PROTOCOL_SPICE)
            return

        if getattr(self, "_spice_embed_disabled", False):
            self._sync_external_viewer(state, PROTOCOL_SPICE)
            return
        if getattr(self, "spice_widget", None) is not None:
            return

        try:
            _can_embed = bool(can_embed_spice())
        except Exception:
            _can_embed = False

        if not _can_embed:
            try:
                self.log_message(
                    "==> SPICE: no se puede embeber aquí "
                    "(Wayland o sin spice-gtk para Python); visor externo."
                )
            except Exception:
                pass
            self._spice_embed_disabled = True
            self._sync_external_viewer(state, PROTOCOL_SPICE)
            return

        if not _HAS_SPICE_WIDGET:
            self._spice_embed_disabled = True
            self._sync_external_viewer(state, PROTOCOL_SPICE)
            return

        try:
            self.spice_widget = SpiceConsoleWidget(
                parent=self.console_page,
                socket_path=f"spice://127.0.0.1:{port}",
                vm_name=os.path.basename(self.current_vm_dir),
                log_func=self.log_message,
            )
            try:
                self.spice_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
                )
            except Exception:
                pass
            try:
                self.spice_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            except Exception:
                pass
            layout = self.console_page.layout()
            if layout is not None:
                layout.replaceWidget(self.vnc_placeholder, self.spice_widget)
                self.vnc_placeholder.hide()
            self._spice_widget_vm_dir = self.current_vm_dir
            self.vnc_label_status.setText(f"SPICE: 127.0.0.1:{port}")
            self.log_message(f"==> SPICE: widget embebido (127.0.0.1:{port}).")
            self._focus_console_tab()
        except Exception as e:
            try:
                self.log_message(f"[AVISO] No se pudo crear el widget SPICE: {e}")
            except Exception:
                pass
            self.spice_widget = None
            self._spice_widget_vm_dir = None
            self._spice_embed_disabled = True
            self._sync_external_viewer(state, PROTOCOL_SPICE)


    def _setup_vnc_logging(self, force_debug=None):
        """Configura el nivel de log del cliente VNC embebido.

        Por defecto INFO. Antes se forzaba DEBUG en cada creación del
        widget, lo que escribía una línea por frame en launch.log (miles
        por segundo), consumía CPU y hacía ilegibles otros logs.

        El usuario puede activar DEBUG desde Configuración → Pantalla →
        "Log VNC detallado (DEBUG)" para diagnosticar un problema
        concreto. La elección se guarda en QSettings.

        `force_debug`: si no es None, se usa ese valor en vez de leer
        QSettings (lo usa el slot del checkbox).
        """
        import logging
        from PyQt6.QtCore import QSettings

        if force_debug is None:
            try:
                debug_on = bool(QSettings().value(
                    "console/vnc_debug_log", False, type=bool))
            except Exception:
                debug_on = False
        else:
            debug_on = bool(force_debug)

        # basicConfig solo si el root logger no tiene handlers todavía.
        # Reutilizar el que ya exista evita pisar el formato del log
        # general de la app (y duplicar líneas si se llamara dos veces).
        root = logging.getLogger()
        if not root.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            )

        level = logging.DEBUG if debug_on else logging.INFO
        for name in ("QVNCWidget", "rfb", "RFB", "vnc_widget",
                     "vnc_widget.rfb", "vnc_widget.qvncwidget"):
            try:
                logging.getLogger(name).setLevel(level)
            except Exception:
                continue
        return debug_on

    def _on_vnc_debug_log_toggled(self, checked):
        """Slot del checkbox 'Log VNC detallado' de Configuración → Pantalla."""
        from PyQt6.QtCore import QSettings
        QSettings().setValue("console/vnc_debug_log", bool(checked))
        try:
            self._setup_vnc_logging(force_debug=bool(checked))
        except Exception:
            pass
        try:
            self.log_message(
                "==> VNC: log detallado "
                + ("ACTIVADO (DEBUG; puede llenar launch.log)."
                   if checked else "desactivado (INFO).")
            )
        except Exception:
            pass

    def _sync_embedded_vnc(self, state):
        """Conecta/desconecta el widget VNC según el estado de la VM.

        NOTA: el filtro antiguo _NormalVNCKeyFilter fue eliminado porque
        llamaba a keyPressEvent() directamente, bypaseando el flujo normal
        de eventos de Qt y rompiendo el envío de teclas al guest. Ahora se
        usa VNCFocusKeyboardFilter, que captura el teclado correctamente
        (grabKeyboard + XGrabKeyboard) y deja que el widget reciba las
        teclas por su flujo normal.
        """
        if not hasattr(self, "vnc_widget") and not hasattr(self, "vnc_placeholder"):
            return
        if getattr(self, "_console_tab_index", -1) < 0:
            return

        vnc_connected = getattr(self, "vnc_widget", None) is not None

        # Si el widget está conectado a OTRA VM (el usuario cambió la
        # selección en la lista lateral), destruirlo: apunta al socket
        # de la VM anterior, no de la nueva.
        widget_vm = getattr(self, "_vnc_widget_vm_dir", None)
        if vnc_connected and widget_vm and widget_vm != self.current_vm_dir:
            try:
                self.log_message(
                    "==> VNC: cambio de VM en la lista; reconectando la consola embebida."
                )
            except Exception:
                pass
            self._destroy_embedded_console_widget()
            vnc_connected = False

        if state == "running" and not vnc_connected:
            socket_path = os.path.join(self.current_vm_dir, "qemu.vnc.sock") if self.current_vm_dir else ""
            if not socket_path or not os.path.exists(socket_path):
                try:
                    self.vnc_label_status.setText("Iniciando VNC… esperando socket")
                except Exception:
                    pass
                return
            try:
                from vnc_widget_centered import CenteredVNCWidget as QVNCWidget
                # Configurar el nivel de log del cliente VNC. Por defecto
                # INFO (antes era DEBUG y escribía una línea por frame en
                # launch.log, miles por segundo). El usuario puede activar
                # DEBUG desde Configuración → Pantalla → "Log VNC detallado".
                self._setup_vnc_logging()

                self.vnc_widget = QVNCWidget(
                    parent=self.console_page,
                    host=socket_path,
                    port=0,
                    password="",
                    readOnly=False,
                )
                from PyQt6.QtWidgets import QSizePolicy as _QSP, QScrollArea as _QScrollArea
                from PyQt6.QtCore import Qt as _Qt
                self.vnc_widget.setSizePolicy(_QSP.Policy.Expanding, _QSP.Policy.Expanding)
                self.vnc_widget.setMinimumSize(320, 240)
                self.vnc_widget.setFocusPolicy(_Qt.FocusPolicy.StrongFocus)
                # Forzar política de foco para que reciba eventos de teclado al
                # hacer clic, sin depender de que el usuario pulse Tab.
                self.vnc_widget.setAttribute(_Qt.WidgetAttribute.WA_InputMethodEnabled, False)

                self.vnc_scroll_area = _QScrollArea()
                self.vnc_scroll_area.setFrameShape(_QScrollArea.Shape.NoFrame)
                self.vnc_scroll_area.setWidget(self.vnc_widget)
                self._apply_vnc_display_mode()

                # Resetear el flag de auto-reconexión al crear un widget nuevo.
                try:
                    self.vnc_widget.start()
                    self.log_message(f"==> VNC: iniciando conexión al socket {os.path.basename(socket_path)}")
                except Exception as vnc_err:
                    self.log_message(f"[AVISO] No se pudo iniciar el cliente VNC: {vnc_err}")


                # Filtro de foco/captura de teclado (v2).
                try:
                    from vnc_focus_filter import VNCFocusKeyboardFilter
                    self._vnc_focus_filter = VNCFocusKeyboardFilter(self, self.vnc_widget)
                    self.vnc_widget.installEventFilter(self._vnc_focus_filter)
                except Exception as focus_err:
                    self.log_message(f"[AVISO] No se pudo instalar el filtro de foco del VNC: {focus_err}")

                # Watcher de resolución: detecta cambios del framebuffer del guest
                # (por ejemplo tras restaurar un snapshot con otra resolución)
                # y reajusta el modo de visualización del widget.
                try:
                    self._start_vnc_resize_watcher()
                except Exception as watcher_err:
                    self.log_message(
                        f"[AVISO] No se pudo iniciar el watcher de resolución VNC: {watcher_err}"
                    )

                from PyQt6.QtCore import QTimer as _QTimer
                # Damos foco tras un instante para que la ventana ya esté mapeada
                # y el XGrabKeyboard del filtro pueda aplicarse con éxito.
                _QTimer.singleShot(250, lambda w=self.vnc_widget: w.setFocus())

                # Reaplicar el modo de visualización varias veces durante
                # los primeros segundos, para atrapar los cambios de
                # resolución que hace el guest tras arrancar.
                try:
                    self._schedule_vnc_display_refresh()
                except Exception as _refresh_err:
                    self.log_message(
                        "[AVISO] No se pudo programar el refresco del VNC: "
                        + str(_refresh_err)
                    )
                if hasattr(self, "btn_vnc_fullscreen") and self.btn_vnc_fullscreen is not None:
                    self.btn_vnc_fullscreen.setEnabled(True)
                layout = self.console_page.layout()
                if layout is not None:
                    layout.replaceWidget(self.vnc_placeholder, self.vnc_scroll_area)
                    self.vnc_placeholder.hide()
                self._vnc_widget_vm_dir = self.current_vm_dir
                self.vnc_label_status.setText(f"Conectado a {os.path.basename(socket_path)}")
                self._focus_console_tab()
            except Exception as e:
                # Enviar el error completo a la Consola de Progreso para que
                # el usuario lo vea sin tener que mirar el terminal. Incluye
                # el traceback completo, que es lo único que permite
                # diagnosticar la causa real.
                try:
                    import traceback as _tb
                    tb = _tb.format_exc()
                    self.log_message(
                        f"[ERROR] No se pudo crear/conectar el widget VNC: {e}"
                    )
                    # Volcar el traceback línea por línea para que aparezca
                    # completo en la consola.
                    for line in tb.splitlines():
                        self.log_message("    " + line)
                except Exception as log_err:
                    # Último recurso: si log_message falla, escribirlo en stderr.
                    import sys as _sys
                    print(f"[VNC ERROR] {e}", file=_sys.stderr)
                    print(f"[VNC ERROR al loguear] {log_err}", file=_sys.stderr)
                # Mostrar un mensaje corto en la barra del widget.
                try:
                    self.vnc_label_status.setText(f"Error al conectar VNC: {e}")
                except Exception:
                    pass
                self.vnc_widget = None
                self._vnc_widget_vm_dir = None

        elif state == "stopped" and vnc_connected:
            try:
                # Desinstalar el filtro de foco ANTES de destruir el widget, para
                # que el X11 ungrab se ejecute y el teclado vuelva al host.
                focus_filter = getattr(self, "_vnc_focus_filter", None)
                if focus_filter is not None and self.vnc_widget is not None:
                    try:
                        focus_filter.detach()
                        self.vnc_widget.removeEventFilter(focus_filter)
                    except Exception:
                        pass
                self._vnc_focus_filter = None

                layout = self.console_page.layout()
                scroll_area = getattr(self, "vnc_scroll_area", None)
                if layout is not None and scroll_area is not None:
                    layout.replaceWidget(scroll_area, self.vnc_placeholder)
                if scroll_area is not None:
                    scroll_area.takeWidget()
                    scroll_area.deleteLater()
                self.vnc_widget.deleteLater()
            except Exception:
                pass
            if getattr(self, "_vnc_fullscreen_window", None) is not None:
                try:
                    self._close_vnc_fullscreen()
                except Exception:
                    pass
            self.vnc_widget = None
            self.vnc_scroll_area = None
            self._vnc_widget_vm_dir = None
            try:
                self.vnc_placeholder.show()
                self.vnc_placeholder.setText("Esperando conexión de la VM…")
                self.vnc_label_status.setText("La VM no está corriendo.")
                if hasattr(self, "btn_vnc_fullscreen") and self.btn_vnc_fullscreen is not None:
                    self.btn_vnc_fullscreen.setEnabled(False)
            except Exception:
                pass


    def _schedule_vnc_display_refresh(self):
        """Programa varias reaplicaciones del modo de visualización del VNC.

        Razon: durante el arranque del guest, la resolución del framebuffer
        cambia varias veces (framebuffer VNC inicial → boot del guest →
        resolución de usuario). Cada cambio puede dejar el widget con
        dimensiones temporales que hay que corregir. En vez de esperar al
        watcher periódico, disparamos varios refrescos concretos en los
        primeros segundos tras conectar.
        """
        from PyQt6.QtCore import QTimer as _QTimer
        # Delays en milisegundos. Los tres momentos cubren:
        #   400 ms  → primer handshake RFB
        #   1200 ms → guest arrancando
        #   2500 ms → guest a resolución final
        #   5000 ms → por si el guest tarda más en estabilizar
        for delay_ms in (400, 1200, 2500, 5000):
            _QTimer.singleShot(
                delay_ms,
                lambda: self._force_widget_relayout()
                if getattr(self, "vnc_widget", None) is not None else None,
            )

    # ------------------------------------------------------------------
    # Zoom del visor embebido (VNC dentro de la app)
    # ------------------------------------------------------------------
    # El widget VNC pinta el backbuffer escalado a SU PROPIO tamaño
    # (ver qvncwidget.paintEvent). Por eso el zoom se controla desde
    # aquí cambiando el tamaño fijo del widget y el widgetResizable del
    # QScrollArea, SIN tocar el widget ni el cliente RFB.
    #
    # Modos:
    #   • "fit"    → widget expansible + widgetResizable(True). La imagen
    #                se escala al viewport (comportamiento anterior al
    #                checkbox "Tamaño real").
    #   • "manual" → widget con tamaño fijo = vncWidth*pct/100 ×
    #                vncHeight*pct/100 y widgetResizable(False).
    #                Si no cabe, aparecen barras de desplazamiento.
    #
    # Persistencia en QSettings:
    #   console/vnc_zoom_mode    (str: "fit" | "manual")
    #   console/vnc_zoom_percent (int: 10..400)
    # El antiguo console/vnc_real_size se migra al arrancar.

    _VNC_ZOOM_LEVELS = (10, 25, 50, 75, 100, 125, 150, 200, 300, 400)
    _VNC_ZOOM_MIN = 10
    _VNC_ZOOM_MAX = 400

    def _migrate_vnc_zoom_settings(self):
        """Migra la preferencia antigua (bool) al nuevo esquema de zoom.

        Idempotente: si ya existe console/vnc_zoom_mode, no toca nada.
        """
        try:
            from PyQt6.QtCore import QSettings
        except Exception:
            return
        s = QSettings()
        if s.contains("console/vnc_zoom_mode"):
            return
        old = s.value("console/vnc_real_size", None)
        if old is None:
            s.setValue("console/vnc_zoom_mode", "fit")
            s.setValue("console/vnc_zoom_percent", 100)
        else:
            s.setValue("console/vnc_zoom_mode",
                       "manual" if bool(old) else "fit")
            s.setValue("console/vnc_zoom_percent", 100)
        # No borramos la clave antigua por si el usuario revierte el
        # parche; simplemente dejamos de leerla.

    def _vnc_zoom_state(self):
        """Devuelve (mode, percent). mode: 'fit' | 'manual'."""
        try:
            from PyQt6.QtCore import QSettings
        except Exception:
            return "fit", 100
        s = QSettings()
        mode = str(s.value("console/vnc_zoom_mode", "fit") or "fit")
        if mode not in ("fit", "manual"):
            mode = "fit"
        try:
            pct = int(s.value("console/vnc_zoom_percent", 100))
        except (TypeError, ValueError):
            pct = 100
        if pct < self._VNC_ZOOM_MIN or pct > self._VNC_ZOOM_MAX:
            pct = 100
        return mode, pct

    def _save_vnc_zoom_state(self, mode, percent):
        try:
            from PyQt6.QtCore import QSettings
        except Exception:
            return
        s = QSettings()
        s.setValue("console/vnc_zoom_mode", str(mode))
        try:
            s.setValue("console/vnc_zoom_percent", int(percent))
        except (TypeError, ValueError):
            s.setValue("console/vnc_zoom_percent", 100)

    def _vnc_zoom_label_text(self):
        mode, pct = self._vnc_zoom_state()
        if mode == "fit":
            return "Ajustado"
        return f"{pct}%"

    def _update_vnc_zoom_controls(self):
        """Refresca los widgets de zoom (label central y resaltados)."""
        lbl = getattr(self, "lbl_vnc_zoom_state", None)
        if lbl is not None:
            try:
                lbl.setText(self._vnc_zoom_label_text())
            except Exception:
                pass
        mode, pct = self._vnc_zoom_state()
        for name, active in (
            ("btn_vnc_zoom_fit", mode == "fit"),
            ("btn_vnc_zoom_real", mode == "manual" and pct == 100),
        ):
            btn = getattr(self, name, None)
            if btn is None:
                continue
            try:
                if active:
                    btn.setStyleSheet(
                        "QPushButton { background-color: #1976d2; color: white; "
                        "font-weight: bold; border: 1px solid #0d47a1; "
                        "border-radius: 6px; padding: 4px 8px; }"
                    )
                else:
                    btn.setStyleSheet("")
            except Exception:
                pass
        # Habilitar/deshabilitar las lupas en los extremos del rango.
        for name, enabled in (
            ("btn_vnc_zoom_out",
             mode == "manual" and pct > self._VNC_ZOOM_MIN),
            ("btn_vnc_zoom_in",
             mode == "manual" and pct < self._VNC_ZOOM_MAX),
        ):
            btn = getattr(self, name, None)
            if btn is None:
                continue
            try:
                btn.setEnabled(True)
            except Exception:
                pass

    def _schedule_zoom_resize(self):
        """Programa varias reaplicaciones del tamaño del widget de zoom.

        Qt puede tardar uno o más ciclos del bucle de eventos en propagar
        el cambio de tamaño al QScrollArea. Programamos tres reintentos
        cortos (0 / 50 / 150 ms) para que el cambio se vea sin tener que
        redimensionar la ventana a mano.
        """
        try:
            from PyQt6.QtCore import QTimer
        except Exception:
            return
        for delay in (0, 50, 150):
            QTimer.singleShot(delay, self._force_zoom_resize)

    def _force_zoom_resize(self):
        """Aplica el tamaño del widget de zoom y fuerza al QScrollArea a
        recomputar sus scrollbars.

        - setFixedSize deja el widget del tamaño exacto que pide el zoom.
        - updateGeometry() del widget avisa al padre de que cambió.
        - El QScrollArea, con widgetResizable(False), no siempre
          reacciona solo; se le postea un LayoutRequest explícito para
          forzarlo a recomputar el rango de scroll y repintar el
          viewport.
        """
        widget = getattr(self, "vnc_widget", None)
        scroll_area = getattr(self, "vnc_scroll_area", None)
        if widget is None or scroll_area is None:
            return
        mode, pct = self._vnc_zoom_state()
        if mode == "fit":
            return
        vw = int(getattr(widget, "vncWidth", 0) or 0)
        vh = int(getattr(widget, "vncHeight", 0) or 0)
        if vw <= 0 or vh <= 0:
            return
        tw = max(1, int(round(vw * pct / 100.0)))
        th = max(1, int(round(vh * pct / 100.0)))
        try:
            widget.setFixedSize(tw, th)
        except Exception:
            pass
        try:
            widget.updateGeometry()
        except Exception:
            pass
        try:
            scroll_area.updateGeometry()
            scroll_area.viewport().update()
        except Exception:
            pass
        try:
            from PyQt6.QtCore import QEvent
            from PyQt6.QtWidgets import QApplication
            QApplication.postEvent(
                scroll_area, QEvent(QEvent.Type.LayoutRequest)
            )
        except Exception:
            pass

        # Log solo cuando el tamaño aplicado cambia (evita spam).
        try:
            last = getattr(self, "_last_zoom_applied_size", None)
            if last != (tw, th):
                self._last_zoom_applied_size = (tw, th)
                self.log_message(f"[DIAG] zoom → setFixedSize({tw}x{th})")
        except Exception:
            pass

    def _on_vnc_zoom_in(self):
        mode, pct = self._vnc_zoom_state()
        if mode == "fit":
            new_pct = 100
        else:
            nxt = next((x for x in self._VNC_ZOOM_LEVELS if x > pct), None)
            new_pct = nxt if nxt is not None else self._VNC_ZOOM_LEVELS[-1]
        self._save_vnc_zoom_state("manual", new_pct)
        self._apply_vnc_display_mode()
        self._update_vnc_zoom_controls()
        self._schedule_zoom_resize()

    def _on_vnc_zoom_out(self):
        mode, pct = self._vnc_zoom_state()
        if mode == "fit":
            new_pct = 100
        else:
            prv = next(
                (x for x in reversed(self._VNC_ZOOM_LEVELS) if x < pct),
                None,
            )
            new_pct = prv if prv is not None else self._VNC_ZOOM_LEVELS[0]
        self._save_vnc_zoom_state("manual", new_pct)
        self._apply_vnc_display_mode()
        self._update_vnc_zoom_controls()
        self._schedule_zoom_resize()

    def _on_vnc_zoom_fit(self):
        mode, pct = self._vnc_zoom_state()
        self._save_vnc_zoom_state("fit", pct)
        self._apply_vnc_display_mode()
        self._update_vnc_zoom_controls()
        self._schedule_zoom_resize()

    def _on_vnc_zoom_real(self):
        self._save_vnc_zoom_state("manual", 100)
        self._apply_vnc_display_mode()
        self._update_vnc_zoom_controls()
        self._schedule_zoom_resize()

    def _apply_vnc_display_mode(self):
        """Aplica el modo de visualización del widget VNC.

        Defensivo: puede llamarse antes de que el widget haya
        completado el handshake RFB (vncWidth / vncHeight todavía no
        existen). En ese caso, si estamos en modo "manual" no fijamos
        tamaño (lo hará el watcher cuando llegue onInitialResize).
        En modo "fit" sí aplicamos las políticas expansibles desde ya.
        """
        widget = getattr(self, "vnc_widget", None)
        scroll_area = getattr(self, "vnc_scroll_area", None)
        if widget is None or scroll_area is None:
            return
        try:
            from PyQt6.QtCore import Qt as _Qt
            from PyQt6.QtWidgets import QSizePolicy as _QSP
        except Exception:
            return

        mode, pct = self._vnc_zoom_state()

        # 1) Política del QScrollArea ANTES de tocar el tamaño del
        #    widget. Si dejamos widgetResizable(True) mientras el widget
        #    intenta fijar su tamaño, el scroll area lo sobreescribe
        #    (estira el widget al viewport) y el zoom no se ve.
        if mode == "fit":
            try:
                scroll_area.setWidgetResizable(True)
                bar_policy = _Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                scroll_area.setHorizontalScrollBarPolicy(bar_policy)
                scroll_area.setVerticalScrollBarPolicy(bar_policy)
            except Exception:
                pass
        else:
            try:
                scroll_area.setWidgetResizable(False)
                bar_policy = _Qt.ScrollBarPolicy.ScrollBarAsNeeded
                scroll_area.setHorizontalScrollBarPolicy(bar_policy)
                scroll_area.setVerticalScrollBarPolicy(bar_policy)
            except Exception:
                pass

        # 2) Delegar el modo de pintado y el tamaño en el widget. El
        #    wrapper CenteredVNCWidget implementa set_zoom(percent_or_None):
        #      set_zoom(None)  → ajustar a ventana
        #      set_zoom(pct)   → tamaño fijo vncWidth*pct/100 × ...
        target_pct = None if mode == "fit" else pct
        handled_by_widget = False
        try:
            fn = getattr(widget, "set_zoom", None)
            if callable(fn):
                fn(target_pct)
                handled_by_widget = True
        except Exception:
            handled_by_widget = False

        if not handled_by_widget:
            # Fallback por si algún día se usa un widget sin set_zoom().
            try:
                fn = getattr(widget, "set_fit_to_window", None)
                if callable(fn):
                    fn(mode == "fit")
            except Exception:
                pass

        # 3) Red de seguridad: forzar resize() explícito. Hay widgets o
        #    combinaciones de layout en las que min/max solos no cambian
        #    el tamaño actual del widget dentro de un scroll area con
        #    widgetResizable(False); sin este resize, la llamada a
        #    set_zoom no se traduce en un cambio visual.
        if mode != "fit":
            try:
                vw = int(getattr(widget, "vncWidth", 0) or 0)
                vh = int(getattr(widget, "vncHeight", 0) or 0)
                if vw > 0 and vh > 0:
                    tw = max(1, int(round(vw * pct / 100.0)))
                    th = max(1, int(round(vh * pct / 100.0)))
                    widget.resize(tw, th)
            except Exception:
                pass

        try:
            scroll_area.viewport().update()
        except Exception:
            pass
        try:
            widget.updateGeometry()
            widget.update()
        except Exception:
            pass

        self._update_vnc_zoom_controls()

    def _update_usb_button_state(self, state):
        """Habilita los botones "💿 Medios" solo si hay VM y está encendida.

        Hay DOS botones que comparten el mismo menú (CD/DVD + USB):
          • btn_vm_usb         — pestaña Resumen, junto a Clonar / etc.
          • btn_vm_usb_console — barra superior de la Consola Gráfica.

        Con la VM apagada o sin VM seleccionada, el menú mostraría un
        mensaje poco útil; es mejor deshabilitar los dos a la vez.
        """
        enabled = self._vm_is_selected() and state in ("running", "paused")
        for attr in ("btn_vm_usb", "btn_vm_usb_console"):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                btn.setEnabled(enabled)
            except Exception:
                pass

    # ==================================================================
    # Watchdog de QEMU: detecta muerte inesperada y muestra el motivo
    # ==================================================================
    # refresh_vm_runtime_status corre cada 1.5 s. Aquí comparamos el
    # estado actual de cada VM con el guardado en _vm_last_state. Si una
    # VM pasó de running/paused a stopped, distinguimos dos casos:
    #
    #   1. El usuario apagó la VM → el trap EXIT de run_temp.sh borró
    #      qemu.pid. No hay nada que reportar.
    #   2. QEMU se cayó solo → el pid file sigue ahí pero el proceso ya
    #      no existe. Logueamos las últimas líneas de launch.log para
    #      que el usuario sepa qué pasó (falta de RAM, /dev/kvm ocupado,
    #      un dispositivo incompatible…).

    def _vm_last_log_lines(self, vm_dir, n=15):
        """Devuelve las últimas n líneas no vacías de launch.log, o []."""
        log_path = os.path.join(vm_dir, "launch.log")
        if not os.path.isfile(log_path):
            return []
        try:
            # Leemos solo el final: los logs pueden ser grandes.
            with open(log_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                # 8 KB es suficiente para ~50-100 líneas típicas.
                block = min(size, 8192)
                f.seek(size - block)
                raw = f.read().decode("utf-8", errors="replace")
            lines = [ln for ln in raw.splitlines() if ln.strip()]
            return lines[-n:]
        except Exception:
            return []

    def _watchdog_detect_death(self, vm_name):
        """True si esta VM murió de forma inesperada.

        Criterio: el estado anterior era running o paused, el actual es
        stopped, y qemu.pid sigue existiendo (el trap de QEMU no llegó a
        borrarlo porque el proceso no salió de forma ordenada).
        """
        prev = getattr(self, "_vm_last_state", {}).get(vm_name)
        if prev not in ("running", "paused"):
            return False
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
        pid_path = os.path.join(vm_dir, "qemu.pid")
        return os.path.isfile(pid_path)

    def _watchdog_report_death(self, vm_name):
        """Loguea el motivo probable de la muerte de QEMU.

        Además limpia el pid file (ya no sirve para nada) y marca la VM
        en la lista lateral para que el usuario la vea destacada.
        """
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
        try:
            self.log_message("")
            self.log_message(
                "=" * 62
            )
            self.log_message(
                f"[ERROR] La VM '{vm_name}' se detuvo de forma inesperada."
            )
            self.log_message(
                "        QEMU ya no está corriendo, pero dejó su pid file."
            )
            self.log_message(
                "        Últimas líneas de launch.log:"
            )
            for ln in self._vm_last_log_lines(vm_dir, n=15):
                self.log_message(f"        {ln}")
            self.log_message(
                "        Sugerencia: revisa el log completo con "
                "'Ver log completo'. Causas frecuentes: /dev/kvm ocupado, "
                "RAM insuficiente, un dispositivo incompatible, o error de "
                "configuración."
            )
            self.log_message("=" * 62)
            self.log_message("")
        except Exception:
            pass

        # Limpiar pid file muerto (ya no vale para nada).
        try:
            pid_path = os.path.join(vm_dir, "qemu.pid")
            if os.path.isfile(pid_path):
                os.remove(pid_path)
        except OSError:
            pass

        # Marcar la VM con ⚠️ en la lista hasta que el usuario la abra.
        try:
            self._vm_death_flag = getattr(self, "_vm_death_flag", set())
            self._vm_death_flag.add(vm_name)
        except Exception:
            pass

    def _watchdog_update_states(self):
        """Recorre todas las VMs, compara con el estado anterior y actúa.

        Se llama desde refresh_vm_runtime_status una vez por tick.
        """
        try:
            if not hasattr(self, "vm_list"):
                return
            if not hasattr(self, "_vm_last_state"):
                self._vm_last_state = {}

            for i in range(self.vm_list.count()):
                item = self.vm_list.item(i)
                if item is None:
                    continue
                name = self._vm_name_from_item(item)
                if not name:
                    continue
                state = self._runtime_state(name)
                prev = self._vm_last_state.get(name)

                # Detección de muerte inesperada.
                if (prev in ("running", "paused")
                        and state == "stopped"
                        and self._watchdog_detect_death(name)):
                    self._watchdog_report_death(name)

                # vm_history_v1 — E2: registrar el fin de sesión
                # en el historial cuando el watchdog detecta la
                # transición running/paused → stopped. El método
                # _history_on_transition decide el stop_reason:
                #   • acpi    → el usuario pulsó Apagar.
                #   • forced  → el usuario forzó apagado/reinicio.
                #   • crash   → pid huérfano detectado por el watchdog.
                #   • unknown → cualquier otro caso.
                try:
                    if hasattr(self, "_history_on_transition"):
                        self._history_on_transition(name, prev, state)
                except Exception as _h_err:
                    try:
                        self.log_message(
                            f"[AVISO] vm_history_v1: transición "
                            f"{prev}→{state} de '{name}' no registrada: "
                            f"{_h_err}"
                        )
                    except Exception:
                        pass

                self._vm_last_state[name] = state

            # Purgar entradas de VMs que ya no existen.
            known = set()
            for i in range(self.vm_list.count()):
                known.add(self._vm_name_from_item(self.vm_list.item(i)))
            for k in list(self._vm_last_state.keys()):
                if k not in known:
                    self._vm_last_state.pop(k, None)
        except Exception:
            pass

    # ==================================================================
    # Foco de la consola al seleccionar una VM
    # ==================================================================
    # Reglas:
    #   • VM apagada                    → pestaña Resumen.
    #   • VM corriendo + visor externo  → subir la ventana externa.
    #   • VM corriendo + embebida/etc.  → pestaña Consola Gráfica.

    def _focus_external_window_for_vm(self, vm_dir, vm_name):
        """Intenta subir la ventana del visor externo de esta VM.

        Estrategia:
          1. Por PID del Popen registrado en _external_viewers.
          2. Por WM_CLASS del visor (Spicy, Remote-viewer, Vncviewer...).
          3. Por título que contenga "spice", "vnc" o el nombre de la VM.

        Devuelve True si subió alguna ventana. Si todos los intentos
        fallan, hace un volcado de diagnóstico de `wmctrl` (una vez por
        sesión) para que el usuario pueda pegarlo en un reporte.
        """
        import shutil as _sh
        wmctrl = _sh.which("wmctrl")
        if not wmctrl:
            self._warn_wmctrl_once()
            return False

        # ---- 1) Por PID registrado ----
        entry = (getattr(self, "_external_viewers", {}) or {}).get(vm_dir)
        proc = (entry or {}).get("proc")
        if proc is not None and proc.poll() is None:
            if self._focus_window_by_pid(proc.pid):
                try:
                    self.log_message(
                        f"[DIAG] Visor externo de '{vm_name}': ventana subida por PID {proc.pid}."
                    )
                except Exception:
                    pass
                return True
            try:
                self.log_message(
                    f"[DIAG] Visor externo de '{vm_name}': wmctrl no encontró "
                    f"ventana para PID {proc.pid}; probando WM_CLASS y título."
                )
            except Exception:
                pass

        # ---- 2) Por WM_CLASS del visor ----
        classes_to_try = [
            # GTK-based (spicy, remote-viewer, gvncviewer)
            "Spicy", "spicy",
            "Remote-viewer", "remote-viewer", "remote_viewer",
            "Gvncviewer", "gvncviewer", "gtk-vnc", "gtk_vnc",
            "Vinagre", "vinagre",
            "Remmina", "remmina", "org.remmina.Remmina",
            # TigerVNC (FLTK)
            "Vncviewer", "vncviewer", "tigervnc", "TigerVNC",
            # Cualquier ventana cuyo título contenga 'vnc' o 'spice'
            # (el substring match por título cubre el resto).
        ]
        for cls in classes_to_try:
            if self._focus_window_by_class(cls):
                try:
                    self.log_message(
                        f"[DIAG] Visor externo de '{vm_name}': ventana subida "
                        f"por WM_CLASS '{cls}'."
                    )
                except Exception:
                    pass
                return True

        # ---- 3) Por título ----
        titles_to_try = ["spice", "vnc", vm_name]
        for title in titles_to_try:
            if title and self._focus_window_by_title_substr(title):
                try:
                    self.log_message(
                        f"[DIAG] Visor externo de '{vm_name}': ventana subida "
                        f"por título que contiene '{title}'."
                    )
                except Exception:
                    pass
                return True

        try:
            self.log_message(
                f"[DIAG] No se encontró ninguna ventana externa para '{vm_name}'."
            )
        except Exception:
            pass
        self._dump_wmctrl_once()
        return False

    def _focus_window_by_class(self, wm_class):
        """Sube la primera ventana cuyo WM_CLASS contenga `wm_class`."""
        import subprocess as _sp
        try:
            r = _sp.run(["wmctrl", "-lx"], capture_output=True, text=True, timeout=3)
        except Exception:
            return False
        if r.returncode != 0:
            return False
        needle = wm_class.lower()
        for line in r.stdout.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 4:
                continue
            wid = parts[0]
            wclass = parts[2].lower()
            if needle in wclass:
                try:
                    r2 = _sp.run(["wmctrl", "-i", "-a", wid],
                                 capture_output=True, text=True, timeout=3)
                    return r2.returncode == 0
                except Exception:
                    return False
        return False

    def _focus_window_by_title_substr(self, substr):
        """Sube la primera ventana cuyo título contenga `substr`."""
        import subprocess as _sp
        needle = (substr or "").lower()
        if not needle:
            return False
        try:
            r = _sp.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=3)
        except Exception:
            return False
        if r.returncode != 0:
            return False
        for line in r.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            wid = parts[0]
            title = parts[3].lower()
            if needle in title:
                try:
                    r2 = _sp.run(["wmctrl", "-i", "-a", wid],
                                 capture_output=True, text=True, timeout=3)
                    return r2.returncode == 0
                except Exception:
                    return False
        return False

    def _dump_wmctrl_once(self):
        """Vuelca wmctrl -lp y -lx al log UNA VEZ por sesión.

        Solo cuando todos los intentos de subir una ventana fallaron.
        Sirve para que el usuario pueda compartir la salida y diagnosticar
        por qué wmctrl no encuentra el visor externo.
        """
        if getattr(self, "_wmctrl_dumped", False):
            return
        self._wmctrl_dumped = True
        import subprocess as _sp
        for args in (["-lp"], ["-lx"]):
            try:
                r = _sp.run(["wmctrl"] + args, capture_output=True, text=True, timeout=3)
                try:
                    self.log_message(f"[DIAG] wmctrl {' '.join(args)} (rc={r.returncode}):")
                    for line in (r.stdout or "").splitlines():
                        self.log_message(f"        {line}")
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.log_message(f"[DIAG] wmctrl {' '.join(args)} falló: {e}")
                except Exception:
                    pass

    def _register_external_viewer(self, vm_dir, proc, protocol):
        """Registra un visor externo en self._external_viewers.

        Se llama desde dos sitios:
          • _sync_external_viewer (auto-lanzado al arrancar la VM).
          • _launch_external_console (botón "Abrir en ventana externa").
        """
        if not vm_dir or proc is None:
            return
        import time as _time
        if not hasattr(self, "_external_viewers"):
            self._external_viewers = {}
        self._external_viewers[vm_dir] = {
            "proc": proc,
            "protocol": protocol,
            "last_launch": _time.monotonic(),
        }

    def _focus_console_for_vm(self, vm_name, data=None):
        # Debounce: al hacer clic en la lista, currentTextChanged y
        # itemClicked disparan casi simultáneamente. Si ya enfocamos
        # esta VM hace < 400 ms, salimos (evita el doble [DIAG]).
        import time as _t_debounce
        now = _t_debounce.monotonic()
        key = (vm_name or "")
        last_key = getattr(self, "_focus_console_last_key", None)
        last_ts = getattr(self, "_focus_console_last_ts", 0.0)
        if key == last_key and (now - last_ts) < 0.4:
            return
        self._focus_console_last_key = key
        self._focus_console_last_ts = now
        """Aplica el foco correcto para la VM indicada.

        `vm_name` es el nombre de la carpeta (basename de current_vm_dir).
        `data` es el dict de load_vm_config, opcional (se recarga si None).

        Se llama desde open_vm() y desde el clic sobre la VM ya
        seleccionada. No se llama desde on_vm_list_changed directamente:
        open_vm ya lo hace.
        """
        if not vm_name:
            return
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
        if not os.path.isdir(vm_dir):
            return

        # Si no hay data, cargarla.
        if data is None:
            try:
                data = self._load_vm_config_cached(vm_dir)
            except Exception:
                data = {}

        state = self._runtime_state(vm_name)

        # --- VM apagada → Resumen ---
        if state not in ("running", "paused"):
            try:
                if hasattr(self, "main_tabs"):
                    self.main_tabs.setCurrentIndex(0)
            except Exception:
                pass
            return

        # --- VM encendida: ¿dónde se está mostrando? ---
        extra = (data or {}).get("extra") or {}
        protocol = str(extra.get("console_protocol") or "vnc").lower()
        mode = str(extra.get("console_mode") or "").lower()
        if not mode:
            mode = "embedded" if extra.get("vnc_embedded", True) else "native"

        # Modo externo: subir la ventana externa.
        if mode == "external":
            if self._focus_external_window_for_vm(vm_dir, vm_name):
                return  # conseguido
            # Si no se pudo subir ninguna ventana, caer al comportamiento
            # por defecto (pestaña Consola Gráfica como pista visual).
            try:
                idx = getattr(self, "_console_tab_index", -1)
                if idx >= 0 and hasattr(self, "main_tabs"):
                    self.main_tabs.setCurrentIndex(idx)
            except Exception:
                pass
            return

        # Modo nativo: QEMU tiene su propia ventana. Intentamos subirla.
        if mode == "native":
            pid_path = os.path.join(vm_dir, "qemu.pid")
            try:
                with open(pid_path, encoding="utf-8") as f:
                    pid = int(f.read().strip())
            except Exception:
                pid = None
            if pid is not None and self._focus_window_by_pid(pid):
                return
            # Fallback: dejar la pestaña como estaba. No hay consola embebida.
            return

        # Modo embedded o hybrid → pestaña Consola Gráfica.
        try:
            idx = getattr(self, "_console_tab_index", -1)
            if idx >= 0 and hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass

    def _focus_window_by_pid(self, pid):
        """Sube al frente la primera ventana que pertenece a `pid`.

        Usa `wmctrl -lp` para listar ventanas con su PID, encuentra la del
        PID buscado y la activa con `wmctrl -i -a <id>`. Funciona en X11
        y en Wayland a través de Xwayland para apps GTK (spicy,
        remote-viewer) y para la ventana de QEMU si es X11/Xwayland.

        Devuelve True si logró subir la ventana; False si no hay wmctrl,
        si no se encontró ninguna ventana con ese PID, o si falló el
        activate.
        """
        import shutil as _sh
        import subprocess as _sp
        wmctrl = _sh.which("wmctrl")
        if not wmctrl:
            return False
        try:
            r = _sp.run([wmctrl, "-lp"], capture_output=True, text=True, timeout=3)
        except Exception:
            return False
        if r.returncode != 0:
            return False
        target_wid = None
        for line in r.stdout.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 3:
                continue
            wid = parts[0]
            try:
                wpid = int(parts[2])
            except (ValueError, IndexError):
                continue
            if wpid == pid:
                target_wid = wid
                break
        if target_wid is None:
            return False
        try:
            r2 = _sp.run(
                [wmctrl, "-i", "-a", target_wid],
                capture_output=True, text=True, timeout=3,
            )
            return r2.returncode == 0
        except Exception:
            return False

    def _warn_wmctrl_once(self):
        """Avisa una sola vez que wmctrl falta, para no spamear la consola."""
        if getattr(self, "_wmctrl_warned", False):
            return
        self._wmctrl_warned = True
        try:
            self.log_message(
                "[AVISO] No se encontró 'wmctrl'. No es posible subir "
                "automáticamente la ventana del visor externo al "
                "seleccionar una VM en la lista. Instálalo con "
                "`sudo pacman -S wmctrl` (Arch) o `sudo apt install wmctrl` "
                "(Debian/Ubuntu). Mientras tanto, la app simplemente "
                "cambia a la pestaña Consola Gráfica."
            )
        except Exception:
            pass

    def _update_start_stop_buttons(self, state):
        """Habilita o deshabilita Iniciar / Pausar / Apagar según el estado.

        Reglas:
          • Sin VM seleccionada → los tres deshabilitados.
          • VM apagada          → solo Iniciar habilitado.
          • VM corriendo        → Pausar y Apagar habilitados.
          • VM pausada          → Pausar (reanudar) y Apagar habilitados.

        Se llama desde refresh_vm_runtime_status en cada tick (1.5 s) y
        también cuando se deselecciona la VM (current_vm_dir = None).
        """
        selected = self._vm_is_selected()
        running = state in ("running", "paused")
        stopped = selected and not running

        for attr, enabled in (
            ("btn_vm_start", stopped),
            ("btn_vm_pause", selected and running),
            ("btn_vm_poweroff", selected and running),
        ):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                btn.setEnabled(bool(enabled))
            except Exception:
                pass

    def refresh_vm_runtime_status(self):
        if not hasattr(self, "vm_list"):
            return
        # Watchdog: detecta muertes inesperadas de QEMU y limpia el
        # pid file huérfano. Debe correr ANTES del refresco de
        # etiquetas para que el ⚠️ de la lista use el estado nuevo.
        if hasattr(self, "_watchdog_update_states"):
            self._watchdog_update_states()

        for i in range(self.vm_list.count()):
            item = self.vm_list.item(i)
            name = self._vm_name_from_item(item)
            state = self._runtime_state(name)
            wanted = self._vm_list_label(name, state)
            if item.text() != wanted:
                item.setText(wanted)
        if self.current_vm_dir:
            name = os.path.basename(self.current_vm_dir)
            state = self._runtime_state(name)
            labels = {
                "running": (self.tr("● Ejecutándose"), "#2e7d32"),
                "paused": (self.tr("● Pausada"), "#f57c00"),
                "stopped": (self.tr("● Apagada"), "#757575"),
            }
            text, color = labels.get(state, labels["stopped"])
            self.vm_control_status.setText(text)
            self.vm_control_status.setStyleSheet(f"font-weight:bold; color:{color}; padding:4px;")
            self._set_vm_status("running" if state == "running" else "saved")
            # Refrescar el botón Pausar (texto y acciones del menú) según estado.
            if hasattr(self, "_update_pause_button_state"):
                self._update_pause_button_state(state)
            # Habilitar el botón USB solo cuando la VM está encendida.
            if hasattr(self, "_update_usb_button_state"):
                self._update_usb_button_state(state)
            # Botones Iniciar/Pausar/Apagar según estado.
            if hasattr(self, "_update_start_stop_buttons"):
                self._update_start_stop_buttons(state)
            # Botón "🧬 Desenlazar" (solo para clones enlazados apagados).
            if hasattr(self, "_update_linked_clone_buttons_state"):
                self._update_linked_clone_buttons_state(state)
            if hasattr(self, "manager_vm_title"):
                self._update_manager_details()
        if self.current_vm_dir:
            _vnc_state = self._runtime_state(os.path.basename(self.current_vm_dir))
            # Despachador: elige VNC o SPICE según la elección guardada
            # en la VM (extra.console_protocol / console_mode).
            if hasattr(self, "_sync_console_widget"):
                self._sync_console_widget(_vnc_state)
            elif hasattr(self, "_sync_embedded_vnc"):
                self._sync_embedded_vnc(_vnc_state)
        # Si no hay VM seleccionada, deshabilitar los botones de control.
        if not self.current_vm_dir and hasattr(self, "_update_start_stop_buttons"):
            self._update_start_stop_buttons("stopped")
        if hasattr(self, "_ensure_performance_monitoring"):
            self._ensure_performance_monitoring()
        if hasattr(self, "_refresh_suggestions"):
            self._refresh_suggestions()
        if hasattr(self, "_refresh_console_status_banner"):
            self._refresh_console_status_banner()
        # vm_history_v1 — E3a: refrescar el panel de historial
        # en cada tick (con caché por mtime, así no toca disco si
        # nada cambió).
        if hasattr(self, "_refresh_history_summary"):
            try:
                self._refresh_history_summary()
            except Exception:
                pass

    def control_start_vm(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Iniciar VM"), self.tr("Selecciona una máquina virtual."))
            return
        self.start_installation()

    def _update_pause_button_state(self, state):
        """Actualiza el texto y las acciones del botón Pausar según el estado.

        - running: "⏸ Pausar"; Pausar / Tomar Snapshot habilitadas.
        - paused:  "▶ Reanudar"; Pausar / Tomar Snapshot deshabilitadas.
        - stopped / otros: "⏸ Pausar"; Pausar / Tomar Snapshot deshabilitadas.

        IMPORTANTE: la acción "Reanudar" se deja SIEMPRE habilitada. El slot
        control_resume_vm decide si procede y, si no, informa al usuario. Así
        el menú nunca queda "muerto" cuando el estado detectado no es
        exactamente "paused" (por ejemplo justo después de un snapshot-save
        asíncrono o si el guest vuelve a "running" por su cuenta).

        Orden del menú: Pausar (rápido) → Reanudar → Tomar Snapshot.
        """
        btn = getattr(self, "btn_vm_pause", None)
        if btn is None:
            return
        if state == "paused":
            btn.setText(self.tr("▶ Reanudar"))
            btn.setToolTip(self.tr(
                "Reanudar la VM pausada. Usa la flecha para más opciones:\n"
                "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
                "• Reanudar: vuelve a ejecutar la VM.\n"
                "• Tomar Snapshot: guarda el estado a disco y pausa."
            ))
        else:
            btn.setText(self.tr("⏸ Pausar"))
            btn.setToolTip(self.tr(
                "Pausar la VM. Usa la flecha para más opciones:\n"
                "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
                "• Reanudar: vuelve a ejecutar la VM pausada.\n"
                "• Tomar Snapshot: guarda el estado a disco y pausa."
            ))
        # Pausar y Tomar Snapshot solo aplican si la VM está corriendo.
        for name in ("action_vm_pause", "action_vm_pause_save"):
            action = getattr(self, name, None)
            if action is not None:
                try:
                    action.setEnabled(state == "running")
                except Exception:
                    pass
        # Reanudar siempre habilitada: el slot decide si procede.
        a_resume = getattr(self, "action_vm_resume", None)
        if a_resume is not None:
            try:
                a_resume.setEnabled(True)
            except Exception:
                pass


    def control_pause_vm(self):
        """Control del botón Pausar (clic directo).

        Contexto:
          - Running → pausa simple (sin diálogo, rápido).
          - Pausada → reanuda.
          - Apagada → informa y no hace nada.
        Para 'Guardar estado y pausar' o 'Reanudar' explícitos usa el menú
        desplegable del botón.
        """
        if not self._vm_is_selected():
            return
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
            if state == "paused":
                self.control_resume_vm()
            elif state == "running":
                self.control_pause_vm_simple()
            else:
                QMessageBox.information(
                    self, self.tr("Pausar"),
                    self.tr("La máquina virtual no está corriendo."),
                )
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Control de VM"),
                self.tr("No se pudo cambiar el estado de la VM.\n\n{0}").format(e),
            )
            self.refresh_vm_runtime_status()

    def control_pause_vm_simple(self):
        """Pausa la VM sin guardar el estado en disco (rápido)."""
        if not self._vm_is_selected():
            return
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
            if state == "paused":
                return
            if state != "running":
                QMessageBox.information(self, self.tr("Pausar"), self.tr("La máquina virtual no está corriendo."))
                return
            self._qmp_hmp(self.current_vm_dir, "stop")
            self.log_message("==> VM pausada (sin guardar estado en disco).")
        except Exception as e:
            QMessageBox.warning(self, self.tr("Pausar"), self.tr("No se pudo pausar la VM.\n\n{0}").format(e))
        self.refresh_vm_runtime_status()

    def control_pause_vm_with_snapshot(self):
        """Pausa la VM guardando antes su estado (RAM + dispositivos) en un snapshot."""
        if not self._vm_is_selected():
            return
        self._pause_with_snapshot()

    def control_resume_vm(self):
        """Reanuda la ejecución de la VM pausada.

        Si el usuario pulsa 'Reanudar' cuando la VM no está pausada, se lo
        informamos sin fallar: así el menú puede dejar la acción siempre
        disponible sin que parezca rota.
        """
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Reanudar"), self.tr("Selecciona una máquina virtual."))
            return
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
            if state == "running":
                QMessageBox.information(
                    self, self.tr("Reanudar"),
                    self.tr("La máquina virtual ya está corriendo."),
                )
                return
            if state != "paused":
                QMessageBox.information(
                    self, self.tr("Reanudar"),
                    self.tr("La máquina virtual no está pausada: no hay nada que reanudar."),
                )
                return
            self._qmp_hmp(self.current_vm_dir, "cont")
            self.log_message("==> VM reanudada.")
        except Exception as e:
            QMessageBox.warning(self, self.tr("Reanudar"), self.tr("No se pudo reanudar la VM.\n\n{0}").format(e))
        self.refresh_vm_runtime_status()

    def _pause_with_snapshot(self):
        """Guarda el estado de la VM en un snapshot y luego la pausa.

        Se usa el worker de snapshots existente (SnapshotOperationWorker) para
        que la UI siga respondiendo mientras QEMU escribe la RAM a disco.
        """
        readiness = self._snapshot_readiness()
        if not readiness.get("state_disk"):
            QMessageBox.warning(
                self, "Guardar estado",
                "No se puede guardar el estado: no hay un QCOW2 escribible "
                "y no removible disponible.\n\n"
                + "\n".join(readiness.get("problems") or []),
            )
            return

        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        snap_name = "pause_" + time.strftime("%Y%m%d_%H%M%S")

        if state != "running":
            self._snapshot_log(
                "[SNAPSHOT] La VM no está corriendo; no hay estado en memoria "
                "que guardar. Se pausará igualmente."
            )
            try:
                self._qmp_hmp(self.current_vm_dir, "stop")
            except Exception:
                pass
            self.refresh_vm_runtime_status()
            return

        try:
            state_node, device_nodes = self._snapshot_qmp_nodes()
        except Exception as e:
            QMessageBox.warning(
                self, "Guardar estado",
                f"No se pudo preparar el snapshot.\n\n{e}",
            )
            return

        job_id = (
            "snap_pause_"
            + re.sub(r"[^A-Za-z0-9_.-]", "_", snap_name)[:40]
            + "_" + str(int(time.time()))
        )
        self._snapshot_log(
            f"[SNAPSHOT] Guardando estado '{snap_name}' antes de pausar la VM…"
        )
        self._snapshot_log(
            "[SNAPSHOT] Nota: QEMU puede congelar el guest mientras escribe la RAM."
        )
        # Captura de pantalla antes de lanzar el snapshot: es exactamente
        # el mismo paso que hace create_snapshot_from_page para que el
        # snapshot de pausa tenga miniatura como los demás.
        try:
            self._capture_snapshot_screenshot(snap_name)
        except Exception as shot_err:
            self._snapshot_log(
                f"[SNAPSHOT] ⚠ No se pudo guardar la captura de pantalla: {shot_err}"
            )
        self._start_snapshot_worker(
            self.current_vm_dir, "snapshot-save",
            {"job-id": job_id, "tag": snap_name,
             "vmstate": state_node, "devices": device_nodes},
            f"Guardando estado '{snap_name}'", snap_name, "pause",
        )


    def control_poweroff_vm(self):
        if not self._vm_is_selected(): return
        # vm_history_v1 — E2: marcar la intención (ACPI) para que el
        # watchdog clasifique el fin de sesión como "acpi" en vez de
        # "unknown" cuando detecte la transición running→stopped.
        try:
            if not hasattr(self, "_vm_stop_intent"):
                self._vm_stop_intent = {}
            _name = os.path.basename(self.current_vm_dir)
            self._vm_stop_intent[_name] = "acpi"
        except Exception:
            pass
        try:
            self._qmp_hmp(self.current_vm_dir, "system_powerdown")
        except Exception as e:
            QMessageBox.warning(self, self.tr("Apagar VM"), self.tr("No se pudo enviar la orden de apagado.\n\n{0}").format(e))
        self.refresh_vm_runtime_status()

    def control_reboot_vm(self):
        if not self._vm_is_selected(): return
        try:
            self._qmp_hmp(self.current_vm_dir, "system_reset")
        except Exception as e:
            QMessageBox.warning(self, self.tr("Reiniciar VM"), self.tr("No se pudo enviar la orden de reinicio.\n\n{0}").format(e))
        self.refresh_vm_runtime_status()

    def _confirm_force_action(self, title, message):
        resp = QMessageBox.warning(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return resp == QMessageBox.StandardButton.Yes

    def _kill_vm_process(self, vm_dir, timeout=5.0):
        pid_path, _ = self._runtime_paths(vm_dir)
        if not pid_path or not os.path.isfile(pid_path):
            return True
        try:
            with open(pid_path, encoding="utf-8") as f:
                pid = int(f.read().strip())
        except Exception:
            return True

        import signal
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return True
        except Exception as e:
            raise RuntimeError(f"No se pudo terminar el proceso de la VM (PID {pid}).\n\n{e}")

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.2)

        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return True
        except Exception as e:
            raise RuntimeError(f"No se pudo forzar la terminación del proceso de la VM (PID {pid}).\n\n{e}")
        return True

    def control_force_poweroff_vm(self):
        if not self._vm_is_selected(): return
        if not self._confirm_force_action(
            self.tr("Forzar apagado"),
            self.tr("Esto corta la VM de inmediato, sin avisar al sistema operativo invitado "
                    "(como desenchufar un equipo real).\n\n"
                    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
                    "¿Deseas continuar?"),
        ):
            return
        # vm_history_v1 — E2: marcar intención "forced".
        try:
            if not hasattr(self, "_vm_stop_intent"):
                self._vm_stop_intent = {}
            _name = os.path.basename(self.current_vm_dir)
            self._vm_stop_intent[_name] = "forced"
        except Exception:
            pass
        try:
            self._kill_vm_process(self.current_vm_dir)
        except Exception as e:
            QMessageBox.warning(self, "Forzar apagado", str(e))
        self.refresh_vm_runtime_status()

    def control_force_reboot_vm(self):
        if not self._vm_is_selected(): return
        if not self._confirm_force_action(
            self.tr("Forzar reinicio"),
            self.tr("Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin "
                    "avisar al sistema operativo invitado.\n\n"
                    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
                    "¿Deseas continuar?"),
        ):
            return
        # vm_history_v1 — E2: marcar intención "forced" + flag de
        # reinicio para que start_installation sepa que viene de aquí.
        try:
            if not hasattr(self, "_vm_stop_intent"):
                self._vm_stop_intent = {}
            _name = os.path.basename(self.current_vm_dir)
            self._vm_stop_intent[_name] = "forced"
            self._history_pending_reboot = True
        except Exception:
            pass
        try:
            self._kill_vm_process(self.current_vm_dir)
        except Exception as e:
            QMessageBox.warning(self, "Forzar reinicio", str(e))
            self.refresh_vm_runtime_status()
            return
        self.refresh_vm_runtime_status()
        from PyQt6.QtCore import QTimer as _QTimer
        _QTimer.singleShot(500, self.start_installation)

    def new_vm(self):
        self.current_vm_dir = None
        # config_tab_gating_v1: activar modo creación. La pestaña
        # "Configuración VM" queda habilitada aunque no haya VM.
        self._new_vm_mode = True
        # config_tab_gating_v2: en modo creación, el aviso breve de
        # macOS SÍ debe poder dispararse (es el contexto correcto).
        self._opening_vm = False
        self._macos_notice_shown_this_session = False
        self.input_vm_name.setEnabled(True)
        self.input_vm_name.clear()
        self.combo_firmware.setCurrentIndex(self.combo_firmware.findData("bios"))
        self.combo_chipset.setCurrentIndex(self.combo_chipset.findData("pc"))
        if hasattr(self, "combo_cpu_model"):
            self.combo_cpu_model.setCurrentIndex(self.combo_cpu_model.findData("auto"))
        self.check_secure_boot.setChecked(False)
        self.check_tpm.setChecked(False)
        if hasattr(self, "check_autostart_on_launch"):
            self.check_autostart_on_launch.blockSignals(True)
            self.check_autostart_on_launch.setChecked(False)
            self.check_autostart_on_launch.blockSignals(False)
        if hasattr(self, "check_snapshot_compat"):
            self.check_snapshot_compat.blockSignals(True)
            self.check_snapshot_compat.setChecked(False)
            self.check_snapshot_compat.blockSignals(False)
        try:
            self._refresh_snapshot_compat_ui_on_os_change()
        except Exception:
            pass
        self._save_boot_order(["cdrom","disk","network"]) if self.current_vm_dir else None
        self.combo_network.setCurrentIndex(self.combo_network.findData("virtio-net-pci"))
        self.combo_network_mode.setCurrentIndex(self.combo_network_mode.findData("nat"))
        self.combo_network_count.setCurrentIndex(self.combo_network_count.findData(1))
        self.combo_audio.setCurrentIndex(self.combo_audio.findData("intel-hda"))
        self.combo_graphics.setCurrentIndex(self.combo_graphics.findData("auto"))
        self.combo_graphics_vram.setCurrentIndex(self.combo_graphics_vram.findData("256M"))
        if hasattr(self, "check_serial_to_file"):
            self.check_serial_to_file.blockSignals(True)
            self.check_serial_to_file.setChecked(False)
            self.check_serial_to_file.blockSignals(False)
        self.update_network_options()
        self.refresh_network_devices_ui()
        self._passthrough_saved=[]
        self.refresh_passthrough_tree()
        self.input_vm_name.setFocus()
        self._set_vm_status("new")
        self._update_vm_summary()
        self.refresh_boot_order_choices()
        self.log_message("==> Formulario listo para una nueva máquina virtual.")
        if hasattr(self, "main_tabs"):
            self.main_tabs.setCurrentIndex(1)
        if hasattr(self, "manager_vm_title"):
            self._update_manager_details()
        # vm_history_v1 — E3a: limpiar el panel de historial en una VM nueva.
        if hasattr(self, "_refresh_history_summary"):
            try:
                self._refresh_history_summary()
            except Exception:
                pass
        # config_tab_gating_v1: habilitar la pestaña "Configuración VM".
        try:
            self._update_config_tab_gating()
        except Exception:
            pass
        # vm_config_save_cancel_v1_dirty: en modo creación no hay
        # .ini con el que comparar. Los botones quedan deshabilitados
        # (no hay "cambios pendientes" respecto a nada).
        try:
            self._update_config_dirty_state()
        except Exception:
            pass

    def apply_windows11_defaults(self, *args):
        if self.combo_main_os.currentData() != "windows":
            return
        is_win11 = self.combo_win_ver.currentText() == "Windows 11"
        if is_win11:
            idx = self.combo_firmware.findData("uefi")
            if idx >= 0:
                self.combo_firmware.setCurrentIndex(idx)
            self.check_secure_boot.setChecked(True)
            self.check_tpm.setChecked(True)
        else:
            self.check_secure_boot.setChecked(self.combo_firmware.currentData() == "uefi" and self.check_secure_boot.isChecked())
            self.check_tpm.setChecked(self.combo_firmware.currentData() == "uefi" and self.check_tpm.isChecked())
        legacy = self.combo_win_ver.currentText() not in ("Windows 10", "Windows 11")
        if hasattr(self, "check_win_auto"):
            self.check_win_auto.setEnabled(not legacy)
            if legacy:
                self.check_win_auto.setChecked(False)
        self.update_firmware_options_visibility()

    def open_vm(self, vm_name: str):
        # config_tab_gating_v2: marcar apertura de VM. Sirve para
        # que el aviso breve de macOS no se dispare al abrir una
        # VM existente (solo al crear una nueva).
        self._opening_vm = True
        self._macos_notice_shown_this_session = True
        try:
            vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_name)
            try:
                data = self._load_vm_config_cached(vm_dir)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo leer la configuración de '{vm_name}': {e}")
                return

            # macos_storage_cleanup_v1: en macOS, los archivos del bloque
            # fijo de OSX-KVM (BaseSystem.img, mac_hdd_ng.qcow2, OpenCore.qcow2)
            # NO deben estar registrados como discos SATA/NVMe del usuario.
            # Si una version antigua los dejo ahi, QEMU intentaria abrirlos
            # por segunda vez (junto al bloque fijo del script) y fallaria
            # con "Failed to get write lock". Se purgan aqui, antes de que
            # workers.py lea la configuracion.
            try:
                _os_type = (data.get("os_type") or "").lower()
                if _os_type == "macos":
                    _extra = data.get("extra") or {}
                    _devices = _extra.get("storage_devices") or []
                    if isinstance(_devices, list) and _devices:
                        _reserved_names = {
                            "basesystem.img",
                            "mac_hdd_ng.qcow2",
                            "opencore.qcow2",
                        }
                        _kept = []
                        _removed = []
                        for _d in _devices:
                            if not isinstance(_d, dict):
                                _kept.append(_d)
                                continue
                            _kind = str(_d.get("device") or "")
                            _p = str(_d.get("path") or "")
                            _base = os.path.basename(_p).lower() if _p else ""
                            if _kind in ("sata", "nvme", "floppy") and _base in _reserved_names:
                                _removed.append(_d)
                            else:
                                _kept.append(_d)
                        if _removed:
                            _cfg_path = os.path.join(vm_dir, "vm_config.ini")
                            if os.path.isfile(_cfg_path):
                                import configparser as _cfgmod
                                _c = _cfgmod.ConfigParser(interpolation=None)
                                _c.read(_cfg_path, encoding="utf-8")
                                if not _c.has_section("extra"):
                                    _c.add_section("extra")
                                try:
                                    _extra_data = json.loads(_c["extra"].get("data", "{}"))
                                except Exception:
                                    _extra_data = {}
                                _extra_data["storage_devices"] = _kept
                                _c.set("extra", "data", json.dumps(_extra_data, ensure_ascii=False))
                                with open(_cfg_path, "w", encoding="utf-8") as _fh:
                                    _c.write(_fh)
                                if hasattr(self, "_invalidate_vm_config_cache"):
                                    self._invalidate_vm_config_cache(vm_dir)
                                _names = [
                                    os.path.basename(str(_d.get("path") or ""))
                                    for _d in _removed
                                ]
                                self.log_message(
                                    "==> macOS: purgadas "
                                    + str(len(_removed))
                                    + " entrada(s) reservada(s) de storage_devices: "
                                    + ", ".join(_names)
                                )
            except Exception as _clean_err:
                try:
                    self.log_message(
                        "[AVISO] macOS: no se pudo purgar storage_devices: "
                        + str(_clean_err)
                    )
                except Exception:
                    pass

            # linux_installer_cleanup_v1: si la VM es Linux y su distro no
            # tiene descarga automatica, cualquier unidad CD/DVD con
            # source="installer" pendiente se convierte en vacia. Esto
            # limpia VMs que se configuraron antes del fix (o que vinieron
            # de un import) y evita que QEMU reciba "Auto-deteccion no
            # soportada para: <distro>" al arrancar.
            try:
                _os_type_l = (data.get("os_type") or "").lower()
                if _os_type_l == "linux":
                    _extra_l = data.get("extra") or {}
                    _distro_l = (_extra_l.get("distro") or "").strip()
                    _needs_cleanup = False
                    if _distro_l:
                        try:
                            import iso_versions as _iv_l
                            _needs_cleanup = not _iv_l.supports_auto_download(_distro_l)
                        except Exception:
                            _needs_cleanup = False
                    else:
                        _needs_cleanup = True  # sin distro conocida: limpiar por si acaso
                    if _needs_cleanup:
                        _devs_l = _extra_l.get("storage_devices") or []
                        _kept_l = []
                        _removed_l = []
                        for _d_l in _devs_l:
                            if not isinstance(_d_l, dict):
                                _kept_l.append(_d_l)
                                continue
                            if (_d_l.get("device") == "cdrom"
                                    and _d_l.get("source") == "installer"
                                    and not (_d_l.get("path") or "")):
                                _d_l.pop("source", None)
                                _removed_l.append(_d_l.get("name") or "CD/DVD")
                            _kept_l.append(_d_l)
                        if _removed_l:
                            _cfg_path_l = os.path.join(vm_dir, "vm_config.ini")
                            if os.path.isfile(_cfg_path_l):
                                import configparser as _cfg_l
                                _c_l = _cfg_l.ConfigParser(interpolation=None)
                                _c_l.read(_cfg_path_l, encoding="utf-8")
                                if not _c_l.has_section("extra"):
                                    _c_l.add_section("extra")
                                try:
                                    _ex_l = json.loads(_c_l["extra"].get("data", "{}"))
                                except Exception:
                                    _ex_l = {}
                                _ex_l["storage_devices"] = _kept_l
                                _c_l.set("extra", "data", json.dumps(_ex_l, ensure_ascii=False))
                                with open(_cfg_path_l, "w", encoding="utf-8") as _fh_l:
                                    _c_l.write(_fh_l)
                                if hasattr(self, "_invalidate_vm_config_cache"):
                                    self._invalidate_vm_config_cache(vm_dir)
                                self.log_message(
                                    "==> Linux: convertidas a vacias "
                                    + str(len(_removed_l))
                                    + " unidad(es) CD/DVD con descarga "
                                    "automatica no soportada: "
                                    + ", ".join(_removed_l)
                                )
            except Exception as _clean_l_err:
                try:
                    self.log_message(
                        "[AVISO] Linux: no se pudo limpiar el source=\"installer\": "
                        + str(_clean_l_err)
                    )
                except Exception:
                    pass

            self.current_vm_dir = vm_dir
            # config_tab_gating_v1: al abrir una VM salimos del modo
            # creación y habilitamos la pestaña "Configuración VM".
            self._new_vm_mode = False
            # El usuario abrió la VM: se considera atendida la alerta de
            # muerte inesperada del watchdog.
            if hasattr(self, "_vm_death_flag"):
                self._vm_death_flag.discard(vm_name)
            # linked_clone_behavior_fix_v1: avisar si el original de este
            # clon enlazado está corriendo (evitado durante auto-arranque).
            if not getattr(self, "_auto_starting", False):
                try:
                    self._check_linked_clone_original_running(vm_dir, data)
                except Exception:
                    pass
                # linked_clone_broken_detection_v1: si el backing del clon ya no
                # existe (típico al mover solo la carpeta del clon), avisar antes
                # de que QEMU falle con un error críptico.
                try:
                    self._check_linked_clone_backing_intact(vm_dir, data)
                except Exception:
                    pass
            self.input_vm_name.setText(data["name"] or vm_name)
            # vm_config_save_cancel_v1_dirty: permitir editar el
            # nombre. Al pulsar "Guardar" se actualiza general/name
            # del .ini. La CARPETA no se renombra.
            self.input_vm_name.setEnabled(True)
            if hasattr(self, "main_tabs"):
                self.main_tabs.setCurrentIndex(0)

            idx = self.combo_main_os.findData(data["os_type"])
            if idx >= 0:
                self.combo_main_os.setCurrentIndex(idx)

            try:
                ram_text = str(data.get("ram", "4G")).upper().replace("GB", "G").replace(" ", "")
                ram_val = int(re.match(r"(\d+)", ram_text).group(1)) if re.match(r"(\d+)", ram_text) else 4
                ram_val = max(self.slider_ram.minimum(), min(self.slider_ram.maximum(), (ram_val // 2) * 2))
                self.slider_ram.setValue(ram_val)
            except Exception:
                pass

            try:
                core_val = int(data.get("cores", 2))
                core_val = max(self.slider_cores.minimum(), min(self.slider_cores.maximum(), (core_val // 2) * 2))
                self.slider_cores.setValue(core_val)
            except (TypeError, ValueError):
                pass

            firmware_idx = self.combo_firmware.findData(data.get("firmware", "bios"))
            if firmware_idx >= 0:
                self.combo_firmware.setCurrentIndex(firmware_idx)
            chipset_idx = self.combo_chipset.findData(data.get("chipset", "pc"))
            if chipset_idx >= 0:
                self.combo_chipset.setCurrentIndex(chipset_idx)
            if hasattr(self, "combo_cpu_model"):
                cpu_model = (data.get("extra") or {}).get("cpu_model", "auto")
                cpu_idx = self.combo_cpu_model.findData(cpu_model)
                if cpu_idx < 0:
                    cpu_idx = self.combo_cpu_model.findData("auto")
                if cpu_idx >= 0:
                    self.combo_cpu_model.setCurrentIndex(cpu_idx)
            self.check_secure_boot.setChecked(bool(data.get("secure_boot", False)))
            self.check_tpm.setChecked(bool(data.get("tpm", False)))
            # Sincronizar el checkbox de auto-inicio con lo guardado en
            # extra["autostart_on_launch"] (blockSignals: no queremos que
            # el simple hecho de abrir la VM reescriba el .ini).
            if hasattr(self, "check_autostart_on_launch"):
                _as = bool((data.get("extra") or {}).get("autostart_on_launch", False))
                self.check_autostart_on_launch.blockSignals(True)
                self.check_autostart_on_launch.setChecked(_as)
                self.check_autostart_on_launch.blockSignals(False)
            self.update_firmware_options_visibility()
            self.refresh_boot_order_choices()
            mode_idx = self.combo_network_mode.findData(data.get("network_mode", "nat"))
            if mode_idx >= 0:
                self.combo_network_mode.setCurrentIndex(mode_idx)
            net_idx = self.combo_network.findData(data.get("network_model", "virtio-net-pci"))
            if net_idx >= 0:
                self.combo_network.setCurrentIndex(net_idx)
            count_idx = self.combo_network_count.findData(int(data.get("network_count", 1)))
            if count_idx >= 0:
                self.combo_network_count.setCurrentIndex(count_idx)
            self.update_network_options(data.get("network_interface", ""))
            audio_idx = self.combo_audio.findData(data.get("audio_device", "intel-hda"))
            if audio_idx >= 0:
                self.combo_audio.setCurrentIndex(audio_idx)
            if hasattr(self, "combo_pointer"):
                _ptr = (data.get("extra") or {}).get("pointer_device") or "auto"
                _ptr_idx = self.combo_pointer.findData(_ptr)
                if _ptr_idx < 0:
                    _ptr_idx = 0
                self.combo_pointer.blockSignals(True)
                self.combo_pointer.setCurrentIndex(_ptr_idx)
                self.combo_pointer.blockSignals(False)
            if hasattr(self, "check_serial_to_file"):
                _ser = bool((data.get("extra") or {}).get("serial_to_file", False))
                self.check_serial_to_file.blockSignals(True)
                self.check_serial_to_file.setChecked(_ser)
                self.check_serial_to_file.blockSignals(False)
            graphics_idx = self.combo_graphics.findData(data.get("graphics_mode", "auto"))
            if graphics_idx >= 0:
                self.combo_graphics.setCurrentIndex(graphics_idx)
            graphics_vram_idx = self.combo_graphics_vram.findData(data.get("graphics_vram", "256M"))
            if graphics_vram_idx >= 0:
                self.combo_graphics_vram.setCurrentIndex(graphics_vram_idx)
            # La elección de consola se aplica más abajo con
            # _apply_console_choice_from_vm(data). Ese método llama a
            # _on_vnc_embedded_changed() al final, así que no duplicamos aquí.
            self.update_graphics_options()
            _nets = data.get("network_devices") or []
            self.refresh_network_devices_ui(_nets)
            if hasattr(self, "check_no_network"):
                self.check_no_network.setChecked(len(_nets) == 0)
            self._passthrough_saved=list(data.get("passthrough_devices") or [])
            self.refresh_passthrough_tree()

            self.disk_size_setting = data.get("disk_size") or "128G"
            self.disk_type_setting = data.get("disk_type") or "dynamic"
            self.disk_format_setting = data.get("disk_format") or "qcow2"
            self.disk_ext_setting = data.get("disk_ext") or ("img" if self.disk_format_setting == "raw" else self.disk_format_setting)

            # Volcar la elección de consola guardada en la VM a los combos.
            # Sin esto, los combos conservaban el valor del VM anterior.
            self._apply_console_choice_from_vm(data)

            extra = data["extra"] or {}
            if data["os_type"] == "macos":
                for i, (_, val) in enumerate(self.os_options):
                    if val == extra.get("os_choice"):
                        self.combo_macos_ver.setCurrentIndex(i)
                        break
                # La fuente de instalación se lee desde la unidad CD/DVD
                # "Principal" en Almacenamiento. No hay widgets en la parte
                # superior que actualizar (se eliminaron por duplicación).
            elif data["os_type"] == "windows":
                win_idx = self.combo_win_ver.findText(extra.get("win_ver", "Windows 11"))
                if win_idx >= 0:
                    self.combo_win_ver.setCurrentIndex(win_idx)
                self.check_win_auto.setChecked(bool(extra.get("auto_detect", False)))
                if not extra.get("auto_detect"):
                    # portable_paths_v1: resolver ruta guardada (relativa) a
                    # absoluta para mostrarla en el input y que os.path.isfile
                    # funcione al arrancar.
                    _stored_iso = extra.get("iso_path", "") or ""
                    _abs_iso = vm_paths.to_absolute(vm_dir, _stored_iso) if _stored_iso else ""
                    self.input_win_iso.setText(_abs_iso)
            elif data["os_type"] == "android":
                # La fuente de instalación se lee desde la unidad CD/DVD
                # "Principal" en Almacenamiento. No hay widget en la parte
                # superior que actualizar (se eliminó por duplicación).
                pass
            else:
                lin_idx = self.combo_lin_distro.findText(extra.get("distro", ""))
                if lin_idx >= 0:
                    self.combo_lin_distro.setCurrentIndex(lin_idx)
                # Restaurar la elección de ISO guardada ('Más reciente', una versión
                # concreta, o 'Ninguna' si el usuario aportó su propia imagen). La
                # unidad manda sobre lo guardado en 'extra' cuando difieren.
                _lin_devices = self._storage_devices_all(vm_dir)
                _lin_choice, _ = principal_cdrom.derive_choice(extra, _lin_devices, "linux")
                self._refresh_lin_versions(select=_lin_choice)

            # Restaurar el flag de modo compatibilidad de snapshots antes
            # de tocar la UI, para que _refresh_snapshot_compat_ui_on_os_change
            # lea el estado correcto.
            if hasattr(self, "check_snapshot_compat"):
                try:
                    _sc = bool((data.get("extra") or {}).get("snapshot_compat", False))
                    self.check_snapshot_compat.blockSignals(True)
                    self.check_snapshot_compat.setChecked(_sc)
                    self.check_snapshot_compat.blockSignals(False)
                except Exception:
                    pass
            try:
                self._refresh_snapshot_compat_ui_on_os_change()
            except Exception:
                pass

            # Cargar la programacion de snapshots automaticos en la UI.
            try:
                self._load_snapshot_schedule_to_ui(data)
            except Exception:
                pass
            # Cargar la programacion de backups automaticos en la UI.
            try:
                self._load_backup_schedule_to_ui(data)
            except Exception:
                pass

            self._set_vm_status("saved")
            self.refresh_shared_folders_ui()
            self._update_vm_summary()
            # Refrescar la miniatura del último snapshot al abrir una VM.
            if hasattr(self, "_refresh_last_snapshot_thumbnail"):
                self._refresh_last_snapshot_thumbnail()
            self.log_message(f"==> Configuración de '{vm_name}' cargada desde {vm_dir}")
            # Refrescar los botones inmediatamente sin esperar al timer.
            if hasattr(self, "_update_start_stop_buttons"):
                try:
                    self._update_start_stop_buttons(self._runtime_state(vm_name))
                except Exception:
                    pass
            # Aplicar el foco correcto (Resumen, Consola Gráfica o
            # visor externo según el estado y el modo de la VM).
            if hasattr(self, "_focus_console_for_vm"):
                try:
                    self._focus_console_for_vm(vm_name, data)
                except Exception:
                    pass
            # vm_history_v1 — E3a: refrescar el panel de historial al
            # abrir una VM (para que no se vea el de la VM anterior).
            if hasattr(self, "_refresh_history_summary"):
                try:
                    self._refresh_history_summary()
                except Exception:
                    pass

        finally:
            # config_tab_gating_v2: limpiar el flag y aplicar el
            # gating SIEMPRE, aunque el cuerpo de open_vm falle.
            self._opening_vm = False
            try:
                self._update_config_tab_gating()
            except Exception:
                pass
            # vm_config_save_cancel_v1_dirty: al abrir una VM el
            # estado base es el del .ini, así que no hay cambios
            # pendientes. Actualizar botones.
            try:
                self._update_config_dirty_state()
            except Exception:
                pass
    def maybe_autofill_vm_name(self, *args):
        if self.input_vm_name.text().strip():
            return
        os_type = self.combo_main_os.currentData()
        if os_type == "macos":
            name = self.os_options[self.combo_macos_ver.currentIndex()][0]
        elif os_type == "windows":
            name = self.combo_win_ver.currentText()
        elif os_type == "android":
            name = "Android"
        else:
            name = self.combo_lin_distro.currentText()
        self.input_vm_name.setText(name)

    def toggle_mac_iso_mode(self, checked):
        """Activa/desactiva el modo "imagen existente" de macOS.

        checked=True  → Recovery (descarga automática): oculta el input.
        checked=False → Imagen existente: muestra el input y el botón.
        """
        use_custom = not checked
        for w in (getattr(self, "input_mac_custom_iso", None),
                  getattr(self, "btn_mac_browse", None)):
            if w is None:
                continue
            w.setEnabled(use_custom)
            w.setVisible(use_custom)

    def toggle_win_iso_mode(self, checked):
        self.input_win_iso.setEnabled(not checked)
        if checked:
            self.input_win_iso.clear()
            self.input_win_iso.setPlaceholderText("Se detectará y descargará automáticamente")
        else:
            self.input_win_iso.setPlaceholderText("/ruta/a/windows.iso")

    def toggle_iso_mode(self, *args):
        return

    def browse_iso(self, line_edit_target):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo ISO", "", "Archivos ISO (*.iso);;Todos los archivos (*)")
        if file_name:
            line_edit_target.setText(file_name)

    def _auto_graphics_effective_label(self):
        """Devuelve (mode_id, texto_corto) que elegiría "Automático" AHORA.

        Tiene en cuenta:
          • El SO invitado (Windows usa VGA estándar; macOS usa VGA OSX-KVM).
          • Si VNC embebido está activo (VNC no soporta OpenGL → VirtIO-GPU 2D
            o VGA estándar).
          • Las capacidades del host (OpenGL, VirGL, soporte de QEMU).
        """
        try:
            os_type = self.combo_main_os.currentData() or "linux"
        except Exception:
            os_type = "linux"

        if os_type == "windows":
            return "std", "VGA estándar (QEMU -vga std)"
        if os_type == "macos":
            return "vga-macos", "VGA de OSX-KVM (VGA virtual)"
        if os_type == "android":
            # Android-x86 9.0 (kernel 4.9) no tiene driver VirtIO-GPU y
            # cae a un shell de rescate. QXL 2D es lo que
            # workers._graphics_args() elige para "auto" en Android.
            # El aviso al usuario si elige VirtIO-GPU a mano está en
            # _update_graphics_compat_hint.
            return "qxl", "Android: Red Hat QXL 2D (recomendado)"

        # ¿VNC embebido activo? → 3D prohibido.
        try:
            _proto, _mode = self._current_console_choice()
            vnc_embedded = (_proto == "vnc" and _mode in ("embedded", "hybrid"))
        except Exception:
            vnc_embedded = False

        # Capacidades del host (con caché dentro de host_deps).
        try:
            _qcaps = qemu_graphics_capabilities()
            qemu_virtio = bool(_qcaps.get("virtio"))
            qemu_virgl = bool(_qcaps.get("virgl"))
            display_gl_ok = bool(_qcaps.get("display_gl"))
        except Exception:
            qemu_virtio = qemu_virgl = display_gl_ok = False

        if vnc_embedded:
            if qemu_virtio:
                return "virtio", "VirtIO-GPU 2D (VNC no soporta 3D)"
            return "std", "VGA estándar de QEMU (VNC no soporta 3D)"

        # Sin VNC embebido: intentar VirGL si el host lo soporta del todo.
        try:
            caps = detect_host_graphics()
            gl_ok = bool(caps.get("opengl"))
            virgl_installed = bool(caps.get("virgl"))
        except Exception:
            gl_ok = virgl_installed = False

        virgl_ok = gl_ok and virgl_installed and qemu_virgl and display_gl_ok
        if virgl_ok:
            return "virgl", "VirtIO-GPU + VirGL 3D"
        if qemu_virtio:
            return "virtio", "VirtIO-GPU 2D"
        return "std", "VGA estándar de QEMU"

    def _refresh_auto_graphics_label(self):
        """Actualiza el TEXTO del item "Automático" del combo Gráficos para
        reflejar qué opción concreta va a usarse. No toca su habilitación:
        "Automático" nunca se deshabilita.
        """
        if not hasattr(self, "combo_graphics"):
            return
        try:
            idx = self.combo_graphics.findData("auto")
            if idx < 0:
                return
            _mode_id, label = self._auto_graphics_effective_label()
            _prefix = self.tr("Automático (recomendado)")
            new_text = f"{_prefix} \u2192 {label}"
            if self.combo_graphics.itemText(idx) != new_text:
                # Bloquear señales: cambiar el texto no debe re-disparar
                # currentIndexChanged ni update_graphics_options.
                self.combo_graphics.blockSignals(True)
                self.combo_graphics.setItemText(idx, new_text)
                self.combo_graphics.blockSignals(False)
        except Exception:
            pass

    def _on_vnc_embedded_changed(self, *args):
        """Rehabilita / deshabilita opciones gráficas según el modo de consola.

        Reglas:
          • "Automático" NUNCA se deshabilita: siempre se puede elegir.
            Su texto se actualiza para decir qué opción va a usar.
          • VirGL y Venus SÍ se deshabilitan con VNC embebido / híbrido,
            porque QEMU no puede embeber su salida OpenGL en un socket VNC.

        El estado de VNC embebido se deriva de los combos VISIBLES
        (protocolo + modo), no del checkbox legacy oculto. Esto evita la
        incoherencia de antes (unos VMs deshabilitaban y otros no, sin
        relación aparente con VNC/SPICE).
        """
        if not hasattr(self, "combo_graphics"):
            return

        # Derivar de los combos visibles.
        try:
            _proto, _mode = self._current_console_choice()
            vnc_on = (_proto == "vnc" and _mode in ("embedded", "hybrid"))
        except Exception:
            vnc_on = bool(
                getattr(self, "check_vnc_embedded", None)
                and self.check_vnc_embedded.isChecked()
            )

        # Sincronizar el checkbox legacy (oculto) sin disparar señales.
        if hasattr(self, "check_vnc_embedded"):
            self.check_vnc_embedded.blockSignals(True)
            self.check_vnc_embedded.setChecked(bool(vnc_on))
            self.check_vnc_embedded.blockSignals(False)

        # "auto" NO está en esta lista: nunca se deshabilita.
        incompatible = {"virgl", "venus"}
        model = self.combo_graphics.model()
        for i in range(self.combo_graphics.count()):
            data = self.combo_graphics.itemData(i)
            item = model.item(i)
            if item is not None:
                item.setEnabled(not (vnc_on and data in incompatible))

        # Si la opción ACTUALMENTE seleccionada quedó deshabilitada,
        # caer a "auto" (que ahora siempre está disponible).
        current = self.combo_graphics.currentData()
        if vnc_on and current in incompatible:
            auto_idx = self.combo_graphics.findData("auto")
            if auto_idx >= 0:
                self.combo_graphics.blockSignals(True)
                self.combo_graphics.setCurrentIndex(auto_idx)
                self.combo_graphics.blockSignals(False)

        # Actualizar el texto de "Automático" para reflejar la elección real.
        self._refresh_auto_graphics_label()

        # Re-aplicar las restricciones del modo compatibilidad de
        # snapshots: al cambiar VNC → SPICE (o al revés), este slot
        # rehabilita el combo de gráficos, pero si el flag está activo
        # VirGL/Venus deben seguir bloqueados. _apply_snapshot_compat_ui
        # ya considera la unión de (snapshot_compat OR vnc_on).
        try:
            self._apply_snapshot_compat_ui()
        except Exception:
            pass

        if hasattr(self, "_update_graphics_compat_hint"):
            self._update_graphics_compat_hint()


    def update_graphics_options(self, *args):
        is_macos = self.combo_main_os.currentData() == "macos"
        os_type = self.combo_main_os.currentData()

        try:
            caps = detect_host_graphics()
            gpu = caps.get("gpu", self.tr("No detectada"))
            gl_ok = bool(caps.get("opengl"))
            virgl_installed = bool(caps.get("virgl"))
            vulkan_ok = bool(caps.get("vulkan"))

            # Las sondas de QEMU (-device/-display help) son lentas y su resultado
            # no cambia entre clics: se leen de la caché de host_deps.
            _qcaps = qemu_graphics_capabilities()
            qemu = _qcaps.get("qemu_path")
            qemu_virtio = _qcaps["virtio"]
            qemu_virgl = _qcaps["virgl"]
            display_gl_ok = _qcaps["display_gl"]

            virgl_ok = gl_ok and virgl_installed and qemu_virgl and display_gl_ok

            gl = self.tr("✓ OpenGL") if gl_ok else self.tr("✗ OpenGL")
            vg = (self.tr("✓ VirGL") if virgl_ok
                  else (self.tr("✓ VirGL instalado") if virgl_installed
                        else self.tr("✗ VirGL")))
            vk = self.tr("✓ Vulkan") if vulkan_ok else self.tr("✗ Vulkan")

            if os_type == "windows":
                auto_video = self.tr("VGA estándar (QEMU -vga std)")
                auto_accel = self.tr("sin aceleración 3D")
            elif os_type == "macos":
                auto_video = self.tr("VGA de OSX-KVM (VGA virtual)")
                auto_accel = self.tr("gestionada por OpenCore/OSX-KVM")
            elif virgl_ok:
                auto_video = self.tr("VirtIO-GPU + VirGL 3D")
                auto_accel = self.tr("OpenGL / VirGL")
            elif qemu_virtio:
                auto_video = self.tr("VirtIO-GPU 2D")
                auto_accel = self.tr("sin aceleración 3D")
            else:
                auto_video = self.tr("VGA estándar de QEMU")
                auto_accel = self.tr("sin aceleración 3D")

            selected = self.combo_graphics.currentData() if hasattr(self, "combo_graphics") else "auto"
            if selected == "auto":
                selected_text = self.tr(
                    "<b>Automático → {0}</b><br>Aceleración: {1}"
                ).format(auto_video, auto_accel)
            else:
                selected_map = {
                    "virtio": self.tr("VirtIO-GPU 2D"),
                    "virgl": self.tr("VirtIO-GPU + VirGL 3D"),
                    "venus": self.tr("VirtIO-GPU + Venus/Vulkan 3D"),
                    "qxl": self.tr("Red Hat QXL 2D"),
                    "vmware": self.tr("VMware SVGA II"),
                    "none": self.tr("Sin video / Headless"),
                }
                selected_name = selected_map.get(selected, self.combo_graphics.currentText())
                selected_text = self.tr("<b>Usará: {0}</b>").format(selected_name)

            self.label_graphics_host.setText(
                self.tr("Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}").format(
                    gpu, gl, vg, vk, selected_text)
            )
        except Exception as e:
            self.label_graphics_host.setText(self.tr(
                "Host GPU: no se pudo determinar automáticamente.<br>"
                "Automático: se seleccionará el modo gráfico compatible disponible."
            ))

        self.combo_graphics.setEnabled(True)
        self.combo_graphics_vram.setEnabled(True)

        # Refrescar el texto del item "Automático" para que diga
        # qué opción concreta se usará (nunca se deshabilita).
        if hasattr(self, "_refresh_auto_graphics_label"):
            try:
                self._refresh_auto_graphics_label()
            except Exception:
                pass

    def _persist_android_iso(self, *_args):
        """Guarda la ruta de la ISO de Android en la unidad "Principal".

        La unidad Principal es la única fuente de verdad para la ISO de
        Android (es la que QEMU monta como CD/DVD de arranque). El input
        de la página Android es solo una vista de esa unidad.

        Se llama con debounce desde virtual_machine.py cada vez que el
        usuario cambia el input, y al pulsar Guardar. Solo escribe si la
        VM actual es Android.
        """
        if not self.current_vm_dir:
            return
        if not hasattr(self, "input_android_iso"):
            return
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        try:
            cfg = configparser.ConfigParser(interpolation=None)
            cfg.read(cfg_path, encoding="utf-8")
            if not cfg.has_section("general"):
                return
            if (cfg["general"].get("os_type", "") or "").lower() != "android":
                return
            iso = self.input_android_iso.text().strip()

            # 1) Actualizar la unidad Principal (fuente de verdad para QEMU).
            try:
                devices = self._storage_devices_all(self.current_vm_dir)
            except Exception:
                devices = []
            p = principal_cdrom.find_principal(devices)
            if p is None:
                try:
                    p, _created = principal_cdrom.ensure_principal(devices, "android")
                except Exception:
                    p = None
            if p is not None:
                p["path"] = os.path.abspath(iso) if iso else ""
                p.pop("source", None)  # ISO manual, no descarga automática
                p["principal"] = True
                if not p.get("name"):
                    p["name"] = principal_cdrom.PRINCIPAL_NAME
                self._write_storage_devices(devices)
                if hasattr(self, "refresh_storage_ui"):
                    try:
                        self.refresh_storage_ui()
                    except Exception:
                        pass

            # 2) Guardar también en extra["android_iso"] por compatibilidad
            #    con VMs creadas antes de este cambio.
            if not cfg.has_section("extra"):
                cfg.add_section("extra")
            try:
                extra = json.loads(cfg["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            # portable_paths_v1: guardar la ruta en forma portable
            # (relativa si está dentro de la carpeta de la VM).
            _portable_iso = vm_paths.to_portable(self.current_vm_dir, iso) if iso else ""
            if (extra.get("android_iso") or "") != _portable_iso:
                extra["android_iso"] = _portable_iso
                cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))
                with open(cfg_path, "w", encoding="utf-8") as f:
                    cfg.write(f)
                if hasattr(self, "_invalidate_vm_config_cache"):
                    self._invalidate_vm_config_cache(self.current_vm_dir)
        except Exception as e:
            try:
                self.log_message(f"[AVISO] No se pudo guardar la ISO de Android: {e}")
            except Exception:
                pass

    def _save_hardware_lists(self):
        if not self.current_vm_dir: return
        cfg_path=os.path.join(self.current_vm_dir,"vm_config.ini")
        cfg=configparser.ConfigParser(interpolation=None); cfg.read(cfg_path,encoding="utf-8")
        if not cfg.has_section("hardware"):
            cfg.add_section("hardware")
        hw=cfg["hardware"]
        hw["network_devices"]=json.dumps(self._network_devices())
        hw["passthrough_devices"]=json.dumps(getattr(self,"_passthrough_saved",[]))
        # Guardar también el dispositivo de señalización elegido (va en
        # extra, junto al resto de opciones de bajo nivel).
        if hasattr(self, "combo_pointer"):
            if not cfg.has_section("extra"):
                cfg.add_section("extra")
            try:
                extra = json.loads(cfg["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["pointer_device"] = self.combo_pointer.currentData() or "auto"
            cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))

        # Auto-inicio de la VM al abrir la app. El checkbox vive en
        # Configuración -> Sistema -> Opciones avanzadas.
        if hasattr(self, "check_autostart_on_launch"):
            if not cfg.has_section("extra"):
                cfg.add_section("extra")
            try:
                extra = json.loads(cfg["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["autostart_on_launch"] = bool(
                self.check_autostart_on_launch.isChecked()
            )
            cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))

        # serial_to_file_v1: persistir el flag de captura del puerto
        # serie (lo consume workers._serial_args()).
        if hasattr(self, "check_serial_to_file"):
            if not cfg.has_section("extra"):
                cfg.add_section("extra")
            try:
                extra = json.loads(cfg["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["serial_to_file"] = bool(
                self.check_serial_to_file.isChecked()
            )
            cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))

        with open(cfg_path,"w",encoding="utf-8") as f: cfg.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(self.current_vm_dir)


    def _load_localized_md(self, base_name, subdir="notes"):
        """Carga <subdir>/<base>_<lang>.md; fallback a _es.

        Marcadores: i18n_tanda2e3_os_notes, i18n_tanda2e4_help_md.
        """
        here = os.path.dirname(os.path.abspath(__file__))
        lang = getattr(self, "_ui_language", "es") or "es"
        base_dir = os.path.join(here, subdir) if subdir else here
        path = os.path.join(base_dir, "%s_%s.md" % (base_name, lang))
        if not os.path.isfile(path):
            path = os.path.join(base_dir, "%s_es.md" % base_name)
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _update_os_notes_visibility(self, *args):
        """Muestra u oculta el aviso contextual del SO seleccionado.

        Marcador: i18n_tanda2e3_os_notes. Lee notes/<os>_<lang>.md y lo
        renderiza como Markdown. El widget os_notes_title ya no se usa
        (el titulo va dentro del .md); se oculta para no dejar hueco.
        """
        widget = getattr(self, "os_notes_widget", None)
        if widget is None:
            return
        try:
            os_type = self.combo_main_os.currentData() or ""
        except Exception:
            os_type = ""
        if os_type not in self._OS_NOTES:
            widget.setVisible(False)
            return
        md = self._load_localized_md(os_type)
        if not md:
            widget.setVisible(False)
            return
        title = getattr(self, "os_notes_title", None)
        if title is not None:
            title.setVisible(False)
        body = getattr(self, "os_notes_body", None)
        if body is not None:
            # PyQt6 no expone QLabel.setMarkdown(); el equivalente es
            # cambiar el textFormat a MarkdownText y asignar el texto.
            try:
                from PyQt6.QtCore import Qt as _Qt
                body.setTextFormat(_Qt.TextFormat.MarkdownText)
            except Exception:
                pass
            body.setText(md)
        widget.setVisible(True)

    def _goto_storage_section(self):
        """Cambia a la sección Almacenamiento de Configuración.

        Se usa desde el botón "Configurar medio en Almacenamiento" de las
        páginas Android y macOS (antes tenían sus propios inputs, que se
        eliminaron por duplicación).
        """
        try:
            sidebar = getattr(self, "config_sidebar", None)
            if sidebar is None:
                return
            for i in range(sidebar.count()):
                item = sidebar.item(i)
                if item is None:
                    continue
                data = item.data(_VM_USER_ROLE) or ""
                if data == "Almacenamiento":
                    sidebar.setCurrentRow(i)
                    return
        except Exception:
            pass

    def _update_version_so_visibility(self, *args):
        """Muestra u oculta "Versión de SO:" según la plataforma.

        Android no tiene versiones de SO (la versión la decide la ISO),
        así que para Android se ocultan el label y el stack de selección.
        Para el resto de SO (Linux, Windows, macOS) se fuerza visibilidad
        explícita de cada widget, incluido el combo de distro Linux, por
        si algún parche anterior lo dejó oculto.
        """
        os_type = ""
        try:
            os_type = self.combo_main_os.currentData() or ""
        except Exception:
            pass
        is_android = (os_type == "android")
        visible = (not is_android)

        # 1) Label "Versión de SO:"
        lbl = getattr(self, "label_version_so", None)
        if lbl is not None:
            lbl.setVisible(visible)

        # 2) Stack de selección de versión (contiene el combo de distro)
        stack = getattr(self, "version_selector_stack", None)
        if stack is None:
            stack = getattr(self, "stack_pages", None)
        if stack is not None:
            stack.setVisible(visible)
            # Reafirmar también el combo específico de Linux. Es el que el
            # usuario espera ver cuando la plataforma es GNU/Linux.
            for name in ("combo_lin_distro", "combo_win_ver", "combo_macos_ver"):
                c = getattr(self, name, None)
                if c is not None:
                    c.setVisible(visible)
                    c.setEnabled(visible)

        # 3) Log informativo (una vez por cambio)
        try:
            if getattr(self, "_last_so_vis_log", None) != (os_type, visible):
                self._last_so_vis_log = (os_type, visible)
                self.log_message(
                    f"==> Visibilidad Versión de SO: os_type={os_type!r} "
                    f"visible={visible} "
                    f"(combo_lin_distro={'sí' if hasattr(self, 'combo_lin_distro') else 'no'})"
                )
        except Exception:
            pass

    def _update_graphics_compat_hint(self):
        if not hasattr(self, "label_graphics_compat"):
            return
        mode = self.combo_graphics.currentData()
        firmware = self.combo_firmware.currentData() if hasattr(self, "combo_firmware") else "bios"
        os_type = self.combo_main_os.currentData() if hasattr(self, "combo_main_os") else "linux"
        # Android-x86 9.0 (kernel 4.9) no trae driver VirtIO-GPU: si se
        # elige a mano, al arrancar se queda en "Detecting Android-x86..."
        # y cae a un shell de rescate. Solo se avisa si el usuario lo
        # eligió explícitamente; "Automático" ya resuelve a QXL para Android.
        if os_type == "android" and mode == "virtio":
            self.label_graphics_compat.setText(self.tr(
                "⚠️ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae "
                "a un shell de rescate con 'Detecting Android-x86…'. Usa "
                "'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o "
                "Bliss OS 15+ sí soportan VirtIO-GPU."
            ))
            self.label_graphics_compat.setVisible(True)
            return
        if firmware == "uefi" and mode in ("qxl", "vmware"):
            nombre = "QXL" if mode == "qxl" else "VMware SVGA"
            self.label_graphics_compat.setText(self.tr(
                f"⚠️ {nombre} + UEFI: el firmware OVMF puede no mostrar nada (pantalla negra) hasta que "
                "el guest cargue su propio driver de video. Si te pasa, prueba 'Automático' o 'VirtIO-GPU 2D'."
            ))
            self.label_graphics_compat.setVisible(True)
        else:
            self.label_graphics_compat.setVisible(False)

    # ==================================================================
    # Exportar OVF / OVA (marcador ovf_ova_io_v1)
    # ==================================================================
    # Referencia: DMTF DSP0243 (Open Virtualization Format 2.0).
    #
    # El OVA es un tar sin comprimir con:
    #   - descriptor.ovf           (XML, siempre)
    #   - manifest.mf              (SHA-1 de cada archivo, siempre)
    #   - disco.vmdk / disco.qcow2 (uno por disco)
    #   - .virtmachine.json        (metadata propia, solo si la generamos)
    #
    # Los hipervisores de terceros ignoran los archivos que no conocen,
    # asi que .virtmachine.json no rompe la compatibilidad.

    @staticmethod
    def _is_enospc_error(err):
        """True si el error viene de 'No space left on device'."""
        s = str(err or "").lower()
        return ("errno 28" in s
                or "no space left" in s
                or "enospc" in s
                or "disk full" in s
                or "espacio insuficiente" in s)

    def _enospc_friendly_msg(self, err, where=""):
        """Mensaje específico cuando falla por falta de espacio."""
        return (
            "La operación se quedó sin espacio en disco.\n"
            f"{('Lugar: ' + where) if where else ''}\n\n"
            f"Detalle técnico:\n{err}\n\n"
            "Cómo resolverlo:\n"
            "  • Comprueba el espacio libre con: df -h\n"
            "  • Libera espacio en el disco donde está el destino.\n"
            "  • Los archivos parciales generados se limpian solos; "
            "vuelve a intentarlo cuando tengas espacio suficiente."
        )

    def _check_space_or_warn(self, dest_path, needed_bytes, op_label,
                             extra_context=None):
        """Comprueba espacio libre antes de operaciones largas.

        Marcador vm_space_guard_v1. Marcador ovf_space_optimize_v1:
        acepta `extra_context` (lista de str) para enriquecer el mensaje
        con desglose y sugerencias. Devuelve True si el usuario acepta
        continuar (o si hay espacio de sobra). False si no hay espacio
        suficiente o el usuario cancela tras el aviso de "va justo".
        """
        try:
            ok, free, msg = ovf_io.check_ovf_space(
                dest_path, needed_bytes, extra_context=extra_context
            )
        except Exception:
            return True
        if ok is False:
            QMessageBox.warning(
                self, f"{op_label}: espacio insuficiente", msg
            )
            return False
        if ok is None:
            resp = QMessageBox.warning(
                self, f"{op_label}: espacio justo",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            return resp == QMessageBox.StandardButton.Yes
        return True

    def _ovf_size_estimate_for_export(self, vm_dir, is_macos, to_vmdk):
        """Estima los bytes necesarios para exportar una VM.

        Marcador ovf_auto_compress_v1. Marcador ovf_space_optimize_v1:
        devuelve (needed, breakdown) en lugar de solo `needed`.

        Calcula el tamaño real de los discos a exportar y aplica un
        factor según la modalidad elegida:

          • VMDK  → 2.1× (temporal VMDK stream-opt + OVA final, que
                    coexisten durante el empaquetado).
          • QCOW2 → 1.3× (temporal comprimido ~0.5× + OVA final ~0.5×,
                    con margen de seguridad).

        Los factores anteriores (2.5 y 1.8) pedían espacio de disco que
        no se corresponde con el pico real: el disco original ya está en
        disco, así que solo importa el espacio que va a ocuparse en el
        DESTINO durante la operación.

        Devuelve:
          (needed_bytes, breakdown)
          breakdown = {
            "original": X,   # tamaño del disco original (informativo)
            "temporal": Y,   # temporal durante la conversión
            "final":    Z,   # OVA / OVF final en el destino
            "peak":     P,   # pico simultáneo en el destino
          }
        Si total <= 0, devuelve (0, {}).
        """
        total = 0
        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception:
            data = {}
        candidates = []
        if is_macos:
            p = os.path.join(vm_dir, "mac_hdd_ng.qcow2")
            if os.path.isfile(p):
                candidates.append(p)
        else:
            for d in ((data.get("extra") or {}).get("storage_devices") or []):
                if not isinstance(d, dict): continue
                if str(d.get("device") or "") not in ("sata", "nvme", "floppy"):
                    continue
                p = str(d.get("path") or "")
                if not p: continue
                p_abs = vm_paths.to_absolute(vm_dir, p)
                if p_abs and os.path.isfile(p_abs):
                    candidates.append(p_abs)
        for p in candidates:
            try:
                total += os.path.getsize(p)
            except OSError:
                pass
        if total <= 0:
            return 0, {}
        if to_vmdk:
            # VMDK stream-optimized: 1× temporal + 1× OVA final.
            temporal = total
            final = total
            peak = temporal + final
            needed = int(total * 2.1)  # 5% colchón sobre el pico real (2.0)
        else:
            # QCOW2 con compresión zlib: ~0.5× temporal + ~0.5× OVA final.
            temporal = int(total * 0.5)
            final = int(total * 0.5)
            peak = temporal + final
            needed = int(total * 1.3)  # colchón amplio sobre el pico (~1.0)
        breakdown = {
            "original": total,
            "temporal": temporal,
            "final": final,
            "peak": peak,
        }
        return needed, breakdown

    def _export_vm_as_ova(self, fmt, vm_name):
        """Punto de entrada del export OVF/OVA.

        Pregunta al usuario si convertir a VMDK (compatibilidad maxima
        con VirtualBox/VMware) y donde guardar. Despues lanza el worker.
        """
        from PyQt6.QtCore import Qt as _Qt
        from PyQt6.QtWidgets import QFileDialog

        # ovf_auto_compress_v1: detectar macOS para elegir textos del
        # diálogo y abrir el diálogo de exportación.
        _vm_os_type = ""
        try:
            _cfg_local = self._load_vm_config_cached(self.current_vm_dir)
            _vm_os_type = str(_cfg_local.get("os_type") or "").lower()
        except Exception:
            _vm_os_type = ""
        _is_macos = (_vm_os_type == "macos")

        _exp_dlg = _ExportOvfDialog(self, vm_name, _is_macos)
        if _exp_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        _exp_vals = _exp_dlg.values() or {}
        to_vmdk = bool(_exp_vals.get("to_vmdk"))
        include_iso = bool(_exp_vals.get("include_iso"))
        # ovf_export_destino_v1: destino explicito elegido por el usuario.
        # Se propaga a _export_vm_as_ova_impl y a ovf_io.build_ovf_xml.
        destino = str(_exp_vals.get("destino") or "virtualbox").lower()
        if destino not in ("vmware", "virtualbox", "virtmachine"):
            destino = "virtualbox"

        # 2) Destino
        if fmt == "ova":
            suggested = os.path.join(os.path.expanduser("~"),
                                     f"{vm_name}.ova")
            dest_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar OVA", suggested,
                "Open Virtual Appliance (*.ova);;Todos los archivos (*)",
            )
            if not dest_path:
                return
            if not dest_path.lower().endswith(".ova"):
                dest_path += ".ova"
        else:
            parent = QFileDialog.getExistingDirectory(
                self, "Elige la carpeta donde crear el OVF + discos",
                os.path.expanduser("~"),
            )
            if not parent:
                return
            dest_path = os.path.join(parent, f"{vm_name}.ovf")

        if os.path.exists(dest_path):
            resp = QMessageBox.question(
                self, "Ya existe",
                f"El destino ya existe:\n{dest_path}\n\n\u00bfSobrescribir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        vm_dir = self.current_vm_dir

        # vm_space_guard_v1: comprobar espacio antes de lanzar el worker.
        # ovf_space_optimize_v1: pasar desglose y sugerencias al mensaje.
        try:
            _needed, _breakdown = self._ovf_size_estimate_for_export(
                vm_dir, _is_macos, to_vmdk
            )
            _ctx = []
            if _breakdown:
                _hb = ovf_io.human_bytes_io
                _ctx.append("Desglose estimado del espacio en el destino:")
                _ctx.append(
                    "  • Disco original: "
                    + _hb(_breakdown["original"])
                    + " (ya está en disco, no cuenta)"
                )
                _ctx.append(
                    "  • Temporal durante conversión: ~"
                    + _hb(_breakdown["temporal"])
                )
                _ctx.append(
                    "  • OVA / OVF final: ~"
                    + _hb(_breakdown["final"])
                )
                _ctx.append(
                    "  Pico simultáneo en el destino: ~"
                    + _hb(_breakdown["peak"])
                )
                if destino == "vmware":
                    _ctx.append("")
                    _ctx.append(
                        "El destino VMware siempre usa VMDK, que "
                        "necesita ~2× el tamaño del disco "
                        "original durante la exportación."
                    )
                    _ctx.append("")
                    _ctx.append("Para liberar espacio:")
                    _ctx.append(
                        "  • Borra archivos en el disco destino, o"
                    )
                    _ctx.append(
                        "  • Elige otra carpeta en un disco con "
                        "más espacio."
                    )
                    _ctx.append("")
                    _ctx.append(
                        "Si NO necesitas específicamente VMware: "
                        "cancela esta exportación y hazla con "
                        "destino 'Virtual.Machine', que ocupa "
                        "~40% menos."
                    )
                elif to_vmdk:
                    _ctx.append("")
                    _ctx.append(
                        "El formato VMDK necesita ~2× el tamaño "
                        "del disco original durante la exportación."
                    )
                    _ctx.append("")
                    _ctx.append("Para liberar espacio:")
                    _ctx.append(
                        "  • Borra archivos en el disco destino, o"
                    )
                    _ctx.append(
                        "  • Elige otra carpeta en un disco con "
                        "más espacio."
                    )
                    _ctx.append("")
                    _ctx.append(
                        "O cancela y cambia el formato a QCOW2 en el "
                        "diálogo: mismo destino, ~40% menos espacio."
                    )
                else:
                    _ctx.append("")
                    _ctx.append(
                        "Ya estás usando el formato más ligero "
                        "(QCOW2)."
                    )
                    _ctx.append("")
                    _ctx.append("Para liberar espacio:")
                    _ctx.append(
                        "  • Borra archivos en el disco destino, o"
                    )
                    _ctx.append(
                        "  • Elige otra carpeta en un disco con "
                        "más espacio."
                    )
            if not self._check_space_or_warn(
                dest_path, _needed, "Exportar OVF/OVA",
                extra_context=_ctx,
            ):
                return
        except Exception as _sp_err:
            try:
                self.log_message(
                    f"[AVISO] No se pudo comprobar el espacio libre: {_sp_err}"
                )
            except Exception:
                pass

        # ovf_export_summary_v1: medimos la duracion real para
        # mostrarla en el dialogo final junto con destino y formato.
        import time as _time_mod
        _t_start = _time_mod.monotonic()

        def _work(log_emit, is_cancelled, progress_emit):
            return self._export_vm_as_ova_impl(
                vm_dir, vm_name, fmt, dest_path, to_vmdk, include_iso,
                _is_macos, destino,
                log_emit, is_cancelled, progress_emit,
            )

        self.run_async(
            _work,
            f"Exportando '{vm_name}' como {fmt.upper()}",
            on_success=lambda result: self._on_export_ova_success(
                result, vm_name, _t_start, destino, to_vmdk, include_iso,
                _is_macos,
            ),
            on_error=lambda e: self._show_selectable_error(
                f"Exportar {fmt.upper()}",
                self._enospc_friendly_msg(e, "carpeta destino")
                if self._is_enospc_error(e)
                else f"No se pudo completar la exportaci\u00f3n.\n\n{e}",
            ),
            cancelable=True,
            show_log=True,
            subtitle=("Convirtiendo disco a VMDK..." if to_vmdk
                      else "Empaquetando OVF/OVA..."),
        )

    def _export_vm_as_ova_impl(self, vm_dir, vm_name, fmt, dest_path,
                                to_vmdk, include_iso, is_macos, destino,
                                log_emit, is_cancelled, progress_emit):
        """Cuerpo del export OVF/OVA. Corre en hilo de fondo.

        ovf_export_destino_v1: `destino` viene ya resuelto por el dialogo
        ("vmware" | "virtualbox" | "virtmachine") y se propaga a
        ovf_io.build_ovf_xml para ajustar el descriptor.
        """
        import tempfile as _tmp
        import shutil as _sh

        log_emit(f"==> Exportando '{vm_name}' como {fmt.upper()} -> {dest_path}")

        # 1) Cargar config
        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception:
            data = {}
        if not data:
            from vm_config import load_vm_config as _lvc
            data = _lvc(vm_dir)

        # 2) Discos a exportar
        storage_devices = (data.get("extra") or {}).get("storage_devices") or []
        if not isinstance(storage_devices, list):
            storage_devices = []
        disks_to_export = []

        # ovf_ova_io_v1_macos_export: rama específica para macOS.
        # El flujo macOS no usa storage_devices (macos_storage_cleanup_v1
        # los purga). Buscamos los archivos fijos del flujo OSX-KVM:
        #   • mac_hdd_ng.qcow2      -> SIEMPRE
        #   • BaseSystem.img        -> opcional (include_iso)
        #   • OpenCore.qcow2        -> NUNCA (imagen compartida)
        if is_macos:
            _mac_hdd = os.path.join(vm_dir, "mac_hdd_ng.qcow2")
            if not os.path.isfile(_mac_hdd):
                raise RuntimeError(self.tr(
                    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la "
                    "carpeta de la VM ({0}). Sin este archivo la VM "
                    "no tiene sistema operativo que exportar.").format(_mac_hdd))
            disks_to_export.append({
                "name": "mac_hdd_ng",
                "path": _mac_hdd,
                "device": "sata",
                "macos_role": "hdd",
            })
            log_emit("==> macOS: mac_hdd_ng.qcow2 incluido (sistema instalado).")
            if include_iso:
                _base_sys = os.path.join(vm_dir, "BaseSystem.img")
                if os.path.isfile(_base_sys) and os.path.getsize(_base_sys) > 0:
                    disks_to_export.append({
                        "name": "BaseSystem",
                        "path": _base_sys,
                        "device": "sata",
                        "macos_role": "basesystem",
                    })
                    log_emit("==> macOS: BaseSystem.img incluido (medio de "
                             "instalación).")
                else:
                    log_emit("[AVISO] macOS: BaseSystem.img no encontrado o "
                             "vacío; se omite del OVA.")
            else:
                log_emit("==> macOS: BaseSystem.img NO se incluye "
                         "(se puede re-descargar en el destino).")
            log_emit("==> macOS: OpenCore.qcow2 NO se incluye "
                     "(imagen compartida de OSX-KVM).")

        if not is_macos:
            for d in storage_devices:
                if not isinstance(d, dict): continue
                typ = str(d.get("device") or "")
                if typ not in ("sata", "nvme", "floppy"): continue
                p = str(d.get("path") or "")
                if not p: continue
                p_abs = vm_paths.to_absolute(vm_dir, p)
                if not p_abs or not os.path.isfile(p_abs): continue
                disks_to_export.append({
                    "name": d.get("name") or os.path.basename(p_abs),
                    "path": p_abs,
                    "device": typ,
                })

        if not disks_to_export:
            raise RuntimeError(self.tr(
                "La VM no tiene discos adjuntos que exportar. "
                "A\u00f1ade al menos un disco en Configuraci\u00f3n \u2192 "
                "Almacenamiento."
            ))

        log_emit(f"==> Discos a exportar: {len(disks_to_export)}")

        # ovf_ova_io_v1_cdrom_export: recopilar unidades CD/DVD reales.
        # Las unidades con source="installer" se omiten (no hay archivo
        # físico). Si include_iso=False, se emiten vacías.
        cdroms_to_export = []
        for cd in storage_devices:
            if not isinstance(cd, dict): continue
            if str(cd.get("device") or "") != "cdrom": continue
            if str(cd.get("source") or "") == "installer": continue
            p = str(cd.get("path") or "")
            if p:
                p_abs = vm_paths.to_absolute(vm_dir, p)
                if p_abs and os.path.isfile(p_abs):
                    cdroms_to_export.append({
                        "src_abs": p_abs,
                        "arcname": os.path.basename(p_abs),
                        "name": cd.get("name") or os.path.basename(p_abs),
                    })
                    continue
            # Unidad vacía
            cdroms_to_export.append({
                "src_abs": "",
                "arcname": "",
                "name": cd.get("name") or "CD/DVD",
            })
        log_emit(f"==> Unidades CD/DVD a exportar: {len(cdroms_to_export)} "
                 f"(ISOs incluidas: {'sí' if include_iso else 'no'})")

        # 3) Directorio temporal
        #
        # ovf_ova_io_v1_rev2: para OVA + QCOW2 no hace falta temp (los
        # discos se empaquetan directamente). Solo se crea si hay que
        # convertir a VMDK (qemu-img necesita escribir a disco antes de
        # meterlo en el tar) o para el modo OVF en carpeta.
        if fmt == "ovf":
            work_dir = os.path.dirname(dest_path) or os.getcwd()
            _cleanup_workdir = False
        elif to_vmdk:
            parent = os.path.dirname(os.path.abspath(dest_path)) or os.getcwd()
            work_dir = _tmp.mkdtemp(prefix=".ovf_export_", dir=parent)
            _cleanup_workdir = True
        else:
            work_dir = None
            _cleanup_workdir = False

        ovf_disks = []
        # ovf_ova_io_v1_diskname: registro de nombres ya usados dentro
        # del OVA/OVF. Si dos discos del original se llaman igual, el
        # segundo pasa a "<nombre>_2.ext".
        _used_names = set()

        # ovf_progress_phases_v1: mapear el progreso de las DOS fases
        # del export (conversión de discos y empaquetado final) a un
        # único rango global 0..100. Sin esto, cada fase emitía 0..100
        # por su cuenta y la barra "retrocedía" al pasar de una a otra
        # (barrido visual 100% → 75%).
        #
        #   • Conversión de discos: 0..80  (cada disco ocupa 80/N).
        #   • Empaquetado OVA:      80..100.
        _N_DISKS = max(1, len(disks_to_export))
        _CONVERT_SHARE = 80.0
        _PACK_SHARE = 20.0
        _SLICE = _CONVERT_SHARE / _N_DISKS
        _disk_counter = {"i": 0}

        def _emit_convert(pct, msg):
            """Reescala 0..100 local de un disco al rango global."""
            if not progress_emit:
                return
            if pct < 0:
                progress_emit(-1, msg)
                return
            base = _disk_counter["i"] * _SLICE
            progress_emit(int(base + pct * _SLICE / 100.0), msg)

        def _emit_pack(pct, msg):
            """ovf_tar_indeterminate_v1: tar no reporta progreso
            intermedio (no tiene opcion -p y su salida no es
            parseable con fiabilidad). En lugar de dejar la barra
            clavada al 80% durante minutos, pasamos a modo
            indeterminado (animacion continua): el usuario ve que
            la operacion sigue viva, aunque no sepamos el % exacto.
            El mensaje del empaquetado si se muestra.
            """
            if not progress_emit:
                return
            progress_emit(-1, msg)

        try:
            # 4) Preparar cada disco
            #
            # ovf_ova_io_v1_rev2: si el formato es OVA y no hay que
            # convertir, empaquetamos el archivo ORIGINAL directamente.
            # Antes se copiaba a un temporal antes de tar, lo que
            # triplicaba la necesidad de espacio (original + temp + .ova).
            for i, d in enumerate(disks_to_export):
                if is_cancelled():
                    raise RuntimeError("Exportaci\u00f3n cancelada por el usuario.")
                # ovf_progress_phases_v1: fijar el índice del disco
                # actual para que _emit_convert sepa en qué franja del
                # rango global 0..80 está.
                _disk_counter["i"] = i
                src = d["path"]
                # ovf_ova_io_v1_diskname: preservar el nombre original
                # del disco, saneado para evitar caracteres problematicos
                # en visores externos (espacios, acentos, simbolos raros).
                _orig_base = os.path.basename(src)
                _stem, _ext_orig = os.path.splitext(_orig_base)
                _ext_orig = _ext_orig.lower().lstrip(".")
                if to_vmdk:
                    ext = "vmdk"
                else:
                    ext = _ext_orig if _ext_orig in (
                        "qcow2","raw","vmdk","vdi","vhd","vhdx"
                    ) else "qcow2"
                # Sanear: solo [A-Za-z0-9._-], sin espacios.
                _stem = re.sub(r"[^A-Za-z0-9._-]+", "_", _stem or "").strip("._")
                if not _stem:
                    _stem = f"disk{i}"
                dst_name = f"{_stem}.{ext}"
                # Deduplicar si ya hay un disco con ese nombre.
                if dst_name in _used_names:
                    k = 2
                    while f"{_stem}_{k}.{ext}" in _used_names:
                        k += 1
                    dst_name = f"{_stem}_{k}.{ext}"
                _used_names.add(dst_name)

                # ovf_auto_compress_v1: política automática por formato:
                #   • VMDK              → conversión a stream-optimized
                #                         (descarta snapshots por diseño).
                #   • QCOW2             → qemu-img convert -c -O qcow2.
                #                         Aplana snapshots + comprime zlib.
                #   • Otros (RAW, VDI…) → copia directa.
                _is_qcow2 = dst_name.lower().endswith(".qcow2")

                # ovf_no_temp_v1: si el disco es QCOW2, está ya
                # aplanado (sin snapshots internos) y no tiene backing
                # file, no hace falta convertirlo: se puede empaquetar
                # directamente. Ahorra tiempo (no se ejecuta qemu-img
                # convert) y espacio temporal (no se duplica el disco
                # en el work_dir). Trade-off: el OVA final no se
                # recomprime con zlib, así que si el QCOW2 original no
                # estaba comprimido, el OVA será algo más grande.
                # Los discos con snapshots o backing SÍ se convierten
                # (necesario para aplanarlos dentro del OVA).
                _skip_convert = False
                if (not to_vmdk) and _is_qcow2:
                    try:
                        _r_info = subprocess.run(
                            ["qemu-img", "info", "--output=json", src],
                            capture_output=True, text=True, timeout=15,
                        )
                        if _r_info.returncode == 0:
                            _info = json.loads(_r_info.stdout or "{}")
                            _snaps = _info.get("snapshots") or []
                            _has_backing = bool(
                                _info.get("backing-filename")
                            )
                            if (not _snaps) and (not _has_backing):
                                _skip_convert = True
                    except Exception:
                        _skip_convert = False

                if _skip_convert:
                    log_emit(
                        f"==> Disco {i+1}/{len(disks_to_export)}: "
                        f"{d['name']} — ya está aplanado y sin "
                        f"snapshots; se empaqueta directamente "
                        f"(sin conversión ni recompresión)."
                    )
                    _emit_convert(0, f"Sin conversión: {dst_name}")
                    _emit_convert(100, f"Listo: {dst_name}")
                    src_for_tar = src
                elif to_vmdk or _is_qcow2:
                    if work_dir is None:
                        parent = (os.path.dirname(os.path.abspath(dest_path))
                                  or os.getcwd())
                        work_dir = _tmp.mkdtemp(prefix=".ovf_export_",
                                                dir=parent)
                        _cleanup_workdir = True
                    dst = os.path.join(work_dir, dst_name)

                    if to_vmdk:
                        log_emit(f"==> Disco {i+1}/{len(disks_to_export)}: "
                                 f"{d['name']} — convirtiendo a VMDK "
                                 f"stream-optimized")
                        ovf_io.convert_to_vmdk_stream_optimized(
                            src, dst,
                            log_emit=log_emit,
                            progress_emit=_emit_convert,
                            is_cancelled=is_cancelled,
                        )
                    else:
                        log_emit(f"==> Disco {i+1}/{len(disks_to_export)}: "
                                 f"{d['name']} — descartando snapshots y "
                                 f"comprimiendo (qemu-img convert -c -O qcow2)")
                        # ovf_progress_phases_v1: qemu-img convert -c
                        # con capture_output no permite parsear la barra
                        # de progreso (se queda en el buffer). Emitimos
                        # manualmente 0 al empezar y 100 al terminar para
                        # que la franja del disco se rellene.
                        _emit_convert(0, f"Comprimiendo {dst_name}...")
                        # ovf_qcow2_compressed_live_progress_v1:
                        # delegamos en ovf_io.convert_to_qcow2_compressed,
                        # que lee el progreso en vivo (qemu-img usa \r,
                        # no \n) y respeta is_cancelled. Antes se usaba
                        # subprocess.run(capture_output=True), que dejaba
                        # la barra congelada al 0% durante toda la
                        # conversion.
                        ovf_io.convert_to_qcow2_compressed(
                            src, dst,
                            log_emit=log_emit,
                            progress_emit=_emit_convert,
                            is_cancelled=is_cancelled,
                        )
                        if (not os.path.isfile(dst)
                                or os.path.getsize(dst) == 0):
                            raise RuntimeError(self.tr(
                                "El aplanado+compresión de "
                                "'{0}' no produjo un "
                                "archivo válido.").format(os.path.basename(src)))
                        _emit_convert(100, f"Comprimido: {dst_name}")
                    src_for_tar = dst
                else:
                    dst = os.path.join(work_dir, dst_name)
                    log_emit(f"==> Preparando disco {i+1}/{len(disks_to_export)}: {d['name']} (copia directa)")
                    _emit_convert(0, f"Copiando {dst_name}...")
                    _sh.copy2(src, dst)
                    _emit_convert(100, f"Copiado: {dst_name}")
                    src_for_tar = dst

                # ovf_ova_io_v1_disksize: el descriptor OVF espera el
                # tamanio VIRTUAL del disco (lo que ve el guest), no el
                # tamanio fisico del archivo QCOW2. Un QCOW2 vacio de 8 GB
                # ocupa ~200 KB pero su virtual-size es 8 GiB.
                capacity_gb = 1
                try:
                    _r = subprocess.run(
                        ["qemu-img", "info", "--output=json", src_for_tar],
                        capture_output=True, text=True, timeout=10, check=True,
                    )
                    _vsize = int(json.loads(_r.stdout or "{}").get("virtual-size") or 0)
                    if _vsize > 0:
                        capacity_gb = max(1, int(round(_vsize / (1024**3))))
                except Exception:
                    try:
                        _sz = os.path.getsize(src_for_tar)
                        capacity_gb = max(1, int(round(_sz / (1024**3))))
                    except OSError:
                        capacity_gb = 1
                if ext == "vmdk":
                    ovf_fmt = ("http://www.vmware.com/interfaces/specifications/"
                               "vmdk.html#streamOptimized")
                elif ext == "qcow2":
                    ovf_fmt = "http://schemas.dmtf.org/ovf/envelope/1/qcow2"
                else:
                    ovf_fmt = ""
                ovf_disks.append({
                    "disk_id": f"vmdisk{i}",
                    "file": dst_name,
                    "capacity_gb": capacity_gb,
                    "format": ovf_fmt,
                    "_abs": src_for_tar,
                    "_arcname": dst_name,
                })

            # 5) Redes y otros datos
            networks = []
            for nd in (data.get("network_devices") or []):
                if not isinstance(nd, dict): continue
                model = "E1000"
                m = str(nd.get("model") or "").lower()
                if "virtio" in m: model = "Virtio"
                elif "rtl8139" in m: model = "PCNet32"
                elif "vmxnet3" in m: model = "VMXNET3"
                networks.append({"name": nd.get("name") or "nat", "model": model})
            if not networks:
                networks = [{"name": "nat", "model": "E1000"}]

            try:
                cpus = int(data.get("cores") or 2)
            except Exception:
                cpus = 2
            ram_text = str(data.get("ram") or "4G").upper().replace("GB", "G").replace(" ", "")
            m = re.match(r"(\d+)", ram_text)
            ram_gb = int(m.group(1)) if m else 4
            memory_mb = ram_gb * 1024

            os_type = (data.get("os_type") or "linux").lower()
            extra = data.get("extra") or {}
            distro_or_version = ""
            if os_type == "linux":
                distro_or_version = extra.get("distro") or ""
            elif os_type == "windows":
                distro_or_version = extra.get("win_ver") or "Windows 10"
            elif os_type == "macos":
                distro_or_version = extra.get("os_choice") or ""

            # 6) Construir OVF
            log_emit("==> Construyendo descriptor OVF...")
            _cdroms_arg = []
            for _i, _cd in enumerate(cdroms_to_export):
                _entry = {"file_id": f"cdrom{_i}_file",
                          "file_arcname": ""}
                if include_iso and _cd.get("src_abs"):
                    _entry["file_arcname"] = _cd["arcname"]
                _cdroms_arg.append(_entry)
            _annotation = ""
            if is_macos:
                _annotation = (
                    "VM macOS exportada por Virtual.Machine. La cadena de "
                    "arranque OpenCore+OSX-KVM no es compatible con "
                    "VirtualBox ni VMware. Este OVA está pensado para "
                    "reimportarse en Virtual.Machine u otro host Linux con "
                    "la misma app."
                )
            # ovf_ova_vbox_uefi_v1_B: pasar el firmware real a
            # build_ovf_xml() para que el descriptor incluya
            # vbox:BIOSSettings/vbox:Firmware=efi cuando corresponda.
            # VirtualBox no puede inferirlo de otra forma: sin este
            # bloque, la VM importada queda en BIOS legacy aunque el
            # disco sea GPT+EFI, y el usuario tiene que activar EFI
            # a mano. macOS siempre va UEFI.
            _firmware_export = str(data.get("firmware") or "bios").lower()
            if is_macos:
                _firmware_export = "uefi"
            # ovf_vmware_compat_v4: pasar el tamano real en bytes
            # de cada disco para rellenar ovf:size. ovftool lo
            # exige; sin el, rechaza con "Invalid value <id> for
            # attribute fileRef".
            _disk_sizes = {}
            for _d_ovf in ovf_disks:
                try:
                    _disk_sizes[_d_ovf["disk_id"]] = int(
                        os.path.getsize(_d_ovf["_abs"])
                    )
                except Exception:
                    _disk_sizes[_d_ovf["disk_id"]] = 0
            ovf_text = ovf_io.build_ovf_xml(
                vm_name=vm_name,
                os_type=os_type,
                distro_or_version=distro_or_version,
                cpus=cpus,
                memory_mb=memory_mb,
                disks=ovf_disks,
                networks=networks,
                cdroms=_cdroms_arg,
                annotation=_annotation,
                firmware=_firmware_export,
                destino=destino,
                disk_sizes=_disk_sizes,
            )

            # 7) Metadata propia
            meta = ovf_io.build_virtmachine_meta(data)

            # 8) Escribir destino
            if fmt == "ova":
                # ovf_ova_io_v1_rev2: pasar tuplas (path, arcname)
                disk_items = [(d["_abs"], d["_arcname"]) for d in ovf_disks]
                # ovf_ova_io_v1_cdrom_export: anadir ISOs si el usuario
                # marco la casilla. Se empaquetan directamente sin copia.
                if include_iso:
                    for _cd in cdroms_to_export:
                        if _cd.get("src_abs"):
                            disk_items.append(
                                (_cd["src_abs"], _cd["arcname"])
                            )
                ovf_io.pack_ova(
                    ovf_text, disk_items, dest_path,
                    extra_meta=meta,
                    log_emit=log_emit,
                    progress_emit=_emit_pack,
                    is_cancelled=is_cancelled,
                )
                if _cleanup_workdir and work_dir and os.path.isdir(work_dir):
                    try:
                        _sh.rmtree(work_dir, ignore_errors=True)
                    except Exception:
                        pass
            else:
                ovf_out = dest_path
                if not ovf_out.lower().endswith(".ovf"):
                    ovf_out = ovf_out + ".ovf"
                with open(ovf_out, "w", encoding="utf-8") as f:
                    f.write(ovf_text)
                meta_out = os.path.join(os.path.dirname(ovf_out),
                                        ovf_io.VIRTMACHINE_META)
                try:
                    import json as _json
                    with open(meta_out, "w", encoding="utf-8") as f:
                        _json.dump(meta, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    log_emit(f"[AVISO] No se pudo escribir la metadata: {e}")
                manifest_files = [ovf_out] + [d["_abs"] for d in ovf_disks]
                manifest_path = os.path.join(os.path.dirname(ovf_out),
                                             ovf_io.MANIFEST_NAME)
                try:
                    ovf_io.write_manifest(manifest_files, manifest_path)
                except Exception as e:
                    log_emit(f"[AVISO] No se pudo escribir el manifest: {e}")
                dest_path = ovf_out

            if progress_emit:
                progress_emit(100, "Exportaci\u00f3n completada.")
            log_emit(f"==> Exportaci\u00f3n OVF/OVA terminada: {dest_path}")
            return dest_path
        finally:
            if _cleanup_workdir and os.path.isdir(work_dir):
                try:
                    _sh.rmtree(work_dir, ignore_errors=True)
                except Exception:
                    pass


    # ==================================================================
    # Importar OVF / OVA (marcador ovf_ova_io_v1)
    # ==================================================================

    def _import_vm_from_ova(self, source):
        """Importacion desde un .ova o .ovf (marcador ovf_ova_io_v1).

        Lee SOLO el descriptor para el dialogo de previsualizacion; la
        extraccion de los discos va despues, en el worker.
        """
        low = source.lower()
        is_ova = low.endswith(".ova")

        # 1) Leer descriptor
        try:
            if is_ova:
                ovf_text = ovf_io.read_ovf_descriptor_only(source)
                if not ovf_text:
                    QMessageBox.warning(
                        self, self.tr("Importar OVA"),
                        self.tr("El archivo .ova no contiene ning\u00fan descriptor .ovf.")
                    )
                    return
            else:
                with open(source, "r", encoding="utf-8", errors="replace") as f:
                    ovf_text = f.read()
                if not ovf_text.strip():
                    QMessageBox.warning(
                        self, self.tr("Importar OVF"),
                        self.tr("El archivo .ovf est\u00e1 vac\u00edo.")
                    )
                    return
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Importar OVF/OVA"),
                self.tr("No se pudo leer el descriptor.\n\n{0}").format(e)
            )
            return

        try:
            ovf_data = ovf_io.parse_ovf_xml(ovf_text)
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Importar OVF/OVA"),
                self.tr("El descriptor OVF no se pudo interpretar.\n\n{0}").format(e)
            )
            return

        # 2) Dialogo de previsualizacion
        suggested_name = (ovf_data.get("name") or
                          os.path.splitext(os.path.basename(source))[0] or
                          "VM-importada")
        suggested_name = re.sub(r'[\\/:*?"<>|]', "_", suggested_name).strip() or "VM-importada"
        existing = set(list_existing_vms())
        base = suggested_name
        i = 2
        while (suggested_name in existing
               or os.path.exists(os.path.join(vm_config.BASE_VM_DIR, suggested_name))):
            suggested_name = f"{base}-{i}"
            i += 1

        dlg = _OvfImportPreviewDialog(self, ovf_data, suggested_name)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        result = dlg.values()
        if not result:
            return

        target_name = result["name"]
        user_os = result["os_type"]
        user_distro_or_ver = result["distro_or_version"]
        import_config_only = result.get("config_only", False)

        target_dir = os.path.join(vm_config.BASE_VM_DIR, target_name)
        if os.path.exists(target_dir):
            resp = QMessageBox.question(
                self, self.tr("Ya existe"),
                self.tr("Ya existe una VM llamada '{0}'.\n\n"
                        "\u00bfReemplazarla? (se eliminar\u00e1 la existente)").format(target_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        # vm_space_guard_v1: comprobar espacio antes de lanzar el worker.
        try:
            _ova_size = 0
            if is_ova:
                try:
                    _ova_size = os.path.getsize(source)
                except OSError:
                    _ova_size = 0
            else:
                _dir = os.path.dirname(os.path.abspath(source))
                for _f in os.listdir(_dir):
                    try:
                        _ova_size += os.path.getsize(os.path.join(_dir, _f))
                    except OSError:
                        pass
            _needed = int(_ova_size * 2.2) if _ova_size else 0
            if not self._check_space_or_warn(
                target_dir, _needed, "Importar OVF/OVA"
            ):
                return
        except Exception as _sp_err:
            try:
                self.log_message(
                    f"[AVISO] No se pudo comprobar el espacio libre: {_sp_err}"
                )
            except Exception:
                pass

        def _work(log_emit, is_cancelled, progress_emit):
            return self._import_vm_from_ova_impl(
                source, is_ova, target_name, target_dir,
                user_os, user_distro_or_ver, import_config_only, ovf_data,
                log_emit, is_cancelled, progress_emit,
            )

        self.run_async(
            _work,
            f"Importando '{target_name}' desde {os.path.basename(source)}",
            on_success=lambda result: self._on_import_success(result),
            on_error=lambda e: self._show_selectable_error(
                self.tr("Importar OVF/OVA"),
                self._enospc_friendly_msg(e, "carpeta de la VM")
                if self._is_enospc_error(e)
                else self.tr("No se pudo completar la importaci\u00f3n.\n\n{0}").format(e),
            ),
            cancelable=True,
            show_log=True,
            subtitle=self.tr("Extrayendo y preparando el OVF/OVA..."),
        )

    def _import_vm_from_ova_impl(self, source, is_ova, target_name, target_dir,
                                   user_os, user_distro_or_ver,
                                   import_config_only, ovf_data,
                                   log_emit, is_cancelled, progress_emit):
        """Cuerpo del import OVF/OVA. Corre en hilo de fondo."""
        import tempfile as _tmp
        import shutil as _sh

        log_emit(f"==> Importando '{target_name}' desde {source}")

        extract_dir = None
        cleanup_extract = False
        try:
            if is_ova:
                os.makedirs(vm_config.BASE_VM_DIR, exist_ok=True)
                parent = os.path.dirname(os.path.abspath(vm_config.BASE_VM_DIR))
                extract_dir = _tmp.mkdtemp(prefix=".ova_extract_", dir=parent)
                cleanup_extract = True
                progress_emit(0, "Extrayendo OVA...")
                log_emit(f"==> Extrayendo OVA en {extract_dir}...")
                ovf_found, meta_found = ovf_io.unpack_ova(source, extract_dir)
                if not ovf_found:
                    raise RuntimeError("El OVA no contiene un descriptor .ovf v\u00e1lido.")
                ovf_dir = os.path.dirname(ovf_found)
                log_emit(f"==> Descriptor encontrado: {os.path.basename(ovf_found)}")
                meta = ovf_io.load_virtmachine_meta(meta_found)
            else:
                ovf_dir = os.path.dirname(os.path.abspath(source))
                meta = ovf_io.load_virtmachine_meta(
                    os.path.join(ovf_dir, ovf_io.VIRTMACHINE_META))

            progress_emit(20, "Preparando configuraci\u00f3n...")

            if os.path.exists(target_dir):
                log_emit(f"==> Eliminando VM existente '{target_name}'...")
                _sh.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            # Convertir/copiar cada disco a QCOW2
            storage_devices = []
            # ovf_ova_io_v1_import_diskname: registro de nombres ya
            # usados dentro de la VM destino.
            _used_disk_names = set()
            disks = ovf_data.get("disks") or []
            log_emit(f"==> Discos a importar: {len(disks)}")

            # ovf_space_optimize_v1_msgfix
# ovf_export_summary_v1_ok
# ovf_ova_io_v1_macos_import: rama específica macOS.
            # El OVA contiene mac_hdd_ng.qcow2 (siempre) y opcionalmente
            # BaseSystem.img. NO van a storage_devices: el flujo macOS
            # los lee por nombre fijo desde vm_dir.
            _is_macos_import = (
                str(user_os or "").lower() == "macos"
                or str(ovf_data.get("os_type") or "").lower() == "macos"
            )

            if _is_macos_import:
                log_emit("==> macOS: importando archivos específicos "
                         "del flujo OSX-KVM.")
                # mac_hdd_ng.qcow2 (siempre)
                _mac_hdd_src = ""
                for _cand in os.listdir(ovf_dir):
                    if _cand.lower() == "mac_hdd_ng.qcow2":
                        _mac_hdd_src = os.path.join(ovf_dir, _cand); break
                if not _mac_hdd_src:
                    for _cand in os.listdir(ovf_dir):
                        _lc = _cand.lower()
                        if _lc.endswith(".qcow2") and "opencore" not in _lc:
                            _mac_hdd_src = os.path.join(ovf_dir, _cand)
                            log_emit(f"[AVISO] macOS: mac_hdd_ng.qcow2 no "
                                     f"encontrado; usando '{_cand}'.")
                            break
                if not _mac_hdd_src:
                    raise RuntimeError(
                        "OVA macOS: no se encontró mac_hdd_ng.qcow2 en "
                        "el paquete. Sin ese archivo no hay sistema que "
                        "importar."
                    )
                _mac_hdd_dst = os.path.join(target_dir, "mac_hdd_ng.qcow2")
                progress_emit(40, "Copiando mac_hdd_ng.qcow2...")
                log_emit("==> Copiando " + os.path.basename(_mac_hdd_src)
                         + " -> mac_hdd_ng.qcow2...")
                _sh.copy2(_mac_hdd_src, _mac_hdd_dst)

                # BaseSystem.img (opcional)
                _bs_src = ""
                for _cand in os.listdir(ovf_dir):
                    if _cand.lower() == "basesystem.img":
                        _bs_src = os.path.join(ovf_dir, _cand); break
                if _bs_src:
                    _bs_dst = os.path.join(target_dir, "BaseSystem.img")
                    progress_emit(70, "Copiando BaseSystem.img...")
                    log_emit("==> Copiando BaseSystem.img...")
                    _sh.copy2(_bs_src, _bs_dst)
                else:
                    log_emit("[AVISO] macOS: BaseSystem.img no está en "
                             "el OVA; se descargará automáticamente "
                             "al iniciar la VM si se necesita.")

                # OSX-KVM en el host (auto-descarga si falta).
                try:
                    _osx_kvm_i = vm_config.OSX_KVM_DIR  # osx_kvm_pkg_paths_v1
                    if not os.path.isdir(_osx_kvm_i):
                        progress_emit(85, "Descargando OSX-KVM...")
                        log_emit("==> OSX-KVM no encontrado; descargando "
                                 "automáticamente...")
                        from host_deps import ensure_osx_kvm_present
                        ensure_osx_kvm_present(log_emit)
                        log_emit("==> OSX-KVM listo.")
                    else:
                        log_emit("==> OSX-KVM ya presente en el host.")
                except Exception as _kx_err:
                    log_emit(f"[AVISO] No se pudo preparar OSX-KVM: "
                             f"{_kx_err}.")

                # Escribir vm_config.ini específico de macOS y salir.
                cpus = int(ovf_data.get("cpus") or 0) or 2
                ram_gb = max(1, int(ovf_data.get("memory_mb") or 0) // 1024) or 4
                ram = f"{ram_gb}G"
                extra = {}
                if meta and isinstance(meta.get("vm_config"), dict):
                    _vmcfg_m = meta["vm_config"]
                    extra = dict(_vmcfg_m.get("extra") or {})
                    # ovf_import_firmware_fix: los campos de hardware
                    # están en el NIVEL SUPERIOR del meta, no dentro de
                    # 'extra'. Los copiamos a extra para que el .ini los
                    # recoja correctamente (firmware, chipset, etc.).
                    for _k in ("firmware", "chipset", "secure_boot", "tpm",
                               "graphics_mode", "graphics_vram",
                               "audio_device", "network_mode",
                               "boot_order"):
                        if _k in _vmcfg_m and _vmcfg_m[_k] is not None:
                            extra.setdefault(_k, _vmcfg_m[_k])
                _mac_ver = user_distro_or_ver or extra.get("os_choice") or ""
                extra["os_choice"] = _mac_ver
                extra["storage_devices"] = []
                extra["cdrom_path"] = ""
                extra["imported_from_ovf"] = True
                try:
                    extra["osx_kvm_source"] = vm_config.OSX_KVM_DIR  # osx_kvm_pkg_paths_v1
                except Exception:
                    pass
                cfg_path = os.path.join(target_dir, "vm_config.ini")
                cfg = configparser.ConfigParser(interpolation=None)
                cfg["general"] = {"name": target_name, "os_type": "macos"}
                cfg["hardware"] = {
                    "ram": ram,
                    "cores": str(cpus),
                    "disk_size": "128G",
                    "disk_type": "dynamic",
                    "disk_format": "qcow2",
                    "disk_ext": "qcow2",
                    "firmware": "uefi",
                    "chipset": "q35",
                    "secure_boot": "False",
                    "tpm": "False",
                    "boot_device": "disk",
                    "boot_order": json.dumps(["disk", "cdrom", "network"]),
                    "network_model": "e1000",
                    "audio_device": extra.get("audio_device") or "intel-hda",
                    "network_mode": "nat",
                    "network_interface": "",
                    "network_count": "1",
                    "graphics_mode": "auto",
                    "graphics_vram": "128M",
                    "network_devices": json.dumps([{
                        "name": "Red 1",
                        "model": "e1000",
                        "mode": "nat",
                        "interface": "",
                        "mac": self._new_qemu_mac(),
                    }]),
                    "passthrough_devices": json.dumps([]),
                }
                cfg["extra"] = {"data": json.dumps(extra, ensure_ascii=False)}
                with open(cfg_path, "w", encoding="utf-8") as f:
                    cfg.write(f)
                if hasattr(self, "_invalidate_vm_config_cache"):
                    self._invalidate_vm_config_cache(target_dir)
                progress_emit(100, self.tr("Importación completada."))
                log_emit(f"==> Importación macOS terminada: {target_dir}")
                log_emit("==> Al arrancar, la app usará OpenCore del "
                         "OSX-KVM del host y descargará el Recovery "
                         "automáticamente si hace falta.")
                return target_dir

            for i, d in enumerate(disks):
                if is_cancelled():
                    raise RuntimeError("Importaci\u00f3n cancelada por el usuario.")
                src_name = d.get("file") or ""
                if not src_name:
                    log_emit(f"[AVISO] Disco {i+1} sin archivo asociado; se omite.")
                    continue
                src_path = os.path.join(ovf_dir, src_name)
                if not os.path.isfile(src_path):
                    for cand in os.listdir(ovf_dir):
                        if cand.lower() == src_name.lower():
                            src_path = os.path.join(ovf_dir, cand)
                            break
                if not os.path.isfile(src_path):
                    log_emit(f"[AVISO] Archivo del disco no encontrado: {src_name}")
                    continue

                if import_config_only:
                    log_emit(f"==> Modo 'solo configuraci\u00f3n': se omite el disco {src_name}")
                    continue

                # ovf_ova_io_v1_import_diskname: preservar el nombre del
                # disco dentro del OVA (saneado, con deduplicación).
                _orig_stem, _orig_ext = os.path.splitext(src_name)
                _orig_stem = re.sub(
                    r"[^A-Za-z0-9._-]+", "_", _orig_stem or ""
                ).strip("._")
                if not _orig_stem:
                    _orig_stem = "disk0" if i == 0 else f"disk{i}"
                dst_name = _orig_stem + ".qcow2"
                if dst_name in _used_disk_names:
                    _k = 2
                    while f"{_orig_stem}_{_k}.qcow2" in _used_disk_names:
                        _k += 1
                    dst_name = f"{_orig_stem}_{_k}.qcow2"
                _used_disk_names.add(dst_name)
                dst_path = os.path.join(target_dir, dst_name)
                log_emit(f"==> Convirtiendo {src_name} -> {dst_name}...")

                try:
                    r = subprocess.run(
                        ["qemu-img", "info", "--output=json", src_path],
                        capture_output=True, text=True, timeout=15, check=True,
                    )
                    info = json.loads(r.stdout or "{}")
                    fmt_src = (info.get("format") or "").lower()
                except Exception:
                    fmt_src = ""
                if fmt_src == "qcow2":
                    _sh.copy2(src_path, dst_path)
                    if progress_emit:
                        progress_emit(-1, f"Copiando {dst_name}...")
                else:
                    ovf_io.convert_to_qcow2(
                        src_path, dst_path,
                        log_emit=log_emit,
                        progress_emit=progress_emit,
                        is_cancelled=is_cancelled,
                    )
                virtual_txt = "128G"
                try:
                    r = subprocess.run(
                        ["qemu-img", "info", "--output=json", dst_path],
                        capture_output=True, text=True, timeout=10, check=True,
                    )
                    info = json.loads(r.stdout or "{}")
                    vsize = int(info.get("virtual-size") or 0)
                    if vsize:
                        virtual_txt = f"{max(1, int(round(vsize / (1024**3))))}G"
                except Exception:
                    pass
                storage_devices.append({
                    "id": f"dev_{uuid.uuid4().hex[:12]}",
                    "name": _orig_stem or f"Disco {i+1}",
                    "device": "sata",
                    "type": "dynamic",
                    "format": "qcow2",
                    "size": virtual_txt,
                    "path": vm_paths.to_portable(target_dir, dst_path),
                    "existing": True,
                })

            progress_emit(80, "Escribiendo vm_config.ini...")

            # Construir vm_config.ini
            extra = {}
            if meta and isinstance(meta.get("vm_config"), dict):
                _vmcfg_g = meta["vm_config"]
                extra = dict(_vmcfg_g.get("extra") or {})
                # ovf_import_firmware_fix: los campos de hardware están
                # en el NIVEL SUPERIOR del meta. Sin este copiado, la VM
                # importada perdía 'firmware=uefi' y quedaba en BIOS,
                # por lo que no arrancaba (UEFI disk sin firmware UEFI).
                for _k in ("firmware", "chipset", "secure_boot", "tpm",
                           "graphics_mode", "graphics_vram",
                           "audio_device", "network_mode",
                           "boot_order"):
                    if _k in _vmcfg_g and _vmcfg_g[_k] is not None:
                        extra.setdefault(_k, _vmcfg_g[_k])
            # ovf_ova_vbox_uefi_v1_B: si el OVA no trae .virtmachine.json
            # (caso típico: viene de VirtualBox/VMware), pero el
            # descriptor declara firmware=efi en vbox:BIOSSettings,
            # respetarlo. Sin esto, cualquier OVA UEFI ajeno se importaba
            # como BIOS legacy.
            if not extra.get("firmware"):
                _fw_desc = str(ovf_data.get("firmware") or "").lower()
                if _fw_desc in ("uefi", "efi"):
                    extra["firmware"] = "uefi"
            os_type = user_os or "linux"
            if os_type == "linux":
                extra["distro"] = user_distro_or_ver or extra.get("distro") or ""
            elif os_type == "windows":
                extra["win_ver"] = user_distro_or_ver or extra.get("win_ver") or "Windows 10"
            elif os_type == "macos":
                extra["os_choice"] = user_distro_or_ver or extra.get("os_choice") or ""
            extra["storage_devices"] = storage_devices
            extra["cdrom_path"] = ""
            extra["imported_from_ovf"] = True

            cpus = int(ovf_data.get("cpus") or 0) or 2
            ram_gb = max(1, int(ovf_data.get("memory_mb") or 0) // 1024) or 4
            ram = f"{ram_gb}G"
            disk_size = "128G"
            if storage_devices:
                disk_size = storage_devices[0].get("size") or "128G"

            cfg_path = os.path.join(target_dir, "vm_config.ini")
            cfg = configparser.ConfigParser(interpolation=None)
            cfg["general"] = {"name": target_name, "os_type": os_type}
            cfg["hardware"] = {
                "ram": ram,
                "cores": str(cpus),
                "disk_size": disk_size,
                "disk_type": "dynamic",
                "disk_format": "qcow2",
                "disk_ext": "qcow2",
                "firmware": extra.get("firmware") or "bios",
                "chipset": extra.get("chipset") or "q35",
                "secure_boot": str(bool(extra.get("secure_boot"))),
                "tpm": str(bool(extra.get("tpm"))),
                "boot_device": "disk",
                "boot_order": json.dumps(["disk", "cdrom", "network"]),
                "network_model": "virtio-net-pci",
                "audio_device": extra.get("audio_device") or "intel-hda",
                "network_mode": extra.get("network_mode") or "nat",
                "network_interface": "",
                "network_count": "1",
                "graphics_mode": extra.get("graphics_mode") or "auto",
                "graphics_vram": extra.get("graphics_vram") or "256M",
                "network_devices": json.dumps([{
                    "name": "Red 1",
                    "model": "virtio-net-pci",
                    "mode": extra.get("network_mode") or "nat",
                    "interface": "",
                    "mac": self._new_qemu_mac(),
                }]),
                "passthrough_devices": json.dumps([]),
            }
            cfg["extra"] = {"data": json.dumps(extra, ensure_ascii=False)}
            with open(cfg_path, "w", encoding="utf-8") as f:
                cfg.write(f)
            if hasattr(self, "_invalidate_vm_config_cache"):
                self._invalidate_vm_config_cache(target_dir)

            progress_emit(100, "Importaci\u00f3n completada.")
            log_emit(f"==> Importaci\u00f3n terminada: {target_dir}")
            return target_dir
        finally:
            if cleanup_extract and extract_dir and os.path.isdir(extract_dir):
                try:
                    _sh.rmtree(extract_dir, ignore_errors=True)
                except Exception:
                    pass

# ovf_ova_io_v1_uuidfix
# ovf_progress_phases_v1
# ovf_ova_vbox_uefi_v1_B
# ovf_ova_io_v1_dialogtext
# ovf_ova_io_v1_disksize
# ovf_ova_io_v1_diskname
# ovf_ova_io_v1_import_diskname
# ovf_ova_io_v1_filefilter
# ovf_ova_io_v1_cdrom_export
# ovf_ova_io_v1_macos_export
# ovf_ova_io_v1_macos_import
# ovf_snapshots_opt_v1
# ovf_snapshots_opt_v1_helper
# ovf_snapshots_opt_v1_impl
# ovf_snapshots_opt_v1_impl
# vm_space_guard_v1
# vm_enospc_msg_v1
# _persist_android_iso_unified_v2

# vm_config_save_cancel_v1_dirty_2b1

# vm_config_save_cancel_v1_actions

# vm_config_save_cancel_v1_actions onchange
