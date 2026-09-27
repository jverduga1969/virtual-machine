#!/bin/bash
# run_debug.sh — arranca Virtual.Machine con diagnóstico de segfaults.
#
# - faulthandler: imprime la pila Python en el momento exacto del crash.
# - PYTHONFAULTHANDLER=1: garantiza que faulthandler esté activo desde el
#   arranque, incluso si el crash ocurre antes de que se ejecute nada.
# - Redirige stdout+stderr a un archivo para poder compartirlo.
#
# Uso:
#   ./run_debug.sh
#
# Cómo usarlo:
#   1. Ejecuta ./run_debug.sh
#   2. Reproduce el crash: selecciona una VM, luego pulsa la pestaña Configuración.
#   3. Cuando se cierre, mira el final de run_debug.log con:
#        tail -60 run_debug.log

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY="$(command -v python3)"
LOG="run_debug.log"

echo "==> Ejecutando con faulthandler. Log: $LOG"
echo "==> Reproduce el crash, luego revisa el final del log."
echo

PYTHONFAULTHANDLER=1 \
PYTHONUNBUFFERED=1 \
QT_LOGGING_RULES="qt.qpa.*=false" \
"$PY" -X faulthandler virtual_machine.py 2>&1 | tee "$LOG"

echo
echo "==> App terminó. Últimas 60 líneas del log:"
echo "--------------------------------------------------------------"
tail -60 "$LOG"
echo "--------------------------------------------------------------"