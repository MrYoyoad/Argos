#!/usr/bin/env bash
# ==================================================
# Environment-Aware Configuration
# ==================================================
# Automatically detects EC2 vs container environment
# and sets appropriate paths for both.

# ---------- Environment Detection ----------

detect_environment() {
    # Check if running in container (has /workspace and HOME is /root)
    if [[ -d "/workspace" ]] && [[ "$HOME" == "/root" ]]; then
        echo "container"
    else
        echo "ec2"
    fi
}

get_base_path() {
    local env=$(detect_environment)

    if [[ "$env" == "container" ]]; then
        echo "/workspace"
    else
        echo "/home/ubuntu"
    fi
}

# ---------- Global Path Configuration ----------

# Export environment type
export ENV_TYPE=$(detect_environment)

# Base path (auto-detects /home/ubuntu or /workspace)
export BASE_PATH=$(get_base_path)

# Component directories
export AUTO_AVSR="${BASE_PATH}/auto_avsr"
export VSP="${BASE_PATH}/VSP-LLM"
export AVH="${BASE_PATH}/av_hubert"

# Virtual environments
export PREP_VENV="${AUTO_AVSR}/pre-process-venv"
export ASR_VENV="${AUTO_AVSR}/pre-process-venv"
export VSP_VENV="${BASE_PATH}/vsp-llm-yoad-venv"

# Dataset name and language
export DATA_NAME="${DATA_NAME:-flat}"
export LANG="${LANG:-en}"

# ---------- Derived Paths ----------

# Core dataset directories
export FLAT_VID_DIR="${AUTO_AVSR}/${DATA_NAME}"
export WRD_DIR="${AUTO_AVSR}/${DATA_NAME}_wrd"
export TXT_DIR="${AUTO_AVSR}/${DATA_NAME}_txt"
export READY_DIR="${AUTO_AVSR}/preprocess_ready_${DATA_NAME}"

# Preprocessing output (segment duration set by main script)
get_prep_root() {
    local seg_duration="${1:-4}"
    echo "${AUTO_AVSR}/preprocessed_${DATA_NAME}_seg${seg_duration}"
}

# Manifest directory
get_manifest_root() {
    local prep_root="$1"
    echo "${prep_root}/433h_data"
}

# VSP-LLM directories
export FEAT_DIR="${VSP}/${DATA_NAME}_features"
export LAB_DIR="${VSP}/${DATA_NAME}_labels"
export DECODE_ROOT="${VSP}/decode"

get_km_path() {
    local num_clusters="${1:-200}"
    echo "${VSP}/${DATA_NAME}_kmeans_${num_clusters}.bin"
}

# ---------- Export Functions for Use in Pipeline ----------

export -f detect_environment
export -f get_base_path
export -f get_prep_root
export -f get_manifest_root
export -f get_km_path
