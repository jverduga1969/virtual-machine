# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2d-3: Red + Dispositivos + Almacenamiento.

Cubre: seccion Red (adaptadores), Dispositivos (audio, senalizacion,
serial a archivo) y Almacenamiento (tabla de discos, botones, orden
de arranque) + storage_mixin.py (dialogo Expandir, avisos disquete).

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 2d-3a: Red + Dispositivos
    # ================================================================
    "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.":
        "Virtuelle Netzwerkadapter. Jeder kann NAT, Bridge oder TAP verwenden.",
    "Adaptadores": "Adapter",
    "➕ Agregar adaptador": "➕ Adapter hinzufügen",
    "✏ Editar": "✏ Bearbeiten",
    "Sin red (ningún adaptador virtual)": "Kein Netzwerk (kein virtueller Adapter)",
    "NAT / Internet (recomendado)": "NAT / Internet (empfohlen)",
    "TAP": "TAP",
    "VirtIO (recomendado)": "VirtIO (empfohlen)",
    "Intel E1000": "Intel E1000",
    "Realtek RTL8139": "Realtek RTL8139",
    "VMware VMXNET3": "VMware VMXNET3",
    "Interfaz/Bridge:": "Schnittstelle/Bridge:",
    "Dispositivos": "Geräte",
    "Audio y otros dispositivos integrados de la máquina virtual.":
        "Audio und weitere integrierte Geräte der virtuellen Maschine.",
    "<b>Audio</b>": "<b>Audio</b>",
    "Intel HDA (recomendado)": "Intel HDA (empfohlen)",
    "AC97": "AC97",
    "Sound Blaster 16": "Sound Blaster 16",
    "Sin sonido": "Kein Ton",
    "<b>Dispositivo de señalización (ratón / teclado)</b>":
        "<b>Zeigegerät (Maus / Tastatur)</b>",
    "USB Tablet (posición absoluta)": "USB Tablet (absolute Position)",
    "USB Mouse (posición relativa)": "USB-Maus (relative Position)",
    "USB Keyboard + Tablet": "USB-Tastatur + Tablet",
    "VirtIO Tablet (requiere drivers en el guest)":
        "VirtIO Tablet (erfordert Treiber im Gast)",
    "PS/2 (clásico)": "PS/2 (klassisch)",
    "Ninguno": "Keines",
    "Dispositivo de entrada que QEMU emula para el ratón/teclado.\n\n"
    "• Automático: macOS usa USB Tablet sobre NEC XHCI; el resto deja\n"
    "  el PS/2 por defecto de QEMU.\n"
    "• USB Tablet: posición absoluta (el cursor del guest sigue 1:1 al\n"
    "  del host). Recomendado si el cursor no se mueve bien.\n"
    "• USB Mouse: posición relativa, como un ratón físico.\n"
    "• USB Keyboard + Tablet: añade también un teclado USB.\n"
    "• VirtIO Tablet: mejor rendimiento, requiere drivers VirtIO en\n"
    "  el guest (no válido en macOS).\n"
    "• PS/2: ratón/teclado tradicionales de QEMU, sin USB.\n"
    "• Ninguno: sin ratón/teclado emulados.":
        "Eingabegerät, das QEMU für Maus/Tastatur emuliert.\n\n"
        "• Automatisch: macOS verwendet USB Tablet über NEC XHCI; der Rest behält\n"
        "  das QEMU-Standard-PS/2.\n"
        "• USB Tablet: absolute Position (der Gast-Cursor folgt 1:1 dem\n"
        "  Host-Cursor). Empfohlen, wenn sich der Cursor nicht gut bewegt.\n"
        "• USB-Maus: relative Position, wie eine physische Maus.\n"
        "• USB-Tastatur + Tablet: fügt zusätzlich eine USB-Tastatur hinzu.\n"
        "• VirtIO Tablet: bessere Leistung, erfordert VirtIO-Treiber im\n"
        "  Gast (nicht gültig unter macOS).\n"
        "• PS/2: traditionelle QEMU-Maus/Tastatur ohne USB.\n"
        "• Keines: keine emulierte Maus/Tastatur.",
    "Capturar el puerto serie a un archivo (serial.log)":
        "Seriellen Port in eine Datei schreiben (serial.log)",
    "Activa -serial file:<vm_dir>/serial.log en la linea de QEMU.\n\n"
    "El puerto serie del guest se vuelca a un archivo dentro de la\n"
    "carpeta de la VM. La BIOS/OVMF, el cargador de arranque y el\n"
    "kernel suelen escribir ahi su progreso: es la forma mas directa\n"
    "de ver por que una VM se queda en pantalla negra o se reinicia.\n\n"
    "El archivo se SOBREESCRIBE en cada arranque: solo conserva la\n"
    "ultima sesion. Se puede abrir con '📂 Carpeta' en la pestana\n"
    "Resumen.":
        "Aktiviert -serial file:<vm_dir>/serial.log in der QEMU-Befehlszeile.\n\n"
        "Der serielle Port des Gastes wird in eine Datei im VM-Ordner\n"
        "geschrieben. BIOS/OVMF, Bootloader und Kernel schreiben dort\n"
        "üblicherweise ihren Fortschritt: das ist der direkteste Weg\n"
        "zu sehen, warum eine VM auf einem schwarzen Bildschirm bleibt\n"
        "oder neu startet.\n\n"
        "Die Datei wird bei jedem Start ÜBERSCHRIEBEN: es bleibt nur\n"
        "die letzte Sitzung erhalten. Sie kann über '📂 Ordner' im\n"
        "Reiter Übersicht geöffnet werden.",
    "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña <b>Dispositivos</b> de la parte superior de la ventana.":
        "Um physische Hardware (PCI/USB) an diese VM durchzureichen, verwende den Reiter <b>Geräte</b> oben im Fenster.",

    # ================================================================
    # Tanda 2d-3b: Almacenamiento
    # ================================================================
    "Almacenamiento": "Speicher",
    "Controladores y dispositivos": "Controller und Geräte",
    "Orden de arranque": "Startreihenfolge",
    "Dispositivo": "Gerät",
    "Tipo / archivo": "Typ / Datei",
    "Tamaño": "Größe",
    "📀 CD / DVD": "📀 CD / DVD",
    "💽 Disco Duro": "💽 Festplatte",
    "💾 Disquete": "💾 Diskette",
    "✏ Modificar": "✏ Ändern",
    "✏️ Modificar": "✏️ Ändern",
    "🗜 Compactar": "🗜 Komprimieren",
    "🗜️ Compactar": "🗜️ Komprimieren",
    "⬆ Subir": "⬆ Nach oben",
    "⬇ Bajar": "⬇ Nach unten",
    "🗑 Quitar": "🗑 Entfernen",
    "🗑️ Quitar": "🗑️ Entfernen",
    "Compacta un disco QCOW2 de la VM seleccionada.\n\n"
    "Reduce el archivo físico en el host eliminando bloques no\n"
    "usados (equivalente a 'qemu-img convert -c'). NO cambia el\n"
    "tamaño virtual que ve el sistema invitado.\n\n"
    "Se pedirá confirmación y se recomienda hacer un backup antes\n"
    "de proceder. Requiere que la VM esté apagada.":
        "Komprimiert eine QCOW2-Festplatte der ausgewählten VM.\n\n"
        "Reduziert die physische Datei auf dem Host durch Entfernen\n"
        "unbenutzter Blöcke (entspricht 'qemu-img convert -c'). Ändert NICHT\n"
        "die virtuelle Größe, die das Gastsystem sieht.\n\n"
        "Es wird eine Bestätigung angefordert und ein Backup vor dem\n"
        "Vorgang empfohlen. Erfordert, dass die VM ausgeschaltet ist.",
    "Discos, unidades ópticas y orden de arranque de la máquina virtual.":
        "Festplatten, optische Laufwerke und Startreihenfolge der virtuellen Maschine.",

    # ================================================================
    # Tanda 2d-3c: storage_mixin.py (Expandir disco)
    # ================================================================
    "Cambiar el medio de esta unidad CD/DVD.":
        "Das Medium dieses CD/DVD-Laufwerks wechseln.",
    "Los disquetes no se pueden redimensionar.\n"
    "Elimina este y crea otro si necesitas otro tamaño.":
        "Disketten können nicht in der Größe geändert werden.\n"
        "Lösche diese und erstelle eine neue, wenn du eine andere Größe benötigst.",
    "↗ Expandir": "↗ Erweitern",
    "Aumentar el tamaño virtual de este disco.\n"
    "El disco solo puede CRECER.":
        "Die virtuelle Größe dieser Festplatte erhöhen.\n"
        "Die Festplatte kann nur WACHSEN.",
    "Expandir disco": "Festplatte erweitern",
    "No se encontro la informacion del dispositivo seleccionado.":
        "Die Informationen zum ausgewählten Gerät wurden nicht gefunden.",
    "Los disquetes no se pueden redimensionar.\n\n"
    "Eliminalo y crea otro si necesitas otro tamano.":
        "Disketten können nicht in der Größe geändert werden.\n\n"
        "Lösche sie und erstelle eine neue, wenn du eine andere Größe benötigst.",
    "↗ Expandir disco": "↗ Festplatte erweitern",
    "Dispositivo:": "Gerät:",
    "Tamano actual:": "Aktuelle Größe:",
    "Ejemplo: 120G (solo crecer)": "Beispiel: 120G (nur wachsen)",
    "Nuevo tamano:": "Neue Größe:",
    "El disco solo puede CRECER. Si escribes un valor menor al actual, se rechaza y el campo vuelve al tamano original.\n\n"
    "Agrandar el archivo NO agranda la particion dentro del guest: tras aplicar el cambio, amplia tambien la particion/volumen desde el sistema invitado.":
        "Die Festplatte kann nur WACHSEN. Wird ein kleinerer Wert als der aktuelle eingegeben, wird er abgelehnt und das Feld auf die ursprüngliche Größe zurückgesetzt.\n\n"
        "Das Vergrößern der Datei vergrößert NICHT die Partition im Gast: nach der Änderung muss auch die Partition bzw. das Volume im Gastsystem erweitert werden.",
    "No se pudo expandir el disco.\n\n{0}":
        "Die Festplatte konnte nicht erweitert werden.\n\n{0}",
}
