# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""iso_versions.py — versiones disponibles de cada distro y la URL de su ISO."""

import re
import fnmatch
import logging
import requests
from urllib.parse import unquote

from . import iso_sources

log = logging.getLogger(__name__)

# Cabeceras para forzar a los servidores (y CDNs como Cloudflare) a no devolver caché
_UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

_FLOORS = {
    "Ubuntu": (18, 4), "Debian": (10, 0), "Fedora": (30,), "Linux Mint": (19, 0),
    "openSUSE": (15, 0), "AlmaLinux": (8, 0), "Rocky Linux": (8, 0), "Pop!_OS": (20, 4),
}

_MINT_BASE = "https://mirrors.edge.kernel.org/linuxmint/stable/"

# ----------------------------------------------------------------------------
# Utilidades de red / parseo
# ----------------------------------------------------------------------------
def _get(url, timeout=10):
    r = requests.get(url, timeout=timeout, headers=_UA)
    r.raise_for_status()
    return r.text

def _try_get(url, timeout=10):
    try:
        return _get(url, timeout)
    except requests.RequestException:
        return None

def _hrefs(html):
    return [unquote(h) for h in re.findall(r"""href=["']([^"'?#]+)["']""", html or "")]

def _dir_names(html):
    names = []
    for h in _hrefs(html):
        if h.endswith("/") and not h.startswith(".."):
            n = h.rstrip("/").rsplit("/", 1)[-1]
            if n and not n.startswith("."): 
                names.append(n)
    return names

def _file_names(html):
    # Limpia rutas relativas como ./ o ../
    return [h.rsplit("/", 1)[-1] for h in _hrefs(html) if h and not h.endswith("/")]

def _vt(s):
    return tuple(int(x) for x in re.findall(r"\d+", s))

def _above_floor(distro, s):
    floor = _FLOORS.get(distro)
    return floor is None or _vt(s)[:len(floor)] >= floor

def _unique_results(results):
    """Elimina duplicados basados en el LABEL (texto visible) para que no se repitan."""
    seen = set()
    out = []
    for r in results:
        if r["label"] not in seen:
            seen.add(r["label"])
            out.append(r)
    return out

def _variant_label(variant):
    mapping = {
        "dvd": "DVD (Completo)", "minimal": "Minimal", "netinst": "Netinst",
        "Live-GNOME": "Live GNOME", "Live-KDE": "Live KDE", "Live-XFCE": "Live XFCE",
        "cinnamon": "Cinnamon", "mate": "MATE", "xfce": "XFCE", "kde": "KDE",
        "gnome": "GNOME", "core": "Core", "lite": "Lite", "education": "Education",
        "desktop": "Desktop", "server": "Server", "installer": "Installer",
        "live": "Live", "official": "Official", "kde-lite": "KDE Lite",
        "dr460nized": "Dr460nized", "mokka": "Mokka", "i3": "i3", "sway": "Sway",
        "fluxbox": "Fluxbox", "Workstation": "Workstation", "Steam-HTPC": "Steam HTPC", 
        "Steam-Handheld": "Steam Handheld", "Pro": "Pro", "standard": "Standard",
        "lxqt": "LXQt", "lxde": "LXDE", "debian-junior": "Debian Junior"
    }
    return mapping.get(variant, variant.capitalize())

