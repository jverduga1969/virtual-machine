# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2f-1: Snapshots manuales.

Cubre: dialogos de crear / restaurar / eliminar / renombrar snapshots,
avisos VirtIO-GPU (crear + restaurar), aviso de clon enlazado,
snapshots solo-disco, apagado incompleto para restauracion en frio,
organigrama y mensajes auxiliares.

Los snapshots programados y los backups van en vm_de_tanda2f2.py.
"""

TRANSLATIONS = {

    # ================================================================
    # Panel de Snapshots (encabezado)
    # ================================================================
    "<b>Snapshots de la máquina virtual</b>":
        "<b>Snapshots der virtuellen Maschine</b>",
    "Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.":
        "Erstellt, stellt wieder her, löscht und verwaltet Snapshots. Die Anwendung prüft die beschreibbaren QCOW2-Festplatten, den freien Speicher und welche Festplatten Teil des Snapshots werden, bevor sie ihn ausführt.",
    "⚠ Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con '🧬 Desenlazar' en la pestaña Resumen.":
        "⚠ Diese VM ist ein verknüpfter Klon (QCOW2-Backing-Datei). Vollständige Snapshots (RAM + Geräte) können in QEMU mit Backing-Datei nicht wiederhergestellt werden; die App verwendet stets NUR-DISK-Snapshots. Für vollständige Snapshots zuerst den Klon mit '🧬 Entkoppeln' im Reiter Übersicht lösen.",
    "🔄 Actualizar": "🔄 Aktualisieren",
    "➕ Crear": "➕ Erstellen",
    "↩ Restaurar": "↩ Wiederherstellen",
    "✏ Cambiar nombre": "✏ Umbenennen",
    "Formato": "Format",
    "Tamaño virtual": "Virtuelle Größe",
    "Tamaño archivo": "Dateigröße",
    "Libre host": "Host frei",
    "Escritura": "Schreibbar",
    "Snapshot": "Snapshot",
    "Sin operación de snapshot": "Kein Snapshot-Vorgang",
    "ID": "ID",
    "Tamaño VM": "VM-Größe",
    "Fecha": "Datum",
    "Reloj VM": "VM-Uhr",
    "Vista:": "Ansicht:",
    "📋 Lista": "📋 Liste",
    "🌳 Organigrama": "🌳 Baum",
    "Zoom:": "Zoom:",
    "Alejar la miniatura": "Miniatur verkleinern",
    "Acercar la miniatura": "Miniatur vergrößern",
    "Ajustar al tamaño original": "An Originalgröße anpassen",
    "Sin captura de pantalla": "Kein Screenshot",
    "(solo disco)": "(nur Disk)",
    "Desconocido": "Unbekannt",
    "💽 SATA": "💽 SATA",
    "⚡ NVMe": "⚡ NVMe",
    "❌ No hay un QCOW2 escribible disponible para snapshots completos de VM.":
        "❌ Es ist kein beschreibbares QCOW2 für vollständige VM-Snapshots verfügbar.",
    "✅ Disco para estado de VM: {0} · tamaño virtual: {1} · archivo actual: {2} · espacio libre del sistema de archivos: {3} · reserva orientativa inicial: {4}. El snapshot QCOW2 crece según se modifican bloques.":
        "✅ Disk für VM-Zustand: {0} · virtuelle Größe: {1} · aktuelle Datei: {2} · freier Speicher im Dateisystem: {3} · anfängliche Schätzreserve: {4}. Der QCOW2-Snapshot wächst mit den geänderten Blöcken.",
    "⚠ {0} El snapshot podría fallar al quedarse sin espacio.":
        "⚠ {0} Der Snapshot könnte fehlschlagen, wenn der Speicher ausgeht.",

    # ================================================================
    # Aviso de apagado incompleto (restauracion en frio)
    # ================================================================
    "Apagado no completado": "Herunterfahren nicht abgeschlossen",
    "La VM no se apagó dentro del tiempo máximo (90 s).\n\n"
    "Puede que el sistema invitado esté colgado. Usa el botón\n"
    "'Forzar apagado' de la lista lateral, luego vuelve a intentar\n"
    "restaurar el snapshot con la VM ya apagada.":
        "Die VM hat nicht innerhalb der maximalen Zeit (90 s) heruntergefahren.\n\n"
        "Möglicherweise ist das Gastsystem hängen geblieben. Verwende den\n"
        "Button 'Ausschalten erzwingen' in der Seitenliste und versuche dann\n"
        "erneut, den Snapshot bei ausgeschalteter VM wiederherzustellen.",

    # ================================================================
    # Aviso clon enlazado al restaurar snapshot completo antiguo
    # ================================================================
    "No se puede restaurar este snapshot": "Dieser Snapshot kann nicht wiederhergestellt werden",
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
    "'🧬 Desenlazar' (convierte el delta en un QCOW2 autónomo).":
        "Die VM ist ein verknüpfter Klon (QCOW2-Backing-Datei) und der "
        "Snapshot '{0}' wurde im VOLLSTÄNDIGEN Modus (RAM + Geräte) erstellt.\n\n"
        "QEMU kann vollständige Snapshots auf einem QCOW2 mit Backing-Datei "
        "nicht wiederherstellen: beim Ausführen von loadvm wird mit einer "
        "internen Zusicherung (vmstate_load_next) abgebrochen und der Prozess "
        "stirbt. Daher die 'Verbindung zurückgesetzt', die du gesehen hast.\n\n"
        "Was zu tun ist:\n"
        "  • Die Snapshots, die du AB JETZT in diesem Klon erstellst, sind\n"
        "    NUR-DISK (die App erzwingt dies bereits) und können wiederhergestellt werden.\n"
        "  • Dieser alte Snapshot kann nicht wiederhergestellt werden. Lösche ihn,\n"
        "    wenn er nicht mehr gebraucht wird.\n"
        "  • Wenn du vollständige Snapshots benötigst, löse den Klon mit\n"
        "    '🧬 Entkoppeln' (wandelt das Delta in ein eigenständiges QCOW2 um).",

    # ================================================================
    # Organigrama: menus contextuales y dialogos
    # ================================================================
    "No hay otros snapshots para elegir como padre.":
        "Es gibt keine anderen Snapshots zur Auswahl als übergeordneten.",
    "Establecer padre": "Übergeordneten festlegen",
    "Padre para '{0}':": "Übergeordneter für '{0}':",
    "(ninguno — mover a la raíz)": "(keiner — zur Wurzel verschieben)",
    "Nuevo snapshot hijo": "Neuer untergeordneter Snapshot",
    "Nombre del snapshot (hijo de '{0}'):":
        "Name des Snapshots (Kind von '{0}'):",
    "No se pudo crear el snapshot.\n\n{0}":
        "Der Snapshot konnte nicht erstellt werden.\n\n{0}",
    "Sin capturas de snapshot": "Keine Snapshot-Screenshots",
    "Los snapshots creados con la VM en ejecución guardan una "
    "captura de pantalla que se muestra aquí.":
        "Snapshots, die bei laufender VM erstellt werden, speichern einen "
        "Screenshot, der hier angezeigt wird.",
    "Captura no legible": "Screenshot nicht lesbar",
    "Restaurar snapshot": "Snapshot wiederherstellen",
    "No hay ningún snapshot reciente para restaurar.":
        "Es gibt keinen aktuellen Snapshot zum Wiederherstellen.",
    "Existe una captura para '{0}', pero ese snapshot ya no "
    "aparece en la lista de la VM (puede haber sido eliminado). "
    "Actualiza la pestaña Snapshots o elimínalo manualmente.":
        "Für '{0}' existiert ein Screenshot, aber dieser Snapshot erscheint "
        "nicht mehr in der VM-Liste (möglicherweise wurde er gelöscht). "
        "Aktualisiere den Reiter Snapshots oder lösche ihn manuell.",

    # ================================================================
    # Aviso VirtIO-GPU al crear snapshot
    # ================================================================
    "Snapshot con VirtIO-GPU": "Snapshot mit VirtIO-GPU",
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
        "Diese VM ist mit Grafik '{0}' konfiguriert, die das WIEDERHERSTELLEN "
        "vollständiger Snapshots in QEMU (RAM + Geräte) nicht erlaubt.\n"
        "\n"
        "Der Snapshot kann erstellt werden, aber beim Versuch, ihn "
        "wiederherzustellen, schlägt QEMU fehl mit: 'Failed to load element of type virtio for virtio'.\n"
        "\n"
        "Optionen:\n"
        "  • NUR-DISK-Snapshot verwenden ('Nein' im folgenden Dialog wählen).\n"
        "    Speichert weder RAM noch Fensterzustand, kann aber bei ausgeschalteter\n"
        "    VM problemlos wiederhergestellt werden.\n"
        "  • Grafik/GPU auf 'Red Hat QXL 2D' oder 'VMware SVGA II' umstellen,\n"
        "    die VM neu starten und vollständige Snapshots erstellen.\n"
        "\n"
        "Snapshot trotzdem erstellen?",

    # ================================================================
    # Aviso VirtIO-GPU al restaurar snapshot
    # ================================================================
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
        "QEMU kann den Snapshot aufgrund eines bekannten Problems "
        "mit dem VirtIO-GPU-Gerät nicht wiederherstellen.\n\n"
        "Technisches Detail:\n"
        "  VirtIO-GPU speichert einen internen Zustand, der nicht zuverlässig\n"
        "  serialisiert werden kann. QEMU versucht ihn bei der Wiederherstellung\n"
        "  neu aufzubauen und schlägt fehl. Es ist kein Bug der App, sondern\n"
        "  eine Einschränkung der Engine.\n\n"
        "Lösung:\n"
        "  1. Öffne Konfiguration → Anzeige.\n"
        "  2. Ändere 'Grafik / GPU' von '{0}' auf 'Red Hat QXL 2D'.\n"
        "  3. Starte die VM neu (ausschalten und wieder einschalten).\n"
        "  4. Erstelle ab dann neue Snapshots: sie können problemlos\n"
        "     wiederhergestellt werden.\n\n"
        "Alte mit virtio-gpu erstellte Snapshots können nicht wiederhergestellt\n"
        "werden (QEMU kann ihren Zustand nicht rekonstruieren). Wenn sie\n"
        "nicht mehr gebraucht werden, lösche sie.",

    # ================================================================
    # Dialogos: crear / restaurar / eliminar / renombrar
    # ================================================================
    "Selecciona una máquina virtual.": "Wähle eine virtuelle Maschine aus.",
    "No se puede crear un snapshot completo.\n\n":
        "Ein vollständiger Snapshot kann nicht erstellt werden.\n\n",
    "Espacio disponible": "Verfügbarer Speicher",
    "{0}\n\n"
    "QEMU puede necesitar espacio adicional a medida que "
    "cambien los bloques. ¿Quieres continuar de todos modos?":
        "{0}\n\n"
        "QEMU kann zusätzlichen Speicher benötigen, wenn sich Blöcke ändern. "
        "Trotzdem fortfahren?",
    "Crear snapshot": "Snapshot erstellen",
    "Nombre del snapshot:": "Name des Snapshots:",
    "Clon enlazado: snapshot solo de discos":
        "Verknüpfter Klon: Nur-Disk-Snapshot",
    "Esta VM es un clon enlazado (backing file QCOW2).\n\n"
    "QEMU no puede crear/restaurar snapshots completos\n"
    "(RAM + dispositivos) sobre un QCOW2 con backing\n"
    "file: al hacer loadvm QEMU aborta con una aserción\n"
    "interna (vmstate_load_next).\n\n"
    "Por seguridad se creará un snapshot SOLO DE DISCOS,\n"
    "que sí se puede restaurar con la VM apagada.\n\n"
    "Si necesitas un snapshot completo, desenlaza\n"
    "primero el clon (🧬 Desenlazar).":
        "Diese VM ist ein verknüpfter Klon (QCOW2-Backing-Datei).\n\n"
        "QEMU kann vollständige Snapshots (RAM + Geräte)\n"
        "auf einem QCOW2 mit Backing-Datei weder erstellen noch\n"
        "wiederherstellen: beim loadvm bricht QEMU mit einer internen\n"
        "Zusicherung ab (vmstate_load_next).\n\n"
        "Aus Sicherheitsgründen wird ein NUR-DISK-Snapshot erstellt,\n"
        "der bei ausgeschalteter VM wiederhergestellt werden kann.\n\n"
        "Wenn du einen vollständigen Snapshot benötigst, löse zuerst den\n"
        "Klon mit '🧬 Entkoppeln'.",
    "Snapshot con la VM encendida": "Snapshot bei laufender VM",
    "La VM está encendida.\n\n"
    "Un snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y "
    "puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos "
    "observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\n"
    "Sí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
    "No = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\n"
    "Cancelar = no hacer nada.":
        "Die VM läuft.\n\n"
        "Ein VOLLSTÄNDIGER Snapshot muss RAM und Zustand aller Geräte speichern "
        "und kann QEMU während dieses Vorgangs vollständig beschäftigen. Bei dieser "
        "VM haben wir bereits beobachtet, dass QEMU lange im STOP-Zustand bleiben kann.\n\n"
        "Ja = VOLLSTÄNDIGEN SNAPSHOT erstellen (VM + RAM + Geräte + Festplatten).\n"
        "Nein = NUR-DISK-SNAPSHOT erstellen (schnell; speichert weder RAM noch Fenster).\n"
        "Abbrechen = nichts tun.",
    "Snapshot de discos creado": "Disk-Snapshot erstellt",
    "Se creó '{0}' en {1} QCOW2.\n\n"
    "Este snapshot no contiene la memoria RAM ni el estado de las ventanas. "
    "Para restaurarlo, la VM debe estar apagada.":
        "'{0}' wurde auf {1} QCOW2 erstellt.\n\n"
        "Dieser Snapshot enthält weder RAM noch Fensterzustand. "
        "Zum Wiederherstellen muss die VM ausgeschaltet sein.",
    "Error al crear snapshot de discos": "Fehler beim Erstellen des Disk-Snapshots",
    "Error al crear snapshot": "Fehler beim Erstellen des Snapshots",
    "No se pudo crear el snapshot completo.\n\n{0}":
        "Der vollständige Snapshot konnte nicht erstellt werden.\n\n{0}",
    "Ya hay una operación de snapshot en curso.":
        "Es läuft bereits ein Snapshot-Vorgang.",
    "La operación se ejecuta en segundo plano; la interfaz sigue "
    "disponible mientras QEMU procesa el snapshot.":
        "Der Vorgang läuft im Hintergrund; die Oberfläche bleibt während "
        "der Verarbeitung durch QEMU verfügbar.",
    "Snapshot — {0}": "Snapshot — {0}",
    "Estado '{0}' guardado y VM pausada.":
        "Zustand '{0}' gespeichert und VM pausiert.",
    "Snapshot '{0}' eliminado.": "Snapshot '{0}' gelöscht.",
    "Snapshot '{0}' restaurado.": "Snapshot '{0}' wiederhergestellt.",
    "Snapshot '{0}' creado.": "Snapshot '{0}' erstellt.",
    "El snapshot '{0}' fue creado y confirmado por QEMU.":
        "Der Snapshot '{0}' wurde von QEMU erstellt und bestätigt.",
    "VM pausada": "VM pausiert",
    "Estado guardado como '{0}'.\n\nLa VM quedó pausada. "
    "Puedes reanudarla con el botón Pausar/Reanudar.":
        "Zustand als '{0}' gespeichert.\n\nDie VM wurde pausiert. "
        "Du kannst sie mit dem Pausieren/Fortsetzen-Button wieder aufnehmen.",
    "Snapshot eliminado": "Snapshot gelöscht",
    "Se eliminó '{0}'.": "'{0}' wurde gelöscht.",
    "Snapshot restaurado": "Snapshot wiederhergestellt",
    "Se restauró '{0}'.": "'{0}' wurde wiederhergestellt.",
    "Error al eliminar snapshot": "Fehler beim Löschen des Snapshots",
    "Error al guardar estado": "Fehler beim Speichern des Zustands",
    "Error al restaurar snapshot": "Fehler beim Wiederherstellen des Snapshots",
    "CREACIÓN": "ERSTELLUNG",
    "ELIMINACIÓN": "LÖSCHUNG",
    "GUARDADO": "SPEICHERUNG",
    "RESTAURACIÓN": "WIEDERHERSTELLUNG",
    "No se pudo completar la operación de snapshot '{0}'.\n\n{1}":
        "Der Snapshot-Vorgang '{0}' konnte nicht abgeschlossen werden.\n\n{1}",
    "¿Restaurar '{0}'?\n\nLa VM volverá al estado del snapshot.":
        "'{0}' wiederherstellen?\n\nDie VM kehrt zum Zustand des Snapshots zurück.",
    "Snapshot solo de discos": "Nur-Disk-Snapshot",
    "El snapshot '{0}' es solo de discos (no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM primero.\n"
    "La VM volverá al estado del snapshot.\n\n"
    "¿Apagar la VM ahora y restaurar el snapshot?":
        "Der Snapshot '{0}' ist nur Disk (enthält kein RAM).\n\n"
        "Zum Wiederherstellen muss die VM zuerst heruntergefahren werden.\n"
        "Die VM kehrt zum Zustand des Snapshots zurück.\n\n"
        "Die VM jetzt herunterfahren und den Snapshot wiederherstellen?",
    "Apagar la VM": "VM herunterfahren",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Der Herunterfahrbefehl konnte nicht gesendet werden.\n\n{0}",
    "Se restauró '{0}' mediante snapshot-load.":
        "'{0}' wurde über snapshot-load wiederhergestellt.",
    "Restauración parcial": "Teilweise Wiederherstellung",
    "El snapshot se restauró en algunos discos, pero falló en otros:\n\n":
        "Der Snapshot wurde auf einigen Festplatten wiederhergestellt, auf anderen schlug er fehl:\n\n",
    "Se restauró el snapshot de disco en los QCOW2 elegibles. "
    "Con la VM apagada no se restaura el estado de RAM/CPU.":
        "Der Disk-Snapshot wurde auf den geeigneten QCOW2 wiederhergestellt. "
        "Bei ausgeschalteter VM wird der RAM-/CPU-Zustand nicht wiederhergestellt.",
    "El snapshot '{0}' es solo de discos "
    "(no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM y volver "
    "a intentarlo. QEMU no puede restaurar snapshots "
    "sin vmstate con la VM encendida.":
        "Der Snapshot '{0}' ist nur Disk "
        "(enthält kein RAM).\n\n"
        "Zum Wiederherstellen muss die VM heruntergefahren und erneut "
        "versucht werden. QEMU kann Snapshots ohne vmstate "
        "bei laufender VM nicht wiederherstellen.",
    "La VM volvió a un estado operativo después de restaurar '{0}'.\n\n"
    "QEMU no confirmó el fin del job dentro del tiempo de espera, "
    "pero la restauración se aplicó.":
        "Die VM kehrte nach dem Wiederherstellen von '{0}' in einen betriebsbereiten Zustand zurück.\n\n"
        "QEMU bestätigte das Ende des Jobs nicht innerhalb des Zeitlimits, "
        "aber die Wiederherstellung wurde angewendet.",
    "No se pudo restaurar el snapshot.\n\n{0}":
        "Der Snapshot konnte nicht wiederhergestellt werden.\n\n{0}",
    "Eliminar snapshot": "Snapshot löschen",
    "¿Eliminar '{0}'?": "'{0}' löschen?",
    "Eliminación parcial": "Teilweise Löschung",
    "El snapshot se eliminó de algunos discos, pero falló en otros:\n\n":
        "Der Snapshot wurde auf einigen Festplatten gelöscht, auf anderen schlug es fehl:\n\n",
    "No se pudo eliminar el snapshot.\n\n{0}":
        "Der Snapshot konnte nicht gelöscht werden.\n\n{0}",
    "Cambiar nombre": "Umbenennen",
    "Nuevo nombre para '{0}':": "Neuer Name für '{0}':",
    "Cambiar nombre de snapshot": "Snapshot umbenennen",
    "QEMU no proporciona un renombrado interno directo. "
    "Esta acción creará un snapshot nuevo con el estado ACTUAL "
    "de la VM y eliminará el anterior.\n\n¿Continuar?":
        "QEMU bietet keine direkte interne Umbenennung. "
        "Diese Aktion erstellt einen neuen Snapshot mit dem AKTUELLEN "
        "Zustand der VM und löscht den vorherigen.\n\nFortfahren?",
    "Cambio de nombre parcial": "Teilweise Umbenennung",
    "El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n":
        "Der neue Snapshot wurde auf einigen Festplatten erstellt, aber es gab Fehler:\n\n",
    "No se pudo cambiar el nombre.\n\n{0}":
        "Der Name konnte nicht geändert werden.\n\n{0}",

    # ================================================================
    # Organigrama: nodos y menus
    # ================================================================
    '(sin miniatura)': '(keine Miniatur)',
    'Restaurar este snapshot': 'Diesen Snapshot wiederherstellen',
    'Renombrar': 'Umbenennen',
    '✏ Renombrar': 'Umbenennen',
    '➕ Crear snapshot hijo': 'Untergeordneten Snapshot erstellen',
    '🔗 Establecer padre…': 'Übergeordneten festlegen…',
    '⬆ Mover a la raíz': 'Zur Wurzel verschieben',
    'Snapshot creado': 'Snapshot erstellt',
    'Error al cambiar nombre': 'Fehler beim Umbenennen',
}
