#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# AVSpeech Fine-Tuning Pipeline
# ==============================================================================
# End-to-end pipeline for fine-tuning VSP-LLM on AVSpeech-like data.
# Reuses all existing lib/ modules for stages 1-7 (preprocessing), then runs
# fairseq-hydra-train for fine-tuning.
#
# Usage:
#   ./run_avspeech_finetune_pipeline.sh /path/to/raw_videos_dir
#
# Environment variables:
#   TRAIN_OUTPUT    - Output dir for checkpoints (default: ~/VSP-LLM/finetune_output)
#   CONFIG_NAME     - Hydra config name (default: vsp-llm-avspeech-finetune)
#   NUM_GPUS        - Number of GPUs (default: 1, set to 8 for multi-GPU)
#   MAX_UPDATE      - Override max training steps (default: from config)
#   FREEZE_STEPS    - Override freeze_finetune_updates (default: from config)
#   SKIP_PREPROCESS - Set to 1 to skip stages 0-6 if data is already preprocessed
#   DRY_RUN         - Set to 1 to validate setup without running training
#
# Example (single GPU, full pipeline):
#   ./run_avspeech_finetune_pipeline.sh ~/vsp_input/avspeech_videos/
#
# Example (8 GPUs, skip preprocessing):
#   SKIP_PREPROCESS=1 NUM_GPUS=8 \
#     ./run_avspeech_finetune_pipeline.sh ~/vsp_input/avspeech_videos/
# ==============================================================================

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/raw_videos_dir"
  echo ""
  echo "  Fine-tunes VSP-LLM on provided video data using the existing pipeline"
  echo "  for preprocessing (stages 0-6) and fairseq-hydra-train for training."
  echo ""
  echo "Environment variables:"
  echo "  TRAIN_OUTPUT    Output dir for checkpoints (default: ~/VSP-LLM/finetune_output)"
  echo "  CONFIG_NAME     Hydra config name (default: vsp-llm-avspeech-finetune)"
  echo "  NUM_GPUS        Number of GPUs (default: 1)"
  echo "  SKIP_PREPROCESS Set to 1 to skip preprocessing if already done"
  echo "  DRY_RUN         Set to 1 for dry run (validate only)"
  exit 1
fi

RAW_DIR="$1"
RAW_DIR="$(printf '%s' "$RAW_DIR" | tr -d '\r\n')"
RAW_DIR="$(realpath "$RAW_DIR")"

########################
# GLOBAL CONFIG
########################

HOME_DIR="${HOME}"

AUTO_AVSR="${HOME_DIR}/auto_avsr"
VSP="${HOME_DIR}/VSP-LLM"
AVH="${HOME_DIR}/av_hubert"

DATA_NAME="flat"
LANG="en"
SEG_DURATION="${SEG_DURATION:-12}"

# Segmentation configuration (same defaults as inference pipeline)
SEGMENTATION_ENABLED="${SEGMENTATION_ENABLED:-1}"
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"
OVERLAP_DURATION="2.0"
MIN_SPLIT_DURATION="12.0"
export SEGMENTATION_ENABLED OVERLAP_ENABLED SEG_DURATION

# Training-specific configuration
TRAIN_OUTPUT="${TRAIN_OUTPUT:-${VSP}/finetune_output}"
CONFIG_NAME="${CONFIG_NAME:-vsp-llm-avspeech-finetune}"
NUM_GPUS="${NUM_GPUS:-1}"
MAX_UPDATE="${MAX_UPDATE:-}"
FREEZE_STEPS="${FREEZE_STEPS:-}"
SKIP_PREPROCESS="${SKIP_PREPROCESS:-0}"
DRY_RUN="${DRY_RUN:-0}"

# Paths (same as inference pipeline)
FLAT_VID_DIR="${AUTO_AVSR}/${DATA_NAME}"
WRD_DIR="${AUTO_AVSR}/${DATA_NAME}_wrd"
TXT_DIR="${AUTO_AVSR}/${DATA_NAME}_txt"
READY_DIR="${AUTO_AVSR}/preprocess_ready_${DATA_NAME}"

