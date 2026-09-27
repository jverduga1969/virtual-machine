# Bitácora de sesiones — Virtual.Machine

Formato: cada entrada tiene fecha, tema, archivos tocados, script aplicado.
Se escribe en orden inverso (más reciente arriba).

---

## 2026-09-27 — Fix del visor externo (spicy)

### Problema
La ventana del visor externo SPICE se relanzaba sola ~30s después de morir,
robando el foco y apareciendo centrada. Se repetía 2 veces seguidas.

### Causa
`_sync_external_viewer` relanzaba el visor tras la ventana de gracia de 30s.
Además, el botón "Abrir en ventana externa" no registraba el Popen, así que
`_sync_external_viewer` podía lanzar un duplicado.

### Fix
- `vm_lifecycle_mixin.py`: nuevo flag `_external_viewer_failed` (set de vm_dir).
  Si el visor muere, se marca la VM y no se relanza. Se limpia al apagar la VM.
- `console_ui_mixin.py`: `_launch_external_console` limpia el flag (permite
  relanzar cuando el usuario lo pide) y registra el proceso en
  `_external_viewers`.

### Archivos tocados
- vm_lifecycle_mixin.py
- console_ui_mixin.py

### Script
scripts/fix_spice_popup.py

### Backups
- vm_lifecycle_mixin.py.bak_before_fix_spice_popup
- console_ui_mixin.py.bak_before_fix_spice_popup

---

## 2026-09-27 — Modo "Híbrida 3D" + cierre de workers

### Problema
El usuario pidió: renombrar "Híbrida" → "Híbrida 2D" y añadir "Híbrida 3D"
(VNC embebido 2D + ventana GL de QEMU con VirGL/Venus).

Tras el cambio, QEMU fallaba al arrancar con "Display already specified".

### Causa
`console_backend.qemu_console_args` y `workers._graphics_args` emitían
ambos `-display`. QEMU solo acepta uno.

### Fix
- `console_backend.py`: en hybrid_gl, solo emite `-vnc unix:...` sin `-display`.
- `workers.py`: importa `MODE_HYBRID_GL`, detecta `_is_hybrid_gl` y loguea un
  mensaje informativo. El flag `-display gtk,gl=on` lo aporta solo
  `_graphics_args()`.

### Archivos tocados
- console_backend.py
- console_ui_mixin.py
- virtual_machine.py
- vm_lifecycle_mixin.py
- workers.py

### Scripts
- scripts/add_hybrid_gl_mode.py
- scripts/fix_hybrid_gl_workers.py

### Backups
- *.bak_before_add_hybrid_gl
- *.bak_before_fix_hybrid_gl_workers

---

## 2026-09-27 — "Automático" nunca se deshabilita

### Problema
La opción "Automático" del combo Gráficos se deshabilitaba con VNC embebido
y confundía al usuario, que no sabía qué opción se iba a usar realmente.

### Fix
- Quitada "auto" de la lista de incompatibles en `_on_vnc_embedded_changed`.
- Añadidos `_auto_graphics_effective_label()` y `_refresh_auto_graphics_label()`
  que actualizan el texto del item para decir el target real:
  - Linux sin VNC embebido → "→ VirtIO-GPU + VirGL 3D" (si el host lo soporta)
  - Linux con VNC embebido → "→ VirtIO-GPU 2D (VNC no soporta 3D)"
  - Windows → "→ VGA estándar (QEMU -vga std)"
  - macOS → "→ VGA de OSX-KVM (VGA virtual)"

### Archivos tocados
- vm_lifecycle_mixin.py

### Script
scripts/fix_auto_graphics_label.py

### Backups
- vm_lifecycle_mixin.py.bak_before_auto_graphics_label

---

## 2026-09-27 — Fix de deshabilitación intermitente del combo Gráficos

### Problema
Al abrir distintas VMs, VirGL / Venus / Auto quedaban deshabilitados o
habilitados de forma inconsistente, sin relación con VNC o SPICE.

### Causa
`_on_vnc_embedded_changed` leía el estado de un checkbox OCULTO
(`check_vnc_embedded`) que se movía con `blockSignals` desde varios sitios.
Al moverse sin señales, nadie reevaluaba el combo Gráficos.

### Fix
- `_on_vnc_embedded_changed` deriva el estado de los combos VISIBLES
  (`combo_console_protocol` + `combo_console_mode`).
- `_apply_console_choice_to_ui` llama a `_on_vnc_embedded_changed` al final
  para que el combo se reevalúe cada vez que se abre una VM.
