#!/usr/bin/env bash
# ==================================================
# Client Outputs Module
# ==================================================
# Generates client-facing outputs (reports and burned videos)
# Assumes VSP_VENV is already activated by caller
# Works on EC2 and Linux container

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

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

  # Generate report
  python "$vsp_dir/scripts/make_report.py" \
    --jsonl "$decode_json" \
    --out_dir "$report_dir" || {
    log_error "make_report.py failed"
    return 1
  }

  # Generate burned videos
  python "$vsp_dir/scripts/make_burn.py" \
    --jsonl "$decode_json" \
    --video_dir "$flat_vid_dir" \
    --segment_dir "$segment_vid_dir" \
    --segment_metadata "$segment_metadata" \
    --out_dir "$burn_dir" || {
    log_error "make_burn.py failed"
    return 1
  }

  log_info "Client outputs complete"
  log_info "Outputs saved to: $post_root"
  return 0
}

export -f run_client_outputs
