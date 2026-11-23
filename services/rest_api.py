"""API REST local, enlazada solo a 127.0.0.1.

No sustituye a la interfaz: expone las operaciones que AppContext ya ofrece
para que un script pueda listar y arrancar/apagar VMs. Requiere un token
Bearer que la propia Configuración Host muestra al activarla.
"""

import hmac
import json
import logging
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

log = logging.getLogger(__name__)

_servidor: ThreadingHTTPServer | None = None
_hilo: threading.Thread | None = None


class _Handler(BaseHTTPRequestHandler):
    server_version = "VirtualMachine-REST/1.0"

    def log_message(self, fmt, *args):
        log.debug("REST %s - " + fmt, self.client_address[0], *args)

    def _autorizado(self) -> bool:
        token = getattr(self.server, "token", "")
        cabecera = self.headers.get("Authorization", "")
        return bool(token) and hmac.compare_digest(cabecera, f"Bearer {token}")

    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _ruta_vm(self):
        partes = [p for p in urlparse(self.path).path.split("/") if p]
        if len(partes) == 2 and partes[0] == "vms":
            return partes[1], ""
        if len(partes) == 3 and partes[0] == "vms":
            return partes[1], partes[2]
        return None, None

    def do_GET(self):
        if not self._autorizado():
            self._responder(401, {"error": "unauthorized"})
            return
        ruta = urlparse(self.path).path.rstrip("/") or "/"
        app = self.server.app
        try:
            if ruta == "/health":
                self._responder(200, {"ok": True, "service": "virtual-machine"})
            elif ruta == "/vms":
                self._responder(200, {"vms": app.get_vms()})
            else:
                vm_id, accion = self._ruta_vm()
                if vm_id and not accion:
                    vm = app.get_vm(vm_id)
                    self._responder(200, vm) if vm else self._responder(404, {"error": "not found"})
                else:
                    self._responder(404, {"error": "not found"})
        except Exception as exc:
            log.exception("Error atendiendo GET %s", ruta)
            self._responder(500, {"error": str(exc)})

    def do_POST(self):
        if not self._autorizado():
            self._responder(401, {"error": "unauthorized"})
            return
        vm_id, accion = self._ruta_vm()
        app = self.server.app
        try:
            if not vm_id or accion not in ("start", "stop") or not app.get_vm(vm_id):
                self._responder(404, {"error": "not found"})
                return
            if accion == "start":
                app.start_vm(vm_id)
            else:
                app.stop_vm(vm_id)
            self._responder(202, {"ok": True, "id": vm_id, "action": accion})
        except Exception as exc:
            log.exception("Error atendiendo POST %s/%s", vm_id, accion)
            self._responder(500, {"error": str(exc)})


def is_running() -> bool:
    return _servidor is not None


def start(app, puerto: int, token: str) -> tuple[bool, str]:
    """Arranca el servidor. Devuelve (éxito, mensaje para la UI)."""
    global _servidor, _hilo
    if _servidor is not None:
        return True, f"API ya activa en http://127.0.0.1:{_servidor.server_port}"
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", puerto), _Handler)
    except OSError as exc:
        return False, f"No se pudo abrir el puerto {puerto}: {exc}"
    servidor.app = app
    servidor.token = token
    _hilo = threading.Thread(target=servidor.serve_forever, daemon=True,
                             name="virtual-machine-rest")
    _hilo.start()
    _servidor = servidor
    log.info("API REST escuchando en 127.0.0.1:%s", puerto)
    return True, f"API activa en http://127.0.0.1:{puerto}"


def stop() -> tuple[bool, str]:
    """Detiene el servidor sin dejar hilos ni puertos abiertos."""
    global _servidor, _hilo
    if _servidor is None:
        return True, "API ya estaba detenida"
    servidor, hilo = _servidor, _hilo
    _servidor = None
    _hilo = None
    servidor.shutdown()
    servidor.server_close()
    if hilo is not None:
        hilo.join(timeout=2)
    log.info("API REST detenida")
    return True, "API REST detenida"


def ensure_token(settings) -> str:
    """Token persistente; se genera una sola vez por instalación."""
    token = settings.value("api/token", "")
    if not token:
        token = secrets.token_urlsafe(24)
        settings.setValue("api/token", token)
    return token
