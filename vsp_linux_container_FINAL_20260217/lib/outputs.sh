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

  mkdir -p "$report_dir"
  # Burned videos / lip-crops / beam-analysis are opt-in. Default output is
  # just the two HTML reports. Set VSP_FULL_OUTPUTS=1 to restore the rest.
  local full_outputs="${VSP_FULL_OUTPUTS:-0}"
  [ "$full_outputs" = "1" ] && mkdir -p "$burn_dir"

  # Find decode output (check both nested and flat paths)
  local decode_json
  decode_json="$(ls -t ${vsp_dir}/decode/vsr/en/vsr/en/hypo-*.json ${vsp_dir}/decode/vsr/en/hypo-*.json 2>/dev/null | grep -v "merged" | head -n 1)"

  if [ -z "$decode_json" ] || [ ! -f "$decode_json" ]; then
    log_error "Decode JSON not found in ${vsp_dir}/decode/vsr/en/"
    return 1
  fi

  # Burns are always rendered on the post-split full-face video in $flat_vid_dir.
  # The mouth-crop dir below is only used downstream (lip_crops/ copy) — never
  # as a burn source (see make_burn.py: refusing to burn on mouth crops).
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

  # ---- Aggregate per-token confidence -> per-word (only if sidecar present) ----
  local confidence_json="${decode_json/hypo-/confidence-}"
  local word_conf_json=""
  if [ -f "$confidence_json" ]; then
    echo ">>> [8] Aggregating per-token confidence to per-word"
    local conf_script="$vsp_dir/scripts/compute_word_confidence.py"
    if [ ! -f "$conf_script" ]; then
      conf_script="${HOME}/docs/_research-tools/generators/compute_word_confidence.py"
    fi
    if [ -f "$conf_script" ]; then
      word_conf_json="$report_dir/word_confidence.json"
      python3 "$conf_script" "$confidence_json" --out "$word_conf_json" \
        || { log_warn "compute_word_confidence.py failed (non-critical)"; word_conf_json=""; }
      cp "$confidence_json" "$report_dir/" 2>/dev/null || true
    else
      log_warn "compute_word_confidence.py not found — confidence aggregation skipped"
    fi
  else
    log_info "[8] No confidence-{fid}.json sidecar — confidence will be skipped"
  fi

  # ---- N-best aggregation (only if nbest sidecar present) ----
  local nbest_json="${decode_json/hypo-/nbest-}"
  local agg_json=""
  if [ -f "$nbest_json" ]; then
    echo ">>> [8] Aggregating n-best beams (MBR / weighted-vote / safe / xseg-merge)"
    local agg_script="$vsp_dir/scripts/nbest_aggregate.py"
    if [ ! -f "$agg_script" ]; then
      agg_script="${HOME}/lib/nbest_aggregate.py"
    fi
    if [ -f "$agg_script" ]; then
      agg_json="$report_dir/aggregated.json"
      local seg_meta_arg=""
      [ -f "$segment_metadata" ] && seg_meta_arg="--seg-meta $segment_metadata"
      python3 "$agg_script" --nbest "$nbest_json" --out "$agg_json" $seg_meta_arg \
        || { log_warn "nbest_aggregate.py failed (non-critical)"; agg_json=""; }
      cp "$nbest_json" "$report_dir/" 2>/dev/null || true
    else
      log_warn "nbest_aggregate.py not found — n-best aggregation skipped"
    fi
  fi

  # ---- Per-word beam-agreement sidecar + joint band rule ----
  # When BOTH nbest + confidence sidecars exist, build agreement-{fid}.json and
  # regenerate word_confidence.json under the joint conf+agreement rule
  # (see TRUST_DIAGNOSTIC.md, May 2 2026). Fails gracefully if missing.
  local agree_json=""
  if [ -f "$nbest_json" ] && [ -f "$confidence_json" ] && [ -n "$word_conf_json" ]; then
    local agree_script="$vsp_dir/scripts/compute_word_agreement.py"
    if [ ! -f "$agree_script" ]; then
      agree_script="${HOME}/VSP-LLM/scripts/compute_word_agreement.py"
    fi
    if [ -f "$agree_script" ]; then
      echo ">>> [8] Computing per-word beam agreement"
      agree_json="$report_dir/agreement-$(basename "$nbest_json" | sed -E 's/^nbest-//; s/\.json$//').json"
      python3 "$agree_script" \
        --nbest "$nbest_json" \
        --confidence "$confidence_json" \
        --out "$agree_json" \
        || { log_warn "compute_word_agreement.py failed (non-critical)"; agree_json=""; }
      if [ -n "$agree_json" ] && [ -f "$agree_json" ]; then
        echo ">>> [8] Re-aggregating per-word confidence with joint conf+agreement rule"
        local conf_script2="$vsp_dir/scripts/compute_word_confidence.py"
        if [ ! -f "$conf_script2" ]; then
          conf_script2="${HOME}/docs/_research-tools/generators/compute_word_confidence.py"
        fi
        python3 "$conf_script2" "$confidence_json" \
          --agreement "$agree_json" \
          --out "$word_conf_json" \
          || log_warn "compute_word_confidence.py (joint pass) failed (non-critical)"
      fi
    else
      log_warn "compute_word_agreement.py not found — joint band rule skipped"
    fi
  fi

  # Compute Intelligibility Scores in reports
  echo ">>> [8] Intelligibility Scores enabled"

  # Generate report (always with IS scoring; optionally with word confidence and aggregated hyps)
  local conf_arg=""
  [ -n "$word_conf_json" ] && conf_arg="--word-confidence $word_conf_json"
  local agg_arg=""
  [ -n "$agg_json" ] && [ -f "$agg_json" ] && agg_arg="--aggregated $agg_json"
  # Display method (Mission 6 production switch, May 2026):
  # When the n-best aggregator has produced an aggregated.json, default to using
  # `hyp_mbr` as the displayed/primary output. This is judge-validated: +40 net
  # Y+P verdicts vs top1 (paired McNemar p=0.0002, n=1,497, May 2 2026).
  # Override with VSP_DISPLAY_METHOD=top1 (or any other method name) if needed
  # for A/B testing or backwards-compatibility runs.
  local display_arg=""
  if [ -n "$agg_json" ] && [ -f "$agg_json" ]; then
    local method="${VSP_DISPLAY_METHOD:-hyp_mbr}"
    display_arg="--display-method $method"
    echo ">>> [8] Display method: $method (override with VSP_DISPLAY_METHOD)"
  fi
  python3 "$vsp_dir/scripts/make_report.py" \
    --jsonl "$decode_json" \
    --out_dir "$report_dir" \
    $params_arg --compute-is $conf_arg $agg_arg $display_arg || {
    log_error "make_report.py failed"
    return 1
  }

  if [ "$full_outputs" = "1" ]; then
    # Optional: full augmented Intelligibility analysis (CSV + summary JSON).
    local is_script="$vsp_dir/scripts/generate_intelligibility_scores.py"
    if [ ! -f "$is_script" ]; then
      is_script="${HOME}/docs/_research-tools/generators/generate_intelligibility_scores.py"
    fi
    if [ -f "$is_script" ] && [ -f "$report_dir/report.csv" ]; then
      echo ">>> [8] Computing full Intelligibility analysis (IS + LLM context recovery)..."
      python3 "$is_script" \
        --csv "$report_dir/report.csv" \
        --out_dir "$report_dir" \
        --device cpu \
        || log_warn "Full Intelligibility analysis failed (non-critical) — basic report still available"
    fi

    # Optional: beam variance & word-level confusion analysis.
    if [ -f "$nbest_json" ] && [ "${VSP_BEAM_ANALYSIS:-1}" = "1" ]; then
      echo ">>> [8] Running beam variance & word-level confusion analysis"
      local bva_script="$vsp_dir/scripts/analyze_beam_variance.py"
      if [ ! -f "$bva_script" ]; then
        bva_script="${HOME}/docs/_research-tools/generators/analyze_beam_variance.py"
      fi
      if [ -f "$bva_script" ]; then
        local bva_dir="$report_dir/beam_analysis"
        mkdir -p "$bva_dir"
        local bva_args=("--nbest" "$nbest_json" "--out-dir" "$bva_dir")
        [ -n "$agg_json" ] && [ -f "$agg_json" ] && bva_args+=("--aggregated" "$agg_json")
        [ -f "$report_dir/report.csv" ] && bva_args+=("--baseline-csv" "$report_dir/report.csv")
        [ -f "$decode_json" ] && bva_args+=("--hypo-json" "$decode_json")
        [ -f "$confidence_json" ] && bva_args+=("--confidence" "$confidence_json")
        python3 "$bva_script" "${bva_args[@]}" \
          || log_warn "analyze_beam_variance.py failed (non-critical)"
      fi
    fi

    # Optional: burned videos with per-word coloring + tier badge.
    local burn_conf_arg=""
    [ -n "$word_conf_json" ] && [ -f "$word_conf_json" ] && burn_conf_arg="--word_confidence $word_conf_json"
    python3 "$vsp_dir/scripts/make_burn.py" \
      --jsonl "$decode_json" \
      --video_dir "$flat_vid_dir" \
      --segment_metadata "$segment_metadata" \
      --out_dir "$burn_dir" \
      $burn_conf_arg \
      || log_warn "make_burn.py failed (non-critical)"

    # Optional: copy lip crops to client output.
    local lip_dir="${post_root}/lip_crops"
    mkdir -p "$lip_dir"
    echo ">>> [8] Copying lip crop videos to client outputs"
    python3 -c "
