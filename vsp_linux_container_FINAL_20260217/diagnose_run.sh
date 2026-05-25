#!/usr/bin/env bash
# ============================================================================
# diagnose_run.sh — Post-mortem state check for a VSP pipeline run.
# ============================================================================
#
# Run on the HOST (not inside a container). Picks the most recent run under
# ${GALAXY_EXPORT_DIR}/flat_runs_archive/ and tells you which features ran
# successfully, which were silently skipped, and which env vars / fixes to
# apply to restore the missing ones.
#
# Usage:
#   bash diagnose_run.sh                        # latest run, auto-detect dirs
#   bash diagnose_run.sh /path/to/run_dir       # specific run
#   GALAXY_EXPORT_DIR=/opt/vsp bash diagnose_run.sh
#
# No mutations, no docker required — just `ls`, `grep`, `head`, `python3 -c`.
# Exits 0 always; the report is the diagnostic.
# ============================================================================

set -u

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; DIM='\033[2m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
hint() { echo -e "    ${DIM}→${NC} $*"; }
header() { echo ""; echo -e "${BLUE}== $* ==${NC}"; }

# ----- locate galaxy_export -----
GALAXY_EXPORT_DIR="${GALAXY_EXPORT_DIR:-$HOME/Desktop/galaxy_export}"
if [ ! -d "$GALAXY_EXPORT_DIR" ]; then
    for cand in "$HOME/galaxy_export" "/home/ds/Desktop/galaxy_export" "/home/ds/galaxy_export" "$(pwd)/galaxy_export"; do
        [ -d "$cand" ] && GALAXY_EXPORT_DIR="$cand" && break
    done
fi
[ -d "$GALAXY_EXPORT_DIR" ] || { echo "ERROR: galaxy_export not found. Set GALAXY_EXPORT_DIR=…"; exit 0; }

header "Environment"
echo "  galaxy_export: $GALAXY_EXPORT_DIR"

# ----- locate run dir -----
RUN_DIR="${1:-}"
if [ -z "$RUN_DIR" ]; then
    RUN_DIR="$(ls -dt "$GALAXY_EXPORT_DIR/flat_runs_archive"/*/ 2>/dev/null | head -1)"
fi
if [ -z "$RUN_DIR" ] || [ ! -d "$RUN_DIR" ]; then
    fail "No run directory under $GALAXY_EXPORT_DIR/flat_runs_archive/"
    hint "Has any pipeline run completed yet? Try a real video first."
    exit 0
fi
RUN_DIR="${RUN_DIR%/}"
echo "  run dir      : $RUN_DIR"

POST_ROOT="$RUN_DIR/client_outputs"
REPORT_DIR="$POST_ROOT/report"
BURN_DIR="$POST_ROOT/burned_videos"
LIP_DIR="$POST_ROOT/lip_crops"
DECODE_DIR="$GALAXY_EXPORT_DIR/VSP-LLM/decode/vsr/en"

# ----- 1. decode artifacts -----
header "Decode artifacts ($DECODE_DIR)"
HYPO="$(ls -t "$DECODE_DIR"/hypo-*.json 2>/dev/null | grep -v merged | head -1)"
CONF="$(ls -t "$DECODE_DIR"/confidence-*.json 2>/dev/null | head -1)"
NBEST="$(ls -t "$DECODE_DIR"/nbest-*.json 2>/dev/null | head -1)"
AGG="$(ls -t "$DECODE_DIR"/aggregated-*.json 2>/dev/null | head -1)"
AGREE="$(ls -t "$DECODE_DIR"/agreement-*.json 2>/dev/null | head -1)"

[ -n "$HYPO"  ] && ok   "hypo-*.json present"          || fail "hypo-*.json MISSING — decode never finished"
[ -n "$CONF"  ] && ok   "confidence-*.json (per-token probs) present" \
                || warn "confidence-*.json MISSING (Mission 4 — per-token confidence)"
[ -n "$NBEST" ] && ok   "nbest-*.json (20-beam sidecar) present" \
                || warn "nbest-*.json MISSING (Mission 6 — n-best aggregation)"
[ -n "$AGG"   ] && ok   "aggregated-*.json (MBR + vote + safe) present" \
                || warn "aggregated-*.json MISSING (Mission 6 — MBR-default display)"
[ -n "$AGREE" ] && ok   "agreement-*.json (beam-agreement) present" \
                || warn "agreement-*.json MISSING (Mission 7 — joint band rule)"

[ -z "$CONF" ] && hint "Set VSP_OUTPUT_SCORES=1 in the env (default in lib/decode.sh; should be on)"
[ -z "$NBEST" ] && hint "Set VSP_NBEST=1 in the env (default in lib/decode.sh; should be on)"

