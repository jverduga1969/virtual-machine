#!/usr/bin/env bash
# Recompila las traducciones y arranca la app.
#
# Uso:
#   ./rebuild_i18n.sh                  # todos los idiomas
#   ./rebuild_i18n.sh fr               # solo frances
#   ./rebuild_i18n.sh fr pt_BR         # frances y portugues (Brasil)
#   ./rebuild_i18n.sh en fr pt_BR it de
#
# Idiomas soportados: en, fr, pt_BR, it, de
set -e
cd "$(dirname "$0")"

# Forzar locale UTF-8: Qt y pylupdate6/lrelease6 se quejan si el
# terminal viene con LC_ALL=C (ANSI_X3.4-1968). No es un error,
# pero ensucia la salida y en algun caso rompe la lectura del .ts.
export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"

if [ $# -eq 0 ]; then
    LANGS="en fr pt_BR it de"
else
    LANGS="$@"
fi

for LANG in $LANGS; do
    TS="i18n/vm_${LANG}.ts"

    echo
    echo "==============================================================="
    echo "==> Idioma: $LANG  ($TS)"
    echo "==============================================================="

    if [ ! -f .pylupdate6_sources ]; then
        echo "[!] Falta .pylupdate6_sources. Ejecuta:"
        echo "    python3 fix_i18n_multiidioma_v1_08.py"
        exit 1
    fi
    echo "==> pylupdate6 (lista blanca) -ts $TS"
    # shellcheck disable=SC2046
    pylupdate6 $(cat .pylupdate6_sources) -ts "$TS"

    echo "==> python3 translate_ts.py --lang $LANG"
    python3 translate_ts.py --lang "$LANG"

    echo "==> lrelease6 $TS"
    lrelease6 "$TS"
done

echo
echo "==> run.sh"
./run.sh