import json, sys
from pathlib import Path

decode_json = Path('$decode_json')
segment_vid_dir = Path('$segment_vid_dir')
lip_dir = Path('$lip_dir')
try:
    data = json.loads(decode_json.read_text())
except Exception as e:
    print(f'[WARN] Cannot read decode JSON for lip crops: {e}')
    sys.exit(0)
utt_ids = data.get('utt_id', [])
if not utt_ids:
    sys.exit(0)
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
import shutil
copied = 0
for base, entries in groups.items():
    entries.sort()
    is_multi = len(entries) > 1
    for part_num, (_, uid) in enumerate(entries, 1):
        src = segment_vid_dir / f'{uid}.mp4'
        if not src.exists():
            continue
        dst_name = f'{base}_Part{part_num}_lip_crop.mp4' if is_multi else f'{base}_lip_crop.mp4'
        shutil.copy2(str(src), str(lip_dir / dst_name))
        copied += 1
print(f'[INFO] Copied {copied} lip crop(s) to {lip_dir}')
" 2>&1 || log_warn "Lip crop copy failed (non-critical)"
  fi

  # Generate Argos confidence-breakdown HTML alongside the main report.
  run_argos_demo_report "$vsp_dir" "$decode_json" "$report_dir" \
    || log_warn "Confidence breakdown report failed (non-critical) — main report still available"

  # Default output is the two HTML files. Prune intermediates unless caller
  # asked for the full output set (VSP_FULL_OUTPUTS=1).
  if [ "$full_outputs" != "1" ]; then
    echo ">>> [8] Pruning intermediates — keeping only HTML reports"
    find "$report_dir" -mindepth 1 -maxdepth 1 \
      ! -name 'report.html' \
      ! -name 'confidence_breakdown.html' \
      -exec rm -rf {} + 2>/dev/null || true
  fi

  log_info "Client outputs complete"
  log_info "Outputs saved to: $post_root"
  return 0
}

