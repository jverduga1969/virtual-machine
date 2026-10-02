# -*- coding: utf-8 -*-
"""Frances — Tanda 2b: VirtualMachineManagerApp (el bloque grande)."""

TRANSLATIONS = {

    # ================================================================
    # Sistema: tooltips avanzados
    # ================================================================
    "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\n"
    "Q35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\n"
    "passthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica.":
        "i440FX : chipset classique, PCI hérité. Compatible avec les OS très anciens.\n"
        "Q35 : chipset moderne avec PCIe natif, AHCI/SATA et meilleur support pour\n"
        "le passthrough de périphériques PCIe. Recommandé sauf compatibilité spécifique.",
    "Si está marcado, esta VM se arranca automáticamente al\n"
    "abrir la aplicación, tras un par de segundos.\n\n"
    "Las VMs marcadas se arrancan en cola, separadas por 4 s\n"
    "entre una y otra para no saturar el host. Las que ya estén\n"
    "corriendo se saltan.\n\n"
    "Nota: al auto-arrancar, la selección de la lista cambia a\n"
    "cada VM que se inicia.":
        "Si coché, cette VM démarre automatiquement à\n"
        "l'ouverture de l'application, après quelques secondes.\n\n"
        "Les VM cochées sont démarrées en file, espacées de 4 s\n"
        "entre chacune pour ne pas saturer l'hôte. Celles déjà\n"
        "en cours sont ignorées.\n\n"
        "Note : au démarrage automatique, la sélection de la liste\n"
        "change pour chaque VM démarrée.",

    # ================================================================
    # Procesador: tooltips avanzados
    # ================================================================
    "Automático usa el perfil del SO. Host ofrece el máximo rendimiento "
    "pero reduce la portabilidad de la VM.":
        "Automatique utilise le profil de l'OS. Hôte offre la performance maximale "
        "mais réduit la portabilité de la VM.",
    "El número de núcleos se ajusta al par más cercano al valor elegido, "
    "hasta la mitad de los hilos del host.":
        "Le nombre de cœurs est arrondi au pair le plus proche de la valeur choisie, "
        "jusqu'à la moitié des threads de l'hôte.",
    "Asignar más de la mitad de la RAM del host puede provocar uso intensivo "
    "de swap. La sugerencia es dejar al menos 2 GB para el sistema anfitrión.":
        "Allouer plus de la moitié de la RAM de l'hôte peut provoquer un usage intensif "
        "du swap. Il est recommandé de laisser au moins 2 Go pour le système hôte.",

    # ================================================================
    # Pantalla: textos extensos
    # ================================================================
    "Automático detecta las capacidades del host y usa aceleración 3D cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\n"
    "Snapshots:\n"
    "  • VirtIO-GPU 2D → solo snap. de discos.\n"
    "  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n"
    "  • VirGL / Venus → no soportan ningún tipo de snapshot.":
        "Automatique détecte les capacités de l'hôte et utilise l'accélération 3D si elle est sûre ; sinon, revient à VirtIO-GPU 2D.\n\n"
        "Instantanés :\n"
        "  • VirtIO-GPU 2D → instantanés de disques uniquement.\n"
        "  • QXL et VMware SVGA → instantané complet (RAM + périphériques).\n"
        "  • VirGL / Venus → ne supportent aucun type d'instantané.",
    "Cuando está activo, la VM se muestra dentro de la app.\n"
    "Fuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\n"
    "Si lo desactivas, la VM se abre en una ventana externa y puedes\n"
    "elegir modos con aceleración 3D (VirGL, Venus).":
        "Lorsqu'activé, la VM s'affiche dans l'application.\n"
        "Force des graphiques sans accélération OpenGL (VNC ne supporte pas GL).\n"
        "Si vous le désactivez, la VM s'ouvre dans une fenêtre externe et vous pouvez\n"
        "choisir des modes avec accélération 3D (VirGL, Venus).",
    "VNC: cliente ligero, funciona con cualquier dispositivo de video.\n"
    "SPICE: mejor rendimiento en local, requiere un visor spice-gtk.\n"
    "Con cualquiera de los dos, QEMU no abre ventana local: solo el socket.":
        "VNC : client léger, fonctionne avec n'importe quel périphérique vidéo.\n"
        "SPICE : meilleure performance en local, nécessite une visionneuse spice-gtk.\n"
        "Avec l'un ou l'autre, QEMU n'ouvre pas de fenêtre locale : seulement le socket.",
    "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\n"
    "Ventana externa: se lanza el visor del sistema (vncviewer / spicy).\n"
    "Nativa QEMU: QEMU abre su propia ventana (comportamiento clásico).":
        "Intégrée : l'écran vit dans cette application (onglet Console graphique).\n"
        "Fenêtre externe : lance la visionneuse du système (vncviewer / spicy).\n"
        "Native QEMU : QEMU ouvre sa propre fenêtre (comportement classique).",
    "Activa el nivel DEBUG del cliente VNC embebido.\n\n"
    "Por defecto INFO: el widget VNC no llena launch.log con\n"
    "una línea por cada frame. Actívalo solo para diagnosticar\n"
    "problemas concretos del cliente VNC; escribe miles de\n"
    "líneas por segundo y puede afectar al rendimiento.":
        "Active le niveau DEBUG du client VNC intégré.\n\n"
        "Par défaut INFO : le widget VNC ne remplit pas launch.log avec\n"
        "une ligne par image. Activez-le seulement pour diagnostiquer\n"
        "des problèmes spécifiques du client VNC ; écrit des milliers de\n"
        "lignes par seconde et peut affecter les performances.",

    # ================================================================
    # Dispositivos: tooltips avanzados
    # ================================================================
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
        "Périphérique d'entrée que QEMU émule pour la souris/le clavier.\n\n"
        "• Automatique : macOS utilise USB Tablet sur NEC XHCI ; les autres gardent\n"
        "  le PS/2 par défaut de QEMU.\n"
        "• USB Tablet : position absolue (le curseur de l'invité suit 1:1 celui\n"
        "  de l'hôte). Recommandé si le curseur ne se déplace pas bien.\n"
        "• USB Mouse : position relative, comme une souris physique.\n"
        "• Clavier USB + Tablet : ajoute aussi un clavier USB.\n"
        "• VirtIO Tablet : meilleure performance, nécessite les pilotes VirtIO dans\n"
        "  l'invité (non valide sur macOS).\n"
        "• PS/2 : souris/clavier traditionnels de QEMU, sans USB.\n"
        "• Aucun : aucun clavier/souris émulé.",
    "Activa -serial file:<vm_dir>/serial.log en la linea de QEMU.\n\n"
    "El puerto serie del guest se vuelca a un archivo dentro de la\n"
    "carpeta de la VM. La BIOS/OVMF, el cargador de arranque y el\n"
    "kernel suelen escribir ahi su progreso: es la forma mas directa\n"
    "de ver por que una VM se queda en pantalla negra o se reinicia.\n\n"
    "El archivo se SOBREESCRIBE en cada arranque: solo conserva la\n"
    "ultima sesion. Se puede abrir con '📂 Carpeta' en la pestana\n"
    "Resumen.":
        "Active -serial file:<vm_dir>/serial.log dans la ligne de commande QEMU.\n\n"
        "Le port série de l'invité est redirigé vers un fichier dans le\n"
        "dossier de la VM. Le BIOS/OVMF, le chargeur d'amorçage et le\n"
        "noyau y écrivent généralement leur progression : c'est le moyen\n"
        "le plus direct de voir pourquoi une VM reste sur écran noir ou redémarre.\n\n"
        "Le fichier est ÉCRASÉ à chaque démarrage : seule la dernière\n"
        "session est conservée. Il peut être ouvert avec '📂 Dossier' dans l'onglet\n"
        "Aperçu.",
    "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña "
    "<b>Dispositivos</b> de la parte superior de la ventana.":
        "Pour passer du matériel physique (PCI/USB) à cette VM, utilisez l'onglet "
        "<b>Périphériques</b> en haut de la fenêtre.",

    # ================================================================
    # Almacenamiento: tooltips avanzados
    # ================================================================
    "Compacta un disco QCOW2 de la VM seleccionada.\n\n"
    "Reduce el archivo físico en el host eliminando bloques no\n"
    "usados (equivalente a 'qemu-img convert -c'). NO cambia el\n"
    "tamaño virtual que ve el sistema invitado.\n\n"
    "Se pedirá confirmación y se recomienda hacer un backup antes\n"
    "de proceder. Requiere que la VM esté apagada.":
        "Compacte un disque QCOW2 de la VM sélectionnée.\n\n"
        "Réduit le fichier physique sur l'hôte en supprimant les blocs non\n"
        "utilisés (équivalent à 'qemu-img convert -c'). NE change PAS la\n"
        "taille virtuelle que voit le système invité.\n\n"
        "Une confirmation sera demandée et une sauvegarde est recommandée avant\n"
        "de procéder. Nécessite que la VM soit éteinte.",

    # ================================================================
    # Compartición: tooltips avanzados
    # ================================================================
    "Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).":
        "Intégration Hôte ↔ Invité. Les dossiers partagés et le presse-papiers sont configurés ici.",
    "Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.":
        "Partage des répertoires de l'hôte avec l'invité. Automatique utilise VirtioFS sous Linux quand virtiofsd est disponible, 9p en secours et SMB pour Windows/macOS. Lecture seule empêche l'invité de modifier les fichiers de l'hôte.",
    "Dependencias del host": "Dépendances de l'hôte",
    "VirtioFS: SIN COMPROBAR": "VirtioFS : NON VÉRIFIÉ",
    "9p: SIN COMPROBAR": "9p : NON VÉRIFIÉ",
    "SMB: SIN COMPROBAR": "SMB : NON VÉRIFIÉ",
    "9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.":
        "9p fait partie de QEMU et ne nécessite généralement pas de paquet supplémentaire sur l'hôte. VirtioFS a besoin de virtiofsd et SMB de Samba/smbd.",
    "\U0001f6e0\ufe0f Instalar faltantes": "\U0001f6e0\ufe0f Installer les manquants",
    "Guest / etiqueta": "Invité / étiquette",
    "Montaje en el guest": "Montage dans l'invité",
    "➕ Agregar": "➕ Ajouter",
    "\U0001f4be Guardar": "\U0001f4be Enregistrer",
    "Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.":
        "Guest Tools rassemble l'intégration du système invité : QEMU Guest Agent, pilotes VirtIO et, sous Windows, composants SPICE. L'ISO peut être montée comme CD/DVD sur n'importe quelle VM.",
    "Activar canal QEMU Guest Agent al iniciar la VM":
        "Activer le canal QEMU Guest Agent au démarrage de la VM",
    "\U0001f50e Probar conexión": "\U0001f50e Tester la connexion",
    "\U0001f4bf Crear / actualizar ISO Guest Tools":
        "\U0001f4bf Créer / mettre à jour l'ISO Guest Tools",
    "\U0001f9f0 Adjuntar a esta VM": "\U0001f9f0 Attacher à cette VM",
    "Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.":
        "Crée l'ISO si elle manque et l'attache comme CD/DVD à la VM sélectionnée, en une seule étape.",
    "\U0001f4c2 Abrir carpeta de Guest Tools":
        "\U0001f4c2 Ouvrir le dossier Guest Tools",
    "Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.":
        "Linux : installez qemu-guest-agent depuis cette ISO ou depuis le gestionnaire de paquets. Windows : INSTALL-WINDOWS.CMD télécharge et installe VirtIO Guest Tools et SPICE Guest Tools depuis leurs sources officielles. Redémarrez ensuite l'invité.",
    "Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.":
        "Linux et Windows : QEMU vdagent + canal VirtIO/SPICE et GTK seront utilisés pour le presse-papiers bidirectionnel. L'invité doit avoir spice-vdagent (Linux) ou SPICE Guest Tools (Windows). macOS sera testé dans une phase spécifique.",
    "\U0001f4be Guardar configuración": "\U0001f4be Enregistrer la configuration",
    "Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.":
        "Configuration par VM. Le mécanisme concret sera choisi selon l'OS invité et son support d'intégration.",

    # ================================================================
    # Passthrough: tooltips avanzados
    # ================================================================
    "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.":
        "Passthrough de matériel physique. PCI utilise VFIO ; USB utilise usb-host sur XHCI. Le programme vérifie l'accès à /dev/bus/usb, démonte automatiquement le stockage USB sélectionné de l'hôte et demande les permissions administratives uniquement quand c'est nécessaire. Ne sélectionnez pas les Root Hubs.",
    "Diagnóstico PCI / VFIO": "Diagnostic PCI / VFIO",
    "Comprobando Intel VT-d / IOMMU...": "Vérification d'Intel VT-d / IOMMU…",
    "\U0001f504 Comprobar IOMMU / VFIO": "\U0001f504 Vérifier IOMMU / VFIO",
    "\u2139 Ver diagnóstico detallado": "\u2139 Voir le diagnostic détaillé",
    "\U0001f6e0 Preparar intel_iommu=on":
        "\U0001f6e0 Préparer intel_iommu=on",
    "\u2699 Abrir UEFI/BIOS": "\u2699 Ouvrir UEFI/BIOS",
    "Permisos USB del host": "Permissions USB de l'hôte",
    "Para poder pasar memorias o discos USB a la VM sin pedir contraseña cada vez, el sistema necesita una regla udev que conceda acceso al usuario activo. Puedes instalarla aquí con un clic; solo se aplica a esta categoría de dispositivos.":
        "Pour pouvoir passer des clés ou disques USB à la VM sans demander le mot de passe à chaque fois, le système a besoin d'une règle udev qui accorde l'accès à l'utilisateur actif. Vous pouvez l'installer ici en un clic ; elle ne s'applique qu'à cette catégorie de périphériques.",
    "\U0001f504 Comprobar": "\U0001f504 Vérifier",
    "\U0001f527 Configurar permisos USB":
        "\U0001f527 Configurer les permissions USB",
    "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\n"
    "que permite el acceso a los dispositivos USB al usuario activo.\n"
    "Solo se toca este archivo; el resto de la configuración USB\n"
    "del sistema no se modifica.":
        "Crée /etc/udev/rules.d/50-vm-manager-usb.rules avec la règle\n"
        "qui accorde l'accès aux périphériques USB à l'utilisateur actif.\n"
        "Seul ce fichier est modifié ; le reste de la configuration USB\n"
        "du système reste intact.",
    "Usar": "Utiliser",
    "IOMMU / Driver": "IOMMU / Pilote",
    "\U0001f504 Detectar dispositivos":
        "\U0001f504 Détecter les périphériques",
    "\U0001f4be Guardar selección":
        "\U0001f4be Enregistrer la sélection",
    "\U0001f50c Conectar USB en caliente":
        "\U0001f50c Connecter USB à chaud",
    "\u23cf Desconectar USB": "\u23cf Déconnecter USB",

    # ================================================================
    # Configuracion Host: subtitulo
    # ================================================================
    "Ajustes y diagnostico del sistema anfitrion. Nada de esta seccion se guarda con la VM: aplica a todo el equipo.":
        "Paramètres et diagnostic du système hôte. Rien de cette section n'est enregistré avec la VM : cela s'applique à toute la machine.",

    # ================================================================
    # Backups: cabecera de la pestana
    # ================================================================
    "<b>Backups de la maquina virtual</b><br><span style='color:#666;font-size:11px;'>Copia periodica de la carpeta completa (discos + config + snapshots). El backup se guarda como carpeta independiente; se puede restaurar con el boton <b>Importar</b> de la pestana Resumen apuntando a la carpeta del backup.</span>":
        "<b>Sauvegardes de la machine virtuelle</b><br><span style='color:#666;font-size:11px;'>Copie périodique du dossier complet (disques + config + instantanés). La sauvegarde est enregistrée comme dossier indépendant ; elle peut être restaurée avec le bouton <b>Importer</b> de l'onglet Aperçu en pointant vers le dossier de sauvegarde.</span>",

    # ================================================================
    # Consola Grafica: tooltips avanzados
    # ================================================================
    "\u2197 Abrir en ventana externa": "\u2197 Ouvrir dans une fenêtre externe",
    "Lanza el visor externo del protocolo configurado en Pantalla,\n"
    "aunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez.":
        "Lance la visionneuse externe du protocole configuré dans Affichage,\n"
        "même si le mode est 'intégré'. Utile pour avoir les deux vues en même temps.",
    "Externos en pantalla completa": "Visonneuses externes en plein écran",
    "Cuando está marcado, los visores externos (los que abre el\n"
    "botón 'Abrir en ventana externa' o el modo 'Ventana externa'\n"
    "de Configuración → Pantalla) se lanzan ocupando toda la\n"
    "pantalla. NO afecta al visor embebido (VNC dentro de la app):\n"
    "para ese, usa el botón 'Pantalla completa del visor'.":
        "Si coché, les visionneuses externes (celles ouvertes par le\n"
        "bouton 'Ouvrir dans une fenêtre externe' ou le mode 'Fenêtre externe'\n"
        "de Configuration → Affichage) se lancent en plein écran.\n"
        "Cela N'affecte PAS la visionneuse intégrée (VNC dans l'app) :\n"
        "pour celle-ci, utilisez le bouton 'Plein écran de la visionneuse'.",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Mismo menú que el botón 'Medios' de la pestaña Resumen.\n"
    "Atajo: Ctrl+M.":
        "Médias de la VM : lecteurs CD/DVD et périphériques USB.\n"
        "Même menu que le bouton 'Médias' de l'onglet Aperçu.\n"
        "Raccourci : Ctrl+M.",
    "\U0001f504 Reconectar": "\U0001f504 Reconnecter",
    "Reconectar el widget VNC.\n"
    "Útil si cambiaste la resolución del guest y la imagen\n"
    "quedó recortada o mal escalada. El cliente VNC básico\n"
    "no puede cambiar el tamaño de su framebuffer sin\n"
    "reconectar.\n\n"
    "Atajo: Ctrl+R.":
        "Reconnecter le widget VNC.\n"
        "Utile si vous avez changé la résolution de l'invité et que l'image\n"
        "s'est retrouvée recadrée ou mal mise à l'échelle. Le client VNC basique\n"
        "ne peut pas redimensionner son framebuffer sans\n"
        "se reconnecter.\n\n"
        "Raccourci : Ctrl+R.",
    "\U0001f50d−": "\U0001f50d−",
    "Reducir el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Réduire le zoom de la visionneuse intégrée.\n"
        "Paliers : 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "Ajustado": "Ajusté",
    "\U0001f50d+": "\U0001f50d+",
    "Aumentar el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Augmenter le zoom de la visionneuse intégrée.\n"
        "Paliers : 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "\u229e Ajustar": "\u229e Ajuster",
    "Ajustar la imagen de la VM al tamaño del widget (escala\n"
    "automática). La VM se ve entera, sin barras de scroll.\n"
    "Si la relación de aspecto no coincide, aparecen bandas\n"
    "negras a los lados.":
        "Ajuster l'image de la VM à la taille du widget (mise à\n"
        "l'échelle automatique). La VM est entièrement visible, sans barres de défilement.\n"
        "Si le rapport d'aspect ne correspond pas, des bandes\n"
        "noires apparaissent sur les côtés.",
    "1:1 Tamaño real": "1:1 Taille réelle",
    "Mostrar la imagen de la VM a su resolución real (100%).\n"
    "Si no cabe en la ventana, aparecen barras de scroll.":
        "Afficher l'image de la VM à sa résolution réelle (100 %).\n"
        "Si elle ne rentre pas dans la fenêtre, des barres de défilement apparaissent.",
    "\U0001f3ac Presentación": "\U0001f3ac Présentation",
    "Modo presentación: oculta los paneles laterales, entra\n"
    "en pantalla completa y salta a la Consola Gráfica.\n"
    "Requiere que la VM esté encendida.\n\n"
    "Atajo: F11. Para salir: F11 o Escape.":
        "Mode présentation : cache les panneaux latéraux, passe\n"
        "en plein écran et saute à la Console graphique.\n"
        "Nécessite que la VM soit allumée.\n\n"
        "Raccourci : F11. Pour quitter : F11 ou Échap.",
    "\u26f6 Pantalla completa del visor": "\u26f6 Plein écran de la visionneuse",
    "Salir con:": "Quitter avec :",
    "Ctrl derecho (como VirtualBox)": "Ctrl droit (comme VirtualBox)",
    "Ctrl+Alt+Intro": "Ctrl+Alt+Entrée",
    "Combinación de teclas para salir de la pantalla completa del visor embebido.\n"
    "Evita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\n"
    "usar Escape o F11 dentro del sistema invitado, no la uses aquí).":
        "Combinaison de touches pour quitter le plein écran de la visionneuse intégrée.\n"
        "Évitez de choisir une touche que vous devez envoyer dans la VM (p. ex. si vous\n"
        "utilisez Échap ou F11 dans le système invité, ne l'utilisez pas ici).",
    "<b>\u2139\ufe0f Notas sobre Android en QEMU/KVM</b>":
        "<b>\u2139\ufe0f Notes sur Android sur QEMU/KVM</b>",

    # ================================================================
    # Consola de Progreso: tooltips avanzados
    # ================================================================
    "\U0001fa7a Salud de la VM": "\U0001fa7a Santé de la VM",
    "Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.":
        "Vérifie en un coup d'œil si la VM est réellement en cours d'exécution, si le Guest Agent répond et si les dossiers partagés ont été montés.",
    "\U0001f6a6 Semáforos": "\U0001f6a6 Feux de signalisation",
    "\U0001f9f9 Limpiar procesos huérfanos":
        "\U0001f9f9 Nettoyer les processus orphelins",
    "Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.":
        "Cherche les processus QEMU/virtiofsd/swtpm restés suspendus d'une session précédente (à cause d'une fermeture forcée) et propose de les arrêter.",
    "Nivel:": "Niveau :",
    "Todo": "Tout",
    "Avisos+": "Avertissements+",
    "Errores": "Erreurs",
    "\U0001f50d Filtrar...": "\U0001f50d Filtrer…",
    "\U0001f4c4 Ver log completo": "\U0001f4c4 Voir le journal complet",
    "Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.":
        "Affiche l'historique complet enregistré sur disque pour cette VM (launch.log), pas seulement ce qui tient dans cette fenêtre.",
    "\U0001f4be Exportar log": "\U0001f4be Exporter le journal",
    "Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.":
        "Enregistre le journal complet de cette VM dans un fichier, utile pour demander de l'aide ou signaler un problème.",
    "Limpiar consola": "Effacer la console",
    "Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').":
        "Efface les messages affichés ici (l'historique complet sur disque reste intact ; utilisez 'Voir le journal complet').",

    # ================================================================
    # Panel derecho: valores dinamicos avanzados
    # ================================================================
    "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n"
    "100% = el proceso usa el equivalente a todos los hilos del host.\n"
    "Si el host tiene 8 hilos y QEMU usa 4, verás 50%.":
        "Utilisation CPU du processus QEMU sur l'hôte, attribuée à cette VM.\n"
        "100 % = le processus utilise l'équivalent de tous les threads de l'hôte.\n"
        "Si l'hôte a 8 threads et QEMU en utilise 4, vous verrez 50 %.",
    "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\n"
    "realmente en el sistema anfitrión), como porcentaje de la RAM\n"
    "total del host. No es la RAM que 've' el sistema invitado.":
        "Mémoire RSS du processus QEMU sur l'hôte (ce que QEMU occupe\n"
        "réellement dans le système hôte), en pourcentage de la RAM\n"
        "totale de l'hôte. Ce n'est pas la RAM que 'voit' le système invité.",
    "I/O de disco generado por el proceso QEMU para esta VM, según\n"
    "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
    "Es el tráfico real a los archivos de disco de la VM en el host.":
        "I/O disque généré par le processus QEMU pour cette VM, d'après\n"
        "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
        "C'est le trafic réel vers les fichiers de disque de la VM sur l'hôte.",
    "Tráfico de red de esta VM.\n"
    "• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n"
    "  asociada en el host (exacto).\n"
    "• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n"
    "  el host, así que no se puede medir sin Guest Agent.\n"
    "  El gráfico mostrará 'NAT (sin medida)'.":
        "Trafic réseau de cette VM.\n"
        "• Mode TAP/Bridge : les compteurs réels de l'interface associée\n"
        "  sur l'hôte sont lus (exact).\n"
        "• Mode NAT : QEMU utilise une pile interne sans interface visible\n"
        "  sur l'hôte, donc la mesure est impossible sans Guest Agent.\n"
        "  Le graphique affichera 'NAT (non mesuré)'.",
    "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\n"
    "Cuando está activo, el clipboard bidireccional y la\n"
    "resolución automática funcionan.":
        "Détection de spice-vdagent dans l'invité via QEMU Guest Agent.\n"
        "Lorsqu'actif, le presse-papiers bidirectionnel et la\n"
        "résolution automatique fonctionnent.",
    "Uso de CPU del proceso QEMU expresado como porcentaje del total\n"
    "de hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\n"
    "valor mostrado es 50%.":
        "Utilisation CPU du processus QEMU exprimée en pourcentage du total\n"
        "des threads de l'hôte. Si l'hôte a 8 threads et QEMU en utilise 4, la\n"
        "valeur affichée est 50 %.",
    "Memoria RAM libre del host, respecto al total.":
        "RAM libre de l'hôte, par rapport au total.",
    "Tamaño del archivo de disco principal de la VM y su tamaño\n"
    "virtual (lo que ve el sistema invitado).":
        "Taille du fichier de disque principal de la VM et sa taille\n"
        "virtuelle (ce que voit le système invité).",
    "Número de snapshots registrados y antigüedad del último.":
        "Nombre d'instantanés enregistrés et âge du dernier.",
    "Restaura el snapshot más reciente de esta VM.\n"
    "Si la VM está corriendo, se restaura en caliente (snapshot-load).\n"
    "Si está apagada, se restauran los discos QCOW2 internos.":
        "Restaure l'instantané le plus récent de cette VM.\n"
        "Si la VM est en cours d'exécution, la restauration est à chaud (snapshot-load).\n"
        "Si elle est éteinte, les disques QCOW2 internes sont restaurés.",
    "Sin VM seleccionada": "Aucune VM sélectionnée",
    "\u21a9 Restaurar este snapshot": "\u21a9 Restaurer cet instantané",

    # ================================================================
    # VM control: errores y avisos avanzados
    # ================================================================
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Mettre la VM en pause. Utilisez la flèche pour plus d'options :\n"
        "• Pause (rapide) : arrête sans enregistrer l'état sur disque.\n"
        "• Reprendre : relance la VM en pause.\n"
        "• Prendre un instantané : enregistre l'état sur disque et met en pause.",
    "Reanudar la VM pausada. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Reprend la VM en pause. Utilisez la flèche pour plus d'options :\n"
        "• Pause (rapide) : arrête sans enregistrer l'état sur disque.\n"
        "• Reprendre : relance la VM.\n"
        "• Prendre un instantané : enregistre l'état sur disque et met en pause.",
    "No se pudo cambiar el estado de la VM.\n\n{0}":
        "Impossible de changer l'état de la VM.\n\n{0}",
    "No se pudo pausar la VM.\n\n{0}":
        "Impossible de mettre la VM en pause.\n\n{0}",
    "No se pudo reanudar la VM.\n\n{0}":
        "Impossible de reprendre la VM.\n\n{0}",
    "No se pudo enviar la orden de reinicio.\n\n{0}":
        "Impossible d'envoyer la commande de redémarrage.\n\n{0}",
    "Esto corta la VM de inmediato, sin avisar al sistema operativo invitado (como desenchufar un equipo real).\n\n"
    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
    "¿Deseas continuar?":
        "Cela coupe la VM immédiatement, sans avertir le système d'exploitation invité (comme débrancher une machine réelle).\n\n"
        "Peut entraîner une perte de données non enregistrées dans la VM.\n\n"
        "Voulez-vous continuer ?",
    "Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin avisar al sistema operativo invitado.\n\n"
    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
    "¿Deseas continuar?":
        "Cela coupe la VM immédiatement et la redémarre à zéro, sans avertir le système d'exploitation invité.\n\n"
        "Peut entraîner une perte de données non enregistrées dans la VM.\n\n"
        "Voulez-vous continuer ?",

    # ================================================================
    # Avisos de SO y firmware
    # ================================================================
    "⚠️ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.":
        "⚠️ Android-x86 9.0 (noyau 4.9) n'inclut pas le pilote VirtIO-GPU et tombe sur un shell de secours avec 'Detecting Android-x86…'. Utilisez 'Automatique' ou 'Red Hat QXL 2D'. Les ISOs avec noyau 5.10+ ou Bliss OS 15+ supportent VirtIO-GPU.",

    # ================================================================
    # Cuadros de dialogo de la app (VM lifecycle integrados)
    # ================================================================
    "Grupo y color para <b>{0}</b>. El grupo es texto libre: escribe uno nuevo para crearlo. El color se aplica como fondo suave del ítem en la lista lateral.":
        "Groupe et couleur pour <b>{0}</b>. Le groupe est du texte libre : tapez-en un nouveau pour le créer. La couleur est appliquée comme arrière-plan doux de l'élément dans la liste latérale.",
    "La VM '{0}' todavia no se ha arrancado.\n\nEl comando QEMU se genera al pulsar Iniciar; vuelve a intentarlo despues del primer arranque.":
        "La VM '{0}' n'a pas encore été démarrée.\n\nLa commande QEMU est générée lorsque vous cliquez sur Démarrer ; réessayez après le premier démarrage.",
    "No se pudo leer run_temp.sh.\n\n{0}":
        "Impossible de lire run_temp.sh.\n\n{0}",
    "Comando QEMU - {0}": "Commande QEMU - {0}",
    "Contenido de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este es el comando exacto con el que QEMU esta ejecutando (o ejecuto por ultima vez) la VM.":
        "Contenu de <code>run_temp.sh</code> pour <b>{0}</b>.<br>C'est la commande exacte avec laquelle QEMU exécute (ou a exécuté pour la dernière fois) la VM.",
    "Copiar al portapapeles": "Copier dans le presse-papiers",
    "Abrir carpeta de la VM": "Ouvrir le dossier de la VM",
    "Abre la carpeta que contiene run_temp.sh, launch.log y los discos.":
        "Ouvre le dossier contenant run_temp.sh, launch.log et les disques.",
    "Notas de la VM": "Notes de la VM",
    "Notas - {0}": "Notes - {0}",
    "Notas libres sobre <b>{0}</b>. Se guardan en <code>vm_config.ini</code> como <code>extra.notes</code> y aparecen como aviso amarillo en la pestana Resumen.":
        "Notes libres sur <b>{0}</b>. Elles sont enregistrées dans <code>vm_config.ini</code> comme <code>extra.notes</code> et apparaissent comme un avertissement jaune dans l'onglet Aperçu.",
    "Ej.: instalado con VirtIO, probar snapshots tras actualizar los drivers; puerto 8080 redirigido al 80 del guest...":
        "Ex. : installé avec VirtIO, tester les instantanés après mise à jour des pilotes ; port 8080 redirigé vers le 80 de l'invité…",
    "Borrar notas": "Effacer les notes",
    "No se pudieron guardar las notas.\n\n{0}":
        "Impossible d'enregistrer les notes.\n\n{0}",
    "Carpeta": "Dossier",
    "Carpeta de la VM": "Dossier de la VM",
    "No se pudo abrir la carpeta.\n\n{0}\n\n{1}":
        "Impossible d'ouvrir le dossier.\n\n{0}\n\n{1}",
    "Resumen de la máquina virtual": "Résumé de la machine virtuelle",

    # --- i18n_fr_tanda2b_v1 ---
}
