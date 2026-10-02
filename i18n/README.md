# i18n / internacionalizacion

Marcador: `i18n_v1`.

## Modelo

- **Espanol es el idioma FUENTE.** Las cadenas del codigo ya estan en
  espanol. No hay `vm_es.ts` / `vm_es.qm`: cuando el idioma activo es
  `"es"`, `load_language()` no instala ningun traductor y se muestra el
  codigo tal cual.
- **Ingles (y futuros idiomas)** viven en `vm_<code>.ts` (texto plano
  XML editable con Qt Linguist) y se compilan a `vm_<code>.qm` (binario
  que Qt carga).

## Workflow

1. Envolver las cadenas de UI en `self.tr("...")` (dentro de cualquier
   `QObject`) o en `QCoreApplication.translate("Contexto", "...")`
   (fuera de QObject).

2. Extraer las cadenas a un `.ts`:

       pylupdate6 *.py -ts i18n/vm_en.ts

   Genera (o actualiza) `i18n/vm_en.ts`. Las entradas ya traducidas se
   conservan; solo se anaden las nuevas y se marcan como `obsolete` las
   que han desaparecido del codigo.

3. Traducir con Qt Linguist:

       linguist i18n/vm_en.ts

4. Compilar a binario:

       lrelease i18n/vm_en.ts

   Genera `i18n/vm_en.qm`.

5. Arrancar la app con `./run.sh` y elegir el idioma en el selector del
   corner superior derecho de las pestanas. La preferencia queda en
   `QSettings("ui/language")` y se aplica en el siguiente arranque.

## Que NO se traduce (a proposito)

- Textos operativos de las VMs: notas, nombres de grupo, colores,
  `vm_config.ini`.
- Logs de consola (`==>`, `[AVISO]`, `[ERROR]`, `✓`): son diagnosticos
  tecnicos. Traducirlos complica los `grep` y los reportes de bug.
- Comandos QEMU, paths, nombres de archivo.

## Pendiente (fases siguientes)

- Envolver strings de `dialogs.py` (`DiskCreationDialog`,
  `MediaPickerDialog`, `NatPortForwardDialog`, `_CreateMediumDialog`).
- Envolver strings de los mixins de UI (`vm_lifecycle_mixin.py`,
  `storage_mixin.py`, `console_ui_mixin.py`, etc.).
- Envolver el panel de Ayuda. Recomendacion: en lugar de meter las ~60
  lineas de HTML en el `.ts`, tener `README_ayuda_es.md` y
  `README_ayuda_en.md` y cargar el que corresponda.
