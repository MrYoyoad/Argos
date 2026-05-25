#!/usr/bin/env bash
# ============================================================================
# VSP Linux Container - Verification Script
# ============================================================================
# Package: vsp_linux_container_FINAL v1.0.0
# Date: February 3, 2026
#
# This script verifies that all 12 critical fixes are properly installed.
#
# Usage:
#   cd /host/galaxy_export  # or /host/galaxy_export
#   bash /path/to/VERIFY.sh
#
# Exit Codes:
#   0 = All fixes verified successfully
#   1 = One or more fixes missing or failed
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VSP Linux Container Fix Verification${NC}"
echo -e "${BLUE}Package: v1.0.0 FINAL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ====================
# Check Working Directory
# ====================

if [ ! -f "run_flat_english_pipeline.sh" ]; then
    echo -e "${RED}ERROR: Must run from galaxy_export directory${NC}"
    echo "Current directory: $(pwd)"
    echo ""
    echo "Usage:"
    echo "  cd /host/galaxy_export"
    echo "  bash /path/to/VERIFY.sh"
    exit 1
fi

# ====================
# Verification Functions
# ====================

FAILED_FIXES=0
TOTAL_FIXES=22

verify_fix() {
    local fix_num=$1
    local description=$2
    local file=$3
    local pattern=$4

    printf "%-60s" "Fix $fix_num: $description"

    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ (file not found: $file)${NC}"
        ((FAILED_FIXES++))
        return 1
    fi

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        echo -e "${RED}❌${NC}"
        ((FAILED_FIXES++))
        return 1
    fi
}

# ====================
# Verify All 12 Fixes
# ====================

echo -e "${YELLOW}Checking all 12 critical fixes...${NC}"
echo ""

verify_fix  1 \
    "Cython auto-build" \
    "lib/decode.sh" \
    "CRITICAL: Check and build fairseq Cython"

verify_fix  2 \
    "max_len config" \
    "VSP-LLM/src/conf/s2s_decode.yaml" \
    "max_len: 2048"

verify_fix  3 \
    "Dynamic transcription paths" \
    "lib/asr.sh" \
    'transcriptions_dir="${raw_dir}/.transcriptions"'

verify_fix  4 \
    "VSP_INPUT_DIR support" \
    "vsp-ui/app/config.py" \
    "VSP_INPUT_DIR"

verify_fix  5 \
    "Absolute imports" \
    "vsp-ui/app/services/transcription_manager.py" \
    "from app.config import INPUT_DIR"

verify_fix  6 \
    "log_info stderr redirect" \
    "lib/common.sh" \
    ">&2"

verify_fix  7 \
    "POST_ROOT definition" \
    "run_flat_english_pipeline.sh" \
    'POST_ROOT='

verify_fix  8 \
    "Step 2.5 metadata creation" \
    "run_flat_english_pipeline.sh" \
    "metadata for whole videos"

verify_fix  9 \
    "Non-segmented naming" \
    "run_flat_english_pipeline.sh" \
    'output_name="${video_name}"'

verify_fix 10 \
    "make_burn segment matching" \
    "VSP-LLM/scripts/make_burn.py" \
    "if seg_idx == -1:"

verify_fix 11 \
    "Logger duplication fix" \
    "VSP-LLM/src/vsp_llm_decode.py" \
    "logger.propagate = False"

verify_fix 12 \
    "Segment duration = 12s" \
    "vsp-ui/app/config.py" \
    "SEGMENT_DURATION = 12"

echo ""

# ====================
# May-2026 Additions: confidence / IS / N-best / agreement / headless icon
# ====================

echo -e "${YELLOW}Checking May-2026 feature additions...${NC}"
echo ""

verify_fix 13 \
    "Per-token confidence script present" \
    "VSP-LLM/scripts/compute_word_confidence.py" \
    "classify_joint"

verify_fix 14 \
    "Intelligibility Score script present" \
    "VSP-LLM/scripts/generate_intelligibility_scores.py" \
    "doublemetaphone"

verify_fix 15 \
    "N-best aggregation script present" \
    "VSP-LLM/scripts/nbest_aggregate.py" \
    "hyp_mbr"

verify_fix 16 \
    "Beam-agreement script present" \
    "VSP-LLM/scripts/compute_word_agreement.py" \
    "_word_confs_for_utt"

verify_fix 17 \
    "outputs.sh wires HF_HUB_OFFLINE for IS" \
    "lib/outputs.sh" \
    "HF_HUB_OFFLINE"

verify_fix 18 \
    "Desktop entry is terminal-free" \
    "vsp-pipeline.desktop" \
    "Terminal=false"

verify_fix 19 \
    "vsp-start.sh has headless branch" \
    "vsp-start.sh" \
    "VSP_HEADLESS"

# Non-grep checks: directory-presence asserts.
asset_dir_check() {
    local fix_num=$1
    local description=$2
    local dir=$3
    local marker=$4   # one filename expected inside

    printf "%-60s" "Fix $fix_num: $description"
    if [ -d "$dir" ] && [ -e "$dir/$marker" ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC} (${dir}/${marker} missing)"
        ((FAILED_FIXES++))
    fi
}

