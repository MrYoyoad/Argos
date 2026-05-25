#requires -RunAsAdministrator
# =====================================================
# VSP Pipeline - self-test (headless)
# =====================================================
# Runs the bundled 12s smoke sample through the pipeline and asserts a
# report + burned video were produced. Proves the install works without
# needing the client's real videos.
#
#   powershell -ExecutionPolicy Bypass -File .\vsp-selftest.ps1
#
# FIRST RUN IS SLOW: ~10-20 min one-time CUDA JIT for the RTX 5090.
# Subsequent runs ~3 min.
# =====================================================

$ErrorActionPreference = "Continue"
function INFO($m) { Write-Host $m }
function OK($m)   { Write-Host "[OK]   $m" -ForegroundColor Green }
function WARN($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

$BwTag    = "vsp-llm-pipeline:client-build-003-bwfix"
$Ctr      = "vsp-selftest"
$tagFile  = "C:\vsp\launcher\image.tag"
$ImgTag   = if (Test-Path $tagFile) { (Get-Content -Raw $tagFile).Trim() } else { $BwTag }

# Sample to run: prefer the installed copy
$sample = $null
foreach ($p in @("C:\vsp\samples\smoke_12s.mp4", (Join-Path $PSScriptRoot "samples\smoke_12s.mp4"))) {
    if (Test-Path $p) { $sample = $p; break }
}
if (-not $sample) { FAIL "smoke_12s.mp4 not found (run vsp-setup.ps1 first)."; Write-Host "SELFTEST FAIL"; exit 1 }

# --- preflight ---
docker version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { FAIL "Docker not responding."; Write-Host "SELFTEST FAIL"; exit 1 }
$img = docker images $ImgTag --format '{{.Repository}}:{{.Tag}}' 2>$null
if ($img -ne $ImgTag) { FAIL "Image '$ImgTag' not loaded."; Write-Host "SELFTEST FAIL"; exit 1 }
OK "Docker up, image present: $ImgTag"

# --- staging: input MUST be on C: (Docker Desktop can't mount removable drives) ---
$stageIn  = "C:\vsp-selftest\in"
$stageOut = "C:\vsp-selftest\out"
Remove-Item -Recurse -Force "C:\vsp-selftest" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stageIn, $stageOut | Out-Null
Copy-Item -Force $sample $stageIn
OK "Staged sample to $stageIn"

docker rm -f $Ctr 2>$null | Out-Null

Write-Host ""
Write-Host "Running pipeline headless. FIRST RUN: 10-20 min (one-time CUDA JIT)." -ForegroundColor Yellow
Write-Host "Do NOT close this window. Subsequent runs are ~3 min." -ForegroundColor Yellow
Write-Host ""

$start = Get-Date
docker run --name $Ctr --gpus all `
  --entrypoint /bin/bash `
  -e VSP_OUTPUT_DIR=/data/out `
  -e VSP_FULL_OUTPUTS=1 `
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 `
  -e TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 `
  -v "${stageIn}:/data/in:ro" `
  -v "${stageOut}:/data/out" `
  $ImgTag `
  /workspace/run_flat_english_pipeline.sh /data/in
$rc = $LASTEXITCODE
$mins = [math]::Round(((Get-Date) - $start).TotalMinutes, 1)

if ($rc -ne 0) {
    FAIL "Pipeline exited with code $rc after $mins min."
    INFO "Last 60 log lines:"
    docker logs $Ctr 2>&1 | Select-Object -Last 60
    Write-Host ""
    Write-Host "SELFTEST FAIL" -ForegroundColor Red
    INFO "Send Yoad: the lines above + 'selftest, exit $rc'."
    exit 1
}
OK "Pipeline finished in $mins min."

# --- extract outputs from the container and assert ---
$probe = "C:\vsp-selftest\_archive"
New-Item -ItemType Directory -Force -Path $probe | Out-Null
docker cp "${Ctr}:/workspace/flat_runs_archive/." $probe 2>$null
$run = Get-ChildItem $probe -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$report = $null
$burned = $null
if ($run) {
    $co = Join-Path $run.FullName "client_outputs"
    $r  = Join-Path $co "report\report.html"
    if (Test-Path $r) { $report = $r }
    $b = Get-ChildItem (Join-Path $co "burned_videos") -Filter *.mp4 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($b) { $burned = $b.FullName }
}

docker rm -f $Ctr 2>$null | Out-Null

Write-Host ""
if ($report -and $burned) {
    OK "report.html : $report"
    OK "burned video: $burned"
    Write-Host ""
    Write-Host "SELFTEST PASS" -ForegroundColor Green
    Write-Host ""
    INFO "Open the report to eyeball it:"
    INFO "  start `"$report`""
    INFO "Send Yoad: 'SELFTEST PASS' + a screenshot of the opened report."
    exit 0
} else {
    FAIL "Pipeline ran but expected outputs are missing."
    if (-not $report) { FAIL "  report/report.html NOT found" }
    if (-not $burned) { FAIL "  burned_videos/*.mp4 NOT found" }
    Write-Host ""
    Write-Host "SELFTEST FAIL" -ForegroundColor Red
    INFO "Send Yoad: this output + 'selftest, outputs missing'."
    exit 1
}
