"""
Servicio de detección de información del sistema anfitrión (Host).
"""
import os
import re
import time
import shutil
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def _read(path: str, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return default


def _run(cmd, timeout: float = 2.0) -> str:
    try:
        return subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=timeout, text=True
        ).strip()
    except Exception:
        return ""


def _which(name: str) -> bool:
    return shutil.which(name) is not None


# ======================================================================
# SOFTWARE
# ======================================================================
def detect_kde_plasma() -> str:
    out = _run(["plasmashell", "--version"])
    m = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", out)
    if m: return m.group(1)
    if _which("pacman"):
        for pkg in ("plasmashell", "plasma-desktop", "plasma-meta"):
            out = _run(["pacman", "-Q", pkg])
            m = re.search(r"\s([0-9][^\s]*)", out)
            if m: return m.group(1)
    return ""


def detect_kde_frameworks() -> str:
    if IS_WINDOWS:
        return ""
    for binary in ("kf6-config", "kf5-config"):
        if _which(binary):
            out = _run([binary, "--version"])
            m = re.search(r"(\d+\.\d+\.\d+)", out)
            if m: return m.group(1)
    for path in (
        "/usr/lib/cmake/KF6Core/KF6CoreConfigVersion.cmake",
        "/usr/lib64/cmake/KF6Core/KF6CoreConfigVersion.cmake",
        "/usr/lib/cmake/KF5CoreAddons/KF5CoreAddonsConfigVersion.cmake",
    ):
        if Path(path).exists():
            content = _read(path)
            m = re.search(r'PACKAGE_VERSION\s+"([^"]+)"', content)
            if m: return m.group(1)
    if _which("pacman"):
        for pkg in ("kf6-kcoreaddons", "kf5-kcoreaddons", "kf6-frameworks", "kf5-frameworks"):
            out = _run(["pacman", "-Q", pkg])
            m = re.search(r"\s([0-9][^\s]*)", out)
            if m: return m.group(1)
    return ""


def detect_gtk_version() -> str:
    if IS_WINDOWS:
        return ""
    if _which("pacman"):
        for pkg in ("gtk4", "gtk3"):
            out = _run(["pacman", "-Q", pkg])
            if out:
                return out.split()[-1]
    return ""


def detect_desktop_environment() -> Dict[str, str]:
    """Detecta dinámicamente el entorno de escritorio."""
    de_name = "Desconocido"
    de_version = ""
    de_extra = ""

    if IS_WINDOWS:
        de_name = "Windows"
        de_version = platform.version() or platform.release()
        de_extra = f"Build {platform.release()}"
        return {"name": de_name, "version": de_version, "extra": de_extra}

    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()

    if "KDE" in desktop or "PLASMA" in desktop:
        de_name = "KDE Plasma"
        de_version = detect_kde_plasma()
        fw = detect_kde_frameworks()
        if fw: de_extra = f"KDE Frameworks {fw}"
    elif "GNOME" in desktop:
        de_name = "GNOME"
        out = _run(["gnome-shell", "--version"])
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", out)
        if m: de_version = m.group(1)
        gtk = detect_gtk_version()
        if gtk: de_extra = f"GTK {gtk}"
    elif "CINNAMON" in desktop:
        de_name = "Cinnamon"
        out = _run(["cinnamon", "--version"])
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", out)
        if m: de_version = m.group(1)
        gtk = detect_gtk_version()
        if gtk: de_extra = f"GTK {gtk}"
    elif "XFCE" in desktop:
        de_name = "XFCE"
        out = _run(["xfce4-session", "--version"])
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", out)
        if m: de_version = m.group(1)
        gtk = detect_gtk_version()
        if gtk: de_extra = f"GTK {gtk}"
    elif "MATE" in desktop:
        de_name = "MATE"
        out = _run(["mate-session", "--version"])
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", out)
        if m: de_version = m.group(1)

    return {"name": de_name, "version": de_version, "extra": de_extra}


def detect_qt_version() -> str:
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        return QT_VERSION_STR
    except Exception:
        return ""


def detect_kernel() -> str:
    if IS_WINDOWS:
        return platform.version() or platform.release()
    return platform.release()


