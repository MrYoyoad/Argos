#!/usr/bin/env bash
# ==============================================================================
# Container Sync Verification Script
# ==============================================================================
# Compares EC2 source files against both container deployments to detect drift.
# Run after any code change to ensure containers stay in sync.
#
# Usage:  bash verify_container_sync.sh [--fix]
#         --fix: automatically copy path-agnostic files that should be identical
#
# Exit codes:
#   0 = all files in sync
#   1 = files out of sync (details printed)
# ==============================================================================

set -u -o pipefail

EC2="/home/ubuntu"

# Auto-detect container directories (find the most recent dated version)
FINAL=$(ls -d "${EC2}/vsp_linux_container_FINAL_"* 2>/dev/null | sort -r | head -1)
GALAXY="${EC2}/vsp_docker/galaxy_export"

FIX_MODE=false
if [[ "${1:-}" == "--fix" ]]; then
    FIX_MODE=true
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0
FIXED=0

# ---- Helpers ----

check_identical() {
    local label="$1"
    local ec2_file="$2"
    local final_file="$3"
    local galaxy_file="$4"

    if [[ ! -f "$ec2_file" ]]; then
        echo -e "  ${YELLOW}SKIP${NC} $label (EC2 file missing: $ec2_file)"
        WARN=$((WARN+1))
        return
    fi

    local ec2_md5 final_md5 galaxy_md5
    ec2_md5=$(md5sum "$ec2_file" 2>/dev/null | awk '{print $1}')

    local ok=true

    # Check FINAL
    if [[ -n "$FINAL" && -f "$final_file" ]]; then
        final_md5=$(md5sum "$final_file" 2>/dev/null | awk '{print $1}')
        if [[ "$ec2_md5" != "$final_md5" ]]; then
            ok=false
            echo -e "  ${RED}DIFF${NC} $label  (EC2 vs FINAL)"
            if $FIX_MODE; then
                cp "$ec2_file" "$final_file"
                echo -e "       ${GREEN}FIXED${NC} → copied EC2 → FINAL"
                FIXED=$((FIXED+1))
            fi
        fi
    elif [[ -n "$FINAL" ]]; then
        ok=false
        echo -e "  ${YELLOW}MISS${NC} $label  (missing in FINAL: $final_file)"
        if $FIX_MODE; then
            mkdir -p "$(dirname "$final_file")"
            cp "$ec2_file" "$final_file"
            echo -e "       ${GREEN}FIXED${NC} → copied EC2 → FINAL"
            FIXED=$((FIXED+1))
        fi
    fi

    # Check Galaxy
    if [[ -f "$galaxy_file" ]]; then
        galaxy_md5=$(md5sum "$galaxy_file" 2>/dev/null | awk '{print $1}')
        if [[ "$ec2_md5" != "$galaxy_md5" ]]; then
            ok=false
            echo -e "  ${RED}DIFF${NC} $label  (EC2 vs Galaxy)"
            if $FIX_MODE; then
                cp "$ec2_file" "$galaxy_file"
                echo -e "       ${GREEN}FIXED${NC} → copied EC2 → Galaxy"
                FIXED=$((FIXED+1))
            fi
        fi
    else
        ok=false
        echo -e "  ${YELLOW}MISS${NC} $label  (missing in Galaxy: $galaxy_file)"
        if $FIX_MODE; then
            mkdir -p "$(dirname "$galaxy_file")"
            cp "$ec2_file" "$galaxy_file"
            echo -e "       ${GREEN}FIXED${NC} → copied EC2 → Galaxy"
            FIXED=$((FIXED+1))
        fi
    fi

    if $ok; then
        echo -e "  ${GREEN}OK${NC}   $label"
        PASS=$((PASS+1))
    else
        FAIL=$((FAIL+1))
    fi
}

check_expected_diff() {
    local label="$1"
    local ec2_file="$2"
    local final_file="$3"
    local galaxy_file="$4"
    local reason="$5"

    if [[ ! -f "$ec2_file" ]]; then
        echo -e "  ${YELLOW}SKIP${NC} $label (EC2 file missing)"
        WARN=$((WARN+1))
        return
    fi

    local line_ec2 line_final line_galaxy
    line_ec2=$(wc -l < "$ec2_file")

    echo -ne "  ${CYAN}DIFF${NC} $label  (expected: $reason)"

    if [[ -n "$FINAL" && -f "$final_file" ]]; then
        line_final=$(wc -l < "$final_file")
        echo -n "  [EC2:${line_ec2}L vs FINAL:${line_final}L"
    fi

    if [[ -f "$galaxy_file" ]]; then
        line_galaxy=$(wc -l < "$galaxy_file")
        echo -n " Galaxy:${line_galaxy}L"
    fi

    echo "]"
    PASS=$((PASS+1))
}

