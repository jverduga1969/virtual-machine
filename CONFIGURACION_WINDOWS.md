# Configuración para Windows — Virtual Machine

Documento de traspaso del repositorio. Contiene el estado real de la rama, los
pasos para usar la app en Windows y el resumen de las fases de auditoría ya
aplicadas, para poder retomar el trabajo en una sesión nueva de OpenCode.

## 1. Estado actual del repositorio

- **Ubicación compartida:** `/run/media/jimmy/Datos/Descargas/DeepSeek Harness/NVM`
  (en Windows: `D:\Descargas\DeepSeek Harness\NVM`).
- **Rama:** `windows-port`. `main` / `origin/main` quedan intactos en `2c7748f`.
  **No se ha promovido `windows-port` a `main` directamente**: GitHub rechaza el
  PR entre ambas por «No common ancestor». Si se quiere integrar, usar un merge
  controlado o renombrar `main-legacy`.
- **Último commit:** `f02c238` — *CI: SPICE local en Windows usa TCP en los tests
  de macOS*. Todo el trabajo de las fases A, B y C está **sin commitear** en el
  árbol de trabajo; ver `git status --short` para el listado exacto.
- **Git local ajustado:** `core.autocrlf=false` y `core.filemode=false`, para que
  Git for Windows no marque todos los archivos como modificados. Todos los
  archivos del repo usan LF (también los `.ps1`); lo garantiza `.gitattributes`
  con `* text=auto eol=lf`, así que el checkout en `windows-latest` no los
  convierte a CRLF.
- **Validación:** `284 passed, 1 warning` con Python 3.11
  (`/tmp/opencode/nvm-venv311/bin/python -m pytest -q`). El aviso restante es el
  `DeprecationWarning` conocido de `locale.getdefaultlocale` en
  `services/iso_sources.py`. También pasan `bash -n scripts/postinstall.sh`,
  `compileall` y `git diff --check`.
- **No se han creado tags ni releases nuevos** después de `v1.0.0-windows-4`.

### Release publicado

- **`v1.0.0-windows-4` → detección real de WHPX + aviso adaptado (el más reciente).**
  https://github.com/jverduga1969/virtual-machine/releases/tag/v1.0.0-windows-4
- Instalador: https://github.com/jverduga1969/virtual-machine/releases/download/v1.0.0-windows-4/VirtualMachine-Setup-1.0.0.exe
- Ejecutable suelto: https://github.com/jverduga1969/virtual-machine/releases/download/v1.0.0-windows-4/VirtualMachine.exe

Los 3 jobs del CI (pytest Ubuntu, pytest Windows, EXE + instalador) estaban en
verde en el run `#17` (`45167973579`) sobre `f02c238`. Los cambios de las fases
A/B/C todavía no se han subido, así que ese run **no** los cubre.

## 2. Instalación y uso en Windows

1. Instalar `VirtualMachine-Setup-1.0.0.exe` del release `v1.0.0-windows-4`.
   Reiniciar sobre la versión anterior está bien.
2. El instalador se ejecuta elevado (instala en `{autopf}`) y lanza
   `scripts\postinstall.ps1` con el token de administrador heredado. El script:
   - instala **solo** `SoftwareFreedomConservancy.QEMU` y `RedHat.VirtViewer`
     con winget (nada de restos del antiguo modo kiosco);
   - exige `qemu-system-x86_64.exe` **y** `qemu-img.exe`;
   - consulta `Get-WindowsOptionalFeature -FeatureName HypervisorPlatform` y,
     si está desactivada, ejecuta `Enable-WindowsOptionalFeature ... -NoRestart`;
     si no puede, avisa y la app sigue con HAX o TCG;
   - elimina las reglas de firewall amplias `VM-Manager VNC`/`SPICE`
     (`5900-6000` / `5930-6000`, perfil `Any`) y crea `VM-Manager QEMU local`
     por ejecutable, con perfil `Private` y `RemoteAddress LocalSubnet`;
   - guarda en `%LOCALAPPDATA%\VirtualMachine\postinstall-paths.txt` solo las
     rutas que añadió al PATH del usuario, para que el desinstalador las retire.
