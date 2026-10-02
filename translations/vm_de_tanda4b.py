# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 4b.

Cubre: dialogos OVF/OVA (_ExportOvfDialog, _OvfImportPreviewDialog),
ciclo de vida de VM (import_vm, export_vm, clone_current_vm completo
y enlazado, unlink_linked_clone, delete_current_vm), dialogos simples
(edit_vm_label, edit_vm_notes, show_qemu_command, open_vm_folder,
show_vm_summary, _set_vm_status) y mensajes raise de OVF.

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # _ExportOvfDialog
    # ================================================================
    "Exportar como OVF/OVA - {0}": "Als OVF/OVA exportieren - {0}",
    "Exporta <b>{0}</b> como OVA (un solo archivo) o como OVF (carpeta con descriptor + discos sueltos).":
        "Exportiert <b>{0}</b> als OVA (einzelne Datei) oder als OVF (Ordner mit Deskriptor + losen Festplatten).",
    "Formato del disco": "Festplattenformat",
    "QCOW2 (recomendado) - instantaneo y comprimido":
        "QCOW2 (empfohlen) - sofort und komprimiert",
    "El disco se aplana (descartando snapshots internos) y se comprime con zlib. Ideal para reimportar en esta misma app.":
        "Die Festplatte wird vereinfacht (interne Snapshots werden verworfen) und mit zlib komprimiert. Ideal zur Reimportierung in dieselbe App.",
    "VMDK stream-optimized - maxima compatibilidad con VirtualBox/VMware":
        "VMDK stream-optimized - maximale Kompatibilität mit VirtualBox/VMware",
    "Requiere conversion previa con qemu-img. Tarda mas y necesita espacio temporal. VMDK stream-optimized ya descarta snapshots.":
        "Erfordert vorherige Konvertierung mit qemu-img. Dauert länger und benötigt temporären Speicher. VMDK stream-optimized verwirft Snapshots ohnehin.",
    "Opciones adicionales": "Zusätzliche Optionen",
    "Incluir medio de instalacion (BaseSystem.img)":
        "Installationsmedium einschließen (BaseSystem.img)",
    "Incluir archivos ISO en el OVA":
        "ISO-Dateien in das OVA einschließen",
    "Exportar": "Exportieren",
    "El disco se convertira a <b>VMDK stream-optimized</b>. Este formato ya descarta los snapshots internos.":
        "Die Festplatte wird in <b>VMDK stream-optimized</b> konvertiert. Dieses Format verwirft interne Snapshots ohnehin.",
    "Los discos QCOW2 se <b>aplanan y comprimen</b> automaticamente al exportar: se descartan los snapshots internos y se aplica compresion zlib. Reduce el OVA entre un 40% y un 60%.":
        "QCOW2-Festplatten werden beim Export automatisch <b>vereinfacht und komprimiert</b>: interne Snapshots werden verworfen und zlib-Kompression wird angewendet. Reduziert das OVA um 40% bis 60%.",

    # ================================================================
    # _OvfImportPreviewDialog
    # ================================================================
    "Importar OVF/OVA": "OVF/OVA importieren",
    "Se ha leído el descriptor OVF. Revisa los datos detectados y corrige lo que haga falta antes de importar.<br><br><i>El sistema operativo detectado puede ser ambiguo: ajústalo si el original no coincide.</i>":
        "Der OVF-Deskriptor wurde gelesen. Überprüfe die erkannten Daten und korrigiere, was nötig ist, bevor du importierst.<br><br><i>Das erkannte Betriebssystem kann mehrdeutig sein: Passe es an, wenn das Original nicht übereinstimmt.</i>",
    "(desconocido)": "(unbekannt)",
    "(sin nombre)": "(ohne Namen)",
    "(sin discos)": "(ohne Festplatten)",
    "<b>Detectado en el OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}":
        "<b>Im OVF erkannt:</b><br>OS: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Festplatten: {4} — {5}",
    "Nombre de la VM:": "VM-Name:",
    "GNU / Linux": "GNU / Linux",
    "Microsoft Windows": "Microsoft Windows",
    "Android (Android-x86 / Bliss OS)": "Android (Android-x86 / Bliss OS)",
    "Plataforma:": "Plattform:",
    "Distribución / versión:": "Distribution / Version:",
    "Importar solo la configuración (sin copiar los discos)":
        "Nur die Konfiguration importieren (ohne Festplatten zu kopieren)",
    "Si está marcado, se importan solo los datos del descriptor (CPU, RAM, red, sistema operativo) y NO se convierten ni copian los discos. Útil para reutilizar una configuración sin duplicar gigabytes de disco.":
        "Wenn aktiviert, werden nur die Daten des Deskriptors importiert (CPU, RAM, Netzwerk, Betriebssystem) und die Festplatten werden NICHT konvertiert oder kopiert. Nützlich, um eine Konfiguration wiederzuverwenden, ohne Gigabytes an Festplatte zu duplizieren.",
    "Importar": "Importieren",
    "Distribución:": "Distribution:",
    "Versión de Windows:": "Windows-Version:",
    "Versión de macOS:": "macOS-Version:",
    "Distribución Android:": "Android-Distribution:",
    "Debes escribir un nombre para la VM importada.":
        "Du musst einen Namen für die importierte VM eingeben.",
    "macOS": "macOS",

    # ================================================================
    # edit_vm_label
    # ================================================================
    "Etiqueta de la VM": "VM-Bezeichnung",
    "Etiqueta - {0}": "Bezeichnung - {0}",
    "Grupo y color para <b>{0}</b>. El grupo es texto libre: escribe uno nuevo para crearlo. El color se aplica como fondo suave del ítem en la lista lateral.":
        "Gruppe und Farbe für <b>{0}</b>. Die Gruppe ist freier Text: Gib eine neue ein, um sie zu erstellen. Die Farbe wird als weicher Hintergrund des Eintrags in der Seitenliste angewendet.",
    "(sin grupo)": "(ohne Gruppe)",
    "Grupo:": "Gruppe:",
    "<b>Color:</b>": "<b>Farbe:</b>",
    "Sin color": "Ohne Farbe",
    "Quitar etiqueta": "Bezeichnung entfernen",
    "Guardar": "Speichern",
    "Etiqueta": "Bezeichnung",
    "No se pudo guardar la etiqueta.\n\n{0}":
        "Die Bezeichnung konnte nicht gespeichert werden.\n\n{0}",

    # ================================================================
    # show_qemu_command
    # ================================================================
    "Comando QEMU": "QEMU-Befehl",
    "Selecciona primero una maquina virtual.":
        "Wähle zuerst eine virtuelle Maschine aus.",
    "La VM '{0}' todavia no se ha arrancado.\n\nEl comando QEMU se genera al pulsar Iniciar; vuelve a intentarlo despues del primer arranque.":
        "Die VM '{0}' wurde noch nicht gestartet.\n\nDer QEMU-Befehl wird beim Drücken von Starten generiert; versuche es nach dem ersten Start erneut.",
    "No se pudo leer run_temp.sh.\n\n{0}":
        "run_temp.sh konnte nicht gelesen werden.\n\n{0}",
    "Comando QEMU - {0}": "QEMU-Befehl - {0}",
    "Contenido de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este es el comando exacto con el que QEMU esta ejecutando (o ejecuto por ultima vez) la VM.":
        "Inhalt von <code>run_temp.sh</code> für <b>{0}</b>.<br>Dies ist der exakte Befehl, mit dem QEMU die VM ausführt (oder zuletzt ausgeführt hat).",
    "Copiar al portapapeles": "In die Zwischenablage kopieren",
    "Abrir carpeta de la VM": "VM-Ordner öffnen",
    "Abre la carpeta que contiene run_temp.sh, launch.log y los discos.":
        "Öffnet den Ordner mit run_temp.sh, launch.log und den Festplatten.",

    # ================================================================
    # edit_vm_notes
    # ================================================================
    "Notas de la VM": "VM-Notizen",
    "Notas - {0}": "Notizen - {0}",
    "Notas libres sobre <b>{0}</b>. Se guardan en <code>vm_config.ini</code> como <code>extra.notes</code> y aparecen como aviso amarillo en la pestana Resumen.":
        "Freie Notizen zu <b>{0}</b>. Sie werden in <code>vm_config.ini</code> als <code>extra.notes</code> gespeichert und erscheinen als gelber Hinweis im Reiter Übersicht.",
    "Ej.: instalado con VirtIO, probar snapshots tras actualizar los drivers; puerto 8080 redirigido al 80 del guest...":
        "Z. B.: mit VirtIO installiert, Snapshots nach Treiber-Update testen; Port 8080 auf Gast-Port 80 weitergeleitet...",
    "Borrar notas": "Notizen löschen",
    "Notas": "Notizen",
    "No se pudieron guardar las notas.\n\n{0}":
        "Die Notizen konnten nicht gespeichert werden.\n\n{0}",

    # ================================================================
    # _set_vm_status
    # ================================================================
    "● Nueva VM": "● Neue VM",
    "● Configurada": "● Konfiguriert",
    "● Ejecutándose": "● Wird ausgeführt",
    "● Error": "● Fehler",

    # ================================================================
    # open_vm_folder / show_vm_summary
    # ================================================================
    "Carpeta": "Ordner",
    "Primero selecciona una máquina virtual existente.":
        "Wähle zuerst eine vorhandene virtuelle Maschine aus.",
    "Carpeta de la VM": "VM-Ordner",
    "No se pudo abrir la carpeta.\n\n{0}\n\n{1}":
        "Der Ordner konnte nicht geöffnet werden.\n\n{0}\n\n{1}",
    "Resumen": "Übersicht",
    "No hay una máquina virtual seleccionada todavía.":
        "Es ist noch keine virtuelle Maschine ausgewählt.",
    "Resumen de la máquina virtual": "Zusammenfassung der virtuellen Maschine",

    # ================================================================
    # import_vm + _import_vm_impl
    # ================================================================
    "Importar VM": "VM importieren",
    "¿Cómo quieres importar la máquina virtual?\n\n  • Desde carpeta: selecciona una carpeta que contenga vm_config.ini.\n  • Desde archivo: selecciona un .ova o .ovf (formato estándar OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip exportado previamente desde otra instalación de Virtual.Machine.":
        "Wie möchtest du die virtuelle Maschine importieren?\n\n  • Aus Ordner: Wähle einen Ordner, der vm_config.ini enthält.\n  • Aus Datei: Wähle ein .ova oder .ovf (OVF-Standardformat, portabel zu VirtualBox/VMware) oder eine zuvor aus einer anderen Virtual.Machine-Installation exportierte .tar.gz- / .tar- / .zip-Datei.",
    "📁 Desde carpeta…": "📁 Aus Ordner…",
    "🗜️ Desde archivo…": "🗜️ Aus Datei…",
    "Selecciona la carpeta de la VM a importar":
        "Wähle den VM-Ordner zum Importieren",
    "Selecciona el archivo a importar":
        "Wähle die zu importierende Datei",
    "OVF/OVA (*.ova *.ovf);;Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;Todos los archivos (*)":
        "OVF/OVA (*.ova *.ovf);;Gepackte VM-Dateien (*.tar.gz *.tgz *.tar *.zip);;Alle Dateien (*)",
    "Formato de archivo no reconocido. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.":
        "Dateiformat nicht erkannt. Verwende .tar.gz, .tgz, .tar, .zip, .ova oder .ovf.",
    "La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\nAsegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.":
        "Der ausgewählte Ordner enthält keine vm_config.ini:\n\n{0}\n\nStelle sicher, dass du den Stammordner der VM wählst, nicht einen Unterordner.",
    "Nombre para la VM importada:\n\n(se importará desde {0})":
        "Name für die importierte VM:\n\n(wird aus {0} importiert)",
    "Nombre inválido.": "Ungültiger Name.",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Eine VM mit dem Namen '{0}' existiert bereits.\n\nErsetzen? (die vorhandene wird gelöscht)",
    "Copiando/desempaquetando en el sistema de archivos del destino (no en /tmp)…":
        "Kopiere/entpacke im Dateisystem des Ziels (nicht in /tmp)…",
    "Desempaquetando archivo…": "Entpacke Datei…",
    "Extrayendo {0}/{1}…": "Extrahiere {0}/{1}…",
    "El archivo no contiene ninguna VM válida (no se encontró vm_config.ini).":
        "Die Datei enthält keine gültige VM (vm_config.ini wurde nicht gefunden).",
    "Importación completada.": "Import abgeschlossen.",
    "Copiando {0}": "Kopiere {0}",
    "VM '{0}' importada correctamente.\n\nRevisa su configuración en la pestaña Configuración antes de arrancarla, especialmente si la importaste desde otro host: puede referenciar rutas que no existan aquí (carpetas compartidas, ISOs externas, dispositivos de passthrough).":
        "VM '{0}' erfolgreich importiert.\n\nÜberprüfe die Konfiguration im Reiter Konfiguration, bevor du sie startest, insbesondere wenn du sie von einem anderen Host importiert hast: sie kann Pfade referenzieren, die hier nicht existieren (gemeinsame Ordner, externe ISOs, Passthrough-Geräte).",

    # ================================================================
    # export_vm + _export_vm_impl
    # ================================================================
    "Exportar VM": "VM exportieren",
    "Primero selecciona una máquina virtual.":
        "Wähle zuerst eine virtuelle Maschine aus.",
    "La VM '{0}' está {1}.\n\nSe recomienda apagarla antes de exportar: si está corriendo, los discos pueden estar en un estado inconsistente (cambios sin sincronizar a disco, locks activos…).\n\n¿Continuar de todos modos?":
        "Die VM '{0}' ist {1}.\n\nEs wird empfohlen, sie vor dem Export herunterzufahren: Wenn sie läuft, können sich die Festplatten in einem inkonsistenten Zustand befinden (nicht synchronisierte Änderungen, aktive Sperren…).\n\nTrotzdem fortfahren?",
    "Copia de carpeta (más rápido, editable)":
        "Ordnerkopie (schneller, bearbeitbar)",
    "Archivo .tar.gz (comprimido, portable)":
        ".tar.gz-Datei (komprimiert, portabel)",
    "Archivo .zip (compatible con Windows)":
        ".zip-Datei (Windows-kompatibel)",
    "Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)":
        ".ova-Datei (Open Virtual Appliance, portabel zu VirtualBox/VMware)",
    "Descriptor .ovf + discos sueltos (carpeta)":
        ".ovf-Deskriptor + lose Festplatten (Ordner)",
    "Formato para exportar '{0}':": "Format zum Exportieren von '{0}':",
    "Elige la carpeta donde crear la copia":
        "Wähle den Ordner, in dem die Kopie erstellt werden soll",
    "En la carpeta destino ya existe '{0}'.\n\n¿Sobrescribir? (se borrará la carpeta destino existente)":
        "Im Zielordner existiert bereits '{0}'.\n\nÜberschreiben? (der vorhandene Zielordner wird gelöscht)",
    "Guardar archivo de exportación": "Exportdatei speichern",
    "Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)":
        "tar.gz-Datei (*.tar.gz);;zip-Datei (*.zip)",
    "Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)":
        "zip-Datei (*.zip);;tar.gz-Datei (*.tar.gz)",
    "El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?":
        "Die Zieldatei existiert bereits:\n{0}\n\nÜberschreiben?",
    "Confirmar exportación": "Export bestätigen",
    "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Contenido: {2} archivo(s), {3}\n  • Destino: {4}\n\nLos archivos de bloqueo (pids, sockets) y logs se omitirán.":
        "'{0}' exportieren als:\n\n  • Format: {1}\n  • Inhalt: {2} Datei(en), {3}\n  • Ziel: {4}\n\nSperrdateien (PIDs, Sockets) und Logs werden übersprungen.",
    "No se pudo completar la exportación.\n\n{0}":
        "Der Export konnte nicht abgeschlossen werden.\n\n{0}",
    "{0} archivo(s), {1} en total": "{0} Datei(en), {1} gesamt",
    "Exportación cancelada por el usuario.":
        "Export vom Benutzer abgebrochen.",
    "Formato de exportación desconocido: {0}":
        "Unbekanntes Exportformat: {0}",
    "Exportación completada ({0} archivo(s)).":
        "Export abgeschlossen ({0} Datei(en)).",
    "'{0}' exportada correctamente.\n\nDestino: {1}":
        "'{0}' erfolgreich exportiert.\n\nZiel: {1}",

    # ================================================================
    # clone_current_vm + full + prompts + checks
    # ================================================================
    "Clonar máquina virtual": "Virtuelle Maschine klonen",
    "Nombre para el clon de '{0}':": "Name für den Klon von '{0}':",
    "Debes escribir un nombre para el clon.":
        "Du musst einen Namen für den Klon eingeben.",
    "Nombre ya existente": "Name existiert bereits",
    "La máquina virtual '{0}' ya existe en el listado.\n\nElige otro nombre para el clon.":
        "Die virtuelle Maschine '{0}' existiert bereits in der Liste.\n\nWähle einen anderen Namen für den Klon.",
    "Ese nombre no puede utilizarse para una máquina virtual.":
        "Dieser Name kann nicht für eine virtuelle Maschine verwendet werden.",
    "Clonar VM": "VM klonen",
    "¿Qué tipo de clon quieres crear a partir de <b>{0}</b>?<br><br><b>Clon completo</b><br>Copia íntegra de todos los discos. Totalmente independiente del original; ocupa el mismo espacio que la VM original.<br><br><b>Clon enlazado</b><br>El disco base se comparte mediante un <i>backing file</i> QCOW2. La nueva VM solo guarda los cambios, así que ocupa muy poco. <b>Depende del original</b>: si se borra o se mueve el original, el clon se rompe.<br>El backing se guarda con <b>ruta relativa</b> para que puedas mover o copiar la carpeta <code>VirtualMachines/</code> entera a otro host sin romper nada.<br><br><b>Importante:</b> una vez que el clon arranque por primera vez, los cambios que hagas DESPUÉS en el original <b>NO se verán</b> en el clon: la vista de su sistema de archivos queda anclada al estado del primer arranque (los bloques que el clon ya escribió no vuelven a consultarse en el backing). Trata el original como de solo lectura mientras el clon exista, o desenlaza el clon con <b>🧬 Desenlazar</b> para independizarlo.":
        "Welche Art von Klon möchtest du aus <b>{0}</b> erstellen?<br><br><b>Vollständiger Klon</b><br>Vollständige Kopie aller Festplatten. Völlig unabhängig vom Original; belegt denselben Speicher wie die Original-VM.<br><br><b>Verknüpfter Klon</b><br>Die Basisfestplatte wird über eine QCOW2-<i>Backing-Datei</i> geteilt. Die neue VM speichert nur Änderungen und belegt daher sehr wenig. <b>Hängt vom Original ab</b>: Wird das Original gelöscht oder verschoben, bricht der Klon.<br>Das Backing wird mit <b>relativem Pfad</b> gespeichert, damit du den gesamten <code>VirtualMachines/</code>-Ordner auf einen anderen Host verschieben oder kopieren kannst, ohne etwas zu beschädigen.<br><br><b>Wichtig:</b> Sobald der Klon zum ersten Mal startet, werden Änderungen, die du SPÄTER am Original vornimmst, <b>NICHT im Klon sichtbar</b> sein: Die Sicht auf sein Dateisystem ist an den Zustand beim ersten Start gebunden (Blöcke, die der Klon bereits geschrieben hat, werden nie wieder im Backing nachgeschlagen). Behandle das Original als schreibgeschützt, solange der Klon existiert, oder löse den Klon mit <b>🧬 Entkoppeln</b>, um ihn eigenständig zu machen.",
    "Clon completo": "Vollständiger Klon",
    "Clon enlazado": "Verknüpfter Klon",
    "No se pudo copiar la carpeta de la VM.\n\n{0}":
        "Der VM-Ordner konnte nicht kopiert werden.\n\n{0}",
    "La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}":
        "Die VM wurde kopiert, aber ihre vm_config.ini konnte nicht neu geschrieben werden.\n\n{0}",
    "Clon creado": "Klon erstellt",
    "La máquina virtual '{0}' fue clonada correctamente (clon completo).\n\nSe han regenerado las direcciones MAC y los IDs internos de los discos para que no choquen con la VM original.":
        "Die virtuelle Maschine '{0}' wurde erfolgreich geklont (vollständiger Klon).\n\nDie MAC-Adressen und internen IDs der Festplatten wurden neu generiert, um Konflikte mit der Original-VM zu vermeiden.",
    "Clon enlazado con original en ejecución":
        "Verknüpfter Klon mit laufendem Original",
    "El original de este clon ('{0}') está corriendo.\n\nArrancar original y clon a la vez puede dar resultados impredecibles:\n\n  • El clon lee del disco del original los bloques que no ha modificado. Si el original escribe algo mientras el clon corre, el clon puede leer estados intermedios.\n  • La vista del sistema de archivos del clon ya está anclada al estado de su primer arranque para los bloques de metadatos, así que los cambios nuevos del original probablemente no se vean, pero el riesgo de lectura inconsistente sigue ahí.\n\nRecomendaciones:\n  • Apaga el original antes de arrancar el clon (o al revés).\n  • O desenlaza el clon con '🧬 Desenlazar' para que sea totalmente independiente.\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "Das Original dieses Klons ('{0}') läuft.\n\nOriginal und Klon gleichzeitig laufen zu lassen, kann unvorhersehbare Ergebnisse liefern:\n\n  • Der Klon liest die Blöcke, die er nicht geändert hat, von der Original-Festplatte. Schreibt das Original etwas, während der Klon läuft, kann der Klon Zwischenzustände lesen.\n  • Die Dateisystem-Sicht des Klons ist für Metadatenblöcke bereits an den Zustand seines ersten Starts gebunden, sodass neue Änderungen des Originals wahrscheinlich nicht sichtbar sind – das Risiko inkonsistenter Lesevorgänge bleibt jedoch bestehen.\n\nEmpfehlungen:\n  • Fahre das Original herunter, bevor du den Klon startest (oder umgekehrt).\n  • Oder löse den Klon mit '🧬 Entkoppeln', damit er vollständig eigenständig ist.\n\nDieser Hinweis erscheint für diese VM in dieser Sitzung nicht erneut.",
    "Clon enlazado con backing roto":
        "Verknüpfter Klon mit defektem Backing",
    "Este clon enlazado espera el backing en:\n\n    {0}\n\nResuelto contra su carpeta queda en:\n\n    {1}\n\nEse archivo no existe. La VM original ('{2}') probablemente se movió o se borró.\n\nQEMU fallará al arrancar con:\n    Could not open backing file: No such file or directory\n\nOpciones:\n  • Mueve también la VM original de vuelta a su carpeta, o\n  • Copia la carpeta 'VirtualMachines/' entera (con original\n    y clon juntos) a la nueva ubicación, o\n  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n    para independizar este clon (puede fallar si el backing\n    ya no está disponible).\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "Dieser verknüpfte Klon erwartet das Backing unter:\n\n    {0}\n\nAufgelöst relativ zu seinem Ordner ist es:\n\n    {1}\n\nDiese Datei existiert nicht. Die Original-VM ('{2}') wurde vermutlich verschoben oder gelöscht.\n\nQEMU wird beim Start fehlschlagen mit:\n    Could not open backing file: No such file or directory\n\nOptionen:\n  • Verschiebe auch die Original-VM zurück in ihren Ordner, oder\n  • Kopiere den gesamten 'VirtualMachines/'-Ordner (mit Original\n    und Klon zusammen) an den neuen Speicherort, oder\n  • Wenn noch möglich, verwende '🧬 Entkoppeln' im Reiter Übersicht,\n    um diesen Klon eigenständig zu machen (kann fehlschlagen,\n    wenn das Backing nicht mehr verfügbar ist).\n\nDieser Hinweis erscheint für diese VM in dieser Sitzung nicht erneut.",

    # ================================================================
    # clone linked + unlink
    # ================================================================
    "No se pudo determinar el disco principal de la VM original.\n\nEl clon enlazado necesita un disco base QCOW2 sobre el que\ncrear el backing file. Si la VM no tiene discos, usa\n'Clon completo'.":
        "Die Hauptfestplatte der Original-VM konnte nicht ermittelt werden.\n\nDer verknüpfte Klon benötigt eine QCOW2-Basisfestplatte, auf der\ndas Backing-File erstellt wird. Wenn die VM keine Festplatten hat,\nverwende 'Vollständiger Klon'.",
    "No se pudo inspeccionar el disco original.\n\n{0}":
        "Die Original-Festplatte konnte nicht untersucht werden.\n\n{0}",
    "El disco principal de la VM original está en formato {0}.\n\nEl clon enlazado solo funciona con QCOW2 (necesita backing\nfile). Usa 'Clon completo' si quieres copiar el disco tal cual.":
        "Die Hauptfestplatte der Original-VM hat das Format {0}.\n\nDer verknüpfte Klon funktioniert nur mit QCOW2 (er benötigt ein\nBacking-File). Verwende 'Vollständiger Klon', wenn du die Festplatte\nunverändert kopieren möchtest.",
    "No se pudo crear la carpeta del clon.\n\n{0}":
        "Der Klon-Ordner konnte nicht erstellt werden.\n\n{0}",
    "qemu-img create falló.\n\n{0}": "qemu-img create schlug fehl.\n\n{0}",
    "No se pudo crear el delta QCOW2.\n\n{0}":
        "Das QCOW2-Delta konnte nicht erstellt werden.\n\n{0}",
    "El backing file quedó guardado como ruta ABSOLUTA, lo que haría el clon no portable.\n\nSe ha abortado la operación para no dejar un clon defectuoso. Reporta esto como bug.":
        "Das Backing-File wurde als ABSOLUTER Pfad gespeichert, was den Klon nicht portabel machen würde.\n\nDer Vorgang wurde abgebrochen, um keinen fehlerhaften Klon zu hinterlassen. Melde dies als Bug.",
    "No se pudieron copiar los archivos auxiliares.\n\n{0}":
        "Die Hilfsdateien konnten nicht kopiert werden.\n\n{0}",
    "El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n{0}\n\nRevisa manualmente el archivo antes de usar la VM.":
        "Der Klon wurde erstellt, aber seine vm_config.ini konnte nicht neu geschrieben werden.\n\n{0}\n\nÜberprüfe die Datei manuell, bevor du die VM verwendest.",
    "La máquina virtual '{0}' fue clonada correctamente (clon enlazado).\n\nEl disco base se comparte con el original mediante un backing\nfile QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\npero DEPENDE del original:\n\n  • Si borras o mueves la VM original, el clon se rompe.\n  • Una vez que el clon arranque por primera vez, los cambios\n    que hagas DESPUÉS en el original NO se verán en el clon:\n    la vista del sistema de archivos queda anclada al estado\n    del primer arranque. Trata el original como de solo lectura\n    mientras el clon exista.\n  • Los snapshots completos (RAM) no funcionarán en este clon\n    — solo de disco. QEMU no puede restaurar (loadvm) un\n    snapshot completo sobre un QCOW2 con backing file.\n  • Los snapshots del clon no son reproducibles mientras el\n    original pueda cambiar: al restaurar, se mezcla el delta\n    guardado con el estado ACTUAL del backing.\n  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n    apagado.\n\nPara mover o copiar la estructura completa a otro host,\nllévate la carpeta 'VirtualMachines/' entera.":
        "Die virtuelle Maschine '{0}' wurde erfolgreich geklont (verknüpfter Klon).\n\nDie Basisfestplatte wird über eine QCOW2-Backing-Datei mit relativem\nPfad mit dem Original geteilt. Der Klon belegt sehr wenig Speicher,\nHÄNGT aber vom Original ab:\n\n  • Wenn du die Original-VM löschst oder verschiebst, bricht der Klon.\n  • Sobald der Klon zum ersten Mal startet, werden Änderungen,\n    die du SPÄTER am Original vornimmst, NICHT im Klon sichtbar:\n    Die Dateisystem-Sicht ist an den Zustand des ersten Starts\n    gebunden. Behandle das Original als schreibgeschützt,\n    solange der Klon existiert.\n  • Vollständige Snapshots (RAM) funktionieren in diesem Klon nicht\n    — nur Disk. QEMU kann einen vollständigen Snapshot auf einem\n    QCOW2 mit Backing-Datei nicht wiederherstellen (loadvm).\n  • Die Snapshots des Klons sind nicht reproduzierbar, solange\n    das Original sich ändern kann: Beim Wiederherstellen wird das\n    gespeicherte Delta mit dem AKTUELLEN Zustand des Backings gemischt.\n  • Wenn du ihn eigenständig machen möchtest, verwende '🧬 Entkoppeln',\n    wenn er ausgeschaltet ist.\n\nUm die gesamte Struktur auf einen anderen Host zu verschieben oder zu kopieren,\nimm den gesamten 'VirtualMachines/'-Ordner mit.",
    "Desenlazar clon": "Klon entkoppeln",
    "Esta VM no es un clon enlazado, no hay nada que desenlazar.":
        "Diese VM ist kein verknüpfter Klon; es gibt nichts zu entkoppeln.",
    "La VM '{0}' está encendida.\n\nApágala antes de desenlazarla: con QEMU activo el archivo\nestá bloqueado y el convert no puede reemplazarlo.":
        "Die VM '{0}' läuft.\n\nFahre sie herunter, bevor du sie entkoppelst: Bei laufendem QEMU ist die Datei\ngesperrt und der Convert-Vorgang kann sie nicht ersetzen.",
    "No se encontró el disco principal del clon.":
        "Die Hauptfestplatte des Klons wurde nicht gefunden.",
    "Se convertirá el disco principal del clon <b>{0}</b> en un QCOW2 <b>autónomo</b>.<br><br>Después de esto, el clon deja de depender del original y puede moverse o copiarse por separado.<br><br><b>Requiere:</b><br>&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>&nbsp;&nbsp;• La VM apagada (ya lo está).<br>&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>El resultado se verifica como QCOW2 válido y se reemplaza atómicamente. Si algo falla a mitad, el archivo original del clon queda intacto.":
        "Die Hauptfestplatte des Klons <b>{0}</b> wird in ein <b>eigenständiges</b> QCOW2 konvertiert.<br><br>Danach hängt der Klon nicht mehr vom Original ab und kann eigenständig verschoben oder kopiert werden.<br><br><b>Erfordert:</b><br>&nbsp;&nbsp;• Freien Speicher auf dem Host (~1,1× der Festplattengröße).<br>&nbsp;&nbsp;• Die ausgeschaltete VM (ist bereits der Fall).<br>&nbsp;&nbsp;• Die Anwendung während des Vorgangs nicht schließen.<br><br>Das Ergebnis wird als gültiges QCOW2 überprüft und atomar ersetzt. Wenn etwas mittendrin fehlschlägt, bleibt die Originaldatei des Klons unversehrt.",
    "Desenlazado cancelado por el usuario.":
        "Entkoppeln vom Benutzer abgebrochen.",
    "Desenlazado": "Entkoppelt",
    "El clon '{0}' ya es autónomo.\n\nTamaño antes: {1}\nTamaño después: {2}\n\nPuedes mover la VM sin llevarte la original.":
        "Der Klon '{0}' ist nun eigenständig.\n\nGröße vorher: {1}\nGröße nachher: {2}\n\nDu kannst die VM verschieben, ohne das Original mitzunehmen.",
    "No se pudo desenlazar el clon.\n\n{0}":
        "Der Klon konnte nicht entkoppelt werden.\n\n{0}",
    "Convirtiendo el clon en un QCOW2 autónomo…":
        "Klon wird in ein eigenständiges QCOW2 konvertiert…",

    # ================================================================
    # delete_current_vm + OVF raises/messages
    # ================================================================
    "Eliminar VM": "VM löschen",
    "Primero selecciona una máquina virtual existente.":
        "Wähle zuerst eine vorhandene virtuelle Maschine aus.",
    "Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n":
        "Nur der Ordner der virtuellen Maschine wird gelöscht:\n\n{0}\n\n",
    "Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n":
        "Die folgenden Medien befinden sich außerhalb des VM-Ordners und werden NICHT gelöscht:\n",
    "⚠ ESTA VM ES EL ORIGINAL DE {0} CLON(ES) ENLAZADO(S):\n":
        "⚠ DIESE VM IST DAS ORIGINAL VON {0} VERKNÜPFTEN KLON(S):\n",
    "\n\nSi continúas, esos clones quedarán inutilizables (su backing file ya no existirá).\n\nSe recomienda desenlazarlos primero: selecciona cada clon y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n":
        "\n\nWenn du fortfährst, werden diese Klone unbrauchbar (ihre Backing-Datei existiert dann nicht mehr).\n\nEs wird empfohlen, sie zuerst zu entkoppeln: Wähle jeden Klon und drücke '🧬 Entkoppeln' in seinem Reiter Übersicht.\n\n",
    "¿Deseas continuar?": "Fortfahren?",
    "Eliminar máquina virtual": "Virtuelle Maschine löschen",
    "No se pudo eliminar '{0}'.\n\n{1}":
        "'{0}' konnte nicht gelöscht werden.\n\n{1}",
    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la carpeta de la VM ({0}). Sin este archivo la VM no tiene sistema operativo que exportar.":
        "macOS-VM: mac_hdd_ng.qcow2 wurde im VM-Ordner ({0}) nicht gefunden. Ohne diese Datei hat die VM kein Betriebssystem zum Exportieren.",
    "La VM no tiene discos adjuntos que exportar. Añade al menos un disco en Configuración → Almacenamiento.":
        "Die VM hat keine angehängten Festplatten zum Exportieren. Füge mindestens eine Festplatte in Konfiguration → Speicher hinzu.",
    "qemu-img convert -c falló para '{0}': {1}":
        "qemu-img convert -c ist für '{0}' fehlgeschlagen: {1}",
    "El aplanado+compresión de '{0}' no produjo un archivo válido.":
        "Das Vereinfachen + Komprimieren von '{0}' ergab keine gültige Datei.",
    "Importar OVA": "OVA importieren",
    "El archivo .ova no contiene ningún descriptor .ovf.":
        "Die .ova-Datei enthält keinen .ovf-Deskriptor.",
    "Importar OVF": "OVF importieren",
    "El archivo .ovf está vacío.": "Die .ovf-Datei ist leer.",
    "No se pudo leer el descriptor.\n\n{0}":
        "Der Deskriptor konnte nicht gelesen werden.\n\n{0}",
    "El descriptor OVF no se pudo interpretar.\n\n{0}":
        "Der OVF-Deskriptor konnte nicht interpretiert werden.\n\n{0}",
    "No se pudo completar la importación.\n\n{0}":
        "Der Import konnte nicht abgeschlossen werden.\n\n{0}",
    "Extrayendo y preparando el OVF/OVA...":
        "OVF/OVA wird extrahiert und vorbereitet...",
}
