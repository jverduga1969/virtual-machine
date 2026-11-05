#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

TS=$(date +%Y%m%d_%H%M%S)
BK="$PROJECT_DIR/.backups_fix_library_$TS"
mkdir -p "$BK"

echo "=========================================================="
echo " 1. Arreglando el crash en config_vm/plugin.py"
echo "=========================================================="
CFG="plugins/config_vm/plugin.py"
if [ -f "$CFG" ]; then
    cp "$CFG" "$BK/plugin.py.config_vm.bak"
    python3 - "$CFG" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# 1. Arreglar CDDVDDialog para recibir default_dir
src = src.replace(
    "class CDDVDDialog(QDialog):\n    def __init__(self, parent=None, cd_data=None):\n        super().__init__(parent)\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")\n        self.resize(500, 300)",
    "class CDDVDDialog(QDialog):\n    def __init__(self, parent=None, cd_data=None, default_dir=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")\n        self.resize(500, 300)"
)

# 2. Arreglar _browse_library en CDDVDDialog
src = src.replace(
    "            lib_dir = self.parent().app.isos_dir\n            p, _ = QFileDialog.getOpenFileName(self, \"Seleccionar de la biblioteca\", str(lib_dir), \"Imágenes (*.iso *.img *.dmg)\")",
    "            lib_dir = self.default_dir or \"\"\n            p, _ = QFileDialog.getOpenFileName(self, \"Seleccionar de la biblioteca\", str(lib_dir), \"Imágenes (*.iso *.img *.dmg)\")"
)

# 3. Arreglar FloppyDialog para recibir default_dir
src = src.replace(
    "class FloppyDialog(QDialog):\n    def __init__(self, parent=None):\n        super().__init__(parent)\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")\n        self.resize(500, 300)",
    "class FloppyDialog(QDialog):\n    def __init__(self, parent=None, default_dir=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")\n        self.resize(500, 300)"
)

# 4. Arreglar _browse_library en FloppyDialog
src = src.replace(
    "            lib_dir = self.parent().app.isos_dir\n            p, _ = QFileDialog.getOpenFileName(self, \"Seleccionar de la biblioteca\", str(lib_dir), \"Imágenes (*.img *.raw *.iso)\")",
    "            lib_dir = self.default_dir or \"\"\n            p, _ = QFileDialog.getOpenFileName(self, \"Seleccionar de la biblioteca\", str(lib_dir), \"Imágenes (*.img *.raw *.iso)\")"
)

# 5. Actualizar instanciaciones en las funciones de agregar/modificar
src = src.replace(
    "dlg = CDDVDDialog(self.app.parent())",
    "dlg = CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir)"
)
src = src.replace(
    "dlg = CDDVDDialog(self.app.parent(), cd_data)",
    "dlg = CDDVDDialog(self.app.parent(), cd_data, default_dir=self.app.isos_dir)"
)
src = src.replace(
    "dlg = FloppyDialog(self.app.parent())",
    "dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir)"
)

if src != orig:
    f.write_text(src, encoding="utf-8")
    print("  OK: Crash de biblioteca solucionado en config_vm.")
else:
    print("  WARN: No se pudo parchear config_vm/plugin.py (¿ya estaba arreglado?).")

PYEOF
fi

echo ""
echo "=========================================================="
echo " 2. Añadiendo botón de biblioteca en Crear VM (quick_vm_dialog)"
echo "=========================================================="
QVM="ui_widgets/quick_vm_dialog.py"
if [ -f "$QVM" ]; then
    cp "$QVM" "$BK/quick_vm_dialog.py.bak"
    python3 - "$QVM" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# Estrategia: buscar el botón de "Buscar" existente y clonarlo para "Biblioteca"
# Buscamos patrones típicos: btn_browse = QPushButton("..."), o btn_file, etc.
# Asumimos que el QLineEdit de la ISO se llama input_file o iso_path.

# 1. Encontrar el botón de buscar
btn_match = re.search(r'(self\.btn_\w+)\s*=\s*QPushButton\(["\']📁[^"\']*["\']\)', src)
if btn_match:
    btn_name = btn_match.group(1)
    # Crear el nuevo botón justo debajo
    new_btn = f'\n        {btn_name}_lib = QPushButton("📚 Biblioteca...")\n        {btn_name}_lib.clicked.connect(self._browse_library)'
    
    # Solo insertar si no existe ya
    if "_browse_library" not in src:
        src = src.replace(btn_match.group(0), btn_match.group(0) + new_btn)
        
        # 2. Añadir el botón al layout (buscamos donde se añade el btn de buscar)
        layout_add = re.search(r'(\w+_layout\.addWidget\(' + btn_name + r'\))', src)
        if layout_add:
            src = src.replace(layout_add.group(1), layout_add.group(1) + f'\n        {layout_add.group(1).split(".")[0]}.addWidget({btn_name}_lib)')
            
        # 3. Crear la función _browse_library en la clase QuickVMDialog (o similar)
        # Buscamos la función _browse existente
        browse_func = re.search(r'(    def _browse\(self\):.*?)(?=\n    def |\Z)', src, re.MULTILINE | re.DOTALL)
        if browse_func:
            new_func = '''
    def _browse_library(self):
        from PyQt6.QtWidgets import QFileDialog
        lib_dir = self.app.isos_dir
        p, _ = QFileDialog.getOpenFileName(self, "Biblioteca", str(lib_dir), "Imágenes (*.iso *.img *.dmg)")
        if p and hasattr(self, 'input_file'):
            self.input_file.setText(p)
'''
            src = src.replace(browse_func.group(1), browse_func.group(1) + new_func)
            print("  OK: Botón de biblioteca añadido en quick_vm_dialog.")
        else:
            print("  WARN: No se encontró la función _browse en quick_vm_dialog para inyectar la biblioteca.")
    else:
        print("  OK: quick_vm_dialog ya tiene el botón de biblioteca.")
else:
    print("  WARN: No se encontró el botón de buscar en quick_vm_dialog.")

f.write_text(src, encoding="utf-8")
PYEOF
else
    echo "  ERROR: No se encuentra $QVM"
fi

find . -name "__pycache__" -type d -exec rm -rf {} +
echo ""
echo "Listo. Prueba a abrir la app y usar la biblioteca en Config VM y en Crear VM."