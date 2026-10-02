# -*- coding: utf-8 -*-
"""vm_it_tanda3c - Traduzioni in italiano - Tanda 3c.

Copre la scheda Libreria dei supporti completa:
  - Intestazione, filtri (SO / Arch. / Formato / Tipo / Origine).
  - Pulsanti superiori (Aggiungi file, Scansiona cartella, Scansiona VM).
  - Tabella colonne.
  - Pannello inferiore (Note, Tag, Colore + palette).
  - Barra pulsanti inferiore (Verifica / SHA256 / Modifica / Elimina /
    Apri cartella / Espandi / Comprimi).
  - Handler di media_library_mixin.
"""

TRANSLATIONS = {

    # ================================================================
    # Intestazione HTML
    # ================================================================
    "<b>Biblioteca de Medios</b><br>"
    "<span style='color:#666;font-size:11px;'>"
    "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
    "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
    "nivel que <code>VirtualMachines/</code>) y se reutilizan "
    "entre maquinas."
    "</span>":
        "<b>Libreria dei supporti</b><br>"
        "<span style='color:#666;font-size:11px;'>"
        "Tutte le ISO / IMG / DMG che usi con le tue VM, in un "
        "unico posto. Risiedono in <code>MediaLibrary/</code> (allo stesso "
        "livello di <code>VirtualMachines/</code>) e vengono riutilizzate "
        "tra le macchine."
        "</span>",

    # ================================================================
    # Filtri
    # ================================================================
    "Buscar por nombre, distro, tag...":
        "Cerca per nome, distro, tag...",
    "SO:": "SO:",
    "Todos": "Tutti",
    "Otros": "Altri",
    "Arq.:": "Arch.:",
    "Todas": "Tutte",
    "Universal": "Universale",
    "Sin especificar": "Non specificato",
    "Formato:": "Formato:",
    "Tipo:": "Tipo:",
    "Disco duro": "Disco rigido",
    "ISO": "ISO",
    "Disquete": "Floppy",
    "Otro": "Altro",
    "Origen:": "Origine:",
    "Manuales": "Manuali",
    "De VMs": "Da VM",
    "Huerfanas de VM": "Orfani di VM",

    # ================================================================
    # Pulsanti superiori
    # ================================================================
    "Anadir archivo(s)": "Aggiungi file",
    "Escanear carpeta": "Scansiona cartella",
    "Busca archivos de medios dentro de MediaLibrary/ que aun no "
    "esten registrados, y detecta entradas huerfanas (archivo "
    "desaparecido del disco).":
        "Cerca file multimediali dentro MediaLibrary/ non ancora "
        "registrati e rileva voci orfane (file scomparso dal disco).",
    "\U0001f50e Escanear VMs": "\U0001f50e Scansiona VM",
    "Recorre todas las VMs en VirtualMachines/ y registra sus "
    "discos duros, ISOs y disquetes en la biblioteca.\n\n"
    "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
    "todas las VMs en la columna 'Usada por'. Las entradas que ya "
    "no usa ninguna VM se marcan como huerfanas pero no se borran.":
        "Percorre tutte le VM in VirtualMachines/ e registra i loro "
        "dischi rigidi, ISO e floppy nella libreria.\n\n"
        "La stessa ISO usata da piu VM appare UNA SOLA VOLTA, con "
        "tutte le VM nella colonna 'Usata da'. Le voci che non "
        "sono piu usate da nessuna VM vengono contrassegnate come orfane ma non eliminate.",

    # ================================================================
    # Tabella colonne
    # ================================================================
    "SO": "SO",
    "Version": "Versione",
    "Arq.": "Arch.",
    "Tamaño real": "Dimensione reale",
    "Usada por": "Usata da",
    "Ultimo uso": "Ultimo utilizzo",
    "Ruta": "Percorso",
    "Estado": "Stato",
    "Tamano": "Dimensione",

    # ================================================================
    # Pannello inferiore (Note / Tag / Colore)
    # ================================================================
    "<b>Notas:</b>": "<b>Note:</b>",
    "Notas libres sobre esta entrada (uso previsto, si dio "
    "problemas, driver necesario, etc.)":
        "Note libere su questa voce (uso previsto, se ha dato "
        "problemi, driver necessario, ecc.)",
    "<b>Tags:</b>": "<b>Tag:</b>",
    "Separados por coma (ej.: probado, servidor, rapiro)":
        "Separati da virgola (es.: testato, server, veloce)",
    "<b>Color:</b>": "<b>Colore:</b>",
    "(Sin color)": "(Nessun colore)",
    "Rojo": "Rosso",
    "Naranja": "Arancione",
    "Ambar": "Ambra",
    "Verde": "Verde",
    "Verde azul": "Verde acqua",
    "Azul": "Blu",
    "Indigo": "Indaco",
    "Violeta": "Viola",
    "Rosa": "Rosa",
    "Gris": "Grigio",

    # ================================================================
    # Barra pulsanti inferiore
    # ================================================================
    "Verificar": "Verifica",
    "Calcular SHA256": "Calcola SHA256",
    "Editar": "Modifica",
    "Eliminar": "Elimina",
    "Abrir carpeta": "Apri cartella",
    "Agrandar": "Espandi",
    "Compactar": "Comprimi",

    # ================================================================
    # Intestazione informativa
    # ================================================================
    "Biblioteca de Medios": "Libreria dei supporti",
    "Biblioteca no disponible.": "Libreria non disponibile.",
    "{0} entrada(s) mostradas de {1} | Tamano total: {2}":
        "{0} voce(i) mostrata(e) di {1} | Dimensione totale: {2}",
    "huerfano": "orfano",
    "verificado?": "verificato?",

    # ================================================================
    # Handler: aggiungi file
    # ================================================================
    "La biblioteca no esta disponible.":
        "La libreria non e disponibile.",
    "Anadir archivos a la biblioteca":
        "Aggiungi file alla libreria",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos los archivos (*)":
        "Immagini disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Tutti i file (*)",

    # ================================================================
    # Handler: scansiona VM
    # ================================================================
    "Escanear VMs": "Scansiona VM",
    "No se pudieron escanear las VMs.\n\n{0}":
        "Impossibile scansionare le VM.\n\n{0}",
    "Archivos unicos encontrados en VMs: {0}.":
        "File unici trovati nelle VM: {0}.",
    "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca.":
        "- {0} supporto(i) nuovo(i) aggiunto(i) alla libreria.",
    "- {0} entrada(s) actualizada(s) con la lista de VMs que las usan.":
        "- {0} voce(i) aggiornata(e) con l'elenco delle VM che le usano.",
    "- {0} entrada(s) ya no las usa ninguna VM (siguen visibles; filtro Origen = 'Huerfanas de VM').":
        "- {0} voce(i) non sono piu usate da nessuna VM (restano visibili; filtro Origine = 'Orfani di VM').",
    "Sin cambios: la biblioteca ya estaba al dia.":
        "Nessuna modifica: la libreria era gia aggiornata.",

    # ================================================================
    # Handler: scansiona cartella
    # ================================================================
    "Escanear": "Scansiona",
    "No se pudo escanear.\n\n{0}":
        "Impossibile scansionare.\n\n{0}",
    "No hay archivos nuevos ni entradas huerfanas.":
        "Non ci sono file nuovi ne voci orfane.",
    "{0} archivo(s) nuevos encontrados:":
        "{0} file nuovo(i) trovato(i):",
    "  ... y {0} mas": "  ... e altri {0}",
    "{0} entrada(s) huerfanas (archivo ya no existe):":
        "{0} voce(i) orfana(e) (file non piu esistente):",
    "Anadir los archivos nuevos a la biblioteca?":
        "Aggiungere i nuovi file alla libreria?",

    # ================================================================
    # Handler: espandi disco
    # ================================================================
    "Selecciona una entrada primero.":
        "Seleziona prima una voce.",
    "Solo se pueden agrandar discos duros (QCOW2/RAW).":
        "Solo i dischi rigidi (QCOW2/RAW) possono essere espansi.",
    "El archivo no existe:\n{0}":
        "Il file non esiste:\n{0}",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de agrandarlo.":
        "Questo disco e usato dalla VM '{0}', che e accesa.\n\nSpegnila prima di espanderlo.",
    "\u2197 Agrandar disco": "\u2197 Espandi disco",
    "Tama\u00f1o actual:": "Dimensione attuale:",
    "Nuevo tama\u00f1o:": "Nuova dimensione:",
    "Ejemplo: 120G (solo crecer)": "Esempio: 120G (solo crescita)",
    "El disco solo puede CRECER. Agrandar el archivo NO agranda\n"
    "la partici\u00f3n dentro del guest: hay que ampliarla tambi\u00e9n desde\n"
    "el sistema invitado para aprovechar el nuevo espacio.":
        "Il disco puo solo CRESCERE. Espandere il file NON espande\n"
        "la partizione all'interno del guest: occorre estenderla anche dal\n"
        "sistema guest per sfruttare il nuovo spazio.",
    "Tama\u00f1o inv\u00e1lido": "Dimensione non valida",
    "'{0}' no es un tama\u00f1o v\u00e1lido.": "'{0}' non e una dimensione valida.",
    "No se puede encoger": "Impossibile ridurre",
    "Actual: {0}, indicado {1}.\n\nEl valor se ha restaurado al tama\u00f1o actual.":
        "Attuale: {0}, indicato {1}.\n\nIl valore e stato ripristinato alla dimensione attuale.",
    "Aplicar": "Applica",
    "No se pudo agrandar el disco.\n\n{0}":
        "Impossibile espandere il disco.\n\n{0}",
    "Disco agrandado": "Disco espanso",
    "Se agrand\u00f3 correctamente a {0}.\n\nRecuerda ampliar tambi\u00e9n la partici\u00f3n dentro del sistema invitado.":
        "Espanso correttamente a {0}.\n\nRicorda di estendere anche la partizione all'interno del sistema guest.",

    # ================================================================
    # Handler: comprimi disco
    # ================================================================
    "Solo se pueden compactar discos en formato QCOW2.":
        "Solo i dischi in formato QCOW2 possono essere compressi.",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de compactarlo: QEMU mantiene un lock de\nescritura sobre el archivo y el compactado fallaria.":
        "Questo disco e usato dalla VM '{0}', che e accesa.\n\nSpegnila prima di comprimerlo: QEMU mantiene un lock di\nscrittura sul file e la compressione fallirebbe.",
    "\n\n\u26a0 Este disco lo usan VMs apagadas: {0}.\nSe recomienda hacer un backup antes de compactar.":
        "\n\n\u26a0 Questo disco e usato da VM spente: {0}.\nSi consiglia di fare un backup prima di comprimere.",
    "Confirmar compactado": "Conferma compressione",
    "\u00bfCompactar '{0}'?\n\nReescribe el QCOW2 eliminando bloques no usados: reduce el\narchivo en el host SIN cambiar el tama\u00f1o virtual que ve el\ninvitado.{1}\n\n\u00bfContinuar?":
        "Comprimere '{0}'?\n\nRiscrive il QCOW2 eliminando i blocchi non usati: riduce il\nfile sull'host SENZA cambiare la dimensione virtuale che vede il\nguest.{1}\n\nContinuare?",
    "Compactando... {0}%": "Compressione... {0}%",
    "No se pudo compactar.\n\n{0}":
        "Impossibile comprimere.\n\n{0}",
    "Disco compactado": "Disco compresso",
    "'{0}' compactado.\n\nAntes: {1}\nDespu\u00e9s: {2}\nAhorro: {3}":
        "'{0}' compresso.\n\nPrima: {1}\nDopo: {2}\nRisparmio: {3}",
    "Compactando '{0}'": "Compressione di '{0}'",
    "Reescribiendo el QCOW2 sin bloques no usados...":
        "Riscrittura del QCOW2 senza blocchi non usati...",

    # ================================================================
    # Handler: verifica / SHA256
    # ================================================================
    "El archivo ya no existe:\n{0}":
        "Il file non esiste piu:\n{0}",
    "El archivo existe. No hay sha256 guardado para comparar; usa 'Calcular SHA256' si quieres uno.":
        "Il file esiste. Nessun sha256 salvato per il confronto; usa 'Calcola SHA256' se ne vuoi uno.",
    "Archivo presente y sha256 coincide.":
        "File presente e sha256 corrisponde.",
    "sha256 NO coincide.\n\nEsperado: {0}\nActual:   {1}":
        "sha256 NON corrisponde.\n\nAtteso:   {0}\nAttuale:  {1}",
    "SHA256": "SHA256",
    "sha256 calculado y guardado:\n\n{0}":
        "sha256 calcolato e salvato:\n\n{0}",
    "Error: {0}": "Errore: {0}",
    "Calculando sha256 \u2014 {0}": "Calcolo sha256 \u2014 {0}",

    # ================================================================
    # Handler: modifica metadati
    # ================================================================
    "Editar \u2014 {0}": "Modifica \u2014 {0}",
    "Nombre:": "Nome:",
    "Distro:": "Distro:",
    "Version:": "Versione:",
    "Arquitectura:": "Architettura:",
    "URL origen:": "URL di origine:",
    "No se pudo guardar: {0}": "Impossibile salvare: {0}",

    # ================================================================
    # Handler: elimina
    # ================================================================
    "Eliminar entrada": "Elimina voce",
    "Eliminar '{0}' de la biblioteca?":
        "Eliminare '{0}' dalla libreria?",
    "Quitar del indice": "Rimuovi dall'indice",
    "Eliminar tambien el archivo": "Elimina anche il file",

    # ================================================================
    # Handler: apri cartella
    # ================================================================
    "La carpeta no existe:\n{0}":
        "La cartella non esiste:\n{0}",

    # ================================================================
    # Tooltip barra pulsanti
    # ================================================================
    "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\n"
    "biblioteca. Requiere que ninguna VM lo esté usando en\n"
    "ese momento. El disco solo puede crecer.":
        "Aumenta la dimensione virtuale di un disco QCOW2/RAW della\n"
        "libreria. Richiede che nessuna VM lo stia usando in\n"
        "quel momento. Il disco puo solo crescere.",
    "Reescribe el QCOW2 sin bloques no usados, reduciendo el\n"
    "archivo en el host. No cambia el tamaño virtual que ve el\n"
    "sistema invitado.":
        "Riscrive il QCOW2 senza i blocchi non usati, riducendo il\n"
        "file sull'host. Non cambia la dimensione virtuale che vede il\n"
        "sistema guest.",
    "Comprueba que el archivo exista en disco y, si hay sha256 calculado, que coincida.":
        "Verifica che il file esista sul disco e, se c'e uno sha256 calcolato, che corrisponda.",
    "Calcula el sha256 del archivo (tarda segun el tamano). Util para detectar duplicados o descargas corruptas.":
        "Calcola lo sha256 del file (richiede tempo in base alla dimensione). Utile per rilevare duplicati o download corrotti.",
    "Edita los metadatos de la entrada: nombre, distro, version, arquitectura, notas, tags y color.":
        "Modifica i metadati della voce: nome, distro, versione, architettura, note, tag e colore.",
    "Elimina la entrada del indice. Opcionalmente borra tambien el archivo del disco (solo si vive dentro de MediaLibrary/).":
        "Elimina la voce dall'indice. Opzionalmente elimina anche il file dal disco (solo se risiede dentro MediaLibrary/).",
    "Abre la carpeta que contiene el archivo en el explorador del sistema.":
        "Apre la cartella che contiene il file nel file manager di sistema.",
}
