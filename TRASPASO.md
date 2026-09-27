# Traspaso de proyecto — Virtual.Machine 38.1

Retomo un proyecto en curso. Léelo entero antes de responder.

## Qué es

Administrador gráfico de VMs QEMU/KVM en Python + PyQt6, tipo VirtualBox.
Soporta Linux, Windows, macOS y Android. Autor: Jimmy Verduga.
GPL-3.0-or-later.
Repo: https://github.com/jverduga1969/virtual-machine

## Estructura del proyecto (raíz)

Módulos reales (se importan al arrancar):
- virtual_machine.py       → ventana principal, combos, layout, señales
- workers.py               → InstallWorker (construye comando QEMU)
- console_backend.py       → constantes/helpers VNC/SPICE
- console_ui_mixin.py      → UI consola (protocolo, modo, ayuda contextual)
- vm_lifecycle_mixin.py    → ciclo de vida VM + opciones gráficas + notas por SO
- snapshots_mixin.py       → snapshots completos y solo-disco
- diagnostics_mixin.py     → log, salud VM, dependencias
- performance_mixin.py     → panel de recursos en vivo
- suggestions_mixin.py     → panel de sugerencias contextuales
- install_flow_mixin.py    → flujo de arranque completo (macOS/Win/Linux/Android)
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
   - Android → Red Hat QXL 2D (ver reglas de Android más abajo)

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
  - La fuente de instalación se configura desde la unidad CD/DVD "Principal"
    (Configuración → Almacenamiento), eligiendo "System Recovery de macOS"
    o "Usar ISO/IMG/DMG existente". Ya NO hay radios/input en la parte
    superior de la ventana (se eliminaron por duplicación).
  - Si una VM macOS no tiene ningún medio configurado, al pulsar Iniciar
    se le auto-crea la unidad Principal con source="recovery".

## Reglas de Android (NUEVO — añadido en la sesión 2026-09-27)

Android se soporta como un SO de primera clase mediante Android-x86 o
Bliss OS, con la ISO aportada por el usuario (no hay descarga automática:
los mirrors cambian de ubicación con frecuencia).

- Firmware BIOS (tradicional) por defecto; chipset Q35.
- Disco SATA/AHCI si el chipset es Q35; si es i440FX (pc), se degrada
  a IDE heredado (ver _chipset_is_q35 en workers.py). Sin esta
  degradación QEMU falla con "Bus 'ide.2' not found".
- Gráficos: **Red Hat QXL 2D** para "Automático". VirtIO-GPU NO sirve
  porque Android-x86 9.0 (kernel 4.9) no trae driver VirtIO-GPU y cae a
  un shell de rescate ("Detecting Android-x86... found at /dev/sr0").
  Bliss OS con kernel 5.15+ sí soporta VirtIO-GPU, pero no es el default.
- Red: e1000 por defecto (compatible sin drivers extra en el guest).
- La ISO se elige en Configuración → Almacenamiento → 📀 CD/DVD
  (unidad "Principal"). La parte superior de la ventana NO tiene input
  de ISO para Android (se eliminó por duplicación).
- Carpetas compartidas (9p/VirtioFS), QEMU Guest Agent y clipboard
  bidireccional NO funcionan en Android: los kernels de Android-x86 /
  Bliss OS no incluyen esos módulos. La app muestra un aviso explicando
  esto en la caja de notas contextuales.
- Bliss OS es más moderno (Android 12/13) pero exige ≥8 GB RAM,
  4 núcleos y chipset Q35. La variante «Bliss-Surface» no arranca bajo
  QEMU. La caja de notas lo advierte.

## Regla del medio de instalación (NUEVO)

La unidad CD/DVD "Principal" (Configuración → Almacenamiento) es la
ÚNICA fuente de verdad para el medio de instalación, en TODOS los SO.

- La parte superior de la ventana muestra, como máximo, el combo
  "Versión ISO" (solo Linux) para elegir qué ISO descargar y en qué
  versión. NO hay inputs ni botones de carpeta que dupliquen lo que
  se configura en Almacenamiento.
- Si el usuario elige "Ninguna (elegir mi propia ISO)" en ese combo,
  se abre automáticamente el diálogo de archivo. No hay botón 📁.
- Las páginas de Android y macOS en el stack solo tienen la caja de
  notas contextuales. El botón "Configurar medio en Almacenamiento"
  se eliminó por redundante.

## Notas contextuales por SO (NUEVO)

Debajo de la fila Nombre/Plataforma/Versión de SO aparece una caja
informativa (ancho completo, altura adaptable) cuyo texto depende de
la plataforma:

- vm_lifecycle_mixin.py: diccionario _OS_NOTES (una entrada por SO).
- virtual_machine.py: crea self.os_notes_widget (QFrame + título +
  cuerpo) y conecta combo_main_os.currentIndexChanged a
  _update_os_notes_visibility.
- El texto enumera qué funciona, qué no y qué ISO se recomienda.
- Fondo azul claro, enlaces clicables (se abren con xdg-open).
- Editar un texto = editar _OS_NOTES, nada más.

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

8. Android fallaba con "Bus 'ide.2' not found" → _chipset_is_q35() en
   workers.py degrada SATA/AHCI a IDE heredado si el chipset es i440FX.

9. Android se quedaba en "Detecting Android-x86... found at /dev/sr0"
   (shell de rescate) → Android-x86 9.0 (kernel 4.9) no tiene driver
   VirtIO-GPU. Solución: "Automático" para Android usa QXL 2D.

10. Dos widgets de carpeta 📁 en la parte superior (uno en la fila de
    SO y otro en la página de Android/macOS) → se eliminaron los de la
    página; el botón de "Versión ISO" (solo Linux) queda siempre oculto.

