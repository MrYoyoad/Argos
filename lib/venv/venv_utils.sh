#!/usr/bin/env bash
# ==================================================
# Virtual Environment Management
# ==================================================
# Works on EC2 and Linux container (same method used in current pipeline)

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../common.sh"

activate_venv() {
    local venv_path="$1"
    local stage_num="${2:-unknown}"

    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found: $venv_path"
        return 1
    fi

    log_info "Activating venv: $venv_path (stage $stage_num)"
    # Same method as line 561, 687, 762 in container pipeline
    source "${venv_path}/bin/activate" || {
        log_error "Failed to activate venv: $venv_path"
        return 1
    }
}

deactivate_venv() {
    if command -v deactivate &>/dev/null; then
        log_info "Deactivating virtual environment"
        deactivate 2>/dev/null || true
    fi
}

export -f activate_venv
export -f deactivate_venv
