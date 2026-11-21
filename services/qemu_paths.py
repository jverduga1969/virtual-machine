"""Resolución de ejecutables de QEMU en Linux y Windows.

La app construye los comandos de QEMU a mano. En Windows, QEMU suele
instalarse sin añadir su directorio al PATH (winget, MSI o descompresión
manual), por lo que llamar a ``subprocess.run(["qemu-img", ...])`` falla con
``WinError 2``. Todas las llamadas deben usar :func:`qemu_cmd`.
"""

import os
import platform
import shutil
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

# Permite fijar la ruta desde tests o desde la configuración de la app.
_dir_override = None


def set_qemu_dir(path):
    """Fija (o limpia) el directorio de QEMU preferido por el usuario."""
    global _dir_override
    _dir_override = str(path) if path else None


def _nombres(name):
    nombres = [name]
    if IS_WINDOWS and not name.lower().endswith(".exe"):
        nombres.append(name + ".exe")
    return nombres


def _existe(ruta):
    try:
        return ruta.is_file()
    except OSError:
        return False


def find_qemu_binary(name):
    """Devuelve la ruta absoluta del ejecutable o ``None`` si no existe."""
    nombres = _nombres(name)

    # 1) PATH (lo habitual en Linux y en instalaciones de Windows bien hechas).
    for candidato in nombres:
        encontrado = shutil.which(candidato)
        if encontrado:
            return encontrado

    if not IS_WINDOWS:
        return None

    # 2) Directorio configurado explícitamente (QEMU_DIR o AppContext).
    directorios = []
    for valor in (_dir_override, os.environ.get("QEMU_DIR", "")):
        if valor and Path(valor) not in directorios:
            directorios.append(Path(valor))

    # 3) Instalaciones típicas en Windows.
    raices = (
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("USERPROFILE", ""),
        r"C:\QEMU",
    )
    subcarpetas = ("qemu", "QEMU", "qemu-64-bit", "Programs\\qemu",
                   "Programs\\QEMU", "scoop\\shims", "msys64\\mingw64\\bin")
    for raiz in raices:
        if not raiz:
            continue
        for sub in subcarpetas:
            directorios.append(Path(raiz) / sub)

    programdata = os.environ.get("ProgramData", "")
    if programdata:
        directorios.append(Path(programdata) / "chocolatey" / "bin")

    for directorio in directorios:
        for candidato in nombres:
            ruta = directorio / candidato
            if _existe(ruta):
                return str(ruta)

    # 4) winget instala QEMU bajo LOCALAPPDATA\ Microsoft\WinGet\Packages.
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        base = Path(localappdata) / "Microsoft" / "WinGet" / "Packages"
        try:
            paquetes = sorted(base.glob("SoftwareFreedomConservancy.QEMU_*"))
        except OSError:
            paquetes = []
        for paquete in paquetes:
            for candidato in nombres:
                try:
                    rutas = sorted(paquete.rglob(candidato))
                except OSError:
                    continue
                for ruta in rutas:
                    if _existe(ruta):
                        return str(ruta)

    return None


def qemu_cmd(name, *args):
    """Construye una lista para subprocess con el ejecutable resuelto."""
    ejecutable = find_qemu_binary(name) or name
    return [ejecutable, *[str(arg) for arg in args]]
