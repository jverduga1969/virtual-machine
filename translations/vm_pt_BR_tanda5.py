# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda5 - Traducciones al portugues (Brasil) - Tanda 5.

Cubre las ultimas cadenas del proyecto:
  - suggestions_mixin.py
  - health_dashboard_mixin.py
  - compare_defaults_mixin.py
  - vm_templates_mixin.py
  - task_progress.py
  - vm_lifecycle_mixin: import/export VM + OVF/OVA, clone, unlink, delete,
    edit_vm_label, show_qemu_command, edit_vm_notes.
  - guest_integration_mixin.py
  - mac_recovery_mixin.py
  - install_flow_mixin.py
  - api_mixin.py (handlers)
"""

TRANSLATIONS = {

    # ================================================================
    # suggestions_mixin.py
    # ================================================================
    "Selecciona una VM para ver sugerencias.":
        "Selecione uma VM para ver sugestões.",
    "No se pudo leer la configuración: {0}":
        "Não foi possível ler a configuração: {0}",
    "Disco del host al {0}% — crítico. Quedan solo {1}. Amplía el disco o mueve archivos.":
        "Disco do host em {0}% — crítico. Restam apenas {1}. Amplie o disco ou mova arquivos.",
    "Disco del host al {0}%. Quedan {1}. Considera ampliarlo o limpiar.":
        "Disco do host em {0}%. Restam {1}. Considere ampliá-lo ou limpar.",
    "RAM de la VM ({0} GB) es el {1}% de la del host ({2} GB). Riesgo de swap.":
        "A RAM da VM ({0} GB) é {1}% da do host ({2} GB). Risco de swap.",
    "El último snapshot tiene {0} días ({1} en total). Puedes crear uno nuevo o limpiar los antiguos.":
        "O último snapshot tem {0} dias ({1} no total). Você pode criar um novo ou limpar os antigos.",
    "Hay {0} snapshots acumulados ocupando {1}. Considera eliminar los que ya no necesites.":
        "Há {0} snapshots acumulados ocupando {1}. Considere excluir os que você não precisa mais.",
    "Hay {0} carpeta(s) VirtioFS configuradas pero el Guest Agent está desactivado. Algunas funciones de automontaje no funcionarán.":
        "Há {0} pasta(s) VirtioFS configurada(s), mas o Guest Agent está desativado. Alguns recursos de automontagem não funcionarão.",
    "{0} carpeta(s) compartida(s) apuntan a rutas que ya no existen en el host: {1}":
        "{0} pasta(s) compartilhada(s) apontam para caminhos que não existem mais no host: {1}",
    "Hay {0} dispositivo(s) PCI en passthrough pero IOMMU no parece estar activo en el kernel. La VM puede no arrancar.":
        "Há {0} dispositivo(s) PCI em passthrough, mas o IOMMU não parece estar ativo no kernel. A VM pode não iniciar.",
    "Windows 11 requiere UEFI + Secure Boot. Cambia el firmware a UEFI.":
        "Windows 11 requer UEFI + Secure Boot. Altere o firmware para UEFI.",
    "macOS/OSX-KVM requiere UEFI (OVMF). Cambia el firmware a UEFI.":
        "macOS/OSX-KVM requer UEFI (OVMF). Altere o firmware para UEFI.",
    "El disco principal está en formato RAW. No admite snapshots internos ni crece dinámicamente. Considera convertir a QCOW2 si necesitas snapshots.":
        "O disco principal está no formato RAW. Não admite snapshots internos nem cresce dinamicamente. Considere converter para QCOW2 se precisar de snapshots.",
    "El log de la VM ({0} MB) es grande. Puedes exportarlo y borrarlo desde 'Ver log completo' → 'Exportar log'.":
        "O log da VM ({0} MB) é grande. Você pode exportá-lo e excluí-lo em 'Ver log completo' → 'Exportar log'.",
    "La configuración no se ha modificado en {0} días. ¿Sigue siendo útil esta VM?":
        "A configuração não é modificada há {0} dias. Esta VM ainda é útil?",
    "La VM tiene audio configurado pero el host no tiene /dev/snd ni PulseAudio/PipeWire (pactl). QEMU puede fallar al arrancar con audio.":
        "A VM tem áudio configurado, mas o host não tem /dev/snd nem PulseAudio/PipeWire (pactl). O QEMU pode falhar ao iniciar com áudio.",
    "Todo en orden. No hay sugerencias pendientes.":
        "Tudo em ordem. Não há sugestões pendentes.",
    "\U0001f4a1 Sugerencias": "\U0001f4a1 Sugestões",

    # ================================================================
    # health_dashboard_mixin.py
    # ================================================================
    "Salud de la máquina virtual": "Saúde da máquina virtual",
    "<b style='font-size:15px;'>\U0001f6a6 Semáforos de salud</b>":
        "<b style='font-size:15px;'>\U0001f6a6 Semáforos de saúde</b>",
    "Cada fila muestra el estado de un subsistema de la VM. "
    "Verde: funciona · Amarillo: parcial o sin confirmar · "
    "Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s.":
        "Cada linha mostra o estado de um subsistema da VM. "
        "Verde: funciona · Amarelo: parcial ou não confirmado · "
        "Vermelho: indisponível · Cinza: não se aplica. Atualiza a cada 4 s.",
    "\U0001f310 Red de la VM": "\U0001f310 Rede da VM",
    "\U0001f5a5\ufe0f Internet del host": "\U0001f5a5\ufe0f Internet do host",
    "\U0001f50a Audio": "\U0001f50a Áudio",
    "\U0001f5bc\ufe0f Pantalla": "\U0001f5bc\ufe0f Tela",
    "\U0001f50c Guest Agent": "\U0001f50c Guest Agent",
    "\U0001f504 Refrescar ahora": "\U0001f504 Atualizar agora",
    "Sin VM seleccionada.": "Nenhuma VM selecionada.",
    "Host con salida a Internet (Apple y Cloudflare responden).":
        "Host com saída para Internet (Apple e Cloudflare respondem).",
    "Salida parcial: uno de los dos destinos no respondió.":
        "Saída parcial: um dos dois destinos não respondeu.",
    "El host no tiene salida a Internet.":
        "O host não tem saída para Internet.",
    "No hay script de arranque todavía.": "Ainda não há script de inicialização.",
    "No se pudo leer el script de arranque.":
        "Não foi possível ler o script de inicialização.",
    "No hay adaptador de red configurado en esta VM.":
        "Não há adaptador de rede configurado nesta VM.",
    "NIC {0}: tráfico activo "
    "({1:.1f} KB/s; "
    "rx {2:.1f} MB, "
    "tx {3:.1f} MB).":
        "NIC {0}: tráfego ativo "
        "({1:.1f} KB/s; "
        "rx {2:.1f} MB, "
        "tx {3:.1f} MB).",
    "NIC {0} con contadores activos pero "
    "sin tráfico en el último intervalo "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB).":
        "NIC {0} com contadores ativos, mas "
        "sem tráfego no último intervalo "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB).",
    "NIC {0}: contadores iniciales leídos "
    "(rx {1:.1f} MB, "
    "tx {2:.1f} MB); "
    "esperando siguiente lectura para medir velocidad.":
        "NIC {0}: contadores iniciais lidos "
        "(rx {1:.1f} MB, "
        "tx {2:.1f} MB); "
        "aguardando a próxima leitura para medir a velocidade.",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host; esperando segunda lectura "
    "para medir cambio.":
        "NIC {0} configurada. {1} conexões TCP "
        "ativas no host; aguardando a segunda leitura "
        "para medir a variação.",
    "NIC {0}: actividad detectada "
    "({1} \u2192 {2} conexiones TCP ESTAB).":
        "NIC {0}: atividade detectada "
        "({1} \u2192 {2} conexões TCP ESTAB).",
    "NIC {0} configurada. {1} conexiones TCP "
    "activas en el host, sin cambios en el último "
    "intervalo (la VM puede estar idle).":
        "NIC {0} configurada. {1} conexões TCP "
        "ativas no host, sem alterações no último "
        "intervalo (a VM pode estar ociosa).",
    "NIC {0} configurada; sin conexiones externas "
    "activas en el host.":
        "NIC {0} configurada; sem conexões externas "
        "ativas no host.",
    "NIC {0} configurada. No se pudo medir tráfico (QMP no "
    "expone query-netdev y ss no está disponible).":
        "NIC {0} configurada. Não foi possível medir o tráfego (o QMP não "
        "expõe query-netdev e o ss não está disponível).",
    "Sin audio configurado en esta VM.": "Sem áudio configurado nesta VM.",
    "Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.":
        "Audiodev configurado. pactl indisponível; não é possível confirmar a reprodução.",
    "Audiodev configurado, pero no hay PID de QEMU para verificar el sink.":
        "Audiodev configurado, mas não há PID do QEMU para verificar o sink.",
    "No se pudo consultar pactl: {0}":
        "Não foi possível consultar o pactl: {0}",
    "pactl no respondió.": "pactl não respondeu.",
    "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo.":
        "Sink ativo: o pactl vê o QEMU (PID {0}) reproduzindo.",
    "Audiodev configurado; QEMU no está reproduciendo ahora. "
    "Es normal si el guest no está emitiendo sonido.":
        "Audiodev configurado; o QEMU não está reproduzindo agora. "
        "É normal se o guest não estiver emitindo som.",
    "Framebuffer VNC {0}\u00d7{1}.": "Framebuffer VNC {0}\u00d7{1}.",
    "Widget VNC conectado, esperando primer frame.":
        "Widget VNC conectado, aguardando o primeiro frame.",
    "Consola SPICE embebida activa.": "Console SPICE embutido ativo.",
    "Visor externo activo (PID {0}).": "Visualizador externo ativo (PID {0}).",
    "Modo remoto (socket VNC/SPICE) sin widget embebido ni "
    "visor activo. Abre la Consola Gráfica para ver la pantalla.":
        "Modo remoto (socket VNC/SPICE) sem widget embutido nem "
        "visualizador ativo. Abra o Console Gráfico para ver a tela.",
    "Modo headless (sin salida de pantalla).":
        "Modo headless (sem saída de vídeo).",
    "Ventana nativa de QEMU activa.": "Janela nativa do QEMU ativa.",
    "Configuración de pantalla detectada en el script de arranque.":
        "Configuração de tela detectada no script de inicialização.",
    "Guest Agent no habilitado para esta VM "
    "(actívalo en Integración Host \u2194 Guest).":
        "Guest Agent não habilitado para esta VM "
        "(ative-o em Integração Host \u2194 Guest).",
    "QEMU Guest Agent responde.": "QEMU Guest Agent responde.",
    "Canal QGA presente, pero el guest no responde.":
        "Canal QGA presente, mas o guest não responde.",
    "Canal QGA presente, sin respuesta: {0}":
        "Canal QGA presente, sem resposta: {0}",

    # ================================================================
    # compare_defaults_mixin.py
    # ================================================================
    "Comparar con defaults": "Comparar com padrões",
    "Selecciona primero una máquina virtual.":
        "Selecione uma máquina virtual primeiro.",
    "No se pudo determinar el perfil del SO seleccionado.":
        "Não foi possível determinar o perfil do SO selecionado.",
    "Firmware": "Firmware",
    "Chipset": "Chipset",
    "CPU (modelo)": "CPU (modelo)",
    "Núcleos": "Núcleos",
    "Gráficos": "Gráficos",
    "VRAM": "VRAM",
    "Audio": "Áudio",
    "Señalización (ratón/teclado)": "Apontamento (mouse/teclado)",
    "Consola: protocolo": "Console: protocolo",
    "Consola: modo": "Console: modo",
    "Comparación de <b>{0}</b> con los valores por defecto del perfil del SO seleccionado. Las filas con fondo amarillo difieren del default.<br><br>Aplicar un default <b>no</b> guarda la VM: solo cambia el widget. Persiste con <b>Guardar</b> (en Configuración) o al iniciar la VM.":
        "Comparação de <b>{0}</b> com os valores padrão do perfil do SO selecionado. As linhas com fundo amarelo diferem do padrão.<br><br>Aplicar um padrão <b>não</b> salva a VM: apenas altera o widget. Persiste com <b>Salvar</b> (em Configuração) ou ao iniciar a VM.",
    "Campo": "Campo",
    "Actual": "Atual",
    "Por defecto": "Padrão",
    "<b>{0}</b> diferencia(s) de <b>{1}</b> campo(s).":
        "<b>{0}</b> diferença(s) em <b>{1}</b> campo(s).",
    "Aplicar al campo seleccionado": "Aplicar ao campo selecionado",
    "Aplicar todos los defaults": "Aplicar todos os padrões",
    "Aplicar": "Aplicar",
    "Selecciona primero una fila.": "Selecione uma linha primeiro.",
    "==> Comparar defaults: aplicados {0} campo(s) a '{1}'.":
        "==> Comparar padrões: {0} campo(s) aplicado(s) a '{1}'.",

    # ================================================================
    # vm_templates_mixin.py
    # ================================================================
    "Guardar como plantilla": "Salvar como modelo",
    "Esta VM no tiene vm_config.ini todavía.\n\nConfigúrala y guárdala primero.":
        "Esta VM ainda não tem vm_config.ini.\n\nConfigure-a e salve-a primeiro.",
    "Ya existe la plantilla '{0}'.\n\n¿Sobrescribirla?":
        "O modelo '{0}' já existe.\n\nSobrescrever?",
    "No se pudo escribir la plantilla.\n\n{0}":
        "Não foi possível gravar o modelo.\n\n{0}",
    "Plantilla guardada": "Modelo salvo",
    "Plantilla '{0}' creada correctamente.\n\nAparecerá en el menú del botón '➕ Nueva VM'.":
        "Modelo '{0}' criado corretamente.\n\nAparecerá no menu do botão '➕ Nova VM'.",
    "\U0001f195 Nueva VM en blanco": "\U0001f195 Nova VM em branco",
    "Desde plantilla:": "A partir de modelo:",
    "Crear desde plantilla": "Criar a partir de modelo",
    "No encuentro la plantilla '{0}'.": "Modelo '{0}' não encontrado.",
    "Ya existe una carpeta para '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Já existe uma pasta para '{0}'.\n\nSubstituir? (a existente será excluída)",
    "No se pudo eliminar la carpeta existente.\n\n{0}":
        "Não foi possível excluir a pasta existente.\n\n{0}",
    "No se pudo crear la VM.\n\n{0}": "Não foi possível criar a VM.\n\n{0}",
    "VM creada": "VM criada",
    "VM '{0}' creada desde la plantilla '{1}'.\n\nSe ha abierto en Configuración → Almacenamiento para que\nañadas el disco y el medio de instalación. La MAC de red se\nha regenerado para evitar conflictos con otras VMs.":
        "VM '{0}' criada a partir do modelo '{1}'.\n\nFoi aberta em Configuração → Armazenamento para que\nvocê adicione o disco e a mídia de instalação. O MAC de rede foi\nregenerado para evitar conflitos com outras VMs.",

    # ================================================================
    # task_progress.py
    # ================================================================
    "Iniciando…": "Iniciando…",
    "Cancelar": "Cancelar",
    "La tarea falló.": "A tarefa falhou.",
    "Cancelando, esperando al trabajador…":
        "Cancelando, aguardando o trabalhador…",
    "Cancelando…": "Cancelando…",

    # ================================================================
    # vm_lifecycle_mixin: edit_vm_label
    # ================================================================
    "Etiqueta de la VM": "Rótulo da VM",
    "Etiqueta - {0}": "Rótulo - {0}",
    "Grupo y color para <b>{0}</b>. El grupo es texto libre: escribe uno nuevo para crearlo. El color se aplica como fondo suave del ítem en la lista lateral.":
        "Grupo e cor para <b>{0}</b>. O grupo é texto livre: digite um novo para criá-lo. A cor é aplicada como fundo suave do item na lista lateral.",
    "(sin grupo)": "(sem grupo)",
    "Grupo:": "Grupo:",
    "Sin color": "Sem cor",
    "Quitar etiqueta": "Remover rótulo",
    "Guardar": "Salvar",
    "Etiqueta": "Rótulo",
    "No se pudo guardar la etiqueta.\n\n{0}":
        "Não foi possível salvar o rótulo.\n\n{0}",

    # ================================================================
    # vm_lifecycle_mixin: show_qemu_command
    # ================================================================
    "Comando QEMU": "Comando QEMU",
    "La VM '{0}' todavia no se ha arrancado.\n\nEl comando QEMU se genera al pulsar Iniciar; vuelve a intentarlo despues del primer arranque.":
        "A VM '{0}' ainda não foi iniciada.\n\nO comando QEMU é gerado ao clicar em Iniciar; tente novamente após a primeira inicialização.",
    "No se pudo leer run_temp.sh.\n\n{0}":
        "Não foi possível ler run_temp.sh.\n\n{0}",
    "Comando QEMU - {0}": "Comando QEMU - {0}",
    "Contenido de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este es el comando exacto con el que QEMU esta ejecutando (o ejecuto por ultima vez) la VM.":
        "Conteúdo de <code>run_temp.sh</code> para <b>{0}</b>.<br>Este é o comando exato com o qual o QEMU está executando (ou executou pela última vez) a VM.",
    "Copiar al portapapeles": "Copiar para a área de transferência",
    "Abrir carpeta de la VM": "Abrir pasta da VM",
    "Abre la carpeta que contiene run_temp.sh, launch.log y los discos.":
        "Abre a pasta que contém run_temp.sh, launch.log e os discos.",

    # ================================================================
    # vm_lifecycle_mixin: edit_vm_notes
    # ================================================================
    "Notas de la VM": "Notas da VM",
    "Notas - {0}": "Notas - {0}",
    "Notas libres sobre <b>{0}</b>. Se guardan en <code>vm_config.ini</code> como <code>extra.notes</code> y aparecen como aviso amarillo en la pestana Resumen.":
        "Notas livres sobre <b>{0}</b>. São salvas em <code>vm_config.ini</code> como <code>extra.notes</code> e aparecem como aviso amarelo na aba Resumo.",
    "Ej.: instalado con VirtIO, probar snapshots tras actualizar los drivers; puerto 8080 redirigido al 80 del guest...":
        "Ex.: instalado com VirtIO, testar snapshots após atualizar os drivers; porta 8080 redirecionada para a 80 do guest...",
    "Borrar notas": "Apagar notas",
    "Notas": "Notas",
    "No se pudieron guardar las notas.\n\n{0}":
        "Não foi possível salvar as notas.\n\n{0}",

    # ================================================================
    # vm_lifecycle_mixin: _set_vm_status / open_vm_folder / summary
    # ================================================================
    "● Nueva VM": "● Nova VM",
    "● Configurada": "● Configurada",
    "● Ejecutándose": "● Em execução",
    "● Error": "● Erro",
    "Carpeta": "Pasta",
    "Primero selecciona una máquina virtual existente.":
        "Selecione primeiro uma máquina virtual existente.",
    "Carpeta de la VM": "Pasta da VM",
    "No se pudo abrir la carpeta.\n\n{0}\n\n{1}":
        "Não foi possível abrir a pasta.\n\n{0}\n\n{1}",
    "Resumen": "Resumo",
    "No hay una máquina virtual seleccionada todavía.":
        "Nenhuma máquina virtual selecionada ainda.",
    "Resumen de la máquina virtual": "Resumo da máquina virtual",

    # ================================================================
    # vm_lifecycle_mixin: import_vm + OVF import
    # ================================================================
    "Importar VM": "Importar VM",
    "¿Cómo quieres importar la máquina virtual?\n\n  • Desde carpeta: selecciona una carpeta que contenga vm_config.ini.\n  • Desde archivo: selecciona un .ova o .ovf (formato estándar OVF, portable a VirtualBox/VMware), o un .tar.gz / .tar / .zip exportado previamente desde otra instalación de Virtual.Machine.":
        "Como você quer importar a máquina virtual?\n\n  • De pasta: selecione uma pasta que contenha vm_config.ini.\n  • De arquivo: selecione um .ova ou .ovf (formato padrão OVF, portátil para VirtualBox/VMware), ou um .tar.gz / .tar / .zip exportado anteriormente de outra instalação do Virtual.Machine.",
    "\U0001f4c1 Desde carpeta…": "\U0001f4c1 De pasta…",
    "\U0001f5dc\ufe0f Desde archivo…": "\U0001f5dc\ufe0f De arquivo…",
    "Selecciona la carpeta de la VM a importar":
        "Selecione a pasta da VM a importar",
    "Selecciona el archivo a importar": "Selecione o arquivo a importar",
    "OVF/OVA (*.ova *.ovf);;Archivos de VM empaquetados (*.tar.gz *.tgz *.tar *.zip);;Todos los archivos (*)":
        "OVF/OVA (*.ova *.ovf);;Arquivos de VM empacotados (*.tar.gz *.tgz *.tar *.zip);;Todos os arquivos (*)",
    "Formato de archivo no reconocido. Usa .tar.gz, .tgz, .tar, .zip, .ova o .ovf.":
        "Formato de arquivo não reconhecido. Use .tar.gz, .tgz, .tar, .zip, .ova ou .ovf.",
    "La carpeta seleccionada no contiene vm_config.ini:\n\n{0}\n\nAsegúrate de elegir la carpeta raíz de la VM, no una subcarpeta.":
        "A pasta selecionada não contém vm_config.ini:\n\n{0}\n\nCertifique-se de escolher a pasta raiz da VM, não uma subpasta.",
    "Nombre para la VM importada:\n\n(se importará desde {0})":
        "Nome para a VM importada:\n\n(será importada de {0})",
    "Nombre inválido.": "Nome inválido.",
    "Ya existe una VM llamada '{0}'.\n\n¿Reemplazarla? (se eliminará la existente)":
        "Já existe uma VM chamada '{0}'.\n\nSubstituí-la? (a existente será excluída)",
    "Copiando/desempaquetando en el sistema de archivos del destino (no en /tmp)…":
        "Copiando/desempacotando no sistema de arquivos do destino (não em /tmp)…",
    "Desempaquetando archivo…": "Desempacotando arquivo…",
    "Extrayendo {0}/{1}…": "Extraindo {0}/{1}…",
    "El archivo no contiene ninguna VM válida (no se encontró vm_config.ini).":
        "O arquivo não contém nenhuma VM válida (vm_config.ini não foi encontrado).",
    "Importación completada.": "Importação concluída.",
    "Copiando {0}": "Copiando {0}",
    "VM '{0}' importada correctamente.\n\nRevisa su configuración en la pestaña Configuración antes de arrancarla, especialmente si la importaste desde otro host: puede referenciar rutas que no existan aquí (carpetas compartidas, ISOs externas, dispositivos de passthrough).":
        "VM '{0}' importada corretamente.\n\nRevise sua configuração na aba Configuração antes de iniciá-la, especialmente se você a importou de outro host: ela pode referenciar caminhos que não existem aqui (pastas compartilhadas, ISOs externas, dispositivos de passthrough).",

    # ================================================================
    # vm_lifecycle_mixin: export_vm + OVF export
    # ================================================================
    "Exportar VM": "Exportar VM",
    "Primero selecciona una máquina virtual.":
        "Selecione primeiro uma máquina virtual.",
    "La VM '{0}' está {1}.\n\nSe recomienda apagarla antes de exportar: si está corriendo, los discos pueden estar en un estado inconsistente (cambios sin sincronizar a disco, locks activos…).\n\n¿Continuar de todos modos?":
        "A VM '{0}' está {1}.\n\nRecomenda-se desligá-la antes de exportar: se estiver em execução, os discos podem estar em um estado inconsistente (alterações não sincronizadas com o disco, locks ativos…).\n\nContinuar de qualquer forma?",
    "Copia de carpeta (más rápido, editable)":
        "Cópia de pasta (mais rápido, editável)",
    "Archivo .tar.gz (comprimido, portable)":
        "Arquivo .tar.gz (compactado, portátil)",
    "Archivo .zip (compatible con Windows)":
        "Arquivo .zip (compatível com Windows)",
    "Archivo .ova (Open Virtual Appliance, portable a VirtualBox/VMware)":
        "Arquivo .ova (Open Virtual Appliance, portátil para VirtualBox/VMware)",
    "Descriptor .ovf + discos sueltos (carpeta)":
        "Descritor .ovf + discos avulsos (pasta)",
    "Formato para exportar '{0}':": "Formato para exportar '{0}':",
    "Elige la carpeta donde crear la copia":
        "Escolha a pasta onde criar a cópia",
    "En la carpeta destino ya existe '{0}'.\n\n¿Sobrescribir? (se borrará la carpeta destino existente)":
        "A pasta de destino já contém '{0}'.\n\nSobrescrever? (a pasta de destino existente será excluída)",
    "Guardar archivo de exportación": "Salvar arquivo de exportação",
    "Archivo tar.gz (*.tar.gz);;Archivo zip (*.zip)":
        "Arquivo tar.gz (*.tar.gz);;Arquivo zip (*.zip)",
    "Archivo zip (*.zip);;Archivo tar.gz (*.tar.gz)":
        "Arquivo zip (*.zip);;Arquivo tar.gz (*.tar.gz)",
    "El archivo destino ya existe:\n{0}\n\n¿Sobrescribir?":
        "O arquivo de destino já existe:\n{0}\n\nSobrescrever?",
    "Confirmar exportación": "Confirmar exportação",
    "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Contenido: {2} archivo(s), {3}\n  • Destino: {4}\n\nLos archivos de bloqueo (pids, sockets) y logs se omitirán.":
        "Exportar '{0}' como:\n\n  • Formato: {1}\n  • Conteúdo: {2} arquivo(s), {3}\n  • Destino: {4}\n\nOs arquivos de bloqueio (pids, sockets) e logs serão omitidos.",
    "No se pudo completar la exportación.\n\n{0}":
        "Não foi possível concluir a exportação.\n\n{0}",
    "{0} archivo(s), {1} en total": "{0} arquivo(s), {1} no total",
    "Exportación cancelada por el usuario.":
        "Exportação cancelada pelo usuário.",
    "Formato de exportación desconocido: {0}":
        "Formato de exportação desconhecido: {0}",
    "Exportación completada ({0} archivo(s)).":
        "Exportação concluída ({0} arquivo(s)).",
    "'{0}' exportada correctamente.\n\nDestino: {1}":
        "'{0}' exportada corretamente.\n\nDestino: {1}",

    # ================================================================
    # vm_lifecycle_mixin: OVF/OVA raises y mensajes
    # ================================================================
    "VM macOS: no se encuentra mac_hdd_ng.qcow2 en la carpeta de la VM ({0}). Sin este archivo la VM no tiene sistema operativo que exportar.":
        "VM macOS: mac_hdd_ng.qcow2 não encontrado na pasta da VM ({0}). Sem este arquivo a VM não tem sistema operacional a exportar.",
    "La VM no tiene discos adjuntos que exportar. Añade al menos un disco en Configuración → Almacenamiento.":
        "A VM não tem discos anexados para exportar. Adicione pelo menos um disco em Configuração → Armazenamento.",
    "qemu-img convert -c falló para '{0}': {1}":
        "qemu-img convert -c falhou para '{0}': {1}",
    "El aplanado+compresión de '{0}' no produjo un archivo válido.":
        "O achatamento+compressão de '{0}' não produziu um arquivo válido.",
    "Importar OVA": "Importar OVA",
    "El archivo .ova no contiene ningún descriptor .ovf.":
        "O arquivo .ova não contém nenhum descritor .ovf.",
    "Importar OVF": "Importar OVF",
    "El archivo .ovf está vacío.": "O arquivo .ovf está vazio.",
    "No se pudo leer el descriptor.\n\n{0}":
        "Não foi possível ler o descritor.\n\n{0}",
    "El descriptor OVF no se pudo interpretar.\n\n{0}":
        "O descritor OVF não pôde ser interpretado.\n\n{0}",
    "No se pudo completar la importación.\n\n{0}":
        "Não foi possível concluir a importação.\n\n{0}",
    "Extrayendo y preparando el OVF/OVA...":
        "Extraindo e preparando o OVF/OVA...",
    "Importar OVF/OVA": "Importar OVF/OVA",

    # ================================================================
    # vm_lifecycle_mixin: clone / unlink
    # ================================================================
    "Clonar máquina virtual": "Clonar máquina virtual",
    "Nombre para el clon de '{0}':": "Nome para o clone de '{0}':",
    "Debes escribir un nombre para el clon.":
        "Você precisa digitar um nome para o clone.",
    "Nombre ya existente": "Nome já existente",
    "La máquina virtual '{0}' ya existe en el listado.\n\nElige otro nombre para el clon.":
        "A máquina virtual '{0}' já existe na lista.\n\nEscolha outro nome para o clone.",
    "Ese nombre no puede utilizarse para una máquina virtual.":
        "Esse nome não pode ser usado para uma máquina virtual.",
    "Clonar VM": "Clonar VM",
    "¿Qué tipo de clon quieres crear a partir de <b>{0}</b>?<br><br><b>Clon completo</b><br>Copia íntegra de todos los discos. Totalmente independiente del original; ocupa el mismo espacio que la VM original.<br><br><b>Clon enlazado</b><br>El disco base se comparte mediante un <i>backing file</i> QCOW2. La nueva VM solo guarda los cambios, así que ocupa muy poco. <b>Depende del original</b>: si se borra o se mueve el original, el clon se rompe.<br>El backing se guarda con <b>ruta relativa</b> para que puedas mover o copiar la carpeta <code>VirtualMachines/</code> entera a otro host sin romper nada.<br><br><b>Importante:</b> una vez que el clon arranque por primera vez, los cambios que hagas DESPUÉS en el original <b>NO se verán</b> en el clon: la vista de su sistema de archivos queda anclada al estado del primer arranque (los bloques que el clon ya escribió no vuelven a consultarse en el backing). Trata el original como de solo lectura mientras el clon exista, o desenlaza el clon con <b>🧬 Desenlazar</b> para independizarlo.":
        "Que tipo de clone você quer criar a partir de <b>{0}</b>?<br><br><b>Clone completo</b><br>Cópia integral de todos os discos. Totalmente independente do original; ocupa o mesmo espaço que a VM original.<br><br><b>Clone vinculado</b><br>O disco base é compartilhado por meio de um <i>backing file</i> QCOW2. A nova VM só guarda as alterações, então ocupa muito pouco. <b>Depende do original</b>: se o original for excluído ou movido, o clone quebra.<br>O backing é salvo com <b>caminho relativo</b> para que você possa mover ou copiar a pasta <code>VirtualMachines/</code> inteira para outro host sem quebrar nada.<br><br><b>Importante:</b> uma vez que o clone inicializar pela primeira vez, as alterações que você fizer DEPOIS no original <b>NÃO serão vistas</b> no clone: a visão do sistema de arquivos fica ancorada ao estado da primeira inicialização (os blocos que o clone já gravou não são mais consultados no backing). Trate o original como somente leitura enquanto o clone existir, ou desvincule o clone com <b>🧬 Desvincular</b> para torná-lo independente.",
    "Clon completo": "Clone completo",
    "Clon enlazado": "Clone vinculado",
    "No se pudo copiar la carpeta de la VM.\n\n{0}":
        "Não foi possível copiar a pasta da VM.\n\n{0}",
    "La VM se copió pero no se pudo reescribir su vm_config.ini.\n\n{0}":
        "A VM foi copiada, mas seu vm_config.ini não pôde ser reescrito.\n\n{0}",
    "Clon creado": "Clone criado",
    "La máquina virtual '{0}' fue clonada correctamente (clon completo).\n\nSe han regenerado las direcciones MAC y los IDs internos de los discos para que no choquen con la VM original.":
        "A máquina virtual '{0}' foi clonada corretamente (clone completo).\n\nOs endereços MAC e os IDs internos dos discos foram regenerados para não conflitar com a VM original.",
    "Clon enlazado con original en ejecución":
        "Clone vinculado com original em execução",
    "El original de este clon ('{0}') está corriendo.\n\nArrancar original y clon a la vez puede dar resultados impredecibles:\n\n  • El clon lee del disco del original los bloques que no ha modificado. Si el original escribe algo mientras el clon corre, el clon puede leer estados intermedios.\n  • La vista del sistema de archivos del clon ya está anclada al estado de su primer arranque para los bloques de metadatos, así que los cambios nuevos del original probablemente no se vean, pero el riesgo de lectura inconsistente sigue ahí.\n\nRecomendaciones:\n  • Apaga el original antes de arrancar el clon (o al revés).\n  • O desenlaza el clon con '🧬 Desenlazar' para que sea totalmente independiente.\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "O original deste clone ('{0}') está em execução.\n\nIniciar original e clone ao mesmo tempo pode dar resultados imprevisíveis:\n\n  • O clone lê do disco do original os blocos que não modificou. Se o original gravar algo enquanto o clone estiver rodando, o clone pode ler estados intermediários.\n  • A visão do sistema de arquivos do clone já está ancorada ao estado de sua primeira inicialização para os blocos de metadados, então as novas alterações do original provavelmente não serão vistas, mas o risco de leitura inconsistente permanece.\n\nRecomendações:\n  • Desligue o original antes de iniciar o clone (ou vice-versa).\n  • Ou desvincule o clone com '🧬 Desvincular' para que seja totalmente independente.\n\nEste aviso não aparecerá novamente para esta VM nesta sessão.",
    "Clon enlazado con backing roto":
        "Clone vinculado com backing quebrado",
    "Este clon enlazado espera el backing en:\n\n    {0}\n\nResuelto contra su carpeta queda en:\n\n    {1}\n\nEse archivo no existe. La VM original ('{2}') probablemente se movió o se borró.\n\nQEMU fallará al arrancar con:\n    Could not open backing file: No such file or directory\n\nOpciones:\n  • Mueve también la VM original de vuelta a su carpeta, o\n  • Copia la carpeta 'VirtualMachines/' entera (con original\n    y clon juntos) a la nueva ubicación, o\n  • Si aún puedes, usa '🧬 Desenlazar' en la pestaña Resumen\n    para independizar este clon (puede fallar si el backing\n    ya no está disponible).\n\nEste aviso no volverá a aparecer para esta VM en esta sesión.":
        "Este clone vinculado espera o backing em:\n\n    {0}\n\nResolvido em relação à sua pasta, ele fica em:\n\n    {1}\n\nEsse arquivo não existe. A VM original ('{2}') provavelmente foi movida ou excluída.\n\nO QEMU falhará ao iniciar com:\n    Could not open backing file: No such file or directory\n\nOpções:\n  • Traga a VM original de volta para sua pasta, ou\n  • Copie a pasta 'VirtualMachines/' inteira (com original\n    e clone juntos) para o novo local, ou\n  • Se ainda puder, use '🧬 Desvincular' na aba Resumo\n    para tornar este clone independente (pode falhar se o backing\n    não estiver mais disponível).\n\nEste aviso não aparecerá novamente para esta VM nesta sessão.",
    "No se pudo determinar el disco principal de la VM original.\n\nEl clon enlazado necesita un disco base QCOW2 sobre el que\ncrear el backing file. Si la VM no tiene discos, usa\n'Clon completo'.":
        "Não foi possível determinar o disco principal da VM original.\n\nO clone vinculado precisa de um disco base QCOW2 sobre o qual\ncriar o backing file. Se a VM não tiver discos, use\n'Clone completo'.",
    "No se pudo inspeccionar el disco original.\n\n{0}":
        "Não foi possível inspecionar o disco original.\n\n{0}",
    "El disco principal de la VM original está en formato {0}.\n\nEl clon enlazado solo funciona con QCOW2 (necesita backing\nfile). Usa 'Clon completo' si quieres copiar el disco tal cual.":
        "O disco principal da VM original está no formato {0}.\n\nO clone vinculado só funciona com QCOW2 (precisa de backing\nfile). Use 'Clone completo' se quiser copiar o disco como está.",
    "No se pudo crear la carpeta del clon.\n\n{0}":
        "Não foi possível criar a pasta do clone.\n\n{0}",
    "qemu-img create falló.\n\n{0}": "qemu-img create falhou.\n\n{0}",
    "No se pudo crear el delta QCOW2.\n\n{0}":
        "Não foi possível criar o delta QCOW2.\n\n{0}",
    "El backing file quedó guardado como ruta ABSOLUTA, lo que haría el clon no portable.\n\nSe ha abortado la operación para no dejar un clon defectuoso. Reporta esto como bug.":
        "O backing file foi salvo como caminho ABSOLUTO, o que tornaria o clone não portátil.\n\nA operação foi abortada para não deixar um clone defeituoso. Reporte isto como bug.",
    "No se pudieron copiar los archivos auxiliares.\n\n{0}":
        "Não foi possível copiar os arquivos auxiliares.\n\n{0}",
    "El clon se creó pero no se pudo reescribir su vm_config.ini.\n\n{0}\n\nRevisa manualmente el archivo antes de usar la VM.":
        "O clone foi criado, mas seu vm_config.ini não pôde ser reescrito.\n\n{0}\n\nVerifique manualmente o arquivo antes de usar a VM.",
    "La máquina virtual '{0}' fue clonada correctamente (clon enlazado).\n\nEl disco base se comparte con el original mediante un backing\nfile QCOW2 con ruta relativa. El clon ocupa muy poco espacio,\npero DEPENDE del original:\n\n  • Si borras o mueves la VM original, el clon se rompe.\n  • Una vez que el clon arranque por primera vez, los cambios\n    que hagas DESPUÉS en el original NO se verán en el clon:\n    la vista del sistema de archivos queda anclada al estado\n    del primer arranque. Trata el original como de solo lectura\n    mientras el clon exista.\n  • Los snapshots completos (RAM) no funcionarán en este clon\n    — solo de disco. QEMU no puede restaurar (loadvm) un\n    snapshot completo sobre un QCOW2 con backing file.\n  • Los snapshots del clon no son reproducibles mientras el\n    original pueda cambiar: al restaurar, se mezcla el delta\n    guardado con el estado ACTUAL del backing.\n  • Si quieres independizarlo, usa '🧬 Desenlazar' cuando esté\n    apagado.\n\nPara mover o copiar la estructura completa a otro host,\nllévate la carpeta 'VirtualMachines/' entera.":
        "A máquina virtual '{0}' foi clonada corretamente (clone vinculado).\n\nO disco base é compartilhado com o original por meio de um backing\nfile QCOW2 com caminho relativo. O clone ocupa muito pouco espaço,\nmas DEPENDE do original:\n\n  • Se você excluir ou mover a VM original, o clone quebra.\n  • Uma vez que o clone inicializar pela primeira vez, as alterações\n    que você fizer DEPOIS no original NÃO serão vistas no clone:\n    a visão do sistema de arquivos fica ancorada ao estado\n    da primeira inicialização. Trate o original como somente leitura\n    enquanto o clone existir.\n  • Snapshots completos (RAM) não funcionarão neste clone\n    — apenas de disco. O QEMU não pode restaurar (loadvm) um\n    snapshot completo sobre um QCOW2 com backing file.\n  • Os snapshots do clone não são reproduzíveis enquanto o\n    original puder mudar: ao restaurar, o delta salvo é misturado\n    com o estado ATUAL do backing.\n  • Se quiser torná-lo independente, use '🧬 Desvincular' quando\n    estiver desligado.\n\nPara mover ou copiar a estrutura completa para outro host,\nleve a pasta 'VirtualMachines/' inteira.",

    # ================================================================
    # vm_lifecycle_mixin: unlink / delete
    # ================================================================
    "Desenlazar clon": "Desvincular clone",
    "Esta VM no es un clon enlazado, no hay nada que desenlazar.":
        "Esta VM não é um clone vinculado, não há nada a desvincular.",
    "La VM '{0}' está encendida.\n\nApágala antes de desenlazarla: con QEMU activo el archivo\nestá bloqueado y el convert no puede reemplazarlo.":
        "A VM '{0}' está ligada.\n\nDesligue-a antes de desvinculá-la: com o QEMU ativo o arquivo\nestá bloqueado e o convert não pode substituí-lo.",
    "No se encontró el disco principal del clon.":
        "O disco principal do clone não foi encontrado.",
    "Se convertirá el disco principal del clon <b>{0}</b> en un QCOW2 <b>autónomo</b>.<br><br>Después de esto, el clon deja de depender del original y puede moverse o copiarse por separado.<br><br><b>Requiere:</b><br>&nbsp;&nbsp;• Espacio libre en el host (~1.1× el tamaño del disco).<br>&nbsp;&nbsp;• La VM apagada (ya lo está).<br>&nbsp;&nbsp;• No cerrar la aplicación durante el proceso.<br><br>El resultado se verifica como QCOW2 válido y se reemplaza atómicamente. Si algo falla a mitad, el archivo original del clon queda intacto.":
        "O disco principal do clone <b>{0}</b> será convertido em um QCOW2 <b>autônomo</b>.<br><br>Após isto, o clone deixa de depender do original e pode ser movido ou copiado separadamente.<br><br><b>Requer:</b><br>&nbsp;&nbsp;• Espaço livre no host (~1,1× o tamanho do disco).<br>&nbsp;&nbsp;• A VM desligada (já está).<br>&nbsp;&nbsp;• Não fechar o aplicativo durante o processo.<br><br>O resultado é verificado como QCOW2 válido e substituído atomicamente. Se algo falhar no meio, o arquivo original do clone permanece intacto.",
    "Desenlazado cancelado por el usuario.":
        "Desvinculação cancelada pelo usuário.",
    "Desenlazado": "Desvinculado",
    "El clon '{0}' ya es autónomo.\n\nTamaño antes: {1}\nTamaño después: {2}\n\nPuedes mover la VM sin llevarte la original.":
        "O clone '{0}' agora é autônomo.\n\nTamanho antes: {1}\nTamanho depois: {2}\n\nVocê pode mover a VM sem levar a original.",
    "No se pudo desenlazar el clon.\n\n{0}":
        "Não foi possível desvincular o clone.\n\n{0}",
    "Convirtiendo el clon en un QCOW2 autónomo…":
        "Convertendo o clone em um QCOW2 autônomo…",
    "Eliminar VM": "Excluir VM",
    "Se eliminará únicamente la carpeta de la máquina virtual:\n\n{0}\n\n":
        "Apenas a pasta da máquina virtual será excluída:\n\n{0}\n\n",
    "Los siguientes medios están fuera de la carpeta de la VM y NO se eliminarán:\n":
        "As seguintes mídias estão fora da pasta da VM e NÃO serão excluídas:\n",
    "\u26a0 ESTA VM ES EL ORIGINAL DE {0} CLON(ES) ENLAZADO(S):\n":
        "\u26a0 ESTA VM É O ORIGINAL DE {0} CLONE(S) VINCULADO(S):\n",
    "\n\nSi continúas, esos clones quedarán inutilizables (su backing file ya no existirá).\n\nSe recomienda desenlazarlos primero: selecciona cada clon y pulsa '🧬 Desenlazar' en su pestaña Resumen.\n\n":
        "\n\nSe você continuar, esses clones ficarão inutilizáveis (seu backing file não existirá mais).\n\nRecomenda-se desvinculá-los primeiro: selecione cada clone e clique em '🧬 Desvincular' na aba Resumo.\n\n",
    "¿Deseas continuar?": "Deseja continuar?",
    "Eliminar máquina virtual": "Excluir máquina virtual",
    "No se pudo eliminar '{0}'.\n\n{1}":
        "Não foi possível excluir '{0}'.\n\n{1}",

    # ================================================================
    # guest_integration_mixin.py
    # ================================================================
    "Montaje automático": "Montagem automática",
    "La VM arrancó, pero no se pudo configurar el montaje automático dentro del SO.\n\n{0}\n\nComprueba que qemu-guest-agent esté instalado y ejecutándose en el guest (pestaña Guest Tools). Una vez instalado, el montaje se hará solo en el próximo arranque de la VM.":
        "A VM iniciou, mas a montagem automática dentro do SO não pôde ser configurada.\n\n{0}\n\nVerifique se o qemu-guest-agent está instalado e em execução no guest (aba Guest Tools). Uma vez instalado, a montagem será feita automaticamente na próxima inicialização da VM.",
    "La carpeta compartida VirtioFS ya está conectada a la VM.\n\nEn Linux el dispositivo debe montarse dentro del guest. En un LiveCD no es posible hacerlo de forma persistente desde el host sin un agente instalado en el guest.\n\nComando(s):\n\n":
        "A pasta compartilhada VirtioFS já está conectada à VM.\n\nNo Linux o dispositivo precisa ser montado dentro do guest. Em um LiveCD não é possível fazê-lo de forma persistente a partir do host sem um agente instalado no guest.\n\nComando(s):\n\n",
    "\n\nEn una instalación Linux permanente podremos añadir automontaje mediante fstab/systemd en una versión posterior.":
        "\n\nEm uma instalação Linux permanente, poderemos adicionar automontagem via fstab/systemd em uma versão posterior.",
    "Carpeta compartida lista": "Pasta compartilhada pronta",
    "Guest Tools": "Guest Tools",
    "Carpeta:\n{0}": "Pasta:\n{0}",
    "Generando ISO de Guest Tools…": "Gerando ISO de Guest Tools…",
    "ISO creada.": "ISO criada.",
    "ISO disponible: {0}": "ISO disponível: {0}",
    "Crear ISO de Guest Tools": "Criar ISO de Guest Tools",
    "No se pudo crear la ISO.\n\n{0}":
        "Não foi possível criar a ISO.\n\n{0}",
    "La ISO se guarda en la carpeta GuestTools.":
        "A ISO é salva na pasta GuestTools.",
    "Selecciona (o crea) una VM primero.":
        "Selecione (ou crie) uma VM primeiro.",
    "Creando ISO de Guest Tools…": "Criando ISO de Guest Tools…",
    "Guest Tools — Adjuntar a la VM": "Guest Tools — Anexar à VM",
    "No se pudo crear ni adjuntar la ISO.\n\n{0}":
        "Não foi possível criar nem anexar a ISO.\n\n{0}",
    "Se creará la ISO y se adjuntará como CD/DVD a esta VM.":
        "A ISO será criada e anexada como CD/DVD a esta VM.",
    "Esta VM ya tiene la ISO de Guest Tools adjunta como CD/DVD.":
        "Esta VM já tem a ISO de Guest Tools anexada como CD/DVD.",
    "ISO de Guest Tools adjuntada a esta VM como CD/DVD.\n\nEn el próximo arranque, dentro del guest: monta la unidad y ejecuta\nINSTALL-LINUX.SH (con sudo) o INSTALL-WINDOWS.CMD (como Administrador).":
        "ISO de Guest Tools anexada a esta VM como CD/DVD.\n\nNa próxima inicialização, dentro do guest: monte a unidade e execute\nINSTALL-LINUX.SH (com sudo) ou INSTALL-WINDOWS.CMD (como Administrador).",
    "No se pudo adjuntar la ISO.\n\n{0}":
        "Não foi possível anexar a ISO.\n\n{0}",
    "Estado: canal no disponible. Enciende la VM con Guest Agent activado.":
        "Estado: canal indisponível. Ligue a VM com o Guest Agent ativado.",
    "Estado: consultando al Guest Agent...":
        "Estado: consultando o Guest Agent...",
    "Estado: sin respuesta del guest agent ({0}).":
        "Estado: sem resposta do guest agent ({0}).",
    "Estado: QEMU Guest Agent responde correctamente (v{0}).":
        "Estado: QEMU Guest Agent responde corretamente (v{0}).",
    "Estado: QGA respondió con un error: {0}":
        "Estado: QGA respondeu com um erro: {0}",
    "Estado: canal QGA presente; pulsa Probar conexión.":
        "Estado: canal QGA presente; clique em Testar conexão.",
    "Estado: canal QGA no activo en este momento.":
        "Estado: canal QGA não ativo neste momento.",
    "Manual": "Manual",
    "Automático al iniciar SO": "Automático ao iniciar SO",
    "Automático bajo demanda": "Automático sob demanda",
    "Solo lectura": "Somente leitura",
    "Lectura / escritura": "Leitura / gravação",
    "Carpeta compartida": "Pasta compartilhada",
    "Seleccionar carpeta del host": "Selecionar pasta do host",
    "Carpeta del host:": "Pasta do host:",
    "Etiqueta / guest:": "Rótulo / guest:",
    "Método:": "Método:",
    "Automático": "Automático",
    "Montaje en el guest:": "Montagem no guest:",
    "Acceso:": "Acesso:",
    "La política de montaje es la misma para todos los SO: Manual, Automático al iniciar SO o Automático bajo demanda. El mecanismo real de montaje se adapta al SO invitado y a sus componentes de integración. En un LiveCD, el montaje persistente normalmente no puede configurarse desde el host.":
        "A política de montagem é a mesma para todos os SOs: Manual, Automático ao iniciar SO ou Automático sob demanda. O mecanismo real de montagem se adapta ao SO convidado e a seus componentes de integração. Em um LiveCD, a montagem persistente normalmente não pode ser configurada a partir do host.",
    "Aceptar": "OK",
    "La carpeta del host no existe o no es un directorio.":
        "A pasta do host não existe ou não é um diretório.",
    "Desactivado": "Desativado",
    "Host → SO invitado": "Host → SO convidado",
    "SO invitado → Host": "SO convidado → Host",
    "Bidireccional": "Bidirecional",
    "No se añadirá ningún canal de clipboard.":
        "Nenhum canal de clipboard será adicionado.",
    "QEMU vdagent + GTK: bidireccional. Requiere spice-vdagent/SPICE Guest Tools.":
        "QEMU vdagent + GTK: bidirecional. Requer spice-vdagent/SPICE Guest Tools.",
    "macOS: integración de clipboard pendiente.":
        "macOS: integração de clipboard pendente.",
    "Selecciona una VM para comprobar la integración disponible.":
        "Selecione uma VM para verificar a integração disponível.",
    "Se activará automáticamente al iniciar la VM.":
        "Será ativado automaticamente ao iniciar a VM.",
    "No se activa.": "Não é ativado.",
    "Configuración actual: {0}. {1} {2}":
        "Configuração atual: {0}. {1} {2}",
    "Clipboard": "Clipboard",
    "Configuración del clipboard guardada para esta VM.":
        "Configuração do clipboard salva para esta VM.",
    "Compartir": "Compartilhar",
    "Configuración guardada. Se aplicará en el próximo arranque.":
        "Configuração salva. Será aplicada na próxima inicialização.",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Faltando:\n\n• {0}\n\nDeseja instalá-las agora usando o gerenciador de pacotes do sistema?",

    # ================================================================
    # mac_recovery_mixin.py
    # ================================================================
    "Para macOS utiliza 'Descargar System Recovery'. Apple distribuye el instalador completo como una aplicación; el flujo de Recovery de OSX-KVM es el método integrado en este gestor.":
        "Para macOS, use 'Baixar System Recovery'. A Apple distribui o instalador completo como um aplicativo; o fluxo de Recovery do OSX-KVM é o método integrado neste gerenciador.",
    "Android-x86 / Bliss OS no tienen descarga automática. Descarga la ISO desde https://www.android-x86.org/download.html o https://blissos.org/ y selecciónala en Plataforma → Android.":
        "Android-x86 / Bliss OS não têm download automático. Baixe a ISO de https://www.android-x86.org/download.html ou https://blissos.org/ e selecione-a em Plataforma → Android.",
    "System Recovery de macOS — {0}": "System Recovery do macOS — {0}",
    "La imagen se descarga y verifica directamente en la carpeta de la VM.":
        "A imagem é baixada e verificada diretamente na pasta da VM.",
    "Iniciando descarga…": "Iniciando download…",
    "Recovery preparado.": "Recovery pronto.",
    "Apple no devolvió una sesión de Recovery válida.":
        "A Apple não retornou uma sessão de Recovery válida.",
    "Apple no devolvió todos los datos del Recovery: {0}":
        "A Apple não retornou todos os dados do Recovery: {0}",
    "{0} — {1:.1f} MB descargados": "{0} — {1:.1f} MB baixados",
    "{0} — 100%": "{0} — 100%",
    "El chunklist de System Recovery está incompleto.":
        "O chunklist do System Recovery está incompleto.",
    "Cabecera de chunklist de Apple no válida.":
        "Cabeçalho de chunklist da Apple inválido.",
    "Chunklist de Apple no válido.": "Chunklist da Apple inválido.",
    "Chunklist truncado en el bloque {0}.":
        "Chunklist truncado no bloco {0}.",
    "La verificación del Recovery falló en el bloque {0}.":
        "A verificação do Recovery falhou no bloco {0}.",
    "La imagen Recovery contiene datos adicionales no descritos por el chunklist.":
        "A imagem Recovery contém dados adicionais não descritos pelo chunklist.",
    "No hay una carpeta de VM seleccionada.":
        "Nenhuma pasta de VM selecionada.",
    "Consultando Apple…": "Consultando a Apple…",
    "Descargando chunklist…": "Baixando chunklist…",
    "Descargando chunklist": "Baixando chunklist",
    "Descargando BaseSystem.dmg…": "Baixando BaseSystem.dmg…",
    "Descargando BaseSystem.dmg": "Baixando BaseSystem.dmg",
    "Verificando integridad…": "Verificando integridade…",
    "Verificación completada.": "Verificação concluída.",
    "No se encontró 'dmg2img' y no se pudo instalar automáticamente. Instálalo con el gestor de paquetes (en Arch/CachyOS: paru -S dmg2img).":
        "'dmg2img' não encontrado e não foi possível instalá-lo automaticamente. Instale-o com o gerenciador de pacotes (no Arch/CachyOS: paru -S dmg2img).",
    "Convirtiendo BaseSystem.dmg → BaseSystem.img…":
        "Convertendo BaseSystem.dmg → BaseSystem.img…",
    "dmg2img no pudo preparar BaseSystem.img.\n{0}":
        "dmg2img não pôde preparar BaseSystem.img.\n{0}",
    "dmg2img terminó pero BaseSystem.img no existe o está vacío.":
        "dmg2img terminou, mas BaseSystem.img não existe ou está vazio.",

    # ================================================================
    # install_flow_mixin.py
    # ================================================================
    "No se encontró qemu-system-x86_64 en PATH. Ejecuta ./run.sh (instala las dependencias de sistema) o instala qemu-system-x86 / qemu-kvm.":
        "qemu-system-x86_64 não encontrado no PATH. Execute ./run.sh (instala as dependências do sistema) ou instale qemu-system-x86 / qemu-kvm.",
    "/dev/kvm no está disponible; QEMU podría funcionar sin aceleración KVM.":
        "/dev/kvm não está disponível; o QEMU pode funcionar sem aceleração KVM.",
    "El usuario no tiene permisos de lectura/escritura sobre /dev/kvm.":
        "O usuário não tem permissões de leitura/gravação sobre /dev/kvm.",
    "No se detectó un firmware OVMF conocido para Secure Boot.":
        "Nenhum firmware OVMF conhecido foi detectado para Secure Boot.",
    "El dispositivo de almacenamiento '{0}' apunta a un archivo que ya no existe: {1}":
        "O dispositivo de armazenamento '{0}' aponta para um arquivo que não existe mais: {1}",
    "La carpeta compartida '{0}' apunta a una ruta del host que ya no existe: {1}":
        "A pasta compartilhada '{0}' aponta para um caminho do host que não existe mais: {1}",
    "Solo quedan {0} GB libres donde vive esta VM; puede fallar durante el uso.":
        "Restam apenas {0} GB livres onde esta VM reside; ela pode falhar durante o uso.",
    "El orden de arranque prioriza el CD/DVD, pero el disco '{0}' ya tiene datos (~{1} GB). Si el sistema ya está instalado, esto puede intentar reinstalar en vez de arrancarlo.":
        "A ordem de inicialização prioriza o CD/DVD, mas o disco '{0}' já contém dados (~{1} GB). Se o sistema já estiver instalado, isto pode tentar reinstalar em vez de inicializá-lo.",
    "Advertencia": "Aviso",
    "Debe indicar un nombre para la máquina virtual.":
        "Você precisa informar um nome para a máquina virtual.",
    'El nombre no puede contener: \\ / : * ? " < > |':
        'O nome não pode conter: \\ / : * ? " < > |',
    "La VM ya está corriendo": "A VM já está em execução",
    "'{0}' ya tiene un proceso QEMU activo. Iniciarla de nuevo puede corromper el disco (dos procesos escribiendo el mismo archivo) o chocar con los sockets ya en uso.\n\nDetén la VM actual antes de volver a iniciarla.":
        "'{0}' já tem um processo QEMU ativo. Iniciá-la novamente pode corromper o disco (dois processos gravando no mesmo arquivo) ou conflitar com os sockets já em uso.\n\nPare a VM atual antes de iniciá-la novamente.",
    "No se puede iniciar la VM": "Não é possível iniciar a VM",
    "Falta QEMU en el sistema. Instala qemu-system-x86 y vuelve a intentarlo.":
        "O QEMU está faltando no sistema. Instale qemu-system-x86 e tente novamente.",
    "Revisión previa": "Verificação prévia",
    "¿Deseas continuar de todos modos?": "Deseja continuar de qualquer forma?",
    "Configuración incompatible": "Configuração incompatível",
    "Secure Boot requiere UEFI (OVMF).": "Secure Boot requer UEFI (OVMF).",
    "El TPM 2.0 no se aplica al flujo actual de macOS/OSX-KVM.":
        "TPM 2.0 não se aplica ao fluxo atual de macOS/OSX-KVM.",
    "Dependencias faltantes": "Dependências faltantes",
    "No se pudieron preparar automáticamente las dependencias necesarias.\n\n{0}":
        "Não foi possível preparar automaticamente as dependências necessárias.\n\n{0}",
    "System Recovery de macOS": "System Recovery do macOS",
    "No se pudo preparar System Recovery antes de iniciar la VM.\n\n{0}":
        "Não foi possível preparar o System Recovery antes de iniciar a VM.\n\n{0}",
    "Disco existente con otra configuración":
        "Disco existente com outra configuração",
    "Ya existe un disco para '{0}' con {1} / {2} / {3}, distinto a lo solicitado ({4} / {5} / {6}).\n\n¿Desea eliminarlo y crear uno nuevo con los parámetros actuales?\n(\"No\" conserva el disco existente tal como está.)":
        "Já existe um disco para '{0}' com {1} / {2} / {3}, diferente do solicitado ({4} / {5} / {6}).\n\nDeseja excluí-lo e criar um novo com os parâmetros atuais?\n(\"Não\" mantém o disco existente como está.)",
    "Debe indicar una ruta de archivo ISO de Windows válida o seleccionar 'Descargar instalador de Windows automáticamente' en CD/DVD.":
        "Você precisa informar um caminho válido de arquivo ISO do Windows ou selecionar 'Baixar instalador do Windows automaticamente' no CD/DVD.",
    "Android": "Android",
    "Debes configurar la ISO de Android-x86 o Bliss OS en Configuración → Almacenamiento → CD / DVD.\n\nDescárgala de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAñade una unidad CD/DVD y elige «Usar ISO/IMG/DMG existente».":
        "Você precisa configurar a ISO do Android-x86 ou Bliss OS em Configuração → Armazenamento → CD / DVD.\n\nBaixe-a de:\n  • https://www.android-x86.org/download.html\n  • https://blissos.org/\n\nAdicione uma unidade CD/DVD e escolha «Usar ISO/IMG/DMG existente».",
    "Error": "Erro",
    "No se encuentra la carpeta 'OSX-KVM'.":
        "A pasta 'OSX-KVM' não foi encontrada.",
    "Error al guardar configuración": "Erro ao salvar configuração",
    "No se pudo guardar vm_config.ini para '{0}': {1}":
        "Não foi possível salvar vm_config.ini para '{0}': {1}",
    "No se puede preparar el passthrough USB": "Não é possível preparar o passthrough USB",
    "La VM no se iniciará hasta resolver el acceso al USB.\n\n{0}\n\nNo se debe seleccionar un Root Hub. La memoria USB debe estar desmontada del anfitrión.":
        "A VM não iniciará até que o acesso ao USB seja resolvido.\n\n{0}\n\nUm Root Hub não deve ser selecionado. O pendrive precisa estar desmontado do host.",
    "Instalador del sistema operativo": "Instalador do sistema operacional",
    "La descarga se realiza dentro de la carpeta de la VM.":
        "O download é feito dentro da pasta da VM.",
    "Máquina virtual iniciada.": "Máquina virtual iniciada.",
    "Descarga cancelada por el usuario.": "Download cancelado pelo usuário.",
    "QEMU terminó con error. Revisa la consola de progreso.":
        "O QEMU terminou com erro. Verifique o console de progresso.",

    # ================================================================
    # api_mixin.py (handlers)
    # ================================================================
    "Peticiones recientes": "Requisições recentes",

    # kvm_preflight_v1
    '/dev/kvm no está disponible. La VM arrancará con emulación por software (TCG), que es 10-100× más lenta que KVM.\n\n{0}':
        '/dev/kvm não está disponível. A VM será iniciada com emulação por software (TCG), 10-100× mais lenta que o KVM.\n\n{0}',
    "Tu usuario no puede usar /dev/kvm (no está en el grupo 'kvm'). La VM arrancará con emulación por software (muy lenta).\n\n{0}":
        "Seu usuário não pode usar /dev/kvm (não está no grupo 'kvm'). A VM será iniciada com emulação por software (muito lenta).\n\n{0}",

    # kvm_preflight_v1_fix1
    'Idioma de la interfaz.':
        'Idioma da interface.',
}
