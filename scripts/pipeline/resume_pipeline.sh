#!/usr/bin/env bash
set -euo pipefail

# Resume pipeline from Step 1 (after normalization completed successfully)
# Normalization completed all 1520 segments, but rm -rf failed on flat dir
# We've manually fixed the flat dir copy, so we pick up from Step 1

HOME_DIR="${HOME}"
AUTO_AVSR="${HOME_DIR}/auto_avsr"
VSP="${HOME_DIR}/VSP-LLM"
AVH="${HOME_DIR}/av_hubert"
DATA_NAME="flat"
LANG="en"
SEG_DURATION="${SEG_DURATION:-12}"
SEGMENTATION_ENABLED="${SEGMENTATION_ENABLED:-1}"
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"
OVERLAP_DURATION="2.0"
MIN_SPLIT_DURATION="12.0"
export SEGMENTATION_ENABLED OVERLAP_ENABLED SEG_DURATION

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
DECODE_ROOT="${VSP}/decode"
ASR_VENV="${AUTO_AVSR}/pre-process-venv"
PREP_VENV="${AUTO_AVSR}/pre-process-venv"
VSP_VENV="${HOME_DIR}/vsp-llm-yoad-venv"

# Use the archive root from the original run
ARCHIVE_ROOT="${HOME_DIR}/flat_runs_archive/20260217_013839"

echo ">>> RESUMING PIPELINE from Step 1"
echo ">>> Archive root: $ARCHIVE_ROOT"
echo ">>> FLAT_VID_DIR: $FLAT_VID_DIR ($(ls "$FLAT_VID_DIR"/*.mp4 | wc -l) files)"
echo

# Ensure output dirs exist
mkdir -p "$WRD_DIR" "$TXT_DIR" "$READY_DIR" "$MANIFEST_ROOT" "$FEAT_DIR" "$LAB_DIR"

echo ">>> [0.5] FLAT_VID_DIR mp4 count:"
find "$FLAT_VID_DIR" -maxdepth 1 -type f -iname "*.mp4" | wc -l
echo

########################
# STEP 1: Prepare directories
########################
echo ">>> [1] Preparing directory structure for preprocessing"
mkdir -p "$READY_DIR"
cp -a "$FLAT_VID_DIR"/*.mp4 "$READY_DIR/" 2>/dev/null || true
echo ">>> [1] Videos copied to $READY_DIR"
echo

########################
# STEP 2: Mouth cropping
########################
DISABLE_SEG_FLAG="--disable-segmentation"

if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    SEG_MODE_MSG="pre-segmented (${SEG_DURATION}s segments, normalized)"
    DIR_SUFFIX="seg${SEG_DURATION}s"
else
    SEG_MODE_MSG="whole videos (normalized, no segmentation)"
    DIR_SUFFIX="whole"
fi

if [ "$SEGMENTATION_ENABLED" = "1" ] && [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [2] Running preprocess_with_overlap.py (mediapipe, ${SEG_MODE_MSG})"
    echo ">>> [2] Processing pre-segmented, normalized videos (face detection + mouth cropping only)"

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
    echo ">>> [INFO] Mouth-cropped segments in: $PREP_ROOT"
else
    echo ">>> [2] Running preprocess_lrs2lrs3.py (mediapipe, ${SEG_MODE_MSG})"
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
    echo ">>> [INFO] Mouth-cropped videos in: $PREP_ROOT"
fi

echo

########################
# STEP 3: ASR
########################
source "${HOME}/lib/asr.sh"

if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    DIR_SUFFIX="seg${SEG_DURATION}s"
else
    DIR_SUFFIX="whole"
fi

run_asr_transcription "$PREP_ROOT" "$ASR_VENV" "$AUTO_AVSR" "$DATA_NAME" \
  "$SEGMENTATION_ENABLED" "$SEG_DURATION" "$HOME" || {
  echo "ERROR: ASR transcription failed" >&2
  exit 4
}

SEGMENT_VID_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_video_${DIR_SUFFIX}"
SEGMENT_TXT_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_text_${DIR_SUFFIX}"
echo

########################
# STEP 4: LRS3 preparation
########################
source "${HOME}/lib/lrs3_prep.sh"

run_lrs3_preparation "$PREP_ROOT" "$AVH" "$SEG_DURATION" "$DIR_SUFFIX" || {
  echo "ERROR: LRS3 preparation failed" >&2
  exit 5
}

########################
# STEP 5: Manifests
########################
source "${HOME}/lib/manifests.sh"

source "$VSP_VENV/bin/activate"

run_manifest_generation "$PREP_ROOT" "$MANIFEST_ROOT" "$AUTO_AVSR" "$AVH" "$VSP" \
  "$SEGMENTATION_ENABLED" "$OVERLAP_ENABLED" || {
  deactivate
  echo "ERROR: Manifest generation failed" >&2
  exit 6
}

########################
# STEP 6: K-means
########################
source "${HOME}/lib/clustering.sh"

run_clustering "$PREP_ROOT" "$FEAT_DIR" "$KM_PATH" "$LAB_DIR" "$AVH" "$VSP" "${TRAIN_KMEANS:-1}" || {
  deactivate
  echo "ERROR: K-means clustering failed" >&2
  exit 7
}

deactivate

########################
# STEP 7: Decode
########################
source "${HOME}/lib/decode.sh"

source "$VSP_VENV/bin/activate"
cd "$VSP"

run_vsp_decode "$VSP" "$MANIFEST_ROOT" "$LAB_DIR" "$WRD_ROOT" "$PREP_ROOT" \
  "$SEGMENTATION_ENABLED" "$OVERLAP_ENABLED" || {
  deactivate
  echo "ERROR: VSP-LLM decode failed" >&2
  exit 8
}

########################
# STEP 8: Client outputs
########################
source "${HOME}/lib/outputs.sh"

run_client_outputs "$VSP" "$ARCHIVE_ROOT" "$FLAT_VID_DIR" "$PREP_ROOT" \
  "$DATA_NAME" "$DIR_SUFFIX" || {
  deactivate
  echo "ERROR: Client outputs generation failed" >&2
  exit 9
}

deactivate

POST_ROOT="$ARCHIVE_ROOT/client_outputs"

echo
echo ">>> Pipeline complete!"
echo "    - Mouth crops: $PREP_ROOT"
echo "    - TSVs: $MANIFEST_ROOT"
echo "    - Labels: $LAB_DIR"
echo "    - K-means: $KM_PATH"
echo "    - Outputs: $POST_ROOT"
