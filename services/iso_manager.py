import os
import logging
import requests
import re
from pathlib import Path

from services.download_utils import HashTracker

try:
    from PyQt6.QtCore import QSettings
    _HAS_QSETTINGS = True
except ImportError:
    QSettings = None
    _HAS_QSETTINGS = False

log = logging.getLogger(__name__)

class ISOManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        saved = ""
        if _HAS_QSETTINGS:
            try:
                saved = QSettings().value("paths/isos_dir", "")
            except Exception:
                saved = ""
        self.iso_dir = Path(saved) if saved else self.data_dir / "isos"
        self.iso_dir.mkdir(parents=True, exist_ok=True)

    def get_download_url(self, platform: str, os_name: str, version: str) -> str:
        try:
            if platform == "GNU / Linux":
                return self._get_linux_url(os_name, version)
            elif platform == "Microsoft Windows":
                return self._get_windows_url(version)
            elif platform == "macOS":
                return self._get_macos_url(version)
            else:
                raise ValueError(f"Descarga no soportada para: {platform}")
        except Exception as e:
            log.error(f"Error obteniendo URL para {platform} {os_name} {version}: {e}")
            raise

    def _get_linux_url(self, os_name: str, version: str) -> str:
        if os_name == "Ubuntu":
            return "https://releases.ubuntu.com/24.04/ubuntu-24.04.1-desktop-amd64.iso"
        elif os_name == "Linux Mint":
            return "https://mirrors.edge.kernel.org/linuxmint/stable/22/linuxmint-22-cinnamon-64bit.iso"
        raise ValueError(f"ISO no encontrada para {os_name} {version}")

    def _get_windows_url(self, version: str) -> str:
        return "https://software.download.prss.microsoft.com/dbazure/Win11_24H2_Spanish_x64.iso"

    def _get_macos_url(self, version: str) -> str:
        return "macos_recovery_script"

    def start_download(self, url: str, filename: str, progress_callback=None,
                       expected_sha256: str = None) -> Path:
        target_path = self.iso_dir / filename
        
        # NUEVO: Si el archivo existe pero es basura (HTML), lo borramos antes de descargar
        if target_path.exists() and target_path.stat().st_size < 5000000:
            log.warning(f"El archivo {target_path} es demasiado pequeño. Borrando HTML corrupto...")
            target_path.unlink()

        log.info(f"Iniciando descarga de {url} en {target_path}...")
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        real_url = url
        try:
            r = session.get(url, stream=True, allow_redirects=True, timeout=15)
            content_type = r.headers.get("Content-Type", "")
            
            if "text/html" in content_type:
                log.warning("Detectada página HTML de SourceForge. Extrayendo enlace real...")
                html = r.text
                match = re.search(r'url=(https?://[^"\']+)', html)
                if not match:
                    match = re.search(r'(https://downloads\.sourceforge\.net/[^"\']+)', html)
                
                if match:
                    real_url = match.group(1)
                    log.info(f"Enlace real extraído: {real_url}")
                else:
                    raise RuntimeError("No se pudo extraer el enlace de descarga real del HTML de SourceForge.")
            else:
                real_url = r.url
        except requests.RequestException as e:
            log.warning(f"Error en petición inicial: {e}. Intentando descarga directa.")

        try:
            with session.get(real_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                if total_size > 0 and total_size < 5000000:
                    raise RuntimeError(f"El archivo es demasiado pequeño ({total_size} bytes). Probablemente sea un HTML de error.")

                temp_path = target_path.with_suffix(".part")
                downloaded = 0
                tracker = HashTracker("sha256", expected_sha256)
                
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                            tracker.update(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size:
                                progress_callback(downloaded, total_size)
                
                if downloaded < 5000000:
                    temp_path.unlink()
                    raise RuntimeError(f"La descarga falló o es un archivo inválido. Tamaño: {downloaded} bytes.")
                
                # Si la fuente anunció un hash, un fallback a HTML/otra ISO
                # se detecta aquí antes de sustituir el archivo bueno.
                digest = tracker.verify()
                temp_path.replace(target_path)
                log.info(f"Descarga completada: {target_path} (sha256={digest})")
                return target_path
                
        except Exception as e:
            log.error(f"Error descargando {real_url}: {e}")
            if target_path.with_suffix(".part").exists():
                target_path.with_suffix(".part").unlink()
            raise