3. **Reiniciar** si el postinstall activó WHPX (lo indica con `RestartNeeded`).
   WHPX no convive bien con VirtualBox, VMware ni HAXM activos.
4. Abrir la app → **Configuración Host → Diagnóstico**. Debe mostrar QEMU,
   `qemu-img`, VARS de OVMF, WHPX y TPM como OK. Los avisos no bloquean.
5. Rellenar las rutas si las VMs no están en el directorio por defecto:
   - **Directorio de QEMU (qemu-img.exe):** p. ej. `C:\Program Files\qemu`.
   - **Directorio base / vms / isos / biblioteca:** ver el apartado 3.
6. Para USB passthrough, instalar **WinUSB** o **libusbK** con Zadig desde
   **Configuración Host → 🔌 USB (Windows)** y añadir un puntero USB en
   **Configuración VM → Dispositivos** para crear el bus XHCI.

No hace falta Python ni Git para ejecutar el `.exe`: es autocontenido.

## 3. Datos y rutas

- En Linux hay **47 GB** en `~/.local/share/virtual-machine/vms`.
- La partición compartida «Datos» tiene solo **39 GB libres** → **no caben**.
- Windows no puede leer la partición btrfs de `/home`.

Para ver las VMs en Windows:
1. Liberar espacio o usar otro disco (≈ 50 GB).
2. Copiar `vms/` (y `isos/` si se usara) a, por ejemplo, `D:\VirtualMachine`.
3. En **Configuración Host → 📁 Rutas de almacenamiento** poner:
   - **Directorio base:** `D:\VirtualMachine`
   - **Directorio de QEMU:** carpeta con `qemu-img.exe`
   - **Directorio de VMs:** `D:\VirtualMachine\vms`
   - **Directorio de ISOs:** `D:\VirtualMachine\isos`
   - **Biblioteca de medios:** `D:\VirtualMachine\MediaLibrary`

El valor por defecto en Windows es `%LOCALAPPDATA%\VirtualMachine`: sin cambiarlo
no aparecerá ninguna VM. El desinstalador **conserva** estos datos.

Claves QSettings: `paths/base_dir`, `paths/vms_dir`, `paths/isos_dir`,
`paths/media_dir`, `paths/qemu_dir`, `ui/language`, `ui/theme`, `api/port` y
`api/token`.

## 4. API REST

**Configuración Host → 🔌 API REST** arranca un servidor HTTP en `127.0.0.1`
(puerto `8730` por defecto), con un token Bearer persistente que se muestra en
la propia página. Endpoints: `GET /health`, `GET /vms`, `GET /vms/<id>`,
`POST /vms/<id>/start` y `POST /vms/<id>/stop`. Ejemplo:

```bash
curl -H "Authorization: Bearer TU_TOKEN" http://127.0.0.1:8730/vms
```

## 5. Desinstalación

El instalador incluye `[UninstallRun]` con `scripts\uninstall.ps1`, que:

- retira del PATH del usuario **solo** las rutas listadas en
  `postinstall-paths.txt`;
- elimina las reglas de firewall `VM-Manager QEMU local`, `VM-Manager VNC` y
  `VM-Manager SPICE`;
- **no** borra datos de VMs ni desinstala QEMU.

Se eliminó `skipifsilent` de `[Run]`: una instalación desatendida también
necesita el host configurado, o la app arrancará sin QEMU y sin aceleración.

## 6. Si vas a seguir desarrollando desde Windows

- Instalar **Git for Windows** y **Python 3.11** (el venv
  `/tmp/opencode/nvm-venv311` es de Linux: rutas absolutas, crear uno nuevo).
