cat > /tmp/fix_ovf_ova_io_v1_08.py << 'PYEOF'
#!/usr/bin/env python3
# fix_ovf_ova_io_v1_08 — fix rev2: empaquetar discos sin copia previa
import ast, os, shutil, sys

TAG = "ovf_ova_io_v1_rev2"
PATH = "ovf_io.py"

with open(PATH, encoding="utf-8") as f:
    src = f.read()

if TAG in src:
    print(f"[{TAG}] {PATH} ya tiene rev2. Nada que hacer.")
    sys.exit(0)

shutil.copy2(PATH, f"{PATH}.bak_before_{TAG}")
print(f"[{TAG}] Backup: {PATH}.bak_before_{TAG}")

# ---- 1) write_manifest acepta tuplas (path, arcname) ----
OLD1 = r'''def write_manifest(files, dest_path):
    """Escribe un manifest .mf con SHA-1 de cada archivo (formato VBox)."""
    lines = []
    for p in files:
        name = os.path.basename(p)
        lines.append(f"SHA1 ({name}) = {_sha1_file(p)}")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
'''
NEW1 = r'''def write_manifest(files, dest_path):
    """Escribe un manifest .mf con SHA-1 de cada archivo (formato VBox).

    ovf_ova_io_v1_rev2: `files` puede contener strings (se usa el
    basename) o tuplas (path, arcname). Asi el empaquetado directo
    puede usar un arcname distinto del original.
    """
    lines = []
    for item in files:
        if isinstance(item, (tuple, list)):
            path, name = item[0], item[1]
        else:
            path, name = item, os.path.basename(item)
        lines.append(f"SHA1 ({name}) = {_sha1_file(path)}")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
'''
if OLD1 not in src:
    print(f"[{TAG}] ERROR: write_manifest no encontrado.", file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print(f"[{TAG}] write_manifest: acepta tuplas")

# ---- 2) pack_ova: descriptor+manifest+metadata en su propio temp dir ----
OLD2 = r'''    tmp_dir = os.path.dirname(disk_files[0]) if disk_files else tempfile.mkdtemp()
    ovf_path = os.path.join(tmp_dir, OVF_DESCRIPTOR_NAME)
    with open(ovf_path, "w", encoding="utf-8") as f:
        f.write(ovf_text)

    meta_path = None
    if extra_meta:
        meta_path = os.path.join(tmp_dir, VIRTMACHINE_META)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(extra_meta, f, ensure_ascii=False, indent=2)

    manifest_path = os.path.join(tmp_dir, MANIFEST_NAME)
    manifest_files = [ovf_path] + list(disk_files)
    if meta_path:
        manifest_files.append(meta_path)
    write_manifest(manifest_files, manifest_path)

    all_files = [ovf_path, manifest_path]
    if meta_path:
        all_files.append(meta_path)
    all_files += list(disk_files)

    total = len(all_files)
    _log(f"==> Empaquetando {total} archivo(s) en {dest_path}...")
    with tarfile.open(dest_path, "w") as tar:
        for i, p in enumerate(all_files):
            if is_cancelled and is_cancelled():
                raise RuntimeError("Exportacion cancelada por el usuario.")
            arcname = os.path.basename(p)
            tar.add(p, arcname=arcname, recursive=False)
            if progress_emit:
                pct = int((i + 1) * 100 / total)
                progress_emit(pct, f"Empaquetando {arcname} ({i+1}/{total})")
    _log(f"==> OVA empaquetado: {dest_path}")
    return dest_path
'''
NEW2 = r'''    # ovf_ova_io_v1_rev2: los archivos pequenos (descriptor, manifest,
    # metadata) van a su propio temp dir. Asi los discos pueden
    # empaquetarse directamente desde su ubicacion original.
    meta_dir = tempfile.mkdtemp(prefix=".ovf_meta_")
    try:
        ovf_path = os.path.join(meta_dir, OVF_DESCRIPTOR_NAME)
        with open(ovf_path, "w", encoding="utf-8") as f:
            f.write(ovf_text)

        meta_path = None
        if extra_meta:
            meta_path = os.path.join(meta_dir, VIRTMACHINE_META)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(extra_meta, f, ensure_ascii=False, indent=2)

        # Normalizar disk_files a lista de tuplas (path, arcname).
        disk_items = []
        for p in disk_files:
            if isinstance(p, (tuple, list)):
                disk_items.append((p[0], p[1]))
            else:
                disk_items.append((p, os.path.basename(p)))

        manifest_path = os.path.join(meta_dir, MANIFEST_NAME)
        manifest_files = [(ovf_path, OVF_DESCRIPTOR_NAME)]
        if meta_path:
            manifest_files.append((meta_path, VIRTMACHINE_META))
        manifest_files += disk_items
        write_manifest(manifest_files, manifest_path)

        all_files = [(ovf_path, OVF_DESCRIPTOR_NAME),
                     (manifest_path, MANIFEST_NAME)]
        if meta_path:
            all_files.append((meta_path, VIRTMACHINE_META))
        all_files += disk_items

        total = len(all_files)
        _log(f"==> Empaquetando {total} archivo(s) en {dest_path}...")
        with tarfile.open(dest_path, "w") as tar:
            for i, (path, arcname) in enumerate(all_files):
                if is_cancelled and is_cancelled():
                    raise RuntimeError("Exportacion cancelada por el usuario.")
                tar.add(path, arcname=arcname, recursive=False)
                if progress_emit:
                    pct = int((i + 1) * 100 / total)
                    progress_emit(pct, f"Empaquetando {arcname} ({i+1}/{total})")
        _log(f"==> OVA empaquetado: {dest_path}")
        return dest_path
    finally:
        try:
            shutil.rmtree(meta_dir, ignore_errors=True)
        except Exception:
            pass
'''
if OLD2 not in src:
    print(f"[{TAG}] ERROR: bloque pack_ova no encontrado.", file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)
print(f"[{TAG}] pack_ova: meta_dir propio + tuplas")

# Marca de revision
src = src.replace(
    'OVF_DESCRIPTOR_NAME = "descriptor.ovf"',
    '# ' + TAG + '\nOVF_DESCRIPTOR_NAME = "descriptor.ovf"',
    1,
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(src)

try:
    with open(PATH, encoding="utf-8") as f: ast.parse(f.read())
    print(f"[{TAG}] OK: {PATH} parcheado (rev2).")
except SyntaxError as e:
    shutil.copy2(f"{PATH}.bak_before_{TAG}", PATH)
    print(f"[{TAG}] ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
python3 /tmp/fix_ovf_ova_io_v1_08.py