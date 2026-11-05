import subprocess
import logging
import os
import shutil
import socket
import json
from typing import List, Dict

log = logging.getLogger(__name__)

class QMPClient:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)
        self._recv_response()  # Saludo
        self._send("qmp_capabilities")
        self._recv_response()

    def _send(self, command, args=None):
        payload = {"execute": command}
        if args:
            payload["arguments"] = args
        self.sock.sendall(json.dumps(payload).encode() + b'\n')

    def _recv_response(self):
        data = b""
        while True:
            chunk = self.sock.recv(4096)
            if not chunk: break
            data += chunk
            try:
                return json.loads(data.decode())
            except json.JSONDecodeError:
                continue
        return {}

    def execute(self, command, args=None):
        self._send(command, args)
        return self._recv_response()

class SnapshotManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def _get_vm_dir(self, vm: dict) -> str:
        return os.path.join(self.data_dir, "vms", vm.get("id", "unknown"))

    def _get_metadata_file(self, vm: dict) -> str:
        return os.path.join(self._get_vm_dir(vm), "snapshots_meta.json")

    def _load_metadata(self, vm: dict) -> dict:
        f = self._get_metadata_file(vm)
        if os.path.exists(f):
            try:
                with open(f, "r") as file:
                    return json.load(file)
            except: pass
        return {}

    def _save_metadata(self, vm: dict, data: dict):
        f = self._get_metadata_file(vm)
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, "w") as file:
            json.dump(data, file, indent=4)

    def _get_disk_path(self, vm: dict) -> str:
        disk = vm.get("disk_path")
        if disk and os.path.exists(disk):
            return disk
        return None

    def _format_size(self, bytes_size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def get_disk_info(self, vm: dict) -> Dict:
        disk_path = self._get_disk_path(vm)
        if not disk_path: return None

        ext = disk_path.split('.')[-1].upper() if '.' in disk_path else ""
        info = {
            "device": os.path.basename(disk_path),
            "format": ext,
            "virtual_size": "-",
            "file_size": "-",
            "host_free": "-",
            "writable": "No",
            "snapshot_capable": "Sí" if ext == "QCOW2" else "No"
        }

        try:
            info["file_size"] = self._format_size(os.path.getsize(disk_path))
            total, used, free = shutil.disk_usage(os.path.dirname(disk_path))
            info["host_free"] = self._format_size(free)
            info["writable"] = "Sí" if os.access(disk_path, os.W_OK) else "No"

            if vm.get("state") != "Running":
                result = subprocess.run(["qemu-img", "info", "--output=json", disk_path], capture_output=True, text=True, check=True)
                q_info = json.loads(result.stdout)
                info["virtual_size"] = self._format_size(q_info.get("virtual-size", 0))
            else:
                info["virtual_size"] = "En uso"
        except Exception:
            pass
        return info

    def list_snapshots(self, vm: dict) -> List[Dict]:
        disk_path = self._get_disk_path(vm)
        if not disk_path or not disk_path.endswith('.qcow2'):
            return []

        meta = self._load_metadata(vm)
        snapshots = []

        # Si la VM está encendida, usamos QMP
        if vm.get("state") == "Running":
            qmp_socket = vm.get("qmp_socket")
            if not qmp_socket or not os.path.exists(qmp_socket):
                return []
            try:
                client = QMPClient(qmp_socket)
                client.connect()
                response = client.execute("human-monitor-command", {"command-line": "info snapshots"})
                output = response.get("return", "")
                lines = output.splitlines()
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        tag = parts[1]
                        size = parts[2]
                        date_str = f"{parts[3]} {parts[4]}" if len(parts) > 4 else "-"
                        vm_clock = parts[5] if len(parts) > 5 else "-"
                        snapshots.append({
                            "id": "-", "name": tag, "size": size,
                            "date": date_str, "vm_clock": vm_clock,
                            "desc": meta.get(tag, {}).get("desc", ""),
                            "thumbnail": meta.get(tag, {}).get("thumbnail", "")
                        })
            except Exception as e:
                log.error(f"Error QMP listando snapshots: {e}")

        # Si está apagada, usamos qemu-img
        else:
            try:
                result = subprocess.run(["qemu-img", "snapshot", "-l", disk_path], capture_output=True, text=True, check=True)
                lines = result.stdout.strip().splitlines()
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 5:
                            tag = parts[1]
                            snapshots.append({
                                "id": parts[0], "name": tag, "size": parts[2],
                                "date": f"{parts[3]} {parts[4]}",
                                "vm_clock": parts[5] if len(parts) > 5 else "-",
                                "desc": meta.get(tag, {}).get("desc", ""),
                                "thumbnail": meta.get(tag, {}).get("thumbnail", "")
                            })
            except Exception as e:
                log.error(f"Error qemu-img listando snapshots: {e}")

        return snapshots

    def create_snapshot(self, vm: dict, name: str, description: str = "") -> tuple[bool, str]:
        # Asegurar que el directorio de la VM existe
        vm_dir = self._get_vm_dir(vm)
        os.makedirs(vm_dir, exist_ok=True)

        # Tomar screenshot si está encendida
        thumb_path = ""
        if vm.get("state") == "Running" and vm.get("qmp_socket"):
            try:
                thumb_path = os.path.join(vm_dir, f"snap_{name}.png")
                client = QMPClient(vm["qmp_socket"])
                client.connect()
                client.execute("screendump", {"filename": thumb_path})
                log.info(f"Miniatura guardada en {thumb_path}")
            except Exception as e:
                log.warning(f"No se pudo tomar screenshot: {e}")
                thumb_path = ""

        # Crear snapshot
        success = False
        msg = ""
        if vm.get("state") == "Running":
            try:
                client = QMPClient(vm["qmp_socket"])
                client.connect()
                res = client.execute("human-monitor-command", {"command-line": f"savevm {name}"})
                if "error" in res:
                    return False, f"Error QMP: {res['error']['desc']}"
                success = True
            except Exception as e:
                return False, f"Error QMP: {e}"
        else:
            disk_path = self._get_disk_path(vm)
            if not disk_path: return False, "No se encontró disco."
            try:
                subprocess.run(["qemu-img", "snapshot", "-c", name, disk_path], check=True, capture_output=True)
                success = True
            except subprocess.CalledProcessError as e:
                return False, str(e)

        if success:
            meta = self._load_metadata(vm)
            meta[name] = {"desc": description, "thumbnail": thumb_path}
            self._save_metadata(vm, meta)
            return True, f"Snapshot '{name}' creado."

        return False, "Fallo desconocido"

    def restore_snapshot(self, vm: dict, name: str) -> tuple[bool, str]:
        if vm.get("state") == "Running":
            try:
                client = QMPClient(vm["qmp_socket"])
                client.connect()
                res = client.execute("human-monitor-command", {"command-line": f"loadvm {name}"})
                if "error" in res: return False, res["error"]["desc"]
                return True, f"Snapshot '{name}' restaurado."
            except Exception as e:
                return False, str(e)
        else:
            disk_path = self._get_disk_path(vm)
            try:
                subprocess.run(["qemu-img", "snapshot", "-a", name, disk_path], check=True, capture_output=True)
                return True, f"Snapshot '{name}' restaurado."
            except subprocess.CalledProcessError as e:
                return False, str(e)

    def delete_snapshot(self, vm: dict, name: str) -> tuple[bool, str]:
        disk_path = self._get_disk_path(vm)
        try:
            subprocess.run(["qemu-img", "snapshot", "-d", name, disk_path], check=True, capture_output=True)
            meta = self._load_metadata(vm)
            if name in meta:
                # Borrar thumbnail si existe
                if meta[name].get("thumbnail") and os.path.exists(meta[name]["thumbnail"]):
                    try: os.remove(meta[name]["thumbnail"])
                    except: pass
                del meta[name]
                self._save_metadata(vm, meta)
            return True, f"Snapshot '{name}' eliminado."
        except subprocess.CalledProcessError as e:
            return False, str(e)