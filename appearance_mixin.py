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

import os

from PyQt6.QtCore import QSettings
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
        group = QGroupBox(self.tr("Apariencia"))
        lay = QFormLayout(group)

        self.combo_theme = QComboBox()
        # i18n_tanda2e2: se envuelve cada etiqueta del combo con
        # self.tr() como literal para que pylupdate6 la extraiga.
        for _label_raw, value in self._THEME_OPTIONS:
            _label_tr = {
                "Sistema (predeterminado)": self.tr("Sistema (predeterminado)"),
                "Claro": self.tr("Claro"),
                "Oscuro": self.tr("Oscuro"),
            }.get(_label_raw, _label_raw)
            self.combo_theme.addItem(_label_tr, value)
        _saved = self._load_theme_preference()
        _idx = self.combo_theme.findData(_saved)
        if _idx >= 0:
            self.combo_theme.setCurrentIndex(_idx)
        self.combo_theme.setToolTip(self.tr(
            "Tema visual de la aplicacion.\n"
            "  - Sistema: usa el estilo y la paleta del escritorio.\n"
            "  - Claro / Oscuro: fuerza el estilo Fusion con una paleta\n"
            "    propia, independiente del SO.\n"
            "\n"
            "Al elegir Claro u Oscuro, la app cambia el estilo de Qt a\n"
            "Fusion. Al volver a Sistema, se restaura el estilo original\n"
            "del escritorio (Breeze, Adwaita, etc.)."
        ))
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        lay.addRow(self.tr("Tema:"), self.combo_theme)

        hint = QLabel(self.tr(
            "Al cambiar entre 'Sistema' y 'Claro/Oscuro' puede ser necesario\n"
            "reiniciar la app para que TODOS los widgets se repinten con los\n"
            "colores nuevos (depende del estilo del escritorio)."
        ))
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
                self, self.tr("Cambio de tema"),
                self.tr("Se ha cambiado el tema.\n\n"
                        "Algunos estilos del escritorio (Kvantum en KDE, por\n"
                        "ejemplo) pueden no repintar todos los widgets hasta\n"
                        "reiniciar la aplicacion.\n\n"
                        "¿Quieres reiniciar ahora para asegurar que todos los\n"
                        "elementos se vean correctamente?"),
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

    # ------------------------------------------------------------------
    # Modo presentación (marcador: presentation_mode_v1)
    # ------------------------------------------------------------------
    # Oculta los paneles laterales, entra en pantalla completa y salta a
    # la pestaña Consola Gráfica. Pensado para proyectar/demostrar la VM
    # sin distracciones. Se entra/sale con F11, Escape o el botón
    # "🎬 Presentación" de la barra de la Consola Gráfica.

    def _presentation_require_running_vm(self):
        """Devuelve (ok, motivo). ok=True si hay VM encendida/pausada."""
        try:
            if not self._vm_is_selected():
                return (False, self.tr("No hay ninguna máquina virtual seleccionada."))
            vm_name = os.path.basename(self.current_vm_dir)
            state = self._runtime_state(vm_name)
            if state not in ("running", "paused"):
                return (False,
                        self.tr("La VM '{0}' no está corriendo. "
                                "Enciéndela antes de entrar en modo presentación.").format(vm_name))
            if getattr(self, "_console_tab_index", -1) < 0:
                return (False,
                        self.tr("La Consola Gráfica no está disponible en este "
                                "sistema (falta el widget VNC embebido)."))
            return (True, "")
        except Exception as e:
            return (False, self.tr("No se pudo comprobar el estado de la VM: {0}").format(e))

    def _enter_presentation_mode(self):
        if getattr(self, "_presentation_mode_active", False):
            return
        ok, motivo = self._presentation_require_running_vm()
        if not ok:
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, self.tr("Modo presentación"), motivo)
            except Exception:
                pass
            return

        # Guardar estado actual.
        state = {}
        try:
            state["geometry"] = self.geometry()
            state["was_fullscreen"] = bool(self.isFullScreen())
            state["was_maximized"] = bool(self.isMaximized())
            state["prev_tab"] = self.main_tabs.currentIndex()
            state["resources_pinned"] = bool(getattr(self, "_resources_pinned", False))
            state["left_visible"] = bool(
                getattr(self, "_left_scroll", None)
                and self._left_scroll.isVisible()
            )
        except Exception:
            pass
        self._presentation_state = state
        self._presentation_mode_active = True

        # Ocultar panel izquierdo.
        try:
            if getattr(self, "_left_scroll", None) is not None:
                self._left_scroll.setVisible(False)
        except Exception:
            pass

        # Desfijar panel de recursos si estaba fijado.
        if state.get("resources_pinned"):
            try:
                self._apply_resources_pinned(False, save=False)
            except Exception:
                pass

        # Cambiar a la pestaña Consola Gráfica.
        try:
            idx = getattr(self, "_console_tab_index", -1)
            if idx >= 0:
                self.main_tabs.setCurrentIndex(idx)
        except Exception:
            pass

        # Pantalla completa.
        try:
            self.showFullScreen()
        except Exception:
            pass

        # presentation_mode_autohide_v1: ocultar las barras superiores
        # y arrancar el watcher que las muestra al subir el ratón.
        try:
            self._presentation_hide_chrome()
            self._start_presentation_cursor_watch()
        except Exception:
            pass

        # Actualizar el botón (texto) si existe.
        self._update_presentation_button()

        try:
            self.log_message(
                "==> Modo presentación ACTIVADO. "
                "Pulsa F11 o Escape para salir. "
                "Mueve el ratón a la parte superior para ver las barras."
            )
        except Exception:
            pass

    def _exit_presentation_mode(self):
        if not getattr(self, "_presentation_mode_active", False):
            return
        self._presentation_mode_active = False
        state = getattr(self, "_presentation_state", {}) or {}

        # Salir de pantalla completa.
        try:
            if self.isFullScreen():
                self.showNormal()
        except Exception:
            pass

        # Restaurar maximizado si lo estaba.
        try:
            if state.get("was_maximized") and not state.get("was_fullscreen"):
                self.showMaximized()
        except Exception:
            pass

        # Restaurar geometría original (si no estaba maximizada ni en
        # pantalla completa al entrar).
        try:
            g = state.get("geometry")
            if g is not None and not state.get("was_maximized") and not state.get("was_fullscreen"):
                self.setGeometry(g)
        except Exception:
            pass

        # Mostrar panel izquierdo.
        try:
            if getattr(self, "_left_scroll", None) is not None:
                self._left_scroll.setVisible(True)
        except Exception:
            pass

        # Restaurar panel de recursos fijado.
        if state.get("resources_pinned"):
            try:
                self._apply_resources_pinned(True, save=False)
            except Exception:
                pass

        # Restaurar pestaña anterior.
        try:
            pt = state.get("prev_tab", 0)
            if pt is not None and pt >= 0:
                self.main_tabs.setCurrentIndex(int(pt))
        except Exception:
            pass

        # presentation_mode_autohide_v1: parar el watcher y mostrar
        # las barras de nuevo.
        try:
            self._stop_presentation_cursor_watch()
            self._presentation_show_chrome()
        except Exception:
            pass

        self._update_presentation_button()

        try:
            self.log_message("==> Modo presentación desactivado.")
        except Exception:
            pass

    def _toggle_presentation_mode(self):
        if getattr(self, "_presentation_mode_active", False):
            self._exit_presentation_mode()
        else:
            self._enter_presentation_mode()

    def _update_presentation_button(self):
        btn = getattr(self, "btn_presentation", None)
        if btn is None:
            return
        try:
            if getattr(self, "_presentation_mode_active", False):
                btn.setText(self.tr("🎬 Salir de presentación"))
                btn.setToolTip(self.tr(
                    "Salir del modo presentación y restaurar la vista normal.\n"
                    "También puedes pulsar F11 o Escape."
                ))
            else:
                btn.setText(self.tr("🎬 Presentación"))
                btn.setToolTip(self.tr(
                    "Modo presentación: oculta los paneles laterales, entra\n"
                    "en pantalla completa y salta a la Consola Gráfica.\n"
                    "Requiere que la VM esté encendida.\n\n"
                    "Atajo: F11. Para salir: F11 o Escape."
                ))
        except Exception:
            pass


    # ------------------------------------------------------------------
    # Auto-hide de las barras superiores (marcador:
    # presentation_mode_autohide_v1)
    # ------------------------------------------------------------------
    # En modo presentación, la barra de pestañas y las dos filas de la
    # Consola Gráfica se ocultan. Solo aparecen cuando el cursor está a
    # menos de _PRESENTATION_HOT_ZONE px del borde superior de la
    # ventana. Mientras el cursor siga sobre alguna de esas barras,
    # permanecen visibles, para que no desaparezcan bajo el clic.
    #
    # Por qué un QTimer y no eventFilter: el widget VNC embebido captura
    # los eventos de ratón cuando tiene el foco. Un filtro dependería de
    # recibir eventos que no siempre llegan. Consultar QCursor.pos() cada
    # 120 ms es barato y funciona siempre, capture quien capture el ratón.

    _PRESENTATION_HOT_ZONE = 8   # px desde el borde superior
    _PRESENTATION_POLL_MS = 120  # frecuencia del watcher

    def _presentation_show_chrome(self):
        """Muestra la barra de pestañas y las dos filas de la consola."""
        try:
            if hasattr(self, "main_tabs"):
                self.main_tabs.tabBar().show()
        except Exception:
            pass
        try:
            w = getattr(self, "console_status_widget", None)
            if w is not None:
                w.show()
        except Exception:
            pass
        try:
            w = getattr(self, "console_toolbar_widget", None)
            if w is not None:
                w.show()
        except Exception:
            pass
        self._presentation_chrome_visible = True
        # presentation_mode_autohide_v2: recordar la altura total del
        # chrome visible. Cuando las barras esten ocultas, esta altura
        # se usa como hot zone extendida: si el usuario sube el raton
        # a donde estaban las barras, se vuelven a mostrar sin tener
        # que tocar exactamente el borde superior.
        try:
            from PyQt6.QtCore import QTimer as _QTimer
            def _remember_height():
                try:
                    h = 0
                    for attr in ("console_status_widget",
                                 "console_toolbar_widget"):
                        w = getattr(self, attr, None)
                        if w is not None and w.isVisible():
                            y2 = w.mapTo(self, w.rect().bottomRight()).y()
                            if y2 > h:
                                h = y2
                    try:
                        tb = self.main_tabs.tabBar()
                        if tb is not None and tb.isVisible():
                            y2 = tb.mapTo(self, tb.rect().bottomRight()).y()
                            if y2 > h:
                                h = y2
                    except Exception:
                        pass
                    if h > 0:
                        self._presentation_last_chrome_height = h + 12
                except Exception:
                    pass
            # Un tick despues: los widgets ya estan re-layoutados.
            _QTimer.singleShot(30, _remember_height)
        except Exception:
            pass

    def _presentation_hide_chrome(self):
        """Oculta la barra de pestañas y las dos filas de la consola."""
        try:
            if hasattr(self, "main_tabs"):
                self.main_tabs.tabBar().hide()
        except Exception:
            pass
        try:
            w = getattr(self, "console_status_widget", None)
            if w is not None:
                w.hide()
        except Exception:
            pass
        try:
            w = getattr(self, "console_toolbar_widget", None)
            if w is not None:
                w.hide()
        except Exception:
            pass
        self._presentation_chrome_visible = False

    def _start_presentation_cursor_watch(self):
        """Arranca el QTimer que mira dónde está el cursor."""
        from PyQt6.QtCore import QTimer
        t = getattr(self, "_presentation_cursor_timer", None)
        if t is None:
            t = QTimer(self)
            t.setInterval(self._PRESENTATION_POLL_MS)
            t.timeout.connect(self._presentation_cursor_tick)
            self._presentation_cursor_timer = t
        t.start()

    def _stop_presentation_cursor_watch(self):
        t = getattr(self, "_presentation_cursor_timer", None)
        if t is not None:
            try:
                t.stop()
            except Exception:
                pass

    def _presentation_cursor_tick(self):
        """Comprueba la posición del cursor y muestra/oculta las barras.

        Version 2 (marcador: presentation_mode_autohide_v2): en vez de
        usar childAt(), que fallaba cuando el cursor pasaba por un
        hueco entre widgets (spacing del layout o margen del contenedor),
        se comparan rectangulos en coordenadas de la ventana. Asi
        cualquier punto dentro del area del chrome mantiene las barras
        visibles, sin importar si esta sobre un boton, entre dos, o en
        el margen.
        """
        if not getattr(self, "_presentation_mode_active", False):
            self._stop_presentation_cursor_watch()
            return
        try:
            from PyQt6.QtGui import QCursor
        except Exception:
            return

        try:
            global_pos = QCursor.pos()
            local = self.mapFromGlobal(global_pos)
        except Exception:
            return

        # Fuera de la ventana: ocultar.
        if not self.rect().contains(local):
            self._presentation_hide_chrome()
            return

        # 1) Hot zone base (borde superior estricto).
        if local.y() < self._PRESENTATION_HOT_ZONE:
            self._presentation_show_chrome()
            return

        # 2) Si las barras estan visibles, mantenerlas mientras el
        #    cursor este dentro del rectangulo del chrome (con margen
        #    de tolerancia). Esto cubre huecos entre widgets, margenes
        #    del contenedor y el spacing del layout.
        if getattr(self, "_presentation_chrome_visible", False):
            if self._presentation_point_inside_chrome_rects(local):
                return
            # Margen vertical adicional: si el cursor esta muy cerca
            # del borde inferior del chrome, dar un poco mas de
            # tolerancia para evitar parpadeos por micro-movimientos.
            r = self._presentation_chrome_rect_local()
            if r is not None:
                x_min, y_min, x_max, y_max = r
                if (x_min <= local.x() <= x_max) and (y_min <= local.y() <= y_max + 16):
                    return
            self._presentation_hide_chrome()
            return

        # 3) Barras ocultas: usar la altura recordada del chrome como
        #    hot zone extendida. Si el usuario sube a donde estaban
        #    las barras, se vuelven a mostrar.
        threshold = max(
            self._PRESENTATION_HOT_ZONE,
            int(getattr(self, "_presentation_last_chrome_height",
                        self._PRESENTATION_HOT_ZONE))
        )
        if local.y() < threshold:
            self._presentation_show_chrome()
            return
        # Nada que hacer: siguen ocultas.

    def _presentation_chrome_rect_local(self):
        """Rectangulo (x_min, y_min, x_max, y_max) en coordenadas de la
        ventana que cubre la barra de pestañas + fila de estado + fila
        de botones, con un margen inferior de tolerancia.

        Devuelve None si ninguna de las barras esta visible.
        """
        rects = []
        try:
            tb = self.main_tabs.tabBar()
            if tb is not None and tb.isVisible():
                tl = tb.mapTo(self, tb.rect().topLeft())
                br = tb.mapTo(self, tb.rect().bottomRight())
                rects.append((tl, br))
        except Exception:
            pass
        for attr in ("console_status_widget", "console_toolbar_widget"):
            w = getattr(self, attr, None)
            if w is None or not w.isVisible():
                continue
            try:
                tl = w.mapTo(self, w.rect().topLeft())
                br = w.mapTo(self, w.rect().bottomRight())
                rects.append((tl, br))
            except Exception:
                continue
        if not rects:
            return None
        x_min = min(r[0].x() for r in rects)
        y_min = min(r[0].y() for r in rects)
        x_max = max(r[1].x() for r in rects)
        y_max = max(r[1].y() for r in rects)
        return (x_min, y_min, x_max, y_max)

    def _presentation_point_inside_chrome_rects(self, local):
        """True si (x, y) en coordenadas de la ventana esta dentro del
        rectangulo del chrome con margen de tolerancia."""
        r = self._presentation_chrome_rect_local()
        if r is None:
            return False
        x_min, y_min, x_max, y_max = r
        # Margen horizontal: no hace falta, dejamos exacto.
        # Margen vertical inferior: 8 px para tolerancia.
        return (x_min <= local.x() <= x_max) and (y_min <= local.y() <= y_max + 8)
