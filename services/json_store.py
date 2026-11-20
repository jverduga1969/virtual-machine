"""Persistencia JSON segura para los archivos de configuración de la app.

Los archivos se escriben siempre en dos pasos (temporal + ``os.replace``)
para que un corte de luz o un hilo que muera a mitad de escritura no deje
el JSON a medias. Además, un archivo corrupto se pone en cuarentena en vez
de sobrescribirse sin más: así no se pierden las VMs del usuario.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    """Devuelve el JSON parseado o ``default`` si no se puede leer."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def quarantine(path: Path) -> Path | None:
    """Renombra un archivo corrupto para poder diagnosticarlo después."""
    path = Path(path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = path.with_name(f"{path.name}.corrupt-{stamp}")
    try:
        os.replace(path, dest)
        return dest
    except OSError:
        return None


def atomic_write_json(path: Path, data: Any, *, indent: int = 4) -> None:
    """Escribe ``data`` en ``path`` de forma atómica y sincronizada."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # En Windows os.replace() funciona incluso si el destino ya existe.
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
