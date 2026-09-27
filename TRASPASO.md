# Traspaso de proyecto — Virtual.Machine 38.1

Retomo un proyecto en curso. Léelo entero antes de responder.

## Qué es

Administrador gráfico de VMs QEMU/KVM en Python + PyQt6, tipo VirtualBox.
Soporta Linux, Windows y macOS. Autor: Jimmy Verduga. GPL-3.0-or-later.

## Estructura

Raíz del proyecto:
- virtual_machine.py       → ventana principal, combos, layout, señales
- workers.py               → InstallWorker (construye comando QEMU), snapshots
- console_backend.py       → constantes/helpers VNC/SPICE
- console_ui_mixin.py      → UI consola (protocolo, modo, ayuda contextual)
- vm_lifecycle_mixin.py    → ciclo de vida VM + opciones gráficas
- snapshots_mixin.py       → snapshots completos y solo-disco
- diagnostics_mixin.py     → log, salud VM, dependencias
- performance_mixin.py     → panel de recursos en vivo
- suggestions_mixin.py     → panel de sugerencias contextuales
- host_deps.py             → detección GPU/OpenGL/Vulkan/VirGL/KVM/OVMF
- async_ui_mixin.py        → helper run_async
- snapshots_graph.py       → organigrama de snapshots
- principal_cdrom.py       → lógica del CD/DVD "Principal"
- network_utils.py, vm_config.py, shared_folders.py, guest_tools_iso.py
- vm_icons.py, spice_widget.py, vnc_widget.py, vnc_focus_filter.py
- x11_keyboard_grab.py, bootstrap_vnc.py, system_deps.py

Archivos de contexto (leer primero si existen):
- SESION.md                → resumen de la sesión anterior
- CONVENCIONES.md          → cómo trabajar en este proyecto
- SESSION_LOG.md           → bitácora de fixes aplicados
- scripts/                 → fix_*.py, add_*.py (idempotentes, con backup)

## Arquitectura

- Mixins por área. Sin clases monolíticas.
- Mixins sin __init__: asumen que self ya tiene widgets/atributos.
- Helpers puros (sin PyQt) en módulos sueltos.
- Comentarios y docstrings en español.
- Marcadores de decisión interna buscables con grep (ej:
  nvme_default_all_modern_os, cdrom_sata_ahci_v1).

## Modelo de consola (crítico)

- Protocolo: PROTOCOL_VNC / PROTOCOL_SPICE.
- Modo:
  - MODE_EMBEDDED   → widget dentro de la app
  - MODE_EXTERNAL   → visor del sistema (spicy/remote-viewer/vncviewer)
  - MODE_NATIVE     → ventana propia de QEMU (GTK/SDL)
  - MODE_HYBRID     → VNC embebido + SPICE externo (2D + 2D)
  - MODE_HYBRID_GL  → VNC embebido (2D) + ventana GL propia de QEMU (3D)

## Reglas de gráficos (no romper)

1. "Automático" NUNCA se deshabilita. Su texto se actualiza con
   _refresh_auto_graphics_label() para decir el target real:
   - Linux sin VNC embebido → VirGL si el host lo soporta, si no VirtIO-GPU 2D
   - Linux con VNC embebido → VirtIO-GPU 2D
   - Windows → VGA estándar
   - macOS → VGA de OSX-KVM

2. VNC embebido / Híbrida 2D → prohibido VirGL y Venus.
   Híbrida 3D → permitido VirGL y Venus (van por ventana GL de QEMU).

3. Solo workers._graphics_args() emite el flag -display. Nadie más.
   Si console_backend también lo emite → QEMU falla con "Display already specified".

4. El visor externo (spicy/remote-viewer) NO se relanza automáticamente
   si muere. Se marca la VM en self._external_viewer_failed y se espera
   acción explícita del usuario (botón "Abrir en ventana externa").

## Bugs resueltos (no reintroducir)

1. Deshabilitación intermitente del combo Gráficos → resuelto derivando
   de combos visibles (combo_console_protocol + combo_console_mode),
   no del checkbox oculto check_vnc_embedded.

2. "Automático" deshabilitado con VNC embebido → quitado de la lista
   incompatible en _on_vnc_embedded_changed.

3. Híbrida 3D fallaba con "Display already specified" → console_backend
   dejó de emitir -display para hybrid_gl.

4. Spicy reaparecía solo cada 30s robando foco → flag _external_viewer_failed.

## Convenciones

- Comentarios/docstrings en español. Código en inglés/spanglish.
- Mensajes consola: "==>" pasos, "[AVISO]" avisos, "[ERROR]" errores, "✓" OK.
- Scripts de fix: idempotentes, con backup (.bak_before_<tag>),
  verificación de sintaxis antes de escribir, salida con colores.
- Backups nunca se borran.

## Cómo se construye el comando QEMU

En InstallWorker._run_impl():
1. Detectar capacidades del host.
2. Construir script bash en script_content línea a línea.
3. Insertar args auxiliares (VirtioFS, QGA, consola) juntos antes de
   -qmp con _insert_pre_qmp_args().
4. Los args gráficos (-display, -device virtio-vga*) salen SOLO de
   _graphics_args().

## Estado actual

Todo funciona: crear/abrir/editar/eliminar VMs Linux/Windows/macOS,
4+1 modos de consola, snapshots, passthrough PCI/VFIO y USB, carpetas
compartidas VirtioFS/9p/SMB, Guest Agent, panel de recursos, sugerencias.

## Cómo trabajar conmigo

1. Si te pido algo, revisa primero los archivos relevantes.
2. Para cambios en varios archivos, dáme scripts .py idempotentes que
   yo pegue en la terminal con heredoc (cat > archivo.py << 'EOF').
3. Nunca modifiques sin backup ni verificación de sintaxis.
4. Si el chat se está llenando, pídeme un resumen de traspaso y avísame.

Pregúntame qué quiero hacer hoy.
