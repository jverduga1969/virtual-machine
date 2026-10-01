# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: API REST local (marcador rest_api_v1).

Puente entre el servidor HTTP (api_server.py, corre en un hilo daemon)
y la app Qt (hilo principal). El servidor NO puede tocar widgets; este
mixin marshalea cada petición al hilo principal usando una señal con
BlockingQueuedConnection.

Expone:

    GET    /api/health                                 (público)
    GET    /api/host
    GET    /api/vms
    GET    /api/vms/{name}
    GET    /api/vms/{name}/stats
    GET    /api/vms/{name}/snapshots
    POST   /api/vms/{name}/start
    POST   /api/vms/{name}/stop
    POST   /api/vms/{name}/force-stop
    POST   /api/vms/{name}/pause
    POST   /api/vms/{name}/resume
    POST   /api/vms/{name}/snapshots           body: {"snapshot_name": "tag"}
    POST   /api/vms/{name}/snapshots/{tag}/restore
    DELETE /api/vms/{name}/snapshots/{tag}

Alcance (MVP mínimo): no hay import/export OVF/OVA, ni creación/borrado
de VMs, ni jobs asíncronos. Las operaciones que tardan minutos se
rechazan con 409 y piden usar la GUI.

Persistencia en QSettings:
    api/enabled   (bool)
    api/port      (int)
    api/token     (str, 64 chars hex)