PREP_ROOT="${AUTO_AVSR}/preprocessed_flat_seg${SEG_DURATION}"
MANIFEST_ROOT="${PREP_ROOT}/433h_data"

FEAT_DIR="${VSP}/${DATA_NAME}_features"
KM_PATH="${VSP}/${DATA_NAME}_kmeans_200.bin"
LAB_DIR="${VSP}/${DATA_NAME}_labels"
WRD_ROOT="${PREP_ROOT}/433h_data"

ASR_VENV="${AUTO_AVSR}/pre-process-venv"
PREP_VENV="${AUTO_AVSR}/pre-process-venv"
VSP_VENV="${HOME_DIR}/vsp-llm-yoad-venv"

# Checkpoints
LLM_PATH="${VSP}/checkpoints/Llama-2-7b-hf"
# Start from the already-trained checkpoint (transfer learning)
PRETRAINED_MODEL="${VSP}/checkpoints/checkpoint_finetune.pt"

# Source common utilities
source "${HOME}/lib/common.sh"

########################
# VALIDATE PREREQUISITES
########################

echo "=============================================="
echo "  AVSpeech Fine-Tuning Pipeline"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  Raw video dir:    $RAW_DIR"
echo "  Training output:  $TRAIN_OUTPUT"
echo "  Config name:      $CONFIG_NAME"
echo "  Num GPUs:         $NUM_GPUS"
echo "  Seg duration:     ${SEG_DURATION}s"
echo "  Skip preprocess:  $SKIP_PREPROCESS"
echo "  Dry run:          $DRY_RUN"
echo ""

# Validate input directory
validate_directory "$RAW_DIR" "Raw video input" || exit 1

