# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: configuración y lanzamiento de la consola remota (VNC / SPICE).

Agrupa toda la lógica de elección de protocolo y modo (embedded, external,
native, hybrid), el guardado de esa elección en vm_config.ini, el lanzamiento
del visor externo cuando aplica, y el texto de ayuda contextual que se muestra
en Configuración → Pantalla.

No conoce PyQt más allá de QMessageBox: los widgets (combos, labels) los crea
virtual_machine.py en _populate_config_pantalla. Los métodos de aquí asumen
que self ya tiene esos widgets cuando se llaman (self.combo_console_protocol,
self.combo_console_mode, self.label_console_requirements, self.label_console_help).
"""
import os

from PyQt6.QtWidgets import QMessageBox

from console_backend import (
    PROTOCOL_VNC, PROTOCOL_SPICE,
    MODE_EMBEDDED, MODE_EXTERNAL, MODE_NATIVE, MODE_HYBRID,
    DEFAULT_PROTOCOL, DEFAULT_MODE,
    describe_requirements,
    find_viewer, console_uri, build_viewer_args,
    socket_path as _cb_socket_path,
)


class ConsoleUiMixin:
    # ==================================================================
    # Consola gráfica: VNC / SPICE, embebida / externa / nativa
    # ==================================================================
    def _current_console_choice(self):
        """Devuelve (protocol, mode) según los combos (con defaults)."""
        proto = DEFAULT_PROTOCOL
        mode = DEFAULT_MODE
        if hasattr(self, "combo_console_protocol"):
            proto = self.combo_console_protocol.currentData() or DEFAULT_PROTOCOL
        if hasattr(self, "combo_console_mode"):
            mode = self.combo_console_mode.currentData() or DEFAULT_MODE
        return proto, mode

    def _apply_console_choice_to_ui(self, protocol, mode):
        """Coloca los combos en la selección indicada sin disparar señales."""
        if hasattr(self, "combo_console_protocol"):
            idx = self.combo_console_protocol.findData(protocol)
            if idx >= 0:
                self.combo_console_protocol.blockSignals(True)
                self.combo_console_protocol.setCurrentIndex(idx)
                self.combo_console_protocol.blockSignals(False)
        if hasattr(self, "combo_console_mode"):
            idx = self.combo_console_mode.findData(mode)
            if idx >= 0:
                self.combo_console_mode.blockSignals(True)
                self.combo_console_mode.setCurrentIndex(idx)
                self.combo_console_mode.blockSignals(False)
        if hasattr(self, "check_vnc_embedded"):
            self.check_vnc_embedded.blockSignals(True)
            self.check_vnc_embedded.setChecked(
                mode == MODE_EMBEDDED and protocol == PROTOCOL_VNC
            )
            self.check_vnc_embedded.blockSignals(False)

        # Reevaluar el combo Gráficos con la elección recién aplicada.
        # Sin esto, abrir una VM con VNC embebido dejaba VirGL/Venus/Auto
        # deshabilitadas "pegadas", y abrir otra VM con SPICE externo NO
        # las rehabilitaba (el checkbox legacy se mueve con blockSignals,
        # así que nadie dispara la reevaluación).
        if hasattr(self, "_on_vnc_embedded_changed"):
            try:
                self._on_vnc_embedded_changed()
            except Exception:
                pass

    def _refresh_console_help(self):
        """Actualiza el texto de ayuda con pros y contras de cada modo.

        Se llama al construir la sección Pantalla y cada vez que cambia la
        elección de protocolo/modo. Refleja el estado real del host (X11 vs
        Wayland, spice-gtk Python) para no prometer cosas que no puede
        cumplir.
        """
        if not hasattr(self, "label_console_help"):
            return

        import os as _os
        session = (_os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
        if not session:
            session = "wayland" if _os.environ.get("WAYLAND_DISPLAY") else "x11"
        is_x11 = (session == "x11")

        try:
            from console_backend import embedded_spice_available as _esa
            spice_gtk_ok = bool(_esa())
        except Exception:
            spice_gtk_ok = False

        # --- Estado de la sesión, con lo que se puede y no se puede hacer ---
        if is_x11:
            session_line = (
                "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden "
                "embeber dentro de la app."
            )
        else:
            session_line = (
                "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber "
                "dentro de la app. SPICE embebido requeriría X11 (XEmbed no "
                "existe en Wayland); si eliges SPICE con modo embebido, "
                "caerá automáticamente a visor externo."
            )

        if spice_gtk_ok:
            spice_line = (
                "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE "
                "funcionará cuando estés en X11."
            )
        else:
            spice_line = (
                "<b>spice-gtk con binding Python: no.</b> Aunque estés en "
                "X11, SPICE no podrá incrustarse; siempre caerá a visor "
                "externo. Instálalo con:<br>"
                "&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>"
                "&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>"
            )

        # --- Pros y contras por protocolo/modo ---
        vnc_block = (
            "<b>VNC</b><br>"
            "<span style='color:#2e7d32;'>✓</span> Compatible con cualquier "
            "gráfico virtual (VirtIO-GPU 2D, QXL, std).<br>"
            "<span style='color:#2e7d32;'>✓</span> Se puede embeber dentro "
            "de la app, incluso en Wayland.<br>"
            "<span style='color:#2e7d32;'>✓</span> Muchos visores externos "
            "disponibles (gvncviewer, vncviewer, remmina).<br>"
            "<span style='color:#2e7d32;'>✓</span> Sin dependencias "
            "adicionales en el guest para funcionar.<br>"
            "<span style='color:#c62828;'>✗</span> Sin aceleración 3D ni "
            "streaming de video (redibuja por regiones).<br>"
            "<span style='color:#c62828;'>✗</span> Clipboard limitado: solo "
            "texto, y el guest necesita <code>vncconfig</code> corriendo.<br>"
            "<span style='color:#c62828;'>✗</span> Sin audio remoto.<br>"
            "<span style='color:#c62828;'>✗</span> Menos fluido en uso "
            "intensivo (vídeo, animaciones, 3D)."
        )

        spice_block = (
            "<b>SPICE</b><br>"
            "<span style='color:#2e7d32;'>✓</span> Mejor rendimiento y "
            "fluidez en local (compresión + streaming de video).<br>"
            "<span style='color:#2e7d32;'>✓</span> Clipboard bidireccional "
            "avanzado (con <code>spice-vdagent</code> en el guest).<br>"
            "<span style='color:#2e7d32;'>✓</span> Audio remoto integrado.<br>"
            "<span style='color:#2e7d32;'>✓</span> Varios monitores, "
            "redirección USB y carpetas compartidas nativas.<br>"
            "<span style='color:#c62828;'>✗</span> No se puede embeber en "
            "Wayland (solo X11 con spice-gtk Python).<br>"
            "<span style='color:#c62828;'>✗</span> Requiere un visor externo "
            "(spicy o remote-viewer) si no se puede embeber.<br>"
            "<span style='color:#c62828;'>✗</span> Para aprovecharlo hay que "
            "instalar <code>spice-vdagent</code> en el guest.<br>"
            "<span style='color:#c62828;'>✗</span> Incompatible con VirGL y "
            "Venus (usan OpenGL y obligan a la ventana nativa de QEMU)."
        )

        hybrid_block = (
            "<b>Híbrida (VNC embebido + SPICE externo)</b><br>"
            "<span style='color:#2e7d32;'>✓</span> Lo mejor de ambos: VNC "
            "siempre visible dentro de la app, SPICE para rendimiento y "
            "clipboard.<br>"
            "<span style='color:#2e7d32;'>✓</span> Funciona en cualquier "
            "sesión: Wayland o X11.<br>"
            "<span style='color:#2e7d32;'>✓</span> Si spicy falla o lo "
            "cierras, el widget VNC sigue funcionando.<br>"
            "<span style='color:#2e7d32;'>✓</span> Útil para ver la VM en "
            "dos monitores o para grabar y controlar a la vez.<br>"
            "<span style='color:#c62828;'>✗</span> Consume más recursos: "
            "QEMU mantiene dos servidores de display en paralelo.<br>"
            "<span style='color:#c62828;'>✗</span> Verás la misma VM en dos "
            "ventanas (dentro de la app y en la de spicy).<br>"
            "<span style='color:#c62828;'>✗</span> La configuración del "
            "guest para sacar partido a SPICE (vdagent, drivers) hay que "
            "hacerla igual.<br>"
            "<span style='color:#c62828;'>✗</span> Como SPICE, incompatible "
            "con VirGL y Venus."
        )

        # --- Nota sobre gráficos (común a todos los modos por socket) ---
        graphics_block = (
            "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> "
            "<b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>"
            "Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su "
            "propia ventana y no expone VNC/SPICE; es el único modo "
            "compatible con esos gráficos 3D."
        )

        html = (
            f"{session_line}<br>{spice_line}"
            "<hr>"
            f"{vnc_block}<br><br>"
            f"{spice_block}<br><br>"
            f"{hybrid_block}<br><br>"
            # Nota: MODE_HYBRID_GL (Hibrida 3D: VNC embebido + ventana
            # GL de QEMU) existe en console_backend pero NO esta
            # expuesto en el combo "Modo" de Configuracion -> Pantalla.
            # Cuando se exponga, anadir aqui su bloque descriptivo.
            "<hr>"
            f"{graphics_block}"
        )
        self.label_console_help.setText(html)


    def _on_console_config_changed(self, *args):
        """Guarda la elección y actualiza la pista de requisitos."""
        protocol, mode = self._current_console_choice()
        if self.current_vm_dir:
            try:
                self._save_console_choice(protocol, mode)
            except Exception as e:
                try:
                    self.log_message(f"[AVISO] No se pudo guardar la elección de consola: {e}")
                except Exception:
                    pass
        try:
            hint = describe_requirements(protocol, mode)
            if hasattr(self, "label_console_requirements"):
                self.label_console_requirements.setText(hint)
        except Exception:
            pass
        try:
            self._refresh_console_help()
        except Exception:
            pass
        # Refrescar el estado dependiente del checkbox antiguo (sin recursión:
        # _on_vnc_embedded_changed NO llama de vuelta a este método).
        try:
            self._on_vnc_embedded_changed()
        except Exception:
            pass

    def _save_console_choice(self, protocol, mode):
        if not self.current_vm_dir:
            return
        import json as _json, configparser as _cfg
        cfg_path = os.path.join(self.current_vm_dir, "vm_config.ini")
        if not os.path.isfile(cfg_path):
            return
        c = _cfg.ConfigParser(interpolation=None)
        c.read(cfg_path, encoding="utf-8")
        if not c.has_section("extra"):
            c.add_section("extra")
        try:
            extra = _json.loads(c["extra"].get("data", "{}"))
        except Exception:
            extra = {}
        extra["console_protocol"] = protocol
        extra["console_mode"] = mode
        extra["vnc_embedded"] = (mode == MODE_EMBEDDED and protocol == PROTOCOL_VNC)
        c.set("extra", "data", _json.dumps(extra, ensure_ascii=False))
        with open(cfg_path, "w", encoding="utf-8") as f:
            c.write(f)

    def _launch_external_console(self):
        """Lanza el visor externo del protocolo actual (aunque el modo sea embedded)."""
        if not self._vm_is_selected():
            QMessageBox.information(self, "Consola externa",
                                    "Selecciona primero una máquina virtual.")
            return
        protocol, _mode = self._current_console_choice()
        viewer, template = find_viewer(protocol)
        if not viewer:
            QMessageBox.warning(
                self, "Consola externa",
                f"No se encontró ningún visor {protocol.upper()} instalado.\n\n"
                + ("Instala gvncviewer o tigervnc (vncviewer)."
                   if protocol == PROTOCOL_VNC
                   else "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).")
            )
            return

        # Determinar el destino: socket VNC o URI/puerto SPICE.
        sock = ""
        spice_port = None
        if protocol == PROTOCOL_SPICE:
            if hasattr(self, "_spice_port_from_runtime"):
                spice_port = self._spice_port_from_runtime()
            if spice_port is None:
                QMessageBox.information(
                    self, "Consola externa",
                    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\n"
                    "La VM debe estar corriendo para que QEMU haya elegido un\n"
                    "puerto."
                )
                return
            sock = f"spice://127.0.0.1:{spice_port}"
        else:
            sock = _cb_socket_path(self.current_vm_dir, protocol)
            if not os.path.exists(sock):
                QMessageBox.information(
                    self, "Consola externa",
                    f"El socket {protocol.upper()} todavía no existe.\n\n"
                    "La VM debe estar corriendo con ese protocolo seleccionado."
                )
                return

        uri = console_uri(protocol, sock)
        try:
            from console_backend import build_viewer_args as _bva
            args = [viewer] + _bva(template, sock, uri, port=spice_port)
        except Exception:
            args = [viewer] + [str(a).replace("{sock}", sock).replace("{uri}", uri)
                               for a in template]
        try:
            import subprocess as _sp
            _sp.Popen(args, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                      start_new_session=True)
            self.log_message(f"==> Visor externo lanzado: {' '.join(args)}")
        except Exception as e:
            QMessageBox.warning(self, "Consola externa",
                                f"No se pudo lanzar el visor:\n\n{e}")