"""

import json
import os
import re
import shutil
import subprocess
import time

from PyQt6.QtCore import QObject, Qt, QSettings, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QVBoxLayout,
)

import vm_config
from api_server import ApiServer, generate_token, API_VERSION


DEFAULT_API_PORT = 8730


class _ApiBridge(QObject):
    """Canal seguro entre el hilo del servidor HTTP y el hilo de Qt.

    La señal se emite con BlockingQueuedConnection: el hilo del
    servidor queda bloqueado hasta que el slot del hilo principal
    termina. El resultado se escribe en el dict `box` que ambos
    extremos comparten por referencia.
    """

    invoke = pyqtSignal(str, dict, dict)  # handler_name, kwargs, box


class ApiMixin:

    # ------------------------------------------------------------------
    # Rutas (regex sobre el path después de /api)
    # ------------------------------------------------------------------
    _API_ROUTES = [
        ("GET",    r"^/health$",                                        "_api_health"),
        ("GET",    r"^/host$",                                          "_api_host"),
        ("GET",    r"^/vms$",                                           "_api_list_vms"),
        ("GET",    r"^/vms/(?P<name>[^/]+)$",                           "_api_vm_info"),
        ("GET",    r"^/vms/(?P<name>[^/]+)/stats$",                     "_api_vm_stats"),
        ("GET",    r"^/vms/(?P<name>[^/]+)/snapshots$",                 "_api_vm_snapshots"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/start$",                     "_api_vm_start"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/stop$",                      "_api_vm_stop"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/force-stop$",                "_api_vm_force_stop"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/pause$",                     "_api_vm_pause"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/resume$",                    "_api_vm_resume"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/snapshots$",                 "_api_snapshot_create"),
        ("POST",   r"^/vms/(?P<name>[^/]+)/snapshots/(?P<tag>[^/]+)/restore$", "_api_snapshot_restore"),
        ("DELETE", r"^/vms/(?P<name>[^/]+)/snapshots/(?P<tag>[^/]+)$", "_api_snapshot_delete"),
    ]

    # ------------------------------------------------------------------
    # Ciclo de vida (llamado desde _apply_initial_state)
    # ------------------------------------------------------------------

    def _init_api(self):
        """Prepara el bridge y arranca el servidor si estaba habilitado."""
        self._api_bridge = _ApiBridge()
        self._api_bridge.invoke.connect(
            self._api_bridge_invoke_on_main,
            Qt.ConnectionType.BlockingQueuedConnection,
        )
        self._api_server = None

        # Asegurar que exista un token, aunque el servidor esté apagado.
        s = QSettings()
        token = str(s.value("api/token", "") or "").strip()
        if not token:
            token = generate_token()
            s.setValue("api/token", token)

        enabled = bool(s.value("api/enabled", False, type=bool))
        if enabled:
            try:
                self._api_start_server()
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] No se pudo arrancar la API REST: {e}"
                    )
                except Exception:
                    pass

    def _api_start_server(self):
        if getattr(self, "_api_server", None) is not None:
            return
        s = QSettings()
        port = int(s.value("api/port", DEFAULT_API_PORT) or DEFAULT_API_PORT)
        token = str(s.value("api/token", "") or "").strip()
        if not token:
            token = generate_token()
            s.setValue("api/token", token)
        srv = ApiServer(
            host="127.0.0.1",
            port=port,
            auth_token=token,
            dispatch=self._api_dispatch,
            on_log=None,
        )
        srv.start()
        self._api_server = srv
        try:
            self.log_message(
                f"==> API REST activa en {srv.base_url()} "
                f"(usa X-API-Token para autenticarte)."
            )
        except Exception:
            pass

    def _api_stop_server(self):
        srv = getattr(self, "_api_server", None)
        if srv is None:
            return
        try:
            srv.stop()
        except Exception:
            pass
        self._api_server = None
        try:
            self.log_message("==> API REST detenida.")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Dispatch: corre en el HILO DEL SERVIDOR
    # ------------------------------------------------------------------

    def _api_dispatch(self, method, path, body):
        """Enruta una petición al handler correspondiente.

        NO tocar Qt aquí. Este método corre en el hilo del servidor.
        Delega al hilo principal vía el bridge (BlockingQueuedConnection).
        """
        # Quitar el prefijo /api
        sub = path
        if sub.startswith("/api"):
            sub = sub[len("/api"):]
        if not sub:
            sub = "/"

        handler = None
        kwargs = {}
        for verb, rx, hname in self._API_ROUTES:
            if verb != method:
                continue
            m = re.match(rx, sub)
            if not m:
                continue
            handler = hname
            kwargs = dict(m.groupdict())
            break

        if handler is None:
            return 404, {
                "ok": False,
                "error": f"No existe el endpoint {method} {path}",
            }

        kwargs["_body"] = body or {}

        box = {"status": 500, "data": {"ok": False, "error": "sin respuesta"}}
        try:
            self._api_bridge.invoke.emit(handler, kwargs, box)
        except Exception as e:
            return 500, {
                "ok": False,
                "error": f"fallo del bridge: {type(e).__name__}: {e}",
            }
        return box.get("status", 500), box.get("data", {})

    # ------------------------------------------------------------------
    # Slot: corre en el HILO PRINCIPAL
    # ------------------------------------------------------------------

    def _api_bridge_invoke_on_main(self, handler_name, kwargs, box):
        try:
            fn = getattr(self, handler_name, None)
            if fn is None or not callable(fn):
                box["status"] = 500
                box["data"] = {
                    "ok": False,
                    "error": f"handler '{handler_name}' no existe",
                }
                return
            status, data = fn(**kwargs)
            box["status"] = int(status)
            box["data"] = data
        except Exception as e:
            box["status"] = 500
            box["data"] = {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _api_vm_dir(self, name):
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            return None
        vm_dir = os.path.join(vm_config.BASE_VM_DIR, name)
        if not os.path.isdir(vm_dir):
            return None
        return vm_dir

    def _api_vm_state(self, name):
        try:
            return self._runtime_state(name)
        except Exception:
            return "unknown"

    def _api_vm_config(self, name):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return None
        try:
            return self._load_vm_config_cached(vm_dir)
        except Exception:
            return None

    def _api_pid_of(self, vm_dir):
        try:
            pid_path = os.path.join(vm_dir, "qemu.pid")
            if not os.path.isfile(pid_path):
                return None
            with open(pid_path, encoding="utf-8") as f:
                return int((f.read() or "").strip())
        except Exception:
            return None

    # ==================================================================
    # READ-ONLY
    # ==================================================================

    def _api_health(self, **kwargs):
        srv = getattr(self, "_api_server", None)
        uptime = srv.uptime_seconds() if srv is not None else 0
        handled = srv.requests_handled if srv is not None else 0
        return 200, {
            "ok": True,
            "data": {
                "app": "Virtual.Machine",
                "version": "38.1",
                "api_version": API_VERSION,
                "uptime_s": uptime,
                "requests_handled": handled,
            },
        }

    def _api_host(self, **kwargs):
        data = {
            "cpu_model": getattr(self, "cpu_model", "desconocido"),
            "cores": int(getattr(self, "physical_cores", 0) or 0),
            "ram_total_gb": float(getattr(self, "mem_total_gb", 0) or 0),
            "ram_free_gb": float(getattr(self, "mem_free_gb", 0) or 0),
            "kvm_available": os.path.exists("/dev/kvm"),
            "qemu_available": bool(shutil.which("qemu-system-x86_64")),
        }
        return 200, {"ok": True, "data": data}

    def _api_list_vms(self, **kwargs):
        try:
            from vm_config import list_existing_vms
            names = list_existing_vms()
        except Exception:
            names = []
        vms = []
        for name in names:
            cfg = self._api_vm_config(name)
            os_type = ""
            try:
                os_type = str((cfg or {}).get("os_type") or "")
            except Exception:
                pass
            vms.append({
                "name": name,
                "state": self._api_vm_state(name),
                "os_type": os_type,
            })
        return 200, {"ok": True, "data": {"count": len(vms), "vms": vms}}

    def _api_vm_info(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        cfg = self._api_vm_config(name) or {}
        # Normalizamos el dict para no exponer claves crudas del .ini.
        return 200, {
            "ok": True,
            "data": {
                "name": name,
                "state": self._api_vm_state(name),
                "os_type": str(cfg.get("os_type") or ""),
                "ram": str(cfg.get("ram") or ""),
                "cores": int(cfg.get("cores") or 0) if str(cfg.get("cores") or "0").isdigit() else 0,
                "firmware": str(cfg.get("firmware") or ""),
                "chipset": str(cfg.get("chipset") or ""),
                "secure_boot": bool(cfg.get("secure_boot")),
                "tpm": bool(cfg.get("tpm")),
                "graphics_mode": str(cfg.get("graphics_mode") or ""),
                "graphics_vram": str(cfg.get("graphics_vram") or ""),
                "audio_device": str(cfg.get("audio_device") or ""),
                "network_mode": str(cfg.get("network_mode") or ""),
                "boot_order": list(cfg.get("boot_order") or []),
                "vm_dir": vm_dir,
            },
        }

    def _api_vm_stats(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        pid = self._api_pid_of(vm_dir)
        if pid is None:
            return 200, {
                "ok": True,
                "data": {"state": "stopped", "pid": None},
            }
        # RAM: RSS de /proc/<pid>/status
        rss_kb = 0
        try:
            with open(f"/proc/{pid}/status", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        break
        except Exception:
            pass
        # CPU: utime + stime de /proc/<pid>/stat
        cpu_s = 0.0
        try:
            with open(f"/proc/{pid}/stat", encoding="utf-8") as f:
                parts = f.read().split()
            utime = int(parts[13]); stime = int(parts[14])
            hz = os.sysconf("SC_CLK_TCK") or 100
            cpu_s = (utime + stime) / float(hz)
        except Exception:
            pass
        # I/O: read_bytes + write_bytes de /proc/<pid>/io
        io_read = io_write = 0
        try:
            with open(f"/proc/{pid}/io", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("read_bytes:"):
                        io_read = int(line.split()[1])
                    elif line.startswith("write_bytes:"):
                        io_write = int(line.split()[1])
        except Exception:
            pass
        ram_total_gb = float(getattr(self, "mem_total_gb", 0) or 0)
        ram_pct = (rss_kb / (1024 * 1024) / ram_total_gb * 100.0) if ram_total_gb else 0.0
        return 200, {
            "ok": True,
            "data": {
                "state": self._api_vm_state(name),
                "pid": pid,
                "cpu_seconds": round(cpu_s, 2),
                "rss_mb": round(rss_kb / 1024.0, 1),
                "ram_pct_of_host": round(ram_pct, 2),
                "io_read_bytes": io_read,
                "io_write_bytes": io_write,
            },
        }

    def _api_vm_snapshots(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        snapshots = []
        # Recolecta snapshots de todos los QCOW2 de la carpeta. Con la VM
        # apagada, es la única fuente fiable; con la VM encendida, el
        # archivo está bloqueado y qemu-img puede fallar.
        qcows = []
        try:
            for f in sorted(os.listdir(vm_dir)):
                if f.lower().endswith(".qcow2"):
                    qcows.append(os.path.join(vm_dir, f))
        except Exception:
            pass
        seen_tags = set()
        for p in qcows:
            try:
                r = subprocess.run(
                    ["qemu-img", "snapshot", "-l", p],
                    capture_output=True, text=True, timeout=8,
                )
                if r.returncode != 0:
                    continue
                for line in (r.stdout or "").splitlines():
                    parts = line.split()
                    if len(parts) < 2 or not parts[0].isdigit():
                        continue
                    tag = parts[1]
                    if tag in seen_tags:
                        continue
                    seen_tags.add(tag)
                    snapshots.append({
                        "id": parts[0],
                        "tag": tag,
                        "vm_size": parts[2] + " " + parts[3] if len(parts) > 3 else "",
                        "date": parts[4] + " " + parts[5] if len(parts) > 5 else "",
                        "source_file": os.path.basename(p),
                    })
            except Exception:
                continue
        return 200, {
            "ok": True,
            "data": {
                "vm_state": state,
                "count": len(snapshots),
                "snapshots": snapshots,
            },
        }

    # ==================================================================
    # CONTROL
    # ==================================================================

    def _api_vm_start(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        if state in ("running", "paused"):
            return 409, {"ok": False, "error": f"La VM ya está {state}."}
        # Estrategia: si la VM no es la actual, abrirla primero. Esto
        # cambia la selección en la GUI (limitación aceptada del MVP).
        try:
            if not self.current_vm_dir or os.path.basename(self.current_vm_dir) != name:
                self.open_vm(name)
            self.start_installation()
            return 200, {
                "ok": True,
                "data": {
                    "name": name,
                    "action": "start",
                    "note": "La arrancada se ejecuta en la GUI; "
                            "consulta el estado con GET /vms/{name}.",
                },
            }
        except Exception as e:
            return 500, {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def _api_vm_stop(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        if state == "stopped":
            return 409, {"ok": False, "error": "La VM ya está apagada."}
        try:
            self._qmp_hmp(vm_dir, "system_powerdown")
            return 200, {
                "ok": True,
                "data": {"name": name, "action": "stop",
                         "note": "ACPI enviado; el guest puede tardar unos segundos."},
            }
        except Exception as e:
            return 500, {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def _api_vm_force_stop(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        if state == "stopped":
            return 409, {"ok": False, "error": "La VM ya está apagada."}
        try:
            self._kill_vm_process(vm_dir)
            return 200, {
                "ok": True,
                "data": {"name": name, "action": "force-stop"},
            }
        except Exception as e:
            return 500, {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def _api_vm_pause(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        if state != "running":
            return 409, {"ok": False,
                         "error": f"La VM no está corriendo (state={state})."}
        try:
            self._qmp_hmp(vm_dir, "stop")
            return 200, {"ok": True,
                         "data": {"name": name, "action": "pause"}}
        except Exception as e:
            return 500, {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def _api_vm_resume(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        state = self._api_vm_state(name)
        if state != "paused":
            return 409, {"ok": False,
                         "error": f"La VM no está pausada (state={state})."}
        try:
            self._qmp_hmp(vm_dir, "cont")
            return 200, {"ok": True,
                         "data": {"name": name, "action": "resume"}}
        except Exception as e:
            return 500, {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # ==================================================================
    # SNAPSHOTS (solo con la VM apagada, MVP mínimo)
    # ==================================================================

    def _api_snapshot_create(self, name=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        body = kwargs.get("_body") or {}
        tag = str(body.get("snapshot_name") or body.get("name") or "").strip()
        if not tag:
            return 400, {"ok": False,
                         "error": "Falta 'snapshot_name' en el body JSON."}
        tag = re.sub(r"[^A-Za-z0-9_.-]", "_", tag)[:63] or "snapshot"
        state = self._api_vm_state(name)
        if state in ("running", "paused"):
            return 409, {
                "ok": False,
                "error": "La VM está encendida. Este MVP solo crea "
                         "snapshots con la VM apagada. Apágala primero "
                         "o usa la GUI para snapshots en caliente.",
            }
        qcows = []
        try:
            for f in sorted(os.listdir(vm_dir)):
                if f.lower().endswith(".qcow2"):
                    qcows.append(os.path.join(vm_dir, f))
        except Exception:
            pass
        if not qcows:
            return 409, {"ok": False,
                         "error": "No hay discos QCOW2 en la VM."}
        ok_count = 0
        errs = []
        for p in qcows:
            try:
                r = subprocess.run(
                    ["qemu-img", "snapshot", "-c", tag, p],
                    capture_output=True, text=True, timeout=30,
                )
                if r.returncode == 0:
                    ok_count += 1
                else:
                    errs.append(f"{os.path.basename(p)}: "
                                f"{(r.stderr or r.stdout or '').strip()}")
            except Exception as e:
                errs.append(f"{os.path.basename(p)}: {e}")
        if ok_count == 0:
            return 500, {"ok": False,
                         "error": "No se pudo crear el snapshot en ningún "
                                  "QCOW2:\n" + "\n".join(errs)}
        return 201, {
            "ok": True,
            "data": {"name": name, "tag": tag,
                     "disks_ok": ok_count, "errors": errs},
        }

    def _api_snapshot_restore(self, name=None, tag=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        if not tag:
            return 400, {"ok": False, "error": "Falta el tag del snapshot."}
        state = self._api_vm_state(name)
        if state in ("running", "paused"):
            return 409, {
                "ok": False,
                "error": "La VM está encendida. Este MVP solo restaura "
                         "snapshots con la VM apagada.",
            }
        ok_count = 0
        errs = []
        try:
            qcows = [os.path.join(vm_dir, f) for f in sorted(os.listdir(vm_dir))
                     if f.lower().endswith(".qcow2")]
        except Exception:
            qcows = []
        for p in qcows:
            try:
                r = subprocess.run(
                    ["qemu-img", "snapshot", "-a", tag, p],
                    capture_output=True, text=True, timeout=30,
                )
                if r.returncode == 0:
                    ok_count += 1
                else:
                    err = (r.stderr or r.stdout or "").strip()
                    if "not found" in err.lower():
                        continue  # este QCOW2 no tiene ese tag
                    errs.append(f"{os.path.basename(p)}: {err}")
            except Exception as e:
                errs.append(f"{os.path.basename(p)}: {e}")
        if ok_count == 0:
            return 404, {
                "ok": False,
                "error": f"El snapshot '{tag}' no existe en ningún QCOW2 "
                         "de la VM.",
                "details": errs,
            }
        return 200, {"ok": True,
                     "data": {"name": name, "tag": tag,
                              "disks_ok": ok_count, "errors": errs}}

    def _api_snapshot_delete(self, name=None, tag=None, **kwargs):
        vm_dir = self._api_vm_dir(name)
        if vm_dir is None:
            return 404, {"ok": False, "error": f"VM '{name}' no existe."}
        if not tag:
            return 400, {"ok": False, "error": "Falta el tag del snapshot."}
        state = self._api_vm_state(name)
        if state in ("running", "paused"):
            return 409, {
                "ok": False,
                "error": "La VM está encendida. Este MVP solo elimina "
                         "snapshots con la VM apagada.",
            }
        ok_count = 0
        errs = []
        try:
            qcows = [os.path.join(vm_dir, f) for f in sorted(os.listdir(vm_dir))
                     if f.lower().endswith(".qcow2")]
        except Exception:
            qcows = []
        for p in qcows:
            try:
                r = subprocess.run(
                    ["qemu-img", "snapshot", "-d", tag, p],
                    capture_output=True, text=True, timeout=30,
                )
                if r.returncode == 0:
                    ok_count += 1
                else:
                    err = (r.stderr or r.stdout or "").strip()
                    if "not found" in err.lower():
                        continue
                    errs.append(f"{os.path.basename(p)}: {err}")
            except Exception as e:
                errs.append(f"{os.path.basename(p)}: {e}")
        if ok_count == 0:
            return 404, {"ok": False,
                         "error": f"El snapshot '{tag}' no existe."}
        return 200, {"ok": True,
                     "data": {"name": name, "tag": tag,
                              "disks_ok": ok_count, "errors": errs}}

    # ==================================================================
    # UI: sección en Configuración Host
    # ==================================================================

    def _build_api_ui(self, parent_layout):
        """Construye la sección 'API REST local' en Configuración Host."""
        group = QGroupBox("API REST local")
        lay = QFormLayout(group)

        info = QLabel(
            "Expone una API HTTP mínima en <b>127.0.0.1</b> para controlar "
            "VMs desde scripts, dashboards o CI. Todo se autentica con un "
            "token local; <b>no</b> es accesible desde la red."
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        lay.addRow("", info)

        self.chk_api_enabled = QCheckBox("Activar API REST local")
        _s = QSettings()
        self.chk_api_enabled.setChecked(bool(_s.value("api/enabled", False, type=bool)))
        self.chk_api_enabled.toggled.connect(self._on_api_enabled_toggled)
        lay.addRow("", self.chk_api_enabled)

        self.spin_api_port = QSpinBox()
        self.spin_api_port.setRange(1024, 65535)
        self.spin_api_port.setValue(int(_s.value("api/port", DEFAULT_API_PORT) or DEFAULT_API_PORT))
        self.spin_api_port.setToolTip(
            "Puerto TCP donde escucha el servidor. Solo 127.0.0.1.\n"
            "Cambios requieren apagar y volver a encender la API."
        )
        self.spin_api_port.valueChanged.connect(self._on_api_port_changed)
        lay.addRow("Puerto:", self.spin_api_port)

        self.lbl_api_url = QLabel("")
        self.lbl_api_url.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_api_url.setStyleSheet("font-family: monospace; font-size: 11px;")
        lay.addRow("URL:", self.lbl_api_url)

        # Token
        token_row = QHBoxLayout()
        self.input_api_token = QLineEdit()
        self.input_api_token.setReadOnly(True)
        self.input_api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_token.setText(str(_s.value("api/token", "") or ""))
        self.input_api_token.setStyleSheet("font-family: monospace;")
        token_row.addWidget(self.input_api_token, 1)
        self.btn_api_toggle_token = QPushButton("👁")
        self.btn_api_toggle_token.setMaximumWidth(36)
        self.btn_api_toggle_token.setToolTip("Mostrar / ocultar el token")
        self.btn_api_toggle_token.clicked.connect(self._on_api_toggle_token)
        token_row.addWidget(self.btn_api_toggle_token)
        self.btn_api_copy_token = QPushButton("Copiar")
        self.btn_api_copy_token.clicked.connect(self._on_api_copy_token)
        token_row.addWidget(self.btn_api_copy_token)
        self.btn_api_regen_token = QPushButton("Regenerar")
        self.btn_api_regen_token.setToolTip(
            "Genera un token nuevo. Las peticiones con el token anterior\n"
            "dejarán de funcionar."
        )
        self.btn_api_regen_token.clicked.connect(self._on_api_regen_token)
        token_row.addWidget(self.btn_api_regen_token)
        lay.addRow("Token:", token_row)

        # Estado + peticiones
        status_row = QHBoxLayout()
        self.lbl_api_status = QLabel("—")
        status_row.addWidget(self.lbl_api_status)
        status_row.addStretch(1)
        self.btn_api_view_requests = QPushButton("Ver peticiones recientes")
        self.btn_api_view_requests.clicked.connect(self._on_api_view_requests)
        status_row.addWidget(self.btn_api_view_requests)
        lay.addRow("", status_row)

        hint = QLabel(
            "Ejemplo de uso desde terminal:<br>"
            "<code>curl -H 'X-API-Token: &lt;tu-token&gt;' "
            "http://127.0.0.1:8730/api/vms</code>"
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666; font-size:11px;")
        lay.addRow("", hint)

        parent_layout.addWidget(group)
        self._refresh_api_ui()
        return group

    def _refresh_api_ui(self):
        srv = getattr(self, "_api_server", None)
        try:
            if self.lbl_api_url is not None:
                port = self.spin_api_port.value() if hasattr(self, "spin_api_port") else DEFAULT_API_PORT
                self.lbl_api_url.setText(
                    f"http://127.0.0.1:{port}/api/"
                )
            if self.lbl_api_status is not None:
                if srv is not None and srv.is_running():
                    self.lbl_api_status.setText(
                        f"<b style='color:#2e7d32;'>Activa</b> — "
                        f"{srv.requests_handled} peticiones desde el arranque"
                    )
                else:
                    self.lbl_api_status.setText(
                        "<b style='color:#888;'>Detenida</b>"
                    )
        except Exception:
            pass

    def _on_api_enabled_toggled(self, checked):
        try:
            QSettings().setValue("api/enabled", bool(checked))
        except Exception:
            pass
        if checked:
            try:
                self._api_start_server()
            except Exception as e:
                QMessageBox.warning(
                    self, "API REST",
                    f"No se pudo arrancar la API REST.\n\n{e}"
                )
                self.chk_api_enabled.blockSignals(True)
                self.chk_api_enabled.setChecked(False)
                self.chk_api_enabled.blockSignals(False)
                try:
                    QSettings().setValue("api/enabled", False)
                except Exception:
                    pass
        else:
            self._api_stop_server()
        self._refresh_api_ui()

    def _on_api_port_changed(self, value):
        try:
            QSettings().setValue("api/port", int(value))
        except Exception:
            pass
        self._refresh_api_ui()

    def _on_api_toggle_token(self):
        try:
            if self.input_api_token.echoMode() == QLineEdit.EchoMode.Password:
                self.input_api_token.setEchoMode(QLineEdit.EchoMode.Normal)
                self.btn_api_toggle_token.setText("🙈")
            else:
                self.input_api_token.setEchoMode(QLineEdit.EchoMode.Password)
                self.btn_api_toggle_token.setText("👁")
        except Exception:
            pass

    def _on_api_copy_token(self):
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.input_api_token.text() or "")
            self.log_message("==> Token de la API copiado al portapapeles.")
        except Exception:
            pass

    def _on_api_regen_token(self):
        resp = QMessageBox.question(
            self, "Regenerar token",
            "Se generará un token nuevo y el anterior dejará de funcionar.\n\n"
            "¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        new = generate_token()
        try:
            QSettings().setValue("api/token", new)
        except Exception:
            pass
        try:
            self.input_api_token.setText(new)
        except Exception:
            pass
        # Reiniciar el servidor si estaba corriendo para que use el nuevo token.
        was_running = getattr(self, "_api_server", None) is not None
        if was_running:
            self._api_stop_server()
            try:
                self._api_start_server()
            except Exception as e:
                QMessageBox.warning(self, "API REST", f"Se regeneró el token "
                                    f"pero no se pudo reiniciar la API:\n\n{e}")
        self._refresh_api_ui()

    def _on_api_view_requests(self):
        srv = getattr(self, "_api_server", None)
        dlg = QDialog(self)
        dlg.setWindowTitle("Peticiones recientes a la API")
        dlg.resize(720, 420)
        lay = QVBoxLayout(dlg)
        info = QLabel(
            "Últimas peticiones atendidas por la API. Se conservan las "
            "50 más recientes."
        )
        info.setWordWrap(True)
        lay.addWidget(info)
        edit = QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setStyleSheet("font-family: monospace;")
        lines = []
        if srv is not None:
            for r in (srv.recent_requests or []):
                try:
                    t = time.strftime("%H:%M:%S", time.localtime(r.get("ts", 0)))
                    lines.append(
                        f"{t}  {r.get('method','?'):6}  "
                        f"{r.get('path','?'):40}  "
                        f"→ {r.get('status','?')}  ({r.get('ms','?')} ms)"
                    )
                except Exception:
                    continue
        edit.setPlainText("\n".join(lines) or "(sin peticiones todavía)")
        lay.addWidget(edit, 1)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn)
        lay.addLayout(row)
        dlg.exec()

    def _shutdown_api(self):
        """Cierra el servidor. Se llama desde closeEvent."""
        try:
            self._api_stop_server()
        except Exception:
            pass
