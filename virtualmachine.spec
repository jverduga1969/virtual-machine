# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Recopilar módulos de los plugins y servicios
hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "psutil",
    "services.host_adapter",
    "services.qemu_paths",
    "services.host_diagnostics",
    "services.host_system_info",
    "services.hardware_scanner",
    "services.host_profile",
    "services.host_passthrough",
    "services.vm_repository",
    "services.vm_runner",
    "services.vm_profiles",
    "services.os_catalog",
    "services.iso_versions",
    "services.iso_sources",
    "services.iso_writer",
    "services.snapshot_manager",
    "services.media_library",
    "services.json_store",
    "services.download_utils",
    "services.ovf_io",
    "services.osx_kvm_updater",
    "services.host_passthrough",
    "core.plugin_base",
    "core.app_context",
    "core.plugin_manager",
    "core.theme",
    "vnc_widget.qvncwidget",
    "vnc_widget.rfbconstants",
    "vnc_widget_centered",
    "ui_widgets.resource_monitor",
    "ui_widgets.hotplug_dialog",
    "ui_widgets.download_iso_dialog",
    "ui_widgets.media_library_dialog",
    "ui_widgets.os_update_dialog",
    "ui_widgets.quick_vm_dialog",
    "plugins.console.plugin",
    "plugins.dashboard.plugin",
    "plugins.host_config.plugin",
    "plugins.config_vm.plugin",
    "plugins.snapshots.plugin",
    "plugins.media_library.plugin",
    "plugins.help.plugin",
    "plugins.progress_console.plugin",
]

# Datos a incluir (OSX-KVM, scripts, Fido, catálogos i18n, etc.)
datas = [
    ("scripts", "scripts"),
    ("Fido.ps1", "."),
    ("services/Fido.ps1", "services"),
    ("i18n", "i18n"),
    ("requirements.txt", "."),
]
if os.path.isdir("OSX-KVM"):
    datas.insert(0, ("OSX-KVM", "OSX-KVM"))

# PyInstaller no incluye un `.icn` (formato de macOS); busca el `.ico` real.
_iconos = [r for r in ("OSX-KVM/resources/icon.ico", "resources/icon.ico",
                       "icon.ico") if os.path.exists(r)]
_icono = _iconos[0] if _iconos else None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="VirtualMachine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icono,
)
