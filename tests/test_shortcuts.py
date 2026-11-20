"""Atajos configurables y paleta de comandos."""

from services.shortcuts import DEFAULT_SHORTCUTS, ShortcutStore, normalize


class FakeSettings:
    def __init__(self):
        self.datos = {}

    def value(self, key, default=""):
        return self.datos.get(key, default)

    def setValue(self, key, value):
        self.datos[key] = value


def test_valores_por_defecto_y_persistencia():
    store = ShortcutStore(FakeSettings())

    assert store.get("command_palette") == "Ctrl+K"
    assert store.get("new_vm") == "Ctrl+N"
    assert set(store.all()) == set(DEFAULT_SHORTCUTS)

    store.set("new_vm", "Ctrl+Shift+N")
    assert store.get("new_vm") == "Ctrl+Shift+N"
    assert store.get("command_palette") == "Ctrl+K"

    store.reset("new_vm")
    assert store.get("new_vm") == "Ctrl+N"
    store.set("start_vm", "F9")
    store.reset_all()
    assert store.all() == DEFAULT_SHORTCUTS


def test_deteccion_de_conflictos_ignora_mayusculas_y_espacios():
    store = ShortcutStore(FakeSettings())

    assert store.conflicts("ctrl+k") == ["command_palette"]
    assert store.conflicts("Ctrl + K") == ["command_palette"]
    assert store.conflicts("Ctrl+Shift+T") == ["save_template"]
    assert store.conflicts("Ctrl+K", exclude="command_palette") == []
    assert store.conflicts("F12") == []
    assert store.conflicts("") == []

    store.set("new_vm", "ctrl+k")
    assert set(store.conflicts("CTRL+K")) == {"command_palette", "new_vm"}


def test_normalizar_atajo():
    assert normalize("Ctrl+K") == normalize("ctrl + k") == "ctrlk"
    assert normalize("F5") == "f5"


def test_paleta_de_comandos_filtra_y_ejecuta(qapp):
    from ui_widgets.command_palette import CommandPalette

    ejecutados = []
    comandos = [
        {"id": "uno", "label": "Crear VM nueva", "shortcut": "Ctrl+N",
         "callback": lambda: ejecutados.append("uno")},
        {"id": "dos", "label": "Ver historial", "shortcut": "Ctrl+H",
         "callback": lambda: ejecutados.append("dos")},
    ]
    paleta = CommandPalette(comandos)

    assert paleta.lista.count() == 2
    paleta.buscar.setText("historial")
    assert paleta.lista.count() == 1
    paleta._ejecutar_actual()

    assert ejecutados == ["dos"]
    paleta.close()


def test_dialogo_de_atajos_guarda_y_restablece(qapp):
    from ui_widgets.shortcut_settings import ShortcutSettingsDialog

    settings = FakeSettings()
    store = ShortcutStore(settings)
    dlg = ShortcutSettingsDialog(store)

    assert len(dlg.edits) == len(DEFAULT_SHORTCUTS)
    dlg.edits["new_vm"].setKeySequence("Ctrl+Shift+N")
    dlg._guardar()
    assert store.get("new_vm") == "Ctrl+Shift+N"

    dlg._restablecer()
    dlg._guardar()
    assert store.get("new_vm") == "Ctrl+N"
    dlg.close()
