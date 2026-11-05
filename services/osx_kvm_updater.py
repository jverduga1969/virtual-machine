import subprocess
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

class OSXKVMUpdater:
    def __init__(self, project_root: Path):
        self.osx_dir = project_root / "OSX-KVM"
        self.repo_url = "https://github.com/kholia/OSX-KVM.git"

    def check_exists(self) -> bool:
        return (self.osx_dir / "OpenCore-Boot.sh").exists()

    def get_current_version(self) -> str:
        git_dir = self.osx_dir / ".git"
        if not git_dir.exists():
            return "Incrustado (no versionado)"
        try:
            result = subprocess.run(
                ["git", "-C", str(self.osx_dir), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception:
            return "Desconocido"

    def update_from_git(self) -> tuple[bool, str]:
        if not self.osx_dir.exists():
            return False, "La carpeta OSX-KVM no existe en el proyecto."

        try:
            # 1. Inicializar si no es repo git
            if not (self.osx_dir / ".git").exists():
                log.info("Inicializando git en OSX-KVM...")
                subprocess.run(["git", "-C", str(self.osx_dir), "init"], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(self.osx_dir), "remote", "add", "origin", self.repo_url], check=True, capture_output=True)
            else:
                # Asegurar que el remote está configurado (por si acaso)
                try:
                    subprocess.run(["git", "-C", str(self.osx_dir), "remote", "get-url", "origin"], capture_output=True, check=True)
                except subprocess.CalledProcessError:
                    subprocess.run(["git", "-C", str(self.osx_dir), "remote", "add", "origin", self.repo_url], check=True, capture_output=True)

            # 2. Fetch
            log.info("Fetching origin...")
            subprocess.run(
                ["git", "-C", str(self.osx_dir), "fetch", "origin", "master"],
                check=True, capture_output=True
            )

            # 3. Reset --hard para sobrescribir cambios locales
            log.info("Haciendo reset --hard a origin/master...")
            subprocess.run(
                ["git", "-C", str(self.osx_dir), "reset", "--hard", "origin/master"],
                check=True, capture_output=True
            )

            return True, "OSX-KVM actualizado con éxito."
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            return False, f"Error de Git: {err}"
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def get_open_core_path(self) -> Path:
        candidate = self.osx_dir / "OpenCore.qcow2"
        if candidate.exists():
            return candidate
        return None