# ----- 2. report -----
header "Report ($REPORT_DIR)"
if [ ! -d "$REPORT_DIR" ]; then
    fail "report/ directory missing — outputs.sh never ran or crashed"
else
    for f in report.html report.csv confidence_breakdown.html intelligibility_scores.csv aggregated.json word_confidence.json; do
        if [ -f "$REPORT_DIR/$f" ]; then
            ok "$f ($(du -h "$REPORT_DIR/$f" | cut -f1))"
        else
            warn "$f missing"
        fi
    done

    # CSV column inspection
    if [ -f "$REPORT_DIR/report.csv" ]; then
        HEADER="$(head -1 "$REPORT_DIR/report.csv")"
        for col in sentence_confidence is_score is_tier is_label niv; do
            if echo "$HEADER" | grep -q "$col"; then
                ok "report.csv has column: $col"
            else
                warn "report.csv missing column: $col"
            fi
        done
    fi
fi

# ----- 3. burned videos -----
header "Burned videos ($BURN_DIR)"
if [ -d "$BURN_DIR" ]; then
    N=$(ls "$BURN_DIR"/*.mp4 2>/dev/null | wc -l)
    if [ "$N" -gt 0 ]; then
        ok "$N burned video(s) found"
    else
        warn "burned_videos/ exists but is empty"
        hint "make_burn.py probably crashed — check pipeline log for 'make_burn.py failed'"
    fi
else
    warn "burned_videos/ does NOT exist"
    hint "VSP_FULL_OUTPUTS was 0 (default). Set VSP_FULL_OUTPUTS=1 to enable burned videos."
fi

# ----- 4. lip crops -----
header "Lip crops ($LIP_DIR)"
if [ -d "$LIP_DIR" ]; then
    N=$(ls "$LIP_DIR"/*.mp4 2>/dev/null | wc -l)
    [ "$N" -gt 0 ] && ok "$N lip-crop(s) found" \
                   || warn "lip_crops/ exists but is empty"
else
    warn "lip_crops/ does NOT exist"
    hint "VSP_FULL_OUTPUTS was 0 (default). Set VSP_FULL_OUTPUTS=1 to enable lip-crop copy."
fi

# ----- 5. IS / beam-analysis -----
header "IS + beam analysis"
if [ -f "$REPORT_DIR/intelligibility_scores.csv" ]; then
    ok "intelligibility_scores.csv ($(wc -l < "$REPORT_DIR/intelligibility_scores.csv") lines)"
else
    warn "intelligibility_scores.csv missing — IS scoring did not run or crashed"
    hint "Possible causes: sentence-transformers import failed, HF cache missing, or VSP_FULL_OUTPUTS=0 skipped it"
fi
if [ -d "$REPORT_DIR/beam_analysis" ]; then
    ok "beam_analysis/ ($(ls "$REPORT_DIR/beam_analysis" | wc -l) file(s))"
else
    warn "beam_analysis/ missing — analyze_beam_variance.py did not run"
    hint "Either VSP_BEAM_ANALYSIS=0 or matplotlib import failed inside the container"
fi

# ----- 6. dependency sanity (venv must be reachable) -----
header "Container venv import sanity (informational only)"
hint "Run this inside the container to confirm:"
echo "    docker run --rm vsp-llm-pipeline:may2026-update \\"
echo "      -c 'source /workspace/vsp-llm-yoad-venv/bin/activate && \\"
echo "          python3 -c \"import sentence_transformers, metaphone, matplotlib, scipy, editdistance; print(\\\"OK\\\")\"'"

# ----- 7. fairseq local-fork patches (do_sample / top_p) -----
header "Local fairseq fork patches (Bug 17 family)"
CFG="$GALAXY_EXPORT_DIR/VSP-LLM/fairseq/fairseq/dataclass/configs.py"
if [ -f "$CFG" ]; then
    for field in max_len repetition_penalty do_sample top_p; do
        if grep -q "^    $field:" "$CFG"; then
            ok "fairseq.GenerationConfig has $field"
        else
            fail "fairseq.GenerationConfig MISSING $field — decode would crash"
            hint "Re-run decode (decode.sh will auto-patch) or apply the in-place fix from UPDATE_GUIDE_MAY2026.md"
        fi
    done
else
    warn "Local fairseq configs.py not found at $CFG"
fi

# ----- 8. STALE-OVERLAY CHECK -----
# Quick scan of deployed files for markers from the May-2026 fixes. If any
# fail here, the operator is running outputs from an OLD overlay extract —
# need to re-pull the latest tarball and re-apply.
header "Deployed file freshness (Are we running the LATEST overlay?)"
STALE=0
chk() {
    local desc="$1" file="$2" pat="$3"
    if [ ! -f "$GALAXY_EXPORT_DIR/$file" ]; then
        fail "missing-file: $file"; STALE=$((STALE+1))
    elif grep -qE "$pat" "$GALAXY_EXPORT_DIR/$file" 2>/dev/null; then
        ok "$desc"
    else
        fail "STALE: $desc"
        hint "expected pattern: $pat"
        hint "in file:          $GALAXY_EXPORT_DIR/$file"
        STALE=$((STALE+1))
    fi
}

chk "lib/outputs.sh VSP_FULL_OUTPUTS=1 default" \
    "lib/outputs.sh" 'VSP_FULL_OUTPUTS:-1'
chk "lib/outputs.sh HF_HUB_OFFLINE wired" \
    "lib/outputs.sh" 'HF_HUB_OFFLINE'
chk "lib/outputs.sh calls nbest_aggregate" \
    "lib/outputs.sh" 'nbest_aggregate'
chk "decode.sh has Patched: do_sample" \
    "VSP-LLM/scripts/decode.sh" 'Patched: do_sample'
chk "decode.sh has Patched: top_p" \
    "VSP-LLM/scripts/decode.sh" 'Patched: top_p'
chk "app.js handleDrop uses isUploading-only gate" \
    "vsp-ui/app/static/app.js" 'if \(isUploading\) \{'
chk "index.html upload-progress at body level (.upload-progress-floating)" \
    "vsp-ui/app/static/index.html" 'upload-progress-floating'
chk "style.css has .upload-progress-floating rule" \
    "vsp-ui/app/static/style.css" '\.upload-progress-floating'
chk "vsp-start.sh passes -e HF_HUB_OFFLINE=1" \
    "vsp-start.sh" 'HF_HUB_OFFLINE=1'
chk "pipeline_runner.py has HF env setdefaults" \
    "vsp-ui/app/services/pipeline_runner.py" 'setdefault\("HF_HUB_OFFLINE"'
chk "make_burn.py uses tight subtitle box (no 320px dark patch)" \
    "VSP-LLM/scripts/make_burn.py" 'box_h = min\(int\(needed\), int\(h \* 0.45\)\)'

# spacy_wheels ABI check
if ls "$GALAXY_EXPORT_DIR"/spacy_wheels/spacy-*-cp310-*.whl >/dev/null 2>&1; then
    ok "spacy_wheels/: cp310 wheel present"
else
    fail "STALE: spacy_wheels/ has no cp310 spaCy wheel — entity metrics will degrade silently"
    hint "Old overlay shipped cp311 wheels. Re-pull latest overlay."
    STALE=$((STALE+1))
fi

if [ "$STALE" -gt 0 ]; then
    echo ""
    echo -e "${RED}  ⚠ DEPLOYED FILES ARE STALE — $STALE marker(s) missing${NC}"
    echo -e "${YELLOW}  → Re-pull the latest overlay tarball from S3 and re-apply:${NC}"
    echo -e "${YELLOW}      aws s3 cp s3://yoad-vsp-transfer/vsp/vsp_linux_container_FINAL_20260217.tar.gz . --region eu-west-1${NC}"
    echo -e "${YELLOW}      tar xzf vsp_linux_container_FINAL_20260217.tar.gz && cd vsp_linux_container_FINAL_20260217 && bash apply_update.sh${NC}"
fi

# ----- 8. summary -----
header "Summary"
N_OK=$(echo -e "$(grep -c ✓ /dev/null)" 2>/dev/null || true)
echo ""
echo "  Run dir   : $RUN_DIR"
echo "  Report    : $REPORT_DIR"
echo "  Burned    : $BURN_DIR  ($([ -d "$BURN_DIR" ] && ls "$BURN_DIR" 2>/dev/null | wc -l || echo 0) files)"
echo "  Lip crops : $LIP_DIR  ($([ -d "$LIP_DIR" ] && ls "$LIP_DIR" 2>/dev/null | wc -l || echo 0) files)"
echo ""
echo "  If anything above shows ⚠ or ✗ that you didn't expect:"
echo "  • For burned/lip crops missing: re-run pipeline with VSP_FULL_OUTPUTS=1"
echo "  • For confidence/nbest missing: VSP_OUTPUT_SCORES=1 + VSP_NBEST=1 (default since May 2 2026 — set explicitly if your env stripped them)"
echo "  • For fairseq field missing  : re-run decode.sh OR apply UPDATE_GUIDE_MAY2026.md § 'Fix on the client' patch"
echo "  • For everything missing     : pipeline never reached Stage 8 — check decode crash log"
echo ""
