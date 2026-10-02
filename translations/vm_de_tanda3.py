# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 3.

Cubre: health_dashboard_mixin.py (semaforos + 5 sondas),
diagnostics_mixin.py (log, salud VM, procesos huerfanos, panel
de dependencias) y guest_integration_mixin.py (QGA guest-exec,
Guest Tools, automontaje, clipboard, carpeta compartida).

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 3.1: health_dashboard_mixin.py
    # ================================================================
    "Salud de la máquina virtual": "Zustand der virtuellen Maschine",
    "Comprobando\u2026": "Prüfe\u2026",
    "\U0001f504 Refrescar ahora": "\U0001f504 Jetzt aktualisieren",
    "Cerrar": "Schließen",
    "Sin VM seleccionada.": "Keine VM ausgewählt.",
    "La VM no está corriendo.": "Die VM läuft nicht.",
    "Cada fila muestra el estado de un subsistema de la VM. "
    "Verde: funciona · Amarillo: parcial o sin confirmar · "
    "Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s.":
        "Jede Zeile zeigt den Status eines VM-Subsystems. "
        "Grün: funktioniert · Gelb: teilweise oder unbestätigt · "
        "Rot: nicht verfügbar · Grau: nicht zutreffend. Aktualisierung alle 4 s.",
    "<b style='font-size:15px;'>\U0001f6a6 Semáforos de salud</b>":
        "<b style='font-size:15px;'>\U0001f6a6 Zustandsampeln</b>",
    "\U0001f310 Red de la VM":        "\U0001f310 VM-Netzwerk",
    "\U0001f5a5\ufe0f Internet del host": "\U0001f5a5\ufe0f Host-Internet",
    "\U0001f50a Audio":               "\U0001f50a Audio",
    "\U0001f5bc\ufe0f Pantalla":      "\U0001f5bc\ufe0f Anzeige",
    "\U0001f50c Guest Agent":         "\U0001f50c Guest Agent",
    "Host con salida a Internet (Apple y Cloudflare responden).":
        "Host hat Internetzugang (Apple und Cloudflare antworten).",
    "Salida parcial: uno de los dos destinos no respondió.":
        "Teilweiser Zugang: eines der beiden Ziele antwortete nicht.",
    "El host no tiene salida a Internet.":
        "Der Host hat keinen Internetzugang.",
    "No hay script de arranque todavía.":
        "Noch kein Startskript vorhanden.",
    "No se pudo leer el script de arranque.":
        "Das Startskript konnte nicht gelesen werden.",
    "No hay adaptador de red configurado en esta VM.":
        "In dieser VM ist kein Netzwerkadapter konfiguriert.",
    "NIC {0}: tráfico activo "
    "({1:.1f} KB/s; "
    "rx {2:.1f} MB, "
    "tx {3:.1f} MB).":
        "NIC {0}: aktiver Datenverkehr "
        "({1:.1f} KB/s; "
        "rx {2:.1f} MB, "
        "tx {3:.1f} MB).",
    "NIC {0} con contadores activos pero "
    "sin tráfico en el último intervalo "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB).":
        "NIC {0} mit aktiven Zählern, aber "
        "keinem Datenverkehr im letzten Intervall "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB).",
    "NIC {0}: contadores iniciales leídos "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB); "
    "esperando siguiente lectura para medir velocidad.":
        "NIC {0}: Anfangszähler gelesen "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB); "
        "warte auf nächste Messung zur Geschwindigkeitsberechnung.",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host; esperando segunda lectura "
    "para medir cambio.":
        "NIC {0} konfiguriert. {1} aktive TCP-"
        "Verbindungen auf dem Host; warte auf zweite Messung "
        "zur Änderungsmessung.",
    "NIC {0}: actividad detectada "
    "({1} \u2192 {2} conexiones TCP ESTAB).":
        "NIC {0}: Aktivität erkannt "
        "({1} \u2192 {2} ESTAB-TCP-Verbindungen).",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host, sin cambios en el último "
    "intervalo (la VM puede estar idle).":
        "NIC {0} konfiguriert. {1} aktive TCP-"
        "Verbindungen auf dem Host, keine Änderung im letzten "
        "Intervall (die VM ist möglicherweise inaktiv).",
    "NIC {0} configurada; sin conexiones externas "
    "activas en el host.":
        "NIC {0} konfiguriert; keine aktiven externen "
        "Verbindungen auf dem Host.",
    "NIC {0} configurada. No se pudo medir tráfico (QMP no "
    "expone query-netdev y ss no está disponible).":
        "NIC {0} konfiguriert. Datenverkehr konnte nicht gemessen werden (QMP "
        "stellt query-netdev nicht bereit und ss ist nicht verfügbar).",
    "Sin audio configurado en esta VM.":
        "In dieser VM ist kein Audio konfiguriert.",
    "Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.":
        "Audiodev konfiguriert. pactl nicht verfügbar; Wiedergabe kann nicht bestätigt werden.",
    "Audiodev configurado, pero no hay PID de QEMU para verificar el sink.":
        "Audiodev konfiguriert, aber keine QEMU-PID zur Überprüfung des Sinks verfügbar.",
    "No se pudo consultar pactl: {0}":
        "pactl konnte nicht abgefragt werden: {0}",
    "pactl no respondió.": "pactl hat nicht geantwortet.",
    "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo.":
        "Aktiver Sink: pactl sieht QEMU (PID {0}) bei der Wiedergabe.",
    "Audiodev configurado; QEMU no está reproduciendo ahora. "
    "Es normal si el guest no está emitiendo sonido.":
        "Audiodev konfiguriert; QEMU gibt derzeit nichts wieder. "
        "Das ist normal, wenn der Gast keinen Ton ausgibt.",
    "Framebuffer VNC {0}\u00d7{1}.": "VNC-Framebuffer {0}\u00d7{1}.",
    "Widget VNC conectado, esperando primer frame.":
        "VNC-Widget verbunden, warte auf ersten Frame.",
    "Consola SPICE embebida activa.":
        "Eingebettete SPICE-Konsole aktiv.",
    "Visor externo activo (PID {0}).":
        "Externer Viewer aktiv (PID {0}).",
    "Modo remoto (socket VNC/SPICE) sin widget embebido ni "
    "visor activo. Abre la Consola Gráfica para ver la pantalla.":
        "Remote-Modus (VNC/SPICE-Socket) ohne eingebettetes Widget "
        "oder aktiven Viewer. Öffne die Grafische Konsole, um den Bildschirm zu sehen.",
    "Modo headless (sin salida de pantalla).":
        "Headless-Modus (keine Display-Ausgabe).",
    "Ventana nativa de QEMU activa.":
        "QEMU-natives Fenster aktiv.",
    "Configuración de pantalla detectada en el script de arranque.":
        "Display-Konfiguration im Startskript erkannt.",
    "Guest Agent no habilitado para esta VM "
    "(actívalo en Integración Host \u2194 Guest).":
        "Guest Agent für diese VM nicht aktiviert "
        "(aktiviere ihn in Host \u2194 Gast-Integration).",
    "QEMU Guest Agent responde.": "QEMU Guest Agent antwortet.",
    "Canal QGA presente, pero el guest no responde.":
        "QGA-Kanal vorhanden, aber der Gast antwortet nicht.",
    "Canal QGA presente, sin respuesta: {0}":
        "QGA-Kanal vorhanden, keine Antwort: {0}",

    # ================================================================
    # Tanda 3.2: diagnostics_mixin.py
    # ================================================================
    "Ver log completo": "Vollständiges Log anzeigen",
    "Selecciona una VM primero.": "Wähle zuerst eine VM aus.",
    "Todavía no hay historial guardado para esta VM.":
        "Für diese VM ist noch kein Verlauf gespeichert.",
    "Exportar log": "Log exportieren",
    "Log completo \u2014 {0}": "Vollständiges Log \u2014 {0}",
    "No se pudo leer el log: {0}":
        "Das Log konnte nicht gelesen werden: {0}",
    "No se pudo exportar el log: {0}":
        "Das Log konnte nicht exportiert werden: {0}",
    "Log exportado a:\n{0}": "Log exportiert nach:\n{0}",
    "Salud de la VM": "VM-Zustand",
    "VM: {0}": "VM: {0}",
    "Carpeta: {0}": "Ordner: {0}",
    "\u25cf QEMU: detenido.": "\u25cf QEMU: angehalten.",
    "\u25cf QEMU: {0}{1}.": "\u25cf QEMU: {0}{1}.",
    "\u25cf Guest Agent: no aplica (VM apagada).":
        "\u25cf Guest Agent: nicht zutreffend (VM ausgeschaltet).",
    "\u25cf Guest Agent: responde (v{0}).":
        "\u25cf Guest Agent: antwortet (v{0}).",
    "\u25cf Guest Agent: sin respuesta ({0}). "
    "Verifica que qemu-guest-agent esté instalado y "
    "corriendo en el guest.":
        "\u25cf Guest Agent: keine Antwort ({0}). "
        "Überprüfe, ob qemu-guest-agent im Gast installiert ist "
        "und läuft.",
    "\u25cf Carpetas compartidas (VirtioFS): ninguna configurada.":
        "\u25cf Gemeinsame Ordner (VirtioFS): keine konfiguriert.",
    "\u25cf Carpetas compartidas (VirtioFS):":
        "\u25cf Gemeinsame Ordner (VirtioFS):",
    "    - {0}: no aplica (VM apagada).":
        "    - {0}: nicht zutreffend (VM ausgeschaltet).",
    "    - {0}: virtiofsd activo (PID {1}).":
        "    - {0}: virtiofsd aktiv (PID {1}).",
    "    - {0}: NO está activo. Revisa {1} si "
    "esperabas que funcionara.":
        "    - {0}: NICHT aktiv. Überprüfe {1}, wenn "
        "du erwartet hast, dass es funktioniert.",
    "Limpiar procesos huérfanos": "Verwaiste Prozesse bereinigen",
    "No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores.":
        "Es wurden keine QEMU-/virtiofsd-Prozesse aus früheren Sitzungen gefunden.",
    "VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):":
        "VMs mit laufendem QEMU (werden hier nicht angetastet, verwende 'VM stoppen', um sie herunterzufahren):",
    "  - {0} (PID {1})": "  - {0} (PID {1})",
    "Procesos virtiofsd huérfanos encontrados:":
        "Verwaiste virtiofsd-Prozesse gefunden:",
    "  - {0}: virtiofsd PID {1}": "  - {0}: virtiofsd PID {1}",
    "Se detuvieron {0} proceso(s) huérfano(s).":
        "{0} verwaiste(r) Prozess(e) wurde(n) beendet.",
    "\n\nNo se pudieron detener:\n":
        "\n\nKonnten nicht beendet werden:\n",
    "Nada que limpiar.": "Nichts zu bereinigen.",
    "Virtualización: sin comprobar": "Virtualisierung: ungeprüft",
    "Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema.":
        "Drücke 'Abhängigkeiten prüfen', um die vollständige Systemdiagnose durchzuführen.",
    "Distribución: {0}": "Distribution: {0}",
    "Gestor de paquetes: {0}": "Paketmanager: {0}",
    "no encontrado": "nicht gefunden",
    "firmware disponible": "Firmware verfügbar",
    "sin plantilla Secure Boot": "keine Secure-Boot-Vorlage",
    "módulos": "Module",
    "módulo no cargado": "Modul nicht geladen",
    "OK": "OK",
    "FALTA": "FEHLT",
    " ({0})": " ({0})",
    "SIN COMPROBAR": "UNGEPRÜFT",
    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | "
    "TPM {4} | Audio {5} | GPU {6}":
        "Virtualisierung: {0} | QEMU {1} | KVM {2} | OVMF {3} | "
        "TPM {4} | Audio {5} | GPU {6}",
    "REVISAR": "PRÜFEN",
    "Distribución: {0}\n"
    "Gestor de paquetes: {1}\n"
    "Secure Boot: {2}\n"
    "VirtIO: {3}\n"
    "Audio: {4}\n"
    "GPU: {5}\n"
    "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}":
        "Distribution: {0}\n"
        "Paketmanager: {1}\n"
        "Secure Boot: {2}\n"
        "VirtIO: {3}\n"
        "Audio: {4}\n"
        "GPU: {5}\n"
        "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}",
    "disponible": "verfügbar",
    "no disponible": "nicht verfügbar",
    "no detectado": "nicht erkannt",
    "sí": "ja",
    "no": "nein",
    "Dependencias": "Abhängigkeiten",
    "La comprobación/reparación terminó correctamente.":
        "Die Prüfung/Reparatur wurde erfolgreich abgeschlossen.",
    "No se pudieron reparar todas las dependencias.\n\n{0}":
        "Nicht alle Abhängigkeiten konnten repariert werden.\n\n{0}",

    # ================================================================
    # Tanda 3.3: guest_integration_mixin.py
    # ================================================================
    "Carpetas compartidas": "Gemeinsame Ordner",
    "Las dependencias del host ya están instaladas.":
        "Die Host-Abhängigkeiten sind bereits installiert.",
    "Instalar dependencias": "Abhängigkeiten installieren",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Fehlen:\n\n• {0}\n\nJetzt mit dem Paketmanager des Systems installieren?",
    "Las dependencias de carpetas compartidas quedaron instaladas y verificadas.":
        "Die Abhängigkeiten für gemeinsame Ordner wurden installiert und überprüft.",
    "No se pudieron instalar todas las dependencias.\n\n{0}":
        "Nicht alle Abhängigkeiten konnten installiert werden.\n\n{0}",
    "El socket de QEMU Guest Agent no está disponible.":
        "Der QEMU-Guest-Agent-Socket ist nicht verfügbar.",
    "QEMU Guest Agent cerró el canal durante la sincronización.":
        "QEMU Guest Agent hat den Kanal während der Synchronisierung geschlossen.",
    "Tiempo agotado sincronizando QEMU Guest Agent.":
        "Zeitüberschreitung bei der Synchronisierung von QEMU Guest Agent.",
    "QEMU Guest Agent cerró el canal.":
        "QEMU Guest Agent hat den Kanal geschlossen.",
    "Tiempo agotado esperando la respuesta de QEMU Guest Agent.":
        "Zeitüberschreitung beim Warten auf die Antwort von QEMU Guest Agent.",
    "Guest Agent no devolvió el PID de guest-exec.":
        "Guest Agent hat die PID von guest-exec nicht zurückgegeben.",
    "guest-exec terminó con código {0}.":
        "guest-exec wurde mit Code {0} beendet.",
    "Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent.":
        "Zeitüberschreitung beim Warten auf das Ende des über QEMU Guest Agent ausgeführten Befehls.",
    "El canal de QEMU Guest Agent no está disponible en esta VM.":
        "Der QEMU-Guest-Agent-Kanal ist in dieser VM nicht verfügbar.",
    "El Guest Agent del invitado no respondió en {0} s (no está instalado o no se está ejecutando).":
        "Der Gast-Guest-Agent hat nicht innerhalb von {0} s geantwortet (nicht installiert oder nicht ausgeführt).",
    "Montaje automático": "Automatisches Einhängen",
    "La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n{0}\n\nComprueba que qemu-guest-agent esté instalado y ejecutándose en el guest (pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.":
        "Die VM wurde gestartet, aber das automatische Einhängen konnte im Betriebssystem nicht konfiguriert werden.\n\n{0}\n\nStelle sicher, dass qemu-guest-agent im Gast installiert ist und läuft (Reiter Guest Tools). Nach der Installation erfolgt das Einhängen beim nächsten VM-Start automatisch.",
    "La carpeta compartida VirtioFS ya está conectada a la VM.\n\nEn Linux el dispositivo debe montarse dentro del guest. En un LiveCD no es posible hacerlo de forma persistente desde el host sin un agente instalado en el guest.\n\nComando(s):\n\n":
        "Der gemeinsame VirtioFS-Ordner ist bereits mit der VM verbunden.\n\nUnter Linux muss das Gerät im Gast eingehängt werden. Bei einer LiveCD ist dies ohne im Gast installierten Agenten nicht persistent vom Host aus möglich.\n\nBefehl(e):\n\n",
    "\n\nEn una instalación Linux permanente podremos añadir automontaje mediante fstab/systemd en una versión posterior.":
        "\n\nBei einer permanenten Linux-Installation können wir in einer späteren Version Automount über fstab/systemd hinzufügen.",
    "Carpeta compartida lista": "Gemeinsamer Ordner bereit",
    "Carpeta:\n{0}": "Ordner:\n{0}",
    "Generando ISO de Guest Tools…": "Guest-Tools-ISO wird erstellt…",
    "ISO creada.": "ISO erstellt.",
    "ISO disponible: {0}": "ISO verfügbar: {0}",
    "Crear ISO de Guest Tools": "Guest-Tools-ISO erstellen",
    "No se pudo crear la ISO.\n\n{0}":
        "Die ISO konnte nicht erstellt werden.\n\n{0}",
    "La ISO se guarda en la carpeta GuestTools.":
        "Die ISO wird im Ordner GuestTools gespeichert.",
    "Selecciona (o crea) una VM primero.":
        "Wähle (oder erstelle) zuerst eine VM.",
    "Creando ISO de Guest Tools…": "Guest-Tools-ISO wird erstellt…",
    "Guest Tools — Adjuntar a la VM": "Guest Tools — An VM anhängen",
    "No se pudo crear ni adjuntar la ISO.\n\n{0}":
        "Die ISO konnte weder erstellt noch angehängt werden.\n\n{0}",
    "Se creará la ISO y se adjuntará como CD/DVD a esta VM.":
        "Die ISO wird erstellt und als CD/DVD an diese VM angehängt.",
    "Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD.":
        "Diese VM hat die Guest-Tools-ISO bereits als CD/DVD angehängt.",
    "ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\nEn el próximo arranque, dentro del guest: monta la unidad y ejecuta\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).":
        "Guest-Tools-ISO als CD/DVD an diese VM angehängt.\n\nBeim nächsten Start im Gast: Laufwerk einhängen und\nINSTALL-LINUX.SH (mit sudo) oder INSTALL-WINDOWS.CMD (als Administrator) ausführen.",
    "No se pudo adjuntar la ISO.\n\n{0}":
        "Die ISO konnte nicht angehängt werden.\n\n{0}",
    "Estado: canal no disponible. Enciende la VM con Guest Agent activado.":
        "Status: Kanal nicht verfügbar. Starte die VM mit aktiviertem Guest Agent.",
    "Estado: consultando al Guest Agent...":
        "Status: Guest Agent wird abgefragt...",
    "Estado: sin respuesta del guest agent ({0}).":
        "Status: Keine Antwort vom Guest Agent ({0}).",
    "desconocida": "unbekannt",
    "Estado: QEMU Guest Agent responde correctamente (v{0}).":
        "Status: QEMU Guest Agent antwortet ordnungsgemäß (v{0}).",
    "Estado: QGA respondió con un error: {0}":
        "Status: QGA hat mit einem Fehler geantwortet: {0}",
    "Estado: canal QGA presente; pulsa Probar conexión.":
        "Status: QGA-Kanal vorhanden; drücke Verbindung testen.",
    "Estado: canal QGA no activo en este momento.":
        "Status: QGA-Kanal derzeit nicht aktiv.",
    "Manual": "Manuell",
    "Automático al iniciar SO": "Automatisch beim OS-Start",
    "Automático bajo demanda": "Automatisch auf Anforderung",
    "Solo lectura": "Nur Lesen",
    "Lectura / escritura": "Lesen / Schreiben",
    "Carpeta compartida": "Gemeinsamer Ordner",
    "Seleccionar carpeta del host": "Host-Ordner auswählen",
    "Carpeta del host:": "Host-Ordner:",
    "Etiqueta / guest:": "Bezeichnung / Gast:",
    "Método:": "Methode:",
    "Automático": "Automatisch",
    "Montaje en el guest:": "Einhängen im Gast:",
    "Acceso:": "Zugriff:",
    "La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.":
        "Die Einhänge-Politik ist für alle Betriebssysteme gleich: Manuell, Automatisch beim OS-Start oder Automatisch auf Anforderung. Der tatsächliche Einhänge-Mechanismus passt sich an das Gast-Betriebssystem und dessen Integrationskomponenten an. Bei einer LiveCD kann das persistente Einhängen normalerweise nicht vom Host aus konfiguriert werden.",
    "La carpeta del host no existe o no es un directorio.":
        "Der Host-Ordner existiert nicht oder ist kein Verzeichnis.",
    "Desactivado": "Deaktiviert",
    "Host → SO invitado": "Host → Gastsystem",
    "SO invitado → Host": "Gastsystem → Host",
    "Bidireccional": "Bidirektional",
    "No se añadirá ningún canal de clipboard.":
        "Es wird kein Zwischenablage-Kanal hinzugefügt.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK: bidirektional. Erfordert spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS: Zwischenablage-Integration ausstehend.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Wähle eine VM, um die verfügbare Integration zu prüfen.",
    "Se activará automáticamente al iniciar la VM.":
        "Wird beim Start der VM automatisch aktiviert.",
    "No se activa.": "Wird nicht aktiviert.",
    "Configuración actual: {0}. {1} {2}":
        "Aktuelle Konfiguration: {0}. {1} {2}",
    "Configuración del clipboard guardada para esta VM.":
        "Zwischenablage-Konfiguration für diese VM gespeichert.",
    "Compartir": "Freigabe",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Konfiguration gespeichert. Wird beim nächsten Start angewendet.",
}
