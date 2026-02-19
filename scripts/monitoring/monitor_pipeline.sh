#!/bin/bash
# Monitor pipeline progress every 20 minutes
LOGFILE="/home/ubuntu/pipeline_full_rerun.log"
PIDFILE="/home/ubuntu/pipeline_full_rerun.pid"
MONITOR_LOG="/home/ubuntu/pipeline_monitor.log"

echo "=== Pipeline Monitor Started $(date) ===" >> "$MONITOR_LOG"

while true; do
    PID=$(cat "$PIDFILE" 2>/dev/null)
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "[$(date)] Pipeline finished (PID $PID no longer running)" >> "$MONITOR_LOG"
        # Check if success or failure
        if grep -q "Pipeline complete" "$LOGFILE" 2>/dev/null; then
            echo "[$(date)] STATUS: SUCCESS" >> "$MONITOR_LOG"
        else
            echo "[$(date)] STATUS: POSSIBLY FAILED (no 'Pipeline complete' found)" >> "$MONITOR_LOG"
            tail -10 "$LOGFILE" >> "$MONITOR_LOG"
        fi
        break
    fi

    # Get current stage
    STAGE=$(grep "^>>>" "$LOGFILE" 2>/dev/null | tail -1)
    # Count progress indicators
    DONE=$(grep -c "✓" "$LOGFILE" 2>/dev/null)
    
    echo "[$(date)] PID=$PID running | Stage: $STAGE | Completed items: $DONE" >> "$MONITOR_LOG"
    
    sleep 1200  # 20 minutes
done

echo "=== Monitor Ended $(date) ===" >> "$MONITOR_LOG"
