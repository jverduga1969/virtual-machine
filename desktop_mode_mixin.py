# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: modo Desktop (marcador desktop_mode_v1).

Permite lanzar una VM a pantalla completa sobre una VT dedicada
usando el launcher externo `desktop_mode.py`. Ese launcher orquesta:

    openvt -> setpriv -> seatd -> cage -m last -> QEMU -> guest

Este mixin solo se encarga de la parte GUI:
  - Mostrar el boton "Desktop Mode" en el Resumen y en el menu contextual.
  - Habilitarlo solo cuando la VM esta apagada y el launcher esta
    instalado en el sistema.
  - Pedir el TTY destino (persistido en QSettings).
  - Lanzar el subproceso y no esperar (la GUI sigue viva en su VT).
  - Dejar que el watchdog normal detecte el fin de la VM.

NO toca workers.py ni la logica de arranque normal.
"""
# Marcador adicional: desktop_mode_cleanup_v2
# desktop_mode_diag_cleanup_v1

import os
import sys
import subprocess

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox, QInputDialog


class DesktopModeMixin:
    # Marcador: desktop_mode_v1

    _DESKTOP_MODE_DEFAULT_TTY = 3
    _DESKTOP_MODE_TTY_MIN = 2
    _DESKTOP_MODE_TTY_MAX = 12
    _DESKTOP_MODE_WRAPPER = "/usr/local/bin/virtual-machine-desktop"

    # ------------------------------------------------------------------
    # Rutas y disponibilidad
    # ------------------------------------------------------------------

    def _desktop_mode_repo_dir(self):
        """Directorio del repo (donde vive desktop_mode.py)."""
        return os.path.dirname(os.path.abspath(__file__))

    def _desktop_mode_launcher_path(self):
        return os.path.join(self._desktop_mode_repo_dir(), "desktop_mode.py")

    def _desktop_mode_wrapper_path(self):
        return self._DESKTOP_MODE_WRAPPER

    def _desktop_mode_is_available(self):
        """True si TODOS los requisitos para Desktop Mode estan OK.

        Marcador: desktop_mode_mixin_v2

        Cadena:
            setpriv -> xinit -> Xorg :N vtN -> matchbox -> QEMU
        """
        try:
            from desktop_mode_host_check import get_desktop_mode_status
            st = get_desktop_mode_status(self._desktop_mode_repo_dir())
        except Exception:
            return False
        if not os.path.isfile(self._desktop_mode_launcher_path()):
            return False
        return bool(
            st.get("wrapper_installed")
            and st.get("conf_present")
            and st.get("xinit_installed")
            and st.get("matchbox_installed")
            and st.get("xorg_installed")
            and st.get("user_in_tty_group")
            and st.get("xwrapper_config_ok")
            and st.get("launcher_installed")
        )

    def _desktop_mode_unsupported_reason(self):
        """Motivo por el que Desktop Mode no esta disponible, o ''.

        Marcador: desktop_mode_mixin_v2
        """
        try:
            from desktop_mode_host_check import get_desktop_mode_status
            st = get_desktop_mode_status(self._desktop_mode_repo_dir())
        except Exception as e:
            return f"No se pudo comprobar el estado de Desktop Mode: {e}"

        missing = []
        if not st.get("launcher_installed"):
            missing.append("  \u2022 Falta desktop_mode.py en el repo.")
        if not st.get("wrapper_installed"):
            missing.append(
                "  \u2022 Falta el wrapper sudo en /usr/local/bin/.\n"
                "    Instalalo con: sudo bash packaging/install-wrapper.sh")
        if not st.get("conf_present"):
            missing.append(
                "  \u2022 Falta /etc/virtual-machine.conf.\n"
                "    Reinstala el wrapper: sudo bash packaging/install-wrapper.sh")
        if not st.get("xinit_installed"):
            missing.append(
                "  \u2022 Falta xinit.\n"
                "    Instalalo con: sudo apt install xinit")
        if not st.get("matchbox_installed"):
            missing.append(
                "  \u2022 Falta matchbox-window-manager.\n"
                "    Instalalo con: sudo apt install matchbox-window-manager")
        if not st.get("xorg_installed"):
            missing.append(
                "  \u2022 Falta Xorg.\n"
                "    Instalalo con: sudo apt install xserver-xorg-core")
        if not st.get("user_in_tty_group"):
            missing.append(
                "  \u2022 El usuario no esta en el grupo 'tty'.\n"
                "    Anadelo con: sudo usermod -aG tty $USER\n"
                "    Despues CIERRA SESION COMPLETA y vuelve a entrar.")
        if not st.get("xwrapper_config_ok"):
            missing.append(
                "  \u2022 /etc/X11/Xwrapper.config no permite allowed_users=anybody.\n"
                "    Se arregla desde el panel 'Configuracion Host'.")
        if not missing:
            return ""
        return "Desktop Mode no esta disponible:\n\n" + "\n".join(missing)


    # desktop_mode_staticmethod_fix_v1: restaurado el decorador.
    @staticmethod
    def _desktop_friendly_name():
        """Nombre legible del escritorio del host, o '' si no se
        puede determinar.

        Marcador: desktop_mode_de_name_v1

        Orden de lectura: XDG_CURRENT_DESKTOP, XDG_SESSION_DESKTOP,
        DESKTOP_SESSION. En Cinnamon, XDG_CURRENT_DESKTOP suele ser
        "X-Cinnamon"; en KDE es "KDE"; en GNOME es "ubuntu:GNOME" o
        "GNOME". Se toma el ultimo token tras dos puntos y se mapea
        a un nombre legible. Si no se reconoce, se devuelve el
        token tal cual (mejor mostrarlo que inventar).
        """
        import os as _os
        raw = (
            _os.environ.get("XDG_CURRENT_DESKTOP")
            or _os.environ.get("XDG_SESSION_DESKTOP")
            or _os.environ.get("DESKTOP_SESSION")
            or ""
        ).strip()
        if not raw:
            return ""
        token = raw.split(":")[-1].strip()
        if not token:
            return ""
        table = {
            "kde":        "KDE Plasma",
            "plasma":     "KDE Plasma",
            "gnome":      "GNOME",
            "x-cinnamon": "Cinnamon",
            "cinnamon":   "Cinnamon",
            "xfce":       "XFCE",
            "mate":       "MATE",
            "lxqt":       "LXQt",
            "lxde":       "LXDE",
            "budgie":     "Budgie",
            "deepin":     "Deepin",
            "pantheon":   "Pantheon",
            "unity":      "Unity",
            "sway":       "Sway",
            "i3":         "i3",
            "hyprland":   "Hyprland",
        }
        return table.get(token.lower(), token)


    # ------------------------------------------------------------------
    # Preferencia del TTY destino
    # ------------------------------------------------------------------

    def _desktop_mode_tty(self):
        """TTY guardado en QSettings, con validacion."""
        try:
            tty = int(QSettings().value(
                "desktop/tty", self._DESKTOP_MODE_DEFAULT_TTY))
        except (TypeError, ValueError):
            tty = self._DESKTOP_MODE_DEFAULT_TTY
        if not (self._DESKTOP_MODE_TTY_MIN <= tty <= self._DESKTOP_MODE_TTY_MAX):
            tty = self._DESKTOP_MODE_DEFAULT_TTY
        return tty

    def _save_desktop_mode_tty(self, tty):
        try:
            QSettings().setValue("desktop/tty", int(tty))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Estado del boton (llamado desde refresh_vm_runtime_status)
    # ------------------------------------------------------------------

    def _update_desktop_mode_button_state(self, state=None):
        """Habilita/deshabilita la entrada "Iniciar en Desktop Mode" del
        menu Iniciar.

        Reglas:
          - Sin VM seleccionada -> deshabilitado.
          - VM corriendo o pausada -> deshabilitado.
          - Launcher o wrapper ausentes -> deshabilitado (tooltip explica).
          - VM apagada + todo presente -> habilitado.
        """
        act = getattr(self, "action_vm_start_desktop", None)
        if act is None:
            return
        if state is None:
            if getattr(self, "current_vm_dir", None):
                try:
                    state = self._runtime_state(
                        os.path.basename(self.current_vm_dir))
                except Exception:
                    state = "stopped"
            else:
                state = "stopped"
        try:
            has_vm = bool(getattr(self, "current_vm_dir", None))
            available = self._desktop_mode_is_available()
            enabled = has_vm and available and (state == "stopped")
            act.setEnabled(enabled)

            if not available:
                act.setToolTip(
                    "Desktop Mode no disponible en este equipo.\n\n"
                    + self._desktop_mode_unsupported_reason()
                )
            elif not has_vm:
                act.setToolTip(
                    "Selecciona una maquina virtual apagada para usar\n"
                    "Desktop Mode."
                )
            elif state != "stopped":
                act.setToolTip(
                    "Desktop Mode requiere que la VM este apagada.\n"
                    "La VM corre en una VT dedicada; un segundo QEMU\n"
                    "sobre el mismo disco corromperia los datos."
                )
            else:
                # desktop_mode_de_name_v1: sustituir el "KDE"
                # hardcodeado por el nombre real del escritorio del host.
                _de = self._desktop_friendly_name()
                if _de:
                    act.setToolTip(
                        "Arranca esta VM a pantalla completa en una VT dedicada\n"
                        f"usando Cage. La sesion de {_de} sigue intacta en su TTY.\n\n"
                        f"Al apagar la VM, vuelves automaticamente a {_de}."
                    )
                else:
                    act.setToolTip(
                        "Arranca esta VM a pantalla completa en una VT dedicada\n"
                        "usando Cage. Tu sesion grafica sigue intacta en su TTY.\n\n"
                        "Al apagar la VM, vuelves automaticamente a tu sesion grafica."
                    )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Punto de entrada del boton
    # ------------------------------------------------------------------

    def _desktop_mode_occupied_ttys(self, exclude_vm_dir=None):
        """Set de TTYs ocupadas por otras VMs en Desktop Mode."""
        out = set()
        for vm_dir, entry in self._desktop_mode_running_map().items():
            if exclude_vm_dir and vm_dir == exclude_vm_dir:
                continue
            try:
                if isinstance(entry, tuple):
                    out.add(int(entry[0]))
                else:
                    out.add(int(entry))
            except Exception:
                continue
        return out

    def _desktop_mode_running_list(self, exclude_vm_dir=None):
        """Lista [(vm_name, tty)] de VMs en Desktop Mode, excluyendo una."""
        out = []
        for vm_dir, entry in self._desktop_mode_running_map().items():
            if exclude_vm_dir and vm_dir == exclude_vm_dir:
                continue
            try:
                tty = int(entry[0] if isinstance(entry, tuple) else entry)
                name = os.path.basename(vm_dir)
                out.append((name, tty))
            except Exception:
                continue
        out.sort(key=lambda x: x[1])
        return out

    # ------------------------------------------------------------------
    # Diálogo único de confirmación (marcador desktop_mode_single_dialog_v1)
    # ------------------------------------------------------------------

    def _desktop_mode_confirm_dialog(self, vm_name):
        """Diálogo único: elegir TTY + confirmar el arranque.

        Reemplaza los dos diálogos que había antes (QInputDialog para el
        TTY + QMessageBox de confirmación). El combo ofrece los TTY del
        rango configurado menos el del escritorio del host (para no
        destruir la sesión gráfica al hacer openvt -f).

        Devuelve {"tty": int} si el usuario acepta, o None si cancela.
        """
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
            QPushButton,
        )
        from PyQt6.QtCore import Qt

        try:
            from desktop_mode_host_check import detect_graphical_tty
            graphical_tty = detect_graphical_tty()
        except Exception:
            graphical_tty = None

        # TTYs ya ocupadas por otras VMs en Desktop Mode.
        exclude_dir = getattr(self, "current_vm_dir", None)
        occupied = self._desktop_mode_occupied_ttys(exclude_vm_dir=exclude_dir)
        other_vms = self._desktop_mode_running_list(exclude_vm_dir=exclude_dir)

        all_ttys = list(range(
            self._DESKTOP_MODE_TTY_MIN,
            self._DESKTOP_MODE_TTY_MAX + 1,
        ))
        offered = [
            t for t in all_ttys
            if t != graphical_tty and t not in occupied
        ]
        if not offered:
            # Todos los TTY del rango están en uso (KDE + VMs).
            from PyQt6.QtWidgets import QMessageBox as _QMB
            _QMB.warning(
                self, self.tr("Desktop Mode"),
                self.tr(
                    "No hay ningún TTY libre en el rango {0}-{1}.\n\n"
                    "El escritorio del host está en tty{2} y las VMs "
                    "en Desktop Mode ocupan: {3}.\n\n"
                    "Apaga alguna VM o edita el rango de TTY en el código."
                ).format(
                    self._DESKTOP_MODE_TTY_MIN,
                    self._DESKTOP_MODE_TTY_MAX,
                    graphical_tty if graphical_tty else "?",
                    ", ".join(f"tty{t}" for t in sorted(occupied)) or "—",
                ),
            )
            return None

        saved = self._desktop_mode_tty()
        if saved not in offered:
            saved = offered[0]

        if graphical_tty:
            return_shortcut = f"Ctrl+Alt+F{graphical_tty}"
        else:
            return_shortcut = ""

        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Desktop Mode"))
        dlg.setModal(True)
        dlg.setMinimumWidth(460)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(10)

        title = QLabel(
            "<b>" + self.tr("{0} se iniciará en Desktop Mode.").format(vm_name) + "</b>"
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(title)

        row = QHBoxLayout()
        row.addWidget(QLabel(self.tr("TTY destino:")))
        combo = QComboBox()
        for t in offered:
            combo.addItem(f"tty{t}", t)
        idx = combo.findData(saved)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        row.addWidget(combo)
        row.addStretch(1)
        lay.addLayout(row)

        if graphical_tty:
            # desktop_mode_de_name_v1: nombre real del escritorio.
            _de = self._desktop_friendly_name()
            if _de:
                info_text = self.tr(
                    "El escritorio del host ({0}) está en tty{1}.\n"
                    "Esa VT no se ofrece como destino."
                ).format(_de, graphical_tty)
            else:
                info_text = self.tr(
                    "El escritorio del host está en tty{0}.\n"
                    "Esa VT no se ofrece como destino."
                ).format(graphical_tty)
        else:
            info_text = self.tr(
                "No se pudo detectar el TTY del escritorio del host."
            )
        if other_vms:
            info_text += "\n\n" + self.tr("Otras VMs en Desktop Mode:")
            for _n, _t in other_vms:
                info_text += f"\n  • {_n} (tty{_t})"
        info = QLabel(info_text)
        info.setStyleSheet("color:#666; font-size:11px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        lay.addSpacing(4)

        msg = QLabel("")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWordWrap(True)

        # desktop_mode_de_name_v1: nombre real del escritorio, o
        # "tu sesion grafica" como fallback.
        _de = self._desktop_friendly_name()
        _de_label = _de if _de else self.tr("tu sesion grafica")

        def _refresh_msg(*_a):
            tty_chosen = combo.currentData()
            if return_shortcut:
                text = self.tr(
                    "La pantalla cambiará en 1-2 segundos.\n"
                    "Volverás a {0} cuando la VM se apague,\n"
                    "o pulsando <b>{1}</b> en cualquier momento.\n\n"
                    "Para volver a la VM desde {0}, pulsa <b>Ctrl+Alt+F{2}</b>."
                ).format(_de_label, return_shortcut, tty_chosen)
            else:
                text = self.tr(
                    "La pantalla cambiará en 1-2 segundos.\n"
                    "Volverás a {0} cuando la VM se apague."
                ).format(_de_label)
            msg.setText(text)

        combo.currentIndexChanged.connect(_refresh_msg)
        _refresh_msg()
        lay.addWidget(msg)

        lay.addSpacing(6)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton(self.tr("Cancelar"))
        cancel.clicked.connect(dlg.reject)
        btns.addWidget(cancel)
        ok = QPushButton(self.tr("Iniciar"))
        ok.setDefault(True)
        ok.clicked.connect(dlg.accept)
        btns.addWidget(ok)
        lay.addLayout(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return {"tty": combo.currentData()}


    def start_fullscreen_mode(self):
        """Arranca la VM con la ventana de QEMU maximizada.

        Marcador: desktop_mode_to_fullscreen_v1

        Sustituye a Desktop Mode. No usa cage, VT dedicada, ni wrapper
        sudo: solo arranca el flujo normal de la app con un flag que
        hace que el worker anada full-screen=on al -display de QEMU.
        Funciona en Cinnamon, GNOME, KDE, XFCE y demas, porque no
        depende de logind, seatd, ni sudoers.
        """
        # 1) Hay VM seleccionada?
        if not getattr(self, "current_vm_dir", None):
            QMessageBox.information(
                self, self.tr("Pantalla completa"),
                self.tr("Selecciona primero una maquina virtual."),
            )
            return

        vm_name = os.path.basename(self.current_vm_dir)

        # 2) La VM debe estar apagada.
        try:
            state = self._runtime_state(vm_name)
        except Exception:
            state = "stopped"
        if state != "stopped":
            QMessageBox.warning(
                self, self.tr("Pantalla completa"),
                self.tr(
                    "La VM '{0}' no esta apagada.\n\n"
                    "Arrancarla de nuevo chocaria con el lock del disco.\n"
                    "Apagala primero."
                ).format(vm_name),
            )
            return

        # 3) Si hay cambios pendientes, guardarlos antes.
        try:
            if (getattr(self, "_has_pending_changes", None)
                    and self._has_pending_changes()):
                _box = QMessageBox(self)
                _box.setWindowTitle(self.tr("Cambios sin guardar"))
                _box.setIcon(QMessageBox.Icon.Question)
                _box.setText(self.tr(
                    "La VM '{0}' tiene cambios sin guardar.\n\n"
                    "El arranque lee la configuracion del disco.\n"
                    "Guardala primero para que los cambios apliquen."
                ).format(vm_name))
                _btn_save = _box.addButton(
                    self.tr("\U0001f4be Guardar y arrancar"),
                    QMessageBox.ButtonRole.AcceptRole,
                )
                _btn_discard = _box.addButton(
                    self.tr("\u21ba Descartar y arrancar"),
                    QMessageBox.ButtonRole.DestructiveRole,
                )
                _btn_cancel = _box.addButton(
                    self.tr("Cancelar"),
                    QMessageBox.ButtonRole.RejectRole,
                )
                _box.setDefaultButton(_btn_save)
                _box.exec()
                clicked = _box.clickedButton()
                if clicked is _btn_cancel:
                    return
                if clicked is _btn_save:
                    if not self._save_config_from_ui():
                        return
                    try:
                        self.open_vm(vm_name)
                    except Exception:
                        pass
        except Exception:
            pass

        # 4) Marcar el flag y arrancar por el flujo normal.
        self._pending_fullscreen = True
        self._pending_snapshot = False  # no es modo demo
        try:
            self.log_message(
                "==> Pantalla completa: arrancando '{0}' con QEMU "
                "maximizado en el escritorio del host.".format(vm_name)
            )
        except Exception:
            pass
        try:
            self.start_installation()
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Pantalla completa"),
                self.tr(
                    "No se pudo arrancar la VM.\n\n{0}"
                ).format(e),
            )


    def start_desktop_mode(self):
        """Lanza Desktop Mode para la VM seleccionada."""
        # 1) Disponibilidad del launcher/wrapper.
        if not self._desktop_mode_is_available():
            QMessageBox.warning(
                self, self.tr("Desktop Mode"),
                self.tr(
                    "Desktop Mode no esta disponible en este equipo.\n\n{0}"
                ).format(self._desktop_mode_unsupported_reason()),
            )
            return

        # 2) VM seleccionada.
        if not getattr(self, "current_vm_dir", None):
            QMessageBox.information(
                self, self.tr("Desktop Mode"),
                self.tr("Selecciona primero una maquina virtual."),
            )
            return

        vm_name = os.path.basename(self.current_vm_dir)

        # 3) VM apagada.
        try:
            state = self._runtime_state(vm_name)
        except Exception:
            state = "stopped"
        if state != "stopped":
            QMessageBox.warning(
                self, self.tr("Desktop Mode"),
                self.tr(
                    "La VM '{0}' no esta apagada.\n\n"
                    "Desktop Mode lanza un QEMU nuevo sobre la VT dedicada.\n"
                    "Si la VM ya esta corriendo, el segundo QEMU chocaria\n"
                    "con el lock del disco. Apagala primero."
                ).format(vm_name),
            )
            return

        # 4) Cambios pendientes: guardar antes de arrancar.
        try:
            if (getattr(self, "_has_pending_changes", None)
                    and self._has_pending_changes()):
                _box = QMessageBox(self)
                _box.setWindowTitle(self.tr("Cambios sin guardar"))
                _box.setIcon(QMessageBox.Icon.Question)
                _box.setText(self.tr(
                    "La VM '{0}' tiene cambios sin guardar.\n\n"
                    "Desktop Mode lee la configuracion del disco. "
                    "Guardala primero para que los cambios apliquen."
                ).format(vm_name))
                _btn_save = _box.addButton(
                    self.tr("\U0001f4be Guardar y arrancar"),
                    QMessageBox.ButtonRole.AcceptRole,
                )
                _btn_discard = _box.addButton(
                    self.tr("\u21ba Descartar y arrancar"),
                    QMessageBox.ButtonRole.DestructiveRole,
                )
                _btn_cancel = _box.addButton(
                    self.tr("Cancelar"),
                    QMessageBox.ButtonRole.RejectRole,
                )
                _box.setDefaultButton(_btn_save)
                _box.exec()
                clicked = _box.clickedButton()
                if clicked is _btn_cancel:
                    return
                if clicked is _btn_save:
                    if not self._save_config_from_ui():
                        return
                    try:
                        self.open_vm(vm_name)
                    except Exception:
                        pass
        except Exception:
            pass

        # 5) Diálogo único: elegir TTY + confirmar en una sola ventana.
        # Marcador: desktop_mode_single_dialog_v1
        result = self._desktop_mode_confirm_dialog(vm_name)
        if not result:
            return
        tty = int(result["tty"])
        self._save_desktop_mode_tty(tty)

        # 7) Lanzar. No esperar: la GUI sigue viva en su VT.
        launcher = self._desktop_mode_launcher_path()
        argv = [
            sys.executable or "python3",
            launcher,
            "--vm", vm_name,
            "--tty", str(tty),
        ]
        try:
            self.log_message(
                f"==> Desktop Mode: lanzando '{vm_name}' en tty{tty}..."
            )
            self.log_message("    " + " ".join(argv))
            # desktop_mode_app_freeze_v1: activar ventana de gracia
            # de 20s durante la cual _runtime_state no consulta QMP.
            # Asi el arranque de QEMU no bloquea el hilo de UI.
            try:
                import time as _time
                self._desktop_mode_grace_until = _time.time() + 20.0
            except Exception:
                pass
            _log_path = os.path.join(
                self.current_vm_dir, "desktop_mode_launch.log")
            _log_fd = None
            try:
                _log_fd = open(_log_path, "ab")
            except Exception:
                _log_fd = None
            try:
                # stdin=DEVNULL: evitar que el wrapper y sus hijos
                # hereden el TTY de la app (podia suspenderla al
                # cambiar de VT).
                subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=_log_fd if _log_fd is not None else subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                )
            finally:
                if _log_fd is not None:
                    try:
                        _log_fd.close()
                    except Exception:
                        pass
            self.log_message(
                "==> Desktop Mode: proceso lanzado. La pantalla cambiara "
                "en 1-2 segundos. El watchdog detectara el fin de la VM "
                "cuando se apague."
            )
            # desktop_mode_qemu_pid_poll_v1: no marcar [Desktop ttyN]
            # de inmediato. Esperar a que aparezca qemu.pid en la carpeta
            # de la VM. Asi no marcamos cuando el wrapper falla antes de
            # arrancar QEMU (bug: "dice que inicio pero no lo hizo").
            self._desktop_mode_poll_qemu_pid(
                self.current_vm_dir, int(tty), attempts_left=32)
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Desktop Mode"),
                self.tr(
                    "No se pudo lanzar Desktop Mode.\n\n{0}"
                ).format(e),
            )


    # ------------------------------------------------------------------
    # Sección "Desktop Mode: requisitos y estado" en Configuración Host.
    # Marcador: desktop_mode_host_check_v1
    # ------------------------------------------------------------------

    def _build_desktop_mode_host_ui(self, parent_layout):
        """Panel "Desktop Mode" en Configuracion Host.

        Marcador: desktop_mode_mixin_v2
        """
        from PyQt6.QtWidgets import (
            QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
            QPushButton,
        )
        group = QGroupBox(self.tr("Desktop Mode (VM en una VT dedicada)"))
        lay = QVBoxLayout(group)

        purpose = QLabel(self.tr(
            "Para que sirve: arranca la VM a pantalla completa en una VT "
            "dedicada, sin el escritorio de fondo. Al apagar la VM, vuelves "
            "automaticamente a tu sesion grafica."
        ))
        purpose.setWordWrap(True)
        purpose.setStyleSheet("color: #666; font-size: 11px;")
        lay.addWidget(purpose)

        info_row = QHBoxLayout()
        self._dm_distro_label = QLabel("\u2014")
        self._dm_manager_label = QLabel("\u2014")
        self._dm_graphical_tty_label = QLabel("\u2014")
        for _lbl, _title in (
            (self._dm_distro_label, self.tr("Distribucion:")),
            (self._dm_manager_label, self.tr("Gestor:")),
            (self._dm_graphical_tty_label, self.tr("TTY grafico:")),
        ):
            info_row.addWidget(QLabel(f"<b>{_title}</b>"))
            info_row.addWidget(_lbl)
            info_row.addSpacing(12)
        info_row.addStretch(1)
        lay.addLayout(info_row)

        self._dm_check_labels = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        _checks = [
            ("xinit",     self.tr("xinit (arranque del servidor X)")),
            ("matchbox",  self.tr("matchbox-window-manager")),
            ("xorg",      self.tr("Xorg (servidor X)")),
            ("tty_group", self.tr("Usuario en el grupo 'tty'")),
            ("xwrapper",  self.tr("Xwrapper.config (allowed_users=anybody)")),
            ("wrapper",   self.tr("Wrapper sudo instalado")),
            ("conf",      self.tr("/etc/virtual-machine.conf presente")),
            ("sudoers",   self.tr("Regla /etc/sudoers.d/ presente")),
            ("launcher",  self.tr("Launcher desktop_mode.py en el repo")),
        ]
        for _i, (_key, _label) in enumerate(_checks):
            _icon = QLabel("\u23f3")
            _icon.setFixedWidth(20)
            _lbl = QLabel(_label)
            _lbl.setWordWrap(True)
            self._dm_check_labels[_key] = _icon
            grid.addWidget(_icon, _i, 0)
            grid.addWidget(_lbl, _i, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)

        self._dm_result_label = QLabel("")
        self._dm_result_label.setWordWrap(True)
        self._dm_result_label.setVisible(False)
        lay.addWidget(self._dm_result_label)

        btns = QHBoxLayout()
        self.btn_dm_check = QPushButton(self.tr("\U0001f504 Comprobar"))
        self.btn_dm_check.clicked.connect(
            lambda: self.refresh_desktop_mode_host_status(silent=False)
        )
        self.btn_dm_repair = QPushButton(self.tr("\U0001f6e0\ufe0f Reparar todo"))
        self.btn_dm_repair.setToolTip(self.tr(
            "Instala lo que falte (una sola autenticacion):\n"
            "  \u2022 xinit y matchbox-window-manager.\n"
            "  \u2022 Grupo 'tty' del usuario.\n"
            "  \u2022 /etc/X11/Xwrapper.config con allowed_users=anybody.\n"
            "  \u2022 Wrapper sudo y regla /etc/sudoers.d/."
        ))
        self.btn_dm_repair.clicked.connect(self.repair_desktop_mode_host)
        btns.addWidget(self.btn_dm_check)
        btns.addWidget(self.btn_dm_repair)
        btns.addStretch(1)
        lay.addLayout(btns)

        parent_layout.addWidget(group)

        try:
            from PyQt6.QtCore import QTimer as _QTimer
            _QTimer.singleShot(
                150,
                lambda: self.refresh_desktop_mode_host_status(silent=True),
            )
        except Exception:
            pass


    def _show_systemd_258_warning(self):
        """systemd_258_warn_btn_v1: aviso bajo demanda."""
        try:
            from desktop_mode_host_check import get_desktop_mode_status
            st = get_desktop_mode_status(self._desktop_mode_repo_dir())
        except Exception:
            st = {}
        _sv = st.get("systemd_version") or "?"
        QMessageBox.warning(
            self, self.tr("Desktop Mode: systemd incompatible"),
            self.tr(
                "La version de systemd de este sistema es {0}.\n\n"
                "systemd 258+ tiene un bug conocido (#43352) que\n"
                "impide volver a la VT de la VM desde KDE: la\n"
                "pantalla no cambia y el teclado/raton quedan\n"
                "bloqueados.\n\n"
                "Workaround: downgrade de systemd a 257.9-1 y\n"
                "bloqueo con IgnorePkg en /etc/pacman.conf.\n\n"
                "Ver 'Desktop Mode' del traspaso para el detalle."
            ).format(_sv),
        )

    def refresh_desktop_mode_host_status(self, silent=False):
        """Re-detecta el estado y actualiza los iconos / etiquetas.

        Marcador: desktop_mode_mixin_v2
        """
        try:
            from desktop_mode_host_check import get_desktop_mode_status
        except Exception as e:
            try:
                self.log_message(
                    "[AVISO] desktop_mode_host_check no disponible: "
                    + str(e))
            except Exception:
                pass
            return

        try:
            status = get_desktop_mode_status(self._desktop_mode_repo_dir())
        except Exception as e:
            try:
                self.log_message(
                    "[AVISO] Error detectando requisitos de Desktop Mode: "
                    + str(e))
            except Exception:
                pass
            return

        def _set(key, ok_flag, tooltip=""):
            lbl = getattr(self, "_dm_check_labels", {}).get(key)
            if lbl is None:
                return
            lbl.setText("\u2705" if ok_flag else "\u274C")
            lbl.setToolTip(tooltip or "")

        _set("xinit", status.get("xinit_installed"),
             status.get("xinit_path") or "no encontrado en PATH")
        _set("matchbox", status.get("matchbox_installed"),
             status.get("matchbox_path") or "no encontrado en PATH")
        _set("xorg", status.get("xorg_installed"),
             status.get("xorg_path") or "no encontrado")
        _set("tty_group", status.get("user_in_tty_group"),
             "usuario en el grupo tty" if status.get("user_in_tty_group")
             else "hay que anadirlo al grupo tty y reloguear")
        _set("xwrapper", status.get("xwrapper_config_ok"),
             status.get("xwrapper_config_path") or "no configurado")
        _set("wrapper", status.get("wrapper_installed"),
             "instalado" if status.get("wrapper_installed")
             else "no instalado en /usr/local/bin")
        _set("conf", status.get("conf_present"),
             status.get("conf_path") or "no presente")
        _set("sudoers", status.get("sudoers_installed"),
             "regla presente" if status.get("sudoers_installed")
             else "regla no encontrada en /etc/sudoers.d")
        _set("launcher", status.get("launcher_installed"),
             status.get("launcher_path") or "no encontrado")

        try:
            tty = status.get("graphical_tty")
            self._dm_graphical_tty_label.setText(
                f"tty{tty}" if tty else self.tr("no detectado"))
            self._dm_distro_label.setText(status.get("distro") or "\u2014")
            self._dm_manager_label.setText(
                status.get("package_manager") or "\u2014")
        except Exception:
            pass

        all_ok = all([
            status.get("xinit_installed"),
            status.get("matchbox_installed"),
            status.get("xorg_installed"),
            status.get("user_in_tty_group"),
            status.get("xwrapper_config_ok"),
            status.get("wrapper_installed"),
            status.get("conf_present"),
            status.get("sudoers_installed"),
            status.get("launcher_installed"),
        ])
        try:
            self.btn_dm_repair.setEnabled(not all_ok)
        except Exception:
            pass
        if not silent:
            try:
                self.log_message(
                    "==> Desktop Mode: estado comprobado. "
                    + ("Todo OK." if all_ok else "Hay requisitos pendientes."))
            except Exception:
                pass
    def repair_desktop_mode_host(self):
        """Lanza la reparación con una sola autenticación."""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        from PyQt6.QtCore import Qt

        try:
            from desktop_mode_host_check import (
                get_desktop_mode_status, repair_desktop_mode,
            )
            _pre = get_desktop_mode_status(self._desktop_mode_repo_dir())
            _need_pkgs = (not _pre.get("cage_installed")
                          or not _pre.get("seatd_installed"))
            if _need_pkgs and not _pre.get("package_manager"):
                QMessageBox.warning(
                    self, self.tr("Reparar Desktop Mode"),
                    self.tr(
                        "No se pudo detectar el gestor de paquetes de este\n"
                        "sistema. Instala 'cage' y 'seatd' manualmente y\n"
                        "vuelve a comprobar."
                    ),
                )
                return
            if (not _pre.get("wrapper_installed")
                    and not _pre.get("wrapper_source")):
                QMessageBox.warning(
                    self, self.tr("Reparar Desktop Mode"),
                    self.tr(
                        "El wrapper no está instalado y no se encontró su\n"
                        "archivo fuente en el repo. Coloca el archivo\n"
                        "'virtual-machine-desktop' en la raíz del proyecto\n"
                        "y vuelve a intentarlo."
                    ),
                )
                return
        except Exception:
            pass

        # systemd_258_warn_v1: si systemd >= 258, Desktop Mode no
        # funcionara aunque todos los requisitos pasen. Avisar ANTES
        # del dialogo de confirmacion de "Reparar todo".
        try:
            if not _pre.get("systemd_ok", True):
                _sv = _pre.get("systemd_version") or "?"
                QMessageBox.warning(
                    self, self.tr("Desktop Mode: systemd incompatible"),
                    self.tr(
                        "La version de systemd de este sistema es {0}.\n\n"
                        "systemd 258+ tiene un bug conocido (#43352) que\n"
                        "impide volver a la VT de la VM desde KDE: la\n"
                        "pantalla no cambia y el teclado/raton quedan\n"
                        "bloqueados.\n\n"
                        "Los requisitos de Desktop Mode pueden estar todos\n"
                        "OK, pero el cambio de VT no funcionara.\n\n"
                        "Workaround: downgrade de systemd a 257.9-1 y\n"
                        "bloqueo con IgnorePkg en /etc/pacman.conf.\n\n"
                        "Ver 'Desktop Mode' del traspaso para el detalle."
                    ).format(_sv),
                )
                return
        except NameError:
            # _pre no definido (raro): no bloqueamos la reparacion.
            pass

        reply = QMessageBox.question(
            self, self.tr("Reparar Desktop Mode"),
            self.tr(
                "Se va a intentar instalar/activar todo lo necesario para\n"
                "Desktop Mode. Se pedirá autenticación UNA sola vez.\n\n"
                "Acciones posibles:\n"
                "  \u2022 Instalar 'cage' y 'seatd' con el gestor del sistema.\n"
                "  \u2022 Activar seatd.service.\n"
                "  \u2022 Crear el grupo 'seat' y añadir al usuario actual.\n"
                "  \u2022 Copiar el wrapper a /usr/local/bin.\n"
                "  \u2022 Crear la regla /etc/sudoers.d/virtual-machine-desktop\n"
                "    (validada con visudo antes de activarse).\n\n"
                "\u00bfContinuar?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.btn_dm_repair.setEnabled(False)
            self.btn_dm_check.setEnabled(False)
        except Exception:
            pass
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result = repair_desktop_mode(
                self._desktop_mode_repo_dir(),
                log_func=lambda msg: self.log_message(msg),
            )
            msg = "\n".join(result.get("details", [])) or "(sin cambios)"
            try:
                self._dm_result_label.setText(
                    ("\u2705 " if result.get("ok") else "\u26A0 ") + msg
                )
                self._dm_result_label.setStyleSheet(
                    "font-size: 11px; "
                    + ("color:#2e7d32;" if result.get("ok")
                       else "color:#b36b00;")
                )
                self._dm_result_label.setVisible(True)
            except Exception:
                pass
            if not result.get("ok"):
                QMessageBox.warning(
                    self, self.tr("Reparar Desktop Mode"),
                    self.tr(
                        "Algunas acciones no se completaron. Revisa el\n"
                        "detalle en esta sección o en la Consola de\n"
                        "Progreso."
                    ),
                )
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Reparar Desktop Mode"),
                self.tr("Error durante la reparación:\n\n{0}").format(e),
            )
        finally:
            QApplication.restoreOverrideCursor()
            try:
                self.btn_dm_check.setEnabled(True)
            except Exception:
                pass
            try:
                self.refresh_desktop_mode_host_status(silent=True)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Estado runtime de Desktop Mode (marcador desktop_mode_v1)
    # ------------------------------------------------------------------
    # Mientras la app lanza una VM en Desktop Mode, guarda
    # {vm_dir: (tty, seen_running)} para que la lista lateral muestre
    # [Desktop ttyN]. seen_running evita que la marca se caiga en el
    # primer tick del watchdog, cuando QEMU todavia no ha escrito su
    # qemu.pid (mismo patron que _demo_set en vm_lifecycle_mixin).

    def _desktop_mode_running_map(self):
        """dict {vm_dir: (tty, seen_running)}. Lazy-init."""
        m = getattr(self, "_desktop_mode_running", None)
        if m is None:
            m = {}
            self._desktop_mode_running = m
        return m

    def _desktop_mode_marker_for(self, vm_name):
        """Texto a anadir a la etiqueta de la VM en la lista lateral.

        Sin emoji (Kvantum segfaulta con emoji en QListWidgetItem).
        Devuelve '' si la VM no esta en Desktop Mode.
        """
        try:
            import vm_config as _vc
            vm_dir = os.path.join(_vc.BASE_VM_DIR, vm_name)
        except Exception:
            return ""
        entry = self._desktop_mode_running_map().get(vm_dir)
        if entry is None:
            return ""
        if isinstance(entry, tuple):
            tty = entry[0]
        else:
            tty = entry
        try:
            return f" [Desktop tty{int(tty)}]"
        except Exception:
            return ""

    def _desktop_mode_poll_qemu_pid(self, vm_dir, tty, attempts_left=32):
        """Sondea qemu.pid cada 250 ms antes de marcar [Desktop ttyN].

        Marcador: desktop_mode_qemu_pid_poll_v1

        Si tras `attempts_left` intentos (32 * 250ms = 8s) no aparece
        qemu.pid, no marca la VM y avisa en la consola de progreso.

        Por que sondea qemu.pid: el wrapper puede tardar en arrancar QEMU
        (openvt, setpriv, cage, Xwayland, luego QEMU). Marcar la VM en el
        momento del Popen produce falsos positivos cuando el wrapper
        falla a los 200ms. qemu.pid es la senal real de que QEMU arranco.
        """
        from PyQt6.QtCore import QTimer
        pid_path = os.path.join(vm_dir, "qemu.pid")
        if os.path.isfile(pid_path):
            self._desktop_mode_running_map()[vm_dir] = (int(tty), False)
            try:
                self.refresh_vm_list()
            except Exception:
                pass
            return
        if attempts_left <= 0:
            try:
                self.log_message(
                    "[AVISO] Desktop Mode: qemu.pid no aparecio en 8s. "
                    "La VM no se marco como [Desktop ttyN]. "
                    f"Revisa {os.path.join(vm_dir, 'desktop_mode_launch.log')} "
                    "para diagnosticar.")
            except Exception:
                pass
            return
        QTimer.singleShot(
            250,
            lambda: self._desktop_mode_poll_qemu_pid(
                vm_dir, tty, attempts_left - 1),
        )

    def _desktop_mode_cleanup_stopped(self):
        """Mantiene el mapa coherente con el estado real de cada VM.

        Reglas:
          - state running/paused -> seen_running=True.
          - state stopped        -> borrar SOLO si seen_running ya era
                                    True. Asi la marca no se cae en el
                                    primer tick, cuando QEMU todavia no
                                    ha escrito su qemu.pid.

        La llama refresh_vm_runtime_status en cada tick. Idempotente.
        """
        m = getattr(self, "_desktop_mode_running", None)
        if not m:
            return
        changed = False
        for vm_dir in list(m.keys()):
            name = os.path.basename(vm_dir)
            try:
                state = self._runtime_state(name)
            except Exception:
                m.pop(vm_dir, None)
                changed = True
                continue
            entry = m.get(vm_dir)
            if isinstance(entry, tuple) and len(entry) == 2:
                tty, seen = entry
            else:
                tty, seen = entry, True
            if state in ("running", "paused"):
                if not seen:
                    m[vm_dir] = (tty, True)
            elif seen and state == "stopped":
                m.pop(vm_dir, None)
                changed = True
        if changed:
            try:
                self.refresh_vm_list()
            except Exception:
                pass

# host_check_layout_v1_applied


# systemd_version_check_v1


# systemd_258_warn_v1

# systemd_258_warn_btn_v1

# systemd_258_btn_v1

# systemd_258_btn_logic_v1


# desktop_mode_portable_install_v1
