#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — Post-install verification
# ==================================================
# Run on the client AFTER `docker load`. Confirms the image works
# end-to-end on the curated smoke samples and that all feature parity
# items (n-best aggregation, MBR display, IS scoring, agreement-aware
# bands, NIV labels) are present.
#
# Usage: ./post_install_check.sh [image_tag]
# Defaults to the tag in /opt/vsp/launcher/image.tag, or the first
# vsp-llm-pipeline image if that file is absent.
# ==================================================

set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${KIT_DIR}/post_install_check.log"
SAMPLES_DIR="${KIT_DIR}/../samples"
WORK_DIR="$(mktemp -d /tmp/vsp_post_install.XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

# --- Resolve image tag ---
IMG_TAG="${1:-}"
if [ -z "$IMG_TAG" ]; then
  for tag_file in /opt/vsp/launcher/image.tag "${KIT_DIR}/../launcher/image.tag"; do
    if [ -f "$tag_file" ]; then
      IMG_TAG="$(tr -d '[:space:]' < "$tag_file")"
      break
    fi
  done
fi
if [ -z "$IMG_TAG" ]; then
  IMG_TAG="$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^vsp-llm-pipeline:' | head -n1)"
fi
if [ -z "$IMG_TAG" ]; then
  echo "ERROR: Could not determine image tag. Pass it as the first argument."
  exit 1
fi

# --- Color helpers ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; NC=''
fi

