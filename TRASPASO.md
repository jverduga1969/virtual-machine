# Traspaso de proyecto — Virtual.Machine 38.1

Retomo un proyecto en curso. Léelo entero antes de responder.

## Qué es

Administrador gráfico de VMs QEMU/KVM en Python + PyQt6, tipo VirtualBox.
Soporta Linux, Windows y macOS. Autor: Jimmy Verduga. GPL-3.0-or-later.
Repo: https://github.com/jverduga1969/virtual-machine

## Estructura del proyecto (raíz)

Modulos reales (se importan al arrancar):
- virtual_machine.py       → ventana principal, combos, layout, señales
- workers.py               → InstallWorker (construye comando QEMU)
- console_backend.py       → constantes/helpers VNC/SPICE
- console_ui_mixin.py      → UI consola (protocolo, modo, ayuda contextual)
- vm_lifecycle_mixin.py    → ciclo de vida VM + opciones gráficas
- snapshots_mixin.py       → snapshots completos y solo-disco
- diagnostics_mixin.py     → log, salud VM, dependencias
- performance_mixin.py     → panel de recursos en vivo
- suggestions_mixin.py     → panel de sugerencias contextuales
- install_flow_mixin.py    → flujo de arranque completo (macOS/Win/Linux)
- mac_recovery_mixin.py    → descarga del Recovery de macOS
- guest_integration_mixin.py, network_config_mixin.py, passthrough_mixin.py
- storage_mixin.py, async_ui_mixin.py, snapshots_graph.py, principal_cdrom.py
- network_utils.py, vm_config.py, shared_folders.py, guest_tools_iso.py
- vm_icons.py, spice_widget.py, vnc_widget_centered.py, vnc_focus_filter.py
- x11_keyboard_grab.py, bootstrap_vnc.py, system_deps.py, host_deps.py
- dialogs.py, task_progress.py, iso_sources.py, iso_versions.py

Archivos de contexto:
- SESION.md                → resumen del proyecto y decisiones
- CONVENCIONES.md          → cómo trabajar en este proyecto
- SESSION_LOG.md           → bitácora detallada de fixes aplicados
- TRASPASO.md              → este archivo (se pega en cada chat nuevo)
- scripts/                 → fix_*.py, add_*.py (locales, NO subidos a Git)

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

## Reglas de macOS (no romper)

Modelo de OSX-KVM: tres discos fijos.
  - OpenCoreBoot  → OpenCore.qcow2 (master en OSX-KVM/, snapshot mode)
  - InstallMedia  → BaseSystem.img (RAW, descargado del Recovery)
  - MacHDD        → mac_hdd_ng.qcow2 (QCOW2, 128G, creado por la app)

Instalación de macOS:
  - El flujo de arranque (install_flow_mixin.py) IGNORA storage_devices
    del usuario para elegir el disco del sistema. Usa siempre mac_hdd_ng.qcow2.
  - Si falta BaseSystem.img, descarga el Recovery con un diálogo modal
    bloqueante (_macos_recovery_download_blocking). Al terminar, el arranque
    continúa automáticamente.
  - Cancelar la descarga aborta el arranque sin diálogo de error.

## Bugs resueltos (no reintroducir)

1. Deshabilitación intermitente del combo Gráficos → resuelto derivando
   de combos visibles (combo_console_protocol + combo_console_mode),
   no del checkbox oculto check_vnc_embedded.

2. "Automático" deshabilitado con VNC embebido → quitado de la lista
   incompatible en _on_vnc_embedded_changed.

3. Híbrida 3D fallaba con "Display already specified" → console_backend
   dejó de emitir -display para hybrid_gl.

4. Spicy reaparecía solo cada 30s robando foco → flag _external_viewer_failed.

5. macOS fallaba con "Image is not in qcow2 format" → install_flow_mixin.py
   fuerza mac_hdd_ng.qcow2 como disco del sistema, no BaseSystem.img.

6. Descarga del Recovery bloqueaba al usuario pidiendo pulsar Iniciar dos
   veces → ahora es bloqueante con diálogo modal y continúa sola.

7. install_flow_mixin.py no estaba en GitHub → la regla 'install_*.py' del
   .gitignore lo capturaba. Añadidas excepciones al final del .gitignore.

## Convenciones

- Comentarios/docstrings en español. Código en inglés/spanglish.
- Mensajes consola: "==>" pasos, "[AVISO]" avisos, "[ERROR]" errores, "✓" OK.
- Scripts de fix: idempotentes, con backup (.bak_before_<tag>),
  verificación de sintaxis antes de escribir, salida con colores.
- Backups nunca se borran.
- Los scripts de fix viven en scripts/ y NO se suben a Git.

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
5 modos de consola, snapshots, passthrough PCI/VFIO y USB, carpetas
compartidas VirtioFS/9p/SMB, Guest Agent, panel de recursos, sugerencias.
La app arranca macOS con Recovery descargándose on-demand.

Pendientes menores conocidos:
- Ninguno crítico.

## Sobre el .gitignore (leer si se añade un archivo nuevo)

El .gitignore tiene muchos patrones wildcard peligrosos: install_*.py,
fix_*.py, add_*.py, refactor_*.py, rename_*.py, cleanup_*.py, probe_*.py,
integrate_*.py, switch_*.py, snapshot_*.py, tune_*.py, etc.

Cada vez que se cree un archivo REAL del proyecto con alguno de esos
prefijos, comprobar:
  git check-ignore -v archivo.py
Si sale una regla, añadir excepción al final del .gitignore:
  !archivo.py

Y revisar SIEMPRE con:
  git status --ignored --short | grep '^!!' | grep '.py$'
que ningún archivo real quede atrapado.

## Cómo trabajar conmigo

1. Si te pido algo, revisa primero los archivos relevantes.
2. Para cambios en varios archivos, dame scripts .py idempotentes que
   yo pegue en la terminal con heredoc (cat > archivo.py << 'PYEOF').
3. Nunca modifiques sin backup ni verificación de sintaxis.
4. Si el chat se está llenando, pídeme un resumen de traspaso y avísame.

Pregúntame qué quiero hacer hoy.
