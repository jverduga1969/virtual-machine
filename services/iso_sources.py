# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""
Detección de la última ISO disponible para cada distro/versión soportada.
Incluye fallbacks para Windows usando Fido, la API de Microsoft y msdl.
"""
import os
import re
import sys
import platform
import subprocess
import logging
import shutil
import locale
import tempfile
from pathlib import Path
from datetime import date, timedelta
from urllib.parse import urlparse, unquote

import requests
from packaging import version

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
})

SUPPORTED_AUTODETECT = {
    "Ubuntu", "Debian", "Fedora", "Arch Linux", "Linux Mint",
    "Manjaro Linux", "openSUSE", "Pop!_OS", "AlmaLinux", "Rocky Linux",
    "Kubuntu", "Xubuntu", "Lubuntu", "EndeavourOS", "Kali Linux",
    "Garuda Linux", "elementary OS",
    "Bliss OS", "Android-x86",
}

def supports_auto_download(distro: str) -> bool:
    return distro in SUPPORTED_AUTODETECT

def get_latest_iso_url(distro: str) -> str:
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
        "Kubuntu": _latest_kubuntu,
        "Xubuntu": _latest_xubuntu,
        "Lubuntu": _latest_lubuntu,
        "Kali Linux": _latest_kali,
        "Garuda Linux": _latest_garuda,
        "EndeavourOS": _latest_endeavouros,
        "elementary OS": _latest_elementary,
        "Bliss OS": _latest_bliss_os,
        "Android-x86": _latest_android_x86,
    }
    fn = handlers.get(distro)
    if fn is None:
        raise ValueError(f"Auto-detección no soportada para: {distro}")
    return fn()

# =========================================================
# LINUX: Funciones de descarga
# =========================================================

def _latest_ubuntu() -> str:
    base = "https://releases.ubuntu.com/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Ubuntu.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = _session.get(base + latest + "/", timeout=15).text
    m = re.search(rf'ubuntu-{re.escape(latest)}[\d.]*-desktop-amd64\.iso', idx)
    if not m:
        m = re.search(rf'ubuntu-{re.escape(latest)}[\d.]*-live-server-amd64\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO de escritorio para Ubuntu {latest}.")
    return base + latest + "/" + m.group(0)

def _latest_debian() -> str:
    base = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    html = _session.get(base, timeout=15).text
    m = re.search(r'debian-([\d.]+)-amd64-netinst\.iso', html)
    if not m:
        raise RuntimeError("No se encontró ISO de Debian en el índice actual.")
    return base + m.group(0)

def _latest_fedora() -> str:
    # 1. Intentar JSON API
    try:
        r = _session.get("https://fedoraproject.org/releases.json", timeout=15)
        r.raise_for_status()
        data = r.json()
        candidates = [
            item for item in data
            if item.get("variant") == "Workstation" and item.get("arch") == "x86_64"
            and str(item.get("link", "")).endswith(".iso")
        ]
        if not candidates:
            raise ValueError("No Fedora Workstation ISOs found in JSON")
        
        def vkey(x):
            v = str(x.get("version", ""))
            m = re.search(r'(\d+)', v)
            return int(m.group(1)) if m else 0
            
        latest = max(candidates, key=vkey)
        return latest["link"]
    except Exception as e:
        log.warning(f"Fedora JSON API failed: {e}. Falling back to HTML parsing.")
        
    # 2. Fallback: Parsear HTML
    try:
        base = "https://download.fedoraproject.org/pub/fedora/linux/releases/"
        html = _session.get(base, timeout=15).text
        versions = re.findall(r'href="(\d+)/"', html)
        if not versions:
            raise RuntimeError("No se encontraron versiones de Fedora.")
        latest = max(versions, key=lambda v: int(v))
        
        iso_dir = f"{base}{latest}/Workstation/x86_64/iso/"
        idx = _session.get(iso_dir, timeout=15).text
        m = re.search(r'Fedora-Workstation-Live-x86_64-[\d.]+\.iso', idx)
        if not m:
            raise RuntimeError(f"No se encontró ISO para Fedora {latest}.")
        return iso_dir + m.group(0)
    except Exception as e2:
        raise RuntimeError(f"No se pudo obtener la ISO de Fedora. Revisa manualmente. Error: {e2}")

def _latest_arch() -> str:
    today = date.today()
    for ym in (today.strftime("%Y.%m"), (today.replace(day=1) - timedelta(days=1)).strftime("%Y.%m")):
        url = f"https://geo.mirror.pkgbuild.com/iso/{ym}/"
        try:
            html = _session.get(url, timeout=15).text
        except requests.RequestException:
            continue
        m = re.search(r'archlinux-[\d.]+-x86_64\.iso', html)
        if m:
            return url + m.group(0)
    raise RuntimeError("No se encontró ISO de Arch Linux en el mirror.")

def _latest_mint() -> str:
    base = "https://mirrors.edge.kernel.org/linuxmint/stable/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+(?:\.\d+)?)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Linux Mint.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = _session.get(base + latest + "/", timeout=15).text
    m = re.search(r'linuxmint-[\d.]+-cinnamon-64bit\.iso', idx)
    if not m:
        m = re.search(r'linuxmint-[\d.]+-xfce-64bit\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Linux Mint {latest}.")
    return base + latest + "/" + m.group(0)

def _latest_manjaro() -> str:
    r = _session.get(
        "https://sourceforge.net/projects/manjarolinux/files/xfce/latest/download",
        timeout=15, allow_redirects=True, stream=True
    )
    r.close()
    if not r.url.lower().endswith(".iso"):
        raise RuntimeError("No se pudo resolver la última ISO de Manjaro.")
    return r.url

def _latest_opensuse() -> str:
    base = "https://download.opensuse.org/distribution/leap/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de openSUSE Leap.")
    latest = max(versions, key=lambda v: version.parse(v))
    iso_dir = f"{base}{latest}/iso/"
    idx = _session.get(iso_dir, timeout=15).text
    m = re.search(rf'openSUSE-Leap-{re.escape(latest)}-DVD-x86_64-Media\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para openSUSE Leap {latest}.")
    return iso_dir + m.group(0)

def _latest_popos() -> str:
    base = "https://iso.pop-os.org/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Pop!_OS.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = _session.get(base + latest + "/amd64/intel/", timeout=15).text
    m = re.search(r'pop-os_[\d.]+_amd64_intel_\d+\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Pop!_OS {latest}.")
    return base + latest + "/amd64/intel/" + m.group(0)

def _latest_almalinux() -> str:
    base = "https://repo.almalinux.org/almalinux/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de AlmaLinux.")
    latest = max(versions, key=lambda v: int(v))
    iso_dir = f"{base}{latest}/isos/x86_64/"
    idx = _session.get(iso_dir, timeout=15).text
    m = re.search(r'AlmaLinux-[\d.]+-x86_64-dvd\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para AlmaLinux {latest}.")
    return iso_dir + m.group(0)

def _latest_rocky() -> str:
    base = "https://download.rockylinux.org/pub/rocky/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+)/"', html)
    if not versions:
        raise RuntimeError("No se encontraron versiones de Rocky Linux.")
    latest = max(versions, key=lambda v: int(v))
    iso_dir = f"{base}{latest}/isos/x86_64/"
    idx = _session.get(iso_dir, timeout=15).text
    m = re.search(r'Rocky-[\d.]+-x86_64-dvd\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para Rocky Linux {latest}.")
    return iso_dir + m.group(0)

def _latest_flavor(flavor: str) -> str:
    base = f"https://cdimage.ubuntu.com/{flavor}/releases/"
    html = _session.get(base, timeout=15).text
    versions = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/"', html)
    if not versions:
        raise RuntimeError(f"No se encontraron versiones de {flavor}.")
    latest = max(versions, key=lambda v: version.parse(v))
    idx = _session.get(base + latest + "/release/", timeout=15).text
    m = re.search(rf'{flavor.lower()}-{re.escape(latest)}[\d.]*-desktop-amd64\.iso', idx)
    if not m:
        raise RuntimeError(f"No se encontró ISO para {flavor} {latest}.")
    return base + latest + "/release/" + m.group(0)

def _latest_kubuntu() -> str: return _latest_flavor("kubuntu")
def _latest_xubuntu() -> str: return _latest_flavor("xubuntu")
def _latest_lubuntu() -> str: return _latest_flavor("lubuntu")

def _latest_kali() -> str:
    base = "https://cdimage.kali.org/current/"
    html = _session.get(base, timeout=15).text
    m = re.search(r'kali-linux-[\d.]+-installer-amd64\.iso', html)
    if not m:
        m = re.search(r'kali-linux-[\d.]+-live-amd64\.iso', html)
    if not m:
        raise RuntimeError("No se encontró ISO de Kali Linux.")
    return base + m.group(0)

def _latest_garuda() -> str:
    base = "https://iso.builds.garudalinux.org/iso/garuda/"
    html = _session.get(base, timeout=15).text
    dirs = re.findall(r'href="([^"]+/)"', html)
    for d in sorted(dirs, reverse=True):
        if d.startswith('..') or d.startswith('?') or d.startswith('/'): continue
        sub_url = base + d
        sub_html = _session.get(sub_url, timeout=15).text
        isos = re.findall(r'href="([^"]+\.iso)"', sub_html)
        if isos:
            return sub_url + isos[0]
    raise RuntimeError("No se encontró ISO de Garuda Linux.")

def _latest_endeavouros() -> str:
    url = "https://api.github.com/repos/endeavouros-team/ISO/releases/latest"
    r = _session.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    for asset in data.get("assets", []):
        if asset["name"].endswith(".iso"):
            return asset["browser_download_url"]
    raise RuntimeError("No se encontró la ISO en las releases de EndeavourOS.")

def _latest_elementary() -> str:
    url = "https://api.github.com/repos/elementary/os/releases/latest"
    r = _session.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    for asset in data.get("assets", []):
        if asset["name"].endswith(".iso"):
            return asset["browser_download_url"]
    raise RuntimeError("No se encontró ISO en las releases de elementary OS.")

# =========================================================
# ANDROID: Bliss OS y Android-x86
# =========================================================

def _latest_bliss_os() -> str:
    return "https://downloads.sourceforge.net/project/blissos-x86/Official/BlissOS16/Gapps/Generic/Bliss-v16.9.6-x86_64-OFFICIAL-gapps-20240220.iso"

def _latest_android_x86() -> str:
    return "https://downloads.sourceforge.net/project/android-x86/Release%209.0/android-x86_64-9.0-r2.iso"

# =========================================================
# WINDOWS: Fido + API + msdl
# =========================================================

def _patch_fido_for_linux(fido_path: str) -> str:
    """Devuelve un Fido ejecutable desde Linux/macOS, sin tocar el original.

    El parche fuerza `$winver = 10.0` porque Fido no detecta la versión de
    Windows cuando corre bajo pwsh en otro sistema. La copia canónica ya lo
    lleva aplicado; si no es así, se escribe en el temporal porque la ruta
    instalada puede ser de solo lectura.
    """
    ruta = Path(fido_path)
    contenido = ruta.read_text(encoding="utf-8-sig")
    marcador = "# --- patched-for-linux ---"
    if marcador in contenido:
        return str(ruta)

    original = "$winver = Get-Platform-Version"
    if original in contenido:
        contenido = contenido.replace(original, f"$winver = 10.0 {marcador}", 1)
    else:
        log.warning("No se encontró la línea de versión en Fido.ps1; se usa tal cual.")

    destino = Path(tempfile.gettempdir()) / "Fido-patched.ps1"
    if destino.resolve() != ruta.resolve() or not destino.is_file():
        destino.write_text(contenido, encoding="utf-8")
    return str(destino)

def get_host_language() -> str:
    try:
        loc = locale.getdefaultlocale()[0] or os.environ.get('LANG', 'en_US.UTF-8')
        code = loc.split('.')[0].split('_')[0].lower()
        mapping = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'zh': 'Chinese (Simplified)', 'ko': 'Korean', 'nl': 'Dutch',
            'pl': 'Polish', 'tr': 'Turkish', 'sv': 'Swedish', 'cs': 'Czech',
            'da': 'Danish', 'fi': 'Finnish', 'nb': 'Norwegian',
        }
        if code == 'pt' and 'br' in loc.lower():
            return 'Portuguese (Brazil)'
        return mapping.get(code, 'English')
    except Exception:
        return 'English'

def get_windows_url_via_api(win_ver: str, lang_name: str) -> str:
    import uuid
    lang_map = {
        "Spanish": "Spanish", "English": "English (United States)",
        "French": "French", "German": "German", "Italian": "Italian",
        "Portuguese": "Portuguese (Brazil)", "Russian": "Russian"
    }
    ms_lang = lang_map.get(lang_name, "English (United States)")

    product_edition_id = 2618
    sku = "Pro"
    friendly_name = f"Win{win_ver.split()[-1]}_{ms_lang.replace(' ', '_')}_x64.iso"

    session_id = str(uuid.uuid4())
    try:
        _session.get(f"https://vlscppe.microsoft.com/tags?org_id=y6jn8c31&session_id={session_id}", timeout=10)
    except:
        pass

    api_url = (
        f"https://www.microsoft.com/en-us/api/Controls/ContentManagement/Content/GetProductDownloadLinksBySku"
        f"?profile=606624d4-9b1a-4e2b-8b52-24fb80c4402d"
        f"&productEditionId={product_edition_id}&SKU={sku}"
        f"&friendlyFileName={friendly_name}&Lang={ms_lang}&sessionId={session_id}"
    )
    r = _session.get(api_url, timeout=15)
    r.raise_for_status()
    data = r.json()
    try:
        options = data["ProductDownloadOptions"]
        return options[0]["DownloadLink"]
    except (KeyError, IndexError):
        raise RuntimeError("La API de Microsoft no devolvió un enlace válido.")

def get_windows_url_via_msdl(win_ver: str, lang_name: str) -> str:
    if not shutil.which("msdl"):
        instalacion = ("winget install --id starkSV.msdl" if IS_WINDOWS
                       else "yay -S msdl-bin")
        raise RuntimeError(
            "La herramienta 'msdl' no está instalada.\n"
            f"Instálala con: {instalacion}\n"
            "O descarga el binario desde https://github.com/starkSV/windows-iso-downloader/releases"
        )

    lang_map = {
        "Spanish": "Spanish", "English": "English", "French": "French",
        "German": "German", "Italian": "Italian", "Portuguese": "Portuguese (Brazil)",
        "Russian": "Russian"
    }
    ms_lang = lang_map.get(lang_name, "English")

    product_id = "3813" if "11" in win_ver else "2618"
    cmd = ["msdl", "-id", product_id, "--lang", ms_lang]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        url = result.stdout.strip()
        if not url.startswith("http"):
            raise RuntimeError(f"Salida inesperada de msdl: {url}")
        return url
    except FileNotFoundError:
        raise RuntimeError("msdl no encontrado en el PATH.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("msdl tardó más de 60 segundos en responder.")

def _resolve_fido_path(fido_path: str = "Fido.ps1", download: bool = True) -> str:
    """Localiza Fido.ps1 también cuando la app se ejecuta empaquetada.

    ``download=False`` lo usa el diagnóstico: nunca debe provocar una
    descarga de red solo por comprobar el estado del host.
    """
    base = Path(__file__).resolve().parent
    # Una sola fuente canónica (v1.71); 'services/Fido.ps1' (v1.70, con otro
    # catálogo) ya no existe. En desarrollo se respeta una ruta explícita, pero
    # en el exe gana siempre la copia empaquetada.
    candidatos = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(getattr(sys, "_MEIPASS", base)) / "Fido.ps1")
    if fido_path != "Fido.ps1" or Path(fido_path).is_absolute():
        candidatos.append(Path(fido_path))
    candidatos += [base.parent / "Fido.ps1", Path(fido_path)]
    for candidato in candidatos:
        if candidato.is_file():
            return str(candidato)

    if not download:
        return ""

    # El directorio de trabajo suele ser de solo lectura (Program Files), así
    # que en Windows descargamos siempre al temporal del usuario.
    destino = (Path(tempfile.gettempdir()) / "Fido.ps1" if IS_WINDOWS
               else Path(fido_path))
    try:
        r = _session.get("https://raw.githubusercontent.com/pbatard/Fido/master/Fido.ps1",
                         timeout=20)
        r.raise_for_status()
        destino.write_bytes(r.content)
    except Exception as e:
        log.warning(f"No se pudo descargar Fido: {e}")
    return str(destino)


def _powershell_candidates() -> list[str]:
    # Windows 10/11 incluyen powershell.exe 5.1, pero no pwsh (PowerShell 7).
    return (["powershell.exe", "powershell", "pwsh"] if IS_WINDOWS
            else ["pwsh", "powershell"])


def get_latest_windows_iso_url(win_ver: str, fido_path: str = "Fido.ps1") -> str:
    win_num = "11" if "11" in win_ver else "10"

    fido_path = _resolve_fido_path(fido_path)
    # El parche fuerza Windows 10 porque Fido no detecta bien la versión bajo
    # pwsh en Linux. En Windows se ejecuta tal cual.
    if not IS_WINDOWS:
        fido_path = _patch_fido_for_linux(fido_path)
    lang = get_host_language()

    def _run_fido(lang_arg):
        argumentos = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", fido_path,
                      "-Win", win_num, "-Rel", "Latest", "-Ed", "Pro", "-Arch", "x64",
                      "-PlatformArch", "x64"]
        if lang_arg:
            argumentos.extend(["-Lang", lang_arg])
        argumentos.append("-GetUrl")
        ultimo_error = "PowerShell no está instalado."
        for shell in _powershell_candidates():
            try:
                result = subprocess.run([shell] + argumentos,
                                        capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    ultimo_error = result.stderr.strip() or result.stdout.strip()
                    continue
                lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                url_lines = [l for l in lines if l.startswith("http")]
                if not url_lines:
                    ultimo_error = f"No se pudo extraer la URL: {result.stdout}"
                    continue
                return True, url_lines[-1]
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                ultimo_error = "Fido tardó más de 60 segundos."
            except Exception as e:
                ultimo_error = str(e)
        return False, ultimo_error

    if lang != "English":
        success, result = _run_fido(lang)
        if success: return result
        log.warning(f"Fido falló con '{lang}', reintentando en inglés...")
    success, result = _run_fido("English")
    if success: return result
    success, result = _run_fido(None)
    if success: return result

    api_err = "No intentado"
    log.warning("Fido falló. Intentando con la API directa de Microsoft...")
    try:
        return get_windows_url_via_api(win_ver, lang)
    except Exception as e:
        api_err = str(e)
        log.warning(f"API de Microsoft falló: {api_err}")

    msdl_err = "No intentado"
    log.warning("API falló. Intentando con msdl...")
    try:
        return get_windows_url_via_msdl(win_ver, lang)
    except Exception as e:
        msdl_err = str(e)

    raise RuntimeError(
        f"No se pudo obtener la ISO de Windows automáticamente.\n\n"
        f"• Fido falló: {result}\n"
        f"• API de Microsoft falló: {api_err}\n"
        f"• msdl falló: {msdl_err}\n\n"
        f"Descarga la ISO manualmente desde https://www.microsoft.com/software-download/windows11 "
        f"y usa la opción 'Seleccionar un archivo ISO'."
    )