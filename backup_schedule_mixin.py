# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: backups programados de la carpeta de la VM (Bloque C #13).

Marcador: backup_schedule_v1

- Nueva pestana "Backups" con UI compacta: activar, destino, frecuencia,
  retencion, opcion "tambien si esta encendida" y boton "Backup ahora".
- Persistencia en extra["backup_schedule"]:
    {
      "enabled": bool,
      "destination": "/ruta/absoluta/",
      "interval": "hourly" | "every6h" | "every12h" | "daily" | "weekly",
      "keep": int,                # 1..50
      "allow_running": bool,
      "last_run": "ISO8601"
    }
- Reutiliza el scheduler central (marcador scheduler_v1). Registra la
  tarea "backup_schedule" a 60 s.
- El backup real lo hace `_export_vm_impl` (ya existente, con progreso,
  cancelacion y omision de pids/sockets), en un hilo de fondo.
- Nombres de backup: <vm>_backup_YYYYMMDD_HHMMSS (carpeta).
- Retencion: al terminar un backup OK, se borran los mas antiguos por
  encima de keep.

AVISO: si la VM esta encendida, la copia del .qcow2 puede quedar
inconsistente (QEMU esta escribiendo). Se avisa en la consola y se
permite solo si el usuario marco la opcion explicita. Lo recomendable
es programar backups cuando la VM esta apagada.
"""
import os
import glob
import json
import time
import shutil
import datetime
import configparser

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QFileDialog,
)

import vm_config
from workers import _BackgroundCallThread


class BackupScheduleMixin:

    _BACKUP_INTERVALOS = [
        ("Cada hora",     "hourly",   3600),
        ("Cada 6 horas",  "every6h",  21600),
        ("Cada 12 horas", "every12h", 43200),
        ("Diario",        "daily",    86400),
        ("Semanal",       "weekly",   604800),
    ]

    @classmethod
    def _backup_interval_seconds(cls, key):
        for _lbl, k, sec in cls._BACKUP_INTERVALOS:
            if k == key:
                return sec
        return 86400

    # ------------------------------------------------------------------
    # Persistencia auxiliar
    # ------------------------------------------------------------------
    def _write_backup_extra(self, vm_dir, mutator):
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
    # UI
    # ------------------------------------------------------------------
    def _build_backup_schedule_ui(self, parent_layout):
        box = QGroupBox(self.tr("Backups automaticos programados"))
        form = QFormLayout(box)

        self.check_backup_schedule_enabled = QCheckBox(self.tr("Activar"))
        self.check_backup_schedule_enabled.setToolTip(self.tr(
            "Cuando esta activo, la app copia la carpeta completa de la VM "
            "(discos, configuracion, snapshots) al destino elegido segun "
            "la frecuencia. Los backups son carpetas independientes; "
            "puedes borrarlos manualmente o dejar que la retencion los "
            "limpie."
        ))
        self.check_backup_schedule_enabled.stateChanged.connect(
            self._on_backup_schedule_changed
        )
        form.addRow("", self.check_backup_schedule_enabled)

        row_dest = QHBoxLayout()
        self.input_backup_destination = QLineEdit()
        self.input_backup_destination.setPlaceholderText(
            self.tr("Carpeta del host donde guardar los backups")
        )
        self.input_backup_destination.editingFinished.connect(
            self._on_backup_schedule_changed
        )
        row_dest.addWidget(self.input_backup_destination, 1)
        self.btn_backup_destination = QPushButton(self.tr("Elegir carpeta..."))
        self.btn_backup_destination.clicked.connect(
            self._choose_backup_destination
        )
        row_dest.addWidget(self.btn_backup_destination)
        form.addRow(self.tr("Destino:"), row_dest)

        self.combo_backup_interval = QComboBox()
        # i18n_tanda2f3: los labels viven en _BACKUP_INTERVALOS (atributo
        # de clase); se mapean aqui con literales para que pylupdate6 los
        # extraiga bajo el contexto de la app.
        _interval_labels_tr = {
            "Cada hora": self.tr("Cada hora"),
            "Cada 6 horas": self.tr("Cada 6 horas"),
            "Cada 12 horas": self.tr("Cada 12 horas"),
            "Diario": self.tr("Diario"),
            "Semanal": self.tr("Semanal"),
        }
        for label, key, _sec in self._BACKUP_INTERVALOS:
            _label_tr = _interval_labels_tr.get(label, label)
            self.combo_backup_interval.addItem(_label_tr, key)
        self.combo_backup_interval.currentIndexChanged.connect(
            self._on_backup_schedule_changed
        )
        form.addRow(self.tr("Frecuencia:"), self.combo_backup_interval)

        self.spin_backup_keep = QSpinBox()
        self.spin_backup_keep.setRange(1, 50)
        self.spin_backup_keep.setValue(3)
        self.spin_backup_keep.setToolTip(self.tr(
            "Cuantos backups conservar en el destino. Tras cada backup "
            "exitoso se borran los mas antiguos por encima de este numero."
        ))
        self.spin_backup_keep.valueChanged.connect(
            self._on_backup_schedule_changed
        )
        form.addRow(self.tr("Conservar:"), self.spin_backup_keep)

        self.check_backup_allow_running = QCheckBox(
            self.tr("Tambien cuando la VM esta encendida")
        )
        self.check_backup_allow_running.setToolTip(self.tr(
            "Desactivado (recomendado): los backups solo se ejecutan con "
            "la VM apagada.\n\n"
            "Activado: si la VM esta encendida, se copian los discos de "
            "todos modos; la copia puede quedar inconsistente porque QEMU "
            "esta escribiendo en el .qcow2 en ese momento. La restauracion "
            "podria requerir fsck o no arrancar. Solo si estas dispuesto a "
            "asumir ese riesgo."
        ))
        self.check_backup_allow_running.stateChanged.connect(
            self._on_backup_schedule_changed
        )
        form.addRow("", self.check_backup_allow_running)

        note = QLabel(self.tr(
            "Los backups son <b>carpetas</b> con todos los archivos de la "
            "VM (discos + configuración + snapshots + capturas). No "
            "incluyen pids, sockets ni logs. Para restaurar, usa el botón "
            "<b>Importar</b> de la pestaña Resumen con la carpeta del "
            "backup."
        ))
        note.setWordWrap(True)
        note.setStyleSheet("color:#666; font-size:11px;")
        form.addRow("", note)

        self.label_backup_schedule_status = QLabel("")
        self.label_backup_schedule_status.setWordWrap(True)
        self.label_backup_schedule_status.setStyleSheet(
            "color:#666; font-size:11px;"
        )
        form.addRow("", self.label_backup_schedule_status)

        row_actions = QHBoxLayout()
        self.btn_backup_now = QPushButton(self.tr("Backup ahora"))
        self.btn_backup_now.setToolTip(self.tr(
            "Ejecuta un backup inmediato con la configuracion actual, sin "
            "esperar a la proxima programacion."
        ))
        self.btn_backup_now.clicked.connect(self.backup_now)
        row_actions.addWidget(self.btn_backup_now)
        row_actions.addStretch(1)
        form.addRow("", row_actions)

        parent_layout.addWidget(box)
        self._backup_schedule_loading = False
        self._backup_in_progress = set()  # set de vm_dir
        self._refresh_backup_schedule_status()

    def _choose_backup_destination(self):
        start = self.input_backup_destination.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Elegir carpeta de destino para backups"), start,
        )
        if not path:
            return
        self.input_backup_destination.setText(path)
        self._on_backup_schedule_changed()

    # ------------------------------------------------------------------
    # Cargar / guardar
    # ------------------------------------------------------------------
    def _load_backup_schedule_to_ui(self, data):
        if not hasattr(self, "check_backup_schedule_enabled"):
            return
        sched = ((data or {}).get("extra") or {}).get("backup_schedule") or {}
        self._backup_schedule_loading = True
        try:
            self.check_backup_schedule_enabled.setChecked(
                bool(sched.get("enabled"))
            )
            self.input_backup_destination.setText(
                str(sched.get("destination") or "")
            )
            key = str(sched.get("interval") or "daily")
            idx = self.combo_backup_interval.findData(key)
            if idx < 0:
                idx = self.combo_backup_interval.findData("daily")
            self.combo_backup_interval.setCurrentIndex(idx)
            try:
                keep = int(sched.get("keep") or 3)
            except Exception:
                keep = 3
            self.spin_backup_keep.setValue(max(1, min(50, keep)))
            self.check_backup_allow_running.setChecked(
                bool(sched.get("allow_running"))
            )
        finally:
            self._backup_schedule_loading = False
        self._refresh_backup_schedule_status()

    def _on_backup_schedule_changed(self, *_args):
        if getattr(self, "_backup_schedule_loading", False):
            return
        if not getattr(self, "current_vm_dir", None):
            return
        enabled = self.check_backup_schedule_enabled.isChecked()
        dest = self.input_backup_destination.text().strip()
        interval = self.combo_backup_interval.currentData() or "daily"
        keep = int(self.spin_backup_keep.value())
        allow_running = self.check_backup_allow_running.isChecked()

        def _mut(extra):
            old = extra.get("backup_schedule") or {}
            extra["backup_schedule"] = {
                "enabled": enabled,
                "destination": dest,
                "interval": interval,
                "keep": keep,
                "allow_running": allow_running,
                "last_run": old.get("last_run", ""),
            }

        try:
            self._write_backup_extra(self.current_vm_dir, _mut)
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] No se pudo guardar la programacion de backups: {e}"
                )
            except Exception:
                pass
            return
        self._refresh_backup_schedule_status()

    def _refresh_backup_schedule_status(self):
        lbl = getattr(self, "label_backup_schedule_status", None)
        if lbl is None:
            return
        if not getattr(self, "current_vm_dir", None):
            lbl.setText(self.tr("Selecciona una VM para programar backups."))
            return
        if not self.check_backup_schedule_enabled.isChecked():
            lbl.setText(self.tr("Desactivado para esta VM."))
            return
        dest = self.input_backup_destination.text().strip()
        if not dest:
            lbl.setText(self.tr("Falta elegir una carpeta de destino."))
            return
        interval_sec = self._backup_interval_seconds(
            self.combo_backup_interval.currentData()
        )
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
            sched = (data.get("extra") or {}).get("backup_schedule") or {}
            last_iso = str(sched.get("last_run") or "")
        except Exception:
            last_iso = ""
        try:
            du = shutil.disk_usage(dest if os.path.isdir(dest)
                                    else os.path.dirname(dest) or dest)
            free_txt = self._format_bytes_iexport(int(du.free))
        except Exception:
            free_txt = "?"
        if not last_iso:
            lbl.setText(self.tr(
                "Sin backups todavia. Libre en destino: {0}. "
                "Se creara el primero tras cumplirse la frecuencia."
            ).format(free_txt))
            return
        try:
            last_dt = datetime.datetime.fromisoformat(last_iso)
            nxt = last_dt + datetime.timedelta(seconds=interval_sec)
            now = datetime.datetime.now()
            if nxt <= now:
                lbl.setText(self.tr(
                    "Pendiente (ultimo: {0}). Libre: {1}."
                ).format(
                    last_dt.strftime('%Y-%m-%d %H:%M'), free_txt
                ))
            else:
                mins = max(1, int((nxt - now).total_seconds() // 60))
                lbl.setText(self.tr(
                    "Ultimo: {0} · Proximo en ~{1} min · Libre: {2}."
                ).format(
                    last_dt.strftime('%Y-%m-%d %H:%M'), mins, free_txt
                ))
        except Exception:
            lbl.setText(self.tr("Ultimo: {0} · Libre: {1}.").format(last_iso, free_txt))

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------
    def _iter_vms_with_backup_schedule(self):
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
            sched = (data.get("extra") or {}).get("backup_schedule") or {}
            if not isinstance(sched, dict) or not sched.get("enabled"):
                continue
            yield name, vm_dir, sched

    def _check_backup_schedules(self):
        now = time.time()
        for name, vm_dir, sched in self._iter_vms_with_backup_schedule():
            interval_sec = self._backup_interval_seconds(sched.get("interval"))
            last_iso = str(sched.get("last_run") or "")
            last_ts = 0.0
            if last_iso:
                try:
                    last_ts = datetime.datetime.fromisoformat(last_iso).timestamp()
                except Exception:
                    last_ts = 0.0
            if now - last_ts < interval_sec:
                continue
            if not sched.get("destination"):
                self._backup_update_last_run(vm_dir)
                continue
            if vm_dir in getattr(self, "_backup_in_progress", set()):
                continue
            # Estado de la VM.
            try:
                state = self._runtime_state(name)
            except Exception:
                state = "stopped"
            if state in ("running", "paused") and not sched.get("allow_running"):
                try:
                    self.log_message(
                        f"==> Backup programado de '{name}': se omite, la VM "
                        f"esta {state} y no se permitio backup en ejecucion."
                    )
                except Exception:
                    pass
                self._backup_update_last_run(vm_dir)
                continue
            try:
                self._launch_scheduled_backup(name, vm_dir, sched)
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Backup programado de '{name}' fallo al "
                        f"lanzar: {e}"
                    )
                except Exception:
                    pass
                self._backup_update_last_run(vm_dir)

    def _backup_update_last_run(self, vm_dir):
        iso = datetime.datetime.now().replace(microsecond=0).isoformat()
        def _mut(extra):
            sched = extra.get("backup_schedule") or {}
            sched["last_run"] = iso
            extra["backup_schedule"] = sched
        try:
            self._write_backup_extra(vm_dir, _mut)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Lanzar el backup
    # ------------------------------------------------------------------
    def _launch_scheduled_backup(self, vm_name, vm_dir, sched, manual=False):
        destination = sched.get("destination")
        if not destination:
            if manual:
                QMessageBox.warning(
                    self, self.tr("Backup"),
                    self.tr("Configura primero una carpeta de destino."),
                )
            return
        try:
            os.makedirs(destination, exist_ok=True)
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] Backup de '{vm_name}': no se pudo crear el "
                    f"destino {destination}: {e}"
                )
            except Exception:
                pass
            if manual:
                QMessageBox.warning(
                    self, self.tr("Backup"),
                    self.tr("No se pudo crear la carpeta destino:\n{0}\n\n{1}").format(
                        destination, e
                    ),
                )
            return

        ts = time.strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(destination, f"{vm_name}_backup_{ts}")
        if os.path.exists(dest_path):
            # Extremadamente raro (dos backups en el mismo segundo);
            # añadimos sufijo para no pisar.
            i = 1
            while os.path.exists(f"{dest_path}_{i}"):
                i += 1
            dest_path = f"{dest_path}_{i}"

        # Comprobacion de espacio (rapida: solo stat, no copia).
        try:
            files = self._walk_vm_files(vm_dir)
            needed = sum(sz for _a, _r, sz in files) or 0
        except Exception:
            needed = 0
        try:
            du = shutil.disk_usage(destination)
            if needed and du.free < needed * 1.1:
                msg = self.tr(
                    "Espacio insuficiente en el destino. Necesario "
                    "~{0}, libre {1}."
                ).format(
                    self._format_bytes_iexport(needed),
                    self._format_bytes_iexport(int(du.free)),
                )
                try:
                    self.log_message(f"[AVISO] Backup de '{vm_name}': {msg}")
                except Exception:
                    pass
                if manual:
                    QMessageBox.warning(self, "Backup", msg)
                return
        except Exception:
            pass

        # Marcar en curso y actualizar last_run en cuanto lancemos.
        self._backup_in_progress = getattr(self, "_backup_in_progress", set())
        self._backup_in_progress.add(vm_dir)
        self._backup_update_last_run(vm_dir)

        try:
            self.log_message(
                f"==> Backup programado de '{vm_name}' iniciado → {dest_path}"
            )
        except Exception:
            pass

        def _work(log_emit, is_cancelled, progress_emit):
            return self._export_vm_impl(
                vm_dir, vm_name, "folder", dest_path,
                log_emit, is_cancelled, progress_emit,
            )

        thread = _BackgroundCallThread(_work, parent=self)
        # Log en vivo a la consola global.
        try:
            thread.log_signal.connect(self.log_message)
        except Exception:
            pass

        def _on_done(result, error):
            try:
                self._backup_in_progress.discard(vm_dir)
            except Exception:
                pass
            if error is not None:
                try:
                    self.log_message(
                        f"[AVISO] Backup de '{vm_name}' fallo: {error}"
                    )
                except Exception:
                    pass
                return
            try:
                self.log_message(
                    f"==> Backup de '{vm_name}' completado: {result}"
                )
            except Exception:
                pass
            # Retencion.
            try:
                self._apply_backup_retention(
                    destination, vm_name, int(sched.get("keep") or 3)
                )
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Retencion de backups: {e}"
                    )
                except Exception:
                    pass
            # Refrescar estado si esta VM esta seleccionada.
            try:
                if self.current_vm_dir == vm_dir:
                    self._refresh_backup_schedule_status()
            except Exception:
                pass

        thread.done_signal.connect(_on_done)
        # Guardar referencia para no perderla (evita GC).
        if not hasattr(self, "_backup_threads"):
            self._backup_threads = []
        self._backup_threads.append(thread)
        # Limpiar la lista cuando termine.
        thread.finished.connect(
            lambda t=thread: self._backup_threads.remove(t)
            if t in getattr(self, "_backup_threads", []) else None
        )
        thread.start()

    # ------------------------------------------------------------------
    # Retencion
    # ------------------------------------------------------------------
    def _apply_backup_retention(self, destination, vm_name, keep):
        keep = max(1, int(keep))
        pattern = os.path.join(destination, f"{vm_name}_backup_*")
        entries = sorted(glob.glob(pattern))
        # Solo carpetas.
        entries = [p for p in entries if os.path.isdir(p)]
        if len(entries) <= keep:
            return
        to_delete = entries[: len(entries) - keep]
        for p in to_delete:
            try:
                shutil.rmtree(p, ignore_errors=False)
                try:
                    self.log_message(
                        f"==> Backup antiguo eliminado por retencion: "
                        f"{os.path.basename(p)}"
                    )
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] No se pudo eliminar '{p}': {e}"
                    )
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Manual
    # ------------------------------------------------------------------
    def backup_now(self):
        if not self._vm_is_selected():
            QMessageBox.information(
                self, self.tr("Backup"),
                self.tr("Selecciona primero una maquina virtual."),
            )
            return
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
        except Exception:
            data = {}
        sched = (data.get("extra") or {}).get("backup_schedule") or {}
        if not sched.get("destination"):
            # Intentar tomar del widget por si aun no se guardo.
            dest = self.input_backup_destination.text().strip()
            if not dest:
                QMessageBox.warning(
                    self, self.tr("Backup"),
                    self.tr("Configura primero una carpeta de destino en esta "
                            "seccion."),
                )
                return
            sched = dict(sched)
            sched["destination"] = dest
        name = os.path.basename(self.current_vm_dir)
        try:
            state = self._runtime_state(name)
        except Exception:
            state = "stopped"
        if state in ("running", "paused") and not sched.get("allow_running"):
            QMessageBox.warning(
                self, self.tr("Backup con la VM encendida"),
                self.tr(
                    "La VM esta encendida.\n\n"
                    "Para evitar una copia inconsistente, apagala primero, o "
                    "marca la opcion 'Tambien cuando la VM esta encendida' en "
                    "esta seccion (asumiendo el riesgo)."
                ),
            )
            return
        self._launch_scheduled_backup(name, self.current_vm_dir, sched,
                                       manual=True)

# i18n_tanda2f3_backup_schedule_v1
