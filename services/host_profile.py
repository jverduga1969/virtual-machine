import os
import platform
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class HostProfile:
    """Gestiona la detección de hardware y el cálculo de perfiles."""
    def __init__(self):
        self.total_ram_mb = 8192
        self.total_cores = 4
        self._detect_hardware()

    def _detect_hardware(self):
        if IS_WINDOWS:
            detectado = False
            # psutil es una dependencia de la app y da el total real del equipo;
            # WMI puede no estar instalado en Python empaquetado.
            try:
                import psutil
                vm = psutil.virtual_memory()
                self.total_ram_mb = vm.total // (1024 * 1024)
                detectado = True
            except Exception:
                try:
                    import wmi
                    c = wmi.WMI()
                    modulos = [int(int(mem.Capacity) // (1024 * 1024))
                               for mem in c.Win32_PhysicalMemory()]
                    if modulos:
                        # Asignar, nunca sumar al valor por defecto.
                        self.total_ram_mb = sum(modulos)
                        detectado = True
                except Exception:
                    pass
            if not detectado:
                log.error("No se pudo detectar RAM en Windows; usando valor por defecto 8192 MB")
            self.total_cores = os.cpu_count() or 4
            return

        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        kb = int(line.split()[1])
                        self.total_ram_mb = kb // 1024
                        break
        except Exception as e:
            log.error(f"Error detectando RAM: {e}")

        self.total_cores = os.cpu_count() or 4

    def get_profile_settings(self, profile_name: str) -> Dict[str, Any]:
        """Devuelve la configuración recomendada según el perfil y el host."""
        # Límites máximos (mitad del host para no ahogarlo)
        max_ram = min(131072, (self.total_ram_mb // 2)) # Hasta 128GB
        max_cores = min(32, (self.total_cores // 2) * 2) # Hasta 32, número par

        if profile_name == "General / Ofimática":
            return {"cores": min(max_cores, 2), "ram": min(max_ram, 4096), "vram": "128 MB", "graphics": "Automático"}
        elif profile_name == "Desarrollo":
            return {"cores": min(max_cores, 4), "ram": min(max_ram, 8192), "vram": "256 MB", "graphics": "Automático"}
        elif profile_name == "Juegos":
            return {"cores": min(max_cores, 8), "ram": min(max_ram, 16384), "vram": "512 MB", "graphics": "VirtIO-GPU 2D"} # VirGL/Venus iría aquí en el futuro
        elif profile_name == "Ligero":
            return {"cores": min(max_cores, 2), "ram": min(max_ram, 2048), "vram": "64 MB", "graphics": "VGA estándar"}

        return {"cores": 2, "ram": 2048, "vram": "128 MB", "graphics": "Automático"}

    def is_overcommitted(self, ram_mb: int, cores: int) -> bool:
        """Verifica si los valores exceden el host."""
        return ram_mb > self.total_ram_mb or cores > self.total_cores
