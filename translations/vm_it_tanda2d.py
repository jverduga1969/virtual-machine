# -*- coding: utf-8 -*-
"""vm_it_tanda2d - Traduzioni in italiano - Tanda 2d.

Copre la scheda Configurazione Host completa:
  - Stato del sistema di virtualizzazione.
  - Diagnostica PCI / VFIO (IOMMU, VT-d, prepara intel_iommu=on,
    apri UEFI/BIOS, albero dispositivi).
  - Permessi USB dell'host (regola udev).
  - Dipendenze cartelle condivise.
  - Aspetto (selettore tema).
  - Scorciatoie da tastiera configurabili.
  - API REST locale.

Copre anche due voci della sidebar Config VM che mancavano:
Passthrough e Condivisione.
"""

TRANSLATIONS = {

    # ================================================================
    # Sidebar Config VM
    # ================================================================
    "Passthrough": "Passthrough",
    "Compartición": "Condivisione",

    # ================================================================
    # Sottotitolo Configurazione Host
    # ================================================================
    "Ajustes y diagnostico del sistema anfitrion. Nada de esta seccion se guarda con la VM: aplica a todo el equipo.":
        "Impostazioni e diagnostica del sistema host. Nulla di questa sezione viene salvato con la VM: si applica all'intero computer.",

    # ================================================================
    # Aspetto (theme_selector_v1)
    # ================================================================
    "Apariencia": "Aspetto",
    "Sistema (predeterminado)": "Sistema (predefinito)",
    "Claro": "Chiaro",
    "Oscuro": "Scuro",
    "Tema visual de la aplicacion.\n"
    "  - Sistema: usa el estilo y la paleta del escritorio.\n"
    "  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n"
    "    propia, independiente del SO.\n\n"
    "Al elegir Claro u Oscuro, la app cambia el estilo de Qt a\n"
    "Fusion. Al volver a Sistema, se restaura el estilo original\n"
    "del escritorio (Breeze, Adwaita, etc.).":
        "Tema visivo dell'applicazione.\n"
        "  - Sistema: usa lo stile e la palette del desktop.\n"
        "  - Chiaro / Scuro: forza lo stile Fusion con una palette\n"
        "    propria, indipendente dal SO.\n\n"
        "Scegliendo Chiaro o Scuro, l'app cambia lo stile Qt a\n"
        "Fusion. Tornando a Sistema, viene ripristinato lo stile originale\n"
        "del desktop (Breeze, Adwaita, ecc.).",
    "Tema:": "Tema:",
    "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\n"
    "reiniciar la app para que TODOS los widgets se repinten con los\n"
    "colores nuevos (depende del estilo del escritorio).":
        "Passando da 'Sistema' a 'Chiaro/Scuro' puo essere necessario\n"
        "riavviare l'app per far ridisegnare TUTTI i widget con i\n"
        "nuovi colori (dipende dallo stile del desktop).",
    "Cambio de tema": "Cambio tema",
    "Se ha cambiado el tema.\n\n"
    "Algunos estilos del escritorio (Kvantum en KDE, por\n"
    "ejemplo) pueden no repintar todos los widgets hasta\n"
    "reiniciar la aplicacion.\n\n"
    "¿Quieres reiniciar ahora para asegurar que todos los\n"
    "elementos se vean correctamente?":
        "Il tema e stato cambiato.\n\n"
        "Alcuni stili del desktop (Kvantum su KDE, ad\n"
        "esempio) potrebbero non ridisegnare tutti i widget finche\n"
        "non si riavvia l'applicazione.\n\n"
        "Vuoi riavviare ora per assicurarti che tutti gli\n"
        "elementi vengano visualizzati correttamente?",

    # ================================================================
    # Scorciatoie da tastiera
    # ================================================================
    "Atajos de teclado": "Scorciatoie da tastiera",
    "Reasigna los atajos globales de la aplicacion. Los cambios\n"
    "se aplican al instante, sin reiniciar.":
        "Riassegna le scorciatoie globali dell'applicazione. Le modifiche\n"
        "vengono applicate immediatamente, senza riavvio.",
    "Configurar atajos...": "Configura scorciatoie...",
    "Configurar atajos de teclado": "Configura scorciatoie da tastiera",
    "Haz clic en <b>Cambiar...</b> para capturar una nueva\n"
    "combinacion de teclas. Pulsa <b>Escape</b> durante la\n"
    "captura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\n"
    "para deshabilitar un atajo.":
        "Fai clic su <b>Cambia...</b> per catturare una nuova\n"
        "combinazione di tasti. Premi <b>Escape</b> durante la\n"
        "cattura per annullarla. Usa <b>Canc</b> o <b>Backspace</b>\n"
        "per disabilitare una scorciatoia.",
    "Accion": "Azione",
    "Atajo": "Scorciatoia",
    "Cambiar...": "Cambia...",
    "Restaurar todos por defecto": "Ripristina tutti ai valori predefiniti",
    "(sin atajo)": "(nessuna scorciatoia)",
    "Conflicto de atajos": "Conflitto di scorciatoie",
    "El atajo {0} ya esta asignado a:\n\n  {1}\n\nElige otro o cambia primero el otro atajo.":
        "La scorciatoia {0} e gia assegnata a:\n\n  {1}\n\nScegline un'altra o cambia prima l'altra scorciatoia.",
    "Restaurar atajos": "Ripristina scorciatoie",
    "¿Restaurar los cuatro atajos a sus valores por defecto?":
        "Ripristinare le quattro scorciatoie ai valori predefiniti?",
    "Pulsa la nueva combinacion": "Premi la nuova combinazione",
    "<b>Pulsa la combinacion de teclas que quieras asignar.</b>":
        "<b>Premi la combinazione di tasti che vuoi assegnare.</b>",
    "Esperando pulsacion...\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "In attesa di un tasto...\n\nEscape annulla. Canc o Backspace disabilita la scorciatoia.",
    "Atajo actual: <b>{0}</b>": "Scorciatoia attuale: <b>{0}</b>",
    "Solo has pulsado un modificador. Anade una tecla normal.\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "Hai premuto solo un modificatore. Aggiungi un tasto normale.\n\nEscape annulla. Canc o Backspace disabilita la scorciatoia.",
    "Abrir menu de Medios (CD/DVD + USB)":
        "Apri menu Supporti (CD/DVD + USB)",
    "Reconectar el widget VNC": "Riconnetti il widget VNC",
    "Alternar Consola Grafica": "Attiva/disattiva Console Grafica",
    "Entrar / salir del modo presentacion":
        "Entra / esci dalla modalita presentazione",

    # ================================================================
    # API REST locale
    # ================================================================
    "API REST local": "API REST locale",
    "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar VMs desde scripts, dashboards o CI. Todo se autentica con un token local; <b>no</b> es accesible desde la red.":
        "Espone un'API HTTP minima su <b>127.0.0.1</b> per controllare le VM da script, dashboard o CI. Tutto viene autenticato con un token locale; <b>non</b> e accessibile dalla rete.",
    "Activar API REST local": "Attiva API REST locale",
    "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\nCambios requieren apagar y volver a encender la API.":
        "Porta TCP su cui il server resta in ascolto. Solo 127.0.0.1.\nLe modifiche richiedono di spegnere e riaccendere l'API.",
    "Puerto:": "Porta:",
    "URL:": "URL:",
    "Token:": "Token:",
    "Mostrar / ocultar el token": "Mostra / nascondi il token",
    "Copiar": "Copia",
    "Regenerar": "Rigenera",
    "Genera un token nuevo. Las peticiones con el token anterior\ndejarán de funcionar.":
        "Genera un nuovo token. Le richieste con il token precedente\nsmetteranno di funzionare.",
    "Ver peticiones recientes": "Vedi richieste recenti",
    "Ejemplo de uso desde terminal:<br><code>curl -H 'X-API-Token: &lt;tu-token&gt;' http://127.0.0.1:8730/api/vms</code>":
        "Esempio d'uso da terminale:<br><code>curl -H 'X-API-Token: &lt;tuo-token&gt;' http://127.0.0.1:8730/api/vms</code>",
    "API REST": "API REST",
    "<b style='color:#2e7d32;'>Activa</b> — {0} peticiones desde el arranque":
        "<b style='color:#2e7d32;'>Attiva</b> — {0} richieste dall'avvio",
    "<b style='color:#888;'>Detenida</b>":
        "<b style='color:#888;'>Ferma</b>",
    "No se pudo arrancar la API REST.\n\n{0}":
        "Impossibile avviare l'API REST.\n\n{0}",
    "Regenerar token": "Rigenera token",
    "Se generará un token nuevo y el anterior dejará de funcionar.\n\n¿Continuar?":
        "Verra generato un nuovo token e quello precedente smettera di funzionare.\n\nContinuare?",
    "Se regeneró el token pero no se pudo reiniciar la API:\n\n{0}":
        "Il token e stato rigenerato ma non e stato possibile riavviare l'API:\n\n{0}",
    "Peticiones recientes a la API": "Richieste recenti all'API",
    "Últimas peticiones atendidas por la API. Se conservan las 50 más recientes.":
        "Ultime richieste servite dall'API. Vengono conservate le 50 piu recenti.",
    "(sin peticiones todavía)": "(nessuna richiesta ancora)",

    # ================================================================
    # Stato del sistema di virtualizzazione
    # ================================================================
    "Estado del sistema de virtualización": "Stato del sistema di virtualizzazione",
    "Distribución: comprobando...": "Distribuzione: verifica in corso...",
    "Gestor de paquetes: comprobando...": "Gestore di pacchetti: verifica in corso...",
    "\U0001f504 Comprobar dependencias": "\U0001f504 Verifica dipendenze",
    "\U0001f504\ufe0f Comprobar dependencias": "\U0001f504\ufe0f Verifica dipendenze",
    "\U0001f6e0 Comprobar/Reparar dependencias":
        "\U0001f6e0 Verifica/Ripara dipendenze",
    "\U0001f6e0\ufe0f Comprobar/Reparar dependencias":
        "\U0001f6e0\ufe0f Verifica/Ripara dipendenze",

    # ================================================================
    # Diagnostica PCI / VFIO
    # ================================================================
    "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.":
        "Passthrough di hardware fisico. PCI usa VFIO; USB usa usb-host su XHCI. Il programma verifichera l'accesso a /dev/bus/usb, smontera automaticamente l'archiviazione USB selezionata dall'host e richiedera permessi amministrativi solo quando necessario. Non selezionare Root Hub.",
    "Diagnóstico PCI / VFIO": "Diagnostica PCI / VFIO",
    "Comprobando Intel VT-d / IOMMU...": "Verifica Intel VT-d / IOMMU in corso...",
    "\U0001f504 Comprobar IOMMU / VFIO": "\U0001f504 Verifica IOMMU / VFIO",
    "\u2139 Ver diagnóstico detallado": "\u2139 Vedi diagnostica dettagliata",
    "\U0001f6e0 Preparar intel_iommu=on": "\U0001f6e0 Prepara intel_iommu=on",
    "\u2699 Abrir UEFI/BIOS": "\u2699 Apri UEFI/BIOS",
    "Usar": "Usa",
    "IOMMU / Driver": "IOMMU / Driver",
    "\U0001f504 Detectar dispositivos": "\U0001f504 Rileva dispositivi",
    "\U0001f4be Guardar selección": "\U0001f4be Salva selezione",
    "\U0001f50c Conectar USB en caliente": "\U0001f50c Collega USB a caldo",
    "\u23cf Desconectar USB": "\u23cf Scollega USB",

    # --- Testi di stato VFIO ---
    "\u2705 Intel VT-d / IOMMU activo": "\u2705 Intel VT-d / IOMMU attivo",
    "\u26a0 VT-d detectado por firmware, pero no hay grupos IOMMU utilizables":
        "\u26a0 VT-d rilevato dal firmware, ma nessun gruppo IOMMU utilizzabile",
    "\u274c Intel VT-d / IOMMU no detectado": "\u274c Intel VT-d / IOMMU non rilevato",
    "(sin datos)": "(nessun dato)",
    "<b>{0}</b><br>"
    "Firmware/ACPI DMAR: {1}<br>"
    "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>"
    "Gestor de arranque: {4}<br>"
    "Parámetros kernel: <code>{5}</code>":
        "<b>{0}</b><br>"
        "Firmware/ACPI DMAR: {1}<br>"
        "Gruppi IOMMU: {2} &nbsp;|&nbsp; PCI pronti per VFIO: {3}<br>"
        "Gestore di avvio: {4}<br>"
        "Parametri del kernel: <code>{5}</code>",
    "Desconocido": "Sconosciuto",
    "<br>\u26a0 El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.":
        "<br>\u26a0 La CPU non e stata identificata come Intel; controlla la diagnostica AMD/IOMMU.",
    "<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. "
    "Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.":
        "<br>Raccomandazione: usare <b>Prepara intel_iommu=on</b> e riavviare. "
        "Se dopo il riavvio non ci sono gruppi, controllare VT-d nel BIOS/UEFI.",
    "<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar "
    "<code>intel_iommu=on</code> en el arranque.":
        "<br>Raccomandazione: abilitare Intel VT-d nel BIOS/UEFI e poi attivare "
        "<code>intel_iommu=on</code> all'avvio.",

    # --- Diagnostic preparazione IOMMU ---
    "El procesador no se identificó como Intel; no se aplicará intel_iommu=on.":
        "Il processore non e stato identificato come Intel; intel_iommu=on non verra applicato.",
    "No pude identificar de forma segura el gestor de arranque.":
        "Non e stato possibile identificare in modo sicuro il gestore di avvio.",
    "La preparación automática está implementada actualmente para GRUB. "
    "Gestor detectado: {0}.":
        "La preparazione automatica e attualmente implementata per GRUB. "
        "Gestore rilevato: {0}.",
    "No se pudo leer {0}.": "Impossibile leggere {0}.",
    "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub.":
        "GRUB_CMDLINE_LINUX_DEFAULT non trovato in /etc/default/grub.",
    "intel_iommu=on ya está presente en /etc/default/grub.":
        "intel_iommu=on e gia presente in /etc/default/grub.",
    "operación cancelada": "operazione annullata",
    "Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ":
        "/etc/default/grub e stato modificato, ma non e stato possibile rigenerare grub.cfg: ",
    "error desconocido": "errore sconosciuto",
    "Se añadió intel_iommu=on y se regeneró GRUB.":
        "intel_iommu=on e stato aggiunto e GRUB e stato rigenerato.",
    "IOMMU / VT-d": "IOMMU / VT-d",
    "El IOMMU ya aparece activo. No es necesario modificar el arranque.":
        "IOMMU risulta gia attivo. Non e necessario modificare l'avvio.",
    "No se identificó un CPU Intel.": "Nessuna CPU Intel identificata.",
    "Preparar Intel IOMMU": "Prepara Intel IOMMU",
    "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\n"
    "Se hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\n"
    "Esto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\n"
    "Gestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?":
        "intel_iommu=on verra aggiunto alla configurazione del gestore di avvio.\n\n"
        "Verra fatta una copia di backup prima di modificarla e verra richiesta l'autorizzazione amministrativa.\n\n"
        "Questo NON attiva VT-d all'interno del BIOS/UEFI; quella parte va abilitata nel firmware.\n\n"
        "Gestore rilevato: {0}\nFile: {1}\n\nContinuare?",
    "no identificado": "non identificato",
    "Configuración actualizada.": "Configurazione aggiornata.",
    "\n\nReinicia el equipo para que el parámetro tenga efecto.":
        "\n\nRiavvia il computer per rendere effettivo il parametro.",
    "No se pudo preparar IOMMU": "Impossibile preparare IOMMU",
    "Abrir UEFI/BIOS": "Apri UEFI/BIOS",
    "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\n"
    "Busca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?":
        "Il computer si riavviera direttamente alla configurazione del firmware se il sistema lo consente.\n\n"
        "Cerca un'opzione chiamata Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o simile e attivala.\n\nRiavviare ora?",
    "No se pudo solicitar el reinicio al firmware.":
        "Impossibile richiedere il riavvio al firmware.",
    "No se pudo abrir UEFI/BIOS": "Impossibile aprire UEFI/BIOS",
    "Desactivado por parámetro del kernel": "Disattivato da parametro del kernel",
    "Activo": "Attivo",
    "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles":
        "VT-d rilevato dal firmware/kernel; IOMMU senza gruppi visibili",
    "No detectado": "Non rilevato",
    "Detectado": "Rilevato",
    "No confirmado": "Non confermato",
    "\u2713 Listo para VFIO": "\u2713 Pronto per VFIO",
    "\u26a0 Sin grupo IOMMU": "\u26a0 Nessun gruppo IOMMU",
    "\u26a0 Comparte grupo IOMMU": "\u26a0 Condivide gruppo IOMMU",
    "\u26a0 Requiere preparación VFIO": "\u26a0 Richiede preparazione VFIO",

    # --- Diagnostica dettagliata ---
    "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===":
        "=== DIAGNOSTICA INTEL VT-d / IOMMU / VFIO ===",
    "Estado: {0}": "Stato: {0}",
    "Arquitectura: {0}": "Architettura: {0}",
    "desconocida": "sconosciuta",
    "CPU Intel detectado: {0}": "CPU Intel rilevata: {0}",
    "intel_iommu=on en kernel actual: {0}":
        "intel_iommu=on nel kernel attuale: {0}",
    "IOMMU desactivado por parámetro: {0}":
        "IOMMU disattivato da parametro: {0}",
    "Clases IOMMU: {0}": "Classi IOMMU: {0}",
    "Gestor de arranque: {0}": "Gestore di avvio: {0}",
    "desconocido": "sconosciuto",
    "Configuración: {0}": "Configurazione: {0}",
    "no identificada": "non identificata",
    "Parámetros kernel: {0}": "Parametri del kernel: {0}",
    "=== DISPOSITIVOS PCI ===": "=== DISPOSITIVI PCI ===",
    "{0} | {1} | driver={2} | grupo={3} | estado={4}":
        "{0} | {1} | driver={2} | gruppo={3} | stato={4}",
    "sin driver": "senza driver",
    "Diagnóstico VFIO": "Diagnostica VFIO",
    "Diagnóstico copiado al portapapeles.":
        "Diagnostica copiata negli appunti.",
    "No se pudo copiar el diagnóstico":
        "Impossibile copiare la diagnostica",
    "Diagnóstico Intel VT-d / IOMMU / VFIO":
        "Diagnostica Intel VT-d / IOMMU / VFIO",
    "\U0001f4cb Copiar": "\U0001f4cb Copia",

    # --- _pci_preflight ---
    "IOMMU/Intel VT-d: {0}": "IOMMU/Intel VT-d: {0}",
    "Firmware/ACPI DMAR: {0}": "Firmware/ACPI DMAR: {0}",
    "Grupos IOMMU: {0}": "Gruppi IOMMU: {0}",
    "{0}: no tiene grupo IOMMU ({1})": "{0}: non ha un gruppo IOMMU ({1})",
    "{0}: comparte grupo IOMMU {1} con {2}":
        "{0}: condivide il gruppo IOMMU {1} con {2}",
    "{0}: driver actual {1}; todavía no está ligado a vfio-pci":
        "{0}: driver attuale {1}; non ancora associato a vfio-pci",
    "\u2022 {0} | grupo {1} | driver {2}":
        "\u2022 {0} | gruppo {1} | driver {2}",

    # ================================================================
    # Permessi USB dell'host
    # ================================================================
    "Permisos USB del host": "Permessi USB dell'host",
    "Para poder pasar memorias o discos USB a la VM sin pedir contraseña cada vez, el sistema necesita una regla udev que conceda acceso al usuario activo. Puedes instalarla aquí con un clic; solo se aplica a esta categoría de dispositivos.":
        "Per poter passare chiavette o dischi USB alla VM senza chiedere la password ogni volta, il sistema necessita di una regola udev che conceda l'accesso all'utente attivo. Puoi installarla qui con un clic; si applica solo a questa categoria di dispositivi.",
    "Comprobando…": "Verifica in corso…",
    "\U0001f504 Comprobar": "\U0001f504 Verifica",
    "\U0001f527 Configurar permisos USB": "\U0001f527 Configura permessi USB",
    "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\n"
    "que permite el acceso a los dispositivos USB al usuario activo.\n"
    "Solo se toca este archivo; el resto de la configuración USB\n"
    "del sistema no se modifica.":
        "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regola\n"
        "che consente l'accesso ai dispositivi USB all'utente attivo.\n"
        "Viene modificato solo questo file; il resto della configurazione USB\n"
        "di sistema non viene toccata.",

    # --- Errori USB ---
    "No existe {0}. El número Device puede haber cambiado; "
    "vuelve a detectar USB.":
        "{0} non esiste. Il numero Device potrebbe essere cambiato; "
        "rileva di nuovo l'USB.",
    "Sin acceso de lectura/escritura a {0}.":
        "Nessun accesso in lettura/scrittura a {0}.",
    "No se encontró 'pkexec'. No puedo solicitar permisos "
    "administrativos automáticamente.":
        "'pkexec' non trovato. Impossibile richiedere permessi "
        "amministrativi automaticamente.",
    "No se pudo ejecutar la acción administrativa ({0}): {1}":
        "Impossibile eseguire l'azione amministrativa ({0}): {1}",
    "No se pudo realizar la acción administrativa ({0}). {1}":
        "Impossibile eseguire l'azione amministrativa ({0}). {1}",
    "No existe el nodo USB actual {0}; el dispositivo "
    "pudo cambiar de dirección.":
        "Il nodo USB attuale {0} non esiste; il dispositivo "
        "potrebbe aver cambiato indirizzo.",
    "(desconocido)": "(sconosciuto)",
    "dar acceso temporal al dispositivo USB":
        "concedere accesso temporaneo al dispositivo USB",
    "No pude desmontar automáticamente el almacenamiento USB:\n"
    "{0}\n\n{1}":
        "Impossibile smontare automaticamente l'archiviazione USB:\n"
        "{0}\n\n{1}",
    "El USB sigue sin acceso después de preparar el dispositivo: {0}":
        "L'USB continua senza accesso dopo aver preparato il dispositivo: {0}",
    "USB {0} | nodo: {1} | acceso usuario: {2} | {3}":
        "USB {0} | nodo: {1} | accesso utente: {2} | {3}",
    "NO": "NO",
    "no se pudo leer ({0})": "impossibile leggere ({0})",
    "error al comprobar: {0}": "errore durante la verifica: {0}",
    "\u2705 Permisos USB: OK ({0}). El passthrough en caliente "
    "no pedirá contraseña.":
        "\u2705 Permessi USB: OK ({0}). Il passthrough a caldo "
        "non chiedera la password.",
    "Los permisos USB ya están configurados.\n"
    "Si quieres desinstalarlos, borra:\n"
    "{0}":
        "I permessi USB sono gia configurati.\n"
        "Se vuoi disinstallarli, elimina:\n"
        "{0}",
    "\u26a0 Permisos USB: {0}. El passthrough en caliente "
    "pedirá contraseña cada vez.":
        "\u26a0 Permessi USB: {0}. Il passthrough a caldo "
        "chiedera la password ogni volta.",
    "Permisos USB": "Permessi USB",
    "No se encontró 'pkexec'. Instálalo (paquete 'polkit') para "
    "que la aplicación pueda solicitar permisos administrativos "
    "de forma gráfica.":
        "'pkexec' non trovato. Installalo (pacchetto 'polkit') per "
        "consentire all'applicazione di richiedere permessi amministrativi "
        "graficamente.",
    "No se encontró 'udevadm'. Este sistema parece no usar udev "
    "para gestionar dispositivos USB. Aplica los permisos "
    "manualmente según tu distribución.":
        "'udevadm' non trovato. Questo sistema sembra non usare udev "
        "per gestire i dispositivi USB. Applica i permessi "
        "manualmente in base alla tua distribuzione.",
    "Configurar permisos USB": "Configura permessi USB",
    "La operación tardó demasiado. Vuelve a intentarlo.":
        "L'operazione ha impiegato troppo tempo. Riprova.",
    "Dispositivo USB inválido.": "Dispositivo USB non valido.",

    # ================================================================
    # Dipendenze cartelle condivise
    # ================================================================
    "Dependencias del host": "Dipendenze dell'host",
    "VirtioFS: SIN COMPROBAR": "VirtioFS: NON VERIFICATO",
    "9p: SIN COMPROBAR": "9p: NON VERIFICATO",
    "SMB: SIN COMPROBAR": "SMB: NON VERIFICATO",
    "9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.":
        "9p fa parte di QEMU e normalmente non richiede l'installazione di un pacchetto aggiuntivo sull'host. VirtioFS necessita di virtiofsd e SMB necessita di Samba/smbd.",
    "\U0001f6e0\ufe0f Instalar faltantes": "\U0001f6e0\ufe0f Installa mancanti",
    "FALTA": "MANCANTE",
    "Dependencias": "Dipendenze",
    "Las dependencias del host ya están instaladas.":
        "Le dipendenze dell'host sono gia installate.",
    "Instalar dependencias": "Installa dipendenze",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Mancano:\n\n• {0}\n\nVuoi installarle ora usando il gestore di pacchetti di sistema?",
    "Las dependencias de carpetas compartidas quedaron instaladas y verificadas.":
        "Le dipendenze delle cartelle condivise sono state installate e verificate.",
    "No se pudieron instalar todas las dependencias.\n\n{0}":
        "Non e stato possibile installare tutte le dipendenze.\n\n{0}",

    # ================================================================
    # Stringhe mancanti dal pannello sinistro
    # ================================================================
    "Selecciona primero una máquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "Primero selecciona una máquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "Primero selecciona una máquina virtual existente.":
        "Seleziona prima una macchina virtuale esistente.",
    "Selecciona primero una maquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "Selecciona una máquina virtual.":
        "Seleziona una macchina virtuale.",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Seleziona una VM per gestirla. Usa 'Nuova macchina virtuale' per crearne un'altra.",
    "No hay una máquina virtual seleccionada todavía.":
        "Nessuna macchina virtuale selezionata ancora.",
}
