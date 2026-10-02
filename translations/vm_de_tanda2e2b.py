# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2e-2b: Passthrough VFIO/IOMMU.

Cubre: intro del panel Passthrough, Diagnostico PCI / VFIO, estados
IOMMU, _pci_preflight, refresh_vfio_diagnostics, _vfio_diagnostic_text,
copy_vfio_diagnostic y errores de preparacion intel_iommu=on.

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Passthrough: intro + diagnostico PCI / VFIO
    # ================================================================
    "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.":
        "Passthrough physischer Hardware. PCI verwendet VFIO; USB verwendet usb-host über XHCI. Das Programm prüft den Zugriff auf /dev/bus/usb, hängt den ausgewählten USB-Speicher automatisch vom Host aus und fordert administrative Rechte nur bei Bedarf an. Root Hubs dürfen nicht ausgewählt werden.",
    "Diagnóstico PCI / VFIO": "PCI- / VFIO-Diagnose",
    "Comprobando Intel VT-d / IOMMU...": "Intel VT-d / IOMMU wird geprüft...",
    "\U0001f504 Comprobar IOMMU / VFIO": "\U0001f504 IOMMU / VFIO prüfen",
    "\u2139 Ver diagnóstico detallado": "\u2139 Detaillierte Diagnose anzeigen",
    "\U0001f6e0 Preparar intel_iommu=on": "\U0001f6e0 intel_iommu=on vorbereiten",
    "\u2699 Abrir UEFI/BIOS": "\u2699 UEFI/BIOS öffnen",

    # ================================================================
    # Estados del IOMMU
    # ================================================================
    "Desactivado por parámetro del kernel": "Durch Kernel-Parameter deaktiviert",
    "Activo": "Aktiv",
    "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles":
        "VT-d von Firmware/Kernel erkannt; IOMMU ohne sichtbare Gruppen",
    "No detectado": "Nicht erkannt",
    "Detectado": "Erkannt",
    "No confirmado": "Nicht bestätigt",

    # ================================================================
    # Estados del tree PCI
    # ================================================================
    "\u2713 Listo para VFIO": "\u2713 Bereit für VFIO",
    "\u26a0 Sin grupo IOMMU": "\u26a0 Keine IOMMU-Gruppe",
    "\u26a0 Comparte grupo IOMMU": "\u26a0 Teilt IOMMU-Gruppe",
    "\u26a0 Requiere preparación VFIO": "\u26a0 VFIO-Vorbereitung erforderlich",

    # ================================================================
    # _pci_preflight
    # ================================================================
    "IOMMU/Intel VT-d: {0}": "IOMMU/Intel VT-d: {0}",
    "Firmware/ACPI DMAR: {0}": "Firmware/ACPI DMAR: {0}",
    "Grupos IOMMU: {0}": "IOMMU-Gruppen: {0}",
    "{0}: no tiene grupo IOMMU ({1})": "{0}: hat keine IOMMU-Gruppe ({1})",
    "{0}: comparte grupo IOMMU {1} con {2}":
        "{0}: teilt IOMMU-Gruppe {1} mit {2}",
    "{0}: driver actual {1}; todavía no está ligado a vfio-pci":
        "{0}: aktueller Treiber {1}; noch nicht an vfio-pci gebunden",
    "\u2022 {0} | grupo {1} | driver {2}":
        "\u2022 {0} | Gruppe {1} | Treiber {2}",

    # ================================================================
    # refresh_vfio_diagnostics
    # ================================================================
    "\u2705 Intel VT-d / IOMMU activo": "\u2705 Intel VT-d / IOMMU aktiv",
    "\u26a0 VT-d detectado por firmware, pero no hay grupos IOMMU utilizables":
        "\u26a0 VT-d von Firmware erkannt, aber keine nutzbaren IOMMU-Gruppen",
    "\u274c Intel VT-d / IOMMU no detectado":
        "\u274c Intel VT-d / IOMMU nicht erkannt",
    "(sin datos)": "(keine Daten)",
    "<b>{0}</b><br>"
    "Firmware/ACPI DMAR: {1}<br>"
    "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>"
    "Gestor de arranque: {4}<br>"
    "Parámetros kernel: <code>{5}</code>":
        "<b>{0}</b><br>"
        "Firmware/ACPI DMAR: {1}<br>"
        "IOMMU-Gruppen: {2} &nbsp;|&nbsp; VFIO-bereite PCI: {3}<br>"
        "Bootmanager: {4}<br>"
        "Kernel-Parameter: <code>{5}</code>",
    "Desconocido": "Unbekannt",
    "<br>\u26a0 El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.":
        "<br>\u26a0 Die CPU wurde nicht als Intel identifiziert; AMD-/IOMMU-Diagnose prüfen.",
    "<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. "
    "Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.":
        "<br>Empfehlung: <b>intel_iommu=on vorbereiten</b> verwenden und neu starten. "
        "Wenn nach dem Neustart keine Gruppen vorhanden sind, VT-d im BIOS/UEFI prüfen.",
    "<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar "
    "<code>intel_iommu=on</code> en el arranque.":
        "<br>Empfehlung: Intel VT-d im BIOS/UEFI aktivieren und danach "
        "<code>intel_iommu=on</code> beim Start aktivieren.",

    # ================================================================
    # _vfio_diagnostic_text
    # ================================================================
    "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===":
        "=== INTEL VT-d / IOMMU / VFIO-DIAGNOSE ===",
    "Estado: {0}": "Status: {0}",
    "Arquitectura: {0}": "Architektur: {0}",
    "desconocida": "unbekannt",
    "CPU Intel detectado: {0}": "Intel-CPU erkannt: {0}",
    "intel_iommu=on en kernel actual: {0}":
        "intel_iommu=on im aktuellen Kernel: {0}",
    "IOMMU desactivado por parámetro: {0}":
        "IOMMU durch Parameter deaktiviert: {0}",
    "Clases IOMMU: {0}": "IOMMU-Klassen: {0}",
    "Gestor de arranque: {0}": "Bootmanager: {0}",
    "desconocido": "unbekannt",
    "Configuración: {0}": "Konfiguration: {0}",
    "no identificada": "nicht identifiziert",
    "Parámetros kernel: {0}": "Kernel-Parameter: {0}",
    "=== DISPOSITIVOS PCI ===": "=== PCI-GERÄTE ===",
    "{0} | {1} | driver={2} | grupo={3} | estado={4}":
        "{0} | {1} | Treiber={2} | Gruppe={3} | Status={4}",
    "sin driver": "kein Treiber",

    # ================================================================
    # copy_vfio_diagnostic / vfio_diagnostic_details
    # ================================================================
    "Diagnóstico VFIO": "VFIO-Diagnose",
    "Diagnóstico copiado al portapapeles.":
        "Diagnose in die Zwischenablage kopiert.",
    "No se pudo copiar el diagnóstico": "Die Diagnose konnte nicht kopiert werden",
    "Diagnóstico Intel VT-d / IOMMU / VFIO":
        "Intel VT-d / IOMMU / VFIO-Diagnose",
    "\U0001f4cb Copiar": "\U0001f4cb Kopieren",

    # ================================================================
    # IOMMU / VT-d: RuntimeError de preparacion (intel_iommu=on)
    # ================================================================
    "El procesador no se identificó como Intel; no se aplicará intel_iommu=on.":
        "Der Prozessor wurde nicht als Intel identifiziert; intel_iommu=on wird nicht angewendet.",
    "No pude identificar de forma segura el gestor de arranque.":
        "Der Bootmanager konnte nicht sicher identifiziert werden.",
    "La preparación automática está implementada actualmente para GRUB. "
    "Gestor detectado: {0}.":
        "Die automatische Vorbereitung ist derzeit für GRUB implementiert. "
        "Erkannter Manager: {0}.",
    "No se pudo leer {0}.": "{0} konnte nicht gelesen werden.",
    "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub.":
        "GRUB_CMDLINE_LINUX_DEFAULT wurde in /etc/default/grub nicht gefunden.",
    "intel_iommu=on ya está presente en /etc/default/grub.":
        "intel_iommu=on ist bereits in /etc/default/grub vorhanden.",
    "operación cancelada": "Vorgang abgebrochen",
    "Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ":
        "/etc/default/grub wurde geändert, aber grub.cfg konnte nicht neu erzeugt werden: ",
    "error desconocido": "unbekannter Fehler",
    "Se añadió intel_iommu=on y se regeneró GRUB.":
        "intel_iommu=on wurde hinzugefügt und GRUB neu erzeugt.",

    # ================================================================
    # IOMMU / VT-d: UI
    # ================================================================
    "IOMMU / VT-d": "IOMMU / VT-d",
    "El IOMMU ya aparece activo. No es necesario modificar el arranque.":
        "Die IOMMU erscheint bereits aktiv. Der Start muss nicht geändert werden.",
    "No se identificó un CPU Intel.": "Es wurde keine Intel-CPU identifiziert.",
    "Preparar Intel IOMMU": "Intel IOMMU vorbereiten",
    "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\n"
    "Se hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\n"
    "Esto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\n"
    "Gestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?":
        "intel_iommu=on wird zur Konfiguration des Bootmanagers hinzugefügt.\n\n"
        "Vor der Änderung wird ein Backup erstellt und eine administrative Autorisierung angefordert.\n\n"
        "Dies aktiviert NICHT VT-d im BIOS/UEFI; dieser Teil muss in der Firmware aktiviert werden.\n\n"
        "Erkannter Manager: {0}\nDatei: {1}\n\nFortfahren?",
    "no identificado": "nicht identifiziert",
    "Configuración actualizada.": "Konfiguration aktualisiert.",
    "\n\nReinicia el equipo para que el parámetro tenga efecto.":
        "\n\nStarte den Rechner neu, damit der Parameter wirksam wird.",
    "No se pudo preparar IOMMU": "IOMMU konnte nicht vorbereitet werden",
    "Abrir UEFI/BIOS": "UEFI/BIOS öffnen",
    "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\n"
    "Busca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?":
        "Der Rechner startet direkt in die Firmware-Konfiguration neu, falls das System dies zulässt.\n\n"
        "Suche nach einer Option namens Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d oder ähnlich und aktiviere sie.\n\nJetzt neu starten?",
    "No se pudo solicitar el reinicio al firmware.":
        "Der Neustart der Firmware konnte nicht angefordert werden.",
    "No se pudo abrir UEFI/BIOS": "UEFI/BIOS konnte nicht geöffnet werden",
}
