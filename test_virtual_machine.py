# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

r"""
Tests automatizados para las funciones más críticas y frágiles de
virtual_machine.py: construcción de argumentos de QEMU (gráficos, clipboard,
carpetas compartidas) y fusión de configuración guardada.

Estas funciones son "puras" en su mayoría (config -> string de argumentos),
lo que las hace ideales para tests unitarios baratos. El objetivo principal
es que un cambio futuro no vuelva a introducir bugs como los ya corregidos:
- El regex del trap de limpieza con doble backslash (\\s en vez de \s).
- virtio-gpu/vmware/qxl sin salida VGA compatible bajo firmware UEFI.
- Un solo virtiofsd roto abortando el arranque completo de la VM (exit 1).
- Un virtiofsd huérfano de un intento anterior bloqueando el siguiente.

Ejecutar con:
    QT_QPA_PLATFORM=offscreen python3 -m unittest test_virtual_machine -v
"""
import os
import re
import sys
import time
import shutil
import tempfile
import subprocess
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv[:1])

import virtual_machine as vm
import vm_config
import workers


def make_worker(**overrides):
    """Crea un InstallWorker con valores por defecto razonables, para no
    repetir en cada test los ~20 parámetros posicionales del constructor."""
    tmp_dir = tempfile.mkdtemp(prefix="vmtest_")
    defaults = dict(
        os_type="linux", ram="4G", cores=2, disk_size="40G", disk_type="qcow2",
        disk_format="qcow2", disk_ext=".qcow2", firmware="bios", secure_boot=False,
        tpm=False, boot_device="disk", network_model="virtio-net-pci",
        audio_device="intel-hda", network_mode="nat", network_interface="",
        network_count=1, graphics_mode="auto", graphics_vram="256M",
        extra_params={}, vm_dir=tmp_dir, disk_path=os.path.join(tmp_dir, "disk.qcow2"),
    )
    defaults.update(overrides)
    return vm.InstallWorker(**defaults)


class GraphicsArgsTests(unittest.TestCase):
    def test_headless(self):
        w = make_worker(graphics_mode="none")
        args, note = w._graphics_args()
        self.assertEqual(args, "-display none -vga none")
        self.assertIn("headless", note.lower())

    def test_macos_delegates_to_opencore(self):
        w = make_worker(os_type="macos")
        args, note = w._graphics_args()
        self.assertEqual(args, "")
        self.assertIn("OSX-KVM", note)

    def test_windows_auto_prefers_std_vga(self):
        w = make_worker(os_type="windows", graphics_mode="auto")
        args, note = w._graphics_args()
        self.assertIn("-vga std", args)

    def test_linux_auto_without_host_qemu_falls_back_safely(self):
        # Sin qemu-system-x86_64 en el host (como en este entorno de test),
        # toda detección de capacidades debe fallar cerrado y caer a VGA
        # estándar, nunca lanzar una excepción.
        w = make_worker(os_type="linux", graphics_mode="auto")
        with mock.patch.object(vm.shutil, "which", return_value=None):
            args, note = w._graphics_args()
        self.assertEqual(args, "")
        self.assertIn("VGA estándar", note)

    def test_qxl_uefi_emits_gop_warning(self):
        # Regresión: antes esta combinación podía dejar la pantalla en negro
        # sin ningún aviso previo.
        w = make_worker(graphics_mode="qxl", firmware="uefi")
        logs = []
        w.log_signal.connect(logs.append)
        with mock.patch.object(vm.shutil, "which", return_value=None):
            w._graphics_args()
        self.assertTrue(any("GOP" in m for m in logs), f"Debía avisar sobre GOP; logs={logs}")

    def test_vmware_uefi_emits_gop_warning(self):
        w = make_worker(graphics_mode="vmware", firmware="uefi")
        logs = []
        w.log_signal.connect(logs.append)
        args, note = w._graphics_args()
        self.assertTrue(any("GOP" in m for m in logs), f"Debía avisar sobre GOP; logs={logs}")
        self.assertIn("-vga vmware", args)

    def test_vmware_bios_no_warning(self):
        # El aviso es específico de UEFI; con BIOS clásico no debe dispararse.
        w = make_worker(graphics_mode="vmware", firmware="bios")
        logs = []
        w.log_signal.connect(logs.append)
        w._graphics_args()
        self.assertFalse(any("GOP" in m for m in logs))

    def test_linux_gl_modes_use_vga_compatible_device(self):
        # Regresión directa del bug de "Guest has not initialized the display":
        # el dispositivo con aceleración 3D debe ser el compatible con VGA
        # (virtio-vga-gl), no el que carece de modo de texto heredado
        # (virtio-gpu-gl), o UEFI/GRUB no pueden dibujar nada antes de que el
        # kernel cargue su driver.
        # console_mode=native para no activar la rebaja virgl→virtio
        # que se aplica cuando la consola va por socket.
        w = make_worker(graphics_mode="virgl", firmware="uefi",
                        extra_params={"console_mode": "native"})
        with mock.patch.object(w, "_qemu_supports", return_value=True), \
             mock.patch.object(w, "_virgl_available", return_value=True), \
             mock.patch.object(w, "_display_opengl_args", return_value=("-display gtk,gl=on", True)):
            args, note = w._graphics_args()
        self.assertIn("virtio-vga-gl", args)
        self.assertNotIn("virtio-gpu-gl", args)


