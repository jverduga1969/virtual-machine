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
    # media_library_host_mount_v1_urgent01: QCheckBox faltaba en el
    # import. Sin esto, _ask_mount_mode() lanzaba NameError al pulsar
    # "Montar en host".
    QCheckBox,
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

# media_library_host_mount_v1: constantes para montar/desmontar
# discos virtuales en el sistema anfitrion.
_MOUNT_STATUS_OK = "\U0001f7e2 "        # circulo verde
_MOUNT_STATUS_RW = "\U0001f7e0 "        # circulo naranja


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
        hdr = QLabel(self.tr(
            "<b>Biblioteca de Medios</b><br>"
            "<span style='color:#666;font-size:11px;'>"
            "Todas las ISOs / IMGs / DMGs que usas con tus VMs, en un "
            "unico sitio. Viven en <code>MediaLibrary/</code> (al mismo "
            "nivel que <code>VirtualMachines/</code>) y se reutilizan "
            "entre maquinas."
            "</span>"
        ))
        hdr.setWordWrap(True)
        parent_layout.addWidget(hdr)

        # --- Fila 1: filtros ---
        filt = QHBoxLayout()
        filt.setSpacing(6)

        self.media_search = QLineEdit()
        self.media_search.setPlaceholderText(self.tr("Buscar por nombre, distro, tag..."))
        self.media_search.setMinimumWidth(220)
        self.media_search.textChanged.connect(self._on_media_search_changed)
        filt.addWidget(self.media_search, 1)

        filt.addWidget(QLabel(self.tr("SO:")))
        self.media_filter_os = QComboBox()
        _os_labels_tr = {
            "Todos": self.tr("Todos"),
            "Guest Tools": self.tr("Guest Tools"),
            "Otros": self.tr("Otros"),
        }
        for label, value in _MEDIA_OS_LABELS:
            self.media_filter_os.addItem(_os_labels_tr.get(label, label), value)
        self.media_filter_os.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_os)

        filt.addWidget(QLabel(self.tr("Arq.:")))
        self.media_filter_arch = QComboBox()
        _arch_labels_tr = {
            "Todas": self.tr("Todas"),
            "Universal": self.tr("Universal"),
            "Sin especificar": self.tr("Sin especificar"),
        }
        for label, value in _MEDIA_ARCH_LABELS:
            self.media_filter_arch.addItem(_arch_labels_tr.get(label, label), value)
        self.media_filter_arch.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_arch)

        filt.addWidget(QLabel(self.tr("Formato:")))
        self.media_filter_kind = QComboBox()
        _kind_labels_tr = {
            "Todos": self.tr("Todos"),
            "Otros": self.tr("Otros"),
        }
        for label, value in _MEDIA_KIND_LABELS:
            self.media_filter_kind.addItem(_kind_labels_tr.get(label, label), value)
        self.media_filter_kind.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_kind)

        # media_library_type_column_v1: filtro por tipo de medio.
        filt.addWidget(QLabel(self.tr("Tipo:")))
        self.media_filter_type = QComboBox()
        self.media_filter_type.addItem(self.tr("Todos"), "")
        self.media_filter_type.addItem(self.tr("Disco duro"), "disk")
        self.media_filter_type.addItem(self.tr("ISO"), "iso")
        self.media_filter_type.addItem(self.tr("Disquete"), "floppy")
        self.media_filter_type.addItem(self.tr("Otro"), "other")
        self.media_filter_type.currentIndexChanged.connect(self._on_media_filter_changed)
        filt.addWidget(self.media_filter_type)

        # media_library_ui_vm_scan_v1: filtro por origen.
        filt.addWidget(QLabel(self.tr("Origen:")))
        self.media_filter_origin = QComboBox()
        self.media_filter_origin.addItem(self.tr("Todos"), "")
        self.media_filter_origin.addItem(self.tr("Manuales"), "manual")
        self.media_filter_origin.addItem(self.tr("De VMs"), "vm")
        self.media_filter_origin.addItem(self.tr("Huerfanas de VM"), "vm_orphan")
        self.media_filter_origin.currentIndexChanged.connect(
            self._on_media_filter_changed
        )
        filt.addWidget(self.media_filter_origin)

        parent_layout.addLayout(filt)

        # --- Fila 2: acciones superiores ---
        acts = QHBoxLayout()
        acts.setSpacing(6)

        self.btn_media_add = QPushButton(self.tr("Anadir archivo(s)"))
        self.btn_media_add.setMinimumHeight(30)
        self.btn_media_add.clicked.connect(self.add_media_from_files)
        acts.addWidget(self.btn_media_add)

        # media_library_create_disk_v1_mixin: crear un disco nuevo
        # directamente en MediaLibrary/.
        self.btn_media_create_disk = QPushButton(
            self.tr("\u2795 Crear disco"))
        self.btn_media_create_disk.setMinimumHeight(30)
        self.btn_media_create_disk.setToolTip(self.tr(
            "Crea un disco virtual nuevo en la biblioteca con\n"
            "'qemu-img create'.\n\n"
            "Formatos soportados: QCOW2, RAW, VMDK, VDI, VHD, VHDX\n"
            "y disquete (IMG). El archivo se guarda en MediaLibrary/\n"
            "y se registra automáticamente en el índice."))
        self.btn_media_create_disk.clicked.connect(
            self.create_medium_in_library)
        acts.addWidget(self.btn_media_create_disk)

        self.btn_media_scan = QPushButton(self.tr("Escanear carpeta"))
        self.btn_media_scan.setMinimumHeight(30)
        self.btn_media_scan.setToolTip(self.tr(
            "Busca archivos de medios dentro de MediaLibrary/ que aun no "
            "esten registrados, y detecta entradas huerfanas (archivo "
            "desaparecido del disco)."
        ))
        self.btn_media_scan.clicked.connect(self.scan_media_library)
        acts.addWidget(self.btn_media_scan)

        # media_library_ui_vm_scan_v1: escaneo de VMs.
        self.btn_media_scan_vms = QPushButton(self.tr("\U0001f50e Escanear VMs"))
        self.btn_media_scan_vms.setMinimumHeight(30)
        self.btn_media_scan_vms.setToolTip(self.tr(
            "Recorre todas las VMs en VirtualMachines/ y registra sus "
            "discos duros, ISOs y disquetes en la biblioteca.\n\n"
            "La misma ISO usada por varias VMs aparece UNA SOLA VEZ, con "
            "todas las VMs en la columna 'Usada por'. Las entradas que ya "
            "no usa ninguna VM se marcan como huerfanas pero no se borran."
        ))
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
        self.media_table.setHeaderLabels([
            self.tr("Nombre"), self.tr("Tipo"), self.tr("SO"),
            self.tr("Version"), self.tr("Arq."),
            self.tr("Tamaño real"), self.tr("Tamaño VM"),
            self.tr("Usada por"), self.tr("Estado"),
            self.tr("Ultimo uso"), self.tr("Ruta"),
        ])
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

        # media_library_host_mount_v1: cada tupla lleva ahora un 4o campo
        # "attr" para que podamos guardar una referencia al boton y
        # habilitarlo/deshabilitarlo segun el estado del disco.
        for label, slot, tip, attr in (
            (self.tr("↗ Agrandar"), self.enlarge_media_entry,
             self.tr("Aumentar el tamaño virtual de un disco QCOW2/RAW de la\n"
                     "biblioteca. Requiere que ninguna VM lo esté usando en\n"
                     "ese momento. El disco solo puede crecer."),
             None),
            (self.tr("🗜 Compactar"), self.compact_media_entry,
             self.tr("Reescribe el QCOW2 sin bloques no usados, reduciendo el\n"
                     "archivo en el host. No cambia el tamaño virtual que ve el\n"
                     "sistema invitado."),
             None),
            # media_library_host_mount_v1: montar/desmontar el disco en el host.
            (self.tr("\U0001f50c Montar en host"), self.mount_media_entry,
             self.tr("Monta este disco virtual en el sistema anfitrión para\n"
                     "inspeccionar o copiar su contenido sin arrancar la VM.\n\n"
                     "Se usa guestmount (FUSE, sin root) si está disponible,\n"
                     "o qemu-nbd (con pkexec) como alternativa.\n\n"
                     "Requiere que ninguna VM que lo use esté encendida:\n"
                     "QEMU mantiene un bloqueo de escritura sobre el archivo."),
             "btn_media_mount"),
            (self.tr("\u23cf Desmontar del host"), self.unmount_media_entry,
             self.tr("Desmonta del sistema anfitrión el disco que se montó\n"
                     "previamente con 'Montar en host'."),
             "btn_media_unmount"),
            (self.tr("Verificar"), self.verify_media_entry,
             self.tr("Comprueba que el archivo exista en disco y, si hay sha256 "
                     "calculado, que coincida."),
             None),
            (self.tr("Calcular SHA256"), self.compute_media_sha256,
             self.tr("Calcula el sha256 del archivo (tarda segun el tamano). "
                     "Util para detectar duplicados o descargas corruptas."),
             None),
            (self.tr("Editar"), self.edit_media_metadata,
             self.tr("Edita los metadatos de la entrada: nombre, distro, version, "
                     "arquitectura, notas, tags y color."),
             None),
            (self.tr("Eliminar"), self.delete_media_entry,
             self.tr("Elimina la entrada del indice. Opcionalmente borra tambien "
                     "el archivo del disco (solo si vive dentro de MediaLibrary/)."),
             None),
            (self.tr("Abrir carpeta"), self.open_media_folder,
             self.tr("Abre la carpeta que contiene el archivo en el explorador "
                     "del sistema."),
             None),
        ):
            b = QPushButton(label)
            b.setMinimumHeight(28)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            acts2.addWidget(b)
            if attr:
                setattr(self, attr, b)
        # media_library_host_mount_v1: estado inicial de los dos botones
        # nuevos, ahora que ya existen.
        try:
            self._update_media_mount_buttons_state()
        except Exception:
            pass

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

        meta_lay.addWidget(QLabel(self.tr("<b>Notas:</b>")), 0, 0, Qt.AlignmentFlag.AlignTop)
        self.media_notes_edit = QPlainTextEdit()
        self.media_notes_edit.setPlaceholderText(self.tr(
            "Notas libres sobre esta entrada (uso previsto, si dio "
            "problemas, driver necesario, etc.)"
        ))
        self.media_notes_edit.setMaximumHeight(70)
        self.media_notes_edit.textChanged.connect(self._on_media_notes_changed)
        meta_lay.addWidget(self.media_notes_edit, 0, 1, 1, 3)

        meta_lay.addWidget(QLabel(self.tr("<b>Tags:</b>")), 1, 0)
        self.media_tags_edit = QLineEdit()
        self.media_tags_edit.setPlaceholderText(self.tr(
            "Separados por coma (ej.: probado, servidor, rapiro)"
        ))
        self.media_tags_edit.editingFinished.connect(self._on_media_tags_changed)
        meta_lay.addWidget(self.media_tags_edit, 1, 1, 1, 3)

        meta_lay.addWidget(QLabel(self.tr("<b>Color:</b>")), 2, 0)
        self.media_color_combo = QComboBox()
        self.media_color_combo.addItem(self.tr("(Sin color)"), "")
        _color_labels_tr = {
            "Rojo": self.tr("Rojo"),
            "Naranja": self.tr("Naranja"),
            "Ambar": self.tr("Ambar"),
            "Verde": self.tr("Verde"),
            "Verde azul": self.tr("Verde azul"),
            "Azul": self.tr("Azul"),
            "Indigo": self.tr("Indigo"),
            "Violeta": self.tr("Violeta"),
            "Rosa": self.tr("Rosa"),
            "Gris": self.tr("Gris"),
        }
        for label, hex_c in _MEDIA_COLOR_PALETTE:
            self.media_color_combo.addItem(_color_labels_tr.get(label, label), hex_c)
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
        # media_library_host_mount_v1: comprobar montajes huerfanos de
        # una sesion anterior (con un retardo, para no bloquear el
        # arranque de la UI).
        try:
            from PyQt6.QtCore import QTimer as _QTimer
            _QTimer.singleShot(1200, self._detect_orphan_mounts_on_start)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Refresco de la tabla
    # ------------------------------------------------------------------

    def refresh_media_library_table(self):
        """Reconstruye la tabla segun filtros y busqueda actuales."""
        if not hasattr(self, "media_table"):
            return
        # media_library_host_mount_v1: validar el estado de montajes
        # antes de pintar la tabla (los que ya no esten montados se
        # limpian solos).
        try:
            self._sync_mounted_media_state()
        except Exception:
            pass
        lib = self._media_library_instance()
        if lib is None:
            self.media_table.clear()
            self.media_count_label.setText(
                self.tr("Biblioteca no disponible.")
            )
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
                _tk = _ml_mod.media_type_key(e)
                tipo_txt = {
                    "disk": self.tr("Disco duro"),
                    "iso": self.tr("ISO"),
                    "floppy": self.tr("Disquete"),
                    "other": self.tr("Otro"),
                }.get(_tk, self.tr("Otro"))
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
        self.media_count_label.setText(self.tr(
            "{0} entrada(s) mostradas de {1} | Tamano total: {2}"
        ).format(
            len(entries), stats.get('total', 0),
            stats.get('size_total_human', '-'),
        ))

        # Restaurar la seleccion si seguia estando.
        if current_id:
            for i in range(self.media_table.topLevelItemCount()):
                row = self.media_table.topLevelItem(i)
                if row.data(0, _MEDIA_USER_ROLE) == current_id:
                    self.media_table.setCurrentItem(row)
                    break
        self._on_media_selection_changed()
        # media_library_host_mount_v1: refrescar el estado de los botones.
        try:
            self._update_media_mount_buttons_state()
        except Exception:
            pass

    def _media_status_for_entry(self, entry):
        """Icono textual del estado de una entrada."""
        # media_library_host_mount_v1: si esta montado en el host, ese
        # estado manda sobre "OK"/"verificado?"/"huerfano".
        try:
            eid = str(entry.get("id") or "")
            self._sync_mounted_media_state()
            info = (self._mounted_media or {}).get(eid)
            if info:
                _mp = info.get("mp") or ""
                if _mp and os.path.ismount(_mp):
                    _mode = (info.get("mode") or "ro").lower()
                    if _mode == "rw":
                        return _MOUNT_STATUS_RW + self.tr("montado (rw)")
                    return _MOUNT_STATUS_OK + self.tr("montado (ro)")
        except Exception:
            pass
        try:
            path_abs = self._media_library_instance().resolve_path(entry)
        except Exception:
            path_abs = ""
        if not path_abs or not os.path.isfile(path_abs):
            return self.tr("huerfano")
        if str(entry.get("sha256") or "").strip():
            return self.tr("verificado?")
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
        # media_library_host_mount_v1: refrescar botones Montar/Desmontar.
        try:
            self._update_media_mount_buttons_state()
        except Exception:
            pass

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
            QMessageBox.warning(self, self.tr("Biblioteca de Medios"),
                                self.tr("La biblioteca no esta disponible."))
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Anadir archivos a la biblioteca"),
            os.path.expanduser("~"),
            self.tr("Imagenes de disco (*.iso *.img *.dmg *.raw *.qcow2 *.qcow);;"
                    "Todos los archivos (*)"),
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
            QMessageBox.warning(self, self.tr("Biblioteca de Medios"),
                                self.tr("La biblioteca no esta disponible."))
            return
        try:
            res = lib.scan_vms()
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Escanear VMs"),
                self.tr("No se pudieron escanear las VMs.\n\n{0}").format(e)
            )
            return
        self.refresh_media_library_table()

        nuevas = int(res.get("nuevas") or 0)
        actualizadas = int(res.get("actualizadas") or 0)
        huerfanas = res.get("huerfanas_de_vm") or []
        total = int(res.get("total_paths") or 0)

        lines = [self.tr(
            "Archivos unicos encontrados en VMs: {0}."
        ).format(total)]
        if nuevas:
            lines.append(self.tr(
                "- {0} medio(s) nuevo(s) anadido(s) a la biblioteca."
            ).format(nuevas))
        if actualizadas:
            lines.append(self.tr(
                "- {0} entrada(s) actualizada(s) con la "
                "lista de VMs que las usan."
            ).format(actualizadas))
        if huerfanas:
            lines.append(self.tr(
                "- {0} entrada(s) ya no las usa ninguna VM "
                "(siguen visibles; filtro Origen = 'Huerfanas de VM')."
            ).format(len(huerfanas)))
        if not (nuevas or actualizadas or huerfanas):
            lines.append(self.tr(
                "Sin cambios: la biblioteca ya estaba al dia."
            ))

        try:
            self.log_message("==> Biblioteca: " + " ".join(lines))
        except Exception:
            pass
        QMessageBox.information(
            self, self.tr("Escanear VMs"), "\n".join(lines)
        )

    def scan_media_library(self):
        lib = self._media_library_instance()
        if lib is None:
            return
        try:
            res = lib.scan()
        except Exception as e:
            QMessageBox.warning(self, self.tr("Escanear"),
                self.tr("No se pudo escanear.\n\n{0}").format(e))
            return
        nuevos = res.get("nuevos") or []
        huerfanos = res.get("huerfanos") or []
        if not nuevos and not huerfanos:
            QMessageBox.information(
                self, self.tr("Escanear"),
                self.tr("No hay archivos nuevos ni entradas huerfanas.")
            )
            return
        msg = []
        if nuevos:
            msg.append(self.tr(
                "{0} archivo(s) nuevos encontrados:"
            ).format(len(nuevos)))
            for n in nuevos[:8]:
                msg.append(f"  - {os.path.basename(n.get('path_abs',''))} "
                           f"[{n.get('os_type','?')}]")
            if len(nuevos) > 8:
                msg.append(self.tr("  ... y {0} mas").format(
                    len(nuevos) - 8))
        if huerfanos:
            msg.append("")
            msg.append(self.tr(
                "{0} entrada(s) huerfanas (archivo ya no existe):"
            ).format(len(huerfanos)))
            for h in huerfanos[:8]:
                msg.append(f"  - {h.get('name') or h.get('filename','?')}")
            if len(huerfanos) > 8:
                msg.append(self.tr("  ... y {0} mas").format(
                    len(huerfanos) - 8))
        msg.append("")
        if nuevos:
            msg.append(self.tr("Anadir los archivos nuevos a la biblioteca?"))
            r = QMessageBox.question(
                self, self.tr("Escanear"),
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
            QMessageBox.information(self, self.tr("Escanear"), "\n".join(msg))
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
            QMessageBox.information(self, self.tr("Agrandar"),
                                    self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return

        try:
            import media_library as _ml_mod
            if _ml_mod.media_type_key(e) != "disk":
                QMessageBox.information(
                    self, self.tr("Agrandar"),
                    self.tr("Solo se pueden agrandar discos duros (QCOW2/RAW).")
                )
                return
        except Exception:
            pass

        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, self.tr("Agrandar"),
                self.tr("El archivo no existe:\n{0}").format(path))
            return

        running = self._media_entry_in_use_by_running_vm(e)
        if running:
            QMessageBox.warning(
                self, self.tr("Agrandar"),
                self.tr("Este disco lo usa la VM '{0}', que esta encendida."
                        "\n\nApagala antes de agrandarlo.").format(running)
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
        dlg.setWindowTitle(self.tr("↗ Agrandar disco"))
        dlg.resize(520, 260)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()
        form.addRow(self.tr("Archivo:"), QLabel(os.path.basename(path)))
        form.addRow(self.tr("Tamaño actual:"), QLabel(cur_txt))
        size_edit = QLineEdit(cur_qemu)
        size_edit.setPlaceholderText(
            self.tr("Ejemplo: 120G (solo crecer)"))
        form.addRow(self.tr("Nuevo tamaño:"), size_edit)
        lay.addLayout(form)

        hint = QLabel(self.tr(
            "El disco solo puede CRECER. Agrandar el archivo NO agranda\n"
            "la partición dentro del guest: hay que ampliarla también desde\n"
            "el sistema invitado para aprovechar el nuevo espacio."
        ))
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
                QMessageBox.warning(dlg, self.tr("Tamaño inválido"),
                    self.tr("'{0}' no es un tamaño válido.").format(txt))
                size_edit.setText(cur_qemu)
                return
            if new_b < _cur:
                QMessageBox.warning(
                    dlg, self.tr("No se puede encoger"),
                    self.tr("Actual: {0}, indicado {1}.\n\n"
                            "El valor se ha restaurado al tamaño actual."
                            ).format(cur_txt, txt)
                )
                size_edit.setText(cur_qemu)
                return
            dlg.accept()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_b = QPushButton(self.tr("Cancelar"))
        ok_b = QPushButton(self.tr("Aplicar"))
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
            QMessageBox.critical(self, self.tr("Agrandar"),
                self.tr("No se pudo agrandar el disco.\n\n{0}").format(ex))
            return
        try:
            lib.update_virtual_size(eid)
        except Exception:
            pass
        self.refresh_media_library_table()
        QMessageBox.information(
            self, self.tr("Disco agrandado"),
            self.tr("Se agrandó correctamente a {0}.\n\n"
                    "Recuerda ampliar también la partición dentro del "
                    "sistema invitado.").format(new_txt)
        )

    def compact_media_entry(self):
        """Compacta un disco QCOW2 de la biblioteca."""
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, self.tr("Compactar"),
                                    self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return
        if not self._is_qcow2_disk(e):
            QMessageBox.information(
                self, self.tr("Compactar"),
                self.tr("Solo se pueden compactar discos en formato QCOW2.")
            )
            return
        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, self.tr("Compactar"),
                self.tr("El archivo no existe:\n{0}").format(path))
            return
        name = os.path.basename(path)

        running = self._media_entry_in_use_by_running_vm(e)
        if running:
            QMessageBox.warning(
                self, self.tr("Compactar"),
                self.tr("Este disco lo usa la VM '{0}', que esta encendida."
                        "\n\nApagala antes de compactarlo: QEMU mantiene "
                        "un lock de\nescritura sobre el archivo y el "
                        "compactado fallaria.").format(running)
            )
            return

        used_by = e.get("used_by") or []
        warn = ""
        if used_by:
            warn = self.tr(
                "\n\n⚠ Este disco lo usan VMs apagadas: {0}.\n"
                "Se recomienda hacer un backup antes de compactar."
            ).format(", ".join(used_by))

        ans = QMessageBox.warning(
            self, self.tr("Confirmar compactado"),
            self.tr("¿Compactar '{0}'?\n\n"
                    "Reescribe el QCOW2 eliminando bloques no usados: "
                    "reduce el\narchivo en el host SIN cambiar el tamaño "
                    "virtual que ve el\ninvitado.{1}\n\n¿Continuar?"
                    ).format(name, warn),
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
                            progress_emit(pct, self.tr("Compactando... {0}%"
                                                       ).format(pct))
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
                self, self.tr("Disco compactado"),
                self.tr("'{0}' compactado.\n\n"
                        "Antes: {1}\nDespués: {2}\nAhorro: {3}"
                        ).format(name, fo, fn, fs)
            )

        def _on_error(err):
            QMessageBox.critical(self, self.tr("Compactar"),
                self.tr("No se pudo compactar.\n\n{0}").format(err))

        self.run_async(
            _work,
            self.tr("Compactando '{0}'").format(name),
            on_success=_on_success,
            on_error=_on_error,
            cancelable=True,
            show_log=True,
            subtitle=self.tr(
                "Reescribiendo el QCOW2 sin bloques no usados..."),
        )

    def verify_media_entry(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, self.tr("Verificar"),
                                    self.tr("Selecciona una entrada primero."))
            return
        try:
            r = lib.verify(eid)
        except Exception as e:
            QMessageBox.warning(self, self.tr("Verificar"), str(e))
            return
        if not r.get("exists"):
            QMessageBox.warning(
                self, self.tr("Verificar"),
                self.tr("El archivo ya no existe:\n{0}"
                        ).format(r.get('path'))
            )
        elif not r.get("expected"):
            QMessageBox.information(
                self, self.tr("Verificar"),
                self.tr("El archivo existe. No hay sha256 guardado para "
                        "comparar; usa 'Calcular SHA256' si quieres uno.")
            )
        elif r.get("hash_ok"):
            QMessageBox.information(
                self, self.tr("Verificar"),
                self.tr("Archivo presente y sha256 coincide.")
            )
        else:
            QMessageBox.warning(
                self, self.tr("Verificar"),
                self.tr("sha256 NO coincide.\n\nEsperado: {0}\n"
                        "Actual:   {1}").format(r.get('expected'),
                                                r.get('actual'))
            )
        self.refresh_media_library_table()

    def compute_media_sha256(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, self.tr("SHA256"),
                                    self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return
        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, self.tr("SHA256"),
                self.tr("El archivo no existe:\n{0}").format(path))
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
                self, self.tr("SHA256"),
                self.tr("sha256 calculado y guardado:\n\n{0}"
                        ).format(digest)
            )

        def _on_error(err):
            QMessageBox.warning(self, self.tr("SHA256"),
                self.tr("Error: {0}").format(err))

        try:
            self.run_async(
                _work,
                self.tr("Calculando sha256 — {0}").format(
                    os.path.basename(path)),
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
            QMessageBox.information(self, self.tr("SHA256"), digest)

    # ------------------------------------------------------------------
    # Editar / eliminar / abrir carpeta
    # ------------------------------------------------------------------

    def _on_media_table_double_click(self, item, _col):
        self.edit_media_metadata()

    def edit_media_metadata(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, self.tr("Editar"),
                                    self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Editar — {0}").format(e.get('name','')))
        dlg.resize(520, 420)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()

        name_edit = QLineEdit(str(e.get("name") or ""))
        form.addRow(self.tr("Nombre:"), name_edit)

        os_combo = QComboBox()
        _os_labels_tr = {
            "Todos": self.tr("Todos"),
            "Guest Tools": self.tr("Guest Tools"),
            "Otros": self.tr("Otros"),
        }
        for label, value in _MEDIA_OS_LABELS[1:]:
            os_combo.addItem(_os_labels_tr.get(label, label), value)
        idx = os_combo.findData(str(e.get("os_type") or "other"))
        os_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(self.tr("SO:"), os_combo)

        distro_edit = QLineEdit(str(e.get("distro") or ""))
        form.addRow(self.tr("Distro:"), distro_edit)

        version_edit = QLineEdit(str(e.get("version") or ""))
        form.addRow(self.tr("Version:"), version_edit)

        arch_combo = QComboBox()
        _arch_labels_tr = {
            "Todas": self.tr("Todas"),
            "Universal": self.tr("Universal"),
            "Sin especificar": self.tr("Sin especificar"),
        }
        for label, value in _MEDIA_ARCH_LABELS[1:]:
            arch_combo.addItem(_arch_labels_tr.get(label, label), value)
        idx = arch_combo.findData(str(e.get("arch") or ""))
        arch_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(self.tr("Arquitectura:"), arch_combo)

        notes_edit = QPlainTextEdit(str(e.get("notes") or ""))
        notes_edit.setMaximumHeight(80)
        form.addRow(self.tr("Notas:"), notes_edit)

        source_edit = QLineEdit(str(e.get("source_url") or ""))
        form.addRow(self.tr("URL origen:"), source_edit)

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
            QMessageBox.warning(self, self.tr("Editar"),
                self.tr("No se pudo guardar: {0}").format(ex))

    def delete_media_entry(self):
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(self, self.tr("Eliminar"),
                                    self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return
        filename = str(e.get("filename") or e.get("name") or "?")
        is_external = bool(e.get("external"))

        box = QMessageBox(self)
        box.setWindowTitle(self.tr("Eliminar entrada"))
        box.setText(self.tr(
            "Eliminar '{0}' de la biblioteca?").format(filename))
        _btn_idx = self.tr("Quitar del indice")
        _btn_file = self.tr("Eliminar tambien el archivo")
        _btn_cancel = self.tr("Cancelar")
        box.addButton(_btn_idx, QMessageBox.ButtonRole.AcceptRole)
        if not is_external:
            box.addButton(_btn_file,
                          QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(_btn_cancel, QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is None or clicked.text() == _btn_cancel:
            return
        delete_file = (clicked.text() == _btn_file)
        try:
            lib.remove(eid, delete_file=delete_file)
            self.refresh_media_library_table()
        except Exception as ex:
            QMessageBox.warning(self, self.tr("Eliminar"), str(ex))

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
            QMessageBox.warning(self, self.tr("Abrir carpeta"),
                self.tr("La carpeta no existe:\n{0}").format(folder))
            return
        try:
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", folder],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.information(self, self.tr("Abrir carpeta"), folder)


    # ------------------------------------------------------------------
    # media_library_host_mount_v1: montar/desmontar discos en el host
    # ------------------------------------------------------------------
    # Monta un disco virtual (QCOW2/RAW/VMDK/VDI/VHD/VHDX) en el sistema
    # anfitrion para inspeccionar o copiar su contenido sin arrancar la
    # VM. No toca ninguna VM: solo habilita el contenido al host.
    #
    # Backend preferido: guestmount (libguestfs, FUSE, sin root,
    #   detecta particiones y sistemas de archivos automaticamente).
    # Fallback: qemu-nbd + mount (necesita root via pkexec, monta la
    #   primera particion o el disco entero).
    #
    # Estado por entrada (self._mounted_media[eid]):
    #   {
    #     "mp": "/home/user/.local/share/virtual-machine/mounts/<eid>",
    #     "mode": "ro" | "rw",
    #     "backend": "guestmount" | "qemu_nbd",
    #     "nbd_index": "0"  # solo si backend == qemu_nbd
    #   }
    #
    # El estado se valida contra os.path.ismount() en cada refresco de
    # la tabla; si el usuario desmonto a mano con `fusermount -u` o
    # `umount`, la entrada se limpia sola sin error.

    def _mount_dir_root(self):
        """Directorio raiz donde se crean los puntos de montaje."""
        xdg = (os.environ.get("XDG_DATA_HOME")
               or os.path.expanduser("~/.local/share"))
        root = os.path.join(xdg, "virtual-machine", "mounts")
        try:
            os.makedirs(root, exist_ok=True)
        except OSError:
            pass
        return root

    @staticmethod
    def _sanitize_mount_dir_name(name, fallback="disco"):
        """Sanea el nombre de una entrada para usarlo como carpeta.

        Marcador: media_library_host_mount_v1_friendly_mp.
        Deja solo [A-Za-z0-9._-], sustituye espacios por _, quita
        acentos, y limita a 40 chars. Si queda vacio usa fallback.
        """
        import unicodedata as _ud
        s = str(name or "").strip()
        # Quitar acentos (NFKD normaliza y luego quitamos comb marks).
        try:
            s = _ud.normalize("NFKD", s)
            s = "".join(c for c in s if not _ud.combining(c))
        except Exception:
            pass
        s = s.replace(" ", "_")
        # Descartar cualquier caracter no permitido.
        s = "".join(c if (c.isalnum() or c in "._-") else "_" for c in s)
        s = s.strip("._-")[:40]
        return s or fallback

    def _mount_dir_for(self, entry):
        """Devuelve el punto de montaje legible para una entrada.

        Formato: <nombre_saneado>-<eid[:8]>.
        El sufijo corto del id evita colisiones cuando dos entradas
        tienen el mismo nombre. Ej: "hd_mint-a1b2c3d4".
        """
        eid = str((entry or {}).get("id") or "")
        name = (entry or {}).get("name") or (entry or {}).get("filename") or ""
        safe = self._sanitize_mount_dir_name(name, "disco")
        short = eid[3:11] if eid.startswith("ml_") else eid[:8]
        suffix = ("-" + short) if short else ""
        return os.path.join(self._mount_dir_root(), safe + suffix)

    def _mount_tools_status(self):
        """Devuelve dict con las herramientas de montaje disponibles."""
        gm = shutil.which("guestmount")
        qn = shutil.which("qemu-nbd")
        pk = shutil.which("pkexec")
        return {
            "guestmount": gm,
            "qemu_nbd": qn,
            "pkexec": pk,
            "any": bool(gm or (qn and pk)),
        }

    def _offer_install_mount_tools(self):
        """Ofrece instalar libguestfs+guestfs-tools (o qemu-nbd).
        Devuelve True si la instalacion termino con exito."""
        pm = None
        pkgs = []
        for cmd, cand in (
            ("pacman",   ["libguestfs", "guestfs-tools"]),
            ("apt",      ["libguestfs-tools"]),
            ("apt-get",  ["libguestfs-tools"]),
            ("dnf",      ["libguestfs-tools-c", "libguestfs-tools"]),
            ("zypper",   ["guestfs-tools"]),
        ):
            if shutil.which(cmd):
                pm = cmd
                pkgs = cand
                break
        if pm is None:
            QMessageBox.information(
                self, self.tr("Herramientas de montaje"),
                self.tr(
                    "No se encontró guestmount ni qemu-nbd en el sistema.\n\n"
                    "Instala 'libguestfs' y 'guestfs-tools' (o 'qemu-nbd'\n"
                    "como alternativa) con el gestor de paquetes de tu\n"
                    "distribución para poder montar discos virtuales.")
            )
            return False
        if not shutil.which("pkexec"):
            QMessageBox.information(
                self, self.tr("Herramientas de montaje"),
                self.tr(
                    "Faltan las herramientas de montaje y no se encontró\n"
                    "'pkexec' para pedir permisos de administrador.\n\n"
                    "Ejecuta a mano:\n\n"
                    "  sudo {0} install {1}").format(pm, " ".join(pkgs)))
            return False
        if pm == "pacman":
            cmd = ["pkexec", pm, "-S", "--noconfirm"] + pkgs
        elif pm == "zypper":
            cmd = ["pkexec", pm, "-n", "install"] + pkgs
        else:
            cmd = ["pkexec", pm, "install", "-y"] + pkgs
        resp = QMessageBox.question(
            self, self.tr("Herramientas de montaje"),
            self.tr(
                "Se necesitan herramientas adicionales para montar discos\n"
                "en el host.\n\n"
                "  • guestmount (libguestfs) es lo ideal: sin root, detecta\n"
                "    particiones y sistemas de archivos automáticamente.\n"
                "  • qemu-nbd es la alternativa si no hay libguestfs.\n\n"
                "¿Quieres instalar las herramientas ahora? Se pedirá la\n"
                "contraseña de administrador.\n\n"
                "Comando:\n  {0}").format(" ".join(cmd)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return False
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Herramientas de montaje"),
                self.tr("No se pudo ejecutar el comando de instalación.\n\n{0}").format(e)
            )
            return False
        if r.returncode != 0:
            QMessageBox.critical(
                self, self.tr("Herramientas de montaje"),
                self.tr("La instalación falló.\n\n{0}").format(
                    (r.stderr or r.stdout or "(sin salida)")[-500:])
            )
            return False
        QMessageBox.information(
            self, self.tr("Herramientas de montaje"),
            self.tr("Instalación completada."))
        return True

    def _sync_mounted_media_state(self):
        """Valida self._mounted_media contra el estado real del sistema.

        Si un punto de montaje ya no esta montado (el usuario lo
        desmonto a mano, o el proceso murio), se limpia del dict y se
        intenta borrar el directorio vacio.
        """
        if not hasattr(self, "_mounted_media"):
            self._mounted_media = {}
            return
        stale = []
        for eid, info in list(self._mounted_media.items()):
            mp = (info or {}).get("mp") or ""
            if not mp or not os.path.ismount(mp):
                stale.append((eid, mp))
        for eid, mp in stale:
            self._mounted_media.pop(eid, None)
            if mp:
                try:
                    os.rmdir(mp)
                except OSError:
                    pass

    def _detect_orphan_mounts_on_start(self):
        """Busca montajes huerfanos de una sesion anterior.

        Se llama una vez por arranque (con un QTimer.singleShot para no
        bloquear la construccion inicial de la UI). Si hay montajes
        vivos, ofrece desmontarlos; si el usuario dice 'No', no se
        vuelve a preguntar en esta sesion.
        """
        if getattr(self, "_orphans_checked", False):
            return
        self._orphans_checked = True
        root = self._mount_dir_root()
        orphans = []
        try:
            for name in os.listdir(root):
                sub = os.path.join(root, name)
                if not os.path.isdir(sub):
                    continue
                if os.path.ismount(sub):
                    orphans.append(sub)
                else:
                    try:
                        os.rmdir(sub)
                    except OSError:
                        pass
        except OSError:
            return
        if not orphans or getattr(self, "_orphans_ignored", False):
            return
        try:
            self._offer_orphan_cleanup(orphans)
        except Exception as e:
            self._media_mount_log_exc("detect_orphan_mounts", e)

    def _offer_orphan_cleanup(self, orphans):
        """Cuerpo real, separado para que las excepciones no maten
        el callback del QTimer."""
        resp = QMessageBox.question(
            self, self.tr("Montajes previos detectados"),
            self.tr(
                "Se encontraron {0} disco(s) montados en el sistema de\n"
                "una sesión anterior de la aplicación:\n\n"
                "{1}\n\n"
                "¿Quieres desmontarlos ahora?").format(
                    len(orphans), "\n".join(orphans)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            self._orphans_ignored = True
            return
        for mp in orphans:
            try:
                subprocess.run(["fusermount", "-u", mp],
                               capture_output=True, text=True, timeout=15)
            except Exception:
                pass
            if os.path.ismount(mp):
                try:
                    subprocess.run(["pkexec", "umount", mp],
                                   capture_output=True, text=True, timeout=60)
                except Exception:
                    pass
            if not os.path.ismount(mp):
                try:
                    os.rmdir(mp)
                except OSError:
                    pass

    def _ask_mount_mode(self, entry_name):
        """Pregunta ro/rw antes de montar. Devuelve 'ro', 'rw' o None."""
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Montar en el host"))
        dlg.setModal(True)
        dlg.resize(560, 280)
        lay = QVBoxLayout(dlg)
        info = QLabel(self.tr(
            "Se va a montar <b>{0}</b> en el sistema anfitrión.<br><br>"
            "El disco debe estar apagado: ninguna VM que lo use puede\n"
            "estar encendida, porque QEMU mantiene un bloqueo de escritura\n"
            "sobre el archivo.").format(entry_name))
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        lay.addWidget(info)
        chk_rw = QCheckBox(self.tr(
            "Permitir escritura (montar en modo read-write)"))
        chk_rw.setChecked(False)
        lay.addWidget(chk_rw)
        warn = QLabel(self.tr(
            "⚠ Con read-write, escribir en el disco puede corromper el\n"
            "sistema de archivos si después se arranca la VM sin\n"
            "desmontarlo. Para inspeccionar o copiar, deja read-only.\n\n"
            "Los archivos que crees desde el host se atribuirán a tu\n"
            "usuario del guest (uid/gid {0}:{1}) cuando el sistema de\n"
            "archivos lo permita; si no, aparecerán como root.").format(
                os.getuid(), os.getgid()))
        warn.setWordWrap(True)
        warn.setStyleSheet("color:#b36b00; font-size:11px;")
        lay.addWidget(warn)
        lay.addStretch(1)
        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        ok = QPushButton(self.tr("Montar"))
        ok.setDefault(True)
        cancel.clicked.connect(dlg.reject)
        ok.clicked.connect(dlg.accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return "rw" if chk_rw.isChecked() else "ro"

    def _update_media_mount_buttons_state(self):
        """Habilita/deshabilita y reescribe tooltips de Montar/Desmontar."""
        btn_m = getattr(self, "btn_media_mount", None)
        btn_u = getattr(self, "btn_media_unmount", None)
        if btn_m is None or btn_u is None:
            return
        try:
            lib = self._media_library_instance()
            eid = self._media_selected_id()
            e = lib.get(eid) if (lib and eid) else None
            if not e:
                btn_m.setEnabled(False)
                btn_u.setEnabled(False)
                btn_m.setToolTip(self.tr(
                    "Selecciona un disco virtual para montarlo en el host."))
                btn_u.setToolTip(self.tr(
                    "Selecciona un disco previamente montado para desmontarlo."))
                return
            try:
                import media_library as _ml_mod
                is_disk = (_ml_mod.media_type_key(e) == "disk")
            except Exception:
                is_disk = False
            self._sync_mounted_media_state()
            is_mounted = eid in self._mounted_media
            running = self._media_entry_in_use_by_running_vm(e)
            btn_m.setEnabled(bool(is_disk and not is_mounted and not running))
            btn_u.setEnabled(bool(is_mounted))
            if not is_disk:
                btn_m.setToolTip(self.tr(
                    "Solo se pueden montar discos virtuales\n"
                    "(QCOW2, RAW, VMDK, VDI, VHD, VHDX)."))
            elif is_mounted:
                btn_m.setToolTip(self.tr(
                    "Este disco ya está montado. Usa '⏏ Desmontar del host'\n"
                    "para liberarlo."))
            elif running:
                btn_m.setToolTip(self.tr(
                    "La VM '{0}' está usando este disco y está encendida.\n"
                    "Apágala para poder montarlo en el host.").format(running))
            else:
                btn_m.setToolTip(self.tr(
                    "Monta este disco virtual en el sistema anfitrión para\n"
                    "inspeccionar o copiar su contenido sin arrancar la VM."))
            if is_mounted:
                _mp = (self._mounted_media.get(eid) or {}).get("mp") or ""
                btn_u.setToolTip(self.tr("Desmontar de {0}").format(_mp))
            else:
                btn_u.setToolTip(self.tr(
                    "Este disco no está montado en el host."))
        except Exception:
            try:
                btn_m.setEnabled(False)
                btn_u.setEnabled(False)
            except Exception:
                pass

    def _media_mount_log_exc(self, ctx, exc):
        """Loguea una excepcion a la consola de progreso SIN propagarla.

        Marcador: media_library_host_mount_v1_urgent01. Los slots de
        los botones nuevos no deben poder tumbar la app: cualquier
        excepcion se registra con traceback y se sigue.
        """
        try:
            import traceback as _tb
            self.log_message(
                "[ERROR] {}: {}".format(ctx, exc)
            )
            for line in _tb.format_exc().splitlines():
                self.log_message("    " + line)
        except Exception:
            import sys as _sys
            print("[ERROR] {}: {}".format(ctx, exc), file=_sys.stderr)

    def mount_media_entry(self):
        """Monta el disco seleccionado en el sistema anfitrion."""
        try:
            self._mount_media_entry_impl()
        except Exception as e:
            self._media_mount_log_exc("mount_media_entry", e)
            try:
                QMessageBox.critical(
                    self, self.tr("Montar en host"),
                    self.tr("Error inesperado al montar el disco.\n\n"
                            "Puedes ver el detalle en la Consola de Progreso.\n\n"
                            "{0}").format(e))
            except Exception:
                pass

    def _mount_media_entry_impl(self):
        """Cuerpo real de mount_media_entry (sin try global)."""
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(
                self, self.tr("Montar en host"),
                self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return
        try:
            import media_library as _ml_mod
            if _ml_mod.media_type_key(e) != "disk":
                QMessageBox.information(
                    self, self.tr("Montar en host"),
                    self.tr("Solo se pueden montar discos virtuales\n"
                            "(QCOW2, RAW, VMDK, VDI, VHD, VHDX)."))
                return
        except Exception:
            pass

        self._sync_mounted_media_state()
        if eid in self._mounted_media:
            QMessageBox.information(
                self, self.tr("Montar en host"),
                self.tr("Este disco ya está montado."))
            return

        running_vm = self._media_entry_in_use_by_running_vm(e)
        if running_vm:
            QMessageBox.warning(
                self, self.tr("Montar en host"),
                self.tr("La VM '{0}' está usando este disco y está encendida.\n\n"
                        "Apágala antes de montar el disco en el host: QEMU\n"
                        "mantiene un bloqueo de escritura sobre el archivo\n"
                        "y el montaje fallaría.").format(running_vm))
            return

        path = lib.resolve_path(e)
        if not path or not os.path.isfile(path):
            QMessageBox.warning(
                self, self.tr("Montar en host"),
                self.tr("El archivo no existe:\n{0}").format(path))
            return

        tools = self._mount_tools_status()
        if not tools.get("any"):
            if not self._offer_install_mount_tools():
                return
            tools = self._mount_tools_status()
            if not tools.get("any"):
                QMessageBox.warning(
                    self, self.tr("Montar en host"),
                    self.tr("Las herramientas de montaje siguen sin estar\n"
                            "disponibles después de la instalación."))
                return

        name = os.path.basename(path)
        mode = self._ask_mount_mode(name)
        if mode is None:
            return

        # media_library_host_mount_v1_friendly_mp: nombre legible
        # <nombre_disco>-<eid[:8]> en vez del id crudo.
        mp = self._mount_dir_for(e)
        try:
            os.makedirs(mp, exist_ok=True)
        except OSError as e_mk:
            QMessageBox.critical(
                self, self.tr("Montar en host"),
                self.tr("No se pudo crear el punto de montaje.\n\n{0}").format(e_mk))
            return

        backend = "guestmount" if tools.get("guestmount") else "qemu_nbd"

        def _work(log_emit, is_cancelled, progress_emit):
            log_emit("==> Montando '{}' en {} (modo {}, {}).".format(
                name, mp, mode, backend))
            if backend == "guestmount":
                # media_library_host_mount_v1_uid_gid: en RW, mapear
                # uid/gid del usuario del host. Sin esto, los archivos
                # que se creen desde el host aparecen en el guest con
                # propietario root (libguestfs ejecuta la mini-VM como
                # root), y el usuario no puede tocarlos dentro del
                # sistema invitado.
                _uid = -1
                _gid = -1
                if mode == "rw":
                    try:
                        _uid = os.getuid()
                        _gid = os.getgid()
                    except Exception:
                        _uid = _gid = -1

                cmd = ["guestmount", "-a", path, "-i"]
                if mode == "ro":
                    cmd.append("--ro")
                if mode == "rw" and _uid >= 0:
                    cmd += ["-o", "uid={},gid={}".format(_uid, _gid)]
                cmd.append(mp)
                log_emit("==> " + " ".join(cmd))
                r = subprocess.run(cmd, capture_output=True,
                                    text=True, timeout=180)

                # Fallback: si falla con uid/gid (FS sin soporte, p.ej.
                # vfat sin umask), reintentar sin el mapeo.
                _uid_mapped = True
                if r.returncode != 0 and mode == "rw" and _uid >= 0:
                    log_emit("[AVISO] guestmount con -o uid/gid falló; "
                             "reintentando sin mapeo de usuario.")
                    cmd2 = ["guestmount", "-a", path, "-i", mp]
                    log_emit("==> " + " ".join(cmd2))
                    r = subprocess.run(cmd2, capture_output=True,
                                       text=True, timeout=180)
                    _uid_mapped = False

                if r.returncode != 0:
                    raise RuntimeError(
                        (r.stderr or r.stdout or "guestmount falló").strip())
                if mode == "rw" and _uid_mapped:
                    log_emit("==> Montado con guestmount en {} "
                             "(uid={}, gid={}).".format(mp, _uid, _gid))
                elif mode == "rw":
                    log_emit("==> Montado con guestmount en {} "
                             "(sin mapeo de uid/gid; los archivos "
                             "nuevos aparecerán como root en el guest)."
                             .format(mp))
                else:
                    log_emit("==> Montado con guestmount en {} (read-only)."
                             .format(mp))
                return {"backend": "guestmount", "mp": mp, "mode": mode,
                        "uid_mapped": _uid_mapped}
            # qemu_nbd: necesita pkexec.
            _ro_opt = "-o ro " if mode == "ro" else ""
            script = (
                "set -e; "
                "modprobe nbd max_part=16; "
                "NBD=''; "
                "for i in 0 1 2 3 4 5 6 7 8 9; do "
                "  if [ ! -e /sys/block/nbd$i/pid ] || "
                "     ! kill -0 $(cat /sys/block/nbd$i/pid) 2>/dev/null; then "
                "    NBD=$i; break; fi; done; "
                "[ -n \"$NBD\" ] || { echo 'sin /dev/nbdN libre'; exit 1; }; "
                "qemu-nbd --connect=/dev/nbd$NBD " + chr(39) + path + chr(39) + "; "
                "sleep 1; "
                "DEV=/dev/nbd${NBD}p1; "
                "[ -b $DEV ] || DEV=/dev/nbd${NBD}; "
                "mount " + _ro_opt + "$DEV " + chr(39) + mp + chr(39) + "; "
                "echo \"$NBD\" > " + chr(39) + mp + "/.nbd_index" + chr(39)
            )
            log_emit("==> Ejecutando: pkexec bash -c '...' (se pedirá contraseña).")
            r = subprocess.run(
                ["pkexec", "bash", "-c", script],
                capture_output=True, text=True, timeout=240)
            if r.returncode != 0:
                raise RuntimeError(
                    (r.stderr or r.stdout or "qemu-nbd falló").strip())
            nbd_idx = ""
            try:
                with open(os.path.join(mp, ".nbd_index")) as f:
                    nbd_idx = f.read().strip()
                os.remove(os.path.join(mp, ".nbd_index"))
            except Exception:
                pass
            log_emit("==> Montado con qemu-nbd (nbd{}) en {}.".format(nbd_idx, mp))
            return {"backend": "qemu_nbd", "mp": mp, "mode": mode,
                    "nbd_index": nbd_idx}

        def _on_success(res):
            if not isinstance(res, dict):
                return
            if not hasattr(self, "_mounted_media"):
                self._mounted_media = {}
            self._mounted_media[eid] = res
            try:
                self.refresh_media_library_table()
            except Exception:
                pass
            _warn_uid = ""
            if mode == "rw" and res.get("uid_mapped") is False:
                _warn_uid = "\n\n" + self.tr(
                    "Aviso: el sistema de archivos del guest no acepta "
                    "mapeo de usuario; los archivos que crees desde el "
                    "host aparecerán como root en el guest. Para "
                    "trabajar sin problemas de permisos, escribe desde "
                    "el guest en lugar del host.")
            QMessageBox.information(
                self, self.tr("Disco montado"),
                self.tr("'{0}' montado correctamente.\n\n"
                        "Punto de montaje: {1}\n"
                        "Modo: {2}{3}").format(
                    name, res["mp"],
                    self.tr("read-only") if mode == "ro" else self.tr("read-write"),
                    _warn_uid))

        def _on_error(err):
            try:
                os.rmdir(mp)
            except OSError:
                pass
            QMessageBox.critical(
                self, self.tr("Montar en host"),
                self.tr("No se pudo montar el disco.\n\n{0}").format(err))

        self.run_async(
            _work,
            self.tr("Montando '{0}'").format(name),
            on_success=_on_success,
            on_error=_on_error,
            cancelable=False,
            show_log=True,
            subtitle=self.tr("Preparando el punto de montaje en el host…"),
        )

    def unmount_media_entry(self):
        """Desmonta del host el disco seleccionado."""
        try:
            self._unmount_media_entry_impl()
        except Exception as e:
            self._media_mount_log_exc("unmount_media_entry", e)
            try:
                QMessageBox.critical(
                    self, self.tr("Desmontar del host"),
                    self.tr("Error inesperado al desmontar.\n\n"
                            "Puedes ver el detalle en la Consola de Progreso.\n\n"
                            "{0}").format(e))
            except Exception:
                pass

    def _unmount_media_entry_impl(self):
        """Cuerpo real de unmount_media_entry (sin try global)."""
        lib = self._media_library_instance()
        eid = self._media_selected_id()
        if lib is None or not eid:
            QMessageBox.information(
                self, self.tr("Desmontar del host"),
                self.tr("Selecciona una entrada primero."))
            return
        e = lib.get(eid)
        if not e:
            return
        self._sync_mounted_media_state()
        info = self._mounted_media.get(eid)
        if not info:
            QMessageBox.information(
                self, self.tr("Desmontar del host"),
                self.tr("Este disco no está montado en el host."))
            return
        mp = info.get("mp") or ""
        if not mp or not os.path.ismount(mp):
            self._mounted_media.pop(eid, None)
            try:
                self.refresh_media_library_table()
            except Exception:
                pass
            return
        backend = info.get("backend") or "guestmount"
        nbd_idx = info.get("nbd_index") or ""
        name = os.path.basename(lib.resolve_path(e)) or str(e.get("name") or "?")

        resp = QMessageBox.question(
            self, self.tr("Desmontar del host"),
            self.tr("¿Desmontar '{0}' de {1}?").format(name, mp),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        def _work(log_emit, is_cancelled, progress_emit):
            if backend == "guestmount":
                cmd = ["fusermount", "-u", mp]
                log_emit("==> " + " ".join(cmd))
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if r.returncode != 0:
                    log_emit("[AVISO] fusermount falló; probando pkexec umount.")
                    r = subprocess.run(
                        ["pkexec", "umount", mp],
                        capture_output=True, text=True, timeout=120)
                    if r.returncode != 0:
                        raise RuntimeError(
                            (r.stderr or r.stdout or "no se pudo desmontar").strip())
            else:
                script = "umount " + chr(39) + mp + chr(39) + "; "
                if nbd_idx:
                    script += "qemu-nbd --disconnect /dev/nbd" + str(nbd_idx) + "; "
                log_emit("==> Ejecutando: pkexec bash -c '...' (se pedirá contraseña).")
                r = subprocess.run(
                    ["pkexec", "bash", "-c", script],
                    capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    raise RuntimeError(
                        (r.stderr or r.stdout or "no se pudo desmontar").strip())
            return True

        def _on_success(_res):
            self._mounted_media.pop(eid, None)
            try:
                os.rmdir(mp)
            except OSError:
                pass
            try:
                self.refresh_media_library_table()
            except Exception:
                pass
            QMessageBox.information(
                self, self.tr("Desmontar del host"),
                self.tr("'{0}' desmontado correctamente.").format(name))

        def _on_error(err):
            QMessageBox.critical(
                self, self.tr("Desmontar del host"),
                self.tr("No se pudo desmontar.\n\n{0}").format(err))

        self.run_async(
            _work,
            self.tr("Desmontando '{0}'").format(name),
            on_success=_on_success,
            on_error=_on_error,
            cancelable=False,
            show_log=True,
            subtitle=self.tr("Liberando el punto de montaje…"),
        )

    def _unmount_all_mounted_media(self):
        """Desmonta todos los discos montados. Best-effort, sin dialogos.

        Se llama desde closeEvent. No usa pkexec: cerrar la app no debe
        quedarse bloqueado pidiendo contraseña. Los montajes FUSE se
        desmontan sin root; los qemu-nbd sin root se quedan como estan
        y el arranque siguiente ofrecera limpiarlos.
        """
        if not hasattr(self, "_mounted_media"):
            return
        try:
            self._sync_mounted_media_state()
        except Exception:
            pass
        for eid, info in list(self._mounted_media.items()):
            mp = (info or {}).get("mp") or ""
            if not mp or not os.path.ismount(mp):
                self._mounted_media.pop(eid, None)
                continue
            try:
                subprocess.run(["fusermount", "-u", mp],
                               capture_output=True, text=True, timeout=10)
            except Exception:
                pass
            if os.path.ismount(mp):
                try:
                    subprocess.run(["umount", mp],
                                   capture_output=True, text=True, timeout=10)
                except Exception:
                    pass
            if not os.path.ismount(mp):
                try:
                    os.rmdir(mp)
                except OSError:
                    pass
            self._mounted_media.pop(eid, None)


    # ------------------------------------------------------------------
    # media_library_create_disk_v1_mixin: crear discos desde la biblioteca
    # ------------------------------------------------------------------
    # Reutiliza el diálogo _CreateMediumDialog (ampliado con VMDK, VDI,
    # VHD, VHDX) para que el usuario cree un disco nuevo y lo registre
    # en el índice de la biblioteca sin salir de la pestaña Medios.
    #
    # El archivo se crea con `qemu-img create -f <fmt> <path> <size>`.
    # Al registrarlo, se preserva el `kind` elegido (auto_detect puede
    # haber decidido otro a partir del nombre) y se añade una nota.

    def create_medium_in_library(self):
        """Abre el diálogo de creación y registra el disco en la biblioteca."""
        try:
            self._create_medium_in_library_impl()
        except Exception as e:
            try:
                self._media_mount_log_exc("create_medium_in_library", e)
            except Exception:
                pass
            try:
                QMessageBox.critical(
                    self, self.tr("Crear disco"),
                    self.tr("Error inesperado al crear el disco.\n\n"
                            "Puedes ver el detalle en la Consola de "
                            "Progreso.\n\n{0}").format(e))
            except Exception:
                pass

    def _create_medium_in_library_impl(self):
        """Cuerpo real de create_medium_in_library (sin try global)."""
        lib = self._media_library_instance()
        if lib is None:
            QMessageBox.warning(
                self, self.tr("Crear disco"),
                self.tr("La biblioteca no está disponible."))
            return

        from dialogs import _CreateMediumDialog
        dlg = _CreateMediumDialog(self, default_type="qcow2")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.values()

        fname = v["name"] + v["extension"]
        target = os.path.join(lib.base_dir, fname)

        if os.path.exists(target):
            _resp = QMessageBox.question(
                self, self.tr("Ya existe"),
                self.tr("Ya existe un archivo con ese nombre en la "
                        "biblioteca:\n\n{0}\n\n¿Sobrescribir? "
                        "(se perderá el contenido anterior)").format(target),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if _resp != QMessageBox.StandardButton.Yes:
                return

        # Ejecutar qemu-img create en un worker para no bloquear la UI.
        def _work(log_emit, is_cancelled, progress_emit):
            # media_library_create_disk_v1_prealloc: delega al helper.
            from dialogs import _CreateMediumDialog
            cmd = _CreateMediumDialog.build_qemu_create_cmd(v, target)
            log_emit("==> " + " ".join(cmd))
            try:
                r = subprocess.run(cmd, capture_output=True,
                                    text=True, timeout=300)
            except FileNotFoundError:
                raise RuntimeError(
                    self.tr("No se encontró 'qemu-img'. Instálalo "
                            "(paquete qemu-utils / qemu-img)."))
            if r.returncode != 0:
                raise RuntimeError(
                    (r.stderr or r.stdout or "qemu-img falló").strip())
            log_emit("==> Disco creado: {} ({}, {}).".format(
                fname, v["size"], v["format"].upper()))

            # Registrar en el índice preservando el 'kind' elegido.
            entry_id = None
            try:
                e = lib.add(target)
                if isinstance(e, dict) and e.get("id"):
                    entry_id = e["id"]
                    lib.update(
                        entry_id,
                        kind=v["kind"],
                        notes=self.tr(
                            "Creado con qemu-img create. "
                            "Tamaño: {0}.").format(v["size"]),
                    )
            except Exception as e_reg:
                log_emit("[AVISO] No se pudo registrar en el índice: "
                         "{}".format(e_reg))
            return {"entry_id": entry_id, "name": fname,
                    "size": v["size"], "format": v["format"]}

        def _on_success(res):
            try:
                self.refresh_media_library_table()
            except Exception:
                pass
            QMessageBox.information(
                self, self.tr("Disco creado"),
                self.tr("Se creó el disco correctamente.\n\n"
                        "Archivo: {0}\n"
                        "Tamaño: {1}\n"
                        "Formato: {2}").format(
                    res["name"], res["size"], res["format"].upper()))

        def _on_error(err):
            QMessageBox.critical(
                self, self.tr("Crear disco"),
                self.tr("No se pudo crear el disco.\n\n{0}").format(err))

        self.run_async(
            _work,
            self.tr("Creando '{0}'").format(fname),
            on_success=_on_success,
            on_error=_on_error,
            cancelable=False,
            show_log=True,
            subtitle=self.tr("Ejecutando qemu-img create…"),
        )


# media_library_create_disk_v1_mixin

# i18n_tanda2f4_media_library_ui_v1

# i18n_tanda2f4_media_library_handlers_v1


# media_library_host_mount_v1_urgent01


# media_library_host_mount_v1_friendly_mp


# media_library_host_mount_v1_uid_gid


# media_library_create_disk_v1_prealloc_mixin
