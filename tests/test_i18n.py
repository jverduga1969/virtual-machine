"""Traducciones reales: 6 idiomas y aplicación en caliente."""

import pytest

from core import i18n


class FakeSettings:
    def __init__(self, lang="Español"):
        self.lang = lang

    def value(self, key, default=""):
        return self.lang if key == "ui/language" else default


@pytest.fixture(autouse=True)
def _restaurar_idioma():
    anterior = dict(i18n._current)
    yield
    i18n._current = anterior


def test_seis_idiomas_incluyen_espanol_e_ingles():
    assert len(i18n.LANGUAGES) == 6
    assert set(i18n.available_languages()) == {
        "Español", "English", "Português (BR)", "Deutsch", "Français", "Italiano",
    }
    assert i18n.code_for("Español") == "es"
    assert i18n.code_for("English") == "en"
    assert i18n.code_for("Português (BR)") == "pt_BR"
    assert i18n.code_for("desconocido") == "es"


@pytest.mark.parametrize("nombre,codigo", list(i18n.LANGUAGES.items()))
def test_todos_los_idiomas_tienen_archivo_de_traduccion(nombre, codigo):
    datos = i18n.load_translations(codigo)
    if codigo == "es":
        assert datos == {}
        assert i18n.tr("Medios") == "Medios"
        return
    assert isinstance(datos, dict) and datos
    assert "Resumen" in datos
    assert "Configuración VM" in datos
    assert "Medios" in datos
    assert all(isinstance(v, str) and v for v in datos.values())


def test_install_lee_el_idioma_de_qsettings():
    i18n.install(FakeSettings("Deutsch"))
    assert i18n.tr("Resumen") == "Übersicht"

    i18n.install(FakeSettings("Español"))
    assert i18n.tr("Resumen") == "Resumen"


def test_traducir_arbol_de_widgets_en_caliente(qapp):
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget, QLineEdit
    from PyQt6.QtGui import QAction

    root = QWidget()
    layout = QVBoxLayout(root)
    etiqueta = QLabel("Resumen")
    boton = QPushButton("🧬 Clonar")
    boton.setToolTip("Añadir archivo(s)")
    busqueda = QLineEdit()
    busqueda.setPlaceholderText("Buscar")
    layout.addWidget(etiqueta)
    layout.addWidget(boton)
    layout.addWidget(busqueda)

    pestañas = QTabWidget()
    pestañas.addTab(QWidget(), "Medios")
    pestañas.addTab(QWidget(), "Ayuda")
    layout.addWidget(pestañas)

    accion = QAction("Atajos de teclado", root)
    root.addAction(accion)

    i18n.install(FakeSettings("English"))
    i18n.translate_widgets(root)
    assert etiqueta.text() == "Overview"
    assert boton.text() == "🧬 Clone"
    assert boton.toolTip() == "Add file(s)"
    assert busqueda.placeholderText() == "Search"  # el placeholder sí se traduce
    assert pestañas.tabText(0) == "Media"
    assert pestañas.tabText(1) == "Help"
    assert accion.text() == "Keyboard shortcuts"

    i18n.install(FakeSettings("Deutsch"))
    i18n.translate_widgets(root)
    assert etiqueta.text() == "Übersicht"
    assert pestañas.tabText(0) == "Medien"
    assert accion.text() == "Tastenkürzel"

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(root)
    assert etiqueta.text() == "Resumen"
    assert boton.text() == "🧬 Clonar"
    assert pestañas.tabText(0) == "Medios"
    assert accion.text() == "Atajos de teclado"


def test_combobox_se_traduce_pero_el_texto_del_usuario_no(qapp):
    from PyQt6.QtWidgets import QComboBox, QLineEdit

    combo = QComboBox()
    combo.addItems(["Diario", "Semanal", "Español"])
    busqueda = QLineEdit()
    busqueda.setText("Resumen")  # texto del usuario: no debe traducirse

    i18n.install(FakeSettings("English"))
    i18n.translate_widgets(combo)
    i18n.translate_widgets(busqueda)
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "Daily", "Weekly", "Español"]
    assert busqueda.text() == "Resumen"

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(combo)
    assert combo.itemText(0) == "Diario"


def test_widget_creado_ya_traducido_tambien_cambia_de_idioma(qapp):
    from PyQt6.QtWidgets import QLabel

    i18n.install(FakeSettings("English"))
    etiqueta = QLabel(i18n.tr("Medios"))  # "Media" desde el principio
    i18n.translate_widgets(etiqueta)
    assert etiqueta.text() == "Media"

    i18n.install(FakeSettings("Français"))
    i18n.translate_widgets(etiqueta)
    assert etiqueta.text() == "Médias"


