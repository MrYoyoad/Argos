#!/bin/bash
# Watcher for full 1,396-video pipeline re-run
# Saves all results when pipeline finishes

PIDFILE="/home/ubuntu/pipeline_full_rerun.pid"
LOGFILE="/home/ubuntu/pipeline_full_rerun.log"
RESULTS_DIR="/home/ubuntu/english_full_results"

PID=$(cat "$PIDFILE" 2>/dev/null)
if [ -z "$PID" ]; then
    echo "No PID file found at $PIDFILE"
    exit 1
fi

echo "Watching pipeline PID $PID..."
while kill -0 "$PID" 2>/dev/null; do sleep 60; done

echo "Pipeline finished at $(date). Saving results..."
mkdir -p "$RESULTS_DIR"

# Save k-means model
cp /home/ubuntu/VSP-LLM/flat_kmeans_200.bin "$RESULTS_DIR/" 2>/dev/null && echo "Saved k-means model" || echo "No k-means model found"

# Save labels
cp -r /home/ubuntu/VSP-LLM/flat_labels "$RESULTS_DIR/" 2>/dev/null && echo "Saved labels"

# Save decode output
mkdir -p "$RESULTS_DIR/decode_output"
cp -r /home/ubuntu/VSP-LLM/decode/vsr/en/* "$RESULTS_DIR/decode_output/" 2>/dev/null && echo "Saved decode output"

# Save client outputs from latest archive
ARCHIVE_DIR=$(ls -dt /home/ubuntu/flat_runs_archive/*/ 2>/dev/null | head -1)
if [ -n "$ARCHIVE_DIR" ]; then
    cp -r "${ARCHIVE_DIR}client_outputs" "$RESULTS_DIR/" 2>/dev/null && echo "Saved client outputs from $ARCHIVE_DIR"
fi

# Save manifests
cp -r /home/ubuntu/auto_avsr/preprocessed_flat_seg12/433h_data "$RESULTS_DIR/manifests" 2>/dev/null && echo "Saved manifests"

# Save segment metadata
cp /home/ubuntu/auto_avsr/preprocessed_flat_seg12/segment_metadata.json "$RESULTS_DIR/" 2>/dev/null

# Copy log
cp "$LOGFILE" "$RESULTS_DIR/pipeline.log"

# Summary
echo "=== FULL PIPELINE RE-RUN SUMMARY ===" > "$RESULTS_DIR/summary.txt"
echo "Finished: $(date)" >> "$RESULTS_DIR/summary.txt"
grep -q "Pipeline complete" "$LOGFILE" && echo "Status: SUCCESS" >> "$RESULTS_DIR/summary.txt" || echo "Status: FAILED" >> "$RESULTS_DIR/summary.txt"
echo "K-means: $(ls -lh "$RESULTS_DIR/flat_kmeans_200.bin" 2>/dev/null | awk '{print $5}')" >> "$RESULTS_DIR/summary.txt"
echo "Cached transcriptions reused: 895" >> "$RESULTS_DIR/summary.txt"

# Count segments
REPORT="$RESULTS_DIR/client_outputs/report/report.csv"
if [ -f "$REPORT" ]; then
    SEGMENTS=$(($(wc -l < "$REPORT") - 1))
    echo "Segments in report: $SEGMENTS" >> "$RESULTS_DIR/summary.txt"
fi

# Show last 20 lines of log
echo "" >> "$RESULTS_DIR/summary.txt"
echo "=== Last 20 lines of log ===" >> "$RESULTS_DIR/summary.txt"
tail -20 "$LOGFILE" >> "$RESULTS_DIR/summary.txt"

echo "Done. Results in $RESULTS_DIR"
cat "$RESULTS_DIR/summary.txt"
