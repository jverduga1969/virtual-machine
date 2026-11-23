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
#   3) Prepara firewall y directorios de datos. La eleva la UI con
#      Start-Process -Verb RunAs o el instalador, no un manifest.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts/postinstall.ps1
#   (Ejecutar como Administrador)
#
# Pensado para ser invocado por:
#   * El instalador del paquete para Windows (.msi / Inno Setup / NSIS) - en su postinstall.
#   * El boton "Reparar lo que falte" de Configuracion Host.

$ErrorActionPreference = "Stop"
$MARKER = "postinstall_win_v1"
$errores = @()
# Directorios que este script anade al PATH del usuario. Se guardan para que
# uninstall.ps1 pueda retirar solo lo que nosotros anadimos.
$pathDirs = @()

function Add-Error {
    param([string]$Mensaje)
    # Write-Error + ErrorActionPreference=Stop lanzaria una excepcion aqui y
    # el script terminaria antes de mostrar el resumen. Escribimos en stderr
    # sin lanzar y dejamos que el exit 1 final informe del resultado real.
    [Console]::Error.WriteLine("ERROR: $Mensaje")
    $script:errores += $Mensaje
}

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
    "$env:ProgramFiles\qemu\qemu-system-x86_64.exe",
    "$env:ProgramFiles\QEMU\qemu-system-x86_64.exe",
    "${env:ProgramFiles(x86)}\qemu\qemu-system-x86_64.exe",
    "${env:ProgramFiles(x86)}\QEMU\qemu-system-x86_64.exe",
    "$env:LOCALAPPDATA\Programs\QEMU\qemu-system-x86_64.exe",
    "$env:ProgramData\chocolatey\bin\qemu-system-x86_64.exe",
    "$env:USERPROFILE\scoop\apps\qemu\current\qemu-system-x86_64.exe",
    "$env:QEMU_DIR\qemu-system-x86_64.exe",
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
    Add-Error "QEMU no encontrado. Instala SoftwareFreedomConservancy.QEMU o configura QEMU_DIR."
} else {
    # QEMU no siempre anade su carpeta al PATH (winget/MSI/descompresion manual).
    $qemuDir = Split-Path $qemuExe -Parent
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$qemuDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$qemuDir", "User")
        $env:Path += ";$qemuDir"
        $pathDirs += $qemuDir
        Write-Host "OK Anadido al PATH del usuario: $qemuDir"
    }
    $imgExe = Join-Path $qemuDir "qemu-img.exe"
    if (Test-Path $imgExe) {
        Write-Host "OK qemu-img.exe encontrado en: $imgExe"
    } else {
        Add-Error "No se encontro qemu-img.exe junto a $qemuExe. Lo necesitan los snapshots, ISOs y OVF."
    }
}

# ----------------------------------------------------------------------
# Anadir VirtViewer (remote-viewer.exe) al PATH del usuario
# ----------------------------------------------------------------------
$viewerCandidates = @()
$viewerCandidates += Get-ChildItem `
    "C:\Program Files\VirtViewer*\bin\remote-viewer.exe",
    "C:\Program Files (x86)\VirtViewer*\bin\remote-viewer.exe" `
    -ErrorAction SilentlyContinue
$viewerCmd = Get-Command remote-viewer.exe -ErrorAction SilentlyContinue
if ($viewerCmd) { $viewerCandidates += $viewerCmd }
foreach ($p in @(
    "$env:ProgramData\chocolatey\bin\remote-viewer.exe",
    "$env:USERPROFILE\scoop\apps\virt-viewer\current\bin\remote-viewer.exe"
)) {
    $item = Get-Item $p -ErrorAction SilentlyContinue
    if ($item) { $viewerCandidates += $item }
}
$viewerExe = $viewerCandidates | Select-Object -First 1
$viewerPath = $null
if ($viewerExe) {
    $viewerPath = $viewerExe.Source
    if (-not $viewerPath) { $viewerPath = $viewerExe.FullName }
}

if ($viewerPath) {
    Write-Host "OK Visor SPICE encontrado en: $viewerPath"
    $viewerDir = Split-Path $viewerPath -Parent
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$viewerDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$viewerDir", "User")
        $env:Path += ";$viewerDir"
        $pathDirs += $viewerDir
        Write-Host "OK Anadido al PATH del usuario: $viewerDir"
    }
} else {
    Write-Warning "remote-viewer.exe no encontrado. El modo SPICE externo no podra abrir la consola."
}

