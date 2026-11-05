import subprocess
import logging
import os
import time
import socket
import shutil
import glob
import json
from pathlib import Path
from typing import Dict
from .host_adapter import HostAdapter

log = logging.getLogger(__name__)

class VMRunner:
    def __init__(self, host: HostAdapter, data_dir: Path):
        self.host = host
        self.data_dir = data_dir
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.active_viewers: Dict[str, subprocess.Popen] = {}

    def _find_free_port(self, start: int = 5900, end: int = 6000, exclude: set = None) -> int:
        exclude = exclude or set()
        for port in range(start, end):
            if port in exclude:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        raise RuntimeError(f"No hay puertos libres entre {start} y {end}.")

    def _find_free_vnc_port(self, exclude: set = None) -> int:
        return self._find_free_port(5900, 6000, exclude=exclude)

    def _find_ovmf(self, secure_boot=False):
        project_root = Path(__file__).parent.parent
        search_dirs = [
            project_root / "OSX-KVM", self.data_dir / "OSX-KVM",
            Path("/usr/share/edk2/x64/"), Path("/usr/share/OVMF/"),
            Path("/usr/share/edk2/ovmf/"), Path("/usr/share/edk2-ovmf/x64/"),
            Path("/usr/share/qemu/"), self.data_dir
        ]

        def _is_valid_code(path):
            try: return os.path.exists(path) and os.path.getsize(path) > 1024 * 1024
            except: return False
        def _is_valid_vars(path):
            try: return os.path.exists(path) and os.path.getsize(path) > 10 * 1024
            except: return False

        if secure_boot:
            for d in search_dirs:
                if not d.exists(): continue
                code_candidates = glob.glob(str(d / "OVMF_CODE*.secboot*.fd"))
                valid_codes = [p for p in code_candidates if _is_valid_code(p)]
                if not valid_codes: continue
                code_path = valid_codes[0]
                vars_candidates = glob.glob(str(d / "OVMF_VARS*.secboot*.fd"))
                valid_vars = [p for p in vars_candidates if _is_valid_vars(p)]
                if not valid_vars:
                    vars_candidates = glob.glob(str(d / "OVMF_VARS*.4m.fd")) + glob.glob(str(d / "OVMF_VARS*.fd"))
                    valid_vars = [p for p in vars_candidates if _is_valid_vars(p)]
                if valid_vars: return code_path, valid_vars[0]

        for d in search_dirs:
            if not d.exists(): continue
            for code_pat in ["OVMF_CODE_4M.fd", "OVMF_CODE*.4m.fd", "OVMF_CODE*.fd"]:
                matches = glob.glob(str(d / code_pat))
                valid = [p for p in matches if _is_valid_code(p)]
                if valid:
                    code_path = valid[0]
                    break
            else: continue
            for vars_pat in ["OVMF_VARS.fd", "OVMF_VARS*.4m.fd", "OVMF_VARS*.fd"]:
                matches = glob.glob(str(d / vars_pat))
                valid = [p for p in matches if _is_valid_vars(p)]
                if valid: return code_path, valid[0]
        return None, None

    def _kill_orphan_qemu(self, disk_path):
        if not disk_path or not os.path.exists(disk_path): return
        try:
            result = subprocess.run(["lsof", "-t", disk_path], capture_output=True, text=True, timeout=3)
            pids = result.stdout.strip().split()
            if pids:
                for pid in pids:
                    try: os.kill(int(pid), 9)
                    except: pass
                time.sleep(1)
        except: pass

    def _setup_tpm(self, vm: dict, q35: bool) -> list[str]:
        vm_id = vm["id"]
        tpm_dir = os.path.join(self.data_dir, "vms", vm_id, "tpm")
        os.makedirs(tpm_dir, exist_ok=True)
        sock_path = f"/tmp/swtpm-{vm_id}.sock"
        try:
            subprocess.run(["pkill", "-9", "-f", f"swtpm.*{vm_id}"], check=False, timeout=2)
            time.sleep(0.3)
        except: pass
        if os.path.exists(sock_path):
            try: os.remove(sock_path)
            except: pass
        for f in ["tpm2-00.permall", "tpm-00.permall"]:
            p = os.path.join(tpm_dir, f)
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        swtpm_cmd = ["swtpm", "socket", "--tpmstate", f"dir={tpm_dir}", "--ctrl", f"type=unixio,path={sock_path}", "--tpm2", "--daemon", "--log", f"file={tpm_dir}/swtpm.log,level=5"]
        try: subprocess.run(swtpm_cmd, check=True)
        except FileNotFoundError: raise RuntimeError("swtpm no instalado.")
        start = time.time()
        while not os.path.exists(sock_path):
            if time.time() - start > 3.0: raise RuntimeError("Timeout esperando a swtpm.")
            time.sleep(0.1)
        tpm_device = "tpm-crb" if q35 else "tpm-tis"
        return ["-chardev", f"socket,id=chrtpm,path={sock_path}", "-tpmdev", "emulator,id=tpm0,chardev=chrtpm", "-device", f"{tpm_device},tpmdev=tpm0"]

    def _build_cpu_args(self, vm: dict) -> list[str]:
        cpu_idx = vm.get("cpu_type_idx", 0)
        base_map = {0: None, 1: "host", 2: "qemu64", 3: "Skylake-Client", 4: "Haswell", 5: "Broadwell", 6: "SandyBridge", 7: "Penryn"}
        base = base_map.get(cpu_idx, None) or ("host" if self.host.kvm_available else "qemu64")
        flags = []
        if vm.get("nested_virt"): flags.append("vmx=on")
        if vm.get("hyperv"): flags.extend(["hv_relaxed=on", "hv_spinlocks=0x1fff", "hv_vapic=on", "hv_time=on"])
        return [f"{base}," + ",".join(flags)] if flags else [base]

    def _build_graphics_device_args(self, vm: dict) -> list[str]:
        gfx_idx = vm.get("graphics_idx", 0)
        vram_mb = [64, 128, 256, 512][vm.get("vram_idx", 0)]
        if any(d.get("is_vga", False) and d.get("type") == "PCI" for d in vm.get("passthrough_devices", [])):
            return ["-vga", "none"]
        graphics_map = {
            0: ["-vga", "virtio"], 1: ["-vga", "virtio"],
            2: ["-vga", "virtio", "-display", "gtk,gl=on"], 3: ["-vga", "virtio", "-display", "gtk,gl=on"],
            4: ["-vga", "qxl", "-global", f"qxl-vga.vgamem_mb={vram_mb}"],
            5: ["-vga", "vmware"], 6: ["-vga", "std"], 7: ["-vga", "none"],
        }
        return list(graphics_map.get(gfx_idx, graphics_map[0]))

    def _build_display_protocol_args(self, vm: dict, exclude_ports: set = None):
        exclude_ports = exclude_ports or set()
        proto_idx, mode_idx = vm.get("console_proto_idx", 0), vm.get("console_mode_idx", 0)
        args, external_info = [], None

        if mode_idx == 2:
            vnc_port = self._find_free_vnc_port(exclude=exclude_ports)
            exclude_ports.add(vnc_port); vm["vnc_port"] = vnc_port
            args.extend(["-vnc", f"127.0.0.1:{vnc_port - 5900}"])
            spice_port = self._find_free_port(5930, 6000, exclude=exclude_ports)
            exclude_ports.add(spice_port); vm["spice_port"] = spice_port
            args.extend(["-spice", f"port={spice_port},addr=127.0.0.1,disable-ticketing=on"])
            args.extend(["-device", "virtio-serial-pci", "-chardev", "spicevmc,id=vdagent,name=vdagent", "-device", "virtserialport,chardev=vdagent,name=com.redhat.spice.0"])
            return args, {"type": "spice", "port": spice_port}

        if proto_idx == 1:
            if mode_idx in (0, 3): mode_idx = 1
            spice_port = self._find_free_port(5930, 6000, exclude=exclude_ports)
            exclude_ports.add(spice_port); vm["spice_port"] = spice_port
            args.extend(["-spice", f"port={spice_port},addr=127.0.0.1,disable-ticketing=on"])
            args.extend(["-device", "virtio-serial-pci", "-chardev", "spicevmc,id=vdagent,name=vdagent", "-device", "virtserialport,chardev=vdagent,name=com.redhat.spice.0"])
            if mode_idx == 1: external_info = {"type": "spice", "port": spice_port}
        else:
            vnc_port = self._find_free_vnc_port(exclude=exclude_ports)
            exclude_ports.add(vnc_port); vm["vnc_port"] = vnc_port
            args.extend(["-vnc", f"127.0.0.1:{vnc_port - 5900}"])
            if mode_idx == 1: external_info = {"type": "vnc", "port": vnc_port}
        return args, external_info

    def _build_passthrough_args(self, vm: dict) -> list[str]:
        args = []
        from . import host_passthrough
        for dev in vm.get("passthrough_devices", []):
            dtype = dev.get("type", "")
            
            if dtype == "PCI":
                did = dev.get("id", "")
                is_bdf = did.count(":") == 2 and "." in did
                if is_bdf:
                    driver_path = f"/sys/bus/pci/devices/{did}/driver"
                    current_driver = ""
                    if os.path.exists(driver_path):
                        try: current_driver = os.path.basename(os.readlink(driver_path))
                        except: pass
                    
                    if current_driver != "vfio-pci":
                        log.info(f"Vinculando {did} a vfio-pci (driver: {current_driver})...")
                        if not host_passthrough.dynamic_bind_vfio(did):
                            raise RuntimeError(f"Cancelado o fallido al enlazar {did} a vfio-pci. Abortando arranque de VM para evitar crash.")
                        time.sleep(1.5)
                    
                    opts = [f"host={did}"]
                    if dev.get("is_vga", False):
                        opts.append("x-vga=on")
                        opts.append("multifunction=on")
                    args.extend(["-device", "vfio-pci," + ",".join(opts)])
                else:
                    log.error(f"PCI passthrough con id inválido '{did}'. Se omite.")
                    
            elif dtype == "USB":
                vid_did = dev.get("vid_did", "")
                if ":" in vid_did:
                    vid, pid = vid_did.split(":", 1)
                    args.extend(["-device", f"usb-host,bus=xhci.0,vendorid=0x{vid},productid=0x{pid}"])
                else:
                    did = dev.get("id", "")
                    if did.count(":") == 1:
                        bus, addr = did.split(":", 1)
                        args.extend(["-device", f"usb-host,bus=xhci.0,hostbus={bus},hostaddr={addr}"])
                    else:
                        log.error(f"USB passthrough con id inválido '{did}'. Se omite.")
        return args

    def _launch_external_viewer(self, vm_id: str, info: dict):
        if not info: return None
        vtype, port = info.get("type"), info.get("port")
        if not vtype or not port: return None
        candidates = [
            ("xtigervncviewer", ["xtigervncviewer", f"127.0.0.1:{port - 5900}"]),
            ("vncviewer", ["vncviewer", f"127.0.0.1:{port - 5900}"]),
            ("remmina", ["remmina", "-c", f"vnc://127.0.0.1:{port}"])
        ] if vtype == "vnc" else [
            ("remote-viewer", ["remote-viewer", f"spice://127.0.0.1:{port}"]),
            ("virt-viewer", ["virt-viewer", "--connect", f"spice://127.0.0.1:{port}"]),
            ("spicy", ["spicy", "-h", "127.0.0.1", "-p", str(port)])
        ]
        for name, cmd in candidates:
            if not shutil.which(name): continue
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                log.info(f"Viewer externo '{name}' lanzado para {vm_id}")
                return proc
            except Exception as e: log.warning(f"Fallo lanzando '{name}': {e}")
        return None

    def _kill_external_viewer(self, vm_id: str):
        viewer = self.active_viewers.pop(vm_id, None)
        if viewer and viewer.poll() is None:
            viewer.terminate()
            try: viewer.wait(timeout=3)
            except: viewer.kill()

    def _build_cdrom_args(self, vm: dict, q35: bool) -> list[str]:
        iso_path = vm.get("iso_path")
        cdrom_bus = vm.get("cdrom_bus", "SATA/AHCI" if q35 else "IDE")
        if iso_path and os.path.exists(iso_path) and os.path.getsize(iso_path) > 5000000:
            file_opt = f"file={iso_path},format=raw"
        else:
            file_opt = ""
        args = ["-drive", f"id=cdrom0,if=none,media=cdrom,{file_opt}".rstrip(",")]
        b = cdrom_bus.lower()
        if "sata" in b or "auto" in b:
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ahci.1"])
        elif "scsi" in b:
            args.extend(["-device", "lsi53c895a,id=scsi0", "-device", "scsi-cd,drive=cdrom0,bus=scsi0.0"])
        elif "usb" in b:
            args.extend(["-device", "usb-storage,drive=cdrom0"])
        else:
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ide.1"])
        return args

    def build_command(self, vm: Dict) -> list[str]:
        if not self.host.qemu_path: raise RuntimeError("QEMU no instalado.")
        disk_path = vm.get("disk_path")
        disk_format = vm.get("disk_format", "qcow2")
        
        if disk_path:
            ext = os.path.splitext(disk_path)[1].lower()
            disk_format = {"img": "raw", "raw": "raw", "vdi": "vdi", "vmdk": "vmdk", "vhd": "vpc", "vhdx": "vhdx", "qcow2": "qcow2"}.get(ext, disk_format)
            self._kill_orphan_qemu(disk_path)

        is_macos = (vm.get("platform", "") == "macOS")
        q35 = True if is_macos else (vm.get("chipset_idx", 0) == 1)
        machine_type = "q35" if q35 else "pc"

        cmd = [self.host.qemu_path, "-machine", machine_type, "-accel", "kvm" if self.host.kvm_available else "tcg"]
        cmd.extend(["-cpu"] + (["Skylake-Client,-hle,-rtm,kvm=on,vendor=GenuineIntel,+invtsc,vmware-cpuid-freq=on,+ssse3,+sse4.2,+popcnt,+avx,+aes,+xsave,+xsaveopt,check"] if is_macos else self._build_cpu_args(vm)))
        
        ram_mb = ((vm.get("ram", 4096) + 1023) // 1024) * 1024 if is_macos else vm.get("ram", 4096)
        cmd.extend(["-m", str(ram_mb)])

        total_cores = vm.get("cores", 2)
        if vm.get("cpu_topology", False):
            s, c, t = vm.get("cpu_sockets", 1), vm.get("cpu_cores_per_socket", 2), vm.get("cpu_threads_per_core", 1)
            cmd.extend(["-smp", f"{s*c*t},sockets={s},cores={c},threads={t}"])
        else:
            cmd.extend(["-smp", str(total_cores if total_cores % 2 == 0 else total_cores + 1)])

        if vm.get("firmware_idx", 0) == 1:
            code_path, vars_path = self._find_ovmf(vm.get("secure_boot", False))
            if code_path and vars_path:
                vm_dir = os.path.join(self.data_dir, "vms", vm["id"])
                os.makedirs(vm_dir, exist_ok=True)
                local_vars = os.path.join(vm_dir, "OVMF_VARS.fd")
                if not os.path.exists(local_vars) or os.path.getsize(local_vars) != os.path.getsize(vars_path):
                    shutil.copy(vars_path, local_vars)
                cmd.extend(["-drive", f"if=pflash,format=raw,readonly=on,file={code_path}", "-drive", f"if=pflash,format=raw,file={local_vars}"])

        if vm.get("tpm", False) and not is_macos:
            cmd.extend(self._setup_tpm(vm, q35))

        if is_macos:
            cmd.extend(["-device", "ich9-ahci,id=sata"])
            project_root = Path(__file__).parent.parent
            opencore_candidates = [project_root / "OSX-KVM" / "OpenCore" / "OpenCore.qcow2", self.data_dir / "OSX-KVM" / "OpenCore" / "OpenCore.qcow2"]
            opencore_path = next((p for p in opencore_candidates if p.exists()), None)
            if not opencore_path: raise RuntimeError("No se encontró OpenCore.qcow2.")

            cmd.extend(["-drive", f"id=OpenCoreBoot,if=none,snapshot=on,format=qcow2,file={opencore_path}", "-device", "ide-hd,bus=sata.2,drive=OpenCoreBoot"])
            osk = "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
            cmd.extend(["-device", f"isa-applesmc,osk=\"{osk}\"", "-smbios", "type=2"])
            cmd.extend(["-global", "ICH9-LPC.disable_s3=1", "-global", "ICH9-LPC.disable_s4=1"])
            cmd.extend(["-device", "usb-ehci,id=ehci"])

            if disk_path and os.path.exists(disk_path):
                cmd.extend(["-drive", f"id=MacHDD,if=none,file={disk_path},format={disk_format}", "-device", "ide-hd,bus=sata.4,drive=MacHDD"])
            iso_path = vm.get("iso_path")
            if iso_path and os.path.exists(iso_path):
                cmd.extend(["-drive", f"id=InstallMedia,if=none,file={iso_path},format=raw", "-device", "ide-hd,bus=sata.3,drive=InstallMedia"])

            cmd.extend(["-device", "ich9-intel-hda", "-device", "hda-duplex", "-device", "vmware-svga"])
            cmd.extend(["-netdev", "user,id=net0,hostfwd=tcp::2222-:22"])
            if any(v in vm.get("version", "") for v in ["High Sierra", "Mojave", "Catalina"]):
                cmd.extend(["-device", "vmxnet3,netdev=net0,id=net0,mac=52:54:00:c9:18:27"])
            else:
                cmd.extend(["-device", "virtio-net-pci,netdev=net0,id=net0,mac=52:54:00:c9:18:27"])

            cmd.extend(["-device", "qemu-xhci,id=xhci", "-device", "usb-kbd,bus=xhci.0", "-device", "usb-tablet,bus=xhci.0", "-boot", "menu=on"])
            qmp_socket = f"/tmp/qemu-{vm['id']}-qmp.sock"
            if os.path.exists(qmp_socket):
                try: os.remove(qmp_socket)
                except: pass
            vm["qmp_socket"] = qmp_socket
            cmd.extend(["-qmp", f"unix:{qmp_socket},server,nowait"])

            vnc_port = self._find_free_vnc_port()
            vm["vnc_port"] = vnc_port
            cmd.extend(["-vnc", f"127.0.0.1:{vnc_port - 5900}"])
            vm["_pending_external_viewer"] = None
            return cmd

        if disk_path and os.path.exists(disk_path):
            disk_bus = vm.get("disk_bus", "sata").lower()
            opts = [f"file={disk_path},format={disk_format}"]
            if "none" in vm.get("disk_cache", ""): opts.append("cache=none")
            if "native" in vm.get("disk_aio", ""): opts.append("aio=native")
            
            opts_str = ",".join(opts)
            
            if "nvme" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "nvme,serial=1234,drive=disk0"])
            elif "virtio-scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "virtio-scsi-pci,id=scsi0", "-device", "scsi-hd,drive=disk0,bus=scsi0.0"])
            elif "virtio" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=virtio"])
            elif "scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "lsi53c895a,id=scsi0", "-device", "scsi-hd,drive=disk0,bus=scsi0.0"])
            elif "ide" in disk_bus and not q35:
                cmd.extend(["-drive", f"{opts_str},if=ide"])
            else:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0", "-device", "ahci,id=ahci", "-device", "ide-hd,drive=disk0,bus=ahci.0"])

        cmd.extend(self._build_cdrom_args(vm, q35))
        if vm.get("iso_path"):
            cmd.extend(["-boot", "order=d,menu=on"])

        for i, net in enumerate(vm.get("network_adapters", []) or [{"model": "VirtIO"}]):
            dev_model = "virtio-net-pci"
            if "e1000" in net.get("model", "").lower(): dev_model = "e1000"
            elif "vmxnet3" in net.get("model", "").lower(): dev_model = "vmxnet3"
            cmd.extend(["-netdev", f"user,id=net{i}", "-device", f"{dev_model},netdev=net{i}"])

        cmd.extend(self._build_graphics_device_args(vm))
        proto_args, external_info = self._build_display_protocol_args(vm)
        cmd.extend(proto_args)
        vm["_pending_external_viewer"] = external_info

        cmd.extend(["-device", "qemu-xhci,id=xhci", "-device", "usb-tablet,bus=xhci.0"])
        cmd.extend(["-device", "intel-hda", "-device", "hda-duplex"])
        cmd.extend(self._build_passthrough_args(vm))

        qmp_socket = f"/tmp/qemu-{vm['id']}-qmp.sock"
        if os.path.exists(qmp_socket):
            try: os.remove(qmp_socket)
            except: pass
        vm["qmp_socket"] = qmp_socket
        cmd.extend(["-qmp", f"unix:{qmp_socket},server,nowait"])

        return cmd

    def start_vm(self, vm: Dict) -> subprocess.Popen:
        vm_id = vm.get("id", "unknown")
        if vm_id in self.active_processes: return self.active_processes[vm_id]
        cmd = self.build_command(vm)
        log.info(f"Comando QEMU: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
            time.sleep(1.5)
            if process.poll() is not None:
                stdout, _ = process.communicate()
                raise RuntimeError(f"QEMU falló al arrancar: {stdout.strip()}")
            self.active_processes[vm_id] = process
            ext_info = vm.pop("_pending_external_viewer", None)
            if ext_info:
                viewer = self._launch_external_viewer(vm_id, ext_info)
                if viewer: self.active_viewers[vm_id] = viewer
            return process
        except Exception as e:
            log.error(f"Error lanzando QEMU: {e}")
            raise

    def _qmp_command(self, vm_id, command):
        qmp_socket = f"/tmp/qemu-{vm_id}-qmp.sock"
        if not os.path.exists(qmp_socket): return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(qmp_socket)
                s.recv(4096)
                s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode() + b'\n')
                s.recv(4096)
                s.sendall(json.dumps({"execute": command}).encode() + b'\n')
                s.recv(4096)
                return True
        except Exception as e:
            log.warning(f"No se pudo enviar comando QMP {command} a {vm_id}: {e}")
            return False

    def change_iso(self, vm_id: str, iso_path: str) -> bool:
        if not os.path.exists(iso_path): return False
        return self._qmp_command(vm_id, "blockdev-change-medium", {"device": "cdrom0", "filename": iso_path, "format": "raw"}) if hasattr(self, "_qmp_command") else False

    def stop_vm(self, vm_id: str):
        self._kill_external_viewer(vm_id)
        process = self.active_processes.get(vm_id)
        if process:
            if not self._qmp_command(vm_id, "system_powerdown"): process.terminate()
            try: process.wait(timeout=15)
            except: process.kill()
            del self.active_processes[vm_id]

    def force_stop_vm(self, vm_id: str):
        self._kill_external_viewer(vm_id)
        process = self.active_processes.get(vm_id)
        if process:
            process.kill()
            del self.active_processes[vm_id]

    def pause_vm(self, vm_id: str):
        if not self._qmp_command(vm_id, "stop"):
            if process := self.active_processes.get(vm_id): process.send_signal(19)

    def resume_vm(self, vm_id: str):
        if not self._qmp_command(vm_id, "cont"):
            if process := self.active_processes.get(vm_id): process.send_signal(18)