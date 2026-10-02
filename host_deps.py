# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Dependencias de virtualización del host: OSX-KVM, OVMF/UEFI, KVM/TPM,
detección de GPU y el chequeo previo de passthrough PCI/VFIO.

Funciones puras que devuelven strings/dicts describiendo el estado del
host; quien las llama decide cómo mostrarlo (log, diálogo, etc.) via el
parámetro log_func, no acoplan nada de PyQt aquí.
"""
import os
import re
import json
import shutil
import shlex
import glob
import zipfile
import configparser
import subprocess
import uuid
import time
from pathlib import Path
from datetime import date, timedelta
import requests
from packaging import version

def ensure_osx_kvm_present(log_func=print):
    """Si la carpeta 'OSX-KVM' no existe, la descarga desde
    https://github.com/kholia/OSX-KVM y la descomprime en OSX_KVM_DIR.

    Marcador: xdg_osx_kvm_v1. La ruta destino la decide vm_config
    (respeta XDG cuando la app esta instalada en /usr/).
    """
    # Import diferido para no crear dependencia circular con vm_config.
    try:
        from vm_config import OSX_KVM_DIR as target_dir
    except Exception:
        target_dir = os.path.join(os.getcwd(), "OSX-KVM")

    if os.path.isdir(target_dir):
        return

    parent_dir = os.path.dirname(target_dir) or os.getcwd()
    os.makedirs(parent_dir, exist_ok=True)

    log_func("==> Carpeta 'OSX-KVM' no encontrada. Descargando desde GitHub (kholia/OSX-KVM)...")
    zip_url = "https://github.com/kholia/OSX-KVM/archive/refs/heads/master.zip"
    zip_path = os.path.join(parent_dir, "_osxkvm_download.zip")
    try:
        r = requests.get(zip_url, timeout=60, stream=True)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        log_func("==> Descarga completa. Descomprimiendo...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(parent_dir)

        extracted_dir = os.path.join(parent_dir, "OSX-KVM-master")
        if not os.path.isdir(extracted_dir):
            raise RuntimeError("No se encontró la carpeta 'OSX-KVM-master' tras descomprimir.")
        shutil.move(extracted_dir, target_dir)
        log_func("==> 'OSX-KVM' lista para usarse.")
    finally:
        if os.path.isfile(zip_path):
            os.remove(zip_path)


def _read_os_release():
    info = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                info[k] = v.strip().strip('"')
    except OSError:
        pass
    return info


def detect_linux_package_manager():
    """Detecta la familia de distribución y el gestor de paquetes disponible."""
    info = _read_os_release()
    ids = {info.get("ID", "").lower()}
    ids.update(x.strip().lower() for x in info.get("ID_LIKE", "").split())
    candidates = [
        ("apt", ["apt-get"], {"debian", "ubuntu", "linuxmint", "pop", "elementary", "zorin"}),
        ("dnf", ["dnf"], {"fedora", "rhel", "centos", "rocky", "almalinux"}),
        ("pacman", ["pacman"], {"arch", "manjaro", "cachyos", "endeavouros"}),
        ("zypper", ["zypper"], {"opensuse", "suse"}),
        ("apk", ["apk"], {"alpine"}),
    ]
    for manager, binaries, families in candidates:
        if ids & families and any(shutil.which(b) for b in binaries):
            return manager, info
    for manager, binaries, _ in candidates:
        if any(shutil.which(b) for b in binaries):
            return manager, info
    return None, info


def _run_privileged_install(command, log_func=print):
    """Ejecuta una instalación con privilegios. Prefiere pkexec para mostrar
    una ventana gráfica de autenticación y usa sudo como respaldo."""
    if os.geteuid() == 0:
        cmd = command
    elif shutil.which("pkexec"):
        cmd = ["pkexec"] + command
    elif shutil.which("sudo"):
        cmd = ["sudo"] + command
    else:
        raise RuntimeError("No se encontró pkexec ni sudo para instalar paquetes con privilegios.")

    log_func("==> Instalando dependencias: " + " ".join(command))
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError("La instalación de dependencias fue cancelada o falló.")


def find_ovmf_files(secure_boot=False):
    """Busca una pareja OVMF CODE/VARS compatible, incluyendo nombres usados por Arch/CachyOS."""
    if secure_boot:
        code_patterns = [
            "OVMF_CODE_4M.secboot.fd", "OVMF_CODE.secboot.fd",
            "OVMF_CODE.secboot.4m.fd", "OVMF_CODE.4m.secboot.fd",
            "OVMF_CODE_4M.ms.fd", "OVMF_CODE.ms.fd", "OVMF_CODE.4MB.ms.fd",
            "OVMF_CODE.4MB.fd",
        ]
        vars_patterns = [
            "OVMF_VARS_4M.ms.fd", "OVMF_VARS.ms.fd",
            "OVMF_VARS.4m.ms.fd", "OVMF_VARS.4MB.ms.fd",
            "OVMF_VARS_4M.secboot.fd", "OVMF_VARS.secboot.fd",
            "OVMF_VARS.secboot.4m.fd",
        ]
        # Algunas distribuciones (incluidas variantes Arch) entregan el CODE
        # Secure Boot junto a un VARS 4M genérico. Ese VARS es válido como
        # plantilla, aunque Secure Boot queda sin claves hasta que se inscriban.
        generic_vars_patterns = [
            "OVMF_VARS_4M.fd", "OVMF_VARS.4m.fd", "OVMF_VARS.4MB.fd",
            "OVMF_VARS.fd",
        ]
    else:
        code_patterns = ["OVMF_CODE_4M.fd", "OVMF_CODE.fd", "OVMF_CODE.4m.fd", "OVMF_CODE.4MB.fd"]
        vars_patterns = [
            "OVMF_VARS_4M.fd", "OVMF_VARS.fd", "OVMF_VARS.4m.fd", "OVMF_VARS.4MB.fd",
            "OVMF_VARS-1920x1080.fd", "OVMF_VARS-1024x768.fd",
        ]
        generic_vars_patterns = []

    roots = [
        "/usr/share/OVMF", "/usr/share/edk2/ovmf", "/usr/share/edk2/x64",
        "/usr/share/edk2/ovmf-4m", "/usr/share/edk2/x64/ovmf", "/usr/share/edk2-ovmf/x64",
        "/usr/share/edk2-ovmf", "/usr/share/qemu", "/usr/lib/edk2/ovmf",
        "/usr/lib/edk2/x64", "/usr/lib/qemu", "/usr/libexec/edk2", "/usr/libexec/qemu",
    ]
    search_dirs = [d for d in roots if os.path.isdir(d)]
    # Importante: no hacemos búsquedas recursivas por todo /usr/share y /usr/lib
    # durante el arranque. Eso hacía que la interfaz tardara varios segundos en aparecer.
    # Las rutas habituales de OVMF/EDK2 están cubiertas arriba y añadimos solo
    # directorios inmediatos relacionados con edk2/qemu.
    for base in ("/usr/share/edk2", "/usr/share/edk2-ovmf", "/usr/share/OVMF",
                 "/usr/lib/edk2", "/usr/lib/edk2-ovmf", "/usr/lib/OVMF"):
        if os.path.isdir(base):
            try:
                for entry in os.listdir(base):
                    candidate_dir = os.path.join(base, entry)
                    if os.path.isdir(candidate_dir):
                        search_dirs.append(candidate_dir)
            except OSError:
                pass

    # OSX-KVM solo aporta OVMF normal; no se debe usar como Secure Boot.
    # xdg_osx_kvm_v1: leer de la ruta XDG si esta definida.
    try:
        from vm_config import OSX_KVM_DIR as _osx_dir
        local_osx = _osx_dir
    except Exception:
        local_osx = os.path.abspath("OSX-KVM")
    if os.path.isdir(local_osx) and not secure_boot:
        search_dirs.extend([
            os.path.join(local_osx, "OVMF_CODE_4M.fd"),
            os.path.join(local_osx, "OVMF_CODE.fd"),
            os.path.join(local_osx, "OVMF_VARS-1920x1080.fd"),
            os.path.join(local_osx, "OVMF_VARS-1024x768.fd"),
            os.path.join(local_osx, "OVMF_VARS.fd"),
        ])

    # Unimos los nombres posibles que pueden aparecer en CODE/VARS.
    # La versión anterior referenciaba `all_patterns` sin definirlo, lo que
    # provocaba el error al pulsar "Comprobar dependencias".
    all_patterns = list(dict.fromkeys(
        code_patterns + vars_patterns + generic_vars_patterns
    ))

    files = []
    for item in search_dirs:
        if os.path.isfile(item):
            files.append(item)
        elif os.path.isdir(item):
            for pattern in all_patterns:
                candidate = os.path.join(item, pattern)
                if os.path.isfile(candidate):
                    files.append(candidate)

    # El orden de los patrones manda: preferimos MS-enrolled para Win11.
    def first_matching(patterns):
        for pattern in patterns:
            for path in files:
                if os.path.basename(path) == pattern:
                    return path
        return None

    code = first_matching(code_patterns)
    vars_template = first_matching(vars_patterns)
    if secure_boot and code and not vars_template:
        vars_template = first_matching(generic_vars_patterns)
    return code, vars_template


def ovmf_available(secure_boot=False):
    code, vars_template = find_ovmf_files(secure_boot=secure_boot)
    return bool(code and vars_template)


def _detect_host_graphics_uncached():
    """Detecta GPU, OpenGL, Vulkan, VirGL y VFIO sin depender de una GPU concreta."""
    gpu = "No detectada"
    vendors = []
    if shutil.which("lspci"):
        try:
            r = subprocess.run(["lspci", "-nn"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                low = line.lower()
                if "vga compatible controller" in low or "3d controller" in low or "display controller" in low:
                    vendors.append(line.strip())
            if vendors:
                gpu = " | ".join(vendors[:2])
        except Exception:
            pass

    opengl = False
    if shutil.which("glxinfo"):
        try:
            r = subprocess.run(["glxinfo", "-B"], capture_output=True, text=True, timeout=5)
            opengl = r.returncode == 0 and "OpenGL" in r.stdout
        except Exception:
            pass
    vulkan = bool(shutil.which("vulkaninfo"))
    if vulkan:
        try:
            r = subprocess.run(["vulkaninfo", "--summary"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7)
            vulkan = r.returncode == 0
        except Exception:
            vulkan = False

    virgl = False
    if shutil.which("ldconfig"):
        try:
            r = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True, timeout=5)
            virgl = "libvirglrenderer" in r.stdout
        except Exception:
            pass
    vfio = os.path.exists("/sys/module/vfio") or os.path.exists("/dev/vfio")
    return {"gpu": gpu, "opengl": opengl, "vulkan": vulkan, "virgl": virgl, "vfio": vfio}


# ---------------------------------------------------------------------------
# Caché de las sondas del host (GPU, OpenGL, Vulkan, capacidades de QEMU).
# Lanzan varios subprocesos (lspci, glxinfo, vulkaninfo, qemu -device help...)
# y su resultado no cambia mientras la app está abierta; repetirlas en cada clic
# de la lista de VMs congelaba la interfaz. La caché se invalida sola cuando
# cambia el binario de QEMU o /etc/ld.so.cache (se regenera al instalar o
# actualizar paquetes).
# ---------------------------------------------------------------------------
import threading as _threading

_CAPS_LOCK = _threading.Lock()
_CAPS_CACHE = {}


def _fingerprint(*paths):
    out = []
    for path in paths:
        try:
            out.append(os.stat(path).st_mtime_ns)
        except (OSError, TypeError):
            out.append(0)
    return tuple(out)


# ---------------------------------------------------------------------------
# Persistencia en disco de la caché de sondas del host.
# ---------------------------------------------------------------------------
# Las sondas del host (lspci, glxinfo, vulkaninfo, qemu -device help,
# etc.) lanzan varios subprocesos que tardan cientos de milisegundos. Su
# resultado no cambia entre ejecuciones de la app salvo que el usuario
# actualice QEMU o las librerías del sistema. Persistimos el resultado en
# ~/.cache/virtual-machine/qemu_caps.json con TTL 24h; el fingerprint
# (mtime del binario de QEMU y /etc/ld.so.cache) invalida la caché
# automáticamente cuando algo cambia.
_DISK_CACHE_PATH = Path.home() / ".cache" / "virtual-machine" / "qemu_caps.json"
_DISK_CACHE_TTL = 24 * 3600
_DISK_CACHE_LOADED = False


def _load_disk_cache():
    global _DISK_CACHE_LOADED
    if _DISK_CACHE_LOADED:
        return
    _DISK_CACHE_LOADED = True
    try:
        if not _DISK_CACHE_PATH.is_file():
            return
        data = json.loads(_DISK_CACHE_PATH.read_text(encoding="utf-8"))
        if data.get("version") != 1:
            return
        if (time.time() - float(data.get("saved_at", 0))) > _DISK_CACHE_TTL:
            return
        entries = data.get("entries") or {}
        with _CAPS_LOCK:
            for name, entry in entries.items():
                fp = entry.get("fingerprint")
                val = entry.get("value")
                if fp is None or val is None:
                    continue
                _CAPS_CACHE[name] = (tuple(fp), val)
    except Exception:
        # Cualquier problema con el archivo de caché (JSON roto, permisos,
        # versión desconocida) se ignora sin más: el peor caso es que se
        # vuelvan a ejecutar las sondas.
        pass


def _save_disk_cache():
    try:
        _DISK_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CAPS_LOCK:
            entries = {
                k: {"fingerprint": list(v[0]), "value": v[1]}
                for k, v in _CAPS_CACHE.items()
            }
        payload = {
            "version": 1,
            "saved_at": time.time(),
            "entries": entries,
        }
        _DISK_CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _cached_probe(name, fingerprint, producer, force=False):
    # Intentar cargar la caché de disco la primera vez que se llama.
    _load_disk_cache()
    # El lock se mantiene durante el cálculo: si el hilo de precalentamiento
    # está midiendo, el hilo de la GUI espera su resultado en vez de duplicarlo.
    with _CAPS_LOCK:
        hit = _CAPS_CACHE.get(name)
        if hit is not None and not force and hit[0] == fingerprint:
            return hit[1]
        value = producer()
        _CAPS_CACHE[name] = (fingerprint, value)
    # Guardar fuera del lock para no serializar durante la escritura.
    _save_disk_cache()
    return value


def detect_host_graphics(force=False):
    """GPU, OpenGL, Vulkan, VirGL y VFIO del host (con caché; force=True la ignora)."""
    data = dict(_cached_probe("host_graphics", _fingerprint("/etc/ld.so.cache"),
                              _detect_host_graphics_uncached, force))
    # VFIO es una comprobación barata de rutas: siempre fresca.
    data["vfio"] = os.path.exists("/sys/module/vfio") or os.path.exists("/dev/vfio")
    return data


def qemu_graphics_capabilities(force=False):
    """Capacidades gráficas de QEMU: dispositivos virtio-gpu/virgl y displays gtk/sdl."""
    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        return {"qemu_path": None, "virtio": False, "virgl": False, "display_gl": False}

    def _probe():
        res = {"qemu_path": qemu, "virtio": False, "virgl": False, "display_gl": False}
        try:
            r = subprocess.run([qemu, "-device", "help"], capture_output=True, text=True, timeout=5)
            devices = r.stdout or ""
            res["virtio"] = "virtio-vga" in devices or "virtio-gpu" in devices
            res["virgl"] = "virtio-vga-gl" in devices or "virtio-gpu-gl" in devices
        except Exception:
            pass
        try:
            r = subprocess.run([qemu, "-display", "help"], capture_output=True, text=True, timeout=5)
            text = (r.stdout or "") + (r.stderr or "")
            res["display_gl"] = bool(re.search(r"\bgtk\b", text, re.IGNORECASE) or
                                     re.search(r"\bsdl\b", text, re.IGNORECASE))
        except Exception:
            pass
        return res

    fp = _fingerprint(qemu, "/etc/ld.so.cache")
    return dict(_cached_probe("qemu_graphics:" + qemu, fp, _probe, force))


def prewarm_host_capabilities():
    """Rellena la caché en un hilo de fondo (llamar al arrancar la app)."""
    def _run():
        for fn in (detect_host_graphics, qemu_graphics_capabilities):
            try:
                fn()
            except Exception:
                pass
    th = _threading.Thread(target=_run, name="host-caps-prewarm", daemon=True)
    th.start()
    return th



def get_virtualization_dependency_status():
    """Devuelve el estado local de las dependencias principales."""
    qemu = shutil.which("qemu-system-x86_64")
    swtpm = shutil.which("swtpm")
    kvm = os.path.exists("/dev/kvm")
    virtio = any(os.path.exists(x) for x in (
        "/sys/module/virtio",
        "/sys/module/virtio_pci",
        "/sys/module/virtio_blk",
    ))
    code, vars_template = find_ovmf_files(False)
    secure_code, secure_vars = find_ovmf_files(True)
    manager, info = detect_linux_package_manager()
    return {
        "qemu": bool(qemu),
        "qemu_path": qemu or "",
        "kvm": kvm,
        "ovmf": bool(code and vars_template),
        "ovmf_code_path": code or "",
        "ovmf_vars_path": vars_template or "",
        "secure_boot": bool(secure_code and secure_vars),
        "secure_boot_code_path": secure_code or "",
        "secure_boot_vars_path": secure_vars or "",
        "swtpm": bool(swtpm),
        "swtpm_path": swtpm or "",
        "virtio": virtio,
        "audio": bool(shutil.which("pactl") and os.path.exists("/dev/snd")) or bool(shutil.which("aplay") and os.path.exists("/dev/snd")),
        "audio_backend": "PulseAudio/PipeWire" if shutil.which("pactl") else ("ALSA" if shutil.which("aplay") else "No detectado"),
        "graphics": detect_host_graphics(force=True),
        "package_manager": manager or "No detectado",
        "distro": info.get("PRETTY_NAME") or info.get("ID") or "Linux",
    }

def ensure_virtualization_dependencies(need_ovmf=False, need_swtpm=False, need_secure_boot=False, log_func=print):
    """Comprueba OVMF/swtpm y, si faltan, intenta instalarlos automáticamente."""
    missing = []
    if need_ovmf and not ovmf_available(False):
        missing.append("ovmf")
    if need_secure_boot and not ovmf_available(True):
        if "ovmf" not in missing:
            missing.append("ovmf")
    if need_swtpm and shutil.which("swtpm") is None:
        missing.append("swtpm")

    if not missing:
        return

    manager, info = detect_linux_package_manager()
    distro = info.get("PRETTY_NAME") or info.get("ID") or "Linux"
    if not manager:
        raise RuntimeError(
            f"No pude detectar el gestor de paquetes de {distro}. "
            f"Faltan: {', '.join(missing)}."
        )

    package_map = {
        "apt": {"ovmf": "ovmf", "swtpm": "swtpm"},
        "dnf": {"ovmf": "edk2-ovmf", "swtpm": "swtpm"},
        "pacman": {"ovmf": "edk2-ovmf", "swtpm": "swtpm"},
        "zypper": {"ovmf": "qemu-ovmf-x86_64", "swtpm": "swtpm"},
        "apk": {"ovmf": "edk2-ovmf", "swtpm": "swtpm"},
    }
    if manager not in package_map:
        raise RuntimeError(f"El gestor '{manager}' aún no tiene nombres de paquetes configurados.")
    packages = [package_map[manager][item] for item in missing]

    if manager == "apt":
        _run_privileged_install(["apt-get", "update"], log_func)
        _run_privileged_install(["apt-get", "install", "-y"] + packages, log_func)
    elif manager == "dnf":
        _run_privileged_install(["dnf", "install", "-y"] + packages, log_func)
    elif manager == "pacman":
        _run_privileged_install(["pacman", "-Sy", "--noconfirm"] + packages, log_func)
    elif manager == "zypper":
        _run_privileged_install(["zypper", "--non-interactive", "install"] + packages, log_func)
    elif manager == "apk":
        _run_privileged_install(["apk", "add"] + packages, log_func)

    if need_swtpm and shutil.which("swtpm") is None:
        raise RuntimeError("La instalación terminó, pero 'swtpm' todavía no está disponible.")
    if need_ovmf and not ovmf_available(False):
        raise RuntimeError(
            "OVMF se instaló (o el gestor terminó sin error), pero no se encontró una pareja "
            "OVMF_CODE/OVMF_VARS compatible. Se revisaron las rutas habituales y la carpeta OSX-KVM."
        )
    if need_secure_boot and not ovmf_available(True):
        raise RuntimeError(
            "Se necesita OVMF con Secure Boot, pero no se encontró una plantilla CODE/VARS "
            "con soporte de claves Secure Boot."
        )


def pci_preflight_host(selected):
    """Preflight PCI/VFIO independiente de la interfaz gráfica.
    Se ejecuta en InstallWorker sin depender de métodos de VirtualMachineManagerApp.
    No hace bind/unbind: solo verifica IOMMU, grupos y driver actual.
    """
    cmdline = ""
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        pass
    groups = sorted(
        glob.glob("/sys/kernel/iommu_groups/[0-9]*"),
        key=lambda x: int(os.path.basename(x)) if os.path.basename(x).isdigit() else 0,
    )
    iommu_classes = glob.glob("/sys/class/iommu/*")
    dmar = os.path.exists("/sys/firmware/acpi/tables/DMAR") or os.path.exists("/sys/firmware/acpi/tables/data/DMAR")
    iommu_on = bool(re.search(r"(?:^|\s)(?:intel_iommu=on|iommu=on)(?:\s|$)", cmdline))
    iommu_off = bool(re.search(r"(?:^|\s)(?:intel_iommu=off|iommu=off)(?:\s|$)", cmdline))
    active = bool(groups or iommu_classes)
    if iommu_off:
        state = "Desactivado por parámetro del kernel"
    elif active and (dmar or iommu_on or iommu_classes):
        state = "Activo"
    elif dmar:
        state = "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles"
    else:
        state = "No detectado"

    details = []
    bad = []
    for d in selected or []:
        if d.get("kind") != "pci":
            continue
        addr = str(d.get("address") or "").strip()
        if not addr:
            continue
        link = f"/sys/bus/pci/devices/{addr}/iommu_group"
        group = None
        try:
            if os.path.islink(link):
                group = int(os.path.basename(os.path.realpath(link)))
        except Exception:
            pass
        driver = str(d.get("driver") or "").strip()
        if not driver:
            drvlink = f"/sys/bus/pci/devices/{addr}/driver"
            try:
                if os.path.islink(drvlink):
                    driver = os.path.basename(os.path.realpath(drvlink))
            except Exception:
                pass
        members = []
        if group is not None:
            base = f"/sys/kernel/iommu_groups/{group}/devices"
            members = [os.path.basename(x) for x in sorted(glob.glob(os.path.join(base, "*")))]
        shared = [x for x in members if x != addr]
        if group is None:
            bad.append(f"{addr}: no tiene grupo IOMMU ({driver or 'sin driver'})")
        elif shared:
            bad.append(f"{addr}: comparte grupo IOMMU {group} con {', '.join(shared)}")
        elif driver != "vfio-pci":
            bad.append(f"{addr}: driver actual {driver or 'sin driver'}; todavía no está ligado a vfio-pci")
        details.append(f"• {addr} | grupo {group if group is not None else '—'} | driver {driver or 'sin driver'}")
    diag = {
        "state": state, "firmware": "Detectado" if dmar else "No confirmado",
        "groups": groups, "iommu_classes": iommu_classes,
        "cmdline": cmdline, "intel_iommu_on": iommu_on, "intel_iommu_off": iommu_off,
        "dmar": dmar, "active": active,
    }
    return diag, bad, "\n".join(details)


