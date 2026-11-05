#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

CFG="plugins/config_vm/plugin.py"
echo "Limpiando error de sintaxis en $CFG..."

python3 - "$CFG" <<'PYEOF'
import sys, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")

# Limpiar el argumento duplicado
bad_str = ", default_dir=self.app.isos_dir, default_dir=self.app.isos_dir)"
good_str = ", default_dir=self.app.isos_dir)"
if bad_str in src:
    src = src.replace(bad_str, good_str)
    f.write_text(src, encoding="utf-8")
    print("  OK: Argumento duplicado eliminado.")
else:
    print("  AVISO: No se encontró el duplicado exacto. Revisando otras posibles variantes...")
    # Variante con espacios
    bad_str2 = ", default_dir=self.app.isos_dir,  default_dir=self.app.isos_dir)"
    if bad_str2 in src:
        src = src.replace(bad_str2, good_str)
        f.write_text(src, encoding="utf-8")
        print("  OK: Variante con espacios eliminada.")
PYEOF

echo ""
echo "Comprobando la sintaxis de Python..."
python3 -m py_compile "$CFG" && echo "  ✓ Sintaxis correcta." || echo "  ✗ Aún hay errores de sintaxis."

find . -name "__pycache__" -type d -exec rm -rf {} +
echo "Listo. Ya puedes volver a abrir la app."