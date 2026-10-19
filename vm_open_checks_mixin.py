# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_open_checks_mixin.py — deteccion de estado invalido al abrir VM.

Marcador: vm_open_state_checks_v1.

Al abrir una VM se comprueban tres cosas:

  1. Limites de bus de disco (disk_bus.validate_disk_bus_limits).
     Ejemplo: 5 discos SATA cuando el controlador admite 4.

  2. Archivos de disco que no existen en el host. Discos registrados
     en storage_devices cuyo archivo no esta en el disco del host
     (tipico tras mover la VM sin llevarse todo).

  3. Firmware UEFI sin OVMF instalado (host_deps.ovmf_available).
     La VM no arrancaria; avisamos antes de que el usuario pulse
     Iniciar.

Los avisos se muestran en un banner amarillo en la pestana Resumen
con un boton "Ir a Almacenamiento", y se registran como [AVISO] en la
Consola de Progreso. NO bloquean nada: el usuario puede intentar
arrancar igualmente.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class VmOpenChecksMixin:
    # ------------------------------------------------------------------
    # Punto de entrada: se llama desde open_vm.
    # ------------------------------------------------------------------
    def _check_vm_state_on_open(self, vm_dir, data=None):
        """Devuelve lista de strings con avisos, o [] si todo OK."""
        warnings = []
        if not vm_dir or not os.path.isdir(vm_dir):
            return warnings
        try:
            if data is None:
                data = self._load_vm_config_cached(vm_dir)
        except Exception:
            data = {}

        extra = (data or {}).get("extra") or {}
        devices = extra.get("storage_devices") or []
        if not isinstance(devices, list):
            devices = []

        os_type = str((data or {}).get("os_type") or "linux").lower()
        win_ver = ""
        if os_type == "windows":
            win_ver = str(extra.get("win_ver") or "")
        chipset = str((data or {}).get("chipset") or "q35").lower()
        chipset_q35 = (chipset == "q35")

        # 1) Limites de bus.
        try:
            import disk_bus
            cdroms = sum(
                1 for d in devices
                if isinstance(d, dict)
                and str(d.get("device") or "").lower() == "cdrom"
            )
            errs = disk_bus.validate_disk_bus_limits(
                devices, os_type=os_type, win_ver=win_ver,
                chipset_is_q35=chipset_q35, cdroms_count=cdroms,
            )
            for e in errs:
                warnings.append("Bus de disco: " + str(e))
        except Exception:
            pass

        # 2) Archivos de disco inexistentes.
        try:
            import vm_paths
            for d in devices:
                if not isinstance(d, dict):
                    continue
                typ = str(d.get("device") or "").lower()
                if typ == "cdrom":
                    continue
                p = str(d.get("path") or "")
                if not p:
                    continue
                try:
                    p_abs = vm_paths.to_absolute(vm_dir, p)
                except Exception:
                    p_abs = p
                if p_abs and not os.path.exists(p_abs):
                    nm = d.get("name") or os.path.basename(p_abs) or "?"
                    warnings.append(
                        "Disco '{0}': el archivo no existe en el host "
                        "({1}).".format(nm, p_abs)
                    )
        except Exception:
            pass

        # 3) Firmware UEFI sin OVMF.
        try:
            fw = str((data or {}).get("firmware") or "bios").lower()
            if fw == "uefi":
                import host_deps
                _ok = True
                try:
                    _ok = bool(host_deps.ovmf_available())
                except Exception:
                    _ok = True  # sin informacion no avisamos
                if not _ok:
                    warnings.append(
                        "Firmware UEFI seleccionado, pero OVMF no "
                        "esta instalado en el host. La VM no arrancara."
                    )
        except Exception:
            pass

        return warnings

    # ------------------------------------------------------------------
    # Banner en Resumen + log en Consola
    # ------------------------------------------------------------------
    def _update_vm_issues_banner(self, warnings):
        """Muestra u oculta el banner de avisos."""
        widget = getattr(self, "manager_issues_banner", None)
        if widget is None:
            return
        warnings = [str(w) for w in (warnings or []) if w]
        if not warnings:
            try:
                widget.setVisible(False)
            except Exception:
                pass
            lbl = getattr(self, "manager_issues_label", None)
            if lbl is not None:
                try:
                    lbl.setText("")
                except Exception:
                    pass
            return

        # HTML del banner.
        html = ("<b>\u26a0 " + self.tr("Avisos al abrir esta VM")
                + "</b><ul style='margin:4px 0 0 18px;padding:0;'>")
        for w in warnings:
            html += "<li>" + w + "</li>"
        html += "</ul>"

        lbl = getattr(self, "manager_issues_label", None)
        if lbl is not None:
            try:
                lbl.setText(html)
            except Exception:
                pass
        try:
            widget.setVisible(True)
        except Exception:
            pass

        # Log en la Consola de Progreso.
        try:
            _vm_name = (os.path.basename(self.current_vm_dir)
                        if self.current_vm_dir else "?")
            for w in warnings:
                self.log_message(
                    "[AVISO] VM '{0}': {1}".format(_vm_name, w))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Boton "Ir a Almacenamiento"
    # ------------------------------------------------------------------
    def _on_vm_issues_goto_storage(self):
        """Salta a Configuracion VM -> Almacenamiento."""
        try:
            if (hasattr(self, "main_tabs")
                    and hasattr(self, "config_tab_container")):
                idx = self.main_tabs.indexOf(self.config_tab_container)
                if idx >= 0:
                    self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass
        try:
            if hasattr(self, "_goto_storage_section"):
                self._goto_storage_section()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Construccion del banner (se llama desde virtual_machine.py)
    # ------------------------------------------------------------------
    def _build_vm_issues_banner(self):
        """Construye el QFrame del banner. Devuelve el widget para que
        el llamador lo inserte en el layout del Resumen."""
        self.manager_issues_banner = QFrame()
        self.manager_issues_banner.setObjectName("vmIssuesBox")
        self.manager_issues_banner.setFrameShape(QFrame.Shape.NoFrame)

        _lay = QVBoxLayout(self.manager_issues_banner)
        _lay.setContentsMargins(10, 8, 10, 8)
        _lay.setSpacing(4)

        self.manager_issues_label = QLabel("")
        self.manager_issues_label.setWordWrap(True)
        self.manager_issues_label.setTextFormat(Qt.TextFormat.RichText)
        self.manager_issues_label.setStyleSheet(
            "background: transparent; color: #7a5b00; font-size: 11px;")
        _lay.addWidget(self.manager_issues_label)

        _row = QHBoxLayout()
        self.btn_vm_issues_goto_storage = QPushButton(
            self.tr("\U0001F4C2 Ir a Almacenamiento"))
        self.btn_vm_issues_goto_storage.setToolTip(self.tr(
            "Abre Configuracion VM -> Almacenamiento, donde puedes "
            "anadir, quitar o modificar discos."))
        self.btn_vm_issues_goto_storage.clicked.connect(
            self._on_vm_issues_goto_storage)
        _row.addWidget(self.btn_vm_issues_goto_storage)
        _row.addStretch(1)
        _lay.addLayout(_row)

        self.manager_issues_banner.setStyleSheet(
            "QFrame#vmIssuesBox { "
            "  background: #fff8e1; "
            "  border: 1px solid #ffe082; "
            "  border-radius: 6px; "
            "}"
            "QFrame#vmIssuesBox QLabel { background: transparent; }"
            "QFrame#vmIssuesBox QPushButton { padding: 3px 10px; }"
        )
        self.manager_issues_banner.setVisible(False)
        return self.manager_issues_banner

    # ------------------------------------------------------------------
    # Limpiar el banner al cambiar de VM o crear una nueva.
    # ------------------------------------------------------------------
    def _clear_vm_issues_banner(self):
        try:
            self._update_vm_issues_banner([])
        except Exception:
            pass


# vm_open_state_checks_v1
