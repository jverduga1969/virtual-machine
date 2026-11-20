"""Internacionalización de la interfaz.

Los textos se guardan en ``i18n/<codigo>.json`` con el texto español como
clave. No hace falta recompilar ficheros .qm: la traducción se aplica
recorriendo los widgets ya creados, así que funciona también con los plugins
cargados dinámicamente y con cualquier tema.
"""

import json
import logging
import re
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QLineEdit, QMenu, QComboBox,
    QTableWidget, QTreeWidget, QListWidget, QGroupBox, QDialog, QMessageBox,
    QTextBrowser,
)
from PyQt6.QtGui import QAction

ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = ROOT / "i18n"

log = logging.getLogger(__name__)

# Los nombres son exactamente los del selector de Configuración Host.
LANGUAGES = {
    "Español": "es",
    "English": "en",
    "Português (BR)": "pt_BR",
    "Deutsch": "de",
    "Français": "fr",
    "Italiano": "it",
}

_ORIGINAL = "_nvm_i18n_original"


def code_for(name):
    return LANGUAGES.get(str(name), "es")


def available_languages():
    return list(LANGUAGES)


def load_translations(code):
    """Devuelve el diccionario de traducciones; español = identidad."""
    if code == "es":
        return {}
    path = I18N_DIR / f"{code}.json"
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


_current = {}


def tr(text):
    return _current.get(text, text)


# Muchas etiquetas se crean como texto enriquecido, p. ej. "<b>Nombre:</b>"
# o "<b>Aviso</b><br><br>Detalle". Traducimos solo los segmentos de texto y
# conservamos las etiquetas HTML intactas.
_TAG_SPLIT = re.compile(r"(<[^>]+>)")


def _es_etiqueta(segmento):
    return segmento.startswith("<") and segmento.endswith(">")


def _translate_segment(texto):
    if texto in _current:
        return _current[texto]
    # Textos como "Versión actual: 4c378a4" o "2 núcleos" llevan un valor
    # variable: traducimos la parte conocida y conservamos el resto.
    prefijos = sorted((c for c in _current if len(c) > 3 and c.endswith(
        (" ", ":", "‑", "–", "·", "•"))), key=len, reverse=True)
    sufijos = sorted((c for c in _current if len(c) > 3 and c.startswith((" ", "(", "·"))),
                     key=len, reverse=True)
    resultado = texto
    for clave in prefijos:
        if resultado.startswith(clave):
            resultado = _current[clave] + resultado[len(clave):]
            break
    for clave in sufijos:
        if resultado.endswith(clave):
            resultado = resultado[:-len(clave)] + _current[clave]
            break
    # Textos como "Mi VM [Apagada]": el estado entre corchetes es dinámico.
    def traducir_corchete(m):
        interior = m.group(1)
        return "[" + _current.get(interior, interior) + "]"
    return re.sub(r"\[([^\]]+)\]", traducir_corchete, resultado)


def _translate_text(texto):
    if texto in _current:
        return _current[texto]
    partes = _TAG_SPLIT.split(texto)
    if len(partes) == 1:
        return _translate_segment(texto)
    resultado = []
    traducido = False
    for parte in partes:
        if _es_etiqueta(parte):
            resultado.append(parte)
            continue
        parte_traducida = _translate_segment(parte)
        if parte_traducida != parte:
            traducido = True
        resultado.append(parte_traducida)
    return "".join(resultado) if traducido else texto


# Un QTextBrowser muestra documentos HTML completos: sus textos no pasan por
# text()/setText(), así que necesitan su propio traductor. Se conservan las
# etiquetas y los bloques <style> intactos.
_ESTILO_HTML = re.compile(r"(<style\b[^>]*>.*?</style>)", re.I | re.S)


def _translate_html_texto(texto):
    if texto in _current:
        return _current[texto]
    inicio = len(texto) - len(texto.lstrip())
    fin = len(texto.rstrip())
    if inicio >= fin:
        return texto
    centro = texto[inicio:fin]
    if centro in _current:
        return texto[:inicio] + _current[centro] + texto[fin:]
    return texto[:inicio] + _translate_segment(centro) + texto[fin:]


def translate_html(texto):
    """Traduce el texto visible de un fragmento HTML sin tocar sus etiquetas."""
    if not isinstance(texto, str) or not texto:
        return texto
    if texto in _current:
        return _current[texto]
    resultado = []
    for parte in _ESTILO_HTML.split(texto):
        if not parte:
            continue
        if parte.lower().startswith("<style"):
            resultado.append(parte)
            continue
        for trozo in _TAG_SPLIT.split(parte):
            if _es_etiqueta(trozo):
                resultado.append(trozo)
            else:
                resultado.append(_translate_html_texto(trozo))
    return "".join(resultado)


def _clave_original(texto):
    for texto_es, valor in _current.items():
        if valor == texto:
            return texto_es
    partes = _TAG_SPLIT.split(texto)
    if len(partes) == 1:
        return texto
    invertido = {valor: clave for clave, valor in _current.items()}
    candidato = "".join(parte if _es_etiqueta(parte) else invertido.get(parte, parte)
                        for parte in partes)
    def deshacer_corchete(m):
        interior = m.group(1)
        return "[" + invertido.get(interior, interior) + "]"
    candidato = re.sub(r"\[([^\]]+)\]", deshacer_corchete, candidato)
    return candidato if candidato != texto else texto


def original_key(texto):
    """Devuelve la clave española de un texto ya traducido.

    Útil para combos y tablas donde el valor visible cambia con el idioma
    pero el dato guardado debe seguir siendo estable.
    """
    return _clave_original(texto)


