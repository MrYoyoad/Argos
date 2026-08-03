#!/usr/bin/env bash
# ==================================================
# Environment Readiness Test
# ==================================================
# Validates that a (fresh or existing) EC2 box has everything the VSP
# pipeline needs: GPU, system tools, both venvs with their critical
# imports, model files at minimum sizes, and auth.
#
# Companion doc: docs/guides/ec2-setup-from-scratch.md (§7 validation ladder)
# Read-only: performs no writes outside stdout.
#
# Exit codes: 0 = all checks passed (warnings allowed), 1 = at least one FAIL.

set -euo pipefail

PASSED=0
FAILED=0
WARNED=0
TEST_RESULTS=()

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

warn() {
    local msg="$*"
    echo -e "${YELLOW}[WARN]${NC} $msg"
    TEST_RESULTS+=("! $msg")
    ((WARNED++)) || true
}

HOME_DIR="${HOME:-/home/ubuntu}"
ASR_VENV="$HOME_DIR/auto_avsr/pre-process-venv"
VSP_VENV="$HOME_DIR/vsp-llm-yoad-venv"

# Check a file exists and is at least N bytes.
# $1=path  $2=min bytes  $3=label
check_model_file() {
    local path="$1" min_bytes="$2" label="$3"
    if [ ! -f "$path" ]; then
        fail "$label missing: $path"
        return
    fi
    local size
    size=$(stat -c%s "$path" 2>/dev/null || echo 0)
    if [ "$size" -ge "$min_bytes" ]; then
        pass "$label present ($(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")): $path"
    else
        fail "$label too small (${size} bytes < ${min_bytes}): $path"
    fi
}

echo "=================================================="
echo "Environment Readiness Test"
echo "=================================================="
echo ""

# ==================================================
# 1. GPU / driver
# ==================================================
log_test "GPU and NVIDIA driver"

if command -v nvidia-smi &>/dev/null; then
    pass "nvidia-smi present"
    GPU_LINE=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -n1 || true)
    if [ -n "$GPU_LINE" ]; then
        pass "GPU listed: $GPU_LINE"
    else
        fail "nvidia-smi present but no GPU listed"
    fi
else
    fail "nvidia-smi NOT found (install NVIDIA driver >= 570)"
fi

echo ""

# ==================================================
# 2. System tools
# ==================================================
log_test "System tools"

for exe in ffmpeg ffprobe python3.9; do
    if command -v "$exe" &>/dev/null; then
        pass "$exe found in PATH"
    else
        fail "$exe NOT FOUND in PATH"
    fi
done

echo ""

# ==================================================
# 3. Virtual environments exist
# ==================================================
log_test "Virtual environments"

for venv in "$ASR_VENV" "$VSP_VENV"; do
    if [ -d "$venv" ] && [ -x "$venv/bin/python" ]; then
        pass "Venv exists with python: $venv"
    else
        fail "Venv missing or broken: $venv"
    fi
done

echo ""

# ==================================================
# 4. ASR venv imports (torch, whisper, mediapipe)
# ==================================================
log_test "ASR venv imports ($ASR_VENV)"

if [ -x "$ASR_VENV/bin/python" ]; then
    if TORCH_OUT=$("$ASR_VENV/bin/python" -c 'import torch; print(torch.__version__, torch.cuda.is_available())' 2>&1); then
        TORCH_VER=$(echo "$TORCH_OUT" | awk '{print $1}')
        TORCH_CUDA=$(echo "$TORCH_OUT" | awk '{print $2}')
        pass "ASR venv: import torch OK (version $TORCH_VER)"
        if [ "$TORCH_CUDA" = "True" ]; then
            pass "ASR venv: torch.cuda.is_available() == True"
        else
            warn "ASR venv: torch.cuda.is_available() == False (CPU-only box? GPU stages will not run)"
        fi
    else
        fail "ASR venv: import torch FAILED"
    fi

    if "$ASR_VENV/bin/python" -c 'import whisper' 2>/dev/null; then
        pass "ASR venv: import whisper OK"
    else
        fail "ASR venv: import whisper FAILED"
    fi

    if "$ASR_VENV/bin/python" -c 'import mediapipe' 2>/dev/null; then
        pass "ASR venv: import mediapipe OK"
    else
        fail "ASR venv: import mediapipe FAILED"
    fi
else
    fail "ASR venv python missing — skipping ASR import checks"
fi

echo ""

# ==================================================
# 5. VSP venv imports (torch, fairseq + Cython ext, spacy, sentence-transformers)
# ==================================================
log_test "VSP venv imports ($VSP_VENV)"

