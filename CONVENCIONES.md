# Convenciones del proyecto Virtual.Machine

## Idioma y estilo

- Comentarios, docstrings y mensajes al usuario: **en español**.
- Nombres de variables, funciones, clases y archivos: **en inglés** o
  spanglish consistente con lo existente (ej: `_sync_external_viewer`).
- Longitud de línea: ~100 caracteres. Sin obsesión, pero sin pasarse.
- Indentación: 4 espacios (Python estándar). Sin tabs.
- Citas: comillas dobles para strings. Comillas simples solo si el
  string contiene comillas dobles.

## Arquitectura

- **Mixins** agrupan funcionalidad por área. No clases monolíticas.
  Ej: `ConsoleUiMixin`, `SnapshotsMixin`, `VmLifecycleMixin`.
- La clase principal `VirtualMachineManagerApp` hereda de todos los mixins.
- Los mixins **no tienen `__init__`**; asumen que `self` ya tiene todo
  lo que necesitan (widgets, atributos) cuando se llaman.
- Helpers puros (sin PyQt) van en módulos sueltos: `console_backend.py`,
  `host_deps.py`, `network_utils.py`, `vm_config.py`, `shared_folders.py`.

## Formato de mensajes en consola

- `==>` → paso importante (color info)
- `[AVISO]` → algo no crítico pero digno de mención (amarillo)
- `[ERROR]` → fallo (rojo)
- `✓` → confirmación de éxito (verde)
- Sin prefijo → información general

## Marcadores internos

Cuando una decisión no es obvia, se deja un comentario con un marcador
que se pueda buscar con grep. Ejemplos:

- `nvme_default_all_modern_os` → política de bus de discos por SO
- `cdrom_sata_ahci_v1` → versión del esquema de CDs por AHCI
- `MODE_HYBRID_GL` → modo híbrido con ventana GL de QEMU

Así, si alguien quiere saber "por qué este disco va por NVMe", puede
hacer `grep -rn nvme_default_all_modern_os .` y encontrar todo lo relevante.

## Scripts de fix

- Viven en `scripts/` (o en la raíz si son pocos).
- Nombres: `fix_<cosa>.py`, `add_<cosa>.py`.
- **Idempotentes**: si ya está aplicado, dicen "ya estaba" y no escriben.
- **Backup automático**: `archivo.py.bak_before_<tag>`.
- **Verifican sintaxis** antes de escribir (`compile(text, "<check>", "exec")`).
- **Salida con colores**: `OK` verde, `[!]` amarillo, `X` rojo.
- **Nunca borran backups**.
- Al final imprimen "Listo. Arranca con ./run.sh".

## Backups

- Los `.bak_before_<tag>` **no se borran nunca**.
- Antes de un fix grande, se puede crear un backup manual con
  `cp archivo.py archivo.py.bak_manual_$(date +%Y%m%d_%H%M)`.
- Si un fix falla, el usuario revierte con `cp archivo.py.bak_before_<tag> archivo.py`.

## Cómo se construye el comando QEMU

Todo el comando se arma en `InstallWorker._run_impl()`:

1. Se detectan capacidades del host (KVM, OVMF, swtpm, audio, gráficos).
2. Se construye el script bash línea a línea en `script_content`.
3. Los argumentos auxiliares (VirtioFS, QGA, consola) se insertan juntos
   antes de `-qmp` con `_insert_pre_qmp_args()`.
4. **Importante**: los argumentos gráficos (`-display`, `-device virtio-vga*`)
   los emite SOLO `_graphics_args()`. Nadie más debe emitir `-display`.

## Modos de consola (modelo actual)

- `PROTOCOL_VNC` / `PROTOCOL_SPICE`
- `MODE_EMBEDDED`   → widget dentro de la app
- `MODE_EXTERNAL`   → visor del sistema (spicy/remote-viewer/vncviewer)
- `MODE_NATIVE`     → ventana propia de QEMU (GTK/SDL)
- `MODE_HYBRID`     → VNC embebido + SPICE externo (los dos a la vez)
- `MODE_HYBRID_GL`  → VNC embebido (2D) + ventana GL propia de QEMU (3D)

## Gráficos

- `graphics_mode` posibles: `auto`, `virtio`, `virgl`, `venus`,
  `qxl`, `vmware`, `none`.
- Con VNC embebido o Híbrida 2D: se prohíben `virgl`, `venus`.
- Con Híbrida 3D: se permiten todos, porque el 3D va por la ventana
  GL de QEMU, no por el socket VNC.
- **"Automático" nunca se deshabilita**. Su texto se actualiza con
  `_refresh_auto_graphics_label()` para decir qué opción usará.

## Testing

- Antes de aplicar un fix, compilar el archivo con `compile()`.
- Después de aplicar, arrancar la app y probar el flujo afectado.
- No hay suite de tests formal todavía. Se aceptan tests puntuales.

## Cómo trabajar con el asistente

- Pídele resúmenes de traspaso antes de que el chat se llene.
- Cada fix exitoso → anotar 4 líneas en `SESSION_LOG.md`.
- Cada decisión no obvia → comentario con marcador en el código.
- Los scripts largos se pegan como heredoc (`cat > archivo << 'EOF'`)
  para evitar problemas de copiar/pegar.
