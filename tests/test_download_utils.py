"""Hashing oportunista de descargas (Fase 1)."""

import hashlib

import pytest

from services.download_utils import (
    HashMismatch,
    HashTracker,
    expected_hash,
    save_checksum,
)


def test_expected_hash_acepta_sufijos_y_normaliza():
    digest = "A" * 64
    assert expected_hash({"sha256_hash": f"  {digest}  "}) == ("sha256", digest.lower())
    assert expected_hash({"sha512": "b" * 128}) == ("sha512", "b" * 128)
    assert expected_hash({"md5": "c" * 32}) == ("md5", "c" * 32)
    assert expected_hash({"name": "sin hash"}) == (None, None)
    assert expected_hash(None) == (None, None)


def test_hash_tracker_verifica_hash_correcto():
    payload = b"contenido de prueba"
    esperado = hashlib.sha256(payload).hexdigest()
    tracker = HashTracker("sha256", esperado)
    tracker.update(payload[:5])
    tracker.update(payload[5:])

    assert tracker.verify() == esperado


def test_hash_tracker_rechaza_hash_distinto():
    tracker = HashTracker("sha256", "0" * 64)
    tracker.update(b"otro contenido")

    with pytest.raises(HashMismatch, match="no coincide"):
        tracker.verify()


def test_hash_tracker_sin_esperado_solo_calcula():
    tracker = HashTracker()  # algoritmo desconocido cae a sha256
    assert tracker.algo == "sha256"
    tracker.update(b"abc")
    assert tracker.verify() == hashlib.sha256(b"abc").hexdigest()


def test_save_checksum_escribe_sidecar_y_tolera_fallo(tmp_path):
    iso = tmp_path / "imagen.iso"
    digest = "d" * 64

    sidecar = save_checksum(iso, digest)

    assert sidecar == tmp_path / "imagen.iso.sha256"
    assert sidecar.read_text(encoding="utf-8") == f"{digest}  imagen.iso\n"

    # Un directorio como destino fuerza OSError: la descarga no debe fallar.
    assert save_checksum(tmp_path / "directorio" / "no.iso", digest) is None
