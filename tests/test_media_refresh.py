"""El botón Refrescar sincroniza la biblioteca de medios con el disco."""

import json

from services.media_library import MediaLibraryManager


class _Settings:
    def __init__(self, media_dir):
        self.media_dir = str(media_dir)

    def value(self, key, default=""):
        return self.media_dir if key == "paths/media_dir" else default


def _manager(tmp_path):
    media_dir = tmp_path / "MediaLibrary"
    media_dir.mkdir()
    return MediaLibraryManager(tmp_path, _Settings(media_dir)), media_dir


def test_refrescar_quita_medios_cuyo_archivo_ya_no_existe(tmp_path):
    manager, media_dir = _manager(tmp_path)
    vivo = media_dir / "vivo.iso"
    vivo.write_bytes(b"iso")
    manager.add_media("vivo", vivo, "ISO", "-", fmt="ISO")

    borrado = media_dir / "borrado.qcow2"
    borrado.write_bytes(b"disco")
    manager.add_media("borrado", borrado, "Disco duro", "-", fmt="QCOW2")
    borrado.unlink()

    resultado = manager.reconcile()

    assert resultado["removed"] == 1
    assert [m["path"] for m in manager.get_all()] == [str(vivo)]
    assert len(json.loads(manager.db_file.read_text(encoding="utf-8"))) == 1


def test_refrescar_anade_medios_nuevos_y_no_duplica(tmp_path):
    manager, media_dir = _manager(tmp_path)
    (media_dir / "en_biblioteca.qcow2").write_bytes(b"disco")

    isos_dir = tmp_path / "isos"
    isos_dir.mkdir()
    (isos_dir / "descargada.iso").write_bytes(b"iso")

    primero = manager.reconcile(extra_dirs=[isos_dir])
    nombres = {m["name"] for m in manager.get_all()}

    assert primero["added"] == 2
    assert nombres == {"en_biblioteca.qcow2", "descargada.iso"}
    assert {m["format"] for m in manager.get_all()} == {"QCOW2", "ISO"}

    segundo = manager.reconcile(extra_dirs=[isos_dir])
    assert (segundo["added"], segundo["removed"]) == (0, 0)
    assert len(manager.get_all()) == 2


def test_refrescar_conserva_medios_de_rutas_externas(tmp_path):
    manager, media_dir = _manager(tmp_path)
    externo = tmp_path / "otro" / "disco.raw"
    externo.parent.mkdir()
    externo.write_bytes(b"raw")
    manager.add_media("externo", externo, "Disco duro", "-", fmt="RAW")

    manager.reconcile()

    assert [m["path"] for m in manager.get_all()] == [str(externo)]


def test_refrescar_actualiza_estado_si_el_archivo_reaparece(tmp_path):
    manager, media_dir = _manager(tmp_path)
    archivo = media_dir / "temporal.img"
    manager.add_media("temporal", archivo, "ISO", "-", fmt="IMG")

    assert manager.get_all()[0]["status"] == "huérfano"
    archivo.write_bytes(b"img de nuevo")

    resultado = manager.reconcile()

    assert resultado["removed"] == 0
    assert resultado["updated"] >= 1
    assert manager.get_all()[0]["status"] == "OK"


def test_usada_por_refleja_las_vms_que_usan_cada_medio(tmp_path):
    manager, media_dir = _manager(tmp_path)
    disco = media_dir / "disco.qcow2"
    iso = media_dir / "instalador.iso"
    disco.write_bytes(b"disco")
    iso.write_bytes(b"iso")
    manager.add_media("disco", disco, "Disco duro", "-", fmt="QCOW2")
    manager.add_media("instalador", iso, "ISO", "-", fmt="ISO")

    vms = [{
        "id": "vm1", "name": "Ubuntu",
        "disk_path": str(disco),
        "optical_drives": [{"path": str(iso)}],
    }]
    manager.sync_usage(vms)

    por_path = {m["path"]: m["used_by"] for m in manager.get_all()}
    assert por_path[str(disco)] == "Ubuntu"
    assert por_path[str(iso)] == "Ubuntu"

    # Si la VM deja de usar la ISO, la columna vuelve a '-'.
    manager.sync_usage([{"id": "vm1", "name": "Ubuntu", "disk_path": str(disco)}])
    por_path = {m["path"]: m["used_by"] for m in manager.get_all()}
    assert por_path[str(disco)] == "Ubuntu"
    assert por_path[str(iso)] == "-"


def test_usada_por_agrupa_varias_vms_y_lee_boot_order(tmp_path):
    manager, media_dir = _manager(tmp_path)
    imagen = media_dir / "tools.img"
    imagen.write_bytes(b"img")
    manager.add_media("tools", imagen, "ISO", "-", fmt="IMG")

    vms = [
        {"id": "vm2", "name": "Zeta", "floppy_path": str(imagen)},
        {"id": "vm1", "name": "Alfa",
         "boot_order": [f"Unidad óptica — {imagen}"]},
    ]

    manager.sync_usage(vms)

    assert manager.get_all()[0]["used_by"] == "Alfa, Zeta"