# ----------------------------------------------------------------------------
# Fedora
# ----------------------------------------------------------------------------
def _versions_fedora():
    try:
        base = "https://download.fedoraproject.org/pub/fedora/linux/releases/"
        html = _get(base)
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+", n) and _above_floor("Fedora", n)}
        results = []
        for v in sorted(vers, key=_vt, reverse=True):
            idx = _try_get(f"{base}{v}/Workstation/x86_64/iso/")
            if idx:
                matches = fnmatch.filter(_file_names(idx), f"Fedora-Workstation-Live-x86_64-{v}-*.iso")
                if matches:
                    results.append({"id": matches[0], "label": f"Fedora {v} (Workstation)"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_fedora(v):
    m = re.search(r'Live-x86_64-(\d+)-', v)
    if not m: raise RuntimeError("Formato de Fedora inválido")
    major = m.group(1)
    url_actual = f"https://download.fedoraproject.org/pub/fedora/linux/releases/{major}/Workstation/x86_64/iso/{v}"
    url_arch = f"https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/{major}/Workstation/x86_64/iso/{v}"
    if _try_get(url_actual, timeout=5): return url_actual
    return url_arch

# ----------------------------------------------------------------------------
# Ubuntu (y sabores)
# ----------------------------------------------------------------------------
def _versions_ubuntu():
    try:
        base = "https://releases.ubuntu.com/"
        html = _get(base)
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", n) and _above_floor("Ubuntu", n)}
        results = []
        for v in sorted(vers, key=_vt, reverse=True):
            idx = _try_get(f"{base}{v}/")
            if not idx: continue
            for f in _file_names(idx):
                if f.startswith(f"ubuntu-{v}") and f.endswith("-desktop-amd64.iso"):
                    results.append({"id": f, "label": f"Ubuntu {v} (Desktop)"})
                elif f.startswith(f"ubuntu-{v}") and f.endswith("-live-server-amd64.iso"):
                    results.append({"id": f, "label": f"Ubuntu {v} (Server)"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_ubuntu(v):
    m = re.match(r"ubuntu-(\d+\.\d+(?:\.\d+)?)", v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"https://releases.ubuntu.com/{m.group(1)}/{v}"

def _versions_flavor(flavor):
    try:
        base = f"https://cdimage.ubuntu.com/{flavor}/releases/"
        html = _get(base)
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", n)}
        results = []
        for v in sorted(vers, key=_vt, reverse=True):
            idx = _try_get(f"{base}{v}/release/")
            if not idx: continue
            for f in _file_names(idx):
                if f.endswith(".iso") and "desktop-amd64" in f:
                    results.append({"id": f, "label": f"{flavor.capitalize()} {v} (Desktop)"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_flavor(flavor, v):
    m = re.search(r'(\d+\.\d+(?:\.\d+)?)', v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"https://cdimage.ubuntu.com/{flavor}/releases/{m.group(1)}/release/{v}"

# ----------------------------------------------------------------------------
# Debian
# ----------------------------------------------------------------------------
def _versions_debian():
    try:
        results = []
        live_html = _try_get("https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/")
        if live_html:
            for f in _file_names(live_html):
                m = re.match(r"debian-live-(\d+\.\d+\.\d+)-amd64-(.+)\.iso", f)
                if m:
                    ver, variant = m.groups()
                    results.append({"id": f, "label": f"Debian {ver} ({_variant_label(variant)})"})
        
        curr_html = _try_get("https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/")
        if curr_html:
            for f in _file_names(curr_html):
                if f.endswith("-netinst.iso"):
                    m = re.search(r"(\d+\.\d+\.\d+)", f)
                    if m:
                        results.append({"id": f, "label": f"Debian {m.group(1)} (Netinst)"})
        
        arch_html = _try_get("https://cdimage.debian.org/mirror/cdimage/archive/")
        if arch_html:
            dirs = [d for d in _dir_names(arch_html) if re.match(r"\d+\.\d+\.\d+", d)]
            dirs = sorted(dirs, key=_vt, reverse=True)[:3]
            for d in dirs:
                sub = _try_get(f"https://cdimage.debian.org/mirror/cdimage/archive/{d}/amd64/iso-cd/")
                if sub:
                    for f in _file_names(sub):
                        if f.endswith("-netinst.iso"):
                            results.append({"id": f, "label": f"Debian {d} (Netinst)"})
                            
        return _unique_results(sorted(results, key=lambda x: (_vt(x["label"]), x["label"]), reverse=True))
    except Exception:
        return None

def _iso_debian(v):
    if "live" in v:
        return f"https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/{v}"
    m = re.search(r"(\d+\.\d+\.\d+)", v)
    if not m: raise RuntimeError("Versión inválida.")
    ver = m.group(1)
    curr = f"https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/{v}"
    if _try_get(curr, timeout=5): return curr
    return f"https://cdimage.debian.org/mirror/cdimage/archive/{ver}/amd64/iso-cd/{v}"

# ----------------------------------------------------------------------------
# Linux Mint
# ----------------------------------------------------------------------------
def _versions_mint():
    try:
        html = _get(_MINT_BASE)
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+(?:\.\d+)?", n) and _above_floor("Linux Mint", n)}
        results = []
        for v in sorted(vers, key=_vt, reverse=True):
            idx = _try_get(f"{_MINT_BASE}{v}/")
            if not idx: continue
            files = set(_file_names(idx))
            for edition in ("cinnamon", "mate", "xfce"):
                name = f"linuxmint-{v}-{edition}-64bit.iso"
                if name in files:
                    results.append({"id": name, "label": f"Linux Mint {v} ({_variant_label(edition)})"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_mint(v):
    m = re.search(r"(\d+(?:\.\d+)?)", v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"{_MINT_BASE}{m.group(1)}/{v}"

# ----------------------------------------------------------------------------
# Zorin OS
# ----------------------------------------------------------------------------
def _versions_zorin():
    try:
        html = _try_get("https://sourceforge.net/projects/zorin-os/files/")
        if not html: return None
        results = []
        for d in _dir_names(html):
            if re.match(r"\d+(?:\.\d+)?$", d):
                ver = d
                sub = _try_get(f"https://sourceforge.net/projects/zorin-os/files/{ver}/")
                if sub:
                    for sd in _dir_names(sub):
                        if sd in ("Core", "Lite", "Education", "Pro"):
                            results.append({"id": f"{ver}/{sd}", "label": f"Zorin OS {ver} ({_variant_label(sd)})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception as e:
        log.error(f"Error Zorin: {e}")
        return None

def _iso_zorin(v):
    ver, var = v.split("/")
    return f"https://sourceforge.net/projects/zorin-os/files/{ver}/{var}/latest/download"

# ----------------------------------------------------------------------------
# MX Linux
# ----------------------------------------------------------------------------
def _versions_mx():
    try:
        base = "http://mirror.koddos.net/mxlinux-cd/MX/Final/"
        html = _get(base)
        variants = [d for d in _dir_names(html) if d in ("Xfce", "KDE", "Fluxbox")]
        results = []
        for var in variants:
            idx = _try_get(f"{base}{var}/")
            if not idx: continue
            for f in _file_names(idx):
                m = re.match(r"MX-(\d+(?:\.\d+)*)_([A-Za-z]+)_x64\.iso", f)
                if m:
                    ver, vtype = m.groups()
                    results.append({"id": f, "label": f"MX Linux {ver} ({vtype})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception:
        return None

def _iso_mx(v):
    m = re.search(r"MX-(\d+(?:\.\d+)*)_([A-Za-z]+)_x64\.iso", v)
    if m:
        ver, vtype = m.groups()
        return f"http://mirror.koddos.net/mxlinux-cd/MX/Final/{vtype}/{v}"
    raise RuntimeError("Formato MX inválido.")

# ----------------------------------------------------------------------------
# AlmaLinux & Rocky Linux
# ----------------------------------------------------------------------------
def _versions_almalinux():
    try:
        base = "https://repo.almalinux.org/almalinux/"
        html = _get(base)
        majors = [n for n in _dir_names(html) if re.fullmatch(r"\d+", n)]
        results = []
        for major in majors:
            iso_html = _try_get(f"{base}{major}/isos/x86_64/")
            if iso_html:
                for f in _file_names(iso_html):
                    m = re.match(rf"AlmaLinux-({major}\.\d+)-x86_64-(.+)\.iso", f)
                    if m:
                        ver, var = m.groups()
                        if var == "boot": continue
                        results.append({"id": f, "label": f"AlmaLinux {ver} ({_variant_label(var)})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception:
        return None

def _iso_almalinux(v):
    m = re.search(r'AlmaLinux-(\d+)\.', v)
    if not m: raise RuntimeError("Formato inválido.")
    return f"https://repo.almalinux.org/almalinux/{m.group(1)}/isos/x86_64/{v}"

def _versions_rocky():
    try:
        base = "https://download.rockylinux.org/pub/rocky/"
        html = _get(base)
        majors = [n for n in _dir_names(html) if re.fullmatch(r"\d+", n)]
        results = []
        for major in majors:
            iso_html = _try_get(f"{base}{major}/isos/x86_64/")
            if iso_html:
                for f in _file_names(iso_html):
                    m = re.match(rf"Rocky-({major}\.\d+)-x86_64-(.+)\.iso", f)
                    if m:
                        ver, var = m.groups()
                        if var == "boot": continue
                        results.append({"id": f, "label": f"Rocky Linux {ver} ({_variant_label(var)})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception:
        return None

def _iso_rocky(v):
    m = re.search(r'Rocky-(\d+)\.', v)
    if not m: raise RuntimeError("Formato inválido.")
    return f"https://download.rockylinux.org/pub/rocky/{m.group(1)}/isos/x86_64/{v}"

# ----------------------------------------------------------------------------
# openSUSE
# ----------------------------------------------------------------------------
def _versions_opensuse():
    try:
        results = []
        leap_html = _try_get("https://download.opensuse.org/distribution/leap/")
        if leap_html:
            for v in [n for n in _dir_names(leap_html) if re.fullmatch(r"\d+\.\d+", n)]:
                idx = _try_get(f"https://download.opensuse.org/distribution/leap/{v}/iso/")
                if idx:
                    for f in _file_names(idx):
                        if "DVD-x86_64-Media.iso" in f:
                            results.append({"id": f, "label": f"openSUSE Leap {v} (DVD)"})
                        elif "NET-x86_64-Media.iso" in f:
                            results.append({"id": f, "label": f"openSUSE Leap {v} (Network)"})
        
        tw_html = _try_get("https://download.opensuse.org/tumbleweed/iso/")
        if tw_html:
            for f in _file_names(tw_html):
                if "Media.iso" in f and "Tumbleweed" in f:
                    m = re.search(r"openSUSE-Tumbleweed-(.*?)-x86_64-Snapshot(\d+)-Media.iso", f)
                    if m:
                        var, snap = m.groups()
                        results.append({"id": f, "label": f"openSUSE Tumbleweed ({_variant_label(var)}) - {snap}"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_opensuse(v):
    if "Leap" in v:
        ver = re.search(r"Leap-(\d+\.\d+)", v).group(1)
        return f"https://download.opensuse.org/distribution/leap/{ver}/iso/{v}"
    return f"https://download.opensuse.org/tumbleweed/iso/{v}"

# ----------------------------------------------------------------------------
# Garuda Linux
# ----------------------------------------------------------------------------
def _versions_garuda():
    try:
        base = "https://iso.builds.garudalinux.org/iso/garuda/"
        html = _get(base)
        variants = [d for d in _dir_names(html) if not d.startswith(".")]
        results = []
        for var in variants:
            idx = _try_get(f"{base}{var}/")
            if idx:
                dates = [d for d in _dir_names(idx) if re.fullmatch(r"\d{6}", d)]
                for date in dates:
                    results.append({"id": f"{var}/{date}", "label": f"Garuda {_variant_label(var)} ({date})"})
        return _unique_results(sorted(results, key=lambda x: x["label"], reverse=True)[:30])
    except Exception:
        return None

def _iso_garuda(v):
    var, date = v.split("/")
    url_dir = f"https://iso.builds.garudalinux.org/iso/garuda/{var}/{date}/"
    html = _try_get(url_dir)
    if html:
        for f in _file_names(html):
            if f.endswith(".iso"): return url_dir + f
    raise RuntimeError("No se encontró ISO para Garuda.")

# ----------------------------------------------------------------------------
# Manjaro Linux
# ----------------------------------------------------------------------------
def _versions_manjaro():
    try:
        results = []
        for var in ("xfce", "kde", "gnome"):
            html = _try_get(f"https://sourceforge.net/projects/manjarolinux/files/{var}/")
            if html:
                for d in _dir_names(html):
                    if re.match(r"\d+\.\d+\.\d+$", d):
                        ver = d
                        results.append({"id": f"{var}/{ver}", "label": f"Manjaro {ver} ({var.upper()})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception as e:
        log.error(f"Error Manjaro: {e}")
        return None

def _iso_manjaro(v):
    var, ver = v.split("/")
    return f"https://sourceforge.net/projects/manjarolinux/files/{var}/{ver}/latest/download"

# ----------------------------------------------------------------------------
# Nobara Project
# ----------------------------------------------------------------------------
def _versions_nobara():
    try:
        base = "https://nobara-images.nobaraproject.org/"
        html = _get(base)
        results = []
        for f in _file_names(html):
            m = re.match(r"Nobara-(\d+)-(Official|GNOME|KDE|Steam-HTPC|Steam-Handheld).*\.iso", f)
            if m:
                ver, var = m.groups()
                results.append({"id": f, "label": f"Nobara {ver} ({_variant_label(var)})"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception as e:
        log.error(f"Error Nobara: {e}")
        return None

def _iso_nobara(v):
    return f"https://nobara-images.nobaraproject.org/{v}"

# ----------------------------------------------------------------------------
# EndeavourOS
# ----------------------------------------------------------------------------
def _versions_endeavour():
    try:
        base = "https://mirrors.urbanwave.co.za/endeavouros/iso/"
        html = _get(base)
        results = []
        for f in _file_names(html):
            if f.endswith(".iso"):
                m = re.search(r"EndeavourOS_(.+)-(\d+\.\d+\.\d+)\.iso", f)
                if m:
                    name, date = m.groups()
                    results.append({"id": f, "label": f"EndeavourOS {name} ({date})"})
        return _unique_results(sorted(results, key=lambda x: x["label"], reverse=True))
    except Exception:
        return None

def _iso_endeavour(v):
    return f"https://mirrors.urbanwave.co.za/endeavouros/iso/{v}"

# ----------------------------------------------------------------------------
# Kali Linux
# ----------------------------------------------------------------------------
def _versions_kali():
    try:
        html = _get("https://cdimage.kali.org/")
        vers = set()
        for h in _dir_names(html):
            m = re.match(r"kali-(\d{4}\.\d+)", h)
            if m: vers.add(m.group(1))
        results = []
        for v in sorted(vers, reverse=True):
            idx = _try_get(f"https://cdimage.kali.org/kali-{v}/")
            if idx:
                for f in _file_names(idx):
                    if f.endswith(".iso") and "amd64" in f:
                        var = "Installer" if "installer" in f else "Live"
                        results.append({"id": f, "label": f"Kali Linux {v} ({var})"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_kali(v):
    m = re.search(r"kali-(\d{4}\.\d+)", v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"https://cdimage.kali.org/kali-{m.group(1)}/{v}"

# ----------------------------------------------------------------------------
# Pop!_OS
# ----------------------------------------------------------------------------
def _versions_popos():
    try:
        html = _get("https://iso.pop-os.org/")
        vers = {n for n in _dir_names(html) if re.fullmatch(r"\d+\.\d+", n)}
        results = []
        for v in sorted(vers, key=_vt, reverse=True):
            idx = _try_get(f"https://iso.pop-os.org/{v}/amd64/intel/")
            if idx:
                for f in _file_names(idx):
                    if f.endswith(".iso"):
                        results.append({"id": f, "label": f"Pop!_OS {v}"})
        return _unique_results(results)
    except Exception:
        return None

def _iso_popos(v):
    m = re.search(r"pop-os_(\d+\.\d+)", v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"https://iso.pop-os.org/{m.group(1)}/amd64/intel/{v}"

# ----------------------------------------------------------------------------
# Arch Linux
# ----------------------------------------------------------------------------
def _versions_arch():
    try:
        html = _get("https://geo.mirror.pkgbuild.com/iso/")
        versions = _dir_names(html)
        if not versions: return None
        latest = versions[-1]
        idx = _try_get(f"https://geo.mirror.pkgbuild.com/iso/{latest}/")
        if idx:
            for f in _file_names(idx):
                if f.endswith(".iso"):
                    return [{"id": f, "label": f"Arch Linux {latest}"}]
        return None
    except Exception:
        return None

def _iso_arch(v):
    m = re.search(r"(\d{4}\.\d{2}\.\d{2})", v)
    if not m: raise RuntimeError("Versión inválida.")
    return f"https://geo.mirror.pkgbuild.com/iso/{m.group(1)}/{v}"

# ----------------------------------------------------------------------------
# elementary OS
# ----------------------------------------------------------------------------
def _versions_elementary():
    try:
        r = requests.get("https://api.github.com/repos/elementary/os/releases", timeout=10, headers=_UA)
        data = r.json()
        results = []
        for rel in data:
            tag = rel.get("tag_name", "").replace("v", "")
            if re.match(r"\d+\.\d+", tag):
                for asset in rel.get("assets", []):
                    if asset["name"].endswith(".iso"):
                        results.append({"id": asset["name"], "label": f"elementary OS {tag}"})
        return _unique_results(sorted(results, key=lambda x: _vt(x["label"]), reverse=True))
    except Exception:
        return None

def _iso_elementary(v):
    try:
        r = requests.get("https://api.github.com/repos/elementary/os/releases", timeout=10, headers=_UA)
        data = r.json()
        for rel in data:
            for asset in rel.get("assets", []):
                if asset["name"] == v:
                    return asset["browser_download_url"]
    except Exception:
        pass
    return iso_sources.get_latest_iso_url("elementary OS")

# ----------------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------------
_ISO_URL_FUNCS = {
    "Ubuntu": _iso_ubuntu, "Linux Mint": _iso_mint, "Debian": _iso_debian,
    "Fedora": _iso_fedora, "Pop!_OS": _iso_popos, "openSUSE": _iso_opensuse,
    "Kali Linux": _iso_kali, "Nobara": _iso_nobara, "EndeavourOS": _iso_endeavour,
    "elementary OS": _iso_elementary, "Garuda Linux": _iso_garuda,
    "AlmaLinux": _iso_almalinux, "Rocky Linux": _iso_rocky, "Manjaro": _iso_manjaro,
    "Zorin OS": _iso_zorin, "MX Linux": _iso_mx, "Arch Linux": _iso_arch,
    "Lubuntu": lambda v: _iso_flavor("lubuntu", v), "Xubuntu": lambda v: _iso_flavor("xubuntu", v),
    "Kubuntu": lambda v: _iso_flavor("kubuntu", v),
}

_VERSIONS_FUNCS = {
    "Ubuntu": _versions_ubuntu, "Linux Mint": _versions_mint, "Debian": _versions_debian,
    "Fedora": _versions_fedora, "Pop!_OS": _versions_popos, "openSUSE": _versions_opensuse,
    "Kali Linux": _versions_kali, "Nobara": _versions_nobara, "EndeavourOS": _versions_endeavour,
    "elementary OS": _versions_elementary, "Garuda Linux": _versions_garuda,
    "AlmaLinux": _versions_almalinux, "Rocky Linux": _versions_rocky, "Manjaro": _versions_manjaro,
    "Zorin OS": _versions_zorin, "MX Linux": _versions_mx, "Arch Linux": _versions_arch,
    "Lubuntu": lambda: _versions_flavor("lubuntu"), "Xubuntu": lambda: _versions_flavor("xubuntu"),
    "Kubuntu": lambda: _versions_flavor("kubuntu"),
}

def supports_versions(distro: str) -> bool:
    return distro in _ISO_URL_FUNCS

def get_available_versions(distro: str) -> list[dict]:
    func = _VERSIONS_FUNCS.get(distro)
    if not func: return None
    try:
        return func()
    except Exception as e:
        log.error(f"Error obteniendo versiones para {distro}: {e}")
        return None

def get_iso_url(distro: str, version_id: str) -> str:
    func = _ISO_URL_FUNCS.get(distro)
    if not func: return iso_sources.get_latest_iso_url(distro)
    return func(version_id)