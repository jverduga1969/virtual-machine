# -*- coding: utf-8 -*-
"""vm_pt_BR_fix2 - Traducciones al portugues (Brasil) - Cierre VS16.

Bug clasico: el emoji ⚠ existe en dos formas (U+26A0 sin VS16 y
U+26A0\ufe0f con VS16). El .ts tiene la variante con VS16; el
diccionario la tenia sin VS16. Se cubren AMBAS variantes para que
coincida seguro. Leccion documentada en TRASPASO.md bug 34.
"""

_TRAD = ("\u26a0 Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU "
         "y cae a un shell de rescate con 'Detecting Android-x86\u2026'. "
         "Usa 'Autom\u00e1tico' o 'Red Hat QXL 2D'. Las ISOs con kernel "
         "5.10+ o Bliss OS 15+ s\u00ed soportan VirtIO-GPU.")

_TRAD_PT = ("\u26a0 Android-x86 9.0 (kernel 4.9) n\u00e3o inclui o driver "
            "VirtIO-GPU e cai em um shell de resgate com "
            "'Detecting Android-x86\u2026'. Use 'Autom\u00e1tico' ou "
            "'Red Hat QXL 2D'. As ISOs com kernel 5.10+ ou Bliss OS 15+ "
            "suportam VirtIO-GPU.")

TRANSLATIONS = {
    # Variante SIN VS16 (U+26A0 solo) - ya estaba en fix1, se repite
    # por si acaso y para tener las dos en el mismo archivo.
    _TRAD: _TRAD_PT,
    # Variante CON VS16 (U+26A0 + U+FE0F) - la que tiene el .ts real.
    _TRAD.replace("\u26a0 ", "\u26a0\ufe0f "): _TRAD_PT.replace("\u26a0 ", "\u26a0\ufe0f "),
    # Cubrir tambien la forma sin espacio tras el emoji, por si el .ts
    # la hubiera guardado asi (no deberia, pero no cuesta nada).
    _TRAD.replace("\u26a0 ", "\u26a0"): _TRAD_PT.replace("\u26a0 ", "\u26a0"),
    _TRAD.replace("\u26a0 ", "\u26a0\ufe0f"): _TRAD_PT.replace("\u26a0 ", "\u26a0\ufe0f"),
}
