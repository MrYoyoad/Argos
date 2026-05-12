#!/usr/bin/env bash
# ==========================================================================
# LRS3 → VSP-LLM Training Data Preparation
# ==========================================================================
# Routes raw LRS3 ({pretrain,trainval,test}/<spk>/<utt>.{mp4,txt}) through the
# AV-HuBERT prep pipeline and VSP-LLM clustering, producing the fairseq-ready
# manifest set the paper-equivalent training run expects.
#
# Pipeline stages (resumable: each stage skips if its sentinel output exists):
#   1. lrs3_prepare.py step 1-4: split long pretrains, trim, audio extract, file/label lists
#   2. detect_landmark.py + align_mouth.py: facial landmarks + 88x88 mouth ROIs
#   3. count_frames.py: per-clip audio/video frame counts
#   4. lrs3_manifest.py: build initial train/valid/test TSVs
#   5. dump_hubert_feature.py: AV-HuBERT layer-12 visual features
#   6. learn_kmeans.py: 200-cluster k-means (skip if golden_kmeans/ exists)
#   7. dump_km_label.py + cluster_counts.py: per-frame cluster labels → cluster_counts
#   8. Stage outputs to ${VSP_TRAIN_DATA} for fairseq-hydra-train
#
# Output: ${VSP_TRAIN_DATA}/{train,valid,test}.{tsv,wrd,cluster_counts} + dict.wrd.txt
#
# Environment (override via env vars, defaults shown):
#   LRS3_RAW        = /home/ubuntu/datasets/lrs3_raw
#   LRS3_PROCESSED  = /home/ubuntu/datasets/lrs3_processed
#   VSP_TRAIN_DATA  = /home/ubuntu/lrs3_train_data
#   AVH             = /home/ubuntu/av_hubert
#   VSP             = /home/ubuntu/VSP-LLM
#   AVH_CKPT        = ${VSP}/checkpoints/large_vox_iter5.pt
#   KMEANS_BIN      = ${VSP_TRAIN_DATA}/lrs3_kmeans_200.bin  (or reuse golden_kmeans/)
#   N_CLUSTERS      = 200
#   FEAT_LAYER      = 12
#   NSHARD          = 1   (set to # of GPUs for parallel feature/label dump)
#   FFMPEG          = ffmpeg
#   VENV            = /home/ubuntu/vsp-llm-yoad-venv
# ==========================================================================
set -euo pipefail

LRS3_RAW="${LRS3_RAW:-/home/ubuntu/datasets/lrs3_raw}"
LRS3_PROCESSED="${LRS3_PROCESSED:-/home/ubuntu/datasets/lrs3_processed}"
VSP_TRAIN_DATA="${VSP_TRAIN_DATA:-/home/ubuntu/lrs3_train_data}"
AVH="${AVH:-/home/ubuntu/av_hubert}"
VSP="${VSP:-/home/ubuntu/VSP-LLM}"
AVH_CKPT="${AVH_CKPT:-${VSP}/checkpoints/large_vox_iter5.pt}"
KMEANS_BIN="${KMEANS_BIN:-${VSP_TRAIN_DATA}/lrs3_kmeans_200.bin}"
N_CLUSTERS="${N_CLUSTERS:-200}"
FEAT_LAYER="${FEAT_LAYER:-12}"
NSHARD="${NSHARD:-1}"
FFMPEG="${FFMPEG:-ffmpeg}"
VENV="${VENV:-/home/ubuntu/vsp-llm-yoad-venv}"

# Lib helpers for consistent logging
source "${HOME}/lib/common.sh"

source "${VENV}/bin/activate"
export PYTHONPATH="${VSP}/fairseq:${AVH}:${PYTHONPATH:-}"

mkdir -p "${LRS3_PROCESSED}" "${VSP_TRAIN_DATA}"

# Pre-flight: confirm raw LRS3 layout is sane
for split in pretrain trainval test; do
  if [ ! -d "${LRS3_RAW}/${split}" ]; then
    log_error "Missing ${LRS3_RAW}/${split}/ — expected the Oxford VGG LRS3 layout (pretrain, trainval, test)."
    log_error "Acquire LRS3 first (see docs/finetuning/llama3-migration.md §4 'LRS3 acquisition')."
    exit 1
  fi
done
log_info "Raw LRS3 found at ${LRS3_RAW}"

