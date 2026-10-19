# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_profiles.py — perfiles de uso avanzados para Modo Rapido y VMs.

Modulo puro (sin PyQt): dado un perfil y un SO, devuelve los valores
recomendados.

Estructura por perfil:
    values:    ajustes basicos (RAM, cores, disco, VRAM). Los usa el
               Modo Rapido al crear la VM. NO se tocan al aplicar un
               perfil sobre una VM existente (vm_optimizer_v1).
    advanced:  ajustes avanzados (graficos, CPU, memoria, consola,
               I/O, clipboard, snapshot_compat). Los usa el Modo Rapido
               al crear Y el boton "Aplicar perfil" sobre VMs existentes.

Nota sobre snapshot_compat y clipboard:
    El chardev vdagent (clipboard con consola VNC/SPICE) rompe los
    snapshots completos. Por eso los perfiles que priorizan snapshots
    completos ("general", "light") llevan clipboard="disabled" y
    snapshot_compat=True. Los que priorizan integracion ("dev",
    "gaming") llevan clipboard="bidirectional" y snapshot_compat=False.

Marcadores: vm_profiles_advanced_v1, vm_optimizer_v1_profiles
"""

import copy as _copy

# -----------------------------------------------------------------
# Bloques comunes reutilizados por varios perfiles.
# -----------------------------------------------------------------

_DISK_IO_AUTO = {
    "cache": "auto", "io": "auto", "aio": "auto",
    "discard": "auto", "detect_zeroes": "auto",
}
_DISK_IO_DEV = {
    "cache": "none", "io": "io_uring", "aio": "native",
    "discard": "auto", "detect_zeroes": "auto",
}
_DISK_IO_GAMING = {
    "cache": "none", "io": "io_uring", "aio": "native",
    "discard": "unmap", "detect_zeroes": "unmap",
}
_MEM_OFF      = {"hugepages": False, "prealloc": False, "memfd_lock": False}
_MEM_PREALLOC = {"hugepages": False, "prealloc": True,  "memfd_lock": False}
_MEM_MEMFD    = {"hugepages": False, "prealloc": False, "memfd_lock": True}
_TOPO_AUTO    = {"mode": "auto", "sockets": 1, "cores": 2, "threads": 1}


PROFILES = {
    "general": {
        "id": "general",
        "label": "General / Ofimática",
        "icon": "\U0001F3E0",   # 🏠
        "description": "Navegación, ofimática y uso diario con total compatibilidad.",
        "values": {
            "linux":   {"ram": "4G", "cores": 2, "disk_gb": 40,  "vram": "128M"},
            "windows": {"ram": "4G", "cores": 2, "disk_gb": 60,  "vram": "128M"},
            "macos":   {"ram": "4G", "cores": 2, "disk_gb": 128, "vram": "128M"},
            "android": {"ram": "4G", "cores": 2, "disk_gb": 40,  "vram": "128M"},
        },
        "advanced": {
            "linux": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "disabled",
            },
            "windows": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": True,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "disabled",
            },
            "macos": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "disabled",
            },
            "android": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "none",
            },
        },
    },
    "dev": {
        "id": "dev",
        "label": "Desarrollo",
        "icon": "\U0001F4BB",   # 💻
        "description": "Compilar, contenedores e IDEs pesados (virtualización anidada).",
        "values": {
            "linux":   {"ram": "8G", "cores": 4, "disk_gb": 80,  "vram": "128M"},
            "windows": {"ram": "8G", "cores": 4, "disk_gb": 100, "vram": "128M"},
            "macos":   {"ram": "8G", "cores": 4, "disk_gb": 128, "vram": "128M"},
            "android": {"ram": "8G", "cores": 4, "disk_gb": 60,  "vram": "128M"},
        },
        "advanced": {
            "linux": {
                "graphics_mode": "auto",
                "nested_virt": True, "hyperv_enlightenments": False,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_MEMFD,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_DEV, "clipboard": "bidirectional",
            },
            "windows": {
                "graphics_mode": "auto",
                "nested_virt": True, "hyperv_enlightenments": True,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_MEMFD,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_DEV, "clipboard": "bidirectional",
            },
            "macos": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_MEMFD,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_DEV, "clipboard": "bidirectional",
            },
            "android": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_MEMFD,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_DEV, "clipboard": "none",
            },
        },
    },
    "gaming": {
        "id": "gaming",
        "label": "Juegos",
        "icon": "\U0001F3AE",   # 🎮
        "description": "Aceleración 3D (VirGL/Venus). Nota: Rompe snapshots completos.",
        "values": {
            "linux":   {"ram": "8G", "cores": 4, "disk_gb": 100, "vram": "256M"},
            "windows": {"ram": "8G", "cores": 4, "disk_gb": 100, "vram": "256M"},
            "macos":   None,
            "android": None,
        },
        "advanced": {
            "linux": {
                "graphics_mode": "virgl",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_PREALLOC,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_GAMING, "clipboard": "bidirectional",
            },
            "windows": {
                "graphics_mode": "virgl",
                "nested_virt": False, "hyperv_enlightenments": True,
                "virtio_rng": True, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_PREALLOC,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "spice",
                "snapshot_compat": False,
                "disk_io": _DISK_IO_GAMING, "clipboard": "bidirectional",
            },
            "macos": None,
            "android": None,
        },
    },
    "light": {
        "id": "light",
        "label": "Ligero",
        "icon": "\U0001F5A5\uFE0F",   # 🖥️
        "description": "Recursos mínimos para NAS, pruebas y distro hopping.",
        "values": {
            "linux":   {"ram": "2G", "cores": 2, "disk_gb": 20, "vram": "64M"},
            "windows": {"ram": "4G", "cores": 2, "disk_gb": 40, "vram": "64M"},
            "macos":   None,
            "android": {"ram": "4G", "cores": 2, "disk_gb": 30, "vram": "64M"},
        },
        "advanced": {
            "linux": {
                "graphics_mode": "std",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "vnc",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "disabled",
            },
            "windows": {
                "graphics_mode": "std",
                "nested_virt": False, "hyperv_enlightenments": True,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "vnc",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "disabled",
            },
            "macos": None,
            "android": {
                "graphics_mode": "auto",
                "nested_virt": False, "hyperv_enlightenments": False,
                "virtio_rng": False, "virtio_balloon": False,
                "virtio_watchdog": False,
                "memory_tuning": _MEM_OFF,
                "cpu_topology": _TOPO_AUTO,
                "console_mode": "embedded", "console_protocol": "vnc",
                "snapshot_compat": True,
                "disk_io": _DISK_IO_AUTO, "clipboard": "none",
            },
        },
    },
}

DEFAULT_PROFILE = "general"


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------

def is_supported(profile_id, os_type):
    prof = PROFILES.get(profile_id)
    if not prof:
        return False
    return prof["values"].get(os_type) is not None


def reason_unsupported(profile_id, os_type):
    if is_supported(profile_id, os_type):
        return None
    if os_type == "macos":
        if profile_id == "gaming":
            return "macOS no soporta aceleración 3D en este gestor (solo VGA genérico)."
        if profile_id == "light":
            return "macOS usa un disco fijo de 128 GB y RAM mínima de OSX-KVM."
    if os_type == "android":
        if profile_id == "gaming":
            return "Android usa QXL 2D obligatorio (sin aceleración 3D)."
    return "Este perfil no está disponible para el SO seleccionado."


def profile_defaults(profile_id, os_type, os_version="", host_ram_mb=0):
    """Bloque 'values' (basicos). None si el perfil no aplica al SO."""
    prof = PROFILES.get(profile_id)
    if not prof:
        return None
    vals = prof["values"].get(os_type)
    if vals is None:
        return None
    out = dict(vals)
    if os_type == "windows" and "11" in (os_version or ""):
        if out["disk_gb"] < 64:
            out["disk_gb"] = 64
    if os_type == "macos":
        out["disk_gb"] = 128
    return out


def profile_advanced(profile_id, os_type):
    """Bloque 'advanced' (avanzados). None si el perfil no aplica.

    Marcador: vm_optimizer_v1_profiles. Devuelve una COPIA PROFUNDA del
    bloque para que el llamador pueda mutarlo sin afectar al catalogo.
    """
    prof = PROFILES.get(profile_id)
    if not prof:
        return None
    adv = prof.get("advanced") or {}
    blk = adv.get(os_type)
    if blk is None:
        return None
    return _copy.deepcopy(blk)


def all_profile_ids():
    return list(PROFILES.keys())


def profile_label(profile_id):
    prof = PROFILES.get(profile_id)
    return prof["label"] if prof else profile_id


def profile_icon(profile_id):
    prof = PROFILES.get(profile_id)
    return prof["icon"] if prof else ""


# vm_optimizer_v1_profiles
