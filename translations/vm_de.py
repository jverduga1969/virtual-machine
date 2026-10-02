# -*- coding: utf-8 -*-
"""Traducciones al aleman - VM Einstellungen - Bloque base.

Cubre: i18n_v1 (pestanas principales + titulo + dialogo de reinicio),
Tanda 2a (dialogs.py), MediaPickerDialog, NatPortForwardDialog,
NetworkDeviceDialog y _CreateMediumDialog.

Se fusiona con vm_de_tanda2b.py, vm_de_tanda2c.py, ... en orden
alfabetico por _load_external_dict() en translate_ts.py.
"""

TRANSLATIONS = {

    # ================================================================
    # i18n_v1: pestanas principales, titulo y dialogo de reinicio
    # ================================================================
    "Resumen": "Übersicht",
    "Configuración VM": "VM-Einstellungen",
    "Configuración Host": "Host-Einstellungen",
    "Snapshots": "Snapshots",
    "\U0001f4be Backups": "\U0001f4be Backups",
    "\U0001f4da Medios": "\U0001f4da Medien",
    "\U0001f5a5\ufe0f Consola Gráfica": "\U0001f5a5\ufe0f Grafische Konsole",
    "\U0001f4cb Consola de Progreso": "\U0001f4cb Fortschrittskonsole",
    "\u2753 Ayuda": "\u2753 Hilfe",
    "Administrador QEMU/KVM": "QEMU/KVM-Verwaltung",
    "Cambio de idioma": "Sprachwechsel",
    "Se ha cambiado el idioma a {0}.\n\n"
    "Para que TODA la aplicación use el idioma nuevo\n"
    "es necesario reiniciar.\n\n"
    "¿Quieres reiniciar ahora?":
        "Die Sprache wurde auf {0} geändert.\n\n"
        "Damit die GESAMTE Anwendung die neue Sprache verwendet,\n"
        "ist ein Neustart erforderlich.\n\n"
        "Jetzt neu starten?",

    # ================================================================
    # Tanda 2a: dialogs.py
    # ================================================================

    # --- DiskCreationDialog: cabeceras segun tipo de dispositivo ---
    'Configurar dispositivo de almacenamiento': 'Speichergerät konfigurieren',
    '\U0001f4bd Disco SATA': '\U0001f4bd SATA-Festplatte',
    '\u26a1 Disco NVMe': '\u26a1 NVMe-Festplatte',
    '\U0001f4be Disquetera': '\U0001f4be Diskettenlaufwerk',
    '\U0001f4c0 Unidad CD / DVD': '\U0001f4c0 CD-/DVD-Laufwerk',
    'Dispositivo de almacenamiento': 'Speichergerät',

    # --- Botones comunes ---
    'Cancelar': 'Abbrechen',
    'Aceptar': 'OK',
    'Crear': 'Erstellen',
    'Elegir': 'Auswählen',

    # --- DiskCreationDialog: fuentes del medio (CD/DVD) ---
    'Mantener vacío': 'Leer lassen',
    'Usar ISO/IMG/DMG existente': 'Vorhandenes ISO/IMG/DMG verwenden',
    'System Recovery de macOS (descargar al iniciar)':
        'macOS System Recovery (beim Start herunterladen)',
    'Descargar instalador de Windows automáticamente':
        'Windows-Installer automatisch herunterladen',
    'Descargar instalador de Linux automáticamente':
        'Linux-Installer automatisch herunterladen',
    'Fuente del medio:': 'Medienquelle:',

    # --- DiskCreationDialog: campos de formulario ---
    'Nombre:': 'Name:',
    'Tamaño:': 'Größe:',
    'Tipo:': 'Typ:',
    'Formato:': 'Format:',
    'Origen:': 'Quelle:',
    'Archivo:': 'Datei:',
    'Medio:': 'Medium:',
    'Ruta del archivo existente…': 'Pfad der vorhandenen Datei…',
    'Selecciona una ISO / IMG / DMG…': 'ISO / IMG / DMG auswählen…',
    'Ej.: 40G, 100G, 1T': 'z. B.: 40G, 100G, 1T',

    # --- DiskCreationDialog: botones de exploracion ---
    '\U0001f4c1 Buscar…': '\U0001f4c1 Durchsuchen…',
    '\U0001f4da Biblioteca…': '\U0001f4da Bibliothek…',

    # --- DiskCreationDialog: toggles y modos ---
    'Crear nuevo': 'Neu erstellen',
    'Usar archivo existente': 'Vorhandene Datei verwenden',
    'Expandible (dinámico)': 'Erweiterbar (dynamisch)',
    'Fijo (preasignado)': 'Fest (vorab zugewiesen)',

    # --- DiskCreationDialog: tooltips ---
    'Elegir un medio de la biblioteca central (MediaLibrary/).\n'
    'Se reutiliza entre todas las VMs.':
        'Ein Medium aus der zentralen Bibliothek (MediaLibrary/) wählen.\n'
        'Wird von allen VMs gemeinsam genutzt.',
    'Elegir un archivo ya registrado en la Biblioteca de Medios.\n'
    'Se filtra por el tipo del dispositivo.':
        'Eine bereits in der Medienbibliothek registrierte Datei wählen.\n'
        'Wird nach Gerätetyp gefiltert.',

    # --- DiskCreationDialog: hints bajo el formulario ---
    'Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.':
        'RAW-Diskette. 720 KB, 1,44 MB oder 2,88 MB wählen.',
    'Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. '
    'También puedes adjuntar un disco existente.':
        'Erweiterbar: wächst bei Nutzung. Fest: reserviert den Speicher auf dem Host. '
        'Du kannst auch eine vorhandene Festplatte anhängen.',
    'La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.':
        'Das Laufwerk wird leer erstellt. Ein ISO kann später eingelegt werden, auch bei laufender VM.',
    'Selecciona un ISO/IMG/DMG que ya exista en tu equipo.':
        'Ein bereits vorhandenes ISO/IMG/DMG auf diesem Rechner auswählen.',
    'Para macOS se descargará System Recovery automáticamente al iniciar la VM '
    'y se asociará a esta unidad óptica.':
        'Für macOS wird System Recovery beim Start der VM automatisch heruntergeladen '
        'und diesem optischen Laufwerk zugeordnet.',
    'El instalador se descargará automáticamente al iniciar la VM, mostrando una '
    'barra de porcentaje, y quedará conectado a esta unidad CD/DVD.':
        'Der Installer wird beim Start der VM automatisch heruntergeladen, mit '
        'Fortschrittsbalken, und mit diesem CD/DVD-Laufwerk verbunden.',

    # --- Filtros de QFileDialog (parte humana; los globos se conservan) ---
    'Imágenes de disquete (*.img *.raw);;Todos los archivos (*)':
        'Diskettenabbilder (*.img *.raw);;Alle Dateien (*)',
    'Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)':
        'Virtuelle Festplatten (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Alle Dateien (*)',
    'Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)':
        'Abbilder (*.iso *.img *.dmg);;Alle Dateien (*)',
    'Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)':
        'Festplattenabbilder (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Alle (*)',

    # --- Titulos de QFileDialog ---
    'Seleccionar archivo existente': 'Vorhandene Datei auswählen',
    'Seleccionar medio óptico': 'Optisches Medium auswählen',
    'Anadir a la biblioteca': 'Zur Bibliothek hinzufügen',

    # --- Avisos y errores de validacion (DiskCreationDialog) ---
    'Medio inválido': 'Ungültiges Medium',
    'Selecciona un ISO/IMG/DMG válido.': 'Ein gültiges ISO/IMG/DMG auswählen.',
    'Archivo inválido': 'Ungültige Datei',
    'Selecciona un archivo existente válido.': 'Eine gültige vorhandene Datei auswählen.',
    'Nombre requerido': 'Name erforderlich',
    'Indica un nombre para el dispositivo.': 'Gib einen Namen für das Gerät an.',
    'Escribe un nombre para el medio.': 'Gib einen Namen für das Medium ein.',
    'Tamaño inválido': 'Ungültige Größe',
    'Usa un tamaño como 40G, 512M o 1T.': 'Verwende eine Größe wie 40G, 512M oder 1T.',
    'Nombre inválido': 'Ungültiger Name',
    'El nombre no puede contener \\ / : * ? " < > |':
        'Der Name darf folgende Zeichen nicht enthalten: \\ / : * ? " < > |',

    # --- DiskCreationDialog: nombre por defecto del CD/DVD ---
    'CD/DVD': 'CD/DVD',

    # ================================================================
    # MediaPickerDialog: selector de medios de la biblioteca
    # ================================================================
    'Elegir medio de la biblioteca': 'Medium aus der Bibliothek wählen',
    'Elige una ISO/IMG/DMG de la biblioteca central.<br>'
    'La biblioteca vive en <code>MediaLibrary/</code>, al mismo nivel que '
    '<code>VirtualMachines/</code>. Se reutiliza entre todas las VMs.':
        'Ein ISO/IMG/DMG aus der zentralen Bibliothek wählen.<br>'
        'Die Bibliothek liegt in <code>MediaLibrary/</code>, auf derselben Ebene wie '
        '<code>VirtualMachines/</code>. Sie wird von allen VMs gemeinsam genutzt.',

    # --- Filtros del picker ---
    'Buscar...': 'Suchen...',
    'SO:': 'Betriebssystem:',
    'Todos': 'Alle',
    'Disco duro': 'Festplatte',
    'Disquete': 'Diskette',

    # --- Cabeceras de la tabla del picker ---
    'Nombre': 'Name',
    'Tipo': 'Typ',
    'SO': 'OS',
    'Version': 'Version',
    'Arq.': 'Arch.',
    'Tamano': 'Größe',
    'Usada por': 'Verwendet von',
    'Ruta': 'Pfad',

    # --- Botones del picker ---
    'Anadir archivo a la biblioteca...': 'Datei zur Bibliothek hinzufügen...',
    'Registrar una ISO nueva sin salir de este dialogo.':
        'Ein neues ISO registrieren, ohne diesen Dialog zu verlassen.',
    'Crear disco...': 'Festplatte erstellen...',
    "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
    "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
    "sobre MediaLibrary/<nombre>.<ext>.":
        "Eine virtuelle Festplatte (QCOW2 / RAW) oder eine Diskette (IMG)\n"
        "direkt in der Bibliothek erstellen. Entspricht 'qemu-img create'\n"
        "auf MediaLibrary/<Name>.<Erw>.",
    'Abrir carpeta': 'Ordner öffnen',
    'Abre MediaLibrary/ en el explorador del sistema.':
        'Öffnet MediaLibrary/ im Dateimanager des Systems.',

    # --- Celdas dinamicas del picker ---
    '{0}   (huerfano)': '{0}   (verwaist)',
    '{0}, {1} (+{2})': '{0}, {1} (+{2})',
    '(sin archivo)': '(keine Datei)',
    'No la usa ninguna VM.': 'Wird von keiner VM verwendet.',

    # --- Avisos del picker ---
    'Archivo no disponible': 'Datei nicht verfügbar',
    'El archivo de esta entrada ya no existe en el disco.\n\n'
    'Ruta esperada:\n{0}':
        'Die Datei dieses Eintrags existiert nicht mehr auf dem Datenträger.\n\n'
        'Erwarteter Pfad:\n{0}',
    'Biblioteca no disponible': 'Bibliothek nicht verfügbar',
    'La biblioteca de medios no está disponible.':
        'Die Medienbibliothek ist nicht verfügbar.',
    'Ya existe': 'Existiert bereits',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n'
    'Elige otro nombre o bórralo desde la pestaña Medios.':
        'Eine Datei mit diesem Namen existiert bereits in der Bibliothek:\n\n{0}\n\n'
        'Wähle einen anderen Namen oder lösche sie im Medien-Tab.',
    'Crear medio': 'Medium erstellen',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
    "en Debian/Ubuntu, qemu-img en Arch) para crear discos.":
        "'qemu-img' wurde nicht gefunden. Installiere es (Paket qemu-utils\n"
        "unter Debian/Ubuntu, qemu-img unter Arch), um Festplatten zu erstellen.",
    'No se pudo crear el medio.\n\n{0}':
        'Das Medium konnte nicht erstellt werden.\n\n{0}',
    'Creado con qemu-img create. Tamaño: {0}.':
        'Mit qemu-img create erstellt. Größe: {0}.',
    'El archivo se creó correctamente pero no se pudo\n'
    'registrar en la biblioteca:\n\n{0}':
        'Die Datei wurde erfolgreich erstellt, konnte aber nicht\n'
        'in der Bibliothek registriert werden:\n\n{0}',
    'Medio creado': 'Medium erstellt',
    'Se creó el medio correctamente.\n\n'
    'Archivo: {0}\n'
    'Tamaño: {1}\n'
    'Formato: {2}':
        'Das Medium wurde erfolgreich erstellt.\n\n'
        'Datei: {0}\n'
        'Größe: {1}\n'
        'Format: {2}',

    # ================================================================
    # NatPortForwardDialog: reglas NAT
    # ================================================================
    'Reglas de reenvío de puertos NAT': 'NAT-Portweiterleitungsregeln',
    'Redirige puertos del host al guest a través del NAT de QEMU '
    '(<code>-netdev user,hostfwd=...</code>). Cada regla conecta '
    '<b>localhost:puerto_host</b> del anfitrión con <b>puerto_guest</b> '
    'dentro del sistema invitado.<br><br>Ejemplo: host 2222 → guest 22 '
    'reenvía SSH; luego entra con '
    '<code>ssh -p 2222 usuario@localhost</code>.':
        'Leitet Host-Ports über das NAT von QEMU an den Gast weiter '
        '(<code>-netdev user,hostfwd=...</code>). Jede Regel verbindet '
        '<b>localhost:Host-Port</b> des Hosts mit <b>Gast-Port</b> '
        'im Gastsystem.<br><br>Beispiel: Host 2222 → Gast 22 '
        'leitet SSH weiter; dann verbindet man mit '
        '<code>ssh -p 2222 benutzer@localhost</code>.',
    'Puerto host:': 'Host-Port:',
    'Puerto en el host (donde tú te conectas).':
        'Port auf dem Host (von dem aus du dich verbindest).',
    'Puerto guest:': 'Gast-Port:',
    'Puerto dentro de la VM (a donde se reenvía).':
        'Port innerhalb der VM (an den weitergeleitet wird).',
    'Protocolo:': 'Protokoll:',
    '\u2795 Añadir regla': '\u2795 Regel hinzufügen',
    'Puerto host': 'Host-Port',
    'Puerto guest': 'Gast-Port',
    'Protocolo': 'Protokoll',
    '\U0001f5d1 Quitar seleccionada': '\U0001f5d1 Ausgewählte entfernen',
    'Regla duplicada': 'Doppelte Regel',
    'Ya existe una regla para el puerto host {0} ({1}).\n\n'
    'Elige otro puerto host o cambia el protocolo.':
        'Für den Host-Port {0} ({1}) existiert bereits eine Regel.\n\n'
        'Wähle einen anderen Host-Port oder ändere das Protokoll.',

    # ================================================================
    # NetworkDeviceDialog: adaptador de red virtual
    # ================================================================
    'Adaptador de red virtual': 'Virtueller Netzwerkadapter',
    'Red 1': 'Netzwerk 1',
    'NAT / Internet': 'NAT / Internet',
    'Bridge existente': 'Vorhandene Bridge',
    'Opcional: 52:54:00:xx:xx:xx': 'Optional: 52:54:00:xx:xx:xx',
    'Modelo:': 'Modell:',
    'Backend:': 'Backend:',
    'Bridge / TAP:': 'Bridge / TAP:',
    'MAC:': 'MAC:',
    '\U0001f500 Reglas NAT…': '\U0001f500 NAT-Regeln…',
    '\U0001f500 Reglas NAT… ({0})': '\U0001f500 NAT-Regeln… ({0})',
    'Redirigir puertos del host al guest a través del NAT de QEMU\n'
    '(hostfwd). Solo aplica cuando el backend es NAT.':
        'Host-Ports über das NAT von QEMU an den Gast weiterleiten\n'
        '(hostfwd). Gilt nur, wenn das Backend NAT ist.',
    'Red': 'Netzwerk',

    # ================================================================
    # _CreateMediumDialog: crear disco nuevo en la biblioteca
    # ================================================================
    'Crear medio nuevo': 'Neues Medium erstellen',
    'Ej: disco_ubuntu_datos': 'z. B.: ubuntu_datenplatte',
    'Disco duro QCOW2 (recomendado)': 'QCOW2-Festplatte (empfohlen)',
    'Disco duro RAW': 'RAW-Festplatte',
    'Disquete IMG (RAW)': 'IMG-Diskette (RAW)',
    "Disquete formateado como RAW. Se registra como tipo 'Disquete' en "
    "la biblioteca. Tamaños típicos: 720 KB, 1.44 MB, 2.88 MB.":
        "Als RAW formatierte Diskette. Wird als Typ 'Diskette' in "
        "der Bibliothek registriert. Typische Größen: 720 KB, 1,44 MB, 2,88 MB.",
    'Disco virtual expandible (recomendado). El archivo en el host '
    'crece solo según se usa en el guest.':
        'Erweiterbare virtuelle Festplatte (empfohlen). Die Datei auf dem Host '
        'wächst nur bei Nutzung im Gast.',
    'Disco RAW (imagen plana). Ocupa el tamaño completo en el host '
    'desde el momento de su creación.':
        'RAW-Festplatte (flaches Abbild). Belegt die volle Größe auf dem Host '
        'ab dem Zeitpunkt der Erstellung.',

    # kvm_preflight_v1
    '/dev/kvm no está disponible. La VM arrancará con emulación por software (TCG), que es 10-100× más lenta que KVM.\n\n{0}':
        '/dev/kvm ist nicht verfügbar. Die VM startet mit Software-Emulation (TCG), die 10-100× langsamer als KVM ist.\n\n{0}',
    "Tu usuario no puede usar /dev/kvm (no está en el grupo 'kvm'). La VM arrancará con emulación por software (muy lenta).\n\n{0}":
        "Dein Benutzer kann /dev/kvm nicht verwenden (nicht in der Gruppe 'kvm'). Die VM startet mit Software-Emulation (sehr langsam).\n\n{0}",
}
