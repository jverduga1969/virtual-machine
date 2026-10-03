# -*- coding: utf-8 -*-
"""Traducciones fr - tanda6 (media_library_host_mount_v1"
 + media_library_create_disk_v1 + dialogos VMDK/VDI/VHD/VHDX).
Marcador: tanda6_media_library_v1."""

TRANSLATIONS = {
    '➕ Crear disco':
        '➕ Créer un disque',
    "Crea un disco virtual nuevo en la biblioteca con\n'qemu-img create'.\n\nFormatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ny disquete (IMG). El archivo se guarda en MediaLibrary/\ny se registra automáticamente en el índice.":
        "Crée un nouveau disque virtuel dans la bibliothèque avec\n'qemu-img create'.\n\nFormats pris en charge : QCOW2, RAW, VMDK, VDI, VHD, VHDX\net disquette (IMG). Le fichier est enregistré dans MediaLibrary/\net automatiquement inscrit dans l'index.",
    '🔌 Montar en host':
        "🔌 Monter sur l'hôte",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.\n\nSe usa guestmount (FUSE, sin root) si está disponible,\no qemu-nbd (con pkexec) como alternativa.\n\nRequiere que ninguna VM que lo use esté encendida:\nQEMU mantiene un bloqueo de escritura sobre el archivo.':
        "Monte ce disque virtuel sur le système hôte pour\ninspecter ou copier son contenu sans démarrer la VM.\n\nguestmount (FUSE, sans root) est utilisé s'il est disponible,\nou qemu-nbd (avec pkexec) en alternative.\n\nExige qu'aucune VM qui l'utilise ne soit démarrée :\nQEMU maintient un verrou d'écriture sur le fichier.",
    '⏏ Desmontar del host':
        "⏏ Démonter de l'hôte",
    "Desmonta del sistema anfitrión el disco que se montó\npreviamente con 'Montar en host'.":
        "Démonte du système hôte le disque précédemment\nmonté avec 'Monter sur l'hôte'.",
    'montado (rw)':
        'monté (rw)',
    'montado (ro)':
        'monté (ro)',
    'Herramientas de montaje':
        'Outils de montage',
    "No se encontró guestmount ni qemu-nbd en el sistema.\n\nInstala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\ncomo alternativa) con el gestor de paquetes de tu\ndistribución para poder montar discos virtuales.":
        "Ni guestmount ni qemu-nbd n'ont été trouvés sur le système.\n\nInstallez 'libguestfs' et 'guestfs-tools' (ou 'qemu-nbd'\nen alternative) avec le gestionnaire de paquets de votre\ndistribution pour pouvoir monter des disques virtuels.",
    "Faltan las herramientas de montaje y no se encontró\n'pkexec' para pedir permisos de administrador.\n\nEjecuta a mano:\n\n  sudo {0} install {1}":
        "Les outils de montage sont manquants et 'pkexec' est\nintrouvable pour demander les droits d'administrateur.\n\nExécutez manuellement :\n\n  sudo {0} install {1}",
    'Se necesitan herramientas adicionales para montar discos\nen el host.\n\n  • guestmount (libguestfs) es lo ideal: sin root, detecta\n    particiones y sistemas de archivos automáticamente.\n  • qemu-nbd es la alternativa si no hay libguestfs.\n\n¿Quieres instalar las herramientas ahora? Se pedirá la\ncontraseña de administrador.\n\nComando:\n  {0}':
        "Des outils supplémentaires sont nécessaires pour monter\ndes disques sur l'hôte.\n\n  • guestmount (libguestfs) est idéal : sans root, il détecte\n    automatiquement les partitions et systèmes de fichiers.\n  • qemu-nbd est l'alternative si libguestfs n'est pas présent.\n\nVoulez-vous installer les outils maintenant ? Le mot de\npasse administrateur sera demandé.\n\nCommande :\n  {0}",
    'No se pudo ejecutar el comando de instalación.\n\n{0}':
        "Impossible d'exécuter la commande d'installation.\n\n{0}",
    'La instalación falló.\n\n{0}':
        "L'installation a échoué.\n\n{0}",
    'Instalación completada.':
        'Installation terminée.',
    'Montajes previos detectados':
        'Montages précédents détectés',
    'Se encontraron {0} disco(s) montados en el sistema de\nuna sesión anterior de la aplicación:\n\n{1}\n\n¿Quieres desmontarlos ahora?':
        "{0} disque(s) monté(s) sur le système depuis une session\nprécédente de l'application ont été trouvés :\n\n{1}\n\nVoulez-vous les démonter maintenant ?",
    'Montar en el host':
        "Monter sur l'hôte",
    'Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>El disco debe estar apagado: ninguna VM que lo use puede\nestar encendida, porque QEMU mantiene un bloqueo de escritura\nsobre el archivo.':
        "<b>{0}</b> va être monté sur le système hôte.<br><br>Le disque doit être éteint : aucune VM qui l'utilise ne peut\nêtre démarrée, car QEMU maintient un verrou d'écriture\nsur le fichier.",
    'Permitir escritura (montar en modo read-write)':
        "Autoriser l'écriture (monter en mode lecture-écriture)",
    '⚠ Con read-write, escribir en el disco puede corromper el\nsistema de archivos si después se arranca la VM sin\ndesmontarlo. Para inspeccionar o copiar, deja read-only.\n\nLos archivos que crees desde el host se atribuirán a tu\nusuario del guest (uid/gid {0}:{1}) cuando el sistema de\narchivos lo permita; si no, aparecerán como root.':
        "⚠ En lecture-écriture, écrire sur le disque peut corrompre le\nsystème de fichiers si la VM est ensuite démarrée sans\nle démonter. Pour inspecter ou copier, laissez en lecture seule.\n\nLes fichiers que vous créez depuis l'hôte seront attribués à\nvotre utilisateur invité (uid/gid {0}:{1}) lorsque le système\nde fichiers le permet ; sinon, ils apparaîtront comme root.",
    'Montar':
        'Monter',
    'Selecciona un disco virtual para montarlo en el host.':
        "Sélectionnez un disque virtuel pour le monter sur l'hôte.",
    'Selecciona un disco previamente montado para desmontarlo.':
        'Sélectionnez un disque précédemment monté pour le démonter.',
    'Solo se pueden montar discos virtuales\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).':
        'Seuls les disques virtuels peuvent être montés\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).',
    "Este disco ya está montado. Usa '⏏ Desmontar del host'\npara liberarlo.":
        "Ce disque est déjà monté. Utilisez '⏏ Démonter de l'hôte'\npour le libérer.",
    "La VM '{0}' está usando este disco y está encendida.\nApágala para poder montarlo en el host.":
        "La VM '{0}' utilise ce disque et est démarrée.\nÉteignez-la pour pouvoir le monter sur l'hôte.",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.':
        'Monte ce disque virtuel sur le système hôte pour\ninspecter ou copier son contenu sans démarrer la VM.',
    'Desmontar de {0}':
        'Démonter de {0}',
    'Este disco no está montado en el host.':
        "Ce disque n'est pas monté sur l'hôte.",
    'Montar en host':
        "Monter sur l'hôte",
    'Error inesperado al montar el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erreur inattendue lors du montage du disque.\n\nVous pouvez voir les détails dans la Console de progression.\n\n{0}',
    'Este disco ya está montado.':
        'Ce disque est déjà monté.',
    "La VM '{0}' está usando este disco y está encendida.\n\nApágala antes de montar el disco en el host: QEMU\nmantiene un bloqueo de escritura sobre el archivo\ny el montaje fallaría.":
        "La VM '{0}' utilise ce disque et est démarrée.\n\nÉteignez-la avant de monter le disque sur l'hôte : QEMU\nmaintient un verrou d'écriture sur le fichier et le montage\néchouerait.",
    'Las herramientas de montaje siguen sin estar\ndisponibles después de la instalación.':
        "Les outils de montage sont toujours indisponibles\naprès l'installation.",
    'No se pudo crear el punto de montaje.\n\n{0}':
        'Impossible de créer le point de montage.\n\n{0}',
    'Aviso: el sistema de archivos del guest no acepta mapeo de usuario; los archivos que crees desde el host aparecerán como root en el guest. Para trabajar sin problemas de permisos, escribe desde el guest en lugar del host.':
        "Avertissement : le système de fichiers de l'invité n'accepte pas le mappage d'utilisateur ; les fichiers que vous créez depuis l'hôte apparaîtront comme root dans l'invité. Pour travailler sans problèmes de permissions, écrivez depuis l'invité plutôt que depuis l'hôte.",
    'Disco montado':
        'Disque monté',
    "'{0}' montado correctamente.\n\nPunto de montaje: {1}\nModo: {2}{3}":
        "'{0}' monté avec succès.\n\nPoint de montage : {1}\nMode : {2}{3}",
    'read-only':
        'lecture seule',
    'read-write':
        'lecture-écriture',
    'No se pudo montar el disco.\n\n{0}':
        'Impossible de monter le disque.\n\n{0}',
    "Montando '{0}'":
        "Montage de '{0}'",
    'Preparando el punto de montaje en el host…':
        "Préparation du point de montage sur l'hôte…",
    'Desmontar del host':
        "Démonter de l'hôte",
    'Error inesperado al desmontar.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erreur inattendue lors du démontage.\n\nVous pouvez voir les détails dans la Console de progression.\n\n{0}',
    "¿Desmontar '{0}' de {1}?":
        "Démonter '{0}' de {1} ?",
    "'{0}' desmontado correctamente.":
        "'{0}' démonté avec succès.",
    'No se pudo desmontar.\n\n{0}':
        'Impossible de démonter.\n\n{0}',
    "Desmontando '{0}'":
        "Démontage de '{0}'",
    'Liberando el punto de montaje…':
        'Libération du point de montage…',
    'Crear disco':
        'Créer un disque',
    'Error inesperado al crear el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erreur inattendue lors de la création du disque.\n\nVous pouvez voir les détails dans la Console de progression.\n\n{0}',
    'La biblioteca no está disponible.':
        "La bibliothèque n'est pas disponible.",
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n¿Sobrescribir? (se perderá el contenido anterior)':
        'Un fichier portant ce nom existe déjà dans la bibliothèque :\n\n{0}\n\nÉcraser ? (le contenu précédent sera perdu)',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils / qemu-img).":
        "'qemu-img' est introuvable. Installez-le (paquet qemu-utils / qemu-img).",
    'Disco creado':
        'Disque créé',
    'Se creó el disco correctamente.\n\nArchivo: {0}\nTamaño: {1}\nFormato: {2}':
        'Disque créé avec succès.\n\nFichier : {0}\nTaille : {1}\nFormat : {2}',
    'No se pudo crear el disco.\n\n{0}':
        'Impossible de créer le disque.\n\n{0}',
    "Creando '{0}'":
        "Création de '{0}'",
    'Ejecutando qemu-img create…':
        'Exécution de qemu-img create…',
    'Disco duro VMDK (VirtualBox / VMware)':
        'Disque dur VMDK (VirtualBox / VMware)',
    'Disco duro VDI (VirtualBox nativo)':
        'Disque dur VDI (VirtualBox natif)',
    'Disco duro VHD (Hyper-V antiguo)':
        'Disque dur VHD (Hyper-V ancien)',
    'Disco duro VHDX (Hyper-V moderno)':
        'Disque dur VHDX (Hyper-V moderne)',
    'Preasignación:':
        'Préallocation :',
    'Expandible: el archivo crece solo según se usa (recomendado).\nFijo: reserva todo el espacio en disco desde el momento de\nsu creación. Tarda más y ocupa más, pero el rendimiento de\nescritura es más predecible.':
        "Extensible : le fichier grandit à mesure qu'il est utilisé (recommandé).\nFixe : réserve tout l'espace disque dès la création.\nPrend plus de temps et occupe plus d'espace, mais les\nperformances d'écriture sont plus prévisibles.",
    'Expandible: preallocation=off (recomendado).\nFijo: preallocation=full. Reserva todo el espacio\nen el host desde el momento de su creación.':
        "Extensible : preallocation=off (recommandé).\nFixe : preallocation=full. Réserve tout l'espace\nsur l'hôte dès la création.",
    'Expandible: VDI dinámico (recomendado).\nFijo: static=on. Reserva todo el espacio en el host.':
        "Extensible : VDI dynamique (recommandé).\nFixe : static=on. Réserve tout l'espace sur l'hôte.",
    'Expandible: VHD dynamic (recomendado).\nFijo: subformat=fixed. Reserva todo el espacio.':
        "Extensible : VHD dynamique (recommandé).\nFixe : subformat=fixed. Réserve tout l'espace.",
    'Formato VMDK monolithicSparse (compatible con VirtualBox y VMware). El archivo crece según se usa; las snapshots internas de QEMU no aplican.':
        "Format VMDK monolithicSparse (compatible avec VirtualBox et VMware). Le fichier grandit à mesure qu'il est utilisé ; les snapshots internes de QEMU ne s'appliquent pas.",
    'Formato VDI nativo de VirtualBox. El archivo crece según se usa.':
        "Format VDI natif de VirtualBox. Le fichier grandit à mesure qu'il est utilisé.",
    "Formato VHD (Hyper-V hasta Windows 2008 R2). Compatible con la mayoría de hipervisores. QEMU lo llama internamente 'vpc'.":
        "Format VHD (Hyper-V jusqu'à Windows 2008 R2). Compatible avec la plupart des hyperviseurs. QEMU l'appelle en interne 'vpc'.",
    'Formato VHDX (Hyper-V moderno, desde Windows 2012). Soporta discos de hasta 64 TB y bloques de 4 KB.':
        "Format VHDX (Hyper-V moderne, depuis Windows 2012). Prend en charge des disques jusqu'à 64 To et des blocs de 4 Ko.",
    'Disco virtual expandible.':
        'Disque virtuel extensible.',
}
