#!/usr/bin/env bash
# List all available golden k-means models
set -euo pipefail

GOLDEN_DIR="/home/ubuntu/VSP-LLM/golden_kmeans"

if [[ ! -d "$GOLDEN_DIR" ]]; then
  echo "No golden models directory found."
  echo "Run save_golden_kmeans.sh first to create one."
  exit 0
fi

echo "Available golden k-means models:"
echo "================================"
echo

if ! ls -1 "$GOLDEN_DIR"/*.bin 2>/dev/null | grep -q .; then
  echo "No golden models found in $GOLDEN_DIR"
  echo
  exit 0
fi

for model in "$GOLDEN_DIR"/*.bin; do
  name=$(basename "$model")
  size=$(du -h "$model" | cut -f1)
  date=$(stat -c '%y' "$model" | cut -d' ' -f1)
  echo "  Name: $name"
  echo "  Size: $size"
  echo "  Date: $date"
  echo "  Path: $model"
  echo
done

echo "To use a golden model:"
echo "  export GOLDEN_KMEANS='/path/to/model.bin'"
echo "  ./run_flat_english_pipeline.sh /path/to/videos"
