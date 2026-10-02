# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Panel de Sugerencias: analiza el estado de una VM y propone acciones
concretas al usuario (disco lleno, snapshot antiguo, RAM excesiva, etc.).

Diseño:
- La lógica pura está en `compute_suggestions(vm_dir)` que NO depende de PyQt
  y puede testearse con un `tmpdir`.
- `SuggestionsMixin` aporta la parte UI: crea el widget, lo refresca desde
  el timer de estado, y se integra con el panel derecho.
"""
import os
import time

from vm_config import load_vm_config


# Umbrales configurables (constantes, no hardcodeados en la lógica).
DISK_WARN_PCT = 85
DISK_CRIT_PCT = 95
SNAPSHOT_OLD_DAYS = 30
SNAPSHOT_MANY_COUNT = 5
RAM_HOST_MAX_PCT = 50
VM_IDLE_DAYS = 90
LOG_WARN_SIZE_MB = 50


def _fmt_size(n_bytes):
    """Formato compacto de bytes: 12.3 GB, 456 MB, etc."""
    try:
        n = float(n_bytes)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


def _disk_usage_for(vm_dir):
    """Devuelve (used_pct, free_bytes, total_bytes) del filesystem donde vive la VM."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(vm_dir)
        pct = (used / total * 100.0) if total else 0.0
        return pct, free, total
    except Exception:
        return None, None, None


def _snapshot_info(vm_dir):
    """Devuelve (age_days, count, total_bytes) del conjunto de snapshots.
    age_days es la edad del más reciente. Devuelve (None, 0, 0) si no hay."""
    snapshot_dir = os.path.join(vm_dir, "snapshots")
    if not os.path.isdir(snapshot_dir):
        return None, 0, 0
    pngs = []
    total = 0
    try:
        for f in os.listdir(snapshot_dir):
            if f.endswith(".png"):
                p = os.path.join(snapshot_dir, f)
                pngs.append((p, os.path.getmtime(p)))
                total += os.path.getsize(p)
    except Exception:
        return None, 0, 0
    if not pngs:
        return None, 0, 0
    latest = max(t for _, t in pngs)
    return (time.time() - latest) / 86400.0, len(pngs), total


def _host_ram_gb():
    """RAM total del host en GB, o None si no se pudo detectar."""
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    return int(line.split()[1]) / (1024 * 1024)
    except Exception:
        pass
    return None


def _check_iommu_active():
    """¿Está IOMMU activo? Lee /sys/kernel/iommu_groups y /proc/cmdline."""
    try:
        if os.path.isdir("/sys/kernel/iommu_groups"):
            groups = os.listdir("/sys/kernel/iommu_groups")
            if groups:
                return True
        with open("/proc/cmdline", encoding="utf-8") as f:
            cmdline = f.read()
        if "iommu=on" in cmdline or "intel_iommu=on" in cmdline or "amd_iommu=on" in cmdline:
            return True
    except Exception:
        pass
    return False


def _log_size_mb(vm_dir):
    """Tamaño del launch.log en MB, o None si no existe."""
    log_path = os.path.join(vm_dir, "launch.log")
    if not os.path.isfile(log_path):
        return None
    try:
        return os.path.getsize(log_path) / (1024 * 1024)
    except Exception:
        return None


