# Configuración para Windows — Virtual Machine

Documento de traspaso (no versionado todavía). Contiene el estado del proyecto, los
pasos para usar la app en Windows y el resumen de la conversación para retomar el
trabajo en una sesión nueva de OpenCode.

## 1. Estado actual del repositorio

- **Ubicación compartida:** `/run/media/jimmy/Datos/Descargas/DeepSeek Harness/NVM`
  (en Windows: `D:\Descargas\DeepSeek Harness\NVM`).
- **Rama:** `windows-port`. `main` queda intacta en `2c7748f`.
- **HEAD:** `7e4ee9d` — *Detectar WHPX con QEMU y adaptar el aviso de TCG en Windows*.
- Commit previos ya publicados: `cb5bc27` (monitor de host con psutil), `27ef78a`
  (plugins en PyInstaller), `9696a7f` (workflow de releases).
- **Copia original en Linux:** `/home/jimmy/Descargas/DeepSeek Harness/NVM` se conservó
  en `cb5bc27` con los cambios de WHPX sin commitear. Es una copia antigua: la fuente
  de verdad es la ruta compartida.
- **Git local ya ajustado** en la copia compartida:
  - `core.autocrlf=false`
  - `core.filemode=false`
  Así Git for Windows no marca todos los archivos como modificados.
- `git status` limpio en la copia compartida.
- Tests: **155 passed** (`/tmp/opencode/nvm-venv314/bin/python -m pytest -q`).
- `compileall` correcto y los 6 JSON de `i18n/` válidos.

### Releases

- `v1.0.0-windows-2` → primer build con fix de `qemu-img`.
- `v1.0.0-windows-3` → pestañas restauradas + monitor de host.
- **`v1.0.0-windows-4` → detección real de WHPX + aviso adaptado (el más reciente).**

https://github.com/jverduga1969/virtual-machine/releases/tag/v1.0.0-windows-4

- Instalador: https://github.com/jverduga1969/virtual-machine/releases/download/v1.0.0-windows-4/VirtualMachine-Setup-1.0.0.exe
- Ejecutable suelto: https://github.com/jverduga1969/virtual-machine/releases/download/v1.0.0-windows-4/VirtualMachine.exe

Los 3 jobs del CI (pytest Ubuntu, pytest Windows, EXE + instalador) están en verde.

## 2. Pasos para usar la app en Windows

1. Instalar `VirtualMachine-Setup-1.0.0.exe` del release `v1.0.0-windows-4`.
   Reiniciar sobre la versión anterior está bien.
2. Activar WHPX. Como administrador:
   ```powershell
   dism /Online /Enable-Feature /FeatureName:HypervisorPlatform /All
   ```
   También se puede desde *Activar o desactivar características de Windows* →
   **Plataforma de hipervisor de Windows** (y **Hyper-V** si no está). Reiniciar.
   WHPX no convive bien con VirtualBox, VMware ni HAXM activos.
3. Abrir la app → **Configuración Host** y rellenar:
   - **Directorio de QEMU (qemu-img.exe):** p. ej. `C:\Program Files\qemu`
   - **Directorio base / vms / isos:** ver el apartado 3.
4. Si se usa SPICE, instalar **RedHat.VirtViewer** (lo hace el botón **Reparar**,
   que eleva con `Start-Process -Verb RunAs` sobre `scripts/postinstall.ps1`).
   Ese script instala **solo** `SoftwareFreedomConservancy.QEMU` y
   `RedHat.VirtViewer`: no instalar restos del antiguo modo kiosco.

No hace falta Python ni Git para ejecutar el `.exe`: es autocontenido.

## 3. Importante: las VMs existentes

- En Linux hay **47 GB** en `~/.local/share/virtual-machine/vms`.
- La partición compartida «Datos» tiene solo **39 GB libres** → **no caben**.
- Windows no puede leer la partición btrfs de `/home`.

Para ver las VMs en Windows:
1. Liberar espacio o usar otro disco (≈ 50 GB).
2. Copiar `vms/` (y `isos/` si se usara) a, por ejemplo, `D:\VirtualMachine`.
3. En **Configuración Host** poner:
   - **Directorio base:** `D:\VirtualMachine`
   - **Directorio de QEMU:** carpeta con `qemu-img.exe`
   - **Directorio de VMs:** `D:\VirtualMachine\vms`
   - **Directorio de ISOs:** `D:\VirtualMachine\isos`

