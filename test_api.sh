#!/bin/bash
# test_api.sh — smoke test de la API REST local (marcador rest_api_v1)
#
# Uso:
#   ./test_api.sh <token> [base_url]
#
# El token se obtiene en la app:
#   Configuración Host → API REST local → Copiar

set -u
TOKEN="${1:-}"
BASE="${2:-http://127.0.0.1:8730/api}"

if [ -z "$TOKEN" ]; then
    echo "Uso: $0 <token> [base_url]"
    exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: se necesita 'curl' en el PATH."
    exit 2
fi

pass=0
fail=0

check() {
    local label="$1"; shift
    local expected="$1"; shift
    local code
    code="$("$@" 2>/dev/null | tail -n1)"
    if [ "$code" = "$expected" ]; then
        echo "PASS  $label  (HTTP $code)"
        pass=$((pass+1))
    else
        echo "FAIL  $label  (esperado HTTP $expected, obtenido $code)"
        fail=$((fail+1))
    fi
}

H_AUTH=(-H "X-API-Token: $TOKEN")
BAD_TOKEN="0000000000000000000000000000000000000000000000000000000000000000"

echo "== Probando $BASE con token ${TOKEN:0:8}... =="
echo

check "GET /health (público, 200)"      200 \
    curl -s -o /dev/null -w "%{http_code}\n" "$BASE/health"
check "GET /host (con token, 200)"      200 \
    curl -s -o /dev/null -w "%{http_code}\n" "${H_AUTH[@]}" "$BASE/host"
check "GET /vms (con token, 200)"       200 \
    curl -s -o /dev/null -w "%{http_code}\n" "${H_AUTH[@]}" "$BASE/vms"
check "GET /vms sin token (401)"        401 \
    curl -s -o /dev/null -w "%{http_code}\n" "$BASE/vms"
check "GET /vms token inválido (401)"   401 \
    curl -s -o /dev/null -w "%{http_code}\n" \
    -H "X-API-Token: $BAD_TOKEN" "$BASE/vms"
check "GET /vms/NoExiste (404)"         404 \
    curl -s -o /dev/null -w "%{http_code}\n" "${H_AUTH[@]}" "$BASE/vms/NoExiste"
check "GET /vms/../../etc/passwd (404)" 404 \
    curl -s -o /dev/null -w "%{http_code}\n" "${H_AUTH[@]}" \
    "$BASE/vms/../../etc/passwd"
check "GET /ruta-inexistente (404)"     404 \
    curl -s -o /dev/null -w "%{http_code}\n" "${H_AUTH[@]}" \
    "$BASE/ruta-inexistente"
check "PUT /vms (404, método no soportado)" 404 \
    curl -s -o /dev/null -w "%{http_code}\n" -X PUT \
    "${H_AUTH[@]}" "$BASE/vms"

echo
echo "Resultado: $pass PASS, $fail FAIL"
[ "$fail" -eq 0 ] || exit 1
exit 0
