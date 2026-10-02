# -*- coding: utf-8 -*-
"""vm_it_tanda2c - Traduzioni in italiano - Tanda 2c.

Copre la scheda Configurazione VM completa:
  - Sistema (firmware, chipset, sicurezza, opzioni avanzate, autostart,
    modalita compatibilita istantanee).
  - Processore (modello CPU, core).
  - Memoria (RAM assegnata).
  - Schermo (grafica, VRAM, VNC integrato, Console remota, log VNC).
  - Rete (adattatori, modalita, modello).
  - Dispositivi (audio, puntatore, porta seriale).
  - Archiviazione (controller, dispositivi, ordine di avvio) +
    storage_mixin (Espandi disco).
"""

TRANSLATIONS = {

    # ================================================================
    # Sistema
    # ================================================================
    "Sistema": "Sistema",
    "Plataforma, firmware y opciones de bajo nivel del hardware virtual.":
        "Piattaforma, firmware e opzioni di basso livello dell'hardware virtuale.",
    "<b>Firmware</b>": "<b>Firmware</b>",
    "BIOS (tradicional)": "BIOS (tradizionale)",
    "UEFI (OVMF)": "UEFI (OVMF)",
    "<b>Chipset</b>": "<b>Chipset</b>",
    "i440FX (clásico)": "i440FX (classico)",
    "Q35 (moderno, PCIe)": "Q35 (moderno, PCIe)",
    "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\n"
    "Q35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\n"
    "passthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica.":
        "i440FX: chipset classico, PCI legacy. Compatibile con SO molto vecchi.\n"
        "Q35: chipset moderno con PCIe nativo, AHCI/SATA e miglior supporto per\n"
        "passthrough di dispositivi PCIe. Consigliato salvo specifiche esigenze di compatibilita.",
    "<b>Seguridad</b>": "<b>Sicurezza</b>",
    "Secure Boot": "Secure Boot",
    "TPM 2.0": "TPM 2.0",
    "<b>Perfiles del sistema</b>": "<b>Profili di sistema</b>",
    "Configuración optimizada para el sistema operativo seleccionado. Puede modificar los valores según sus necesidades.":
        "Configurazione ottimizzata per il sistema operativo selezionato. Puoi modificare i valori in base alle tue esigenze.",
    "<b>Opciones avanzadas</b>": "<b>Opzioni avanzate</b>",
    "Habilitar ACPI": "Abilita ACPI",
    "Habilitar APIC": "Abilita APIC",
    "Habilitar IOMMU": "Abilita IOMMU",
    "PCIe Root Port": "PCIe Root Port",
    "Arrancar esta VM al abrir la aplicación": "Avvia questa VM all'apertura dell'applicazione",
    "Si está marcado, esta VM se arranca automáticamente al\n"
    "abrir la aplicación, tras un par de segundos.\n\n"
    "Las VMs marcadas se arrancan en cola, separadas por 4 s\n"
    "entre una y otra para no saturar el host. Las que ya estén\n"
    "corriendo se saltan.\n\n"
    "Nota: al auto-arrancar, la selección de la lista cambia a\n"
    "cada VM que se inicia.":
        "Se selezionato, questa VM viene avviata automaticamente all'\n"
        "apertura dell'applicazione, dopo un paio di secondi.\n\n"
        "Le VM selezionate vengono avviate in coda, separate da 4 s\n"
        "l'una dall'altra per non saturare l'host. Quelle gia\n"
        "in esecuzione vengono saltate.\n\n"
        "Nota: durante l'avvio automatico, la selezione dell'elenco passa\n"
        "a ogni VM che viene avviata.",
    "Modo compatibilidad de snapshots (fuerza hardware snapshoteable)":
        "Modalita compatibilita istantanee (forza hardware compatibile con snapshot)",

    # ================================================================
    # Processore
    # ================================================================
    "Procesador": "Processore",
    "Modelo de CPU y número de núcleos asignados a la máquina virtual.":
        "Modello di CPU e numero di core assegnati alla macchina virtuale.",
    "<b>Tipo de procesador</b>": "<b>Tipo di processore</b>",
    "Automático (recomendado)": "Automatico (consigliato)",
    "Host (máximo rendimiento)": "Host (massime prestazioni)",
    "QEMU x86-64 (compatibilidad)": "QEMU x86-64 (compatibilita)",
    "Automático usa el perfil del SO. Host ofrece el máximo rendimiento pero reduce la portabilidad de la VM.":
        "Automatico usa il profilo del SO. Host offre le massime prestazioni ma riduce la portabilita della VM.",
    "<b>Núcleos</b>": "<b>Core</b>",
    "{0} núcleos": "{0} core",
    "El número de núcleos se ajusta al par más cercano al valor elegido, hasta la mitad de los hilos del host.":
        "Il numero di core viene arrotondato al pari piu vicino al valore scelto, fino alla meta dei thread dell'host.",

    # ================================================================
    # Memoria
    # ================================================================
    "Memoria": "Memoria",
    "Cantidad de memoria RAM asignada a la máquina virtual.":
        "Quantita di memoria RAM assegnata alla macchina virtuale.",
    "<b>RAM asignada</b>": "<b>RAM assegnata</b>",
    "RAM del host: {0} GB (libre: {1} GB)": "RAM dell'host: {0} GB (libera: {1} GB)",
    "Asignar más de la mitad de la RAM del host puede provocar uso intensivo de swap. La sugerencia es dejar al menos 2 GB para el sistema anfitrión.":
        "Assegnare piu della meta della RAM dell'host puo causare un uso intenso dello swap. Il suggerimento e di lasciare almeno 2 GB per il sistema host.",

    # ================================================================
    # Schermo
    # ================================================================
    "Pantalla": "Schermo",
    "Controlador gráfico virtual y memoria de video.":
        "Controller grafico virtuale e memoria video.",
    "<b>Gráficos / GPU</b>": "<b>Grafica / GPU</b>",
    "VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)":
        "VirtIO-GPU 2D (compatibile • ist. dischi ✓ • ist. completo ✗)",
    "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)":
        "VirtIO-GPU + VirGL 3D (OpenGL • istantanee ✗)",
    "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)":
        "VirtIO-GPU + Venus/Vulkan 3D (sperimentale • istantanee ✗)",
    "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)":
        "Red Hat QXL 2D (3D ✗ • ist. completo ✓ • macOS ⚠)",
    "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)":
        "VMware SVGA II (3D accelerato ✗ • ist. completo ✓ • macOS ⚠)",
    "Sin video / Headless": "Senza video / Headless",
    "Automático detecta las capacidades del host y usa aceleración 3D cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\nSnapshots:\n  • VirtIO-GPU 2D → solo snap. de discos.\n  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n  • VirGL / Venus → no soportan ningún tipo de snapshot.":
        "Automatico rileva le capacita dell'host e usa l'accelerazione 3D quando e sicura; altrimenti torna a VirtIO-GPU 2D.\n\nIstantanee:\n  • VirtIO-GPU 2D → solo ist. di dischi.\n  • QXL e VMware SVGA → ist. completo (RAM + dispositivi).\n  • VirGL / Venus → non supportano alcun tipo di istantanea.",
    "<b>Memoria de video (VRAM)</b>": "<b>Memoria video (VRAM)</b>",
    "Host GPU: detectando…": "GPU host: rilevamento in corso…",
    "\U0001f5bc\ufe0f Mostrar la VM dentro de la app (consola VNC embebida)":
        "\U0001f5bc\ufe0f Mostra la VM dentro l'app (console VNC integrata)",
    "Cuando está activo, la VM se muestra dentro de la app.\n"
    "Fuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\n"
    "Si lo desactivas, la VM se abre en una ventana externa y puedes\n"
    "elegir modos con aceleración 3D (VirGL, Venus).":
        "Quando attivo, la VM viene mostrata dentro l'app.\n"
        "Forza grafica senza accelerazione OpenGL (VNC non supporta GL).\n"
        "Se lo disattivi, la VM si apre in una finestra esterna e puoi\n"
        "scegliere modalita con accelerazione 3D (VirGL, Venus).",

    # --- Console remota ---
    "Consola remota": "Console remota",
    "VNC (compatible con cualquier gráfico)": "VNC (compatibile con qualsiasi grafica)",
    "SPICE (mejor rendimiento en local)": "SPICE (prestazioni migliori in locale)",
    "VNC: cliente ligero, funciona con cualquier dispositivo de video.\n"
    "SPICE: mejor rendimiento en local, requiere un visor spice-gtk.\n"
    "Con cualquiera de los dos, QEMU no abre ventana local: solo el socket.":
        "VNC: client leggero, funziona con qualsiasi dispositivo video.\n"
        "SPICE: prestazioni migliori in locale, richiede un visualizzatore spice-gtk.\n"
        "Con entrambi, QEMU non apre una finestra locale: solo il socket.",
    "Protocolo:": "Protocollo:",
    "Embebida en la app": "Integrata nell'app",
    "Ventana externa (visor del sistema)": "Finestra esterna (visualizzatore di sistema)",
    "Ventana nativa de QEMU": "Finestra nativa di QEMU",
    "Híbrida (VNC embebido + SPICE externo)": "Ibrida (VNC integrato + SPICE esterno)",
    "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\n"
    "Ventana externa: se lanza el visor del sistema (vncviewer / spicy).\n"
    "Nativa QEMU: QEMU abre su propia ventana (comportamiento clásico).":
        "Integrata: lo schermo vive dentro questa app (scheda Console Grafica).\n"
        "Finestra esterna: viene lanciato il visualizzatore di sistema (vncviewer / spicy).\n"
        "Nativa QEMU: QEMU apre la propria finestra (comportamento classico).",
    "Modo:": "Modalita:",
    "Log VNC detallado (DEBUG)": "Log VNC dettagliato (DEBUG)",
    "Activa el nivel DEBUG del cliente VNC embebido.\n\n"
    "Por defecto INFO: el widget VNC no llena launch.log con\n"
    "una línea por cada frame. Actívalo solo para diagnosticar\n"
    "problemas concretos del cliente VNC; escribe miles de\n"
    "líneas por segundo y puede afectar al rendimiento.":
        "Attiva il livello DEBUG del client VNC integrato.\n\n"
        "Predefinito INFO: il widget VNC non riempie launch.log con\n"
        "una riga per ogni frame. Attivalo solo per diagnosticare\n"
        "problemi specifici del client VNC; scrive migliaia di\n"
        "righe al secondo e puo influire sulle prestazioni.",

    # ================================================================
    # Rete
    # ================================================================
    "Red": "Rete",
    "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.":
        "Adattatori di rete virtuali. Ognuno puo usare NAT, bridge o TAP.",
    "Adaptadores": "Adattatori",
    "\u2795 Agregar adaptador": "\u2795 Aggiungi adattatore",
    "\u270f Editar": "\u270f Modifica",
    "Sin red (ningún adaptador virtual)": "Senza rete (nessun adattatore virtuale)",
    "NAT / Internet (recomendado)": "NAT / Internet (consigliato)",
    "Bridge existente": "Bridge esistente",
    "TAP": "TAP",
    "VirtIO (recomendado)": "VirtIO (consigliato)",
    "Intel E1000": "Intel E1000",
    "Realtek RTL8139": "Realtek RTL8139",
    "VMware VMXNET3": "VMware VMXNET3",
    "Interfaz/Bridge:": "Interfaccia/Bridge:",

    # ================================================================
    # Dispositivi
    # ================================================================
    "Dispositivos": "Dispositivi",
    "Audio y otros dispositivos integrados de la máquina virtual.":
        "Audio e altri dispositivi integrati della macchina virtuale.",
    "<b>Audio</b>": "<b>Audio</b>",
    "Intel HDA (recomendado)": "Intel HDA (consigliato)",
    "AC97": "AC97",
    "Sound Blaster 16": "Sound Blaster 16",
    "Sin sonido": "Senza audio",
    "<b>Dispositivo de señalización (ratón / teclado)</b>":
        "<b>Dispositivo di puntamento (mouse / tastiera)</b>",
    "USB Tablet (posición absoluta)": "USB Tablet (posizione assoluta)",
    "USB Mouse (posición relativa)": "USB Mouse (posizione relativa)",
    "USB Keyboard + Tablet": "USB Keyboard + Tablet",
    "VirtIO Tablet (requiere drivers en el guest)": "VirtIO Tablet (richiede driver nel guest)",
    "PS/2 (clásico)": "PS/2 (classico)",
    "Ninguno": "Nessuno",
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
        "Dispositivo di input che QEMU emula per mouse/tastiera.\n\n"
        "• Automatico: macOS usa USB Tablet su NEC XHCI; gli altri mantengono\n"
        "  il PS/2 predefinito di QEMU.\n"
        "• USB Tablet: posizione assoluta (il cursore del guest segue 1:1 quello\n"
        "  dell'host). Consigliato se il cursore non si muove bene.\n"
        "• USB Mouse: posizione relativa, come un mouse fisico.\n"
        "• USB Keyboard + Tablet: aggiunge anche una tastiera USB.\n"
        "• VirtIO Tablet: prestazioni migliori, richiede driver VirtIO nel\n"
        "  guest (non valido su macOS).\n"
        "• PS/2: mouse/tastiera tradizionali di QEMU, senza USB.\n"
        "• Nessuno: nessun mouse/tastiera emulati.",
    "Capturar el puerto serie a un archivo (serial.log)":
        "Cattura la porta seriale su file (serial.log)",
    "Activa -serial file:<vm_dir>/serial.log en la linea de QEMU.\n\n"
    "El puerto serie del guest se vuelca a un archivo dentro de la\n"
    "carpeta de la VM. La BIOS/OVMF, el cargador de arranque y el\n"
    "kernel suelen escribir ahi su progreso: es la forma mas directa\n"
    "de ver por que una VM se queda en pantalla negra o se reinicia.\n\n"
    "El archivo se SOBREESCRIBE en cada arranque: solo conserva la\n"
    "ultima sesion. Se puede abrir con '📂 Carpeta' en la pestana\n"
    "Resumen.":
        "Attiva -serial file:<vm_dir>/serial.log nella riga di comando QEMU.\n\n"
        "La porta seriale del guest viene riversata in un file dentro la\n"
        "cartella della VM. Il BIOS/OVMF, il bootloader e il\n"
        "kernel di solito vi scrivono il loro avanzamento: e il modo piu diretto\n"
        "per vedere perche una VM resta su schermo nero o si riavvia.\n\n"
        "Il file viene SOVRASCRITTO ad ogni avvio: conserva solo l'\n"
        "ultima sessione. Si puo aprire con '📂 Cartella' nella scheda\n"
        "Panoramica.",
    "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña <b>Dispositivos</b> de la parte superior de la ventana.":
        "Per passare hardware fisico (PCI/USB) a questa VM, usa la scheda <b>Dispositivi</b> nella parte superiore della finestra.",

    # ================================================================
    # Archiviazione
    # ================================================================
    "Almacenamiento": "Archiviazione",
    "Discos, unidades ópticas y orden de arranque de la máquina virtual.":
        "Dischi, unita ottiche e ordine di avvio della macchina virtuale.",
    "Controladores y dispositivos": "Controller e dispositivi",
    "Dispositivo": "Dispositivo",
    "Tipo / archivo": "Tipo / file",
    "Tamaño": "Dimensione",
    "\U0001f4c0 CD / DVD": "\U0001f4c0 CD / DVD",
    "\U0001f4bd Disco Duro": "\U0001f4bd Disco rigido",
    "\U0001f4be Disquete": "\U0001f4be Floppy",
    "\u270f Modificar": "\u270f Modifica",
    "\u270f\ufe0f Modificar": "\u270f\ufe0f Modifica",
    "\U0001f5dc Compactar": "\U0001f5dc Compatta",
    "\U0001f5dc\ufe0f Compactar": "\U0001f5dc\ufe0f Compatta",
    "Compacta un disco QCOW2 de la VM seleccionada.\n\n"
    "Reduce el archivo físico en el host eliminando bloques no\n"
    "usados (equivalente a 'qemu-img convert -c'). NO cambia el\n"
    "tamaño virtual que ve el sistema invitado.\n\n"
    "Se pedirá confirmación y se recomienda hacer un backup antes\n"
    "de proceder. Requiere que la VM esté apagada.":
        "Compatta un disco QCOW2 della VM selezionata.\n\n"
        "Riduce il file fisico sull'host eliminando blocchi non\n"
        "usati (equivalente a 'qemu-img convert -c'). NON cambia la\n"
        "dimensione virtuale che vede il sistema guest.\n\n"
        "Verra richiesta conferma e si consiglia di fare un backup prima\n"
        "di procedere. Richiede che la VM sia spenta.",
    "Orden de arranque": "Ordine di avvio",
    "\u2b06 Subir": "\u2b06 Sposta su",
    "\u2b07 Bajar": "\u2b07 Sposta giu",
    "\U0001f5d1 Quitar": "\U0001f5d1 Rimuovi",
    "\U0001f5d1\ufe0f Quitar": "\U0001f5d1\ufe0f Rimuovi",

    # ================================================================
    # storage_mixin.py
    # ================================================================
    "Cambiar el medio de esta unidad CD/DVD.":
        "Cambia il supporto di questa unita CD/DVD.",
    "Los disquetes no se pueden redimensionar.\n"
    "Elimina este y crea otro si necesitas otro tamaño.":
        "I floppy non possono essere ridimensionati.\n"
        "Elimina questo e creane un altro se ti serve una dimensione diversa.",
    "\u2197 Expandir": "\u2197 Espandi",
    "Aumentar el tamaño virtual de este disco.\n"
    "El disco solo puede CRECER.":
        "Aumenta la dimensione virtuale di questo disco.\n"
        "Il disco puo solo CRESCERE.",
    "Expandir disco": "Espandi disco",
    "No se encontro la informacion del dispositivo seleccionado.":
        "Non e stata trovata l'informazione del dispositivo selezionato.",
    "Los disquetes no se pueden redimensionar.\n\n"
    "Eliminalo y crea otro si necesitas otro tamano.":
        "I floppy non possono essere ridimensionati.\n\n"
        "Eliminalo e creane un altro se ti serve una dimensione diversa.",
    "\u2197 Expandir disco": "\u2197 Espandi disco",
    "Dispositivo:": "Dispositivo:",
    "Tamano actual:": "Dimensione attuale:",
    "Ejemplo: 120G (solo crecer)": "Esempio: 120G (solo crescita)",
    "Nuevo tamano:": "Nuova dimensione:",
    "El disco solo puede CRECER. Si escribes un valor menor al actual, se rechaza y el campo vuelve al tamano original.\n\n"
    "Agrandar el archivo NO agranda la particion dentro del guest: tras aplicar el cambio, amplia tambien la particion/volumen desde el sistema invitado.":
        "Il disco puo solo CRESCERE. Se inserisci un valore inferiore a quello attuale, viene rifiutato e il campo torna alla dimensione originale.\n\n"
        "Ingrandire il file NON ingrandisce la partizione all'interno del guest: dopo aver applicato la modifica, estendi anche la partizione/volume dal sistema guest.",
    "No se pudo expandir el disco.\n\n{0}":
        "Impossibile espandere il disco.\n\n{0}",
}
