# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""API REST local mínima (marcador rest_api_v1).

Servidor HTTP embebido que expone una API JSON para controlar la app
desde scripts, dashboards o CI. Escucha SOLO en 127.0.0.1.

Este módulo es puro (sin PyQt): el servidor corre en un hilo daemon y
delega TODAS las peticiones al handler que le pasa la app. La app (el
mixin ApiMixin) es quien marshalea al hilo principal de Qt.

Diseño:

    ApiServer
        ├─ _ApiHttpd           (ThreadingHTTPServer con ref al ApiServer)
        └─ _ApiHandler         (BaseHTTPRequestHandler)
             ├─ auth: X-API-Token o Authorization: Bearer
             ├─ parse: método, path, body JSON
             └─ dispatch: llama al handler de la app

Autenticación:
    - Si auth_token == "", la API está deshabilitada.
    - El cliente envía "X-API-Token: <token>" o "Authorization: Bearer <token>".
    - /api/health es público (para healthchecks).
"""

import json
import secrets
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


API_VERSION = "1.0"


class _ApiHttpd(ThreadingHTTPServer):
    """HTTPServer con referencia al ApiServer propietario."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, handler, api_server):
        super().__init__(addr, handler)
        self.api_server = api_server


class _ApiHandler(BaseHTTPRequestHandler):
    server_version = "VirtualMachineApi/" + API_VERSION

    # --- Entry points HTTP ---
    def do_GET(self):     self._handle("GET")
    def do_POST(self):    self._handle("POST")
    def do_DELETE(self):  self._handle("DELETE")
    def do_PUT(self):     self._handle("PUT")

    def do_OPTIONS(self):
        # Preflight CORS (útil si un dashboard web local quiere hablar
        # con la API). Sin auth, solo informativo.
        self.send_response(204)
        self._cors_headers()
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def log_message(self, fmt, *args):
        # Silenciar el log por defecto de BaseHTTPRequestHandler.
        pass

    # --- Lógica ---
    def _handle(self, method):
        api_server = self.server.api_server

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        # Normalizar trailing slash excepto en la raíz.
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Auth: /api/health es público, el resto requiere token.
        if path != "/api/health":
            if not api_server._auth_ok(self.headers):
                self._respond(401, {
                    "ok": False,
                    "error": "Autenticación requerida. Envía el header "
                             "X-API-Token: <token> o Authorization: Bearer <token>.",
                })
                return

        # Body JSON para POST/PUT.
        body = {}
        if method in ("POST", "PUT"):
            length = 0
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except Exception:
                length = 0
            if length > 0:
                if length > 8 * 1024 * 1024:
                    self._respond(413, {
                        "ok": False,
                        "error": "Payload demasiado grande (máx 8 MB).",
                    })
                    return
                try:
                    raw = self.rfile.read(length)
                    body = json.loads(raw.decode("utf-8")) or {}
                    if not isinstance(body, dict):
                        body = {"_payload": body}
                except Exception as e:
                    self._respond(400, {
                        "ok": False,
                        "error": f"JSON inválido: {e}",
                    })
                    return

        # Dispatch al handler de la app.
        t0 = time.monotonic()
        try:
            status, data = api_server._dispatch(method, path, body)
        except Exception as e:
            status, data = 500, {
                "ok": False,
                "error": f"Error interno: {e}",
            }
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        # Métricas.
        api_server.requests_handled += 1
        api_server.recent_requests.append({
            "ts": time.time(),
            "method": method,
            "path": path,
            "status": status,
            "ms": elapsed_ms,
        })
        if len(api_server.recent_requests) > 50:
            api_server.recent_requests = api_server.recent_requests[-50:]

        self._respond(status, data)

    def _respond(self, status, data):
        try:
            payload = json.dumps(
                data, ensure_ascii=False, default=str
            ).encode("utf-8")
        except Exception:
            payload = b'{"ok": false, "error": "serializacion fallida"}'
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        try:
            self.wfile.write(payload)
        except Exception:
            pass

    def _cors_headers(self):
        # Solo permitimos orígenes locales. No es un servicio público.
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.send_header(
            "Access-Control-Allow-Headers",
            "X-API-Token, Authorization, Content-Type",
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, DELETE, PUT, OPTIONS",
        )


class ApiServer:
    """Servidor HTTP local con auth por token.

    Uso típico desde el mixin:

        srv = ApiServer(
            host="127.0.0.1", port=8730,
            auth_token="abc...",
            dispatch=self._api_dispatch,
        )
        srv.start()
        ...
        srv.stop()
    """

    def __init__(self, host, port, auth_token, dispatch,
                 on_log=None):
        self.host = str(host or "127.0.0.1")
        self.port = int(port or 8730)
        self.auth_token = str(auth_token or "")
        self._dispatch_cb = dispatch
        self._on_log = on_log
        self._httpd = None
        self._thread = None
        self.requests_handled = 0
        self.recent_requests = []
        self.started_at = None

    # --- Ciclo de vida ---
    def start(self):
        if self._httpd is not None:
            return
        if not self.auth_token:
            raise RuntimeError(
                "ApiServer: auth_token vacío. Genera un token antes de "
                "arrancar el servidor."
            )
        try:
            self._httpd = _ApiHttpd(
                (self.host, self.port), _ApiHandler, self,
            )
        except OSError as e:
            raise RuntimeError(
                f"No se pudo abrir {self.host}:{self.port} — {e}. "
                "¿Otro proceso lo está usando? Prueba otro puerto."
            )
        # Puerto real (por si era 0: el SO asignó uno).
        try:
            self.port = int(self._httpd.server_address[1])
        except Exception:
            pass
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="vm-api-server",
            daemon=True,
        )
        self._thread.start()
        self.started_at = time.time()
        self._log(f"==> API REST escuchando en http://{self.host}:{self.port}/api/")

    def stop(self):
        if self._httpd is None:
            return
        try:
            self._httpd.shutdown()
        except Exception:
            pass
        try:
            self._httpd.server_close()
        except Exception:
            pass
        self._httpd = None
        self._thread = None
        self.started_at = None
        self._log("==> API REST detenida.")

    def is_running(self):
        return self._httpd is not None

    def base_url(self):
        return f"http://{self.host}:{self.port}/api/"

    def uptime_seconds(self):
        if self.started_at is None:
            return 0
        return int(time.time() - self.started_at)

    # --- Internos ---
    def _auth_ok(self, headers):
        if not self.auth_token:
            return False
        token = str(headers.get("X-API-Token") or "").strip()
        if not token:
            auth = str(headers.get("Authorization") or "")
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()
        if not token:
            return False
        return secrets.compare_digest(token, self.auth_token)

    def _dispatch(self, method, path, body):
        return self._dispatch_cb(method, path, body)

    def _log(self, msg):
        if self._on_log is not None:
            try:
                self._on_log(msg)
            except Exception:
                pass


def generate_token():
    """Genera un token aleatorio de 32 bytes (hex, 64 chars)."""
    return secrets.token_hex(32)
