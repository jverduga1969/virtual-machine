# -*- coding: utf-8 -*-
"""vm_pt_BR_tanda3c - Traducciones al portugues (Brasil) - Tanda 3c.

Cubre la pestana Biblioteca de Medios completa:
  - Cabecera, filtros (SO / Arq. / Formato / Tipo / Origen).
  - Botones superiores (Anadir archivo(s), Escanear carpeta, Escanear VMs).
  - Tabla de columnas.
  - Panel inferior (Notas, Tags, Color + paleta).
  - Botonera inferior (Verificar / SHA256 / Editar / Eliminar / Abrir carpeta /
    Agrandar / Compactar).
  - Handlers de media_library_mixin: add, scan_vms, scan_library, enlarge,
    compact, verify, compute_sha256, edit_metadata, delete, open_folder.
"""

TRANSLATIONS = {

    # ================================================================
    # Cabecera HTML + descripcion
    # ================================================================
    "<b>Biblioteca de Medios</b><br>"
    "<span style='color:#666;font-size:11px;'>"
    "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
    "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
    "nivel que <code>VirtualMachines/</code>) y se reutilizan "
    "entre maquinas."
    "</span>":
        "<b>Biblioteca de Mídias</b><br>"
        "<span style='color:#666;font-size:11px;'>"
        "Todas as ISOs / IMGs / DMGs que você usa com suas VMs, em "
        "um só lugar. Ficam em <code>MediaLibrary/</code> (no mesmo "
        "nível que <code>VirtualMachines/</code>) e são reutilizadas "
        "entre máquinas."
        "</span>",

    # ================================================================
    # Filtros
    # ================================================================
    "Buscar por nombre, distro, tag...":
        "Buscar por nome, distro, tag...",
    "SO:": "SO:",
    "Todos": "Todos",
    "Otros": "Outros",
    "Arq.:": "Arq.:",
    "Todas": "Todas",
    "Universal": "Universal",
    "Sin especificar": "Não especificado",
    "Formato:": "Formato:",
    "Tipo:": "Tipo:",
    "Disco duro": "Disco rígido",
    "ISO": "ISO",
    "Disquete": "Disquete",
    "Otro": "Outro",
    "Origen:": "Origem:",
    "Manuales": "Manuais",
    "De VMs": "De VMs",
    "Huerfanas de VM": "Órfãos de VM",

    # ================================================================
    # Botones superiores
    # ================================================================
    "Anadir archivo(s)": "Adicionar arquivo(s)",
    "Escanear carpeta": "Escanear pasta",
    "Busca archivos de medios dentro de MediaLibrary/ que aun no "
    "esten registrados, y detecta entradas huerfanas (archivo "
    "desaparecido del disco).":
        "Busca arquivos de mídia dentro de MediaLibrary/ que ainda não "
        "estejam registrados e detecta entradas órfãs (arquivo "
        "desaparecido do disco).",
    "\U0001f50e Escanear VMs": "\U0001f50e Escanear VMs",
    "Recorre todas las VMs en VirtualMachines/ y registra sus "
    "discos duros, ISOs y disquetes en la biblioteca.\n\n"
    "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
    "todas las VMs en la columna 'Usada por'. Las entradas que ya "
    "no usa ninguna VM se marcan como huerfanas pero no se borran.":
        "Percorre todas as VMs em VirtualMachines/ e registra seus "
        "discos rígidos, ISOs e disquetes na biblioteca.\n\n"
        "A mesma ISO usada por várias VMs aparece UMA ÚNICA VEZ, com "
        "todas as VMs na coluna 'Usada por'. As entradas que já "
        "não são usadas por nenhuma VM são marcadas como órfãs, mas não são excluídas.",

    # ================================================================
    # Tabla de columnas
    # ================================================================
    "SO": "SO",
    "Version": "Versão",
    "Arq.": "Arq.",
    "Tamaño real": "Tamanho real",
    "Usada por": "Usada por",
    "Ultimo uso": "Último uso",
    "Ruta": "Caminho",
    "Estado": "Estado",
    "Tamano": "Tamanho",

    # ================================================================
    # Panel inferior (Notas / Tags / Color)
    # ================================================================
    "<b>Notas:</b>": "<b>Notas:</b>",
    "Notas libres sobre esta entrada (uso previsto, si dio "
    "problemas, driver necesario, etc.)":
        "Notas livres sobre esta entrada (uso pretendido, se deu "
        "problemas, driver necessário, etc.)",
    "<b>Tags:</b>": "<b>Tags:</b>",
    "Separados por coma (ej.: probado, servidor, rapiro)":
        "Separadas por vírgula (ex.: testado, servidor, rápido)",
    "<b>Color:</b>": "<b>Cor:</b>",
    "(Sin color)": "(Sem cor)",
    "Rojo": "Vermelho",
    "Naranja": "Laranja",
    "Ambar": "Âmbar",
    "Verde": "Verde",
    "Verde azul": "Verde-azulado",
    "Azul": "Azul",
    "Indigo": "Índigo",
    "Violeta": "Violeta",
    "Rosa": "Rosa",
    "Gris": "Cinza",

    # ================================================================
    # Botonera inferior
    # ================================================================
    "Verificar": "Verificar",
    "Calcular SHA256": "Calcular SHA256",
    "Editar": "Editar",
    "Eliminar": "Excluir",
    "Abrir carpeta": "Abrir pasta",
    "Agrandar": "Ampliar",
    "Compactar": "Compactar",

    # ================================================================
    # Cabecera informativa + fila de resumen
    # ================================================================
    "Biblioteca de Medios": "Biblioteca de Mídias",
    "Biblioteca no disponible.": "Biblioteca não disponível.",
    "{0} entrada(s) mostradas de {1} | Tamano total: {2}":
        "{0} entrada(s) mostrada(s) de {1} | Tamanho total: {2}",
    "huerfano": "órfão",
    "verificado?": "verificado?",

    # ================================================================
    # Handlers: alta de archivos
    # ================================================================
    "La biblioteca no esta disponible.":
        "A biblioteca não está disponível.",
    "Anadir archivos a la biblioteca":
        "Adicionar arquivos à biblioteca",
    "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos los archivos (*)":
        "Imagens de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;Todos os arquivos (*)",

    # ================================================================
    # Handlers: escanear VMs
    # ================================================================
    "Escanear VMs": "Escanear VMs",
    "No se pudieron escanear las VMs.\n\n{0}":
        "Não foi possível escanear as VMs.\n\n{0}",
    "Archivos unicos encontrados en VMs: {0}.":
        "Arquivos únicos encontrados em VMs: {0}.",
    "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca.":
        "- {0} mídia(s) nova(s) adicionada(s) à biblioteca.",
    "- {0} entrada(s) actualizada(s) con la lista de VMs que las usan.":
        "- {0} entrada(s) atualizada(s) com a lista de VMs que as usam.",
    "- {0} entrada(s) ya no las usa ninguna VM (siguen visibles; filtro Origen = 'Huerfanas de VM').":
        "- {0} entrada(s) não são mais usadas por nenhuma VM (continuam visíveis; filtro Origem = 'Órfãos de VM').",
    "Sin cambios: la biblioteca ya estaba al dia.":
        "Sem alterações: a biblioteca já estava atualizada.",

    # ================================================================
    # Handlers: escanear carpeta
    # ================================================================
    "Escanear": "Escanear",
    "No se pudo escanear.\n\n{0}":
        "Não foi possível escanear.\n\n{0}",
    "No hay archivos nuevos ni entradas huerfanas.":
        "Não há arquivos novos nem entradas órfãs.",
    "{0} archivo(s) nuevos encontrados:":
        "{0} arquivo(s) novo(s) encontrado(s):",
    "  ... y {0} mas": "  ... e mais {0}",
    "{0} entrada(s) huerfanas (archivo ya no existe):":
        "{0} entrada(s) órfã(s) (arquivo não existe mais):",
    "Anadir los archivos nuevos a la biblioteca?":
        "Adicionar os novos arquivos à biblioteca?",

    # ================================================================
    # Handlers: agrandar disco
    # ================================================================
    "Selecciona una entrada primero.":
        "Selecione uma entrada primeiro.",
    "Solo se pueden agrandar discos duros (QCOW2/RAW).":
        "Apenas discos rígidos (QCOW2/RAW) podem ser ampliados.",
    "El archivo no existe:\n{0}":
        "O arquivo não existe:\n{0}",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de agrandarlo.":
        "Este disco é usado pela VM '{0}', que está ligada.\n\nDesligue-a antes de ampliá-lo.",
    "\u2197 Agrandar disco": "\u2197 Ampliar disco",
    "Tama\u00f1o actual:": "Tamanho atual:",
    "Nuevo tama\u00f1o:": "Novo tamanho:",
    "Ejemplo: 120G (solo crecer)": "Exemplo: 120G (apenas crescer)",
    "El disco solo puede CRECER. Agrandar el archivo NO agranda\n"
    "la partici\u00f3n dentro del guest: hay que ampliarla tambi\u00e9n desde\n"
    "el sistema invitado para aprovechar el nuevo espacio.":
        "O disco só pode CRESCER. Ampliar o arquivo NÃO amplia\n"
        "a partição dentro do guest: é preciso ampliá-la também pelo\n"
        "sistema convidado para aproveitar o novo espaço.",
    "Tama\u00f1o inv\u00e1lido": "Tamanho inválido",
    "'{0}' no es un tama\u00f1o v\u00e1lido.": "'{0}' não é um tamanho válido.",
    "No se puede encoger": "Não é possível encolher",
    "Actual: {0}, indicado {1}.\n\nEl valor se ha restaurado al tama\u00f1o actual.":
        "Atual: {0}, informado {1}.\n\nO valor foi restaurado para o tamanho atual.",
    "Aplicar": "Aplicar",
    "No se pudo agrandar el disco.\n\n{0}":
        "Não foi possível ampliar o disco.\n\n{0}",
    "Disco agrandado": "Disco ampliado",
    "Se agrand\u00f3 correctamente a {0}.\n\nRecuerda ampliar tambi\u00e9n la partici\u00f3n dentro del sistema invitado.":
        "Ampliado corretamente para {0}.\n\nLembre-se de ampliar também a partição dentro do sistema convidado.",

    # ================================================================
    # Handlers: compactar disco
    # ================================================================
    "Solo se pueden compactar discos en formato QCOW2.":
        "Apenas discos no formato QCOW2 podem ser compactados.",
    "Este disco lo usa la VM '{0}', que esta encendida.\n\nApagala antes de compactarlo: QEMU mantiene un lock de\nescritura sobre el archivo y el compactado fallaria.":
        "Este disco é usado pela VM '{0}', que está ligada.\n\nDesligue-a antes de compactá-lo: o QEMU mantém um lock de\ngravação sobre o arquivo e a compactação falharia.",
    "\n\n\u26a0 Este disco lo usan VMs apagadas: {0}.\nSe recomienda hacer un backup antes de compactar.":
        "\n\n\u26a0 Este disco é usado por VMs desligadas: {0}.\nÉ recomendado fazer um backup antes de compactar.",
    "Confirmar compactado": "Confirmar compactação",
    "\u00bfCompactar '{0}'?\n\nReescribe el QCOW2 eliminando bloques no usados: reduce el\narchivo en el host SIN cambiar el tama\u00f1o virtual que ve el\ninvitado.{1}\n\n\u00bfContinuar?":
        "Compactar '{0}'?\n\nReescreve o QCOW2 removendo blocos não usados: reduz o\narquivo no host SEM alterar o tamanho virtual que o\nconvidado vê.{1}\n\nContinuar?",
    "Compactando... {0}%": "Compactando... {0}%",
    "No se pudo compactar.\n\n{0}":
        "Não foi possível compactar.\n\n{0}",
    "Disco compactado": "Disco compactado",
    "'{0}' compactado.\n\nAntes: {1}\nDespu\u00e9s: {2}\nAhorro: {3}":
        "'{0}' compactado.\n\nAntes: {1}\nDepois: {2}\nEconomia: {3}",
    "Compactando '{0}'": "Compactando '{0}'",
    "Reescribiendo el QCOW2 sin bloques no usados...":
        "Reescrevendo o QCOW2 sem blocos não usados...",

    # ================================================================
    # Handlers: verificar / SHA256
    # ================================================================
    "El archivo ya no existe:\n{0}":
        "O arquivo não existe mais:\n{0}",
    "El archivo existe. No hay sha256 guardado para comparar; usa 'Calcular SHA256' si quieres uno.":
        "O arquivo existe. Não há sha256 salvo para comparar; use 'Calcular SHA256' se quiser um.",
    "Archivo presente y sha256 coincide.":
        "Arquivo presente e sha256 coincide.",
    "sha256 NO coincide.\n\nEsperado: {0}\nActual:   {1}":
        "sha256 NÃO coincide.\n\nEsperado: {0}\nAtual:    {1}",
    "SHA256": "SHA256",
    "sha256 calculado y guardado:\n\n{0}":
        "sha256 calculado e salvo:\n\n{0}",
    "Error: {0}": "Erro: {0}",
    "Calculando sha256 \u2014 {0}": "Calculando sha256 \u2014 {0}",

    # ================================================================
    # Handlers: editar metadatos
    # ================================================================
    "Editar \u2014 {0}": "Editar \u2014 {0}",
    "Nombre:": "Nome:",
    "Distro:": "Distro:",
    "Version:": "Versão:",
    "Arquitectura:": "Arquitetura:",
    "URL origen:": "URL de origem:",
    "No se pudo guardar: {0}": "Não foi possível salvar: {0}",

    # ================================================================
    # Handlers: eliminar
    # ================================================================
    "Eliminar entrada": "Excluir entrada",
    "Eliminar '{0}' de la biblioteca?":
        "Excluir '{0}' da biblioteca?",
    "Quitar del indice": "Remover do índice",
    "Eliminar tambien el archivo": "Excluir também o arquivo",

    # ================================================================
    # Handlers: abrir carpeta
    # ================================================================
    "La carpeta no existe:\n{0}":
        "A pasta não existe:\n{0}",

    # ================================================================
    # Tooltips de la botonera
    # ================================================================
    "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\n"
    "biblioteca. Requiere que ninguna VM lo esté usando en\n"
    "ese momento. El disco solo puede crecer.":
        "Aumentar o tamanho virtual de um disco QCOW2/RAW da\n"
        "biblioteca. Requer que nenhuma VM o esteja usando\n"
        "nesse momento. O disco só pode crescer.",
    "Reescribe el QCOW2 sin bloques no usados, reduciendo el\n"
    "archivo en el host. No cambia el tamaño virtual que ve el\n"
    "sistema invitado.":
        "Reescreve o QCOW2 sem blocos não usados, reduzindo o\n"
        "arquivo no host. Não altera o tamanho virtual que o\n"
        "sistema convidado vê.",
    "Comprueba que el archivo exista en disco y, si hay sha256 calculado, que coincida.":
        "Verifica se o arquivo existe no disco e, se houver sha256 calculado, se coincide.",
    "Calcula el sha256 del archivo (tarda segun el tamano). Util para detectar duplicados o descargas corruptas.":
        "Calcula o sha256 do arquivo (demora conforme o tamanho). Útil para detectar duplicatas ou downloads corrompidos.",
    "Edita los metadatos de la entrada: nombre, distro, version, arquitectura, notas, tags y color.":
        "Edita os metadados da entrada: nome, distro, versão, arquitetura, notas, tags e cor.",
    "Elimina la entrada del indice. Opcionalmente borra tambien el archivo del disco (solo si vive dentro de MediaLibrary/).":
        "Exclui a entrada do índice. Opcionalmente, exclui também o arquivo do disco (apenas se estiver dentro de MediaLibrary/).",
    "Abre la carpeta que contiene el archivo en el explorador del sistema.":
        "Abre a pasta que contém o arquivo no gerenciador de arquivos do sistema.",
}
