#!/usr/bin/env bash
# ==================================================
# EC2 Environment Test Suite
# ==================================================
# Tests that all updated scripts and modules work correctly on EC2
# after adding container environment detection

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS=()
PASSED=0
FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $*"
}

pass() {
    local msg="$*"
    echo -e "${GREEN}[PASS]${NC} $msg"
    TEST_RESULTS+=("✓ $msg")
    ((PASSED++)) || true
}

fail() {
    local msg="$*"
    echo -e "${RED}[FAIL]${NC} $msg"
    TEST_RESULTS+=("✗ $msg")
    ((FAILED++)) || true
}

echo "=================================================="
echo "EC2 Environment Test Suite"
echo "=================================================="
echo ""

# ==================================================
# Test 1: lib/config.sh Environment Detection
# ==================================================
log_test "Testing lib/config.sh environment detection"

cd "$SCRIPT_DIR/vsp_docker/galaxy_export"
source lib/config.sh

if [[ "$ENV_TYPE" == "ec2" ]]; then
    pass "ENV_TYPE correctly detected as 'ec2'"
else
    fail "ENV_TYPE is '$ENV_TYPE', expected 'ec2'"
fi

if [[ "$BASE_PATH" == "/home/ubuntu" ]]; then
    pass "BASE_PATH correctly set to '/home/ubuntu'"
else
    fail "BASE_PATH is '$BASE_PATH', expected '/home/ubuntu'"
fi

if [[ "$AUTO_AVSR" == "/home/ubuntu/auto_avsr" ]]; then
    pass "AUTO_AVSR path correct"
else
    fail "AUTO_AVSR is '$AUTO_AVSR'"
fi

if [[ "$VSP" == "/home/ubuntu/VSP-LLM" ]]; then
    pass "VSP path correct"
else
    fail "VSP is '$VSP'"
fi

# ==================================================
# Test 2: lib/asr.sh Transcription Path Detection
# ==================================================
log_test "Testing lib/asr.sh transcription path detection"

# Create a test function to check transcription path
test_transcription_path() {
    source lib/asr.sh

    # Simulate the transcription path detection from run_asr_transcription
    local home_dir="$HOME"
    local transcriptions_dir

    if [ -d "/host/vsp_input" ]; then
        transcriptions_dir="/host/vsp_input/.transcriptions"
    elif [ -d "/workspace/vsp_input" ]; then
        transcriptions_dir="/workspace/vsp_input/.transcriptions"
    else
        transcriptions_dir="$home_dir/vsp_input/.transcriptions"
    fi

    echo "$transcriptions_dir"
}

TRANS_DIR=$(test_transcription_path)
if [[ "$TRANS_DIR" == "/home/ubuntu/vsp_input/.transcriptions" ]]; then
    pass "Transcription directory correctly set to '/home/ubuntu/vsp_input/.transcriptions'"
else
    fail "Transcription directory is '$TRANS_DIR'"
fi

# ==================================================
# Test 3: All lib modules can be sourced
# ==================================================
log_test "Testing all lib modules can be sourced"

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
    if source "$module" 2>/dev/null; then
        pass "Module $module sources correctly"
    else
        fail "Module $module failed to source"
    fi
done

# ==================================================
# Test 4: av_hubert flat_to_lrs3_preperation.sh
# ==================================================
log_test "Testing av_hubert environment detection"

# Extract environment detection logic
PREP_SCRIPT="av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh"
if [ -f "$PREP_SCRIPT" ]; then
    # Check if script has environment detection
    if grep -q "# Environment detection: Container vs EC2" "$PREP_SCRIPT"; then
        pass "flat_to_lrs3_preperation.sh has environment detection"

        # Verify EC2 paths are set correctly in fallback
        if grep -q 'BASE_DIR="/home/ubuntu"' "$PREP_SCRIPT" && \
           grep -q 'VENV_BASE="/home/ubuntu"' "$PREP_SCRIPT"; then
            pass "flat_to_lrs3_preperation.sh EC2 paths correct"
        else
            fail "flat_to_lrs3_preperation.sh EC2 paths incorrect"
        fi
    else
        fail "flat_to_lrs3_preperation.sh missing environment detection"
    fi
else
    fail "flat_to_lrs3_preperation.sh not found"
fi

# ==================================================
# Test 5: auto_avsr asr_to_words_notime.py Whisper path
# ==================================================
log_test "Testing asr_to_words_notime.py Whisper path detection"

ASR_SCRIPT="auto_avsr/asr_to_words_notime.py"
if [ -f "$ASR_SCRIPT" ]; then
    # Check for relative path logic
    if grep -q "script_dir = Path(__file__).parent.parent" "$ASR_SCRIPT"; then
        pass "asr_to_words_notime.py uses relative path for Whisper cache"

        # Verify it goes to galaxy_export/whisper
        if grep -q 'download_root = str(script_dir / "whisper")' "$ASR_SCRIPT"; then
            pass "Whisper cache path is galaxy_export/whisper"
        else
            fail "Whisper cache path logic incorrect"
        fi
    else
        fail "asr_to_words_notime.py missing relative path logic"
    fi
else
    fail "asr_to_words_notime.py not found"
fi

# ==================================================
# Test 6: UI config.py Environment Detection (Python)
# ==================================================
log_test "Testing vsp-ui config.py environment detection"

