# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
"""Importacion / exportacion OVF / OVA (marcador ovf_ova_io_v1).

Modulo puro (sin PyQt): construye y parsea descriptores OVF, empaqueta y
desempaqueta OVA (tar sin comprimir, por spec DMTF DSP0243) y mapea entre
el modelo OVF y el vm_config.ini de esta aplicacion.

La metadata propia (grupo, color, notas, schedules...) viaja dentro del
OVA como archivo ".virtmachine.json", que los hipervisores de terceros
ignoran pero que esta app lee al reimportar.
"""

import os
import re
import json
import shutil
import hashlib
import subprocess
import tarfile
import tempfile
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime


# --- Namespaces DMTF --------------------------------------------------------
NS_OVF  = "http://schemas.dmtf.org/ovf/envelope/1"
NS_RASD = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"
NS_VSSD = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData"
NS_VBOX = "http://www.virtualbox.org/ovf/machine"
NS_VMW  = "http://www.vmware.com/schema/ovf"

for _p, _ns in (("ovf", NS_OVF), ("rasd", NS_RASD), ("vssd", NS_VSSD),
                ("vbox", NS_VBOX), ("vmw", NS_VMW)):
    ET.register_namespace(_p, _ns)

VIRTMACHINE_META = ".virtmachine.json"
# ovf_ova_io_v1_rev2
# ovf_ova_io_v1_cdrom
# ovf_ova_io_v1_annotation
# ovf_io_space_guard_v1
# ovf_ova_io_v1_vbox_tar_ustar
# ovf_ova_vbox_uefi_v1
# ovf_io_tar_sparse_v1
OVF_DESCRIPTOR_NAME = "descriptor.ovf"
MANIFEST_NAME = "manifest.mf"