# ----------------------------------------------------------------------------
# Stage 1: lrs3_prepare.py steps 1-4 (split, trim, audio, lists)
# ----------------------------------------------------------------------------
SENTINEL_S1="${LRS3_RAW}/file.list"
if [ ! -f "${SENTINEL_S1}" ]; then
  log_stage "1" "lrs3_prepare.py — split + trim + audio + lists"
  cd "${AVH}/avhubert/preparation"
  for step in 1 2 3 4; do
    log_info "  step ${step}/4"
    for rank in $(seq 0 $((NSHARD - 1))); do
      python lrs3_prepare.py \
        --lrs3 "${LRS3_RAW}" \
        --ffmpeg "${FFMPEG}" \
        --rank "${rank}" \
        --nshard "${NSHARD}" \
        --step "${step}"
    done
  done
else
  log_info "Stage 1 already done (${SENTINEL_S1} present)"
fi

# ----------------------------------------------------------------------------
# Stage 2: facial landmarks + 88x88 mouth ROIs
# ----------------------------------------------------------------------------
SENTINEL_S2="${LRS3_PROCESSED}/video"
if [ ! -d "${SENTINEL_S2}" ] || [ -z "$(ls -A "${SENTINEL_S2}" 2>/dev/null)" ]; then
  log_stage "2" "detect_landmark.py + align_mouth.py — face detect + mouth ROI"
  cd "${AVH}/avhubert/preparation"
  for rank in $(seq 0 $((NSHARD - 1))); do
    python detect_landmark.py \
      --root "${LRS3_RAW}" \
      --landmark "${LRS3_RAW}/landmark" \
      --manifest "${LRS3_RAW}/file.list" \
      --rank "${rank}" \
      --nshard "${NSHARD}" \
      --ffmpeg "${FFMPEG}"
    python align_mouth.py \
      --video-direc "${LRS3_RAW}" \
      --landmark "${LRS3_RAW}/landmark" \
      --filename-path "${LRS3_RAW}/file.list" \
      --save-direc "${LRS3_PROCESSED}/video" \
      --mean-face "${AVH}/avhubert/preparation/data/20words_mean_face.npy" \
      --ffmpeg "${FFMPEG}" \
      --rank "${rank}" \
      --nshard "${NSHARD}"
  done
else
  log_info "Stage 2 already done (mouth ROIs present at ${SENTINEL_S2})"
fi

# ----------------------------------------------------------------------------
# Stage 3: count frames per clip
# ----------------------------------------------------------------------------
SENTINEL_S3="${LRS3_PROCESSED}/nframes.video"
if [ ! -f "${SENTINEL_S3}" ]; then
  log_stage "3" "count_frames.py — per-clip frame counts"
  cd "${AVH}/avhubert/preparation"
  for rank in $(seq 0 $((NSHARD - 1))); do
    python count_frames.py \
      --root "${LRS3_PROCESSED}" \
      --manifest "${LRS3_RAW}/file.list" \
      --nshard "${NSHARD}" \
      --rank "${rank}"
  done
  # Merge shards
  for kind in audio video; do
    cat "${LRS3_PROCESSED}/nframes.${kind}".* > "${LRS3_PROCESSED}/nframes.${kind}"
  done
else
  log_info "Stage 3 already done (${SENTINEL_S3} present)"
fi

