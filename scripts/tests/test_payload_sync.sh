#!/usr/bin/env bash
# test_payload_sync.sh — EC2 source-of-truth vs Docker build payload sync check
#
# Compares /home/ubuntu (EC2, source of truth) against
# vsp_docker/container_payload_20260507/ (the Docker build context) and fails
# if any deploy-critical file differs or is missing. Run this BEFORE every
# `docker build` (see docs/guides/client-laptop-deployment-aug2026.md §4).
#
# What it checks:
#   (a) run_flat_english_pipeline.sh
#   (b) every lib/*.sh + lib/nbest_aggregate.py
#   (c) vsp-ui/app/ recursively (*.py, *.js, *.html, *.css)
#   (d) sample fixtures: checksums.txt verification in BOTH sample dirs
#       (vsp_docker/samples/ = kit-side copy, container_payload_20260507/samples/
#       = in-image copy) + detection of the historical smoke_35s_360p.mp4 vs
#       smoke_75s.mp4 naming mismatch
#   (e) container-adaptation markers in the payload — guards against a naive
#       wholesale rsync clobbering the container-specific patches
#       (grep probes from docs/guides/container-deployment-lessons-may2026.md)
#
# Files in EXPECTED_DIFF are container adaptations (path translation, env
# detection) that differ from EC2 BY DESIGN. They are reported as
# DIFF-EXPECTED (warning, never failure) — but their adaptation markers are
# verified in (e), and any EC2-side feature change to these files must be
# hand-merged (a plain copy would strip the container patches; a skipped
# merge strips the new feature).
#
# Exit: 0 if no failures, 1 otherwise.
# Env:
#   SYNC_ALLOW_DIFF=1   downgrade all failures to warnings (mid-development)
#   EC2_ROOT, PAYLOAD   override the two roots (defaults below)

set -euo pipefail

EC2_ROOT="${EC2_ROOT:-/home/ubuntu}"
PAYLOAD="${PAYLOAD:-${EC2_ROOT}/vsp_docker/container_payload_20260507}"
KIT_SAMPLES="${KIT_SAMPLES:-${EC2_ROOT}/vsp_docker/samples}"
SYNC_ALLOW_DIFF="${SYNC_ALLOW_DIFF:-0}"

PASS_N=0; WARN_N=0; FAIL_N=0
FAIL_LIST=(); WARN_LIST=()

pass() { PASS_N=$((PASS_N+1)); echo "  PASS  $*"; }
warn() { WARN_N=$((WARN_N+1)); WARN_LIST+=("$*"); echo "  WARN  $*"; }
fail() {
  if [ "$SYNC_ALLOW_DIFF" = "1" ]; then
    warn "$* [downgraded: SYNC_ALLOW_DIFF=1]"
  else
    FAIL_N=$((FAIL_N+1)); FAIL_LIST+=("$*"); echo "  FAIL  $*"
  fi
}
hdr() { echo; echo "== $* =="; }

# Container adaptations — differ from EC2 by design (path translation,
# env detection, RAW_DIR transcriptions). See lessons doc for each.
EXPECTED_DIFF=(
  "run_flat_english_pipeline.sh"
  "lib/asr.sh"
  "lib/lrs3_prep.sh"
  "lib/test_all_modules.sh"
  "vsp-ui/app/config.py"
  "vsp-ui/app/services/transcription_manager.py"
)

is_expected_diff() {
  local f="$1" e
  for e in "${EXPECTED_DIFF[@]}"; do [ "$f" = "$e" ] && return 0; done
  return 1
}

# compare_file <relative-path>
compare_file() {
  local rel="$1"
  local src="${EC2_ROOT}/${rel}" dst="${PAYLOAD}/${rel}"
  if [ ! -f "$src" ]; then
    warn "$rel: missing on EC2 side (payload-only file?) — check manually"
    return
  fi
  if [ ! -f "$dst" ]; then
    fail "$rel: MISSING in payload"
    return
  fi
  if cmp -s "$src" "$dst"; then
    pass "$rel: identical"
  elif is_expected_diff "$rel"; then
    local n
    n=$( (diff "$src" "$dst" || true) | wc -l)
    warn "$rel: DIFF-EXPECTED (container adaptation, ${n} diff lines) — if EC2 side changed since last release, hand-merge required"
  else
    fail "$rel: DIFFERS from EC2 (payload is stale or EC2 drifted — resync before build)"
  fi
}

echo "test_payload_sync: EC2=${EC2_ROOT}  PAYLOAD=${PAYLOAD}"
[ -d "$PAYLOAD" ] || { echo "FATAL: payload dir not found: $PAYLOAD"; exit 1; }

# ---------------------------------------------------------------- (a) ----
hdr "(a) Master pipeline script"
compare_file "run_flat_english_pipeline.sh"

# ---------------------------------------------------------------- (b) ----
hdr "(b) lib/ modules"
while IFS= read -r f; do
  compare_file "lib/$(basename "$f")"
done < <(find "${EC2_ROOT}/lib" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) | sort)
# Payload-only lib files (should not exist — everything comes from EC2)
while IFS= read -r f; do
  b=$(basename "$f")
  [ -f "${EC2_ROOT}/lib/${b}" ] || warn "lib/${b}: exists only in payload (orphan — was it removed on EC2?)"
done < <(find "${PAYLOAD}/lib" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) | sort)

# ---------------------------------------------------------------- (c) ----
hdr "(c) vsp-ui/app/ (py/js/html/css, recursive)"
while IFS= read -r f; do
  rel="vsp-ui/app/${f#"${EC2_ROOT}"/vsp-ui/app/}"
  compare_file "$rel"
