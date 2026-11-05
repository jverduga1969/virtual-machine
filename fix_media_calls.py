import re
import pathlib

# 1. Parchear config_vm/plugin.py
cfg = pathlib.Path("plugins/config_vm/plugin.py")
if cfg.exists():
    src = cfg.read_text(encoding="utf-8")
    
    # Arreglar DiskDialog
    src = src.replace(
        "dlg = MediaLibraryDialog(self, default_dir=self.default_dir, file_filters=['.qcow2', '.img', '.raw', '.vdi', '.vmdk', '.vhd', '.vhdx'])",
        "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.qcow2', '.img', '.raw', '.vdi', '.vmdk', '.vhd', '.vhdx'])"
    )
    # Arreglar CDDVDDialog
    src = src.replace(
        "dlg = MediaLibraryDialog(self, default_dir=self.default_dir, file_filters=['.iso', '.img', '.dmg'])",
        "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.iso', '.img', '.dmg'])"
    )
    # Arreglar FloppyDialog
    src = src.replace(
        "dlg = MediaLibraryDialog(self, default_dir=self.default_dir, file_filters=['.img', '.raw', '.iso'])",
        "dlg = MediaLibraryDialog(self, app=self.parent().app, file_filters=['.img', '.raw', '.iso'])"
    )
    cfg.write_text(src, encoding="utf-8")
    print("  OK: config_vm/plugin.py actualizado.")

# 2. Parchear ui_widgets/quick_vm_dialog.py
qvm = pathlib.Path("ui_widgets/quick_vm_dialog.py")
if qvm.exists():
    src = qvm.read_text(encoding="utf-8")
    src = src.replace(
        "dlg = MediaLibraryDialog(self, default_dir=self.app.isos_dir, file_filters=['.iso', '.img', '.dmg'])",
        "dlg = MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])"
    )
    # En caso de que el parche anterior haya dejado una versión distinta
    src = re.sub(
        r"MediaLibraryDialog\(self,\s*default_dir=[^,]+,\s*file_filters=\['\.iso',\s*'\.img',\s*'\.dmg'\]\)",
        "MediaLibraryDialog(self, app=self.app, file_filters=['.iso', '.img', '.dmg'])",
        src
    )
    qvm.write_text(src, encoding="utf-8")
    print("  OK: quick_vm_dialog.py actualizado.")

print("Limpieza completada. Ya puedes abrir la app.")