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

## Etapa 8 — Organización (Bloque B completo)

- **#8** Grupos y etiquetas de color por VM (`vm_label_v1`):
  `extra["group"]` + `extra["color"]`, prefijo `[Grupo] ` en la lista
  lateral, fondo con alfa 150, filtro por grupo en el panel izquierdo.
- **#9** Plantillas de VM sin discos (`vm_templates_v1`):
  archivos `.ini` sueltos en `VirtualMachines/_templates/`. Menú
  desplegable en el botón "➕ Nueva VM".
- **#10** Comparar config actual vs defaults del perfil del SO
  (`compare_defaults_v1`): tabla 3 columnas, filas que difieren en
  amarillo, aplicar al seleccionado o a todos.

## Etapa 9 — Snapshots y backup (Bloque C completo)

- **#11** Modo compatibilidad de snapshots (`snapshot_compat_v1`):
  deshabilita VirGL/Venus y passthrough PCI/USB en la VM para
  garantizar savevm. Flag `extra["snapshot_compat"]`.
- **#12** Snapshots automáticos programados (`snapshot_schedule_v1`):
  scheduler central con tick de 60 s. Snapshots solo-disco con
  prefijo `auto_YYYYMMDD_HHMMSS` y retención configurable.
- **#13** Backups programados (`backup_schedule_v1`): pestaña
  "💾 Backups" con destino, frecuencia, retención y backup manual.
- **#14** Clon enlazado (`linked_clone_v1`): backing file QCOW2 con
  ruta relativa (portabilidad de `VirtualMachines/`). MACs e IDs
  regenerados al clonar. Botón "🧬 Desenlazar"
  (`linked_clone_unlink_v1`). Snapshots forzados a solo-disco
  (`linked_clone_snapshot_v1`).

## Etapa 10 — Biblioteca de Medios (Bloque G completo) + reorganización UI

- **#34** Helper `media_library.py` sin PyQt.
- **#35** Pestaña "📚 Medios".
- **#36** `MediaPickerDialog` integrado en Config VM → Almacenamiento
  y en el menú 💿 Medios (con filtro por tipo de dispositivo).
- **#37** Crear medios desde la biblioteca (`qemu-img create`).
- **#38** Detección de huérfanos + columna Estado.
- **#39** Metadatos (notas, tags, color).
- **Escaneo de VMs** (`media_library_vm_scan_v1`): cataloga discos,
  ISOs y disquetes de `VirtualMachines/`, con `used_by` y `roles`.
- **Reorganización UI** (`split_vm_host_config_v1`): nueva pestaña
  "Configuración Host" para lo que toca al sistema anfitrión;
  Passthrough y Carpetas compartidas pasan a secciones del sidebar
  de Configuración VM.
- **Fix de teclado VNC** (`vnc_keysym_fix_v1`): traducción de códigos
  Qt a keysyms X11. TAB, Ctrl, Alt, F-keys y flechas funcionan dentro
  del guest.

## Etapa 11 — macOS: extras, Recovery opcional y UI de gráficos

- **Recovery opcional** (`macos_recovery_optional_v1`): `BaseSystem.img`
  ya no es obligatorio. Solo se exige si hay unidad `source="recovery"`.
- **Discos e ISOs extra** (`macos_extras_v1`): segundo controlador
  AHCI (`sataext`) para no chocar con los tres discos fijos de OSX-KVM.
- **Filtro de rutas reservadas** (`macos_extras_filter_v1`): evita
  abrir dos veces `BaseSystem.img` / `mac_hdd_ng.qcow2` / `OpenCore.qcow2`.
- **CPU model y VRAM respetados** (`macos_cpu_model_v1`,
  `macos_graphics_guard_v1`).
- **MAC única por VM** (`macos_mac_uniqueness_v1`).
- **UI de gráficos coherente** (`macos_graphics_ui_v2`): el combo
  Gráficos centraliza las reglas de bloqueo (snapshot_compat OR VNC
  OR macOS) en `_apply_snapshot_compat_ui`.
- **Ajustes avanzados ocultos** (`advanced_options_hidden_v1`):
  ACPI, APIC, IOMMU y PCIe Root Port dejan de mostrarse.
- **Limpieza**: `macos_storage_cleanup_v1`, `macos_dead_code_v1`.

## Etapa 12 — Selector de tema

- **`theme_selector_v1`**: selector de tema en Configuración Host →
  Apariencia. Sistema / Claro / Oscuro.
- **Mixin nuevo**: `appearance_mixin.py`. Persistencia en
  `QSettings("appearance/theme")`.
- **Estrategia**: forzar el estilo `Fusion` cuando el tema es Claro u
  Oscuro (Fusion respeta `QPalette`; Kvantum y Breeze no). Restaurar el
  estilo original del escritorio al volver a "Sistema".
- **Aplicación antes de crear la `QApplication`** en `__main__`, para
  que la ventana nazca ya pintada con el tema correcto.
- **Diálogo de reinicio opcional** al cambiar el tema en caliente.

## Etapa 13 — Modo presentación

- **`presentation_mode_v1`**: modo presentación con F11. Oculta el
  panel izquierdo, entra en pantalla completa y salta a la Consola
  Gráfica. Botón "🎬 Presentación" en la barra de la consola.
- **`presentation_mode_autohide_v1/v2`**: auto-ocultado de las barras
  superiores. Se muestran cuando el cursor se acerca al borde superior
  y se ocultan al alejarse. Comparación por rectángulos, no por
  `childAt()`, para no ocultarse en los huecos entre botones.

## Correcciones puntuales

- Cambio entre VMs con consola embebida: el widget se recrea al cambiar de VM.
- Foco de ventana externa al clic sobre la VM (con `wmctrl`).
- Botones Iniciar/Pausar/Apagar coherentes con el estado.
- Panel de recursos con "Fijar".
- Resumen reorganizado en grilla 2x2 + fila.
- Refresco inmediato al cambiar de VM.