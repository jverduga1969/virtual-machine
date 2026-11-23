"""Validaciones estáticas del repositorio, usadas por CI y por desarrolladores.

Comprueba las invariantes que la suite de tests no cubre directamente:
scripts de Windows en ASCII/LF, catálogos i18n sincronizados, instalador y spec
con referencias completas, y versión de la Ayuda alineada con el instalador.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ERRORES: list[str] = []


def error(mensaje: str) -> None:
    ERRORES.append(mensaje)


def verificar_scripts() -> None:
    """Los .ps1 deben ser ASCII estricto y usar LF, igual que el resto del repo."""
    atributos = ROOT / ".gitattributes"
    if not atributos.exists() or "eol=lf" not in atributos.read_text(encoding="utf-8"):
        error("Falta .gitattributes con eol=lf (Git for Windows convertiria a CRLF)")
    for nombre in ("scripts/postinstall.ps1", "scripts/uninstall.ps1"):
        ruta = ROOT / nombre
        if not ruta.exists():
            error(f"Falta {nombre}")
            continue
        datos = ruta.read_bytes()
        no_ascii = sorted({b for b in datos if b > 127})
        if no_ascii:
            error(f"{nombre} contiene bytes no ASCII: {no_ascii}")
        if b"\r\n" in datos:
            error(f"{nombre} debe usar LF, no CRLF")


def verificar_i18n() -> None:
    """Los cinco catálogos traducidos deben tener exactamente las mismas claves."""
    codigos = ("en", "de", "fr", "it", "pt_BR")
    catalogos = {}
    for codigo in codigos:
        ruta = ROOT / "i18n" / f"{codigo}.json"
        catalogos[codigo] = json.loads(ruta.read_text(encoding="utf-8"))
    bases = set(catalogos["en"])
    for codigo in codigos:
        claves = set(catalogos[codigo])
        if claves != bases:
            faltan = sorted(bases - claves)[:5]
            sobran = sorted(claves - bases)[:5]
            error(f"i18n/{codigo}.json dispare: faltan {faltan}, sobran {sobran}")
    es = json.loads((ROOT / "i18n" / "es.json").read_text(encoding="utf-8"))
    if es:
        error("i18n/es.json debe quedar vacío (español = identidad)")


def verificar_instalador() -> None:
    iss = (ROOT / "installer.iss").read_text(encoding="utf-8")
    for nombre in ("postinstall.ps1", "uninstall.ps1", "Fido.ps1"):
        if nombre not in iss:
            error(f"installer.iss no incluye {nombre}")
    for nombre in ("postinstall.ps1", "uninstall.ps1"):
        if not (ROOT / "scripts" / nombre).exists():
            error(f"Falta scripts/{nombre} referenciado por installer.iss")
    if "[UninstallRun]" not in iss:
        error("installer.iss no tiene [UninstallRun]")

    m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', iss)
    if not m:
        error("No se encontró MyAppVersion en installer.iss")
        return
    version = m.group(1)
    ayuda = (ROOT / "plugins" / "help" / "plugin.py").read_text(encoding="utf-8")
    m2 = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', ayuda)
    version_ayuda = m2.group(1) if m2 else "?"
    if version_ayuda != version:
        error(f"APP_VERSION de Ayuda ({version_ayuda}) != MyAppVersion ({version})")


def verificar_spec() -> None:
    spec = (ROOT / "virtualmachine.spec").read_text(encoding="utf-8")
    for modulo in ("services.rest_api", "services.host_diagnostics", "psutil"):
        if modulo not in spec:
            error(f"virtualmachine.spec no incluye {modulo}")


def main() -> int:
    ERRORES.clear()
    verificar_scripts()
    verificar_i18n()
    verificar_instalador()
    verificar_spec()
    if ERRORES:
        for mensaje in ERRORES:
            print(f"ERROR: {mensaje}", file=sys.stderr)
        return 1
    print("Verificación del repositorio OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
