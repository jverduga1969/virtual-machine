# -*- coding: utf-8 -*-
"""Traducciones it - tanda6 (media_library_host_mount_v1"
 + media_library_create_disk_v1 + dialogos VMDK/VDI/VHD/VHDX).
Marcador: tanda6_media_library_v1."""

TRANSLATIONS = {
    '➕ Crear disco':
        '➕ Crea disco',
    "Crea un disco virtual nuevo en la biblioteca con\n'qemu-img create'.\n\nFormatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ny disquete (IMG). El archivo se guarda en MediaLibrary/\ny se registra automáticamente en el índice.":
        "Crea un nuovo disco virtuale nella libreria con\n'qemu-img create'.\n\nFormati supportati: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ne floppy (IMG). Il file viene salvato in MediaLibrary/\ne registrato automaticamente nell'indice.",
    '🔌 Montar en host':
        "🔌 Monta sull'host",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.\n\nSe usa guestmount (FUSE, sin root) si está disponible,\no qemu-nbd (con pkexec) como alternativa.\n\nRequiere que ninguna VM que lo use esté encendida:\nQEMU mantiene un bloqueo de escritura sobre el archivo.':
        'Monta questo disco virtuale sul sistema host per\nispezionare o copiare il suo contenuto senza avviare la VM.\n\nguestmount (FUSE, senza root) viene usato se disponibile,\no qemu-nbd (con pkexec) come alternativa.\n\nRichiede che nessuna VM che lo usa sia accesa:\nQEMU mantiene un blocco di scrittura sul file.',
    '⏏ Desmontar del host':
        "⏏ Smonta dall'host",
    "Desmonta del sistema anfitrión el disco que se montó\npreviamente con 'Montar en host'.":
        "Smonta dal sistema host il disco precedentemente\nmontato con 'Monta sull'host'.",
    'montado (rw)':
        'montato (rw)',
    'montado (ro)':
        'montato (ro)',
    'Herramientas de montaje':
        'Strumenti di montaggio',
    "No se encontró guestmount ni qemu-nbd en el sistema.\n\nInstala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\ncomo alternativa) con el gestor de paquetes de tu\ndistribución para poder montar discos virtuales.":
        "Né guestmount né qemu-nbd sono stati trovati sul sistema.\n\nInstalla 'libguestfs' e 'guestfs-tools' (o 'qemu-nbd'\ncome alternativa) con il gestore di pacchetti della tua\ndistribuzione per poter montare dischi virtuali.",
    "Faltan las herramientas de montaje y no se encontró\n'pkexec' para pedir permisos de administrador.\n\nEjecuta a mano:\n\n  sudo {0} install {1}":
        "Mancano gli strumenti di montaggio e 'pkexec' non è\nstato trovato per richiedere i permessi di amministratore.\n\nEsegui manualmente:\n\n  sudo {0} install {1}",
    'Se necesitan herramientas adicionales para montar discos\nen el host.\n\n  • guestmount (libguestfs) es lo ideal: sin root, detecta\n    particiones y sistemas de archivos automáticamente.\n  • qemu-nbd es la alternativa si no hay libguestfs.\n\n¿Quieres instalar las herramientas ahora? Se pedirá la\ncontraseña de administrador.\n\nComando:\n  {0}':
        "Sono necessari strumenti aggiuntivi per montare dischi\nsull'host.\n\n  • guestmount (libguestfs) è l'ideale: senza root, rileva\n    partizioni e filesystem automaticamente.\n  • qemu-nbd è l'alternativa se libguestfs non è disponibile.\n\nVuoi installare gli strumenti ora? Verrà richiesta la\npassword di amministratore.\n\nComando:\n  {0}",
    'No se pudo ejecutar el comando de instalación.\n\n{0}':
        'Impossibile eseguire il comando di installazione.\n\n{0}',
    'La instalación falló.\n\n{0}':
        'Installazione fallita.\n\n{0}',
    'Instalación completada.':
        'Installazione completata.',
    'Montajes previos detectados':
        'Montaggi precedenti rilevati',
    'Se encontraron {0} disco(s) montados en el sistema de\nuna sesión anterior de la aplicación:\n\n{1}\n\n¿Quieres desmontarlos ahora?':
        "Sono stati trovati {0} disco(i) montati sul sistema da una\nsessione precedente dell'applicazione:\n\n{1}\n\nVuoi smontarli ora?",
    'Montar en el host':
        "Monta sull'host",
    'Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>El disco debe estar apagado: ninguna VM que lo use puede\nestar encendida, porque QEMU mantiene un bloqueo de escritura\nsobre el archivo.':
        '<b>{0}</b> verrà montato sul sistema host.<br><br>Il disco deve essere spento: nessuna VM che lo usa può\nessere accesa, perché QEMU mantiene un blocco di scrittura\nsul file.',
    'Permitir escritura (montar en modo read-write)':
        'Consenti scrittura (monta in modalità lettura-scrittura)',
    '⚠ Con read-write, escribir en el disco puede corromper el\nsistema de archivos si después se arranca la VM sin\ndesmontarlo. Para inspeccionar o copiar, deja read-only.\n\nLos archivos que crees desde el host se atribuirán a tu\nusuario del guest (uid/gid {0}:{1}) cuando el sistema de\narchivos lo permita; si no, aparecerán como root.':
        "⚠ In lettura-scrittura, scrivere sul disco può corrompere il\nfilesystem se la VM viene successivamente avviata senza\nsmontarlo. Per ispezionare o copiare, lascia in sola lettura.\n\nI file che crei dall'host saranno attribuiti al tuo utente\nnel guest (uid/gid {0}:{1}) quando il filesystem lo\npermette; altrimenti, appariranno come root.",
    'Montar':
        'Monta',
    'Selecciona un disco virtual para montarlo en el host.':
        "Seleziona un disco virtuale per montarlo sull'host.",
    'Selecciona un disco previamente montado para desmontarlo.':
        'Seleziona un disco precedentemente montato per smontarlo.',
    'Solo se pueden montar discos virtuales\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).':
        'Solo i dischi virtuali possono essere montati\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).',
    "Este disco ya está montado. Usa '⏏ Desmontar del host'\npara liberarlo.":
        "Questo disco è già montato. Usa '⏏ Smonta dall'host'\nper rilasciarlo.",
    "La VM '{0}' está usando este disco y está encendida.\nApágala para poder montarlo en el host.":
        "La VM '{0}' sta usando questo disco ed è accesa.\nSpegnila per poterlo montare sull'host.",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.':
        'Monta questo disco virtuale sul sistema host per\nispezionare o copiare il suo contenuto senza avviare la VM.',
    'Desmontar de {0}':
        'Smonta da {0}',
    'Este disco no está montado en el host.':
        "Questo disco non è montato sull'host.",
    'Montar en host':
        "Monta sull'host",
    'Error inesperado al montar el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Errore imprevisto durante il montaggio del disco.\n\nPuoi vedere i dettagli nella Console di Progresso.\n\n{0}',
    'Este disco ya está montado.':
        'Questo disco è già montato.',
    "La VM '{0}' está usando este disco y está encendida.\n\nApágala antes de montar el disco en el host: QEMU\nmantiene un bloqueo de escritura sobre el archivo\ny el montaje fallaría.":
        "La VM '{0}' sta usando questo disco ed è accesa.\n\nSpegnila prima di montare il disco sull'host: QEMU\nmantiene un blocco di scrittura sul file\ne il montaggio fallirebbe.",
    'Las herramientas de montaje siguen sin estar\ndisponibles después de la instalación.':
        "Gli strumenti di montaggio sono ancora indisponibili\ndopo l'installazione.",
    'No se pudo crear el punto de montaje.\n\n{0}':
        'Impossibile creare il punto di montaggio.\n\n{0}',
    'Aviso: el sistema de archivos del guest no acepta mapeo de usuario; los archivos que crees desde el host aparecerán como root en el guest. Para trabajar sin problemas de permisos, escribe desde el guest en lugar del host.':
        "Avviso: il filesystem del guest non accetta la mappatura dell'utente; i file che crei dall'host appariranno come root nel guest. Per lavorare senza problemi di permessi, scrivi dal guest invece che dall'host.",
    'Disco montado':
        'Disco montato',
    "'{0}' montado correctamente.\n\nPunto de montaje: {1}\nModo: {2}{3}":
        "'{0}' montato con successo.\n\nPunto di montaggio: {1}\nModalità: {2}{3}",
    'read-only':
        'sola lettura',
    'read-write':
        'lettura-scrittura',
    'No se pudo montar el disco.\n\n{0}':
        'Impossibile montare il disco.\n\n{0}',
    "Montando '{0}'":
        "Montaggio di '{0}'",
    'Preparando el punto de montaje en el host…':
        "Preparazione del punto di montaggio sull'host…",
    'Desmontar del host':
        "Smonta dall'host",
    'Error inesperado al desmontar.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Errore imprevisto durante lo smontaggio.\n\nPuoi vedere i dettagli nella Console di Progresso.\n\n{0}',
    "¿Desmontar '{0}' de {1}?":
        "Smontare '{0}' da {1}?",
    "'{0}' desmontado correctamente.":
        "'{0}' smontato con successo.",
    'No se pudo desmontar.\n\n{0}':
        'Impossibile smontare.\n\n{0}',
    "Desmontando '{0}'":
        "Smontaggio di '{0}'",
    'Liberando el punto de montaje…':
        'Rilascio del punto di montaggio…',
    'Crear disco':
        'Crea disco',
    'Error inesperado al crear el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Errore imprevisto durante la creazione del disco.\n\nPuoi vedere i dettagli nella Console di Progresso.\n\n{0}',
    'La biblioteca no está disponible.':
        'La libreria non è disponibile.',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n¿Sobrescribir? (se perderá el contenido anterior)':
        'Esiste già un file con quel nome nella libreria:\n\n{0}\n\nSovrascrivere? (il contenuto precedente andrà perso)',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils / qemu-img).":
        "'qemu-img' non è stato trovato. Installalo (pacchetto qemu-utils / qemu-img).",
    'Disco creado':
        'Disco creato',
    'Se creó el disco correctamente.\n\nArchivo: {0}\nTamaño: {1}\nFormato: {2}':
        'Disco creato con successo.\n\nFile: {0}\nDimensione: {1}\nFormato: {2}',
    'No se pudo crear el disco.\n\n{0}':
        'Impossibile creare il disco.\n\n{0}',
    "Creando '{0}'":
        "Creazione di '{0}'",
    'Ejecutando qemu-img create…':
        'Esecuzione di qemu-img create…',
    'Disco duro VMDK (VirtualBox / VMware)':
        'Disco rigido VMDK (VirtualBox / VMware)',
    'Disco duro VDI (VirtualBox nativo)':
        'Disco rigido VDI (VirtualBox nativo)',
    'Disco duro VHD (Hyper-V antiguo)':
        'Disco rigido VHD (Hyper-V precedente)',
    'Disco duro VHDX (Hyper-V moderno)':
        'Disco rigido VHDX (Hyper-V moderno)',
    'Preasignación:':
        'Preallocazione:',
    'Expandible: el archivo crece solo según se usa (recomendado).\nFijo: reserva todo el espacio en disco desde el momento de\nsu creación. Tarda más y ocupa más, pero el rendimiento de\nescritura es más predecible.':
        'Espandibile: il file cresce man mano che viene usato (consigliato).\nFisso: riserva tutto lo spazio su disco al momento della\ncreazione. Richiede più tempo e occupa più spazio, ma le\nprestazioni di scrittura sono più prevedibili.',
    'Expandible: preallocation=off (recomendado).\nFijo: preallocation=full. Reserva todo el espacio\nen el host desde el momento de su creación.':
        "Espandibile: preallocation=off (consigliato).\nFisso: preallocation=full. Riserva tutto lo spazio\nsull'host al momento della creazione.",
    'Expandible: VDI dinámico (recomendado).\nFijo: static=on. Reserva todo el espacio en el host.':
        "Espandibile: VDI dinamico (consigliato).\nFisso: static=on. Riserva tutto lo spazio sull'host.",
    'Expandible: VHD dynamic (recomendado).\nFijo: subformat=fixed. Reserva todo el espacio.':
        'Espandibile: VHD dinamico (consigliato).\nFisso: subformat=fixed. Riserva tutto lo spazio.',
    'Formato VMDK monolithicSparse (compatible con VirtualBox y VMware). El archivo crece según se usa; las snapshots internas de QEMU no aplican.':
        'Formato VMDK monolithicSparse (compatibile con VirtualBox e VMware). Il file cresce man mano che viene usato; gli snapshot interni di QEMU non si applicano.',
    'Formato VDI nativo de VirtualBox. El archivo crece según se usa.':
        'Formato VDI nativo di VirtualBox. Il file cresce man mano che viene usato.',
    "Formato VHD (Hyper-V hasta Windows 2008 R2). Compatible con la mayoría de hipervisores. QEMU lo llama internamente 'vpc'.":
        "Formato VHD (Hyper-V fino a Windows 2008 R2). Compatibile con la maggior parte degli hypervisor. QEMU lo chiama internamente 'vpc'.",
    'Formato VHDX (Hyper-V moderno, desde Windows 2012). Soporta discos de hasta 64 TB y bloques de 4 KB.':
        'Formato VHDX (Hyper-V moderno, da Windows 2012). Supporta dischi fino a 64 TB e blocchi da 4 KB.',
    'Disco virtual expandible.':
        'Disco virtuale espandibile.',
}
