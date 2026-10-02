# -*- coding: utf-8 -*-
"""vm_it_tanda2a - Traduzioni in italiano - Tanda 2a.

Copre: pannello sinistro (lista VM, ricerca, ordinamento, filtro
gruppo, pulsante Nuova VM), controlli VM (Avvia/Pausa/Spegni/Riavvia/
Forza), toolbar Panoramica (Supporti/Clona/Scollega/Importa/Esporta/
Modello/Comando QEMU/Note/Etichetta/Confronta/Elimina) e titolo/stato
del pannello centrale.
"""

TRANSLATIONS = {

    # ================================================================
    # Pannello sinistro
    # ================================================================
    "<b>MÁQUINAS VIRTUALES</b>": "<b>MACCHINE VIRTUALI</b>",
    "\U0001f50d Buscar máquinas...": "\U0001f50d Cerca macchine...",
    "Ordenar: Nombre (A-Z)": "Ordina: Nome (A-Z)",
    "Ordenar: Estado": "Ordina: Stato",
    "Ordenar: Ultima vez usada": "Ordina: Ultimo utilizzo",
    "Como ordenar la lista de maquinas virtuales.\n"
    "  - Nombre: alfabetico.\n"
    "  - Estado: encendidas primero, luego pausadas, apagadas al final.\n"
    "  - Ultima vez usada: por fecha de modificacion del vm_config.ini\n"
    "    (aproxima cuando se configuro por ultima vez).":
        "Come ordinare l'elenco delle macchine virtuali.\n"
        "  - Nome: alfabetico.\n"
        "  - Stato: accese per prime, poi in pausa, spente alla fine.\n"
        "  - Ultimo utilizzo: per data di modifica del vm_config.ini\n"
        "    (approssima quando è stata configurata l'ultima volta).",
    "Todos los grupos": "Tutti i gruppi",
    "Muestra solo las VMs de un grupo concreto.\n"
    "  • Todos los grupos: sin filtro de grupo.\n"
    "  • Sin grupo: solo VMs sin etiqueta de grupo.\n"
    "  • <nombre>: solo VMs con ese grupo.\n"
    "\n"
    "Los grupos se asignan desde el botón '🏷 Etiqueta' del Resumen.":
        "Mostra solo le VM di un gruppo specifico.\n"
        "  • Tutti i gruppi: nessun filtro di gruppo.\n"
        "  • Senza gruppo: solo VM senza etichetta di gruppo.\n"
        "  • <nome>: solo VM con quel gruppo.\n"
        "\n"
        "I gruppi vengono assegnati dal pulsante '🏷 Etichetta' della Panoramica.",
    "\u2795 Nueva VM": "\u2795 Nuova VM",
    "Selecciona una máquina virtual": "Seleziona una macchina virtuale",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Seleziona una macchina virtuale nell'elenco a sinistra.",
    "● Sin VM seleccionada": "● Nessuna VM selezionata",

    # ================================================================
    # Controlli VM
    # ================================================================
    "▶ Iniciar": "▶ Avvia",
    "⏸ Pausar": "⏸ Pausa",
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.":
        "Metti in pausa la VM. Usa la freccia per più opzioni:\n"
        "• Pausa (rapida): ferma senza salvare lo stato su disco.\n"
        "• Salva stato e pausa: scrive la RAM su disco prima di mettere in pausa.\n"
        "• Riprendi: riprende l'esecuzione della VM in pausa.",
    "⏹ Apagar": "⏹ Spegni",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.":
        "Spegnimento (ACPI): chiede alla VM di spegnersi in modo ordinato.",
    "⏹ Apagado (ACPI)": "⏹ Spegnimento (ACPI)",
    "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\n"
    "encendido en un equipo real. El sistema operativo invitado decide cuándo\n"
    "y cómo cerrar. Puede tardar unos segundos o no responder si está colgado.":
        "Chiede alla VM di spegnersi in modo ordinato, come premere il pulsante\n"
        "di accensione su un computer reale. Il sistema operativo guest decide quando\n"
        "e come chiudersi. Può richiedere alcuni secondi o non rispondere se è bloccato.",
    "⏻ Forzar apagado": "⏻ Forza spegnimento",
    "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\n"
    "como desenchufar un equipo real. Puede causar pérdida de datos no\n"
    "guardados; úsalo solo si la VM no responde al apagado normal.":
        "Interrompe la VM immediatamente, senza avvisare il sistema operativo guest —\n"
        "come staccare la spina a un computer reale. Può causare perdita di dati non\n"
        "salvati; usalo solo se la VM non risponde allo spegnimento normale.",
    "⟳ Reiniciar": "⟳ Riavvia",
    "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\n"
    "No es un apagado ordenado del sistema operativo invitado: simplemente\n"
    "reinicia el hardware virtual.":
        "Riavvia la VM (equivalente al pulsante di reset di un computer reale).\n"
        "Non è uno spegnimento ordinato del sistema operativo guest: semplicemente\n"
        "reimposta l'hardware virtuale.",
    "⟲ Forzar reinicio": "⟲ Forza riavvio",
    "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\n"
    "al sistema operativo invitado. Úsalo solo si la VM no responde ni al\n"
    "apagado ni al reinicio normales.":
        "Interrompe completamente la VM e la riavvia da zero, senza avvisare\n"
        "il sistema operativo guest. Usalo solo se la VM non risponde né allo\n"
        "spegnimento né al riavvio normali.",
    "⏸ Pausar (rápido)": "⏸ Pausa (rapida)",
    "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\n"
    "el estado (RAM y dispositivos) se pierde si el host se reinicia.":
        "Mette in pausa la VM senza salvare lo stato su disco. È istantaneo, ma\n"
        "lo stato (RAM e dispositivi) va perso se l'host si riavvia.",
    "▶ Reanudar": "▶ Riprendi",
    "Reanuda la ejecución de la VM pausada.":
        "Riprende l'esecuzione della VM in pausa.",
    "Reanudar la VM pausada. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Riprende la VM in pausa. Usa la freccia per più opzioni:\n"
        "• Pausa (rapida): ferma senza salvare lo stato su disco.\n"
        "• Riprendi: riprende l'esecuzione della VM.\n"
        "• Crea istantanea: salva lo stato su disco e mette in pausa.",
    "📸 Tomar Snapshot": "📸 Crea istantanea",
    "Guarda la RAM y el estado de los dispositivos a disco (como un\n"
    "snapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\n"
    "El snapshot aparecerá en la pestaña Snapshots y su captura de\n"
    "pantalla en el panel 'Último snapshot'.":
        "Salva la RAM e lo stato dei dispositivi su disco (come un'\n"
        "istantanea) e poi mette in pausa la VM. Richiede più tempo ma sopravvive ai riavvii.\n"
        "L'istantanea apparirà nella scheda Istantanee e la sua schermata\n"
        "nel pannello 'Ultima istantanea'.",
    "Iniciar VM": "Avvia VM",
    "Pausar/Reanudar VM": "Pausa/Riprendi VM",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\n"
    "Usa la flecha para más opciones (forzar, reiniciar).":
        "Spegnimento (ACPI): chiede alla VM di spegnersi in modo ordinato.\n"
        "Usa la freccia per più opzioni (forza, riavvia).",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Seleziona una VM per gestirla. Usa 'Nuova macchina virtuale' per crearne un'altra.",
    "Nueva máquina virtual": "Nuova macchina virtuale",
    "● Nueva VM": "● Nuova VM",

    # ================================================================
    # Toolbar Panoramica
    # ================================================================
    "\U0001f4bf Medios": "\U0001f4bf Supporti",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Cambia ISO en caliente, expulsa medios y conecta/desconecta\n"
    "USB sin reiniciar la máquina. Atajo: Ctrl+M.":
        "Supporti della VM: unità CD/DVD e dispositivi USB.\n"
        "Cambia ISO a caldo, espelli supporti e collega/scollega\n"
        "USB senza riavviare la macchina. Scorciatoia: Ctrl+M.",
    "\U0001f9ec Clonar": "\U0001f9ec Clona",
    "Crea una copia completa de esta VM en una carpeta nueva.":
        "Crea una copia completa di questa VM in una nuova cartella.",
    "\U0001f9ec Desenlazar": "\U0001f9ec Scollega",
    "Convierte este clon enlazado en un QCOW2 autónomo.\n"
    "Después, el clon deja de depender del original y puede\n"
    "moverse o copiarse por separado.\n\n"
    "Solo aparece cuando la VM seleccionada es un clon\n"
    "enlazado y está apagada.":
        "Converte questo clone collegato in un QCOW2 autonomo.\n"
        "Dopo di che, il clone non dipende più dall'originale e può\n"
        "essere spostato o copiato separatamente.\n\n"
        "Appare solo quando la VM selezionata è un clone\n"
        "collegato ed è spenta.",
    "⇩ Importar": "⇩ Importa",
    "Importar una VM desde una carpeta (con vm_config.ini) o desde\n"
    "un archivo .tar.gz / .zip exportado previamente.":
        "Importa una VM da una cartella (con vm_config.ini) o da\n"
        "un file .tar.gz / .zip esportato in precedenza.",
    "⇪ Exportar": "⇪ Esporta",
    "Exportar esta VM como carpeta, .tar.gz o .zip portable.\n"
    "Se omiten los archivos de runtime (pids, sockets, logs).":
        "Esporta questa VM come cartella, .tar.gz o .zip portatile.\n"
        "I file di runtime (pid, socket, log) vengono omessi.",
    "\U0001f4be Plantilla": "\U0001f4be Modello",
    "Guarda la configuración de hardware de esta VM como\n"
    "plantilla reutilizable. Se omiten discos, ISOs, MACs,\n"
    "carpetas compartidas, notas y reglas NAT.\n"
    "Aparecerá en el menú del botón '➕ Nueva VM'.":
        "Salva la configurazione hardware di questa VM come\n"
        "modello riutilizzabile. Dischi, ISO, MAC,\n"
        "cartelle condivise, note e regole NAT vengono omessi.\n"
        "Apparirà nel menu del pulsante '➕ Nuova VM'.",
    "\U0001f4dc Comando QEMU": "\U0001f4dc Comando QEMU",
    "Muestra el contenido de run_temp.sh: el comando exacto con\n"
    "el que QEMU está ejecutando (o ejecutó por última vez) esta\n"
    "VM. Solo está disponible si la VM se ha arrancado alguna vez.":
        "Mostra il contenuto di run_temp.sh: il comando esatto con\n"
        "cui QEMU sta eseguendo (o ha eseguito l'ultima volta) questa\n"
        "VM. Disponibile solo se la VM è stata avviata almeno una volta.",
    "\U0001f4dd Notas": "\U0001f4dd Note",
    "Notas libres sobre esta VM. Se guardan en vm_config.ini\n"
    "(extra.notes) y aparecen como aviso amarillo debajo del\n"
    "estado en esta misma pestaña.":
        "Note libere su questa VM. Vengono salvate in vm_config.ini\n"
        "(extra.notes) e appaiono come avviso giallo sotto lo\n"
        "stato in questa stessa scheda.",
    "\U0001f3f7 Etiqueta": "\U0001f3f7 Etichetta",
    "Grupo y color de esta VM. El grupo agrupa VMs en la lista\n"
    "lateral; el color se aplica como fondo del ítem.":
        "Gruppo e colore di questa VM. Il gruppo raggruppa le VM nell'elenco\n"
        "laterale; il colore viene applicato come sfondo dell'elemento.",
    "⚖ Comparar con defaults": "⚖ Confronta con i predefiniti",
    "Compara la configuración actual de esta VM con los\n"
    "valores por defecto del perfil del SO. Permite aplicar\n"
    "los defaults a un campo o a todos; los cambios se aplican\n"
    "a los widgets y se persisten al Guardar.":
        "Confronta la configurazione attuale di questa VM con i\n"
        "valori predefiniti del profilo del SO. Permette di applicare\n"
        "i predefiniti a un campo o a tutti; le modifiche vengono applicate\n"
        "ai widget e persistite al Salva.",
    "\U0001f5d1 Eliminar": "\U0001f5d1 Elimina",
    "Elimina esta VM (con opción de conservar los discos).":
        "Elimina questa VM (con opzione di conservare i dischi).",
    "\U0001f5d1\ufe0f Eliminar": "\U0001f5d1 Elimina",

    # ================================================================
    # Riepilogo: titolo
    # ================================================================
    "Resumen de Configuración": "Riepilogo della configurazione",

    # ================================================================
    # Messaggi di controllo VM
    # ================================================================
    "Pausar": "Pausa",
    "La máquina virtual no está corriendo.": "La macchina virtuale non è in esecuzione.",
    "Control de VM": "Controllo VM",
    "No se pudo cambiar el estado de la VM.\n\n{0}":
        "Impossibile cambiare lo stato della VM.\n\n{0}",
    "No se pudo pausar la VM.\n\n{0}":
        "Impossibile mettere in pausa la VM.\n\n{0}",
    "Reanudar": "Riprendi",
    "La máquina virtual ya está corriendo.": "La macchina virtuale è già in esecuzione.",
    "La máquina virtual no está pausada: no hay nada que reanudar.":
        "La macchina virtuale non è in pausa: non c'è nulla da riprendere.",
    "No se pudo reanudar la VM.\n\n{0}":
        "Impossibile riprendere la VM.\n\n{0}",
    "Apagar VM": "Spegni VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Impossibile inviare il comando di spegnimento.\n\n{0}",
    "Reiniciar VM": "Riavvia VM",
    "No se pudo enviar la orden de reinicio.\n\n{0}":
        "Impossibile inviare il comando di riavvio.\n\n{0}",
    "Forzar apagado": "Forza spegnimento",
    "Esto corta la VM de inmediato, sin avisar al sistema operativo invitado (como desenchufar un equipo real).\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "Questo interrompe la VM immediatamente, senza avvisare il sistema operativo guest (come staccare la spina a un computer reale).\n\nPuò causare perdita di dati non salvati all'interno della VM.\n\nVuoi continuare?",
    "Forzar reinicio": "Forza riavvio",
    "Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin avisar al sistema operativo invitado.\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "Questo interrompe la VM immediatamente e la riavvia da zero, senza avvisare il sistema operativo guest.\n\nPuò causare perdita di dati non salvati all'interno della VM.\n\nVuoi continuare?",
    "¿Deseas continuar?": "Vuoi continuare?",
}
