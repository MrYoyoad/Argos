#!/usr/bin/env bash
# ==================================================
# Common Utilities for VSP Pipeline
# ==================================================
# Provides logging, validation, and utility functions
# used across all pipeline stages.

# ---------- Logging Functions ----------

log_info() {
    echo "[$(date +'%H:%M:%S')] INFO: $*" >&2
}

log_error() {
    echo "[$(date +'%H:%M:%S')] ERROR: $*" >&2
}

log_warn() {
    echo "[$(date +'%H:%M:%S')] WARN: $*" >&2
}

log_stage() {
    local stage_num="$1"
    local stage_name="$2"
    echo ""
    echo "==================================================="
    echo ">>> [$stage_num] $stage_name"
    echo "==================================================="
}

# ---------- Validation Functions ----------

validate_directory() {
    local dir="$1"
    local name="$2"

    if [[ ! -d "$dir" ]]; then
        log_error "$name directory not found: $dir"
        return 1
    fi
    return 0
}

validate_file() {
    local file="$1"
    local name="$2"

    if [[ ! -f "$file" ]]; then
        log_error "$name file not found: $file"
        return 1
    fi
    return 0
}

validate_command() {
    local cmd="$1"

    if ! command -v "$cmd" &>/dev/null; then
        log_error "Required command not found: $cmd"
        return 1
    fi
    return 0
}

# ---------- Utility Functions ----------

ensure_directory() {
    local dir="$1"
    mkdir -p "$dir" || {
        log_error "Failed to create directory: $dir"
        return 1
    }
    return 0
}

count_files() {
    local dir="$1"
    local pattern="$2"

    find "$dir" -maxdepth 1 -type f -name "$pattern" 2>/dev/null | wc -l | tr -d ' '
}
