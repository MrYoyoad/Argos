# =====================================================
# VSP Pipeline — install launcher + desktop shortcut (Windows)
# =====================================================
# Place this kit's launcher under C:\vsp\launcher\ and create a desktop
# shortcut pointing at it. Idempotent — safe to re-run.
#
# Usage (from Admin PowerShell): .\install_launcher.ps1
# =====================================================

$ErrorActionPreference = "Stop"

# Require admin for system-wide install
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "ERROR: Run from an Administrator PowerShell window."
    exit 1
}

$KitDir = $PSScriptRoot
$Prefix = "C:\vsp\launcher"

Write-Host "Installing VSP launcher into $Prefix..."
New-Item -ItemType Directory -Force -Path $Prefix | Out-Null

# --- Copy launcher artifacts ---
Copy-Item -Force -Path (Join-Path $KitDir "vsp-pipeline.ps1") -Destination "$Prefix\vsp-pipeline.ps1"
Copy-Item -Force -Path (Join-Path $KitDir "image.tag")        -Destination "$Prefix\image.tag"
foreach ($f in @("apply_update.ps1","rollback.ps1","vsp-icon.ico")) {
    $src = Join-Path $KitDir $f
    if (Test-Path $src) { Copy-Item -Force -Path $src -Destination "$Prefix\$f" }
}

# --- Desktop shortcut for the current (Admin's) user — adjust as needed ---
$DesktopUser = if ($env:SUDO_USER) { $env:SUDO_USER } else { $env:USERNAME }
$DesktopPath = "$env:USERPROFILE\Desktop\VSP Pipeline.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($DesktopPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Prefix\vsp-pipeline.ps1`""
$Shortcut.WorkingDirectory = $Prefix
$Shortcut.Description = "Run the visual speech recognition pipeline on a folder of videos"
if (Test-Path "$Prefix\vsp-icon.ico") {
    $Shortcut.IconLocation = "$Prefix\vsp-icon.ico"
}
$Shortcut.Save()

Write-Host "Desktop shortcut placed at: $DesktopPath"
Write-Host "Image tag: $((Get-Content $Prefix\image.tag).Trim())"
Write-Host ""
Write-Host "Done. Next: run ..\checks\post_install_check.ps1 to verify."