- `pip install -r requirements.txt -r requirements-dev.txt`.
- Comandos útiles desde la ruta compartida:
  ```powershell
  python -m compileall -q core services plugins ui_widgets vnc_widget tests
  $env:QT_QPA_PLATFORM="offscreen"; python -m pytest -q
  ```
- Para publicar se necesita un token con scope `workflow`. En Linux se ponía en
  `/tmp/opencode/gh_token` y se borraba después de usarlo. **El token actual ya
  fue borrado**: hay que crear uno nuevo cuando toque hacer push.
- **No hacer commit ni push salvo petición explícita.**
- Ignorar por completo `Virtual.Machine/`.
- No restaurar el modo kiosco.
- `scripts/postinstall.ps1` y `scripts/uninstall.ps1` deben permanecer ASCII
  estricto y en LF; `python scripts/verify_repo.py` lo comprueba antes de cada
  build.

## 7. Resumen de las fases de auditoría

### Fase A — honestidad y verificación

- `core/app_context.py`: `default_base_dir()` compartido entre `AppContext` y
  Configuración Host.
- `services/host_diagnostics.py`: `find_qemu_binary()`, check de `qemu-img`,
  VARS/Secure Boot (mínimo 10 KB), IOMMU real, VNC embebido verificado y avisos
  honestos de WHPX/TPM/Samba en Windows.
- `plugins/host_config/plugin.py`: diagnósticos con `tr()`, `_wait_for_repair()`
  con código de salida real, `-PassThru`/`ExitCode` y reparación OVMF con ramas
  Linux/Windows.
- `scripts/postinstall.sh` / `.ps1`: `pipefail`, contador de errores y `exit 1`
  si fallan paquetes o grupos.
- Fido: copia canónica **v1.71** con `# --- patched-for-linux ---` en la raíz;
  se eliminó `services/Fido.ps1` (v1.70). En Linux/macOS se parchea una copia
  temporal, nunca la ruta instalada. Los IDs `3813`/`3816` son correctos porque
  `msdl` ya usa `3813`.
- 16 regresiones nuevas en `tests/test_host_diagnostics.py`.

### Fase B — correcciones técnicas

- WHPX real con DISM, firewall acotado, `scripts/uninstall.ps1` y
  `[UninstallRun]`; `skipifsilent` eliminado.
- IOMMU conectado a la UI (`--enable-iommu`).
- TPM verificado con `qemu -tpmdev help` en Linux y Windows.
- Fido diagnosticado sin red; driver USB con enlace a Zadig.
- Utilidades de apoyo (`lsof`, `git`, `tar`, `xdg-utils`, `libnotify*`) en
  `postinstall.sh`.
- OVMF de Windows alineado con `find_ovmf_windows()`.
- `services/rest_api.py` nuevo, enlazado a `127.0.0.1` con token Bearer, y
  conectado a la página antes inerte.
- 17 regresiones nuevas en `tests/test_host_phase_b.py`.

### Fase C — documentación, Ayuda y CI

- Pestaña **Ayuda** actualizada: Configuración Host con USB/IOMMU/diagnóstico,
  tema nuevo de API REST con ejemplos, requisitos Linux + Windows, FAQ de
  WHPX/firewall/API/Fido, rutas de ambos sistemas y versión alineada con el
  instalador (`1.0.0`).
- Este documento y `INSTALL_WINDOWS.md` actualizados.
- `.github/workflows/tests.yml` ampliado con validaciones estáticas de shells,
  ASCII de PowerShell, sintaxis de scripts y cobertura i18n.
- Tests de regresión en `tests/test_phase_c.py`.

## 8. Pendiente / decisiones

- No se ha tocado `Virtual.Machine/`.
- No se ha restaurado el kiosco.
- No hay commit, tag ni push nuevos: hace falta autorización explícita.
- Decisión pendiente histórica: no promover `windows-port` a `main` directamente.
- Sin acceso real a Windows/WHPX/UAC ni macOS: los tests simulan comandos y
  estados. La API REST sí se probó contra un servidor HTTP real.
