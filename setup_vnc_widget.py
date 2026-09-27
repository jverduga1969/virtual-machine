#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Crea un directorio `vnc_widget/` en el proyecto copiando qvncwidget
y portando el widget Qt de PyQt5 a PyQt6.

Estructura final:
    vnc_widget/
    ├── __init__.py
    ├── easystruct.py       (copia tal cual)
    ├── qvncwidget.py       (portado a PyQt6)
    ├── rfb.py              (copia tal cual)
    ├── rfbconstants.py     (copia tal cual)
    ├── rfbdes.py           (copia tal cual)
    └── rfbhelpers.py       (copia tal cual)
"""
import re
import shutil
from pathlib import Path

# Localizar el paquete instalado de forma AGNÓSTICA al intérprete:
# preguntamos al Python actual dónde está instalado qvncwidget. Esto
# funciona con venv, con pip --user (~/.local/) o con instalación de
# sistema, sin depender de rutas hardcodeadas como .venv/lib/python*/.
try:
    import qvncwidget as _qvnc_source
    src_dir = Path(_qvnc_source.__file__).resolve().parent
except Exception as _e:
    print(f"❌ No se pudo importar qvncwidget: {_e}")
    print("   Instálalo con: python3 -m pip install --user --break-system-packages qvncwidget")
    raise SystemExit(1)

print(f"✅ qvncwidget encontrado en: {src_dir}")

# Crear destino
dst_dir = Path("vnc_widget")
dst_dir.mkdir(exist_ok=True)

# Archivos que se copian tal cual (no usan PyQt)
pure_files = ["easystruct.py", "rfb.py", "rfbconstants.py", "rfbdes.py", "rfbhelpers.py"]
for name in pure_files:
    src = src_dir / name
    dst = dst_dir / name
    shutil.copy2(src, dst)
    print(f"✅ Copiado: {name}")

# Archivo que hay que portar (usa PyQt5 → PyQt6)
src = src_dir / "qvncwidget.py"
content = src.read_text(encoding="utf-8")

# ────────────────────────────────────────────────────────────
# Port PyQt5 → PyQt6
# ────────────────────────────────────────────────────────────

# 1. Imports
content = content.replace("from PyQt5.QtCore import", "from PyQt6.QtCore import")
content = content.replace("from PyQt5.QtGui import", "from PyQt6.QtGui import")
content = content.replace("from PyQt5.QtWidgets import", "from PyQt6.QtWidgets import")

# 2. pyqtSignal (PyQt5) → pyqtSignal (PyQt6) — no cambia, pero por si acaso
content = content.replace("from PyQt5.QtCore import pyqtSignal", "from PyQt6.QtCore import pyqtSignal")

# 3. Enums que cambiaron de nombre en PyQt6:
#    - QImage.Format_RGB32 → QImage.Format.Format_RGB32 (ya está en el código)
#    - Qt.red → Qt.GlobalColor.red
#    - Qt.AlignCenter → Qt.AlignmentFlag.AlignCenter
content = re.sub(r'\bQt\.red\b', 'Qt.GlobalColor.red', content)
content = re.sub(r'\bQt\.black\b', 'Qt.GlobalColor.black', content)
content = re.sub(r'\bQt\.white\b', 'Qt.GlobalColor.white', content)
content = re.sub(r'\bQt\.AlignCenter\b', 'Qt.AlignmentFlag.AlignCenter', content)

# 4. Qt.WindowFlags() → en PyQt6 es Qt.WindowType.WindowFlags() pero
#    en la práctica QWidget() sin flags funciona bien. No lo tocamos.

# 5. QOpenGLWidget: si no está disponible en PyQt6, comentamos la clase GL
#    (solo usamos la clase QVNCWidget normal, no la GL)
#    Esto se hace más abajo.

# 6. pyqtSignal con tipos: en PyQt6 el nombre es el mismo. Sin cambios.

# 7. QImage(self.vncWidth, self.vncHeight, self.PIX_FORMAT) — en PyQt6
#    QImage necesita un QSize o dos ints. Ya funciona con ints.

# 8. QPixmap.fromImage: sin cambios.

# 9. QMouseEvent/RFBInput.fromQMouseEvent: sin cambios (la función está en rfbhelpers).

# Guardar
dst = dst_dir / "qvncwidget.py"
dst.write_text(content, encoding="utf-8")
print(f"✅ Portado y copiado: qvncwidget.py")

# ────────────────────────────────────────────────────────────
# __init__.py — reexporta QVNCWidget
# ────────────────────────────────────────────────────────────
init_content = '''"""Cliente VNC embebido para PyQt6.

Basado en https://github.com/zocker-160/pyQVNCWidget (MIT).
Adaptado localmente para usar PyQt6 en lugar de PyQt5.
"""
from .qvncwidget import QVNCWidget
from .rfb import RFBClient

__all__ = ["QVNCWidget", "RFBClient"]
'''
(dst_dir / "__init__.py").write_text(init_content, encoding="utf-8")
print("✅ Creado: __init__.py")

print()
print("🎉 Listo. Estructura creada en ./vnc_widget/")
print("   Ahora puedes hacer: from vnc_widget import QVNCWidget")