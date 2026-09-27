# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

r"""Tests unitarios de console_backend.py.

Módulo puro (sin PyQt, sin GTK): todo lo testeable aquí se puede ejecutar
en cualquier entorno, incluso sin QEMU instalado.

Ejecutar solo estos:
    python3 -m unittest test_console_backend -v
Ejecutar toda la suite del proyecto:
    ./run_tests.sh
"""
import os
import sys
import unittest
from unittest import mock

import console_backend as cb


class ConstantsTests(unittest.TestCase):
    def test_protocols(self):
        self.assertEqual(cb.PROTOCOL_VNC, "vnc")
        self.assertEqual(cb.PROTOCOL_SPICE, "spice")
        self.assertIn(cb.PROTOCOL_VNC, cb.ALL_PROTOCOLS)
        self.assertIn(cb.PROTOCOL_SPICE, cb.ALL_PROTOCOLS)

    def test_modes(self):
        for m in ("embedded", "external", "native", "hybrid"):
            self.assertIn(m, cb.ALL_MODES)
        self.assertEqual(cb.MODE_HYBRID, "hybrid")

    def test_defaults(self):
        self.assertEqual(cb.DEFAULT_PROTOCOL, cb.PROTOCOL_VNC)
        self.assertEqual(cb.DEFAULT_MODE, cb.MODE_EMBEDDED)


class SocketPathTests(unittest.TestCase):
    def test_vnc_socket_path(self):
        path = cb.vnc_socket_path("/tmp/vm-x")
        self.assertTrue(path.endswith("qemu.vnc.sock"))
        self.assertTrue(path.startswith("/tmp/vm-x"))

    def test_spice_socket_path(self):
        path = cb.spice_socket_path("/tmp/vm-x")
        self.assertTrue(path.endswith("qemu.spice.sock"))

    def test_socket_path_dispatch(self):
        self.assertIn("vnc", cb.socket_path("/tmp/v", cb.PROTOCOL_VNC))
        self.assertIn("spice", cb.socket_path("/tmp/v", cb.PROTOCOL_SPICE))


class PickFreePortTests(unittest.TestCase):
    def test_returns_int_in_range(self):
        port = cb._pick_free_port()
        if port is not None:
            self.assertGreaterEqual(port, 5930)
            self.assertLessEqual(port, 6199)

    def test_custom_range(self):
        port = cb._pick_free_port(lo=50000, hi=50010)
        if port is not None:
            self.assertGreaterEqual(port, 50000)
            self.assertLessEqual(port, 50010)


class QemuConsoleArgsTests(unittest.TestCase):
    VM_DIR = "/tmp/vmtest-console"

    def test_native_returns_no_args(self):
        args, info = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_VNC, cb.MODE_NATIVE)
        self.assertEqual(args, "")
        self.assertEqual(info["mode"], cb.MODE_NATIVE)

    def test_vnc_embedded_uses_display_none_and_vnc(self):
        args, info = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_VNC, cb.MODE_EMBEDDED)
        self.assertIn("-vnc unix:", args)
        self.assertIn("-display none", args)
        self.assertIn("qemu.vnc.sock", info["socket"])

    def test_spice_embedded_uses_port_and_display_none(self):
        args, info = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_SPICE, cb.MODE_EMBEDDED)
        self.assertIn("-spice port=", args)
        self.assertIn("-display none", args)
        self.assertNotIn("-vnc ", args)
        self.assertIn("port", info)
        self.assertIn("uri", info)
        self.assertTrue(str(info["uri"]).startswith("spice://127.0.0.1:"))

    def test_hybrid_uses_both_vnc_and_spice(self):
        args, info = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_VNC, cb.MODE_HYBRID)
        self.assertIn("-vnc unix:", args)
        self.assertIn("-spice port=", args)
        self.assertIn("vnc_socket", info)
        self.assertIn("port", info)

    def test_external_matches_embedded_for_same_protocol(self):
        a1, i1 = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_SPICE, cb.MODE_EMBEDDED)
        a2, i2 = cb.qemu_console_args(self.VM_DIR, cb.PROTOCOL_SPICE, cb.MODE_EXTERNAL)
        # Mismos args en QEMU: la diferencia es quién se conecta.
        self.assertEqual(a1, a2)


class ConsoleUriTests(unittest.TestCase):
    def test_vnc_returns_path(self):
        self.assertEqual(
            cb.console_uri(cb.PROTOCOL_VNC, "/run/vm.vnc.sock"),
            "/run/vm.vnc.sock",
        )

    def test_spice_with_full_uri(self):
        self.assertEqual(
            cb.console_uri(cb.PROTOCOL_SPICE, "spice://127.0.0.1:5930"),
            "spice://127.0.0.1:5930",
        )

    def test_spice_with_port_string(self):
        self.assertEqual(
            cb.console_uri(cb.PROTOCOL_SPICE, "5930"),
            "spice://127.0.0.1:5930",
        )

    def test_spice_with_socket_path_uses_scheme(self):
        uri = cb.console_uri(cb.PROTOCOL_SPICE, "/run/vm.spice.sock")
        self.assertTrue(uri.startswith("spice+unix://"))
        self.assertIn("/run/vm.spice.sock", uri.replace("%2F", "/"))


