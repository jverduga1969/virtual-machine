# -*- coding: utf-8 -*-
"""vm_it_tanda2b - Traduzioni in italiano - Tanda 2b.

Copre il pannello destro della Panoramica:
  - Pulsante 'Fissa' e il suo tooltip.
  - Pannello 'Uso risorse' (CPU/RAM/Disco/Rete) + tooltip.
  - Pannello 'Informazioni generali' (etichette statiche).
  - Pannello 'Ultima istantanea'.
  - Pannello destro dinamico (valori aggiornati selezionando una VM).
"""

TRANSLATIONS = {

    # ================================================================
    # Pulsante Fissa
    # ================================================================
    "\U0001f4cc Fijar": "\U0001f4cc Fissa",
    "Fija este panel como columna derecha de la ventana, siempre visible.\n"
    "Útil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\n"
    "Vuelve a pulsar para devolverlo a Resumen.":
        "Fissa questo pannello come colonna destra della finestra, sempre visibile.\n"
        "Utile per monitorare CPU/RAM mentre lavori in un'altra scheda.\n"
        "Premi di nuovo per riportarlo alla Panoramica.",

    # ================================================================
    # Pannello 'Uso risorse'
    # ================================================================
    "\U0001f4ca Uso de recursos": "\U0001f4ca Uso risorse",
    "CPU (VM)": "CPU (VM)",
    "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n"
    "100% = el proceso usa el equivalente a todos los hilos del host.\n"
    "Si el host tiene 8 hilos y QEMU usa 4, verás 50%.":
        "Uso CPU del processo QEMU sull'host, attribuito a questa VM.\n"
        "100% = il processo usa l'equivalente di tutti i thread dell'host.\n"
        "Se l'host ha 8 thread e QEMU ne usa 4, vedrai 50%.",
    "RAM (QEMU)": "RAM (QEMU)",
    "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\n"
    "realmente en el sistema anfitrión), como porcentaje de la RAM\n"
    "total del host. No es la RAM que 've' el sistema invitado.":
        "Memoria RSS del processo QEMU sull'host (quello che QEMU occupa\n"
        "realmente nel sistema host), come percentuale della RAM\n"
        "totale dell'host. Non è la RAM che 'vede' il sistema guest.",
    "Disco (VM)": "Disco (VM)",
    "I/O de disco generado por el proceso QEMU para esta VM, según\n"
    "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
    "Es el tráfico real a los archivos de disco de la VM en el host.":
        "I/O disco generato dal processo QEMU per questa VM, secondo\n"
        "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
        "È il traffico reale verso i file del disco della VM sull'host.",
    "Red (VM)": "Rete (VM)",
    "Tráfico de red de esta VM.\n"
    "• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n"
    "  asociada en el host (exacto).\n"
    "• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n"
    "  el host, así que no se puede medir sin Guest Agent.\n"
    "  El gráfico mostrará 'NAT (sin medida)'.":
        "Traffico di rete di questa VM.\n"
        "• Modalità TAP/Bridge: vengono letti i contatori reali dell'interfaccia\n"
        "  associata sull'host (esatto).\n"
        "• Modalità NAT: QEMU usa uno stack interno senza interfaccia visibile\n"
        "  sull'host, quindi non può essere misurato senza Guest Agent.\n"
        "  Il grafico mostrerà 'NAT (non misurato)'.",

    # ================================================================
    # Pannello 'Informazioni generali'
    # ================================================================
    "\u2139\ufe0f Información general": "\u2139\ufe0f Informazioni generali",
    "Estado:": "Stato:",
    "Tiempo activo:": "Tempo di attività:",
    "Procesos:": "Processi:",
    "Dirección IP:": "Indirizzo IP:",
    "Dirección MAC:": "Indirizzo MAC:",
    "Guest Agent:": "Guest Agent:",
    "Carpetas:": "Cartelle:",
    "Clipboard:": "Appunti:",
    "spice-vdagent:": "spice-vdagent:",
    "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\n"
    "Cuando está activo, el clipboard bidireccional y la\n"
    "resolución automática funcionan.":
        "Rilevamento di spice-vdagent nel guest tramite QEMU Guest Agent.\n"
        "Quando è attivo, gli appunti bidirezionali e la\n"
        "risoluzione automatica funzionano.",
    "PID QEMU:": "PID QEMU:",
    "Uso de CPU del proceso QEMU expresado como porcentaje del total\n"
    "de hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\n"
    "valor mostrado es 50%.":
        "Uso CPU del processo QEMU espresso come percentuale del totale\n"
        "dei thread dell'host. Se l'host ha 8 thread e QEMU ne usa 4, il\n"
        "valore mostrato è 50%.",
    "CPU (VM):": "CPU (VM):",
    "Memoria RAM libre del host, respecto al total.":
        "Memoria RAM libera dell'host, rispetto al totale.",
    "RAM host:": "RAM host:",
    "Tamaño del archivo de disco principal de la VM y su tamaño\n"
    "virtual (lo que ve el sistema invitado).":
        "Dimensione del file del disco principale della VM e la sua dimensione\n"
        "virtuale (quella che vede il sistema guest).",
    "Disco:": "Disco:",
    "Número de snapshots registrados y antigüedad del último.":
        "Numero di istantanee registrate ed età dell'ultima.",
    "Snapshots:": "Istantanee:",

    # ================================================================
    # Pannello 'Ultima istantanea'
    # ================================================================
    "\U0001f5bc\ufe0f Último snapshot": "\U0001f5bc\ufe0f Ultima istantanea",
    "Sin VM seleccionada": "Nessuna VM selezionata",
    "\u21a9 Restaurar este snapshot": "\u21a9 Ripristina questa istantanea",
    "Restaura el snapshot más reciente de esta VM.\n"
    "Si la VM está corriendo, se restaura en caliente (snapshot-load).\n"
    "Si está apagada, se restauran los discos QCOW2 internos.":
        "Ripristina l'istantanea più recente di questa VM.\n"
        "Se la VM è in esecuzione, viene ripristinata a caldo (snapshot-load).\n"
        "Se è spenta, vengono ripristinati i dischi QCOW2 interni.",
    "Sin captura de pantalla": "Nessuna schermata",

    # ================================================================
    # Pannello destro dinamico
    # ================================================================
    "No hay una máquina virtual seleccionada.\n\n"
    "Pulsa 'Nueva máquina virtual' para comenzar.":
        "Nessuna macchina virtuale selezionata.\n\n"
        "Premi 'Nuova macchina virtuale' per iniziare.",
    "Configura el sistema en la pestaña 'Configuración'.":
        "Configura il sistema nella scheda 'Configurazione'.",
    "● Ejecutándose": "● In esecuzione",
    "● Pausada": "● In pausa",
    "● Apagada": "● Spenta",
    "Notas:": "Note:",
    "Sí": "Sì",
    "No": "No",
    "Red 1": "Rete 1",
    "Sin adaptadores configurados": "Nessun adattatore configurato",
    "Disco Duro": "Disco rigido",
    "CD/DVD": "CD/DVD",
    "vacío": "vuoto",
    "Sin dispositivos": "Nessun dispositivo",
    "Sistema:": "Sistema:",
    "CPU:": "CPU:",
    "RAM:": "RAM:",
    "núcleos": "core",
    "Firmware:": "Firmware:",
    "Secure Boot:": "Secure Boot:",
    "TPM:": "TPM:",
    "Gráficos:": "Grafica:",
    "Audio:": "Audio:",
    "Red:": "Rete:",
    "Almacenamiento:": "Archiviazione:",
    "Orden de arranque:": "Ordine di avvio:",
    "Ubicación:": "Posizione:",
    "VM nueva: todavía no se ha guardado una configuración.":
        "Nuova VM: nessuna configurazione ancora salvata.",
    "Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio.":
        "Configura la VM nella scheda 'Configurazione' e premi il pulsante di avvio.",
    "Usa 'Configuración' para modificar hardware y opciones avanzadas.":
        "Usa 'Configurazione' per modificare hardware e opzioni avanzate.",

    # ================================================================
    # Valori dinamici integrazione Host <-> Guest
    # ================================================================
    "Guest Agent: —": "Guest Agent: —",
    "Carpetas: —": "Cartelle: —",
    "Clipboard: —": "Appunti: —",
    "spice-vdagent: —": "spice-vdagent: —",
    "Guest Agent: apagado": "Guest Agent: spento",
    "Carpetas: apagado": "Cartelle: spento",
    "Clipboard: apagado": "Appunti: spento",
    "spice-vdagent: apagado": "spice-vdagent: spento",
    "Guest Agent: {0}": "Guest Agent: {0}",
    "activo": "attivo",
    "sin respuesta": "nessuna risposta",
    "Carpetas: {0}": "Cartelle: {0}",
    "con problemas": "con problemi",
    "Clipboard: activo": "Appunti: attivo",
    "Clipboard: desactivado": "Appunti: disattivato",
    "spice-vdagent: activo": "spice-vdagent: attivo",
    "spice-vdagent: no detectado": "spice-vdagent: non rilevato",
}