class _ShowFilter(QObject):
    """Traduce diálogos y menús al crearlos, aunque se abran después del arranque."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show and isinstance(obj, (QDialog, QMenu, QMessageBox)):
            translate_widgets(obj)
        return False


_filtro = None

# Los items de tablas, árboles y listas son wrappers efímeros: no conservan
# atributos Python entre llamadas. Guardamos su texto original por widget.
_ITEM_ORIGINALS = {}


def _translate_item(owner, item, getter, setter, clave):
    key = (id(owner), clave)
    try:
        actual = getter()
    except Exception:
        return
    if not isinstance(actual, str) or not actual:
        return
    original = _ITEM_ORIGINALS.get(key)
    if original is None:
        original = _clave_original(actual)
        _ITEM_ORIGINALS[key] = original
    traducido = _translate_text(original)
    if traducido != actual:
        try:
            setter(traducido)
        except Exception:
            pass


def install(settings):
    """Carga el idioma guardado en QSettings para esta sesión."""
    global _current, _filtro
    nombre = settings.value("ui/language", "Español") if settings else "Español"
    _current = load_translations(code_for(nombre))
    app = QApplication.instance()
    if app is not None and _filtro is None:
        _filtro = _ShowFilter(app)
        app.installEventFilter(_filtro)
    return _current


def _translate_property(obj, getter, setter, clave="text"):
    try:
        actual = getter()
    except Exception:
        return
    if not isinstance(actual, str) or not actual:
        return
    atributo = f"{_ORIGINAL}_{clave}"
    original = getattr(obj, atributo, None)
    if original is None:
        # Si el widget se creó con app.tr(), su texto ya estaba traducido.
        # Recuperamos la clave española para poder cambiar de idioma en vivo.
        original = _clave_original(actual.lstrip("&"))
        if actual.startswith("&") and not original.startswith("&"):
            original = "&" + original
        try:
            setattr(obj, atributo, original)
        except Exception:
            return
    traducido = _translate_text(original.lstrip("&"))
    if actual.startswith("&") and not traducido.startswith("&"):
        traducido = "&" + traducido
    if traducido != actual:
        try:
            setter(traducido)
        except Exception:
            pass


def translate_widgets(root):
    """Aplica (o vuelve a aplicar) el idioma a un árbol de widgets."""
    if root is None:
        return
    objetos = [root]
    objetos.extend(root.findChildren(QWidget))
    objetos.extend(root.findChildren(QAction))

    for obj in objetos:
        # Los widgets con celdas generadas dinámicamente pueden ofrecer su
        # propio gancho para actualizarlas al cambiar de idioma.
        retranslate = getattr(obj, "_nvm_retranslate", None)
        if callable(retranslate):
            try:
                retranslate()
            except Exception:
                log.debug("No se pudo retraducir un widget dinámico", exc_info=True)
        if isinstance(obj, QTabWidget):
            for i in range(obj.count()):
                _translate_property(
                    obj,
                    lambda o=obj, i=i: o.tabText(i),
                    lambda texto, o=obj, i=i: o.setTabText(i, texto),
                    clave=f"tab_{i}",
                )
        if isinstance(obj, QLineEdit):
            # Solo el placeholder: el contenido puede ser texto escrito por el usuario.
            _translate_property(
                obj,
                lambda o=obj: o.placeholderText(),
                lambda texto, o=obj: o.setPlaceholderText(texto),
                clave="placeholder",
            )
        if isinstance(obj, QTableWidget):
            for i in range(obj.columnCount()):
                item = obj.horizontalHeaderItem(i)
                if item is not None:
                    _translate_item(obj, item, item.text, item.setText, f"header_h_{i}")
            for i in range(obj.rowCount()):
                item = obj.verticalHeaderItem(i)
                if item is not None:
                    _translate_item(obj, item, item.text, item.setText, f"header_v_{i}")
        elif isinstance(obj, QTreeWidget) and obj.headerItem() is not None:
            item = obj.headerItem()
            for columna in range(obj.columnCount()):
                _translate_item(
                    obj, item,
                    lambda i=columna: item.text(i),
                    lambda texto, i=columna: item.setText(i, texto),
                    f"header_{columna}",
                )
        if isinstance(obj, QListWidget):
            for i in range(obj.count()):
                item = obj.item(i)
                if item is not None:
                    _translate_item(obj, item, item.text, item.setText, f"item_{i}")
        if isinstance(obj, QComboBox) and not obj.isEditable():
            for i in range(obj.count()):
                _translate_property(
                    obj,
                    lambda o=obj, i=i: o.itemText(i),
                    lambda texto, o=obj, i=i: o.setItemText(i, texto),
                    clave=f"combo_{i}",
                )
        if isinstance(obj, (QMenu, QGroupBox)):
            _translate_property(obj, obj.title, obj.setTitle, "title")
        if isinstance(obj, QTextBrowser):
            original = getattr(obj, "_nvm_i18n_html", None)
            if original is not None:
                obj.setHtml(translate_html(original))
        if hasattr(obj, "text") and hasattr(obj, "setText") and not isinstance(obj, QLineEdit):
            _translate_property(obj, obj.text, obj.setText, "text")
        if hasattr(obj, "toolTip") and hasattr(obj, "setToolTip"):
            _translate_property(obj, obj.toolTip, obj.setToolTip, "tooltip")
        if hasattr(obj, "windowTitle") and hasattr(obj, "setWindowTitle"):
            _translate_property(obj, obj.windowTitle, obj.setWindowTitle, "windowtitle")
