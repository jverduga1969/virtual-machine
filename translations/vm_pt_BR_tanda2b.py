# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda2b - Traducciones al portugues (Brasil) - Tanda 2b.

Cubre: panel derecho del Resumen.
  - Boton 'Fijar' y su tooltip.
  - Panel 'Uso de recursos' (CPU/RAM/Disco/Red) + tooltips.
  - Panel 'Informacion general' (labels estaticos).
  - Panel 'Ultimo snapshot'.
  - Panel derecho dinamico (valores que se actualizan al seleccionar
    una VM: estado, CPU, RAM, disco, firmware, red, snapshots...).
"""

TRANSLATIONS = {

    # ================================================================
    # Boton Fijar
    # ================================================================
    "\U0001f4cc Fijar": "\U0001f4cc Fixar",
    "Fija este panel como columna derecha de la ventana, siempre visible.\n"
    "Útil para monitorizar CPU/RAM mientras trabajas en otra pestaña.\n"
    "Vuelve a pulsar para devolverlo a Resumen.":
        "Fixa este painel como coluna direita da janela, sempre visível.\n"
        "Útil para monitorar CPU/RAM enquanto você trabalha em outra aba.\n"
        "Clique novamente para devolvê-lo ao Resumo.",

    # ================================================================
    # Panel 'Uso de recursos' (graficos en vivo)
    # ================================================================
    "\U0001f4ca Uso de recursos": "\U0001f4ca Uso de recursos",
    "CPU (VM)": "CPU (VM)",
    "Uso de CPU del proceso QEMU en el host, atribuido a esta VM.\n"
    "100% = el proceso usa el equivalente a todos los hilos del host.\n"
    "Si el host tiene 8 hilos y QEMU usa 4, verás 50%.":
        "Uso de CPU do processo QEMU no host, atribuído a esta VM.\n"
        "100% = o processo usa o equivalente a todas as threads do host.\n"
        "Se o host tem 8 threads e o QEMU usa 4, você verá 50%.",
    "RAM (QEMU)": "RAM (QEMU)",
    "Memoria RSS del proceso QEMU en el host (lo que QEMU ocupa\n"
    "realmente en el sistema anfitrión), como porcentaje de la RAM\n"
    "total del host. No es la RAM que 've' el sistema invitado.":
        "Memória RSS do processo QEMU no host (o que o QEMU ocupa\n"
        "realmente no sistema anfitrião), como porcentagem da RAM\n"
        "total do host. Não é a RAM que o sistema convidado 'vê'.",
    "Disco (VM)": "Disco (VM)",
    "I/O de disco generado por el proceso QEMU para esta VM, según\n"
    "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
    "Es el tráfico real a los archivos de disco de la VM en el host.":
        "I/O de disco gerado pelo processo QEMU para esta VM, segundo\n"
        "/proc/<pid_qemu>/io (read_bytes + write_bytes).\n"
        "É o tráfego real para os arquivos de disco da VM no host.",
    "Red (VM)": "Rede (VM)",
    "Tráfico de red de esta VM.\n"
    "• Modo TAP/Bridge: se leen los contadores reales de la interfaz\n"
    "  asociada en el host (exacto).\n"
    "• Modo NAT: QEMU usa un stack interno sin interfaz visible en\n"
    "  el host, así que no se puede medir sin Guest Agent.\n"
    "  El gráfico mostrará 'NAT (sin medida)'.":
        "Tráfego de rede desta VM.\n"
        "• Modo TAP/Bridge: leem-se os contadores reais da interface\n"
        "  associada no host (exato).\n"
        "• Modo NAT: o QEMU usa uma pilha interna sem interface visível\n"
        "  no host, então não pode ser medido sem o Guest Agent.\n"
        "  O gráfico mostrará 'NAT (sem medição)'.",

    # ================================================================
    # Panel 'Informacion general' (labels estaticos)
    # ================================================================
    "\u2139\ufe0f Información general": "\u2139\ufe0f Informações gerais",
    "Estado:": "Estado:",
    "Tiempo activo:": "Tempo ativo:",
    "Procesos:": "Processos:",
    "Dirección IP:": "Endereço IP:",
    "Dirección MAC:": "Endereço MAC:",
    "Guest Agent:": "Guest Agent:",
    "Carpetas:": "Pastas:",
    "Clipboard:": "Clipboard:",
    "spice-vdagent:": "spice-vdagent:",
    "Detección de spice-vdagent en el guest vía QEMU Guest Agent.\n"
    "Cuando está activo, el clipboard bidireccional y la\n"
    "resolución automática funcionan.":
        "Detecção de spice-vdagent no guest via QEMU Guest Agent.\n"
        "Quando ativo, o clipboard bidirecional e a\n"
        "resolução automática funcionam.",
    "PID QEMU:": "PID QEMU:",
    "Uso de CPU del proceso QEMU expresado como porcentaje del total\n"
    "de hilos del host. Si el host tiene 8 hilos y QEMU usa 4, el\n"
    "valor mostrado es 50%.":
        "Uso de CPU do processo QEMU expresso como porcentagem do total\n"
        "de threads do host. Se o host tem 8 threads e o QEMU usa 4, o\n"
        "valor mostrado é 50%.",
    "CPU (VM):": "CPU (VM):",
    "Memoria RAM libre del host, respecto al total.":
        "Memória RAM livre do host, em relação ao total.",
    "RAM host:": "RAM host:",
    "Tamaño del archivo de disco principal de la VM y su tamaño\n"
    "virtual (lo que ve el sistema invitado).":
        "Tamanho do arquivo de disco principal da VM e seu tamanho\n"
        "virtual (o que o sistema convidado vê).",
    "Disco:": "Disco:",
    "Número de snapshots registrados y antigüedad del último.":
        "Número de instantâneos registrados e idade do último.",
    "Snapshots:": "Snapshots:",

    # ================================================================
    # Panel 'Ultimo snapshot'
    # ================================================================
    "\U0001f5bc\ufe0f Último snapshot": "\U0001f5bc\ufe0f Último instantâneo",
    "Sin VM seleccionada": "Nenhuma VM selecionada",
    "\u21a9 Restaurar este snapshot": "\u21a9 Restaurar este instantâneo",
    "Restaura el snapshot más reciente de esta VM.\n"
    "Si la VM está corriendo, se restaura en caliente (snapshot-load).\n"
    "Si está apagada, se restauran los discos QCOW2 internos.":
        "Restaura o instantâneo mais recente desta VM.\n"
        "Se a VM estiver em execução, é restaurado a quente (snapshot-load).\n"
        "Se estiver desligada, os discos QCOW2 internos são restaurados.",
    "Sin captura de pantalla": "Sem captura de tela",

    # ================================================================
    # Panel derecho dinamico (se actualiza al seleccionar una VM)
    # ================================================================
    "No hay una máquina virtual seleccionada.\n\n"
    "Pulsa 'Nueva máquina virtual' para comenzar.":
        "Nenhuma máquina virtual selecionada.\n\n"
        "Clique em 'Nova máquina virtual' para começar.",
    "Configura el sistema en la pestaña 'Configuración'.":
        "Configure o sistema na aba 'Configuração'.",
    "● Ejecutándose": "● Em execução",
    "● Pausada": "● Pausada",
    "● Apagada": "● Desligada",
    "Notas:": "Notas:",
    "Sí": "Sim",
    "No": "Não",
    "Red 1": "Rede 1",
    "Sin adaptadores configurados": "Nenhum adaptador configurado",
    "Disco Duro": "Disco rígido",
    "CD/DVD": "CD/DVD",
    "vacío": "vazio",
    "Sin dispositivos": "Sem dispositivos",
    "Sistema:": "Sistema:",
    "CPU:": "CPU:",
    "RAM:": "RAM:",
    "núcleos": "núcleos",
    "Firmware:": "Firmware:",
    "Secure Boot:": "Secure Boot:",
    "TPM:": "TPM:",
    "Gráficos:": "Gráficos:",
    "Audio:": "Áudio:",
    "Red:": "Rede:",
    "Almacenamiento:": "Armazenamento:",
    "Orden de arranque:": "Ordem de inicialização:",
    "Ubicación:": "Localização:",
    "VM nueva: todavía no se ha guardado una configuración.":
        "Nova VM: nenhuma configuração foi salva ainda.",
    "Configura la VM en la pestaña 'Configuración' y pulsa el botón de inicio.":
        "Configure a VM na aba 'Configuração' e clique no botão de iniciar.",
    "Usa 'Configuración' para modificar hardware y opciones avanzadas.":
        "Use 'Configuração' para modificar hardware e opções avançadas.",

    # ================================================================
    # Valores dinamicos de integracion Host <-> Guest (panel derecho)
    # ================================================================
    "Guest Agent: —": "Guest Agent: —",
    "Carpetas: —": "Pastas: —",
    "Clipboard: —": "Clipboard: —",
    "spice-vdagent: —": "spice-vdagent: —",
    "Guest Agent: apagado": "Guest Agent: desligado",
    "Carpetas: apagado": "Pastas: desligado",
    "Clipboard: apagado": "Clipboard: desligado",
    "spice-vdagent: apagado": "spice-vdagent: desligado",
    "Guest Agent: {0}": "Guest Agent: {0}",
    "activo": "ativo",
    "sin respuesta": "sem resposta",
    "Carpetas: {0}": "Pastas: {0}",
    "con problemas": "com problemas",
    "Clipboard: activo": "Clipboard: ativo",
    "Clipboard: desactivado": "Clipboard: desativado",
    "spice-vdagent: activo": "spice-vdagent: ativo",
    "spice-vdagent: no detectado": "spice-vdagent: não detectado",
}
