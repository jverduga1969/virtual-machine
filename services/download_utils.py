"""Utilidades compartidas para verificar la integridad de las descargas.

Ningún catálogo de la app publica todavía un hash conocido, así que el
comportamiento es *oportunista*: siempre calculamos SHA-256 (para poder
guardarlo y que el usuario pueda comprobarlo) y solo rechazamos el archivo
cuando la fuente aporta un hash esperado.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

HASH_KEYS = ("sha256", "sha512", "md5")


class HashMismatch(ValueError):
    """El archivo descargado no coincide con el hash anunciado."""


def expected_hash(source: Any) -> tuple[Optional[str], Optional[str]]:
    """Extrae ``(algoritmo, hexdigest)`` de un dict de VM/fuente.

    Acepta tanto ``sha256`` como ``sha256_hash`` y tolera espacios/mayúsculas.
    """
    if not isinstance(source, dict):
        return None, None
    for algo in HASH_KEYS:
        for key in (algo, f"{algo}_hash"):
            value = source.get(key)
            if value:
                digest = str(value).strip().lower().replace(" ", "")
                return algo, digest
    return None, None


class HashTracker:
    """Acumula el hash de un stream mientras se escriben sus chunks."""

    def __init__(self, algo: str = "sha256", expected: Optional[str] = None):
        self.algo = algo if algo in HASH_KEYS else "sha256"
        self.expected = (expected or "").strip().lower().replace(" ", "") or None
        self._hash = hashlib.new(self.algo)

    def update(self, chunk: bytes) -> None:
        if chunk:
            self._hash.update(chunk)

    @property
    def hexdigest(self) -> str:
        return self._hash.hexdigest()

    def verify(self) -> str:
        """Devuelve el hash calculado o lanza ``HashMismatch``."""
        actual = self.hexdigest
        if self.expected and actual != self.expected:
            raise HashMismatch(
                f"El hash {self.algo} no coincide: "
                f"esperado {self.expected}, obtenido {actual}")
        return actual


def save_checksum(path, digest: str, algo: str = "sha256") -> Optional[Path]:
    """Guarda un sidecar ``<archivo>.sha256`` estilo sha256sum.

    Un fallo al escribir el sidecar no invalida una descarga correcta.
    """
    target = Path(path)
    sidecar = target.with_name(f"{target.name}.{algo}")
    try:
        sidecar.write_text(f"{digest}  {target.name}\n", encoding="utf-8")
        return sidecar
    except OSError as e:
        log.warning("No se pudo guardar %s: %s", sidecar, e)
        return None
