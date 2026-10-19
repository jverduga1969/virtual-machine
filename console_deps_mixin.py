# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: chequeo/reparacion de las dependencias de consola remota
(SPICE embebido y visores externos) en Configuracion Host.

Marcador: console_deps_host_check_v1.
"""
import os
import shutil

from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QMessageBox,
)
from PyQt6.QtCore import QTimer


class ConsoleDepsMixin:
    # Marcador: console_deps_host_check_v1

    def _console_deps_status(self):
        """Devuelve el estado de cada dependencia de consola.

        Marcador: console_deps_status_v1.
        """
        spice_gtk_py = False
        try:
            import gi
            gi.require_version("SpiceClientGtk", "3.0")
            from gi.repository import SpiceClientGtk  # noqa: F401
            spice_gtk_py = True
        except Exception:
            spice_gtk_py = False

        spice_viewer_path = (
            shutil.which("spicy") or shutil.which("remote-viewer")
        )
        vnc_viewer_path = (
            shutil.which("gvncviewer") or shutil.which("vncviewer")
            or shutil.which("tigervnc-viewer")
        )
        try:
            from console_backend import is_x11_session
            x11 = bool(is_x11_session())
        except Exception:
            x11 = False

        return {
            "spice_gtk_py": spice_gtk_py,
            "spice_viewer_path": spice_viewer_path or "",
            "vnc_viewer_path": vnc_viewer_path or "",
            "is_x11": x11,
        }

    def _build_console_deps_group(self, parent_layout):
        """Construye y anade el grupo 'Consola remota' a Configuracion Host.

        Marcador: console_deps_host_check_v1.
        """
        group = QGroupBox(self.tr("Consola remota (VNC / SPICE)"))
        lay = QVBoxLayout(group)

        purpose = QLabel(self.tr(
            "Para que sirve: mostrar la VM dentro de la app (SPICE "
            "embebido) o abrirla en una ventana externa con el visor "
            "del sistema. SPICE embebido necesita spice-gtk con binding "
            "Python y una sesion X11."
        ))
        purpose.setWordWrap(True)
        purpose.setStyleSheet("color: #666; font-size: 11px;")
        lay.addWidget(purpose)

        self._cd_check_labels = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        _checks = [
            ("spice_gtk_py", self.tr("spice-gtk (binding Python, para embeber SPICE)")),
            ("spice_viewer", self.tr("Visor SPICE externo (spicy / remote-viewer)")),
            ("vnc_viewer",   self.tr("Visor VNC externo (gvncviewer / tigervnc)")),
            ("x11",          self.tr("Sesion X11 (necesaria para embeber SPICE)")),
        ]
        for _i, (_key, _label) in enumerate(_checks):
            _icon = QLabel("\u23f3")
            _icon.setFixedWidth(20)
            _lbl = QLabel(_label)
            _lbl.setWordWrap(True)
            self._cd_check_labels[_key] = _icon
            grid.addWidget(_icon, _i, 0)
            grid.addWidget(_lbl, _i, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)

        self._cd_result_label = QLabel("")
        self._cd_result_label.setWordWrap(True)
        self._cd_result_label.setVisible(False)
        lay.addWidget(self._cd_result_label)

        btns = QHBoxLayout()
        self.btn_cd_check = QPushButton(self.tr("\U0001f504 Comprobar"))
        self.btn_cd_check.clicked.connect(
            lambda: self.refresh_console_deps_status(silent=False)
        )
        self.btn_cd_repair = QPushButton(
            self.tr("\U0001f6e0\ufe0f Reparar lo que falte")
        )
        self.btn_cd_repair.setToolTip(self.tr(
            "Instala lo que falte (una sola autenticacion):\n"
            "  - spice-gtk con binding Python.\n"
            "  - Visor SPICE externo (spicy / remote-viewer).\n"
            "  - Visor VNC externo (gvncviewer / tigervnc).\n"
            "La sesion X11 no se puede instalar: depende del escritorio."
        ))
        self.btn_cd_repair.clicked.connect(self.repair_console_deps)
        btns.addWidget(self.btn_cd_check)
        btns.addWidget(self.btn_cd_repair)
        btns.addStretch(1)
        lay.addLayout(btns)

        parent_layout.addWidget(group)

        QTimer.singleShot(
            150,
            lambda: self.refresh_console_deps_status(silent=True),
        )

    def refresh_console_deps_status(self, silent=False):
        """Actualiza iconos y etiquetas del grupo.

        Marcador: console_deps_status_v1.
        """
        try:
            st = self._console_deps_status()
        except Exception as e:
            try:
                self.log_message("[AVISO] console_deps: " + str(e))
            except Exception:
                pass
            return

        def _set(key, ok_flag, tooltip=""):
            lbl = getattr(self, "_cd_check_labels", {}).get(key)
            if lbl is None:
                return
            lbl.setText("\u2705" if ok_flag else "\u274C")
            lbl.setToolTip(tooltip or "")

        _set("spice_gtk_py", st["spice_gtk_py"],
             "binding Python de spice-gtk disponible"
             if st["spice_gtk_py"]
             else "instala python3-gi + gir1.2-spiceclientgtk-3.0 (apt) "
                  "o python-gobject + spice-gtk (pacman)")
        _set("spice_viewer", bool(st["spice_viewer_path"]),
             st["spice_viewer_path"] or "no encontrado")
        _set("vnc_viewer", bool(st["vnc_viewer_path"]),
             st["vnc_viewer_path"] or "no encontrado")
        _set("x11", st["is_x11"],
             "sesion X11 detectada" if st["is_x11"]
             else "sesion Wayland: SPICE embebido no disponible")

        all_ok = (st["spice_gtk_py"] and st["spice_viewer_path"]
                  and st["vnc_viewer_path"] and st["is_x11"])
        try:
            self.btn_cd_repair.setEnabled(not all_ok)
        except Exception:
            pass
        if not silent:
            try:
                self.log_message(
                    "==> Consola remota: estado comprobado. "
                    + ("Todo OK." if all_ok else "Hay requisitos pendientes."))
            except Exception:
                pass

    def repair_console_deps(self):
        """Instala lo que falte con una sola autenticacion.

        Marcador: console_deps_repair_v1.
        """
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt

        try:
            st = self._console_deps_status()
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Consola remota"),
                self.tr("No se pudo comprobar el estado:\n\n{0}").format(e),
            )
            return

        missing = []
        if not st["spice_gtk_py"]:
            missing.append("spice-gtk (binding Python)")
        if not st["spice_viewer_path"]:
            missing.append("visor SPICE externo")
        if not st["vnc_viewer_path"]:
            missing.append("visor VNC externo")

        if not missing:
            QMessageBox.information(
                self, self.tr("Consola remota"),
                self.tr(
                    "No hay nada que instalar en este equipo.\n\n"
                    "Nota: la sesion X11 (necesaria para embeber SPICE)\n"
                    "es una propiedad del escritorio, no un paquete."
                ),
            )
            return

        reply = QMessageBox.question(
            self, self.tr("Reparar dependencias de consola"),
            self.tr(
                "Se instalara con el gestor de paquetes del sistema:\n\n"
                "  - {0}\n\n"
                "Se pedira autenticacion UNA sola vez.\n\n"
                "Continuar?"
            ).format("\n  - ".join(missing)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.btn_cd_repair.setEnabled(False)
            self.btn_cd_check.setEnabled(False)
        except Exception:
            pass
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            from system_deps import (
                detect_manager, _priv_prefix, _run, _install_cmd,
            )
            manager, info = detect_manager()
            if manager is None:
                QMessageBox.warning(
                    self, self.tr("Consola remota"),
                    self.tr(
                        "No se reconoce el gestor de paquetes de esta\n"
                        "distribucion. Instala los paquetes a mano."
                    ),
                )
                return

            pkg_map = {
                "apt": {
                    "spice_gtk_py": ["python3-gi",
                                     "gir1.2-spiceclientgtk-3.0"],
                    "spice_viewer": ["virt-viewer", "spice-client-gtk"],
                    "vnc_viewer":   ["gvncviewer", "tigervnc-viewer"],
                },
                "dnf": {
                    "spice_gtk_py": ["python3-gobject", "spice-gtk3"],
                    "spice_viewer": ["virt-viewer", "spice-gtk-tools"],
                    "vnc_viewer":   ["gvncviewer", "tigervnc"],
                },
                "pacman": {
                    "spice_gtk_py": ["python-gobject", "spice-gtk"],
                    "spice_viewer": ["virt-viewer", "spice-gtk"],
                    "vnc_viewer":   ["gtk-vnc", "tigervnc"],
                },
            }
            if manager not in pkg_map:
                QMessageBox.warning(
                    self, self.tr("Consola remota"),
                    self.tr(
                        "El gestor '{0}' aun no tiene nombres de paquetes\n"
                        "configurados."
                    ).format(manager),
                )
                return

            prefix = _priv_prefix(prefer_gui=True)
            if prefix is None:
                QMessageBox.warning(
                    self, self.tr("Consola remota"),
                    self.tr("No hay pkexec ni sudo para instalar paquetes."),
                )
                return

            self.log_message(
                "==> Consola remota: instalando dependencias con "
                + manager + "...")
            if manager == "apt":
                _run(prefix, ["apt-get", "update"])

            # Instalar grupo a grupo para que si un nombre no existe en el
            # repo, los demas grupos se intenten igualmente.
            for key in ("spice_gtk_py", "spice_viewer", "vnc_viewer"):
                if key == "spice_gtk_py" and st["spice_gtk_py"]:
                    continue
                if key == "spice_viewer" and st["spice_viewer_path"]:
                    continue
                if key == "vnc_viewer" and st["vnc_viewer_path"]:
                    continue
                pkgs = pkg_map[manager].get(key, [])
                if not pkgs:
                    continue
                try:
                    _run(prefix, _install_cmd(manager, pkgs))
                except Exception as _e:
                    self.log_message(
                        "[AVISO] Consola remota: instalacion parcial ({0}): "
                        "{1}".format(key, _e))

            self.refresh_console_deps_status(silent=True)
            try:
                self._cd_result_label.setText(
                    "Dependencias de consola revisadas. Si acabas de "
                    "instalar spice-gtk, REINICIA la app para que el "
                    "modulo Python se cargue."
                )
                self._cd_result_label.setStyleSheet(
                    "font-size: 11px; color:#2e7d32;")
                self._cd_result_label.setVisible(True)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Consola remota"),
                self.tr("Error durante la reparacion:\n\n{0}").format(e),
            )
        finally:
            QApplication.restoreOverrideCursor()
            try:
                self.btn_cd_check.setEnabled(True)
            except Exception:
                pass
            try:
                self.refresh_console_deps_status(silent=True)
            except Exception:
                pass


# console_deps_host_check_v1