if [ -x "$VSP_VENV/bin/python" ]; then
    if TORCH_OUT=$("$VSP_VENV/bin/python" -c 'import torch; print(torch.__version__, torch.cuda.is_available())' 2>&1); then
        TORCH_VER=$(echo "$TORCH_OUT" | awk '{print $1}')
        TORCH_CUDA=$(echo "$TORCH_OUT" | awk '{print $2}')
        pass "VSP venv: import torch OK (version $TORCH_VER)"
        if [ "$TORCH_CUDA" = "True" ]; then
            pass "VSP venv: torch.cuda.is_available() == True"
        else
            warn "VSP venv: torch.cuda.is_available() == False (CPU-only box? decode will not run)"
        fi
    else
        fail "VSP venv: import torch FAILED"
    fi

    if "$VSP_VENV/bin/python" -c 'import fairseq' 2>/dev/null; then
        pass "VSP venv: import fairseq OK"
    else
        fail "VSP venv: import fairseq FAILED (editable install from VSP-LLM/fairseq missing?)"
    fi

    # The Cython trap: lib/decode.sh auto-builds this on first decode; if the
    # import fails here, first decode will spend time building (or fail offline).
    if "$VSP_VENV/bin/python" -c 'from fairseq.data import data_utils_fast' 2>/dev/null; then
        pass "VSP venv: fairseq Cython extensions built (data_utils_fast imports)"
    else
        fail "VSP venv: fairseq.data.data_utils_fast NOT importable — run: cd ~/VSP-LLM/fairseq && $VSP_VENV/bin/python setup.py build_ext --inplace"
    fi

    if "$VSP_VENV/bin/python" -c 'import spacy; spacy.load("en_core_web_sm")' 2>/dev/null; then
        pass "VSP venv: spacy + en_core_web_sm load OK"
    else
        fail "VSP venv: spacy or en_core_web_sm model FAILED"
    fi

    if "$VSP_VENV/bin/python" -c 'import sentence_transformers' 2>/dev/null; then
        pass "VSP venv: import sentence_transformers OK"
    else
        fail "VSP venv: import sentence_transformers FAILED (IS scoring unavailable)"
    fi
else
    fail "VSP venv python missing — skipping VSP import checks"
fi

echo ""

# ==================================================
# 6. Model files (minimum sizes)
# ==================================================
log_test "Model files"

GB=1073741824
check_model_file "$HOME_DIR/VSP-LLM/checkpoints/checkpoint_finetune.pt" $((35 * GB / 10)) "Decode model checkpoint_finetune.pt (>3.5GB)"
check_model_file "$HOME_DIR/VSP-LLM/checkpoints/large_vox_iter5.pt"     $((3 * GB))       "AV-HuBERT large_vox_iter5.pt (>3GB)"
check_model_file "$HOME_DIR/.cache/whisper/large-v3.pt"                 $((25 * GB / 10)) "Whisper large-v3.pt (>2.5GB)"

KM_BIN="$HOME_DIR/golden_weights/baseline_20260218/flat_kmeans_200.bin"
if [ -f "$KM_BIN" ]; then
    pass "Golden k-means bin present: $KM_BIN"
else
    fail "Golden k-means bin missing: $KM_BIN"
fi

BUFFALO_DIR="$HOME_DIR/.insightface/models/buffalo_l"
if [ -d "$BUFFALO_DIR" ] && [ -n "$(ls -A "$BUFFALO_DIR" 2>/dev/null)" ]; then
    pass "insightface buffalo_l dir non-empty: $BUFFALO_DIR"
else
    fail "insightface buffalo_l dir missing or empty: $BUFFALO_DIR (pre-seed for offline use)"
fi

echo ""

# ==================================================
# 7. Auth (warn-only)
# ==================================================
log_test "Auth"

if [ -f "$HOME_DIR/.cache/huggingface/token" ]; then
    pass "HF token file exists: ~/.cache/huggingface/token"
else
    warn "HF token file missing (~/.cache/huggingface/token) — gated HF downloads (Llama-2) will fail; run huggingface-cli login"
fi

echo ""

# ==================================================
# Summary
# ==================================================
echo "=================================================="
echo "Readiness Summary"
echo "=================================================="
echo ""

for result in "${TEST_RESULTS[@]}"; do
    case "$result" in
        ✓*) echo -e "${GREEN}$result${NC}" ;;
        !*) echo -e "${YELLOW}$result${NC}" ;;
        *)  echo -e "${RED}$result${NC}" ;;
    esac
done

echo ""
echo "=================================================="
TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}ALL CHECKS PASSED${NC} ($PASSED/$TOTAL passed, $WARNED warning(s))"
    echo "=================================================="
    exit 0
else
    echo -e "${RED}SOME CHECKS FAILED${NC} (Passed: $PASSED, Failed: $FAILED, Warnings: $WARNED)"
    echo "=================================================="
    exit 1
fi