def compute_suggestions(vm_dir, host_ram_gb=None, tr=None):
    """Analiza el estado de una VM y devuelve una lista de tuplas (nivel, texto).

    Niveles: "info" (ℹ️), "warn" (⚠️), "ok" (✅).
    Esta función es pura (respecto a la UI): no toca PyQt. Sí lee el sistema
    de archivos y /proc, pero no modifica nada.

    i18n_tanda4a2_6_v1: recibe `tr` opcional. Si no se pasa, se identifica
    a si mismo (devuelve las cadenas en español, el idioma fuente).
    El mixin lo llama con tr=self.tr para traducir al idioma activo.
    """
    _ = tr if callable(tr) else (lambda s, *a, **k: s)
    suggestions = []

    if not vm_dir or not os.path.isdir(vm_dir):
        return [("info", _("Selecciona una VM para ver sugerencias."))]

    try:
        cfg = load_vm_config(vm_dir)
    except Exception as e:
        return [("warn", _("No se pudo leer la configuración: {0}").format(e))]

    extra = cfg.get("extra") or {}

    # ============================================================
    # 1. Disco del host donde vive la VM
    # ============================================================
    used_pct, free_bytes, _ = _disk_usage_for(vm_dir)
    if used_pct is not None:
        if used_pct >= DISK_CRIT_PCT:
            suggestions.append((
                "warn",
                _("Disco del host al {0}% — crítico. "
                  "Quedan solo {1}. Amplía el disco o mueve archivos.").format(
                      f"{used_pct:.0f}", _fmt_size(free_bytes))
            ))
        elif used_pct >= DISK_WARN_PCT:
            suggestions.append((
                "warn",
                _("Disco del host al {0}%. "
                  "Quedan {1}. Considera ampliarlo o limpiar.").format(
                      f"{used_pct:.0f}", _fmt_size(free_bytes))
            ))

    # ============================================================
    # 2. RAM configurada vs RAM del host
    # ============================================================
    try:
        ram_text = str(cfg.get("ram", "0")).upper().replace("GB", "G").replace(" ", "")
        ram_gb = float(ram_text.rstrip("G"))
        if host_ram_gb is None:
            host_ram_gb = _host_ram_gb()
        if host_ram_gb:
            pct = ram_gb / host_ram_gb * 100.0
            if pct > RAM_HOST_MAX_PCT:
                suggestions.append((
                    "warn",
                    _("RAM de la VM ({0} GB) es el {1}% de la del host "
                      "({2} GB). Riesgo de swap.").format(
                          f"{ram_gb:.0f}", f"{pct:.0f}", f"{host_ram_gb:.0f}")
                ))
    except (ValueError, AttributeError):
        pass

    # ============================================================
    # 3. Snapshots: antigüedad, cantidad, tamaño
    # ============================================================
    age_days, snap_count, snap_bytes = _snapshot_info(vm_dir)
    if age_days is not None:
        if age_days > SNAPSHOT_OLD_DAYS:
            suggestions.append((
                "info",
                _("El último snapshot tiene {0} días ({1} en total). "
                  "Puedes crear uno nuevo o limpiar los antiguos.").format(
                      f"{age_days:.0f}", snap_count)
            ))
        if snap_count >= SNAPSHOT_MANY_COUNT:
            suggestions.append((
                "warn",
                _("Hay {0} snapshots acumulados ocupando {1}. "
                  "Considera eliminar los que ya no necesites.").format(
                      snap_count, _fmt_size(snap_bytes))
            ))

    # ============================================================
    # 4. Carpetas compartidas sin Guest Agent
    # ============================================================
    folders = extra.get("shared_folders") or []
    guest_agent = bool(extra.get("guest_agent_enabled", False))
    virtio_folders = [f for f in folders if isinstance(f, dict)
                      and str(f.get("method", "")).lower() in ("auto", "virtiofs")]
    if virtio_folders and not guest_agent:
        suggestions.append((
            "info",
            _("Hay {0} carpeta(s) VirtioFS configuradas "
              "pero el Guest Agent está desactivado. Algunas funciones de "
              "automontaje no funcionarán.").format(len(virtio_folders))
        ))

    # ============================================================
    # 5. Rutas rotas en carpetas compartidas
    # ============================================================
    broken_folders = []
    for f in folders:
        if not isinstance(f, dict):
            continue
        host_path = f.get("host", "")
        if host_path and not os.path.isdir(host_path):
            broken_folders.append(f.get("guest") or host_path)
    if broken_folders:
        suggestions.append((
            "warn",
            _("{0} carpeta(s) compartida(s) apuntan a rutas "
              "que ya no existen en el host: {1}").format(
                  len(broken_folders), ', '.join(broken_folders[:3]))
            + ("..." if len(broken_folders) > 3 else "")
        ))

    # ============================================================
    # 6. IOMMU / VFIO si hay PCI passthrough configurado
    # ============================================================
    passthrough = cfg.get("passthrough_devices") or extra.get("passthrough_devices") or []
    pci_devices = [d for d in passthrough if isinstance(d, dict) and d.get("kind") == "pci"]
    if pci_devices:
        if not _check_iommu_active():
            suggestions.append((
                "warn",
                _("Hay {0} dispositivo(s) PCI en passthrough pero "
                  "IOMMU no parece estar activo en el kernel. La VM puede no arrancar.").format(len(pci_devices))
            ))

    # ============================================================
    # 7. Firmware / SO mismatch
    # ============================================================
    os_type = cfg.get("os_type", "linux")
    firmware = str(cfg.get("firmware", "bios")).lower()
    win_ver = str(extra.get("win_ver", "")).lower()
    is_win11 = (os_type == "windows" and "11" in win_ver)
    if is_win11 and firmware != "uefi":
        suggestions.append((
            "warn",
            _("Windows 11 requiere UEFI + Secure Boot. Cambia el firmware a UEFI.")
        ))
    elif os_type == "macos" and firmware != "uefi":
        suggestions.append((
            "warn",
            _("macOS/OSX-KVM requiere UEFI (OVMF). Cambia el firmware a UEFI.")
        ))

    # ============================================================
    # 8. Disco principal en formato RAW (no admite snapshots internos)
    # ============================================================
    try:
        disk_format = str(cfg.get("disk_format", "")).lower()
        if disk_format == "raw":
            suggestions.append((
                "info",
                _("El disco principal está en formato RAW. No admite snapshots internos "
                  "ni crece dinámicamente. Considera convertir a QCOW2 si necesitas snapshots.")
            ))
    except Exception:
        pass

    # ============================================================
    # 9. Log de la VM muy grande
    # ============================================================
    log_mb = _log_size_mb(vm_dir)
    if log_mb is not None and log_mb > LOG_WARN_SIZE_MB:
        suggestions.append((
            "info",
            _("El log de la VM ({0} MB) es grande. Puedes exportarlo y "
              "borrarlo desde 'Ver log completo' → 'Exportar log'.").format(
                  f"{log_mb:.0f}")
        ))

    # ============================================================
    # 10. VM apagada hace mucho tiempo
    # ============================================================
    try:
        cfg_mtime = os.path.getmtime(os.path.join(vm_dir, "vm_config.ini"))
        idle_days = (time.time() - cfg_mtime) / 86400.0
        if idle_days > VM_IDLE_DAYS:
            suggestions.append((
                "info",
                _("La configuración no se ha modificado en {0} días. "
                  "¿Sigue siendo útil esta VM?").format(f"{idle_days:.0f}")
            ))
    except Exception:
        pass

    # ============================================================
    # 11. Audio sin backend disponible en el host
    # ============================================================
    audio_device = str(cfg.get("audio_device", "")).lower()
    if audio_device and audio_device not in ("none", "off", "disabled"):
        has_backend = os.path.exists("/dev/snd")
        import shutil
        has_pactl = bool(shutil.which("pactl"))
        if not has_backend and not has_pactl:
            suggestions.append((
                "warn",
                _("La VM tiene audio configurado pero el host no tiene /dev/snd ni "
                  "PulseAudio/PipeWire (pactl). QEMU puede fallar al arrancar con audio.")
            ))

    # ============================================================
    # 12. Si no hay nada, mostrar OK
    # ============================================================
    if not suggestions:
        suggestions.append(("ok", _("Todo en orden. No hay sugerencias pendientes.")))

    return suggestions


