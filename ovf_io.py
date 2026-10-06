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
import json
import shutil
import hashlib
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime


# --- Namespaces DMTF --------------------------------------------------------
NS_OVF  = "http://schemas.dmtf.org/ovf/envelope/1"
NS_RASD = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"
NS_VSSD = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData"
NS_VBOX = "http://www.virtualbox.org/ovf/machine"
NS_VMW  = "http://www.vmware.com/schema/ovf"

# ovf_vmware_compat_v7: ElementTree NO puede declarar el mismo URI
# dos veces (como default y como prefijo "ovf:"). Si registramos
# NS_OVF como default, pierde el prefijo en los ATRIBUTOS y ovftool
# no encuentra ovf:id / ovf:fileRef. Volvemos al prefijo "ovf:"
# explicito en todo el documento.
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
            # ovf_vmware_compat_v2: el namespace de vbox:ostype es
            # "http://www.virtualbox.org/ovf/machine", que NO contiene
            # la subcadena "vbox". Buscamos "virtualbox" en su lugar.
            if _localname(k) == "ostype" and "virtualbox" in k.lower():
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
            _ln = _localname(_c.tag)
            if _ln == "Firmware":
                _fw = ""
                for _k, _v in _c.attrib.items():
                    if _localname(_k) == "type":
                        _fw = _v; break
                if _fw.lower() in ("efi", "uefi"):
                    out["firmware"] = "uefi"
                break
            # ovf_vmware_compat_v2: leer tambien vmw:Config firmware
            if _ln == "Config":
                _k = _v = ""
                for _ak, _av in _c.attrib.items():
                    _lnk = _localname(_ak)
                    if _lnk == "key": _k = _av
                    elif _lnk == "value": _v = _av
                if _k == "firmware" and _v.lower() in ("efi", "uefi"):
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
        # ovf_vmware_compat_v3: tras el fix, fileRef ya no coincide
        # con diskId (file0 vs vmdisk0). Resolvemos el nombre de
        # archivo por el fileRef y lo asignamos al disco cuyo disk_id
        # coincide. Tambien aceptamos la vieja coincidencia (OVA
        # antiguos exportados antes del fix).
        _resolved_href = _resolve_file_ref(root, file_ref) if file_ref else ""
        for d in out["disks"]:
            if d.get("disk_id") == disk_id:
                d["file"] = _resolved_href
                d["capacity_gb"] = capacity
                d["format"] = fmt
                d["capacity_units"] = units

    return out



def _vbox_to_vmware_ostype(vbox_ostype):
    """ovf_export_destino_v1: mapea un ostype de VirtualBox al osType
    equivalente de VMware (atributo vmw:osType). VMware lo usa para
    autodetectar el SO invitado al importar. Devuelve "" si no hay
    match (entonces no se emite el atributo).
    """
    s = str(vbox_ostype or "").strip().lower().replace("_64", "")
    _map = {
        "ubuntu": "ubuntu-64", "debian": "debian-64", "fedora": "fedora-64",
        "linuxmint": "ubuntu-64", "opensuse": "opensuse-64",
        "archlinux": "otherlinux-64", "manjaro": "otherlinux-64",
        "kali": "debian-64", "almalinux": "rhel-64", "rocky": "rhel-64",
        "popos": "ubuntu-64", "elementary": "ubuntu-64", "zorin": "ubuntu-64",
        "mx": "debian-64", "solus": "otherlinux-64", "alpine": "otherlinux-64",
        "void": "otherlinux-64", "linux26": "otherlinux-64",
        "windows11": "windows9-64", "windows10": "windows9-64",
        "win11": "windows9-64", "win10": "windows9-64",
        "windows7": "windows7-64", "win7": "windows7-64",
        "windowsvista": "winvista-64", "winvista": "winvista-64",
        "windowsxp": "winXPPro", "winxp": "winXPPro",
        "windows2000": "winNetStandard", "win2k": "winNetStandard",
        "macos": "darwin-64", "android": "other-64",
    }
    return _map.get(s, "")


