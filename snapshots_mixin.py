# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin con toda la funcionalidad de snapshots (instantáneas) de disco:
listar, crear, restaurar, eliminar y renombrar, más las utilidades QMP de
bajo nivel que usa (query-block, grafo de nodos de bloque) y la vista
previa con captura de pantalla del estado de la VM al momento del snapshot.

Se mezcla dentro de VirtualMachineManagerApp; todos los métodos asumen el
`self` de esa clase (current_vm_dir, widgets de la pestaña de snapshots,
etc. ya están definidos en su __init__/init_ui). No tiene __init__ propio:
un mixin solo aporta métodos, nunca estado.
"""
import os
import re
import json
import shutil
import subprocess
import time
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox, QInputDialog, QTreeWidgetItem

from task_progress import TaskProgressDialog
from vm_config import load_vm_config
from workers import SnapshotOperationWorker


class SnapshotsMixin:
    def _qmp_block_info(self, vm_dir):
        """Obtiene información de los discos conectados sin abrir los archivos del host."""
        try:
            result = self._qmp_command(vm_dir, {"execute": "query-block"})
            rows = result.get("return") or []
            data = {}
            for row in rows:
                ins = row.get("inserted") or {}
                file_name = ins.get("file") or ""
                if file_name:
                    data[os.path.abspath(file_name)] = ins
            return data
        except Exception:
            return {}

    def _snapshot_candidate_disks(self):
        """Analiza discos SATA/NVMe aptos para snapshots sin violar los locks de QEMU."""
        if not self._vm_is_selected():
            return []
        running = self._runtime_state(os.path.basename(self.current_vm_dir)) in ("running", "paused")
        qmp_info = self._qmp_block_info(self.current_vm_dir) if running else {}
        try:
            config = load_vm_config(self.current_vm_dir)
        except Exception:
            config = {}
        configured_format = str(config.get("disk_format") or "").lower()
        devices = []
        for d in self._storage_devices_all(self.current_vm_dir):
            typ = d.get("device", "sata")
            path = d.get("path") or ""
            if typ not in ("sata", "nvme") or not path:
                continue
            path = os.path.abspath(path)
            exists = os.path.isfile(path)
            info_error = ""
            meta = {}
            if running:
                # NO llamamos a qemu-img sobre un disco en uso: QEMU mantiene un lock de escritura.
                ins = qmp_info.get(path, {})
                fmt = str(ins.get("drv") or "").lower()
                if not fmt:
                    fmt = str(d.get("format") or "").lower()
                if not fmt:
                    ext = os.path.splitext(path)[1].lower().lstrip(".")
                    fmt = ext if ext in ("qcow2", "raw", "vdi", "vmdk", "vhdx") else configured_format
                writable = bool(exists and os.access(path, os.W_OK) and not bool(ins.get("ro", False)))
                if not exists:
                    info_error = "El archivo del disco no existe."
                virtual_size = 0
                if ins.get("virtual-size") is not None:
                    try: virtual_size = int(ins.get("virtual-size"))
                    except Exception: pass
                if not virtual_size:
                    try:
                        ds = str(d.get("size") or d.get("virtual_size") or "")
                        m = re.match(r"(\d+(?:\.\d+)?)\s*(GB|G|MB|M|TB|T)", ds, re.I)
                        if m:
                            n=float(m.group(1)); u=m.group(2).upper(); mult=1024**3 if u in ("GB","G") else 1024**2 if u in ("MB","M") else 1024**4
                            virtual_size=int(n*mult)
                    except Exception: pass
                actual_size = os.path.getsize(path) if exists else -1
                encrypted = False
                backing_file = ""
            else:
                if exists:
                    try:
                        info = subprocess.run(["qemu-img", "info", "--output=json", path], capture_output=True, text=True, timeout=10, check=True)
                        meta = json.loads(info.stdout or "{}")
                    except FileNotFoundError:
                        info_error = "qemu-img no está instalado o no está en PATH."
                    except subprocess.CalledProcessError as e:
                        info_error = (e.stderr or e.stdout or "qemu-img info falló").strip()
                    except Exception as e:
                        info_error = str(e)
                else:
                    info_error = "El archivo del disco no existe."
                fmt = str(meta.get("format") or "").lower()
                writable = bool(exists and os.access(path, os.W_OK))
                try: virtual_size=int(meta.get("virtual-size") or 0)
                except Exception: virtual_size=0
                try: actual_size=int(meta.get("actual-size")) if meta.get("actual-size") is not None else (int(os.path.getsize(path)) if exists else -1)
                except Exception: actual_size=-1
                encrypted=bool(meta.get("encrypted", False))
                backing_file=meta.get("backing-filename") or meta.get("backing_file") or ""
            try:
                du=shutil.disk_usage(os.path.dirname(path) or os.getcwd()); free=int(du.free)
            except Exception:
                free=-1
            devices.append({"id":str(d.get("id") or ""),"name":d.get("name") or os.path.basename(path),"path":path,"device":typ,"format":fmt or "desconocido","writable":writable,"free":free,"virtual_size":virtual_size,"actual_size":actual_size,"encrypted":encrypted,"backing_file":backing_file,"exists":exists,"info_error":info_error,"running":running})
        return devices

    @staticmethod
    def _format_bytes(value):
        if value is None or value < 0:
            return "Desconocido"
        n=float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or unit == "TB":
                return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
            n/=1024.0

    def _snapshot_readiness(self):
        """Comprueba candidatos sin intentar abrir con escritura una imagen bloqueada por QEMU."""
        disks = self._snapshot_candidate_disks()
        qcow = [d for d in disks if d["exists"] and d["format"] == "qcow2" and d["writable"] and not d["encrypted"] and not d["info_error"]]
        first = qcow[0] if qcow else None
        try:
            data = load_vm_config(self.current_vm_dir) if self._vm_is_selected() else {}
            ram_text = str(data.get("ram") or "0").upper()
            m = re.match(r"(\d+)\s*(G|M)", ram_text)
            ram_bytes = int(m.group(1)) * (1024**3 if m and m.group(2)=="G" else 1024**2) if m else 0
        except Exception:
            ram_bytes=0
        reserve=ram_bytes + 512*1024**2
        problems=[]
        if not first:
            problems.append("No hay ningún disco QCOW2 escribible y no removible disponible para guardar el estado de la VM.")
            for d in disks:
                if d.get("info_error"): problems.append(f"{d['name']}: {d['info_error']}")
                elif d.get("format") not in ("qcow2", "desconocido"): problems.append(f"{d['name']}: formato detectado {d['format'].upper()}, no QCOW2.")
                elif d.get("exists") and not d.get("writable"): problems.append(f"{d['name']}: el archivo no es escribible o QEMU lo tiene protegido.")
        low_space=[d for d in disks if d["format"]=="qcow2" and d["writable"] and d["free"]>=0 and d["free"]<reserve]
        if low_space:
            problems.append("Poco espacio libre en: " + ", ".join(d["name"] for d in low_space) + ".")
        return {"disks":disks,"eligible":qcow,"state_disk":first,"reserve":reserve,"problems":problems}

    def _snapshot_list(self):
        """Devuelve líneas de snapshots de forma consistente.

        En ejecución, QEMU expone el snapshot de VM mediante `info snapshots`.
        Con la VM apagada, leemos TODOS los QCOW2 elegibles y unimos los
        resultados, eliminando duplicados por (id, tag, fecha, reloj).
        """
        if not self._vm_is_selected():
            return []
        state=self._runtime_state(os.path.basename(self.current_vm_dir))
        if state in ("running", "paused"):
            try:
                result=self._qmp_hmp(self.current_vm_dir, "info snapshots")
                text=str(result.get("return") or "")
                if not text.strip():
                    return []
                parsed_rows=[]
                seen_tags=set()
                for line in text.splitlines():
                    parsed=self._parse_snapshot_line(line)
                    if not parsed:
                        continue
                    tag=parsed[1]
                    key_tag=tag if tag else f"__id__:{parsed[0]}"
                    if key_tag in seen_tags:
                        continue
                    seen_tags.add(key_tag)
                    parsed_rows.append(parsed)
                return ["\t".join(row) for row in parsed_rows]
            except Exception:
                return []

        if not shutil.which("qemu-img"):
            return []
        # Con la VM apagada, cada QCOW2 tiene su propia numeración interna.
        # Para una vista de VM usamos el TAG/nombre como identidad del snapshot y
        # escogemos la fila más completa entre los discos.
        best={}
        order=[]
        for d in self._snapshot_candidate_disks():
            path=d.get("path")
            if d.get("format") != "qcow2" or not path or not d.get("exists"):
                continue
            try:
                out=subprocess.run(["qemu-img","snapshot","-l",path],capture_output=True,text=True,timeout=8,check=False)
                for line in out.stdout.splitlines():
                    parsed=self._parse_snapshot_line(line)
                    if not parsed:
                        continue
                    tag=parsed[1] or f"__id__:{parsed[0]}"
                    if tag not in best:
                        best[tag]=parsed
                        order.append(tag)
                    else:
                        # Prefiere una fila con fecha/reloj/tamaño no vacíos.
                        cur=best[tag]
                        score=lambda r: sum(bool(x and x.strip()) for x in r[1:])
                        if score(parsed) > score(cur):
                            best[tag]=parsed
            except Exception:
                continue
        return ["\t".join(best[tag]) for tag in order]

    @staticmethod
    def _parse_snapshot_line(line):
        """Parsea formatos antiguos y modernos de qemu-img/info snapshots.

        Devuelve (id, tag, vm_size, date_text, clock_text).
        Importante: `0 B` son DOS columnas; la letra B no es un estado.
        """
        raw=" ".join(str(line).strip().split())
        if not raw or not raw[0].isdigit() or raw.lower().startswith("snapshot list"):
            return None
        parts=raw.split()
        if len(parts) < 6 or not parts[0].isdigit():
            return None
        snap_id=parts[0]
        # ID + TAG + VM_SIZE + DATE(YYYY-MM-DD) + TIME(HH:MM:SS) + CLOCK...
        idx=1
        tag=parts[idx] if idx < len(parts) else ""
        # Si TAG está vacío en la salida, qemu puede desplazar el tamaño.
        idx+=1
        if idx >= len(parts):
            return None
        # VM_SIZE puede ser `0 B`, `4.0 MiB`, etc. Detectamos la unidad.
        if idx+1 < len(parts) and parts[idx+1].upper() in {"B","KB","KIB","MB","MIB","GB","GIB","TB","TIB","K","M","G","T"}:
            vm_size=f"{parts[idx]} {parts[idx+1]}"
            idx+=2
        else:
            vm_size=parts[idx]
            idx+=1
        if idx+1 >= len(parts):
            return None
        date_text=f"{parts[idx]} {parts[idx+1]}"
        idx+=2
        clock_text=" ".join(parts[idx:])
        return (snap_id, tag, vm_size, date_text, clock_text)

    @staticmethod
    def _format_snapshot_size(n_bytes):
        """Formato compacto para el tamaño del PNG del snapshot."""
        try:
            n = float(n_bytes)
        except (TypeError, ValueError):
            return "—"
        for u in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or u == "TB":
                return f"{n:.1f} {u}" if u != "B" else f"{int(n)} B"
            n /= 1024.0

    def _refresh_last_snapshot_thumbnail(self):
        """Actualiza el panel 'Último snapshot' del lateral derecho.

        Busca la captura .png más reciente en <vm_dir>/snapshots/, la
        muestra escalada, rellena el nombre y —en la etiqueta
        last_snap_time_label— la fecha y hora de la captura.

        Se llama desde refresh_snapshot_page (tras crear/restaurar/eliminar)
        y desde open_vm (al abrir una VM).
        """
        if not hasattr(self, "last_snap_thumbnail"):
            return

        def _clear_time_label():
            """Vacía la etiqueta de fecha/hora y su tooltip si existe."""
            if hasattr(self, "last_snap_time_label"):
                try:
                    self.last_snap_time_label.setText("")
                    self.last_snap_time_label.setToolTip("")
                except Exception:
                    pass

        # --- Caso 1: sin VM seleccionada ---
        if not self._vm_is_selected():
            self.last_snap_thumbnail.setPixmap(QPixmap())
            self.last_snap_thumbnail.setText("Sin VM seleccionada")
            self.last_snap_name_label.setText("—")
            _clear_time_label()
            self.btn_last_snap_restore.setEnabled(False)
            self._last_snapshot_tag = None
            return

        # --- Buscar capturas .png más recientes ---
        snap_dir = self._snapshot_screenshot_dir()
        entries = []
        if snap_dir and os.path.isdir(snap_dir):
            try:
                for name in os.listdir(snap_dir):
                    if not name.endswith(".png"):
                        continue
                    path = os.path.join(snap_dir, name)
                    try:
                        entries.append((os.path.getmtime(path), path, name[:-4]))
                    except OSError:
                        continue
            except OSError:
                pass

        # --- Caso 2: no hay capturas ---
        if not entries:
            self.last_snap_thumbnail.setPixmap(QPixmap())
            self.last_snap_thumbnail.setText("Sin capturas de snapshot")
            self.last_snap_name_label.setText(
                "Los snapshots creados con la VM en ejecución guardan una "
                "captura de pantalla que se muestra aquí."
            )
            _clear_time_label()
            self.btn_last_snap_restore.setEnabled(False)
            self._last_snapshot_tag = None
            return

        # --- Elegir la más reciente ---
        entries.sort(key=lambda e: e[0], reverse=True)
        mtime, path, tag = entries[0]

        # --- Miniatura ---
        pix = QPixmap(path)
        if pix.isNull():
            self.last_snap_thumbnail.setPixmap(QPixmap())
            self.last_snap_thumbnail.setText("Captura no legible")
            self.last_snap_name_label.setText(f"'{tag}'")
            _clear_time_label()
            self.btn_last_snap_restore.setEnabled(False)
            self._last_snapshot_tag = None
            return

        self.last_snap_thumbnail.setText("")
        self.last_snap_thumbnail.setPixmap(
            pix.scaled(
                260, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        # --- Nombre ---
        self.last_snap_name_label.setText(f"'{tag}'")

        # --- Fecha y hora del PNG (mtime) ---
        # Formato corto visible:   "22 sep 2026 · 21:43:05"
        # Tooltip con info extra:  fecha larga + tamaño del archivo.
        try:
            import time as _t
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            when_short = _t.strftime("%d %b %Y · %H:%M:%S", _t.localtime(mtime))
            when_long = _t.strftime(
                "%A, %d de %B de %Y a las %H:%M:%S", _t.localtime(mtime)
            )
            size_txt = self._format_snapshot_size(size)
            if hasattr(self, "last_snap_time_label"):
                self.last_snap_time_label.setText(when_short)
                self.last_snap_time_label.setToolTip(
                    f"{when_long}\nTamaño: {size_txt}"
                )
                # Forzar un repintado por si la etiqueta estaba oculta o
                # con tamaño 0 tras un cambio previo de layout.
                try:
                    self.last_snap_time_label.adjustSize()
                    self.last_snap_time_label.show()
                except Exception:
                    pass
        except Exception as e:
            # Si algo falla aquí (locale raro, etc.), no bloqueamos el
            # resto del panel.
            if hasattr(self, "last_snap_time_label"):
                try:
                    self.last_snap_time_label.setText("")
                    self.last_snap_time_label.setToolTip(str(e))
                except Exception:
                    pass

        self._last_snapshot_tag = tag
        self.btn_last_snap_restore.setEnabled(True)


    def _restore_last_snapshot(self):
        """Restaura el snapshot mostrado en el panel 'Último snapshot'.

        Reutiliza el flujo habitual: selecciona la fila correspondiente en
        la lista de snapshots y delega en restore_snapshot_from_page(), que
        ya sabe manejarlo con la VM encendida (snapshot-load) o apagada
        (qemu-img snapshot -a).
        """
        tag = getattr(self, "_last_snapshot_tag", None)
        if not tag:
            QMessageBox.information(
                self, "Restaurar snapshot",
                "No hay ningún snapshot reciente para restaurar.",
            )
            return
        # Refrescar la lista para asegurar que el item existe con la captura actual.
        try:
            self.refresh_snapshot_page()
        except Exception:
            pass
        target = None
        if hasattr(self, "snapshot_list_widget"):
            for i in range(self.snapshot_list_widget.topLevelItemCount()):
                it = self.snapshot_list_widget.topLevelItem(i)
                if it.text(1).strip() == tag:
                    target = it
                    break
        if target is None:
            QMessageBox.information(
                self, "Restaurar snapshot",
                f"Existe una captura para '{tag}', pero ese snapshot ya no "
                "aparece en la lista de la VM (puede haber sido eliminado). "
                "Actualiza la pestaña Snapshots o elimínalo manualmente.",
            )
            return
        self.snapshot_list_widget.setCurrentItem(target)
        self.restore_snapshot_from_page()

    # ==================================================================
    # Organigrama de snapshots
    # ==================================================================
    def _on_snap_view_toggled(self, idx):
        """Alterna entre vista Lista (idx=0) y Organigrama (idx=1)."""
        want_graph = (idx == 1)
        try:
            self.snap_view_stack.setCurrentIndex(1 if want_graph else 0)
        except Exception:
            pass
        try:
            if hasattr(self, "snapshot_preview_container"):
                self.snapshot_preview_container.setVisible(not want_graph)
        except Exception:
            pass
        if want_graph:
            try:
                self.refresh_snapshot_graph()
            except Exception:
                pass


    def _snapshots_meta_path(self):
        """Ruta de vm_config.ini para la VM actual."""
        if not self.current_vm_dir:
            return None
        return os.path.join(self.current_vm_dir, "vm_config.ini")

    def _load_snapshots_meta(self):
        """Lee `extra.snapshots_meta` del vm_config.ini actual.

        Devuelve un dict {tag: {"parent": "padre_tag"}}.
        Si no existe la sección, devuelve {}.
        """
        path = self._snapshots_meta_path()
        if not path or not os.path.isfile(path):
            return {}
        try:
            import configparser as _cfg
            import json as _json
            c = _cfg.ConfigParser(interpolation=None)
            c.read(path, encoding="utf-8")
            if not c.has_section("extra"):
                return {}
            extra = _json.loads(c["extra"].get("data", "{}"))
            meta = extra.get("snapshots_meta") or {}
            return meta if isinstance(meta, dict) else {}
        except Exception:
            return {}

    def _save_snapshots_meta(self, meta):
        """Guarda `extra.snapshots_meta` en vm_config.ini."""
        path = self._snapshots_meta_path()
        if not path or not os.path.isfile(path):
            return
        try:
            import configparser as _cfg
            import json as _json
            c = _cfg.ConfigParser(interpolation=None)
            c.read(path, encoding="utf-8")
            if not c.has_section("extra"):
                c.add_section("extra")
            try:
                extra = _json.loads(c["extra"].get("data", "{}"))
            except Exception:
                extra = {}
            extra["snapshots_meta"] = meta
            c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
            with open(path, "w", encoding="utf-8") as f:
                c.write(f)
        except Exception as e:
            try:
                self.log_message(f"[AVISO] No se pudo guardar meta de snapshots: {e}")
            except Exception:
                pass

    def _build_snapshot_edges(self, valid_tags):
        """Construye el dict {padre: [hijos]} a partir de la meta.

        Reglas:
          - Si meta[tag]["parent"] existe y ese padre está en valid_tags,
            el tag se considera hijo de él.
          - Si no, el tag es hijo de la raíz "VM original".
          - Detecta ciclos: si al seguir la cadena de padres llegamos a un
            tag ya visitado, se mueve ese tag a la raíz.
        """
        meta = self._load_snapshots_meta()
        root_label = "VM original"
        edges = {root_label: []}

        # Primera pasada: asignar cada tag a su padre declarado o a la raíz.
        for tag in valid_tags:
            parent = None
            info = meta.get(tag) or {}
            if isinstance(info, dict):
                parent = info.get("parent")
            if parent and parent in valid_tags and parent != tag:
                edges.setdefault(parent, []).append(tag)
            else:
                edges[root_label].append(tag)

        # Detección de ciclos: recorrer hacia arriba; si volvemos al inicio,
        # mover ese tag a la raíz.
        def has_cycle(tag, seen=None):
            if seen is None:
                seen = set()
            if tag in seen:
                return True
            seen.add(tag)
            parent = None
            info = meta.get(tag) or {}
            if isinstance(info, dict):
                parent = info.get("parent")
            if parent and parent in valid_tags:
                return has_cycle(parent, seen)
            return False

        for tag in list(valid_tags):
            if has_cycle(tag):
                # Quitar de su padre actual y ponerlo bajo la raíz.
                for parent, children in list(edges.items()):
                    if tag in children and parent != root_label:
                        children.remove(tag)
                if tag not in edges[root_label]:
                    edges[root_label].append(tag)

        return edges, root_label

    def refresh_snapshot_graph(self):
        """Reconstruye el organigrama con los snapshots actuales."""
        if not hasattr(self, "snapshot_graph_view"):
            return
        try:
            rows = self._snapshot_rows()
        except Exception:
            rows = []
        snapshots = []
        valid_tags = []
        for row in rows:
            # row = (id, tag, vm_size, date, clock)
            tag = row[1]
            if not tag:
                continue
            valid_tags.append(tag)
            snapshots.append({
                "tag": tag,
                "vm_size": row[2] or "",
                "date": row[3] or "",
            })
        edges, root_label = self._build_snapshot_edges(valid_tags)
        screenshot_dir = self._snapshot_screenshot_dir()
        # Conectar las señales del grafo (solo la primera vez; si ya
        # están conectadas, Qt las ignoraría silenciosamente, así que
        # usamos un flag).
        if not getattr(self, "_snap_graph_signals_connected", False):
            try:
                self.snapshot_graph_view.node_action.connect(
                    self._on_snapshot_graph_action)
                self.snapshot_graph_view.selection_changed.connect(
                    self._on_snapshot_graph_selection)
                self._snap_graph_signals_connected = True
            except Exception as _conn_err:
                try:
                    self.log_message(
                        f"[AVISO] No se pudieron conectar las senales del organigrama: {_conn_err}"
                    )
                except Exception:
                    pass
        try:
            self.snapshot_graph_view.rebuild(
                snapshots, edges, screenshot_dir, root_label=root_label,
            )
        except Exception as e:
            try:
                self.log_message(f"[AVISO] No se pudo reconstruir el organigrama: {e}")
            except Exception:
                pass

    def _on_snapshot_graph_action(self, action, tag):
        """Maneja una acción disparada desde el organigrama.

        Reutiliza los flujos existentes de la pestaña Snapshots (que
        operan sobre el snapshot seleccionado en el árbol). Antes de
        llamarlos, selecciona el nodo correspondiente en el árbol para
        que la acción apunte al snapshot correcto.

        action ∈ restore | delete | rename | set_parent | clear_parent |
                  create_child
        """
        if not tag:
            return
        # Seleccionar el snapshot en el árbol (los métodos existentes
        # dependen de _selected_snapshot_tag()).
        self._select_snapshot_in_tree(tag)

        try:
            if action == "restore":
                self.restore_snapshot_from_page()
            elif action == "delete":
                self.delete_snapshot_from_page()
            elif action == "rename":
                self.rename_snapshot_from_page()
            elif action == "set_parent":
                self._snapshot_graph_set_parent(tag)
            elif action == "clear_parent":
                self._snapshot_graph_clear_parent(tag)
            elif action == "create_child":
                self._snapshot_graph_create_child(tag)
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] Acción del organigrama '{action}' falló: {e}"
                )
            except Exception:
                pass

    def _on_snapshot_graph_selection(self, tag):
        """Sincroniza la selección del organigrama con la del árbol."""
        if not tag:
            return
        self._select_snapshot_in_tree(tag)

    def _select_snapshot_in_tree(self, tag):
        """Selecciona en snapshot_list_widget el snapshot con ese tag."""
        if not hasattr(self, "snapshot_list_widget"):
            return
        try:
            for i in range(self.snapshot_list_widget.topLevelItemCount()):
                it = self.snapshot_list_widget.topLevelItem(i)
                if it.text(1).strip() == tag:
                    self.snapshot_list_widget.setCurrentItem(it)
                    return
        except Exception:
            pass

    def _snapshot_graph_set_parent(self, tag):
        """Pregunta al usuario un nuevo padre para `tag` y lo guarda."""
        rows = self._snapshot_rows()
        candidates = [r[1] for r in rows if r[1] and r[1] != tag]
        if not candidates:
            QMessageBox.information(
                self, "Organigrama",
                "No hay otros snapshots para elegir como padre.",
            )
            return
        from PyQt6.QtWidgets import QInputDialog
        candidates.insert(0, "(ninguno — mover a la raíz)")
        item, ok = QInputDialog.getItem(
            self, "Establecer padre",
            f"Padre para '{tag}':",
            candidates, 0, False,
        )
        if not ok:
            return
        meta = self._load_snapshots_meta()
        if item.startswith("(ninguno"):
            info = meta.get(tag) or {}
            if isinstance(info, dict):
                info.pop("parent", None)
            meta[tag] = info
        else:
            meta.setdefault(tag, {})["parent"] = item
        self._save_snapshots_meta(meta)
        self.refresh_snapshot_graph()

    def _snapshot_graph_clear_parent(self, tag):
        """Mueve el snapshot a la raíz del organigrama."""
        meta = self._load_snapshots_meta()
        info = meta.get(tag) or {}
        if isinstance(info, dict):
            info.pop("parent", None)
        meta[tag] = info
        self._save_snapshots_meta(meta)
        self.refresh_snapshot_graph()

    def _snapshot_graph_create_child(self, parent_tag):
        """Crea un snapshot y lo marca como hijo de parent_tag."""
        if not self._vm_is_selected():
            return
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "Nuevo snapshot hijo",
            f"Nombre del snapshot (hijo de '{parent_tag}'):",
        )
        if not ok or not name.strip():
            return
        name = name.strip().replace(" ", "_")
        # Crear el snapshot por el flujo normal (con la VM apagada o corriendo).
        try:
            # Registrar la relación ANTES de crearlo: así cuando el
            # snapshot aparezca, ya estará en su sitio del árbol.
            meta = self._load_snapshots_meta()
            meta.setdefault(name, {})["parent"] = parent_tag
            self._save_snapshots_meta(meta)
        except Exception:
            pass
        # Delegar la creación al flujo existente.
        try:
            self._create_snapshot_with_name(name)
        except Exception as e:
            QMessageBox.warning(
                self, "Nuevo snapshot hijo",
                f"No se pudo crear el snapshot.\n\n{e}",
            )
            return
        # Refrescar el organigrama tras un pequeño delay para que el
        # snapshot aparezca en la lista cuando se reconstruya.
        try:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, self.refresh_snapshot_graph)
        except Exception:
            pass

    def _snapshot_graph_on_delete(self, tag):
        """Hook al eliminar: limpiar la meta del tag y reasignar sus hijos."""
        meta = self._load_snapshots_meta()
        # Los hijos del tag eliminado pasan a la raíz.
        for other_tag, info in list(meta.items()):
            if isinstance(info, dict) and info.get("parent") == tag:
                info.pop("parent", None)
        meta.pop(tag, None)
        self._save_snapshots_meta(meta)


    def manage_snapshots(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Snapshots", "Selecciona una máquina virtual.")
            return
        self.main_tabs.setCurrentIndex(getattr(self, "_snapshots_tab_index", 3))
        self.refresh_snapshot_page()

    def _snapshot_rows(self):
        rows=[]
        seen=set()
        for line in self._snapshot_list():
            parsed=self._parse_snapshot_line(line)
            if not parsed:
                continue
            key=(parsed[0], parsed[1], parsed[3], parsed[4])
            if key in seen:
                continue
            seen.add(key)
            rows.append(parsed)
        return rows

    def refresh_snapshot_page(self):
        if not hasattr(self, 'snapshot_list_widget'): return
        self.snapshot_list_widget.clear()
        if hasattr(self, 'snapshot_disk_status'):
            self.snapshot_disk_status.clear()
        if hasattr(self, 'snapshot_space_label'):
            self.snapshot_space_label.clear()
        # Refrescar la miniatura del panel derecho aunque no haya VM
        # seleccionada (para que muestre 'Sin VM seleccionada').
        if hasattr(self, "_refresh_last_snapshot_thumbnail"):
            self._refresh_last_snapshot_thumbnail()
        if not self._vm_is_selected():
            return
        readiness=self._snapshot_readiness()
        for d in readiness["disks"]:
            typ={"sata":"💽 SATA", "nvme":"⚡ NVMe"}.get(d["device"], d["device"])
            fmt=d["format"].upper()
            writable="Sí" if d["writable"] else "No"
            virtual_size=self._format_bytes(d.get("virtual_size", 0)) if d.get("virtual_size", 0) else "Desconocido"
            actual_size=self._format_bytes(d.get("actual_size", -1))
            free=self._format_bytes(d["free"])
            snap="Sí" if d in readiness["eligible"] else "No"
            item=QTreeWidgetItem([f"{typ} — {d['name']}", fmt, virtual_size, actual_size, free, writable, snap])
            if d.get("info_error"):
                item.setText(1, f"{fmt} ⚠")
                item.setToolTip(1, d["info_error"])
            self.snapshot_disk_status.addTopLevelItem(item)
        state_disk=readiness["state_disk"]
        if not state_disk:
            self.snapshot_space_label.setText("❌ No hay un QCOW2 escribible disponible para snapshots completos de VM.")
            self.snapshot_space_label.setStyleSheet("color:#b71c1c; padding:4px;")
        else:
            reserve=self._format_bytes(readiness["reserve"])
            self.snapshot_space_label.setText(f"✅ Disco para estado de VM: {state_disk['name']} · tamaño virtual: {self._format_bytes(state_disk.get('virtual_size', 0))} · archivo actual: {self._format_bytes(state_disk.get('actual_size', -1))} · espacio libre del sistema de archivos: {self._format_bytes(state_disk.get('free', -1))} · reserva orientativa inicial: {reserve}. El snapshot QCOW2 crece según se modifican bloques.")
            self.snapshot_space_label.setStyleSheet("color:#2e7d32; padding:4px;")
            if readiness["problems"]:
                self.snapshot_space_label.setText("⚠ " + " ".join(readiness["problems"]) + " El snapshot podría fallar al quedarse sin espacio.")
                self.snapshot_space_label.setStyleSheet("color:#b26a00; padding:4px;")
        for row in self._snapshot_rows():
            self.snapshot_list_widget.addTopLevelItem(QTreeWidgetItem(list(row)))
        self._update_snapshot_preview()
        # Si la vista del organigrama está activa, reconstruirla también.
        try:
            if (hasattr(self, 'snap_view_stack')
                    and self.snap_view_stack.currentIndex() == 1
                    and hasattr(self, 'refresh_snapshot_graph')):
                self.refresh_snapshot_graph()
        except Exception:
            pass

    def _snapshot_screenshot_dir(self):
        if not self.current_vm_dir:
            return ""
        path = os.path.join(self.current_vm_dir, "snapshots")
        os.makedirs(path, exist_ok=True)
        return path

    def _snapshot_screenshot_path(self, tag):
        base = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(tag or "snapshot")).strip("._") or "snapshot"
        return os.path.join(self._snapshot_screenshot_dir(), base + ".png")

    def _capture_snapshot_screenshot(self, tag):
        """Captura la pantalla del guest justo antes del snapshot, si QEMU lo soporta."""
        if not self._vm_is_selected():
            return None
        try:
            path = self._snapshot_screenshot_path(tag)
            result = self._qmp_command(self.current_vm_dir, {
                "execute": "screendump",
                "arguments": {"filename": path, "format": "png"}
            })
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                self._snapshot_log(f"[SNAPSHOT] ✓ Captura de pantalla guardada: {path}")
                return path
            raise RuntimeError("QEMU no generó el archivo de captura.")
        except Exception as e:
            self._snapshot_log(f"[SNAPSHOT] ⚠ No se pudo capturar la pantalla: {e}")
            return None

    def _update_snapshot_preview(self):
        """Actualiza la miniatura del snapshot seleccionado."""
        if not hasattr(self, "snapshot_preview_label"):
            return
        tag = self._selected_snapshot_tag()
        if not tag or not self.current_vm_dir:
            self._set_preview_pixmap(None)
            return
        path = self._snapshot_screenshot_path(tag)
        if os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self._set_preview_pixmap(pix)
                return
        self._set_preview_pixmap(None)

    def _set_preview_pixmap(self, pix):
        """Coloca el pixmap en el label del preview con el zoom actual."""
        try:
            from PyQt6.QtCore import Qt as _Qt
        except Exception:
            return
        if pix is None:
            try:
                self.snapshot_preview_label.setPixmap(QPixmap())
                self.snapshot_preview_label.setText("Sin captura de pantalla")
                self.snapshot_preview_label.resize(320, 180)
            except Exception:
                pass
            return
        zoom = float(getattr(self, "_snapshot_preview_zoom", 1.0) or 1.0)
        w = max(1, int(pix.width() * zoom))
        h = max(1, int(pix.height() * zoom))
        scaled = pix.scaled(
            w, h,
            _Qt.AspectRatioMode.KeepAspectRatio,
            _Qt.TransformationMode.SmoothTransformation,
        )
        try:
            self.snapshot_preview_label.setText("")
            self.snapshot_preview_label.setPixmap(scaled)
            self.snapshot_preview_label.resize(scaled.size())
        except Exception:
            pass

    def _change_preview_zoom(self, factor):
        cur = float(getattr(self, "_snapshot_preview_zoom", 1.0) or 1.0)
        new = max(0.1, min(5.0, cur * float(factor)))
        self._snapshot_preview_zoom = new
        try:
            self.snapshot_preview_zoom_label.setText(f"{int(round(new * 100))}%")
        except Exception:
            pass
        self._update_snapshot_preview()

    def _reset_preview_zoom(self):
        self._snapshot_preview_zoom = 1.0
        try:
            self.snapshot_preview_zoom_label.setText("100%")
        except Exception:
            pass
        self._update_snapshot_preview()


    def _selected_snapshot_tag(self):
        if not hasattr(self, 'snapshot_list_widget'): return None
        item=self.snapshot_list_widget.currentItem()
        return item.text(1).strip() if item else None

    def _qmp_named_block_nodes(self, vm_dir):
        """Devuelve nodos de bloque de QEMU con su archivo asociado, sin abrir los discos desde el host."""
        result = self._qmp_command(vm_dir, {"execute": "query-named-block-nodes"})
        rows = result.get("return") or []
        data = []
        for row in rows:
            node = str(row.get("node-name") or row.get("node_name") or "").strip()
            file_name = str(row.get("file") or "").strip()
            drv = str(row.get("driver") or "").strip().lower()
            if node:
                data.append({"node": node, "file": os.path.abspath(file_name) if file_name else "", "driver": drv, "raw": row})
        return data

    def _snapshot_qmp_nodes(self):
        """Resuelve identificadores de bloque para cada disco QCOW2 de la VM.

        Devuelve `(state_ref, [dict, ...])` donde cada dict tiene:
          • "device"    → id del BlockBackend (disk0, cdrom_0, ...). Es lo
                          que espera `blockdev-snapshot-internal-sync` en su
                          campo `device`.
          • "node_name" → nombre del nodo en el grafo de bloques. Es lo que
                          esperan `snapshot-save`, `snapshot-load` y
                          `snapshot-delete` en su campo `devices`.
          • "path"      → ruta absoluta del archivo del disco.
          • "name"      → etiqueta amigable para logs.

        `state_ref` es el identificador (node_name) que se usará para el
        vmstate: preferimos el disco que la readiness marca como
        `state_disk` y caemos al primero de la lista.
        """
        vm_dir = self.current_vm_dir
        storage = self._snapshot_candidate_disks()
        storage_by_path = {os.path.abspath(d["path"]): d for d in storage if d.get("path")}
        storage_by_base = {os.path.basename(os.path.abspath(d["path"])): d for d in storage if d.get("path")}

        # query-block da simultáneamente:
        #   • device              → id del BlockBackend (lo que necesita
        #                           blockdev-snapshot-internal-sync)
        #   • inserted.node-name  → nombre del nodo (lo que necesitan
        #                           snapshot-save/load/delete)
        #   • inserted.file       → ruta del archivo
        #   • inserted.drv        → driver (qcow2, raw, …)
        result = self._qmp_command(vm_dir, {"execute": "query-block"})
        rows = result.get("return") or []

        candidates = []
        seen_paths = set()
        for row in rows:
            device = str(row.get("device") or "").strip()
            inserted = row.get("inserted") or {}
            node_name = str(inserted.get("node-name") or inserted.get("node_name") or "").strip()
            path = str(inserted.get("file") or "").strip()
            drv = str(inserted.get("drv") or inserted.get("driver") or "").lower().strip()
            if not device or drv != "qcow2" or not path:
                continue
            apath = os.path.abspath(path)
            if apath in seen_paths:
                continue
            seen_paths.add(apath)
            d = storage_by_path.get(apath) or storage_by_base.get(os.path.basename(apath))
            if not d or d.get("format") != "qcow2" or not d.get("exists") or not d.get("writable"):
                continue
            candidates.append({
                "device": device,
                # Si QEMU no expone node-name (nodo implícito sin nombre), usamos
                # el propio device id. QEMU lo acepta como node-name en esos casos.
                "node_name": node_name or device,
                "path": apath,
                "name": d.get("name") or os.path.basename(apath),
            })

        # Fallback: en algunos builds muy antiguos, query-block no trae
        # inserted.drv para discos no removibles. Probamos query-named-block-nodes
        # para no quedarnos sin candidatos.
        if not candidates:
            for row in self._qmp_named_block_nodes(vm_dir):
                node = str(row.get("node") or "").strip()
                drv = str(row.get("driver") or "").lower().strip()
                raw_path = str(row.get("file") or "").strip()
                if not node or drv != "qcow2" or not raw_path:
                    continue
                apath = os.path.abspath(raw_path)
                d = storage_by_path.get(apath) or storage_by_base.get(os.path.basename(apath))
                if not d or d.get("format") != "qcow2" or not d.get("exists") or not d.get("writable"):
                    continue
                candidates.append({
                    "device": node,        # último recurso
                    "node_name": node,
                    "path": apath,
                    "name": d.get("name") or os.path.basename(apath),
                })

        if not candidates:
            # Diagnóstico detallado (igual que antes del fix).
            seen = []
            for row in self._qmp_named_block_nodes(vm_dir):
                seen.append(f"{row.get('node','?')}[{row.get('driver','?')}] → {row.get('file','')}")
            detail = "\n".join(seen[:40]) or "(QEMU no devolvió nodos nombrados)"
            detail += "\n\nDiagnóstico query-block:\n" + self._snapshot_dump_block_graph()
            raise RuntimeError(
                "QEMU no expone un nodo de formato QCOW2 escribible asociado a los discos de la VM.\n\n"
                "Nodos detectados por QEMU:\n" + detail
            )

        # Elegir state_ref entre los candidatos: preferimos el disco que la
        # readiness marca como state_disk; si no, el primero.
        state_disk = (self._snapshot_readiness().get("state_disk") or {})
        state_path = os.path.abspath(state_disk.get("path") or "")
        state_ref = None
        for c in candidates:
            if c["path"] == state_path:
                state_ref = c["node_name"]
                break
        if not state_ref:
            state_ref = candidates[0]["node_name"]

        return state_ref, candidates


    def _qmp_launch_snapshot_job(self, vm_dir, command, arguments, operation_label, timeout=1800, log_callback=None):
        """Ejecuta snapshot-save/load con una sola conexión QMP.

        Para snapshot-save/load QEMU puede detener las CPU durante una parte importante
        de la operación. No enviamos query-jobs continuamente mientras QEMU está en STOP,
        porque eso puede añadir esperas innecesarias al monitor. Seguimos principalmente
        JOB_STATUS_CHANGE y usamos query-jobs solo como comprobación cuando la VM vuelve a
        responder.
        """
        import socket, json as _json, time
        def log(message):
            if log_callback is not None:
                try:
                    log_callback(message)
                except Exception:
                    pass

        qmp = os.path.join(vm_dir, "qemu.qmp")
        if not os.path.exists(qmp):
            raise RuntimeError("El monitor QMP de la VM no está disponible.")

        def recv_message(sock, buffer, timeout=None):
            if timeout is not None:
                sock.settimeout(max(0.1, timeout))
            while True:
                pos = buffer.find(b"\r\n")
                if pos >= 0:
                    raw, buffer = buffer[:pos], buffer[pos + 2:]
                    if not raw:
                        continue
                    try:
                        return _json.loads(raw.decode("utf-8", errors="replace")), buffer
                    except Exception:
                        continue
                try:
                    chunk = sock.recv(8192)
                except socket.timeout:
                    raise
                if not chunk:
                    raise RuntimeError("QMP cerró la conexión antes de terminar el trabajo.")
                buffer += chunk
                if len(buffer) > 2 * 1024 * 1024:
                    raise RuntimeError("Respuesta QMP demasiado grande.")

        def send_command(sock, payload, command_id):
            req = dict(payload)
            req["id"] = command_id
            sock.sendall((_json.dumps(req, separators=(",", ":")) + "\r\n").encode("utf-8"))
            return req

        def error_text(value):
            if isinstance(value, dict):
                return str(value.get("desc") or value.get("class") or value)
            return str(value or "Error QMP desconocido")

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        buffer = b""
        launch_id = "snap_launch_" + str(int(time.time() * 1000000))
        job_id = str(arguments.get("job-id") or "")
        tag = str(arguments.get("tag") or "")
        last_status = None
        last_pct = None
        saw_running = False
        saw_stop = False
        saw_resume = False
        job_finished = False
        job_error = None
        deadline = time.monotonic() + float(timeout)
        last_safe_query = 0.0

        try:
            log(f"[SNAPSHOT] Conectando al monitor QMP para {operation_label}...")
            sock.connect(qmp)
            _, buffer = recv_message(sock, buffer, 5.0)

            cap_id = "cap_" + str(int(time.time() * 1000000))
            send_command(sock, {"execute": "qmp_capabilities"}, cap_id)
            while True:
                msg, buffer = recv_message(sock, buffer, 10.0)
                if str(msg.get("id") or "") != cap_id:
                    continue
                if "error" in msg:
                    raise RuntimeError(error_text(msg.get("error")))
                break

            log(f"[SNAPSHOT] Solicitando {command} '{tag}'...")
            send_command(sock, {"execute": command, "arguments": arguments}, launch_id)

            # La respuesta inicial y JOB_STATUS_CHANGE pueden llegar en distinto orden.
            # La recepción de created/running ya es una confirmación suficiente.
            accept_deadline = time.monotonic() + 20.0
            accepted = False
            while time.monotonic() < accept_deadline and not accepted:
                try:
                    msg, buffer = recv_message(sock, buffer, 1.0)
                except socket.timeout:
                    continue
                msg_id = str(msg.get("id") or "")
                event = msg.get("event")
                if event == "JOB_STATUS_CHANGE":
                    data = msg.get("data") or {}
                    if str(data.get("id")) != job_id:
                        continue
                    status = str(data.get("status") or "").lower()
                    if status != last_status:
                        log(f"[SNAPSHOT] {operation_label}: estado QMP = {status}.")
                        last_status = status
                    accepted = status in ("created", "running", "waiting", "pending", "concluded")
                    saw_running = saw_running or status == "running"
                    if status == "concluded":
                        job_finished = True
                        job_error = data.get("error")
                    elif status in ("aborting", "cancelled"):
                        job_finished = True
                        job_error = data.get("error") or f"QEMU terminó el trabajo en estado '{status}' sin proporcionar una descripción adicional."
                elif event in ("STOP", "RESUME"):
                    if event == "STOP":
                        saw_stop = True
                    else:
                        saw_resume = True
                    log(f"[SNAPSHOT] Evento QEMU: {event}.")
                elif msg_id == launch_id:
                    if "error" in msg:
                        raise RuntimeError(error_text(msg.get("error")))
                    accepted = True
                    log(f"[SNAPSHOT] ✓ QEMU aceptó {command}; el trabajo continúa de forma asíncrona.")

            if not accepted:
                # Última comprobación, todavía en la misma conexión.
                qid = "qj_accept_" + str(int(time.time() * 1000000))
                send_command(sock, {"execute": "query-jobs"}, qid)
                qdeadline = time.monotonic() + 5.0
                while time.monotonic() < qdeadline and not accepted:
                    try:
                        msg, buffer = recv_message(sock, buffer, 1.0)
                    except socket.timeout:
                        continue
                    if str(msg.get("id") or "") != qid:
                        event = msg.get("event")
                        if event == "JOB_STATUS_CHANGE" and str((msg.get("data") or {}).get("id")) == job_id:
                            accepted = True
                            status = str((msg.get("data") or {}).get("status") or "").lower()
                            last_status = status or last_status
                            log(f"[SNAPSHOT] ✓ Trabajo {job_id} detectado mediante JOB_STATUS_CHANGE ({status}).")
                        elif event in ("STOP", "RESUME"):
                            log(f"[SNAPSHOT] Evento QEMU: {event}.")
                        continue
                    if "error" in msg:
                        raise RuntimeError(error_text(msg.get("error")))
                    jobs = msg.get("return") or []
                    job = next((j for j in jobs if str(j.get("id")) == job_id), None)
                    if job is not None:
                        accepted = True
                        last_status = str(job.get("status") or "").lower() or last_status
                if not accepted:
                    raise RuntimeError(f"QMP no confirmó la aceptación de {command} para '{tag}'.")

            log(f"[SNAPSHOT] ✓ Trabajo {job_id} aceptado.")
            if saw_running:
                log("[SNAPSHOT] QEMU está ejecutando el trabajo; la VM puede quedar pausada durante la escritura del estado.")

            # Seguimiento: durante STOP escuchamos eventos, pero NO bombardeamos QEMU con
            # query-jobs. Cuando vuelve RESUME, se puede consultar de nuevo con seguridad.
            while time.monotonic() < deadline and not job_finished:
                try:
                    msg, buffer = recv_message(sock, buffer, 1.0)
                except socket.timeout:
                    now = time.monotonic()
                    if saw_stop and not saw_resume and command == "snapshot-save":
                        if int(now) % 10 == 0:
                            remaining = max(0, int(deadline - now))
                            log(f"[SNAPSHOT] QEMU mantiene la VM pausada mientras guarda el snapshot; esperando ({remaining}s de margen)...")
                    # Una consulta segura cada 2s solo cuando no estamos dentro de STOP.
                    if not saw_stop or saw_resume:
                        if now - last_safe_query >= 2.0:
                            qid = "qj_" + str(int(now * 1000000))
                            send_command(sock, {"execute": "query-jobs"}, qid)
                            last_safe_query = now
                    continue

                event = msg.get("event")
                if event == "JOB_STATUS_CHANGE":
                    data = msg.get("data") or {}
                    if str(data.get("id")) != job_id:
                        continue
                    status = str(data.get("status") or "").lower()
                    if status != last_status:
                        log(f"[SNAPSHOT] {operation_label}: estado QMP = {status}.")
                        last_status = status
                    if status == "running":
                        saw_running = True
                    if status == "concluded":
                        job_finished = True
                        job_error = data.get("error")
                    elif status in ("aborting", "cancelled"):
                        job_finished = True
                        job_error = data.get("error") or f"QEMU terminó el trabajo en estado '{status}' sin proporcionar una descripción adicional."
                    continue

                if event in ("STOP", "RESUME"):
                    if event == "STOP":
                        saw_stop = True
                        log("[SNAPSHOT] Evento QEMU: STOP — las CPU virtuales están pausadas mientras QEMU guarda el estado.")
                    else:
                        saw_resume = True
                        log("[SNAPSHOT] Evento QEMU: RESUME — las CPU virtuales volvieron a ejecutarse.")
                    continue

                msg_id = str(msg.get("id") or "")
                if msg_id == launch_id:
                    if "error" in msg:
                        raise RuntimeError(error_text(msg.get("error")))
                    continue

                if msg_id.startswith("qj_"):
                    if "error" in msg:
                        log(f"[SNAPSHOT] query-jobs devolvió error: {error_text(msg.get('error'))}")
                        continue
                    jobs = msg.get("return") or []
                    job = next((j for j in jobs if str(j.get("id")) == job_id), None)
                    if job is None:
                        # Puede auto-retirarse tras concluir; solo lo consideramos éxito
                        # si vimos explícitamente un estado de finalización.
                        continue
                    status = str(job.get("status") or "").lower()
                    if status != last_status:
                        log(f"[SNAPSHOT] {operation_label}: estado = {status}.")
                        last_status = status
                    cur = job.get("current-progress")
                    total = job.get("total-progress")
                    if isinstance(cur, (int, float)) and isinstance(total, (int, float)) and total:
                        pct = max(0, min(100, int(float(cur) / float(total) * 100)))
                        if pct != last_pct:
                            log(f"[SNAPSHOT] {operation_label}: {pct}% ({cur}/{total}).")
                            last_pct = pct
                    if status == "concluded":
                        job_finished = True
                        job_error = job.get("error")
                    elif status in ("aborting", "cancelled"):
                        job_finished = True
                        job_error = job.get("error") or f"QEMU terminó el trabajo en estado '{status}' sin proporcionar una descripción adicional."

            if not job_finished:
                # Si el job sigue running y la VM está pausada, no fingimos que falló:
                # dejamos un diagnóstico preciso para evitar un falso positivo.
                if command == "snapshot-save" and saw_stop and not saw_resume:
                    raise RuntimeError(
                        f"QEMU mantiene la VM pausada y no ha concluido '{tag}' dentro del margen de {int(timeout)} s. "
                        "El guest puede permanecer congelado durante un snapshot completo porque QEMU debe guardar el estado de la RAM y de los dispositivos. "
                        "No se informa como éxito hasta recibir JOB_STATUS_CHANGE=concluded."
                    )
                raise RuntimeError(f"Tiempo de espera agotado esperando el trabajo QMP '{job_id}'.")
            # Un job en estado aborting/cancelled JAMÁS se considera éxito.
            # Algunas versiones de QEMU no incluyen el campo error en el evento final,
            # por lo que hacemos una última consulta antes de informar el fallo.
            if last_status in ("aborting", "cancelled"):
                detail = error_text(job_error) if job_error else f"QEMU terminó el trabajo en estado '{last_status}'."
                try:
                    qid = "qj_final_" + str(int(time.time() * 1000000))
                    send_command(sock, {"execute": "query-jobs"}, qid)
                    final_deadline = time.monotonic() + 2.0
                    while time.monotonic() < final_deadline:
                        msg, buffer = recv_message(sock, buffer, 0.5)
                        if str(msg.get("id") or "") != qid:
                            event = msg.get("event")
                            if event == "RESUME":
                                saw_resume = True
                                log("[SNAPSHOT] Evento QEMU: RESUME — las CPU virtuales volvieron a ejecutarse.")
                            continue
                        if "error" not in msg:
                            jobs = msg.get("return") or []
                            job = next((j for j in jobs if str(j.get("id")) == job_id), None)
                            if job:
                                if job.get("error"):
                                    detail = error_text(job.get("error"))
                                elif job.get("status"):
                                    detail = f"QEMU terminó el trabajo en estado '{job.get('status')}'."
                        break
                except Exception:
                    pass
                raise RuntimeError(detail)

            if job_error:
                raise RuntimeError(error_text(job_error))

            log(f"[SNAPSHOT] ✓ Trabajo '{job_id}' concluido correctamente.")
            return {"status": "concluded", "id": job_id}
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _snapshot_dump_block_graph(self):
        """Devuelve un diagnóstico compacto del grafo de bloques de QEMU."""
        lines=[]
        try:
            r=self._qmp_command(self.current_vm_dir,{"execute":"query-block"})
            for row in (r.get("return") or []):
                ins=row.get("inserted") or {}
                lines.append(
                    f"device={row.get('device','?')} removable={row.get('removable',False)} "
                    f"node={ins.get('node-name','?')} drv={ins.get('drv','?')} "
                    f"file={ins.get('file','')} ro={ins.get('ro',False)}"
                )
        except Exception as e:
            lines.append(f"query-block falló: {e}")
        try:
            r=self._qmp_command(self.current_vm_dir,{"execute":"query-named-block-nodes","arguments":{"flat":True}})
            lines.append("-- query-named-block-nodes --")
            for row in (r.get("return") or []):
                lines.append(
                    f"node={row.get('node-name','?')} drv={row.get('drv','?')} "
                    f"file={row.get('file','')} ro={row.get('ro',False)}"
                )
        except Exception as e:
            lines.append(f"query-named-block-nodes falló: {e}")
        return "\n".join(lines)

    def _snapshot_graphics_blocker(self):
        """Detecta gráficos no migrables que impiden savevm/loadvm (p. ej. VirGL)."""
        if not self._vm_is_selected():
            return ""
        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        if state not in ("running", "paused"):
            return ""

        # Primero revisamos el proceso QEMU real: esto evita equivocarnos con
        # el modo configurado cuando está en "auto".
        try:
            pid_path = os.path.join(self.current_vm_dir, "qemu.pid")
            if os.path.isfile(pid_path):
                with open(pid_path, "r", encoding="utf-8") as f:
                    pid = f.read().strip()
                cmdline_path = f"/proc/{pid}/cmdline"
                if os.path.isfile(cmdline_path):
                    raw = Path(cmdline_path).read_bytes().replace(b"\x00", b" ").decode("utf-8", "ignore")
                    if "virtio-vga-gl" in raw or "virtio-gpu-gl" in raw or "venus=true" in raw or "-device\x00virtio-vga-gl" in raw:
                        return (
                            "QEMU está ejecutando la VM con VirtIO-GPU + VirGL/Venus, "
                            "y ese dispositivo gráfico no es migrable. QEMU bloquea los "
                            "snapshots completos (savevm) con este dispositivo. "
                            "Para crear un snapshot completo debes apagar la VM, cambiar "
                            "Gráficos/GPU a 'VirtIO-GPU 2D (compatible)' (o VGA estándar) "
                            "y volver a iniciarla antes de crear el snapshot."
                        )
        except Exception:
            pass

        # Fallback a la configuración guardada para VMs antiguas o si /proc no está disponible.
        try:
            cfg = load_vm_config(self.current_vm_dir)
            mode = str(cfg.get("graphics_mode") or "auto").lower()
            if mode in ("virgl", "venus"):
                return (
                    "La VM está configurada con gráficos VirGL/Venus, que no son "
                    "migrables para snapshots completos de QEMU. Cambia Gráficos/GPU "
                    "a 'VirtIO-GPU 2D (compatible)' o VGA estándar y reinicia la VM."
                )
        except Exception:
            pass
        return ""

    def _snapshot_log(self, message):
        """Registra un mensaje del snapshot.

        • En la consola de progreso global (log_message).
        • En el diálogo de snapshot si está abierto (append_log + set_progress
          cuando el mensaje incluya un porcentaje).
        • En la barra inline SOLO si el diálogo no está abierto (compatibilidad).
        """
        try:
            self.log_message(message)
        except Exception:
            pass

        # Extraer porcentaje del mensaje, si lo hay.
        pct = None
        try:
            m = re.search(r"(?<!\d)(\d{1,3})%(?!\d)", str(message))
            if m:
                pct = max(0, min(100, int(m.group(1))))
        except Exception:
            pct = None

        # Texto limpio (sin etiquetas HTML, sin prefijo [SNAPSHOT]).
        clean = re.sub(r"<[^>]+>", "", str(message))
        if clean.startswith("[SNAPSHOT] "):
            clean = clean[len("[SNAPSHOT] "):]

        # 1) Diálogo de snapshot (preferente).
        dlg = getattr(self, "_snapshot_progress_dialog", None)
        if dlg is not None:
            try:
                if pct is not None:
                    dlg.set_progress(pct, clean)
                # Añadir también al log del diálogo para que quede histórico.
                dlg.append_log(clean)
            except Exception:
                pass
            return

        # 2) Barra inline (fallback si no hay diálogo).
        try:
            if hasattr(self, "snapshot_progress_label"):
                self.snapshot_progress_label.setText(clean)
            if pct is not None and hasattr(self, "snapshot_progress_bar"):
                self.snapshot_progress_bar.setRange(0, 100)
                self.snapshot_progress_bar.setValue(pct)
        except Exception:
            pass


    def _create_live_disk_only_snapshot(self, name, readiness):
        """Crea snapshots internos de todos los QCOW2 mientras la VM está encendida.
        No guarda RAM/CPU; es una alternativa segura al snapshot completo en vivo.
        """
        self._snapshot_log("[SNAPSHOT] Modo: SOLO DISCOS (VM en ejecución).")
        _state_ref, device_list = self._snapshot_qmp_nodes()
        if not device_list:
            raise RuntimeError("No hay nodos QCOW2 elegibles para crear el snapshot de disco.")
        _names = [d.get('name') or d.get('device') for d in device_list]
        self._snapshot_log(f"[SNAPSHOT] Nodos QCOW2: {', '.join(_names)}")
        # blockdev-snapshot-internal-sync exige el campo 'device' con el
        # id del BlockBackend (disk0, cdrom_0, ...). Pasar 'node-name'
        # provoca "Parameter 'actions[0].data.device' is missing" en QEMU 11.
        actions = [{
            "type": "blockdev-snapshot-internal-sync",
            "data": {"device": d["device"], "name": name},
        } for d in device_list]
        result = self._qmp_command(self.current_vm_dir, {
            "execute": "transaction",
            "arguments": {"actions": actions},
        })
        if "error" in result:
            err = result.get("error") or {}
            raise RuntimeError(str(err.get("desc") or err.get("class") or err))
        return device_nodes

    # ------------------------------------------------------------------
    # Detección de gráficos problemáticos para snapshots
    # ------------------------------------------------------------------
    # VirtIO-GPU no permite restaurar snapshots completos: QEMU guarda su
    # estado pero no puede reconstruirlo ("Failed to load element of type
    # virtio for virtio"). QXL y VGA estándar sí funcionan.

    def _vm_graphics_mode(self):
        """Devuelve el modo de gráficos actual de la VM (o None)."""
        if not self.current_vm_dir:
            return None
        try:
            from vm_config import load_vm_config
            cfg = load_vm_config(self.current_vm_dir)
            return str(cfg.get("graphics_mode") or "auto").lower()
        except Exception:
            return None

    def _vm_graphics_is_problematic_for_snapshots(self):
        """True si el modo gráfico actual rompe la restauración de
        snapshots completos (RAM + dispositivos)."""
        mode = self._vm_graphics_mode()
        if mode is None:
            return False
        # virtio y virgl/venus no son serializables; auto se resuelve a
        # uno de ellos en la mayoría de configs Linux.
        return mode in ("virtio", "virgl", "venus", "auto")

    def _warn_virtio_gpu_snapshot(self):
        """Avisa si los gráficos actuales impiden RESTAURAR snapshots completos.

        IMPORTANTE: este aviso es solo para snapshots COMPLETOS (RAM +
        dispositivos). Los snapshots SOLO DE DISCOS sí funcionan con
        cualquier gráfico y se pueden restaurar con la VM apagada.

        Devuelve True si el usuario decide continuar.
        """
        if not self._vm_graphics_is_problematic_for_snapshots():
            return True
        mode = self._vm_graphics_mode() or "?"
        resp = QMessageBox.warning(
            self, "Snapshot con VirtIO-GPU",
            f"Esta VM está configurada con gráficos '{mode}', que no permiten\n"
            "RESTAURAR snapshots completos en QEMU (RAM + dispositivos).\n"
            "\n"
            "El snapshot se puede crear, pero al intentar restaurarlo QEMU\n"
            "fallará con: 'Failed to load element of type virtio for virtio'.\n"
            "\n"
            "Opciones:\n"
            "  • Usar snapshot SOLO DE DISCOS (elegir 'No' en el siguiente\n"
            "    diálogo). No guarda RAM ni estado de ventanas, pero se\n"
            "    restaura sin problema con la VM apagada.\n"
            "  • Cambiar Gráficos/GPU a 'Red Hat QXL 2D' o 'VMware SVGA II',\n"
            "    reiniciar la VM y crear snapshots completos.\n"
            "\n"
            "¿Crear el snapshot igualmente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return resp == QMessageBox.StandardButton.Yes


    def create_snapshot_from_page(self):
        if not self._vm_is_selected():
            QMessageBox.information(self,'Snapshots','Selecciona una máquina virtual.'); return
        readiness=self._snapshot_readiness()
        if not readiness["state_disk"]:
            self._snapshot_log("[SNAPSHOT] ERROR: no hay un QCOW2 elegible para guardar el estado de la VM.")
            QMessageBox.warning(self,'Snapshots', 'No se puede crear un snapshot completo.\n\n' + '\n'.join(readiness["problems"] or ['Se necesita al menos un disco QCOW2 escribible y no removible.']))
            return
        if readiness["problems"]:
            details='\n'.join(readiness["problems"])
            reply=QMessageBox.warning(self,'Espacio disponible', f"{details}\n\nQEMU puede necesitar espacio adicional a medida que cambien los bloques. ¿Quieres continuar de todos modos?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        # Avisar si los gráficos actuales harán que el snapshot no
        # se pueda restaurar (virtio-gpu, virgl, venus).
        try:
            if not self._warn_virtio_gpu_snapshot():
                return
        except Exception:
            pass
        name,ok=QInputDialog.getText(self,'Crear snapshot','Nombre del snapshot:')
        if not ok or not name.strip(): return
        name=name.strip().replace(' ','_')
        state=self._runtime_state(os.path.basename(self.current_vm_dir))
        self._snapshot_log("\n========== SNAPSHOT ==========")
        self._snapshot_log(f"[SNAPSHOT] Iniciando snapshot '{name}'...")
        self._snapshot_log(f"[SNAPSHOT] Estado actual de la VM: {state}")
        try:
            _usb_passthrough = [d for d in (getattr(self, "_passthrough_saved", []) or []) if d.get("kind") == "usb"]
            if _usb_passthrough:
                self._snapshot_log("[SNAPSHOT] ⚠ Hay USB passthrough seleccionado. QEMU documenta soporte incompleto de snapshots para dispositivos USB; el estado del USB puede no quedar guardado/restaurado correctamente.")
        except Exception:
            pass
        import time
        self._snapshot_log(f"[SNAPSHOT] Disco para estado de VM: {readiness['state_disk']['name']}")
        self._snapshot_log(f"[SNAPSHOT] QCOW2 escribibles incluidos: {len(readiness['eligible'])}")
        for d in readiness['eligible']:
            self._snapshot_log(f"[SNAPSHOT]   • {d['name']} | {self._format_bytes(d.get('virtual_size',0))} | archivo: {self._format_bytes(d.get('actual_size',-1))} | libre host: {self._format_bytes(d.get('free',-1))}")
        try:
            if state in ('running','paused'):
                choice = QMessageBox.question(
                    self,
                    'Snapshot con la VM encendida',
                    "La VM está encendida.\n\n"
                    "Un snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y "
                    "puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos "
                    "observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\n"
                    "Sí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
                    "No = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\n"
                    "Cancelar = no hacer nada.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.No,
                )
                if choice == QMessageBox.StandardButton.Cancel:
                    return
                if choice == QMessageBox.StandardButton.No:
                    try:
                        self._snapshot_log("\n========== SNAPSHOT DE DISCOS ==========")
                        self._snapshot_log(f"[SNAPSHOT] Iniciando snapshot de discos '{name}'...")
                        self._snapshot_log(f"[SNAPSHOT] Estado actual de la VM: {state}")
                        self._capture_snapshot_screenshot(name)
                        nodes = self._create_live_disk_only_snapshot(name, readiness)
                        self._snapshot_log(f"[SNAPSHOT] ✓ Snapshot de discos '{name}' creado en {len(nodes)} QCOW2.")
                        self._snapshot_log("[SNAPSHOT] ✓ Creación finalizada. No se guardó RAM/CPU.")
                        QMessageBox.information(
                            self,
                            'Snapshot de discos creado',
                            f"Se creó '{name}' en {len(nodes)} QCOW2.\n\n"
                            "Este snapshot no contiene la memoria RAM ni el estado de las ventanas. "
                            "Para restaurarlo, la VM debe estar apagada."
                        )
                        self.refresh_snapshot_page()
                    except Exception as e:
                        msg = str(e)
                        self._snapshot_log(f"[SNAPSHOT] ✗ SNAPSHOT DE DISCOS FALLIDO: {msg}")
                        self._show_selectable_error('Error al crear snapshot de discos', msg)
                    return

                self._snapshot_log("[SNAPSHOT] Modo: SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).")
                self._snapshot_log("[SNAPSHOT] VM en ejecución: usando QMP moderno 'snapshot-save'.")
                self._snapshot_log("[SNAPSHOT] Consultando nodos de bloque expuestos por QEMU...")
                state_ref, device_list = self._snapshot_qmp_nodes()
                node_names = [d["node_name"] for d in device_list]
                job_id = "snap_save_" + re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:40] + "_" + str(int(time.time()))
                self._snapshot_log(f"[SNAPSHOT] Nodo para VM state: {state_ref}")
                self._snapshot_log(f"[SNAPSHOT] Nodos QCOW2 incluidos: {', '.join(node_names)}")
                try:
                    ram_gb = float(re.sub(r"[^0-9.]", "", str(readiness['ram']))) if readiness.get('ram') else None
                except Exception:
                    ram_gb = None
                if ram_gb:
                    self._snapshot_log(f"[SNAPSHOT] Estado de RAM a guardar: aproximadamente {ram_gb:.1f} GB.")
                free_host = readiness.get('state_disk', {}).get('free', -1)
                if free_host >= 0:
                    self._snapshot_log(f"[SNAPSHOT] Espacio libre en el sistema de archivos del disco de estado: {self._format_bytes(free_host)}.")
                    if ram_gb and free_host < int(ram_gb * 1024**3):
                        self._snapshot_log("[SNAPSHOT] ⚠ El espacio libre del host es inferior a la RAM configurada; el snapshot completo puede fallar.")
                self._snapshot_log("[SNAPSHOT] Advertencia: QEMU puede pausar completamente el guest durante snapshot-save.")
                self._snapshot_log(f"[SNAPSHOT] Preparando snapshot de memoria RAM ({self._format_bytes(int((ram_gb or 0) * 1024**3)) if ram_gb else 'tamaño desconocido'})...")
                try:
                    _cfg = load_vm_config(self.current_vm_dir) if self.current_vm_dir else {}
                    _cores = int(_cfg.get("cores", 2) or 2)
                except Exception:
                    _cores = 2
                self._snapshot_log(f"[SNAPSHOT] Guardando estado del procesador ({_cores} vCPU)...")
                for d in readiness["eligible"]:
                    self._snapshot_log(f"[SNAPSHOT] Preparando snapshot del disco duro '{d['name']}'...")
                self._capture_snapshot_screenshot(name)
                self._snapshot_log(f"[SNAPSHOT] Solicitando snapshot-save '{name}'...")
                self._start_snapshot_worker(
                    self.current_vm_dir, "snapshot-save",
                    {"job-id":job_id,"tag":name,"vmstate":state_ref,"devices":node_names},
                    f"Creando '{name}'",
                    name, "create"
                )
                return
            else:
                self._snapshot_log("[SNAPSHOT] VM apagada: creando snapshots internos del tag en cada QCOW2 elegible.")
                created=0
                for d in readiness["eligible"]:
                    self._snapshot_log(f"[SNAPSHOT] Creando snapshot del disco duro '{d['name']}'...")
                    proc=subprocess.run(['qemu-img','snapshot','-c',name,d['path']],capture_output=True,text=True,timeout=30)
                    if proc.returncode != 0:
                        raise RuntimeError(f"{d['name']}: {(proc.stderr or proc.stdout).strip()}")
                    created += 1
                    self._snapshot_log(f"[SNAPSHOT] ✓ Snapshot de disco creado en {d['name']}.")
                self._snapshot_log(f"[SNAPSHOT] ✓ Creación finalizada en {created} disco(s). Con la VM apagada no se guarda RAM/CPU.")
                QMessageBox.information(self,'Snapshot creado',f"Se creó el snapshot de disco '{name}' en {created} QCOW2 elegible(s). Con la VM apagada no se guarda RAM/CPU.")
                self.refresh_snapshot_page()
        except Exception as e:
            msg = str(e)
            self._snapshot_log(f"[SNAPSHOT] ✗ CREACIÓN FALLIDA: {msg}")
            if 'virgl is not yet migratable' in msg.lower() or 'not migratable' in msg.lower():
                msg += ('\n\nCausa: el dispositivo gráfico VirGL/Venus activo no permite guardar el estado migrable de la VM.\n'
                        'Si necesitas un snapshot completo, cambia temporalmente la GPU a VirtIO-GPU 2D (compatible) o VGA estándar y reinicia la VM.')
            self._show_selectable_error('Error al crear snapshot', f'No se pudo crear el snapshot completo.\n\n{msg}')

    def _start_snapshot_worker(self, vm_dir, command, arguments,
                               operation_label, tag, mode):
        """Inicia el worker de snapshot y muestra un TaskProgressDialog.

        Sustituye la barra inline de la pestaña Snapshots por el mismo
        diálogo que se usa para la descarga de ISO: título, estado, barra,
        log en vivo y botón de cierre.
        """
        if getattr(self, "_snapshot_worker", None) is not None \
                and self._snapshot_worker.isRunning():
            QMessageBox.information(
                self, "Snapshots",
                "Ya hay una operación de snapshot en curso.",
            )
            return

        worker = SnapshotOperationWorker(
            self, vm_dir, command, arguments, operation_label,
            timeout=1800, parent=self,
        )
        self._snapshot_worker = worker
        self._snapshot_operation_tag = tag
        self._snapshot_operation_mode = mode

        # --- Diálogo modal de progreso (mismo widget que ISO) ---
        subtitle = (
            "La operación se ejecuta en segundo plano; la interfaz sigue "
            "disponible mientras QEMU procesa el snapshot."
        )
        try:
            dlg = TaskProgressDialog(
                f"Snapshot — {operation_label}",
                self,
                cancelable=False,
                show_log=True,
                subtitle=subtitle,
            )
            dlg.set_progress(-1, "Iniciando…")
            self._snapshot_progress_dialog = dlg
            # Conectar el log del worker al diálogo (append en vivo).
            worker.log_signal.connect(dlg.append_log)
            # Mostrar el diálogo sin bloquear.
            dlg.show()
        except Exception as e:
            log_err = f"[AVISO] No se pudo crear el diálogo de progreso: {e}"
            try:
                self.log_message(log_err)
            except Exception:
                print(log_err)
            self._snapshot_progress_dialog = None

        # Ocultar la barra inline (ya no se usa durante la operación).
        try:
            if hasattr(self, "snapshot_progress_bar"):
                self.snapshot_progress_bar.setVisible(False)
            if hasattr(self, "snapshot_progress_label"):
                self.snapshot_progress_label.setVisible(False)
        except Exception:
            pass

        # Señales del worker.
        worker.log_signal.connect(self._snapshot_log)
        worker.success_signal.connect(self._snapshot_worker_succeeded)
        worker.error_signal.connect(self._snapshot_worker_failed)
        worker.finished.connect(lambda: setattr(self, "_snapshot_worker", None))

        worker.start()
        self._snapshot_log(
            "[SNAPSHOT] Operación iniciada en segundo plano."
        )


    def _finish_snapshot_progress_dialog(self, ok, tag, mode, error_msg=""):
        """Cierra el diálogo de snapshot y restaura la barra inline.

        Se llama al terminar (éxito o error) la operación de snapshot.
        """
        dlg = getattr(self, "_snapshot_progress_dialog", None)
        if dlg is not None:
            try:
                if ok:
                    if mode == "pause":
                        msg = f"Estado '{tag}' guardado y VM pausada."
                    elif mode == "delete":
                        msg = f"Snapshot '{tag}' eliminado."
                    elif mode == "restore":
                        msg = f"Snapshot '{tag}' restaurado."
                    else:
                        msg = f"Snapshot '{tag}' creado."
                    dlg.finish(True, msg)
                else:
                    dlg.finish(False, error_msg or "Operación fallida.")
            except Exception:
                pass
            try:
                dlg.deleteLater()
            except Exception:
                pass
            self._snapshot_progress_dialog = None

        # Restaurar la barra inline (que se ocultó al iniciar).
        try:
            if hasattr(self, "snapshot_progress_bar"):
                self.snapshot_progress_bar.setVisible(True)
                self.snapshot_progress_bar.setValue(0)
            if hasattr(self, "snapshot_progress_label"):
                self.snapshot_progress_label.setVisible(True)
                self.snapshot_progress_label.setText("Sin operación de snapshot")
        except Exception:
            pass

    def _snapshot_worker_succeeded(self, result):
        tag = getattr(self, '_snapshot_operation_tag', '')
        mode = getattr(self, '_snapshot_operation_mode', '')
        # Cerrar el diálogo de progreso con éxito.
        self._finish_snapshot_progress_dialog(True, tag, mode)
        try:
            self._snapshot_log(f"[SNAPSHOT] ✓ Trabajo QMP concluido: {result.get('id') if isinstance(result, dict) else result}")
            if mode == 'create':
                tags={row[1] for row in (self._parse_snapshot_line(x) for x in self._snapshot_list()) if row and row[1]}
                if tag not in tags:
                    raise RuntimeError(f"El trabajo terminó, pero QEMU no muestra el snapshot '{tag}' en info snapshots.")
                self._snapshot_log(f"[SNAPSHOT] ✓ Snapshot '{tag}' confirmado por QEMU.")
                self._snapshot_log("[SNAPSHOT] ✓ Creación finalizada.")
                if hasattr(self, "snapshot_progress_bar"):
                    self.snapshot_progress_bar.setValue(100)
                if hasattr(self, "snapshot_progress_label"):
                    self.snapshot_progress_label.setText("Snapshot finalizado (100%).")
                self.refresh_snapshot_page()
                QMessageBox.information(self,'Snapshot creado',f"El snapshot '{tag}' fue creado y confirmado por QEMU.")
            elif mode == 'pause':
                # El snapshot se creó correctamente; ahora pausamos la VM.
                self._snapshot_log(f"[SNAPSHOT] ✓ Estado '{tag}' guardado en disco.")
                try:
                    self._qmp_hmp(self.current_vm_dir, "stop")
                    self._snapshot_log("[SNAPSHOT] ✓ VM pausada.")
                except Exception as stop_err:
                    self._snapshot_log(f"[AVISO] No se pudo pausar tras guardar: {stop_err}")
                if hasattr(self, "snapshot_progress_bar"):
                    self.snapshot_progress_bar.setValue(100)
                if hasattr(self, "snapshot_progress_label"):
                    self.snapshot_progress_label.setText("Estado guardado; VM pausada.")
                self.refresh_snapshot_page()
                QMessageBox.information(
                    self, 'VM pausada',
                    f"Estado guardado como '{tag}'.\n\nLa VM quedó pausada. "
                    "Puedes reanudarla con el botón Pausar/Reanudar.",
                )
            elif mode == 'delete':
                self._snapshot_log(f"[SNAPSHOT] ✓ Eliminación de '{tag}' finalizada.")
                shot = self._snapshot_screenshot_path(tag) if self.current_vm_dir else ""
                if shot and os.path.isfile(shot):
                    try: os.remove(shot)
                    except OSError: pass
                self.refresh_snapshot_page()
                QMessageBox.information(self,'Snapshot eliminado',f"Se eliminó '{tag}'.")
            else:
                self._snapshot_log(f"[SNAPSHOT] ✓ Restauración de '{tag}' finalizada.")
                status = self._runtime_state(os.path.basename(self.current_vm_dir))
                self._snapshot_log(f"[SNAPSHOT] Estado de QEMU después de la operación: {status}")
                if status in ('paused','save-vm','restore-vm'):
                    self._qmp_hmp(self.current_vm_dir, 'cont')
                    self._snapshot_log("[SNAPSHOT] ✓ VM reanudada.")
                self.refresh_snapshot_page()
                QMessageBox.information(self,'Snapshot restaurado',f"Se restauró '{tag}'.")
        except Exception as e:
            self._snapshot_worker_failed(str(e))

    def _snapshot_worker_failed(self, message):
        tag = getattr(self, '_snapshot_operation_tag', '')
        mode = getattr(self, '_snapshot_operation_mode', '')
        # Cerrar el diálogo de progreso con error.
        self._finish_snapshot_progress_dialog(False, tag, mode,
                                               error_msg=str(message))
        if mode == 'create':
            title, action = 'Error al crear snapshot', 'CREACIÓN'
        elif mode == 'delete':
            title, action = 'Error al eliminar snapshot', 'ELIMINACIÓN'
        elif mode == 'pause':
            title, action = 'Error al guardar estado', 'GUARDADO'
        else:
            title, action = 'Error al restaurar snapshot', 'RESTAURACIÓN'
        self._snapshot_log(f"[SNAPSHOT] ✗ {action} FALLIDA: {message}")
        if hasattr(self, "snapshot_progress_label"):
            self.snapshot_progress_label.setText(f"{action.capitalize()} fallida")
        if hasattr(self, "snapshot_progress_bar"):
            self.snapshot_progress_bar.setValue(0)
        if mode == 'create' and self.current_vm_dir and tag:
            try:
                shot = self._snapshot_screenshot_path(tag)
                if os.path.isfile(shot): os.remove(shot)
            except Exception:
                pass
        # Si una operación de snapshot dejó el guest detenido, intenta devolverlo
        # al estado ejecutándose para evitar que un fallo de snapshot congele la VM.
        try:
            if mode == 'create' and self._vm_is_selected():
                name_vm = os.path.basename(self.current_vm_dir)
                state_now = self._runtime_state(name_vm)
                if state_now == 'paused':
                    self._snapshot_log('[SNAPSHOT] La VM quedó pausada tras el fallo; enviando cont para recuperar la ejecución.')
                    self._qmp_hmp(self.current_vm_dir, 'cont')
                    self._snapshot_log('[SNAPSHOT] ✓ VM reanudada tras el fallo del snapshot.')
        except Exception as resume_error:
            self._snapshot_log(f'[SNAPSHOT] ⚠ No se pudo reanudar automáticamente la VM: {resume_error}')
        # Si el usuario pidió "guardar y pausar" y el snapshot falló, pausamos
        # igualmente: la pausa era la acción principal que él eligió.
        if mode == 'pause' and self._vm_is_selected():
            try:
                state_now = self._runtime_state(os.path.basename(self.current_vm_dir))
                if state_now == 'running':
                    self._snapshot_log(
                        "[SNAPSHOT] El guardado falló; se pausa la VM igualmente "
                        "porque era la acción solicitada."
                    )
                    self._qmp_hmp(self.current_vm_dir, "stop")
            except Exception as pause_err:
                self._snapshot_log(f"[AVISO] Tampoco se pudo pausar: {pause_err}")
        msg=str(message)
        if 'virgl is not yet migratable' in msg.lower() or 'not migratable' in msg.lower():
            msg += ('\n\nCausa: el dispositivo gráfico VirGL/Venus activo no permite guardar el estado migrable de la VM.\n'
                    'Cambia Gráficos/GPU a VirtIO-GPU 2D (compatible) o VGA estándar y reinicia la VM antes de intentarlo de nuevo.')
        self._show_selectable_error(title, f"No se pudo completar la operación de snapshot '{tag}'.\n\n{msg}")
        self.refresh_snapshot_page()

    def restore_snapshot_from_page(self):
        tag=self._selected_snapshot_tag()
        if not tag:
            QMessageBox.information(self,'Snapshots','Selecciona un snapshot.'); return
        if QMessageBox.warning(self,'Restaurar snapshot',f"¿Restaurar '{tag}'?\n\nLa VM volverá al estado del snapshot.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self._snapshot_log("\n========== RESTAURACIÓN DE SNAPSHOT ==========")
        self._snapshot_log(f"[SNAPSHOT] Iniciando restauración de '{tag}'...")
        try:
            state=self._runtime_state(os.path.basename(self.current_vm_dir))
            self._snapshot_log(f"[SNAPSHOT] Estado actual de la VM: {state}")
            if state in ('running','paused'):
                self._snapshot_log(f"[SNAPSHOT] VM en ejecución: usando QMP moderno 'snapshot-load' para '{tag}'.")
                state_ref, device_list = self._snapshot_qmp_nodes()
                node_names = [d["node_name"] for d in device_list]
                job_id = "snap_load_" + re.sub(r"[^A-Za-z0-9_.-]", "_", tag)[:40] + "_" + str(int(time.time()))
                self._snapshot_log(f"[SNAPSHOT] Nodo para VM state: {state_ref}")
                self._snapshot_log(f"[SNAPSHOT] Nodos QCOW2 incluidos: {', '.join(node_names)}")
                self._snapshot_log(f"[SNAPSHOT] Solicitando snapshot-load '{tag}'...")
                try:
                    self._qmp_launch_snapshot_job(
                        self.current_vm_dir,
                        "snapshot-load",
                        {"job-id":job_id,"tag":tag,"vmstate":state_ref,"devices":node_names},
                        f"Restaurando '{tag}'"
                    )
                except Exception as modern_error:
                    modern_text=str(modern_error)
                    self._snapshot_log(f"[SNAPSHOT] snapshot-load no pudo completar: {modern_text}")
                    self._snapshot_log("[SNAPSHOT] Diagnóstico del grafo de bloques:")
                    self._snapshot_log(self._snapshot_dump_block_graph())
                    if any(k in modern_text.lower() for k in (
                        "does not support snapshots", "not supported", "unknown command",
                        "commandnotfound", "unsupported")): 
                        self._snapshot_log("[SNAPSHOT] Intentando fallback HMP 'loadvm'...")
                        self._qmp_hmp(self.current_vm_dir, "loadvm " + tag)
                        self._snapshot_log(f"[SNAPSHOT] ✓ Fallback HMP 'loadvm {tag}' aceptado.")
                    else:
                        raise
                status = self._runtime_state(os.path.basename(self.current_vm_dir))
                self._snapshot_log(f"[SNAPSHOT] Estado de QEMU después de snapshot-load: {status}")
                if status in ("paused", "save-vm", "restore-vm"):
                    self._snapshot_log("[SNAPSHOT] La VM quedó pausada; reanudando con 'cont'...")
                    self._qmp_hmp(self.current_vm_dir, 'cont')
                    self._snapshot_log("[SNAPSHOT] ✓ VM reanudada.")
                self._snapshot_log(f"[SNAPSHOT] ✓ Restauración de '{tag}' finalizada.")
                QMessageBox.information(self,'Snapshot restaurado',f"Se restauró '{tag}' mediante snapshot-load.")
            else:
                restored=0; errors=[]
                candidates=[d for d in self._snapshot_candidate_disks() if d.get("format")=="qcow2" and d.get("path") and d.get("exists")]
                self._snapshot_log(f"[SNAPSHOT] VM apagada: se intentará restaurar '{tag}' en {len(candidates)} QCOW2.")
                for d in candidates:
                    self._snapshot_log(f"[SNAPSHOT] Restaurando en {d['name']}...")
                    proc=subprocess.run(['qemu-img','snapshot','-a',tag,d['path']],capture_output=True,text=True,timeout=30)
                    if proc.returncode == 0:
                        restored += 1
                        self._snapshot_log(f"[SNAPSHOT] ✓ Restaurado en {d['name']}.")
                    else:
                        err=(proc.stderr or proc.stdout).strip()
                        errors.append(f"{d.get('name')}: {err}")
                        self._snapshot_log(f"[SNAPSHOT] ✗ Falló en {d['name']}: {err}")
                if restored == 0:
                    raise RuntimeError("No se pudo restaurar el snapshot en ningún QCOW2.\n\n" + "\n".join(errors))
                self._snapshot_log(f"[SNAPSHOT] ✓ Restauración de discos finalizada: {restored} OK / {len(errors)} con error.")
                if errors:
                    self._show_selectable_error('Restauración parcial', 'El snapshot se restauró en algunos discos, pero falló en otros:\n\n' + "\n".join(errors))
                else:
                    QMessageBox.information(self,'Snapshot restaurado','Se restauró el snapshot de disco en los QCOW2 elegibles. Con la VM apagada no se restaura el estado de RAM/CPU.')
        except Exception as e:
            msg = str(e)
            # Caso especial: virtio-gpu rompe la restauración.
            if self._is_virtio_gpu_restore_error(msg):
                self._snapshot_log(
                    '[SNAPSHOT] ERROR: virtio-gpu no permite restaurar snapshots.'
                )
                self._show_virtio_gpu_restore_help()
                self.refresh_snapshot_page()
                return
            # Durante snapshot-load QEMU puede cambiar transitoriamente el estado de la VM
            # y una conexión QMP nueva puede no observar el job antes de que auto-dismiss
            # lo retire. Si el error es solo de espera, comprobamos el estado de la VM antes
            # de declarar un fallo.
            if "tiempo de espera" in msg.lower() or "timed out" in msg.lower():
                try:
                    time.sleep(1.0)
                    status = self._runtime_state(os.path.basename(self.current_vm_dir))
                    self._snapshot_log(f"[SNAPSHOT] La espera QMP terminó por timeout; estado actual de la VM: {status}")
                    if status in ("running", "paused"):
                        self._snapshot_log(f"[SNAPSHOT] ✓ La VM sigue operativa después de restaurar '{tag}'.")
                        if status == "paused":
                            try:
                                self._qmp_hmp(self.current_vm_dir, "cont")
                                self._snapshot_log("[SNAPSHOT] ✓ VM reanudada después de la restauración.")
                            except Exception:
                                pass
                        QMessageBox.information(self,'Snapshot restaurado',f"La VM volvió a un estado operativo después de restaurar '{tag}'.\n\nQEMU no confirmó el fin del job dentro del tiempo de espera, pero la restauración se aplicó.")
                        self.refresh_snapshot_page()
                        return
                except Exception as verify_error:
                    self._snapshot_log(f"[SNAPSHOT] No se pudo verificar el estado tras timeout: {verify_error}")
            self._snapshot_log(f"[SNAPSHOT] ✗ RESTAURACIÓN FALLIDA: {msg}")
            self._show_selectable_error('Error al restaurar snapshot', f'No se pudo restaurar el snapshot.\n\n{msg}')
        self.refresh_snapshot_page()

    @staticmethod
    def _is_virtio_gpu_restore_error(msg):
        """True si el error de QEMU corresponde a un fallo por virtio-gpu.

        Se detecta por el patrón 'element of type virtio for virtio' o
        'virtio-gpu' en el mensaje. Cuando eso ocurre, mostramos un
        mensaje específico en lugar del genérico de QEMU.
        """
        low = str(msg or "").lower()
        return ("element of type virtio for virtio" in low
                or "virtio-gpu" in low)

    def _show_virtio_gpu_restore_help(self):
        """Muestra un aviso específico cuando la restauración falla por
        virtio-gpu. Ofrece continuar sin más (no cambia nada)."""
        mode = self._vm_graphics_mode() or "?"
        QMessageBox.warning(
            self, "No se puede restaurar este snapshot",
            f"QEMU no puede restaurar el snapshot por un problema conocido "
            "con el dispositivo VirtIO-GPU.\n\n"
            "Detalle técnico:\n"
            "  VirtIO-GPU guarda un estado interno que no es serializable "
            "de forma fiable. QEMU intenta reconstruirlo al restaurar y "
            "falla. No es un bug de la app, es una limitación del motor.\n\n"
            "Cómo resolverlo:\n"
            "  1. Abre Configuración → Pantalla.\n"
            "  2. Cambia 'Gráficos / GPU' de '{mode}' a 'Red Hat QXL 2D'.\n"
            "  3. Reinicia la VM (apágala y vuelve a arrancarla).\n"
            "  4. Crea snapshots nuevos a partir de ese momento: se podrán "
            "restaurar sin problemas.\n\n"
            "Los snapshots antiguos creados con virtio-gpu no se pueden "
            "recuperar (QEMU no puede reconstruir su estado). Si ya no los "
            "necesitas, elimínalos.",
        )

    def delete_snapshot_from_page(self):
        tag=self._selected_snapshot_tag()
        if not tag: QMessageBox.information(self,'Snapshots','Selecciona un snapshot.'); return
        if QMessageBox.question(self,'Eliminar snapshot',f"¿Eliminar '{tag}'?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        try:
            state=self._runtime_state(os.path.basename(self.current_vm_dir))
            if state in ('running','paused'):
                self._snapshot_log(f"\n========== ELIMINACIÓN DE SNAPSHOT ==========")
                self._snapshot_log(f"[SNAPSHOT] Iniciando eliminación de '{tag}'...")
                _state_ref, device_list = self._snapshot_qmp_nodes()
                node_names = [d["node_name"] for d in device_list]
                # snapshot-delete solo debe recibir los nodos QCOW2 reales; nunca pflash/OVMF.
                job_id = "snap_delete_" + re.sub(r"[^A-Za-z0-9_.-]", "_", tag)[:40] + "_" + str(int(time.time()))
                self._snapshot_log(f"[SNAPSHOT] QCOW2 afectados: {', '.join(node_names)}")
                self._start_snapshot_worker(self.current_vm_dir, "snapshot-delete",
                    {"job-id":job_id,"tag":tag,"devices":node_names},
                    f"Eliminando '{tag}'", tag, "delete")
                return
            else:
                deleted=0; errors=[]
                for d in self._snapshot_candidate_disks():
                    if d.get("format") != "qcow2" or not d.get("path") or not d.get("exists"):
                        continue
                    proc=subprocess.run(['qemu-img','snapshot','-d',tag,d['path']],capture_output=True,text=True,timeout=30)
                    if proc.returncode == 0:
                        deleted += 1
                    elif 'not found' not in (proc.stderr or '').lower():
                        errors.append(f"{d.get('name')}: {(proc.stderr or proc.stdout).strip()}")
                if deleted == 0 and errors:
                    raise RuntimeError("No se pudo eliminar el snapshot.\n\n" + "\n".join(errors))
                if errors:
                    self._show_selectable_error('Eliminación parcial', 'El snapshot se eliminó de algunos discos, pero falló en otros:\n\n' + "\n".join(errors))
            self.refresh_snapshot_page()
        except Exception as e:
            self._show_selectable_error('Error al eliminar snapshot', f'No se pudo eliminar el snapshot.\n\n{e}')

    def rename_snapshot_from_page(self):
        old=self._selected_snapshot_tag()
        if not old: QMessageBox.information(self,'Snapshots','Selecciona un snapshot.'); return
        new,ok=QInputDialog.getText(self,'Cambiar nombre',f"Nuevo nombre para '{old}':")
        if not ok or not new.strip(): return
        new=new.strip().replace(' ','_')
        if new == old: return
        reply=QMessageBox.warning(self,'Cambiar nombre de snapshot',
            'QEMU no proporciona un renombrado interno directo. Esta acción creará un snapshot nuevo con el estado ACTUAL de la VM y eliminará el anterior.\n\n¿Continuar?',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            state=self._runtime_state(os.path.basename(self.current_vm_dir))
            if state in ('running','paused'):
                self._qmp_hmp(self.current_vm_dir, 'savevm ' + new)
                self._qmp_hmp(self.current_vm_dir, 'delvm ' + old)
            else:
                targets=[d for d in self._snapshot_candidate_disks() if d.get("format") == "qcow2" and d.get("path") and d.get("exists")]
                if not targets:
                    raise RuntimeError("No hay QCOW2 disponibles para renombrar el snapshot.")
                created=0; errors=[]
                for d in targets:
                    p1=subprocess.run(['qemu-img','snapshot','-c',new,d['path']],capture_output=True,text=True,timeout=30)
                    if p1.returncode == 0:
                        created += 1
                        p2=subprocess.run(['qemu-img','snapshot','-d',old,d['path']],capture_output=True,text=True,timeout=30)
                        if p2.returncode != 0:
                            errors.append(f"{d.get('name')}: no se pudo eliminar '{old}': {(p2.stderr or p2.stdout).strip()}")
                    else:
                        errors.append(f"{d.get('name')}: no se pudo crear '{new}': {(p1.stderr or p1.stdout).strip()}")
                if created == 0:
                    raise RuntimeError("No se pudo renombrar el snapshot en ningún QCOW2.\n\n" + "\n".join(errors))
                if errors:
                    self._show_selectable_error('Cambio de nombre parcial', 'El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n' + "\n".join(errors))
            old_shot = self._snapshot_screenshot_path(old) if self.current_vm_dir else ""
            new_shot = self._snapshot_screenshot_path(new) if self.current_vm_dir else ""
            if old_shot and os.path.isfile(old_shot):
                try:
                    os.replace(old_shot, new_shot)
                except OSError:
                    pass
            self.refresh_snapshot_page()
        except Exception as e:
            self._show_selectable_error('Error al cambiar nombre', f'No se pudo cambiar el nombre.\n\n{e}')

