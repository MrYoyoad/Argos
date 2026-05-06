# =====================================================
# VSP Pipeline — Pre-install host check (Windows)
# =====================================================
# Run BEFORE `docker load`. Verifies the host meets the requirements
# for the air-gapped image. Mirrors checks/pre_install_check.sh.
#
# Usage: .\pre_install_check.ps1 [path\to\vsp-image-<build-id>.tar.zst]
# =====================================================

param([string]$ImgTar)

$ErrorActionPreference = "Continue"

$KitDir = $PSScriptRoot
$Log = Join-Path $KitDir "pre_install_check.log"
"" | Out-File -Encoding utf8 $Log

$script:PASSES = 0
$script:WARNS = 0
$script:FAILS = 0

function Write-Pass($msg) {
    Write-Host "[PASS] $msg" -ForegroundColor Green
    Add-Content $Log "[PASS] $msg"
    $script:PASSES++
}
function Write-Warn($msg) {
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
    Add-Content $Log "[WARN] $msg"
    $script:WARNS++
}
function Write-Fail($msg) {
    Write-Host "[FAIL] $msg" -ForegroundColor Red
    Add-Content $Log "[FAIL] $msg"
    $script:FAILS++
}
function Write-Info($msg) {
    Write-Host "       $msg"
    Add-Content $Log "       $msg"
}

function Prompt-ToContinue($msg) {
    Write-Host "[WARN+PROMPT] $msg" -ForegroundColor Yellow
    Add-Content $Log "[WARN+PROMPT] $msg"
    if ($env:VSP_NONINTERACTIVE_PROCEED -eq "1") {
        Write-Info "VSP_NONINTERACTIVE_PROCEED=1; treating as WARN, not FAIL."
        $script:WARNS++
        return $true
    }
    if (-not [Environment]::UserInteractive) {
        Write-Fail "$msg (running non-interactively, treating as FAIL)"
        return $false
    }
    $ans = Read-Host "       Continue anyway? [y/N]"
    if ($ans -match '^[Yy]') {
        Write-Info "User chose to proceed despite warning."
        $script:WARNS++
        return $true
    }
    Write-Fail "$msg (user declined to proceed)"
    return $false
}

Write-Host "=========================================="
Write-Host "VSP Pipeline — Pre-install host check (Windows)"
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
Write-Host "Host: $env:COMPUTERNAME"
Write-Host "=========================================="
Write-Host ""

# --- 1. OS + WSL2 ---
Write-Host "[1/9] OS + WSL2"
$os = Get-CimInstance Win32_OperatingSystem
Write-Pass "OS: $($os.Caption) $($os.Version)"

$wslVersion = wsl --version 2>$null
if ($LASTEXITCODE -eq 0 -and $wslVersion) {
    Write-Pass "WSL2 installed: $(($wslVersion -join ' ').Trim())"
} else {
    Write-Fail "WSL2 not installed. Run 'wsl --install' or install from the kit."
}
Write-Host ""

# --- 2. NVIDIA driver (host) ---
Write-Host "[2/9] NVIDIA driver (host)"
try {
    $nvSmi = & nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits 2>$null
    if ($LASTEXITCODE -eq 0 -and $nvSmi) {
        $driverVer = $nvSmi[0].Trim()
        $major = [int]($driverVer -split '\.')[0]
        if ($major -ge 525) {
            Write-Pass "NVIDIA driver: $driverVer (>=525, supports CUDA 12.x)"
        } else {
            Write-Fail "NVIDIA driver $driverVer too old (need >=525). Update via NVIDIA installer."
        }
    } else {
        Write-Fail "nvidia-smi did not return driver version."
    }
} catch {
    Write-Fail "nvidia-smi not found. Install NVIDIA Windows driver first."
}
Write-Host ""

# --- 3. GPU compute capability + VRAM ---
Write-Host "[3/9] GPU compute capability + VRAM"
try {
    $gpuInfo = & nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader,nounits 2>$null
    foreach ($line in $gpuInfo) {
        $parts = $line -split ','
        $gpuName = $parts[0].Trim()
        $cc = $parts[1].Trim()
        $memMib = [int]$parts[2].Trim()
        Write-Info "GPU: $gpuName"
        Write-Info "  compute capability: $cc"
        Write-Info "  VRAM: $memMib MiB"

        $ccInt = [int](($cc -split '\.')[0]) * 100 + [int](($cc -split '\.')[1])
        if ($ccInt -ge 700) {
            Write-Pass "  compute_cap $cc OK (>=7.0)"
        } elseif ($ccInt -ge 500) {
            Write-Warn "  compute_cap $cc loads but is too slow for usable performance"
        } else {
            Write-Fail "  compute_cap $cc not supported by shipped wheels"
        }

        if ($memMib -ge 12000) {
            Write-Pass "  VRAM $memMib MiB OK (>=12 GB)"
        } elseif ($memMib -ge 8000) {
            Write-Warn "  VRAM $memMib MiB below recommended 12 GB"
        } else {
            Write-Fail "  VRAM $memMib MiB below 8 GB minimum"
        }
    }
} catch {
    Write-Warn "nvidia-smi GPU query failed."
}
Write-Host ""