11. Cambios de medio en Almacenamiento no se reflejaban en la fila de
    SO (y viceversa) → unificación: la unidad Principal es la única
    fuente de verdad. Los widgets duplicados se eliminaron.

12. vm_config.ini guardaba os_profile con el texto del SO anterior
    ("Android — Linux Mint") → cosmético, se regenera al abrir+guardar.

13. _save_hardware_lists quedó fusionado dentro de _persist_android_iso
    por un script mal anclado (AttributeError al pulsar Guardar en Red).
    Se separaron los dos métodos.

## Convenciones

- Comentarios/docstrings en español. Código en inglés/spanglish.
- Mensajes consola: "==>" pasos, "[AVISO]" avisos, "[ERROR]" errores, "✓" OK.
- Scripts de fix: idempotentes, con backup (.bak_before_<tag>),
  verificación de sintaxis antes de escribir, salida con colores.
- Backups nunca se borran.
- Los scripts de fix viven en scripts/ (o en la raíz para los one-shot)
  y NO se suben a Git (patrones del .gitignore los capturan).

## Cómo se construye el comando QEMU

En InstallWorker._run_impl():
1. Detectar capacidades del host.
2. Construir script bash en script_content línea a línea.
3. Insertar args auxiliares (VirtioFS, QGA, consola) juntos antes de
   -qmp con _insert_pre_qmp_args().
4. Los args gráficos (-display, -device virtio-vga*) salen SOLO de
   _graphics_args().
5. Los discos se resuelven con _resolve_disk_bus_for_os(), que traduce
   el "device" lógico (sata/nvme/floppy) al bus QEMU adecuado según el
   SO invitado. Para Android: sata_ahci si Q35, ide si i440FX.

## Estado actual

Todo funciona: crear/abrir/editar/eliminar VMs Linux/Windows/macOS/Android,
5 modos de consola, snapshots, passthrough PCI/VFIO y USB, carpetas
compartidas VirtioFS/9p/SMB, Guest Agent, panel de recursos, sugerencias,
notas contextuales por SO.

Android:
  - Android-x86 9.0 arranca con QXL (probado por el usuario).
  - Bliss OS v14.10.3 (variante Surface) no arranca bajo QEMU: es la
    variante incorrecta. La app lo advierte en la caja de notas.
  - Bliss OS genérico (v15+) aún sin probar: pendiente por el usuario.

Pendientes menores conocidos:
  - Nirvanilla, pero ninguno crítico.

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

Excepciones ya presentes en el .gitignore:
  !add_license_headers.py
  !install_flow_mixin.py
  !*_mixin.py
  scripts/refactor_console_to_mixin.py

## Sobre Git — qué sube y qué no

Archivos REALES del proyecto (SÍ a Git):
  virtual_machine.py, workers.py, vm_config.py, dialogs.py,
  install_flow_mixin.py, vm_lifecycle_mixin.py, console_ui_mixin.py,
  console_backend.py, storage_mixin.py, snapshots_mixin.py,
  diagnostics_mixin.py, performance_mixin.py, suggestions_mixin.py,
  mac_recovery_mixin.py, guest_integration_mixin.py,
  network_config_mixin.py, passthrough_mixin.py, async_ui_mixin.py,
  snapshots_graph.py, principal_cdrom.py, network_utils.py,
  shared_folders.py, guest_tools_iso.py, vm_icons.py, spice_widget.py,
  vnc_widget_centered.py, vnc_focus_filter.py, x11_keyboard_grab.py,
  bootstrap_vnc.py, system_deps.py, host_deps.py, task_progress.py,
  iso_sources.py, iso_versions.py.

Archivos de contexto (SÍ a Git):
  SESION.md, CONVENCIONES.md, SESSION_LOG.md, TRASPASO.md.

Scripts de fix / one-shot (NO a Git, .gitignore los captura):
  fix_*.py, add_*.py, install_*.py, refactor_*.py, rename_*.py,
  cleanup_*.py, probe_*.py, move_*.py, polish_*.py, integrate_*.py,
  switch_*.py, shorten_*.py, snapshot_*.py, stack_*.py, tune_*.py,
  reorder_*.py, reorganize_*.py, implement_*.py, enhance_*.py,
  export_*.py, help_*.py, improve_*.py, apply_*.py, setup_console_*.py.
  Incluso scripts/fix_*.py.

Backups (NO a Git, .gitignore los captura):
  *.bak, *.bak_before_*, *.bak_after_*.

VMs y discos (NO a Git):
  VirtualMachines/, OSX-KVM/, *.qcow2, *.img, *.iso, etc.

Comandos útiles antes de hacer commit:
  git status --short                              # qué se subirá
  git status --ignored --short | grep '^!!'       # qué se ignora
  git check-ignore -v archivo.py                  # por qué se ignora

Si un archivo real queda atrapado por un patrón, añadir excepción al
final del .gitignore con !archivo.py y verificar con git check-ignore.

## Cómo trabajar conmigo

1. Si te pido algo, revisa primero los archivos relevantes.
2. Para cambios en varios archivos, dame scripts .py idempotentes que
   yo pegue en la terminal con heredoc (cat > archivo.py << 'PYEOF').
3. Nunca modifiques sin backup ni verificación de sintaxis.
4. Si el chat se está llenando, pídeme un resumen de traspaso y avísame.
5. Verifica SIEMPRE con compile() antes de escribir y con
   python3 -c "import ast; ast.parse(open(f).read())" después.
6. Si un script no encuentra su ancla, para y pide ver el archivo real
   antes de seguir tocando.

Pregúntame qué quiero hacer hoy.
