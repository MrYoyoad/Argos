#!/usr/bin/env bash
# ==================================================
# K-means Clustering Module
# ==================================================
# Handles k-means feature extraction and cluster count generation
# Works on EC2 and Linux container

# Source common utilities for logging
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${MODULE_DIR}/common.sh"

# Run k-means clustering and cluster count extraction
# Parameters:
#   $1 - PREP_ROOT path
#   $2 - FEAT_DIR path
#   $3 - KM_PATH path
#   $4 - LAB_DIR path
#   $5 - AVH directory
#   $6 - VSP directory
#   $7 - TRAIN_KMEANS flag (0 or 1, default 1)
run_clustering() {
  local prep_root="$1"
  local feat_dir="$2"
  local km_path="$3"
  local lab_dir="$4"
  local avh_dir="$5"
  local vsp_dir="$6"
  local train_kmeans="${7:-1}"

  log_stage "6" "Running k-means and cluster count extraction"

  cd "$avh_dir/avhubert/preparation" || {
    log_error "Failed to cd to avhubert/preparation"
    return 1
  }

  # Run k-means feature extraction and training
  TRAIN_KMEANS="$train_kmeans" \
  LRS3_ROOT="$prep_root" \
  SPLIT="train" \
  NSHARD=1 \
  PERCENT=1.0 \
  FEAT_DIR="$feat_dir" \
  KM_PATH="$km_path" \
  LAB_DIR="$lab_dir" \
  "$vsp_dir/scripts/run_flat_kmeans.sh" || {
    log_error "K-means training failed"
    return 1
  }

  # Run cluster count generation
  LRS3_ROOT="$prep_root" \
  FEAT_DIR="$feat_dir" \
  KM_PATH="$km_path" \
  LAB_DIR="$lab_dir" \
  SPLIT="train" \
  NSHARD=1 \
  "$vsp_dir/scripts/run_cluster_counts.sh" || {
    log_error "Cluster count generation failed"
    return 1
  }

  log_info "K-means clustering complete"
  return 0
}

export -f run_clustering
