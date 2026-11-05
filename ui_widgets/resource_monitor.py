import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette


class RealtimeGraph(QWidget):
    """Widget personalizado para dibujar un gráfico de líneas simple."""
    def __init__(self, title, unit, max_val, color="#3b82f6"):
        super().__init__()
        self.setMinimumHeight(60)
        self.title = title
        self.unit = unit
        self.max_val = max_val
        self.color = QColor(color)
        self.data = [0.0] * 50 # Historial de 50 puntos
        self.current_val = 0.0

    def add_value(self, val):
        self.current_val = min(val, self.max_val)
        self.data.pop(0)
        self.data.append(self.current_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Fondo usando la paleta del sistema (claro u oscuro)
        painter.fillRect(self.rect(), self.palette().window())
        
        # 2. Color de texto adaptable al tema
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        
        # Título
        painter.setPen(text_color)
        painter.drawText(5, 15, self.title)
        
        # Valor actual (usando el color de la línea del gráfico)
        painter.setPen(self.color)
        painter.drawText(self.width() - 60, 15, f"{self.current_val:.1f} {self.unit}")
        
        # 3. Dibujar gráfico
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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Gráficos ---
        self.graph_cpu = RealtimeGraph("CPU (VM)", "%", 100, "#3b82f6")
        self.graph_ram = RealtimeGraph("RAM (QEMU)", "%", 100, "#10b981")
        self.graph_disk = RealtimeGraph("Disco (VM)", "MB/s", 100, "#f59e0b")
        self.graph_net = RealtimeGraph("Red (VM)", "MB/s", 100, "#ef4444")
        
        layout.addWidget(self.graph_cpu)
        layout.addWidget(self.graph_ram)
        layout.addWidget(self.graph_disk)
        layout.addWidget(self.graph_net)

        # --- Información general ---
        info_box = QGroupBox("ℹ️ Información general")
        info_layout = QFormLayout(info_box)
        
        self.lbl_estado = QLabel("● Apagada")
        self.lbl_uptime = QLabel("—")
        self.lbl_procesos = QLabel("—")
        self.lbl_ip = QLabel("—")
        self.lbl_mac = QLabel("—")
        self.lbl_guest_agent = QLabel("—")
        
        info_layout.addRow("Estado:", self.lbl_estado)
        info_layout.addRow("Tiempo activo:", self.lbl_uptime)
        info_layout.addRow("Procesos:", self.lbl_procesos)
        info_layout.addRow("Dirección IP:", self.lbl_ip)
        info_layout.addRow("Dirección MAC:", self.lbl_mac)
        info_layout.addRow("Guest Agent:", self.lbl_guest_agent)
        
        layout.addWidget(info_box)
        layout.addStretch()

        # Timer para actualizar
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start()

    def set_vm(self, vm_id):
        self.current_vm_id = vm_id
        vm = self.app.get_vm(vm_id)
        if vm:
            self.lbl_estado.setText(f"● {vm.get('state', 'Apagada')}")
        else:
            self.lbl_estado.setText("● Sin VM seleccionada")
            
        # Resetear estadísticas al cambiar de VM
        self.last_cpu_time = 0
        self.last_time = 0
        self.last_disk_bytes = 0
        self.last_disk_time = 0

    def _update_stats(self):
        if not self.current_vm_id:
            return
            
        vm = self.app.get_vm(self.current_vm_id)
        if not vm or vm.get("state") != "Running":
            self.lbl_estado.setText("● Apagada")
            self.lbl_uptime.setText("—")
            return
            
        self.lbl_estado.setText("● Running (Encendida)")

        # Obtener PID del proceso QEMU
        process = self.app.runner.active_processes.get(self.current_vm_id)
        if not process:
            return
            
        pid = process.pid
        
        # Leer estadísticas reales de /proc
        stats = self._read_proc_stats(pid)
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
            self.lbl_guest_agent.setText("Inactivo")

    def _read_proc_stats(self, pid):
        """Lee /proc para obtener métricas reales del proceso QEMU."""
        stats = {}
        try:
            # RAM (VmRSS)
            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        stats["ram"] = (kb / 1024 / 1024) * 100 # Aprox %
                    elif line.startswith("Threads:"):
                        stats["threads"] = int(line.split()[1])
                        
            # CPU (utime + stime)
            with open(f"/proc/{pid}/stat", "r") as f:
                parts = f.read().split()
                utime = int(parts[13])
                stime = int(parts[14])
                total_time = utime + stime
                
                # Calcular delta
                now = time.time()
                if self.last_cpu_time > 0 and self.last_time > 0:
                    delta_time = total_time - self.last_cpu_time
                    delta_wall = now - self.last_time
                    if delta_wall > 0:
                        cpu_pct = (delta_time / os.sysconf('SC_CLK_TCK')) / delta_wall * 100
                        stats["cpu"] = cpu_pct
                self.last_cpu_time = total_time
                self.last_time = now
                
                # Uptime aproximado
                stats["uptime"] = int(now - os.path.getctime(f"/proc/{pid}"))

            # Disco I/O (read_bytes + write_bytes) - Calculado como tasa MB/s
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

            # Nota: La lectura de red real vía /proc no es trivial porque
            # QEMU usa un socket o tap. Dejamos 0 por ahora.
            stats["net"] = 0

        except Exception:
            pass
            
        return stats