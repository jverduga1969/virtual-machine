import os
import re
import sys
import platform
import logging
import subprocess
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, pyqtSignal

from services.qemu_paths import qemu_cmd

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Mapeo de nuestras opciones a los números del menú de fetch-macOS-v2.py
MACOS_VERSIONS_MAP = {
    "Big Sur (11.7)": "4",
    "Monterey (12.6)": "5",
    "Ventura (13) ⭐ [ÓPTIMO]": "6",
    "Sonoma (14)": "7",
    "Sequoia (15)": "8",
    "Tahoe": "9",
}


def resolve_macos_version_label(version_label: str) -> str:
    """Acepta etiqueta visible, nombre corto o id guardado por la UI."""
    raw = str(version_label or "").strip()
    if not raw:
        return "Ventura (13) ⭐ [ÓPTIMO]"
    if raw in MACOS_VERSIONS_MAP:
        return raw

    normalized = re.sub(r"[^\w\s.-]", "", raw)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    aliases = {
        "big sur": "Big Sur (11.7)",
        "bigsur": "Big Sur (11.7)",
        "monterey": "Monterey (12.6)",
        "ventura": "Ventura (13) ⭐ [ÓPTIMO]",
        "sonoma": "Sonoma (14)",
        "sequoia": "Sequoia (15)",
        "tahoe": "Tahoe",
        "macos": "Ventura (13) ⭐ [ÓPTIMO]",
    }
    if normalized in aliases:
        return aliases[normalized]

    for label in MACOS_VERSIONS_MAP:
        etiqueta = re.sub(r"[^\w\s.-]", "", label)
        etiqueta = re.sub(r"\s+", " ", etiqueta).strip().lower()
        nombre = etiqueta.split("(")[0].strip()
        if normalized == etiqueta or normalized == nombre:
            return label
        if nombre and nombre in normalized:
            return label
    return raw

