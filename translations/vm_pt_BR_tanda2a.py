# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda2a - Traducciones al portugues (Brasil) - Tanda 2a.

Cubre: panel izquierdo (lista de VMs, busqueda, orden, filtro de
grupo, boton Nueva VM), controles de la VM (Iniciar/Pausar/Apagar/
Reiniciar/Forzar), toolbar del Resumen (Medios/Clonar/Desenlazar/
Importar/Exportar/Plantilla/Comando QEMU/Notas/Etiqueta/Comparar/
Eliminar) y titulo/estado del panel central.

Convenciones de traduccion:
  - "Snapshot" -> "Instantaneo" (coherente con el frances).
  - "Desenlazar" -> "Desvincular" (linked clone).
  - "Apagar" -> "Desligar" (shutdown).
  - "Reanudar" -> "Retomar".
"""

TRANSLATIONS = {

    # ================================================================
    # Panel izquierdo: cabecera, buscador, orden, filtro de grupo
    # ================================================================
    "<b>MÁQUINAS VIRTUALES</b>": "<b>MÁQUINAS VIRTUAIS</b>",
    "\U0001f50d Buscar máquinas...": "\U0001f50d Buscar máquinas...",
    "Ordenar: Nombre (A-Z)": "Ordenar: Nome (A-Z)",
    "Ordenar: Estado": "Ordenar: Estado",
    "Ordenar: Ultima vez usada": "Ordenar: Última vez usada",
    "Como ordenar la lista de maquinas virtuales.\n"
    "  - Nombre: alfabetico.\n"
    "  - Estado: encendidas primero, luego pausadas, apagadas al final.\n"
    "  - Ultima vez usada: por fecha de modificacion del vm_config.ini\n"
    "    (aproxima cuando se configuro por ultima vez).":
        "Como ordenar a lista de máquinas virtuais.\n"
        "  - Nome: alfabético.\n"
        "  - Estado: ligadas primeiro, depois pausadas, desligadas por último.\n"
        "  - Última vez usada: pela data de modificação do vm_config.ini\n"
        "    (aproxima quando foi configurada pela última vez).",
    "Todos los grupos": "Todos os grupos",
    "Muestra solo las VMs de un grupo concreto.\n"
    "  • Todos los grupos: sin filtro de grupo.\n"
    "  • Sin grupo: solo VMs sin etiqueta de grupo.\n"
    "  • <nombre>: solo VMs con ese grupo.\n"
    "\n"
    "Los grupos se asignan desde el botón '🏷 Etiqueta' del Resumen.":
        "Mostra apenas as VMs de um grupo específico.\n"
        "  • Todos os grupos: sem filtro de grupo.\n"
        "  • Sem grupo: apenas VMs sem rótulo de grupo.\n"
        "  • <nome>: apenas VMs com esse grupo.\n"
        "\n"
        "Os grupos são atribuídos pelo botão '🏷 Rótulo' do Resumo.",
    "\u2795 Nueva VM": "\u2795 Nova VM",
    "Selecciona una máquina virtual": "Selecione uma máquina virtual",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Selecione uma máquina virtual na lista à esquerda.",
    "● Sin VM seleccionada": "● Nenhuma VM selecionada",

    # ================================================================
    # Controles de la VM (Iniciar / Pausar / Apagar / Reiniciar)
    # ================================================================
    "▶ Iniciar": "▶ Iniciar",
    "⏸ Pausar": "⏸ Pausar",
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Guardar estado y pausar: escribe la RAM a disco antes de pausar.\n"
    "• Reanudar: vuelve a ejecutar la VM pausada.":
        "Pausar a VM. Use a seta para mais opções:\n"
        "• Pausar (rápido): para sem salvar o estado no disco.\n"
        "• Salvar estado e pausar: grava a RAM no disco antes de pausar.\n"
        "• Retomar: volta a executar a VM pausada.",
    "⏹ Apagar": "⏹ Desligar",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.":
        "Desligamento (ACPI): pede à VM que se desligue de forma ordenada.",
    "⏹ Apagado (ACPI)": "⏹ Desligamento (ACPI)",
    "Pide a la VM que se apague de forma ordenada, como pulsar el botón de\n"
    "encendido en un equipo real. El sistema operativo invitado decide cuándo\n"
    "y cómo cerrar. Puede tardar unos segundos o no responder si está colgado.":
        "Pede à VM que se desligue de forma ordenada, como apertar o botão de\n"
        "energia em um computador real. O sistema operacional convidado decide quando\n"
        "e como fechar. Pode demorar alguns segundos ou não responder se estiver travado.",
    "⏻ Forzar apagado": "⏻ Forçar desligamento",
    "Corta la VM de inmediato, sin avisar al sistema operativo invitado —\n"
    "como desenchufar un equipo real. Puede causar pérdida de datos no\n"
    "guardados; úsalo solo si la VM no responde al apagado normal.":
        "Corta a VM imediatamente, sem avisar o sistema operacional convidado —\n"
        "como desconectar um computador real da tomada. Pode causar perda de dados\n"
        "não salvos; use apenas se a VM não responder ao desligamento normal.",
    "⟳ Reiniciar": "⟳ Reiniciar",
    "Reinicia la VM (equivalente al botón de reinicio de un equipo real).\n"
    "No es un apagado ordenado del sistema operativo invitado: simplemente\n"
    "reinicia el hardware virtual.":
        "Reinicia a VM (equivalente ao botão de reset de um computador real).\n"
        "Não é um desligamento ordenado do sistema operacional convidado: apenas\n"
        "reinicia o hardware virtual.",
    "⟲ Forzar reinicio": "⟲ Forçar reinício",
    "Corta la VM por completo y la vuelve a iniciar desde cero, sin avisar\n"
    "al sistema operativo invitado. Úsalo solo si la VM no responde ni al\n"
    "apagado ni al reinicio normales.":
        "Corta a VM por completo e a reinicia do zero, sem avisar\n"
        "o sistema operacional convidado. Use apenas se a VM não responder\n"
        "nem ao desligamento nem ao reinício normais.",
    "⏸ Pausar (rápido)": "⏸ Pausar (rápido)",
    "Pausa la VM sin guardar el estado en disco. Es instantáneo, pero\n"
    "el estado (RAM y dispositivos) se pierde si el host se reinicia.":
        "Pausa a VM sem salvar o estado no disco. É instantâneo, mas\n"
        "o estado (RAM e dispositivos) é perdido se o host reiniciar.",
    "▶ Reanudar": "▶ Retomar",
    "Reanuda la ejecución de la VM pausada.":
        "Retoma a execução da VM pausada.",
    "Reanudar la VM pausada. Usa la flecha para más opciones:\n"
    "• Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "• Reanudar: vuelve a ejecutar la VM.\n"
    "• Tomar Snapshot: guarda el estado a disco y pausa.":
        "Retomar a VM pausada. Use a seta para mais opções:\n"
        "• Pausar (rápido): para sem salvar o estado no disco.\n"
        "• Retomar: volta a executar a VM.\n"
        "• Criar Instantâneo: salva o estado no disco e pausa.",
    "📸 Tomar Snapshot": "📸 Criar Instantâneo",
    "Guarda la RAM y el estado de los dispositivos a disco (como un\n"
    "snapshot) y luego pausa la VM. Tarda más pero sobrevive a reinicios.\n"
    "El snapshot aparecerá en la pestaña Snapshots y su captura de\n"
    "pantalla en el panel 'Último snapshot'.":
        "Salva a RAM e o estado dos dispositivos no disco (como um\n"
        "instantâneo) e depois pausa a VM. Demora mais, mas sobrevive a reinícios.\n"
        "O instantâneo aparecerá na aba Instantâneos e sua captura de\n"
        "tela no painel 'Último instantâneo'.",
    "Iniciar VM": "Iniciar VM",
    "Pausar/Reanudar VM": "Pausar/Retomar VM",
    "Apagado (ACPI): pide a la VM que se apague de forma ordenada.\n"
    "Usa la flecha para más opciones (forzar, reiniciar).":
        "Desligamento (ACPI): pede à VM que se desligue de forma ordenada.\n"
        "Use a seta para mais opções (forçar, reiniciar).",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Selecione uma VM para gerenciá-la. Use 'Nova máquina virtual' para criar outra.",
    "Nueva máquina virtual": "Nova máquina virtual",
    "● Nueva VM": "● Nova VM",

    # ================================================================
    # Toolbar del Resumen (botones de acciones sobre la VM)
    # ================================================================
    "\U0001f4bf Medios": "\U0001f4bf Mídias",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Cambia ISO en caliente, expulsa medios y conecta/desconecta\n"
    "USB sin reiniciar la máquina. Atajo: Ctrl+M.":
        "Mídias da VM: unidades CD/DVD e dispositivos USB.\n"
        "Troque ISO a quente, ejetar mídias e conectar/desconectar\n"
        "USB sem reiniciar a máquina. Atalho: Ctrl+M.",
    "\U0001f9ec Clonar": "\U0001f9ec Clonar",
    "Crea una copia completa de esta VM en una carpeta nueva.":
        "Cria uma cópia completa desta VM em uma nova pasta.",
    "\U0001f9ec Desenlazar": "\U0001f9ec Desvincular",
    "Convierte este clon enlazado en un QCOW2 autónomo.\n"
    "Después, el clon deja de depender del original y puede\n"
    "moverse o copiarse por separado.\n\n"
    "Solo aparece cuando la VM seleccionada es un clon\n"
    "enlazado y está apagada.":
        "Converte este clone vinculado em um QCOW2 autônomo.\n"
        "Depois disso, o clone deixa de depender do original e pode\n"
        "ser movido ou copiado separadamente.\n\n"
        "Só aparece quando a VM selecionada é um clone\n"
        "vinculado e está desligada.",
    "⇩ Importar": "⇩ Importar",
    "Importar una VM desde una carpeta (con vm_config.ini) o desde\n"
    "un archivo .tar.gz / .zip exportado previamente.":
        "Importar uma VM de uma pasta (com vm_config.ini) ou de\n"
        "um arquivo .tar.gz / .zip exportado anteriormente.",
    "⇪ Exportar": "⇪ Exportar",
    "Exportar esta VM como carpeta, .tar.gz o .zip portable.\n"
    "Se omiten los archivos de runtime (pids, sockets, logs).":
        "Exportar esta VM como pasta, .tar.gz ou .zip portátil.\n"
        "Os arquivos de runtime (pids, sockets, logs) são omitidos.",
    "\U0001f4be Plantilla": "\U0001f4be Modelo",
    "Guarda la configuración de hardware de esta VM como\n"
    "plantilla reutilizable. Se omiten discos, ISOs, MACs,\n"
    "carpetas compartidas, notas y reglas NAT.\n"
    "Aparecerá en el menú del botón '➕ Nueva VM'.":
        "Salva a configuração de hardware desta VM como\n"
        "modelo reutilizável. Discos, ISOs, MACs,\n"
        "pastas compartilhadas, notas e regras NAT são omitidos.\n"
        "Aparecerá no menu do botão '➕ Nova VM'.",
    "\U0001f4dc Comando QEMU": "\U0001f4dc Comando QEMU",
    "Muestra el contenido de run_temp.sh: el comando exacto con\n"
    "el que QEMU está ejecutando (o ejecutó por última vez) esta\n"
    "VM. Solo está disponible si la VM se ha arrancado alguna vez.":
        "Mostra o conteúdo de run_temp.sh: o comando exato com\n"
        "o qual o QEMU está executando (ou executou pela última vez) esta\n"
        "VM. Disponível apenas se a VM já foi iniciada alguma vez.",
    "\U0001f4dd Notas": "\U0001f4dd Notas",
    "Notas libres sobre esta VM. Se guardan en vm_config.ini\n"
    "(extra.notes) y aparecen como aviso amarillo debajo del\n"
    "estado en esta misma pestaña.":
        "Notas livres sobre esta VM. São salvas em vm_config.ini\n"
        "(extra.notes) e aparecem como aviso amarelo abaixo do\n"
        "estado nesta mesma aba.",
    "\U0001f3f7 Etiqueta": "\U0001f3f7 Rótulo",
    "Grupo y color de esta VM. El grupo agrupa VMs en la lista\n"
    "lateral; el color se aplica como fondo del ítem.":
        "Grupo e cor desta VM. O grupo agrupa VMs na lista\n"
        "lateral; a cor é aplicada como fundo do item.",
    "⚖ Comparar con defaults": "⚖ Comparar com padrões",
    "Compara la configuración actual de esta VM con los\n"
    "valores por defecto del perfil del SO. Permite aplicar\n"
    "los defaults a un campo o a todos; los cambios se aplican\n"
    "a los widgets y se persisten al Guardar.":
        "Compara a configuração atual desta VM com os\n"
        "valores padrão do perfil do SO. Permite aplicar\n"
        "os padrões a um campo ou a todos; as alterações são aplicadas\n"
        "aos widgets e persistidas ao Salvar.",
    "\U0001f5d1 Eliminar": "\U0001f5d1 Excluir",
    "Elimina esta VM (con opción de conservar los discos).":
        "Exclui esta VM (com opção de preservar os discos).",
    "\U0001f5d1\ufe0f Eliminar": "\U0001f5d1 Excluir",

    # ================================================================
    # Resumen: titulo y estado
    # ================================================================
    "Resumen de Configuración": "Resumo da Configuração",

    # ================================================================
    # Mensajes de control de VM (usados desde los slots de los botones)
    # ================================================================
    "Pausar": "Pausar",
    "La máquina virtual no está corriendo.": "A máquina virtual não está em execução.",
    "Control de VM": "Controle da VM",
    "No se pudo cambiar el estado de la VM.\n\n{0}":
        "Não foi possível alterar o estado da VM.\n\n{0}",
    "No se pudo pausar la VM.\n\n{0}":
        "Não foi possível pausar a VM.\n\n{0}",
    "Reanudar": "Retomar",
    "La máquina virtual ya está corriendo.": "A máquina virtual já está em execução.",
    "La máquina virtual no está pausada: no hay nada que reanudar.":
        "A máquina virtual não está pausada: não há nada para retomar.",
    "No se pudo reanudar la VM.\n\n{0}":
        "Não foi possível retomar a VM.\n\n{0}",
    "Apagar VM": "Desligar VM",
    "No se pudo enviar la orden de apagado.\n\n{0}":
        "Não foi possível enviar o comando de desligamento.\n\n{0}",
    "Reiniciar VM": "Reiniciar VM",
    "No se pudo enviar la orden de reinicio.\n\n{0}":
        "Não foi possível enviar o comando de reinício.\n\n{0}",
    "Forzar apagado": "Forçar desligamento",
    "Esto corta la VM de inmediato, sin avisar al sistema operativo invitado (como desenchufar un equipo real).\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "Isto corta a VM imediatamente, sem avisar o sistema operacional convidado (como desconectar um computador real da tomada).\n\nPode causar perda de dados não salvos dentro da VM.\n\nDeseja continuar?",
    "Forzar reinicio": "Forçar reinício",
    "Esto corta la VM de inmediato y la vuelve a iniciar desde cero, sin avisar al sistema operativo invitado.\n\nPuede causar pérdida de datos no guardados dentro de la VM.\n\n¿Deseas continuar?":
        "Isto corta a VM imediatamente e a reinicia do zero, sem avisar o sistema operacional convidado.\n\nPode causar perda de dados não salvos dentro da VM.\n\nDeseja continuar?",
    "¿Deseas continuar?": "Deseja continuar?",
}
