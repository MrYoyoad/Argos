#!/bin/bash
LOGFILE="/home/ubuntu/pipeline_english_1k_20260217_013839.log"
PID=$(cat /home/ubuntu/pipeline_english_1k.pid)
RESULTS_DIR="/home/ubuntu/english_1k_results"

echo "Watching pipeline PID $PID..."
# Wait for pipeline to finish
while kill -0 "$PID" 2>/dev/null; do sleep 30; done

echo "Pipeline finished at $(date). Saving results..."
mkdir -p "$RESULTS_DIR"

# Save k-means model
cp /home/ubuntu/VSP-LLM/flat_kmeans_200.bin "$RESULTS_DIR/" 2>/dev/null && echo "Saved k-means model" || echo "No k-means model found"

# Save labels
cp -r /home/ubuntu/VSP-LLM/flat_labels "$RESULTS_DIR/" 2>/dev/null

# Save decode output
cp -r /home/ubuntu/VSP-LLM/decode/vsr/en "$RESULTS_DIR/decode_output" 2>/dev/null

# Save client outputs from latest archive
ARCHIVE_DIR=$(ls -dt /home/ubuntu/flat_runs_archive/*/ 2>/dev/null | head -1)
cp -r "${ARCHIVE_DIR}client_outputs" "$RESULTS_DIR/" 2>/dev/null

# Save manifests
cp -r /home/ubuntu/auto_avsr/preprocessed_flat_seg12/433h_data "$RESULTS_DIR/manifests" 2>/dev/null

# Copy log
cp "$LOGFILE" "$RESULTS_DIR/pipeline.log"

# Quick summary
echo "=== PIPELINE SUMMARY ===" > "$RESULTS_DIR/summary.txt"
echo "Finished: $(date)" >> "$RESULTS_DIR/summary.txt"
grep -q "Pipeline complete" "$LOGFILE" && echo "Status: SUCCESS" >> "$RESULTS_DIR/summary.txt" || echo "Status: FAILED" >> "$RESULTS_DIR/summary.txt"
echo "K-means: $(ls -lh "$RESULTS_DIR/flat_kmeans_200.bin" 2>/dev/null | awk '{print $5}')" >> "$RESULTS_DIR/summary.txt"
echo "Transcriptions: $(ls /home/ubuntu/auto_avsr/flat_wrd/*.wrd 2>/dev/null | wc -l) files" >> "$RESULTS_DIR/summary.txt"
echo "Decode files: $(ls "$RESULTS_DIR/decode_output/" 2>/dev/null | wc -l)" >> "$RESULTS_DIR/summary.txt"
echo "Results saved to: $RESULTS_DIR" >> "$RESULTS_DIR/summary.txt"
tail -20 "$LOGFILE" >> "$RESULTS_DIR/summary.txt"
echo "Done. Results in $RESULTS_DIR"