# ---- Main ----

echo "=============================================="
echo "  Container Sync Verification"
echo "=============================================="
echo
echo "  EC2:    $EC2"
echo "  FINAL:  ${FINAL:-NOT FOUND}"
echo "  Galaxy: $GALAXY"
echo

if [[ -z "$FINAL" ]]; then
    echo -e "${YELLOW}WARNING: No vsp_linux_container_FINAL_* directory found${NC}"
fi

# -----------------------------------------------
# Category 1: Path-agnostic files (MUST be identical)
# -----------------------------------------------
echo -e "${CYAN}=== Category 1: Path-Agnostic Files (must be identical) ===${NC}"
echo

echo "--- VSP-LLM Python Scripts ---"
check_identical "make_report.py" \
    "$EC2/VSP-LLM/scripts/make_report.py" \
    "${FINAL}/VSP-LLM/scripts/make_report.py" \
    "$GALAXY/VSP-LLM/scripts/make_report.py"

check_identical "make_burn.py" \
    "$EC2/VSP-LLM/scripts/make_burn.py" \
    "${FINAL}/VSP-LLM/scripts/make_burn.py" \
    "$GALAXY/VSP-LLM/scripts/make_burn.py"

echo
echo "--- VSP-LLM Config ---"
check_identical "s2s_decode.yaml" \
    "$EC2/VSP-LLM/src/conf/s2s_decode.yaml" \
    "${FINAL}/VSP-LLM/src/conf/s2s_decode.yaml" \
    "$GALAXY/VSP-LLM/src/conf/s2s_decode.yaml"

echo
echo "--- VSP-LLM Core ---"
check_identical "vsp_llm_decode.py" \
    "$EC2/VSP-LLM/src/vsp_llm_decode.py" \
    "${FINAL}/VSP-LLM/src/vsp_llm_decode.py" \
    "$GALAXY/VSP-LLM/src/vsp_llm_decode.py"

check_identical "vsp_llm.py" \
    "$EC2/VSP-LLM/src/vsp_llm.py" \
    "${FINAL}/VSP-LLM/src/vsp_llm.py" \
    "$GALAXY/VSP-LLM/src/vsp_llm.py"

echo
echo "--- lib/ modules (identical subset) ---"
for module in common.sh config.sh archive.sh normalization.sh manifests.sh \
              clustering.sh decode.sh outputs.sh test_all_modules.sh; do
    check_identical "lib/$module" \
        "$EC2/lib/$module" \
        "${FINAL}/lib/$module" \
        "$GALAXY/lib/$module"
done

echo

# -----------------------------------------------
# Category 2: Files with expected container-specific differences
# -----------------------------------------------
echo -e "${CYAN}=== Category 2: Expected Differences (container-specific paths) ===${NC}"
echo

check_expected_diff "run_flat_english_pipeline.sh" \
    "$EC2/run_flat_english_pipeline.sh" \
    "${FINAL}/run_flat_english_pipeline.sh" \
    "$GALAXY/run_flat_english_pipeline.sh" \
    "path strategy (HOME vs SCRIPT_DIR)"

check_expected_diff "lib/asr.sh" \
    "$EC2/lib/asr.sh" \
    "${FINAL}/lib/asr.sh" \
    "$GALAXY/lib/asr.sh" \
    "transcription path + whisper cache"

check_expected_diff "lib/lrs3_prep.sh" \
    "$EC2/lib/lrs3_prep.sh" \
    "${FINAL}/lib/lrs3_prep.sh" \
    "$GALAXY/lib/lrs3_prep.sh" \
    "PREP_VENV passthrough"

check_expected_diff "VSP-LLM/scripts/decode.sh" \
    "$EC2/VSP-LLM/scripts/decode.sh" \
    "${FINAL}/VSP-LLM/scripts/decode.sh" \
    "$GALAXY/VSP-LLM/scripts/decode.sh" \
    "fairseq auto-patch block"

echo

