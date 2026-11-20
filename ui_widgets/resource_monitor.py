import os
import time
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette


IS_WINDOWS = platform.system() == "Windows"


class RealtimeGraph(QWidget):
    """Widget personalizado para dibujar un gráfico de líneas simple."""
    def __init__(self, title, unit, max_val, color="#3b82f6"):
        super().__init__()
        self.setMinimumHeight(60)
        self.title = title
        self.unit = unit
        self.max_val = max_val
        self.color = QColor(color)
        self.data = [0.0] * 50
        self.current_val = 0.0

    def add_value(self, val):
        self.current_val = min(val, self.max_val)
        self.data.pop(0)
        self.data.append(self.current_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.palette().window())
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        painter.setPen(text_color)
        painter.drawText(5, 15, self.title)
        painter.setPen(self.color)
        painter.drawText(self.width() - 60, 15, f"{self.current_val:.1f} {self.unit}")
        if len(self.data) > 1:
            painter.setPen(QPen(self.color, 2))
            w = self.width()
            h = self.height() - 20
            step = w / (len(self.data) - 1)
            path = []
            for i, val in enumerate(self.data):
                x = i * step
                y = h - (val / self.max_val * h) + 20
                path.append((x, y))
            for i in range(len(path) - 1):
                painter.drawLine(int(path[i][0]), int(path[i][1]),
                                 int(path[i+1][0]), int(path[i+1][1]))
        painter.end()


