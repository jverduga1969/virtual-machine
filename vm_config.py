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

# portable_paths_v1: BASE_VM_DIR se ancla a la ubicación de este módulo,
# no a os.getcwd(). Antes, si la app se lanzaba desde otro directorio (o
# vía un .desktop con Path= distinto), las VMs "desaparecían" de la lista.
# La variable de entorno VM_BASE_DIR permite override si el usuario tiene
# sus VMs en otro sitio.
_HERE = os.path.dirname(os.path.abspath(__file__))
_LEGACY_BASE_VM_DIR = os.path.join(os.getcwd(), "VirtualMachines")


def _resolve_base_vm_dir() -> str:
    """Devuelve la carpeta donde viven las VMs.

    Marcador: xdg_base_dir_v1.

    Orden de prioridad:
      1. Variable de entorno VM_BASE_DIR (override manual).
      2. Modo desarrollo: si el directorio del modulo es escribible y no
         esta bajo /usr/, usa <modulo>/VirtualMachines/ (comportamiento
         historico, util cuando se clona el repo).
      3. Modo paquete (AUR/distro): si el modulo esta instalado en /usr/
         o el directorio no es escribible, usa
         $XDG_DATA_HOME/virtual-machine/VirtualMachines/ o su defecto
         ~/.local/share/virtual-machine/VirtualMachines/.
    """
    env = os.environ.get("VM_BASE_DIR")
    if env:
        return env

    # Modo paquete: instalado en /usr/ o directorio no escribible.
    if _HERE.startswith("/usr/") or not os.access(_HERE, os.W_OK):
        xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return os.path.join(xdg, "virtual-machine", "VirtualMachines")

    # Modo desarrollo (repo clonado).
    return os.path.join(_HERE, "VirtualMachines")


BASE_VM_DIR = _resolve_base_vm_dir()


def legacy_base_vm_dir_warning():
    """Aviso si detectamos VMs en un VirtualMachines/ heredado del cwd.

    Caso típico: al arrancar la app desde otro directorio, las VMs creadas
    con la versión antigua quedaron en un VirtualMachines/ distinto al que
    ahora se usa. Este helper devuelve (mensaje, ruta_legacy) para que la
    app pueda avisar al usuario, o (None, None) si no hay nada que avisar.

    portable_paths_v1
    """
    if os.environ.get("VM_BASE_DIR"):
        return (None, None)
    try:
        legacy_abs = os.path.abspath(_LEGACY_BASE_VM_DIR)
        base_abs = os.path.abspath(BASE_VM_DIR)
    except Exception:
        return (None, None)
    if legacy_abs == base_abs:
        return (None, None)
    if not os.path.isdir(legacy_abs):
        return (None, None)
    try:
        entries = os.listdir(legacy_abs)
    except OSError:
        return (None, None)
    has_real_vms = any(
        os.path.isfile(os.path.join(legacy_abs, e, "vm_config.ini"))
        for e in entries
    )
    if not has_real_vms:
        return (None, None)
    try:
        new_has_vms = any(
            os.path.isfile(os.path.join(base_abs, e, "vm_config.ini"))
            for e in os.listdir(base_abs)
        )
    except (OSError, FileNotFoundError):
        new_has_vms = False
    if new_has_vms:
        return (None, None)
    return (
        f"Se detectaron VMs en {legacy_abs} pero la app ahora las busca "
        f"en {base_abs}. Mueve tus VMs o arranca con "
        f"VM_BASE_DIR='{legacy_abs}'",
        legacy_abs,
    )


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