# Generate the dark per-segment "Confidence Breakdown" HTML alongside the
# main report. Per-word coloring uses the confidence palette
# (blue / orange / purple) when a real word_confidence sidecar is available,
# falling back to the synthetic REF↔HYP alignment otherwise.
#
# Parameters:
#   $1 - VSP directory (used to locate the script)
#   $2 - decode JSON path (hypo-NNNN.json)
#   $3 - report output directory (where confidence_breakdown.html is written)
run_argos_demo_report() {
  local vsp_dir="$1"
  local decode_json="$2"
  local report_dir="$3"

  if [ ! -f "$decode_json" ]; then
    log_warn "Confidence breakdown: decode JSON not found at $decode_json"
    return 1
  fi

  # Resolve generator script: prefer the canonical scripts/ copy, fall back
  # to the EC2 docs/ copy for development environments.
  local gen_script="$vsp_dir/scripts/generate_client_demo_report.py"
  if [ ! -f "$gen_script" ]; then
    gen_script="${HOME}/docs/_research-tools/generators/generate_client_demo_report.py"
  fi
  if [ ! -f "$gen_script" ]; then
    log_warn "Confidence breakdown: generator script not found (tried scripts/ and docs/)"
    return 1
  fi

  local out_html="${report_dir}/confidence_breakdown.html"
  echo ">>> [8] Generating Confidence Breakdown HTML report"
  python3 "$gen_script" \
    --decode "$decode_json" \
    --out "$out_html" \
    || { log_warn "Confidence breakdown report generator failed"; return 1; }

  log_info "Confidence breakdown report: $out_html"
  return 0
}

export -f run_client_outputs
export -f run_argos_demo_report
