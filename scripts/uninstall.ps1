# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
#
# scripts/uninstall.ps1 - Limpieza de los cambios del postinstall de Windows.
# Marcador: postinstall_win_v1
#
# Se ejecuta desde Inno Setup ([UninstallRun]) antes de borrar {app}.
# No desinstala QEMU ni borra datos: solo retira lo que postinstall.ps1
# anadio al PATH del usuario y sus reglas de firewall.

$ErrorActionPreference = "Stop"
$MARKER = "postinstall_win_v1"

Write-Host "==> Limpiando cambios de Virtual.Machine ($MARKER)."

# ----------------------------------------------------------------------
# PATH del usuario: solo las rutas que guardo el postinstall
# ----------------------------------------------------------------------
$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$dataDir = Join-Path $localAppData "VirtualMachine"
$pathDirsFile = Join-Path $dataDir "postinstall-paths.txt"

if (Test-Path $pathDirsFile) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $entries = @()
    if ($userPath) { $entries = $userPath -split ';' }

    foreach ($dir in (Get-Content -Path $pathDirsFile -ErrorAction SilentlyContinue)) {
        if (-not $dir) { continue }
        $nuevas = @()
        foreach ($entry in $entries) {
            if ($entry.TrimEnd('\') -ieq $dir.TrimEnd('\')) { continue }
            $nuevas += $entry
        }
        $entries = $nuevas
    }

    $limpio = ($entries | Where-Object { $_ }) -join ';'
    try {
        [Environment]::SetEnvironmentVariable("Path", $limpio, "User")
        Write-Host "OK Entradas del PATH del usuario retiradas."
    } catch {
        Write-Warning "No se pudo limpiar el PATH del usuario: $($_.Exception.Message)"
    }
    try {
        Remove-Item -Path $pathDirsFile -Force -ErrorAction Stop
    } catch {
        Write-Warning "No se pudo borrar $pathDirsFile : $($_.Exception.Message)"
    }
} else {
    Write-Host "OK No hay historial de PATH que limpiar."
}

# ----------------------------------------------------------------------
# Firewall: solo reglas creadas por este programa
# ----------------------------------------------------------------------
foreach ($nombre in @("VM-Manager QEMU local", "VM-Manager VNC", "VM-Manager SPICE")) {
    if (Get-NetFirewallRule -DisplayName $nombre -ErrorAction SilentlyContinue) {
        try {
            Remove-NetFirewallRule -DisplayName $nombre -ErrorAction Stop
            Write-Host "OK Regla de firewall eliminada: $nombre"
        } catch {
            Write-Warning "No se pudo eliminar la regla $nombre : $($_.Exception.Message)"
        }
    }
}

Write-Host "==> Limpieza completada. Los datos de VMs se han conservado."
exit 0
