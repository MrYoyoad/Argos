#!/usr/bin/env bash
# ==================================================
# EC2 End-to-End Smoke Decode Test
# ==================================================
# Runs the FULL pipeline (run_flat_english_pipeline.sh) on the bundled 12s
# smoke sample and asserts that a segment report with at least one non-empty
# hypothesis comes out the other end. Takes ~5-10 minutes on a T4.
#
# Companion doc: docs/guides/ec2-setup-from-scratch.md (§7 validation ladder)
#
# !!! THIS TEST MUTATES PIPELINE STATE !!!
# The pipeline's first act is to ARCHIVE the previous run's working outputs
# (auto_avsr/flat_wrd, flat_txt, preprocess_ready_flat, VSP-LLM/flat_features,
# flat_labels, preprocessed_flat_seg*) into ~/flat_runs_archive/<timestamp>/.
# Nothing is deleted — but the current working dirs are MOVED. This script
# backs up NOTHING itself. You must opt in explicitly:
#
#     ALLOW_PIPELINE_RUN=1 bash scripts/tests/test_ec2_smoke_decode.sh
#
# The input videos are NOT taken from ~/vsp_input: run_flat_english_pipeline.sh
# takes the raw-video directory as its single argument, so this test feeds it a
# temporary isolated directory containing only the smoke sample.

set -euo pipefail

HOME_DIR="${HOME:-/home/ubuntu}"
PIPELINE="$HOME_DIR/run_flat_english_pipeline.sh"
SAMPLE="$HOME_DIR/vsp_docker/container_payload_20260507/samples/smoke_12s.mp4"
ARCHIVE_BASE="$HOME_DIR/flat_runs_archive"
LOG_DIR="$HOME_DIR/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }

echo "=================================================="
echo "EC2 Smoke Decode Test (end-to-end pipeline)"
echo "=================================================="
echo ""
echo -e "${YELLOW}WARNING:${NC} this run will ARCHIVE the current pipeline working outputs"
echo "         into $ARCHIVE_BASE/<timestamp>/ (moved, not deleted)."
echo "         This script backs up nothing itself."
echo ""

if [ "${ALLOW_PIPELINE_RUN:-0}" != "1" ]; then
    echo -e "${RED}Refusing to run:${NC} set ALLOW_PIPELINE_RUN=1 to acknowledge the archive side-effect."
    echo "    ALLOW_PIPELINE_RUN=1 bash $0"
    exit 2
fi

# ---------- Preconditions ----------
if [ ! -f "$PIPELINE" ]; then
    fail "Pipeline script missing: $PIPELINE"
    exit 1
fi
if [ ! -f "$SAMPLE" ]; then
    fail "Smoke sample missing: $SAMPLE"
    exit 1
fi

# ---------- Isolated temporary input ----------
SMOKE_INPUT="$(mktemp -d "${TMPDIR:-/tmp}/vsp_smoke_input.XXXXXX")"
cleanup() { rm -rf "$SMOKE_INPUT"; }
trap cleanup EXIT

cp "$SAMPLE" "$SMOKE_INPUT/"
echo "Temporary input dir: $SMOKE_INPUT ($(ls "$SMOKE_INPUT"))"

mkdir -p "$LOG_DIR"
RUN_STAMP="$(date +'%Y%m%d_%H%M%S')"
LOG_FILE="$LOG_DIR/smoke_decode_${RUN_STAMP}.log"
START_EPOCH="$(date +%s)"

# ---------- Run the pipeline ----------
echo ""
echo ">>> Running: bash $PIPELINE $SMOKE_INPUT"
echo ">>> Full log: $LOG_FILE"
echo ""

set +e
bash "$PIPELINE" "$SMOKE_INPUT" 2>&1 | tee "$LOG_FILE"
PIPE_STATUS=${PIPESTATUS[0]}
set -e

if [ "$PIPE_STATUS" -ne 0 ]; then
    fail "Pipeline exited non-zero ($PIPE_STATUS) — see $LOG_FILE"
    exit 1
fi
pass "Pipeline completed (exit 0)"

# ---------- Locate this run's report ----------
# Stage 8 (lib/outputs.sh) writes client outputs into the SAME archive dir the
# run created at startup: ~/flat_runs_archive/<run_id>/client_outputs/report/report.csv.
# Pick the newest archive dir created at/after our start time.
REPORT_CSV=""
for d in $(ls -td "$ARCHIVE_BASE"/*/ 2>/dev/null); do
    DIR_EPOCH="$(stat -c %Y "$d" 2>/dev/null || echo 0)"
    # stat mtime of the dir updates as outputs land; use birth-by-name fallback:
    if [ -f "$d/client_outputs/report/report.csv" ] && [ "$DIR_EPOCH" -ge "$START_EPOCH" ]; then
        REPORT_CSV="$d/client_outputs/report/report.csv"
        break
    fi
done

if [ -z "$REPORT_CSV" ]; then
    fail "No client_outputs/report/report.csv found under $ARCHIVE_BASE for a run newer than start time"
    exit 1
fi
pass "Report CSV found: $REPORT_CSV"

# ---------- Assert >=1 row with non-empty hypothesis ----------
# report.csv header (make_report.py): utt_id, display_name, ref, hyp, hyp_tagged, ...
set +e
python3 - "$REPORT_CSV" <<'PYEOF'
import csv, sys

path = sys.argv[1]
with open(path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

if not rows:
    print("FAIL: report.csv has no data rows")
    sys.exit(1)

hyp_col = "hyp" if "hyp" in rows[0] else None
if hyp_col is None:
    print(f"FAIL: no 'hyp' column in report.csv (columns: {list(rows[0].keys())})")
    sys.exit(1)

non_empty = [r for r in rows if (r.get(hyp_col) or "").strip()]
if not non_empty:
    print(f"FAIL: {len(rows)} row(s) but every hypothesis is empty")
    sys.exit(1)

print(f"OK: {len(rows)} segment row(s), {len(non_empty)} with non-empty hypothesis")
print(f"First hypothesis: {non_empty[0][hyp_col].strip()!r}")
PYEOF
CSV_STATUS=$?
set -e

if [ "$CSV_STATUS" -ne 0 ]; then
    fail "Report CSV assertion failed"
    exit 1
fi
pass "Report CSV has >=1 row with non-empty hypothesis"

echo ""
echo "=================================================="
echo -e "${GREEN}SMOKE DECODE TEST PASSED${NC}"
echo "Report: $REPORT_CSV"
echo "Log:    $LOG_FILE"
echo "=================================================="
exit 0
