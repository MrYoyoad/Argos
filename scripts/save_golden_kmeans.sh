
#!/usr/bin/env bash
# Save current k-means model as a golden model
set -euo pipefail

GOLDEN_DIR="/home/ubuntu/VSP-LLM/golden_kmeans"
CURRENT_MODEL="/home/ubuntu/VSP-LLM/flat_kmeans_200.bin"

if [[ ! -f "$CURRENT_MODEL" ]]; then
  echo "ERROR: No k-means model found at $CURRENT_MODEL"
  echo "Run the pipeline with k-means training first."
  exit 1
fi

mkdir -p "$GOLDEN_DIR"

# Prompt for model name
echo "Current k-means model: $CURRENT_MODEL"
echo
read -p "Enter a name for this golden model (e.g., '500videos_jan25'): " MODEL_NAME

if [[ -z "$MODEL_NAME" ]]; then
  echo "ERROR: Model name cannot be empty"
  exit 1
fi

# Add .bin extension if not present
if [[ ! "$MODEL_NAME" =~ \.bin$ ]]; then
  MODEL_NAME="${MODEL_NAME}.bin"
fi

GOLDEN_PATH="${GOLDEN_DIR}/${MODEL_NAME}"

if [[ -f "$GOLDEN_PATH" ]]; then
  read -p "Model '$MODEL_NAME' already exists. Overwrite? (y/N): " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

cp "$CURRENT_MODEL" "$GOLDEN_PATH"
echo
echo "✓ Saved golden k-means model to: $GOLDEN_PATH"
echo "  Size: $(du -h "$GOLDEN_PATH" | cut -f1)"
echo
echo "To use this model in a pipeline run:"
echo "  export GOLDEN_KMEANS='$GOLDEN_PATH'"
echo "  ./run_flat_english_pipeline.sh /path/to/videos"
