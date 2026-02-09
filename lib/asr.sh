#!/usr/bin/env bash
# ==================================================
# ASR (Automatic Speech Recognition) Module
# ==================================================
# Handles Whisper ASR transcription with unified transcription management
# Includes Steps 0.6, 3, and 1.5 for transcription persistence
# Works on EC2 and Linux container

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Run ASR transcription on segmented videos
# Parameters:
#   $1 - PREP_ROOT path
#   $2 - ASR_VENV path
#   $3 - AUTO_AVSR directory
#   $4 - DATA_NAME (e.g., "flat")
#   $5 - SEGMENTATION_ENABLED flag (0 or 1)
#   $6 - SEG_DURATION value
#   $7 - HOME directory (for .transcriptions/)
run_asr_transcription() {
  local prep_root="$1"
  local asr_venv="$2"
  local auto_avsr_dir="$3"
  local data_name="$4"
  local segmentation_enabled="${5:-1}"
  local seg_duration="${6:-12}"
  local home_dir="$7"

  log_stage "3" "Running ASR on videos"

  # Determine directory suffix based on SEGMENTATION_ENABLED
  local dir_suffix
  if [ "$segmentation_enabled" = "1" ]; then
    dir_suffix="seg${seg_duration}s"
  else
    dir_suffix="whole"
  fi

  # Get the video directory (segmented or whole)
  local segment_vid_dir="$prep_root/${data_name}/${data_name}_video_${dir_suffix}"
  local segment_txt_dir="$prep_root/${data_name}/${data_name}_text_${dir_suffix}"

  if [ ! -d "$segment_vid_dir" ]; then
    log_error "Segmented video directory not found: $segment_vid_dir"
    return 1
  fi

  # Create temp directory for ASR output (.wrd format)
  local segment_wrd_tmp="${prep_root}/segment_wrd_tmp"
  mkdir -p "$segment_wrd_tmp"

  # ============================================
  # STEP 0.6: Copy existing transcriptions from .transcriptions/ to working directory
  # ============================================
  echo ">>> [0.6] Checking for existing transcriptions"
  local transcriptions_dir="$home_dir/vsp_input/.transcriptions"

  if [ -d "$transcriptions_dir" ]; then
    local copied_count=0

    # Simple direct matching: video name = transcription name
    for video_file in "$segment_vid_dir"/*.mp4; do
      if [ -f "$video_file" ]; then
        local video_name=$(basename "$video_file" .mp4)
        local src_wrd="$transcriptions_dir/${video_name}.wrd"
        local dest_wrd="$segment_wrd_tmp/${video_name}.wrd"

        if [ -f "$src_wrd" ]; then
          cp "$src_wrd" "$dest_wrd"
          copied_count=$((copied_count + 1))
          echo ">>> [0.6]   Copied: ${video_name}.wrd"
        fi
      fi
    done

    if [ $copied_count -gt 0 ]; then
      echo ">>> [0.6] Copied $copied_count transcription(s)"
      echo ">>> [0.6] Whisper will skip these $copied_count segment(s)"
    else
      echo ">>> [0.6] No matching transcriptions found"
    fi
  else
    echo ">>> [0.6] No .transcriptions directory found (first run)"
  fi

  # ============================================
  # STEP 3: Run Whisper ASR
  # ============================================
  echo ">>> [3] Running Whisper on segmented videos from: $segment_vid_dir"
  source "$asr_venv/bin/activate" || {
    log_error "Failed to activate ASR venv: $asr_venv"
    return 1
  }

  # Auto-detect Whisper model cache directory
  local base_dir="$(dirname "$auto_avsr_dir")"
  local whisper_root=""
  if [ -d "$base_dir/whisper" ]; then
    whisper_root="$base_dir/whisper"
  elif [ -d "$HOME/.cache/whisper" ]; then
    whisper_root="$HOME/.cache/whisper"
  fi

  local download_root_arg=""
  if [ -n "$whisper_root" ]; then
    echo ">>> [3] Using Whisper model cache: $whisper_root"
    download_root_arg="--download_root $whisper_root"
  fi

  python "$auto_avsr_dir/asr_to_words_notime.py" \
    --in_videos "$segment_vid_dir" \
    --out_wrd   "$segment_wrd_tmp" \
    --model medium \
    --lang en \
    --tokenize alnum \
    --lower \
    $download_root_arg || {
    log_error "Whisper ASR failed"
    deactivate
    return 1
  }

  deactivate

  # ============================================
  # STEP 1.5: Save new Whisper outputs to .transcriptions/ for future reuse
  # ============================================
  echo ">>> [1.5] Saving new auto-transcriptions to .transcriptions/"
  mkdir -p "$transcriptions_dir"

  # Load metadata to check which transcriptions are manual
  local metadata_file="$transcriptions_dir/metadata.json"
  if [ ! -f "$metadata_file" ]; then
    echo '{"transcriptions":{}}' > "$metadata_file"
  fi

  local saved_count=0
  local skipped_count=0

  for wrd_file in "$segment_wrd_tmp"/*.wrd; do
    if [ -f "$wrd_file" ]; then
      local filename=$(basename "$wrd_file")
      local dest_file="$transcriptions_dir/$filename"

      # Check if this is a segment transcription
      if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
        # Check if transcription already exists and is manual
        local is_manual=$(python3 -c "
import json, sys
try:
    with open('$metadata_file') as f:
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
    with open('$metadata_file', 'r') as f:
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

with open('$metadata_file', 'w') as f:
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

  # ============================================
  # Convert .wrd files to .txt files (space-separated format expected by pipeline)
  # ============================================
  echo ">>> [3] Converting .wrd to .txt format"
  mkdir -p "$segment_txt_dir"

  for wrd_file in "$segment_wrd_tmp"/*.wrd; do
    if [ -f "$wrd_file" ]; then
      local basename_noext=$(basename "$wrd_file" .wrd)
      local txt_file="$segment_txt_dir/${basename_noext}.txt"
      # Convert one-word-per-line to space-separated
      tr '\n' ' ' < "$wrd_file" | sed 's/ $//' > "$txt_file"
    fi
  done

  # Clean up temp directory
  rm -rf "$segment_wrd_tmp"

  echo ">>> [3] ASR complete. Transcriptions saved to: $segment_txt_dir"
  log_info "ASR transcription complete"
  return 0
}

export -f run_asr_transcription