def _localname(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag

def _iter_local(root, name):
    for c in root.iter():
        if _localname(c.tag) == name:
            yield c

def _first_local(root, name):
    for c in _iter_local(root, name): return c
    return None

def _text_local(root, name, default=""):
    c = _first_local(root, name)
    if c is None or c.text is None: return default
    return c.text.strip()


# --- Mapeo ostype VirtualBox <-> (os_type, distro/version) -----------------
_VBOX_OSTYPE_MAP = {
    "ubuntu": ("linux", "Ubuntu"), "ubuntu_64": ("linux", "Ubuntu"),
    "debian": ("linux", "Debian"), "debian_64": ("linux", "Debian"),
    "fedora": ("linux", "Fedora"), "fedora_64": ("linux", "Fedora"),
    "linux26": ("linux", ""), "linux26_64": ("linux", ""),
    "linuxmint": ("linux", "Linux Mint"), "linuxmint_64": ("linux", "Linux Mint"),
    "opensuse": ("linux", "openSUSE"), "opensuse_64": ("linux", "openSUSE"),
    "archlinux": ("linux", "Arch Linux"), "archlinux_64": ("linux", "Arch Linux"),
    "manjaro": ("linux", "Manjaro Linux"), "manjaro_64": ("linux", "Manjaro Linux"),
    "kali": ("linux", "Kali Linux"), "kali_64": ("linux", "Kali Linux"),
    "almalinux": ("linux", "AlmaLinux"), "almalinux_64": ("linux", "AlmaLinux"),
    "rocky": ("linux", "Rocky Linux"), "rocky_64": ("linux", "Rocky Linux"),
    "popos": ("linux", "Pop!_OS"), "popos_64": ("linux", "Pop!_OS"),
    "elementary": ("linux", "elementary OS"), "elementary_64": ("linux", "elementary OS"),
    "zorin": ("linux", "Zorin OS"), "zorin_64": ("linux", "Zorin OS"),
    "mx": ("linux", "MX Linux"), "mx_64": ("linux", "MX Linux"),
    "solus": ("linux", "Solus"), "solus_64": ("linux", "Solus"),
    "alpine": ("linux", "Alpine Linux"), "alpine_64": ("linux", "Alpine Linux"),
    "void": ("linux", "Void Linux"), "void_64": ("linux", "Void Linux"),
    "win10": ("windows", "Windows 10"), "win10_64": ("windows", "Windows 10"),
    "windows10": ("windows", "Windows 10"), "windows10_64": ("windows", "Windows 10"),
    "win11": ("windows", "Windows 11"), "win11_64": ("windows", "Windows 11"),
    "windows11": ("windows", "Windows 11"), "windows11_64": ("windows", "Windows 11"),
    "win7": ("windows", "Windows 7"), "win7_64": ("windows", "Windows 7"),
    "windows7": ("windows", "Windows 7"), "windows7_64": ("windows", "Windows 7"),
    "winxp": ("windows", "Windows XP"), "windowsxp": ("windows", "Windows XP"),
    "winvista": ("windows", "Windows Vista"), "windowsvista": ("windows", "Windows Vista"),
    "win2k": ("windows", "Windows 2000"), "windows2000": ("windows", "Windows 2000"),
    "macos": ("macos", ""), "macos_64": ("macos", ""),
    "macos1013": ("macos", "High Sierra (10.13)"),
    "macos1014": ("macos", "Mojave (10.14)"),
    "macos1015": ("macos", "Catalina (10.15)"),
    "macos11": ("macos", "Big Sur (11.7)"),
    "macos12": ("macos", "Monterey (12.6)"),
    "macos13": ("macos", "Ventura (13)"),
    "macos14": ("macos", "Sonoma (14)"),
    "macos15": ("macos", "Sequoia (15)"),
    "android": ("android", ""), "android_x86": ("android", ""),
    "androidx86": ("android", ""), "androidx86_64": ("android", ""),
}

_OS_TO_VBOX_OSTYPE = {
    ("linux", "Ubuntu"): "Ubuntu_64",
    ("linux", "Debian"): "Debian_64",
    ("linux", "Fedora"): "Fedora_64",
    ("linux", "Linux Mint"): "LinuxMint_64",
    ("linux", "openSUSE"): "openSUSE_64",
    ("linux", "Arch Linux"): "ArchLinux_64",
    ("linux", "Manjaro Linux"): "Manjaro_64",
    ("linux", "Kali Linux"): "Kali_64",
    ("linux", "AlmaLinux"): "AlmaLinux_64",
    ("linux", "Rocky Linux"): "Rocky_64",
    ("linux", "Pop!_OS"): "PopOS_64",
    ("linux", "elementary OS"): "Elementary_64",
    ("linux", "Zorin OS"): "Zorin_64",
    ("linux", "MX Linux"): "MX_64",
    ("linux", "Solus"): "Solus_64",
    ("linux", "Alpine Linux"): "Alpine_64",
    ("linux", "Void Linux"): "Void_64",
    ("windows", "Windows 11"): "Windows11_64",
    ("windows", "Windows 10"): "Windows10_64",
    ("windows", "Windows 7"): "Windows7_64",
    ("windows", "Windows Vista"): "WindowsVista_64",
    ("windows", "Windows XP"): "WindowsXP_64",
    ("windows", "Windows 2000"): "Windows2000",
    ("macos", ""): "MacOS_64",
    ("android", ""): "Android_64",
}


def _normalize_ostype(ostype_str):
    s = str(ostype_str or "").strip()
    if not s: return ""
    if "/" in s:
        s = s.rsplit("/", 1)[-1]
    return s.strip().lower()


def map_ostype_to_vm(ostype_str):
    """Devuelve (os_type, distro_o_version) a partir de un ostype VBox."""
    key = _normalize_ostype(ostype_str)
    if key in _VBOX_OSTYPE_MAP:
        return _VBOX_OSTYPE_MAP[key]
    if "win" in key:
        if "11" in key: return ("windows", "Windows 11")
        if "10" in key: return ("windows", "Windows 10")
        if "7"  in key: return ("windows", "Windows 7")
        return ("windows", "Windows 10")
    if "mac" in key or "darwin" in key or "osx" in key:
        return ("macos", "")
    if "android" in key: return ("android", "")
    return ("linux", "")


def map_vm_to_ostype(os_type, distro_or_version=""):
    key = (os_type, distro_or_version)
    if key in _OS_TO_VBOX_OSTYPE:
        return _OS_TO_VBOX_OSTYPE[key]
    return {"linux": "Linux26_64", "windows": "Windows10_64",
            "macos": "MacOS_64", "android": "Android_64"}.get(
                os_type, "Other_64")


def _resolve_file_ref(root, file_ref):
    if not file_ref: return ""
    for f in _iter_local(root, "File"):
        fid = href = ""
        for k, v in f.attrib.items():
            if _localname(k) == "id": fid = v
            elif _localname(k) == "href": href = v
        if fid == file_ref:
            return href
    return file_ref


def parse_ovf_xml(text):
    """Parsea un descriptor OVF y devuelve un dict normalizado."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise RuntimeError(f"OVF inválido (XML mal formado): {e}")

    out = {
        "name": "", "description": "",
        "ostype_vbox": "", "ostype_id": "",
        "os_type": "", "distro": "", "win_ver": "", "macos_ver": "",
        "memory_mb": 0, "cpus": 0,
        "disks": [], "networks": [], "cdroms": [],
    }

    vs = _first_local(root, "VirtualSystem")
    if vs is not None:
        out["name"] = _text_local(vs, "Name", "")
        out["description"] = _text_local(vs, "Description", "")
        # ovf_ova_io_v1_annotation
        out["annotation"] = _text_local(vs, "Annotation", "")

    os_sec = _first_local(root, "OperatingSystemSection")
    if os_sec is not None:
        for k, v in os_sec.attrib.items():
            if _localname(k) == "ostype" and "vbox" in k.lower():
                out["ostype_vbox"] = v; break
        if not out["ostype_vbox"]:
            for k, v in os_sec.attrib.items():
                if _localname(k) == "osType":
                    out["ostype_vbox"] = v; break
        for k, v in os_sec.attrib.items():
            if _localname(k) == "id":
                out["ostype_id"] = str(v); break
        if not out["ostype_vbox"]:
            desc = _text_local(os_sec, "Description", "")
            if desc: out["ostype_vbox"] = desc

    os_type, extra = map_ostype_to_vm(out["ostype_vbox"])
    out["os_type"] = os_type
    if os_type == "linux":      out["distro"] = extra or ""
    elif os_type == "windows":  out["win_ver"] = extra or "Windows 10"
    elif os_type == "macos":    out["macos_ver"] = extra or ""

    vhs = _first_local(root, "VirtualHardwareSection")
    if vhs is not None:
        for item in _iter_local(vhs, "Item"):
            rt = _text_local(item, "ResourceType", "")
            if rt == "3":
                try: out["cpus"] = int(_text_local(item, "VirtualQuantity", "0"))
                except ValueError: pass
            elif rt == "4":
                try: out["memory_mb"] = int(_text_local(item, "VirtualQuantity", "0"))
                except ValueError: pass
            elif rt == "10":
                out["networks"].append({
                    "name": _text_local(item, "Connection", "nat"),
                    "model": _text_local(item, "ResourceSubType", "E1000"),
                })
            elif rt == "15":  # CD-ROM (DMTF DSP0243)
                hr = _text_local(item, "HostResource", "")
                cd = {"file": "", "file_id": ""}
                if hr.startswith("ovf:/file/"):
                    fid = hr[len("ovf:/file/"):]
                    cd["file_id"] = fid
                    cd["file"] = _resolve_file_ref(root, fid)
                out["cdroms"].append(cd)
            elif rt == "17":
                hr = _text_local(item, "HostResource", "")
                if hr.startswith("ovf:/disk/"):
                    out["disks"].append({"disk_id": hr[len("ovf:/disk/"):],
                                          "file": "", "capacity_gb": 0,
                                          "format": ""})

    # ovf_ova_vbox_uefi_v1: leer el firmware desde vbox:BIOSSettings.
    # Si no aparece, se asume BIOS legacy (comportamiento de VirtualBox).
    out["firmware"] = "bios"
    _vhs = _first_local(root, "VirtualHardwareSection")
    if _vhs is not None:
        for _c in _vhs.iter():
            if _localname(_c.tag) == "Firmware":
                _fw = ""
                for _k, _v in _c.attrib.items():
                    if _localname(_k) == "type":
                        _fw = _v; break
                if _fw.lower() in ("efi", "uefi"):
                    out["firmware"] = "uefi"
                break

    for disk in _iter_local(root, "Disk"):
        disk_id = file_ref = units = fmt = ""
        capacity = 0
        for k, v in disk.attrib.items():
            ln = _localname(k)
            if ln == "diskId": disk_id = v
            elif ln == "fileRef": file_ref = v
            elif ln == "capacity":
                try: capacity = int(v)
                except ValueError: pass
            elif ln == "capacityAllocationUnits": units = v
            elif ln == "format": fmt = v
        for d in out["disks"]:
            if d.get("disk_id") == disk_id:
                d["file"] = _resolve_file_ref(root, file_ref)
                d["capacity_gb"] = capacity
                d["format"] = fmt
                d["capacity_units"] = units

    return out


# _OVF_IO_PART_B_MARKER
# ---------------------------------------------------------------------------
# Construccion del descriptor OVF
# ---------------------------------------------------------------------------
def build_ovf_xml(vm_name, os_type, distro_or_version, cpus, memory_mb,
                  disks, networks, vbox_ostype=None, cdroms=None,
                  annotation="", firmware="bios"):
    """Construye un descriptor OVF minimo pero valido.

    `disks` es una lista de dicts: {file, capacity_gb, format, disk_id}
    `networks` es una lista de dicts: {name, model}
    """
    env = ET.Element(f"{{{NS_OVF}}}Envelope")

    refs = ET.SubElement(env, f"{{{NS_OVF}}}References")
    for d in disks:
        f = ET.SubElement(refs, f"{{{NS_OVF}}}File")
        f.set(f"{{{NS_OVF}}}id", d["disk_id"])
        f.set(f"{{{NS_OVF}}}href", d["file"])
        f.set(f"{{{NS_OVF}}}size", "0")
    # ovf_ova_io_v1_cdrom: File entries para las ISOs incluidas.
    for i, cd in enumerate(cdroms or []):
        if cd.get("file_arcname"):
            fid = cd.get("file_id") or f"cdrom{i}_file"
            f = ET.SubElement(refs, f"{{{NS_OVF}}}File")
            f.set(f"{{{NS_OVF}}}id", fid)
            f.set(f"{{{NS_OVF}}}href", cd["file_arcname"])
            f.set(f"{{{NS_OVF}}}size", "0")

    ds = ET.SubElement(env, f"{{{NS_OVF}}}DiskSection")
    info = ET.SubElement(ds, f"{{{NS_OVF}}}Info")
    info.text = "List of the virtual disks"
    for d in disks:
        disk = ET.SubElement(ds, f"{{{NS_OVF}}}Disk")
        disk.set(f"{{{NS_OVF}}}diskId", d["disk_id"])
        disk.set(f"{{{NS_OVF}}}fileRef", d["disk_id"])
        disk.set(f"{{{NS_OVF}}}capacity", str(int(d.get("capacity_gb") or 0)))
        disk.set(f"{{{NS_OVF}}}capacityAllocationUnits", "byte * 2^30")
        disk.set(f"{{{NS_OVF}}}format", d.get("format", ""))

    ns = ET.SubElement(env, f"{{{NS_OVF}}}NetworkSection")
    info = ET.SubElement(ns, f"{{{NS_OVF}}}Info")
    info.text = "List of logical networks"
    for n in networks or [{"name": "nat", "model": "E1000"}]:
        net = ET.SubElement(ns, f"{{{NS_OVF}}}Network")
        net.set(f"{{{NS_OVF}}}name", n.get("name") or "nat")

    vs = ET.SubElement(env, f"{{{NS_OVF}}}VirtualSystem")
    vs.set(f"{{{NS_OVF}}}id", vm_name)
    info = ET.SubElement(vs, f"{{{NS_OVF}}}Info")
    info.text = f"Virtual.Machine: {vm_name}"
    nm = ET.SubElement(vs, f"{{{NS_OVF}}}Name")
    nm.text = vm_name
    desc = ET.SubElement(vs, f"{{{NS_OVF}}}Description")
    desc.text = "Exportado por Virtual.Machine desde vm_config.ini"
    if annotation:
        _ann = ET.SubElement(vs, f"{{{NS_OVF}}}Annotation")
        _ann.text = annotation

    os_sec = ET.SubElement(vs, f"{{{NS_OVF}}}OperatingSystemSection")
    cim_ids = {"linux": "80", "windows": "96", "macos": "103", "android": "80"}
    os_sec.set(f"{{{NS_OVF}}}id", cim_ids.get(os_type, "1"))
    vbox_ost = vbox_ostype or map_vm_to_ostype(os_type, distro_or_version)
    os_sec.set(f"{{{NS_VBOX}}}ostype", vbox_ost)
    info = ET.SubElement(os_sec, f"{{{NS_OVF}}}Info")
    info.text = "Operating system"
    desc = ET.SubElement(os_sec, f"{{{NS_OVF}}}Description")
    if os_type == "linux":       desc.text = f"Linux - {distro_or_version or 'Generic'}"
    elif os_type == "windows":   desc.text = distro_or_version or "Windows"
    elif os_type == "macos":     desc.text = f"macOS - {distro_or_version or 'Generic'}"
    elif os_type == "android":   desc.text = "Android-x86 / Bliss OS"
    else:                        desc.text = distro_or_version or "Other"

    vhs = ET.SubElement(vs, f"{{{NS_OVF}}}VirtualHardwareSection")
    info = ET.SubElement(vhs, f"{{{NS_OVF}}}Info")
    info.text = "Virtual hardware requirements"
    sys_el = ET.SubElement(vhs, f"{{{NS_OVF}}}System")
    ET.SubElement(sys_el, f"{{{NS_VSSD}}}ElementName").text = "Virtual Hardware Family"
    ET.SubElement(sys_el, f"{{{NS_VSSD}}}InstanceID").text = "0"
    ET.SubElement(sys_el, f"{{{NS_VSSD}}}VirtualSystemIdentifier").text = vm_name
    ET.SubElement(sys_el, f"{{{NS_VSSD}}}VirtualSystemType").text = "virtualbox-1.0"

    item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
    ET.SubElement(item, f"{{{NS_RASD}}}AllocationUnits").text = "hertz * 10^6"
    ET.SubElement(item, f"{{{NS_RASD}}}Description").text = "Number of Virtual CPUs"
    ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = f"{cpus} virtual CPU(s)"
    ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = "1"
    ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "3"
    ET.SubElement(item, f"{{{NS_RASD}}}VirtualQuantity").text = str(cpus)

    item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
    ET.SubElement(item, f"{{{NS_RASD}}}AllocationUnits").text = "byte * 2^20"
    ET.SubElement(item, f"{{{NS_RASD}}}Description").text = "Memory Size"
    ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = f"{memory_mb}MB of memory"
    ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = "2"
    ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "4"
    ET.SubElement(item, f"{{{NS_RASD}}}VirtualQuantity").text = str(memory_mb)

    item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
    ET.SubElement(item, f"{{{NS_RASD}}}Address").text = "0"
    ET.SubElement(item, f"{{{NS_RASD}}}Description").text = "IDE Controller"
    ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = "IDE Controller"
    ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = "3"
    ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "5"

    item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
    ET.SubElement(item, f"{{{NS_RASD}}}Address").text = "0"
    ET.SubElement(item, f"{{{NS_RASD}}}Description").text = "SATA Controller"
    ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = "SATA Controller"
    ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = "4"
    ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "20"
    # ovf_ova_io_v1_sata_subtype: VirtualBox exige ResourceSubType
    # cuando ResourceType=20 (SATA). Valores válidos: AHCI,
    # virtio-scsi, NVMe. Sin él, la importación falla con
    #   "Host resource of type 'Other Storage Device (20)' is
    #    supported with SATA AHCI or Virtio-SCSI or NVMe
    #    controllers only, line 2 (subtype)."
    ET.SubElement(item, f"{{{NS_RASD}}}ResourceSubType").text = "AHCI"

    for i, d in enumerate(disks):
        item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
        ET.SubElement(item, f"{{{NS_RASD}}}AddressOnParent").text = str(i)
        ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = f"Hard Disk {i+1}"
        ET.SubElement(item, f"{{{NS_RASD}}}HostResource").text = f"ovf:/disk/{d['disk_id']}"
        ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = str(5 + i)
        ET.SubElement(item, f"{{{NS_RASD}}}Parent").text = "4"
        ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "17"

    for i, n in enumerate(networks or [{"name": "nat", "model": "E1000"}]):
        item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
        ET.SubElement(item, f"{{{NS_RASD}}}AddressOnParent").text = str(7 + i)
        ET.SubElement(item, f"{{{NS_RASD}}}AutomaticAllocation").text = "true"
        ET.SubElement(item, f"{{{NS_RASD}}}Connection").text = n.get("name") or "nat"
        ET.SubElement(item, f"{{{NS_RASD}}}Description").text = "Ethernet adapter"
        ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = f"Network adapter {i+1}"
        ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = str(20 + i)
        ET.SubElement(item, f"{{{NS_RASD}}}ResourceSubType").text = n.get("model") or "E1000"
        ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "10"

    # ovf_ova_io_v1_cdrom: unidades CD/DVD SIEMPRE sobre SATA (Parent=4).
    # ResourceType 15 = CD-ROM. Si cd["file_arcname"] existe, se referencia
    # el ISO incluido; si no, se emite la unidad vacia.
    for i, cd in enumerate(cdroms or []):
        item = ET.SubElement(vhs, f"{{{NS_OVF}}}Item")
        ET.SubElement(item, f"{{{NS_RASD}}}AddressOnParent").text = str(i)
        ET.SubElement(item, f"{{{NS_RASD}}}ElementName").text = f"CD/DVD {i+1}"
        ET.SubElement(item, f"{{{NS_RASD}}}InstanceID").text = str(40 + i)
        ET.SubElement(item, f"{{{NS_RASD}}}Parent").text = "4"
        ET.SubElement(item, f"{{{NS_RASD}}}ResourceType").text = "15"
        if cd.get("file_arcname"):
            fid = cd.get("file_id") or f"cdrom{i}_file"
            ET.SubElement(item, f"{{{NS_RASD}}}HostResource").text = f"ovf:/file/{fid}"

    # ovf_ova_io_v1_remove_keyboard_videocard:
    # El teclado (ResourceType 13) no se declara. VirtualBox rechaza
    # ese tipo con "Unknown resource type 13" y ademas no lo necesita:
    # teclado y raton son implicitos en cualquier VM. Los OVF que
    # genera VirtualBox tampoco los declaran.

    # ovf_ova_io_v1_remove_keyboard_videocard:
    # La tarjeta de video se omitia con ResourceType 24, pero en la
    # interpretacion de VirtualBox el 24 es "USB Controller", no video.
    # VirtualBox y VMware infieren la GPU por si solos; no hace falta
    # declararla. Se elimina para evitar el error de importacion.

    # ovf_ova_vbox_uefi_v1: VirtualBox detecta el firmware UEFI a
    # traves de vbox:BIOSSettings/vbox:Firmware. Sin esto, cualquier
    # OVA importado en VirtualBox se queda en BIOS legacy aunque el
    # disco sea GPT+EFI, y el usuario tiene que activar EFI a mano.
    if (firmware or "").lower() in ("uefi", "efi"):
        _bios = ET.SubElement(vhs, f"{{{NS_VBOX}}}BIOSSettings")
        _fw = ET.SubElement(_bios, f"{{{NS_VBOX}}}Firmware")
        _fw.set("type", "efi")

    xml_bytes = ET.tostring(env, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


# ---------------------------------------------------------------------------
# Empaquetado / desempaquetado OVA
# ---------------------------------------------------------------------------
def free_space_for_path(path):
    """Devuelve bytes libres en el FS que contiene `path`.

    Acepta rutas que aún no existen: sube por los directorios padres
    hasta encontrar uno existente y comprueba ahí.
    """
    p = os.path.abspath(str(path or "."))
    while p and not os.path.exists(p):
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    try:
        return int(shutil.disk_usage(p).free)
    except Exception:
        return -1


def check_ovf_space(path, needed_bytes, margin=1.2):
    """Comprueba si hay espacio suficiente en el FS de `path`.

    Devuelve (ok, free, msg):
      ok=True   → hay espacio con margen.
      ok=False  → NO cabe; msg explica cuánto falta.
      ok=None   → cabe pero con poco margen (< margin); msg advierte.

    `needed_bytes` es el mínimo indispensable; `margin` es el factor
    de seguridad (1.2 = necesitamos 20% extra para no ir al límite).
    """
    free = free_space_for_path(path)
    if free < 0:
        return True, -1, ""  # no pudimos medir; dejar pasar
    need = max(0, int(needed_bytes))
    if need <= 0:
        return True, free, ""
    if free < need:
        falta = need - free
        return False, free, (
            f"Espacio insuficiente en {path}.\n"
            f"  Necesario: {human_bytes_io(need)}\n"
            f"  Disponible: {human_bytes_io(free)}\n"
            f"  Faltan: {human_bytes_io(falta)}\n\n"
            "Libera espacio en ese disco (o elige otro destino) y "
            "vuelve a intentarlo."
        )
    if free < int(need * float(margin)):
        return None, free, (
            f"El espacio libre en {path} va a quedar muy justo.\n"
            f"  Necesario (mínimo): {human_bytes_io(need)}\n"
            f"  Recomendado: {human_bytes_io(int(need * float(margin)))}\n"
            f"  Disponible: {human_bytes_io(free)}\n\n"
            "Si se queda sin espacio a mitad, la operación fallará.\n"
            "¿Continuar de todos modos?"
        )
    return True, free, ""


def human_bytes_io(n):
    """Formato compacto de bytes, sin dependencias."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f} {u}" if u != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} PB"