done < <(find "${EC2_ROOT}/vsp-ui/app" -type f \( -name '*.py' -o -name '*.js' -o -name '*.html' -o -name '*.css' \) ! -path '*/__pycache__/*' | sort)
# Payload-only UI files
while IFS= read -r f; do
  rel="${f#"${PAYLOAD}"/vsp-ui/app/}"
  [ -f "${EC2_ROOT}/vsp-ui/app/${rel}" ] || warn "vsp-ui/app/${rel}: exists only in payload (orphan)"
done < <(find "${PAYLOAD}/vsp-ui/app" -type f \( -name '*.py' -o -name '*.js' -o -name '*.html' -o -name '*.css' \) ! -path '*/__pycache__/*' 2>/dev/null | sort)

# ---------------------------------------------------------------- (d) ----
hdr "(d) Sample fixtures (smoke videos + checksums)"
check_samples_dir() {
  local dir="$1" label="$2"
  if [ ! -d "$dir" ]; then
    fail "${label}: directory missing (${dir})"
    return
  fi
  # Historical naming mismatch: the file content named smoke_75s.mp4 in the
  # payload/checksums was named smoke_35s_360p.mp4 in the kit-side copy,
  # breaking `sha256sum -c checksums.txt` and post_install_check.sh step 3.
  if [ -f "${dir}/smoke_35s_360p.mp4" ] && [ ! -f "${dir}/smoke_75s.mp4" ]; then
    fail "${label}: KNOWN NAMING MISMATCH — has smoke_35s_360p.mp4 but checks/checksums expect smoke_75s.mp4. Fix: mv '${dir}/smoke_35s_360p.mp4' '${dir}/smoke_75s.mp4'"
  fi
  if [ -f "${dir}/checksums.txt" ]; then
    if (cd "$dir" && sha256sum -c checksums.txt >/dev/null 2>&1); then
      pass "${label}: checksums.txt verifies (fixtures intact)"
    else
      fail "${label}: checksums.txt does NOT verify (fixture rot, rename, or missing file)"
    fi
  else
    fail "${label}: checksums.txt missing"
  fi
}
check_samples_dir "${PAYLOAD}/samples" "payload samples (in-image copy)"
check_samples_dir "${KIT_SAMPLES}"     "kit samples (vsp_docker/samples, USB copy)"
# The two copies must be content-identical (same fixtures in image and on USB)
for s in smoke_12s.mp4 smoke_75s.mp4; do
  if [ -f "${PAYLOAD}/samples/$s" ] && [ -f "${KIT_SAMPLES}/$s" ]; then
    cmp -s "${PAYLOAD}/samples/$s" "${KIT_SAMPLES}/$s" \
      && pass "samples/$s: kit copy == payload copy" \
      || fail "samples/$s: kit copy != payload copy"
  fi
done

# ---------------------------------------------------------------- (e) ----
hdr "(e) Container-adaptation markers in payload (anti-clobber probes)"
probe() {
  local desc="$1" file="$2" pattern="$3" min="${4:-1}"
  if [ ! -f "$file" ]; then fail "probe '${desc}': file missing (${file})"; return; fi
  local n
  n=$(grep -c -- "$pattern" "$file" || true)
  if [ "$n" -ge "$min" ]; then
    pass "probe: ${desc} (${n} hits)"
  else
    fail "probe: ${desc} — expected >=${min} hits of '${pattern}' in ${file#"${EC2_ROOT}"/}, got ${n}. A wholesale copy likely clobbered the container patch."
  fi
}
probe "run_flat uses SCRIPT_DIR auto-detect (no \$HOME paths)" \
      "${PAYLOAD}/run_flat_english_pipeline.sh" 'SCRIPT_DIR' 2
probe "asr.sh writes transcriptions under RAW_DIR (ro-mount-safe wiring)" \
      "${PAYLOAD}/lib/asr.sh" 'raw_dir' 2
probe "lrs3_prep.sh passes VENV=PREP_VENV to flat_to_lrs3 (Bug 2)" \
      "${PAYLOAD}/lib/lrs3_prep.sh" 'PREP_VENV' 1
probe "test_all_modules.sh auto-detects LIB_DIR" \
      "${PAYLOAD}/lib/test_all_modules.sh" 'BASH_SOURCE' 1
probe "vsp-ui config.py has _detect_environment (container layouts)" \
      "${PAYLOAD}/vsp-ui/app/config.py" '_detect_environment' 2
probe "outputs.sh finds nbest_aggregate via BASH_SOURCE fallback (Bug 4)" \
      "${PAYLOAD}/lib/outputs.sh" 'BASH_SOURCE' 1
probe "decode.sh fairseq monkey-patches all present (Bugs 3+17, need 4 patches)" \
      "${PAYLOAD}/VSP-LLM/scripts/decode.sh" 'Patched: \|Patch [0-9]' 8
if [ -f "${PAYLOAD}/whisper_cache/medium.pt" ]; then
  pass "probe: whisper_cache/medium.pt at top level (no nested whisper/ subdir, Bug 7)"
else
  fail "probe: whisper_cache/medium.pt not at payload top level — Whisper will re-download at runtime (fatal air-gapped, Bug 7)"
fi

# ------------------------------------------------------------- summary ----
echo
echo "=================================================================="
echo "SUMMARY: ${PASS_N} pass, ${WARN_N} warn, ${FAIL_N} fail"
if [ "${#WARN_LIST[@]}" -gt 0 ]; then
  echo "Warnings (review, not blocking):"
  for w in "${WARN_LIST[@]}"; do echo "  - $w"; done
fi
if [ "$FAIL_N" -gt 0 ]; then
  echo "FAILURES (deploy-blocking — resync payload before docker build):"
  for f in "${FAIL_LIST[@]}"; do echo "  - $f"; done
  echo "RESULT: FAIL"
  exit 1
fi
echo "RESULT: PASS"