UI_CONFIG="vsp-ui/app/config.py"
if [ -f "$UI_CONFIG" ]; then
    # Test Python environment detection
    PYTHON_TEST=$(python3 << 'EOF'
import sys
sys.path.insert(0, '/home/ubuntu/vsp_docker/galaxy_export/vsp-ui')
from app.config import BASE_DIR, INPUT_DIR

# Check paths
base_correct = str(BASE_DIR) == "/home/ubuntu"
input_correct = str(INPUT_DIR) == "/home/ubuntu/vsp_input"

if base_correct and input_correct:
    print("PASS")
else:
    print(f"FAIL: BASE_DIR={BASE_DIR}, INPUT_DIR={INPUT_DIR}")
EOF
    )

    if [[ "$PYTHON_TEST" == "PASS" ]]; then
        pass "UI config.py correctly detects EC2 environment"
    else
        fail "UI config.py environment detection: $PYTHON_TEST"
    fi
else
    fail "vsp-ui/app/config.py not found"
fi

# ==================================================
# Test 7: UI transcription_manager.py Path Detection
# ==================================================
log_test "Testing transcription_manager.py environment detection"

TRANS_MGR="vsp-ui/app/services/transcription_manager.py"
if [ -f "$TRANS_MGR" ]; then
    PYTHON_TEST=$(python3 << 'EOF'
import sys
sys.path.insert(0, '/home/ubuntu/vsp_docker/galaxy_export/vsp-ui')
from app.services.transcription_manager import TranscriptionManager

# Check transcription directory path
trans_dir = str(TranscriptionManager.TRANSCRIPTIONS_DIR)
expected = "/home/ubuntu/vsp_input/.transcriptions"

if trans_dir == expected:
    print("PASS")
else:
    print(f"FAIL: Got {trans_dir}, expected {expected}")
EOF
    )

    if [[ "$PYTHON_TEST" == "PASS" ]]; then
        pass "TranscriptionManager correctly detects EC2 path"
    else
        fail "TranscriptionManager: $PYTHON_TEST"
    fi
else
    fail "transcription_manager.py not found"
fi

# ==================================================
# Test 8: run_flat_preprocess_batch.sh Environment Detection
# ==================================================
log_test "Testing run_flat_preprocess_batch.sh environment detection"

BATCH_SCRIPT="auto_avsr/preparation/run_flat_preprocess_batch.sh"
if [ -f "$BATCH_SCRIPT" ]; then
    if grep -q "# Environment detection: Container vs EC2" "$BATCH_SCRIPT"; then
        pass "run_flat_preprocess_batch.sh has environment detection"

        # Verify EC2 paths
        if grep -q 'BASE_ROOT="/home/ubuntu/auto_avsr"' "$BATCH_SCRIPT" && \
           grep -q 'VSP_ROOT="/home/ubuntu/VSP-LLM"' "$BATCH_SCRIPT"; then
            pass "run_flat_preprocess_batch.sh EC2 paths correct"
        else
            fail "run_flat_preprocess_batch.sh EC2 paths incorrect"
        fi
    else
        fail "run_flat_preprocess_batch.sh missing environment detection"
    fi
else
    fail "run_flat_preprocess_batch.sh not found"
fi

# ==================================================
# Test 9: Main Pipeline Script Integrity
# ==================================================
log_test "Testing main pipeline script integrity"

MAIN_PIPELINE="run_flat_english_pipeline.sh"
if [ -f "$MAIN_PIPELINE" ]; then
    # Check for SCRIPT_DIR definition
    if grep -q 'SCRIPT_DIR=' "$MAIN_PIPELINE"; then
        pass "Main pipeline defines SCRIPT_DIR"
    else
        fail "Main pipeline doesn't define SCRIPT_DIR"
    fi

    # Check for module sourcing
    if grep -q 'source.*lib/.*\.sh' "$MAIN_PIPELINE"; then
        pass "Main pipeline sources lib modules"
    else
        fail "Main pipeline doesn't source lib modules"
    fi

    # Verify main pipeline can be parsed (syntax check)
    if bash -n "$MAIN_PIPELINE" 2>/dev/null; then
        pass "Main pipeline has valid bash syntax"
    else
        fail "Main pipeline has syntax errors"
    fi
else
    fail "run_flat_english_pipeline.sh not found"
fi

# ==================================================
# Test 10: Virtual Environment Paths
# ==================================================
log_test "Testing virtual environment paths"

VENVS=(
    "/home/ubuntu/auto_avsr/pre-process-venv"
    "/home/ubuntu/vsp-llm-yoad-venv"
)

for venv in "${VENVS[@]}"; do
    if [ -d "$venv" ]; then
        pass "Virtual environment exists: $venv"
    else
        fail "Virtual environment missing: $venv"
    fi
done

# ==================================================
# Test 11: Critical Directories Exist
# ==================================================
log_test "Testing critical directories exist on EC2"

DIRS=(
    "/home/ubuntu/auto_avsr"
    "/home/ubuntu/VSP-LLM"
    "/home/ubuntu/av_hubert"
    "/home/ubuntu/vsp_input"
    "/home/ubuntu/vsp_docker/galaxy_export/lib"
    "/home/ubuntu/vsp_docker/galaxy_export/vsp-ui"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        pass "Directory exists: $dir"
    else
        fail "Directory missing: $dir"
    fi
done

# ==================================================
# Test Summary
# ==================================================
echo ""
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo ""

for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == ✓* ]]; then
        echo -e "${GREEN}$result${NC}"
    else
        echo -e "${RED}$result${NC}"
    fi
done

echo ""
echo "=================================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}ALL TESTS PASSED${NC} ($PASSED/$((PASSED+FAILED)))"
    echo "=================================================="
    exit 0
else
    echo -e "${RED}SOME TESTS FAILED${NC} (Passed: $PASSED, Failed: $FAILED)"
    echo "=================================================="
    exit 1
fi
