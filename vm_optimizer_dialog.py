# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""vm_optimizer_dialog.py — dialogo "Aplicar perfil" (vm_optimizer_v1).

Muestra los 4 perfiles del Modo Rapido, una vista previa de los ajustes
avanzados que se aplicarian sobre la VM actual (con la columna "Actual"
y "Perfil" en paralelo) y avisos amarillos si el host no puede cumplir
algun valor (el dialogo AVISA pero APLICA igual: el perfil propone, el
worker decide; ver decision 5 del marcador).

El dialogo NO toca la VM. Solo devuelve el profile_id elegido. El
llamador (vm_optimizer_mixin) se encarga de escribir en los widgets
y en vm_config.ini.

Marcador: vm_optimizer_v1_dialog_impl.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import vm_profiles


# ---------------------------------------------------------------------
# Etiquetas legibles para las claves del bloque avanzado.
# ---------------------------------------------------------------------
_FIELD_LABELS = [
    # (clave en advanced, etiqueta visible, tipo)
    ("graphics_mode",         "Gráficos",                     "combo"),
    ("nested_virt",           "Virtualización anidada",       "bool"),
    ("hyperv_enlightenments", "Hyper-V enlightenments",       "bool"),
    ("virtio_rng",            "VirtIO-RNG (entropía)",        "bool"),
    ("virtio_balloon",        "VirtIO-balloon (RAM al host)", "bool"),
    ("virtio_watchdog",       "Watchdog de hardware",         "bool"),
    ("memory_tuning",         "Hugepages",                    "mem_hugepages"),
    ("memory_tuning",         "Prealloc RAM al arrancar",     "mem_prealloc"),
    ("memory_tuning",         "memfd-lock (evitar swap)",     "mem_memfd"),
    ("cpu_topology",          "Topología manual de CPU",      "topo_mode"),
    ("console_protocol",      "Consola: protocolo",           "combo"),
    ("console_mode",          "Consola: modo",                "combo"),
    ("snapshot_compat",       "Modo compat. de snapshots",    "bool"),
    ("disk_io",               "I/O cache",                    "disk_cache"),
    ("disk_io",               "I/O io",                       "disk_io"),
    ("disk_io",               "I/O aio",                      "disk_aio"),
    ("disk_io",               "I/O discard",                  "disk_discard"),
    ("disk_io",               "I/O detect-zeroes",            "disk_zeroes"),
    ("clipboard",             "Clipboard",                    "combo"),
]

_GRAPHICS_NAMES = {
    "auto":   "Automático",
    "virtio": "VirtIO-GPU 2D",
    "virgl":  "VirtIO-GPU + VirGL 3D",
    "venus":  "VirtIO-GPU + Venus/Vulkan",
    "qxl":    "Red Hat QXL 2D",
    "vmware": "VMware SVGA II",
    "std":    "VGA estándar",
    "none":   "Sin video",
}

_CONSOLE_PROTO_NAMES = {
    "vnc":   "VNC",
    "spice": "SPICE",
}

_CONSOLE_MODE_NAMES = {
    "embedded": "Embebida en la app",
    "external": "Ventana externa",
    "native":   "Ventana nativa de QEMU",
    "hybrid":   "Híbrida (VNC + SPICE)",
}

_CLIPBOARD_NAMES = {
    "disabled":      "Desactivado",
    "none":          "Desactivado",
    "host_to_guest": "Host → Guest",
    "guest_to_host": "Guest → Host",
    "bidirectional": "Bidireccional",
}


def _bool_txt(tr, v):
    return tr("Sí") if bool(v) else tr("No")


def _get_nested(d, *path):
    """d = {"memory_tuning": {"hugepages": True}}; _get_nested(d, "memory_tuning", "hugepages")."""
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