def _sha1_file(path, chunk=1024 * 1024):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()


def write_manifest(files, dest_path):
    """Escribe un manifest .mf con SHA-1 de cada archivo (formato VBox).

    ovf_ova_io_v1_rev2: `files` puede contener strings (se usa el
    basename) o tuplas (path, arcname). Asi el empaquetado directo
    puede usar un arcname distinto del original.
    """
    lines = []
    for item in files:
        if isinstance(item, (tuple, list)):
            path, name = item[0], item[1]
        else:
            path, name = item, os.path.basename(item)
        lines.append(f"SHA1 ({name}) = {_sha1_file(path)}")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def pack_ova(ovf_text, disk_files, dest_path, extra_meta=None,
             log_emit=None, progress_emit=None, is_cancelled=None):
    """Empaqueta un OVA: tar sin comprimir con OVF + manifest + discos
    + (opcional) .virtmachine.json."""
    def _log(m):
        if log_emit:
            try: log_emit(m)
            except Exception: pass

    if os.path.exists(dest_path):
        try: os.remove(dest_path)
        except OSError: pass

    # ovf_ova_io_v1_rev2: los archivos pequenos (descriptor, manifest,
    # metadata) van a su propio temp dir. Asi los discos pueden
    # empaquetarse directamente desde su ubicacion original.
    # ovf_io_space_guard_v1: crear el temp junto al destino, no en /tmp,
    # para que el FS sea el mismo y el rename final sea barato.
    _meta_parent = None
    try:
        if disk_files:
            _first = disk_files[0]
            if isinstance(_first, (tuple, list)):
                _first = _first[0]
            _meta_parent = os.path.dirname(os.path.abspath(_first))
        if not _meta_parent or not os.path.isdir(_meta_parent):
            _meta_parent = os.path.dirname(os.path.abspath(dest_path))
    except Exception:
        _meta_parent = None
    meta_dir = tempfile.mkdtemp(prefix=".ovf_meta_", dir=_meta_parent)
    try:
        ovf_path = os.path.join(meta_dir, OVF_DESCRIPTOR_NAME)
        with open(ovf_path, "w", encoding="utf-8") as f:
            f.write(ovf_text)

        meta_path = None
        if extra_meta:
            meta_path = os.path.join(meta_dir, VIRTMACHINE_META)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(extra_meta, f, ensure_ascii=False, indent=2)

        # Normalizar disk_files a lista de tuplas (path, arcname).
        disk_items = []
        for p in disk_files:
            if isinstance(p, (tuple, list)):
                disk_items.append((p[0], p[1]))
            else:
                disk_items.append((p, os.path.basename(p)))

        manifest_path = os.path.join(meta_dir, MANIFEST_NAME)
        manifest_files = [(ovf_path, OVF_DESCRIPTOR_NAME)]
        if meta_path:
            manifest_files.append((meta_path, VIRTMACHINE_META))
        manifest_files += disk_items
        write_manifest(manifest_files, manifest_path)

        all_files = [(ovf_path, OVF_DESCRIPTOR_NAME),
                     (manifest_path, MANIFEST_NAME)]
        if meta_path:
            all_files.append((meta_path, VIRTMACHINE_META))
        all_files += disk_items

        total = len(all_files)
        _log(f"==> Empaquetando {total} archivo(s) en {dest_path}...")

        # ovf_io_tar_sparse_v1 (DESCARTADO): intentamos usar `tar --sparse`
        # para reducir el OVA cuando los discos tienen bloques cero, pero
        #   1) VirtualBox rechaza los headers GNU con
        #      VERR_TAR_UNSUPPORTED_GNU_HEADER_TYPE.
        #   2) --sparse NO reduce el tamaño de un QCOW2 aplanado (usa
        #      clusters vacios en la tabla L1/L2, no huecos del FS).
        # ovf_ova_io_v1_vbox_tar_ustar: forzamos formato USTAR (POSIX.1-1988),
        # lo unico que VirtualBox acepta de forma fiable.
        use_system_tar = False
        tar_bin = shutil.which("tar")
        if tar_bin:
            try:
                _v = subprocess.run([tar_bin, "--version"],
                                     capture_output=True, text=True,
                                     timeout=3)
                if _v.returncode == 0:
                    use_system_tar = True
            except Exception:
                use_system_tar = False

        if use_system_tar:
            _log("==> Empaquetando con tar (formato USTAR/POSIX).")
            if is_cancelled and is_cancelled():
                raise RuntimeError("Exportacion cancelada por el usuario.")
            # El nombre base de cada archivo se pasa en el mismo orden que
            # all_files. Todos están en el mismo directorio padre (meta_dir
            # para descriptor/manifest, y el dir de cada disco).
            # Como pueden estar en directorios distintos, hacemos tar con
            # rutas absolutas + --transform para normalizar el arcname.
            # Alternativa simple: construir el tar añadiendo un archivo a
            # la vez con --append (más lento pero robusto).
            # Usamos --append: crea el tar con el primero y luego añade.
            created = False
            for i, (path, arcname) in enumerate(all_files):
                if is_cancelled and is_cancelled():
                    raise RuntimeError("Exportacion cancelada por el usuario.")
                # tar -cf crea; tar -rf añade. Guardamos el directorio y
                # el basename por separado, invocando desde ahí con -C.
                d = os.path.dirname(os.path.abspath(path))
                b = os.path.basename(path)
                if not created:
                    _r = subprocess.run(
                        [tar_bin, "--format=ustar", "-cf", dest_path,
                         "-C", d, "--transform", f"s|{b}|{arcname}|", b],
                        capture_output=True, text=True,
                    )
                    created = True
                else:
                    _r = subprocess.run(
                        [tar_bin, "--format=ustar", "-rf", dest_path,
                         "-C", d, "--transform", f"s|{b}|{arcname}|", b],
                        capture_output=True, text=True,
                    )
                if _r.returncode != 0:
                    err = (_r.stderr or _r.stdout or "").strip()
                    raise RuntimeError(
                        f"tar falló al empaquetar '{arcname}': {err}"
                    )
                if progress_emit:
                    pct = int((i + 1) * 100 / total)
                    progress_emit(pct, f"Empaquetando {arcname} ({i+1}/{total})")
        else:
            _log("==> tar del sistema no disponible; usando tarfile de Python.")
            with tarfile.open(dest_path, "w",
                              format=tarfile.USTAR_FORMAT) as tar:
                for i, (path, arcname) in enumerate(all_files):
                    if is_cancelled and is_cancelled():
                        raise RuntimeError("Exportacion cancelada por el usuario.")
                    tar.add(path, arcname=arcname, recursive=False)
                    if progress_emit:
                        pct = int((i + 1) * 100 / total)
                        progress_emit(pct, f"Empaquetando {arcname} ({i+1}/{total})")
        _log(f"==> OVA empaquetado: {dest_path}")
        return dest_path
    finally:
        try:
            shutil.rmtree(meta_dir, ignore_errors=True)
        except Exception:
            pass


