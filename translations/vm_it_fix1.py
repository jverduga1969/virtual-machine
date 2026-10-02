# -*- coding: utf-8 -*-
"""vm_it_fix1 - Traduzioni in italiano - Chiusura.

Riempe le stringhe rimaste non tradotte dopo le 5 tanda.
Chiavi copiate letteralmente dal .ts per garantire corrispondenza esatta.
"""

TRANSLATIONS = {

    # ================================================================
    # guest_integration_mixin.py - sottoscheda Condividi cartelle
    # ================================================================
    "Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).":
        "Integrazione Host ↔ Guest. Qui vengono configurate le cartelle condivise e gli appunti (clipboard).",
    "Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.":
        "Condividi directory dell'host con il guest. Automatico usa VirtioFS su Linux quando virtiofsd è disponibile, 9p come fallback e SMB per Windows/macOS. Sola lettura impedisce al guest di modificare i file dell'host.",
    "Host": "Host",
    "Guest / etiqueta": "Guest / etichetta",
    "Método": "Metodo",
    "Montaje en el guest": "Montaggio nel guest",
    "Acceso": "Accesso",
    "\u2795 Agregar": "\u2795 Aggiungi",
    "\U0001f4be Guardar": "\U0001f4be Salva",
    "Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.":
        "Guest Tools raccoglie l'integrazione del sistema guest: QEMU Guest Agent, driver VirtIO e, su Windows, componenti SPICE. L'ISO può essere montata come CD/DVD su qualsiasi VM.",
    "QEMU Guest Agent": "QEMU Guest Agent",
    "Activar canal QEMU Guest Agent al iniciar la VM":
        "Attiva canale QEMU Guest Agent all'avvio della VM",
    "Canal:": "Canale:",
    "Estado: no comprobado": "Stato: non verificato",
    "\U0001f50e Probar conexión": "\U0001f50e Testa connessione",
    "\U0001f4bf Crear / actualizar ISO Guest Tools":
        "\U0001f4bf Crea / aggiorna ISO Guest Tools",
    "\U0001f9f0 Adjuntar a esta VM": "\U0001f9f0 Collega a questa VM",
    "Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.":
        "Crea l'ISO se manca e la collega come CD/DVD alla VM selezionata, in un solo passo.",
    "\U0001f4c2 Abrir carpeta de Guest Tools":
        "\U0001f4c2 Apri cartella Guest Tools",
    "Acciones:": "Azioni:",
    "Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.":
        "Linux: installa qemu-guest-agent da questa ISO o dal gestore di pacchetti. Windows: INSTALL-WINDOWS.CMD scarica e installa VirtIO Guest Tools e SPICE Guest Tools dalle loro fonti ufficiali. Poi riavvia il guest.",
    "Compartir clipboard": "Condividi appunti",
    "Dirección:": "Direzione:",
    "Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.":
        "Linux e Windows: verrà usato QEMU vdagent + canale VirtIO/SPICE e GTK per appunti bidirezionali. Il guest deve avere spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS sarà testato in una fase specifica.",
    "\U0001f4be Guardar configuración": "\U0001f4be Salva configurazione",
    "Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.":
        "Configurazione per VM. Il meccanismo concreto verrà selezionato in base al SO guest e al suo supporto di integrazione.",
    "Compartir Carpetas": "Condividi cartelle",

    # ================================================================
    # Pannello Aiuto + valori dinamici del pannello host
    # ================================================================
    "<h2>Ayuda de Virtual.Machine</h2>": "<h2>Aiuto di Virtual.Machine</h2>",
    "OK": "OK",
    " ({0})": " ({0})",
    "SIN COMPROBAR": "NON VERIFICATO",
    "Virtualización: sin comprobar": "Virtualizzazione: non verificata",
    "Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema.":
        "Premi 'Verifica dipendenze' per eseguire la diagnostica completa del sistema.",
    "Distribución: {0}": "Distribuzione: {0}",
    "Gestor de paquetes: {0}": "Gestore di pacchetti: {0}",
    "no encontrado": "non trovato",
    "firmware disponible": "firmware disponibile",
    "sin plantilla Secure Boot": "nessun template Secure Boot",
    "módulos": "moduli",
    "módulo no cargado": "modulo non caricato",
    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Audio {5} | GPU {6}":
        "Virtualizzazione: {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Audio {5} | GPU {6}",
    "REVISAR": "VERIFICARE",
    "sí": "sì",
    "no": "no",
    "Distribución: {0}\n"
    "Gestor de paquetes: {1}\n"
    "Secure Boot: {2}\n"
    "VirtIO: {3}\n"
    "Audio: {4}\n"
    "GPU: {5}\n"
    "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}":
        "Distribuzione: {0}\n"
        "Gestore di pacchetti: {1}\n"
        "Secure Boot: {2}\n"
        "VirtIO: {3}\n"
        "Audio: {4}\n"
        "GPU: {5}\n"
        "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}",
    "disponible": "disponibile",
    "no disponible": "non disponibile",
    "no detectado": "non rilevato",
    "La comprobación/reparación terminó correctamente.":
        "La verifica/riparazione è terminata correttamente.",
    "No se pudieron reparar todas las dependencias.\n\n{0}":
        "Non è stato possibile riparare tutte le dipendenze.\n\n{0}",
    "Carpetas compartidas": "Cartelle condivise",
    "El socket de QEMU Guest Agent no está disponible.":
        "Il socket di QEMU Guest Agent non è disponibile.",
    "QEMU Guest Agent cerró el canal durante la sincronización.":
        "QEMU Guest Agent ha chiuso il canale durante la sincronizzazione.",
    "Tiempo agotado sincronizando QEMU Guest Agent.":
        "Timeout durante la sincronizzazione di QEMU Guest Agent.",
    "QEMU Guest Agent cerró el canal.":
        "QEMU Guest Agent ha chiuso il canale.",
    "Tiempo agotado esperando la respuesta de QEMU Guest Agent.":
        "Timeout in attesa della risposta di QEMU Guest Agent.",
    "Guest Agent no devolvió el PID de guest-exec.":
        "Il Guest Agent non ha restituito il PID di guest-exec.",
    "guest-exec terminó con código {0}.":
        "guest-exec è terminato con codice {0}.",
    "Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent.":
        "Timeout in attesa del completamento del comando eseguito tramite QEMU Guest Agent.",
    "El canal de QEMU Guest Agent no está disponible en esta VM.":
        "Il canale di QEMU Guest Agent non è disponibile su questa VM.",
    "El Guest Agent del invitado no respondió en {0} s (no está instalado o no se está ejecutando).":
        "Il Guest Agent del guest non ha risposto in {0} s (non installato o non in esecuzione).",

    # ================================================================
    # Pulsante 'Agrandar' della libreria
    # ================================================================
    "\u2197 Agrandar": "\u2197 Espandi",

    # ================================================================
    # passthrough_mixin.py: menu Supporti (CD/DVD + USB)
    # ================================================================
    "\U0001f4c0 Unidades ópticas": "\U0001f4c0 Unità ottiche",
    "      (Sin unidades CD/DVD)": "      (Nessuna unità CD/DVD)",
    "\U0001f310 descargar instalador al iniciar":
        "\U0001f310 scarica installer all'avvio",
    "\U0001f310 descargar Recovery al iniciar":
        "\U0001f310 scarica Recovery all'avvio",
    "   \U0001f4c0 {0} \u2014 {1}": "   \U0001f4c0 {0} \u2014 {1}",
    "\U0001f4c2 Cambiar medio…": "\U0001f4c2 Cambia supporto…",
    "\u23cf Expulsar medio": "\u23cf Espelli supporto",
    "\U0001f50c Dispositivos USB": "\U0001f50c Dispositivi USB",
    "      (La VM debe estar encendida para conectarlos)":
        "      (La VM deve essere accesa per collegarli)",
    "      Error al detectar USB: {0}":
        "      Errore durante il rilevamento USB: {0}",
    "      (No hay dispositivos USB detectados)":
        "      (Nessun dispositivo USB rilevato)",
    "conectado a la VM": "collegato alla VM",
    "disponible en el host": "disponibile sull'host",
    "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
    "Estado: {5}\n\n{6}":
        "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
        "Stato: {5}\n\n{6}",
    "Clic para DESCONECTAR de la VM": "Clicca per SCOPLLEGARE dalla VM",
    "Clic para CONECTAR a la VM": "Clicca per COLLEGARE alla VM",
    "(Selecciona una VM primero)": "(Seleziona prima una VM)",
    "\U0001f4bf Medios de '{0}'": "\U0001f4bf Supporti di '{0}'",
    "\U0001f504 Refrescar": "\U0001f504 Aggiorna",
    "\u2699 Gestionar USB en Passthrough…":
        "\u2699 Gestisci USB in Passthrough…",
    "Grupo {0}": "Gruppo {0}",
    "Sin grupo IOMMU": "Nessun gruppo IOMMU",
    " \u2022 {0}": " \u2022 {0}",
    "\u26a0 Revisar": "\u26a0 Verifica",
    "\u2713 Acceso OK": "\u2713 Accesso OK",
    "\u26a0 Revisar acceso": "\u26a0 Verifica accesso",
    "Passthrough: teclado o ratón del host":
        "Passthrough: tastiera o mouse dell'host",
    "Passthrough USB": "Passthrough USB",
    "Selecciona un dispositivo USB.": "Seleziona un dispositivo USB.",
    "La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.":
        "La VM non è accesa; usa Salva selezione per collegarlo al prossimo avvio.",
    "Dispositivo USB conectado en caliente a la VM.\n\n"
    "Nota: el host debe permitir acceso a /dev/bus/usb y el "
    "dispositivo no debería estar siendo usado por el sistema "
    "anfitrión.":
        "Dispositivo USB collegato a caldo alla VM.\n\n"
        "Nota: l'host deve consentire l'accesso a /dev/bus/usb e il "
        "dispositivo non dovrebbe essere in uso dal sistema "
        "host.",
    "Error al conectar USB": "Errore durante il collegamento USB",
    "La VM no está encendida.": "La VM non è accesa.",
    "Solicitud de desconexión USB enviada a QEMU.":
        "Richiesta di scollegamento USB inviata a QEMU.",
    "Error al desconectar USB": "Errore durante lo scollegamento USB",

    # ================================================================
    # Storage: tipi di disco
    # ================================================================
    "\U0001f4bd SATA": "\U0001f4bd SATA",
    "\u26a1 NVMe": "\u26a1 NVMe",
    "\u274c No hay un QCOW2 escribible disponible para snapshots completos de VM.":
        "\u274c Nessun QCOW2 scrivibile disponibile per istantanee complete di VM.",
    "\u2705 Disco para estado de VM: {0} \u00b7 tamaño virtual: {1} \u00b7 archivo actual: {2} \u00b7 espacio libre del sistema de archivos: {3} \u00b7 reserva orientativa inicial: {4}. El snapshot QCOW2 crece según se modifican bloques.":
        "\u2705 Disco per stato della VM: {0} \u00b7 dimensione virtuale: {1} \u00b7 file attuale: {2} \u00b7 spazio libero del filesystem: {3} \u00b7 riserva indicativa iniziale: {4}. L'istantanea QCOW2 cresce man mano che i blocchi vengono modificati.",
    "\u26a0 {0} El snapshot podría fallar al quedarse sin espacio.":
        "\u26a0 {0} L'istantanea potrebbe fallire se rimane senza spazio.",
    "Disco": "Disco",
    "FDC": "FDC",
    "\U0001f310 Descargar instalador de Internet al iniciar":
        "\U0001f310 Scarica installer da Internet all'avvio",
    "\U0001f310 Instalador por Internet (se descargará al iniciar)":
        "\U0001f310 Installer da Internet (verrà scaricato all'avvio)",
    "\U0001f310 Descargar System Recovery al iniciar":
        "\U0001f310 Scarica System Recovery all'avvio",
    "\U0001f310 System Recovery (se descargará al iniciar)":
        "\U0001f310 System Recovery (verrà scaricato all'avvio)",
    "Sin medio": "Nessun supporto",
    "Sin grupo": "Nessun gruppo",

    # ================================================================
    # Popup 'Pausar la VM'
    # ================================================================
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "\u2022 Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "\u2022 Reanudar: vuelve a ejecutar la VM pausada.\n"
    "\u2022 Tomar Snapshot: guarda el estado a disco y pausa.":
        "Metti in pausa la VM. Usa la freccia per più opzioni:\n"
        "\u2022 Pausa (rapida): ferma senza salvare lo stato su disco.\n"
        "\u2022 Riprendi: riprende l'esecuzione della VM in pausa.\n"
        "\u2022 Crea istantanea: salva lo stato su disco e mette in pausa.",

    # ================================================================
    # _ExportOvfDialog
    # ================================================================
    "Exportar como OVF/OVA - {0}": "Esporta come OVF/OVA - {0}",
    "Exporta <b>{0}</b> como OVA (un solo archivo) o como OVF (carpeta con descriptor + discos sueltos).":
        "Esporta <b>{0}</b> come OVA (file singolo) o come OVF (cartella con descrittore + dischi sfusi).",
    "Formato del disco": "Formato del disco",
    "QCOW2 (recomendado) - instantaneo y comprimido":
        "QCOW2 (consigliato) - istantanea e compresso",
    "El disco se aplana (descartando snapshots internos) y se comprime con zlib. Ideal para reimportar en esta misma app.":
        "Il disco viene appiattito (scartando le istantanee interne) e compresso con zlib. Ideale per reimportare in questa stessa app.",
    "VMDK stream-optimized - maxima compatibilidad con VirtualBox/VMware":
        "VMDK stream-optimized - massima compatibilità con VirtualBox/VMware",
    "Requiere conversion previa con qemu-img. Tarda mas y necesita espacio temporal. VMDK stream-optimized ya descarta snapshots.":
        "Richiede conversione preventiva con qemu-img. Più lento e necessita spazio temporaneo. VMDK stream-optimized scarta già le istantanee.",
    "Opciones adicionales": "Opzioni aggiuntive",
    "Incluir medio de instalacion (BaseSystem.img)":
        "Includi supporto di installazione (BaseSystem.img)",
    "Incluir archivos ISO en el OVA":
        "Includi file ISO nell'OVA",
    "Exportar": "Esporta",
    "El disco se convertira a <b>VMDK stream-optimized</b>. Este formato ya descarta los snapshots internos.":
        "Il disco verrà convertito in <b>VMDK stream-optimized</b>. Questo formato scarta già le istantanee interne.",
    "Los discos QCOW2 se <b>aplanan y comprimen</b> automaticamente al exportar: se descartan los snapshots internos y se aplica compresion zlib. Reduce el OVA entre un 40% y un 60%.":
        "I dischi QCOW2 vengono <b>appiattiti e compressi</b> automaticamente durante l'esportazione: le istantanee interne vengono scartate e viene applicata la compressione zlib. Riduce l'OVA dal 40% al 60%.",

    # ================================================================
    # _OvfImportPreviewDialog
    # ================================================================
    "Se ha leído el descriptor OVF. Revisa los datos detectados y corrige lo que haga falta antes de importar.<br><br><i>El sistema operativo detectado puede ser ambiguo: ajústalo si el original no coincide.</i>":
        "Il descrittore OVF è stato letto. Controlla i dati rilevati e correggi ciò che serve prima di importare.<br><br><i>Il sistema operativo rilevato potrebbe essere ambiguo: adattalo se l'originale non corrisponde.</i>",
    "(sin nombre)": "(senza nome)",
    "(sin discos)": "(senza dischi)",
    "<b>Detectado en el OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}":
        "<b>Rilevato nell'OVF:</b><br>SO: {0} {1}<br>CPU: {2} &nbsp; RAM: {3} MB<br>Dischi: {4} — {5}",
    "Nombre de la VM:": "Nome della VM:",
    "GNU / Linux": "GNU / Linux",
    "Microsoft Windows": "Microsoft Windows",
    "macOS": "macOS",
    "Android (Android-x86 / Bliss OS)": "Android (Android-x86 / Bliss OS)",
    "Plataforma:": "Piattaforma:",
    "Distribución / versión:": "Distribuzione / versione:",
    "Importar solo la configuración (sin copiar los discos)":
        "Importa solo la configurazione (senza copiare i dischi)",
    "Si está marcado, se importan solo los datos del descriptor (CPU, RAM, red, sistema operativo) y NO se convierten ni copian los discos. Útil para reutilizar una configuración sin duplicar gigabytes de disco.":
        "Se selezionato, vengono importati solo i dati del descrittore (CPU, RAM, rete, sistema operativo) e i dischi NON vengono convertiti né copiati. Utile per riutilizzare una configurazione senza duplicare gigabyte di disco.",
    "Importar": "Importa",
    "Distribución:": "Distribuzione:",
    "Versión de Windows:": "Versione di Windows:",
    "Versión de macOS:": "Versione di macOS:",
    "Distribución Android:": "Distribuzione Android:",
    "Debes escribir un nombre para la VM importada.":
        "Devi inserire un nome per la VM importata.",
}
