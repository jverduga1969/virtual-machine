# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2d-1: Sistema + Procesador + Memoria.

Cubre: seccion Sistema (firmware, chipset, seguridad, perfiles,
opciones avanzadas, auto-arranque, modo compatibilidad snapshots),
Procesador (modelo CPU, nucleos) y Memoria (RAM asignada, aviso
de swap).

Se fusiona con las tandas anteriores por _load_external_dict().
"""

TRANSLATIONS = {

    # ================================================================
    # Sistema
    # ================================================================
    "Sistema": "System",
    "Plataforma, firmware y opciones de bajo nivel del hardware virtual.":
        "Plattform, Firmware und Low-Level-Optionen der virtuellen Hardware.",
    "<b>Firmware</b>": "<b>Firmware</b>",
    "BIOS (tradicional)": "BIOS (klassisch)",
    "UEFI (OVMF)": "UEFI (OVMF)",
    "<b>Chipset</b>": "<b>Chipsatz</b>",
    "i440FX (clásico)": "i440FX (klassisch)",
    "Q35 (moderno, PCIe)": "Q35 (modern, PCIe)",
    "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\n"
    "Q35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\n"
    "passthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica.":
        "i440FX: klassischer Chipsatz, Legacy-PCI. Kompatibel mit sehr alten Betriebssystemen.\n"
        "Q35: moderner Chipsatz mit nativem PCIe, AHCI/SATA und besserer Unterstützung für\n"
        "Passthrough von PCIe-Geräten. Empfohlen, sofern keine spezielle Kompatibilität nötig ist.",
    "<b>Seguridad</b>": "<b>Sicherheit</b>",
    "Secure Boot": "Secure Boot",
    "TPM 2.0": "TPM 2.0",
    "<b>Perfiles del sistema</b>": "<b>Systemprofile</b>",
    "Configuración optimizada para el sistema operativo seleccionado. "
    "Puede modificar los valores según sus necesidades.":
        "Optimierte Konfiguration für das ausgewählte Betriebssystem. "
        "Du kannst die Werte nach Bedarf anpassen.",
    "<b>Opciones avanzadas</b>": "<b>Erweiterte Optionen</b>",
    "Habilitar ACPI": "ACPI aktivieren",
    "Habilitar APIC": "APIC aktivieren",
    "Habilitar IOMMU": "IOMMU aktivieren",
    "PCIe Root Port": "PCIe Root Port",
    "Arrancar esta VM al abrir la aplicación":
        "Diese VM beim Start der Anwendung hochfahren",
    "Si está marcado, esta VM se arranca automáticamente al\n"
    "abrir la aplicación, tras un par de segundos.\n\n"
    "Las VMs marcadas se arrancan en cola, separadas por 4 s\n"
    "entre una y otra para no saturar el host. Las que ya estén\n"
    "corriendo se saltan.\n\n"
    "Nota: al auto-arrancar, la selección de la lista cambia a\n"
    "cada VM que se inicia.":
        "Wenn aktiviert, startet diese VM beim Öffnen der Anwendung\n"
        "automatisch, nach ein paar Sekunden.\n\n"
        "Markierte VMs werden in einer Warteschlange gestartet, mit 4 s\n"
        "Abstand zueinander, um den Host nicht zu überlasten. Bereits\n"
        "laufende werden übersprungen.\n\n"
        "Hinweis: Beim Auto-Start wechselt die Listenauswahl zu\n"
        "jeder startenden VM.",
    "Modo compatibilidad de snapshots (fuerza hardware snapshoteable)":
        "Snapshot-Kompatibilitätsmodus (erzwingt snapshot-fähige Hardware)",

    # ================================================================
    # Procesador
    # ================================================================
    "Procesador": "Prozessor",
    "Modelo de CPU y número de núcleos asignados a la máquina virtual.":
        "CPU-Modell und Anzahl der der VM zugewiesenen Kerne.",
    "<b>Tipo de procesador</b>": "<b>Prozessortyp</b>",
    "Automático (recomendado)": "Automatisch (empfohlen)",
    "Host (máximo rendimiento)": "Host (maximale Leistung)",
    "QEMU x86-64 (compatibilidad)": "QEMU x86-64 (Kompatibilität)",
    "Automático usa el perfil del SO. Host ofrece el máximo rendimiento "
    "pero reduce la portabilidad de la VM.":
        "Automatisch verwendet das Betriebssystem-Profil. Host bietet die maximale "
        "Leistung, verringert jedoch die Portabilität der VM.",
    "<b>Núcleos</b>": "<b>Kerne</b>",
    "{0} núcleos": "{0} Kerne",
    "El número de núcleos se ajusta al par más cercano al valor elegido, "
    "hasta la mitad de los hilos del host.":
        "Die Anzahl der Kerne wird auf den nächsten geraden Wert bis zur Hälfte "
        "der Host-Threads gerundet.",

    # ================================================================
    # Memoria
    # ================================================================
    "Memoria": "Speicher",
    "Cantidad de memoria RAM asignada a la máquina virtual.":
        "Der virtuellen Maschine zugewiesene RAM-Menge.",
    "<b>RAM asignada</b>": "<b>Zugewiesener RAM</b>",
    "RAM del host: {0} GB (libre: {1} GB)":
        "Host-RAM: {0} GB (frei: {1} GB)",
    "Asignar más de la mitad de la RAM del host puede provocar uso intensivo "
    "de swap. La sugerencia es dejar al menos 2 GB para el sistema anfitrión.":
        "Mehr als die Hälfte des Host-RAM zuzuweisen, kann zu intensiver "
        "Swap-Nutzung führen. Empfohlen ist, mindestens 2 GB für das Wirtssystem freizuhalten.",
}
