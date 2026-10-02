# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Fachada de internacionalizacion para Virtual.Machine.

Marcador: i18n_v1.

Estrategia:
  - Espanol es el idioma FUENTE. Las cadenas del codigo ya estan en
    espanol; no hay vm_es.qm ni hace falta. El codigo se muestra tal
    cual cuando el idioma activo es "es".
  - Ingles (y futuros idiomas) viven en i18n/vm_<code>.ts (texto
    editable con Qt Linguist) y se compilan a .qm con lrelease.
  - load_language(app, code) instala el QTranslator correspondiente
    ANTES de crear la QApplication principal, igual que el tema.

Convenciones:
  - Dentro de cualquier QObject (widgets, mixins, dialogs):
        self.tr("texto")
  - Fuera de QObject (helpers sueltos, diccionarios de modulo):
        QCoreApplication.translate("Contexto", "texto")
  - NUNCA traducir: textos operativos de VMs (notas, grupos, colores),
    logs de consola (==>, [AVISO], [ERROR]), comandos QEMU ni paths.
    Esos son datos del usuario o diagnosticos tecnicos, no interfaz.
"""

import os

from PyQt6.QtCore import QTranslator, QSettings


LANGUAGE_NAMES = {
    "es": "Español",
    "en": "English",
    "fr": "Français",
    "pt_BR": "Português (Brasil)",
    "it": "Italiano",
    "de": "Deutsch",
}

# language_flags_v1: bandera emoji por idioma.
#
# Se usa un emoji "regional indicator" (U+1F1E6..U+1F1FF) en lugar de
# un PNG/SVG: no anade assets al repo y aprovecha la fuente de emoji
# del sistema (Noto Color Emoji en la mayoria de distros Linux).
#
# Limitacion conocida: algunos sistemas (Windows con una version
# antigua de Segoe UI Emoji) muestran las banderas como los dos
# codigos de pais en un recuadro. Por eso el combo tambien lleva el
# codigo del idioma (ES/EN) al lado del icono: la opcion sigue
# siendo identificable aunque el emoji no se pinte como bandera.
LANGUAGE_FLAGS = {
    # language_flags_v1_bis: se construyen con chr() en vez de
    # escapes \U para que un doble escape accidental no vuelva
    # a dejar el string como texto literal.
    "es": chr(0x1F1EA) + chr(0x1F1F8),     # Espana
    "en": chr(0x1F1EC) + chr(0x1F1E7),     # Reino Unido
    "fr": chr(0x1F1EB) + chr(0x1F1F7),     # Francia
    "pt_BR": chr(0x1F1E7) + chr(0x1F1F7),  # Brasil
    "it": chr(0x1F1EE) + chr(0x1F1F9),     # Italia
    "de": chr(0x1F1E9) + chr(0x1F1EA),     # Alemania
}


# Referencia global al QTranslator activo. Si se queda solo en una
# variable local, el recolector de basura de Python lo destruye en
# cuanto load_language() retorna y Qt pierde el idioma al primer
# acceso. Bug clasico de PyQt6.
_ACTIVE_TRANSLATOR = None


def normalize_language(value):
    """Devuelve un codigo admitido; espanol es el idioma de respaldo."""
    return value if value in LANGUAGE_NAMES else "es"


def language_flag(code):
    """Bandera emoji del idioma, o cadena vacia si no hay.

    Marcador: language_flags_v1.
    """
    return LANGUAGE_FLAGS.get(normalize_language(code), "")


def _i18n_dir():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "i18n"
    )


def load_language(app, code):
    """Instala el QTranslator para `code` en la QApplication dada.

    Devuelve True si el idioma quedo activo (incluido el caso "es", que
    no necesita .qm porque es el idioma fuente). False si se pidio un
    idioma que tiene .ts pero aun no hay .qm compilado.

    IMPORTANTE: llamar ANTES de crear la ventana principal, para que
    todas las cadenas envueltas en self.tr(...) se resuelvan al
    construirse los widgets. Cambiar de idioma en caliente requiere
    reiniciar la app (igual que el tema).
    """
    global _ACTIVE_TRANSLATOR

    if _ACTIVE_TRANSLATOR is not None:
        try:
            app.removeTranslator(_ACTIVE_TRANSLATOR)
        except Exception:
            pass
        _ACTIVE_TRANSLATOR = None

    code = normalize_language(code)

    # Espanol = idioma fuente: las cadenas ya estan en espanol.
    if code == "es":
        return True

    qm_path = os.path.join(_i18n_dir(), "vm_%s.qm" % code)
    if not os.path.isfile(qm_path):
        return False

    tr = QTranslator()
    if not tr.load(qm_path):
        return False

    app.installTranslator(tr)
    _ACTIVE_TRANSLATOR = tr
    return True


def current_language():
    """Devuelve el idioma activo leido de QSettings."""
    try:
        return normalize_language(
            QSettings().value("ui/language", "es", type=str)
        )
    except Exception:
        return "es"


def save_language(code):
    """Persiste el idioma elegido en QSettings."""
    try:
        QSettings().setValue("ui/language", normalize_language(code))
    except Exception:
        pass
