# Changelog

Registro de cambios aplicados al proyecto **Virtual.Machine** por etapas de mejora continua.

## Etapa 1 — Quick wins visibles

- Auto-selección de consola al crear VM.
- Botón "📋 Copiar comando" en el toolbar de Consola Gráfica.
- Etiqueta de estado del visor externo.
- Botón "✖ Cerrar visor".

## Etapa 2 — Consolidación de código

- `console_ui_mixin.py`: extraídos los métodos de configuración de consola.
- Renombrado `_sync_vnc_widget` → `_sync_embedded_vnc`.
- `cleanup_backups.py`: utilidad de limpieza de backups.

## Etapa 3 — Fiabilidad

- Watchdog de QEMU (detecta muerte inesperada).
- Backup automático de `run_temp.sh`.
- Validación de red contra lista blanca.
- Rango de puertos SPICE ampliado (5930–6199).
- Aviso de policy kit para pkexec.

## Etapa 4 — Rendimiento

- Caché persistente de sondas del host.
- Throttling de gráficos por foco y pestaña.
- Población diferida del árbol de Passthrough.

## Etapa 5 — Tests

- `test_console_backend.py` (~30 tests).
- `ConsoleSwitchTests` en `test_virtual_machine.py`.
- `run_tests.sh`. Total actual: 106 tests.

## Etapa 6 — UX refinada

- Banner de estado de la consola.
- Checkbox "Pantalla completa" para visores externos.
- Atajo `Ctrl+Alt+C`.
- Tooltips enriquecidos en los combos de consola.
- Detección de `spice-vdagent` en el guest.

## Correcciones puntuales

- Cambio entre VMs con consola embebida: el widget se recrea al cambiar de VM.
- Foco de ventana externa al clic sobre la VM (con `wmctrl`).
- Botones Iniciar/Pausar/Apagar coherentes con el estado.
- Panel de recursos con "Fijar".
- Resumen reorganizado en grilla 2x2 + fila.
- Refresco inmediato al cambiar de VM.