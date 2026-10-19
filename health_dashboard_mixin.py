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
    QFrame, QWidget, QTabWidget, QPlainTextEdit, QMessageBox,
)
from PyQt6.QtGui import QFont


_GREEN = "#2e7d32"
_YELLOW = "#f9a825"
_RED = "#c62828"
_GREY = "#757575"


class _QgaLiveInfoDialog(QDialog):
    """Diálogo con información del guest obtenida vía QEMU Guest Agent.

    Marcador: qga_live_info_v1.

    Pestañas:
      • Sistema  — distro, versión, kernel, arquitectura, hora vs host.
      • Red      — interfaces con IPs v4/v6, MAC, estado.
      • Usuarios — usuarios logueados ahora (TTY, host, hora de login).
      • Discos   — filesystems con mountpoint, total, usado, libre, % uso.

    Se refresca automáticamente cada 6 s. No-modal: permite seguir
    operando la app mientras está abierto.
    """

    REFRESH_MS = 6000

    def __init__(self, parent, vm_dir, qga_request):
        super().__init__(parent)
        self._vm_dir = vm_dir
        self._qga_request = qga_request
        vm_name = os.path.basename(vm_dir) if vm_dir else "VM"
        self.setWindowTitle(
            self.tr("Información del guest — {0}").format(vm_name)
        )
        self.resize(820, 620)
        self.setModal(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel(self.tr(
            "<b style='font-size:14px;'>"
            "\U0001f50d Información del guest (QGA)</b>"
        ))
        root.addWidget(title)

        subtitle = QLabel(self.tr(
            "Datos obtenidos del sistema invitado a través de QEMU "
            "Guest Agent. Se refresca cada 6 s mientras esta ventana "
            "está abierta."
        ))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#666; font-size:11px;")
        root.addWidget(subtitle)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        _mono = QFont("monospace")
        _mono.setStyleHint(QFont.StyleHint.TypeWriter)

        self._editors = {}
        for key, label in (
            ("sistema",  self.tr("\U0001f5a5\ufe0f Sistema")),
            ("red",      self.tr("\U0001f310 Red")),
            ("usuarios", self.tr("\U0001f464 Usuarios")),
            ("discos",   self.tr("\U0001f4be Discos")),
        ):
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            edit.setFont(_mono)
            edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            edit.setStyleSheet("font-size: 11px;")
            self._editors[key] = edit
            self._tabs.addTab(edit, label)

        root.addWidget(self._tabs, 1)

        bar = QHBoxLayout()
        self._refresh_btn = QPushButton(self.tr("🔄 Refrescar ahora"))
        self._refresh_btn.clicked.connect(self._refresh_all)
        bar.addWidget(self._refresh_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color:#888; font-size:11px;")
        bar.addWidget(self._status_label, 1)

        close_btn = QPushButton(self.tr("Cerrar"))
        close_btn.clicked.connect(self.close)
        bar.addWidget(close_btn)
        root.addLayout(bar)

        self._timer = QTimer(self)
        self._timer.setInterval(self.REFRESH_MS)
        self._timer.timeout.connect(self._refresh_all)

        self._refresh_all()
        self._timer.start()

    def closeEvent(self, event):
        try:
            self._timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Llamadas a QGA
    # ------------------------------------------------------------------

    def _qga_call(self, cmd, timeout=3):
        """Envía un comando QGA. Devuelve el 'return' o None si falla."""
        try:
            r = self._qga_request({"execute": cmd}, timeout=timeout)
        except Exception:
            return None
        if isinstance(r, dict) and "return" in r:
            return r["return"]
        return None

    def _qga_error(self, cmd):
        """Como _qga_call pero distingue 'sin respuesta' de 'error del agente'."""
        try:
            r = self._qga_request({"execute": cmd}, timeout=3)
        except Exception as e:
            return None, str(e)
        if not isinstance(r, dict):
            return None, self.tr("respuesta inesperada del agente")
        if "error" in r:
            err = r["error"]
            if isinstance(err, dict):
                return None, err.get("desc") or str(err)
            return None, str(err)
        return r.get("return"), None

    def _set_editor(self, key, text):
        ed = self._editors.get(key)
        if ed is not None:
            try:
                ed.setPlainText(text)
            except Exception:
                pass

    def _refresh_all(self):
        for key, fn in (
            ("sistema",  self._refresh_sistema),
            ("red",      self._refresh_red),
            ("usuarios", self._refresh_usuarios),
            ("discos",   self._refresh_discos),
        ):
            try:
                fn()
            except Exception as e:
                self._set_editor(key, self.tr("Error: {0}").format(e))
        try:
            self._status_label.setText(
                self.tr("Actualizado a las {0}").format(
                    time.strftime("%H:%M:%S"))
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Pestañas
    # ------------------------------------------------------------------

    def _refresh_sistema(self):
        lines = []

        osinfo, err = self._qga_error("guest-get-osinfo")
        if osinfo is None:
            lines.append(self.tr("SO: no disponible ({0})").format(
                err or self.tr("sin respuesta")))
        elif isinstance(osinfo, dict):
            pretty = osinfo.get("pretty-name") or osinfo.get("name") or "?"
            version_ = osinfo.get("version") or "?"
            kernel = osinfo.get("kernel-release") or "?"
            arch = osinfo.get("machine") or "?"
            kversion = osinfo.get("kernel-version") or ""
            lines.append(self.tr("SO:        {0}").format(pretty))
            lines.append(self.tr("Versión:   {0}").format(version_))
            kline = (kernel + " " + kversion).strip()
            lines.append(self.tr("Kernel:    {0}").format(kline))
            lines.append(self.tr("Arq:       {0}").format(arch))
            if osinfo.get("id"):
                lines.append(self.tr("ID:        {0}").format(osinfo["id"]))

        lines.append("")

        gtime = self._qga_call("guest-get-time")
        if gtime is None:
            lines.append(self.tr("Hora:      no disponible"))
        else:
            try:
                gsec = int(gtime) / 1e9
                hsec = time.time()
                diff = gsec - hsec
                if abs(diff) < 1:
                    diff_txt = self.tr("sincronizada")
                elif diff > 0:
                    diff_txt = self.tr("guest adelantado {0:.1f} s").format(diff)
                else:
                    diff_txt = self.tr("guest atrasado {0:.1f} s").format(abs(diff))
                lines.append(self.tr("Hora guest:  {0}").format(
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(gsec))))
                lines.append(self.tr("Hora host:   {0}").format(
                    time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(hsec))))
                lines.append(self.tr("Desfase:     {0}").format(diff_txt))
            except Exception as e:
                lines.append(self.tr("Hora:      error ({0})").format(e))

        self._set_editor("sistema", "\n".join(lines))

    def _refresh_red(self):
        ifaces = self._qga_call("guest-network-get-interfaces")
        if ifaces is None:
            self._set_editor("red", self.tr(
                "No disponible: el Guest Agent del invitado no responde a\n"
                "guest-network-get-interfaces (puede ser un agente antiguo)."
            ))
            return
        if not isinstance(ifaces, list):
            self._set_editor("red", self.tr("Respuesta inesperada del agente."))
            return

        lines = []
        for iface in ifaces:
            if not isinstance(iface, dict):
                continue
            name = iface.get("name") or "?"
            hwaddr = iface.get("hardware-address") or ""
            addrs = iface.get("ip-addresses") or []
            lines.append(self.tr("Interfaz: {0}").format(name))
            if hwaddr:
                lines.append(self.tr("  MAC:  {0}").format(hwaddr))
            if not addrs:
                lines.append(self.tr("  (sin direcciones IP)"))
            else:
                for ip in addrs:
                    if not isinstance(ip, dict):
                        continue
                    itype = ip.get("ip-address-type") or "?"
                    iaddr = ip.get("ip-address") or "?"
                    plen = ip.get("prefix")
                    if plen is not None:
                        lines.append("  {0}/{1}: {2}".format(
                            itype, plen, iaddr))
                    else:
                        lines.append("  {0}: {1}".format(itype, iaddr))
            lines.append("")

        if not lines:
            lines.append(self.tr("Sin interfaces reportadas."))
        self._set_editor("red", "\n".join(lines))

    def _refresh_usuarios(self):
        users, err = self._qga_error("guest-get-users")
        if users is None:
            self._set_editor("usuarios", self.tr(
                "No disponible: {0}\n\n"
                "(guest-get-users requiere QEMU 5.2+ y un agente\n"
                "razonablemente moderno en el guest.)"
            ).format(err or self.tr("sin respuesta")))
            return
        if not isinstance(users, list):
            self._set_editor("usuarios", self.tr("Respuesta inesperada."))
            return
        if not users:
            self._set_editor("usuarios", self.tr(
                "Ningún usuario con sesión abierta en el guest."))
            return

        lines = []
        for u in users:
            if not isinstance(u, dict):
                continue
            user = u.get("user") or "?"
            tty = u.get("tty") or ""
            host = u.get("host") or ""
            login_ts = u.get("login-time")
            login_txt = ""
            if login_ts:
                try:
                    sec = int(login_ts) / 1e9
                    login_txt = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(sec))
                except Exception:
                    login_txt = str(login_ts)
            lines.append(self.tr("Usuario: {0}").format(user))
            if tty:
                lines.append(self.tr("  TTY:   {0}").format(tty))
            if host:
                lines.append(self.tr("  Desde: {0}").format(host))
            if login_txt:
                lines.append(self.tr("  Login: {0}").format(login_txt))
            lines.append("")
        self._set_editor("usuarios", "\n".join(lines))

    def _refresh_discos(self):
        fs, err = self._qga_error("guest-get-fsinfo")
        if fs is None:
            self._set_editor("discos", self.tr(
                "No disponible: {0}\n\n"
                "(guest-get-fsinfo requiere QEMU 5.2+ y un agente\n"
                "razonablemente moderno en el guest.)"
            ).format(err or self.tr("sin respuesta")))
            return
        if not isinstance(fs, list):
            self._set_editor("discos", self.tr("Respuesta inesperada."))
            return
        if not fs:
            self._set_editor("discos", self.tr(
                "Sin filesystems reportados."))
            return

        def _fmt(n):
            try:
                n = int(n)
            except Exception:
                return "—"
            if n < 1024:
                return "{0} B".format(n)
            if n < 1024 ** 2:
                return "{0:.1f} K".format(n / 1024)
            if n < 1024 ** 3:
                return "{0:.1f} M".format(n / 1024 ** 2)
            if n < 1024 ** 4:
                return "{0:.2f} G".format(n / 1024 ** 3)
            return "{0:.2f} T".format(n / 1024 ** 4)

        hdr = "{0:<34} {1:>10} {2:>10} {3:>10} {4:>6}".format(
            "Mountpoint", "Total", "Usado", "Libre", "Uso%")
        lines = [hdr, "-" * 78]

        for entry in fs:
            if not isinstance(entry, dict):
                continue
            mp = entry.get("mountpoint") or "?"
            if isinstance(mp, list):
                mp = " / ".join(str(x) for x in mp)
            total = entry.get("total-bytes") or 0
            used = entry.get("used-bytes")
            free = entry.get("free-bytes")
            if used is None and free is not None and total:
                used = total - free
            if free is None and used is not None and total:
                free = total - used
            pct = ""
            try:
                if total and used is not None:
                    pct = "{0:.0f}%".format((used / total) * 100)
            except Exception:
                pct = ""
            mp_txt = str(mp)
            if len(mp_txt) > 34:
                mp_txt = "..." + mp_txt[-31:]
            lines.append("{0:<34} {1:>10} {2:>10} {3:>10} {4:>6}".format(
                mp_txt, _fmt(total), _fmt(used), _fmt(free), pct))

        lines.append("")
        lines.append(self.tr("Total de filesystems: {0}").format(
            len([f for f in fs if isinstance(f, dict)])))

        self._set_editor("discos", "\n".join(lines))


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

        # qga_live_info_v1: boton para abrir el dialogo de informacion
        # del guest. Deshabilitado salvo cuando el semaforo de QGA esta
        # verde (esto es, el agente responde a guest-info).
        self._health_qga_details_btn = QPushButton(
            self.tr("\U0001f50d Info del guest")
        )
        self._health_qga_details_btn.setToolTip(self.tr(
            "Abre un dialogo con informacion en vivo del sistema\n"
            "invitado: distro, kernel, interfaces de red, usuarios\n"
            "logueados y uso de disco. Todo via QEMU Guest Agent.\n"
            "\n"
            "Se habilita cuando el semaforo 'Guest Agent' esta verde."
        ))
        self._health_qga_details_btn.setEnabled(False)
        self._health_qga_details_btn.clicked.connect(
            self._open_qga_live_info
        )
        btn_row.addWidget(self._health_qga_details_btn)

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
            self._toggle_qga_details_button(False)
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
            self._toggle_qga_details_button(False)
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
                if key == "qga":
                    self._toggle_qga_details_button(color == _GREEN)
            except Exception as e:
                self._set_health(key, _GREY, f"No se pudo comprobar: {e}")
                if key == "qga":
                    self._toggle_qga_details_button(False)

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
    def _qemu_child_pids(self, qemu_pid):
        """PIDs hijos directos de QEMU (excluye zombies).

        Marcador: audio_probe_pipewire_v1. Se usa para cubrir casos
        donde el nodo de PipeWire/ALSA lo abre un proceso auxiliar
        (raro con QEMU, pero barato de cubrir).
        """
        try:
            r = subprocess.run(
                ["ps", "-o", "pid=", "--ppid", str(qemu_pid)],
                capture_output=True, text=True, timeout=2,
            )
            if r.returncode != 0:
                return set()
            return {int(x) for x in (r.stdout or "").split()
                    if x.strip().isdigit()}
        except Exception:
            return set()

    def _probe_audio_pipewire_node(self, pids):
        """Busca el nodo de QEMU en PipeWire.

        Marcador: audio_probe_pipewire_v2.

        Devuelve (name, state, match_reason) o (None, None, None) si no
        encuentra nada. `state` es el valor de info.state del nodo
        ('running' / 'idle' / 'suspended' / ...).

        Estrategia de match, por orden de preferencia:
          1) application.process.id == PID de QEMU (o de sus hijos o
             del visor externo). Lo mas fiable cuando esta disponible.
          2) application.process.binary contiene 'qemu'.
          3) application.name o node.name contienen 'qemu'.
        En todos los casos filtramos a nodos con media.class que
        empiece por 'Stream/Output' / 'Audio/Sink' / 'Audio/Duplex'
        (playback). Los nodos 'Stream/Input/Audio' (microfono) se
        descartan.
        """
        if not pids:
            pids = set()
        pw_dump = shutil.which("pw-dump")
        if not pw_dump:
            return None, None, None
        try:
            r = subprocess.run(
                [pw_dump], capture_output=True, text=True, timeout=3,
            )
        except Exception:
            return None, None, None
        if r.returncode != 0 or not r.stdout:
            return None, None, None
        import json as _json
        try:
            data = _json.loads(r.stdout)
        except Exception:
            return None, None, None
        if not isinstance(data, list):
            return None, None, None

        pids_int = set()
        for p in (pids or set()):
            try:
                pids_int.add(int(p))
            except Exception:
                continue

        candidates = []

        for node in data:
            if not isinstance(node, dict):
                continue
            if node.get("type") != "PipeWire:Interface:Node":
                continue
            info = node.get("info") or {}
            props = info.get("props") or {}
            mc = str(props.get("media.class") or "")
            if not (mc.startswith("Stream/Output")
                    or mc.startswith("Audio/Sink")
                    or mc.startswith("Audio/Duplex")):
                continue

            bin_ = str(props.get("application.process.binary") or "")
            nm = str(
                props.get("application.name")
                or props.get("node.name")
                or ""
            )
            try:
                node_pid = int(props.get("application.process.id") or 0)
            except Exception:
                node_pid = 0
            state = str(info.get("state") or "")
            name = nm or bin_ or "nodo"

            candidates.append({
                "pid": node_pid,
                "binary": bin_,
                "name": name,
                "state": state,
                "mc": mc,
            })

            if node_pid and node_pid in pids_int:
                return name, state, "pid"
            if "qemu" in bin_.lower():
                return name, state, "binary"
            if "qemu" in nm.lower():
                return name, state, "name"

        try:
            self._audio_last_candidates = candidates
        except Exception:
            pass
        return None, None, None


    def _probe_audio_health(self, vm_dir):
        """Semaforo de audio del dashboard de salud.

        Marcador: audio_probe_pipewire_v2.

        Interpreta el estado del nodo PipeWire:
          - running    -> verde (QEMU esta reproduciendo ahora).
          - idle       -> amarillo informativo.
          - suspended  -> amarillo informativo.
          - error      -> rojo.
        Si no encuentra nodo, cae a pactl / alsa / spice / honesto.
        Si nada funciona, vuelca los nodos Stream/Output/Audio a la
        consola de progreso (una sola vez por VM y sesion).
        """
        run_sh = os.path.join(vm_dir, "run_temp.sh")
        if not os.path.isfile(run_sh):
            return _GREY, self.tr("No hay script de arranque todavía.")
        try:
            with open(run_sh, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return _GREY, self.tr("No se pudo leer el script de arranque.")

        if ("-audiodev" not in content
                and "-device intel-hda" not in content
                and "-device AC97" not in content
                and "-device sb16" not in content):
            return _GREY, self.tr("Sin audio configurado en esta VM.")

        m = re.search(r"-audiodev\s+([A-Za-z0-9_]+)", content)
        backend = (m.group(1).lower() if m else "").strip() or "?"
        kind = {
            "pipewire": "PipeWire",
            "pa":       "PulseAudio / pipewire-pulse",
            "alsa":     "ALSA",
            "spice":    "SPICE (audio por canal)",
        }.get(backend, backend)

        # --- PIDs candidatos ---
        pid_path = os.path.join(vm_dir, "qemu.pid")
        qemu_pid = None
        if os.path.isfile(pid_path):
            try:
                with open(pid_path, encoding="utf-8") as f:
                    qemu_pid = int(f.read().strip())
            except Exception:
                pass
        pids = set()
        if qemu_pid:
            pids.add(qemu_pid)
            try:
                pids |= self._qemu_child_pids(qemu_pid)
            except Exception:
                pass
        try:
            viewers = getattr(self, "_external_viewers", {}) or {}
            entry = viewers.get(vm_dir)
            if entry is not None:
                p = entry.get("proc")
                if p is not None and p.poll() is None:
                    pids.add(p.pid)
        except Exception:
            pass

        # --- 1) PipeWire nativo: pw-dump ---
        if backend == "pipewire":
            name, state, reason = (None, None, None)
            try:
                name, state, reason = self._probe_audio_pipewire_node(pids)
            except Exception:
                pass

            if name:
                _st = (state or "").lower()
                if _st == "running":
                    return _GREEN, self.tr(
                        "PipeWire: reproduciendo (nodo '{0}', match {1})."
                    ).format(name, reason or "?")
                if _st in ("idle", "suspended"):
                    return _YELLOW, self.tr(
                        "PipeWire: nodo '{0}' presente ({1}), sin "
                        "reproducción ahora mismo."
                    ).format(name, _st)
                if _st == "error":
                    return _RED, self.tr(
                        "PipeWire: nodo '{0}' en estado de error."
                    ).format(name)
                return _YELLOW, self.tr(
                    "PipeWire: nodo '{0}' encontrado, estado '{1}'."
                ).format(name, state or "?")

            # Sin nodo: volcar candidatos a la consola de progreso.
            try:
                dumped = getattr(self, "_audio_diag_dumped", None)
                if dumped is None:
                    dumped = set()
                    self._audio_diag_dumped = dumped
                if vm_dir not in dumped:
                    dumped.add(vm_dir)
                    cands = getattr(self, "_audio_last_candidates", []) or []
                    self.log_message(
                        "==> Audio diag (PipeWire): nodo de QEMU no "
                        "detectado. Candidatos Stream/Output/Audio en "
                        "el host:"
                    )
                    if not cands:
                        self.log_message(
                            "        (pw-dump no devolvió ningún nodo "
                            "de playback ni sink.)"
                        )
                    else:
                        for c in cands[:20]:
                            self.log_message(
                                "        PID={0} state={1} mc={2} "
                                "name={3!r} binary={4!r}".format(
                                    c.get("pid"), c.get("state"),
                                    c.get("mc"), c.get("name"),
                                    c.get("binary"),
                                )
                            )
                    self.log_message(
                        "==> Comprueba que QEMU abre un nodo PipeWire "
                        "cuando el guest reproduce sonido. Si no aparece "
                        "ninguno con 'qemu' o el PID de QEMU, el backend "
                        "real no es PipeWire nativo."
                    )
            except Exception:
                pass

            if shutil.which("pw-dump") is None:
                return _YELLOW, self.tr(
                    "Backend PipeWire configurado; no se puede verificar "
                    "reproducción (falta 'pw-dump')."
                )

        # --- 2) pactl (PulseAudio / pipewire-pulse, o respaldo) ---
        pactl = shutil.which("pactl")
        if pactl and pids:
            try:
                r = subprocess.run(
                    [pactl, "list", "sink-inputs"],
                    capture_output=True, text=True, timeout=3,
                )
            except Exception:
                r = None
            if r is not None and r.returncode == 0:
                text = r.stdout or ""
                for pid in pids:
                    if (f'application.process.id = "{pid}"' in text
                            or f'application.process.id = {pid}' in text):
                        return _GREEN, self.tr(
                            "Sink activo ({0}): PID {1} reproduciendo."
                        ).format(kind, pid)
                if "qemu-system-x86_64" in text or "QEMU" in text:
                    return _YELLOW, self.tr(
                        "pactl ve un cliente con pinta de QEMU, pero "
                        "no se pudo confirmar el PID activo."
                    )

        # --- 3) ALSA directo ---
        if backend == "alsa":
            try:
                import glob as _glob
                for pcm_status in _glob.glob(
                        "/proc/asound/card*/pcm*/sub*/status"):
                    try:
                        with open(pcm_status, "r") as f:
                            if "RUNNING" in f.read():
                                return _GREEN, self.tr(
                                    "ALSA: un dispositivo de sonido del "
                                    "host está reproduciendo."
                                )
                    except Exception:
                        continue
            except Exception:
                pass

        # --- 4) Fallback honesto ---
        if not qemu_pid:
            return _YELLOW, self.tr(
                "Backend {0} configurado, pero no hay PID de QEMU para "
                "verificar la reproducción."
            ).format(kind)
        return _YELLOW, (
            self.tr(
                "Backend {0} configurado; no se detecta reproducción "
                "ahora. Es normal si el guest no está emitiendo sonido."
            ).format(kind)
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

    # ------------------------------------------------------------------
    # Info del guest (marcador: qga_live_info_v1)
    # ------------------------------------------------------------------

    def _toggle_qga_details_button(self, enabled):
        """Habilita/deshabilita el boton 'Info del guest' segun el
        semaforo de QGA. Marcador: qga_live_info_v1."""
        btn = getattr(self, "_health_qga_details_btn", None)
        if btn is None:
            return
        try:
            btn.setEnabled(bool(enabled))
        except Exception:
            pass

    def _open_qga_live_info(self):
        """Abre el dialogo de informacion del guest via QGA.

        Marcador: qga_live_info_v1. Reutiliza una unica instancia si
        ya estaba abierta (mismo patron que el propio dashboard).
        """
        if not self.current_vm_dir:
            QMessageBox.information(
                self, self.tr("Info del guest"),
                self.tr("Selecciona primero una maquina virtual.")
            )
            return
        dlg = getattr(self, "_qga_info_dialog", None)
        if dlg is not None:
            try:
                dlg.raise_()
                dlg.activateWindow()
                dlg._refresh_all()
                return
            except Exception:
                pass
        try:
            dlg = _QgaLiveInfoDialog(
                self, self.current_vm_dir, self._qga_request
            )
        except Exception as e:
            QMessageBox.warning(
                self, self.tr("Info del guest"),
                self.tr(
                    "No se pudo abrir el dialogo.\n\n{0}"
                ).format(e)
            )
            return
        self._qga_info_dialog = dlg
        dlg.finished.connect(lambda _: self._clear_qga_info_dialog())
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _clear_qga_info_dialog(self):
        """Limpia la referencia al dialogo cuando se cierra."""
        dlg = getattr(self, "_qga_info_dialog", None)
        if dlg is not None:
            try:
                dlg.deleteLater()
            except Exception:
                pass
            self._qga_info_dialog = None

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

# qga_live_info_v1_applied

# audio_probe_pipewire_v1_applied

# audio_probe_pipewire_v2_applied
