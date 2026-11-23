"""Regresiones de la Fase C: Ayuda, documentación y validaciones de CI."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT

AYUDA = ROOT / "plugins" / "help" / "plugin.py"
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
DOC_WIN = ROOT / "CONFIGURACION_WINDOWS.md"
INSTALL_WIN = ROOT / "INSTALL_WINDOWS.md"


# ----------------------------------------------------------------------
# Ayuda
# ----------------------------------------------------------------------
def test_ayuda_tiene_todos_los_temas():
    from plugins.help.plugin import TOPICS

    claves = [clave for clave, _titulo, _cuerpo in TOPICS]
    assert "host" in claves
    assert "api_rest" in claves
    assert "requisitos" in claves
    assert "faq" in claves
    assert "rutas" in claves
    assert len(claves) == len(set(claves))


def test_ayuda_de_configuracion_host_refleja_la_ui_real():
    from plugins.help.plugin import TOPICS

    cuerpo = dict((clave, html) for clave, _titulo, html in TOPICS)["host"]
    for texto in ("USB (Windows)", "Zadig", "IOMMU", "--enable-iommu",
                  "Fido", "qemu-img", "backend", "utilidades"):
        assert texto.lower() in cuerpo.lower(), texto


def test_ayuda_de_api_rest_explica_autenticacion_y_endpoints():
    from plugins.help.plugin import TOPICS

    cuerpo = dict((clave, html) for clave, _titulo, html in TOPICS)["api_rest"]
    for texto in ("127.0.0.1", "8730", "Authorization", "Bearer",
                  "/health", "/vms", "/start", "/stop", "curl"):
        assert texto in cuerpo, texto


def test_ayuda_de_requisitos_cubre_linux_y_windows():
    from plugins.help.plugin import TOPICS

    cuerpo = dict((clave, html) for clave, _titulo, html in TOPICS)["requisitos"]
    for texto in ("KVM", "WHPX", "qemu-img", "swtpm", "Zadig", "Fido"):
        assert texto in cuerpo, texto
    assert "<th>Linux</th>" in cuerpo
    assert "<th>Windows</th>" in cuerpo


def test_faq_incluye_los_problemas_nuevos():
    from plugins.help.plugin import TOPICS

    cuerpo = dict((clave, html) for clave, _titulo, html in TOPICS)["faq"]
    for titulo in ("WHPX no se activa", "firewall bloquea", "API REST no responde",
                   "Fido no encuentra"):
        assert titulo in cuerpo, titulo


def test_version_de_ayuda_coincide_con_el_instalador():
    from plugins.help import plugin as ayuda

    texto = (ROOT / "installer.iss").read_text(encoding="utf-8")
    m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', texto)
    assert m is not None
    assert ayuda.APP_VERSION == m.group(1)


def test_la_pestaña_muestra_el_tema_de_api(qapp):
    from plugins.help.plugin import Plugin

    plugin = Plugin(None)
    _tabs = plugin.get_tabs()  # mantener vivo el QWidget mientras se consulta
    titulos = [plugin.list_topics.item(i).text()
               for i in range(plugin.list_topics.count())]
    assert any("API REST local" == titulo for titulo in titulos)
    plugin.input_filter.setText("curl")
    visibles = [plugin.list_topics.item(i).text()
                for i in range(plugin.list_topics.count())
                if not plugin.list_topics.item(i).isHidden()]
    assert visibles == ["API REST local"]


# ----------------------------------------------------------------------
# Documentación
# ----------------------------------------------------------------------
@pytest.mark.parametrize("ruta", [DOC_WIN, INSTALL_WIN])
def test_docs_no_contienen_datos_obsoletos(ruta):
    texto = ruta.read_text(encoding="utf-8")
    for obsoleto in ("59.0.0", "TightVNC", "NVM_harness_test", "155 passed",
                     "7e4ee9d", "Python 3 y PyQt6"):
        assert obsoleto not in texto, (ruta.name, obsoleto)


@pytest.mark.parametrize("ruta", [DOC_WIN, INSTALL_WIN])
def test_docs_cubren_las_fases_a_b_c(ruta):
    texto = ruta.read_text(encoding="utf-8")
    for texto_buscado in ("WHPX", "qemu-img", "TPM", "Zadig", "API REST",
                          "uninstall.ps1", "Fido"):
        assert texto_buscado.lower() in texto.lower(), (ruta.name, texto_buscado)


def test_doc_de_traspaso_refleja_el_estado_sin_commit():
    texto = DOC_WIN.read_text(encoding="utf-8")
    assert "f02c238" in texto
    assert "2c7748f" in texto
    assert "windows-port" in texto
    assert "284 passed" in texto
    assert "No hacer commit ni push salvo petición explícita" in texto
    assert "Fase C" in texto


def test_instalador_explica_reinicio_y_desinstalacion():
    texto = INSTALL_WIN.read_text(encoding="utf-8")
    assert "reinicia Windows" in texto
    assert "skipifsilent" in texto
    assert "Los datos de las VMs se conservan" in texto


# ----------------------------------------------------------------------
# CI
# ----------------------------------------------------------------------
def test_workflow_valida_shell_y_librerias():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "bash -n scripts/postinstall.sh" in texto
    assert "python scripts/verify_repo.py" in texto
    assert "compileall -q core services plugins ui_widgets vnc_widget tests" in texto
    assert texto.count("python scripts/verify_repo.py") >= 2  # pytest y build


def test_gitattributes_fuerza_lf_en_todos_los_sistemas():
    contenido = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in contenido


def test_workflow_sigue_publicando_releases_por_tag():
    texto = WORKFLOW.read_text(encoding="utf-8")
    assert "tags: ['v*']" in texto
    assert "softprops/action-gh-release@v2" in texto
    assert "upload-artifact@v4" in texto


def test_validador_del_repositorio_pasa():
    resultado = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_repo.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "Verificación del repositorio OK" in resultado.stdout
