# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: integración host↔guest — carpetas compartidas (VirtioFS/9p/SMB),
clipboard, Guest Agent (QGA por socket unix) y Guest Tools (generar/
adjuntar el ISO de instalación de spice-vdagent/qemu-guest-agent).
"""
import os
import re
import json
import shlex
import socket
import subprocess
import time
import uuid
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFormLayout, QCheckBox, QFileDialog,
    QTreeWidgetItem,
)
from task_progress import TaskProgressDialog

import vm_config
from vm_config import load_vm_config, save_vm_config
from shared_folders import get_shared_folder_dependency_status, ensure_shared_folder_dependencies
from guest_tools_iso import GUEST_TOOLS_ISO_NAME, create_guest_tools_iso
from workers import _BackgroundCallThread


class GuestIntegrationMixin:
    def _set_shared_dep_label(self, label, name, ok, detail=""):
        label.setText(f"{name}: {self.tr('OK') if ok else self.tr('FALTA')}" + (f" ({detail})" if detail else ""))
        label.setStyleSheet("color:#2e7d32; font-weight:bold;" if ok else "color:#c62828; font-weight:bold;")

    def refresh_shared_folder_dependencies(self):
        """Comprueba las dependencias host necesarias para cada método de carpetas compartidas."""
        try:
            st=get_shared_folder_dependency_status()
            self._set_shared_dep_label(self.sf_dep_virtiofsd,"VirtioFS",st["virtiofsd"],st["virtiofsd_path"] or "virtiofsd no encontrado")
            self._set_shared_dep_label(self.sf_dep_9p,"9p",st["9p"],st["9p_detail"])
            self._set_shared_dep_label(self.sf_dep_smb,"SMB",st["smb"],st["smb_detail"])
            self.btn_sf_install_deps.setEnabled(not st["virtiofsd"] or not st["smb"])
            return st
        except Exception as e:
            self.log_message(f"ERROR comprobando dependencias de carpetas compartidas: {e}")
            return None

    def install_shared_folder_dependencies(self):
        """Instala virtiofsd y/o Samba si faltan en el host."""
        st=self.refresh_shared_folder_dependencies()
        if not st: return
        need_v=not st["virtiofsd"]
        need_s=not st["smb"]
        if not need_v and not need_s:
            QMessageBox.information(self,self.tr("Carpetas compartidas"),self.tr("Las dependencias del host ya están instaladas."))
            return
        items=[]
        if need_v: items.append("VirtioFS (virtiofsd)")
        if need_s: items.append("SMB (Samba/smbd)")
        ans=QMessageBox.question(self,self.tr("Instalar dependencias"), self.tr("Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?").format("\n• ".join(items)), QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if ans != QMessageBox.StandardButton.Yes: return
        try:
            self.log_message("==> Instalando dependencias de carpetas compartidas...")
            ensure_shared_folder_dependencies(need_virtiofsd=need_v, need_smb=need_s, log_func=self.log_message)
            self.refresh_shared_folder_dependencies()
            QMessageBox.information(self,self.tr("Dependencias"),self.tr("Las dependencias de carpetas compartidas quedaron instaladas y verificadas."))
        except Exception as e:
            self.refresh_shared_folder_dependencies()
            QMessageBox.critical(self,self.tr("Dependencias"),self.tr("No se pudieron instalar todas las dependencias.\n\n{0}").format(e))

    def _qga_socket_path(self, vm_dir=None):
        return os.path.join(vm_dir or self.current_vm_dir or "", "qga.sock")

    def _qga_connect(self, timeout=8, vm_dir=None):
        """Abre el canal QGA y sincroniza el protocolo antes de enviar comandos.

        Importante: QEMU Guest Agent NO envía un saludo inicial como QMP.
        El cliente debe iniciar la comunicación con guest-sync-delimited.
        """
        import socket
        path = self._qga_socket_path(vm_dir)
        if not path or not os.path.exists(path):
            raise RuntimeError(self.tr("El socket de QEMU Guest Agent no está disponible."))
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(path)
        try:
            sync_id = int(time.time_ns() & 0x7FFFFFFFFFFFFFFF)
            # 0xFF fuerza al parser del QGA a un estado conocido; después
            # usamos guest-sync-delimited, recomendado por la documentación.
            sync_req = {
                "execute": "guest-sync-delimited",
                "arguments": {"id": sync_id},
                "id": sync_id,
            }
            sock.sendall(b"\xff" + json.dumps(sync_req, separators=(",", ":")).encode() + b"\n")
            deadline = time.time() + timeout
            while time.time() < deadline:
                data = sock.recv(65536)
                if not data:
                    raise RuntimeError(self.tr("QEMU Guest Agent cerró el canal durante la sincronización."))
                # La respuesta de guest-sync-delimited comienza con 0xFF.
                for raw in data.splitlines():
                    raw = raw.lstrip(b"\xff\x00\r\n")
                    if not raw:
                        continue
                    try:
                        obj = json.loads(raw.decode(errors="replace"))
                    except json.JSONDecodeError:
                        continue
                    if obj.get("return") == sync_id or obj.get("id") == sync_id:
                        return sock
            raise RuntimeError(self.tr("Tiempo agotado sincronizando QEMU Guest Agent."))
        except Exception:
            sock.close()
            raise

    def _qga_send(self, sock, payload, timeout=8):
        """Envía un comando QGA y devuelve su respuesta, ignorando eventos ajenos."""
        req = dict(payload)
        if "id" not in req:
            req["id"] = int(time.time_ns() & 0x7FFFFFFFFFFFFFFF)
        expected_id = req["id"]
        sock.settimeout(timeout)
        sock.sendall(json.dumps(req, separators=(",", ":")).encode() + b"\n")
        deadline = time.time() + timeout
        pending = b""
        while time.time() < deadline:
            data = sock.recv(65536)
            if not data:
                raise RuntimeError(self.tr("QEMU Guest Agent cerró el canal."))
            pending += data
            while b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
                raw = raw.lstrip(b"\xff\x00\r\n")
                if not raw:
                    continue
                try:
                    obj = json.loads(raw.decode(errors="replace"))
                except json.JSONDecodeError:
                    continue
                if obj.get("id") == expected_id:
                    return obj
        raise RuntimeError(self.tr("Tiempo agotado esperando la respuesta de QEMU Guest Agent."))

    def _qga_request(self, payload, timeout=8):
        """Envía una petición QEMU Guest Agent usando guest-sync-delimited."""
        sock = self._qga_connect(timeout=timeout)
        try:
            return self._qga_send(sock, payload, timeout=timeout)
        finally:
            sock.close()

    def _qga_exec(self, command, args=None, timeout=20, vm_dir=None):
        sock = self._qga_connect(timeout=8, vm_dir=vm_dir)
        try:
            rid = int(time.time_ns() & 0x7FFFFFFFFFFFFFFF)
            r = self._qga_send(sock, {
                "execute": "guest-exec",
                "arguments": {
                    "path": command,
                    "arg": args or [],
                    "capture-output": False,
                },
                "id": rid,
            }, timeout=8)
            if "error" in r:
                raise RuntimeError(r["error"].get("desc") or str(r["error"]))
            pid = (r.get("return") or {}).get("pid")
            if not pid:
                raise RuntimeError(self.tr("Guest Agent no devolvió el PID de guest-exec."))

            deadline = time.time() + timeout
            while time.time() < deadline:
                time.sleep(0.4)
                status_id = int(time.time_ns() & 0x7FFFFFFFFFFFFFFF)
                r = self._qga_send(sock, {
                    "execute": "guest-exec-status",
                    "arguments": {"pid": pid},
                    "id": status_id,
                }, timeout=8)
                if "error" in r:
                    raise RuntimeError(r["error"].get("desc") or str(r["error"]))
                ret = r.get("return") or {}
                if ret.get("exited"):
                    code = int(ret.get("exitcode", 1))
                    if code != 0:
                        raise RuntimeError(self.tr("guest-exec terminó con código {0}.").format(code))
                    return True
            raise RuntimeError(self.tr("Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent."))
        finally:
            sock.close()

    def _qga_wait_ready(self, vm_dir, log_emit, is_cancelled, max_wait=180, poll=3):
        """Espera a que el QEMU Guest Agent del guest responda a guest-ping.

        Devuelve True si respondió; False si la VM se detuvo o se canceló
        (no es un error); lanza RuntimeError si agota max_wait o si el canal
        nunca apareció. Es normal que el agente tarde: el guest tiene que
        terminar de arrancar (y tenerlo instalado)."""
        sock_path = self._qga_socket_path(vm_dir)
        start = time.time()
        last_log = start
        seen_socket = False
        while True:
            if is_cancelled():
                return False
            elapsed = time.time() - start
            if os.path.exists(sock_path):
                seen_socket = True
            elif seen_socket:
                return False  # el socket desapareció: la VM se apagó
            elif elapsed > 30:
                raise RuntimeError(self.tr("El canal de QEMU Guest Agent no está disponible en esta VM."))
            if seen_socket:
                try:
                    s = self._qga_connect(timeout=4, vm_dir=vm_dir)
                    try:
                        r = self._qga_send(s, {"execute": "guest-ping"}, timeout=4)
                    finally:
                        s.close()
                    if "error" not in r:
                        return True
                except (ConnectionRefusedError, FileNotFoundError):
                    return False  # QEMU ya no está escuchando
                except Exception:
                    pass  # el agente todavía no responde (arrancando o no instalado)
            if elapsed >= max_wait:
                raise RuntimeError(
                    self.tr("El Guest Agent del invitado no respondió en {0} s "
                            "(no está instalado o no se está ejecutando).").format(int(max_wait)))
            if time.time() - last_log >= 30:
                log_emit(f"==> Esperando al Guest Agent del invitado ({int(elapsed)} s)...")
                last_log = time.time()
            for _ in range(int(poll * 2)):
                if is_cancelled():
                    return False
                time.sleep(0.5)

    def _configure_linux_shared_automount(self):
        """Monta automáticamente, en un Linux instalado, las carpetas VirtioFS
        marcadas como auto-start. Requiere qemu-guest-agent en el guest.

        Corre en un hilo de fondo: primero espera (hasta 3 min) a que el
        agente responda, y en cuanto lo hace configura /etc/fstab y arranca la
        unidad automount de cada carpeta. Así funciona aunque el guest tarde en
        arrancar; si la VM se apaga antes, termina sin molestar."""
        if not self.current_vm_dir:
            return
        vm_dir = self.current_vm_dir
        threads = getattr(self, "_automount_threads", None)
        if threads is None:
            threads = self._automount_threads = {}
        running = threads.get(vm_dir)
        if running is not None and running.isRunning():
            return

        def _work(log_emit, is_cancelled, progress_emit=None):
            cfg = load_vm_config(vm_dir)
            if cfg.get("os_type") != "linux":
                return
            folders = (cfg.get("extra") or {}).get("shared_folders", [])
            pending = [d for d in folders if isinstance(d, dict)
                       and str(d.get("mount_mode", "manual")).lower() == "auto_start"
                       and str(d.get("method", "auto")).lower() in ("auto", "virtiofs")]
            if not pending:
                return
            log_emit("==> Carpetas compartidas con montaje automático: esperando al QEMU Guest Agent del invitado...")
            if not self._qga_wait_ready(vm_dir, log_emit, is_cancelled):
                return
            log_emit("==> Guest Agent listo; configurando montajes.")
            for d in pending:
                if is_cancelled():
                    return
                tag = re.sub(r"[^A-Za-z0-9_.-]", "_", str(d.get("guest") or "share"))[:40] or "share"
                mountpoint = "/mnt/" + tag
                opts = "nofail,x-systemd.automount"
                if d.get("readonly"):
                    opts += ",ro"
                line = f"{tag} {mountpoint} virtiofs {opts} 0 0"
                qline = shlex.quote(line)
                # No ejecutamos `mount` directamente: con x-systemd.automount
                # podría quedarse esperando y hacer que guest-exec parezca
                # colgado. Creamos la entrada persistente, recargamos systemd y
                # arrancamos solo la unidad automount; el montaje real ocurre
                # al acceder a /mnt/<tag>. El nombre de la unidad lo calcula
                # systemd-escape (escapa '-', '.', etc.); el cálculo manual es
                # solo un respaldo.
                fallback_unit = mountpoint.lstrip("/").replace("/", "-") + ".automount"
                script = "\n".join([
                    "set -e",
                    "mkdir -p " + shlex.quote(mountpoint),
                    "touch /etc/fstab",
                    "grep -Fqx -- " + qline + " /etc/fstab || printf '%s\\n' " + qline + " >> /etc/fstab",
                    "systemctl daemon-reload",
                    "U=$(systemd-escape -p --suffix=automount " + shlex.quote(mountpoint) + " 2>/dev/null || true)",
                    "[ -n \"$U\" ] || U=" + shlex.quote(fallback_unit),
                    "systemctl start \"$U\"",
                ])
                log_emit(f"==> Configurando montaje automático de VirtioFS: {mountpoint}")
                self._qga_exec("/bin/sh", ["-c", script], timeout=25, vm_dir=vm_dir)
                log_emit(f"✓ VirtioFS montado automáticamente en {mountpoint}.")

        thread = _BackgroundCallThread(_work, parent=self)
        thread.log_signal.connect(self.log_message)

        def _on_done(_result, error):
            if error is not None:
                QMessageBox.information(
                    self, self.tr("Montaje automático"),
                    self.tr("La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n"
                            "{0}\n\n"
                            "Comprueba que qemu-guest-agent esté instalado y ejecutándose en el guest "
                            "(pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.").format(error)
                )
                self.log_message(f"[AVISO] Montaje automático: {error}")
            threads.pop(vm_dir, None)

        thread.done_signal.connect(_on_done)
        threads[vm_dir] = thread
        thread.start()

    def _show_shared_mount_hint(self, vm_name=None):
        """Muestra al usuario cómo montar VirtioFS dentro de un guest Linux.

        QEMU presenta el dispositivo al guest, pero el montaje pertenece al sistema
        operativo invitado. Esto es especialmente importante en LiveCD, donde no
        podemos modificar de forma persistente /etc/fstab.
        """
        if not self.current_vm_dir:
            return
        try:
            cfg = load_vm_config(self.current_vm_dir)
            if cfg.get("os_type") != "linux":
                return
            folders = (cfg.get("extra") or {}).get("shared_folders", [])
            if not isinstance(folders, list):
                return
            virtio = [d for d in folders if isinstance(d, dict) and str(d.get("method") or "auto").lower() in ("auto", "virtiofs")]
            if not virtio:
                return
            lines = []
            for d in virtio[:8]:
                tag = re.sub(r"[^A-Za-z0-9_.-]", "_", str(d.get("guest") or "share"))[:40] or "share"
                mountpoint = "/mnt/" + tag
                lines.append(f"sudo mkdir -p {mountpoint}\nsudo mount -t virtiofs {tag} {mountpoint}")
            text = (
                self.tr("La carpeta compartida VirtioFS ya está conectada a la VM.\n\n"
                        "En Linux el dispositivo debe montarse dentro del guest. En un LiveCD "
                        "no es posible hacerlo de forma persistente desde el host sin un agente "
                        "instalado en el guest.\n\n"
                        "Comando(s):\n\n") + "\n\n".join(lines) +
                self.tr("\n\n"
                        "En una instalación Linux permanente podremos añadir automontaje mediante "
                        "fstab/systemd en una versión posterior.")
            )
            QMessageBox.information(self, self.tr("Carpeta compartida lista"), text)
        except Exception as e:
            self.log_message(f"[AVISO] No se pudieron mostrar las instrucciones de montaje: {e}")

    def _guest_tools_dir(self):
        return os.path.join(vm_config.BASE_VM_DIR, "GuestTools")

    def open_guest_tools_folder(self):
        folder=self._guest_tools_dir(); os.makedirs(folder, exist_ok=True)
        try: subprocess.Popen(["xdg-open", folder])
        except Exception: QMessageBox.information(self, self.tr("Guest Tools"), self.tr("Carpeta:\n{0}").format(folder))

    def create_guest_tools_iso_ui(self):
        """Genera la ISO de Guest Tools en un hilo de fondo (mkisofs puede
        tardar 1-2 segundos y bloquear la UI si se hace de forma síncrona)."""
        folder = self._guest_tools_dir()
        os.makedirs(folder, exist_ok=True)
        out = os.path.join(folder, GUEST_TOOLS_ISO_NAME)

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit("==> Generando ISO de Guest Tools…")
            progress_emit(-1, self.tr("Generando ISO de Guest Tools…"))
            create_guest_tools_iso(out)
            log_emit(f"==> ISO de Guest Tools generada: {out}")
            progress_emit(100, self.tr("ISO creada."))
            return out

        def _on_success(iso_path):
            if hasattr(self, "guest_agent_status_label"):
                self.guest_agent_status_label.setText(self.tr("ISO disponible: {0}").format(iso_path))

        self.run_async(
            _work,
            self.tr("Crear ISO de Guest Tools"),
            on_success=_on_success,
            on_error=lambda e: self._show_selectable_error(
                self.tr("Guest Tools"), self.tr("No se pudo crear la ISO.\n\n{0}").format(e)
            ),
            cancelable=False,
            show_log=True,
            subtitle=self.tr("La ISO se guarda en la carpeta GuestTools."),
        )


    def attach_guest_tools_iso(self):
        """Genera la ISO de Guest Tools si falta, y la adjunta como CD/DVD
        a la VM seleccionada. La creación de la ISO corre en segundo plano
        (puede tardar 1-2 segundos); el adjuntado se hace en el hilo principal
        porque toca widgets y archivos de configuración."""
        if not self.current_vm_dir:
            QMessageBox.information(self, self.tr("Guest Tools"), self.tr("Selecciona (o crea) una VM primero."))
            return

        folder = self._guest_tools_dir()
        iso_path = os.path.join(folder, GUEST_TOOLS_ISO_NAME)

        # Caso rápido: la ISO ya existe y no hay nada que generar.
        if os.path.isfile(iso_path):
            self._attach_guest_tools_iso_to_vm(iso_path)
            return

        # Caso general: crear la ISO en segundo plano y adjuntar al terminar.
        os.makedirs(folder, exist_ok=True)

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit("==> Creando ISO de Guest Tools…")
            progress_emit(-1, self.tr("Creando ISO de Guest Tools…"))
            create_guest_tools_iso(iso_path)
            log_emit(f"==> ISO creada: {iso_path}")
            progress_emit(100, "ISO creada.")
            return iso_path

        def _on_success(path):
            self._attach_guest_tools_iso_to_vm(path)

        self.run_async(
            _work,
            self.tr("Guest Tools — Adjuntar a la VM"),
            on_success=_on_success,
            on_error=lambda e: self._show_selectable_error(
                self.tr("Guest Tools"), self.tr("No se pudo crear ni adjuntar la ISO.\n\n{0}").format(e)
            ),
            cancelable=False,
            show_log=True,
            subtitle=self.tr("Se creará la ISO y se adjuntará como CD/DVD a esta VM."),
        )

    def _attach_guest_tools_iso_to_vm(self, iso_path):
        """Lógica real del adjuntado. Se ejecuta en el hilo principal."""
        if not self.current_vm_dir:
            return
        try:
            devices = self._storage_devices_all(self.current_vm_dir)
            if any(d.get("path") == iso_path for d in devices):
                QMessageBox.information(self, self.tr("Guest Tools"), self.tr("Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD."))
                return
            devices.append({
                "id": f"dev_{uuid.uuid4().hex[:8]}",
                "name": "Guest Tools",
                "path": iso_path,
                "device": "cdrom",
            })
            self._write_storage_devices(devices)
            if hasattr(self, "refresh_storage_ui"):
                self.refresh_storage_ui()
            if hasattr(self, "refresh_boot_order_choices"):
                self.refresh_boot_order_choices()
            if hasattr(self, "_update_manager_details"):
                self._update_manager_details()
            QMessageBox.information(
                self, self.tr("Guest Tools"),
                self.tr("ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\n"
                        "En el próximo arranque, dentro del guest: monta la unidad y ejecuta\n"
                        "INSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).")
            )
        except Exception as e:
            self._show_selectable_error(self.tr("Guest Tools"), self.tr("No se pudo adjuntar la ISO.\n\n{0}").format(e))


    def _guest_agent_socket_path(self):
        return os.path.join(self.current_vm_dir, "qga.sock") if self.current_vm_dir else ""

    def test_guest_agent(self):
        path=self._guest_agent_socket_path()
        if not path or not os.path.exists(path):
            self.guest_agent_status_label.setText(self.tr("Estado: canal no disponible. Enciende la VM con Guest Agent activado."))
            return
        if getattr(self, "_qga_test_thread", None) is not None and self._qga_test_thread.isRunning():
            return
        self.guest_agent_status_label.setText(self.tr("Estado: consultando al Guest Agent..."))

        def _work(_log_emit):
            return self._qga_request({"execute": "guest-info"}, timeout=3)

        thread = _BackgroundCallThread(_work, parent=self)

        def _on_done(result, error):
            if error is not None:
                self.guest_agent_status_label.setText(self.tr("Estado: sin respuesta del guest agent ({0}).").format(error))
            elif "return" in result:
                info = result.get("return") or {}
                ver = info.get("version") or self.tr("desconocida")
                self.guest_agent_status_label.setText(self.tr("Estado: QEMU Guest Agent responde correctamente (v{0}).").format(ver))
            else:
                self.guest_agent_status_label.setText(self.tr("Estado: QGA respondió con un error: {0}").format(result.get('error', result)))
            self._qga_test_thread = None

        thread.done_signal.connect(_on_done)
        self._qga_test_thread = thread
        thread.start()

    def refresh_guest_tools_ui(self):
        if not hasattr(self,"guest_agent_enabled"): return
        enabled=False
        try:
            if self.current_vm_dir:
                cfg=load_vm_config(self.current_vm_dir); enabled=bool((cfg.get("extra") or {}).get("guest_agent_enabled",False))
        except Exception: pass
        self.guest_agent_enabled.blockSignals(True); self.guest_agent_enabled.setChecked(enabled); self.guest_agent_enabled.blockSignals(False)
        if self.current_vm_dir and os.path.exists(self._guest_agent_socket_path()): self.guest_agent_status_label.setText(self.tr("Estado: canal QGA presente; pulsa Probar conexión."))
        else: self.guest_agent_status_label.setText(self.tr("Estado: canal QGA no activo en este momento."))

        # vm_config_save_cancel_v1_grupo_b_doc:
        # Este campo forma parte del "Grupo B" y se auto-guarda a
        # proposito: NO pasa por el modelo Guardar/Descartar del
        # "Grupo A" (vm_config_save_cancel_v1_*). Motivos:
        #   1. No tiene widget persistente en la pestana Configuracion
        #      VM (este ajuste vive en su propio dialogo o su propio
        #      panel).
        #   2. El usuario espera que un cambio aqui se aplique ya, sin
        #      un paso extra de "Guardar configuracion".
        #   3. Coherente con guest_agent_enabled y clipboard_mode, que
        #      estan en el mismo caso.
        # Si en el futuro se quisiera integrar en el modelo dirty,
        # habria que:
        #   - Darle un widget persistente en la pestana Configuracion VM,
        #   - Anadirlo a _collect_config_from_ui() y _load_config_comparable(),
        #   - Engancharlo a _wire_config_dirty_signals(),
        #   - Anadirlo a la lista de claves comparadas en _has_pending_changes().
    def save_guest_tools_settings(self):
        if not self.current_vm_dir: return
        cfg=load_vm_config(self.current_vm_dir); extra=cfg.get("extra") or {}; extra["guest_agent_enabled"]=self.guest_agent_enabled.isChecked()
        save_vm_config(self.current_vm_dir,cfg["name"],cfg["os_type"],cfg["ram"],cfg["cores"],cfg["disk_size"],cfg["disk_type"],cfg["disk_format"],cfg["disk_ext"],extra,cfg["firmware"],cfg["secure_boot"],cfg["tpm"],cfg["boot_device"],cfg["network_model"],cfg["audio_device"],cfg["network_mode"],cfg["network_interface"],cfg["network_count"],cfg["graphics_mode"],cfg["graphics_vram"],cfg["boot_order"],network_devices=cfg.get("network_devices",[]),passthrough_devices=cfg.get("passthrough_devices",[]),chipset=cfg.get("chipset","pc"))
        self.refresh_guest_tools_ui(); self._update_manager_details()

    def _shared_folders_data(self):
        if not self.current_vm_dir: return []
        try:
            d=load_vm_config(self.current_vm_dir); x=(d.get("extra") or {}).get("shared_folders",[]); return x if isinstance(x,list) else []
        except Exception: return []

    def refresh_shared_folders_ui(self):
        if not hasattr(self,"shared_folders_tree"): return
        self.shared_folders_tree.clear()
        mount_labels={"manual":self.tr("Manual"),"auto_start":self.tr("Automático al iniciar SO"),"auto_demand":self.tr("Automático bajo demanda")}
        for d in self._shared_folders_data():
            mount_mode=str(d.get("mount_mode","manual"))
            item=QTreeWidgetItem([str(d.get("host","")),str(d.get("guest","share")),str(d.get("method","auto")).upper(),mount_labels.get(mount_mode,mount_mode),self.tr("Solo lectura") if d.get("readonly") else self.tr("Lectura / escritura")]); item.setData(0,Qt.ItemDataRole.UserRole,d); self.shared_folders_tree.addTopLevelItem(item)
        self.refresh_clipboard_ui()
        self.refresh_guest_tools_ui()

    def _shared_folder_dialog(self,initial=None):
        initial=initial or {}; dlg=QDialog(self); dlg.setWindowTitle(self.tr("Carpeta compartida")); dlg.resize(680,300); form=QFormLayout(dlg)
        host=QLineEdit(initial.get("host","")); browse=QPushButton("📁"); row=QHBoxLayout(); row.addWidget(host); row.addWidget(browse); browse.clicked.connect(lambda: host.setText(QFileDialog.getExistingDirectory(self,self.tr("Seleccionar carpeta del host"),host.text() or os.path.expanduser("~")))); form.addRow(self.tr("Carpeta del host:"),row)
        guest=QLineEdit(initial.get("guest","share")); form.addRow(self.tr("Etiqueta / guest:"),guest)
        method=QComboBox(); [method.addItem(t,v) for t,v in ((self.tr("Automático"),"auto"),("VirtioFS","virtiofs"),("9p","9p"),("SMB","smb"))]; idx=method.findData(initial.get("method","auto")); method.setCurrentIndex(max(0,idx)); form.addRow(self.tr("Método:"),method)
        mount_mode=QComboBox(); [mount_mode.addItem(t,v) for t,v in ((self.tr("Manual"),"manual"),(self.tr("Automático al iniciar SO"),"auto_start"),(self.tr("Automático bajo demanda"),"auto_demand"))]; midx=mount_mode.findData(initial.get("mount_mode","manual")); mount_mode.setCurrentIndex(max(0,midx)); form.addRow(self.tr("Montaje en el guest:"),mount_mode)
        ro=QCheckBox(self.tr("Solo lectura")); ro.setChecked(bool(initial.get("readonly",False))); form.addRow(self.tr("Acceso:"),ro)
        note=QLabel(self.tr("La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.")); note.setWordWrap(True); note.setStyleSheet("color:#666;"); form.addRow("",note)
        buttons=QHBoxLayout(); ok=QPushButton(self.tr("Aceptar")); cancel=QPushButton(self.tr("Cancelar")); buttons.addStretch(); buttons.addWidget(ok); buttons.addWidget(cancel); form.addRow("",buttons); ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        if dlg.exec()!=QDialog.DialogCode.Accepted: return None
        hp=os.path.abspath(host.text().strip()) if host.text().strip() else ""
        if not hp or not os.path.isdir(hp): QMessageBox.warning(self,self.tr("Carpeta compartida"),self.tr("La carpeta del host no existe o no es un directorio.")); return None
        gp=re.sub(r"[^A-Za-z0-9_.-]","_",guest.text().strip() or "share")
        return {"host":hp,"guest":gp,"method":method.currentData(),"mount_mode":mount_mode.currentData(),"readonly":ro.isChecked()}

    def refresh_clipboard_ui(self):
        if not hasattr(self,"clipboard_mode"): return
        data=self._shared_folders_data()
        cfg={}
        try:
            if self.current_vm_dir:
                c=load_vm_config(self.current_vm_dir); cfg=(c.get("extra") or {}).get("clipboard",{}) or {}
        except Exception: cfg={}
        mode=str(cfg.get("mode","disabled")); idx=self.clipboard_mode.findData(mode); self.clipboard_mode.setCurrentIndex(max(0,idx))
        labels={"disabled":self.tr("Desactivado"),"host_to_guest":self.tr("Host → SO invitado"),"guest_to_host":self.tr("SO invitado → Host"),"bidirectional":self.tr("Bidireccional")}
        if mode == "disabled":
            detail = self.tr("No se añadirá ningún canal de clipboard.")
        elif self.current_vm_dir:
            os_type = load_vm_config(self.current_vm_dir).get("os_type", "linux")
            detail = (self.tr("QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.") if os_type in ("linux", "windows") else self.tr("macOS: integración de clipboard pendiente."))
        else:
            detail = self.tr("Selecciona una VM para comprobar la integración disponible.")
        _suffix = self.tr("Se activará automáticamente al iniciar la VM.") if mode != 'disabled' else self.tr("No se activa.")
        self.clipboard_status_label.setText(self.tr("Configuración actual: {0}. {1} {2}").format(labels.get(mode,mode), _suffix, detail))

        # vm_config_save_cancel_v1_grupo_b_doc:
        # Este campo forma parte del "Grupo B" y se auto-guarda a
        # proposito: NO pasa por el modelo Guardar/Descartar del
        # "Grupo A" (vm_config_save_cancel_v1_*). Motivos:
        #   1. No tiene widget persistente en la pestana Configuracion
        #      VM (este ajuste vive en su propio dialogo o su propio
        #      panel).
        #   2. El usuario espera que un cambio aqui se aplique ya, sin
        #      un paso extra de "Guardar configuracion".
        #   3. Coherente con guest_agent_enabled y clipboard_mode, que
        #      estan en el mismo caso.
        # Si en el futuro se quisiera integrar en el modelo dirty,
        # habria que:
        #   - Darle un widget persistente en la pestana Configuracion VM,
        #   - Anadirlo a _collect_config_from_ui() y _load_config_comparable(),
        #   - Engancharlo a _wire_config_dirty_signals(),
        #   - Anadirlo a la lista de claves comparadas en _has_pending_changes().
    def save_clipboard_settings(self):
        if not self.current_vm_dir: return
        cfg=load_vm_config(self.current_vm_dir); extra=cfg.get("extra") or {}; extra["clipboard"]={"mode":self.clipboard_mode.currentData()}
        save_vm_config(self.current_vm_dir,cfg["name"],cfg["os_type"],cfg["ram"],cfg["cores"],cfg["disk_size"],cfg["disk_type"],cfg["disk_format"],cfg["disk_ext"],extra,cfg["firmware"],cfg["secure_boot"],cfg["tpm"],cfg["boot_device"],cfg["network_model"],cfg["audio_device"],cfg["network_mode"],cfg["network_interface"],cfg["network_count"],cfg["graphics_mode"],cfg["graphics_vram"],cfg["boot_order"],network_devices=cfg.get("network_devices",[]),passthrough_devices=cfg.get("passthrough_devices",[]),chipset=cfg.get("chipset","pc")); self.refresh_clipboard_ui(); self._update_manager_details(); QMessageBox.information(self,self.tr("Clipboard"),self.tr("Configuración del clipboard guardada para esta VM."))

    def _set_shared_folders_data(self,data):
        if not self.current_vm_dir: return
        cfg=load_vm_config(self.current_vm_dir); extra=cfg.get("extra") or {}; extra["shared_folders"]=data
        save_vm_config(self.current_vm_dir,cfg["name"],cfg["os_type"],cfg["ram"],cfg["cores"],cfg["disk_size"],cfg["disk_type"],cfg["disk_format"],cfg["disk_ext"],extra,cfg["firmware"],cfg["secure_boot"],cfg["tpm"],cfg["boot_device"],cfg["network_model"],cfg["audio_device"],cfg["network_mode"],cfg["network_interface"],cfg["network_count"],cfg["graphics_mode"],cfg["graphics_vram"],cfg["boot_order"],network_devices=cfg.get("network_devices",[]),passthrough_devices=cfg.get("passthrough_devices",[]),chipset=cfg.get("chipset","pc")); self.refresh_shared_folders_ui(); self._update_manager_details()

    def add_shared_folder(self):
        d=self._shared_folder_dialog();
        if d is not None: self._set_shared_folders_data(self._shared_folders_data()+[d])

    def edit_shared_folder(self):
        item=self.shared_folders_tree.currentItem()
        if not item: return
        d=self._shared_folder_dialog(item.data(0,Qt.ItemDataRole.UserRole) or {});
        if d is not None:
            data=self._shared_folders_data(); row=self.shared_folders_tree.indexOfTopLevelItem(item)
            if 0<=row<len(data): data[row]=d; self._set_shared_folders_data(data)

    def delete_shared_folder(self):
        item=self.shared_folders_tree.currentItem()
        if not item: return
        data=self._shared_folders_data(); row=self.shared_folders_tree.indexOfTopLevelItem(item)
        if 0<=row<len(data): data.pop(row); self._set_shared_folders_data(data)

    def save_shared_folders(self):
        self._set_shared_folders_data(self._shared_folders_data()); QMessageBox.information(self,self.tr("Compartir"),self.tr("Configuración guardada. Se aplicará en el próximo arranque."))

