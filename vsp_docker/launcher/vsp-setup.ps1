#requires -RunAsAdministrator
# =====================================================
# VSP Pipeline - setup + doctor (idempotent)
# =====================================================
# Run from an Administrator PowerShell, from the unzipped kit folder:
#   cd C:\vsp-kit
#   powershell -ExecutionPolicy Bypass -File .\vsp-setup.ps1
#
# It: purges ALL old VSP shortcuts everywhere, reinstalls the launchers,
# sanity-checks that the UI container actually starts (catches the
# "window opens then closes" bug), verifies the shortcuts resolve, and
# prints a VERIFY block to paste back.
# =====================================================

$ErrorActionPreference = "Continue"
function INFO($m) { Write-Host $m }
function OK($m)   { Write-Host "[OK]   $m" -ForegroundColor Green }
function WARN($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }
function HDR($m)  { Write-Host ""; Write-Host "==== $m ====" -ForegroundColor Cyan }

$BwTag  = "vsp-llm-pipeline:client-build-003-bwfix"
$Prefix = "C:\vsp\launcher"
$KitDir = $PSScriptRoot
$report = New-Object System.Collections.ArrayList
function Rep($line) { [void]$report.Add($line) }

# --- 0. admin ---
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) { FAIL "Re-run from an Administrator PowerShell window."; exit 1 }
OK "Running as administrator."

# --- 1. Docker + image ---
HDR "Environment"
docker version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { FAIL "Docker not responding. Start Docker Desktop, wait for green 'Engine running', re-run."; Rep "docker: DOWN"; exit 1 }
$srvVer = (docker version --format '{{.Server.Version}}' 2>$null)
OK "Docker daemon up (server $srvVer)"; Rep "docker: up ($srvVer)"

$tagFile = "$Prefix\image.tag"
$ImgTag  = if (Test-Path $tagFile) { (Get-Content -Raw $tagFile).Trim() } else { $BwTag }
$img = docker images $ImgTag --format '{{.Repository}}:{{.Tag}}' 2>$null
if ($img -ne $ImgTag) {
    FAIL "Image '$ImgTag' is NOT loaded. The earlier image-load/Blackwell fix did not complete."
    Rep "image: MISSING ($ImgTag)"
    FAIL "STOP - send this to Yoad."
    exit 1
}
OK "Image present: $ImgTag"; Rep "image: present ($ImgTag)"

# --- 2. kit files present + parse-valid (catches transfer corruption) ---
HDR "Kit files"
$startSrc = Join-Path $KitDir "vsp-start.ps1"
$runSrc   = Join-Path $KitDir "vsp-run.ps1"
foreach ($f in @($startSrc,$runSrc)) {
    if (-not (Test-Path $f)) { FAIL "Missing kit file: $f"; Rep "kitfile $f : MISSING"; exit 1 }
    $leaf = Split-Path $f -Leaf
    $toks = $null
    $errs = $null
    try {
        [void][System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$toks, [ref]$errs)
    } catch {
        FAIL "Could not parse $leaf : $($_.Exception.Message)"
        Rep "parse ${leaf}: EXCEPTION"
        exit 1
    }
    if ($errs -and $errs.Count -gt 0) {
        FAIL "$f has a PowerShell syntax error (corrupt transfer?). First: $($errs[0].Message)"
        Rep "parse ${leaf}: FAIL"
        exit 1
    }
    OK "$leaf present + parses clean"
    Rep "parse $(Split-Path $f -Leaf): ok"
}

# --- 3. install launchers ---
HDR "Install launchers -> $Prefix"
New-Item -ItemType Directory -Force -Path $Prefix | Out-Null
Copy-Item -Force $startSrc "$Prefix\vsp-start.ps1"
Copy-Item -Force $runSrc   "$Prefix\vsp-run.ps1"
if (-not (Test-Path $tagFile)) { $BwTag | Out-File -NoNewline -Encoding ascii $tagFile; OK "Wrote image.tag -> $BwTag" }
else { OK "image.tag kept: $((Get-Content -Raw $tagFile).Trim())" }

@"
@echo off
title VSP Pipeline (UI)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0vsp-start.ps1"
if errorlevel 1 ( echo. & echo Launcher exited with an error - read above. & pause )
"@ | Out-File -Encoding ascii -NoNewline "$Prefix\VSP-UI.bat"
@"
@echo off
title VSP Pipeline (CLI)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0vsp-run.ps1"
if errorlevel 1 ( echo. & echo Launcher exited with an error - read above. & pause )
"@ | Out-File -Encoding ascii -NoNewline "$Prefix\VSP-CLI.bat"
OK "Wrote VSP-UI.bat + VSP-CLI.bat"

if (Test-Path (Join-Path $KitDir "samples")) {
    New-Item -ItemType Directory -Force -Path "C:\vsp\samples" | Out-Null
    Copy-Item -Force -Recurse (Join-Path $KitDir "samples\*") "C:\vsp\samples\"
    OK "Samples -> C:\vsp\samples"
}