class BuildViewerArgsTests(unittest.TestCase):
    def test_substitutes_sock(self):
        out = cb.build_viewer_args(["{sock}"], "/run/vm.vnc.sock", "")
        self.assertEqual(out, ["/run/vm.vnc.sock"])

    def test_substitutes_uri(self):
        out = cb.build_viewer_args(["{uri}"], "", "spice://127.0.0.1:5930")
        self.assertEqual(out, ["spice://127.0.0.1:5930"])

    def test_substitutes_port_and_host(self):
        out = cb.build_viewer_args(
            ["--host={host}", "--port={port}"], "", "", port=5930,
        )
        self.assertEqual(out, ["--host=127.0.0.1", "--port=5930"])

    def test_leaves_port_marker_if_none(self):
        out = cb.build_viewer_args(["--port={port}"], "", "", port=None)
        self.assertEqual(out, ["--port={port}"])


class FindViewerTests(unittest.TestCase):
    def test_vnc_prefers_gvncviewer(self):
        with mock.patch.object(cb.shutil, "which",
                               side_effect=lambda n: f"/usr/bin/{n}" if n == "gvncviewer" else None):
            viewer, tmpl = cb.find_vnc_viewer()
        self.assertEqual(viewer, "/usr/bin/gvncviewer")
        self.assertEqual(tmpl, ["{sock}"])

    def test_vnc_falls_back_to_tigervnc(self):
        def fake_which(n):
            return "/usr/bin/vncviewer" if n == "vncviewer" else None
        with mock.patch.object(cb.shutil, "which", side_effect=fake_which):
            viewer, tmpl = cb.find_vnc_viewer()
        self.assertEqual(viewer, "/usr/bin/vncviewer")

    def test_spice_prefers_spicy_with_port(self):
        with mock.patch.object(cb.shutil, "which",
                               side_effect=lambda n: f"/usr/bin/{n}" if n == "spicy" else None):
            viewer, tmpl = cb.find_spice_viewer()
        self.assertEqual(viewer, "/usr/bin/spicy")
        # spicy no acepta URIs en --host; se pasan host y port separados.
        self.assertIn("--port={port}", tmpl)

    def test_spice_falls_back_to_remote_viewer(self):
        def fake_which(n):
            return "/usr/bin/remote-viewer" if n == "remote-viewer" else None
        with mock.patch.object(cb.shutil, "which", side_effect=fake_which):
            viewer, tmpl = cb.find_spice_viewer()
        self.assertEqual(viewer, "/usr/bin/remote-viewer")
        self.assertEqual(tmpl, ["{uri}"])

    def test_find_viewer_dispatch(self):
        with mock.patch.object(cb, "find_vnc_viewer", return_value=("v", ["{sock}"])):
            self.assertEqual(cb.find_viewer(cb.PROTOCOL_VNC), ("v", ["{sock}"]))
        with mock.patch.object(cb, "find_spice_viewer", return_value=("s", ["{uri}"])):
            self.assertEqual(cb.find_viewer(cb.PROTOCOL_SPICE), ("s", ["{uri}"]))


class DescribeRequirementsTests(unittest.TestCase):
    def test_all_combinations_return_string(self):
        for proto in (cb.PROTOCOL_VNC, cb.PROTOCOL_SPICE):
            for mode in (cb.MODE_EMBEDDED, cb.MODE_EXTERNAL, cb.MODE_NATIVE, cb.MODE_HYBRID):
                s = cb.describe_requirements(proto, mode)
                self.assertIsInstance(s, str)
                self.assertTrue(s.strip())

    def test_hybrid_mentions_vnc_and_spice(self):
        s = cb.describe_requirements(cb.PROTOCOL_VNC, cb.MODE_HYBRID)
        low = s.lower()
        self.assertIn("vnc", low)
        self.assertIn("spice", low)


class SessionDetectionTests(unittest.TestCase):
    def test_x11_by_env(self):
        with mock.patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11", "WAYLAND_DISPLAY": ""}, clear=False):
            self.assertTrue(cb.is_x11_session())

    def test_wayland_by_env(self):
        with mock.patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            self.assertFalse(cb.is_x11_session())

    def test_wayland_by_display(self):
        env = {k: v for k, v in os.environ.items() if k != "XDG_SESSION_TYPE"}
        env["WAYLAND_DISPLAY"] = "wayland-0"
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(cb.is_x11_session())


if __name__ == "__main__":
    unittest.main()
