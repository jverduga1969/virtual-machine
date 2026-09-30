# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: pestana Biblioteca de Medios (marcador media_library_v1).

Permite ver, filtrar, anadir, editar y eliminar entradas de la
biblioteca central (`media_library.MediaLibrary`), que vive en
`MediaLibrary/` al mismo nivel que `VirtualMachines/`.

La pestana se monta como una pestana principal mas de `main_tabs`,
junto a Resumen / Configuracion / Snapshots / etc.
"""
import os
import shutil
import subprocess

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QBrush, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox,
    QInputDialog, QDialog, QFormLayout, QDialogButtonBox, QPlainTextEdit,
    QGridLayout, QFrame, QSizePolicy,
)

import media_library as _ml


_MEDIA_USER_ROLE = 260

_MEDIA_OS_LABELS = [
    ("Todos", ""),
    ("Linux", "linux"),
    ("Windows", "windows"),
    ("macOS", "macos"),
    ("Android", "android"),
    ("Guest Tools", "guest-tools"),
    ("Otros", "other"),
]

_MEDIA_ARCH_LABELS = [
    ("Todas", ""),
    ("x86_64", "x86_64"),
    ("i686", "i686"),
    ("aarch64", "aarch64"),
    ("Universal", "universal"),
    ("Sin especificar", "unknown"),
]

_MEDIA_KIND_LABELS = [
    ("Todos", ""),
    ("ISO", "iso"),
    ("IMG", "img"),
    ("DMG", "dmg"),
    ("RAW", "raw"),
    ("QCOW2", "qcow2"),
    ("Otros", "other"),
]

_MEDIA_COLOR_PALETTE = [
    ("Rojo",       "#e53935"),
    ("Naranja",    "#fb8c00"),
    ("Ambar",      "#fdd835"),
    ("Verde",      "#43a047"),
    ("Verde azul", "#00897b"),
    ("Azul",       "#1e88e5"),
    ("Indigo",     "#3949ab"),
    ("Violeta",    "#8e24aa"),
    ("Rosa",       "#d81b60"),
    ("Gris",       "#757575"),
]


# media_library_sort_v1: QTreeWidgetItem con orden numerico real en
# la columna "Tamano". QTreeWidget ordena por texto del DisplayRole;
# sin esto, "1.5 GB" aparece antes que "500 MB" al ordenar por Tamano.
class _MediaTreeItem(QTreeWidgetItem):
    """Item con orden numerico en la columna Tamano (indice 4)."""

    # library_sizes_v1: dos columnas numericas (Tamaño real + Tamaño VM).
    _NUMERIC_COLS = (5, 6)

    def __lt__(self, other):
        tree = self.treeWidget()
        if tree is None:
            return super().__lt__(other)
        col = tree.sortColumn()
        if col in self._NUMERIC_COLS:
            try:
                a = self.data(col, Qt.ItemDataRole.UserRole)
                b = other.data(col, Qt.ItemDataRole.UserRole)
                return int(a or 0) < int(b or 0)
            except Exception:
                pass
        try:
            return self.text(col) < other.text(col)
        except Exception:
            return super().__lt__(other)


class MediaLibraryMixin:
    """Mixin: pestana Biblioteca de Medios (media_library_v1)."""

    def _media_library_instance(self):
        """Devuelve la instancia unica de MediaLibrary (lazy)."""
        if getattr(self, "_media_lib", None) is None:
            try:
                self._media_lib = _ml.MediaLibrary()
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] No se pudo abrir la biblioteca de medios: {e}"
                    )
                except Exception:
                    pass
                self._media_lib = None
        return self._media_lib

    # ------------------------------------------------------------------
    # Construccion de la UI
    # ------------------------------------------------------------------

    def _build_media_library_ui(self, parent_layout):
        """Construye la pestana completa y la anyade a parent_layout."""
        parent_layout.setContentsMargins(14, 14, 14, 14)
        parent_layout.setSpacing(10)

        # --- Cabecera: titulo + resumen ---
        hdr = QLabel(
            "<b>Biblioteca de Medios</b><br>"
            "<span style='color:#666;font-size:11px;'>"
            "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
            "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
            "nivel que <code>VirtualMachines/</code>) y se reutilizan "
            "entre maquinas."
            "</span>"
        )
        hdr.setWordWrap(True)
        parent_layout.addWidget(hdr)

        # --- Fila 1: filtros ---
        filt = QHBoxLayout()
        filt.setSpacing(6)

        self.media_search = QLineEdit()
        self.media_search.setPlaceholderText("Buscar por nombre, distro, tag...")
        self.media_search.setMinimumWidth(220)
        self.media_search.textChanged.connect(self._on_media_search_changed)
        filt.addWidget(self.media_search, 1)

        filt.addWidget(QLabel("SO:"))
        self.media_filter_os = QComboBox()
        for label, value in _MEDIA_OS_LABELS:
            self.media_filter_os.addItem(label, value)
        self.media_filter_os.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_os)

        filt.addWidget(QLabel("Arq.:"))
        self.media_filter_arch = QComboBox()
        for label, value in _MEDIA_ARCH_LABELS:
            self.media_filter_arch.addItem(label, value)
        self.media_filter_arch.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_arch)

        filt.addWidget(QLabel("Formato:"))
        self.media_filter_kind = QComboBox()
        for label, value in _MEDIA_KIND_LABELS:
            self.media_filter_kind.addItem(label, value)
        self.media_filter_kind.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_kind)

        # media_library_type_column_v1: filtro por tipo de medio.
        filt.addWidget(QLabel("Tipo:"))
        self.media_filter_type = QComboBox()
        self.media_filter_type.addItem("Todos", "")
        self.media_filter_type.addItem("Disco duro", "disk")
        self.media_filter_type.addItem("ISO", "iso")
        self.media_filter_type.addItem("Disquete", "floppy")
        self.media_filter_type.addItem("Otro", "other")
        self.media_filter_type.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_type)

        # media_library_ui_vm_scan_v1: filtro por origen.
        filt.addWidget(QLabel("Origen:"))
        self.media_filter_origin = QComboBox()
        self.media_filter_origin.addItem("Todos", "")
        self.media_filter_origin.addItem("Manuales", "manual")
        self.media_filter_origin.addItem("De VMs", "vm")
        self.media_filter_origin.addItem("Huerfanas de VM", "vm_orphan")
        self.media_filter_origin.currentIndexChanged.connect(
            self._on_media_filter_changed
        )
        filt.addWidget(self.media_filter_origin)

        parent_layout.addLayout(filt)

        # --- Fila 2: acciones superiores ---
        acts = QHBoxLayout()
        acts.setSpacing(6)

        self.btn_media_add = QPushButton("Anadir archivo(s)")
        self.btn_media_add.setMinimumHeight(30)
        self.btn_media_add.clicked.connect(self.add_media_from_files)
        acts.addWidget(self.btn_media_add)

        self.btn_media_scan = QPushButton("Escanear carpeta")
        self.btn_media_scan.setMinimumHeight(30)
        self.btn_media_scan.setToolTip(
            "Busca archivos de medios dentro de MediaLibrary/ que aun no "
            "esten registrados, y detecta entradas huerfanas (archivo "
            "desaparecido del disco)."
        )
        self.btn_media_scan.clicked.connect(self.scan_media_library)
        acts.addWidget(self.btn_media_scan)

        # media_library_ui_vm_scan_v1: escaneo de VMs.
        self.btn_media_scan_vms = QPushButton("\U0001f50e Escanear VMs")
        self.btn_media_scan_vms.setMinimumHeight(30)
        self.btn_media_scan_vms.setToolTip(
            "Recorre todas las VMs en VirtualMachines/ y registra sus "
            "discos duros, ISOs y disquetes en la biblioteca.\n\n"
            "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
            "todas las VMs en la columna 'Usada por'. Las entradas que ya "
            "no usa ninguna VM se marcan como huerfanas pero no se borran."
        )
        self.btn_media_scan_vms.clicked.connect(self.scan_media_vms)
        acts.addWidget(self.btn_media_scan_vms)

        acts.addStretch(1)

        self.media_count_label = QLabel("")
        self.media_count_label.setStyleSheet("color:#666; font-size:11px;")
        acts.addWidget(self.media_count_label)

        parent_layout.addLayout(acts)

        # --- Tabla central ---
        self.media_table = QTreeWidget()
        # media_library_sort_v1: "Ruta" pasa al final; la columna
        # "Tamano" sigue en el indice 4 (usado por _MediaTreeItem
        # para ordenar numericamente).
        self.media_table.setHeaderLabels(
            ["Nombre", "Tipo", "SO", "Version", "Arq.",
             "Tamaño real", "Tamaño VM",
             "Usada por", "Estado", "Ultimo uso", "Ruta"]
        )
        self.media_table.setColumnWidth(0, 200)
        self.media_table.setColumnWidth(1, 100)
        self.media_table.setColumnWidth(2, 65)
        self.media_table.setColumnWidth(3, 60)
        self.media_table.setColumnWidth(4, 60)
        self.media_table.setColumnWidth(5, 95)
        self.media_table.setColumnWidth(6, 95)
        self.media_table.setColumnWidth(7, 140)
        self.media_table.setColumnWidth(8, 65)
        self.media_table.setColumnWidth(9, 85)
        self.media_table.setColumnWidth(10, 220)
        # media_library_sort_v1: permitir ordenar pinchando cabeceras.
        self.media_table.setSortingEnabled(True)
        self.media_table.setRootIsDecorated(False)
        self.media_table.setAlternatingRowColors(True)
        self.media_table.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.media_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.media_table.itemSelectionChanged.connect(
            self._on_media_selection_changed
        )
        self.media_table.itemDoubleClicked.connect(
            self._on_media_table_double_click
        )
        parent_layout.addWidget(self.media_table, 3)

        # --- Fila 3: acciones sobre la fila seleccionada ---
        acts2 = QHBoxLayout()
        acts2.setSpacing(6)

        for label, slot, tip in (
            ("↗ Agrandar", self.enlarge_media_entry,
             "Aumentar el tamaño virtual de un disco QCOW2/RAW de la\n"
             "biblioteca. Requiere que ninguna VM lo esté usando en\n"
             "ese momento. El disco solo puede crecer."),
            ("🗜 Compactar", self.compact_media_entry,
             "Reescribe el QCOW2 sin bloques no usados, reduciendo el\n"
             "archivo en el host. No cambia el tamaño virtual que ve el\n"
             "sistema invitado."),
            ("Verificar", self.verify_media_entry,
             "Comprueba que el archivo exista en disco y, si hay sha256 "
             "calculado, que coincida."),
            ("Calcular SHA256", self.compute_media_sha256,
             "Calcula el sha256 del archivo (tarda segun el tamano). "
             "Util para detectar duplicados o descargas corruptas."),
            ("Editar", self.edit_media_metadata,
             "Edita los metadatos de la entrada: nombre, distro, version, "
             "arquitectura, notas, tags y color."),
            ("Eliminar", self.delete_media_entry,
             "Elimina la entrada del indice. Opcionalmente borra tambien "
             "el archivo del disco (solo si vive dentro de MediaLibrary/)."),
            ("Abrir carpeta", self.open_media_folder,
             "Abre la carpeta que contiene el archivo en el explorador "
             "del sistema."),
        ):
            b = QPushButton(label)
            b.setMinimumHeight(28)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            acts2.addWidget(b)

        acts2.addStretch(1)
        parent_layout.addLayout(acts2)

        # --- Panel inferior: metadatos editables ---
        meta_box = QFrame()
        meta_box.setFrameShape(QFrame.Shape.StyledPanel)
        meta_box.setStyleSheet(
            "QFrame { background: palette(alternate-base); "
            "border: 1px solid palette(mid); border-radius: 6px; }"
        )
        meta_lay = QGridLayout(meta_box)
        meta_lay.setContentsMargins(10, 10, 10, 10)
        meta_lay.setHorizontalSpacing(10)
        meta_lay.setVerticalSpacing(6)

        meta_lay.addWidget(QLabel("<b>Notas:</b>"), 0, 0, Qt.AlignmentFlag.AlignTop)
        self.media_notes_edit = QPlainTextEdit()
        self.media_notes_edit.setPlaceholderText(
            "Notas libres sobre esta entrada (uso previsto, si dio "
            "problemas, driver necesario, etc.)"
        )
        self.media_notes_edit.setMaximumHeight(70)
        self.media_notes_edit.textChanged.connect(self._on_media_notes_changed)
        meta_lay.addWidget(self.media_notes_edit, 0, 1, 1, 3)

        meta_lay.addWidget(QLabel("<b>Tags:</b>"), 1, 0)
        self.media_tags_edit = QLineEdit()
        self.media_tags_edit.setPlaceholderText(
            "Separados por coma (ej.: probado, servidor, rapiro)"
        )
        self.media_tags_edit.editingFinished.connect(self._on_media_tags_changed)
        meta_lay.addWidget(self.media_tags_edit, 1, 1, 1, 3)

        meta_lay.addWidget(QLabel("<b>Color:</b>"), 2, 0)
        self.media_color_combo = QComboBox()
        self.media_color_combo.addItem("(Sin color)", "")
        for label, hex_c in _MEDIA_COLOR_PALETTE:
            self.media_color_combo.addItem(label, hex_c)
        self.media_color_combo.currentIndexChanged.connect(
            self._on_media_color_changed
        )
        meta_lay.addWidget(self.media_color_combo, 2, 1)

        self.media_meta_hint = QLabel("")
        self.media_meta_hint.setStyleSheet("color:#888; font-size:10px;")
        meta_lay.addWidget(self.media_meta_hint, 2, 2, 1, 2)

        parent_layout.addWidget(meta_box, 0)

        # Cargar la tabla por primera vez.
        try:
            self.refresh_media_library_table()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Refresco de la tabla
    # ------------------------------------------------------------------

    def refresh_media_library_table(self):
        """Reconstruye la tabla segun filtros y busqueda actuales."""
        if not hasattr(self, "media_table"):
            return
        lib = self._media_library_instance()
        if lib is None:
            self.media_table.clear()
            self.media_count_label.setText("Biblioteca no disponible.")
            return

        query = (self.media_search.text() or "").strip()
        os_type = self.media_filter_os.currentData() or ""
        arch = self.media_filter_arch.currentData() or ""
        kind = self.media_filter_kind.currentData() or ""
        try:
            origin = self.media_filter_origin.currentData() or ""
        except Exception:
            origin = ""

        entries = lib.list_all()
        if query:
            entries = lib.find(query)
        if os_type or arch or kind:
            entries = lib.filter_by(
                os_type=os_type or None,
                arch=arch if arch and arch != "unknown" else None,
                kind=kind or None,
            )
            if arch == "unknown":
                entries = [e for e in entries if not (e.get("arch") or "").strip()]
        # media_library_ui_vm_scan_v1: filtro por origen.
        if origin == "manual":
            entries = [e for e in entries
                       if str(e.get("origin") or "") == "manual"]
        elif origin == "vm":
            entries = [e for e in entries
                       if str(e.get("origin") or "") == "vm"]
        elif origin == "vm_orphan":
            entries = [e for e in entries
                       if str(e.get("origin") or "") == "vm"
                       and not (e.get("used_by") or [])]
        # media_library_type_column_v1: filtro por tipo de medio.
        try:
            _media_type = self.media_filter_type.currentData() or ""
        except Exception:
            _media_type = ""
        if _media_type:
            try:
                import media_library as _ml_mod
                entries = [e for e in entries
                           if _ml_mod.media_type_key(e) == _media_type]
            except Exception:
                pass

        # Preservar la seleccion actual (por id).
        current_id = None
        it = self.media_table.currentItem()
        if it is not None:
            current_id = it.data(0, _MEDIA_USER_ROLE)

        # media_library_sort_v1: deshabilitar sorting durante el
        # llenado masivo para que Qt no re-ordene en cada addItem.
        _sort_was = self.media_table.isSortingEnabled()
        self.media_table.setSortingEnabled(False)
        self.media_table.clear()
        for e in entries:
            eid = str(e.get("id") or "")
            name = str(e.get("name") or e.get("filename") or "?")
            os_txt = str(e.get("os_type") or "").capitalize()
            ver = str(e.get("version") or "")
            arch_txt = str(e.get("arch") or "")
            size_txt = _ml._human_bytes(e.get("size") or 0) if hasattr(_ml, "_human_bytes") else ""
            status = self._media_status_for_entry(e)

            # media_library_ui_vm_scan_v1: columna "Usada por".
            used_by = list(e.get("used_by") or [])
            if not used_by:
                used_by_txt = "\u2014"
            elif len(used_by) == 1:
                used_by_txt = used_by[0]
            elif len(used_by) <= 3:
                used_by_txt = ", ".join(used_by)
            else:
                used_by_txt = (f"{used_by[0]}, {used_by[1]} "
                               f"(+{len(used_by) - 2})")

            # media_library_ui_vm_scan_v1: columna "Ruta".
            stored_path = str(e.get("path") or "")
            if not stored_path:
                path_txt = "(sin archivo)"
            elif os.path.isabs(stored_path) and len(stored_path) > 40:
                path_txt = "\u2026" + stored_path[-37:]
            else:
                path_txt = stored_path

            # media_library_sort_v1: orden de columnas actualizado
            # ("Ruta" al final) + sort key numerico para "Tamano".
            try:
                import media_library as _ml_mod
                tipo_txt = _ml_mod.media_type_label(e)
            except Exception:
                tipo_txt = ""
            # library_sizes_v1: dos columnas de tamaño.
            try:
                _real = int(e.get("size") or 0)
            except Exception:
                _real = 0
            try:
                _virt = int(e.get("virtual_size") or 0)
            except Exception:
                _virt = 0
            real_txt = _ml._human_bytes(_real) if _real else "—"
            virt_txt = _ml._human_bytes(_virt) if _virt else "—"

            row = _MediaTreeItem([
                name, tipo_txt, os_txt, ver, arch_txt, real_txt, virt_txt,
                used_by_txt, status, str(e.get("last_used") or ""),
                path_txt,
            ])
            row.setData(0, _MEDIA_USER_ROLE, eid)
            try:
                row.setData(5, Qt.ItemDataRole.UserRole, _real)
                row.setData(6, Qt.ItemDataRole.UserRole, _virt)
            except Exception:
                pass
            row.setToolTip(0, str(e.get("path") or ""))
            row.setToolTip(5, "Espacio real ocupado en el host.")
            row.setToolTip(6, "Tamaño virtual (lo que ve el sistema invitado).")
            row.setToolTip(7, ("\n".join(used_by) if used_by
                               else "No la usa ninguna VM."))
            row.setToolTip(10, stored_path or "(sin archivo)")

            hex_c = str(e.get("color") or "").strip()
            if hex_c.startswith("#") and len(hex_c) == 7:
                try:
                    col = QColor(hex_c)
                    col.setAlpha(80)
                    for c in range(11):
                        row.setBackground(c, QBrush(col))
                except Exception:
                    pass

            self.media_table.addTopLevelItem(row)

        # media_library_sort_v1: reactivar sorting tras el llenado y
        # forzar un re-orden para que las filas ya presentes tomen el
        # orden que el usuario tenia seleccionado.
        self.media_table.setSortingEnabled(bool(_sort_was))
        try:
            hdr = self.media_table.header()
            if hdr is not None and hdr.sortIndicatorSection() >= 0:
                self.media_table.sortByColumn(
                    hdr.sortIndicatorSection(),
                    hdr.sortIndicatorOrder(),
                )
        except Exception:
            pass

        stats = lib.stats()
        self.media_count_label.setText(
            f"{len(entries)} entrada(s) mostradas de {stats.get('total', 0)} "
            f"| Tamano total: {stats.get('size_total_human', '-')}"
        )

        # Restaurar la seleccion si seguia estando.
        if current_id:
            for i in range(self.media_table.topLevelItemCount()):
                row = self.media_table.topLevelItem(i)
                if row.data(0, _MEDIA_USER_ROLE) == current_id:
                    self.media_table.setCurrentItem(row)
                    break
        self._on_media_selection_changed()

    def _media_status_for_entry(self, entry):
        """Icono textual del estado de una entrada."""
        try:
            path_abs = self._media_library_instance().resolve_path(entry)
        except Exception:
            path_abs = ""
        if not path_abs or not os.path.isfile(path_abs):
            return "huerfano"
        if str(entry.get("sha256") or "").strip():
            return "verificado?"
        return "OK"

    # ------------------------------------------------------------------
    # Filtros y busqueda
    # ------------------------------------------------------------------

    def _on_media_search_changed(self, *_args):
        self.refresh_media_library_table()

    def _on_media_filter_changed(self, *_args):
        self.refresh_media_library_table()

    # ------------------------------------------------------------------
    # Seleccion: rellenar el panel inferior
    # ------------------------------------------------------------------

    def _media_selected_id(self):
        it = self.media_table.currentItem() if hasattr(self, "media_table") else None
        return it.data(0, _MEDIA_USER_ROLE) if it is not None else None

    def _on_media_selection_changed(self, *_args):
        lib = self._media_library_instance()
        if lib is None:
            return
        eid = self._media_selected_id()
        e = lib.get(eid) if eid else None
        # Bloquear senales para no reescribir al rellenar.
        self.media_notes_edit.blockSignals(True)
        self.media_tags_edit.blockSignals(True)
        self.media_color_combo.blockSignals(True)
        try:
            if e is None:
                self.media_notes_edit.setPlainText("")
                self.media_tags_edit.setText("")
                self.media_color_combo.setCurrentIndex(0)
                self.media_notes_edit.setEnabled(False)
                self.media_tags_edit.setEnabled(False)
                self.media_color_combo.setEnabled(False)
                self.media_meta_hint.setText("")
            else:
                self.media_notes_edit.setEnabled(True)
                self.media_tags_edit.setEnabled(True)
                self.media_color_combo.setEnabled(True)
                self.media_notes_edit.setPlainText(str(e.get("notes") or ""))
                self.media_tags_edit.setText(", ".join(e.get("tags") or []))
                cur = str(e.get("color") or "")
                idx = self.media_color_combo.findData(cur)
                self.media_color_combo.setCurrentIndex(idx if idx >= 0 else 0)
                path_txt = lib.resolve_path(e)
                size_txt = _ml._human_bytes(e.get("size") or 0)
                _used = list(e.get("used_by") or [])
                _used_txt = (f" | Usada por: {', '.join(_used)}"
                             if _used else "")
                self.media_meta_hint.setText(
                    f"{e.get('filename','')} | {size_txt} | "
                    f"{path_txt}{_used_txt}"
                )
        finally:
            self.media_notes_edit.blockSignals(False)
            self.media_tags_edit.blockSignals(False)
            self.media_color_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Panel inferior: guardar metadatos
    # ------------------------------------------------------------------

    def _on_media_notes_changed(self):
        eid = self._media_selected_id()
        if not eid:
            return
        lib = self._media_library_instance()
        if lib is None:
            return
        try:
            lib.update(eid, notes=self.media_notes_edit.toPlainText())
            self.media_meta_hint.setText(self.media_meta_hint.text())
        except Exception:
            pass

    def _on_media_tags_changed(self):
        eid = self._media_selected_id()
        if not eid:
            return
        lib = self._media_library_instance()
        if lib is None:
            return
        txt = self.media_tags_edit.text() or ""
        tags = [t.strip() for t in txt.split(",") if t.strip()]
        try:
            lib.update(eid, tags=tags)
        except Exception:
            pass

    def _on_media_color_changed(self, *_args):
        eid = self._media_selected_id()
        if not eid:
            return
        lib = self._media_library_instance()
        if lib is None:
            return
        hex_c = self.media_color_combo.currentData() or ""
        try:
            lib.update(eid, color=hex_c)
            self.refresh_media_library_table()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Anadir archivos
    # ------------------------------------------------------------------

    def add_media_from_files(self):
        lib = self._media_library_instance()
        if lib is None:
            QMessageBox.warning(self, "Biblioteca de Medios",
                                "La biblioteca no esta disponible.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Anadir archivos a la biblioteca", os.path.expanduser("~"),
            "Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;"
            "Todos los archivos (*)",
        )
        if not paths:
            return
        anadidos = 0
        duplicados = 0
        for p in paths:
            ap = os.path.abspath(p)
            # Duplicado por ruta ya presente?
            ya = any(
                str(e.get("path") or "") == ap or
                (not os.path.isabs(str(e.get("path") or "")) and
                 lib._to_absolute(e.get("path")) == ap)
                for e in lib.list_all()
            )
            if ya:
                duplicados += 1
                continue
            try:
                lib.add(ap)
                anadidos += 1
            except Exception as e:
                try:
                    self.log_message(f"[AVISO] No se pudo anadir {ap}: {e}")
                except Exception:
                    pass
        self.refresh_media_library_table()
        msg = f"{anadidos} entrada(s) anadidas."
        if duplicados:
            msg += f" {duplicados} ya estaban registradas."
        try:
            self.log_message(f"==> Biblioteca de Medios: {msg}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Escanear
    # ------------------------------------------------------------------

    def scan_media_vms(self):
        """Recorre VirtualMachines/ y cataloga los medios de cada VM."""
        lib = self._media_library_instance()
        if lib is None:
            QMessageBox.warning(self, "Biblioteca de Medios",
                                "La biblioteca no esta disponible.")
            return
        try:
            res = lib.scan_vms()
        except Exception as e:
            QMessageBox.warning(
                self, "Escanear VMs",
                f"No se pudieron escanear las VMs.\n\n{e}"
            )
            return
        self.refresh_media_library_table()

        nuevas = int(res.get("nuevas") or 0)
        actualizadas = int(res.get("actualizadas") or 0)
        huerfanas = res.get("huerfanas_de_vm") or []
        total = int(res.get("total_paths") or 0)

        lines = [f"Archivos unicos encontrados en VMs: {total}."]
        if nuevas:
            lines.append(
                f"- {nuevas} medio(s) nuevo(s) anadido(s) a la biblioteca."
            )
        if actualizadas:
            lines.append(
                f"- {actualizadas} entrada(s) actualizada(s) con la "
                "lista de VMs que las usan."
            )
        if huerfanas:
            lines.append(
                f"- {len(huerfanas)} entrada(s) ya no las usa ninguna VM "
                "(siguen visibles; filtro Origen = 'Huerfanas de VM')."
            )
        if not (nuevas or actualizadas or huerfanas):
            lines.append("Sin cambios: la biblioteca ya estaba al dia.")

        try:
            self.log_message("==> Biblioteca: " + " ".join(lines))
        except Exception:
            pass
        QMessageBox.information(
            self, "Escanear VMs", "\n".join(lines)
        )

    def scan_media_library(self):
        lib = self._media_library_instance()
        if lib is None:
            return
        try:
            res = lib.scan()
        except Exception as e:
            QMessageBox.warning(self, "Escanear", f"No se pudo escanear.\n\n{e}")
            return
        nuevos = res.get("nuevos") or []
        huerfanos = res.get("huerfanos") or []
        if not nuevos and not huerfanos:
            QMessageBox.information(
                self, "Escanear",
                "No hay archivos nuevos ni entradas huerfanas."
            )
            return
        msg = []
        if nuevos:
            msg.append(f"{len(nuevos)} archivo(s) nuevos encontrados:")
            for n in nuevos[:8]:
                msg.append(f"  - {os.path.basename(n.get('path_abs',''))} "
                           f"[{n.get('os_type','?')}]")
            if len(nuevos) > 8:
                msg.append(f"  ... y {len(nuevos) - 8} mas")
        if huerfanos:
            msg.append("")
            msg.append(f"{len(huerfanos)} entrada(s) huerfanas (archivo ya no existe):")
            for h in huerfanos[:8]:
                msg.append(f"  - {h.get('name') or h.get('filename','?')}")
            if len(huerfanos) > 8:
                msg.append(f"  ... y {len(huerfanos) - 8} mas")
        msg.append("")
        if nuevos:
            msg.append("Anadir los archivos nuevos a la biblioteca?")
            r = QMessageBox.question(
                self, "Escanear",
                "\n".join(msg),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if r == QMessageBox.StandardButton.Yes:
                for n in nuevos:
                    try:
                        lib.add(n.get("path_abs"))
                    except Exception:
                        pass
                self.refresh_media_library_table()
            else:
                self.refresh_media_library_table()
        else:
            QMessageBox.information(self, "Escanear", "\n".join(msg))
            self.refresh_media_library_table()

    # ------------------------------------------------------------------
    # Verificar / SHA256
    # ------------------------------------------------------------------

    # ---------------------------------------------------------------
    # library_sizes_v1: Agrandar y Compactar desde la Biblioteca
    # ---------------------------------------------------------------

    @staticmethod
    def _is_qcow2_disk(entry):
        """True si la entrada es un disco QCOW2 (permite compactar)."""
        if not isinstance(entry, dict):
            return False
        p = str(entry.get("path") or "").lower()
        k = str(entry.get("kind") or "").lower()
        return (p.endswith(".qcow2") or p.endswith(".qcow")
                or k == "qcow2")

    def _media_entry_in_use_by_running_vm(self, entry):
        """Devuelve el nombre de la VM que usa la entrada y esta encendida."""
        used = entry.get("used_by") or []
        if not used:
            return ""
        for vm_name in used:
            try:
                st = self._runtime_state(vm_name)
            except Exception:
                st = "stopped"
            if st in ("running", "paused"):
                return vm_name
        return ""

    def enlarge_media_entry(self):
        """Aumenta el tamaño virtual de un disco de la biblioteca."""
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "Agrandar",
                                    "Selecciona una entrada primero.")
            return
        e = lib.get(eid)
        if not e:
            return

        try:
            import media_library as _ml_mod
            if _ml_mod.media_type_key(e) != "disk":
                QMessageBox.information(
                    self, "Agrandar",
                    "Solo se pueden agrandar discos duros (QCOW2/RAW)."
                )
                return
        except Exception:
            pass

        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, "Agrandar",
                                f"El archivo no existe:\n{path}")
            return

        running = self._media_entry_in_use_by_running_vm(e)
        if running:
            QMessageBox.warning(
                self, "Agrandar",
                f"Este disco lo usa la VM '{running}', que esta encendida.\n\n"
                "Apagala antes de agrandarlo."
            )
            return

        _cur = 0
        try:
            r = subprocess.run(
                ["qemu-img", "info", "--output=json", path],
                capture_output=True, text=True, timeout=10, check=True,
            )
            _cur = int(json.loads(r.stdout).get("virtual-size", 0) or 0)
        except Exception:
            _cur = 0

        def _fmt(n):
            try:
                return self._format_bytes_iexport(int(n))
            except Exception:
                return f"{int(n)} B"

        def _bytes_to_qemu_size(n):
            try:
                n = int(n)
            except (TypeError, ValueError):
                return ""
            if n <= 0:
                return ""
            for unit, div in (("T", 1024 ** 4), ("G", 1024 ** 3),
                              ("M", 1024 ** 2), ("K", 1024)):
                if n >= div:
                    v = n / div
                    if v == int(v):
                        return f"{int(v)}{unit}"
                    return f"{v:.2f}".rstrip("0").rstrip(".") + unit
            return str(n)

        cur_qemu = _bytes_to_qemu_size(_cur)
        cur_txt = _fmt(_cur) if _cur else "—"

        dlg = QDialog(self)
        dlg.setWindowTitle("↗ Agrandar disco")
        dlg.resize(520, 260)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()
        form.addRow("Archivo:", QLabel(os.path.basename(path)))
        form.addRow("Tamaño actual:", QLabel(cur_txt))
        size_edit = QLineEdit(cur_qemu)
        size_edit.setPlaceholderText("Ejemplo: 120G (solo crecer)")
        form.addRow("Nuevo tamaño:", size_edit)
        lay.addLayout(form)

        hint = QLabel(
            "El disco solo puede CRECER. Agrandar el archivo NO agranda\n"
            "la partición dentro del guest: hay que ampliarla también desde\n"
            "el sistema invitado para aprovechar el nuevo espacio."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666; font-size:11px;")
        lay.addWidget(hint)

        def _on_accept():
            txt = size_edit.text().strip()
            if _cur <= 0 or not txt or txt == cur_qemu:
                dlg.accept()
                return
            try:
                new_b = self._parse_size_to_bytes(txt)
            except Exception:
                new_b = None
            if new_b is None:
                QMessageBox.warning(dlg, "Tamaño inválido",
                                    f"'{txt}' no es un tamaño válido.")
                size_edit.setText(cur_qemu)
                return
            if new_b < _cur:
                QMessageBox.warning(
                    dlg, "No se puede encoger",
                    f"Actual: {cur_txt}, indicado {txt}.\n\n"
                    "El valor se ha restaurado al tamaño actual."
                )
                size_edit.setText(cur_qemu)
                return
            dlg.accept()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_b = QPushButton("Cancelar")
        ok_b = QPushButton("Aplicar")
        cancel_b.clicked.connect(dlg.reject)
        ok_b.clicked.connect(_on_accept)
        btn_row.addWidget(cancel_b)
        btn_row.addWidget(ok_b)
        lay.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_txt = size_edit.text().strip()
        if not new_txt or new_txt == cur_qemu:
            return
        try:
            subprocess.run(
                ["qemu-img", "resize", path, new_txt],
                check=True, capture_output=True, text=True, timeout=600,
            )
        except Exception as ex:
            QMessageBox.critical(self, "Agrandar",
                                 f"No se pudo agrandar el disco.\n\n{ex}")
            return
        try:
            lib.update_virtual_size(eid)
        except Exception:
            pass
        self.refresh_media_library_table()
        QMessageBox.information(
            self, "Disco agrandado",
            f"Se agrandó correctamente a {new_txt}.\n\n"
            "Recuerda ampliar también la partición dentro del sistema invitado."
        )

    def compact_media_entry(self):
        """Compacta un disco QCOW2 de la biblioteca."""
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "Compactar",
                                    "Selecciona una entrada primero.")
            return
        e = lib.get(eid)
        if not e:
            return
        if not self._is_qcow2_disk(e):
            QMessageBox.information(
                self, "Compactar",
                "Solo se pueden compactar discos en formato QCOW2."
            )
            return
        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, "Compactar",
                                f"El archivo no existe:\n{path}")
            return
        name = os.path.basename(path)

        running = self._media_entry_in_use_by_running_vm(e)
        if running:
            QMessageBox.warning(
                self, "Compactar",
                f"Este disco lo usa la VM '{running}', que esta encendida.\n\n"
                "Apagala antes de compactarlo: QEMU mantiene un lock de\n"
                "escritura sobre el archivo y el compactado fallaria."
            )
            return

        used_by = e.get("used_by") or []
        warn = ""
        if used_by:
            warn = ("\n\n⚠ Este disco lo usan VMs apagadas: "
                    + ", ".join(used_by) + ".\nSe recomienda hacer un "
                    "backup antes de compactar.")

        ans = QMessageBox.warning(
            self, "Confirmar compactado",
            f"¿Compactar '{name}'?\n\n"
            "Reescribe el QCOW2 eliminando bloques no usados: reduce el\n"
            "archivo en el host SIN cambiar el tamaño virtual que ve el\n"
            "invitado." + warn + "\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        tmp_path = path + ".compact.qcow2"
        try:
            orig_size = os.path.getsize(path)
        except OSError:
            orig_size = 0

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit(f"==> Compactando '{name}'...")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            try:
                proc = subprocess.Popen(
                    ["qemu-img", "convert", "-c", "-O", "qcow2", "-p",
                     path, tmp_path],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            except FileNotFoundError:
                raise RuntimeError("qemu-img no esta en PATH.")
            last_pct = -1
            if proc.stdout is not None:
                for line in iter(proc.stdout.readline, ""):
                    if is_cancelled():
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                        if os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except OSError:
                                pass
                        raise RuntimeError("Compactado cancelado.")
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                    if m:
                        pct = int(float(m.group(1)))
                        if pct != last_pct:
                            last_pct = pct
                            progress_emit(pct, f"Compactando... {pct}%")
            proc.wait()
            if proc.returncode != 0:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                raise RuntimeError(
                    f"qemu-img convert termino con codigo {proc.returncode}."
                )
            try:
                os.replace(tmp_path, path)
            except OSError as ex:
                raise RuntimeError(f"No se pudo reemplazar el archivo: {ex}")
            try:
                new_size = os.path.getsize(path)
            except OSError:
                new_size = 0
            return {"orig": orig_size, "new": new_size}

        def _on_success(res):
            try:
                lib.update_virtual_size(eid)
            except Exception:
                pass
            self.refresh_media_library_table()
            try:
                fo = self._format_bytes_iexport(res["orig"])
                fn = self._format_bytes_iexport(res["new"])
                fs = self._format_bytes_iexport(max(0, res["orig"] - res["new"]))
            except Exception:
                fo, fn, fs = str(res["orig"]), str(res["new"]), "?"
            QMessageBox.information(
                self, "Disco compactado",
                f"'{name}' compactado.\n\n"
                f"Antes: {fo}\nDespués: {fn}\nAhorro: {fs}"
            )

        def _on_error(err):
            QMessageBox.critical(self, "Compactar",
                                 f"No se pudo compactar.\n\n{err}")

        self.run_async(
            _work,
            f"Compactando '{name}'",
            on_success=_on_success,
            on_error=_on_error,
            cancelable=True,
            show_log=True,
            subtitle="Reescribiendo el QCOW2 sin bloques no usados...",
        )

    def verify_media_entry(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "Verificar",
                                    "Selecciona una entrada primero.")
            return
        try:
            r = lib.verify(eid)
        except Exception as e:
            QMessageBox.warning(self, "Verificar", str(e))
            return
        if not r.get("exists"):
            QMessageBox.warning(
                self, "Verificar",
                f"El archivo ya no existe:\n{r.get('path')}"
            )
        elif not r.get("expected"):
            QMessageBox.information(
                self, "Verificar",
                "El archivo existe. No hay sha256 guardado para comparar; "
                "usa 'Calcular SHA256' si quieres uno."
            )
        elif r.get("hash_ok"):
            QMessageBox.information(
                self, "Verificar",
                "Archivo presente y sha256 coincide."
            )
        else:
            QMessageBox.warning(
                self, "Verificar",
                f"sha256 NO coincide.\n\nEsperado: {r.get('expected')}\n"
                f"Actual:   {r.get('actual')}"
            )
        self.refresh_media_library_table()

    def compute_media_sha256(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "SHA256",
                                    "Selecciona una entrada primero.")
            return
        e = lib.get(eid)
        if not e:
            return
        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, "SHA256",
                                f"El archivo no existe:\n{path}")
            return

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit(f"==> Calculando sha256 de {os.path.basename(path)}...")

            def _cb(read, total):
                if total:
                    pct = int(read * 100 / total)
                    progress_emit(pct, f"{pct}% — "
                                       f"{_ml._human_bytes(read)} / "
                                       f"{_ml._human_bytes(total)}")
                else:
                    progress_emit(-1, f"{_ml._human_bytes(read)} leidos")

            digest = _ml.compute_sha256(path, progress_cb=_cb)
            log_emit(f"==> sha256: {digest}")
            return digest

        def _on_success(digest):
            try:
                lib.update(eid, sha256=digest)
            except Exception:
                pass
            self.refresh_media_library_table()
            QMessageBox.information(
                self, "SHA256",
                f"sha256 calculado y guardado:\n\n{digest}"
            )

        def _on_error(err):
            QMessageBox.warning(self, "SHA256", f"Error: {err}")

        try:
            self.run_async(
                _work,
                f"Calculando sha256 — {os.path.basename(path)}",
                on_success=_on_success,
                on_error=_on_error,
                cancelable=True,
                show_log=True,
            )
        except Exception:
            # Fallback sincrono.
            digest = _ml.compute_sha256(path)
            lib.update(eid, sha256=digest)
            self.refresh_media_library_table()
            QMessageBox.information(self, "SHA256", digest)

    # ------------------------------------------------------------------
    # Editar / eliminar / abrir carpeta
    # ------------------------------------------------------------------

    def _on_media_table_double_click(self, item, _col):
        self.edit_media_metadata()

    def edit_media_metadata(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "Editar",
                                    "Selecciona una entrada primero.")
            return
        e = lib.get(eid)
        if not e:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar — {e.get('name','')}")
        dlg.resize(520, 420)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()

        name_edit = QLineEdit(str(e.get("name") or ""))
        form.addRow("Nombre:", name_edit)

        os_combo = QComboBox()
        for label, value in _MEDIA_OS_LABELS[1:]:
            os_combo.addItem(label, value)
        idx = os_combo.findData(str(e.get("os_type") or "other"))
        os_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("SO:", os_combo)

        distro_edit = QLineEdit(str(e.get("distro") or ""))
        form.addRow("Distro:", distro_edit)

        version_edit = QLineEdit(str(e.get("version") or ""))
        form.addRow("Version:", version_edit)

        arch_combo = QComboBox()
        for label, value in _MEDIA_ARCH_LABELS[1:]:
            arch_combo.addItem(label, value)
        idx = arch_combo.findData(str(e.get("arch") or ""))
        arch_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Arquitectura:", arch_combo)

        notes_edit = QPlainTextEdit(str(e.get("notes") or ""))
        notes_edit.setMaximumHeight(80)
        form.addRow("Notas:", notes_edit)

        source_edit = QLineEdit(str(e.get("source_url") or ""))
        form.addRow("URL origen:", source_edit)

        lay.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            lib.update(
                eid,
                name=name_edit.text().strip(),
                os_type=os_combo.currentData(),
                distro=distro_edit.text().strip(),
                version=version_edit.text().strip(),
                arch=arch_combo.currentData() or "",
                notes=notes_edit.toPlainText(),
                source_url=source_edit.text().strip(),
            )
            self.refresh_media_library_table()
        except Exception as ex:
            QMessageBox.warning(self, "Editar", f"No se pudo guardar: {ex}")

    def delete_media_entry(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, "Eliminar",
                                    "Selecciona una entrada primero.")
            return
        e = lib.get(eid)
        if not e:
            return
        filename = str(e.get("filename") or e.get("name") or "?")
        is_external = bool(e.get("external"))

        box = QMessageBox(self)
        box.setWindowTitle("Eliminar entrada")
        box.setText(f"Eliminar '{filename}' de la biblioteca?")
        box.addButton("Quitar del indice", QMessageBox.ButtonRole.AcceptRole)
        if not is_external:
            box.addButton("Eliminar tambien el archivo",
                          QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is None or clicked.text() == "Cancelar":
            return
        delete_file = (clicked.text() == "Eliminar tambien el archivo")
        try:
            lib.remove(eid, delete_file=delete_file)
            self.refresh_media_library_table()
        except Exception as ex:
            QMessageBox.warning(self, "Eliminar", str(ex))

    def open_media_folder(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            return
        e = lib.get(eid)
        if not e:
            return
        path = lib.resolve_path(e)
        folder = os.path.dirname(path) if path else lib.base_dir
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Abrir carpeta",
                                f"La carpeta no existe:\n{folder}")
            return
        try:
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", folder],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.information(self, "Abrir carpeta", folder)
