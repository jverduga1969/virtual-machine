# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Resolución y validación del bus de disco de QEMU.

Marcador: disk_bus_v1

Fuente única de verdad sobre:
  • Qué bus QEMU usar para un disco (según SO invitado, chipset y
    la preferencia explícita `bus_hint` del usuario).
  • Los límites reales por bus (cuántos discos admite cada tipo).
  • Etiquetas legibles para la UI.

Contexto histórico:
  Antes, workers._resolve_disk_bus_for_os() decidía el bus según el SO
  e IGNORABA la elección del usuario. Para Linux y Windows modernos
  ascendía `device="sata"` a NVMe, lo cual rompía silenciosamente los
  snapshots completos (QEMU no puede migrar el controlador `nvme`).

  Este módulo reemplaza ese comportamiento:
    • `bus_hint` explícito en storage_devices:
      "auto" | "sata" | "nvme" | "virtio-blk" | "virtio-scsi".
    • Default "auto" resuelve a SATA/AHCI (no NVMe), preservando
      compatibilidad con snapshots completos.
    • Validación previa: error claro ANTES de llegar a QEMU, en lugar
      de "Bus 'ide.6' not found" a mitad de arranque.

Marcadores relacionados: disk_bus_limits_v1, virtio_scsi_v1,
virtio_blk_v1, sata_default_all_modern_os_v1.
"""

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

# Valores aceptados en storage_devices[i]["bus_hint"].
BUS_HINT_VALUES = ("auto", "sata", "nvme", "virtio-blk", "virtio-scsi")

# Bus QEMU reales que puede devolver resolve_disk_bus_for_os().
# "floppy" y "cdrom" son casos especiales (no son "discos duros").
DISK_BUS_RESOLVED = (
    "sata_ahci", "ide", "nvme", "virtio-blk", "virtio-scsi",
    "floppy", "cdrom",
)

# Máximo de discos duros por bus (ver traspaso para la justificación).
#   • SATA/AHCI (Q35 ICH9) → 6 puertos, 2 reservados para CDs → 4 discos.
#   • IDE heredado (i440FX) → 2 canales × 1 disco.
#   • NVMe / VirtIO-BLK    → ~25 slots PCIe en Q35, reserva para GPU,
#                             audio, NIC, USB → 20 con margen.
#   • VirtIO-SCSI          → 1 controller + hasta 256 scsi-hd.
#   • Floppy               → fd0 y fd1.
DISK_BUS_LIMITS = {
    "sata_ahci":   4,
    "ide":         2,
    "nvme":        20,
    "virtio-blk":  20,
    "virtio-scsi": 256,
    "floppy":      2,
}

BUS_LABELS = {
    "sata_ahci":   "SATA/AHCI",
    "ide":         "IDE (heredado)",
    "nvme":        "NVMe",
    "virtio-blk":  "VirtIO-BLK",
    "virtio-scsi": "VirtIO-SCSI",
    "floppy":      "Disquetera",
    "cdrom":       "CD/DVD",
}


# ----------------------------------------------------------------------
# Resolución
# ----------------------------------------------------------------------

def resolve_disk_bus_for_os(os_type, win_ver="", chipset_is_q35=True,
                             devtype="sata", bus_hint="auto"):
    """Devuelve el bus QEMU real que se usará para un disco.

    Prioridad:
      1. devtype="nvme"/"floppy"/"cdrom" → siempre ese, sin importar hint
         (compatibilidad con VMs guardadas por la versión antigua).
      2. bus_hint explícito → respetado tal cual.
      3. bus_hint="auto" → tabla por SO. El default ha cambiado: ahora
         SATA/AHCI (no NVMe), para que los snapshots completos funcionen
         por defecto.

    Marcador: sata_default_all_modern_os_v1
    (reemplaza semánticamente a nvme_default_all_modern_os)
    """
    # 1) Tipos forzados
    if devtype == "nvme":
        return "nvme"
    if devtype in ("floppy", "cdrom"):
        return devtype

    # 2) Hint explícito
    hint = str(bus_hint or "auto").strip().lower()
    if hint == "sata":
        return "sata_ahci" if chipset_is_q35 else "ide"
    if hint == "nvme":
        return "nvme"
    if hint == "virtio-blk":
        return "virtio-blk"
    if hint == "virtio-scsi":
        return "virtio-scsi"
    # hint desconocido → tratar como auto.

    # 3) Default por SO (revertido: SATA, no NVMe).
    if os_type == "macos":
        return "sata_ahci"
    if os_type == "windows":
        wv = str(win_ver or "").lower()
        if "xp" in wv or "2000" in wv:
            return "ide"
        if "vista" in wv or "windows 7" in wv:
            return "sata_ahci"
        # Windows 8.1+ → SATA (antes NVMe, que rompe snapshots).
        return "sata_ahci"
    if os_type == "android":
        return "sata_ahci" if chipset_is_q35 else "ide"
    # Linux y cualquier otro.
    return "sata_ahci"


def resolve_disk_bus_for_device(d, os_type, win_ver="", chipset_is_q35=True):
    """Atajo: resuelve el bus real de UNA entrada de storage_devices."""
    if not isinstance(d, dict):
        return "sata_ahci"
    return resolve_disk_bus_for_os(
        os_type=os_type,
        win_ver=win_ver,
        chipset_is_q35=chipset_is_q35,
        devtype=str(d.get("device") or "sata").lower(),
        bus_hint=str(d.get("bus_hint") or "auto").lower(),
    )


# ----------------------------------------------------------------------
# Validación de límites
# ----------------------------------------------------------------------

def validate_disk_bus_limits(devices, os_type="linux", win_ver="",
                              chipset_is_q35=True, cdroms_count=0):
    """Valida que no se superen los límites de cada bus.

    `devices` es una lista de dicts tipo storage_devices (con "device"
    y opcional "bus_hint"). Los CD/DVD se cuentan aparte (`cdroms_count`).

    Devuelve lista de strings con errores legibles. Vacío = OK.

    Marcador: disk_bus_limits_v1
    """
    errors = []
    counts = {}
    for d in devices or []:
        if not isinstance(d, dict):
            continue
        dev_type = str(d.get("device") or "sata").lower()
        if dev_type == "cdrom":
            continue
        bus = resolve_disk_bus_for_device(
            d, os_type, win_ver, chipset_is_q35
        )
        counts[bus] = counts.get(bus, 0) + 1

    for bus, n in counts.items():
        limit = DISK_BUS_LIMITS.get(bus)
        if limit is None:
            continue
        if n > limit:
            label = BUS_LABELS.get(bus, bus)
            errors.append(
                "El bus {0} admite {1} disco(s), pero hay {2} "
                "configurado(s).".format(label, limit, n)
            )

    # Regla combinada SATA/AHCI + CD/DVD: comparten los puertos del
    # mismo controlador AHCI. En Q35 hay 6; en i440FX solo 2.
    _sata_disks = counts.get("sata_ahci", 0)
    if _sata_disks and cdroms_count:
        _total_ahci = _sata_disks + int(cdroms_count or 0)
        _ahci_limit = 6 if chipset_is_q35 else 2
        if _total_ahci > _ahci_limit:
            errors.append(
                "El controlador AHCI tiene {0} puertos y hay {1} "
                "dispositivo(s) entre discos SATA y CD/DVD "
                "({2} disco(s) + {3} CD/DVD).".format(
                    _ahci_limit, _total_ahci, _sata_disks, cdroms_count
                )
            )
    return errors


def check_new_disk_fits(devices, new_device, os_type="linux",
                         win_ver="", chipset_is_q35=True,
                         cdroms_count=0):
    """Comprueba si un disco nuevo cabe en su bus.

    Simula la lista [*devices, new_device] y devuelve errores.
    `devices` NO debe incluir todavía al new_device.
    """
    sim = list(devices or []) + [dict(new_device or {})]
    return validate_disk_bus_limits(
        sim, os_type=os_type, win_ver=win_ver,
        chipset_is_q35=chipset_is_q35, cdroms_count=cdroms_count,
    )


# ----------------------------------------------------------------------
# Etiquetas
# ----------------------------------------------------------------------

def bus_label(bus):
    """Etiqueta humana de un bus resuelto."""
    return BUS_LABELS.get(str(bus or "").lower(), str(bus or ""))


def bus_limit(bus):
    """Límite de discos duros de un bus (o None si no aplica)."""
    return DISK_BUS_LIMITS.get(str(bus or "").lower())


# sata_default_all_modern_os_v1
# disk_bus_limits_v1
