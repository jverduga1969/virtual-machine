# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: snapshots automaticos programados (Bloque C #12).

Marcador: snapshot_schedule_v1

- Seccion compacta en la pestana Snapshots: checkbox + combo de
  intervalo + spinbox de retencion.
- Persistencia en extra["snapshot_schedule"]:
    {
      "enabled": bool,
      "interval": "hourly" | "every6h" | "every12h" | "daily" | "weekly",
      "keep": int,                # 1..50
      "last_run": "ISO8601"       # opcional, para depurar
    }
- Un tick del scheduler central cada 60 s revisa todas las VMs con
  enabled=true y, cuando toca, lanza un SNAPSHOT SOLO DE DISCOS
  (no completo) para no congelar la VM del usuario.
- Los snapshots automaticos se marcan con prefijo "auto_" y se
  registran en extra.snapshots_meta con {"scheduled": true} para
  aplicar la retencion por separado de los manuales.
"""
import os
import json
import time
import datetime
import configparser

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QLabel, QSpinBox,
)

import vm_config


class SnapshotScheduleMixin:

    _INTERVALOS = [
        ("Cada hora",     "hourly",   3600),
        ("Cada 6 horas",  "every6h",  21600),
        ("Cada 12 horas", "every12h", 43200),
        ("Diario",        "daily",    86400),
        ("Semanal",       "weekly",   604800),
    ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _interval_seconds(cls, key):
        for _label, k, sec in cls._INTERVALOS:
            if k == key:
                return sec
        return 86400

    def _write_extra_to_vm(self, vm_dir, mutator):
        """Aplica una funcion al extra[] de una VM concreta y guarda.

        `mutator` recibe el dict extra y lo modifica in-place. Se usa
        para no tocar el extra de la VM activa cuando se trabaja sobre
        otras VMs (scheduler).
        """
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return None
        c = configparser.ConfigParser(interpolation=None)
        c.read(cfg_path, encoding="utf-8")
        if not c.has_section("extra"):
            c.add_section("extra")
        try:
            extra = json.loads(c["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        mutator(extra)
        c.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(vm_dir)
        return extra

    # ------------------------------------------------------------------
    # UI: se construye desde virtual_machine.py al crear la pestana
    # Snapshots.
    # ------------------------------------------------------------------
    def _build_snapshot_schedule_ui(self, parent_layout):
        box = QGroupBox("Snapshots automaticos programados")
        form = QFormLayout(box)

        self.check_snapshot_schedule_enabled = QCheckBox("Activar")
        self.check_snapshot_schedule_enabled.setToolTip(
            "Cuando esta activo, la app crea snapshots de disco "
            "automaticamente en esta VM segun la frecuencia elegida.\n\n"
            "Los snapshots programados son SOLO DE DISCOS (no guardan "
            "RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan "
            "por antiguedad al superar el limite de retencion.\n\n"
            "No se ejecutan si la VM esta apagada."
        )
        self.check_snapshot_schedule_enabled.stateChanged.connect(
            self._on_snapshot_schedule_changed
        )
        form.addRow("", self.check_snapshot_schedule_enabled)

        self.combo_snapshot_schedule_interval = QComboBox()
        for label, key, _sec in self._INTERVALOS:
            self.combo_snapshot_schedule_interval.addItem(label, key)
        self.combo_snapshot_schedule_interval.setToolTip(
            "Frecuencia con la que se crea el snapshot automatico.\n"
            "El primer snapshot se crea pasada una frecuencia completa "
            "desde la activacion (o desde el ultimo, si ya habia uno)."
        )
        self.combo_snapshot_schedule_interval.currentIndexChanged.connect(
            self._on_snapshot_schedule_changed
        )
        form.addRow("Frecuencia:", self.combo_snapshot_schedule_interval)

        self.spin_snapshot_schedule_keep = QSpinBox()
        self.spin_snapshot_schedule_keep.setRange(1, 50)
        self.spin_snapshot_schedule_keep.setValue(5)
        self.spin_snapshot_schedule_keep.setToolTip(
            "Cuantos snapshots automaticos conservar. Al superar este "
            "numero se eliminan los mas antiguos (solo los que empiezan "
            "por 'auto_'; los manuales nunca se tocan)."
        )
        self.spin_snapshot_schedule_keep.valueChanged.connect(
            self._on_snapshot_schedule_changed
        )
        form.addRow("Conservar:", self.spin_snapshot_schedule_keep)

        note = QLabel(
            "Los snapshots programados son <b>solo de discos</b>: no "
            "guardan RAM ni estado de ventanas. No congelan la VM del "
            "usuario (el snapshot completo si puede hacerlo)."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#666; font-size:11px;")
        form.addRow("", note)

        self.label_snapshot_schedule_status = QLabel("")
        self.label_snapshot_schedule_status.setWordWrap(True)
        self.label_snapshot_schedule_status.setStyleSheet(
            "color:#666; font-size:11px;"
        )
        form.addRow("", self.label_snapshot_schedule_status)

        parent_layout.addWidget(box)
        self._snapshot_schedule_loading = False
        self._refresh_snapshot_schedule_status()

    # ------------------------------------------------------------------
    # Cargar/guardar los widgets
    # ------------------------------------------------------------------
    def _load_snapshot_schedule_to_ui(self, data):
        """Vuelca extra["snapshot_schedule"] a los widgets."""
        if not hasattr(self, "check_snapshot_schedule_enabled"):
            return
        sched = ((data or {}).get("extra") or {}).get("snapshot_schedule") or {}
        self._snapshot_schedule_loading = True
        try:
            self.check_snapshot_schedule_enabled.setChecked(
                bool(sched.get("enabled"))
            )
            key = str(sched.get("interval") or "daily")
            idx = self.combo_snapshot_schedule_interval.findData(key)
            if idx < 0:
                idx = self.combo_snapshot_schedule_interval.findData("daily")
            self.combo_snapshot_schedule_interval.setCurrentIndex(idx)
            try:
                keep = int(sched.get("keep") or 5)
            except Exception:
                keep = 5
            keep = max(1, min(50, keep))
            self.spin_snapshot_schedule_keep.setValue(keep)
        finally:
            self._snapshot_schedule_loading = False
        self._refresh_snapshot_schedule_status()

    def _on_snapshot_schedule_changed(self, *_args):
        if getattr(self, "_snapshot_schedule_loading", False):
            return
        if not getattr(self, "current_vm_dir", None):
            return
        enabled = self.check_snapshot_schedule_enabled.isChecked()
        interval = self.combo_snapshot_schedule_interval.currentData() or "daily"
        keep = int(self.spin_snapshot_schedule_keep.value())

        def _mut(extra):
            old = extra.get("snapshot_schedule") or {}
            extra["snapshot_schedule"] = {
                "enabled": enabled,
                "interval": interval,
                "keep": keep,
                "last_run": old.get("last_run", ""),
            }

        try:
            self._write_extra_to_vm(self.current_vm_dir, _mut)
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] No se pudo guardar la programacion de snapshots: {e}"
                )
            except Exception:
                pass
            return
        self._refresh_snapshot_schedule_status()

    def _refresh_snapshot_schedule_status(self):
        lbl = getattr(self, "label_snapshot_schedule_status", None)
        if lbl is None:
            return
        if not getattr(self, "current_vm_dir", None):
            lbl.setText("Selecciona una VM para programar snapshots.")
            return
        if not self.check_snapshot_schedule_enabled.isChecked():
            lbl.setText("Desactivado para esta VM.")
            return
        interval_key = self.combo_snapshot_schedule_interval.currentData()
        interval_sec = self._interval_seconds(interval_key)
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
            sched = (data.get("extra") or {}).get("snapshot_schedule") or {}
            last_iso = str(sched.get("last_run") or "")
        except Exception:
            last_iso = ""
        if not last_iso:
            lbl.setText(
                "Sin snapshots programados todavia. Se creara el primero "
                "tras cumplirse la frecuencia elegida."
            )
            return
        try:
            last_dt = datetime.datetime.fromisoformat(last_iso)
            nxt = last_dt + datetime.timedelta(seconds=interval_sec)
            now = datetime.datetime.now()
            if nxt <= now:
                lbl.setText(
                    f"Pendiente (ultimo: "
                    f"{last_dt.strftime('%Y-%m-%d %H:%M')}). Se ejecutara "
                    f"en el proximo chequeo del scheduler."
                )
            else:
                delta = nxt - now
                mins = max(1, int(delta.total_seconds() // 60))
                lbl.setText(
                    f"Ultimo: {last_dt.strftime('%Y-%m-%d %H:%M')} · "
                    f"Proximo en ~{mins} min."
                )
        except Exception:
            lbl.setText(f"Ultimo: {last_iso}")

    # ------------------------------------------------------------------
    # Chequeo periodico (invocado por el scheduler central)
    # ------------------------------------------------------------------
    def _iter_vms_with_schedule(self):
        """Genera (vm_name, vm_dir, sched) para VMs con scheduling activo."""
        try:
            vms = vm_config.list_existing_vms()
        except Exception:
            return
        for name in vms:
            vm_dir = os.path.join(vm_config.BASE_VM_DIR, name)
            try:
                data = self._load_vm_config_cached(vm_dir)
            except Exception:
                continue
            sched = (data.get("extra") or {}).get("snapshot_schedule") or {}
            if not isinstance(sched, dict) or not sched.get("enabled"):
                continue
            yield name, vm_dir, sched

    def _check_snapshot_schedules(self):
        """Entrada del scheduler: revisa todas las VMs programadas."""
        now = time.time()
        for name, vm_dir, sched in self._iter_vms_with_schedule():
            interval_sec = self._interval_seconds(sched.get("interval"))
            last_iso = str(sched.get("last_run") or "")
            last_ts = 0.0
            if last_iso:
                try:
                    last_ts = datetime.datetime.fromisoformat(last_iso).timestamp()
                except Exception:
                    last_ts = 0.0
            if now - last_ts < interval_sec:
                continue
            # Toca. Solo aplica si la VM esta encendida.
            try:
                state = self._runtime_state(name)
            except Exception:
                continue
            if state not in ("running", "paused"):
                # Marcar como "intentado" para no repetir cada minuto; se
                # volvera a intentar en el proximo intervalo completo.
                self._update_schedule_last_run(vm_dir)
                continue
            try:
                self._run_scheduled_snapshot(name, vm_dir, sched)
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Snapshot programado de '{name}' fallo: {e}"
                    )
                except Exception:
                    pass

    def _update_schedule_last_run(self, vm_dir):
        """Graba el timestamp actual en extra["snapshot_schedule"]["last_run"]."""
        iso = datetime.datetime.now().replace(microsecond=0).isoformat()

        def _mut(extra):
            sched = extra.get("snapshot_schedule") or {}
            sched["last_run"] = iso
            extra["snapshot_schedule"] = sched

        try:
            self._write_extra_to_vm(vm_dir, _mut)
        except Exception:
            pass

    def _run_scheduled_snapshot(self, vm_name, vm_dir, sched):
        """Crea un snapshot solo de discos para la VM objetivo.

        Cambia temporalmente self.current_vm_dir porque toda la maquinaria
        de snapshots_mixin lo usa (readiness, qmp nodes, ejecucion). Es
        seguro porque el scheduler corre en el hilo de la UI y el cambio
        es de duracion corta.

        Importante: si el usuario tiene seleccionada esta misma VM, se
        refresca la pestana de snapshots al terminar. Si tiene otra VM
        seleccionada, la vista del usuario no se toca.
        """
        saved_vm_dir = getattr(self, "current_vm_dir", None)
        try:
            self.current_vm_dir = vm_dir
            readiness = self._snapshot_readiness()
            if not readiness.get("state_disk"):
                try:
                    self.log_message(
                        f"[AVISO] Snapshot programado de '{vm_name}': "
                        f"no hay disco QCOW2 escribible disponible."
                    )
                except Exception:
                    pass
                self._update_schedule_last_run(vm_dir)
                return
            tag = "auto_" + time.strftime("%Y%m%d_%H%M%S")
            try:
                nodes = self._create_live_disk_only_snapshot(tag, readiness)
                try:
                    self.log_message(
                        f"==> Snapshot programado '{tag}' creado para "
                        f"'{vm_name}' ({len(nodes or [])} disco(s))."
                    )
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Snapshot programado de '{vm_name}' fallo "
                        f"al crear: {e}"
                    )
                except Exception:
                    pass
                self._update_schedule_last_run(vm_dir)
                return
            # Registrar en snapshots_meta como programado.
            try:
                meta = self._load_snapshots_meta()
                entry = meta.get(tag) or {}
                if not isinstance(entry, dict):
                    entry = {}
                entry["scheduled"] = True
                meta[tag] = entry
                self._save_snapshots_meta(meta)
            except Exception:
                pass
            # Retencion.
            try:
                self._apply_schedule_retention(vm_dir, int(sched.get("keep") or 5))
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Retencion de snapshots programados: {e}"
                    )
                except Exception:
                    pass
            # Actualizar last_run.
            self._update_schedule_last_run(vm_dir)
            # Refrescar la pestana si el usuario esta viendo esta VM.
            if saved_vm_dir == vm_dir:
                try:
                    self.refresh_snapshot_page()
                except Exception:
                    pass
        finally:
            self.current_vm_dir = saved_vm_dir

    def _apply_schedule_retention(self, vm_dir, keep):
        """Elimina los snapshots automaticos mas antiguos si supera keep."""
        keep = max(1, int(keep))
        meta = self._load_snapshots_meta()
        scheduled = [
            tag for tag, info in meta.items()
            if isinstance(info, dict) and info.get("scheduled")
        ]
        scheduled.sort()
        if len(scheduled) <= keep:
            return
        to_delete = scheduled[: len(scheduled) - keep]
        for tag in to_delete:
            try:
                self._delete_snapshot_by_tag(vm_dir, tag)
                meta.pop(tag, None)
                try:
                    self.log_message(
                        f"==> Snapshot programado antiguo '{tag}' eliminado "
                        f"(retencion {keep})."
                    )
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] No se pudo eliminar '{tag}' en retencion: {e}"
                    )
                except Exception:
                    pass
        self._save_snapshots_meta(meta)

    def _delete_snapshot_by_tag(self, vm_dir, tag):
        """Elimina un snapshot de disco por tag (VM encendida o apagada)."""
        import subprocess
        try:
            state = self._runtime_state(os.path.basename(vm_dir))
        except Exception:
            state = "stopped"
        if state in ("running", "paused"):
            self._qmp_hmp(vm_dir, "delvm " + tag)
            return
        for d in self._snapshot_candidate_disks():
            p = subprocess.run(
                ["qemu-img", "snapshot", "-d", tag, d["path"]],
                capture_output=True, text=True, timeout=30,
            )
            if p.returncode != 0 and "not found" not in (p.stderr or "").lower():
                raise RuntimeError((p.stderr or p.stdout).strip())
