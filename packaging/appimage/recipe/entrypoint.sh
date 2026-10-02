#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"

if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo "[ERROR] qemu-system-x86_64 no encontrado en PATH." >&2
    echo "Instalalo con el gestor de paquetes de tu distribucion." >&2
    exit 1
fi

export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"

exec python3 "$HERE/usr/src/virtual-machine/virtual_machine.py" "$@"
