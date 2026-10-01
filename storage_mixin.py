# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: gestión de almacenamiento — discos (crear/redimensionar/
eliminar), CD/DVD, y orden de arranque.

Marcador storage_mixin_dedup_v1: en el archivo original había tres
métodos duplicados (_get_cdrom_path, configure_boot_order,
_save_boot_order) que Python resolvía descartando la primera definición
en silencio. Se eliminaron las primeras (legacy) y se conservan las
segundas, que son las que ya se ejecutaban: sin cambio de
comportamiento, sin duplicación.
"""
import os
import re
import json
import subprocess
import uuid
import configparser
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QFileDialog, QInputDialog, QListWidgetItem,
    QLineEdit, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QFormLayout,
)

import vm_config
import vm_paths  # portable_paths_v1
from vm_config import load_vm_config, save_vm_config
from dialogs import DiskCreationDialog
from workers import _qemu_safe_identifier


# ovf_ova_io_v1_macos_reserved
class StorageMixin:
    # ovf_ova_io_v1_macos_reserved: archivos internos del flujo macOS.
    # NUNCA deben aparecer en storage_devices ni en _storage_entries_with_types.
    #   - mac_hdd_ng.qcow2  -> disco del sistema (lo usa InstallWorker)
    #   - BaseSystem.img    -> medio de instalacion del Recovery
    #   - OpenCore.qcow2    -> imagen compartida de OSX-KVM
    _MACOS_RESERVED_FILENAMES = {
        "mac_hdd_ng.qcow2",
        "basesystem.img",
        "opencore.qcow2",
    }

    def _is_macos_reserved_file(self, name):
        """True si el nombre corresponde a un archivo reservado de macOS."""
        return os.path.basename(str(name or "")).lower() in self._MACOS_RESERVED_FILENAMES

    def _vm_is_macos(self, vm_dir=None):
        """True si la VM actual (o vm_dir) es macOS."""
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir:
            return False
        try:
            data = self._load_vm_config_cached(vm_dir)
            return str(data.get("os_type") or "").lower() == "macos"
        except Exception:
            return False

    def manage_disks(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Discos", "Selecciona una máquina virtual.")
            return
        vm_dir = self.current_vm_dir
        state = self._runtime_state(os.path.basename(vm_dir))
        disks = self._get_vm_disk_entries(vm_dir)
        lines = [f"{i}. {d['name']} — {d['format']} — {d['size']}" for i, d in enumerate(disks, 1)]
        text = "Discos de esta VM:\n\n" + ("\n".join(lines) if lines else "No hay discos registrados.")
        box = QMessageBox(self)
        box.setWindowTitle("💾 Administrador de discos")
        box.setText(text)
        create_btn = box.addButton("➕ Crear disco", QMessageBox.ButtonRole.AcceptRole)
        resize_btn = box.addButton("↔ Redimensionar", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == create_btn:
            if state != "stopped":
                QMessageBox.warning(self, "Discos", "Apaga la VM antes de crear discos nuevos.")
                return
            self.create_vm_disk()
        elif clicked == resize_btn:
            self.resize_vm_disk()

    def _get_vm_disk_entries(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        entries = []
        try:
            cfg = self._load_vm_config_cached(vm_dir)
            primary_ext = cfg.get("disk_ext", "qcow2")
        except Exception:
            primary_ext = "qcow2"
        candidates = []
        primary = os.path.join(vm_dir, f"vm_disk.{primary_ext}")
        if os.path.isfile(primary):
            candidates.append(primary)
        # ovf_ova_io_v1_macos_reserved: en macOS saltar los reservados.
        _skip_macos_dlg = self._vm_is_macos(vm_dir)
        for name in sorted(os.listdir(vm_dir)):
            if _skip_macos_dlg and self._is_macos_reserved_file(name):
                continue
            if name.startswith(("disk_", "sata_", "nvme_", "hd_", "floppy_")) and os.path.isfile(os.path.join(vm_dir, name)):
                candidates.append(os.path.join(vm_dir, name))
        for path in candidates:
            try:
                result = subprocess.run(["qemu-img", "info", "--output=json", path], capture_output=True, text=True, timeout=10, check=True)
                info = json.loads(result.stdout)
                virtual = info.get("virtual-size", 0)
                size = f"{virtual / 1024**3:.1f} GiB" if virtual else "?"
                fmt = info.get("format", os.path.splitext(path)[1].lstrip("."))
            except Exception:
                size = "?"
                fmt = os.path.splitext(path)[1].lstrip(".")
            entries.append({"name": os.path.basename(path), "path": path, "format": fmt, "size": size})
        return entries

    def _primary_disk_path(self, vm_dir=None):
        """Devuelve (abs_path, tipo) del disco principal de la VM.

        - macOS → mac_hdd_ng.qcow2 (modelo OSX-KVM, QCOW2 fijo).
        - Otros → primer disco SATA/NVMe registrado en
                  _storage_entries_with_types(vm_dir).
        - Fallback → vm_disk.{disk_ext} del vm_config.ini.

        Devuelve (None, None) si no encuentra nada. Es la base para el
        clon enlazado: sobre este archivo se crea el backing file QCOW2.
        Marcador linked_clone_v1.
        """
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return (None, None)

        try:
            data = self._load_vm_config_cached(vm_dir)
        except Exception:
            data = {}
        os_type = (data.get("os_type") or "").lower()

        if os_type == "macos":
            p = os.path.join(vm_dir, "mac_hdd_ng.qcow2")
            if os.path.isfile(p):
                return (os.path.abspath(p), "qcow2")
            return (None, None)

        try:
            entries = self._storage_entries_with_types(vm_dir)
        except Exception:
            entries = []
        for name, typ, path in entries:
            if typ in ("sata", "nvme") and os.path.isfile(path):
                return (os.path.abspath(path), typ)

        try:
            ext = data.get("disk_ext") or "qcow2"
        except Exception:
            ext = "qcow2"
        p = os.path.join(vm_dir, f"vm_disk.{ext}")
        if os.path.isfile(p):
            return (os.path.abspath(p), ext)
        return (None, None)


    def create_vm_disk(self):
        vm_dir = self.current_vm_dir
        if not vm_dir:
            QMessageBox.information(self, "Disco", "Primero selecciona una máquina virtual.")
            return

        # Una sola ventana para todos los datos del nuevo disco.
        dialog = DiskCreationDialog(self, "sata")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        self._create_virtual_disk_from_values(vm_dir, values, "sata")
        self.refresh_boot_order_choices()

    def _create_virtual_disk_from_values(self, vm_dir, values, devtype="sata"):
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", values["name"] or "datos")
        # Prefijo neutro para el archivo del disco. Coherente con la
        # interfaz: el usuario ve "Disco Duro", no "SATA".
        prefix = {"sata": "hd_", "nvme": "hd_", "floppy": "floppy_"}.get(devtype, "disk_")
        if not name.startswith(prefix):
            name = prefix + name
        size = values["size"]
        fmt = values["format"]
        disk_type = values["type"]
        if devtype == "floppy":
            fmt = "raw"
            size = size or "1.44M"
            disk_type = "fixed"
        ext = "img" if fmt == "raw" else fmt
        path = os.path.abspath(os.path.join(vm_dir, name + "." + ext))

        # Evitar dos registros físicos para el mismo dispositivo.
        try:
            for existing_name, existing_type, existing_path in self._storage_entries_with_types(vm_dir):
                if os.path.abspath(existing_path) == path or existing_name == os.path.basename(path):
                    QMessageBox.warning(self, "Dispositivo existente", f"Ese dispositivo ya está registrado:\n\n{existing_name}")
                    return
        except Exception:
            pass
        if os.path.exists(path):
            QMessageBox.warning(self, "Existe", f"Ya existe ese dispositivo:\n{os.path.basename(path)}")
            return

        cmd = ["qemu-img", "create", "-f", fmt]
        # Expandible = sin preasignación. Fijo = preasignación completa.
        if disk_type == "fixed":
            cmd += ["-o", "preallocation=full"]
        elif fmt == "qcow2":
            cmd += ["-o", "preallocation=off"]
        cmd += [path, size]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
            self.log_message(f"==> Dispositivo {devtype.upper()} creado: {os.path.basename(path)} ({size}, {disk_type}, {fmt.upper()})")
            self._register_storage_device(os.path.basename(path), path, devtype)
            # Crear un dispositivo de almacenamiento siempre actualiza también el orden de arranque.
            self.refresh_boot_order_choices()
            QMessageBox.information(
                self, "Dispositivo creado",
                f"Se creó correctamente:\n\n{os.path.basename(path)}\n\n"
                f"Tamaño virtual: {size}\nTipo: {'Fijo' if disk_type == 'fixed' else 'Expandible'}\nFormato: {fmt.upper()}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Crear dispositivo", f"No se pudo crear el dispositivo.\n\n{e}")

    def resize_vm_disk(self):
        disks = self._get_vm_disk_entries()
        if not disks:
            QMessageBox.information(self, "Discos", "No hay discos para redimensionar.")
            return
        names = [d["name"] for d in disks]
        name, ok = QInputDialog.getItem(self, "Redimensionar disco", "Selecciona el disco:", names, 0, False)
        if not ok:
            return
        disk = next(d["path"] for d in disks if d["name"] == name)
        new_size, ok = QInputDialog.getText(self, "Redimensionar disco", "Nuevo tamaño (ej. 120G, 200G, 1T):", QLineEdit.EchoMode.Normal, "")
        if not ok or not new_size.strip():
            return
        try:
            subprocess.run(["qemu-img", "resize", disk, new_size.strip()], check=True, capture_output=True, text=True, timeout=30)
            QMessageBox.information(self, "Disco", "Disco redimensionado correctamente.\n\nSi aumentaste el disco, amplía también la partición/volumen dentro del sistema invitado.")
        except Exception as e:
            QMessageBox.critical(self, "Redimensionar", f"No se pudo redimensionar el disco.\n\n{e}")


    # ------------------------------------------------------------------
    # Compactar disco QCOW2 (marcador compact_full_v5)
    # ------------------------------------------------------------------
    # qemu-img convert -c -O qcow2 reescribe el archivo eliminando bloques
    # no usados. No cambia el tamaño virtual del disco: solo reduce el
    # archivo físico en el host. Requiere VM apagada y ~1.1× el tamaño
    # actual libre en el mismo sistema de archivos.

    def compact_vm_disk(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Compactar disco",
                                    "Selecciona una máquina virtual.")
            return

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)
        state = self._runtime_state(vm_name)
        if state != "stopped":
            QMessageBox.warning(
                self, "Compactar disco",
                f"La VM '{vm_name}' está encendida.\n\n"
                "Apágala antes de compactar sus discos QCOW2: con QEMU "
                "activo el archivo está bloqueado y puede haber cambios "
                "sin sincronizar a disco.",
            )
            return

        qcow2_disks = [d for d in self._get_vm_disk_entries()
                       if str(d.get("format", "")).lower() == "qcow2"]
        if not qcow2_disks:
            QMessageBox.information(
                self, "Compactar disco",
                "No hay discos QCOW2 en esta VM. La compactación solo "
                "aplica a QCOW2 (no a RAW, VDI, VMDK).",
            )
            return

        if len(qcow2_disks) == 1:
            disk = qcow2_disks[0]
        else:
            labels = [f"{d['name']}  ({d['size']})" for d in qcow2_disks]
            label, ok = QInputDialog.getItem(
                self, "Compactar disco",
                "Selecciona el disco QCOW2 a compactar:",
                labels, 0, False,
            )
            if not ok:
                return
            disk = qcow2_disks[labels.index(label)]

        disk_path = disk["path"]
        name = disk["name"]

        _box = QMessageBox(self)
        _box.setWindowTitle("Confirmar compactado")
        _box.setIcon(QMessageBox.Icon.Warning)
        _box.setTextFormat(Qt.TextFormat.RichText)
        _box.setText(
            f"¿Está seguro de querer proceder con el compactado del medio "
            f"<b>'{name}'</b>?<br><br>"
            "<b>⚠ Recomendación:</b> haz un <b>backup del disco antes de "
            "proceder</b>. El compactado reescribe el archivo por completo "
            "(en un archivo temporal y luego reemplaza el original). Si el "
            "proceso se interrumpe o el host se queda sin espacio, el disco "
            "original podría quedar dañado.<br><br>"
            "<b>Qué hace:</b><br>"
            "&nbsp;&nbsp;• Reescribe el archivo QCOW2 eliminando bloques no usados.<br>"
            "&nbsp;&nbsp;• Reduce el tamaño del archivo en el host.<br>"
            "&nbsp;&nbsp;• <b>NO</b> cambia el tamaño virtual que ve la VM.<br>"
            "&nbsp;&nbsp;• Necesita ~1.1× el tamaño actual libre en el host."
        )
        _box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        _box.setDefaultButton(QMessageBox.StandardButton.No)
        if _box.exec() != QMessageBox.StandardButton.Yes:
            return

        tmp_path = disk_path + ".compact.qcow2"
        orig_size = 0
        try:
            orig_size = os.path.getsize(disk_path)
        except OSError:
            pass

        def _work(log_emit, is_cancelled, progress_emit):
            import subprocess as _sp
            log_emit(f"==> Compactando '{name}'…")
            log_emit(f"    Origen:   {disk_path}")
            log_emit(f"    Temporal: {tmp_path}")

            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            try:
                proc = _sp.Popen(
                    ["qemu-img", "convert", "-c", "-O", "qcow2", "-p",
                     disk_path, tmp_path],
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
                        raise RuntimeError("Compactado cancelado por el usuario.")
                    if not line:
                        continue
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                    if m:
                        pct = int(float(m.group(1)))
                        if pct != last_pct:
                            last_pct = pct
                            progress_emit(pct, f"Compactando '{name}'… {pct}%")
                    else:
                        progress_emit(-1, f"Compactando '{name}'…")

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

            # Verificación: el temporal debe ser un QCOW2 válido.
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
            except Exception as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                raise RuntimeError(f"No se pudo verificar el temporal: {e}")

            # Rename atómico (mismo directorio → mismo FS).
            try:
                os.replace(tmp_path, disk_path)
            except OSError as e:
                raise RuntimeError(
                    f"No se pudo reemplazar el disco original: {e}\n"
                    f"El compactado quedó en: {tmp_path}"
                )

            try:
                new_size = os.path.getsize(disk_path)
            except OSError:
                new_size = 0
            savings = max(0, orig_size - new_size)
            log_emit(
                f"==> Compactado terminado: {orig_size} → {new_size} bytes "
                f"(ahorro: {savings} bytes)."
            )
            return {
                "name": name,
                "orig": orig_size,
                "new": new_size,
                "savings": savings,
            }

        def _on_success(result):
            if not result:
                return
            try:
                fmt_orig = self._format_bytes_iexport(result["orig"])
                fmt_new = self._format_bytes_iexport(result["new"])
                fmt_sav = self._format_bytes_iexport(result["savings"])
            except Exception:
                fmt_orig = str(result["orig"])
                fmt_new = str(result["new"])
                fmt_sav = str(result["savings"])
            QMessageBox.information(
                self, "Disco compactado",
                f"'{result['name']}' compactado correctamente.\n\n"
                f"Antes: {fmt_orig}\n"
                f"Después: {fmt_new}\n"
                f"Ahorro: {fmt_sav}",
            )
            if hasattr(self, "_update_manager_details"):
                try:
                    self._update_manager_details()
                except Exception:
                    pass
            # Refrescar el árbol para que la columna "Tamaño" muestre el
            # nuevo espacio ocupado.
            if hasattr(self, "refresh_storage_ui"):
                try:
                    self.refresh_storage_ui()
                except Exception:
                    pass

        def _on_error(e):
            QMessageBox.critical(
                self, "Compactar disco",
                f"No se pudo compactar el disco.\n\n{e}",
            )

        self.run_async(
            _work,
            f"Compactando '{name}'",
            on_success=_on_success,
            on_error=_on_error,
            cancelable=True,
            show_log=True,
            subtitle="Reescribiendo el archivo QCOW2 sin bloques no usados…",
        )


    def _update_storage_buttons_state(self):
        """Habilita Modificar / Compactar / Eliminar según el ítem del árbol.

        Reglas (marcador storage_v6):
          • Grupo del árbol (sin UserRole) → los tres deshabilitados.
          • Disco SATA/NVMe → Modificar y Eliminar activos. Compactar solo
            si el disco está en formato QCOW2.
          • Floppy → Modificar y Eliminar activos. Compactar NO.
          • CD/DVD → Modificar y Eliminar activos. Compactar NO.

        Se llama desde el slot itemSelectionChanged de storage_tree y
        también al final de refresh_storage_ui (rebuild → sin selección).
        """
        tree = getattr(self, "storage_tree", None)
        if tree is None:
            return
        item = tree.currentItem()
        meta = None
        if item is not None:
            try:
                meta = item.data(0, Qt.ItemDataRole.UserRole)
            except Exception:
                meta = None
        is_device = isinstance(meta, dict) and bool(meta.get("kind"))
        kind = (meta or {}).get("kind") if is_device else None

        # ¿Es un disco QCOW2? Solo esos se pueden compactar.
        is_qcow2 = False
        if is_device and kind == "disk":
            path = meta.get("path") or ""
            dev = meta.get("device") or "sata"
            if dev in ("sata", "nvme") and path and os.path.isfile(path):
                try:
                    r = subprocess.run(
                        ["qemu-img", "info", "--output=json", path],
                        capture_output=True, text=True, timeout=5, check=True,
                    )
                    fmt = (json.loads(r.stdout).get("format") or "").lower()
                    is_qcow2 = (fmt == "qcow2")
                except Exception:
                    is_qcow2 = path.lower().endswith(".qcow2")

        # expand_only_v1: el boton Modificar cambia de etiqueta segun
        # el dispositivo y solo permite acciones coherentes.
        #   • CD/DVD  -> "✏ Modificar" (cambiar medio)
        #   • Disco   -> "↗ Expandir"   (cambiar tamano, sin nombre/path)
        #   • Floppy  -> deshabilitado  (no se redimensiona)
        modify_btn = getattr(self, "btn_storage_modify_device", None)
        if modify_btn is not None:
            try:
                if not is_device:
                    modify_btn.setText("✏ Modificar")
                    modify_btn.setEnabled(False)
                    modify_btn.setToolTip("")
                elif kind == "cdrom":
                    modify_btn.setText("✏ Modificar")
                    modify_btn.setEnabled(True)
                    modify_btn.setToolTip(
                        "Cambiar el medio de esta unidad CD/DVD."
                    )
                elif kind == "disk":
                    dev = (meta or {}).get("device") or "sata"
                    if dev == "floppy":
                        modify_btn.setText("✏ Modificar")
                        modify_btn.setEnabled(False)
                        modify_btn.setToolTip(
                            "Los disquetes no se pueden redimensionar.\n"
                            "Elimina este y crea otro si necesitas otro tamaño."
                        )
                    else:
                        modify_btn.setText("↗ Expandir")
                        modify_btn.setEnabled(True)
                        modify_btn.setToolTip(
                            "Aumentar el tamaño virtual de este disco.\n"
                            "El disco solo puede CRECER."
                        )
                else:
                    modify_btn.setText("✏ Modificar")
                    modify_btn.setEnabled(False)
            except Exception:
                pass

        # Eliminar: cualquier dispositivo concreto.
        del_btn = getattr(self, "btn_storage_delete_device", None)
        if del_btn is not None:
            try:
                del_btn.setEnabled(is_device)
            except Exception:
                pass

        # Compactar: solo discos QCOW2.
        btn_compact = getattr(self, "btn_storage_disk_manager", None)
        if btn_compact is not None:
            try:
                btn_compact.setEnabled(is_device and is_qcow2)
            except Exception:
                pass
            try:
                if is_device and kind == "cdrom":
                    btn_compact.setToolTip(
                        "Las unidades CD/DVD no se compactan.\n"
                        "Solo aplica a discos duros en formato QCOW2."
                    )
                elif is_device and kind == "disk" and not is_qcow2:
                    btn_compact.setToolTip(
                        "El disco seleccionado no está en formato QCOW2.\n"
                        "La compactación solo aplica a discos QCOW2."
                    )
                else:
                    btn_compact.setToolTip(
                        "Compacta un disco QCOW2 de la VM seleccionada.\n"
                        "\n"
                        "Reduce el archivo físico en el host eliminando bloques\n"
                        "no usados (equivalente a 'qemu-img convert -c'). NO\n"
                        "cambia el tamaño virtual que ve el sistema invitado.\n"
                        "\n"
                        "Se pedirá confirmación y se recomienda hacer un backup\n"
                        "antes de proceder. Requiere que la VM esté apagada."
                    )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Re-escaneo automatico de la biblioteca de medios
    # ------------------------------------------------------------------
    # Marcador: media_library_vm_scan_autotrigger_v1.
    #
    # Cuando el usuario cambia almacenamiento de una VM (crear / eliminar /
    # modificar un disco, cambiar el medio de un CD/DVD), se vuelve a
    # escanear VirtualMachines/ para mantener el indice de la Biblioteca
    # de Medios al dia.

    def _scan_media_vms_after_storage_change(self):
        """Re-escanea las VMs tras un cambio de almacenamiento."""
        try:
            import media_library as _ml
        except Exception:
            return
        try:
            lib = _ml.MediaLibrary()
            res = lib.scan_vms()
        except Exception as e:
            try:
                self.log_message(
                    f"[AVISO] No se pudo re-escanear la biblioteca de "
                    f"medios: {e}"
                )
            except Exception:
                pass
            return
        try:
            nuevas = int(res.get("nuevas") or 0)
            actualizadas = int(res.get("actualizadas") or 0)
            huerfanas = len(res.get("huerfanas_de_vm") or [])
            if nuevas or actualizadas or huerfanas:
                self.log_message(
                    f"==> Biblioteca de Medios: {nuevas} nueva(s), "
                    f"{actualizadas} actualizada(s), {huerfanas} "
                    f"huerfana(s) de VM."
                )
        except Exception:
            pass
        try:
            if hasattr(self, "refresh_media_library_table"):
                self.refresh_media_library_table()
        except Exception:
            pass

    def refresh_boot_order_choices(self):
        # El orden de arranque se administra exclusivamente desde Almacenamiento.
        # Ya no existe un control separado/redundante en la configuración.
        if hasattr(self, "storage_list"):
            self.refresh_storage_ui()

    def _storage_devices_all(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        try:
            data = self._load_vm_config_cached(vm_dir)
            extra = data.get("extra") or {}
            devices = extra.get("storage_devices", [])
            devices = devices if isinstance(devices, list) else []
        except Exception:
            data, extra, devices = {}, {}, []

        # portable_paths_v1: resolver paths guardados (relativos) a absolutos
        # para que os.path.isfile() y los consumidores los usen directamente.
        # La escritura los vuelve a relativizar en _write_storage_devices.
        try:
            devices = vm_paths.resolve_storage_devices(vm_dir, devices)
        except Exception:
            pass

        changed = False
        # Migra dispositivos sin ID y normaliza IDs antiguos para que QEMU los acepte.
        for d in devices:
            current_id = str(d.get("id") or "")
            normalized_id = _qemu_safe_identifier(current_id, "dev") if current_id else "dev_" + uuid.uuid4().hex[:12]
            if current_id != normalized_id:
                d["id"] = normalized_id
                changed = True

        # Descubre discos que ya existen en la carpeta de la VM pero no quedaron registrados
        # en storage_devices. Esto corrige VMs creadas con versiones anteriores y mantiene
        # el árbol de almacenamiento consistente con Información.
        # portable_paths_v1_prune: descartar entradas huérfanas antes del
        # auto-descubrimiento. Un disco registrado cuyo archivo ya no existe
        # en el host (típico tras mover la VM sin actualizar el .ini, o tras
        # una entrada heredada apuntando a otro sitio) provocaría que el
        # auto-descubrimiento añada una SEGUNDA entrada para el mismo archivo
        # real: la VM termina con dos "hd_mint.qcow2" en el árbol, uno sin
        # tamaño. No se tocan los CD/DVD vacíos (path="" sin source) ni los
        # placeholders de descarga (source="installer"/"recovery").
        pruned = []
        for d in devices:
            if not isinstance(d, dict):
                pruned.append(d)
                continue
            p = str(d.get("path") or "")
            if p and not os.path.exists(p) and not d.get("source"):
                try:
                    self.log_message(
                        f"[AVISO] storage_devices: se descarta entrada huérfana "
                        f"'{d.get('name','?')}' (path inexistente: {p})."
                    )
                except Exception:
                    pass
                changed = True
                continue
            pruned.append(d)
        devices = pruned

        registered_paths={os.path.abspath(d.get("path","")) for d in devices if d.get("path")}
        # ovf_ova_io_v1_macos_reserved: en macOS, no auto-descubrir los
        # archivos internos (mac_hdd_ng.qcow2, BaseSystem.img, OpenCore.qcow2).
        # Los gestiona exclusivamente el flujo macOS (workers.py), y
        # meterlos en storage_devices duplica entradas y rompe el arranque.
        _skip_autodetect = self._vm_is_macos(vm_dir)
        try:
            for name in sorted(os.listdir(vm_dir)):
                path=os.path.join(vm_dir, name)
                if not os.path.isfile(path) or os.path.abspath(path) in registered_paths:
                    continue
                if _skip_autodetect and self._is_macos_reserved_file(name):
                    continue
                low=name.lower()
                if not low.endswith((".qcow2", ".qcow", ".img", ".raw", ".vdi", ".vmdk", ".vhd", ".vhdx")):
                    continue
                if low.startswith("nvme_"):
                    typ="nvme"
                elif low.startswith("floppy_"):
                    typ="floppy"
                else:
                    # "hd_", "sata_", "disk_" y cualquier otro → sata
                    typ="sata"
                devices.append({"id":"dev_" + uuid.uuid4().hex[:12], "name":name, "path":os.path.abspath(path), "device":typ})
                registered_paths.add(os.path.abspath(path))
                changed=True
        except Exception:
            pass

        # Migra una configuración antigua con cdrom_path a una unidad óptica real.
        legacy_cd = extra.get("cdrom_path", "")
        if legacy_cd and not any(d.get("device") == "cdrom" for d in devices):
            devices.append({"id":"dev_" + uuid.uuid4().hex[:12], "name":"CD/DVD 1", "path":os.path.abspath(legacy_cd), "device":"cdrom"})
            changed=True

        if changed and vm_dir == self.current_vm_dir:
            self._write_storage_devices(devices)
        return devices

    def _write_storage_devices(self, devices):
        if not self.current_vm_dir:
            return
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        cfg = configparser.ConfigParser(interpolation=None); cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("extra"):
            cfg.add_section("extra")
        try:
            extra = json.loads(cfg["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        # portable_paths_v1: guardar paths relativos si están dentro
        # de la carpeta de la VM (portabilidad de VirtualMachines/).
        try:
            devices = vm_paths.normalize_storage_devices(self.current_vm_dir, devices)
        except Exception:
            pass
        extra["storage_devices"] = devices
        # Nueva estructura: ya no dependemos de un único cdrom_path.
        extra["cdrom_path"] = ""
        cfg.set("extra", "data", json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f: cfg.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(self.current_vm_dir)

    def _current_boot_order_tokens(self):
        if not self.current_vm_dir or not os.path.isdir(self.current_vm_dir):
            return ["network"]
        try:
            data = self._load_vm_config_cached(self.current_vm_dir)
            saved = data.get("boot_order") or []
        except Exception:
            saved = []
        devices = self._storage_devices_all(self.current_vm_dir)
        disk_tokens = []
        cd_tokens = []
        for d in devices:
            ident = d.get("id")
            typ = d.get("device")
            path = d.get("path") or ""
            if typ in ("sata", "nvme", "floppy") and ident and path:
                if typ == "floppy" or os.path.isfile(path):
                    disk_tokens.append(f"disk:{ident}")
            elif typ == "cdrom" and ident:
                # Una unidad óptica existe aunque esté vacía; puede quedar en el orden
                # de arranque y recibir un medio más tarde.
                cd_tokens.append(f"cdrom:{ident}")
        # Los dispositivos NUEVOS (sin token previo guardado) se anteponen como
        # CD/DVD antes que discos: en una VM recién creada, el CD/DVD de
        # instalación debe quedar primero en el orden de arranque.
        available = cd_tokens + disk_tokens + ["network"]

        # Migra tokens genéricos de versiones antiguas a los dispositivos reales.
        legacy_disk = disk_tokens[0] if disk_tokens else None
        legacy_cd = cd_tokens[0] if cd_tokens else None
        normalized = []
        for t in saved:
            if t == "cdrom":
                if legacy_cd and legacy_cd not in normalized:
                    normalized.append(legacy_cd)
            elif t == "disk":
                if legacy_disk and legacy_disk not in normalized:
                    normalized.append(legacy_disk)
            elif t in available and t not in normalized:
                normalized.append(t)

        # Conserva el orden guardado y agrega al final cualquier dispositivo nuevo.
        order = [t for t in normalized if t in available]
        order += [t for t in available if t not in order]
        # Siempre debe existir Red/PXE como último recurso.
        if "network" not in order:
            order.append("network")

        # Persiste la versión canónica cuando ha cambiado. Esto evita que el orden
        # quede solo en la memoria de la interfaz y se pierda al reiniciar el programa.
        if order != saved and getattr(self, "current_vm_dir", None):
            try:
                self._save_boot_order(order)
            except Exception:
                pass
        return order

    def _boot_token_label(self, token):
        if token == "network": return "Red/PXE"
        if token == "cdrom": return "CD/DVD"
        if token.startswith("cdrom:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident), None)
            if dev:
                source = str(dev.get("source") or "")
                path=dev.get("path") or ""
                if source == "installer":
                    media = "🌐 descargar instalador al iniciar"
                elif source == "recovery":
                    media = "🌐 descargar System Recovery al iniciar"
                else:
                    media = os.path.basename(path) if path else "vacío"
                return f"CD/DVD — {dev.get('name') or 'CD/DVD'} — {media}"
            return "CD/DVD"
        if token == "disk": return "Disco principal"
        if token.startswith("disk:"):
            ident=token.split(":",1)[1]
            dev=next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident or os.path.basename(d.get("path",""))==ident), None)
            name=(dev.get("name") if dev else ident) or ident
            low=name.lower()
            typ=dev.get("device") if dev else "sata"
            if typ == "nvme":
                return "NVMe — " + name
            if typ == "floppy":
                return "Floppy — " + name
            return "SATA — " + name
        return token

    def _storage_entries_with_types(self, vm_dir=None):
        vm_dir = vm_dir or self.current_vm_dir
        if not vm_dir or not os.path.isdir(vm_dir):
            return []
        result = []
        seen = set()
        try:
            cfg = self._load_vm_config_cached(vm_dir)
            devices = (cfg.get("extra") or {}).get("storage_devices", [])
        except Exception:
            devices = []
        for d in devices if isinstance(devices, list) else []:
            # portable_paths_v1: resolver path relativo contra vm_dir.
            path = vm_paths.to_absolute(vm_dir, d.get("path", ""))
            if not path or not os.path.isfile(path) or d.get("device") == "cdrom":
                continue
            typ = d.get("device", "sata")
            name = d.get("name") or os.path.basename(path)
            result.append((name, typ, path)); seen.add(os.path.abspath(path))
        # Compatibilidad con discos creados por versiones anteriores.
        # ovf_ova_io_v1_macos_reserved: en macOS, saltar archivos internos.
        _skip_macos = self._vm_is_macos(vm_dir)
        for name in sorted(os.listdir(vm_dir)):
            low = name.lower(); path = os.path.join(vm_dir, name)
            if not os.path.isfile(path) or os.path.abspath(path) in seen:
                continue
            if _skip_macos and self._is_macos_reserved_file(name):
                continue
            if low.startswith(("disk_", "sata_", "nvme_", "hd_", "floppy_", "vm_disk.")):
                if low.startswith("nvme_"): typ = "nvme"
                elif low.startswith("floppy_"): typ = "floppy"
                else: typ = "sata"
                result.append((name, typ, path))
        return result
    @staticmethod
    def _parse_size_to_bytes(s):
        """Convierte '80G', '1.5T', '512M' a bytes. None si no encaja."""
        if not s:
            return None
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([KMGTP]?)B?",
                         s.strip(), re.IGNORECASE)
        if not m:
            return None
        try:
            n = float(m.group(1))
        except ValueError:
            return None
        unit = (m.group(2) or "").upper()
        mult = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3,
                "T": 1024 ** 4, "P": 1024 ** 5}
        return int(n * mult.get(unit, 1))

    def _device_size_label(self, device):
        """Devuelve el tamaño legible de un dispositivo para la 3ª columna
        del árbol de almacenamiento ("Tamaño").

        Para discos SATA/NVMe: tamaño virtual + espacio real ocupado.
        Para CD/DVD: tamaño del archivo o un indicador de descarga/vacío.
        Para floppies: tamaño del archivo.
        """
        typ = device.get("device", "sata")
        path = device.get("path", "") or ""
        source = str(device.get("source") or "")

        if typ == "cdrom":
            if source in ("installer", "recovery"):
                return "\U0001f310 descarga"
            if not path or not os.path.isfile(path):
                return "vacío"
            try:
                return self._format_bytes_iexport(os.path.getsize(path))
            except Exception:
                return "—"

        if not path or not os.path.isfile(path):
            return "—"

        if typ == "floppy":
            try:
                return self._format_bytes_iexport(os.path.getsize(path))
            except Exception:
                return "—"

        # Discos SATA/NVMe: tamaño virtual + espacio ocupado en el host.
        try:
            r = subprocess.run(
                ["qemu-img", "info", "--output=json", path],
                capture_output=True, text=True, timeout=8, check=True,
            )
            info = json.loads(r.stdout)
            virt = int(info.get("virtual-size", 0) or 0)
            actual = int(info.get("actual-size", 0) or 0)
            if virt and actual:
                return (f"{self._format_bytes_iexport(virt)} "
                        f"(ocupa {self._format_bytes_iexport(actual)})")
            if virt:
                return self._format_bytes_iexport(virt)
        except Exception:
            pass
        return "—"


    def refresh_storage_ui(self):
        if hasattr(self, "storage_tree"):
            self.storage_tree.clear()
            # UI simplificada: SATA y NVMe comparten un solo grupo
            # visual ("Disco Duro"). El bus real lo decide workers.py
            # según el SO invitado.
            groups = {
                "sata": QTreeWidgetItem(["💽 Disco Duro", "Disco"]),
                "nvme": None,  # se muestra dentro del grupo "sata"
                "floppy": QTreeWidgetItem(["💾 Disquetera", "FDC"]),
                "cdrom": QTreeWidgetItem(["📀 Unidades ópticas", "CD/DVD"]),
            }
            for d in self._storage_devices_all(self.current_vm_dir):
                typ=d.get("device","sata"); name=d.get("name") or os.path.basename(d.get("path","")) or typ.upper()
                path=d.get("path","")
                if typ == "cdrom":
                    source = str(d.get("source") or "")
                    if source == "installer":
                        media_label = "🌐 Descargar instalador de Internet al iniciar"
                        detail_label = "🌐 Instalador por Internet (se descargará al iniciar)"
                    elif source == "recovery":
                        media_label = "🌐 Descargar System Recovery al iniciar"
                        detail_label = "🌐 System Recovery (se descargará al iniciar)"
                    else:
                        media_label = os.path.basename(path) if path else "vacío"
                        detail_label = path or "Sin medio"
                    label=f"{name} — {media_label}"
                    size_col = self._device_size_label(d)
                    item=QTreeWidgetItem([label, detail_label, size_col])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"kind":"cdrom","id":d.get("id"),"path":path,"source":source})
                    groups["cdrom"].addChild(item)
                elif typ in groups or typ == "nvme":
                    group_key = "sata" if typ == "nvme" else typ
                    size_col = self._device_size_label(d)
                    item=QTreeWidgetItem([name, path, size_col])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"kind":"disk","id":d.get("id"),"path":path,"device":typ})
                    groups[group_key].addChild(item)
            for key in ("sata","nvme","floppy","cdrom"):
                root=groups.get(key)
                # Algunos grupos pueden ser None tras fusiones
                # (por ejemplo, "nvme" se muestra bajo "sata").
                if root is None:
                    continue
                if root.childCount() or key=="cdrom":
                    self.storage_tree.addTopLevelItem(root); root.setExpanded(True)

        if not hasattr(self, "storage_list"):
            return
        self.storage_list.blockSignals(True); self.storage_list.clear()
        for token in self._current_boot_order_tokens():
            item=QListWidgetItem(self._boot_token_label(token)); item.setData(Qt.ItemDataRole.UserRole, token); self.storage_list.addItem(item)
        if self.storage_list.count(): self.storage_list.setCurrentRow(0)
        self.storage_list.blockSignals(False)
        # Tras reconstruir el árbol no hay selección: resetear botones.
        if hasattr(self, "_update_storage_buttons_state"):
            try:
                self._update_storage_buttons_state()
            except Exception:
                pass

    def _boot_order_from_list(self):
        if not getattr(self, "current_vm_dir", None) or not hasattr(self, "storage_list"):
            return
        order = [self.storage_list.item(k).data(Qt.ItemDataRole.UserRole) for k in range(self.storage_list.count())]
        self._save_boot_order(order)


    def move_storage_boot(self, delta):
        if not hasattr(self, "storage_list") or not self.current_vm_dir:
            return
        i = self.storage_list.currentRow(); j = i + delta
        if i < 0 or j < 0 or j >= self.storage_list.count():
            return
        item = self.storage_list.takeItem(i)
        self.storage_list.insertItem(j, item)
        self.storage_list.setCurrentRow(j)
        self._boot_order_from_list()

    def remove_storage_device(self):
        if not hasattr(self, "storage_list"): return
        item=self.storage_list.currentItem()
        if not item: return
        token=item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(self,"Almacenamiento","Para quitar un dispositivo usa el botón 🗑 Eliminar del árbol de Almacenamiento. El orden de arranque solo controla prioridad.")

    def delete_storage_device(self):
        if not self.current_vm_dir or not hasattr(self, "storage_tree"):
            QMessageBox.information(self, "Almacenamiento", "Selecciona una máquina virtual y un dispositivo."); return
        item=self.storage_tree.currentItem(); meta=item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(meta, dict) or not meta.get("kind"):
            QMessageBox.information(self,"Almacenamiento","Selecciona un dispositivo concreto, no el controlador."); return
        devices=self._storage_devices_all(self.current_vm_dir)
        dev=next((d for d in devices if d.get("id")==meta.get("id")),None)
        if not dev:
            QMessageBox.warning(self,"Almacenamiento","No se encontró el dispositivo seleccionado."); return
        typ=dev.get("device")
        path=os.path.abspath(dev.get("path")) if dev.get("path") else ""
        if typ == "cdrom":
            msg=f"¿Quitar la unidad {dev.get('name','CD/DVD')} de la VM?\n\nEl medio no se eliminará del host."
            if QMessageBox.question(self,"Eliminar CD/DVD",msg,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes: return
            devices=[d for d in devices if d.get("id")!=dev.get("id")]
            self._write_storage_devices(devices)
        else:
            if not path or not os.path.isfile(path):
                QMessageBox.warning(self,"Dispositivo","El archivo seleccionado ya no existe en el host."); return
            box=QMessageBox(self); box.setWindowTitle("Eliminar dispositivo"); box.setText(f"¿Qué deseas hacer con '{os.path.basename(path)}'?")
            box.addButton("Quitar de la VM",QMessageBox.ButtonRole.AcceptRole); delb=box.addButton("Eliminar también el archivo",QMessageBox.ButtonRole.DestructiveRole); cancel=box.addButton("Cancelar",QMessageBox.ButtonRole.RejectRole); box.exec()
            if box.clickedButton()==cancel: return
            devices=[d for d in devices if d.get("id")!=dev.get("id")]; self._write_storage_devices(devices)
            if box.clickedButton()==delb: os.remove(path)
        # elimina el token correspondiente del orden guardado y vuelve a sincronizar ambos paneles
        old=[t for t in self._current_boot_order_tokens() if t != (f"cdrom:{dev.get('id')}" if typ=="cdrom" else f"disk:{dev.get('id')}" )]
        self._save_boot_order(old)
        self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
        try:
            self._scan_media_vms_after_storage_change()
        except Exception:
            pass

    def _unregister_storage_path(self, path):
        devices=self._storage_devices_all(self.current_vm_dir)
        devices=[d for d in devices if os.path.abspath(d.get("path","")) != os.path.abspath(path)]
        self._write_storage_devices(devices)

    def _ensure_storage_target_vm(self):
        """Crea/guarda una VM provisional cuando el usuario está en Nueva VM y quiere añadir almacenamiento."""
        if self._vm_is_selected():
            return True
        name = self.input_vm_name.text().strip() if hasattr(self, "input_vm_name") else ""
        if not name:
            name, ok = QInputDialog.getText(self, "Nueva máquina virtual", "Nombre de la máquina virtual:")
            if not ok or not name.strip():
                return False
            name = name.strip()
            self.input_vm_name.setText(name)
        safe = vm_config.vm_folder_name(name)
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, safe)
        if os.path.exists(vm_dir):
            QMessageBox.warning(self, "Nueva máquina virtual", f"Ya existe una máquina virtual con ese nombre:\n\n{safe}\n\nSelecciona esa VM o elige otro nombre.")
            return False
        try:
            os.makedirs(vm_dir, exist_ok=False)
            os_type = self.combo_main_os.currentData() if hasattr(self, "combo_main_os") else "linux"
            ram = f"{self.slider_ram.value()}G" if hasattr(self, "slider_ram") else "4G"
            cores = self.slider_cores.value() if hasattr(self, "slider_cores") else 2
            firmware = self.combo_firmware.currentData() if hasattr(self, "combo_firmware") else "bios"
            secure = self.check_secure_boot.isChecked() if hasattr(self, "check_secure_boot") else False
            tpm = self.check_tpm.isChecked() if hasattr(self, "check_tpm") else False
            save_vm_config(
                vm_dir, name, os_type, ram, cores, "40G", "dynamic", "qcow2", "qcow2", {"cpu_model": self.combo_cpu_model.currentData() if hasattr(self, "combo_cpu_model") else "auto"},
                firmware=firmware, secure_boot=secure, tpm=tpm, boot_device="cdrom",
                network_model=(self.combo_network.currentData() if hasattr(self, "combo_network") else "virtio-net-pci"),
                audio_device=(self.combo_audio.currentData() if hasattr(self, "combo_audio") else "intel-hda"),
                network_mode=(self.combo_network_mode.currentData() if hasattr(self, "combo_network_mode") else "nat"),
                network_interface="", network_count=1,
                graphics_mode=(self.combo_graphics.currentData() if hasattr(self, "combo_graphics") else "auto"),
                graphics_vram=(self.combo_graphics_vram.currentData() if hasattr(self, "combo_graphics_vram") else "256M"),
                boot_order=["cdrom", "disk", "network"],
                network_devices=(self._network_devices() if hasattr(self, "_network_devices") else []),
                passthrough_devices=getattr(self, "_passthrough_saved", []),
                chipset=(self.combo_chipset.currentData() if hasattr(self, "combo_chipset") else "pc"),
            )
            self.current_vm_dir = vm_dir
            self._set_vm_status("saved")
            self.refresh_vm_list()
            self.refresh_storage_ui()
            self._update_manager_details()
            self.log_message(f"==> VM creada provisionalmente para administrar almacenamiento: {name}")
            return True
        except Exception as e:
            try:
                if os.path.isdir(vm_dir) and not os.listdir(vm_dir):
                    os.rmdir(vm_dir)
            except Exception:
                pass
            QMessageBox.critical(self, "Nueva máquina virtual", f"No se pudo preparar la máquina virtual.\n\n{e}")
            return False

    def create_storage_device(self, devtype):
        if not self._ensure_storage_target_vm():
            return
        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        if state != "stopped":
            QMessageBox.warning(self, "Almacenamiento", "Apaga la VM antes de modificar sus dispositivos de almacenamiento.")
            return

        os_type = self.combo_main_os.currentData() if hasattr(self, "combo_main_os") else "linux"
        os_version = ""
        distro = ""
        win_ver = "Windows 11"
        try:
            if os_type == "macos":
                os_version = self.os_options[self.combo_macos_ver.currentIndex()][0]
            elif os_type == "windows":
                win_ver = self.combo_win_ver.currentText()
            else:
                distro = self.combo_lin_distro.currentText()
        except Exception:
            pass

        dialog = DiskCreationDialog(self, devtype, os_type, os_version, distro, win_ver)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()

        if devtype == "cdrom":
            mode = values.get("cd_mode", "empty")
            try:
                path = ""
                if mode == "existing":
                    path = values.get("path", "")
                elif mode == "installer":
                    # Igual que macOS Recovery: no descargamos al crear la unidad.
                    # Se marca el medio y la descarga comenzará al pulsar Iniciar.
                    path = ""
                elif mode == "recovery":
                    # El Recovery se descarga al iniciar la VM, no al crear la unidad óptica.
                    path = ""
                source = mode if mode in ("installer", "recovery") else ""
                ident = self._register_cdrom_device(values.get("name") or "CD/DVD", path, source=source)
                self.log_message(f"==> Unidad CD/DVD creada: {values.get('name') or 'CD/DVD'}")
                self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
                try:
                    self._scan_media_vms_after_storage_change()
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "CD/DVD", f"No se pudo configurar la unidad óptica.\n\n{e}")
                return
            return

        if values.get("existing"):
            self._attach_existing_storage(values, devtype)
        else:
            self._create_virtual_disk_from_values(self.current_vm_dir, values, devtype)
        self.refresh_boot_order_choices()
        try:
            self._scan_media_vms_after_storage_change()
        except Exception:
            pass

    def _register_storage_device(self, name, path, devtype):
        devices=self._storage_devices_all(self.current_vm_dir)
        ap=os.path.abspath(path) if path else ""
        # Evita duplicados por ruta solo para discos; CD/DVD pueden tener el mismo ISO en varias unidades.
        if devtype != "cdrom":
            devices=[d for d in devices if os.path.abspath(d.get("path","")) != ap]
        devices.append({"id":"dev_" + uuid.uuid4().hex[:12],"name":name,"path":ap,"device":devtype})
        self._write_storage_devices(devices)

    def _register_cdrom_device(self, name, path="", source=""):
        devices=self._storage_devices_all(self.current_vm_dir)
        base=name or "CD/DVD"
        names={str(d.get("name") or "") for d in devices if d.get("device")=="cdrom"}
        final_name=base
        n=2
        while final_name in names:
            final_name=f"{base} {n}"
            n+=1
        entry={"id":"dev_" + uuid.uuid4().hex[:12],"name":final_name,"path":os.path.abspath(path) if path else "","device":"cdrom"}
        if source:
            entry["source"] = source
        devices.append(entry)
        self._write_storage_devices(devices)
        return entry["id"]

    def _update_cdrom_device(self, ident, path, source=None):
        """Actualiza una unidad CD/DVD y mantiene sincronizada la fuente del medio.

        Si el usuario cambia de un instalador por Internet a un ISO/IMG/DMG
        existente, hay que quitar explícitamente source=installer; de lo contrario
        el arranque volvería a considerar la unidad como un instalador pendiente
        y descargaría otra ISO aunque ya tenga una ruta válida.

        linux_installer_guard_v2: si la unidad queda sin source y sin
        path, se borra la ISO propia recordada (own_iso) para que no
        reaparezca al reabrir el dialogo.
        """
        devices=self._storage_devices_all(self.current_vm_dir)
        for d in devices:
            if d.get("id")==ident:
                d["path"]=os.path.abspath(path) if path else ""
                if source is not None:
                    if source:
                        d["source"] = source
                    else:
                        d.pop("source", None)
                if not d.get("source") and not d.get("path"):
                    d.pop("own_iso", None)
                break
        self._write_storage_devices(devices)

    def _get_cdrom_path(self):
        for d in self._storage_devices_all(self.current_vm_dir):
            if d.get("device")=="cdrom": return d.get("path","")
        return ""

    def _save_cdrom_path(self, path):
        # Compatibilidad: actualiza la primera unidad óptica existente; si no existe, crea una.
        devices=self._storage_devices_all(self.current_vm_dir)
        cd=next((d for d in devices if d.get("device")=="cdrom"),None)
        if cd:
            cd["path"]=os.path.abspath(path) if path else ""
        else:
            devices.append({"id":"dev_" + uuid.uuid4().hex[:12],"name":"CD/DVD 1","path":os.path.abspath(path) if path else "","device":"cdrom"})
        self._write_storage_devices(devices)

    def configure_boot_order(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, "Arranque", "Primero crea o selecciona una máquina virtual.")
            return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        tokens = self._current_boot_order_tokens()
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ Orden de dispositivos de arranque")
        dialog.resize(430, 360)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("El primero será el dispositivo que QEMU/UEFI intentará arrancar primero."))
        lst = QListWidget()
        layout.addWidget(lst, 1)
        for token in tokens:
            lst.addItem(self._boot_token_label(token))
            lst.item(lst.count() - 1).setData(Qt.ItemDataRole.UserRole, token)
        row = QHBoxLayout()
        up = QPushButton("⬆ Subir")
        down = QPushButton("⬇ Bajar")
        row.addWidget(up)
        row.addWidget(down)
        row.addStretch()
        layout.addLayout(row)
        def move(delta):
            i = lst.currentRow()
            j = i + delta
            if i < 0 or j < 0 or j >= lst.count():
                return
            item = lst.takeItem(i)
            lst.insertItem(j, item)
            lst.setCurrentRow(j)
        up.clicked.connect(lambda: move(-1))
        down.clicked.connect(lambda: move(1))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_order = [lst.item(i).data(Qt.ItemDataRole.UserRole) for i in range(lst.count())]
        self._save_boot_order(new_order)
        self.refresh_boot_order_choices()

    def _save_boot_order(self, order):
        if not self.current_vm_dir:
            return
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(cfg_path, encoding="utf-8")
        if not cfg.has_section("hardware"):
            cfg.add_section("hardware")
        cfg.set("hardware", "boot_order", json.dumps(order))
        first = order[0] if order else "disk"
        cfg.set("hardware", "boot_device", "cdrom" if str(first).startswith("cdrom") else ("network" if first == "network" else "disk"))
        with open(cfg_path, "w", encoding="utf-8") as f:
            cfg.write(f)
        if hasattr(self, "_invalidate_vm_config_cache"):
            self._invalidate_vm_config_cache(self.current_vm_dir)
        self.log_message("==> Orden de arranque guardado: " + " → ".join(self._boot_token_label(x) for x in order))

    def manage_cdrom(self):
        if not self._vm_is_selected():
            QMessageBox.information(self,"CD / DVD","Selecciona una máquina virtual."); return
        cds=[d for d in self._storage_devices_all(self.current_vm_dir) if d.get("device")=="cdrom"]
        if not cds:
            QMessageBox.information(self,"CD / DVD","Esta VM no tiene unidades CD/DVD."); return
        names=[f"{d.get('name','CD/DVD')} — {os.path.basename(d.get('path','')) if d.get('path') else 'vacío'}" for d in cds]
        name,ok=QInputDialog.getItem(self,"Unidad CD/DVD","Selecciona la unidad:",names,0,False)
        if not ok:return
        cd=cds[names.index(name)]; ident=cd.get('id'); state=self._runtime_state(os.path.basename(self.current_vm_dir))
        device_id=f"cd{cds.index(cd)}"
        if state=="stopped":
            # linux_installer_guard_v2: pasar distro para que el
            # dialogo pueda decidir si la opcion "installer" es
            # aplicable a esta distro.
            _distro_for_dlg = ""
            try:
                if self.combo_main_os.currentData() == "linux":
                    _distro_for_dlg = self.combo_lin_distro.currentText()
            except Exception:
                _distro_for_dlg = ""
            dialog=DiskCreationDialog(self,"cdrom",
                os_type=self.combo_main_os.currentData() if hasattr(self,'combo_main_os') else 'linux',
                distro=_distro_for_dlg,
                initial_path=cd.get('path',''), initial_name=cd.get('name','CD/DVD'))
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            v=dialog.values(); mode=v.get('cd_mode','empty')
            try:
                path=''
                if mode=='existing':
                    path=v.get('path','')
                    # Un ISO indicado manualmente deja de ser un instalador
                    # automático: limpiar source evita una descarga al arrancar.
                    self._update_cdrom_device(ident, path, source='')
                elif mode=='installer':
                    # La descarga se realiza al iniciar la VM.
                    self._update_cdrom_device(ident, '', source='installer')
                elif mode=='recovery':
                    # Recovery mantiene su flujo de descarga al iniciar.
                    self._update_cdrom_device(ident, '', source='recovery')
                self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
                try:
                    self._scan_media_vms_after_storage_change()
                except Exception:
                    pass
            except Exception as e: QMessageBox.critical(self,'CD/DVD',str(e))
            return
        current=cd.get('path','')
        if QMessageBox.question(self,"CD / DVD",f"¿Expulsar el medio de '{cd.get('name','CD/DVD')}'?\n\nEl archivo no se borrará.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            try:
                self._qmp_hmp(self.current_vm_dir,f"eject -f {device_id}"); QMessageBox.information(self,"CD/DVD","Medio expulsado.")
            except Exception as e: QMessageBox.warning(self,"CD/DVD",str(e))
            return
        # media_library_picker_v1: ofrecer dos vias para elegir el medio.
        box = QMessageBox(self)
        box.setWindowTitle("Cambiar medio en caliente")
        box.setText(
            f"Origen del nuevo medio para '{cd.get('name','CD/DVD')}':"
        )
        btn_disk = box.addButton("📁 Buscar en disco…",
                                 QMessageBox.ButtonRole.AcceptRole)
        btn_lib = box.addButton("📚 Elegir de la biblioteca…",
                                QMessageBox.ButtonRole.ActionRole)
        box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is None:
            return
        if clicked == btn_disk:
            iso, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar ISO", "",
                "Imágenes ISO (*.iso *.img *.dmg);;Todos los archivos (*)"
            )
            if not iso:
                return
        elif clicked == btn_lib:
            try:
                from dialogs import MediaPickerDialog
            except Exception as _imp_err:
                QMessageBox.warning(
                    self, "Biblioteca de Medios",
                    f"No se pudo abrir el selector de la biblioteca.\n\n{_imp_err}"
                )
                return
            _os = ""
            try:
                _os = self.combo_main_os.currentData() or ""
            except Exception:
                _os = ""
            # media_library_device_picker_storage_v1: filtrar por ISO.
            dlg = MediaPickerDialog(self, filter_os_type=_os,
                                    filter_media_type="iso")
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            chosen = dlg.chosen()
            if not chosen or not chosen.get("path"):
                return
            iso = chosen["path"]
        else:
            return
        try:
            self._qmp_hmp(self.current_vm_dir,f"change {device_id} {iso}"); self._update_cdrom_device(ident,iso); self.refresh_storage_ui(); self._update_manager_details(); QMessageBox.information(self,"CD/DVD","Medio cambiado en caliente.")
            try:
                self._scan_media_vms_after_storage_change()
            except Exception:
                pass
        except Exception as e: QMessageBox.critical(self,"CD/DVD",str(e))

    def modify_storage_device(self):
        if not self._ensure_storage_target_vm() or not hasattr(self, 'storage_tree'):
            QMessageBox.information(self, 'Almacenamiento', 'Selecciona o crea una máquina virtual.')
            return
        if self._runtime_state(os.path.basename(self.current_vm_dir)) != 'stopped':
            QMessageBox.warning(self, 'Almacenamiento', 'Apaga la VM antes de modificar un dispositivo de almacenamiento.')
            return
        item = self.storage_tree.currentItem()
        if not item or not item.data(0, Qt.ItemDataRole.UserRole):
            QMessageBox.information(self, 'Modificar dispositivo', 'Selecciona un dispositivo concreto en el árbol.')
            return
        meta = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(meta, dict) and meta.get("kind") == "cdrom":
            ident = meta.get("id")
            cd = next((d for d in self._storage_devices_all(self.current_vm_dir) if d.get("id")==ident), None)
            if not cd:
                QMessageBox.information(self,'Modificar dispositivo','No se encontró la unidad CD/DVD seleccionada.'); return
            # linux_installer_guard_v2: pasar distro para que el
            # dialogo pueda decidir si la opcion "installer" aplica.
            _distro_for_dlg2 = ""
            try:
                if self.combo_main_os.currentData() == "linux":
                    _distro_for_dlg2 = self.combo_lin_distro.currentText()
            except Exception:
                _distro_for_dlg2 = ""
            dialog = DiskCreationDialog(self, 'cdrom',
                                        os_type=self.combo_main_os.currentData() if hasattr(self, 'combo_main_os') else 'linux',
                                        distro=_distro_for_dlg2,
                                        initial_path=cd.get('path',''), initial_name=cd.get('name','CD/DVD'))
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = dialog.values()
            if values.get('cd_mode') == 'existing':
                # Al elegir manualmente un archivo existente, se cancela cualquier
                # marca anterior de descarga automática.
                self._update_cdrom_device(ident, values.get('path', ''), source='')
            elif values.get('cd_mode') == 'empty':
                self._update_cdrom_device(ident, '', source='')
            elif values.get('cd_mode') in ('installer', 'recovery'):
                # No descargamos al modificar: la descarga queda programada para
                # el próximo arranque, igual que al crear la unidad.
                source = values['cd_mode']
                self._update_cdrom_device(ident, '', source=source)
            devices=self._storage_devices_all(self.current_vm_dir)
            for d in devices:
                if d.get('id')==ident: d['name']=values.get('name') or d.get('name','CD/DVD')
            self._write_storage_devices(devices)
            self.refresh_storage_ui(); self.refresh_boot_order_choices(); self._update_manager_details()
            try:
                self._scan_media_vms_after_storage_change()
            except Exception:
                pass
            return

        path = meta.get("path") if isinstance(meta, dict) else item.data(0, Qt.ItemDataRole.UserRole)
        info = None
        for name, typ, dpath in self._storage_entries_with_types(self.current_vm_dir):
            if os.path.abspath(dpath) == os.path.abspath(path):
                info = (name, typ, dpath); break
        if not info:
            QMessageBox.information(self, 'Expandir disco',
                                    'No se encontro la informacion del '
                                    'dispositivo seleccionado.')
            return
        old_name, devtype, old_path = info

        # expand_only_v1_disk: solo se puede cambiar el TAMANO. El
        # nombre y la ruta del archivo quedan fijos para evitar
        # referencias rotas en la config de la VM (cambiar el path del
        # disco principal podia romper el arranque).
        if devtype == "floppy":
            QMessageBox.information(
                self, "Expandir disco",
                "Los disquetes no se pueden redimensionar.\n\n"
                "Eliminalo y crea otro si necesitas otro tamano."
            )
            return

        def _bytes_to_qemu_size(n):
            try:
                n = int(n)
            except (TypeError, ValueError):
                return ""
            if n <= 0:
                return ""
            for unit, div in (("T", 1024 ** 4), ("G", 1024 ** 3),
                              ("M", 1024 ** 2), ("K", 1024)):
                if n >= div:
                    v = n / div
                    if v == int(v):
                        return f"{int(v)}{unit}"
                    return f"{v:.2f}".rstrip("0").rstrip(".") + unit
            return str(n)

        _current_bytes = 0
        try:
            _r = subprocess.run(
                ["qemu-img", "info", "--output=json", old_path],
                capture_output=True, text=True, timeout=10, check=True,
            )
            _current_bytes = int(
                json.loads(_r.stdout).get("virtual-size", 0) or 0
            )
        except Exception:
            _current_bytes = 0

        try:
            _current_txt = (self._format_bytes_iexport(_current_bytes)
                            if _current_bytes else "\u2014")
        except Exception:
            _current_txt = f"{_current_bytes} B" if _current_bytes else "\u2014"
        _current_qemu = _bytes_to_qemu_size(_current_bytes)

        dialog = QDialog(self)
        dialog.setWindowTitle("\u2197 Expandir disco")
        dialog.resize(520, 280)
        lay = QVBoxLayout(dialog)
        form = QFormLayout()
        form.addRow("Dispositivo:", QLabel(devtype.upper()))
        form.addRow("Archivo:", QLabel(os.path.basename(old_path)))
        form.addRow("Tamano actual:", QLabel(_current_txt))
        size_edit = QLineEdit(_current_qemu)
        size_edit.setPlaceholderText("Ejemplo: 120G (solo crecer)")
        form.addRow("Nuevo tamano:", size_edit)
        lay.addLayout(form)

        hint = QLabel(
            "El disco solo puede CRECER. Si escribes un valor menor al "
            "actual, se rechaza y el campo vuelve al tamano original.\n\n"
            "Agrandar el archivo NO agranda la particion dentro del guest: "
            "tras aplicar el cambio, amplia tambien la particion/volumen "
            "desde el sistema invitado."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666;")
        lay.addWidget(hint)

        def _validate_and_accept():
            txt = size_edit.text().strip()
            if _current_bytes <= 0 or not txt or txt == _current_qemu:
                dialog.accept()
                return
            new_bytes = None
            if hasattr(self, '_parse_size_to_bytes'):
                try:
                    new_bytes = self._parse_size_to_bytes(txt)
                except Exception:
                    new_bytes = None
            if new_bytes is None:
                QMessageBox.warning(
                    dialog, 'Tamano invalido',
                    f"'{txt}' no es un tamano valido.\n\n"
                    "Usa un formato como 80G, 200G o 1T."
                )
                size_edit.setText(_current_qemu)
                return
            if new_bytes < _current_bytes:
                QMessageBox.warning(
                    dialog, 'No se puede encoger',
                    f"El disco no puede encogerse: tamano actual "
                    f"{_current_txt}, indicado {txt}.\n\n"
                    "El valor se ha restaurado al tamano actual. Si "
                    "necesitas un disco mas pequeno, crea uno nuevo y "
                    "migra los datos."
                )
                size_edit.setText(_current_qemu)
                return
            dialog.accept()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_b = QPushButton("Cancelar")
        ok_b = QPushButton("Aplicar")
        cancel_b.clicked.connect(dialog.reject)
        ok_b.clicked.connect(_validate_and_accept)
        btn_row.addWidget(cancel_b)
        btn_row.addWidget(ok_b)
        lay.addLayout(btn_row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        _txt = size_edit.text().strip()
        if not _txt or _txt == _current_qemu:
            return
        try:
            subprocess.run(
                ['qemu-img', 'resize', old_path, _txt],
                check=True, capture_output=True, text=True, timeout=600,
            )
            self.refresh_storage_ui()
            self._update_manager_details()
            QMessageBox.information(
                self, "Disco expandido",
                f"El disco se expandio correctamente a {_txt}.\n\n"
                "Recuerda ampliar tambien la particion/volumen dentro del "
                "sistema invitado si quieres aprovechar el nuevo espacio."
            )
            try:
                self._scan_media_vms_after_storage_change()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(
                self, "Expandir disco",
                f"No se pudo expandir el disco.\n\n{e}"
            )
