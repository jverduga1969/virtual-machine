# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 4a.

Cubre: barrido general de cadenas hardcodeadas (Tanda 4a-1),
Consola Grafica + Consola de Progreso (4a-2.2), valores dinamicos
del panel derecho (4a-2.4), compare_defaults_mixin y
vm_templates_mixin (4a-2.5.1).

Los dialogos OVF/OVA + ciclo de vida (import/export/clone/unlink/
delete) van en vm_de_tanda4b.py. El resto de Tanda 4a va en 4c.
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 4a-1: barrido general de cadenas hardcodeadas
    # ================================================================
    "Sin grupo": "Keine Gruppe",
    "Resumen de Configuración": "Konfigurationsübersicht",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Wähle eine virtuelle Maschine aus der linken Liste.",
    "Sin medio": "Kein Medium",
    "🌐 descarga": "🌐 Download",
    "💡 Sugerencias": "💡 Vorschläge",
    "🌐 Descargar instalador de Internet al iniciar":
        "🌐 Installer beim Start aus dem Internet herunterladen",
    "🌐 Instalador por Internet (se descargará al iniciar)":
        "🌐 Internet-Installer (wird beim Start heruntergeladen)",
    "🌐 Descargar System Recovery al iniciar":
        "🌐 System Recovery beim Start herunterladen",
    "🌐 System Recovery (se descargará al iniciar)":
        "🌐 System Recovery (wird beim Start heruntergeladen)",
    "🌐 descargar instalador al iniciar":
        "🌐 Installer beim Start herunterladen",
    "🌐 descargar System Recovery al iniciar":
        "🌐 System Recovery beim Start herunterladen",

    # ================================================================
    # Tanda 4a-2.2: Consola Grafica
    # ================================================================
    "La VM no está corriendo.": "Die VM läuft nicht.",
    "↗ Abrir en ventana externa": "↗ In externem Fenster öffnen",
    "Lanza el visor externo del protocolo configurado en Pantalla,\n"
    "aunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez.":
        "Startet den externen Viewer des unter Anzeige konfigurierten Protokolls,\n"
        "auch wenn der Modus 'eingebettet' ist. Nützlich, um beide Ansichten gleichzeitig zu haben.",
    "Externos en pantalla completa": "Externe im Vollbild",
    "Cuando está marcado, los visores externos (los que abre el\n"
    "botón 'Abrir en ventana externa' o el modo 'Ventana externa'\n"
    "de Configuración → Pantalla) se lanzan ocupando toda la\n"
    "pantalla. NO afecta al visor embebido (VNC dentro de la app):\n"
    "para ese, usa el botón 'Pantalla completa del visor'.":
        "Wenn aktiviert, werden externe Viewer (die durch den Button\n"
        "'In externem Fenster öffnen' oder den Modus 'Externes Fenster'\n"
        "in Konfiguration → Anzeige geöffnet werden) im Vollbild gestartet.\n"
        "Betrifft NICHT den eingebetteten Viewer (VNC in der Anwendung):\n"
        "Verwende für diesen den Button 'Viewer-Vollbild'.",
    "💿 Medios": "💿 Medien",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Mismo menú que el botón 'Medios' de la pestaña Resumen.\n"
    "Atajo: Ctrl+M.":
        "Medien der VM: CD/DVD-Laufwerke und USB-Geräte.\n"
        "Gleiches Menü wie der Button 'Medien' im Reiter Übersicht.\n"
        "Tastenkürzel: Strg+M.",
    "🔄 Reconectar": "🔄 Neu verbinden",
    "Reconectar el widget VNC.\n"
    "Útil si cambiaste la resolución del guest y la imagen\n"
    "quedó recortada o mal escalada. El cliente VNC básico\n"
    "no puede cambiar el tamaño de su framebuffer sin\n"
    "reconectar.\n\n"
    "Atajo: Ctrl+R.":
        "VNC-Widget neu verbinden.\n"
        "Nützlich, wenn du die Auflösung des Gastes geändert hast und\n"
        "das Bild beschnitten oder falsch skaliert wurde. Der einfache\n"
        "VNC-Client kann die Größe seines Framebuffers nur durch\n"
        "Neuverbinden ändern.\n\n"
        "Tastenkürzel: Strg+R.",
    "🔍−": "🔍−",
    "Reducir el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Zoom des eingebetteten Viewers verkleinern.\n"
        "Stufen: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "Ajustado": "Angepasst",
    "🔍+": "🔍+",
    "Aumentar el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Zoom des eingebetteten Viewers vergrößern.\n"
        "Stufen: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "⊞ Ajustar": "⊞ Anpassen",
    "Ajustar la imagen de la VM al tamaño del widget (escala\n"
    "automática). La VM se ve entera, sin barras de scroll.\n"
    "Si la relación de aspecto no coincide, aparecen bandas\n"
    "negras a los lados.":
        "Das VM-Bild an die Größe des Widgets anpassen (automatische\n"
        "Skalierung). Die VM ist vollständig sichtbar, ohne Bildlaufleisten.\n"
        "Bei abweichendem Seitenverhältnis erscheinen schwarze\n"
        "Streifen an den Seiten.",
    "1:1 Tamaño real": "1:1 Originalgröße",
    "Mostrar la imagen de la VM a su resolución real (100%).\n"
    "Si no cabe en la ventana, aparecen barras de scroll.":
        "Das VM-Bild in seiner tatsächlichen Auflösung anzeigen (100%).\n"
        "Falls es nicht ins Fenster passt, erscheinen Bildlaufleisten.",
    "🎬 Presentación": "🎬 Präsentation",
    "Modo presentación: oculta los paneles laterales, entra\n"
    "en pantalla completa y salta a la Consola Gráfica.\n"
    "Requiere que la VM esté encendida.\n\n"
    "Atajo: F11. Para salir: F11 o Escape.":
        "Präsentationsmodus: blendet die Seitenleisten aus, wechselt\n"
        "ins Vollbild und springt zur Grafischen Konsole.\n"
        "Erfordert, dass die VM läuft.\n\n"
        "Tastenkürzel: F11. Zum Verlassen: F11 oder Escape.",
    "⛶ Pantalla completa del visor": "⛶ Viewer-Vollbild",
    "Salir con:": "Verlassen mit:",
    "Ctrl derecho (como VirtualBox)": "Rechte Strg (wie VirtualBox)",
    "Ctrl+Alt+Intro": "Strg+Alt+Enter",
    "Combinación de teclas para salir de la pantalla completa del visor embebido.\n"
    "Evita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\n"
    "usar Escape o F11 dentro del sistema invitado, no la uses aquí).":
        "Tastenkombination zum Verlassen des Vollbilds des eingebetteten Viewers.\n"
        "Vermeide eine Taste zu wählen, die du innerhalb der VM benötigst (z. B. wenn du\n"
        "Escape oder F11 im Gastsystem verwenden willst, nutze sie hier nicht).",

    # ================================================================
    # Tanda 4a-2.2: Consola de Progreso
    # ================================================================
    "🩺 Salud de la VM": "🩺 VM-Zustand",
    "Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.":
        "Prüft auf einen Blick, ob die VM wirklich läuft, ob der Guest Agent antwortet und ob die gemeinsamen Ordner eingehängt wurden.",
    "🚦 Semáforos": "🚦 Ampeln",
    "🧹 Limpiar procesos huérfanos": "🧹 Verwaiste Prozesse bereinigen",
    "Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.":
        "Sucht nach QEMU-/virtiofsd-/swtpm-Prozessen aus einer früheren Sitzung (durch einen erzwungenen Abschluss) und bietet an, sie zu beenden.",
    "Nivel:": "Stufe:",
    "Todo": "Alles",
    "Avisos+": "Warnungen+",
    "Errores": "Fehler",
    "🔍 Filtrar...": "🔍 Filtern...",
    "Auto-scroll": "Automatisches Scrollen",
    "📄 Ver log completo": "📄 Vollständiges Log anzeigen",
    "Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.":
        "Zeigt den vollständigen auf dem Datenträger gespeicherten Verlauf dieser VM (launch.log), nicht nur das, was in dieses Fenster passt.",
    "💾 Exportar log": "💾 Log exportieren",
    "Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.":
        "Speichert das vollständige Log dieser VM in einer Datei – nützlich, um Hilfe zu erbitten oder ein Problem zu melden.",
    "Limpiar consola": "Konsole leeren",
    "Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').":
        "Löscht die hier angezeigten Meldungen (der vollständige Verlauf auf dem Datenträger bleibt unberührt; verwende 'Vollständiges Log anzeigen').",

    # ================================================================
    # Tanda 4a-2.4: valores dinamicos del panel derecho
    # ================================================================
    "Guest Agent: —": "Guest Agent: —",
    "Carpetas: —": "Ordner: —",
    "Clipboard: —": "Zwischenablage: —",
    "spice-vdagent: —": "spice-vdagent: —",
    "Guest Agent: apagado": "Guest Agent: aus",
    "Carpetas: apagado": "Ordner: aus",
    "Clipboard: apagado": "Zwischenablage: aus",
    "spice-vdagent: apagado": "spice-vdagent: aus",
    "Guest Agent: {0}": "Guest Agent: {0}",
    "activo": "aktiv",
    "sin respuesta": "keine Antwort",
    "Carpetas: {0}": "Ordner: {0}",
    "OK": "OK",
    "con problemas": "mit Problemen",
    "Clipboard: activo": "Zwischenablage: aktiv",
    "Clipboard: desactivado": "Zwischenablage: deaktiviert",
    "spice-vdagent: activo": "spice-vdagent: aktiv",
    "spice-vdagent: no detectado": "spice-vdagent: nicht erkannt",
    "Ctrl derecho": "Rechte Strg",
    "Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\n"
    "completa en una ventana propia. NO afecta al visor externo:\n"
    "para ese, usa el checkbox 'Externos en pantalla completa'\n"
    "de la fila de estado.\n\n"
    "Pulsa {0} para salir.":
        "Zeigt den EINGEBETTETEN Viewer (VNC in der Anwendung) im Vollbild\n"
        "in einem eigenen Fenster. Betrifft NICHT den externen Viewer:\n"
        "Verwende dafür das Kontrollkästchen 'Externe im Vollbild' in der\n"
        "Statuszeile.\n\n"
        "Drücke {0} zum Verlassen.",
    "▶ Reanudar": "▶ Fortsetzen",
    "Reanudar la VM pausada. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Setzt die pausierte VM fort. Mit dem Pfeil weitere Optionen:\n"
        "• Pausieren (schnell): stoppt, ohne den Zustand auf Disk zu speichern.\n"
        "• Fortsetzen: führt die VM erneut aus.\n"
        "• Snapshot erstellen: speichert den Zustand auf Disk und pausiert.",
    "⏸ Pausar": "⏸ Pausieren",
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Pausiert die VM. Mit dem Pfeil weitere Optionen:\n"
        "• Pausieren (schnell): stoppt, ohne den Zustand auf Disk zu speichern.\n"
        "• Fortsetzen: führt die pausierte VM erneut aus.\n"
        "• Snapshot erstellen: speichert den Zustand auf Disk und pausiert.",
    "Pausar": "Pausieren",
    "La máquina virtual no está corriendo.": "Die virtuelle Maschine läuft nicht.",
    "Control de VM": "VM-Steuerung",
    "No se pudo cambiar el estado de la VM.\n\n{0}":
        "Der VM-Status konnte nicht geändert werden.\n\n{0}",
    "No se pudo pausar la VM.\n\n{0}":
        "Die VM konnte nicht pausiert werden.\n\n{0}",
    "Reanudar": "Fortsetzen",
    "La máquina virtual ya está corriendo.": "Die virtuelle Maschine läuft bereits.",
    "La máquina virtual no está pausada: no hay nada que reanudar.":
        "Die virtuelle Maschine ist nicht pausiert: nichts fortzusetzen.",
    "No se pudo reanudar la VM.\n\n{0}":
        "Die VM konnte nicht fortgesetzt werden.\n\n{0}",
    "Apagar VM": "VM herunterfahren",
    "Reiniciar VM": "VM neu starten",
    "No se pudo enviar la orden de reinicio.\n\n{0}":
        "Der Neustartbefehl konnte nicht gesendet werden.\n\n{0}",
    "Forzar apagado": "Ausschalten erzwingen",
    "Esto corta la VM de inmediato, sin avisar al sistema operativo invitado (como desenchufar un equipo real).\n\n"
    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
    "¿Deseas continuar?":
        "Dies unterbricht die VM sofort, ohne das Gastsystem zu warnen (wie das Ziehen des Steckers an einem echten Rechner).\n\n"
        "Kann Verlust ungespeicherter Daten in der VM verursachen.\n\n"
        "Fortfahren?",
    "Forzar reinicio": "Neustart erzwingen",
    "Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin avisar al sistema operativo invitado.\n\n"
    "Puede causar pérdida de datos no guardados dentro de la VM.\n\n"
    "¿Deseas continuar?":
        "Dies unterbricht die VM sofort und startet sie von Grund auf neu, ohne das Gastsystem zu warnen.\n\n"
        "Kann Verlust ungespeicherter Daten in der VM verursachen.\n\n"
        "Fortfahren?",

    # ================================================================
    # Tanda 4a-2.5.1: compare_defaults_mixin
    # ================================================================
    "Comparar con defaults": "Mit Standardwerten vergleichen",
    "Selecciona primero una máquina virtual.":
        "Wähle zuerst eine virtuelle Maschine aus.",
    "No se pudo determinar el perfil del SO seleccionado.":
        "Das Profil des ausgewählten Betriebssystems konnte nicht ermittelt werden.",
    "Firmware": "Firmware",
    "Chipset": "Chipsatz",
    "CPU (modelo)": "CPU (Modell)",
    "Núcleos": "Kerne",
    "Gráficos": "Grafik",
    "VRAM": "VRAM",
    "Audio": "Audio",
    "Señalización (ratón/teclado)": "Zeigegerät (Maus/Tastatur)",
    "Consola: protocolo": "Konsole: Protokoll",
    "Consola: modo": "Konsole: Modus",
    "Comparación de <b>{0}</b> con los valores por defecto del perfil del SO seleccionado. Las filas con fondo amarillo difieren del default.<br><br>Aplicar un default <b>no</b> guarda la VM: solo cambia el widget. Persiste con <b>Guardar</b> (en Configuración) o al iniciar la VM.":
        "Vergleich von <b>{0}</b> mit den Standardwerten des ausgewählten Betriebssystem-Profils. Zeilen mit gelbem Hintergrund weichen vom Standard ab.<br><br>Das Anwenden eines Standards speichert die VM <b>nicht</b>: Es ändert nur das Widget. Speichere mit <b>Speichern</b> (in der Konfiguration) oder beim Start der VM.",
    "Campo": "Feld",
    "Actual": "Aktuell",
    "Por defecto": "Standard",
    "<b>{0}</b> diferencia(s) de <b>{1}</b> campo(s).":
        "<b>{0}</b> Unterschied(e) von <b>{1}</b> Feld(ern).",
    "Aplicar al campo seleccionado": "Auf ausgewähltes Feld anwenden",
    "Aplicar todos los defaults": "Alle Standardwerte anwenden",
    "Aplicar": "Anwenden",
    "Selecciona primero una fila.": "Wähle zuerst eine Zeile aus.",
    "==> Comparar defaults: aplicados {0} campo(s) a '{1}'.":
        "==> Standardvergleich: {0} Feld(er) auf '{1}' angewendet.",

    # ================================================================
    # Tanda 4a-2.5.1: vm_templates_mixin
    # ================================================================
    "Guardar como plantilla": "Als Vorlage speichern",
    "Esta VM no tiene vm_config.ini todavía.\n\nConfigúrala y guárdala primero.":
        "Diese VM hat noch keine vm_config.ini.\n\nKonfiguriere und speichere sie zuerst.",
    "Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?":
        "Die Vorlage '{0}' existiert bereits.\n\nÜberschreiben?",
    "No se pudo escribir la plantilla.\n\n{0}":
        "Die Vorlage konnte nicht geschrieben werden.\n\n{0}",
    "Plantilla guardada": "Vorlage gespeichert",
    "Plantilla '{0}' creada correctamente.\n\nAparecerá en el menú del botón '➕ Nueva VM'.":
        "Vorlage '{0}' erfolgreich erstellt.\n\nSie erscheint im Menü des Buttons '➕ Neue VM'.",
    "🆕 Nueva VM en blanco": "🆕 Neue leere VM",
    "Desde plantilla:": "Aus Vorlage:",
    "Crear desde plantilla": "Aus Vorlage erstellen",
    "No encuentro la plantilla '{0}'.": "Vorlage '{0}' nicht gefunden.",
    "Ya existe una carpeta para '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Ein Ordner für '{0}' existiert bereits.\n\nErsetzen? (der vorhandene wird gelöscht)",
    "No se pudo eliminar la carpeta existente.\n\n{0}":
        "Der vorhandene Ordner konnte nicht gelöscht werden.\n\n{0}",
    "No se pudo crear la VM.\n\n{0}":
        "Die VM konnte nicht erstellt werden.\n\n{0}",
    "VM creada": "VM erstellt",
    "VM '{0}' creada desde la plantilla '{1}'.\n\nSe ha abierto en Configuración → Almacenamiento para que\nañadas el disco y el medio de instalación. La MAC de red se\nha regenerado para evitar conflictos con otras VMs.":
        "VM '{0}' aus der Vorlage '{1}' erstellt.\n\nSie wurde in Konfiguration → Speicher geöffnet, damit du die\nFestplatte und das Installationsmedium hinzufügen kannst. Die\nNetzwerk-MAC wurde neu generiert, um Konflikte mit anderen VMs zu vermeiden.",
}
