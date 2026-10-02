# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda1 - Traducciones al portugues (Brasil) - Tanda 1.

Cubre: pestanas principales, titulo de ventana, dialogo de cambio de
idioma, y todo dialogs.py (DiskCreationDialog, MediaPickerDialog,
NatPortForwardDialog, NetworkDeviceDialog, _CreateMediumDialog).

Para compilar:
    ./rebuild_i18n.sh pt_BR

O paso a paso:
    pylupdate6 $(cat .pylupdate6_sources) -ts i18n/vm_pt_BR.ts
    python3 translate_ts.py --lang pt_BR
    lrelease6 i18n/vm_pt_BR.ts
    ./run.sh
"""

TRANSLATIONS = {

    # ================================================================
    # i18n_v1: pestanas principales, titulo y dialogo de reinicio
    # ================================================================
    "Resumen": "Resumo",
    "Configuración VM": "Configuração da VM",
    "Configuración Host": "Configuração do Host",
    "Snapshots": "Snapshots",
    "\U0001f4be Backups": "\U0001f4be Backups",
    "\U0001f4da Medios": "\U0001f4da Mídias",
    "\U0001f5a5\ufe0f Consola Gráfica": "\U0001f5a5\ufe0f Console Gráfico",
    "\U0001f4cb Consola de Progreso": "\U0001f4cb Console de Progresso",
    "\u2753 Ayuda": "\u2753 Ajuda",
    "Administrador QEMU/KVM": "Gerenciador QEMU/KVM",
    "Cambio de idioma": "Mudança de idioma",
    "Se ha cambiado el idioma a {0}.\n\n"
    "Para que TODA la aplicación use el idioma nuevo\n"
    "es necesario reiniciar.\n\n"
    "¿Quieres reiniciar ahora?":
        "O idioma foi alterado para {0}.\n\n"
        "Para que TODO o aplicativo use o novo idioma,\n"
        "é necessário reiniciar.\n\n"
        "Deseja reiniciar agora?",

    # ================================================================
    # Tanda 2a: dialogs.py - DiskCreationDialog
    # ================================================================

    # --- Cabeceras segun tipo de dispositivo ---
    'Configurar dispositivo de almacenamiento': 'Configurar dispositivo de armazenamento',
    '\U0001f4bd Disco SATA': '\U0001f4bd Disco SATA',
    '\u26a1 Disco NVMe': '\u26a1 Disco NVMe',
    '\U0001f4be Disquetera': '\U0001f4be Unidade de disquete',
    '\U0001f4c0 Unidad CD / DVD': '\U0001f4c0 Unidade CD / DVD',
    'Dispositivo de almacenamiento': 'Dispositivo de armazenamento',

    # --- Botones comunes ---
    'Cancelar': 'Cancelar',
    'Aceptar': 'OK',
    'Crear': 'Criar',
    'Elegir': 'Escolher',

    # --- Fuentes del medio (CD/DVD) ---
    'Mantener vacío': 'Manter vazio',
    'Usar ISO/IMG/DMG existente': 'Usar ISO/IMG/DMG existente',
    'System Recovery de macOS (descargar al iniciar)':
        'System Recovery do macOS (baixar ao iniciar)',
    'Descargar instalador de Windows automáticamente':
        'Baixar instalador do Windows automaticamente',
    'Descargar instalador de Linux automáticamente':
        'Baixar instalador do Linux automaticamente',
    'Fuente del medio:': 'Fonte da mídia:',

    # --- Campos de formulario ---
    'Nombre:': 'Nome:',
    'Tamaño:': 'Tamanho:',
    'Tipo:': 'Tipo:',
    'Formato:': 'Formato:',
    'Origen:': 'Origem:',
    'Archivo:': 'Arquivo:',
    'Medio:': 'Mídia:',
    'Ruta del archivo existente…': 'Caminho do arquivo existente…',
    'Selecciona una ISO / IMG / DMG…': 'Selecione uma ISO / IMG / DMG…',
    'Ej.: 40G, 100G, 1T': 'Ex.: 40G, 100G, 1T',

    # --- Botones de exploracion ---
    '\U0001f4c1 Buscar…': '\U0001f4c1 Procurar…',
    '\U0001f4da Biblioteca…': '\U0001f4da Biblioteca…',

    # --- Toggles y modos ---
    'Crear nuevo': 'Criar novo',
    'Usar archivo existente': 'Usar arquivo existente',
    'Expandible (dinámico)': 'Expansível (dinâmico)',
    'Fijo (preasignado)': 'Fixo (pré-alocado)',

    # --- Tooltips ---
    'Elegir un medio de la biblioteca central (MediaLibrary/).\n'
    'Se reutiliza entre todas las VMs.':
        'Escolher uma mídia da biblioteca central (MediaLibrary/).\n'
        'Ela é reutilizada entre todas as VMs.',
    'Elegir un archivo ya registrado en la Biblioteca de Medios.\n'
    'Se filtra por el tipo del dispositivo.':
        'Escolher um arquivo já registrado na Biblioteca de Mídias.\n'
        'Ele é filtrado pelo tipo do dispositivo.',

    # --- Hints bajo el formulario ---
    'Disquete RAW. Selecciona 720 KB, 1.44 MB o 2.88 MB.':
        'Disquete RAW. Selecione 720 KB, 1,44 MB ou 2,88 MB.',
    'Expandible: crece según se utiliza. Fijo: reserva el espacio en el host. '
    'También puedes adjuntar un disco existente.':
        'Expansível: cresce conforme é usado. Fixo: reserva o espaço no host. '
        'Você também pode anexar um disco existente.',
    'La unidad se crea vacía. Podrás insertar un ISO después, incluso con la VM encendida.':
        'A unidade é criada vazia. Você poderá inserir uma ISO depois, mesmo com a VM ligada.',
    'Selecciona un ISO/IMG/DMG que ya exista en tu equipo.':
        'Selecione uma ISO/IMG/DMG que já exista na sua máquina.',
    'Para macOS se descargará System Recovery automáticamente al iniciar la VM '
    'y se asociará a esta unidad óptica.':
        'Para macOS, o System Recovery será baixado automaticamente ao iniciar a VM '
        'e será associado a esta unidade óptica.',
    'El instalador se descargará automáticamente al iniciar la VM, mostrando una '
    'barra de porcentaje, y quedará conectado a esta unidad CD/DVD.':
        'O instalador será baixado automaticamente ao iniciar a VM, mostrando uma '
        'barra de porcentagem, e ficará conectado a esta unidade CD/DVD.',

    # --- Filtros de QFileDialog ---
    'Imágenes de disquete (*.img *.raw);;Todos los archivos (*)':
        'Imagens de disquete (*.img *.raw);;Todos os arquivos (*)',
    'Discos virtuales (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos los archivos (*)':
        'Discos virtuais (*.qcow2 *.qcow *.raw *.img *.vdi *.vmdk *.vhd *.vhdx);;Todos os arquivos (*)',
    'Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)':
        'Imagens (*.iso *.img *.dmg);;Todos os arquivos (*)',
    'Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)':
        'Imagens de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos (*)',

    # --- Titulos de QFileDialog ---
    'Seleccionar archivo existente': 'Selecionar arquivo existente',
    'Seleccionar medio óptico': 'Selecionar mídia óptica',
    'Anadir a la biblioteca': 'Adicionar à biblioteca',

    # --- Avisos y errores de validacion ---
    'Medio inválido': 'Mídia inválida',
    'Selecciona un ISO/IMG/DMG válido.': 'Selecione uma ISO/IMG/DMG válida.',
    'Archivo inválido': 'Arquivo inválido',
    'Selecciona un archivo existente válido.': 'Selecione um arquivo existente válido.',
    'Nombre requerido': 'Nome obrigatório',
    'Indica un nombre para el dispositivo.': 'Informe um nome para o dispositivo.',
    'Escribe un nombre para el medio.': 'Digite um nome para a mídia.',
    'Tamaño inválido': 'Tamanho inválido',
    'Usa un tamaño como 40G, 512M o 1T.': 'Use um tamanho como 40G, 512M ou 1T.',
    'Nombre inválido': 'Nome inválido',
    'El nombre no puede contener \\ / : * ? " < > |':
        'O nome não pode conter \\ / : * ? " < > |',
    'CD/DVD': 'CD/DVD',

    # ================================================================
    # dialogs.py - MediaPickerDialog
    # ================================================================
    'Elegir medio de la biblioteca': 'Escolher mídia da biblioteca',
    'Elige una ISO/IMG/DMG de la biblioteca central.<br>'
    'La biblioteca vive en <code>MediaLibrary/</code>, al mismo nivel que '
    '<code>VirtualMachines/</code>. Se reutiliza entre todas las VMs.':
        'Escolha uma ISO/IMG/DMG da biblioteca central.<br>'
        'A biblioteca fica em <code>MediaLibrary/</code>, no mesmo nível que '
        '<code>VirtualMachines/</code>. Ela é reutilizada entre todas as VMs.',

    'Buscar...': 'Buscar...',
    'SO:': 'SO:',
    'Todos': 'Todos',
    'Disco duro': 'Disco rígido',
    'Disquete': 'Disquete',

    'Nombre': 'Nome',
    'Tipo': 'Tipo',
    'SO': 'SO',
    'Version': 'Versão',
    'Arq.': 'Arq.',
    'Tamano': 'Tamanho',
    'Usada por': 'Usada por',
    'Ruta': 'Caminho',

    'Anadir archivo a la biblioteca...': 'Adicionar arquivo à biblioteca...',
    'Registrar una ISO nueva sin salir de este dialogo.':
        'Registrar uma nova ISO sem sair deste diálogo.',
    'Crear disco...': 'Criar disco...',
    "Crear un disco virtual (QCOW2 / RAW) o un disquete (IMG)\n"
    "directamente en la biblioteca. Equivale a 'qemu-img create'\n"
    "sobre MediaLibrary/<nombre>.<ext>.":
        "Criar um disco virtual (QCOW2 / RAW) ou um disquete (IMG)\n"
        "diretamente na biblioteca. Equivale a 'qemu-img create'\n"
        "sobre MediaLibrary/<nome>.<ext>.",
    'Abrir carpeta': 'Abrir pasta',
    'Abre MediaLibrary/ en el explorador del sistema.':
        'Abre MediaLibrary/ no gerenciador de arquivos do sistema.',

    '{0}   (huerfano)': '{0}   (órfão)',
    '{0}, {1} (+{2})': '{0}, {1} (+{2})',
    '(sin archivo)': '(sem arquivo)',
    'No la usa ninguna VM.': 'Nenhuma VM a utiliza.',

    'Archivo no disponible': 'Arquivo não disponível',
    'El archivo de esta entrada ya no existe en el disco.\n\n'
    'Ruta esperada:\n{0}':
        'O arquivo desta entrada não existe mais no disco.\n\n'
        'Caminho esperado:\n{0}',
    'Biblioteca no disponible': 'Biblioteca não disponível',
    'La biblioteca de medios no está disponible.':
        'A biblioteca de mídias não está disponível.',
    'Ya existe': 'Já existe',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n'
    'Elige otro nombre o bórralo desde la pestaña Medios.':
        'Já existe um arquivo com esse nome na biblioteca:\n\n{0}\n\n'
        'Escolha outro nome ou exclua-o pela aba Mídias.',
    'Crear medio': 'Criar mídia',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils\n"
    "en Debian/Ubuntu, qemu-img en Arch) para crear discos.":
        "'qemu-img' não encontrado. Instale-o (pacote qemu-utils\n"
        "no Debian/Ubuntu, qemu-img no Arch) para criar discos.",
    'No se pudo crear el medio.\n\n{0}':
        'Não foi possível criar a mídia.\n\n{0}',
    'Creado con qemu-img create. Tamaño: {0}.':
        'Criado com qemu-img create. Tamanho: {0}.',
    'El archivo se creó correctamente pero no se pudo\n'
    'registrar en la biblioteca:\n\n{0}':
        'O arquivo foi criado corretamente, mas não foi possível\n'
        'registrá-lo na biblioteca:\n\n{0}',
    'Medio creado': 'Mídia criada',
    'Se creó el medio correctamente.\n\n'
    'Archivo: {0}\n'
    'Tamaño: {1}\n'
    'Formato: {2}':
        'A mídia foi criada corretamente.\n\n'
        'Arquivo: {0}\n'
        'Tamanho: {1}\n'
        'Formato: {2}',

    # ================================================================
    # dialogs.py - NatPortForwardDialog
    # ================================================================
    'Reglas de reenvío de puertos NAT': 'Regras de encaminhamento de portas NAT',
    'Redirige puertos del host al guest a través del NAT de QEMU '
    '(<code>-netdev user,hostfwd=...</code>). Cada regla conecta '
    '<b>localhost:puerto_host</b> del anfitrión con <b>puerto_guest</b> '
    'dentro del sistema invitado.<br><br>Ejemplo: host 2222 → guest 22 '
    'reenvía SSH; luego entra con '
    '<code>ssh -p 2222 usuario@localhost</code>.':
        "Redireciona portas do host para o guest através do NAT do QEMU "
        "(<code>-netdev user,hostfwd=...</code>). Cada regra conecta "
        "<b>localhost:porta_host</b> do host com <b>porta_guest</b> "
        "dentro do sistema convidado.<br><br>Exemplo: host 2222 → guest 22 "
        "encaminha SSH; depois entre com "
        "<code>ssh -p 2222 usuario@localhost</code>.",
    'Puerto host:': 'Porta host:',
    'Puerto en el host (donde tú te conectas).':
        'Porta no host (onde você se conecta).',
    'Puerto guest:': 'Porta guest:',
    'Puerto dentro de la VM (a donde se reenvía).':
        'Porta dentro da VM (para onde o tráfego é encaminhado).',
    'Protocolo:': 'Protocolo:',
    '\u2795 Añadir regla': '\u2795 Adicionar regra',
    'Puerto host': 'Porta host',
    'Puerto guest': 'Porta guest',
    'Protocolo': 'Protocolo',
    '\U0001f5d1 Quitar seleccionada': '\U0001f5d1 Remover selecionada',
    'Regla duplicada': 'Regra duplicada',
    'Ya existe una regla para el puerto host {0} ({1}).\n\n'
    'Elige otro puerto host o cambia el protocolo.':
        'Já existe uma regra para a porta host {0} ({1}).\n\n'
        'Escolha outra porta host ou altere o protocolo.',

    # ================================================================
    # dialogs.py - NetworkDeviceDialog
    # ================================================================
    'Adaptador de red virtual': 'Adaptador de rede virtual',
    'Red 1': 'Rede 1',
    'NAT / Internet': 'NAT / Internet',
    'Bridge existente': 'Bridge existente',
    'Opcional: 52:54:00:xx:xx:xx': 'Opcional: 52:54:00:xx:xx:xx',
    'Modelo:': 'Modelo:',
    'Backend:': 'Backend:',
    'Bridge / TAP:': 'Bridge / TAP:',
    'MAC:': 'MAC:',
    '\U0001f500 Reglas NAT…': '\U0001f500 Regras NAT…',
    '\U0001f500 Reglas NAT… ({0})': '\U0001f500 Regras NAT… ({0})',
    'Redirigir puertos del host al guest a través del NAT de QEMU\n'
    '(hostfwd). Solo aplica cuando el backend es NAT.':
        "Redirecionar portas do host para o guest através do NAT do QEMU\n"
        "(hostfwd). Aplica-se apenas quando o backend é NAT.",
    'Red': 'Rede',

    # ================================================================
    # dialogs.py - _CreateMediumDialog
    # ================================================================
    'Crear medio nuevo': 'Criar nova mídia',
    'Ej: disco_ubuntu_datos': 'Ex.: disco_ubuntu_dados',
    'Disco duro QCOW2 (recomendado)': 'Disco rígido QCOW2 (recomendado)',
    'Disco duro RAW': 'Disco rígido RAW',
    'Disquete IMG (RAW)': 'Disquete IMG (RAW)',
    "Disquete formateado como RAW. Se registra como tipo 'Disquete' en "
    "la biblioteca. Tamaños típicos: 720 KB, 1.44 MB, 2.88 MB.":
        "Disquete formatado como RAW. É registrado como tipo 'Disquete' na "
        "biblioteca. Tamanhos típicos: 720 KB, 1,44 MB, 2,88 MB.",
    'Disco virtual expandible (recomendado). El archivo en el host '
    'crece solo según se usa en el guest.':
        'Disco virtual expansível (recomendado). O arquivo no host '
        'cresce apenas conforme o uso no guest.',
    'Disco RAW (imagen plana). Ocupa el tamaño completo en el host '
    'desde el momento de su creación.':
        'Disco RAW (imagem plana). Ocupa o tamanho completo no host '
        'desde o momento da criação.',
}
