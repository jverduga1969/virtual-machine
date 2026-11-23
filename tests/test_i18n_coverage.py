"""Auditoría de cobertura: toda clave usada con tr() existe en los 5 idiomas."""

import ast
from pathlib import Path

import pytest

from core import i18n
from conftest import ROOT

IDIOMAS = ["English", "Português (BR)", "Deutsch", "Français", "Italiano"]


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            parte.value if isinstance(parte, ast.Constant) else "{}"
            for parte in node.values
        )
    return None


def _claves_tr():
    claves = {}
    for archivo in ROOT.glob("**/*.py"):
        if "venv" in archivo.parts or "__pycache__" in archivo.parts:
            continue
        try:
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call) or not nodo.args:
                continue
            func = nodo.func
            nombre = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if nombre != "tr":
                continue
            texto = _literal(nodo.args[0])
            if texto and len(texto) > 3:
                claves.setdefault(texto, f"{archivo.relative_to(ROOT)}:{nodo.lineno}")
    return claves


@pytest.mark.parametrize("idioma", IDIOMAS)
def test_todas_las_claves_tr_estan_traducidas(idioma):
    catalogo = i18n.load_translations(i18n.code_for(idioma))
    ausentes = {clave: origen for clave, origen in _claves_tr().items()
                if clave not in catalogo}
    assert not ausentes, f"{idioma}: faltan {len(ausentes)} claves: {ausentes}"


@pytest.mark.parametrize("idioma", IDIOMAS)
def test_mensajes_dinamicos_del_semaforo_estan_traducidos(idioma, monkeypatch):
    # monkeypatch restaura el idioma anterior al terminar, para no afectar a
    # otros tests que ejecutan la interfaz en español.
    monkeypatch.setattr(
        i18n, "_current", i18n.load_translations(i18n.code_for(idioma)))
    from plugins.config_vm.plugin import Plugin

    casos = (
        (Plugin._capacity_status("ram", 17, {
            "total_ram_mb": 16384, "available_ram_mb": 14336,
            "safe_ram_mb": 12288, "reserve_ram_mb": 4096}),
         "Excede la RAM física ({} GB > {} GB): overcommit"),
        (Plugin._capacity_status("ram", 8, {
            "total_ram_mb": 16384, "available_ram_mb": 14336,
            "safe_ram_mb": 12288, "reserve_ram_mb": 4096}),
         "Margen seguro: deja {} GB para el host"),
        (Plugin._capacity_status("cpu", 9, {
            "total_cores": 8, "free_cores": 7, "safe_cores": 6,
            "reserve_cores": 2}),
         "Excede los {} núcleos lógicos del host"),
    )
    for (_, mensaje), clave in casos:
        assert mensaje != clave
        assert "{}" not in mensaje
