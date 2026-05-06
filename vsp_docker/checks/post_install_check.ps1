# =====================================================
# VSP Pipeline — Post-install verification (Windows)
# =====================================================
# Run AFTER `docker load`. Mirrors checks/post_install_check.sh.
# Usage: .\post_install_check.ps1 [image_tag]
# =====================================================

param([string]$ImgTag)

$ErrorActionPreference = "Continue"

$KitDir = $PSScriptRoot
$Log = Join-Path $KitDir "post_install_check.log"
$SamplesDir = Join-Path (Split-Path $KitDir -Parent) "samples"
$WorkDir = Join-Path $env:TEMP "vsp_post_install_$(Get-Random)"
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

# Resolve image tag
if (-not $ImgTag) {
    foreach ($f in @("C:\vsp\launcher\image.tag", (Join-Path (Split-Path $KitDir -Parent) "launcher\image.tag"))) {
        if (Test-Path $f) { $ImgTag = (Get-Content -Raw $f).Trim(); break }
    }
}
if (-not $ImgTag) {
    $ImgTag = (& docker images --format '{{.Repository}}:{{.Tag}}' 2>$null | Select-String '^vsp-llm-pipeline:' | Select-Object -First 1).ToString().Trim()
}
if (-not $ImgTag) {
    Write-Host "ERROR: Could not determine image tag. Pass it as the first argument." -ForegroundColor Red
    exit 1
}

$script:PASSES = 0
$script:FAILS = 0
function Write-Pass($msg) { Write-Host "[PASS] $msg" -ForegroundColor Green; Add-Content $Log "[PASS] $msg"; $script:PASSES++ }
function Write-Fail($msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; Add-Content $Log "[FAIL] $msg"; $script:FAILS++ }
function Write-Info($msg) { Write-Host "       $msg"; Add-Content $Log "       $msg" }

"" | Out-File -Encoding utf8 $Log
Write-Host "=========================================="
Write-Host "VSP Pipeline — Post-install verification"
Write-Host "Image: $ImgTag"
Write-Host "Date:  $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
Write-Host "=========================================="
Write-Host ""

# --- 1. Image is loaded ---
Write-Host "[1/8] Image is loaded"
& docker image inspect $ImgTag *>$null
if ($LASTEXITCODE -eq 0) {
    Write-Pass "Image $ImgTag present"
} else {
    Write-Fail "Image $ImgTag not loaded. Run docker load -i vsp-image-*.tar first."
    exit 1
}
Write-Host ""

# --- 2. In-container module tests ---
Write-Host "[2/8] In-container module tests (lib/test_all_modules.sh)"
$out = & docker run --rm $ImgTag bash /workspace/lib/test_all_modules.sh 2>&1
Add-Content $Log ($out -join "`n")
if ($LASTEXITCODE -eq 0) {
    Write-Pass "All module tests passed"
} else {
    Write-Fail "lib/test_all_modules.sh failed"
}
Write-Host ""

# --- 3. Sample fixture integrity ---
Write-Host "[3/8] Sample fixture integrity"
$sumsFile = Join-Path $SamplesDir "checksums.txt"
if (Test-Path $sumsFile) {
    Push-Location $SamplesDir
    $sha = & sha256sum -c "checksums.txt" 2>&1
    $shaRC = $LASTEXITCODE
    Pop-Location
    Add-Content $Log ($sha -join "`n")
    if ($shaRC -eq 0) {
        Write-Pass "Curated samples match checksums.txt"
    } else {
        Write-Fail "Sample fixture SHA256 mismatch"
    }
} else {
    Write-Fail "samples\checksums.txt missing"
}
Write-Host ""

