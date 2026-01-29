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

HOME_DIR="${HOME}"

AUTO_AVSR="${HOME_DIR}/auto_avsr"
VSP="${HOME_DIR}/VSP-LLM"
AVH="${HOME_DIR}/av_hubert"

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

ASR_VENV="${AUTO_AVSR}/pre-process-venv"
PREP_VENV="${AUTO_AVSR}/pre-process-venv"
VSP_VENV="${HOME_DIR}/vsp-llm-yoad-venv"

########################
# ARCHIVE PREVIOUS RUN
########################
# Load archive module
source "${HOME}/lib/archive.sh"

# Archive standard directories
ARCHIVE_ROOT=$(archive_previous_run "$HOME_DIR" "$SEG_DURATION" \
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
# STEP 0.1: FAST SEGMENTATION (if SEGMENT_ONLY=1)
############################################
SEGMENT_ONLY="${SEGMENT_ONLY:-0}"

if [ "$SEGMENT_ONLY" = "1" ]; then
  FAST_SEG_DIR="${PREP_ROOT}/fast_segments"
  mkdir -p "${FAST_SEG_DIR}"

  if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    echo ">>> [0.1] Fast Segmentation Mode (splitting videos)"
    echo ">>> [0.1] This creates raw segments quickly so users can start transcribing"

    source "${PREP_VENV}/bin/activate"

    # Determine overlap settings
    if [ "$OVERLAP_ENABLED" = "1" ]; then
      OVERLAP_ARG="--overlap ${OVERLAP_DURATION}"
      echo ">>> [0.1] Using ${OVERLAP_DURATION}s overlap for videos >${MIN_SPLIT_DURATION}s"
    else
      OVERLAP_ARG="--overlap 0.0"
      echo ">>> [0.1] Overlap disabled (no overlap between segments)"
    fi

    python "${AUTO_AVSR}/preparation/fast_segment.py" \
      --data-dir "${RAW_DIR}" \
      --output-dir "${FAST_SEG_DIR}" \
      --seg-duration "${SEG_DURATION}" \
      ${OVERLAP_ARG} \
      --min-split-duration "${MIN_SPLIT_DURATION}"

    echo
    echo ">>> [0.1] Fast segmentation complete!"
    echo ">>> [0.1] Segments saved to: ${FAST_SEG_DIR}"
    echo ">>> [0.1] Metadata: ${FAST_SEG_DIR}/segment_metadata.json"
  else
    echo ">>> [0.1] Whole Video Mode (segmentation disabled)"
    echo ">>> [0.1] Copying videos as-is for transcription review"

    # Also create the expected directory structure for when pipeline continues
    SEGMENT_VID_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_video_seg${SEG_DURATION}s"
    mkdir -p "${SEGMENT_VID_DIR}"

    # Copy whole videos to both locations
    # 1. fast_segments/ for UI review
    # 2. preprocessed directory for pipeline continuation
    copied_count=0
    shopt -s nullglob  # Avoid literal glob patterns if no files match
    for video_file in "${RAW_DIR}"/*.mp4 "${RAW_DIR}"/*.mkv "${RAW_DIR}"/*.webm "${RAW_DIR}"/*.mov "${RAW_DIR}"/*.avi "${RAW_DIR}"/*.m4v; do
      if [ -f "$video_file" ]; then
        video_name=$(basename "$video_file")
        video_id="${video_name%.*}"
        video_ext="${video_name##*.}"
        # Name as segment 0 with placeholder frame numbers, preserve extension
        output_name="${video_id}_00_000000_999999.${video_ext}"

        # Copy to fast_segments for UI review
        cp "$video_file" "${FAST_SEG_DIR}/${output_name}"

        # Also copy to preprocessed directory for pipeline continuation
        cp "$video_file" "${SEGMENT_VID_DIR}/${output_name}"

        copied_count=$((copied_count + 1))
        echo "  ✓ Copied: $video_name (whole video)"
      fi
    done
    shopt -u nullglob

    # Create minimal segment metadata for whole videos
    echo "{\"segments\": [], \"total_videos\": $copied_count, \"segmentation_enabled\": false}" > "${FAST_SEG_DIR}/segment_metadata.json"

    echo
    echo ">>> [0.1] Copied $copied_count whole video(s)"
    echo ">>> [0.1] Videos saved to: ${FAST_SEG_DIR}"
    echo ">>> [0.1] Also prepared in: ${SEGMENT_VID_DIR}"
  fi

  echo
  echo ">>> [INFO] SEGMENT_ONLY mode - stopping for transcription review"
  echo ">>> [INFO] Next steps:"
  echo "    1. Review/transcribe videos in the UI"
  echo "    2. Continue pipeline for full processing:"
  echo "       - Video normalization (HDR/10-bit conversion)"
  echo "       - Face detection & mouth cropping"
  echo "       - ASR (auto-transcription for remaining videos)"
  echo "       - K-means clustering & VSP-LLM decoding"
  echo
  exit 0
fi

############################################
# STEP 0.5: Prepare/Normalize raw videos -> FLAT_VID_DIR
############################################
# Load normalization module
source "${HOME}/lib/normalization.sh"

# Configuration variables with defaults
SKIP_NORM="${SKIP_NORM:-0}"
MAX_DIM="${MAX_DIM:-0}"  # 0 = keep original resolution, or set to 720/1080/etc to limit
FPS_OUT="${FPS_OUT:-25}"
USE_GPU_NORM="${USE_GPU_NORM:-1}"
NORM_TIMEOUT_SEC="${NORM_TIMEOUT_SEC:-600}"

echo ">>> [0.5] Preparing videos (SKIP_NORM=${SKIP_NORM}, USE_GPU_NORM=${USE_GPU_NORM}, MAX_DIM=${MAX_DIM}, FPS=${FPS_OUT}, TIMEOUT=${NORM_TIMEOUT_SEC}s)"

# Prepare output directory
PREP_DIR="${AUTO_AVSR}/${DATA_NAME}_prepared"

# Run normalization
run_normalization "$RAW_DIR" "$PREP_DIR" "$SKIP_NORM" "$MAX_DIM" "$FPS_OUT" "$USE_GPU_NORM" "$NORM_TIMEOUT_SEC" || {
  echo "ERROR: Video normalization failed" >&2
  exit 3
}

# IMPORTANT: wipe FLAT_VID_DIR so Whisper does NOT see leftovers
echo ">>> [0.5] Resetting FLAT_VID_DIR and copying prepared videos -> ${FLAT_VID_DIR}"
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
# STEP 2: Preprocessing with optional overlap/segmentation
########################
# Determine directory suffix and flags based on SEGMENTATION_ENABLED
if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    SEG_MODE_MSG="segmented (${SEG_DURATION}s segments)"
    DISABLE_SEG_FLAG=""
    DIR_SUFFIX="seg${SEG_DURATION}s"
else
    SEG_MODE_MSG="whole videos (no segmentation)"
    DISABLE_SEG_FLAG="--disable-segmentation"
    DIR_SUFFIX="whole"
fi

if [ "$SEGMENTATION_ENABLED" = "1" ] && [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [2] Running preprocess_with_overlap.py (mediapipe, ${SEG_MODE_MSG}, overlap=${OVERLAP_DURATION}s)"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python preprocess_with_overlap.py \
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
    echo ">>> [INFO] Overlapping segments + metadata in: $PREP_ROOT"
else
    echo ">>> [2] Running preprocess_lrs2lrs3.py (mediapipe, ${SEG_MODE_MSG})"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python preprocess_lrs2lrs3.py \
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
    echo ">>> [INFO] Standard mouth crops in: $PREP_ROOT"
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
echo ">>> [3] Running ASR on videos"

# Determine directory suffix based on SEGMENTATION_ENABLED
if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    DIR_SUFFIX="seg${SEG_DURATION}s"
else
    DIR_SUFFIX="whole"
fi

# Get the video directory (segmented or whole)
SEGMENT_VID_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_video_${DIR_SUFFIX}"
SEGMENT_TXT_DIR="$PREP_ROOT/${DATA_NAME}/${DATA_NAME}_text_${DIR_SUFFIX}"

if [ ! -d "$SEGMENT_VID_DIR" ]; then
    echo "ERROR: Segmented video directory not found: $SEGMENT_VID_DIR" >&2
    exit 4
fi

# Create temp directory for ASR output (.wrd format)
SEGMENT_WRD_TMP="${PREP_ROOT}/segment_wrd_tmp"
mkdir -p "$SEGMENT_WRD_TMP"

########################
# STEP 0.6: Copy existing transcriptions from .transcriptions/ to working directory
########################
echo ">>> [0.6] Checking for existing manual transcriptions"
TRANSCRIPTIONS_DIR="$HOME/vsp_input/.transcriptions"

if [ -d "$TRANSCRIPTIONS_DIR" ]; then
  copied_count=0
  for wrd_file in "$TRANSCRIPTIONS_DIR"/*.wrd; do
    if [ -f "$wrd_file" ]; then
      filename=$(basename "$wrd_file")
      # Check if this is a segment transcription (has frame numbers in name)
      if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
        cp "$wrd_file" "$SEGMENT_WRD_TMP/"
        copied_count=$((copied_count + 1))
        echo ">>> [0.6]   Copied manual transcription: $filename"
      fi
    fi
  done

  if [ $copied_count -gt 0 ]; then
    echo ">>> [0.6] Copied $copied_count existing transcription(s) - Whisper will skip these segments"
  else
    echo ">>> [0.6] No existing segment transcriptions found"
  fi
else
  echo ">>> [0.6] No .transcriptions directory found (first run)"
fi

echo ">>> [3] Running Whisper on segmented videos from: $SEGMENT_VID_DIR"
source "$ASR_VENV/bin/activate"

python "$AUTO_AVSR/asr_to_words_notime.py" \
  --in_videos "$SEGMENT_VID_DIR" \
  --out_wrd   "$SEGMENT_WRD_TMP" \
  --model medium \
  --lang en \
  --tokenize alnum \
  --lower

deactivate

########################
# STEP 1.5: Save new Whisper outputs to .transcriptions/ for future reuse
########################
echo ">>> [1.5] Saving new auto-transcriptions to .transcriptions/"
mkdir -p "$TRANSCRIPTIONS_DIR"

# Load metadata to check which transcriptions are manual
METADATA_FILE="$TRANSCRIPTIONS_DIR/metadata.json"
if [ ! -f "$METADATA_FILE" ]; then
  echo '{"transcriptions":{}}' > "$METADATA_FILE"
fi

saved_count=0
skipped_count=0

for wrd_file in "$SEGMENT_WRD_TMP"/*.wrd; do
  if [ -f "$wrd_file" ]; then
    filename=$(basename "$wrd_file")
    dest_file="$TRANSCRIPTIONS_DIR/$filename"

    # Check if this is a segment transcription
    if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
      # Check if transcription already exists and is manual
      is_manual=$(python3 -c "
import json, sys
try:
    with open('$METADATA_FILE') as f:
        meta = json.load(f)
    filename_mp4 = '${filename%.wrd}.mp4'
    trans_type = meta.get('transcriptions', {}).get(filename_mp4, {}).get('type', 'auto')
    print('yes' if trans_type == 'manual' else 'no')
except:
    print('no')
" 2>/dev/null)

      if [ "$is_manual" = "yes" ]; then
        echo ">>> [1.5]   Skipping $filename (manual transcription exists)"
        skipped_count=$((skipped_count + 1))
      else
        cp "$wrd_file" "$dest_file"
        saved_count=$((saved_count + 1))

        # Update metadata to mark as 'auto'
        python3 << EOF
import json
from datetime import datetime

try:
    with open('$METADATA_FILE', 'r') as f:
        meta = json.load(f)
except:
    meta = {'transcriptions': {}}

filename_mp4 = '${filename%.wrd}.mp4'
word_count = len(open('$wrd_file').read().strip().split('\n'))

meta['transcriptions'][filename_mp4] = {
    'type': 'auto',
    'created_at': datetime.utcnow().isoformat() + 'Z',
    'edited_at': None,
    'word_count': word_count,
    'video_checksum': None
}

with open('$METADATA_FILE', 'w') as f:
    json.dump(meta, f, indent=2)
EOF
      fi
    fi
  fi
done

if [ $saved_count -gt 0 ]; then
  echo ">>> [1.5] Saved $saved_count new auto-transcription(s) to .transcriptions/"
fi
if [ $skipped_count -gt 0 ]; then
  echo ">>> [1.5] Skipped $skipped_count manual transcription(s) (preserved)"
fi

# Convert .wrd files to .txt files (space-separated format expected by pipeline)
echo ">>> [3] Converting .wrd to .txt format"
mkdir -p "$SEGMENT_TXT_DIR"

for wrd_file in "$SEGMENT_WRD_TMP"/*.wrd; do
    if [ -f "$wrd_file" ]; then
        basename_noext=$(basename "$wrd_file" .wrd)
        txt_file="$SEGMENT_TXT_DIR/${basename_noext}.txt"
        # Convert one-word-per-line to space-separated
        tr '\n' ' ' < "$wrd_file" | sed 's/ $//' > "$txt_file"
        echo "$txt_file" >> /dev/null  # Suppress output
    fi
done

# Clean up temp directory
rm -rf "$SEGMENT_WRD_TMP"

echo ">>> [3] ASR complete. Transcriptions saved to: $SEGMENT_TXT_DIR"
echo

########################
# STEP 4: flat_to_lrs3_preperation.sh
########################
echo ">>> [4] Running flat_to_lrs3_preperation.sh"

# Use the same DIR_SUFFIX as preprocessing
SEG_DURATION="$SEG_DURATION" \
DIR_SUFFIX="$DIR_SUFFIX" \
LRS3_ROOT="$PREP_ROOT" \
bash "$AVH/avhubert/preparation/flat_to_lrs3_preperation.sh" \
  "$PREP_ROOT"

########################
# STEP 5: manifests + splits + train.tsv
########################
echo ">>> [5] Building manifests and TSVs"

source "$VSP_VENV/bin/activate"

python "$AUTO_AVSR/make_simple_manifest.py" \
  --root "$PREP_ROOT" \
  --split train \
  --out-dir "$MANIFEST_ROOT"

python "$AVH/avhubert/preparation/split_flat_dataset.py" \
  --root "$PREP_ROOT" \
  --train-ratio 1.0 \
  --valid-ratio 0.0 \
  --test-ratio 0.0 \
  --seed 0

python "$VSP/scripts/build_flat_train_tsv.py" \
  --root "$PREP_ROOT"

########################
# STEP 5a: Generate segment timing metadata (if segmentation and overlap enabled)
########################
if [ "$SEGMENTATION_ENABLED" = "1" ] && [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [5a] Generating segment timing metadata..."

    python "$AUTO_AVSR/generate_segment_timing.py" \
      --manifest-tsv "$MANIFEST_ROOT/train.tsv" \
      --segment-metadata "$PREP_ROOT/segment_metadata.json" \
      --output-json "$MANIFEST_ROOT/segment_timing.json"

    echo ">>> [INFO] Timing metadata saved to: $MANIFEST_ROOT/segment_timing.json"
else
    echo ">>> [5a] Skipping segment timing (segmentation disabled or overlap disabled)"
fi

#########################
# STEP 6: k-means + cluster counts
########################
echo ">>> [6] Running k-means and cluster count extraction"

cd "$AVH/avhubert/preparation"

TRAIN_KMEANS="${TRAIN_KMEANS:-1}" \
LRS3_ROOT="$PREP_ROOT" \
SPLIT="train" \
NSHARD=1 \
PERCENT=1.0 \
FEAT_DIR="$FEAT_DIR" \
KM_PATH="$KM_PATH" \
LAB_DIR="$LAB_DIR" \
"$VSP/scripts/run_flat_kmeans.sh"

LRS3_ROOT="$PREP_ROOT" \
FEAT_DIR="$FEAT_DIR" \
KM_PATH="$KM_PATH" \
LAB_DIR="$LAB_DIR" \
SPLIT="train" \
NSHARD=1 \
"$VSP/scripts/run_cluster_counts.sh"

deactivate

#######################
# STEP 7: LLM decode
########################
echo ">>> [7] Running VSP-LLM decode"

mkdir -p "$VSP/src/dataset/vsr/en"

ln -sf "$MANIFEST_ROOT/train.tsv" "$VSP/src/dataset/vsr/en/train.tsv"
ln -sf "$MANIFEST_ROOT/train.wrd" "$VSP/src/dataset/vsr/en/train.wrd"
ln -sf "$LAB_DIR/train.cluster_counts" "$VSP/src/dataset/vsr/en/train.cluster_counts"

ln -sf "$VSP/src/dataset/vsr/en/train.tsv" "$VSP/src/dataset/vsr/en/test.tsv"
ln -sf "$VSP/src/dataset/vsr/en/train.wrd" "$VSP/src/dataset/vsr/en/test.wrd"
ln -sf "$VSP/src/dataset/vsr/en/train.cluster_counts" "$VSP/src/dataset/vsr/en/test.cluster_counts"

source "$VSP_VENV/bin/activate"
cd "$VSP"

LANG="en" \
SPLIT="train" \
LRS3_ROOT="$PREP_ROOT" \
LAB_DIR="$LAB_DIR" \
WRD_ROOT="$WRD_ROOT" \
bash "$VSP/scripts/run_flat_decode.sh"

########################
# STEP 7a: Merge - DISABLED (segments treated independently, or whole videos if no segmentation)
########################
if [ "$SEGMENTATION_ENABLED" = "1" ]; then
    if [ "$OVERLAP_ENABLED" = "1" ]; then
        echo ">>> [7a] Segments processed independently - merge step skipped"
        echo "    Each segment will appear separately in reports and burned videos"
    else
        echo ">>> [7a] Segments processed independently (overlap disabled)"
    fi
else
    echo ">>> [7a] Whole videos processed (no segmentation) - merge step not applicable"
fi

########################
# STEP 8: Client outputs
########################
echo ">>> [8] Building client outputs"

POST_ROOT="${ARCHIVE_ROOT}/client_outputs"
REPORT_DIR="${POST_ROOT}/report"
BURN_DIR="${POST_ROOT}/burned_videos"

mkdir -p "$REPORT_DIR" "$BURN_DIR"

# Find decode output (check both nested and flat paths)
DECODE_JSON="$(ls -t ${VSP}/decode/vsr/en/vsr/en/hypo-*.json ${VSP}/decode/vsr/en/hypo-*.json 2>/dev/null | grep -v "merged" | head -n 1)"

# Use segmented video directory for burning (each segment is separate video)
SEGMENT_VID_DIR="${PREP_ROOT}/${DATA_NAME}/${DATA_NAME}_video_seg${SEG_DURATION}s"
SEGMENT_METADATA="${PREP_ROOT}/segment_metadata.json"

echo ">>> [8] Generating segment-level reports and burned videos"

python "$VSP/scripts/make_report.py" \
    --jsonl "$DECODE_JSON" \
    --out_dir "$REPORT_DIR"

python "$VSP/scripts/make_burn.py" \
    --jsonl "$DECODE_JSON" \
    --video_dir "$FLAT_VID_DIR" \
    --segment_dir "$SEGMENT_VID_DIR" \
    --segment_metadata "$SEGMENT_METADATA" \
    --out_dir "$BURN_DIR"

deactivate

echo
echo ">>> Pipeline complete!"
echo "    - Mouth crops: $PREP_ROOT"
echo "    - TSVs: $MANIFEST_ROOT"
echo "    - Labels: $LAB_DIR"
echo "    - Outputs: $POST_ROOT"