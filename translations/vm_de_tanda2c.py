# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2c.

Cubre: panel derecho dinamico (estados de la VM, resumen de la
configuracion en "Informacion general", lista de dispositivos,
Notas: Si/No) y mensajes auxiliares del panel.

Se fusiona con vm_de.py y vm_de_tanda2b.py.
"""

TRANSLATIONS = {

    # ================================================================
    # Tanda 2c: panel derecho - estados y resumen dinamico
    # ================================================================
    "No hay una máquina virtual seleccionada.\n\n"
    "Pulsa 'Nueva máquina virtual' para comenzar.":
        "Keine virtuelle Maschine ausgewählt.\n\n"
        "Drücke 'Neue virtuelle Maschine', um zu beginnen.",
    "Configura el sistema en la pestaña 'Configuración'.":
        "Konfiguriere das System im Reiter 'Konfiguration'.",
    "● Ejecutándose": "● Wird ausgeführt",
    "● Pausada": "● Pausiert",
    "● Apagada": "● Ausgeschaltet",
    "Notas:": "Notizen:",
    "Sí": "Ja",
    "No": "Nein",
    "Red 1": "Netzwerk 1",
    "Sin adaptadores configurados": "Keine Adapter konfiguriert",
    "Disco Duro": "Festplatte",
    "CD/DVD": "CD/DVD",
    "vacío": "leer",
    "Sin dispositivos": "Keine Geräte",
    "Sistema:": "System:",
    "CPU:": "CPU:",
    "RAM:": "RAM:",
    "núcleos": "Kerne",
    "Firmware:": "Firmware:",
    "Secure Boot:": "Secure Boot:",
    "TPM:": "TPM:",
    "Gráficos:": "Grafik:",
    "Audio:": "Audio:",
    "Red:": "Netzwerk:",
    "Almacenamiento:": "Speicher:",
    "Orden de arranque:": "Startreihenfolge:",
    "Ubicación:": "Speicherort:",
    "VM nueva: todavía no se ha guardado una configuración.":
        "Neue VM: Es wurde noch keine Konfiguration gespeichert.",
    "Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio.":
        "Konfiguriere die VM im Reiter 'Konfiguration' und drücke die Start-Schaltfläche.",
    "Usa 'Configuración' para modificar hardware y opciones avanzadas.":
        "Verwende 'Konfiguration', um Hardware und erweiterte Optionen zu ändern.",

    # --- estados adicionales de botones del Resumen (dinamicos) ---
    "● Configurada": "● Konfiguriert",
    "● Error": "● Fehler",

    # --- valores dinamicos de la barra de estado/panel ---
    "Sin VM seleccionada.": "Keine VM ausgewählt.",
    "Sin VM seleccionada": "Keine VM ausgewählt",
    "Primero selecciona una máquina virtual existente.":
        "Wähle zuerst eine vorhandene virtuelle Maschine aus.",

    # --- terminos auxiliares del panel (info general) ---
    "Estado:": "Status:",
    "Grupo:": "Gruppe:",
    "(sin grupo)": "(ohne Gruppe)",
    "(Sin color)": "(Ohne Farbe)",
    "Sin color": "Ohne Farbe",
    "vacía": "leer",
    "No configurado": "Nicht konfiguriert",
    "Configurado": "Konfiguriert",
}
