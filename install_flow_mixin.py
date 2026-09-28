"""Mixin: flujo de instalación/arranque — descarga del instalador,
preflight extendido (discos/carpetas rotas, orden de arranque riesgoso),
start_installation (arma InstallWorker y lo lanza) y el manejo de su
progreso/cancelación hasta que termina.
"""
import os
import re
import json
import shutil
import subprocess
import requests
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox, QApplication
from task_progress import TaskProgressDialog

import vm_config
from vm_config import load_vm_config, save_vm_config, get_os_profile
from iso_sources import get_latest_iso_url, get_latest_windows_iso_url
import iso_versions
import principal_cdrom
from host_deps import ensure_virtualization_dependencies, ensure_osx_kvm_present, find_ovmf_files
from workers import InstallWorker


class InstallFlowMixin:
    def _download_selected_os_installer_for_vm(self):
        os_type = self.combo_main_os.currentData()
        if os_type == "macos":
            raise RuntimeError("Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.")
        if os_type == "android":
            # Android-x86 / Bliss OS no tienen descarga automática: el
            # usuario aporta su propia ISO. Esta guarda existe por si
            # algún flujo futuro invoca este helper con una VM Android;
            # el flujo real de start_installation ya no lo hace.
            raise RuntimeError(
                "Android-x86 / Bliss OS no tienen descarga automática. "
                "Descarga la ISO desde https://www.android-x86.org/download.html "
                "o https://blissos.org/ y selecciónala en Plataforma → Android."
            )
        if os_type == "windows":
            win_ver = self.combo_win_ver.currentText()
            url = get_latest_windows_iso_url(win_ver)
            filename = os.path.join(self.current_vm_dir, "installer_" + re.sub(r"[^A-Za-z0-9_.-]", "_", win_ver.lower()) + ".iso")
        else:
            distro = self.combo_lin_distro.currentText()
            distro_version = self._selected_lin_version()
            url = iso_versions.get_iso_url(distro, distro_version)
            filename = os.path.join(self.current_vm_dir, "installer_" + re.sub(r"[^A-Za-z0-9_.-]", "_", distro.lower())
                                    + iso_versions.iso_filename_tag(distro_version) + ".iso")
        return self._download_file_to(url, filename)

    def _download_file_to(self, url, filename):
        self.log_message(f"==> Descargando: {url}")
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", "0") or 0)
        done = 0
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = int(done * 100 / total)
                    self.log_message(f"==> Descarga: {pct}%") if pct % 10 == 0 else None
                QApplication.processEvents()
        return filename

    def _prepare_macos_recovery_for_start(self, vm_dir):
        """Asegura que BaseSystem.img esté listo antes de arrancar macOS.

        Si no hay ningún medio configurado en Almacenamiento (ni Recovery
        ni un archivo existente), crea automáticamente la unidad Principal
        con source="recovery". Sin esto, una VM macOS nueva fallaría con
        "No existe BaseSystem.img".

        Si ya existe, actualiza las unidades CD/DVD con su ruta y devuelve
        la lista de dispositivos.

        Si no existe, muestra un diálogo modal de progreso y BLOQUEA el
        flujo hasta que la descarga termine. Al terminar, actualiza
        vm_config.ini y devuelve los dispositivos. El arranque continúa
        automáticamente: el usuario ya no tiene que volver a pulsar Iniciar.

        Devuelve la lista de dispositivos si todo va bien, o None si el
        usuario canceló la descarga (para abortar el arranque sin diálogo
        de error).
        """
        devices = self._storage_devices_all(vm_dir)
        recovery_devices = [d for d in devices if d.get("device") == "cdrom" and d.get("source") == "recovery"]
        # Auto-crear la unidad Principal con Recovery si no hay ningún medio.
        _has_medium = any(
            d.get("device") == "cdrom"
            and (d.get("source") == "recovery"
                 or (d.get("path") and os.path.isfile(d.get("path", ""))))
            for d in devices
        )
        if not _has_medium:
            import uuid as _uuid
            _entry = {
                "id": "dev_" + _uuid.uuid4().hex[:12],
                "name": "Principal",
                "path": "",
                "device": "cdrom",
                "principal": True,
                "source": "recovery",
            }
            _cds = [i for i, d in enumerate(devices) if d.get("device") == "cdrom"]
            devices.insert(_cds[0] if _cds else 0, _entry)
            recovery_devices = [_entry]
            _saved = self.current_vm_dir
            try:
                self.current_vm_dir = vm_dir
                self._write_storage_devices(devices)
            except Exception as _e:
                self.log_message(f"[AVISO] macOS: no se pudo guardar el medio Recovery: {_e}")
            finally:
                self.current_vm_dir = _saved
            self.log_message(
                "==> macOS: no había medio de instalación configurado; "
                "se usará System Recovery (descarga al iniciar)."
            )
        if not recovery_devices:
            return devices

        existing_img = os.path.join(vm_dir, "BaseSystem.img")
        legacy_img = os.path.join(vm_dir, "OSX-KVM", "BaseSystem.img")
        if not (os.path.isfile(existing_img) and os.path.getsize(existing_img) > 0) \
                and os.path.isfile(legacy_img) and os.path.getsize(legacy_img) > 0:
            existing_img = legacy_img

        if os.path.isfile(existing_img) and os.path.getsize(existing_img) > 0:
            self.log_message(f"==> System Recovery ya preparado: {existing_img}")
            for d in recovery_devices:
                d["path"] = existing_img
            self._write_storage_devices(devices)
            return devices

        # No existe: descargar bloqueando la UI.
        self.current_vm_dir = vm_dir
        self.log_message("==> System Recovery no encontrado. Iniciando descarga…")
        img = self._macos_recovery_download_blocking(vm_dir)
        if not img or not os.path.isfile(img) or os.path.getsize(img) == 0:
            # Cancelado por el usuario: abortar sin dialogo de error.
            self.log_message("[AVISO] Descarga de System Recovery cancelada.")
            return None

        self.log_message(f"==> System Recovery listo: {os.path.basename(img)}")
        for d in recovery_devices:
            d["path"] = img
        self._write_storage_devices(devices)
        return devices


    def _macos_recovery_download_blocking(self, vm_dir):
        """Descarga el Recovery de macOS bloqueando el hilo de la UI con
        un QEventLoop, mientras un QThread ejecuta la descarga real y un
        diálogo modal muestra el avance.

        Devuelve la ruta de BaseSystem.img al terminar, o None si el
        usuario cancela o si hay un error.
        """
        from PyQt6.QtCore import QEventLoop
        from PyQt6.QtWidgets import QApplication
        from task_progress import TaskProgressDialog
        from workers import _BackgroundCallThread

        product = self._macos_recovery_product()

        dlg = TaskProgressDialog(
            f"System Recovery de macOS — {product['name']}",
            self,
            cancelable=True,
            show_log=True,
            subtitle="La imagen se descarga y verifica directamente en la carpeta de la VM.",
        )
        dlg.set_progress(-1, "Iniciando descarga…")
        try:
            dlg.setModal(True)
        except Exception:
            pass

        result_holder = {"img": None, "error": None, "cancelled": False}
        loop = QEventLoop()

        def _work(log_emit, is_cancelled, progress_emit):
            return self._macos_recovery_impl(
                product, vm_dir, is_cancelled, progress_emit, log_emit,
            )

        thread = _BackgroundCallThread(_work, parent=self)
        thread.log_signal.connect(dlg.append_log)
        thread.progress_signal.connect(dlg.set_progress)

        def _on_done(result, error):
            if error is not None:
                result_holder["error"] = error
            else:
                result_holder["img"] = result
            try:
                if error is None:
                    dlg.finish(True, "Recovery preparado.")
                else:
                    dlg.finish(False, str(error))
            except Exception:
                pass
            loop.quit()

        thread.done_signal.connect(_on_done)

        def _on_cancel():
            result_holder["cancelled"] = True
            try:
                thread.request_cancel()
            except Exception:
                pass
            # No cerramos el dialog todavia: esperamos a que el thread
            # termine limpiamente para no dejar procesos huérfanos.

        try:
            dlg.canceled.connect(_on_cancel)
        except Exception:
            pass

        thread.start()
        try:
            dlg.show()
        except Exception:
            pass
        try:
            QApplication.processEvents()
        except Exception:
            pass
        loop.exec()
        try:
            thread.wait(3000)
        except Exception:
            pass

        if result_holder["cancelled"]:
            return None
        if result_holder["error"] is not None:
            self.log_message(f"[ERROR] Recovery: {result_holder['error']}")
            return None
        return result_holder["img"]


    def _preflight_check(self, os_type=None):
        """Comprobaciones rápidas previas al arranque; no modifica el host."""
        problems = []
        qemu = shutil.which("qemu-system-x86_64")
        if not qemu:
            problems.append("No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.")
        if not os.path.exists("/dev/kvm"):
            problems.append("/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.")
        elif not os.access("/dev/kvm", os.R_OK | os.W_OK):
            problems.append("El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.")
        if os_type != "macos" and getattr(self, "check_secure_boot", None) and self.check_secure_boot.isChecked():
            try:
                _sb_code, _sb_vars = find_ovmf_files(secure_boot=True)
            except Exception:
                _sb_code, _sb_vars = None, None
            if not (_sb_code and _sb_vars):
                problems.append("No se detectó un firmware OVMF conocido para Secure Boot.")

        if self.current_vm_dir and os.path.isdir(self.current_vm_dir):
            devices = self._storage_devices_all(self.current_vm_dir)

            # Discos/ISOs configurados cuyo archivo ya no existe: hoy esto solo
            # se descubre a mitad del script de arranque, enterrado en el log.
            for dev in devices:
                path = dev.get("path", "")
                if path and not os.path.exists(path):
                    etiqueta = dev.get("name") or dev.get("id") or path
                    problems.append(f"El dispositivo de almacenamiento '{etiqueta}' apunta a un archivo que ya no existe: {path}")

            # Carpetas compartidas cuyo directorio en el host desapareció.
            try:
                cfg = load_vm_config(self.current_vm_dir)
                folders = (cfg.get("extra") or {}).get("shared_folders", [])
                folders = folders if isinstance(folders, list) else []
            except Exception:
                folders = []
            for f in folders:
                host = f.get("host", "") if isinstance(f, dict) else ""
                if host and not os.path.isdir(host):
                    problems.append(f"La carpeta compartida '{f.get('guest', '?')}' apunta a una ruta del host que ya no existe: {host}")

            # Espacio libre en el disco donde vive la VM.
            try:
                free_bytes = shutil.disk_usage(self.current_vm_dir).free
                if free_bytes < 2 * 1024**3:
                    problems.append(f"Solo quedan {free_bytes / 1024**3:.1f} GB libres donde vive esta VM; puede fallar durante el uso.")
            except OSError:
                pass

            # Orden de arranque: CD/DVD antes que un disco que ya parece tener
            # un sistema instalado -> riesgo real de reinstalar por accidente
            # en vez de arrancar el sistema existente (nos pasó en esta app).
            boot_order = self._current_boot_order_tokens()
            if boot_order and boot_order[0].startswith("cdrom:") and any(t.startswith("disk:") for t in boot_order):
                by_id = {d.get("id"): d for d in devices}
                for token in boot_order:
                    if not token.startswith("disk:"):
                        continue
                    dev = by_id.get(token.split(":", 1)[1], {})
                    path = dev.get("path", "")
                    try:
                        size = os.path.getsize(path) if path and os.path.exists(path) else 0
                    except OSError:
                        size = 0
                    if size > 300 * 1024 * 1024:
                        problems.append(
                            "El orden de arranque prioriza el CD/DVD, pero el disco "
                            f"'{dev.get('name', path)}' ya tiene datos (~{size / 1024**3:.1f} GB). "
                            "Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo."
                        )
                        break

        return qemu, problems

    def start_installation(self):
        vm_name = self.input_vm_name.text().strip()
        if not vm_name:
            QMessageBox.warning(self, "Advertencia", "Debe indicar un nombre para la máquina virtual.")
            return
        if re.search(r'[\\/:*?"<>|]', vm_name):
            QMessageBox.warning(self, "Advertencia", 'El nombre no puede contener: \\ / : * ? " < > |')
            return
        if self._runtime_state(vm_name) != "stopped":
            QMessageBox.warning(
                self, "La VM ya está corriendo",
                f"'{vm_name}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco "
                "(dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\n"
                "Detén la VM actual antes de volver a iniciarla."
            )
            return

        os_type = self.combo_main_os.currentData()
        qemu_path, preflight_problems = self._preflight_check(os_type)
        if not qemu_path:
            QMessageBox.critical(self, "No se puede iniciar la VM", "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.")
            return
        if preflight_problems:
            details = "\n".join(f"• {item}" for item in preflight_problems)
            answer = QMessageBox.warning(self, "Revisión previa", details + "\n\n¿Deseas continuar de todos modos?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        ram = f"{self.slider_ram.value()}G"
        cores = str(self.slider_cores.value())
        firmware = self.combo_firmware.currentData()
        secure_boot = self.check_secure_boot.isChecked()
        tpm = self.check_tpm.isChecked()
        boot_order = self._current_boot_order_tokens() if self.current_vm_dir else ["cdrom", "disk", "network"]
        boot_device = "cdrom" if boot_order and boot_order[0] == "cdrom" else ("network" if boot_order and boot_order[0] == "network" else "disk")
        network_devices = self._network_devices() if hasattr(self, "network_devices_list") and self.network_devices_list.count() else []
        if hasattr(self, "check_no_network") and self.check_no_network.isChecked():
            network_devices = []

        # La red puede estar deshabilitada o todavía no tener adaptadores
        # configurados. No debemos acceder a network_devices[0] en ese caso.
        # Los valores por defecto se mantienen para el flujo de creación, pero
        # network_count=0 hace que QEMU no agregue ningún adaptador virtual.
        first_network = network_devices[0] if network_devices else {}
        network_model = first_network.get("model", "virtio-net-pci")
        network_mode = first_network.get("mode", "nat")
        network_interface = first_network.get("interface", "")
        network_count = len(network_devices)
        passthrough_devices = list(getattr(self, "_passthrough_saved", []))
        audio_device = self.combo_audio.currentData()
        graphics_mode = self.combo_graphics.currentData()
        graphics_vram = self.combo_graphics_vram.currentData()
        if os_type == "macos":
            # macOS/OSX-KVM utiliza siempre UEFI + OpenCore.
            firmware = "uefi"
            secure_boot = False
            tpm = False
            network_mode = "nat"
            network_interface = ""
            # macOS/OSX-KVM necesita una interfaz de red para el flujo normal.
            # Si el usuario no tenía adaptadores configurados, usamos e1000 como
            # valor seguro en lugar de acceder a network_devices[0].
            macos_network_model = first_network.get("model", "e1000")
            network_devices = [{"name":"Red 1","model":macos_network_model,"mode":"nat","interface":"","mac":""}]
            network_count = 1
            graphics_mode = "auto"
            graphics_vram = "256M"
            self.combo_firmware.setCurrentIndex(self.combo_firmware.findData("uefi"))
            self.check_secure_boot.setChecked(False)
            self.check_tpm.setChecked(False)
        elif os_type == "windows" and self.combo_win_ver.currentText() == "Windows 11":
            firmware = "uefi"
            secure_boot = True
            tpm = True
            self.combo_firmware.setCurrentIndex(self.combo_firmware.findData("uefi"))
            self.check_secure_boot.setChecked(True)
            self.check_tpm.setChecked(True)
        if secure_boot and firmware != "uefi":
            QMessageBox.warning(self, "Configuración incompatible", "Secure Boot requiere UEFI (OVMF).")
            return
        if tpm and os_type == "macos":
            QMessageBox.warning(self, "Configuración incompatible", "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.")
            return
        # Comprobar e instalar automáticamente las dependencias necesarias.
        # OVMF se necesita para UEFI/Secure Boot y swtpm para TPM 2.0.
        need_ovmf = firmware == "uefi"
        need_swtpm = tpm
        if need_ovmf or need_swtpm:
            try:
                self.log_message("==> Comprobando dependencias de UEFI/TPM...")
                ensure_virtualization_dependencies(
                    need_ovmf=need_ovmf,
                    need_swtpm=need_swtpm,
                    need_secure_boot=secure_boot,
                    log_func=self.log_message,
                )
                self.log_message("==> Dependencias de virtualización listas.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Dependencias faltantes",
                    f"No se pudieron preparar automáticamente las dependencias necesarias.\n\n{e}"
                )
                return

        disk = getattr(self, "disk_size_setting", "128G")
        disk_type = getattr(self, "disk_type_setting", "dynamic")
        disk_format = getattr(self, "disk_format_setting", "qcow2")
        disk_ext = getattr(self, "disk_ext_setting", "img" if disk_format == "raw" else disk_format)
        format_data = (disk_format, disk_ext)

        vm_dir = os.path.join(vm_config.BASE_VM_DIR, vm_config.vm_folder_name(vm_name))
        # Si ya hay una VM seleccionada/provisional con este mismo nombre (p. ej. creada
        # al añadir almacenamiento antes de iniciar), reutilizar SU carpeta en lugar de
        # crear otra distinta.
        _cur = self.current_vm_dir
        if _cur and os.path.isdir(_cur):
            try:
                if load_vm_config(_cur).get("name") == vm_name:
                    vm_dir = _cur
            except Exception:
                pass
        os.makedirs(vm_dir, exist_ok=True)
        config_path = os.path.join(vm_dir, "vm_config.ini")

        # System Recovery de macOS se descarga al comenzar el arranque, no al crear
        # la unidad óptica. Esto mantiene la configuración rápida y evita una descarga
        # que el usuario quizá nunca llegue a utilizar.
        if os_type == "macos":
            try:
                _rec_result = self._prepare_macos_recovery_for_start(vm_dir)
                if _rec_result is None:
                    # El usuario cancelo la descarga del Recovery: abortar
                    # sin dialogo de error.
                    return
            except Exception as e:
                QMessageBox.critical(self, "System Recovery de macOS",
                                     f"No se pudo preparar System Recovery antes de iniciar la VM.\n\n{e}")
                return

        # Si el usuario ya creó un SATA/NVMe desde Almacenamiento, ese disco es el
        # disco de la VM y no se crea además un vm_disk genérico.
        skip_disk_create = False
        disk_path = None
        if os_type == "macos":
            # macOS sigue el modelo de OSX-KVM: usa un disco dedicado
            # (mac_hdd_ng.qcow2, QCOW2) para el sistema. NO reutiliza
            # storage_devices, porque el BaseSystem.img (medio de
            # instalacion, RAW) NO es un disco de sistema valido: si se
            # intenta usar como MacHDD, QEMU falla con:
            #   "Image is not in qcow2 format"
            disk_path = os.path.join(vm_dir, "mac_hdd_ng.qcow2")
            skip_disk_create = os.path.isfile(disk_path)
            if skip_disk_create:
                try:
                    info_res = subprocess.run(
                        ["qemu-img", "info", "--output=json", disk_path],
                        capture_output=True, text=True, timeout=10, check=True,
                    )
                    info_d = json.loads(info_res.stdout)
                    v_size = int(info_d.get("virtual-size", 0) or 0)
                    disk = f"{v_size / 1024**3:.0f}G" if v_size else "128G"
                except Exception:
                    disk = "128G"
                self.log_message(
                    f"==> macOS: disco del sistema existente: "
                    f"mac_hdd_ng.qcow2 ({disk})"
                )
            else:
                disk = "128G"
                self.log_message(
                    f"==> macOS: se creara mac_hdd_ng.qcow2 ({disk} QCOW2) "
                    f"en la primera ejecucion."
                )
            disk_format = "qcow2"
            disk_ext = "qcow2"
            disk_type = "dynamic"
            format_data = ("qcow2", "qcow2")
        else:
            try:
                storage_entries = self._storage_entries_with_types(vm_dir)
            except Exception:
                storage_entries = []
            preferred = next(((n, t, p) for n, t, p in storage_entries
                              if t in ("sata", "nvme") and os.path.isfile(p)), None)
            if preferred:
                _, preferred_type, preferred_path = preferred
                disk_path = os.path.abspath(preferred_path)
                skip_disk_create = True
                try:
                    info_res = subprocess.run(["qemu-img", "info", "--output=json", disk_path], capture_output=True, text=True, timeout=10, check=True)
                    info = json.loads(info_res.stdout)
                    disk_format = info.get("format", disk_format)
                    virtual_size = int(info.get("virtual-size", 0) or 0)
                    if virtual_size:
                        disk = f"{virtual_size / 1024**3:.1f}G"
                    disk_ext = "img" if disk_format == "raw" else disk_format
                    format_data = (disk_format, disk_ext)
                except Exception:
                    pass
                self.log_message(f"==> Usando el almacenamiento creado por el usuario como disco principal: {os.path.basename(disk_path)}")
            else:
                disk_path = os.path.join(vm_dir, f"vm_disk.{format_data[1]}")
        if (not skip_disk_create) and os.path.isfile(config_path) and os.path.isfile(disk_path):
            old = load_vm_config(vm_dir)
            same_spec = (
                old["disk_size"] == disk
                and old["disk_type"] == disk_type
                and old["disk_format"] == format_data[0]
            )
            if same_spec:
                skip_disk_create = True
                self.log_message(f"==> Disco existente compatible para '{vm_name}' — se reutilizará sin recrear.")
            else:
                resp = QMessageBox.question(
                    self,
                    "Disco existente con otra configuración",
                    f"Ya existe un disco para '{vm_name}' con "
                    f"{old['disk_size']} / {old['disk_type']} / {old['disk_format']}, "
                    f"distinto a lo solicitado ({disk} / {disk_type} / {format_data[0]}).\n\n"
                    "¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n"
                    "(\"No\" conserva el disco existente tal como está.)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if resp == QMessageBox.StandardButton.Yes:
                    os.remove(disk_path)
                    skip_disk_create = False
                else:
                    skip_disk_create = True
                    disk, disk_type = old["disk_size"], old["disk_type"]
                    format_data = (old["disk_format"], old["disk_ext"])

        self.disk_size_setting = disk
        self.disk_type_setting = disk_type
        self.disk_format_setting = format_data[0]
        self.disk_ext_setting = format_data[1]
        # 'is_new_vm' distingue una VM que se guarda por primera vez (todavía sin
        # vm_config.ini) de una que ya existía; solo en la primera forzamos el
        # orden de arranque para anteponer la unidad Principal.
        is_new_vm = not os.path.isfile(config_path)

        # Conservar datos de almacenamiento ya creados antes de guardar la configuración
        # general. La versión anterior sobrescribía [extra] y hacía desaparecer las unidades
        # recién creadas al iniciar la VM.
        extra_params = {}
        if os.path.isfile(config_path):
            try:
                existing_cfg = load_vm_config(vm_dir)
                old_extra = existing_cfg.get("extra") or {}
                if isinstance(old_extra, dict):
                    extra_params.update(old_extra)
            except Exception:
                pass
        if self.current_vm_dir == vm_dir:
            try:
                current_storage = self._storage_devices_all(vm_dir)
                if current_storage:
                    extra_params["storage_devices"] = current_storage
            except Exception:
                pass
        if hasattr(self,"shared_folders_tree") and self.current_vm_dir == vm_dir:
            extra_params["shared_folders"] = self._shared_folders_data()
        if hasattr(self,"guest_agent_enabled") and self.current_vm_dir == vm_dir:
            extra_params["guest_agent_enabled"] = self.guest_agent_enabled.isChecked()
        # Dispositivo de señalización (ratón/teclado) elegido en Dispositivos.
        if hasattr(self, "combo_pointer"):
            extra_params["pointer_device"] = self.combo_pointer.currentData() or "auto"
        # Persistir la preferencia de consola VNC embebida para esta VM.
        if hasattr(self, "check_vnc_embedded"):
            extra_params["vnc_embedded"] = self.check_vnc_embedded.isChecked()
        profile_version=self.combo_macos_ver.currentText() if os_type=="macos" else (self.combo_win_ver.currentText() if os_type=="windows" else self.combo_lin_distro.currentText())
        extra_params["os_profile"]=get_os_profile(os_type,profile_version,profile_version if os_type=="linux" else "")
        if os_type == "macos":
            if not os.path.isdir("OSX-KVM"):
                QMessageBox.critical(self, "Error", "No se encuentra la carpeta 'OSX-KVM'.")
                return
            extra_params["os_choice"] = self.os_options[self.combo_macos_ver.currentIndex()][1]
            extra_params["osx_kvm_source"] = os.path.abspath("OSX-KVM")
            # La fuente de instalación se lee desde la unidad CD/DVD
            # "Principal". Si tiene source="recovery", se descarga el
            # Recovery al iniciar; si tiene un path de archivo, se usa
            # ese archivo (BaseSystem.img o .dmg con dmg2img).
            # La descarga del Recovery en sí la gestiona
            # _prepare_macos_recovery_for_start, que corre antes de este
            # bloque. Ver ese método para el auto-creado de la unidad.
        elif os_type == "windows":
            auto_detect_win = self.check_win_auto.isChecked()
            iso = self.input_win_iso.text().strip()

            # Si el CD/DVD fue configurado como "Descargar instalador automáticamente",
            # la ISO todavía no existe y se descargará al pulsar Iniciar. En ese caso
            # no debemos exigir una ruta local en esta etapa.
            installer_selected = False
            storage_iso = ""
            try:
                configured_storage = self._storage_devices_all(vm_dir)
                for d in configured_storage:
                    if d.get("device") != "cdrom":
                        continue
                    source = str(d.get("source") or "")
                    path = os.path.abspath(d.get("path")) if d.get("path") else ""
                    # Una unidad marcada como instalador y sin ruta todavía debe descargar.
                    if source == "installer" and not (path and os.path.isfile(path)):
                        installer_selected = True
                    # Si el usuario seleccionó manualmente una ISO existente, esa ruta manda,
                    # aunque una configuración antigua conserve source=installer por error.
                    elif path and os.path.isfile(path):
                        storage_iso = path
            except Exception:
                configured_storage = []

            # Prioridad para Windows: ISO indicada en CD/DVD > ISO del formulario > descarga.
            if storage_iso:
                iso = storage_iso
                installer_selected = False

            if not installer_selected and not auto_detect_win and (not iso or not os.path.isfile(iso)):
                QMessageBox.warning(self, "Advertencia", "Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.")
                return
            extra_params["win_ver"] = self.combo_win_ver.currentText()
            # Si el CD/DVD tiene una ISO local válida, QEMU usará esa ISO y no habrá descarga.
            # Solo InstallWorker descargará cuando source=installer y todavía no exista una ruta.
            extra_params["auto_detect"] = bool(auto_detect_win and not installer_selected and not storage_iso)
            extra_params["iso_path"] = iso if not installer_selected else ""
        elif os_type == "android":
            # Android-x86 / Bliss OS. La ISO se configura en la unidad
            # CD/DVD "Principal" (Configuración → Almacenamiento). Aquí
            # solo leemos esa unidad y validamos que apunte a un archivo.
            android_iso = ""
            try:
                _devices_now = self._storage_devices_all(vm_dir)
                _p = principal_cdrom.find_principal(_devices_now)
                if _p is not None:
                    _p_path = _p.get("path") or ""
                    if _p_path and os.path.isfile(_p_path):
                        android_iso = _p_path
            except Exception:
                pass
            if not android_iso:
                QMessageBox.warning(
                    self, "Android",
                    "Debes configurar la ISO de Android-x86 o Bliss OS en "
                    "Configuración → Almacenamiento → CD / DVD." + chr(92) + "n" + chr(92) + "n" +
                    "Descárgala de:" + chr(92) + "n" +
                    "  • https://www.android-x86.org/download.html" + chr(92) + "n" +
                    "  • https://blissos.org/" + chr(92) + "n" + chr(92) + "n" +
                    "Añade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente»."
                )
                return
            extra_params["android_iso"] = android_iso
            self.log_message(
                f"==> Android: ISO de instalación: {os.path.basename(android_iso)}"
            )
        else:  # Linux
            distro = self.combo_lin_distro.currentText()
            extra_params["distro"] = distro
            lin_choice = self._selected_lin_version()
            extra_params["distro_version"] = lin_choice
            extra_params["iso_choice"] = lin_choice
            # Crea/actualiza la unidad óptica 'Principal' con la elección hecha en
            # Versión ISO (descarga automática, una versión concreta, o la ISO
            # propia si se eligió 'Ninguna').
            own_iso = self._own_lin_iso_path() if hasattr(self, "_own_lin_iso_path") else ""
            _devices_for_principal = extra_params.get("storage_devices", []) or []
            principal_cdrom.apply_choice(_devices_for_principal, "linux", lin_choice,
                                         profile=distro, own_iso=own_iso, new_vm=is_new_vm)
            extra_params["storage_devices"] = _devices_for_principal

        if is_new_vm and os_type in ("linux", "android"):
            # VM nueva: la unidad Principal (recién creada arriba) debe quedar
            # primera en el orden de arranque, sin importar lo que trajera 'boot_order'.
            boot_order = principal_cdrom.boot_first(
                boot_order or ["cdrom", "disk", "network"], extra_params.get("storage_devices", []))
        try:
            boot_order = boot_order if boot_order else ["cdrom", "disk", "network"]
            save_vm_config(vm_dir, vm_name, os_type, ram, cores, disk, disk_type, format_data[0], format_data[1], extra_params, firmware, secure_boot, tpm, boot_device, network_model, audio_device, network_mode, network_interface, network_count, graphics_mode, graphics_vram, boot_order, network_devices=network_devices, passthrough_devices=passthrough_devices, chipset=self.combo_chipset.currentData())
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar configuración",
                                  f"No se pudo guardar vm_config.ini para '{vm_name}': {e}")
            return
        self.current_vm_dir = vm_dir
        self.refresh_vm_list(select_name=vm_name)
        self.refresh_boot_order_choices()

        pci_unbound=[d for d in passthrough_devices if d.get("kind")=="pci" and d.get("driver") and d.get("driver")!="vfio-pci"]
        usb_selected=[d for d in passthrough_devices if d.get("kind")=="usb"]
        if usb_selected:
            try:
                self._prepare_usb_passthrough(usb_selected)
                for d in usb_selected:
                    self.log_message(f"[USB] {self._usb_runtime_diagnostics(d)}")
            except Exception as e:
                self._show_selectable_error("No se puede preparar el passthrough USB",
                    f"La VM no se iniciará hasta resolver el acceso al USB.\n\n{e}\n\n"
                    "No se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.")
                self.btn_start.setEnabled(True)
                return
        if pci_unbound:
            self.log_message("[AVISO] Hay dispositivos PCI seleccionados que siguen usando el driver del host. QEMU/VFIO puede requerir que se enlacen a vfio-pci y que IOMMU esté activo antes de iniciar la VM.")
        self.btn_start.setEnabled(False)
        extra_params["chipset"] = self.combo_chipset.currentData()
        extra_params["cpu_model"] = self.combo_cpu_model.currentData() if hasattr(self, "combo_cpu_model") else extra_params.get("cpu_model", "auto")
        self.log_message(f"==> Iniciando máquina virtual '{vm_name}' [{os_type.upper()}], Firmware: {firmware.upper()}, Secure Boot: {'ON' if secure_boot else 'OFF'}, TPM 2.0: {'ON' if tpm else 'OFF'}, Arranque: {boot_device}, Redes: {len(network_devices)}, Audio: {audio_device}, Gráficos: {graphics_mode}/{graphics_vram}, RAM: {ram}, CPUs: {cores}, CPU modelo: {extra_params.get('cpu_model','auto')}, Passthrough: {len(passthrough_devices)}...")

        self.worker = InstallWorker(os_type, ram, cores, disk, disk_type, format_data[0], format_data[1],
                                     firmware, secure_boot, tpm, boot_device, network_model, audio_device, network_mode, network_interface, network_count, graphics_mode, graphics_vram, extra_params, vm_dir, disk_path, skip_disk_create, boot_order, network_devices, passthrough_devices)
        self.worker.log_signal.connect(self.log_message)
        self.worker.progress_signal.connect(self._update_installer_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        # El diálogo de descarga se crea de forma perezosa.
        # Si no hay una descarga real pendiente, NO se muestra ninguna ventana
        # de "Preparando la descarga" al iniciar una VM.
        self._installer_progress_dialog = None
        self.worker.start()
        # Integración Host ↔ Guest: el dispositivo VirtioFS se conecta al arrancar.
        # Si una carpeta está en "Automático al iniciar SO", intentamos configurar
        # /etc/fstab mediante QEMU Guest Agent una vez que el guest haya terminado de arrancar.
        try:
            auto_start = any(
                isinstance(d, dict) and str(d.get("mount_mode","manual")).lower() == "auto_start"
                and str(d.get("method") or "auto").lower() in ("auto", "virtiofs")
                for d in self._shared_folders_data()
            )
            has_shared = any(
                isinstance(d, dict) and str(d.get("method") or "auto").lower() in ("auto", "virtiofs")
                for d in self._shared_folders_data()
            )
            if os_type == "linux" and auto_start:
                QTimer.singleShot(7000, self._configure_linux_shared_automount)
            elif os_type == "linux" and has_shared:
                QTimer.singleShot(2500, self._show_shared_mount_hint)
        except Exception:
            pass

    def _cancel_installer_download(self):
        worker = getattr(self, "worker", None)
        if worker is None or not worker.isRunning():
            return
        self.log_message("==> Cancelando descarga…")
        worker.request_cancel()
        dialog = getattr(self, "_installer_progress_dialog", None)
        if dialog is not None:
            dialog._cancel_btn.setEnabled(False)
            dialog._cancel_btn.setText("Cancelando…")

    def _update_installer_progress(self, percent, text):
        dialog = getattr(self, "_installer_progress_dialog", None)
        if dialog is None:
            dialog = TaskProgressDialog(
                "Instalador del sistema operativo",
                self,
                cancelable=True,
                show_log=True,
                subtitle="La descarga se realiza dentro de la carpeta de la VM.",
            )
            dialog.canceled.connect(self._cancel_installer_download)
            # Conectar el log del worker a la consola del diálogo también,
            # para que el usuario vea el progreso en vivo dentro del diálogo
            # (además de en la consola principal de la app).
            worker = getattr(self, "worker", None)
            if worker is not None:
                try:
                    worker.log_signal.connect(dialog.append_log)
                except Exception:
                    pass
            self._installer_progress_dialog = dialog
        dialog.set_progress(percent, text)

    def on_worker_finished(self, code):
        dialog = getattr(self, "_installer_progress_dialog", None)
        if dialog is not None:
            if code == 0:
                dialog.finish(True, "Máquina virtual iniciada.")
            elif code == 2:
                dialog.finish(False, "Descarga cancelada por el usuario.")
            else:
                dialog.finish(False, "QEMU terminó con error. Revisa la consola de progreso.")
            dialog.deleteLater()
            self._installer_progress_dialog = None
        self.btn_start.setEnabled(True)
