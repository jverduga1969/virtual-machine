# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: panel unificado de Configuracion Host.

Marcador: config_host_mixin_v1

Sustituye los 7 paneles independientes que hoy viven en Configuracion
Host (deps de virtualizacion, udmabuf, permisos USB, PCI/VFIO,
carpetas compartidas, Modo kiosco, consola remota). Cada uno tenia su
propio pkexec y su propio par de botones.

Ahora:
  * Una sola lista con semaforos (icono + etiqueta + detalle).
  * Agrupada por categoria (virtualizacion, permisos, python, udev,
    consola, comparticion, vfio, kiosco).
  * Niveles: basic (siempre visible) y advanced (detras del toggle
    "Mostrar opciones avanzadas").
  * Dos botones: [Comprobar] y [Reparar lo que falte].
  * Reparar ejecuta packaging/postinstall.sh via pkexec, UNA sola
    elevacion, script idempotente.

El catalogo de requisitos y sus checks viven en config_host_deps.py.
Este mixin solo pinta la UI y conecta los botones.

Los metodos viejos (repair_dependency_status, install_usb_permissions,
_build_vfio_host_ui, etc.) siguen existiendo por si otro codigo los
referencia, pero YA NO se llaman desde Config Host.
"""

import os


class ConfigHostMixin:
    # Marcador: config_host_mixin_v1

    # ------------------------------------------------------------------
    # Construccion de la UI
    # ------------------------------------------------------------------

    def _build_config_host_ui(self, parent_layout):
        """Construye y anade el panel unificado a `parent_layout`.

        Patron heredado de desktop_mode_host_check_v1 / vfio_host_check_v1:
        QGroupBox + descripcion 11px + grid [icono][texto][detalle] +
        botones Comprobar/Reparar + QTimer.singleShot para la primera
        comprobacion.
        """
        from PyQt6.QtWidgets import (
            QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
            QPushButton, QCheckBox, QFrame,
        )
        from PyQt6.QtCore import Qt, QTimer, QSettings

        group = QGroupBox(self.tr("Estado del host"))
        lay = QVBoxLayout(group)
        lay.setSpacing(8)

        purpose = QLabel(self.tr(
            "Para que sirve: comprobar de un vistazo que este equipo "
            "tiene todo lo necesario para que la aplicacion funcione. "
            "Si algo falta, 'Reparar lo que falte' lo resuelve con una "
            "sola autenticacion."
        ))
        purpose.setWordWrap(True)
        purpose.setStyleSheet("color:#666; font-size:11px;")
        lay.addWidget(purpose)

        # Fila informativa: distro + gestor de paquetes.
        info_row = QHBoxLayout()
        self._ch_distro_label = QLabel("\u2014")
        self._ch_pm_label = QLabel("\u2014")
        for _w, _title in (
            (self._ch_distro_label, self.tr("Distribucion:")),
            (self._ch_pm_label, self.tr("Gestor:")),
        ):
            info_row.addWidget(QLabel(f"<b>{_title}</b>"))
            info_row.addWidget(_w)
            info_row.addSpacing(16)
        info_row.addStretch(1)
        lay.addLayout(info_row)

        # Toggle "Mostrar opciones avanzadas".
        self._ch_show_advanced = QCheckBox(
            self.tr("Mostrar opciones avanzadas")
        )
        self._ch_show_advanced.setToolTip(self.tr(
            "Muestra los requisitos avanzados: comparticion de carpetas,\n"
            "passthrough PCI/VFIO y Modo kiosco. Desactivado por defecto\n"
            "para no abrumar al usuario casual."
        ))
        try:
            _saved = QSettings().value(
                "ui/config_host_advanced", False, type=bool)
        except Exception:
            _saved = False
        self._ch_show_advanced.setChecked(bool(_saved))
        self._ch_show_advanced.toggled.connect(
            self._on_config_host_advanced_toggled
        )
        lay.addWidget(self._ch_show_advanced)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        lay.addWidget(sep)

        # Catalogo de requisitos.
        try:
            from config_host_deps import REQUIREMENTS, CATEGORIES
        except Exception as e:
            _err = QLabel(self.tr(
                "No se pudo cargar el catalogo de requisitos: {0}"
            ).format(e))
            _err.setWordWrap(True)
            _err.setStyleSheet("color:#c62828;")
            lay.addWidget(_err)
            parent_layout.addWidget(group)
            return group

        # Almacenes por key para poder actualizar / ocultar.
        self._ch_icons        = {}
        self._ch_labels       = {}
        self._ch_details      = {}
        self._ch_section_rows = {}

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)

        # Reagrupar por categoria respetando el orden de CATEGORIES.
        by_cat = {}
        for r in REQUIREMENTS:
            by_cat.setdefault(r["category"], []).append(r)

        row = 0
        for cat_key, cat_title in CATEGORIES:
            items = by_cat.get(cat_key, [])
            if not items:
                continue
            sec = QLabel(f"<b>{self.tr(cat_title)}</b>")
            sec.setStyleSheet("padding-top: 8px; color: #555;")
            grid.addWidget(sec, row, 0, 1, 3)
            self._ch_section_rows[cat_key] = sec
            row += 1

            for r in items:
                icon = QLabel("\u23f3")  # ⏳ pendiente
                icon.setFixedWidth(22)
                icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl = QLabel(r["label"])
                lbl.setWordWrap(True)
                det = QLabel("")
                det.setWordWrap(True)
                det.setStyleSheet("color:#888; font-size:11px;")
                grid.addWidget(icon, row, 0)
                grid.addWidget(lbl,  row, 1)
                grid.addWidget(det,  row, 2)

                self._ch_icons[r["key"]]   = icon
                self._ch_labels[r["key"]]  = lbl
                self._ch_details[r["key"]] = det
                row += 1

        lay.addLayout(grid)

        # Etiqueta de resultado (aparece tras la primera comprobacion).
        self._ch_result_label = QLabel("")
        self._ch_result_label.setWordWrap(True)
        self._ch_result_label.setVisible(False)
        lay.addWidget(self._ch_result_label)

        # Botones.
        btn_row = QHBoxLayout()
        self.btn_ch_check = QPushButton(self.tr("\U0001f504 Comprobar"))
        self.btn_ch_check.setToolTip(self.tr(
            "Vuelve a comprobar el estado de todos los requisitos.\n"
            "No modifica nada del sistema."
        ))
        self.btn_ch_check.clicked.connect(
            lambda: self._refresh_config_host(silent=False)
        )
        btn_row.addWidget(self.btn_ch_check)

        self.btn_ch_repair = QPushButton(
            self.tr("\U0001f6e0\ufe0f Reparar lo que falte")
        )
        self.btn_ch_repair.setToolTip(self.tr(
            "Ejecuta packaging/postinstall.sh con una sola autenticacion.\n"
            "Instala lo que falte: paquetes del sistema, grupos del\n"
            "usuario, reglas udev, wrapper sudo. Es idempotente."
        ))
        self.btn_ch_repair.clicked.connect(self._repair_config_host)
        btn_row.addWidget(self.btn_ch_repair)
        btn_row.addStretch(1)
        lay.addLayout(btn_row)

        parent_layout.addWidget(group)

        # Visibilidad inicial segun el toggle.
        self._apply_config_host_visibility()

        # Primera comprobacion diferida (no bloquea el arranque).
        try:
            QTimer.singleShot(
                200,
                lambda: self._refresh_config_host(silent=True),
            )
        except Exception:
            pass

        return group

    # ------------------------------------------------------------------
    # Visibilidad del toggle "Mostrar opciones avanzadas"
    # ------------------------------------------------------------------

    def _on_config_host_advanced_toggled(self, checked):
        try:
            from PyQt6.QtCore import QSettings
            QSettings().setValue(
                "ui/config_host_advanced", bool(checked))
        except Exception:
            pass
        self._apply_config_host_visibility()

    def _apply_config_host_visibility(self):
        """Muestra/oculta requisitos segun el toggle advanced.

        Marcador: config_host_mixin_v1.
        """
        try:
            from config_host_deps import REQUIREMENTS, CATEGORIES
        except Exception:
            return
        try:
            show_adv = bool(getattr(self, "_ch_show_advanced", None)
                            and self._ch_show_advanced.isChecked())
        except Exception:
            show_adv = False

        for r in REQUIREMENTS:
            visible = (r["level"] == "basic") or show_adv
            for store in (self._ch_icons, self._ch_labels, self._ch_details):
                w = store.get(r["key"])
                if w is not None:
                    w.setVisible(visible)

        # Encabezado de categoria visible solo si tiene items visibles.
        for cat_key, _title in CATEGORIES:
            items = [r for r in REQUIREMENTS if r["category"] == cat_key]
            any_vis = any((r["level"] == "basic") or show_adv for r in items)
            hdr = self._ch_section_rows.get(cat_key)
            if hdr is not None:
                hdr.setVisible(any_vis)

    # ------------------------------------------------------------------
    # Comprobar
    # ------------------------------------------------------------------

    def _refresh_config_host(self, silent=False):
        """Re-detecta el estado de todos los requisitos y repinta.

        Marcador: config_host_mixin_v1.
        """
        try:
            from config_host_deps import REQUIREMENTS, check_one
        except Exception as e:
            try:
                self.log_message(
                    "[AVISO] config_host_deps no disponible: " + str(e))
            except Exception:
                pass
            return

        # Distro + gestor de paquetes.
        try:
            from host_deps import detect_linux_package_manager
            _mgr, _info = detect_linux_package_manager()
            _distro = (
                (_info or {}).get("PRETTY_NAME")
                or (_info or {}).get("ID")
                or "Linux"
            )
            self._ch_distro_label.setText(_distro)
            self._ch_pm_label.setText(_mgr or "\u2014")
        except Exception:
            pass

        ok_count = 0
        for r in REQUIREMENTS:
            o, detail = check_one(r)
            if o:
                ok_count += 1

            icon = self._ch_icons.get(r["key"])
            if icon is not None:
                icon.setText("\u2705" if o else "\u274c")
                icon.setToolTip("" if o else (detail or ""))

            det = self._ch_details.get(r["key"])
            if det is not None:
                det.setText(detail or "")
                det.setStyleSheet(
                    "color:#2e7d32; font-size:11px;" if o
                    else "color:#c62828; font-size:11px;"
                )

        total = len(REQUIREMENTS)
        try:
            self._ch_result_label.setText(self.tr(
                "Estado: {0} de {1} requisitos OK."
            ).format(ok_count, total))
            self._ch_result_label.setStyleSheet(
                "font-size: 11px; "
                + ("color:#2e7d32;" if ok_count == total
                   else "color:#b36b00;")
            )
            self._ch_result_label.setVisible(True)
        except Exception:
            pass

        # Reparar: habilitado solo si el postinstall esta disponible.
        try:
            from config_host_deps import postinstall_available
            avail = postinstall_available()
        except Exception:
            avail = False
        try:
            self.btn_ch_repair.setEnabled(avail)
            if not avail:
                self.btn_ch_repair.setToolTip(self.tr(
                    "No encontre packaging/postinstall.sh en el repo."
                ))
        except Exception:
            pass

        if not silent:
            try:
                self.log_message(
                    "==> Configuracion Host: {0}/{1} requisitos OK.".format(
                        ok_count, total)
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Reparar (postinstall.sh via pkexec, una sola elevacion)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Slots para el worker de reparacion.
    # IMPORTANTE: deben ser metodos bound de un QObject que viva en el
    # hilo de UI. Si fueran closures, PyQt los ejecutaria en el hilo
    # emisor (el worker) y las llamadas a dlg.* no se renderizarian:
    # el dialogo se queda visualmente congelado en "Preparando
    # reparacion..." aunque el worker siga avanzando.
    # Marcador: config_host_progress_v4.
    # ------------------------------------------------------------------

    def _repair_config_host(self):
        """Version QProcess: sin hilos, sin colas, sin senales cross-thread.

        Marcador: config_host_progress_v5.

        Usa QProcess de Qt para lanzar pkexec. QProcess emite
        readyReadStandardOutput en el hilo de UI cuando el proceso
        escribe. No necesita QThread ni QueuedConnection.
        """
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog
        from PyQt6.QtCore import QProcess, Qt, QTimer
        import shutil as _sh

        try:
            from config_host_deps import (
                REQUIREMENTS, check_one,
                postinstall_available, POSTINSTALL_SH,
            )
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Reparar requisitos"),
                self.tr("No se pudo cargar config_host_deps: {0}").format(e),
            )
            return

        if not postinstall_available():
            _msg = (
                self.tr("No encontre packaging/postinstall.sh en el repo.")
                + chr(10) + chr(10)
                + self.tr("Comprueba que existe.")
            )
            QMessageBox.warning(self, self.tr("Reparar requisitos"), _msg)
            return

        pkexec = _sh.which("pkexec")
        if not pkexec:
            QMessageBox.critical(
                self, self.tr("Reparar requisitos"),
                self.tr("No se encontro pkexec."),
            )
            return

        pre_failing = set()
        for r in REQUIREMENTS:
            o, _d = check_one(r)
            if not o:
                pre_failing.add(r["key"])
        _needs_logout = bool(pre_failing & {"kvm_group", "kiosk_tty_group"})

        _confirm = (
            self.tr("Se ejecutara packaging/postinstall.sh con UNA sola")
            + chr(10)
            + self.tr("autenticacion (pkexec).")
            + chr(10) + chr(10)
            + self.tr("Es idempotente: si algo ya esta, no lo toca.")
            + chr(10) + chr(10)
            + self.tr("Continuar?")
        )
        resp = QMessageBox.question(
            self, self.tr("Reparar lo que falte"),
            _confirm,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        dlg = QProgressDialog(
            self.tr("Lanzando pkexec. Si aparece un dialogo de contrasena, "
                    "introducela."),
            None, 0, 100, self,
        )
        dlg.setWindowTitle(self.tr("Reparando requisitos del host"))
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.setMinimumWidth(520)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        try:
            dlg.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        except Exception:
            pass
        dlg.show()
        try:
            QTimer.singleShot(120, dlg.lower)
        except Exception:
            pass

        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        state = {
            "phase_pat": [
                (r"Postinstall .* iniciado",        3),
                (r"Gestor de paquetes detectado",   4),
                (r"Actualizando indices",           6),
                (r": instalando ",                 20),
                (r"ya instalado",                  30),
                (r"Ajustando grupos",              60),
                (r"Instalando reglas udev",        72),
                (r"udev recargado",                78),
                (r"Configurando /etc/X11",         82),
                (r"Xwrapper.config listo",         85),
                (r"Instalando wrapper sudo",       88),
                (r"wrapper instalado",             91),
                (r"regla sudoers instalada",       94),
                (r"Postinstall .* completado",     98),
            ],
            "buf": "",
        }
        import re as _re

        def _on_ready():
            try:
                raw = bytes(proc.readAllStandardOutput()).decode(
                    "utf-8", "replace")
            except Exception:
                return
            state["buf"] += raw
            while chr(10) in state["buf"]:
                line, state["buf"] = state["buf"].split(chr(10), 1)
                line = line.rstrip()
                if not line:
                    continue
                try:
                    self.log_message("    " + line)
                except Exception:
                    pass
                for pat, pct in state["phase_pat"]:
                    if _re.search(pat, line):
                        try:
                            dlg.setValue(max(0, min(100, int(pct))))
                            dlg.setLabelText(
                                self.tr("Reparando requisitos del host...")
                                + chr(10) + chr(10) + line
                            )
                        except Exception:
                            pass
                        break

        def _on_finished(exit_code, exit_status):
            try:
                _on_ready()
            except Exception:
                pass
            try:
                dlg.setValue(100)
            except Exception:
                pass
            try:
                dlg.close()
            except Exception:
                pass
            try:
                self._refresh_config_host(silent=True)
            except Exception:
                pass

            ok = (exit_code == 0)
            if ok:
                _tail = ""
                if _needs_logout:
                    _tail = (
                        chr(10) + chr(10)
                        + self.tr("IMPORTANTE: se anadieron grupos al usuario.")
                        + chr(10)
                        + self.tr("Para que tengan efecto, CIERRA SESION "
                                  "y vuelve a entrar.")
                    )
                QMessageBox.information(
                    self, self.tr("Reparar lo que falte"),
                    self.tr("Reparacion completada correctamente.") + _tail,
                )
                try:
                    self.log_message(
                        "==> Configuracion Host: reparacion completada.")
                except Exception:
                    pass
            else:
                _tail = ""
                if exit_code in (126, 127):
                    _tail = (
                        chr(10) + chr(10)
                        + self.tr("pkexec devolvio {0}. Puede que hayas "
                                  "cancelado la autenticacion.").format(exit_code)
                    )
                QMessageBox.warning(
                    self, self.tr("Reparar lo que falte"),
                    self.tr("La reparacion no termino correctamente.")
                    + _tail,
                )

        proc.readyReadStandardOutput.connect(_on_ready)
        proc.finished.connect(_on_finished)

        self._ch_repair_proc = proc
        self._ch_repair_dlg = dlg

        proc.start(pkexec, ["bash", str(POSTINSTALL_SH)])


# config_host_mixin_v1

# config_host_progress_v5