class SuggestionsMixin:
    """Mixin que añade un panel de sugerencias contextuales al lateral derecho.

    Requiere que la clase anfitriona tenga:
    - `self.current_vm_dir` (ruta de la VM seleccionada o None)
    - `self.suggestions_label` (QLabel del panel)
    """

    def _build_suggestions_panel(self):
        """Crea el QGroupBox y el QLabel. Se llama desde _build_main_container."""
        from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel
        from PyQt6.QtCore import Qt

        box = QGroupBox(self.tr("💡 Sugerencias"))
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 8, 8, 8)
        self.suggestions_label = QLabel("—")
        self.suggestions_label.setWordWrap(True)
        self.suggestions_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.suggestions_label.setStyleSheet(
            "font-size: 11px; padding: 4px; line-height: 1.4;"
        )
        layout.addWidget(self.suggestions_label)
        return box

    def _refresh_suggestions(self):
        """Actualiza el panel con las sugerencias de la VM actual."""
        if not hasattr(self, "suggestions_label"):
            return
        try:
            suggestions = compute_suggestions(self.current_vm_dir, tr=self.tr)
        except Exception as e:
            self.suggestions_label.setText(
                f"<span style='color:#c62828;'>⚠️ Error al analizar: {e}</span>"
            )
            return

        if not suggestions:
            self.suggestions_label.setText("—")
            return

        icon_map = {"info": "ℹ️", "warn": "⚠️", "ok": "✅"}
        color_map = {
            "info": "#1565c0",
            "warn": "#b26a00",
            "ok": "#2e7d32",
        }
        parts = []
        for level, text in suggestions:
            icon = icon_map.get(level, "•")
            color = color_map.get(level, "#333")
            parts.append(f"<span style='color:{color};'>{icon} {text}</span>")
        self.suggestions_label.setText("<br><br>".join(parts))
