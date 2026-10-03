# -*- coding: utf-8 -*-
"""translate_ts.py - Rellena i18n/vm_en.ts a partir de un diccionario.

Uso (desde la raiz del proyecto):
    python3 translate_ts.py
    lrelease6 i18n/vm_en.ts

Mantiene el diccionario TRANSLATIONS abajo. Cada vez que ejecutes
pylupdate6 para anadir cadenas nuevas, corre este script para rellenar
las que ya tengas traducidas. Las que no esten en el diccionario se
quedan como "unfinished" (Qt Linguist las muestra pendientes).
"""
import os, sys
import argparse
import importlib.util
import xml.etree.ElementTree as ET

TS_PATH = os.path.join("i18n", "vm_en.ts")


def _load_external_dict(lang):
    """Carga y fusiona todos los translations/vm_<lang>*.py.

    Permite dividir las traducciones de un idioma en varios archivos
    (vm_fr.py, vm_fr_tanda2a.py, vm_fr_tanda2b.py, ...) sin tener que
    mantener un unico dict gigante. Los ultimos archivos sobreescriben
    a los primeros (por orden alfabetico), asi que una correccion
    posterior puede ir en vm_<lang>_fix1.py.
    """
    import glob
    pattern = os.path.join("translations", "vm_%s*.py" % lang)
    files = sorted(glob.glob(pattern))
    # Excluir __init__.py y similares
    files = [p for p in files if os.path.basename(p) != "__init__.py"]
    if not files:
        return None
    merged = {}
    for path in files:
        modname = os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(modname, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        merged.update(getattr(mod, "TRANSLATIONS", {}))
    return merged

# --------------------------------------------------------------------
# Diccionario: clave = texto original (espanol), valor = traduccion.
# Anade aqui las nuevas a medida que las vayas necesitando.
#
# Cuidado con:
#   - Los placeholders {0}, {1}, {2} deben conservarse.
#   - El HTML embebido (<br>, <code>, <b>) va dentro de la cadena.
#   - Los emojis al inicio forman parte de la cadena.
#   - El caracter ... puede ser el unicode U+2026 (...) o tres puntos.
# --------------------------------------------------------------------
TRANSLATIONS = {

    # ================================================================
    # i18n_v1: pestanas principales, titulo y dialogo de reinicio
    # ================================================================
    "Resumen": "Overview",
    "Configuración VM": "VM Settings",
    "Configuración Host": "Host Settings",
    "Snapshots": "Snapshots",
    "\U0001f4be Backups": "\U0001f4be Backups",
    "\U0001f4da Medios": "\U0001f4da Media",
    "\U0001f5a5\ufe0f Consola Gráfica": "\U0001f5a5\ufe0f Graphical Console",
    "\U0001f4cb Consola de Progreso": "\U0001f4cb Progress Console",
    "\u2753 Ayuda": "\u2753 Help",
    "Administrador QEMU/KVM": "QEMU/KVM Manager",
    "Cambio de idioma": "Language change",
    "Se ha cambiado el idioma a {0}.\n\n"
    "Para que TODA la aplicación use el idioma nuevo\n"
    "es necesario reiniciar.\n\n"
    "¿Quieres reiniciar ahora?":
        "The language has been changed to {0}.\n\n"
        "To apply the new language to the WHOLE application,\n"
        "a restart is required.\n\n"
        "Do you want to restart now?",

    # ================================================================
    # Tanda 2a: dialogs.py
    # ================================================================

    # --- DiskCreationDialog: cabeceras segun tipo de dispositivo ---
    'Configurar dispositivo de almacenamiento': 'Configure storage device',
    '\U0001f4bd Disco SATA': '\U0001f4bd SATA Disk',
    '\u26a1 Disco NVMe': '\u26a1 NVMe Disk',
    '\U0001f4be Disquetera': '\U0001f4be Floppy Drive',
    '\U0001f4c0 Unidad CD / DVD': '\U0001f4c0 CD / DVD Drive',
    'Dispositivo de almacenamiento': 'Storage device',

    # --- Botones comunes ---
    'Cancelar': 'Cancel',
    'Aceptar': 'OK',
    'Crear': 'Create',
    'Elegir': 'Pick',

    # --- DiskCreationDialog: fuentes del medio (CD/DVD) ---
    'Mantener vacío': 'Keep empty',
    'Usar ISO/IMG/DMG existente': 'Use existing ISO/IMG/DMG',
    'System Recovery de macOS (descargar al iniciar)':
        'macOS System Recovery (download on start)',
    'Descargar instalador de Windows automáticamente':
        'Download Windows installer automatically',
    'Descargar instalador de Linux automáticamente':
        'Download Linux installer automatically',
    'Fuente del medio:': 'Medium source:',

    # --- DiskCreationDialog: campos de formulario ---
    'Nombre:': 'Name:',
    'Tamaño:': 'Size:',
    'Tipo:': 'Type:',
    'Formato:': 'Format:',
    'Origen:': 'Source:',
    'Archivo:': 'File:',
    'Medio:': 'Medium:',
    'Ruta del archivo existente…': 'Path of the existing file…',
    'Selecciona una ISO / IMG / DMG…': 'Select an ISO / IMG / DMG…',
    'Ej.: 40G, 100G, 1T': 'E.g.: 40G, 100G, 1T',

    # --- DiskCreationDialog: botones de exploracion ---
    '\U0001f4c1 Buscar…': '\U0001f4c1 Browse…',
    '\U0001f4da Biblioteca…': '\U0001f4da Library…',

    # --- DiskCreationDialog: toggles y modos ---
    'Crear nuevo': 'Create new',
    'Usar archivo existente': 'Use existing file',
    'Expandible (dinámico)': 'Expandable (dynamic)',
    'Fijo (preasignado)': 'Fixed (preallocated)',

    # --- DiskCreationDialog: tooltips ---
    'Elegir un medio de la biblioteca central (MediaLibrary/).\n'
    'Se reutiliza entre todas las VMs.':
        'Pick a medium from the central library (MediaLibrary/).\n'
        'It is shared across all VMs.',
    'Elegir un archivo ya registrado en la Biblioteca de Medios.\n'
    'Se filtra por el tipo del dispositivo.':
        'Pick a file already registered in the Media Library.\n'
        'It is filtered by device type.',

    # --- DiskCreationDialog: hints bajo el formulario ---
    'Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.':
        'RAW floppy. Choose 720 KB, 1.44 MB or 2.88 MB.',
    'Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. '
    'También puedes adjuntar un disco existente.':
        'Expandable: grows as it is used. Fixed: reserves the space on the host. '
        'You can also attach an existing disk.',
    'La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.':
        'The drive is created empty. You can insert an ISO later, even while the VM is running.',
    'Selecciona un ISO/IMG/DMG que ya exista en tu equipo.':
        'Select an ISO/IMG/DMG that already exists on your computer.',
    'Para macOS se descargará System Recovery automáticamente al iniciar la VM '
    'y se asociará a esta unidad óptica.':
        'For macOS, System Recovery will be downloaded automatically when the VM starts '
        'and attached to this optical drive.',
    'El instalador se descargará automáticamente al iniciar la VM, mostrando una '
    'barra de porcentaje, y quedará conectado a esta unidad CD/DVD.':
        'The installer will be downloaded automatically when the VM starts, showing '
        'a progress bar, and will be attached to this CD/DVD drive.',

    # --- Filtros de QFileDialog (parte humana; los globos se conservan) ---
    'Imágenes de disquete (*.img *.raw);;Todos los archivos (*)':
        'Floppy images (*.img *.raw);;All files (*)',
    'Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)':
        'Virtual disks (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;All files (*)',
    'Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)':
        'Images (*.iso *.img *.dmg);;All files (*)',
    'Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)':
        'Disk images (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;All (*)',

    # --- Titulos de QFileDialog ---
    'Seleccionar archivo existente': 'Select existing file',
    'Seleccionar medio óptico': 'Select optical medium',
    'Anadir a la biblioteca': 'Add to library',

    # --- Avisos y errores de validacion (DiskCreationDialog) ---
    'Medio inválido': 'Invalid medium',
    'Selecciona un ISO/IMG/DMG válido.': 'Select a valid ISO/IMG/DMG.',
    'Archivo inválido': 'Invalid file',
    'Selecciona un archivo existente válido.': 'Select a valid existing file.',
    'Nombre requerido': 'Name required',
    'Indica un nombre para el dispositivo.': 'Enter a name for the device.',
    'Escribe un nombre para el medio.': 'Enter a name for the medium.',
    'Tamaño inválido': 'Invalid size',
    'Usa un tamaño como 40G, 512M o 1T.': 'Use a size like 40G, 512M or 1T.',
    'Nombre inválido': 'Invalid name',
    'El nombre no puede contener \\ / : * ? " < > |':
        'The name cannot contain \\ / : * ? " < > |',

    # --- DiskCreationDialog: nombre por defecto del CD/DVD ---
    'CD/DVD': 'CD/DVD',

    # ================================================================
    # MediaPickerDialog: selector de medios de la biblioteca
    # ================================================================
    'Elegir medio de la biblioteca': 'Pick a medium from the library',
    'Elige una ISO/IMG/DMG de la biblioteca central.<br>'
    'La biblioteca vive en <code>MediaLibrary/</code>, al mismo nivel que '
    '<code>VirtualMachines/</code>. Se reutiliza entre todas las VMs.':
        'Pick an ISO/IMG/DMG from the central library.<br>'
        'The library lives in <code>MediaLibrary/</code>, at the same level as '
        '<code>VirtualMachines/</code>. It is shared across all VMs.',

    # --- Filtros del picker ---
    'Buscar...': 'Search...',
    'SO:': 'OS:',
    'Todos': 'All',
    'Disco duro': 'Hard disk',
    'Disquete': 'Floppy',

    # --- Cabeceras de la tabla del picker ---
    'Nombre': 'Name',
    'Tipo': 'Type',
    'SO': 'OS',
    'Version': 'Version',
    'Arq.': 'Arch.',
    'Tamano': 'Size',
    'Usada por': 'Used by',
    'Ruta': 'Path',

    # --- Botones del picker ---
    'Anadir archivo a la biblioteca...': 'Add file to library...',
    'Registrar una ISO nueva sin salir de este dialogo.':
        'Register a new ISO without leaving this dialog.',
    'Crear disco...': 'Create disk...',
    "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
    "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
    "sobre MediaLibrary/<nombre>.<ext>.":
        "Create a virtual disk (QCOW2 / RAW) or a floppy (IMG)\n"
        "directly in the library. Equivalent to 'qemu-img create'\n"
        "on MediaLibrary/<name>.<ext>.",
    'Abrir carpeta': 'Open folder',
    'Abre MediaLibrary/ en el explorador del sistema.':
        'Opens MediaLibrary/ in the system file manager.',

    # --- Celdas dinamicas del picker ---
    '{0}   (huerfano)': '{0}   (orphan)',
    '{0}, {1} (+{2})': '{0}, {1} (+{2})',
    '(sin archivo)': '(no file)',
    'No la usa ninguna VM.': 'No VM is using it.',

    # --- Avisos del picker ---
    'Archivo no disponible': 'File not available',
    'El archivo de esta entrada ya no existe en el disco.\n\n'
    'Ruta esperada:\n{0}':
        'The file for this entry no longer exists on disk.\n\n'
        'Expected path:\n{0}',
    'Biblioteca no disponible': 'Library not available',
    'La biblioteca de medios no está disponible.':
        'The media library is not available.',
    'Ya existe': 'Already exists',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n'
    'Elige otro nombre o bórralo desde la pestaña Medios.':
        'A file with that name already exists in the library:\n\n{0}\n\n'
        'Choose another name or delete it from the Media tab.',
    'Crear medio': 'Create medium',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
    "en Debian/Ubuntu, qemu-img en Arch) para crear discos.":
        "'qemu-img' not found. Install it (package qemu-utils\n"
        "on Debian/Ubuntu, qemu-img on Arch) to create disks.",
    'No se pudo crear el medio.\n\n{0}':
        'The medium could not be created.\n\n{0}',
    'Creado con qemu-img create. Tamaño: {0}.':
        'Created with qemu-img create. Size: {0}.',
    'El archivo se creó correctamente pero no se pudo\n'
    'registrar en la biblioteca:\n\n{0}':
        'The file was created successfully but could not be\n'
        'registered in the library:\n\n{0}',
    'Medio creado': 'Medium created',
    'Se creó el medio correctamente.\n\n'
    'Archivo: {0}\n'
    'Tamaño: {1}\n'
    'Formato: {2}':
        'The medium was created successfully.\n\n'
        'File: {0}\n'
        'Size: {1}\n'
        'Format: {2}',

    # ================================================================
    # NatPortForwardDialog: reglas NAT
    # ================================================================
    'Reglas de reenvío de puertos NAT': 'NAT port forwarding rules',
    'Redirige puertos del host al guest a través del NAT de QEMU '
    '(<code>-netdev user,hostfwd=...</code>). Cada regla conecta '
    '<b>localhost:puerto_host</b> del anfitrión con <b>puerto_guest</b> '
    'dentro del sistema invitado.<br><br>Ejemplo: host 2222 → guest 22 '
    'reenvía SSH; luego entra con '
    '<code>ssh -p 2222 usuario@localhost</code>.':
        "Forward host ports to the guest through QEMU's NAT "
        "(<code>-netdev user,hostfwd=...</code>). Each rule maps "
        "<b>localhost:host_port</b> on the host to <b>guest_port</b> "
        "inside the guest system.<br><br>Example: host 2222 → guest 22 "
        "forwards SSH; then connect with "
        "<code>ssh -p 2222 user@localhost</code>.",
    'Puerto host:': 'Host port:',
    'Puerto en el host (donde tú te conectas).':
        'Port on the host (where you connect from).',
    'Puerto guest:': 'Guest port:',
    'Puerto dentro de la VM (a donde se reenvía).':
        'Port inside the VM (where traffic is forwarded to).',
    'Protocolo:': 'Protocol:',
    '\u2795 Añadir regla': '\u2795 Add rule',
    'Puerto host': 'Host port',
    'Puerto guest': 'Guest port',
    'Protocolo': 'Protocol',
    '\U0001f5d1 Quitar seleccionada': '\U0001f5d1 Remove selected',
    'Regla duplicada': 'Duplicate rule',
    'Ya existe una regla para el puerto host {0} ({1}).\n\n'
    'Elige otro puerto host o cambia el protocolo.':
        'A rule for host port {0} ({1}) already exists.\n\n'
        'Choose another host port or change the protocol.',

    # ================================================================
    # NetworkDeviceDialog: adaptador de red virtual
    # ================================================================
    'Adaptador de red virtual': 'Virtual network adapter',
    'Red 1': 'Network 1',
    'NAT / Internet': 'NAT / Internet',
    'Bridge existente': 'Existing bridge',
    'Opcional: 52:54:00:xx:xx:xx': 'Optional: 52:54:00:xx:xx:xx',
    'Modelo:': 'Model:',
    'Backend:': 'Backend:',
    'Bridge / TAP:': 'Bridge / TAP:',
    'MAC:': 'MAC:',
    '\U0001f500 Reglas NAT…': '\U0001f500 NAT rules…',
    '\U0001f500 Reglas NAT… ({0})': '\U0001f500 NAT rules… ({0})',
    'Redirigir puertos del host al guest a través del NAT de QEMU\n'
    '(hostfwd). Solo aplica cuando el backend es NAT.':
        "Forward host ports to the guest through QEMU's NAT\n"
        "(hostfwd). Only applies when the backend is NAT.",
    'Red': 'Network',

    # ================================================================
    # _CreateMediumDialog: crear disco nuevo en la biblioteca
    # ================================================================
    'Crear medio nuevo': 'Create new medium',
    'Ej: disco_ubuntu_datos': 'E.g.: ubuntu_data_disk',
    'Disco duro QCOW2 (recomendado)': 'QCOW2 hard disk (recommended)',
    'Disco duro RAW': 'RAW hard disk',
    'Disquete IMG (RAW)': 'IMG floppy (RAW)',
    "Disquete formateado como RAW. Se registra como tipo 'Disquete' en "
    "la biblioteca. Tamaños típicos: 720 KB, 1.44 MB, 2.88 MB.":
        "Floppy formatted as RAW. Registered as type 'Floppy' in "
        "the library. Typical sizes: 720 KB, 1.44 MB, 2.88 MB.",
    'Disco virtual expandible (recomendado). El archivo en el host '
    'crece solo según se usa en el guest.':
        'Expandable virtual disk (recommended). The file on the host '
        'grows only as it is used in the guest.',
    'Disco RAW (imagen plana). Ocupa el tamaño completo en el host '
    'desde el momento de su creación.':
        'RAW disk (flat image). Occupies the full size on the host '
        'from the moment it is created.',

    # ================================================================
    # Tanda 2b: panel izquierdo + toolbar de Resumen
    # ================================================================
    "<b>MÁQUINAS VIRTUALES</b>": "<b>VIRTUAL MACHINES</b>",
    "🔍 Buscar máquinas...": "🔍 Search machines...",
    "Ordenar: Nombre (A-Z)": "Sort: Name (A-Z)",
    "Ordenar: Estado": "Sort: State",
    "Ordenar: Ultima vez usada": "Sort: Last used",
    "Como ordenar la lista de maquinas virtuales.\n"
    "  - Nombre: alfabetico.\n"
    "  - Estado: encendidas primero, luego pausadas, apagadas al final.\n"
    "  - Ultima vez usada: por fecha de modificacion del vm_config.ini\n"
    "    (aproxima cuando se configuro por ultima vez).":
        "How to sort the virtual machine list.\n"
        "  - Name: alphabetical.\n"
        "  - State: running first, then paused, shutdown last.\n"
        "  - Last used: by vm_config.ini modification date\n"
        "    (approximates when it was last configured).",
    "Todos los grupos": "All groups",
    "Muestra solo las VMs de un grupo concreto.\n"
    "  • Todos los grupos: sin filtro de grupo.\n"
    "  • Sin grupo: solo VMs sin etiqueta de grupo.\n"
    "  • <nombre>: solo VMs con ese grupo.\n"
    "\n"
    "Los grupos se asignan desde el botón '🏷 Etiqueta' del Resumen.":
        "Show only VMs in a specific group.\n"
        "  • All groups: no group filter.\n"
        "  • No group: only VMs without a group label.\n"
        "  • <name>: only VMs with that group.\n"
        "\n"
        "Groups are assigned from the '🏷 Label' button in Overview.",
    "➕ Nueva VM": "➕ New VM",
    "Selecciona una máquina virtual": "Select a virtual machine",
    "● Sin VM seleccionada": "● No VM selected",
    "▶ Iniciar": "▶ Start",
    "⏸ Pausar": "⏸ Pause",
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.":
        "Pause the VM. Use the arrow for more options:\n"
        "• Pause (quick): stops without saving state to disk.\n"
        "• Save state and pause: writes RAM to disk before pausing.\n"
        "• Resume: runs the paused VM again.",
    "⏹ Apagar": "⏹ Shut down",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.":
        "Shutdown (ACPI): asks the VM to shut down gracefully.",
    "⏹ Apagado (ACPI)": "⏹ Shutdown (ACPI)",
    "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\n"
    "encendido en un equipo real. El sistema operativo invitado decide cuándo\n"
    "y cómo cerrar. Puede tardar unos segundos o no responder si está colgado.":
        "Asks the VM to shut down gracefully, like pressing the power\n"
        "button on a real machine. The guest OS decides when and how\n"
        "to close. May take a few seconds or not respond if it is hung.",
    "⏻ Forzar apagado": "⏻ Force shutdown",
    "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\n"
    "como desenchufar un equipo real. Puede causar pérdida de datos no\n"
    "guardados; úsalo solo si la VM no responde al apagado normal.":
        "Cuts the VM immediately, without warning the guest OS —\n"
        "like unplugging a real machine. May cause loss of unsaved\n"
        "data; use only if the VM does not respond to normal shutdown.",
    "⟳ Reiniciar": "⟳ Reboot",
    "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\n"
    "No es un apagado ordenado del sistema operativo invitado: simplemente\n"
    "reinicia el hardware virtual.":
        "Reboots the VM (equivalent to the reset button on a real machine).\n"
        "It is not a graceful guest OS shutdown: it simply resets\n"
        "the virtual hardware.",
    "⟲ Forzar reinicio": "⟲ Force reboot",
    "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\n"
    "al sistema operativo invitado. Úsalo solo si la VM no responde ni al\n"
    "apagado ni al reinicio normales.":
        "Cuts the VM completely and restarts it from scratch, without warning\n"
        "the guest OS. Use only if the VM does not respond to either\n"
        "normal shutdown or reboot.",
    "⏸ Pausar (rápido)": "⏸ Pause (quick)",
    "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\n"
    "el estado (RAM y dispositivos) se pierde si el host se reinicia.":
        "Pauses the VM without saving state to disk. Instant, but\n"
        "the state (RAM and devices) is lost if the host reboots.",
    "▶ Reanudar": "▶ Resume",
    "Reanuda la ejecución de la VM pausada.":
        "Resumes execution of the paused VM.",
    "📸 Tomar Snapshot": "📸 Take Snapshot",
    "Guarda la RAM y el estado de los dispositivos a disco (como un\n"
    "snapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\n"
    "El snapshot aparecerá en la pestaña Snapshots y su captura de\n"
    "pantalla en el panel 'Último snapshot'.":
        "Saves RAM and device state to disk (like a snapshot)\n"
        "and then pauses the VM. Slower but survives reboots.\n"
        "The snapshot will appear in the Snapshots tab and its screenshot\n"
        "in the 'Last snapshot' panel.",
    "Iniciar VM": "Start VM",
    "Pausar/Reanudar VM": "Pause/Resume VM",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\n"
    "Usa la flecha para más opciones (forzar, reiniciar).":
        "Shutdown (ACPI): asks the VM to shut down gracefully.\n"
        "Use the arrow for more options (force, reboot).",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Select a VM to manage it. Use 'New virtual machine' to create another.",
    "Nueva máquina virtual": "New virtual machine",
    "● Nueva VM": "● New VM",
    "💿 Medios": "💿 Media",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Cambia ISO en caliente, expulsa medios y conecta/desconecta\n"
    "USB sin reiniciar la máquina. Atajo: Ctrl+M.":
        "VM media: CD/DVD drives and USB devices.\n"
        "Hot-swap ISOs, eject media and connect/disconnect\n"
        "USB without restarting the machine. Shortcut: Ctrl+M.",
    "🧬 Clonar": "🧬 Clone",
    "Crea una copia completa de esta VM en una carpeta nueva.":
        "Creates a full copy of this VM in a new folder.",
    "🧬 Desenlazar": "🧬 Unlink",
    "Convierte este clon enlazado en un QCOW2 autónomo.\n"
    "Después, el clon deja de depender del original y puede\n"
    "moverse o copiarse por separado.\n\n"
    "Solo aparece cuando la VM seleccionada es un clon\n"
    "enlazado y está apagada.":
        "Converts this linked clone into a standalone QCOW2.\n"
        "Afterwards, the clone no longer depends on the original\n"
        "and can be moved or copied separately.\n\n"
        "Only appears when the selected VM is a linked\n"
        "clone and is powered off.",
    "⇩ Importar": "⇩ Import",
    "Importar una VM desde una carpeta (con vm_config.ini) o desde\n"
    "un archivo .tar.gz / .zip exportado previamente.":
        "Import a VM from a folder (with vm_config.ini) or from\n"
        "a previously exported .tar.gz / .zip file.",
    "⇪ Exportar": "⇪ Export",
    "Exportar esta VM como carpeta, .tar.gz o .zip portable.\n"
    "Se omiten los archivos de runtime (pids, sockets, logs).":
        "Export this VM as a folder, .tar.gz or portable .zip.\n"
        "Runtime files (pids, sockets, logs) are skipped.",
    "💾 Plantilla": "💾 Template",
    "Guarda la configuración de hardware de esta VM como\n"
    "plantilla reutilizable. Se omiten discos, ISOs, MACs,\n"
    "carpetas compartidas, notas y reglas NAT.\n"
    "Aparecerá en el menú del botón '➕ Nueva VM'.":
        "Saves this VM's hardware configuration as a\n"
        "reusable template. Disks, ISOs, MACs, shared\n"
        "folders, notes and NAT rules are skipped.\n"
        "It will appear in the '➕ New VM' button menu.",
    "📜 Comando QEMU": "📜 QEMU command",
    "Muestra el contenido de run_temp.sh: el comando exacto con\n"
    "el que QEMU está ejecutando (o ejecutó por última vez) esta\n"
    "VM. Solo está disponible si la VM se ha arrancado alguna vez.":
        "Shows the contents of run_temp.sh: the exact command\n"
        "QEMU is using (or last used) for this VM. Only available\n"
        "if the VM has been started at least once.",
    "📝 Notas": "📝 Notes",
    "Notas libres sobre esta VM. Se guardan en vm_config.ini\n"
    "(extra.notes) y aparecen como aviso amarillo debajo del\n"
    "estado en esta misma pestaña.":
        "Free-form notes about this VM. Stored in vm_config.ini\n"
        "(extra.notes) and shown as a yellow notice below the\n"
        "state in this same tab.",
    "🏷 Etiqueta": "🏷 Label",
    "Grupo y color de esta VM. El grupo agrupa VMs en la lista\n"
    "lateral; el color se aplica como fondo del ítem.":
        "Group and colour of this VM. The group bundles VMs in the\n"
        "sidebar; the colour is applied as the item background.",
    "⚖ Comparar con defaults": "⚖ Compare with defaults",
    "Compara la configuración actual de esta VM con los\n"
    "valores por defecto del perfil del SO. Permite aplicar\n"
    "los defaults a un campo o a todos; los cambios se aplican\n"
    "a los widgets y se persisten al Guardar.":
        "Compares this VM's current configuration with the\n"
        "OS profile defaults. Lets you apply defaults to\n"
        "one field or all; changes are applied to widgets\n"
        "and persisted on Save.",
    "🗑 Eliminar": "🗑 Delete",
    "Elimina esta VM (con opción de conservar los discos).":
        "Deletes this VM (with option to keep the disks).",
    "🗑️ Eliminar": "\U0001f5d1 Delete",
    "ℹ️ Información general": "ℹ️ General information",
    "🖼️ Último snapshot": "🖼️ Last snapshot",

    # --- Tanda 2c: panel derecho ---
    "📌 Fijar": "📌 Pin",
    "Fija este panel como columna derecha de la ventana, siempre visible.\nÚtil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\nVuelve a pulsar para devolverlo a Resumen.": "Pins this panel to the right column, always visible.\nUseful for monitoring CPU/RAM while working on another tab.\nPress again to return it to Overview.",
    "📊 Uso de recursos": "📊 Resource usage",
    "CPU (VM)": "CPU (VM)",
    "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n100% = el proceso usa el equivalente a todos los hilos del host.\nSi el host tiene 8 hilos y QEMU usa 4, verás 50%.": "QEMU process CPU usage on the host, attributed to this VM.\n100% = the process uses the equivalent of all host threads.\nIf the host has 8 threads and QEMU uses 4, you will see 50%.",
    "RAM (QEMU)": "RAM (QEMU)",
    "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\nrealmente en el sistema anfitrión), como porcentaje de la RAM\ntotal del host. No es la RAM que 've' el sistema invitado.": "RSS memory of the QEMU process on the host (what QEMU actually\noccupies on the host system), as a percentage of the host's\ntotal RAM. It is not the RAM the guest system 'sees'.",
    "Disco (VM)": "Disk (VM)",
    "I/O de disco generado por el proceso QEMU para esta VM, según\n/proc/<pid_qemu>/io (read_bytes + write_bytes).\nEs el tráfico real a los archivos de disco de la VM en el host.": "Disk I/O generated by the QEMU process for this VM, from\n/proc/<pid_qemu>/io (read_bytes + write_bytes).\nIt is the real traffic to the VM's disk files on the host.",
    "Red (VM)": "Network (VM)",
    "Tráfico de red de esta VM.\n• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n  asociada en el host (exacto).\n• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n  el host, así que no se puede medir sin Guest Agent.\n  El gráfico mostrará 'NAT (sin medida)'.": "Network traffic of this VM.\n• TAP/Bridge mode: reads the real counters of the associated\n  interface on the host (exact).\n• NAT mode: QEMU uses an internal stack with no visible interface\n  on the host, so it cannot be measured without a Guest Agent.\n  The graph will show 'NAT (no measurement)'.",
    "Estado:": "State:",
    "Tiempo activo:": "Uptime:",
    "Procesos:": "Processes:",
    "Dirección IP:": "IP address:",
    "Dirección MAC:": "MAC address:",
    "Guest Agent:": "Guest Agent:",
    "Carpetas:": "Folders:",
    "Clipboard:": "Clipboard:",
    "spice-vdagent:": "spice-vdagent:",
    "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\nCuando está activo, el clipboard bidireccional y la\nresolución automática funcionan.": "Detection of spice-vdagent in the guest via QEMU Guest Agent.\nWhen active, bidirectional clipboard and automatic\nresolution work.",
    "PID QEMU:": "QEMU PID:",
    "Uso de CPU del proceso QEMU expresado como porcentaje del total\nde hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\nvalor mostrado es 50%.": "QEMU process CPU usage expressed as a percentage of total host\nthreads. If the host has 8 threads and QEMU uses 4, the\nvalue shown is 50%.",
    "CPU (VM):": "CPU (VM):",
    "Memoria RAM libre del host, respecto al total.": "Free host RAM, relative to the total.",
    "RAM host:": "Host RAM:",
    "Tamaño del archivo de disco principal de la VM y su tamaño\nvirtual (lo que ve el sistema invitado).": "Size of the VM's main disk file and its virtual size\n(what the guest system sees).",
    "Disco:": "Disk:",
    "Número de snapshots registrados y antigüedad del último.": "Number of registered snapshots and age of the latest.",
    "Snapshots:": "Snapshots:",
    "Sin VM seleccionada": "No VM selected",
    "↩ Restaurar este snapshot": "↩ Restore this snapshot",
    "Restaura el snapshot más reciente de esta VM.\nSi la VM está corriendo, se restaura en caliente (snapshot-load).\nSi está apagada, se restauran los discos QCOW2 internos.": "Restores the most recent snapshot of this VM.\nIf the VM is running, it is restored live (snapshot-load).\nIf it is off, the internal QCOW2 disks are restored.",

    # --- Tanda 2c-bis: dinamicos panel derecho ---
    "No hay una máquina virtual seleccionada.\n\nPulsa 'Nueva máquina virtual' para comenzar.": "No virtual machine selected.\n\nPress 'New virtual machine' to begin.",
    "Configura el sistema en la pestaña 'Configuración'.": "Configure the system in the 'Settings' tab.",
    "● Ejecutándose": "● Running",
    "● Pausada": "● Paused",
    "● Apagada": "● Powered off",
    "Notas:": "Notes:",
    "Sí": "Yes",
    "No": "No",
    "Red 1": "Network 1",
    "Sin adaptadores configurados": "No adapters configured",
    "Disco Duro": "Hard disk",
    "CD/DVD": "CD/DVD",
    "vacío": "empty",
    "Sin dispositivos": "No devices",
    "Sistema:": "System:",
    "CPU:": "CPU:",
    "RAM:": "RAM:",
    "núcleos": "cores",
    "Firmware:": "Firmware:",
    "Secure Boot:": "Secure Boot:",
    "TPM:": "TPM:",
    "Gráficos:": "Graphics:",
    "Audio:": "Audio:",
    "Red:": "Network:",
    "Almacenamiento:": "Storage:",
    "Orden de arranque:": "Boot order:",
    "Ubicación:": "Location:",
    "VM nueva: todavía no se ha guardado una configuración.": "New VM: no configuration saved yet.",
    "Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio.": "Configure the VM in the 'Settings' tab and press the start button.",
    "Usa 'Configuración' para modificar hardware y opciones avanzadas.": "Use 'Settings' to change hardware and advanced options.",

    # --- Tanda 2d-1: Sistema + Procesador + Memoria ---
    "Sistema": "System",
    "Plataforma, firmware y opciones de bajo nivel del hardware virtual.": "Platform, firmware and low-level virtual hardware options.",
    "<b>Firmware</b>": "<b>Firmware</b>",
    "BIOS (tradicional)": "BIOS (legacy)",
    "UEFI (OVMF)": "UEFI (OVMF)",
    "<b>Chipset</b>": "<b>Chipset</b>",
    "i440FX (clásico)": "i440FX (classic)",
    "Q35 (moderno, PCIe)": "Q35 (modern, PCIe)",
    "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\nQ35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\npassthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica.": "i440FX: classic chipset, legacy PCI. Compatible with very old OSes.\nQ35: modern chipset with native PCIe, AHCI/SATA and better support for\nPCIe device passthrough. Recommended unless specific compatibility is required.",
    "<b>Seguridad</b>": "<b>Security</b>",
    "Secure Boot": "Secure Boot",
    "TPM 2.0": "TPM 2.0",
    "<b>Perfiles del sistema</b>": "<b>System profiles</b>",
    "Configuración optimizada para el sistema operativo seleccionado. Puede modificar los valores según sus necesidades.": "Optimised configuration for the selected operating system. You can adjust the values to your needs.",
    "<b>Opciones avanzadas</b>": "<b>Advanced options</b>",
    "Habilitar ACPI": "Enable ACPI",
    "Habilitar APIC": "Enable APIC",
    "Habilitar IOMMU": "Enable IOMMU",
    "PCIe Root Port": "PCIe Root Port",
    "Arrancar esta VM al abrir la aplicación": "Start this VM when the application opens",
    "Si está marcado, esta VM se arranca automáticamente al\nabrir la aplicación, tras un par de segundos.\n\nLas VMs marcadas se arrancan en cola, separadas por 4 s\nentre una y otra para no saturar el host. Las que ya estén\ncorriendo se saltan.\n\nNota: al auto-arrancar, la selección de la lista cambia a\ncada VM que se inicia.": "If checked, this VM starts automatically when the\napplication opens, after a couple of seconds.\n\nMarked VMs are started in a queue, 4 s apart from each\nother to avoid saturating the host. Already running ones\nare skipped.\n\nNote: during auto-start, the list selection changes to\neach VM being started.",
    "Modo compatibilidad de snapshots (fuerza hardware snapshoteable)": "Snapshot compatibility mode (forces snapshottable hardware)",
    "Procesador": "Processor",
    "Modelo de CPU y número de núcleos asignados a la máquina virtual.": "CPU model and number of cores assigned to the virtual machine.",
    "<b>Tipo de procesador</b>": "<b>Processor type</b>",
    "Automático (recomendado)": "Automatic (recommended)",
    "Host (máximo rendimiento)": "Host (maximum performance)",
    "QEMU x86-64 (compatibilidad)": "QEMU x86-64 (compatibility)",
    "Automático usa el perfil del SO. Host ofrece el máximo rendimiento pero reduce la portabilidad de la VM.": "Automatic uses the OS profile. Host offers the maximum performance but reduces the VM's portability.",
    "<b>Núcleos</b>": "<b>Cores</b>",
    "{0} núcleos": "{0} cores",
    "El número de núcleos se ajusta al par más cercano al valor elegido, hasta la mitad de los hilos del host.": "The number of cores is rounded to the nearest even value up to half the host threads.",
    "Memoria": "Memory",
    "Cantidad de memoria RAM asignada a la máquina virtual.": "Amount of RAM assigned to the virtual machine.",
    "<b>RAM asignada</b>": "<b>Allocated RAM</b>",
    "RAM del host: {0} GB (libre: {1} GB)": "Host RAM: {0} GB (free: {1} GB)",
    "Asignar más de la mitad de la RAM del host puede provocar uso intensivo de swap. La sugerencia es dejar al menos 2 GB para el sistema anfitrión.": "Allocating more than half of the host RAM may cause intensive swap usage. It is recommended to leave at least 2 GB for the host system.",

    # --- Tanda 2d-2: Pantalla + Consola remota ---
    "Pantalla": "Display",
    "Controlador gráfico virtual y memoria de video.": "Virtual graphics controller and video memory.",
    "<b>Gráficos / GPU</b>": "<b>Graphics / GPU</b>",
    "VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)": "VirtIO-GPU 2D (compatible • disk snap. ✓ • full snap. ✗)",
    "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)": "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)",
    "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)": "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)",
    "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)": "Red Hat QXL 2D (3D ✗ • full snap. ✓ • macOS ⚠)",
    "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)": "VMware SVGA II (accelerated 3D ✗ • full snap. ✓ • macOS ⚠)",
    "Sin video / Headless": "No video / Headless",
    "Automático detecta las capacidades del host y usa aceleración 3D cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\nSnapshots:\n  • VirtIO-GPU 2D → solo snap. de discos.\n  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n  • VirGL / Venus → no soportan ningún tipo de snapshot.": "Automatic detects the host capabilities and uses 3D acceleration when it is safe; otherwise, falls back to VirtIO-GPU 2D.\n\nSnapshots:\n  • VirtIO-GPU 2D → disk snapshots only.\n  • QXL and VMware SVGA → full snapshot (RAM + devices).\n  • VirGL / Venus → do not support any kind of snapshot.",
    "<b>Memoria de video (VRAM)</b>": "<b>Video memory (VRAM)</b>",
    "Host GPU: detectando…": "Host GPU: detecting…",
    "🖼 Mostrar la VM dentro de la app (consola VNC embebida)": "🖼 Show the VM inside the app (embedded VNC console)",
    "🖼️ Mostrar la VM dentro de la app (consola VNC embebida)": "🖼️ Show the VM inside the app (embedded VNC console)",
    "Cuando está activo, la VM se muestra dentro de la app.\nFuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\nSi lo desactivas, la VM se abre en una ventana externa y puedes\nelegir modos con aceleración 3D (VirGL, Venus).": "When enabled, the VM is shown inside the app.\nForces graphics without OpenGL acceleration (VNC does not support GL).\nIf you disable it, the VM opens in an external window and you can\nchoose modes with 3D acceleration (VirGL, Venus).",
    "Consola remota": "Remote console",
    "VNC (compatible con cualquier gráfico)": "VNC (compatible with any graphics)",
    "SPICE (mejor rendimiento en local)": "SPICE (better performance on local)",
    "VNC: cliente ligero, funciona con cualquier dispositivo de video.\nSPICE: mejor rendimiento en local, requiere un visor spice-gtk.\nCon cualquiera de los dos, QEMU no abre ventana local: solo el socket.": "VNC: lightweight client, works with any video device.\nSPICE: better performance on local, requires a spice-gtk viewer.\nWith either one, QEMU does not open a local window: only the socket.",
    "Protocolo:": "Protocol:",
    "Embebida en la app": "Embedded in the app",
    "Ventana externa (visor del sistema)": "External window (system viewer)",
    "Ventana nativa de QEMU": "QEMU native window",
    "Híbrida (VNC embebido + SPICE externo)": "Hybrid (embedded VNC + external SPICE)",
    "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\nVentana externa: se lanza el visor del sistema (vncviewer / spicy).\nNativa QEMU: QEMU abre su propia ventana (comportamiento clásico).": "Embedded: the screen lives inside this app (Graphical Console tab).\nExternal window: launches the system viewer (vncviewer / spicy).\nQEMU native: QEMU opens its own window (classic behaviour).",
    "Modo:": "Mode:",
    "Log VNC detallado (DEBUG)": "Detailed VNC log (DEBUG)",
    "Activa el nivel DEBUG del cliente VNC embebido.\n\nPor defecto INFO: el widget VNC no llena launch.log con\nuna línea por cada frame. Actívalo solo para diagnosticar\nproblemas concretos del cliente VNC; escribe miles de\nlíneas por segundo y puede afectar al rendimiento.": "Enables the DEBUG level of the embedded VNC client.\n\nDefault INFO: the VNC widget does not fill launch.log with\none line per frame. Enable only to diagnose specific\nVNC client issues; writes thousands of lines per second\nand may affect performance.",

    # --- Tanda 2d-2b: consola remota (backend + mixin) ---
    "QEMU abre su propia ventana (GTK/SDL). No hace falta visor externo ni cliente; a cambio, la VM no aparece dentro de la app.": "QEMU opens its own window (GTK/SDL). No external viewer or client needed; in exchange, the VM does not appear inside the app.",
    "Híbrida: VNC se muestra dentro de la app (funciona en Wayland y X11) y SPICE se abre en una ventana externa con spicy o remote-viewer. Lo mejor de ambos: embebido para tenerlo a mano, SPICE para rendimiento y clipboard avanzado.": "Hybrid: VNC is shown inside the app (works on Wayland and X11) and SPICE opens in an external window with spicy or remote-viewer. Best of both: embedded to have it at hand, SPICE for performance and advanced clipboard.",
    "VNC embebido en la app. Sin dependencias adicionales.": "VNC embedded in the app. No additional dependencies.",
    "VNC en ventana externa. Necesitas vncviewer (tigervnc), gvncviewer o remmina instalado.": "VNC in an external window. You need vncviewer (tigervnc), gvncviewer or remmina installed.",
    "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). Requiere sesión X11; en Wayland cae a visor externo.": "SPICE embedded in the app (Gtk.SpiceDisplay via XEmbed). Requires an X11 session; on Wayland it falls back to external viewer.",
    "SPICE embebido solicitado, pero spice-gtk no tiene binding Python. Se usará visor externo como respaldo. Instala python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).": "SPICE embedding requested, but spice-gtk has no Python binding. An external viewer will be used as fallback. Install python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) or python-gobject + spice-gtk (Arch).",
    "SPICE en ventana externa. Necesitas spicy (spice-gtk) o remote-viewer (virt-viewer).": "SPICE in an external window. You need spicy (spice-gtk) or remote-viewer (virt-viewer).",
    "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden embeber dentro de la app.": "<b>Current session: X11.</b> Both VNC and SPICE can be embedded inside the app.",
    "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber dentro de la app. SPICE embebido requeriría X11 (XEmbed no existe en Wayland); si eliges SPICE con modo embebido, caerá automáticamente a visor externo.": "<b>Current session: Wayland.</b> Only VNC can be embedded inside the app. Embedded SPICE would require X11 (XEmbed does not exist on Wayland); if you choose SPICE with embedded mode, it will automatically fall back to an external viewer.",
    "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE funcionará cuando estés en X11.": "<b>spice-gtk with Python binding: yes.</b> SPICE embedding will work when you are on X11.",
    "<b>spice-gtk con binding Python: no.</b> Aunque estés en X11, SPICE no podrá incrustarse; siempre caerá a visor externo. Instálalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>": "<b>spice-gtk with Python binding: no.</b> Even on X11, SPICE cannot be embedded; it will always fall back to an external viewer. Install it with:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>",
    "<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Compatible con cualquier gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Se puede embeber dentro de la app, incluso en Wayland.<br><span style='color:#2e7d32;'>✓</span> Muchos visores externos disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> Sin dependencias adicionales en el guest para funcionar.<br><span style='color:#c62828;'>✗</span> Sin aceleración 3D ni streaming de video (redibuja por regiones).<br><span style='color:#c62828;'>✗</span> Clipboard limitado: solo texto, y el guest necesita <code>vncconfig</code> corriendo.<br><span style='color:#c62828;'>✗</span> Sin audio remoto.<br><span style='color:#c62828;'>✗</span> Menos fluido en uso intensivo (vídeo, animaciones, 3D).": "<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Compatible with any virtual graphics (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Can be embedded inside the app, even on Wayland.<br><span style='color:#2e7d32;'>✓</span> Many external viewers available (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> No additional dependencies in the guest to work.<br><span style='color:#c62828;'>✗</span> No 3D acceleration or video streaming (redraws by regions).<br><span style='color:#c62828;'>✗</span> Limited clipboard: text only, and the guest needs <code>vncconfig</code> running.<br><span style='color:#c62828;'>✗</span> No remote audio.<br><span style='color:#c62828;'>✗</span> Less fluid under heavy use (video, animations, 3D).",
    "<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Mejor rendimiento y fluidez en local (compresión + streaming de video).<br><span style='color:#2e7d32;'>✓</span> Clipboard bidireccional avanzado (con <code>spice-vdagent</code> en el guest).<br><span style='color:#2e7d32;'>✓</span> Audio remoto integrado.<br><span style='color:#2e7d32;'>✓</span> Varios monitores, redirección USB y carpetas compartidas nativas.<br><span style='color:#c62828;'>✗</span> No se puede embeber en Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Requiere un visor externo (spicy o remote-viewer) si no se puede embeber.<br><span style='color:#c62828;'>✗</span> Para aprovecharlo hay que instalar <code>spice-vdagent</code> en el guest.<br><span style='color:#c62828;'>✗</span> Incompatible con VirGL y Venus (usan OpenGL y obligan a la ventana nativa de QEMU).": "<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Better local performance and fluidity (compression + video streaming).<br><span style='color:#2e7d32;'>✓</span> Advanced bidirectional clipboard (with <code>spice-vdagent</code> in the guest).<br><span style='color:#2e7d32;'>✓</span> Integrated remote audio.<br><span style='color:#2e7d32;'>✓</span> Multiple monitors, USB redirection and native shared folders.<br><span style='color:#c62828;'>✗</span> Cannot be embedded on Wayland (X11 only, with spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Requires an external viewer (spicy or remote-viewer) if it cannot be embedded.<br><span style='color:#c62828;'>✗</span> To take advantage of it you must install <code>spice-vdagent</code> in the guest.<br><span style='color:#c62828;'>✗</span> Incompatible with VirGL and Venus (they use OpenGL and force QEMU's native window).",
    "<b>Híbrida (VNC embebido + SPICE externo)</b><br><span style='color:#2e7d32;'>✓</span> Lo mejor de ambos: VNC siempre visible dentro de la app, SPICE para rendimiento y clipboard.<br><span style='color:#2e7d32;'>✓</span> Funciona en cualquier sesión: Wayland o X11.<br><span style='color:#2e7d32;'>✓</span> Si spicy falla o lo cierras, el widget VNC sigue funcionando.<br><span style='color:#2e7d32;'>✓</span> Útil para ver la VM en dos monitores o para grabar y controlar a la vez.<br><span style='color:#c62828;'>✗</span> Consume más recursos: QEMU mantiene dos servidores de display en paralelo.<br><span style='color:#c62828;'>✗</span> Verás la misma VM en dos ventanas (dentro de la app y en la de spicy).<br><span style='color:#c62828;'>✗</span> La configuración del guest para sacar partido a SPICE (vdagent, drivers) hay que hacerla igual.<br><span style='color:#c62828;'>✗</span> Como SPICE, incompatible con VirGL y Venus.": "<b>Hybrid (embedded VNC + external SPICE)</b><br><span style='color:#2e7d32;'>✓</span> Best of both: VNC always visible inside the app, SPICE for performance and clipboard.<br><span style='color:#2e7d32;'>✓</span> Works on any session: Wayland or X11.<br><span style='color:#2e7d32;'>✓</span> If spicy fails or you close it, the VNC widget keeps working.<br><span style='color:#2e7d32;'>✓</span> Useful to see the VM on two monitors or to record and control at the same time.<br><span style='color:#c62828;'>✗</span> Uses more resources: QEMU keeps two display servers in parallel.<br><span style='color:#c62828;'>✗</span> You will see the same VM in two windows (inside the app and in spicy).<br><span style='color:#c62828;'>✗</span> The guest configuration to make the most of SPICE (vdagent, drivers) must be done either way.<br><span style='color:#c62828;'>✗</span> Like SPICE, incompatible with VirGL and Venus.",
    "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su propia ventana y no expone VNC/SPICE; es el único modo compatible con esos gráficos 3D.": "<b>Graphics compatible with VNC / SPICE / Hybrid:</b> <b>Automatic</b>, <b>VirtIO-GPU 2D</b> or <b>QXL</b>.<br>With <b>VirGL</b> or <b>Venus</b> selected, QEMU opens its own window and does not expose VNC/SPICE; it is the only mode compatible with those 3D graphics.",
    "Consola externa": "External console",
    "Selecciona primero una máquina virtual.": "Select a virtual machine first.",
    "No se encontró ningún visor {0} instalado.\n\n": "No {0} viewer was found installed.\n\n",
    "Instala gvncviewer o tigervnc (vncviewer).": "Install gvncviewer or tigervnc (vncviewer).",
    "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).": "Install spicy (spice-gtk) or remote-viewer (virt-viewer).",
    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\nLa VM debe estar corriendo para que QEMU haya elegido un\npuerto.": "I cannot determine the SPICE port of this VM yet.\n\nThe VM must be running for QEMU to have chosen a\nport.",
    "El socket {0} todavía no existe.\n\nLa VM debe estar corriendo con ese protocolo seleccionado.": "The {0} socket does not exist yet.\n\nThe VM must be running with that protocol selected.",

    # --- Tanda 2d-2c: graphics dynamic labels + hints ---
    "No detectada": "Not detected",
    "✓ OpenGL": "✓ OpenGL",
    "✗ OpenGL": "✗ OpenGL",
    "✓ VirGL": "✓ VirGL",
    "✓ VirGL instalado": "✓ VirGL installed",
    "✗ VirGL": "✗ VirGL",
    "✓ Vulkan": "✓ Vulkan",
    "✗ Vulkan": "✗ Vulkan",
    "VGA estándar (QEMU -vga std)": "Standard VGA (QEMU -vga std)",
    "VGA de OSX-KVM (VGA virtual)": "OSX-KVM VGA (virtual VGA)",
    "gestionada por OpenCore/OSX-KVM": "managed by OpenCore/OSX-KVM",
    "VirtIO-GPU + VirGL 3D": "VirtIO-GPU + VirGL 3D",
    "OpenGL / VirGL": "OpenGL / VirGL",
    "VirtIO-GPU 2D": "VirtIO-GPU 2D",
    "sin aceleración 3D": "without 3D acceleration",
    "VGA estándar de QEMU": "Standard QEMU VGA",
    "<b>Automático → {0}</b><br>Aceleración: {1}": "<b>Automatic → {0}</b><br>Acceleration: {1}",
    "VirtIO-GPU + Venus/Vulkan 3D": "VirtIO-GPU + Venus/Vulkan 3D",
    "Red Hat QXL 2D": "Red Hat QXL 2D",
    "VMware SVGA II": "VMware SVGA II",
    "<b>Usará: {0}</b>": "<b>Will use: {0}</b>",
    "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}": "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}",
    "Host GPU: no se pudo determinar automáticamente.<br>Automático: se seleccionará el modo gráfico compatible disponible.": "Host GPU: could not be determined automatically.<br>Automatic: the available compatible graphics mode will be selected.",
    "⚠ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.": "⚠ Android-x86 9.0 (kernel 4.9) does not include the VirtIO-GPU driver and falls back to a rescue shell with 'Detecting Android-x86…'. Use 'Automatic' or 'Red Hat QXL 2D'. ISOs with kernel 5.10+ or Bliss OS 15+ do support VirtIO-GPU.",
    "⚠️ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.": "⚠️ Android-x86 9.0 (kernel 4.9) does not include the VirtIO-GPU driver and falls back to a rescue shell with 'Detecting Android-x86…'. Use 'Automatic' or 'Red Hat QXL 2D'. ISOs with kernel 5.10+ or Bliss OS 15+ do support VirtIO-GPU.",
    "⚠ {0} + UEFI: el firmware OVMF puede no mostrar nada (pantalla negra) hasta que el guest cargue su propio driver de video. Si te pasa, prueba 'Automático' o 'VirtIO-GPU 2D'.": "⚠ {0} + UEFI: the OVMF firmware may show nothing (black screen) until the guest loads its own video driver. If this happens, try 'Automatic' or 'VirtIO-GPU 2D'.",
    "⚠️ {0} + UEFI: el firmware OVMF puede no mostrar nada (pantalla negra) hasta que el guest cargue su propio driver de video. Si te pasa, prueba 'Automático' o 'VirtIO-GPU 2D'.": "⚠️ {0} + UEFI: the OVMF firmware may show nothing (black screen) until the guest loads its own video driver. If this happens, try 'Automatic' or 'VirtIO-GPU 2D'.",

    # --- Tanda 2d-3a: Red + Dispositivos ---
    "Red": "Network",
    "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.": "Virtual network adapters. Each one can use NAT, bridge or TAP.",
    "Adaptadores": "Adapters",
    "➕ Agregar adaptador": "➕ Add adapter",
    "✏ Editar": "✏ Edit",
    "Sin red (ningún adaptador virtual)": "No network (no virtual adapter)",
    "NAT / Internet (recomendado)": "NAT / Internet (recommended)",
    "Bridge existente": "Existing bridge",
    "TAP": "TAP",
    "VirtIO (recomendado)": "VirtIO (recommended)",
    "Intel E1000": "Intel E1000",
    "Realtek RTL8139": "Realtek RTL8139",
    "VMware VMXNET3": "VMware VMXNET3",
    "Interfaz/Bridge:": "Interface/Bridge:",
    "Dispositivos": "Devices",
    "Audio y otros dispositivos integrados de la máquina virtual.": "Audio and other built-in devices of the virtual machine.",
    "<b>Audio</b>": "<b>Audio</b>",
    "Intel HDA (recomendado)": "Intel HDA (recommended)",
    "AC97": "AC97",
    "Sound Blaster 16": "Sound Blaster 16",
    "Sin sonido": "No sound",
    "<b>Dispositivo de señalización (ratón / teclado)</b>": "<b>Pointer device (mouse / keyboard)</b>",
    "USB Tablet (posición absoluta)": "USB Tablet (absolute position)",
    "USB Mouse (posición relativa)": "USB Mouse (relative position)",
    "USB Keyboard + Tablet": "USB Keyboard + Tablet",
    "VirtIO Tablet (requiere drivers en el guest)": "VirtIO Tablet (requires drivers in the guest)",
    "PS/2 (clásico)": "PS/2 (classic)",
    "Ninguno": "None",
    "Dispositivo de entrada que QEMU emula para el ratón/teclado.\n\n• Automático: macOS usa USB Tablet sobre NEC XHCI; el resto deja\n  el PS/2 por defecto de QEMU.\n• USB Tablet: posición absoluta (el cursor del guest sigue 1:1 al\n  del host). Recomendado si el cursor no se mueve bien.\n• USB Mouse: posición relativa, como un ratón físico.\n• USB Keyboard + Tablet: añade también un teclado USB.\n• VirtIO Tablet: mejor rendimiento, requiere drivers VirtIO en\n  el guest (no válido en macOS).\n• PS/2: ratón/teclado tradicionales de QEMU, sin USB.\n• Ninguno: sin ratón/teclado emulados.": "Input device QEMU emulates for mouse/keyboard.\n\n• Automatic: macOS uses USB Tablet over NEC XHCI; the rest keep\n  QEMU's default PS/2.\n• USB Tablet: absolute position (the guest cursor tracks 1:1 the\n  host's). Recommended if the cursor does not move well.\n• USB Mouse: relative position, like a physical mouse.\n• USB Keyboard + Tablet: also adds a USB keyboard.\n• VirtIO Tablet: better performance, requires VirtIO drivers in\n  the guest (not valid on macOS).\n• PS/2: traditional QEMU mouse/keyboard, no USB.\n• None: no emulated mouse/keyboard.",
    "Capturar el puerto serie a un archivo (serial.log)": "Capture the serial port to a file (serial.log)",
    "Activa -serial file:<vm_dir>/serial.log en la linea de QEMU.\n\nEl puerto serie del guest se vuelca a un archivo dentro de la\ncarpeta de la VM. La BIOS/OVMF, el cargador de arranque y el\nkernel suelen escribir ahi su progreso: es la forma mas directa\nde ver por que una VM se queda en pantalla negra o se reinicia.\n\nEl archivo se SOBREESCRIBE en cada arranque: solo conserva la\nultima sesion. Se puede abrir con '📂 Carpeta' en la pestana\nResumen.": "Enables -serial file:<vm_dir>/serial.log in the QEMU command line.\n\nThe guest serial port is dumped to a file inside the VM folder.\nBIOS/OVMF, the bootloader and the kernel usually write their\nprogress there: it is the most direct way to see why a VM stays\non a black screen or reboots.\n\nThe file is OVERWRITTEN on every boot: only the last session\nis kept. It can be opened with '📂 Folder' in the Overview tab.",
    "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña <b>Dispositivos</b> de la parte superior de la ventana.": "To pass physical hardware (PCI/USB) to this VM, use the <b>Devices</b> tab at the top of the window.",

    # --- Tanda 2d-3b: Almacenamiento ---
    "Almacenamiento": "Storage",
    "Controladores y dispositivos": "Controllers and devices",
    "Orden de arranque": "Boot order",
    "Dispositivo": "Device",
    "Tipo / archivo": "Type / file",
    "Tamaño": "Size",
    "📀 CD / DVD": "📀 CD / DVD",
    "💽 Disco Duro": "💽 Hard disk",
    "💾 Disquete": "💾 Floppy",
    "✏ Modificar": "✏ Modify",
    "✏️ Modificar": "✏️ Modify",
    "🗜 Compactar": "🗜 Compact",
    "🗜️ Compactar": "🗜️ Compact",
    "⬆ Subir": "⬆ Move up",
    "⬇ Bajar": "⬇ Move down",
    "🗑 Quitar": "🗑 Remove",
    "🗑️ Quitar": "🗑️ Remove",
    "Compacta un disco QCOW2 de la VM seleccionada.\n\nReduce el archivo físico en el host eliminando bloques no\nusados (equivalente a 'qemu-img convert -c'). NO cambia el\ntamaño virtual que ve el sistema invitado.\n\nSe pedirá confirmación y se recomienda hacer un backup antes\nde proceder. Requiere que la VM esté apagada.": "Compacts a QCOW2 disk of the selected VM.\n\nReduces the physical file on the host by removing unused\nblocks (equivalent to 'qemu-img convert -c'). Does NOT change\nthe virtual size the guest system sees.\n\nA confirmation will be requested and a backup is recommended\nbefore proceeding. Requires the VM to be powered off.",
    "Discos, unidades ópticas y orden de arranque de la máquina virtual.": "Disks, optical drives and boot order of the virtual machine.",

    # --- Tanda 2d-3c: storage_mixin.py (Expandir disco) ---
    "Cambiar el medio de esta unidad CD/DVD.": "Change the medium of this CD/DVD drive.",
    "Los disquetes no se pueden redimensionar.\nElimina este y crea otro si necesitas otro tamaño.": "Floppies cannot be resized.\nDelete this one and create another if you need a different size.",
    "↗ Expandir": "↗ Expand",
    "Aumentar el tamaño virtual de este disco.\nEl disco solo puede CRECER.": "Increase the virtual size of this disk.\nThe disk can only GROW.",
    "Expandir disco": "Expand disk",
    "No se encontro la informacion del dispositivo seleccionado.": "Information about the selected device was not found.",
    "Los disquetes no se pueden redimensionar.\n\nEliminalo y crea otro si necesitas otro tamano.": "Floppies cannot be resized.\n\nDelete it and create another if you need a different size.",
    "↗ Expandir disco": "↗ Expand disk",
    "Dispositivo:": "Device:",
    "Tamano actual:": "Current size:",
    "Ejemplo: 120G (solo crecer)": "Example: 120G (grow only)",
    "Nuevo tamano:": "New size:",
    "El disco solo puede CRECER. Si escribes un valor menor al actual, se rechaza y el campo vuelve al tamano original.\n\nAgrandar el archivo NO agranda la particion dentro del guest: tras aplicar el cambio, amplia tambien la particion/volumen desde el sistema invitado.": "The disk can only GROW. If you enter a smaller value than the current one, it will be rejected and the field will revert to the original size.\n\nEnlarging the file does NOT enlarge the partition inside the guest: after applying the change, also extend the partition/volume from the guest system.",
    "No se pudo expandir el disco.\n\n{0}": "The disk could not be expanded.\n\n{0}",

    # --- Tanda 2e-1: sidebar Configuracion VM ---
    "Passthrough": "Passthrough",
    "Compartición": "Sharing",

    # --- Tanda 2e-4: titulo Ayuda + boton guia consola ---
    "<h2>Ayuda de Virtual.Machine</h2>": "<h2>Virtual.Machine Help</h2>",
    "Guia completa de la consola (VNC / SPICE)": "Full console guide (VNC / SPICE)",
    "Guía completa de la consola (VNC / SPICE)": "Full console guide (VNC / SPICE)",

    # --- Tanda 2e-2: Config Host / Estado virtualizacion ---
    "Estado del sistema de virtualización": "Virtualization system status",
    "Distribución: comprobando...": "Distribution: checking...",
    "Gestor de paquetes: comprobando...": "Package manager: checking...",
    "🔄 Comprobar dependencias": "🔄 Check dependencies",
    "🔄️ Comprobar dependencias": "🔄️ Check dependencies",
    "🛠 Comprobar/Reparar dependencias": "🛠 Check/Repair dependencies",
    "🛠️ Comprobar/Reparar dependencias": "🛠️ Check/Repair dependencies",

    # --- Tanda 2e-2 full: Host Settings (apariencia, atajos, API) ---
    "Apariencia": "Appearance",
    "Sistema (predeterminado)": "System (default)",
    "Claro": "Light",
    "Oscuro": "Dark",
    "Tema visual de la aplicacion.\n  - Sistema: usa el estilo y la paleta del escritorio.\n  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n    propia, independiente del SO.\n\nAl elegir Claro u Oscuro, la app cambia el estilo de Qt a\nFusion. Al volver a Sistema, se restaura el estilo original\ndel escritorio (Breeze, Adwaita, etc.).": "Visual theme of the application.\n  - System: uses the desktop style and palette.\n  - Light / Dark: forces the Fusion style with its own\n    palette, independent of the OS.\n\nWhen you choose Light or Dark, the app switches the Qt style to\nFusion. When you switch back to System, the original desktop\nstyle is restored (Breeze, Adwaita, etc.).",
    "Tema:": "Theme:",
    "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\nreiniciar la app para que TODOS los widgets se repinten con los\ncolores nuevos (depende del estilo del escritorio).": "When switching between 'System' and 'Light/Dark' it may be\nnecessary to restart the app so that ALL widgets are repainted\nwith the new colours (depends on the desktop style).",
    "Atajos de teclado": "Keyboard shortcuts",
    "Reasigna los atajos globales de la aplicacion. Los cambios\nse aplican al instante, sin reiniciar.": "Reassign the global shortcuts of the application. Changes\napply immediately, without restarting.",
    "Configurar atajos...": "Configure shortcuts...",
    "API REST local": "Local REST API",
    "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar VMs desde scripts, dashboards o CI. Todo se autentica con un token local; <b>no</b> es accesible desde la red.": "Exposes a minimal HTTP API on <b>127.0.0.1</b> to control VMs from scripts, dashboards or CI. Everything is authenticated with a local token; it is <b>not</b> accessible from the network.",
    "Activar API REST local": "Enable local REST API",
    "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\nCambios requieren apagar y volver a encender la API.": "TCP port where the server listens. Only 127.0.0.1.\nChanges require stopping and restarting the API.",
    "Puerto:": "Port:",
    "URL:": "URL:",
    "Token:": "Token:",
    "Mostrar / ocultar el token": "Show / hide the token",
    "Copiar": "Copy",
    "Regenerar": "Regenerate",
    "Genera un token nuevo. Las peticiones con el token anterior\ndejarán de funcionar.": "Generates a new token. Requests with the previous\ntoken will stop working.",
    "Ver peticiones recientes": "View recent requests",
    "Ejemplo de uso desde terminal:<br><code>curl -H 'X-API-Token: &lt;tu-token&gt;' http://127.0.0.1:8730/api/vms</code>": "Example of use from terminal:<br><code>curl -H 'X-API-Token: &lt;your-token&gt;' http://127.0.0.1:8730/api/vms</code>",
    "Detenida": "Stopped",
    "Activa": "Active",

    # --- Tanda 2f-1: Snapshots ---
    "<b>Snapshots de la máquina virtual</b>": "<b>Virtual machine snapshots</b>",
    "Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.": "Create, restore, delete and manage snapshots. The application checks the writable QCOW2 disks, the free space and which disks will be part of the snapshot before running it.",
    "⚠ Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con ‘🧬 Desenlazar’ en la pestaña Resumen.": "⚠ This VM is a linked clone (QCOW2 backing file). Full snapshots (RAM + devices) cannot be restored in QEMU with a backing file; the app will always use DISK-ONLY snapshots. To get full snapshots, first unlink the clone with ‘🧬 Unlink’ in the Overview tab.",
    "🔄 Actualizar": "🔄 Refresh",
    "➕ Crear": "➕ Create",
    "↩ Restaurar": "↩ Restore",
    "✏ Cambiar nombre": "✏ Rename",
    "Formato": "Format",
    "Tamaño virtual": "Virtual size",
    "Tamaño archivo": "File size",
    "Libre host": "Host free",
    "Escritura": "Writable",
    "Snapshot": "Snapshot",
    "Sin operación de snapshot": "No snapshot operation",
    "ID": "ID",
    "Tamaño VM": "VM size",
    "Fecha": "Date",
    "Reloj VM": "VM clock",
    "Vista:": "View:",
    "📋 Lista": "📋 List",
    "🌳 Organigrama": "🌳 Tree",
    "Zoom:": "Zoom:",
    "Alejar la miniatura": "Zoom out the thumbnail",
    "Acercar la miniatura": "Zoom in the thumbnail",
    "Ajustar al tamaño original": "Fit to original size",
    "Sin captura de pantalla": "No screenshot",

    # --- Tanda 2f-1b: snapshots programados ---
    "Snapshots automaticos programados": "Scheduled snapshots",
    "Activar": "Enable",
    "Cuando esta activo, la app crea snapshots de disco automaticamente en esta VM segun la frecuencia elegida.\n\nLos snapshots programados son SOLO DE DISCOS (no guardan RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan por antiguedad al superar el limite de retencion.\n\nNo se ejecutan si la VM esta apagada.": "When enabled, the app creates disk snapshots automatically on this VM according to the chosen frequency.\n\nScheduled snapshots are DISK-ONLY (they do not save RAM or window state). They are created with the 'auto_' prefix and removed by age once the retention limit is exceeded.\n\nThey do not run if the VM is powered off.",
    "Cada hora": "Hourly",
    "Cada 6 horas": "Every 6 hours",
    "Cada 12 horas": "Every 12 hours",
    "Diario": "Daily",
    "Semanal": "Weekly",
    "Frecuencia con la que se crea el snapshot automatico.\nEl primer snapshot se crea pasada una frecuencia completa desde la activacion (o desde el ultimo, si ya habia uno).": "Frequency with which the automatic snapshot is created.\nThe first snapshot is created after one full period from activation (or from the last one, if there was already one).",
    "Frecuencia:": "Frequency:",
    "Cuantos snapshots automaticos conservar. Al superar este numero se eliminan los mas antiguos (solo los que empiezan por 'auto_'; los manuales nunca se tocan).": "How many automatic snapshots to keep. Once this number is exceeded, the oldest ones are removed (only those starting with 'auto_'; manual ones are never touched).",
    "Conservar:": "Keep:",
    "Los snapshots programados son <b>solo de discos</b>: no guardan RAM ni estado de ventanas. No congelan la VM del usuario (el snapshot completo si puede hacerlo).": "Scheduled snapshots are <b>disk-only</b>: they do not save RAM or window state. They do not freeze the user's VM (a full snapshot can).",
    "Selecciona una VM para programar snapshots.": "Select a VM to schedule snapshots.",
    "Desactivado para esta VM.": "Disabled for this VM.",
    "Sin snapshots programados todavia. Se creara el primero tras cumplirse la frecuencia elegida.": "No scheduled snapshots yet. The first one will be created once the chosen frequency elapses.",
    "Pendiente (ultimo: {0}). Se ejecutara en el proximo chequeo del scheduler.": "Pending (last: {0}). It will run on the next scheduler check.",
    "Ultimo: {0} · Proximo en ~{1} min.": "Last: {0} · Next in ~{1} min.",
    "Ultimo: {0}": "Last: {0}",

    # --- Boton Ajustar del preview ---
    "\u21ba Ajustar": "\u21ba Fit",

    # --- Tanda 2f-3: backup_schedule_mixin.py (Backups programados) ---
    "Backups automaticos programados": "Scheduled backups",
    "Cuando esta activo, la app copia la carpeta completa de la VM "
    "(discos, configuracion, snapshots) al destino elegido segun "
    "la frecuencia. Los backups son carpetas independientes; "
    "puedes borrarlos manualmente o dejar que la retencion los "
    "limpie.":
        "When enabled, the app copies the entire VM folder "
        "(disks, configuration, snapshots) to the chosen destination "
        "according to the frequency. Backups are independent folders; "
        "you can delete them manually or let retention clean them up.",
    "Carpeta del host donde guardar los backups":
        "Host folder where backups are stored",
    "Elegir carpeta...": "Choose folder...",
    "Destino:": "Destination:",
    "Cuantos backups conservar en el destino. Tras cada backup "
    "exitoso se borran los mas antiguos por encima de este numero.":
        "How many backups to keep at the destination. After each "
        "successful backup, the oldest ones beyond this number are "
        "removed.",
    "Tambien cuando la VM esta encendida": "Also when the VM is running",
    "Desactivado (recomendado): los backups solo se ejecutan con "
    "la VM apagada.\n\n"
    "Activado: si la VM esta encendida, se copian los discos de "
    "todos modos; la copia puede quedar inconsistente porque QEMU "
    "esta escribiendo en el .qcow2 en ese momento. La restauracion "
    "podria requerir fsck o no arrancar. Solo si estas dispuesto a "
    "asumir ese riesgo.":
        "Disabled (recommended): backups only run with the VM "
        "powered off.\n\n"
        "Enabled: if the VM is running, disks are copied anyway; "
        "the copy may be inconsistent because QEMU is writing to "
        "the .qcow2 at that moment. Restoring might require fsck "
        "or fail to boot. Only if you are willing to accept that "
        "risk.",
    "Los backups son <b>carpetas</b> con todos los archivos de la "
    "VM (discos + configuraci\u00f3n + snapshots + capturas). No "
    "incluyen pids, sockets ni logs. Para restaurar, usa el bot\u00f3n "
    "<b>Importar</b> de la pesta\u00f1a Resumen con la carpeta del "
    "backup.":
        "Backups are <b>folders</b> containing all the VM's files "
        "(disks + configuration + snapshots + screenshots). They do "
        "not include pids, sockets or logs. To restore, use the "
        "<b>Import</b> button in the Overview tab pointing at the "
        "backup folder.",
    "Backup ahora": "Backup now",
    "Ejecuta un backup inmediato con la configuracion actual, sin "
    "esperar a la proxima programacion.":
        "Runs an immediate backup with the current configuration, "
        "without waiting for the next schedule.",
    "Elegir carpeta de destino para backups":
        "Choose destination folder for backups",
    "Selecciona una VM para programar backups.":
        "Select a VM to schedule backups.",
    "Falta elegir una carpeta de destino.":
        "A destination folder must be chosen.",
    "Sin backups todavia. Libre en destino: {0}. "
    "Se creara el primero tras cumplirse la frecuencia.":
        "No backups yet. Free space at destination: {0}. "
        "The first one will be created once the frequency elapses.",
    "Pendiente (ultimo: {0}). Libre: {1}.":
        "Pending (last: {0}). Free: {1}.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min \u00b7 Libre: {2}.":
        "Last: {0} \u00b7 Next in ~{1} min \u00b7 Free: {2}.",
    "Ultimo: {0} \u00b7 Libre: {1}.":
        "Last: {0} \u00b7 Free: {1}.",
    "Backup": "Backup",
    "Configura primero una carpeta de destino.":
        "Configure a destination folder first.",
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "The destination folder could not be created:\n{0}\n\n{1}",
    "Espacio insuficiente en el destino. Necesario ~{0}, libre {1}.":
        "Not enough space at the destination. Needed ~{0}, free {1}.",
    "Selecciona primero una maquina virtual.":
        "Select a virtual machine first.",
    "Configura primero una carpeta de destino en esta "
    "seccion.":
        "Configure a destination folder in this section first.",
    "Backup con la VM encendida": "Backup with the VM running",
    "La VM esta encendida.\n\n"
    "Para evitar una copia inconsistente, apagala primero, o "
    "marca la opcion 'Tambien cuando la VM esta encendida' en "
    "esta seccion (asumiendo el riesgo).":
        "The VM is running.\n\n"
        "To avoid an inconsistent copy, shut it down first, or "
        "check the option 'Also when the VM is running' in this "
        "section (accepting the risk).",

    # i18n_tanda2f3_backup_schedule_v1,

    # --- Tanda 2f-4: media_library_mixin.py (Biblioteca de Medios UI) ---
    "Buscar por nombre, distro, tag...":
        "Search by name, distro, tag...",
    "Origen:": "Origin:",
    "Guest Tools": "Guest Tools",
    "Otros": "Others",
    "Todas": "All",
    "Universal": "Universal",
    "Sin especificar": "Unspecified",
    "Otro": "Other",
    "Manuales": "Manual",
    "De VMs": "From VMs",
    "Huerfanas de VM": "VM orphans",
    "Anadir archivo(s)": "Add file(s)",
    "Escanear carpeta": "Scan folder",
    "\U0001f50e Escanear VMs": "\U0001f50e Scan VMs",
    "Busca archivos de medios dentro de MediaLibrary/ que aun no "
    "esten registrados, y detecta entradas huerfanas (archivo "
    "desaparecido del disco).":
        "Looks for media files inside MediaLibrary/ that are not yet "
        "registered, and detects orphan entries (file missing from "
        "disk).",
    "Recorre todas las VMs en VirtualMachines/ y registra sus "
    "discos duros, ISOs y disquetes en la biblioteca.\n\n"
    "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
    "todas las VMs en la columna 'Usada por'. Las entradas que ya "
    "no usa ninguna VM se marcan como huerfanas pero no se borran.":
        "Walks all VMs in VirtualMachines/ and registers their hard "
        "disks, ISOs and floppies in the library.\n\n"
        "The same ISO used by several VMs appears ONLY ONCE, with "
        "all the VMs in the 'Used by' column. Entries no longer "
        "used by any VM are marked as orphans but are not deleted.",
    "<b>Biblioteca de Medios</b><br>"
    "<span style='color:#666;font-size:11px;'>"
    "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
    "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
    "nivel que <code>VirtualMachines/</code>) y se reutilizan "
    "entre maquinas."
    "</span>":
        "<b>Media Library</b><br>"
        "<span style='color:#666;font-size:11px;'>"
        "All the ISOs / IMGs / DMGs you use with your VMs, in a "
        "single place. They live in <code>MediaLibrary/</code> (same "
        "level as <code>VirtualMachines/</code>) and are shared "
        "across machines."
        "</span>",
    "Tamaño real": "Actual size",
    "Estado": "Status",
    "Ultimo uso": "Last used",
    "<b>Notas:</b>": "<b>Notes:</b>",
    "Notas libres sobre esta entrada (uso previsto, si dio "
    "problemas, driver necesario, etc.)":
        "Free-form notes about this entry (intended use, issues, "
        "required driver, etc.)",
    "<b>Tags:</b>": "<b>Tags:</b>",
    "Separados por coma (ej.: probado, servidor, rapiro)":
        "Comma-separated (e.g.: tested, server, fast)",
    "<b>Color:</b>": "<b>Color:</b>",
    "(Sin color)": "(No colour)",
    "Rojo": "Red",
    "Naranja": "Orange",
    "Ambar": "Amber",
    "Verde": "Green",
    "Verde azul": "Teal",
    "Azul": "Blue",
    "Indigo": "Indigo",
    "Violeta": "Violet",
    "Rosa": "Pink",
    "Gris": "Grey",
    "Biblioteca no disponible.": "Library not available.",
    "{0} entrada(s) mostradas de {1} | Tamano total: {2}":
        "{0} entry(ies) shown out of {1} | Total size: {2}",
    "huerfano": "orphan",
    "verificado?": "verified?",
    "Arq.:": "Arch.:",
    "ISO": "ISO",

    # --- Tanda 2f-4b: media_library_mixin.py handlers ---
    "Biblioteca de Medios": "Media Library",
    "La biblioteca no esta disponible.": "The library is not available.",
    "Anadir archivos a la biblioteca": "Add files to the library",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos los archivos (*)":
        "Disk images (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;All files (*)",
    "Escanear VMs": "Scan VMs",
    "No se pudieron escanear las VMs.\n\n{0}":
        "The VMs could not be scanned.\n\n{0}",
    "Archivos unicos encontrados en VMs: {0}.":
        "Unique files found in VMs: {0}.",
    "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca.":
        "- {0} new medium(s) added to the library.",
    "- {0} entrada(s) actualizada(s) con la lista de VMs que las usan.":
        "- {0} entry(ies) updated with the list of VMs using them.",
    "- {0} entrada(s) ya no las usa ninguna VM (siguen visibles; filtro Origen = 'Huerfanas de VM').":
        "- {0} entry(ies) are no longer used by any VM (still visible; filter Origin = 'VM orphans').",
    "Sin cambios: la biblioteca ya estaba al dia.":
        "No changes: the library was already up to date.",
    "Escanear": "Scan",
    "No se pudo escanear.\n\n{0}":
        "Could not scan.\n\n{0}",
    "No hay archivos nuevos ni entradas huerfanas.":
        "There are no new files or orphan entries.",
    "{0} archivo(s) nuevos encontrados:":
        "{0} new file(s) found:",
    "  ... y {0} mas": "  ... and {0} more",
    "{0} entrada(s) huerfanas (archivo ya no existe):":
        "{0} orphan entry(ies) (file no longer exists):",
    "Anadir los archivos nuevos a la biblioteca?":
        "Add the new files to the library?",
    "Agrandar": "Enlarge",
    "Selecciona una entrada primero.": "Select an entry first.",
    "Solo se pueden agrandar discos duros (QCOW2/RAW).":
        "Only hard disks (QCOW2/RAW) can be enlarged.",
    "El archivo no existe:\n{0}": "The file does not exist:\n{0}",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de agrandarlo.":
        "This disk is used by VM '{0}', which is running.\n\nShut it down before enlarging it.",
    "\u2197 Agrandar disco": "\u2197 Enlarge disk",
    "Version:": "Version:",
    "Eliminar": "Delete",
    "Tama\u00f1o actual:": "Current size:",
    "Nuevo tama\u00f1o:": "New size:",
    "Ejemplo: 120G (solo crecer)": "Example: 120G (grow only)",
    "El disco solo puede CRECER. Agrandar el archivo NO agranda\nla partici\u00f3n dentro del guest: hay que ampliarla tambi\u00e9n desde\nel sistema invitado para aprovechar el nuevo espacio.":
        "The disk can only GROW. Enlarging the file does NOT enlarge\nthe partition inside the guest: you also need to extend it from\nthe guest system to use the new space.",
    "Tama\u00f1o inv\u00e1lido": "Invalid size",
    "'{0}' no es un tama\u00f1o v\u00e1lido.": "'{0}' is not a valid size.",
    "No se puede encoger": "Cannot shrink",
    "Actual: {0}, indicado {1}.\n\nEl valor se ha restaurado al tama\u00f1o actual.":
        "Current: {0}, entered {1}.\n\nThe value has been reset to the current size.",
    "Aplicar": "Apply",
    "No se pudo agrandar el disco.\n\n{0}":
        "The disk could not be enlarged.\n\n{0}",
    "Disco agrandado": "Disk enlarged",
    "Se agrand\u00f3 correctamente a {0}.\n\nRecuerda ampliar tambi\u00e9n la partici\u00f3n dentro del sistema invitado.":
        "Successfully enlarged to {0}.\n\nRemember to also extend the partition inside the guest system.",
    "Compactar": "Compact",
    "Solo se pueden compactar discos en formato QCOW2.":
        "Only QCOW2 disks can be compacted.",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de compactarlo: QEMU mantiene un lock de\nescritura sobre el archivo y el compactado fallaria.":
        "This disk is used by VM '{0}', which is running.\n\nShut it down before compacting: QEMU holds a write lock\non the file and compaction would fail.",
    "\n\n\u26a0 Este disco lo usan VMs apagadas: {0}.\nSe recomienda hacer un backup antes de compactar.":
        "\n\n\u26a0 This disk is used by powered-off VMs: {0}.\nA backup is recommended before compacting.",
    "Confirmar compactado": "Confirm compaction",
    "\u00bfCompactar '{0}'?\n\nReescribe el QCOW2 eliminando bloques no usados: reduce el\narchivo en el host SIN cambiar el tama\u00f1o virtual que ve el\ninvitado.{1}\n\n\u00bfContinuar?":
        "Compact '{0}'?\n\nRewrites the QCOW2 removing unused blocks: reduces the\nfile on the host WITHOUT changing the virtual size the\nguest sees.{1}\n\nContinue?",
    "Compactando... {0}%": "Compacting... {0}%",
    "No se pudo compactar.\n\n{0}":
        "Could not compact.\n\n{0}",
    "Disco compactado": "Disk compacted",
    "'{0}' compactado.\n\nAntes: {1}\nDespu\u00e9s: {2}\nAhorro: {3}":
        "'{0}' compacted.\n\nBefore: {1}\nAfter: {2}\nSaved: {3}",
    "Compactando '{0}'": "Compacting '{0}'",
    "Reescribiendo el QCOW2 sin bloques no usados...":
        "Rewriting the QCOW2 without unused blocks...",
    "Verificar": "Verify",
    "El archivo ya no existe:\n{0}":
        "The file no longer exists:\n{0}",
    "El archivo existe. No hay sha256 guardado para comparar; usa 'Calcular SHA256' si quieres uno.":
        "The file exists. No sha256 stored to compare; use 'Compute SHA256' if you want one.",
    "Archivo presente y sha256 coincide.":
        "File present and sha256 matches.",
    "sha256 NO coincide.\n\nEsperado: {0}\nActual:   {1}":
        "sha256 does NOT match.\n\nExpected: {0}\nActual:   {1}",
    "SHA256": "SHA256",
    "sha256 calculado y guardado:\n\n{0}":
        "sha256 computed and saved:\n\n{0}",
    "Error: {0}": "Error: {0}",
    "Calculando sha256 \u2014 {0}": "Computing sha256 \u2014 {0}",
    "Editar": "Edit",
    "Editar \u2014 {0}": "Edit \u2014 {0}",
    "Distro:": "Distro:",
    "Arquitectura:": "Architecture:",
    "URL origen:": "Source URL:",
    "No se pudo guardar: {0}": "Could not save: {0}",
    "Eliminar entrada": "Delete entry",
    "Eliminar '{0}' de la biblioteca?":
        "Delete '{0}' from the library?",
    "Quitar del indice": "Remove from index",
    "Eliminar tambien el archivo": "Also delete the file",
    "La carpeta no existe:\n{0}":
        "The folder does not exist:\n{0}",

    # i18n_tanda2f4_media_library_handlers_v1

    # i18n_tanda2f4_media_library_ui_v1

    # --- Tanda 2f-5: snapshots_mixin.py (dialogos y avisos) ---
    "Apagado no completado": "Shutdown did not complete",
    "La VM no se apagó dentro del tiempo máximo (90 s).\n\n"
    "Puede que el sistema invitado esté colgado. Usa el botón\n"
    "'Forzar apagado' de la lista lateral, luego vuelve a intentar\n"
    "restaurar el snapshot con la VM ya apagada.":
        "The VM did not shut down within the maximum time (90 s).\n\n"
        "The guest system may be hung. Use the\n"
        "'Force shutdown' button in the sidebar, then try\n"
        "restoring the snapshot with the VM already powered off.",
    "No se puede restaurar este snapshot": "This snapshot cannot be restored",
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
        "The VM is a linked clone (QCOW2 backing file) and snapshot "
        "'{0}' was created in COMPLETE mode (RAM + devices).\n\n"
        "QEMU cannot restore full snapshots on a QCOW2 with a backing "
        "file: when running loadvm it aborts with an internal assertion "
        "(vmstate_load_next) and the process dies. That is the "
        "'Connection reset' you have seen.\n\n"
        "What to do:\n"
        "  • Snapshots you create FROM NOW ON in this clone will be "
        "disk-only (the app already forces this) and can be restored.\n"
        "  • This old snapshot cannot be restored. Delete it if you "
        "no longer need it.\n"
        "  • If you need full snapshots, unlink the clone with "
        "'🧬 Unlink' (converts the delta into a standalone QCOW2).",
    "Organigrama": "Tree",
    "No hay otros snapshots para elegir como padre.":
        "There are no other snapshots to choose as parent.",
    "Establecer padre": "Set parent",
    "Padre para '{0}':": "Parent for '{0}':",
    "(ninguno — mover a la raíz)": "(none — move to root)",
    "Nuevo snapshot hijo": "New child snapshot",
    "Nombre del snapshot (hijo de '{0}'):":
        "Snapshot name (child of '{0}'):",
    "No se pudo crear el snapshot.\n\n{0}":
        "The snapshot could not be created.\n\n{0}",
    "Sin capturas de snapshot": "No snapshot screenshots",
    "Los snapshots creados con la VM en ejecución guardan una "
    "captura de pantalla que se muestra aquí.":
        "Snapshots created while the VM is running save a "
        "screenshot that is shown here.",
    "Captura no legible": "Screenshot not readable",
    "Restaurar snapshot": "Restore snapshot",
    "No hay ningún snapshot reciente para restaurar.":
        "There is no recent snapshot to restore.",
    "Existe una captura para '{0}', pero ese snapshot ya no "
    "aparece en la lista de la VM (puede haber sido eliminado). "
    "Actualiza la pestaña Snapshots o elimínalo manualmente.":
        "A screenshot exists for '{0}', but that snapshot no longer "
        "appears in the VM list (it may have been deleted). "
        "Refresh the Snapshots tab or delete it manually.",
    "Snapshot con VirtIO-GPU": "Snapshot with VirtIO-GPU",
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
        "This VM is configured with '{0}' graphics, which do not allow\n"
        "RESTORING full snapshots in QEMU (RAM + devices).\n"
        "\n"
        "The snapshot can be created, but when trying to restore it QEMU\n"
        "will fail with: 'Failed to load element of type virtio for virtio'.\n"
        "\n"
        "Options:\n"
        "  • Use DISK-ONLY snapshot (choose 'No' in the next dialog).\n"
        "    It does not save RAM or window state, but can be restored\n"
        "    with the VM powered off.\n"
        "  • Change Graphics/GPU to 'Red Hat QXL 2D' or 'VMware SVGA II',\n"
        "    restart the VM and create full snapshots.\n"
        "\n"
        "Create the snapshot anyway?",
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
        "QEMU cannot restore the snapshot due to a known issue "
        "with the VirtIO-GPU device.\n\n"
        "Technical detail:\n"
        "  VirtIO-GPU stores internal state that is not reliably "
        "serialisable. QEMU tries to rebuild it on restore and fails.\n"
        "It is not an app bug, it is a limitation of the engine.\n\n"
        "How to fix it:\n"
        "  1. Open Settings → Display.\n"
        "  2. Change 'Graphics / GPU' from '{0}' to 'Red Hat QXL 2D'.\n"
        "  3. Restart the VM (power it off and boot it again).\n"
        "  4. Create new snapshots from that point on: they can be "
        "restored without issues.\n\n"
        "Old snapshots created with virtio-gpu cannot be recovered "
        "(QEMU cannot rebuild their state). If you no longer need them, "
        "delete them.",
    "Selecciona una máquina virtual.": "Select a virtual machine.",
    "No se puede crear un snapshot completo.\n\n":
        "A full snapshot cannot be created.\n\n",
    "Espacio disponible": "Available space",
    "{0}\n\n"
    "QEMU puede necesitar espacio adicional a medida que "
    "cambien los bloques. ¿Quieres continuar de todos modos?":
        "{0}\n\n"
        "QEMU may need additional space as blocks change. "
        "Do you want to continue anyway?",
    "Crear snapshot": "Create snapshot",
    "Nombre del snapshot:": "Snapshot name:",
    "Clon enlazado: snapshot solo de discos":
        "Linked clone: disk-only snapshot",
    "Esta VM es un clon enlazado (backing file QCOW2).\n\n"
    "QEMU no puede crear/restaurar snapshots completos\n"
    "(RAM + dispositivos) sobre un QCOW2 con backing\n"
    "file: al hacer loadvm QEMU aborta con una aserción\n"
    "interna (vmstate_load_next).\n\n"
    "Por seguridad se creará un snapshot SOLO DE DISCOS,\n"
    "que sí se puede restaurar con la VM apagada.\n\n"
    "Si necesitas un snapshot completo, desenlaza\n"
    "primero el clon (🧬 Desenlazar).":
        "This VM is a linked clone (QCOW2 backing file).\n\n"
        "QEMU cannot create/restore full snapshots\n"
        "(RAM + devices) on a QCOW2 with a backing\n"
        "file: when running loadvm, QEMU aborts with an internal\n"
        "assertion (vmstate_load_next).\n\n"
        "For safety, a DISK-ONLY snapshot will be created,\n"
        "which can be restored with the VM powered off.\n\n"
        "If you need a full snapshot, first unlink the clone\n"
        "(🧬 Unlink).",
    "Snapshot con la VM encendida": "Snapshot with the VM running",
    "La VM está encendida.\n\n"
    "Un snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y "
    "puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos "
    "observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\n"
    "Sí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
    "No = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\n"
    "Cancelar = no hacer nada.":
        "The VM is running.\n\n"
        "A COMPLETE snapshot must save RAM and the state of all devices and "
        "may keep QEMU fully busy during that process. On this VM we have "
        "already observed that QEMU can stay in STOP for a long time.\n\n"
        "Yes = create a COMPLETE SNAPSHOT (VM + RAM + devices + disks).\n"
        "No = create a DISK-ONLY SNAPSHOT (fast; does not save RAM or windows).\n"
        "Cancel = do nothing.",
    "Snapshot de discos creado": "Disk snapshot created",
    "Se creó '{0}' en {1} QCOW2.\n\n"
    "Este snapshot no contiene la memoria RAM ni el estado de las ventanas. "
    "Para restaurarlo, la VM debe estar apagada.":
        "'{0}' was created on {1} QCOW2.\n\n"
        "This snapshot does not contain RAM or window state. "
        "To restore it, the VM must be powered off.",
    "Error al crear snapshot de discos": "Error creating disk snapshot",
    "Error al crear snapshot": "Error creating snapshot",
    "No se pudo crear el snapshot completo.\n\n{0}":
        "The full snapshot could not be created.\n\n{0}",
    "Ya hay una operación de snapshot en curso.":
        "A snapshot operation is already running.",
    "La operación se ejecuta en segundo plano; la interfaz sigue "
    "disponible mientras QEMU procesa el snapshot.":
        "The operation runs in the background; the interface stays "
        "available while QEMU processes the snapshot.",
    "Snapshot — {0}": "Snapshot — {0}",
    "Estado '{0}' guardado y VM pausada.":
        "State '{0}' saved and VM paused.",
    "Snapshot '{0}' eliminado.": "Snapshot '{0}' deleted.",
    "Snapshot '{0}' restaurado.": "Snapshot '{0}' restored.",
    "Snapshot '{0}' creado.": "Snapshot '{0}' created.",
    "El snapshot '{0}' fue creado y confirmado por QEMU.":
        "Snapshot '{0}' was created and confirmed by QEMU.",
    "VM pausada": "VM paused",
    "Estado guardado como '{0}'.\n\nLa VM quedó pausada. "
    "Puedes reanudarla con el botón Pausar/Reanudar.":
        "State saved as '{0}'.\n\nThe VM was paused. "
        "You can resume it with the Pause/Resume button.",
    "Snapshot eliminado": "Snapshot deleted",
    "Se eliminó '{0}'.": "'{0}' was deleted.",
    "Snapshot restaurado": "Snapshot restored",
    "Se restauró '{0}'.": "'{0}' was restored.",
    "Error al eliminar snapshot": "Error deleting snapshot",
    "Error al guardar estado": "Error saving state",
    "Error al restaurar snapshot": "Error restoring snapshot",
    "CREACIÓN": "CREATION",
    "ELIMINACIÓN": "DELETION",
    "GUARDADO": "SAVE",
    "RESTAURACIÓN": "RESTORATION",
    "No se pudo completar la operación de snapshot '{0}'.\n\n{1}":
        "The snapshot operation '{0}' could not be completed.\n\n{1}",
    "¿Restaurar '{0}'?\n\nLa VM volverá al estado del snapshot.":
        "Restore '{0}'?\n\nThe VM will revert to the snapshot state.",
    "Snapshot solo de discos": "Disk-only snapshot",
    "El snapshot '{0}' es solo de discos (no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM primero.\n"
    "La VM volverá al estado del snapshot.\n\n"
    "¿Apagar la VM ahora y restaurar el snapshot?":
        "Snapshot '{0}' is disk-only (it does not contain RAM).\n\n"
        "To restore it, the VM must be shut down first.\n"
        "The VM will revert to the snapshot state.\n\n"
        "Shut down the VM now and restore the snapshot?",
    "Apagar la VM": "Shut down the VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "The shutdown command could not be sent.\n\n{0}",
    "Se restauró '{0}' mediante snapshot-load.":
        "'{0}' was restored via snapshot-load.",
    "Restauración parcial": "Partial restore",
    "El snapshot se restauró en algunos discos, pero falló en otros:\n\n":
        "The snapshot was restored on some disks, but failed on others:\n\n",
    "Se restauró el snapshot de disco en los QCOW2 elegibles. "
    "Con la VM apagada no se restaura el estado de RAM/CPU.":
        "The disk snapshot was restored on the eligible QCOW2 files. "
        "With the VM powered off, RAM/CPU state is not restored.",
    "El snapshot '{0}' es solo de discos "
    "(no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM y volver "
    "a intentarlo. QEMU no puede restaurar snapshots "
    "sin vmstate con la VM encendida.":
        "Snapshot '{0}' is disk-only "
        "(it does not contain RAM).\n\n"
        "To restore it, the VM must be shut down and you must retry. "
        "QEMU cannot restore snapshots without vmstate "
        "while the VM is running.",
    "La VM volvió a un estado operativo después de restaurar '{0}'.\n\n"
    "QEMU no confirmó el fin del job dentro del tiempo de espera, "
    "pero la restauración se aplicó.":
        "The VM returned to an operational state after restoring '{0}'.\n\n"
        "QEMU did not confirm job completion within the timeout, "
        "but the restore was applied.",
    "No se pudo restaurar el snapshot.\n\n{0}":
        "The snapshot could not be restored.\n\n{0}",
    "Eliminar snapshot": "Delete snapshot",
    "¿Eliminar '{0}'?": "Delete '{0}'?",
    "Eliminación parcial": "Partial deletion",
    "El snapshot se eliminó de algunos discos, pero falló en otros:\n\n":
        "The snapshot was deleted from some disks, but failed on others:\n\n",
    "No se pudo eliminar el snapshot.\n\n{0}":
        "The snapshot could not be deleted.\n\n{0}",
    "Cambiar nombre": "Rename",
    "Nuevo nombre para '{0}':": "New name for '{0}':",
    "Cambiar nombre de snapshot": "Rename snapshot",
    "QEMU no proporciona un renombrado interno directo. "
    "Esta acción creará un snapshot nuevo con el estado ACTUAL "
    "de la VM y eliminará el anterior.\n\n¿Continuar?":
        "QEMU does not provide a direct internal rename. "
        "This action will create a new snapshot with the CURRENT state "
        "of the VM and delete the previous one.\n\nContinue?",
    "Cambio de nombre parcial": "Partial rename",
    "El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n":
        "The new snapshot was created on some disks, but there were errors:\n\n",
    "No se pudo cambiar el nombre.\n\n{0}":
        "The name could not be changed.\n\n{0}",

    # i18n_tanda2f5_snapshots_mixin_v1
    '(sin miniatura)': '(no thumbnail)',
    'Restaurar este snapshot': 'Restore this snapshot',
    'Renombrar': 'Rename',
    '✏ Renombrar': 'Rename',
    '➕ Crear snapshot hijo': 'Create child snapshot',
    '🔗 Establecer padre…': 'Set parent…',
    '⬆ Mover a la raíz': 'Move to root',
    'Snapshot creado': 'Snapshot created',
    'Error al cambiar nombre': 'Error renaming',

    # i18n_tanda2f5_snapshots_mixin_fix1_v1

    # --- Tanda 3.1: health_dashboard_mixin.py ---
    "Salud de la máquina virtual": "Virtual machine health",
    "Comprobando\u2026": "Checking\u2026",
    "\U0001f504 Refrescar ahora": "\U0001f504 Refresh now",
    "Cerrar": "Close",
    "Sin VM seleccionada.": "No VM selected.",
    "La VM no está corriendo.": "The VM is not running.",
    "Cada fila muestra el estado de un subsistema de la VM. "
    "Verde: funciona · Amarillo: parcial o sin confirmar · "
    "Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s.":
        "Each row shows the status of a VM subsystem. "
        "Green: working · Yellow: partial or unconfirmed · "
        "Red: unavailable · Grey: not applicable. Refreshes every 4 s.",
    "<b style='font-size:15px;'>\U0001f6a6 Semáforos de salud</b>":
        "<b style='font-size:15px;'>\U0001f6a6 Health traffic lights</b>",
    "\U0001f310 Red de la VM":        "\U0001f310 VM network",
    "\U0001f5a5\ufe0f Internet del host": "\U0001f5a5\ufe0f Host Internet",
    "\U0001f50a Audio":               "\U0001f50a Audio",
    "\U0001f5bc\ufe0f Pantalla":      "\U0001f5bc\ufe0f Display",
    "\U0001f50c Guest Agent":         "\U0001f50c Guest Agent",
    "Host con salida a Internet (Apple y Cloudflare responden).":
        "Host has Internet access (Apple and Cloudflare respond).",
    "Salida parcial: uno de los dos destinos no respondió.":
        "Partial connectivity: one of the two destinations did not respond.",
    "El host no tiene salida a Internet.":
        "The host does not have Internet access.",
    "No hay script de arranque todavía.":
        "No launch script yet.",
    "No se pudo leer el script de arranque.":
        "The launch script could not be read.",
    "No hay adaptador de red configurado en esta VM.":
        "No network adapter is configured on this VM.",
    "NIC {0}: tráfico activo "
    "({1:.1f} KB/s; "
    "rx {2:.1f} MB, "
    "tx {3:.1f} MB).":
        "NIC {0}: active traffic "
        "({1:.1f} KB/s; "
        "rx {2:.1f} MB, "
        "tx {3:.1f} MB).",
    "NIC {0} con contadores activos pero "
    "sin tráfico en el último intervalo "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB).":
        "NIC {0} with active counters but "
        "no traffic in the last interval "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB).",
    "NIC {0}: contadores iniciales leídos "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB); "
    "esperando siguiente lectura para medir velocidad.":
        "NIC {0}: initial counters read "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB); "
        "waiting for next reading to measure speed.",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host; esperando segunda lectura "
    "para medir cambio.":
        "NIC {0} configured. {1} active TCP "
        "connections on the host; waiting for a second reading "
        "to measure change.",
    "NIC {0}: actividad detectada "
    "({1} \u2192 {2} conexiones TCP ESTAB).":
        "NIC {0}: activity detected "
        "({1} \u2192 {2} ESTAB TCP connections).",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host, sin cambios en el último "
    "intervalo (la VM puede estar idle).":
        "NIC {0} configured. {1} active TCP "
        "connections on the host, no change in the last "
        "interval (the VM may be idle).",
    "NIC {0} configurada; sin conexiones externas "
    "activas en el host.":
        "NIC {0} configured; no external connections "
        "active on the host.",
    "NIC {0} configurada. No se pudo medir tráfico (QMP no "
    "expone query-netdev y ss no está disponible).":
        "NIC {0} configured. Traffic could not be measured (QMP does not "
        "expose query-netdev and ss is not available).",
    "Sin audio configurado en esta VM.":
        "No audio configured on this VM.",
    "Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.":
        "Audiodev configured. pactl not available; playback cannot be confirmed.",
    "Audiodev configurado, pero no hay PID de QEMU para verificar el sink.":
        "Audiodev configured, but there is no QEMU PID to verify the sink.",
    "No se pudo consultar pactl: {0}":
        "Could not query pactl: {0}",
    "pactl no respondió.": "pactl did not respond.",
    "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo.":
        "Active sink: pactl sees QEMU (PID {0}) playing.",
    "Audiodev configurado; QEMU no está reproduciendo ahora. "
    "Es normal si el guest no está emitiendo sonido.":
        "Audiodev configured; QEMU is not playing right now. "
        "This is normal if the guest is not emitting sound.",
    "Framebuffer VNC {0}\u00d7{1}.": "VNC framebuffer {0}\u00d7{1}.",
    "Widget VNC conectado, esperando primer frame.":
        "VNC widget connected, waiting for the first frame.",
    "Consola SPICE embebida activa.":
        "Embedded SPICE console active.",
    "Visor externo activo (PID {0}).":
        "External viewer active (PID {0}).",
    "Modo remoto (socket VNC/SPICE) sin widget embebido ni "
    "visor activo. Abre la Consola Gráfica para ver la pantalla.":
        "Remote mode (VNC/SPICE socket) with no embedded widget or "
        "active viewer. Open the Graphical Console to see the screen.",
    "Modo headless (sin salida de pantalla).":
        "Headless mode (no display output).",
    "Ventana nativa de QEMU activa.":
        "QEMU native window active.",
    "Configuración de pantalla detectada en el script de arranque.":
        "Display configuration detected in the launch script.",
    "Guest Agent no habilitado para esta VM "
    "(actívalo en Integración Host \u2194 Guest).":
        "Guest Agent not enabled for this VM "
        "(enable it in Host \u2194 Guest Integration).",
    "QEMU Guest Agent responde.": "QEMU Guest Agent responds.",
    "Canal QGA presente, pero el guest no responde.":
        "QGA channel present, but the guest does not respond.",
    "Canal QGA presente, sin respuesta: {0}":
        "QGA channel present, no response: {0}",

    # i18n_tanda3_health_dashboard_v1

    # --- Tanda 3.2: diagnostics_mixin.py ---
    "Ver log completo": "View full log",
    "Selecciona una VM primero.": "Select a VM first.",
    "Todavía no hay historial guardado para esta VM.":
        "There is no saved history for this VM yet.",
    "Exportar log": "Export log",
    "Log completo \u2014 {0}": "Full log \u2014 {0}",
    "No se pudo leer el log: {0}":
        "The log could not be read: {0}",
    "No se pudo exportar el log: {0}":
        "The log could not be exported: {0}",
    "Log exportado a:\n{0}": "Log exported to:\n{0}",
    "Cerrar": "Close",
    "Salud de la VM": "VM health",
    "VM: {0}": "VM: {0}",
    "Carpeta: {0}": "Folder: {0}",
    "\u25cf QEMU: detenido.": "\u25cf QEMU: stopped.",
    "\u25cf QEMU: {0}{1}.": "\u25cf QEMU: {0}{1}.",
    "\u25cf Guest Agent: no aplica (VM apagada).":
        "\u25cf Guest Agent: not applicable (VM powered off).",
    "\u25cf Guest Agent: responde (v{0}).":
        "\u25cf Guest Agent: responds (v{0}).",
    "\u25cf Guest Agent: sin respuesta ({0}). "
    "Verifica que qemu-guest-agent esté instalado y "
    "corriendo en el guest.":
        "\u25cf Guest Agent: no response ({0}). "
        "Verify that qemu-guest-agent is installed and "
        "running in the guest.",
    "\u25cf Carpetas compartidas (VirtioFS): ninguna configurada.":
        "\u25cf Shared folders (VirtioFS): none configured.",
    "\u25cf Carpetas compartidas (VirtioFS):":
        "\u25cf Shared folders (VirtioFS):",
    "    - {0}: no aplica (VM apagada).":
        "    - {0}: not applicable (VM powered off).",
    "    - {0}: virtiofsd activo (PID {1}).":
        "    - {0}: virtiofsd active (PID {1}).",
    "    - {0}: NO está activo. Revisa {1} si "
    "esperabas que funcionara.":
        "    - {0}: NOT active. Check {1} if "
        "you expected it to work.",
    "Limpiar procesos huérfanos": "Clean orphan processes",
    "No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores.":
        "No QEMU/virtiofsd processes hanging from previous sessions were found.",
    "VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):":
        "VMs with QEMU running (not touched here, use 'Stop VM' if you want to power them off):",
    "  - {0} (PID {1})": "  - {0} (PID {1})",
    "Procesos virtiofsd huérfanos encontrados:":
        "Orphan virtiofsd processes found:",
    "  - {0}: virtiofsd PID {1}": "  - {0}: virtiofsd PID {1}",
    "Se detuvieron {0} proceso(s) huérfano(s).":
        "{0} orphan process(es) were stopped.",
    "\n\nNo se pudieron detener:\n":
        "\n\nCould not be stopped:\n",
    "Nada que limpiar.": "Nothing to clean.",
    "Virtualización: sin comprobar": "Virtualization: unchecked",
    "Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema.":
        "Press 'Check dependencies' to run the full system diagnostic.",
    "Distribución: {0}": "Distribution: {0}",
    "Gestor de paquetes: {0}": "Package manager: {0}",
    "no encontrado": "not found",
    "firmware disponible": "firmware available",
    "sin plantilla Secure Boot": "no Secure Boot template",
    "módulos": "modules",
    "módulo no cargado": "module not loaded",
    "OK": "OK",
    "FALTA": "MISSING",
    " ({0})": " ({0})",
    "SIN COMPROBAR": "UNCHECKED",
    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | "
    "TPM {4} | Audio {5} | GPU {6}":
        "Virtualization: {0} | QEMU {1} | KVM {2} | OVMF {3} | "
        "TPM {4} | Audio {5} | GPU {6}",
    "REVISAR": "CHECK",
    "Distribución: {0}\n"
    "Gestor de paquetes: {1}\n"
    "Secure Boot: {2}\n"
    "VirtIO: {3}\n"
    "Audio: {4}\n"
    "GPU: {5}\n"
    "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}":
        "Distribution: {0}\n"
        "Package manager: {1}\n"
        "Secure Boot: {2}\n"
        "VirtIO: {3}\n"
        "Audio: {4}\n"
        "GPU: {5}\n"
        "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}",
    "disponible": "available",
    "no disponible": "not available",
    "no detectado": "not detected",
    "sí": "yes",
    "no": "no",
    "Dependencias": "Dependencies",
    "La comprobación/reparación terminó correctamente.":
        "The check/repair completed successfully.",
    "No se pudieron reparar todas las dependencias.\n\n{0}":
        "Not all dependencies could be repaired.\n\n{0}",

    # i18n_tanda3_diagnostics_v1

    # ============================================================
    # Tanda 3.3: passthrough_mixin.py (cierre)
    # ============================================================

    # --- IOMMU / VT-d: RuntimeError de preparación ---
    "El procesador no se identificó como Intel; no se aplicará intel_iommu=on.":
        "The processor was not identified as Intel; intel_iommu=on will not be applied.",
    "No pude identificar de forma segura el gestor de arranque.":
        "Could not safely identify the boot manager.",
    "La preparación automática está implementada actualmente para GRUB. "
    "Gestor detectado: {0}.":
        "Automatic preparation is currently implemented for GRUB. "
        "Detected manager: {0}.",
    "No se pudo leer {0}.": "Could not read {0}.",
    "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub.":
        "GRUB_CMDLINE_LINUX_DEFAULT was not found in /etc/default/grub.",
    "intel_iommu=on ya está presente en /etc/default/grub.":
        "intel_iommu=on is already present in /etc/default/grub.",
    "operación cancelada": "operation cancelled",
    "Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ":
        "/etc/default/grub was modified, but grub.cfg could not be regenerated: ",
    "error desconocido": "unknown error",
    "Se añadió intel_iommu=on y se regeneró GRUB.":
        "intel_iommu=on was added and GRUB was regenerated.",

    # --- IOMMU / VT-d: UI ---
    "IOMMU / VT-d": "IOMMU / VT-d",
    "El IOMMU ya aparece activo. No es necesario modificar el arranque.":
        "IOMMU already appears active. No need to modify boot.",
    "No se identificó un CPU Intel.": "No Intel CPU was identified.",
    "Preparar Intel IOMMU": "Prepare Intel IOMMU",
    "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\n"
    "Se hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\n"
    "Esto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\n"
    "Gestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?":
        "intel_iommu=on will be added to the boot manager configuration.\n\n"
        "A backup will be made before modifying it and administrative authorisation will be requested.\n\n"
        "This does NOT enable VT-d inside BIOS/UEFI; that part must be enabled in the firmware.\n\n"
        "Detected manager: {0}\nFile: {1}\n\nContinue?",
    "no identificado": "not identified",
    "Configuración actualizada.": "Configuration updated.",
    "\n\nReinicia el equipo para que el parámetro tenga efecto.":
        "\n\nReboot the computer for the parameter to take effect.",
    "No se pudo preparar IOMMU": "Could not prepare IOMMU",
    "Abrir UEFI/BIOS": "Open UEFI/BIOS",
    "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\n"
    "Busca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?":
        "The computer will reboot directly to the firmware configuration if the system allows it.\n\n"
        "Look for an option called Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d or similar and enable it.\n\nReboot now?",
    "No se pudo solicitar el reinicio al firmware.":
        "Could not request firmware reboot.",
    "No se pudo abrir UEFI/BIOS": "Could not open UEFI/BIOS",

    # --- Estados del IOMMU ---
    "Desactivado por parámetro del kernel": "Disabled by kernel parameter",
    "Activo": "Active",
    "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles":
        "VT-d detected by firmware/kernel; IOMMU without visible groups",
    "No detectado": "Not detected",
    "Detectado": "Detected",
    "No confirmado": "Not confirmed",

    # --- Estados del tree PCI ---
    "\u2713 Listo para VFIO": "\u2713 Ready for VFIO",
    "\u26a0 Sin grupo IOMMU": "\u26a0 No IOMMU group",
    "\u26a0 Comparte grupo IOMMU": "\u26a0 Shares IOMMU group",
    "\u26a0 Requiere preparación VFIO": "\u26a0 VFIO preparation required",

    # --- _pci_preflight ---
    "IOMMU/Intel VT-d: {0}": "IOMMU/Intel VT-d: {0}",
    "Firmware/ACPI DMAR: {0}": "Firmware/ACPI DMAR: {0}",
    "Grupos IOMMU: {0}": "IOMMU groups: {0}",
    "{0}: no tiene grupo IOMMU ({1})": "{0}: has no IOMMU group ({1})",
    "{0}: comparte grupo IOMMU {1} con {2}":
        "{0}: shares IOMMU group {1} with {2}",
    "{0}: driver actual {1}; todavía no está ligado a vfio-pci":
        "{0}: current driver {1}; not yet bound to vfio-pci",
    "\u2022 {0} | grupo {1} | driver {2}":
        "\u2022 {0} | group {1} | driver {2}",

    # --- refresh_vfio_diagnostics ---
    "\u2705 Intel VT-d / IOMMU activo":
        "\u2705 Intel VT-d / IOMMU active",
    "\u26a0 VT-d detectado por firmware, pero no hay grupos IOMMU utilizables":
        "\u26a0 VT-d detected by firmware, but no usable IOMMU groups",
    "\u274c Intel VT-d / IOMMU no detectado":
        "\u274c Intel VT-d / IOMMU not detected",
    "(sin datos)": "(no data)",
    "<b>{0}</b><br>"
    "Firmware/ACPI DMAR: {1}<br>"
    "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>"
    "Gestor de arranque: {4}<br>"
    "Parámetros kernel: <code>{5}</code>":
        "<b>{0}</b><br>"
        "Firmware/ACPI DMAR: {1}<br>"
        "IOMMU groups: {2} &nbsp;|&nbsp; PCI ready for VFIO: {3}<br>"
        "Boot manager: {4}<br>"
        "Kernel parameters: <code>{5}</code>",
    "Desconocido": "Unknown",
    "<br>\u26a0 El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.":
        "<br>\u26a0 The CPU was not identified as Intel; check AMD/IOMMU diagnostic.",
    "<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. "
    "Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.":
        "<br>Recommendation: use <b>Prepare intel_iommu=on</b> and reboot. "
        "If there are still no groups after rebooting, check VT-d in BIOS/UEFI.",
    "<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar "
    "<code>intel_iommu=on</code> en el arranque.":
        "<br>Recommendation: enable Intel VT-d in BIOS/UEFI and then activate "
        "<code>intel_iommu=on</code> at boot.",

    # --- _vfio_diagnostic_text ---
    "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===":
        "=== INTEL VT-d / IOMMU / VFIO DIAGNOSTIC ===",
    "Estado: {0}": "State: {0}",
    "Arquitectura: {0}": "Architecture: {0}",
    "desconocida": "unknown",
    "CPU Intel detectado: {0}": "Intel CPU detected: {0}",
    "intel_iommu=on en kernel actual: {0}":
        "intel_iommu=on in current kernel: {0}",
    "IOMMU desactivado por parámetro: {0}":
        "IOMMU disabled by parameter: {0}",
    "Clases IOMMU: {0}": "IOMMU classes: {0}",
    "Gestor de arranque: {0}": "Boot manager: {0}",
    "desconocido": "unknown",
    "Configuración: {0}": "Configuration: {0}",
    "no identificada": "not identified",
    "Parámetros kernel: {0}": "Kernel parameters: {0}",
    "=== DISPOSITIVOS PCI ===": "=== PCI DEVICES ===",
    "{0} | {1} | driver={2} | grupo={3} | estado={4}":
        "{0} | {1} | driver={2} | group={3} | status={4}",
    "sin driver": "no driver",

    # --- copy_vfio_diagnostic / vfio_diagnostic_details ---
    "Diagnóstico VFIO": "VFIO diagnostic",
    "Diagnóstico copiado al portapapeles.":
        "Diagnostic copied to clipboard.",
    "No se pudo copiar el diagnóstico":
        "Could not copy the diagnostic",
    "Diagnóstico Intel VT-d / IOMMU / VFIO":
        "Intel VT-d / IOMMU / VFIO diagnostic",
    "\U0001f4cb Copiar": "\U0001f4cb Copy",

    # --- USB: errores de preparación ---
    "No existe {0}. El número Device puede haber cambiado; "
    "vuelve a detectar USB.":
        "{0} does not exist. The Device number may have changed; "
        "detect USB again.",
    "Sin acceso de lectura/escritura a {0}.":
        "No read/write access to {0}.",
    "No se encontró 'pkexec'. No puedo solicitar permisos "
    "administrativos automáticamente.":
        "'pkexec' was not found. Cannot request administrative "
        "permissions automatically.",
    "No se pudo ejecutar la acción administrativa ({0}): {1}":
        "Could not execute the administrative action ({0}): {1}",
    "No se pudo realizar la acción administrativa ({0}). {1}":
        "Could not perform the administrative action ({0}). {1}",
    "No existe el nodo USB actual {0}; el dispositivo "
    "pudo cambiar de dirección.":
        "The current USB node {0} does not exist; the device "
        "may have changed address.",
    "(desconocido)": "(unknown)",
    "dar acceso temporal al dispositivo USB":
        "grant temporary access to the USB device",
    "No pude desmontar automáticamente el almacenamiento USB:\n"
    "{0}\n\n{1}":
        "Could not automatically unmount the USB storage:\n"
        "{0}\n\n{1}",
    "El USB sigue sin acceso después de preparar el dispositivo: {0}":
        "The USB still has no access after preparing the device: {0}",
    "USB {0} | nodo: {1} | acceso usuario: {2} | {3}":
        "USB {0} | node: {1} | user access: {2} | {3}",
    "NO": "NO",
    "no se pudo leer ({0})": "could not be read ({0})",
    "error al comprobar: {0}": "error checking: {0}",

    # --- Permisos USB ---
    "\u2705 Permisos USB: OK ({0}). El passthrough en caliente "
    "no pedirá contraseña.":
        "\u2705 USB permissions: OK ({0}). Hotplug passthrough "
        "will not ask for a password.",
    "Los permisos USB ya están configurados.\n"
    "Si quieres desinstalarlos, borra:\n"
    "{0}":
        "USB permissions are already configured.\n"
        "If you want to uninstall them, delete:\n"
        "{0}",
    "\u26a0 Permisos USB: {0}. El passthrough en caliente "
    "pedirá contraseña cada vez.":
        "\u26a0 USB permissions: {0}. Hotplug passthrough "
        "will ask for a password every time.",
    "Permisos USB": "USB permissions",
    "No se encontró 'pkexec'. Instálalo (paquete 'polkit') para "
    "que la aplicación pueda solicitar permisos administrativos "
    "de forma gráfica.":
        "'pkexec' was not found. Install it (package 'polkit') so "
        "the application can request administrative permissions "
        "graphically.",
    "No se encontró 'udevadm'. Este sistema parece no usar udev "
    "para gestionar dispositivos USB. Aplica los permisos "
    "manualmente según tu distribución.":
        "'udevadm' was not found. This system does not appear to use udev "
        "to manage USB devices. Apply permissions "
        "manually according to your distribution.",
    "Configurar permisos USB": "Configure USB permissions",
    "La operación tardó demasiado. Vuelve a intentarlo.":
        "The operation took too long. Please try again.",

    # --- Menú Medios: CD/DVD ---
    "Dispositivo USB inválido.": "Invalid USB device.",
    "\U0001f4c0 Unidades ópticas": "\U0001f4c0 Optical drives",
    "      (Sin unidades CD/DVD)": "      (No CD/DVD drives)",
    "\U0001f310 descargar instalador al iniciar":
        "\U0001f310 download installer on start",
    "\U0001f310 descargar Recovery al iniciar":
        "\U0001f310 download Recovery on start",
    "   \U0001f4c0 {0} \u2014 {1}": "   \U0001f4c0 {0} \u2014 {1}",
    "\U0001f4c2 Cambiar medio\u2026":
        "\U0001f4c2 Change medium\u2026",
    "\u23cf Expulsar medio": "\u23cf Eject medium",

    # --- Menú Medios: USB ---
    "\U0001f50c Dispositivos USB":
        "\U0001f50c USB devices",
    "      (La VM debe estar encendida para conectarlos)":
        "      (The VM must be running to connect them)",
    "      Error al detectar USB: {0}":
        "      Error detecting USB: {0}",
    "      (No hay dispositivos USB detectados)":
        "      (No USB devices detected)",
    "conectado a la VM": "connected to the VM",
    "disponible en el host": "available on the host",
    "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
    "Estado: {5}\n\n{6}":
        "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
        "State: {5}\n\n{6}",
    "Clic para DESCONECTAR de la VM":
        "Click to DISCONNECT from the VM",
    "Clic para CONECTAR a la VM":
        "Click to CONNECT to the VM",
    "(Selecciona una VM primero)": "(Select a VM first)",
    "\U0001f4bf Medios de '{0}'": "\U0001f4bf Media of '{0}'",
    "\U0001f504 Refrescar": "\U0001f504 Refresh",
    "\u2699 Gestionar USB en Passthrough\u2026":
        "\u2699 Manage USB in Passthrough\u2026",

    # --- Tree passthrough ---
    "Grupo {0}": "Group {0}",
    "Sin grupo IOMMU": "No IOMMU group",
    " \u2022 {0}": " \u2022 {0}",
    "\u26a0 Revisar": "\u26a0 Review",
    "\u2713 Acceso OK": "\u2713 Access OK",
    "\u26a0 Revisar acceso": "\u26a0 Review access",

    # --- Passthrough USB: diálogos ---
    "Passthrough: teclado o ratón del host":
        "Passthrough: host keyboard or mouse",
    "Passthrough USB": "USB Passthrough",
    "Selecciona un dispositivo USB.":
        "Select a USB device.",
    "La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.":
        "The VM is not running; use Save selection to attach it on the next boot.",
    "Dispositivo USB conectado en caliente a la VM.\n\n"
    "Nota: el host debe permitir acceso a /dev/bus/usb y el "
    "dispositivo no debería estar siendo usado por el sistema "
    "anfitrión.":
        "USB device hot-plugged into the VM.\n\n"
        "Note: the host must allow access to /dev/bus/usb and the "
        "device should not be in use by the host system.",
    "Error al conectar USB": "Error connecting USB",
    "La VM no está encendida.": "The VM is not running.",
    "Solicitud de desconexión USB enviada a QEMU.":
        "USB disconnect request sent to QEMU.",
    "Error al desconectar USB": "Error disconnecting USB",

    # ================================================================
    # Tanda 4a-1: barrido de cadenas hardcodeadas en espanol
    # (i18n_tanda4_barrido_es_v1)
    # ================================================================
    "Sin grupo": "No group",
    "Resumen de Configuración": "Configuration summary",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Select a virtual machine from the list on the left.",

    # --- Passthrough: parrafo + VFIO ---
    "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.":
        "Hardware passthrough. PCI uses VFIO; USB uses usb-host over XHCI. The program will check access to /dev/bus/usb, automatically unmount the selected USB storage from the host, and request administrative permissions only when necessary. Do not select Root Hubs.",
    "Diagnóstico PCI / VFIO": "PCI / VFIO diagnostics",
    "Comprobando Intel VT-d / IOMMU...":
        "Checking Intel VT-d / IOMMU...",
    "\U0001f504 Comprobar IOMMU / VFIO":
        "\U0001f504 Check IOMMU / VFIO",
    "\u2139 Ver diagnóstico detallado":
        "\u2139 View detailed diagnostics",
    "\U0001f6e0 Preparar intel_iommu=on":
        "\U0001f6e0 Prepare intel_iommu=on",
    "\u2699 Abrir UEFI/BIOS":
        "\u2699 Open UEFI/BIOS",

    # --- Permisos USB del host ---
    "Permisos USB del host": "Host USB permissions",
    "Para poder pasar memorias o discos USB a la VM sin pedir contraseña cada vez, el sistema necesita una regla udev que conceda acceso al usuario activo. Puedes instalarla aquí con un clic; solo se aplica a esta categoría de dispositivos.":
        "To pass USB sticks or disks to the VM without being asked for a password each time, the system needs a udev rule that grants access to the active user. You can install it here with one click; it only applies to this category of devices.",
    "\U0001f504 Comprobar":
        "\U0001f504 Check",
    "\U0001f527 Configurar permisos USB":
        "\U0001f527 Configure USB permissions",
    "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\nque permite el acceso a los dispositivos USB al usuario activo.\nSolo se toca este archivo; el resto de la configuración USB\ndel sistema no se modifica.":
        "Creates /etc/udev/rules.d/50-vm-manager-usb.rules with the rule\nthat grants access to USB devices to the active user.\nOnly this file is touched; the rest of the system's USB\nconfiguration is left untouched.",

    # --- Passthrough: tabla + botones inferiores ---
    "Usar": "Use",
    "IOMMU / Driver": "IOMMU / Driver",
    "\U0001f504 Detectar dispositivos":
        "\U0001f504 Detect devices",
    "\U0001f4be Guardar selección":
        "\U0001f4be Save selection",
    "\U0001f50c Conectar USB en caliente":
        "\U0001f50c Hotplug USB",
    "\u23cf Desconectar USB":
        "\u23cf Unplug USB",

    # --- Configuracion Host: subtitulo ---
    "Ajustes y diagnostico del sistema anfitrion. Nada de esta seccion se guarda con la VM: aplica a todo el equipo.":
        "Host system settings and diagnostics. None of this section is stored with the VM: it applies to the whole machine.",

    # --- Backups: cabecera de la pestana ---
    "<b>Backups de la maquina virtual</b><br><span style='color:#666;font-size:11px;'>Copia periodica de la carpeta completa (discos + config + snapshots). El backup se guarda como carpeta independiente; se puede restaurar con el boton <b>Importar</b> de la pestana Resumen apuntando a la carpeta del backup.</span>":
        "<b>Virtual machine backups</b><br><span style='color:#666;font-size:11px;'>Periodic copy of the full folder (disks + config + snapshots). The backup is saved as an independent folder; it can be restored with the <b>Import</b> button on the Overview tab pointing to the backup folder.</span>",

    # ================================================================
    # Tanda 4a-2.1: Comparticion + Sugerencias + valores Storage
    # (i18n_tanda4a2_1_v1)
    # ================================================================
    "Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).":
        "Host ↔ Guest integration. Shared folders and clipboard are configured here.",
    "Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.":
        "Share host directories with the guest. Automatic uses VirtioFS on Linux when virtiofsd is available, 9p as a fallback and SMB for Windows/macOS. Read-only prevents the guest from modifying host files.",
    "Dependencias del host": "Host dependencies",
    "VirtioFS: SIN COMPROBAR": "VirtioFS: UNCHECKED",
    "9p: SIN COMPROBAR": "9p: UNCHECKED",
    "SMB: SIN COMPROBAR": "SMB: UNCHECKED",
    "9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.":
        "9p is part of QEMU and normally does not require installing an extra package on the host. VirtioFS needs virtiofsd and SMB needs Samba/smbd.",
    "🛠️ Instalar faltantes": "🛠️ Install missing",
    "Host": "Host",
    "Guest / etiqueta": "Guest / label",
    "Método": "Method",
    "Montaje en el guest": "Mount in guest",
    "Acceso": "Access",
    "➕ Agregar": "➕ Add",
    "✏ Modificar": "✏ Modify",
    "💾 Guardar": "💾 Save",
    "Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.":
        "Guest Tools bundles the guest system integration: QEMU Guest Agent, VirtIO drivers and, on Windows, SPICE components. The ISO can be mounted as a CD/DVD on any VM.",
    "QEMU Guest Agent": "QEMU Guest Agent",
    "Activar canal QEMU Guest Agent al iniciar la VM":
        "Enable QEMU Guest Agent channel on VM start",
    "Canal:": "Channel:",
    "Estado: no comprobado": "Status: not checked",
    "🔎 Probar conexión": "🔎 Test connection",
    "💿 Crear / actualizar ISO Guest Tools":
        "💿 Create / update Guest Tools ISO",
    "🧰 Adjuntar a esta VM": "🧰 Attach to this VM",
    "Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.":
        "Creates the ISO if missing and attaches it as a CD/DVD to the selected VM, in a single step.",
    "📂 Abrir carpeta de Guest Tools": "📂 Open Guest Tools folder",
    "Acciones:": "Actions:",
    "Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.":
        "Linux: install qemu-guest-agent from this ISO or from the package manager. Windows: INSTALL-WINDOWS.CMD downloads and installs VirtIO Guest Tools and SPICE Guest Tools from their official sources. Then reboot the guest.",
    "Compartir clipboard": "Share clipboard",
    "Desactivado": "Disabled",
    "Host → SO invitado": "Host → Guest OS",
    "SO invitado → Host": "Guest OS → Host",
    "Bidireccional": "Bidirectional",
    "Dirección:": "Direction:",
    "Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.":
        "Linux and Windows: QEMU vdagent + VirtIO/SPICE channel and GTK will be used for bidirectional clipboard. The guest must have spice-vdagent (Linux) or SPICE Guest Tools (Windows). macOS will be tested in a specific phase.",
    "💾 Guardar configuración": "💾 Save configuration",
    "Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.":
        "Per-VM configuration. The concrete mechanism will be chosen according to the guest OS and its integration support.",
    "Compartir Carpetas": "Share Folders",
    "Clipboard": "Clipboard",
    "💽 Disco Duro": "💽 Hard disk",
    "Disco": "Disk",
    "💾 Disquetera": "💾 Floppy drive",
    "FDC": "FDC",
    "📀 Unidades ópticas": "📀 Optical drives",
    "🌐 Descargar instalador de Internet al iniciar":
        "🌐 Download installer from the Internet on start",
    "🌐 Instalador por Internet (se descargará al iniciar)":
        "🌐 Internet installer (will be downloaded on start)",
    "🌐 Descargar System Recovery al iniciar":
        "🌐 Download System Recovery on start",
    "🌐 System Recovery (se descargará al iniciar)":
        "🌐 System Recovery (will be downloaded on start)",
    "vacío": "empty",
    "Sin medio": "No medium",
    "🌐 descarga": "🌐 download",
    "🌐 descargar instalador al iniciar": "🌐 download installer on start",
    "🌐 descargar System Recovery al iniciar":
        "🌐 download System Recovery on start",
    "💡 Sugerencias": "💡 Suggestions",

    # ================================================================
    # Tanda 4a-2.2: Consola Grafica + Consola de Progreso
    # (i18n_tanda4a2_2_v1)
    # ================================================================
    "La VM no está corriendo.": "The VM is not running.",
    "↗ Abrir en ventana externa": "↗ Open in external window",
    "Lanza el visor externo del protocolo configurado en Pantalla,\naunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez.":
        "Launches the external viewer for the protocol configured in Display,\neven if the mode is 'embedded'. Useful to have both views at once.",
    "Externos en pantalla completa": "External viewers in fullscreen",
    "Cuando está marcado, los visores externos (los que abre el\nbotón 'Abrir en ventana externa' o el modo 'Ventana externa'\nde Configuración → Pantalla) se lanzan ocupando toda la\npantalla. NO afecta al visor embebido (VNC dentro de la app):\npara ese, usa el botón 'Pantalla completa del visor'.":
        "When checked, external viewers (opened by the\n'Open in external window' button or the 'External window'\nmode in Settings → Display) launch fullscreen.\nIt does NOT affect the embedded viewer (VNC inside the app):\nfor that one, use the 'Viewer fullscreen' button.",
    "💿 Medios": "💿 Media",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\nMismo menú que el botón 'Medios' de la pestaña Resumen.\nAtajo: Ctrl+M.":
        "VM media: CD/DVD drives and USB devices.\nSame menu as the 'Media' button on the Overview tab.\nShortcut: Ctrl+M.",
    "🔄 Reconectar": "🔄 Reconnect",
    "Reconectar el widget VNC.\nÚtil si cambiaste la resolución del guest y la imagen\nquedó recortada o mal escalada. El cliente VNC básico\nno puede cambiar el tamaño de su framebuffer sin\nreconectar.\n\nAtajo: Ctrl+R.":
        "Reconnect the VNC widget.\nUseful if you changed the guest resolution and the image\nwas cropped or badly scaled. The basic VNC client\ncannot resize its framebuffer without\nreconnecting.\n\nShortcut: Ctrl+R.",
    "Zoom:": "Zoom:",
    "🔍−": "🔍−",
    "Reducir el zoom del visor embebido.\nEscalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Reduce the embedded viewer zoom.\nSteps: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "Ajustado": "Fit",
    "🔍+": "🔍+",
    "Aumentar el zoom del visor embebido.\nEscalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Increase the embedded viewer zoom.\nSteps: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "⊞ Ajustar": "⊞ Fit",
    "Ajustar la imagen de la VM al tamaño del widget (escala\nautomática). La VM se ve entera, sin barras de scroll.\nSi la relación de aspecto no coincide, aparecen bandas\nnegras a los lados.":
        "Fit the VM image to the widget size (automatic\nscaling). The VM is fully visible, no scroll bars.\nIf the aspect ratio does not match, black bands\nappear on the sides.",
    "1:1 Tamaño real": "1:1 Actual size",
    "Mostrar la imagen de la VM a su resolución real (100%).\nSi no cabe en la ventana, aparecen barras de scroll.":
        "Show the VM image at its actual resolution (100%).\nIf it does not fit in the window, scroll bars appear.",
    "🎬 Presentación": "🎬 Presentation",
    "Modo presentación: oculta los paneles laterales, entra\nen pantalla completa y salta a la Consola Gráfica.\nRequiere que la VM esté encendida.\n\nAtajo: F11. Para salir: F11 o Escape.":
        "Presentation mode: hides the side panels, enters\nfullscreen and jumps to the Graphical Console.\nRequires the VM to be running.\n\nShortcut: F11. To exit: F11 or Escape.",
    "⛶ Pantalla completa del visor": "⛶ Viewer fullscreen",
    "Salir con:": "Exit with:",
    "Ctrl derecho (como VirtualBox)": "Right Ctrl (like VirtualBox)",
    "Ctrl+Alt+Intro": "Ctrl+Alt+Enter",
    "Combinación de teclas para salir de la pantalla completa del visor embebido.\nEvita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\nusar Escape o F11 dentro del sistema invitado, no la uses aquí).":
        "Key combination to exit embedded-viewer fullscreen.\nAvoid choosing a key you may need to send inside the VM (e.g. if you plan to\nuse Escape or F11 inside the guest, do not use it here).",
    "<b>ℹ️ Notas sobre Android en QEMU/KVM</b>":
        "<b>ℹ️ Notes about Android on QEMU/KVM</b>",

    # --- Consola de Progreso ---
    "🩺 Salud de la VM": "🩺 VM health",
    "Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.":
        "Checks at a glance whether the VM is really running, whether the Guest Agent responds and whether shared folders mounted.",
    "🚦 Semáforos": "🚦 Traffic lights",
    "🧹 Limpiar procesos huérfanos": "🧹 Clean orphan processes",
    "Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.":
        "Looks for QEMU/virtiofsd/swtpm processes left hanging from a previous session (due to a forced close) and offers to stop them.",
    "Nivel:": "Level:",
    "Todo": "All",
    "Avisos+": "Warnings+",
    "Errores": "Errors",
    "🔍 Filtrar...": "🔍 Filter...",
    "Auto-scroll": "Auto-scroll",
    "📄 Ver log completo": "📄 View full log",
    "Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.":
        "Shows the full history saved on disk for this VM (launch.log), not just what fits in this window.",
    "💾 Exportar log": "💾 Export log",
    "Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.":
        "Saves the full log of this VM to a file, useful for asking for help or reporting an issue.",
    "Limpiar consola": "Clear console",
    "Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').":
        "Clears the messages shown here (the full history on disk is untouched; use 'View full log').",

    # ================================================================
    # Tanda 4a-2.3: Snapshots (Si/No + info) + Media Library (tipo + botones)
    # (i18n_tanda4a2_3_v1)
    # ================================================================
    "Desconocido": "Unknown",
    "(solo disco)": "(disk-only)",
    "Sí": "Yes",
    "No": "No",
    "💽 SATA": "💽 SATA",
    "⚡ NVMe": "⚡ NVMe",
    "❌ No hay un QCOW2 escribible disponible para snapshots completos de VM.":
        "❌ There is no writable QCOW2 available for full VM snapshots.",
    "✅ Disco para estado de VM: {0} · tamaño virtual: {1} · archivo actual: {2} · espacio libre del sistema de archivos: {3} · reserva orientativa inicial: {4}. El snapshot QCOW2 crece según se modifican bloques.":
        "✅ Disk for VM state: {0} · virtual size: {1} · current file: {2} · filesystem free space: {3} · initial estimate reserve: {4}. The QCOW2 snapshot grows as blocks change.",
    "⚠ {0} El snapshot podría fallar al quedarse sin espacio.":
        "⚠ {0} The snapshot may fail if it runs out of space.",
    "↗ Agrandar": "↗ Enlarge",
    "🗜 Compactar": "🗜 Compact",
    "Verificar": "Verify",
    "Calcular SHA256": "Compute SHA256",
    "Editar": "Edit",
    "Eliminar": "Delete",
    "Abrir carpeta": "Open folder",
    "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\nbiblioteca. Requiere que ninguna VM lo esté usando en\nese momento. El disco solo puede crecer.":
        "Increase the virtual size of a QCOW2/RAW disk in the\nlibrary. Requires no VM is currently using it. The disk\ncan only grow.",
    # i18n_tanda4a2_4_dict_fix1
    "Reescribe el QCOW2 sin bloques no usados, reduciendo el\narchivo en el host. No cambia el tamaño virtual que ve el\nsistema invitado.":
        "Rewrites the QCOW2 without unused blocks, reducing the\nfile on the host. Does not change the virtual size the\nguest system sees.",
    "Comprueba que el archivo exista en disco y, si hay sha256 calculado, que coincida.":
        "Checks that the file exists on disk and, if a sha256 has been computed, that it matches.",
    "Calcula el sha256 del archivo (tarda segun el tamano). Util para detectar duplicados o descargas corruptas.":
        "Computes the file's sha256 (takes time depending on size). Useful to detect duplicates or corrupted downloads.",
    "Edita los metadatos de la entrada: nombre, distro, version, arquitectura, notas, tags y color.":
        "Edits the entry metadata: name, distro, version, architecture, notes, tags and color.",
    "Elimina la entrada del indice. Opcionalmente borra tambien el archivo del disco (solo si vive dentro de MediaLibrary/).":
        "Deletes the entry from the index. Optionally also removes the file from disk (only if it lives inside MediaLibrary/).",
    "Abre la carpeta que contiene el archivo en el explorador del sistema.":
        "Opens the folder containing the file in the system file manager.",

    # ================================================================
    # Tanda 4a-2.4: valores dinamicos del panel derecho
    # (i18n_tanda4a2_4_v1)
    # ================================================================
    "Guest Agent: —": "Guest Agent: —",
    "Carpetas: —": "Folders: —",
    "Clipboard: —": "Clipboard: —",
    "spice-vdagent: —": "spice-vdagent: —",
    "Guest Agent: apagado": "Guest Agent: off",
    "Carpetas: apagado": "Folders: off",
    "Clipboard: apagado": "Clipboard: off",
    "spice-vdagent: apagado": "spice-vdagent: off",
    "Guest Agent: {0}": "Guest Agent: {0}",
    "activo": "active",
    "sin respuesta": "no response",
    "Carpetas: {0}": "Folders: {0}",
    "OK": "OK",
    "con problemas": "with problems",
    "Clipboard: activo": "Clipboard: active",
    "Clipboard: desactivado": "Clipboard: disabled",
    "spice-vdagent: activo": "spice-vdagent: active",
    "spice-vdagent: no detectado": "spice-vdagent: not detected",
    "Ctrl derecho": "Right Ctrl",
    "Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\ncompleta en una ventana propia. NO afecta al visor externo:\npara ese, usa el checkbox 'Externos en pantalla completa'\nde la fila de estado.\n\nPulsa {0} para salir.":
        "Shows the EMBEDDED viewer (VNC inside the app) fullscreen\nin its own window. It does NOT affect the external viewer:\nfor that one, use the 'External viewers in fullscreen' checkbox\nin the status row.\n\nPress {0} to exit.",
    "▶ Reanudar": "▶ Resume",
    "Reanudar la VM pausada. Usa la flecha para más opciones:\n• Pausar (rápido): detiene sin guardar el estado en disco.\n• Reanudar: vuelve a ejecutar la VM.\n• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Resumes the paused VM. Use the arrow for more options:\n• Pause (quick): stops without saving state to disk.\n• Resume: runs the VM again.\n• Take Snapshot: saves state to disk and pauses.",
    "⏸ Pausar": "⏸ Pause",
    "Pausar la VM. Usa la flecha para más opciones:\n• Pausar (rápido): detiene sin guardar el estado en disco.\n• Reanudar: vuelve a ejecutar la VM pausada.\n• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Pauses the VM. Use the arrow for more options:\n• Pause (quick): stops without saving state to disk.\n• Resume: runs the paused VM again.\n• Take Snapshot: saves state to disk and pauses.",
    "● Sin VM seleccionada": "● No VM selected",
    "Iniciar VM": "Start VM",
    "Selecciona una máquina virtual.": "Select a virtual machine.",
    "Pausar": "Pause",
    "La máquina virtual no está corriendo.": "The virtual machine is not running.",
    "Control de VM": "VM control",
    "No se pudo cambiar el estado de la VM.\n\n{0}":
        "Could not change the VM state.\n\n{0}",
    "No se pudo pausar la VM.\n\n{0}":
        "Could not pause the VM.\n\n{0}",
    "Reanudar": "Resume",
    "La máquina virtual ya está corriendo.": "The virtual machine is already running.",
    "La máquina virtual no está pausada: no hay nada que reanudar.":
        "The virtual machine is not paused: nothing to resume.",
    "No se pudo reanudar la VM.\n\n{0}":
        "Could not resume the VM.\n\n{0}",
    "Apagar VM": "Shut down VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Could not send the shutdown command.\n\n{0}",
    "Reiniciar VM": "Reboot VM",
    "No se pudo enviar la orden de reinicio.\n\n{0}":
        "Could not send the reboot command.\n\n{0}",
    "Forzar apagado": "Force shutdown",
    "Esto corta la VM de inmediato, sin avisar al sistema operativo invitado (como desenchufar un equipo real).\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "This cuts the VM immediately, without warning the guest OS (like unplugging a real machine).\n\nIt may cause loss of unsaved data inside the VM.\n\nDo you want to continue?",
    "Forzar reinicio": "Force reboot",
    "Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin avisar al sistema operativo invitado.\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "This cuts the VM immediately and restarts it from scratch, without warning the guest OS.\n\nIt may cause loss of unsaved data inside the VM.\n\nDo you want to continue?",

    # ================================================================
    # Tanda 4a-2.5: Dialogos de botones del Resumen
    # (i18n_tanda4a2_5_1_v1)
    # ================================================================
    # --- compare_defaults_mixin ---
    "Comparar con defaults": "Compare with defaults",
    "Selecciona primero una máquina virtual.":
        "Select a virtual machine first.",
    "No se pudo determinar el perfil del SO seleccionado.":
        "The selected OS profile could not be determined.",
    "Firmware": "Firmware",
    "Chipset": "Chipset",
    "CPU (modelo)": "CPU (model)",
    "Núcleos": "Cores",
    "Gráficos": "Graphics",
    "VRAM": "VRAM",
    "Audio": "Audio",
    "Señalización (ratón/teclado)": "Pointer (mouse/keyboard)",
    "Consola: protocolo": "Console: protocol",
    "Consola: modo": "Console: mode",
    "Comparación de <b>{0}</b> con los valores por defecto del perfil del SO seleccionado. Las filas con fondo amarillo difieren del default.<br><br>Aplicar un default <b>no</b> guarda la VM: solo cambia el widget. Persiste con <b>Guardar</b> (en Configuración) o al iniciar la VM.":
        "Comparison of <b>{0}</b> with the default values of the selected OS profile. Rows with a yellow background differ from the default.<br><br>Applying a default does <b>not</b> save the VM: it only changes the widget. Persist with <b>Save</b> (in Settings) or when starting the VM.",
    "Campo": "Field",
    "Actual": "Current",
    "Por defecto": "Default",
    "<b>{0}</b> diferencia(s) de <b>{1}</b> campo(s).":
        "<b>{0}</b> difference(s) out of <b>{1}</b> field(s).",
    "Aplicar al campo seleccionado": "Apply to selected field",
    "Aplicar todos los defaults": "Apply all defaults",
    "Aplicar": "Apply",
    "Selecciona primero una fila.": "Select a row first.",
    "==> Comparar defaults: aplicados {0} campo(s) a '{1}'.":
        "==> Compare defaults: {0} field(s) applied to '{1}'.",

    # --- vm_templates_mixin ---
    "Guardar como plantilla": "Save as template",
    "Esta VM no tiene vm_config.ini todavía.\n\nConfigúrala y guárdala primero.":
        "This VM does not have a vm_config.ini yet.\n\nConfigure and save it first.",
    "Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?":
        "Template '{0}' already exists.\n\nOverwrite it?",
    "No se pudo escribir la plantilla.\n\n{0}":
        "Could not write the template.\n\n{0}",
    "Plantilla guardada": "Template saved",
    "Plantilla '{0}' creada correctamente.\n\nAparecerá en el menú del botón '➕ Nueva VM'.":
        "Template '{0}' created successfully.\n\nIt will appear in the '➕ New VM' button menu.",
    "🆕 Nueva VM en blanco": "🆕 New blank VM",
    "Desde plantilla:": "From template:",
    "Crear desde plantilla": "Create from template",
    "No encuentro la plantilla '{0}'.": "Template '{0}' not found.",
    "Ya existe una carpeta para '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "A folder for '{0}' already exists.\n\nReplace it? (the existing one will be deleted)",
    "No se pudo eliminar la carpeta existente.\n\n{0}":
        "Could not delete the existing folder.\n\n{0}",
    "No se pudo crear la VM.\n\n{0}": "Could not create the VM.\n\n{0}",
    "VM creada": "VM created",
    "VM '{0}' creada desde la plantilla '{1}'.\n\nSe ha abierto en Configuración → Almacenamiento para que\nañadas el disco y el medio de instalación. La MAC de red se\nha regenerado para evitar conflictos con otras VMs.":
        "VM '{0}' created from template '{1}'.\n\nIt has been opened in Settings → Storage so that\nyou can add the disk and the installation medium. The network MAC has\nbeen regenerated to avoid conflicts with other VMs.",

    # ================================================================
    # Tanda 4a-2.5.3a: Dialogos OVF/OVA
    # (i18n_tanda4a2_5_3a_v1)
    # ================================================================
    # --- _ExportOvfDialog ---
    "Exportar como OVF/OVA - {0}": "Export as OVF/OVA - {0}",
    "Exporta <b>{0}</b> como OVA (un solo archivo) o como OVF (carpeta con descriptor + discos sueltos).":
        "Export <b>{0}</b> as OVA (single file) or as OVF (folder with descriptor + standalone disks).",
    "Formato del disco": "Disk format",
    "QCOW2 (recomendado) - instantaneo y comprimido":
        "QCOW2 (recommended) - instant and compressed",
    "El disco se aplana (descartando snapshots internos) y se comprime con zlib. Ideal para reimportar en esta misma app.":
        "The disk is flattened (discarding internal snapshots) and compressed with zlib. Ideal for reimporting in this same app.",
    "VMDK stream-optimized - maxima compatibilidad con VirtualBox/VMware":
        "VMDK stream-optimized - maximum compatibility with VirtualBox/VMware",
    "Requiere conversion previa con qemu-img. Tarda mas y necesita espacio temporal. VMDK stream-optimized ya descarta snapshots.":
        "Requires previous conversion with qemu-img. Takes longer and needs temporary space. VMDK stream-optimized already discards snapshots.",
    "Opciones adicionales": "Additional options",
    "Incluir medio de instalacion (BaseSystem.img)":
        "Include installation medium (BaseSystem.img)",
    "Incluir archivos ISO en el OVA":
        "Include ISO files in the OVA",
    "Cancelar": "Cancel",
    "Exportar": "Export",
    "El disco se convertira a <b>VMDK stream-optimized</b>. Este formato ya descarta los snapshots internos.":
        "The disk will be converted to <b>VMDK stream-optimized</b>. This format already discards internal snapshots.",
    "Los discos QCOW2 se <b>aplanan y comprimen</b> automaticamente al exportar: se descartan los snapshots internos y se aplica compresion zlib. Reduce el OVA entre un 40% y un 60%.":
        "QCOW2 disks are <b>flattened and compressed</b> automatically on export: internal snapshots are discarded and zlib compression is applied. Reduces the OVA by 40% to 60%.",

    # --- _OvfImportPreviewDialog ---
    "Importar OVF/OVA": "Import OVF/OVA",
    "Se ha leído el descriptor OVF. Revisa los datos detectados y corrige lo que haga falta antes de importar.<br><br><i>El sistema operativo detectado puede ser ambiguo: ajústalo si el original no coincide.</i>":
        "The OVF descriptor has been read. Review the detected data and correct what is needed before importing.<br><br><i>The detected operating system may be ambiguous: adjust it if the original does not match.</i>",
    "(desconocido)": "(unknown)",
    "(sin nombre)": "(no name)",
    "(sin discos)": "(no disks)",
    "<b>Detectado en el OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}":
        "<b>Detected in the OVF:</b><br>OS: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Disks: {4} — {5}",
    "Nombre de la VM:": "VM name:",
    "GNU / Linux": "GNU / Linux",
    "Microsoft Windows": "Microsoft Windows",
    "Android (Android-x86 / Bliss OS)": "Android (Android-x86 / Bliss OS)",
    "Plataforma:": "Platform:",
    "Distribución / versión:": "Distribution / version:",
    "Importar solo la configuración (sin copiar los discos)":
        "Import configuration only (without copying disks)",
    "Si está marcado, se importan solo los datos del descriptor (CPU, RAM, red, sistema operativo) y NO se convierten ni copian los discos. Útil para reutilizar una configuración sin duplicar gigabytes de disco.":
        "If checked, only the descriptor data is imported (CPU, RAM, network, operating system) and the disks are NOT converted or copied. Useful for reusing a configuration without duplicating gigabytes of disk.",
    "Importar": "Import",
    "Distribución:": "Distribution:",
    "Versión de Windows:": "Windows version:",
    "Versión de macOS:": "macOS version:",
    "Distribución Android:": "Android distribution:",
    "Nombre inválido": "Invalid name",
    "Debes escribir un nombre para la VM importada.":
        "You must enter a name for the imported VM.",

    "macOS": "macOS",
    # ================================================================
    # Tanda 4a-2.5.3b: Dialogos simples de vm_lifecycle_mixin
    # (i18n_tanda4a2_5_3b_v1)
    # ================================================================
    # --- edit_vm_label ---
    "Etiqueta de la VM": "VM label",
    "Etiqueta - {0}": "Label - {0}",
    "Grupo y color para <b>{0}</b>. El grupo es texto libre: escribe uno nuevo para crearlo. El color se aplica como fondo suave del ítem en la lista lateral.":
        "Group and colour for <b>{0}</b>. The group is free text: type a new one to create it. The colour is applied as a soft background of the item in the sidebar.",
    "(sin grupo)": "(no group)",
    "Grupo:": "Group:",
    "<b>Color:</b>": "<b>Colour:</b>",
    "Sin color": "No colour",
    "Quitar etiqueta": "Remove label",
    "Guardar": "Save",
    "Etiqueta": "Label",
    "No se pudo guardar la etiqueta.\n\n{0}":
        "Could not save the label.\n\n{0}",

    # --- show_qemu_command ---
    "Comando QEMU": "QEMU command",
    "Selecciona primero una maquina virtual.":
        "Select a virtual machine first.",
    "La VM '{0}' todavia no se ha arrancado.\n\nEl comando QEMU se genera al pulsar Iniciar; vuelve a intentarlo despues del primer arranque.":
        "The VM '{0}' has not been started yet.\n\nThe QEMU command is generated when you press Start; try again after the first boot.",
    "No se pudo leer run_temp.sh.\n\n{0}":
        "Could not read run_temp.sh.\n\n{0}",
    "Comando QEMU - {0}": "QEMU command - {0}",
    "Contenido de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este es el comando exacto con el que QEMU esta ejecutando (o ejecuto por ultima vez) la VM.":
        "Contents of <code>run_temp.sh</code> for <b>{0}</b>.<br>This is the exact command QEMU is using (or last used) for the VM.",
    "Copiar al portapapeles": "Copy to clipboard",
    "Abrir carpeta de la VM": "Open VM folder",
    "Abre la carpeta que contiene run_temp.sh, launch.log y los discos.":
        "Opens the folder containing run_temp.sh, launch.log and the disks.",
    "Cerrar": "Close",

    # --- edit_vm_notes ---
    "Notas de la VM": "VM notes",
    "Notas - {0}": "Notes - {0}",
    "Notas libres sobre <b>{0}</b>. Se guardan en <code>vm_config.ini</code> como <code>extra.notes</code> y aparecen como aviso amarillo en la pestana Resumen.":
        "Free-form notes about <b>{0}</b>. They are stored in <code>vm_config.ini</code> as <code>extra.notes</code> and appear as a yellow notice in the Overview tab.",
    "Ej.: instalado con VirtIO, probar snapshots tras actualizar los drivers; puerto 8080 redirigido al 80 del guest...":
        "E.g.: installed with VirtIO, test snapshots after updating drivers; port 8080 forwarded to guest's 80...",
    "Borrar notas": "Clear notes",
    "Notas": "Notes",
    "No se pudieron guardar las notas.\n\n{0}":
        "Could not save the notes.\n\n{0}",

    # --- _set_vm_status ---
    "● Nueva VM": "● New VM",
    "● Configurada": "● Configured",
    "● Ejecutándose": "● Running",
    "● Error": "● Error",

    # --- open_vm_folder / show_vm_summary ---
    "Carpeta": "Folder",
    "Primero selecciona una máquina virtual existente.":
        "First select an existing virtual machine.",
    "Carpeta de la VM": "VM folder",
    "No se pudo abrir la carpeta.\n\n{0}\n\n{1}":
        "Could not open the folder.\n\n{0}\n\n{1}",
    "Resumen": "Overview",
    "No hay una máquina virtual seleccionada todavía.":
        "No virtual machine selected yet.",
    "Resumen de la máquina virtual": "Virtual machine summary",

    # ================================================================
    # Tanda 4a-2.5.3c1: import_vm + _import_vm_impl
    # (i18n_tanda4a2_5_3c1_v1)
    # ================================================================
    "Importar VM": "Import VM",
    "¿Cómo quieres importar la máquina virtual?\n\n  • Desde carpeta: selecciona una carpeta que contenga vm_config.ini.\n  • Desde archivo: selecciona un .ova o .ovf (formato estándar OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip exportado previamente desde otra instalación de Virtual.Machine.":
        "How do you want to import the virtual machine?\n\n  • From folder: select a folder containing vm_config.ini.\n  • From file: select an .ova or .ovf (standard OVF format, portable to VirtualBox/VMware), or a .tar.gz / .tar / .zip previously exported from another Virtual.Machine installation.",
    "📁 Desde carpeta…": "📁 From folder…",
    "🗜️ Desde archivo…": "🗜️ From file…",
    "Selecciona la carpeta de la VM a importar":
        "Select the VM folder to import",
    "Selecciona el archivo a importar":
        "Select the file to import",
    "OVF/OVA (*.ova *.ovf);;Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;Todos los archivos (*)":
        "OVF/OVA (*.ova *.ovf);;Packaged VM files (*.tar.gz *.tgz *.tar *.zip);;All files (*)",
    "Formato de archivo no reconocido. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.":
        "Unrecognised file format. Use .tar.gz, .tgz, .tar, .zip, .ova or .ovf.",
    "La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\nAsegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.":
        "The selected folder does not contain vm_config.ini:\n\n{0}\n\nMake sure you select the VM root folder, not a subfolder.",
    "Nombre para la VM importada:\n\n(se importará desde {0})":
        "Name for the imported VM:\n\n(will be imported from {0})",
    "Nombre inválido.": "Invalid name.",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "A VM named '{0}' already exists.\n\nReplace it? (the existing one will be deleted)",
    "Copiando/desempaquetando en el sistema de archivos del destino (no en /tmp)…":
        "Copying/unpacking into the destination filesystem (not /tmp)…",
    "Desempaquetando archivo…": "Unpacking file…",
    "Extrayendo {0}/{1}…": "Extracting {0}/{1}…",
    "El archivo no contiene ninguna VM válida (no se encontró vm_config.ini).":
        "The file does not contain any valid VM (vm_config.ini was not found).",
    "Importación completada.": "Import completed.",
    "Copiando {0}": "Copying {0}",
    "VM '{0}' importada correctamente.\n\nRevisa su configuración en la pestaña Configuración antes de arrancarla, especialmente si la importaste desde otro host: puede referenciar rutas que no existan aquí (carpetas compartidas, ISOs externas, dispositivos de passthrough).":
        "VM '{0}' imported successfully.\n\nReview its configuration in the Settings tab before starting it, especially if you imported it from another host: it may reference paths that do not exist here (shared folders, external ISOs, passthrough devices).",

    # ================================================================
    # Tanda 4a-2.5.3c2: export_vm + _export_vm_impl
    # (i18n_tanda4a2_5_3c2_v1)
    # ================================================================
    "Exportar VM": "Export VM",
    "Primero selecciona una máquina virtual.":
        "Select a virtual machine first.",
    "La VM '{0}' está {1}.\n\nSe recomienda apagarla antes de exportar: si está corriendo, los discos pueden estar en un estado inconsistente (cambios sin sincronizar a disco, locks activos…).\n\n¿Continuar de todos modos?":
        "VM '{0}' is {1}.\n\nIt is recommended to power it off before exporting: if it is running, the disks may be in an inconsistent state (unsynced changes, active locks…).\n\nContinue anyway?",
    "Copia de carpeta (más rápido, editable)":
        "Folder copy (faster, editable)",
    "Archivo .tar.gz (comprimido, portable)":
        ".tar.gz file (compressed, portable)",
    "Archivo .zip (compatible con Windows)":
        ".zip file (Windows-compatible)",
    "Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)":
        ".ova file (Open Virtual Appliance, portable to VirtualBox/VMware)",
    "Descriptor .ovf + discos sueltos (carpeta)":
        ".ovf descriptor + standalone disks (folder)",
    "Formato para exportar '{0}':": "Format to export '{0}':",
    "Elige la carpeta donde crear la copia":
        "Choose the folder where the copy will be created",
    "En la carpeta destino ya existe '{0}'.\n\n¿Sobrescribir? (se borrará la carpeta destino existente)":
        "The destination folder already contains '{0}'.\n\nOverwrite? (the existing destination folder will be deleted)",
    "Guardar archivo de exportación": "Save export file",
    "Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)":
        "tar.gz file (*.tar.gz);;zip file (*.zip)",
    "Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)":
        "zip file (*.zip);;tar.gz file (*.tar.gz)",
    "El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?":
        "The destination file already exists:\n{0}\n\nOverwrite?",
    "Confirmar exportación": "Confirm export",
    "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Contenido: {2} archivo(s), {3}\n  • Destino: {4}\n\nLos archivos de bloqueo (pids, sockets) y logs se omitirán.":
        "Export '{0}' as:\n\n  • Format: {1}\n  • Content: {2} file(s), {3}\n  • Destination: {4}\n\nLock files (pids, sockets) and logs will be skipped.",
    "No se pudo completar la exportación.\n\n{0}":
        "Could not complete the export.\n\n{0}",
    "{0} archivo(s), {1} en total": "{0} file(s), {1} total",
    "Exportación cancelada por el usuario.":
        "Export cancelled by the user.",
    "Formato de exportación desconocido: {0}":
        "Unknown export format: {0}",
    "Exportación completada ({0} archivo(s)).":
        "Export completed ({0} file(s)).",
    "'{0}' exportada correctamente.\n\nDestino: {1}":
        "'{0}' exported successfully.\n\nDestination: {1}",

    # ================================================================
    # Tanda 4a-2.5.3c3a: clone_current_vm + full + prompts + checks
    # (i18n_tanda4a2_5_3c3a_v1)
    # ================================================================
    "Clonar máquina virtual": "Clone virtual machine",
    "Nombre para el clon de '{0}':": "Name for the clone of '{0}':",
    "Debes escribir un nombre para el clon.":
        "You must enter a name for the clone.",
    "Nombre ya existente": "Name already exists",
    "La máquina virtual '{0}' ya existe en el listado.\n\nElige otro nombre para el clon.":
        "The virtual machine '{0}' already exists in the list.\n\nChoose another name for the clone.",
    "Ese nombre no puede utilizarse para una máquina virtual.":
        "That name cannot be used for a virtual machine.",
    "Clonar VM": "Clone VM",
    "Primero selecciona una máquina virtual existente.":
        "First select an existing virtual machine.",
    "¿Qué tipo de clon quieres crear a partir de <b>{0}</b>?<br><br><b>Clon completo</b><br>Copia íntegra de todos los discos. Totalmente independiente del original; ocupa el mismo espacio que la VM original.<br><br><b>Clon enlazado</b><br>El disco base se comparte mediante un <i>backing file</i> QCOW2. La nueva VM solo guarda los cambios, así que ocupa muy poco. <b>Depende del original</b>: si se borra o se mueve el original, el clon se rompe.<br>El backing se guarda con <b>ruta relativa</b> para que puedas mover o copiar la carpeta <code>VirtualMachines/</code> entera a otro host sin romper nada.<br><br><b>Importante:</b> una vez que el clon arranque por primera vez, los cambios que hagas DESPUÉS en el original <b>NO se verán</b> en el clon: la vista de su sistema de archivos queda anclada al estado del primer arranque (los bloques que el clon ya escribió no vuelven a consultarse en el backing). Trata el original como de solo lectura mientras el clon exista, o desenlaza el clon con <b>🧬 Desenlazar</b> para independizarlo.":
        "What type of clone do you want to create from <b>{0}</b>?<br><br><b>Full clone</b><br>Complete copy of all disks. Fully independent from the original; uses the same space as the original VM.<br><br><b>Linked clone</b><br>The base disk is shared via a QCOW2 <i>backing file</i>. The new VM only stores changes, so it uses very little. <b>Depends on the original</b>: if the original is deleted or moved, the clone breaks.<br>The backing is stored with a <b>relative path</b> so you can move or copy the whole <code>VirtualMachines/</code> folder to another host without breaking anything.<br><br><b>Important:</b> once the clone boots for the first time, changes you make LATER in the original <b>will NOT be visible</b> in the clone: its filesystem view is anchored to the state at first boot (blocks the clone has already written are never looked up in the backing again). Treat the original as read-only while the clone exists, or unlink the clone with <b>🧬 Unlink</b> to make it independent.",
    "Clon completo": "Full clone",
    "Clon enlazado": "Linked clone",
    "No se pudo copiar la carpeta de la VM.\n\n{0}":
        "Could not copy the VM folder.\n\n{0}",
    "La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}":
        "The VM was copied but its vm_config.ini could not be rewritten.\n\n{0}",
    "Clon creado": "Clone created",
    "La máquina virtual '{0}' fue clonada correctamente (clon completo).\n\nSe han regenerado las direcciones MAC y los IDs internos de los discos para que no choquen con la VM original.":
        "The virtual machine '{0}' was cloned successfully (full clone).\n\nMAC addresses and internal disk IDs have been regenerated so they do not clash with the original VM.",
    "Clon enlazado con original en ejecución":
        "Linked clone with running original",
    "El original de este clon ('{0}') está corriendo.\n\nArrancar original y clon a la vez puede dar resultados impredecibles:\n\n  • El clon lee del disco del original los bloques que no ha modificado. Si el original escribe algo mientras el clon corre, el clon puede leer estados intermedios.\n  • La vista del sistema de archivos del clon ya está anclada al estado de su primer arranque para los bloques de metadatos, así que los cambios nuevos del original probablemente no se vean, pero el riesgo de lectura inconsistente sigue ahí.\n\nRecomendaciones:\n  • Apaga el original antes de arrancar el clon (o al revés).\n  • O desenlaza el clon con '🧬 Desenlazar' para que sea totalmente independiente.\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "The original of this clone ('{0}') is running.\n\nRunning the original and the clone at the same time may give unpredictable results:\n\n  • The clone reads from the original's disk the blocks it has not modified. If the original writes anything while the clone runs, the clone may read intermediate states.\n  • The clone's filesystem view is already anchored to the state of its first boot for metadata blocks, so new changes in the original probably will not be seen, but the risk of inconsistent reads remains.\n\nRecommendations:\n  • Power off the original before starting the clone (or vice versa).\n  • Or unlink the clone with '🧬 Unlink' to make it fully independent.\n\nThis warning will not appear again for this VM in this session.",
    "Clon enlazado con backing roto":
        "Linked clone with broken backing",
    "Este clon enlazado espera el backing en:\n\n    {0}\n\nResuelto contra su carpeta queda en:\n\n    {1}\n\nEse archivo no existe. La VM original ('{2}') probablemente se movió o se borró.\n\nQEMU fallará al arrancar con:\n    Could not open backing file: No such file or directory\n\nOpciones:\n  • Mueve también la VM original de vuelta a su carpeta, o\n  • Copia la carpeta 'VirtualMachines/' entera (con original\n    y clon juntos) a la nueva ubicación, o\n  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n    para independizar este clon (puede fallar si el backing\n    ya no está disponible).\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "This linked clone expects the backing at:\n\n    {0}\n\nResolved against its folder it becomes:\n\n    {1}\n\nThat file does not exist. The original VM ('{2}') was probably moved or deleted.\n\nQEMU will fail to start with:\n    Could not open backing file: No such file or directory\n\nOptions:\n  • Move the original VM back to its folder, or\n  • Copy the whole 'VirtualMachines/' folder (with original\n    and clone together) to the new location, or\n  • If you still can, use '🧬 Unlink' on the Overview tab\n    to make this clone independent (may fail if the backing\n    is no longer available).\n\nThis warning will not appear again for this VM in this session.",

    # ================================================================
    # Tanda 4a-2.5.3c3b: clone linked + unlink
    # (i18n_tanda4a2_5_3c3b_v1)
    # ================================================================
    "No se pudo determinar el disco principal de la VM original.\n\nEl clon enlazado necesita un disco base QCOW2 sobre el que\ncrear el backing file. Si la VM no tiene discos, usa\n'Clon completo'.":
        "Could not determine the original VM's primary disk.\n\nThe linked clone needs a QCOW2 base disk on which\nto create the backing file. If the VM has no disks, use\n'Full clone'.",
    "No se pudo inspeccionar el disco original.\n\n{0}":
        "Could not inspect the original disk.\n\n{0}",
    "El disco principal de la VM original está en formato {0}.\n\nEl clon enlazado solo funciona con QCOW2 (necesita backing\nfile). Usa 'Clon completo' si quieres copiar el disco tal cual.":
        "The original VM's primary disk is in {0} format.\n\nThe linked clone only works with QCOW2 (it needs a backing\nfile). Use 'Full clone' if you want to copy the disk as is.",
    "No se pudo crear la carpeta del clon.\n\n{0}":
        "Could not create the clone folder.\n\n{0}",
    "qemu-img create falló.\n\n{0}": "qemu-img create failed.\n\n{0}",
    "No se pudo crear el delta QCOW2.\n\n{0}":
        "Could not create the QCOW2 delta.\n\n{0}",
    "El backing file quedó guardado como ruta ABSOLUTA, lo que haría el clon no portable.\n\nSe ha abortado la operación para no dejar un clon defectuoso. Reporta esto como bug.":
        "The backing file was stored as an ABSOLUTE path, which would make the clone non-portable.\n\nThe operation has been aborted to avoid leaving a defective clone. Report this as a bug.",
    "No se pudieron copiar los archivos auxiliares.\n\n{0}":
        "Could not copy the auxiliary files.\n\n{0}",
    "El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n{0}\n\nRevisa manualmente el archivo antes de usar la VM.":
        "The clone was created but its vm_config.ini could not be rewritten.\n\n{0}\n\nReview the file manually before using the VM.",
    "La máquina virtual '{0}' fue clonada correctamente (clon enlazado).\n\nEl disco base se comparte con el original mediante un backing\nfile QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\npero DEPENDE del original:\n\n  • Si borras o mueves la VM original, el clon se rompe.\n  • Una vez que el clon arranque por primera vez, los cambios\n    que hagas DESPUÉS en el original NO se verán en el clon:\n    la vista del sistema de archivos queda anclada al estado\n    del primer arranque. Trata el original como de solo lectura\n    mientras el clon exista.\n  • Los snapshots completos (RAM) no funcionarán en este clon\n    — solo de disco. QEMU no puede restaurar (loadvm) un\n    snapshot completo sobre un QCOW2 con backing file.\n  • Los snapshots del clon no son reproducibles mientras el\n    original pueda cambiar: al restaurar, se mezcla el delta\n    guardado con el estado ACTUAL del backing.\n  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n    apagado.\n\nPara mover o copiar la estructura completa a otro host,\nllévate la carpeta 'VirtualMachines/' entera.":
        "The virtual machine '{0}' was cloned successfully (linked clone).\n\nThe base disk is shared with the original through a QCOW2\nbacking file with a relative path. The clone uses very little space,\nbut DEPENDS on the original:\n\n  • If you delete or move the original VM, the clone breaks.\n  • Once the clone boots for the first time, changes you make\n    LATER in the original will NOT be visible in the clone:\n    the filesystem view is anchored to the state of the first\n    boot. Treat the original as read-only while the clone exists.\n  • Full snapshots (RAM) will not work on this clone\n    — disk-only. QEMU cannot restore (loadvm) a full\n    snapshot on a QCOW2 with a backing file.\n  • Snapshots of the clone are not reproducible while the\n    original can change: on restore, the saved delta is mixed\n    with the CURRENT state of the backing.\n  • If you want to make it independent, use '🧬 Unlink' when it is\n    powered off.\n\nTo move or copy the whole structure to another host,\ntake the entire 'VirtualMachines/' folder.",
    "Desenlazar clon": "Unlink clone",
    "Esta VM no es un clon enlazado, no hay nada que desenlazar.":
        "This VM is not a linked clone, there is nothing to unlink.",
    "La VM '{0}' está encendida.\n\nApágala antes de desenlazarla: con QEMU activo el archivo\nestá bloqueado y el convert no puede reemplazarlo.":
        "VM '{0}' is running.\n\nPower it off before unlinking: with QEMU running the file\nis locked and the convert cannot replace it.",
    "No se encontró el disco principal del clon.":
        "The clone's primary disk was not found.",
    "Se convertirá el disco principal del clon <b>{0}</b> en un QCOW2 <b>autónomo</b>.<br><br>Después de esto, el clon deja de depender del original y puede moverse o copiarse por separado.<br><br><b>Requiere:</b><br>&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>&nbsp;&nbsp;• La VM apagada (ya lo está).<br>&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>El resultado se verifica como QCOW2 válido y se reemplaza atómicamente. Si algo falla a mitad, el archivo original del clon queda intacto.":
        "The clone's primary disk <b>{0}</b> will be converted into a standalone QCOW2.<br><br>After this, the clone no longer depends on the original and can be moved or copied separately.<br><br><b>Requires:</b><br>&nbsp;&nbsp;• Free space on the host (~1.1× the disk size).<br>&nbsp;&nbsp;• The VM powered off (already is).<br>&nbsp;&nbsp;• Not closing the application during the process.<br><br>The result is verified as a valid QCOW2 and replaced atomically. If anything fails mid-way, the clone's original file remains intact.",
    "Desenlazado cancelado por el usuario.":
        "Unlink cancelled by the user.",
    "Desenlazado": "Unlinked",
    "El clon '{0}' ya es autónomo.\n\nTamaño antes: {1}\nTamaño después: {2}\n\nPuedes mover la VM sin llevarte la original.":
        "Clone '{0}' is now standalone.\n\nSize before: {1}\nSize after: {2}\n\nYou can move the VM without taking the original with it.",
    "No se pudo desenlazar el clon.\n\n{0}":
        "Could not unlink the clone.\n\n{0}",
    "Convirtiendo el clon en un QCOW2 autónomo…":
        "Converting the clone into a standalone QCOW2…",

    # ================================================================
    # Tanda 4a-2.5.3c4: delete_current_vm + OVF raises/messages
    # (i18n_tanda4a2_5_3c4_v1)
    # ================================================================
    # --- delete_current_vm ---
    "Eliminar VM": "Delete VM",
    "Primero selecciona una máquina virtual existente.":
        "First select an existing virtual machine.",
    "Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n":
        "Only the virtual machine folder will be deleted:\n\n{0}\n\n",
    "Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n":
        "The following media are outside the VM folder and will NOT be deleted:\n",
    "⚠ ESTA VM ES EL ORIGINAL DE {0} CLON(ES) ENLAZADO(S):\n":
        "⚠ THIS VM IS THE ORIGINAL OF {0} LINKED CLONE(S):\n",
    "\n\nSi continúas, esos clones quedarán inutilizables (su backing file ya no existirá).\n\nSe recomienda desenlazarlos primero: selecciona cada clon y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n":
        "\n\nIf you continue, those clones will become unusable (their backing file will no longer exist).\n\nIt is recommended to unlink them first: select each clone and press '🧬 Unlink' in its Overview tab.\n\n",
    "¿Deseas continuar?": "Do you want to continue?",
    "Eliminar máquina virtual": "Delete virtual machine",
    "No se pudo eliminar '{0}'.\n\n{1}":
        "Could not delete '{0}'.\n\n{1}",

    # --- OVF export raises ---
    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la carpeta de la VM ({0}). Sin este archivo la VM no tiene sistema operativo que exportar.":
        "macOS VM: mac_hdd_ng.qcow2 not found in the VM folder ({0}). Without this file the VM has no operating system to export.",
    "La VM no tiene discos adjuntos que exportar. Añade al menos un disco en Configuración → Almacenamiento.":
        "The VM has no attached disks to export. Add at least one disk in Settings → Storage.",
    "qemu-img convert -c falló para '{0}': {1}":
        "qemu-img convert -c failed for '{0}': {1}",
    "El aplanado+compresión de '{0}' no produjo un archivo válido.":
        "Flattening+compression of '{0}' did not produce a valid file.",

    # --- OVF import ---
    "Importar OVA": "Import OVA",
    "El archivo .ova no contiene ningún descriptor .ovf.":
        "The .ova file does not contain any .ovf descriptor.",
    "Importar OVF": "Import OVF",
    "El archivo .ovf está vacío.": "The .ovf file is empty.",
    "No se pudo leer el descriptor.\n\n{0}":
        "Could not read the descriptor.\n\n{0}",
    "El descriptor OVF no se pudo interpretar.\n\n{0}":
        "The OVF descriptor could not be parsed.\n\n{0}",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "A VM named '{0}' already exists.\n\nReplace it? (the existing one will be deleted)",
    "No se pudo completar la importación.\n\n{0}":
        "Could not complete the import.\n\n{0}",
    "Extrayendo y preparando el OVF/OVA...":
        "Extracting and preparing the OVF/OVA...",

    # ================================================================
    # Tanda 4a-2.6: suggestions_mixin (helper puro con tr opcional)
    # (i18n_tanda4a2_6_v1)
    # ================================================================
    "Selecciona una VM para ver sugerencias.":
        "Select a VM to see suggestions.",
    "No se pudo leer la configuración: {0}":
        "Could not read the configuration: {0}",
    "Disco del host al {0}% — crítico. Quedan solo {1}. Amplía el disco o mueve archivos.":
        "Host disk at {0}% — critical. Only {1} left. Enlarge the disk or move files.",
    "Disco del host al {0}%. Quedan {1}. Considera ampliarlo o limpiar.":
        "Host disk at {0}%. {1} left. Consider enlarging it or cleaning up.",
    "RAM de la VM ({0} GB) es el {1}% de la del host ({2} GB). Riesgo de swap.":
        "VM RAM ({0} GB) is {1}% of the host's ({2} GB). Risk of swapping.",
    "El último snapshot tiene {0} días ({1} en total). Puedes crear uno nuevo o limpiar los antiguos.":
        "The last snapshot is {0} days old ({1} total). You can create a new one or clean up old ones.",
    "Hay {0} snapshots acumulados ocupando {1}. Considera eliminar los que ya no necesites.":
        "{0} snapshots accumulated using {1}. Consider deleting the ones you no longer need.",
    "Hay {0} carpeta(s) VirtioFS configuradas pero el Guest Agent está desactivado. Algunas funciones de automontaje no funcionarán.":
        "{0} VirtioFS folder(s) configured but the Guest Agent is disabled. Some automount features will not work.",
    "{0} carpeta(s) compartida(s) apuntan a rutas que ya no existen en el host: {1}":
        "{0} shared folder(s) point to paths that no longer exist on the host: {1}",
    "Hay {0} dispositivo(s) PCI en passthrough pero IOMMU no parece estar activo en el kernel. La VM puede no arrancar.":
        "{0} PCI device(s) in passthrough but IOMMU does not appear active in the kernel. The VM may fail to boot.",
    "Windows 11 requiere UEFI + Secure Boot. Cambia el firmware a UEFI.":
        "Windows 11 requires UEFI + Secure Boot. Change the firmware to UEFI.",
    "macOS/OSX-KVM requiere UEFI (OVMF). Cambia el firmware a UEFI.":
        "macOS/OSX-KVM requires UEFI (OVMF). Change the firmware to UEFI.",
    "El disco principal está en formato RAW. No admite snapshots internos ni crece dinámicamente. Considera convertir a QCOW2 si necesitas snapshots.":
        "The primary disk is in RAW format. It does not support internal snapshots or dynamic growth. Consider converting to QCOW2 if you need snapshots.",
    "El log de la VM ({0} MB) es grande. Puedes exportarlo y borrarlo desde 'Ver log completo' → 'Exportar log'.":
        "The VM log ({0} MB) is large. You can export it and delete it from 'View full log' → 'Export log'.",
    "La configuración no se ha modificado en {0} días. ¿Sigue siendo útil esta VM?":
        "The configuration has not been modified in {0} days. Is this VM still useful?",
    "La VM tiene audio configurado pero el host no tiene /dev/snd ni PulseAudio/PipeWire (pactl). QEMU puede fallar al arrancar con audio.":
        "The VM has audio configured but the host has neither /dev/snd nor PulseAudio/PipeWire (pactl). QEMU may fail to start with audio.",
    "Todo en orden. No hay sugerencias pendientes.":
        "All good. No pending suggestions.",

    # ================================================================
    # Tanda 4a-3: task_progress + async_ui + shortcuts + appearance
    # (i18n_tanda4a3_v1)
    # ================================================================
    # --- task_progress ---
    "Iniciando…": "Starting…",
    "Cancelar": "Cancel",
    "Cerrar": "Close",
    "Completado.": "Completed.",
    "Error:": "Error:",
    "La tarea falló.": "The task failed.",
    "Cancelando, esperando al trabajador…":
        "Cancelling, waiting for the worker…",
    "Cancelando…": "Cancelling…",

    # --- shortcuts_mixin ---
    "Configurar atajos de teclado": "Configure keyboard shortcuts",
    "Haz clic en <b>Cambiar...</b> para capturar una nueva\ncombinacion de teclas. Pulsa <b>Escape</b> durante la\ncaptura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\npara deshabilitar un atajo.":
        "Click <b>Change...</b> to capture a new key\ncombination. Press <b>Escape</b> during\nthe capture to cancel it. Use <b>Del</b> or <b>Backspace</b>\nto disable a shortcut.",
    "Accion": "Action",
    "Atajo": "Shortcut",
    "Cambiar...": "Change...",
    "Restaurar todos por defecto": "Restore all to defaults",
    "(sin atajo)": "(no shortcut)",
    "Conflicto de atajos": "Shortcut conflict",
    "El atajo {0} ya esta asignado a:\n\n  {1}\n\nElige otro o cambia primero el otro atajo.":
        "The shortcut {0} is already assigned to:\n\n  {1}\n\nChoose another or change the other shortcut first.",
    "Restaurar atajos": "Restore shortcuts",
    "¿Restaurar los cuatro atajos a sus valores por defecto?":
        "Restore all four shortcuts to their default values?",
    "Pulsa la nueva combinacion": "Press the new combination",
    "<b>Pulsa la combinacion de teclas que quieras asignar.</b>":
        "<b>Press the key combination you want to assign.</b>",
    "Esperando pulsacion...\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "Waiting for a keypress...\n\nEscape cancels. Del or Backspace disables the shortcut.",
    "Atajo actual: <b>{0}</b>": "Current shortcut: <b>{0}</b>",
    "Solo has pulsado un modificador. Anade una tecla normal.\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "You only pressed a modifier. Add a normal key.\n\nEscape cancels. Del or Backspace disables the shortcut.",
    "Abrir menu de Medios (CD/DVD + USB)":
        "Open Media menu (CD/DVD + USB)",
    "Reconectar el widget VNC": "Reconnect the VNC widget",
    "Alternar Consola Grafica": "Toggle Graphical Console",
    "Entrar / salir del modo presentacion":
        "Enter / exit presentation mode",

    # --- appearance_mixin ---
    "Cambio de tema": "Theme change",
    "Se ha cambiado el tema.\n\nAlgunos estilos del escritorio (Kvantum en KDE, por\nejemplo) pueden no repintar todos los widgets hasta\nreiniciar la aplicacion.\n\n¿Quieres reiniciar ahora para asegurar que todos los\nelementos se vean correctamente?":
        "The theme has been changed.\n\nSome desktop styles (Kvantum on KDE, for\nexample) may not repaint all widgets until\nthe application is restarted.\n\nDo you want to restart now to ensure all\nelements are shown correctly?",
    "No hay ninguna máquina virtual seleccionada.":
        "No virtual machine selected.",
    "La VM '{0}' no está corriendo. Enciéndela antes de entrar en modo presentación.":
        "VM '{0}' is not running. Start it before entering presentation mode.",
    "La Consola Gráfica no está disponible en este sistema (falta el widget VNC embebido).":
        "The Graphical Console is not available on this system (the embedded VNC widget is missing).",
    "No se pudo comprobar el estado de la VM: {0}":
        "Could not check the VM state: {0}",
    "Modo presentación": "Presentation mode",
    "🎬 Salir de presentación": "🎬 Exit presentation",
    "Salir del modo presentación y restaurar la vista normal.\nTambién puedes pulsar F11 o Escape.":
        "Exit presentation mode and restore the normal view.\nYou can also press F11 or Escape.",
    "🎬 Presentación": "🎬 Presentation",
    "Modo presentación: oculta los paneles laterales, entra\nen pantalla completa y salta a la Consola Gráfica.\nRequiere que la VM esté encendida.\n\nAtajo: F11. Para salir: F11 o Escape.":
        "Presentation mode: hides the side panels, enters\nfullscreen and jumps to the Graphical Console.\nRequires the VM to be running.\n\nShortcut: F11. To exit: F11 or Escape.",

    # ================================================================
    # Tanda 4a-4: api_mixin (UI visible; respuestas HTTP NO se traducen)
    # (i18n_tanda4a4_v1)
    # ================================================================
    "<b style='color:#2e7d32;'>Activa</b> — {0} peticiones desde el arranque":
        "<b style='color:#2e7d32;'>Active</b> — {0} requests since startup",
    "<b style='color:#888;'>Detenida</b>":
        "<b style='color:#888;'>Stopped</b>",
    "API REST": "REST API",
    "No se pudo arrancar la API REST.\n\n{0}":
        "Could not start the REST API.\n\n{0}",
    "Regenerar token": "Regenerate token",
    "Se generará un token nuevo y el anterior dejará de funcionar.\n\n¿Continuar?":
        "A new token will be generated and the previous one will stop working.\n\nContinue?",
    "Se regeneró el token pero no se pudo reiniciar la API:\n\n{0}":
        "The token was regenerated but the API could not be restarted:\n\n{0}",
    "Peticiones recientes a la API": "Recent API requests",
    "Últimas peticiones atendidas por la API. Se conservan las 50 más recientes.":
        "Latest requests served by the API. The 50 most recent are kept.",
    "(sin peticiones todavía)": "(no requests yet)",

    # ================================================================
    # Tanda 4a-5: install_flow + mac_recovery
    # (i18n_tanda4a5_v1)
    # ================================================================
    "Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.":
        "For macOS use 'Download System Recovery'. Apple ships the full installer as an application; the OSX-KVM Recovery flow is the method integrated in this manager.",
    "Android-x86 / Bliss OS no tienen descarga automática. Descarga la ISO desde https://www.android-x86.org/download.html o https://blissos.org/ y selecciónala en Plataforma → Android.":
        "Android-x86 / Bliss OS do not support automatic download. Download the ISO from https://www.android-x86.org/download.html or https://blissos.org/ and select it in Platform → Android.",
    "System Recovery de macOS — {0}": "macOS System Recovery — {0}",
    "La imagen se descarga y verifica directamente en la carpeta de la VM.":
        "The image is downloaded and verified directly in the VM folder.",
    "Iniciando descarga…": "Starting download…",
    "Recovery preparado.": "Recovery ready.",
    "No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.":
        "qemu-system-x86_64 was not found in PATH. Run ./run.sh (installs the system dependencies) or install qemu-system-x86 / qemu-kvm.",
    "/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.":
        "/dev/kvm is not available; QEMU might work without KVM acceleration.",
    "El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.":
        "The user does not have read/write permissions on /dev/kvm.",
    "No se detectó un firmware OVMF conocido para Secure Boot.":
        "No known OVMF firmware was detected for Secure Boot.",
    "El dispositivo de almacenamiento '{0}' apunta a un archivo que ya no existe: {1}":
        "The storage device '{0}' points to a file that no longer exists: {1}",
    "La carpeta compartida '{0}' apunta a una ruta del host que ya no existe: {1}":
        "The shared folder '{0}' points to a host path that no longer exists: {1}",
    "Solo quedan {0} GB libres donde vive esta VM; puede fallar durante el uso.":
        "Only {0} GB left where this VM lives; it may fail during use.",
    "El orden de arranque prioriza el CD/DVD, pero el disco '{0}' ya tiene datos (~{1} GB). Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo.":
        "The boot order prioritises the CD/DVD, but disk '{0}' already contains data (~{1} GB). If the system is already installed, this may attempt to reinstall instead of booting it.",
    "Advertencia": "Warning",
    "Debe indicar un nombre para la máquina virtual.":
        "You must enter a name for the virtual machine.",
    'El nombre no puede contener: \\ / : * ? " < > |':
        'The name cannot contain: \\ / : * ? " < > |',
    "La VM ya está corriendo": "The VM is already running",
    "'{0}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco (dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\nDetén la VM actual antes de volver a iniciarla.":
        "'{0}' already has an active QEMU process. Starting it again may corrupt the disk (two processes writing to the same file) or clash with sockets already in use.\n\nStop the current VM before starting it again.",
    "No se puede iniciar la VM": "Cannot start the VM",
    "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.":
        "QEMU is missing on the system. Install qemu-system-x86 and try again.",
    "Revisión previa": "Preflight check",
    "¿Deseas continuar de todos modos?": "Do you want to continue anyway?",
    "Configuración incompatible": "Incompatible configuration",
    "Secure Boot requiere UEFI (OVMF).":
        "Secure Boot requires UEFI (OVMF).",
    "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.":
        "TPM 2.0 does not apply to the current macOS/OSX-KVM flow.",
    "Dependencias faltantes": "Missing dependencies",
    "No se pudieron preparar automáticamente las dependencias necesarias.\n\n{0}":
        "The required dependencies could not be prepared automatically.\n\n{0}",
    "System Recovery de macOS": "macOS System Recovery",
    "No se pudo preparar System Recovery antes de iniciar la VM.\n\n{0}":
        "System Recovery could not be prepared before starting the VM.\n\n{0}",
    "Disco existente con otra configuración":
        "Existing disk with a different configuration",
    "Ya existe un disco para '{0}' con {1} / {2} / {3}, distinto a lo solicitado ({4} / {5} / {6}).\n\n¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n(\"No\" conserva el disco existente tal como está.)":
        "A disk already exists for '{0}' with {1} / {2} / {3}, different from what was requested ({4} / {5} / {6}).\n\nDo you want to delete it and create a new one with the current parameters?\n(\"No\" keeps the existing disk as is.)",
    "Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.":
        "You must enter a valid Windows ISO file path or select 'Download Windows installer automatically' in CD/DVD.",
    "Android": "Android",
    "Debes configurar la ISO de Android-x86 o Bliss OS en Configuración → Almacenamiento → CD / DVD.\n\nDescárgala de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAñade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente».":
        "You must configure the Android-x86 or Bliss OS ISO in Settings → Storage → CD / DVD.\n\nDownload it from:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAdd a CD/DVD drive and choose «Use existing ISO/IMG/DMG».",
    "Error": "Error",
    "No se encuentra la carpeta 'OSX-KVM'.":
        "The 'OSX-KVM' folder was not found.",
    "Error al guardar configuración": "Error saving configuration",
    "No se pudo guardar vm_config.ini para '{0}': {1}":
        "Could not save vm_config.ini for '{0}': {1}",
    "No se puede preparar el passthrough USB":
        "Cannot prepare USB passthrough",
    "La VM no se iniciará hasta resolver el acceso al USB.\n\n{0}\n\nNo se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.":
        "The VM will not start until USB access is resolved.\n\n{0}\n\nDo not select a Root Hub. The USB stick must be unmounted from the host.",
    "Cancelando…": "Cancelling…",
    "Instalador del sistema operativo": "Operating system installer",
    "La descarga se realiza dentro de la carpeta de la VM.":
        "The download runs inside the VM folder.",
    "Máquina virtual iniciada.": "Virtual machine started.",
    "Descarga cancelada por el usuario.":
        "Download cancelled by the user.",
    "QEMU terminó con error. Revisa la consola de progreso.":
        "QEMU exited with an error. Check the progress console.",
    "Apple no devolvió una sesión de Recovery válida.":
        "Apple did not return a valid Recovery session.",
    "Apple no devolvió todos los datos del Recovery: {0}":
        "Apple did not return all the Recovery data: {0}",
    "{0} — {1:.1f} MB descargados": "{0} — {1:.1f} MB downloaded",
    "{0} — 100%": "{0} — 100%",
    "El chunklist de System Recovery está incompleto.":
        "The System Recovery chunklist is incomplete.",
    "Cabecera de chunklist de Apple no válida.":
        "Invalid Apple chunklist header.",
    "Chunklist de Apple no válido.": "Invalid Apple chunklist.",
    "Chunklist truncado en el bloque {0}.":
        "Chunklist truncated at block {0}.",
    "La verificación del Recovery falló en el bloque {0}.":
        "Recovery verification failed at block {0}.",
    "La imagen Recovery contiene datos adicionales no descritos por el chunklist.":
        "The Recovery image contains extra data not described by the chunklist.",
    "No hay una carpeta de VM seleccionada.":
        "No VM folder selected.",
    "Consultando Apple…": "Querying Apple…",
    "Descargando chunklist…": "Downloading chunklist…",
    "Descargando chunklist": "Downloading chunklist",
    "Descargando BaseSystem.dmg…": "Downloading BaseSystem.dmg…",
    "Descargando BaseSystem.dmg": "Downloading BaseSystem.dmg",
    "Verificando integridad…": "Verifying integrity…",
    "Verificación completada.": "Verification completed.",
    "No se encontró 'dmg2img' y no se pudo instalar automáticamente. Instálalo con el gestor de paquetes (en Arch/CachyOS: paru -S dmg2img).":
        "'dmg2img' was not found and could not be installed automatically. Install it with the package manager (on Arch/CachyOS: paru -S dmg2img).",
    "Convirtiendo BaseSystem.dmg → BaseSystem.img…":
        "Converting BaseSystem.dmg → BaseSystem.img…",
    "dmg2img no pudo preparar BaseSystem.img.\n{0}":
        "dmg2img could not prepare BaseSystem.img.\n{0}",
    "dmg2img terminó pero BaseSystem.img no existe o está vacío.":
        "dmg2img finished but BaseSystem.img does not exist or is empty.",

    # ================================================================
    # Tanda 4a-6: guest_integration_mixin
    # (i18n_tanda4a6_v1)
    # ================================================================
    "FALTA": "MISSING",
    "Carpetas compartidas": "Shared folders",
    "Las dependencias del host ya están instaladas.":
        "The host dependencies are already installed.",
    "Instalar dependencias": "Install dependencies",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Missing:\n\n• {0}\n\nDo you want to install them now using the system package manager?",
    "Dependencias": "Dependencies",
    "Las dependencias de carpetas compartidas quedaron instaladas y verificadas.":
        "The shared folder dependencies were installed and verified.",
    "No se pudieron instalar todas las dependencias.\n\n{0}":
        "Not all dependencies could be installed.\n\n{0}",
    "El socket de QEMU Guest Agent no está disponible.":
        "The QEMU Guest Agent socket is not available.",
    "QEMU Guest Agent cerró el canal durante la sincronización.":
        "QEMU Guest Agent closed the channel during synchronisation.",
    "Tiempo agotado sincronizando QEMU Guest Agent.":
        "Timeout synchronising QEMU Guest Agent.",
    "QEMU Guest Agent cerró el canal.":
        "QEMU Guest Agent closed the channel.",
    "Tiempo agotado esperando la respuesta de QEMU Guest Agent.":
        "Timeout waiting for the QEMU Guest Agent response.",
    "Guest Agent no devolvió el PID de guest-exec.":
        "Guest Agent did not return the guest-exec PID.",
    "guest-exec terminó con código {0}.":
        "guest-exec exited with code {0}.",
    "Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent.":
        "Timeout waiting for the command executed via QEMU Guest Agent to finish.",
    "El canal de QEMU Guest Agent no está disponible en esta VM.":
        "The QEMU Guest Agent channel is not available on this VM.",
    "El Guest Agent del invitado no respondió en {0} s (no está instalado o no se está ejecutando).":
        "The guest Guest Agent did not respond within {0} s (not installed or not running).",
    "Montaje automático": "Automatic mount",
    "La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n{0}\n\nComprueba que qemu-guest-agent esté instalado y ejecutándose en el guest (pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.":
        "The VM booted, but the automatic mount could not be configured inside the OS.\n\n{0}\n\nCheck that qemu-guest-agent is installed and running in the guest (Guest Tools tab). Once installed, the mount will be done automatically on the next VM boot.",
    "La carpeta compartida VirtioFS ya está conectada a la VM.\n\nEn Linux el dispositivo debe montarse dentro del guest. En un LiveCD no es posible hacerlo de forma persistente desde el host sin un agente instalado en el guest.\n\nComando(s):\n\n":
        "The VirtioFS shared folder is already connected to the VM.\n\nOn Linux the device must be mounted inside the guest. On a LiveCD it is not possible to do it persistently from the host without an agent installed in the guest.\n\nCommand(s):\n\n",
    "\n\nEn una instalación Linux permanente podremos añadir automontaje mediante fstab/systemd en una versión posterior.":
        "\n\nOn a permanent Linux installation we will be able to add automount via fstab/systemd in a future version.",
    "Carpeta compartida lista": "Shared folder ready",
    "Guest Tools": "Guest Tools",
    "Carpeta:\n{0}": "Folder:\n{0}",
    "Generando ISO de Guest Tools…": "Generating Guest Tools ISO…",
    "ISO creada.": "ISO created.",
    "ISO disponible: {0}": "ISO available: {0}",
    "Crear ISO de Guest Tools": "Create Guest Tools ISO",
    "No se pudo crear la ISO.\n\n{0}":
        "Could not create the ISO.\n\n{0}",
    "La ISO se guarda en la carpeta GuestTools.":
        "The ISO is saved in the GuestTools folder.",
    "Selecciona (o crea) una VM primero.":
        "Select (or create) a VM first.",
    "Creando ISO de Guest Tools…": "Creating Guest Tools ISO…",
    "Guest Tools — Adjuntar a la VM": "Guest Tools — Attach to the VM",
    "No se pudo crear ni adjuntar la ISO.\n\n{0}":
        "Could not create or attach the ISO.\n\n{0}",
    "Se creará la ISO y se adjuntará como CD/DVD a esta VM.":
        "The ISO will be created and attached as a CD/DVD to this VM.",
    "Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD.":
        "This VM already has the Guest Tools ISO attached as a CD/DVD.",
    "ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\nEn el próximo arranque, dentro del guest: monta la unidad y ejecuta\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).":
        "Guest Tools ISO attached to this VM as a CD/DVD.\n\nOn the next boot, inside the guest: mount the drive and run\nINSTALL-LINUX.SH (with sudo) or INSTALL-WINDOWS.CMD (as Administrator).",
    "No se pudo adjuntar la ISO.\n\n{0}":
        "Could not attach the ISO.\n\n{0}",
    "Estado: canal no disponible. Enciende la VM con Guest Agent activado.":
        "Status: channel not available. Start the VM with Guest Agent enabled.",
    "Estado: consultando al Guest Agent...":
        "Status: querying the Guest Agent...",
    "Estado: sin respuesta del guest agent ({0}).":
        "Status: no response from guest agent ({0}).",
    "desconocida": "unknown",
    "Estado: QEMU Guest Agent responde correctamente (v{0}).":
        "Status: QEMU Guest Agent responds correctly (v{0}).",
    "Estado: QGA respondió con un error: {0}":
        "Status: QGA replied with an error: {0}",
    "Estado: canal QGA presente; pulsa Probar conexión.":
        "Status: QGA channel present; press Test connection.",
    "Estado: canal QGA no activo en este momento.":
        "Status: QGA channel not active right now.",
    "Manual": "Manual",
    "Automático al iniciar SO": "Automatic on OS start",
    "Automático bajo demanda": "Automatic on demand",
    "Solo lectura": "Read-only",
    "Lectura / escritura": "Read / write",
    "Carpeta compartida": "Shared folder",
    "Seleccionar carpeta del host": "Select host folder",
    "Carpeta del host:": "Host folder:",
    "Etiqueta / guest:": "Label / guest:",
    "Método:": "Method:",
    "Automático": "Automatic",
    "Montaje en el guest:": "Mount in guest:",
    "Acceso:": "Access:",
    "La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.":
        "The mount policy is the same for all OSes: Manual, Automatic on OS start or Automatic on demand. The actual mount mechanism adapts to the guest OS and its integration components. On a LiveCD, persistent mount usually cannot be configured from the host.",
    "Aceptar": "OK",
    "La carpeta del host no existe o no es un directorio.":
        "The host folder does not exist or is not a directory.",
    "Desactivado": "Disabled",
    "Host → SO invitado": "Host → Guest OS",
    "SO invitado → Host": "Guest OS → Host",
    "Bidireccional": "Bidirectional",
    "No se añadirá ningún canal de clipboard.":
        "No clipboard channel will be added.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK: bidirectional. Requires spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS: clipboard integration pending.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Select a VM to check the available integration.",
    "Se activará automáticamente al iniciar la VM.":
        "It will be enabled automatically when the VM starts.",
    "No se activa.": "It is not enabled.",
    "Configuración actual: {0}. {1} {2}":
        "Current configuration: {0}. {1} {2}",
    "Clipboard": "Clipboard",
    "Configuración del clipboard guardada para esta VM.":
        "Clipboard configuration saved for this VM.",
    "Compartir": "Sharing",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Configuration saved. It will be applied on the next boot.",

    # i18n_tanda4a6_v1

    # kvm_preflight_v1
    '/dev/kvm no está disponible. La VM arrancará con emulación por software (TCG), que es 10-100× más lenta que KVM.\n\n{0}':
        '/dev/kvm is not available. The VM will boot with software emulation (TCG), which is 10-100× slower than KVM.\n\n{0}',
    "Tu usuario no puede usar /dev/kvm (no está en el grupo 'kvm'). La VM arrancará con emulación por software (muy lenta).\n\n{0}":
        "Your user cannot use /dev/kvm (not in the 'kvm' group). The VM will boot with software emulation (very slow).\n\n{0}",

    # kvm_preflight_v1_fix1
    'Idioma de la interfaz.':
        'Interface language.',

    # --------------------------------------------------------
    # media_library_host_mount_v1_i18n_en: montar/desmontar en
    # host + crear discos (VMDK/VDI/VHD/VHDX) desde la
    # biblioteca de medios.
    # --------------------------------------------------------
    '➕ Crear disco':
        '➕ Create disk',
    "Crea un disco virtual nuevo en la biblioteca con\n'qemu-img create'.\n\nFormatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ny disquete (IMG). El archivo se guarda en MediaLibrary/\ny se registra automáticamente en el índice.":
        "Create a new virtual disk in the library with\n'qemu-img create'.\n\nSupported formats: QCOW2, RAW, VMDK, VDI, VHD, VHDX\nand floppy (IMG). The file is saved in MediaLibrary/\nand automatically registered in the index.",
    '🔌 Montar en host':
        '🔌 Mount on host',
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.\n\nSe usa guestmount (FUSE, sin root) si está disponible,\no qemu-nbd (con pkexec) como alternativa.\n\nRequiere que ninguna VM que lo use esté encendida:\nQEMU mantiene un bloqueo de escritura sobre el archivo.':
        'Mount this virtual disk on the host system to\ninspect or copy its contents without starting the VM.\n\nguestmount (FUSE, no root) is used if available,\nor qemu-nbd (with pkexec) as a fallback.\n\nRequires that no VM using it is running:\nQEMU holds a write lock on the file.',
    '⏏ Desmontar del host':
        '⏏ Unmount from host',
    "Desmonta del sistema anfitrión el disco que se montó\npreviamente con 'Montar en host'.":
        "Unmount from the host system the disk previously\nmounted with 'Mount on host'.",
    'montado (rw)':
        'mounted (rw)',
    'montado (ro)':
        'mounted (ro)',
    'Herramientas de montaje':
        'Mounting tools',
    "No se encontró guestmount ni qemu-nbd en el sistema.\n\nInstala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\ncomo alternativa) con el gestor de paquetes de tu\ndistribución para poder montar discos virtuales.":
        "Neither guestmount nor qemu-nbd was found on the system.\n\nInstall 'libguestfs' and 'guestfs-tools' (or 'qemu-nbd'\nas an alternative) with your distribution's package\nmanager to be able to mount virtual disks.",
    "Faltan las herramientas de montaje y no se encontró\n'pkexec' para pedir permisos de administrador.\n\nEjecuta a mano:\n\n  sudo {0} install {1}":
        "Mounting tools are missing and 'pkexec' was not found\nto request administrator permissions.\n\nRun manually:\n\n  sudo {0} install {1}",
    'Se necesitan herramientas adicionales para montar discos\nen el host.\n\n  • guestmount (libguestfs) es lo ideal: sin root, detecta\n    particiones y sistemas de archivos automáticamente.\n  • qemu-nbd es la alternativa si no hay libguestfs.\n\n¿Quieres instalar las herramientas ahora? Se pedirá la\ncontraseña de administrador.\n\nComando:\n  {0}':
        'Additional tools are needed to mount disks\non the host.\n\n  • guestmount (libguestfs) is ideal: no root, detects\n    partitions and filesystems automatically.\n  • qemu-nbd is the fallback if libguestfs is not available.\n\nDo you want to install the tools now? You will be asked\nfor the administrator password.\n\nCommand:\n  {0}',
    'No se pudo ejecutar el comando de instalación.\n\n{0}':
        'Could not run the installation command.\n\n{0}',
    'La instalación falló.\n\n{0}':
        'Installation failed.\n\n{0}',
    'Instalación completada.':
        'Installation completed.',
    'Montajes previos detectados':
        'Previous mounts detected',
    'Se encontraron {0} disco(s) montados en el sistema de\nuna sesión anterior de la aplicación:\n\n{1}\n\n¿Quieres desmontarlos ahora?':
        '{0} disk(s) mounted on the system from a previous\nsession of the application were found:\n\n{1}\n\nDo you want to unmount them now?',
    'Montar en el host':
        'Mount on host',
    'Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>El disco debe estar apagado: ninguna VM que lo use puede\nestar encendida, porque QEMU mantiene un bloqueo de escritura\nsobre el archivo.':
        '<b>{0}</b> will be mounted on the host system.<br><br>The disk must be powered off: no VM using it can be\nrunning, because QEMU holds a write lock on the file.',
    'Permitir escritura (montar en modo read-write)':
        'Allow writing (mount in read-write mode)',
    '⚠ Con read-write, escribir en el disco puede corromper el\nsistema de archivos si después se arranca la VM sin\ndesmontarlo. Para inspeccionar o copiar, deja read-only.\n\nLos archivos que crees desde el host se atribuirán a tu\nusuario del guest (uid/gid {0}:{1}) cuando el sistema de\narchivos lo permita; si no, aparecerán como root.':
        '⚠ With read-write, writing to the disk can corrupt the\nfilesystem if the VM is later started without\nunmounting it. To inspect or copy, keep read-only.\n\nFiles you create from the host will be attributed to your\nguest user (uid/gid {0}:{1}) when the filesystem\nallows it; otherwise, they will appear as root.',
    'Montar':
        'Mount',
    'Selecciona un disco virtual para montarlo en el host.':
        'Select a virtual disk to mount it on the host.',
    'Selecciona un disco previamente montado para desmontarlo.':
        'Select a previously mounted disk to unmount it.',
    'Solo se pueden montar discos virtuales\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).':
        'Only virtual disks can be mounted\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).',
    "Este disco ya está montado. Usa '⏏ Desmontar del host'\npara liberarlo.":
        "This disk is already mounted. Use '⏏ Unmount from host'\nto release it.",
    "La VM '{0}' está usando este disco y está encendida.\nApágala para poder montarlo en el host.":
        "VM '{0}' is using this disk and is running.\nShut it down to mount it on the host.",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.':
        'Mount this virtual disk on the host system to\ninspect or copy its contents without starting the VM.',
    'Desmontar de {0}':
        'Unmount from {0}',
    'Este disco no está montado en el host.':
        'This disk is not mounted on the host.',
    'Montar en host':
        'Mount on host',
    'Error inesperado al montar el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unexpected error while mounting the disk.\n\nYou can see the details in the Progress Console.\n\n{0}',
    'Este disco ya está montado.':
        'This disk is already mounted.',
    "La VM '{0}' está usando este disco y está encendida.\n\nApágala antes de montar el disco en el host: QEMU\nmantiene un bloqueo de escritura sobre el archivo\ny el montaje fallaría.":
        "VM '{0}' is using this disk and is running.\n\nShut it down before mounting the disk on the host: QEMU\nholds a write lock on the file and the mount would fail.",
    'Las herramientas de montaje siguen sin estar\ndisponibles después de la instalación.':
        'Mounting tools are still not available\nafter installation.',
    'No se pudo crear el punto de montaje.\n\n{0}':
        'Could not create the mount point.\n\n{0}',
    'Aviso: el sistema de archivos del guest no acepta mapeo de usuario; los archivos que crees desde el host aparecerán como root en el guest. Para trabajar sin problemas de permisos, escribe desde el guest en lugar del host.':
        'Warning: the guest filesystem does not accept user mapping; files you create from the host will appear as root in the guest. To work without permission issues, write from the guest instead of the host.',
    'Disco montado':
        'Disk mounted',
    "'{0}' montado correctamente.\n\nPunto de montaje: {1}\nModo: {2}{3}":
        "'{0}' mounted successfully.\n\nMount point: {1}\nMode: {2}{3}",
    'read-only':
        'read-only',
    'read-write':
        'read-write',
    'No se pudo montar el disco.\n\n{0}':
        'Could not mount the disk.\n\n{0}',
    "Montando '{0}'":
        "Mounting '{0}'",
    'Preparando el punto de montaje en el host…':
        'Preparing the mount point on the host…',
    'Desmontar del host':
        'Unmount from host',
    'Error inesperado al desmontar.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unexpected error while unmounting.\n\nYou can see the details in the Progress Console.\n\n{0}',
    "¿Desmontar '{0}' de {1}?":
        "Unmount '{0}' from {1}?",
    "'{0}' desmontado correctamente.":
        "'{0}' unmounted successfully.",
    'No se pudo desmontar.\n\n{0}':
        'Could not unmount.\n\n{0}',
    "Desmontando '{0}'":
        "Unmounting '{0}'",
    'Liberando el punto de montaje…':
        'Releasing the mount point…',
    'Crear disco':
        'Create disk',
    'Error inesperado al crear el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Unexpected error while creating the disk.\n\nYou can see the details in the Progress Console.\n\n{0}',
    'La biblioteca no está disponible.':
        'The library is not available.',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n¿Sobrescribir? (se perderá el contenido anterior)':
        'A file with that name already exists in the library:\n\n{0}\n\nOverwrite? (previous contents will be lost)',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils / qemu-img).":
        "'qemu-img' was not found. Install it (package qemu-utils / qemu-img).",
    'Disco creado':
        'Disk created',
    'Se creó el disco correctamente.\n\nArchivo: {0}\nTamaño: {1}\nFormato: {2}':
        'Disk created successfully.\n\nFile: {0}\nSize: {1}\nFormat: {2}',
    'No se pudo crear el disco.\n\n{0}':
        'Could not create the disk.\n\n{0}',
    "Creando '{0}'":
        "Creating '{0}'",
    'Ejecutando qemu-img create…':
        'Running qemu-img create…',
    'Disco duro VMDK (VirtualBox / VMware)':
        'VMDK hard disk (VirtualBox / VMware)',
    'Disco duro VDI (VirtualBox nativo)':
        'VDI hard disk (VirtualBox native)',
    'Disco duro VHD (Hyper-V antiguo)':
        'VHD hard disk (legacy Hyper-V)',
    'Disco duro VHDX (Hyper-V moderno)':
        'VHDX hard disk (modern Hyper-V)',
    'Preasignación:':
        'Preallocation:',
    'Expandible: el archivo crece solo según se usa (recomendado).\nFijo: reserva todo el espacio en disco desde el momento de\nsu creación. Tarda más y ocupa más, pero el rendimiento de\nescritura es más predecible.':
        'Expandable: the file grows as it is used (recommended).\nFixed: reserves all disk space at creation time.\nTakes longer and uses more space, but write performance\nis more predictable.',
    'Expandible: preallocation=off (recomendado).\nFijo: preallocation=full. Reserva todo el espacio\nen el host desde el momento de su creación.':
        'Expandable: preallocation=off (recommended).\nFixed: preallocation=full. Reserves all the space\non the host at creation time.',
    'Expandible: VDI dinámico (recomendado).\nFijo: static=on. Reserva todo el espacio en el host.':
        'Expandable: dynamic VDI (recommended).\nFixed: static=on. Reserves all the space on the host.',
    'Expandible: VHD dynamic (recomendado).\nFijo: subformat=fixed. Reserva todo el espacio.':
        'Expandable: dynamic VHD (recommended).\nFixed: subformat=fixed. Reserves all the space.',
    'Formato VMDK monolithicSparse (compatible con VirtualBox y VMware). El archivo crece según se usa; las snapshots internas de QEMU no aplican.':
        'VMDK monolithicSparse format (compatible with VirtualBox and VMware). The file grows as it is used; QEMU internal snapshots do not apply.',
    'Formato VDI nativo de VirtualBox. El archivo crece según se usa.':
        'VDI format native to VirtualBox. The file grows as it is used.',
    "Formato VHD (Hyper-V hasta Windows 2008 R2). Compatible con la mayoría de hipervisores. QEMU lo llama internamente 'vpc'.":
        "VHD format (Hyper-V up to Windows 2008 R2). Compatible with most hypervisors. QEMU calls it internally 'vpc'.",
    'Formato VHDX (Hyper-V moderno, desde Windows 2012). Soporta discos de hasta 64 TB y bloques de 4 KB.':
        'VHDX format (modern Hyper-V, since Windows 2012). Supports disks up to 64 TB and 4 KB blocks.',
    'Disco virtual expandible.':
        'Expandable virtual disk.',
}
# --------------------------------------------------------------------

