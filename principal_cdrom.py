# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""principal_cdrom.py — la unidad CD/DVD "Principal" de cada máquina virtual.

Toda VM tiene una unidad óptica llamada "Principal". Ahí va la ISO con la que se
instala el sistema, según lo que el usuario elija en "Versión ISO":

    ""      Descargar automáticamente (la más reciente, o la versión concreta)
    "none"  Ninguna: el usuario elige la ISO de su equipo
    "24.04" (Linux) una versión concreta de la distro

La unidad es un dispositivo más de extra["storage_devices"] (device="cdrom"), con
estas marcas propias:

    principal  True                 identifica la unidad
    source     "installer"|"recovery"   la ISO se descargará al iniciar (macOS: recovery)
    iso_key    "none" | "<so>|<perfil>|<elección>"   qué representan source/path
    own_iso    ruta de la ISO propia del usuario (se recuerda al cambiar a descarga)

`iso_key` hace que apply_choice() sea idempotente: solo borra la ISO ya
descargada cuando cambia la elección (otra distro, otra versión, otro Windows),
nunca por abrir una VM o volver a guardar. Módulo sin dependencias de Qt.
"""
import json
import os
import uuid

PRINCIPAL_NAME = "Principal"
CHOICE_LATEST = ""       # descargar automáticamente
CHOICE_NONE = "none"     # el usuario elige su ISO
_DOWNLOAD_SOURCES = ("installer", "recovery")


def _new_id():
    return "dev_" + uuid.uuid4().hex[:12]


def download_source_for(os_type):
    """macOS descarga el System Recovery; Linux y Windows, el instalador."""
    return "recovery" if os_type == "macos" else "installer"


def find_principal(devices):
    for d in devices:
        if isinstance(d, dict) and d.get("device") == "cdrom" and d.get("principal"):
            return d
    return None


def ensure_principal(devices, os_type, new_vm=False):
    """Garantiza que `devices` tenga la unidad Principal. Devuelve (unidad, creada).

    VM nueva      -> se crea una unidad vacía, la primera de las ópticas.
    VM existente  -> nunca se inventa contenido (no debe descargar nada por sorpresa):
                     se marca como Principal una unidad ya llamada así o, si no, la
                     que ya descarga un instalador, o la primera óptica. Si no hay
                     ninguna, se crea vacía y sin fuente."""
    p = find_principal(devices)
    if p:
        p["name"] = PRINCIPAL_NAME
        return p, False

    cds = [d for d in devices if isinstance(d, dict) and d.get("device") == "cdrom"]
    for d in cds:
        if str(d.get("name", "")).strip().lower() == PRINCIPAL_NAME.lower():
            d["name"] = PRINCIPAL_NAME
            d["principal"] = True
            return d, False

    if cds and not new_vm:
        pick = next((d for d in cds if d.get("source") in _DOWNLOAD_SOURCES), cds[0])
        pick["name"] = PRINCIPAL_NAME
        pick["principal"] = True
        return pick, False

    entry = {"id": _new_id(), "name": PRINCIPAL_NAME, "path": "", "device": "cdrom", "principal": True}
    idx = next((i for i, d in enumerate(devices) if isinstance(d, dict) and d.get("device") == "cdrom"),
               len(devices))
    devices.insert(idx if new_vm else len(devices), entry)
    return entry, True


def _abs_if_file(path):
    return os.path.abspath(path) if path and os.path.isfile(path) else ""


def iso_key(os_type, profile, choice):
    return "none" if choice == CHOICE_NONE else f"{os_type}|{profile}|{choice}"


def apply_choice(devices, os_type, choice, profile="", own_iso="", new_vm=False):
    """Configura la unidad Principal según la elección. Devuelve True si algo cambió.

    Solo actúa si la elección cambió respecto a lo que la unidad ya representa
    (iso_key), salvo que se pase una ISO propia nueva."""
    p, _ = ensure_principal(devices, os_type, new_vm=new_vm)
    before = json.dumps(p, sort_keys=True)
    key = iso_key(os_type, profile, choice)
    prev = p.get("iso_key")
    cur_src = p.get("source") or ""
    cur_path = p.get("path") or ""

    if key == prev:
        # Misma elección. Solo se actualiza la ISO propia si el usuario indicó otra.
        if choice == CHOICE_NONE and own_iso:
            own = _abs_if_file(own_iso)
            if own:
                p["path"] = own
                p["own_iso"] = own
    elif choice == CHOICE_NONE:
        if cur_src:                       # venía de una descarga: esa ISO no es "la del usuario"
            p.pop("source", None)
            cur_path = ""
        own = _abs_if_file(own_iso)
        if not own and prev in (None, CHOICE_NONE):
            own = _abs_if_file(cur_path)  # una ISO local que ya estaba puesta
        if not own:
            own = _abs_if_file(p.get("own_iso", ""))
        p["path"] = own
        if own:
            p["own_iso"] = own
        p["iso_key"] = key
    else:
        if prev is None and cur_src in _DOWNLOAD_SOURCES:
            pass                          # configuración anterior: se adopta sin borrar lo descargado
        else:
            if not cur_src and _abs_if_file(cur_path):
                p["own_iso"] = os.path.abspath(cur_path)   # recordar la ISO propia
            p["source"] = download_source_for(os_type)
            p["path"] = ""                # la ISO descargada era de otra elección
        p["iso_key"] = key

    return json.dumps(p, sort_keys=True) != before


def boot_first(tokens, devices):
    """Orden de arranque con la unidad Principal en primer lugar."""
    p = find_principal(devices)
    if not p:
        return list(tokens)
    tok = f"cdrom:{p['id']}"
    return [tok] + [t for t in tokens if t not in (tok, "cdrom")]


def derive_choice(extra, devices, os_type):
    """Elección a mostrar al abrir una VM: (elección, ISO propia).

    La verdad la tiene la unidad: si descarga (source), es descarga; si no, es ISO
    propia. Las VMs antiguas de macOS con imagen personalizada cuentan como propia."""
    extra = extra or {}
    if os_type == "macos" and extra.get("mac_use_custom"):
        return CHOICE_NONE, extra.get("mac_custom_image", "") or ""
    p = find_principal(devices)
    saved = extra.get("iso_choice")
    if p:
        own = p.get("own_iso") or ""
        if p.get("source") in _DOWNLOAD_SOURCES:
            if saved not in (None, CHOICE_NONE):
                return saved, own
            legacy = extra.get("distro_version", "") if os_type == "linux" else ""
            return legacy or CHOICE_LATEST, own
        return CHOICE_NONE, p.get("path") or own
    if saved is not None:
        return saved, ""
    if os_type == "linux" and extra.get("distro_version"):
        # Migración: VMs guardadas por una versión anterior de la app que ya
        # registraba distro_version pero todavía no creaba la unidad Principal.
        return extra["distro_version"], ""
    return CHOICE_LATEST, ""
