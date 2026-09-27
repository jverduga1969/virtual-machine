# Sesión actual — Virtual.Machine 38.1

## Objetivo del proyecto

Administrador gráfico de máquinas virtuales QEMU/KVM escrito en Python
con PyQt6. Gestiona VMs Linux, Windows, macOS y Android con interfaz
tipo VirtualBox: lista lateral, pestañas de configuración, consola
embebida (VNC/SPICE), snapshots, passthrough de hardware PCI/USB,
carpetas compartidas, Guest Tools y notas contextuales por SO.

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
- workers.py                → InstallWorker (construye el comando QEMU)
- console_backend.py        → constantes y helpers de VNC/SPICE
- console_ui_mixin.py       → UI de la consola (protocolo, modo, ayuda)
- vm_lifecycle_mixin.py     → ciclo de vida de la VM + notas por SO
- snapshots_mixin.py        → snapshots
- diagnostics_mixin.py      → log, salud de la VM, dependencias
- performance_mixin.py      → panel de recursos en vivo
- suggestions_mixin.py      → panel de sugerencias
- host_deps.py              → detección de capacidades del host
- async_ui_mixin.py         → helper run_async
- snapshots_graph.py        → organigrama de snapshots
- principal_cdrom.py        → lógica del CD/DVD "Principal"
- install_flow_mixin.py     → flujo de arranque por SO (Linux/Win/macOS/Android)

Scripts de fix (en scripts/ y en raíz, NO subidos a Git):
- fix_graphics_toggle.py
- fix_auto_graphics_label.py
- add_hybrid_gl_mode.py
- fix_hybrid_gl_workers.py
- fix_spice_popup.py
- fix_os_notes_generic.py
- fix_medium_final.py
- fix_version_iso_visible_linux.py
- ... (ver SESSION_LOG.md)

Backups generados: *.bak_before_<tag>

## Qué funciona

- Crear/abrir/editar/eliminar VMs Linux, Windows, macOS y Android
- Modo Híbrida 3D (VNC embebido 2D + ventana GL de QEMU con VirGL/Venus)
- Los 4 modos de consola: Embebida, Externa, Nativa QEMU, Híbrida 2D,
  Híbrida 3D
- Snapshots completos (RAM + dispositivos) y solo de discos
- Panel de recursos en vivo (CPU/RAM/disco/red)
- Sugerencias contextuales por VM
- Passthrough PCI/VFIO y USB hotplug
- Carpetas compartidas VirtioFS/9p/SMB
- Guest Agent y detección de spice-vdagent
- Notas contextuales por SO (Linux/Windows/macOS/Android)
- Opción "Automático" en gráficos que muestra el target real

## Decisiones importantes

1. **"Automático" nunca se deshabilita**. Su texto dice qué opción usará:
   - Sin VNC embebido → VirGL si el host lo soporta, si no VirtIO-GPU 2D
   - Con VNC embebido → VirtIO-GPU 2D (VNC no soporta OpenGL)
   - Windows → VGA estándar
   - macOS → VGA de OSX-KVM
   - Android → Red Hat QXL 2D

2. **VNC embebido / híbrido 2D** deshabilita VirGL y Venus.

3. **Híbrida 3D** permite VirGL/Venus: el 3D va por la ventana GL.

4. **console_backend.py NO emite -display** en hybrid_gl. Solo workers.

5. **El visor externo (spicy/remote-viewer) NO se relanza** si muere.

6. **Modelo de consola**: protocolo (vnc/spice) × modo
   (embedded/external/native/hybrid/hybrid_gl).

7. **Comentarios y docstrings en español**. Mensajes:
   "==>" pasos, "[AVISO]" avisos, "[ERROR]" errores, "✓" OK.

8. **Unidad CD/DVD "Principal" = única fuente de verdad** del medio de
   instalación. Ningún otro widget la duplica.

9. **Caja de notas contextuales por SO** debajo de la fila superior.
   Diccionario _OS_NOTES en vm_lifecycle_mixin.py.

10. **Android usa QXL 2D por defecto**. VirtIO-GPU no arranca
    Android-x86 9.0 (kernel 4.9).

## Errores resueltos en esta sesión (2026-09-27)

1. Android: "Bus 'ide.2' not found" con chipset i440FX → degradación
   automática a IDE heredado.

2. Android: shell de rescate "Detecting Android-x86..." → uso de QXL
   2D en lugar de VirtIO-GPU.

3. Duplicación de widgets de medio (input + botón carpeta en la fila
   superior y en páginas de Android/macOS) → eliminados.

4. Popup flotante de "Versión ISO" → se restauró al layout y luego se
   ocultó permanentemente (solo queda el combo, y solo en Linux).

5. _save_hardware_lists fusionado dentro de _persist_android_iso por
   un script mal anclado → separados.

6. Referencias residuales a métodos eliminados (_update_android_warning_visibility)
   rompían el arranque → limpiadas.

## Próximos pasos posibles

- Probar Bliss OS genérico (v15+) en una VM aparte con 8 GB RAM y
  4 núcleos, chipset Q35.
- Cazar el bug de la ventana nativa de QEMU que aparece a la vez que
  el widget VNC embebido (reportado, sin reproducir todavía).
- Añadir tests unitarios para _auto_graphics_effective_label y para
  _chipset_is_q35.
- Añadir soporte de Android en las carpetas compartidas (imposible sin
  módulos 9p/virtiofs en el kernel; quizá vía adb push documentado).

## Cómo arrancar un chat nuevo

1. Pega TRASPASO.md como primer mensaje.
2. Pega CONVENCIONES.md como segundo mensaje.
3. Di en qué quieres trabajar.

Con esos dos archivos se retoma el hilo al instante.
