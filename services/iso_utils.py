import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)

# Intentar importar tus archivos originales desde la carpeta services
try:
    from services import iso_versions
    HAS_ISO_VERSIONS = True
except ImportError:
    HAS_ISO_VERSIONS = False
    log.warning("No se encontró services/iso_versions.py. Usando versiones simuladas.")

def get_linux_versions(distro_name: str) -> list[str]:
    """Devuelve una lista de strings con las versiones disponibles."""
    if not HAS_ISO_VERSIONS:
        # Fallback simulado si no están los archivos
        if distro_name == "Ubuntu": return ["24.04 LTS", "22.04 LTS", "20.04 LTS"]
        if distro_name == "Linux Mint": return ["22.3", "22.1", "21.3"]
        return ["Más reciente (automático)"]

    try:
        # Llamada real a tu motor de versiones
        versions = iso_versions.list_distro_versions(distro_name)
        if not versions:
            return ["Más reciente (automático)"]
        
        # Devolver los IDs (ej. "24.04")
        return [v["id"] for v in versions]
    except Exception as e:
        log.error(f"Error obteniendo versiones para {distro_name}: {e}")
        return ["Error al conectar con el espejo"]
