# =====================================================
# VSP Pipeline — desktop launcher (Windows)
# =====================================================
# Double-click target. Picks an input folder, runs the pipeline in a
# console window, dumps outputs to %USERPROFILE%\vsp-output\<timestamp>\.
#
# Image tag is read from C:\vsp\launcher\image.tag (single source of
# truth, swapped by apply_update.ps1 on patches).
# =====================================================

$ErrorActionPreference = "Stop"

# --- Resolve image tag ---
$TagFile = "C:\vsp\launcher\image.tag"
if (-not (Test-Path $TagFile)) {
    # Fall back to relative location (kit not installed system-wide yet).
    $TagFile = Join-Path $PSScriptRoot "image.tag"
}
if (-not (Test-Path $TagFile)) {
    [System.Windows.Forms.MessageBox]::Show("Image tag config not found: $TagFile`n`nRun the kit's install_launcher.ps1 first.","VSP Pipeline","OK","Error") | Out-Null
    exit 1
}
$ImgTag = (Get-Content -Raw $TagFile).Trim()

# Validate tag — defends against accidental editing of image.tag.
if ($ImgTag -notmatch '^[a-zA-Z0-9._/:\-]+$') {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show("Invalid image tag in $TagFile : $ImgTag","VSP Pipeline","OK","Error") | Out-Null
    exit 1
}

# --- Working dirs ---
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = if ($env:VSP_OUTPUT_DIR) { $env:VSP_OUTPUT_DIR } else { Join-Path $env:USERPROFILE "vsp-output\$Timestamp" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# --- Pick input folder ---
Add-Type -AssemblyName System.Windows.Forms
$dlg = New-Object System.Windows.Forms.FolderBrowserDialog
$dlg.Description = "Pick the folder with raw videos"
$dlg.ShowNewFolderButton = $false
if ($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    exit 0
}
$InputDir = $dlg.SelectedPath

if (-not (Test-Path $InputDir)) {
    [System.Windows.Forms.MessageBox]::Show("Selected folder doesn't exist: $InputDir","VSP Pipeline","OK","Error") | Out-Null
    exit 1
}

# --- Existence-check before remove (filters spurious "no such container" without hiding real errors) ---
$null = docker inspect vsp 2>$null
if ($LASTEXITCODE -eq 0) {
    docker rm -f vsp | Out-Null
}

# --- Run the pipeline. PowerShell handles paths with spaces/quotes natively. ---
Write-Host ""
Write-Host "VSP Pipeline launcher"
Write-Host "Image:   $ImgTag"
Write-Host "Input:   $InputDir (read-only)"
Write-Host "Output:  $OutDir"
Write-Host "Started: $(Get-Date)"
Write-Host ""
Write-Host "Press Ctrl+C to abort. The container will be removed on exit."
Write-Host "----------------------------------------"

docker run --name vsp --gpus all `
  -e VSP_OUTPUT_DIR=/data/out `
  -v "${InputDir}:/data/in:ro" `
  -v "${OutDir}:/data/out" `
  $ImgTag `
  /workspace/run_flat_english_pipeline.sh /data/in
$RC = $LASTEXITCODE

Write-Host ""
Write-Host "----------------------------------------"
if ($RC -eq 0) {
    Write-Host "Pipeline finished successfully."
    Write-Host "Outputs are in: $OutDir"
    if (Test-Path "$OutDir\report.html") {
        Write-Host "Open the report: start $OutDir\report.html"
    }
} else {
    Write-Host "Pipeline exited with code $RC."
    Write-Host "If this is unexpected, run .\checks\collect_diagnostics.ps1"
    Write-Host "and send the resulting tarball to support."
}
Write-Host ""
Read-Host "Press Enter to close"
