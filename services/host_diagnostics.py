import os
import shutil
import subprocess
import logging
from typing import List, Dict, Any

log = logging.getLogger(__name__)

class HostDiagnostics:
    def run_all(self) -> List[Dict[str, Any]]:
        checks = []
        
        # --- 1. Virtualización Básica ---
        checks.append({"cat": "Virtualización", "name": "QEMU", "st": "ok" if shutil.which("qemu-system-x86_64") else "err", "desc": shutil.which("qemu-system-x86_64") or "No instalado"})
        checks.append({"cat": "Virtualización", "name": "KVM (/dev/kvm)", "st": "ok" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "err", "desc": "/dev/kvm accesible" if os.path.exists("/dev/kvm") else "No existe"})
        checks.append({"cat": "Virtualización", "name": "Firmware UEFI (OVMF)", "st": "ok" if os.path.exists("/usr/share/edk2/x64/OVMF_CODE.fd") or os.path.exists("/usr/share/OVMF/OVMF_CODE.fd") else "warn", "desc": "Encontrado"})
        checks.append({"cat": "Virtualización", "name": "TPM 2.0 (swtpm)", "st": "ok" if shutil.which("swtpm") else "warn", "desc": shutil.which("swtpm") or "No instalado"})
        checks.append({"cat": "Virtualización", "name": "Módulos VirtIO", "st": "ok" if os.path.exists("/sys/module/virtio") else "warn", "desc": "Presentes" if os.path.exists("/sys/module/virtio") else "No cargados"})
        checks.append({"cat": "Virtualización", "name": "Audio del host", "st": "ok" if shutil.which("pactl") or shutil.which("pipewire") else "warn", "desc": "PulseAudio/PipeWire detectado"})

        # --- 2. Python Dependencies ---
        checks.append({"cat": "Python", "name": "PyQt6", "st": "ok", "desc": "Instalado"})
        checks.append({"cat": "Python", "name": "requests", "st": "ok", "desc": "Instalado"})
        checks.append({"cat": "Python", "name": "packaging", "st": "ok", "desc": "Instalado"})
        checks.append({"cat": "Python", "name": "polkit / pkexec", "st": "ok" if shutil.which("pkexec") else "warn", "desc": shutil.which("pkexec") or "No instalado"})
        checks.append({"cat": "Python", "name": "udev / udevadm", "st": "ok" if shutil.which("udevadm") else "warn", "desc": shutil.which("udevadm") or "No instalado"})

        # --- 3. Consola (VNC / SPICE) ---
        checks.append({"cat": "Consola", "name": "Cliente VNC embebido", "st": "ok", "desc": "vnc_widget importable"})
        checks.append({"cat": "Consola", "name": "Spice-gtk (binding Python)", "st": "ok" if shutil.which("spicy") else "warn", "desc": "Disponible" if shutil.which("spicy") else "No instalado"})
        checks.append({"cat": "Consola", "name": "Visor VNC externo", "st": "ok" if shutil.which("vncviewer") else "warn", "desc": shutil.which("vncviewer") or "No instalado"})
        checks.append({"cat": "Consola", "name": "Visor SPICE externo", "st": "ok" if shutil.which("remote-viewer") else "warn", "desc": shutil.which("remote-viewer") or "No instalado"})

        # --- 4. Compartición ---
        checks.append({"cat": "Compartición", "name": "VirtioFSD", "st": "ok" if shutil.which("virtiofsd") else "warn", "desc": shutil.which("virtiofsd") or "No instalado"})
        checks.append({"cat": "Compartición", "name": "Samba (smbd)", "st": "ok" if shutil.which("smbd") else "warn", "desc": shutil.which("smbd") or "No instalado"})
        
        # --- 5. Passthrough ---
        checks.append({"cat": "Passthrough", "name": "IOMMU en Kernel", "st": "warn", "desc": "Requiere reinicio"})
        checks.append({"cat": "Passthrough", "name": "Grupos IOMMU", "st": "warn", "desc": "Sin grupos visibles"})
        checks.append({"cat": "Passthrough", "name": "Regla udev udmabuf", "st": "ok" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/60-virtual-machine-udmabuf.rules") else "Falta"})
        checks.append({"cat": "Passthrough", "name": "Regla udev USB", "st": "ok" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "warn", "desc": "Instalada" if os.path.exists("/etc/udev/rules.d/50-vm-manager-usb.rules") else "Falta"})

        # --- 6. Modo Kiosco ---
        checks.append({"cat": "Modo Kiosco", "name": "Xorg", "st": "ok" if shutil.which("Xorg") else "warn", "desc": "Instalado"})
        checks.append({"cat": "Modo Kiosco", "name": "xinit", "st": "ok" if shutil.which("xinit") else "warn", "desc": "Instalado"})
        checks.append({"cat": "Modo Kiosco", "name": "matchbox-window-manager", "st": "warn", "desc": "No encontrado"})
        checks.append({"cat": "Modo Kiosco", "name": "Wrapper sudo", "st": "ok" if os.path.exists("/usr/local/bin/virtual-machine-desktop") else "warn", "desc": "Instalado"})
        checks.append({"cat": "Modo Kiosco", "name": "/etc/virtual-machine.conf", "st": "ok" if os.path.exists("/etc/virtual-machine.conf") else "warn", "desc": "Configurado"})
        checks.append({"cat": "Modo Kiosco", "name": "Regla sudoers", "st": "ok" if os.path.exists("/etc/sudoers.d/virtual-machine-desktop") else "warn", "desc": "Configurada"})
        checks.append({"cat": "Modo Kiosco", "name": "Xwrapper.config", "st": "ok" if os.path.exists("/etc/X11/Xwrapper.config") else "warn", "desc": "Configurado"})

        return checks
