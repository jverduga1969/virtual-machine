# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""iso_versions.py — versiones disponibles de cada distro y la URL de su ISO.

Complementa iso_sources.py (que solo sabe devolver "la más reciente"). Funciones
puras, sin PyQt, pensadas para llamarse desde un hilo de fondo.

    list_distro_versions("Ubuntu")   -> [{"id": "26.04", "label": "Ubuntu 26.04.1 LTS"}, ...]
    get_iso_url("Ubuntu", "24.04")   -> URL de la ISO de esa versión
    get_iso_url("Ubuntu")            -> la más reciente (comportamiento anterior)

El "id" de cada versión es lo que se guarda en la configuración de la VM; el
"label" es lo que ve el usuario. Las listas se obtienen de los índices de los
espejos oficiales y se cachean una hora en memoria.

Distros con lista de versiones: Ubuntu, Debian, Fedora, Linux Mint, openSUSE,
Arch Linux, AlmaLinux, Rocky Linux y Pop!_OS. Manjaro solo ofrece "más reciente".
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote

import requests

import iso_sources

_UA = {"User-Agent": "VM-Manager/1.0 (selector de versiones de ISO)"}
_TTL = 3600  # segundos que se conserva una lista en memoria

# Versión mínima que se ofrece (las anteriores ya no arrancan bien en QEMU/UEFI
# moderno o tienen estructuras de ISO distintas). Tupla comparable.
_FLOORS = {
    "Ubuntu": (18, 4), "Debian": (10, 0), "Fedora": (30,), "Linux Mint": (19, 0),
    "openSUSE": (15, 0), "AlmaLinux": (8, 0), "Rocky Linux": (8, 0), "Pop!_OS": (20, 4),
}
_DEBIAN_CODENAMES = {10: "buster", 11: "bullseye", 12: "bookworm", 13: "trixie", 14: "forky", 15: "duke"}


# ----------------------------------------------------------------------------
# Utilidades de red / parseo de índices de directorio
# ----------------------------------------------------------------------------
def _get(url, timeout=15):
    r = requests.get(url, timeout=timeout, headers=_UA)
    r.raise_for_status()
    return r.text


def _try_get(url, timeout=15):
    """Texto de la URL o None si no existe / falla (para probar varias fuentes)."""
    try:
        return _get(url, timeout)
    except requests.RequestException:
        return None


