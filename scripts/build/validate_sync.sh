#!/usr/bin/env bash
set -euo pipefail

# ==================================================
# Validate Container Sync
# ==================================================
# Checks that critical files exist and paths are correct
#
# Usage: ./sync/validate_sync.sh /path/to/container/export
# ==================================================

CONTAINER_DIR="${1:-}"

if [[ -z "$CONTAINER_DIR" ]]; then
    echo "Usage: $0 /path/to/container/export"
    exit 1
fi

if [[ ! -d "$CONTAINER_DIR" ]]; then
    echo "ERROR: Container directory does not exist: $CONTAINER_DIR"
    exit 1
fi

echo "=========================================="
echo "Validating Container Sync"
echo "=========================================="
echo "Container directory: ${CONTAINER_DIR}"
echo ""

ERRORS=0
WARNINGS=0

# ---------- Check Critical Files Exist ----------
echo ">>> Checking critical files exist..."

CRITICAL_FILES=(
    "run_flat_english_pipeline.sh"
    "VSP-LLM/scripts/run_flat_kmeans.sh"
    "VSP-LLM/scripts/decode.sh"
    "VSP-LLM/scripts/make_report.py"
    "vsp-ui/app/server.py"
    "vsp-ui/app/services/transcription_manager.py"
    "vsp-ui/app/services/validator.py"
    "vsp-ui/app/services/pipeline_runner.py"
    "vsp-ui/app/static/app.js"
    "vsp-ui/app/static/index.html"
    "vsp-ui/app/static/style.css"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [[ ! -f "${CONTAINER_DIR}/${file}" ]]; then
        echo "  ✗ MISSING: ${file}"
        ((ERRORS++))
    else
        echo "  ✓ ${file}"
    fi
done

# ---------- Check for Hardcoded EC2 Paths ----------
echo ""
echo ">>> Checking for hardcoded EC2 paths..."

# Check shell scripts for hardcoded /home/ubuntu
HARDCODED_PATHS=0

if [[ -f "${CONTAINER_DIR}/run_flat_english_pipeline.sh" ]]; then
    if grep -q "/home/ubuntu" "${CONTAINER_DIR}/run_flat_english_pipeline.sh"; then
        echo "  ⚠ WARNING: Found /home/ubuntu in run_flat_english_pipeline.sh"
        echo "    Lines with /home/ubuntu:"
        grep -n "/home/ubuntu" "${CONTAINER_DIR}/run_flat_english_pipeline.sh" | head -5
        ((WARNINGS++))
        HARDCODED_PATHS=1
    fi
fi

# Check VSP-LLM scripts
if [[ -d "${CONTAINER_DIR}/VSP-LLM/scripts" ]]; then
    if grep -r "/home/ubuntu" "${CONTAINER_DIR}/VSP-LLM/scripts"/*.sh 2>/dev/null; then
        echo "  ⚠ WARNING: Found /home/ubuntu in VSP-LLM/scripts/*.sh"
        ((WARNINGS++))
        HARDCODED_PATHS=1
    fi
fi

if [[ $HARDCODED_PATHS -eq 0 ]]; then
    echo "  ✓ No hardcoded /home/ubuntu paths found"
fi

# ---------- Check File Permissions ----------
echo ""
echo ">>> Checking executable permissions..."

EXECUTABLE_SCRIPTS=(
    "run_flat_english_pipeline.sh"
    "VSP-LLM/scripts/run_flat_kmeans.sh"
    "VSP-LLM/scripts/decode.sh"
)

for script in "${EXECUTABLE_SCRIPTS[@]}"; do
    if [[ -f "${CONTAINER_DIR}/${script}" ]]; then
        if [[ ! -x "${CONTAINER_DIR}/${script}" ]]; then
            echo "  ⚠ WARNING: ${script} is not executable"
            ((WARNINGS++))
        else
            echo "  ✓ ${script} is executable"
        fi
    fi
done

# ---------- Check Key Features Present ----------
echo ""
echo ">>> Checking for key features..."

# Check for transcription manager (8 pending updates)
if [[ -f "${CONTAINER_DIR}/vsp-ui/app/services/transcription_manager.py" ]]; then
    echo "  ✓ Transcription manager present (unified transcription management)"
else
    echo "  ✗ MISSING: transcription_manager.py (pending update #3)"
    ((ERRORS++))
fi

# Check for segment duration update in config
if [[ -f "${CONTAINER_DIR}/vsp-ui/app/config.py" ]]; then
    if grep -q "SEGMENT_DURATION.*=.*12" "${CONTAINER_DIR}/vsp-ui/app/config.py"; then
        echo "  ✓ Segment duration updated to 12s (pending update #4)"
    else
        echo "  ⚠ WARNING: Segment duration may not be updated to 12s"
        ((WARNINGS++))
    fi
fi

# Check for k-means toggle in pipeline runner
if [[ -f "${CONTAINER_DIR}/vsp-ui/app/services/pipeline_runner.py" ]]; then
    if grep -q "train_kmeans" "${CONTAINER_DIR}/vsp-ui/app/services/pipeline_runner.py"; then
        echo "  ✓ K-means toggle present (pending update #2)"
    else
        echo "  ⚠ WARNING: K-means toggle may not be implemented"
        ((WARNINGS++))
    fi
fi

# ---------- Summary ----------
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo "✓ Validation PASSED (no errors or warnings)"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo "⚠ Validation PASSED with ${WARNINGS} warnings"
    echo ""
    echo "Warnings indicate potential issues but sync appears functional."
    echo "Review warnings above and decide if manual fixes are needed."
    exit 0
else
    echo "✗ Validation FAILED"
    echo "  Errors: ${ERRORS}"
    echo "  Warnings: ${WARNINGS}"
    echo ""
    echo "Critical files are missing. Sync may be incomplete."
    exit 1
fi
