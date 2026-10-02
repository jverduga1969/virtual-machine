# -*- coding: utf-8 -*-
"""Frances — Tanda 2a: dialogos.

Cubre DiskCreationDialog (parte avanzada), MediaPickerDialog,
NatPortForwardDialog, NetworkDeviceDialog, _CreateMediumDialog,
_ExportOvfDialog, _OvfImportPreviewDialog, _ShortcutsDialog,
_ShortcutCaptureDialog. Sobre traduce la tanda 1 si hay conflicto.
"""

TRANSLATIONS = {

    # ================================================================
    # DiskCreationDialog: tooltips y hints avanzados
    # ================================================================
    "Elegir un medio de la biblioteca central (MediaLibrary/).\n"
    "Se reutiliza entre todas las VMs.":
        "Choisir un support dans la bibliothèque centrale (MediaLibrary/).\n"
        "Il est réutilisé entre toutes les VM.",
    "Elegir un archivo ya registrado en la Biblioteca de Medios.\n"
    "Se filtra por el tipo del dispositivo.":
        "Choisir un fichier déjà enregistré dans la Bibliothèque de médias.\n"
        "Il est filtré selon le type du périphérique.",
    "Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.":
        "Disquette RAW. Choisissez 720 Ko, 1,44 Mo ou 2,88 Mo.",
    "Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. "
    "También puedes adjuntar un disco existente.":
        "Extensible : grandit au fur et à mesure. Fixe : réserve l'espace sur l'hôte. "
        "Vous pouvez aussi joindre un disque existant.",
    "La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.":
        "Le lecteur est créé vide. Vous pourrez insérer une ISO plus tard, même avec la VM allumée.",
    "Selecciona un ISO/IMG/DMG que ya exista en tu equipo.":
        "Sélectionnez une ISO/IMG/DMG existant sur votre machine.",
    "Para macOS se descargará System Recovery automáticamente al iniciar la VM "
    "y se asociará a esta unidad óptica.":
        "Pour macOS, System Recovery sera téléchargé automatiquement au démarrage de la VM "
        "et associé à ce lecteur optique.",
    "El instalador se descargará automáticamente al iniciar la VM, mostrando una "
    "barra de porcentaje, y quedará conectado a esta unidad CD/DVD.":
        "L'installateur sera téléchargé automatiquement au démarrage de la VM, avec une "
        "barre de pourcentage, et restera attaché à ce lecteur CD/DVD.",
    "Imágenes de disquete (*.img *.raw);;Todos los archivos (*)":
        "Images de disquette (*.img *.raw);;Tous les fichiers (*)",
    "Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)":
        "Disques virtuels (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Tous les fichiers (*)",
    "Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)":
        "Images (*.iso *.img *.dmg);;Tous les fichiers (*)",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)":
        "Images de disque (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Toutes (*)",
    "El archivo de esta entrada ya no existe en el disco.\n\n"
    "Ruta esperada:\n{0}":
        "Le fichier de cette entrée n'existe plus sur le disque.\n\n"
        "Chemin attendu :\n{0}",
    "No la usa ninguna VM.": "Aucune VM ne l'utilise.",
    "{0}   (huerfano)": "{0}   (orphelin)",
    "(sin archivo)": "(aucun fichier)",
    "Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n"
    "Elige otro nombre o bórralo desde la pestaña Medios.":
        "Un fichier de ce nom existe déjà dans la bibliothèque :\n\n{0}\n\n"
        "Choisissez un autre nom ou supprimez-le depuis l'onglet Médias.",
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
    "en Debian/Ubuntu, qemu-img en Arch) para crear discos.":
        "'qemu-img' introuvable. Installez-le (paquet qemu-utils\n"
        "sous Debian/Ubuntu, qemu-img sous Arch) pour créer des disques.",
    "No se pudo crear el medio.\n\n{0}":
        "Impossible de créer le support.\n\n{0}",
    "Creado con qemu-img create. Tamaño: {0}.":
        "Créé avec qemu-img create. Taille : {0}.",
    "El archivo se creó correctamente pero no se pudo\n"
    "registrar en la biblioteca:\n\n{0}":
        "Le fichier a été créé correctement mais n'a pas pu être\n"
        "enregistré dans la bibliothèque :\n\n{0}",
    "Se creó el medio correctamente.\n\n"
    "Archivo: {0}\n"
    "Tamaño: {1}\n"
    "Formato: {2}":
        "Le support a été créé correctement.\n\n"
        "Fichier : {0}\n"
        "Taille : {1}\n"
        "Format : {2}",

    # ================================================================
    # MediaPickerDialog: tooltips y headers
    # ================================================================
    "Elige una ISO/IMG/DMG de la biblioteca central.<br>"
    "La biblioteca vive en <code>MediaLibrary/</code>, al mismo nivel que "
    "<code>VirtualMachines/</code>. Se reutiliza entre todas las VMs.":
        "Choisissez une ISO/IMG/DMG de la bibliothèque centrale.<br>"
        "La bibliothèque vit dans <code>MediaLibrary/</code>, au même niveau que "
        "<code>VirtualMachines/</code>. Elle est réutilisée entre toutes les VM.",
    "Registrar una ISO nueva sin salir de este dialogo.":
        "Enregistrer une nouvelle ISO sans quitter cette fenêtre.",
    "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
    "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
    "sobre MediaLibrary/<nombre>.<ext>.":
        "Créer un disque virtuel (QCOW2 / RAW) ou une disquette (IMG)\n"
        "directement dans la bibliothèque. Équivaut à 'qemu-img create'\n"
        "sur MediaLibrary/<nom>.<ext>.",
    "Abre MediaLibrary/ en el explorador del sistema.":
        "Ouvre MediaLibrary/ dans le gestionnaire de fichiers du système.",

    # ================================================================
    # NatPortForwardDialog: tooltips avanzados
    # ================================================================
    "Redirige puertos del host al guest a través del NAT de QEMU "
    "(<code>-netdev user,hostfwd=...</code>). Cada regla conecta "
    "<b>localhost:puerto_host</b> del anfitrión con <b>puerto_guest</b> "
    "dentro del sistema invitado.<br><br>Ejemplo: host 2222 → guest 22 "
    "reenvía SSH; luego entra con "
    "<code>ssh -p 2222 usuario@localhost</code>.":
        "Redirige des ports de l'hôte vers l'invité via le NAT de QEMU "
        "(<code>-netdev user,hostfwd=...</code>). Chaque règle relie "
        "<b>localhost:port_hôte</b> de l'hôte à <b>port_invité</b> "
        "dans le système invité.<br><br>Exemple : hôte 2222 → invité 22 "
        "redirige SSH ; puis connectez-vous avec "
        "<code>ssh -p 2222 utilisateur@localhost</code>.",
    "Puerto en el host (donde tú te conectas).":
        "Port sur l'hôte (où vous vous connectez).",
    "Puerto dentro de la VM (a donde se reenvía).":
        "Port dans la VM (où le trafic est redirigé).",
    "Ya existe una regla para el puerto host {0} ({1}).\n\n"
    "Elige otro puerto host o cambia el protocolo.":
        "Une règle pour le port hôte {0} ({1}) existe déjà.\n\n"
        "Choisissez un autre port hôte ou changez le protocole.",

    # ================================================================
    # NetworkDeviceDialog
    # ================================================================
    "Redirigir puertos del host al guest a través del NAT de QEMU\n"
    "(hostfwd). Solo aplica cuando el backend es NAT.":
        "Rediriger des ports de l'hôte vers l'invité via le NAT de QEMU\n"
        "(hostfwd). Ne s'applique que lorsque le backend est NAT.",

    # ================================================================
    # _CreateMediumDialog
    # ================================================================
    "Disquete formateado como RAW. Se registra como tipo 'Disquete' en "
    "la biblioteca. Tamaños típicos: 720 KB, 1.44 MB, 2.88 MB.":
        "Disquette formatée RAW. Enregistrée comme type 'Disquette' dans "
        "la bibliothèque. Tailles typiques : 720 Ko, 1,44 Mo, 2,88 Mo.",
    "Disco virtual expandible (recomendado). El archivo en el host "
    "crece solo según se usa en el guest.":
        "Disque virtuel extensible (recommandé). Le fichier sur l'hôte "
        "ne grandit qu'au fur et à mesure de son utilisation dans l'invité.",
    "Disco RAW (imagen plana). Ocupa el tamaño completo en el host "
    "desde el momento de su creación.":
        "Disque RAW (image plate). Occupe toute la taille sur l'hôte "
        "dès sa création.",

    # ================================================================
    # _ExportOvfDialog
    # ================================================================
    "Exportar como OVF/OVA - {0}": "Exporter en OVF/OVA - {0}",
    "Exporta <b>{0}</b> como OVA (un solo archivo) o como OVF (carpeta con descriptor + discos sueltos).":
        "Exporte <b>{0}</b> comme OVA (fichier unique) ou comme OVF (dossier avec descripteur + disques séparés).",
    "QCOW2 (recomendado) - instantaneo y comprimido":
        "QCOW2 (recommandé) - instantané et compressé",
    "El disco se aplana (descartando snapshots internos) y se comprime con zlib. Ideal para reimportar en esta misma app.":
        "Le disque est aplati (en supprimant les instantanés internes) et compressé avec zlib. Idéal pour réimporter dans cette même application.",
    "VMDK stream-optimized - maxima compatibilidad con VirtualBox/VMware":
        "VMDK stream-optimized - compatibilité maximale avec VirtualBox/VMware",
    "Requiere conversion previa con qemu-img. Tarda mas y necesita espacio temporal. VMDK stream-optimized ya descarta snapshots.":
        "Nécessite une conversion préalable avec qemu-img. Plus long et nécessite de l'espace temporaire. VMDK stream-optimized supprime déjà les instantanés.",
    "Incluir medio de instalacion (BaseSystem.img)":
        "Inclure le support d'installation (BaseSystem.img)",
    "Incluir archivos ISO en el OVA":
        "Inclure les fichiers ISO dans l'OVA",
    "El disco se convertira a <b>VMDK stream-optimized</b>. Este formato ya descarta los snapshots internos.":
        "Le disque sera converti en <b>VMDK stream-optimized</b>. Ce format supprime déjà les instantanés internes.",
    "Los discos QCOW2 se <b>aplanan y comprimen</b> automaticamente al exportar: se descartan los snapshots internos y se aplica compresion zlib. Reduce el OVA entre un 40% y un 60%.":
        "Les disques QCOW2 sont <b>aplatis et compressés</b> automatiquement à l'exportation : les instantanés internes sont supprimés et une compression zlib est appliquée. Réduit l'OVA de 40 % à 60 %.",

    # ================================================================
    # _OvfImportPreviewDialog
    # ================================================================
    "Se ha leído el descriptor OVF. Revisa los datos detectados y corrige lo que haga falta antes de importar.<br><br><i>El sistema operativo detectado puede ser ambiguo: ajústalo si el original no coincide.</i>":
        "Le descripteur OVF a été lu. Vérifiez les données détectées et corrigez ce qui est nécessaire avant d'importer.<br><br><i>Le système d'exploitation détecté peut être ambigu : ajustez-le si l'original ne correspond pas.</i>",
    "(desconocido)": "(inconnu)",
    "(sin nombre)": "(sans nom)",
    "(sin discos)": "(sans disques)",
    "<b>Detectado en el OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}":
        "<b>Détecté dans l'OVF :</b><br>OS : {0} {1}<br>CPUs : {2} &nbsp; RAM : {3} Mo<br>Disques : {4} — {5}",
    "Nombre de la VM:": "Nom de la VM :",
    "GNU / Linux": "GNU / Linux",
    "Microsoft Windows": "Microsoft Windows",
    "Android (Android-x86 / Bliss OS)": "Android (Android-x86 / Bliss OS)",
    "Plataforma:": "Plateforme :",
    "Distribución / versión:": "Distribution / version :",
    "Importar solo la configuración (sin copiar los discos)":
        "Importer seulement la configuration (sans copier les disques)",
    "Si está marcado, se importan solo los datos del descriptor (CPU, RAM, red, sistema operativo) y NO se convierten ni copian los discos. Útil para reutilizar una configuración sin duplicar gigabytes de disco.":
        "Si coché, seules les données du descripteur sont importées (CPU, RAM, réseau, système d'exploitation) et les disques ne sont NI convertis NI copiés. Utile pour réutiliser une configuration sans dupliquer des gigaoctets de disque.",
    "Distribución:": "Distribution :",
    "Versión de Windows:": "Version de Windows :",
    "Versión de macOS:": "Version de macOS :",
    "Distribución Android:": "Distribution Android :",
    "Debes escribir un nombre para la VM importada.":
        "Vous devez saisir un nom pour la VM importée.",

    # ================================================================
    # _ShortcutsDialog + _ShortcutCaptureDialog
    # ================================================================
    "Haz clic en <b>Cambiar...</b> para capturar una nueva\n"
    "combinacion de teclas. Pulsa <b>Escape</b> durante la\n"
    "captura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\n"
    "para deshabilitar un atajo.":
        "Cliquez sur <b>Modifier…</b> pour capturer une nouvelle\n"
        "combinaison de touches. Appuyez sur <b>Échap</b> pendant\n"
        "la capture pour l'annuler. Utilisez <b>Suppr</b> ou <b>Retour arrière</b>\n"
        "pour désactiver un raccourci.",
    "El atajo {0} ya esta asignado a:\n\n  {1}\n\nElige otro o cambia primero el otro atajo.":
        "Le raccourci {0} est déjà assigné à :\n\n  {1}\n\nChoisissez-en un autre ou changez d'abord l'autre raccourci.",
    "¿Restaurar los cuatro atajos a sus valores por defecto?":
        "Restaurer les quatre raccourcis à leurs valeurs par défaut ?",
    "<b>Pulsa la combinacion de teclas que quieras asignar.</b>":
        "<b>Appuyez sur la combinaison de touches à assigner.</b>",
    "Esperando pulsacion...\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "En attente d'une touche…\n\nÉchap annule. Suppr ou Retour arrière désactive le raccourci.",
    "Atajo actual: <b>{0}</b>": "Raccourci actuel : <b>{0}</b>",
    "Solo has pulsado un modificador. Anade una tecla normal.\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "Vous n'avez appuyé que sur un modificateur. Ajoutez une touche normale.\n\nÉchap annule. Suppr ou Retour arrière désactive le raccourci.",

    # --- i18n_fr_tanda2a_v1 ---
}