# Count input videos
VIDEO_COUNT=$(find "$RAW_DIR" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.mkv" -o -iname "*.webm" -o -iname "*.mov" -o -iname "*.avi" \) 2>/dev/null | wc -l | tr -d ' ')
if [ "$VIDEO_COUNT" -eq 0 ]; then
  log_error "No video files found in $RAW_DIR"
  exit 1
fi
log_info "Found $VIDEO_COUNT video(s) in input directory"

# Validate critical paths
validate_directory "$VSP" "VSP-LLM" || exit 1
validate_directory "$LLM_PATH" "LLaMA-2-7B checkpoint" || exit 1
validate_file "$PRETRAINED_MODEL" "Pre-trained model checkpoint" || exit 1
validate_file "${VSP}/src/conf/${CONFIG_NAME}.yaml" "Training config" || exit 1
validate_directory "$VSP_VENV" "VSP virtual environment" || exit 1

if [ "$SKIP_PREPROCESS" = "0" ]; then
  validate_directory "$AUTO_AVSR" "auto_avsr" || exit 1
  validate_directory "$AVH" "av_hubert" || exit 1
  validate_directory "$ASR_VENV" "ASR virtual environment" || exit 1
fi

# Check GPU availability
if ! command -v nvidia-smi &>/dev/null; then
  log_error "nvidia-smi not found - GPU required for training"
  exit 1
fi

GPU_COUNT=$(nvidia-smi -L 2>/dev/null | wc -l | tr -d ' ')
log_info "Detected $GPU_COUNT GPU(s)"

if [ "$NUM_GPUS" -gt "$GPU_COUNT" ]; then
  log_error "Requested $NUM_GPUS GPUs but only $GPU_COUNT available"
  exit 1
fi

# Check disk space (need at least 20GB free)
FREE_GB=$(df -BG "$HOME_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
log_info "Free disk space: ${FREE_GB}GB"
if [ "$FREE_GB" -lt 20 ]; then
  log_warn "Low disk space (${FREE_GB}GB free). Training checkpoints are ~2GB each."
fi

echo ""

########################
# DRY RUN CHECK
########################

if [ "$DRY_RUN" = "1" ]; then
  echo "=============================================="
  echo "  DRY RUN - Validation Complete"
  echo "=============================================="
  echo ""
  echo "All prerequisites validated. Training would run with:"
  echo "  Config:           ${CONFIG_NAME}"
  echo "  Pretrained model: ${PRETRAINED_MODEL}"
  echo "  LLM checkpoint:   ${LLM_PATH}"
  echo "  GPUs:             ${NUM_GPUS}"
  echo "  Output:           ${TRAIN_OUTPUT}"
  if [ -n "$MAX_UPDATE" ]; then
    echo "  Max steps:        ${MAX_UPDATE} (override)"
  fi
  if [ -n "$FREEZE_STEPS" ]; then
    echo "  Freeze steps:     ${FREEZE_STEPS} (override)"
  fi
  echo ""
  echo "To run training, remove DRY_RUN=1"
  exit 0
fi

########################
# PREPROCESSING (STAGES 0-6)
########################

if [ "$SKIP_PREPROCESS" = "1" ]; then
  log_info "Skipping preprocessing (SKIP_PREPROCESS=1)"
  log_info "Expecting preprocessed data at: $MANIFEST_ROOT"

  # Validate that preprocessed data exists
  validate_file "$MANIFEST_ROOT/train.tsv" "Training manifest (train.tsv)" || {
    log_error "Preprocessed data not found. Run without SKIP_PREPROCESS first."
    exit 1
  }
  validate_file "$MANIFEST_ROOT/train.wrd" "Training labels (train.wrd)" || {
    log_error "Preprocessed data not found. Run without SKIP_PREPROCESS first."
    exit 1
  }
  validate_file "$LAB_DIR/train.cluster_counts" "Cluster counts" || {
    log_error "Preprocessed data not found. Run without SKIP_PREPROCESS first."
    exit 1
  }
else

  ########################
  # ARCHIVE PREVIOUS RUN
  ########################
  source "${HOME}/lib/archive.sh"

  ARCHIVE_ROOT=$(archive_previous_run "$HOME_DIR" "$SEG_DURATION" \
    "${WRD_DIR}" "${TXT_DIR}" "${READY_DIR}" "${FEAT_DIR}" "${LAB_DIR}")

  archive_prep_root "${PREP_ROOT}" "${ARCHIVE_ROOT}" "${SEG_DURATION}"
  echo

  ########################
  # CREATE FRESH OUTPUT DIRS
  ########################
  mkdir -p \
    "$FLAT_VID_DIR" "$WRD_DIR" "$TXT_DIR" "$READY_DIR" \
    "$MANIFEST_ROOT" "$FEAT_DIR" "$LAB_DIR"

  ############################################
  # STAGE 0.1: FAST SEGMENTATION
  ############################################
  FAST_SEG_DIR="${PREP_ROOT}/fast_segments"
  mkdir -p "${FAST_SEG_DIR}"

  if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    log_stage "0.1" "Fast Segmentation (${SEG_DURATION}s segments)"

    source "${PREP_VENV}/bin/activate"

    if [ "$OVERLAP_ENABLED" = "1" ]; then
      OVERLAP_ARG="--overlap ${OVERLAP_DURATION}"
    else
      OVERLAP_ARG="--overlap 0.0"
    fi

    python3 "${AUTO_AVSR}/preparation/fast_segment.py" \
      --data-dir "${RAW_DIR}" \
      --output-dir "${FAST_SEG_DIR}" \
      --seg-duration "${SEG_DURATION}" \
      ${OVERLAP_ARG} \
      --min-split-duration "${MIN_SPLIT_DURATION}"

    deactivate
    log_info "Fast segmentation complete: ${FAST_SEG_DIR}"
  else
    log_stage "0.1" "Whole Video Mode (copying as-is)"
    shopt -s nullglob
    for video_file in "${RAW_DIR}"/*.mp4 "${RAW_DIR}"/*.mkv "${RAW_DIR}"/*.webm "${RAW_DIR}"/*.mov "${RAW_DIR}"/*.avi "${RAW_DIR}"/*.m4v; do
      [ -f "$video_file" ] && cp "$video_file" "${FAST_SEG_DIR}/"
    done
    shopt -u nullglob
    log_info "Copied videos to ${FAST_SEG_DIR}"
  fi

  echo

  ############################################
  # STAGE 0.5: NORMALIZE SEGMENTS
  ############################################
  source "${HOME}/lib/normalization.sh"

  SKIP_NORM="${SKIP_NORM:-0}"
  MAX_DIM="${MAX_DIM:-0}"
  FPS_OUT="${FPS_OUT:-25}"
  USE_GPU_NORM="${USE_GPU_NORM:-0}"
  NORM_TIMEOUT_SEC="${NORM_TIMEOUT_SEC:-600}"

  log_stage "0.5" "Normalizing segments"

  PREP_DIR="${AUTO_AVSR}/${DATA_NAME}_prepared"

  run_normalization "$FAST_SEG_DIR" "$PREP_DIR" "$SKIP_NORM" "$MAX_DIM" "$FPS_OUT" "$USE_GPU_NORM" "$NORM_TIMEOUT_SEC" || {
    log_error "Video normalization failed"
    exit 3
  }

  rm -rf "$FLAT_VID_DIR"
  mkdir -p "$FLAT_VID_DIR"
  cp -a "${PREP_DIR}/." "${FLAT_VID_DIR}/"
  log_info "Normalized segments in: ${FLAT_VID_DIR}"

  echo

  ########################
  # STAGE 1: DIRECTORY STRUCTURE
  ########################
  log_stage "1" "Preparing directory structure"
  mkdir -p "$READY_DIR"
  cp -a "$FLAT_VID_DIR"/*.mp4 "$READY_DIR/" 2>/dev/null || true
  log_info "Videos copied to $READY_DIR"

  echo

  ########################
  # STAGE 2: MOUTH CROPPING
  ########################
  DISABLE_SEG_FLAG="--disable-segmentation"

  if [ "$SEGMENTATION_ENABLED" = "1" ] && [ "$OVERLAP_ENABLED" = "1" ]; then
    log_stage "2" "Mouth cropping (mediapipe, overlap mode)"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python3 preprocess_with_overlap.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration "$SEG_DURATION" \
      --overlap-duration "$OVERLAP_DURATION" \
      --min-split-duration "$MIN_SPLIT_DURATION" \
      --groups 1 \
      --job-index 0 \
      $DISABLE_SEG_FLAG

    deactivate
  else
    log_stage "2" "Mouth cropping (mediapipe)"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python3 preprocess_lrs2lrs3.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration "$SEG_DURATION" \
      --groups 1 \
      --job-index 0 \
      $DISABLE_SEG_FLAG

    deactivate
  fi

  log_info "Mouth cropping complete"
  echo

  ########################
  # STAGE 3: ASR TRANSCRIPTION
  ########################
  source "${HOME}/lib/asr.sh"

  if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    DIR_SUFFIX="seg${SEG_DURATION}s"
  else
    DIR_SUFFIX="whole"
  fi

  run_asr_transcription "$PREP_ROOT" "$ASR_VENV" "$AUTO_AVSR" "$DATA_NAME" \
    "$SEGMENTATION_ENABLED" "$SEG_DURATION" "$HOME" || {
    log_error "ASR transcription failed"
    exit 4
  }

  echo

  ########################
  # STAGE 4: LRS3 FORMAT CONVERSION
  ########################
  source "${HOME}/lib/lrs3_prep.sh"

  run_lrs3_preparation "$PREP_ROOT" "$AVH" "$SEG_DURATION" "$DIR_SUFFIX" || {
    log_error "LRS3 preparation failed"
    exit 5
  }

  ########################
  # STAGE 5: MANIFESTS + SPLITS
  ########################
  source "${HOME}/lib/manifests.sh"

  source "$VSP_VENV/bin/activate"

  run_manifest_generation "$PREP_ROOT" "$MANIFEST_ROOT" "$AUTO_AVSR" "$AVH" "$VSP" \
    "$SEGMENTATION_ENABLED" "$OVERLAP_ENABLED" || {
    deactivate
    log_error "Manifest generation failed"
    exit 6
  }

  ########################
  # STAGE 6: K-MEANS CLUSTERING
  ########################
  source "${HOME}/lib/clustering.sh"

  run_clustering "$PREP_ROOT" "$FEAT_DIR" "$KM_PATH" "$LAB_DIR" "$AVH" "$VSP" "${TRAIN_KMEANS:-1}" || {
    deactivate
    log_error "K-means clustering failed"
    exit 7
  }

  deactivate

fi  # end SKIP_PREPROCESS

########################
# STAGE 7: FINE-TUNING
########################

log_stage "7" "Fine-tuning VSP-LLM (fairseq-hydra-train)"

source "$VSP_VENV/bin/activate"
cd "$VSP"

# Check and build fairseq Cython extensions if needed
log_info "Checking fairseq Cython extensions"
if ! python3 -c "from fairseq.data.data_utils_fast import batch_by_size_vec" 2>/dev/null; then
  log_info "Building fairseq Cython extensions (one-time setup)"
  cd "$VSP/fairseq"
  python3 setup.py build_ext --inplace || {
    log_error "Failed to build fairseq Cython extensions"
    deactivate
    exit 8
  }
  log_info "Fairseq Cython extensions built"
  cd "$VSP"
else
  log_info "Fairseq Cython extensions already present"
fi

# Create output directory
mkdir -p "$TRAIN_OUTPUT"

# Build training data symlinks (fairseq expects data and label_dir)
TRAIN_DATA_DIR="${VSP}/src/dataset/finetune_data"
mkdir -p "$TRAIN_DATA_DIR"

ln -sf "$MANIFEST_ROOT/train.tsv" "$TRAIN_DATA_DIR/train.tsv"
ln -sf "$MANIFEST_ROOT/train.wrd" "$TRAIN_DATA_DIR/train.wrd"
ln -sf "$LAB_DIR/train.km" "$TRAIN_DATA_DIR/train.km" 2>/dev/null || true
ln -sf "$LAB_DIR/train.cluster_counts" "$TRAIN_DATA_DIR/train.cluster_counts"

# Use the same data for validation (monitor training progress)
ln -sf "$TRAIN_DATA_DIR/train.tsv" "$TRAIN_DATA_DIR/test.tsv"
ln -sf "$TRAIN_DATA_DIR/train.wrd" "$TRAIN_DATA_DIR/test.wrd"
ln -sf "$TRAIN_DATA_DIR/train.cluster_counts" "$TRAIN_DATA_DIR/test.cluster_counts"

log_info "Training data symlinks created at: $TRAIN_DATA_DIR"

# Count training samples
TRAIN_SAMPLES=$(($(wc -l < "$MANIFEST_ROOT/train.tsv") - 1))
log_info "Training samples: $TRAIN_SAMPLES"

# Build the fairseq-hydra-train command
SRC="${VSP}/src"

# Determine update_freq based on GPU count
if [ "$NUM_GPUS" -gt 1 ]; then
  UPDATE_FREQ=1
else
  UPDATE_FREQ=8
fi

echo ""
echo "Training configuration:"
echo "  Config:              $CONFIG_NAME"
echo "  Pretrained model:    $PRETRAINED_MODEL"
echo "  LLM checkpoint:     $LLM_PATH"
echo "  Training data:      $TRAIN_DATA_DIR"
echo "  Training samples:   $TRAIN_SAMPLES"
echo "  GPUs:               $NUM_GPUS"
echo "  Update freq:        $UPDATE_FREQ (effective batch = $((NUM_GPUS * UPDATE_FREQ)))"
echo "  Output:             $TRAIN_OUTPUT"
echo ""

# Build override arguments
OVERRIDES=(
  "common.user_dir=${SRC}"
  "task.data=${TRAIN_DATA_DIR}"
  "task.label_dir=${TRAIN_DATA_DIR}"
  "task.llm_ckpt_path=${LLM_PATH}"
  "model.w2v_path=${PRETRAINED_MODEL}"
  "model.llm_ckpt_path=${LLM_PATH}"
  "hydra.run.dir=${TRAIN_OUTPUT}"
  "distributed_training.distributed_world_size=${NUM_GPUS}"
  "distributed_training.nprocs_per_node=${NUM_GPUS}"
  "optimization.update_freq=[${UPDATE_FREQ}]"
)

# Apply optional overrides
if [ -n "$MAX_UPDATE" ]; then
  OVERRIDES+=("optimization.max_update=${MAX_UPDATE}")
  log_info "Overriding max_update to $MAX_UPDATE"
fi

if [ -n "$FREEZE_STEPS" ]; then
  OVERRIDES+=("model.freeze_finetune_updates=${FREEZE_STEPS}")
  log_info "Overriding freeze_finetune_updates to $FREEZE_STEPS"
fi

# Set PYTHONPATH for fairseq
export PYTHONPATH="${VSP}/fairseq:${PYTHONPATH:-}"

# Log the command for reproducibility
TRAIN_CMD="fairseq-hydra-train --config-dir ${SRC}/conf --config-name ${CONFIG_NAME}"
for ovr in "${OVERRIDES[@]}"; do
  TRAIN_CMD="$TRAIN_CMD $ovr"
done

log_info "Training command:"
echo "  $TRAIN_CMD"
echo ""

# Save command to output dir for reproducibility
echo "$TRAIN_CMD" > "$TRAIN_OUTPUT/train_command.txt"
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$TRAIN_OUTPUT/train_command.txt"
echo "Input dir: $RAW_DIR" >> "$TRAIN_OUTPUT/train_command.txt"
echo "Video count: $VIDEO_COUNT" >> "$TRAIN_OUTPUT/train_command.txt"
echo "Training samples: $TRAIN_SAMPLES" >> "$TRAIN_OUTPUT/train_command.txt"

log_info "Starting fine-tuning... (this will take hours)"
log_info "Monitor with: tail -f $TRAIN_OUTPUT/train.log"
log_info "GPU usage: watch nvidia-smi"
echo ""

# Run training
fairseq-hydra-train \
  --config-dir "${SRC}/conf" \
  --config-name "${CONFIG_NAME}" \
  "${OVERRIDES[@]}" \
  2>&1 | tee "$TRAIN_OUTPUT/train.log" || {
  log_error "Training failed. Check log: $TRAIN_OUTPUT/train.log"
  deactivate
  exit 8
}

deactivate

########################
# TRAINING COMPLETE
########################

echo ""
echo "=============================================="
echo "  Fine-Tuning Complete!"
echo "=============================================="
echo ""
echo "Outputs:"
echo "  Checkpoints:     $TRAIN_OUTPUT/"
echo "  Training log:    $TRAIN_OUTPUT/train.log"
echo "  Tensorboard:     $TRAIN_OUTPUT/tblog/"
echo ""
echo "Next steps:"
echo "  1. Evaluate: Run inference pipeline with the new checkpoint:"
echo "       # In run_flat_english_pipeline.sh or decode config, point to:"
echo "       #   model.w2v_path=$TRAIN_OUTPUT/checkpoint_best.pt"
echo ""
echo "  2. Compare: Decode english_1k with new vs old checkpoint to measure WER delta"
echo ""
echo "  3. (Optional) Re-cluster: If encoder was unfrozen, k-means features changed."
echo "     Re-extract features and re-train k-means with the fine-tuned encoder:"
echo "       # Extract features with fine-tuned model, then re-run clustering"
echo ""
echo "  Training command saved to: $TRAIN_OUTPUT/train_command.txt"
