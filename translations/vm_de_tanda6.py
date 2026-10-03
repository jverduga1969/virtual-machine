# -*- coding: utf-8 -*-
"""Traducciones de - tanda6 (media_library_host_mount_v1"
 + media_library_create_disk_v1 + dialogos VMDK/VDI/VHD/VHDX).
Marcador: tanda6_media_library_v1."""

TRANSLATIONS = {
    '➕ Crear disco':
        '➕ Disk erstellen',
    "Crea un disco virtual nuevo en la biblioteca con\n'qemu-img create'.\n\nFormatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ny disquete (IMG). El archivo se guarda en MediaLibrary/\ny se registra automáticamente en el índice.":
        "Erstellt eine neue virtuelle Festplatte in der Bibliothek mit\n'qemu-img create'.\n\nUnterstützte Formate: QCOW2, RAW, VMDK, VDI, VHD, VHDX\nund Diskette (IMG). Die Datei wird in MediaLibrary/ gespeichert\nund automatisch im Index registriert.",
    '🔌 Montar en host':
        '🔌 Auf Host einbinden',
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.\n\nSe usa guestmount (FUSE, sin root) si está disponible,\no qemu-nbd (con pkexec) como alternativa.\n\nRequiere que ninguna VM que lo use esté encendida:\nQEMU mantiene un bloqueo de escritura sobre el archivo.':
        'Bindet diese virtuelle Festplatte in das Hostsystem ein, um\nihren Inhalt zu prüfen oder zu kopieren, ohne die VM zu starten.\n\nguestmount (FUSE, ohne root) wird verwendet, falls verfügbar,\noder qemu-nbd (mit pkexec) als Alternative.\n\nErfordert, dass keine VM, die sie verwendet, läuft:\nQEMU hält eine Schreibsperre auf der Datei.',
    '⏏ Desmontar del host':
        '⏏ Vom Host aushängen',
    "Desmonta del sistema anfitrión el disco que se montó\npreviamente con 'Montar en host'.":
        "Hängt die zuvor mit 'Auf Host einbinden' eingebundene\nFestplatte aus dem Hostsystem aus.",
    'montado (rw)':
        'eingebunden (rw)',
    'montado (ro)':
        'eingebunden (ro)',
    'Herramientas de montaje':
        'Einbindungswerkzeuge',
    "No se encontró guestmount ni qemu-nbd en el sistema.\n\nInstala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\ncomo alternativa) con el gestor de paquetes de tu\ndistribución para poder montar discos virtuales.":
        "Weder guestmount noch qemu-nbd wurden auf dem System gefunden.\n\nInstallieren Sie 'libguestfs' und 'guestfs-tools' (oder 'qemu-nbd'\nals Alternative) mit dem Paketmanager Ihrer Distribution,\num virtuelle Festplatten einbinden zu können.",
    "Faltan las herramientas de montaje y no se encontró\n'pkexec' para pedir permisos de administrador.\n\nEjecuta a mano:\n\n  sudo {0} install {1}":
        "Die Einbindungswerkzeuge fehlen und 'pkexec' wurde nicht\ngefunden, um Administratorrechte anzufordern.\n\nFühren Sie manuell aus:\n\n  sudo {0} install {1}",
    'Se necesitan herramientas adicionales para montar discos\nen el host.\n\n  • guestmount (libguestfs) es lo ideal: sin root, detecta\n    particiones y sistemas de archivos automáticamente.\n  • qemu-nbd es la alternativa si no hay libguestfs.\n\n¿Quieres instalar las herramientas ahora? Se pedirá la\ncontraseña de administrador.\n\nComando:\n  {0}':
        'Zusätzliche Werkzeuge sind erforderlich, um Festplatten\nauf dem Host einzubinden.\n\n  • guestmount (libguestfs) ist ideal: ohne root, erkennt\n    Partitionen und Dateisysteme automatisch.\n  • qemu-nbd ist die Alternative, wenn libguestfs fehlt.\n\nMöchten Sie die Werkzeuge jetzt installieren? Sie werden\nnach dem Administratorkennwort gefragt.\n\nBefehl:\n  {0}',
    'No se pudo ejecutar el comando de instalación.\n\n{0}':
        'Der Installationsbefehl konnte nicht ausgeführt werden.\n\n{0}',
    'La instalación falló.\n\n{0}':
        'Die Installation ist fehlgeschlagen.\n\n{0}',
    'Instalación completada.':
        'Installation abgeschlossen.',
    'Montajes previos detectados':
        'Frühere Einbindungen erkannt',
    'Se encontraron {0} disco(s) montados en el sistema de\nuna sesión anterior de la aplicación:\n\n{1}\n\n¿Quieres desmontarlos ahora?':
        'Es wurden {0} Festplatte(n) gefunden, die aus einer früheren\nSitzung der Anwendung im System eingebunden sind:\n\n{1}\n\nMöchten Sie sie jetzt aushängen?',
    'Montar en el host':
        'Auf Host einbinden',
    'Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>El disco debe estar apagado: ninguna VM que lo use puede\nestar encendida, porque QEMU mantiene un bloqueo de escritura\nsobre el archivo.':
        '<b>{0}</b> wird in das Hostsystem eingebunden.<br><br>Die Festplatte muss ausgeschaltet sein: keine VM, die sie\nverwendet, darf laufen, da QEMU eine Schreibsperre auf\nder Datei hält.',
    'Permitir escritura (montar en modo read-write)':
        'Schreiben erlauben (im Lese-/Schreibmodus einbinden)',
    '⚠ Con read-write, escribir en el disco puede corromper el\nsistema de archivos si después se arranca la VM sin\ndesmontarlo. Para inspeccionar o copiar, deja read-only.\n\nLos archivos que crees desde el host se atribuirán a tu\nusuario del guest (uid/gid {0}:{1}) cuando el sistema de\narchivos lo permita; si no, aparecerán como root.':
        '⚠ Im Lese-/Schreibmodus kann das Beschreiben der Festplatte\ndas Dateisystem beschädigen, wenn die VM danach gestartet\nwird, ohne sie auszuhängen. Zum Prüfen oder Kopieren im\nNur-Lese-Modus belassen.\n\nDateien, die Sie vom Host aus erstellen, werden Ihrem\nGastbenutzer (uid/gid {0}:{1}) zugewiesen, sofern das\nDateisystem es zulässt; andernfalls erscheinen sie als root.',
    'Montar':
        'Einbinden',
    'Selecciona un disco virtual para montarlo en el host.':
        'Wählen Sie eine virtuelle Festplatte aus, um sie auf dem Host\neinzubinden.',
    'Selecciona un disco previamente montado para desmontarlo.':
        'Wählen Sie eine zuvor eingebundene Festplatte aus, um sie\nauszuhängen.',
    'Solo se pueden montar discos virtuales\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).':
        'Nur virtuelle Festplatten können eingebunden werden\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).',
    "Este disco ya está montado. Usa '⏏ Desmontar del host'\npara liberarlo.":
        "Diese Festplatte ist bereits eingebunden. Verwenden Sie\n'⏏ Vom Host aushängen', um sie freizugeben.",
    "La VM '{0}' está usando este disco y está encendida.\nApágala para poder montarlo en el host.":
        "Die VM '{0}' verwendet diese Festplatte und läuft.\nSchalten Sie sie aus, um sie auf dem Host einzubinden.",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.':
        'Bindet diese virtuelle Festplatte in das Hostsystem ein,\num ihren Inhalt zu prüfen oder zu kopieren, ohne die VM\nzu starten.',
    'Desmontar de {0}':
        'Aushängen von {0}',
    'Este disco no está montado en el host.':
        'Diese Festplatte ist nicht auf dem Host eingebunden.',
    'Montar en host':
        'Auf Host einbinden',
    'Error inesperado al montar el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unerwarteter Fehler beim Einbinden der Festplatte.\n\nDetails finden Sie in der Fortschrittskonsole.\n\n{0}',
    'Este disco ya está montado.':
        'Diese Festplatte ist bereits eingebunden.',
    "La VM '{0}' está usando este disco y está encendida.\n\nApágala antes de montar el disco en el host: QEMU\nmantiene un bloqueo de escritura sobre el archivo\ny el montaje fallaría.":
        "Die VM '{0}' verwendet diese Festplatte und läuft.\n\nSchalten Sie sie aus, bevor Sie die Festplatte auf dem Host\neinbinden: QEMU hält eine Schreibsperre auf der Datei und\ndas Einbinden würde fehlschlagen.",
    'Las herramientas de montaje siguen sin estar\ndisponibles después de la instalación.':
        'Die Einbindungswerkzeuge sind nach der Installation\nweiterhin nicht verfügbar.',
    'No se pudo crear el punto de montaje.\n\n{0}':
        'Der Einbindungspunkt konnte nicht erstellt werden.\n\n{0}',
    'Aviso: el sistema de archivos del guest no acepta mapeo de usuario; los archivos que crees desde el host aparecerán como root en el guest. Para trabajar sin problemas de permisos, escribe desde el guest en lugar del host.':
        'Warnung: Das Gastdateisystem akzeptiert keine Benutzerzuordnung; Dateien, die Sie vom Host aus erstellen, erscheinen im Gast als root. Um ohne Berechtigungsprobleme zu arbeiten, schreiben Sie vom Gast aus statt vom Host.',
    'Disco montado':
        'Festplatte eingebunden',
    "'{0}' montado correctamente.\n\nPunto de montaje: {1}\nModo: {2}{3}":
        "'{0}' erfolgreich eingebunden.\n\nEinbindungspunkt: {1}\nModus: {2}{3}",
    'read-only':
        'Nur-Lesen',
    'read-write':
        'Lese-Schreiben',
    'No se pudo montar el disco.\n\n{0}':
        'Die Festplatte konnte nicht eingebunden werden.\n\n{0}',
    "Montando '{0}'":
        "Einbinden von '{0}'",
    'Preparando el punto de montaje en el host…':
        'Einbindungspunkt auf dem Host wird vorbereitet…',
    'Desmontar del host':
        'Vom Host aushängen',
    'Error inesperado al desmontar.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unerwarteter Fehler beim Aushängen.\n\nDetails finden Sie in der Fortschrittskonsole.\n\n{0}',
    "¿Desmontar '{0}' de {1}?":
        "'{0}' von {1} aushängen?",
    "'{0}' desmontado correctamente.":
        "'{0}' erfolgreich ausgehängt.",
    'No se pudo desmontar.\n\n{0}':
        'Aushängen fehlgeschlagen.\n\n{0}',
    "Desmontando '{0}'":
        "Aushängen von '{0}'",
    'Liberando el punto de montaje…':
        'Einbindungspunkt wird freigegeben…',
    'Crear disco':
        'Disk erstellen',
    'Error inesperado al crear el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unerwarteter Fehler beim Erstellen der Festplatte.\n\nDetails finden Sie in der Fortschrittskonsole.\n\n{0}',
    'La biblioteca no está disponible.':
        'Die Bibliothek ist nicht verfügbar.',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n¿Sobrescribir? (se perderá el contenido anterior)':
        'In der Bibliothek existiert bereits eine Datei mit diesem Namen:\n\n{0}\n\nÜberschreiben? (der vorherige Inhalt geht verloren)',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils / qemu-img).":
        "'qemu-img' wurde nicht gefunden. Installieren Sie es (Paket qemu-utils / qemu-img).",
    'Disco creado':
        'Festplatte erstellt',
    'Se creó el disco correctamente.\n\nArchivo: {0}\nTamaño: {1}\nFormato: {2}':
        'Festplatte erfolgreich erstellt.\n\nDatei: {0}\nGröße: {1}\nFormat: {2}',
    'No se pudo crear el disco.\n\n{0}':
        'Die Festplatte konnte nicht erstellt werden.\n\n{0}',
    "Creando '{0}'":
        "Erstellen von '{0}'",
    'Ejecutando qemu-img create…':
        'qemu-img create wird ausgeführt…',
    'Disco duro VMDK (VirtualBox / VMware)':
        'VMDK-Festplatte (VirtualBox / VMware)',
    'Disco duro VDI (VirtualBox nativo)':
        'VDI-Festplatte (VirtualBox nativ)',
    'Disco duro VHD (Hyper-V antiguo)':
        'VHD-Festplatte (älteres Hyper-V)',
    'Disco duro VHDX (Hyper-V moderno)':
        'VHDX-Festplatte (modernes Hyper-V)',
    'Preasignación:':
        'Vorbelegung:',
    'Expandible: el archivo crece solo según se usa (recomendado).\nFijo: reserva todo el espacio en disco desde el momento de\nsu creación. Tarda más y ocupa más, pero el rendimiento de\nescritura es más predecible.':
        'Erweiterbar: Die Datei wächst mit der Nutzung (empfohlen).\nFest: Reserviert den gesamten Speicherplatz bei der Erstellung.\nDauert länger und belegt mehr Speicher, aber die Schreibleistung\nist besser vorhersehbar.',
    'Expandible: preallocation=off (recomendado).\nFijo: preallocation=full. Reserva todo el espacio\nen el host desde el momento de su creación.':
        'Erweiterbar: preallocation=off (empfohlen).\nFest: preallocation=full. Reserviert den gesamten Speicher\nauf dem Host bei der Erstellung.',
    'Expandible: VDI dinámico (recomendado).\nFijo: static=on. Reserva todo el espacio en el host.':
        'Erweiterbar: dynamische VDI (empfohlen).\nFest: static=on. Reserviert den gesamten Speicher auf dem Host.',
    'Expandible: VHD dynamic (recomendado).\nFijo: subformat=fixed. Reserva todo el espacio.':
        'Erweiterbar: dynamische VHD (empfohlen).\nFest: subformat=fixed. Reserviert den gesamten Speicher.',
    'Formato VMDK monolithicSparse (compatible con VirtualBox y VMware). El archivo crece según se usa; las snapshots internas de QEMU no aplican.':
        'VMDK-Format monolithicSparse (kompatibel mit VirtualBox und VMware). Die Datei wächst mit der Nutzung; interne QEMU-Snapshots sind nicht anwendbar.',
    'Formato VDI nativo de VirtualBox. El archivo crece según se usa.':
        'VDI-Format, nativ für VirtualBox. Die Datei wächst mit der Nutzung.',
    "Formato VHD (Hyper-V hasta Windows 2008 R2). Compatible con la mayoría de hipervisores. QEMU lo llama internamente 'vpc'.":
        "VHD-Format (Hyper-V bis Windows 2008 R2). Kompatibel mit den meisten Hypervisoren. QEMU nennt es intern 'vpc'.",
    'Formato VHDX (Hyper-V moderno, desde Windows 2012). Soporta discos de hasta 64 TB y bloques de 4 KB.':
        'VHDX-Format (modernes Hyper-V, seit Windows 2012). Unterstützt Festplatten bis 64 TB und 4-KB-Blöcke.',
    'Disco virtual expandible.':
        'Erweiterbare virtuelle Festplatte.',
}
