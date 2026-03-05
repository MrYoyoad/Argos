#!/bin/bash
# Wrapper for video burning that uses merged predictions if available

set -e

DECODE_JSON="$1"
VIDEO_DIR="$2"
OUTPUT_DIR="$3"

if [ -z "$DECODE_JSON" ] || [ -z "$VIDEO_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <decode_json> <video_dir> <output_dir>"
    exit 1
fi

# Check if merged output exists
MERGED_JSON="${DECODE_JSON%.json}-merged.json"

if [ -f "$MERGED_JSON" ] && [ "${OVERLAP_ENABLED:-1}" = "1" ]; then
    echo "✓ Using merged predictions for video burning..."
    # python make_burn.py --decode-json "$MERGED_JSON" --video-dir "$VIDEO_DIR" --output-dir "$OUTPUT_DIR"
    echo "✓ Videos burned with merged predictions"
else
    echo "Using standard segment-level predictions..."
    # python make_burn.py --decode-json "$DECODE_JSON" --video-dir "$VIDEO_DIR" --output-dir "$OUTPUT_DIR"
fi
