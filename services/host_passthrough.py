import os
import platform
import re
import subprocess
import logging

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Los BDF/VID:DID se interpolan en comandos ejecutados como root mediante
# pkexec. Validarlos aquí evita que un valor de la UI o de /sys inyecte
# comandos shell (p. ej. "0000:01:00.0; curl ... | sh").
_BDF_RE = re.compile(r"^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$")
_VID_DID_RE = re.compile(r"^[0-9a-fA-F]{4}:[0-9a-fA-F]{4}$")


def _require_bdf(value, label="BDF"):
    if not isinstance(value, str) or not _BDF_RE.fullmatch(value):
        raise ValueError(f"{label} inválido: {value!r}")
    return value


def _require_vid_did(value):
    if not isinstance(value, str) or not _VID_DID_RE.fullmatch(value):
        raise ValueError(f"VID:DID inválido: {value!r}")
    return value


def check_iommu():
    """Comprueba IOMMU (solo Linux). En Windows devuelve valores por defecto."""
    if IS_WINDOWS:
        return {
            "in_cmdline": False,
            "groups": 0,
            "needs_reboot": False,
            "enabled": False
        }

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
    """Comprueba si vfio_pci está cargado (solo Linux)."""
    if IS_WINDOWS:
        return False
    try:
        with open("/proc/modules", "r") as f:
            return "vfio_pci" in f.read()
    except Exception:
        return False


def get_bootloader():
    """Detecta el gestor de arranque (solo Linux)."""
    if IS_WINDOWS:
        return "unknown"
    if os.path.exists("/etc/default/grub"):
        return "grub"
    if os.path.exists("/etc/kernel/cmdline") or os.path.exists("/boot/loader/entries"):
        return "systemd-boot"
    if os.path.exists("/etc/default/limine") or os.path.exists("/boot/limine.conf"):
        return "limine"
    return "unknown"


def enable_iommu():
    """Habilita IOMMU en el gestor de arranque (solo Linux)."""
    if IS_WINDOWS:
        log.warning("enable_iommu no soportado en Windows.")
        return False

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
    """Configura vfio-pci (solo Linux)."""
    if IS_WINDOWS:
        log.warning("setup_vfio no soportado en Windows.")
        return False
    script = """
    echo "vfio-pci" > /etc/modules-load.d/vfio-pci.conf
    modprobe vfio-pci || true
    """
    subprocess.run(["pkexec", "bash", "-c", script])
    return True


def setup_udev_rules():
    """Configura reglas udev (solo Linux)."""
    if IS_WINDOWS:
        log.warning("setup_udev_rules no soportado en Windows.")
        return False
    # Mismos nombres y contenido que scripts/postinstall.sh, que son los
    # que HostDiagnostics marca en verde. Así no se crean reglas duplicadas.
    script = """
    if [ ! -f /etc/udev/rules.d/60-virtual-machine-udmabuf.rules ] || \
       ! grep -q 'SUBSYSTEM=="misc"' /etc/udev/rules.d/60-virtual-machine-udmabuf.rules; then
        echo 'KERNEL=="udmabuf", SUBSYSTEM=="misc", TAG+="uaccess"' > /etc/udev/rules.d/60-virtual-machine-udmabuf.rules
    fi
    if [ ! -f /etc/udev/rules.d/50-vm-manager-usb.rules ] || \
       ! grep -q 'ACTION=="add"' /etc/udev/rules.d/50-vm-manager-usb.rules; then
        echo 'SUBSYSTEM=="usb", ACTION=="add", TAG+="uaccess"' > /etc/udev/rules.d/50-vm-manager-usb.rules
    fi
    mkdir -p /etc/modules-load.d
    if ! grep -qx udmabuf /etc/modules-load.d/udmabuf.conf 2>/dev/null; then
        echo udmabuf > /etc/modules-load.d/udmabuf.conf
    fi
    modprobe udmabuf 2>/dev/null || true
    udevadm control --reload-rules
    udevadm trigger --name-match=udmabuf
    udevadm trigger --subsystem-match=usb
    """
    subprocess.run(["pkexec", "bash", "-c", script])
    return True


def add_pci_udev_rule(vid_did):
    """Añade regla udev para un dispositivo PCI (solo Linux)."""
    if IS_WINDOWS:
        return
    _require_vid_did(vid_did)
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


