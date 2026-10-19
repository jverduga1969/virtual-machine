# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""quick_create_mixin.py — integracion del Modo Rapido.

Marcador: quick_create_v1_mixin
"""


import os  # vm_optimizer_v1_quick_import_os


class QuickCreateMixin:
    def open_quick_create(self):
        from PyQt6.QtWidgets import QDialog
        from quick_create_dialog import QuickCreateDialog
        host_ram_mb = int(getattr(self, "physical_ram_gb", 8)) * 1024
        host_cores = max(2, int(getattr(self, "physical_cores", 4)))
        macos_versions = [name for name, _ in getattr(self, "os_options", [])]
        dlg = QuickCreateDialog(parent=self, host_ram_mb=host_ram_mb,
                                host_cores=host_cores,
                                macos_versions=macos_versions or None)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.result_data()
        self._populate_from_quick_create(data)
        # quick_create_v1_materialize: crear carpeta + .ini +
        # disco + unidad Principal ya, para que Configuracion ->
        # Almacenamiento los muestre al cerrar el wizard.
        self._materialize_quick_create(data)

    def _populate_from_quick_create(self, data):
        self.new_vm()
        try:
            self.input_vm_name.setText(data.get("name", ""))
        except Exception:
            pass
        platform = data.get("platform") or "linux"
        try:
            idx = self.combo_main_os.findData(platform)
            if idx >= 0:
                self.combo_main_os.setCurrentIndex(idx)
        except Exception:
            pass
        os_name = data.get("os_name") or ""
        try:
            if platform == "linux":
                self.combo_lin_distro.setCurrentText(os_name)
            elif platform == "windows":
                self.combo_win_ver.setCurrentText(os_name)
            elif platform == "macos":
                for i in range(self.combo_macos_ver.count()):
                    txt = self.combo_macos_ver.itemText(i)
                    if txt.startswith(os_name):
                        self.combo_macos_ver.setCurrentIndex(i)
                        break
        except Exception:
            pass
        try:
            ram_gb = int(str(data.get("ram", "4G")).rstrip("G"))
            if ram_gb % 2:
                ram_gb += 1
            ram_gb = max(self.slider_ram.minimum(),
                         min(self.slider_ram.maximum(), ram_gb))
            self.slider_ram.setValue(ram_gb)
        except Exception:
            pass
        try:
            cores = int(data.get("cores", 2))
            if cores % 2:
                cores += 1
            cores = max(self.slider_cores.minimum(),
                        min(self.slider_cores.maximum(), cores))
            self.slider_cores.setValue(cores)
        except Exception:
            pass
        try:
            self.disk_size_setting = f"{int(data.get('disk_gb', 40))}G"
        except Exception:
            pass
        # Graficos del perfil (graphics_mode_by_profile).
        try:
            gm = data.get("graphics_mode", "")
            if gm:
                idx = self.combo_graphics.findData(gm)
                if idx >= 0:
                    self.combo_graphics.setCurrentIndex(idx)
        except Exception:
            pass
        try:
            gv = data.get("graphics_vram", "")
            if gv:
                idx = self.combo_graphics_vram.findData(gv)
                if idx >= 0:
                    self.combo_graphics_vram.setCurrentIndex(idx)
        except Exception:
            pass
        # vm_optimizer_v1_quick: volcar a los widgets los campos
        # avanzados del perfil (rng, balloon, watchdog, memoria,
        # topologia, consola, snapshot_compat). Va despues de los
        # basicos y antes de guardar el pending.
        try:
            self._apply_advanced_from_quick(data)
        except Exception as _adv_err:
            try:
                self.log_message(
                    "[AVISO] Modo Rapido: avanzados no aplicados: "
                    + str(_adv_err))
            except Exception:
                pass
        self._pending_quick_create = dict(data)
        try:
            self.log_message(
                "==> Modo Rapido: '{0}' ({1}/{2}) preparado.".format(
                    data.get("name", ""), platform, os_name)
            )
        except Exception:
            pass
        try:
            self.input_vm_name.setFocus()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # vm_optimizer_v1_quick: aplicacion de los campos avanzados del perfil
    # ------------------------------------------------------------------
    def _apply_advanced_from_quick(self, data):
        """Vuelca a los widgets los campos avanzados del perfil.

        Marcador: vm_optimizer_v1_quick. Se llama desde
        _populate_from_quick_create DESPUES de new_vm() y de rellenar
        los basicos. Usa blockSignals para no disparar el dirty
        tracking ni los auto-save mientras los widgets aun no tienen
        un vm_config.ini detras (current_vm_dir sigue siendo None).
        """
        if not data:
            return

        def _set_check(attr, value):
            w = getattr(self, attr, None)
            if w is None:
                return
            try:
                w.blockSignals(True)
                w.setChecked(bool(value))
                w.blockSignals(False)
            except Exception:
                pass

        def _set_combo(attr, value):
            w = getattr(self, attr, None)
            if w is None or value in (None, ""):
                return
            try:
                idx = w.findData(value)
                if idx < 0:
                    return
                w.blockSignals(True)
                w.setCurrentIndex(idx)
                w.blockSignals(False)
            except Exception:
                pass

        def _set_spin(attr, value, default=1):
            w = getattr(self, attr, None)
            if w is None:
                return
            try:
                v = int(value) if value is not None else int(default)
            except Exception:
                v = int(default)
            try:
                w.blockSignals(True)
                w.setValue(v)
                w.blockSignals(False)
            except Exception:
                pass

        # --- Caracteristicas de CPU ---
        _set_check("check_nested_virt",
                   data.get("nested_virt", False))
        _set_check("check_hyperv_enlight",
                   data.get("hyperv_enlightenments", False))

        # --- VirtIO extras ---
        _set_check("check_virtio_rng", data.get("virtio_rng", False))
        _set_check("check_virtio_balloon",
                   data.get("virtio_balloon", False))
        _set_check("check_virtio_watchdog",
                   data.get("virtio_watchdog", False))
        # El perfil no especifica la accion del watchdog: se queda en
        # "reset" (valor por defecto del combo).

        # --- Tuning de memoria ---
        mt = data.get("memory_tuning") or {}
        if isinstance(mt, dict):
            _set_check("check_mem_hugepages",
                       bool(mt.get("hugepages", False)))
            _set_check("check_mem_prealloc",
                       bool(mt.get("prealloc", False)))
            _set_check("check_mem_memfd_lock",
                       bool(mt.get("memfd_lock", False)))
        try:
            self._refresh_hugepages_status()
        except Exception:
            pass

        # --- Topologia manual de CPU ---
        topo = data.get("cpu_topology") or {}
        if isinstance(topo, dict):
            _manual = str(topo.get("mode") or "auto").lower() == "manual"
            _set_check("check_cpu_topology_manual", _manual)
            _set_spin("spin_cpu_sockets", topo.get("sockets"), 1)
            _set_spin("spin_cpu_cores", topo.get("cores"), 2)
            _set_spin("spin_cpu_threads", topo.get("threads"), 1)
            try:
                w = getattr(self, "_cpu_topo_widget", None)
                if w is not None:
                    w.setVisible(_manual)
            except Exception:
                pass
        try:
            self._refresh_cpu_topology_total()
        except Exception:
            pass

        # --- Consola remota ---
        _set_combo("combo_console_protocol",
                   data.get("console_protocol"))
        _set_combo("combo_console_mode", data.get("console_mode"))

        # --- Snapshot compat ---
        _set_check("check_snapshot_compat",
                   data.get("snapshot_compat", False))
        try:
            self._refresh_snapshot_compat_ui_on_os_change()
        except Exception:
            pass


    def _persist_advanced_from_quick(self, data, vm_dir):
        """Escribe los campos avanzados del perfil en vm_config.ini.

        Marcador: vm_optimizer_v1_quick. Se llama desde
        _materialize_quick_create justo despues de
        _ensure_storage_target_vm() (que ya creo el .ini). Los widgets
        ya estan rellenos por _apply_advanced_from_quick; esto
        garantiza que el .ini arranque coherente con la UI.

        Campos persistidos en extra:
            virtio_rng, virtio_balloon, virtio_watchdog,
            virtio_watchdog_action, nested_virt,
            hyperv_enlightenments, memory_tuning, cpu_topology,
            console_protocol, console_mode, snapshot_compat,
            clipboard (dict {"mode": ...}).
        """
        if not vm_dir or not data:
            return
        import json as _json
        import configparser as _cfg
        import time as _t

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

        # Solo escribimos las claves que el perfil define. Las que no
        # lleguen se dejan con el valor que ya hubiera (si lo hubiera).
        if "virtio_rng" in data:
            extra["virtio_rng"] = bool(data.get("virtio_rng"))
        if "virtio_balloon" in data:
            extra["virtio_balloon"] = bool(data.get("virtio_balloon"))
        if "virtio_watchdog" in data:
            extra["virtio_watchdog"] = bool(data.get("virtio_watchdog"))
            extra.setdefault("virtio_watchdog_action", "reset")
        if "nested_virt" in data:
            extra["nested_virt"] = bool(data.get("nested_virt"))
        if "hyperv_enlightenments" in data:
            extra["hyperv_enlightenments"] = bool(
                data.get("hyperv_enlightenments"))
        if isinstance(data.get("memory_tuning"), dict):
            extra["memory_tuning"] = dict(data["memory_tuning"])
        if isinstance(data.get("cpu_topology"), dict):
            extra["cpu_topology"] = dict(data["cpu_topology"])
        if data.get("console_protocol"):
            extra["console_protocol"] = str(data["console_protocol"])
        if data.get("console_mode"):
            extra["console_mode"] = str(data["console_mode"])
        if "snapshot_compat" in data:
            extra["snapshot_compat"] = bool(data.get("snapshot_compat"))
        _clip = data.get("clipboard")
        if _clip in ("disabled", "host_to_guest",
                     "guest_to_host", "bidirectional"):
            extra["clipboard"] = {"mode": _clip}

        # vm_optimizer_v1_quick_marks_profile: marcar la VM con el
        # perfil aplicado + candado cerrado, igual que hace el
        # boton "Aplicar perfil" sobre una VM existente. Sin esto,
        # una VM creada por el wizard no mostraba el label
        # "Perfil: X" en el Resumen ni traia el candado cerrado.
        _pid = (data.get("profile_id")
                or data.get("profile")
                or "")
        if _pid:
            extra["applied_profile"]    = str(_pid)
            extra["profile_locked"]     = True
            extra["profile_applied_at"] = _t.strftime(
                "%Y-%m-%dT%H:%M:%S")

        c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(vm_dir)

        try:
            self.log_message(
                "==> Modo Rapido: avanzados del perfil '{0}' "
                "persistidos en el .ini.".format(
                    data.get("profile_id") or data.get("profile") or "?"))
        except Exception:
            pass


    def _inject_pending_iso(self, extra, os_type):
        pending = getattr(self, "_pending_quick_create", None)
        if not pending:
            return False
        try:
            from principal_cdrom import apply_choice, CHOICE_NONE
            iso_choice = pending.get("iso_choice", "")
            iso_path = pending.get("iso_path", "")
            os_name = pending.get("os_name", "")
            devices = extra.setdefault("storage_devices", [])
            if iso_choice == CHOICE_NONE and iso_path:
                apply_choice(devices, os_type, CHOICE_NONE,
                             profile=os_name, own_iso=iso_path, new_vm=True)
            elif iso_choice == CHOICE_NONE:
                apply_choice(devices, os_type, CHOICE_NONE,
                             profile=os_name, new_vm=True)
            else:
                apply_choice(devices, os_type, iso_choice,
                             profile=os_name, new_vm=True)
            try:
                self.log_message(
                    "==> Modo Rapido: unidad Principal configurada "
                    "(iso_choice={0!r}).".format(iso_choice)
                )
            except Exception:
                pass
            return True
        except Exception as e:
            try:
                self.log_message(
                    "[AVISO] Modo Rapido: no se pudo aplicar la ISO: " + str(e)
                )
            except Exception:
                pass
            return False
        finally:
            self._pending_quick_create = None


    # ------------------------------------------------------------------
    # Materializacion del wizard (marcador quick_create_v1_materialize)
    # ------------------------------------------------------------------
    def _materialize_quick_create(self, data):
        """Crea la VM provisional y registra disco + ISO tras el wizard.

        Marcador: quick_create_v1_materialize

        Antes, el wizard solo pre-rellenaba el formulario y guardaba la
        eleccion del ISO en self._pending_quick_create, que nadie
        consumia. Resultado: Configuracion -> Almacenamiento aparecia
        vacia hasta que el usuario anadia dispositivos a mano.
        """
        import os as _os
        import uuid as _uuid
        import subprocess as _sp
        import principal_cdrom as _pc

        if not self._ensure_storage_target_vm():
            return

        vm_dir = self.current_vm_dir
        if not vm_dir or not _os.path.isdir(vm_dir):
            return

        # vm_optimizer_v1_quick: persistir los avanzados del
        # perfil en el .ini. Los widgets ya se rellenaron en
        # _populate_from_quick_create.
        try:
            self._persist_advanced_from_quick(data, vm_dir)
        except Exception as _padv_err:
            try:
                self.log_message(
                    "[AVISO] Modo Rapido: no se pudieron persistir "
                    "los avanzados: " + str(_padv_err))
            except Exception:
                pass

        os_type    = data.get("platform") or "linux"
        os_name    = data.get("os_name") or ""
        iso_choice = data.get("iso_choice", "")
        iso_path   = data.get("iso_path", "")

        # 1) Disco duro fisico.
        try:
            disk_gb = int(data.get("disk_gb", 40))
        except Exception:
            disk_gb = 40
        disk_gb = max(5, min(2000, disk_gb))
        disk_path = _os.path.join(vm_dir, "vm_disk.qcow2")
        if not _os.path.isfile(disk_path):
            try:
                _sp.run(
                    ["qemu-img", "create", "-f", "qcow2",
                     "-o", "preallocation=off",
                     disk_path, f"{disk_gb}G"],
                    check=True, capture_output=True, text=True, timeout=180,
                )
                self.log_message(
                    "==> Modo Rapido: disco creado: "
                    + _os.path.basename(disk_path) + f" ({disk_gb} GB)"
                )
            except Exception as e:
                self.log_message(
                    "[AVISO] Modo Rapido: no se pudo crear el disco: "
                    + str(e)
                )
                return

        # 2) Registrar disco + ISO en storage_devices.
        devices = self._storage_devices_all(vm_dir)

        if not any(
            isinstance(d, dict) and d.get("device") in ("sata", "nvme")
            for d in devices
        ):
            _disk_entry = {
                "id":     "dev_" + _uuid.uuid4().hex[:12],
                "name":   _os.path.basename(disk_path),
                "path":   disk_path,
                "device": "sata",
                # disk_bus_storage_devices_v1: el Modo Rápido usa "auto"
                # (SATA/AHCI por defecto) para preservar snapshots completos.
                "bus_hint": "auto",
            }
            # vm_optimizer_v1_quick: aplicar al disco recien creado
            # los ajustes de I/O del perfil (disk_io_tuning_v1).
            try:
                _dio = data.get("disk_io") or {}
                if isinstance(_dio, dict):
                    for _src, _dst in (
                        ("cache", "disk_cache"),
                        ("io", "disk_io"),
                        ("aio", "disk_aio"),
                        ("discard", "disk_discard"),
                        ("detect_zeroes", "disk_detect_zeroes"),
                    ):
                        _val = _dio.get(_src)
                        if _val and str(_val).lower() != "auto":
                            _disk_entry[_dst] = str(_val)
            except Exception:
                pass
            devices.append(_disk_entry)

        try:
            _pc.apply_choice(
                devices, os_type, iso_choice,
                profile=os_name,
                own_iso=iso_path or None,
                new_vm=True,
            )
        except Exception as e:
            self.log_message(
                "[AVISO] Modo Rapido: no se pudo aplicar la ISO: " + str(e)
            )

        # 3) Persistir y refrescar UI.
        self._write_storage_devices(devices)
        try:
            self.refresh_storage_ui()
            self.refresh_boot_order_choices()
            if hasattr(self, "_update_manager_details"):
                self._update_manager_details()
        except Exception:
            pass

        # 4) La eleccion ya se aplico. Vaciar el pending para que el
        #    arranque no la vuelva a procesar (evita doble inyeccion).
        self._pending_quick_create = None


# disk_bus_storage_devices_v1_quick

# vm_optimizer_v1_quick_marks_profile

# vm_optimizer_v1_quick_import_os
