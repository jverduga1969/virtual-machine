# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: comparar la configuración actual de la VM con los valores por
defecto del perfil del SO seleccionado.

Marcador: compare_defaults_v1

- Botón "⚖ Comparar con defaults" en el Resumen.
- Diálogo con 3 columnas (Campo / Actual / Por defecto).
- Las filas que difieren se resaltan con fondo amarillo.
- Se puede aplicar el default a una fila o a todas de golpe.
- Aplicar NO persiste: solo cambia los widgets. La VM se guarda con el
  flujo normal (botón Guardar o Iniciar).
"""
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)


class CompareDefaultsMixin:
    # ------------------------------------------------------------------
    # Entrada pública: se llama desde el botón del Resumen.
    # ------------------------------------------------------------------
    def compare_config_with_defaults(self):
        """Abre el diálogo comparativo para la VM seleccionada."""
        if not self._vm_is_selected():
            QMessageBox.information(
                self, "Comparar con defaults",
                "Selecciona primero una máquina virtual.",
            )
            return

        profile = self._current_os_profile()
        rows = self._compare_rows(profile)
        if not rows:
            QMessageBox.information(
                self, "Comparar con defaults",
                "No se pudo determinar el perfil del SO seleccionado.",
            )
            return
        self._show_compare_dialog(rows)

    # ------------------------------------------------------------------
    # Perfil del SO
    # ------------------------------------------------------------------
    def _current_os_profile(self):
        try:
            os_type = self.combo_main_os.currentData()
        except Exception:
            return {}
        if os_type == "macos":
            version_name = self.combo_macos_ver.currentText()
        elif os_type == "windows":
            version_name = self.combo_win_ver.currentText()
        elif os_type == "android":
            version_name = "Android-x86 / Bliss OS"
        else:
            version_name = self.combo_lin_distro.currentText()
        try:
            from vm_config import get_os_profile
            return get_os_profile(
                os_type, version_name,
                version_name if os_type == "linux" else "",
            ) or {}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Defaults calculados (misma fórmula que la creación de la VM)
    # ------------------------------------------------------------------
    def _default_cores(self):
        try:
            max_cores_even = max(2, (int(self.physical_cores) // 2) * 2)
            def_cores = min(
                max_cores_even,
                max(2, (max_cores_even // 2) if max_cores_even >= 4 else 2),
            )
            if def_cores % 2:
                def_cores -= 1
            return max(2, def_cores)
        except Exception:
            return 2

    def _default_ram_gb(self):
        try:
            max_ram_even = max(2, (int(self.physical_ram_gb) // 2) * 2)
            return min(
                max_ram_even,
                16 if max_ram_even >= 32
                else (8 if max_ram_even >= 16 else 2),
            )
        except Exception:
            return 4

    # ------------------------------------------------------------------
    # Construcción de filas
    # ------------------------------------------------------------------
    def _compare_rows(self, profile):
        """Devuelve la lista de filas a comparar.

        Cada fila es un dict:
            label, widget, kind, default, current_text, default_text, differs
        """
        rows = []

        def _add_combo(label, attr, default_id):
            w = getattr(self, attr, None)
            if w is None:
                return
            cur_id = w.currentData()
            cur_text = w.currentText()
            idx = w.findData(default_id)
            def_text = w.itemText(idx) if idx >= 0 else str(default_id)
            rows.append({
                "label": label,
                "widget": w,
                "kind": "combo",
                "default": default_id,
                "current_text": cur_text,
                "default_text": def_text,
                "differs": (cur_id != default_id),
            })

        def _add_int(label, attr, default_val, unit):
            w = getattr(self, attr, None)
            if w is None:
                return
            cur = int(w.value())
            rows.append({
                "label": label,
                "widget": w,
                "kind": "int",
                "default": default_val,
                "unit": unit,
                "current_text": f"{cur} {unit}",
                "default_text": f"{default_val} {unit}",
                "differs": (cur != default_val),
            })

        def _add_bool(label, attr, default_val):
            w = getattr(self, attr, None)
            if w is None:
                return
            cur = bool(w.isChecked())
            rows.append({
                "label": label,
                "widget": w,
                "kind": "bool",
                "default": bool(default_val),
                "current_text": "Sí" if cur else "No",
                "default_text": "Sí" if bool(default_val) else "No",
                "differs": (cur != bool(default_val)),
            })

        # ¿La VM actual es Windows 11? Secure Boot y TPM siempre true.
        try:
            os_type = self.combo_main_os.currentData() or ""
        except Exception:
            os_type = ""
        is_win11 = (
            os_type == "windows"
            and self.combo_win_ver.currentText() == "Windows 11"
        )

        # --- Filas, en orden lógico ---
        _add_combo("Firmware", "combo_firmware",
                   profile.get("firmware", "bios"))
        _add_combo("Chipset", "combo_chipset",
                   profile.get("chipset", "q35"))
        _add_combo("CPU (modelo)", "combo_cpu_model", "auto")
        _add_int("Núcleos", "slider_cores",
                 self._default_cores(), "núcleos")
        _add_int("RAM", "slider_ram",
                 self._default_ram_gb(), "GB")
        _add_bool("Secure Boot", "check_secure_boot",
                  bool(profile.get("secure_boot", False) or is_win11))
        _add_bool("TPM 2.0", "check_tpm",
                  bool(profile.get("tpm", False) or is_win11))
        _add_combo("Gráficos", "combo_graphics", "auto")
        _add_combo("VRAM", "combo_graphics_vram", "256M")
        _add_combo("Audio", "combo_audio", "intel-hda")
        _add_combo("Señalización (ratón/teclado)",
                   "combo_pointer", "auto")
        _add_combo("Consola: protocolo",
                   "combo_console_protocol", "vnc")
        _add_combo("Consola: modo",
                   "combo_console_mode", "embedded")
        return rows

    # ------------------------------------------------------------------
    # Aplicar un default
    # ------------------------------------------------------------------
    def _apply_row_default(self, row):
        w = row["widget"]
        kind = row["kind"]
        val = row["default"]
        try:
            if kind == "combo":
                idx = w.findData(val)
                if idx >= 0:
                    w.setCurrentIndex(idx)
                    return True
                return False
            if kind == "int":
                w.setValue(int(val))
                return True
            if kind == "bool":
                w.setChecked(bool(val))
                return True
        except Exception:
            return False
        return False

    # ------------------------------------------------------------------
    # Texto actual y "differs" recalculados (tras aplicar)
    # ------------------------------------------------------------------
    def _current_text_for_row(self, row):
        w = row["widget"]
        kind = row["kind"]
        try:
            if kind == "combo":
                return w.currentText()
            if kind == "int":
                unit = row.get("unit", "")
                return f"{int(w.value())} {unit}".strip()
            if kind == "bool":
                return "Sí" if w.isChecked() else "No"
        except Exception:
            pass
        return ""

    def _row_differs(self, row):
        w = row["widget"]
        kind = row["kind"]
        val = row["default"]
        try:
            if kind == "combo":
                return w.currentData() != val
            if kind == "int":
                return int(w.value()) != int(val)
            if kind == "bool":
                return bool(w.isChecked()) != bool(val)
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # Diálogo
    # ------------------------------------------------------------------
    def _show_compare_dialog(self, rows):
        try:
            vm_name = (os.path.basename(self.current_vm_dir)
                       if self.current_vm_dir else "—")
        except Exception:
            vm_name = "—"

        dlg = QDialog(self)
        dlg.setWindowTitle("Comparar con defaults")
        dlg.resize(820, 580)
        layout = QVBoxLayout(dlg)

        info = QLabel(
            f"Comparación de <b>{vm_name}</b> con los valores por defecto "
            "del perfil del SO seleccionado. Las filas con fondo amarillo "
            "difieren del default.<br><br>"
            "Aplicar un default <b>no</b> guarda la VM: solo cambia el "
            "widget. Persiste con <b>Guardar</b> (en Configuración) o al "
            "iniciar la VM."
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)

        tree = QTreeWidget()
        tree.setHeaderLabels(["Campo", "Actual", "Por defecto"])
        tree.setRootIsDecorated(False)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setAlternatingRowColors(False)
        tree.setColumnWidth(0, 260)
        tree.setColumnWidth(1, 260)
        tree.setColumnWidth(2, 260)

        diff_brush = QBrush(QColor("#fff3cd"))
        diff_font = QFont()
        diff_font.setBold(True)

        items = []
        for row in rows:
            it = QTreeWidgetItem([
                row["label"], row["current_text"], row["default_text"],
            ])
            if row["differs"]:
                for col in range(3):
                    it.setBackground(col, diff_brush)
                it.setFont(1, diff_font)
                it.setFont(2, diff_font)
            tree.addTopLevelItem(it)
            items.append((it, row))

        layout.addWidget(tree, 1)

        summary = QLabel("")
        summary.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(summary)

        def _refresh():
            for it, row in items:
                cur_txt = self._current_text_for_row(row)
                row["current_text"] = cur_txt
                row["differs"] = self._row_differs(row)
                it.setText(1, cur_txt)
                if row["differs"]:
                    for col in range(3):
                        it.setBackground(col, diff_brush)
                    it.setFont(1, diff_font)
                    it.setFont(2, diff_font)
                else:
                    for col in range(3):
                        it.setBackground(col, QBrush())
                    it.setFont(1, QFont())
                    it.setFont(2, QFont())
            n = sum(1 for _, r in items if r["differs"])
            summary.setText(
                f"<b>{n}</b> diferencia(s) de <b>{len(items)}</b> campo(s)."
            )

        _refresh()

        btns = QHBoxLayout()
        btn_apply_sel = QPushButton("Aplicar al campo seleccionado")
        btn_apply_all = QPushButton("Aplicar todos los defaults")
        btn_close = QPushButton("Cerrar")

        def _apply_selected():
            sel = tree.selectedItems()
            if not sel:
                QMessageBox.information(
                    dlg, "Aplicar",
                    "Selecciona primero una fila.",
                )
                return
            for it, row in items:
                if it is sel[0]:
                    if self._apply_row_default(row):
                        _refresh()
                    break

        def _apply_all():
            n = 0
            for _, row in items:
                if row["differs"]:
                    if self._apply_row_default(row):
                        n += 1
            _refresh()
            try:
                self.log_message(
                    f"==> Comparar defaults: aplicados {n} campo(s) a "
                    f"'{vm_name}'."
                )
            except Exception:
                pass

        btn_apply_sel.clicked.connect(_apply_selected)
        btn_apply_all.clicked.connect(_apply_all)
        btn_close.clicked.connect(dlg.accept)
        btns.addWidget(btn_apply_sel)
        btns.addWidget(btn_apply_all)
        btns.addStretch(1)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

        dlg.exec()
