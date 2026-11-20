import os
import json
import logging
import subprocess
import hashlib
import re
import threading
from pathlib import Path
from datetime import datetime

from services.json_store import atomic_write_json, quarantine, read_json

log = logging.getLogger(__name__)
try:
    from PyQt6.QtCore import QSettings
    _HAS_QSETTINGS = True
except ImportError:
    QSettings = None
    _HAS_QSETTINGS = False

# Extensiones que la biblioteca considera medios. Incluye .dmg porque el
# descargador de macOS guarda ese formato en la carpeta de ISOs.
MEDIA_EXTENSIONS = (".iso", ".img", ".dmg", ".qcow2", ".raw", ".vdi", ".vmdk")

# Claves de la configuración de una VM que apuntan a un archivo de medios.
VM_MEDIA_KEYS = ("disk_path", "iso_path", "floppy_path")


class MediaLibraryManager:
    def __init__(self, data_dir: Path, settings=None):
        self.data_dir = data_dir
        self._lock = threading.RLock()
        saved_media_dir = ""
        # ``settings`` es el QSettings compartido por AppContext (Fase 0).
        # El fallback mantiene compatibilidad con llamadas antiguas.
        store = settings or (QSettings() if _HAS_QSETTINGS else None)
        if store is not None:
            try:
                saved_media_dir = store.value("paths/media_dir", "")
            except Exception:
                saved_media_dir = ""
        if saved_media_dir:
            self.media_dir = Path(saved_media_dir)
        else:
            self.media_dir = self.data_dir / "MediaLibrary"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "media_library.json"
        self._media = []
        self.load()

    def load(self):
        raw = read_json(self.db_file, None)
        if raw is None or not isinstance(raw, list):
            if self.db_file.exists():
                dest = quarantine(self.db_file)
                log.error(
                    "Biblioteca de medios corrupta%s; se arranca vacía.",
                    f" (copia en {dest})" if dest else "",
                )
            self._media = []
            return
        self._media = raw

    def save(self):
        with self._lock:
            atomic_write_json(self.db_file, self._media)

    def get_all(self):
        return self._media

    def _format_size(self, bytes_size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def get_virtual_size_bytes(self, path):
        ext = path.lower().split('.')[-1]
        if ext in ("iso", "img"):
            return os.path.getsize(path)
        try:
            result = subprocess.run(
                ["qemu-img", "info", "--output=json", path],
                capture_output=True, text=True, check=True
            )
            info = json.loads(result.stdout)
            return info.get("virtual-size", 0)
        except Exception:
            return 0

    def get_virtual_size(self, path):
        ext = path.lower().split('.')[-1]
        if ext in ("iso", "img"):
            return self._format_size(os.path.getsize(path))
        b = self.get_virtual_size_bytes(path)
        return self._format_size(b) if b > 0 else "-"

    @staticmethod
    def _normalize_path(path):
        """Compara rutas sin que diferencias de `./`, `~` o mayúsculas cuenten."""
        return os.path.normcase(os.path.abspath(os.path.expanduser(str(path))))

    def _make_item(self, name, path, media_type, size_real="-", size_vm="-",
                   os_type="Other", arch="x86_64", fmt="ISO", used_by="-",
                   last_used=None):
        path = str(path)
        if size_real == "-" and os.path.isfile(path):
            size_real = self._format_size(os.path.getsize(path))
        if size_vm == "-" and os.path.isfile(path):
            size_vm = self.get_virtual_size(path)
        return {
            "id": str(hash(path)),
            "name": name, "path": path, "type": media_type,
            "os": os_type, "version": "Unknown", "arch": arch,
            "size_real": size_real, "size_vm": size_vm,
            "used_by": used_by,
            "status": "OK" if os.path.isfile(path) else "huérfano",
            "last_used": last_used or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "format": fmt, "notes": "", "tags": "", "color": ""
        }

    def add_media(self, name, path, media_type, size_real, size_vm="-", os_type="Other", arch="x86_64", fmt="ISO", used_by="-", last_used=None):
        path = str(path)
        destino = self._normalize_path(path)
        with self._lock:
            if any(self._normalize_path(m.get("path", "")) == destino
                   for m in self._media):
                return False
            self._media.append(self._make_item(
                name, path, media_type, size_real, size_vm, os_type, arch,
                fmt, used_by, last_used,
            ))
            self.save()
            return True

    def reconcile(self, extra_dirs=()):
        """Sincroniza el JSON con el disco.

        Elimina entradas cuyo archivo ya no existe y añade los medios
        presentes en la carpeta de la biblioteca (y en ``extra_dirs``,
        normalmente la carpeta de ISOs) que aún no estuvieran registrados.
        """
        with self._lock:
            vistos = set()
            conservados = []
            eliminados = 0
            actualizados = 0

            for media in self._media:
                path = media.get("path", "")
                if not path or not os.path.isfile(path):
                    eliminados += 1
                    continue
                normalizado = self._normalize_path(path)
                if normalizado in vistos:
                    eliminados += 1
                    continue
                vistos.add(normalizado)

                cambiado = False
                if media.get("status") != "OK":
                    media["status"] = "OK"
                    cambiado = True
                size_real = self._format_size(os.path.getsize(path))
                if media.get("size_real") != size_real:
                    media["size_real"] = size_real
                    cambiado = True
                if cambiado:
                    actualizados += 1
                conservados.append(media)

            dirs = [self.media_dir]
            dirs.extend(Path(d) for d in extra_dirs if d)
            vistos_dirs = set()
            nuevos = []
            for directory in dirs:
                if not directory or not Path(directory).is_dir():
                    continue
                clave_dir = self._normalize_path(directory)
                if clave_dir in vistos_dirs:
                    continue
                vistos_dirs.add(clave_dir)
                for root, _, files in os.walk(directory):
                    for nombre in files:
                        if not nombre.lower().endswith(MEDIA_EXTENSIONS):
                            continue
                        completo = os.path.join(root, nombre)
                        normalizado = self._normalize_path(completo)
                        if normalizado in vistos:
                            continue
                        vistos.add(normalizado)
                        nuevos.append(completo)

            for completo in nuevos:
                fmt = Path(completo).suffix.lstrip(".").upper()
                tipo = "ISO" if fmt in ("ISO", "IMG", "DMG") else "Disco duro"
                conservados.append(self._make_item(
                    Path(completo).name, completo, tipo, fmt=fmt,
                ))

            if eliminados or nuevos or actualizados:
                self._media = conservados
                self.save()
            return {"removed": eliminados, "added": len(nuevos),
                    "updated": actualizados}

    @staticmethod
    def _vm_media_paths(vm):
        """Todas las rutas de medios referenciadas por una configuración de VM."""
        if not isinstance(vm, dict):
            return
        for clave in VM_MEDIA_KEYS:
            valor = vm.get(clave)
            if valor:
                yield valor
        for clave in ("optical_drives", "disks", "cdroms", "storage_devices", "drives"):
            for entrada in (vm.get(clave) or []):
                if isinstance(entrada, dict):
                    valor = (entrada.get("path") or entrada.get("file")
                             or entrada.get("source"))
                    if valor:
                        yield valor
                elif isinstance(entrada, str) and entrada.startswith("Unidad óptica — "):
                    yield entrada[len("Unidad óptica — "):]
        for entrada in (vm.get("boot_order") or []):
            if isinstance(entrada, str) and entrada.startswith("Unidad óptica — "):
                yield entrada[len("Unidad óptica — "):]

    def sync_usage(self, vms):
        """Rellena `used_by` con las VMs que usan cada medio.

        Se recalcula desde el repositorio de VMs en cada refresco, así que
        nunca queda obsoleto si una VM cambia de disco o de ISO.
        """
        with self._lock:
            uso = {}
            for vm in vms or []:
                nombre = vm.get("name") or vm.get("id") or "VM"
                for path in self._vm_media_paths(vm):
                    uso.setdefault(self._normalize_path(path), set()).add(nombre)

            cambiado = False
            for media in self._media:
                nombres = uso.get(self._normalize_path(media.get("path", "")), set())
                valor = ", ".join(sorted(nombres)) if nombres else "-"
                if media.get("used_by") != valor:
                    media["used_by"] = valor
                    cambiado = True
            if cambiado:
                self.save()
            return cambiado

    def update_media_size(self, path, size_vm):
        """Actualiza el tamaño virtual registrado para un medio existente."""
        changed = False
        for m in self._media:
            if m.get("path") == str(path):
                m["size_vm"] = size_vm
                changed = True
                break
        if changed:
            self.save()
        return changed

    def scan_directory(self, directory):
        added = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(MEDIA_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    fmt = file.split('.')[-1].upper()
                    m_type = "ISO" if fmt in ("ISO", "IMG") else "Disco duro"
                    if self.add_media(file, full_path, m_type, "-", fmt=fmt):
                        added += 1
        return added

    def scan_vms(self, vms_dir):
        """Escanea la carpeta de VMs buscando discos no registrados."""
        added = 0
        if not vms_dir.exists():
            return 0
        for root, _, files in os.walk(vms_dir):
            for file in files:
                if file.lower().endswith(MEDIA_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    fmt = file.split('.')[-1].upper()
                    if self.add_media(file, full_path, "Disco duro", "-", fmt=fmt):
                        added += 1
        return added

    def create_disk(self, name, size, fmt="qcow2", path=None):
        if not path:
            path = self.media_dir / f"{name}.{fmt}"
        cmd = ["qemu-img", "create", "-f", fmt, str(path), size]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            self.add_media(name, str(path), "Disco duro", "-", size_vm=size, fmt=fmt.upper())
            return True, str(path)
        except Exception as e:
            return False, str(e)

    def resize_disk(self, path, new_size_str):
        current_bytes = self.get_virtual_size_bytes(path)
        new_bytes = self._parse_size_to_bytes(new_size_str)
        
        if new_bytes == -1:
            return False, f"Formato de tamaño inválido: '{new_size_str}'"
        if new_bytes < current_bytes:
            return False, f"No se puede reducir el tamaño.\nActual: {self._format_size(current_bytes)}\nSolicitado: {new_size_str}"
        if new_bytes == current_bytes:
            return True, "El tamaño es el mismo, no se requiere cambios."

        try:
            cmd = ["qemu-img", "resize", path, new_size_str]
            subprocess.run(cmd, check=True, capture_output=True)
            return True, f"Disco redimensionado a {new_size_str}."
        except Exception as e:
            return False, str(e)

    def _parse_size_to_bytes(self, size_str):
        size_str = str(size_str).upper().strip()
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTP]?)B?$', size_str)
        if not match:
            return -1
        val = float(match.group(1))
        unit = match.group(2)
        multipliers = {'': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4, 'P': 1024**5}
        return int(val * multipliers[unit])

    def compact_disk(self, path):
        if not path.lower().endswith('.qcow2'):
            return False, "Solo se pueden compactar discos QCOW2."
        tmp_path = f"{path}.tmp"
        try:
            cmd = ["qemu-img", "convert", "-O", "qcow2", "-c", path, tmp_path]
            subprocess.run(cmd, check=True, capture_output=True)
            os.replace(tmp_path, path)
            return True, "Compactado con éxito."
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False, str(e)

    def get_sha256(self, path):
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"Error: {e}"