def unpack_ova(ova_path, extract_dir):
    """Extrae un OVA a `extract_dir` y devuelve (ruta .ovf, ruta .virtmachine.json)."""
    os.makedirs(extract_dir, exist_ok=True)
    ovf_found = None
    meta_found = None
    try:
        with tarfile.open(ova_path, "r:") as tar:
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name.split("/"):
                    raise RuntimeError(
                        f"El OVA contiene un path inseguro: {member.name}"
                    )
                tar.extract(member, extract_dir)
                name_lower = os.path.basename(member.name).lower()
                if name_lower.endswith(".ovf") and ovf_found is None:
                    ovf_found = os.path.join(extract_dir, member.name)
                elif name_lower == VIRTMACHINE_META and meta_found is None:
                    meta_found = os.path.join(extract_dir, member.name)
    except tarfile.TarError as e:
        raise RuntimeError(f"No se pudo leer el OVA: {e}")
    return ovf_found, meta_found


def read_ovf_descriptor_only(ova_path):
    """Lee SOLO el .ovf dentro de un OVA sin extraer los discos."""
    try:
        with tarfile.open(ova_path, "r:") as tar:
            for member in tar.getmembers():
                if member.name.lower().endswith(".ovf"):
                    f = tar.extractfile(member)
                    if f is None: continue
                    return f.read().decode("utf-8", errors="replace")
    except tarfile.TarError as e:
        raise RuntimeError(f"No se pudo leer el OVA: {e}")
    return ""


