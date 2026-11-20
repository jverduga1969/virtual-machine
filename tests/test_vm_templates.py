"""Plantillas de VM: guardar, reutilizar y borrar."""

from services.vm_templates import TemplateManager


def _manager(tmp_path):
    return TemplateManager(tmp_path / "data")


def test_guardar_y_listar_plantillas(tmp_path):
    mgr = _manager(tmp_path)
    vm = {"id": "vm1", "name": "Ubuntu", "state": "Running", "cores": 4,
          "ram": 4096, "firmware_idx": 1, "disk_path": "/vms/ubuntu/disco.qcow2",
          "notes": "privado", "qmp_socket": "/tmp/qmp.sock"}

    plantilla = mgr.save_template("Dev Linux", vm, icon="🐧", description=" Para programar ")

    assert plantilla["name"] == "Dev Linux"
    assert plantilla["icon"] == "🐧"
    assert plantilla["description"] == "Para programar"
    config = plantilla["config"]
    assert config["cores"] == 4
    assert config["ram"] == 4096
    assert "id" not in config
    assert "name" not in config
    assert "state" not in config
    assert "disk_path" not in config
    assert "notes" not in config
    assert "qmp_socket" not in config
    assert mgr.get_template(plantilla["id"])["name"] == "Dev Linux"


def test_guardar_mismo_nombre_actualiza_en_lugar_de_duplicar(tmp_path):
    mgr = _manager(tmp_path)
    vm = {"id": "vm1", "name": "Ubuntu", "cores": 2}

    primera = mgr.save_template("Ofimática", vm)
    segunda = mgr.save_template("ofimatica", {"id": "vm2", "name": "Ubuntu", "cores": 8})

    assert primera["id"] == segunda["id"]
    assert len(mgr.list_templates()) == 1
    assert mgr.list_templates()[0]["config"]["cores"] == 8


def test_crear_vm_desde_plantilla_genera_id_y_nombre_nuevos(tmp_path):
    mgr = _manager(tmp_path)
    vm = {"id": "vm1", "name": "Ubuntu", "state": "Running", "cores": 4,
          "ram": 4096, "disk_size": "60G", "disk_path": "/vms/vm1/disco.qcow2"}
    plantilla = mgr.save_template("Base", vm)

    config = mgr.create_vm_config(plantilla["id"], "Mi nueva VM", "/vms/nuevo/disco.qcow2")

    assert config["id"] != vm["id"]
    assert config["name"] == "Mi nueva VM"
    assert config["state"] == "Apagada"
    assert config["disk_path"] == "/vms/nuevo/disco.qcow2"
    assert config["cores"] == 4
    assert config["disk_size"] == "60G"


def test_crear_vm_sin_nombre_usa_uno_por_defecto(tmp_path):
    mgr = _manager(tmp_path)
    plantilla = mgr.save_template("Servidor", {"id": "vm1", "name": "Vieja"})

    config = mgr.create_vm_config(plantilla["id"], "   ")

    assert config["name"] == "VM desde Servidor"
    assert config["disk_path"] == ""


def test_borrar_plantilla(tmp_path):
    mgr = _manager(tmp_path)
    plantilla = mgr.save_template("Temporal", {"id": "vm1", "name": "Ubuntu"})

    assert mgr.delete_template(plantilla["id"]) is True
    assert mgr.list_templates() == []
    assert mgr.delete_template(plantilla["id"]) is False


def test_plantilla_inexistente_lanza_keyerror(tmp_path):
    mgr = _manager(tmp_path)
    try:
        mgr.create_vm_config("no-existe", "VM")
    except KeyError:
        pass
    else:
        raise AssertionError("Debe fallar si la plantilla no existe")


def test_json_corrupto_se_pone_en_cuarentena(tmp_path):
    directorio = tmp_path / "data"
    directorio.mkdir()
    archivo = directorio / "templates.json"
    archivo.write_text("[ roto", encoding="utf-8")

    mgr = TemplateManager(directorio)

    assert mgr.list_templates() == []
    assert any("corrupt-" in p.name for p in directorio.iterdir())


def test_dialogos_de_plantillas(qapp, tmp_path):
    from ui_widgets.vm_template_dialogs import SaveTemplateDialog, TemplatePickerDialog

    mgr = _manager(tmp_path)
    mgr.save_template("Dev", {"id": "vm1", "name": "Ubuntu", "cores": 4})

    guardar = SaveTemplateDialog({"name": "Ubuntu"})
    assert guardar.template_name == "Ubuntu — plantilla"
    guardar.input_name.setText("Otra")
    assert guardar.template_name == "Otra"
    guardar.close()

    elegir = TemplatePickerDialog(mgr)
    assert elegir.lista.count() == 1
    assert elegir.selected_id is not None
    elegir.close()