def detect_graphics_platform() -> str:
    if IS_WINDOWS:
        return "Windows (DirectX/DXGI)"
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session == "wayland": return "Wayland"
    if session == "x11": return "X11"
    if os.environ.get("WAYLAND_DISPLAY"): return "Wayland"
    if os.environ.get("DISPLAY"): return "X11"
    return session.capitalize() if session else "Desconocida"


def detect_distro() -> Dict[str, str]:
    result = {"pretty": "", "id": "", "version": ""}
    if IS_WINDOWS:
        result["pretty"] = f"Windows {platform.release()}"
        result["id"] = "windows"
        result["version"] = platform.version() or platform.release()
        return result
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" not in line: continue
                k, v = line.strip().split("=", 1)
                v = v.strip('"')
                if k == "PRETTY_NAME": result["pretty"] = v
                elif k == "ID": result["id"] = v
                elif k == "VERSION_ID": result["version"] = v
    except Exception:
        pass
    return result


# ======================================================================
# HARDWARE
# ======================================================================
def detect_cpu() -> Dict:
    info = {"model": "", "logical": 0, "physical": 0, "mhz": ""}
    if IS_WINDOWS:
        try:
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                info["model"] = cpu.Name.strip()
                info["logical"] = cpu.NumberOfLogicalProcessors or 0
                info["physical"] = cpu.NumberOfCores or 0
                info["mhz"] = str(cpu.MaxClockSpeed or "")
                break
        except Exception:
            # Fallback sin wmi
            info["logical"] = os.cpu_count() or 0
            info["physical"] = info["logical"] // 2 if info["logical"] else 0
        return info
    try:
        with open("/proc/cpuinfo") as f:
            cpus = []
            current = {}
            for raw in f:
                line = raw.strip()
                if not line:
                    if current: cpus.append(current); current = {}
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    current[k.strip()] = v.strip()
            if current: cpus.append(current)

        if cpus:
            info["model"] = cpus[0].get("model name", "")
            info["mhz"] = cpus[0].get("cpu MHz", "")
            info["logical"] = len(cpus)
            cores = set()
            for c in cpus:
                cores.add((c.get("physical id", "0"), c.get("core id", "0")))
            info["physical"] = len(cores) if cores else len(cpus)
    except Exception as e:
        log.error(f"Error leyendo /proc/cpuinfo: {e}")
    return info


