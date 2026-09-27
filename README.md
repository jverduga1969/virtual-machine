# Virtual.Machine

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-informational.svg)](#plataforma-soportada)

Asistente gráfico para crear y administrar máquinas virtuales con
**QEMU/KVM** en Linux. Interfaz Qt6 con consola VNC/SPICE embebida,
snapshots gráficos, integración con el huésped y soporte para
invitados Linux, Windows, macOS y Android.

---

## Capturas

### Instalacion de Android en curso

<p align="center">
  <img src="docs/screenshots/install-android.png" alt="Instalacion de Android" width="720">
</p>

### Instalacion de macOS en curso

<p align="center">
  <img src="docs/screenshots/install-macos.png" alt="Instalacion de macOS" width="720">
</p>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/main-resumen.png" alt="Pantalla principal"></td>
    <td width="50%"><img src="docs/screenshots/config-console.png" alt="Configuracion de la consola"></td>
  </tr>
  <tr>
    <td align="center"><em>Pantalla principal y panel de recursos</em></td>
    <td align="center"><em>Configuracion de la consola VNC/SPICE</em></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/console-vnc.png" alt="Consola VNC embebida"></td>
    <td width="50%"><img src="docs/screenshots/snapshots-graph.png" alt="Organigrama de snapshots"></td>
  </tr>
  <tr>
    <td align="center"><em>Consola VNC embebida dentro de la app</em></td>
    <td align="center"><em>Organigrama de snapshots</em></td>
  </tr>
</table>

---

## Plataforma soportada

**Virtual.Machine funciona únicamente en Linux con KVM.**

Es una decisión de diseño, no una limitación temporal. La aplicación se
apoya en servicios y subsistemas que solo existen en Linux:

| Componente | Depende de |
|---|---|
| Aceleración de hardware | `/dev/kvm` (Linux) |
| Passthrough PCI | VFIO + IOMMU + grupos IOMMU del kernel Linux |
| Passthrough USB sin contraseña | Reglas `udev` |
| Red en modo bridge | `/sys/class/net/<iface>/bridge` |
| Carpetas compartidas VirtioFS | `virtiofsd` del host Linux |
| Métricas de la VM (CPU, RAM, disco, red) | `/proc`, `/sys` |
| Elevación de privilegios | `pkexec` o `sudo` |
| Inhibición de suspensión | `systemd-inhibit` |

En macOS y Windows estos subsistemas no existen (o tienen equivalentes
muy distintos), así que **portar la app no es "cambiar un par de
llamadas"**: requiere reescribir la capa de interacción con el sistema
operativo. Ver la sección *Portabilidad* al final.

> Esta app **no** es un competidor de VirtualBox o VMware. Está pensada
> para el usuario de Linux que quiere controlar QEMU/KVM desde una GUI
> bien cuidada, sin renunciar a las funciones avanzadas del motor.

---

## Requisitos

- **Linux** con kernel 5.10+ (probado en CachyOS, Arch, Ubuntu 22.04+,
  Debian 12+, Fedora 36+).
- **QEMU 6.2+** (`qemu-system-x86_64`, `qemu-img`).
- **KVM** habilitado (`/dev/kvm` accesible).
- **Python 3.10+**.
- **PyQt6**, `requests`, `packaging` (se instalan automáticamente vía
  `run.sh`).

Opcionales según uso:

- `virtiofsd` para carpetas compartidas rápidas.
- `smbd` (Samba) para carpetas compartidas con Windows/macOS invitado.
- `swtpm` para TPM 2.0 (requerido por Windows 11).
- `dmg2img` para conversión del Recovery de macOS.
- `wmctrl` para subir al frente los visores externos al clic en la VM.
- `spicy` o `remote-viewer` para consola SPICE en ventana externa.
- `gvncviewer`, `vncviewer` o `remmina` para consola VNC en ventana
  externa.

---

## Instalación

```bash
git clone https://github.com/TU-USUARIO/virtual-machine.git
cd virtual-machine
./run.sh
```

El script `run.sh` verifica las dependencias de sistema, instala lo que
falta en `~/.local/` (sin tocar el Python del sistema) y arranca la app.
En el primer arranque, la app descarga OSX-KVM (para invitados macOS)
automáticamente si no está presente.

### Uso desde un entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install PyQt6 requests packaging
python3 virtual_machine.py
```

---

## Funcionalidades

### Gestión de VMs

- Crear, clonar, eliminar VMs con asistente guiado.
- Selección de versión de SO y descarga automática de ISO desde los
  espejos oficiales (Ubuntu, Debian, Fedora, Linux Mint, Arch, openSUSE,
  AlmaLinux, Rocky Linux, Pop!_OS; y Windows retail vía Fido).
- **Android-x86 / Bliss OS**: el usuario aporta la ISO. La app ajusta
  el hardware virtual (BIOS, chipset Q35, SATA/AHCI con degradación
  a IDE si i440FX, red e1000, gráficos QXL 2D) para que arranque sin
  configuración manual.
- Firmware BIOS o UEFI (OVMF), Secure Boot y TPM 2.0.
- Almacenamiento configurable: discos virtuales con distintos formatos
  (QCOW2, RAW, VDI, VMDK), unidades ópticas y orden de arranque.
- Red: múltiples adaptadores con modo NAT, bridge o TAP.
- Passthrough de hardware físico: PCI (VFIO) y USB con hotplug.
- Importar/Exportar VMs (carpeta, `.tar.gz`, `.zip`).

### Consola gráfica

- **VNC embebido** en la app (funciona en X11 y Wayland).
- **SPICE externo** con visor del sistema (`spicy`, `remote-viewer`).
- **Modo híbrido**: VNC dentro de la app + SPICE en ventana externa a
  la vez.
- **Ventana nativa de QEMU**: para gráficos con aceleración 3D
  (VirGL, Venus).
- Atajos globales, modo "tamaño real con scroll", reconexión manual y
  automática.

> Guía detallada: [`README_console.md`](README_console.md).

### Snapshots

- Snapshots de disco y snapshots completos (RAM + dispositivos + discos).
- Vista de organigrama con jerarquía configurable.
- Captura de pantalla automática al crear el snapshot.
- Panel persistente con la miniatura del último snapshot.

### Integración con el huésped

- QEMU Guest Agent.
- Carpetas compartidas VirtioFS/9p/SMB con automontaje.
- Clipboard bidireccional (con SPICE + `spice-vdagent` en el huésped).
- Detección del estado de `spice-vdagent` en el huésped.
- ISO de Guest Tools generada por la app, con scripts de instalación
  para Linux y Windows.

### Notas específicas de Android

- **ISO recomendada**: [Android-x86 9.0](https://www.android-x86.org/download.html)
  (probado). Para **Bliss OS** ([blissos.org](https://blissos.org/))
  se recomienda la variante genérica v15+ —no la «Bliss-Surface», que
  no arranca bajo QEMU—, con **≥8 GB de RAM, 4 núcleos y chipset Q35**.
- **No disponible**: carpetas compartidas (9p / VirtioFS), QEMU Guest
  Agent y clipboard bidireccional. Los kernels de Android-x86 / Bliss OS
  no incluyen esos módulos. Para pasar archivos usa ADB o la red.
- **Gráficos**: la app usa **Red Hat QXL 2D** por defecto, porque
  Android-x86 9.0 (kernel 4.9) no trae driver VirtIO-GPU y caería a un
  shell de rescate con `Detecting Android-x86...`. Las ISOs con kernel
  5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU y se puede elegir a mano.

### Diagnóstico

- Consola de progreso con filtros por nivel y búsqueda.
- Panel de "Salud de la VM" (procesos, Guest Agent, carpetas).
- Sugerencias contextuales (disco lleno, snapshots antiguos, RAM
  excesiva, PCI sin IOMMU, etc.).
- Watchdog que detecta caídas inesperadas de QEMU y muestra el motivo.

---

## Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+M` | Abrir menú de Medios (CD/DVD + USB) |
| `Ctrl+R` | Reconectar el widget VNC/SPICE |
| `Ctrl+Alt+C` | Alternar entre Consola Gráfica y la pestaña anterior |

---

## Portabilidad

**¿Por qué solo Linux?** La app depende de subsistemas específicos del
kernel Linux (VFIO, udev, `/proc`, `/sys`, cgroups, `systemd-inhibit`).
Portarla requiere abstraer toda esa capa en una interfaz común
(`HostAdapter`) y escribir una implementación por SO. Ese trabajo **no
está hecho** y no hay plan inmediato de hacerlo.

**¿Y macOS/Windows como huésped?** Eso es distinto y ya está soportado:
puedes instalar macOS (vía OpenCore/OSX-KVM) y Windows como sistema
invitado dentro de la VM sobre un host Linux.

**Si quieres portarla**:

- El camino es empezar por una capa de abstracción (`hosts/base.py`,
  `hosts/linux.py`, `hosts/darwin.py`, …). Está descrito en
  [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Las partes no portables (passthrough PCI, udev, VirtioFS) se
  deshabilitarían en otros SO con un aviso claro.
- Un PR que empiece por la capa abstracta (Fase A) sería muy
  bienvenido, aunque no complete la portabilidad.

---

## Créditos y agradecimientos

Este proyecto no existiría sin el trabajo previo de otros. Gracias a
todos los mantenedores y contribuyentes de los siguientes proyectos:

### Proyectos base

- **[OSX-KVM](https://github.com/kholia/OSX-KVM)** (kholia) — Licencia
  MIT. Base del flujo de virtualización de macOS/OpenCore. La carpeta
  `OSX-KVM/` se descarga automáticamente la primera vez que se ejecuta
  la app.

- **[QEMU](https://www.qemu.org/)** — Licencia GPLv2. Motor de
  virtualización subyacente. La app es un frontend gráfico sobre
  `qemu-system-x86_64`.

- **[pyQVNCWidget](https://github.com/zocker-160/pyQVNCWidget)** —
  Licencia MIT. Widget VNC para Qt del que se tomó la base del cliente
  VNC embebido. Portado a PyQt6 en `vnc_widget/`.

- **[python-xlib](https://github.com/python-xlib/python-xlib)** —
  Licencia LGPL v2.1+. Usado para capturar el teclado a nivel X11
  (Meta/Super, Ctrl+Alt+F*).

- **[spice-gtk](https://www.spice-space.org/)** — Licencia LGPL v2.1+.
  Base del cliente SPICE embebido.

- **[Fido](https://github.com/pbatard/Fido)** (pbatard) — Licencia MIT.
  Script de PowerShell para obtener los enlaces directos oficiales de
  Microsoft a las ISOs retail de Windows.

### Herramientas y librerías

- **[PyQt6](https://riverbankcomputing.com/software/pyqt/)** —
  Licencia GPLv3 o comercial.
- **[Requests](https://requests.readthedocs.io/)** — Licencia Apache 2.0.
- **[packaging](https://github.com/pypa/packaging)** — Licencia
  Apache 2.0 / BSD.

---

## Autoría y uso de IA

- **Autor principal**: Jimmy Verduga.
- **Desarrollo asistido por IA**: este proyecto ha sido desarrollado
  con la asistencia de los modelos **DeepSeek** (uso mayoritario),
  **ChatGPT** (OpenAI) y **Claude** (Anthropic).

### Reparto aproximado del trabajo

- **Diseño, arquitectura y decisiones de producto**: Jimmy Verduga.
- **Especificación de funcionalidades y requisitos**: Jimmy Verduga.
- **Revisión, prueba manual y validación final**: Jimmy Verduga.
- **Generación de código base, refactors y documentación**: asistida
  por IA, revisada y corregida por Jimmy Verduga.
- **Diagnóstico de errores y ajustes iterativos**: repartido entre
  Jimmy Verduga (ejecución y validación) y la IA (análisis y propuesta
  de soluciones).

### Transparencia

La IA se usó como herramienta de apoyo durante el desarrollo, no como
autora del proyecto. Los fragmentos adaptados de otros proyectos están
citados en la sección *Créditos*. El autor asume la responsabilidad
final del código y su comportamiento.

---

## Licencia

Este proyecto se distribuye bajo **GNU General Public License v3.0 o
posterior** (GPLv3+). Consulta el archivo [`LICENSE`](LICENSE) para el
texto completo.

### Por qué GPLv3

La aplicación usa **PyQt6** (Riverbank Computing), cuya licencia es
**dual: GPLv3 o comercial**. Al distribuir el proyecto bajo GPLv3
cumplimos con los términos de la versión gratuita de PyQt6.

Si necesitas integrar partes de este proyecto en software propietario:

1. **Aísla el componente** que te interese y reimplementa sin PyQt6 (o
   usa **PySide6**, que es LGPL).
2. **Adquiere una licencia comercial de PyQt6** y relicencia tu
   derivado como quieras.

### Resumen

- **Puedes**: usar la app, estudiarla, modificarla, redistribuirla,
  empaquetarla para tu distro.
- **Debes**: mantener la atribución y, si redistribuyes una versión
  modificada, publicar el código fuente bajo GPLv3.
- **No puedes**: vender una versión modificada como software
  propietario sin comprar la licencia comercial de PyQt6 o reescribir
  la parte de PyQt6.

---

## Contribuir

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md). Bugs, sugerencias y PRs son
bienvenidos. La suite de tests se ejecuta con:

```bash
./run_tests.sh
```

---

## Enlaces

- [Guía de la consola VNC/SPICE](README_console.md)
- [Changelog de mejoras](CHANGELOG.md)
- [Cómo contribuir](CONTRIBUTING.md)
