import os
import json
import logging
import subprocess
import hashlib
import re
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)

class MediaLibraryManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.media_dir = self.data_dir / "MediaLibrary"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "media_library.json"
        self._media = []
        self.load()

    def load(self):
        if self.db_file.exists():
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self._media = json.load(f)
            except Exception as e:
                log.error(f"Error cargando biblioteca: {e}")
                self._media = []
        else:
            self._media = []

    def save(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self._media, f, indent=4)
        except Exception as e:
            log.error(f"Error guardando biblioteca: {e}")

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

    def add_media(self, name, path, media_type, size_real, size_vm="-", os_type="Other", arch="x86_64", fmt="ISO"):
        if size_real == "-" and os.path.exists(path):
            size_real = self._format_size(os.path.getsize(path))
        
        if size_vm == "-" and os.path.exists(path):
            size_vm = self.get_virtual_size(path)
            
        item = {
            "id": str(hash(path)),
            "name": name, "path": str(path), "type": media_type,
            "os": os_type, "version": "Unknown", "arch": arch,
            "size_real": size_real, "size_vm": size_vm,
            "used_by": "-", "status": "OK" if os.path.exists(path) else "huérfano",
            "last_used": datetime.now().strftime("%Y-%m-%d"),
            "format": fmt, "notes": "", "tags": "", "color": ""
        }
        if not any(m["path"] == path for m in self._media):
            self._media.append(item)
            self.save()
            return True
        return False

    def scan_directory(self, directory):
        added = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.iso', '.img', '.qcow2', '.raw', '.vdi', '.vmdk')):
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
                if file.lower().endswith(('.qcow2', '.raw', '.vdi', '.vmdk', '.img')):
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