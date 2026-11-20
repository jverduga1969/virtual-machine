# SPDX-License-Identifier: GPL-3.0-or-later
"""Escritor ISO 9660 mínimo con Joliet, sin herramientas externas.

Solo cubre lo que necesita la app: un árbol pequeño de archivos y
directorios para el ISO de Guest Tools. Está pensado para Windows, donde
normalmente no hay mkisofs/genisoimage/xorriso. Genera simultáneamente:

* una vista ISO 9660 (nombres 8.3 en mayúsculas) en el Volume Descriptor
  primario, y
* una vista Joliet (nombres Unicode origiales) en el suplementario.

Ambas vistas comparten los mismos archivos; solo cambian los registros de
directorio y las path tables.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SECTOR_SIZE = 2048
_VALID_ISO = re.compile(r"[^A-Z0-9_]")


@dataclass
class _Node:
    path: Path
    iso_name: str
    joliet_name: str
    is_dir: bool
    parent: "_Node | None" = None
    children: list["_Node"] = field(default_factory=list)
    number: int = 0
    extents: dict[str, int] = field(default_factory=dict)
    size: int = 0

    @property
    def data(self) -> bytes:
        return self.path.read_bytes() if not self.is_dir else b""


def _normal_iso(name: str) -> str:
    limpio = _VALID_ISO.sub("_", name.upper())
    return limpio or "FILE"


def _unique_name(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    for n in range(1, 1000):
        candidato = f"{base[:5]}~{n}"
        if candidato not in used:
            used.add(candidato)
            return candidato
    raise RuntimeError("Demasiados nombres repetidos al crear el ISO.")


def _file_name(name: str, used: set[str]) -> str:
    stem, sep, ext = name.rpartition(".")
    if not sep:
        stem, ext = name, ""
    base = f"{_normal_iso(stem)[:8]}.{_normal_iso(ext)[:3]}" if ext else _normal_iso(stem)[:8]
    return _unique_name(f"{base};1", used)


def _build_tree(root: Path) -> _Node:
    usados_por_directorio: dict[Path, set[str]] = {}

    def visit(path: Path, parent: _Node | None) -> _Node:
        usados = usados_por_directorio.setdefault(path.parent, set())
        if parent is None:
            iso = "\x00"
        elif path.is_dir():
            iso = _unique_name(_normal_iso(path.name)[:8], usados)
        else:
            iso = _file_name(path.name, usados)
        node = _Node(path=path, iso_name=iso, joliet_name=path.name,
                     is_dir=path.is_dir(), parent=parent)
        if node.is_dir:
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                node.children.append(visit(child, node))
        return node

    return visit(root, None)


def _flatten_dirs(root: _Node) -> list[_Node]:
    directorios = []

    def visit(node: _Node) -> None:
        if not node.is_dir:
            return
        node.number = len(directorios) + 1
        directorios.append(node)
        for child in node.children:
            visit(child)

    visit(root)
    return directorios


def _flatten_files(root: _Node) -> list[_Node]:
    archivos = []

    def visit(node: _Node) -> None:
        if node.is_dir:
            for child in node.children:
                visit(child)
        else:
            archivos.append(node)

    visit(root)
    return archivos


def _pad_sector(n: int) -> int:
    return (n + SECTOR_SIZE - 1) // SECTOR_SIZE * SECTOR_SIZE


def _both16(value: int) -> bytes:
    return struct.pack("<H", value) + struct.pack(">H", value)


def _both32(value: int) -> bytes:
    return struct.pack("<I", value) + struct.pack(">I", value)


def _field(text: str, size: int) -> bytes:
    return text.encode("ascii", errors="replace")[:size].ljust(size, b" ")


def _joliet_field(text: str, size: int) -> bytes:
    raw = text.encode("utf-16-be")[:size]
    return (raw + b"\x00 " * size)[:size]


def _dir_record(ident: bytes, extent: int, size: int, is_dir: bool,
                stamp: bytes, pad: bool = True) -> bytes:
    largo = 33 + len(ident)  # 33 bytes de cabecera + identificador
    if pad:
        largo += largo % 2  # el registro debe terminar en posición par
    record = bytearray(largo)
    record[0] = largo
    record[2:10] = _both32(extent)
    record[10:18] = _both32(size)
    record[18:25] = stamp
    record[25] = 0x02 if is_dir else 0x00
    record[28:32] = _both16(1)
    record[32] = len(ident)
    record[33:33 + len(ident)] = ident
    return bytes(record)


def _path_entry(ident: bytes, extent: int, parent: int, big: bool) -> bytes:
    # El identificador de la entrada raíz es siempre 1 byte (0x00); los
    # demás se alinean a longitud par.
    if ident != b"\x00" and len(ident) % 2:
        ident += b"\x00"
    pack32 = struct.pack(">I", extent) if big else struct.pack("<I", extent)
    pack16 = struct.pack(">H", parent) if big else struct.pack("<H", parent)
    return bytes([len(ident), 0]) + pack32 + pack16 + ident


def _stamp() -> bytes:
    now = datetime.now(timezone.utc)
    return bytes([now.year - 1900, now.month, now.day,
                  now.hour, now.minute, now.second, 0])


def _long_stamp() -> bytes:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%d%H%M%S").encode("ascii") + b"00\x00"


def _directory_data(node: _Node, view: str, stamp: bytes) -> bytes:
    registros = []
    for hijo in [node, node.parent] + node.children:
        if hijo is None:
            continue
        if hijo is node:
            ident = b"\x00"
        elif hijo is node.parent:
            ident = b"\x01"
        elif view == "joliet":
            ident = hijo.joliet_name.encode("utf-16-be")
        else:
            ident = hijo.iso_name.encode("ascii")
        registros.append(_dir_record(ident, hijo.extents.get(view, 0), hijo.size,
                                     hijo.is_dir, stamp))
    # El orden es obligatorio: ".", ".." y después el resto por nombre.
    registros.sort(key=lambda r: (0 if r[32] == 1 and r[33:34] == b"\x00" else
                                  1 if r[32] == 1 and r[33:34] == b"\x01" else 2,
                                  r[33:33 + r[32]]))
    return b"".join(registros)


def _descriptor(vd_type: int, volume_id: str, root: bytes, path_size: int,
                path_l: int, path_m: int, sectors: int, joliet: bool) -> bytes:
    buf = bytearray(SECTOR_SIZE)
    buf[0] = vd_type
    buf[1:6] = b"CD001"
    buf[6] = 1
    if joliet:
        # Joliet codifica también los identificadores del descriptor en UCS-2.
        buf[8:40] = _joliet_field("", 32)
        buf[40:72] = _joliet_field(volume_id, 32)
    else:
        buf[8:40] = _field("NVM", 32)
        buf[40:72] = _field(volume_id, 32)
    buf[80:88] = _both32(sectors)
    if joliet:
        buf[88:91] = b"%/E"            # escape UCS-2 nivel 3 (Joliet)
    buf[120:124] = _both16(1)          # tamaño del conjunto de volúmenes
    buf[124:128] = _both16(1)          # número de secuencia
    buf[128:132] = _both16(SECTOR_SIZE)
    buf[132:140] = _both32(path_size)
    buf[140:144] = struct.pack("<I", path_l)
    buf[148:152] = struct.pack(">I", path_m)
    buf[156:190] = root
    # Los campos de texto sin usar van rellenos de espacios (en UCS-2 en
    # Joliet); dejarlos a cero hace que algunos lectores fallen al convertir.
    for inicio, fin in ((190, 318), (318, 446), (446, 574), (574, 702),
                        (702, 739), (739, 776), (776, 813)):
        buf[inicio:fin] = (_joliet_field("", fin - inicio) if joliet
                           else b" " * (fin - inicio))
    sello = _long_stamp()
    buf[813:830] = sello
    buf[830:847] = sello
    buf[847:864] = b"0" * 16 + b"\x00"  # sin fecha de expiración
    buf[864:881] = b"0" * 16 + b"\x00"  # sin fecha efectiva
    buf[881] = 1
    return bytes(buf)


def create_iso(source_dir: str | Path, output_path: str | Path,
               volume_id: str = "GUEST_TOOLS") -> Path:
    """Crea un ISO 9660/Joliet con el contenido de ``source_dir``."""
    root_path = Path(source_dir)
    salida = Path(output_path)
    salida.parent.mkdir(parents=True, exist_ok=True)

    root = _build_tree(root_path)
    directorios = _flatten_dirs(root)
    archivos = _flatten_files(root)
    stamp = _stamp()

    vistas = {}
    for view in ("iso", "joliet"):
        vistas[view] = {dir_.number: _directory_data(dir_, view, stamp)
                        for dir_ in directorios}

    def make_path_table(view: str, big: bool) -> bytes:
        entradas = []
        for d in directorios:
            if d is root:
                ident = b"\x00"
            elif view == "joliet":
                ident = d.joliet_name.encode("utf-16-be")
            else:
                ident = d.iso_name.encode("ascii")
            entradas.append(_path_entry(ident, d.extents.get(view, 0),
                                        d.parent.number if d.parent else 1, big))
        return b"".join(entradas)

    claves = ("pvd_l", "pvd_m", "joliet_l", "joliet_m")
    tamanos = {
        "pvd_l": len(make_path_table("iso", False)),
        "pvd_m": len(make_path_table("iso", True)),
        "joliet_l": len(make_path_table("joliet", False)),
        "joliet_m": len(make_path_table("joliet", True)),
    }
    sector = 19
    sectores = {}
    for clave in claves:
        sectores[clave] = sector
        sector += _pad_sector(tamanos[clave]) // SECTOR_SIZE

    for view in ("iso", "joliet"):
        for dir_ in directorios:
            size = _pad_sector(len(vistas[view][dir_.number]))
            dir_.extents[view] = sector
            dir_.size = size
            sector += size // SECTOR_SIZE

    for archivo in archivos:
        archivo.extents["iso"] = sector
        archivo.extents["joliet"] = sector
        archivo.size = len(archivo.data)
        sector += _pad_sector(archivo.size) // SECTOR_SIZE

    # Con todos los extents conocidos, regeneramos registros y path tables
    # con las direcciones reales (su longitud no cambia).
    for view in ("iso", "joliet"):
        vistas[view] = {dir_.number: _directory_data(dir_, view, stamp)
                        for dir_ in directorios}
    tablas = {
        "pvd_l": make_path_table("iso", False),
        "pvd_m": make_path_table("iso", True),
        "joliet_l": make_path_table("joliet", False),
        "joliet_m": make_path_table("joliet", True),
    }

    total_sectores = sector
    # El campo de directorio raíz del descriptor ocupa exactamente 34 bytes
    # (sin el relleno a posición par de los registros de directorio normales).
    root_iso = _dir_record(b"\x00", root.extents["iso"], root.size, True, stamp,
                           pad=False)
    root_joliet = _dir_record(b"\x00", root.extents["joliet"], root.size, True,
                              stamp, pad=False)

    with salida.open("wb") as fh:
        fh.write(b"\x00" * (SECTOR_SIZE * 16))
        fh.write(_descriptor(1, volume_id, root_iso, len(tablas["pvd_l"]),
                             sectores["pvd_l"], sectores["pvd_m"],
                             total_sectores, False))
        fh.write(_descriptor(2, volume_id, root_joliet, len(tablas["joliet_l"]),
                             sectores["joliet_l"], sectores["joliet_m"],
                             total_sectores, True))
        fh.write(bytes([255]) + b"CD001" + b"\x01" + b"\x00" * (SECTOR_SIZE - 7))
        for clave in ("pvd_l", "pvd_m", "joliet_l", "joliet_m"):
            fh.write(tablas[clave].ljust(_pad_sector(len(tablas[clave])), b"\x00"))
        for view in ("iso", "joliet"):
            for dir_ in directorios:
                fh.write(vistas[view][dir_.number].ljust(dir_.size, b"\x00"))
        for archivo in archivos:
            fh.write(archivo.data.ljust(_pad_sector(archivo.size), b"\x00"))

    return salida
