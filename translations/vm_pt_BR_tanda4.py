# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda4 - Traducciones al portugues (Brasil) - Tanda 4.

Cubre:
  - Consola Grafica: barra de botones, zoom, modo presentacion,
    pantalla completa del visor, combo de salida.
  - Consola de Progreso: filtros, botones de log, salud VM,
    limpiar procesos huerfanos.
  - Panel Ayuda (pestana).
  - console_backend.py (descripciones de modos VNC/SPICE).
  - console_ui_mixin.py (bloque de ayuda grande con pros/contras).
"""

TRANSLATIONS = {

    # ================================================================
    # Consola Grafica: botones de la barra superior
    # ================================================================
    "La VM no está corriendo.": "A VM não está em execução.",
    "\u2197 Abrir en ventana externa": "\u2197 Abrir em janela externa",
    "Lanza el visor externo del protocolo configurado en Pantalla,\n"
    "aunque el modo sea 'embebida'. Útil para tener las dos vistas a la vez.":
        "Abre o visualizador externo do protocolo configurado em Tela,\n"
        "mesmo que o modo seja 'embutido'. Útil para ter as duas visualizações ao mesmo tempo.",
    "Externos en pantalla completa": "Externos em tela cheia",
    "Cuando está marcado, los visores externos (los que abre el\n"
    "botón 'Abrir en ventana externa' o el modo 'Ventana externa'\n"
    "de Configuración → Pantalla) se lanzan ocupando toda la\n"
    "pantalla. NO afecta al visor embebido (VNC dentro de la app):\n"
    "para ese, usa el botón 'Pantalla completa del visor'.":
        "Quando marcado, os visualizadores externos (os abertos pelo\n"
        "botão 'Abrir em janela externa' ou o modo 'Janela externa'\n"
        "de Configuração → Tela) são iniciados ocupando toda a\n"
        "tela. NÃO afeta o visualizador embutido (VNC dentro do aplicativo):\n"
        "para esse, use o botão 'Tela cheia do visualizador'.",
    "\U0001f4bf Medios": "\U0001f4bf Mídias",
    "Medios de la VM: unidades CD/DVD y dispositivos USB.\n"
    "Mismo menú que el botón 'Medios' de la pestaña Resumen.\n"
    "Atajo: Ctrl+M.":
        "Mídias da VM: unidades CD/DVD e dispositivos USB.\n"
        "Mesmo menu do botão 'Mídias' da aba Resumo.\n"
        "Atalho: Ctrl+M.",
    "\U0001f504 Reconectar": "\U0001f504 Reconectar",
    "Reconectar el widget VNC.\n"
    "Útil si cambiaste la resolución del guest y la imagen\n"
    "quedó recortada o mal escalada. El cliente VNC básico\n"
    "no puede cambiar el tamaño de su framebuffer sin\n"
    "reconectar.\n\n"
    "Atajo: Ctrl+R.":
        "Reconectar o widget VNC.\n"
        "Útil se você alterou a resolução do guest e a imagem\n"
        "ficou recortada ou mal escalada. O cliente VNC básico\n"
        "não pode alterar o tamanho de seu framebuffer sem\n"
        "reconectar.\n\n"
        "Atalho: Ctrl+R.",

    # ================================================================
    # Consola Grafica: zoom del visor embebido
    # ================================================================
    "Zoom:": "Zoom:",
    "\U0001f50d\u2212": "\U0001f50d\u2212",
    "Reducir el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Reduzir o zoom do visualizador embutido.\n"
        "Níveis: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "Ajustado": "Ajustado",
    "\U0001f50d+": "\U0001f50d+",
    "Aumentar el zoom del visor embebido.\n"
    "Escalones: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.":
        "Aumentar o zoom do visualizador embutido.\n"
        "Níveis: 10, 25, 50, 75, 100, 125, 150, 200, 300, 400.",
    "\u229e Ajustar": "\u229e Ajustar",
    "Ajustar la imagen de la VM al tamaño del widget (escala\n"
    "automática). La VM se ve entera, sin barras de scroll.\n"
    "Si la relación de aspecto no coincide, aparecen bandas\n"
    "negras a los lados.":
        "Ajustar a imagem da VM ao tamanho do widget (escala\n"
        "automática). A VM aparece inteira, sem barras de rolagem.\n"
        "Se a proporção não coincidir, aparecem faixas\n"
        "pretas nas laterais.",
    "1:1 Tamaño real": "1:1 Tamanho real",
    "Mostrar la imagen de la VM a su resolución real (100%).\n"
    "Si no cabe en la ventana, aparecen barras de scroll.":
        "Mostrar a imagem da VM em sua resolução real (100%).\n"
        "Se não couber na janela, aparecem barras de rolagem.",

    # ================================================================
    # Consola Grafica: modo presentacion
    # ================================================================
    "\U0001f3ac Presentación": "\U0001f3ac Apresentação",
    "Modo presentación: oculta los paneles laterales, entra\n"
    "en pantalla completa y salta a la Consola Gráfica.\n"
    "Requiere que la VM esté encendida.\n\n"
    "Atajo: F11. Para salir: F11 o Escape.":
        "Modo apresentação: oculta os painéis laterais, entra\n"
        "em tela cheia e salta para o Console Gráfico.\n"
        "Requer que a VM esteja ligada.\n\n"
        "Atalho: F11. Para sair: F11 ou Escape.",
    "\u26f6 Pantalla completa del visor": "\u26f6 Tela cheia do visualizador",
    "Salir con:": "Sair com:",
    "Ctrl derecho (como VirtualBox)": "Ctrl direito (como VirtualBox)",
    "Ctrl+Alt+Intro": "Ctrl+Alt+Enter",
    "Combinación de teclas para salir de la pantalla completa del visor embebido.\n"
    "Evita elegir una tecla que necesites enviar dentro de la VM (p. ej. si vas a\n"
    "usar Escape o F11 dentro del sistema invitado, no la uses aquí).":
        "Combinação de teclas para sair da tela cheia do visualizador embutido.\n"
        "Evite escolher uma tecla que você precise enviar dentro da VM (por exemplo, se\n"
        "você for usar Escape ou F11 dentro do sistema convidado, não a use aqui).",
    "Ctrl derecho": "Ctrl direito",
    "Muestra el visor EMBEBIDO (VNC dentro de la app) a pantalla\n"
    "completa en una ventana propia. NO afecta al visor externo:\n"
    "para ese, usa el checkbox 'Externos en pantalla completa'\n"
    "de la fila de estado.\n\n"
    "Pulsa {0} para salir.":
        "Mostra o visualizador EMBUTIDO (VNC dentro do aplicativo) em tela\n"
        "cheia em uma janela própria. NÃO afeta o visualizador externo:\n"
        "para esse, use a caixa 'Externos em tela cheia'\n"
        "da linha de status.\n\n"
        "Pressione {0} para sair.",
    "Modo presentación": "Modo apresentação",
    "\U0001f3ac Salir de presentación": "\U0001f3ac Sair da apresentação",
    "Salir del modo presentación y restaurar la vista normal.\n"
    "También puedes pulsar F11 o Escape.":
        "Sair do modo apresentação e restaurar a visualização normal.\n"
        "Você também pode pressionar F11 ou Escape.",
    "La VM '{0}' no está corriendo. Enciéndela antes de entrar en modo presentación.":
        "A VM '{0}' não está em execução. Inicie-a antes de entrar no modo apresentação.",
    "La Consola Gráfica no está disponible en este sistema (falta el widget VNC embebido).":
        "O Console Gráfico não está disponível neste sistema (falta o widget VNC embutido).",
    "No se pudo comprobar el estado de la VM: {0}":
        "Não foi possível verificar o estado da VM: {0}",
    "No hay ninguna máquina virtual seleccionada.":
        "Nenhuma máquina virtual selecionada.",

    # ================================================================
    # Consola Grafica: notas contextuales de Android (bloque HTML)
    # ================================================================
    "<b>\u2139\ufe0f Notas sobre Android en QEMU/KVM</b>":
        "<b>\u2139\ufe0f Notas sobre Android no QEMU/KVM</b>",

    # ================================================================
    # Consola de Progreso: cabecera de botones
    # ================================================================
    "\U0001fa7a Salud de la VM": "\U0001fa7a Saúde da VM",
    "Comprueba de un vistazo si la VM realmente está corriendo, si el Guest Agent responde y si las carpetas compartidas montaron.":
        "Verifica rapidamente se a VM está realmente em execução, se o Guest Agent responde e se as pastas compartilhadas foram montadas.",
    "\U0001f6a6 Semáforos": "\U0001f6a6 Semáforos",
    "\U0001f9f9 Limpiar procesos huérfanos": "\U0001f9f9 Limpar processos órfãos",
    "Busca procesos QEMU/virtiofsd/swtpm que quedaron colgados de una sesión anterior (por un cierre forzado) y ofrece detenerlos.":
        "Procura processos QEMU/virtiofsd/swtpm que ficaram pendurados de uma sessão anterior (por um fechamento forçado) e oferece detê-los.",
    "Nivel:": "Nível:",
    "Todo": "Tudo",
    "Avisos+": "Avisos+",
    "Errores": "Erros",
    "\U0001f50d Filtrar...": "\U0001f50d Filtrar...",
    "Auto-scroll": "Rolagem automática",
    "\U0001f4c4 Ver log completo": "\U0001f4c4 Ver log completo",
    "Muestra el historial completo guardado en disco para esta VM (launch.log), no solo lo que cabe en esta ventana.":
        "Mostra o histórico completo salvo em disco para esta VM (launch.log), não apenas o que cabe nesta janela.",
    "\U0001f4be Exportar log": "\U0001f4be Exportar log",
    "Guarda el log completo de esta VM en un archivo, útil para pedir ayuda o reportar un problema.":
        "Salva o log completo desta VM em um arquivo, útil para pedir ajuda ou reportar um problema.",
    "Limpiar consola": "Limpar console",
    "Borra los mensajes mostrados aquí (el historial completo en disco no se toca; usa 'Ver log completo').":
        "Apaga as mensagens mostradas aqui (o histórico completo em disco não é alterado; use 'Ver log completo').",
    "Completado.": "Concluído.",

    # ================================================================
    # Consola de Progreso: log y salud VM (diagnostics_mixin)
    # ================================================================
    "Ver log completo": "Ver log completo",
    "Selecciona una VM primero.": "Selecione uma VM primeiro.",
    "Todavía no hay historial guardado para esta VM.":
        "Ainda não há histórico salvo para esta VM.",
    "Exportar log": "Exportar log",
    "Log completo \u2014 {0}": "Log completo \u2014 {0}",
    "No se pudo leer el log: {0}":
        "Não foi possível ler o log: {0}",
    "No se pudo exportar el log: {0}":
        "Não foi possível exportar o log: {0}",
    "Log exportado a:\n{0}": "Log exportado para:\n{0}",
    "Cerrar": "Fechar",
    "Salud de la VM": "Saúde da VM",
    "VM: {0}": "VM: {0}",
    "Carpeta: {0}": "Pasta: {0}",
    "\u25cf QEMU: detenido.": "\u25cf QEMU: parado.",
    "\u25cf QEMU: {0}{1}.": "\u25cf QEMU: {0}{1}.",
    "\u25cf Guest Agent: no aplica (VM apagada).":
        "\u25cf Guest Agent: não se aplica (VM desligada).",
    "\u25cf Guest Agent: responde (v{0}).":
        "\u25cf Guest Agent: responde (v{0}).",
    "\u25cf Guest Agent: sin respuesta ({0}). "
    "Verifica que qemu-guest-agent esté instalado y "
    "corriendo en el guest.":
        "\u25cf Guest Agent: sem resposta ({0}). "
        "Verifique se o qemu-guest-agent está instalado e "
        "em execução no guest.",
    "\u25cf Carpetas compartidas (VirtioFS): ninguna configurada.":
        "\u25cf Pastas compartilhadas (VirtioFS): nenhuma configurada.",
    "\u25cf Carpetas compartidas (VirtioFS):":
        "\u25cf Pastas compartilhadas (VirtioFS):",
    "    - {0}: no aplica (VM apagada).":
        "    - {0}: não se aplica (VM desligada).",
    "    - {0}: virtiofsd activo (PID {1}).":
        "    - {0}: virtiofsd ativo (PID {1}).",
    "    - {0}: NO está activo. Revisa {1} si "
    "esperabas que funcionara.":
        "    - {0}: NÃO está ativo. Verifique {1} se "
        "você esperava que funcionasse.",
    "Limpiar procesos huérfanos": "Limpar processos órfãos",
    "No se encontraron procesos QEMU/virtiofsd colgados de sesiones anteriores.":
        "Nenhum processo QEMU/virtiofsd pendurado de sessões anteriores foi encontrado.",
    "VMs con QEMU corriendo (no se tocan aquí, usa 'Detener VM' si quieres apagarlas):":
        "VMs com QEMU em execução (não são tocadas aqui; use 'Parar VM' se quiser desligá-las):",
    "  - {0} (PID {1})": "  - {0} (PID {1})",
    "Procesos virtiofsd huérfanos encontrados:":
        "Processos virtiofsd órfãos encontrados:",
    "  - {0}: virtiofsd PID {1}": "  - {0}: virtiofsd PID {1}",
    "Se detuvieron {0} proceso(s) huérfano(s).":
        "{0} processo(s) órfão(s) foram encerrados.",
    "\n\nNo se pudieron detener:\n":
        "\n\nNão foi possível encerrar:\n",
    "Nada que limpiar.": "Nada para limpar.",

    # ================================================================
    # Panel Ayuda
    # ================================================================
    "Ayuda de Virtual.Machine": "Ajuda do Virtual.Machine",
    "Guia completa de la consola (VNC / SPICE)":
        "Guia completa do console (VNC / SPICE)",
    "\u2753 Ayuda": "\u2753 Ajuda",
    "Idioma de la interfaz.": "Idioma da interface.",

    # ================================================================
    # console_backend.py: descripciones de modos
    # ================================================================
    "QEMU abre su propia ventana (GTK/SDL). No hace falta visor externo ni cliente; a cambio, la VM no aparece dentro de la app.":
        "O QEMU abre sua própria janela (GTK/SDL). Não é necessário visualizador externo nem cliente; em contrapartida, a VM não aparece dentro do aplicativo.",
    "Híbrida: VNC se muestra dentro de la app (funciona en Wayland y X11) y SPICE se abre en una ventana externa con spicy o remote-viewer. Lo mejor de ambos: embebido para tenerlo a mano, SPICE para rendimiento y clipboard avanzado.":
        "Híbrido: o VNC é mostrado dentro do aplicativo (funciona em Wayland e X11) e o SPICE abre em uma janela externa com spicy ou remote-viewer. O melhor dos dois: embutido para ter à mão, SPICE para desempenho e clipboard avançado.",
    "VNC embebido en la app. Sin dependencias adicionales.":
        "VNC embutido no aplicativo. Sem dependências adicionais.",
    "VNC en ventana externa. Necesitas vncviewer (tigervnc), gvncviewer o remmina instalado.":
        "VNC em janela externa. Você precisa do vncviewer (tigervnc), gvncviewer ou remmina instalado.",
    "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). Requiere sesión X11; en Wayland cae a visor externo.":
        "SPICE embutido no aplicativo (Gtk.SpiceDisplay via XEmbed). Requer sessão X11; no Wayland cai para o visualizador externo.",
    "SPICE embebido solicitado, pero spice-gtk no tiene binding Python. Se usará visor externo como respaldo. Instala python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).":
        "SPICE embutido solicitado, mas o spice-gtk não tem binding Python. Um visualizador externo será usado como alternativa. Instale python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) ou python-gobject + spice-gtk (Arch).",
    "SPICE en ventana externa. Necesitas spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "SPICE em janela externa. Você precisa do spicy (spice-gtk) ou remote-viewer (virt-viewer).",
    "Consola externa": "Console externo",
    "Selecciona primero una máquina virtual.": "Selecione uma máquina virtual primeiro.",
    "No se encontró ningún visor {0} instalado.\n\n":
        "Nenhum visualizador {0} foi encontrado instalado.\n\n",
    "Instala gvncviewer o tigervnc (vncviewer).":
        "Instale o gvncviewer ou tigervnc (vncviewer).",
    "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "Instale o spicy (spice-gtk) ou remote-viewer (virt-viewer).",
    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\nLa VM debe estar corriendo para que QEMU haya elegido un\npuerto.":
        "Ainda não é possível determinar a porta SPICE desta VM.\n\nA VM precisa estar em execução para o QEMU ter escolhido uma\nporta.",
    "El socket {0} todavía no existe.\n\nLa VM debe estar corriendo con ese protocolo seleccionado.":
        "O socket {0} ainda não existe.\n\nA VM precisa estar em execução com esse protocolo selecionado.",

    # ================================================================
    # console_ui_mixin.py: bloque de ayuda grande (VNC / SPICE / Hibrida)
    # ================================================================
    "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden embeber dentro de la app.":
        "<b>Sessão atual: X11.</b> Tanto VNC quanto SPICE podem ser embutidos dentro do aplicativo.",
    "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber dentro de la app. SPICE embebido requeriría X11 (XEmbed no existe en Wayland); si eliges SPICE con modo embebido, caerá automáticamente a visor externo.":
        "<b>Sessão atual: Wayland.</b> Apenas VNC pode ser embutido dentro do aplicativo. SPICE embutido exigiria X11 (XEmbed não existe no Wayland); se você escolher SPICE no modo embutido, cairá automaticamente para o visualizador externo.",
    "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE funcionará cuando estés en X11.":
        "<b>spice-gtk com binding Python: sim.</b> A incorporação do SPICE funcionará quando você estiver em X11.",
    "<b>spice-gtk con binding Python: no.</b> Aunque estés en X11, SPICE no podrá incrustarse; siempre caerá a visor externo. Instálalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>":
        "<b>spice-gtk com binding Python: não.</b> Mesmo em X11, o SPICE não poderá ser incorporado; sempre cairá para o visualizador externo. Instale-o com:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>",
    "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su propia ventana y no expone VNC/SPICE; es el único modo compatible con esos gráficos 3D.":
        "<b>Gráficos compatíveis com VNC / SPICE / Híbrido:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> ou <b>QXL</b>.<br>Com <b>VirGL</b> ou <b>Venus</b> selecionados, o QEMU abre sua própria janela e não expõe VNC/SPICE; é o único modo compatível com esses gráficos 3D.",
    "<b>VNC</b><br><span style='color:#2e7d32;'>\u2713</span> Compatible con cualquier gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>\u2713</span> Se puede embeber dentro de la app, incluso en Wayland.<br><span style='color:#2e7d32;'>\u2713</span> Muchos visores externos disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>\u2713</span> Sin dependencias adicionales en el guest para funcionar.<br><span style='color:#c62828;'>\u2717</span> Sin aceleración 3D ni streaming de video (redibuja por regiones).<br><span style='color:#c62828;'>\u2717</span> Clipboard limitado: solo texto, y el guest necesita <code>vncconfig</code> corriendo.<br><span style='color:#c62828;'>\u2717</span> Sin audio remoto.<br><span style='color:#c62828;'>\u2717</span> Menos fluido en uso intensivo (vídeo, animaciones, 3D).":
        "<b>VNC</b><br><span style='color:#2e7d32;'>\u2713</span> Compatível com qualquer gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>\u2713</span> Pode ser embutido dentro do aplicativo, inclusive no Wayland.<br><span style='color:#2e7d32;'>\u2713</span> Muitos visualizadores externos disponíveis (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>\u2713</span> Sem dependências adicionais no guest para funcionar.<br><span style='color:#c62828;'>\u2717</span> Sem aceleração 3D nem streaming de vídeo (redesenha por regiões).<br><span style='color:#c62828;'>\u2717</span> Clipboard limitado: apenas texto, e o guest precisa do <code>vncconfig</code> em execução.<br><span style='color:#c62828;'>\u2717</span> Sem áudio remoto.<br><span style='color:#c62828;'>\u2717</span> Menos fluido em uso intenso (vídeo, animações, 3D).",
    "<b>SPICE</b><br><span style='color:#2e7d32;'>\u2713</span> Mejor rendimiento y fluidez en local (compresión + streaming de video).<br><span style='color:#2e7d32;'>\u2713</span> Clipboard bidireccional avanzado (con <code>spice-vdagent</code> en el guest).<br><span style='color:#2e7d32;'>\u2713</span> Audio remoto integrado.<br><span style='color:#2e7d32;'>\u2713</span> Varios monitores, redirección USB y carpetas compartidas nativas.<br><span style='color:#c62828;'>\u2717</span> No se puede embeber en Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>\u2717</span> Requiere un visor externo (spicy o remote-viewer) si no se puede embeber.<br><span style='color:#c62828;'>\u2717</span> Para aprovecharlo hay que instalar <code>spice-vdagent</code> en el guest.<br><span style='color:#c62828;'>\u2717</span> Incompatible con VirGL y Venus (usan OpenGL y obligan a la ventana nativa de QEMU).":
        "<b>SPICE</b><br><span style='color:#2e7d32;'>\u2713</span> Melhor desempenho e fluidez local (compressão + streaming de vídeo).<br><span style='color:#2e7d32;'>\u2713</span> Clipboard bidirecional avançado (com <code>spice-vdagent</code> no guest).<br><span style='color:#2e7d32;'>\u2713</span> Áudio remoto integrado.<br><span style='color:#2e7d32;'>\u2713</span> Vários monitores, redirecionamento USB e pastas compartilhadas nativas.<br><span style='color:#c62828;'>\u2717</span> Não pode ser embutido no Wayland (apenas X11 com spice-gtk Python).<br><span style='color:#c62828;'>\u2717</span> Requer um visualizador externo (spicy ou remote-viewer) se não puder ser embutido.<br><span style='color:#c62828;'>\u2717</span> Para aproveitá-lo é preciso instalar <code>spice-vdagent</code> no guest.<br><span style='color:#c62828;'>\u2717</span> Incompatível com VirGL e Venus (usam OpenGL e forçam a janela nativa do QEMU).",
    "<b>Híbrida (VNC embebido + SPICE externo)</b><br><span style='color:#2e7d32;'>\u2713</span> Lo mejor de ambos: VNC siempre visible dentro de la app, SPICE para rendimiento y clipboard.<br><span style='color:#2e7d32;'>\u2713</span> Funciona en cualquier sesión: Wayland o X11.<br><span style='color:#2e7d32;'>\u2713</span> Si spicy falla o lo cierras, el widget VNC sigue funcionando.<br><span style='color:#2e7d32;'>\u2713</span> Útil para ver la VM en dos monitores o para grabar y controlar a la vez.<br><span style='color:#c62828;'>\u2717</span> Consume más recursos: QEMU mantiene dos servidores de display en paralelo.<br><span style='color:#c62828;'>\u2717</span> Verás la misma VM en dos ventanas (dentro de la app y en la de spicy).<br><span style='color:#c62828;'>\u2717</span> La configuración del guest para sacar partido a SPICE (vdagent, drivers) hay que hacerla igual.<br><span style='color:#c62828;'>\u2717</span> Como SPICE, incompatible con VirGL y Venus.":
        "<b>Híbrido (VNC embutido + SPICE externo)</b><br><span style='color:#2e7d32;'>\u2713</span> O melhor dos dois: VNC sempre visível dentro do aplicativo, SPICE para desempenho e clipboard.<br><span style='color:#2e7d32;'>\u2713</span> Funciona em qualquer sessão: Wayland ou X11.<br><span style='color:#2e7d32;'>\u2713</span> Se o spicy falhar ou você fechá-lo, o widget VNC continua funcionando.<br><span style='color:#2e7d32;'>\u2713</span> Útil para ver a VM em dois monitores ou para gravar e controlar ao mesmo tempo.<br><span style='color:#c62828;'>\u2717</span> Consome mais recursos: o QEMU mantém dois servidores de exibição em paralelo.<br><span style='color:#c62828;'>\u2717</span> Você verá a mesma VM em duas janelas (dentro do aplicativo e na do spicy).<br><span style='color:#c62828;'>\u2717</span> A configuração do guest para aproveitar o SPICE (vdagent, drivers) precisa ser feita de qualquer forma.<br><span style='color:#c62828;'>\u2717</span> Assim como o SPICE, incompatível com VirGL e Venus.",

    # ================================================================
    # console_ui_mixin.py: etiquetas dinamicas de estado de graficos
    # ================================================================
    "No detectada": "Não detectada",
    "\u2713 OpenGL": "\u2713 OpenGL",
    "\u2717 OpenGL": "\u2717 OpenGL",
    "\u2713 VirGL": "\u2713 VirGL",
    "\u2713 VirGL instalado": "\u2713 VirGL instalado",
    "\u2717 VirGL": "\u2717 VirGL",
    "\u2713 Vulkan": "\u2713 Vulkan",
    "\u2717 Vulkan": "\u2717 Vulkan",
    "VGA estándar (QEMU -vga std)": "VGA padrão (QEMU -vga std)",
    "VGA de OSX-KVM (VGA virtual)": "VGA do OSX-KVM (VGA virtual)",
    "gestionada por OpenCore/OSX-KVM": "gerenciada pelo OpenCore/OSX-KVM",
    "VirtIO-GPU + VirGL 3D": "VirtIO-GPU + VirGL 3D",
    "OpenGL / VirGL": "OpenGL / VirGL",
    "VirtIO-GPU 2D": "VirtIO-GPU 2D",
    "sin aceleración 3D": "sem aceleração 3D",
    "VGA estándar de QEMU": "VGA padrão do QEMU",
    "<b>Automático \u2192 {0}</b><br>Aceleración: {1}":
        "<b>Automático \u2192 {0}</b><br>Aceleração: {1}",
    "VirtIO-GPU + Venus/Vulkan 3D": "VirtIO-GPU + Venus/Vulkan 3D",
    "Red Hat QXL 2D": "Red Hat QXL 2D",
    "VMware SVGA II": "VMware SVGA II",
    "<b>Usará: {0}</b>": "<b>Usará: {0}</b>",
    "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}":
        "GPU do host: {0}<br>{1}  |  {2}  |  {3}<br>{4}",
    "Host GPU: no se pudo determinar automáticamente.<br>Automático: se seleccionará el modo gráfico compatible disponible.":
        "GPU do host: não foi possível determinar automaticamente.<br>Automático: o modo gráfico compatível disponível será selecionado.",
}
