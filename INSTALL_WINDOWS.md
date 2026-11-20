# Instalación de Virtual.Machine en Windows
# ========================================

## Requisitos previos
- Windows 10 o Windows 11 (64 bits)
- Procesador con soporte para virtualización (Intel VT-x o AMD-V)
- Al menos 4 GB de RAM (8 GB recomendados)
- Conexión a internet para descargar dependencias

## Paso 1: Instalar dependencias del sistema

Ejecutar como Administrador:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\postinstall.ps1
```

Este script instala:
- QEMU para Windows (qemu-system-x86_64.exe)
- virt-viewer (visor SPICE/VNC)
- TightVNC (visor VNC)
- Python 3 y PyQt6

## Paso 2: Descargar o clonar el proyecto

```powershell
git clone https://github.com/jimmyverduga/NVM_harness_test.git
cd NVM_harness_test
```

O descargar el ZIP desde GitHub y extraerlo.

## Paso 3: Instalar dependencias de Python

```powershell
python -m pip install -r requirements.txt
```

## Paso 4: Ejecutar la aplicación

```powershell
python main.py
```

## Paso 5: Configurar el host

1. Ir a **Configuración Host** → **Diagnóstico**
2. Pulsar **Comprobar** para verificar que todo está instalado
3. Si falta algo, pulsar **Reparar** para lanzar el script de postinstalación

## Paso 6: Crear y arrancar una VM

1. Ir a **Configuración VM**
2. Pulsar **Nueva VM** y seguir el asistente
3. Seleccionar una ISO de instalación
4. Pulsar **Iniciar**

## Notas importantes para Windows

- **Aceleración**: La app usa WHPX (Windows Hypervisor Platform) si está disponible, o TCG (emulación pura) como fallback. WHPX es mucho más rápido.
- **WHPX**: Requiere habilitar "Plataforma de hipervisor de Windows" en Características de Windows.
- **Passthrough de GPU/USB**: No soportado en Windows (requiere Linux con vfio-pci).
- **Desktop Mode**: Eliminado de esta versión (era específico de Linux con Xorg/VT).
- **Guest Agent**: El montaje automático de carpetas compartidas requiere qemu-guest-agent en el invitado (solo Linux invitado).

## Desinstalación

Ejecutar el desinstalador desde el Panel de Control, o borrar manualmente:
- Carpeta de instalación
- `%LOCALAPPDATA%\VirtualMachine` (datos de las VMs)