class ClipboardTests(unittest.TestCase):
    def test_disabled_by_default(self):
        w = make_worker(extra_params={})
        self.assertFalse(w._clipboard_enabled())

    def test_any_non_disabled_mode_enables_it(self):
        # Regresión: ya no existe el checkbox "Activar automáticamente"; el
        # modo por sí solo decide si el clipboard se activa al iniciar la VM.
        for mode in ("host_to_guest", "guest_to_host", "bidirectional"):
            w = make_worker(extra_params={"clipboard": {"mode": mode}})
            self.assertTrue(w._clipboard_enabled(), f"mode={mode} debería activar el clipboard")

    def test_disabled_mode_is_off(self):
        w = make_worker(extra_params={"clipboard": {"mode": "disabled"}})
        self.assertFalse(w._clipboard_enabled())

    def test_macos_never_gets_clipboard_args(self):
        w = make_worker(os_type="macos", extra_params={"clipboard": {"mode": "bidirectional"}})
        self.assertEqual(w._clipboard_qemu_args(), ("", ""))

    def test_enabled_without_host_qemu_raises_clear_error(self):
        w = make_worker(extra_params={"clipboard": {"mode": "bidirectional"}})
        with mock.patch.object(vm.shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError):
                w._clipboard_qemu_args()


class SharedFolderArgsTests(unittest.TestCase):
    def setUp(self):
        self.host_dir = tempfile.mkdtemp(prefix="vmtest_share_")
        self.addCleanup(shutil.rmtree, self.host_dir, ignore_errors=True)

    def test_9p_folder_produces_virtfs_arg(self):
        w = make_worker(extra_params={"shared_folders": [
            {"host": self.host_dir, "guest": "share", "method": "9p", "readonly": False}
        ]})
        qemu, start, cleanup = w._shared_folder_args()
        self.assertIn("-virtfs local", qemu)
        self.assertIn("mount_tag=share", qemu)

    def test_virtiofs_missing_binary_is_skipped_not_fatal(self):
        w = make_worker(extra_params={"shared_folders": [
            {"host": self.host_dir, "guest": "share", "method": "virtiofs", "readonly": False}
        ]})
        logs = []
        w.log_signal.connect(logs.append)
        with mock.patch.object(workers, "find_virtiofsd", return_value=None):
            qemu, start, cleanup = w._shared_folder_args()
        self.assertTrue(any("virtiofsd" in m.lower() for m in logs))
        self.assertNotIn("charfs0", qemu)

    def test_virtiofs_start_script_no_longer_uses_exit_on_failure(self):
        # Regresión directa: un virtiofsd roto ya NO debe poder abortar el
        # resto del script de arranque con 'exit 1'.
        w = make_worker(extra_params={"shared_folders": [
            {"host": self.host_dir, "guest": "share", "method": "virtiofs", "readonly": False}
        ]})
        with mock.patch.object(workers, "find_virtiofsd", return_value="/bin/false"):
            qemu, start, cleanup = w._shared_folder_args()
        self.assertNotIn("exit 1", start)

    def test_virtiofs_start_script_is_valid_bash_and_survives_failure(self):
        w = make_worker(extra_params={"shared_folders": [
            {"host": self.host_dir, "guest": "share", "method": "virtiofs", "readonly": False}
        ]})
        with mock.patch.object(workers, "find_virtiofsd", return_value="/bin/false"):
            qemu, start, cleanup = w._shared_folder_args()
        script = "#!/bin/bash\nset -e\nEXTRA_FS_ARGS=()\n" + start + "\necho FIN\n"
        proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("FIN", proc.stdout, "El script debe llegar al final aunque virtiofsd falle")

    def test_virtiofs_kills_orphan_from_previous_run(self):
        # Regresión directa: un virtiofsd huérfano de un intento anterior
        # (guardado en virtiofs-0.pid) debe matarse antes de reintentar.
        w = make_worker(extra_params={"shared_folders": [
            {"host": self.host_dir, "guest": "share", "method": "virtiofs", "readonly": False}
        ]})
        with mock.patch.object(workers, "find_virtiofsd", return_value="/bin/true"):
            qemu, start, cleanup = w._shared_folder_args()

        proc = subprocess.Popen(["sleep", "300"])
        pidfile = os.path.join(w.vm_dir, "virtiofs-0.pid")
        with open(pidfile, "w") as f:
            f.write(str(proc.pid))
        try:
            script = "#!/bin/bash\nset -e\nEXTRA_FS_ARGS=()\n" + start + "\n"
            subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=10)
            proc.poll()
            self.assertIsNotNone(proc.returncode, "El proceso huérfano debía haber sido eliminado")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


