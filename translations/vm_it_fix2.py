# -*- coding: utf-8 -*-
"""vm_it_fix2 - Traduzioni in italiano - Chiusura VS16.

Bug classico: l'emoji ⚠ esiste in due forme (U+26A0 senza VS16 e
U+26A0\ufe0f con VS16). Il .ts ha la variante con VS16; il dizionario
la aveva senza VS16. Si coprono ENTRAMBE le varianti.
Lezione documentata in TRASPASO.md bug 34.
"""

_TRAD = ("\u26a0 Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU "
         "y cae a un shell de rescate con 'Detecting Android-x86\u2026'. "
         "Usa 'Autom\u00e1tico' o 'Red Hat QXL 2D'. Las ISOs con kernel "
         "5.10+ o Bliss OS 15+ s\u00ed soportan VirtIO-GPU.")

_TRAD_IT = ("\u26a0 Android-x86 9.0 (kernel 4.9) non include il driver "
            "VirtIO-GPU e cade in una shell di ripristino con "
            "'Detecting Android-x86\u2026'. Usa 'Automatico' o "
            "'Red Hat QXL 2D'. Le ISO con kernel 5.10+ o Bliss OS 15+ "
            "supportano VirtIO-GPU.")

TRANSLATIONS = {
    # Variante SENZA VS16 (U+26A0 solo)
    _TRAD: _TRAD_IT,
    # Variante CON VS16 (U+26A0 + U+FE0F) - quella presente nel .ts reale
    _TRAD.replace("\u26a0 ", "\u26a0\ufe0f "): _TRAD_IT.replace("\u26a0 ", "\u26a0\ufe0f "),
    # Varianti senza spazio dopo l'emoji, per sicurezza
    _TRAD.replace("\u26a0 ", "\u26a0"): _TRAD_IT.replace("\u26a0 ", "\u26a0"),
    _TRAD.replace("\u26a0 ", "\u26a0\ufe0f"): _TRAD_IT.replace("\u26a0 ", "\u26a0\ufe0f"),
}