# --- 4-5. Smoke decodes ---
function Run-SmokeDecode($sample, $label, $subdir) {
    if (-not (Test-Path $sample)) {
        Write-Fail "Smoke sample missing: $sample"
        return $null
    }
    $inDir = Join-Path $WorkDir "${subdir}_in"
    $outDir = Join-Path $WorkDir "${subdir}_out"
    New-Item -ItemType Directory -Force -Path $inDir, $outDir | Out-Null
    Copy-Item $sample $inDir
    Write-Host ">>> Running smoke decode on $label..."
    $cName = "vsp_smoke_$subdir"
    & docker rm -f $cName *>$null
    & docker run --rm --name $cName --gpus all `
        -e VSP_OUTPUT_DIR=/data/out `
        -v "${inDir}:/data/in:ro" `
        -v "${outDir}:/data/out" `
        $ImgTag `
        /workspace/run_flat_english_pipeline.sh /data/in 2>&1 | Tee-Object -FilePath $Log -Append | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Smoke decode ($label) completed without error"
        return $outDir
    } else {
        Write-Fail "Smoke decode ($label) failed"
        return $null
    }
}

Write-Host "[4/8] Smoke decode — 12s sample"
$smoke12Out = Run-SmokeDecode (Join-Path $SamplesDir "smoke_12s.mp4") "12-second" "smoke12"
Write-Host ""
Write-Host "[5/8] Smoke decode — 75s sample (full pipeline + n-best)"
$smoke75Out = Run-SmokeDecode (Join-Path $SamplesDir "smoke_75s.mp4") "75-second" "smoke75"
Write-Host ""

# --- 6. Mechanism checks ---
Write-Host "[6/8] Feature-parity mechanism checks (75s output)"
if (-not $smoke75Out) {
    Write-Fail "75s output dir missing — skipping mechanism checks"
} else {
    $OUT = $smoke75Out

    # 6.1 aggregated.json with all 5 hyps
    $aggJson = Join-Path $OUT "aggregated.json"
    if (Test-Path $aggJson) {
        $script = @"
import json, sys
d = json.load(open(r'$aggJson'))
keys = set()
for v in (d.values() if isinstance(d, dict) else []):
    if isinstance(v, dict): keys |= set(v.keys())
required = {'hyp_mbr','hyp_vote_score','hyp_vote_conf','hyp_safe','hyp_xseg_merge'}
sys.exit(1 if not required.issubset(keys) else 0)
"@
        $tmp = New-TemporaryFile
        Set-Content $tmp $script
        & docker run --rm -v "${OUT}:/out:ro" $ImgTag python3 /tmp/check.py 2>&1 | Out-Null
        # Simpler approach: parse JSON in PowerShell
        $aggData = Get-Content $aggJson | ConvertFrom-Json
        $allKeys = @()
        $aggData.PSObject.Properties | ForEach-Object {
            if ($_.Value -is [PSCustomObject]) {
                $allKeys += $_.Value.PSObject.Properties.Name
            }
        }
        $allKeys = $allKeys | Select-Object -Unique
        $required = @('hyp_mbr','hyp_vote_score','hyp_vote_conf','hyp_safe','hyp_xseg_merge')
        $missing = $required | Where-Object { $_ -notin $allKeys }
        if ($missing.Count -eq 0) {
            Write-Pass "n-best aggregation: all 5 hypothesis methods present"
        } else {
            Write-Fail "n-best aggregation: missing keys: $($missing -join ', ')"
        }
    } else {
        Write-Fail "aggregated.json not produced"
    }

    # 6.2 report.csv columns
    $reportCsv = Join-Path $OUT "report.csv"
    if (Test-Path $reportCsv) {
        $header = (Get-Content $reportCsv -First 1)
        $needed = @('sentence_confidence', 'hyp_mbr')
        $nivOk = ($header -match 'NIV|niv')
        $missing = $needed | Where-Object { $header -notmatch $_ }
        if ($missing.Count -eq 0 -and $nivOk) {
            Write-Pass "report.csv has sentence_confidence + hyp_mbr + NIV columns"
        } else {
            Write-Fail "report.csv missing columns: $($missing -join ', ') (NIV: $nivOk)"
        }
    } else {
        Write-Fail "report.csv not produced"
    }

    # 6.3 tier classification
    if ((Test-Path $reportCsv) -and (Select-String -Path $reportCsv -Pattern 'Trust|Salvage|Strip' -Quiet)) {
        Write-Pass "Tier classification (Trust/Salvage/Strip) fired"
    } else {
        Write-Fail "No tier markers in report.csv"
    }

    # 6.4 IS scoring
    if (Test-Path (Join-Path $OUT "intelligibility_scores.csv")) {
        Write-Pass "IS scoring produced intelligibility_scores.csv"
    } else {
        Write-Fail "intelligibility_scores.csv not produced"
    }

    # 6.5 k-means saved
    if (Get-ChildItem $OUT -Filter "*_kmeans_200.bin" -ErrorAction SilentlyContinue) {
        Write-Pass "k-means model exported"
    } else {
        Write-Fail "No *_kmeans_200.bin in output"
    }

    # 6.6 Confidence palette in report.html
    $reportHtml = Join-Path $OUT "report.html"
    if (Test-Path $reportHtml) {
        $html = Get-Content -Raw $reportHtml
        if ($html -match '#(00ff00|008000|ff0000|800000|ffff00)') {
            Write-Fail "report.html contains old-palette hex codes"
        } else {
            Write-Pass "No old-palette hex codes in report.html"
        }
        $newPalette = @('blue','orange','purple','teal') | ForEach-Object { $html -match $_ }
        if ($newPalette -notcontains $false) {
            Write-Pass "report.html legend has all 4 new-palette color words"
        } else {
            Write-Fail "report.html missing new-palette color word(s)"
        }
    } else {
        Write-Fail "report.html not produced"
    }

    # 6.7 VSP_NBEST=1 in logs
    $logFiles = Get-ChildItem $OUT -Filter "*.log" -ErrorAction SilentlyContinue
    $nbestFound = $false
    foreach ($lf in $logFiles) {
        if (Select-String -Path $lf.FullName -Pattern 'VSP_NBEST=1|n-best' -Quiet) {
            $nbestFound = $true; break
        }
    }
    if ($nbestFound) {
        Write-Pass "VSP_NBEST=1 default fired"
    } else {
        Write-Fail "No n-best evidence in logs"
    }
}
Write-Host ""

# --- 7. Timing note ---
Write-Host "[7/8] Decode timing"
Write-Info "Manual review: confirm 75s smoke completed in under ~10 min."
Write-Host ""

# --- 8. Summary ---
Write-Host "[8/8] Summary"
Write-Host "  PASS: $($script:PASSES)"
Write-Host "  FAIL: $($script:FAILS)"
Write-Host ""

$report = Join-Path $KitDir "INSTALL_REPORT.txt"
@"
VSP Pipeline — Install Report
Generated: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
Image: $ImgTag
Host: $env:COMPUTERNAME

PASSES: $($script:PASSES)
FAILS:  $($script:FAILS)

$(if ($script:FAILS -eq 0) { "STATUS: READY`nAll checks passed. Pipeline ready to use.`nLaunch via the desktop shortcut (VSP Pipeline)." } else { "STATUS: FAILED`n$($script:FAILS) check(s) failed. Run collect_diagnostics.ps1 and contact support." })
"@ | Set-Content $report

Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue

if ($script:FAILS -gt 0) {
    Write-Host "Post-install check FAILED. See $Log and $report" -ForegroundColor Red
    exit 1
} else {
    Write-Host "Post-install check passed. Image is ready." -ForegroundColor Green
    Write-Host "Report: $report"
    exit 0
}