# --------------------------------------------------------------------
# i18n_context_merge_v1: en runtime, self.tr() busca bajo la clase real
# del objeto (VirtualMachineManagerApp). pylupdate6, en cambio, extrae
# cada self.tr() bajo la clase donde esta escrito el metodo (p.ej.
# VmLifecycleMixin). Si no coinciden, la traduccion no se aplica.
#
# Este paso mueve TODOS los mensajes de contextos <XxxMixin> al contexto
# <VirtualMachineManagerApp> y deduplica por source. Asi self.tr() en
# cualquier mixin encuentra su traduccion.
# --------------------------------------------------------------------
CONTEXTO_DESTINO = "VirtualMachineManagerApp"


def _es_contexto_de_mixin(nombre):
    """True si el nombre parece un mixin interno del proyecto."""
    if not nombre:
        return False
    # Todos los mixins del proyecto terminan en "Mixin".
    return nombre.endswith("Mixin")


def normalizar_contextos_ts(tree):
    """Mueve los mensajes de los mixins a VirtualMachineManagerApp."""
    root = tree.getroot()
    contexto_destino = None
    movidos = 0

    # Buscar o crear el contexto destino.
    for ctx in root.findall("context"):
        if ctx.find("name") is not None and ctx.find("name").text == CONTEXTO_DESTINO:
            contexto_destino = ctx
            break
    if contexto_destino is None:
        contexto_destino = ET.SubElement(root, "context")
        ET.SubElement(contexto_destino, "name").text = CONTEXTO_DESTINO

    # Sources ya presentes en el destino (para deduplicar).
    existentes = set()
    for msg in contexto_destino.findall("message"):
        s = msg.find("source")
        if s is not None:
            existentes.add(s.text or "")

    # Recorrer contextos origen.
    for ctx in list(root.findall("context")):
        if ctx is contexto_destino:
            continue
        name_el = ctx.find("name")
        if name_el is None or not _es_contexto_de_mixin(name_el.text):
            continue
        for msg in list(ctx.findall("message")):
            s = msg.find("source")
            if s is None:
                continue
            source = s.text or ""
            tr = msg.find("translation")
            # Solo mover si tiene traduccion real (no obsoleta).
            if tr is not None and tr.get("type") == "obsolete":
                continue
            if source in existentes:
                # Ya hay uno en el destino; descartar el del mixin.
                ctx.remove(msg)
                continue
            # Mover el mensaje al destino.
            ctx.remove(msg)
            contexto_destino.append(msg)
            existentes.add(source)
            movidos += 1
        # Si el contexto origen se quedo vacio, borrarlo.
        if len(ctx.findall("message")) == 0:
            root.remove(ctx)

    return movidos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang", default="en",
        help="Codigo de idioma (en, fr, pt_BR, it, de). Default: en.",
    )
    args = parser.parse_args()
    lang = args.lang

    if lang == "en":
        dict_tr = TRANSLATIONS
    else:
        dict_tr = _load_external_dict(lang)
        if dict_tr is None:
            print("[!] No existe translations/vm_%s.py" % lang)
            sys.exit(1)

    ts_path = os.path.join("i18n", "vm_%s.ts" % lang)
    if not os.path.isfile(ts_path):
        print("[!] No existe %s. Corre antes:" % ts_path)
        print("    pylupdate6 *.py -ts %s" % ts_path)
        sys.exit(1)

    tree = ET.parse(ts_path)
    root = tree.getroot()

    filled = 0
    unfinished = 0
    unfinished_list = []
    for msg in root.iter("message"):
        src_el = msg.find("source")
        tr_el = msg.find("translation")
        if src_el is None or tr_el is None:
            continue
        source = src_el.text or ""
        # Los mensajes obsoletos se dejan tal cual: no se traducen ni
        # se cuentan como pendientes.
        if tr_el.get("type") == "obsolete":
            continue
        if source in dict_tr:
            tr_el.text = dict_tr[source]
            if "type" in tr_el.attrib:
                del tr_el.attrib["type"]
            filled += 1
        else:
            if tr_el.get("type") != "unfinished":
                tr_el.set("type", "unfinished")
            unfinished += 1
            unfinished_list.append(source)

    # i18n_context_merge_v1: mover mensajes de mixins a
    # VirtualMachineManagerApp antes de compilar.
    _movidos = normalizar_contextos_ts(tree)
    if _movidos:
        print("   (normalizados %d mensajes de contextos de mixin)" % _movidos)

    xml_str = ET.tostring(root, encoding="unicode")
    with open(ts_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write("<!DOCTYPE TS>\n")
        f.write(xml_str)

    print("OK [%s] %d traducidas, %d pendientes." % (lang, filled, unfinished))
    if unfinished_list:
        print()
        print("Pendientes (no estan en el diccionario):")
        for s in unfinished_list:
            print("    %r" % s)
    print()
    print("Compila con:")
    print("    lrelease6 %s" % ts_path)


if __name__ == "__main__":
    main()
