# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Helpers de portabilidad de paths en vm_config.ini.

Marcador: portable_paths_v1

Regla general:
  - Paths DENTRO de la carpeta de la VM (discos, ISOs propias, android_iso,
    iso_path, backing files de clones enlazados) se guardan RELATIVOS a la
    carpeta de la VM.
  - Paths FUERA de la carpeta (carpetas compartidas del host, osx_kvm_source,
    destino de backups, imagen .dmg externa) se guardan ABSOLUTOS: no son
    portables por definición.

Así, mover/copiar la carpeta `VirtualMachines/` a otro host o a otra ruta
dentro del mismo equipo no rompe las referencias internas.

Los paths guardados usan os.sep, que en Linux es "/". El proyecto apunta a
Linux; no se soportan hosts Windows hoy.
"""
import os


# portable_paths_v1


def is_inside(child_path, parent_dir):
    """True si `child_path` está dentro de `parent_dir` (o es igual)."""
    if not child_path or not parent_dir:
        return False
    try:
        child_abs = os.path.abspath(child_path)
        parent_abs = os.path.abspath(parent_dir)
        return os.path.commonpath([child_abs, parent_abs]) == parent_abs
    except (ValueError, TypeError):
        return False


def to_portable(vm_dir, path):
    """Convierte un path a su forma portable.

      - Vacío o None → devuelve tal cual.
      - Dentro de vm_dir → relativo a vm_dir.
      - Fuera de vm_dir → absoluto.
    """
    if not path:
        return path
    if not vm_dir:
        return path
    try:
        abs_path = os.path.abspath(path)
    except (TypeError, ValueError):
        return path
    if is_inside(abs_path, vm_dir):
        try:
            return os.path.relpath(abs_path, start=os.path.abspath(vm_dir))
        except ValueError:
            return abs_path
    return abs_path


def to_absolute(vm_dir, stored):
    """Convierte un path guardado (relativo o absoluto) a absoluto.

      - Vacío o None → tal cual.
      - Absoluto → tal cual (compatibilidad hacia atrás).
      - Relativo → resuelto contra vm_dir.
    """
    if not stored:
        return stored
    if not vm_dir:
        return stored
    try:
        if os.path.isabs(stored):
            return stored
        return os.path.abspath(os.path.join(vm_dir, stored))
    except (TypeError, ValueError):
        return stored


def normalize_storage_devices(vm_dir, devices):
    """Normaliza paths de una lista de storage_devices in-place.

    Afecta a `path` y `own_iso` de cada dispositivo. Devuelve la misma
    lista para encadenar.
    """
    if not isinstance(devices, list):
        return devices
    for d in devices:
        if not isinstance(d, dict):
            continue
        if "path" in d:
            d["path"] = to_portable(vm_dir, d.get("path") or "")
        if "own_iso" in d:
            d["own_iso"] = to_portable(vm_dir, d.get("own_iso") or "")
    return devices


def resolve_storage_devices(vm_dir, devices):
    """Devuelve una COPIA de storage_devices con paths resueltos a absoluto.

    No modifica el original. Útil para consumidores que esperan paths
    absolutos (workers.py, UI).
    """
    if not isinstance(devices, list):
        return devices
    out = []
    for d in devices:
        if not isinstance(d, dict):
            out.append(d)
            continue
        nd = dict(d)
        if nd.get("path"):
            nd["path"] = to_absolute(vm_dir, nd["path"])
        if nd.get("own_iso"):
            nd["own_iso"] = to_absolute(vm_dir, nd["own_iso"])
        out.append(nd)
    return out


# Claves de `extra` que contienen un path a un recurso dentro de la VM.
# NO incluye: shared_folders[].host, osx_kvm_source, backup_schedule.destination,
# mac_custom_image (siempre absolutos por definición: apuntan a recursos
# externos a la VM).
_EXTRA_PATH_KEYS = ("android_iso", "iso_path")


def normalize_extra_paths(vm_dir, extra):
    """Normaliza los paths conocidos dentro del dict `extra` in-place.

    Claves afectadas:
      - storage_devices[].path
      - storage_devices[].own_iso
      - android_iso
      - iso_path

    Devuelve el mismo dict por comodidad.
    """
    if not isinstance(extra, dict):
        return extra
    if isinstance(extra.get("storage_devices"), list):
        normalize_storage_devices(vm_dir, extra["storage_devices"])
    for k in _EXTRA_PATH_KEYS:
        if extra.get(k):
            extra[k] = to_portable(vm_dir, extra[k])
    return extra
