# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Persistencia de configuración de cada VM: dónde vive, y cómo se guarda
y se lee su vm_config.ini.

BASE_VM_DIR es la única fuente de verdad de dónde viven las VMs; otros
módulos que necesiten esa ruta deben importarla de aquí, no redefinirla.
"""
import os
import re
import json
import shutil
import shlex
import glob
import zipfile
import configparser
import subprocess
import uuid
import time
from datetime import date, timedelta
import requests
from packaging import version

BASE_VM_DIR = os.path.join(os.getcwd(), "VirtualMachines")


def vm_folder_name(name: str) -> str:
    """Única regla nombre de VM -> nombre de carpeta.

    Solo se reemplazan los caracteres que el sistema de archivos no admite
    (los mismos que start_installation rechaza). Paréntesis, acentos, ñ, etc.
    se conservan, así todos los flujos apuntan a la misma carpeta."""
    return re.sub(r'[\\/:*?"<>|]', "_", str(name or "")).strip() or "VM"


def list_existing_vms(base_dir: str = BASE_VM_DIR) -> list:
    """Devuelve los nombres de las carpetas bajo base_dir que contienen
    un vm_config.ini válido (es decir, VMs creadas previamente)."""
    vms = []
    if os.path.isdir(base_dir):
        for entry in sorted(os.listdir(base_dir)):
            vm_path = os.path.join(base_dir, entry)
            if os.path.isdir(vm_path) and os.path.isfile(os.path.join(vm_path, "vm_config.ini")):
                vms.append(entry)
    return vms



def get_os_profile(os_type, version_name="", distro=""):
    """Perfil base del SO: concentra defaults de hardware sin crear ramas por distro."""
    if os_type == "macos":
        return {"id":"macos-osxkvm", "label":f"macOS — {version_name or 'OSX-KVM'}", "firmware":"uefi", "chipset":"q35", "secure_boot":False, "tpm":False, "cpu":"Penryn/Skylake según versión", "disk":"SATA/AHCI", "network":"e1000/OSX-KVM", "graphics":"Automático / OSX-KVM", "sharing":"SMB (recomendado)"}
    if os_type == "windows":
        win11=str(version_name).lower().startswith("windows 11")
        return {"id":"windows-11" if win11 else "windows-10", "label":"Windows 11" if win11 else "Windows 10", "firmware":"uefi", "chipset":"q35", "secure_boot":win11, "tpm":win11, "cpu":"host", "disk":"VirtIO/SATA", "network":"VirtIO", "graphics":"VGA estándar QEMU", "sharing":"SMB"}
    if os_type == "android":
        return {
            "id": "android-x86",
            "label": f"Android \u2014 {version_name or 'Android-x86 / Bliss OS'}",
            "firmware": "bios",
            "chipset": "q35",
            "secure_boot": False,
            "tpm": False,
            "cpu": "host",
            "disk": "SATA/AHCI",
            "network": "e1000",
            "graphics": "Autom\u00e1tico / Red Hat QXL 2D",
            "sharing": "9p",
        }
    distro=distro or "Linux"
    return {"id":"linux-modern", "label":f"Linux moderno — {distro}", "firmware":"uefi", "chipset":"q35", "secure_boot":False, "tpm":False, "cpu":"host", "disk":"VirtIO/SATA", "network":"VirtIO", "graphics":"Automático / VirtIO-GPU", "sharing":"VirtioFS → 9p"}


def save_vm_config(vm_dir, name, os_type, ram, cores, disk_size, disk_type, disk_format, disk_ext, extra_params, firmware="bios", secure_boot=False, tpm=False, boot_device="cdrom", network_model="virtio-net-pci", audio_device="intel-hda", network_mode="nat", network_interface="", network_count=1, graphics_mode="auto", graphics_vram="256M", boot_order=None, network_devices=None, passthrough_devices=None, chipset="pc", log_func=None):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg["general"] = {"name": name, "os_type": os_type}
    cfg["hardware"] = {
        "ram": ram,
        "cores": str(cores),
        "disk_size": disk_size,
        "disk_type": disk_type,
        "disk_format": disk_format,
        "disk_ext": disk_ext,
        "firmware": firmware,
        "chipset": chipset or "pc",
        "secure_boot": str(bool(secure_boot)),
        "tpm": str(bool(tpm)),
        "boot_device": boot_device,
        "boot_order": json.dumps(boot_order or ["cdrom", "disk", "network"]),
        "network_model": network_model,
        "audio_device": audio_device,
        "network_mode": network_mode,
        "network_interface": network_interface,
        "network_count": str(int(network_count or 1)),
        "graphics_mode": graphics_mode or "auto",
        "graphics_vram": graphics_vram or "256M",
        "network_devices": json.dumps(network_devices or []),
        "passthrough_devices": json.dumps(passthrough_devices or []),
    }
    # No sobrescribir dispositivos de almacenamiento existentes por datos antiguos de la UI.
    try:
        existing_path = os.path.join(vm_dir, "vm_config.ini")
        if os.path.isfile(existing_path):
            old_cfg = configparser.ConfigParser(interpolation=None)
            old_cfg.read(existing_path, encoding="utf-8")
            if old_cfg.has_section("extra"):
                old_extra = json.loads(old_cfg["extra"].get("data", "{}"))
                if not isinstance(extra_params.get("storage_devices"), list) and isinstance(old_extra.get("storage_devices"), list):
                    extra_params["storage_devices"] = old_extra["storage_devices"]
    except Exception as e:
        if log_func:
            log_func(f"[AVISO] No se pudo fusionar la configuración anterior de '{name}': {e}")
    cfg["extra"] = {"data": json.dumps(extra_params, ensure_ascii=False)}
    with open(os.path.join(vm_dir, "vm_config.ini"), "w", encoding="utf-8") as f:
        cfg.write(f)


def load_vm_config(vm_dir: str) -> dict:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(os.path.join(vm_dir, "vm_config.ini"))
    general = cfg["general"]
    hardware = cfg["hardware"]
    extra = json.loads(cfg["extra"].get("data", "{}")) if cfg.has_section("extra") else {}
    return {
        "name": general.get("name"),
        "os_type": general.get("os_type"),
        "ram": hardware.get("ram"),
        "cores": hardware.get("cores"),
        "disk_size": hardware.get("disk_size"),
        "disk_type": hardware.get("disk_type"),
        "disk_format": hardware.get("disk_format"),
        "disk_ext": hardware.get("disk_ext"),
        "firmware": hardware.get("firmware", "bios"),
        "chipset": hardware.get("chipset", "pc"),
        "secure_boot": hardware.get("secure_boot", "False").lower() == "true",
        "tpm": hardware.get("tpm", "False").lower() == "true",
        "boot_device": hardware.get("boot_device", "cdrom"),
        "boot_order": json.loads(hardware.get("boot_order", '["cdrom", "disk", "network"]')),
        "network_model": hardware.get("network_model", "virtio-net-pci"),
        "audio_device": hardware.get("audio_device", "intel-hda"),
        "network_mode": hardware.get("network_mode", "nat"),
        "network_interface": hardware.get("network_interface", ""),
        "network_count": hardware.getint("network_count", fallback=1),
        "graphics_mode": hardware.get("graphics_mode", "auto"),
        "graphics_vram": hardware.get("graphics_vram", "256M"),
        "network_devices": json.loads(hardware.get("network_devices", "[]")),
        "passthrough_devices": json.loads(hardware.get("passthrough_devices", "[]")),
        "extra": extra,
    }