# _OVF_IO_PART_B_MARKER
# ---------------------------------------------------------------------------
# Construccion del descriptor OVF
# ---------------------------------------------------------------------------
def build_ovf_xml(vm_name, os_type, distro_or_version, cpus, memory_mb,
                  disks, networks, vbox_ostype=None, cdroms=None,
                  annotation="", firmware="bios", destino="virtualbox",
                  disk_sizes=None):
    """Genera un descriptor OVF.

    ovf_vmware_template_v1: cuando el destino es VMware, genera el
    descriptor replicando exactamente el formato que produce VMware
    ovftool (namespace por defecto + atributos con prefijo ovf:).
    Esto evita los problemas de ovftool al resolver fileRef.
    Para VirtualBox y Virtual.Machine se mantiene el formato anterior
    (ElementTree con prefijo ovf:).
    """
    if destino == "vmware":
        return _build_ovf_xml_vmware(
            vm_name, os_type, distro_or_version, cpus, memory_mb,
            disks, networks, vbox_ostype, cdroms, annotation,
            firmware, disk_sizes,
        )
    # --- Formato ElementTree clasico (VirtualBox / Virtual.Machine) ---
    if destino not in ("virtualbox", "virtmachine"):
        destino = "virtualbox"

    env = ET.Element(f"{{{NS_OVF}}}Envelope")

    refs = ET.SubElement(env, f"{{{NS_OVF}}}References")
    _refs_info = ET.SubElement(refs, f"{{{NS_OVF}}}Info")
    _refs_info.text = "List of files in this OVF package"
    for _i, d in enumerate(disks):
        f = ET.SubElement(refs, f"{{{NS_OVF}}}File")
        f.set(f"{{{NS_OVF}}}id", f"file{_i+1}")
        f.set(f"{{{NS_OVF}}}href", d["file"])
        _sz = int(_sizes.get(d.get("disk_id"), 0) or 0)
        f.set(f"{{{NS_OVF}}}size", str(_sz))

    ds = ET.SubElement(env, f"{{{NS_OVF}}}DiskSection")
    info = ET.SubElement(ds, f"{{{NS_OVF}}}Info")
    info.text = "List of the virtual disks"
    for _i, d in enumerate(disks):
        disk = ET.SubElement(ds, f"{{{NS_OVF}}}Disk")
        disk.set(f"{{{NS_OVF}}}diskId", d["disk_id"])
        disk.set(f"{{{NS_OVF}}}fileRef", f"file{_i+1}")
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

    if (firmware or "").lower() in ("uefi", "efi"):
        _bios = ET.SubElement(vhs, f"{{{NS_VBOX}}}BIOSSettings")
        _fw = ET.SubElement(_bios, f"{{{NS_VBOX}}}Firmware")
        _fw.set("type", "efi")

    xml_bytes = ET.tostring(env, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def _build_ovf_xml_vmware(vm_name, os_type, distro_or_version, cpus,
                           memory_mb, disks, networks, vbox_ostype, cdroms,
                           annotation, firmware, disk_sizes):
    """ovf_vmware_template_v1: descriptor VMware como string literal.

    Replica byte a byte el formato que produce ovftool: namespace
    por defecto, atributos con prefijo ovf:, sin elemento Annotation.
    """
    _sizes = dict(disk_sizes or {})
    _vbox_ost = vbox_ostype or map_vm_to_ostype(os_type, distro_or_version)
    _vmw_ost = _vbox_to_vmware_ostype(_vbox_ost) or "otherGuest"

    # --- File entries ---
    _refs_lines = []
    for _i, _d in enumerate(disks):
        _sz = int(_sizes.get(_d.get("disk_id"), 0) or 0)
        _href = _d.get("file") or f"disk{_i+1}.vmdk"
        _refs_lines.append(
            f'    <File ovf:href="{_href}" ovf:id="file{_i+1}" ovf:size="{_sz}"/>'
        )

    # --- Disk entries ---
    _disk_lines = []
    for _i, _d in enumerate(disks):
        _cap = int(_d.get("capacity_gb") or 0)
        _fmt = _d.get("format", "") or (
            "http://www.vmware.com/interfaces/specifications/"
            "vmdk.html#streamOptimized"
        )
        _disk_lines.append(
            f'    <Disk ovf:capacity="{_cap}" '
            f'ovf:capacityAllocationUnits="byte * 2^30" '
            f'ovf:diskId="vmdisk{_i+1}" ovf:fileRef="file{_i+1}" '
            f'ovf:format="{_fmt}" ovf:populatedSize="0"/>'
        )

    # --- Network ---
    _net_name = "nat"
    if networks:
        _net_name = networks[0].get("name") or "nat"
    _net_lines = [
        f'    <Network ovf:name="{_net_name}">',
        f'      <Description>The {_net_name} network</Description>',
        '    </Network>',
    ]

    # --- VirtualHardware items ---
    _hw_lines = []
    _hw_lines.append(
        '      <Item>\n'
        '        <rasd:AllocationUnits>hertz * 10^6</rasd:AllocationUnits>\n'
        '        <rasd:Description>Number of Virtual CPUs</rasd:Description>\n'
        f'        <rasd:ElementName>{cpus} virtual CPU(s)</rasd:ElementName>\n'
        '        <rasd:InstanceID>1</rasd:InstanceID>\n'
        '        <rasd:ResourceType>3</rasd:ResourceType>\n'
        f'        <rasd:VirtualQuantity>{cpus}</rasd:VirtualQuantity>\n'
        '      </Item>'
    )
    _hw_lines.append(
        '      <Item>\n'
        '        <rasd:AllocationUnits>byte * 2^20</rasd:AllocationUnits>\n'
        '        <rasd:Description>Memory Size</rasd:Description>\n'
        f'        <rasd:ElementName>{memory_mb}MB of memory</rasd:ElementName>\n'
        '        <rasd:InstanceID>2</rasd:InstanceID>\n'
        '        <rasd:ResourceType>4</rasd:ResourceType>\n'
        f'        <rasd:VirtualQuantity>{memory_mb}</rasd:VirtualQuantity>\n'
        '      </Item>'
    )
    _hw_lines.append(
        '      <Item>\n'
        '        <rasd:Address>0</rasd:Address>\n'
        '        <rasd:Description>SATA Controller</rasd:Description>\n'
        '        <rasd:ElementName>sataController0</rasd:ElementName>\n'
        '        <rasd:InstanceID>3</rasd:InstanceID>\n'
        '        <rasd:ResourceSubType>vmware.sata.ahci</rasd:ResourceSubType>\n'
        '        <rasd:ResourceType>20</rasd:ResourceType>\n'
        '      </Item>'
    )
    for _i, _d in enumerate(disks):
        _hw_lines.append(
            '      <Item>\n'
            f'        <rasd:AddressOnParent>{_i}</rasd:AddressOnParent>\n'
            f'        <rasd:ElementName>disk{_i}</rasd:ElementName>\n'
            f'        <rasd:HostResource>ovf:/disk/vmdisk{_i+1}</rasd:HostResource>\n'
            f'        <rasd:InstanceID>{7 + _i}</rasd:InstanceID>\n'
            '        <rasd:Parent>3</rasd:Parent>\n'
            '        <rasd:ResourceType>17</rasd:ResourceType>\n'
            '      </Item>'
        )
    for _i, _n in enumerate(networks or [{"name": "nat"}]):
        _nm = _n.get("name") or "nat"
        _hw_lines.append(
            '      <Item>\n'
            f'        <rasd:AddressOnParent>{2 + _i}</rasd:AddressOnParent>\n'
            '        <rasd:AutomaticAllocation>true</rasd:AutomaticAllocation>\n'
            f'        <rasd:Connection>{_nm}</rasd:Connection>\n'
            f'        <rasd:Description>PCNet32 ethernet adapter on "{_nm}"</rasd:Description>\n'
            '        <rasd:ElementName>ethernet0</rasd:ElementName>\n'
            f'        <rasd:InstanceID>{10 + _i}</rasd:InstanceID>\n'
            '        <rasd:ResourceSubType>PCNet32</rasd:ResourceSubType>\n'
            '        <rasd:ResourceType>10</rasd:ResourceType>\n'
            '      </Item>'
        )
    for _i, _cd in enumerate(cdroms or []):
        _hw_lines.append(
            '      <Item ovf:required="false">\n'
            f'        <rasd:AddressOnParent>{_i + 1}</rasd:AddressOnParent>\n'
            '        <rasd:AutomaticAllocation>false</rasd:AutomaticAllocation>\n'
            f'        <rasd:ElementName>cdrom{_i}</rasd:ElementName>\n'
            f'        <rasd:InstanceID>{20 + _i}</rasd:InstanceID>\n'
            '        <rasd:Parent>3</rasd:Parent>\n'
            '        <rasd:ResourceType>15</rasd:ResourceType>\n'
            '      </Item>'
        )

    _hw_block = "\n".join(_hw_lines)
    _refs_block = "\n".join(_refs_lines)
    _disks_block = "\n".join(_disk_lines)
    _net_block = "\n".join(_net_lines)

    _fw_config = ""
    if (firmware or "").lower() in ("uefi", "efi"):
        _fw_config = (
            '      <vmw:Config ovf:required="false" '
            'vmw:key="firmware" vmw:value="efi"/>\n'
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Envelope xmlns="http://schemas.dmtf.org/ovf/envelope/1" '
        'xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" '
        'xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
        'CIM_ResourceAllocationSettingData" '
        'xmlns:vssd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
        'CIM_VirtualSystemSettingData" '
        'xmlns:vmw="http://www.vmware.com/schema/ovf">\n'
        '  <References>\n'
        f'{_refs_block}\n'
        '  </References>\n'
        '  <DiskSection>\n'
        '    <Info>Virtual disk information</Info>\n'
        f'{_disks_block}\n'
        '  </DiskSection>\n'
        '  <NetworkSection>\n'
        '    <Info>The list of logical networks</Info>\n'
        f'{_net_block}\n'
        '  </NetworkSection>\n'
        '  <VirtualSystem ovf:id="vm">\n'
        '    <Info>A virtual machine</Info>\n'
        f'    <Name>{vm_name}</Name>\n'
        f'    <OperatingSystemSection ovf:id="80" vmw:osType="{_vmw_ost}">\n'
        '      <Info>The kind of installed guest operating system</Info>\n'
        '    </OperatingSystemSection>\n'
        '    <VirtualHardwareSection>\n'
        '      <Info>Virtual hardware requirements</Info>\n'
        '      <System>\n'
        '        <vssd:ElementName>Virtual Hardware Family</vssd:ElementName>\n'
        '        <vssd:InstanceID>0</vssd:InstanceID>\n'
        f'        <vssd:VirtualSystemIdentifier>{vm_name}</vssd:VirtualSystemIdentifier>\n'
        '        <vssd:VirtualSystemType>vmx-14</vssd:VirtualSystemType>\n'
        '      </System>\n'
        f'{_hw_block}\n'
        f'{_fw_config}'
        '    </VirtualHardwareSection>\n'
        '  </VirtualSystem>\n'
        '</Envelope>\n'
    )


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


def check_ovf_space(path, needed_bytes, margin=1.05, extra_context=None):
    """Comprueba si hay espacio suficiente en el FS de `path`.

    Devuelve (ok, free, msg):
      ok=True   → hay espacio con margen.
      ok=False  → NO cabe; msg explica cuánto falta.
      ok=None   → cabe pero con poco margen (< margin); msg advierte.

    `needed_bytes` es el mínimo indispensable; `margin` es el factor
    de seguridad (1.05 = 5% extra para no ir al límite). El margen se
    bajó de 1.20 a 1.05 en ovf_space_optimize_v1: los factores de
    estimación ya incluyen su propio colchón y duplicar el margen
    pedía espacio libre irreal a discos externos.

    `extra_context`: lista opcional de líneas adicionales (str) que se
    concatenan al mensaje devuelto. Se usa para añadir un desglose de
    "qué ocupa qué" y sugerencias de alternativas.
    """
    free = free_space_for_path(path)
    if free < 0:
        return True, -1, ""  # no pudimos medir; dejar pasar
    need = max(0, int(needed_bytes))
    if need <= 0:
        return True, free, ""
    _extra = list(extra_context or [])
    if free < need:
        falta = need - free
        _lines = [
            f"Espacio insuficiente en {path}.\n",
            f"  Necesario: {human_bytes_io(need)}",
            f"  Disponible: {human_bytes_io(free)}",
            f"  Faltan: {human_bytes_io(falta)}",
        ]
        if _extra:
            _lines.append("")
            _lines.extend(_extra)
        _lines.append("")
        _lines.append(
            "Libera espacio en ese disco (o elige otro destino) y "
            "vuelve a intentarlo."
        )
        return False, free, "\n".join(_lines)
    if free < int(need * float(margin)):
        _lines = [
            f"El espacio libre en {path} va a quedar muy justo.\n",
            f"  Necesario (mínimo): {human_bytes_io(need)}",
            f"  Recomendado: {human_bytes_io(int(need * float(margin)))}",
            f"  Disponible: {human_bytes_io(free)}",
        ]
        if _extra:
            _lines.append("")
            _lines.extend(_extra)
        _lines.append("")
        _lines.append("Si se queda sin espacio a mitad, la operación fallará.")
        _lines.append("¿Continuar de todos modos?")
        return None, free, "\n".join(_lines)
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
    """Convierte un disco con qemu-img convert.

    ovf_qemu_img_measure_poll_v1: no dependemos de qemu-img -p (que
    solo activa la barra si stdout es terminal y ademas varia entre
    versiones de QEMU). En su lugar:

      1. Preguntamos a `qemu-img measure` cuanto pesara el destino.
      2. Lanzamos la conversion sin -p.
      3. Medimos el archivo destino cada 500 ms y estimamos el %.
      4. Al terminar, cerramos la barra en 100.

    Funciona en cualquier version de QEMU, sin TTYs ni parseo.
    """
    import time as _time
    import json as _json

    def _log(m):
        if log_emit:
            try: log_emit(m)
            except Exception: pass

    if not shutil.which("qemu-img"):
        raise RuntimeError("qemu-img no esta en el PATH.")
    if os.path.exists(dest):
        try: os.remove(dest)
        except OSError: pass

    # 1) Tamano esperado del destino.
    #    ovf_qemu_img_measure_poll_v2: qemu-img measure NO acepta
    #    opciones especificas de subformato (falla con
    #    subformat=streamOptimized,compat6 para VMDK). Cascada:
    #      a) measure con TODAS las opciones (funciona en QCOW2 -c).
    #      b) measure SIN opciones (funciona en VMDK plano).
    #      c) estimacion por factor segun formato (ultimo recurso).
    expected = 0
    _src_size = 0
    try:
        _src_size = os.path.getsize(src)
    except OSError:
        _src_size = 0

    # 1a) measure con opciones
    try:
        _mc = ["qemu-img", "measure", "-O", fmt]
        if extra_opts:
            _mc += list(extra_opts)
        _mc.append(src)
        _mr = subprocess.run(_mc, capture_output=True, text=True, timeout=120)
        if _mr.returncode == 0:
            _md = json.loads(_mr.stdout or "{}")
            _req = int(_md.get("required") or 0)
            _full = int(_md.get("fully-allocated") or 0)
            expected = max(_req, _full)
            if expected > 0:
                _log(f"==> qemu-img measure: destino esperado ~{expected/1e9:.2f} GB.")
    except Exception:
        pass

    # 1b) measure sin opciones (para VMDK stream-optimized)
    if expected <= 0:
        try:
            _mc2 = ["qemu-img", "measure", "-O", fmt, src]
            _mr2 = subprocess.run(_mc2, capture_output=True, text=True, timeout=120)
            if _mr2.returncode == 0:
                _md2 = json.loads(_mr2.stdout or "{}")
                _req2 = int(_md2.get("required") or 0)
                _full2 = int(_md2.get("fully-allocated") or 0)
                expected = max(_req2, _full2)
                if expected > 0:
                    _log(f"==> qemu-img measure (sin opciones): destino "
                         f"esperado ~{expected/1e9:.2f} GB.")
        except Exception:
            pass

    # 1c) Estimacion por factor segun formato
    if expected <= 0 and _src_size > 0:
        _fmt_low = (fmt or "").lower()
        if _fmt_low == "vmdk":
            # VMDK stream-optimized: ~1.0x el origen (no comprime, pero
            # suele descartar snapshots internos).
            expected = int(_src_size * 1.05)
        elif _fmt_low == "qcow2":
            # QCOW2 con -c: ~0.5x el origen.
            expected = int(_src_size * 0.55)
        else:
            expected = _src_size
        _log(f"==> Estimacion por factor ({_fmt_low}): destino esperado "
             f"~{expected/1e9:.2f} GB (origen: {_src_size/1e9:.2f} GB).")

    if expected <= 0:
        _log("[AVISO] Sin estimacion de tamano; sin barra de progreso.")

    # 2) Lanzar la conversion sin -p
    cmd = ["qemu-img", "convert", "-O", fmt]
    if extra_opts:
        cmd += list(extra_opts)
    cmd += [src, dest]
    _log(f"==> qemu-img convert -O {fmt}: {os.path.basename(src)} -> {os.path.basename(dest)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)

    # 3) Polling del archivo destino
    last_pct = -1
    try:
        while True:
            rc = proc.poll()
            if is_cancelled and is_cancelled():
                try: proc.terminate()
                except Exception: pass
                try: proc.wait(timeout=5)
                except Exception:
                    try: proc.kill()
                    except Exception: pass
                try:
                    if os.path.exists(dest): os.remove(dest)
                except OSError: pass
                raise RuntimeError("Conversion cancelada por el usuario.")
            try:
                cur = os.path.getsize(dest)
            except OSError:
                cur = 0
            if expected > 0 and progress_emit:
                pct = min(99, int(cur * 100 / expected))
                if pct != last_pct:
                    last_pct = pct
                    progress_emit(pct, f"Convirtiendo {os.path.basename(src)}... {pct}%")
            if rc is not None:
                break
            _time.sleep(0.5)
    finally:
        try: proc.wait(timeout=10)
        except Exception: pass

    # 4) Comprobaciones finales
    if proc.returncode != 0:
        _err = b""
        try:
            if proc.stderr is not None:
                _err = proc.stderr.read() or b""
        except Exception:
            pass
        try:
            if os.path.exists(dest): os.remove(dest)
        except OSError: pass
        _msg = _err.decode("utf-8", "replace").strip() or f"rc={proc.returncode}"
        raise RuntimeError(f"qemu-img convert fallo (codigo {proc.returncode}): {_msg}")

    if progress_emit:
        progress_emit(100, f"Convertido: {os.path.basename(dest)}")
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


def convert_to_qcow2_compressed(src, dest, log_emit=None,
                                 progress_emit=None,
                                 is_cancelled=None):
    """Convierte un disco a QCOW2 aplanado y comprimido con zlib.

    Marcador ovf_qcow2_compressed_live_progress_v1: aplanado
    (descarta snapshots internos y backing file) + compresion
    zlib. Emite progreso en vivo porque el bucle interno de
    _qemu_img_convert corta tanto en \r como en \n.
    """
    return _qemu_img_convert(src, dest, "qcow2", extra_opts=["-c"],
                              log_emit=log_emit,
                              progress_emit=progress_emit,
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
