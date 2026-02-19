#!/usr/bin/env bash
# ==================================================
# Pipeline Smoke Test
# ==================================================
# Quick smoke test of pipeline paths and dependencies
# Does NOT run the full pipeline, just validates setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/vsp_docker/galaxy_export"

PASSED=0
FAILED=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() {
    echo -e "${GREEN}✓${NC} $*"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $*"
    ((FAILED++))
}

echo "=================================================="
echo "Pipeline Smoke Test (EC2)"
echo "=================================================="
echo ""

# ==================================================
# Check Critical Executables
# ==================================================
echo "Checking critical executables..."

EXECUTABLES=(
    "ffmpeg"
    "ffprobe"
    "python3"
    "bash"
)

for exe in "${EXECUTABLES[@]}"; do
    if command -v "$exe" &>/dev/null; then
        pass "$exe found in PATH"
    else
        fail "$exe NOT FOUND in PATH"
    fi
done

echo ""

# ==================================================
# Check Virtual Environments
# ==================================================
echo "Checking virtual environments..."

if [ -d "/home/ubuntu/auto_avsr/pre-process-venv" ]; then
    if [ -f "/home/ubuntu/auto_avsr/pre-process-venv/bin/activate" ]; then
        pass "ASR venv exists and has activate script"
    else
        fail "ASR venv missing activate script"
    fi
else
    fail "ASR venv not found"
fi

if [ -d "/home/ubuntu/vsp-llm-yoad-venv" ]; then
    if [ -f "/home/ubuntu/vsp-llm-yoad-venv/bin/activate" ]; then
        pass "VSP-LLM venv exists and has activate script"
    else
        fail "VSP-LLM venv missing activate script"
    fi
else
    fail "VSP-LLM venv not found"
fi

echo ""

# ==================================================
# Check Pipeline Script
# ==================================================
echo "Checking main pipeline script..."

if [ -f "run_flat_english_pipeline.sh" ]; then
    pass "Main pipeline script exists"

    if [ -x "run_flat_english_pipeline.sh" ]; then
        pass "Main pipeline script is executable"
    else
        fail "Main pipeline script not executable"
    fi

    # Syntax check
    if bash -n "run_flat_english_pipeline.sh" 2>/dev/null; then
        pass "Main pipeline script has valid syntax"
    else
        fail "Main pipeline script has syntax errors"
    fi
else
    fail "Main pipeline script not found"
fi

echo ""

# ==================================================
# Check lib Modules
# ==================================================
echo "Checking lib modules..."

MODULES=(
    "lib/common.sh"
    "lib/config.sh"
    "lib/archive.sh"
    "lib/normalization.sh"
    "lib/asr.sh"
    "lib/lrs3_prep.sh"
    "lib/manifests.sh"
    "lib/clustering.sh"
    "lib/decode.sh"
    "lib/outputs.sh"
    "lib/venv/venv_utils.sh"
)

for module in "${MODULES[@]}"; do
    if [ -f "$module" ]; then
        if bash -n "$module" 2>/dev/null; then
            pass "$module exists and has valid syntax"
        else
            fail "$module has syntax errors"
        fi
    else
        fail "$module not found"
    fi
done

echo ""

# ==================================================
# Check Component Directories
# ==================================================
echo "Checking component directories..."

