"""El monitor de recursos del host también funciona en Windows."""

import sys
import types

import ui_widgets.resource_monitor as rm


def test_host_windows_usa_psutil(qapp, monkeypatch):
    fake = types.ModuleType("psutil")
    fake.cpu_percent = lambda interval=None: 42.0
    fake.virtual_memory = lambda: types.SimpleNamespace(
        total=16 * 1024 ** 3, percent=63.0)
    fake.boot_time = lambda: 1000.0
    fake.net_io_counters = lambda: types.SimpleNamespace(
        bytes_sent=1024 * 1024, bytes_recv=2 * 1024 * 1024)
    fake.disk_io_counters = lambda: types.SimpleNamespace(
        read_bytes=4 * 1024 * 1024, write_bytes=6 * 1024 * 1024)
    monkeypatch.setitem(sys.modules, "psutil", fake)
    monkeypatch.setattr(rm, "IS_WINDOWS", True)
    monkeypatch.setattr(rm.time, "time", lambda: 1005.0)

    monitor = rm.ResourceMonitor(app=None)
    try:
        assert "16.0 GB" in monitor.lbl_host_ram_total.text()

        monitor._update_host_stats()

        assert monitor.graph_host_cpu.current_val == 42.0
        assert monitor.graph_host_ram.current_val == 63.0
        assert "0h 0m 5s" in monitor.lbl_host_uptime.text()
        assert monitor.lbl_host_load.text()

        # Segunda lectura con 1 s más: red y disco dan MB/s reales.
        monkeypatch.setattr(rm.time, "time", lambda: 1006.0)
        fake.net_io_counters = lambda: types.SimpleNamespace(
            bytes_sent=2 * 1024 * 1024, bytes_recv=4 * 1024 * 1024)
        fake.disk_io_counters = lambda: types.SimpleNamespace(
            read_bytes=8 * 1024 * 1024, write_bytes=12 * 1024 * 1024)
        monitor._update_host_stats()

        assert monitor.graph_host_net.current_val == 3.0
        assert monitor.graph_host_dsk.current_val == 10.0
    finally:
        monitor.timer.stop()
