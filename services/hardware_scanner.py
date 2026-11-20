import os
import platform
import logging

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def scan_pci_devices():
    """Lee los dispositivos PCI reales de /sys/bus/pci/devices/ (solo Linux)."""
    if IS_WINDOWS:
        # En Windows no existe /sys/bus/pci; devolver lista vacía
        return []
    devices = []
    pci_path = "/sys/bus/pci/devices"
    if not os.path.exists(pci_path):
        return devices

    for dev_id in os.listdir(pci_path):
        dev_dir = os.path.join(pci_path, dev_id)
        try:
            with open(os.path.join(dev_dir, "vendor"), "r") as f:
                vendor = f.read().strip()
            with open(os.path.join(dev_dir, "device"), "r") as f:
                device = f.read().strip()

            # Formato: 8086:1234
            full_id = f"{vendor.replace('0x','')}:{device.replace('0x','')}"

            # Comprobar grupo IOMMU
            iommu_group = "Sin grupo IOMMU"
            if os.path.exists(os.path.join(dev_dir, "iommu_group")):
                group_num = os.path.basename(os.readlink(os.path.join(dev_dir, "iommu_group")))
                iommu_group = f"Grupo {group_num}"

            devices.append({
                "type": "PCI",
                "id": full_id,
                "desc": f"PCI {full_id}",
                "iommu": iommu_group,
                "status": "Listo" if iommu_group != "Sin grupo IOMMU" else "Falta IOMMU"
            })
        except Exception:
            continue
    return devices


def scan_usb_devices():
    """Lee los dispositivos USB reales de /sys/bus/usb/devices/ (solo Linux)."""
    if IS_WINDOWS:
        return []
    devices = []
    usb_path = "/sys/bus/usb/devices"
    if not os.path.exists(usb_path):
        return devices

    for dev_id in os.listdir(usb_path):
        dev_dir = os.path.join(usb_path, dev_id)
        try:
            vendor_path = os.path.join(dev_dir, "idVendor")
            product_path = os.path.join(dev_dir, "idProduct")
            if not os.path.exists(vendor_path) or not os.path.exists(product_path):
                continue

            with open(vendor_path, "r") as f:
                vendor = f.read().strip()
            with open(product_path, "r") as f:
                product = f.read().strip()

            full_id = f"{vendor}:{product}"

            # Intentar leer el nombre
            name = "Dispositivo USB"
            prod_name = os.path.join(dev_dir, "product")
            if os.path.exists(prod_name):
                with open(prod_name, "r") as f:
                    name = f.read().strip()

            devices.append({
                "type": "USB",
                "id": full_id,
                "desc": f"{name} ({full_id})",
                "iommu": "N/A",
                "status": "Listo"
            })
        except Exception:
            continue
    return devices
