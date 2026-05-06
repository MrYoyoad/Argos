# =====================================================
# VSP Pipeline — Diagnostics bundle (Windows)
# =====================================================
# Air-gapped equivalent of "phone home". Bundles host info + logs.
# Usage: .\collect_diagnostics.ps1
# Output: vsp-diagnostics-<host>-<ts>.zip in the kit directory.
# =====================================================

$ErrorActionPreference = "Continue"

$KitDir = $PSScriptRoot
$TS = Get-Date -Format "yyyyMMdd_HHmmssZ"
$Host = $env:COMPUTERNAME
$Bundle = "vsp-diagnostics-$Host-$TS"
$Work = Join-Path $env:TEMP "$Bundle.work"
$Target = Join-Path $Work $Bundle
New-Item -ItemType Directory -Force -Path $Target | Out-Null

Write-Host "Collecting VSP diagnostics into $Bundle.zip..."

# Host info
@"
=== Get-CimInstance Win32_OperatingSystem ===
$(Get-CimInstance Win32_OperatingSystem | Format-List | Out-String)
=== Get-CimInstance Win32_ComputerSystem ===
$(Get-CimInstance Win32_ComputerSystem | Format-List | Out-String)
=== wsl --version ===
$(wsl --version 2>&1 | Out-String)
=== Date ===
$(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
"@ | Set-Content (Join-Path $Target "host_info.txt")

# GPU + driver
@"
=== nvidia-smi ===
$(& nvidia-smi 2>&1 | Out-String)
=== nvidia-smi -q ===
$(& nvidia-smi -q 2>&1 | Out-String)
"@ | Set-Content (Join-Path $Target "nvidia.txt")

# Disk + memory
@"
=== Get-PSDrive ===
$(Get-PSDrive | Where-Object { $_.Provider.Name -eq 'FileSystem' } | Format-Table | Out-String)
=== Memory ===
$(Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize | Format-List | Out-String)
"@ | Set-Content (Join-Path $Target "sys.txt")

# Docker
@"
=== docker version ===
$(& docker version 2>&1 | Out-String)
=== docker info ===
$(& docker info 2>&1 | Out-String)
=== docker images ===
$(& docker images 2>&1 | Out-String)
=== docker ps -a ===
$(& docker ps -a 2>&1 | Out-String)
"@ | Set-Content (Join-Path $Target "docker.txt")

# Pre/post install logs + reports
foreach ($f in @("pre_install_check.log", "post_install_check.log", "INSTALL_REPORT.txt")) {
    $src = Join-Path $KitDir $f
    if (Test-Path $src) { Copy-Item $src $Target }
}

# Image tag snapshots
foreach ($f in @("C:\vsp\launcher\image.tag", (Join-Path (Split-Path $KitDir -Parent) "launcher\image.tag"))) {
    if (Test-Path $f) {
        Copy-Item $f (Join-Path $Target "image.tag.$(($f -replace '[\\:]','_')).snapshot")
    }
}

# Recent run outputs (small text files only)
$outBase = if ($env:VSP_OUTPUT_DIR) { $env:VSP_OUTPUT_DIR } else { "$env:USERPROFILE\vsp-output" }
if (Test-Path $outBase) {
    $recentOut = Join-Path $Target "recent_outputs"
    New-Item -ItemType Directory -Force -Path $recentOut | Out-Null
    Get-ChildItem -Directory $outBase | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object {
        $runDest = Join-Path $recentOut $_.Name
        New-Item -ItemType Directory -Force -Path $runDest | Out-Null
        Get-ChildItem -Path $_.FullName -Recurse -Include *.csv,*.json,*.log,*.txt,*.html `
          | Where-Object { $_.Length -lt 2MB } `
          | ForEach-Object { Copy-Item $_.FullName -Destination $runDest -ErrorAction SilentlyContinue }
    }
}

# Bundle as ZIP (Windows-native, no tar)
$Zip = Join-Path $KitDir "$Bundle.zip"
if (Test-Path $Zip) { Remove-Item $Zip }
Compress-Archive -Path $Target -DestinationPath $Zip
Remove-Item -Recurse -Force $Work

$size = "{0:N1} MB" -f ((Get-Item $Zip).Length / 1MB)
Write-Host "Diagnostics bundle: $Zip ($size)"
Write-Host ""
Write-Host "Copy this file to USB and send it to support."
Write-Host "Contains host info, NVIDIA + Docker state, recent logs, install reports."
Write-Host "Does NOT contain raw videos or model weights."