class TrapCleanupRegressionTests(unittest.TestCase):
    def test_trap_regex_matches_whitespace_not_literal_backslash(self):
        # Bug histórico: r"...(\\s*)...EXIT\\s*$" (doble backslash) nunca
        # hacía match porque buscaba un '\' literal en el script, no espacios.
        pattern = re.compile(r"(?m)^(\s*)trap '(rm -f .*?)' EXIT\s*$")
        script = "set -e\n    trap 'rm -f /tmp/x.sock' EXIT\nqemu-system-x86_64 ...\n"
        self.assertIsNotNone(pattern.search(script))

    def test_insert_cleanup_trap_merges_into_existing_trap(self):
        w = make_worker()
        script = "set -e\n    trap 'rm -f /tmp/original.pflash' EXIT\nqemu-system-x86_64 ...\n"
        result = w._insert_cleanup_trap(script, "rm -f /tmp/virtiofs-0.sock")
        self.assertIn("rm -f /tmp/original.pflash; rm -f /tmp/virtiofs-0.sock", result)

    def test_insert_cleanup_trap_escapes_single_quotes_in_paths(self):
        # Ruta con comilla simple (caso límite real: "Virtual Machine's Folder").
        w = make_worker()
        script = "set -e\n    trap 'rm -f /tmp/original.pflash' EXIT\nqemu-system-x86_64 ...\n"
        cleanup = "rm -f '/tmp/Virtual Machine'\"'\"'s Folder/x.sock'"
        result = w._insert_cleanup_trap(script, cleanup)
        proc = subprocess.run(["bash", "-n"], input=result, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_insert_cleanup_trap_falls_back_when_pattern_not_found(self):
        # Regresión: si el trap original no tiene el formato esperado (p. ej.
        # el template cambia en el futuro), ya no se pierde la limpieza en
        # silencio; se agrega un trap de respaldo propio.
        w = make_worker()
        logs = []
        w.log_signal.connect(logs.append)
        script = "set -e\necho 'sin ningun trap reconocible aqui'\nqemu-system-x86_64 ...\n"
        result = w._insert_cleanup_trap(script, "rm -f /tmp/virtiofs-0.sock")
        self.assertIn("trap 'rm -f /tmp/virtiofs-0.sock' EXIT", result)
        self.assertTrue(any("respaldo" in m.lower() for m in logs))

    def test_insert_pre_qmp_args_reports_missing_marker(self):
        w = make_worker()
        script, found = w._insert_pre_qmp_args("qemu-system-x86_64 -m 4G &\n", "-chardev socket,id=x")
        self.assertFalse(found)

    def test_insert_pre_qmp_args_inserts_before_qmp(self):
        w = make_worker()
        script = '    -qmp unix:"/tmp/q.sock",server=on,wait=off &\n'
        result, found = w._insert_pre_qmp_args(script, "-chardev socket,id=x")
        self.assertTrue(found)
        self.assertIn("-chardev socket,id=x -qmp unix:", result)


class SaveVmConfigTests(unittest.TestCase):
    def test_storage_devices_survive_an_unrelated_save(self):
        vm_dir = tempfile.mkdtemp(prefix="vmtest_cfg_")
        self.addCleanup(shutil.rmtree, vm_dir, ignore_errors=True)
        vm.save_vm_config(vm_dir, "TestVM", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"storage_devices": [{"path": "disk0.qcow2"}]})
        # Un guardado posterior que no menciona storage_devices no debe borrarlo.
        vm.save_vm_config(vm_dir, "TestVM", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"clipboard": {"mode": "bidirectional"}})
        cfg = vm.load_vm_config(vm_dir)
        self.assertEqual(cfg["extra"].get("storage_devices"), [{"path": "disk0.qcow2"}])

    def test_merge_failure_is_logged_not_silent(self):
        # Regresión: antes este except era 'except Exception: pass'.
        vm_dir = tempfile.mkdtemp(prefix="vmtest_cfg2_")
        self.addCleanup(shutil.rmtree, vm_dir, ignore_errors=True)
        cfg_path = os.path.join(vm_dir, "vm_config.ini")
        with open(cfg_path, "w") as f:
            f.write("[extra]\ndata = {esto no es json valido\n")
        logs = []
        vm.save_vm_config(vm_dir, "TestVM", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"clipboard": {"mode": "bidirectional"}}, log_func=logs.append)
        self.assertTrue(any("fusionar" in m for m in logs), f"Debía loguear el fallo; logs={logs}")


