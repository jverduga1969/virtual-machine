# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Utilidades de red del host: listar interfaces/bridges disponibles y
validar/generar nombres de interfaces TAP. Sin dependencias de PyQt.
"""
import os
import re

def list_host_network_interfaces():
    """Lista interfaces de red reales del host (excluye looper/virtuales obvias)."""
    names = []
    try:
        for name in sorted(os.listdir("/sys/class/net")):
            if name == "lo":
                continue
            names.append(name)
    except Exception:
        pass
    return names


def list_host_bridges():
    """Lista bridges Linux existentes y, cuando es posible, sus interfaces miembro."""
    result = []
    base = "/sys/class/net"
    try:
        for name in sorted(os.listdir(base)):
            bridge_dir = os.path.join(base, name, "bridge")
            if not os.path.isdir(bridge_dir):
                continue
            members = []
            brif = os.path.join(base, name, "brif")
            try:
                members = sorted(os.listdir(brif))
            except Exception:
                pass
            result.append((name, members))
    except Exception:
        pass
    return result


def network_interface_exists(name: str) -> bool:
    return bool(name) and os.path.exists(os.path.join("/sys/class/net", name))


def sanitize_tap_name(name: str) -> str:
    """Genera un nombre TAP válido y estable por VM."""
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name or "vm")
    return ("qvm-" + safe)[:15]


