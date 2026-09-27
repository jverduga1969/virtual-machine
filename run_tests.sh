#!/usr/bin/env bash
# run_tests.sh — Ejecuta la suite de tests de Virtual.Machine.
#
# Todo corre con QT_QPA_PLATFORM=offscreen: los widgets de PyQt6 se
# instancian sin necesitar un servidor gráfico real.
#
# Uso:
#   ./run_tests.sh                 # toda la suite
#   ./run_tests.sh ConsoleSwitch   # solo tests que contengan ese patrón
#   ./run_tests.sh -v              # modo verbose (por defecto ya lo es)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export QT_QPA_PLATFORM=offscreen
export PYTHONWARNINGS=ignore

# Si el usuario pasa un filtro posicional, lo usamos como patrón.
# Los flags empiezan por '-' y se pasan tal cual.
PATTERN=""
EXTRA=()
for arg in "$@"; do
    if [[ "$arg" == -* ]]; then
        EXTRA+=("$arg")
    else
        PATTERN="$arg"
    fi
done

MODULES=(test_console_backend test_virtual_machine)

if [ -n "$PATTERN" ]; then
    echo "==> Filtrando tests por patrón: $PATTERN"
    python3 -m unittest -v "${EXTRA[@]}" \
        $(python3 - <<PY
import unittest
mods = "${MODULES[*]}".split()
for mod in mods:
    try:
        __import__(mod)
        m = __import__(mod)
        loader = unittest.TestLoader()
        for name in dir(m):
            if name.startswith("Test") or name.endswith("Tests"):
                cls = getattr(m, name)
                if isinstance(cls, type) and issubclass(cls, unittest.TestCase):
                    print(f"{mod}.{name}")
    except Exception:
        pass
PY
)
else
    echo "==> Ejecutando: ${MODULES[*]}"
    python3 -m unittest -v "${EXTRA[@]}" "${MODULES[@]}"
fi

echo
echo "==> Todos los tests pasaron."
