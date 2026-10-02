# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2e-1.

Cubre: sidebar de Configuracion VM (Passthrough, Comparticion),
Configuracion Host completa: subtitulo, estado de virtualizacion,
Apariencia (selector de tema), Atajos de teclado (dialogo completo)
y API REST local (UI + dialogos).

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 2e-1: sidebar Configuracion VM
    # ================================================================
    "Passthrough": "Passthrough",
    "Compartición": "Freigabe",

    # ================================================================
    # Tanda 2e-2: Configuracion Host (subtitulo + estado virtualizacion)
    # ================================================================
    "Ajustes y diagnostico del sistema anfitrion. Nada de esta seccion se guarda con la VM: aplica a todo el equipo.":
        "Einstellungen und Diagnose des Wirtssystems. Nichts aus diesem Bereich wird mit der VM gespeichert: es gilt für den gesamten Rechner.",
    "Estado del sistema de virtualización": "Status des Virtualisierungssystems",
    "Distribución: comprobando...": "Distribution: wird geprüft...",
    "Gestor de paquetes: comprobando...": "Paketmanager: wird geprüft...",
    "🔄 Comprobar dependencias": "🔄 Abhängigkeiten prüfen",
    "🔄️ Comprobar dependencias": "🔄️ Abhängigkeiten prüfen",
    "🛠 Comprobar/Reparar dependencias": "🛠 Abhängigkeiten prüfen/reparieren",
    "🛠️ Comprobar/Reparar dependencias": "🛠️ Abhängigkeiten prüfen/reparieren",

    # ================================================================
    # Tanda 2e-2 full: Apariencia (selector de tema)
    # ================================================================
    "Apariencia": "Erscheinungsbild",
    "Sistema (predeterminado)": "System (Standard)",
    "Claro": "Hell",
    "Oscuro": "Dunkel",
    "Tema visual de la aplicacion.\n"
    "  - Sistema: usa el estilo y la paleta del escritorio.\n"
    "  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n"
    "    propia, independiente del SO.\n"
    "\n"
    "Al elegir Claro u Oscuro, la app cambia el estilo de Qt a\n"
    "Fusion. Al volver a Sistema, se restaura el estilo original\n"
    "del escritorio (Breeze, Adwaita, etc.).":
        "Visuelles Thema der Anwendung.\n"
        "  - System: verwendet Stil und Palette des Desktops.\n"
        "  - Hell / Dunkel: erzwingt den Fusion-Stil mit eigener\n"
        "    Palette, unabhängig vom Betriebssystem.\n"
        "\n"
        "Bei Auswahl von Hell oder Dunkel wechselt die App den Qt-Stil\n"
        "auf Fusion. Bei Rückkehr zu System wird der ursprüngliche\n"
        "Desktop-Stil wiederhergestellt (Breeze, Adwaita usw.).",
    "Tema:": "Thema:",
    "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\n"
    "reiniciar la app para que TODOS los widgets se repinten con los\n"
    "colores nuevos (depende del estilo del escritorio).":
        "Beim Wechsel zwischen 'System' und 'Hell/Dunkel' kann ein\n"
        "Neustart der App erforderlich sein, damit ALLE Widgets mit\n"
        "den neuen Farben neu gezeichnet werden (abhängig vom Desktop-Stil).",

    # ================================================================
    # Tanda 2e-2 full: Atajos de teclado
    # ================================================================
    "Atajos de teclado": "Tastenkürzel",
    "Reasigna los atajos globales de la aplicacion. Los cambios\n"
    "se aplican al instante, sin reiniciar.":
        "Weist die globalen Tastenkürzel der Anwendung neu zu. Änderungen\n"
        "werden sofort übernommen, ohne Neustart.",
    "Configurar atajos...": "Tastenkürzel konfigurieren...",
    "Configurar atajos de teclado": "Tastenkürzel konfigurieren",
    "Haz clic en <b>Cambiar...</b> para capturar una nueva\n"
    "combinacion de teclas. Pulsa <b>Escape</b> durante la\n"
    "captura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\n"
    "para deshabilitar un atajo.":
        "Klicke auf <b>Ändern...</b>, um eine neue Tastenkombination\n"
        "aufzunehmen. Drücke während der Aufnahme <b>Escape</b>,\n"
        "um sie abzubrechen. Verwende <b>Entf</b> oder <b>Rücktaste</b>,\n"
        "um ein Tastenkürzel zu deaktivieren.",
    "Accion": "Aktion",
    "Atajo": "Tastenkürzel",
    "Cambiar...": "Ändern...",
    "Restaurar todos por defecto": "Alle auf Standard zurücksetzen",
    "(sin atajo)": "(kein Tastenkürzel)",
    "Conflicto de atajos": "Tastenkürzel-Konflikt",
    "El atajo {0} ya esta asignado a:\n\n  {1}\n\n"
    "Elige otro o cambia primero el otro atajo.":
        "Das Tastenkürzel {0} ist bereits zugewiesen an:\n\n  {1}\n\n"
        "Wähle ein anderes oder ändere zuerst das andere Tastenkürzel.",
    "Restaurar atajos": "Tastenkürzel zurücksetzen",
    "¿Restaurar los cuatro atajos a sus valores por defecto?":
        "Alle vier Tastenkürzel auf ihre Standardwerte zurücksetzen?",
    "Pulsa la nueva combinacion": "Neue Kombination drücken",
    "<b>Pulsa la combinacion de teclas que quieras asignar.</b>":
        "<b>Drücke die Tastenkombination, die du zuweisen möchtest.</b>",
    "Esperando pulsacion...\n\n"
    "Escape cancela. Supr o Retroceso deshabilita el atajo.":
        "Warte auf Tastendruck...\n\n"
        "Escape bricht ab. Entf oder Rücktaste deaktiviert das Tastenkürzel.",
    "Atajo actual: <b>{0}</b>": "Aktuelles Tastenkürzel: <b>{0}</b>",
    "Solo has pulsado un modificador. Anade una tecla normal.\n\n"
    "Escape cancela. Supr o Retroceso deshabilita el atajo.":
        "Du hast nur eine Modifikatortaste gedrückt. Füge eine normale Taste hinzu.\n\n"
        "Escape bricht ab. Entf oder Rücktaste deaktiviert das Tastenkürzel.",
    "Abrir menu de Medios (CD/DVD + USB)":
        "Medienmenü öffnen (CD/DVD + USB)",
    "Reconectar el widget VNC": "VNC-Widget neu verbinden",
    "Alternar Consola Grafica": "Grafische Konsole umschalten",
    "Entrar / salir del modo presentacion":
        "Präsentationsmodus betreten / verlassen",

    # ================================================================
    # Tanda 2e-2 full: API REST local
    # ================================================================
    "API REST local": "Lokale REST-API",
    "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar VMs "
    "desde scripts, dashboards o CI. Todo se autentica con un token "
    "local; <b>no</b> es accesible desde la red.":
        "Stellt eine minimale HTTP-API auf <b>127.0.0.1</b> bereit, um VMs "
        "aus Skripten, Dashboards oder CI zu steuern. Alles wird mit einem "
        "lokalen Token authentifiziert; ist <b>nicht</b> aus dem Netzwerk erreichbar.",
    "Activar API REST local": "Lokale REST-API aktivieren",
    "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\n"
    "Cambios requieren apagar y volver a encender la API.":
        "TCP-Port, auf dem der Server lauscht. Nur 127.0.0.1.\n"
        "Änderungen erfordern ein Aus- und Wiedereinschalten der API.",
    "Puerto:": "Port:",
    "URL:": "URL:",
    "Token:": "Token:",
    "Mostrar / ocultar el token": "Token anzeigen / verbergen",
    "Copiar": "Kopieren",
    "Regenerar": "Neu generieren",
    "Genera un token nuevo. Las peticiones con el token anterior\n"
    "dejarán de funcionar.":
        "Generiert ein neues Token. Anfragen mit dem vorherigen Token\n"
        "funktionieren nicht mehr.",
    "Ver peticiones recientes": "Letzte Anfragen anzeigen",
    "Ejemplo de uso desde terminal:<br>"
    "<code>curl -H 'X-API-Token: &lt;tu-token&gt;' http://127.0.0.1:8730/api/vms</code>":
        "Beispiel für die Verwendung im Terminal:<br>"
        "<code>curl -H 'X-API-Token: &lt;dein-token&gt;' http://127.0.0.1:8730/api/vms</code>",
    "Detenida": "Gestoppt",
    "Activa": "Aktiv",
    "API REST": "REST-API",
    "No se pudo arrancar la API REST.\n\n{0}":
        "Die REST-API konnte nicht gestartet werden.\n\n{0}",
    "Regenerar token": "Token neu generieren",
    "Se generará un token nuevo y el anterior dejará de funcionar.\n\n"
    "¿Continuar?":
        "Es wird ein neues Token generiert und das vorherige funktioniert nicht mehr.\n\n"
        "Fortfahren?",
    "Se regeneró el token pero no se pudo reiniciar la API:\n\n{0}":
        "Das Token wurde neu generiert, aber die API konnte nicht neu gestartet werden:\n\n{0}",
    "Peticiones recientes a la API": "Letzte Anfragen an die API",
    "Últimas peticiones atendidas por la API. Se conservan las 50 más recientes.":
        "Zuletzt von der API bediente Anfragen. Die letzten 50 werden aufbewahrt.",
    "(sin peticiones todavía)": "(noch keine Anfragen)",
    "<b style='color:#2e7d32;'>Activa</b> — {0} peticiones desde el arranque":
        "<b style='color:#2e7d32;'>Aktiv</b> — {0} Anfragen seit dem Start",
    "<b style='color:#888;'>Detenida</b>":
        "<b style='color:#888;'>Gestoppt</b>",

    # ================================================================
    # Tanda 2e-2 full: Aviso cambio de tema
    # ================================================================
    "Cambio de tema": "Themenwechsel",
    "Se ha cambiado el tema.\n\n"
    "Algunos estilos del escritorio (Kvantum en KDE, por\n"
    "ejemplo) pueden no repintar todos los widgets hasta\n"
    "reiniciar la aplicacion.\n\n"
    "¿Quieres reiniciar ahora para asegurar que todos los\n"
    "elementos se vean correctamente?":
        "Das Thema wurde geändert.\n\n"
        "Einige Desktop-Stile (z. B. Kvantum unter KDE) zeichnen\n"
        "möglicherweise nicht alle Widgets neu, bis die Anwendung\n"
        "neu gestartet wird.\n\n"
        "Jetzt neu starten, damit alle Elemente korrekt angezeigt werden?",
}
