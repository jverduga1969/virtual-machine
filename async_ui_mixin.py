# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Helper para lanzar tareas largas desde la UI sin bloquearla.

Uso:
    self.run_async(
        func=lambda log, cancel, progress: do_heavy_work(log, cancel, progress),
        title="Convirtiendo imagen",
        on_success=lambda r: self.log_message(f"OK: {r}"),
        on_error=lambda e: self._show_selectable_error("Falló", str(e)),
        cancelable=True,
    )

El mixin no conoce PyQt más allá de señales; la lógica pesada corre en
_BackgroundCallThread (definido en workers.py) y el diálogo de progreso
es un TaskProgressDialog.
"""
from workers import _BackgroundCallThread
from task_progress import TaskProgressDialog


class AsyncUiMixin:
    def run_async(self, func, title, *, on_success=None, on_error=None,
                  cancelable=False, show_log=True, subtitle=""):
        """Lanza func en un hilo de fondo con TaskProgressDialog.

        func puede aceptar 1, 2 o 3 argumentos:
            func(log_emit)
            func(log_emit, is_cancelled)
            func(log_emit, is_cancelled, progress_emit)

        Devuelve (thread, dialog). Si ya hay una tarea del mismo tipo
        corriendo, devuelve (None, None) para no solapar.
        """
        active = getattr(self, "_active_task", None)
        if active is not None:
            try:
                if active[0].isRunning():
                    return None, None
            except Exception:
                pass

        dlg = TaskProgressDialog(title, self, cancelable=cancelable,
                                 show_log=show_log, subtitle=subtitle)
        thread = _BackgroundCallThread(func, parent=self)
        thread.log_signal.connect(dlg.append_log)
        thread.progress_signal.connect(dlg.set_progress)

        def _on_done(result, error):
            self._active_task = None
            if error is not None:
                dlg.finish(False, str(error))
                if on_error is not None:
                    try:
                        on_error(error)
                    except Exception as e:
                        try:
                            self.log_message(f"[AVISO] on_error lanzó: {e}")
                        except Exception:
                            pass
            else:
                dlg.finish(True, self.tr("Completado."))
                if on_success is not None:
                    try:
                        on_success(result)
                    except Exception as e:
                        try:
                            self.log_message(f"[AVISO] on_success lanzó: {e}")
                        except Exception:
                            pass

        thread.done_signal.connect(_on_done)
        if cancelable:
            dlg.canceled.connect(thread.request_cancel)

        self._active_task = (thread, dlg)
        dlg.show()
        thread.start()
        return thread, dlg