#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/raw_videos_dir"
  exit 1
fi

RAW_DIR="$1"
RAW_DIR="$(printf '%s' "$RAW_DIR" | tr -d '\r\n')"
RAW_DIR="$(realpath "$RAW_DIR")"

########################
# GLOBAL CONFIG
########################

# Auto-detect installation directory from script location
# Works regardless of where galaxy_export is installed (/home/ubuntu, /workspace, /host, etc.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"

AUTO_AVSR="${BASE_DIR}/auto_avsr"
VSP="${BASE_DIR}/VSP-LLM"
AVH="${BASE_DIR}/av_hubert"

DATA_NAME="flat"
LANG="en"
SEG_DURATION="${SEG_DURATION:-12}"  # Segment duration in seconds (default 12s for optimal context)

# Segmentation configuration
SEGMENTATION_ENABLED="${SEGMENTATION_ENABLED:-1}"  # Default: enabled (1=segment videos, 0=process whole videos)
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"  # Default: enabled (only used if SEGMENTATION_ENABLED=1)
OVERLAP_DURATION="2.0"  # 2 seconds to prevent word boundary splits (only used if SEGMENTATION_ENABLED=1)
MIN_SPLIT_DURATION="12.0"  # Split videos 12s and longer (allows 2s overlap)
export SEGMENTATION_ENABLED OVERLAP_ENABLED SEG_DURATION

# Preprocessing-only mode (stop after segmentation for manual transcription)
PREPROCESS_ONLY="${PREPROCESS_ONLY:-0}"  # Set to 1 to stop after Step 2


FLAT_VID_DIR="${AUTO_AVSR}/${DATA_NAME}"
WRD_DIR="${AUTO_AVSR}/${DATA_NAME}_wrd"
TXT_DIR="${AUTO_AVSR}/${DATA_NAME}_txt"
READY_DIR="${AUTO_AVSR}/preprocess_ready_${DATA_NAME}"

# Use dynamic segment duration in path
PREP_ROOT="${AUTO_AVSR}/preprocessed_flat_seg${SEG_DURATION}"
MANIFEST_ROOT="${PREP_ROOT}/433h_data"

FEAT_DIR="${VSP}/${DATA_NAME}_features"
KM_PATH="${VSP}/${DATA_NAME}_kmeans_200.bin"
LAB_DIR="${VSP}/${DATA_NAME}_labels"
WRD_ROOT="${PREP_ROOT}/433h_data"
DECODE_ROOT="${VSP}/decode"

# CONTAINER VERSION: Hardcoded /workspace paths for standalone Linux container
# - galaxy_export code at: /host/galaxy_export
# - venvs at: /workspace/...
ASR_VENV="/workspace/auto_avsr/pre-process-venv"
PREP_VENV="/workspace/auto_avsr/pre-process-venv"
VSP_VENV="/workspace/vsp-llm-yoad-venv"

########################
# ARCHIVE PREVIOUS RUN
########################
# Load archive module
source "${SCRIPT_DIR}/lib/archive.sh"

# Archive standard directories
ARCHIVE_ROOT=$(archive_previous_run "$BASE_DIR" "$SEG_DURATION" \
  "${WRD_DIR}" "${TXT_DIR}" "${READY_DIR}" "${FEAT_DIR}" "${LAB_DIR}")

# Archive PREP_ROOT with special handling for segment transcriptions
archive_prep_root "${PREP_ROOT}" "${ARCHIVE_ROOT}" "${SEG_DURATION}"

echo

########################
# CREATE FRESH OUTPUT DIRS
########################
mkdir -p \
  "$FLAT_VID_DIR" "$WRD_DIR" "$TXT_DIR" "$READY_DIR" \
  "$MANIFEST_ROOT" "$FEAT_DIR" "$LAB_DIR"

############################################
# STEP 0.1: FAST SEGMENTATION (always run for efficiency)
############################################
# Segment raw videos FIRST, then normalize segments (not whole videos)
# This is much more efficient for long videos

SEGMENT_ONLY="${SEGMENT_ONLY:-0}"
FAST_SEG_DIR="${PREP_ROOT}/fast_segments"
mkdir -p "${FAST_SEG_DIR}"

