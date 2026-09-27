#!/usr/bin/env python3
"""add_license_headers.py — inserta la cabecera SPDX en cada .py del proyecto.

Cabecera insertada:

    # SPDX-License-Identifier: GPL-3.0-or-later
    # Copyright (C) 2025 Jimmy Verduga

Se preservan shebang, coding PEP 263 y docstring del módulo.

No toca scripts de parcheo (fix_*, add_*, refactor_*, etc.), backups,
terceros (vnc_widget/, OSX-KVM/) ni a sí mismo.

Idempotente. Uso:
    python3 add_license_headers.py             # aplica
    python3 add_license_headers.py --dry-run   # solo muestra qué haría
"""
import re
import sys
from pathlib import Path

G, Y, R, C, RS = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m"
def ok(m):   print(f"{G}OK{RS} {m}")
def info(m): print(f"{C}i{RS}  {m}")
def warn(m): print(f"{Y}!{RS}  {m}")
def fail(m): print(f"{R}X{RS} {m}")

DRY_RUN = "--dry-run" in sys.argv

SPDX_LINE = "# SPDX-License-Identifier: GPL-3.0-or-later"
COPY_LINE = "# Copyright (C) 2025 Jimmy Verduga"

PATCH_PREFIXES = (
    "fix_", "add_", "refactor_", "rename_", "cleanup_",
    "recover", "move_", "polish_", "install_", "integrate_",
    "switch_", "shorten_", "snapshot_", "stack_", "tune_",
    "reorder_", "reorganize_", "implement_", "enhance_",
    "export_", "help_", "improve_",
    "apply_", "setup_console_",
)

SKIP_DIRS = {
    ".git", "__pycache__", "vnc_widget", "OSX-KVM", "VirtualMachines",
    "_backups", "_patches_aplicados",
    ".venv", "venv", "env",
    "build", "dist", "node_modules",
    ".cache", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "assets", "docs", "tests",
}


def _is_patch_script(name):
    low = name.lower()
    for prefix in PATCH_PREFIXES:
        if low.startswith(prefix):
            return True
    if low in ("probe_iso_sources.py", "recover.py", "recover.py.py"):
        return True
    return False


def _insert_header(text):
    """Devuelve (texto_nuevo, cambiado)."""
    if SPDX_LINE in text[:500]:
        return text, False

    lines = text.splitlines(keepends=True)
    insert_at = 0

    # Saltar shebang
    if insert_at < len(lines) and lines[insert_at].startswith("#!"):
        insert_at += 1
    # Saltar declaración de codificación PEP 263
    if insert_at < len(lines) and re.match(r"^#.*coding[:=]", lines[insert_at]):
        insert_at += 1

    insertion = [SPDX_LINE + "\n", COPY_LINE + "\n"]
    if insert_at < len(lines) and lines[insert_at].strip() != "":
        insertion.append("\n")

    new_lines = lines[:insert_at] + insertion + lines[insert_at:]
    return "".join(new_lines), True


def _check(text):
    try:
        compile(text, "<check>", "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"línea {e.lineno}: {e.msg}"


def _iter_py_files(root):
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name = path.name
        if ".bak_before_" in name or ".bak_after_" in name or name.endswith(".bak"):
            continue
        if _is_patch_script(name):
            continue
        if name == "add_license_headers.py":
            continue
        yield path


def main():
    print(f"{C}=== add_license_headers.py ==={RS}")
    if DRY_RUN:
        print(f"{Y}Modo dry-run: no se escribirá nada.{RS}")
    print()

    root = Path(".")
    files = list(_iter_py_files(root))
    if not files:
        warn("No se encontraron archivos .py elegibles.")
        return

    changed = 0
    skipped = 0
    errored = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            fail(f"No se pudo leer {path}: {e}")
            errored += 1
            continue

        new_text, did_change = _insert_header(text)
        if not did_change:
            skipped += 1
            continue

        ok_syn, err = _check(new_text)
        if not ok_syn:
            fail(f"{path}: quedaría con error de sintaxis — {err}")
            errored += 1
            continue

        if DRY_RUN:
            info(f"[dry-run] Se añadiría cabecera a {path}")
        else:
            try:
                bak = path.with_suffix(path.suffix + ".bak_before_license_header")
                if not bak.exists():
                    bak.write_text(text, encoding="utf-8")
                path.write_text(new_text, encoding="utf-8")
                ok(f"Cabecera añadida: {path}")
            except OSError as e:
                fail(f"No se pudo escribir {path}: {e}")
                errored += 1
                continue
        changed += 1

    print()
    print(f"{C}Resumen:{RS}")
    print(f"  Archivos modificados : {changed}")
    print(f"  Ya tenían la cabecera: {skipped}")
    print(f"  Errores              : {errored}")
    print()

    if DRY_RUN:
        print(f"{Y}(dry-run) Nada se ha escrito. Quita --dry-run para aplicar.{RS}")
    elif changed > 0:
        print(f"{G}Listo. Revisa el diff con:{RS}  git diff")
    else:
        info("No había nada que cambiar.")


if __name__ == "__main__":
    main()