# --- 4. CPU + RAM ---
Write-Host "[4/9] CPU + RAM"
$cpu = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
Write-Info "CPU logical cores: $cpu"
if ($cpu -lt 4) {
    Write-Fail "CPU cores $cpu below 4-core minimum."
} elseif ($cpu -lt 8) {
    Write-Warn "CPU cores $cpu below 8-core recommendation."
} else {
    Write-Pass "CPU cores: $cpu (>=8)"
}

$ramGib = [int]((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
Write-Info "RAM: $ramGib GiB"
if ($ramGib -lt 16) {
    Write-Fail "RAM $ramGib GiB below 16 GB minimum."
} elseif ($ramGib -lt 32) {
    Prompt-ToContinue "RAM $ramGib GiB is below 32 GB recommended. Decode will be slower." | Out-Null
} else {
    Write-Pass "RAM: $ramGib GiB (>=32)"
}
Write-Host ""

# --- 5. Disk free ---
Write-Host "[5/9] Disk free"
$cDrive = Get-PSDrive C
$cFreeGib = [int]($cDrive.Free / 1GB)
Write-Info "C: drive: $cFreeGib GiB free"
if ($cFreeGib -lt 150) {
    Write-Fail "C: drive has only $cFreeGib GiB free; need >=150 GiB (Docker Desktop image storage)."
} else {
    Write-Pass "C: drive: $cFreeGib GiB free (>=150)"
}

$outDir = if ($env:VSP_OUTPUT_DIR) { $env:VSP_OUTPUT_DIR } else { "$env:USERPROFILE\vsp-output" }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outDriveLetter = (Split-Path $outDir -Qualifier).TrimEnd(':')
$outDrive = Get-PSDrive $outDriveLetter
$outFreeGib = [int]($outDrive.Free / 1GB)
Write-Info "Output partition (${outDir}): $outFreeGib GiB free"
if ($outFreeGib -lt 20) {
    Write-Warn "Output partition has only $outFreeGib GiB free; recommend >=20 GiB."
} else {
    Write-Pass "Output partition: $outFreeGib GiB free (>=20)"
}
Write-Host ""

# --- 6. Docker engine ---
Write-Host "[6/9] Docker engine"
$dockerInfo = & docker info 2>$null
if ($LASTEXITCODE -eq 0) {
    $dockerVer = & docker version --format '{{.Server.Version}}' 2>$null
    Write-Pass "Docker daemon running (server version: $dockerVer)"
} else {
    Write-Fail "Docker daemon not reachable. Start Docker Desktop."
}
Write-Host ""

# --- 7. NVIDIA Container Toolkit ---
Write-Host "[7/9] NVIDIA Container Toolkit (GPU passthrough into Docker)"
if ($LASTEXITCODE -eq 0) {
    $toolkitOut = & docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi 2>&1
    if ($toolkitOut -match 'NVIDIA-SMI') {
        Write-Pass "GPU is visible inside Docker containers"
    } elseif ($toolkitOut -match 'could not select device driver|nvidia-container-cli') {
        Write-Fail "Docker cannot see GPU: NVIDIA Container Toolkit not configured."
        Write-Info "  In Docker Desktop: Settings -> Resources -> WSL Integration -> Enable; restart Docker."
    } elseif ($toolkitOut -match 'Unable to find image') {
        Write-Warn "Toolkit base image not present locally and offline."
        Write-Info "  Skipping toolkit check. Verify manually: docker run --rm --gpus all <local-image> nvidia-smi"
    } else {
        Write-Fail "Docker GPU access failed for unknown reason."
        Write-Info "  Output: $($toolkitOut -join ' | ')"
    }
} else {
    Write-Warn "Skipped (docker not available)."
}
Write-Host ""

# --- 8. Image tarball ---
Write-Host "[8/9] Image tarball"
if (-not $ImgTar) {
    Write-Warn "No image tarball path provided. Pass it as the first arg to verify."
} elseif (-not (Test-Path $ImgTar)) {
    Write-Fail "Image tarball not found: $ImgTar"
} else {
    $imgSizeGib = [int]((Get-Item $ImgTar).Length / 1GB)
    Write-Info "Tarball: $ImgTar (${imgSizeGib} GiB)"
    if (Test-Path "$ImgTar.sha256") {
        Push-Location (Split-Path $ImgTar -Parent)
        & sha256sum -c (Split-Path "$ImgTar.sha256" -Leaf) | Out-Null
        $shaRC = $LASTEXITCODE
        Pop-Location
        if ($shaRC -eq 0) {
            Write-Pass "SHA256 matches"
        } else {
            Write-Fail "SHA256 mismatch — tarball is corrupt. Re-transfer."
        }
    } else {
        Write-Warn "No .sha256 sidecar; cannot verify integrity."
    }
}
Write-Host ""

# --- 9. Summary ---
Write-Host "[9/9] Summary"
Write-Host "  PASS: $($script:PASSES)"
Write-Host "  WARN: $($script:WARNS)"
Write-Host "  FAIL: $($script:FAILS)"
Write-Host ""
if ($script:FAILS -gt 0) {
    Write-Host "Pre-install check FAILED. Resolve items above before running install." -ForegroundColor Red
    Write-Host "Log: $Log"
    exit 1
} elseif ($script:WARNS -gt 0) {
    Write-Host "Pre-install check passed with warnings. Review log before proceeding." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "Pre-install check passed cleanly. Ready for docker load." -ForegroundColor Green
    exit 0
}
