"""QEMU se resuelve aunque no esté en el PATH (Windows)."""

import services.qemu_paths as qp


def test_qemu_cmd_usa_el_path_resuelto(tmp_path, monkeypatch):
    monkeypatch.setattr(qp.shutil, "which", lambda name: None)
    monkeypatch.setattr(qp, "IS_WINDOWS", True)
    exe = tmp_path / "qemu-img.exe"
    exe.write_bytes(b"exe")

    qp.set_qemu_dir(str(tmp_path))
    try:
        assert qp.find_qemu_binary("qemu-img") == str(exe)
        assert qp.qemu_cmd("qemu-img", "create", 20) == [
            str(exe), "create", "20"]
    finally:
        qp.set_qemu_dir(None)


def test_busca_en_winget_y_en_rutas_de_program_files(tmp_path, monkeypatch):
    monkeypatch.setattr(qp.shutil, "which", lambda name: None)
    monkeypatch.setattr(qp, "IS_WINDOWS", True)
    qp.set_qemu_dir(None)

    programa = tmp_path / "Program Files" / "qemu" / "qemu-img.exe"
    programa.parent.mkdir(parents=True)
    programa.write_bytes(b"exe")
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Program Files"))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "vacias"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "user"))
    monkeypatch.delenv("QEMU_DIR", raising=False)

    assert qp.find_qemu_binary("qemu-img") == str(programa)

    programa.unlink()
    ala = (tmp_path / "local" / "Microsoft" / "WinGet" / "Packages" /
           "SoftwareFreedomConservancy.QEMU_1.0" / "tools" / "qemu-img.exe")
    ala.parent.mkdir(parents=True)
    ala.write_bytes(b"exe")
    assert qp.find_qemu_binary("qemu-img") == str(ala)


def test_linux_sigue_usando_path(monkeypatch):
    monkeypatch.setattr(qp, "IS_WINDOWS", False)
    monkeypatch.setattr(qp.shutil, "which", lambda name: "/usr/bin/" + name)
    assert qp.find_qemu_binary("qemu-img") == "/usr/bin/qemu-img"
    assert qp.qemu_cmd("qemu-img", "info") == ["/usr/bin/qemu-img", "info"]
