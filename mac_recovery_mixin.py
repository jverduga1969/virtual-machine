# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: descarga del recovery de macOS (para instalar/reinstalar macOS
sin una ISO propia), incluida la verificación del chunklist de Apple.
"""
import os
import shutil
import subprocess
import time
import hashlib
import struct
from PyQt6.QtWidgets import QApplication
from task_progress import TaskProgressDialog


class MacRecoveryMixin:
    def _macos_recovery_product(self):
        """Devuelve los datos necesarios para pedir el Recovery a los servidores de Apple.
        No depende de ejecutar fetch-macOS-v2.py como proceso externo.
        """
        products = [
            {"name": "High Sierra (10.13)", "bid": "Mac-7BA5B2D9E42DDD94", "mlb": "00000000000J80300", "short": "high-sierra", "os": "default"},
            {"name": "Mojave (10.14)", "bid": "Mac-7BA5B2DFE22DDD8C", "mlb": "00000000000KXPG00", "short": "mojave", "os": "default"},
            {"name": "Catalina (10.15)", "bid": "Mac-00BE6ED71E35EB86", "mlb": "00000000000000000", "short": "catalina", "os": "default"},
            {"name": "Big Sur (11.7)", "bid": "Mac-2BD1B31983FE1663", "mlb": "00000000000000000", "short": "big-sur", "os": "default"},
            {"name": "Monterey (12.6)", "bid": "Mac-B809C3757DA9BB8D", "mlb": "00000000000000000", "short": "monterey", "os": "latest"},
            {"name": "Ventura (13)", "bid": "Mac-4B682C642B45593E", "mlb": "00000000000000000", "short": "ventura", "os": "latest"},
            {"name": "Sonoma (14)", "bid": "Mac-827FAC58A8FDFA22", "mlb": "00000000000000000", "short": "sonoma", "os": "default"},
            {"name": "Sequoia (15)", "bid": "Mac-7BA5B2D9E42DDD94", "mlb": "00000000000000000", "short": "sequoia", "os": "default"},
            {"name": "Tahoe (26)", "bid": "Mac-CFF7D910A743CAAF", "mlb": "00000000000000000", "short": "tahoe", "os": "latest"},
        ]
        # La segunda columna de os_options es un código numérico histórico (1..9),
        # mientras que la tabla de Recovery usa el identificador textual "short".
        # La versión elegida debe resolverse por posición/código, nunca comparando
        # directamente "7" con "sonoma" (eso hacía que siempre cayéramos en Sonoma).
        try:
            selected_code = str(self.os_options[self.combo_macos_ver.currentIndex()][1])
        except Exception:
            selected_code = "7"
        code_to_short = {
            "1": "high-sierra", "2": "mojave", "3": "catalina",
            "4": "big-sur", "5": "monterey", "6": "ventura",
            "7": "sonoma", "8": "sequoia", "9": "tahoe",
        }
        selected_short = code_to_short.get(selected_code, "sonoma")
        for product in products:
            if selected_short == product["short"]:
                return product
        return products[6]

    def _macos_recovery_request(self, product):
        """Obtiene de Apple los metadatos firmados de la imagen Recovery."""
        import http.cookiejar
        import urllib.request
        from urllib.parse import urlparse

        headers = {
            "Host": "osrecovery.apple.com",
            "Connection": "close",
            "User-Agent": "InternetRecovery/1.0",
        }
        req = urllib.request.Request("http://osrecovery.apple.com/", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            session_cookie = response.headers.get("Set-Cookie", "")
        session = next((part for part in session_cookie.split("; ") if part.startswith("session=")), "")
        if not session:
            raise RuntimeError("Apple no devolvió una sesión de Recovery válida.")

        import random, string
        def token(n):
            return ''.join(random.choices(string.hexdigits[:16].upper(), k=n))

        post = {
            "cid": token(16),
            "sn": product["mlb"],
            "bid": product["bid"],
            "k": token(64),
            "fg": token(64),
            "os": product["os"],
        }
        body = "\n".join(f"{k}={v}" for k, v in post.items()).encode("utf-8")
        payload_headers = dict(headers)
        payload_headers.update({"Cookie": session, "Content-Type": "text/plain"})
        req = urllib.request.Request(
            "http://osrecovery.apple.com/InstallationPayload/RecoveryImage",
            headers=payload_headers,
            data=body,
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8", errors="replace")
        info = {}
        for line in text.splitlines():
            if ": " in line:
                k, v = line.split(": ", 1)
                info[k.strip()] = v.strip()
        required = ("AP", "AU", "AH", "AT", "CU", "CH", "CT")
        missing = [k for k in required if k not in info]
        if missing:
            raise RuntimeError("Apple no devolvió todos los datos del Recovery: " + ", ".join(missing))
        return info

    def _macos_recovery_download_stream(self, url, asset_token, filename, dlg, label, is_cancelled=None):
        """Descarga un asset de Apple mostrando progreso en el TaskProgressDialog.

        dlg debe exponer set_progress(int, str). El progreso se reporta con
        texto "label — NN% (MB/MB)". Se consulta is_cancelled() entre chunks
        para permitir cancelación cooperativa.
        """
        import urllib.request
        from urllib.parse import urlparse
        purl = urlparse(url)
        headers = {
            "Host": purl.hostname or "osrecovery.apple.com",
            "Connection": "close",
            "User-Agent": "InternetRecovery/1.0",
            "Cookie": "AssetToken=" + asset_token,
        }
        request = urllib.request.Request(url, headers=headers)
        tmp = filename + ".part"
        done = 0
        last_percent = -1
        last_update = 0.0
        with urllib.request.urlopen(request, timeout=60) as response, open(tmp, "wb") as fh:
            total = int(response.headers.get("Content-Length", "0") or 0)
            while True:
                if is_cancelled is not None and is_cancelled():
                    raise RuntimeError("Descarga cancelada por el usuario.")
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                done += len(chunk)
                now = time.monotonic()
                pct = min(100.0, done * 100.0 / total) if total > 0 else 0.0
                if pct >= 100.0 or int(pct) != last_percent or now - last_update >= 0.5:
                    last_percent = int(pct)
                    last_update = now
                    done_mb = done / (1024 ** 2)
                    total_mb = total / (1024 ** 2) if total else 0.0
                    if total:
                        text = f"{label} — {pct:.1f}% ({done_mb:.1f}/{total_mb:.1f} MB)"
                        dlg.set_progress(int(pct), text)
                    else:
                        text = f"{label} — {done_mb:.1f} MB descargados"
                        dlg.set_progress(-1, text)
        os.replace(tmp, filename)
        dlg.set_progress(100, f"{label} — 100%")
        return filename

    def _verify_macos_chunklist(self, dmgpath, cnkpath):
        """Verifica el DMG usando el chunklist firmado entregado por Apple."""
        import hashlib
        import struct
        header_struct = struct.Struct("<4sIBBBxQQQ")
        chunk_struct = struct.Struct("<I32s")
        with open(cnkpath, "rb") as f:
            data = f.read(header_struct.size)
            if len(data) != header_struct.size:
                raise RuntimeError("El chunklist de System Recovery está incompleto.")
            magic, header_size, file_version, chunk_method, signature_method, chunk_count, chunk_offset, signature_offset = header_struct.unpack(data)
            if magic != b"CNKL" or header_size != header_struct.size or file_version != 1 or chunk_method != 1:
                raise RuntimeError("Cabecera de chunklist de Apple no válida.")
            if chunk_count <= 0 or chunk_offset != 0x24:
                raise RuntimeError("Chunklist de Apple no válido.")
            with open(dmgpath, "rb") as dmg:
                for index in range(chunk_count):
                    entry = f.read(chunk_struct.size)
                    if len(entry) != chunk_struct.size:
                        raise RuntimeError(f"Chunklist truncado en el bloque {index + 1}.")
                    chunk_size, expected = chunk_struct.unpack(entry)
                    chunk = dmg.read(chunk_size)
                    if len(chunk) != chunk_size or hashlib.sha256(chunk).digest() != expected:
                        raise RuntimeError(f"La verificación del Recovery falló en el bloque {index + 1}.")
                    QApplication.processEvents()
                if dmg.read(1) != b"":
                    raise RuntimeError("La imagen Recovery contiene datos adicionales no descritos por el chunklist.")
        return True

    def _download_macos_recovery_for_vm(self):
        """Lanza la descarga del Recovery en segundo plano (no bloquea la UI).

        Devuelve None inmediatamente. El llamador que necesite el path final
        debe consultar self.current_vm_dir/BaseSystem.img cuando la tarea
        asíncrona termine (o pulsar Iniciar de nuevo tras la descarga).
        """
        if not self.current_vm_dir:
            raise RuntimeError("No hay una carpeta de VM seleccionada.")
        os.makedirs(self.current_vm_dir, exist_ok=True)
        product = self._macos_recovery_product()
        vm_dir = self.current_vm_dir

        def _work(log_emit, is_cancelled, progress_emit):
            return self._macos_recovery_impl(product, vm_dir, is_cancelled, progress_emit, log_emit)

        self.run_async(
            _work,
            f"System Recovery de macOS — {product['name']}",
            on_success=lambda img: self.log_message(f"==> Recovery preparado: {os.path.basename(img)}"),
            on_error=lambda e: self.log_message(f"[ERROR] Recovery: {e}"),
            cancelable=True,
            show_log=True,
            subtitle="La imagen se descarga y verifica directamente en la carpeta de la VM.",
        )
        return None

    def _macos_recovery_impl(self, product, vm_dir, is_cancelled, progress_emit, log_emit):
        """Cuerpo real; corre en hilo de fondo. progress_emit(pct, text) es seguro."""
        class _Dlg:
            """Adaptador que expone set_progress para el stream."""
            def __init__(self, emit_progress, emit_log):
                self._emit_progress = emit_progress
                self._emit_log = emit_log
            def set_progress(self, percent, text=""):
                self._emit_progress(int(percent), text or "")
                if text:
                    self._emit_log(text)
            def append_log(self, line):
                if line:
                    self._emit_log(line)

        dlg = _Dlg(progress_emit, log_emit)

        dmg = os.path.join(vm_dir, "BaseSystem.dmg")
        cnk = os.path.join(vm_dir, "BaseSystem.chunklist")
        img = os.path.join(vm_dir, "BaseSystem.img")
        tmp_dmg = dmg + ".part"
        tmp_cnk = cnk + ".part"
        try:
            log_emit("Consultando Apple para obtener System Recovery…")
            progress_emit(-1, "Consultando Apple…")
            info = self._macos_recovery_request(product)
            log_emit(f"Producto Recovery: {info.get('AP', product['name'])}")

            log_emit("Descargando firma/chunklist de System Recovery…")
            progress_emit(0, "Descargando chunklist…")
            self._macos_recovery_download_stream(
                info["CU"], info["CT"], tmp_cnk, dlg,
                "Descargando chunklist", is_cancelled=is_cancelled,
            )
            os.replace(tmp_cnk, cnk)

            log_emit("Descargando imagen BaseSystem.dmg…")
            progress_emit(0, "Descargando BaseSystem.dmg…")
            self._macos_recovery_download_stream(
                info["AU"], info["AT"], tmp_dmg, dlg,
                "Descargando BaseSystem.dmg", is_cancelled=is_cancelled,
            )
            os.replace(tmp_dmg, dmg)

            log_emit("Verificando System Recovery con chunklist…")
            progress_emit(-1, "Verificando integridad…")
            self._verify_macos_chunklist(dmg, cnk)
            progress_emit(100, "Verificación completada.")
            log_emit("Verificación de System Recovery completada.")

            dmg2img = shutil.which("dmg2img")
            if not dmg2img:
                import system_deps
                dmg2img = system_deps.ensure_dmg2img(log_emit)
            if not dmg2img:
                raise RuntimeError("No se encontró 'dmg2img' y no se pudo instalar automáticamente. "
                                   "Instálalo con el gestor de paquetes (en Arch/CachyOS: paru -S dmg2img).")
            log_emit("Preparando BaseSystem.img para OpenCore (dmg2img)…")
            progress_emit(-1, "Convirtiendo BaseSystem.dmg → BaseSystem.img…")
            result = subprocess.run([dmg2img, dmg, img], capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError("dmg2img no pudo preparar BaseSystem.img.\n" + (result.stderr or result.stdout or "sin detalles"))
            if not os.path.isfile(img) or os.path.getsize(img) == 0:
                raise RuntimeError("dmg2img terminó pero BaseSystem.img no existe o está vacío.")
            log_emit(f"Recovery preparado: {os.path.basename(img)}")
            return img
        finally:
            for tmp in (tmp_dmg, tmp_cnk):
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass
