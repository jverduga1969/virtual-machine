# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: modo compatibilidad de snapshots.

Marcador: snapshot_compat_v1

Cuando el flag extra["snapshot_compat"] esta activo en una VM:
  - Se fuerza VirtIO-GPU 2D o QXL al arrancar (VirGL/Venus usan la
    GPU del host, incompatible con savevm/snapshot-save).
  - Se omite el passthrough PCI/USB al arrancar (hardware fisico sin
    vmstate posible).
  - La UI de Pantalla y Passthrough se deshabilita con avisos claros.

Los discos RAW adjuntos tambien impiden snapshots completos, pero eso
se detecta en snapshots_mixin (readiness); aqui solo se avisa en el
tooltip del checkbox.

En macOS el flag no aplica: los 3 discos fijos de OSX-KVM lo hacen
inviable sin reescribir OSX-KVM. Se deshabilita con tooltip.
"""


class SnapshotCompatMixin:

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def _is_snapshot_compat_active(self):
        """True si el flag esta activo AHORA (combina checkbox y .ini)."""
        check = getattr(self, "check_snapshot_compat", None)
        if check is not None:
            try:
                return bool(check.isChecked())
            except Exception:
                pass
        if getattr(self, "current_vm_dir", None):
            try:
                data = self._load_vm_config_cached(self.current_vm_dir)
                return bool((data.get("extra") or {}).get("snapshot_compat"))
            except Exception:
                pass
        return False

    # ------------------------------------------------------------------
    # Slot del checkbox
    # ------------------------------------------------------------------
    def _on_snapshot_compat_toggled(self, checked):
        """Guarda el flag y reaplica toda la UI afectada."""
        if getattr(self, "current_vm_dir", None) and hasattr(self, "_save_hardware_lists"):
            try:
                self._save_hardware_lists()
            except Exception:
                pass
        self._apply_snapshot_compat_ui()
        try:
            self.log_message(
                "==> Modo compatibilidad de snapshots "
                + ("ACTIVADO. VirGL/Venus y passthrough quedarán "
                   "deshabilitados en esta VM."
                   if checked else "desactivado.")
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Aplicar el estado del flag a toda la UI
    # ------------------------------------------------------------------
    def _apply_snapshot_compat_ui(self):
        active = self._is_snapshot_compat_active()

        # ¿VNC embebido activo? Leer directo de los combos, no vía
        # _current_console_choice(): esa función (en console_ui_mixin.py)
        # puede leer de vm_config.ini u otra fuente que aún no refleja el
        # cambio recién hecho en el combo. Si eso pasa, vnc_on sale False
        # y esta función desbloquea VirGL/Venus aunque el usuario acabe
        # de elegir VNC. Los combos son la fuente de verdad instantánea.
        vnc_on = False
        try:
            _proto = self.combo_console_protocol.currentData()
            _mode = self.combo_console_mode.currentData()
            vnc_on = (_proto == "vnc" and _mode in ("embedded", "hybrid"))
        except Exception:
            # Fallback: si los combos no existen todavía (arranque), usar
            # la función auxiliar como última red.
            try:
                _p, _m = self._current_console_choice()
                vnc_on = (_p == "vnc" and _m in ("embedded", "hybrid"))
            except Exception:
                pass

        # --- 1) Combo Gráficos: deshabilitar VirGL/Venus ---
        combo = getattr(self, "combo_graphics", None)
        if combo is not None:
            incompatible = {"virgl", "venus"}
            model = combo.model()
            for i in range(combo.count()):
                data = combo.itemData(i)
                item = model.item(i)
                if item is None:
                    continue
                blocked = (
                    (active and data in incompatible)
                    or (vnc_on and data in incompatible)
                )
                try:
                    item.setEnabled(not blocked)
                except Exception:
                    pass
            cur = combo.currentData()
            if active and cur in incompatible:
                idx = combo.findData("auto")
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)

        # --- 2) Aviso en Pantalla ---
        notice = getattr(self, "label_snapshot_compat_notice", None)
        if notice is not None:
            if active:
                notice.setText(
                    "\u26a0 Modo compatibilidad de snapshots ACTIVADO: "
                    "VirGL y Venus están deshabilitados en esta VM porque "
                    "usan la GPU del host, incompatible con snapshots "
                    "completos (savevm). Para habilitarlos, desactiva el "
                    "modo en Configuración \u2192 Sistema."
                )
                notice.setVisible(True)
            else:
                notice.setVisible(False)

        # --- 3) Aviso + bloqueo en Passthrough ---
        pt_widgets = (
            "btn_passthrough_refresh",
            "btn_passthrough_apply",
            "btn_passthrough_hotplug",
            "btn_passthrough_unplug",
            "passthrough_tree",
            "btn_vfio_refresh",
            "btn_vfio_details",
            "btn_vfio_prepare",
            "btn_vfio_firmware",
        )
        prefix = "\u26a0 Deshabilitado en modo compatibilidad de snapshots.\n\n"
        for name in pt_widgets:
            w = getattr(self, name, None)
            if w is None:
                continue
            try:
                if active:
                    w.setEnabled(False)
                    if not w.toolTip().startswith("\u26a0 Deshabilitado en modo"):
                        w.setToolTip(prefix + w.toolTip())
                else:
                    w.setEnabled(True)
                    tip = w.toolTip()
                    if tip.startswith(prefix):
                        w.setToolTip(tip[len(prefix):])
            except Exception:
                pass

        pt_notice = getattr(self, "label_passthrough_snapshot_notice", None)
        if pt_notice is not None:
            pt_notice.setVisible(bool(active))

    # ------------------------------------------------------------------
    # Re-aplicar al cambiar el SO (macOS deshabilita el checkbox)
    # ------------------------------------------------------------------
    def _refresh_snapshot_compat_ui_on_os_change(self, *args):
        check = getattr(self, "check_snapshot_compat", None)
        if check is None:
            return
        try:
            is_macos = self.combo_main_os.currentData() == "macos"
        except Exception:
            is_macos = False
        if is_macos:
            check.setEnabled(False)
            check.setToolTip(
                "No aplicable a macOS: los 3 discos fijos de OSX-KVM "
                "(OpenCore + BaseSystem + MacHDD) no permiten snapshots "
                "completos sin reescribir OSX-KVM.\n\n"
                "Usa snapshots de disco (solo la capa QCOW2)."
            )
        else:
            check.setEnabled(True)
            check.setToolTip(
                "Cuando está activo, la VM se arranca en un modo que "
                "garantiza snapshots completos (RAM + dispositivos):\n"
                "  \u2022 Se fuerza VirtIO-GPU 2D o QXL al arrancar.\n"
                "  \u2022 Se omite el passthrough PCI/USB.\n"
                "  \u2022 Los discos RAW adjuntos pueden impedir el "
                "snapshot (se avisará al intentarlo).\n\n"
                "Al activarlo se deshabilitan las opciones incompatibles "
                "en Pantalla y Passthrough."
            )
        self._apply_snapshot_compat_ui()
