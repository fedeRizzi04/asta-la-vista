# Updates an installation made in a folder chosen by the user, as version 0.4.0 allowed: Setup
# must uninstall it and install in the default folder. It starts, installs and removes the app of
# the current user and writes in their data folder, so it is meant for a throwaway CI runner.
#
#   ./bin/test-windows-update.ps1 -Setup <setup.exe> -OldDir <folder>
#
# An older version must be installed in <folder> already (the release workflow installs 0.4.0
# there). Removing a copy that needs administrator rights is not covered.

param(
    [Parameter(Mandatory)] [string] $Setup,
    [Parameter(Mandatory)] [string] $OldDir
)

$ErrorActionPreference = "Stop"

$key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{B465494F-A456-435C-BFD8-B53EF0F31759}_is1"
$newDir = "$env:LOCALAPPDATA\Programs\Asta la Vista"
$dataDir = "$env:APPDATA\Asta la Vista"
$database = "$dataDir\asta-la-vista.sqlite3"
$shortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Asta la Vista.lnk"
$setupLog = Join-Path ([IO.Path]::GetTempPath()) "asta-la-vista-setup.log"
$setupExitStoppedBeforeInstalling = 7

function Assert([bool] $condition, [string] $message) {
    if (-not $condition) { throw $message }
}

function Get-InstallFolder {
    (Get-ItemProperty -LiteralPath $key)."Inno Setup: App Path"
}

function Invoke-Setup {
    $process = Start-Process -Wait -PassThru $Setup `
        -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/LOG=`"$setupLog`""
    $process.ExitCode
}

# The installer script writes this line in the log of Setup when it runs an old uninstaller.
function Test-UninstallerRun {
    [bool] (Select-String -LiteralPath $setupLog -SimpleMatch "The uninstaller in " -Quiet)
}

function Assert-OldCopyKept([int] $exitCode) {
    Assert ($exitCode -eq $setupExitStoppedBeforeInstalling) "Setup ended with $exitCode"
    Assert (Test-Path -LiteralPath "$OldDir\AstaLaVista.exe") "The old copy is gone"
    Assert ((Get-InstallFolder) -eq $OldDir) "The registered folder changed"
    Assert (-not (Test-Path -LiteralPath $newDir)) "Something was installed in '$newDir'"
}

function Assert-Updated([int] $exitCode) {
    Assert ($exitCode -eq 0) "Setup ended with $exitCode"
    Assert ((Get-InstallFolder) -eq $newDir) "The app is registered in '$(Get-InstallFolder)'"
    Assert (Test-Path -LiteralPath "$newDir\AstaLaVista.exe") "No app in '$newDir'"
    # Both copies use this shortcut: it is missing if the old one was uninstalled afterwards.
    Assert (Test-Path -LiteralPath $shortcut) "No Start menu shortcut"
    $target = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcut).TargetPath
    Assert ($target -eq "$newDir\AstaLaVista.exe") "The shortcut opens '$target'"
}

$app = $null
$passed = $false
try {
    # Without these, the test could pass without testing anything.
    Assert ((Get-InstallFolder) -eq $OldDir) "The app is registered in '$(Get-InstallFolder)'"
    Assert (-not (Test-Path -LiteralPath $newDir)) "'$newDir' exists before the update"
    Assert (-not (Test-Path -LiteralPath "$dataDir\instance.json")) "An earlier run left instance.json"

    Write-Host "Updating while the old copy is open..."
    $app = Start-Process -PassThru "$OldDir\AstaLaVista.exe" -ArgumentList "--headless"
    for ($second = 0; -not (Test-Path -LiteralPath "$dataDir\instance.json"); $second++) {
        Assert (-not $app.HasExited) "The app exited during startup"
        Assert ($second -lt 120) "The app did not start"
        Start-Sleep -Seconds 1
    }
    Assert-OldCopyKept (Invoke-Setup)
    Stop-Process -Id $app.Id
    $app.WaitForExit()
    $data = (Get-FileHash -LiteralPath $database).Hash

    Write-Host "Updating when the old copy cannot be uninstalled..."
    # Without its data file the uninstaller does nothing, as when its permission request is refused.
    Rename-Item -LiteralPath "$OldDir\unins000.dat" "unins000.dat.hidden"
    Assert-OldCopyKept (Invoke-Setup)
    Rename-Item -LiteralPath "$OldDir\unins000.dat.hidden" "unins000.dat"

    Write-Host "Updating..."
    Assert-Updated (Invoke-Setup)
    Assert (Test-UninstallerRun) "The log does not show the old uninstaller"
    Assert (-not (Test-Path -LiteralPath $OldDir)) "The old folder is still there"

    Write-Host "Updating the copy in the default folder..."
    Assert-Updated (Invoke-Setup)
    Assert (-not (Test-UninstallerRun)) "Setup uninstalled the copy it was updating"

    Assert ((Get-FileHash -LiteralPath $database).Hash -eq $data) "The database changed"
    $passed = $true
    Write-Host "Update test passed."
}
finally {
    if ($app -and -not $app.HasExited) { Stop-Process -Id $app.Id }
    if (-not $passed -and (Test-Path -LiteralPath $setupLog)) {
        Write-Host "--- log of the last Setup run ---"
        Get-Content -LiteralPath $setupLog
    }
}
