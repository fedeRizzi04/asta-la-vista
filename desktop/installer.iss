; Inno Setup script: packs the Windows build (dist\desktop\AstaLaVista) into one Setup .exe.
; The release workflow runs it after ./bin/build-desktop:
;
;   iscc /DVersion=0.4.0 desktop\installer.iss   -> dist\installer\AstaLaVista-0.4.0-windows-setup.exe
;
; It installs for the current user only, so it needs no administrator password. The user's data
; (%APPDATA%\Asta la Vista) is never touched: uninstalling keeps the auctions.

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
; ("Access denied"). For the same reason an update does not reuse the folder of the previous
; installation, which version 0.4.0 let the user choose (Setup would reuse it even with the folder
; page hidden): a copy found in another folder is uninstalled first, see [Code].
DisableDirPage=yes
UsePreviousAppDir=no
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
OutputDir=..\dist\installer
OutputBaseFilename=AstaLaVista-{#Version}-windows-setup
; Setup follows the language of Windows and asks only if it has no match below. An update reuses
; the language of the previous installation.
ShowLanguageDialog=auto

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; An update replaces the bundled libraries entirely, so no old library is left in the folder
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

[CustomMessages]
en.CloseAppFirst={#AppName} is open. Close it, then run this installer again.
it.CloseAppFirst={#AppName} è aperta. Chiudila, poi avvia di nuovo l'installazione.
en.OldCopyNotRemoved=The previous installation in %1 could not be removed. Run this installer again and, if Windows asks for permission to remove it, allow it.
it.OldCopyNotRemoved=Non è stato possibile rimuovere la precedente installazione in %1. Avvia di nuovo l'installazione e, se Windows chiede il permesso di rimuoverla, consentilo.

[Code]
// Uninstalls a copy registered in another folder before this one is installed. The order matters:
// both copies share the "Installed apps" entry and the names of the shortcuts, so the old
// uninstaller, if run afterwards, would remove those of the new copy. It asks for administrator
// rights by itself if that copy needs them. Returning a message stops Setup with nothing installed.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Key, OldDir, Uninstaller, LockFile: String;
  ResultCode: Integer;
begin
  Result := '';
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B465494F-A456-435C-BFD8-B53EF0F31759}_is1';
  if not RegQueryStringValue(HKCU, Key, 'Inno Setup: App Path', OldDir) or
    not RegQueryStringValue(HKCU, Key, 'UninstallString', Uninstaller) then
    Exit;
  Uninstaller := RemoveQuotes(Uninstaller);
  // Nothing to run if the user has already deleted the old folder by hand.
  if (CompareText(OldDir, ExpandConstant('{app}')) = 0) or not FileExists(Uninstaller) then
    Exit;

  // The files of a running copy cannot be removed. The app keeps this file open while it runs,
  // so it cannot be deleted then; otherwise deleting it is harmless, each launch creates it.
  LockFile := ExpandConstant('{userappdata}\{#AppName}\instance.lock');
  if FileExists(LockFile) and not DeleteFile(LockFile) then
  begin
    Result := CustomMessage('CloseAppFirst');
    Exit;
  end;

  // The result is judged by what is left: the uninstaller can report success with files left.
  if Exec(Uninstaller, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_SHOWNORMAL,
    ewWaitUntilTerminated, ResultCode) then
    Log(Format('The uninstaller in %s ended with code %d', [OldDir, ResultCode]))
  else
    Log(Format('The uninstaller in %s did not start: %s', [OldDir, SysErrorMessage(ResultCode)]));
  if FileExists(AddBackslash(OldDir) + '{#AppExe}') then
    Result := FmtMessage(CustomMessage('OldCopyNotRemoved'), [OldDir]);
end;
