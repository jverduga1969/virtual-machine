"""Historial de configuración de VMs: se puede consultar y deshacer."""

from services.vm_repository import MAX_HISTORY, VMRepository


def _repo(tmp_path):
    return VMRepository(tmp_path / "data")


def test_cada_cambio_de_configuracion_crea_una_version(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu", "cores": 2, "ram": 2048, "state": "Apagada"})

    repo.update("vm1", {"cores": 4})
    repo.update("vm1", {"ram": 4096})

    historial = repo.get_history("vm1")
    assert len(historial) == 3  # creación + dos cambios
    assert [h["reason"] for h in historial] == [
        "Cambio de configuración", "Cambio de configuración", "VM creada"]
    assert historial[-1]["vm"]["cores"] == 2
    assert historial[0]["vm"]["ram"] == 4096


def test_cambios_de_estado_no_generan_historial(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu", "state": "Apagada",
              "qmp_socket": "/tmp/viejo.sock", "vnc_port": 5900})

    for estado in ("Running", "Apagada", "Paused"):
        repo.update("vm1", {"state": estado, "qmp_socket": "/tmp/nuevo.sock"})

    assert len(repo.get_history("vm1")) == 1
    assert repo.get("vm1")["state"] == "Paused"
    assert repo.get("vm1")["qmp_socket"] == "/tmp/nuevo.sock"


def test_restarar_guarda_la_configuracion_actual_para_poder_deshacer(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu", "cores": 2, "ram": 2048,
              "state": "Running", "vnc_port": 5900})
    repo.update("vm1", {"cores": 8, "ram": 8192})

    # versión 0 = la mas reciente (cores=8), versión 1 = la original (cores=2)
    assert repo.restore("vm1", 1) is True

    vm = repo.get("vm1")
    assert vm["cores"] == 2
    assert vm["ram"] == 2048
    # Los datos de ejecución no se revierten.
    assert vm["state"] == "Running"
    assert vm["vnc_port"] == 5900

    razones = [h["reason"] for h in repo.get_history("vm1")]
    assert razones[0].startswith("Restaurada")
    assert "Antes de restaurar" in razones

    # Deshacer la restauración devuelve la configuración de 8 núcleos.
    assert repo.restore("vm1", 1) is True
    assert repo.get("vm1")["cores"] == 8


def test_restaurar_indice_invalido_no_hace_nada(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu"})
    antes = len(repo.get_history("vm1"))

    assert repo.restore("vm1", 99) is False
    assert repo.restore("vm1", -1) is False
    assert len(repo.get_history("vm1")) == antes


def test_eliminar_vm_conserva_su_ultima_configuracion(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu", "cores": 4})
    repo.update("vm1", {"name": "Ubuntu Server"})

    assert repo.delete("vm1") is True
    assert repo.get("vm1") is None

    historial = repo.get_history("vm1")
    assert historial[0]["reason"] == "VM eliminada"
    assert historial[0]["vm"]["name"] == "Ubuntu Server"


def test_historial_esta_limitado(tmp_path):
    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu"})
    for n in range(MAX_HISTORY + 10):
        repo.update("vm1", {"name": f"Ubuntu {n}"})

    assert len(repo.get_history("vm1")) == MAX_HISTORY
    assert repo.get_history("vm1")[0]["vm"]["name"] == f"Ubuntu {MAX_HISTORY + 9}"


def test_historial_corrupto_se_pone_en_cuarentena(tmp_path):
    repo = _repo(tmp_path)
    archivo = tmp_path / "data" / "history" / "vm1.json"
    archivo.write_text("{ json roto", encoding="utf-8")

    assert repo.get_history("vm1") == []
    assert any("corrupt-" in p.name for p in archivo.parent.iterdir())


def test_dialogo_historial_lista_versiones(qapp, tmp_path):
    from ui_widgets.vm_history_dialog import VMHistoryDialog

    repo = _repo(tmp_path)
    repo.add({"id": "vm1", "name": "Ubuntu", "cores": 2})
    repo.update("vm1", {"cores": 4})

    dlg = VMHistoryDialog(repo, "vm1")

    assert dlg.windowTitle() == "Historial de Ubuntu"
    assert dlg.tabla.rowCount() == 2
    assert "Cambio de configuración" in dlg.tabla.item(0, 2).text()
    dlg.close()