class ResourceMonitor(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.current_vm_id = None
        self.last_cpu_time = 0
        self.last_time = 0
        self.last_disk_bytes = 0
        self.last_disk_time = 0
        self.last_net_bytes = 0
        self.last_net_time = 0
        # Estado previo para métricas del host
        self._host_prev_cpu   = None
        self._host_prev_net   = None
        self._host_prev_disk  = None
        self._host_prev_time  = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Sección VM ──────────────────────────────────────────────────
        vm_box = QGroupBox("🖥️ Máquina Virtual")
        vm_layout = QVBoxLayout(vm_box)
        vm_layout.setSpacing(4)

        self.graph_cpu  = RealtimeGraph("CPU (VM)",   "%",    100, "#3b82f6")
        self.graph_ram  = RealtimeGraph("RAM (QEMU)", "%",    100, "#10b981")
        self.graph_disk = RealtimeGraph("Disco (VM)", "MB/s", 100, "#f59e0b")
        self.graph_net  = RealtimeGraph("Red (VM)",   "MB/s", 100, "#ef4444")

        for g in (self.graph_cpu, self.graph_ram, self.graph_disk, self.graph_net):
            vm_layout.addWidget(g)

        info_layout = QFormLayout()
        self.lbl_estado      = QLabel("● Apagada")
        self.lbl_uptime      = QLabel("—")
        self.lbl_procesos    = QLabel("—")
        self.lbl_ip          = QLabel("—")
        self.lbl_mac         = QLabel("—")
        self.lbl_guest_agent = QLabel("—")
        info_layout.addRow("Estado:",        self.lbl_estado)
        info_layout.addRow("Tiempo activo:", self.lbl_uptime)
        info_layout.addRow("Procesos:",      self.lbl_procesos)
        info_layout.addRow("Dirección IP:",  self.lbl_ip)
        info_layout.addRow("Dirección MAC:", self.lbl_mac)
        info_layout.addRow("Guest Agent:",   self.lbl_guest_agent)
        vm_layout.addLayout(info_layout)
        layout.addWidget(vm_box)

        # ── Separador ───────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # ── Sección Host ─────────────────────────────────────────────────
        host_box = QGroupBox("🏠 Host")
        host_layout = QVBoxLayout(host_box)
        host_layout.setSpacing(4)

        self.graph_host_cpu = RealtimeGraph("CPU (host)",   "%",    100, "#8b5cf6")
        self.graph_host_ram = RealtimeGraph("RAM (host)",   "%",    100, "#06b6d4")
        self.graph_host_dsk = RealtimeGraph("Disco (host)", "MB/s", 200, "#84cc16")
        self.graph_host_net = RealtimeGraph("Red (host)",   "MB/s", 50,  "#f43f5e")

        for g in (self.graph_host_cpu, self.graph_host_ram,
                  self.graph_host_dsk, self.graph_host_net):
            host_layout.addWidget(g)

        host_info = QFormLayout()
        self.lbl_host_cpu_model = QLabel("—")
        self.lbl_host_ram_total = QLabel("—")
        self.lbl_host_uptime    = QLabel("—")
        self.lbl_host_load      = QLabel("—")
        host_info.addRow("CPU:",         self.lbl_host_cpu_model)
        host_info.addRow("RAM total:",   self.lbl_host_ram_total)
        host_info.addRow("Uptime host:", self.lbl_host_uptime)
        host_info.addRow("Carga:",       self.lbl_host_load)
        host_layout.addLayout(host_info)
        layout.addWidget(host_box)

        layout.addStretch()

        # Poblar etiquetas estáticas del host una sola vez
        self._init_host_static()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start()

    def showEvent(self, event):
        """Reanudar el timer cuando el panel se hace visible."""
        super().showEvent(event)
        self.timer.start()

    def hideEvent(self, event):
        """Pausar el timer cuando el panel se oculta para no gastar CPU."""
        super().hideEvent(event)
        self.timer.stop()

    # ------------------------------------------------------------------ #
    # Host – datos estáticos                                               #
    # ------------------------------------------------------------------ #
    def _init_host_static(self):
        try:
            import multiprocessing
            cores = multiprocessing.cpu_count()
            model = "—"
            if not IS_WINDOWS:
                try:
                    with open("/proc/cpuinfo") as f:
                        for line in f:
                            if "model name" in line:
                                model = line.split(":", 1)[1].strip()
                                break
                except Exception:
                    pass
            self.lbl_host_cpu_model.setText(f"{model} ({cores} núcleos)")

            if not IS_WINDOWS:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            self.lbl_host_ram_total.setText(f"{kb / 1024 / 1024:.1f} GB")
                            break
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Bucle de actualización                                               #
    # ------------------------------------------------------------------ #
    def set_vm(self, vm_id):
        self.current_vm_id = vm_id
        vm = self.app.get_vm(vm_id)
        if vm:
            self.lbl_estado.setText(f"● {self.app.tr(vm.get('state', 'Apagada'))}")
        else:
            self.lbl_estado.setText(self.app.tr("● Sin VM seleccionada"))
        self.last_cpu_time = 0
        self.last_time = 0
        self.last_disk_bytes = 0
        self.last_disk_time = 0
        self.last_net_bytes = 0
        self.last_net_time = 0

    def _update_stats(self):
        try:
            from PyQt6 import sip
            if sip.isdeleted(self):
                self.timer.stop()
                return
        except Exception:
            pass
        self._update_vm_stats()
        self._update_host_stats()

    def _update_vm_stats(self):
        if not self.current_vm_id:
            return
        vm = self.app.get_vm(self.current_vm_id)
        if not vm or vm.get("state") not in ("Running", "Paused"):
            self.lbl_estado.setText(self.app.tr("● Apagada"))
            self.lbl_uptime.setText("—")
            return

        state_text = self.app.tr("Encendida" if vm.get("state") == "Running" else "Pausada")
        self.lbl_estado.setText(f"● {state_text}")

        process = self.app.runner.active_processes.get(self.current_vm_id)
        if not process:
            return

        stats = self._read_proc_stats(process.pid)
        if stats:
            self.graph_cpu.add_value(stats.get("cpu", 0))
            self.graph_ram.add_value(stats.get("ram", 0))
            self.graph_disk.add_value(stats.get("disk", 0))
            self.graph_net.add_value(stats.get("net", 0))
            uptime_sec = stats.get("uptime", 0)
            self.lbl_uptime.setText(f"{uptime_sec // 60}m {uptime_sec % 60}s")
            self.lbl_procesos.setText(str(stats.get("threads", 1)))
            self.lbl_ip.setText(vm.get("ip", "—"))
            self.lbl_mac.setText(vm.get("mac", "—"))
            # El canal virtio-serial del agent se configura en la VM; no hay
            # forma fiable de saber si el servicio dentro del guest está activo.
            self.lbl_guest_agent.setText(
                "Configurado" if vm.get("guest_agent") else "No configurado")

    def _update_host_stats(self):
        if IS_WINDOWS:
            return
        try:
            now = time.time()

            # CPU global (/proc/stat)
            with open("/proc/stat") as f:
                cpu_line = f.readline().split()
            user, nice, system, idle, iowait = (int(cpu_line[i]) for i in range(1, 6))
            total  = sum(int(x) for x in cpu_line[1:])
            active = total - idle - iowait
            if self._host_prev_cpu is not None:
                prev_total, prev_active = self._host_prev_cpu
                dt = total - prev_total
                da = active - prev_active
                cpu_pct = (da / dt * 100) if dt > 0 else 0.0
                self.graph_host_cpu.add_value(cpu_pct)
            self._host_prev_cpu = (total, active)

            # RAM (/proc/meminfo)
            mem = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    mem[k.strip()] = int(v.split()[0])  # en kB
            total_kb = mem.get("MemTotal", 1)
            avail_kb = mem.get("MemAvailable", 0)
            used_pct = (1 - avail_kb / total_kb) * 100
            self.graph_host_ram.add_value(used_pct)

            # Uptime (/proc/uptime)
            with open("/proc/uptime") as f:
                up_sec = int(float(f.read().split()[0]))
            h, rem = divmod(up_sec, 3600)
            m, s   = divmod(rem, 60)
            self.lbl_host_uptime.setText(f"{h}h {m}m {s}s")

            # Carga
            load1, load5, load15 = os.getloadavg()
            self.lbl_host_load.setText(f"{load1:.2f}  {load5:.2f}  {load15:.2f}")

            # Red (/proc/net/dev)
            net_bytes = 0
            with open("/proc/net/dev") as f:
                for line in f.readlines()[2:]:
                    parts = line.split()
                    if parts[0].rstrip(":") != "lo":
                        net_bytes += int(parts[1]) + int(parts[9])
            if self._host_prev_net is not None and self._host_prev_time is not None:
                dt = now - self._host_prev_time
                if dt > 0:
                    self.graph_host_net.add_value(
                        (net_bytes - self._host_prev_net) / 1024 / 1024 / dt)
            self._host_prev_net = net_bytes

            # Disco (/proc/diskstats) — suma de sectores leídos+escritos de discos reales
            disk_sectors = 0
            with open("/proc/diskstats") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 14 and parts[2][:2] in ("sd", "vd", "nv", "hd"):
                        disk_sectors += int(parts[5]) + int(parts[9])  # sect leídos + escritos
            # 1 sector = 512 bytes
            disk_bytes = disk_sectors * 512
            if self._host_prev_disk is not None and self._host_prev_time is not None:
                dt = now - self._host_prev_time
                if dt > 0:
                    self.graph_host_dsk.add_value(
                        (disk_bytes - self._host_prev_disk) / 1024 / 1024 / dt)
            self._host_prev_disk = disk_bytes
            self._host_prev_time = now

        except Exception:
            pass

    def _read_proc_stats(self, pid):
        """Lee /proc para obtener métricas reales del proceso QEMU (solo Linux)."""
        stats = {}
        if IS_WINDOWS:
            try:
                import psutil
                proc = psutil.Process(pid)
                mem_info = proc.memory_info()
                ram_total = psutil.virtual_memory().total
                stats["ram"] = (mem_info.rss / ram_total) * 100 if ram_total else 0
                stats["threads"] = proc.num_threads()
                cores = os.cpu_count() or 1
                stats["cpu"] = proc.cpu_percent(interval=0.1) / cores
                stats["uptime"] = int(time.time() - proc.create_time())
                io = proc.io_counters()
                stats["disk"] = (io.read_bytes + io.write_bytes) / 1024 / 1024
                stats["net"] = 0
            except Exception:
                stats = {"ram": 0, "threads": 1, "cpu": 0, "uptime": 0, "disk": 0, "net": 0}
            return stats
        try:
            # RAM como porcentaje de la memoria TOTAL del host (No como GB).
            mem_total_kb = 1
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total_kb = int(line.split()[1])
                        break

            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        stats["ram"] = (kb / mem_total_kb) * 100
                    elif line.startswith("Threads:"):
                        stats["threads"] = int(line.split()[1])

            with open(f"/proc/{pid}/stat", "r") as f:
                parts = f.read().split()
                utime = int(parts[13])
                stime = int(parts[14])
                total_time = utime + stime
                now = time.time()
                if self.last_cpu_time > 0 and self.last_time > 0:
                    delta_time = total_time - self.last_cpu_time
                    delta_wall = now - self.last_time
                    if delta_wall > 0:
                        cores = os.cpu_count() or 1
                        cpu_pct = (delta_time / os.sysconf('SC_CLK_TCK')) / delta_wall * 100
                        # Normalizar por cores: 100% = todo el host, no 1 core.
                        stats["cpu"] = cpu_pct / cores
                self.last_cpu_time = total_time
                self.last_time = now
                stats["uptime"] = int(now - os.path.getctime(f"/proc/{pid}"))

            with open(f"/proc/{pid}/io", "r") as f:
                io_data = {}
                for line in f:
                    k, v = line.split(": ")
                    io_data[k] = int(v)
                total_io = io_data.get("read_bytes", 0) + io_data.get("write_bytes", 0)
                now = time.time()
                if self.last_disk_bytes > 0 and self.last_disk_time > 0:
                    delta_bytes = total_io - self.last_disk_bytes
                    delta_t = now - self.last_disk_time
                    if delta_t > 0:
                        stats["disk"] = (delta_bytes / 1024 / 1024) / delta_t
                self.last_disk_bytes = total_io
                self.last_disk_time = now

            try:
                with open(f"/proc/{pid}/net/dev", "r") as f:
                    lines = f.readlines()[2:]
                    total_net_bytes = 0
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 10:
                            iface = parts[0].rstrip(':')
                            if iface != 'lo':
                                total_net_bytes += int(parts[1]) + int(parts[9])
                    now = time.time()
                    if self.last_net_bytes > 0 and self.last_net_time > 0:
                        delta_net = total_net_bytes - self.last_net_bytes
                        delta_t = now - self.last_net_time
                        if delta_t > 0:
                            stats["net"] = (delta_net / 1024 / 1024) / delta_t
                    self.last_net_bytes = total_net_bytes
                    self.last_net_time = now
            except Exception:
                stats["net"] = 0

        except Exception:
            pass
        return stats