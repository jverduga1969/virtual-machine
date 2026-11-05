import pathlib
import re

CFG = pathlib.Path("plugins/config_vm/plugin.py")
if not CFG.exists():
    print("ERROR: No se encuentra plugins/config_vm/plugin.py")
    exit(1)

src = CFG.read_text(encoding="utf-8")
orig = src

# 1. Modificar DiskDialog para aceptar app
src = src.replace(
    "class DiskDialog(QDialog):\n    def __init__(self, parent=None, disk_data=None, default_dir=None):\n        super().__init__(parent)\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")",
    "class DiskDialog(QDialog):\n    def __init__(self, parent=None, disk_data=None, default_dir=None, app=None):\n        super().__init__(parent)\n        self.app = app\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")"
)

# 2. Modificar CDDVDDialog para aceptar app
src = src.replace(
    "class CDDVDDialog(QDialog):\n    def __init__(self, parent=None, cd_data=None, default_dir=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")",
    "class CDDVDDialog(QDialog):\n    def __init__(self, parent=None, cd_data=None, default_dir=None, app=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.app = app\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")"
)

# 3. Modificar FloppyDialog para aceptar app
src = src.replace(
    "class FloppyDialog(QDialog):\n    def __init__(self, parent=None, default_dir=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")",
    "class FloppyDialog(QDialog):\n    def __init__(self, parent=None, default_dir=None, app=None):\n        super().__init__(parent)\n        self.default_dir = default_dir\n        self.app = app\n        self.setWindowTitle(\"Configurar dispositivo de almacenamiento\")"
)

# 4. Arreglar _browse_library en DiskDialog
src = src.replace(
    "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.qcow2', '.img', '.raw', '.vdi', '.vmdk', '.vhd', '.vhdx'])",
    "dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.qcow2', '.img', '.raw', '.vdi', '.vmdk', '.vhd', '.vhdx'])"
)

# 5. Arreglar _browse_library en CDDVDDialog
src = src.replace(
    "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.iso', '.img', '.dmg'])",
    "dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])"
)

# 6. Arreglar _browse_library en FloppyDialog
src = src.replace(
    "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.img', '.raw', '.iso'])",
    "dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.img', '.raw', '.iso'])"
)

# 7. Pasar app=self.app al instanciar los diálogos en el Plugin
src = src.replace(
    "dlg = CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir)",
    "dlg = CDDVDDialog(self.app.parent(), default_dir=self.app.isos_dir, app=self.app)"
)
src = src.replace(
    "dlg = CDDVDDialog(self.app.parent(), cd_data, default_dir=self.app.isos_dir)",
    "dlg = CDDVDDialog(self.app.parent(), cd_data, default_dir=self.app.isos_dir, app=self.app)"
)
src = src.replace(
    "dlg = DiskDialog(self.app.parent(), default_dir=vm_dir)",
    "dlg = DiskDialog(self.app.parent(), default_dir=vm_dir, app=self.app)"
)
src = src.replace(
    "dlg = DiskDialog(self.app.parent(), disk_data, default_dir=self.app.vms_dir)",
    "dlg = DiskDialog(self.app.parent(), disk_data, default_dir=self.app.vms_dir, app=self.app)"
)
src = src.replace(
    "dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir)",
    "dlg = FloppyDialog(self.app.parent(), default_dir=self.app.isos_dir, app=self.app)"
)

if src != orig:
    CFG.write_text(src, encoding="utf-8")
    print("  OK: plugins/config_vm/plugin.py ha sido actualizado con éxito.")
else:
    print("  WARN: No se aplicaron cambios en config_vm/plugin.py (revisa si los bloques coinciden).")

print("Listo. Abre la app y el botón de biblioteca ya no debería fallar.")