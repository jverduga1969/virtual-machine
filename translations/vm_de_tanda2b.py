# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2b.

Cubre: panel izquierdo (lista de VMs, buscador, orden, filtro de
grupo) + toolbar completo de Resumen + panel derecho estatico
(Uso de recursos, Informacion general, Ultimo snapshot).

Se fusiona con vm_de.py por _load_external_dict().
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 2b: panel izquierdo + toolbar de Resumen
    # ================================================================
    "<b>MÁQUINAS VIRTUALES</b>": "<b>VIRTUELLE MASCHINEN</b>",
    "🔍 Buscar máquinas...": "🔍 Maschinen suchen...",
    "Ordenar: Nombre (A-Z)": "Sortieren: Name (A-Z)",
    "Ordenar: Estado": "Sortieren: Status",
    "Ordenar: Ultima vez usada": "Sortieren: Zuletzt verwendet",
    "Como ordenar la lista de maquinas virtuales.\n"
    "  - Nombre: alfabetico.\n"
    "  - Estado: encendidas primero, luego pausadas, apagadas al final.\n"
    "  - Ultima vez usada: por fecha de modificacion del vm_config.ini\n"
    "    (aproxima cuando se configuro por ultima vez).":
        "Wie die Liste der virtuellen Maschinen sortiert wird.\n"
        "  - Name: alphabetisch.\n"
        "  - Status: laufende zuerst, dann pausierte, ausgeschaltete am Ende.\n"
        "  - Zuletzt verwendet: nach Änderungsdatum der vm_config.ini\n"
        "    (Näherung, wann zuletzt konfiguriert).",
    "Todos los grupos": "Alle Gruppen",
    "Muestra solo las VMs de un grupo concreto.\n"
    "  • Todos los grupos: sin filtro de grupo.\n"
    "  • Sin grupo: solo VMs sin etiqueta de grupo.\n"
    "  • <nombre>: solo VMs con ese grupo.\n"
    "\n"
    "Los grupos se asignan desde el botón '🏷 Etiqueta' del Resumen.":
        "Nur VMs einer bestimmten Gruppe anzeigen.\n"
        "  • Alle Gruppen: kein Gruppenfilter.\n"
        "  • Ohne Gruppe: nur VMs ohne Gruppenbezeichnung.\n"
        "  • <Name>: nur VMs mit dieser Gruppe.\n"
        "\n"
        "Gruppen werden über den Button '🏷 Bezeichnung' in der Übersicht zugewiesen.",
    "➕ Nueva VM": "➕ Neue VM",
    "Selecciona una máquina virtual": "Virtuelle Maschine auswählen",
    "● Sin VM seleccionada": "● Keine VM ausgewählt",
    "▶ Iniciar": "▶ Starten",
    "⏸ Pausar": "⏸ Pausieren",
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.":
        "VM pausieren. Mit dem Pfeil weitere Optionen:\n"
        "• Pausieren (schnell): stoppt, ohne den Zustand auf Disk zu speichern.\n"
        "• Zustand speichern und pausieren: schreibt RAM vor dem Pausieren auf Disk.\n"
        "• Fortsetzen: setzt die pausierte VM fort.",
    "⏹ Apagar": "⏹ Herunterfahren",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.":
        "Herunterfahren (ACPI): fordert die VM zum geordneten Herunterfahren auf.",
    "⏹ Apagado (ACPI)": "⏹ Herunterfahren (ACPI)",
    "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\n"
    "encendido en un equipo real. El sistema operativo invitado decide cuándo\n"
    "y cómo cerrar. Puede tardar unos segundos o no responder si está colgado.":
        "Fordert die VM zum geordneten Herunterfahren auf, wie das Drücken des\n"
        "Ein-/Ausschalters an einem echten Rechner. Das Gastsystem entscheidet,\n"
        "wann und wie es schließt. Kann ein paar Sekunden dauern oder hängen bleiben.",
    "⏻ Forzar apagado": "⏻ Ausschalten erzwingen",
    "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\n"
    "como desenchufar un equipo real. Puede causar pérdida de datos no\n"
    "guardados; úsalo solo si la VM no responde al apagado normal.":
        "Schaltet die VM sofort ab, ohne das Gastsystem zu warnen —\n"
        "wie das Ziehen des Steckers an einem echten Rechner. Kann Verlust\n"
        "ungespeicherter Daten verursachen; nur verwenden, wenn die VM nicht\n"
        "auf normales Herunterfahren reagiert.",
    "⟳ Reiniciar": "⟳ Neustart",
    "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\n"
    "No es un apagado ordenado del sistema operativo invitado: simplemente\n"
    "reinicia el hardware virtual.":
        "Startet die VM neu (entspricht dem Reset-Knopf an einem echten Rechner).\n"
        "Kein geordnetes Herunterfahren des Gastsystems: es wird nur die\n"
        "virtuelle Hardware zurückgesetzt.",
    "⟲ Forzar reinicio": "⟲ Neustart erzwingen",
    "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\n"
    "al sistema operativo invitado. Úsalo solo si la VM no responde ni al\n"
    "apagado ni al reinicio normales.":
        "Unterbricht die VM vollständig und startet sie von Null neu, ohne das\n"
        "Gastsystem zu warnen. Nur verwenden, wenn die VM weder auf normales\n"
        "Herunterfahren noch auf Neustart reagiert.",
    "⏸ Pausar (rápido)": "⏸ Pausieren (schnell)",
    "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\n"
    "el estado (RAM y dispositivos) se pierde si el host se reinicia.":
        "Pausiert die VM, ohne den Zustand auf Disk zu speichern. Sofort, aber\n"
        "der Zustand (RAM und Geräte) geht bei einem Host-Neustart verloren.",
    "▶ Reanudar": "▶ Fortsetzen",
    "Reanuda la ejecución de la VM pausada.":
        "Setzt die Ausführung der pausierten VM fort.",
    "📸 Tomar Snapshot": "📸 Snapshot erstellen",
    "Guarda la RAM y el estado de los dispositivos a disco (como un\n"
    "snapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\n"
    "El snapshot aparecerá en la pestaña Snapshots y su captura de\n"
    "pantalla en el panel 'Último snapshot'.":
        "Speichert RAM und Gerätezustand auf Disk (wie einen Snapshot)\n"
        "und pausiert dann die VM. Dauert länger, übersteht aber Neustarts.\n"
        "Der Snapshot erscheint im Reiter Snapshots, der Screenshot\n"
        "im Bereich 'Letzter Snapshot'.",
    "Iniciar VM": "VM starten",
    "Pausar/Reanudar VM": "VM pausieren/fortsetzen",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\n"
    "Usa la flecha para más opciones (forzar, reiniciar).":
        "Herunterfahren (ACPI): fordert die VM zum geordneten Herunterfahren auf.\n"
        "Mit dem Pfeil weitere Optionen (erzwingen, Neustart).",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Wähle eine VM zur Verwaltung. Mit 'Neue virtuelle Maschine' eine weitere anlegen.",
    "Nueva máquina virtual": "Neue virtuelle Maschine",
    "● Nueva VM": "● Neue VM",
    "💿 Medios": "💿 Medien",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Cambia ISO en caliente, expulsa medios y conecta/desconecta\n"
    "USB sin reiniciar la máquina. Atajo: Ctrl+M.":
        "Medien der VM: CD/DVD-Laufwerke und USB-Geräte.\n"
        "ISO im laufenden Betrieb wechseln, Medien auswerfen und\n"
        "USB verbinden/trennen ohne Neustart. Tastenkürzel: Strg+M.",
    "🧬 Clonar": "🧬 Klonen",
    "Crea una copia completa de esta VM en una carpeta nueva.":
        "Erstellt eine vollständige Kopie dieser VM in einem neuen Ordner.",
    "🧬 Desenlazar": "🧬 Entkoppeln",
    "Convierte este clon enlazado en un QCOW2 autónomo.\n"
    "Después, el clon deja de depender del original y puede\n"
    "moverse o copiarse por separado.\n\n"
    "Solo aparece cuando la VM seleccionada es un clon\n"
    "enlazado y está apagada.":
        "Wandelt diesen verknüpften Klon in ein eigenständiges QCOW2 um.\n"
        "Danach hängt der Klon nicht mehr vom Original ab und kann\n"
        "eigenständig verschoben oder kopiert werden.\n\n"
        "Erscheint nur, wenn die ausgewählte VM ein verknüpfter\n"
        "Klon und ausgeschaltet ist.",
    "⇩ Importar": "⇩ Importieren",
    "Importar una VM desde una carpeta (con vm_config.ini) o desde\n"
    "un archivo .tar.gz / .zip exportado previamente.":
        "Eine VM aus einem Ordner (mit vm_config.ini) oder aus einer\n"
        "zuvor exportierten .tar.gz- / .zip-Datei importieren.",
    "⇪ Exportar": "⇪ Exportieren",
    "Exportar esta VM como carpeta, .tar.gz o .zip portable.\n"
    "Se omiten los archivos de runtime (pids, sockets, logs).":
        "Diese VM als Ordner, portable .tar.gz- oder .zip-Datei exportieren.\n"
        "Laufzeitdateien (PIDs, Sockets, Logs) werden übersprungen.",
    "💾 Plantilla": "💾 Vorlage",
    "Guarda la configuración de hardware de esta VM como\n"
    "plantilla reutilizable. Se omiten discos, ISOs, MACs,\n"
    "carpetas compartidas, notas y reglas NAT.\n"
    "Aparecerá en el menú del botón '➕ Nueva VM'.":
        "Speichert die Hardware-Konfiguration dieser VM als\n"
        "wiederverwendbare Vorlage. Festplatten, ISOs, MACs,\n"
        "gemeinsame Ordner, Notizen und NAT-Regeln werden übersprungen.\n"
        "Erscheint im Menü des Buttons '➕ Neue VM'.",
    "📜 Comando QEMU": "📜 QEMU-Befehl",
    "Muestra el contenido de run_temp.sh: el comando exacto con\n"
    "el que QEMU está ejecutando (o ejecutó por última vez) esta\n"
    "VM. Solo está disponible si la VM se ha arrancado alguna vez.":
        "Zeigt den Inhalt von run_temp.sh: den exakten Befehl, mit dem\n"
        "QEMU diese VM ausführt (oder zuletzt ausgeführt hat). Nur\n"
        "verfügbar, wenn die VM mindestens einmal gestartet wurde.",
    "📝 Notas": "📝 Notizen",
    "Notas libres sobre esta VM. Se guardan en vm_config.ini\n"
    "(extra.notes) y aparecen como aviso amarillo debajo del\n"
    "estado en esta misma pestaña.":
        "Freie Notizen zu dieser VM. Werden in vm_config.ini gespeichert\n"
        "(extra.notes) und erscheinen als gelber Hinweis unter dem\n"
        "Status in diesem Reiter.",
    "🏷 Etiqueta": "🏷 Bezeichnung",
    "Grupo y color de esta VM. El grupo agrupa VMs en la lista\n"
    "lateral; el color se aplica como fondo del ítem.":
        "Gruppe und Farbe dieser VM. Die Gruppe bündelt VMs in der\n"
        "Seitenliste; die Farbe wird als Hintergrund des Eintrags angewendet.",
    "⚖ Comparar con defaults": "⚖ Mit Standardwerten vergleichen",
    "Compara la configuración actual de esta VM con los\n"
    "valores por defecto del perfil del SO. Permite aplicar\n"
    "los defaults a un campo o a todos; los cambios se aplican\n"
    "a los widgets y se persisten al Guardar.":
        "Vergleicht die aktuelle Konfiguration dieser VM mit den\n"
        "Standardwerten des Betriebssystem-Profils. Standardwerte\n"
        "können auf ein Feld oder alle angewendet werden; Änderungen\n"
        "betreffen die Widgets und werden beim Speichern persistiert.",
    "🗑 Eliminar": "🗑 Löschen",
    "Elimina esta VM (con opción de conservar los discos).":
        "Löscht diese VM (mit Option, die Festplatten zu behalten).",
    "🗑️ Eliminar": "\U0001f5d1 Löschen",
    "ℹ️ Información general": "ℹ️ Allgemeine Informationen",
    "🖼️ Último snapshot": "🖼️ Letzter Snapshot",

    # ================================================================
    # Tanda 2c: panel derecho - seccion Uso de recursos
    # ================================================================
    "📌 Fijar": "📌 Anheften",
    "Fija este panel como columna derecha de la ventana, siempre visible.\n"
    "Útil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\n"
    "Vuelve a pulsar para devolverlo a Resumen.":
        "Heftet dieses Bedienfeld als rechte Spalte des Fensters an, dauerhaft sichtbar.\n"
        "Nützlich zur CPU-/RAM-Überwachung während der Arbeit in einem anderen Reiter.\n"
        "Erneut drücken, um es zur Übersicht zurückzugeben.",
    "📊 Uso de recursos": "📊 Ressourcennutzung",
    "CPU (VM)": "CPU (VM)",
    "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n"
    "100% = el proceso usa el equivalente a todos los hilos del host.\n"
    "Si el host tiene 8 hilos y QEMU usa 4, verás 50%.":
        "CPU-Nutzung des QEMU-Prozesses auf dem Host, dieser VM zugeordnet.\n"
        "100% = der Prozess nutzt das Äquivalent aller Host-Threads.\n"
        "Bei 8 Host-Threads und 4 durch QEMU werden 50% angezeigt.",
    "RAM (QEMU)": "RAM (QEMU)",
    "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\n"
    "realmente en el sistema anfitrión), como porcentaje de la RAM\n"
    "total del host. No es la RAM que 've' el sistema invitado.":
        "RSS-Speicher des QEMU-Prozesses auf dem Host (was QEMU tatsächlich\n"
        "im Wirtssystem belegt), als Prozentsatz des Gesamt-RAM des Hosts.\n"
        "Nicht der RAM, den das Gastsystem 'sieht'.",
    "Disco (VM)": "Festplatte (VM)",
    "I/O de disco generado por el proceso QEMU para esta VM, según\n"
    "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
    "Es el tráfico real a los archivos de disco de la VM en el host.":
        "Festplatten-I/O, das der QEMU-Prozess für diese VM erzeugt, laut\n"
        "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
        "Dies ist der reale Datenverkehr zu den Festplattendateien der VM auf dem Host.",
    "Red (VM)": "Netzwerk (VM)",
    "Tráfico de red de esta VM.\n"
    "• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n"
    "  asociada en el host (exacto).\n"
    "• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n"
    "  el host, así que no se puede medir sin Guest Agent.\n"
    "  El gráfico mostrará 'NAT (sin medida)'.":
        "Netzwerkverkehr dieser VM.\n"
        "• TAP-/Bridge-Modus: es werden die echten Zähler der zugeordneten\n"
        "  Host-Schnittstelle gelesen (exakt).\n"
        "• NAT-Modus: QEMU nutzt einen internen Stack ohne sichtbare\n"
        "  Host-Schnittstelle, daher ohne Guest Agent nicht messbar.\n"
        "  Die Anzeige zeigt 'NAT (keine Messung)'.",
    "Estado:": "Status:",
    "Tiempo activo:": "Laufzeit:",
    "Procesos:": "Prozesse:",
    "Dirección IP:": "IP-Adresse:",
    "Dirección MAC:": "MAC-Adresse:",
    "Guest Agent:": "Guest Agent:",
    "Carpetas:": "Ordner:",
    "Clipboard:": "Zwischenablage:",
    "spice-vdagent:": "spice-vdagent:",
    "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\n"
    "Cuando está activo, el clipboard bidireccional y la\n"
    "resolución automática funcionan.":
        "Erkennung von spice-vdagent im Gast über QEMU Guest Agent.\n"
        "Bei Aktivität funktionieren bidirektionale Zwischenablage und\n"
        "automatische Auflösung.",
    "PID QEMU:": "QEMU-PID:",
    "Uso de CPU del proceso QEMU expresado como porcentaje del total\n"
    "de hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\n"
    "valor mostrado es 50%.":
        "CPU-Nutzung des QEMU-Prozesses als Prozentsatz aller Host-Threads.\n"
        "Bei 8 Host-Threads und 4 durch QEMU beträgt der angezeigte\n"
        "Wert 50%.",
    "CPU (VM):": "CPU (VM):",
    "Memoria RAM libre del host, respecto al total.":
        "Freier Host-RAM im Verhältnis zum Gesamtspeicher.",
    "RAM host:": "Host-RAM:",
    "Tamaño del archivo de disco principal de la VM y su tamaño\n"
    "virtual (lo que ve el sistema invitado).":
        "Größe der Hauptfestplattendatei der VM und ihre virtuelle\n"
        "Größe (was das Gastsystem sieht).",
    "Disco:": "Festplatte:",
    "Número de snapshots registrados y antigüedad del último.":
        "Anzahl der registrierten Snapshots und Alter des letzten.",
    "Snapshots:": "Snapshots:",
    "Sin VM seleccionada": "Keine VM ausgewählt",
    "↩ Restaurar este snapshot": "↩ Diesen Snapshot wiederherstellen",
    "Restaura el snapshot más reciente de esta VM.\n"
    "Si la VM está corriendo, se restaura en caliente (snapshot-load).\n"
    "Si está apagada, se restauran los discos QCOW2 internos.":
        "Stellt den neuesten Snapshot dieser VM wieder her.\n"
        "Bei laufender VM wird im laufenden Betrieb wiederhergestellt (snapshot-load).\n"
        "Bei ausgeschalteter VM werden die internen QCOW2-Festplatten wiederhergestellt.",
}
