# -*- coding: utf-8 -*-
"""Frances — Fix 1: cierra los 78 pendientes que no matchearon por
bytes invisibles (VS16 en emojis, comillas tipograficas, <br> distintos).
Las claves estan copiadas textualmente del listado de pendientes.
"""

TRANSLATIONS = {

# ---- 1-3: emoji VS16 + listas + RAM -----
"🖼 Mostrar la VM dentro de la app (consola VNC embebida)":
    "🖼 Afficher la VM dans l'application (console VNC intégrée)",

"Muestra solo las VMs de un grupo concreto.\n  • Todos los grupos: sin filtro de grupo.\n  • Sin grupo: solo VMs sin etiqueta de grupo.\n  • <nombre>: solo VMs con ese grupo.\n\nLos grupos se asignan desde el botón '🏷 Etiqueta' del Resumen.":
    "Afficher uniquement les VM d'un groupe spécifique.\n  • Tous les groupes : sans filtre de groupe.\n  • Sans groupe : uniquement les VM sans étiquette de groupe.\n  • <nom> : uniquement les VM de ce groupe.\n\nLes groupes sont assignés depuis le bouton '🏷 Étiquette' de l'Aperçu.",

"Guarda la RAM y el estado de los dispositivos a disco (como un\nsnapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\nEl snapshot aparecerá en la pestaña Snapshots y su captura de\npantalla en el panel 'Último snapshot'.":
    "Enregistre la RAM et l'état des périphériques sur disque (comme un\ninstantané) puis met la VM en pause. Plus long mais survit aux redémarrages.\nL'instantané apparaîtra dans l'onglet Instantanés et sa capture\nd'écran dans le panneau 'Dernier instantané'.",

# ---- 4-6: seleccion + plantilla + API -----
"Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
    "Sélectionnez une VM pour la gérer. Utilisez 'Nouvelle machine virtuelle' pour en créer une autre.",

"Guarda la configuración de hardware de esta VM como\nplantilla reutilizable. Se omiten discos, ISOs, MACs,\ncarpetas compartidas, notas y reglas NAT.\nAparecerá en el menú del botón '➕ Nueva VM'.":
    "Enregistre la configuration matérielle de cette VM comme\nmodèle réutilisable. Les disques, ISOs, MACs,\ndossiers partagés, notes et règles NAT sont ignorés.\nIl apparaîtra dans le menu du bouton '➕ Nouvelle VM'.",

"Ejemplo de uso desde terminal:<br><code>curl -H 'X-API-Token: &lt;tu-token&gt;' http://127.0.0.1:8730/api/vms</code>":
    "Exemple d'utilisation depuis le terminal :<br><code>curl -H 'X-API-Token: &lt;votre-jeton&gt;' http://127.0.0.1:8730/api/vms</code>",

# ---- 7-12: API + apariencia + presentacion -----
"<b style='color:#2e7d32;'>Activa</b> — {0} peticiones desde el arranque":
    "<b style='color:#2e7d32;'>Active</b> — {0} requêtes depuis le démarrage",

"<b style='color:#888;'>Detenida</b>":
    "<b style='color:#888;'>Arrêtée</b>",

"Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\nreiniciar la app para que TODOS los widgets se repinten con los\ncolores nuevos (depende del estilo del escritorio).":
    "En passant de 'Système' à 'Clair/Sombre', il peut être nécessaire\nde redémarrer l'application pour que TOUS les widgets soient repeints avec les\nnouvelles couleurs (dépend du style du bureau).",

"La VM '{0}' no está corriendo. Enciéndela antes de entrar en modo presentación.":
    "La VM '{0}' n'est pas en cours d'exécution. Démarrez-la avant d'entrer en mode présentation.",

"La VM esta encendida.\n\nPara evitar una copia inconsistente, apagala primero, o marca la opcion 'Tambien cuando la VM esta encendida' en esta seccion (asumiendo el riesgo).":
    "La VM est allumée.\n\nPour éviter une copie incohérente, éteignez-la d'abord, ou cochez l'option 'Aussi quand la VM est allumée' dans cette section (en assumant le risque).",

"==> Comparar defaults: aplicados {0} campo(s) a '{1}'.":
    "==> Comparer les valeurs par défaut : {0} champ(s) appliqué(s) à '{1}'.",

# ---- 13-15: bloques VNC / SPICE / Hibrida -----
"<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Compatible con cualquier gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Se puede embeber dentro de la app, incluso en Wayland.<br><span style='color:#2e7d32;'>✓</span> Muchos visores externos disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> Sin dependencias adicionales en el guest para funcionar.<br><span style='color:#c62828;'>✗</span> Sin aceleración 3D ni streaming de video (redibuja por regiones).<br><span style='color:#c62828;'>✗</span> Clipboard limitado: solo texto, y el guest necesita <code>vncconfig</code> corriendo.<br><span style='color:#c62828;'>✗</span> Sin audio remoto.<br><span style='color:#c62828;'>✗</span> Menos fluido en uso intensivo (vídeo, animaciones, 3D).":
    "<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Compatible avec tout graphique virtuel (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Peut être intégré dans l'application, même sous Wayland.<br><span style='color:#2e7d32;'>✓</span> De nombreuses visionneuses externes disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> Aucune dépendance supplémentaire dans l'invité pour fonctionner.<br><span style='color:#c62828;'>✗</span> Pas d'accélération 3D ni de streaming vidéo (redessine par régions).<br><span style='color:#c62828;'>✗</span> Presse-papiers limité : texte uniquement, et l'invité a besoin de <code>vncconfig</code> en cours d'exécution.<br><span style='color:#c62828;'>✗</span> Pas d'audio distant.<br><span style='color:#c62828;'>✗</span> Moins fluide en usage intensif (vidéo, animations, 3D).",

"<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Mejor rendimiento y fluidez en local (compresión + streaming de video).<br><span style='color:#2e7d32;'>✓</span> Clipboard bidireccional avanzado (con <code>spice-vdagent</code> en el guest).<br><span style='color:#2e7d32;'>✓</span> Audio remoto integrado.<br><span style='color:#2e7d32;'>✓</span> Varios monitores, redirección USB y carpetas compartidas nativas.<br><span style='color:#c62828;'>✗</span> No se puede embeber en Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Requiere un visor externo (spicy o remote-viewer) si no se puede embeber.<br><span style='color:#c62828;'>✗</span> Para aprovecharlo hay que instalar <code>spice-vdagent</code> en el guest.<br><span style='color:#c62828;'>✗</span> Incompatible con VirGL y Venus (usan OpenGL y obligan a la ventana nativa de QEMU).":
    "<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Meilleure performance et fluidité en local (compression + streaming vidéo).<br><span style='color:#2e7d32;'>✓</span> Presse-papiers bidirectionnel avancé (avec <code>spice-vdagent</code> dans l'invité).<br><span style='color:#2e7d32;'>✓</span> Audio distant intégré.<br><span style='color:#2e7d32;'>✓</span> Plusieurs moniteurs, redirection USB et dossiers partagés natifs.<br><span style='color:#c62828;'>✗</span> Ne peut pas être intégré sous Wayland (X11 uniquement, avec spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Nécessite une visionneuse externe (spicy ou remote-viewer) s'il ne peut pas être intégré.<br><span style='color:#c62828;'>✗</span> Pour en profiter, il faut installer <code>spice-vdagent</code> dans l'invité.<br><span style='color:#c62828;'>✗</span> Incompatible avec VirGL et Venus (utilisent OpenGL et forcent la fenêtre native de QEMU).",

"<b>Híbrida (VNC embebido + SPICE externo)</b><br><span style='color:#2e7d32;'>✓</span> Lo mejor de ambos: VNC siempre visible dentro de la app, SPICE para rendimiento y clipboard.<br><span style='color:#2e7d32;'>✓</span> Funciona en cualquier sesión: Wayland o X11.<br><span style='color:#2e7d32;'>✓</span> Si spicy falla o lo cierras, el widget VNC sigue funcionando.<br><span style='color:#2e7d32;'>✓</span> Útil para ver la VM en dos monitores o para grabar y controlar a la vez.<br><span style='color:#c62828;'>✗</span> Consume más recursos: QEMU mantiene dos servidores de display en paralelo.<br><span style='color:#c62828;'>✗</span> Verás la misma VM en dos ventanas (dentro de la app y en la de spicy).<br><span style='color:#c62828;'>✗</span> La configuración del guest para sacar partido a SPICE (vdagent, drivers) hay que hacerla igual.<br><span style='color:#c62828;'>✗</span> Como SPICE, incompatible con VirGL y Venus.":
    "<b>Hybride (VNC intégré + SPICE externe)</b><br><span style='color:#2e7d32;'>✓</span> Le meilleur des deux : VNC toujours visible dans l'application, SPICE pour la performance et le presse-papiers.<br><span style='color:#2e7d32;'>✓</span> Fonctionne dans n'importe quelle session : Wayland ou X11.<br><span style='color:#2e7d32;'>✓</span> Si spicy échoue ou que vous le fermez, le widget VNC continue de fonctionner.<br><span style='color:#2e7d32;'>✓</span> Utile pour voir la VM sur deux moniteurs ou pour enregistrer et contrôler en même temps.<br><span style='color:#c62828;'>✗</span> Consomme plus de ressources : QEMU maintient deux serveurs d'affichage en parallèle.<br><span style='color:#c62828;'>✗</span> Vous verrez la même VM dans deux fenêtres (dans l'application et dans spicy).<br><span style='color:#c62828;'>✗</span> La configuration de l'invité pour profiter de SPICE (vdagent, pilotes) doit être faite de la même manière.<br><span style='color:#c62828;'>✗</span> Comme SPICE, incompatible avec VirGL et Venus.",

# ---- 16-18: panel izquierdo + salud -----
"VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):":
    "VM avec QEMU en cours d'exécution (non modifiées ici, utilisez 'Arrêter la VM' si vous voulez les éteindre) :",

"Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema.":
    "Appuyez sur 'Vérifier les dépendances' pour effectuer le diagnostic complet du système.",

"<b style='font-size:15px;'>🚦 Semáforos de salud</b>":
    "<b style='font-size:15px;'>🚦 Feux de santé</b>",

# ---- 19-26: macOS + preflight + OVF -----
"Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.":
    "Pour macOS, utilisez 'Télécharger System Recovery'. Apple distribue l'installateur complet comme une application ; le flux Recovery d'OSX-KVM est la méthode intégrée à ce gestionnaire.",

"El dispositivo de almacenamiento '{0}' apunta a un archivo que ya no existe: {1}":
    "Le périphérique de stockage '{0}' pointe vers un fichier qui n'existe plus : {1}",

"La carpeta compartida '{0}' apunta a una ruta del host que ya no existe: {1}":
    "Le dossier partagé '{0}' pointe vers un chemin de l'hôte qui n'existe plus : {1}",

"El orden de arranque prioriza el CD/DVD, pero el disco '{0}' ya tiene datos (~{1} GB). Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo.":
    "L'ordre de démarrage donne la priorité au CD/DVD, mais le disque '{0}' contient déjà des données (~{1} Go). Si le système est déjà installé, cela peut tenter de le réinstaller au lieu de le démarrer.",

"'{0}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco (dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\nDetén la VM actual antes de volver a iniciarla.":
    "'{0}' a déjà un processus QEMU actif. Le relancer peut corrompre le disque (deux processus écrivant dans le même fichier) ou entrer en conflit avec les sockets déjà utilisés.\n\nArrêtez la VM actuelle avant de la relancer.",

"No se encuentra la carpeta 'OSX-KVM'.":
    "Le dossier 'OSX-KVM' est introuvable.",

"Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.":
    "Vous devez indiquer un chemin de fichier ISO Windows valide ou sélectionner 'Télécharger automatiquement l'installateur Windows' dans CD/DVD.",

"No se pudo guardar vm_config.ini para '{0}': {1}":
    "Impossible d'enregistrer vm_config.ini pour '{0}' : {1}",

# ---- 27-30: media library -----
"<b>Biblioteca de Medios</b><br><span style='color:#666;font-size:11px;'>Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un unico sitio. Viven en <code>MediaLibrary/</code> (al mismo nivel que <code>VirtualMachines/</code>) y se reutilizan entre maquinas.</span>":
    "<b>Bibliothèque de médias</b><br><span style='color:#666;font-size:11px;'>Toutes les ISOs / IMGs / DMGs que vous utilisez avec vos VM, en un seul endroit. Elles vivent dans <code>MediaLibrary/</code> (au même niveau que <code>VirtualMachines/</code>) et sont réutilisées entre les machines.</span>",

"Recorre todas las VMs en VirtualMachines/ y registra sus discos duros, ISOs y disquetes en la biblioteca.\n\nLa misma ISO usada por varias VMs aparece UNA SOLA VEZ, con todas las VMs en la columna 'Usada por'. Las entradas que ya no usa ninguna VM se marcan como huerfanas pero no se borran.":
    "Parcourt toutes les VM dans VirtualMachines/ et enregistre leurs disques durs, ISOs et disquettes dans la bibliothèque.\n\nLa même ISO utilisée par plusieurs VM n'apparaît qu'UNE SEULE FOIS, avec toutes les VM dans la colonne 'Utilisé par'. Les entrées qu'aucune VM n'utilise plus sont marquées comme orphelines mais ne sont pas supprimées.",

"Aumentar el tamaño virtual de un disco QCOW2/RAW de la\nbiblioteca. Requiere que ninguna VM lo esté usando en\nes momento. El disco solo puede crecer.":
    "Augmenter la taille virtuelle d'un disque QCOW2/RAW de la\nbibliothèque. Nécessite qu'aucune VM ne l'utilise à\nce moment. Le disque ne peut que grandir.",

"- {0} entrada(s) ya no las usa ninguna VM (siguen visibles; filtro Origen = 'Huerfanas de VM').":
    "- {0} entrée(s) ne sont plus utilisées par aucune VM (toujours visibles ; filtre Origine = 'Orphelins de VM').",

# ---- 31-42: media library: agrandar, compactar, sha256, pkexec -----
"Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de agrandarlo.":
    "Ce disque est utilisé par la VM '{0}', qui est allumée.\n\nÉteignez-la avant de l'agrandir.",

"'{0}' no es un tamaño válido.":
    "'{0}' n'est pas une taille valide.",

"Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de compactarlo: QEMU mantiene un lock de\nescritura sobre el archivo y el compactado fallaria.":
    "Ce disque est utilisé par la VM '{0}', qui est allumée.\n\nÉteignez-la avant de le compacter : QEMU maintient un verrou\nd'écriture sur le fichier et la compaction échouerait.",

"¿Compactar '{0}'?\n\nReescribe el QCOW2 eliminando bloques no usados: reduce el\narchivo en el host SIN cambiar el tamaño virtual que ve el\ninvitado.{1}\n\n¿Continuar?":
    "Compacter '{0}' ?\n\nRéécrit le QCOW2 en supprimant les blocs non utilisés : réduit le\nfichier sur l'hôte SANS changer la taille virtuelle que voit\nl'invité.{1}\n\nContinuer ?",

"'{0}' compactado.\n\nAntes: {1}\nDespués: {2}\nAhorro: {3}":
    "'{0}' compacté.\n\nAvant : {1}\nAprès : {2}\nÉconomie : {3}",

"Compactando '{0}'":
    "Compaction de '{0}'",

"El archivo existe. No hay sha256 guardado para comparar; usa 'Calcular SHA256' si quieres uno.":
    "Le fichier existe. Aucun sha256 enregistré pour comparer ; utilisez 'Calculer le SHA256' si vous en voulez un.",

"Eliminar '{0}' de la biblioteca?":
    "Supprimer '{0}' de la bibliothèque ?",

"No se encontró 'pkexec'. No puedo solicitar permisos administrativos automáticamente.":
    "'pkexec' introuvable. Impossible de demander automatiquement les permissions administratives.",

"No se encontró 'pkexec'. Instálalo (paquete 'polkit') para que la aplicación pueda solicitar permisos administrativos de forma gráfica.":
    "'pkexec' introuvable. Installez-le (paquet 'polkit') pour que l'application puisse demander les permissions administratives graphiquement.",

"No se encontró 'udevadm'. Este sistema parece no usar udev para gestionar dispositivos USB. Aplica los permisos manualmente según tu distribución.":
    "'udevadm' introuvable. Ce système ne semble pas utiliser udev pour gérer les périphériques USB. Appliquez les permissions manuellement selon votre distribution.",

"💿 Medios de '{0}'":
    "💿 Médias de '{0}'",

# ---- 43-44: snapshots programados -----
"Cuando esta activo, la app crea snapshots de disco automaticamente en esta VM segun la frecuencia elegida.\n\nLos snapshots programados son SOLO DE DISCOS (no guardan RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan por antiguedad al superar el limite de retencion.\n\nNo se ejecutan si la VM esta apagada.":
    "Lorsque cette option est active, l'application crée automatiquement des instantanés de disque sur cette VM selon la fréquence choisie.\n\nLes instantanés programmés sont DISQUE UNIQUEMENT (ils n'enregistrent ni la RAM ni les fenêtres). Ils sont créés avec le préfixe 'auto_' et supprimés par ancienneté au-delà de la limite de rétention.\n\nIls ne s'exécutent pas si la VM est éteinte.",

"Cuantos snapshots automaticos conservar. Al superar este numero se eliminan los mas antiguos (solo los que empiezan por 'auto_'; los manuales nunca se tocan).":
    "Combien d'instantanés automatiques conserver. Au-delà de ce nombre, les plus anciens sont supprimés (uniquement ceux commençant par 'auto_' ; les manuels ne sont jamais touchés).",

# ---- 45-66: snapshots dialogos y errores -----
"La VM no se apagó dentro del tiempo máximo (90 s).\n\nPuede que el sistema invitado esté colgado. Usa el botón\n'Forzar apagado' de la lista lateral, luego vuelve a intentar\nrestaurar el snapshot con la VM ya apagada.":
    "La VM ne s'est pas éteinte dans le temps maximum (90 s).\n\nLe système invité est peut-être bloqué. Utilisez le bouton\n'Arrêt forcé' de la liste latérale, puis réessayez\nde restaurer l'instantané avec la VM éteinte.",

"La VM es un clon enlazado (backing file QCOW2) y el snapshot '{0}' fue creado en modo COMPLETO (RAM + dispositivos).\n\nQEMU no puede restaurar snapshots completos sobre un QCOW2 con backing file: al ejecutar loadvm aborta con una aserción interna (vmstate_load_next) y el proceso muere. De ahí el 'Conexión reinicializada' que has visto.\n\nQué hacer:\n  • Los snapshots que crees A PARTIR DE AHORA en este clon serán solo de discos (la app ya lo fuerza) y se podrán restaurar.\n  • Este snapshot antiguo no se puede restaurar. Elimínalo si ya no lo necesitas.\n  • Si necesitas snapshots completos, desenlaza el clon con '🧬 Desenlazar' (convierte el delta en un QCOW2 autónomo).":
    "La VM est un clone lié (backing file QCOW2) et l'instantané '{0}' a été créé en mode COMPLET (RAM + périphériques).\n\nQEMU ne peut pas restaurer des instantanés complets sur un QCOW2 avec backing file : lors du loadvm, il abandonne avec une assertion interne (vmstate_load_next) et le processus meurt. D'où la 'Connexion réinitialisée' que vous avez vue.\n\nQue faire :\n  • Les instantanés que vous créerez À PARTIR DE MAINTENANT sur ce clone seront disque uniquement (l'application le force déjà) et pourront être restaurés.\n  • Cet ancien instantané ne peut pas être restauré. Supprimez-le si vous n'en avez plus besoin.\n  • Si vous avez besoin d'instantanés complets, détachez le clone avec '🧬 Détacher' (convertit le delta en un QCOW2 autonome).",

"Existe una captura para '{0}', pero ese snapshot ya no aparece en la lista de la VM (puede haber sido eliminado). Actualiza la pestaña Snapshots o elimínalo manualmente.":
    "Une capture existe pour '{0}', mais cet instantané n'apparaît plus dans la liste de la VM (il a peut-être été supprimé). Actualisez l'onglet Instantanés ou supprimez-le manuellement.",

"Padre para '{0}':":
    "Parent pour '{0}' :",

"Nombre del snapshot (hijo de '{0}'):":
    "Nom de l'instantané (enfant de '{0}') :",

"Esta VM está configurada con gráficos '{0}', que no permiten\nRESTAURAR snapshots completos en QEMU (RAM + dispositivos).\n\nEl snapshot se puede crear, pero al intentar restaurarlo QEMU\nfallará con: 'Failed to load element of type virtio for virtio'.\n\nOpciones:\n  • Usar snapshot SOLO DE DISCOS (elegir 'No' en el siguiente\n    diálogo). No guarda RAM ni estado de ventanas, pero se\n    restaura sin problema con la VM apagada.\n  • Cambiar Gráficos/GPU a 'Red Hat QXL 2D' o 'VMware SVGA II',\n    reiniciar la VM y crear snapshots completos.\n\n¿Crear el snapshot igualmente?":
    "Cette VM est configurée avec des graphiques '{0}', qui ne permettent pas\nde RESTAURER des instantanés complets dans QEMU (RAM + périphériques).\n\nL'instantané peut être créé, mais lors de la restauration QEMU\néchouera avec : 'Failed to load element of type virtio for virtio'.\n\nOptions :\n  • Utiliser un instantané DISQUE UNIQUEMENT (choisir 'Non' dans le\n    dialogue suivant). Il n'enregistre ni la RAM ni l'état des fenêtres, mais\n    se restaure sans problème avec la VM éteinte.\n  • Changer Graphiques/GPU vers 'Red Hat QXL 2D' ou 'VMware SVGA II',\n    redémarrer la VM et créer des instantanés complets.\n\nCréer l'instantané quand même ?",

"Se creó '{0}' en {1} QCOW2.\n\nEste snapshot no contiene la memoria RAM ni el estado de las ventanas. Para restaurarlo, la VM debe estar apagada.":
    "'{0}' a été créé sur {1} QCOW2.\n\nCet instantané ne contient ni la mémoire RAM ni l'état des fenêtres. Pour le restaurer, la VM doit être éteinte.",

"Estado '{0}' guardado y VM pausada.":
    "État '{0}' enregistré et VM en pause.",

"Snapshot '{0}' eliminado.":
    "Instantané '{0}' supprimé.",

"Snapshot '{0}' restaurado.":
    "Instantané '{0}' restauré.",

"Snapshot '{0}' creado.":
    "Instantané '{0}' créé.",

"El snapshot '{0}' fue creado y confirmado por QEMU.":
    "L'instantané '{0}' a été créé et confirmé par QEMU.",

"Estado guardado como '{0}'.\n\nLa VM quedó pausada. Puedes reanudarla con el botón Pausar/Reanudar.":
    "État enregistré sous '{0}'.\n\nLa VM a été mise en pause. Vous pouvez la reprendre avec le bouton Pause/Reprendre.",

"Se eliminó '{0}'.":
    "'{0}' a été supprimé.",

"Se restauró '{0}'.":
    "'{0}' a été restauré.",

"No se pudo completar la operación de snapshot '{0}'.\n\n{1}":
    "L'opération d'instantané '{0}' n'a pas pu être terminée.\n\n{1}",

"¿Restaurar '{0}'?\n\nLa VM volverá al estado del snapshot.":
    "Restaurer '{0}' ?\n\nLa VM reviendra à l'état de l'instantané.",

"El snapshot '{0}' es solo de discos (no contiene RAM).\n\nPara restaurarlo hay que apagar la VM primero.\nLa VM volverá al estado del snapshot.\n\n¿Apagar la VM ahora y restaurar el snapshot?":
    "L'instantané '{0}' est disque uniquement (il ne contient pas la RAM).\n\nPour le restaurer, il faut d'abord éteindre la VM.\nLa VM reviendra à l'état de l'instantané.\n\nÉteindre la VM maintenant et restaurer l'instantané ?",

"Se restauró '{0}' mediante snapshot-load.":
    "'{0}' a été restauré via snapshot-load.",

"El snapshot '{0}' es solo de discos (no contiene RAM).\n\nPara restaurarlo hay que apagar la VM y volver a intentarlo. QEMU no puede restaurar snapshots sin vmstate con la VM encendida.":
    "L'instantané '{0}' est disque uniquement (il ne contient pas la RAM).\n\nPour le restaurer, il faut éteindre la VM et réessayer. QEMU ne peut pas restaurer des instantanés sans vmstate avec la VM allumée.",

"La VM volvió a un estado operativo después de restaurar '{0}'.\n\nQEMU no confirmó el fin del job dentro del tiempo de espera, pero la restauración se aplicó.":
    "La VM est revenue à un état opérationnel après avoir restauré '{0}'.\n\nQEMU n'a pas confirmé la fin du job dans le délai, mais la restauration a été appliquée.",

"QEMU no puede restaurar el snapshot por un problema conocido con el dispositivo VirtIO-GPU.\n\nDetalle técnico:\n  VirtIO-GPU guarda un estado interno que no es serializable de forma fiable. QEMU intenta reconstruirlo al restaurar y falla. No es un bug de la app, es una limitación del motor.\n\nCómo resolverlo:\n  1. Abre Configuración → Pantalla.\n  2. Cambia 'Gráficos / GPU' de '{0}' a 'Red Hat QXL 2D'.\n  3. Reinicia la VM (apágala y vuelve a arrancarla).\n  4. Crea snapshots nuevos a partir de ese momento: se podrán restaurar sin problemas.\n\nLos snapshots antiguos creados con virtio-gpu no se pueden recuperar (QEMU no puede reconstruir su estado). Si ya no los necesitas, elimínalos.":
    "QEMU ne peut pas restaurer l'instantané en raison d'un problème connu avec le périphérique VirtIO-GPU.\n\nDétail technique :\n  VirtIO-GPU stocke un état interne qui n'est pas sérialisable de manière fiable. QEMU tente de le reconstruire lors de la restauration et échoue. Ce n'est pas un bug de l'application, c'est une limitation du moteur.\n\nComment résoudre :\n  1. Ouvrez Configuration → Affichage.\n  2. Changez 'Graphiques / GPU' de '{0}' vers 'Red Hat QXL 2D'.\n  3. Redémarrez la VM (éteignez-la et redémarrez-la).\n  4. Créez de nouveaux instantanés à partir de ce moment : ils pourront être restaurés sans problème.\n\nLes anciens instantanés créés avec virtio-gpu ne peuvent pas être récupérés (QEMU ne peut pas reconstruire leur état). Si vous n'en avez plus besoin, supprimez-les.",

"¿Eliminar '{0}'?":
    "Supprimer '{0}' ?",

"Nuevo nombre para '{0}':":
    "Nouveau nom pour '{0}' :",

# ---- 67-78: mensajes del panel derecho y plantillas -----
"No hay una máquina virtual seleccionada.\n\nPulsa 'Nueva máquina virtual' para comenzar.":
    "Aucune machine virtuelle sélectionnée.\n\nAppuyez sur 'Nouvelle machine virtuelle' pour commencer.",

"Configura el sistema en la pestaña 'Configuración'.":
    "Configurez le système dans l'onglet 'Configuration'.",

"Usa 'Configuración' para modificar hardware y opciones avanzadas.":
    "Utilisez 'Configuration' pour modifier le matériel et les options avancées.",

"Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio.":
    "Configurez la VM dans l'onglet 'Configuration' et appuyez sur le bouton de démarrage.",

"Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\ncompleta en una ventana propia. NO afecta al visor externo:\npara ese, usa el checkbox 'Externos en pantalla completa'\nde la fila de estado.\n\nPulsa {0} para salir.":
    "Affiche la visionneuse INTÉGRÉE (VNC dans l'application) en plein\nécran dans sa propre fenêtre. N'affecte PAS la visionneuse externe :\npour celle-ci, utilisez la case 'Visionneuses externes en plein écran'\nde la ligne d'état.\n\nAppuyez sur {0} pour quitter.",

"Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?":
    "Le modèle '{0}' existe déjà.\n\nL'écraser ?",

"Plantilla '{0}' creada correctamente.\n\nAparecerá en el menú del botón '➕ Nueva VM'.":
    "Modèle '{0}' créé correctement.\n\nIl apparaîtra dans le menu du bouton '➕ Nouvelle VM'.",

"No encuentro la plantilla '{0}'.":
    "Modèle '{0}' introuvable.",

"Ya existe una carpeta para '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
    "Un dossier pour '{0}' existe déjà.\n\nLe remplacer ? (l'actuel sera supprimé)",

"VM '{0}' creada desde la plantilla '{1}'.\n\nSe ha abierto en Configuración → Almacenamiento para que\nañadas el disco y el medio de instalación. La MAC de red se\nha regenerado para evitar conflictos con otras VMs.":
    "VM '{0}' créée depuis le modèle '{1}'.\n\nElle a été ouverte dans Configuration → Stockage pour que\nvous ajoutiez le disque et le support d'installation. La MAC réseau a\nété régénérée pour éviter les conflits avec d'autres VM.",

# i18n_fr_fix1_v1
}
