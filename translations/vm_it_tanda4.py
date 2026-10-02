# -*- coding: utf-8 -*-
"""vm_it_tanda4 - Traduzioni in italiano - Tanda 4.

Copre:
  - Console Grafica: barra pulsanti, zoom, modalita presentazione,
    schermo intero del visualizzatore, combo uscita.
  - Console di Avanzamento: filtri, pulsanti log, salute VM,
    pulizia processi orfani.
  - Pannello Aiuto.
  - console_backend.py (descrizioni modalita VNC/SPICE).
  - console_ui_mixin.py (blocco aiuto grande con pro/contro).
"""

TRANSLATIONS = {

    # ================================================================
    # Console Grafica: barra superiore
    # ================================================================
    "La VM no está corriendo.": "La VM non e in esecuzione.",
    "\u2197 Abrir en ventana externa": "\u2197 Apri in finestra esterna",
    "Lanza el visor externo del protocolo configurado en Pantalla,\n"
    "aunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez.":
        "Avvia il visualizzatore esterno del protocollo configurato in Schermo,\n"
        "anche se la modalita e 'integrata'. Utile per avere entrambe le viste contemporaneamente.",
    "Externos en pantalla completa": "Esterni a schermo intero",
    "Cuando está marcado, los visores externos (los que abre el\n"
    "botón 'Abrir en ventana externa' o el modo 'Ventana externa'\n"
    "de Configuración → Pantalla) se lanzan ocupando toda la\n"
    "pantalla. NO afecta al visor embebido (VNC dentro de la app):\n"
    "para ese, usa el botón 'Pantalla completa del visor'.":
        "Quando selezionato, i visualizzatori esterni (quelli aperti dal\n"
        "pulsante 'Apri in finestra esterna' o dalla modalita 'Finestra esterna'\n"
        "di Configurazione → Schermo) vengono avviati occupando l'intero\n"
        "schermo. NON influisce sul visualizzatore integrato (VNC dentro l'app):\n"
        "per quello, usa il pulsante 'Schermo intero del visualizzatore'.",
    "\U0001f4bf Medios": "\U0001f4bf Supporti",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Mismo menú que el botón 'Medios' de la pestaña Resumen.\n"
    "Atajo: Ctrl+M.":
        "Supporti della VM: unita CD/DVD e dispositivi USB.\n"
        "Stesso menu del pulsante 'Supporti' nella scheda Panoramica.\n"
        "Scorciatoia: Ctrl+M.",
    "\U0001f504 Reconectar": "\U0001f504 Riconnetti",
    "Reconectar el widget VNC.\n"
    "Útil si cambiaste la resolución del guest y la imagen\n"
    "quedó recortada o mal escalada. El cliente VNC básico\n"
    "no puede cambiar el tamaño de su framebuffer sin\n"
    "reconectar.\n\n"
    "Atajo: Ctrl+R.":
        "Riconnetti il widget VNC.\n"
        "Utile se hai cambiato la risoluzione del guest e l'immagine\n"
        "risulta tagliata o mal scalata. Il client VNC di base\n"
        "non puo cambiare la dimensione del suo framebuffer senza\n"
        "riconnettersi.\n\n"
        "Scorciatoia: Ctrl+R.",

    # ================================================================
    # Console Grafica: zoom del visualizzatore
    # ================================================================
    "Zoom:": "Zoom:",
    "\U0001f50d\u2212": "\U0001f50d\u2212",
    "Reducir el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Riduci lo zoom del visualizzatore integrato.\n"
        "Livelli: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "Ajustado": "Adattato",
    "\U0001f50d+": "\U0001f50d+",
    "Aumentar el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Aumenta lo zoom del visualizzatore integrato.\n"
        "Livelli: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "\u229e Ajustar": "\u229e Adatta",
    "Ajustar la imagen de la VM al tamaño del widget (escala\n"
    "automática). La VM se ve entera, sin barras de scroll.\n"
    "Si la relación de aspecto no coincide, aparecen bandas\n"
    "negras a los lados.":
        "Adatta l'immagine della VM alla dimensione del widget (scala\n"
        "automatica). La VM viene mostrata interamente, senza barre di scorrimento.\n"
        "Se le proporzioni non corrispondono, compaiono bande\n"
        "nere ai lati.",
    "1:1 Tamaño real": "1:1 Dimensione reale",
    "Mostrar la imagen de la VM a su resolución real (100%).\n"
    "Si no cabe en la ventana, aparecen barras de scroll.":
        "Mostra l'immagine della VM alla sua risoluzione reale (100%).\n"
        "Se non entra nella finestra, compaiono barre di scorrimento.",

    # ================================================================
    # Console Grafica: modalita presentazione
    # ================================================================
    "\U0001f3ac Presentación": "\U0001f3ac Presentazione",
    "Modo presentación: oculta los paneles laterales, entra\n"
    "en pantalla completa y salta a la Consola Gráfica.\n"
    "Requiere que la VM esté encendida.\n\n"
    "Atajo: F11. Para salir: F11 o Escape.":
        "Modalita presentazione: nasconde i pannelli laterali, entra\n"
        "a schermo intero e passa alla Console Grafica.\n"
        "Richiede che la VM sia accesa.\n\n"
        "Scorciatoia: F11. Per uscire: F11 o Escape.",
    "\u26f6 Pantalla completa del visor": "\u26f6 Schermo intero del visualizzatore",
    "Salir con:": "Esci con:",
    "Ctrl derecho (como VirtualBox)": "Ctrl destro (come VirtualBox)",
    "Ctrl+Alt+Intro": "Ctrl+Alt+Invio",
    "Combinación de teclas para salir de la pantalla completa del visor embebido.\n"
    "Evita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\n"
    "usar Escape o F11 dentro del sistema invitado, no la uses aquí).":
        "Combinazione di tasti per uscire dallo schermo intero del visualizzatore integrato.\n"
        "Evita di scegliere un tasto che devi inviare all'interno della VM (ad es. se usi\n"
        "Escape o F11 nel sistema guest, non usarlo qui).",
    "Ctrl derecho": "Ctrl destro",
    "Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\n"
    "completa en una ventana propia. NO afecta al visor externo:\n"
    "para ese, usa el checkbox 'Externos en pantalla completa'\n"
    "de la fila de estado.\n\n"
    "Pulsa {0} para salir.":
        "Mostra il visualizzatore INTEGRATO (VNC dentro l'app) a schermo\n"
        "intero in una finestra propria. NON influisce sul visualizzatore esterno:\n"
        "per quello, usa la casella 'Esterni a schermo intero'\n"
        "nella riga di stato.\n\n"
        "Premi {0} per uscire.",
    "Modo presentación": "Modalita presentazione",
    "\U0001f3ac Salir de presentación": "\U0001f3ac Esci dalla presentazione",
    "Salir del modo presentación y restaurar la vista normal.\n"
    "También puedes pulsar F11 o Escape.":
        "Esci dalla modalita presentazione e ripristina la vista normale.\n"
        "Puoi anche premere F11 o Escape.",
    "La VM '{0}' no está corriendo. Enciéndela antes de entrar en modo presentación.":
        "La VM '{0}' non e in esecuzione. Avviala prima di entrare in modalita presentazione.",
    "La Consola Gráfica no está disponible en este sistema (falta el widget VNC embebido).":
        "La Console Grafica non e disponibile su questo sistema (manca il widget VNC integrato).",
    "No se pudo comprobar el estado de la VM: {0}":
        "Impossibile verificare lo stato della VM: {0}",
    "No hay ninguna máquina virtual seleccionada.":
        "Nessuna macchina virtuale selezionata.",

    # ================================================================
    # Console Grafica: avviso Android
    # ================================================================
    "<b>\u2139\ufe0f Notas sobre Android en QEMU/KVM</b>":
        "<b>\u2139\ufe0f Note su Android in QEMU/KVM</b>",

    # ================================================================
    # Console di Avanzamento: pulsanti testata
    # ================================================================
    "\U0001fa7a Salud de la VM": "\U0001fa7a Salute della VM",
    "Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.":
        "Verifica a colpo d'occhio se la VM e realmente in esecuzione, se il Guest Agent risponde e se le cartelle condivise sono state montate.",
    "\U0001f6a6 Semáforos": "\U0001f6a6 Semafari",
    "\U0001f9f9 Limpiar procesos huérfanos": "\U0001f9f9 Pulisci processi orfani",
    "Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.":
        "Cerca processi QEMU/virtiofsd/swtpm rimasti bloccati da una sessione precedente (a causa di una chiusura forzata) e offre di fermarli.",
    "Nivel:": "Livello:",
    "Todo": "Tutto",
    "Avisos+": "Avvisi+",
    "Errores": "Errori",
    "\U0001f50d Filtrar...": "\U0001f50d Filtra...",
    "Auto-scroll": "Scorrimento automatico",
    "\U0001f4c4 Ver log completo": "\U0001f4c4 Vedi log completo",
    "Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.":
        "Mostra la cronologia completa salvata su disco per questa VM (launch.log), non solo quello che entra in questa finestra.",
    "\U0001f4be Exportar log": "\U0001f4be Esporta log",
    "Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.":
        "Salva il log completo di questa VM in un file, utile per chiedere aiuto o segnalare un problema.",
    "Limpiar consola": "Pulisci console",
    "Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').":
        "Cancella i messaggi mostrati qui (la cronologia completa su disco non viene toccata; usa 'Vedi log completo').",
    "Completado.": "Completato.",

    # ================================================================
    # Console di Avanzamento: log e salute VM
    # ================================================================
    "Ver log completo": "Vedi log completo",
    "Selecciona una VM primero.": "Seleziona prima una VM.",
    "Todavía no hay historial guardado para esta VM.":
        "Non c'e ancora una cronologia salvata per questa VM.",
    "Exportar log": "Esporta log",
    "Log completo \u2014 {0}": "Log completo \u2014 {0}",
    "No se pudo leer el log: {0}":
        "Impossibile leggere il log: {0}",
    "No se pudo exportar el log: {0}":
        "Impossibile esportare il log: {0}",
    "Log exportado a:\n{0}": "Log esportato in:\n{0}",
    "Cerrar": "Chiudi",
    "Salud de la VM": "Salute della VM",
    "VM: {0}": "VM: {0}",
    "Carpeta: {0}": "Cartella: {0}",
    "\u25cf QEMU: detenido.": "\u25cf QEMU: fermo.",
    "\u25cf QEMU: {0}{1}.": "\u25cf QEMU: {0}{1}.",
    "\u25cf Guest Agent: no aplica (VM apagada).":
        "\u25cf Guest Agent: non applicabile (VM spenta).",
    "\u25cf Guest Agent: responde (v{0}).":
        "\u25cf Guest Agent: risponde (v{0}).",
    "\u25cf Guest Agent: sin respuesta ({0}). "
    "Verifica que qemu-guest-agent esté instalado y "
    "corriendo en el guest.":
        "\u25cf Guest Agent: nessuna risposta ({0}). "
        "Verifica che qemu-guest-agent sia installato e "
        "in esecuzione nel guest.",
    "\u25cf Carpetas compartidas (VirtioFS): ninguna configurada.":
        "\u25cf Cartelle condivise (VirtioFS): nessuna configurata.",
    "\u25cf Carpetas compartidas (VirtioFS):":
        "\u25cf Cartelle condivise (VirtioFS):",
    "    - {0}: no aplica (VM apagada).":
        "    - {0}: non applicabile (VM spenta).",
    "    - {0}: virtiofsd activo (PID {1}).":
        "    - {0}: virtiofsd attivo (PID {1}).",
    "    - {0}: NO está activo. Revisa {1} si "
    "esperabas que funcionara.":
        "    - {0}: NON e attivo. Controlla {1} se "
        "ti aspettavi che funzionasse.",
    "Limpiar procesos huérfanos": "Pulisci processi orfani",
    "No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores.":
        "Nessun processo QEMU/virtiofsd bloccato da sessioni precedenti trovato.",
    "VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):":
        "VM con QEMU in esecuzione (non toccate qui, usa 'Ferma VM' se vuoi spegnerle):",
    "  - {0} (PID {1})": "  - {0} (PID {1})",
    "Procesos virtiofsd huérfanos encontrados:":
        "Processi virtiofsd orfani trovati:",
    "  - {0}: virtiofsd PID {1}": "  - {0}: virtiofsd PID {1}",
    "Se detuvieron {0} proceso(s) huérfano(s).":
        "{0} processo(i) orfano(i) fermato(i).",
    "\n\nNo se pudieron detener:\n":
        "\n\nImpossibile fermare:\n",
    "Nada que limpiar.": "Niente da pulire.",

    # ================================================================
    # Pannello Aiuto
    # ================================================================
    "Ayuda de Virtual.Machine": "Aiuto di Virtual.Machine",
    "Guia completa de la consola (VNC / SPICE)":
        "Guida completa della console (VNC / SPICE)",
    "\u2753 Ayuda": "\u2753 Aiuto",
    "Idioma de la interfaz.": "Lingua dell'interfaccia.",

    # ================================================================
    # console_backend.py
    # ================================================================
    "QEMU abre su propia ventana (GTK/SDL). No hace falta visor externo ni cliente; a cambio, la VM no aparece dentro de la app.":
        "QEMU apre la propria finestra (GTK/SDL). Non serve un visualizzatore esterno ne un client; in cambio, la VM non appare all'interno dell'app.",
    "Híbrida: VNC se muestra dentro de la app (funciona en Wayland y X11) y SPICE se abre en una ventana externa con spicy o remote-viewer. Lo mejor de ambos: embebido para tenerlo a mano, SPICE para rendimiento y clipboard avanzado.":
        "Ibrida: VNC viene mostrato dentro l'app (funziona su Wayland e X11) e SPICE si apre in una finestra esterna con spicy o remote-viewer. Il meglio di entrambi: integrato per averlo a portata di mano, SPICE per prestazioni e appunti avanzati.",
    "VNC embebido en la app. Sin dependencias adicionales.":
        "VNC integrato nell'app. Nessuna dipendenza aggiuntiva.",
    "VNC en ventana externa. Necesitas vncviewer (tigervnc), gvncviewer o remmina instalado.":
        "VNC in finestra esterna. Serve vncviewer (tigervnc), gvncviewer o remmina installato.",
    "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). Requiere sesión X11; en Wayland cae a visor externo.":
        "SPICE integrato nell'app (Gtk.SpiceDisplay via XEmbed). Richiede sessione X11; su Wayland ricade sul visualizzatore esterno.",
    "SPICE embebido solicitado, pero spice-gtk no tiene binding Python. Se usará visor externo como respaldo. Instala python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).":
        "SPICE integrato richiesto, ma spice-gtk non ha binding Python. Verra usato un visualizzatore esterno come fallback. Installa python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).",
    "SPICE en ventana externa. Necesitas spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "SPICE in finestra esterna. Serve spicy (spice-gtk) o remote-viewer (virt-viewer).",
    "Consola externa": "Console esterna",
    "Selecciona primero una máquina virtual.": "Seleziona prima una macchina virtuale.",
    "No se encontró ningún visor {0} instalado.\n\n":
        "Nessun visualizzatore {0} installato trovato.\n\n",
    "Instala gvncviewer o tigervnc (vncviewer).":
        "Installa gvncviewer o tigervnc (vncviewer).",
    "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "Installa spicy (spice-gtk) o remote-viewer (virt-viewer).",
    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\nLa VM debe estar corriendo para que QEMU haya elegido un\npuerto.":
        "Non riesco ancora a determinare la porta SPICE di questa VM.\n\nLa VM deve essere in esecuzione perche QEMU abbia scelto una\nporta.",
    "El socket {0} todavía no existe.\n\nLa VM debe estar corriendo con ese protocolo seleccionado.":
        "Il socket {0} non esiste ancora.\n\nLa VM deve essere in esecuzione con quel protocollo selezionato.",

    # ================================================================
    # console_ui_mixin.py: blocco aiuto grande
    # ================================================================
    "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden embeber dentro de la app.":
        "<b>Sessione attuale: X11.</b> Sia VNC che SPICE possono essere integrati dentro l'app.",
    "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber dentro de la app. SPICE embebido requeriría X11 (XEmbed no existe en Wayland); si eliges SPICE con modo embebido, caerá automáticamente a visor externo.":
        "<b>Sessione attuale: Wayland.</b> Solo VNC puo essere integrato dentro l'app. SPICE integrato richiederebbe X11 (XEmbed non esiste su Wayland); se scegli SPICE con modalita integrata, ricadra automaticamente sul visualizzatore esterno.",
    "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE funcionará cuando estés en X11.":
        "<b>spice-gtk con binding Python: si.</b> L'integrazione di SPICE funzionera quando sei su X11.",
    "<b>spice-gtk con binding Python: no.</b> Aunque estés en X11, SPICE no podrá incrustarse; siempre caerá a visor externo. Instálalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>":
        "<b>spice-gtk con binding Python: no.</b> Anche se sei su X11, SPICE non puo essere integrato; ricadra sempre sul visualizzatore esterno. Installalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>",
    "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su propia ventana y no expone VNC/SPICE; es el único modo compatible con esos gráficos 3D.":
        "<b>Grafica compatibile con VNC / SPICE / Ibrida:</b> <b>Automatico</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> selezionati, QEMU apre la propria finestra e non espone VNC/SPICE; e l'unica modalita compatibile con quelle grafiche 3D.",
    "<b>VNC</b><br><span style='color:#2e7d32;'>\u2713</span> Compatible con cualquier gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>\u2713</span> Se puede embeber dentro de la app, incluso en Wayland.<br><span style='color:#2e7d32;'>\u2713</span> Muchos visores externos disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>\u2713</span> Sin dependencias adicionales en el guest para funcionar.<br><span style='color:#c62828;'>\u2717</span> Sin aceleración 3D ni streaming de video (redibuja por regiones).<br><span style='color:#c62828;'>\u2717</span> Clipboard limitado: solo texto, y el guest necesita <code>vncconfig</code> corriendo.<br><span style='color:#c62828;'>\u2717</span> Sin audio remoto.<br><span style='color:#c62828;'>\u2717</span> Menos fluido en uso intensivo (vídeo, animaciones, 3D).":
        "<b>VNC</b><br><span style='color:#2e7d32;'>\u2713</span> Compatibile con qualsiasi grafica virtuale (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>\u2713</span> Puo essere integrato dentro l'app, anche su Wayland.<br><span style='color:#2e7d32;'>\u2713</span> Molti visualizzatori esterni disponibili (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>\u2713</span> Nessuna dipendenza aggiuntiva nel guest per funzionare.<br><span style='color:#c62828;'>\u2717</span> Nessuna accelerazione 3D ne streaming video (ridisegna per regioni).<br><span style='color:#c62828;'>\u2717</span> Appunti limitati: solo testo, e il guest necessita di <code>vncconfig</code> in esecuzione.<br><span style='color:#c62828;'>\u2717</span> Nessun audio remoto.<br><span style='color:#c62828;'>\u2717</span> Meno fluido in uso intensivo (video, animazioni, 3D).",
    "<b>SPICE</b><br><span style='color:#2e7d32;'>\u2713</span> Mejor rendimiento y fluidez en local (compresión + streaming de video).<br><span style='color:#2e7d32;'>\u2713</span> Clipboard bidireccional avanzado (con <code>spice-vdagent</code> en el guest).<br><span style='color:#2e7d32;'>\u2713</span> Audio remoto integrado.<br><span style='color:#2e7d32;'>\u2713</span> Varios monitores, redirección USB y carpetas compartidas nativas.<br><span style='color:#c62828;'>\u2717</span> No se puede embeber en Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>\u2717</span> Requiere un visor externo (spicy o remote-viewer) si no se puede embeber.<br><span style='color:#c62828;'>\u2717</span> Para aprovecharlo hay que instalar <code>spice-vdagent</code> en el guest.<br><span style='color:#c62828;'>\u2717</span> Incompatible con VirGL y Venus (usan OpenGL y obligan a la ventana nativa de QEMU).":
        "<b>SPICE</b><br><span style='color:#2e7d32;'>\u2713</span> Prestazioni e fluidita migliori in locale (compressione + streaming video).<br><span style='color:#2e7d32;'>\u2713</span> Appunti bidirezionali avanzati (con <code>spice-vdagent</code> nel guest).<br><span style='color:#2e7d32;'>\u2713</span> Audio remoto integrato.<br><span style='color:#2e7d32;'>\u2713</span> Piu monitor, reindirizzamento USB e cartelle condivise native.<br><span style='color:#c62828;'>\u2717</span> Non puo essere integrato su Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>\u2717</span> Richiede un visualizzatore esterno (spicy o remote-viewer) se non puo essere integrato.<br><span style='color:#c62828;'>\u2717</span> Per sfruttarlo occorre installare <code>spice-vdagent</code> nel guest.<br><span style='color:#c62828;'>\u2717</span> Incompatibile con VirGL e Venus (usano OpenGL e obbligano alla finestra nativa di QEMU).",
    "<b>Híbrida (VNC embebido + SPICE externo)</b><br><span style='color:#2e7d32;'>\u2713</span> Lo mejor de ambos: VNC siempre visible dentro de la app, SPICE para rendimiento y clipboard.<br><span style='color:#2e7d32;'>\u2713</span> Funciona en cualquier sesión: Wayland o X11.<br><span style='color:#2e7d32;'>\u2713</span> Si spicy falla o lo cierras, el widget VNC sigue funcionando.<br><span style='color:#2e7d32;'>\u2713</span> Útil para ver la VM en dos monitores o para grabar y controlar a la vez.<br><span style='color:#c62828;'>\u2717</span> Consume más recursos: QEMU mantiene dos servidores de display en paralelo.<br><span style='color:#c62828;'>\u2717</span> Verás la misma VM en dos ventanas (dentro de la app y en la de spicy).<br><span style='color:#c62828;'>\u2717</span> La configuración del guest para sacar partido a SPICE (vdagent, drivers) hay que hacerla igual.<br><span style='color:#c62828;'>\u2717</span> Como SPICE, incompatible con VirGL y Venus.":
        "<b>Ibrida (VNC integrato + SPICE esterno)</b><br><span style='color:#2e7d32;'>\u2713</span> Il meglio di entrambi: VNC sempre visibile dentro l'app, SPICE per prestazioni e appunti.<br><span style='color:#2e7d32;'>\u2713</span> Funziona in qualsiasi sessione: Wayland o X11.<br><span style='color:#2e7d32;'>\u2713</span> Se spicy fallisce o lo chiudi, il widget VNC continua a funzionare.<br><span style='color:#2e7d32;'>\u2713</span> Utile per vedere la VM su due monitor o per registrare e controllare contemporaneamente.<br><span style='color:#c62828;'>\u2717</span> Consuma piu risorse: QEMU mantiene due server di visualizzazione in parallelo.<br><span style='color:#c62828;'>\u2717</span> Vedrai la stessa VM in due finestre (dentro l'app e in quella di spicy).<br><span style='color:#c62828;'>\u2717</span> La configurazione del guest per sfruttare SPICE (vdagent, driver) va fatta comunque.<br><span style='color:#c62828;'>\u2717</span> Come SPICE, incompatibile con VirGL e Venus.",

    # ================================================================
    # console_ui_mixin.py: etichette dinamiche grafica
    # ================================================================
    "No detectada": "Non rilevata",
    "\u2713 OpenGL": "\u2713 OpenGL",
    "\u2717 OpenGL": "\u2717 OpenGL",
    "\u2713 VirGL": "\u2713 VirGL",
    "\u2713 VirGL instalado": "\u2713 VirGL installato",
    "\u2717 VirGL": "\u2717 VirGL",
    "\u2713 Vulkan": "\u2713 Vulkan",
    "\u2717 Vulkan": "\u2717 Vulkan",
    "VGA estándar (QEMU -vga std)": "VGA standard (QEMU -vga std)",
    "VGA de OSX-KVM (VGA virtual)": "VGA di OSX-KVM (VGA virtuale)",
    "gestionada por OpenCore/OSX-KVM": "gestita da OpenCore/OSX-KVM",
    "VirtIO-GPU + VirGL 3D": "VirtIO-GPU + VirGL 3D",
    "OpenGL / VirGL": "OpenGL / VirGL",
    "VirtIO-GPU 2D": "VirtIO-GPU 2D",
    "sin aceleración 3D": "senza accelerazione 3D",
    "VGA estándar de QEMU": "VGA standard di QEMU",
    "<b>Automático \u2192 {0}</b><br>Aceleración: {1}":
        "<b>Automatico \u2192 {0}</b><br>Accelerazione: {1}",
    "VirtIO-GPU + Venus/Vulkan 3D": "VirtIO-GPU + Venus/Vulkan 3D",
    "Red Hat QXL 2D": "Red Hat QXL 2D",
    "VMware SVGA II": "VMware SVGA II",
    "<b>Usará: {0}</b>": "<b>Usera: {0}</b>",
    "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}":
        "GPU host: {0}<br>{1}  |  {2}  |  {3}<br>{4}",
    "Host GPU: no se pudo determinar automáticamente.<br>Automático: se seleccionará el modo gráfico compatible disponible.":
        "GPU host: non e stato possibile determinarlo automaticamente.<br>Automatico: verra selezionata la modalita grafica compatibile disponibile.",
}