class AppInstanceTests(unittest.TestCase):
    """Tests contra la ventana principal real (VirtualMachineManagerApp), instanciada
    bajo Qt en modo offscreen. Cubren las funciones de salud/diagnóstico y los
    chequeos previos al arranque agregados a la app (log persistente, panel
    de salud, preflight extendido, aviso de orden de arranque, bloqueo de
    doble arranque y limpieza de procesos huérfanos)."""

    def setUp(self):
        self.base_dir = tempfile.mkdtemp(prefix="vmtest_base_")
        self.addCleanup(shutil.rmtree, self.base_dir, ignore_errors=True)
        patcher = mock.patch.object(vm_config, "BASE_VM_DIR", self.base_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.win = vm.VirtualMachineManagerApp()
        self.win.show()
        self.addCleanup(self.win.close)

    def _make_vm_dir(self, name):
        vm_dir = os.path.join(self.base_dir, name)
        os.makedirs(vm_dir, exist_ok=True)
        return vm_dir

    @staticmethod
    def _stop(proc):
        if proc.poll() is None:
            proc.kill()
            proc.wait()

    def test_graphics_compat_hint_matrix(self):
        tabs = self.win.main_tabs
        for i in range(tabs.count()):
            if tabs.widget(i).isAncestorOf(self.win.combo_graphics):
                tabs.setCurrentIndex(i)
                break
        self.win.combo_main_os.setCurrentIndex(self.win.combo_main_os.findData("linux"))
        cases = [
            ("qxl", "uefi", True), ("vmware", "uefi", True),
            ("qxl", "bios", False), ("vmware", "bios", False),
            ("auto", "uefi", False), ("virtio", "uefi", False), ("none", "uefi", False),
        ]
        for mode, fw, expected in cases:
            self.win.combo_graphics.setCurrentIndex(self.win.combo_graphics.findData(mode))
            self.win.combo_firmware.setCurrentIndex(self.win.combo_firmware.findData(fw))
            self.win._update_graphics_compat_hint()
            # isHidden() refleja la decisión explícita del código
            # (setVisible True/False) sin depender de si la página de
            # configuración está activa en este momento.
            self.assertEqual(
                not self.win.label_graphics_compat.isHidden(),
                expected,
                f"modo={mode} firmware={fw}",
            )

    def test_log_message_persists_to_disk(self):
        vm_dir = self._make_vm_dir("TestLog")
        self.win.current_vm_dir = vm_dir
        self.win.log_message("==> hola mundo")
        log_path = os.path.join(vm_dir, "launch.log")
        self.assertTrue(os.path.isfile(log_path))
        with open(log_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("hola mundo", content)

    def test_preflight_detects_missing_storage_shared_folder_and_boot_order(self):
        vm_dir = self._make_vm_dir("TestPreflight")
        disk_path = os.path.join(vm_dir, "sata_Sistema.qcow2")
        with open(disk_path, "wb") as f:
            f.truncate(500 * 1024 * 1024)
        storage_devices = [
            {"id": "dev_disk1", "name": "Disco 1", "path": disk_path, "device": "sata"},
            {"id": "dev_cd1", "name": "CD/DVD 1", "path": "/ruta/inexistente.iso", "device": "cdrom"},
        ]
        shared_folders = [{"host": "/ruta/host/inexistente", "guest": "share", "method": "virtiofs", "readonly": False}]
        vm.save_vm_config(
            vm_dir, "TestPreflight", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
            {"storage_devices": storage_devices, "shared_folders": shared_folders},
            boot_order=["cdrom:dev_cd1", "disk:dev_disk1", "network"],
        )
        self.win.current_vm_dir = vm_dir
        _qemu, problems = self.win._preflight_check("linux")
        joined = "\n".join(problems)
        self.assertIn("CD/DVD 1", joined)
        self.assertIn("no existe", joined)
        self.assertIn("share", joined)
        self.assertIn("reinstalar", joined)

    def test_preflight_clean_vm_has_no_problems_beyond_host_environment(self):
        # Una VM sin discos rotos ni carpetas rotas no debe generar avisos
        # propios (los únicos posibles problemas restantes son del entorno
        # host de pruebas, como la falta de qemu-system-x86_64 o /dev/kvm).
        vm_dir = self._make_vm_dir("TestPreflightClean")
        vm.save_vm_config(vm_dir, "TestPreflightClean", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2", {})
        self.win.current_vm_dir = vm_dir
        _qemu, problems = self.win._preflight_check("linux")
        for p in problems:
            self.assertNotIn("ya no existe", p)
            self.assertNotIn("reinstalar", p)

    def test_start_installation_blocks_when_already_running(self):
        vm_dir = self._make_vm_dir("TestRunning")
        proc = subprocess.Popen(["sleep", "30"])
        self.addCleanup(self._stop, proc)
        with open(os.path.join(vm_dir, "qemu.pid"), "w") as f:
            f.write(str(proc.pid))
        self.win.input_vm_name.setText("TestRunning")
        with mock.patch.object(vm.QMessageBox, "warning") as warn:
            self.win.start_installation()
        self.assertTrue(warn.called)
        self.assertIn("ya está corriendo", warn.call_args[0][1])

    def test_clean_orphan_processes_kills_recorded_orphan(self):
        vm_dir = self._make_vm_dir("TestOrphan")
        orphan = subprocess.Popen(["sleep", "30"])
        self.addCleanup(self._stop, orphan)
        pidfile = os.path.join(vm_dir, "virtiofs-0.pid")
        with open(pidfile, "w") as f:
            f.write(str(orphan.pid))
        with mock.patch.object(vm.QMessageBox, "question", return_value=vm.QMessageBox.StandardButton.Yes), \
             mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.clean_orphan_processes()
        time.sleep(0.3)
        self.assertIsNotNone(orphan.poll(), "El proceso huérfano debía haber sido eliminado")
        self.assertFalse(os.path.exists(pidfile))
        self.assertTrue(info.called)

    def test_clean_orphan_processes_does_not_offer_to_kill_active_vm(self):
        vm_dir = self._make_vm_dir("TestActive")
        proc = subprocess.Popen(["sleep", "30"])
        self.addCleanup(self._stop, proc)
        with open(os.path.join(vm_dir, "qemu.pid"), "w") as f:
            f.write(str(proc.pid))
        with mock.patch.object(vm.QMessageBox, "question") as question, \
             mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.clean_orphan_processes()
        self.assertFalse(question.called, "No debe ofrecer matar una VM activa desde este botón")
        self.assertTrue(info.called)

    def test_clean_orphan_processes_reports_nothing_to_clean(self):
        with mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.clean_orphan_processes()
        self.assertTrue(info.called)
        self.assertIn("No se encontraron", info.call_args[0][2])

    def test_show_vm_health_check_reports_stopped_vm(self):
        vm_dir = self._make_vm_dir("TestHealthStopped")
        self.win.current_vm_dir = vm_dir
        with mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.show_vm_health_check()
        self.assertTrue(info.called)
        self.assertIn("detenido", info.call_args[0][2].lower())

    # --- #8: indicador de salud en la lista lateral ---

    def test_vm_list_label_warns_on_broken_shared_folder(self):
        vm_dir = self._make_vm_dir("TestSidebar")
        vm.save_vm_config(vm_dir, "TestSidebar", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"shared_folders": [{"host": "/tmp", "guest": "share", "method": "virtiofs", "readonly": False}]})
        # Sin virtiofs-0.pid -> la carpeta se considera caída.
        label = self.win._vm_list_label("TestSidebar", "running")
        self.assertIn("⚠️", label)

        proc = subprocess.Popen(["sleep", "30"])
        self.addCleanup(self._stop, proc)
        with open(os.path.join(vm_dir, "virtiofs-0.pid"), "w") as f:
            f.write(str(proc.pid))
        label_ok = self.win._vm_list_label("TestSidebar", "running")
        self.assertNotIn("⚠️", label_ok)

    def test_vm_list_label_never_warns_when_stopped(self):
        vm_dir = self._make_vm_dir("TestSidebarStopped")
        vm.save_vm_config(vm_dir, "TestSidebarStopped", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"shared_folders": [{"host": "/tmp", "guest": "share", "method": "virtiofs", "readonly": False}]})
        self.assertNotIn("⚠️", self.win._vm_list_label("TestSidebarStopped", "stopped"))

    def test_vm_name_from_list_text_strips_icon_and_warning_suffix(self):
        self.assertEqual(self.win._vm_name_from_list_text("🟢  MiVM ⚠️"), "MiVM")
        self.assertEqual(self.win._vm_name_from_list_text("⚪  MiVM"), "MiVM")

    # --- #7: estado en vivo de Guest Agent / carpetas / clipboard ---

    def test_live_integration_status_without_selected_vm(self):
        self.win.current_vm_dir = None
        self.win._refresh_live_integration_status()
        self.assertIn("—", self.win.label_live_guest_agent.text())

    def test_live_integration_status_shows_off_when_vm_stopped(self):
        vm_dir = self._make_vm_dir("TestLiveStopped")
        vm.save_vm_config(vm_dir, "TestLiveStopped", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2", {})
        self.win.current_vm_dir = vm_dir
        self.win._refresh_live_integration_status()
        self.assertIn("apagado", self.win.label_live_guest_agent.text())
        self.assertIn("apagado", self.win.label_live_shared_folders.text())
        self.assertIn("apagado", self.win.label_live_clipboard.text())

    def test_compute_live_integration_status_reports_broken_folder_and_clipboard_mode(self):
        vm_dir = self._make_vm_dir("TestLiveCompute")
        vm.save_vm_config(vm_dir, "TestLiveCompute", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2",
                           {"clipboard": {"mode": "bidirectional"},
                            "shared_folders": [{"host": "/tmp", "guest": "share", "method": "virtiofs", "readonly": False}]})
        with mock.patch.object(vm.shutil, "which", return_value=None):  # sin qemu -> guest agent sin respuesta
            result = self.win._compute_live_integration_status(vm_dir)
        self.assertFalse(result["guest_agent"])
        self.assertFalse(result["shared_folders"])  # falta virtiofs-0.pid
        self.assertEqual(result["clipboard"], "bidirectional")

    def test_compute_live_integration_status_clipboard_disabled(self):
        vm_dir = self._make_vm_dir("TestLiveNoClip")
        vm.save_vm_config(vm_dir, "TestLiveNoClip", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2", {})
        with mock.patch.object(vm.shutil, "which", return_value=None):
            result = self.win._compute_live_integration_status(vm_dir)
        self.assertIsNone(result["clipboard"])

    # --- #10: adjuntar Guest Tools con un clic ---

    def test_attach_guest_tools_iso_creates_and_attaches(self):
        vm_dir = self._make_vm_dir("TestGuestTools")
        vm.save_vm_config(vm_dir, "TestGuestTools", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2", {})
        self.win.current_vm_dir = vm_dir
        guest_tools_dir = tempfile.mkdtemp(prefix="vmtest_gt_")
        self.addCleanup(shutil.rmtree, guest_tools_dir, ignore_errors=True)
        iso_path = os.path.join(guest_tools_dir, vm.GUEST_TOOLS_ISO_NAME)

        # attach_guest_tools_iso usa run_async (asíncrono). Para el test
        # ejecutamos la tarea de forma síncrona mockeando run_async.
        def sync_run_async(func, title, on_success=None, on_error=None,
                           cancelable=False, show_log=True, subtitle=""):
            try:
                # El TaskProgressDialog no es necesario; extraemos la lógica pura.
                # La función de _work recibe (log_emit, is_cancelled, progress_emit).
                class _DlgStub:
                    def set_progress(self, *a, **k): pass
                    def append_log(self, *a, **k): pass
                class _ThreadStub:
                    log_signal = mock.MagicMock()
                    progress_signal = mock.MagicMock()
                    def isRunning(self): return False
                    def request_cancel(self): pass
                    def start(self): pass
                result = None
                try:
                    result = func(lambda msg: None, lambda: False, lambda pct, txt="": None)
                except TypeError:
                    try:
                        result = func(lambda msg: None, lambda: False)
                    except TypeError:
                        result = func(lambda msg: None)
                if on_success:
                    on_success(result)
            except Exception as e:
                if on_error:
                    on_error(e)
                else:
                    raise
            return None, None

        with mock.patch.object(self.win, "_guest_tools_dir", return_value=guest_tools_dir), \
             mock.patch.object(self.win, "run_async", side_effect=sync_run_async), \
             mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.attach_guest_tools_iso()
        self.assertTrue(os.path.isfile(iso_path))
        devices = self.win._storage_devices_all(vm_dir)
        self.assertTrue(any(d.get("path") == iso_path and d.get("device") == "cdrom" for d in devices))
        self.assertIn("adjuntada", info.call_args[0][2])

    def test_attach_guest_tools_iso_does_not_duplicate(self):
        vm_dir = self._make_vm_dir("TestGuestToolsTwice")
        vm.save_vm_config(vm_dir, "TestGuestToolsTwice", "linux", "4G", 2, "40G", "qcow2", "qcow2", ".qcow2", {})
        self.win.current_vm_dir = vm_dir
        guest_tools_dir = tempfile.mkdtemp(prefix="vmtest_gt2_")
        self.addCleanup(shutil.rmtree, guest_tools_dir, ignore_errors=True)
        iso_path = os.path.join(guest_tools_dir, vm.GUEST_TOOLS_ISO_NAME)

        # Ver el comentario en test_attach_guest_tools_iso_creates_and_attaches:
        # run_async se mockea para ejecutar la tarea de forma síncrona.
        def sync_run_async(func, title, on_success=None, on_error=None,
                           cancelable=False, show_log=True, subtitle=""):
            try:
                result = None
                try:
                    result = func(lambda msg: None, lambda: False, lambda pct, txt="": None)
                except TypeError:
                    try:
                        result = func(lambda msg: None, lambda: False)
                    except TypeError:
                        result = func(lambda msg: None)
                if on_success:
                    on_success(result)
            except Exception as e:
                if on_error:
                    on_error(e)
                else:
                    raise
            return None, None

        with mock.patch.object(self.win, "_guest_tools_dir", return_value=guest_tools_dir), \
             mock.patch.object(self.win, "run_async", side_effect=sync_run_async), \
             mock.patch.object(vm.QMessageBox, "information"):
            self.win.attach_guest_tools_iso()
            self.win.attach_guest_tools_iso()
        devices = self.win._storage_devices_all(vm_dir)
        self.assertEqual(sum(1 for d in devices if d.get("path") == iso_path), 1)

    def test_attach_guest_tools_iso_requires_selected_vm(self):
        self.win.current_vm_dir = None
        with mock.patch.object(vm.QMessageBox, "information") as info:
            self.win.attach_guest_tools_iso()
        self.assertIn("Selecciona", info.call_args[0][2])


class LaunchCommandTests(unittest.TestCase):
    """#9: evitar que el host se suspenda mientras la VM corre."""

    def test_uses_systemd_inhibit_when_available(self):
        w = make_worker()
        exec_path = os.path.join(w.vm_dir, "run_temp.sh")
        with mock.patch.object(vm.shutil, "which", return_value="/usr/bin/systemd-inhibit"):
            cmd = w._build_launch_command(exec_path)
        self.assertEqual(cmd[0], "/usr/bin/systemd-inhibit")
        self.assertEqual(cmd[-1], exec_path)
        self.assertIn("--what=sleep:idle", cmd)

    def test_falls_back_without_systemd_inhibit(self):
        w = make_worker()
        exec_path = os.path.join(w.vm_dir, "run_temp.sh")
        with mock.patch.object(vm.shutil, "which", return_value=None):
            cmd = w._build_launch_command(exec_path)
        self.assertEqual(cmd, [exec_path])

    def test_logs_when_inhibit_is_used(self):
        w = make_worker()
        exec_path = os.path.join(w.vm_dir, "run_temp.sh")
        logs = []
        w.log_signal.connect(logs.append)
        with mock.patch.object(vm.shutil, "which", return_value="/usr/bin/systemd-inhibit"):
            w._build_launch_command(exec_path)
        self.assertTrue(any("systemd-inhibit" in m for m in logs))


class DialogsWidgetTests(unittest.TestCase):
    """Regresión: RealtimePerformanceGraph usaba Qt.AlignmentFlag en su
    paintEvent sin importar Qt en dialogs.py. Un simple `show()` no dispara
    paintEvent en el backend offscreen, así que estos tests fuerzan un
    repintado real con `repaint()` para no volver a dejar pasar este tipo
    de NameError silencioso."""

    def test_realtime_performance_graph_paints_without_crashing(self):
        w = vm.RealtimePerformanceGraph("CPU")
        w.resize(300, 150)
        w.show()
        w.repaint()  # dispara paintEvent de verdad
        w.close()

    def test_realtime_performance_graph_paints_with_data(self):
        w = vm.RealtimePerformanceGraph("RAM")
        w.resize(300, 150)
        if hasattr(w, "add_value"):
            w.add_value(42.0)
        w.show()
        w.repaint()
        w.close()

    def test_network_device_dialog_paints_without_crashing(self):
        d = vm.NetworkDeviceDialog()
        d.show()
        d.repaint()
        d.close()

    def test_disk_creation_dialog_paints_without_crashing(self):
        d = vm.DiskCreationDialog()
        d.show()
        d.repaint()
        d.close()



class SuggestionsTests(unittest.TestCase):
    """Tests para compute_suggestions() en suggestions_mixin.py.

    Estos tests NO dependen del estado real del host (disco, RAM, IOMMU):
    mockean las funciones internas que leen el sistema, para poder verificar
    cada sugerencia de forma aislada y determinista.
    """

    def setUp(self):
        self.base_dir = tempfile.mkdtemp(prefix="vmtest_sugg_")
        self.addCleanup(shutil.rmtree, self.base_dir, ignore_errors=True)

    def _make_vm(self, name, extra=None, **overrides):
        """Crea una VM de prueba con la configuración mínima + extras."""
        vm_dir = os.path.join(self.base_dir, name)
        os.makedirs(vm_dir, exist_ok=True)
        params = dict(
            os_type="linux", ram="4G", cores=2, disk_size="40G",
            disk_type="qcow2", disk_format="qcow2", disk_ext=".qcow2",
        )
        params.update(overrides)
        vm.save_vm_config(
            vm_dir, name,
            params["os_type"], params["ram"], params["cores"],
            params["disk_size"], params["disk_type"],
            params["disk_format"], params["disk_ext"],
            extra or {},
        )
        return vm_dir

    # ------------------------------------------------------------------
    # 1. Selección vacía
    # ------------------------------------------------------------------
    def test_no_vm_selected_returns_info(self):
        from suggestions_mixin import compute_suggestions
        result = compute_suggestions(None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "info")
        self.assertIn("Selecciona", result[0][1])

    # ------------------------------------------------------------------
    # 2. Todo en orden
    # ------------------------------------------------------------------
    def test_all_ok_returns_ok_message(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestOK")
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)), \
             mock.patch("suggestions_mixin._check_iommu_active", return_value=True), \
             mock.patch("suggestions_mixin._log_size_mb", return_value=None):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any(lvl == "ok" for lvl, _ in result),
                        f"Se esperaba 'ok'; resultado={result}")

    # ------------------------------------------------------------------
    # 3. Disco lleno (warn)
    # ------------------------------------------------------------------
    def test_disk_full_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestDiskFull")
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(92.0, 5*1024**3, 100*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        warn_msgs = [txt for lvl, txt in result if lvl == "warn"]
        self.assertTrue(any("92" in m or "crítico" in m.lower() for m in warn_msgs),
                        f"Se esperaba warning de disco; resultado={result}")

    # ------------------------------------------------------------------
    # 4. Disco crítico (>= 95%)
    # ------------------------------------------------------------------
    def test_disk_critical_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestDiskCrit")
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(97.0, 1*1024**3, 100*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("crítico" in m.lower() for _, m in result),
                        f"Se esperaba 'crítico'; resultado={result}")

    # ------------------------------------------------------------------
    # 5. RAM excesiva
    # ------------------------------------------------------------------
    def test_excessive_ram_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestRam", ram="24G")
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        # 24G / 32G = 75% > 50%
        self.assertTrue(any("swap" in m.lower() or "RAM" in m for _, m in result),
                        f"Se esperaba warning de RAM; resultado={result}")

    # ------------------------------------------------------------------
    # 6. Carpeta compartida rota
    # ------------------------------------------------------------------
    def test_broken_shared_folder_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestBrokenFolder", extra={
            "shared_folders": [
                {"host": "/ruta/que/no/existe", "guest": "rota", "method": "virtiofs", "readonly": False},
            ],
        })
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("rota" in m or "ya no existen" in m for _, m in result),
                        f"Se esperaba warning de carpeta rota; resultado={result}")

    # ------------------------------------------------------------------
    # 7. Windows 11 sin UEFI
    # ------------------------------------------------------------------
    def test_win11_without_uefi_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm(
            "TestWin11",
            os_type="windows", firmware="bios",
            extra={"win_ver": "Windows 11"},
        )
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("Windows 11" in m and "UEFI" in m for _, m in result),
                        f"Se esperaba warning Win11/UEFI; resultado={result}")

    # ------------------------------------------------------------------
    # 8. Disco RAW sugiere QCOW2
    # ------------------------------------------------------------------
    def test_raw_disk_suggests_qcow2(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestRaw", disk_format="raw", disk_ext=".img")
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("RAW" in m and "QCOW2" in m for _, m in result),
                        f"Se esperaba sugerencia de QCOW2; resultado={result}")

    # ------------------------------------------------------------------
    # 9. PCI passthrough sin IOMMU
    # ------------------------------------------------------------------
    def test_pci_without_iommu_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestPci", extra={
            "passthrough_devices": [
                {"kind": "pci", "address": "0000:01:00.0"},
            ],
        })
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)), \
             mock.patch("suggestions_mixin._check_iommu_active", return_value=False):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("IOMMU" in m for _, m in result),
                        f"Se esperaba warning de IOMMU; resultado={result}")

    # ------------------------------------------------------------------
    # 10. Snapshot antiguo
    # ------------------------------------------------------------------
    def test_old_snapshot_informs(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestSnap")
        # Crear un PNG con fecha antigua simulada
        snap_dir = os.path.join(vm_dir, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        snap_path = os.path.join(snap_dir, "viejo.png")
        with open(snap_path, "wb") as f:
            f.write(b"fake")
        # Simular 60 días de antigüedad
        old_time = time.time() - 60 * 86400
        os.utime(snap_path, (old_time, old_time))
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("snapshot" in m.lower() and "días" in m.lower() for _, m in result),
                        f"Se esperaba info de snapshot antiguo; resultado={result}")

    # ------------------------------------------------------------------
    # 11. Muchos snapshots acumulados
    # ------------------------------------------------------------------
    def test_many_snapshots_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = self._make_vm("TestManySnaps")
        snap_dir = os.path.join(vm_dir, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        for i in range(6):
            with open(os.path.join(snap_dir, f"snap{i}.png"), "wb") as f:
                f.write(b"x" * 1024)
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("6" in m or "acumulados" in m for _, m in result),
                        f"Se esperaba warning de muchos snapshots; resultado={result}")

    # ------------------------------------------------------------------
    # 12. VM sin Guest Agent con VirtioFS
    # ------------------------------------------------------------------
    def test_virtiofs_without_guest_agent_informs(self):
        from suggestions_mixin import compute_suggestions
        tmp_host = tempfile.mkdtemp(prefix="vmtest_host_")
        self.addCleanup(shutil.rmtree, tmp_host, ignore_errors=True)
        vm_dir = self._make_vm("TestVirtioNoAgent", extra={
            "shared_folders": [
                {"host": tmp_host, "guest": "share", "method": "virtiofs", "readonly": False},
            ],
            "guest_agent_enabled": False,
        })
        with mock.patch("suggestions_mixin._disk_usage_for", return_value=(30.0, 100*1024**3, 200*1024**3)):
            result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any("Guest Agent" in m for _, m in result),
                        f"Se esperaba info de Guest Agent; resultado={result}")

    # ------------------------------------------------------------------
    # 13. Config ilegible → warning
    # ------------------------------------------------------------------
    def test_unreadable_config_warns(self):
        from suggestions_mixin import compute_suggestions
        vm_dir = os.path.join(self.base_dir, "TestBadCfg")
        os.makedirs(vm_dir, exist_ok=True)
        with open(os.path.join(vm_dir, "vm_config.ini"), "w") as f:
            f.write("[general]\nname = X\n")  # falta [hardware]
        result = compute_suggestions(vm_dir, host_ram_gb=32)
        self.assertTrue(any(lvl == "warn" for lvl, _ in result),
                        f"Se esperaba warning; resultado={result}")


