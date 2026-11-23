# Instalación en macOS Intel (uso personal)

Esta guía cubre **macOS Intel como host** (no Apple Silicon). El objetivo es
ejecutar VMs x86_64 con aceleración por hardware mediante
**Hypervisor.framework (HVF)**, el equivalente a KVM en Linux y WHPX en Windows.

> La aplicación es para **uso personal no comercial**. El bundle `.app` que
> genera el CI se firma *ad hoc*: **no está notarizado**. Ábrelo con
> **clic derecho → Abrir**, o quita la cuarentena:
> ```bash
> xattr -d com.apple.quarantine ~/Downloads/VirtualMachine.app
> ```

## Requisitos

| Componente | Por qué | Cómo instalarlo |
|---|---|---|
| macOS 10.15+ en **Intel** (VT-x + EPT) | HVF no existe en Apple Silicon | — |
| Python 3.11 | Solo si se ejecuta desde código | `brew install python@3.11` |
| QEMU con HVF | Motor de las VM y firmware OVMF | `brew install qemu` |
| PowerShell 7 (`pwsh`) | Solo para Fido (resolver ISOs de Windows) | `brew install --cask powershell` |

Homebrew instala en `/usr/local/bin` en Mac Intel. La aplicación busca QEMU
también en `/opt/homebrew/bin` (Apple Silicon) y `/opt/local/bin` (MacPorts),
así que funciona aunque la app se lance desde Finder sin el `PATH` de Terminal.

## Opción A — ejecutar desde código (recomendado para empezar)

```bash
cd virtual-machine
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
brew install qemu
python main.py
```

## Opción B — bundle `.app` del CI

1. Descarga `VirtualMachine-macOS-intel.zip` desde el Release.
2. Descomprime y mueve `VirtualMachine.app` a `/Applications` (o donde quieras).
3. Ábrelo con **clic derecho → Abrir** la primera vez (o con `xattr` arriba).
4. El `.app` **no incluye QEMU**: instálalo con `brew install qemu`.

El `.zip` se genera automáticamente en el job `build-macos` del CI y se adjunta
a los tags `v*`. No hay DMG ni notarización: para distribuirlo públicamente
haría falta un Developer ID (99 USD/año), innecesario para uso personal.

## Comprobar que HVF está activo

En **Configuración Host → Diagnóstico** debe aparecer:

- `QEMU`: ruta bajo `/usr/local/bin/...`
- `HVF (Hypervisor.framework)`: ✅ *disponible (comprobado)*
- `Firmware UEFI (OVMF)`: ruta bajo `/usr/local/share/qemu/...`

Si en la consola aparece el aviso **«Sin HVF: esta VM corre con TCG»**,
revisa que `qemu-system-x86_64` exista y vuelve a abrir la app. Sin HVF una VM
macOS invitada es prácticamente inutilizable.

## Crear una VM macOS invitada

El proyecto incluye OSX-KVM/OpenCore y ya aplica los ajustes que funcionaban
en `main`: VGA de 128 MB, USB EHCI (teclado/tablet), un solo monitor, VNC/SPICE
sin portapapeles ni Guest Agent y keycodes RFB clásicos para el menú de arranque.

1. Descarga la imagen base de recuperación desde **Medios → MacOS Recovery**
   (busca el script en `~/Downloads/OSX-KVM` o `~/Descargas/OSX-KVM`).
2. Crea la VM con plataforma `macOS`, firmware UEFI y 4–8 GB de RAM.
3. Arranca y abre la consola embebida (VNC). El menú de OpenCore responde al
   teclado desde el primer momento.

## Limitaciones conocidas en host macOS

- **Sin passthrough PCI/IOMMU**: HVF no lo expone al invitado. El diagnóstico lo
  marca como aviso, no como error.
- **Sin VirtioFSD**: usa SMB con `smbd` (macOS lo trae; actívalo en
  *Ajustes del sistema → General → Compartir → Compartir archivo*).
- **SPICE sin portapapeles**: se prefiere la consola VNC embebida.
- **RAM y CPU** se leen con `psutil`/`sysctl`, así que el semáforo RAM/vCPU es
  correcto. El escáner PCI/USB de `/sys` queda vacío (no afecta a las VM).
- **Invitados ARM no se aceleran**: el runner genera máquinas `x86_64`. HVF en
  una Mac Intel solo acelera invitados x86_64.
- **Reparación del host**: en macOS no hay pkexec/udev/WHPX que reparar; el
  botón muestra las instrucciones de Homebrew en vez de fallar.

## Datos y configuración

| Sistema | Directorio de datos |
|---|---|
| Windows | `%LOCALAPPDATA%\VirtualMachine` |
| Linux | `~/.local/share/virtual-machine` |
| macOS | `~/Library/Application Support/VirtualMachine` |

Los ajustes (tema, idioma, API REST en `127.0.0.1:8730`, rutas de QEMU) usan
`QSettings` y se guardan en `~/Library/Preferences` con GUI de macOS.
