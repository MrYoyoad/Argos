#!/usr/bin/env bash
# ==================================================
# LRS3 Preparation Module
# ==================================================
# Converts flat dataset to LRS3 format
# Works on EC2 and Linux container

# Source common utilities for logging
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${MODULE_DIR}/common.sh"

# Run flat_to_lrs3_preperation.sh
# Parameters:
#   $1 - PREP_ROOT path
#   $2 - AVH directory
#   $3 - SEG_DURATION value
#   $4 - DIR_SUFFIX value
run_lrs3_preparation() {
  local prep_root="$1"
  local avh_dir="$2"
  local seg_duration="$3"
  local dir_suffix="$4"

  log_stage "4" "Running flat_to_lrs3_preperation.sh"

  SEG_DURATION="$seg_duration" \
  DIR_SUFFIX="$dir_suffix" \
  LRS3_ROOT="$prep_root" \
  bash "$avh_dir/avhubert/preparation/flat_to_lrs3_preperation.sh" \
    "$prep_root" || {
    log_error "flat_to_lrs3_preperation.sh failed"
    return 1
  }

  log_info "LRS3 preparation complete"
  return 0
}

export -f run_lrs3_preparation
