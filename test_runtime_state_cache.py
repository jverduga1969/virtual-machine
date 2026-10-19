# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Tests de la cache de estado de VM (marcador rendimiento_v1).

Un QMP falso (socket Unix en un hilo) permite contar conexiones y cambiar
el estado. Ejecutar con:  QT_QPA_PLATFORM=offscreen python3 -m unittest test_runtime_state_cache -v
"""

import json
import os
import socket
import tempfile
import threading
import time
import unittest
from unittest import mock

import vm_config
from vm_lifecycle_mixin import VmLifecycleMixin


class FakeQmp:
    def __init__(self, path):
        self.status = "running"
        self.connections = 0
        self.commands = []
        self._s = socket.socket(socket.AF_UNIX)
        self._s.bind(path)
        self._s.listen(8)
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                c, _ = self._s.accept()
            except OSError:
                return
            self.connections += 1
            threading.Thread(target=self._handle, args=(c,), daemon=True).start()

    def _handle(self, c):
        try:
            c.sendall(b'{"QMP":{}}\r\n')
            buf = b""
            while True:
                chunk = c.recv(4096)
                if not chunk:
                    return
                buf += chunk
                while b"\r\n" in buf:
                    line, buf = buf.split(b"\r\n", 1)
                    if not line:
                        continue
                    req = json.loads(line)
                    ex = req["execute"]
                    self.commands.append(ex)
                    if ex == "stop":
                        self.status = "paused"
                    elif ex == "cont":
                        self.status = "running"
                    ret = {"status": self.status} if ex == "query-status" else {}
                    c.sendall((json.dumps({"return": ret, "id": req.get("id")}) + "\r\n").encode())
        finally:
            c.close()

    def close(self):
        self._s.close()


class Host(VmLifecycleMixin):
    pass


class RuntimeStateCacheTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(vm_config, "BASE_VM_DIR", self.tmp.name)
        p.start()
        self.addCleanup(p.stop)
        self.vm_dir = os.path.join(self.tmp.name, "vm1")
        os.makedirs(self.vm_dir)
        with open(os.path.join(self.vm_dir, "qemu.pid"), "w") as f:
            f.write(str(os.getpid()))
        self.qmp = FakeQmp(os.path.join(self.vm_dir, "qemu.qmp"))
        self.addCleanup(self.qmp.close)
        self.h = Host()

    def test_llamadas_seguidas_hacen_una_sola_consulta(self):
        for _ in range(6):
            self.assertEqual(self.h._runtime_state("vm1"), "running")
        self.assertEqual(self.qmp.connections, 1)

    def test_la_cache_caduca(self):
        self.h._runtime_state("vm1")
        key = "vm1"
        pid, ts, st = self.h._runtime_qmp_cache[key]
        self.h._runtime_qmp_cache[key] = (pid, ts - 2.0, st)  # simular 2 s despues
        self.h._runtime_state("vm1")
        self.assertEqual(self.qmp.connections, 2)

    def test_pausar_invalida_y_se_ve_el_cambio_al_instante(self):
        self.assertEqual(self.h._runtime_state("vm1"), "running")
        self.h._qmp_command(self.vm_dir, {"execute": "stop"})
        self.assertEqual(self.h._runtime_state("vm1"), "paused")
        self.h._qmp_command(self.vm_dir, {"execute": "cont"})
        self.assertEqual(self.h._runtime_state("vm1"), "running")

    def test_los_comandos_query_no_invalidan(self):
        self.h._runtime_state("vm1")
        self.h._qmp_command(self.vm_dir, {"execute": "query-status"})
        self.assertIn("vm1", self.h._runtime_qmp_cache)

    def test_proceso_muerto_es_stopped_sin_esperar_al_ttl(self):
        self.assertEqual(self.h._runtime_state("vm1"), "running")
        with open(os.path.join(self.vm_dir, "qemu.pid"), "w") as f:
            f.write("2999999")  # pid inexistente
        self.assertEqual(self.h._runtime_state("vm1"), "stopped")

    def test_pid_distinto_no_reutiliza_la_cache(self):
        self.h._runtime_state("vm1")
        pid, ts, _ = self.h._runtime_qmp_cache["vm1"]
        self.h._runtime_qmp_cache["vm1"] = (pid + 1, ts, "paused")  # cache de otro proceso
        self.assertEqual(self.h._runtime_state("vm1"), "running")

    def test_fallo_de_qmp_se_cachea_y_devuelve_running(self):
        self.qmp.close()
        os.unlink(os.path.join(self.vm_dir, "qemu.qmp"))
        t = time.monotonic()
        for _ in range(4):
            self.assertEqual(self.h._runtime_state("vm1"), "running")
        self.assertLess(time.monotonic() - t, 1.0)


if __name__ == "__main__":
    unittest.main()