def test_app_tr_usa_el_idioma_actual(app_ctx):
    i18n.install(FakeSettings("Italiano"))
    assert app_ctx.tr("Ayuda") == "Aiuto"
    i18n.install(FakeSettings("Español"))
    assert app_ctx.tr("Ayuda") == "Ayuda"


def test_catalogos_ampliados_cubren_textos_de_ui():
    claves = ["Buscar máquinas...", "Crear VM", "Disco duro", "Biblioteca de Medios",
              "📋 Copiar información de soporte", "Puerto host", "Sin reglas de reenvío configuradas."]
    for codigo in ("en", "pt_BR", "de", "fr", "it"):
        datos = i18n.load_translations(codigo)
        assert len(datos) >= 600, codigo
        for clave in claves:
            assert clave in datos, (codigo, clave)
            assert isinstance(datos[clave], str) and datos[clave], (codigo, clave)


def test_cabeceras_de_tabla_y_arbol_se_traducen(qapp):
    from PyQt6.QtWidgets import QTableWidget, QTreeWidget

    tabla = QTableWidget(2, 3)
    tabla.setHorizontalHeaderLabels(["Estado", "Nombre", "Tamaño"])
    tabla.setVerticalHeaderLabels(["ID", "Tipo"])
    arbol = QTreeWidget()
    arbol.setColumnCount(5)
    arbol.setHeaderLabels(["Dispositivo", "Bus", "Tipo / archivo", "Tamaño", "Estado"])

    i18n.install(FakeSettings("English"))
    i18n.translate_widgets(tabla)
    i18n.translate_widgets(arbol)
    assert [tabla.horizontalHeaderItem(i).text() for i in range(3)] == [
        "Status", "Name", "Size"]
    assert [tabla.verticalHeaderItem(i).text() for i in range(2)] == ["ID", "Type"]
    assert [arbol.headerItem().text(i) for i in range(5)] == [
        "Device", "Bus", "Type / file", "Size", "Status"]

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(tabla)
    i18n.translate_widgets(arbol)
    assert [tabla.horizontalHeaderItem(i).text() for i in range(3)] == [
        "Estado", "Nombre", "Tamaño"]
    assert [arbol.headerItem().text(i) for i in range(5)] == [
        "Dispositivo", "Bus", "Tipo / archivo", "Tamaño", "Estado"]


@pytest.mark.parametrize("nombre", ["English", "Português (BR)", "Deutsch", "Français", "Italiano"])
def test_cambio_en_vivo_ida_y_vuelta(qapp, nombre):
    from PyQt6.QtWidgets import QLabel

    etiqueta = QLabel("Configuración Host")
    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(etiqueta)
    assert etiqueta.text() == "Configuración Host"

    i18n.install(FakeSettings(nombre))
    i18n.translate_widgets(etiqueta)
    assert etiqueta.text() != "Configuración Host"

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(etiqueta)
    assert etiqueta.text() == "Configuración Host"


def test_etiquetas_html_y_groupboxes_y_listas(qapp):
    from PyQt6.QtWidgets import QLabel, QGroupBox, QListWidget

    etiqueta = QLabel("<b>Nombre:</b>")
    grupo = QGroupBox("Idioma")
    lista = QListWidget()
    lista.addItems(["🎨 Apariencia", "🔌 API REST"])

    i18n.install(FakeSettings("English"))
    i18n.translate_widgets(etiqueta)
    i18n.translate_widgets(grupo)
    i18n.translate_widgets(lista)
    assert etiqueta.text() == "<b>Name:</b>"
    assert grupo.title() == "Language"
    assert [lista.item(i).text() for i in range(lista.count())] == [
        "🎨 Appearance", "🔌 REST API"]

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(etiqueta)
    i18n.translate_widgets(grupo)
    i18n.translate_widgets(lista)
    assert etiqueta.text() == "<b>Nombre:</b>"
    assert grupo.title() == "Idioma"
    assert [lista.item(i).text() for i in range(lista.count())] == [
        "🎨 Apariencia", "🔌 API REST"]