# ---------------------------------------------------------------------------
# Conversion de discos con qemu-img
# ---------------------------------------------------------------------------
def _qemu_img_convert(src, dest, fmt, extra_opts=None,
                       log_emit=None, progress_emit=None, is_cancelled=None):
    def _log(m):
        if log_emit:
            try: log_emit(m)
            except Exception: pass
    if not shutil.which("qemu-img"):
        raise RuntimeError("qemu-img no esta en el PATH.")
    if os.path.exists(dest):
        try: os.remove(dest)
        except OSError: pass
    cmd = ["qemu-img", "convert", "-p", "-O", fmt]
    if extra_opts:
        cmd += extra_opts
    cmd += [src, dest]
    _log(f"==> qemu-img convert -O {fmt}: {os.path.basename(src)} -> {os.path.basename(dest)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    last_pct = -1
    if proc.stdout is not None:
        for line in iter(proc.stdout.readline, ""):
            if is_cancelled and is_cancelled():
                proc.terminate()
                try: proc.wait(timeout=5)
                except Exception:
                    try: proc.kill()
                    except Exception: pass
                try: os.remove(dest)
                except OSError: pass
                raise RuntimeError("Conversion cancelada por el usuario.")
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", line or "")
            if m and progress_emit:
                pct = int(float(m.group(1)))
                if pct != last_pct:
                    last_pct = pct
                    progress_emit(pct, f"Convirtiendo {os.path.basename(src)}... {pct}%")
    proc.wait()
    if proc.returncode != 0:
        try:
            if os.path.exists(dest): os.remove(dest)
        except OSError: pass
        raise RuntimeError(f"qemu-img convert fallo (codigo {proc.returncode}).")
    return dest


def convert_to_vmdk_stream_optimized(src, dest, log_emit=None,
                                       progress_emit=None, is_cancelled=None):
    """Convierte un disco a VMDK stream-optimized (compatible VirtualBox/VMware)."""
    return _qemu_img_convert(src, dest, "vmdk",
                              extra_opts=["-o", "subformat=streamOptimized,compat6"],
                              log_emit=log_emit, progress_emit=progress_emit,
                              is_cancelled=is_cancelled)


def convert_to_qcow2(src, dest, log_emit=None, progress_emit=None,
                       is_cancelled=None):
    """Convierte un disco (VMDK, VHD, RAW, ...) a QCOW2."""
    return _qemu_img_convert(src, dest, "qcow2", extra_opts=[],
                              log_emit=log_emit, progress_emit=progress_emit,
                              is_cancelled=is_cancelled)


# ---------------------------------------------------------------------------
# Metadata propia del OVA (.virtmachine.json)
# ---------------------------------------------------------------------------
def build_virtmachine_meta(vm_config_dict):
    """Construye el dict de metadata propia a partir de un vm_config
    ya cargado. Se preserva extra, menos las claves que no tienen
    sentido fuera del host de origen."""
    extra = dict(vm_config_dict.get("extra") or {})
    for k in ("storage_devices", "cdrom_path", "android_iso", "iso_path",
              "macos_nic_mac", "shared_folders", "snapshot_schedule",
              "backup_schedule", "snapshots_meta", "linked_clone",
              "linked_backing_rel", "linked_original"):
        extra.pop(k, None)
    return {
        "schema": "virtmachine-1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "vm_config": {
            "name": vm_config_dict.get("name"),
            "os_type": vm_config_dict.get("os_type"),
            "firmware": vm_config_dict.get("firmware"),
            "chipset": vm_config_dict.get("chipset"),
            "secure_boot": vm_config_dict.get("secure_boot"),
            "tpm": vm_config_dict.get("tpm"),
            "graphics_mode": vm_config_dict.get("graphics_mode"),
            "graphics_vram": vm_config_dict.get("graphics_vram"),
            "audio_device": vm_config_dict.get("audio_device"),
            "network_mode": vm_config_dict.get("network_mode"),
            "boot_order": vm_config_dict.get("boot_order"),
            "extra": extra,
        },
    }


def load_virtmachine_meta(path):
    """Lee el .virtmachine.json si existe; None si no esta o esta corrupto."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
