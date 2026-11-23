"""Plantillas de VM definidas por el usuario.

Una plantilla guarda el "perfil de hardware" de una VM (CPU, RAM, firmware,
red...) para crear otras nuevas sin repetir todos los ajustes. A diferencia de
clonar, no copia discos ni datos del invitado.
"""

import unicodedata
import uuid
from pathlib import Path

from services.json_store import atomic_write_json, quarantine, read_json

# Datos de ejecución o exclusivos de cada VM: no van en la plantilla.
EXCLUDED_FIELDS = frozenset({
    "id", "name", "state", "qmp_socket", "vnc_port", "vnc_heads",
    "spice_port", "disk_path", "notes", "last_used", "used_by",
})
ICONOS = ("📋", "🐧", "🪟", "🍎", "💻", "🎮", "🧪", "🌐")


class TemplateManager:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.db_file = self.data_dir / "templates.json"
        self._templates = []
        self.load()

    def load(self):
        datos = read_json(self.db_file, None)
        if not isinstance(datos, list):
            if self.db_file.exists():
                quarantine(self.db_file)
            self._templates = []
            return
        self._templates = [t for t in datos if isinstance(t, dict)]

    def save(self):
        atomic_write_json(self.db_file, self._templates)

    @staticmethod
    def extract_config(vm):
        return {k: v for k, v in vm.items() if k not in EXCLUDED_FIELDS}

    @staticmethod
    def _clave_nombre(nombre):
        """Compara nombres sin distinguir mayúsculas ni tildes."""
        normalizado = unicodedata.normalize("NFD", str(nombre).lower())
        return "".join(c for c in normalizado if not unicodedata.combining(c))

    def list_templates(self):
        return list(self._templates)

    def save_template(self, name, vm, icon="📋", description="", template_id=None):
        config = self.extract_config(vm)
        nombre = str(name).strip()
        if not nombre:
            raise ValueError("El nombre de la plantilla no puede estar vacío.")
        description = str(description).strip()
        clave = self._clave_nombre(nombre)
        existente = next((t for t in self._templates
                          if t["id"] == template_id
                          or self._clave_nombre(t["name"]) == clave), None)
        if existente:
            existente.update({"name": nombre, "icon": icon,
                              "description": description, "config": config})
            plantilla = existente
        else:
            plantilla = {
                "id": str(uuid.uuid4()),
                "name": nombre,
                "icon": icon,
                "description": description,
                "config": config,
            }
            self._templates.append(plantilla)
        self.save()
        return plantilla

    def delete_template(self, template_id):
        antes = len(self._templates)
        self._templates = [t for t in self._templates if t["id"] != template_id]
        if len(self._templates) != antes:
            self.save()
            return True
        return False

    def get_template(self, template_id):
        return next((t for t in self._templates if t["id"] == template_id), None)

    def create_vm_config(self, template_id, name, disk_path=None):
        """Devuelve la configuración de una VM nueva basada en la plantilla."""
        plantilla = self.get_template(template_id)
        if plantilla is None:
            raise KeyError(f"Plantilla no encontrada: {template_id}")
        nombre = str(name).strip() or f"VM desde {plantilla['name']}"
        config = dict(plantilla.get("config") or {})
        config.update({
            "id": str(uuid.uuid4()),
            "name": nombre,
            "state": "Apagada",
            "disk_path": str(disk_path) if disk_path else "",
        })
        return config
