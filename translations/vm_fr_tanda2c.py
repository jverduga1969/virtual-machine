# -*- coding: utf-8 -*-
"""Frances — Tanda 2c: import/export + guest_integration + estados."""

TRANSLATIONS = {

    # ================================================================
    # Import / Export
    # ================================================================
    "¿Cómo quieres importar la máquina virtual?\n\n  • Desde carpeta: selecciona una carpeta que contenga vm_config.ini.\n  • Desde archivo: selecciona un .ova o .ovf (formato estándar OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip exportado previamente desde otra instalación de Virtual.Machine.":
        "Comment voulez-vous importer la machine virtuelle ?\n\n  • Depuis un dossier : sélectionnez un dossier contenant vm_config.ini.\n  • Depuis un fichier : sélectionnez un .ova ou .ovf (format standard OVF, portable vers VirtualBox/VMware), ou un .tar.gz / .tar / .zip précédemment exporté depuis une autre installation de Virtual.Machine.",
    "📁 Desde carpeta…": "📁 Depuis un dossier…",
    "🗜️ Desde archivo…": "🗜️ Depuis un fichier…",
    "Selecciona la carpeta de la VM a importar":
        "Sélectionnez le dossier de la VM à importer",
    "Selecciona el archivo a importar":
        "Sélectionnez le fichier à importer",
    "OVF/OVA (*.ova *.ovf);;Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;Todos los archivos (*)":
        "OVF/OVA (*.ova *.ovf);;Fichiers VM empaquetés (*.tar.gz *.tgz *.tar *.zip);;Tous les fichiers (*)",
    "Formato de archivo no reconocido. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.":
        "Format de fichier non reconnu. Utilisez .tar.gz, .tgz, .tar, .zip, .ova ou .ovf.",
    "La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\nAsegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.":
        "Le dossier sélectionné ne contient pas vm_config.ini :\n\n{0}\n\nAssurez-vous de choisir le dossier racine de la VM, pas un sous-dossier.",
    "Nombre para la VM importada:\n\n(se importará desde {0})":
        "Nom pour la VM importée :\n\n(sera importée depuis {0})",
    "Nombre inválido.": "Nom invalide.",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Une VM nommée '{0}' existe déjà.\n\nLa remplacer ? (l'actuelle sera supprimée)",
    "Copiando/desempaquetando en el sistema de archivos del destino (no en /tmp)…":
        "Copie/décompression dans le système de fichiers de destination (pas dans /tmp)…",
    "Desempaquetando archivo…": "Décompression du fichier…",
    "Extrayendo {0}/{1}…": "Extraction {0}/{1}…",
    "El archivo no contiene ninguna VM válida (no se encontró vm_config.ini).":
        "Le fichier ne contient aucune VM valide (vm_config.ini introuvable).",
    "Importación completada.": "Importation terminée.",
    "Copiando {0}": "Copie de {0}",
    "VM '{0}' importada correctamente.\n\nRevisa su configuración en la pestaña Configuración antes de arrancarla, especialmente si la importaste desde otro host: puede referenciar rutas que no existan aquí (carpetas compartidas, ISOs externas, dispositivos de passthrough).":
        "VM '{0}' importée correctement.\n\nVérifiez sa configuration dans l'onglet Configuration avant de la démarrer, surtout si vous l'avez importée depuis un autre hôte : elle peut référencer des chemins qui n'existent pas ici (dossiers partagés, ISOs externes, périphériques en passthrough).",
    "La VM '{0}' está {1}.\n\nSe recomienda apagarla antes de exportar: si está corriendo, los discos pueden estar en un estado inconsistente (cambios sin sincronizar a disco, locks activos…).\n\n¿Continuar de todos modos?":
        "La VM '{0}' est {1}.\n\nIl est recommandé de l'éteindre avant l'exportation : si elle tourne, les disques peuvent être dans un état incohérent (changements non synchronisés, verrous actifs…).\n\nContinuer quand même ?",
    "Copia de carpeta (más rápido, editable)":
        "Copie de dossier (plus rapide, modifiable)",
    "Archivo .tar.gz (comprimido, portable)":
        "Fichier .tar.gz (compressé, portable)",
    "Archivo .zip (compatible con Windows)":
        "Fichier .zip (compatible Windows)",
    "Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)":
        "Fichier .ova (Open Virtual Appliance, portable vers VirtualBox/VMware)",
    "Descriptor .ovf + discos sueltos (carpeta)":
        "Descripteur .ovf + disques séparés (dossier)",
    "Formato para exportar '{0}':": "Format pour exporter '{0}' :",
    "Elige la carpeta donde crear la copia":
        "Choisissez le dossier où créer la copie",
    "En la carpeta destino ya existe '{0}'.\n\n¿Sobrescribir? (se borrará la carpeta destino existente)":
        "Dans le dossier de destination, '{0}' existe déjà.\n\nÉcraser ? (le dossier de destination existant sera supprimé)",
    "Guardar archivo de exportación": "Enregistrer le fichier d'exportation",
    "Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)":
        "Fichier tar.gz (*.tar.gz);;Fichier zip (*.zip)",
    "Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)":
        "Fichier zip (*.zip);;Fichier tar.gz (*.tar.gz)",
    "El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?":
        "Le fichier de destination existe déjà :\n{0}\n\nÉcraser ?",
    "Confirmar exportación": "Confirmer l'exportation",
    "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Contenido: {2} archivo(s), {3}\n  • Destino: {4}\n\nLos archivos de bloqueo (pids, sockets) y logs se omitirán.":
        "Exporter '{0}' comme :\n\n  • Format : {1}\n  • Contenu : {2} fichier(s), {3}\n  • Destination : {4}\n\nLes fichiers de verrouillage (pids, sockets) et journaux seront ignorés.",
    "No se pudo completar la exportación.\n\n{0}":
        "Impossible de terminer l'exportation.\n\n{0}",
    "{0} archivo(s), {1} en total": "{0} fichier(s), {1} au total",
    "Exportación cancelada por el usuario.":
        "Exportation annulée par l'utilisateur.",
    "Formato de exportación desconocido: {0}":
        "Format d'exportation inconnu : {0}",
    "Exportación completada ({0} archivo(s)).":
        "Exportation terminée ({0} fichier(s)).",
    "'{0}' exportada correctamente.\n\nDestino: {1}":
        "'{0}' exportée correctement.\n\nDestination : {1}",

    # ================================================================
    # Clon / Desenlazar
    # ================================================================
    "Clonar máquina virtual": "Cloner la machine virtuelle",
    "Nombre para el clon de '{0}':": "Nom pour le clone de '{0}' :",
    "Debes escribir un nombre para el clon.":
        "Vous devez saisir un nom pour le clone.",
    "Nombre ya existente": "Nom déjà existant",
    "La máquina virtual '{0}' ya existe en el listado.\n\nElige otro nombre para el clon.":
        "La machine virtuelle '{0}' existe déjà dans la liste.\n\nChoisissez un autre nom pour le clone.",
    "Ese nombre no puede utilizarse para una máquina virtual.":
        "Ce nom ne peut pas être utilisé pour une machine virtuelle.",
    "Clonar VM": "Cloner la VM",
    "¿Qué tipo de clon quieres crear a partir de <b>{0}</b>?<br><br><b>Clon completo</b><br>Copia íntegra de todos los discos. Totalmente independiente del original; ocupa el mismo espacio que la VM original.<br><br><b>Clon enlazado</b><br>El disco base se comparte mediante un <i>backing file</i> QCOW2. La nueva VM solo guarda los cambios, así que ocupa muy poco. <b>Depende del original</b>: si se borra o se mueve el original, el clon se rompe.<br>El backing se guarda con <b>ruta relativa</b> para que puedas mover o copiar la carpeta <code>VirtualMachines/</code> entera a otro host sin romper nada.<br><br><b>Importante:</b> una vez que el clon arranque por primera vez, los cambios que hagas DESPUÉS en el original <b>NO se verán</b> en el clon: la vista de su sistema de archivos queda anclada al estado del primer arranque (los bloques que el clon ya escribió no vuelven a consultarse en el backing). Trata el original como de solo lectura mientras el clon exista, o desenlaza el clon con <b>🧬 Desenlazar</b> para independizarlo.":
        "Quel type de clone voulez-vous créer à partir de <b>{0}</b> ?<br><br><b>Clone complet</b><br>Copie intégrale de tous les disques. Totalement indépendant de l'original ; occupe le même espace que la VM originale.<br><br><b>Clone lié</b><br>Le disque de base est partagé via un <i>backing file</i> QCOW2. La nouvelle VM ne stocke que les changements, donc il occupe très peu. <b>Dépend de l'original</b> : si l'original est supprimé ou déplacé, le clone est cassé.<br>Le backing est enregistré avec un <b>chemin relatif</b> pour que vous puissiez déplacer ou copier le dossier <code>VirtualMachines/</code> entier vers un autre hôte sans rien casser.<br><br><b>Important :</b> une fois que le clone démarre pour la première fois, les changements effectués APRÈS dans l'original <b>ne seront PAS visibles</b> dans le clone : la vue de son système de fichiers est ancrée à l'état du premier démarrage (les blocs que le clone a déjà écrits ne sont plus relus dans le backing). Traitez l'original comme lecture seule tant que le clone existe, ou détachez le clone avec <b>🧬 Détacher</b> pour l'indépendantiser.",
    "No se pudo copiar la carpeta de la VM.\n\n{0}":
        "Impossible de copier le dossier de la VM.\n\n{0}",
    "La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}":
        "La VM a été copiée mais son vm_config.ini n'a pas pu être réécrit.\n\n{0}",
    "La máquina virtual '{0}' fue clonada correctamente (clon completo).\n\nSe han regenerado las direcciones MAC y los IDs internos de los discos para que no choquen con la VM original.":
        "La machine virtuelle '{0}' a été clonée correctement (clone complet).\n\nLes adresses MAC et les IDs internes des disques ont été régénérés pour ne pas entrer en conflit avec la VM originale.",
    "Clon enlazado con original en ejecución":
        "Clone lié avec original en cours d'exécution",
    "El original de este clon ('{0}') está corriendo.\n\nArrancar original y clon a la vez puede dar resultados impredecibles:\n\n  • El clon lee del disco del original los bloques que no ha modificado. Si el original escribe algo mientras el clon corre, el clon puede leer estados intermedios.\n  • La vista del sistema de archivos del clon ya está anclada al estado de su primer arranque para los bloques de metadatos, así que los cambios nuevos del original probablemente no se vean, pero el riesgo de lectura inconsistente sigue ahí.\n\nRecomendaciones:\n  • Apaga el original antes de arrancar el clon (o al revés).\n  • O desenlaza el clon con '🧬 Desenlazar' para que sea totalmente independiente.\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "L'original de ce clone ('{0}') est en cours d'exécution.\n\nDémarrer l'original et le clone en même temps peut donner des résultats imprévisibles :\n\n  • Le clone lit sur le disque de l'original les blocs qu'il n'a pas modifiés. Si l'original écrit quelque chose pendant que le clone tourne, le clone peut lire des états intermédiaires.\n  • La vue du système de fichiers du clone est déjà ancrée à l'état de son premier démarrage pour les blocs de métadonnées, donc les nouveaux changements de l'original ne seront probablement pas visibles, mais le risque de lecture incohérente persiste.\n\nRecommandations :\n  • Éteignez l'original avant de démarrer le clone (ou inversement).\n  • Ou détachez le clone avec '🧬 Détacher' pour qu'il soit totalement indépendant.\n\nCet avertissement ne réapparaîtra pas pour cette VM dans cette session.",
    "Clon enlazado con backing roto":
        "Clone lié avec backing cassé",
    "Este clon enlazado espera el backing en:\n\n    {0}\n\nResuelto contra su carpeta queda en:\n\n    {1}\n\nEse archivo no existe. La VM original ('{2}') probablemente se movió o se borró.\n\nQEMU fallará al arrancar con:\n    Could not open backing file: No such file or directory\n\nOpciones:\n  • Mueve también la VM original de vuelta a su carpeta, o\n  • Copia la carpeta 'VirtualMachines/' entera (con original\n    y clon juntos) a la nueva ubicación, o\n  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n    para independizar este clon (puede fallar si el backing\n    ya no está disponible).\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "Ce clone lié attend le backing à :\n\n    {0}\n\nRésolu par rapport à son dossier, il devient :\n\n    {1}\n\nCe fichier n'existe pas. La VM originale ('{2}') a probablement été déplacée ou supprimée.\n\nQEMU échouera au démarrage avec :\n    Could not open backing file: No such file or directory\n\nOptions :\n  • Ramenez aussi la VM originale dans son dossier, ou\n  • Copiez le dossier 'VirtualMachines/' entier (avec l'original\n    et le clone ensemble) vers le nouvel emplacement, ou\n  • Si vous pouvez encore, utilisez '🧬 Détacher' dans l'onglet Aperçu\n    pour rendre ce clone indépendant (peut échouer si le backing\n    n'est plus disponible).\n\nCet avertissement ne réapparaîtra pas pour cette VM dans cette session.",
    "No se pudo determinar el disco principal de la VM original.\n\nEl clon enlazado necesita un disco base QCOW2 sobre el que\ncrear el backing file. Si la VM no tiene discos, usa\n'Clon completo'.":
        "Impossible de déterminer le disque principal de la VM originale.\n\nLe clone lié a besoin d'un disque de base QCOW2 sur lequel\ncréer le backing file. Si la VM n'a pas de disques, utilisez\n'Clone complet'.",
    "No se pudo inspeccionar el disco original.\n\n{0}":
        "Impossible d'inspecter le disque original.\n\n{0}",
    "El disco principal de la VM original está en formato {0}.\n\nEl clon enlazado solo funciona con QCOW2 (necesita backing\nfile). Usa 'Clon completo' si quieres copiar el disco tal cual.":
        "Le disque principal de la VM originale est au format {0}.\n\nLe clone lié ne fonctionne qu'avec QCOW2 (il a besoin d'un backing\nfile). Utilisez 'Clone complet' si vous voulez copier le disque tel quel.",
    "No se pudo crear la carpeta del clon.\n\n{0}":
        "Impossible de créer le dossier du clone.\n\n{0}",
    "qemu-img create falló.\n\n{0}": "qemu-img create a échoué.\n\n{0}",
    "No se pudo crear el delta QCOW2.\n\n{0}":
        "Impossible de créer le delta QCOW2.\n\n{0}",
    "El backing file quedó guardado como ruta ABSOLUTA, lo que haría el clon no portable.\n\nSe ha abortado la operación para no dejar un clon defectuoso. Reporta esto como bug.":
        "Le backing file a été enregistré comme chemin ABSOLU, ce qui rendrait le clone non portable.\n\nL'opération a été abandonnée pour ne pas laisser un clone défectueux. Signalez ceci comme un bug.",
    "No se pudieron copiar los archivos auxiliares.\n\n{0}":
        "Impossible de copier les fichiers auxiliaires.\n\n{0}",
    "El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n{0}\n\nRevisa manualmente el archivo antes de usar la VM.":
        "Le clone a été créé mais son vm_config.ini n'a pas pu être réécrit.\n\n{0}\n\nVérifiez manuellement le fichier avant d'utiliser la VM.",
    "La máquina virtual '{0}' fue clonada correctamente (clon enlazado).\n\nEl disco base se comparte con el original mediante un backing\nfile QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\npero DEPENDE del original:\n\n  • Si borras o mueves la VM original, el clon se rompe.\n  • Una vez que el clon arranque por primera vez, los cambios\n    que hagas DESPUÉS en el original NO se verán en el clon:\n    la vista del sistema de archivos queda anclada al estado\n    del primer arranque. Trata el original como de solo lectura\n    mientras el clon exista.\n  • Los snapshots completos (RAM) no funcionarán en este clon\n    — solo de disco. QEMU no puede restaurar (loadvm) un\n    snapshot completo sobre un QCOW2 con backing file.\n  • Los snapshots del clon no son reproducibles mientras el\n    original pueda cambiar: al restaurar, se mezcla el delta\n    guardado con el estado ACTUAL del backing.\n  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n    apagado.\n\nPara mover o copiar la estructura completa a otro host,\nllévate la carpeta 'VirtualMachines/' entera.":
        "La machine virtuelle '{0}' a été clonée correctement (clone lié).\n\nLe disque de base est partagé avec l'original via un backing\nfile QCOW2 avec chemin relatif. Le clone occupe très peu d'espace,\nmais DÉPEND de l'original :\n\n  • Si vous supprimez ou déplacez la VM originale, le clone casse.\n  • Une fois que le clone démarre pour la première fois, les changements\n    effectués APRÈS dans l'original ne seront PAS visibles dans le clone :\n    la vue du système de fichiers est ancrée à l'état du premier\n    démarrage. Traitez l'original comme lecture seule tant que\n    le clone existe.\n  • Les instantanés complets (RAM) ne fonctionneront pas sur ce clone\n    — disque uniquement. QEMU ne peut pas restaurer (loadvm) un\n    instantané complet sur un QCOW2 avec backing file.\n  • Les instantanés du clone ne sont pas reproductibles tant que\n    l'original peut changer : à la restauration, le delta sauvegardé\n    se mélange avec l'état ACTUEL du backing.\n  • Si vous voulez l'indépendantiser, utilisez '🧬 Détacher' quand il est\n    éteint.\n\nPour déplacer ou copier la structure complète vers un autre hôte,\nemportez le dossier 'VirtualMachines/' entier.",
    "Desenlazar clon": "Détacher le clone",
    "Esta VM no es un clon enlazado, no hay nada que desenlazar.":
        "Cette VM n'est pas un clone lié, il n'y a rien à détacher.",
    "La VM '{0}' está encendida.\n\nApágala antes de desenlazarla: con QEMU activo el archivo\nestá bloqueado y el convert no puede reemplazarlo.":
        "La VM '{0}' est allumée.\n\nÉteignez-la avant de la détacher : avec QEMU actif, le fichier\nest verrouillé et le convert ne peut pas le remplacer.",
    "No se encontró el disco principal del clon.":
        "Le disque principal du clone n'a pas été trouvé.",
    "Se convertirá el disco principal del clon <b>{0}</b> en un QCOW2 <b>autónomo</b>.<br><br>Después de esto, el clon deja de depender del original y puede moverse o copiarse por separado.<br><br><b>Requiere:</b><br>&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>&nbsp;&nbsp;• La VM apagada (ya lo está).<br>&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>El resultado se verifica como QCOW2 válido y se reemplaza atómicamente. Si algo falla a mitad, el archivo original del clon queda intacto.":
        "Le disque principal du clone <b>{0}</b> sera converti en un QCOW2 <b>autonome</b>.<br><br>Après cela, le clone ne dépend plus de l'original et peut être déplacé ou copié séparément.<br><br><b>Nécessite :</b><br>&nbsp;&nbsp;• Espace libre sur l'hôte (~1,1× la taille du disque).<br>&nbsp;&nbsp;• La VM éteinte (c'est déjà le cas).<br>&nbsp;&nbsp;• Ne pas fermer l'application pendant le processus.<br><br>Le résultat est vérifié comme QCOW2 valide et remplacé atomiquement. Si quelque chose échoue en cours de route, le fichier original du clone reste intact.",
    "El clon '{0}' ya es autónomo.\n\nTamaño antes: {1}\nTamaño después: {2}\n\nPuedes mover la VM sin llevarte la original.":
        "Le clone '{0}' est maintenant autonome.\n\nTaille avant : {1}\nTaille après : {2}\n\nVous pouvez déplacer la VM sans emporter l'originale.",
    "No se pudo desenlazar el clon.\n\n{0}":
        "Impossible de détacher le clone.\n\n{0}",
    "Convirtiendo el clon en un QCOW2 autónomo…":
        "Conversion du clone en QCOW2 autonome…",

    # ================================================================
    # Eliminar VM
    # ================================================================
    "Eliminar VM": "Supprimer la VM",
    "Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n":
        "Seul le dossier de la machine virtuelle sera supprimé :\n\n{0}\n\n",
    "Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n":
        "Les supports suivants sont en dehors du dossier de la VM et ne seront PAS supprimés :\n",
    "⚠ ESTA VM ES EL ORIGINAL DE {0} CLON(ES) ENLAZADO(S):\n":
        "⚠ CETTE VM EST L'ORIGINAL DE {0} CLONE(S) LIÉ(S) :\n",
    "\n\nSi continúas, esos clones quedarán inutilizables (su backing file ya no existirá).\n\nSe recomienda desenlazarlos primero: selecciona cada clon y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n":
        "\n\nSi vous continuez, ces clones deviendront inutilisables (leur backing file n'existera plus).\n\nIl est recommandé de les détacher d'abord : sélectionnez chaque clone et cliquez sur '🧬 Détacher' dans son onglet Aperçu.\n\n",
    "Eliminar máquina virtual": "Supprimer la machine virtuelle",
    "No se pudo eliminar '{0}'.\n\n{1}":
        "Impossible de supprimer '{0}'.\n\n{1}",

    # ================================================================
    # OVF/OVA: errores
    # ================================================================
    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la carpeta de la VM ({0}). Sin este archivo la VM no tiene sistema operativo que exportar.":
        "VM macOS : mac_hdd_ng.qcow2 introuvable dans le dossier de la VM ({0}). Sans ce fichier la VM n'a pas de système d'exploitation à exporter.",
    "La VM no tiene discos adjuntos que exportar. Añade al menos un disco en Configuración → Almacenamiento.":
        "La VM n'a aucun disque joint à exporter. Ajoutez au moins un disque dans Configuration → Stockage.",
    "qemu-img convert -c falló para '{0}': {1}":
        "qemu-img convert -c a échoué pour '{0}' : {1}",
    "El aplanado+compresión de '{0}' no produjo un archivo válido.":
        "L'aplatissement+compression de '{0}' n'a pas produit de fichier valide.",
    "El archivo .ova no contiene ningún descriptor .ovf.":
        "Le fichier .ova ne contient aucun descripteur .ovf.",
    "El archivo .ovf está vacío.": "Le fichier .ovf est vide.",
    "No se pudo leer el descriptor.\n\n{0}":
        "Impossible de lire le descripteur.\n\n{0}",
    "El descriptor OVF no se pudo interpretar.\n\n{0}":
        "Le descripteur OVF n'a pas pu être interprété.\n\n{0}",
    "No se pudo completar la importación.\n\n{0}":
        "Impossible de terminer l'importation.\n\n{0}",
    "Extrayendo y preparando el OVF/OVA...":
        "Extraction et préparation de l'OVF/OVA…",

    # ================================================================
    # Guest integration: QGA / carpetas / clipboard
    # ================================================================
    "Las dependencias del host ya están instaladas.":
        "Les dépendances de l'hôte sont déjà installées.",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Manquantes :\n\n• {0}\n\nVoulez-vous les installer maintenant via le gestionnaire de paquets du système ?",
    "Las dependencias de carpetas compartidas quedaron instaladas y verificadas.":
        "Les dépendances de dossiers partagés ont été installées et vérifiées.",
    "No se pudieron instalar todas las dependencias.\n\n{0}":
        "Toutes les dépendances n'ont pas pu être installées.\n\n{0}",
    "El socket de QEMU Guest Agent no está disponible.":
        "Le socket du QEMU Guest Agent n'est pas disponible.",
    "QEMU Guest Agent cerró el canal durante la sincronización.":
        "QEMU Guest Agent a fermé le canal pendant la synchronisation.",
    "Tiempo agotado sincronizando QEMU Guest Agent.":
        "Délai dépassé en synchronisant QEMU Guest Agent.",
    "QEMU Guest Agent cerró el canal.":
        "QEMU Guest Agent a fermé le canal.",
    "Tiempo agotado esperando la respuesta de QEMU Guest Agent.":
        "Délai dépassé en attendant la réponse du QEMU Guest Agent.",
    "Guest Agent no devolvió el PID de guest-exec.":
        "Le Guest Agent n'a pas renvoyé le PID de guest-exec.",
    "guest-exec terminó con código {0}.":
        "guest-exec s'est terminé avec le code {0}.",
    "Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent.":
        "Délai dépassé en attendant la fin de la commande exécutée via QEMU Guest Agent.",
    "El canal de QEMU Guest Agent no está disponible en esta VM.":
        "Le canal du QEMU Guest Agent n'est pas disponible sur cette VM.",
    "El Guest Agent del invitado no respondió en {0} s (no está instalado o no se está ejecutando).":
        "Le Guest Agent de l'invité n'a pas répondu en {0} s (non installé ou non en cours d'exécution).",
    "La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n{0}\n\nComprueba que qemu-guest-agent esté instalado y ejecutándose en el guest (pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.":
        "La VM a démarré, mais le montage automatique dans l'OS n'a pas pu être configuré.\n\n{0}\n\nVérifiez que qemu-guest-agent est installé et en cours d'exécution dans l'invité (onglet Guest Tools). Une fois installé, le montage se fera automatiquement au prochain démarrage de la VM.",
    "La carpeta compartida VirtioFS ya está conectada a la VM.\n\nEn Linux el dispositivo debe montarse dentro del guest. En un LiveCD no es posible hacerlo de forma persistente desde el host sin un agente instalado en el guest.\n\nComando(s):\n\n":
        "Le dossier partagé VirtioFS est déjà connecté à la VM.\n\nSous Linux, le périphérique doit être monté dans l'invité. Sur un LiveCD, il n'est pas possible de le faire de manière persistante depuis l'hôte sans un agent installé dans l'invité.\n\nCommande(s) :\n\n",
    "\n\nEn una instalación Linux permanente podremos añadir automontaje mediante fstab/systemd en una versión posterior.":
        "\n\nSur une installation Linux permanente, nous pourrons ajouter le montage automatique via fstab/systemd dans une version ultérieure.",
    "Carpeta:\n{0}": "Dossier :\n{0}",
    "Generando ISO de Guest Tools…": "Génération de l'ISO Guest Tools…",
    "ISO creada.": "ISO créée.",
    "ISO disponible: {0}": "ISO disponible : {0}",
    "Crear ISO de Guest Tools": "Créer l'ISO Guest Tools",
    "No se pudo crear la ISO.\n\n{0}":
        "Impossible de créer l'ISO.\n\n{0}",
    "La ISO se guarda en la carpeta GuestTools.":
        "L'ISO est enregistrée dans le dossier GuestTools.",
    "Selecciona (o crea) una VM primero.":
        "Sélectionnez (ou créez) d'abord une VM.",
    "Creando ISO de Guest Tools…": "Création de l'ISO Guest Tools…",
    "Guest Tools — Adjuntar a la VM": "Guest Tools — Attacher à la VM",
    "No se pudo crear ni adjuntar la ISO.\n\n{0}":
        "Impossible de créer ou d'attacher l'ISO.\n\n{0}",
    "Se creará la ISO y se adjuntará como CD/DVD a esta VM.":
        "L'ISO sera créée et attachée comme CD/DVD à cette VM.",
    "Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD.":
        "Cette VM a déjà l'ISO Guest Tools attachée comme CD/DVD.",
    "ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\nEn el próximo arranque, dentro del guest: monta la unidad y ejecuta\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).":
        "ISO Guest Tools attachée à cette VM comme CD/DVD.\n\nAu prochain démarrage, dans l'invité : montez le lecteur et exécutez\nINSTALL-LINUX.SH (avec sudo) ou INSTALL-WINDOWS.CMD (en tant qu'Administrateur).",
    "No se pudo adjuntar la ISO.\n\n{0}":
        "Impossible d'attacher l'ISO.\n\n{0}",
    "Estado: canal no disponible. Enciende la VM con Guest Agent activado.":
        "État : canal non disponible. Démarrez la VM avec le Guest Agent activé.",
    "Estado: consultando al Guest Agent...":
        "État : interrogation du Guest Agent…",
    "Estado: sin respuesta del guest agent ({0}).":
        "État : pas de réponse du guest agent ({0}).",
    "Estado: QEMU Guest Agent responde correctamente (v{0}).":
        "État : QEMU Guest Agent répond correctement (v{0}).",
    "Estado: QGA respondió con un error: {0}":
        "État : QGA a répondu avec une erreur : {0}",
    "Estado: canal QGA presente; pulsa Probar conexión.":
        "État : canal QGA présent ; appuyez sur Tester la connexion.",
    "Estado: canal QGA no activo en este momento.":
        "État : canal QGA inactif pour le moment.",
    "La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.":
        "La politique de montage est la même pour tous les OS : Manuel, Automatique au démarrage de l'OS ou Automatique à la demande. Le mécanisme de montage réel s'adapte à l'OS invité et à ses composants d'intégration. Sur un LiveCD, le montage persistant ne peut généralement pas être configuré depuis l'hôte.",
    "La carpeta del host no existe o no es un directorio.":
        "Le dossier de l'hôte n'existe pas ou n'est pas un répertoire.",
    "No se añadirá ningún canal de clipboard.":
        "Aucun canal de presse-papiers ne sera ajouté.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK : bidirectionnel. Nécessite spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS : intégration du presse-papiers en attente.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Sélectionnez une VM pour vérifier l'intégration disponible.",
    "Se activará automáticamente al iniciar la VM.":
        "Sera activé automatiquement au démarrage de la VM.",
    "No se activa.": "N'est pas activé.",
    "Configuración actual: {0}. {1} {2}":
        "Configuration actuelle : {0}. {1} {2}",
    "Configuración del clipboard guardada para esta VM.":
        "Configuration du presse-papiers enregistrée pour cette VM.",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Configuration enregistrée. Elle sera appliquée au prochain démarrage.",

    # ================================================================
    # i18n_tanda_fr_2c_v1
    # ================================================================
}