DIRS=(
    "/home/ubuntu/auto_avsr"
    "/home/ubuntu/auto_avsr/preparation"
    "/home/ubuntu/VSP-LLM"
    "/home/ubuntu/VSP-LLM/src"
    "/home/ubuntu/VSP-LLM/scripts"
    "/home/ubuntu/VSP-LLM/checkpoints"
    "/home/ubuntu/av_hubert"
    "/home/ubuntu/vsp_input"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        pass "$dir exists"
    else
        fail "$dir not found"
    fi
done

echo ""

# ==================================================
# Check Critical Scripts
# ==================================================
echo "Checking critical component scripts..."

SCRIPTS=(
    "auto_avsr/asr_to_words_notime.py"
    "auto_avsr/preparation/preprocess_lrs2lrs3.py"
    "auto_avsr/preparation/fast_segment.py"
    "auto_avsr/preparation/preprocess_with_overlap.py"
    "VSP-LLM/src/vsp_llm_decode.py"
    "VSP-LLM/scripts/run_flat_kmeans.sh"
    "VSP-LLM/scripts/run_cluster_counts.sh"
    "VSP-LLM/scripts/make_report.py"
    "VSP-LLM/scripts/make_burn.py"
    "av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        pass "$script exists"
    else
        fail "$script not found"
    fi
done

echo ""

# ==================================================
# Check Model Checkpoints
# ==================================================
echo "Checking model checkpoints..."

CHECKPOINTS=(
    "/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf"
    "/home/ubuntu/VSP-LLM/checkpoints/large_vox_iter5.pt"
    "/home/ubuntu/VSP-LLM/checkpoints/checkpoint_finetune.pt"
)

for checkpoint in "${CHECKPOINTS[@]}"; do
    if [ -e "$checkpoint" ]; then
        pass "Checkpoint exists: $(basename "$checkpoint")"
    else
        fail "Checkpoint missing: $(basename "$checkpoint")"
    fi
done

echo ""

# ==================================================
# Check Whisper Model Cache
# ==================================================
echo "Checking Whisper model cache..."

WHISPER_CACHE="/home/ubuntu/vsp_docker/galaxy_export/whisper"
if [ -d "$WHISPER_CACHE" ]; then
    pass "Whisper cache directory exists"

    # Check for medium model
    if [ -f "$WHISPER_CACHE/medium.pt" ]; then
        pass "Whisper medium model found"
    else
        fail "Whisper medium model not found"
    fi
else
    fail "Whisper cache directory not found"
fi

echo ""

# ==================================================
# Check UI Components
# ==================================================
echo "Checking VSP UI components..."

UI_FILES=(
    "vsp-ui/app/server.py"
    "vsp-ui/app/config.py"
    "vsp-ui/app/services/validator.py"
    "vsp-ui/app/services/pipeline_runner.py"
    "vsp-ui/app/services/transcription_manager.py"
    "vsp-ui/app/static/index.html"
    "vsp-ui/app/static/app.js"
    "vsp-ui/app/static/style.css"
)

for file in "${UI_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "UI file exists: $(basename "$file")"
    else
        fail "UI file not found: $(basename "$file")"
    fi
done

echo ""

# ==================================================
# Test Environment Variables
# ==================================================
echo "Testing environment configuration..."

source lib/config.sh

if [[ "$ENV_TYPE" == "ec2" ]]; then
    pass "Environment correctly detected as EC2"
else
    fail "Environment detection incorrect: $ENV_TYPE"
fi

if [[ "$BASE_PATH" == "/home/ubuntu" ]]; then
    pass "BASE_PATH correct: $BASE_PATH"
else
    fail "BASE_PATH incorrect: $BASE_PATH"
fi

if [[ "$AUTO_AVSR" == "/home/ubuntu/auto_avsr" ]]; then
    pass "AUTO_AVSR path correct"
else
    fail "AUTO_AVSR path incorrect: $AUTO_AVSR"
fi

if [[ "$VSP" == "/home/ubuntu/VSP-LLM" ]]; then
    pass "VSP path correct"
else
    fail "VSP path incorrect: $VSP"
fi

echo ""

# ==================================================
# Summary
# ==================================================
echo "=================================================="
echo "Smoke Test Summary"
echo "=================================================="
echo ""

TOTAL=$((PASSED + FAILED))
echo "Tests run: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL SMOKE TESTS PASSED${NC}"
    echo ""
    echo "The pipeline appears to be correctly configured for EC2."
    echo "All critical files, scripts, and dependencies are present."
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME SMOKE TESTS FAILED${NC}"
    echo ""
    echo "Please review the failures above before running the pipeline."
    echo ""
    exit 1
fi
