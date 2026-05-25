# =====================================================
# VSP Pipeline - UI mode launcher (Windows)
# =====================================================
# Starts the Docker container with:
#   - GPU passthrough
#   - Port 8080 mapped (UI server)
#   - vsp-input bind-mount (drag-drop + manual transcriptions)
#   - vsp-output bind-mount (reports, burned videos)
#   - vsp-transcriptions bind-mount (persistent across runs)
# Then opens the browser to http://localhost:8080.
#
# Usage: .\vsp-start.ps1           # start
#        .\vsp-start.ps1 stop      # stop the container
#        .\vsp-start.ps1 status    # check if running
# =====================================================

param([string]$Action = "start")

# NOTE: must be "Continue" not "Stop" - "Stop" aborts on benign docker stderr
# (e.g. "no such container") and breaks the launcher on PowerShell 5.1.
$ErrorActionPreference = "Continue"

# --- Resolve image tag ---
$TagFile = "C:\vsp\launcher\image.tag"
if (-not (Test-Path $TagFile)) {
    $TagFile = Join-Path $PSScriptRoot "image.tag"
}
if (Test-Path $TagFile) {
    $ImgTag = (Get-Content -Raw $TagFile).Trim()
} else {
    # No tag file: fall back to the Blackwell hot-fixed image.
    $ImgTag = "vsp-llm-pipeline:client-build-003-bwfix"
    Write-Host "image.tag not found; defaulting to $ImgTag" -ForegroundColor Yellow
}
if ($ImgTag -notmatch '^[a-zA-Z0-9._/:\-]+$') {
    Write-Host "Invalid tag: $ImgTag" -ForegroundColor Red
    exit 1
}

# --- Settings ---
$ContainerName = if ($env:VSP_CONTAINER_NAME) { $env:VSP_CONTAINER_NAME } else { "vsp" }
$Port = if ($env:VSP_UI_PORT) { $env:VSP_UI_PORT } else { "8080" }
$Url = "http://localhost:${Port}"

$InputDir = if ($env:VSP_INPUT_DIR) { $env:VSP_INPUT_DIR } else { Join-Path $env:USERPROFILE "vsp-input" }
$OutputDir = if ($env:VSP_OUTPUT_DIR) { $env:VSP_OUTPUT_DIR } else { Join-Path $env:USERPROFILE "vsp-output" }
$TransDir = if ($env:VSP_TRANSCRIPTIONS_DIR) { $env:VSP_TRANSCRIPTIONS_DIR } else { Join-Path $env:USERPROFILE "vsp-transcriptions" }

New-Item -ItemType Directory -Force -Path $InputDir, $OutputDir, $TransDir | Out-Null

function Is-ContainerRunning {
    $running = docker ps --filter "name=^/${ContainerName}$" --format '{{.Names}}' 2>$null
    return ($running -eq $ContainerName)
}

function Is-ServerReady {
    # "Ready" = the web server answers HTTP at all. A 200 on /api/status is
    # ideal, but even a 404 on / means the server socket is up and serving,
    # which is enough to open the browser. We also catch the WebException
    # that carries an HTTP response (PowerShell throws on non-2xx).
    foreach ($path in @("/api/status", "/")) {
        try {
            $r = Invoke-WebRequest -Uri "${Url}${path}" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -ge 200) { return $true }
        } catch [System.Net.WebException] {
            if ($_.Exception.Response -ne $null) { return $true }  # server answered with an error code = it's up
        } catch {
            # connection refused / not yet listening - keep waiting
        }
    }
    return $false
}

function Open-Browser($u) {
    Start-Process $u
}

