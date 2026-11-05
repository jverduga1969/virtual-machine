#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:-$HOME/Descargas/NVM}"
cd "$PROJECT_DIR" || exit 1

TS=$(date +%Y%m%d_%H%M%S)
BK="$PROJECT_DIR/.backups_fix_bus_v2_$TS"
mkdir -p "$BK"

CFG="plugins/config_vm/plugin.py"
cp "$CFG" "$BK/plugin.py.config_vm.bak"

echo "=========================================================="
echo " Reparando lógica de buses y UI de discos"
echo "=========================================================="

python3 - "$CFG" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# 1. Actualizar opciones del ComboBox de Bus (Disco Duro)
old_hdd_bus = 'self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "NVMe", "VirtIO-BLK", "VirtIO-SCSI"])'
new_hdd_bus = 'self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "NVMe", "IDE", "SCSI (emulado)", "VirtIO-BLK", "VirtIO-SCSI"])'
src = src.replace(old_hdd_bus, new_hdd_bus)

# 2. Actualizar opciones del ComboBox de Bus (CD/DVD)
old_cd_bus = 'self.combo_bus.addItems(["SATA/AHCI", "IDE", "SCSI", "USB"])'
new_cd_bus = 'self.combo_bus.addItems(["Automático (recomendado) — SATA/AHCI", "SATA/AHCI", "IDE", "SCSI (emulado)", "USB"])'
src = src.replace(old_cd_bus, new_cd_bus)

# 3. Hacer el campo de ubicación de solo lectura y ocultarlo al usar archivo existente
old_path_ui = '''        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Ruta completa del disco...")
        self.btn_browse_path = QPushButton("📁")
        self.btn_browse_path.clicked.connect(self._browse_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.input_path)
        path_layout.addWidget(self.btn_browse_path)
        form.addRow("Ubicación del disco:", path_layout)'''
new_path_ui = '''        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Ruta completa del disco...")
        self.input_path.setReadOnly(True)
        self.btn_browse_path = QPushButton("📁")
        self.btn_browse_path.clicked.connect(self._browse_path)
        
        self.path_widget = QWidget()
        path_layout = QHBoxLayout(self.path_widget)
        path_layout.setContentsMargins(0,0,0,0)
        path_layout.addWidget(self.input_path)
        path_layout.addWidget(self.btn_browse_path)
        form.addRow("Ubicación del disco:", self.path_widget)'''
src = src.replace(old_path_ui, new_path_ui)

# 4. Modificar _toggle_mode para ocultar path_widget
old_toggle = '''    def _toggle_mode(self):
        self.widget_new.setVisible(self.radio_new.isChecked())
        self.widget_existing.setVisible(not self.radio_new.isChecked())
        if self.radio_new.isChecked(): self._update_path()'''
new_toggle = '''    def _toggle_mode(self):
        is_new = self.radio_new.isChecked()
        self.widget_new.setVisible(is_new)
        self.path_widget.setVisible(is_new)
        self.widget_existing.setVisible(not is_new)
        if is_new: self._update_path()'''
src = src.replace(old_toggle, new_toggle)

# 5. Actualizar _save_config para mapear correctamente los strings a los valores que espera vm_runner
old_save_bus = '''                bus_text = item.text(1).lower()
                if "virtio" in bus_text: data["disk_bus"] = "virtio"
                elif "nvme" in bus_text: data["disk_bus"] = "nvme"
                else: data["disk_bus"] = "sata"'''
new_save_bus = '''                bus_text = item.text(1).lower()
                if "virtio-blk" in bus_text: data["disk_bus"] = "virtio"
                elif "virtio-scsi" in bus_text: data["disk_bus"] = "virtio-scsi"
                elif "nvme" in bus_text: data["disk_bus"] = "nvme"
                elif "scsi" in bus_text: data["disk_bus"] = "scsi"
                elif "ide" in bus_text: data["disk_bus"] = "ide"
                else: data["disk_bus"] = "sata"'''
src = src.replace(old_save_bus, new_save_bus)

# 6. Mapear el CD/DVD bus en _save_config
old_save_cd = '''                data["iso_source_type"] = source_type
                data["cdrom_bus"] = item.data(3, Qt.ItemDataRole.UserRole + 1) or item.text(3) or "SATA/AHCI"'''
