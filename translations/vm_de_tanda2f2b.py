# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2f-2b: Biblioteca de Medios.

Cubre: cabecera HTML, filtros, botones, cabeceras de tabla,
panel inferior (Notas/Tags/Color), estados dinamicos de la tabla
y todos los handlers (anadir / escanear / verificar / editar /
eliminar / agrandar / compactar / abrir carpeta).

Se fusiona con las tandas anteriores por _load_external_dict().
"""

TRANSLATIONS = {

    # ================================================================
    # Cabecera + filtros de la biblioteca
    # ================================================================
    "<b>Biblioteca de Medios</b><br>"
    "<span style='color:#666;font-size:11px;'>"
    "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
    "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
    "nivel que <code>VirtualMachines/</code>) y se reutilizan "
    "entre maquinas."
    "</span>":
        "<b>Medienbibliothek</b><br>"
        "<span style='color:#666;font-size:11px;'>"
        "Alle ISOs / IMGs / DMGs, die du mit deinen VMs verwendest, "
        "an einem einzigen Ort. Sie liegen in <code>MediaLibrary/</code> "
        "(auf derselben Ebene wie <code>VirtualMachines/</code>) und "
        "werden maschinenübergreifend genutzt."
        "</span>",
    "Buscar por nombre, distro, tag...":
        "Nach Name, Distro, Tag suchen...",
    "Origen:": "Quelle:",
    "Guest Tools": "Guest Tools",
    "Otros": "Andere",
    "Todas": "Alle",
    "Universal": "Universal",
    "Sin especificar": "Nicht angegeben",
    "Otro": "Andere",
    "Manuales": "Manuell",
    "De VMs": "Von VMs",
    "Huerfanas de VM": "VM-Verwaiste",
    "Anadir archivo(s)": "Datei(en) hinzufügen",
    "Escanear carpeta": "Ordner durchsuchen",
    "\U0001f50e Escanear VMs": "\U0001f50e VMs durchsuchen",
    "Busca archivos de medios dentro de MediaLibrary/ que aun no "
    "esten registrados, y detecta entradas huerfanas (archivo "
    "desaparecido del disco).":
        "Sucht in MediaLibrary/ nach Mediendateien, die noch nicht "
        "registriert sind, und erkennt verwaiste Einträge (Datei "
        "vom Datenträger verschwunden).",
    "Recorre todas las VMs en VirtualMachines/ y registra sus "
    "discos duros, ISOs y disquetes en la biblioteca.\n\n"
    "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
    "todas las VMs en la columna 'Usada por'. Las entradas que ya "
    "no usa ninguna VM se marcan como huerfanas pero no se borran.":
        "Durchläuft alle VMs in VirtualMachines/ und registriert deren "
        "Festplatten, ISOs und Disketten in der Bibliothek.\n\n"
        "Dasselbe ISO, das von mehreren VMs verwendet wird, erscheint "
        "NUR EINMAL, mit allen VMs in der Spalte 'Verwendet von'. "
        "Einträge, die von keiner VM mehr verwendet werden, werden als "
        "verwaist markiert, aber nicht gelöscht.",

    # ================================================================
    # Cabeceras de la tabla + panel inferior
    # ================================================================
    "Tamaño real": "Tatsächliche Größe",
    "Estado": "Status",
    "Ultimo uso": "Letzte Verwendung",
    "<b>Notas:</b>": "<b>Notizen:</b>",
    "Notas libres sobre esta entrada (uso previsto, si dio "
    "problemas, driver necesario, etc.)":
        "Freie Notizen zu diesem Eintrag (vorgesehene Nutzung, "
        "Probleme, benötigter Treiber usw.)",
    "<b>Tags:</b>": "<b>Tags:</b>",
    "Separados por coma (ej.: probado, servidor, rapiro)":
        "Mit Komma getrennt (z. B.: getestet, server, schnell)",
    "<b>Color:</b>": "<b>Farbe:</b>",
    "(Sin color)": "(Ohne Farbe)",
    "Rojo": "Rot",
    "Naranja": "Orange",
    "Ambar": "Bernstein",
    "Verde": "Grün",
    "Verde azul": "Blaugrün",
    "Azul": "Blau",
    "Indigo": "Indigo",
    "Violeta": "Violett",
    "Rosa": "Rosa",
    "Gris": "Grau",
    "Biblioteca no disponible.": "Bibliothek nicht verfügbar.",
    "{0} entrada(s) mostradas de {1} | Tamano total: {2}":
        "{0} Eintrag/Einträge angezeigt von {1} | Gesamtgröße: {2}",
    "huerfano": "verwaist",
    "verificado?": "verifiziert?",
    "Arq.:": "Arch.:",
    "ISO": "ISO",

    # ================================================================
    # Handlers: anadir / escanear
    # ================================================================
    "Biblioteca de Medios": "Medienbibliothek",
    "La biblioteca no esta disponible.": "Die Bibliothek ist nicht verfügbar.",
    "Anadir archivos a la biblioteca": "Dateien zur Bibliothek hinzufügen",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos los archivos (*)":
        "Festplattenabbilder (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Alle Dateien (*)",
    "Escanear VMs": "VMs durchsuchen",
    "No se pudieron escanear las VMs.\n\n{0}":
        "Die VMs konnten nicht durchsucht werden.\n\n{0}",
    "Archivos unicos encontrados en VMs: {0}.":
        "Eindeutige in VMs gefundene Dateien: {0}.",
    "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca.":
        "- {0} neue(s) Medium/Medien zur Bibliothek hinzugefügt.",
    "- {0} entrada(s) actualizada(s) con la lista de VMs que las usan.":
        "- {0} Eintrag/Einträge mit der Liste der VMs, die sie nutzen, aktualisiert.",
    "- {0} entrada(s) ya no las usa ninguna VM (siguen visibles; filtro Origen = 'Huerfanas de VM').":
        "- {0} Eintrag/Einträge werden von keiner VM mehr verwendet (weiterhin sichtbar; Filter Quelle = 'VM-Verwaiste').",
    "Sin cambios: la biblioteca ya estaba al dia.":
        "Keine Änderungen: Die Bibliothek war bereits aktuell.",
    "Escanear": "Durchsuchen",
    "No se pudo escanear.\n\n{0}":
        "Durchsuchen nicht möglich.\n\n{0}",
    "No hay archivos nuevos ni entradas huerfanas.":
        "Es gibt weder neue Dateien noch verwaiste Einträge.",
    "{0} archivo(s) nuevos encontrados:":
        "{0} neue Datei(en) gefunden:",
    "  ... y {0} mas": "  ... und {0} weitere",
    "{0} entrada(s) huerfanas (archivo ya no existe):":
        "{0} verwaiste(r) Eintrag/Einträge (Datei existiert nicht mehr):",
    "Anadir los archivos nuevos a la biblioteca?":
        "Die neuen Dateien zur Bibliothek hinzufügen?",

    # ================================================================
    # Handlers: agrandar disco
    # ================================================================
    "Agrandar": "Vergrößern",
    "Selecciona una entrada primero.": "Wähle zuerst einen Eintrag aus.",
    "Solo se pueden agrandar discos duros (QCOW2/RAW).":
        "Nur Festplatten (QCOW2/RAW) können vergrößert werden.",
    "El archivo no existe:\n{0}": "Die Datei existiert nicht:\n{0}",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de agrandarlo.":
        "Diese Festplatte wird von der VM '{0}' verwendet, die läuft.\n\nFahre sie herunter, bevor du sie vergrößerst.",
    "\u2197 Agrandar disco": "\u2197 Festplatte vergrößern",
    "Version:": "Version:",
    "Eliminar": "Löschen",
    "Tama\u00f1o actual:": "Aktuelle Größe:",
    "Nuevo tama\u00f1o:": "Neue Größe:",
    "Ejemplo: 120G (solo crecer)": "Beispiel: 120G (nur wachsen)",
    "El disco solo puede CRECER. Agrandar el archivo NO agranda\n"
    "la partici\u00f3n dentro del guest: hay que ampliarla tambi\u00e9n desde\n"
    "el sistema invitado para aprovechar el nuevo espacio.":
        "Die Festplatte kann nur WACHSEN. Das Vergrößern der Datei vergrößert NICHT\n"
        "die Partition im Gast: diese muss ebenfalls im Gastsystem erweitert\n"
        "werden, um den neuen Speicher zu nutzen.",
    "Tama\u00f1o inv\u00e1lido": "Ungültige Größe",
    "'{0}' no es un tama\u00f1o v\u00e1lido.": "'{0}' ist keine gültige Größe.",
    "No se puede encoger": "Verkleinern nicht möglich",
    "Actual: {0}, indicado {1}.\n\nEl valor se ha restaurado al tama\u00f1o actual.":
        "Aktuell: {0}, angegeben {1}.\n\nDer Wert wurde auf die aktuelle Größe zurückgesetzt.",
    "Aplicar": "Anwenden",
    "No se pudo agrandar el disco.\n\n{0}":
        "Die Festplatte konnte nicht vergrößert werden.\n\n{0}",
    "Disco agrandado": "Festplatte vergrößert",
    "Se agrand\u00f3 correctamente a {0}.\n\nRecuerda ampliar tambi\u00e9n la partici\u00f3n dentro del sistema invitado.":
        "Erfolgreich auf {0} vergrößert.\n\nDenke daran, auch die Partition im Gastsystem zu erweitern.",

    # ================================================================
    # Handlers: compactar disco
    # ================================================================
    "Compactar": "Komprimieren",
    "Solo se pueden compactar discos en formato QCOW2.":
        "Nur QCOW2-Festplatten können komprimiert werden.",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de compactarlo: QEMU mantiene un lock de\nescritura sobre el archivo y el compactado fallaria.":
        "Diese Festplatte wird von der VM '{0}' verwendet, die läuft.\n\nFahre sie herunter, bevor du sie komprimierst: QEMU hält eine Schreibsperre\nauf der Datei und die Komprimierung würde fehlschlagen.",
    "\n\n\u26a0 Este disco lo usan VMs apagadas: {0}.\nSe recomienda hacer un backup antes de compactar.":
        "\n\n\u26a0 Diese Festplatte wird von ausgeschalteten VMs verwendet: {0}.\nEin Backup vor dem Komprimieren wird empfohlen.",
    "Confirmar compactado": "Komprimierung bestätigen",
    "\u00bfCompactar '{0}'?\n\nReescribe el QCOW2 eliminando bloques no usados: reduce el\narchivo en el host SIN cambiar el tama\u00f1o virtual que ve el\ninvitado.{1}\n\n\u00bfContinuar?":
        "'{0}' komprimieren?\n\nSchreibt das QCOW2 neu, ohne unbenutzte Blöcke: reduziert\ndie Datei auf dem Host OHNE die virtuelle Größe zu ändern, die der\nGast sieht.{1}\n\nFortfahren?",
    "Compactando... {0}%": "Komprimiere... {0}%",
    "No se pudo compactar.\n\n{0}":
        "Komprimierung nicht möglich.\n\n{0}",
    "Disco compactado": "Festplatte komprimiert",
    "'{0}' compactado.\n\nAntes: {1}\nDespu\u00e9s: {2}\nAhorro: {3}":
        "'{0}' komprimiert.\n\nVorher: {1}\nNachher: {2}\nErsparnis: {3}",
    "Compactando '{0}'": "Komprimiere '{0}'",
    "Reescribiendo el QCOW2 sin bloques no usados...":
        "QCOW2 wird ohne unbenutzte Blöcke neu geschrieben...",

    # ================================================================
    # Handlers: verificar / sha256
    # ================================================================
    "Verificar": "Überprüfen",
    "El archivo ya no existe:\n{0}":
        "Die Datei existiert nicht mehr:\n{0}",
    "El archivo existe. No hay sha256 guardado para comparar; usa 'Calcular SHA256' si quieres uno.":
        "Die Datei existiert. Es ist kein sha256 zum Vergleich gespeichert; verwende 'SHA256 berechnen', falls du eines möchtest.",
    "Archivo presente y sha256 coincide.":
        "Datei vorhanden und sha256 stimmt überein.",
    "sha256 NO coincide.\n\nEsperado: {0}\nActual:   {1}":
        "sha256 stimmt NICHT überein.\n\nErwartet: {0}\nAktuell:   {1}",
    "SHA256": "SHA256",
    "sha256 calculado y guardado:\n\n{0}":
        "sha256 berechnet und gespeichert:\n\n{0}",
    "Error: {0}": "Fehler: {0}",
    "Calculando sha256 \u2014 {0}": "Berechne sha256 \u2014 {0}",

    # ================================================================
    # Handlers: editar / eliminar / abrir carpeta
    # ================================================================
    "Editar": "Bearbeiten",
    "Editar \u2014 {0}": "Bearbeiten \u2014 {0}",
    "Distro:": "Distro:",
    "Arquitectura:": "Architektur:",
    "URL origen:": "Quell-URL:",
    "No se pudo guardar: {0}": "Speichern fehlgeschlagen: {0}",
    "Eliminar entrada": "Eintrag löschen",
    "Eliminar '{0}' de la biblioteca?":
        "'{0}' aus der Bibliothek löschen?",
    "Quitar del indice": "Aus Index entfernen",
    "Eliminar tambien el archivo": "Datei ebenfalls löschen",
    "La carpeta no existe:\n{0}":
        "Der Ordner existiert nicht:\n{0}",

    # ================================================================
    # Botones inferiores con tooltips
    # ================================================================
    "Calcular SHA256": "SHA256 berechnen",
    "Abrir carpeta": "Ordner öffnen",
    "\u2197 Agrandar": "\u2197 Vergrößern",
    "\U0001f5dc Compactar": "\U0001f5dc Komprimieren",
    "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\n"
    "biblioteca. Requiere que ninguna VM lo esté usando en\n"
    "ese momento. El disco solo puede crecer.":
        "Die virtuelle Größe einer QCOW2/RAW-Festplatte in der\n"
        "Bibliothek erhöhen. Erfordert, dass sie derzeit von keiner VM\n"
        "verwendet wird. Die Festplatte kann nur wachsen.",
    "Reescribe el QCOW2 sin bloques no usados, reduciendo el\n"
    "archivo en el host. No cambia el tamaño virtual que ve el\n"
    "sistema invitado.":
        "Schreibt das QCOW2 ohne unbenutzte Blöcke neu und reduziert\n"
        "die Datei auf dem Host. Ändert nicht die virtuelle Größe,\n"
        "die das Gastsystem sieht.",
    "Comprueba que el archivo exista en disco y, si hay sha256 calculado, que coincida.":
        "Prüft, ob die Datei auf dem Datenträger existiert und, falls ein sha256 berechnet wurde, ob er übereinstimmt.",
    "Calcula el sha256 del archivo (tarda segun el tamano). Util para detectar duplicados o descargas corruptas.":
        "Berechnet den sha256 der Datei (Dauer abhängig von der Größe). Nützlich zur Erkennung von Duplikaten oder beschädigten Downloads.",
    "Edita los metadatos de la entrada: nombre, distro, version, arquitectura, notas, tags y color.":
        "Bearbeitet die Metadaten des Eintrags: Name, Distro, Version, Architektur, Notizen, Tags und Farbe.",
    "Elimina la entrada del indice. Opcionalmente borra tambien el archivo del disco (solo si vive dentro de MediaLibrary/).":
        "Löscht den Eintrag aus dem Index. Optional wird auch die Datei vom Datenträger gelöscht (nur, wenn sie sich in MediaLibrary/ befindet).",
    "Abre la carpeta que contiene el archivo en el explorador del sistema.":
        "Öffnet den Ordner mit der Datei im Dateimanager des Systems.",
}
