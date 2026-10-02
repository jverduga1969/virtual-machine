# -*- coding: utf-8 -*-
"""vm_it_tanda3a - Traduzioni in italiano - Tanda 3a.

Copre la scheda Istantanee completa:
  - Intestazione + avviso clone collegato.
  - Pulsanti Aggiorna/Crea/Ripristina/Rinomina/Elimina.
  - Tabella dischi + tabella istantanee + vista Elenco/Albero.
  - Anteprima con zoom.
  - snapshots_mixin.py: tutti i dialoghi e gli avvisi.
  - snapshots_graph.py: nodi dell'albero.
"""

TRANSLATIONS = {

    # ================================================================
    # Intestazione della scheda Istantanee
    # ================================================================
    "<b>Snapshots de la máquina virtual</b>":
        "<b>Istantanee della macchina virtuale</b>",
    "Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.":
        "Crea, ripristina, elimina e gestisci istantanee. L'applicazione controlla i dischi QCOW2 scrivibili, lo spazio libero e quali dischi faranno parte dell'istantanea prima di eseguirla.",
    "\u26a0 Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con \u2018\U0001f9ec Desenlazar\u2019 en la pestaña Resumen.":
        "\u26a0 Questa VM e un clone collegato (backing file QCOW2). Le istantanee complete (RAM + dispositivi) non possono essere ripristinate in QEMU con backing file; l'app usera sempre istantanee SOLO DISCO. Per avere istantanee complete, scollega prima il clone con \u2018\U0001f9ec Scollega\u2019 nella scheda Panoramica.",

    # ================================================================
    # Pulsanti della scheda
    # ================================================================
    "\U0001f504 Actualizar": "\U0001f504 Aggiorna",
    "\u2795 Crear": "\u2795 Crea",
    "\u21a9 Restaurar": "\u21a9 Ripristina",
    "\u270f Cambiar nombre": "\u270f Rinomina",
    "\U0001f5d1 Eliminar": "\U0001f5d1 Elimina",

    # ================================================================
    # Tabella dischi ammissibili
    # ================================================================
    "Formato": "Formato",
    "Tamaño virtual": "Dimensione virtuale",
    "Tamaño archivo": "Dimensione file",
    "Libre host": "Libero host",
    "Escritura": "Scrittura",
    "Snapshot": "Istantanea",
    "Sin operación de snapshot": "Nessuna operazione istantanea in corso",

    # ================================================================
    # Tabella istantanee
    # ================================================================
    "ID": "ID",
    "Tamaño VM": "Dimensione VM",
    "Fecha": "Data",
    "Reloj VM": "Orologio VM",

    # ================================================================
    # Vista Elenco/Albero + zoom anteprima
    # ================================================================
    "Vista:": "Vista:",
    "\U0001f4cb Lista": "\U0001f4cb Elenco",
    "\U0001f333 Organigrama": "\U0001f333 Albero",
    "Zoom:": "Zoom:",
    "Alejar la miniatura": "Riduci la miniatura",
    "Acercar la miniatura": "Ingrandisci la miniatura",
    "\u21ba Ajustar": "\u21ba Adatta",
    "Ajustar al tamaño original": "Adatta alla dimensione originale",
    "Sin captura de pantalla": "Nessuna schermata",

    # ================================================================
    # snapshots_graph.py
    # ================================================================
    "(sin miniatura)": "(senza miniatura)",
    "Restaurar este snapshot": "Ripristina questa istantanea",
    "Renombrar": "Rinomina",
    "\u270f Renombrar": "\u270f Rinomina",
    "\u2795 Crear snapshot hijo": "\u2795 Crea istantanea figlia",
    "\U0001f517 Establecer padre…": "\U0001f517 Imposta genitore…",
    "\u2b06 Mover a la raíz": "\u2b06 Sposta alla radice",

    # ================================================================
    # snapshots_mixin.py: creazione
    # ================================================================
    "Selecciona una máquina virtual.": "Seleziona una macchina virtuale.",
    "No se puede crear un snapshot completo.\n\n":
        "Impossibile creare un'istantanea completa.\n\n",
    "Espacio disponible": "Spazio disponibile",
    "{0}\n\n"
    "QEMU puede necesitar espacio adicional a medida que cambien los bloques. ¿Quieres continuar de todos modos?":
        "{0}\n\n"
        "QEMU potrebbe aver bisogno di spazio aggiuntivo man mano che i blocchi cambiano. Vuoi continuare comunque?",
    "Crear snapshot": "Crea istantanea",
    "Nombre del snapshot:": "Nome dell'istantanea:",
    "Clon enlazado: snapshot solo de discos":
        "Clone collegato: istantanea solo disco",
    "Esta VM es un clon enlazado (backing file QCOW2).\n\n"
    "QEMU no puede crear/restaurar snapshots completos\n"
    "(RAM + dispositivos) sobre un QCOW2 con backing\n"
    "file: al hacer loadvm QEMU aborta con una aserción\n"
    "interna (vmstate_load_next).\n\n"
    "Por seguridad se creará un snapshot SOLO DE DISCOS,\n"
    "que sí se puede restaurar con la VM apagada.\n\n"
    "Si necesitas un snapshot completo, desenlaza\n"
    "primero el clon (\U0001f9ec Desenlazar).":
        "Questa VM e un clone collegato (backing file QCOW2).\n\n"
        "QEMU non puo creare/ripristinare istantanee complete\n"
        "(RAM + dispositivi) su un QCOW2 con backing\n"
        "file: al loadvm QEMU si interrompe con un'asserzione\n"
        "interna (vmstate_load_next).\n\n"
        "Per sicurezza verra creata un'istantanea SOLO DISCO,\n"
        "che puo essere ripristinata con la VM spenta.\n\n"
        "Se hai bisogno di un'istantanea completa, scollega\n"
        "prima il clone (\U0001f9ec Scollega).",
    "Snapshot con la VM encendida": "Istantanea con la VM accesa",
    "La VM está encendida.\n\n"
    "Un snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y "
    "puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos "
    "observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\n"
    "Sí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
    "No = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\n"
    "Cancelar = no hacer nada.":
        "La VM e accesa.\n\n"
        "Un'istantanea COMPLETA deve salvare la RAM e lo stato di tutti i dispositivi e "
        "puo lasciare QEMU completamente occupato durante quel processo. Su questa VM abbiamo gia "
        "osservato che QEMU puo rimanere in STOP per molto tempo.\n\n"
        "Si = crea ISTANTANEA COMPLETA (VM + RAM + dispositivi + dischi).\n"
        "No = crea ISTANTANEA SOLO DISCO (veloce; non salva RAM ne finestre).\n"
        "Annulla = non fare nulla.",
    "Snapshot de discos creado": "Istantanea disco creata",
    "Se creó '{0}' en {1} QCOW2.\n\n"
    "Este snapshot no contiene la memoria RAM ni el estado de las ventanas. "
    "Para restaurarlo, la VM debe estar apagada.":
        "'{0}' e stata creata su {1} QCOW2.\n\n"
        "Questa istantanea non contiene la memoria RAM ne lo stato delle finestre. "
        "Per ripristinarla, la VM deve essere spenta.",
    "Error al crear snapshot de discos": "Errore durante la creazione dell'istantanea disco",
    "Error al crear snapshot": "Errore durante la creazione dell'istantanea",
    "No se pudo crear el snapshot completo.\n\n{0}":
        "Impossibile creare l'istantanea completa.\n\n{0}",
    "Ya hay una operación de snapshot en curso.":
        "E gia in corso un'operazione istantanea.",
    "La operación se ejecuta en segundo plano; la interfaz sigue "
    "disponible mientras QEMU procesa el snapshot.":
        "L'operazione viene eseguita in background; l'interfaccia rimane "
        "disponibile mentre QEMU elabora l'istantanea.",
    "Snapshot — {0}": "Istantanea — {0}",
    "Estado '{0}' guardado y VM pausada.":
        "Stato '{0}' salvato e VM in pausa.",
    "Snapshot '{0}' eliminado.": "Istantanea '{0}' eliminata.",
    "Snapshot '{0}' restaurado.": "Istantanea '{0}' ripristinata.",
    "Snapshot '{0}' creado.": "Istantanea '{0}' creata.",
    "El snapshot '{0}' fue creado y confirmado por QEMU.":
        "L'istantanea '{0}' e stata creata e confermata da QEMU.",
    "VM pausada": "VM in pausa",
    "Estado guardado como '{0}'.\n\nLa VM quedó pausada. "
    "Puedes reanudarla con el botón Pausar/Reanudar.":
        "Stato salvato come '{0}'.\n\nLa VM e stata messa in pausa. "
        "Puoi riprenderla con il pulsante Pausa/Riprendi.",
    "Snapshot eliminado": "Istantanea eliminata",
    "Se eliminó '{0}'.": "'{0}' e stata eliminata.",
    "Snapshot restaurado": "Istantanea ripristinata",
    "Se restauró '{0}'.": "'{0}' e stata ripristinata.",
    "Snapshot creado": "Istantanea creata",
    "Error al eliminar snapshot": "Errore durante l'eliminazione dell'istantanea",
    "Error al guardar estado": "Errore durante il salvataggio dello stato",
    "Error al restaurar snapshot": "Errore durante il ripristino dell'istantanea",
    "CREACIÓN": "CREAZIONE",
    "ELIMINACIÓN": "ELIMINAZIONE",
    "GUARDADO": "SALVATAGGIO",
    "RESTAURACIÓN": "RIPRISTINO",
    "No se pudo completar la operación de snapshot '{0}'.\n\n{1}":
        "Impossibile completare l'operazione istantanea '{0}'.\n\n{1}",

    # ================================================================
    # snapshots_mixin.py: ripristino
    # ================================================================
    "¿Restaurar '{0}'?\n\nLa VM volverá al estado del snapshot.":
        "Ripristinare '{0}'?\n\nLa VM tornera allo stato dell'istantanea.",
    "Snapshot solo de discos": "Istantanea solo disco",
    "El snapshot '{0}' es solo de discos (no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM primero.\n"
    "La VM volverá al estado del snapshot.\n\n"
    "¿Apagar la VM ahora y restaurar el snapshot?":
        "L'istantanea '{0}' e solo disco (non contiene la RAM).\n\n"
        "Per ripristinarla e necessario spegnere prima la VM.\n"
        "La VM tornera allo stato dell'istantanea.\n\n"
        "Spegnere la VM ora e ripristinare l'istantanea?",
    "Apagar la VM": "Spegni la VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Impossibile inviare il comando di spegnimento.\n\n{0}",
    "Se restauró '{0}' mediante snapshot-load.":
        "'{0}' e stata ripristinata tramite snapshot-load.",
    "Restauración parcial": "Ripristino parziale",
    "El snapshot se restauró en algunos discos, pero falló en otros:\n\n":
        "L'istantanea e stata ripristinata su alcuni dischi, ma ha fallito su altri:\n\n",
    "Se restauró el snapshot de disco en los QCOW2 elegibles. "
    "Con la VM apagada no se restaura el estado de RAM/CPU.":
        "L'istantanea disco e stata ripristinata sui QCOW2 ammissibili. "
        "Con la VM spenta, lo stato di RAM/CPU non viene ripristinato.",
    "El snapshot '{0}' es solo de discos "
    "(no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM y volver "
    "a intentarlo. QEMU no puede restaurar snapshots "
    "sin vmstate con la VM encendida.":
        "L'istantanea '{0}' e solo disco "
        "(non contiene la RAM).\n\n"
        "Per ripristinarla e necessario spegnere la VM e "
        "riprovare. QEMU non puo ripristinare istantanee "
        "senza vmstate con la VM accesa.",
    "La VM volvió a un estado operativo después de restaurar '{0}'.\n\n"
    "QEMU no confirmó el fin del job dentro del tiempo de espera, "
    "pero la restauración se aplicó.":
        "La VM e tornata a uno stato operativo dopo il ripristino di '{0}'.\n\n"
        "QEMU non ha confermato la fine del job entro il timeout, "
        "ma il ripristino e stato applicato.",
    "No se pudo restaurar el snapshot.\n\n{0}":
        "Impossibile ripristinare l'istantanea.\n\n{0}",
    "No se puede restaurar este snapshot": "Impossibile ripristinare questa istantanea",
    "Apagado no completado": "Spegnimento non completato",
    "La VM no se apagó dentro del tiempo máximo (90 s).\n\n"
    "Puede que el sistema invitado esté colgado. Usa el botón\n"
    "'Forzar apagado' de la lista lateral, luego vuelve a intentar\n"
    "restaurar el snapshot con la VM ya apagada.":
        "La VM non si e spenta entro il tempo massimo (90 s).\n\n"
        "Il sistema guest potrebbe essere bloccato. Usa il pulsante\n"
        "'Forza spegnimento' nell'elenco laterale, poi prova di nuovo\n"
        "a ripristinare l'istantanea con la VM gia spenta.",

    # ================================================================
    # snapshots_mixin.py: eliminazione
    # ================================================================
    "¿Eliminar '{0}'?": "Eliminare '{0}'?",
    "Eliminar snapshot": "Elimina istantanea",
    "Eliminación parcial": "Eliminazione parziale",
    "El snapshot se eliminó de algunos discos, pero falló en otros:\n\n":
        "L'istantanea e stata eliminata da alcuni dischi, ma ha fallito su altri:\n\n",
    "No se pudo eliminar el snapshot.\n\n{0}":
        "Impossibile eliminare l'istantanea.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: rinomina
    # ================================================================
    "Cambiar nombre": "Rinomina",
    "Nuevo nombre para '{0}':": "Nuovo nome per '{0}':",
    "Cambiar nombre de snapshot": "Rinomina istantanea",
    "QEMU no proporciona un renombrado interno directo. "
    "Esta acción creará un snapshot nuevo con el estado ACTUAL "
    "de la VM y eliminará el anterior.\n\n¿Continuar?":
        "QEMU non fornisce una rinomina interna diretta. "
        "Questa azione creera una nuova istantanea con lo stato ATTUALE "
        "della VM ed eliminera la precedente.\n\nContinuare?",
    "Cambio de nombre parcial": "Rinomina parziale",
    "El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n":
        "La nuova istantanea e stata creata su alcuni dischi, ma ci sono stati errori:\n\n",
    "Error al cambiar nombre": "Errore durante la rinomina",
    "No se pudo cambiar el nombre.\n\n{0}":
        "Impossibile cambiare il nome.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: avvisi VirtIO-GPU / clone collegato
    # ================================================================
    "Snapshot con VirtIO-GPU": "Istantanea con VirtIO-GPU",
    "Esta VM está configurada con gráficos '{0}', que no permiten\n"
    "RESTAURAR snapshots completos en QEMU (RAM + dispositivos).\n"
    "\n"
    "El snapshot se puede crear, pero al intentar restaurarlo QEMU\n"
    "fallará con: 'Failed to load element of type virtio for virtio'.\n"
    "\n"
    "Opciones:\n"
    "  • Usar snapshot SOLO DE DISCOS (elegir 'No' en el siguiente\n"
    "    diálogo). No guarda RAM ni estado de ventanas, pero se\n"
    "    restaura sin problema con la VM apagada.\n"
    "  • Cambiar Gráficos/GPU a 'Red Hat QXL 2D' o 'VMware SVGA II',\n"
    "    reiniciar la VM y crear snapshots completos.\n"
    "\n"
    "¿Crear el snapshot igualmente?":
        "Questa VM e configurata con grafica '{0}', che non permette\n"
        "di RIPRISTINARE istantanee complete in QEMU (RAM + dispositivi).\n"
        "\n"
        "L'istantanea puo essere creata, ma al momento del ripristino QEMU\n"
        "fallira con: 'Failed to load element of type virtio for virtio'.\n"
        "\n"
        "Opzioni:\n"
        "  • Usare un'istantanea SOLO DISCO (scegli 'No' nel prossimo\n"
        "    dialogo). Non salva RAM ne stato delle finestre, ma\n"
        "    puo essere ripristinata senza problemi con la VM spenta.\n"
        "  • Cambiare Grafica/GPU in 'Red Hat QXL 2D' o 'VMware SVGA II',\n"
        "    riavviare la VM e creare istantanee complete.\n"
        "\n"
        "Creare l'istantanea comunque?",
    "QEMU no puede restaurar el snapshot por un problema conocido "
    "con el dispositivo VirtIO-GPU.\n\n"
    "Detalle técnico:\n"
    "  VirtIO-GPU guarda un estado interno que no es serializable "
    "de forma fiable. QEMU intenta reconstruirlo al restaurar y "
    "falla. No es un bug de la app, es una limitación del motor.\n\n"
    "Cómo resolverlo:\n"
    "  1. Abre Configuración → Pantalla.\n"
    "  2. Cambia 'Gráficos / GPU' de '{0}' a 'Red Hat QXL 2D'.\n"
    "  3. Reinicia la VM (apágala y vuelve a arrancarla).\n"
    "  4. Crea snapshots nuevos a partir de ese momento: se podrán "
    "restaurar sin problemas.\n\n"
    "Los snapshots antiguos creados con virtio-gpu no se pueden "
    "recuperar (QEMU no puede reconstruir su estado). Si ya no los "
    "necesitas, elimínalos.":
        "QEMU non puo ripristinare l'istantanea a causa di un problema noto "
        "con il dispositivo VirtIO-GPU.\n\n"
        "Dettaglio tecnico:\n"
        "  VirtIO-GPU conserva uno stato interno che non e serializzabile "
        "in modo affidabile. QEMU tenta di ricostruirlo al ripristino e "
        "fallisce. Non e un bug dell'app, e una limitazione del motore.\n\n"
        "Come risolvere:\n"
        "  1. Apri Configurazione → Schermo.\n"
        "  2. Cambia 'Grafica / GPU' da '{0}' a 'Red Hat QXL 2D'.\n"
        "  3. Riavvia la VM (spegni e riavvia).\n"
        "  4. Crea nuove istantanee da quel momento: potranno essere "
        "ripristinate senza problemi.\n\n"
        "Le istantanee precedenti create con virtio-gpu non possono essere "
        "recuperate (QEMU non puo ricostruirne lo stato). Se non ti servono "
        "piu, eliminale.",
    "La VM es un clon enlazado (backing file QCOW2) y el "
    "snapshot '{0}' fue creado en modo COMPLETO "
    "(RAM + dispositivos).\n\n"
    "QEMU no puede restaurar snapshots completos sobre un QCOW2 "
    "con backing file: al ejecutar loadvm aborta con una aserción "
    "interna (vmstate_load_next) y el proceso muere. De ahí el "
    "'Conexión reinicializada' que has visto.\n\n"
    "Qué hacer:\n"
    "  • Los snapshots que crees A PARTIR DE AHORA en este clon "
    "serán solo de discos (la app ya lo fuerza) y se podrán "
    "restaurar.\n"
    "  • Este snapshot antiguo no se puede restaurar. Elimínalo "
    "si ya no lo necesitas.\n"
    "  • Si necesitas snapshots completos, desenlaza el clon con "
    "'\U0001f9ec Desenlazar' (convierte el delta en un QCOW2 autónomo).":
        "La VM e un clone collegato (backing file QCOW2) e l'"
        "istantanea '{0}' e stata creata in modalita COMPLETA "
        "(RAM + dispositivi).\n\n"
        "QEMU non puo ripristinare istantanee complete su un QCOW2 "
        "con backing file: al loadvm si interrompe con un'asserzione "
        "interna (vmstate_load_next) e il processo muore. Da qui il "
        "'Connection reset' che hai visto.\n\n"
        "Cosa fare:\n"
        "  • Le istantanee che crei DA ORA in poi su questo clone "
        "saranno solo disco (l'app lo forza gia) e potranno essere "
        "ripristinate.\n"
        "  • Questa istantanea vecchia non puo essere ripristinata. "
        "Eliminala se non ti serve piu.\n"
        "  • Se hai bisogno di istantanee complete, scollega il clone con "
        "'\U0001f9ec Scollega' (converte il delta in un QCOW2 autonomo).",

    # ================================================================
    # snapshots_mixin.py: schermate / anteprima
    # ================================================================
    "Sin capturas de snapshot": "Nessuna schermata di istantanea",
    "Los snapshots creados con la VM en ejecución guardan una "
    "captura de pantalla que se muestra aquí.":
        "Le istantanee create con la VM in esecuzione salvano una "
        "schermata che viene mostrata qui.",
    "Captura no legible": "Schermata non leggibile",
    "Restaurar snapshot": "Ripristina istantanea",
    "No hay ningún snapshot reciente para restaurar.":
        "Non c'e nessuna istantanea recente da ripristinare.",
    "Existe una captura para '{0}', pero ese snapshot ya no "
    "aparece en la lista de la VM (puede haber sido eliminado). "
    "Actualiza la pestaña Snapshots o elimínalo manualmente.":
        "Esiste una schermata per '{0}', ma quell'istantanea non "
        "appare piu nell'elenco della VM (potrebbe essere stata eliminata). "
        "Aggiorna la scheda Istantanee o eliminala manualmente.",

    # ================================================================
    # snapshots_mixin.py: crea figlia / imposta genitore
    # ================================================================
    "Organigrama": "Albero",
    "No hay otros snapshots para elegir como padre.":
        "Non ci sono altre istantanee da scegliere come genitore.",
    "Establecer padre": "Imposta genitore",
    "Padre para '{0}':": "Genitore per '{0}':",
    "(ninguno — mover a la raíz)": "(nessuno — sposta alla radice)",
    "Nuevo snapshot hijo": "Nuova istantanea figlia",
    "Nombre del snapshot (hijo de '{0}'):":
        "Nome dell'istantanea (figlia di '{0}'):",
    "No se pudo crear el snapshot.\n\n{0}":
        "Impossibile creare l'istantanea.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: solo disco
    # ================================================================
    "(solo disco)": "(solo disco)",
}