def detect_memory() -> Dict:
    info = {"total_kb": 0, "available_kb": 0, "used_kb": 0, "physical_kb": 0}
    if IS_WINDOWS:
        try:
            import wmi
            c = wmi.WMI()
            for mem in c.Win32_PhysicalMemory():
                info["total_kb"] += int(int(mem.Capacity) // 1024)
            for os_info in c.Win32_OperatingSystem():
                info["available_kb"] = int(int(os_info.FreePhysicalMemory) // 1) if os_info.FreePhysicalMemory else 0
            info["used_kb"] = max(0, info["total_kb"] - info["available_kb"])
        except Exception:
            # Fallback usando psutil si está disponible
            try:
                import psutil
                vm = psutil.virtual_memory()
                info["total_kb"] = vm.total // 1024
                info["available_kb"] = vm.available // 1024
                info["used_kb"] = vm.used // 1024
            except Exception:
                pass
        return info
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" not in line: continue
                k, v = line.split(":", 1)
                v = v.strip().split()[0] if v.strip() else "0"
                try: val = int(v)
                except ValueError: continue
                if k == "MemTotal": info["total_kb"] = val
                elif k == "MemAvailable": info["available_kb"] = val
        info["used_kb"] = max(0, info["total_kb"] - info["available_kb"])
    except Exception as e:
        log.error(f"Error leyendo /proc/meminfo: {e}")

    out = _run(["dmesg"])
    m = re.search(r"Memory:\s+\d+K/(\d+)K available", out)
    if m: info["physical_kb"] = int(m.group(1))
    return info


def detect_gpu() -> str:
    if IS_WINDOWS:
        try:
            import wmi
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                return gpu.Name.strip() or "Desconocida"
        except Exception:
            return "Desconocida"
    if _which("lspci"):
        out = _run(["lspci", "-nn"])
        for line in out.splitlines():
            if any(k in line for k in ("VGA compatible controller", "3D controller", "Display controller")):
                after = line.split(":", 1)[-1].strip()
                after = re.sub(r"\s*\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]", "", after)
                after = re.sub(r"\s*\(rev [0-9a-fA-F]+\)", "", after)
                return after.strip()
    return "Desconocida"


def detect_dmi(field: str) -> str:
    if IS_WINDOWS:
        try:
            import wmi
            c = wmi.WMI()
            if field == "sys_vendor":
                for cs in c.Win32_ComputerSystem():
                    return cs.Manufacturer or "—"
            elif field == "product_name":
                for cs in c.Win32_ComputerSystem():
                    return cs.Model or "—"
            elif field == "product_serial":
                for bios in c.Win32_BIOS():
                    return bios.SerialNumber or "—"
        except Exception:
            pass
        return "—"
    return _read(f"/sys/devices/virtual/dmi/id/{field}")


# ======================================================================
# AGREGACIÓN + CACHÉ
# ======================================================================
_CACHE: Dict = {"data": None, "ts": 0.0, "ttl": 20.0}


def _gather() -> Dict:
    cpu = detect_cpu()
    mem = detect_memory()
    distro = detect_distro()
    de = detect_desktop_environment()

    return {
        # --- Software ---
        "distro_name": distro["pretty"] or f"{platform.system()} {platform.release()}",
        "de_name": de["name"],
        "de_version": de["version"],
        "de_extra": de["extra"],
        "qt_version": detect_qt_version() or "—",
        "kernel": detect_kernel() or "—",
        "graphics_platform": detect_graphics_platform(),
        # --- Hardware ---
        "cpu_model": cpu["model"],
        "cpu_logical": cpu["logical"],
        "cpu_physical": cpu["physical"],
        "cpu_mhz": cpu["mhz"],
        "ram_total_kb": mem["total_kb"],
        "ram_available_kb": mem["available_kb"],
        "ram_used_kb": mem["used_kb"],
        "ram_physical_kb": mem["physical_kb"],
        "gpu": detect_gpu(),
        "manufacturer": detect_dmi("sys_vendor") or "—",
        "product_name": detect_dmi("product_name") or "—",
        "serial_number": detect_dmi("product_serial") or "—",
        "hostname": platform.node() or "—",
        "arch": platform.machine() or "—",
    }


def get_host_info(force: bool = False) -> Dict:
    now = time.time()
    if not force and _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE["ttl"]:
        return _CACHE["data"]

    data = _gather()
    _CACHE["data"] = data
    _CACHE["ts"] = now
    return data


def invalidate_cache():
    _CACHE["data"] = None
    _CACHE["ts"] = 0.0


# ======================================================================
# FORMATEADORES
# ======================================================================
def fmt_kb_to_gib(kb: int) -> str:
    if not kb: return "—"
    return f"{kb / (1024 * 1024):.1f} GiB"


def fmt_cpu(info: Dict, tr=None) -> str:
    model = (info.get("cpu_model") or "").strip()
    model = re.sub(r"\s+", " ", model)
    model = model.replace("(R)", "").replace("(TM)", "").replace("(tm)", "")
    model = re.sub(r"\s+", " ", model).strip()
    logical = info.get("cpu_logical", 0)
    if logical and model:
        return f"{logical} × {model}"
    if not model:
        return tr("Desconocido") if tr else "Desconocido"
    return model


def fmt_memory(info: Dict, tr=None) -> str:
    total_kb = info.get("ram_total_kb", 0)
    physical_kb = info.get("ram_physical_kb", 0)
    used_kb = info.get("ram_used_kb", 0)

    if not total_kb: return "—"
    total_gib = total_kb / (1024 * 1024)
    used_gib = used_kb / (1024 * 1024)

    plantilla = "{:.1f} GiB totales · {:.1f} GiB en uso"
    if physical_kb and physical_kb > total_kb * 1.01:
        plantilla = "{:.1f} GiB de RAM ({:.1f} GiB utilizables) · {:.1f} GiB en uso"
        return (tr(plantilla) if tr else plantilla).format(
            physical_kb / (1024 * 1024), total_gib, used_gib)
    return (tr(plantilla) if tr else plantilla).format(total_gib, used_gib)