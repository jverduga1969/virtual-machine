#!/usr/bin/env python3
"""Parche macos_pcap_debug_v1 para workers.py.

Añade, en el bloque de red de macOS, una captura de tráfico opcional:
si se lanza la app con MACOS_PCAP_DEBUG=1, QEMU escribe /tmp/vm-net.pcap.
Sin la variable de entorno no cambia nada.

Uso:
    python3 patch_pcap_debug.py /ruta/a/workers.py
"""
import py_compile
import re
import shutil
import sys

MARKER = "macos_pcap_debug_v1"

PATTERN = re.compile(
    r'(?P<indent>[ \t]+)network_args = \(\n'
    r'(?P=indent)    f"-netdev user,id=net0,dns=10\.0\.2\.3 "\n'
    r'(?P=indent)    f"-device \{_mac_nic\},netdev=net0,id=net0,mac=\{_mac_mac\}"\n'
    r'(?P=indent)\)\n'
)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        src = fh.read()

    if MARKER in src:
        print(f"Ya aplicado ({MARKER}). No se cambia nada.")
        return 0

    matches = list(PATTERN.finditer(src))
    if len(matches) != 1:
        print(f"ERROR: se esperaba 1 coincidencia del bloque de red macOS y hay {len(matches)}.")
        print("No se modificó el archivo.")
        return 2

    m = matches[0]
    ind = m.group("indent")
    extra = (
        f"{ind}# {MARKER}: con MACOS_PCAP_DEBUG=1 se guarda el trafico de la VM\n"
        f"{ind}# en /tmp/vm-net.pcap (diagnostico de red; desactivado por defecto).\n"
        f"{ind}import os as _os_pcap\n"
        f'{ind}if _os_pcap.environ.get("MACOS_PCAP_DEBUG") == "1":\n'
        f"{ind}    network_args += (\n"
        f'{ind}        " -object filter-dump,id=fdump0,netdev=net0,"\n'
        f'{ind}        "file=/tmp/vm-net.pcap"\n'
        f"{ind}    )\n"
    )
    new_src = src[: m.end()] + extra + src[m.end():]

    shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_src)

    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as err:
        shutil.copy2(path + ".bak", path)
        print(f"ERROR de sintaxis tras el parche, se restauró el original:\n{err}")
        return 3

    print(f"OK: parche aplicado. Copia de seguridad en {path}.bak")
    return 0


if __name__ == "__main__":
    sys.exit(main())