if [ "$SEGMENTATION_ENABLED" = "1" ]; then
  echo ">>> [0.1] Fast Segmentation (splitting videos into ${SEG_DURATION}s segments)"
  echo ">>> [0.1] This creates raw segments before normalization (efficient for long videos)"

  source "${PREP_VENV}/bin/activate"

  # Determine overlap settings
  if [ "$OVERLAP_ENABLED" = "1" ]; then
    OVERLAP_ARG="--overlap ${OVERLAP_DURATION}"
    echo ">>> [0.1] Using ${OVERLAP_DURATION}s overlap for videos >${MIN_SPLIT_DURATION}s"
  else
    OVERLAP_ARG="--overlap 0.0"
    echo ">>> [0.1] Overlap disabled (no overlap between segments)"
  fi

  python3 "${AUTO_AVSR}/preparation/fast_segment.py" \
    --data-dir "${RAW_DIR}" \
    --output-dir "${FAST_SEG_DIR}" \
    --seg-duration "${SEG_DURATION}" \
    ${OVERLAP_ARG} \
    --min-split-duration "${MIN_SPLIT_DURATION}"

  deactivate

  echo
  echo ">>> [0.1] Fast segmentation complete!"
  echo ">>> [0.1] Segments saved to: ${FAST_SEG_DIR}"
  echo ">>> [0.1] Metadata: ${FAST_SEG_DIR}/segment_metadata.json"