- `open_vm` deja de mover el checkbox legacy a mano.

### Archivos tocados
- vm_lifecycle_mixin.py
- console_ui_mixin.py

### Script
scripts/fix_graphics_toggle.py

### Backups
- vm_lifecycle_mixin.py.bak_before_graphics_toggle_A
- vm_lifecycle_mixin.py.bak_before_graphics_toggle_C
- console_ui_mixin.py.bak_before_graphics_toggle_B

---

## Notas sobre scripts anteriores (no documentados aquí)

Existen otros scripts en el proyecto que fueron creados antes de esta
bitácora:

- fix_snapshot_labels.py         → etiquetas del combo Gráficos con snap. discos / completo
- fix_snapshot_warning_dialog.py → diálogo de snapshot con VirtIO-GPU más claro

Cuando se retomen, documentar aquí.

---

## 2026-09-27 — install_flow_mixin.py nunca se subió a GitHub

### Problema
El archivo install_flow_mixin.py (módulo real del proyecto) nunca estaba
en GitHub. El .gitignore tenía la regla 'install_*.py' para ignorar
scripts temporales, pero también capturaba este archivo real.

### Fix
Añadidas excepciones al final del .gitignore:
  !install_flow_mixin.py
  !*_mixin.py

### Lección aprendida
Los patrones wildcard en .gitignore son peligrosos. Cada vez que se
añade un patrón, ejecutar:
  git status --ignored --short | grep '^!!' | grep '.py$'
y revisar que ningún archivo real quede atrapado.

---

## 2026-09-27 — Fix macOS: disco dedicado + Recovery bloqueante + .gitignore

### Problema 1
Arrancar macOS fallaba con:
  qemu-system-x86_64: -drive id=MacHDD,...format=qcow2: Image is not in qcow2 format
Porque el BaseSystem.img (RAW) estaba registrado como disco SATA y se usaba
como MacHDD.

### Fix 1
install_flow_mixin.py: branch para macOS que usa siempre mac_hdd_ng.qcow2
(QCOW2, 128G) como disco del sistema. Ignora storage_devices del usuario.
Sigue el modelo de OSX-KVM: OpenCore (bootloader) + BaseSystem (instalacion)
+ MacHDD (disco del sistema).

### Problema 2
Al faltar el Recovery, la app lanzaba la descarga en segundo plano y
mostraba un dialogo critical pidiendo al usuario que volviera a pulsar
Iniciar al terminar.

### Fix 2
install_flow_mixin.py: nueva funcion _macos_recovery_download_blocking.
Usa QEventLoop + TaskProgressDialog modal + _BackgroundCallThread para
bloquear el flujo de arranque hasta que la descarga termine. Al terminar,
continua automaticamente. Cancelar aborta sin dialogo de error.

### Problema 3 (critico)
install_flow_mixin.py NUNCA estaba en GitHub. El .gitignore tenia la regla
'install_*.py' para ignorar scripts temporales, pero capturaba tambien
este archivo real. Cualquiera que clonara el repo obtenia una app rota.

### Fix 3
Anadidas excepciones al final del .gitignore:
  !install_flow_mixin.py
  !*_mixin.py
Se sube install_flow_mixin.py por primera vez.

### Archivos tocados
- install_flow_mixin.py
- .gitignore
- docs/screenshots/install-macos.png (nueva captura)
- README.md (anadida la captura)

### Scripts aplicados
- scripts/fix_macos_disk_logic.py
- scripts/fix_macos_recovery_flow.py
- scripts/fix_gitignore_install_flow.py

### Leccion aprendida sobre .gitignore
Los patrones wildcard son peligrosos. Cada vez que se anade uno, ejecutar:
  git status --ignored --short | grep '^!!' | grep '.py$'
y revisar que ningun archivo real del proyecto quede atrapado.

Patrones actuales en .gitignore que podrian ser peligrosos si se anaden
archivos reales con esos nombres: fix_*.py, add_*.py, refactor_*.py,
rename_*.py, cleanup_*.py, probe_*.py, install_*.py, integrate_*.py,
switch_*.py, shorten_*.py, snapshot_*.py, stack_*.py, tune_*.py,
reorder_*.py, reorganize_*.py, implement_*.py, enhance_*.py, export_*.py,
help_*.py, improve_*.py, apply_*.py, setup_console_*.py.

Si en el futuro se crea un modulo real del proyecto con alguno de estos
prefijos (por ejemplo "install_helpers.py"), hay que anadir su excepcion
correspondiente (!install_helpers.py) al final del .gitignore.
