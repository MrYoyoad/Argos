#!/usr/bin/env bash
# ==================================================
# Archive Module
# ==================================================
# Handles archiving of previous pipeline run outputs
# Preserves segment transcriptions for reuse

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Archive previous run outputs
# Parameters:
#   $1 - Base directory (HOME_DIR)
#   $2 - Segment duration (for PREP_ROOT path)
#   $3+ - Array of directories to archive (passed as separate arguments)
#
# Special handling:
#   - Creates timestamped archive directory
#   - Archives standard directories with simple move
#   - Preserves segment transcriptions in PREP_ROOT/flat/flat_text_seg*
#
# Returns:
#   Archive root path via stdout
archive_previous_run() {
  local home_dir="$1"
  local seg_duration="$2"
  shift 2

  # Remaining arguments are directories to archive
  local to_archive=("$@")

  # Create timestamped archive directory
  local run_id
  run_id="$(date +'%Y%m%d_%H%M%S')"
  local archive_root="${home_dir}/flat_runs_archive/${run_id}"
  mkdir -p "${archive_root}"

  log_info "Run ID: ${run_id}"
  log_info "Archiving previous outputs (if any) to: ${archive_root}"

  # Archive standard directories
  local d
  for d in "${to_archive[@]}"; do
    if [[ -e "${d}" ]]; then
      log_info "Moving ${d} -> ${archive_root}/"
      mv "${d}" "${archive_root}/"
    fi
  done

  log_info "Archive step done"

  # Return archive root path for caller
  echo "${archive_root}"
}

# Archive PREP_ROOT with special handling for segment transcriptions
# Parameters:
#   $1 - PREP_ROOT path
#   $2 - Archive root path
#   $3 - Segment duration (for directory name)
archive_prep_root() {
  local prep_root="$1"
  local archive_root="$2"
  local seg_duration="$3"

  if [[ ! -e "${prep_root}" ]]; then
    return 0
  fi

  log_info "Archiving ${prep_root} (preserving segment transcriptions)..."
  mkdir -p "${archive_root}/preprocessed_flat_seg${seg_duration}"

  # Move everything except 'flat' directory (handle it separately)
  local item basename_item
  for item in "${prep_root}"/*; do
    if [[ -e "${item}" ]]; then
      basename_item=$(basename "${item}")

      # Skip the 'flat' directory - we'll handle it separately
      if [[ "${basename_item}" == "flat" ]]; then
        continue
      fi

      echo ">>> [INIT]   Moving ${item}"
      mv "${item}" "${archive_root}/preprocessed_flat_seg${seg_duration}/"
    fi
  done

  # Handle 'flat' subdirectory: preserve flat_text_seg* folders
  if [[ -d "${prep_root}/flat" ]]; then
    mkdir -p "${archive_root}/preprocessed_flat_seg${seg_duration}/flat"

    for item in "${prep_root}/flat"/*; do
      if [[ -e "${item}" ]]; then
        basename_item=$(basename "${item}")

        # Skip flat_text_seg* folders (these contain manual/auto segment transcriptions)
        if [[ "${basename_item}" =~ ^flat_text_seg[0-9]+s$ ]]; then
          echo ">>> [INIT]   Preserving ${item} (segment transcriptions)"
          continue
        fi

        echo ">>> [INIT]   Moving ${item}"
        mv "${item}" "${archive_root}/preprocessed_flat_seg${seg_duration}/flat/"
      fi
    done
  fi
}

export -f archive_previous_run
export -f archive_prep_root
