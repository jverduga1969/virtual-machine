# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: panel de semáforos de salud de la VM.

Muestra un diálogo con un semáforo por subsistema (red de la VM, internet
del host, audio, pantalla, Guest Agent) que se refresca en vivo cada
4 segundos mientras está abierto. Los datos salen de fuentes que no
dependen del guest: script de arranque (run_temp.sh), QMP, pactl, widget
VNC/SPICE y la propia tabla de visores externos.

Marcador: health_dashboard_v1
"""
import os
import re
import socket
import subprocess
import shutil
import time  # health_dashboard_import_time_v1
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget,
)
from PyQt6.QtGui import QFont


_GREEN = "#2e7d32"
_YELLOW = "#f9a825"
_RED = "#c62828"
_GREY = "#757575"


class HealthDashboardMixin:
    # ------------------------------------------------------------------
    # Entrada pública
    # ------------------------------------------------------------------

    def show_health_dashboard(self):
        """Abre el panel de semáforos. Si ya estaba abierto, lo sube al
        frente y lo refresca."""
        dlg = getattr(self, "_health_dashboard_dialog", None)
        if dlg is not None:
            try:
                dlg.raise_()
                dlg.activateWindow()
                self._refresh_health_dashboard()
                return
            except Exception:
                pass
        self._open_health_dashboard()

    def _open_health_dashboard(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Salud de la máquina virtual"))
        dlg.resize(640, 440)
        self._health_dashboard_dialog = dlg

        root = QVBoxLayout(dlg)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel(self.tr("<b style='font-size:15px;'>🚦 Semáforos de salud</b>"))
        root.addWidget(title)

        subtitle = QLabel(
            self.tr(
                "Cada fila muestra el estado de un subsistema de la VM. "
                "Verde: funciona · Amarillo: parcial o sin confirmar · "
                "Rojo: no disponible · Gris: no aplica. Se refresca cada 4 s."
            )
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#666; font-size:11px;")
        root.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        self._health_rows = {}
        rows = (
            ("network", self.tr("🌐 Red de la VM")),
            ("host",    self.tr("🖥️ Internet del host")),
            ("audio",   self.tr("🔊 Audio")),
            ("display", self.tr("🖼️ Pantalla")),
            ("qga",     self.tr("🔌 Guest Agent")),
        )
        for key, label in rows:
            row = QWidget()
            lay = QHBoxLayout(row)
            lay.setContentsMargins(4, 6, 4, 6)
            lay.setSpacing(10)

            dot = QLabel("●")
            dot.setFixedWidth(20)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            f = QFont()
            f.setPointSize(14)
            dot.setFont(f)
            dot.setStyleSheet(f"color: {_GREY};")

            name = QLabel(f"<b>{label}</b>")
            name.setMinimumWidth(180)

            detail = QLabel(self.tr("Comprobando…"))
            detail.setWordWrap(True)
            detail.setStyleSheet("color:#555; font-size:11px;")

            lay.addWidget(dot)
            lay.addWidget(name)
            lay.addWidget(detail, 1)

            self._health_rows[key] = (dot, detail)
            root.addWidget(row)

        root.addStretch(1)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton(self.tr("🔄 Refrescar ahora"))
        refresh_btn.clicked.connect(self._refresh_health_dashboard)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch(1)

        close_btn = QPushButton(self.tr("Cerrar"))
        close_btn.clicked.connect(self._close_health_dashboard)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self._health_timer = QTimer(dlg)
        self._health_timer.setInterval(4000)
        self._health_timer.timeout.connect(self._refresh_health_dashboard)
        self._health_timer.start()

        self._refresh_health_dashboard()

        dlg.finished.connect(lambda _: self._close_health_dashboard())

        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _close_health_dashboard(self):
        timer = getattr(self, "_health_timer", None)
        if timer is not None:
            try:
                timer.stop()
            except Exception:
                pass
            self._health_timer = None
        dlg = getattr(self, "_health_dashboard_dialog", None)
        if dlg is not None:
            try:
                dlg.close()
                dlg.deleteLater()
            except Exception:
                pass
            self._health_dashboard_dialog = None

    def _set_health(self, key, color, text):
        row = (getattr(self, "_health_rows", {}) or {}).get(key)
        if row is None:
            return
        dot, detail = row
        dot.setStyleSheet(f"color: {color};")
        detail.setText(text)

    # ------------------------------------------------------------------
    # Refresco global
    # ------------------------------------------------------------------

    def _refresh_health_dashboard(self):
        if not getattr(self, "_health_rows", None):
            return
        if not self.current_vm_dir:
            for key, (dot, detail) in self._health_rows.items():
                dot.setStyleSheet(f"color: {_GREY};")
                detail.setText(self.tr("Sin VM seleccionada."))
            return

        vm_dir = self.current_vm_dir
        vm_name = os.path.basename(vm_dir)

        # Internet del host: independiente del estado de la VM.
        try:
            color, text = self._probe_host_internet()
            self._set_health("host", color, text)
        except Exception as e:
            self._set_health("host", _GREY, f"No se pudo comprobar: {e}")

        try:
            state = self._runtime_state(vm_name)
        except Exception:
            state = "stopped"

        if state not in ("running", "paused"):
            for key in ("network", "audio", "display", "qga"):
                self._set_health(key, _GREY, self.tr("La VM no está corriendo."))
            return

        for key, probe in (
            ("network", self._probe_network_health),
            ("audio",   self._probe_audio_health),
            ("display", self._probe_display_health),
            ("qga",     self._probe_qga_health),
        ):
            try:
                color, text = probe(vm_dir)
                self._set_health(key, color, text)
            except Exception as e:
                self._set_health(key, _GREY, f"No se pudo comprobar: {e}")

    # ------------------------------------------------------------------
    # Sondas
    # ------------------------------------------------------------------

    def _probe_host_internet(self):
        """TCP connect a dos destinos conocidos. No requiere root."""
        results = []
        for host, port in (("apple.com", 443), ("1.1.1.1", 443)):
            try:
                s = socket.create_connection((host, port), timeout=2.0)
                s.close()
                results.append(True)
            except Exception:
                results.append(False)
        if all(results):
            return _GREEN, self.tr("Host con salida a Internet (Apple y Cloudflare responden).")
        if any(results):
            return _YELLOW, self.tr("Salida parcial: uno de los dos destinos no respondió.")
        return _RED, self.tr("El host no tiene salida a Internet.")

    def _probe_network_health(self, vm_dir):
        """health_network_qmp_v2

        Estrategia sin sudo:
          1) query-netdev por QMP  -> contadores internos del netdev.
             Calcula KB/s comparando con la lectura anterior.
          2) ss -tn (sin -p)       -> cuenta conexiones ESTAB no locales
             y detecta cambio respecto a la lectura anterior.
          3) Amarillo honesto si nada de lo anterior da señal.
        """
        run_sh = os.path.join(vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return _GREY, self.tr("No hay script de arranque todavía.")
        try:
            with open(run_sh, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return _GREY, self.tr("No se pudo leer el script de arranque.")

        if "-netdev" not in content:
            return _RED, self.tr("No hay adaptador de red configurado en esta VM.")

        is_user = bool(re.search(r"-netdev\s+user", content))
        kind = "user (slirp)" if is_user else "directa"

        prev = getattr(self, "_health_net_prev", None)
        if prev is None:
            prev = {}
            self._health_net_prev = prev
        now = time.monotonic()

        # ---- 1) query-netdev por QMP ----
        try:
            r = self._qmp_command(vm_dir, {"execute": "query-netdev"})
            rows = r.get("return") or []
            if rows:
                rx_total = 0
                tx_total = 0
                for row in rows:
                    stats = row.get("stats") or {}
                    rx_total += int(stats.get("rx-bytes", 0) or 0)
                    tx_total += int(stats.get("tx-bytes", 0) or 0)
                if rx_total or tx_total:
                    prev_entry = prev.get(vm_dir)
                    if prev_entry and (now - prev_entry.get("ts", 0)) > 0.5:
                        dt = now - prev_entry["ts"]
                        d_rx = max(0, rx_total - prev_entry.get("rx", 0))
                        d_tx = max(0, tx_total - prev_entry.get("tx", 0))
                        kbps = (d_rx + d_tx) / 1024.0 / max(dt, 1.0)
                        prev[vm_dir] = {"ts": now, "rx": rx_total, "tx": tx_total}
                        if kbps > 1.0:
                            return _GREEN, (
                                self.tr(
                                    "NIC {0}: tráfico activo "
                                    "({1:.1f} KB/s; "
                                    "rx {2:.1f} MB, "
                                    "tx {3:.1f} MB)."
                                ).format(
                                    kind, kbps,
                                    rx_total / 1024 / 1024,
                                    tx_total / 1024 / 1024,
                                )
                            )
                        return _YELLOW, (
                            self.tr(
                                "NIC {0} con contadores activos pero "
                                "sin tráfico en el último intervalo "
                                "(rx {1:.1f} MB, "
                                "tx {2:.1f} MB)."
                            ).format(
                                kind,
                                rx_total / 1024 / 1024,
                                tx_total / 1024 / 1024,
                            )
                        )
                    prev[vm_dir] = {"ts": now, "rx": rx_total, "tx": tx_total}
                    return _YELLOW, (
                        self.tr(
                            "NIC {0}: contadores iniciales leídos "
                            "(rx {1:.1f} MB, "
                            "tx {2:.1f} MB); "
                            "esperando siguiente lectura para medir velocidad."
                        ).format(
                            kind,
                            rx_total / 1024 / 1024,
                            tx_total / 1024 / 1024,
                        )
                    )
                # Sin contadores: caer al fallback.
        except Exception:
            pass

        # ---- 2) ss -tn SIN -p (no requiere privilegios) ----
        ss = shutil.which("ss")
        if ss:
            try:
                r = subprocess.run(
                    [ss, "-tn"], capture_output=True, text=True, timeout=3,
                )
                if r.returncode == 0:
                    count = 0
                    for line in (r.stdout or "").splitlines():
                        if "ESTAB" not in line:
                            continue
                        # Excluir loopback y ::1.
                        if "127.0.0.1" in line or "[::1]" in line:
                            continue
                        count += 1

                    prev_entry = prev.get(vm_dir)
                    prev_count = prev_entry.get("ss_count") if prev_entry else None
                    prev_ss_ts = prev_entry.get("ss_ts", 0) if prev_entry else 0

                    new_entry = dict(prev_entry or {})
                    new_entry["ss_count"] = count
                    new_entry["ss_ts"] = now
                    prev[vm_dir] = new_entry

                    if prev_count is None:
                        return _YELLOW, (
                            self.tr(
                                "NIC {0} configurada. {1} conexiones TCP "
                                "activas en el host; esperando segunda lectura "
                                "para medir cambio."
                            ).format(kind, count)
                        )
                    if count != prev_count:
                        return _GREEN, (
                            self.tr(
                                "NIC {0}: actividad detectada "
                                "({1} → {2} conexiones TCP ESTAB)."
                            ).format(kind, prev_count, count)
                        )
                    if count > 0:
                        return _YELLOW, (
                            self.tr(
                                "NIC {0} configurada. {1} conexiones TCP "
                                "activas en el host, sin cambios en el último "
                                "intervalo (la VM puede estar idle)."
                            ).format(kind, count)
                        )
                    return _YELLOW, (
                        self.tr(
                            "NIC {0} configurada; sin conexiones externas "
                            "activas en el host."
                        ).format(kind)
                    )
            except Exception:
                pass

        return _YELLOW, (
            self.tr(
                "NIC {0} configurada. No se pudo medir tráfico (QMP no "
                "expone query-netdev y ss no está disponible)."
            ).format(kind)
        )
    def _probe_audio_health(self, vm_dir):
        run_sh = os.path.join(vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return _GREY, self.tr("No hay script de arranque todavía.")
        try:
            with open(run_sh, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return _GREY, self.tr("No se pudo leer el script de arranque.")

        if "-audiodev" not in content and "-device intel-hda" not in content:
            return _GREY, self.tr("Sin audio configurado en esta VM.")

        pactl = shutil.which("pactl")
        if not pactl:
            return _YELLOW, self.tr("Audiodev configurado. pactl no disponible; no se puede confirmar reproducción.")

        pid_path = os.path.join(vm_dir, "qemu.pid")
        qemu_pid = None
        if os.path.isfile(pid_path):
            try:
                with open(pid_path, encoding="utf-8") as f:
                    qemu_pid = int(f.read().strip())
            except Exception:
                pass
        if not qemu_pid:
            return _YELLOW, self.tr("Audiodev configurado, pero no hay PID de QEMU para verificar el sink.")

        try:
            r = subprocess.run([pactl, "list", "sink-inputs"],
                               capture_output=True, text=True, timeout=3)
        except Exception as e:
            return _YELLOW, self.tr("No se pudo consultar pactl: {0}").format(e)
        if r.returncode != 0:
            return _YELLOW, self.tr("pactl no respondió.")

        text = r.stdout or ""
        needle = f'application.process.id = "{qemu_pid}"'
        if needle in text or f"application.process.id = {qemu_pid}" in text:
            return _GREEN, self.tr(
                "Sink activo: pactl ve al QEMU (PID {0}) reproduciendo."
            ).format(qemu_pid)
        return _YELLOW, (
            self.tr(
                "Audiodev configurado; QEMU no está reproduciendo ahora. "
                "Es normal si el guest no está emitiendo sonido."
            )
        )

    def _probe_display_health(self, vm_dir):
        # Widget embebido: usar resolución si está disponible.
        w = getattr(self, "vnc_widget", None)
        if w is not None:
            try:
                vw = int(getattr(w, "vncWidth", 0) or 0)
                vh = int(getattr(w, "vncHeight", 0) or 0)
                if vw > 0 and vh > 0:
                    return _GREEN, self.tr(
                        "Framebuffer VNC {0}×{1}."
                    ).format(vw, vh)
                return _YELLOW, self.tr("Widget VNC conectado, esperando primer frame.")
            except Exception:
                pass

        sw = getattr(self, "spice_widget", None)
        if sw is not None:
            return _GREEN, self.tr("Consola SPICE embebida activa.")

        viewers = getattr(self, "_external_viewers", {}) or {}
        entry = viewers.get(vm_dir)
        if entry is not None:
            p = entry.get("proc")
            try:
                if p is not None and p.poll() is None:
                    return _GREEN, self.tr(
                        "Visor externo activo (PID {0})."
                    ).format(p.pid)
            except Exception:
                pass

        run_sh = os.path.join(vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return _GREY, self.tr("No hay script de arranque todavía.")
        try:
            with open(run_sh, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return _GREY, self.tr("No se pudo leer el script de arranque.")

        if "-display none" in content:
            if "-vnc " in content or "-spice " in content:
                return _YELLOW, (
                    self.tr(
                        "Modo remoto (socket VNC/SPICE) sin widget embebido ni "
                        "visor activo. Abre la Consola Gráfica para ver la pantalla."
                    )
                )
            return _YELLOW, self.tr("Modo headless (sin salida de pantalla).")
        if "-display gtk" in content or "-display sdl" in content:
            return _GREEN, self.tr("Ventana nativa de QEMU activa.")
        return _YELLOW, self.tr("Configuración de pantalla detectada en el script de arranque.")

    def _probe_qga_health(self, vm_dir):
        run_sh = os.path.join(vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return _GREY, self.tr("No hay script de arranque todavía.")
        try:
            with open(run_sh, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return _GREY, self.tr("No se pudo leer el script de arranque.")

        if "org.qemu.guest_agent.0" not in content:
            return _GREY, (
                self.tr(
                    "Guest Agent no habilitado para esta VM "
                    "(actívalo en Integración Host ↔ Guest)."
                )
            )

        try:
            r = self._qga_request({"execute": "guest-info"}, timeout=2)
            if r and "return" in r:
                return _GREEN, self.tr("QEMU Guest Agent responde.")
            return _RED, self.tr("Canal QGA presente, pero el guest no responde.")
        except Exception as e:
            return _RED, self.tr(
                "Canal QGA presente, sin respuesta: {0}"
            ).format(e)

# i18n_tanda3_health_dashboard_v1
