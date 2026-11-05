# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""iso_versions.py — versiones disponibles de cada distro y la URL de su ISO.

Complementa iso_sources.py (que solo sabe devolver "la más reciente"). Funciones
puras, sin PyQt, pensadas para llamarse desde un hilo de fondo.
"""
import re
import threading
import time
import fnmatch
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote

import requests

from . import iso_sources

_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
_TTL = 3600

_FLOORS = {
    "Ubuntu": (18, 4), "Debian": (10, 0), "Fedora": (30,), "Linux Mint": (19, 0),
    "openSUSE": (15, 0), "AlmaLinux": (8, 0), "Rocky Linux": (8, 0), "Pop!_OS": (20, 4),
}
_DEBIAN_CODENAMES = {10: "buster", 11: "bullseye", 12: "bookworm", 13: "trixie", 14: "forky", 15: "duke"}

_MINT_BASE = "https://mirrors.edge.kernel.org/linuxmint/stable/"

# ----------------------------------------------------------------------------
# Utilidades de red / parseo de índices de directorio
# ----------------------------------------------------------------------------
def _get(url, timeout=15):
    r = requests.get(url, timeout=timeout, headers=_UA)
    r.raise_for_status()
    return r.text

def _try_get(url, timeout=15):
    try:
        return _get(url, timeout)
    except requests.RequestException:
        return None

def _head_ok(url, timeout=10):
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout, headers=_UA)
    except requests.RequestException:
        return None
    if r.status_code == 200: return True
    if r.status_code in (404, 410): return False
    return None

def _hrefs(html):
    return [unquote(h) for h in re.findall(r"""href=["']([^"'?#]+)["']""", html or "")]

def _dir_names(html):
    names = []
    for h in _hrefs(html):
        if h.endswith("/") and not h.startswith(".."):
            n = h.rstrip("/").rsplit("/", 1)[-1]
            if n: names.append(n)
    return names

def _file_names(html):
    return [h.rsplit("/", 1)[-1] for h in _hrefs(html) if h and not h.endswith("/")]

def _vt(s):
    return tuple(int(x) for x in re.findall(r"\d+", s))

def _above_floor(distro, s):
    floor = _FLOORS.get(distro)
    return floor is None or _vt(s)[:len(floor)] >= floor

# ----------------------------------------------------------------------------
# Ubuntu, Debian, Fedora, etc. (Sin cambios, se mantienen igual)
# ----------------------------------------------------------------------------
# ... [Aquí va el resto de funciones de Ubuntu, Debian, Fedora, openSUSE, Arch, Alma, Rocky, Pop!_OS] ...
# Para no hacer el mensaje infinito, asumo que tienes esas partes intactas y solo 
# reemplazas las funciones de Mint. Si necesitas el archivo entero, dímelo.

def _versions_mint():
    try:
        html = _get(_MINT_BASE)
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+(?:\.\d+)?", n) and _above_floor("Linux Mint", n)}
        return [{"id": v, "label": f"Linux Mint {v}"} for v in sorted(vers, key=_vt, reverse=True)]
    except Exception:
        return [
            {"id": "22.2", "label": "Linux Mint 22.2"},
            {"id": "22.1", "label": "Linux Mint 22.1"},
            {"id": "22", "label": "Linux Mint 22"},
            {"id": "21.3", "label": "Linux Mint 21.3"}
        ]

def _iso_mint(v):
    # Intentar con la versión exacta
    html = _try_get(f"{_MINT_BASE}{v}/")
    if html:
        files = set(_file_names(html))
        for edition in ("cinnamon", "xfce", "mate"):
            name = f"linuxmint-{v}-{edition}-64bit.iso"
            if name in files:
                return f"{_MINT_BASE}{v}/{name}"
                
    # Si falla, buscar cualquier versión que empiece igual (ej. si pide 22.3, buscar en 22.2 o 22)
    index = _try_get(_MINT_BASE)
    if index:
        dirs = [d for d in _dir_names(index) if re.fullmatch(r"\d+(?:\.\d+)?", d)]
        for d in sorted(dirs, key=_vt, reverse=True):
            if d.startswith(v.split(".")[0]):
                html2 = _try_get(f"{_MINT_BASE}{d}/")
                if html2:
                    files = set(_file_names(html2))
                    for edition in ("cinnamon", "xfce", "mate"):
                        matches = fnmatch.filter(files, f"linuxmint-{d}-{edition}*.iso")
                        if matches:
                            return f"{_MINT_BASE}{d}/{matches[0]}"
                            
    raise RuntimeError(f"No se encontró ISO para Linux Mint {v} en el espejo.")

# ... [El resto del archivo se queda igual] ...