# -----------------------------------------------
# Category 3: UI files
# -----------------------------------------------
echo -e "${CYAN}=== Category 3: UI Files ===${NC}"
echo

echo "--- vsp-ui/ (primary UI) ---"
check_expected_diff "vsp-ui/app/server.py" \
    "$EC2/vsp-ui/app/server.py" \
    "${FINAL}/vsp-ui/app/server.py" \
    "$GALAXY/vsp-ui/app/server.py" \
    "BASE_DIR + path imports"

check_expected_diff "vsp-ui/app/static/app.js" \
    "$EC2/vsp-ui/app/static/app.js" \
    "${FINAL}/vsp-ui/app/static/app.js" \
    "$GALAXY/vsp-ui/app/static/app.js" \
    "UI feature delta"

check_expected_diff "vsp-ui/app/static/index.html" \
    "$EC2/vsp-ui/app/static/index.html" \
    "${FINAL}/vsp-ui/app/static/index.html" \
    "$GALAXY/vsp-ui/app/static/index.html" \
    "UI layout delta"

check_expected_diff "vsp-ui/app/static/style.css" \
    "$EC2/vsp-ui/app/static/style.css" \
    "${FINAL}/vsp-ui/app/static/style.css" \
    "$GALAXY/vsp-ui/app/static/style.css" \
    "UI style delta"

echo

# Check ui/ directory status (legacy ui/ should have been removed)
echo "--- ui/ directory check ---"
for location_name in "FINAL" "Galaxy"; do
    if [[ "$location_name" == "FINAL" && -n "$FINAL" ]]; then
        dir="$FINAL"
    elif [[ "$location_name" == "Galaxy" ]]; then
        dir="$GALAXY"
    else
        continue
    fi

    if [[ -d "$dir/ui" ]]; then
        echo -e "  ${RED}FAIL${NC} $location_name has legacy ui/ directory (should be removed)"
        ((FAIL++))
    elif [[ -d "$dir/vsp-ui" ]]; then
        echo -e "  ${GREEN}OK${NC}   $location_name has only vsp-ui/ (correct)"
        ((PASS++))
    else
        echo -e "  ${RED}FAIL${NC} $location_name missing vsp-ui/ directory"
        ((FAIL++))
    fi
done

echo
echo "--- Container-to-Container consistency ---"
# Check that FINAL and Galaxy containers match each other for shared files
if [[ -n "$FINAL" ]]; then
    # Files that MUST be identical between containers
    for f in run_flat_english_pipeline.sh; do
        ff="${FINAL}/$f"
        gf="$GALAXY/$f"
        if [[ -f "$ff" && -f "$gf" ]]; then
            if diff -q "$ff" "$gf" > /dev/null 2>&1; then
                echo -e "  ${GREEN}OK${NC}   FINAL↔Galaxy: $f"
            else
                echo -e "  ${RED}DIFF${NC} FINAL↔Galaxy: $f"
                FAIL=$((FAIL+1))
            fi
        fi
    done
    # Files with expected FINAL-specific features (whisper cache, PREP_VENV)
    for f in lib/asr.sh lib/lrs3_prep.sh; do
        ff="${FINAL}/$f"
        gf="$GALAXY/$f"
        if [[ -f "$ff" && -f "$gf" ]]; then
            if diff -q "$ff" "$gf" > /dev/null 2>&1; then
                echo -e "  ${GREEN}OK${NC}   FINAL↔Galaxy: $f (identical)"
            else
                fl=$(wc -l < "$ff"); gl=$(wc -l < "$gf")
                echo -e "  ${CYAN}DIFF${NC} FINAL↔Galaxy: $f (expected: FINAL has extras) [FINAL:${fl}L Galaxy:${gl}L]"
            fi
        fi
    done
fi

# -----------------------------------------------
# Summary
# -----------------------------------------------
echo
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo -e "  ${GREEN}PASS${NC}: $PASS"
echo -e "  ${RED}FAIL${NC}: $FAIL"
echo -e "  ${YELLOW}WARN${NC}: $WARN"
if $FIX_MODE; then
    echo -e "  ${GREEN}FIXED${NC}: $FIXED"
fi
echo

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}Some files are out of sync!${NC}"
    if ! $FIX_MODE; then
        echo "Run with --fix to auto-copy path-agnostic files."
    fi
    exit 1
else
    echo -e "${GREEN}All checked files are in expected state.${NC}"
    exit 0
fi
