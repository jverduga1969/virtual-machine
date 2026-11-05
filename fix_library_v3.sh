#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

TS=$(date +%Y%m%d_%H%M%S)
BK="$PROJECT_DIR/.backups_fix_library_v3_$TS"
mkdir -p "$BK"

echo "=========================================================="
echo " 1. Forzando ruta de biblioteca en config_vm/plugin.py"
echo "=========================================================="
CFG="plugins/config_vm/plugin.py"
cp "$CFG" "$BK/plugin.py.config_vm.bak"
python3 - "$CFG" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")

# Buscar llamadas a CDDVDDialog y FloppyDialog e inyectar default_dir
src = re.sub(r"CDDVDDialog\(self\.app\.parent\(\)\)", "CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir)", src)
src = re.sub(r"CDDVDDialog\(self\.app\.parent\(\), (.*?)\)", r"CDDVDDialog(self.app.parent(), \1, default_dir=self.app.isos_dir)", src)
src = re.sub(r"FloppyDialog\(self\.app\.parent\(\)\)", "FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir)", src)

f.write_text(src, encoding="utf-8")
print("  OK: Llamadas parcheadas en config_vm.")
PYEOF

echo ""
echo "=========================================================="
echo " 2. Forzando botón biblioteca en ui_widgets/quick_vm_dialog.py"
echo "=========================================================="
QVM="ui_widgets/quick_vm_dialog.py"
cp "$QVM" "$BK/quick_vm_dialog.py.bak"

python3 - "$QVM" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# Buscar cualquier QPushButton que contenga 'Buscar' o el icono de carpeta
match = re.search(r"self\.(\w+)\s*=\s*QPushButton\(['\"].*?Buscar.*?['\"]\)", src)
if not match:
    match = re.search(r"self\.(\w+)\s*=\s*QPushButton\(['\"]📁.*?['\"]\)", src)

if match and "btn_library" not in src:
    btn_name = match.group(1)
    
    # Inyectar el botón
    src = src.replace(match.group(0), match.group(0) + f'\n        self.btn_library = QPushButton("📚 Biblioteca...")\n        self.btn_library.clicked.connect(self._browse_library)')
    
    # Inyectar en el layout
    layout_match = re.search(r"(\w+)\.addWidget\(" + btn_name + r"\)", src)
    if layout_match:
        layout_name = layout_match.group(1)
        src = src.replace(layout_match.group(0), layout_match.group(0) + f'\n        {layout_name}.addWidget(self.btn_library)')
        
    # Inyectar la función
    init_match = re.search(r"(    def __init__\(self.*?)(?=\n    def |\Z)", src, re.DOTALL)
    if init_match:
        new_method = """
    def _browse_library(self):
        from PyQt6.QtWidgets import QFileDialog
        lib_dir = ""
        if hasattr(self, "app") and hasattr(self.app, "isos_dir"):
            lib_dir = self.app.isos_dir
        
        path, _ = QFileDialog.getOpenFileName(self, "Biblioteca", str(lib_dir), "Imágenes (*.iso *.img *.dmg)")
        if path:
            # Buscar el QLineEdit correspondiente a la ISO
            if hasattr(self, "input_iso"): self.input_iso.setText(path)
            elif hasattr(self, "iso_path"): self.iso_path.setText(path)
            elif hasattr(self, "input_file"): self.input_file.setText(path)
"""
        src = src.replace(init_match.group(1), init_match.group(1) + new_method)
        print("  OK: Botón de biblioteca añadido en quick_vm_dialog.")
    else:
        print("  WARN: No se encontró __init__ para inyectar.")
elif "btn_library" in src:
    print("  OK: El botón ya existe.")
else:
    print("  ⚠️ ALERTA: No se encontró el botón de 'Buscar' en quick_vm_dialog.py.")
    print("  Aquí tienes los botones que SÍ se han encontrado en el archivo:")
    for line in src.splitlines():
        if "QPushButton(" in line and "self." in line:
            print("    " + line.strip())

f.write_text(src, encoding="utf-8")
PYEOF

find . -name "__pycache__" -type d -exec rm -rf {} +
echo ""
echo "Listo. Abre la app y comprueba:"
echo "1. En Config VM -> CD/DVD, el botón de biblioteca ya debería abrir la carpeta de ISOs."
echo "2. En Crear VM, si el script encontró el botón, ahora tendrás uno de biblioteca al lado."