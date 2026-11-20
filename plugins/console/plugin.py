import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QTimer
from core.plugin_base import PluginBase

log = logging.getLogger(__name__)

try:
    from vnc_widget import QVNCWidget
    from vnc_widget_centered import CenteredVNCWidget
    HAS_VNC = True
except ImportError as e:
    HAS_VNC = False
    print(f"[VNC ERROR] No se pudo importar el visor: {e}")


class ConsoleWidget(QWidget):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def showEvent(self, event):
        super().showEvent(event)
        self.plugin._try_connect_vnc()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.plugin._update_zoom_label()


class Plugin(PluginBase):
    name = "Console"
    version = "1.4.0"

    def __init__(self, app):
        super().__init__(app)
        self.vnc_widget = None
        self.current_vm_id = None
        self.current_zoom = None
        self.is_connected = False
        self._fs_window = None

    def get_tabs(self):
        main_widget = ConsoleWidget(self)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        if not HAS_VNC:
            lbl = QLabel("El módulo VNC no está instalado o falló al cargar.")
            layout.addWidget(lbl)
            return [("Consola Gráfica", main_widget)]

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)

        self.btn_fit = QPushButton("⊞ Ajustar")
        self.btn_fit.setToolTip("Ajustar la imagen de la consola al tamaño del panel")
        self.btn_fit.clicked.connect(self._zoom_fit)
        toolbar.addWidget(self.btn_fit)

        self.btn_zoom_out = QPushButton("🔍−")
        self.btn_zoom_out.setToolTip("Reducir el zoom de la consola")
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        toolbar.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLabel("Ajustado")
        self.lbl_zoom.setStyleSheet("font-weight: bold; min-width: 60px;")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setToolTip("Nivel de zoom actual de la consola gráfica")
        toolbar.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setToolTip("Aumentar el zoom de la consola")
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        toolbar.addWidget(self.btn_zoom_in)

        self.btn_real = QPushButton("1:1")
        self.btn_real.setToolTip("Mostrar la consola al tamaño real (100 % de zoom)")
        self.btn_real.clicked.connect(self._zoom_real)
        toolbar.addWidget(self.btn_real)

        toolbar.addStretch()

        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setToolTip("Pantalla completa de la consola gráfica (F11)")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        toolbar.addWidget(self.btn_fullscreen)

        layout.addLayout(toolbar)

        host = getattr(self.app, "host", None)
        if getattr(host, "acceleration", "") == "tcg":
            banner = QLabel("⚠️ Sin KVM: esta VM corre con TCG (emulación, ~2–5 % de velocidad). Instala KVM (/dev/kvm) para acelerarla.")
            banner.setWordWrap(True)
            banner.setStyleSheet("background-color: #92400e; color: #fef3c7; padding: 6px 10px; font-weight: bold;")
            layout.addWidget(banner)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: black;")
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.placeholder = QLabel("Selecciona una VM y enciéndela para ver la pantalla.")
        self.placeholder.setStyleSheet("color: white; font-size: 16px;")
        self.placeholder.setToolTip("Pantalla de la máquina virtual invitada. Aparece cuando la VM está encendida.")
        self.scroll_area.setWidget(self.placeholder)

        layout.addWidget(self.scroll_area, 1)

        self.app.vm_selection_changed.connect(self._on_vm_selected)
        self.app.vm_state_changed.connect(self._on_vm_state_changed)

        return [("Consola Gráfica", main_widget)]

    def _on_vm_selected(self, vm_id: str):
        if self.current_vm_id != vm_id:
            self.current_vm_id = vm_id
            self._disconnect_vnc()
            vm = self.app.get_vm(vm_id)
            if vm:
                self._safe_set_text(f"VM: {vm.get('name')}\nEsperando que la VM se encienda...")

    def _on_vm_state_changed(self, vm_id: str, state: str):
        if vm_id != self.current_vm_id:
            return

        if state == "Running":
            self._try_connect_vnc()
        else:
            self._disconnect_vnc()
            vm = self.app.get_vm(vm_id)
            if vm:
                self._safe_set_text(f"VM: {vm.get('name')}\nEstado: {state}")

    def _try_connect_vnc(self):
        if not self.current_vm_id or self.is_connected:
            return

        vm = self.app.get_vm(self.current_vm_id)
        if not vm:
            return

        if vm.get("state") != "Running":
            self._safe_set_text(f"VM: {vm.get('name')}\nLa VM no está encendida.")
            return

        proto_idx = vm.get("console_proto_idx", 0)
        mode_idx = vm.get("console_mode_idx", 0)

        # Embebemos VNC cuando:
        #   * proto=VNC + mode ∈ {Embebida(0), Pantalla completa(3)}
        #   * mode=Híbrida(2) → VNC en widget + SPICE externo
        embed_vnc = (
            (proto_idx == 0 and mode_idx in (0, 3))
            or mode_idx == 2
        )

        if not embed_vnc:
            if proto_idx == 1 and mode_idx == 1:
                self._safe_set_text(f"VM: {vm.get('name')}\nSPICE en ventana externa (remote-viewer).")
            elif proto_idx == 0 and mode_idx == 1:
                self._safe_set_text(f"VM: {vm.get('name')}\nVNC en ventana externa (xtigervncviewer).")
            else:
                self._safe_set_text(f"VM: {vm.get('name')}\nEsta VM no usa visor embebido.")
            return

        vnc_port = vm.get("vnc_port")
        if not vnc_port:
            self._safe_set_text("Esperando puerto VNC...")
            return

        self._disconnect_vnc()

        try:
            self.vnc_widget = CenteredVNCWidget(
                parent=self.scroll_area,
                host="127.0.0.1",
                port=vnc_port
            )
            self._apply_zoom()
            self.scroll_area.setWidget(self.vnc_widget)
            self.vnc_widget.start()
            self.vnc_widget.setFocus()
            self.is_connected = True

            # Conectar señales de fullscreen
            if hasattr(self.vnc_widget, "fullscreen_toggle_requested"):
                self.vnc_widget.fullscreen_toggle_requested.connect(self._toggle_fullscreen)
            if hasattr(self.vnc_widget, "fullscreen_exit_requested"):
                self.vnc_widget.fullscreen_exit_requested.connect(self._on_fullscreen_exit_requested)
            if hasattr(self.vnc_widget, "fullscreen_changed"):
                self.vnc_widget.fullscreen_changed.connect(self._on_fullscreen_changed)

            # Autofullscreen si modo = "Pantalla completa"
            if mode_idx == 3:
                QTimer.singleShot(800, self._toggle_fullscreen)
        except Exception as e:
            self._safe_set_text(f"Error al conectar VNC: {e}")
            log.exception("Error conectando VNC")

    def _disconnect_vnc(self):
        if self.vnc_widget:
            try:
                self.vnc_widget.stop()
                self.vnc_widget.deleteLater()
            except Exception:
                pass
            self.vnc_widget = None
            self.is_connected = False
            try:
                self.placeholder = QLabel("Selecciona una VM y enciéndela para ver la pantalla.")
                self.placeholder.setStyleSheet("color: white; font-size: 16px;")
                self.scroll_area.setWidget(self.placeholder)
            except RuntimeError:
                pass

    def _safe_set_text(self, text):
        if hasattr(self, 'placeholder') and self.placeholder is not None:
            try:
                self.placeholder.setText(text)
            except RuntimeError:
                pass

    def _toggle_fullscreen(self):
        if not self.is_connected or not self.vnc_widget:
            return
        if self._fs_window is not None:
            self._exit_fullscreen_impl()
        else:
            self._enter_fullscreen_impl()

    def _on_fullscreen_exit_requested(self):
        if self._fs_window is not None:
            self._exit_fullscreen_impl()

    def _enter_fullscreen_impl(self):
        from PyQt6.QtWidgets import QWidget as QW, QVBoxLayout as QVL
        from PyQt6.QtCore import Qt as QtCore

        try:
            self.scroll_area.takeWidget()

            self._fs_window = QW(None, QtCore.WindowType.Window)
            self._fs_window.setStyleSheet("background-color: black;")
            self._fs_window.setWindowTitle("VNC - Pantalla completa")

            fs_layout = QVL(self._fs_window)
            fs_layout.setContentsMargins(0, 0, 0, 0)

            self.vnc_widget.setParent(self._fs_window)
            fs_layout.addWidget(self.vnc_widget)

            self._fs_window.showFullScreen()

            self._fs_prev_zoom = self.current_zoom
            self.current_zoom = None
            self._apply_zoom()

            self.vnc_widget.setFocus()
            self._on_fullscreen_changed(True)
        except Exception as e:
            log.exception("Error entrando a pantalla completa")
            self._fs_window = None

    def _exit_fullscreen_impl(self):
        if self._fs_window is None:
            return

        try:
            self.vnc_widget.setParent(None)
            self._fs_window.close()
            self._fs_window.deleteLater()
            self._fs_window = None

            self.scroll_area.setWidget(self.vnc_widget)

            self.current_zoom = self._fs_prev_zoom
            self._fs_prev_zoom = None
            self._apply_zoom()

            self.vnc_widget.setFocus()
            self._on_fullscreen_changed(False)
        except Exception as e:
            log.exception("Error saliendo de pantalla completa")

    def _on_fullscreen_changed(self, is_fs: bool):
        try:
            if is_fs:
                self.btn_fullscreen.setText("⛶ Salir")
                self.btn_fullscreen.setToolTip("Salir de pantalla completa (F11 o Ctrl+Alt+F)")
            else:
                self.btn_fullscreen.setText("⛶")
                self.btn_fullscreen.setToolTip("Pantalla completa (F11)")
        except RuntimeError:
            pass

    # --- Zoom ---
    def _get_current_percentage(self):
        if self.current_zoom is not None:
            return self.current_zoom
        if self.vnc_widget and getattr(self.vnc_widget, 'vncWidth', 0) > 0:
            w_widget = self.vnc_widget.width()
            w_vnc = self.vnc_widget.vncWidth
            if w_vnc > 0:
                return int((w_widget / w_vnc) * 100)
        return 100

    def _update_zoom_label(self):
        # La barra de zoom solo existe si el visor VNC se pudo importar
        # (HAS_VNC). Sin ella, no hay etiqueta que actualizar.
        lbl = getattr(self, "lbl_zoom", None)
        if lbl is None:
            return
        if self.current_zoom is None:
            pct = self._get_current_percentage()
            lbl.setText(f"Ajustado ({pct}%)")
        else:
            lbl.setText(f"{self.current_zoom}%")

    def _apply_zoom(self):
        if not self.vnc_widget:
            return
        self.vnc_widget.set_zoom(self.current_zoom)
        self._update_zoom_label()

    def _zoom_in(self):
        actual = self._get_current_percentage()
        siguiente = (actual // 10 + 1) * 10
        self.current_zoom = min(400, siguiente)
        self._apply_zoom()

    def _zoom_out(self):
        actual = self._get_current_percentage()
        anterior = max(10, (actual // 10) * 10)
        if anterior == actual:
            anterior = max(10, anterior - 10)
        self.current_zoom = anterior
        self._apply_zoom()

    def _zoom_fit(self):
        self.current_zoom = None
        self._apply_zoom()

    def _zoom_real(self):
        self.current_zoom = 100
        self._apply_zoom()