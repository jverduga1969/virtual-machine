# Instalar Virtual.Machine en Windows

La forma recomendada es el instalador del release. El ejecutable es
autocontenido: **no** hace falta instalar Python, Git ni PyQt6 a mano.

## 1. Requisitos

- Windows 10 u 11 de **64 bits**.
- Procesador con Intel VT-x o AMD-V (para WHPX; sin él la app usa TCG y va muy
  lento).
- Al menos 4 GB de RAM (8 GB recomendados).
- Permisos de administrador para que el postinstall pueda activar WHPX y crear
  reglas de firewall.

## 2. Instalación

1. Descargar `VirtualMachine-Setup-1.0.0.exe` desde el release
   [`v1.0.0-windows-4`](https://github.com/jverduga1969/virtual-machine/releases/tag/v1.0.0-windows-4).
2. Ejecutarlo. El instalador ya corre elevado porque instala en
   `{autopf}\Virtual.Machine`.
3. Al terminar se lanza automáticamente `scripts\postinstall.ps1` (también en
   instalaciones silenciosas: se quitó `skipifsilent`). El script:
   - instala `SoftwareFreedomConservancy.QEMU` y `RedHat.VirtViewer` con winget;
   - localiza `qemu-system-x86_64.exe` y `qemu-img.exe` en Program Files, winget,
     Chocolatey, Scoop, `QEMU_DIR` o el PATH, y añade su carpeta al PATH del
     usuario;
   - activa **HypervisorPlatform (WHPX)** con
     `Enable-WindowsOptionalFeature -NoRestart` si estaba desactivado;
   - sustituye las reglas de firewall amplias por `VM-Manager QEMU local`
     (por ejecutable, perfil Privado, solo subred local);
   - crea `%LOCALAPPDATA%\VirtualMachine` con las carpetas `vms`, `isos` y la
     biblioteca de medios.

   Si la activación de WHPX falla, el script lo avisa pero no aborta: la app
   funciona con HAX o TCG. Si se activó, **reinicia Windows**.

## 3. Primera puesta en marcha

1. Abrir **Virtual.Machine**.
2. Ir a **Configuración Host → Diagnóstico** y pulsar **🔄 Comprobar de nuevo**.
   Deben aparecer como OK: QEMU, `qemu-img`, OVMF (CODE y VARS), WHPX y TPM.
   Los avisos indican funciones opcionales, no errores.
3. Si el diagnóstico marca algo en rojo, pulsar **🛠️ Reparar lo que falte**.
   El botón eleva con `Start-Process -Verb RunAs`.
4. En **📁 Rutas de almacenamiento**, indicar dónde están las VMs y las ISOs si
   no usas el directorio por defecto `%LOCALAPPDATA%\VirtualMachine`. El cambio
   requiere reiniciar la aplicación.
5. Pulsar **➕ Nueva VM**, elegir sistema e ISO, guardar y pulsar **▶ Iniciar**.

## 4. Puntos específicos de Windows

- **Aceleración:** se usa WHPX cuando está disponible; si no, TCG (emulación
  por software, 2–5 % de velocidad). WHPX no convive bien con VirtualBox,
  VMware ni HAXM activos. Si lo activas a mano: *Activar o desactivar
  características de Windows* → **Plataforma de hipervisor de Windows** y
  reiniciar.
- **Windows 11:** necesita UEFI con Secure Boot y TPM 2.0. El TPM se emula con
  el backend `emulator` de QEMU; el diagnóstico lo verifica preguntando al
  propio QEMU. Si faltan los VARS de Secure Boot, usar **Configuración Host →
  🛠️ Reparar OVMF**. El diagnóstico también valida que la copia de **Fido v1.71**
  incluida con la app sirva para resolver las URLs de las ISOs de Windows, sin
  descargar nada durante la comprobación.
- **Consolas:** VNC funciona embebida. Para SPICE externo hace falta
  `remote-viewer.exe` (lo instala el postinstall). Las consolas escuchan solo
  en `127.0.0.1`; no se abren rangos de puertos al firewall.
- **USB passthrough:** sí está soportado. QEMU usa `usb-host` con libusb, así
  que cada dispositivo necesita **WinUSB** o **libusbK**. Abre **Configuración
  Host → 🔌 USB (Windows) → Abrir Zadig**, instala el driver al dispositivo y
  añade un puntero USB en **Configuración VM → Dispositivos** para crear el bus
  XHCI.
- **PCI/GPU passthrough (VFIO):** no soportado en Windows; requiere Linux con
  `vfio-pci` e IOMMU.
- **Carpetas compartidas:** requieren Samba con `smbd` y, para el montaje
  automático, **QEMU Guest Agent** dentro del invitado.
- **API REST:** en **Configuración Host → 🔌 API REST** se activa un servicio
  local en `127.0.0.1:8730` con token Bearer; ver el tema *API REST local* de
  la pestaña Ayuda.
- **Desktop Mode / modo kiosco:** eliminado; no restaurar.

## 5. Desinstalación

Usar el desinstalador del Panel de Control o *Aplicaciones y características*.
Además de borrar la carpeta de instalación, se ejecuta `scripts\uninstall.ps1`,
que retira solo el PATH y las reglas de firewall que añadió el postinstall.
**Los datos de las VMs se conservan**: para borrarlos manualmente, eliminar
`%LOCALAPPDATA%\VirtualMachine`.

## 6. Instalación desde el código (desarrolladores)

Solo si quieres compilar o depurar:

```powershell
git clone <url-del-repositorio>
cd NVM
python -m pip install -r requirements.txt -r requirements-dev.txt
$env:QT_QPA_PLATFORM="offscreen"; python -m pytest -q
python -m PyInstaller --noconfirm --clean virtualmachine.spec
```

La rama de trabajo es `windows-port`; `main` se mantiene intacta. No hacer
commit ni push salvo petición explícita. Ver `CONFIGURACION_WINDOWS.md` para el
estado detallado del repositorio y las fases de auditoría aplicadas.
