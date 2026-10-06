# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""bootstrap_vnc.py — instalación automática de la Consola Gráfica.

Se llama desde `virtual_machine.py` cuando el import de `vnc_widget` falla.
Intenta, en este orden:

  1. Instalar `qvncwidget` (fuente del widget) y `python-xlib` (opcional,
     para captura de teclado X11) en el mismo intérprete que corre la app,
     vía `python -m pip install`. Si el intérprete no es un venv y pip
     falla por permisos, reintenta con `--user`.

  2. Regenerar la carpeta local `vnc_widget/` ejecutando
     `setup_vnc_widget.py` con el mismo intérprete.

  3. Volver a comprobar que `from vnc_widget import QVNCWidget` funciona.

Si todo está ya instalado, es prácticamente no-op (un `find_spec` y un
`import`), así que se puede llamar en cada arranque sin coste apreciable.

Nunca lanza excepciones: devuelve `(ok, error_msg)` para que el llamador
decida qué hacer.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

_PREFIX = "[bootstrap-vnc]"


def _log(msg):
    print(f"{_PREFIX} {msg}", flush=True)


def _warn(msg):
    print(f"{_PREFIX} ⚠️  {msg}", flush=True)


def _ok(msg):
    print(f"{_PREFIX} ✅ {msg}", flush=True)


def _has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _run_pip(package, extra_args=None):
    """Instala `package` con el mismo intérprete. Devuelve (ok, detalle)."""
    args = [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"]
    if extra_args:
        args.extend(extra_args)
    args.append(package)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, f"timeout instalando {package}"
    except Exception as e:
        return False, f"error lanzando pip para {package}: {e}"
    if proc.returncode == 0:
        return True, ""
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    detail = detail[-1] if detail else "sin detalle"
    return False, detail


def _try_install(package):
    """Intenta instalar un paquete probando variantes de pip en cascada.

    Orden (primera que funcione gana):
      1. pip install <pkg>                       (venv activo)
      2. pip install --user <pkg>                (fuera de venv)
      3. pip install --user --break-system-packages <pkg>   # pip con fallback en cascada
         (Arch, Debian 12+, Fedora 38+ bloquean el pip directo por
          PEP 668 y necesitan este flag explícito).
    Devuelve (ok, detalle)."""
    ok, err = _run_pip(package)
    if ok:
        return True, ""
    _log(f"pip install {package} falló; reintentando con --user…")
    ok, err = _run_pip(package, extra_args=["--user"])
    if ok:
        return True, ""
    _log(f"pip install --user {package} falló; reintentando con --break-system-packages…")
    ok, err = _run_pip(package, extra_args=["--user", "--break-system-packages"])
    if ok:
        return True, ""
    return False, err


def _project_root():
    """Directorio del proyecto = directorio de este archivo."""
    return Path(__file__).resolve().parent


def _regenerate_local_vnc_widget():
    """Ejecuta setup_vnc_widget.py para (re)crear la carpeta local vnc_widget/.

    Devuelve (ok, detalle).
    """
    root = _project_root()
    script = root / "setup_vnc_widget.py"
    if not script.is_file():
        return False, (
            f"No se encontró {script.name} en {root}. "
            "Crea la carpeta vnc_widget/ manualmente o restaura ese script."
        )
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(root),
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout ejecutando setup_vnc_widget.py"
    except Exception as e:
        return False, f"error lanzando setup_vnc_widget.py: {e}"
    if proc.returncode == 0:
        return True, ""
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    tail = tail[-1] if tail else "sin detalle"
    return False, tail


def _can_import_vnc_widget():
    """Comprueba realmente que el import funciona (no solo find_spec)."""
    try:
        import importlib
        if "vnc_widget" in sys.modules:
            importlib.reload(sys.modules["vnc_widget"])
        else:
            importlib.import_module("vnc_widget")
        return True, ""
    except Exception as e:
        return False, str(e)


def ensure_vnc_available():
    """Asegura que la Consola Gráfica está operativa.

    Devuelve (ok, error_msg):
      - ok=True  → vnc_widget se puede importar. La pestaña Consola aparecerá.
      - ok=False → error_msg explica qué falló y qué hacer.

    Esta función es segura de llamar siempre: si ya está todo, retorna
    rápido sin ejecutar pip ni tocar archivos.
    """
    # Camino rápido: ¿ya funciona?
    ok, _ = _can_import_vnc_widget()
    if ok:
        return True, ""

    _log("Consola Gráfica no disponible; iniciando instalación automática…")

    # ¿Falta qvncwidget (fuente)?
    if not _has_module("qvncwidget"):
        _log("Instalando qvncwidget (fuente del widget VNC)…")
        ok_q, err_q = _try_install("qvncwidget")
        if not ok_q:
            return False, (
                "No se pudo instalar qvncwidget automáticamente.\n"
                f"Detalle: {err_q}\n\n"
                "Prueba manualmente:\n"
                f"  {sys.executable} -m pip install qvncwidget"
            )
        _ok("qvncwidget instalado.")
    else:
        _log("qvncwidget ya estaba instalado.")

    # python-xlib es opcional (solo para el grab X11 de teclas especiales).
    if not _has_module("Xlib"):
        _log("Instalando python-xlib (captura de teclado X11, opcional)…")
        ok_x, err_x = _try_install("python-xlib")
        if ok_x:
            _ok("python-xlib instalado.")
        else:
            _warn(
                "No se pudo instalar python-xlib. La Consola Gráfica funcionará, "
                "pero las teclas especiales (Meta/Super, Ctrl+Alt+F*) no se podrán "
                f"capturar. Detalle: {err_x}"
            )

    # Regenerar la carpeta local vnc_widget/ (port a PyQt6).
    ok_after_install, _ = _can_import_vnc_widget()
    if not ok_after_install:
        _log("Generando carpeta local vnc_widget/ (port a PyQt6)…")
        ok_r, err_r = _regenerate_local_vnc_widget()
        if not ok_r:
            return False, (
                "qvncwidget está instalado pero no se pudo generar la carpeta "
                "local vnc_widget/.\n"
                f"Detalle: {err_r}\n\n"
                "Prueba manualmente:\n"
                f"  cd {_project_root()} && {sys.executable} setup_vnc_widget.py"
            )
        _ok("vnc_widget/ regenerado.")

    # Última comprobación.
    ok_final, err_final = _can_import_vnc_widget()
    if ok_final:
        _ok("Consola Gráfica lista.")
        return True, ""
    return False, (
        "Se instalaron/generaron las dependencias pero el import sigue fallando.\n"
        f"Detalle: {err_final}\n\n"
        "Prueba a reiniciar la aplicación. Si persiste, revisa con:\n"
        f"  {sys.executable} -c \"from vnc_widget import QVNCWidget\""
    )
