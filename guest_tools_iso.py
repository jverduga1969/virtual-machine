# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Generación del ISO de Guest Tools (spice-vdagent/qemu-guest-agent para
Linux, VirtIO+SPICE Guest Tools para Windows) que se adjunta a las VMs
para instalar la integración host<->guest desde dentro del propio guest.
"""
import os
import re

GUEST_TOOLS_ISO_NAME = "VM-Manager-GuestTools.iso"
GUEST_TOOLS_WINDOWS_URLS = {
    "VirtIO Guest Tools": "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/virtio-win-guest-tools.exe",
    "SPICE Guest Tools": "https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe",
}

def _iso9660_dir_record(extent, size, flags, name_byte):
    name = bytes(name_byte)
    length = 33 + len(name) + (1 if len(name) % 2 == 0 else 0)
    rec = bytearray(length)
    rec[0] = length
    rec[2:6] = int(extent).to_bytes(4, "little")
    rec[6:10] = int(extent).to_bytes(4, "big")
    rec[10:14] = int(size).to_bytes(4, "little")
    rec[14:18] = int(size).to_bytes(4, "big")
    rec[18:25] = bytes((126, 9, 16, 0, 0, 0, 0))
    rec[25] = flags
    rec[28:30] = (1).to_bytes(2, "little")
    rec[30:32] = (1).to_bytes(2, "big")
    rec[32] = len(name)
    rec[33:33+len(name)] = name
    return bytes(rec)

def build_simple_iso9660(output_path, files_map, volume_id="VM_MANAGER_GUEST_TOOLS"):
    sector = 2048
    vol_id = re.sub(r"[^A-Z0-9_]", "_", volume_id.upper())[:32].ljust(32)
    normalized = {}
    for name, content in files_map.items():
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(name).upper())[:31]
        if isinstance(content, str): content = content.encode("utf-8")
        normalized[safe] = bytes(content)
    root_extent = 19
    root_dir_size = sector
    next_extent = 20
    file_extents = {}
    for name, content in normalized.items():
        file_extents[name] = next_extent
        next_extent += max(1, (len(content) + sector - 1) // sector)
    total_sectors = next_extent + 1
    pvd = bytearray(sector)
    pvd[0] = 1; pvd[1:6] = b"CD001"; pvd[6] = 1
    pvd[8:40] = b"VM-MANAGER".ljust(32, b" ")
    pvd[40:72] = vol_id.encode("ascii")
    pvd[80:84] = total_sectors.to_bytes(4, "little")
    pvd[84:88] = total_sectors.to_bytes(4, "big")
    pvd[120:124] = (1).to_bytes(2, "little") + (1).to_bytes(2, "big")
    pvd[124:128] = (1).to_bytes(2, "little") + (1).to_bytes(2, "big")
    pvd[128:132] = sector.to_bytes(2, "little") + sector.to_bytes(2, "big")
    pvd[132:136] = (18).to_bytes(4, "little")
    root_record = _iso9660_dir_record(root_extent, root_dir_size, 2, b"\x00")
    pvd[156:156+len(root_record)] = root_record
    term = bytearray(sector); term[0] = 255; term[1:6] = b"CD001"; term[6] = 1
    path_table = bytearray(sector)
    path_table[0] = 1; path_table[2:6] = root_extent.to_bytes(4, "little"); path_table[6:8] = (1).to_bytes(2, "little")
    root = bytearray(root_dir_size); pos = 0
    for special in (b"\x00", b"\x01"):
        rec = _iso9660_dir_record(root_extent, root_dir_size, 2, special)
        root[pos:pos+len(rec)] = rec; pos += len(rec)
    for name, content in normalized.items():
        rec = _iso9660_dir_record(file_extents[name], len(content), 0, name.encode("ascii"))
        root[pos:pos+len(rec)] = rec; pos += len(rec)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(b"\x00" * (16 * sector)); f.write(pvd); f.write(b"\x00" * sector); f.write(path_table); f.write(root)
        current_sector = 20
        for name, content in normalized.items():
            target = file_extents[name]
            while current_sector < target:
                f.write(b"\x00" * sector); current_sector += 1
            f.write(content)
            pad = (-len(content)) % sector
            if pad: f.write(b"\x00" * pad)
            current_sector += max(1, (len(content) + sector - 1) // sector)
        f.write(term)
        expected = total_sectors * sector
        if f.tell() < expected: f.write(b"\x00" * (expected - f.tell()))

def create_guest_tools_iso(output_path):
    readme = """VM MANAGER - GUEST TOOLS\n========================\n\nEsta ISO contiene scripts para integrar el guest con QEMU/KVM.\n\nWINDOWS: ejecuta INSTALL-WINDOWS.CMD como Administrador. Descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde fuentes oficiales.\n\nLINUX: ejecuta INSTALL-LINUX.SH con sudo. Instala qemu-guest-agent y spice-vdagent cuando esté disponible, para clipboard e integración SPICE.\n\nEl administrador expone el canal VirtIO serial org.qemu.guest_agent.0 cuando se activa Guest Tools.\n\nFuentes:\nhttps://www.qemu.org/docs/master/interop/qemu-ga.html\nhttps://github.com/virtio-win/virtio-win-pkg-scripts\nhttps://www.spice-space.org/download/windows/\n"""
    win_ps = "$ErrorActionPreference = \"Stop\"\n$virtio = \"" + GUEST_TOOLS_WINDOWS_URLS["VirtIO Guest Tools"] + "\"\n$spice = \"" + GUEST_TOOLS_WINDOWS_URLS["SPICE Guest Tools"] + "\"\n$dest = Join-Path $env:TEMP \"VMManagerGuestTools\"\nNew-Item -ItemType Directory -Force -Path $dest | Out-Null\n$virtioFile = Join-Path $dest \"virtio-win-guest-tools.exe\"\n$spiceFile = Join-Path $dest \"spice-guest-tools.exe\"\nInvoke-WebRequest -Uri $virtio -OutFile $virtioFile\nInvoke-WebRequest -Uri $spice -OutFile $spiceFile\nStart-Process -FilePath $virtioFile -Wait\nStart-Process -FilePath $spiceFile -Wait\nWrite-Host \"Guest Tools instaladas. Reinicia Windows.\"\n"
    win_cmd = "@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0INSTALL-WINDOWS.PS1\"\npause\n"
    linux_sh = """#!/bin/sh
set -eu

# Instala herramientas de integración según la familia de la distribución.
# qemu-guest-agent permite administración desde el host; spice-vdagent
# proporciona clipboard/funciones SPICE cuando el display y el guest lo soportan.
MANAGER=unknown
case "$(. /etc/os-release 2>/dev/null; echo \"${ID:-} ${ID_LIKE:-}\" | tr \"[:upper:]\" \"[:lower:]\")" in
  *ubuntu*|*debian*|*linuxmint*|*pop*|*elementary*|*zorin*) MANAGER=apt ;;
  *fedora*|*rhel*|*centos*|*rocky*|*almalinux*) MANAGER=dnf ;;
  *arch*|*manjaro*|*cachyos*|*endeavouros*) MANAGER=pacman ;;
  *opensuse*|*suse*) MANAGER=zypper ;;
  *alpine*) MANAGER=apk ;;
esac

case "$MANAGER" in
  apt)
    sudo apt-get update
    sudo apt-get install -y qemu-guest-agent spice-vdagent || {
      echo "No se pudo instalar spice-vdagent; se instalará al menos qemu-guest-agent."
      sudo apt-get install -y qemu-guest-agent
    }
    ;;
  dnf)
    sudo dnf install -y qemu-guest-agent spice-vdagent || {
      echo "No se pudo instalar spice-vdagent; se instalará al menos qemu-guest-agent."
      sudo dnf install -y qemu-guest-agent
    }
    ;;
  pacman)
    sudo pacman -Sy --noconfirm qemu-guest-agent spice-vdagent || {
      echo "No se pudo instalar spice-vdagent; se instalará al menos qemu-guest-agent."
      sudo pacman -Sy --noconfirm qemu-guest-agent
    }
    ;;
  zypper)
    sudo zypper --non-interactive install qemu-guest-agent spice-vdagent || {
      echo "No se pudo instalar spice-vdagent; se instalará al menos qemu-guest-agent."
      sudo zypper --non-interactive install qemu-guest-agent
    }
    ;;
  apk)
    sudo apk add qemu-guest-agent
    echo "Alpine: spice-vdagent puede no estar empaquetado; revisa los repositorios de tu versión."
    ;;
  *)
    echo "Distribución/gestor no reconocido. Instala qemu-guest-agent y spice-vdagent manualmente." >&2
    exit 1
    ;;
esac

# QGA suele ser un servicio systemd. No todos los sistemas usan systemd.
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl enable --now qemu-guest-agent.service 2>/dev/null || sudo systemctl start qemu-guest-agent.service 2>/dev/null || true
  if systemctl list-unit-files spice-vdagentd.service >/dev/null 2>&1 && systemctl cat spice-vdagentd.service >/dev/null 2>&1; then
    sudo systemctl enable --now spice-vdagentd.service || sudo systemctl start spice-vdagentd.service || true
  elif systemctl cat spice-vdagent.service >/dev/null 2>&1; then
    sudo systemctl enable --now spice-vdagent.service || sudo systemctl start spice-vdagent.service || true
  else
    echo "No se encontró un servicio spice-vdagentd; en algunas distros se inicia en la sesión gráfica del usuario."
  fi
fi

echo "Instalación terminada. Reinicia el guest y prueba clipboard. Verifica /dev/virtio-ports/ y el servicio spice-vdagent."
"""
    channel = "CANAL QEMU GUEST AGENT\n======================\nNombre: org.qemu.guest_agent.0\nLinux normalmente: /dev/virtio-ports/org.qemu.guest_agent.0\n"
    files = {"README.TXT":readme,"INSTALL-WINDOWS.CMD":win_cmd,"INSTALL-WINDOWS.PS1":win_ps,"INSTALL-LINUX.SH":linux_sh,"QGA-CHANNEL.TXT":channel,"OFFICIAL-LINKS.TXT":"\n".join(GUEST_TOOLS_WINDOWS_URLS.values())+"\n"}
    build_simple_iso9660(os.path.abspath(output_path), files)
    return os.path.abspath(output_path)

