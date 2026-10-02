# -*- coding: utf-8 -*-
"""vm_it_tanda5 - Traduzioni in italiano - Tanda 5 (ultima).

Copre:
  - suggestions_mixin.py
  - health_dashboard_mixin.py
  - compare_defaults_mixin.py
  - vm_templates_mixin.py
  - task_progress.py
  - vm_lifecycle_mixin: import/export VM + OVF/OVA, clone, scollega,
    elimina, edit_vm_label, show_qemu_command, edit_vm_notes.
  - guest_integration_mixin.py
  - mac_recovery_mixin.py
  - install_flow_mixin.py
  - api_mixin.py
"""

TRANSLATIONS = {

    # ================================================================
    # suggestions_mixin.py
    # ================================================================
    "Selecciona una VM para ver sugerencias.":
        "Seleziona una VM per vedere i suggerimenti.",
    "No se pudo leer la configuración: {0}":
        "Impossibile leggere la configurazione: {0}",
    "Disco del host al {0}% — crítico. Quedan solo {1}. Amplía el disco o mueve archivos.":
        "Disco dell'host al {0}% — critico. Restano solo {1}. Espandi il disco o sposta i file.",
    "Disco del host al {0}%. Quedan {1}. Considera ampliarlo o limpiar.":
        "Disco dell'host al {0}%. Restano {1}. Considera di espanderlo o pulire.",
    "RAM de la VM ({0} GB) es el {1}% de la del host ({2} GB). Riesgo de swap.":
        "La RAM della VM ({0} GB) e il {1}% di quella dell'host ({2} GB). Rischio di swap.",
    "El último snapshot tiene {0} días ({1} en total). Puedes crear uno nuevo o limpiar los antiguos.":
        "L'ultima istantanea ha {0} giorni ({1} in totale). Puoi crearne una nuova o eliminare quelle vecchie.",
    "Hay {0} snapshots acumulados ocupando {1}. Considera eliminar los que ya no necesites.":
        "Ci sono {0} istantanee accumulate che occupano {1}. Considera di eliminare quelle che non ti servono piu.",
    "Hay {0} carpeta(s) VirtioFS configuradas pero el Guest Agent está desactivado. Algunas funciones de automontaje no funcionarán.":
        "Ci sono {0} cartella(e) VirtioFS configurate ma il Guest Agent e disattivato. Alcune funzioni di automontaggio non funzioneranno.",
    "{0} carpeta(s) compartida(s) apuntan a rutas que ya no existen en el host: {1}":
        "{0} cartella(e) condivisa(e) puntano a percorsi che non esistono piu sull'host: {1}",
    "Hay {0} dispositivo(s) PCI en passthrough pero IOMMU no parece estar activo en el kernel. La VM puede no arrancar.":
        "Ci sono {0} dispositivo(i) PCI in passthrough ma IOMMU non sembra essere attivo nel kernel. La VM potrebbe non avviarsi.",
    "Windows 11 requiere UEFI + Secure Boot. Cambia el firmware a UEFI.":
        "Windows 11 richiede UEFI + Secure Boot. Cambia il firmware in UEFI.",
    "macOS/OSX-KVM requiere UEFI (OVMF). Cambia el firmware a UEFI.":
        "macOS/OSX-KVM richiede UEFI (OVMF). Cambia il firmware in UEFI.",
    "El disco principal está en formato RAW. No admite snapshots internos ni crece dinámicamente. Considera convertir a QCOW2 si necesitas snapshots.":
        "Il disco principale e in formato RAW. Non supporta istantanee interne ne cresce dinamicamente. Considera di convertirlo in QCOW2 se hai bisogno di istantanee.",
    "El log de la VM ({0} MB) es grande. Puedes exportarlo y borrarlo desde 'Ver log completo' → 'Exportar log'.":
        "Il log della VM ({0} MB) e grande. Puoi esportarlo ed eliminarlo da 'Vedi log completo' → 'Esporta log'.",
    "La configuración no se ha modificado en {0} días. ¿Sigue siendo útil esta VM?":
        "La configurazione non e stata modificata da {0} giorni. Questa VM e ancora utile?",
    "La VM tiene audio configurado pero el host no tiene /dev/snd ni PulseAudio/PipeWire (pactl). QEMU puede fallar al arrancar con audio.":
        "La VM ha l'audio configurato ma l'host non ha /dev/snd ne PulseAudio/PipeWire (pactl). QEMU potrebbe fallire l'avvio con l'audio.",
    "Todo en orden. No hay sugerencias pendientes.":
        "Tutto in ordine. Nessun suggerimento in sospeso.",
    "\U0001f4a1 Sugerencias": "\U0001f4a1 Suggerimenti",

    # ================================================================
    # health_dashboard_mixin.py
    # ================================================================
    "Salud de la máquina virtual": "Salute della macchina virtuale",
    "<b style='font-size:15px;'>\U0001f6a6 Semáforos de salud</b>":
        "<b style='font-size:15px;'>\U0001f6a6 Semafari di salute</b>",
    "Cada fila muestra el estado de un subsistema de la VM. "
    "Verde: funciona · Amarillo: parcial o sin confirmar · "
    "Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s.":
        "Ogni riga mostra lo stato di un sottosistema della VM. "
        "Verde: funziona · Giallo: parziale o non confermato · "
        "Rosso: non disponibile · Grigio: non applicabile. Si aggiorna ogni 4 s.",
    "\U0001f310 Red de la VM": "\U0001f310 Rete della VM",
    "\U0001f5a5\ufe0f Internet del host": "\U0001f5a5\ufe0f Internet dell'host",
    "\U0001f50a Audio": "\U0001f50a Audio",
    "\U0001f5bc\ufe0f Pantalla": "\U0001f5bc\ufe0f Schermo",
    "\U0001f50c Guest Agent": "\U0001f50c Guest Agent",
    "\U0001f504 Refrescar ahora": "\U0001f504 Aggiorna adesso",
    "Sin VM seleccionada.": "Nessuna VM selezionata.",
    "Host con salida a Internet (Apple y Cloudflare responden).":
        "Host con accesso a Internet (Apple e Cloudflare rispondono).",
    "Salida parcial: uno de los dos destinos no respondió.":
        "Accesso parziale: una delle due destinazioni non ha risposto.",
    "El host no tiene salida a Internet.":
        "L'host non ha accesso a Internet.",
    "No hay script de arranque todavía.": "Nessuno script di avvio ancora.",
    "No se pudo leer el script de arranque.":
        "Impossibile leggere lo script di avvio.",
    "No hay adaptador de red configurado en esta VM.":
        "Nessun adattatore di rete configurato su questa VM.",
    "NIC {0}: tráfico activo "
    "({1:.1f} KB/s; "
    "rx {2:.1f} MB, "
    "tx {3:.1f} MB).":
        "NIC {0}: traffico attivo "
        "({1:.1f} KB/s; "
        "rx {2:.1f} MB, "
        "tx {3:.1f} MB).",
    "NIC {0} con contadores activos pero "
    "sin tráfico en el último intervalo "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB).":
        "NIC {0} con contatori attivi ma "
        "senza traffico nell'ultimo intervallo "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB).",
    "NIC {0}: contadores iniciales leídos "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB); "
    "esperando siguiente lectura para medir velocidad.":
        "NIC {0}: contatori iniziali letti "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB); "
        "in attesa della prossima lettura per misurare la velocita.",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host; esperando segunda lectura "
    "para medir cambio.":
        "NIC {0} configurata. {1} connessioni TCP "
        "attive sull'host; in attesa della seconda lettura "
        "per misurare la variazione.",
    "NIC {0}: actividad detectada "
    "({1} \u2192 {2} conexiones TCP ESTAB).":
        "NIC {0}: attivita rilevata "
        "({1} \u2192 {2} connessioni TCP ESTAB).",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host, sin cambios en el último "
    "intervalo (la VM puede estar idle).":
        "NIC {0} configurata. {1} connessioni TCP "
        "attive sull'host, nessun cambiamento nell'ultimo "
        "intervallo (la VM potrebbe essere inattiva).",
    "NIC {0} configurada; sin conexiones externas "
    "activas en el host.":
        "NIC {0} configurata; nessuna connessione esterna "
        "attiva sull'host.",
    "NIC {0} configurada. No se pudo medir tráfico (QMP no "
    "expone query-netdev y ss no está disponible).":
        "NIC {0} configurata. Impossibile misurare il traffico (QMP non "
        "espone query-netdev e ss non e disponibile).",
    "Sin audio configurado en esta VM.": "Nessun audio configurato su questa VM.",
    "Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.":
        "Audiodev configurato. pactl non disponibile; impossibile confermare la riproduzione.",
    "Audiodev configurado, pero no hay PID de QEMU para verificar el sink.":
        "Audiodev configurato, ma nessun PID di QEMU per verificare il sink.",
    "No se pudo consultar pactl: {0}":
        "Impossibile consultare pactl: {0}",
    "pactl no respondió.": "pactl non ha risposto.",
    "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo.":
        "Sink attivo: pactl vede QEMU (PID {0}) in riproduzione.",
    "Audiodev configurado; QEMU no está reproduciendo ahora. "
    "Es normal si el guest no está emitiendo sonido.":
        "Audiodev configurato; QEMU non sta riproducendo ora. "
        "E normale se il guest non sta emettendo suono.",
    "Framebuffer VNC {0}\u00d7{1}.": "Framebuffer VNC {0}\u00d7{1}.",
    "Widget VNC conectado, esperando primer frame.":
        "Widget VNC connesso, in attesa del primo frame.",
    "Consola SPICE embebida activa.": "Console SPICE integrata attiva.",
    "Visor externo activo (PID {0}).": "Visualizzatore esterno attivo (PID {0}).",
    "Modo remoto (socket VNC/SPICE) sin widget embebido ni "
    "visor activo. Abre la Consola Gráfica para ver la pantalla.":
        "Modalita remota (socket VNC/SPICE) senza widget integrato ne "
        "visualizzatore attivo. Apri la Console Grafica per vedere lo schermo.",
    "Modo headless (sin salida de pantalla).":
        "Modalita headless (senza uscita video).",
    "Ventana nativa de QEMU activa.": "Finestra nativa di QEMU attiva.",
    "Configuración de pantalla detectada en el script de arranque.":
        "Configurazione dello schermo rilevata nello script di avvio.",
    "Guest Agent no habilitado para esta VM "
    "(actívalo en Integración Host \u2194 Guest).":
        "Guest Agent non abilitato per questa VM "
        "(attivalo in Integrazione Host \u2194 Guest).",
    "QEMU Guest Agent responde.": "QEMU Guest Agent risponde.",
    "Canal QGA presente, pero el guest no responde.":
        "Canale QGA presente, ma il guest non risponde.",
    "Canal QGA presente, sin respuesta: {0}":
        "Canale QGA presente, nessuna risposta: {0}",

    # ================================================================
    # compare_defaults_mixin.py
    # ================================================================
    "Comparar con defaults": "Confronta con i predefiniti",
    "Selecciona primero una máquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "No se pudo determinar el perfil del SO seleccionado.":
        "Impossibile determinare il profilo del SO selezionato.",
    "Firmware": "Firmware",
    "Chipset": "Chipset",
    "CPU (modelo)": "CPU (modello)",
    "Núcleos": "Core",
    "Gráficos": "Grafica",
    "VRAM": "VRAM",
    "Audio": "Audio",
    "Señalización (ratón/teclado)": "Puntamento (mouse/tastiera)",
    "Consola: protocolo": "Console: protocollo",
    "Consola: modo": "Console: modalita",
    "Comparación de <b>{0}</b> con los valores por defecto del perfil del SO seleccionado. Las filas con fondo amarillo difieren del default.<br><br>Aplicar un default <b>no</b> guarda la VM: solo cambia el widget. Persiste con <b>Guardar</b> (en Configuración) o al iniciar la VM.":
        "Confronto di <b>{0}</b> con i valori predefiniti del profilo del SO selezionato. Le righe con sfondo giallo differiscono dal predefinito.<br><br>Applicare un predefinito <b>non</b> salva la VM: cambia solo il widget. Persiste con <b>Salva</b> (in Configurazione) o all'avvio della VM.",
    "Campo": "Campo",
    "Actual": "Attuale",
    "Por defecto": "Predefinito",
    "<b>{0}</b> diferencia(s) de <b>{1}</b> campo(s).":
        "<b>{0}</b> differenza(e) su <b>{1}</b> campo(i).",
    "Aplicar al campo seleccionado": "Applica al campo selezionato",
    "Aplicar todos los defaults": "Applica tutti i predefiniti",
    "Aplicar": "Applica",
    "Selecciona primero una fila.": "Seleziona prima una riga.",
    "==> Comparar defaults: aplicados {0} campo(s) a '{1}'.":
        "==> Confronta predefiniti: {0} campo(i) applicato(i) a '{1}'.",

    # ================================================================
    # vm_templates_mixin.py
    # ================================================================
    "Guardar como plantilla": "Salva come modello",
    "Esta VM no tiene vm_config.ini todavía.\n\nConfigúrala y guárdala primero.":
        "Questa VM non ha ancora vm_config.ini.\n\nConfigurala e salvala prima.",
    "Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?":
        "Il modello '{0}' esiste gia.\n\nSovrascrivere?",
    "No se pudo escribir la plantilla.\n\n{0}":
        "Impossibile scrivere il modello.\n\n{0}",
    "Plantilla guardada": "Modello salvato",
    "Plantilla '{0}' creada correctamente.\n\nAparecerá en el menú del botón '➕ Nueva VM'.":
        "Modello '{0}' creato correttamente.\n\nApparira nel menu del pulsante '➕ Nuova VM'.",
    "\U0001f195 Nueva VM en blanco": "\U0001f195 Nuova VM vuota",
    "Desde plantilla:": "Da modello:",
    "Crear desde plantilla": "Crea da modello",
    "No encuentro la plantilla '{0}'.": "Modello '{0}' non trovato.",
    "Ya existe una carpeta para '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Esiste gia una cartella per '{0}'.\n\nSostituirla? (quella esistente verra eliminata)",
    "No se pudo eliminar la carpeta existente.\n\n{0}":
        "Impossibile eliminare la cartella esistente.\n\n{0}",
    "No se pudo crear la VM.\n\n{0}": "Impossibile creare la VM.\n\n{0}",
    "VM creada": "VM creata",
    "VM '{0}' creada desde la plantilla '{1}'.\n\nSe ha abierto en Configuración → Almacenamiento para que\nañadas el disco y el medio de instalación. La MAC de red se\nha regenerado para evitar conflictos con otras VMs.":
        "VM '{0}' creata dal modello '{1}'.\n\nE stata aperta in Configurazione → Archiviazione cosi\npuoi aggiungere il disco e il supporto di installazione. Il MAC di rete e\nstato rigenerato per evitare conflitti con altre VM.",

    # ================================================================
    # task_progress.py
    # ================================================================
    "Iniciando…": "Avvio in corso…",
    "Cancelar": "Annulla",
    "La tarea falló.": "L'attivita e fallita.",
    "Cancelando, esperando al trabajador…":
        "Annullamento in corso, in attesa del worker…",
    "Cancelando…": "Annullamento in corso…",
    "Error:": "Errore:",

    # ================================================================
    # vm_lifecycle_mixin: edit_vm_label
    # ================================================================
    "Etiqueta de la VM": "Etichetta della VM",
    "Etiqueta - {0}": "Etichetta - {0}",
    "Grupo y color para <b>{0}</b>. El grupo es texto libre: escribe uno nuevo para crearlo. El color se aplica como fondo suave del ítem en la lista lateral.":
        "Gruppo e colore per <b>{0}</b>. Il gruppo e testo libero: scrivine uno nuovo per crearlo. Il colore viene applicato come sfondo tenue dell'elemento nell'elenco laterale.",
    "(sin grupo)": "(nessun gruppo)",
    "Grupo:": "Gruppo:",
    "Sin color": "Nessun colore",
    "Quitar etiqueta": "Rimuovi etichetta",
    "Guardar": "Salva",
    "Etiqueta": "Etichetta",
    "No se pudo guardar la etiqueta.\n\n{0}":
        "Impossibile salvare l'etichetta.\n\n{0}",

    # ================================================================
    # vm_lifecycle_mixin: show_qemu_command
    # ================================================================
    "Comando QEMU": "Comando QEMU",
    "La VM '{0}' todavia no se ha arrancado.\n\nEl comando QEMU se genera al pulsar Iniciar; vuelve a intentarlo despues del primer arranque.":
        "La VM '{0}' non e ancora stata avviata.\n\nIl comando QEMU viene generato al clic su Avvia; riprova dopo il primo avvio.",
    "No se pudo leer run_temp.sh.\n\n{0}":
        "Impossibile leggere run_temp.sh.\n\n{0}",
    "Comando QEMU - {0}": "Comando QEMU - {0}",
    "Contenido de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este es el comando exacto con el que QEMU esta ejecutando (o ejecuto por ultima vez) la VM.":
        "Contenuto di <code>run_temp.sh</code> per <b>{0}</b>.<br>Questo e il comando esatto con cui QEMU sta eseguendo (o ha eseguito l'ultima volta) la VM.",
    "Copiar al portapapeles": "Copia negli appunti",
    "Abrir carpeta de la VM": "Apri cartella della VM",
    "Abre la carpeta que contiene run_temp.sh, launch.log y los discos.":
        "Apre la cartella che contiene run_temp.sh, launch.log e i dischi.",

    # ================================================================
    # vm_lifecycle_mixin: edit_vm_notes
    # ================================================================
    "Notas de la VM": "Note della VM",
    "Notas - {0}": "Note - {0}",
    "Notas libres sobre <b>{0}</b>. Se guardan en <code>vm_config.ini</code> como <code>extra.notes</code> y aparecen como aviso amarillo en la pestana Resumen.":
        "Note libere su <b>{0}</b>. Vengono salvate in <code>vm_config.ini</code> come <code>extra.notes</code> e appaiono come avviso giallo nella scheda Panoramica.",
    "Ej.: instalado con VirtIO, probar snapshots tras actualizar los drivers; puerto 8080 redirigido al 80 del guest...":
        "Es.: installato con VirtIO, provare le istantanee dopo l'aggiornamento dei driver; porta 8080 reindirizzata alla 80 del guest...",
    "Borrar notas": "Cancella note",
    "Notas": "Note",
    "No se pudieron guardar las notas.\n\n{0}":
        "Impossibile salvare le note.\n\n{0}",

    # ================================================================
    # vm_lifecycle_mixin: stato / cartella / riepilogo
    # ================================================================
    "● Nueva VM": "● Nuova VM",
    "● Configurada": "● Configurata",
    "● Ejecutándose": "● In esecuzione",
    "● Error": "● Errore",
    "Carpeta": "Cartella",
    "Primero selecciona una máquina virtual existente.":
        "Seleziona prima una macchina virtuale esistente.",
    "Carpeta de la VM": "Cartella della VM",
    "No se pudo abrir la carpeta.\n\n{0}\n\n{1}":
        "Impossibile aprire la cartella.\n\n{0}\n\n{1}",
    "Resumen": "Panoramica",
    "No hay una máquina virtual seleccionada todavía.":
        "Nessuna macchina virtuale selezionata ancora.",
    "Resumen de la máquina virtual": "Riepilogo della macchina virtuale",

    # ================================================================
    # vm_lifecycle_mixin: import_vm + OVF import
    # ================================================================
    "Importar VM": "Importa VM",
    "¿Cómo quieres importar la máquina virtual?\n\n  • Desde carpeta: selecciona una carpeta que contenga vm_config.ini.\n  • Desde archivo: selecciona un .ova o .ovf (formato estándar OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip exportado previamente desde otra instalación de Virtual.Machine.":
        "Come vuoi importare la macchina virtuale?\n\n  • Da cartella: seleziona una cartella che contenga vm_config.ini.\n  • Da file: seleziona un .ova o .ovf (formato standard OVF, portatile su VirtualBox/VMware), o un .tar.gz / .tar / .zip esportato in precedenza da un'altra installazione di Virtual.Machine.",
    "\U0001f4c1 Desde carpeta…": "\U0001f4c1 Da cartella…",
    "\U0001f5dc\ufe0f Desde archivo…": "\U0001f5dc\ufe0f Da file…",
    "Selecciona la carpeta de la VM a importar":
        "Seleziona la cartella della VM da importare",
    "Selecciona el archivo a importar": "Seleziona il file da importare",
    "OVF/OVA (*.ova *.ovf);;Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;Todos los archivos (*)":
        "OVF/OVA (*.ova *.ovf);;File VM impacchettati (*.tar.gz *.tgz *.tar *.zip);;Tutti i file (*)",
    "Formato de archivo no reconocido. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.":
        "Formato di file non riconosciuto. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.",
    "La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\nAsegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.":
        "La cartella selezionata non contiene vm_config.ini:\n\n{0}\n\nAssicurati di scegliere la cartella radice della VM, non una sottocartella.",
    "Nombre para la VM importada:\n\n(se importará desde {0})":
        "Nome per la VM importata:\n\n(verra importata da {0})",
    "Nombre inválido.": "Nome non valido.",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Esiste gia una VM chiamata '{0}'.\n\nSostituirla? (quella esistente verra eliminata)",
    "Copiando/desempaquetando en el sistema de archivos del destino (no en /tmp)…":
        "Copia/decompressione nel filesystem di destinazione (non in /tmp)…",
    "Desempaquetando archivo…": "Decompressione file…",
    "Extrayendo {0}/{1}…": "Estrazione {0}/{1}…",
    "El archivo no contiene ninguna VM válida (no se encontró vm_config.ini).":
        "Il file non contiene nessuna VM valida (vm_config.ini non trovato).",
    "Importación completada.": "Importazione completata.",
    "Copiando {0}": "Copia di {0}",
    "VM '{0}' importada correctamente.\n\nRevisa su configuración en la pestaña Configuración antes de arrancarla, especialmente si la importaste desde otro host: puede referenciar rutas que no existan aquí (carpetas compartidas, ISOs externas, dispositivos de passthrough).":
        "VM '{0}' importata correttamente.\n\nControlla la sua configurazione nella scheda Configurazione prima di avviarla, soprattutto se l'hai importata da un altro host: potrebbe fare riferimento a percorsi che non esistono qui (cartelle condivise, ISO esterne, dispositivi in passthrough).",

    # ================================================================
    # vm_lifecycle_mixin: export_vm
    # ================================================================
    "Exportar VM": "Esporta VM",
    "Primero selecciona una máquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "La VM '{0}' está {1}.\n\nSe recomienda apagarla antes de exportar: si está corriendo, los discos pueden estar en un estado inconsistente (cambios sin sincronizar a disco, locks activos…).\n\n¿Continuar de todos modos?":
        "La VM '{0}' e {1}.\n\nSi consiglia di spegnerla prima di esportare: se e in esecuzione, i dischi potrebbero essere in uno stato incoerente (modifiche non sincronizzate su disco, lock attivi…).\n\nContinuare comunque?",
    "Copia de carpeta (más rápido, editable)":
        "Copia di cartella (piu veloce, modificabile)",
    "Archivo .tar.gz (comprimido, portable)":
        "File .tar.gz (compresso, portatile)",
    "Archivo .zip (compatible con Windows)":
        "File .zip (compatibile con Windows)",
    "Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)":
        "File .ova (Open Virtual Appliance, portatile su VirtualBox/VMware)",
    "Descriptor .ovf + discos sueltos (carpeta)":
        "Descrittore .ovf + dischi sfusi (cartella)",
    "Formato para exportar '{0}':": "Formato per esportare '{0}':",
    "Elige la carpeta donde crear la copia":
        "Scegli la cartella dove creare la copia",
    "En la carpeta destino ya existe '{0}'.\n\n¿Sobrescribir? (se borrará la carpeta destino existente)":
        "Nella cartella di destinazione esiste gia '{0}'.\n\nSovrascrivere? (la cartella di destinazione esistente verra eliminata)",
    "Guardar archivo de exportación": "Salva file di esportazione",
    "Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)":
        "File tar.gz (*.tar.gz);;File zip (*.zip)",
    "Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)":
        "File zip (*.zip);;File tar.gz (*.tar.gz)",
    "El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?":
        "Il file di destinazione esiste gia:\n{0}\n\nSovrascrivere?",
    "Confirmar exportación": "Conferma esportazione",
    "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Contenido: {2} archivo(s), {3}\n  • Destino: {4}\n\nLos archivos de bloqueo (pids, sockets) y logs se omitirán.":
        "Esporta '{0}' come:\n\n  • Formato: {1}\n  • Contenuto: {2} file, {3}\n  • Destinazione: {4}\n\nI file di lock (pid, socket) e i log verranno omessi.",
    "No se pudo completar la exportación.\n\n{0}":
        "Impossibile completare l'esportazione.\n\n{0}",
    "{0} archivo(s), {1} en total": "{0} file, {1} in totale",
    "Exportación cancelada por el usuario.":
        "Esportazione annullata dall'utente.",
    "Formato de exportación desconocido: {0}":
        "Formato di esportazione sconosciuto: {0}",
    "Exportación completada ({0} archivo(s)).":
        "Esportazione completata ({0} file).",
    "'{0}' exportada correctamente.\n\nDestino: {1}":
        "'{0}' esportata correttamente.\n\nDestinazione: {1}",

    # ================================================================
    # vm_lifecycle_mixin: OVF/OVA raise e messaggi
    # ================================================================
    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la carpeta de la VM ({0}). Sin este archivo la VM no tiene sistema operativo que exportar.":
        "VM macOS: mac_hdd_ng.qcow2 non trovato nella cartella della VM ({0}). Senza questo file la VM non ha un sistema operativo da esportare.",
    "La VM no tiene discos adjuntos que exportar. Añade al menos un disco en Configuración → Almacenamiento.":
        "La VM non ha dischi collegati da esportare. Aggiungi almeno un disco in Configurazione → Archiviazione.",
    "qemu-img convert -c falló para '{0}': {1}":
        "qemu-img convert -c fallito per '{0}': {1}",
    "El aplanado+compresión de '{0}' no produjo un archivo válido.":
        "L'appiattimento+compressione di '{0}' non ha prodotto un file valido.",
    "Importar OVA": "Importa OVA",
    "El archivo .ova no contiene ningún descriptor .ovf.":
        "Il file .ova non contiene nessun descrittore .ovf.",
    "Importar OVF": "Importa OVF",
    "El archivo .ovf está vacío.": "Il file .ovf e vuoto.",
    "No se pudo leer el descriptor.\n\n{0}":
        "Impossibile leggere il descrittore.\n\n{0}",
    "El descriptor OVF no se pudo interpretar.\n\n{0}":
        "Il descrittore OVF non puo essere interpretato.\n\n{0}",
    "No se pudo completar la importación.\n\n{0}":
        "Impossibile completare l'importazione.\n\n{0}",
    "Extrayendo y preparando el OVF/OVA...":
        "Estrazione e preparazione dell'OVF/OVA...",
    "Importar OVF/OVA": "Importa OVF/OVA",

    # ================================================================
    # vm_lifecycle_mixin: clona / scollega
    # ================================================================
    "Clonar máquina virtual": "Clona macchina virtuale",
    "Nombre para el clon de '{0}':": "Nome per il clone di '{0}':",
    "Debes escribir un nombre para el clon.":
        "Devi inserire un nome per il clone.",
    "Nombre ya existente": "Nome gia esistente",
    "La máquina virtual '{0}' ya existe en el listado.\n\nElige otro nombre para el clon.":
        "La macchina virtuale '{0}' esiste gia nell'elenco.\n\nScegli un altro nome per il clone.",
    "Ese nombre no puede utilizarse para una máquina virtual.":
        "Questo nome non puo essere usato per una macchina virtuale.",
    "Clonar VM": "Clona VM",
    "¿Qué tipo de clon quieres crear a partir de <b>{0}</b>?<br><br><b>Clon completo</b><br>Copia íntegra de todos los discos. Totalmente independiente del original; ocupa el mismo espacio que la VM original.<br><br><b>Clon enlazado</b><br>El disco base se comparte mediante un <i>backing file</i> QCOW2. La nueva VM solo guarda los cambios, así que ocupa muy poco. <b>Depende del original</b>: si se borra o se mueve el original, el clon se rompe.<br>El backing se guarda con <b>ruta relativa</b> para que puedas mover o copiar la carpeta <code>VirtualMachines/</code> entera a otro host sin romper nada.<br><br><b>Importante:</b> una vez que el clon arranque por primera vez, los cambios que hagas DESPUÉS en el original <b>NO se verán</b> en el clon: la vista de su sistema de archivos queda anclada al estado del primer arranque (los bloques que el clon ya escribió no vuelven a consultarse en el backing). Trata el original como de solo lectura mientras el clon exista, o desenlaza el clon con <b>🧬 Desenlazar</b> para independizarlo.":
        "Che tipo di clone vuoi creare da <b>{0}</b>?<br><br><b>Clone completo</b><br>Copia integrale di tutti i dischi. Totalmente indipendente dall'originale; occupa lo stesso spazio della VM originale.<br><br><b>Clone collegato</b><br>Il disco di base viene condiviso tramite un <i>backing file</i> QCOW2. La nuova VM salva solo le modifiche, quindi occupa pochissimo. <b>Dipende dall'originale</b>: se l'originale viene eliminato o spostato, il clone si rompe.<br>Il backing viene salvato con un <b>percorso relativo</b> per consentirti di spostare o copiare l'intera cartella <code>VirtualMachines/</code> su un altro host senza rompere nulla.<br><br><b>Importante:</b> una volta che il clone si avvia per la prima volta, le modifiche che fai DOPO nell'originale <b>NON saranno visibili</b> nel clone: la vista del suo filesystem rimane ancorata allo stato del primo avvio (i blocchi che il clone ha gia scritto non vengono piu consultati nel backing). Considera l'originale come di sola lettura finche il clone esiste, oppure scollega il clone con <b>🧬 Scollega</b> per renderlo indipendente.",
    "Clon completo": "Clone completo",
    "Clon enlazado": "Clone collegato",
    "No se pudo copiar la carpeta de la VM.\n\n{0}":
        "Impossibile copiare la cartella della VM.\n\n{0}",
    "La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}":
        "La VM e stata copiata ma il suo vm_config.ini non puo essere riscritto.\n\n{0}",
    "Clon creado": "Clone creato",
    "La máquina virtual '{0}' fue clonada correctamente (clon completo).\n\nSe han regenerado las direcciones MAC y los IDs internos de los discos para que no choquen con la VM original.":
        "La macchina virtuale '{0}' e stata clonata correttamente (clone completo).\n\nGli indirizzi MAC e gli ID interni dei dischi sono stati rigenerati per non entrare in conflitto con la VM originale.",
    "Clon enlazado con original en ejecución":
        "Clone collegato con originale in esecuzione",
    "El original de este clon ('{0}') está corriendo.\n\nArrancar original y clon a la vez puede dar resultados impredecibles:\n\n  • El clon lee del disco del original los bloques que no ha modificado. Si el original escribe algo mientras el clon corre, el clon puede leer estados intermedios.\n  • La vista del sistema de archivos del clon ya está anclada al estado de su primer arranque para los bloques de metadatos, así que los cambios nuevos del original probablemente no se vean, pero el riesgo de lectura inconsistente sigue ahí.\n\nRecomendaciones:\n  • Apaga el original antes de arrancar el clon (o al revés).\n  • O desenlaza el clon con '🧬 Desenlazar' para que sea totalmente independiente.\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "L'originale di questo clone ('{0}') e in esecuzione.\n\nAvviare originale e clone contemporaneamente puo dare risultati imprevedibili:\n\n  • Il clone legge dal disco dell'originale i blocchi che non ha modificato. Se l'originale scrive qualcosa mentre il clone e in esecuzione, il clone puo leggere stati intermedi.\n  • La vista del filesystem del clone e gia ancorata allo stato del suo primo avvio per i blocchi di metadati, quindi le nuove modifiche dell'originale probabilmente non saranno visibili, ma il rischio di lettura incoerente rimane.\n\nRaccomandazioni:\n  • Spegni l'originale prima di avviare il clone (o viceversa).\n  • Oppure scollega il clone con '🧬 Scollega' per renderlo totalmente indipendente.\n\nQuesto avviso non apparira piu per questa VM in questa sessione.",
    "Clon enlazado con backing roto":
        "Clone collegato con backing rotto",
    "Este clon enlazado espera el backing en:\n\n    {0}\n\nResuelto contra su carpeta queda en:\n\n    {1}\n\nEse archivo no existe. La VM original ('{2}') probablemente se movió o se borró.\n\nQEMU fallará al arrancar con:\n    Could not open backing file: No such file or directory\n\nOpciones:\n  • Mueve también la VM original de vuelta a su carpeta, o\n  • Copia la carpeta 'VirtualMachines/' entera (con original\n    y clon juntos) a la nueva ubicación, o\n  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n    para independizar este clon (puede fallar si el backing\n    ya no está disponible).\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "Questo clone collegato si aspetta il backing in:\n\n    {0}\n\nRisolto rispetto alla sua cartella diventa:\n\n    {1}\n\nQuel file non esiste. La VM originale ('{2}') e stata probabilmente spostata o eliminata.\n\nQEMU fallira all'avvio con:\n    Could not open backing file: No such file or directory\n\nOpzioni:\n  • Riporta anche la VM originale nella sua cartella, oppure\n  • Copia l'intera cartella 'VirtualMachines/' (con originale\n    e clone insieme) nella nuova posizione, oppure\n  • Se puoi ancora, usa '🧬 Scollega' nella scheda Panoramica\n    per rendere questo clone indipendente (potrebbe fallire se il backing\n    non e piu disponibile).\n\nQuesto avviso non apparira piu per questa VM in questa sessione.",
    "No se pudo determinar el disco principal de la VM original.\n\nEl clon enlazado necesita un disco base QCOW2 sobre el que\ncrear el backing file. Si la VM no tiene discos, usa\n'Clon completo'.":
        "Impossibile determinare il disco principale della VM originale.\n\nIl clone collegato necessita di un disco di base QCOW2 su cui\ncreare il backing file. Se la VM non ha dischi, usa\n'Clone completo'.",
    "No se pudo inspeccionar el disco original.\n\n{0}":
        "Impossibile ispezionare il disco originale.\n\n{0}",
    "El disco principal de la VM original está en formato {0}.\n\nEl clon enlazado solo funciona con QCOW2 (necesita backing\nfile). Usa 'Clon completo' si quieres copiar el disco tal cual.":
        "Il disco principale della VM originale e in formato {0}.\n\nIl clone collegato funziona solo con QCOW2 (necessita del backing\nfile). Usa 'Clone completo' se vuoi copiare il disco cosi com'e.",
    "No se pudo crear la carpeta del clon.\n\n{0}":
        "Impossibile creare la cartella del clone.\n\n{0}",
    "qemu-img create falló.\n\n{0}": "qemu-img create fallito.\n\n{0}",
    "No se pudo crear el delta QCOW2.\n\n{0}":
        "Impossibile creare il delta QCOW2.\n\n{0}",
    "El backing file quedó guardado como ruta ABSOLUTA, lo que haría el clon no portable.\n\nSe ha abortado la operación para no dejar un clon defectuoso. Reporta esto como bug.":
        "Il backing file e stato salvato come percorso ASSOLUTO, cosa che renderebbe il clone non portatile.\n\nL'operazione e stata interrotta per non lasciare un clone difettoso. Segnala questo come bug.",
    "No se pudieron copiar los archivos auxiliares.\n\n{0}":
        "Impossibile copiare i file ausiliari.\n\n{0}",
    "El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n{0}\n\nRevisa manualmente el archivo antes de usar la VM.":
        "Il clone e stato creato ma il suo vm_config.ini non puo essere riscritto.\n\n{0}\n\nControlla manualmente il file prima di usare la VM.",
    "La máquina virtual '{0}' fue clonada correctamente (clon enlazado).\n\nEl disco base se comparte con el original mediante un backing\nfile QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\npero DEPENDE del original:\n\n  • Si borras o mueves la VM original, el clon se rompe.\n  • Una vez que el clon arranque por primera vez, los cambios\n    que hagas DESPUÉS en el original NO se verán en el clon:\n    la vista del sistema de archivos queda anclada al estado\n    del primer arranque. Trata el original como de solo lectura\n    mientras el clon exista.\n  • Los snapshots completos (RAM) no funcionarán en este clon\n    — solo de disco. QEMU no puede restaurar (loadvm) un\n    snapshot completo sobre un QCOW2 con backing file.\n  • Los snapshots del clon no son reproducibles mientras el\n    original pueda cambiar: al restaurar, se mezcla el delta\n    guardado con el estado ACTUAL del backing.\n  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n    apagado.\n\nPara mover o copiar la estructura completa a otro host,\nllévate la carpeta 'VirtualMachines/' entera.":
        "La macchina virtuale '{0}' e stata clonata correttamente (clone collegato).\n\nIl disco di base viene condiviso con l'originale tramite un backing\nfile QCOW2 con percorso relativo. Il clone occupa pochissimo spazio,\nma DIPENDE dall'originale:\n\n  • Se elimini o sposti la VM originale, il clone si rompe.\n  • Una volta che il clone si avvia per la prima volta, le modifiche\n    che fai DOPO nell'originale NON saranno visibili nel clone:\n    la vista del filesystem rimane ancorata allo stato\n    del primo avvio. Considera l'originale come sola lettura\n    finche il clone esiste.\n  • Le istantanee complete (RAM) non funzioneranno su questo clone\n    — solo disco. QEMU non puo ripristinare (loadvm) un'istantanea\n    completa su un QCOW2 con backing file.\n  • Le istantanee del clone non sono riproducibili finche\n    l'originale puo cambiare: al ripristino, il delta salvato viene\n    mescolato con lo stato ATTUALE del backing.\n  • Se vuoi renderlo indipendente, usa '🧬 Scollega' quando e\n    spento.\n\nPer spostare o copiare l'intera struttura su un altro host,\nporta con te l'intera cartella 'VirtualMachines/'.",

    # ================================================================
    # vm_lifecycle_mixin: scollega / elimina
    # ================================================================
    "Desenlazar clon": "Scollega clone",
    "Esta VM no es un clon enlazado, no hay nada que desenlazar.":
        "Questa VM non e un clone collegato, non c'e nulla da scollegare.",
    "La VM '{0}' está encendida.\n\nApágala antes de desenlazarla: con QEMU activo el archivo\nestá bloqueado y el convert no puede reemplazarlo.":
        "La VM '{0}' e accesa.\n\nSpegnila prima di scollegarla: con QEMU attivo il file\nresta bloccato e il convert non puo sostituirlo.",
    "No se encontró el disco principal del clon.":
        "Il disco principale del clone non e stato trovato.",
    "Se convertirá el disco principal del clon <b>{0}</b> en un QCOW2 <b>autónomo</b>.<br><br>Después de esto, el clon deja de depender del original y puede moverse o copiarse por separado.<br><br><b>Requiere:</b><br>&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>&nbsp;&nbsp;• La VM apagada (ya lo está).<br>&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>El resultado se verifica como QCOW2 válido y se reemplaza atómicamente. Si algo falla a mitad, el archivo original del clon queda intacto.":
        "Il disco principale del clone <b>{0}</b> verra convertito in un QCOW2 <b>autonomo</b>.<br><br>Dopo di che, il clone non dipende piu dall'originale e puo essere spostato o copiato separatamente.<br><br><b>Richiede:</b><br>&nbsp;&nbsp;• Spazio libero sull'host (~1,1× la dimensione del disco).<br>&nbsp;&nbsp;• La VM spenta (lo e gia).<br>&nbsp;&nbsp;• Non chiudere l'applicazione durante il processo.<br><br>Il risultato viene verificato come QCOW2 valido e sostituito atomicamente. Se qualcosa fallisce a meta, il file originale del clone rimane intatto.",
    "Desenlazado cancelado por el usuario.":
        "Scollegamento annullato dall'utente.",
    "Desenlazado": "Scollegato",
    "El clon '{0}' ya es autónomo.\n\nTamaño antes: {1}\nTamaño después: {2}\n\nPuedes mover la VM sin llevarte la original.":
        "Il clone '{0}' ora e autonomo.\n\nDimensione prima: {1}\nDimensione dopo: {2}\n\nPuoi spostare la VM senza portarti dietro l'originale.",
    "No se pudo desenlazar el clon.\n\n{0}":
        "Impossibile scollegare il clone.\n\n{0}",
    "Convirtiendo el clon en un QCOW2 autónomo…":
        "Conversione del clone in QCOW2 autonomo…",
    "Eliminar VM": "Elimina VM",
    "Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n":
        "Verrà eliminata solo la cartella della macchina virtuale:\n\n{0}\n\n",
    "Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n":
        "I seguenti supporti sono fuori dalla cartella della VM e NON verranno eliminati:\n",
    "\u26a0 ESTA VM ES EL ORIGINAL DE {0} CLON(ES) ENLAZADO(S):\n":
        "\u26a0 QUESTA VM E L'ORIGINALE DI {0} CLONE(I) COLLEGATO(I):\n",
    "\n\nSi continúas, esos clones quedarán inutilizables (su backing file ya no existirá).\n\nSe recomienda desenlazarlos primero: selecciona cada clon y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n":
        "\n\nSe continui, quei cloni diventeranno inutilizzabili (il loro backing file non esistera piu).\n\nSi consiglia di scollegarli prima: seleziona ogni clone e premi '🧬 Scollega' nella sua scheda Panoramica.\n\n",
    "¿Deseas continuar?": "Vuoi continuare?",
    "Eliminar máquina virtual": "Elimina macchina virtuale",
    "No se pudo eliminar '{0}'.\n\n{1}":
        "Impossibile eliminare '{0}'.\n\n{1}",

    # ================================================================
    # guest_integration_mixin.py
    # ================================================================
    "Montaje automático": "Automontaggio",
    "La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n{0}\n\nComprueba que qemu-guest-agent esté instalado y ejecutándose en el guest (pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.":
        "La VM e stata avviata, ma non e stato possibile configurare l'automontaggio nel SO.\n\n{0}\n\nVerifica che qemu-guest-agent sia installato e in esecuzione nel guest (scheda Guest Tools). Una volta installato, il montaggio verra fatto automaticamente al prossimo avvio della VM.",
    "La carpeta compartida VirtioFS ya está conectada a la VM.\n\nEn Linux el dispositivo debe montarse dentro del guest. En un LiveCD no es posible hacerlo de forma persistente desde el host sin un agente instalado en el guest.\n\nComando(s):\n\n":
        "La cartella condivisa VirtioFS e gia collegata alla VM.\n\nSu Linux il dispositivo deve essere montato dentro il guest. Su un LiveCD non e possibile farlo in modo persistente dall'host senza un agente installato nel guest.\n\nComando(i):\n\n",
    "\n\nEn una instalación Linux permanente podremos añadir automontaje mediante fstab/systemd en una versión posterior.":
        "\n\nSu un'installazione Linux permanente potremo aggiungere l'automontaggio tramite fstab/systemd in una versione successiva.",
    "Carpeta compartida lista": "Cartella condivisa pronta",
    "Guest Tools": "Guest Tools",
    "Carpeta:\n{0}": "Cartella:\n{0}",
    "Generando ISO de Guest Tools…": "Generazione ISO Guest Tools…",
    "ISO creada.": "ISO creata.",
    "ISO disponible: {0}": "ISO disponibile: {0}",
    "Crear ISO de Guest Tools": "Crea ISO Guest Tools",
    "No se pudo crear la ISO.\n\n{0}":
        "Impossibile creare l'ISO.\n\n{0}",
    "La ISO se guarda en la carpeta GuestTools.":
        "L'ISO viene salvata nella cartella GuestTools.",
    "Selecciona (o crea) una VM primero.":
        "Seleziona (o crea) prima una VM.",
    "Creando ISO de Guest Tools…": "Creazione ISO Guest Tools…",
    "Guest Tools — Adjuntar a la VM": "Guest Tools — Collega alla VM",
    "No se pudo crear ni adjuntar la ISO.\n\n{0}":
        "Impossibile creare o collegare l'ISO.\n\n{0}",
    "Se creará la ISO y se adjuntará como CD/DVD a esta VM.":
        "L'ISO verra creata e collegata come CD/DVD a questa VM.",
    "Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD.":
        "Questa VM ha gia l'ISO Guest Tools collegata come CD/DVD.",
    "ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\nEn el próximo arranque, dentro del guest: monta la unidad y ejecuta\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).":
        "ISO Guest Tools collegata a questa VM come CD/DVD.\n\nAl prossimo avvio, dentro il guest: monta l'unita ed esegui\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (come Amministratore).",
    "No se pudo adjuntar la ISO.\n\n{0}":
        "Impossibile collegare l'ISO.\n\n{0}",
    "Estado: canal no disponible. Enciende la VM con Guest Agent activado.":
        "Stato: canale non disponibile. Avvia la VM con il Guest Agent attivato.",
    "Estado: consultando al Guest Agent...":
        "Stato: interrogazione del Guest Agent in corso...",
    "Estado: sin respuesta del guest agent ({0}).":
        "Stato: nessuna risposta dal guest agent ({0}).",
    "Estado: QEMU Guest Agent responde correctamente (v{0}).":
        "Stato: QEMU Guest Agent risponde correttamente (v{0}).",
    "Estado: QGA respondió con un error: {0}":
        "Stato: QGA ha risposto con un errore: {0}",
    "Estado: canal QGA presente; pulsa Probar conexión.":
        "Stato: canale QGA presente; premi Testa connessione.",
    "Estado: canal QGA no activo en este momento.":
        "Stato: canale QGA non attivo in questo momento.",
    "Manual": "Manuale",
    "Automático al iniciar SO": "Automatico all'avvio del SO",
    "Automático bajo demanda": "Automatico su richiesta",
    "Solo lectura": "Sola lettura",
    "Lectura / escritura": "Lettura / scrittura",
    "Carpeta compartida": "Cartella condivisa",
    "Seleccionar carpeta del host": "Seleziona cartella dell'host",
    "Carpeta del host:": "Cartella dell'host:",
    "Etiqueta / guest:": "Etichetta / guest:",
    "Método:": "Metodo:",
    "Automático": "Automatico",
    "Montaje en el guest:": "Montaggio nel guest:",
    "Acceso:": "Accesso:",
    "La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.":
        "La politica di montaggio e la stessa per tutti i SO: Manuale, Automatico all'avvio del SO o Automatico su richiesta. Il meccanismo effettivo di montaggio si adatta al SO guest e ai suoi componenti di integrazione. Su un LiveCD, il montaggio persistente di solito non puo essere configurato dall'host.",
    "Aceptar": "OK",
    "La carpeta del host no existe o no es un directorio.":
        "La cartella dell'host non esiste o non e una directory.",
    "Desactivado": "Disattivato",
    "Host → SO invitado": "Host → SO guest",
    "SO invitado → Host": "SO guest → Host",
    "Bidireccional": "Bidirezionale",
    "No se añadirá ningún canal de clipboard.":
        "Nessun canale appunti verra aggiunto.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK: bidirezionale. Richiede spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS: integrazione appunti in sospeso.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Seleziona una VM per verificare l'integrazione disponibile.",
    "Se activará automáticamente al iniciar la VM.":
        "Verrà attivato automaticamente all'avvio della VM.",
    "No se activa.": "Non viene attivato.",
    "Configuración actual: {0}. {1} {2}":
        "Configurazione attuale: {0}. {1} {2}",
    "Clipboard": "Appunti",
    "Configuración del clipboard guardada para esta VM.":
        "Configurazione degli appunti salvata per questa VM.",
    "Compartir": "Condividi",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Configurazione salvata. Verra applicata al prossimo avvio.",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Mancano:\n\n• {0}\n\nVuoi installarle ora usando il gestore di pacchetti di sistema?",

    # ================================================================
    # mac_recovery_mixin.py
    # ================================================================
    "Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.":
        "Per macOS usa 'Scarica System Recovery'. Apple distribuisce l'installer completo come applicazione; il flusso Recovery di OSX-KVM e il metodo integrato in questo gestore.",
    "Android-x86 / Bliss OS no tienen descarga automática. Descarga la ISO desde https://www.android-x86.org/download.html o https://blissos.org/ y selecciónala en Plataforma → Android.":
        "Android-x86 / Bliss OS non supportano il download automatico. Scarica l'ISO da https://www.android-x86.org/download.html o https://blissos.org/ e selezionala in Piattaforma → Android.",
    "System Recovery de macOS — {0}": "System Recovery di macOS — {0}",
    "La imagen se descarga y verifica directamente en la carpeta de la VM.":
        "L'immagine viene scaricata e verificata direttamente nella cartella della VM.",
    "Iniciando descarga…": "Avvio del download…",
    "Recovery preparado.": "Recovery pronto.",
    "Apple no devolvió una sesión de Recovery válida.":
        "Apple non ha restituito una sessione Recovery valida.",
    "Apple no devolvió todos los datos del Recovery: {0}":
        "Apple non ha restituito tutti i dati del Recovery: {0}",
    "{0} — {1:.1f} MB descargados": "{0} — {1:.1f} MB scaricati",
    "{0} — 100%": "{0} — 100%",
    "El chunklist de System Recovery está incompleto.":
        "Il chunklist di System Recovery e incompleto.",
    "Cabecera de chunklist de Apple no válida.":
        "Header del chunklist Apple non valido.",
    "Chunklist de Apple no válido.": "Chunklist Apple non valido.",
    "Chunklist truncado en el bloque {0}.":
        "Chunklist troncato al blocco {0}.",
    "La verificación del Recovery falló en el bloque {0}.":
        "La verifica del Recovery e fallita al blocco {0}.",
    "La imagen Recovery contiene datos adicionales no descritos por el chunklist.":
        "L'immagine Recovery contiene dati aggiuntivi non descritti dal chunklist.",
    "No hay una carpeta de VM seleccionada.":
        "Nessuna cartella VM selezionata.",
    "Consultando Apple…": "Interrogazione di Apple…",
    "Descargando chunklist…": "Download del chunklist…",
    "Descargando chunklist": "Download del chunklist",
    "Descargando BaseSystem.dmg…": "Download di BaseSystem.dmg…",
    "Descargando BaseSystem.dmg": "Download di BaseSystem.dmg",
    "Verificando integridad…": "Verifica dell'integrita…",
    "Verificación completada.": "Verifica completata.",
    "No se encontró 'dmg2img' y no se pudo instalar automáticamente. Instálalo con el gestor de paquetes (en Arch/CachyOS: paru -S dmg2img).":
        "'dmg2img' non trovato e non e stato possibile installarlo automaticamente. Installalo con il gestore di pacchetti (su Arch/CachyOS: paru -S dmg2img).",
    "Convirtiendo BaseSystem.dmg → BaseSystem.img…":
        "Conversione di BaseSystem.dmg → BaseSystem.img…",
    "dmg2img no pudo preparar BaseSystem.img.\n{0}":
        "dmg2img non ha potuto preparare BaseSystem.img.\n{0}",
    "dmg2img terminó pero BaseSystem.img no existe o está vacío.":
        "dmg2img e terminato ma BaseSystem.img non esiste o e vuoto.",

    # ================================================================
    # install_flow_mixin.py
    # ================================================================
    "No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.":
        "qemu-system-x86_64 non trovato nel PATH. Esegui ./run.sh (installa le dipendenze di sistema) oppure installa qemu-system-x86 / qemu-kvm.",
    "/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.":
        "/dev/kvm non e disponibile; QEMU potrebbe funzionare senza accelerazione KVM.",
    "El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.":
        "L'utente non ha i permessi di lettura/scrittura su /dev/kvm.",
    "No se detectó un firmware OVMF conocido para Secure Boot.":
        "Nessun firmware OVMF conosciuto rilevato per Secure Boot.",
    "El dispositivo de almacenamiento '{0}' apunta a un archivo que ya no existe: {1}":
        "Il dispositivo di archiviazione '{0}' punta a un file che non esiste piu: {1}",
    "La carpeta compartida '{0}' apunta a una ruta del host que ya no existe: {1}":
        "La cartella condivisa '{0}' punta a un percorso dell'host che non esiste piu: {1}",
    "Solo quedan {0} GB libres donde vive esta VM; puede fallar durante el uso.":
        "Restano solo {0} GB liberi dove risiede questa VM; potrebbe fallire durante l'uso.",
    "El orden de arranque prioriza el CD/DVD, pero el disco '{0}' ya tiene datos (~{1} GB). Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo.":
        "L'ordine di avvio da priorita al CD/DVD, ma il disco '{0}' contiene gia dati (~{1} GB). Se il sistema e gia installato, questo potrebbe tentare di reinstallarlo invece di avviarlo.",
    "Advertencia": "Avviso",
    "Debe indicar un nombre para la máquina virtual.":
        "Devi indicare un nome per la macchina virtuale.",
    'El nombre no puede contener: \\ / : * ? " < > |':
        'Il nome non puo contenere: \\ / : * ? " < > |',
    "La VM ya está corriendo": "La VM e gia in esecuzione",
    "'{0}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco (dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\nDetén la VM actual antes de volver a iniciarla.":
        "'{0}' ha gia un processo QEMU attivo. Avviarla di nuovo puo corrompere il disco (due processi che scrivono sullo stesso file) o entrare in conflitto con i socket gia in uso.\n\nFerma la VM attuale prima di riavviarla.",
    "No se puede iniciar la VM": "Impossibile avviare la VM",
    "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.":
        "Manca QEMU nel sistema. Installa qemu-system-x86 e riprova.",
    "Revisión previa": "Controllo preliminare",
    "¿Deseas continuar de todos modos?": "Vuoi continuare comunque?",
    "Configuración incompatible": "Configurazione incompatibile",
    "Secure Boot requiere UEFI (OVMF).": "Secure Boot richiede UEFI (OVMF).",
    "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.":
        "TPM 2.0 non si applica al flusso attuale di macOS/OSX-KVM.",
    "Dependencias faltantes": "Dipendenze mancanti",
    "No se pudieron preparar automáticamente las dependencias necesarias.\n\n{0}":
        "Non e stato possibile preparare automaticamente le dipendenze necessarie.\n\n{0}",
    "System Recovery de macOS": "System Recovery di macOS",
    "No se pudo preparar System Recovery antes de iniciar la VM.\n\n{0}":
        "Impossibile preparare System Recovery prima di avviare la VM.\n\n{0}",
    "Disco existente con otra configuración":
        "Disco esistente con un'altra configurazione",
    "Ya existe un disco para '{0}' con {1} / {2} / {3}, distinto a lo solicitado ({4} / {5} / {6}).\n\n¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n(\"No\" conserva el disco existente tal como está.)":
        "Esiste gia un disco per '{0}' con {1} / {2} / {3}, diverso da quello richiesto ({4} / {5} / {6}).\n\nVuoi eliminarlo e crearne uno nuovo con i parametri attuali?\n(\"No\" mantiene il disco esistente cosi com'e.)",
    "Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.":
        "Devi indicare un percorso valido del file ISO di Windows oppure selezionare 'Scarica automaticamente l'installer di Windows' nel CD/DVD.",
    "Android": "Android",
    "Debes configurar la ISO de Android-x86 o Bliss OS en Configuración → Almacenamiento → CD / DVD.\n\nDescárgala de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAñade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente».":
        "Devi configurare l'ISO di Android-x86 o Bliss OS in Configurazione → Archiviazione → CD / DVD.\n\nScaricala da:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAggiungi un'unita CD/DVD e scegli «Usa ISO/IMG/DMG esistente».",
    "Error": "Errore",
    "No se encuentra la carpeta 'OSX-KVM'.":
        "La cartella 'OSX-KVM' non e stata trovata.",
    "Error al guardar configuración": "Errore durante il salvataggio della configurazione",
    "No se pudo guardar vm_config.ini para '{0}': {1}":
        "Impossibile salvare vm_config.ini per '{0}': {1}",
    "No se puede preparar el passthrough USB": "Impossibile preparare il passthrough USB",
    "La VM no se iniciará hasta resolver el acceso al USB.\n\n{0}\n\nNo se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.":
        "La VM non si avviera finche l'accesso USB non sara risolto.\n\n{0}\n\nNon selezionare un Root Hub. La chiavetta USB deve essere smontata dall'host.",
    "Instalador del sistema operativo": "Installer del sistema operativo",
    "La descarga se realiza dentro de la carpeta de la VM.":
        "Il download viene eseguito nella cartella della VM.",
    "Máquina virtual iniciada.": "Macchina virtuale avviata.",
    "Descarga cancelada por el usuario.": "Download annullato dall'utente.",
    "QEMU terminó con error. Revisa la consola de progreso.":
        "QEMU e terminato con errore. Controlla la console di avanzamento.",

    # ================================================================
    # api_mixin.py
    # ================================================================
    "Peticiones recientes": "Richieste recenti",
}
