#!/usr/bin/env bash
# ==================================================
# VSP-LLM Decode Module
# ==================================================
# Handles VSP-LLM decoding for visual speech recognition
# Assumes VSP_VENV is already activated by caller
# Works on EC2 and Linux container

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Run VSP-LLM decode
# Parameters:
#   $1 - VSP directory
#   $2 - MANIFEST_ROOT path
#   $3 - LAB_DIR path
#   $4 - WRD_ROOT path
#   $5 - PREP_ROOT path
#   $6 - SEGMENTATION_ENABLED flag (0 or 1)
#   $7 - OVERLAP_ENABLED flag (0 or 1)
#
# Note: Assumes VSP_VENV is already activated by caller
run_vsp_decode() {
  local vsp_dir="$1"
  local manifest_root="$2"
  local lab_dir="$3"
  local wrd_root="$4"
  local prep_root="$5"
  local segmentation_enabled="${6:-1}"
  local overlap_enabled="${7:-1}"

  log_stage "7" "Running VSP-LLM decode"

  # Create dataset directory and symlinks
  mkdir -p "$vsp_dir/src/dataset/vsr/en"

  ln -sf "$manifest_root/train.tsv" "$vsp_dir/src/dataset/vsr/en/train.tsv"
  ln -sf "$manifest_root/train.wrd" "$vsp_dir/src/dataset/vsr/en/train.wrd"
  ln -sf "$lab_dir/train.cluster_counts" "$vsp_dir/src/dataset/vsr/en/train.cluster_counts"

  # Create test symlinks (point to train data)
  ln -sf "$vsp_dir/src/dataset/vsr/en/train.tsv" "$vsp_dir/src/dataset/vsr/en/test.tsv"
  ln -sf "$vsp_dir/src/dataset/vsr/en/train.wrd" "$vsp_dir/src/dataset/vsr/en/test.wrd"
  ln -sf "$vsp_dir/src/dataset/vsr/en/train.cluster_counts" "$vsp_dir/src/dataset/vsr/en/test.cluster_counts"

  # Run decode script
  cd "$vsp_dir" || {
    log_error "Failed to cd to VSP directory: $vsp_dir"
    return 1
  }

  LANG="en" \
  SPLIT="train" \
  LRS3_ROOT="$prep_root" \
  LAB_DIR="$lab_dir" \
  WRD_ROOT="$wrd_root" \
  bash "$vsp_dir/scripts/run_flat_decode.sh" || {
    log_error "VSP-LLM decode failed"
    return 1
  }

  # ============================================
  # STEP 7a: Merge - DISABLED
  # ============================================
  if [ "$segmentation_enabled" = "1" ]; then
    if [ "$overlap_enabled" = "1" ]; then
      echo ">>> [7a] Segments processed independently - merge step skipped"
      echo "    Each segment will appear separately in reports and burned videos"
    else
      echo ">>> [7a] Segments processed independently (overlap disabled)"
    fi
  else
    echo ">>> [7a] Whole videos processed (no segmentation) - merge step not applicable"
  fi

  log_info "VSP-LLM decode complete"
  return 0
}

export -f run_vsp_decode
