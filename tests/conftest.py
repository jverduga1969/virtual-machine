"""Configuración común de la suite headless.

Se ejecuta antes de importar cualquier módulo de la app, así que aquí se
fijan las variables de entorno que hacen falta para que PyQt6 funcione sin
servidor gráfico y para que los QSettings de los tests no toquen la
configuración real del usuario.
"""

import atexit
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_CONFIG_DIR = Path(tempfile.mkdtemp(prefix="nvm-tests-config-"))
os.environ["XDG_CONFIG_HOME"] = str(_CONFIG_DIR)
atexit.register(lambda: shutil.rmtree(_CONFIG_DIR, ignore_errors=True))

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _plataforma_neutra(monkeypatch):
    """Los tests heredados simulan Windows/Linux con dos flags sueltos.

    Al importar en macOS, ``IS_MAC`` queda a True y esas simulaciones entran
    en las ramas nuevas de la Fase D. Lo neutralizamos por test; las pruebas
    que de verdad cubren macOS lo vuelven a poner a True con monkeypatch.
    """
    modulos = (
        "core.app_context",
        "services.host_adapter",
        "services.host_diagnostics",
        "services.host_profile",
        "services.host_system_info",
        "services.qemu_paths",
        "services.vm_runner",
    )
    import importlib
    for nombre in modulos:
        modulo = importlib.import_module(nombre)
        if hasattr(modulo, "IS_MAC"):
            monkeypatch.setattr(modulo, "IS_MAC", False)


@pytest.fixture(scope="session")
def qapp():
    """Única QApplication del proceso, con organization/app name de la app."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setOrganizationName("VirtualMachine")
    app.setApplicationName("VirtualMachineApp")
    return app


class FakeRunner:
    """Sustituto de VMRunner: no lanza QEMU, solo registra llamadas."""

    def __init__(self):
        self.active_processes = {}
        self.calls = []

    def stop_vm(self, vm_id):
        self.calls.append(("stop", vm_id))

    def force_stop_vm(self, vm_id):
        self.calls.append(("force_stop", vm_id))

    def start_vm(self, vm):
        self.calls.append(("start", vm["id"]))
        self.active_processes[vm["id"]] = object()
        return self.active_processes[vm["id"]]

    def pause_vm(self, vm_id):
        self.calls.append(("pause", vm_id))
        return True

    def resume_vm(self, vm_id):
        self.calls.append(("resume", vm_id))
        return True

    def change_iso(self, vm_id, iso_path):
        self.calls.append(("change_iso", vm_id, iso_path))
        return True


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """QSettings en un INI temporal, con rutas de datos también temporales."""
    from PyQt6.QtCore import QSettings

    import core.app_context as ac

    base = tmp_path / "data"
    settings = QSettings(str(tmp_path / "config.ini"), QSettings.Format.IniFormat)
    settings.setValue("paths/base_dir", str(base))
    settings.setValue("paths/vms_dir", str(base / "vms"))
    settings.setValue("paths/isos_dir", str(base / "isos"))
    # Qt cachea XDG_CONFIG_HOME al crear la QApplication; inyectar el objeto
    # es la única forma garantizada de no leer la configuración del usuario.
    monkeypatch.setattr(ac, "QSettings", lambda: settings)
    return settings


@pytest.fixture
def app_ctx(qapp, isolated_settings, monkeypatch):
    """AppContext aislado: datos y QSettings en directorios temporales."""
    from core.app_context import AppContext

    ctx = AppContext()
    monkeypatch.setattr(ctx, "_notify_desktop", lambda *args, **kwargs: None)
    yield ctx
    # AppContext añade un handler global de logs: retirarlo para no dejar
    # señales conectadas a un QObject ya destruido entre tests.
    logging.getLogger().removeHandler(ctx._log_handler)
