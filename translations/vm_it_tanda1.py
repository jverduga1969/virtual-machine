# -*- coding: utf-8 -*-
"""vm_it_tanda1 - Traduzioni in italiano - Tanda 1.

Copre: schede principali, titolo finestra, dialogo cambio lingua,
dialogs.py (DiskCreationDialog, MediaPickerDialog, NatPortForwardDialog,
NetworkDeviceDialog, _CreateMediumDialog).

Per compilare:
    ./rebuild_i18n.sh it

Oppure passo a passo:
    pylupdate6 $(cat .pylupdate6_sources) -ts i18n/vm_it.ts
    python3 translate_ts.py --lang it
    lrelease6 i18n/vm_it.ts
    ./run.sh
"""

TRANSLATIONS = {

    # ================================================================
    # i18n_v1: schede principali, titolo e dialogo di riavvio
    # ================================================================
    "Resumen": "Panoramica",
    "Configuración VM": "Configurazione VM",
    "Configuración Host": "Configurazione Host",
    "Snapshots": "Istantanee",
    "\U0001f4be Backups": "\U0001f4be Backup",
    "\U0001f4da Medios": "\U0001f4da Supporti",
    "\U0001f5a5\ufe0f Consola Gráfica": "\U0001f5a5\ufe0f Console Grafica",
    "\U0001f4cb Consola de Progreso": "\U0001f4cb Console di Avanzamento",
    "\u2753 Ayuda": "\u2753 Aiuto",
    "Administrador QEMU/KVM": "Gestore QEMU/KVM",
    "Cambio de idioma": "Cambio lingua",
    "Se ha cambiado el idioma a {0}.\n\n"
    "Para que TODA la aplicación use el idioma nuevo\n"
    "es necesario reiniciar.\n\n"
    "¿Quieres reiniciar ahora?":
        "La lingua è stata cambiata in {0}.\n\n"
        "Per applicare la nuova lingua a TUTTA l'applicazione\n"
        "è necessario riavviare.\n\n"
        "Vuoi riavviare adesso?",

    # ================================================================
    # dialogs.py - DiskCreationDialog
    # ================================================================
    'Configurar dispositivo de almacenamiento': 'Configura dispositivo di archiviazione',
    '\U0001f4bd Disco SATA': '\U0001f4bd Disco SATA',
    '\u26a1 Disco NVMe': '\u26a1 Disco NVMe',
    '\U0001f4be Disquetera': '\U0001f4be Unità floppy',
    '\U0001f4c0 Unidad CD / DVD': '\U0001f4c0 Unità CD / DVD',
    'Dispositivo de almacenamiento': 'Dispositivo di archiviazione',

    'Cancelar': 'Annulla',
    'Aceptar': 'OK',
    'Crear': 'Crea',
    'Elegir': 'Scegli',

    'Mantener vacío': 'Mantieni vuoto',
    'Usar ISO/IMG/DMG existente': 'Usa ISO/IMG/DMG esistente',
    'System Recovery de macOS (descargar al iniciar)':
        'System Recovery di macOS (scarica all\'avvio)',
    'Descargar instalador de Windows automáticamente':
        'Scarica automaticamente l\'installer di Windows',
    'Descargar instalador de Linux automáticamente':
        'Scarica automaticamente l\'installer di Linux',
    'Fuente del medio:': 'Origine del supporto:',

    'Nombre:': 'Nome:',
    'Tamaño:': 'Dimensione:',
    'Tipo:': 'Tipo:',
    'Formato:': 'Formato:',
    'Origen:': 'Origine:',
    'Archivo:': 'File:',
    'Medio:': 'Supporto:',
    'Ruta del archivo existente…': 'Percorso del file esistente…',
    'Selecciona una ISO / IMG / DMG…': 'Seleziona una ISO / IMG / DMG…',
    'Ej.: 40G, 100G, 1T': 'Es.: 40G, 100G, 1T',

    '\U0001f4c1 Buscar…': '\U0001f4c1 Sfoglia…',
    '\U0001f4da Biblioteca…': '\U0001f4da Libreria…',

    'Crear nuevo': 'Crea nuovo',
    'Usar archivo existente': 'Usa file esistente',
    'Expandible (dinámico)': 'Espandibile (dinamico)',
    'Fijo (preasignado)': 'Fisso (preallocato)',

    'Elegir un medio de la biblioteca central (MediaLibrary/).\n'
    'Se reutiliza entre todas las VMs.':
        'Scegli un supporto dalla libreria centrale (MediaLibrary/).\n'
        'Viene riutilizzato tra tutte le VM.',
    'Elegir un archivo ya registrado en la Biblioteca de Medios.\n'
    'Se filtra por el tipo del dispositivo.':
        'Scegli un file già registrato nella Libreria dei supporti.\n'
        'Viene filtrato in base al tipo del dispositivo.',

    'Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.':
        'Floppy RAW. Scegli 720 KB, 1,44 MB o 2,88 MB.',
    'Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. '
    'También puedes adjuntar un disco existente.':
        'Espandibile: cresce man mano che viene usato. Fisso: riserva lo spazio sull\'host. '
        'Puoi anche allegare un disco esistente.',
    'La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.':
        'L\'unità viene creata vuota. Potrai inserire un\'ISO in seguito, anche con la VM accesa.',
    'Selecciona un ISO/IMG/DMG que ya exista en tu equipo.':
        'Seleziona un\'ISO/IMG/DMG già presente sul tuo computer.',
    'Para macOS se descargará System Recovery automáticamente al iniciar la VM '
    'y se asociará a esta unidad óptica.':
        'Per macOS, System Recovery verrà scaricato automaticamente all\'avvio della VM '
        'e associato a questa unità ottica.',
    'El instalador se descargará automáticamente al iniciar la VM, mostrando una '
    'barra de porcentaje, y quedará conectado a esta unidad CD/DVD.':
        'L\'installer verrà scaricato automaticamente all\'avvio della VM, mostrando una '
        'barra percentuale, e rimarrà collegato a questa unità CD/DVD.',

    'Imágenes de disquete (*.img *.raw);;Todos los archivos (*)':
        'Immagini floppy (*.img *.raw);;Tutti i file (*)',
    'Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)':
        'Dischi virtuali (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Tutti i file (*)',
    'Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)':
        'Immagini (*.iso *.img *.dmg);;Tutti i file (*)',
    'Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)':
        'Immagini disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Tutti (*)',

    'Seleccionar archivo existente': 'Seleziona file esistente',
    'Seleccionar medio óptico': 'Seleziona supporto ottico',
    'Anadir a la biblioteca': 'Aggiungi alla libreria',

    'Medio inválido': 'Supporto non valido',
    'Selecciona un ISO/IMG/DMG válido.': 'Seleziona un\'ISO/IMG/DMG valido.',
    'Archivo inválido': 'File non valido',
    'Selecciona un archivo existente válido.': 'Seleziona un file esistente valido.',
    'Nombre requerido': 'Nome richiesto',
    'Indica un nombre para el dispositivo.': 'Inserisci un nome per il dispositivo.',
    'Escribe un nombre para el medio.': 'Inserisci un nome per il supporto.',
    'Tamaño inválido': 'Dimensione non valida',
    'Usa un tamaño como 40G, 512M o 1T.': 'Usa una dimensione come 40G, 512M o 1T.',
    'Nombre inválido': 'Nome non valido',
    'El nombre no puede contener \\ / : * ? " < > |':
        'Il nome non può contenere \\ / : * ? " < > |',
    'CD/DVD': 'CD/DVD',

    # ================================================================
    # dialogs.py - MediaPickerDialog
    # ================================================================
    'Elegir medio de la biblioteca': 'Scegli supporto dalla libreria',
    'Elige una ISO/IMG/DMG de la biblioteca central.<br>'
    'La biblioteca vive en <code>MediaLibrary/</code>, al mismo nivel que '
    '<code>VirtualMachines/</code>. Se reutiliza entre todas las VMs.':
        'Scegli un\'ISO/IMG/DMG dalla libreria centrale.<br>'
        'La libreria si trova in <code>MediaLibrary/</code>, allo stesso livello di '
        '<code>VirtualMachines/</code>. Viene riutilizzata tra tutte le VM.',

    'Buscar...': 'Cerca...',
    'SO:': 'SO:',
    'Todos': 'Tutti',
    'Disco duro': 'Disco rigido',
    'Disquete': 'Floppy',

    'Nombre': 'Nome',
    'Tipo': 'Tipo',
    'SO': 'SO',
    'Version': 'Versione',
    'Arq.': 'Arch.',
    'Tamano': 'Dimensione',
    'Usada por': 'Usata da',
    'Ruta': 'Percorso',

    'Anadir archivo a la biblioteca...': 'Aggiungi file alla libreria...',
    'Registrar una ISO nueva sin salir de este dialogo.':
        'Registra una nuova ISO senza uscire da questo dialogo.',
    'Crear disco...': 'Crea disco...',
    "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
    "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
    "sobre MediaLibrary/<nombre>.<ext>.":
        "Crea un disco virtuale (QCOW2 / RAW) o un floppy (IMG)\n"
        "direttamente nella libreria. Equivale a 'qemu-img create'\n"
        "su MediaLibrary/<nome>.<ext>.",
    'Abrir carpeta': 'Apri cartella',
    'Abre MediaLibrary/ en el explorador del sistema.':
        'Apre MediaLibrary/ nel file manager di sistema.',

    '{0}   (huerfano)': '{0}   (orfano)',
    '{0}, {1} (+{2})': '{0}, {1} (+{2})',
    '(sin archivo)': '(nessun file)',
    'No la usa ninguna VM.': 'Nessuna VM la usa.',

    'Archivo no disponible': 'File non disponibile',
    'El archivo de esta entrada ya no existe en el disco.\n\n'
    'Ruta esperada:\n{0}':
        'Il file di questa voce non esiste più sul disco.\n\n'
        'Percorso previsto:\n{0}',
    'Biblioteca no disponible': 'Libreria non disponibile',
    'La biblioteca de medios no está disponible.':
        'La libreria dei supporti non è disponibile.',
    'Ya existe': 'Esiste già',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n'
    'Elige otro nombre o bórralo desde la pestaña Medios.':
        'Esiste già un file con quel nome nella libreria:\n\n{0}\n\n'
        'Scegli un altro nome o eliminalo dalla scheda Supporti.',
    'Crear medio': 'Crea supporto',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
    "en Debian/Ubuntu, qemu-img en Arch) para crear discos.":
        "'qemu-img' non trovato. Installalo (pacchetto qemu-utils\n"
        "su Debian/Ubuntu, qemu-img su Arch) per creare dischi.",
    'No se pudo crear el medio.\n\n{0}':
        'Impossibile creare il supporto.\n\n{0}',
    'Creado con qemu-img create. Tamaño: {0}.':
        'Creato con qemu-img create. Dimensione: {0}.',
    'El archivo se creó correctamente pero no se pudo\n'
    'registrar en la biblioteca:\n\n{0}':
        'Il file è stato creato correttamente ma non è stato possibile\n'
        'registrarlo nella libreria:\n\n{0}',
    'Medio creado': 'Supporto creato',
    'Se creó el medio correctamente.\n\n'
    'Archivo: {0}\n'
    'Tamaño: {1}\n'
    'Formato: {2}':
        'Il supporto è stato creato correttamente.\n\n'
        'File: {0}\n'
        'Dimensione: {1}\n'
        'Formato: {2}',

    # ================================================================
    # dialogs.py - NatPortForwardDialog
    # ================================================================
    'Reglas de reenvío de puertos NAT': 'Regole di inoltro porte NAT',
    'Redirige puertos del host al guest a través del NAT de QEMU '
    '(<code>-netdev user,hostfwd=...</code>). Cada regla conecta '
    '<b>localhost:puerto_host</b> del anfitrión con <b>puerto_guest</b> '
    'dentro del sistema invitado.<br><br>Ejemplo: host 2222 → guest 22 '
    'reenvía SSH; luego entra con '
    '<code>ssh -p 2222 usuario@localhost</code>.':
        "Reindirizza le porte dell'host al guest tramite il NAT di QEMU "
        "(<code>-netdev user,hostfwd=...</code>). Ogni regola collega "
        "<b>localhost:porta_host</b> dell'host a <b>porta_guest</b> "
        "all'interno del sistema guest.<br><br>Esempio: host 2222 → guest 22 "
        "inoltra SSH; poi accedi con "
        "<code>ssh -p 2222 utente@localhost</code>.",
    'Puerto host:': 'Porta host:',
    'Puerto en el host (donde tú te conectas).':
        'Porta sull\'host (da cui ti connetti).',
    'Puerto guest:': 'Porta guest:',
    'Puerto dentro de la VM (a donde se reenvía).':
        'Porta all\'interno della VM (dove viene inoltrato il traffico).',
    'Protocolo:': 'Protocollo:',
    '\u2795 Añadir regla': '\u2795 Aggiungi regola',
    'Puerto host': 'Porta host',
    'Puerto guest': 'Porta guest',
    'Protocolo': 'Protocollo',
    '\U0001f5d1 Quitar seleccionada': '\U0001f5d1 Rimuovi selezionata',
    'Regla duplicada': 'Regola duplicata',
    'Ya existe una regla para el puerto host {0} ({1}).\n\n'
    'Elige otro puerto host o cambia el protocolo.':
        'Esiste già una regola per la porta host {0} ({1}).\n\n'
        'Scegli un\'altra porta host o cambia il protocollo.',

    # ================================================================
    # dialogs.py - NetworkDeviceDialog
    # ================================================================
    'Adaptador de red virtual': 'Adattatore di rete virtuale',
    'Red 1': 'Rete 1',
    'NAT / Internet': 'NAT / Internet',
    'Bridge existente': 'Bridge esistente',
    'Opcional: 52:54:00:xx:xx:xx': 'Opzionale: 52:54:00:xx:xx:xx',
    'Modelo:': 'Modello:',
    'Backend:': 'Backend:',
    'Bridge / TAP:': 'Bridge / TAP:',
    'MAC:': 'MAC:',
    '\U0001f500 Reglas NAT…': '\U0001f500 Regole NAT…',
    '\U0001f500 Reglas NAT… ({0})': '\U0001f500 Regole NAT… ({0})',
    'Redirigir puertos del host al guest a través del NAT de QEMU\n'
    '(hostfwd). Solo aplica cuando el backend es NAT.':
        "Reindirizza le porte dell'host al guest tramite il NAT di QEMU\n"
        "(hostfwd). Si applica solo quando il backend è NAT.",
    'Red': 'Rete',

    # ================================================================
    # dialogs.py - _CreateMediumDialog
    # ================================================================
    'Crear medio nuevo': 'Crea nuovo supporto',
    'Ej: disco_ubuntu_datos': 'Es.: disco_ubuntu_dati',
    'Disco duro QCOW2 (recomendado)': 'Disco rigido QCOW2 (consigliato)',
    'Disco duro RAW': 'Disco rigido RAW',
    'Disquete IMG (RAW)': 'Floppy IMG (RAW)',
    "Disquete formateado como RAW. Se registra como tipo 'Disquete' en "
    "la biblioteca. Tamaños típicos: 720 KB, 1.44 MB, 2.88 MB.":
        "Floppy formattato come RAW. Viene registrato come tipo 'Floppy' nella "
        "libreria. Dimensioni tipiche: 720 KB, 1,44 MB, 2,88 MB.",
    'Disco virtual expandible (recomendado). El archivo en el host '
    'crece solo según se usa en el guest.':
        'Disco virtuale espandibile (consigliato). Il file sull\'host '
        'cresce solo in base all\'uso nel guest.',
    'Disco RAW (imagen plana). Ocupa el tamaño completo en el host '
    'desde el momento de su creación.':
        'Disco RAW (immagine piatta). Occupa l\'intera dimensione sull\'host '
        'dal momento della creazione.',
}