# --- 4. PURGE every stale VSP shortcut on every desktop ---
HDR "Purge old shortcuts"
$sh = New-Object -ComObject WScript.Shell
$allDesktops = @()
$allDesktops += (Join-Path $env:PUBLIC "Desktop")
$allDesktops += (Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName "Desktop" })
$allDesktops = $allDesktops | Where-Object { Test-Path $_ } | Select-Object -Unique
$purged = 0
foreach ($d in $allDesktops) {
    Get-ChildItem "$d\*.lnk" -ErrorAction SilentlyContinue | ForEach-Object {
        $isVsp = $false
        if ($_.Name -match 'VSP') {
            $isVsp = $true
        } else {
            try {
                if ($sh.CreateShortcut($_.FullName).TargetPath -match 'vsp\\launcher') { $isVsp = $true }
            } catch { }   # corrupt .lnk - ignore, don't abort the purge
        }
        if ($isVsp) {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
            $purged++
            INFO "  removed $($_.FullName)"
        }
    }
}
OK "Purged $purged old VSP shortcut(s)"; Rep "purged old shortcuts: $purged"

# --- 5. recreate the two shortcuts (Public + interactive user) ---
HDR "Create shortcuts"
$targets = @( (Join-Path $env:PUBLIC "Desktop") )
try {
    $u = (Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" |
          ForEach-Object { (Invoke-CimMethod -InputObject $_ -MethodName GetOwner) } |
          Select-Object -First 1)
    if ($u -and $u.User) {
        $ud = "C:\Users\$($u.User)\Desktop"
        if ((Test-Path $ud) -and ($targets -notcontains $ud)) { $targets += $ud }
    }
} catch {}
$made = @()
foreach ($desk in ($targets | Where-Object { Test-Path $_ })) {
    foreach ($pair in @(@('VSP Pipeline (UI)','VSP-UI.bat','shell32.dll,14'),
                        @('VSP Pipeline (CLI)','VSP-CLI.bat','shell32.dll,15'))) {
        $lnk = "$desk\$($pair[0]).lnk"
        $s = $sh.CreateShortcut($lnk)
        $s.TargetPath       = "$Prefix\$($pair[1])"
        $s.WorkingDirectory = $Prefix
        $s.IconLocation     = $pair[2]
        $s.Description       = "VSP Pipeline"
        $s.Save()
        # read back to confirm it resolves
        $chk = $sh.CreateShortcut($lnk)
        if ((Test-Path $lnk) -and ($chk.TargetPath -eq "$Prefix\$($pair[1])") -and (Test-Path $chk.TargetPath)) {
            OK "OK  $lnk  ->  $($chk.TargetPath)"
            $made += "$lnk -> $($chk.TargetPath)"
        } else {
            FAIL "BAD $lnk (did not resolve)"
            $made += "$lnk -> BROKEN"
        }
    }
}
$made | ForEach-Object { Rep "shortcut: $_" }

# --- 6. container sanity: does the UI container actually START and STAY UP? ---
# This catches the "window opens then immediately closes" class of bug
# WITHOUT waiting for the full 10-15 min CUDA JIT. We only check the
# container doesn't die in the first ~25 s (a bad flag/mount/name dies fast).
HDR "Container start sanity (UI)"
docker rm -f vsp 2>$null | Out-Null
$port = if ($env:VSP_UI_PORT) { $env:VSP_UI_PORT } else { "8080" }
$inDir  = Join-Path $env:USERPROFILE "vsp-input"
$outDir = Join-Path $env:USERPROFILE "vsp-output"
$trDir  = Join-Path $env:USERPROFILE "vsp-transcriptions"
New-Item -ItemType Directory -Force -Path $inDir,$outDir,$trDir | Out-Null
docker run -d --name vsp --gpus all -p "${port}:${port}" --entrypoint /bin/bash `
  -e VSP_INPUT_DIR=/data/in -e VSP_OUTPUT_DIR=/data/out -e VSP_TRANSCRIPTIONS_DIR=/data/transcriptions `
  -e VSP_UI_HOST=0.0.0.0 -e VSP_UI_PORT=$port -e VSP_FULL_OUTPUTS=1 `
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 `
  -e TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 `
  -v "${inDir}:/data/in" -v "${outDir}:/data/out" -v "${trDir}:/data/transcriptions" `
  $ImgTag -c "cd /workspace/vsp-ui && python3 -m app.server" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    FAIL "docker run failed immediately (exit $LASTEXITCODE). Port $port busy, or Docker issue."
    Rep "container-sanity: docker run FAILED (exit $LASTEXITCODE)"
} else {
    Start-Sleep -Seconds 25
    $st = (docker inspect -f '{{.State.Status}}' vsp 2>$null | Select-Object -First 1)
    if ($st) { $st = $st.Trim() }
    if ($st -eq 'running') {
        OK "Container is RUNNING after 25 s - the launcher invocation is valid."
        OK "(The UI/server itself may still need the one-time CUDA JIT on first real use.)"
        Rep "container-sanity: RUNNING ok"
    } else {
        FAIL "Container is '$st' after 25 s - it died early. Last 30 log lines:"
        docker logs vsp 2>&1 | Select-Object -Last 30
        Rep "container-sanity: DIED (state=$st)"
    }
}
docker rm -f vsp 2>$null | Out-Null

# --- 7. VERIFY block ---
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SETUP COMPLETE - paste EVERYTHING below back to Yoad" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "----- VSP-VERIFY-BEGIN -----"
$report | ForEach-Object { Write-Host $_ }
Write-Host "----- VSP-VERIFY-END -----"
Write-Host ""
Write-Host "To use it now: double-click  'VSP Pipeline (UI)'  on the Desktop."
Write-Host "If you still see only generic/old icons, press F5 on the Desktop,"
Write-Host "or open  C:\Users\Public\Desktop  and double-click the .lnk there."
