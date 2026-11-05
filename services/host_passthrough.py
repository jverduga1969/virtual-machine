import os
import subprocess
import logging

log = logging.getLogger(__name__)

def check_iommu():
    in_cmdline = False
    try:
        with open("/proc/cmdline", "r") as f:
            cmdline = f.read()
            if "amd_iommu=on" in cmdline or "intel_iommu=on" in cmdline or "iommu=pt" in cmdline:
                in_cmdline = True
    except Exception:
        pass

    groups = 0
    if os.path.exists("/sys/kernel/iommu_groups"):
        groups = len([d for d in os.listdir("/sys/kernel/iommu_groups") if os.path.isdir(os.path.join("/sys/kernel/iommu_groups", d))])

    return {
        "in_cmdline": in_cmdline,
        "groups": groups,
        "needs_reboot": in_cmdline and groups == 0,
        "enabled": in_cmdline and groups > 0
    }

def check_vfio():
    try:
        with open("/proc/modules", "r") as f:
            return "vfio_pci" in f.read()
    except Exception:
        return False

def get_bootloader():
    if os.path.exists("/etc/default/grub"):
        return "grub"
    if os.path.exists("/etc/kernel/cmdline") or os.path.exists("/boot/loader/entries"):
        return "systemd-boot"
    if os.path.exists("/etc/default/limine") or os.path.exists("/boot/limine.conf"):
        return "limine"
    return "unknown"

def enable_iommu():
    bl = get_bootloader()
    cmdline_arg = "amd_iommu=on iommu=pt"
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo", "r") as f:
                if "GenuineIntel" in f.read():
                    cmdline_arg = "intel_iommu=on iommu=pt"
        except Exception:
            pass

    if bl == "grub":
        script = f"""
        if ! grep -q '{cmdline_arg}' /etc/default/grub; then
            if grep -q 'GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub; then
                sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\\([^"]*\\)"/GRUB_CMDLINE_LINUX_DEFAULT="\\1 {cmdline_arg}"/' /etc/default/grub
            else
                echo 'GRUB_CMDLINE_LINUX_DEFAULT="{cmdline_arg}"' >> /etc/default/grub
            fi
            grub-mkconfig -o /boot/grub/grub.cfg
        fi
        """
        subprocess.run(["pkexec", "bash", "-c", script])
        return True
    elif bl == "systemd-boot":
        script = f"""
        if [ -f /etc/kernel/cmdline ]; then
            if ! grep -q '{cmdline_arg}' /etc/kernel/cmdline; then
                echo " {cmdline_arg}" >> /etc/kernel/cmdline
                bootctl update
            fi
        fi
        """
        subprocess.run(["pkexec", "bash", "-c", script])
        return True
    elif bl == "limine":
        script = f"""
        if [ -f /etc/default/limine ]; then
            if ! grep -q '{cmdline_arg}' /etc/default/limine; then
                echo 'KERNEL_CMDLINE[default]+="{cmdline_arg}"' >> /etc/default/limine
                limine-update || true
            fi
        fi
        """
        subprocess.run(["pkexec", "bash", "-c", script])
        return True
    return False

def setup_vfio():
    script = """
    echo "vfio-pci" > /etc/modules-load.d/vfio-pci.conf
    modprobe vfio-pci || true
    """
    subprocess.run(["pkexec", "bash", "-c", script])
    return True

def setup_udev_rules():
    script = """
    if [ ! -f /etc/udev/rules.d/99-udmabuf.rules ]; then
        echo 'KERNEL=="udmabuf", SUBSYSTEM=="misc", TAG+="uaccess"' > /etc/udev/rules.d/99-udmabuf.rules
    fi
    if [ ! -f /etc/udev/rules.d/99-qemu-usb.rules ]; then
        echo 'SUBSYSTEM=="usb", TAG+="uaccess"' > /etc/udev/rules.d/99-qemu-usb.rules
    fi
    udevadm control --reload-rules
    udevadm trigger
    """
    subprocess.run(["pkexec", "bash", "-c", script])
    return True

def add_pci_udev_rule(vid_did):
    if not vid_did or ":" not in vid_did:
        return
    vid, did = vid_did.split(":")
    rule_path = f"/etc/udev/rules.d/99-vfio-{vid}-{did}.rules"
    if os.path.exists(rule_path):
        return
        
    content = f'ACTION=="add", SUBSYSTEM=="pci", ATTR{{vendor}}=="0x{vid}", ATTR{{device}}=="0x{did}", ATTR{{driver_override}}="vfio-pci"'
    script = f"""
    echo '{content}' > {rule_path}
    udevadm control --reload-rules
    udevadm trigger
    """
    subprocess.run(["pkexec", "bash", "-c", script])

def dynamic_bind_vfio(bdf):
    """Fuerza la vinculación de un BDF a vfio-pci inmediatamente.
    Devuelve True si tuvo éxito, False si falló o el usuario canceló.
    """
    script = f"""
    if [ -d /sys/bus/pci/devices/{bdf} ]; then
        echo vfio-pci > /sys/bus/pci/devices/{bdf}/driver_override
        echo {bdf} > /sys/bus/pci/drivers_probe
    fi
    """
    res = subprocess.run(["pkexec", "bash", "-c", script])
    return res.returncode == 0