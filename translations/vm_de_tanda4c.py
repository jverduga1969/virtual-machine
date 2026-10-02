# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 4c: cierre.

Cubre las 68 cadenas que quedaban pendientes tras 4a y 4b:
  - TaskProgressDialog (task_progress.py)
  - Cadenas duplicadas con bytes tipograficos distintos (comillas
    curvas U+2018/U+2019, emoji VS16).
  - install_flow_mixin.py (preflight, mensajes por SO, USB).
  - mac_recovery_mixin.py (descarga del BaseSystem.dmg).
  - Algunas cadenas sueltas del arbol de dispositivos.

IMPORTANTE: los source con comillas tipograficas ('...') DEBEN
conservar esas comillas exactas; no sustituirlas por '...'.
"""

TRANSLATIONS = {

    # ================================================================
    # task_progress.py
    # ================================================================
    "Iniciando…": "Wird gestartet…",
    "Completado.": "Abgeschlossen.",
    "Error:": "Fehler:",
    "La tarea falló.": "Die Aufgabe ist fehlgeschlagen.",
    "Cancelando…": "Wird abgebrochen…",
    "Cancelando, esperando al trabajador…":
        "Wird abgebrochen, warte auf den Worker…",

    # ================================================================
    # Duplicados con bytes tipograficos / emoji VS16
    # (comillas curvas U+2018 y U+2019 en 'Desenlazar')
    # ================================================================
    "⚠ Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con ‘🧬 Desenlazar’ en la pestaña Resumen.":
        "⚠ Diese VM ist ein verknüpfter Klon (QCOW2-Backing-Datei). Vollständige Snapshots (RAM + Geräte) können in QEMU mit Backing-Datei nicht wiederhergestellt werden; die App verwendet stets NUR-DISK-Snapshots. Für vollständige Snapshots zuerst den Klon mit ‘🧬 Entkoppeln’ im Reiter Übersicht lösen.",
    "↺ Ajustar": "↺ Anpassen",
    "Permisos USB del host": "USB-Berechtigungen des Hosts",
    "Idioma de la interfaz.": "Sprache der Benutzeroberfläche.",
    "No hay ninguna máquina virtual seleccionada.":
        "Es ist keine virtuelle Maschine ausgewählt.",
    "La VM '{0}' no está corriendo. Enciéndela antes de entrar en modo presentación.":
        "Die VM '{0}' läuft nicht. Starte sie, bevor du den Präsentationsmodus betrittst.",
    "La Consola Gráfica no está disponible en este sistema (falta el widget VNC embebido).":
        "Die Grafische Konsole ist auf diesem System nicht verfügbar (das eingebettete VNC-Widget fehlt).",
    "No se pudo comprobar el estado de la VM: {0}":
        "Der VM-Status konnte nicht überprüft werden: {0}",
    "Modo presentación": "Präsentationsmodus",
    "🎬 Salir de presentación": "🎬 Präsentation beenden",
    "Salir del modo presentación y restaurar la vista normal.\nTambién puedes pulsar F11 o Escape.":
        "Den Präsentationsmodus verlassen und die normale Ansicht wiederherstellen.\nDu kannst auch F11 oder Escape drücken.",

    # ================================================================
    # install_flow_mixin.py: mensajes por SO
    # ================================================================
    "Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.":
        "Verwende für macOS 'System Recovery herunterladen'. Apple liefert den vollständigen Installer als Anwendung; der OSX-KVM-Recovery-Workflow ist die in diesem Manager integrierte Methode.",
    "Android-x86 / Bliss OS no tienen descarga automática. Descarga la ISO desde https://www.android-x86.org/download.html o https://blissos.org/ y selecciónala en Plataforma → Android.":
        "Android-x86 / Bliss OS unterstützen keinen automatischen Download. Lade das ISO von https://www.android-x86.org/download.html oder https://blissos.org/ herunter und wähle es in Plattform → Android aus.",
    "System Recovery de macOS — {0}": "macOS System Recovery — {0}",
    "La imagen se descarga y verifica directamente en la carpeta de la VM.":
        "Das Image wird direkt im VM-Ordner heruntergeladen und überprüft.",
    "Iniciando descarga…": "Download wird gestartet…",
    "Recovery preparado.": "Recovery bereit.",
    "No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.":
        "qemu-system-x86_64 wurde nicht in PATH gefunden. Führe ./run.sh aus (installiert die Systemabhängigkeiten) oder installiere qemu-system-x86 / qemu-kvm.",
    "/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.":
        "/dev/kvm ist nicht verfügbar; QEMU könnte ohne KVM-Beschleunigung funktionieren.",
    "El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.":
        "Der Benutzer hat keine Lese-/Schreibberechtigung auf /dev/kvm.",
    "No se detectó un firmware OVMF conocido para Secure Boot.":
        "Es wurde keine bekannte OVMF-Firmware für Secure Boot erkannt.",
    "El dispositivo de almacenamiento '{0}' apunta a un archivo que ya no existe: {1}":
        "Das Speichergerät '{0}' verweist auf eine Datei, die nicht mehr existiert: {1}",
    "La carpeta compartida '{0}' apunta a una ruta del host que ya no existe: {1}":
        "Der gemeinsame Ordner '{0}' verweist auf einen Host-Pfad, der nicht mehr existiert: {1}",
    "Solo quedan {0} GB libres donde vive esta VM; puede fallar durante el uso.":
        "Nur noch {0} GB frei, wo diese VM liegt; kann während der Nutzung fehlschlagen.",
    "El orden de arranque prioriza el CD/DVD, pero el disco '{0}' ya tiene datos (~{1} GB). Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo.":
        "Die Startreihenfolge priorisiert das CD/DVD, aber die Festplatte '{0}' enthält bereits Daten (~{1} GB). Wenn das System bereits installiert ist, könnte dies eine Neuinstallation statt eines Starts versuchen.",
    "Advertencia": "Warnung",
    "Debe indicar un nombre para la máquina virtual.":
        "Du musst einen Namen für die virtuelle Maschine angeben.",
    'El nombre no puede contener: \\ / : * ? " < > |':
        'Der Name darf nicht enthalten: \\ / : * ? " < > |',
    "La VM ya está corriendo": "Die VM läuft bereits",
    "'{0}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco (dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\nDetén la VM actual antes de volver a iniciarla.":
        "'{0}' hat bereits einen aktiven QEMU-Prozess. Ein erneuter Start kann die Festplatte beschädigen (zwei Prozesse schreiben dieselbe Datei) oder mit den belegten Sockets kollidieren.\n\nStoppe die aktuelle VM, bevor du sie neu startest.",
    "No se puede iniciar la VM": "VM kann nicht gestartet werden",
    "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.":
        "QEMU fehlt auf dem System. Installiere qemu-system-x86 und versuche es erneut.",
    "Revisión previa": "Vorabprüfung",
    "¿Deseas continuar de todos modos?": "Trotzdem fortfahren?",
    "Configuración incompatible": "Inkompatible Konfiguration",
    "Secure Boot requiere UEFI (OVMF).": "Secure Boot erfordert UEFI (OVMF).",
    "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.":
        "TPM 2.0 gilt nicht für den aktuellen macOS/OSX-KVM-Workflow.",
    "Dependencias faltantes": "Fehlende Abhängigkeiten",
    "No se pudieron preparar automáticamente las dependencias necesarias.\n\n{0}":
        "Die erforderlichen Abhängigkeiten konnten nicht automatisch vorbereitet werden.\n\n{0}",
    "System Recovery de macOS": "macOS System Recovery",
    "No se pudo preparar System Recovery antes de iniciar la VM.\n\n{0}":
        "System Recovery konnte vor dem Start der VM nicht vorbereitet werden.\n\n{0}",
    "Disco existente con otra configuración":
        "Vorhandene Festplatte mit anderer Konfiguration",
    "Ya existe un disco para '{0}' con {1} / {2} / {3}, distinto a lo solicitado ({4} / {5} / {6}).\n\n¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n(\"No\" conserva el disco existente tal como está.)":
        "Es existiert bereits eine Festplatte für '{0}' mit {1} / {2} / {3}, abweichend von der angeforderten ({4} / {5} / {6}).\n\nMöchtest du sie löschen und eine neue mit den aktuellen Parametern erstellen?\n(\"Nein\" behält die vorhandene Festplatte unverändert.)",
    "Error": "Fehler",
    "No se encuentra la carpeta 'OSX-KVM'.": "Der Ordner 'OSX-KVM' wurde nicht gefunden.",
    "Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.":
        "Du musst einen gültigen Windows-ISO-Dateipfad angeben oder 'Windows-Installer automatisch herunterladen' im CD/DVD auswählen.",
    "Android": "Android",
    "Debes configurar la ISO de Android-x86 o Bliss OS en Configuración → Almacenamiento → CD / DVD.\n\nDescárgala de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAñade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente».":
        "Du musst das Android-x86- oder Bliss-OS-ISO in Konfiguration → Speicher → CD / DVD konfigurieren.\n\nLade es herunter von:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nFüge ein CD/DVD-Laufwerk hinzu und wähle «Vorhandenes ISO/IMG/DMG verwenden».",
    "Error al guardar configuración": "Fehler beim Speichern der Konfiguration",
    "No se pudo guardar vm_config.ini para '{0}': {1}":
        "vm_config.ini konnte für '{0}' nicht gespeichert werden: {1}",
    "No se puede preparar el passthrough USB":
        "USB-Passthrough kann nicht vorbereitet werden",
    "La VM no se iniciará hasta resolver el acceso al USB.\n\n{0}\n\nNo se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.":
        "Die VM startet erst, wenn der USB-Zugriff gelöst ist.\n\n{0}\n\nEin Root Hub darf nicht ausgewählt werden. Der USB-Stick muss vom Host ausgehängt werden.",
    "Instalador del sistema operativo": "Betriebssystem-Installer",
    "La descarga se realiza dentro de la carpeta de la VM.":
        "Der Download erfolgt im VM-Ordner.",
    "Máquina virtual iniciada.": "Virtuelle Maschine gestartet.",
    "Descarga cancelada por el usuario.":
        "Download vom Benutzer abgebrochen.",
    "QEMU terminó con error. Revisa la consola de progreso.":
        "QEMU wurde mit Fehler beendet. Überprüfe die Fortschrittskonsole.",

    # ================================================================
    # mac_recovery_mixin.py
    # ================================================================
    "Apple no devolvió una sesión de Recovery válida.":
        "Apple hat keine gültige Recovery-Sitzung zurückgegeben.",
    "Apple no devolvió todos los datos del Recovery: {0}":
        "Apple hat nicht alle Recovery-Daten zurückgegeben: {0}",
    "{0} — {1:.1f} MB descargados":
        "{0} — {1:.1f} MB heruntergeladen",
    "{0} — 100%": "{0} — 100%",
    "El chunklist de System Recovery está incompleto.":
        "Die System-Recovery-Chunklist ist unvollständig.",
    "Cabecera de chunklist de Apple no válida.":
        "Ungültiger Apple-Chunklist-Header.",
    "Chunklist de Apple no válido.": "Ungültige Apple-Chunklist.",
    "Chunklist truncado en el bloque {0}.":
        "Chunklist bei Block {0} abgeschnitten.",
    "La verificación del Recovery falló en el bloque {0}.":
        "Die Recovery-Überprüfung ist bei Block {0} fehlgeschlagen.",
    "La imagen Recovery contiene datos adicionales no descritos por el chunklist.":
        "Das Recovery-Image enthält zusätzliche Daten, die nicht in der Chunklist beschrieben sind.",
    "No hay una carpeta de VM seleccionada.":
        "Es ist kein VM-Ordner ausgewählt.",
    "Consultando Apple…": "Apple wird abgefragt…",
    "Descargando chunklist…": "Chunklist wird heruntergeladen…",
    "Descargando chunklist": "Chunklist wird heruntergeladen",
    "Descargando BaseSystem.dmg…": "BaseSystem.dmg wird heruntergeladen…",
    "Descargando BaseSystem.dmg": "BaseSystem.dmg wird heruntergeladen",
    "Verificando integridad…": "Integrität wird überprüft…",
    "Verificación completada.": "Überprüfung abgeschlossen.",
    "No se encontró 'dmg2img' y no se pudo instalar automáticamente. Instálalo con el gestor de paquetes (en Arch/CachyOS: paru -S dmg2img).":
        "'dmg2img' wurde nicht gefunden und konnte nicht automatisch installiert werden. Installiere es mit dem Paketmanager (unter Arch/CachyOS: paru -S dmg2img).",
    "Convirtiendo BaseSystem.dmg → BaseSystem.img…":
        "BaseSystem.dmg → BaseSystem.img wird konvertiert…",
    "dmg2img no pudo preparar BaseSystem.img.\n{0}":
        "dmg2img konnte BaseSystem.img nicht vorbereiten.\n{0}",
    "dmg2img terminó pero BaseSystem.img no existe o está vacío.":
        "dmg2img wurde beendet, aber BaseSystem.img existiert nicht oder ist leer.",

    # ================================================================
    # Cadenas sueltas del tree de dispositivos
    # ================================================================
    "Organigrama": "Baum",
    "Disco": "Festplatte",
    "FDC": "FDC",
}