def test_estados_vm_y_texto_dinamico(qapp):
    from PyQt6.QtWidgets import QLabel

    i18n.install(FakeSettings("English"))
    etiqueta = QLabel("Prueba [Apagada]")
    version = QLabel("Versión 59.0.0 · documentación del sistema")
    i18n.translate_widgets(etiqueta)
    i18n.translate_widgets(version)
    assert etiqueta.text() == "Prueba [Off]"
    assert version.text() == "Version 59.0.0 · system documentation"

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(etiqueta)
    i18n.translate_widgets(version)
    assert etiqueta.text() == "Prueba [Apagada]"
    assert version.text() == "Versión 59.0.0 · documentación del sistema"


def test_dialogo_creado_despues_se_traduce_al_mostrarse(qapp):
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

    i18n.install(FakeSettings("English"))
    dialogo = QDialog()
    layout = QVBoxLayout(dialogo)
    etiqueta = QLabel("Biblioteca de Medios")
    layout.addWidget(etiqueta)
    assert etiqueta.text() == "Biblioteca de Medios"

    dialogo.show()
    qapp.processEvents()
    assert etiqueta.text() == "Media Library"
    dialogo.close()


def test_translate_html_conserva_etiquetas_y_estilos(qapp):
    from PyQt6.QtWidgets import QTextBrowser

    html = (
        "<style>h1 { color: red; }</style>"
        "<h1>Inicio rápido</h1>"
        '<p class="muted">Pulsa <b>➕ Nueva VM</b> y elige nombre y sistema operativo.</p>'
    )
    navegador = QTextBrowser()
    navegador._nvm_i18n_html = html
    navegador.setHtml(i18n.translate_html(html))

    i18n.install(FakeSettings("English"))
    i18n.translate_widgets(navegador)
    assert navegador.toPlainText().startswith("Quick start")
    assert "Click ➕ New VM and choose a name and operating system." in navegador.toPlainText()
    assert "h1 { color: red; }" in i18n.translate_html(html)

    i18n.install(FakeSettings("Deutsch"))
    i18n.translate_widgets(navegador)
    assert navegador.toPlainText().startswith("Schnellstart")

    i18n.install(FakeSettings("Español"))
    i18n.translate_widgets(navegador)
    assert navegador.toPlainText().startswith("Inicio rápido")


def test_contenido_ayuda_y_diagnostico_en_vivo(qapp):
    from pathlib import Path

    from core import AppContext, PluginManager
    from main_window import MainWindow
    from PyQt6.QtWidgets import QListWidget, QPushButton, QTextBrowser

    i18n.install(FakeSettings("English"))
    ctx = AppContext()
    gestor = PluginManager(ctx, Path("plugins"))
    gestor.load_all()
    try:
        ventana = MainWindow(ctx, gestor)
        indice = next(i for i in range(ventana.tabs.count())
                      if ventana.tabs.tabText(i) == "Help")
        ventana.tabs.setCurrentIndex(indice)
        qapp.processEvents()

        lista = next(w for w in ventana.findChildren(QListWidget)
                     if w.count() and "Quick start" in w.item(0).text())
        navegador = next(w for w in ventana.findChildren(QTextBrowser)
                         if "Quick start" in w.toPlainText())

        titulos = [lista.item(i).text() for i in range(lista.count())]
        assert "Common problems" in titulos
        assert not any("Problemas frecuentes" in t for t in titulos)

        for fila in range(lista.count()):
            lista.setCurrentRow(fila)
            qapp.processEvents()
            texto = navegador.toPlainText()
            assert "Inicio rápido" not in texto
            assert "Pestañas del sistema" not in texto
            assert "Problemas frecuentes" not in texto
            if fila == 11:
                assert "The VM does not start" in texto
            if fila == 10:
                assert "TPM 2.0 (Windows 11 requirement)" in texto

        # El diagnóstico se genera bajo demanda y debe mostrarse traducido.
        boton = next(b for b in ventana.findChildren(QPushButton)
                     if "Run diagnostics" in b.text())
        boton.click()
        qapp.processEvents()
        diagnosticos = [b for b in ventana.findChildren(QTextBrowser)
                        if "System diagnostics" in b.toPlainText()]
        assert diagnosticos
        texto = diagnosticos[0].toPlainText()
        assert "Check of the components required" in texto
        assert "Category" in texto and "Component" in texto and "Detail" in texto

        i18n.install(FakeSettings("Deutsch"))
        i18n.translate_widgets(ventana)
        qapp.processEvents()
        assert "Systemdiagnose" in diagnosticos[0].toPlainText()
        assert "Kategorie" in diagnosticos[0].toPlainText()
        ventana.close()
    finally:
        gestor.unload_all()
