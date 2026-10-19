#!/usr/bin/env python3
"""Test de runtime del Modo Rapido. Regla del Incidente B1."""
import importlib, os, sys, traceback
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
V = "\033[92m"; R = "\033[91m"; RS = "\033[0m"
def _ok(m):  print(f"{V}[OK]{RS}  {m}")
def _fail(m): print(f"{R}[FALLO]{RS} {m}")


def test_vm_profiles():
    m = importlib.import_module("vm_profiles")
    assert m.DEFAULT_PROFILE == "general"
    for pid in ("general", "dev", "gaming", "light"):
        assert pid in m.PROFILES, pid
    assert m.is_supported("general", "linux")
    assert not m.is_supported("gaming", "macos")
    assert not m.is_supported("light", "macos")
    d = m.profile_defaults("light", "linux")
    assert d["cores"] >= 2, d
    d = m.profile_defaults("general", "windows", "Windows 11")
    assert d["disk_gb"] >= 64, d
    d = m.profile_defaults("light", "windows", "Windows 11")
    assert d["disk_gb"] >= 64, d
    d = m.profile_defaults("general", "macos")
    assert d["disk_gb"] == 128, d
    assert m.profile_defaults("gaming", "macos") is None


def test_quick_create_dialog_import():
    m = importlib.import_module("quick_create_dialog")
    assert hasattr(m, "QuickCreateDialog")
    assert hasattr(m, "_ProfileCard")
    assert hasattr(m, "_VersionsLoader")
    assert isinstance(m.LINUX_SOS, list) and len(m.LINUX_SOS) > 0
    assert "Ubuntu" in m.LINUX_SOS


def test_quick_create_mixin():
    m = importlib.import_module("quick_create_mixin")
    assert hasattr(m, "QuickCreateMixin")
    for n in ("open_quick_create", "_populate_from_quick_create",
              "_inject_pending_iso"):
        assert hasattr(m.QuickCreateMixin, n), n


def test_principal_cdrom_integration():
    import principal_cdrom as pc
    devices = []
    pc.apply_choice(devices, "linux", "24.04", profile="Ubuntu", new_vm=True)
    p = pc.find_principal(devices)
    assert p is not None
    assert p.get("source") == "installer"
    assert p.get("iso_key") == "linux|Ubuntu|24.04"


def test_no_qt_import_in_profiles():
    import subprocess
    code = ("import sys; sys.path.insert(0,'.'); "
            "import vm_profiles; "
            "assert 'PyQt6' not in sys.modules; print('OK')")
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert "OK" in r.stdout


TESTS = [
    ("vm_profiles",         test_vm_profiles),
    ("quick_create_dialog", test_quick_create_dialog_import),
    ("quick_create_mixin",  test_quick_create_mixin),
    ("principal_cdrom",     test_principal_cdrom_integration),
    ("pureza",              test_no_qt_import_in_profiles),
]


def main():
    print("=" * 70)
    print("  TEST DE RUNTIME - Modo Rapido")
    print("=" * 70)
    passed = failed = 0
    errores = []
    for n, fn in TESTS:
        try:
            fn()
            passed += 1
            _ok(n)
        except Exception as e:
            failed += 1
            _fail(f"{n}: {e}")
            traceback.print_exc()
            errores.append((n, str(e)))
    print()
    print(f"  Resultado: {passed} OK / {failed} FALLO")
    if errores:
        for n, e in errores:
            print(f"  - {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