def _head_ok(url, timeout=10):
    """True si existe, False si el servidor dice que no, None si no se pudo saber."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout, headers=_UA)
    except requests.RequestException:
        return None
    if r.status_code == 200:
        return True
    if r.status_code in (404, 410):
        return False
    return None


def _hrefs(html):
    return [unquote(h) for h in re.findall(r"""href=["']([^"'?#]+)["']""", html or "")]


def _dir_names(html):
    """Nombres de subdirectorios de un índice (enlaces que terminan en '/')."""
    names = []
    for h in _hrefs(html):
        if h.endswith("/") and not h.startswith(".."):
            n = h.rstrip("/").rsplit("/", 1)[-1]
            if n:
                names.append(n)
    return names


def _file_names(html):
    return [h.rsplit("/", 1)[-1] for h in _hrefs(html) if h and not h.endswith("/")]


def _vt(s):
    """'24.04.5.1' -> (24, 4, 5, 1) para comparar versiones."""
    return tuple(int(x) for x in re.findall(r"\d+", s))


def _above_floor(distro, s):
    floor = _FLOORS.get(distro)
    return floor is None or _vt(s)[:len(floor)] >= floor


# ----------------------------------------------------------------------------
# Ubuntu — releases.ubuntu.com (con soporte) + old-releases.ubuntu.com (caducadas)
# ----------------------------------------------------------------------------
_UBUNTU_BASES = ("https://releases.ubuntu.com/", "https://old-releases.ubuntu.com/releases/")


def _versions_ubuntu():
    series, reachable = {}, False
    for base in _UBUNTU_BASES:
        html = _try_get(base)
        if html is None:
            continue
        reachable = True
        for n in _dir_names(html):
            m = re.fullmatch(r"(\d{2}\.\d{2})((?:\.\d+){0,2})", n)
            if not m or not _above_floor("Ubuntu", m.group(1)):
                continue
            s = m.group(1)
            if s not in series or _vt(n) > _vt(series[s]):
                series[s] = n
    if not reachable:
        raise RuntimeError("No se pudo consultar releases.ubuntu.com ni old-releases.ubuntu.com.")
    out = []
    for s in sorted(series, key=_vt, reverse=True):
        lts = s.endswith(".04") and int(s[:2]) % 2 == 0
        out.append({"id": s, "label": f"Ubuntu {series[s]}" + (" LTS" if lts else "")})
    return out


def _iso_from_ubuntu_dir(html):
    isos = _file_names(html)
    for kind in ("desktop", "live-server"):
        c = [f for f in isos if re.fullmatch(rf"ubuntu-\d+(?:\.\d+){{1,3}}-{kind}-amd64\.iso", f)]
        if c:
            return max(c, key=_vt)
    return None


def _iso_ubuntu(series):
    for base in _UBUNTU_BASES:
        html = _try_get(f"{base}{series}/")
        name = _iso_from_ubuntu_dir(html) if html else None
        if name:
            return f"{base}{series}/{name}"
        # A veces la carpeta de la serie no tiene ISO y sí las de punto (24.04.x).
        index = _try_get(base)
        if not index:
            continue
        points = sorted((n for n in _dir_names(index) if re.fullmatch(re.escape(series) + r"\.\d+(?:\.\d+)?", n)),
                        key=_vt, reverse=True)
        for p in points:
            html = _try_get(f"{base}{p}/")
            name = _iso_from_ubuntu_dir(html) if html else None
            if name:
                return f"{base}{p}/{name}"
    raise RuntimeError(f"No se encontró ISO de Ubuntu {series} en releases.ubuntu.com ni en old-releases.")


# ----------------------------------------------------------------------------
# Debian — cdimage/release (vigentes) + cdimage/archive (anteriores)
# ----------------------------------------------------------------------------
_DEBIAN_BASES = ("https://cdimage.debian.org/cdimage/release/", "https://cdimage.debian.org/cdimage/archive/")


def _versions_debian():
    newest, reachable = {}, False
    for base in _DEBIAN_BASES:
        html = _try_get(base)
        if html is None:
            continue
        reachable = True
        for n in _dir_names(html):
            if not re.fullmatch(r"\d+\.\d+\.\d+", n):
                continue
            major = _vt(n)[0]
            if not _above_floor("Debian", n):
                continue
            if major not in newest or _vt(n) > _vt(newest[major]):
                newest[major] = n
    if not reachable:
        raise RuntimeError("No se pudo consultar cdimage.debian.org.")
    out = []
    for major in sorted(newest, reverse=True):
        code = _DEBIAN_CODENAMES.get(major)
        out.append({"id": newest[major],
                    "label": f"Debian {major}" + (f" \"{code}\"" if code else "") + f" ({newest[major]})"})
    return out


def _iso_debian(full):
    for base in _DEBIAN_BASES:
        d = f"{base}{full}/amd64/iso-cd/"
        html = _try_get(d)
        if not html:
            continue
        c = [f for f in _file_names(html) if re.fullmatch(r"debian-[\d.]+-amd64-netinst\.iso", f)]
        if c:
            return d + max(c, key=_vt)
    raise RuntimeError(f"No se encontró la ISO netinst de Debian {full}.")


# ----------------------------------------------------------------------------
# Fedora Workstation — releases (vigentes) + archive (caducadas)
# ----------------------------------------------------------------------------
_FEDORA_BASES = ("https://dl.fedoraproject.org/pub/fedora/linux/releases/",
                 "https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/")


def _versions_fedora():
    found, reachable = set(), False
    for base in _FEDORA_BASES:
        html = _try_get(base)
        if html is None:
            continue
        reachable = True
        for n in _dir_names(html):
            if re.fullmatch(r"\d+", n) and _above_floor("Fedora", n):
                found.add(int(n))
    if not reachable:
        raise RuntimeError("No se pudo consultar los repositorios de Fedora.")
    return [{"id": str(n), "label": f"Fedora {n} Workstation"} for n in sorted(found, reverse=True)]


def _iso_fedora(n):
    for base in _FEDORA_BASES:
        d = f"{base}{n}/Workstation/x86_64/iso/"
        html = _try_get(d)
        if not html:
            continue
        # Se excluye la variante OSBuild ("-osb-"): solo interesa la Live normal.
        c = [f for f in _file_names(html)
             if f.startswith("Fedora-Workstation-Live") and f.endswith(".iso") and "-osb-" not in f]
        if c:
            return d + sorted(c)[-1]
    raise RuntimeError(f"No se encontró la ISO Live de Fedora {n} Workstation.")


# ----------------------------------------------------------------------------
# Linux Mint — stable/<versión>/linuxmint-<v>-<edición>-64bit.iso
# ----------------------------------------------------------------------------
_MINT_BASE = "https://mirrors.edge.kernel.org/linuxmint/stable/"


def _versions_mint():
    html = _get(_MINT_BASE)
    vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+(?:\.\d+)?", n) and _above_floor("Linux Mint", n)}
    return [{"id": v, "label": f"Linux Mint {v}"} for v in sorted(vers, key=_vt, reverse=True)]


def _iso_mint(v):
    html = _try_get(f"{_MINT_BASE}{v}/")
    if html:
        files = set(_file_names(html))
        for edition in ("cinnamon", "xfce", "mate"):
            name = f"linuxmint-{v}-{edition}-64bit.iso"
            if name in files:
                return f"{_MINT_BASE}{v}/{name}"
    raise RuntimeError(f"No se encontró ISO para Linux Mint {v}.")


# ----------------------------------------------------------------------------
# openSUSE — Leap (15.x: iso/DVD; 16.x: offline/installer) + Tumbleweed
# ----------------------------------------------------------------------------
_LEAP_BASE = "https://download.opensuse.org/distribution/leap/"
_TUMBLEWEED_URL = "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-x86_64-Current.iso"


def _leap_iso_url(v):
    if _vt(v)[0] >= 16:
        return f"{_LEAP_BASE}{v}/offline/Leap-{v}-offline-installer-x86_64.install.iso"
    return f"{_LEAP_BASE}{v}/iso/openSUSE-Leap-{v}-DVD-x86_64-Media.iso"


def _versions_opensuse():
    html = _get(_LEAP_BASE)
    vers = sorted({n for n in _dir_names(html) if re.fullmatch(r"\d+\.\d+", n) and _above_floor("openSUSE", n)},
                  key=_vt, reverse=True)
    candidates = [(v, f"openSUSE Leap {v}", _leap_iso_url(v)) for v in vers]
    candidates.append(("tumbleweed", "openSUSE Tumbleweed (rolling)", _TUMBLEWEED_URL))
    # Un directorio de Leap puede existir sin ISO publicada (versión en desarrollo):
    # se comprueba con HEAD y solo se descartan las que el servidor dice que no existen.
    with ThreadPoolExecutor(max_workers=6) as pool:
        checks = list(pool.map(lambda c: _head_ok(c[2]), candidates))
    out = [{"id": vid, "label": label} for (vid, label, _), ok in zip(candidates, checks) if ok is not False]
    if not out:
        raise RuntimeError("No se encontraron ISOs de openSUSE.")
    return out


def _iso_opensuse(vid):
    if vid == "tumbleweed":
        return _TUMBLEWEED_URL
    url = _leap_iso_url(vid)
    if _head_ok(url) is False:
        raise RuntimeError(f"No se encontró la ISO de openSUSE Leap {vid}.")
    return url


# ----------------------------------------------------------------------------
# Arch Linux — iso/AAAA.MM.DD/archlinux-AAAA.MM.DD-x86_64.iso (mensuales)
# ----------------------------------------------------------------------------
_ARCH_BASE = "https://geo.mirror.pkgbuild.com/iso/"


def _versions_arch():
    html = _get(_ARCH_BASE)
    dates = sorted({n for n in _dir_names(html) if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", n)}, reverse=True)[:12]
    if not dates:
        raise RuntimeError("No se encontraron ISOs de Arch Linux en el espejo.")
    return [{"id": d, "label": f"Arch Linux {d}"} for d in dates]


def _iso_arch(date):
    d = f"{_ARCH_BASE}{date}/"
    html = _try_get(d)
    if html:
        c = [f for f in _file_names(html) if re.fullmatch(r"archlinux-[\d.]+-x86_64\.iso", f)]
        if c:
            return d + max(c, key=_vt)
    raise RuntimeError(f"No se encontró la ISO de Arch Linux {date}.")


# ----------------------------------------------------------------------------
# AlmaLinux / Rocky Linux — una carpeta por versión menor (vigente + vault)
# ----------------------------------------------------------------------------
_ALMA_BASES = ("https://repo.almalinux.org/almalinux/", "https://vault.almalinux.org/")
_ROCKY_BASES = ("https://download.rockylinux.org/pub/rocky/", "https://dl.rockylinux.org/vault/rocky/")


def _versions_el(distro, bases):
    found, reachable = set(), False
    for base in bases:
        html = _try_get(base)
        if html is None:
            continue
        reachable = True
        for n in _dir_names(html):
            if re.fullmatch(r"\d+\.\d+", n) and _above_floor(distro, n):
                found.add(n)
    if not reachable:
        raise RuntimeError(f"No se pudo consultar el repositorio de {distro}.")
    return [{"id": v, "label": f"{distro} {v}"} for v in sorted(found, key=_vt, reverse=True)]


def _iso_el(distro, bases, pattern, v):
    for base in bases:
        d = f"{base}{v}/isos/x86_64/"
        html = _try_get(d)
        if not html:
            continue
        c = [f for f in _file_names(html) if re.fullmatch(pattern.format(v=re.escape(v)), f)]
        if c:
            return d + sorted(c)[0]
    raise RuntimeError(f"No se encontró la ISO DVD de {distro} {v}.")


# ----------------------------------------------------------------------------
# Pop!_OS — iso.pop-os.org/<versión>/amd64/intel/...
# ----------------------------------------------------------------------------
_POP_BASE = "https://iso.pop-os.org/"


def _versions_pop():
    html = _get(_POP_BASE)
    vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+\.\d+", n) and _above_floor("Pop!_OS", n)}
    return [{"id": v, "label": f"Pop!_OS {v}"} for v in sorted(vers, key=_vt, reverse=True)]


def _iso_pop(v):
    d = f"{_POP_BASE}{v}/amd64/intel/"
    html = _try_get(d)
    if not html:
        raise RuntimeError(f"No se encontró Pop!_OS {v} para Intel/AMD.")
    pat = r"pop-os_[\d.]+_amd64_intel_\d+\.iso"
    direct = [f for f in _file_names(html) if re.fullmatch(pat, f)]
    if direct:  # ISO directamente en la carpeta
        return d + max(direct, key=_vt)
    # Estructura con una subcarpeta por compilación: se usa la más alta que tenga ISO.
    for sub in sorted((n for n in _dir_names(html) if n.isdigit()), key=int, reverse=True):
        h2 = _try_get(f"{d}{sub}/")
        c = [f for f in _file_names(h2 or "") if re.fullmatch(pat, f)]
        if c:
            return f"{d}{sub}/{max(c, key=_vt)}"
    raise RuntimeError(f"No se encontró ISO de Pop!_OS {v}.")


# ----------------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------------
VERSION_LISTERS = {
    "Ubuntu": _versions_ubuntu,
    "Debian": _versions_debian,
    "Fedora": _versions_fedora,
    "Linux Mint": _versions_mint,
    "openSUSE": _versions_opensuse,
    "Arch Linux": _versions_arch,
    "AlmaLinux": lambda: _versions_el("AlmaLinux", _ALMA_BASES),
    "Rocky Linux": lambda: _versions_el("Rocky Linux", _ROCKY_BASES),
    "Pop!_OS": _versions_pop,
}

ISO_RESOLVERS = {
    "Ubuntu": _iso_ubuntu,
    "Debian": _iso_debian,
    "Fedora": _iso_fedora,
    "Linux Mint": _iso_mint,
    "openSUSE": _iso_opensuse,
    "Arch Linux": _iso_arch,
    "AlmaLinux": lambda v: _iso_el("AlmaLinux", _ALMA_BASES, r"AlmaLinux-{v}-x86_64-dvd\.iso", v),
    "Rocky Linux": lambda v: _iso_el("Rocky Linux", _ROCKY_BASES, r"Rocky-{v}-x86_64-dvd1?\.iso", v),
    "Pop!_OS": _iso_pop,
}

_CACHE = {}
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def supports_versions(distro):
    """¿Esta distro ofrece lista de versiones? (Manjaro y las no soportadas: no)."""
    return distro in VERSION_LISTERS


def supports_auto_download(distro):
    """¿La app sabe descargar la ISO de esta distro (última o por versión)?"""
    return distro in iso_sources.SUPPORTED_AUTODETECT


def list_distro_versions(distro, force=False):
    """Lista [{"id","label"}, ...] de versiones, de la más nueva a la más antigua.

    Lanza RuntimeError si el espejo no responde. Las listas se cachean una hora;
    si dos hilos piden la misma distro a la vez, el segundo espera al primero."""
    lister = VERSION_LISTERS.get(distro)
    if lister is None:
        return []
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(distro, threading.Lock())
    with lock:
        hit = _CACHE.get(distro)
        if hit and not force and time.time() - hit[0] < _TTL:
            return [dict(v) for v in hit[1]]
        versions = lister()
        _CACHE[distro] = (time.time(), versions)
        return [dict(v) for v in versions]


def get_iso_url(distro, version_id=""):
    """URL de la ISO. Sin version_id: la más reciente (como get_latest_iso_url)."""
    if version_id:
        resolver = ISO_RESOLVERS.get(distro)
        if resolver is None:
            raise ValueError(f"No hay selección de versión para: {distro}")
        return resolver(version_id)
    # "Más reciente". En Arch y openSUSE el método anterior ya no encuentra la ISO
    # (Arch usa carpetas AAAA.MM.DD y Leap 16 cambió la estructura), así que se
    # resuelven con las listas nuevas; el resto sigue igual que antes.
    if distro in ("Arch Linux", "openSUSE"):
        versions = list_distro_versions(distro)
        vid = next((v["id"] for v in versions if v["id"] != "tumbleweed"), None)
        if not vid:
            raise RuntimeError(f"No se encontraron versiones de {distro}.")
        return ISO_RESOLVERS[distro](vid)
    return iso_sources.get_latest_iso_url(distro)


def iso_filename_tag(version_id):
    """Sufijo seguro para el nombre del archivo descargado ('' si no hay versión).
    Evita reutilizar una ISO de otra versión que ya estuviera en la carpeta."""
    return ("_" + re.sub(r"[^A-Za-z0-9_.-]", "_", str(version_id).lower())) if version_id else ""
