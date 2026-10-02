# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2f-2a.

Cubre: Snapshots automaticos programados (checkbox, frecuencia,
retencion, etiquetas de estado) + Backups automaticos programados
(destino, frecuencia, retencion, allow running, backup_now,
avisos de espacio, etiquetas de estado).

Los Media Library UI y handlers van en vm_de_tanda2f2b.py.
"""

TRANSLATIONS = {

    # ================================================================
    # Snapshots automaticos programados
    # ================================================================
    "Snapshots automaticos programados": "Geplante Snapshots",
    "Activar": "Aktivieren",
    "Cuando esta activo, la app crea snapshots de disco automaticamente en esta VM segun la frecuencia elegida.\n\n"
    "Los snapshots programados son SOLO DE DISCOS (no guardan RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan por antiguedad al superar el limite de retencion.\n\n"
    "No se ejecutan si la VM esta apagada.":
        "Wenn aktiviert, erstellt die App automatisch Disk-Snapshots dieser VM gemäß der gewählten Häufigkeit.\n\n"
        "Geplante Snapshots sind NUR-DISK (sie speichern weder RAM noch Fensterzustand). Sie werden mit dem Präfix 'auto_' erstellt und nach Überschreiten des Aufbewahrungslimits nach Alter gelöscht.\n\n"
        "Sie werden nicht ausgeführt, wenn die VM ausgeschaltet ist.",
    "Cada hora": "Stündlich",
    "Cada 6 horas": "Alle 6 Stunden",
    "Cada 12 horas": "Alle 12 Stunden",
    "Diario": "Täglich",
    "Semanal": "Wöchentlich",
    "Frecuencia con la que se crea el snapshot automatico.\n"
    "El primer snapshot se crea pasada una frecuencia completa desde la activacion (o desde el ultimo, si ya habia uno).":
        "Häufigkeit, mit der der automatische Snapshot erstellt wird.\n"
        "Der erste Snapshot wird nach einer vollständigen Periode seit der Aktivierung (oder seit dem letzten, falls bereits einer existierte) erstellt.",
    "Frecuencia:": "Häufigkeit:",
    "Cuantos snapshots automaticos conservar. Al superar este numero se eliminan los mas antiguos (solo los que empiezan por 'auto_'; los manuales nunca se tocan).":
        "Wie viele automatische Snapshots aufbewahrt werden. Bei Überschreitung dieser Anzahl werden die ältesten gelöscht (nur die mit 'auto_' am Anfang; manuelle werden nie angetastet).",
    "Conservar:": "Behalten:",
    "Los snapshots programados son <b>solo de discos</b>: no guardan RAM ni estado de ventanas. No congelan la VM del usuario (el snapshot completo si puede hacerlo).":
        "Geplante Snapshots sind <b>nur Disk</b>: sie speichern weder RAM noch Fensterzustand. Sie frieren die VM des Benutzers nicht ein (ein vollständiger Snapshot kann dies tun).",
    "Selecciona una VM para programar snapshots.":
        "Wähle eine VM, um Snapshots zu planen.",
    "Desactivado para esta VM.": "Für diese VM deaktiviert.",
    "Sin snapshots programados todavia. Se creara el primero tras cumplirse la frecuencia elegida.":
        "Noch keine geplanten Snapshots. Der erste wird nach Ablauf der gewählten Häufigkeit erstellt.",
    "Pendiente (ultimo: {0}). Se ejecutara en el proximo chequeo del scheduler.":
        "Ausstehend (letzter: {0}). Wird beim nächsten Scheduler-Durchlauf ausgeführt.",
    "Ultimo: {0} · Proximo en ~{1} min.":
        "Letzter: {0} · Nächster in ~{1} Min.",
    "Ultimo: {0}": "Letzter: {0}",

    # ================================================================
    # Backups automaticos programados
    # ================================================================
    "Backups automaticos programados": "Geplante Backups",
    "Cuando esta activo, la app copia la carpeta completa de la VM "
    "(discos, configuracion, snapshots) al destino elegido segun "
    "la frecuencia. Los backups son carpetas independientes; "
    "puedes borrarlos manualmente o dejar que la retencion los "
    "limpie.":
        "Wenn aktiviert, kopiert die App den gesamten VM-Ordner "
        "(Festplatten, Konfiguration, Snapshots) gemäß der Häufigkeit "
        "zum gewählten Ziel. Backups sind eigenständige Ordner; "
        "du kannst sie manuell löschen oder die Aufbewahrung "
        "aufräumen lassen.",
    "Carpeta del host donde guardar los backups":
        "Host-Ordner, in dem Backups gespeichert werden",
    "Elegir carpeta...": "Ordner wählen...",
    "Destino:": "Ziel:",
    "Cuantos backups conservar en el destino. Tras cada backup "
    "exitoso se borran los mas antiguos por encima de este numero.":
        "Wie viele Backups am Ziel aufbewahrt werden. Nach jedem "
        "erfolgreichen Backup werden die ältesten über dieser Anzahl gelöscht.",
    "Tambien cuando la VM esta encendida": "Auch bei laufender VM",
    "Desactivado (recomendado): los backups solo se ejecutan con "
    "la VM apagada.\n\n"
    "Activado: si la VM esta encendida, se copian los discos de "
    "todos modos; la copia puede quedar inconsistente porque QEMU "
    "esta escribiendo en el .qcow2 en ese momento. La restauracion "
    "podria requerir fsck o no arrancar. Solo si estas dispuesto a "
    "asumir ese riesgo.":
        "Deaktiviert (empfohlen): Backups werden nur bei ausgeschalteter "
        "VM ausgeführt.\n\n"
        "Aktiviert: Wenn die VM läuft, werden die Festplatten trotzdem "
        "kopiert; die Kopie kann inkonsistent werden, da QEMU in diesem "
        "Moment in das .qcow2 schreibt. Die Wiederherstellung könnte fsck "
        "erfordern oder nicht starten. Nur, wenn du bereit bist, "
        "dieses Risiko zu tragen.",
    "Los backups son <b>carpetas</b> con todos los archivos de la "
    "VM (discos + configuraci\u00f3n + snapshots + capturas). No "
    "incluyen pids, sockets ni logs. Para restaurar, usa el bot\u00f3n "
    "<b>Importar</b> de la pesta\u00f1a Resumen con la carpeta del "
    "backup.":
        "Backups sind <b>Ordner</b> mit allen Dateien der VM "
        "(Festplatten + Konfiguration + Snapshots + Screenshots). "
        "Sie enthalten weder PIDs, Sockets noch Logs. Zum "
        "Wiederherstellen verwende den Button <b>Importieren</b> im "
        "Reiter Übersicht mit dem Backup-Ordner.",
    "Backup ahora": "Jetzt sichern",
    "Ejecuta un backup inmediato con la configuracion actual, sin "
    "esperar a la proxima programacion.":
        "Führt sofort ein Backup mit der aktuellen Konfiguration aus, "
        "ohne auf den nächsten geplanten Lauf zu warten.",
    "Elegir carpeta de destino para backups":
        "Zielordner für Backups wählen",
    "Selecciona una VM para programar backups.":
        "Wähle eine VM, um Backups zu planen.",
    "Falta elegir una carpeta de destino.":
        "Es muss noch ein Zielordner gewählt werden.",
    "Sin backups todavia. Libre en destino: {0}. "
    "Se creara el primero tras cumplirse la frecuencia.":
        "Noch keine Backups. Frei am Ziel: {0}. "
        "Der erste wird nach Ablauf der Häufigkeit erstellt.",
    "Pendiente (ultimo: {0}). Libre: {1}.":
        "Ausstehend (letzter: {0}). Frei: {1}.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min \u00b7 Libre: {2}.":
        "Letzter: {0} \u00b7 Nächster in ~{1} Min. \u00b7 Frei: {2}.",
    "Ultimo: {0} \u00b7 Libre: {1}.":
        "Letzter: {0} \u00b7 Frei: {1}.",
    "Backup": "Backup",
    "Configura primero una carpeta de destino.":
        "Konfiguriere zuerst einen Zielordner.",
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "Der Zielordner konnte nicht erstellt werden:\n{0}\n\n{1}",
    "Espacio insuficiente en el destino. Necesario ~{0}, libre {1}.":
        "Nicht genügend Speicher am Ziel. Benötigt ~{0}, frei {1}.",
    "Selecciona primero una maquina virtual.":
        "Wähle zuerst eine virtuelle Maschine aus.",
    "Configura primero una carpeta de destino en esta "
    "seccion.":
        "Konfiguriere zuerst einen Zielordner in diesem "
        "Bereich.",
    "Backup con la VM encendida": "Backup bei laufender VM",
    "La VM esta encendida.\n\n"
    "Para evitar una copia inconsistente, apagala primero, o "
    "marca la opcion 'Tambien cuando la VM esta encendida' en "
    "esta seccion (asumiendo el riesgo).":
        "Die VM läuft.\n\n"
        "Um eine inkonsistente Kopie zu vermeiden, fahre sie zuerst "
        "herunter, oder aktiviere die Option 'Auch bei laufender VM' "
        "in diesem Bereich (unter Übernahme des Risikos).",

    # ================================================================
    # Encabezado de la pestana Backups
    # ================================================================
    "<b>Backups de la maquina virtual</b><br>"
    "<span style='color:#666;font-size:11px;'>"
    "Copia periodica de la carpeta completa (discos + config + snapshots). "
    "El backup se guarda como carpeta independiente; se puede restaurar "
    "con el boton <b>Importar</b> de la pestana Resumen apuntando a la "
    "carpeta del backup.</span>":
        "<b>Backups der virtuellen Maschine</b><br>"
        "<span style='color:#666;font-size:11px;'>"
        "Regelmäßige Kopie des gesamten Ordners (Festplatten + Konfiguration + Snapshots). "
        "Das Backup wird als eigenständiger Ordner gespeichert; es kann über "
        "den Button <b>Importieren</b> im Reiter Übersicht wiederhergestellt werden, "
        "indem auf den Backup-Ordner gezeigt wird.</span>",
}
