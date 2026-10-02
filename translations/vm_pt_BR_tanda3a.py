# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda3a - Traducciones al portugues (Brasil) - Tanda 3a.

Cubre la pestana Snapshots completa:
  - Cabecera + aviso de clon enlazado.
  - Botones Actualizar/Crear/Restaurar/Renombrar/Eliminar.
  - Tabla de discos + tabla de snapshots + vista Lista/Organigrama.
  - Preview con zoom.
  - snapshots_mixin.py: todos los dialogos y avisos.
  - snapshots_graph.py: nodos del organigrama.
"""

TRANSLATIONS = {

    # ================================================================
    # Cabecera de la pestana Snapshots
    # ================================================================
    "<b>Snapshots de la máquina virtual</b>":
        "<b>Snapshots da máquina virtual</b>",
    "Crea, restaura, elimina y administra snapshots. La aplicación comprueba los discos QCOW2 escribibles, el espacio libre y qué discos formarán parte del snapshot antes de ejecutarlo.":
        "Crie, restaure, exclua e gerencie snapshots. O aplicativo verifica os discos QCOW2 graváveis, o espaço livre e quais discos farão parte do snapshot antes de executá-lo.",
    "\u26a0 Esta VM es un clon enlazado (backing file QCOW2). Los snapshots completos (RAM + dispositivos) no se pueden restaurar en QEMU con backing file; la app usará siempre snapshots SOLO DE DISCOS. Para tener snapshots completos, desenlaza primero el clon con \u2018\U0001f9ec Desenlazar\u2019 en la pestaña Resumen.":
        "\u26a0 Esta VM é um clone vinculado (backing file QCOW2). Os snapshots completos (RAM + dispositivos) não podem ser restaurados no QEMU com backing file; o aplicativo sempre usará snapshots APENAS DE DISCOS. Para ter snapshots completos, desvincule primeiro o clone com \u2018\U0001f9ec Desvincular\u2019 na aba Resumo.",

    # ================================================================
    # Botones de la pestana
    # ================================================================
    "\U0001f504 Actualizar": "\U0001f504 Atualizar",
    "\u2795 Crear": "\u2795 Criar",
    "\u21a9 Restaurar": "\u21a9 Restaurar",
    "\u270f Cambiar nombre": "\u270f Renomear",
    "\U0001f5d1 Eliminar": "\U0001f5d1 Excluir",

    # ================================================================
    # Tabla de discos elegibles
    # ================================================================
    "Formato": "Formato",
    "Tamaño virtual": "Tamanho virtual",
    "Tamaño archivo": "Tamanho do arquivo",
    "Libre host": "Livre no host",
    "Escritura": "Gravação",
    "Snapshot": "Snapshot",
    "Sin operación de snapshot": "Nenhuma operação de snapshot em andamento",

    # ================================================================
    # Tabla de snapshots (columnas)
    # ================================================================
    "ID": "ID",
    "Tamaño VM": "Tamanho da VM",
    "Fecha": "Data",
    "Reloj VM": "Relógio da VM",

    # ================================================================
    # Vista Lista / Organigrama + preview zoom
    # ================================================================
    "Vista:": "Visualização:",
    "\U0001f4cb Lista": "\U0001f4cb Lista",
    "\U0001f333 Organigrama": "\U0001f333 Árvore",
    "Zoom:": "Zoom:",
    "Alejar la miniatura": "Reduzir a miniatura",
    "Acercar la miniatura": "Ampliar a miniatura",
    "\u21ba Ajustar": "\u21ba Ajustar",
    "Ajustar al tamaño original": "Ajustar ao tamanho original",
    "Sin captura de pantalla": "Sem captura de tela",

    # ================================================================
    # snapshots_graph.py (nodos del organigrama)
    # ================================================================
    "(sin miniatura)": "(sem miniatura)",
    "Restaurar este snapshot": "Restaurar este snapshot",
    "Renombrar": "Renomear",
    "\u270f Renombrar": "\u270f Renomear",
    "\u2795 Crear snapshot hijo": "\u2795 Criar snapshot filho",
    "\U0001f517 Establecer padre…": "\U0001f517 Definir pai…",
    "\u2b06 Mover a la raíz": "\u2b06 Mover para a raiz",

    # ================================================================
    # snapshots_mixin.py: dialogos de creacion
    # ================================================================
    "Selecciona una máquina virtual.": "Selecione uma máquina virtual.",
    "No se puede crear un snapshot completo.\n\n":
        "Não é possível criar um snapshot completo.\n\n",
    "Espacio disponible": "Espaço disponível",
    "{0}\n\n"
    "QEMU puede necesitar espacio adicional a medida que cambien los bloques. ¿Quieres continuar de todos modos?":
        "{0}\n\n"
        "O QEMU pode precisar de espaço adicional conforme os blocos mudam. Deseja continuar de qualquer forma?",
    "Crear snapshot": "Criar snapshot",
    "Nombre del snapshot:": "Nome do snapshot:",
    "Clon enlazado: snapshot solo de discos":
        "Clone vinculado: snapshot apenas de discos",
    "Esta VM es un clon enlazado (backing file QCOW2).\n\n"
    "QEMU no puede crear/restaurar snapshots completos\n"
    "(RAM + dispositivos) sobre un QCOW2 con backing\n"
    "file: al hacer loadvm QEMU aborta con una aserción\n"
    "interna (vmstate_load_next).\n\n"
    "Por seguridad se creará un snapshot SOLO DE DISCOS,\n"
    "que sí se puede restaurar con la VM apagada.\n\n"
    "Si necesitas un snapshot completo, desenlaza\n"
    "primero el clon (\U0001f9ec Desenlazar).":
        "Esta VM é um clone vinculado (backing file QCOW2).\n\n"
        "O QEMU não pode criar/restaurar snapshots completos\n"
        "(RAM + dispositivos) sobre um QCOW2 com backing\n"
        "file: ao executar loadvm, o QEMU aborta com uma asserção\n"
        "interna (vmstate_load_next).\n\n"
        "Por segurança, será criado um snapshot APENAS DE DISCOS,\n"
        "que pode ser restaurado com a VM desligada.\n\n"
        "Se você precisar de um snapshot completo, desvincule\n"
        "primeiro o clone (\U0001f9ec Desvincular).",
    "Snapshot con la VM encendida": "Snapshot com a VM ligada",
    "La VM está encendida.\n\n"
    "Un snapshot COMPLETO debe guardar la RAM y el estado de todos los dispositivos y "
    "puede dejar QEMU completamente ocupado durante ese proceso. En esta VM ya hemos "
    "observado que QEMU puede quedarse en STOP durante mucho tiempo.\n\n"
    "Sí = crear SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
    "No = crear SNAPSHOT SOLO DE DISCOS (rápido; no guarda RAM ni ventanas).\n"
    "Cancelar = no hacer nada.":
        "A VM está ligada.\n\n"
        "Um snapshot COMPLETO deve salvar a RAM e o estado de todos os dispositivos e "
        "pode deixar o QEMU completamente ocupado durante esse processo. Nesta VM já "
        "observamos que o QEMU pode ficar em STOP por muito tempo.\n\n"
        "Sim = criar SNAPSHOT COMPLETO (VM + RAM + dispositivos + discos).\n"
        "Não = criar SNAPSHOT APENAS DE DISCOS (rápido; não salva RAM nem janelas).\n"
        "Cancelar = não fazer nada.",
    "Snapshot de discos creado": "Snapshot de discos criado",
    "Se creó '{0}' en {1} QCOW2.\n\n"
    "Este snapshot no contiene la memoria RAM ni el estado de las ventanas. "
    "Para restaurarlo, la VM debe estar apagada.":
        "'{0}' foi criado em {1} QCOW2.\n\n"
        "Este snapshot não contém a memória RAM nem o estado das janelas. "
        "Para restaurá-lo, a VM deve estar desligada.",
    "Error al crear snapshot de discos": "Erro ao criar snapshot de discos",
    "Error al crear snapshot": "Erro ao criar snapshot",
    "No se pudo crear el snapshot completo.\n\n{0}":
        "Não foi possível criar o snapshot completo.\n\n{0}",
    "Ya hay una operación de snapshot en curso.":
        "Já há uma operação de snapshot em andamento.",
    "La operación se ejecuta en segundo plano; la interfaz sigue "
    "disponible mientras QEMU procesa el snapshot.":
        "A operação é executada em segundo plano; a interface permanece "
        "disponível enquanto o QEMU processa o snapshot.",
    "Snapshot — {0}": "Snapshot — {0}",
    "Estado '{0}' guardado y VM pausada.":
        "Estado '{0}' salvo e VM pausada.",
    "Snapshot '{0}' eliminado.": "Snapshot '{0}' excluído.",
    "Snapshot '{0}' restaurado.": "Snapshot '{0}' restaurado.",
    "Snapshot '{0}' creado.": "Snapshot '{0}' criado.",
    "El snapshot '{0}' fue creado y confirmado por QEMU.":
        "O snapshot '{0}' foi criado e confirmado pelo QEMU.",
    "VM pausada": "VM pausada",
    "Estado guardado como '{0}'.\n\nLa VM quedó pausada. "
    "Puedes reanudarla con el botón Pausar/Reanudar.":
        "Estado salvo como '{0}'.\n\nA VM ficou pausada. "
        "Você pode retomá-la com o botão Pausar/Retomar.",
    "Snapshot eliminado": "Snapshot excluído",
    "Se eliminó '{0}'.": "'{0}' foi excluído.",
    "Snapshot restaurado": "Snapshot restaurado",
    "Se restauró '{0}'.": "'{0}' foi restaurado.",
    "Snapshot creado": "Snapshot criado",
    "Error al eliminar snapshot": "Erro ao excluir snapshot",
    "Error al guardar estado": "Erro ao salvar estado",
    "Error al restaurar snapshot": "Erro ao restaurar snapshot",
    "CREACIÓN": "CRIAÇÃO",
    "ELIMINACIÓN": "EXCLUSÃO",
    "GUARDADO": "SALVAMENTO",
    "RESTAURACIÓN": "RESTAURAÇÃO",
    "No se pudo completar la operación de snapshot '{0}'.\n\n{1}":
        "Não foi possível completar a operação de snapshot '{0}'.\n\n{1}",

    # ================================================================
    # snapshots_mixin.py: restaurar
    # ================================================================
    "¿Restaurar '{0}'?\n\nLa VM volverá al estado del snapshot.":
        "Restaurar '{0}'?\n\nA VM voltará ao estado do snapshot.",
    "Snapshot solo de discos": "Snapshot apenas de discos",
    "El snapshot '{0}' es solo de discos (no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM primero.\n"
    "La VM volverá al estado del snapshot.\n\n"
    "¿Apagar la VM ahora y restaurar el snapshot?":
        "O snapshot '{0}' é apenas de discos (não contém RAM).\n\n"
        "Para restaurá-lo, é preciso desligar a VM primeiro.\n"
        "A VM voltará ao estado do snapshot.\n\n"
        "Desligar a VM agora e restaurar o snapshot?",
    "Apagar la VM": "Desligar a VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Não foi possível enviar o comando de desligamento.\n\n{0}",
    "Se restauró '{0}' mediante snapshot-load.":
        "'{0}' foi restaurado via snapshot-load.",
    "Restauración parcial": "Restauração parcial",
    "El snapshot se restauró en algunos discos, pero falló en otros:\n\n":
        "O snapshot foi restaurado em alguns discos, mas falhou em outros:\n\n",
    "Se restauró el snapshot de disco en los QCOW2 elegibles. "
    "Con la VM apagada no se restaura el estado de RAM/CPU.":
        "O snapshot de disco foi restaurado nos QCOW2 elegíveis. "
        "Com a VM desligada, o estado de RAM/CPU não é restaurado.",
    "El snapshot '{0}' es solo de discos "
    "(no contiene RAM).\n\n"
    "Para restaurarlo hay que apagar la VM y volver "
    "a intentarlo. QEMU no puede restaurar snapshots "
    "sin vmstate con la VM encendida.":
        "O snapshot '{0}' é apenas de discos "
        "(não contém RAM).\n\n"
        "Para restaurá-lo, é preciso desligar a VM e tentar "
        "novamente. O QEMU não pode restaurar snapshots "
        "sem vmstate com a VM ligada.",
    "La VM volvió a un estado operativo después de restaurar '{0}'.\n\n"
    "QEMU no confirmó el fin del job dentro del tiempo de espera, "
    "pero la restauración se aplicó.":
        "A VM voltou a um estado operacional após restaurar '{0}'.\n\n"
        "O QEMU não confirmou o fim do job dentro do tempo de espera, "
        "mas a restauração foi aplicada.",
    "No se pudo restaurar el snapshot.\n\n{0}":
        "Não foi possível restaurar o snapshot.\n\n{0}",
    "No se puede restaurar este snapshot": "Não é possível restaurar este snapshot",
    "Apagado no completado": "Desligamento não concluído",
    "La VM no se apagó dentro del tiempo máximo (90 s).\n\n"
    "Puede que el sistema invitado esté colgado. Usa el botón\n"
    "'Forzar apagado' de la lista lateral, luego vuelve a intentar\n"
    "restaurar el snapshot con la VM ya apagada.":
        "A VM não desligou dentro do tempo máximo (90 s).\n\n"
        "O sistema convidado pode estar travado. Use o botão\n"
        "'Forçar desligamento' da lista lateral e depois tente\n"
        "restaurar o snapshot com a VM já desligada.",

    # ================================================================
    # snapshots_mixin.py: eliminar
    # ================================================================
    "¿Eliminar '{0}'?": "Excluir '{0}'?",
    "Eliminar snapshot": "Excluir snapshot",
    "Eliminación parcial": "Exclusão parcial",
    "El snapshot se eliminó de algunos discos, pero falló en otros:\n\n":
        "O snapshot foi excluído de alguns discos, mas falhou em outros:\n\n",
    "No se pudo eliminar el snapshot.\n\n{0}":
        "Não foi possível excluir o snapshot.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: renombrar
    # ================================================================
    "Cambiar nombre": "Renomear",
    "Nuevo nombre para '{0}':": "Novo nome para '{0}':",
    "Cambiar nombre de snapshot": "Renomear snapshot",
    "QEMU no proporciona un renombrado interno directo. "
    "Esta acción creará un snapshot nuevo con el estado ACTUAL "
    "de la VM y eliminará el anterior.\n\n¿Continuar?":
        "O QEMU não fornece um renomeamento interno direto. "
        "Esta ação criará um novo snapshot com o estado ATUAL "
        "da VM e excluirá o anterior.\n\nContinuar?",
    "Cambio de nombre parcial": "Renomeamento parcial",
    "El nuevo snapshot se creó en algunos discos, pero hubo errores:\n\n":
        "O novo snapshot foi criado em alguns discos, mas houve erros:\n\n",
    "Error al cambiar nombre": "Erro ao renomear",
    "No se pudo cambiar el nombre.\n\n{0}":
        "Não foi possível alterar o nome.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: avisos VirtIO-GPU / clon enlazado
    # ================================================================
    "Snapshot con VirtIO-GPU": "Snapshot com VirtIO-GPU",
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
        "Esta VM está configurada com gráficos '{0}', que não permitem\n"
        "RESTAURAR snapshots completos no QEMU (RAM + dispositivos).\n"
        "\n"
        "O snapshot pode ser criado, mas ao tentar restaurá-lo o QEMU\n"
        "falhará com: 'Failed to load element of type virtio for virtio'.\n"
        "\n"
        "Opções:\n"
        "  • Usar snapshot APENAS DE DISCOS (escolher 'Não' no próximo\n"
        "    diálogo). Não salva RAM nem estado das janelas, mas\n"
        "    é restaurado sem problema com a VM desligada.\n"
        "  • Alterar Gráficos/GPU para 'Red Hat QXL 2D' ou 'VMware SVGA II',\n"
        "    reiniciar a VM e criar snapshots completos.\n"
        "\n"
        "Criar o snapshot mesmo assim?",
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
        "O QEMU não pode restaurar o snapshot por um problema conhecido "
        "com o dispositivo VirtIO-GPU.\n\n"
        "Detalhe técnico:\n"
        "  O VirtIO-GPU armazena um estado interno que não é serializável "
        "de forma confiável. O QEMU tenta reconstruí-lo ao restaurar e "
        "falha. Não é um bug do aplicativo, é uma limitação do motor.\n\n"
        "Como resolver:\n"
        "  1. Abra Configuração → Tela.\n"
        "  2. Altere 'Gráficos / GPU' de '{0}' para 'Red Hat QXL 2D'.\n"
        "  3. Reinicie a VM (desligue-a e inicie-a novamente).\n"
        "  4. Crie novos snapshots a partir desse momento: eles poderão "
        "ser restaurados sem problemas.\n\n"
        "Os snapshots antigos criados com virtio-gpu não podem ser "
        "recuperados (o QEMU não consegue reconstruir seu estado). Se "
        "você não precisar mais deles, exclua-os.",
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
    "'\U0001f9ec Desenlazar' (convierte el delta en un QCOW2 autónomo).":
        "A VM é um clone vinculado (backing file QCOW2) e o "
        "snapshot '{0}' foi criado no modo COMPLETO "
        "(RAM + dispositivos).\n\n"
        "O QEMU não pode restaurar snapshots completos sobre um QCOW2 "
        "com backing file: ao executar loadvm, ele aborta com uma asserção "
        "interna (vmstate_load_next) e o processo morre. Daí a "
        "'Conexão reinicializada' que você viu.\n\n"
        "O que fazer:\n"
        "  • Os snapshots que você criar A PARTIR DE AGORA neste clone "
        "serão apenas de discos (o aplicativo já força isso) e poderão "
        "ser restaurados.\n"
        "  • Este snapshot antigo não pode ser restaurado. Exclua-o "
        "se você não precisar mais dele.\n"
        "  • Se você precisar de snapshots completos, desvincule o clone com "
        "'\U0001f9ec Desvincular' (converte o delta em um QCOW2 autônomo).",

    # ================================================================
    # snapshots_mixin.py: capturas / preview
    # ================================================================
    "Sin capturas de snapshot": "Sem capturas de snapshot",
    "Los snapshots creados con la VM en ejecución guardan una "
    "captura de pantalla que se muestra aquí.":
        "Os snapshots criados com a VM em execução salvam uma "
        "captura de tela que é mostrada aqui.",
    "Captura no legible": "Captura ilegível",
    "Restaurar snapshot": "Restaurar snapshot",
    "No hay ningún snapshot reciente para restaurar.":
        "Não há nenhum snapshot recente para restaurar.",
    "Existe una captura para '{0}', pero ese snapshot ya no "
    "aparece en la lista de la VM (puede haber sido eliminado). "
    "Actualiza la pestaña Snapshots o elimínalo manualmente.":
        "Existe uma captura para '{0}', mas esse snapshot não "
        "aparece mais na lista da VM (pode ter sido excluído). "
        "Atualize a aba Snapshots ou exclua-a manualmente.",

    # ================================================================
    # snapshots_mixin.py: crear hijo / establecer padre
    # ================================================================
    "Organigrama": "Árvore",
    "No hay otros snapshots para elegir como padre.":
        "Não há outros snapshots para escolher como pai.",
    "Establecer padre": "Definir pai",
    "Padre para '{0}':": "Pai para '{0}':",
    "(ninguno — mover a la raíz)": "(nenhum — mover para a raiz)",
    "Nuevo snapshot hijo": "Novo snapshot filho",
    "Nombre del snapshot (hijo de '{0}'):":
        "Nome do snapshot (filho de '{0}'):",
    "No se pudo crear el snapshot.\n\n{0}":
        "Não foi possível criar o snapshot.\n\n{0}",

    # ================================================================
    # snapshots_mixin.py: solo-disco / preview info
    # ================================================================
    "(solo disco)": "(apenas disco)",
}