class ConsoleSwitchTests(unittest.TestCase):
    """Tests de la consola por VM: combos y botones de control.

    Requiere instanciar la ventana principal, así que hereda del patrón
    de AppInstanceTests (Qt en modo offscreen con BASE_VM_DIR temporal).
    """

    def setUp(self):
        self.base_dir = tempfile.mkdtemp(prefix="vmtest_conswitch_")
        self.addCleanup(shutil.rmtree, self.base_dir, ignore_errors=True)
        patcher = mock.patch.object(vm_config, "BASE_VM_DIR", self.base_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.win = vm.VirtualMachineManagerApp()
        self.addCleanup(self.win.close)

    # ------------------------------------------------------------------
    # _apply_console_choice_from_vm: los combos siguen a la VM
    # ------------------------------------------------------------------

    def test_apply_console_choice_embedded_vnc(self):
        data = {"extra": {"console_protocol": "vnc", "console_mode": "embedded"}}
        self.win._apply_console_choice_from_vm(data)
        self.assertEqual(self.win.combo_console_protocol.currentData(), "vnc")
        self.assertEqual(self.win.combo_console_mode.currentData(), "embedded")

    def test_apply_console_choice_external_spice(self):
        data = {"extra": {"console_protocol": "spice", "console_mode": "external"}}
        self.win._apply_console_choice_from_vm(data)
        self.assertEqual(self.win.combo_console_protocol.currentData(), "spice")
        self.assertEqual(self.win.combo_console_mode.currentData(), "external")

    def test_apply_console_choice_legacy_vnc_embedded(self):
        # Compatibilidad: VMs sin console_protocol / console_mode, pero con
        # vnc_embedded=True, se interpretan como VNC + Embebida.
        data = {"extra": {"vnc_embedded": True}}
        self.win._apply_console_choice_from_vm(data)
        self.assertEqual(self.win.combo_console_protocol.currentData(), "vnc")
        self.assertEqual(self.win.combo_console_mode.currentData(), "embedded")

    def test_apply_console_choice_legacy_no_embedded(self):
        data = {"extra": {"vnc_embedded": False}}
        self.win._apply_console_choice_from_vm(data)
        self.assertEqual(self.win.combo_console_mode.currentData(), "native")

    # ------------------------------------------------------------------
    # _update_start_stop_buttons: habilitación coherente
    # ------------------------------------------------------------------

    def _make_vm_selected(self, name="SwitchTest"):
        vm_dir = os.path.join(self.base_dir, name)
        os.makedirs(vm_dir, exist_ok=True)
        vm.save_vm_config(vm_dir, name, "linux", "4G", 2, "40G",
                          "qcow2", "qcow2", ".qcow2", {})
        self.win.current_vm_dir = vm_dir
        return vm_dir

    def test_buttons_disabled_without_vm(self):
        self.win.current_vm_dir = None
        self.win._update_start_stop_buttons("stopped")
        self.assertFalse(self.win.btn_vm_start.isEnabled())
        self.assertFalse(self.win.btn_vm_pause.isEnabled())
        self.assertFalse(self.win.btn_vm_poweroff.isEnabled())

    def test_only_start_enabled_when_stopped(self):
        self._make_vm_selected()
        self.win._update_start_stop_buttons("stopped")
        self.assertTrue(self.win.btn_vm_start.isEnabled())
        self.assertFalse(self.win.btn_vm_pause.isEnabled())
        self.assertFalse(self.win.btn_vm_poweroff.isEnabled())

    def test_pause_and_poweroff_enabled_when_running(self):
        self._make_vm_selected()
        self.win._update_start_stop_buttons("running")
        self.assertFalse(self.win.btn_vm_start.isEnabled())
        self.assertTrue(self.win.btn_vm_pause.isEnabled())
        self.assertTrue(self.win.btn_vm_poweroff.isEnabled())

    def test_pause_and_poweroff_enabled_when_paused(self):
        self._make_vm_selected()
        self.win._update_start_stop_buttons("paused")
        self.assertFalse(self.win.btn_vm_start.isEnabled())
        self.assertTrue(self.win.btn_vm_pause.isEnabled())
        self.assertTrue(self.win.btn_vm_poweroff.isEnabled())

    # ------------------------------------------------------------------
    # _focus_console_for_vm: no debe explotar aunque no haya ventanas
    # ------------------------------------------------------------------

    def test_focus_console_without_data_does_not_raise(self):
        # Sin VM seleccionada y sin data; solo comprueba que no lanza.
        try:
            self.win._focus_console_for_vm("NoExiste")
        except Exception as e:
            self.fail(f"_focus_console_for_vm lanzó: {e}")

    def test_focus_console_goes_to_console_tab_when_embedded(self):
        # VM apagada: va a Resumen (índice 0).
        vm_dir = self._make_vm_selected("FocusEmbedded")
        # Forzamos modo embedded en la config.
        data = vm.load_vm_config(vm_dir)
        data["extra"] = data.get("extra") or {}
        data["extra"]["console_protocol"] = "vnc"
        data["extra"]["console_mode"] = "embedded"
        # Mock de _runtime_state para simular "running" sin QEMU real.
        with mock.patch.object(self.win, "_runtime_state", return_value="running"):
            with mock.patch.object(vm, "load_vm_config", return_value=data):
                self.win._focus_console_for_vm("FocusEmbedded", data)
        idx = self.win.main_tabs.currentIndex()
        console_idx = getattr(self.win, "_console_tab_index", -1)
        if console_idx >= 0:
            self.assertEqual(idx, console_idx)


if __name__ == "__main__":
    unittest.main()
