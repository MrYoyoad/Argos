#!/bin/bash
# check_container_inventory.sh - Run this inside your container

OUTPUT_FILE="/tmp/container_inventory_$(date +%Y%m%d_%H%M%S).txt"

echo "=== Container Inventory Check ===" | tee "$OUTPUT_FILE"
echo "Date: $(date)" | tee -a "$OUTPUT_FILE"
echo | tee -a "$OUTPUT_FILE"

cd /host/galaxy_export 2>/dev/null || cd /workspace/galaxy_export 2>/dev/null || {
  echo "ERROR: Cannot find galaxy_export" | tee -a "$OUTPUT_FILE"
  exit 1
}

BASE_DIR="$(pwd)"
echo "Galaxy Export Base: $BASE_DIR" | tee -a "$OUTPUT_FILE"
echo | tee -a "$OUTPUT_FILE"

# Check critical directories
echo "=== Directory Structure ===" | tee -a "$OUTPUT_FILE"
for dir in lib auto_avsr/preparation VSP-LLM/src VSP-LLM/scripts vsp-ui av_hubert; do
  if [ -d "$dir" ]; then
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    files=$(find "$dir" -type f 2>/dev/null | wc -l)
    echo "✓ $dir/ - Size: $size, Files: $files" | tee -a "$OUTPUT_FILE"
  else
    echo "✗ MISSING: $dir/" | tee -a "$OUTPUT_FILE"
  fi
done
echo | tee -a "$OUTPUT_FILE"

# Check specific NEW/MODIFIED files from refactoring
echo "=== Critical Files (NEW or MODIFIED) ===" | tee -a "$OUTPUT_FILE"
declare -a critical_files=(
  # Main pipeline (MODIFIED)
  "run_flat_english_pipeline.sh"

  # Lib modules (ALL NEW from refactoring)
  "lib/common.sh"
  "lib/config.sh"
  "lib/archive.sh"
  "lib/normalization.sh"
  "lib/asr.sh"
  "lib/lrs3_prep.sh"
  "lib/manifests.sh"
  "lib/clustering.sh"
  "lib/decode.sh"
  "lib/outputs.sh"
  "lib/venv/venv_utils.sh"
  "lib/test_all_modules.sh"

  # Auto-AVSR NEW files
  "auto_avsr/preparation/fast_segment.py"
  "auto_avsr/preparation/preprocess_with_overlap.py"
  "auto_avsr/generate_segment_timing.py"

  # Auto-AVSR existing files (check if they exist)
  "auto_avsr/preparation/preprocess_lrs2lrs3.py"
  "auto_avsr/preparation/transforms.py"
  "auto_avsr/preparation/utils.py"
  "auto_avsr/preparation/run_flat_preprocess_batch.sh"
  "auto_avsr/asr_to_words_notime.py"
  "auto_avsr/make_simple_manifest.py"

  # VSP-LLM MODIFIED files
  "VSP-LLM/scripts/run_flat_kmeans.sh"
  "VSP-LLM/scripts/run_cluster_counts.sh"
  "VSP-LLM/scripts/make_report_wrapper.sh"
  "VSP-LLM/scripts/make_burn.py"
  "VSP-LLM/scripts/make_report.py"
  "VSP-LLM/src/vsp_llm_decode.py"
  "VSP-LLM/fairseq/fairseq/dataclass/configs.py"

  # VSP-UI (check structure)
  "vsp-ui/app/__init__.py"
  "vsp-ui/app/__main__.py"
  "vsp-ui/app/server.py"
  "vsp-ui/app/config.py"
  "vsp-ui/app/services/__init__.py"
  "vsp-ui/app/services/transcription_manager.py"
  "vsp-ui/app/services/validator.py"
  "vsp-ui/app/services/pipeline_runner.py"
  "vsp-ui/app/services/progress_tracker.py"
  "vsp-ui/launcher.sh"
  "vsp-ui/install.sh"
  "vsp-ui/app/static/index.html"
  "vsp-ui/app/static/app.js"
  "vsp-ui/app/static/style.css"

  # AV-HuBERT MODIFIED files
  "av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh"
  "av_hubert/avhubert/preparation/split_flat_dataset.py"
  "av_hubert/avhubert/preparation/count_frames.py"
)

for file in "${critical_files[@]}"; do
  if [ -f "$file" ]; then
    size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
    modified=$(stat -c '%y' "$file" 2>/dev/null | cut -d' ' -f1)

    # Check for "CONTAINER VERSION" marker (indicates container-specific paths)
    if grep -q "CONTAINER VERSION" "$file" 2>/dev/null; then
      marker=" [HAS CONTAINER VERSION]"
    else
      marker=""
    fi

    echo "✓ $file - $size (modified: $modified)$marker" | tee -a "$OUTPUT_FILE"
  else
    echo "✗ MISSING: $file" | tee -a "$OUTPUT_FILE"
  fi
done
echo | tee -a "$OUTPUT_FILE"

# Check for large directories that should NOT be packaged
echo "=== Large Directories (exclude from package) ===" | tee -a "$OUTPUT_FILE"
for dir in VSP-LLM/checkpoints vsp_input flat_runs_archive preprocessed_*; do
  if [ -d "$dir" ]; then
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    echo "⚠ $dir/ - Size: $size (EXCLUDE from package)" | tee -a "$OUTPUT_FILE"
  fi
done
echo | tee -a "$OUTPUT_FILE"

# Check Python package structure
echo "=== Python Package Files (__init__.py) ===" | tee -a "$OUTPUT_FILE"
find . -name "__init__.py" -type f 2>/dev/null | sort | tee -a "$OUTPUT_FILE"
echo | tee -a "$OUTPUT_FILE"

# Summary
echo "=== Summary ===" | tee -a "$OUTPUT_FILE"
echo "Output saved to: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo | tee -a "$OUTPUT_FILE"
echo "NEXT STEP: Copy this file to EC2 so we can identify what's missing" | tee -a "$OUTPUT_FILE"
echo "Command: docker cp <container>:$OUTPUT_FILE /path/on/ec2/" | tee -a "$OUTPUT_FILE"