# ----------------------------------------------------------------------------
# Stage 4: lrs3_manifest.py — build initial TSVs + word dict
# ----------------------------------------------------------------------------
SENTINEL_S4="${LRS3_PROCESSED}/train.tsv"
if [ ! -f "${SENTINEL_S4}" ]; then
  log_stage "4" "lrs3_manifest.py — initial TSV/wrd manifests"
  cd "${AVH}/avhubert/preparation"
  python lrs3_manifest.py \
    --lrs3 "${LRS3_PROCESSED}" \
    --vocab-size "${N_CLUSTERS}"
  # AV-HuBERT writes TSVs into ${lrs3}/{30h,433h}/{train,valid,test}.tsv etc.
  # For paper-equivalent 433h, link the 433h split to top level.
  if [ -d "${LRS3_PROCESSED}/433h_data" ]; then
    cp "${LRS3_PROCESSED}/433h_data"/*.tsv "${LRS3_PROCESSED}/" 2>/dev/null || true
    cp "${LRS3_PROCESSED}/433h_data"/*.wrd "${LRS3_PROCESSED}/" 2>/dev/null || true
    cp "${LRS3_PROCESSED}/433h_data/dict.wrd.txt" "${LRS3_PROCESSED}/" 2>/dev/null || true
  fi
else
  log_info "Stage 4 already done (${SENTINEL_S4} present)"
fi

# ----------------------------------------------------------------------------
# Stage 5: AV-HuBERT layer-12 features for clustering
# ----------------------------------------------------------------------------
FEAT_DIR="${LRS3_PROCESSED}/features"
SENTINEL_S5="${FEAT_DIR}/train_0_${NSHARD}.npy"
if [ ! -f "${SENTINEL_S5}" ]; then
  log_stage "5" "dump_hubert_feature.py — layer-${FEAT_LAYER} visual features"
  mkdir -p "${FEAT_DIR}"
  cd "${VSP}/src/clustering"
  for rank in $(seq 0 $((NSHARD - 1))); do
    python dump_hubert_feature.py \
      "${LRS3_PROCESSED}" train "${AVH_CKPT}" "${FEAT_LAYER}" "${NSHARD}" "${rank}" "${FEAT_DIR}"
    python dump_hubert_feature.py \
      "${LRS3_PROCESSED}" valid "${AVH_CKPT}" "${FEAT_LAYER}" "${NSHARD}" "${rank}" "${FEAT_DIR}"
  done
else
  log_info "Stage 5 already done (${SENTINEL_S5} present)"
fi

# ----------------------------------------------------------------------------
# Stage 6: K-means (skip if pre-trained centroids are available in golden_kmeans/)
# ----------------------------------------------------------------------------
GOLDEN_KMEANS="${HOME}/golden_weights/golden_kmeans_200.bin"
if [ -f "${GOLDEN_KMEANS}" ] && [ ! -f "${KMEANS_BIN}" ]; then
  log_stage "6" "Reusing pre-trained k-means centroids from ${GOLDEN_KMEANS}"
  cp "${GOLDEN_KMEANS}" "${KMEANS_BIN}"
elif [ ! -f "${KMEANS_BIN}" ]; then
  log_stage "6" "learn_kmeans.py — training ${N_CLUSTERS}-cluster k-means on 10% LRS3-train"
  cd "${VSP}/src/clustering"
  python learn_kmeans.py \
    "${FEAT_DIR}" train "${NSHARD}" "${KMEANS_BIN}" "${N_CLUSTERS}" --percent 0.1
else
  log_info "Stage 6 already done (${KMEANS_BIN} present)"
fi

# ----------------------------------------------------------------------------
# Stage 7: per-frame cluster labels + cluster_counts
# ----------------------------------------------------------------------------
LAB_DIR="${LRS3_PROCESSED}/labels"
SENTINEL_S7="${LRS3_PROCESSED}/train.cluster_counts"
if [ ! -f "${SENTINEL_S7}" ]; then
  log_stage "7" "dump_km_label.py + cluster_counts.py — frame-level cluster labels"
  mkdir -p "${LAB_DIR}"
  cd "${VSP}/src/clustering"
  for split in train valid; do
    for rank in $(seq 0 $((NSHARD - 1))); do
      python dump_km_label.py \
        "${FEAT_DIR}" "${split}" "${KMEANS_BIN}" "${NSHARD}" "${rank}" "${LAB_DIR}"
    done
    cat "${LAB_DIR}/${split}"_*.km > "${LAB_DIR}/${split}.km"
  done
  # cluster_counts: collapse runs of identical cluster ids per frame to a per-segment count vector
  python cluster_counts.py \
    --km-path "${LAB_DIR}" \
    --out-dir "${LRS3_PROCESSED}"
else
  log_info "Stage 7 already done (${SENTINEL_S7} present)"
fi

# ----------------------------------------------------------------------------
# Stage 8: stage final manifests for fairseq-hydra-train
# ----------------------------------------------------------------------------
log_stage "8" "Staging final manifests to ${VSP_TRAIN_DATA}"
for f in train.tsv train.wrd train.cluster_counts \
         valid.tsv valid.wrd valid.cluster_counts \
         dict.wrd.txt; do
  if [ -f "${LRS3_PROCESSED}/${f}" ]; then
    cp -f "${LRS3_PROCESSED}/${f}" "${VSP_TRAIN_DATA}/${f}"
  else
    log_error "Missing ${LRS3_PROCESSED}/${f} — prep is incomplete"
    exit 1
  fi
done

log_info "Done. Final fairseq training data at ${VSP_TRAIN_DATA}:"
ls -la "${VSP_TRAIN_DATA}"
log_info ""
log_info "Next: launch training via VSP-LLM/scripts/train.sh, e.g.:"
log_info "  DATA_PATH=${VSP_TRAIN_DATA} OUT_PATH=/home/ubuntu/lrs3_train_out \\"
log_info "    bash ${VSP}/scripts/train.sh \\"
log_info "      distributed_training.distributed_world_size=8 \\"
log_info "      distributed_training.nprocs_per_node=8 \\"
log_info "      optimization.update_freq=[8]"