class MacOSDownloader(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, version_label, dest_dir, data_dir):
        super().__init__()
        self.version_label = resolve_macos_version_label(version_label)
        self.dest_dir = Path(dest_dir)
        self.data_dir = Path(data_dir)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

    def _get_safe_name(self):
        """Nombre estable por versión para no mezclar ISOs de macOS.

        Ejemplos: Big Sur (11.7) -> BigSur, Mojave -> Mojave.
        """
        nombre = str(self.version_label or "")
        # Quita paréntesis, emojis y sufijos como "⭐ [ÓPTIMO]".
        nombre = re.sub(r"\(.*?\)", "", nombre)
        nombre = re.sub(r"[^\w\s-]", "", nombre)
        nombre = re.sub(r"\s+", " ", nombre).strip()
        if not nombre:
            return "macOS"
        # "Big Sur" -> "BigSur", "Mac OS X" queda raro pero no ocurre aquí.
        return "".join(part.capitalize() for part in re.split(r"[\s_-]+", nombre) if part)

    def start(self):
        # El archivo oficial es un .img en RAW, no qcow2. Ahora usamos el nombre de la versión.
        safe_name = self._get_safe_name()
        img_path = self.dest_dir / f"BaseSystem-{safe_name}.img"
        dmg_path = self.dest_dir / f"BaseSystem-{safe_name}.dmg"
        
        # Si ya existe el IMG final para esta versión, saltamos la descarga
        if img_path.exists() and img_path.stat().st_size > 100 * 1024 * 1024:
            log.info(f"{img_path.name} ya existe y es válido. Saltando descarga.")
            self.finished.emit(str(img_path))
            return

        project_root = Path(__file__).parent.parent
        cwd = Path.cwd()
        
        search_paths = []
        if getattr(sys, "frozen", False):
            search_paths.append(Path(getattr(sys, "_MEIPASS", project_root)) / "OSX-KVM")
        search_paths += [
            project_root / "OSX-KVM",
            self.data_dir / "OSX-KVM",
            cwd / "OSX-KVM",
            Path.home() / "OSX-KVM",
            Path.home() / "Descargas" / "OSX-KVM",
            Path.home() / "Downloads" / "OSX-KVM",
        ]
        
        SCRIPT_NAMES = ["fetch-macOS-v2.py", "fetch-macos.py", "fetch-macos-v2.py", "fetch-macOS.py"]
        
        script_path = None
        for path in search_paths:
            for name in SCRIPT_NAMES:
                candidate = path / name
                if candidate.exists():
                    script_path = candidate
                    log.info(f"Encontrado {name} en: {script_path}")
                    break
            if script_path:
                break
                
        if not script_path:
            paths_str = "\n".join([str(p) for p in search_paths])
            self.error.emit(f"No se encontró fetch-macOS-v2.py.\nSe buscó en:\n{paths_str}")
            return
            
        option_num = MACOS_VERSIONS_MAP.get(self.version_label, "1")
        
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        
        # El script de Apple siempre guarda "BaseSystem.dmg" temporalmente
        temp_dmg = self.dest_dir / "BaseSystem.dmg"
        
        for p in (temp_dmg, dmg_path, img_path):
            if p.exists():
                try: p.unlink()
                except: pass
        
        self.process.setWorkingDirectory(str(self.dest_dir))
        
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        if not IS_WINDOWS:
            env.insert("TERM", "xterm-256color")
        self.process.setProcessEnvironment(env)
        
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._on_finished)
        
        self.progress.emit(f"macOS {self.version_label}\nConectando con Apple...")
        # En el paquete no hay un `python3` garantizado: usamos el intérprete
        # que ya está ejecutando la aplicación.
        self.process.start(sys.executable, [str(script_path)])
        
        if self.process.waitForStarted(5000):
            self.process.write(f"{option_num}\n".encode())
        else:
            self.error.emit("No se pudo iniciar el script de descarga.")
            
    def _read_output(self):
        data = self.process.readAllStandardOutput().data().decode(errors='replace')
        for line in data.replace('\r', '\n').split('\n'):
            line = line.strip()
            if line:
                if "MB" in line or "%" in line:
                    self.progress.emit(f"Descargando BaseSystem.dmg...\n{line}")
                elif "Download complete" in line:
                    self.progress.emit("Descarga completada, preparando conversión...")
                elif "Saving" in line:
                    self.progress.emit(f"Obteniendo enlace de Apple...\n{line}")
                    
    def _on_finished(self, exitCode, exitStatus):
        if exitCode != 0:
            self.error.emit(f"fetch-macos.py falló con código {exitCode}.")
            return
            
        safe_name = self._get_safe_name()
        temp_dmg = self.dest_dir / "BaseSystem.dmg"
        final_dmg = self.dest_dir / f"BaseSystem-{safe_name}.dmg"
        final_img = self.dest_dir / f"BaseSystem-{safe_name}.img"
        
        if not temp_dmg.exists():
            self.error.emit("No se generó BaseSystem.dmg.")
            return
            
        self.progress.emit("Convirtiendo a formato RAW (IMG)...\n(Esto puede tardar un poco)")
        
        try:
            # 1. Renombrar el DMG para que no se pierda el original de la versión
            if final_dmg.exists():
                final_dmg.unlink()
            temp_dmg.rename(final_dmg)
            
            # 2. Convertir a RAW (formato .img) usando el nombre único
            subprocess.run(
                qemu_cmd("qemu-img", "convert", "-f", "dmg", "-O", "raw", str(final_dmg), str(final_img)), 
                check=True, capture_output=True
            )
            
            # 3. Borrar el DMG temporal tras una conversión exitosa para ahorrar espacio
            try: 
                final_dmg.unlink()
            except: 
                pass
                
            self.finished.emit(str(final_img))
        except Exception as e:
            self.error.emit(f"Error convirtiendo a IMG: {e}")

MacOSRecoveryDownloader = MacOSDownloader