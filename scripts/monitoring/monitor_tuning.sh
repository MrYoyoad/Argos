#!/bin/bash
LOG="/home/ubuntu/tuning_experiments.log"
PIDFILE="/home/ubuntu/tuning_experiments.pid"
MLOG="/home/ubuntu/tuning_monitor.log"

echo "=== Tuning Monitor Started $(date) ===" >> "$MLOG"

while true; do
    PID=$(cat "$PIDFILE" 2>/dev/null)
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "[$(date)] Experiments finished (PID $PID done)" >> "$MLOG"
        COMPLETED=$(grep -c "Experiment.*complete!" "$LOG" 2>/dev/null)
        echo "[$(date)] Completed experiments: $COMPLETED/7" >> "$MLOG"
        tail -20 "$LOG" >> "$MLOG"
        break
    fi
    
    COMPLETED=$(grep -c "Experiment.*complete!" "$LOG" 2>/dev/null)
    DECODED=$(grep -c "speech_recognize" "$LOG" 2>/dev/null)
    CURRENT=$(grep ">>> \[" "$LOG" 2>/dev/null | tail -1)
    
    echo "[$(date)] Running | Completed: $COMPLETED/7 | Decoded: $DECODED | $CURRENT" >> "$MLOG"
    sleep 600  # 10 minutes
done

echo "=== Tuning Monitor Ended $(date) ===" >> "$MLOG"
