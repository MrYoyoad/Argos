#!/usr/bin/env bash
# ==================================================
# Client Outputs Module
# ==================================================
# Generates client-facing outputs (reports and burned videos)
# Assumes VSP_VENV is already activated by caller
# Works on EC2 and Linux container

# Source common utilities for logging
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${MODULE_DIR}/common.sh"

# Generate client outputs (reports and burned videos)
# Parameters:
#   $1 - VSP directory
#   $2 - ARCHIVE_ROOT path
#   $3 - FLAT_VID_DIR path
#   $4 - PREP_ROOT path
#   $5 - DATA_NAME (e.g., "flat")
#   $6 - DIR_SUFFIX (e.g., "seg12s" or "whole")
#
# Note: Assumes VSP_VENV is already activated by caller
run_client_outputs() {
  local vsp_dir="$1"
  local archive_root="$2"
  local flat_vid_dir="$3"
  local prep_root="$4"
  local data_name="$5"
  local dir_suffix="$6"

  log_stage "8" "Building client outputs"

  local post_root="${archive_root}/client_outputs"
  local report_dir="${post_root}/report"
  local burn_dir="${post_root}/burned_videos"

  mkdir -p "$report_dir" "$burn_dir"

  # Find decode output (check both nested and flat paths)
  local decode_json
  decode_json="$(ls -t ${vsp_dir}/decode/vsr/en/vsr/en/hypo-*.json ${vsp_dir}/decode/vsr/en/hypo-*.json 2>/dev/null | grep -v "merged" | head -n 1)"

  if [ -z "$decode_json" ] || [ ! -f "$decode_json" ]; then
    log_error "Decode JSON not found in ${vsp_dir}/decode/vsr/en/"
    return 1
  fi

  # Use video directory for burning (dynamic based on segmentation mode)
  local segment_vid_dir="${prep_root}/${data_name}/${data_name}_video_${dir_suffix}"
  local segment_metadata="${prep_root}/segment_metadata.json"

  echo ">>> [8] Generating segment-level reports and burned videos"

  # Auto-install spaCy for full NEA/WWER metrics (falls back gracefully if offline)
  if ! python3 -c "import spacy" 2>/dev/null; then
    echo ">>> [8] Installing spaCy for entity metrics (one-time)..."
    # Try local wheels first (offline/standalone)
    local wheels_dir="${MODULE_DIR}/../spacy_wheels"
    if [ -d "$wheels_dir" ] && ls "$wheels_dir"/spacy-*.whl &>/dev/null; then
      pip install --no-index --find-links="$wheels_dir" spacy 2>/dev/null \
        && pip install --no-index --find-links="$wheels_dir" en_core_web_sm 2>/dev/null \
        && echo ">>> [8] spaCy installed from local wheels" \
        || echo ">>> [8] Local wheel install failed — trying online..."
    fi
    # Fallback to online install if local failed
    if ! python3 -c "import spacy" 2>/dev/null; then
      pip install spacy 2>/dev/null && python3 -m spacy download en_core_web_sm 2>/dev/null \
        && echo ">>> [8] spaCy installed successfully" \
        || echo ">>> [8] spaCy install skipped (offline?) — using fallback metrics"
    fi
  fi

  # Find matching decode params file (if decode wrote one)
  local params_json="${decode_json/hypo-/decode_params-}"
  local params_arg=""
  if [ -f "$params_json" ]; then
    params_arg="--params $params_json"
    echo ">>> [8] Found decode params: $params_json"
  fi

  # Auto-install IS dependencies if missing (like spaCy above)
  if ! python3 -c "import metaphone" 2>/dev/null; then
    echo ">>> [8] Installing metaphone for IS scoring (one-time)..."
    local is_wheels_dir="${MODULE_DIR}/../is_wheels"
    if [ -d "$is_wheels_dir" ] && ls "$is_wheels_dir"/metaphone-*.whl &>/dev/null; then
      pip install --no-index --find-links="$is_wheels_dir" metaphone 2>/dev/null \
        && echo ">>> [8] metaphone installed from local wheels" \
        || pip install metaphone 2>/dev/null
    else
      pip install metaphone 2>/dev/null \
        || echo ">>> [8] metaphone install failed — IS scoring may be limited"
    fi
  fi

  # Compute Intelligibility Scores in reports
  echo ">>> [8] Intelligibility Scores enabled"

  # Generate report (always with IS scoring)
  python3 "$vsp_dir/scripts/make_report.py" \
    --jsonl "$decode_json" \
    --out_dir "$report_dir" \
    $params_arg --compute-is || {
    log_error "make_report.py failed"
    return 1
  }

  # Generate full Intelligibility analysis (augmented CSV + summary JSON)
  local is_script="$vsp_dir/scripts/generate_intelligibility_scores.py"
  # Fallback: check docs path (EC2 development layout)
  if [ ! -f "$is_script" ]; then
    is_script="${HOME}/docs/_research-tools/generators/generate_intelligibility_scores.py"
  fi
  if [ -f "$is_script" ] && [ -f "$report_dir/report.csv" ]; then
    echo ">>> [8] Computing full Intelligibility analysis (IS + LLM context recovery)..."
    python3 "$is_script" \
      --csv "$report_dir/report.csv" \
      --out_dir "$report_dir" \
      --device cpu || {
      log_warn "Full Intelligibility analysis failed (non-critical) — basic report still available"
    }
  fi

  # Generate burned videos
  python3 "$vsp_dir/scripts/make_burn.py" \
    --jsonl "$decode_json" \
    --video_dir "$flat_vid_dir" \
    --segment_dir "$segment_vid_dir" \
    --segment_metadata "$segment_metadata" \
    --out_dir "$burn_dir" || {
    log_error "make_burn.py failed"
    return 1
  }

  # Copy lip crops to client output (non-critical — warn on failure, don't abort)
  local lip_dir="${post_root}/lip_crops"
  mkdir -p "$lip_dir"
  echo ">>> [8] Copying lip crop videos to client outputs"
  python3 -c "
import json, sys
from pathlib import Path

decode_json = Path('$decode_json')
segment_vid_dir = Path('$segment_vid_dir')
lip_dir = Path('$lip_dir')

# Load decode output to get processed segment IDs
try:
    data = json.loads(decode_json.read_text())
except Exception as e:
    print(f'[WARN] Cannot read decode JSON for lip crops: {e}')
    sys.exit(0)

utt_ids = data.get('utt_id', [])
if not utt_ids:
    print('[WARN] No utt_ids in decode JSON for lip crops')
    sys.exit(0)

# Parse segment IDs and build display names (same logic as make_report.py)
def parse_segment_id(sid):
    parts = sid.split('_')
    if len(parts) < 4:
        return sid, -1
    try:
        int(parts[-1]); int(parts[-2]); int(parts[-3])
        return '_'.join(parts[:-3]), int(parts[-3])
    except (ValueError, IndexError):
        return sid, -1

groups = {}
for uid in utt_ids:
    base, idx = parse_segment_id(uid)
    groups.setdefault(base, []).append((idx, uid))

copied = 0
for base, entries in groups.items():
    entries.sort()
    is_multi = len(entries) > 1
    for part_num, (_, uid) in enumerate(entries, 1):
        src = segment_vid_dir / f'{uid}.mp4'
        if not src.exists():
            continue
        if is_multi:
            dst_name = f'{base}_Part{part_num}_lip_crop.mp4'
        else:
            dst_name = f'{base}_lip_crop.mp4'
        import shutil
        shutil.copy2(str(src), str(lip_dir / dst_name))
        copied += 1

print(f'[INFO] Copied {copied} lip crop(s) to {lip_dir}')
" 2>&1 || log_warn "Lip crop copy failed (non-critical)"

  log_info "Client outputs complete"
  log_info "Outputs saved to: $post_root"
  return 0
}

export -f run_client_outputs
