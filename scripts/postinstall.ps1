# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
#
# scripts/postinstall.ps1 - Instalador y reparador del host para Windows.
# Marcador: postinstall_win_v1
#
# Hace TODO lo que requiere administracion en un solo paso idempotente:
#   1) Instala QEMU y el visor de consola (via winget/chocolatey). Python y
#      PyQt6 NO se instalan aqui: el ejecutable de la app ya los incluye.
#   2) Configura reglas de firewall para QEMU.
#   3) Crea las reglas de sudo no necesarias en Windows (se usa manifest de elevacion).
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts/postinstall.ps1
#   (Ejecutar como Administrador)
#
# Pensado para ser invocado por:
#   * El instalador del paquete para Windows (.msi / Inno Setup / NSIS) - en su postinstall.
#   * El boton "Reparar lo que falte" de Configuracion Host.

$ErrorActionPreference = "Continue"
$MARKER = "postinstall_win_v1"

Write-Host "==> Postinstall Windows $MARKER iniciado."

# ----------------------------------------------------------------------
# Detectar gestor de paquetes disponible
# ----------------------------------------------------------------------
$haveWinget = Get-Command winget -ErrorAction SilentlyContinue
$haveChoco  = Get-Command choco -ErrorAction SilentlyContinue

if (-not $haveWinget -and -not $haveChoco) {
    Write-Warning "No se encontro winget ni chocolatey. Se omitira la instalacion de paquetes."
}

# ----------------------------------------------------------------------
# Paquetes necesarios para Windows
# ----------------------------------------------------------------------
# IDs reales del repositorio de winget (y su equivalente en chocolatey).
$packages = @(
    @{ Winget = "SoftwareFreedomConservancy.QEMU"; Choco = "qemu" },
    @{ Winget = "RedHat.VirtViewer";                Choco = "virt-viewer" }
)

function Install-Package {
    param([string]$WingetId, [string]$ChocoId)
    if ($haveWinget) {
        # winget devuelve distinto de 0 cuando el paquete ya esta instalado,
        # asi que comprobar primero para no tratar eso como un fallo.
        $instalado = winget list --exact --id "$WingetId" 2>$null
        if ($instalado -match [regex]::Escape($WingetId)) {
            Write-Host "OK $WingetId ya esta instalado."
            return
        }
        Write-Host "==> Instalando $WingetId via winget..."
        winget install --exact --id "$WingetId" --source winget `
            --accept-source-agreements --accept-package-agreements -h 2>$null
        if ($LASTEXITCODE -eq 0) { return }
        Write-Warning "winget no pudo instalar $WingetId; se probara chocolatey."
    }
    if ($haveChoco) {
        Write-Host "==> Instalando $ChocoId via chocolatey..."
        choco install "$ChocoId" -y 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "chocolatey no pudo instalar $ChocoId"
        }
    }
}

foreach ($pkg in $packages) {
    Install-Package -WingetId $pkg.Winget -ChocoId $pkg.Choco
}

# ----------------------------------------------------------------------
# Buscar qemu-system-x86_64.exe en rutas comunes de Windows
# ----------------------------------------------------------------------
$qemuPaths = @(
    "C:\Program Files\qemu\qemu-system-x86_64.exe",
    "C:\Program Files\QEMU\qemu-system-x86_64.exe",
    "C:\Program Files (x86)\qemu\qemu-system-x86_64.exe",
    "C:\Program Files (x86)\QEMU\qemu-system-x86_64.exe",
    (Get-Command qemu-system-x86_64.exe -ErrorAction SilentlyContinue).Source
)

$qemuFound = $false
$qemuExe = $null
foreach ($p in $qemuPaths) {
    if ($p -and (Test-Path $p)) {
        Write-Host "OK QEMU encontrado en: $p"
        $qemuFound = $true
        $qemuExe = $p
        break
    }
}

if (-not $qemuFound) {
    Write-Warning "QEMU no encontrado en rutas comunes. Instalalo manualmente o verifica el PATH."
} else {
    # QEMU no siempre anade su carpeta al PATH (winget/MSI/descompresion manual).
    $qemuDir = Split-Path $qemuExe -Parent
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$qemuDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$qemuDir", "User")
        $env:Path += ";$qemuDir"
        Write-Host "OK Anadido al PATH del usuario: $qemuDir"
    }
    $imgExe = Join-Path $qemuDir "qemu-img.exe"
    if (Test-Path $imgExe) {
        Write-Host "OK qemu-img.exe encontrado en: $imgExe"
    } else {
        Write-Warning "No se encontro qemu-img.exe junto a $qemuExe. La app lo buscara en esa carpeta de todas formas."
    }
}

# ----------------------------------------------------------------------
# Anadir VirtViewer (remote-viewer.exe) al PATH del usuario
# ----------------------------------------------------------------------
$viewerExe = Get-ChildItem `
    "C:\Program Files\VirtViewer*\bin\remote-viewer.exe",
    "C:\Program Files (x86)\VirtViewer*\bin\remote-viewer.exe" `
    -ErrorAction SilentlyContinue | Select-Object -First 1

if ($viewerExe) {
    Write-Host "OK Visor SPICE encontrado en: $($viewerExe.FullName)"
    $viewerDir = Split-Path $viewerExe.FullName -Parent
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$viewerDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$viewerDir", "User")
        $env:Path += ";$viewerDir"
        Write-Host "OK Anadido al PATH del usuario: $viewerDir"
    }
} else {
    Write-Warning "remote-viewer.exe no encontrado. El modo SPICE externo no podra abrir la consola."
}

# ----------------------------------------------------------------------
# Configurar firewall para QEMU (puertos VNC 5900-6000, SPICE 5930-6000)
# ----------------------------------------------------------------------
Write-Host "==> Configurando reglas de firewall para QEMU..."

$fwRules = @(
    @{Name = "VM-Manager VNC"; Ports = "5900-6000"; Proto = "TCP"},
    @{Name = "VM-Manager SPICE"; Ports = "5930-6000"; Proto = "TCP"}
)

foreach ($rule in $fwRules) {
    $exists = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if (-not $exists) {
        New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Protocol $rule.Proto -LocalPort $rule.Ports -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
        if ($?) {
            Write-Host "OK Regla de firewall creada: $($rule.Name)"
        } else {
            Write-Warning "No se pudo crear la regla de firewall: $($rule.Name)"
        }
    } else {
        Write-Host "OK Regla de firewall ya existe: $($rule.Name)"
    }
}

# ----------------------------------------------------------------------
# Crear directorio de datos de la aplicacion
# ----------------------------------------------------------------------
$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$dataDir = Join-Path $localAppData "VirtualMachine"
$vmsDir = Join-Path $dataDir "vms"
$isosDir = Join-Path $dataDir "isos"

foreach ($dir in @($dataDir, $vmsDir, $isosDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force 2>$null
        Write-Host "OK Directorio creado: $dir"
    }
}

# ----------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------
Write-Host ""
Write-Host "==> Postinstall Windows $MARKER completado."
Write-Host ""
Write-Host "Notas:"
Write-Host "  - Si instalaste QEMU manualmente, asegurate de que qemu-system-x86_64.exe este en el PATH."
Write-Host "  - Para GPU passthrough en Windows, se requiere configuracion adicional de Hyper-V/WHPX."
Write-Host "  - Vuelve a Configuracion Host y pulsa 'Comprobar' para verificar el estado."
Write-Host ""