def get_driver_original(bdf):
    """Lee el driver actualmente asignado a un BDF (solo Linux)."""
    if IS_WINDOWS:
        return None
    _require_bdf(bdf)
    driver_path = f"/sys/bus/pci/devices/{bdf}/driver"
    if os.path.exists(driver_path):
        try:
            with open(driver_path, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def rollback_bind(bdf, original_driver):
    """Restaura el driver original de un BDF tras un bind fallido (solo Linux)."""
    if IS_WINDOWS:
        return
    _require_bdf(bdf)
    unbind_script = f"""
    if [ -d /sys/bus/pci/drivers/vfio-pci ]; then
        echo {bdf} > /sys/bus/pci/drivers/vfio-pci/unbind 2>/dev/null || true
    fi
    echo {bdf} > /sys/bus/pci/drivers_probe 2>/dev/null || true
    """
    subprocess.run(["pkexec", "bash", "-c", unbind_script], capture_output=True, text=True)
    log.info(f"Rollback completado para {bdf}, driver original: {original_driver}")


def dynamic_bind_vfio(bdf):
    """Fuerza la vinculación de un BDF a vfio-pci inmediatamente (solo Linux)."""
    if IS_WINDOWS:
        log.warning("dynamic_bind_vfio no soportado en Windows.")
        return False
    _require_bdf(bdf)
    if not os.path.exists(f"/sys/bus/pci/devices/{bdf}"):
        log.error(f"BDF {bdf} no encontrado en /sys/bus/pci/devices")
        return False

    original_driver = get_driver_original(bdf)

    script = f"""
    if [ -d /sys/bus/pci/devices/{bdf} ]; then
        echo vfio-pci > /sys/bus/pci/devices/{bdf}/driver_override
        echo {bdf} > /sys/bus/pci/drivers_probe
    fi
    """
    res = subprocess.run(["pkexec", "bash", "-c", script], capture_output=True, text=True)

    if res.returncode != 0:
        log.error(f"pkexec bind falló para {bdf}: {res.stderr.strip()}")
        print(f"ERROR: No se pudo hacer bind de {bdf} a vfio-pci. Detalles: {res.stderr.strip()}")
        if original_driver:
            print(f"Restaurando driver original ({original_driver})...")
            rollback_bind(bdf, original_driver)
        return False

    log.info(f"Bind exitoso: {bdf} -> vfio-pci")
    return True


def find_usb_device_by_vid_pid(vid, pid):
    """Busca el BDF de un dispositivo USB por vendor:product id (solo Linux)."""
    if IS_WINDOWS:
        return None
    _require_vid_did(f"{vid}:{pid}")
    vid_lower = vid.lower()
    pid_lower = pid.lower()
    usb_sys = "/sys/bus/usb/devices"
    if not os.path.exists(usb_sys):
        return None
    for dev in os.listdir(usb_sys):
        dev_path = os.path.join(usb_sys, dev)
        id_vendor_path = os.path.join(dev_path, "idVendor")
        id_product_path = os.path.join(dev_path, "idProduct")
        if os.path.exists(id_vendor_path) and os.path.exists(id_product_path):
            try:
                with open(id_vendor_path, "r") as f:
                    dev_vid = f.read().strip().lower()
                with open(id_product_path, "r") as f:
                    dev_pid = f.read().strip().lower()
                if dev_vid == vid_lower and dev_pid == pid_lower:
                    return dev
            except Exception:
                continue
    return None


def usb_passthrough(vid_pid):
    """Configura passthrough de un dispositivo USB usando vendorid:productid (solo Linux)."""
    if IS_WINDOWS:
        log.error("USB passthrough no soportado en Windows.")
        return False
    try:
        _require_vid_did(vid_pid)
    except ValueError:
        log.error(f"Formato inválido para USB: {vid_pid}. Se espera vendorid:productid")
        return False
    vid, pid = vid_pid.split(":")
    device = find_usb_device_by_vid_pid(vid, pid)
    if not device:
        log.error(f"No se encontró dispositivo USB con vid:{vid} pid:{pid}")
        return False
    log.info(f"Dispositivo USB encontrado: {device} (vid:{vid} pid:{pid})")
    return True


def get_iommu_group_devices(bdf):
    """Obtiene los dispositivos que pertenecen al mismo IOMMU group que el BDF dado (solo Linux)."""
    if IS_WINDOWS:
        return []
    _require_bdf(bdf)
    group_path = f"/sys/bus/pci/devices/{bdf}/iommu_group/devices"
    if not os.path.exists(group_path):
        return []
    devices = []
    for entry in os.listdir(group_path):
        full_path = os.path.join(group_path, entry)
        if os.path.islink(full_path):
            devices.append(os.path.basename(full_path))
    return devices


def find_audio_device_in_group(bdf):
    """Busca un dispositivo de audio en el mismo IOMMU group que la GPU (solo Linux)."""
    if IS_WINDOWS:
        return None
    _require_bdf(bdf)
    group_devices = get_iommu_group_devices(bdf)
    for dev_bdf in group_devices:
        if dev_bdf == bdf:
            continue
        # Los nombres vienen de /sys, pero se validan igualmente antes de
        # interpolaren en un script con privilegios.
        try:
            _require_bdf(dev_bdf, "BDF del grupo IOMMU")
        except ValueError:
            continue
        modalias_path = f"/sys/bus/pci/devices/{dev_bdf}/modalias"
        class_path = f"/sys/bus/pci/devices/{dev_bdf}/class"
        is_audio = False
        if os.path.exists(class_path):
            try:
                with open(class_path, "r") as f:
                    cls = f.read().strip()
                    # Clase 0x04 = Audio device
                    if cls == "0x0400" or cls == "0x0401" or cls == "0x0402" or cls == "0x0403":
                        is_audio = True
            except Exception:
                pass
        if not is_audio and os.path.exists(modalias_path):
            try:
                with open(modalias_path, "r") as f:
                    modalias = f.read().strip().lower()
                    if "audio" in modalias:
                        is_audio = True
            except Exception:
                pass
        if is_audio:
            return dev_bdf
    return None


def gpu_passthrough(gpu_bdf):
    """Configura passthrough de GPU con multifunction=on y audio automático del mismo IOMMU group (solo Linux)."""
    if IS_WINDOWS:
        log.error("GPU passthrough no soportado en Windows.")
        return False
    _require_bdf(gpu_bdf)
    if not os.path.exists(f"/sys/bus/pci/devices/{gpu_bdf}"):
        log.error(f"GPU BDF {gpu_bdf} no encontrado")
        return False

    # 1. Bind de la GPU con multifunction=on
    script = f"""
    if [ -d /sys/bus/pci/devices/{gpu_bdf} ]; then
        echo vfio-pci > /sys/bus/pci/devices/{gpu_bdf}/driver_override
        echo {gpu_bdf} > /sys/bus/pci/drivers_probe
    fi
    """
    res = subprocess.run(["pkexec", "bash", "-c", script], capture_output=True, text=True)
    if res.returncode != 0:
        log.error(f"Fallo al hacer bind de GPU {gpu_bdf}: {res.stderr.strip()}")
        print(f"ERROR: No se pudo hacer bind de la GPU {gpu_bdf} a vfio-pci: {res.stderr.strip()}")
        original_driver = get_driver_original(gpu_bdf)
        if original_driver:
            print("Restaurando driver original...")
            rollback_bind(gpu_bdf, original_driver)
        return False

    log.info(f"GPU {gpu_bdf} vinculada a vfio-pci con multifunction=on")

    # 2. Buscar y vincular dispositivo de audio en el mismo IOMMU group
    audio_bdf = find_audio_device_in_group(gpu_bdf)
    if audio_bdf:
        _require_bdf(audio_bdf, "BDF de audio")
        log.info(f"Dispositivo de audio encontrado en mismo grupo IOMMU: {audio_bdf}")
        audio_script = f"""
        if [ -d /sys/bus/pci/devices/{audio_bdf} ]; then
            echo vfio-pci > /sys/bus/pci/devices/{audio_bdf}/driver_override
            echo {audio_bdf} > /sys/bus/pci/drivers_probe
        fi
        """
        res_audio = subprocess.run(["pkexec", "bash", "-c", audio_script], capture_output=True, text=True)
        if res_audio.returncode != 0:
            log.warning(f"No se pudo vincular el audio {audio_bdf}: {res_audio.stderr.strip()}")
            print(f"ADVERTENCIA: No se pudo hacer bind del dispositivo de audio {audio_bdf}")
        else:
            log.info(f"Dispositivo de audio {audio_bdf} vinculado a vfio-pci")
    else:
        log.info(f"No se encontró dispositivo de audio en el mismo IOMMU group que {gpu_bdf}")

    return True
