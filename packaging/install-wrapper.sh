#!/bin/bash
# install-wrapper.sh - instala el wrapper sudo de Desktop Mode.
# Idempotente. Requiere sudo.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
SRC_WRAPPER="$REPO_DIR/packaging/virtual-machine-desktop"
DST_WRAPPER="/usr/local/bin/virtual-machine-desktop"
CONF="/etc/virtual-machine.conf"
SUDOERS="/etc/sudoers.d/virtual-machine-desktop"

if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Ejecuta con sudo: sudo bash $0" >&2
    exit 1
fi
if [ ! -f "$SRC_WRAPPER" ]; then
    echo "[ERROR] No existe $SRC_WRAPPER" >&2
    exit 1
fi
if [ ! -f "$REPO_DIR/desktop_mode.py" ]; then
    echo "[ERROR] No existe $REPO_DIR/desktop_mode.py" >&2
    exit 1
fi

USER_NAME="${SUDO_USER:-}"
if [ -z "$USER_NAME" ] || [ "$USER_NAME" = "root" ]; then
    echo "[ERROR] Ejecuta desde una cuenta de usuario, no root directo." >&2
    exit 1
fi

echo "==> Instalando wrapper en $DST_WRAPPER"
install -m 0755 "$SRC_WRAPPER" "$DST_WRAPPER"

echo "==> Escribiendo $CONF"
printf 'REPO_DIR=%q\n' "$REPO_DIR" > "$CONF"
chmod 0644 "$CONF"

echo "==> Creando regla sudoers para $USER_NAME"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cat > "$TMP" <<EOF
# Generado por install-wrapper.sh
$USER_NAME ALL=(root) NOPASSWD: $DST_WRAPPER
EOF
chmod 0644 "$TMP"
if ! visudo -c -f "$TMP" >/dev/null; then
    echo "[ERROR] La regla sudoers no valida. Abortando." >&2
    exit 1
fi
install -m 0440 -o root -g root "$TMP" "$SUDOERS"

if ! systemctl is-active --quiet seatd 2>/dev/null; then
    if command -v systemctl >/dev/null; then
        echo "==> Iniciando seatd.service"
        systemctl enable --now seatd 2>/dev/null || systemctl start seatd 2>/dev/null || true
    fi
fi

echo ""
echo "==> Listo."
echo "    Wrapper:  $DST_WRAPPER"
echo "    Config:   $CONF (REPO_DIR=$REPO_DIR)"
echo "    Sudoers:  $SUDOERS"
echo ""
echo "Prueba: python3 desktop_mode.py --vm \"NOMBRE\" --dry-run"
