# =====================================================
# VSP Pipeline — apply a code-only update (Windows)
# =====================================================
# Usage: .\apply_update.ps1 <new-image-tarball.tar.zst> <new-image-tag>
# =====================================================

param(
    [Parameter(Mandatory=$true)] [string] $Tarball,
    [Parameter(Mandatory=$true)] [string] $NewTag
)

$ErrorActionPreference = "Stop"

$TagFile = "C:\vsp\launcher\image.tag"
if (-not (Test-Path $TagFile)) {
    Write-Host "ERROR: $TagFile not found. Run install_launcher.ps1 first."
    exit 1
}
$PrevTag = (Get-Content -Raw $TagFile).Trim()

if (-not (Test-Path $Tarball)) {
    Write-Host "ERROR: tarball not found: $Tarball"
    exit 1
}
if ($NewTag -notmatch '^[a-zA-Z0-9._/:\-]+$') {
    Write-Host "ERROR: invalid image tag: $NewTag"
    exit 1
}

Write-Host "=========================================="
Write-Host "VSP Pipeline — apply update"
Write-Host "  current tag: $PrevTag"
Write-Host "  new tag:     $NewTag"
Write-Host "  tarball:     $Tarball"
Write-Host "=========================================="

# Step 1: integrity (zstd integrity test if applicable)
Write-Host "[1/5] Verifying tarball integrity..."
if ($Tarball -match '\.zst$') {
    & zstd -t $Tarball
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: zstd integrity check failed"; exit 2 }
}
$ShaFile = "$Tarball.sha256"
if (Test-Path $ShaFile) {
    Push-Location (Split-Path $Tarball -Parent)
    $shaResult = & sha256sum -c (Split-Path $ShaFile -Leaf)
    Pop-Location
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: SHA256 mismatch"; exit 2 }
}
Write-Host "  OK"

# Step 2: load
Write-Host "[2/5] Loading image..."
if ($Tarball -match '\.zst$') {
    & zstd -d -c $Tarball | docker load
} else {
    docker load -i $Tarball
}
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: docker load failed"; exit 2 }

# Step 3: smoke test
Write-Host "[3/5] Smoke-testing new image..."
docker run --rm $NewTag bash /workspace/lib/test_all_modules.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: smoke test failed on new image. Old build still active."
    Write-Host "Tag in image.tag is still: $PrevTag"
    exit 3
}
Write-Host "  OK"

# Step 4: atomic tag swap
Write-Host "[4/5] Swapping image.tag..."
Set-Content -Path "$TagFile.previous" -Value $PrevTag
Set-Content -Path "$TagFile.tmp" -Value $NewTag
Move-Item -Force "$TagFile.tmp" $TagFile
Write-Host "  image.tag now: $((Get-Content $TagFile).Trim())"
Write-Host "  previous saved at: $TagFile.previous"

# Step 5: keep previous image
Write-Host "[5/5] Keeping previous image $PrevTag on disk for rollback (use rollback.ps1 to flip back)."
Write-Host ""
Write-Host "Update complete. Next pipeline launch uses $NewTag."
