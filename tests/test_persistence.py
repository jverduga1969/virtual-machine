"""Repositorio de VMs y biblioteca de medios con concurrency y cuarentena."""

import json
from concurrent.futures import ThreadPoolExecutor

from services.media_library import MediaLibraryManager
from services.vm_repository import VMRepository


class _Settings:
    """QSettings mínimo para comprobar el parámetro opcional del manager."""

    def __init__(self, media_dir):
        self.media_dir = str(media_dir)

    def value(self, key, default=""):
        return self.media_dir if key == "paths/media_dir" else default


def test_vm_repository_crud(tmp_path):
    repo = VMRepository(tmp_path)
    repo.add({"id": "vm1", "name": "Prueba", "state": "Apagada"})
    repo.update("vm1", {"state": "Running"})

    assert repo.get("vm1")["state"] == "Running"
    assert repo.db_file.read_text(encoding="utf-8").count('"vm1"') == 1

    repo.delete("vm1")
    assert repo.get("vm1") is None
    assert json.loads(repo.db_file.read_text(encoding="utf-8")) == []


def test_get_all_devuelve_copia(tmp_path):
    repo = VMRepository(tmp_path)
    repo.add({"id": "vm1", "name": "Original"})

    copia = repo.get_all()
    copia.clear()

    assert [vm["id"] for vm in repo.get_all()] == ["vm1"]


def test_vm_repository_escribe_cuarentena_si_json_esta_corrupto(tmp_path):
    repo = VMRepository(tmp_path)
    repo.add({"id": "vm1", "name": "Antes de romper"})
    repo.db_file.write_text('{"roto":', encoding="utf-8")

    reiniciado = VMRepository(tmp_path)

    assert reiniciado.get_all() == []
    copias = list(tmp_path.glob("vms.json.corrupt-*"))
    assert len(copias) == 1
    assert "roto" in copias[0].read_text(encoding="utf-8")


def test_vm_repository_soporta_escrituras_concurrentes(tmp_path):
    repo = VMRepository(tmp_path)
    repo.add({"id": "vm1", "name": "Concurrente"})

    def actualizar(i):
        repo.update("vm1", {f"clave_{i}": i})

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(actualizar, range(25)))

    en_memoria = repo.get("vm1")
    en_disco = json.loads(repo.db_file.read_text(encoding="utf-8"))[0]
    for i in range(25):
        assert en_memoria[f"clave_{i}"] == i
        assert en_disco[f"clave_{i}"] == i


def test_media_library_usa_settings_y_hace_cuarentena(tmp_path):
    media_dir = tmp_path / "MisMedios"
    settings = _Settings(media_dir)

    media = MediaLibraryManager(tmp_path, settings)
    assert media.media_dir == media_dir
    assert media.add_media("iso", str(tmp_path / "no-existe.iso"), "ISO", "-")
    assert len(media.get_all()) == 1

    media.db_file.write_text("[1, 2", encoding="utf-8")
    reiniciada = MediaLibraryManager(tmp_path, settings)

    assert reiniciada.get_all() == []
    assert list(tmp_path.glob("media_library.json.corrupt-*"))
