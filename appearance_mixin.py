# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: selector de tema (Sistema / Claro / Oscuro).

Marcador: theme_selector_v1

Estrategia robusta:

  1. Cuando el usuario elige "Claro" u "Oscuro", forzamos el estilo
     "Fusion" + una QPalette manual. Fusion SI respeta QPalette, a
     diferencia de Breeze/Kvantum que dibujan sus propios widgets.

  2. Cuando elige "Sistema", restauramos el nombre del estilo original
     del escritorio y dejamos que Qt/el SO gestionen la paleta.

  3. La preferencia se guarda en QSettings ("appearance/theme") y se
     aplica ANTES de crear la QApplication (en el __main__), para que
     la ventana nazca ya con el tema correcto.

  4. Al cambiar el tema en caliente se ofrece reiniciar la app, porque
     algunos estilos del escritorio (Kvantum en KDE) pueden no repintar
     todos los widgets hasta reiniciar.
"""

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QGroupBox, QLabel,
    QMessageBox,
)


class AppearanceMixin:

    _THEME_OPTIONS = [
        ("Sistema (predeterminado)", "system"),
        ("Claro", "light"),
        ("Oscuro", "dark"),
    ]

    def _load_theme_preference(self):
        try:
            v = QSettings().value("appearance/theme", "system")
            v = str(v or "system")
            if v not in ("system", "light", "dark"):
                v = "system"
            return v
        except Exception:
            return "system"

    def _save_theme_preference(self, value):
        try:
            QSettings().setValue("appearance/theme", str(value))
        except Exception:
            pass

    @staticmethod
    def _detect_system_style_name():
        try:
            app = QApplication.instance()
            if app is None:
                return ""
            return str(app.style().objectName() or "")
        except Exception:
            return ""

    def _apply_theme_preference(self, theme=None, silent=False):
        if theme is None:
            theme = self._load_theme_preference()
        theme = str(theme or "system")
        if theme not in ("system", "light", "dark"):
            theme = "system"

        app = QApplication.instance()
        if app is None:
            return

        if not hasattr(self, "_original_system_style"):
            self._original_system_style = self._detect_system_style_name()

        # 1) Elegir estilo. Fusion respeta QPalette; Kvantum no.
        if theme in ("dark", "light"):
            try:
                app.setStyle("Fusion")
            except Exception:
                pass
        else:
            orig = getattr(self, "_original_system_style", "") or ""
            if orig and orig.lower() != "fusion":
                try:
                    app.setStyle(orig)
                except Exception:
                    pass

        # 2) Aplicar la paleta correspondiente.
        try:
            if theme == "dark":
                self._apply_dark_palette(app)
            elif theme == "light":
                self._apply_light_palette(app)
            else:
                try:
                    app.setPalette(app.style().standardPalette())
                except Exception:
                    pass
        except Exception:
            pass

        # 3) Repintar todos los widgets.
        self._refresh_all_widgets()

    def _refresh_all_widgets(self):
        try:
            app = QApplication.instance()
            if app is None:
                return
            for w in app.allWidgets():
                try:
                    w.style().unpolish(w)
                    w.style().polish(w)
                    w.update()
                except Exception:
                    continue
        except Exception:
            pass

    def _apply_dark_palette(self, app):
        p = QPalette()
        bg = QColor(53, 53, 53)
        base = QColor(35, 35, 35)
        text = QColor(230, 230, 230)
        disabled = QColor(127, 127, 127)
        highlight = QColor(42, 130, 218)
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, text)
        p.setColor(QPalette.ColorRole.Base, base)
        p.setColor(QPalette.ColorRole.AlternateBase, bg)
        p.setColor(QPalette.ColorRole.ToolTipBase, base)
        p.setColor(QPalette.ColorRole.ToolTipText, text)
        p.setColor(QPalette.ColorRole.Text, text)
        p.setColor(QPalette.ColorRole.Button, bg)
        p.setColor(QPalette.ColorRole.ButtonText, text)
        p.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
        p.setColor(QPalette.ColorRole.Link, highlight)
        p.setColor(QPalette.ColorRole.Highlight, highlight)
        p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
        app.setPalette(p)

    def _apply_light_palette(self, app):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        p.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))
        p.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        p.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        p.setColor(QPalette.ColorRole.Text, QColor(20, 20, 20))
        p.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(20, 20, 20))
        p.setColor(QPalette.ColorRole.BrightText, QColor(220, 30, 30))
        p.setColor(QPalette.ColorRole.Link, QColor(0, 100, 200))
        p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(p)

    def _build_appearance_ui(self, parent_layout):
        group = QGroupBox("Apariencia")
        lay = QFormLayout(group)

        self.combo_theme = QComboBox()
        for label, value in self._THEME_OPTIONS:
            self.combo_theme.addItem(label, value)
        _saved = self._load_theme_preference()
        _idx = self.combo_theme.findData(_saved)
        if _idx >= 0:
            self.combo_theme.setCurrentIndex(_idx)
        self.combo_theme.setToolTip(
            "Tema visual de la aplicacion.\n"
            "  - Sistema: usa el estilo y la paleta del escritorio.\n"
            "  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n"
            "    propia, independiente del SO.\n"
            "\n"
            "Al elegir Claro u Oscuro, la app cambia el estilo de Qt a\n"
            "Fusion. Al volver a Sistema, se restaura el estilo original\n"
            "del escritorio (Breeze, Adwaita, etc.)."
        )
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        lay.addRow("Tema:", self.combo_theme)

        hint = QLabel(
            "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\n"
            "reiniciar la app para que TODOS los widgets se repinten con los\n"
            "colores nuevos (depende del estilo del escritorio)."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:11px;")
        lay.addRow("", hint)

        parent_layout.addWidget(group)
        return group

    def _on_theme_changed(self, _index):
        combo = getattr(self, "combo_theme", None)
        if combo is None:
            return
        value = combo.currentData() or "system"
        self._save_theme_preference(value)
        self._apply_theme_preference(value)
        try:
            self.log_message(
                "==> Tema cambiado a: "
                + {"system": "Sistema", "light": "Claro", "dark": "Oscuro"}.get(value, value)
            )
        except Exception:
            pass

        try:
            resp = QMessageBox.question(
                self, "Cambio de tema",
                "Se ha cambiado el tema.\n\n"
                "Algunos estilos del escritorio (Kvantum en KDE, por\n"
                "ejemplo) pueden no repintar todos los widgets hasta\n"
                "reiniciar la aplicacion.\n\n"
                "¿Quieres reiniciar ahora para asegurar que todos los\n"
                "elementos se vean correctamente?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._restart_application()
        except Exception:
            pass

    def _restart_application(self):
        try:
            import subprocess, sys, os
            script = os.path.abspath(sys.argv[0])
            subprocess.Popen([sys.executable, script] + sys.argv[1:])
        except Exception as e:
            try:
                self.log_message("[AVISO] No se pudo reiniciar: " + str(e))
            except Exception:
                pass
            return
        try:
            app = QApplication.instance()
            if app is not None:
                app.quit()
        except Exception:
            pass
