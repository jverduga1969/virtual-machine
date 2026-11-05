#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

TS=$(date +%Y%m%d_%H%M%S)
BK="$PROJECT_DIR/.backups_fix_ui_library_$TS"
mkdir -p "$BK"

CFG="plugins/config_vm/plugin.py"
cp "$CFG" "$BK/plugin.py.config_vm.bak"

echo "=========================================================="
echo " Actualizando UI de CD/DVD y Floppy (Biblioteca y visibilidad)"
echo "=========================================================="

python3 - "$CFG" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# ─────────────────────────────────────────────────────────────────────
# 1. Actualizar CDDVDDialog
# ─────────────────────────────────────────────────────────────────────
new_cd_dialog = '''class CDDVDDialog(QDialog):
    def __init__(self, parent=None, cd_data=None):
        super().__init__(parent)
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
        lib_dir = self.parent().app.isos_dir
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar de la biblioteca", str(lib_dir), "Imágenes (*.iso *.img *.dmg)")
        if p: self.input_file.setText(p)
'''
pat_cd = re.compile(r'^class CDDVDDialog\(QDialog\):.*?(?=^class |\Z)', re.MULTILINE | re.DOTALL)
src = pat_cd.sub(new_cd_dialog + "\n", src)

# ─────────────────────────────────────────────────────────────────────
# 2. Actualizar FloppyDialog (Añadir Biblioteca, quitar selector de bus)
# ─────────────────────────────────────────────────────────────────────
new_floppy_dialog = '''class FloppyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        lib_dir = self.parent().app.isos_dir
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar de la biblioteca", str(lib_dir), "Imágenes (*.img *.raw *.iso)")
        if p: self.input_file.setText(p)
'''
pat_floppy = re.compile(r'^class FloppyDialog\(QDialog\):.*?(?=^class |\Z)', re.MULTILINE | re.DOTALL)
src = pat_floppy.sub(new_floppy_dialog + "\n", src)

if src != orig:
    f.write_text(src, encoding="utf-8")
    print("  OK: Diálogos CD/DVD y Floppy actualizados.")
else:
    print("  WARN: No se pudieron reemplazar los diálogos.")

PYEOF

find . -name "__pycache__" -type d -exec rm -rf {} +
echo "Listo. Ahora:"
echo "1. CD/DVD: Al elegir 'Mantener vacío' o 'Descargar', la sección de archivo se oculta."
echo "2. CD/DVD: El botón 'Biblioteca' abre la carpeta de ISOs de la app."
echo "3. Floppy: Añadido el botón 'Biblioteca' (el bus siempre es FDC internamente)."