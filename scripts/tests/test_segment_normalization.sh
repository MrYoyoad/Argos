#!/usr/bin/env bash
# Test script to verify normalization works on segments instead of whole videos

set -euo pipefail

echo "=========================================="
echo "Test: Segment-First Normalization"
echo "=========================================="
echo

# Test configuration
TEST_DIR="/tmp/test_segment_normalization_$$"
TEST_VIDEO_DIR="${TEST_DIR}/raw_videos"
TEST_DURATION=36  # 36 seconds = should create 4 segments (0-12, 10-22, 20-32, 30-36)

# Cleanup function
cleanup() {
  echo
  echo ">>> Cleaning up test directory..."
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Create test environment
echo ">>> Setting up test environment..."
mkdir -p "$TEST_VIDEO_DIR"

# Create a test video (36 seconds, solid color with audio tone)
echo ">>> Creating test video (${TEST_DURATION}s)..."
ffmpeg -y -f lavfi -i color=c=blue:s=640x480:d=$TEST_DURATION:r=25 \
       -f lavfi -i "sine=frequency=440:duration=$TEST_DURATION" \
       -pix_fmt yuv420p -c:v libx264 -preset ultrafast -c:a aac \
       "${TEST_VIDEO_DIR}/test_video.mp4" 2>/dev/null

if [ ! -f "${TEST_VIDEO_DIR}/test_video.mp4" ]; then
  echo "ERROR: Failed to create test video"
  exit 1
fi

echo "✓ Test video created: ${TEST_VIDEO_DIR}/test_video.mp4 (${TEST_DURATION}s)"
echo

# Run the pipeline up to Step 0.5 (normalization)
echo ">>> Running pipeline Steps 0.1 and 0.5..."
echo

# Set required environment variables
export SEGMENTATION_ENABLED=1
export OVERLAP_ENABLED=1
export SEG_DURATION=12
export SKIP_NORM=0  # Enable normalization
export USE_GPU_NORM=0  # Use CPU to avoid GPU requirements in test

# Extract just Steps 0.1 and 0.5 from the pipeline
cd /home/ubuntu

# Step 0.1: Fast Segmentation
echo ">>> [TEST 0.1] Running fast segmentation..."
PREP_ROOT="${TEST_DIR}/preprocessed_flat_seg12"
FAST_SEG_DIR="${PREP_ROOT}/fast_segments"
mkdir -p "${FAST_SEG_DIR}"

source ~/auto_avsr/pre-process-venv/bin/activate

python ~/auto_avsr/preparation/fast_segment.py \
  --data-dir "${TEST_VIDEO_DIR}" \
  --output-dir "${FAST_SEG_DIR}" \
  --seg-duration 12 \
  --overlap 2.0 \
  --min-split-duration 12.0

deactivate

# Count segments created
SEGMENT_COUNT=$(find "$FAST_SEG_DIR" -name "*.mp4" | wc -l)
echo "✓ Fast segmentation complete: $SEGMENT_COUNT segments created"
echo

# Verify segments were created
if [ "$SEGMENT_COUNT" -eq 0 ]; then
  echo "ERROR: No segments created by fast_segment.py"
  exit 1
fi

# Check segment durations
echo ">>> Verifying segment durations..."
for seg in "$FAST_SEG_DIR"/*.mp4; do
  if [ -f "$seg" ]; then
    seg_name=$(basename "$seg")
    seg_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$seg" 2>/dev/null)
    seg_dur_int=$(printf "%.0f" "$seg_dur")
    echo "  - $seg_name: ${seg_dur}s"

    # Each segment should be ≤ 12 seconds
    if (( $(echo "$seg_dur > 12.5" | bc -l) )); then
      echo "ERROR: Segment duration $seg_dur exceeds expected 12s"
      exit 1
    fi
  fi
done
echo "✓ All segments are ≤12 seconds"
echo

# Step 0.5: Normalization (on segments!)
echo ">>> [TEST 0.5] Running normalization on segments..."
source "${HOME}/lib/normalization.sh"

PREP_DIR="${TEST_DIR}/flat_prepared"
FLAT_VID_DIR="${TEST_DIR}/flat"

# This should normalize SEGMENTS, not the original 36s video
run_normalization "$FAST_SEG_DIR" "$PREP_DIR" 0 0 25 0 600

# Copy to FLAT_VID_DIR (like the pipeline does)
mkdir -p "$FLAT_VID_DIR"
cp -a "${PREP_DIR}/." "${FLAT_VID_DIR}/"

# Verify normalized videos
NORMALIZED_COUNT=$(find "$PREP_DIR" -name "*.mp4" | wc -l)
echo "✓ Normalization complete: $NORMALIZED_COUNT videos normalized"
echo

# Verify counts match
if [ "$NORMALIZED_COUNT" -ne "$SEGMENT_COUNT" ]; then
  echo "ERROR: Normalized count ($NORMALIZED_COUNT) doesn't match segment count ($SEGMENT_COUNT)"
  exit 1
fi

# Verify normalized video durations
echo ">>> Verifying normalized segment durations..."
for norm_vid in "$PREP_DIR"/*.mp4; do
  if [ -f "$norm_vid" ]; then
    vid_name=$(basename "$norm_vid")
    vid_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$norm_vid" 2>/dev/null)
    vid_dur_int=$(printf "%.0f" "$vid_dur")
    echo "  - $vid_name: ${vid_dur}s"

    # Each normalized segment should be ≤ 12 seconds
    if (( $(echo "$vid_dur > 12.5" | bc -l) )); then
      echo "ERROR: Normalized segment duration $vid_dur exceeds expected 12s"
      exit 1
    fi
  fi
done
echo "✓ All normalized segments are ≤12 seconds"
echo

# Final verification
echo "=========================================="
echo "Test Results:"
echo "=========================================="
echo "✓ Step 0.1: Created $SEGMENT_COUNT segments from ${TEST_DURATION}s video"
echo "✓ Step 0.5: Normalized $NORMALIZED_COUNT segments (NOT the whole video)"
echo "✓ All segments ≤12 seconds (efficient normalization!)"
echo
echo "SUCCESS: Normalization is working on segments, not whole videos!"
echo "=========================================="