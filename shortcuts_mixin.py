# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: atajos de teclado configurables.

Marcador: configurable_shortcuts_v1

Expone un pequeño conjunto de atajos que el usuario puede reasignar
desde Configuracion Host -> Apariencia -> "Configurar atajos...".

Atajos configurables (4):
  - media           -> abrir menu de Medios (CD/DVD + USB)    [Ctrl+M]
  - reconnect       -> reconectar el widget VNC                [Ctrl+R]
  - console_toggle  -> alternar Consola Grafica                [Ctrl+Alt+C]
  - presentation    -> entrar/salir del modo presentacion      [F11]

Escape (salir del modo presentacion) NO es configurable a proposito:
si el usuario lo reasignara a otra accion, se quedaria sin forma de
salir de presentacion sin el raton.

Persistencia en QSettings:
    shortcuts/media
    shortcuts/reconnect
    shortcuts/console_toggle
    shortcuts/presentation

Los valores son cadenas de QKeySequence (por ejemplo "Ctrl+M", "F11").
Un valor vacio significa "atajo deshabilitado".
"""

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout,
)


class ShortcutsMixin:

    # ------------------------------------------------------------------
    # Registro de atajos configurables
    # ------------------------------------------------------------------
    # Cada entrada: (clave, etiqueta, valor por defecto, nombre del slot)
    #
    # El slot se resuelve con getattr(self, nombre) al aplicar los
    # atajos, porque los mixins se cargan en orden arbitrario y no
    # podemos asumir que ya existen al construir este diccionario.

    _SHORTCUT_DEFS = [
        ("media",          "Abrir menu de Medios (CD/DVD + USB)",
         "Ctrl+M",     "_show_media_menu_at_cursor"),
        ("reconnect",      "Reconectar el widget VNC",
         "Ctrl+R",     "_manual_refresh_vnc"),
        ("console_toggle", "Alternar Consola Grafica",
         "Ctrl+Alt+C", "_toggle_console_tab"),
        ("presentation",   "Entrar / salir del modo presentacion",
         "F11",        "_toggle_presentation_mode"),
    ]

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _shortcut_default(self, key):
        for k, _label, default, _slot in self._SHORTCUT_DEFS:
            if k == key:
                return default
        return ""

    def _load_shortcut(self, key):
        """Devuelve el valor actual de un atajo (string de QKeySequence).

        Cadena vacia = atajo deshabilitado. Nunca devuelve None.
        """
        try:
            v = QSettings().value("shortcuts/" + key, None)
            if v is None:
                return self._shortcut_default(key)
            return str(v)
        except Exception:
            return self._shortcut_default(key)

    def _save_shortcut(self, key, value):
        try:
            QSettings().setValue("shortcuts/" + key, str(value or ""))
        except Exception:
            pass

    def _load_all_shortcuts(self):
        return {k: self._load_shortcut(k) for k, _l, _d, _s in self._SHORTCUT_DEFS}

    def _save_all_shortcuts(self, values):
        for k, v in (values or {}).items():
            self._save_shortcut(k, v)

    # ------------------------------------------------------------------
    # Registro de los QShortcut en la ventana
    # ------------------------------------------------------------------

    def _unregister_shortcuts(self):
        """Elimina los QShortcut actuales (si los hay) y limpia el registry."""
        reg = getattr(self, "_shortcuts_registry", None)
        if not reg:
            self._shortcuts_registry = {}
            return
        for key, obj in list(reg.items()):
            try:
                obj.setEnabled(False)
                obj.deleteLater()
            except Exception:
                pass
        self._shortcuts_registry = {}

    def _register_shortcut(self, key, seq_str, slot):
        """Crea un QShortcut y lo registra. Cadena vacia = no crear."""
        from PyQt6.QtGui import QShortcut
        if not seq_str:
            return None
        try:
            sc = QShortcut(QKeySequence(seq_str), self)
            sc.activated.connect(slot)
            self._shortcuts_registry[key] = sc
            return sc
        except Exception:
            return None

    def _apply_all_shortcuts(self):
        """Re-registra TODOS los atajos desde QSettings.

        Se llama al arrancar y cada vez que el usuario guarda cambios
        en el dialogo de configuracion. Los QShortcut previos se
        destruyen primero para no duplicar disparos.
        """
        self._unregister_shortcuts()
        values = self._load_all_shortcuts()
        for key, _label, _default, slot_name in self._SHORTCUT_DEFS:
            slot = getattr(self, slot_name, None)
            if slot is None:
                continue
            self._register_shortcut(key, values.get(key, ""), slot)

        # Escape: no configurable. Solo activo cuando el modo
        # presentacion esta activo; el slot lo comprueba.
        try:
            from PyQt6.QtGui import QShortcut
            sc_esc = QShortcut(QKeySequence("Escape"), self)
            try:
                sc_esc.setContext(Qt.ShortcutContext.WindowShortcut)
            except Exception:
                pass
            sc_esc.activated.connect(self._on_presentation_escape)
            self._shortcuts_registry["__escape__"] = sc_esc
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI: boton + dialogo
    # ------------------------------------------------------------------

    def _build_shortcuts_ui(self, parent_layout):
        """Anade el boton 'Configurar atajos...' al layout indicado."""
        from PyQt6.QtWidgets import QGroupBox, QFormLayout
        group = QGroupBox("Atajos de teclado")
        lay = QFormLayout(group)

        info = QLabel(
            "Reasigna los atajos globales de la aplicacion. Los cambios\n"
            "se aplican al instante, sin reiniciar."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        lay.addRow("", info)

        self.btn_configure_shortcuts = QPushButton("Configurar atajos...")
        self.btn_configure_shortcuts.clicked.connect(
            self._open_shortcuts_dialog
        )
        lay.addRow("", self.btn_configure_shortcuts)

        parent_layout.addWidget(group)
        return group

    def _open_shortcuts_dialog(self):
        dlg = _ShortcutsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_values = dlg.values()
            self._save_all_shortcuts(new_values)
            self._apply_all_shortcuts()
            try:
                self.log_message(
                    "==> Atajos de teclado actualizados."
                )
            except Exception:
                pass


# ======================================================================
# Dialogo de configuracion de atajos
# ======================================================================

class _ShortcutsDialog(QDialog):
    """Tabla de atajos con boton Cambiar por fila y Restaurar por defecto."""

    def __init__(self, app, parent=None):
        super().__init__(parent or app)
        self.app = app
        self.setWindowTitle("Configurar atajos de teclado")
        self.setModal(True)
        self.resize(660, 380)

        # Copia local de los valores: se aplican solo al guardar.
        self._values = dict(app._load_all_shortcuts())

        lay = QVBoxLayout(self)

        info = QLabel(
            "Haz clic en <b>Cambiar...</b> para capturar una nueva\n"
            "combinacion de teclas. Pulsa <b>Escape</b> durante la\n"
            "captura para cancelarla. Usa <b>Supr</b> o <b>Retroceso</b>\n"
            "para deshabilitar un atajo."
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        lay.addWidget(info)

        self.table = QTableWidget(len(app._SHORTCUT_DEFS), 3)
        self.table.setHorizontalHeaderLabels(["Accion", "Atajo", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._row_keys = []
        for row, (key, label, _default, _slot) in enumerate(app._SHORTCUT_DEFS):
            self._row_keys.append(key)

            item_label = QTableWidgetItem(label)
            self.table.setItem(row, 0, item_label)

            item_seq = QTableWidgetItem(self._display(key))
            self.table.setItem(row, 1, item_seq)

            btn = QPushButton("Cambiar...")
            btn.clicked.connect(lambda _checked=False, r=row: self._on_change(r))
            self.table.setCellWidget(row, 2, btn)

        lay.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        self.btn_reset = QPushButton("Restaurar todos por defecto")
        self.btn_reset.clicked.connect(self._on_reset)
        bottom.addWidget(self.btn_reset)
        bottom.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        bottom.addWidget(buttons)
        lay.addLayout(bottom)

    def _display(self, key):
        v = self._values.get(key, "")
        if not v:
            return "(sin atajo)"
        try:
            return QKeySequence(v).toString(QKeySequence.SequenceFormat.NativeText)
        except Exception:
            return v

    def _refresh_row(self, row):
        key = self._row_keys[row]
        item = self.table.item(row, 1)
        if item is not None:
            item.setText(self._display(key))

    def _on_change(self, row):
        key = self._row_keys[row]
        current = self._values.get(key, "")
        dlg = _ShortcutCaptureDialog(self, current)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_seq = dlg.result_sequence()
        if new_seq is None:
            return  # cancelado en el subdialogo

        # Validar conflicto con los otros 3 atajos.
        if new_seq:
            for other_key, other_label, _d, _s in self.app._SHORTCUT_DEFS:
                if other_key == key:
                    continue
                if self._values.get(other_key, "") == new_seq:
                    QMessageBox.warning(
                        self, "Conflicto de atajos",
                        f"El atajo {QKeySequence(new_seq).toString(QKeySequence.SequenceFormat.NativeText)} "
                        f"ya esta asignado a:\n\n  {other_label}\n\n"
                        "Elige otro o cambia primero el otro atajo."
                    )
                    return

        self._values[key] = new_seq
        self._refresh_row(row)

    def _on_reset(self):
        resp = QMessageBox.question(
            self, "Restaurar atajos",
            "¿Restaurar los cuatro atajos a sus valores por defecto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        for key, _l, default, _s in self.app._SHORTCUT_DEFS:
            self._values[key] = default
        for row in range(len(self._row_keys)):
            self._refresh_row(row)

    def values(self):
        return dict(self._values)


class _ShortcutCaptureDialog(QDialog):
    """Captura la siguiente pulsacion de tecla como QKeySequence."""

    def __init__(self, parent, current_seq=""):
        super().__init__(parent)
        self.setWindowTitle("Pulsa la nueva combinacion")
        self.setModal(True)
        self.resize(460, 220)
        self._seq = None  # None = cancelado

        lay = QVBoxLayout(self)
        title = QLabel(
            "<b>Pulsa la combinacion de teclas que quieras asignar.</b>"
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(title)

        self.lbl_state = QLabel(
            "Esperando pulsacion...\n\n"
            "Escape cancela. Supr o Retroceso deshabilita el atajo."
        )
        self.lbl_state.setWordWrap(True)
        self.lbl_state.setStyleSheet("font-size: 11px; color: #888;")
        lay.addWidget(self.lbl_state)

        cur = ""
        if current_seq:
            try:
                cur = QKeySequence(current_seq).toString(
                    QKeySequence.SequenceFormat.NativeText)
            except Exception:
                cur = current_seq
        self.lbl_current = QLabel(f"Atajo actual: <b>{cur or '(sin atajo)'}</b>")
        self.lbl_current.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(self.lbl_current)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # Escape cancela la captura.
        if key == Qt.Key.Key_Escape and mods == Qt.KeyboardModifier.NoModifier:
            self._seq = None
            self.reject()
            return

        # Supr / Retroceso = deshabilitar atajo.
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and mods == Qt.KeyboardModifier.NoModifier:
            self._seq = ""
            self.accept()
            return

        # Solo modificadores: ignorar.
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Shift,
            Qt.Key.Key_Alt, Qt.Key.Key_Meta,
        ):
            self.lbl_state.setText(
                "Solo has pulsado un modificador. Anade una tecla normal.\n\n"
                "Escape cancela. Supr o Retroceso deshabilita el atajo."
            )
            return

        # Componer QKeySequence con la combinacion recibida.
        try:
            ks = QKeySequence(event.keyCombination())
            seq = ks.toString(QKeySequence.SequenceFormat.PortableText)
        except Exception:
            seq = ""

        if not seq:
            return

        self._seq = seq
        self.accept()

    def result_sequence(self):
        return self._seq
