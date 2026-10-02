# -*- coding: utf-8 -*-
"""Frances — Tanda 3: cierre. Cubre los pendientes de la tanda 2."""

TRANSLATIONS = {

    # ================================================================
    # Snapshots: dialogo organigrama
    # ================================================================
    "{0}, {1} (+{2})": "{0}, {1} (+{2})",
    "Archivo no disponible": "Fichier non disponible",
    "(sin miniatura)": "(sans miniature)",
    "Restaurar este snapshot": "Restaurer cet instantané",
    "Renombrar": "Renommer",
    "✏ Renombrar": "✏ Renommer",
    "➕ Crear snapshot hijo": "➕ Créer un instantané enfant",
    "🔗 Establecer padre…": "🔗 Définir le parent…",
    "⬆ Mover a la raíz": "⬆ Déplacer à la racine",

    # ================================================================
    # Consola backend: descripciones de cada modo
    # ================================================================
    "QEMU abre su propia ventana (GTK/SDL). No hace falta visor externo ni cliente; a cambio, la VM no aparece dentro de la app.":
        "QEMU ouvre sa propre fenêtre (GTK/SDL). Aucune visionneuse ni client externe n'est nécessaire ; en échange, la VM n'apparaît pas dans l'application.",
    "Híbrida: VNC se muestra dentro de la app (funciona en Wayland y X11) y SPICE se abre en una ventana externa con spicy o remote-viewer. Lo mejor de ambos: embebido para tenerlo a mano, SPICE para rendimiento y clipboard avanzado.":
        "Hybride : VNC est affiché dans l'application (fonctionne sous Wayland et X11) et SPICE s'ouvre dans une fenêtre externe avec spicy ou remote-viewer. Le meilleur des deux : intégré pour l'avoir à portée de main, SPICE pour la performance et le presse-papiers avancé.",
    "VNC embebido en la app. Sin dependencias adicionales.":
        "VNC intégré dans l'application. Aucune dépendance supplémentaire.",
    "VNC en ventana externa. Necesitas vncviewer (tigervnc), gvncviewer o remmina instalado.":
        "VNC en fenêtre externe. Vous avez besoin de vncviewer (tigervnc), gvncviewer ou remmina installé.",
    "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). Requiere sesión X11; en Wayland cae a visor externo.":
        "SPICE intégré dans l'application (Gtk.SpiceDisplay via XEmbed). Nécessite une session X11 ; sous Wayland, retombe sur la visionneuse externe.",
    "SPICE embebido solicitado, pero spice-gtk no tiene binding Python. Se usará visor externo como respaldo. Instala python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).":
        "Intégration SPICE demandée, mais spice-gtk n'a pas de binding Python. Une visionneuse externe sera utilisée en secours. Installez python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) ou python-gobject + spice-gtk (Arch).",
    "SPICE en ventana externa. Necesitas spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "SPICE en fenêtre externe. Vous avez besoin de spicy (spice-gtk) ou remote-viewer (virt-viewer).",
    "🖼 Mostrar la VM dentro de la app (consola VNC embebida)":
        "🖼 Afficher la VM dans l'application (console VNC intégrée)",

    # ================================================================
    # Panel izquierdo + toolbar: tooltips largos
    # ================================================================
    "Como ordenar la lista de maquinas virtuales.\n  - Nombre: alfabetico.\n  - Estado: encendidas primero, luego pausadas, apagadas al final.\n  - Ultima vez usada: por fecha de modificacion del vm_config.ini\n    (aproxima cuando se configuro por ultima vez).":
        "Comment trier la liste des machines virtuelles.\n  - Nom : alphabétique.\n  - État : allumées d'abord, puis en pause, éteintes à la fin.\n  - Dernière utilisation : par date de modification du vm_config.ini\n    (approximation de la dernière configuration).",
    "Pausar la VM. Usa la flecha para más opciones:\n• Pausar (rápido): detiene sin guardar el estado en disco.\n• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n• Reanudar: vuelve a ejecutar la VM pausada.":
        "Mettre la VM en pause. Utilisez la flèche pour plus d'options :\n• Pause (rapide) : arrête sans enregistrer l'état sur disque.\n• Enregistrer l'état et mettre en pause : écrit la RAM sur disque avant la pause.\n• Reprendre : relance la VM en pause.",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.":
        "Arrêt (ACPI) : demande à la VM de s'éteindre proprement.",
    "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\nencendido en un equipo real. El sistema operativo invitado decide cuándo\ny cómo cerrar. Puede tardar unos segundos o no responder si está colgado.":
        "Demande à la VM de s'éteindre proprement, comme appuyer sur le bouton\nd'alimentation d'une machine réelle. Le système d'exploitation invité décide quand\net comment fermer. Cela peut prendre quelques secondes ou ne pas répondre si elle est bloquée.",
    "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\ncomo desenchufar un equipo real. Puede causar pérdida de datos no\nguardados; úsalo solo si la VM no responde al apagado normal.":
        "Coupe la VM immédiatement, sans prévenir le système d'exploitation invité —\ncomme débrancher une machine réelle. Peut causer une perte de données non\nenregistrées ; à utiliser seulement si la VM ne répond pas à l'arrêt normal.",
    "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\nNo es un apagado ordenado del sistema operativo invitado: simplemente\nreinicia el hardware virtual.":
        "Redémarre la VM (équivalent au bouton reset d'une machine réelle).\nCe n'est pas un arrêt propre du système invité : cela réinitialise simplement\nle matériel virtuel.",
    "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\nal sistema operativo invitado. Úsalo solo si la VM no responde ni al\napagado ni al reinicio normales.":
        "Coupe complètement la VM et la redémarre à zéro, sans prévenir\nle système d'exploitation invité. À utiliser seulement si la VM ne répond ni à\nl'arrêt ni au redémarrage normaux.",
    "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\nel estado (RAM y dispositivos) se pierde si el host se reinicia.":
        "Met la VM en pause sans enregistrer l'état sur disque. Instantané, mais\nl'état (RAM et périphériques) est perdu si l'hôte redémarre.",
    "Reanuda la ejecución de la VM pausada.":
        "Reprend l'exécution de la VM en pause.",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\nUsa la flecha para más opciones (forzar, reiniciar).":
        "Arrêt (ACPI) : demande à la VM de s'éteindre proprement.\nUtilisez la flèche pour plus d'options (forcer, redémarrer).",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\nCambia ISO en caliente, expulsa medios y conecta/desconecta\nUSB sin reiniciar la máquina. Atajo: Ctrl+M.":
        "Médias de la VM : lecteurs CD/DVD et périphériques USB.\nChanger l'ISO à chaud, éjecter les médias et connecter/déconnecter\nUSB sans redémarrer la machine. Raccourci : Ctrl+M.",
    "Convierte este clon enlazado en un QCOW2 autónomo.\nDespués, el clon deja de depender del original y puede\nmoverse o copiarse por separado.\n\nSolo aparece cuando la VM seleccionada es un clon\nenlazado y está apagada.":
        "Convertit ce clone lié en un QCOW2 autonome.\nEnsuite, le clone ne dépend plus de l'original et peut\nêtre déplacé ou copié séparément.\n\nN'apparaît que lorsque la VM sélectionnée est un clone\nlié et est éteinte.",
    "Importar una VM desde una carpeta (con vm_config.ini) o desde\nun archivo .tar.gz / .zip exportado previamente.":
        "Importer une VM depuis un dossier (avec vm_config.ini) ou depuis\nun fichier .tar.gz / .zip précédemment exporté.",
    "Exportar esta VM como carpeta, .tar.gz o .zip portable.\nSe omiten los archivos de runtime (pids, sockets, logs).":
        "Exporter cette VM comme dossier, .tar.gz ou .zip portable.\nLes fichiers d'exécution (pids, sockets, journaux) sont ignorés.",
    "Muestra el contenido de run_temp.sh: el comando exacto con\nel que QEMU está ejecutando (o ejecutó por última vez) esta\nVM. Solo está disponible si la VM se ha arrancado alguna vez.":
        "Affiche le contenu de run_temp.sh : la commande exacte avec\nlaquelle QEMU exécute (ou a exécuté pour la dernière fois) cette\nVM. Disponible uniquement si la VM a été démarrée au moins une fois.",
    "Notas libres sobre esta VM. Se guardan en vm_config.ini\n(extra.notes) y aparecen como aviso amarillo debajo del\nestado en esta misma pestaña.":
        "Notes libres sur cette VM. Enregistrées dans vm_config.ini\n(extra.notes) et affichées comme avertissement jaune sous\nl'état dans ce même onglet.",
    "Grupo y color de esta VM. El grupo agrupa VMs en la lista\nlateral; el color se aplica como fondo del ítem.":
        "Groupe et couleur de cette VM. Le groupe regroupe les VM dans la liste\nlatérale ; la couleur est appliquée comme arrière-plan de l'élément.",
    "Compara la configuración actual de esta VM con los\nvalores por defecto del perfil del SO. Permite aplicar\nlos defaults a un campo o a todos; los cambios se aplican\na los widgets y se persisten al Guardar.":
        "Compare la configuration actuelle de cette VM avec les\nvaleurs par défaut du profil de l'OS. Permet d'appliquer\nles valeurs par défaut à un champ ou à tous ; les modifications sont appliquées\naux widgets et persistent lors de l'enregistrement.",

    # ================================================================
    # Snapshots: cabecera de pestaña + avisos largos
    # ================================================================
    "<b>Snapshots de la máquina virtual</b>":
        "<b>Instantanés de la machine virtuelle</b>",
    "Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.":
        "Crée, restaure, supprime et gère les instantanés. L'application vérifie les disques QCOW2 inscriptibles, l'espace libre et quels disques feront partie de l'instantané avant de l'exécuter.",
    "⚠ Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con ‘🧬 Desenlazar’ en la pestaña Resumen.":
        "⚠ Cette VM est un clone lié (backing file QCOW2). Les instantanés complets (RAM + périphériques) ne peuvent pas être restaurés dans QEMU avec un backing file ; l'application utilisera toujours des instantanés DISQUE UNIQUEMENT. Pour avoir des instantanés complets, détachez d'abord le clone avec ‘🧬 Détacher’ dans l'onglet Aperçu.",
    "Alejar la miniatura": "Réduire la miniature",
    "Acercar la miniatura": "Agrandir la miniature",
    "↺ Ajustar": "↺ Ajuster",
    "Ajustar al tamaño original": "Ajuster à la taille d'origine",
    "Auto-scroll": "Défilement automatique",
    "<h2>Ayuda de Virtual.Machine</h2>": "<h2>Aide de Virtual.Machine</h2>",
    "Guia completa de la consola (VNC / SPICE)": "Guide complet de la console (VNC / SPICE)",
    "Idioma de la interfaz.": "Langue de l'interface.",

    # ================================================================
    # API REST
    # ================================================================
    "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar VMs desde scripts, dashboards o CI. Todo se autentica con un token local; <b>no</b> es accesible desde la red.":
        "Expose une API HTTP minimale sur <b>127.0.0.1</b> pour contrôler les VM depuis des scripts, tableaux de bord ou CI. Tout est authentifié avec un jeton local ; <b>pas</b> accessible depuis le réseau.",
    "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\nCambios requieren apagar y volver a encender la API.":
        "Port TCP sur lequel le serveur écoute. Uniquement 127.0.0.1.\nLes changements nécessitent d'arrêter puis de redémarrer l'API.",
    "Mostrar / ocultar el token": "Afficher / masquer le jeton",
    "Genera un token nuevo. Las peticiones con el token anterior\ndejarán de funcionar.":
        "Génère un nouveau jeton. Les requêtes avec l'ancien jeton\ncesseront de fonctionner.",
    "Ver peticiones recientes": "Voir les requêtes récentes",
    "API REST": "API REST",
    "No se pudo arrancar la API REST.\n\n{0}":
        "Impossible de démarrer l'API REST.\n\n{0}",
    "Regenerar token": "Régénérer le jeton",
    "Se generará un token nuevo y el anterior dejará de funcionar.\n\n¿Continuar?":
        "Un nouveau jeton sera généré et l'ancien cessera de fonctionner.\n\nContinuer ?",
    "Se regeneró el token pero no se pudo reiniciar la API:\n\n{0}":
        "Le jeton a été régénéré mais l'API n'a pas pu être redémarrée :\n\n{0}",
    "Peticiones recientes a la API": "Requêtes récentes à l'API",
    "Últimas peticiones atendidas por la API. Se conservan las 50 más recientes.":
        "Dernières requêtes servies par l'API. Les 50 plus récentes sont conservées.",
    "(sin peticiones todavía)": "(aucune requête pour le moment)",

    # ================================================================
    # Apariencia + tema + presentacion
    # ================================================================
    "Tema visual de la aplicacion.\n  - Sistema: usa el estilo y la paleta del escritorio.\n  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n    propia, independiente del SO.\n\nAl elegir Claro u Oscuro, la app cambia el estilo de Qt a\nFusion. Al volver a Sistema, se restaura el estilo original\ndel escritorio (Breeze, Adwaita, etc.).":
        "Thème visuel de l'application.\n  - Système : utilise le style et la palette du bureau.\n  - Clair / Sombre : force le style Fusion avec sa propre\n    palette, indépendante de l'OS.\n\nEn choisissant Clair ou Sombre, l'application bascule le style Qt sur\nFusion. En revenant à Système, le style d'origine du bureau\nest restauré (Breeze, Adwaita, etc.).",
    "Se ha cambiado el tema.\n\nAlgunos estilos del escritorio (Kvantum en KDE, por\nejemplo) pueden no repintar todos los widgets hasta\nreiniciar la aplicacion.\n\n¿Quieres reiniciar ahora para asegurar que todos los\nelementos se vean correctamente?":
        "Le thème a été changé.\n\nCertains styles du bureau (Kvantum sous KDE, par\nexemple) peuvent ne pas repeindre tous les widgets avant\nun redémarrage de l'application.\n\nVoulez-vous redémarrer maintenant pour vous assurer que tous les\néléments s'affichent correctement ?",
    "No hay ninguna máquina virtual seleccionada.":
        "Aucune machine virtuelle n'est sélectionnée.",
    "La Consola Gráfica no está disponible en este sistema (falta el widget VNC embebido).":
        "La Console graphique n'est pas disponible sur ce système (le widget VNC intégré est manquant).",
    "Salir del modo presentación y restaurar la vista normal.\nTambién puedes pulsar F11 o Escape.":
        "Quitter le mode présentation et restaurer la vue normale.\nVous pouvez aussi appuyer sur F11 ou Échap.",

    # ================================================================
    # Backup schedule: bloque completo
    # ================================================================
    "Cuando esta activo, la app copia la carpeta completa de la VM (discos, configuracion, snapshots) al destino elegido segun la frecuencia. Los backups son carpetas independientes; puedes borrarlos manualmente o dejar que la retencion los limpie.":
        "Lorsqu'activé, l'application copie le dossier complet de la VM (disques, configuration, instantanés) vers la destination choisie selon la fréquence. Les sauvegardes sont des dossiers indépendants ; vous pouvez les supprimer manuellement ou laisser la rétention les nettoyer.",
    "Carpeta del host donde guardar los backups":
        "Dossier de l'hôte où enregistrer les sauvegardes",
    "Cuantos backups conservar en el destino. Tras cada backup exitoso se borran los mas antiguos por encima de este numero.":
        "Combien de sauvegardes conserver à la destination. Après chaque sauvegarde réussie, les plus anciennes au-delà de ce nombre sont supprimées.",
    "Tambien cuando la VM esta encendida": "Aussi quand la VM est allumée",
    "Desactivado (recomendado): los backups solo se ejecutan con la VM apagada.\n\nActivado: si la VM esta encendida, se copian los discos de todos modos; la copia puede quedar inconsistente porque QEMU esta escribiendo en el .qcow2 en ese momento. La restauracion podria requerir fsck o no arrancar. Solo si estas dispuesto a asumir ese riesgo.":
        "Désactivé (recommandé) : les sauvegardes ne s'exécutent qu'avec la VM éteinte.\n\nActivé : si la VM est allumée, les disques sont copiés de\ntoutes façons ; la copie peut devenir incohérente car QEMU écrit\ndans le .qcow2 à ce moment-là. La restauration pourrait nécessiter fsck ou ne pas démarrer. Seulement si vous êtes prêt à assumer ce risque.",
    "Los backups son <b>carpetas</b> con todos los archivos de la VM (discos + configuración + snapshots + capturas). No incluyen pids, sockets ni logs. Para restaurar, usa el botón <b>Importar</b> de la pestaña Resumen con la carpeta del backup.":
        "Les sauvegardes sont des <b>dossiers</b> contenant tous les fichiers de la VM (disques + configuration + instantanés + captures). Elles n'incluent ni pids, ni sockets, ni journaux. Pour restaurer, utilisez le bouton <b>Importer</b> de l'onglet Aperçu avec le dossier de sauvegarde.",
    "Ejecuta un backup inmediato con la configuracion actual, sin esperar a la proxima programacion.":
        "Exécute une sauvegarde immédiate avec la configuration actuelle, sans attendre la prochaine planification.",
    "Elegir carpeta de destino para backups":
        "Choisir le dossier de destination pour les sauvegardes",
    "Selecciona una VM para programar backups.":
        "Sélectionnez une VM pour programmer les sauvegardes.",
    "Desactivado para esta VM.": "Désactivé pour cette VM.",
    "Falta elegir una carpeta de destino.":
        "Un dossier de destination doit être choisi.",
    "Sin backups todavia. Libre en destino: {0}. Se creara el primero tras cumplirse la frecuencia.":
        "Aucune sauvegarde pour le moment. Libre à la destination : {0}. La première sera créée une fois la fréquence écoulée.",
    "Pendiente (ultimo: {0}). Libre: {1}.":
        "En attente (dernière : {0}). Libre : {1}.",
    "Ultimo: {0} · Proximo en ~{1} min · Libre: {2}.":
        "Dernière : {0} · Prochaine dans ~{1} min · Libre : {2}.",
    "Ultimo: {0} · Libre: {1}.":
        "Dernière : {0} · Libre : {1}.",
    "Configura primero una carpeta de destino.":
        "Configurez d'abord un dossier de destination.",
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "Impossible de créer le dossier de destination :\n{0}\n\n{1}",
    "Espacio insuficiente en el destino. Necesario ~{0}, libre {1}.":
        "Espace insuffisant à la destination. Nécessaire ~{0}, libre {1}.",
    "Configura primero una carpeta de destino en esta seccion.":
        "Configurez d'abord un dossier de destination dans cette section.",
    "Backup con la VM encendida": "Sauvegarde avec la VM allumée",

    # ================================================================
    # Compare defaults
    # ================================================================
    "No se pudo determinar el perfil del SO seleccionado.":
        "Le profil de l'OS sélectionné n'a pas pu être déterminé.",
    "Señalización (ratón/teclado)": "Pointage (souris/clavier)",
    "Consola: protocolo": "Console : protocole",
    "Consola: modo": "Console : mode",
    "Comparación de <b>{0}</b> con los valores por defecto del perfil del SO seleccionado. Las filas con fondo amarillo difieren del default.<br><br>Aplicar un default <b>no</b> guarda la VM: solo cambia el widget. Persiste con <b>Guardar</b> (en Configuración) o al iniciar la VM.":
        "Comparaison de <b>{0}</b> avec les valeurs par défaut du profil de l'OS sélectionné. Les lignes avec fond jaune diffèrent de la valeur par défaut.<br><br>Appliquer une valeur par défaut <b>n'</b>enregistre <b>pas</b> la VM : cela modifie seulement le widget. Persistez avec <b>Enregistrer</b> (dans Configuration) ou au démarrage de la VM.",
    "<b>{0}</b> diferencia(s) de <b>{1}</b> campo(s).":
        "<b>{0}</b> différence(s) sur <b>{1}</b> champ(s).",
    "Selecciona primero una fila.": "Sélectionnez d'abord une ligne.",

    # ================================================================
    # Consola: avisos de sesion X11/Wayland
    # ================================================================
    "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden embeber dentro de la app.":
        "<b>Session actuelle : X11.</b> VNC et SPICE peuvent être intégrés dans l'application.",
    "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber dentro de la app. SPICE embebido requeriría X11 (XEmbed no existe en Wayland); si eliges SPICE con modo embebido, caerá automáticamente a visor externo.":
        "<b>Session actuelle : Wayland.</b> Seul VNC peut être intégré dans l'application. SPICE intégré nécessiterait X11 (XEmbed n'existe pas sous Wayland) ; si vous choisissez SPICE avec mode intégré, il basculera automatiquement vers la visionneuse externe.",
    "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE funcionará cuando estés en X11.":
        "<b>spice-gtk avec binding Python : oui.</b> L'intégration SPICE fonctionnera lorsque vous serez sous X11.",
    "<b>spice-gtk con binding Python: no.</b> Aunque estés en X11, SPICE no podrá incrustarse; siempre caerá a visor externo. Instálalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>":
        "<b>spice-gtk avec binding Python : non.</b> Même sous X11, SPICE ne pourra pas être intégré ; il basculera toujours vers la visionneuse externe. Installez-le avec :<br>&nbsp;&nbsp;<code>Debian/Ubuntu : python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch : python-gobject spice-gtk</code>",
    "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su propia ventana y no expone VNC/SPICE; es el único modo compatible con esos gráficos 3D.":
        "<b>Graphiques compatibles avec VNC / SPICE / Hybride :</b> <b>Automatique</b>, <b>VirtIO-GPU 2D</b> ou <b>QXL</b>.<br>Avec <b>VirGL</b> ou <b>Venus</b> sélectionnés, QEMU ouvre sa propre fenêtre et n'expose pas VNC/SPICE ; c'est le seul mode compatible avec ces graphiques 3D.",
    "Consola externa": "Console externe",
    "No se encontró ningún visor {0} instalado.\n\n":
        "Aucune visionneuse {0} installée trouvée.\n\n",
    "Instala gvncviewer o tigervnc (vncviewer).":
        "Installez gvncviewer ou tigervnc (vncviewer).",
    "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "Installez spicy (spice-gtk) ou remote-viewer (virt-viewer).",
    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\nLa VM debe estar corriendo para que QEMU haya elegido un\npuerto.":
        "Je ne peux pas encore déterminer le port SPICE de cette VM.\n\nLa VM doit être en cours d'exécution pour que QEMU ait choisi un\nport.",
    "El socket {0} todavía no existe.\n\nLa VM debe estar corriendo con ese protocolo seleccionado.":
        "Le socket {0} n'existe pas encore.\n\nLa VM doit être en cours d'exécution avec ce protocole sélectionné.",

    # ================================================================
    # Diagnostics
    # ================================================================
    "Todavía no hay historial guardado para esta VM.":
        "Il n'y a pas encore d'historique enregistré pour cette VM.",
    "No se pudo leer el log: {0}": "Impossible de lire le journal : {0}",
    "Log completo — {0}": "Journal complet — {0}",
    "Log exportado a:\n{0}": "Journal exporté vers :\n{0}",
    "No se pudo exportar el log: {0}":
        "Impossible d'exporter le journal : {0}",
    "VM: {0}": "VM : {0}",
    "Carpeta: {0}": "Dossier : {0}",
    "● QEMU: detenido.": "● QEMU : arrêté.",
    "● QEMU: {0}{1}.": "● QEMU : {0}{1}.",
    "● Guest Agent: no aplica (VM apagada).":
        "● Guest Agent : non applicable (VM éteinte).",
    "● Guest Agent: responde (v{0}).":
        "● Guest Agent : répond (v{0}).",
    "● Guest Agent: sin respuesta ({0}). Verifica que qemu-guest-agent esté instalado y corriendo en el guest.":
        "● Guest Agent : pas de réponse ({0}). Vérifiez que qemu-guest-agent est installé et en cours d'exécution dans l'invité.",
    "● Carpetas compartidas (VirtioFS): ninguna configurada.":
        "● Dossiers partagés (VirtioFS) : aucun configuré.",
    "● Carpetas compartidas (VirtioFS):":
        "● Dossiers partagés (VirtioFS) :",
    "    - {0}: no aplica (VM apagada).":
        "    - {0} : non applicable (VM éteinte).",
    "    - {0}: virtiofsd activo (PID {1}).":
        "    - {0} : virtiofsd actif (PID {1}).",
    "    - {0}: NO está activo. Revisa {1} si esperabas que funcionara.":
        "    - {0} : N'est PAS actif. Vérifiez {1} si vous vous attendiez à ce qu'il fonctionne.",
    "No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores.":
        "Aucun processus QEMU/virtiofsd suspendu de sessions précédentes trouvé.",
    "  - {0} (PID {1})": "  - {0} (PID {1})",
    "Procesos virtiofsd huérfanos encontrados:":
        "Processus virtiofsd orphelins trouvés :",
    "  - {0}: virtiofsd PID {1}": "  - {0} : virtiofsd PID {1}",
    "Se detuvieron {0} proceso(s) huérfano(s).":
        "{0} processus orphelin(s) arrêté(s).",
    "\n\nNo se pudieron detener:\n":
        "\n\nN'ont pas pu être arrêtés :\n",
    "FALTA": "MANQUANT",
    " ({0})": " ({0})",
    "firmware disponible": "firmware disponible",
    "sin plantilla Secure Boot": "pas de modèle Secure Boot",
    "módulos": "modules",
    "módulo no cargado": "module non chargé",
    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Audio {5} | GPU {6}":
        "Virtualisation : {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Audio {5} | GPU {6}",
    "sí": "oui",
    "no": "non",
    "Distribución: {0}\nGestor de paquetes: {1}\nSecure Boot: {2}\nVirtIO: {3}\nAudio: {4}\nGPU: {5}\nOpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}":
        "Distribution : {0}\nGestionnaire de paquets : {1}\nSecure Boot : {2}\nVirtIO : {3}\nAudio : {4}\nGPU : {5}\nOpenGL : {6} | Vulkan : {7} | VirGL : {8} | VFIO : {9}",
    "La comprobación/reparación terminó correctamente.":
        "La vérification/réparation s'est terminée correctement.",
    "No se pudieron reparar todas las dependencias.\n\n{0}":
        "Toutes les dépendances n'ont pas pu être réparées.\n\n{0}",
    "desconocida": "inconnue",

    # ================================================================
    # Health dashboard
    # ================================================================
    "Cada fila muestra el estado de un subsistema de la VM. Verde: funciona · Amarillo: parcial o sin confirmar · Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s.":
        "Chaque ligne affiche l'état d'un sous-système de la VM. Vert : fonctionne · Jaune : partiel ou non confirmé · Rouge : indisponible · Gris : non applicable. Rafraîchissement toutes les 4 s.",
    "Salida parcial: uno de los dos destinos no respondió.":
        "Connectivité partielle : l'une des deux destinations n'a pas répondu.",
    "No hay script de arranque todavía.":
        "Pas encore de script de démarrage.",
    "No se pudo leer el script de arranque.":
        "Le script de démarrage n'a pas pu être lu.",
    "No hay adaptador de red configurado en esta VM.":
        "Aucun adaptateur réseau configuré sur cette VM.",
    "NIC {0}: tráfico activo ({1:.1f} KB/s; rx {2:.1f} MB, tx {3:.1f} MB).":
        "NIC {0} : trafic actif ({1:.1f} Ko/s ; rx {2:.1f} Mo, tx {3:.1f} Mo).",
    "NIC {0} con contadores activos pero sin tráfico en el último intervalo (rx {1:.1f} MB, tx {2:.1f} MB).":
        "NIC {0} avec compteurs actifs mais sans trafic dans le dernier intervalle (rx {1:.1f} Mo, tx {2:.1f} Mo).",
    "NIC {0}: contadores iniciales leídos (rx {1:.1f} MB, tx {2:.1f} MB); esperando siguiente lectura para medir velocidad.":
        "NIC {0} : compteurs initiaux lus (rx {1:.1f} Mo, tx {2:.1f} Mo) ; en attente de la prochaine lecture pour mesurer la vitesse.",
    "NIC {0} configurada. {1} conexiones TCP activas en el host; esperando segunda lectura para medir cambio.":
        "NIC {0} configurée. {1} connexions TCP actives sur l'hôte ; en attente d'une deuxième lecture pour mesurer le changement.",
    "NIC {0}: actividad detectada ({1} → {2} conexiones TCP ESTAB).":
        "NIC {0} : activité détectée ({1} → {2} connexions TCP ESTAB).",
    "NIC {0} configurada. {1} conexiones TCP activas en el host, sin cambios en el último intervalo (la VM puede estar idle).":
        "NIC {0} configurée. {1} connexions TCP actives sur l'hôte, aucun changement dans le dernier intervalle (la VM peut être inactive).",
    "NIC {0} configurada; sin conexiones externas activas en el host.":
        "NIC {0} configurée ; aucune connexion externe active sur l'hôte.",
    "NIC {0} configurada. No se pudo medir tráfico (QMP no expone query-netdev y ss no está disponible).":
        "NIC {0} configurée. Impossible de mesurer le trafic (QMP n'expose pas query-netdev et ss n'est pas disponible).",
    "Sin audio configurado en esta VM.":
        "Aucun audio configuré sur cette VM.",
    "Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.":
        "Audiodev configuré. pactl non disponible ; la lecture ne peut pas être confirmée.",
    "Audiodev configurado, pero no hay PID de QEMU para verificar el sink.":
        "Audiodev configuré, mais aucun PID QEMU pour vérifier le sink.",
    "No se pudo consultar pactl: {0}": "Impossible d'interroger pactl : {0}",
    "pactl no respondió.": "pactl n'a pas répondu.",
    "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo.":
        "Sink actif : pactl voit QEMU (PID {0}) en cours de lecture.",
    "Audiodev configurado; QEMU no está reproduciendo ahora. Es normal si el guest no está emitiendo sonido.":
        "Audiodev configuré ; QEMU ne lit rien pour le moment. C'est normal si l'invité n'émet pas de son.",
    "Framebuffer VNC {0}×{1}.": "Framebuffer VNC {0}×{1}.",
    "Widget VNC conectado, esperando primer frame.":
        "Widget VNC connecté, en attente de la première image.",
    "Consola SPICE embebida activa.": "Console SPICE intégrée active.",
    "Visor externo activo (PID {0}).":
        "Visionneuse externe active (PID {0}).",
    "Modo remoto (socket VNC/SPICE) sin widget embebido ni visor activo. Abre la Consola Gráfica para ver la pantalla.":
        "Mode distant (socket VNC/SPICE) sans widget intégré ni visionneuse active. Ouvrez la Console graphique pour voir l'écran.",
    "Modo headless (sin salida de pantalla).":
        "Mode headless (aucune sortie d'affichage).",
    "Ventana nativa de QEMU activa.": "Fenêtre native QEMU active.",
    "Configuración de pantalla detectada en el script de arranque.":
        "Configuration d'affichage détectée dans le script de démarrage.",
    "Guest Agent no habilitado para esta VM (actívalo en Integración Host ↔ Guest).":
        "Guest Agent non activé pour cette VM (activez-le dans Intégration Hôte ↔ Invité).",
    "QEMU Guest Agent responde.": "QEMU Guest Agent répond.",
    "Canal QGA presente, pero el guest no responde.":
        "Canal QGA présent, mais l'invité ne répond pas.",
    "Canal QGA presente, sin respuesta: {0}":
        "Canal QGA présent, sans réponse : {0}",

    # ================================================================
    # Install flow + mac recovery
    # ================================================================
    "Android-x86 / Bliss OS no tienen descarga automática. Descarga la ISO desde https://www.android-x86.org/download.html o https://blissos.org/ y selecciónala en Plataforma → Android.":
        "Android-x86 / Bliss OS ne supportent pas le téléchargement automatique. Téléchargez l'ISO depuis https://www.android-x86.org/download.html ou https://blissos.org/ et sélectionnez-la dans Plateforme → Android.",
    "System Recovery de macOS — {0}": "System Recovery de macOS — {0}",
    "La imagen se descarga y verifica directamente en la carpeta de la VM.":
        "L'image est téléchargée et vérifiée directement dans le dossier de la VM.",
    "No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.":
        "qemu-system-x86_64 introuvable dans le PATH. Lancez ./run.sh (installe les dépendances système) ou installez qemu-system-x86 / qemu-kvm.",
    "/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.":
        "/dev/kvm n'est pas disponible ; QEMU pourrait fonctionner sans accélération KVM.",
    "El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.":
        "L'utilisateur n'a pas les permissions de lecture/écriture sur /dev/kvm.",
    "No se detectó un firmware OVMF conocido para Secure Boot.":
        "Aucun firmware OVMF connu détecté pour Secure Boot.",
    "Solo quedan {0} GB libres donde vive esta VM; puede fallar durante el uso.":
        "Il ne reste que {0} Go libres là où vit cette VM ; elle peut échouer en cours d'utilisation.",
    "Debe indicar un nombre para la máquina virtual.":
        "Vous devez indiquer un nom pour la machine virtuelle.",
    "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.":
        "QEMU est manquant sur le système. Installez qemu-system-x86 et réessayez.",
    "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.":
        "TPM 2.0 ne s'applique pas au flux actuel de macOS/OSX-KVM.",
    "No se pudieron preparar automáticamente las dependencias necesarias.\n\n{0}":
        "Les dépendances requises n'ont pas pu être préparées automatiquement.\n\n{0}",
    "System Recovery de macOS": "System Recovery de macOS",
    "No se pudo preparar System Recovery antes de iniciar la VM.\n\n{0}":
        "System Recovery n'a pas pu être préparé avant de démarrer la VM.\n\n{0}",
    "Disco existente con otra configuración":
        "Disque existant avec une autre configuration",
    "Ya existe un disco para '{0}' con {1} / {2} / {3}, distinto a lo solicitado ({4} / {5} / {6}).\n\n¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n(\"No\" conserva el disco existente tal como está.)":
        "Un disque existe déjà pour '{0}' avec {1} / {2} / {3}, différent de ce qui a été demandé ({4} / {5} / {6}).\n\nVoulez-vous le supprimer et en créer un nouveau avec les paramètres actuels ?\n(\"Non\" conserve le disque existant tel quel.)",
    "Android": "Android",
    "Debes configurar la ISO de Android-x86 o Bliss OS en Configuración → Almacenamiento → CD / DVD.\n\nDescárgala de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAñade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente».":
        "Vous devez configurer l'ISO Android-x86 ou Bliss OS dans Configuration → Stockage → CD / DVD.\n\nTéléchargez-la depuis :\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAjoutez un lecteur CD/DVD et choisissez « Utiliser une ISO/IMG/DMG existante ».",
    "Error al guardar configuración":
        "Erreur lors de l'enregistrement de la configuration",
    "No se puede preparar el passthrough USB":
        "Impossible de préparer le passthrough USB",
    "La VM no se iniciará hasta resolver el acceso al USB.\n\n{0}\n\nNo se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.":
        "La VM ne démarrera pas tant que l'accès USB n'est pas résolu.\n\n{0}\n\nNe sélectionnez pas un Root Hub. La clé USB doit être démontée de l'hôte.",
    "Instalador del sistema operativo":
        "Installateur du système d'exploitation",
    "La descarga se realiza dentro de la carpeta de la VM.":
        "Le téléchargement se fait dans le dossier de la VM.",
    "QEMU terminó con error. Revisa la consola de progreso.":
        "QEMU s'est terminé avec une erreur. Consultez la console de progression.",

    # ================================================================
    # Media library: handlers y dialogos
    # ================================================================
    "Manuales": "Manuels",
    "De VMs": "Des VM",
    "Huerfanas de VM": "Orphelins de VM",
    "Busca archivos de medios dentro de MediaLibrary/ que aun no esten registrados, y detecta entradas huerfanas (archivo desaparecido del disco).":
        "Cherche les fichiers de médias dans MediaLibrary/ qui ne sont pas encore enregistrés, et détecte les entrées orphelines (fichier disparu du disque).",
    "↗ Agrandar": "↗ Agrandir",
    "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\nbiblioteca. Requiere que ninguna VM lo esté usando en\nes momento. El disco solo puede crecer.":
        "Augmenter la taille virtuelle d'un disque QCOW2/RAW de la\nbibliothèque. Nécessite qu'aucune VM ne l'utilise à\nce moment. Le disque ne peut que grandir.",
    "Reescribe el QCOW2 sin bloques no usados, reduciendo el\narchivo en el host. No cambia el tamaño virtual que ve el\nsistema invitado.":
        "Réécrit le QCOW2 sans les blocs non utilisés, réduisant le\nfichier sur l'hôte. Ne change pas la taille virtuelle que voit le\nsystème invité.",
    "Comprueba que el archivo exista en disco y, si hay sha256 calculado, que coincida.":
        "Vérifie que le fichier existe sur disque et, si un sha256 a été calculé, qu'il correspond.",
    "Calcula el sha256 del archivo (tarda segun el tamano). Util para detectar duplicados o descargas corruptas.":
        "Calcule le sha256 du fichier (prend du temps selon la taille). Utile pour détecter les doublons ou les téléchargements corrompus.",
    "Edita los metadatos de la entrada: nombre, distro, version, arquitectura, notas, tags y color.":
        "Modifie les métadonnées de l'entrée : nom, distro, version, architecture, notes, tags et couleur.",
    "Elimina la entrada del indice. Opcionalmente borra tambien el archivo del disco (solo si vive dentro de MediaLibrary/).":
        "Supprime l'entrée de l'index. Supprime aussi optionnellement le fichier du disque (seulement s'il vit dans MediaLibrary/).",
    "Abre la carpeta que contiene el archivo en el explorador del sistema.":
        "Ouvre le dossier contenant le fichier dans le gestionnaire de fichiers du système.",
    "<b>Notas:</b>": "<b>Notes :</b>",
    "Notas libres sobre esta entrada (uso previsto, si dio problemas, driver necesario, etc.)":
        "Notes libres sur cette entrée (utilisation prévue, si elle a posé problème, pilote nécessaire, etc.)",
    "<b>Tags:</b>": "<b>Tags :</b>",
    "Separados por coma (ej.: probado, servidor, rapiro)":
        "Séparés par une virgule (ex. : testé, serveur, rapide)",
    "<b>Color:</b>": "<b>Couleur :</b>",
    "{0} entrada(s) mostradas de {1} | Tamano total: {2}":
        "{0} entrée(s) affichée(s) sur {1} | Taille totale : {2}",
    "Anadir archivos a la biblioteca":
        "Ajouter des fichiers à la bibliothèque",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos los archivos (*)":
        "Images de disque (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Tous les fichiers (*)",
    "No se pudieron escanear las VMs.\n\n{0}":
        "Impossible d'analyser les VM.\n\n{0}",
    "Archivos unicos encontrados en VMs: {0}.":
        "Fichiers uniques trouvés dans les VM : {0}.",
    "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca.":
        "- {0} nouveau(x) support(s) ajouté(s) à la bibliothèque.",
    "- {0} entrada(s) actualizada(s) con la lista de VMs que las usan.":
        "- {0} entrée(s) mise(s) à jour avec la liste des VM qui les utilisent.",
    "Sin cambios: la biblioteca ya estaba al dia.":
        "Aucun changement : la bibliothèque était déjà à jour.",
    "No se pudo escanear.\n\n{0}":
        "Impossible d'analyser.\n\n{0}",
    "No hay archivos nuevos ni entradas huerfanas.":
        "Il n'y a pas de nouveaux fichiers ni d'entrées orphelines.",
    "{0} archivo(s) nuevos encontrados:":
        "{0} nouveau(x) fichier(s) trouvé(s) :",
    "  ... y {0} mas": "  ... et {0} de plus",
    "{0} entrada(s) huerfanas (archivo ya no existe):":
        "{0} entrée(s) orpheline(s) (le fichier n'existe plus) :",
    "Anadir los archivos nuevos a la biblioteca?":
        "Ajouter les nouveaux fichiers à la bibliothèque ?",
    "Selecciona una entrada primero.":
        "Sélectionnez d'abord une entrée.",
    "Solo se pueden agrandar discos duros (QCOW2/RAW).":
        "Seuls les disques durs (QCOW2/RAW) peuvent être agrandis.",
    "El archivo no existe:\n{0}": "Le fichier n'existe pas :\n{0}",
    "↗ Agrandar disco": "↗ Agrandir le disque",
    "Tamaño actual:": "Taille actuelle :",
    "Ejemplo: 120G (solo crecer)":
        "Exemple : 120G (agrandissement uniquement)",
    "Nuevo tamaño:": "Nouvelle taille :",
    "El disco solo puede CRECER. Agrandar el archivo NO agranda\nla partición dentro del guest: hay que ampliarla también desde\nel sistema invitado para aprovechar el nuevo espacio.":
        "Le disque ne peut que GRANDIR. Agrandir le fichier N'agrandit PAS\nla partition dans l'invité : il faut aussi l'étendre depuis\nle système invité pour profiter du nouvel espace.",
    "No se puede encoger": "Impossible de réduire",
    "Actual: {0}, indicado {1}.\n\nEl valor se ha restaurado al tamaño actual.":
        "Actuel : {0}, indiqué {1}.\n\nLa valeur a été restaurée à la taille actuelle.",
    "No se pudo agrandar el disco.\n\n{0}":
        "Impossible d'agrandir le disque.\n\n{0}",
    "Disco agrandado": "Disque agrandi",
    "Se agrandó correctamente a {0}.\n\nRecuerda ampliar también la partición dentro del sistema invitado.":
        "Agrandi correctement à {0}.\n\nN'oubliez pas d'étendre aussi la partition dans le système invité.",
    "Solo se pueden compactar discos en formato QCOW2.":
        "Seuls les disques au format QCOW2 peuvent être compactés.",
    "\n\n⚠ Este disco lo usan VMs apagadas: {0}.\nSe recomienda hacer un backup antes de compactar.":
        "\n\n⚠ Ce disque est utilisé par des VM éteintes : {0}.\nUne sauvegarde est recommandée avant de compacter.",
    "Confirmar compactado": "Confirmer la compaction",
    "Compactando... {0}%": "Compaction... {0} %",
    "Disco compactado": "Disque compacté",
    "No se pudo compactar.\n\n{0}":
        "Impossible de compacter.\n\n{0}",
    "Reescribiendo el QCOW2 sin bloques no usados...":
        "Réécriture du QCOW2 sans les blocs non utilisés…",
    "El archivo ya no existe:\n{0}": "Le fichier n'existe plus :\n{0}",
    "Archivo presente y sha256 coincide.":
        "Fichier présent et le sha256 correspond.",
    "sha256 NO coincide.\n\nEsperado: {0}\nActual:   {1}":
        "sha256 NE correspond PAS.\n\nAttendu : {0}\nActuel :   {1}",
    "SHA256": "SHA256",
    "sha256 calculado y guardado:\n\n{0}":
        "sha256 calculé et enregistré :\n\n{0}",
    "Error: {0}": "Erreur : {0}",
    "Calculando sha256 — {0}": "Calcul du sha256 — {0}",
    "Editar — {0}": "Modifier — {0}",
    "Version:": "Version :",
    "No se pudo guardar: {0}": "Impossible d'enregistrer : {0}",
    "La carpeta no existe:\n{0}": "Le dossier n'existe pas :\n{0}",

    # ================================================================
    # Passthrough: IOMMU / VFIO / USB
    # ================================================================
    "El procesador no se identificó como Intel; no se aplicará intel_iommu=on.":
        "Le processeur n'a pas été identifié comme Intel ; intel_iommu=on ne sera pas appliqué.",
    "No pude identificar de forma segura el gestor de arranque.":
        "Impossible d'identifier en toute sécurité le gestionnaire d'amorçage.",
    "La preparación automática está implementada actualmente para GRUB. Gestor detectado: {0}.":
        "La préparation automatique est actuellement implémentée pour GRUB. Gestionnaire détecté : {0}.",
    "No se pudo leer {0}.": "Impossible de lire {0}.",
    "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub.":
        "GRUB_CMDLINE_LINUX_DEFAULT introuvable dans /etc/default/grub.",
    "intel_iommu=on ya está presente en /etc/default/grub.":
        "intel_iommu=on est déjà présent dans /etc/default/grub.",
    "operación cancelada": "opération annulée",
    "Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ":
        "/etc/default/grub a été modifié, mais grub.cfg n'a pas pu être régénéré : ",
    "error desconocido": "erreur inconnue",
    "Se añadió intel_iommu=on y se regeneró GRUB.":
        "intel_iommu=on a été ajouté et GRUB régénéré.",
    "IOMMU / VT-d": "IOMMU / VT-d",
    "El IOMMU ya aparece activo. No es necesario modificar el arranque.":
        "IOMMU apparaît déjà actif. Pas besoin de modifier le démarrage.",
    "No se identificó un CPU Intel.": "Aucun CPU Intel identifié.",
    "Preparar Intel IOMMU": "Préparer Intel IOMMU",
    "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\nSe hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\nEsto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\nGestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?":
        "intel_iommu=on sera ajouté à la configuration du gestionnaire d'amorçage.\n\nUne sauvegarde sera faite avant de la modifier et une autorisation administrative sera demandée.\n\nCela N'active PAS VT-d dans le BIOS/UEFI ; cette partie doit être activée dans le firmware.\n\nGestionnaire détecté : {0}\nFichier : {1}\n\nContinuer ?",
    "no identificado": "non identifié",
    "Configuración actualizada.": "Configuration mise à jour.",
    "\n\nReinicia el equipo para que el parámetro tenga efecto.":
        "\n\nRedémarrez l'ordinateur pour que le paramètre prenne effet.",
    "No se pudo preparar IOMMU": "Impossible de préparer IOMMU",
    "Abrir UEFI/BIOS": "Ouvrir UEFI/BIOS",
    "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\nBusca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?":
        "L'ordinateur redémarrera directement vers la configuration du firmware si le système le permet.\n\nCherchez une option appelée Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d ou similaire et activez-la.\n\nRedémarrer maintenant ?",
    "No se pudo solicitar el reinicio al firmware.":
        "Impossible de demander le redémarrage au firmware.",
    "No se pudo abrir UEFI/BIOS": "Impossible d'ouvrir UEFI/BIOS",
    "Desactivado por parámetro del kernel":
        "Désactivé par paramètre du noyau",
    "Activo": "Actif",
    "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles":
        "VT-d détecté par firmware/noyau ; IOMMU sans groupes visibles",
    "No detectado": "Non détecté",
    "Detectado": "Détecté",
    "No confirmado": "Non confirmé",
    "✓ Listo para VFIO": "✓ Prêt pour VFIO",
    "⚠ Sin grupo IOMMU": "⚠ Sans groupe IOMMU",
    "⚠ Comparte grupo IOMMU": "⚠ Partage le groupe IOMMU",
    "⚠ Requiere preparación VFIO": "⚠ Préparation VFIO requise",
    "IOMMU/Intel VT-d: {0}": "IOMMU/Intel VT-d : {0}",
    "Firmware/ACPI DMAR: {0}": "Firmware/ACPI DMAR : {0}",
    "Grupos IOMMU: {0}": "Groupes IOMMU : {0}",
    "{0}: no tiene grupo IOMMU ({1})":
        "{0} : n'a pas de groupe IOMMU ({1})",
    "{0}: comparte grupo IOMMU {1} con {2}":
        "{0} : partage le groupe IOMMU {1} avec {2}",
    "{0}: driver actual {1}; todavía no está ligado a vfio-pci":
        "{0} : pilote actuel {1} ; pas encore lié à vfio-pci",
    "• {0} | grupo {1} | driver {2}":
        "• {0} | groupe {1} | pilote {2}",
    "✅ Intel VT-d / IOMMU activo": "✅ Intel VT-d / IOMMU actif",
    "⚠ VT-d detectado por firmware, pero no hay grupos IOMMU utilizables":
        "⚠ VT-d détecté par firmware, mais aucun groupe IOMMU utilisable",
    "❌ Intel VT-d / IOMMU no detectado":
        "❌ Intel VT-d / IOMMU non détecté",
    "(sin datos)": "(sans données)",
    "<b>{0}</b><br>Firmware/ACPI DMAR: {1}<br>Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>Gestor de arranque: {4}<br>Parámetros kernel: <code>{5}</code>":
        "<b>{0}</b><br>Firmware/ACPI DMAR : {1}<br>Groupes IOMMU : {2} &nbsp;|&nbsp; PCI prêts pour VFIO : {3}<br>Gestionnaire d'amorçage : {4}<br>Paramètres noyau : <code>{5}</code>",
    "Desconocido": "Inconnu",
    "<br>⚠ El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.":
        "<br>⚠ Le CPU n'a pas été identifié comme Intel ; vérifier le diagnostic AMD/IOMMU.",
    "<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.":
        "<br>Recommandation : utiliser <b>Préparer intel_iommu=on</b> et redémarrer. Si après redémarrage il n'y a toujours pas de groupes, vérifier VT-d dans le BIOS/UEFI.",
    "<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar <code>intel_iommu=on</code> en el arranque.":
        "<br>Recommandation : activer Intel VT-d dans le BIOS/UEFI puis activer <code>intel_iommu=on</code> au démarrage.",
    "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===":
        "=== DIAGNOSTIC INTEL VT-d / IOMMU / VFIO ===",
    "Estado: {0}": "État : {0}",
    "Arquitectura: {0}": "Architecture : {0}",
    "CPU Intel detectado: {0}": "CPU Intel détecté : {0}",
    "intel_iommu=on en kernel actual: {0}":
        "intel_iommu=on dans le noyau actuel : {0}",
    "IOMMU desactivado por parámetro: {0}":
        "IOMMU désactivé par paramètre : {0}",
    "Clases IOMMU: {0}": "Classes IOMMU : {0}",
    "Gestor de arranque: {0}": "Gestionnaire d'amorçage : {0}",
    "desconocido": "inconnu",
    "Configuración: {0}": "Configuration : {0}",
    "no identificada": "non identifiée",
    "Parámetros kernel: {0}": "Paramètres noyau : {0}",
    "=== DISPOSITIVOS PCI ===": "=== PÉRIPHÉRIQUES PCI ===",
    "{0} | {1} | driver={2} | grupo={3} | estado={4}":
        "{0} | {1} | pilote={2} | groupe={3} | état={4}",
    "sin driver": "sans pilote",
    "Diagnóstico VFIO": "Diagnostic VFIO",
    "Diagnóstico copiado al portapapeles.":
        "Diagnostic copié dans le presse-papiers.",
    "No se pudo copiar el diagnóstico":
        "Impossible de copier le diagnostic",
    "Diagnóstico Intel VT-d / IOMMU / VFIO":
        "Diagnostic Intel VT-d / IOMMU / VFIO",
    "📋 Copiar": "📋 Copier",
    "No existe {0}. El número Device puede haber cambiado; vuelve a detectar USB.":
        "{0} n'existe pas. Le numéro Device a peut-être changé ; redétectez l'USB.",
    "Sin acceso de lectura/escritura a {0}.":
        "Pas d'accès en lecture/écriture à {0}.",
    "No se pudo ejecutar la acción administrativa ({0}): {1}":
        "Impossible d'exécuter l'action administrative ({0}) : {1}",
    "No se pudo realizar la acción administrativa ({0}). {1}":
        "Impossible d'effectuer l'action administrative ({0}). {1}",
    "No existe el nodo USB actual {0}; el dispositivo pudo cambiar de dirección.":
        "Le nœud USB actuel {0} n'existe pas ; le périphérique a peut-être changé d'adresse.",
    "dar acceso temporal al dispositivo USB":
        "accorder un accès temporaire au périphérique USB",
    "No pude desmontar automáticamente el almacenamiento USB:\n{0}\n\n{1}":
        "Impossible de démonter automatiquement le stockage USB :\n{0}\n\n{1}",
    "El USB sigue sin acceso después de preparar el dispositivo: {0}":
        "L'USB est toujours sans accès après avoir préparé le périphérique : {0}",
    "USB {0} | nodo: {1} | acceso usuario: {2} | {3}":
        "USB {0} | nœud : {1} | accès utilisateur : {2} | {3}",
    "NO": "NON",
    "no se pudo leer ({0})": "impossible de lire ({0})",
    "error al comprobar: {0}": "erreur lors de la vérification : {0}",
    "✅ Permisos USB: OK ({0}). El passthrough en caliente no pedirá contraseña.":
        "✅ Permissions USB : OK ({0}). Le passthrough à chaud ne demandera pas de mot de passe.",
    "Los permisos USB ya están configurados.\nSi quieres desinstalarlos, borra:\n{0}":
        "Les permissions USB sont déjà configurées.\nSi vous voulez les désinstaller, supprimez :\n{0}",
    "⚠ Permisos USB: {0}. El passthrough en caliente pedirá contraseña cada vez.":
        "⚠ Permissions USB : {0}. Le passthrough à chaud demandera le mot de passe à chaque fois.",
    "Permisos USB": "Permissions USB",
    "Configurar permisos USB": "Configurer les permissions USB",
    "La operación tardó demasiado. Vuelve a intentarlo.":
        "L'opération a pris trop de temps. Veuillez réessayer.",
    "Dispositivo USB inválido.": "Périphérique USB invalide.",

    # ================================================================
    # Menu Medios: unidades opticas + USB
    # ================================================================
    "📀 Unidades ópticas": "📀 Lecteurs optiques",
    "      (Sin unidades CD/DVD)": "      (Aucun lecteur CD/DVD)",
    "🌐 descargar instalador al iniciar":
        "🌐 télécharger l'installateur au démarrage",
    "🌐 descargar Recovery al iniciar":
        "🌐 télécharger le Recovery au démarrage",
    "   📀 {0} — {1}": "   📀 {0} — {1}",
    "📂 Cambiar medio…": "📂 Changer le support…",
    "⏏ Expulsar medio": "⏏ Éjecter le support",
    "🔌 Dispositivos USB": "🔌 Périphériques USB",
    "      (La VM debe estar encendida para conectarlos)":
        "      (La VM doit être allumée pour les connecter)",
    "      Error al detectar USB: {0}":
        "      Erreur lors de la détection USB : {0}",
    "      (No hay dispositivos USB detectados)":
        "      (Aucun périphérique USB détecté)",
    "conectado a la VM": "connecté à la VM",
    "disponible en el host": "disponible sur l'hôte",
    "{0}\nVID:PID = {1}:{2}\nBus {3} · Device {4}\nEstado: {5}\n\n{6}":
        "{0}\nVID:PID = {1}:{2}\nBus {3} · Device {4}\nÉtat : {5}\n\n{6}",
    "Clic para DESCONECTAR de la VM":
        "Cliquer pour DÉCONNECTER de la VM",
    "Clic para CONECTAR a la VM":
        "Cliquer pour CONNECTER à la VM",
    "(Selecciona una VM primero)": "(Sélectionnez d'abord une VM)",
    "🔄 Refrescar": "🔄 Actualiser",
    "⚙ Gestionar USB en Passthrough…":
        "⚙ Gérer l'USB en Passthrough…",
    "Grupo {0}": "Groupe {0}",
    "Sin grupo IOMMU": "Sans groupe IOMMU",
    " • {0}": " • {0}",
    "⚠ Revisar": "⚠ À vérifier",
    "✓ Acceso OK": "✓ Accès OK",
    "⚠ Revisar acceso": "⚠ Vérifier l'accès",
    "Passthrough: teclado o ratón del host":
        "Passthrough : clavier ou souris de l'hôte",
    "Passthrough USB": "Passthrough USB",
    "Selecciona un dispositivo USB.":
        "Sélectionnez un périphérique USB.",
    "La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.":
        "La VM n'est pas allumée ; utilisez Enregistrer la sélection pour l'attacher au prochain démarrage.",
    "Dispositivo USB conectado en caliente a la VM.\n\nNota: el host debe permitir acceso a /dev/bus/usb y el dispositivo no debería estar siendo usado por el sistema anfitrión.":
        "Périphérique USB connecté à chaud à la VM.\n\nNote : l'hôte doit autoriser l'accès à /dev/bus/usb et le périphérique ne doit pas être utilisé par le système hôte.",
    "Error al conectar USB": "Erreur lors de la connexion USB",
    "La VM no está encendida.": "La VM n'est pas allumée.",
    "Solicitud de desconexión USB enviada a QEMU.":
        "Demande de déconnexion USB envoyée à QEMU.",
    "Error al desconectar USB": "Erreur lors de la déconnexion USB",

    # ================================================================
    # Shortcuts (tooltip grande que quedo pendiente)
    # ================================================================
    "Reasigna los atajos globales de la aplicacion. Los cambios\nse aplican al instante, sin reiniciar.":
        "Réassigne les raccourcis globaux de l'application. Les changements\ns'appliquent immédiatement, sans redémarrage.",

    # ================================================================
    # Snapshots automaticos programados
    # ================================================================
    "Snapshots automaticos programados": "Instantanés programmés",
    "Frecuencia con la que se crea el snapshot automatico.\nEl primer snapshot se crea pasada una frecuencia completa desde la activacion (o desde el ultimo, si ya habia uno).":
        "Fréquence à laquelle l'instantané automatique est créé.\nLe premier instantané est créé après une période complète depuis l'activation (ou depuis le dernier, s'il y en avait déjà un).",
    "Los snapshots programados son <b>solo de discos</b>: no guardan RAM ni estado de ventanas. No congelan la VM del usuario (el snapshot completo si puede hacerlo).":
        "Les instantanés programmés sont <b>disque uniquement</b> : ils n'enregistrent ni la RAM ni l'état des fenêtres. Ils ne gèlent pas la VM de l'utilisateur (un instantané complet peut le faire).",
    "Selecciona una VM para programar snapshots.":
        "Sélectionnez une VM pour programmer les instantanés.",
    "Sin snapshots programados todavia. Se creara el primero tras cumplirse la frecuencia elegida.":
        "Aucun instantané programmé pour le moment. Le premier sera créé une fois la fréquence choisie écoulée.",
    "Pendiente (ultimo: {0}). Se ejecutara en el proximo chequeo del scheduler.":
        "En attente (dernière : {0}). S'exécutera au prochain contrôle du planificateur.",
    "Ultimo: {0} · Proximo en ~{1} min.":
        "Dernière : {0} · Prochaine dans ~{1} min.",
    "Ultimo: {0}": "Dernière : {0}",

    # ================================================================
    # Snapshots: dialogos de creacion / restauracion / borrado
    # ================================================================
    "Apagado no completado": "Arrêt non terminé",
    "No se puede restaurar este snapshot":
        "Cet instantané ne peut pas être restauré",
    "(solo disco)": "(disque uniquement)",
    "Los snapshots creados con la VM en ejecución guardan una captura de pantalla que se muestra aquí.":
        "Les instantanés créés pendant que la VM est en cours d'exécution enregistrent une capture d'écran qui est affichée ici.",
    "Captura no legible": "Capture illisible",
    "Restaurar snapshot": "Restaurer l'instantané",
    "No hay ningún snapshot reciente para restaurar.":
        "Il n'y a aucun instantané récent à restaurer.",
    "No hay otros snapshots para elegir como padre.":
        "Il n'y a pas d'autres instantanés à choisir comme parent.",
    "(ninguno — mover a la raíz)": "(aucun — déplacer à la racine)",
    "Establecer padre": "Définir le parent",
    "Nuevo snapshot hijo": "Nouvel instantané enfant",
    "No se pudo crear el snapshot.\n\n{0}":
        "Impossible de créer l'instantané.\n\n{0}",
    "💽 SATA": "💽 SATA",
    "⚡ NVMe": "⚡ NVMe",
    "❌ No hay un QCOW2 escribible disponible para snapshots completos de VM.":
        "❌ Aucun QCOW2 inscriptible disponible pour des instantanés complets de VM.",
    "✅ Disco para estado de VM: {0} · tamaño virtual: {1} · archivo actual: {2} · espacio libre del sistema de archivos: {3} · reserva orientativa inicial: {4}. El snapshot QCOW2 crece según se modifican bloques.":
        "✅ Disque pour l'état de la VM : {0} · taille virtuelle : {1} · fichier actuel : {2} · espace libre du système de fichiers : {3} · réserve indicative initiale : {4}. L'instantané QCOW2 grandit au fur et à mesure que les blocs sont modifiés.",
    "⚠ {0} El snapshot podría fallar al quedarse sin espacio.":
        "⚠ {0} L'instantané pourrait échouer en manquant d'espace.",
    "Snapshot con VirtIO-GPU": "Instantané avec VirtIO-GPU",
    "Selecciona una máquina virtual.": "Sélectionnez une machine virtuelle.",
    "No se puede crear un snapshot completo.\n\n":
        "Impossible de créer un instantané complet.\n\n",
    "Espacio disponible": "Espace disponible",
    "{0}\n\nQEMU puede necesitar espacio adicional a medida que cambien los bloques. ¿Quieres continuar de todos modos?":
        "{0}\n\nQEMU peut avoir besoin d'espace supplémentaire au fur et à mesure que les blocs changent. Voulez-vous continuer quand même ?",
    "Crear snapshot": "Créer un instantané",
    "Nombre del snapshot:": "Nom de l'instantané :",
    "Clon enlazado: snapshot solo de discos":
        "Clone lié : instantané disque uniquement",
    "Esta VM es un clon enlazado (backing file QCOW2).\n\nQEMU no puede crear/restaurar snapshots completos\n(RAM + dispositivos) sobre un QCOW2 con backing\nfile: al hacer loadvm QEMU aborta con una aserción\ninterna (vmstate_load_next).\n\nPor seguridad se creará un snapshot SOLO DE DISCOS,\nque sí se puede restaurar con la VM apagada.\n\nSi necesitas un snapshot completo, desenlaza\nprimero el clon (🧬 Desenlazar).":
        "Cette VM est un clone lié (backing file QCOW2).\n\nQEMU ne peut pas créer/restaurer d'instantanés complets\n(RAM + périphériques) sur un QCOW2 avec backing\nfile : lors du loadvm, QEMU abandonne avec une assertion\ninterne (vmstate_load_next).\n\nPar sécurité, un instantané DISQUE UNIQUEMENT sera créé,\nqui peut être restauré avec la VM éteinte.\n\nSi vous avez besoin d'un instantané complet, détachez\nd'abord le clone (🧬 Détacher).",
    "Snapshot con la VM encendida": "Instantané avec la VM allumée",
    "La VM está encendida.\n\nUn snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\nSí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\nNo = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\nCancelar = no hacer nada.":
        "La VM est allumée.\n\nUn instantané COMPLET doit enregistrer la RAM et l'état de tous les périphériques et peut occuper QEMU complètement pendant ce processus. Sur cette VM, nous avons déjà observé que QEMU peut rester en STOP pendant longtemps.\n\nOui = créer un INSTANTANÉ COMPLET (VM + RAM + périphériques + disques).\nNon = créer un INSTANTANÉ DISQUE UNIQUEMENT (rapide ; n'enregistre ni la RAM ni les fenêtres).\nAnnuler = ne rien faire.",
    "Snapshot de discos creado": "Instantané de disques créé",
    "Error al crear snapshot de discos":
        "Erreur lors de la création de l'instantané de disques",
    "Error al crear snapshot":
        "Erreur lors de la création de l'instantané",
    "No se pudo crear el snapshot completo.\n\n{0}":
        "Impossible de créer l'instantané complet.\n\n{0}",
    "Ya hay una operación de snapshot en curso.":
        "Une opération d'instantané est déjà en cours.",
    "La operación se ejecuta en segundo plano; la interfaz sigue disponible mientras QEMU procesa el snapshot.":
        "L'opération s'exécute en arrière-plan ; l'interface reste disponible pendant que QEMU traite l'instantané.",
    "Snapshot — {0}": "Instantané — {0}",
    "Snapshot creado": "Instantané créé",
    "VM pausada": "VM en pause",
    "Snapshot eliminado": "Instantané supprimé",
    "Snapshot restaurado": "Instantané restauré",
    "CREACIÓN": "CRÉATION",
    "ELIMINACIÓN": "SUPPRESSION",
    "GUARDADO": "ENREGISTREMENT",
    "RESTAURACIÓN": "RESTAURATION",
    "Snapshot solo de discos": "Instantané disque uniquement",
    "Apagar la VM": "Éteindre la VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Impossible d'envoyer la commande d'arrêt.\n\n{0}",
    "Restauración parcial": "Restauration partielle",
    "El snapshot se restauró en algunos discos, pero falló en otros:\n\n":
        "L'instantané a été restauré sur certains disques, mais a échoué sur d'autres :\n\n",
    "Se restauró el snapshot de disco en los QCOW2 elegibles. Con la VM apagada no se restaura el estado de RAM/CPU.":
        "L'instantané de disque a été restauré sur les QCOW2 éligibles. Avec la VM éteinte, l'état RAM/CPU n'est pas restauré.",
    "Error al restaurar snapshot":
        "Erreur lors de la restauration de l'instantané",
    "No se pudo restaurar el snapshot.\n\n{0}":
        "Impossible de restaurer l'instantané.\n\n{0}",
    "Eliminar snapshot": "Supprimer l'instantané",
    "Eliminación parcial": "Suppression partielle",
    "El snapshot se eliminó de algunos discos, pero falló en otros:\n\n":
        "L'instantané a été supprimé de certains disques, mais a échoué sur d'autres :\n\n",
    "Error al eliminar snapshot":
        "Erreur lors de la suppression de l'instantané",
    "No se pudo eliminar el snapshot.\n\n{0}":
        "Impossible de supprimer l'instantané.\n\n{0}",
    "Cambiar nombre de snapshot": "Renommer l'instantané",
    "QEMU no proporciona un renombrado interno directo. Esta acción creará un snapshot nuevo con el estado ACTUAL de la VM y eliminará el anterior.\n\n¿Continuar?":
        "QEMU ne fournit pas de renommage interne direct. Cette action créera un nouvel instantané avec l'état ACTUEL de la VM et supprimera le précédent.\n\nContinuer ?",
    "Cambio de nombre parcial": "Renommage partiel",
    "El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n":
        "Le nouvel instantané a été créé sur certains disques, mais il y a eu des erreurs :\n\n",
    "Error al cambiar nombre": "Erreur lors du renommage",
    "No se pudo cambiar el nombre.\n\n{0}":
        "Impossible de changer le nom.\n\n{0}",

    # ================================================================
    # Storage: expandir disco
    # ================================================================
    "Cambiar el medio de esta unidad CD/DVD.":
        "Changer le support de ce lecteur CD/DVD.",
    "Los disquetes no se pueden redimensionar.\nElimina este y crea otro si necesitas otro tamaño.":
        "Les disquettes ne peuvent pas être redimensionnées.\nSupprimez celle-ci et créez-en une autre si vous avez besoin d'une autre taille.",
    "↗ Expandir": "↗ Étendre",
    "Aumentar el tamaño virtual de este disco.\nEl disco solo puede CRECER.":
        "Augmenter la taille virtuelle de ce disque.\nLe disque ne peut que GRANDIR.",
    "Disco": "Disque",
    "FDC": "FDC",
    "🌐 Descargar instalador de Internet al iniciar":
        "🌐 Télécharger l'installateur depuis Internet au démarrage",
    "🌐 Instalador por Internet (se descargará al iniciar)":
        "🌐 Installateur par Internet (sera téléchargé au démarrage)",
    "🌐 Descargar System Recovery al iniciar":
        "🌐 Télécharger System Recovery au démarrage",
    "🌐 System Recovery (se descargará al iniciar)":
        "🌐 System Recovery (sera téléchargé au démarrage)",
    "Sin medio": "Sans support",
    "Expandir disco": "Étendre le disque",
    "No se encontro la informacion del dispositivo seleccionado.":
        "Les informations du périphérique sélectionné n'ont pas été trouvées.",
    "Los disquetes no se pueden redimensionar.\n\nEliminalo y crea otro si necesitas otro tamano.":
        "Les disquettes ne peuvent pas être redimensionnées.\n\nSupprimez-la et créez-en une autre si vous avez besoin d'une autre taille.",
    "↗ Expandir disco": "↗ Étendre le disque",
    "Dispositivo:": "Périphérique :",
    "Tamano actual:": "Taille actuelle :",
    "Nuevo tamano:": "Nouvelle taille :",
    "El disco solo puede CRECER. Si escribes un valor menor al actual, se rechaza y el campo vuelve al tamano original.\n\nAgrandar el archivo NO agranda la particion dentro del guest: tras aplicar el cambio, amplia tambien la particion/volumen desde el sistema invitado.":
        "Le disque ne peut que GRANDIR. Si vous saisissez une valeur inférieure à l'actuelle, elle est rejetée et le champ revient à la taille d'origine.\n\nAgrandir le fichier N'agrandit PAS la partition dans l'invité : après avoir appliqué le changement, étendez aussi la partition/le volume depuis le système invité.",
    "No se pudo expandir el disco.\n\n{0}":
        "Impossible d'étendre le disque.\n\n{0}",
    "💡 Sugerencias": "💡 Suggestions",
    "No se pudo guardar la etiqueta.\n\n{0}":
        "Impossible d'enregistrer l'étiquette.\n\n{0}",
    "Comando QEMU": "Commande QEMU",
    "Sin adaptadores configurados": "Aucun adaptateur configuré",
    "VM nueva: todavía no se ha guardado una configuración.":
        "Nouvelle VM : aucune configuration enregistrée pour le moment.",
    "Primero selecciona una máquina virtual existente.":
        "Sélectionnez d'abord une machine virtuelle existante.",
    "¿Deseas continuar?": "Voulez-vous continuer ?",
    "Guest Agent: {0}": "Guest Agent : {0}",
    "Carpetas: {0}": "Dossiers : {0}",
    "Ctrl derecho": "Ctrl droit",

    # ================================================================
    # Graficos: labels dinamicos
    # ================================================================
    "No detectada": "Non détecté",
    "✓ OpenGL": "✓ OpenGL",
    "✗ OpenGL": "✗ OpenGL",
    "✓ VirGL": "✓ VirGL",
    "✓ VirGL instalado": "✓ VirGL installé",
    "✗ VirGL": "✗ VirGL",
    "✓ Vulkan": "✓ Vulkan",
    "✗ Vulkan": "✗ Vulkan",
    "VGA estándar (QEMU -vga std)": "VGA standard (QEMU -vga std)",
    "sin aceleración 3D": "sans accélération 3D",
    "VGA de OSX-KVM (VGA virtual)": "VGA de OSX-KVM (VGA virtuel)",
    "gestionada por OpenCore/OSX-KVM": "gérée par OpenCore/OSX-KVM",
    "VirtIO-GPU + VirGL 3D": "VirtIO-GPU + VirGL 3D",
    "OpenGL / VirGL": "OpenGL / VirGL",
    "VirtIO-GPU 2D": "VirtIO-GPU 2D",
    "VGA estándar de QEMU": "VGA standard de QEMU",
    "<b>Automático → {0}</b><br>Aceleración: {1}":
        "<b>Automatique → {0}</b><br>Accélération : {1}",
    "VirtIO-GPU + Venus/Vulkan 3D": "VirtIO-GPU + Venus/Vulkan 3D",
    "Red Hat QXL 2D": "Red Hat QXL 2D",
    "VMware SVGA II": "VMware SVGA II",
    "<b>Usará: {0}</b>": "<b>Utilisera : {0}</b>",
    "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}":
        "GPU hôte : {0}<br>{1}  |  {2}  |  {3}<br>{4}",
    "Host GPU: no se pudo determinar automáticamente.<br>Automático: se seleccionará el modo gráfico compatible disponible.":
        "GPU hôte : n'a pas pu être déterminé automatiquement.<br>Automatique : le mode graphique compatible disponible sera sélectionné.",

    # ================================================================
    # Plantillas
    # ================================================================
    "Guardar como plantilla": "Enregistrer comme modèle",
    "Esta VM no tiene vm_config.ini todavía.\n\nConfigúrala y guárdala primero.":
        "Cette VM n'a pas encore de vm_config.ini.\n\nConfigurez-la et enregistrez-la d'abord.",
    "No se pudo escribir la plantilla.\n\n{0}":
        "Impossible d'écrire le modèle.\n\n{0}",
    "🆕 Nueva VM en blanco": "🆕 Nouvelle VM vierge",
    "Desde plantilla:": "Depuis un modèle :",
    "Crear desde plantilla": "Créer depuis un modèle",
    "No se pudo eliminar la carpeta existente.\n\n{0}":
        "Impossible de supprimer le dossier existant.\n\n{0}",
    "No se pudo crear la VM.\n\n{0}":
        "Impossible de créer la VM.\n\n{0}",
    "macOS": "macOS",

    # --- i18n_fr_tanda3_v1 ---
}
