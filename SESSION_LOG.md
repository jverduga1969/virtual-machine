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
