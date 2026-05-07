#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — desktop launcher (Linux)
# ==================================================
# Double-click target. Picks an input folder via zenity, runs the
# pipeline in a terminal window, dumps outputs to ~/vsp-output/<ts>/.
#
# Image tag is read from /opt/vsp/launcher/image.tag (single source of
# truth, swapped by apply_update.sh on patches).
# ==================================================

set -euo pipefail

# --- Resolve image tag ---
TAG_FILE="/opt/vsp/launcher/image.tag"
if [ ! -f "$TAG_FILE" ]; then
  # Fall back to relative location (kit not installed system-wide yet).
  TAG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/image.tag"
fi
if [ ! -f "$TAG_FILE" ]; then
  zenity --error --text="Image tag config not found:\n$TAG_FILE\n\nRun the kit's install.sh first."
  exit 1
fi
IMG_TAG="$(tr -d '[:space:]' < "$TAG_FILE")"
# Validate tag: defends against a corrupted image.tag breaking the docker run.
if [[ ! "$IMG_TAG" =~ ^[a-zA-Z0-9._/:-]+$ ]]; then
  zenity --error --text="Invalid image tag in $TAG_FILE: $IMG_TAG"
  exit 1
fi

# --- Working dirs ---
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${VSP_OUTPUT_DIR:-$HOME/vsp-output/$TIMESTAMP}"
mkdir -p "$OUT_DIR"

# --- Pick input folder ---
INPUT_DIR="$(zenity --file-selection --directory --title='Pick the folder with raw videos' 2>/dev/null || true)"
if [ -z "$INPUT_DIR" ]; then
  exit 0
fi
if [ ! -d "$INPUT_DIR" ]; then
  zenity --error --text="Selected folder doesn't exist: $INPUT_DIR"
  exit 1
fi

# --- Persistent transcriptions dir (per-input-dataset) ---
# Survives across pipeline runs so Whisper skips already-transcribed segments
# AND manual transcription edits are kept. Keyed by basename of the input dir
# so different datasets don't collide. Lives on the host (writable) — input
# is mounted :ro for safety, so transcriptions can't live alongside videos
# in the container.
DATASET_NAME="$(basename "$INPUT_DIR")"
TRANS_DIR="$HOME/vsp-transcriptions/${DATASET_NAME}"
mkdir -p "$TRANS_DIR"

# --- Pick a terminal that actually exists on this DE ---
TERM_CMD=""
for t in x-terminal-emulator gnome-terminal konsole xfce4-terminal mate-terminal terminator alacritty kitty xterm; do
  if command -v "$t" >/dev/null 2>&1; then TERM_CMD="$t"; break; fi
done
if [ -z "$TERM_CMD" ]; then
  zenity --error --text="No terminal emulator found. Install one of: gnome-terminal, konsole, xfce4-terminal, xterm."
  exit 1
fi

# --- Existence-check before remove (filters spurious "no such container" without hiding real errors) ---
if docker inspect vsp >/dev/null 2>&1; then
  docker rm -f vsp >/dev/null 2>&1 || {
    zenity --error --text="Failed to remove existing 'vsp' container.\nRun 'docker rm -f vsp' manually."
    exit 1
  }
fi

# --- Build the run command in a temp script (avoids fragile nested quoting; safe for spaces in paths) ---
RUN_SCRIPT="$(mktemp /tmp/vsp-run.XXXXXX.sh)"
trap 'rm -f "$RUN_SCRIPT"' EXIT
cat > "$RUN_SCRIPT" <<EOF
#!/usr/bin/env bash
set -uo pipefail
echo "VSP Pipeline launcher"
echo "Image:           $IMG_TAG"
echo "Input:           $INPUT_DIR (read-only)"
echo "Output:          $OUT_DIR"
echo "Transcriptions:  $TRANS_DIR (persistent across runs; keyed by dataset name)"
echo "Started:         \$(date)"
echo
echo "Press Ctrl+C to abort. The container will be removed on exit."
echo "----------------------------------------"

docker run --name vsp --gpus all \\
  -e VSP_OUTPUT_DIR=/data/out \\
  -e VSP_TRANSCRIPTIONS_DIR=/data/transcriptions \\
  -v $(printf '%q' "$INPUT_DIR"):/data/in:ro \\
  -v $(printf '%q' "$OUT_DIR"):/data/out \\
  -v $(printf '%q' "$TRANS_DIR"):/data/transcriptions \\
  $IMG_TAG \\
  /workspace/run_flat_english_pipeline.sh /data/in
RC=\$?

echo
echo "----------------------------------------"
if [ \$RC -eq 0 ]; then
  echo "Pipeline finished successfully."
  echo "Outputs are in: $OUT_DIR"
  if command -v xdg-open >/dev/null 2>&1; then
    if [ -f "$OUT_DIR/report.html" ]; then
      echo "Open the report: xdg-open $OUT_DIR/report.html"
    fi
  fi
else
  echo "Pipeline exited with code \$RC."
  echo "If this is unexpected, run ./checks/collect_diagnostics.sh"
  echo "and send the resulting tarball to support."
fi
echo
echo "Press Enter to close."
read
EOF
chmod +x "$RUN_SCRIPT"

case "$TERM_CMD" in
  gnome-terminal)
    "$TERM_CMD" -- bash "$RUN_SCRIPT"
    ;;
  *)
    "$TERM_CMD" -e bash "$RUN_SCRIPT"
    ;;
esac