new_save_cd = '''                data["iso_source_type"] = source_type
                bus_text = (item.data(3, Qt.ItemDataRole.UserRole + 1) or item.text(3) or "SATA").lower()
                if "ide" in bus_text: data["cdrom_bus"] = "ide"
                elif "scsi" in bus_text: data["cdrom_bus"] = "scsi"
                elif "usb" in bus_text: data["cdrom_bus"] = "usb"
                else: data["cdrom_bus"] = "sata"'''
src = src.replace(old_save_cd, new_save_cd)

if src != orig:
    f.write_text(src, encoding="utf-8")
    print("  OK: UI y mapeo de buses actualizados.")
else:
    print("  WARN: No se aplicaron cambios.")

PYEOF

echo "=========================================================="
echo " Actualizando vm_runner.py para soportar los nuevos buses"
echo "=========================================================="

RUNNER="services/vm_runner.py"
cp "$RUNNER" "$BK/vm_runner.py.bak"

python3 - "$RUNNER" <<'PYEOF'
import sys, re, pathlib
f = pathlib.Path(sys.argv[1])
src = f.read_text(encoding="utf-8")
orig = src

# 1. Actualizar _build_cdrom_args para soportar "auto", scsi, usb, ide y sata
old_cd_args = '''        if "sata" in cdrom_bus.lower():
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ahci.1"])
        elif "scsi" in cdrom_bus.lower():
            args.extend(["-device", "scsi-cd,drive=cdrom0"])
        elif "usb" in cdrom_bus.lower():
            args.extend(["-device", "usb-storage,drive=cdrom0"])
        else:
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ide.1"])
        return args'''
new_cd_args = '''        b = cdrom_bus.lower()
        if "sata" in b or "auto" in b:
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ahci.1"])
        elif "scsi" in b:
            # Usamos el controlador SCSI emulado estándar de QEMU (lsi53c895a) para máxima compatibilidad
            args.extend(["-device", "lsi53c895a,id=scsi0"])
            args.extend(["-device", "scsi-cd,drive=cdrom0,bus=scsi0.0"])
        elif "usb" in b:
            args.extend(["-device", "usb-storage,drive=cdrom0"])
        else: # ide
            args.extend(["-device", "ide-cd,drive=cdrom0,bus=ide.1"])
        return args'''
src = src.replace(old_cd_args, new_cd_args)

# 2. Actualizar el bloque del disco duro en build_command
old_hdd_build = '''            if "nvme" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", f"nvme,serial=1234,drive=disk0"])
            elif "virtio" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=virtio"])
            elif q35:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", "ahci,id=ahci", "-device", "ide-hd,drive=disk0,bus=ahci.0"])
            else:
                cmd.extend(["-drive", f"{opts_str},if=ide"])'''
new_hdd_build = '''            if "nvme" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", f"nvme,serial=1234,drive=disk0"])
            elif "virtio-scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", "virtio-scsi-pci,id=scsi0", "-device", "scsi-hd,drive=disk0,bus=scsi0.0"])
            elif "virtio" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=virtio"])
            elif "scsi" in disk_bus:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", "lsi53c895a,id=scsi0", "-device", "scsi-hd,drive=disk0,bus=scsi0.0"])
            elif "ide" in disk_bus and not q35:
                cmd.extend(["-drive", f"{opts_str},if=ide"])
            else:
                cmd.extend(["-drive", f"{opts_str},if=none,id=disk0"])
                cmd.extend(["-device", "ahci,id=ahci", "-device", "ide-hd,drive=disk0,bus=ahci.0"])'''
src = src.replace(old_hdd_build, new_hdd_build)

if src != orig:
    f.write_text(src, encoding="utf-8")
    print("  OK: vm_runner.py actualizado con soporte SCSI, IDE y VirtIO-SCSI.")
else:
    print("  WARN: No se aplicaron cambios en vm_runner.")

PYEOF

find . -name "__pycache__" -type d -exec rm -rf {} +
echo "Listo. Abre la app y comprueba:"
echo "1. El campo 'Ubicación del disco' ahora es de solo lectura."
echo "2. Al seleccionar 'Usar archivo existente', el campo de ubicación desaparece."
echo "3. Las opciones de bus son coherentes y funcionan en VM."