else
  echo ">>> [0.1] Whole Video Mode (segmentation disabled)"
  echo ">>> [0.1] Copying videos as-is"

  # Copy whole videos to fast_segments
  copied_count=0
  shopt -s nullglob  # Avoid literal glob patterns if no files match
  for video_file in "${RAW_DIR}"/*.mp4 "${RAW_DIR}"/*.mkv "${RAW_DIR}"/*.webm "${RAW_DIR}"/*.mov "${RAW_DIR}"/*.avi "${RAW_DIR}"/*.m4v; do
    if [ -f "$video_file" ]; then
      video_name=$(basename "$video_file")
      # Keep original name (no segment suffix for whole videos)
      output_name="${video_name}"

      # Copy to fast_segments
      cp "$video_file" "${FAST_SEG_DIR}/${output_name}"

      copied_count=$((copied_count + 1))
      echo "  ✓ Copied: $video_name (whole video)"
    fi
  done
  shopt -u nullglob

  # Create proper segment metadata for whole videos
  echo "{" > "${FAST_SEG_DIR}/segment_metadata.json"
  first_video=true
  shopt -s nullglob
  for video_file in "$RAW_DIR"/*.{mp4,mkv,avi,mov,webm,MP4,MKV,AVI,MOV,WEBM}; do
    if [ -f "$video_file" ]; then
      video_name=$(basename "$video_file")
      video_id="${video_name%.*}"

      # Get video duration
      duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video_file" 2>/dev/null || echo "0")

      # Get frame count (at 25fps)
      frame_count=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$video_file" 2>/dev/null || echo "0")
      if [ "$frame_count" = "0" ]; then
        # Estimate from duration if frame count unavailable
        frame_count=$(echo "$duration * 25" | bc -l | cut -d. -f1)
      fi

      # Add comma before entry (except for first)
      if [ "$first_video" = false ]; then
        echo "," >> "${FAST_SEG_DIR}/segment_metadata.json"
      fi
      first_video=false

      # Write video metadata entry
      cat >> "${FAST_SEG_DIR}/segment_metadata.json" <<EOF
  "$video_id": {
    "original_duration": $duration,
    "segment_duration": $duration,
    "overlap_duration": 0,
    "num_segments": 1,
    "segments": [
      {
        "index": 0,
        "start_frame": 0,
        "end_frame": $frame_count,
        "start_sec": 0.0,
        "end_sec": $duration,
        "duration": $duration
      }
    ]
  }
EOF
    fi
  done
  shopt -u nullglob
  echo "}" >> "${FAST_SEG_DIR}/segment_metadata.json"

  echo
  echo ">>> [0.1] Copied $copied_count whole video(s)"
  echo ">>> [0.1] Videos saved to: ${FAST_SEG_DIR}"
fi

echo

# If SEGMENT_ONLY mode, stop here for transcription review
if [ "$SEGMENT_ONLY" = "1" ]; then
  echo ">>> [INFO] SEGMENT_ONLY mode - stopping for transcription review"
  echo ">>> [INFO] Next steps:"
  echo "    1. Review/transcribe videos in the UI"
  echo "    2. Continue pipeline for full processing:"
  echo "       - Video normalization on segments (efficient!)"
  echo "       - Face detection & mouth cropping"
  echo "       - ASR (auto-transcription for remaining videos)"
  echo "       - K-means clustering & VSP-LLM decoding"
  echo
  exit 0
fi

############################################
# STEP 0.5: Normalize segments -> FLAT_VID_DIR
############################################
# Load normalization module
source "${SCRIPT_DIR}/lib/normalization.sh"

# Configuration variables with defaults
SKIP_NORM="${SKIP_NORM:-0}"
MAX_DIM="${MAX_DIM:-0}"  # 0 = keep original resolution, or set to 720/1080/etc to limit
FPS_OUT="${FPS_OUT:-25}"
USE_GPU_NORM="${USE_GPU_NORM:-0}"
NORM_TIMEOUT_SEC="${NORM_TIMEOUT_SEC:-600}"

echo ">>> [0.5] Normalizing segments (SKIP_NORM=${SKIP_NORM}, USE_GPU_NORM=${USE_GPU_NORM}, MAX_DIM=${MAX_DIM}, FPS=${FPS_OUT}, TIMEOUT=${NORM_TIMEOUT_SEC}s)"
echo ">>> [0.5] Input: ${FAST_SEG_DIR} (pre-segmented videos)"

# Prepare output directory
PREP_DIR="${AUTO_AVSR}/${DATA_NAME}_prepared"

# Run normalization on SEGMENTS (not raw videos!)
# This is much more efficient for long videos
run_normalization "$FAST_SEG_DIR" "$PREP_DIR" "$SKIP_NORM" "$MAX_DIM" "$FPS_OUT" "$USE_GPU_NORM" "$NORM_TIMEOUT_SEC" || {
  echo "ERROR: Video normalization failed" >&2
  exit 3
}

# IMPORTANT: wipe FLAT_VID_DIR so Whisper does NOT see leftovers
echo ">>> [0.5] Resetting FLAT_VID_DIR and copying normalized segments -> ${FLAT_VID_DIR}"
rm -rf "$FLAT_VID_DIR"
mkdir -p "$FLAT_VID_DIR"
cp -a "${PREP_DIR}/." "${FLAT_VID_DIR}/"

echo ">>> [0.5] FLAT_VID_DIR mp4 count:"
find "$FLAT_VID_DIR" -maxdepth 1 -type f -iname "*.mp4" | wc -l
echo

########################
# STEP 1: Preprocessing/Segmentation (MOVED BEFORE ASR)
########################
echo ">>> [1] Preparing directory structure for preprocessing"

# Create preprocess_ready structure WITHOUT transcriptions yet
mkdir -p "$READY_DIR"
# Copy videos to preprocess_ready
cp -a "$FLAT_VID_DIR"/*.mp4 "$READY_DIR/" 2>/dev/null || true

echo ">>> [1] Videos copied to $READY_DIR"
echo

########################
# STEP 2: Mouth cropping (face detection + cropping)
########################
# NOTE: Videos are ALREADY segmented and normalized from Step 0.1 and 0.5
# Preprocessing now ONLY does face detection and mouth cropping (no segmentation!)

# Always disable segmentation since videos are already segmented
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
    echo ">>> [2] Processing normalized videos (face detection + mouth cropping only)"

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

########################
# STEP 2.5: Create segment_metadata.json for non-segmented videos
########################
if [ "$SEGMENTATION_ENABLED" = "0" ]; then
  echo ">>> [2.5] Creating segment_metadata.json for whole videos"

  # Create proper segment metadata at PREP_ROOT for make_burn.py
  echo "{" > "${PREP_ROOT}/segment_metadata.json"
  first_video=true
  shopt -s nullglob
  for video_file in "$FLAT_VID_DIR"/*.{mp4,mkv,avi,mov,webm,MP4,MKV,AVI,MOV,WEBM}; do
    if [ -f "$video_file" ]; then
      video_name=$(basename "$video_file")
      video_id="${video_name%.*}"

      # Get video duration
      duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video_file" 2>/dev/null || echo "0")

      # Get frame count (at 25fps)
      frame_count=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$video_file" 2>/dev/null || echo "0")
      if [ "$frame_count" = "0" ]; then
        # Estimate from duration if frame count unavailable
        frame_count=$(echo "$duration * 25" | bc -l | cut -d. -f1)
      fi

      # Add comma before entry (except for first)
      if [ "$first_video" = false ]; then
        echo "," >> "${PREP_ROOT}/segment_metadata.json"
      fi
      first_video=false

      # Write video metadata entry
      cat >> "${PREP_ROOT}/segment_metadata.json" <<EOF
  "$video_id": {
    "original_duration": $duration,
    "segment_duration": $duration,
    "overlap_duration": 0,
    "num_segments": 1,
    "segments": [
      {
        "index": 0,
        "start_frame": 0,
        "end_frame": $frame_count,
        "start_sec": 0.0,
        "end_sec": $duration,
        "duration": $duration
      }
    ]
  }
EOF
    fi
  done
  shopt -u nullglob
  echo "}" >> "${PREP_ROOT}/segment_metadata.json"

  echo ">>> [2.5] Metadata created at: ${PREP_ROOT}/segment_metadata.json"
fi

echo

########################
# Check for preprocessing-only mode
########################
if [ "$PREPROCESS_ONLY" = "1" ]; then
    echo ">>> [INFO] PREPROCESS_ONLY mode - stopping after segmentation"
    echo ">>> [INFO] Segmented videos are in: $PREP_ROOT/${DATA_NAME}/${DATA_NAME}_video_seg${SEG_DURATION}s"
    echo ">>> [INFO] To manually transcribe segments:"
    echo "    1. Create .txt files in: $PREP_ROOT/${DATA_NAME}/${DATA_NAME}_text_seg${SEG_DURATION}s/"
    echo "    2. Each file should contain one word per line (lowercase, alphanumeric only)"
    echo "    3. Run pipeline again with PREPROCESS_ONLY=0 to continue from ASR"
    echo "    Note: ASR will skip segments that already have .txt files"
    echo ""
    echo ">>> Pipeline preprocessing complete! (Manual transcription step)"
    exit 0
fi

########################
# STEP 3: ASR on segmented videos -> .txt files
########################
# Load ASR module
source "${SCRIPT_DIR}/lib/asr.sh"

# Determine directory suffix based on SEGMENTATION_ENABLED
if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    DIR_SUFFIX="seg${SEG_DURATION}s"
else
    DIR_SUFFIX="whole"
fi

# Run ASR transcription (includes Steps 0.6, 3, and 1.5)
run_asr_transcription "$PREP_ROOT" "$ASR_VENV" "$AUTO_AVSR" "$DATA_NAME" \
  "$SEGMENTATION_ENABLED" "$SEG_DURATION" "$RAW_DIR" || {
  echo "ERROR: ASR transcription failed" >&2
  exit 4
}

# Set output directories for next stages
SEGMENT_VID_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_video_${DIR_SUFFIX}"
SEGMENT_TXT_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_text_${DIR_SUFFIX}"

echo

########################
# STEP 4: flat_to_lrs3_preperation.sh
########################
# Load LRS3 preparation module
source "${SCRIPT_DIR}/lib/lrs3_prep.sh"

run_lrs3_preparation "$PREP_ROOT" "$AVH" "$SEG_DURATION" "$DIR_SUFFIX" || {
  echo "ERROR: LRS3 preparation failed" >&2
  exit 5
}

########################
# STEP 5: manifests + splits + train.tsv
########################
# Load manifest generation module
source "${SCRIPT_DIR}/lib/manifests.sh"

source "$VSP_VENV/bin/activate"

run_manifest_generation "$PREP_ROOT" "$MANIFEST_ROOT" "$AUTO_AVSR" "$AVH" "$VSP" \
  "$SEGMENTATION_ENABLED" "$OVERLAP_ENABLED" || {
  deactivate
  echo "ERROR: Manifest generation failed" >&2
  exit 6
}

#########################
# STEP 6: k-means + cluster counts
########################
# Load clustering module
source "${SCRIPT_DIR}/lib/clustering.sh"

run_clustering "$PREP_ROOT" "$FEAT_DIR" "$KM_PATH" "$LAB_DIR" "$AVH" "$VSP" "${TRAIN_KMEANS:-1}" || {
  deactivate
  echo "ERROR: K-means clustering failed" >&2
  exit 7
}

deactivate

#######################
# STEP 7: LLM decode
########################
# Load decode module
source "${SCRIPT_DIR}/lib/decode.sh"

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
# Load outputs module
source "${SCRIPT_DIR}/lib/outputs.sh"

run_client_outputs "$VSP" "$ARCHIVE_ROOT" "$FLAT_VID_DIR" "$PREP_ROOT" \
  "$DATA_NAME" "$DIR_SUFFIX" || {
  deactivate
  echo "ERROR: Client outputs generation failed" >&2
  exit 9
}

deactivate

# Set POST_ROOT for final summary
POST_ROOT="$ARCHIVE_ROOT/client_outputs"

echo
echo ">>> Pipeline complete!"
echo "    - Mouth crops: $PREP_ROOT"
echo "    - TSVs: $MANIFEST_ROOT"
echo "    - Labels: $LAB_DIR"
echo "    - Outputs: $POST_ROOT"