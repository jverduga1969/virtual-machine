# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Soporte de carpetas compartidas VirtioFS: escapado seguro para scripts
bash, localización de virtiofsd en el host, y chequeo/instalación de sus
dependencias.
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

from host_deps import _run_privileged_install, detect_linux_package_manager

def bash_squote(value):
    """Escapa un valor (típicamente una ruta) para insertarlo de forma segura
    dentro de un literal bash entre comillas simples: 'texto{escapado}texto'.

    Antes esto se repetía como `.replace("'", "'\\''")` suelto en varios
    puntos del archivo (carpetas compartidas, trap de limpieza); centralizarlo
    evita que una copia quede desactualizada o mal escrita si se toca solo
    una de ellas.
    """
    return str(value).replace("'", "'\\''")


def find_virtiofsd():
    """Encuentra virtiofsd incluso en distribuciones que lo instalan fuera de PATH."""
    candidates = [
        shutil.which("virtiofsd"),
        "/usr/lib/virtiofsd",
        "/usr/libexec/virtiofsd",
        "/usr/local/libexec/virtiofsd",
        "/usr/lib/qemu/virtiofsd",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return ""


def get_shared_folder_dependency_status():
    """Comprueba las dependencias del host para VirtioFS, 9p y SMB.

    9p no necesita un paquete adicional en el host: QEMU debe ofrecer -virtfs.
    VirtioFS necesita virtiofsd. SMB mediante la red user-mode de QEMU necesita
    un smbd disponible en el host.
    """
    qemu = shutil.which("qemu-system-x86_64")
    qemu_9p = False
    qemu_smb = False
    if qemu:
        try:
            r = subprocess.run([qemu, "-help"], capture_output=True, text=True, timeout=5)
            txt = (r.stdout or "") + "\n" + (r.stderr or "")
            qemu_9p = "-virtfs" in txt or "-fsdev" in txt
        except Exception:
            pass
        try:
            r = subprocess.run([qemu, "-netdev", "help"], capture_output=True, text=True, timeout=5)
            txt = (r.stdout or "") + "\n" + (r.stderr or "")
            qemu_smb = "smb" in txt.lower()
        except Exception:
            pass
    smbd = shutil.which("smbd") or shutil.which("smbd4")
    virtiofsd = find_virtiofsd()
    manager, info = detect_linux_package_manager()
    return {
        "virtiofsd": bool(virtiofsd),
        "virtiofsd_path": virtiofsd,
        "virtiofsd_version": "",
        "9p": bool(qemu_9p),
        "9p_detail": "QEMU -virtfs/-fsdev disponible" if qemu_9p else "QEMU no ofrece -virtfs/-fsdev",
        "smb": bool(smbd) and bool(qemu_smb),
        "smbd": bool(smbd),
        "smbd_path": smbd or "",
        "smb_detail": ("smbd disponible" if smbd else "falta smbd") + (" | QEMU SMB disponible" if qemu_smb else " | QEMU no reporta SMB"),
        "package_manager": manager or "No detectado",
        "distro": info.get("PRETTY_NAME") or info.get("ID") or "Linux",
    }


def ensure_shared_folder_dependencies(need_virtiofsd=False, need_smb=False, log_func=print):
    """Instala solo las dependencias host necesarias para carpetas compartidas."""
    st = get_shared_folder_dependency_status()
    missing = []
    if need_virtiofsd and not st["virtiofsd"]:
        missing.append("virtiofsd")
    if need_smb and not st["smb"]:
        missing.append("samba")
    if not missing:
        return st

    manager, info = detect_linux_package_manager()
    distro = info.get("PRETTY_NAME") or info.get("ID") or "Linux"
    if not manager:
        raise RuntimeError(f"No pude detectar el gestor de paquetes de {distro}. Faltan: {', '.join(missing)}.")
    package_map = {
        "apt": {"virtiofsd": "virtiofsd", "samba": "samba"},
        "dnf": {"virtiofsd": "virtiofsd", "samba": "samba"},
        "pacman": {"virtiofsd": "virtiofsd", "samba": "samba"},
        "zypper": {"virtiofsd": "virtiofsd", "samba": "samba"},
        "apk": {"virtiofsd": "virtiofsd", "samba": "samba"},
    }
    if manager not in package_map:
        raise RuntimeError(f"El gestor '{manager}' aún no tiene nombres de paquetes configurados para carpetas compartidas.")
    packages = [package_map[manager][item] for item in missing]
    if manager == "apt":
        _run_privileged_install(["apt-get", "update"], log_func)
        _run_privileged_install(["apt-get", "install", "-y"] + packages, log_func)
    elif manager == "dnf":
        _run_privileged_install(["dnf", "install", "-y"] + packages, log_func)
    elif manager == "pacman":
        _run_privileged_install(["pacman", "-Sy", "--noconfirm"] + packages, log_func)
    elif manager == "zypper":
        _run_privileged_install(["zypper", "--non-interactive", "install"] + packages, log_func)
    elif manager == "apk":
        _run_privileged_install(["apk", "add"] + packages, log_func)

    st = get_shared_folder_dependency_status()
    if need_virtiofsd and not st["virtiofsd"]:
        raise RuntimeError("La instalación terminó, pero virtiofsd todavía no está disponible.")
    if need_smb and not st["smb"]:
        raise RuntimeError("La instalación terminó, pero SMB/smbd todavía no está disponible.")
    return st


