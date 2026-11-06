; Inno Setup script: packs the Windows build (dist\desktop\AstaLaVista) into one Setup .exe.
; The release workflow runs it after ./bin/build-desktop:
;
;   iscc /DVersion=0.4.0 desktop\installer.iss   -> dist\installer\AstaLaVista-0.4.0-windows-setup.exe
;
; It installs for the current user only, so it needs no administrator password, and the data
; folder (%APPDATA%\Asta la Vista) is never touched: uninstalling keeps the user's auctions.

#ifndef Version
  #error Pass the version: iscc /DVersion=x.y.z desktop\installer.iss
#endif

#define AppName "Asta la Vista"
#define AppExe "AstaLaVista.exe"

[Setup]
; Identifies the app across versions, so a new installer updates the existing installation.
; Never change it.
AppId={{B465494F-A456-435C-BFD8-B53EF0F31759}
AppName={#AppName}
AppVersion={#Version}
AppPublisher=fedeRizzi04
AppPublisherURL=https://github.com/fedeRizzi04/asta-la-vista
; For a current-user install this is %LOCALAPPDATA%\Programs\Asta la Vista.
DefaultDirName={autopf}\{#AppName}
PrivilegesRequired=lowest
; No folder choice: without administrator rights, a folder like Program Files cannot be written
; ("Errore 5: Accesso negato"). Updates reuse the folder of the previous installation.
DisableDirPage=yes
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
OutputDir=..\dist\installer
OutputBaseFilename=AstaLaVista-{#Version}-windows-setup

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; An update replaces the bundled libraries entirely, so no file of the old version is left behind
; (two copies of the app's metadata would make it report either version). This runs before the
; copy and a cancelled update does not restore it, but neither would it restore overwritten files:
; running the installer again repairs the app either way, and the data folder is not involved.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\desktop\AstaLaVista\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
