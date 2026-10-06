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
        """Marca el flag como pendiente y reaplica toda la UI afectada."""
        # vm_config_save_cancel_v1_dirty_2b1: no persistir aquí.
        # snapshot_compat forma parte del Grupo A; se guarda al pulsar
        # "💾 Guardar configuración". El flag solo se lee al arrancar
        # la VM, así que no hay consumidores en caliente que dependan
        # de que esté persistido durante la edición.
        if getattr(self, "current_vm_dir", None):
            try:
                self._on_config_dirty()
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
    def _macos_version_supports_qxl(self):
        """macos_graphics_per_version_v1: True si la version de macOS
        seleccionada soporta QXL (Catalina 10.15+).

        Apple incluye driver QXL desde macOS 10.15. High Sierra
        (10.13) y Mojave (10.14) NO lo tienen: si se elige QXL, la
        pantalla queda negra o a resolucion minima al cargar el
        framebuffer de macOS.

        Si no podemos determinar la version (widget ausente o combo
        vacio), devolvemos False: se aplica el bloqueo conservador.
        """
        if not hasattr(self, "combo_macos_ver"):
            return False
        try:
            txt = (self.combo_macos_ver.currentText() or "").lower()
        except Exception:
            return False
        # High Sierra (10.13) y Mojave (10.14) NO soportan QXL.
        if "10.13" in txt or "10.14" in txt:
            return False
        if "high sierra" in txt or "mojave" in txt:
            return False
        # Si el combo esta vacio o sin seleccion, conservador.
        if not txt.strip():
            return False
        # Todo lo demas (Catalina 10.15 en adelante) si.
        return True

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

        # --- 1) Combo Gráficos: deshabilitar opciones incompatibles ---
        # Marcador: macos_graphics_ui_v1 (extendido a este mixin)
        #
        # Este loop es la ÚLTIMA palabra sobre el estado de los items
        # del combo Gráficos. Combina tres condiciones de bloqueo:
        #   • snapshot_compat activo     -> VirGL/Venus
        #   • VNC embebido / híbrido     -> VirGL/Venus
        #   • macOS                      -> VirGL/Venus/QXL/VMware/
        #                                   VirtIO/Headless
        # "Automático" NUNCA se bloquea: siempre es el fallback.
        #
        # Nota histórica: la restricción macOS vivía también en
        # virtual_machine._apply_macos_graphics_restrictions, pero
        # este loop la pisaba al reejecutarse (open_vm llama a
        # _refresh_snapshot_compat_ui_on_os_change después de
        # update_graphics_options). Centralizar aquí evita el
        # pisado y futuras regresiones si otro mixin toca el combo.
        try:
            _is_macos = self.combo_main_os.currentData() == "macos"
        except Exception:
            _is_macos = False

        combo = getattr(self, "combo_graphics", None)
        if combo is not None:
            _gl_blocked = {"virgl", "venus"}
            # macos_graphics_per_version_v1: QXL es funcional a
            # partir de macOS 10.15 (Catalina). En High Sierra y
            # Mojave solo VGA generico.
            _macos_old = _is_macos and not self._macos_version_supports_qxl()
            if _macos_old:
                _macos_blocked = {"qxl", "vmware", "vmware-svga",
                                  "virtio", "none"}
            else:
                _macos_blocked = {"vmware", "vmware-svga",
                                  "virtio", "none"}
            _macos_tooltips = {
                "qxl": (
                    "QXL no tiene driver para macOS. OpenCore puede "
                    "mostrar el selector de arranque, pero cuando "
                    "macOS carga su framebuffer la pantalla se queda "
                    "en negro o a resolución mínima.\n\n"
                    "Usa 'Automático' (VGA genérico): único modelo "
                    "que macOS reconoce sin driver externo."
                ),
                "vmware": (
                    "VMware SVGA II no tiene driver nativo en macOS "
                    "sobre QEMU. El driver de darwin.iso (VMware "
                    "Tools) está diseñado para hardware VMware real, "
                    "y QEMU no implementa todas las capacidades que "
                    "ese driver espera (alpha cursor, pitchlock...).\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
                "vmware-svga": (
                    "VMware SVGA II no tiene driver nativo en macOS "
                    "sobre QEMU.\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
                "virtio": (
                    "VirtIO-GPU no tiene driver para macOS: la "
                    "pantalla no se inicializa.\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
                "none": (
                    "Sin video: OpenCore necesita mostrar su "
                    "selector de arranque en pantalla.\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
                "virgl": (
                    "macOS no usa un backend de pantalla con OpenGL "
                    "activo; VirGL no puede funcionar aquí.\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
                "venus": (
                    "macOS no usa un backend de pantalla con OpenGL "
                    "activo; Venus no puede funcionar aquí.\n\n"
                    "Usa 'Automático' (VGA genérico)."
                ),
            }
            model = combo.model()
            for i in range(combo.count()):
                data = combo.itemData(i)
                item = model.item(i)
                if item is None:
                    continue
                blocked = False
                if data in _gl_blocked and (active or vnc_on):
                    blocked = True
                if _is_macos and data in (_gl_blocked | _macos_blocked):
                    blocked = True
                try:
                    item.setEnabled(not blocked)
                except Exception:
                    pass
                if _is_macos and data in _macos_tooltips:
                    # macos_graphics_per_version_v1: en Catalina+
                    # QXL no lleva tooltip de bloqueo. Limpiamos
                    # el que hubiera quedado de una version previa.
                    if data == "qxl" and not _macos_old:
                        try:
                            combo.setItemData(i, "", 3)
                        except Exception:
                            pass
                    else:
                        try:
                            combo.setItemData(i, _macos_tooltips[data], 3)
                        except Exception:
                            pass
            cur = combo.currentData()
            _fallback = False
            if active and cur in _gl_blocked:
                _fallback = True
            if _is_macos and cur in (_gl_blocked | _macos_blocked):
                _fallback = True
            if _fallback and cur != "auto":
                idx = combo.findData("auto")
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)
        # macos_graphics_refresh_label_v1: recalcular el texto del
        # item 'Automatico' del combo Graficos. Sin esto, en macOS
        # Catalina+ el texto del label no se actualiza al cambiar la
        # version en vivo (solo cuando el fallback lo fuerza, que
        # ocurre con High Sierra y Mojave).
        try:
            self._refresh_auto_graphics_label()
        except Exception:
            pass

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

# vm_config_save_cancel_v1_dirty_2b1
