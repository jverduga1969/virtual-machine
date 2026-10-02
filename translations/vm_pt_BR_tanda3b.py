# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda3b - Traducciones al portugues (Brasil) - Tanda 3b.

Cubre:
  - Snapshots automaticos programados (snapshot_schedule_mixin).
  - Backups automaticos programados (backup_schedule_mixin).
"""

TRANSLATIONS = {

    # ================================================================
    # Snapshots automaticos programados (snapshot_schedule_v1)
    # ================================================================
    "Snapshots automaticos programados": "Snapshots automáticos programados",
    "Activar": "Ativar",
    "Cuando esta activo, la app crea snapshots de disco automaticamente en esta VM segun la frecuencia elegida.\n\n"
    "Los snapshots programados son SOLO DE DISCOS (no guardan RAM ni ventanas). Se crean con prefijo 'auto_' y se eliminan por antiguedad al superar el limite de retencion.\n\n"
    "No se ejecutan si la VM esta apagada.":
        "Quando ativo, o aplicativo cria snapshots de disco automaticamente nesta VM conforme a frequência escolhida.\n\n"
        "Os snapshots programados são APENAS DE DISCOS (não salvam RAM nem janelas). São criados com o prefixo 'auto_' e removidos por antiguidade ao ultrapassar o limite de retenção.\n\n"
        "Não são executados se a VM estiver desligada.",
    "Cada hora": "A cada hora",
    "Cada 6 horas": "A cada 6 horas",
    "Cada 12 horas": "A cada 12 horas",
    "Diario": "Diário",
    "Semanal": "Semanal",
    "Frecuencia con la que se crea el snapshot automatico.\n"
    "El primer snapshot se crea pasada una frecuencia completa desde la activacion (o desde el ultimo, si ya habia uno).":
        "Frequência com que o snapshot automático é criado.\n"
        "O primeiro snapshot é criado após uma frequência completa desde a ativação (ou desde o último, se já havia um).",
    "Frecuencia:": "Frequência:",
    "Cuantos snapshots automaticos conservar. Al superar este numero se eliminan los mas antiguos (solo los que empiezan por 'auto_'; los manuales nunca se tocan).":
        "Quantos snapshots automáticos manter. Ao ultrapassar este número, os mais antigos são excluídos (apenas os que começam com 'auto_'; os manuais nunca são tocados).",
    "Conservar:": "Manter:",
    "Los snapshots programados son <b>solo de discos</b>: no guardan RAM ni estado de ventanas. No congelan la VM del usuario (el snapshot completo si puede hacerlo).":
        "Os snapshots programados são <b>apenas de discos</b>: não salvam RAM nem estado das janelas. Não congelam a VM do usuário (o snapshot completo pode fazer isso).",
    "Selecciona una VM para programar snapshots.":
        "Selecione uma VM para programar snapshots.",
    "Desactivado para esta VM.": "Desativado para esta VM.",
    "Sin snapshots programados todavia. Se creara el primero tras cumplirse la frecuencia elegida.":
        "Nenhum snapshot programado ainda. O primeiro será criado após decorrer a frequência escolhida.",
    "Pendiente (ultimo: {0}). Se ejecutara en el proximo chequeo del scheduler.":
        "Pendente (último: {0}). Será executado na próxima verificação do agendador.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min.":
        "Último: {0} \u00b7 Próximo em ~{1} min.",
    "Ultimo: {0}": "Último: {0}",

    # ================================================================
    # Backups automaticos programados (backup_schedule_v1)
    # ================================================================
    "Backups automaticos programados": "Backups automáticos programados",
    "Cuando esta activo, la app copia la carpeta completa de la VM "
    "(discos, configuracion, snapshots) al destino elegido segun "
    "la frecuencia. Los backups son carpetas independientes; "
    "puedes borrarlos manualmente o dejar que la retencion los "
    "limpie.":
        "Quando ativo, o aplicativo copia a pasta completa da VM "
        "(discos, configuração, snapshots) para o destino escolhido conforme "
        "a frequência. Os backups são pastas independentes; "
        "você pode excluí-los manualmente ou deixar que a retenção os "
        "limpe.",
    "Carpeta del host donde guardar los backups":
        "Pasta do host onde salvar os backups",
    "Elegir carpeta...": "Escolher pasta...",
    "Destino:": "Destino:",
    "Cuantos backups conservar en el destino. Tras cada backup "
    "exitoso se borran los mas antiguos por encima de este numero.":
        "Quantos backups manter no destino. Após cada backup "
        "bem-sucedido, os mais antigos acima deste número são excluídos.",
    "Tambien cuando la VM esta encendida": "Também quando a VM estiver ligada",
    "Desactivado (recomendado): los backups solo se ejecutan con "
    "la VM apagada.\n\n"
    "Activado: si la VM esta encendida, se copian los discos de "
    "todos modos; la copia puede quedar inconsistente porque QEMU "
    "esta escribiendo en el .qcow2 en ese momento. La restauracion "
    "podria requerir fsck o no arrancar. Solo si estas dispuesto a "
    "asumir ese riesgo.":
        "Desativado (recomendado): os backups só são executados com "
        "a VM desligada.\n\n"
        "Ativado: se a VM estiver ligada, os discos são copiados de "
        "qualquer forma; a cópia pode ficar inconsistente porque o QEMU "
        "está gravando no .qcow2 nesse momento. A restauração "
        "pode exigir fsck ou falhar ao iniciar. Apenas se você estiver "
        "disposto a assumir esse risco.",
    "Los backups son <b>carpetas</b> con todos los archivos de la "
    "VM (discos + configuraci\u00f3n + snapshots + capturas). No "
    "incluyen pids, sockets ni logs. Para restaurar, usa el bot\u00f3n "
    "<b>Importar</b> de la pesta\u00f1a Resumen con la carpeta del "
    "backup.":
        "Os backups são <b>pastas</b> com todos os arquivos da "
        "VM (discos + configuração + snapshots + capturas). Não "
        "incluem pids, sockets nem logs. Para restaurar, use o botão "
        "<b>Importar</b> da aba Resumo com a pasta do "
        "backup.",
    "Backup ahora": "Backup agora",
    "Ejecuta un backup inmediato con la configuracion actual, sin "
    "esperar a la proxima programacion.":
        "Executa um backup imediato com a configuração atual, sem "
        "aguardar a próxima programação.",
    "Elegir carpeta de destino para backups":
        "Escolher pasta de destino para backups",
    "Selecciona una VM para programar backups.":
        "Selecione uma VM para programar backups.",
    "Falta elegir una carpeta de destino.":
        "É preciso escolher uma pasta de destino.",
    "Sin backups todavia. Libre en destino: {0}. "
    "Se creara el primero tras cumplirse la frecuencia.":
        "Nenhum backup ainda. Livre no destino: {0}. "
        "O primeiro será criado após decorrer a frequência.",
    "Pendiente (ultimo: {0}). Libre: {1}.":
        "Pendente (último: {0}). Livre: {1}.",
    "Ultimo: {0} \u00b7 Proximo en ~{1} min \u00b7 Libre: {2}.":
        "Último: {0} \u00b7 Próximo em ~{1} min \u00b7 Livre: {2}.",
    "Ultimo: {0} \u00b7 Libre: {1}.":
        "Último: {0} \u00b7 Livre: {1}.",
    "Backup": "Backup",
    "Configura primero una carpeta de destino.":
        "Configure primeiro uma pasta de destino.",
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "Não foi possível criar a pasta de destino:\n{0}\n\n{1}",
    "Espacio insuficiente en el destino. Necesario ~{0}, libre {1}.":
        "Espaço insuficiente no destino. Necessário ~{0}, livre {1}.",
    "Selecciona primero una maquina virtual.":
        "Selecione primeiro uma máquina virtual.",
    "Configura primero una carpeta de destino en esta "
    "seccion.":
        "Configure primeiro uma pasta de destino nesta "
        "seção.",
    "Backup con la VM encendida": "Backup com a VM ligada",
    "La VM esta encendida.\n\n"
    "Para evitar una copia inconsistente, apagala primero, o "
    "marca la opcion 'Tambien cuando la VM esta encendida' en "
    "esta seccion (asumiendo el riesgo).":
        "A VM está ligada.\n\n"
        "Para evitar uma cópia inconsistente, desligue-a primeiro, ou "
        "marque a opção 'Também quando a VM estiver ligada' nesta "
        "seção (assumindo o risco).",

    # ================================================================
    # Encabezado de la pestana Backups
    # ================================================================
    "<b>Backups de la maquina virtual</b><br><span style='color:#666;font-size:11px;'>Copia periodica de la carpeta completa (discos + config + snapshots). El backup se guarda como carpeta independiente; se puede restaurar con el boton <b>Importar</b> de la pestana Resumen apuntando a la carpeta del backup.</span>":
        "<b>Backups da máquina virtual</b><br><span style='color:#666;font-size:11px;'>Cópia periódica da pasta completa (discos + config + snapshots). O backup é salvo como pasta independente; pode ser restaurado com o botão <b>Importar</b> da aba Resumo apontando para a pasta do backup.</span>",

    # ================================================================
    # Mensajes de error que pueden aparecer durante las tareas
    # ================================================================
    "No se pudo crear la carpeta destino:\n{0}\n\n{1}":
        "Não foi possível criar a pasta de destino:\n{0}\n\n{1}",
}