class VmOptimizerDialog(QDialog):
    """Dialogo 'Aplicar perfil' sobre una VM existente.

    Interfaz:
        dlg = VmOptimizerDialog(parent, vm_name, os_type, current_state)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pid = dlg.chosen_profile()
            # pid != None → aplicar
    """

    def __init__(self, parent, vm_name, os_type, current_state,
                 initial_profile=None):
        """
        vm_name:       nombre visible de la VM (informativo).
        os_type:       "linux" | "windows" | "macos" | "android".
        current_state: dict con los valores avanzados ACTUALES de la VM.
                       Las claves que falten se tratan como default.
        initial_profile: profile_id preseleccionado. Default: "general".
        """
        super().__init__(parent)
        self.setWindowTitle(self.tr("Aplicar perfil — {0}").format(vm_name))
        self.setModal(True)
        self.setMinimumWidth(760)
        self.setMinimumHeight(600)

        self._vm_name = vm_name or ""
        self._os_type = (os_type or "linux").lower()
        self._current  = dict(current_state or {})
        self._chosen_id = None

        # Primera opcion de perfil valida para este SO.
        if initial_profile and vm_profiles.is_supported(
                initial_profile, self._os_type):
            self._chosen_id = initial_profile
        else:
            self._chosen_id = self._first_supported_profile()

        self._cards = {}
        self._build_ui()
        self._on_profile_clicked(self._chosen_id)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _first_supported_profile(self):
        for pid in vm_profiles.all_profile_ids():
            if vm_profiles.is_supported(pid, self._os_type):
                return pid
        return vm_profiles.DEFAULT_PROFILE

    def _current_for_field(self, key, kind):
        """Valor ACTUAL del campo `key`, con el sub-path segun `kind`.

        El 'current_state' guarda memory_tuning, cpu_topology y disk_io
        como dicts anidados. Esta funcion extrae el escalar concreto.
        """
        if kind == "mem_hugepages":
            return bool(_get_nested(self._current, "memory_tuning",
                                    "hugepages") or False)
        if kind == "mem_prealloc":
            return bool(_get_nested(self._current, "memory_tuning",
                                    "prealloc") or False)
        if kind == "mem_memfd":
            return bool(_get_nested(self._current, "memory_tuning",
                                    "memfd_lock") or False)
        if kind == "topo_mode":
            v = _get_nested(self._current, "cpu_topology", "mode")
            return str(v or "auto").lower()
        if kind == "disk_cache":
            return _get_nested(self._current, "disk_io", "cache") or "auto"
        if kind == "disk_io":
            return _get_nested(self._current, "disk_io", "io") or "auto"
        if kind == "disk_aio":
            return _get_nested(self._current, "disk_io", "aio") or "auto"
        if kind == "disk_discard":
            return _get_nested(self._current, "disk_io", "discard") or "auto"
        if kind == "disk_zeroes":
            return _get_nested(self._current, "disk_io", "detect_zeroes") or "auto"
        v = self._current.get(key)
        if v is None:
            # defaults razonables si el .ini no traia la clave.
            _defaults = {
                "graphics_mode": "auto",
                "nested_virt": False,
                "hyperv_enlightenments": False,
                "virtio_rng": False,
                "virtio_balloon": False,
                "virtio_watchdog": False,
                "console_protocol": "vnc",
                "console_mode": "embedded",
                "snapshot_compat": False,
                "clipboard": "disabled",
            }
            return _defaults.get(key, "")
        return v

    def _profile_for_field(self, advanced, key, kind):
        """Valor PROPUESTO por el perfil para el campo, segun `kind`."""
        if kind == "mem_hugepages":
            return bool(_get_nested(advanced, "memory_tuning",
                                    "hugepages") or False)
        if kind == "mem_prealloc":
            return bool(_get_nested(advanced, "memory_tuning",
                                    "prealloc") or False)
        if kind == "mem_memfd":
            return bool(_get_nested(advanced, "memory_tuning",
                                    "memfd_lock") or False)
        if kind == "topo_mode":
            v = _get_nested(advanced, "cpu_topology", "mode")
            return str(v or "auto").lower()
        if kind == "disk_cache":
            return _get_nested(advanced, "disk_io", "cache") or "auto"
        if kind == "disk_io":
            return _get_nested(advanced, "disk_io", "io") or "auto"
        if kind == "disk_aio":
            return _get_nested(advanced, "disk_io", "aio") or "auto"
        if kind == "disk_discard":
            return _get_nested(advanced, "disk_io", "discard") or "auto"
        if kind == "disk_zeroes":
            return _get_nested(advanced, "disk_io", "detect_zeroes") or "auto"
        return advanced.get(key)

    def _render_value(self, key, kind, value):
        """Texto legible para mostrar en la tabla."""
        if kind in ("mem_hugepages", "mem_prealloc", "mem_memfd"):
            return _bool_txt(self.tr, value)
        if kind == "topo_mode":
            v = str(value or "auto").lower()
            return self.tr("Auto") if v == "auto" else self.tr("Manual")
        if kind in ("disk_cache", "disk_io", "disk_aio",
                    "disk_discard", "disk_zeroes"):
            v = str(value or "auto").lower()
            return self.tr("auto (por defecto de QEMU)") if v == "auto" else v
        if key == "graphics_mode":
            return _GRAPHICS_NAMES.get(str(value or "auto"),
                                       str(value or "auto"))
        if key == "console_protocol":
            return _CONSOLE_PROTO_NAMES.get(str(value or "vnc").lower(),
                                            str(value or "vnc"))
        if key == "console_mode":
            return _CONSOLE_MODE_NAMES.get(str(value or "embedded").lower(),
                                           str(value or "embedded"))
        if key == "clipboard":
            return _CLIPBOARD_NAMES.get(str(value or "disabled").lower(),
                                        str(value or "disabled"))
        if isinstance(value, bool):
            return _bool_txt(self.tr, value)
        return str(value)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Cabecera
        head = QLabel(self.tr(
            "Aplicar un perfil del <b>Modo Rápido</b> sobre "
            "<b>{0}</b>.<br>"
            "<span style='font-size:11px;'>"
            "Solo se aplican los ajustes <b>avanzados</b> "
            "(gráficos, CPU, memoria, consola, I/O, clipboard, "
            "compat. de snapshots). RAM, núcleos, disco y placa "
            "<b>no se tocan</b>."
            "</span>"
        ).format(self._vm_name))
        head.setTextFormat(Qt.TextFormat.RichText)
        head.setWordWrap(True)
        root.addWidget(head)

        # Fila de tarjetas
        gb_profile = QGroupBox(self.tr("Perfil"))
        h = QHBoxLayout(gb_profile)
        h.setSpacing(8)
        for pid in vm_profiles.all_profile_ids():
            card = self._make_card(pid)
            h.addWidget(card)
            self._cards[pid] = card
        h.addStretch(1)
        root.addWidget(gb_profile)

        # Vista previa
        gb_prev = QGroupBox(self.tr("Vista previa (solo se muestran los "
                                    "ajustes avanzados)"))
        v_prev = QVBoxLayout(gb_prev)
        v_prev.setContentsMargins(8, 8, 8, 8)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.tr("Campo"),
            self.tr("Actual"),
            self.tr("Perfil"),
        ])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tree.setAlternatingRowColors(False)
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 220)
        self.tree.setColumnWidth(2, 220)
        v_prev.addWidget(self.tree)
        root.addWidget(gb_prev, 1)

        # Avisos del host
        self.warn_box = QFrame()
        self.warn_box.setVisible(False)
        self.warn_box.setStyleSheet(
            "QFrame { background:#fff8e1; border:1px solid #ffe082; "
            "border-radius:6px; padding:8px; }")
        _wb_lay = QVBoxLayout(self.warn_box)
        _wb_lay.setContentsMargins(8, 6, 8, 6)
        self.warn_label = QLabel("")
        self.warn_label.setTextFormat(Qt.TextFormat.RichText)
        self.warn_label.setWordWrap(True)
        self.warn_label.setStyleSheet(
            "font-size:11px; color:#7a5b00; background:transparent;")
        _wb_lay.addWidget(self.warn_label)
        root.addWidget(self.warn_box)

        # Aviso de irreversibilidad
        _irrev = QLabel(self.tr(
            "<span style='color:#7a5b00;font-size:11px;'>"
            "Aplicar un perfil <b>no</b> guarda la VM: los widgets "
            "quedan actualizados y el candado se cierra. Pulsa "
            "<b>💾 Guardar configuración</b> en Configuración VM para "
            "persistir el cambio."
            "</span>"
        ))
        _irrev.setTextFormat(Qt.TextFormat.RichText)
        _irrev.setWordWrap(True)
        root.addWidget(_irrev)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok)
        _ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        _ok_btn.setText(self.tr("Aplicar perfil"))
        _ok_btn.setDefault(True)
        _cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        _cancel_btn.setText(self.tr("Cancelar"))
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _make_card(self, profile_id):
        """Tarjeta simplificada de perfil (sin QFrame custom)."""
        prof = vm_profiles.PROFILES[profile_id]
        card = QPushButton(self.tr("{icon}  {label}").format(
            icon=prof.get("icon", ""), label=prof["label"]))
        card.setCheckable(True)
        card.setMinimumHeight(64)
        card.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)
        card.setToolTip(prof.get("description", ""))
        # vm_optimizer_v1_dialog_impl_rev2: estilos con contraste
        # explicito. La tarjeta seleccionada usa azul #1e40af con
        # texto blanco (igual que el sidebar de Config VM).
        card.setStyleSheet(
            "QPushButton { padding: 8px; "
            "border: 1px solid palette(mid); "
            "border-radius: 6px; }"
            "QPushButton:hover:!checked { "
            "border: 1px solid #2e6fd6; }"
            "QPushButton:checked { "
            "border: 2px solid #1e40af; "
            "background: #1e40af; "
            "color: white; "
            "font-weight: bold; }"
            "QPushButton:disabled { "
            "color: palette(mid); }"
        )

        supported = vm_profiles.is_supported(profile_id, self._os_type)
        if not supported:
            card.setEnabled(False)
            card.setToolTip(vm_profiles.reason_unsupported(
                profile_id, self._os_type) or self.tr("No disponible"))

        def _on_click(_checked=False, pid=profile_id):
            self._on_profile_clicked(pid)
        card.clicked.connect(_on_click)
        return card

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_profile_clicked(self, profile_id):
        if not vm_profiles.is_supported(profile_id, self._os_type):
            return
        self._chosen_id = profile_id
        # Refrescar el estado de las tarjetas.
        for pid, card in self._cards.items():
            try:
                card.setChecked(pid == profile_id)
            except Exception:
                pass
        self._render_preview()
        self._render_warnings()

    # ------------------------------------------------------------------
    # Vista previa
    # ------------------------------------------------------------------
    def _render_preview(self):
        self.tree.clear()
        adv = vm_profiles.profile_advanced(self._chosen_id, self._os_type)
        if adv is None:
            self.tree.addTopLevelItem(QTreeWidgetItem(
                [self.tr("Perfil no disponible para este SO."), "", ""]))
            return

        # vm_optimizer_v1_dialog_impl_rev2: par fondo+texto
        # para que el resaltado sea legible en ambos temas.
        diff_brush = QBrush(QColor("#fff3cd"))
        diff_fg    = QBrush(QColor("#5a3a00"))
        bold = QFont(); bold.setBold(True)

        n_diff = 0
        for key, label, kind in _FIELD_LABELS:
            cur_v = self._current_for_field(key, kind)
            prf_v = self._profile_for_field(adv, key, kind)
            cur_t = self._render_value(key, kind, cur_v)
            prf_t = self._render_value(key, kind, prf_v)
            diff = (str(cur_v) != str(prf_v))
            if diff:
                n_diff += 1
            it = QTreeWidgetItem([label, cur_t, prf_t])
            if diff:
                for col in range(3):
                    it.setBackground(col, diff_brush)
                    it.setForeground(col, diff_fg)
                it.setFont(2, bold)
            self.tree.addTopLevelItem(it)

        # Pie informativo con el conteo.
        foot = QTreeWidgetItem([
            self.tr("({0} campo(s) cambiarían)").format(n_diff), "", ""])
        fnt = QFont(); fnt.setItalic(True)
        for col in range(3):
            foot.setFont(col, fnt)
        self.tree.addTopLevelItem(foot)
        try:
            self.tree.expandAll()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Avisos del host
    # ------------------------------------------------------------------
    def _host_viability_warnings(self, adv):
        """Devuelve lista de strings con los valores del perfil que el
        host no puede cumplir. NO bloquea: el dialogo aplica igual.
        """
        warns = []
        if not isinstance(adv, dict):
            return warns

        gm = str(adv.get("graphics_mode") or "auto").lower()
        # VirGL requiere /dev/udmabuf accesible.
        if gm == "virgl":
            _udmabuf_ok = False
            try:
                _udmabuf_ok = (
                    os.path.exists("/dev/udmabuf")
                    and os.access("/dev/udmabuf", os.R_OK | os.W_OK)
                )
            except Exception:
                _udmabuf_ok = False
            if not _udmabuf_ok:
                warns.append(self.tr(
                    "<b>Gráficos VirGL 3D</b>: el host no expone "
                    "<code>/dev/udmabuf</code> accesible. El worker "
                    "degradará a VirtIO-GPU 2D al arrancar."))
        # Venus requiere Vulkan en el host.
        if gm == "venus":
            _vulkan_ok = False
            try:
                from host_deps import detect_host_graphics
                caps = detect_host_graphics() or {}
                _vulkan_ok = bool(caps.get("vulkan"))
            except Exception:
                _vulkan_ok = False
            if not _vulkan_ok:
                warns.append(self.tr(
                    "<b>Gráficos Venus/Vulkan</b>: el host no reporta "
                    "Vulkan. QEMU puede abortar el arranque."))

        # Hugepages: comprobar /dev/hugepages y páginas libres.
        mt = adv.get("memory_tuning") or {}
        if isinstance(mt, dict) and mt.get("hugepages"):
            _hp_ok = False
            try:
                _hp_ok = os.path.isdir("/dev/hugepages")
            except Exception:
                _hp_ok = False
            if not _hp_ok:
                warns.append(self.tr(
                    "<b>Hugepages</b>: <code>/dev/hugepages</code> no "
                    "existe. QEMU abortará el arranque si no se monta "
                    "hugetlbfs."))

        # snapshot_compat=True con clipboard activo → contradicción.
        if adv.get("snapshot_compat") and adv.get("clipboard") not in (
                None, "disabled", "none"):
            warns.append(self.tr(
                "<b>Clipboard + snapshots completos</b>: el chardev "
                "vdagent impide guardar snapshots completos. El guard "
                "de bloqueadores degradará a snapshot solo-disco."))

        # macOS: VirtIO-RNG, balloon, watchdog no aplican.
        if self._os_type == "macos":
            for k, label in (("virtio_rng", "VirtIO-RNG"),
                             ("virtio_balloon", "VirtIO-balloon"),
                             ("virtio_watchdog", "Watchdog")):
                if adv.get(k):
                    warns.append(self.tr(
                        "<b>{0}</b>: macOS no incluye driver. El worker "
                        "omitirá el dispositivo al arrancar.").format(label))

        # Android: clipboard no funciona.
        if self._os_type == "android" and adv.get("clipboard") not in (
                None, "disabled", "none"):
            warns.append(self.tr(
                "<b>Clipboard</b>: Android-x86 / Bliss OS no soportan "
                "spice-vdagent. El canal no se montará."))

        return warns

    def _render_warnings(self):
        adv = vm_profiles.profile_advanced(self._chosen_id, self._os_type)
        warns = self._host_viability_warnings(adv or {})
        if not warns:
            self.warn_box.setVisible(False)
            self.warn_label.setText("")
            return
        html = "<b>⚠ Avisos del host</b> (el perfil se aplicará igual; " \
               "el worker decidirá al arrancar):<ul style='margin:4px 0 0 " \
               "18px;padding:0;'>"
        for w in warns:
            html += f"<li>{w}</li>"
        html += "</ul>"
        self.warn_label.setText(html)
        self.warn_box.setVisible(True)

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------
    def _on_accept(self):
        if not self._chosen_id:
            QMessageBox.warning(
                self, self.tr("Aplicar perfil"),
                self.tr("Selecciona un perfil primero."))
            return
        if not vm_profiles.is_supported(self._chosen_id, self._os_type):
            QMessageBox.warning(
                self, self.tr("Aplicar perfil"),
                self.tr("El perfil '{0}' no está disponible para este "
                        "sistema operativo.").format(self._chosen_id))
            return
        self.accept()

    def chosen_profile(self):
        """profile_id elegido por el usuario (o None si canceló)."""
        return self._chosen_id


# vm_optimizer_v1_dialog_impl

# vm_optimizer_v1_dialog_impl_rev2
