# -*- coding: utf-8 -*-
"""Traducciones al frances — Virtual.Machine.

Marcador: i18n_fr_tanda1_v1.

Tanda 1: cadenas mas visibles (pestanas, resumen, panel izquierdo,
config VM basica, config Host basica, botones y dialogos comunes).
Las cadenas ausentes se muestran en espanol (idioma fuente) y se
completaran en la tanda 2.
"""

TRANSLATIONS = {

    # ================================================================
    # i18n_v1: pestanas principales, titulo y dialogo de reinicio
    # ================================================================
    "Resumen": "Aperçu",
    "Configuración VM": "Configuration VM",
    "Configuración Host": "Configuration Hôte",
    "Snapshots": "Instantanés",
    "\U0001f4be Backups": "\U0001f4be Sauvegardes",
    "\U0001f4da Medios": "\U0001f4da Médias",
    "\U0001f5a5\ufe0f Consola Gráfica": "\U0001f5a5\ufe0f Console graphique",
    "\U0001f4cb Consola de Progreso": "\U0001f4cb Console de progression",
    "\u2753 Ayuda": "\u2753 Aide",
    "Administrador QEMU/KVM": "Gestionnaire QEMU/KVM",
    "Cambio de idioma": "Changement de langue",
    "Se ha cambiado el idioma a {0}.\n\n"
    "Para que TODA la aplicación use el idioma nuevo\n"
    "es necesario reiniciar.\n\n"
    "¿Quieres reiniciar ahora?":
        "La langue a été changée en {0}.\n\n"
        "Pour que TOUTE l'application utilise la nouvelle langue,\n"
        "un redémarrage est nécessaire.\n\n"
        "Voulez-vous redémarrer maintenant ?",

    # ================================================================
    # Botones y etiquetas comunes
    # ================================================================
    "Cancelar": "Annuler",
    "Aceptar": "OK",
    "Crear": "Créer",
    "Elegir": "Choisir",
    "Guardar": "Enregistrer",
    "Aplicar": "Appliquer",
    "Cerrar": "Fermer",
    "Sí": "Oui",
    "No": "Non",
    "OK": "OK",
    "Nombre:": "Nom :",
    "Tamaño:": "Taille :",
    "Tipo:": "Type :",
    "Formato:": "Format :",
    "Archivo:": "Fichier :",
    "Medio:": "Support :",
    "Origen:": "Origine :",
    "Tamaño": "Taille",
    "Nombre": "Nom",
    "Tipo": "Type",
    "Estado": "État",
    "Estado:": "État :",
    "Versión": "Version",
    "Version": "Version",
    "Formato": "Format",
    "Ruta": "Chemin",
    "Fecha": "Date",

    # ================================================================
    # Panel izquierdo + toolbar de Resumen
    # ================================================================
    "<b>MÁQUINAS VIRTUALES</b>": "<b>MACHINES VIRTUELLES</b>",
    "\U0001f50d Buscar máquinas...": "\U0001f50d Rechercher des machines…",
    "Ordenar: Nombre (A-Z)": "Trier : Nom (A-Z)",
    "Ordenar: Estado": "Trier : État",
    "Ordenar: Ultima vez usada": "Trier : Dernière utilisation",
    "Todos los grupos": "Tous les groupes",
    "➕ Nueva VM": "➕ Nouvelle VM",
    "Selecciona una máquina virtual": "Sélectionnez une machine virtuelle",
    "● Sin VM seleccionada": "● Aucune VM sélectionnée",
    "▶ Iniciar": "▶ Démarrer",
    "⏸ Pausar": "⏸ Mettre en pause",
    "⏹ Apagar": "⏹ Éteindre",
    "⏹ Apagado (ACPI)": "⏹ Arrêt (ACPI)",
    "⏻ Forzar apagado": "⏻ Arrêt forcé",
    "⟳ Reiniciar": "⟳ Redémarrer",
    "⟲ Forzar reinicio": "⟲ Redémarrage forcé",
    "⏸ Pausar (rápido)": "⏸ Mettre en pause (rapide)",
    "▶ Reanudar": "▶ Reprendre",
    "\U0001f4f8 Tomar Snapshot": "\U0001f4f8 Prendre un instantané",
    "Iniciar VM": "Démarrer la VM",
    "Pausar/Reanudar VM": "Pause/Reprendre la VM",
    "Nueva máquina virtual": "Nouvelle machine virtuelle",
    "● Nueva VM": "● Nouvelle VM",
    "\U0001f4bf Medios": "\U0001f4bf Médias",
    "\U0001f9ec Clonar": "\U0001f9ec Cloner",
    "Crea una copia completa de esta VM en una carpeta nueva.":
        "Crée une copie complète de cette VM dans un nouveau dossier.",
    "\U0001f9ec Desenlazar": "\U0001f9ec Détacher",
    "⇩ Importar": "⇩ Importer",
    "⇪ Exportar": "⇪ Exporter",
    "\U0001f4be Plantilla": "\U0001f4be Modèle",
    "\U0001f4dc Comando QEMU": "\U0001f4dc Commande QEMU",
    "\U0001f4dd Notas": "\U0001f4dd Notes",
    "\U0001f3f7 Etiqueta": "\U0001f3f7 Étiquette",
    "⚖ Comparar con defaults": "⚖ Comparer aux valeurs par défaut",
    "\U0001f5d1\ufe0f Eliminar": "\U0001f5d1\ufe0f Supprimer",
    "\U0001f5d1 Eliminar": "\U0001f5d1 Supprimer",
    "Elimina esta VM (con opción de conservar los discos).":
        "Supprime cette VM (avec option pour conserver les disques).",
    "Resumen de Configuración": "Résumé de la configuration",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Sélectionnez une machine virtuelle dans la liste de gauche.",
    "\u2139\ufe0f Información general": "\u2139\ufe0f Informations générales",
    "\U0001f5bc\ufe0f Último snapshot": "\U0001f5bc\ufe0f Dernier instantané",
    "Sin VM seleccionada": "Aucune VM sélectionnée",

    # --- Info general del panel derecho ---
    "Tiempo activo:": "Temps de fonctionnement :",
    "Procesos:": "Processus :",
    "Dirección IP:": "Adresse IP :",
    "Dirección MAC:": "Adresse MAC :",
    "Guest Agent:": "Guest Agent :",
    "Carpetas:": "Dossiers :",
    "Clipboard:": "Presse-papiers :",
    "spice-vdagent:": "spice-vdagent :",
    "PID QEMU:": "PID QEMU :",
    "CPU (VM):": "CPU (VM) :",
    "RAM host:": "RAM hôte :",
    "Disco:": "Disque :",
    "Snapshots:": "Instantanés :",
    "\U0001f4ca Uso de recursos": "\U0001f4ca Utilisation des ressources",
    "CPU (VM)": "CPU (VM)",
    "RAM (QEMU)": "RAM (QEMU)",
    "Disco (VM)": "Disque (VM)",
    "Red (VM)": "Réseau (VM)",
    "\U0001f4cc Fijar": "\U0001f4cc Épingler",
    "Fija este panel como columna derecha de la ventana, siempre visible.\nÚtil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\nVuelve a pulsar para devolverlo a Resumen.":
        "Épingle ce panneau comme colonne de droite, toujours visible.\nUtile pour surveiller le CPU/RAM en travaillant sur un autre onglet.\nAppuyez à nouveau pour le renvoyer à l'Aperçu.",

    # ================================================================
    # Tanda 2d-1: Sistema + Procesador + Memoria
    # ================================================================
    "Sistema": "Système",
    "Plataforma, firmware y opciones de bajo nivel del hardware virtual.":
        "Plateforme, firmware et options bas niveau du matériel virtuel.",
    "<b>Firmware</b>": "<b>Firmware</b>",
    "BIOS (tradicional)": "BIOS (traditionnel)",
    "UEFI (OVMF)": "UEFI (OVMF)",
    "<b>Chipset</b>": "<b>Chipset</b>",
    "i440FX (clásico)": "i440FX (classique)",
    "Q35 (moderno, PCIe)": "Q35 (moderne, PCIe)",
    "<b>Seguridad</b>": "<b>Sécurité</b>",
    "Secure Boot": "Secure Boot",
    "TPM 2.0": "TPM 2.0",
    "<b>Perfiles del sistema</b>": "<b>Profils système</b>",
    "Configuración optimizada para el sistema operativo seleccionado. Puede modificar los valores según sus necesidades.":
        "Configuration optimisée pour le système d'exploitation sélectionné. Vous pouvez modifier les valeurs selon vos besoins.",
    "<b>Opciones avanzadas</b>": "<b>Options avancées</b>",
    "Habilitar ACPI": "Activer ACPI",
    "Habilitar APIC": "Activer APIC",
    "Habilitar IOMMU": "Activer IOMMU",
    "PCIe Root Port": "PCIe Root Port",
    "Arrancar esta VM al abrir la aplicación":
        "Démarrer cette VM à l'ouverture de l'application",
    "Modo compatibilidad de snapshots (fuerza hardware snapshoteable)":
        "Mode compatibilité des instantanés (force un matériel compatible)",
    "Procesador": "Processeur",
    "Modelo de CPU y número de núcleos asignados a la máquina virtual.":
        "Modèle de CPU et nombre de cœurs assignés à la machine virtuelle.",
    "<b>Tipo de procesador</b>": "<b>Type de processeur</b>",
    "Automático (recomendado)": "Automatique (recommandé)",
    "Host (máximo rendimiento)": "Hôte (performance maximale)",
    "QEMU x86-64 (compatibilidad)": "QEMU x86-64 (compatibilité)",
    "<b>Núcleos</b>": "<b>Cœurs</b>",
    "{0} núcleos": "{0} cœurs",
    "Memoria": "Mémoire",
    "Cantidad de memoria RAM asignada a la máquina virtual.":
        "Quantité de RAM assignée à la machine virtuelle.",
    "<b>RAM asignada</b>": "<b>RAM allouée</b>",
    "RAM del host: {0} GB (libre: {1} GB)": "RAM hôte : {0} GB (libre : {1} GB)",
    "núcleos": "cœurs",

    # ================================================================
    # Tanda 2d-2: Pantalla + Consola remota
    # ================================================================
    "Pantalla": "Affichage",
    "Controlador gráfico virtual y memoria de video.":
        "Contrôleur graphique virtuel et mémoire vidéo.",
    "<b>Gráficos / GPU</b>": "<b>Graphiques / GPU</b>",
    "VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)":
        "VirtIO-GPU 2D (compatible • inst. disques ✓ • inst. complet ✗)",
    "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)":
        "VirtIO-GPU + VirGL 3D (OpenGL • instantanés ✗)",
    "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)":
        "VirtIO-GPU + Venus/Vulkan 3D (expérimental • instantanés ✗)",
    "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)":
        "Red Hat QXL 2D (3D ✗ • inst. complet ✓ • macOS ⚠)",
    "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)":
        "VMware SVGA II (3D accéléré ✗ • inst. complet ✓ • macOS ⚠)",
    "Sin video / Headless": "Sans vidéo / Headless",
    "<b>Memoria de video (VRAM)</b>": "<b>Mémoire vidéo (VRAM)</b>",
    "Host GPU: detectando…": "GPU hôte : détection…",
    "Consola remota": "Console distante",
    "VNC (compatible con cualquier gráfico)": "VNC (compatible avec tout graphique)",
    "SPICE (mejor rendimiento en local)": "SPICE (meilleure performance en local)",
    "Protocolo:": "Protocole :",
    "Embebida en la app": "Intégrée à l'application",
    "Ventana externa (visor del sistema)": "Fenêtre externe (visionneuse du système)",
    "Ventana nativa de QEMU": "Fenêtre native de QEMU",
    "Híbrida (VNC embebido + SPICE externo)":
        "Hybride (VNC intégré + SPICE externe)",
    "Modo:": "Mode :",
    "Log VNC detallado (DEBUG)": "Journal VNC détaillé (DEBUG)",
    "\U0001f5a5 Mostrar la VM dentro de la app (consola VNC embebida)":
        "\U0001f5a5 Afficher la VM dans l'application (console VNC intégrée)",
    "\U0001f5a5\ufe0f Mostrar la VM dentro de la app (consola VNC embebida)":
        "\U0001f5a5\ufe0f Afficher la VM dans l'application (console VNC intégrée)",

    # ================================================================
    # Tanda 2d-3a: Red + Dispositivos
    # ================================================================
    "Red": "Réseau",
    "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.":
        "Adaptateurs réseau virtuels. Chacun peut utiliser NAT, bridge ou TAP.",
    "Adaptadores": "Adaptateurs",
    "➕ Agregar adaptador": "➕ Ajouter un adaptateur",
    "✏ Editar": "✏ Modifier",
    "Sin red (ningún adaptador virtual)":
        "Pas de réseau (aucun adaptateur virtuel)",
    "NAT / Internet (recomendado)": "NAT / Internet (recommandé)",
    "Bridge existente": "Bridge existant",
    "TAP": "TAP",
    "VirtIO (recomendado)": "VirtIO (recommandé)",
    "Intel E1000": "Intel E1000",
    "Realtek RTL8139": "Realtek RTL8139",
    "VMware VMXNET3": "VMware VMXNET3",
    "Interfaz/Bridge:": "Interface/Bridge :",
    "Dispositivos": "Périphériques",
    "Audio y otros dispositivos integrados de la máquina virtual.":
        "Audio et autres périphériques intégrés de la machine virtuelle.",
    "<b>Audio</b>": "<b>Audio</b>",
    "Intel HDA (recomendado)": "Intel HDA (recommandé)",
    "AC97": "AC97",
    "Sound Blaster 16": "Sound Blaster 16",
    "Sin sonido": "Sans son",
    "<b>Dispositivo de señalización (ratón / teclado)</b>":
        "<b>Dispositif de pointage (souris / clavier)</b>",
    "USB Tablet (posición absoluta)": "USB Tablet (position absolue)",
    "USB Mouse (posición relativa)": "USB Mouse (position relative)",
    "USB Keyboard + Tablet": "Clavier USB + Tablet",
    "VirtIO Tablet (requiere drivers en el guest)":
        "VirtIO Tablet (nécessite des pilotes dans l'invité)",
    "PS/2 (clásico)": "PS/2 (classique)",
    "Ninguno": "Aucun",
    "Capturar el puerto serie a un archivo (serial.log)":
        "Capturer le port série dans un fichier (serial.log)",

    # ================================================================
    # Tanda 2d-3b: Almacenamiento
    # ================================================================
    "Almacenamiento": "Stockage",
    "Controladores y dispositivos": "Contrôleurs et périphériques",
    "Orden de arranque": "Ordre de démarrage",
    "Dispositivo": "Périphérique",
    "Tipo / archivo": "Type / fichier",
    "\U0001f4c0 CD / DVD": "\U0001f4c0 CD / DVD",
    "\U0001f4bd Disco Duro": "\U0001f4bd Disque dur",
    "\U0001f4be Disquete": "\U0001f4be Disquette",
    "✏ Modificar": "✏ Modifier",
    "\U0001f5dc Compactar": "\U0001f5dc Compacter",
    "⬆ Subir": "⬆ Monter",
    "⬇ Bajar": "⬇ Descendre",
    "\U0001f5d1 Quitar": "\U0001f5d1 Retirer",
    "Discos, unidades ópticas y orden de arranque de la máquina virtual.":
        "Disques, lecteurs optiques et ordre de démarrage de la machine virtuelle.",
    "CD/DVD": "CD/DVD",
    "Disco Duro": "Disque dur",
    "Disquete": "Disquette",
    "Disco duro": "Disque dur",
    "vacío": "vide",
    "Sin dispositivos": "Aucun périphérique",

    # ================================================================
    # Tanda 2e-1: sidebar Config VM
    # ================================================================
    "Passthrough": "Passthrough",
    "Compartición": "Partage",
    "Compartir Carpetas": "Partager des dossiers",
    "Guest Tools": "Guest Tools",
    "Clipboard": "Presse-papiers",
    "Host": "Hôte",
    "Método": "Méthode",
    "Acceso": "Accès",
    "Compartir clipboard": "Partager le presse-papiers",
    "Desactivado": "Désactivé",
    "Host → SO invitado": "Hôte → OS invité",
    "SO invitado → Host": "OS invité → Hôte",
    "Bidireccional": "Bidirectionnel",
    "Dirección:": "Sens :",
    "QEMU Guest Agent": "QEMU Guest Agent",
    "Acciones:": "Actions :",
    "Canal:": "Canal :",
    "Estado: no comprobado": "État : non vérifié",

    # ================================================================
    # Config Host: virtualizacion + apariencia + API
    # ================================================================
    "Estado del sistema de virtualización": "État du système de virtualisation",
    "Distribución: comprobando...": "Distribution : vérification…",
    "Gestor de paquetes: comprobando...": "Gestionnaire de paquets : vérification…",
    "\U0001f504 Comprobar dependencias": "\U0001f504 Vérifier les dépendances",
    "\U0001f6e0\ufe0f Comprobar/Reparar dependencias":
        "\U0001f6e0\ufe0f Vérifier/Réparer les dépendances",
    "Apariencia": "Apparence",
    "Sistema (predeterminado)": "Système (par défaut)",
    "Claro": "Clair",
    "Oscuro": "Sombre",
    "Tema:": "Thème :",
    "Atajos de teclado": "Raccourcis clavier",
    "Configurar atajos...": "Configurer les raccourcis…",
    "API REST local": "API REST locale",
    "Activar API REST local": "Activer l'API REST locale",
    "Puerto:": "Port :",
    "URL:": "URL :",
    "Token:": "Jeton :",
    "Copiar": "Copier",
    "Regenerar": "Régénérer",
    "Detenida": "Arrêtée",
    "Activa": "Active",

    # ================================================================
    # Dialogos comunes
    # ================================================================
    "Configurar dispositivo de almacenamiento":
        "Configurer le périphérique de stockage",
    "\U0001f4bd Disco SATA": "\U0001f4bd Disque SATA",
    "\u26a1 Disco NVMe": "\u26a1 Disque NVMe",
    "\U0001f4be Disquetera": "\U0001f4be Lecteur de disquette",
    "\U0001f4c0 Unidad CD / DVD": "\U0001f4c0 Lecteur CD / DVD",
    "Dispositivo de almacenamiento": "Périphérique de stockage",
    "Mantener vacío": "Laisser vide",
    "Usar ISO/IMG/DMG existente": "Utiliser une ISO/IMG/DMG existante",
    "System Recovery de macOS (descargar al iniciar)":
        "System Recovery de macOS (télécharger au démarrage)",
    "Descargar instalador de Windows automáticamente":
        "Télécharger automatiquement l'installateur Windows",
    "Descargar instalador de Linux automáticamente":
        "Télécharger automatiquement l'installateur Linux",
    "Fuente del medio:": "Source du support :",
    "Crear nuevo": "Créer",
    "Usar archivo existente": "Utiliser un fichier existant",
    "Expandible (dinámico)": "Extensible (dynamique)",
    "Fijo (preasignado)": "Fixe (préalloué)",
    "Selecciona una ISO / IMG / DMG…": "Sélectionnez une ISO / IMG / DMG…",
    "Ruta del archivo existente…": "Chemin du fichier existant…",
    "Ej.: 40G, 100G, 1T": "Ex. : 40G, 100G, 1T",
    "\U0001f4c1 Buscar…": "\U0001f4c1 Parcourir…",
    "\U0001f4da Biblioteca…": "\U0001f4da Bibliothèque…",
    "Medio inválido": "Support invalide",
    "Selecciona un ISO/IMG/DMG válido.":
        "Sélectionnez une ISO/IMG/DMG valide.",
    "Archivo inválido": "Fichier invalide",
    "Selecciona un archivo existente válido.":
        "Sélectionnez un fichier existant valide.",
    "Nombre requerido": "Nom requis",
    "Indica un nombre para el dispositivo.":
        "Indiquez un nom pour le périphérique.",
    "Escribe un nombre para el medio.":
        "Saisissez un nom pour le support.",
    "Tamaño inválido": "Taille invalide",
    "Usa un tamaño como 40G, 512M o 1T.":
        "Utilisez une taille comme 40G, 512M ou 1T.",
    "Nombre inválido": "Nom invalide",
    'El nombre no puede contener: \\ / : * ? " < > |':
        'Le nom ne peut pas contenir : \\ / : * ? " < > |',
    'El nombre no puede contener: \\ / : * ? " &lt; &gt; |':
        'Le nom ne peut pas contenir : \\ / : * ? " &lt; &gt; |',
    "Seleccionar archivo existente": "Sélectionner un fichier existant",
    "Seleccionar medio óptico": "Sélectionner un support optique",
    "Anadir a la biblioteca": "Ajouter à la bibliothèque",
    "El nombre no puede contener \\ / : * ? \" < > |":
        "Le nom ne peut pas contenir \\ / : * ? \" < > |",
    "Ej: disco_ubuntu_datos": "Ex. : disque_donnees_ubuntu",
    "Disco duro QCOW2 (recomendado)": "Disque dur QCOW2 (recommandé)",
    "Disco duro RAW": "Disque dur RAW",
    "Disquete IMG (RAW)": "Disquette IMG (RAW)",

    # --- Adaptador de red dialog ---
    "Adaptador de red virtual": "Adaptateur réseau virtuel",
    "Red 1": "Réseau 1",
    "NAT / Internet": "NAT / Internet",
    "Opcional: 52:54:00:xx:xx:xx": "Optionnel : 52:54:00:xx:xx:xx",
    "Modelo:": "Modèle :",
    "Backend:": "Backend :",
    "Bridge / TAP:": "Bridge / TAP :",
    "MAC:": "MAC :",
    "\U0001f500 Reglas NAT…": "\U0001f500 Règles NAT…",
    "\U0001f500 Reglas NAT… ({0})": "\U0001f500 Règles NAT… ({0})",

    # --- NAT port forwarding ---
    "Reglas de reenvío de puertos NAT": "Règles de transfert de ports NAT",
    "Puerto host:": "Port hôte :",
    "Puerto host": "Port hôte",
    "Puerto guest:": "Port invité :",
    "Puerto guest": "Port invité",
    "Protocolo:": "Protocole :",
    "Protocolo": "Protocole",
    "\u2795 Añadir regla": "\u2795 Ajouter une règle",
    "\U0001f5d1 Quitar seleccionada": "\U0001f5d1 Retirer la sélection",
    "Regla duplicada": "Règle en double",

    # --- Media picker dialog ---
    "Elegir medio de la biblioteca": "Choisir un support dans la bibliothèque",
    "Buscar...": "Rechercher…",
    "SO:": "OS :",
    "SO": "OS",
    "Todos": "Tous",
    "Todas": "Toutes",
    "Universal": "Universel",
    "Sin especificar": "Non spécifié",
    "Otro": "Autre",
    "Otros": "Autres",
    "Arq.": "Arch.",
    "Arq.:": "Arch. :",
    "ISO": "ISO",
    "Tamano": "Taille",
    "Usada por": "Utilisé par",
    "Anadir archivo a la biblioteca...":
        "Ajouter un fichier à la bibliothèque…",
    "Crear disco...": "Créer un disque…",
    "Abrir carpeta": "Ouvrir le dossier",
    "Biblioteca no disponible": "Bibliothèque non disponible",
    "La biblioteca de medios no está disponible.":
        "La bibliothèque de médias n'est pas disponible.",
    "Ya existe": "Existe déjà",
    "Crear medio": "Créer un support",
    "Medio creado": "Support créé",
    "Crear medio nuevo": "Créer un nouveau support",

    # --- Snapshots dialogos comunes ---
    "Sin captura de pantalla": "Aucune capture d'écran",
    "Sin capturas de snapshot": "Aucune capture d'instantané",
    "Organigrama": "Arborescence",
    "📋 Lista": "📋 Liste",
    "🌳 Organigrama": "🌳 Arborescence",
    "Vista:": "Vue :",
    "Zoom:": "Zoom :",
    "Tamaño virtual": "Taille virtuelle",
    "Tamaño archivo": "Taille du fichier",
    "Libre host": "Libre sur l'hôte",
    "Escritura": "Écriture",
    "Snapshot": "Instantané",
    "Sin operación de snapshot": "Aucune opération d'instantané",
    "ID": "ID",
    "Tamaño VM": "Taille VM",
    "Reloj VM": "Horloge VM",
    "\U0001f504 Actualizar": "\U0001f504 Actualiser",
    "➕ Crear": "➕ Créer",
    "↩ Restaurar": "↩ Restaurer",
    "✏ Cambiar nombre": "✏ Renommer",
    "Cambiar nombre": "Renommer",

    # --- task_progress ---
    "Iniciando…": "Démarrage…",
    "Completado.": "Terminé.",
    "Error:": "Erreur :",
    "La tarea falló.": "La tâche a échoué.",
    "Cancelando…": "Annulation…",
    "Cancelando, esperando al trabajador…":
        "Annulation, en attente du worker…",

    # --- shortcuts ---
    "Configurar atajos de teclado": "Configurer les raccourcis clavier",
    "Accion": "Action",
    "Atajo": "Raccourci",
    "Cambiar...": "Modifier…",
    "Restaurar todos por defecto": "Restaurer tous les défauts",
    "(sin atajo)": "(aucun raccourci)",
    "Conflicto de atajos": "Conflit de raccourcis",
    "Restaurar atajos": "Restaurer les raccourcis",
    "Pulsa la nueva combinacion": "Appuyez sur la nouvelle combinaison",

    # --- presentation / theme ---
    "Modo presentación": "Mode présentation",
    "\U0001f3ac Presentación": "\U0001f3ac Présentation",
    "\U0001f3ac Salir de presentación": "\U0001f3ac Quitter la présentation",
    "Cambio de tema": "Changement de thème",
    "Ventana completa": "Plein écran",

    # --- install flow / avisos generales ---
    "Advertencia": "Avertissement",
    "Error": "Erreur",
    "¿Deseas continuar de todos modos ?":
        "Voulez-vous continuer quand même ?",
    "¿Deseas continuar de todos modos?": "Voulez-vous continuer quand même ?",
    "Revisión previa": "Vérification préalable",
    "Configuración incompatible": "Configuration incompatible",
    "Secure Boot requiere UEFI (OVMF).": "Secure Boot nécessite UEFI (OVMF).",
    "Dependencias faltantes": "Dépendances manquantes",
    "La VM ya está corriendo": "La VM est déjà en cours d'exécution",
    "No se puede iniciar la VM": "Impossible de démarrer la VM",
    "Máquina virtual iniciada.": "Machine virtuelle démarrée.",
    "Descarga cancelada por el usuario.": "Téléchargement annulé par l'utilisateur.",
    "Iniciando descarga…": "Démarrage du téléchargement…",
    "Recovery preparado.": "Recovery prêt.",

    # --- health dashboard ---
    "Salud de la máquina virtual": "Santé de la machine virtuelle",
    "Comprobando…": "Vérification…",
    "\U0001f504 Refrescar ahora": "\U0001f504 Actualiser maintenant",
    "Sin VM seleccionada.": "Aucune VM sélectionnée.",
    "La VM no está corriendo.": "La VM n'est pas en cours d'exécution.",
    "\U0001f310 Red de la VM": "\U0001f310 Réseau de la VM",
    "\U0001f5a5\ufe0f Internet del host": "\U0001f5a5\ufe0f Internet de l'hôte",
    "\U0001f50a Audio": "\U0001f50a Audio",
    "\U0001f5bc\ufe0f Pantalla": "\U0001f5bc\ufe0f Affichage",
    "\U0001f50c Guest Agent": "\U0001f50c Guest Agent",
    "Host con salida a Internet (Apple y Cloudflare responden).":
        "Hôte avec accès Internet (Apple et Cloudflare répondent).",
    "El host no tiene salida a Internet.":
        "L'hôte n'a pas d'accès Internet.",

    # --- diagnostics ---
    "Ver log completo": "Voir le journal complet",
    "Selecciona una VM primero.": "Sélectionnez d'abord une VM.",
    "Exportar log": "Exporter le journal",
    "Salud de la VM": "Santé de la VM",
    "Limpiar procesos huérfanos": "Nettoyer les processus orphelins",
    "Nada que limpiar.": "Rien à nettoyer.",
    "Dependencias": "Dépendances",
    "Virtualización: sin comprobar": "Virtualisation : non vérifiée",
    "Distribución: {0}": "Distribution : {0}",
    "Gestor de paquetes: {0}": "Gestionnaire de paquets : {0}",
    "no encontrado": "non trouvé",
    "SIN COMPROBAR": "NON VÉRIFIÉ",
    "REVISAR": "À VÉRIFIER",
    "disponible": "disponible",
    "no disponible": "non disponible",
    "no detectado": "non détecté",

    # --- guest integration ---
    "Carpetas compartidas": "Dossiers partagés",
    "Instalar dependencias": "Installer les dépendances",
    "Dependencias": "Dépendances",
    "Montaje automático": "Montage automatique",
    "Carpeta compartida lista": "Dossier partagé prêt",
    "Carpeta:": "Dossier :",
    "Generando ISO de Guest Tools…":
        "Génération de l'ISO Guest Tools…",
    "ISO creada.": "ISO créée.",
    "ISO disponible: {0}": "ISO disponible : {0}",
    "Crear ISO de Guest Tools": "Créer l'ISO Guest Tools",
    "Creando ISO de Guest Tools…": "Création de l'ISO Guest Tools…",
    "Manual": "Manuel",
    "Automático": "Automatique",
    "Automático al iniciar SO": "Automatique au démarrage de l'OS",
    "Automático bajo demanda": "Automatique à la demande",
    "Solo lectura": "Lecture seule",
    "Lectura / escritura": "Lecture / écriture",
    "Carpeta compartida": "Dossier partagé",
    "Seleccionar carpeta del host": "Sélectionner un dossier de l'hôte",
    "Carpeta del host:": "Dossier de l'hôte :",
    "Etiqueta / guest:": "Étiquette / invité :",
    "Método:": "Méthode :",
    "Montaje en el guest:": "Montage dans l'invité :",
    "Acceso:": "Accès :",
    "Compartir": "Partager",

    # --- backups (basico) ---
    "Backups automaticos programados": "Sauvegardes programmées",
    "Activar": "Activer",
    "Cada hora": "Chaque heure",
    "Cada 6 horas": "Toutes les 6 heures",
    "Cada 12 horas": "Toutes les 12 heures",
    "Diario": "Quotidien",
    "Semanal": "Hebdomadaire",
    "Frecuencia:": "Fréquence :",
    "Conservar:": "Conserver :",
    "Destino:": "Destination :",
    "Elegir carpeta...": "Choisir un dossier…",
    "Backup ahora": "Sauvegarder maintenant",
    "Backup": "Sauvegarde",
    "Selecciona primero una maquina virtual.":
        "Sélectionnez d'abord une machine virtuelle.",
    "Selecciona primero una máquina virtual.":
        "Sélectionnez d'abord une machine virtuelle.",

    # --- plantillas / defaults / clone ---
    "Plantilla guardada": "Modèle enregistré",
    "VM creada": "VM créée",
    "Clon creado": "Clone créé",
    "Clon completo": "Clone complet",
    "Clon enlazado": "Clone lié",
    "Desenlazado": "Détaché",
    "Desenlazado cancelado por el usuario.":
        "Détachement annulé par l'utilisateur.",
    "Etiqueta de la VM": "Étiquette de la VM",
    "Etiqueta": "Étiquette",
    "Etiqueta - {0}": "Étiquette - {0}",
    "(sin grupo)": "(sans groupe)",
    "Grupo:": "Groupe :",
    "Sin color": "Sans couleur",
    "Quitar etiqueta": "Retirer l'étiquette",
    "Sin grupo": "Sans groupe",
    "Comparar con defaults": "Comparer aux valeurs par défaut",
    "Firmware": "Firmware",
    "Chipset": "Chipset",
    "CPU (modelo)": "CPU (modèle)",
    "Núcleos": "Cœurs",
    "Gráficos": "Graphiques",
    "VRAM": "VRAM",
    "Audio": "Audio",
    "Campo": "Champ",
    "Actual": "Actuel",
    "Por defecto": "Par défaut",
    "Aplicar al campo seleccionado": "Appliquer au champ sélectionné",
    "Aplicar todos los defaults": "Appliquer toutes les valeurs par défaut",

    # --- imports/exports/OVF dialogos simples ---
    "Importar VM": "Importer une VM",
    "Exportar VM": "Exporter la VM",
    "Primero selecciona una máquina virtual.":
        "Sélectionnez d'abord une machine virtuelle.",
    "Importar OVF/OVA": "Importer OVF/OVA",
    "Importar OVA": "Importer OVA",
    "Importar OVF": "Importer OVF",
    "Exportar": "Exporter",
    "Importar": "Importer",
    "Formato del disco": "Format du disque",
    "Opciones adicionales": "Options supplémentaires",

    # ================================================================
    # Media library (UI + handlers)
    # ================================================================
    "Biblioteca de Medios": "Bibliothèque de médias",
    "Buscar por nombre, distro, tag...":
        "Rechercher par nom, distro, tag…",
    "Anadir archivo(s)": "Ajouter un/des fichier(s)",
    "Escanear carpeta": "Analyser un dossier",
    "Escanear VMs": "Analyser les VMs",
    "\U0001f50e Escanear VMs": "\U0001f50e Analyser les VMs",
    "Tamaño real": "Taille réelle",
    "Ultimo uso": "Dernière utilisation",
    "Escanear": "Analyser",
    "Agrandar": "Agrandir",
    "Compactar": "Compacter",
    "Verificar": "Vérifier",
    "Calcular SHA256": "Calculer le SHA256",
    "Editar": "Modifier",
    "Eliminar": "Supprimer",
    "Eliminar entrada": "Supprimer l'entrée",
    "Quitar del indice": "Retirer de l'index",
    "Eliminar tambien el archivo": "Supprimer aussi le fichier",
    "Distro:": "Distro :",
    "Arquitectura:": "Architecture :",
    "URL origen:": "URL source :",
    "(Sin color)": "(Sans couleur)",
    "Rojo": "Rouge",
    "Naranja": "Orange",
    "Ambar": "Ambre",
    "Verde": "Vert",
    "Verde azul": "Turquoise",
    "Azul": "Bleu",
    "Indigo": "Indigo",
    "Violeta": "Violet",
    "Rosa": "Rose",
    "Gris": "Gris",
    "huerfano": "orphelin",
    "verificado?": "vérifié ?",
    "Biblioteca no disponible.": "Bibliothèque non disponible.",
    "La biblioteca no esta disponible.":
        "La bibliothèque n'est pas disponible.",

    # --- Etiquetas dinamicas del panel de recursos ---
    "Guest Agent: —": "Guest Agent : —",
    "Carpetas: —": "Dossiers : —",
    "Clipboard: —": "Presse-papiers : —",
    "spice-vdagent: —": "spice-vdagent : —",
    "Guest Agent: apagado": "Guest Agent : éteint",
    "Carpetas: apagado": "Dossiers : éteint",
    "Clipboard: apagado": "Presse-papiers : éteint",
    "spice-vdagent: apagado": "spice-vdagent : éteint",
    "activo": "actif",
    "sin respuesta": "sans réponse",
    "con problemas": "avec des problèmes",
    "Clipboard: activo": "Presse-papiers : actif",
    "Clipboard: desactivado": "Presse-papiers : désactivé",
    "spice-vdagent: activo": "spice-vdagent : actif",
    "spice-vdagent: no detectado": "spice-vdagent : non détecté",

    # --- Estados VM ---
    "● Ejecutándose": "● En cours d'exécution",
    "● Pausada": "● En pause",
    "● Apagada": "● Éteinte",
    "● Nueva VM": "● Nouvelle VM",
    "● Configurada": "● Configurée",
    "● Error": "● Erreur",
    "No hay una máquina virtual seleccionada todavía.":
        "Aucune machine virtuelle sélectionnée pour le moment.",
    "Nueva máquina virtual": "Nouvelle machine virtuelle",

    # --- Firmware / sistema avisos rapidos ---
    "Sistema:": "Système :",
    "CPU:": "CPU :",
    "RAM:": "RAM :",
    "Firmware:": "Firmware :",
    "Secure Boot:": "Secure Boot :",
    "TPM:": "TPM :",
    "Gráficos:": "Graphiques :",
    "Audio:": "Audio :",
    "Red:": "Réseau :",
    "Almacenamiento:": "Stockage :",
    "Orden de arranque:": "Ordre de démarrage :",
    "Ubicación:": "Emplacement :",
    "Notas:": "Notes :",
    "Notas": "Notes",
    "Vacío": "Vide",
    "CD/DVD": "CD/DVD",
    "Disco Duro": "Disque dur",

    # ================================================================
    # Dialogos de sistema/VM (los mas frecuentes)
    # ================================================================
    "La máquina virtual no está corriendo.":
        "La machine virtuelle n'est pas en cours d'exécution.",
    "Control de VM": "Contrôle de la VM",
    "Reanudar": "Reprendre",
    "La máquina virtual ya está corriendo.":
        "La machine virtuelle est déjà en cours d'exécution.",
    "La máquina virtual no está pausada: no hay nada que reanudar.":
        "La machine virtuelle n'est pas en pause : rien à reprendre.",
    "Apagar VM": "Éteindre la VM",
    "Reiniciar VM": "Redémarrer la VM",
    "Forzar apagado": "Arrêt forcé",
    "Forzar reinicio": "Redémarrage forcé",
    "Pausar": "Mettre en pause",
    "Pausar/Reanudar": "Pause/Reprendre",
    "Abriendo…": "Ouverture…",
    "Guardar cambios": "Enregistrer les modifications",
    "No se pudo comprobar el estado de la VM: {0}":
        "Impossible de vérifier l'état de la VM : {0}",

    # ================================================================
    # i18n_tanda_fr_1_v1
    # ================================================================

    # kvm_preflight_v1
    '/dev/kvm no está disponible. La VM arrancará con emulación por software (TCG), que es 10-100× más lenta que KVM.\n\n{0}':
        "/dev/kvm n'est pas disponible. La VM démarrera avec l'émulation logicielle (TCG), 10 à 100× plus lente que KVM.\n\n{0}",
    "Tu usuario no puede usar /dev/kvm (no está en el grupo 'kvm'). La VM arrancará con emulación por software (muy lenta).\n\n{0}":
        "Votre utilisateur ne peut pas utiliser /dev/kvm (pas dans le groupe 'kvm'). La VM démarrera avec l'émulation logicielle (très lente).\n\n{0}",

    # kvm_preflight_v1_fix1
    'Idioma de la interfaz.':
        "Langue de l'interface.",
}
