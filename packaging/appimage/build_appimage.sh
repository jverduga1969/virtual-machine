#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

VERSION="${VERSION:-0.57.0}"
ARCH="$(uname -m)"
OUT="dist/virtual-machine-${VERSION}-${ARCH}.AppImage"
RECIPE_DIR="packaging/appimage/recipe"

mkdir -p dist
echo "==> Empaquetando Virtual.Machine ${VERSION} como AppImage (${ARCH})"
python-appimage build local -p "$(command -v python3)" -r "$RECIPE_DIR" -o "$OUT"
echo "==> AppImage listo: $OUT"
echo "==> Tamano: $(du -h "$OUT" | cut -f1)"
