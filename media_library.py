# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""media_library.py — Biblioteca central de medios de instalación.

Marcador: media_library_v1 / media_library_autodetect_v1.

Almacena y describe todas las ISOs / IMGs / DMGs que el usuario utiliza
para instalar sistemas en sus VMs: instaladores de Linux/Windows, el
Recovery de macOS, ISOs de Android-x86 / Bliss OS, ISOs de Guest Tools
(VirtIO), etc.

Diseño:

  • El índice (_index.json) es la fuente de verdad. Vive al mismo nivel
    que VirtualMachines/ (junto a run.sh), en una carpeta llamada
    MediaLibrary/.
  • Los archivos pueden estar DENTRO de MediaLibrary/ (entradas
    "internas", portables si mueves toda la carpeta del proyecto) o en
    cualquier ruta absoluta del host (entradas "externas").
  • Cada entrada tiene metadatos: nombre, distro, versión, arquitectura,
    tipo de SO, tamaño, sha256 (bajo demanda), notas, tags, color,
    fechas de alta/uso.

Módulo puro: no importa PyQt. Testeable directamente:

    python3 -c "from media_library import MediaLibrary; \\
                lib = MediaLibrary(); print(len(lib.list_all()))"
"""
import os
import re
import json
import uuid
import hashlib
import shutil
import subprocess
import tempfile
from datetime import datetime


# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

LIBRARY_DIRNAME = "MediaLibrary"
INDEX_FILENAME = "_index.json"
INDEX_VERSION = 1

# media_library_host_mount_v1: anadidos vmdk/vdi/vhd/vhdx.
VALID_KINDS = ("iso", "img", "dmg", "raw", "qcow2",
               "vmdk", "vdi", "vhd", "vhdx", "other")
VALID_OS_TYPES = ("linux", "windows", "macos", "android", "guest-tools", "other")


# ----------------------------------------------------------------------
# Helpers puros
# ----------------------------------------------------------------------

def default_base_dir():
    """Devuelve <PROJECT>/MediaLibrary/.

    El proyecto es el directorio de este módulo. Misma convención que
    vm_config.BASE_VM_DIR: no depende del CWD, así la app puede
    arrancarse desde cualquier sitio.
    """
    # media_library_xdg_v1: en modo paquete el modulo vive en /usr/lib
    # (solo lectura); la biblioteca va junto a VirtualMachines/.
    try:
        import vm_config
        root = os.path.dirname(os.path.abspath(vm_config.BASE_VM_DIR))
    except Exception:
        root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, LIBRARY_DIRNAME)


def kind_from_ext(path):
    """Deduce el ``kind`` a partir de la extensión del archivo."""
    ext = os.path.splitext(str(path or ""))[1].lower().lstrip(".")
    if ext == "iso":
        return "iso"
    if ext == "img":
        return "img"
    if ext == "dmg":
        return "dmg"
    if ext == "raw":
        return "raw"
    if ext in ("qcow2", "qcow"):
        return "qcow2"
    # media_library_host_mount_v1: formatos que QEMU abre como disco.
    if ext == "vmdk":
        return "vmdk"
    if ext == "vdi":
        return "vdi"
    if ext == "vhd":
        return "vhd"
    if ext == "vhdx":
        return "vhdx"
    return "other"


# media_library_type_column_v1: categoria visible del medio
# (Disco duro / ISO / Disquete / Otro). Se calcula a partir de `roles`
# (cuando la entrada viene de escanear VMs) y, si esta vacio, cae a
# `kind` + tamano.
def media_type_key(entry):
    """Devuelve 'disk' / 'iso' / 'floppy' / 'other'."""
    if not isinstance(entry, dict):
        return "other"
    roles = set(entry.get("roles") or [])
    kind = str(entry.get("kind") or "").lower()
    if "floppy" in roles:
        return "floppy"
    if "cdrom" in roles or "recovery" in roles or "boot" in roles:
        return "iso"
    if "system-disk" in roles or "data-disk" in roles:
        return "disk"
    if kind in ("iso", "dmg"):
        return "iso"
    if kind in ("qcow2", "qcow", "vdi", "vmdk", "vhd", "vhdx"):
        return "disk"
    if kind in ("img", "raw"):
        try:
            sz = int(entry.get("size") or 0)
        except (TypeError, ValueError):
            sz = 0
        if sz and sz <= 32 * 1024 * 1024:
            return "floppy"
        return "disk"
    return "other"

def media_type_label(entry):
    """Etiqueta humana del tipo de medio."""
    return {
        "disk": "Disco duro",
        "iso": "ISO",
        "floppy": "Disquete",
        "other": "Otro",
    }.get(media_type_key(entry), "Otro")

# virtual_size_v1: tamaño virtual (el que ve el guest) para imagenes
# de disco. Para ISOs/IMGs/DMGs coincide con el tamaño del archivo.
def _virtual_size_for(path):
    """Devuelve el tamaño virtual de una imagen de disco (bytes).

    - QCOW2/RAW/VHD/VMDK/VDI/VHDX -> virtual-size de qemu-img info.
    - Resto (ISO/DMG/IMG) -> tamaño de archivo.
    - Si algo falla -> 0.
    """
    try:
        ext = os.path.splitext(str(path or ""))[1].lower()
    except Exception:
        ext = ""
    if ext in (".qcow2", ".qcow", ".raw", ".vdi", ".vmdk", ".vhd", ".vhdx"):
        try:
            r = subprocess.run(
                ["qemu-img", "info", "--output=json", path],
                capture_output=True, text=True, timeout=10, check=True,
            )
            return int(json.loads(r.stdout).get("virtual-size") or 0)
        except Exception:
            return 0
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _now_str():
    return datetime.now().strftime("%Y-%m-%d")


def _new_id():
    return "ml_" + uuid.uuid4().hex[:12]


def _normalize_kind(value, fallback_path=""):
    v = str(value or "").strip().lower()
    if v in VALID_KINDS:
        return v
    return kind_from_ext(fallback_path) if fallback_path else "other"


def _normalize_os_type(value):
    v = str(value or "").strip().lower()
    if v in VALID_OS_TYPES:
        return v
    return "other"


def _normalize_arch(value):
    v = str(value or "").strip().lower()
    if v in ("x86_64", "amd64", "x64"):
        return "x86_64"
    if v in ("i386", "i486", "i586", "i686", "x86"):
        return "i686"
    if v in ("aarch64", "arm64"):
        return "aarch64"
    if v in ("universal", "all", "any"):
        return "universal"
    return ""


def _human_bytes(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f} {u}" if u != "B" else f"{int(n)} B"
        n /= 1024.0


# ----------------------------------------------------------------------
# Auto-detección de metadatos
# ----------------------------------------------------------------------

# Cada matcher: (regex, os_type, distro). El primero que encaja gana.
_MATCHERS = [
    # --- Windows ---
    # Sin \b final: tras "11", "10"... puede venir "_" (también word char)
    # y romper el \b. Usamos (?![0-9]) para no matchear "Windows 1" mal.
    (re.compile(r"win(?:dows)?[\s_.-]*11(?![0-9])", re.I), "windows", "Windows 11"),
    (re.compile(r"win(?:dows)?[\s_.-]*10(?![0-9])", re.I), "windows", "Windows 10"),
    (re.compile(r"win(?:dows)?[\s_.-]*8(?:[._-]1)?(?![0-9])", re.I), "windows", "Windows 8.1"),
    (re.compile(r"win(?:dows)?[\s_.-]*7(?![0-9])", re.I), "windows", "Windows 7"),
    (re.compile(r"win(?:dows)?[\s_.-]*vista", re.I), "windows", "Windows Vista"),
    (re.compile(r"win(?:dows)?[\s_.-]*xp", re.I), "windows", "Windows XP"),
    (re.compile(r"win(?:dows)?[\s_.-]*2000", re.I), "windows", "Windows 2000"),
    # --- macOS ---
    (re.compile(r"basesystem", re.I), "macos", "macOS Recovery"),
    (re.compile(r"installassistant", re.I), "macos", "macOS Installer"),
    (re.compile(r"macos[\s_.-]*(?:monterey|ventura|sonoma|sequoia|tahoe|big[\s_.-]?sur|catalina|mojave|high[\s_.-]?sierra)", re.I), "macos", "macOS"),
    # --- Android ---
    (re.compile(r"android[\s_.-]?x86", re.I), "android", "Android-x86"),
    (re.compile(r"bliss", re.I), "android", "Bliss OS"),
    # --- Guest Tools ---
    (re.compile(r"virtio[\s_.-]?win", re.I), "guest-tools", "VirtIO Guest Tools"),
    (re.compile(r"spice[\s_.-]?guest", re.I), "guest-tools", "SPICE Guest Tools"),
    # --- Linux (sin \b: "linuxmint", "cachyos" etc. son palabras pegadas) ---
    (re.compile(r"linuxmint|linux[\s_.-]?mint|mint(?![a-z])", re.I), "linux", "Linux Mint"),
    (re.compile(r"ubuntu", re.I), "linux", "Ubuntu"),
    (re.compile(r"debian", re.I), "linux", "Debian"),
    (re.compile(r"fedora", re.I), "linux", "Fedora"),
    (re.compile(r"manjaro", re.I), "linux", "Manjaro"),
    (re.compile(r"cachyos", re.I), "linux", "CachyOS"),
    (re.compile(r"endeavour", re.I), "linux", "EndeavourOS"),
    (re.compile(r"arch[\s_.-]?linux", re.I), "linux", "Arch Linux"),
    (re.compile(r"pop[\s_.-]?[!_ ]?os", re.I), "linux", "Pop!_OS"),
    (re.compile(r"zorinos|zorin", re.I), "linux", "Zorin OS"),
    (re.compile(r"elementary", re.I), "linux", "elementary OS"),
    (re.compile(r"kali", re.I), "linux", "Kali Linux"),
    (re.compile(r"mx[\s_.-]?linux", re.I), "linux", "MX Linux"),
    (re.compile(r"open[\s_.-]?suse|opensuse", re.I), "linux", "openSUSE"),
    (re.compile(r"solus", re.I), "linux", "Solus"),
    (re.compile(r"alma[\s_.-]?linux", re.I), "linux", "AlmaLinux"),
    (re.compile(r"rocky[\s_.-]?linux", re.I), "linux", "Rocky Linux"),
    (re.compile(r"alpine", re.I), "linux", "Alpine Linux"),
    (re.compile(r"void[\s_.-]?linux", re.I), "linux", "Void Linux"),
    (re.compile(r"antix", re.I), "linux", "antiX"),
]

_VERSION_PATTERNS = [
    # Builds tipo "23H2" (Windows) — antes que cualquier patrón numérico.
    # 23H2 pattern relaxed: no usa \b porque "_" tambien
    # es word char y rompe la frontera (Win11_23H2_...).
    re.compile(r"(?<![A-Za-z])(\d{2}H\d)(?![0-9])"),
    # X.Y.Z: permitir 3-4 dígitos en el último segmento
    # (0.1.240, 22.04.3, 9.0.0.0, etc.).
    re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{1,4})\b"),
    # X.Y
    re.compile(r"\b(\d{1,2}\.\d{1,2})\b"),
    # AAAA (año) — antes que el genérico de 1-2 dígitos
    re.compile(r"\b((?:19|20)\d{2})\b"),
    # Número suelto
    re.compile(r"\b(\d{1,2})\b"),
]

_ARCH_PATTERNS = [
    (re.compile(r"(?:^|[\s_.\-])(?:x86[_-]?64|amd64|x64)(?:[\s_.\-]|$)", re.I), "x86_64"),
    (re.compile(r"(?:^|[\s_.\-])(?:i[3-6]86|x86)(?:[\s_.\-]|$)", re.I), "i686"),
    (re.compile(r"(?:^|[\s_.\-])(?:aarch64|arm64)(?:[\s_.\-]|$)", re.I), "aarch64"),
    (re.compile(r"(?:^|[\s_.\-])(?:universal|all|any)(?:[\s_.\-]|$)", re.I), "universal"),
]


def auto_detect(path):
    """Heurística de metadatos a partir del nombre del archivo.

    Devuelve un dict con las keys que reconoce. Los campos que no se
    pueden determinar quedan como cadena vacía o "other" para os_type.

    Ejemplos:
      linuxmint-21.3-cinnamon-64bit.iso
        → os_type=linux, distro=Linux Mint, version=21.3, arch=x86_64
      Win11_23H2_English_x64.iso
        → os_type=windows, distro=Windows 11, version=23H2, arch=x86_64
      BaseSystem.img
        → os_type=macos, distro=macOS Recovery, arch=universal
    """
    filename = os.path.basename(str(path or ""))
    stem = os.path.splitext(filename)[0]
    lower = stem.lower()
    # Para los matchers usamos el filename completo (con extensión):
    # algunos patrones (p. ej. "basesystem") pueden necesitar ver el
    # nombre tal cual, y el "._" no molesta a los que no lo necesitan.
    # Para _VERSION_PATTERNS seguimos usando el stem para no capturar
    # dígitos de la extensión (.7z, .2, etc.).
    haystack_name = filename

    out = {
        "os_type": "other",
        "distro": "",
        "version": "",
        "arch": "",
        "kind": kind_from_ext(path),
        "name": stem,
    }

    for pattern, os_type, distro in _MATCHERS:
        if pattern.search(haystack_name):
            out["os_type"] = os_type
            out["distro"] = distro
            break

    for vp in _VERSION_PATTERNS:
        m = vp.search(stem)
        if m:
            out["version"] = m.group(1)
            break

    for ap, arch in _ARCH_PATTERNS:
        if ap.search(stem):
            out["arch"] = arch
            break

    if not out["arch"]:
        if re.search(r"\b64[\s_-]?bit\b", lower):
            out["arch"] = "x86_64"
        elif re.search(r"\b32[\s_-]?bit\b", lower):
            out["arch"] = "i686"

    # macOS: Apple distribuye Recovery/instaladores como binarios
    # universales. Si no detectamos una arquitectura especifica, es
    # "universal" por defecto.
    if out["os_type"] == "macos" and not out["arch"]:
        out["arch"] = "universal"

    return out


# ----------------------------------------------------------------------
# Hash
# ----------------------------------------------------------------------

def compute_sha256(path, progress_cb=None, chunk_size=1024 * 1024):
    """Calcula el sha256 de un archivo.

    ``progress_cb`` recibe (bytes_leídos, bytes_totales) cada
    ``chunk_size`` bytes. Devuelve el hexdigest. Lanza OSError si no se
    puede leer.
    """
    h = hashlib.sha256()
    try:
        total = os.path.getsize(path)
    except OSError:
        total = 0
    read = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            if progress_cb is not None:
                try:
                    progress_cb(read, total)
                except Exception:
                    pass
    return h.hexdigest()


# ----------------------------------------------------------------------
# Clase principal
# ----------------------------------------------------------------------

class MediaLibrary:
    """Biblioteca central de medios de instalación.

    Las escrituras al índice son atómicas (tmp + os.replace). Las rutas
    internas se guardan relativas a ``base_dir`` para que la carpeta
    sea portable.
    """

    def __init__(self, base_dir=None):
        self.base_dir = os.path.abspath(base_dir or default_base_dir())
        self.index_path = os.path.join(self.base_dir, INDEX_FILENAME)
        self._entries = {}
        self._load_index()

    # ------------------------------------------------------------ índice

    def _load_index(self):
        os.makedirs(self.base_dir, exist_ok=True)
        if not os.path.isfile(self.index_path):
            self._entries = {}
            self._save_index()
            return
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            try:
                shutil.copy2(
                    self.index_path,
                    self.index_path + ".corrupt",
                )
            except Exception:
                pass
            self._entries = {}
            self._save_index()
            return
        entries = data.get("entries") or {}
        self._entries = {}
        for k, v in entries.items():
            if isinstance(v, dict):
                self._entries[str(k)] = v

    def _save_index(self):
        """Escritura atómica del índice (tmp + os.replace)."""
        payload = {
            "version": INDEX_VERSION,
            "entries": self._entries,
        }
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                prefix="_index.",
                suffix=".json.tmp",
                dir=self.base_dir,
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            os.replace(tmp_path, self.index_path)
            tmp_path = None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # ------------------------------------------------------ util. paths

    def _to_stored_path(self, abs_or_rel):
        """Ruta tal como se guarda: relativa si está dentro de
        ``base_dir``; absoluta si está fuera."""
        p = os.path.abspath(abs_or_rel)
        try:
            common = os.path.commonpath([self.base_dir, p])
        except ValueError:
            common = ""
        if common == self.base_dir:
            rel = os.path.relpath(p, self.base_dir)
            return rel.replace(os.sep, "/")
        return p

    def _to_absolute(self, stored):
        s = str(stored or "").strip()
        if not s:
            return ""
        if os.path.isabs(s):
            return os.path.abspath(s)
        return os.path.abspath(os.path.join(self.base_dir, s))

    def resolve_path(self, entry_or_id):
        """Ruta absoluta del archivo asociado a una entrada o id."""
        if isinstance(entry_or_id, dict):
            entry = entry_or_id
        else:
            entry = self._entries.get(str(entry_or_id))
        if not entry:
            return ""
        return self._to_absolute(entry.get("path"))

    # ----------------------------------------------------------- lectura

    def list_all(self):
        out = list(self._entries.values())
        out.sort(key=lambda e: (str(e.get("name") or "").lower(),
                                str(e.get("id") or "")))
        return out

    def get(self, entry_id):
        return self._entries.get(str(entry_id))

    def find(self, query):
        """Búsqueda de texto libre (case-insensitive)."""
        q = str(query or "").strip().lower()
        if not q:
            return self.list_all()
        results = []
        for e in self._entries.values():
            parts = [
                str(e.get(k) or "") for k in
                ("name", "distro", "filename", "notes", "version",
                 "source_url")
            ]
            parts.append(" ".join(str(t) for t in (e.get("tags") or [])))
            haystack = " ".join(parts).lower()
            if q in haystack:
                results.append(e)
        results.sort(key=lambda e: str(e.get("name") or "").lower())
        return results

    def filter_by(self, os_type=None, arch=None, kind=None, tags=None):
        want_os = _normalize_os_type(os_type) if os_type else None
        want_arch = _normalize_arch(arch) if arch else None
        want_kind = str(kind or "").strip().lower() or None
        want_tags = {str(t).lower() for t in (tags or [])}

        out = []
        for e in self._entries.values():
            if want_os and _normalize_os_type(e.get("os_type")) != want_os:
                continue
            if want_arch and _normalize_arch(e.get("arch")) != want_arch:
                continue
            if want_kind and str(e.get("kind") or "").lower() != want_kind:
                continue
            if want_tags:
                have = {str(t).lower() for t in (e.get("tags") or [])}
                if not want_tags.issubset(have):
                    continue
            out.append(e)
        out.sort(key=lambda e: str(e.get("name") or "").lower())
        return out

    # ------------------------------------------------------------ altas

    def add(self, path, **meta):
        """Registra una entrada nueva. Aplica auto_detect() primero y
        luego sobreescribe con los ``meta`` pasados por el usuario."""
        if not path:
            raise ValueError("MediaLibrary.add: path vacío.")

        abs_path = os.path.abspath(path)
        stored = self._to_stored_path(abs_path)
        external = (stored == abs_path)
        detected = auto_detect(abs_path)

        entry = {
            "id": _new_id(),
            "path": stored,
            "external": external,
            "name": detected.get("name") or os.path.basename(abs_path),
            "filename": os.path.basename(abs_path),
            "size": 0,
            "sha256": "",
            "kind": detected.get("kind") or kind_from_ext(abs_path),
            "os_type": detected.get("os_type") or "other",
            "distro": detected.get("distro") or "",
            "version": detected.get("version") or "",
            "arch": detected.get("arch") or "",
            "notes": "",
            "tags": [],
            "color": "",
            "added_at": _now_str(),
            "last_used": "",
            "source_url": "",
            # virtual_size_v1: tamaño virtual (el que ve el guest).
            "virtual_size": 0,
            # media_library_vm_scan_v1: origen y uso por VMs.
            #   origin  = "manual" (la a\u00f1adi\u00f3 el usuario) o
            #             "vm" (descubierta al escanear VirtualMachines/).
            #   used_by = nombres de VMs que usan este archivo. La misma
            #             ISO puede estar en varias VMs: es UNA entrada
            #             con la lista completa.
            #   roles   = roles por uso: system-disk, data-disk, cdrom,
            #             floppy, recovery, boot.
            "origin": "manual",
            "used_by": [],
            "roles": [],
        }
        try:
            entry["size"] = os.path.getsize(abs_path)
        except OSError:
            pass
        # virtual_size_v1
        try:
            entry["virtual_size"] = _virtual_size_for(abs_path)
        except Exception:
            pass

        for k, v in (meta or {}).items():
            if k == "tags" and v is not None:
                entry["tags"] = [str(x) for x in (v or []) if str(x).strip()]
            elif k == "os_type":
                entry["os_type"] = _normalize_os_type(v)
            elif k == "arch":
                entry["arch"] = _normalize_arch(v)
            elif k == "kind":
                entry["kind"] = _normalize_kind(v, abs_path)
            elif k == "id":
                continue
            else:
                entry[k] = v

        self._entries[entry["id"]] = entry
        self._save_index()
        return entry

    def update(self, entry_id, **fields):
        e = self._entries.get(str(entry_id))
        if not e:
            return None
        for k, v in (fields or {}).items():
            if k == "tags" and v is not None:
                e["tags"] = [str(x) for x in (v or []) if str(x).strip()]
            elif k == "os_type":
                e["os_type"] = _normalize_os_type(v)
            elif k == "arch":
                e["arch"] = _normalize_arch(v)
            elif k == "kind":
                e["kind"] = _normalize_kind(v, e.get("path") or "")
            elif k == "id":
                continue
            else:
                e[k] = v
        self._save_index()
        return e

    def remove(self, entry_id, delete_file=False):
        e = self._entries.pop(str(entry_id), None)
        if not e:
            return False
        if delete_file and not e.get("external"):
            abs_path = self._to_absolute(e.get("path") or "")
            if abs_path and os.path.isfile(abs_path):
                try:
                    os.remove(abs_path)
                except OSError:
                    pass
        self._save_index()
        return True

    # ------------------------------------------------------ verificación

    # virtual_size_v1: recalcular el tamaño virtual/real tras expandir
    # o compactar un disco de la biblioteca.
    def update_virtual_size(self, entry_id):
        """Recalcula y persiste el tamaño real y virtual de una entrada."""
        e = self._entries.get(str(entry_id))
        if not e:
            return 0
        abs_path = self._to_absolute(e.get("path") or "")
        if not abs_path or not os.path.isfile(abs_path):
            e["virtual_size"] = 0
        else:
            try:
                e["virtual_size"] = _virtual_size_for(abs_path)
            except Exception:
                e["virtual_size"] = 0
            try:
                e["size"] = os.path.getsize(abs_path)
            except OSError:
                pass
        self._save_index()
        return int(e.get("virtual_size") or 0)

    def refresh_virtual_sizes(self, only_ids=None):
        """Recalcula tamaño real + virtual de una o varias entradas."""
        ids = list(only_ids) if only_ids else list(self._entries.keys())
        for eid in ids:
            try:
                self.update_virtual_size(eid)
            except Exception:
                pass

    def verify(self, entry_id):
        """Comprueba existencia y (si hay hash) coincidencia."""
        e = self._entries.get(str(entry_id))
        if not e:
            return {"exists": False, "hash_ok": None, "path": "",
                    "expected": "", "actual": ""}
        abs_path = self._to_absolute(e.get("path") or "")
        exists = bool(abs_path and os.path.isfile(abs_path))
        result = {
            "exists": exists,
            "hash_ok": None,
            "path": abs_path,
            "expected": str(e.get("sha256") or ""),
            "actual": "",
        }
        if exists and result["expected"]:
            try:
                result["actual"] = compute_sha256(abs_path)
                result["hash_ok"] = (result["actual"] == result["expected"])
            except OSError:
                result["hash_ok"] = False
        return result

    def compute_sha256(self, entry_id, progress_cb=None):
        e = self._entries.get(str(entry_id))
        if not e:
            return None
        abs_path = self._to_absolute(e.get("path") or "")
        if not abs_path or not os.path.isfile(abs_path):
            return None
        digest = compute_sha256(abs_path, progress_cb=progress_cb)
        e["sha256"] = digest
        self._save_index()
        return digest

    # ---------------------------------------------------------- escaneo

    @staticmethod
    def _looks_like_media(filename):
        ext = os.path.splitext(filename)[1].lower()
        # media_library_host_mount_v1: reconocer tambien los formatos
        # de disco que QEMU puede abrir como bloque.
        return ext in (".iso", ".img", ".dmg", ".raw", ".qcow2", ".qcow",
                       ".vmdk", ".vdi", ".vhd", ".vhdx")

    def _file_exists(self, entry):
        abs_path = self._to_absolute(entry.get("path") or "")
        return bool(abs_path and os.path.isfile(abs_path))

    def scan(self):
        """Escanea ``base_dir`` buscando archivos aún no registrados.

        Devuelve ``{"nuevos": [dict,...], "huerfanos": [dict,...]}``.
        NO registra ni elimina automáticamente: el usuario decide desde
        la UI.
        """
        known_abs = set()
        for e in self._entries.values():
            if e.get("external"):
                continue
            abs_path = self._to_absolute(e.get("path") or "")
            if abs_path:
                known_abs.add(abs_path)

        nuevos = []
        try:
            for root, dirs, files in os.walk(self.base_dir):
                dirs[:] = [d for d in dirs
                           if not d.startswith(".") and d != "__pycache__"]
                for f in files:
                    if f == INDEX_FILENAME or f.endswith(".tmp"):
                        continue
                    if f.startswith("_index."):
                        continue
                    abs_path = os.path.abspath(os.path.join(root, f))
                    if abs_path in known_abs:
                        continue
                    if not self._looks_like_media(f):
                        continue
                    det = auto_detect(abs_path)
                    det["path_abs"] = abs_path
                    det["size"] = 0
                    try:
                        det["size"] = os.path.getsize(abs_path)
                    except OSError:
                        pass
                    nuevos.append(det)
        except OSError:
            pass

        huerfanos = [e for e in self._entries.values()
                     if not self._file_exists(e)]
        return {"nuevos": nuevos, "huerfanos": huerfanos}

    # ------------------------------------------------------ scan_vms
    # Marcador: media_library_vm_scan_v1.
    #
    # Escanea VirtualMachines/ y cataloga los medios que usan las VMs:
    # discos duros, ISOs, disquetes, Recovery de macOS, etc. La misma
    # ISO usada por 3 VMs es UNA entrada con used_by=[vm1,vm2,vm3].
    #
    # No borra archivos ni entradas: si una entrada origin="vm" ya no
    # la usa nadie, se queda con used_by=[] para que el usuario decida.

    _ROLE_BY_DEVICE = {
        "sata": "data-disk",
        "nvme": "data-disk",
        "floppy": "floppy",
        "cdrom": "cdrom",
    }

    def _default_vm_dir(self):
        """Directorio VirtualMachines/ del proyecto.

        Se calcula desde la ubicacion de este modulo para no depender
        de vm_config.py (este modulo debe seguir siendo independiente).
        """
        # media_library_xdg_v1
        try:
            import vm_config
            return vm_config.BASE_VM_DIR
        except Exception:
            here = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(here, "VirtualMachines")

    def _role_for_filename(self, filename):
        """Deduce el rol de un archivo por su nombre (heuristica)."""
        low = str(filename or "").lower()
        if low == "mac_hdd_ng.qcow2" or low.startswith("vm_disk."):
            return "system-disk"
        if "opencore" in low:
            return "boot"
        if low.startswith("basesystem") or low == "basesystem.img":
            return "recovery"
        if low.startswith("floppy_"):
            return "floppy"
        if low.endswith(".iso") or low.endswith(".dmg"):
            return "cdrom"
        return "data-disk"

    def _scan_one_vm(self, vm_name, vm_dir, cfg_path, found):
        """Lee un vm_config.ini y acumula sus medios en `found`.

        `found` es un dict: path_abs -> {"vm_names": set, "roles": set}.
        """
        import configparser as _cp
        devices = []
        try:
            cp = _cp.ConfigParser(interpolation=None)
            cp.read(cfg_path, encoding="utf-8")
            if cp.has_section("extra"):
                extra = json.loads(cp["extra"].get("data", "{}"))
                devices = extra.get("storage_devices") or []
        except Exception:
            devices = []

        # --- Pasada 1: storage_devices registrados ---
        for d in (devices if isinstance(devices, list) else []):
            if not isinstance(d, dict):
                continue
            p = str(d.get("path") or "").strip()
            if not p:
                continue
            abs_p = p if os.path.isabs(p) else os.path.abspath(
                os.path.join(vm_dir, p))
            if not os.path.isfile(abs_p):
                continue
            dev = str(d.get("device") or "sata").lower()
            role = self._ROLE_BY_DEVICE.get(dev, "data-disk")
            base_low = os.path.basename(abs_p).lower()
            if (base_low.startswith("vm_disk.")
                    or base_low == "mac_hdd_ng.qcow2"):
                role = "system-disk"
            info = found.setdefault(
                abs_p, {"vm_names": set(), "roles": set()})
            info["vm_names"].add(vm_name)
            info["roles"].add(role)

        # --- Pasada 2: archivos no registrados (auto-descubrimiento y
        # los 3 discos fijos de macOS). ---
        try:
            for name in sorted(os.listdir(vm_dir)):
                full = os.path.join(vm_dir, name)
                if not os.path.isfile(full):
                    continue
                low = name.lower()
                if not low.endswith((
                    ".qcow2", ".qcow", ".img", ".raw",
                    ".vdi", ".vmdk", ".vhd", ".vhdx",
                    ".iso", ".dmg",
                )):
                    continue
                abs_p = os.path.abspath(full)
                role = self._role_for_filename(name)
                info = found.setdefault(
                    abs_p, {"vm_names": set(), "roles": set()})
                info["vm_names"].add(vm_name)
                info["roles"].add(role)
        except OSError:
            pass

    def scan_vms(self, base_vm_dir=None):
        """Escanea las VMs y actualiza el catalogo de medios."""
        if base_vm_dir is None:
            base_vm_dir = self._default_vm_dir()
        base_vm_dir = os.path.abspath(base_vm_dir)

        found = {}
        if os.path.isdir(base_vm_dir):
            for vm_name in sorted(os.listdir(base_vm_dir)):
                vm_dir = os.path.join(base_vm_dir, vm_name)
                if not os.path.isdir(vm_dir):
                    continue
                cfg_path = os.path.join(vm_dir, "vm_config.ini")
                if not os.path.isfile(cfg_path):
                    continue
                try:
                    self._scan_one_vm(vm_name, vm_dir, cfg_path, found)
                except Exception:
                    continue

        existing_by_path = {}
        for e in self._entries.values():
            p = self._to_absolute(e.get("path") or "")
            if p:
                existing_by_path[p] = e

        nuevas = 0
        actualizadas = 0
        sin_cambios = 0
        touched = set()

        for path_abs, info in found.items():
            used_by = sorted(info["vm_names"])
            roles = sorted(info["roles"])
            e = existing_by_path.get(path_abs)
            if e is None:
                # media_library_vm_scan_touched_fix_v1: registrar el id
                # de la entrada recien creada en `touched`. Sin esto, el
                # bloque final la trata como huerfana y le borra
                # used_by/roles en el mismo scan.
                try:
                    new_e = self.add(path_abs, origin="vm",
                                     used_by=used_by, roles=roles)
                    if isinstance(new_e, dict) and new_e.get("id"):
                        touched.add(new_e["id"])
                    nuevas += 1
                except Exception:
                    pass
                continue
            touched.add(e["id"])
            changes = {}
            if list(e.get("used_by") or []) != used_by:
                changes["used_by"] = used_by
            if list(e.get("roles") or []) != roles:
                changes["roles"] = roles
            cur_origin = str(e.get("origin") or "").strip()
            if cur_origin != "manual" and cur_origin != "vm":
                changes["origin"] = "vm"
            if changes:
                self.update(e["id"], **changes)
                actualizadas += 1
            else:
                sin_cambios += 1

        huerfanas_de_vm = []
        for e in self._entries.values():
            if str(e.get("origin") or "") != "vm":
                continue
            if e.get("id") in touched:
                continue
            if e.get("used_by") or e.get("roles"):
                self.update(e["id"], used_by=[], roles=[])
                huerfanas_de_vm.append(e)

        # virtual_size_v1: recalcular tamaños de las entradas afectadas
        # para que la pestaña Medios muestre el tamaño virtual actualizado
        # tras crear/expandir/compactar archivos.
        try:
            self.refresh_virtual_sizes(only_ids=list(touched))
        except Exception:
            pass

        self._save_index()
        return {
            "nuevas": nuevas,
            "actualizadas": actualizadas,
            "sin_cambios": sin_cambios,
            "huerfanas_de_vm": huerfanas_de_vm,
            "total_paths": len(found),
        }

    # -------------------------------------------------------- consultas

    def find_orphans(self):
        return [e for e in self._entries.values() if not self._file_exists(e)]

    def find_duplicates(self):
        """Agrupa por sha256. Solo entre entradas con hash calculado."""
        by_hash = {}
        for e in self._entries.values():
            h = str(e.get("sha256") or "").strip()
            if not h:
                continue
            by_hash.setdefault(h, []).append(e)
        return {h: items for h, items in by_hash.items() if len(items) > 1}

    def mark_used(self, entry_id):
        e = self._entries.get(str(entry_id))
        if not e:
            return False
        e["last_used"] = _now_str()
        self._save_index()
        return True

    # ------------------------------------------------------------- stats

    def stats(self):
        total = 0
        by_os = {}
        by_kind = {}
        size_total = 0
        for e in self._entries.values():
            total += 1
            k_os = _normalize_os_type(e.get("os_type"))
            by_os[k_os] = by_os.get(k_os, 0) + 1
            k_kind = _normalize_kind(e.get("kind"))
            by_kind[k_kind] = by_kind.get(k_kind, 0) + 1
            try:
                size_total += int(e.get("size") or 0)
            except (TypeError, ValueError):
                pass
        return {
            "total": total,
            "by_os_type": by_os,
            "by_kind": by_kind,
            "size_total": size_total,
            "size_total_human": _human_bytes(size_total),
        }

    @staticmethod
    def human_bytes(n):
        return _human_bytes(n)