PASSES=0; FAILS=0
pass() { echo -e "${GREEN}[PASS]${NC} $*" | tee -a "$LOG"; PASSES=$((PASSES+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $*" | tee -a "$LOG"; FAILS=$((FAILS+1)); }
info() { echo -e "       $*" | tee -a "$LOG"; }

: > "$LOG"
echo "=========================================" | tee -a "$LOG"
echo "VSP Pipeline — Post-install verification"   | tee -a "$LOG"
echo "Image: $IMG_TAG"                            | tee -a "$LOG"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"       | tee -a "$LOG"
echo "=========================================" | tee -a "$LOG"
echo                                              | tee -a "$LOG"

# --- 1. Image is loaded ---
echo "[1/8] Image is loaded" | tee -a "$LOG"
if docker image inspect "$IMG_TAG" >/dev/null 2>&1; then
  pass "Image $IMG_TAG present in local Docker"
else
  fail "Image $IMG_TAG not loaded. Run docker load -i vsp-image-*.tar first."
  exit 1
fi
echo | tee -a "$LOG"

# --- 2. In-container module tests (the build-time gate, re-run on host) ---
echo "[2/8] In-container module tests (lib/test_all_modules.sh)" | tee -a "$LOG"
if docker run --rm --entrypoint bash "$IMG_TAG" /workspace/lib/test_all_modules.sh >>"$LOG" 2>&1; then
  pass "All 37 module tests passed inside the container"
else
  fail "lib/test_all_modules.sh failed inside the container — see log."
fi
echo | tee -a "$LOG"

# --- 3. Sample fixture integrity ---
echo "[3/8] Sample fixture integrity" | tee -a "$LOG"
if [ -f "${SAMPLES_DIR}/checksums.txt" ]; then
  if (cd "$SAMPLES_DIR" && sha256sum -c checksums.txt) >>"$LOG" 2>&1; then
    pass "Curated samples match checksums.txt"
  else
    fail "Sample fixture SHA256 mismatch — samples have been swapped or corrupted."
  fi
else
  fail "samples/checksums.txt missing — sample fixtures unverified."
fi
echo | tee -a "$LOG"

# --- 4. Smoke decode (12 s sample) ---
SMOKE12="${SAMPLES_DIR}/smoke_12s.mp4"
SMOKE75="${SAMPLES_DIR}/smoke_75s.mp4"

run_smoke_decode() {
  local sample="$1"
  local sample_label="$2"
  local out_subdir="$3"

  if [ ! -f "$sample" ]; then
    fail "Smoke sample missing: $sample"
    return 1
  fi

  local input_dir="${WORK_DIR}/${out_subdir}_in"
  local output_dir="${WORK_DIR}/${out_subdir}_out"
  mkdir -p "$input_dir" "$output_dir"
  cp "$sample" "$input_dir/"

  echo ">>> Running smoke decode on ${sample_label}..." | tee -a "$LOG"
  local container_name="vsp_smoke_${out_subdir}"
  docker rm -f "$container_name" >/dev/null 2>&1 || true

  if docker run --rm --name "$container_name" --gpus all \
      -e VSP_OUTPUT_DIR=/data/out \
      -v "${input_dir}:/data/in:ro" \
      -v "${output_dir}:/data/out" \
      "$IMG_TAG" \
      /workspace/run_flat_english_pipeline.sh /data/in \
      >>"$LOG" 2>&1; then
    pass "Smoke decode (${sample_label}) completed without error"
    # Result via global, NOT command substitution: $(...) would run this
    # function in a subshell, losing the pass/fail counters and capturing
    # the tee'd progress lines into the "output dir" variable (the exact
    # failure seen on the first build-004 validation run, Aug 6 2026).
    RUN_SMOKE_OUT="$output_dir"
    return 0
  else
    fail "Smoke decode (${sample_label}) failed — see log."
    return 1
  fi
}

echo "[4/8] Smoke decode — 12s sample" | tee -a "$LOG"
RUN_SMOKE_OUT=""
run_smoke_decode "$SMOKE12" "12-second" "smoke12" || true
SMOKE12_OUT="$RUN_SMOKE_OUT"
echo | tee -a "$LOG"

# --- 5. Smoke decode (75 s sample, exercises NBEST/MBR/aggregation paths) ---
echo "[5/8] Smoke decode — 75s sample (exercises full pipeline + n-best)" | tee -a "$LOG"
RUN_SMOKE_OUT=""
run_smoke_decode "$SMOKE75" "75-second" "smoke75" || true
SMOKE75_OUT="$RUN_SMOKE_OUT"
echo | tee -a "$LOG"

# --- 6. Mechanism checks on the 75s decode output ---
echo "[6/8] Feature-parity mechanism checks (on 75s output)" | tee -a "$LOG"

if [ -z "$SMOKE75_OUT" ] || [ ! -d "$SMOKE75_OUT" ]; then
  fail "75s output dir missing — skipping mechanism checks."
else
  OUT="$SMOKE75_OUT"

  # 6.1: aggregated.json with all 5 hypothesis methods
  if [ -s "${OUT}/aggregated.json" ]; then
    if docker run --rm -v "${OUT}:/out:ro" --entrypoint python3 "$IMG_TAG" \
        -c "
import json, sys
d = json.load(open('/out/aggregated.json'))
keys = set()
for v in d.values() if isinstance(d, dict) else []:
    if isinstance(v, dict): keys |= set(v.keys())
required = {'hyp_mbr','hyp_vote_score','hyp_vote_conf','hyp_safe','hyp_xseg_merge'}
missing = required - keys
sys.exit(1 if missing else 0)
" >>"$LOG" 2>&1; then
      pass "n-best aggregation: all 5 hypothesis methods present in aggregated.json"
    else
      fail "n-best aggregation: aggregated.json is missing one or more required hyp_* keys"
    fi
  else
    fail "aggregated.json not produced — VSP_NBEST=1 default may be broken"
  fi

  # 6.2: report.csv has the required columns
  if [ -s "${OUT}/report.csv" ]; then
    HEADER=$(head -1 "${OUT}/report.csv")
    NEEDED=("sentence_confidence" "hyp_mbr")
    NIV_OK=0
    [[ "$HEADER" =~ NIV|niv ]] && NIV_OK=1
    MISSING=()
    for col in "${NEEDED[@]}"; do
      if ! [[ "$HEADER" =~ $col ]]; then MISSING+=("$col"); fi
    done
    if [ "${#MISSING[@]}" -eq 0 ] && [ "$NIV_OK" -eq 1 ]; then
      pass "report.csv has sentence_confidence + hyp_mbr + NIV columns"
    else
      fail "report.csv missing columns: ${MISSING[*]} (NIV present: $NIV_OK)"
    fi
  else
    fail "report.csv not produced"
  fi

  # 6.3: tier classification fired (Trust/Salvage/Strip somewhere in CSV)
  if [ -s "${OUT}/report.csv" ] && grep -qE 'Trust|Salvage|Strip' "${OUT}/report.csv"; then
    pass "Reliability-tier classification (Trust/Salvage/Strip) fired"
  else
    fail "No tier markers found in report.csv"
  fi

  # 6.4: IS scoring
  if [ -s "${OUT}/intelligibility_scores.csv" ]; then
    pass "IS scoring produced intelligibility_scores.csv"
  else
    fail "intelligibility_scores.csv not produced — sentence-transformers/metaphone may be broken"
  fi

  # 6.5: k-means model exported
  if ls "${OUT}"/*_kmeans_200.bin >/dev/null 2>&1; then
    pass "k-means model exported (proves training+save path works)"
  else
    fail "No *_kmeans_200.bin in output — clustering stage broken or export hook missed it"
  fi

  # 6.6: confidence palette in report.html (newest palette: blue/orange/purple/teal)
  if [ -s "${OUT}/report.html" ]; then
    HTML="${OUT}/report.html"
    # Old palette hex codes must NOT appear (#00ff00, #008000, #ff0000, #800000, #ffff00).
    if grep -qiE '#(00ff00|008000|ff0000|800000|ffff00)' "$HTML"; then
      fail "report.html contains old-palette hex codes — wrong make_report.py copy"
    else
      pass "report.html has no old-palette hex codes"
    fi
    # New palette: legend should mention the four color words. The exact element
    # selector should be pinned in samples/README.md after first Layer-2 inspection.
    PALETTE_OK=1
    for word in blue orange purple teal; do
      if ! grep -qi "$word" "$HTML"; then PALETTE_OK=0; fi
    done
    if [ "$PALETTE_OK" -eq 1 ]; then
      pass "report.html legend contains all 4 expected color words (blue/orange/purple/teal)"
    else
      fail "report.html legend missing one or more new-palette color words"
    fi
  else
    fail "report.html not produced"
  fi

  # 6.7: burned video exists, has duration > 1s
  BURN=$(ls "${OUT}"/burned_videos/*_burned.mp4 2>/dev/null | head -n1)
  if [ -n "$BURN" ] && [ -f "$BURN" ]; then
    DUR=$(docker run --rm -v "${OUT}:/out:ro" --entrypoint ffprobe "$IMG_TAG" \
      -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
      "/out/burned_videos/$(basename "$BURN")" 2>/dev/null | head -n1)
    if [ -n "$DUR" ] && awk -v d="$DUR" 'BEGIN { exit (d < 1) ? 1 : 0 }'; then
      pass "Burned video has duration ${DUR}s"
    else
      fail "Burned video has zero or invalid duration"
    fi
  else
    fail "No *_burned.mp4 in output (NB: full burns require VSP_FULL_OUTPUTS=1; the smoke decode may not produce them)"
  fi

  # 6.8: VSP_NBEST=1 fired (logs)
  if grep -qE 'VSP_NBEST=1|n-best|N-best' "${OUT}"/*.log 2>/dev/null; then
    pass "VSP_NBEST=1 default fired (n-best decode in logs)"
  else
    fail "No n-best evidence in logs — VSP_NBEST default may be 0"
  fi
fi
echo | tee -a "$LOG"

# --- 6.9: offline imports — every runtime dep must import with networking
# disabled (air-gapped parity; runs regardless of decode output) ---
if docker run --rm --network=none \
    --entrypoint /workspace/vsp-llm-yoad-venv/bin/python "$IMG_TAG" \
    -c "import sys; sys.path.insert(0, '/workspace/lib'); import torch, fairseq, spacy, matplotlib, sentence_transformers, metaphone, nbest_aggregate; spacy.load('en_core_web_sm')" \
    >>"$LOG" 2>&1; then
  pass "Offline imports OK with --network=none (torch/fairseq/spacy+en_core_web_sm/matplotlib/sentence-transformers/metaphone/nbest_aggregate)"
else
  fail "Offline import failed with networking disabled — a runtime dep is missing or reaches for the network"
fi
echo | tee -a "$LOG"

# --- 7. Decode timing sanity (75s sample should finish in <10 min on a healthy GPU) ---
echo "[7/8] Decode timing" | tee -a "$LOG"
info "Manual review: confirm 75s smoke completed in under ~10 min."
info "If it took >20 min, GPU compute_cap may be too low for shipped wheels."
echo | tee -a "$LOG"

# --- 8. Summary ---
echo "[8/8] Summary" | tee -a "$LOG"
echo "  PASS: $PASSES" | tee -a "$LOG"
echo "  FAIL: $FAILS"  | tee -a "$LOG"
echo                   | tee -a "$LOG"

# Write a one-page install report
INSTALL_REPORT="${KIT_DIR}/INSTALL_REPORT.txt"
{
  echo "VSP Pipeline — Install Report"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Image: $IMG_TAG"
  echo "Host: $(hostname)"
  echo
  echo "PASSES: $PASSES"
  echo "FAILS:  $FAILS"
  echo
  if [ "$FAILS" -eq 0 ]; then
    echo "STATUS: READY"
    echo "All checks passed. The pipeline is ready to use."
    echo "Launch via the desktop shortcut (VSP Pipeline)."
  else
    echo "STATUS: FAILED"
    echo "$FAILS check(s) failed. Run collect_diagnostics.sh and contact support."
  fi
} > "$INSTALL_REPORT"

if [ "$FAILS" -gt 0 ]; then
  echo -e "${RED}Post-install check FAILED. See $LOG and $INSTALL_REPORT.${NC}"
  echo "If you need help, run ./collect_diagnostics.sh and send the resulting tarball."
  exit 1
else
  echo -e "${GREEN}Post-install check passed. Image is ready.${NC}"
  echo "Report: $INSTALL_REPORT"
  exit 0
fi
