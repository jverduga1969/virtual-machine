"""Semáforo de RAM/vCPU en la configuración de la VM.

Verde = margen seguro, amarillo = cabe en lo libre ahora (o habrá swap),
rojo = excede la capacidad física del host.
"""

from PyQt6.QtWidgets import QLabel, QSlider

from plugins.config_vm.plugin import (
    COLOR_BAD,
    COLOR_OK,
    COLOR_WARN,
    Plugin,
)


CAP = {
    "total_ram_mb": 16384,       # 16 GB
    "available_ram_mb": 14336,   # 14 GB libres ahora
    "safe_ram_mb": 12288,        # 12 GB con margen
    "reserve_ram_mb": 4096,
    "total_cores": 8,
    "free_cores": 7,
    "safe_cores": 6,
    "reserve_cores": 2,
}


def test_semaforo_ram():
    assert Plugin._capacity_status("ram", 12, CAP)[0] == COLOR_OK
    assert Plugin._capacity_status("ram", 13, CAP)[0] == COLOR_WARN
    assert "libre actual" in Plugin._capacity_status("ram", 13, CAP)[1]
    assert Plugin._capacity_status("ram", 15, CAP)[0] == COLOR_WARN
    assert "swap" in Plugin._capacity_status("ram", 15, CAP)[1]
    assert Plugin._capacity_status("ram", 17, CAP)[0] == COLOR_BAD
    assert "overcommit" in Plugin._capacity_status("ram", 17, CAP)[1]


def test_semaforo_cpu():
    assert Plugin._capacity_status("cpu", 6, CAP)[0] == COLOR_OK
    assert Plugin._capacity_status("cpu", 7, CAP)[0] == COLOR_WARN
    assert "libres ahora" in Plugin._capacity_status("cpu", 7, CAP)[1]
    assert Plugin._capacity_status("cpu", 8, CAP)[0] == COLOR_WARN
    assert "solo 7" in Plugin._capacity_status("cpu", 8, CAP)[1]
    assert Plugin._capacity_status("cpu", 9, CAP)[0] == COLOR_BAD


def test_indicadores_se_actualizan(qapp, monkeypatch):
    plugin = object.__new__(Plugin)
    plugin.slider_ram = QSlider()
    plugin.slider_ram.setValue(17)
    plugin.slider_cores = QSlider()
    plugin.slider_cores.setValue(9)
    plugin.lbl_ram_status = QLabel()
    plugin.lbl_cores_status = QLabel()
    monkeypatch.setattr(plugin, "_host_capacity", lambda: CAP)

    plugin._refresh_capacity_status()

    assert plugin.lbl_ram_status.text().startswith("●")
    assert COLOR_BAD in plugin.lbl_ram_status.styleSheet()
    assert "overcommit" in plugin.lbl_ram_status.toolTip()
    assert COLOR_BAD in plugin.lbl_cores_status.styleSheet()
    assert "núcleos lógicos" in plugin.lbl_cores_status.toolTip()


def test_indicadores_verdes_con_valores_seguros(qapp, monkeypatch):
    plugin = object.__new__(Plugin)
    plugin.slider_ram = QSlider()
    plugin.slider_ram.setValue(8)
    plugin.slider_cores = QSlider()
    plugin.slider_cores.setValue(4)
    plugin.lbl_ram_status = QLabel()
    plugin.lbl_cores_status = QLabel()
    monkeypatch.setattr(plugin, "_host_capacity", lambda: CAP)

    plugin._refresh_capacity_status()

    assert COLOR_OK in plugin.lbl_ram_status.styleSheet()
    assert COLOR_OK in plugin.lbl_cores_status.styleSheet()
    assert "Margen seguro" in plugin.lbl_ram_status.text()
