# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda2d - Traducciones al portugues (Brasil) - Tanda 2d.

Cubre la pestana Configuracion Host completa:
  - Estado del sistema de virtualizacion.
  - Diagnostico PCI / VFIO (IOMMU, VT-d, preparar intel_iommu=on,
    abrir UEFI/BIOS, arbol de dispositivos).
  - Permisos USB del host (regla udev).
  - Dependencias de carpetas compartidas.
  - Apariencia (selector de tema).
  - Atajos de teclado configurables.
  - API REST local.

  Tambien cubre dos entradas del sidebar de Config VM que faltaban:
  Passthrough y Comparticion.
"""

TRANSLATIONS = {

    # ================================================================
    # Sidebar Config VM: entradas que faltaban
    # ================================================================
    "Passthrough": "Passthrough",
    "Compartición": "Compartilhamento",

    # ================================================================
    # Pestana 'Configuracion Host' - subtitulo
    # ================================================================
    "Ajustes y diagnostico del sistema anfitrion. Nada de esta seccion se guarda con la VM: aplica a todo el equipo.":
        "Ajustes e diagnóstico do sistema anfitrião. Nada desta seção é salvo com a VM: aplica-se a todo o computador.",

    # ================================================================
    # Apariencia (theme_selector_v1)
    # ================================================================
    "Apariencia": "Aparência",
    "Sistema (predeterminado)": "Sistema (padrão)",
    "Claro": "Claro",
    "Oscuro": "Escuro",
    "Tema visual de la aplicacion.\n"
    "  - Sistema: usa el estilo y la paleta del escritorio.\n"
    "  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n"
    "    propia, independiente del SO.\n\n"
    "Al elegir Claro u Oscuro, la app cambia el estilo de Qt a\n"
    "Fusion. Al volver a Sistema, se restaura el estilo original\n"
    "del escritorio (Breeze, Adwaita, etc.).":
        "Tema visual do aplicativo.\n"
        "  - Sistema: usa o estilo e a paleta da área de trabalho.\n"
        "  - Claro / Escuro: força o estilo Fusion com uma paleta\n"
        "    própria, independente do SO.\n\n"
        "Ao escolher Claro ou Escuro, o aplicativo muda o estilo do Qt para\n"
        "Fusion. Ao voltar para Sistema, o estilo original da área de\n"
        "trabalho é restaurado (Breeze, Adwaita, etc.).",
    "Tema:": "Tema:",
    "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\n"
    "reiniciar la app para que TODOS los widgets se repinten con los\n"
    "colores nuevos (depende del estilo del escritorio).":
        "Ao alternar entre 'Sistema' e 'Claro/Escuro' pode ser necessário\n"
        "reiniciar o aplicativo para que TODOS os widgets sejam repintados com\n"
        "as novas cores (depende do estilo da área de trabalho).",
    "Cambio de tema": "Mudança de tema",
    "Se ha cambiado el tema.\n\n"
    "Algunos estilos del escritorio (Kvantum en KDE, por\n"
    "ejemplo) pueden no repintar todos los widgets hasta\n"
    "reiniciar la aplicacion.\n\n"
    "¿Quieres reiniciar ahora para asegurar que todos los\n"
    "elementos se vean correctamente?":
        "O tema foi alterado.\n\n"
        "Alguns estilos da área de trabalho (Kvantum no KDE, por\n"
        "exemplo) podem não repintar todos os widgets até\n"
        "reiniciar o aplicativo.\n\n"
        "Deseja reiniciar agora para garantir que todos os\n"
        "elementos sejam exibidos corretamente?",

    # ================================================================
    # Atajos de teclado configurables (configurable_shortcuts_v1)
    # ================================================================
    "Atajos de teclado": "Atalhos de teclado",
    "Reasigna los atajos globales de la aplicacion. Los cambios\n"
    "se aplican al instante, sin reiniciar.":
        "Reatribui os atalhos globais do aplicativo. As alterações\n"
        "são aplicadas imediatamente, sem reiniciar.",
    "Configurar atajos...": "Configurar atalhos...",
    "Configurar atajos de teclado": "Configurar atalhos de teclado",
    "Haz clic en <b>Cambiar...</b> para capturar una nueva\n"
    "combinacion de teclas. Pulsa <b>Escape</b> durante la\n"
    "captura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\n"
    "para deshabilitar un atajo.":
        "Clique em <b>Alterar...</b> para capturar uma nova\n"
        "combinação de teclas. Pressione <b>Escape</b> durante a\n"
        "captura para cancelá-la. Use <b>Del</b> ou <b>Backspace</b>\n"
        "para desabilitar um atalho.",
    "Accion": "Ação",
    "Atajo": "Atalho",
    "Cambiar...": "Alterar...",
    "Restaurar todos por defecto": "Restaurar tudo para o padrão",
    "(sin atajo)": "(sem atalho)",
    "Conflicto de atajos": "Conflito de atalhos",
    "El atajo {0} ya esta asignado a:\n\n  {1}\n\nElige otro o cambia primero el otro atajo.":
        "O atalho {0} já está atribuído a:\n\n  {1}\n\nEscolha outro ou altere primeiro o outro atalho.",
    "Restaurar atajos": "Restaurar atalhos",
    "¿Restaurar los cuatro atajos a sus valores por defecto?":
        "Restaurar os quatro atalhos para seus valores padrão?",
    "Pulsa la nueva combinacion": "Pressione a nova combinação",
    "<b>Pulsa la combinacion de teclas que quieras asignar.</b>":
        "<b>Pressione a combinação de teclas que deseja atribuir.</b>",
    "Esperando pulsacion...\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "Aguardando tecla...\n\nEscape cancela. Del ou Backspace desabilita o atalho.",
    "Atajo actual: <b>{0}</b>": "Atalho atual: <b>{0}</b>",
    "Solo has pulsado un modificador. Anade una tecla normal.\n\nEscape cancela. Supr o Retroceso deshabilita el atajo.":
        "Você pressionou apenas um modificador. Adicione uma tecla normal.\n\nEscape cancela. Del ou Backspace desabilita o atalho.",
    "Abrir menu de Medios (CD/DVD + USB)":
        "Abrir menu de Mídias (CD/DVD + USB)",
    "Reconectar el widget VNC": "Reconectar o widget VNC",
    "Alternar Consola Grafica": "Alternar Console Gráfico",
    "Entrar / salir del modo presentacion":
        "Entrar / sair do modo apresentação",

    # ================================================================
    # API REST local (rest_api_v1)
    # ================================================================
    "API REST local": "API REST local",
    "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar VMs desde scripts, dashboards o CI. Todo se autentica con un token local; <b>no</b> es accesible desde la red.":
        "Expõe uma API HTTP mínima em <b>127.0.0.1</b> para controlar VMs a partir de scripts, dashboards ou CI. Tudo é autenticado com um token local; <b>não</b> é acessível pela rede.",
    "Activar API REST local": "Ativar API REST local",
    "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\nCambios requieren apagar y volver a encender la API.":
        "Porta TCP onde o servidor escuta. Somente 127.0.0.1.\nAlterações requerem desligar e religar a API.",
    "Puerto:": "Porta:",
    "URL:": "URL:",
    "Token:": "Token:",
    "Mostrar / ocultar el token": "Mostrar / ocultar o token",
    "Copiar": "Copiar",
    "Regenerar": "Regenerar",
    "Genera un token nuevo. Las peticiones con el token anterior\ndejarán de funcionar.":
        "Gera um novo token. As requisições com o token anterior\ndeixarão de funcionar.",
    "Ver peticiones recientes": "Ver requisições recentes",
    "Ejemplo de uso desde terminal:<br><code>curl -H 'X-API-Token: &lt;tu-token&gt;' http://127.0.0.1:8730/api/vms</code>":
        "Exemplo de uso pelo terminal:<br><code>curl -H 'X-API-Token: &lt;seu-token&gt;' http://127.0.0.1:8730/api/vms</code>",
    "API REST": "API REST",
    "<b style='color:#2e7d32;'>Activa</b> — {0} peticiones desde el arranque":
        "<b style='color:#2e7d32;'>Ativa</b> — {0} requisições desde a inicialização",
    "<b style='color:#888;'>Detenida</b>":
        "<b style='color:#888;'>Parada</b>",
    "No se pudo arrancar la API REST.\n\n{0}":
        "Não foi possível iniciar a API REST.\n\n{0}",
    "Regenerar token": "Regenerar token",
    "Se generará un token nuevo y el anterior dejará de funcionar.\n\n¿Continuar?":
        "Um novo token será gerado e o anterior deixará de funcionar.\n\nContinuar?",
    "Se regeneró el token pero no se pudo reiniciar la API:\n\n{0}":
        "O token foi regenerado, mas não foi possível reiniciar a API:\n\n{0}",
    "Peticiones recientes a la API": "Requisições recentes à API",
    "Últimas peticiones atendidas por la API. Se conservan las 50 más recientes.":
        "Últimas requisições atendidas pela API. As 50 mais recentes são preservadas.",
    "(sin peticiones todavía)": "(sem requisições ainda)",

    # ================================================================
    # Estado del sistema de virtualizacion (Config Host)
    # ================================================================
    "Estado del sistema de virtualización": "Estado do sistema de virtualização",
    "Distribución: comprobando...": "Distribuição: verificando...",
    "Gestor de paquetes: comprobando...": "Gerenciador de pacotes: verificando...",
    "\U0001f504 Comprobar dependencias": "\U0001f504 Verificar dependências",
    "\U0001f504\ufe0f Comprobar dependencias": "\U0001f504\ufe0f Verificar dependências",
    "\U0001f6e0 Comprobar/Reparar dependencias":
        "\U0001f6e0 Verificar/Reparar dependências",
    "\U0001f6e0\ufe0f Comprobar/Reparar dependencias":
        "\U0001f6e0\ufe0f Verificar/Reparar dependências",

    # ================================================================
    # Diagnostico PCI / VFIO (passthrough_mixin)
    # ================================================================
    "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. El programa comprobará el acceso a /dev/bus/usb, desmontará automáticamente el almacenamiento USB seleccionado del anfitrión y solicitará permisos administrativos solo cuando sea necesario. No selecciones Root Hubs.":
        "Passthrough de hardware físico. PCI usa VFIO; USB usa usb-host sobre XHCI. O programa verificará o acesso a /dev/bus/usb, desmontará automaticamente o armazenamento USB selecionado do anfitrião e solicitará permissões administrativas apenas quando necessário. Não selecione Root Hubs.",
    "Diagnóstico PCI / VFIO": "Diagnóstico PCI / VFIO",
    "Comprobando Intel VT-d / IOMMU...": "Verificando Intel VT-d / IOMMU...",
    "\U0001f504 Comprobar IOMMU / VFIO": "\U0001f504 Verificar IOMMU / VFIO",
    "\u2139 Ver diagnóstico detallado": "\u2139 Ver diagnóstico detalhado",
    "\U0001f6e0 Preparar intel_iommu=on": "\U0001f6e0 Preparar intel_iommu=on",
    "\u2699 Abrir UEFI/BIOS": "\u2699 Abrir UEFI/BIOS",
    "Usar": "Usar",
    "IOMMU / Driver": "IOMMU / Driver",
    "\U0001f504 Detectar dispositivos": "\U0001f504 Detectar dispositivos",
    "\U0001f4be Guardar selección": "\U0001f4be Salvar seleção",
    "\U0001f50c Conectar USB en caliente": "\U0001f50c Conectar USB a quente",
    "\u23cf Desconectar USB": "\u23cf Desconectar USB",

    # --- Diagnostico VFIO: textos de estado ---
    "\u2705 Intel VT-d / IOMMU activo": "\u2705 Intel VT-d / IOMMU ativo",
    "\u26a0 VT-d detectado por firmware, pero no hay grupos IOMMU utilizables":
        "\u26a0 VT-d detectado pelo firmware, mas sem grupos IOMMU utilizáveis",
    "\u274c Intel VT-d / IOMMU no detectado": "\u274c Intel VT-d / IOMMU não detectado",
    "(sin datos)": "(sem dados)",
    "<b>{0}</b><br>"
    "Firmware/ACPI DMAR: {1}<br>"
    "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>"
    "Gestor de arranque: {4}<br>"
    "Parámetros kernel: <code>{5}</code>":
        "<b>{0}</b><br>"
        "Firmware/ACPI DMAR: {1}<br>"
        "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI prontos para VFIO: {3}<br>"
        "Gerenciador de inicialização: {4}<br>"
        "Parâmetros do kernel: <code>{5}</code>",
    "Desconocido": "Desconhecido",
    "<br>\u26a0 El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.":
        "<br>\u26a0 A CPU não foi identificada como Intel; verificar diagnóstico AMD/IOMMU.",
    "<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. "
    "Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.":
        "<br>Recomendação: usar <b>Preparar intel_iommu=on</b> e reiniciar. "
        "Se após reiniciar não houver grupos, verificar VT-d na BIOS/UEFI.",
    "<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar "
    "<code>intel_iommu=on</code> en el arranque.":
        "<br>Recomendação: habilitar Intel VT-d na BIOS/UEFI e depois ativar "
        "<code>intel_iommu=on</code> na inicialização.",

    # --- Diagnosticos de preparacion IOMMU ---
    "El procesador no se identificó como Intel; no se aplicará intel_iommu=on.":
        "O processador não foi identificado como Intel; intel_iommu=on não será aplicado.",
    "No pude identificar de forma segura el gestor de arranque.":
        "Não foi possível identificar com segurança o gerenciador de inicialização.",
    "La preparación automática está implementada actualmente para GRUB. "
    "Gestor detectado: {0}.":
        "A preparação automática está implementada atualmente para o GRUB. "
        "Gerenciador detectado: {0}.",
    "No se pudo leer {0}.": "Não foi possível ler {0}.",
    "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub.":
        "GRUB_CMDLINE_LINUX_DEFAULT não foi encontrado em /etc/default/grub.",
    "intel_iommu=on ya está presente en /etc/default/grub.":
        "intel_iommu=on já está presente em /etc/default/grub.",
    "operación cancelada": "operação cancelada",
    "Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ":
        "/etc/default/grub foi modificado, mas o grub.cfg não pôde ser regenerado: ",
    "error desconocido": "erro desconhecido",
    "Se añadió intel_iommu=on y se regeneró GRUB.":
        "intel_iommu=on foi adicionado e o GRUB foi regenerado.",
    "IOMMU / VT-d": "IOMMU / VT-d",
    "El IOMMU ya aparece activo. No es necesario modificar el arranque.":
        "O IOMMU já aparece ativo. Não é necessário modificar a inicialização.",
    "No se identificó un CPU Intel.": "Nenhuma CPU Intel foi identificada.",
    "Preparar Intel IOMMU": "Preparar Intel IOMMU",
    "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\n"
    "Se hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\n"
    "Esto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\n"
    "Gestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?":
        "intel_iommu=on será adicionado à configuração do gerenciador de inicialização.\n\n"
        "Uma cópia de segurança será feita antes de modificá-la e autorização administrativa será solicitada.\n\n"
        "Isto NÃO ativa VT-d na BIOS/UEFI; essa parte deve ser habilitada no firmware.\n\n"
        "Gerenciador detectado: {0}\nArquivo: {1}\n\nContinuar?",
    "no identificado": "não identificado",
    "Configuración actualizada.": "Configuração atualizada.",
    "\n\nReinicia el equipo para que el parámetro tenga efecto.":
        "\n\nReinicie o computador para que o parâmetro tenha efeito.",
    "No se pudo preparar IOMMU": "Não foi possível preparar o IOMMU",
    "Abrir UEFI/BIOS": "Abrir UEFI/BIOS",
    "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\n"
    "Busca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?":
        "O computador reiniciará diretamente para a configuração do firmware se o sistema permitir.\n\n"
        "Procure uma opção chamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d ou similar e ative-a.\n\nReiniciar agora?",
    "No se pudo solicitar el reinicio al firmware.":
        "Não foi possível solicitar o reinício ao firmware.",
    "No se pudo abrir UEFI/BIOS": "Não foi possível abrir UEFI/BIOS",
    "Desactivado por parámetro del kernel": "Desativado por parâmetro do kernel",
    "Activo": "Ativo",
    "VT-d detectado por firmware/kernel; IOMMU sin grupos visibles":
        "VT-d detectado pelo firmware/kernel; IOMMU sem grupos visíveis",
    "No detectado": "Não detectado",
    "Detectado": "Detectado",
    "No confirmado": "Não confirmado",
    "\u2713 Listo para VFIO": "\u2713 Pronto para VFIO",
    "\u26a0 Sin grupo IOMMU": "\u26a0 Sem grupo IOMMU",
    "\u26a0 Comparte grupo IOMMU": "\u26a0 Compartilha grupo IOMMU",
    "\u26a0 Requiere preparación VFIO": "\u26a0 Requer preparação VFIO",

    # --- Detalle tecnico (dialogo VFIO) ---
    "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===":
        "=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ===",
    "Estado: {0}": "Estado: {0}",
    "Arquitectura: {0}": "Arquitetura: {0}",
    "desconocida": "desconhecida",
    "CPU Intel detectado: {0}": "CPU Intel detectada: {0}",
    "intel_iommu=on en kernel actual: {0}":
        "intel_iommu=on no kernel atual: {0}",
    "IOMMU desactivado por parámetro: {0}":
        "IOMMU desativado por parâmetro: {0}",
    "Clases IOMMU: {0}": "Classes IOMMU: {0}",
    "Gestor de arranque: {0}": "Gerenciador de inicialização: {0}",
    "desconocido": "desconhecido",
    "Configuración: {0}": "Configuração: {0}",
    "no identificada": "não identificada",
    "Parámetros kernel: {0}": "Parâmetros do kernel: {0}",
    "=== DISPOSITIVOS PCI ===": "=== DISPOSITIVOS PCI ===",
    "{0} | {1} | driver={2} | grupo={3} | estado={4}":
        "{0} | {1} | driver={2} | grupo={3} | estado={4}",
    "sin driver": "sem driver",
    "Diagnóstico VFIO": "Diagnóstico VFIO",
    "Diagnóstico copiado al portapapeles.":
        "Diagnóstico copiado para a área de transferência.",
    "No se pudo copiar el diagnóstico":
        "Não foi possível copiar o diagnóstico",
    "Diagnóstico Intel VT-d / IOMMU / VFIO":
        "Diagnóstico Intel VT-d / IOMMU / VFIO",
    "\U0001f4cb Copiar": "\U0001f4cb Copiar",

    # --- _pci_preflight ---
    "IOMMU/Intel VT-d: {0}": "IOMMU/Intel VT-d: {0}",
    "Firmware/ACPI DMAR: {0}": "Firmware/ACPI DMAR: {0}",
    "Grupos IOMMU: {0}": "Grupos IOMMU: {0}",
    "{0}: no tiene grupo IOMMU ({1})": "{0}: não tem grupo IOMMU ({1})",
    "{0}: comparte grupo IOMMU {1} con {2}":
        "{0}: compartilha grupo IOMMU {1} com {2}",
    "{0}: driver actual {1}; todavía no está ligado a vfio-pci":
        "{0}: driver atual {1}; ainda não está vinculado ao vfio-pci",
    "\u2022 {0} | grupo {1} | driver {2}":
        "\u2022 {0} | grupo {1} | driver {2}",

    # ================================================================
    # Permisos USB del host (udev)
    # ================================================================
    "Permisos USB del host": "Permissões USB do host",
    "Para poder pasar memorias o discos USB a la VM sin pedir contraseña cada vez, el sistema necesita una regla udev que conceda acceso al usuario activo. Puedes instalarla aquí con un clic; solo se aplica a esta categoría de dispositivos.":
        "Para poder passar pen drives ou discos USB à VM sem pedir senha toda vez, o sistema precisa de uma regra udev que conceda acesso ao usuário ativo. Você pode instalá-la aqui com um clique; ela se aplica apenas a esta categoria de dispositivos.",
    "Comprobando…": "Verificando…",
    "\U0001f504 Comprobar": "\U0001f504 Verificar",
    "\U0001f527 Configurar permisos USB": "\U0001f527 Configurar permissões USB",
    "Crea /etc/udev/rules.d/50-vm-manager-usb.rules con la regla\n"
    "que permite el acceso a los dispositivos USB al usuario activo.\n"
    "Solo se toca este archivo; el resto de la configuración USB\n"
    "del sistema no se modifica.":
        "Cria /etc/udev/rules.d/50-vm-manager-usb.rules com a regra\n"
        "que permite o acesso aos dispositivos USB ao usuário ativo.\n"
        "Apenas este arquivo é modificado; o restante da configuração USB\n"
        "do sistema não é alterado.",

    # --- Errores y avisos de USB ---
    "No existe {0}. El número Device puede haber cambiado; "
    "vuelve a detectar USB.":
        "{0} não existe. O número Device pode ter mudado; "
        "detecte o USB novamente.",
    "Sin acceso de lectura/escritura a {0}.":
        "Sem acesso de leitura/escrita a {0}.",
    "No se encontró 'pkexec'. No puedo solicitar permisos "
    "administrativos automáticamente.":
        "'pkexec' não encontrado. Não é possível solicitar permissões "
        "administrativas automaticamente.",
    "No se pudo ejecutar la acción administrativa ({0}): {1}":
        "Não foi possível executar a ação administrativa ({0}): {1}",
    "No se pudo realizar la acción administrativa ({0}). {1}":
        "Não foi possível realizar a ação administrativa ({0}). {1}",
    "No existe el nodo USB actual {0}; el dispositivo "
    "pudo cambiar de dirección.":
        "O nó USB atual {0} não existe; o dispositivo "
        "pode ter mudado de endereço.",
    "(desconocido)": "(desconhecido)",
    "dar acceso temporal al dispositivo USB":
        "conceder acesso temporário ao dispositivo USB",
    "No pude desmontar automáticamente el almacenamiento USB:\n"
    "{0}\n\n{1}":
        "Não foi possível desmontar automaticamente o armazenamento USB:\n"
        "{0}\n\n{1}",
    "El USB sigue sin acceso después de preparar el dispositivo: {0}":
        "O USB continua sem acesso depois de preparar o dispositivo: {0}",
    "USB {0} | nodo: {1} | acceso usuario: {2} | {3}":
        "USB {0} | nó: {1} | acesso do usuário: {2} | {3}",
    "NO": "NÃO",
    "no se pudo leer ({0})": "não foi possível ler ({0})",
    "error al comprobar: {0}": "erro ao verificar: {0}",
    "\u2705 Permisos USB: OK ({0}). El passthrough en caliente "
    "no pedirá contraseña.":
        "\u2705 Permissões USB: OK ({0}). O passthrough a quente "
        "não pedirá senha.",
    "Los permisos USB ya están configurados.\n"
    "Si quieres desinstalarlos, borra:\n"
    "{0}":
        "As permissões USB já estão configuradas.\n"
        "Se quiser desinstalá-las, exclua:\n"
        "{0}",
    "\u26a0 Permisos USB: {0}. El passthrough en caliente "
    "pedirá contraseña cada vez.":
        "\u26a0 Permissões USB: {0}. O passthrough a quente "
        "pedirá senha a cada vez.",
    "Permisos USB": "Permissões USB",
    "No se encontró 'pkexec'. Instálalo (paquete 'polkit') para "
    "que la aplicación pueda solicitar permisos administrativos "
    "de forma gráfica.":
        "'pkexec' não encontrado. Instale-o (pacote 'polkit') para "
        "que o aplicativo possa solicitar permissões administrativas "
        "graficamente.",
    "No se encontró 'udevadm'. Este sistema parece no usar udev "
    "para gestionar dispositivos USB. Aplica los permisos "
    "manualmente según tu distribución.":
        "'udevadm' não encontrado. Este sistema parece não usar o udev "
        "para gerenciar dispositivos USB. Aplique as permissões "
        "manualmente conforme sua distribuição.",
    "Configurar permisos USB": "Configurar permissões USB",
    "La operación tardó demasiado. Vuelve a intentarlo.":
        "A operação demorou demais. Tente novamente.",
    "Dispositivo USB inválido.": "Dispositivo USB inválido.",

    # ================================================================
    # Dependencias de carpetas compartidas (sf_dep)
    # ================================================================
    "Dependencias del host": "Dependências do host",
    "VirtioFS: SIN COMPROBAR": "VirtioFS: NÃO VERIFICADO",
    "9p: SIN COMPROBAR": "9p: NÃO VERIFICADO",
    "SMB: SIN COMPROBAR": "SMB: NÃO VERIFICADO",
    "9p forma parte de QEMU y normalmente no requiere instalar un paquete adicional en el host. VirtioFS necesita virtiofsd y SMB necesita Samba/smbd.":
        "O 9p faz parte do QEMU e normalmente não requer instalar um pacote adicional no host. VirtioFS precisa de virtiofsd e SMB precisa de Samba/smbd.",
    "\U0001f6e0\ufe0f Instalar faltantes": "\U0001f6e0\ufe0f Instalar faltantes",
    "FALTA": "FALTANDO",
    "Dependencias": "Dependências",
    "Las dependencias del host ya están instaladas.":
        "As dependências do host já estão instaladas.",
    "Instalar dependencias": "Instalar dependências",
    "Faltan:\n\n• {0}\n\n¿Deseas instalarlas ahora usando el gestor de paquetes del sistema?":
        "Faltando:\n\n• {0}\n\nDeseja instalá-las agora usando o gerenciador de pacotes do sistema?",
    "Las dependencias de carpetas compartidas quedaron instaladas y verificadas.":
        "As dependências de pastas compartilhadas foram instaladas e verificadas.",
    "No se pudieron instalar todas las dependencias.\n\n{0}":
        "Não foi possível instalar todas as dependências.\n\n{0}",

    # ================================================================
    # Strings del panel izquierdo de Resumen que faltaban
    # ================================================================
    "Selecciona primero una máquina virtual.":
        "Selecione uma máquina virtual primeiro.",
    "Primero selecciona una máquina virtual.":
        "Selecione uma máquina virtual primeiro.",
    "Primero selecciona una máquina virtual existente.":
        "Selecione uma máquina virtual existente primeiro.",
    "Selecciona primero una maquina virtual.":
        "Selecione uma máquina virtual primeiro.",
    "Selecciona una máquina virtual.":
        "Selecione uma máquina virtual.",
    "Selecciona una VM para administrarla. Usa 'Nueva máquina virtual' para crear otra.":
        "Selecione uma VM para gerenciá-la. Use 'Nova máquina virtual' para criar outra.",
    "Selecciona una máquina virtual en la lista de la izquierda.":
        "Selecione uma máquina virtual na lista à esquerda.",
    "No hay una máquina virtual seleccionada todavía.":
        "Nenhuma máquina virtual selecionada ainda.",
}
