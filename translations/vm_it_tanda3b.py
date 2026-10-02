# -*- coding: utf-8 -*-
"""vm_it_tanda3b - Traduzioni in italiano - Tanda 3b.

Copre:
  - Istantanee automatiche programmate (snapshot_schedule_mixin).
  - Backup automatici programmati (backup_schedule_mixin).
  - Intestazione della scheda Backup.
"""

TRANSLATIONS = {

    # ================================================================
    # Istantanee automatiche programmate
    # ================================================================
    "Snapshots automaticos programados": "Istantanee automatiche programmate",
    "Activar": "Attiva",
    "Cuando esta activo, la app crea snapshots de disco automaticamente en esta VM segun la frecuencia elegida.\n\n"
    "Los snapshots programados son SOLO DE DISCOS (no guardan RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan por antiguedad al superar el limite de retencion.\n\n"
    "No se ejecutan si la VM esta apagada.":
        "Quando e attivo, l'app crea automaticamente istantanee disco su questa VM in base alla frequenza scelta.\n\n"
        "Le istantanee programmate sono SOLO DISCO (non salvano RAM ne finestre). Vengono create con il prefisso 'auto_' e rimosse per anzianita al superamento del limite di conservazione.\n\n"
        "Non vengono eseguite se la VM e spenta.",
    "Cada hora": "Ogni ora",
    "Cada 6 horas": "Ogni 6 ore",
    "Cada 12 horas": "Ogni 12 ore",
    "Diario": "Giornaliero",
    "Semanal": "Settimanale",
    "Frecuencia con la que se crea el snapshot automatico.\n"
    "El primer snapshot se crea pasada una frecuencia completa desde la activacion (o desde el ultimo, si ya habia uno).":
        "Frequenza con cui viene creata l'istantanea automatica.\n"
        "La prima istantanea viene creata dopo un'intera frequenza dall'attivazione (o dall'ultima, se ce n'era gia una).",
    "Frecuencia:": "Frequenza:",
    "Cuantos snapshots automaticos conservar. Al superar este numero se eliminan los mas antiguos (solo los que empiezan por 'auto_'; los manuales nunca se tocan).":
        "Quante istantanee automatiche conservare. Al superamento di questo numero vengono eliminate le piu vecchie (solo quelle che iniziano con 'auto_'; quelle manuali non vengono mai toccate).",
    "Conservar:": "Conserva:",
    "Los snapshots programados son <b>solo de discos</b>: no guardan RAM ni estado de ventanas. No congelan la VM del usuario (el snapshot completo si puede hacerlo).":
        "Le istantanee programmate sono <b>solo disco</b>: non salvano RAM ne stato delle finestre. Non congelano la VM dell'utente (un'istantanea completa puo farlo).",
    "Selecciona una VM para programar snapshots.":
        "Seleziona una VM per programmare le istantanee.",
    "Desactivado para esta VM.": "Disattivato per questa VM.",
    "Sin snapshots programados todavia. Se creara el primero tras cumplirse la frecuencia elegida.":
        "Nessuna istantanea programmata ancora. La prima verra creata al termine della frequenza scelta.",
    "Pendiente (ultimo: {0}). Se ejecutara en el proximo chequeo del scheduler.":
        "In attesa (ultima: {0}). Verra eseguita al prossimo controllo dello scheduler.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min.":
        "Ultima: {0} \u00b7 Prossima tra ~{1} min.",
    "Ultimo: {0}": "Ultima: {0}",

    # ================================================================
    # Backup automatici programmati
    # ================================================================
    "Backups automaticos programados": "Backup automatici programmati",
    "Cuando esta activo, la app copia la carpeta completa de la VM "
    "(discos, configuracion, snapshots) al destino elegido segun "
    "la frecuencia. Los backups son carpetas independientes; "
    "puedes borrarlos manualmente o dejar que la retencion los "
    "limpie.":
        "Quando e attivo, l'app copia l'intera cartella della VM "
        "(dischi, configurazione, istantanee) nella destinazione scelta in base "
        "alla frequenza. I backup sono cartelle indipendenti; "
        "puoi eliminarli manualmente o lasciare che la conservazione li "
        "pulisca.",
    "Carpeta del host donde guardar los backups":
        "Cartella dell'host dove salvare i backup",
    "Elegir carpeta...": "Scegli cartella...",
    "Destino:": "Destinazione:",
    "Cuantos backups conservar en el destino. Tras cada backup "
    "exitoso se borran los mas antiguos por encima de este numero.":
        "Quanti backup conservare nella destinazione. Dopo ogni backup "
        "riuscito, i piu vecchi oltre questo numero vengono eliminati.",
    "Tambien cuando la VM esta encendida": "Anche quando la VM e accesa",
    "Desactivado (recomendado): los backups solo se ejecutan con "
    "la VM apagada.\n\n"
    "Activado: si la VM esta encendida, se copian los discos de "
    "todos modos; la copia puede quedar inconsistente porque QEMU "
    "esta escribiendo en el .qcow2 en ese momento. La restauracion "
    "podria requerir fsck o no arrancar. Solo si estas dispuesto a "
    "asumir ese riesgo.":
        "Disattivato (consigliato): i backup vengono eseguiti solo con "
        "la VM spenta.\n\n"
        "Attivato: se la VM e accesa, i dischi vengono copiati "
        "comunque; la copia puo risultare incoerente perche QEMU "
        "sta scrivendo sul .qcow2 in quel momento. Il ripristino "
        "potrebbe richiedere fsck o non avviarsi. Solo se sei disposto "
        "ad assumerti questo rischio.",
    "Los backups son <b>carpetas</b> con todos los archivos de la "
    "VM (discos + configuraci\u00f3n + snapshots + capturas). No "
    "incluyen pids, sockets ni logs. Para restaurar, usa el bot\u00f3n "
    "<b>Importar</b> de la pesta\u00f1a Resumen con la carpeta del "
    "backup.":
        "I backup sono <b>cartelle</b> con tutti i file della "
        "VM (dischi + configurazione + istantanee + schermate). Non "
        "includono pid, socket ne log. Per ripristinare, usa il pulsante "
        "<b>Importa</b> nella scheda Panoramica con la cartella del "
        "backup.",
    "Backup ahora": "Backup adesso",
    "Ejecuta un backup inmediato con la configuracion actual, sin "
    "esperar a la proxima programacion.":
        "Esegue un backup immediato con la configurazione attuale, senza "
        "attendere la prossima programmazione.",
    "Elegir carpeta de destino para backups":
        "Scegli cartella di destinazione per i backup",
    "Selecciona una VM para programar backups.":
        "Seleziona una VM per programmare i backup.",
    "Falta elegir una carpeta de destino.":
        "Devi scegliere una cartella di destinazione.",
    "Sin backups todavia. Libre en destino: {0}. "
    "Se creara el primero tras cumplirse la frecuencia.":
        "Nessun backup ancora. Libero nella destinazione: {0}. "
        "Il primo verra creato al termine della frequenza.",
    "Pendiente (ultimo: {0}). Libre: {1}.":
        "In attesa (ultimo: {0}). Libero: {1}.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min \u00b7 Libre: {2}.":
        "Ultimo: {0} \u00b7 Prossimo tra ~{1} min \u00b7 Libero: {2}.",
    "Ultimo: {0} \u00b7 Libre: {1}.":
        "Ultimo: {0} \u00b7 Libero: {1}.",
    "Backup": "Backup",
    "Configura primero una carpeta de destino.":
        "Configura prima una cartella di destinazione.",
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "Impossibile creare la cartella di destinazione:\n{0}\n\n{1}",
    "Espacio insuficiente en el destino. Necesario ~{0}, libre {1}.":
        "Spazio insufficiente nella destinazione. Necessario ~{0}, libero {1}.",
    "Selecciona primero una maquina virtual.":
        "Seleziona prima una macchina virtuale.",
    "Configura primero una carpeta de destino en esta "
    "seccion.":
        "Configura prima una cartella di destinazione in questa "
        "sezione.",
    "Backup con la VM encendida": "Backup con la VM accesa",
    "La VM esta encendida.\n\n"
    "Para evitar una copia inconsistente, apagala primero, o "
    "marca la opcion 'Tambien cuando la VM esta encendida' en "
    "esta seccion (asumiendo el riesgo).":
        "La VM e accesa.\n\n"
        "Per evitare una copia incoerente, spegnila prima, oppure "
        "seleziona l'opzione 'Anche quando la VM e accesa' in "
        "questa sezione (assumendoti il rischio).",

    # ================================================================
    # Intestazione scheda Backup
    # ================================================================
    "<b>Backups de la maquina virtual</b><br><span style='color:#666;font-size:11px;'>Copia periodica de la carpeta completa (discos + config + snapshots). El backup se guarda como carpeta independiente; se puede restaurar con el boton <b>Importar</b> de la pestana Resumen apuntando a la carpeta del backup.</span>":
        "<b>Backup della macchina virtuale</b><br><span style='color:#666;font-size:11px;'>Copia periodica dell'intera cartella (dischi + config + istantanee). Il backup viene salvato come cartella indipendente; puo essere ripristinato con il pulsante <b>Importa</b> nella scheda Panoramica puntando alla cartella del backup.</span>",
}
