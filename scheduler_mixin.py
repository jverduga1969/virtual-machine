# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: scheduler central de tareas periodicas.

Marcador: scheduler_v1

Cada tarea se registra con:

    self.register_scheduled_task(name, fn, interval_sec)

El scheduler revisa cada 60 s si alguna tarea debe ejecutarse. Las
tareas corren en el hilo de la UI (asi pueden usar QMP, widgets,
dialogos...) por lo que conviene que sean rapidas o que lancen un
worker si van a tardar.

Motivacion: el proyecto va a tener al menos dos features con
necesidades periodicas (snapshots programados #12 y backups #13).
Un unico scheduler central evita tener 2-3 QTimers casi identicos
dentro de distintos mixins.
"""
import time
from PyQt6.QtCore import QTimer


class SchedulerMixin:

    _SCHEDULER_TICK_MS = 60_000  # 1 minuto
    _SCHEDULER_MIN_INTERVAL = 30  # cualquier tarea puede pedir >=30 s

    def _init_scheduler(self):
        """Arranca el QTimer y el registro de tareas. Idempotente."""
        if getattr(self, "_scheduler_timer", None) is not None:
            return
        self._scheduler_tasks = {}
        self._scheduler_timer = QTimer(self)
        self._scheduler_timer.setInterval(self._SCHEDULER_TICK_MS)
        self._scheduler_timer.timeout.connect(self._scheduler_tick)
        self._scheduler_timer.start()
        try:
            self.log_message(
                f"==> Scheduler iniciado (tick cada "
                f"{self._SCHEDULER_TICK_MS // 1000} s)."
            )
        except Exception:
            pass

    def register_scheduled_task(self, name, fn, interval_sec,
                                 run_immediately=False):
        """Registra (o reemplaza) una tarea periodica.

        `interval_sec` se redondea a minimo 30 s. Si `run_immediately`
        es True, la tarea se ejecutara en el primer tick en lugar de
        esperar su intervalo completo.
        """
        if not hasattr(self, "_scheduler_tasks"):
            self._scheduler_tasks = {}
        self._scheduler_tasks[name] = {
            "fn": fn,
            "interval": int(max(self._SCHEDULER_MIN_INTERVAL, interval_sec)),
            "last_run": 0.0 if run_immediately else time.monotonic(),
        }

    def unregister_scheduled_task(self, name):
        tasks = getattr(self, "_scheduler_tasks", None)
        if tasks:
            tasks.pop(name, None)

    def _scheduler_tick(self):
        tasks = getattr(self, "_scheduler_tasks", None)
        if not tasks:
            return
        now = time.monotonic()
        for name, task in list(tasks.items()):
            try:
                if now - task["last_run"] >= task["interval"]:
                    task["last_run"] = now
                    task["fn"]()
            except Exception as e:
                try:
                    self.log_message(
                        f"[AVISO] Tarea programada '{name}' fallo: {e}"
                    )
                except Exception:
                    pass
