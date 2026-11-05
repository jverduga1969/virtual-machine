#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

TS=$(date +%Y%m%d_%H%M%S)
BK="$PROJECT_DIR/.backups_fix_ast_$TS"
mkdir -p "$BK"

echo "=========================================================="
echo " 1. Arreglando CD/DVD y Floppy en config_vm (vía AST)"
echo "=========================================================="
CFG="plugins/config_vm/plugin.py"
if [ -f "$CFG" ]; then
    cp "$CFG" "$BK/plugin.py.config_vm.bak"
    python3 - "$CFG" <<'PYEOF'
import sys, ast, pathlib

f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
lines = src.splitlines()

# Analizar el archivo para encontrar las clases
tree = ast.parse(src)
replacements = []

class CDDVDDialog_Replacer(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        if node.name == "CDDVDDialog":
            replacements.append((node.lineno - 1, node.end_lineno, "CDDVDDialog"))
        elif node.name == "FloppyDialog":
            replacements.append((node.lineno - 1, node.end_lineno, "FloppyDialog"))
        self.generic_visit(node)

CDDVDDialog_Replacer().visit(tree)

NEW_CD = '''class CDDVDDialog(QDialog):
    def __init__(self, parent=None, cd_data=None, default_dir=None):
        super().__init__(parent)
        self.default_dir = default_dir
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>📀 Unidad CD / DVD</b>"))
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(["Mantener vacío", "Usar ISO/IMG/DMG existente", "Descargar"])
        self.combo_source.currentIndexChanged.connect(self._toggle_source)
        layout.addRow("Fuente del medio:", self.combo_source)
        
        self.input_name = QLineEdit("CD/DVD")
        layout.addRow("Nombre:", self.input_name)
        
        self.combo_bus = QComboBox()
        self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "IDE", "SCSI (emulado)", "USB"])
        layout.addRow("Bus del CD/DVD:", self.combo_bus)
        
        self.media_widget = QWidget()
        h = QHBoxLayout(self.media_widget)
        h.setContentsMargins(0,0,0,0)
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.clicked.connect(self._browse_library)
        h.addWidget(self.input_file); h.addWidget(self.btn_browse); h.addWidget(self.btn_lib)
        layout.addRow("Medio:", self.media_widget)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)
        
        if cd_data: 
            self.input_file.setText(cd_data.get("path", ""))
            if cd_data.get("bus"): self.combo_bus.setCurrentText(cd_data.get("bus"))
            if cd_data.get("path"): self.combo_source.setCurrentText("Usar ISO/IMG/DMG existente")
        
        self._toggle_source()

    def _toggle_source(self):
        is_existing = (self.combo_source.currentText() == "Usar ISO/IMG/DMG existente")
        self.media_widget.setVisible(is_existing)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes (*.iso *.img *.dmg)")
        if p: self.input_file.setText(p)
        
    def _browse_library(self):
        lib_dir = self.default_dir or ""
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar de la biblioteca", str(lib_dir), "Imágenes (*.iso *.img *.dmg)")
        if p: self.input_file.setText(p)
'''

NEW_FLOPPY = '''class FloppyDialog(QDialog):
    def __init__(self, parent=None, default_dir=None):
        super().__init__(parent)
        self.default_dir = default_dir
        self.setWindowTitle("Configurar dispositivo de almacenamiento")
        self.resize(500, 300)
        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>💾 Disquetera (FDC)</b>"))
        
        self.input_name = QLineEdit("floppy")
        layout.addRow("Nombre:", self.input_name)
        
        orig = QHBoxLayout()
        self.radio_new = QRadioButton("Crear nuevo"); self.radio_exist = QRadioButton("Usar archivo existente")
        self.radio_new.setChecked(True)
        orig.addWidget(self.radio_new); orig.addWidget(self.radio_exist)
        layout.addRow("Origen:", orig)
        
        self.combo_size = QComboBox()
        self.combo_size.addItems(["720 KB", "1.44 MB", "2.88 MB"]); self.combo_size.setCurrentText("1.44 MB")
        layout.addRow("Tamaño:", self.combo_size)
        
        self.input_format = QLineEdit("RAW"); self.input_format.setReadOnly(True)
        layout.addRow("Formato:", self.input_format)
        
        h_file = QHBoxLayout()
        self.input_file = QLineEdit()
        self.btn_browse = QPushButton("📁 Buscar...")
        self.btn_browse.clicked.connect(self._browse)
        self.btn_lib = QPushButton("📚 Biblioteca...")
        self.btn_lib.clicked.connect(self._browse_library)
        h_file.addWidget(self.input_file); h_file.addWidget(self.btn_browse); h_file.addWidget(self.btn_lib)
        layout.addRow("Archivo:", h_file)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar", "", "Imágenes (*.img *.raw)")
        if p: self.input_file.setText(p)
        
    def _browse_library(self):
        lib_dir = self.default_dir or ""
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar de la biblioteca", str(lib_dir), "Imágenes (*.img *.raw *.iso)")
        if p: self.input_file.setText(p)
'''

# Reemplazar las clases de abajo hacia arriba para no descuadrar los índices
replacements.sort(key=lambda x: x[0], reverse=True)
for start, end, name in replacements:
    new_code = NEW_CD if name == "CDDVDDialog" else NEW_FLOPPY
    lines[start:end] = new_code.splitlines()

src = "\n".join(lines) + "\n"

# Arreglar las instanciaciones para que pasen default_dir
src = src.replace("dlg = CDDVDDialog(self.app.parent())", "dlg = CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir)")
src = src.replace("dlg = CDDVDDialog(self.app.parent(), {\"path\": item.text(2)})", "dlg = CDDVDDialog(self.app.parent(), {\"path\": item.text(2)}, default_dir=self.app.isos_dir)")
src = src.replace("dlg = FloppyDialog(self.app.parent())", "dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir)")

f.write_text(src, encoding="utf-8")
print("  OK: Diálogos CD/DVD y Floppy reemplazados de forma segura.")
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

# Buscar el botón de buscar existente
btn_match = re.search(r'(self\.btn_\w+)\s*=\s*QPushButton\(["\']📁[^"\']*["\']\)', src)
if btn_match and "_browse_library" not in src:
    btn_name = btn_match.group(1)
    
    # Insertar el nuevo botón debajo
    new_btn = f'\n        {btn_name}_lib = QPushButton("📚 Biblioteca...")\n        {btn_name}_lib.clicked.connect(self._browse_library)'
    src = src.replace(btn_match.group(0), btn_match.group(0) + new_btn)
    
    # Encontrar el layout y añadirlo
    layout_match = re.search(r'(\w+_layout\.addWidget\(' + btn_name + r'\))', src)
    if layout_match:
        layout_name = layout_match.group(1).split(".")[0]
        src = src.replace(layout_match.group(1), layout_match.group(1) + f'\n        {layout_name}.addWidget({btn_name}_lib)')
        
    # Añadir la función _browse_library
    browse_func = re.search(r'(    def _browse\(self\):.*?)(?=\n    def |\Z)', src, re.MULTILINE | re.DOTALL)
    if browse_func:
        new_func = '''
    def _browse_library(self):
        from PyQt6.QtWidgets import QFileDialog
        # Asumimos que self.app está disponible, si no, usamos la ruta estándar
        lib_dir = ""
        try: lib_dir = self.app.isos_dir
        except: pass
        p, _ = QFileDialog.getOpenFileName(self, "Biblioteca", str(lib_dir), "Imágenes (*.iso *.img *.dmg)")
        if p and hasattr(self, 'input_file'):
            self.input_file.setText(p)
'''
        src = src.replace(browse_func.group(1), browse_func.group(1) + new_func)
        print("  OK: Botón de biblioteca añadido en quick_vm_dialog.")
    else:
        print("  WARN: No se encontró la función _browse en quick_vm_dialog para inyectar la biblioteca.")
elif "_browse_library" in src:
    print("  OK: quick_vm_dialog ya tiene el botón de biblioteca.")
else:
    print("  WARN: No se encontró el botón de buscar en quick_vm_dialog.")

f.write_text(src, encoding="utf-8")
PYEOF
fi

find . -name "__pycache__" -type d -exec rm -rf {} +
echo ""
echo "Listo. La app ya no debería crashear y los botones de biblioteca funcionarán."