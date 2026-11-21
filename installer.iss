; Script de Inno Setup para Virtual.Machine
; Generar instalador .exe para Windows

#define MyAppName "Virtual.Machine"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jimmy Verduga"
#define MyAppURL "https://github.com/jverduga1969/virtual-machine"
#define MyAppExeName "VirtualMachine.exe"

[Setup]
AppId={{E3F2A1B0-4C5D-6E7F-8A9B-0C1D2E3F4A5B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=Yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=VirtualMachine-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=Yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalTasks}"; Flags: unchecked

[Files]
; PyInstaller genera un único ejecutable (EXE con a.binaries/a.datas incluidos).
Source: "dist\VirtualMachine.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\postinstall.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "Fido.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; El instalador ya se ejecuta elevado (instala en {autopf}), así que el
; postinstall hereda el token de administrador para winget y el firewall.
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\postinstall.ps1"""; Description: "Instalar requisitos del host (QEMU, visores y firewall)"; Flags: postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, "&", "&&")}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
