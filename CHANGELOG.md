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

## Etapa 7 — Integración macOS y diagnóstico

- Fix del cursor/teclado en macOS: se usa EHCI (`usb-ehci` + `usb-kbd` +
  `usb-tablet` sobre `ehci.0`) con `ICH9-LPC.acpi-pci-hotplug-with-bridge-
  support=off` para High Sierra y compatibles. El controlador XHCI de QEMU
  no se inicializa correctamente en esas versiones (cursor quieto en (0,0),
  teclado muerto dentro de macOS aunque OpenCore los detecte).
- Combo "Dispositivo de señalización" en Configuración → Dispositivos
  (`auto` / `usb-tablet` / `usb-mouse` / `usb-kbd-tablet` / `virtio-tablet`
  / `ps2` / `none`), persistido en `extra[pointer_device]`. Otros SO en
  `auto` siguen con PS/2 de QEMU sin cambios.
- Nuevo panel de semáforos de salud (`health_dashboard_mixin.py`): botón
  🚦 en Consola de Progreso con cinco filas —Red de la VM, Internet del
  host, Audio, Pantalla y Guest Agent— refrescadas cada 4 s. La red se
  mide con `query-netdev` de QMP y fallback a `ss -tn` sin sudo.
- Fix del crash del widget VNC: `BrokenPipeError` al mover el ratón cuando
  el servidor ya había cerrado la conexión abortaba la aplicación. Ahora
  se captura, se cierra la conexión y se marca el cliente como desconectado.
- NIC de macOS según versión: `vmxnet3` para High Sierra (10.13) y Mojave
  (10.14), `virtio-net-pci` para Catalina (10.15) y posteriores. Los dos
  primeros no traen driver virtio-net nativo en el instalador y quedaban
  sin IP ("No route to host").
- `dns=10.0.2.3` explícito en el `-netdev user` de slirp: algunos guests
  ignoran el DNS servido por DHCP interno y quedaban sin resolver nombres
  aunque la red funcionara.
- Passthrough USB: aviso (no bloqueante) si el dispositivo seleccionado
  parece ser el teclado o el ratón del host, con recordatorio de Ctrl+Alt+F2.
- `.gitignore`: los archivos de contexto (TRASPASO, SESION, SESSION_LOG,
  CONVENCIONES) dejan de subirse al repositorio público.

## Correcciones puntuales

- Cambio entre VMs con consola embebida: el widget se recrea al cambiar de VM.
- Foco de ventana externa al clic sobre la VM (con `wmctrl`).
- Botones Iniciar/Pausar/Apagar coherentes con el estado.
- Panel de recursos con "Fijar".
- Resumen reorganizado en grilla 2x2 + fila.
- Refresco inmediato al cambiar de VM.