# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2e-2a: Comparticion + Ayuda + Notas por SO.

Cubre: seccion Comparticion (intro, Dependencias del host, tablas
de Carpetas compartidas, Guest Tools, Clipboard) + Panel de Ayuda
+ Notas contextuales por SO.

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Panel de Ayuda
    # ================================================================
    "<h2>Ayuda de Virtual.Machine</h2>": "<h2>Hilfe zu Virtual.Machine</h2>",
    "Guia completa de la consola (VNC / SPICE)":
        "Vollständige Konsolenanleitung (VNC / SPICE)",
    "Guía completa de la consola (VNC / SPICE)":
        "Vollständige Konsolenanleitung (VNC / SPICE)",

    # ================================================================
    # Notas por SO (bloque Android; el resto de notas ya estan en .md)
    # ================================================================
    "<b>ℹ️ Notas sobre Android en QEMU/KVM</b>":
        "<b>ℹ️ Hinweise zu Android unter QEMU/KVM</b>",

    # ================================================================
    # Comparticion - intro + Dependencias del host
    # ================================================================
    "Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).":
        "Host ↔ Gast-Integration. Hier werden gemeinsame Ordner und die Zwischenablage konfiguriert.",
    "Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.":
        "Gibt Host-Verzeichnisse für den Gast frei. Automatisch verwendet VirtioFS unter Linux, wenn virtiofsd verfügbar ist, 9p als Ausweichlösung und SMB für Windows/macOS. Nur-Lesen verhindert, dass der Gast Host-Dateien verändert.",
    "Dependencias del host": "Host-Abhängigkeiten",
    "VirtioFS: SIN COMPROBAR": "VirtioFS: UNGEPRÜFT",
    "9p: SIN COMPROBAR": "9p: UNGEPRÜFT",
    "SMB: SIN COMPROBAR": "SMB: UNGEPRÜFT",
    "9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.":
        "9p ist Teil von QEMU und erfordert normalerweise kein zusätzliches Paket auf dem Host. VirtioFS benötigt virtiofsd und SMB benötigt Samba/smbd.",
    "🛠️ Instalar faltantes": "🛠️ Fehlende installieren",
    "Host": "Host",
    "Guest / etiqueta": "Gast / Bezeichnung",
    "Método": "Methode",
    "Montaje en el guest": "Einhängen im Gast",
    "Acceso": "Zugriff",
    "➕ Agregar": "➕ Hinzufügen",
    "✏ Modificar": "✏ Ändern",
    "💾 Guardar": "💾 Speichern",

    # ================================================================
    # Guest Tools
    # ================================================================
    "Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.":
        "Guest Tools bündelt die Integration des Gastsystems: QEMU Guest Agent, VirtIO-Treiber und unter Windows SPICE-Komponenten. Die ISO kann als CD/DVD in jede VM eingelegt werden.",
    "QEMU Guest Agent": "QEMU Guest Agent",
    "Activar canal QEMU Guest Agent al iniciar la VM":
        "QEMU-Guest-Agent-Kanal beim VM-Start aktivieren",
    "Canal:": "Kanal:",
    "Estado: no comprobado": "Status: nicht geprüft",
    "🔎 Probar conexión": "🔎 Verbindung testen",
    "💿 Crear / actualizar ISO Guest Tools":
        "💿 Guest-Tools-ISO erstellen / aktualisieren",
    "🧰 Adjuntar a esta VM": "🧰 An diese VM anhängen",
    "Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.":
        "Erstellt die ISO, falls sie fehlt, und hängt sie als CD/DVD an die ausgewählte VM an, in einem Schritt.",
    "📂 Abrir carpeta de Guest Tools": "📂 Guest-Tools-Ordner öffnen",
    "Acciones:": "Aktionen:",
    "Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.":
        "Linux: Installiere qemu-guest-agent von dieser ISO oder aus dem Paketmanager. Windows: INSTALL-WINDOWS.CMD lädt die VirtIO Guest Tools und SPICE Guest Tools aus offiziellen Quellen herunter und installiert sie. Danach den Gast neu starten.",

    # ================================================================
    # Clipboard
    # ================================================================
    "Compartir clipboard": "Zwischenablage teilen",
    "Desactivado": "Deaktiviert",
    "Host → SO invitado": "Host → Gastsystem",
    "SO invitado → Host": "Gastsystem → Host",
    "Bidireccional": "Bidirektional",
    "Dirección:": "Richtung:",
    "Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.":
        "Linux und Windows: Es werden QEMU vdagent + VirtIO/SPICE-Kanal und GTK für die bidirektionale Zwischenablage verwendet. Der Gast muss spice-vdagent (Linux) oder SPICE Guest Tools (Windows) haben. macOS wird in einer speziellen Phase getestet.",
    "💾 Guardar configuración": "💾 Konfiguration speichern",
    "Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.":
        "Konfiguration pro VM. Der konkrete Mechanismus wird je nach Gastbetriebssystem und dessen Integrationsunterstützung gewählt.",
    "Compartir Carpetas": "Ordner teilen",
    "Clipboard": "Zwischenablage",
    "Compartir": "Freigabe",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Konfiguration gespeichert. Wird beim nächsten Start angewendet.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Wähle eine VM, um die verfügbare Integration zu prüfen.",
    "Se activará automáticamente al iniciar la VM.":
        "Wird beim Start der VM automatisch aktiviert.",
    "No se activa.": "Wird nicht aktiviert.",
    "Configuración actual: {0}. {1} {2}":
        "Aktuelle Konfiguration: {0}. {1} {2}",
    "No se añadirá ningún canal de clipboard.":
        "Es wird kein Zwischenablage-Kanal hinzugefügt.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK: bidirektional. Erfordert spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS: Zwischenablage-Integration ausstehend.",
    "Configuración del clipboard guardada para esta VM.":
        "Zwischenablage-Konfiguration für diese VM gespeichert.",
}
