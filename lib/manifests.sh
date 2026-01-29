#!/usr/bin/env bash
# ==================================================
# Manifest Generation Module
# ==================================================
# Handles manifest and TSV generation for VSP-LLM
# Works on EC2 and Linux container

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Generate manifests, splits, and train.tsv
# Parameters:
#   $1 - PREP_ROOT path
#   $2 - MANIFEST_ROOT path
#   $3 - AUTO_AVSR directory
#   $4 - AVH directory
#   $5 - VSP directory
#   $6 - SEGMENTATION_ENABLED flag (0 or 1)
#   $7 - OVERLAP_ENABLED flag (0 or 1)
run_manifest_generation() {
  local prep_root="$1"
  local manifest_root="$2"
  local auto_avsr_dir="$3"
  local avh_dir="$4"
  local vsp_dir="$5"
  local segmentation_enabled="${6:-1}"
  local overlap_enabled="${7:-1}"

  log_stage "5" "Building manifests and TSVs"

  # Generate simple manifest
  python "$auto_avsr_dir/make_simple_manifest.py" \
    --root "$prep_root" \
    --split train \
    --out-dir "$manifest_root" || {
    log_error "make_simple_manifest.py failed"
    return 1
  }

  # Split dataset
  python "$avh_dir/avhubert/preparation/split_flat_dataset.py" \
    --root "$prep_root" \
    --train-ratio 1.0 \
    --valid-ratio 0.0 \
    --test-ratio 0.0 \
    --seed 0 || {
    log_error "split_flat_dataset.py failed"
    return 1
  }

  # Build train TSV
  python "$vsp_dir/scripts/build_flat_train_tsv.py" \
    --root "$prep_root" || {
    log_error "build_flat_train_tsv.py failed"
    return 1
  }

  # Generate segment timing metadata (if segmentation and overlap enabled)
  if [ "$segmentation_enabled" = "1" ] && [ "$overlap_enabled" = "1" ]; then
    log_info "Generating segment timing metadata..."

    python "$auto_avsr_dir/generate_segment_timing.py" \
      --manifest-tsv "$manifest_root/train.tsv" \
      --segment-metadata "$prep_root/segment_metadata.json" \
      --output-json "$manifest_root/segment_timing.json" || {
      log_error "generate_segment_timing.py failed"
      return 1
    }

    log_info "Timing metadata saved to: $manifest_root/segment_timing.json"
  else
    log_info "Skipping segment timing (segmentation disabled or overlap disabled)"
  fi

  log_info "Manifest generation complete"
  return 0
}

export -f run_manifest_generation
