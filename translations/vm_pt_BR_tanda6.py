# -*- coding: utf-8 -*-
"""Traducciones pt_BR - tanda6 (media_library_host_mount_v1"
 + media_library_create_disk_v1 + dialogos VMDK/VDI/VHD/VHDX).
Marcador: tanda6_media_library_v1."""

TRANSLATIONS = {
    '➕ Crear disco':
        '➕ Criar disco',
    "Crea un disco virtual nuevo en la biblioteca con\n'qemu-img create'.\n\nFormatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ny disquete (IMG). El archivo se guarda en MediaLibrary/\ny se registra automáticamente en el índice.":
        "Cria um novo disco virtual na biblioteca com\n'qemu-img create'.\n\nFormatos suportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\ne disquete (IMG). O arquivo é salvo em MediaLibrary/\ne registrado automaticamente no índice.",
    '🔌 Montar en host':
        '🔌 Montar no host',
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.\n\nSe usa guestmount (FUSE, sin root) si está disponible,\no qemu-nbd (con pkexec) como alternativa.\n\nRequiere que ninguna VM que lo use esté encendida:\nQEMU mantiene un bloqueo de escritura sobre el archivo.':
        'Monta este disco virtual no sistema anfitrião para\ninspecionar ou copiar seu conteúdo sem iniciar a VM.\n\nguestmount (FUSE, sem root) é usado se estiver disponível,\nou qemu-nbd (com pkexec) como alternativa.\n\nExige que nenhuma VM que o use esteja ligada:\nQEMU mantém um bloqueio de escrita sobre o arquivo.',
    '⏏ Desmontar del host':
        '⏏ Desmontar do host',
    "Desmonta del sistema anfitrión el disco que se montó\npreviamente con 'Montar en host'.":
        "Desmonta do sistema anfitrião o disco que foi montado\npreviamente com 'Montar no host'.",
    'montado (rw)':
        'montado (rw)',
    'montado (ro)':
        'montado (ro)',
    'Herramientas de montaje':
        'Ferramentas de montagem',
    "No se encontró guestmount ni qemu-nbd en el sistema.\n\nInstala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\ncomo alternativa) con el gestor de paquetes de tu\ndistribución para poder montar discos virtuales.":
        "Nem guestmount nem qemu-nbd foram encontrados no sistema.\n\nInstale 'libguestfs' e 'guestfs-tools' (ou 'qemu-nbd'\ncomo alternativa) com o gerenciador de pacotes da sua\ndistribuição para poder montar discos virtuais.",
    "Faltan las herramientas de montaje y no se encontró\n'pkexec' para pedir permisos de administrador.\n\nEjecuta a mano:\n\n  sudo {0} install {1}":
        "Faltam as ferramentas de montagem e 'pkexec' não foi\nencontrado para solicitar permissões de administrador.\n\nExecute manualmente:\n\n  sudo {0} install {1}",
    'Se necesitan herramientas adicionales para montar discos\nen el host.\n\n  • guestmount (libguestfs) es lo ideal: sin root, detecta\n    particiones y sistemas de archivos automáticamente.\n  • qemu-nbd es la alternativa si no hay libguestfs.\n\n¿Quieres instalar las herramientas ahora? Se pedirá la\ncontraseña de administrador.\n\nComando:\n  {0}':
        'Ferramentas adicionais são necessárias para montar discos\nno host.\n\n  • guestmount (libguestfs) é o ideal: sem root, detecta\n    partições e sistemas de arquivos automaticamente.\n  • qemu-nbd é a alternativa se libguestfs não estiver presente.\n\nDeseja instalar as ferramentas agora? Será solicitada a\nsenha do administrador.\n\nComando:\n  {0}',
    'No se pudo ejecutar el comando de instalación.\n\n{0}':
        'Não foi possível executar o comando de instalação.\n\n{0}',
    'La instalación falló.\n\n{0}':
        'A instalação falhou.\n\n{0}',
    'Instalación completada.':
        'Instalação concluída.',
    'Montajes previos detectados':
        'Montagens anteriores detectadas',
    'Se encontraron {0} disco(s) montados en el sistema de\nuna sesión anterior de la aplicación:\n\n{1}\n\n¿Quieres desmontarlos ahora?':
        'Foram encontrados {0} disco(s) montados no sistema de\numa sessão anterior da aplicação:\n\n{1}\n\nDeseja desmontá-los agora?',
    'Montar en el host':
        'Montar no host',
    'Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>El disco debe estar apagado: ninguna VM que lo use puede\nestar encendida, porque QEMU mantiene un bloqueo de escritura\nsobre el archivo.':
        '<b>{0}</b> será montado no sistema anfitrião.<br><br>O disco deve estar desligado: nenhuma VM que o use pode\nestar ligada, porque QEMU mantém um bloqueio de escrita\nsobre o arquivo.',
    'Permitir escritura (montar en modo read-write)':
        'Permitir escrita (montar em modo leitura-escrita)',
    '⚠ Con read-write, escribir en el disco puede corromper el\nsistema de archivos si después se arranca la VM sin\ndesmontarlo. Para inspeccionar o copiar, deja read-only.\n\nLos archivos que crees desde el host se atribuirán a tu\nusuario del guest (uid/gid {0}:{1}) cuando el sistema de\narchivos lo permita; si no, aparecerán como root.':
        '⚠ Em leitura-escrita, escrever no disco pode corromper o\nsistema de arquivos se a VM for iniciada depois sem\ndesmontá-lo. Para inspecionar ou copiar, deixe em somente leitura.\n\nOs arquivos que você criar a partir do host serão atribuídos\nao seu usuário no convidado (uid/gid {0}:{1}) quando o sistema\nde arquivos permitir; caso contrário, aparecerão como root.',
    'Montar':
        'Montar',
    'Selecciona un disco virtual para montarlo en el host.':
        'Selecione um disco virtual para montá-lo no host.',
    'Selecciona un disco previamente montado para desmontarlo.':
        'Selecione um disco previamente montado para desmontá-lo.',
    'Solo se pueden montar discos virtuales\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).':
        'Somente discos virtuais podem ser montados\n(QCOW2, RAW, VMDK, VDI, VHD, VHDX).',
    "Este disco ya está montado. Usa '⏏ Desmontar del host'\npara liberarlo.":
        "Este disco já está montado. Use '⏏ Desmontar do host'\npara liberá-lo.",
    "La VM '{0}' está usando este disco y está encendida.\nApágala para poder montarlo en el host.":
        "A VM '{0}' está usando este disco e está ligada.\nDesligue-a para poder montá-lo no host.",
    'Monta este disco virtual en el sistema anfitrión para\ninspeccionar o copiar su contenido sin arrancar la VM.':
        'Monta este disco virtual no sistema anfitrião para\ninspecionar ou copiar seu conteúdo sem iniciar a VM.',
    'Desmontar de {0}':
        'Desmontar de {0}',
    'Este disco no está montado en el host.':
        'Este disco não está montado no host.',
    'Montar en host':
        'Montar no host',
    'Error inesperado al montar el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erro inesperado ao montar o disco.\n\nVocê pode ver os detalhes no Console de Progresso.\n\n{0}',
    'Este disco ya está montado.':
        'Este disco já está montado.',
    "La VM '{0}' está usando este disco y está encendida.\n\nApágala antes de montar el disco en el host: QEMU\nmantiene un bloqueo de escritura sobre el archivo\ny el montaje fallaría.":
        "A VM '{0}' está usando este disco e está ligada.\n\nDesligue-a antes de montar o disco no host: QEMU\nmantém um bloqueio de escrita sobre o arquivo\ne a montagem falharia.",
    'Las herramientas de montaje siguen sin estar\ndisponibles después de la instalación.':
        'As ferramentas de montagem continuam indisponíveis\napós a instalação.',
    'No se pudo crear el punto de montaje.\n\n{0}':
        'Não foi possível criar o ponto de montagem.\n\n{0}',
    'Aviso: el sistema de archivos del guest no acepta mapeo de usuario; los archivos que crees desde el host aparecerán como root en el guest. Para trabajar sin problemas de permisos, escribe desde el guest en lugar del host.':
        'Aviso: o sistema de arquivos do convidado não aceita mapeamento de usuário; os arquivos que você criar a partir do host aparecerão como root no convidado. Para trabalhar sem problemas de permissão, escreva a partir do convidado em vez do host.',
    'Disco montado':
        'Disco montado',
    "'{0}' montado correctamente.\n\nPunto de montaje: {1}\nModo: {2}{3}":
        "'{0}' montado com sucesso.\n\nPonto de montagem: {1}\nModo: {2}{3}",
    'read-only':
        'somente leitura',
    'read-write':
        'leitura-escrita',
    'No se pudo montar el disco.\n\n{0}':
        'Não foi possível montar o disco.\n\n{0}',
    "Montando '{0}'":
        "Montando '{0}'",
    'Preparando el punto de montaje en el host…':
        'Preparando o ponto de montagem no host…',
    'Desmontar del host':
        'Desmontar do host',
    'Error inesperado al desmontar.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erro inesperado ao desmontar.\n\nVocê pode ver os detalhes no Console de Progresso.\n\n{0}',
    "¿Desmontar '{0}' de {1}?":
        "Desmontar '{0}' de {1}?",
    "'{0}' desmontado correctamente.":
        "'{0}' desmontado com sucesso.",
    'No se pudo desmontar.\n\n{0}':
        'Não foi possível desmontar.\n\n{0}',
    "Desmontando '{0}'":
        "Desmontando '{0}'",
    'Liberando el punto de montaje…':
        'Liberando o ponto de montagem…',
    'Crear disco':
        'Criar disco',
    'Error inesperado al crear el disco.\n\nPuedes ver el detalle en la Consola de Progreso.\n\n{0}':
        'Erro inesperado ao criar o disco.\n\nVocê pode ver os detalhes no Console de Progresso.\n\n{0}',
    'La biblioteca no está disponible.':
        'A biblioteca não está disponível.',
    'Ya existe un archivo con ese nombre en la biblioteca:\n\n{0}\n\n¿Sobrescribir? (se perderá el contenido anterior)':
        'Já existe um arquivo com esse nome na biblioteca:\n\n{0}\n\nSobrescrever? (o conteúdo anterior será perdido)',
    "No se encontró 'qemu-img'. Instálalo (paquete qemu-utils / qemu-img).":
        "'qemu-img' não foi encontrado. Instale-o (pacote qemu-utils / qemu-img).",
    'Disco creado':
        'Disco criado',
    'Se creó el disco correctamente.\n\nArchivo: {0}\nTamaño: {1}\nFormato: {2}':
        'Disco criado com sucesso.\n\nArquivo: {0}\nTamanho: {1}\nFormato: {2}',
    'No se pudo crear el disco.\n\n{0}':
        'Não foi possível criar o disco.\n\n{0}',
    "Creando '{0}'":
        "Criando '{0}'",
    'Ejecutando qemu-img create…':
        'Executando qemu-img create…',
    'Disco duro VMDK (VirtualBox / VMware)':
        'Disco rígido VMDK (VirtualBox / VMware)',
    'Disco duro VDI (VirtualBox nativo)':
        'Disco rígido VDI (VirtualBox nativo)',
    'Disco duro VHD (Hyper-V antiguo)':
        'Disco rígido VHD (Hyper-V antigo)',
    'Disco duro VHDX (Hyper-V moderno)':
        'Disco rígido VHDX (Hyper-V moderno)',
    'Preasignación:':
        'Pré-alocação:',
    'Expandible: el archivo crece solo según se usa (recomendado).\nFijo: reserva todo el espacio en disco desde el momento de\nsu creación. Tarda más y ocupa más, pero el rendimiento de\nescritura es más predecible.':
        'Expansível: o arquivo cresce conforme é usado (recomendado).\nFixo: reserva todo o espaço em disco no momento da\ncriação. Leva mais tempo e ocupa mais, mas o desempenho\nde escrita é mais previsível.',
    'Expandible: preallocation=off (recomendado).\nFijo: preallocation=full. Reserva todo el espacio\nen el host desde el momento de su creación.':
        'Expansível: preallocation=off (recomendado).\nFixo: preallocation=full. Reserva todo o espaço\nno host no momento da criação.',
    'Expandible: VDI dinámico (recomendado).\nFijo: static=on. Reserva todo el espacio en el host.':
        'Expansível: VDI dinâmico (recomendado).\nFixo: static=on. Reserva todo o espaço no host.',
    'Expandible: VHD dynamic (recomendado).\nFijo: subformat=fixed. Reserva todo el espacio.':
        'Expansível: VHD dinâmico (recomendado).\nFixo: subformat=fixed. Reserva todo o espaço.',
    'Formato VMDK monolithicSparse (compatible con VirtualBox y VMware). El archivo crece según se usa; las snapshots internas de QEMU no aplican.':
        'Formato VMDK monolithicSparse (compatível com VirtualBox e VMware). O arquivo cresce conforme é usado; os snapshots internos do QEMU não se aplicam.',
    'Formato VDI nativo de VirtualBox. El archivo crece según se usa.':
        'Formato VDI nativo do VirtualBox. O arquivo cresce conforme é usado.',
    "Formato VHD (Hyper-V hasta Windows 2008 R2). Compatible con la mayoría de hipervisores. QEMU lo llama internamente 'vpc'.":
        "Formato VHD (Hyper-V até Windows 2008 R2). Compatível com a maioria dos hipervisores. O QEMU o chama internamente de 'vpc'.",
    'Formato VHDX (Hyper-V moderno, desde Windows 2012). Soporta discos de hasta 64 TB y bloques de 4 KB.':
        'Formato VHDX (Hyper-V moderno, desde Windows 2012). Suporta discos de até 64 TB e blocos de 4 KB.',
    'Disco virtual expandible.':
        'Disco virtual expansível.',
}
