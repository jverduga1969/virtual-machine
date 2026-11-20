"""Atajos de teclado configurables y compartidos por la app."""

DEFAULT_SHORTCUTS = {
    "command_palette": "Ctrl+K",
    "new_vm": "Ctrl+N",
    "start_vm": "F5",
    "stop_vm": "F6",
    "history": "Ctrl+H",
    "from_template": "Ctrl+T",
    "save_template": "Ctrl+Shift+T",
    "go_media": "Ctrl+M",
    "go_snapshots": "Ctrl+Shift+S",
    "shortcut_settings": "Ctrl+Shift+K",
}

COMMAND_LABELS = {
    "command_palette": "Abrir paleta de comandos",
    "new_vm": "Crear VM nueva",
    "start_vm": "Encender VM seleccionada",
    "stop_vm": "Apagar VM seleccionada",
    "history": "Ver historial de la VM",
    "from_template": "Nueva VM desde plantilla",
    "save_template": "Guardar VM como plantilla",
    "go_media": "Ir a la pestaña Medios",
    "go_snapshots": "Ir a la pestaña Snapshots",
    "shortcut_settings": "Configurar atajos de teclado",
}


def normalize(sequence):
    """Compara atajos sin importar mayúsculas ni espacios sobrantes."""
    return "".join(str(sequence).lower().replace(" ", "").split("+"))


class ShortcutStore:
    def __init__(self, settings):
        self.settings = settings

    def get(self, name):
        return (self.settings.value(f"shortcuts/{name}", "")
                or DEFAULT_SHORTCUTS.get(name, ""))

    def set(self, name, sequence):
        self.settings.setValue(f"shortcuts/{name}", str(sequence))

    def reset(self, name):
        self.settings.setValue(f"shortcuts/{name}", DEFAULT_SHORTCUTS.get(name, ""))

    def reset_all(self):
        for name in DEFAULT_SHORTCUTS:
            self.reset(name)

    def all(self):
        return {name: self.get(name) for name in DEFAULT_SHORTCUTS}

    def conflicts(self, sequence, exclude=None):
        """Devuelve los comandos que ya usan este atajo."""
        objetivo = normalize(sequence)
        if not objetivo:
            return []
        return [name for name, seq in self.all().items()
                if name != exclude and normalize(seq) == objetivo]
