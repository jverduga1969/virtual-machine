# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: monitoreo de rendimiento en vivo (CPU/RAM/disco/red) mientras
la VM corre, mostrado en el panel persistente de recursos (RealtimePerformanceGraph)
y en el panel de Información general (estado, tiempo activo, procesos, IP, MAC).
"""
import os
import subprocess
import time

from vm_config import load_vm_config
from network_utils import sanitize_tap_name
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout


class PerformanceMixin:
    # ==================================================================
    # Panel de recursos: fijar como columna o devolver a Resumen
    # ==================================================================
    def _apply_resources_pinned(self, pinned, save=True):
        """Alterna el bloque "Uso de recursos + Información general".

        pinned=False → vuelven a la grilla de Resumen:
                         (1,0) Uso de recursos  (0,1) Info general
        pinned=True  → se van juntos a la columna derecha del splitter
                         en un contenedor propio.

        El botón 📌 Fijar / ↩ Devolver viaja con el bloque Uso de recursos
        (está en su cabecera), así que siempre está donde se necesita.
        """
        from PyQt6.QtCore import QSettings
        grid = getattr(self, "_resumen_grid", None)
        resources = getattr(self, "_resources_panel", None)
        info_card = getattr(self, "_info_general_card", None)
        splitter = getattr(self, "_main_splitter", None)
        if grid is None or resources is None or info_card is None or splitter is None:
            return

        pinned = bool(pinned)
        prev_pinned = bool(getattr(self, "_resources_pinned", False))

        # Guardar tamaños del estado anterior.
        if save:
            try:
                sizes = splitter.sizes()
                key_old = ("layout/main_splitter_sizes_pinned"
                           if prev_pinned
                           else "layout/main_splitter_sizes")
                QSettings().setValue(key_old, sizes)
            except Exception:
                pass

        # Actualizar el texto del botón.
        btn = getattr(self, "btn_pin_resources", None)
        if btn is not None:
            try:
                if pinned:
                    btn.setText("↩ Devolver")
                    btn.setToolTip(
                        "Devuelve este bloque a la pestaña Resumen."
                    )
                else:
                    btn.setText("📌 Fijar")
                    btn.setToolTip(
                        "Fija este bloque como columna derecha de la ventana,\n"
                        "siempre visible. Útil para monitorizar CPU/RAM y el\n"
                        "estado de la VM mientras trabajas en otra pestaña.\n"
                        "Vuelve a pulsar para devolverlo a Resumen."
                    )
            except Exception:
                pass

        # Detach de la ubicación actual.
        try:
            grid.removeWidget(resources)
        except Exception:
            pass
        try:
            grid.removeWidget(info_card)
        except Exception:
            pass
        try:
            splitter.removeWidget(resources)
        except Exception:
            pass
        try:
            resources.setParent(None)
        except Exception:
            pass
        try:
            info_card.setParent(None)
        except Exception:
            pass

        if pinned:
            # Contenedor temporal para el bloque fijado.
            if getattr(self, "_pinned_container", None) is None:
                self._pinned_container = QWidget()
                self._pinned_container.setMinimumWidth(220)
                self._pinned_container_layout = QVBoxLayout(self._pinned_container)
                self._pinned_container_layout.setContentsMargins(8, 8, 8, 8)
                self._pinned_container_layout.setSpacing(10)
            else:
                lay = getattr(self, "_pinned_container_layout", None)
                if lay is not None:
                    while lay.count():
                        item = lay.takeAt(0)
                        w = item.widget()
                        if w is not None:
                            w.setParent(None)
            self._pinned_container_layout.addWidget(resources)
            self._pinned_container_layout.addWidget(info_card)
            self._pinned_container_layout.addStretch(1)
            try:
                splitter.addWidget(self._pinned_container)
            except Exception:
                pass
            try:
                splitter.setCollapsible(splitter.count() - 1, False)
            except Exception:
                pass
            saved = QSettings().value("layout/main_splitter_sizes_pinned")
            if isinstance(saved, list) and len(saved) == 3:
                try:
                    splitter.setSizes([int(x) for x in saved])
                except (TypeError, ValueError):
                    splitter.setSizes([210, 600, 300])
            else:
                splitter.setSizes([210, 600, 300])
        else:
            # Devolver a la grilla.
            try:
                grid.addWidget(info_card, 0, 1)
                grid.addWidget(resources, 1, 0)
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)
            except Exception:
                pass
            # Quitar el contenedor del splitter si existía.
            cont = getattr(self, "_pinned_container", None)
            if cont is not None:
                try:
                    splitter.removeWidget(cont)
                except Exception:
                    pass
                try:
                    cont.setParent(None)
                except Exception:
                    pass
            saved = QSettings().value("layout/main_splitter_sizes")
            if isinstance(saved, list) and len(saved) >= 2:
                try:
                    splitter.setSizes([int(saved[0]), int(saved[1])])
                except (TypeError, ValueError):
                    splitter.setSizes([210, 900])
            else:
                splitter.setSizes([210, 900])

        self._resources_pinned = pinned
        if save:
            try:
                QSettings().setValue("layout/resources_pinned", pinned)
            except Exception:
                pass



    def _on_main_tab_changed(self, index):
        # Pestaña Snapshots: refrescar la página al entrar.
        if index == getattr(self, '_snapshots_tab_index', -99):
            self.refresh_snapshot_page()
        # Pestaña Passthrough: poblar el árbol la primera vez que se
        # entra. Antes se poblaba al arrancar la app, sumando lspci +
        # lsusb + dmesg al tiempo de inicio sin necesidad.
        if index == getattr(self, '_passthrough_tab_index', -99):
            if getattr(self, '_passthrough_tree_needs_first_populate', False):
                self._passthrough_tree_needs_first_populate = False
                try:
                    self.refresh_passthrough_tree()
                except Exception:
                    pass
        # El monitoreo de recursos vive en un panel persistente (no una pestaña),
        # así que ya no depende de qué pestaña esté activa; ver
        # _ensure_performance_monitoring(), llamada desde open_vm y desde el
        # refresco periódico de estado de la VM.

    def _ensure_performance_monitoring(self):
        """Arranca el monitoreo de recursos de la VM actual.

        Detecta el cambio de VM para que los gráficos y los campos de
        Información general se rellenen inmediatamente, sin esperar al
        siguiente tick del timer ni a que se cumpla el contador de
        lecturas "caras".

        Antes el cambio de VM solo se detectaba por "timer no activo":
        si ya estaba corriendo (porque veníamos de otra VM), la primera
        actualización tardaba hasta 1 s, y los campos pesados hasta 3 s.
        """
        if not self._vm_is_selected():
            self._performance_timer.stop()
            self._reset_perf_history()
            self._update_info_general_labels("stopped")
            # Marcar que no hay VM para que el próximo cambio se detecte.
            self._perf_tracked_vm_dir = None
            return

        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        if state == "stopped":
            self._performance_timer.stop()
            self._reset_perf_history()
            self._update_info_general_labels(state)
            # Aunque la VM esté apagada, seguimos "siguiendo" este vm_dir:
            # así, si vuelve a arrancar, se rellenan los campos sin esperar.
            self._perf_tracked_vm_dir = self.current_vm_dir
            return

        # --- Cambio de VM ---
        current = self.current_vm_dir
        prev = getattr(self, "_perf_tracked_vm_dir", None)
        if prev != current:
            self._perf_tracked_vm_dir = current
            self._reset_perf_history()
            # Forzar la lectura pesada en el primer tick (RAM host, disco,
            # snapshots) — antes podía tardar hasta 3 s.
            self._info_extra_tick = 0
            self._info_extra_force = True

        # Arrancar el timer si no estaba.
        if not self._performance_timer.isActive():
            self._performance_timer.start()

        # Refrescar YA si la pestaña Resumen está visible (si no, se
        # refrescará cuando el usuario vuelva a Resumen). Evita el
        # parpadeo de gráficos vacíos durante 1 s al cambiar de VM.
        try:
            if self._app_is_visible():
                self._update_realtime_performance()
        except Exception:
            pass


    def _reset_perf_history(self):
        self._perf_cpu_hist.clear()
        self._perf_ram_hist.clear()
        self._perf_disk_hist.clear()
        self._perf_net_hist.clear()
        self._perf_prev_io = None
        self._perf_prev_net = None
        self._perf_prev_time = None
        if hasattr(self, 'perf_cpu_graph'):
            self.perf_cpu_graph.set_values([])
            self.perf_ram_graph.set_values([])
            self.perf_disk_graph.set_values([])
            self.perf_net_graph.set_values([])

    def _qemu_io_bytes(self, pid):
        try:
            with open(f"/proc/{pid}/io", "r", encoding="utf-8") as f:
                values = {}
                for line in f:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        values[k.strip()] = int(v.strip())
                return values.get('read_bytes', 0) + values.get('write_bytes', 0)
        except Exception:
            return None

    def _app_is_visible(self):
        """True si la ventana principal está visible Y con foco.

        Se usa para throttling de los gráficos de rendimiento: cuando el
        usuario está en otra app (o la ventana está minimizada), no tiene
        sentido lanzar `ps` y leer /proc/<pid>/io cada segundo.

        Criterios:
          • isMinimized() → oculta (aunque tenga foco en algún WM).
          • isActiveWindow() → sin foco → oculta.
        Si ambas comprobaciones fallan por alguna razón, devolvemos True
        para no romper el comportamiento por defecto.
        """
        try:
            if self.isMinimized():
                return False
            if not self.isActiveWindow():
                return False
        except Exception:
            return True
        return True

    def _update_realtime_performance(self):
        if not self._vm_is_selected():
            self._performance_timer.stop()
            return
        # Throttling: si la ventana está minimizada o en segundo plano,
        # no gastamos subproceso `ps` ni lectura de /proc por segundo.
        # Al volver al frente el timer sigue corriendo y las gráficas
        # se refrescan solas en el siguiente tick.
        if not self._app_is_visible():
            return
        state = self._runtime_state(os.path.basename(self.current_vm_dir))
        if state == 'stopped':
            self._performance_timer.stop()
            self._reset_perf_history()
            self._update_info_general_labels(state)
            self._refresh_general_info_extra()
            return
        pid_path, _ = self._runtime_paths()
        if not pid_path or not os.path.isfile(pid_path):
            return
        try:
            with open(pid_path, encoding='utf-8') as f:
                pid = f.read().strip()
            ps = subprocess.run(['ps', '-p', pid, '-o', '%cpu=,%mem=,rss=,etime='], capture_output=True, text=True, timeout=2)
            parts = ps.stdout.strip().split()
            if len(parts) < 4:
                return
            cpu = float(parts[0])
            mem_pct = float(parts[1])
            rss_kb = int(float(parts[2]))
            etime = parts[3]
            now = time.monotonic()
            io_total = self._qemu_io_bytes(pid)
            # Red: medimos el tráfico de ESTA VM, no todo el host.
            # _vm_network_bytes() detecta el modo (tap/bridge/nat) y
            # devuelve (total, fuente) o (None, motivo).
            net_total, net_source = self._vm_network_bytes(self.current_vm_dir)
            disk_rate = 0.0
            net_rate = 0.0
            if io_total is not None and self._perf_prev_io is not None and self._perf_prev_time:
                dt = max(0.001, now - self._perf_prev_time)
                disk_rate = max(0.0, (io_total - self._perf_prev_io) / dt / (1024**2))
            if net_total is not None and self._perf_prev_net is not None and self._perf_prev_time:
                dt_net = max(0.001, now - self._perf_prev_time)
                net_rate = max(0.0, (net_total - self._perf_prev_net) / dt_net / (1024**2))
            self._perf_prev_io = io_total
            self._perf_prev_net = net_total
            self._perf_prev_time = now
            # ps %mem es relativo a la RAM del host. La tarjeta muestra también el porcentaje.
            cpu_max = max(100.0, min(800.0, float(max(1, self._host_cpu_threads())) * 100.0))
            cpu_pct = min(100.0, cpu / cpu_max * 100.0)
            # Guardar para el panel 'Información general'.
            self._last_cpu_pct = cpu_pct
            self._perf_cpu_hist.append(cpu_pct); self._perf_cpu_hist = self._perf_cpu_hist[-60:]
            self._perf_ram_hist.append(max(0.0, min(100.0, mem_pct))); self._perf_ram_hist = self._perf_ram_hist[-60:]
            self._perf_disk_hist.append(disk_rate); self._perf_disk_hist = self._perf_disk_hist[-60:]
            self._perf_net_hist.append(net_rate); self._perf_net_hist = self._perf_net_hist[-60:]
            self.perf_cpu_graph.max_value = 100.0
            self.perf_ram_graph.max_value = 100.0
            self.perf_disk_graph.max_value = max(10.0, max(self._perf_disk_hist or [0.0]) * 1.25)
            self.perf_net_graph.max_value = max(10.0, max(self._perf_net_hist or [0.0]) * 1.25)
            self.perf_cpu_graph.set_values(self._perf_cpu_hist)
            self.perf_ram_graph.set_values(self._perf_ram_hist)
            self.perf_disk_graph.set_values(self._perf_disk_hist)
            self.perf_net_graph.set_values(self._perf_net_hist)
            self.perf_cpu_graph.title = f"CPU (VM) — {cpu_pct:.0f}% host"
            self.perf_ram_graph.title = f"RAM (QEMU) — {rss_kb/1024:.0f} MiB · {mem_pct:.0f}% host"
            self.perf_disk_graph.title = f"Disco (VM) — {disk_rate:.1f} MB/s"
            if net_total is None:
                # Sin medida posible (p. ej. NAT). Dejamos el gráfico a 0
                # y mostramos el motivo en el título y en el tooltip.
                self.perf_net_graph.title = f"Red (VM) — {net_source or 'sin medida'}"
                self.perf_net_graph.setToolTip(
                    "No hay medida disponible para el modo de red actual.\n"
                    f"Motivo: {net_source or 'sin datos'}.\n\n"
                    "• Modo TAP/Bridge: se leen contadores reales del host.\n"
                    "• Modo NAT: QEMU usa un stack interno sin interfaz\n"
                    "  visible. Para medirlo, cambia la VM a TAP/Bridge\n"
                    "  o activa el Guest Agent."
                )
            else:
                self.perf_net_graph.title = f"Red (VM) — {net_rate:.1f} MB/s"
                self.perf_net_graph.setToolTip(f"Fuente: {net_source}")
            self._refresh_general_info_extra(pid=pid)
            self._update_info_general_labels(state, pid=pid, etime=etime)
        except Exception:
            pass

    def _refresh_general_info_extra(self, pid=None):
        """Actualiza los campos extendidos del panel Información general.

        Los datos "estáticos" del host (RAM libre, tamaño del disco,
        snapshots) se leen cada 3 llamadas (≈ cada 3 s) para no saturar
        el FS ni /proc. Los datos por VM (PID, CPU) se actualizan en cada
        llamada.
        """
        if not hasattr(self, "info_pid_label"):
            return

        # PID de QEMU.
        if pid:
            self.info_pid_label.setText(str(pid))
        else:
            self.info_pid_label.setText("—")

        # Uso de CPU por QEMU (ya lo calcula _update_realtime_performance).
        cpu_pct = None
        if hasattr(self, "_last_cpu_pct"):
            cpu_pct = self._last_cpu_pct
        if cpu_pct is not None:
            self.info_cpu_host_label.setText(f"{cpu_pct:.0f}%")
        else:
            self.info_cpu_host_label.setText("—")

        # Contador para refrescar los datos "caros" solo cada N ticks.
        counter = getattr(self, "_info_extra_tick", 0) + 1
        self._info_extra_tick = counter
        do_heavy = (counter % 3 == 0) or getattr(self, "_info_extra_force", False)
        self._info_extra_force = False

        if not do_heavy:
            return

        # RAM del host: /proc/meminfo (barato, pero no hace falta cada segundo).
        try:
            total_kb = avail_kb = None
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_kb = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        avail_kb = int(line.split()[1])
                    if total_kb is not None and avail_kb is not None:
                        break
            if total_kb and avail_kb is not None:
                total_gb = total_kb / 1024 / 1024
                avail_gb = avail_kb / 1024 / 1024
                used_gb = total_gb - avail_gb
                pct = (used_gb / total_gb * 100) if total_gb else 0
                self.info_ram_host_label.setText(
                    f"{avail_gb:.1f} GB libres / {total_gb:.0f} GB ({pct:.0f}% usado)"
                )
            else:
                self.info_ram_host_label.setText("—")
        except Exception:
            self.info_ram_host_label.setText("—")

        # Disco principal de la VM.
        try:
            disk_path = self._selected_disk_path()
            if disk_path and os.path.isfile(disk_path):
                real = os.path.getsize(disk_path)
                virtual = 0
                try:
                    import json as _json
                    import subprocess as _sp
                    r = _sp.run(
                        ["qemu-img", "info", "--output=json", disk_path],
                        capture_output=True, text=True, timeout=3,
                    )
                    if r.returncode == 0:
                        virtual = int(_json.loads(r.stdout).get("virtual-size", 0) or 0)
                except Exception:
                    pass

                def _fmt(n):
                    if n < 1024:
                        return f"{n} B"
                    if n < 1024**2:
                        return f"{n/1024:.1f} KB"
                    if n < 1024**3:
                        return f"{n/1024**2:.1f} MB"
                    return f"{n/1024**3:.2f} GB"

                if virtual:
                    self.info_disk_size_label.setText(
                        f"{_fmt(real)} / {_fmt(virtual)} virtual"
                    )
                else:
                    self.info_disk_size_label.setText(_fmt(real))
            else:
                self.info_disk_size_label.setText("—")
        except Exception:
            self.info_disk_size_label.setText("—")

        # Snapshots: contar los .png en la carpeta snapshots/ y edad del último.
        try:
            if not self.current_vm_dir:
                self.info_snapshots_label.setText("—")
            else:
                snap_dir = os.path.join(self.current_vm_dir, "snapshots")
                if not os.path.isdir(snap_dir):
                    self.info_snapshots_label.setText("0")
                else:
                    pngs = []
                    for name in os.listdir(snap_dir):
                        if name.endswith(".png"):
                            path = os.path.join(snap_dir, name)
                            try:
                                pngs.append(os.path.getmtime(path))
                            except OSError:
                                pass
                    if not pngs:
                        self.info_snapshots_label.setText("0")
                    else:
                        latest = max(pngs)
                        age_sec = max(0, time.time() - latest)
                        if age_sec < 60:
                            age = "hace <1 min"
                        elif age_sec < 3600:
                            age = f"hace {int(age_sec // 60)} min"
                        elif age_sec < 86400:
                            age = f"hace {int(age_sec // 3600)} h"
                        else:
                            age = f"hace {int(age_sec // 86400)} d"
                        self.info_snapshots_label.setText(
                            f"{len(pngs)} · último {age}"
                        )
        except Exception:
            self.info_snapshots_label.setText("—")

    def _update_info_general_labels(self, state, pid=None, etime=None):
        """Actualiza el panel 'Información general' del lateral derecho."""
        if not hasattr(self, "info_estado_label"):
            return
        labels = {
            "running": ("● En ejecución", "#4ade80"),
            "paused": ("● Pausada", "#f5a623"),
            "stopped": ("● Apagada", "#9aa5c0"),
        }
        text, color = labels.get(state, ("● Desconocido", "#9aa5c0"))
        self.info_estado_label.setText(text)
        self.info_estado_label.setStyleSheet(f"color:{color}; font-weight:bold;")
        self.info_uptime_label.setText(etime or "—")
        if pid and self.current_vm_dir:
            count = 1  # el propio proceso QEMU
            try:
                for fname in os.listdir(self.current_vm_dir):
                    if fname.startswith("virtiofs-") and fname.endswith(".pid"):
                        try:
                            with open(os.path.join(self.current_vm_dir, fname), encoding="utf-8") as f:
                                os.kill(int(f.read().strip()), 0)
                            count += 1
                        except Exception:
                            pass
            except Exception:
                pass
            self.info_procesos_label.setText(str(count))
        else:
            self.info_procesos_label.setText("—")
        # La IP real requiere el Guest Agent (guest-network-get-interfaces);
        # queda pendiente para una fase posterior. La MAC sí se conoce de
        # antemano porque la define la configuración de red de la VM.
        mac = ""
        try:
            devices = self._network_devices()
            if devices:
                mac = devices[0].get("mac", "") or ""
        except Exception:
            pass
        self.info_ip_label.setText("—")
        self.info_mac_label.setText(mac or "automática")

    # ------------------------------------------------------------------
    # Medición del tráfico de red de la VM
    # ------------------------------------------------------------------
    # Antes se usaba _host_network_bytes(), que sumaba TODAS las interfaces
    # del host (incluidas las del propio sistema, no solo las de la VM).
    # Estos dos métodos nuevos detectan el modo de red configurado para la
    # VM y miden lo correcto:
    #   - tap/bridge: leen la interfaz asociada (exacto).
    #   - nat:       no hay interfaz visible → devuelven (None, motivo).

    def _net_iface_counters(self, iface):
        """Devuelve (rx_bytes, tx_bytes) de una interfaz del host, o (None, None)."""
        if not iface:
            return None, None
        base = os.path.join("/sys/class/net", iface, "statistics")
        try:
            with open(os.path.join(base, "rx_bytes")) as f:
                rx = int(f.read().strip())
            with open(os.path.join(base, "tx_bytes")) as f:
                tx = int(f.read().strip())
            return rx, tx
        except Exception:
            return None, None

    def _vm_network_bytes(self, vm_dir):
        """Devuelve (total_bytes, source_label) del tráfico de red de la VM.

        total_bytes: suma rx+tx de todas las interfaces asociadas a la VM.
        source_label: descripción de dónde viene la medida, para el tooltip.
                      Ej.: "tap:qvm-cachyos" / "bridge:br0 (todo el bridge)" /
                      "nat (sin medida)" / "sin interfaces medibles".

        Devuelve (None, motivo) si no se puede medir (NAT, sin config, etc.).
        """
        if not vm_dir:
            return None, "sin VM seleccionada"
        try:
            cfg = load_vm_config(vm_dir)
        except Exception as e:
            return None, f"sin config ({e})"

        devices = cfg.get("network_devices") or []
        if not isinstance(devices, list) or not devices:
            legacy_mode = str(cfg.get("network_mode") or "nat").lower()
            legacy_iface = str(cfg.get("network_interface") or "")
            devices = [{"mode": legacy_mode, "interface": legacy_iface}]

        total = 0
        sources = []
        saw_tap_or_bridge = False
        saw_nat = False

        for i, d in enumerate(devices):
            if not isinstance(d, dict):
                continue
            mode = str(d.get("mode") or "nat").lower()
            iface = str(d.get("interface") or "").strip()

            if mode == "tap":
                if not iface:
                    # Misma lógica que workers.py cuando no se especifica
                    # interface: sanitize_tap_name + sufijo por índice.
                    base = sanitize_tap_name(os.path.basename(vm_dir))
                    if i > 0:
                        iface = f"{base[:13]}{i}"[:15]
                    else:
                        iface = base[:15]
                rx, tx = self._net_iface_counters(iface)
                if rx is not None:
                    total += rx + tx
                    saw_tap_or_bridge = True
                    sources.append(f"tap:{iface}")
                else:
                    sources.append(f"tap:{iface} (no encontrada)")

            elif mode == "bridge":
                if iface:
                    rx, tx = self._net_iface_counters(iface)
                    if rx is not None:
                        # Los contadores del bridge incluyen TODO el tráfico
                        # del bridge, no solo el de esta VM. Se avisa.
                        total += rx + tx
                        saw_tap_or_bridge = True
                        sources.append(f"bridge:{iface} (todo el bridge)")
                    else:
                        sources.append(f"bridge:{iface} (no encontrada)")
                else:
                    sources.append("bridge (sin interfaz)")

            elif mode == "nat":
                saw_nat = True

        if not saw_tap_or_bridge and saw_nat:
            return None, "nat (sin medida precisa)"
        if not sources:
            return None, "sin interfaces medibles"
        return total, " + ".join(sources)

    def _host_network_bytes(self):
        total_rx=total_tx=0
        try:
            with open('/proc/net/dev', encoding='utf-8') as f:
                for line in f:
                    if ':' not in line: continue
                    iface,data=line.split(':',1)
                    iface=iface.strip()
                    if iface == 'lo': continue
                    parts=data.split()
                    if len(parts) >= 9:
                        total_rx += int(parts[0]); total_tx += int(parts[8])
            return total_rx + total_tx
        except Exception:
            return None

    def _host_cpu_threads(self):
        try:
            return int(os.cpu_count() or 1)
        except Exception:
            return 1

    def show_performance(self):
        if not self._vm_is_selected():
            QMessageBox.information(self,"Rendimiento","Selecciona una máquina virtual.")
            return
        name=os.path.basename(self.current_vm_dir)
        state=self._runtime_state(name)
        lines=[f"VM: {name}",f"Estado: {state}"]
        pid_path,_=self._runtime_paths()
        if state != "stopped" and pid_path and os.path.isfile(pid_path):
            try:
                with open(pid_path, encoding="utf-8") as f:
                    pid = f.read().strip()
                ps=subprocess.run(["ps","-p",pid,"-o","%cpu=,%mem=,rss=,etime="],capture_output=True,text=True,timeout=3)
                lines.append(f"QEMU: PID {pid}")
                lines.append(f"CPU / RAM / RSS / tiempo: {ps.stdout.strip() or 'no disponible'}")
            except Exception as e: lines.append(f"Proceso: no disponible ({e})")
        disk=self._selected_disk_path()
        if disk and os.path.isfile(disk):
            try:
                size=os.path.getsize(disk)
                lines.append(f"Archivo de disco: {size/1024**3:.2f} GiB en host")
            except Exception: pass
        try:
            mem=next(x for x in open('/proc/meminfo') if x.startswith('MemAvailable:')).split()[1]
            lines.append(f"RAM disponible en host: {int(mem)/1024/1024:.2f} GiB")
        except Exception: pass
        QMessageBox.information(self,"📈 Rendimiento","\\n".join(lines))

