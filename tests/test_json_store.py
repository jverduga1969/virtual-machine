"""Persistencia atómica y cuarentena de JSON corrupto (Fase 1)."""

import json

from services.json_store import atomic_write_json, quarantine, read_json


def test_read_json_devuelve_default_si_falta_o_esta_corrupto(tmp_path):
    assert read_json(tmp_path / "no-existe.json", ["vacio"]) == ["vacio"]

    corrupto = tmp_path / "roto.json"
    corrupto.write_text('{"roto":', encoding="utf-8")
    assert read_json(corrupto, "fallback") == "fallback"


def test_atomic_write_json_crea_padres_y_no_deja_temporales(tmp_path):
    destino = tmp_path / "sub" / "vms.json"
    datos = [{"id": "vm1", "name": "Prueba üñí"}]

    atomic_write_json(destino, datos)

    assert json.loads(destino.read_text(encoding="utf-8")) == datos
    assert not list(destino.parent.glob("*.tmp"))
    assert not list(destino.parent.glob(".*.tmp"))


def test_quarantine_conserva_el_contenido_para_diagnosticar(tmp_path):
    corrupto = tmp_path / "vms.json"
    corrupto.write_text("contenido a medias", encoding="utf-8")

    copia = quarantine(corrupto)

    assert copia is not None and copia.exists()
    assert ".corrupt-" in copia.name
    assert copia.read_text(encoding="utf-8") == "contenido a medias"
    assert not corrupto.exists()
