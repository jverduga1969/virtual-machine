# Sesión actual — Virtual.Machine 38.1

## Objetivo del proyecto

Administrador gráfico de máquinas virtuales QEMU/KVM escrito en Python con PyQt6.
Gestiona VMs Linux, Windows y macOS con interfaz tipo VirtualBox: lista lateral,
pestañas de configuración, consola embebida (VNC/SPICE), snapshots, passthrough
de hardware PCI/USB, carpetas compartidas y Guest Tools.

Autor: Jimmy Verduga. Licencia: GPL-3.0-or-later.

## Tecnologías

- Python 3.12
- PyQt6 (Qt6)
- QEMU/KVM, virtiofsd, swtpm, OVMF
- Arquitectura modular: mixins para separar responsabilidades
- Scripts de fix idempotentes con backup automático

## Estructura relevante

Archivos principales:
- virtual_machine.py        → ventana principal, combos, layout, señales
- workers.py                → InstallWorker (construye el comando QEMU), snapshots
- console_backend.py        → constantes y helpers de VNC/SPICE
- console_ui_mixin.py       → UI de la consola (protocolo, modo, ayuda)
- vm_lifecycle_mixin.py     → ciclo de vida de la VM + opciones gráficas
- snapshots_mixin.py        → snapshots
- diagnostics_mixin.py      → log, salud de la VM, dependencias
- performance_mixin.py      → panel de recursos en vivo
- suggestions_mixin.py      → panel de sugerencias
- host_deps.py              → detección de capacidades del host (GPU, VirGL, etc.)
- async_ui_mixin.py         → helper run_async para tareas largas
- snapshots_graph.py        → organigrama de snapshots
- principal_cdrom.py        → lógica del CD/DVD "Principal"

Scripts de fix (en scripts/):
- fix_graphics_toggle.py        → arregla deshabilitación intermitente de VirGL/Venus
- fix_auto_graphics_label.py    → "Automático" nunca se deshabilita; su texto dice el target real
- add_hybrid_gl_mode.py         → añade modo "Híbrida 3D" (VNC 2D + ventana GL de QEMU)
- fix_hybrid_gl_workers.py      → elimina -display duplicado en modo Híbrida 3D
- fix_spice_popup.py            → evita relanzamiento automático del visor externo

Backups generados: *.bak_before_<tag>

## Qué funciona

- Crear/abrir/editar/eliminar VMs Linux, Windows y macOS
- Modo Híbrida 3D (VNC embebido 2D + ventana GL de QEMU con VirGL/Venus)
- Los 4 modos de consola: Embebida, Externa, Nativa QEMU, Híbrida 2D, Híbrida 3D
- Snapshots completos (RAM + dispositivos) y solo de discos
- Panel de recursos en vivo (CPU/RAM/disco/red)
- Sugerencias contextuales por VM
- Passthrough PCI/VFIO y USB hotplug
- Carpetas compartidas VirtioFS/9p/SMB
- Guest Agent y detección de spice-vdagent
- Opción "Automático" en gráficos que muestra el target real

## Decisiones importantes

1. **"Automático" nunca se deshabilita**. Su texto dice qué opción usará:
   - Sin VNC embebido → VirGL si el host lo soporta, si no VirtIO-GPU 2D
   - Con VNC embebido → VirtIO-GPU 2D (VNC no soporta OpenGL)
   - Windows → VGA estándar
   - macOS → VGA de OSX-KVM

2. **VNC embebido / híbrido 2D** deshabilita VirGL y Venus (VNC no soporta GL).

3. **Híbrida 3D** permite VirGL/Venus: el 3D va por la ventana GL de QEMU,
   el widget embebido muestra la vista 2D.

4. **`console_backend.py` NO emite `-display`** en hybrid_gl. Solo expone
   el socket VNC. El flag `-display gtk,gl=on` lo aporta `workers._graphics_args()`.
   Si los dos emiten `-display`, QEMU falla con "Display already specified".

5. **El visor externo (spicy/remote-viewer) NO se relanza automáticamente**
   si muere. Antes lo hacía tras 30s, robando el foco. Ahora se marca la VM
   en `_external_viewer_failed` y se espera acción explícita del usuario
   (botón "Abrir en ventana externa").

6. **Modelo de consola**: protocolo (vnc/spice) × modo
   (embedded/external/native/hybrid/hybrid_gl).

7. **Comentarios y docstrings en español**. Mensajes en consola:
   "==>" pasos, "[AVISO]" avisos, "[ERROR]" errores, "✓" OK.

## Errores resueltos en esta sesión

1. **Deshabilitación intermitente de VirGL/Venus/Auto en combo Gráficos**:
   - Causa: `_on_vnc_embedded_changed` leía el estado de un checkbox oculto
     que se movía con `blockSignals`, así que nadie reevaluaba el combo al
     cambiar de VM.
   - Fix: derivar de los combos visibles (`combo_console_protocol` + `combo_console_mode`).

2. **"Automático" se deshabilitaba con VNC embebido**:
   - Causa: estaba en la lista de incompatibles.
   - Fix: quitarlo de esa lista y actualizar su texto para decir el target real.

3. **Modo Híbrida 3D fallaba con "Display already specified"**:
   - Causa: `console_backend` y `workers` emitían ambos `-display`.
   - Fix: `console_backend` deja de emitirlo; solo `workers` lo hace.

4. **Spicy reaparecía solo cada 30s robando el foco**:
   - Causa: `_sync_external_viewer` relanzaba tras morir.
   - Fix: marcarlo como fallido y no relanzar automáticamente.

## Próximos pasos posibles

- Investigar por qué spicy muere solo (posible bug de spice-gtk con
  cambios de resolución o reconexión del vdagent).
- Añadir híbrida SDL como alternativa si GTK+GL falla en algún host.
- Migrar la lógica gráfica de `workers.py` a un módulo dedicado
  (graphics_backend.py) para reducir el tamaño del archivo.
- Añadir tests unitarios para `_auto_graphics_effective_label`.

## Cómo arrancar un chat nuevo

1. Pega este archivo como primer mensaje.
2. Pega `CONVENCIONES.md` como segundo mensaje.
3. Di en qué quieres trabajar.

Con esos dos archivos se retoma el hilo al instante.
