# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Detección de la última ISO disponible para cada distro/versión soportada.

Funciones puras (sin PyQt): dado un nombre de distro o versión de Windows,
devuelven la URL de descarga más reciente. Extraído de virtual_machine.py
para separar "de dónde saco la ISO" de la lógica de la interfaz.
"""
import os
import re
import subprocess
import requests
from packaging import version

SUPPORTED_AUTODETECT = {
    "Ubuntu", "Debian", "Fedora", "Arch Linux", "Linux Mint",
    "Manjaro Linux", "openSUSE", "Pop!_OS", "AlmaLinux", "Rocky Linux",
}


def get_latest_iso_url(distro: str) -> str:
    """Devuelve la URL de la ISO más reciente para una distro soportada.
    Lanza RuntimeError/ValueError con un mensaje claro si falla."""
    handlers = {
        "Ubuntu": _latest_ubuntu,
        "Debian": _latest_debian,
        "Fedora": _latest_fedora,
        "Arch Linux": _latest_arch,
        "Linux Mint": _latest_mint,
        "Manjaro Linux": _latest_manjaro,
        "openSUSE": _latest_opensuse,
        "Pop!_OS": _latest_popos,
        "AlmaLinux": _latest_almalinux,
        "Rocky Linux": _latest_rocky,
    }
    fn = handlers.get(distro)
    if fn is None:
        raise ValueError(f"Auto-detección no soportada para: {distro}")
    return fn()


def _latest_ubuntu() -> str:
    base = "https://releases.ubuntu.com/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Ubuntu.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = requests.get(base + latest + "/", timeout=15).text
    m = re.search(rf'ubuntu-{re.escape(latest)}[\d.]*-desktop-amd64\.iso', idx)
    if not m:
        m = re.search(rf'ubuntu-{re.escape(latest)}[\d.]*-live-server-amd64\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO de escritorio para Ubuntu {latest}.")
    return base + latest + "/" + m.group(0)


def _latest_debian() -> str:
    base = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    html = requests.get(base, timeout=15).text
    m = re.search(r'debian-([\d.]+)-amd64-netinst\.iso', html)
    if not m:
        raise RuntimeError("No se encontró ISO de Debian en el índice actual.")
    return base + m.group(0)


def _latest_fedora() -> str:
    data = requests.get("https://getfedora.org/releases.json", timeout=15).json()
    candidates = [
        r for r in data
        if r.get("variant") == "Workstation" and r.get("arch") == "x86_64"
        and str(r.get("link", "")).endswith(".iso")
    ]
    if not candidates:
        raise RuntimeError("No se encontraron ISOs de Fedora Workstation x86_64.")
    latest = max(candidates, key=lambda r: version.parse(str(r["version"])))
    return latest["link"]


def _latest_arch() -> str:
    today = date.today()
    for ym in (today.strftime("%Y.%m"), (today.replace(day=1) - timedelta(days=1)).strftime("%Y.%m")):
        url = f"https://geo.mirror.pkgbuild.com/iso/{ym}/"
        try:
            html = requests.get(url, timeout=15).text
        except requests.RequestException:
            continue
        m = re.search(r'archlinux-[\d.]+-x86_64\.iso', html)
        if m:
            return url + m.group(0)
    raise RuntimeError("No se encontró ISO de Arch Linux en el mirror.")


def _latest_mint() -> str:
    base = "https://mirrors.edge.kernel.org/linuxmint/stable/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+(?:\.\d+)?)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Linux Mint.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = requests.get(base + latest + "/", timeout=15).text
    m = re.search(r'linuxmint-[\d.]+-cinnamon-64bit\.iso', idx)
    if not m:
        m = re.search(r'linuxmint-[\d.]+-xfce-64bit\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Linux Mint {latest}.")
    return base + latest + "/" + m.group(0)


def _latest_manjaro() -> str:
    r = requests.head(
        "https://sourceforge.net/projects/manjarolinux/files/xfce/latest/download",
        timeout=15, allow_redirects=True,
    )
    if not r.url.lower().endswith(".iso"):
        raise RuntimeError("No se pudo resolver la última ISO de Manjaro.")
    return r.url


def _latest_opensuse() -> str:
    base = "https://download.opensuse.org/distribution/leap/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de openSUSE Leap.")
    latest = max(versions, key=lambda v: version.parse(v))
    iso_dir = f"{base}{latest}/iso/"
    idx = requests.get(iso_dir, timeout=15).text
    m = re.search(rf'openSUSE-Leap-{re.escape(latest)}-DVD-x86_64-Media\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para openSUSE Leap {latest}.")
    return iso_dir + m.group(0)


def _latest_popos() -> str:
    base = "https://iso.pop-os.org/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Pop!_OS.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = requests.get(base + latest + "/amd64/intel/", timeout=15).text
    m = re.search(r'pop-os_[\d.]+_amd64_intel_\d+\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Pop!_OS {latest}.")
    return base + latest + "/amd64/intel/" + m.group(0)


def _latest_almalinux() -> str:
    base = "https://repo.almalinux.org/almalinux/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de AlmaLinux.")
    latest = max(versions, key=lambda v: int(v))
    iso_dir = f"{base}{latest}/isos/x86_64/"
    idx = requests.get(iso_dir, timeout=15).text
    m = re.search(r'AlmaLinux-[\d.]+-x86_64-dvd\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para AlmaLinux {latest}.")
    return iso_dir + m.group(0)


def _latest_rocky() -> str:
    base = "https://download.rockylinux.org/pub/rocky/"
    html = requests.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Rocky Linux.")
    latest = max(versions, key=lambda v: int(v))
    iso_dir = f"{base}{latest}/isos/x86_64/"
    idx = requests.get(iso_dir, timeout=15).text
    m = re.search(r'Rocky-[\d.]+-x86_64-dvd\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Rocky Linux {latest}.")
    return iso_dir + m.group(0)


def _patch_fido_for_linux(fido_path: str) -> None:
    """Fido se niega a correr fuera de Windows por diseño (ver
    https://github.com/pbatard/Fido/issues/60): Get-Platform-Version
    devuelve 0.0 en PowerShell para Linux/Mac, y el script aborta con
    'This feature is not available on this platform.'. Es solo un check
    de conveniencia del autor -- las URLs que entrega son igual las
    oficiales de Microsoft --, así que lo neutralizamos forzando el
    valor que devolvería en Windows 10/11."""
    with open(fido_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    marker = "# --- patched-for-linux ---"
    if marker in content:
        return
    patched = content.replace(
        "$winver = Get-Platform-Version",
        f"$winver = 10.0 {marker}",
        1,
    )
    if patched == content:
        raise RuntimeError(
            "No se encontró la línea esperada en Fido.ps1 para aplicar el parche "
            "(es posible que el script haya cambiado de estructura; revisar manualmente)."
        )
    with open(fido_path, "w", encoding="utf-8") as f:
        f.write(patched)


def get_latest_windows_iso_url(win_ver: str, fido_path: str = "Fido.ps1") -> str:
    """Invoca el script Fido (pbatard/Fido, MIT) vía PowerShell para obtener
    el enlace directo oficial de Microsoft a la última ISO retail.
    Requiere: pwsh instalado y Fido.ps1 descargado (ver comentario abajo)."""
    win_num = "11" if "11" in win_ver else "10"

    if not os.path.isfile(fido_path):
        # Descarga la versión más reciente del script oficial si no existe localmente
        r = requests.get(
            "https://raw.githubusercontent.com/pbatard/Fido/master/Fido.ps1",
            timeout=20,
        )
        r.raise_for_status()
        with open(fido_path, "wb") as f:
            f.write(r.content)

    _patch_fido_for_linux(fido_path)

    cmd = [
        "pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", fido_path,
        "-Win", win_num, "-Rel", "Latest", "-Ed", "Pro", "-Lang", "Int", "-Arch", "x64",
        "-PlatformArch", "x64",  # evita la llamada a Get-CimInstance (WMI), inexistente en pwsh Linux
        "-GetUrl",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Fido falló: {result.stderr.strip() or result.stdout.strip()}")

    # -GetUrl imprime solo la URL; si tu versión de Fido no soporta el flag,
    # cae aquí y se toma la última línea no vacía de la salida como respaldo.
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    url_lines = [l for l in lines if l.startswith("http")]
    if not url_lines:
        raise RuntimeError(f"No se pudo extraer la URL de la salida de Fido:\n{result.stdout}")
    return url_lines[-1]


