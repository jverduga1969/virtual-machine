# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: diagnóstico general — log persistente por VM (ver/exportar),
panel de Salud de la VM, limpieza de procesos huérfanos, y el chequeo/
reparación de dependencias de virtualización del host (KVM, OVMF, etc.).
"""
import os
import shutil
import time
from PyQt6.QtWidgets import (
    QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QMessageBox, QFileDialog,
)

import vm_config
from vm_config import load_vm_config
from host_deps import get_virtualization_dependency_status, ensure_virtualization_dependencies


class DiagnosticsMixin:
    # ------------------------------------------------------------------
    # Consola de progreso enriquecida
    # ------------------------------------------------------------------
    # Cada línea lleva [HH:MM:SS] + color según nivel. El historial se
    # mantiene en memoria (_log_history) para poder re-filtrar por nivel
    # o por texto sin perder mensajes. El log a disco (launch.log) se
    # sigue escribiendo igual que antes, con timestamp completo.

    @staticmethod
    def _log_classify(message):
        """Clasifica un mensaje en info / ok / warn / error.

        Reglas simples por prefijo. Son las mismas convenciones que ya
        usaba el proyecto: '==>' para pasos, '[AVISO]' para avisos,
        '[ERROR]' para errores, '✓' para confirmaciones.
        """
        m = (message or "")
        low = m.lower()
        stripped = low.lstrip()
        if stripped.startswith("[error]") or stripped.startswith("error:"):
            return "error"
        if ("[aviso]" in low) or stripped.startswith("aviso:") or ("warning" in low[:40]):
            return "warn"
        if m.lstrip().startswith("✓") or low.lstrip().startswith("[ok]"):
            return "ok"
        # Por defecto, info (incluye los pasos "==>").
        return "info"

    def _log_should_show(self, level, message):
        """Comprueba si una línea pasa los filtros actuales."""
        order = {"info": 0, "ok": 0, "warn": 1, "error": 2}
        min_level = getattr(self, "_log_min_level", "info")
        if order.get(level, 0) < order.get(min_level, 0):
            return False
        query = getattr(self, "_log_filter_text", "").strip().lower()
        if query and query not in (message or "").lower():
            return False
        return True

    def _log_append_line(self, stamp, level, message):
        """Inserta una línea en el QTextEdit con timestamp y color.

        Usa QTextCursor + insertHtml para garantizar que el HTML se
        interpreta (QTextEdit.append es ambiguo en este sentido entre
        versiones de Qt).
        """
        if not hasattr(self, "console") or self.console is None:
            return
        try:
            from PyQt6.QtGui import QTextCursor
            from html import escape
        except Exception:
            return
        colors = {
            "info": "#4ade80",   # verde claro
            "ok": "#7ee787",     # verde brillante
            "warn": "#f5a623",   # naranja
            "error": "#ff6b6b",  # rojo
        }
        color = colors.get(level, colors["info"])
        safe = escape(message or "")
        # Reemplazamos espacios por &nbsp; para que las líneas con muchos
        # espacios conserven el formato (mensajes tipo "==> [AVISO] ...").
        safe = safe.replace("  ", "&nbsp;&nbsp;")
        html = (
            f'<span style="color:#5c6370;">[{stamp}]</span>&nbsp;'
            f'<span style="color:{color};">{safe}</span><br>'
        )
        try:
            cursor = self.console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml(html)
            if getattr(self, "_log_autoscroll", True):
                self.console.verticalScrollBar().setValue(
                    self.console.verticalScrollBar().maximum()
                )
        except Exception:
            # Fallback a append plano si algo falla.
            try:
                self.console.append(f"[{stamp}] {message}")
            except Exception:
                pass

    def _log_rerender(self):
        """Re-dibuja el QTextEdit a partir del historial y los filtros."""
        if not hasattr(self, "console") or self.console is None:
            return
        try:
            self.console.clear()
        except Exception:
            return
        for stamp, level, message in getattr(self, "_log_history", []):
            if self._log_should_show(level, message):
                self._log_append_line(stamp, level, message)

    def _on_log_level_changed(self, _index):
        combo = getattr(self, "log_level_combo", None)
        if combo is not None:
            self._log_min_level = combo.currentData() or "info"
        self._log_rerender()

    def _on_log_search_changed(self, text):
        self._log_filter_text = text or ""
        self._log_rerender()

    def _on_log_autoscroll_changed(self, state):
        from PyQt6.QtCore import Qt
        self._log_autoscroll = (state == int(Qt.CheckState.Checked.value)
                                or state == 2 or bool(state))

    def _clear_log_console(self):
        """Limpia la consola y el historial en memoria. NO borra launch.log."""
        if hasattr(self, "console") and self.console is not None:
            try:
                self.console.clear()
            except Exception:
                pass
        self._log_history = []

    def log_message(self, message):
        """Añade un mensaje a la consola y a launch.log.

        - En memoria: mantiene (stamp, level, message) para re-filtrado.
        - En pantalla: color + timestamp, sujeto a los filtros actuales.
        - En disco: sigue guardando el timestamp completo igual que antes.
        """
        stamp = time.strftime("%H:%M:%S")
        level = self._log_classify(message)

        if not hasattr(self, "_log_history"):
            self._log_history = []
        self._log_history.append((stamp, level, message))
        # Limitar el historial para no crecer sin control en sesiones largas.
        if len(self._log_history) > 5000:
            self._log_history = self._log_history[-5000:]

        if self._log_should_show(level, message):
            self._log_append_line(stamp, level, message)

        # Persistencia a disco (sin cambios respecto a la versión anterior).
        if self.current_vm_dir:
            try:
                full_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
                with open(os.path.join(self.current_vm_dir, "launch.log"),
                          "a", encoding="utf-8") as f:
                    f.write(f"[{full_stamp}] {message}\n")
            except Exception:
                pass


    def show_full_log(self):
        if not self.current_vm_dir:
            QMessageBox.information(self, self.tr("Ver log completo"), self.tr("Selecciona una VM primero."))
            return
        log_path = os.path.join(self.current_vm_dir, "launch.log")
        if not os.path.isfile(log_path):
            QMessageBox.information(self, self.tr("Ver log completo"), self.tr("Todavía no hay historial guardado para esta VM."))
            return
        try:
            with open(log_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            QMessageBox.warning(
                self, self.tr("Ver log completo"),
                self.tr("No se pudo leer el log: {0}").format(e),
            )
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(
            self.tr("Log completo — {0}").format(
                os.path.basename(self.current_vm_dir))
        )
        dlg.resize(800, 500)
        lay = QVBoxLayout(dlg)
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
        viewer.setPlainText(content)
        viewer.verticalScrollBar().setValue(viewer.verticalScrollBar().maximum())
        lay.addWidget(viewer)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton(self.tr("Cerrar"))
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)
        dlg.exec()

    def export_full_log(self):
        if not self.current_vm_dir:
            QMessageBox.information(self, self.tr("Exportar log"), self.tr("Selecciona una VM primero."))
            return
        log_path = os.path.join(self.current_vm_dir, "launch.log")
        if not os.path.isfile(log_path):
            QMessageBox.information(self, self.tr("Exportar log"), self.tr("Todavía no hay historial guardado para esta VM."))
            return
        suggested = f"{os.path.basename(self.current_vm_dir)}-log.txt"
        dest, _ = QFileDialog.getSaveFileName(self, self.tr("Exportar log"), suggested, "Texto (*.txt);;Todos los archivos (*)")
        if not dest:
            return
        try:
            shutil.copyfile(log_path, dest)
            QMessageBox.information(
                self, self.tr("Exportar log"),
                self.tr("Log exportado a:\n{0}").format(dest),
            )
        except OSError as e:
            QMessageBox.warning(
                self, self.tr("Exportar log"),
                self.tr("No se pudo exportar el log: {0}").format(e),
            )

    def show_vm_health_check(self):
        """Reúne en un solo diálogo lo que hoy exige abrir una terminal y
        correr varios comandos a mano: si el proceso QEMU sigue vivo, si el
        Guest Agent responde, y el estado de cada carpeta compartida y de
        virtiofsd/swtpm asociados a esta VM."""
        if not self.current_vm_dir:
            QMessageBox.information(self, self.tr("Salud de la VM"), self.tr("Selecciona una VM primero."))
            return
        vm_name = os.path.basename(self.current_vm_dir)
        lines = [
            self.tr("VM: {0}").format(vm_name),
            self.tr("Carpeta: {0}").format(self.current_vm_dir),
            "",
        ]

        state = self._runtime_state(vm_name)
        pid_path, qmp_path = self._runtime_paths(self.current_vm_dir)
        if state == "stopped":
            lines.append(self.tr("● QEMU: detenido."))
        else:
            pid_txt = ""
            try:
                with open(pid_path, encoding="utf-8") as f:
                    pid_txt = f" (PID {f.read().strip()})"
            except OSError:
                pass
            lines.append(self.tr("● QEMU: {0}{1}.").format(state, pid_txt))

        # Guest Agent
        if state == "stopped":
            lines.append(self.tr("● Guest Agent: no aplica (VM apagada)."))
        else:
            try:
                result = self._qga_request({"execute": "guest-info"}, timeout=3)
                info = (result or {}).get("return") or {}
                ver = info.get("version") or "desconocida"
                lines.append(self.tr("● Guest Agent: responde (v{0}).").format(ver))
            except Exception as e:
                lines.append(self.tr(
                    "● Guest Agent: sin respuesta ({0}). "
                    "Verifica que qemu-guest-agent esté instalado y "
                    "corriendo en el guest."
                ).format(e))

        # Carpetas compartidas VirtioFS: proceso virtiofsd vivo por cada una.
        try:
            cfg = load_vm_config(self.current_vm_dir)
            folders = (cfg.get("extra") or {}).get("shared_folders", [])
            folders = folders if isinstance(folders, list) else []
        except Exception:
            folders = []
        virtiofs_folders = [f for f in folders if isinstance(f, dict) and str(f.get("method", "")).lower() == "virtiofs"]
        if not virtiofs_folders:
            lines.append(self.tr("● Carpetas compartidas (VirtioFS): ninguna configurada."))
        else:
            lines.append(self.tr("● Carpetas compartidas (VirtioFS):"))
            for i, f in enumerate(virtiofs_folders):
                guest = f.get("guest") or f"share{i}"
                pidfile = os.path.join(self.current_vm_dir, f"virtiofs-{i}.pid")
                alive = False
                pid_val = None
                try:
                    with open(pidfile, encoding="utf-8") as fh:
                        pid_val = int(fh.read().strip())
                    os.kill(pid_val, 0)
                    alive = True
                except Exception:
                    alive = False
                if state == "stopped":
                    lines.append(
                    self.tr("    - {0}: no aplica (VM apagada).").format(guest)
                )
                elif alive:
                    lines.append(
                    self.tr("    - {0}: virtiofsd activo (PID {1}).").format(
                        guest, pid_val)
                )
                else:
                    log_path = os.path.join(self.current_vm_dir, f"virtiofsd_{i}.log")
                    lines.append(self.tr(
                        "    - {0}: NO está activo. Revisa {1} si "
                        "esperabas que funcionara."
                    ).format(guest, log_path))

        QMessageBox.information(self, self.tr("Salud de la VM"), "\n".join(lines))

    def clean_orphan_processes(self):
        """Busca procesos qemu-system-x86_64 / virtiofsd / swtpm que quedaron
        vivos de una sesión anterior (p. ej. tras un cierre forzado que no dejó
        correr el trap de limpieza) y ofrece detenerlos. No toca procesos que
        no pertenezcan a una carpeta de VM gestionada por esta app."""
        candidates = []  # (pid, comando, vm_dir_o_None, descripcion)
        try:
            vm_dirs = [os.path.join(vm_config.BASE_VM_DIR, n) for n in os.listdir(vm_config.BASE_VM_DIR)] if os.path.isdir(vm_config.BASE_VM_DIR) else []
        except OSError:
            vm_dirs = []

        for vm_dir in vm_dirs:
            if not os.path.isdir(vm_dir):
                continue
            vm_name = os.path.basename(vm_dir)
            # qemu.pid: si el proceso murió pero el archivo quedó, no hay nada
            # que "limpiar" como huérfano (no hay proceso vivo); solo importa
            # cuando SÍ hay un proceso vivo pero la app ya no lo considera la
            # VM activa que el usuario ve corriendo intencionalmente.
            for fname in os.listdir(vm_dir) if os.path.isdir(vm_dir) else []:
                if not (fname == "qemu.pid" or (fname.startswith("virtiofs-") and fname.endswith(".pid"))):
                    continue
                fpath = os.path.join(vm_dir, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        pid = int(f.read().strip())
                    os.kill(pid, 0)
                except Exception:
                    continue
                kind = "QEMU" if fname == "qemu.pid" else "virtiofsd"
                candidates.append((pid, kind, vm_name, fpath))

        # Solo se ofrecen como "huérfanos" los procesos auxiliares (virtiofsd);
        # un qemu.pid vivo puede ser perfectamente la VM que el usuario tiene
        # abierta ahora mismo, así que ese caso solo se informa, no se ofrece
        # matar por aquí (para eso está el botón normal de Detener VM).
        aux_orphans = [c for c in candidates if c[1] == "virtiofsd"]
        running_qemu = [c for c in candidates if c[1] == "QEMU"]

        if not candidates:
            QMessageBox.information(self, self.tr("Limpiar procesos huérfanos"), self.tr("No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores."))
            return

        lines = []
        if running_qemu:
            lines.append(self.tr("VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):"))
            for pid, _kind, vm_name, _ in running_qemu:
                lines.append(self.tr("  - {0} (PID {1})").format(vm_name, pid))
            lines.append("")
        if aux_orphans:
            lines.append(self.tr("Procesos virtiofsd huérfanos encontrados:"))
            for pid, _kind, vm_name, _ in aux_orphans:
                lines.append(self.tr("  - {0}: virtiofsd PID {1}").format(vm_name, pid))
            lines.append("\n¿Deseas detenerlos ahora?")
            answer = QMessageBox.question(
                self, self.tr("Limpiar procesos huérfanos"), "\n".join(lines),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                killed, failed = 0, []
                for pid, _kind, vm_name, fpath in aux_orphans:
                    try:
                        os.kill(pid, 15)
                        killed += 1
                        try:
                            os.remove(fpath)
                        except OSError:
                            pass
                    except OSError as e:
                        failed.append(f"{vm_name} (PID {pid}): {e}")
                msg = self.tr("Se detuvieron {0} proceso(s) huérfano(s).").format(killed)
                if failed:
                    msg += self.tr("\n\nNo se pudieron detener:\n")
                    msg += "\n".join(failed)
                QMessageBox.information(self, self.tr("Limpiar procesos huérfanos"), msg)
        else:
            QMessageBox.information(self, self.tr("Limpiar procesos huérfanos"), "\n".join(lines) if lines else self.tr("Nada que limpiar."))

    def _set_status_label(self, label, name, ok, detail=""):
        status = self.tr("OK") if ok else self.tr("FALTA")
        suffix = self.tr(" ({0})").format(detail) if detail else ""
        label.setText(f"{name}: {status}{suffix}")
        self._set_status_color(label, bool(ok))

    def _set_status_color(self, label, state):
        """Colorea el estado: verde=OK, rojo=FALTA/error, gris=sin comprobar."""
        if state is True:
            label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        elif state is False:
            label.setStyleSheet("color: #c62828; font-weight: bold;")
        else:
            label.setStyleSheet("color: #757575;")

    def _set_dependency_status_unchecked(self):
        """Estado inicial ligero: no ejecuta ningún diagnóstico del sistema."""
        labels = [
            (self.status_qemu, "QEMU"), (self.status_kvm, "KVM"),
            (self.status_ovmf, "OVMF"), (self.status_swtpm, "swtpm"),
            (self.status_secure, "Secure Boot"), (self.status_virtio, "VirtIO"),
            (self.status_audio, "Audio"),
        ]
        for label, name in labels:
            label.setText(f"{name}: {self.tr('SIN COMPROBAR')}")
            self._set_status_color(label, None)
        self.header_host_status.setText(self.tr("Virtualización: sin comprobar"))
        self.header_host_status.setStyleSheet("color: #757575; font-weight: bold;")
        self.header_host_status.setToolTip(self.tr("Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema."))

    def refresh_dependency_status(self):
        """Actualiza el panel sin modificar la configuración de la VM."""
        try:
            st = get_virtualization_dependency_status()
            self.label_host_distro.setText(
                self.tr("Distribución: {0}").format(st['distro'])
            )
            self.label_host_manager.setText(
                self.tr("Gestor de paquetes: {0}").format(st['package_manager'])
            )
            self._set_status_label(
                self.status_qemu, "QEMU", st["qemu"],
                st["qemu_path"] or self.tr("no encontrado"),
            )
            self._set_status_label(self.status_kvm, "KVM", st["kvm"], "/dev/kvm" if st["kvm"] else "sin /dev/kvm")
            self._set_status_label(self.status_ovmf, "OVMF", st["ovmf"])
            self._set_status_label(
                self.status_swtpm, "swtpm", st["swtpm"],
                st["swtpm_path"] or self.tr("no encontrado"),
            )
            self._set_status_label(
                self.status_secure, "Secure Boot", st["secure_boot"],
                self.tr("firmware disponible") if st["secure_boot"]
                else self.tr("sin plantilla Secure Boot"),
            )
            self._set_status_label(
                self.status_virtio, "VirtIO", st["virtio"],
                self.tr("módulos") if st["virtio"]
                else self.tr("módulo no cargado"),
            )
            if hasattr(self, "status_audio"):
                self._set_status_label(self.status_audio, "Audio", st["audio"], st["audio_backend"])
            ok_core = st["qemu"] and st["kvm"]
            _mark = lambda b: "✓" if b else "✗"
            self.header_host_status.setText(
                self.tr(
                    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | "
                    "TPM {4} | Audio {5} | GPU {6}"
                ).format(
                    self.tr("OK") if ok_core else self.tr("REVISAR"),
                    _mark(st['qemu']),
                    _mark(st['kvm']),
                    _mark(st['ovmf']),
                    _mark(st['swtpm']),
                    _mark(st['audio']),
                    _mark(st['graphics']['gpu'] != 'No detectada'),
                )
            )
            self.header_host_status.setStyleSheet(
                "color: #2e7d32; font-weight: bold;" if ok_core else
                "color: #c62828; font-weight: bold;"
            )
            _yn = lambda b: self.tr("sí") if b else self.tr("no")
            self.header_host_status.setToolTip(
                self.tr(
                    "Distribución: {0}\n"
                    "Gestor de paquetes: {1}\n"
                    "Secure Boot: {2}\n"
                    "VirtIO: {3}\n"
                    "Audio: {4}\n"
                    "GPU: {5}\n"
                    "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}"
                ).format(
                    st['distro'],
                    st['package_manager'],
                    self.tr("disponible") if st["secure_boot"]
                    else self.tr("no disponible"),
                    self.tr("disponible") if st["virtio"]
                    else self.tr("no detectado"),
                    st['audio_backend'],
                    st['graphics']['gpu'],
                    _yn(st['graphics']['opengl']),
                    _yn(st['graphics']['vulkan']),
                    _yn(st['graphics']['virgl']),
                    _yn(st['graphics']['vfio']),
                )
            )
            return st
        except Exception as e:
            self.log_message(f"ERROR comprobando dependencias: {e}")
            return None

    def repair_dependency_status(self):
        """Comprueba y repara OVMF/swtpm según la configuración actual."""
        st = self.refresh_dependency_status()
        if not st:
            return
        firmware = self.combo_firmware.currentData()
        tpm = self.check_tpm.isChecked()
        # Secure Boot necesita OVMF aunque el combo esté temporalmente en BIOS.
        need_ovmf = firmware == "uefi" or self.check_secure_boot.isChecked()
        try:
            self.log_message("==> Comprobando/Reparando dependencias del sistema...")
            ensure_virtualization_dependencies(
                need_ovmf=need_ovmf,
                need_swtpm=tpm,
                need_secure_boot=self.check_secure_boot.isChecked(),
                log_func=self.log_message,
            )
            self.log_message("==> Comprobación/Reparación finalizada.")
            self.refresh_dependency_status()
            QMessageBox.information(self, self.tr("Dependencias"), self.tr("La comprobación/reparación terminó correctamente."))
        except Exception as e:
            self.refresh_dependency_status()
            QMessageBox.critical(
                self, self.tr("Dependencias"),
                self.tr(
                    "No se pudieron reparar todas las dependencias.\n\n{0}"
                ).format(e),
            )


# i18n_tanda3_diagnostics_v1