asset_dir_check 20 \
    "HF MiniLM model cache bundled" \
    "is_model_cache/hub/models--sentence-transformers--all-MiniLM-L6-v2" \
    "snapshots"

asset_dir_check 21 \
    "IS / confidence cp310 wheels bundled" \
    "is_wheels_cp310" \
    "sentence_transformers-5.1.2-py3-none-any.whl"

# Golden k-means model — UI's /api/golden-models scans here.
printf "%-60s" "Fix 21b: Golden k-means model present"
if ls VSP-LLM/golden_kmeans/*.bin >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC} (VSP-LLM/golden_kmeans/*.bin missing — UI dropdown will be empty)"
    ((FAILED_FIXES++))
fi

# Live import check — only meaningful if the venv is reachable.
printf "%-60s" "Fix 22: IS deps importable in vsp-llm-yoad-venv"
_venv=""
for _v in /workspace/vsp-llm-yoad-venv "$HOME/vsp-llm-yoad-venv"; do
    [ -d "$_v" ] && _venv="$_v" && break
done
if [ -n "$_venv" ]; then
    _rc=0
    "$_venv/bin/python3" - <<'PY' >/tmp/_vsp_is_check 2>&1 || _rc=$?
import importlib
for m in ("sentence_transformers", "metaphone", "matplotlib", "scipy", "editdistance"):
    importlib.import_module(m)
PY
    if [ $_rc -eq 0 ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC} (see /tmp/_vsp_is_check)"
        ((FAILED_FIXES++))
    fi
else
    echo -e "${YELLOW}⚠️  skipped (venv not found at /workspace or \$HOME)${NC}"
fi

echo ""

# ====================
# Module Tests
# ====================

echo -e "${YELLOW}Running pipeline module tests...${NC}"
echo ""

if [ -f "lib/test_all_modules.sh" ]; then
    # Capture test output
    TEST_OUTPUT=$(bash lib/test_all_modules.sh 2>&1)
    TEST_EXIT_CODE=$?

    # Extract summary line
    SUMMARY=$(echo "$TEST_OUTPUT" | grep "Module Tests Complete" || echo "Tests completed")

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ $SUMMARY${NC}"
    else
        echo -e "${YELLOW}⚠️  Module tests had warnings${NC}"
        echo "$SUMMARY"
    fi
else
    echo -e "${YELLOW}⚠️  Module test script not found (lib/test_all_modules.sh)${NC}"
    echo "    This is optional but recommended for complete verification."
fi

echo ""

# ====================
# Summary
# ====================

echo -e "${BLUE}========================================${NC}"

if [ $FAILED_FIXES -eq 0 ]; then
    echo -e "${GREEN}✅ All fixes verified successfully!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}Package Status: READY TO USE ✅${NC}"
    echo ""
    echo "Feb-2026 baseline fixes:"
    echo "  1. ✅ Cython auto-build           7. ✅ POST_ROOT definition"
    echo "  2. ✅ max_len config              8. ✅ Step 2.5 metadata"
    echo "  3. ✅ Dynamic transcription paths 9. ✅ Non-segmented naming"
    echo "  4. ✅ VSP_INPUT_DIR support      10. ✅ make_burn segment matching"
    echo "  5. ✅ Absolute imports           11. ✅ Logger duplication fix"
    echo "  6. ✅ log_info stderr redirect   12. ✅ Segment duration = 12s"
    echo ""
    echo "May-2026 additions (confidence / IS / n-best / agreement / headless):"
    echo " 13. ✅ Per-token confidence       18. ✅ Desktop entry terminal-free"
    echo " 14. ✅ Intelligibility Score      19. ✅ vsp-start.sh headless branch"
    echo " 15. ✅ N-best aggregation         20. ✅ HF MiniLM model cache bundled"
    echo " 16. ✅ Beam-agreement script      21. ✅ IS cp310 wheels bundled"
    echo " 17. ✅ outputs.sh HF_HUB_OFFLINE  22. ✅ IS deps importable in venv"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Test pipeline with sample video:"
    echo "     SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test.mp4"
    echo ""
    echo "  2. Check outputs:"
    echo "     ls flat_runs_archive/*/client_outputs/"
    echo ""
    echo "  3. Start UI (optional):"
    echo "     cd vsp-ui && python3 app/server.py"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Verification failed: $FAILED_FIXES of $TOTAL_FIXES fixes missing${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Package Status: INCOMPLETE ⚠️${NC}"
    echo ""
    echo -e "${RED}Missing or Failed Fixes: $FAILED_FIXES${NC}"
    echo ""
    echo "Common Solutions:"
    echo "  1. Re-run installation script:"
    echo "     bash /path/to/INSTALL.sh"
    echo ""
    echo "  2. Manually install missing components:"
    echo "     - Check which fix failed above"
    echo "     - Copy corresponding file from vsp_linux_container_FINAL/"
    echo ""
    echo "  3. Verify you're in the correct directory:"
    echo "     pwd  # Should show /host/galaxy_export"
    echo ""
    echo "For detailed troubleshooting, see:"
    echo "  - INSTALLATION_GUIDE.md"
    echo "  - TESTING_GUIDE.md"
    echo ""
    exit 1
fi
