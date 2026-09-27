# Política de seguridad

## Versiones soportadas

Solo la rama `main` recibe correcciones de seguridad. Si usas una copia
antigua, actualiza antes de reportar.

## Cómo reportar una vulnerabilidad

**No abras un issue público** si el problema es una vulnerabilidad de
seguridad (por ejemplo, ejecución de código arbitrario, elevación de
privilegios no autorizada, fuga de credenciales).

En su lugar, envía un correo a:

**jimmyverduga [arroba] gmail [punto] com**

Asunto sugerido: `[SECURITY] virtual-machine — descripción breve`

Incluye si puedes:

- Descripción del problema.
- Cómo reproducirlo (versión de la app, distribución, comando o captura).
- Impacto estimado.
- Si tienes una propuesta de solución, mejor.

Te responderé en un plazo de **7 días** confirmando la recepción. Si la
vulnerabilidad es válida, coordinamos la publicación del arreglo y el
crédito.

## Alcance

Este proyecto es una aplicación de escritorio que:

- Se ejecuta con los privilegios del usuario que la lanza.
- Solicita elevación vía `pkexec` para operaciones puntuales (preparar
  PCI/VFIO, reglas udev, montajes) — **siempre muestra un diálogo del
  sistema** antes de elevar; nunca eleva en silencio.
- No envía telemetría a ningún servidor.
- Solo hace peticiones de red para: descargar ISOs desde espejos
  oficiales, descargar Fido.ps1 desde GitHub, y consultar los metadatos
  del Recovery de macOS a Apple.

Fuera de alcance:

- Vulnerabilidades en QEMU, kernel Linux o cualquier dependencia
  upstream. Repórtalas a sus respectivos proyectos.
- Vulnerabilidades en el propio sistema operativo del host.
- Configuraciones inseguras del usuario (por ejemplo, correr la app
  como root).

## Prácticas del proyecto

- Los comandos de shell que se generan usan `shlex.quote` / escape
  explícito para todos los valores que vienen de la configuración de la
  VM.
- La validación de campos de red (`model`, `mode`, `interface`, `mac`)
  se hace contra lista blanca antes de insertarlos en la línea de QEMU.
- Las credenciales nunca se guardan en el proyecto; el token de GitHub
  es solo para desarrollo y no se sube.