function Do-Start {
    Write-Host "========================================="
    Write-Host "  VSP Pipeline - UI mode"
    Write-Host "========================================="
    Write-Host "Image:           $ImgTag"
    Write-Host "Port:            $Port"
    Write-Host "Input dir:       $InputDir (rw - drop videos here OR via UI)"
    Write-Host "Output dir:      $OutputDir"
    Write-Host "Transcriptions:  $TransDir (persistent across runs)"
    Write-Host "URL:             $Url"
    Write-Host "========================================="
    Write-Host ""
    Write-Host "NOTE: First decode on a brand-new GPU (e.g. RTX 5090) may take an"
    Write-Host "      extra 10-15 min while CUDA compiles kernels for your hardware."
    Write-Host "      This is one-time per GPU+driver combination."
    Write-Host ""

    # Always start clean: remove any old/stale 'vsp' container.
    docker rm -f $ContainerName 2>$null | Out-Null

    # Start the container DETACHED. Detached + poll + browser-open in the
    # foreground is reliable when launched from a desktop shortcut/.bat
    # (the old Start-Job approach died when the parent shell exited).
    # TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 is REQUIRED for the bwfix (torch 2.8)
    # image so fairseq checkpoint loading works at pipeline step 6.
    Write-Host "Starting container (detached)..."
    docker run -d `
      --name $ContainerName `
      --gpus all `
      -p "${Port}:${Port}" `
      --entrypoint /bin/bash `
      -e VSP_INPUT_DIR=/data/in `
      -e VSP_OUTPUT_DIR=/data/out `
      -e VSP_TRANSCRIPTIONS_DIR=/data/transcriptions `
      -e VSP_UI_HOST=0.0.0.0 `
      -e VSP_UI_PORT=$Port `
      -e VSP_FULL_OUTPUTS=1 `
      -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 `
      -e TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 `
      -e "VSP_HOST_INPUT_DIR=$InputDir" `
      -v "${InputDir}:/data/in" `
      -v "${OutputDir}:/data/out" `
      -v "${TransDir}:/data/transcriptions" `
      $ImgTag `
      -c "cd /workspace/vsp-ui && python3 -m app.server" | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: container failed to start (exit $LASTEXITCODE)." -ForegroundColor Red
        Write-Host "Is Docker Desktop running (green 'Engine running')?" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to close"
        return
    }

    # Poll until the web server answers, then open the browser.
    Write-Host "Waiting for the UI server to come up (up to 3 min)..."
    $ready = $false
    for ($i = 1; $i -le 180; $i++) {
        if (-not (Is-ContainerRunning)) {
            Write-Host ""
            Write-Host "ERROR: the container exited unexpectedly. Last 40 log lines:" -ForegroundColor Red
            docker logs $ContainerName 2>&1 | Select-Object -Last 40
            Write-Host ""
            Read-Host "Press Enter to close"
            return
        }
        if (Is-ServerReady) { $ready = $true; break }
        Start-Sleep -Seconds 1
        if ($i % 10 -eq 0) { Write-Host "  ...still starting ($i s)" }
    }

    if ($ready) {
        Write-Host ""
        Write-Host "Server is UP. Opening browser: $Url" -ForegroundColor Green
        Open-Browser $Url
    } else {
        Write-Host ""
        Write-Host "Server did not answer in time, but the container is still" -ForegroundColor Yellow
        Write-Host "running. Try opening this in your browser manually:" -ForegroundColor Yellow
        Write-Host "    $Url" -ForegroundColor Yellow
        Open-Browser $Url
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host " VSP UI is running. This window shows the server log."
    Write-Host " - Browser: $Url"
    Write-Host " - To STOP the server: close this window."
    Write-Host "============================================================"
    Write-Host ""

    # Tail logs in the foreground. This keeps the window open AND gives the
    # operator live server output. Closing the window ends this; we then
    # stop the container so it doesn't linger.
    try {
        docker logs -f $ContainerName
    } finally {
        Write-Host ""
        Write-Host "Stopping container..."
        docker stop $ContainerName 2>$null | Out-Null
        docker rm -f $ContainerName 2>$null | Out-Null
        Write-Host "Server stopped."
    }
}

function Do-Stop {
    Write-Host "Stopping VSP Pipeline UI..."
    if (Is-ContainerRunning) {
        docker stop $ContainerName 2>$null | Out-Null
        Write-Host "Stopped."
    } else {
        Write-Host "Not running."
    }
}

function Do-Status {
    if (Is-ContainerRunning) {
        Write-Host "VSP Pipeline UI is RUNNING"
        Write-Host "  Container: $ContainerName"
        Write-Host "  URL:       $Url"
        if (Is-ServerReady) { Write-Host "  Server:    responding" } else { Write-Host "  Server:    not responding" }
    } else {
        Write-Host "VSP Pipeline UI is NOT running."
    }
}

switch ($Action) {
    "start"  { Do-Start }
    "stop"   { Do-Stop }
    "status" { Do-Status }
    default  { Write-Host "Usage: .\vsp-start.ps1 {start|stop|status}"; exit 1 }
}
