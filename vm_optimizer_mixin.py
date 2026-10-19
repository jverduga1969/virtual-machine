# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_optimizer_mixin.py — "Aplicar perfil" + candado global (vm_optimizer_v1).

Logica del boton "⚙ Aplicar perfil…" sobre una VM existente:

  1. Abre el dialogo VmOptimizerDialog (vm_optimizer_dialog.py).
  2. Si el usuario acepta, aplica el bloque 'advanced' del perfil a los
     widgets avanzados de Configuracion VM (graficos, CPU, memoria,
     topologia, consola, snapshot_compat).
  3. Aplica disk_io a todos los discos de la VM y clipboard al dict
     extra["clipboard"] + el combo de la pestana Comparticion.
  4. Persiste en extra:
         applied_profile    = profile_id
         profile_locked     = True
         profile_applied_at = ISO8601
  5. Cierra el candado: los widgets avanzados quedan de solo lectura.

El candado es global (un solo control). Al abrirlo y modificar
cualquier widget avanzado, el perfil pasa a "Personalizado" y el
candado no se vuelve a cerrar hasta que el usuario aplique otro
perfil.

Marcador: vm_optimizer_v1_mixin_impl.
"""

import json
import os
import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

import vm_profiles


class VmOptimizerMixin:
    # ------------------------------------------------------------------
    # Lista de widgets avanzados (candado + señales + aplicacion)
    # ------------------------------------------------------------------
    # Solo incluye los que el perfil controla. Los básicos (RAM, núcleos,
    # disco, placa) NO entran aqui: el perfil no los toca y el candado
    # no los bloquea.
    _ADVANCED_WIDGETS = (
        "combo_graphics",
        "combo_graphics_vram",
        "check_nested_virt",
        "check_hyperv_enlight",
        "check_virtio_rng",
        "check_virtio_balloon",
        "check_virtio_watchdog",
        "combo_virtio_watchdog_action",
        "check_mem_hugepages",
        "check_mem_prealloc",
        "check_mem_memfd_lock",
        "check_cpu_topology_manual",
        "spin_cpu_sockets",
        "spin_cpu_cores",
        "spin_cpu_threads",
        "combo_console_protocol",
        "combo_console_mode",
        "check_snapshot_compat",
    )

    # ==================================================================
    # 1) Lectura del estado actual (lo que el diálogo muestra en "Actual")
    # ==================================================================
    def _read_current_advanced_state(self):
        """Devuelve un dict con los valores avanzados ACTUALES.

        Lee de los widgets (lo que el usuario ve) y completa lo que
        falte desde el .ini (por si algún widget aún no existe).
        """
        out = {}

        def _combo(attr):
            w = getattr(self, attr, None)
            if w is None:
                return None
            try:
                return w.currentData()
            except Exception:
                return None

        def _check(attr):
            w = getattr(self, attr, None)
            if w is None:
                return None
            try:
                return bool(w.isChecked())
            except Exception:
                return None

        def _spin(attr):
            w = getattr(self, attr, None)
            if w is None:
                return None
            try:
                return int(w.value())
            except Exception:
                return None

        out["graphics_mode"]    = _combo("combo_graphics") or "auto"
        out["graphics_vram"]    = _combo("combo_graphics_vram") or "256M"
        out["nested_virt"]      = bool(_check("check_nested_virt"))
        out["hyperv_enlightenments"] = bool(_check("check_hyperv_enlight"))
        out["virtio_rng"]       = bool(_check("check_virtio_rng"))
        out["virtio_balloon"]   = bool(_check("check_virtio_balloon"))
        out["virtio_watchdog"]  = bool(_check("check_virtio_watchdog"))
        out["memory_tuning"] = {
            "hugepages":  bool(_check("check_mem_hugepages")),
            "prealloc":   bool(_check("check_mem_prealloc")),
            "memfd_lock": bool(_check("check_mem_memfd_lock")),
        }
        _topo_manual = bool(_check("check_cpu_topology_manual"))
        out["cpu_topology"] = {
            "mode": "manual" if _topo_manual else "auto",
            "sockets": _spin("spin_cpu_sockets") or 1,
            "cores":   _spin("spin_cpu_cores") or 2,
            "threads": _spin("spin_cpu_threads") or 1,
        }
        out["console_protocol"] = _combo("combo_console_protocol") or "vnc"
        out["console_mode"]     = _combo("combo_console_mode") or "embedded"
        out["snapshot_compat"]  = bool(_check("check_snapshot_compat"))

        # disk_io y clipboard se leen del .ini (no tienen widget
        # directo en Configuracion VM: disk_io va per-disco, clipboard
        # en la pestana Comparticion).
        out["disk_io"] = self._read_current_disk_io() or {
            "cache": "auto", "io": "auto", "aio": "auto",
            "discard": "auto", "detect_zeroes": "auto",
        }
        try:
            _clip_data = self._extra_load() or {}
            _clip = _clip_data.get("clipboard")
            if isinstance(_clip, dict):
                out["clipboard"] = _clip.get("mode") or "disabled"
            else:
                out["clipboard"] = "disabled"
        except Exception:
            out["clipboard"] = "disabled"
        return out

    def _read_current_disk_io(self):
        """Lee disk_io del primer disco no-cdrom del .ini (el resto se
        asume igual: el perfil es único por VM)."""
        if not self.current_vm_dir:
            return None
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
        except Exception:
            return None
        for d in ((data.get("extra") or {}).get("storage_devices") or []):
            if not isinstance(d, dict):
                continue
            if str(d.get("device") or "") not in ("sata", "nvme", "floppy"):
                continue
            return {
                "cache":         d.get("disk_cache")         or "auto",
                "io":            d.get("disk_io")            or "auto",
                "aio":           d.get("disk_aio")           or "auto",
                "discard":       d.get("disk_discard")       or "auto",
                "detect_zeroes": d.get("disk_detect_zeroes") or "auto",
            }
        return None

    # ==================================================================
    # 2) Apertura del diálogo
    # ==================================================================
    def open_vm_optimizer_dialog(self):
        """Slot del botón "⚙ Aplicar perfil…"."""
        if not self.current_vm_dir:
            QMessageBox.information(
                self, self.tr("Aplicar perfil"),
                self.tr("Selecciona primero una máquina virtual."))
            return
        try:
            from vm_optimizer_dialog import VmOptimizerDialog
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Aplicar perfil"),
                self.tr("No se pudo cargar el diálogo.\n\n{0}").format(e))
            return

        vm_name = os.path.basename(self.current_vm_dir)
        try:
            _data = self._load_vm_config_cached(self.current_vm_dir)
            os_type = str(_data.get("os_type") or "linux").lower()
        except Exception:
            os_type = "linux"

        current_state = self._read_current_advanced_state()
        try:
            _cur_profile = (self._extra_load() or {}).get("applied_profile")
        except Exception:
            _cur_profile = None

        dlg = VmOptimizerDialog(
            self, vm_name=vm_name, os_type=os_type,
            current_state=current_state,
            initial_profile=_cur_profile,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        pid = dlg.chosen_profile()
        if not pid:
            return
        self._apply_profile_advanced_to_vm(pid)

    # ==================================================================
    # 3) Aplicación del perfil
    # ==================================================================
    def _apply_profile_advanced_to_vm(self, profile_id):
        """Aplica el bloque advanced del perfil sobre la VM actual."""
        if not self.current_vm_dir:
            return
        try:
            _data = self._load_vm_config_cached(self.current_vm_dir)
            os_type = str(_data.get("os_type") or "linux").lower()
        except Exception:
            os_type = "linux"

        adv = vm_profiles.profile_advanced(profile_id, os_type)
        if adv is None:
            QMessageBox.warning(
                self, self.tr("Aplicar perfil"),
                self.tr("El perfil '{0}' no está disponible para este "
                        "sistema operativo.").format(profile_id))
            return

        vm_name = os.path.basename(self.current_vm_dir)
        n = 0

        # --- Widgets avanzados ---
        n += self._adv_set_combo("combo_graphics",
                                 adv.get("graphics_mode"))
        n += self._adv_set_combo("combo_graphics_vram",
                                 adv.get("graphics_vram"))
        n += self._adv_set_check("check_nested_virt",
                                 adv.get("nested_virt", False))
        n += self._adv_set_check("check_hyperv_enlight",
                                 adv.get("hyperv_enlightenments", False))
        n += self._adv_set_check("check_virtio_rng",
                                 adv.get("virtio_rng", False))
        n += self._adv_set_check("check_virtio_balloon",
                                 adv.get("virtio_balloon", False))
        n += self._adv_set_check("check_virtio_watchdog",
                                 adv.get("virtio_watchdog", False))

        mt = adv.get("memory_tuning") or {}
        if isinstance(mt, dict):
            n += self._adv_set_check("check_mem_hugepages",
                                     bool(mt.get("hugepages", False)))
            n += self._adv_set_check("check_mem_prealloc",
                                     bool(mt.get("prealloc", False)))
            n += self._adv_set_check("check_mem_memfd_lock",
                                     bool(mt.get("memfd_lock", False)))

        topo = adv.get("cpu_topology") or {}
        if isinstance(topo, dict):
            _manual = str(topo.get("mode") or "auto").lower() == "manual"
            n += self._adv_set_check("check_cpu_topology_manual", _manual)
            n += self._adv_set_spin("spin_cpu_sockets",
                                    topo.get("sockets") or 1)
            n += self._adv_set_spin("spin_cpu_cores",
                                    topo.get("cores") or 2)
            n += self._adv_set_spin("spin_cpu_threads",
                                    topo.get("threads") or 1)
            try:
                w = getattr(self, "_cpu_topo_widget", None)
                if w is not None:
                    w.setVisible(_manual)
            except Exception:
                pass

        n += self._adv_set_combo("combo_console_protocol",
                                 adv.get("console_protocol"))
        n += self._adv_set_combo("combo_console_mode",
                                 adv.get("console_mode"))
        n += self._adv_set_check("check_snapshot_compat",
                                 adv.get("snapshot_compat", False))

        # Refrescos visuales que dependen del estado.
        for _fn in ("_refresh_snapshot_compat_ui_on_os_change",
                    "_refresh_hugepages_status",
                    "_refresh_cpu_topology_total",
                    "_refresh_auto_graphics_label"):
            try:
                f = getattr(self, _fn, None)
                if callable(f):
                    f()
            except Exception:
                pass
        # El watchdog tiene un combo de accion que se habilita/deshabilita
        # segun su checkbox.
        try:
            f = getattr(self, "_on_virtio_watchdog_changed", None)
            if callable(f):
                f()
        except Exception:
            pass

        # --- disk_io a todos los discos ---
        _dio = adv.get("disk_io")
        if isinstance(_dio, dict):
            try:
                self._apply_disk_io_to_all_disks(_dio)
            except Exception as _dio_err:
                try:
                    self.log_message(
                        f"[AVISO] Aplicar perfil: disk_io no aplicado: "
                        f"{_dio_err}")
                except Exception:
                    pass

        # --- clipboard ---
        _clip = adv.get("clipboard")
        if _clip:
            try:
                self._apply_clipboard_to_vm(_clip)
            except Exception as _clip_err:
                try:
                    self.log_message(
                        f"[AVISO] Aplicar perfil: clipboard no aplicado: "
                        f"{_clip_err}")
                except Exception:
                    pass

        # --- Persistir en extra ---
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._extra_apply({
            "applied_profile":    profile_id,
            "profile_locked":     True,
            "profile_applied_at": now_iso,
        })
        try:
            self._save_hardware_lists()
        except Exception:
            pass

        # --- UI: candado + indicador ---
        self._set_profile_lock(True, save=False)
        self._update_profile_indicator()
        try:
            self._on_config_dirty()
        except Exception:
            pass

        try:
            self.log_message(
                f"==> Perfil '{profile_id}' aplicado a '{vm_name}' "
                f"({n} widget(s) avanzados + disk_io + clipboard).")
        except Exception:
            pass
        QMessageBox.information(
            self, self.tr("Aplicar perfil"),
            self.tr("Perfil <b>{0}</b> aplicado a <b>{1}</b>.<br><br>"
                    "Los ajustes avanzados se han actualizado y el "
                    "candado se ha cerrado. Pulsa "
                    "<b>💾 Guardar configuración</b> para persistir "
                    "los cambios en disco.").format(profile_id, vm_name))

    # ------------------------------------------------------------------
    # Helpers de escritura en widgets (con blockSignals para no
    # disparar auto-save antes de tiempo)
    # ------------------------------------------------------------------
    def _adv_set_check(self, attr, value):
        w = getattr(self, attr, None)
        if w is None:
            return 0
        try:
            w.blockSignals(True)
            w.setChecked(bool(value))
            w.blockSignals(False)
            return 1
        except Exception:
            return 0

    def _adv_set_combo(self, attr, value):
        w = getattr(self, attr, None)
        if w is None or value is None:
            return 0
        try:
            idx = w.findData(value)
            if idx < 0:
                return 0
            w.blockSignals(True)
            w.setCurrentIndex(idx)
            w.blockSignals(False)
            return 1
        except Exception:
            return 0

    def _adv_set_spin(self, attr, value):
        w = getattr(self, attr, None)
        if w is None:
            return 0
        try:
            v = int(value) if value is not None else 1
        except Exception:
            return 0
        try:
            w.blockSignals(True)
            w.setValue(v)
            w.blockSignals(False)
            return 1
        except Exception:
            return 0

    # ==================================================================
    # 4) disk_io a todos los discos
    # ==================================================================
    def _apply_disk_io_to_all_disks(self, dio):
        """Escribe los campos disk_* en storage_devices[i] de todos los
        discos. Los valores 'auto' se borran (vuelta al default)."""
        if not self.current_vm_dir or not isinstance(dio, dict):
            return
        devices = self._storage_devices_all(self.current_vm_dir)
        touched = 0
        for d in devices:
            if not isinstance(d, dict):
                continue
            if str(d.get("device") or "") not in ("sata", "nvme", "floppy"):
                continue
            for src, dst in (
                ("cache",         "disk_cache"),
                ("io",            "disk_io"),
                ("aio",           "disk_aio"),
                ("discard",       "disk_discard"),
                ("detect_zeroes", "disk_detect_zeroes"),
            ):
                val = dio.get(src)
                if val is None:
                    continue
                if str(val).lower() == "auto":
                    d.pop(dst, None)
                else:
                    d[dst] = str(val)
            touched += 1
        if touched:
            self._write_storage_devices(devices)
            try:
                self.refresh_storage_ui()
            except Exception:
                pass

    # ==================================================================
    # 5) clipboard
    # ==================================================================
    def _apply_clipboard_to_vm(self, mode):
        """Actualiza extra['clipboard']['mode'] y el combo de la pestaña
        Compartición (si existe)."""
        if not self.current_vm_dir:
            return
        if mode in ("none", "disabled"):
            _mode = "disabled"
        else:
            _mode = str(mode)
        # 1) extra
        self._extra_apply({
            "clipboard": {"mode": _mode},
        })
        # 2) combo de la pestaña Compartición
        cmb = getattr(self, "clipboard_mode", None)
        if cmb is not None:
            try:
                idx = cmb.findData(_mode)
                if idx >= 0:
                    cmb.blockSignals(True)
                    cmb.setCurrentIndex(idx)
                    cmb.blockSignals(False)
            except Exception:
                pass

    # ==================================================================
    # 6) helpers extra (leer/escribir el dict extra del .ini)
    # ==================================================================
    def _extra_load(self):
        """Devuelve el dict extra del .ini actual (o {} si no hay)."""
        if not self.current_vm_dir:
            return {}
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
        except Exception:
            return {}
        return dict((data or {}).get("extra") or {})

    def _extra_apply(self, updates):
        """Actualiza varias claves del dict extra y persiste el .ini."""
        if not self.current_vm_dir or not isinstance(updates, dict):
            return
        import configparser as _cfg
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        c = _cfg.ConfigParser(interpolation=None)
        c.read(cfg_path, encoding="utf-8")
        if not c.has_section("extra"):
            c.add_section("extra")
        try:
            extra = json.loads(c["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        for k, v in updates.items():
            extra[k] = v
        c.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(self.current_vm_dir)

    # ==================================================================
    # 7) Candado global
    # ==================================================================
    def _set_profile_lock(self, locked, save=True):
        """Activa/desactiva el candado global de los widgets avanzados.

        locked=True  → widgets en solo lectura + botón candado 🔒.
        locked=False → widgets editables + botón candado 🔓.

        Marcador: vm_optimizer_v1_mixin_impl.
        """
        self._profile_locked = bool(locked)
        for attr in self._ADVANCED_WIDGETS:
            w = getattr(self, attr, None)
            if w is None:
                continue
            try:
                w.setEnabled(not self._profile_locked)
            except Exception:
                pass
        # El combo de accion del watchdog respeta su checkbox.
        try:
            wd_chk = getattr(self, "check_virtio_watchdog", None)
            wd_act = getattr(self, "combo_virtio_watchdog_action", None)
            if wd_chk is not None and wd_act is not None:
                wd_act.setEnabled(
                    (not self._profile_locked) and wd_chk.isChecked())
        except Exception:
            pass
        self._update_profile_lock_button()
        if save and self.current_vm_dir:
            self._extra_apply({"profile_locked": self._profile_locked})

    def _toggle_profile_lock(self):
        """Slot del botón 🔒/🔓."""
        if not self.current_vm_dir:
            QMessageBox.information(
                self, self.tr("Candado del perfil"),
                self.tr("Selecciona primero una máquina virtual."))
            return
        _cur = bool(getattr(self, "_profile_locked", False))
        self._set_profile_lock(not _cur, save=True)
        try:
            self.log_message(
                "==> Perfil: candado "
                + ("CERRADO." if not _cur else "ABIERTO (edición libre)."))
        except Exception:
            pass

    def _update_profile_lock_button(self):
        """Actualiza icono y tooltip del botón candado."""
        btn = getattr(self, "btn_profile_lock", None)
        if btn is None:
            return
        locked = bool(getattr(self, "_profile_locked", False))
        try:
            btn.setText("🔒" if locked else "🔓")
            btn.setToolTip(
                self.tr("Candado del perfil: CERRADO.\n"
                        "Los ajustes avanzados están en solo lectura.\n"
                        "Púlsalo para editar libremente.")
                if locked else
                self.tr("Candado del perfil: ABIERTO.\n"
                        "Puedes editar los ajustes avanzados. Al hacerlo, "
                        "el perfil pasará a 'Personalizado'.")
            )
            btn.setStyleSheet(
                "QToolButton { font-size:16px; padding:2px 6px;"
                " border:1px solid palette(mid); border-radius:5px; }"
                if not locked else
                "QToolButton { font-size:16px; padding:2px 6px;"
                " border:1px solid #c62828; border-radius:5px;"
                " background:#fff3cd; }"
            )
        except Exception:
            pass

    # ==================================================================
    # 8) Detección de modificación con el candado abierto
    # ==================================================================
    def _wire_advanced_widgets_signals(self):
        """Conecta las señales de los widgets avanzados al slot
        _on_advanced_widget_changed. Idempotente."""
        if getattr(self, "_advanced_signals_wired", False):
            return
        self._advanced_signals_wired = True
        pairs = (
            ("combo_graphics",              "currentIndexChanged"),
            ("combo_graphics_vram",         "currentIndexChanged"),
            ("check_nested_virt",           "stateChanged"),
            ("check_hyperv_enlight",        "stateChanged"),
            ("check_virtio_rng",            "stateChanged"),
            ("check_virtio_balloon",        "stateChanged"),
            ("check_virtio_watchdog",       "stateChanged"),
            ("combo_virtio_watchdog_action","currentIndexChanged"),
            ("check_mem_hugepages",         "stateChanged"),
            ("check_mem_prealloc",          "stateChanged"),
            ("check_mem_memfd_lock",        "stateChanged"),
            ("check_cpu_topology_manual",   "stateChanged"),
            ("spin_cpu_sockets",            "valueChanged"),
            ("spin_cpu_cores",              "valueChanged"),
            ("spin_cpu_threads",            "valueChanged"),
            ("combo_console_protocol",      "currentIndexChanged"),
            ("combo_console_mode",          "currentIndexChanged"),
            ("check_snapshot_compat",       "stateChanged"),
        )
        slot = self._on_advanced_widget_changed
        for attr, sig in pairs:
            w = getattr(self, attr, None)
            if w is None:
                continue
            try:
                getattr(w, sig).connect(slot)
            except Exception:
                pass

    def _on_advanced_widget_changed(self, *_args):
        """Slot. Si el candado está abierto, pasa el perfil a
        'Personalizado'. Si está cerrado, no hace nada (los widgets
        están deshabilitados, así que no debería llegar aquí, pero
        por si acaso)."""
        if not self.current_vm_dir:
            return
        if bool(getattr(self, "_profile_locked", True)):
            return
        _cur = getattr(self, "_applied_profile", None)
        if _cur in (None, "Personalizado"):
            return
        self._applied_profile = "Personalizado"
        try:
            self._extra_apply({
                "applied_profile": "Personalizado",
                # El candado NO se vuelve a cerrar automáticamente.
                "profile_locked": False,
            })
        except Exception:
            pass
        self._update_profile_indicator()
        try:
            self.log_message(
                "==> Perfil cambiado a 'Personalizado' (edición manual).")
        except Exception:
            pass

    # ==================================================================
    # 9) Indicador de perfil (pestaña Resumen)
    # ==================================================================
    def _update_profile_indicator(self):
        """Actualiza el chip de perfil (barra Config VM) y el
        label del Resumen.

        Marcador: vm_optimizer_v1_profile_chip.

        Chip (self.config_bar_profile_label): visible junto al
        titulo de Configuracion VM. Estilo pastilla, azul cuando
        hay perfil aplicado, ambar cuando es 'Personalizado'.

        Label del Resumen (self.manager_profile_label): sigue
        actualizandose por compatibilidad; menos visible.
        """
        # --- Resolver texto segun el estado ---
        pid = getattr(self, "_applied_profile", None) if self.current_vm_dir else None
        if not self.current_vm_dir or not pid:
            chip_txt = ""
            chip_style = ""
            resumen_txt = ""
        else:
            locked = bool(getattr(self, "_profile_locked", False))
            if pid == "Personalizado":
                chip_txt = self.tr("📌 Personalizado")
                chip_style = (
                    "QLabel { "
                    "  background: #fff8e1; "
                    "  color: #7a5b00; "
                    "  border: 1px solid #ffe082; "
                    "  border-radius: 10px; "
                    "  padding: 2px 10px; "
                    "  font-weight: bold; "
                    "  font-size: 11px; "
                    "}"
                )
                resumen_txt = self.tr("⚙ Perfil: Personalizado")
            else:
                try:
                    label = vm_profiles.profile_label(pid)
                except Exception:
                    label = str(pid)
                _lock_glyph = "🔒" if locked else "🔓"
                chip_txt = self.tr("📌 {0}  {1}").format(
                    label, _lock_glyph)
                chip_style = (
                    "QLabel { "
                    "  background: #e3f2fd; "
                    "  color: #0d47a1; "
                    "  border: 1px solid #90caf9; "
                    "  border-radius: 10px; "
                    "  padding: 2px 10px; "
                    "  font-weight: bold; "
                    "  font-size: 11px; "
                    "}"
                )
                resumen_txt = self.tr("⚙ Perfil: {0}{1}").format(
                    label, "  🔒" if locked else "")

        # --- Chip en la barra de Config VM ---
        chip = getattr(self, "config_bar_profile_label", None)
        if chip is not None:
            try:
                chip.setText(chip_txt)
                if chip_style:
                    chip.setStyleSheet(chip_style)
                chip.setVisible(bool(chip_txt))
                chip.setToolTip(
                    self.tr("Pulsa \"⚙ Aplicar perfil…\" para cambiar "
                            "o el candado para editar sin cambiar de "
                            "perfil.")
                    if chip_txt else ""
                )
            except Exception:
                pass

        # --- Label del Resumen (compatibilidad) ---
        lbl = getattr(self, "manager_profile_label", None)
        if lbl is not None:
            try:
                lbl.setText(resumen_txt)
                lbl.setVisible(bool(resumen_txt))
            except Exception:
                pass

    # ==================================================================
    # 10) Cargar el estado del perfil al abrir una VM
    # ==================================================================
    def _load_profile_state_from_extra(self, extra):
        """Se llama desde open_vm tras cargar el .ini. Restaura
        applied_profile, profile_locked y el candado."""
        extra = extra or {}
        pid = extra.get("applied_profile")
        locked = bool(extra.get("profile_locked", False))
        self._applied_profile = pid if pid else None
        # Si hay perfil aplicado, respetar el candado; si no, abierto.
        self._profile_locked = bool(locked) if pid else False
        self._set_profile_lock(self._profile_locked, save=False)
        self._update_profile_indicator()


# vm_optimizer_v1_mixin_impl
