# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2e-2c: USB passthrough + Medios.

Cubre: errores de preparacion USB, permisos USB del host, menu
Medios (unidades opticas + dispositivos USB), tabla passthrough
(encabezados + estados) y dialogos de conexion/desconexion USB en
caliente.

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # USB: errores de preparacion
    # ================================================================
    "No existe {0}. El número Device puede haber cambiado; "
    "vuelve a detectar USB.":
        "{0} existiert nicht. Die Gerätenummer kann sich geändert haben; "
        "erkenne USB erneut.",
    "Sin acceso de lectura/escritura a {0}.":
        "Kein Lese-/Schreibzugriff auf {0}.",
    "No se encontró 'pkexec'. No puedo solicitar permisos "
    "administrativos automáticamente.":
        "'pkexec' wurde nicht gefunden. Administrative Rechte können "
        "nicht automatisch angefordert werden.",
    "No se pudo ejecutar la acción administrativa ({0}): {1}":
        "Die administrative Aktion ({0}) konnte nicht ausgeführt werden: {1}",
    "No se pudo realizar la acción administrativa ({0}). {1}":
        "Die administrative Aktion ({0}) konnte nicht durchgeführt werden. {1}",
    "No existe el nodo USB actual {0}; el dispositivo "
    "pudo cambiar de dirección.":
        "Der aktuelle USB-Knoten {0} existiert nicht; das Gerät "
        "kann seine Adresse geändert haben.",
    "(desconocido)": "(unbekannt)",
    "dar acceso temporal al dispositivo USB":
        "temporären Zugriff auf das USB-Gerät gewähren",
    "No pude desmontar automáticamente el almacenamiento USB:\n"
    "{0}\n\n{1}":
        "Der USB-Speicher konnte nicht automatisch ausgehängt werden:\n"
        "{0}\n\n{1}",
    "El USB sigue sin acceso después de preparar el dispositivo: {0}":
        "Der USB hat nach der Vorbereitung weiterhin keinen Zugriff: {0}",
    "USB {0} | nodo: {1} | acceso usuario: {2} | {3}":
        "USB {0} | Knoten: {1} | Benutzerzugriff: {2} | {3}",
    "NO": "NEIN",
    "no se pudo leer ({0})": "konnte nicht gelesen werden ({0})",
    "error al comprobar: {0}": "Fehler beim Prüfen: {0}",

    # ================================================================
    # Permisos USB
    # ================================================================
    "\u2705 Permisos USB: OK ({0}). El passthrough en caliente "
    "no pedirá contraseña.":
        "\u2705 USB-Berechtigungen: OK ({0}). Hotplug-Passthrough "
        "fragt nicht nach einem Passwort.",
    "Los permisos USB ya están configurados.\n"
    "Si quieres desinstalarlos, borra:\n"
    "{0}":
        "Die USB-Berechtigungen sind bereits konfiguriert.\n"
        "Zum Deinstallieren lösche:\n"
        "{0}",
    "\u26a0 Permisos USB: {0}. El passthrough en caliente "
    "pedirá contraseña cada vez.":
        "\u26a0 USB-Berechtigungen: {0}. Hotplug-Passthrough "
        "fragt jedes Mal nach einem Passwort.",
    "Permisos USB": "USB-Berechtigungen",
    "No se encontró 'pkexec'. Instálalo (paquete 'polkit') para "
    "que la aplicación pueda solicitar permisos administrativos "
    "de forma gráfica.":
        "'pkexec' wurde nicht gefunden. Installiere es (Paket 'polkit'), "
        "damit die Anwendung administrative Rechte grafisch anfordern kann.",
    "No se encontró 'udevadm'. Este sistema parece no usar udev "
    "para gestionar dispositivos USB. Aplica los permisos "
    "manualmente según tu distribución.":
        "'udevadm' wurde nicht gefunden. Dieses System verwendet offenbar "
        "kein udev zur Verwaltung von USB-Geräten. Wende die Berechtigungen "
        "manuell gemäß deiner Distribution an.",
    "Configurar permisos USB": "USB-Berechtigungen konfigurieren",
    "La operación tardó demasiado. Vuelve a intentarlo.":
        "Der Vorgang hat zu lange gedauert. Bitte erneut versuchen.",

    # ================================================================
    # Passthrough: parrafo + tabla
    # ================================================================
    "Usar": "Verwenden",
    "IOMMU / Driver": "IOMMU / Treiber",
    "\U0001f504 Detectar dispositivos": "\U0001f504 Geräte erkennen",
    "\U0001f4be Guardar selección": "\U0001f4be Auswahl speichern",
    "\U0001f50c Conectar USB en caliente": "\U0001f50c USB im laufenden Betrieb verbinden",
    "\u23cf Desconectar USB": "\u23cf USB trennen",
    "Grupo {0}": "Gruppe {0}",
    "Sin grupo IOMMU": "Keine IOMMU-Gruppe",
    " \u2022 {0}": " \u2022 {0}",
    "\u26a0 Revisar": "\u26a0 Prüfen",
    "\u2713 Acceso OK": "\u2713 Zugriff OK",
    "\u26a0 Revisar acceso": "\u26a0 Zugriff prüfen",

    # ================================================================
    # Permisos USB del host (seccion)
    # ================================================================
    "Para poder pasar memorias o discos USB a la VM sin pedir contraseña cada vez, el sistema necesita una regla udev que conceda acceso al usuario activo. Puedes instalarla aquí con un clic; solo se aplica a esta categoría de dispositivos.":
        "Um USB-Sticks oder -Festplatten ohne Passwortabfrage an die VM durchzureichen, benötigt das System eine udev-Regel, die dem aktiven Benutzer Zugriff gewährt. Du kannst sie hier mit einem Klick installieren; sie gilt nur für diese Gerätekategorie.",
    "\U0001f504 Comprobar": "\U0001f504 Prüfen",
    "\U0001f527 Configurar permisos USB": "\U0001f527 USB-Berechtigungen konfigurieren",
    "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\n"
    "que permite el acceso a los dispositivos USB al usuario activo.\n"
    "Solo se toca este archivo; el resto de la configuración USB\n"
    "del sistema no se modifica.":
        "Erstellt /etc/udev/rules.d/50-vm-manager-usb.rules mit der Regel,\n"
        "die dem aktiven Benutzer Zugriff auf USB-Geräte erlaubt.\n"
        "Nur diese Datei wird angefasst; der Rest der USB-Konfiguration\n"
        "des Systems bleibt unverändert.",

    # ================================================================
    # Menu Medios: CD/DVD + USB
    # ================================================================
    "Dispositivo USB inválido.": "Ungültiges USB-Gerät.",
    "\U0001f4c0 Unidades ópticas": "\U0001f4c0 Optische Laufwerke",
    "      (Sin unidades CD/DVD)": "      (Keine CD/DVD-Laufwerke)",
    "\U0001f310 descargar instalador al iniciar":
        "\U0001f310 Installer beim Start herunterladen",
    "\U0001f310 descargar Recovery al iniciar":
        "\U0001f310 Recovery beim Start herunterladen",
    "   \U0001f4c0 {0} \u2014 {1}": "   \U0001f4c0 {0} \u2014 {1}",
    "\U0001f4c2 Cambiar medio\u2026": "\U0001f4c2 Medium wechseln\u2026",
    "\u23cf Expulsar medio": "\u23cf Medium auswerfen",
    "\U0001f50c Dispositivos USB": "\U0001f50c USB-Geräte",
    "      (La VM debe estar encendida para conectarlos)":
        "      (Die VM muss laufen, um sie zu verbinden)",
    "      Error al detectar USB: {0}":
        "      Fehler bei der USB-Erkennung: {0}",
    "      (No hay dispositivos USB detectados)":
        "      (Keine USB-Geräte erkannt)",
    "conectado a la VM": "mit der VM verbunden",
    "disponible en el host": "auf dem Host verfügbar",
    "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
    "Estado: {5}\n\n{6}":
        "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Gerät {4}\n"
        "Status: {5}\n\n{6}",
    "Clic para DESCONECTAR de la VM":
        "Klicken, um von der VM zu TRENNEN",
    "Clic para CONECTAR a la VM":
        "Klicken, um mit der VM zu VERBINDEN",
    "(Selecciona una VM primero)": "(Zuerst eine VM auswählen)",
    "\U0001f4bf Medios de '{0}'": "\U0001f4bf Medien von '{0}'",
    "\U0001f504 Refrescar": "\U0001f504 Aktualisieren",
    "\u2699 Gestionar USB en Passthrough\u2026":
        "\u2699 USB im Passthrough verwalten\u2026",

    # ================================================================
    # Passthrough USB: dialogos
    # ================================================================
    "Passthrough: teclado o ratón del host":
        "Passthrough: Tastatur oder Maus des Hosts",
    "Passthrough USB": "USB-Passthrough",
    "Selecciona un dispositivo USB.": "Ein USB-Gerät auswählen.",
    "La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.":
        "Die VM läuft nicht; verwende Auswahl speichern, um es beim nächsten Start anzuhängen.",
    "Dispositivo USB conectado en caliente a la VM.\n\n"
    "Nota: el host debe permitir acceso a /dev/bus/usb y el "
    "dispositivo no debería estar siendo usado por el sistema "
    "anfitrión.":
        "USB-Gerät im laufenden Betrieb mit der VM verbunden.\n\n"
        "Hinweis: Der Host muss den Zugriff auf /dev/bus/usb erlauben "
        "und das Gerät darf nicht vom Wirtssystem verwendet werden.",
    "Error al conectar USB": "Fehler beim Verbinden des USB",
    "La VM no está encendida.": "Die VM läuft nicht.",
    "Solicitud de desconexión USB enviada a QEMU.":
        "USB-Trennanforderung an QEMU gesendet.",
    "Error al desconectar USB": "Fehler beim Trennen des USB",
}
