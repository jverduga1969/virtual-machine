# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda2c - Traducciones al portugues (Brasil) - Tanda 2c.

Cubre la pestana Configuracion VM completa:
  - Sistema (firmware, chipset, seguridad, opciones avanzadas, autostart,
    modo compatibilidad de snapshots).
  - Procesador (modelo CPU, nucleos).
  - Memoria (RAM asignada).
  - Pantalla (graficos, VRAM, VNC embebido, Consola remota, log VNC).
  - Red (adaptadores, modo, modelo).
  - Dispositivos (audio, puntero, puerto serie).
  - Almacenamiento (controladores, dispositivos, orden de arranque) +
    storage_mixin (Expandir disco).
"""

TRANSLATIONS = {

    # ================================================================
    # Sistema
    # ================================================================
    "Sistema": "Sistema",
    "Plataforma, firmware y opciones de bajo nivel del hardware virtual.":
        "Plataforma, firmware e opções de baixo nível do hardware virtual.",
    "<b>Firmware</b>": "<b>Firmware</b>",
    "BIOS (tradicional)": "BIOS (tradicional)",
    "UEFI (OVMF)": "UEFI (OVMF)",
    "<b>Chipset</b>": "<b>Chipset</b>",
    "i440FX (clásico)": "i440FX (clássico)",
    "Q35 (moderno, PCIe)": "Q35 (moderno, PCIe)",
    "i440FX: chipset clásico, PCI legado. Compatible con SO muy antiguos.\n"
    "Q35: chipset moderno con PCIe nativo, AHCI/SATA y mejor soporte para\n"
    "passthrough de dispositivos PCIe. Recomendado salvo compatibilidad específica.":
        "i440FX: chipset clássico, PCI legado. Compatível com SOs muito antigos.\n"
        "Q35: chipset moderno com PCIe nativo, AHCI/SATA e melhor suporte para\n"
        "passthrough de dispositivos PCIe. Recomendado, exceto por compatibilidade específica.",
    "<b>Seguridad</b>": "<b>Segurança</b>",
    "Secure Boot": "Secure Boot",
    "TPM 2.0": "TPM 2.0",
    "<b>Perfiles del sistema</b>": "<b>Perfis do sistema</b>",
    "Configuración optimizada para el sistema operativo seleccionado. Puede modificar los valores según sus necesidades.":
        "Configuração otimizada para o sistema operacional selecionado. Você pode modificar os valores conforme suas necessidades.",
    "<b>Opciones avanzadas</b>": "<b>Opções avançadas</b>",
    "Habilitar ACPI": "Habilitar ACPI",
    "Habilitar APIC": "Habilitar APIC",
    "Habilitar IOMMU": "Habilitar IOMMU",
    "PCIe Root Port": "PCIe Root Port",
    "Arrancar esta VM al abrir la aplicación": "Iniciar esta VM ao abrir o aplicativo",
    "Si está marcado, esta VM se arranca automáticamente al\n"
    "abrir la aplicación, tras un par de segundos.\n\n"
    "Las VMs marcadas se arrancan en cola, separadas por 4 s\n"
    "entre una y otra para no saturar el host. Las que ya estén\n"
    "corriendo se saltan.\n\n"
    "Nota: al auto-arrancar, la selección de la lista cambia a\n"
    "cada VM que se inicia.":
        "Se marcado, esta VM é iniciada automaticamente ao\n"
        "abrir o aplicativo, após alguns segundos.\n\n"
        "As VMs marcadas são iniciadas em fila, separadas por 4 s\n"
        "entre uma e outra para não saturar o host. As que já estiverem\n"
        "em execução são ignoradas.\n\n"
        "Nota: durante a inicialização automática, a seleção da lista muda para\n"
        "cada VM que é iniciada.",
    "Modo compatibilidad de snapshots (fuerza hardware snapshoteable)":
        "Modo de compatibilidade de snapshots (força hardware compatível com snapshots)",

    # ================================================================
    # Procesador
    # ================================================================
    "Procesador": "Processador",
    "Modelo de CPU y número de núcleos asignados a la máquina virtual.":
        "Modelo de CPU e número de núcleos atribuídos à máquina virtual.",
    "<b>Tipo de procesador</b>": "<b>Tipo de processador</b>",
    "Automático (recomendado)": "Automático (recomendado)",
    "Host (máximo rendimiento)": "Host (máximo desempenho)",
    "QEMU x86-64 (compatibilidad)": "QEMU x86-64 (compatibilidade)",
    "Automático usa el perfil del SO. Host ofrece el máximo rendimiento pero reduce la portabilidad de la VM.":
        "Automático usa o perfil do SO. Host oferece o máximo desempenho, mas reduz a portabilidade da VM.",
    "<b>Núcleos</b>": "<b>Núcleos</b>",
    "{0} núcleos": "{0} núcleos",
    "El número de núcleos se ajusta al par más cercano al valor elegido, hasta la mitad de los hilos del host.":
        "O número de núcleos é ajustado ao par mais próximo do valor escolhido, até a metade das threads do host.",

    # ================================================================
    # Memoria
    # ================================================================
    "Memoria": "Memória",
    "Cantidad de memoria RAM asignada a la máquina virtual.":
        "Quantidade de memória RAM atribuída à máquina virtual.",
    "<b>RAM asignada</b>": "<b>RAM atribuída</b>",
    "RAM del host: {0} GB (libre: {1} GB)": "RAM do host: {0} GB (livre: {1} GB)",
    "Asignar más de la mitad de la RAM del host puede provocar uso intensivo de swap. La sugerencia es dejar al menos 2 GB para el sistema anfitrión.":
        "Atribuir mais da metade da RAM do host pode causar uso intenso de swap. A sugestão é deixar pelo menos 2 GB para o sistema anfitrião.",

    # ================================================================
    # Pantalla
    # ================================================================
    "Pantalla": "Tela",
    "Controlador gráfico virtual y memoria de video.":
        "Controlador gráfico virtual e memória de vídeo.",
    "<b>Gráficos / GPU</b>": "<b>Gráficos / GPU</b>",
    "VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)":
        "VirtIO-GPU 2D (compatível • snap. de discos ✓ • snap. completo ✗)",
    "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)":
        "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)",
    "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)":
        "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)",
    "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)":
        "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)",
    "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)":
        "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)",
    "Sin video / Headless": "Sem vídeo / Headless",
    "Automático detecta las capacidades del host y usa aceleración 3D cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\nSnapshots:\n  • VirtIO-GPU 2D → solo snap. de discos.\n  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n  • VirGL / Venus → no soportan ningún tipo de snapshot.":
        "Automático detecta as capacidades do host e usa aceleração 3D quando é segura; caso contrário, volta para VirtIO-GPU 2D.\n\nSnapshots:\n  • VirtIO-GPU 2D → apenas snap. de discos.\n  • QXL e VMware SVGA → snap. completo (RAM + dispositivos).\n  • VirGL / Venus → não suportam nenhum tipo de snapshot.",
    "<b>Memoria de video (VRAM)</b>": "<b>Memória de vídeo (VRAM)</b>",
    "Host GPU: detectando…": "GPU do host: detectando…",
    "\U0001f5bc\ufe0f Mostrar la VM dentro de la app (consola VNC embebida)":
        "\U0001f5bc\ufe0f Mostrar a VM dentro do aplicativo (console VNC embutido)",
    "Cuando está activo, la VM se muestra dentro de la app.\n"
    "Fuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\n"
    "Si lo desactivas, la VM se abre en una ventana externa y puedes\n"
    "elegir modos con aceleración 3D (VirGL, Venus).":
        "Quando ativo, a VM é exibida dentro do aplicativo.\n"
        "Força gráficos sem aceleração OpenGL (o VNC não suporta GL).\n"
        "Se você desativar, a VM abre em uma janela externa e você pode\n"
        "escolher modos com aceleração 3D (VirGL, Venus).",

    # --- Consola remota ---
    "Consola remota": "Console remoto",
    "VNC (compatible con cualquier gráfico)": "VNC (compatível com qualquer gráfico)",
    "SPICE (mejor rendimiento en local)": "SPICE (melhor desempenho local)",
    "VNC: cliente ligero, funciona con cualquier dispositivo de video.\n"
    "SPICE: mejor rendimiento en local, requiere un visor spice-gtk.\n"
    "Con cualquiera de los dos, QEMU no abre ventana local: solo el socket.":
        "VNC: cliente leve, funciona com qualquer dispositivo de vídeo.\n"
        "SPICE: melhor desempenho local, requer um visualizador spice-gtk.\n"
        "Com qualquer um dos dois, o QEMU não abre janela local: apenas o socket.",
    "Protocolo:": "Protocolo:",
    "Embebida en la app": "Embutido no aplicativo",
    "Ventana externa (visor del sistema)": "Janela externa (visualizador do sistema)",
    "Ventana nativa de QEMU": "Janela nativa do QEMU",
    "Híbrida (VNC embebido + SPICE externo)": "Híbrida (VNC embutido + SPICE externo)",
    "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\n"
    "Ventana externa: se lanza el visor del sistema (vncviewer / spicy).\n"
    "Nativa QEMU: QEMU abre su propia ventana (comportamiento clásico).":
        "Embutida: a tela fica dentro deste aplicativo (aba Console Gráfico).\n"
        "Janela externa: inicia o visualizador do sistema (vncviewer / spicy).\n"
        "Nativa do QEMU: o QEMU abre sua própria janela (comportamento clássico).",
    "Modo:": "Modo:",
    "Log VNC detallado (DEBUG)": "Log VNC detalhado (DEBUG)",
    "Activa el nivel DEBUG del cliente VNC embebido.\n\n"
    "Por defecto INFO: el widget VNC no llena launch.log con\n"
    "una línea por cada frame. Actívalo solo para diagnosticar\n"
    "problemas concretos del cliente VNC; escribe miles de\n"
    "líneas por segundo y puede afectar al rendimiento.":
        "Ativa o nível DEBUG do cliente VNC embutido.\n\n"
        "Por padrão INFO: o widget VNC não enche o launch.log com\n"
        "uma linha por quadro. Ative apenas para diagnosticar\n"
        "problemas específicos do cliente VNC; grava milhares de\n"
        "linhas por segundo e pode afetar o desempenho.",

    # ================================================================
    # Red
    # ================================================================
    "Red": "Rede",
    "Adaptadores de red virtuales. Cada uno puede usar NAT, bridge o TAP.":
        "Adaptadores de rede virtuais. Cada um pode usar NAT, bridge ou TAP.",
    "Adaptadores": "Adaptadores",
    "\u2795 Agregar adaptador": "\u2795 Adicionar adaptador",
    "\u270f Editar": "\u270f Editar",
    "Sin red (ningún adaptador virtual)": "Sem rede (nenhum adaptador virtual)",
    "NAT / Internet (recomendado)": "NAT / Internet (recomendado)",
    "Bridge existente": "Bridge existente",
    "TAP": "TAP",
    "VirtIO (recomendado)": "VirtIO (recomendado)",
    "Intel E1000": "Intel E1000",
    "Realtek RTL8139": "Realtek RTL8139",
    "VMware VMXNET3": "VMware VMXNET3",
    "Interfaz/Bridge:": "Interface/Bridge:",

    # ================================================================
    # Dispositivos
    # ================================================================
    "Dispositivos": "Dispositivos",
    "Audio y otros dispositivos integrados de la máquina virtual.":
        "Áudio e outros dispositivos integrados da máquina virtual.",
    "<b>Audio</b>": "<b>Áudio</b>",
    "Intel HDA (recomendado)": "Intel HDA (recomendado)",
    "AC97": "AC97",
    "Sound Blaster 16": "Sound Blaster 16",
    "Sin sonido": "Sem som",
    "<b>Dispositivo de señalización (ratón / teclado)</b>":
        "<b>Dispositivo apontador (mouse / teclado)</b>",
    "USB Tablet (posición absoluta)": "USB Tablet (posição absoluta)",
    "USB Mouse (posición relativa)": "USB Mouse (posição relativa)",
    "USB Keyboard + Tablet": "USB Keyboard + Tablet",
    "VirtIO Tablet (requiere drivers en el guest)": "VirtIO Tablet (requer drivers no guest)",
    "PS/2 (clásico)": "PS/2 (clássico)",
    "Ninguno": "Nenhum",
    "Dispositivo de entrada que QEMU emula para el ratón/teclado.\n\n"
    "• Automático: macOS usa USB Tablet sobre NEC XHCI; el resto deja\n"
    "  el PS/2 por defecto de QEMU.\n"
    "• USB Tablet: posición absoluta (el cursor del guest sigue 1:1 al\n"
    "  del host). Recomendado si el cursor no se mueve bien.\n"
    "• USB Mouse: posición relativa, como un ratón físico.\n"
    "• USB Keyboard + Tablet: añade también un teclado USB.\n"
    "• VirtIO Tablet: mejor rendimiento, requiere drivers VirtIO en\n"
    "  el guest (no válido en macOS).\n"
    "• PS/2: ratón/teclado tradicionales de QEMU, sin USB.\n"
    "• Ninguno: sin ratón/teclado emulados.":
        "Dispositivo de entrada que o QEMU emula para mouse/teclado.\n\n"
        "• Automático: macOS usa USB Tablet sobre NEC XHCI; os demais mantêm\n"
        "  o PS/2 padrão do QEMU.\n"
        "• USB Tablet: posição absoluta (o cursor do guest acompanha 1:1 o\n"
        "  do host). Recomendado se o cursor não se mover bem.\n"
        "• USB Mouse: posição relativa, como um mouse físico.\n"
        "• USB Keyboard + Tablet: adiciona também um teclado USB.\n"
        "• VirtIO Tablet: melhor desempenho, requer drivers VirtIO no\n"
        "  guest (não válido no macOS).\n"
        "• PS/2: mouse/teclado tradicionais do QEMU, sem USB.\n"
        "• Nenhum: sem mouse/teclado emulados.",
    "Capturar el puerto serie a un archivo (serial.log)":
        "Capturar a porta serial para um arquivo (serial.log)",
    "Activa -serial file:<vm_dir>/serial.log en la linea de QEMU.\n\n"
    "El puerto serie del guest se vuelca a un archivo dentro de la\n"
    "carpeta de la VM. La BIOS/OVMF, el cargador de arranque y el\n"
    "kernel suelen escribir ahi su progreso: es la forma mas directa\n"
    "de ver por que una VM se queda en pantalla negra o se reinicia.\n\n"
    "El archivo se SOBREESCRIBE en cada arranque: solo conserva la\n"
    "ultima sesion. Se puede abrir con '📂 Carpeta' en la pestana\n"
    "Resumen.":
        "Ativa -serial file:<vm_dir>/serial.log na linha de comando do QEMU.\n\n"
        "A porta serial do guest é gravada em um arquivo dentro da\n"
        "pasta da VM. A BIOS/OVMF, o carregador de inicialização e o\n"
        "kernel costumam escrever ali seu progresso: é a forma mais direta\n"
        "de ver por que uma VM fica em tela preta ou reinicia.\n\n"
        "O arquivo é SOBRESCRITO a cada inicialização: só preserva a\n"
        "última sessão. Pode ser aberto com '📂 Pasta' na aba\n"
        "Resumo.",
    "Para pasar hardware físico (PCI/USB) a esta VM, usa la pestaña <b>Dispositivos</b> de la parte superior de la ventana.":
        "Para passar hardware físico (PCI/USB) a esta VM, use a aba <b>Dispositivos</b> no topo da janela.",

    # ================================================================
    # Almacenamiento
    # ================================================================
    "Almacenamiento": "Armazenamento",
    "Discos, unidades ópticas y orden de arranque de la máquina virtual.":
        "Discos, unidades ópticas e ordem de inicialização da máquina virtual.",
    "Controladores y dispositivos": "Controladores e dispositivos",
    "Dispositivo": "Dispositivo",
    "Tipo / archivo": "Tipo / arquivo",
    "Tamaño": "Tamanho",
    "\U0001f4c0 CD / DVD": "\U0001f4c0 CD / DVD",
    "\U0001f4bd Disco Duro": "\U0001f4bd Disco rígido",
    "\U0001f4be Disquete": "\U0001f4be Disquete",
    "\u270f Modificar": "\u270f Modificar",
    "\u270f\ufe0f Modificar": "\u270f\ufe0f Modificar",
    "\U0001f5dc Compactar": "\U0001f5dc Compactar",
    "\U0001f5dc\ufe0f Compactar": "\U0001f5dc\ufe0f Compactar",
    "Compacta un disco QCOW2 de la VM seleccionada.\n\n"
    "Reduce el archivo físico en el host eliminando bloques no\n"
    "usados (equivalente a 'qemu-img convert -c'). NO cambia el\n"
    "tamaño virtual que ve el sistema invitado.\n\n"
    "Se pedirá confirmación y se recomienda hacer un backup antes\n"
    "de proceder. Requiere que la VM esté apagada.":
        "Compacta um disco QCOW2 da VM selecionada.\n\n"
        "Reduz o arquivo físico no host removendo blocos não\n"
        "utilizados (equivalente a 'qemu-img convert -c'). NÃO altera o\n"
        "tamanho virtual que o sistema convidado vê.\n\n"
        "Será pedida confirmação e recomenda-se fazer um backup antes\n"
        "de prosseguir. Requer que a VM esteja desligada.",
    "Orden de arranque": "Ordem de inicialização",
    "\u2b06 Subir": "\u2b06 Subir",
    "\u2b07 Bajar": "\u2b07 Descer",
    "\U0001f5d1 Quitar": "\U0001f5d1 Remover",
    "\U0001f5d1\ufe0f Quitar": "\U0001f5d1\ufe0f Remover",

    # ================================================================
    # storage_mixin.py (Expandir disco)
    # ================================================================
    "Cambiar el medio de esta unidad CD/DVD.":
        "Trocar a mídia desta unidade CD/DVD.",
    "Los disquetes no se pueden redimensionar.\n"
    "Elimina este y crea otro si necesitas otro tamaño.":
        "Disquetes não podem ser redimensionados.\n"
        "Exclua este e crie outro se precisar de outro tamanho.",
    "\u2197 Expandir": "\u2197 Expandir",
    "Aumentar el tamaño virtual de este disco.\n"
    "El disco solo puede CRECER.":
        "Aumentar o tamanho virtual deste disco.\n"
        "O disco só pode CRESCER.",
    "Expandir disco": "Expandir disco",
    "No se encontro la informacion del dispositivo seleccionado.":
        "Não foi encontrada a informação do dispositivo selecionado.",
    "Los disquetes no se pueden redimensionar.\n\n"
    "Eliminalo y crea otro si necesitas otro tamano.":
        "Disquetes não podem ser redimensionados.\n\n"
        "Exclua-o e crie outro se precisar de outro tamanho.",
    "\u2197 Expandir disco": "\u2197 Expandir disco",
    "Dispositivo:": "Dispositivo:",
    "Tamano actual:": "Tamanho atual:",
    "Ejemplo: 120G (solo crecer)": "Exemplo: 120G (apenas crescer)",
    "Nuevo tamano:": "Novo tamanho:",
    "El disco solo puede CRECER. Si escribes un valor menor al actual, se rechaza y el campo vuelve al tamano original.\n\n"
    "Agrandar el archivo NO agranda la particion dentro del guest: tras aplicar el cambio, amplia tambien la particion/volumen desde el sistema invitado.":
        "O disco só pode CRESCER. Se você digitar um valor menor que o atual, ele será rejeitado e o campo volta ao tamanho original.\n\n"
        "Aumentar o arquivo NÃO aumenta a partição dentro do guest: após aplicar a alteração, amplie também a partição/volume pelo sistema convidado.",
    "No se pudo expandir el disco.\n\n{0}":
        "Não foi possível expandir o disco.\n\n{0}",
}
