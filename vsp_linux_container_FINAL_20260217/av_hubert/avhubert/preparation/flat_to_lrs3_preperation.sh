#!/usr/bin/env bash
set -euo pipefail

# If you call this as:
#   bash flat_to_lrs3_preperation.sh /home/ubuntu/auto_avsr/preprocessed_flat_seg12
# then:
SEG_DURATION="${SEG_DURATION:-12}"  # Segment duration (default 12s for optimal context)
DIR_SUFFIX="${DIR_SUFFIX:-seg${SEG_DURATION}s}"  # Directory suffix: "seg12s" or "whole"
LRS3_ROOT="${1:-/home/ubuntu/auto_avsr/preprocessed_flat_seg${SEG_DURATION}}"  # default if not given

# Auto-detect paths from script location
PREP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Derive base dir: PREP_DIR is <base>/av_hubert/avhubert/preparation
_BASE_DIR="$(cd "${PREP_DIR}/../../.." && pwd)"

# Use VENV from caller if provided (pipeline passes PREP_VENV),
# otherwise auto-detect from known locations
if [ -z "${VENV:-}" ]; then
    if [ -d "/workspace/auto_avsr/pre-process-venv" ]; then
        VENV="/workspace/auto_avsr/pre-process-venv"
    elif [ -d "${_BASE_DIR}/auto_avsr/pre-process-venv" ]; then
        VENV="${_BASE_DIR}/auto_avsr/pre-process-venv"
    elif [ -d "$HOME/auto_avsr/pre-process-venv" ]; then
        VENV="$HOME/auto_avsr/pre-process-venv"
    else
        echo "ERROR: Cannot find auto_avsr/pre-process-venv" >&2
        echo "  Checked: /workspace/auto_avsr/pre-process-venv" >&2
        echo "  Checked: ${_BASE_DIR}/auto_avsr/pre-process-venv" >&2
        echo "  Checked: $HOME/auto_avsr/pre-process-venv" >&2
        exit 1
    fi
fi

echo ">>> Activating venv: ${VENV}"
source "${VENV}/bin/activate"

echo ">>> Using LRS3_ROOT=${LRS3_ROOT}"
cd "${LRS3_ROOT}"

echo ">>> Creating video/ and audio/ symlinks -> flat/flat_video_${DIR_SUFFIX}"
rm -f video audio
ln -s flat/flat_video_${DIR_SUFFIX} video
ln -s flat/flat_video_${DIR_SUFFIX} audio

echo ">>> Building file.list and label.list from flat_video_${DIR_SUFFIX} and flat_text_${DIR_SUFFIX}"

DIR_SUFFIX="$DIR_SUFFIX" LRS3_ROOT="$LRS3_ROOT" python3 - << 'PYEOF'
import os, glob

dir_suffix = os.environ.get("DIR_SUFFIX", "seg12s")
root = os.environ.get("LRS3_ROOT")
video_dir = os.path.join(root, "flat", f"flat_video_{dir_suffix}")
text_dir  = os.path.join(root, "flat", f"flat_text_{dir_suffix}")

ids = sorted(
    os.path.splitext(os.path.basename(p))[0]
    for p in glob.glob(os.path.join(video_dir, "*.mp4"))
)

file_list_path  = os.path.join(root, "file.list")
label_list_path = os.path.join(root, "label.list")

print(f"Found {len(ids)} segments")

with open(file_list_path, "w") as f_file, \
     open(label_list_path, "w") as f_label:
    for fid in ids:
        f_file.write(fid + "\n")
        txt_path = os.path.join(text_dir, fid + ".txt")
        with open(txt_path, "r") as ft:
            # Read all lines and join with spaces (for multi-word transcriptions)
            words = [line.strip().lower() for line in ft if line.strip()]
            line = " ".join(words)
        f_label.write(line + "\n")

print("Wrote:", file_list_path)
print("Wrote:", label_list_path)
PYEOF

echo ">>> Running count_frames.py"
cd "${PREP_DIR}"

python3 count_frames.py \
  --root "${LRS3_ROOT}" \
  --manifest "${LRS3_ROOT}/file.list" \
  --nshard 1 \
  --rank 0

echo ">>> Copying nframes.*.0 to final names"
cd "${LRS3_ROOT}"

if [[ -f nframes.audio.0 && -f nframes.video.0 ]]; then
  cp nframes.audio.0 nframes.audio
  cp nframes.video.0 nframes.video
  echo "Created nframes.audio and nframes.video"
else
  echo "ERROR: nframes.audio.0 or nframes.video.0 missing. Check count_frames.py output." >&2
  exit 1
fi

echo ">>> Done flat_to_lrs3_preperation.sh"