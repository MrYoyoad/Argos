#!/bin/bash
# Wrapper script that detects merged output and generates appropriate reports

set -e

DECODE_JSON="$1"
OUTPUT_DIR="$2"

if [ -z "$DECODE_JSON" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <decode_json> <output_dir>"
    exit 1
fi

# Check if merged output exists
MERGED_JSON="${DECODE_JSON%.json}-merged.json"

if [ -f "$MERGED_JSON" ] && [ "${OVERLAP_ENABLED:-1}" = "1" ]; then
    echo "✓ Using merged predictions for reports..."
    
    # Use merged output for standard report
    # Note: make_report.py might not exist yet, so we'll just note it here
    # python make_report.py --decode-json "$MERGED_JSON" --output-dir "$OUTPUT_DIR"
    
    # Generate conflict report
    python3 "$(dirname "$0")/generate_conflict_report.py" \
        --merged-json "$MERGED_JSON" \
        --output-dir "$OUTPUT_DIR/conflicts"
    
    echo "✓ Reports generated with merged predictions"
else
    echo "Using standard segment-level reports..."
    # python make_report.py --decode-json "$DECODE_JSON" --output-dir "$OUTPUT_DIR"
fi
