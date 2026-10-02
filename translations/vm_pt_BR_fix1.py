# -*- coding: utf-8 -*-
"""vm_pt_BR_fix1 - Traducciones al portugues (Brasil) - Cierre.

Rellena las cadenas que quedaron sin traducir tras las 5 tandas.
Claves copiadas literalmente del .ts para asegurar coincidencia exacta.
"""

TRANSLATIONS = {

    # ================================================================
    # task_progress.py
    # ================================================================
    "Error:": "Erro:",

    # ================================================================
    # guest_integration_mixin.py: sub-pestana Compartir Carpetas
    # ================================================================
    "Integración Host ↔ Guest. Aquí se configuran las carpetas compartidas y el portapapeles (clipboard).":
        "Integração Host ↔ Guest. Aqui são configuradas as pastas compartilhadas e a área de transferência (clipboard).",
    "Comparte directorios del host con el guest. Automático usa VirtioFS en Linux cuando virtiofsd está disponible, 9p como respaldo y SMB para Windows/macOS. Solo lectura impide que el guest modifique archivos del host.":
        "Compartilha diretórios do host com o guest. Automático usa VirtioFS no Linux quando o virtiofsd está disponível, 9p como alternativa e SMB para Windows/macOS. Somente leitura impede que o guest modifique arquivos do host.",
    "Host": "Host",
    "Guest / etiqueta": "Guest / rótulo",
    "Método": "Método",
    "Montaje en el guest": "Montagem no guest",
    "Acceso": "Acesso",
    "\u2795 Agregar": "\u2795 Adicionar",
    "\U0001f4be Guardar": "\U0001f4be Salvar",
    "Guest Tools reúne la integración del sistema invitado: QEMU Guest Agent, controladores VirtIO y, en Windows, componentes SPICE. La ISO se puede montar como CD/DVD en cualquier VM.":
        "Guest Tools reúne a integração do sistema convidado: QEMU Guest Agent, drivers VirtIO e, no Windows, componentes SPICE. A ISO pode ser montada como CD/DVD em qualquer VM.",
    "QEMU Guest Agent": "QEMU Guest Agent",
    "Activar canal QEMU Guest Agent al iniciar la VM":
        "Ativar canal do QEMU Guest Agent ao iniciar a VM",
    "Canal:": "Canal:",
    "Estado: no comprobado": "Estado: não verificado",
    "\U0001f50e Probar conexión": "\U0001f50e Testar conexão",
    "\U0001f4bf Crear / actualizar ISO Guest Tools":
        "\U0001f4bf Criar / atualizar ISO Guest Tools",
    "\U0001f9f0 Adjuntar a esta VM": "\U0001f9f0 Anexar a esta VM",
    "Crea la ISO si falta y la adjunta como CD/DVD a la VM seleccionada, en un solo paso.":
        "Cria a ISO se faltar e a anexa como CD/DVD à VM selecionada, em um único passo.",
    "\U0001f4c2 Abrir carpeta de Guest Tools":
        "\U0001f4c2 Abrir pasta de Guest Tools",
    "Acciones:": "Ações:",
    "Linux: instala qemu-guest-agent desde esta ISO o desde el gestor de paquetes. Windows: INSTALL-WINDOWS.CMD descarga e instala VirtIO Guest Tools y SPICE Guest Tools desde sus fuentes oficiales. Después reinicia el guest.":
        "Linux: instale qemu-guest-agent a partir desta ISO ou do gerenciador de pacotes. Windows: INSTALL-WINDOWS.CMD baixa e instala VirtIO Guest Tools e SPICE Guest Tools de suas fontes oficiais. Depois reinicie o guest.",
    "Compartir clipboard": "Compartilhar clipboard",
    "Dirección:": "Direção:",
    "Linux y Windows: se usará QEMU vdagent + canal VirtIO/SPICE y GTK para clipboard bidireccional. El guest debe tener spice-vdagent (Linux) o SPICE Guest Tools (Windows). macOS se probará en una fase específica.":
        "Linux e Windows: será usado QEMU vdagent + canal VirtIO/SPICE e GTK para clipboard bidirecional. O guest precisa ter spice-vdagent (Linux) ou SPICE Guest Tools (Windows). macOS será testado em uma fase específica.",
    "\U0001f4be Guardar configuración": "\U0001f4be Salvar configuração",
    "Configuración por VM. El mecanismo concreto se seleccionará según el SO invitado y su soporte de integración.":
        "Configuração por VM. O mecanismo concreto será selecionado conforme o SO convidado e seu suporte de integração.",
    "Compartir Carpetas": "Compartilhar Pastas",

    # ================================================================
    # Panel Ayuda + valores dinamicos del panel host
    # ================================================================
    "<h2>Ayuda de Virtual.Machine</h2>": "<h2>Ajuda do Virtual.Machine</h2>",
    "OK": "OK",
    " ({0})": " ({0})",
    "SIN COMPROBAR": "NÃO VERIFICADO",
    "Virtualización: sin comprobar": "Virtualização: não verificada",
    "Pulsa 'Comprobar dependencias' para realizar el diagnóstico completo del sistema.":
        "Clique em 'Verificar dependências' para realizar o diagnóstico completo do sistema.",
    "Distribución: {0}": "Distribuição: {0}",
    "Gestor de paquetes: {0}": "Gerenciador de pacotes: {0}",
    "no encontrado": "não encontrado",
    "firmware disponible": "firmware disponível",
    "sin plantilla Secure Boot": "sem template de Secure Boot",
    "módulos": "módulos",
    "módulo no cargado": "módulo não carregado",
    "Virtualización: {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Audio {5} | GPU {6}":
        "Virtualização: {0} | QEMU {1} | KVM {2} | OVMF {3} | TPM {4} | Áudio {5} | GPU {6}",
    "REVISAR": "VERIFICAR",
    "sí": "sim",
    "no": "não",
    "Distribución: {0}\n"
    "Gestor de paquetes: {1}\n"
    "Secure Boot: {2}\n"
    "VirtIO: {3}\n"
    "Audio: {4}\n"
    "GPU: {5}\n"
    "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}":
        "Distribuição: {0}\n"
        "Gerenciador de pacotes: {1}\n"
        "Secure Boot: {2}\n"
        "VirtIO: {3}\n"
        "Áudio: {4}\n"
        "GPU: {5}\n"
        "OpenGL: {6} | Vulkan: {7} | VirGL: {8} | VFIO: {9}",
    "disponible": "disponível",
    "no disponible": "não disponível",
    "no detectado": "não detectado",
    "La comprobación/reparación terminó correctamente.":
        "A verificação/reparação foi concluída com sucesso.",
    "No se pudieron reparar todas las dependencias.\n\n{0}":
        "Não foi possível reparar todas as dependências.\n\n{0}",
    "Carpetas compartidas": "Pastas compartilhadas",
    "El socket de QEMU Guest Agent no está disponible.":
        "O socket do QEMU Guest Agent não está disponível.",
    "QEMU Guest Agent cerró el canal durante la sincronización.":
        "O QEMU Guest Agent fechou o canal durante a sincronização.",
    "Tiempo agotado sincronizando QEMU Guest Agent.":
        "Tempo esgotado ao sincronizar o QEMU Guest Agent.",
    "QEMU Guest Agent cerró el canal.":
        "O QEMU Guest Agent fechou o canal.",
    "Tiempo agotado esperando la respuesta de QEMU Guest Agent.":
        "Tempo esgotado aguardando a resposta do QEMU Guest Agent.",
    "Guest Agent no devolvió el PID de guest-exec.":
        "O Guest Agent não retornou o PID de guest-exec.",
    "guest-exec terminó con código {0}.":
        "guest-exec terminou com código {0}.",
    "Tiempo agotado esperando a que termine el comando ejecutado mediante QEMU Guest Agent.":
        "Tempo esgotado aguardando o término do comando executado via QEMU Guest Agent.",
    "El canal de QEMU Guest Agent no está disponible en esta VM.":
        "O canal do QEMU Guest Agent não está disponível nesta VM.",
    "El Guest Agent del invitado no respondió en {0} s (no está instalado o no se está ejecutando).":
        "O Guest Agent do convidado não respondeu em {0} s (não está instalado ou não está em execução).",

    # ================================================================
    # Boton "Agrandar" del media library
    # ================================================================
    "\u2197 Agrandar": "\u2197 Ampliar",

    # ================================================================
    # passthrough_mixin.py: menu Medios (CD/DVD + USB)
    # ================================================================
    "\U0001f4c0 Unidades ópticas": "\U0001f4c0 Unidades ópticas",
    "      (Sin unidades CD/DVD)": "      (Sem unidades CD/DVD)",
    "\U0001f310 descargar instalador al iniciar":
        "\U0001f310 baixar instalador ao iniciar",
    "\U0001f310 descargar Recovery al iniciar":
        "\U0001f310 baixar Recovery ao iniciar",
    "   \U0001f4c0 {0} \u2014 {1}": "   \U0001f4c0 {0} \u2014 {1}",
    "\U0001f4c2 Cambiar medio…": "\U0001f4c2 Trocar mídia…",
    "\u23cf Expulsar medio": "\u23cf Ejetar mídia",
    "\U0001f50c Dispositivos USB": "\U0001f50c Dispositivos USB",
    "      (La VM debe estar encendida para conectarlos)":
        "      (A VM precisa estar ligada para conectá-los)",
    "      Error al detectar USB: {0}":
        "      Erro ao detectar USB: {0}",
    "      (No hay dispositivos USB detectados)":
        "      (Nenhum dispositivo USB detectado)",
    "conectado a la VM": "conectado à VM",
    "disponible en el host": "disponível no host",
    "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
    "Estado: {5}\n\n{6}":
        "{0}\nVID:PID = {1}:{2}\nBus {3} \u00b7 Device {4}\n"
        "Estado: {5}\n\n{6}",
    "Clic para DESCONECTAR de la VM": "Clique para DESCONECTAR da VM",
    "Clic para CONECTAR a la VM": "Clique para CONECTAR à VM",
    "(Selecciona una VM primero)": "(Selecione uma VM primeiro)",
    "\U0001f4bf Medios de '{0}'": "\U0001f4bf Mídias de '{0}'",
    "\U0001f504 Refrescar": "\U0001f504 Atualizar",
    "\u2699 Gestionar USB en Passthrough…":
        "\u2699 Gerenciar USB em Passthrough…",
    "Grupo {0}": "Grupo {0}",
    "Sin grupo IOMMU": "Sem grupo IOMMU",
    " \u2022 {0}": " \u2022 {0}",
    "\u26a0 Revisar": "\u26a0 Verificar",
    "\u2713 Acceso OK": "\u2713 Acesso OK",
    "\u26a0 Revisar acceso": "\u26a0 Verificar acesso",
    "Passthrough: teclado o ratón del host":
        "Passthrough: teclado ou mouse do host",
    "Passthrough USB": "Passthrough USB",
    "Selecciona un dispositivo USB.": "Selecione um dispositivo USB.",
    "La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.":
        "A VM não está ligada; use Salvar seleção para conectá-lo na próxima inicialização.",
    "Dispositivo USB conectado en caliente a la VM.\n\n"
    "Nota: el host debe permitir acceso a /dev/bus/usb y el "
    "dispositivo no debería estar siendo usado por el sistema "
    "anfitrión.":
        "Dispositivo USB conectado a quente à VM.\n\n"
        "Nota: o host precisa permitir acesso a /dev/bus/usb e o "
        "dispositivo não deve estar em uso pelo sistema "
        "anfitrião.",
    "Error al conectar USB": "Erro ao conectar USB",
    "La VM no está encendida.": "A VM não está ligada.",
    "Solicitud de desconexión USB enviada a QEMU.":
        "Solicitação de desconexão USB enviada ao QEMU.",
    "Error al desconectar USB": "Erro ao desconectar USB",

    # ================================================================
    # Storage: tipos de disco
    # ================================================================
    "\U0001f4bd SATA": "\U0001f4bd SATA",
    "\u26a1 NVMe": "\u26a1 NVMe",
    "\u274c No hay un QCOW2 escribible disponible para snapshots completos de VM.":
        "\u274c Não há um QCOW2 gravável disponível para snapshots completos de VM.",
    "\u2705 Disco para estado de VM: {0} \u00b7 tamaño virtual: {1} \u00b7 archivo actual: {2} \u00b7 espacio libre del sistema de archivos: {3} \u00b7 reserva orientativa inicial: {4}. El snapshot QCOW2 crece según se modifican bloques.":
        "\u2705 Disco para estado da VM: {0} \u00b7 tamanho virtual: {1} \u00b7 arquivo atual: {2} \u00b7 espaço livre do sistema de arquivos: {3} \u00b7 reserva estimada inicial: {4}. O snapshot QCOW2 cresce conforme os blocos são modificados.",
    "\u26a0 {0} El snapshot podría fallar al quedarse sin espacio.":
        "\u26a0 {0} O snapshot pode falhar se ficar sem espaço.",
    "Disco": "Disco",
    "FDC": "FDC",
    "\U0001f310 Descargar instalador de Internet al iniciar":
        "\U0001f310 Baixar instalador da Internet ao iniciar",
    "\U0001f310 Instalador por Internet (se descargará al iniciar)":
        "\U0001f310 Instalador pela Internet (será baixado ao iniciar)",
    "\U0001f310 Descargar System Recovery al iniciar":
        "\U0001f310 Baixar System Recovery ao iniciar",
    "\U0001f310 System Recovery (se descargará al iniciar)":
        "\U0001f310 System Recovery (será baixado ao iniciar)",
    "Sin medio": "Sem mídia",
    "Sin grupo": "Sem grupo",

    # ================================================================
    # Bloque grande del popup "Pausar la VM"
    # ================================================================
    "Pausar la VM. Usa la flecha para más opciones:\n"
    "\u2022 Pausar (rápido): detiene sin guardar el estado en disco.\n"
    "\u2022 Reanudar: vuelve a ejecutar la VM pausada.\n"
    "\u2022 Tomar Snapshot: guarda el estado a disco y pausa.":
        "Pausar a VM. Use a seta para mais opções:\n"
        "\u2022 Pausar (rápido): para sem salvar o estado no disco.\n"
        "\u2022 Retomar: volta a executar a VM pausada.\n"
        "\u2022 Criar Instantâneo: salva o estado no disco e pausa.",

    # ================================================================
    # Aviso Android-x86 (con emoji VS16)
    # ================================================================
    "\u26a0 Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.":
        "\u26a0 Android-x86 9.0 (kernel 4.9) não inclui o driver VirtIO-GPU e cai em um shell de resgate com 'Detecting Android-x86…'. Use 'Automático' ou 'Red Hat QXL 2D'. As ISOs com kernel 5.10+ ou Bliss OS 15+ suportam VirtIO-GPU.",

    # ================================================================
    # _ExportOvfDialog
    # ================================================================
    "Exportar como OVF/OVA - {0}": "Exportar como OVF/OVA - {0}",
    "Exporta <b>{0}</b> como OVA (un solo archivo) o como OVF (carpeta con descriptor + discos sueltos).":
        "Exporta <b>{0}</b> como OVA (arquivo único) ou como OVF (pasta com descritor + discos avulsos).",
    "Formato del disco": "Formato do disco",
    "QCOW2 (recomendado) - instantaneo y comprimido":
        "QCOW2 (recomendado) - instantâneo e comprimido",
    "El disco se aplana (descartando snapshots internos) y se comprime con zlib. Ideal para reimportar en esta misma app.":
        "O disco é achatado (descartando snapshots internos) e comprimido com zlib. Ideal para reimportar neste mesmo aplicativo.",
    "VMDK stream-optimized - maxima compatibilidad con VirtualBox/VMware":
        "VMDK stream-optimized - compatibilidade máxima com VirtualBox/VMware",
    "Requiere conversion previa con qemu-img. Tarda mas y necesita espacio temporal. VMDK stream-optimized ya descarta snapshots.":
        "Requer conversão prévia com qemu-img. Demora mais e precisa de espaço temporário. VMDK stream-optimized já descarta snapshots.",
    "Opciones adicionales": "Opções adicionais",
    "Incluir medio de instalacion (BaseSystem.img)":
        "Incluir mídia de instalação (BaseSystem.img)",
    "Incluir archivos ISO en el OVA":
        "Incluir arquivos ISO no OVA",
    "Exportar": "Exportar",
    "El disco se convertira a <b>VMDK stream-optimized</b>. Este formato ya descarta los snapshots internos.":
        "O disco será convertido para <b>VMDK stream-optimized</b>. Este formato já descarta os snapshots internos.",
    "Los discos QCOW2 se <b>aplanan y comprimen</b> automaticamente al exportar: se descartan los snapshots internos y se aplica compresion zlib. Reduce el OVA entre un 40% y un 60%.":
        "Os discos QCOW2 são <b>achatados e comprimidos</b> automaticamente ao exportar: os snapshots internos são descartados e a compressão zlib é aplicada. Reduz o OVA entre 40% e 60%.",

    # ================================================================
    # _OvfImportPreviewDialog
    # ================================================================
    "Se ha leído el descriptor OVF. Revisa los datos detectados y corrige lo que haga falta antes de importar.<br><br><i>El sistema operativo detectado puede ser ambiguo: ajústalo si el original no coincide.</i>":
        "O descritor OVF foi lido. Revise os dados detectados e corrija o que for necessário antes de importar.<br><br><i>O sistema operacional detectado pode ser ambíguo: ajuste-o se o original não coincidir.</i>",
    "(sin nombre)": "(sem nome)",
    "(sin discos)": "(sem discos)",
    "<b>Detectado en el OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}":
        "<b>Detectado no OVF:</b><br>SO: {0} {1}<br>CPUs: {2} &nbsp; RAM: {3} MB<br>Discos: {4} — {5}",
    "Nombre de la VM:": "Nome da VM:",
    "GNU / Linux": "GNU / Linux",
    "Microsoft Windows": "Microsoft Windows",
    "macOS": "macOS",
    "Android (Android-x86 / Bliss OS)": "Android (Android-x86 / Bliss OS)",
    "Plataforma:": "Plataforma:",
    "Distribución / versión:": "Distribuição / versão:",
    "Importar solo la configuración (sin copiar los discos)":
        "Importar apenas a configuração (sem copiar os discos)",
    "Si está marcado, se importan solo los datos del descriptor (CPU, RAM, red, sistema operativo) y NO se convierten ni copian los discos. Útil para reutilizar una configuración sin duplicar gigabytes de disco.":
        "Se marcado, são importados apenas os dados do descritor (CPU, RAM, rede, sistema operacional) e os discos NÃO são convertidos nem copiados. Útil para reutilizar uma configuração sem duplicar gigabytes de disco.",
    "Importar": "Importar",
    "Distribución:": "Distribuição:",
    "Versión de Windows:": "Versão do Windows:",
    "Versión de macOS:": "Versão do macOS:",
    "Distribución Android:": "Distribuição Android:",
    "Debes escribir un nombre para la VM importada.":
        "Você precisa digitar um nome para a VM importada.",
}
