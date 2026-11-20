"""Las validaciones del descargador de macOS sobreviven a python -O (Fase 1)."""

import ast
import subprocess
import sys
from pathlib import Path

from conftest import ROOT

FETCH = ROOT / "services" / "fetch-macOS-v2.py"


def test_no_quedan_assert_en_el_descargador():
    arbol = ast.parse(FETCH.read_text(encoding="utf-8"))

    assert not [n for n in ast.walk(arbol) if isinstance(n, ast.Assert)]


def test_validaciones_activas_con_python_optimizado():
    codigo = f"""
import importlib.util
spec = importlib.util.spec_from_file_location('fetch_macos', {str(FETCH)!r})
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except SystemExit:
    pass
mod._check(True, 'correcto')
try:
    mod._check(False, 'boom')
except ValueError as e:
    print('VALIDACION:', e)
else:
    raise SystemExit('la validación no se ejecutó')
"""
    proceso = subprocess.run(
        [sys.executable, "-O", "-c", codigo],
        capture_output=True, text=True, cwd=ROOT, timeout=30)

    assert proceso.returncode == 0, proceso.stderr
    assert "VALIDACION: boom" in proceso.stdout