El valor por defecto en Windows es `%LOCALAPPDATA%\VirtualMachine`: sin cambiarlo
no aparecerá ninguna VM.

Las claves QSettings son: `paths/base_dir`, `paths/vms_dir`, `paths/isos_dir`,
`paths/qemu_dir`, `ui/language`, `ui/theme`.

## 4. Si vas a seguir desarrollando desde Windows

- Instalar **Git for Windows** y **Python 3.14**.
- `pip install -r requirements.txt`
- El venv `/tmp/opencode/nvm-venv314` es de Linux (rutas absolutas): crear uno nuevo.
- Comandos útiles desde la ruta compartida:
  ```powershell
  python -m compileall -q core plugins services ui_widgets tests
  $env:QT_QPA_PLATFORM="offscreen"; python -m pytest -q
  ```
- Para publicar se necesita un token con scope `workflow`. En Linux se ponía en
  `/tmp/opencode/gh_token` y se borraba después de usarlo. **El token actual ya fue
  borrado**: hay que crear uno nuevo cuando toque hacer push.
- No hacer commit ni push salvo petición explícita.
- Ignorar por completo `Virtual.Machine/`.
- No restaurar el modo kiosco.

## 5. Resumen de la conversación (para retomar)

1. **i18n real en 6 idiomas** (Español, English, Português BR, Deutsch, Français,
   Italiano). `i18n/<codigo>.json` usa el texto español como clave; `es.json` es
   identidad. No hay `.qm` ni `lrelease`. Cambio de idioma en vivo desde
   Configuración Host, conservando `_ShowFilter` y `_nvm_retranslate`.
2. **Pestañas desaparecidas en el `.exe`:** PyInstaller guarda los `plugin.py` en el
   PYZ, no en disco. `core/plugin_manager.py` importa los 8 plugins por nombre
   cuando `sys.frozen` (lista `PLUGIN_MODULES`). Arreglo en `27ef78a`.
3. **Métricas del host en Windows:** `ui_widgets/resource_monitor.py` tenía
   `if IS_WINDOWS: return`. Ahora usa `psutil` para CPU/RAM/uptime/red/disco y
   `platform.processor()` para el modelo. `psutil` está en `hiddenimports` del spec.
   Arreglo en `cb5bc27`.
4. **`qemu-img` no encontrado:** `services/qemu_paths.py` busca en `QEMU_DIR`,
   Program Files, winget, Chocolatey, Scoop y MSYS2; no depende solo del `PATH`.
   `postinstall.ps1` añade la carpeta de QEMU al PATH del usuario.
5. **Aviso «Sin KVM / TCG» en Windows:** TCG es emulación por software (2–5 % de
   velocidad), por eso la ventana queda negra bastante rato. En Windows el
   acelerador es WHPX. La detección usaba `sc query WHvSvc` (servicio inexistente);
   ahora `HostAdapter._qemu_accepts_accel()` prueba `qemu -accel whpx -machine none`.
   El banner dice WHPX en Windows y KVM en Linux, con traducción nueva en los 6
   idiomas. Arreglo en `7e4ee9d`.
6. **Releases automáticos:** `.github/workflows/tests.yml` publica con
   `softprops/action-gh-release@v2` al pushear tags `v*`.
7. `main` y `windows-port` no tienen ancestors comunes: GitHub rechaza PR entre
   ellas («No common ancestor»). No se hizo PR ni force push.
8. Verificación periódica: `sha256sum -c /tmp/opencode/vms-before.sha` (en Linux).
   Hubo un cambio transitorio de `Windows10` a `Apagando...` que se corrigió solo;
   el checksum final vuelve a coincidir con
   `920ebd272d4d1aa1e9d6b3537b5ad7c6c20b3f3d4f3a427e1df52a638841b836`.

## 6. Pendiente / decisiones

- No se ha tocado `Virtual.Machine/`.
- No se ha restaurado el kiosco.
- No hay commit nuevo después de `7e4ee9d`.
- Este archivo **no está commiteado**: borrarlo o versionarlo según se decida.
