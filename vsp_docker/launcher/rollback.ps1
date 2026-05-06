# =====================================================
# VSP Pipeline — rollback to the previous image build (Windows)
# =====================================================

$ErrorActionPreference = "Stop"

$TagFile = "C:\vsp\launcher\image.tag"
$PrevFile = "$TagFile.previous"

if (-not (Test-Path $TagFile)) {
    Write-Host "ERROR: $TagFile not found."
    exit 1
}
if (-not (Test-Path $PrevFile)) {
    Write-Host "ERROR: no previous tag recorded at $PrevFile."
    exit 1
}

$CurTag = (Get-Content -Raw $TagFile).Trim()
$PrevTag = (Get-Content -Raw $PrevFile).Trim()

Write-Host "=========================================="
Write-Host "VSP Pipeline — rollback"
Write-Host "  current tag:     $CurTag"
Write-Host "  rolling back to: $PrevTag"
Write-Host "=========================================="

$null = docker image inspect $PrevTag 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: previous image $PrevTag is not loaded in Docker."
    Write-Host "It may have been removed. Re-load it from a kit tarball before running rollback."
    exit 2
}

Set-Content -Path "$TagFile.previous" -Value $CurTag
Set-Content -Path "$TagFile.tmp" -Value $PrevTag
Move-Item -Force "$TagFile.tmp" $TagFile

Write-Host "Rolled back. image.tag is now: $((Get-Content $TagFile).Trim())"
