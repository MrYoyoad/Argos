#!/usr/bin/env bash
set -euo pipefail

# Auto-detect galaxy_export root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GALAXY_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# CONTAINER VERSION: Hardcoded /workspace venv path
VSP_VENV="/workspace/vsp-llm-yoad-venv"

echo ">>> Activating venv: ${VSP_VENV}"
source "${VSP_VENV}/bin/activate"

# Root of repo (one level up from scripts/)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------- Config with defaults ----------

: "${LRS3_ROOT:=${GALAXY_ROOT}/auto_avsr/preprocessed_flat_seg4}"
# Set TSV_ROOT depending on split:
#   - train/valid: use 433h_data
#   - test:        use 30h_data
# You can still override TSV_ROOT via environment if you want.
if [[ "${SPLIT}" == "test" ]]; then
    : "${TSV_ROOT:=${LRS3_ROOT}/30h_data}"
else
    : "${TSV_ROOT:=${LRS3_ROOT}/433h_data}"
fi

: "${CKPT:=${ROOT}/checkpoints/large_vox_iter5.pt}"
: "${FEAT_DIR:=${ROOT}/flat_features}"
: "${KM_PATH:=${ROOT}/flat_kmeans_200.bin}"
: "${LAB_DIR:=${ROOT}/flat_labels}"
: "${USER_DIR:=${ROOT}/src}"

# THIS is the important one: which split to process
: "${SPLIT:=train}"          # can be train / valid / test
: "${NSHARD:=1}"
: "${TRAIN_KMEANS:=1}"       # 1 = train k-means, 0 = reuse existing
: "${PERCENT:=0.1}"          # fraction of data for k-means training

echo ">>> Using:"
echo "    LRS3_ROOT = ${LRS3_ROOT}"
echo "    TSV_ROOT  = ${TSV_ROOT}"
echo "    CKPT      = ${CKPT}"
echo "    FEAT_DIR  = ${FEAT_DIR}"
echo "    KM_PATH   = ${KM_PATH}"
echo "    LAB_DIR   = ${LAB_DIR}"
echo "    USER_DIR  = ${USER_DIR}"
echo "    NSHARD    = ${NSHARD}"
echo "    TRAIN_KMEANS = ${TRAIN_KMEANS}"
echo "    PERCENT   = ${PERCENT}"
echo "    SPLIT     = ${SPLIT}"
echo

# Make sure dirs exist
mkdir -p "${FEAT_DIR}" "${LAB_DIR}"

# ---------- Step 1: dump HuBERT features ----------

echo ">>> [Step 1] Dumping HuBERT features for split: ${SPLIT}"
python3 "${ROOT}/src/clustering/dump_hubert_feature.py" \
    "${TSV_ROOT}" \
    "${SPLIT}" \
    "${CKPT}" \
    12 \
    "${NSHARD}" \
    0 \
    "${FEAT_DIR}" \
    --max_chunk 1600000 \
    --user_dir "${USER_DIR}"

# ---------- Step 2: train k-means (optional) ----------

# Check if using a golden (pre-trained) model
if [[ -n "${GOLDEN_KMEANS:-}" ]]; then
  echo
  echo ">>> [Step 2] Using golden k-means model: ${GOLDEN_KMEANS}"
  if [[ ! -f "${GOLDEN_KMEANS}" ]]; then
    echo "ERROR: Golden model not found at ${GOLDEN_KMEANS}"
    exit 1
  fi
  cp "${GOLDEN_KMEANS}" "${KM_PATH}"
  echo "    Copied to: ${KM_PATH}"
elif [[ "${TRAIN_KMEANS}" == "1" ]]; then
  echo
  echo ">>> [Step 2] Learning k-means (200 clusters) on ${PERCENT} of data for split: ${SPLIT}"
  python3 "${ROOT}/src/clustering/learn_kmeans.py" \
      "${FEAT_DIR}" \
      "${SPLIT}" \
      "${NSHARD}" \
      "${KM_PATH}" \
      200 \
      --percent "${PERCENT}"
else
  echo
  echo ">>> [Step 2] Skipping k-means training (TRAIN_KMEANS!=1)"
  if [[ ! -f "${KM_PATH}" ]]; then
    echo "ERROR: No k-means model found at ${KM_PATH}"
    echo "       Either train a new model (TRAIN_KMEANS=1) or provide GOLDEN_KMEANS path"
    exit 1
  fi
  echo "    Using existing model: ${KM_PATH}"
fi

# ---------- Step 3: dump k-means labels ----------

echo
echo ">>> [Step 3] Dumping k-means labels for ${SPLIT}"
python3 "${ROOT}/src/clustering/dump_km_label.py" \
    "${FEAT_DIR}" \
    "${SPLIT}" \
    "${KM_PATH}" \
    "${NSHARD}" \
    0 \
    "${LAB_DIR}"

# ---------- Step 4: concat shards ----------

echo
echo ">>> [Step 4] Concatenating shard labels -> ${LAB_DIR}/${SPLIT}.km"
> "${LAB_DIR}/${SPLIT}.km"
for RANK in $(seq 0 $((NSHARD - 1))); do
  cat "${LAB_DIR}/${SPLIT}_${RANK}_${NSHARD}.km" >> "${LAB_DIR}/${SPLIT}.km"
done

echo
echo ">>> Done run_flat_kmeans.sh"
