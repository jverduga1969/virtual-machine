import os
import logging
import subprocess
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, pyqtSignal

log = logging.getLogger(__name__)

# Mapeo de nuestras opciones a los números del menú de fetch-macOS-v2.py
# Las opciones 1, 2 y 3 (High Sierra, Mojave, Catalina) han sido eliminadas
# porque son sistemas antiguos (2017-2019) y muy problemáticos con QEMU 11+.
MACOS_VERSIONS_MAP = {
    "Big Sur (11.7)": "4",
    "Monterey (12.6)": "5",
    "Ventura (13) ⭐ [ÓPTIMO]": "6",
    "Sonoma (14)": "7",
    "Sequoia (15)": "8",
    "Tahoe": "9",
}

class MacOSDownloader(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, version_label, dest_dir, data_dir):
        super().__init__()
        self.version_label = version_label
        self.dest_dir = Path(dest_dir)
        self.data_dir = Path(data_dir)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
    def start(self):
        # El archivo oficial es un .img en RAW, no qcow2
        img_path = self.dest_dir / "BaseSystem.img"
        if img_path.exists() and img_path.stat().st_size > 100 * 1024 * 1024:
            log.info(f"BaseSystem.img ya existe y es válido. Saltando descarga.")
            self.finished.emit(str(img_path))
            return

        project_root = Path(__file__).parent.parent
        cwd = Path.cwd()
        
        search_paths = [
            project_root / "OSX-KVM",
            self.data_dir / "OSX-KVM",
            cwd / "OSX-KVM",
            Path.home() / "OSX-KVM",
            Path.home() / "Descargas" / "OSX-KVM",
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
        
        dmg_path = self.dest_dir / "BaseSystem.dmg"
        
        for p in (dmg_path, img_path):
            if p.exists():
                try: p.unlink()
                except: pass
        
        self.process.setWorkingDirectory(str(self.dest_dir))
        
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("TERM", "xterm-256color")
        self.process.setProcessEnvironment(env)
        
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._on_finished)
        
        self.progress.emit(f"macOS {self.version_label}\nConectando con Apple...")
        self.process.start("python3", [str(script_path)])
        
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
            
        dmg_path = self.dest_dir / "BaseSystem.dmg"
        img_path = self.dest_dir / "BaseSystem.img"
        
        if not dmg_path.exists():
            self.error.emit("No se generó BaseSystem.dmg.")
            return
            
        self.progress.emit("Convirtiendo a formato RAW (IMG)...\n(Esto puede tardar un poco)")
        
        try:
            # Convertir a RAW (formato .img)
            subprocess.run(["qemu-img", "convert", "-f", "dmg", "-O", "raw", str(dmg_path), str(img_path)], check=True, capture_output=True)
            try: dmg_path.unlink()
            except: pass
            self.finished.emit(str(img_path))
        except Exception as e:
            self.error.emit(f"Error convirtiendo a IMG: {e}")

MacOSRecoveryDownloader = MacOSDownloader