# ----------------------------------------------------------------------
# WHPX: activar de verdad la plataforma de hipervisor de Windows
# ----------------------------------------------------------------------
# La app comprueba WHPX con WinHVPlatform.dll. Si la caracteristica del
# sistema esta desactivada, QEMU solo puede usar HAX/TCG. La activacion no
# es imprescindible para arrancar, asi que un fallo es aviso, no error fatal.
Write-Host "==> Comprobando WHPX (HypervisorPlatform)..."
try {
    $feature = Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -ErrorAction Stop
    if ($feature.State -eq "Enabled") {
        Write-Host "OK WHPX ya esta habilitado."
    } else {
        Write-Host "==> Habilitando HypervisorPlatform con DISM..."
        $resultado = Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart -ErrorAction Stop
        if ($resultado -and $resultado.RestartNeeded) {
            Write-Warning "WHPX habilitado. Reinicia Windows para que QEMU pueda usarlo."
        } else {
            Write-Host "OK WHPX habilitado."
        }
    }
} catch {
    Write-Warning "No se pudo habilitar WHPX: $($_.Exception.Message)"
    Write-Warning "La app seguira funcionando con HAX o con TCG (lento)."
}

# ----------------------------------------------------------------------
# Firewall: las consolas escuchan en 127.0.0.1, sin abrir rangos de puertos
# ----------------------------------------------------------------------
Write-Host "==> Acotando reglas de firewall para QEMU..."

# Versiones anteriores abrian 5900-6000 y 5930-6000 a todos los perfiles.
# Se retiran porque el runner enlaza VNC/SPICE solo a localhost.
foreach ($nombre in @("VM-Manager VNC", "VM-Manager SPICE")) {
    if (Get-NetFirewallRule -DisplayName $nombre -ErrorAction SilentlyContinue) {
        try {
            Remove-NetFirewallRule -DisplayName $nombre -ErrorAction Stop
            Write-Host "OK Regla amplia eliminada: $nombre"
        } catch {
            Write-Warning "No se pudo eliminar la regla $nombre : $($_.Exception.Message)"
        }
    }
}

if ($qemuExe) {
    $nombreRegla = "VM-Manager QEMU local"
    try {
        if (-not (Get-NetFirewallRule -DisplayName $nombreRegla -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $nombreRegla -Direction Inbound `
                -Program $qemuExe -Action Allow -Profile Private `
                -RemoteAddress LocalSubnet -ErrorAction Stop | Out-Null
            Write-Host "OK Regla acotada creada para QEMU (perfil privado, subred local)."
        } else {
            Write-Host "OK Regla acotada de QEMU ya existe."
        }
    } catch {
        Write-Warning "No se pudo crear la regla acotada de QEMU: $($_.Exception.Message)"
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
        try {
            New-Item -ItemType Directory -Path $dir -Force -ErrorAction Stop | Out-Null
            Write-Host "OK Directorio creado: $dir"
        } catch {
            Add-Error "No se pudo crear el directorio $dir"
        }
    }
}

# Guardamos solo los directorios que este script anadio al PATH, para que
# uninstall.ps1 no borre entradas de otros programas.
$pathDirsFile = Join-Path $dataDir "postinstall-paths.txt"
try {
    $pathDirs | Where-Object { $_ } | Sort-Object -Unique | Set-Content -Path $pathDirsFile -Encoding ASCII
    Write-Host "OK Historial de PATH guardado en: $pathDirsFile"
} catch {
    Write-Warning "No se pudo guardar el historial de PATH: $($_.Exception.Message)"
}

# ----------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------
Write-Host ""

if ($script:errores.Count -gt 0) {
    Write-Host "==> Postinstall Windows $MARKER termino con $($script:errores.Count) error(es):"
    foreach ($err in $script:errores) { Write-Host "  - $err" }
    exit 1
}

Write-Host "==> Postinstall Windows $MARKER completado."
Write-Host ""
Write-Host "Notas:"
Write-Host "  - Si instalaste QEMU manualmente, asegurate de que qemu-system-x86_64.exe este en el PATH."
Write-Host "  - Para aceleracion WHPX activa la caracteristica HypervisorPlatform y reinicia."
Write-Host "  - Reinicia la app para que el PATH y las rutas nuevas surtan efecto."
Write-Host "  - Vuelve a Configuracion Host y pulsa 'Comprobar' para verificar el estado."
Write-Host ""
exit 0
