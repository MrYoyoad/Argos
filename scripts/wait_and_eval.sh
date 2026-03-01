#!/usr/bin/env bash
# Wait for Experiment B training to finish, then run all evaluations.
#
# Usage: nohup bash scripts/wait_and_eval.sh > eval_watcher.log 2>&1 &
#
# This script:
#   1. Polls for Exp B training completion (checks for checkpoint_best.pt)
#   2. Once training is done, launches run_all_finetune_evals.sh
#   3. Sends a notification file when complete

set -euo pipefail

EXPB_CKPT_DIR="/home/ubuntu/finetune_output_r64/checkpoints"
EXPB_PID_FILE="/home/ubuntu/finetune_output_r64/training.pid"
EVAL_SCRIPT="/home/ubuntu/scripts/run_all_finetune_evals.sh"
STATUS_FILE="/home/ubuntu/finetune_eval_status.txt"

echo "=== Eval Watcher Started ==="
echo "Time: $(date)"
echo "Waiting for Exp B training to complete..."
echo ""

# Wait for training to finish
while true; do
    # Check if training PID is still running
    if [ -f "${EXPB_PID_FILE}" ]; then
        TRAIN_PID=$(cat "${EXPB_PID_FILE}")
        if ! kill -0 "${TRAIN_PID}" 2>/dev/null; then
            echo "[$(date)] Training PID ${TRAIN_PID} is no longer running"
            break
        fi
    fi

    # Also check for checkpoint_best.pt
    if [ -f "${EXPB_CKPT_DIR}/checkpoint_best.pt" ]; then
        echo "[$(date)] checkpoint_best.pt found!"
        break
    fi

    # Check if any .pt file exists (training produced at least one checkpoint)
    if ls "${EXPB_CKPT_DIR}"/*.pt 1>/dev/null 2>&1; then
        # Training is saving checkpoints, check if last checkpoint exists
        if [ -f "${EXPB_CKPT_DIR}/checkpoint_last.pt" ]; then
            # Check if the PID is still running - if not, training is done
            if [ -f "${EXPB_PID_FILE}" ]; then
                TRAIN_PID=$(cat "${EXPB_PID_FILE}")
                if ! kill -0 "${TRAIN_PID}" 2>/dev/null; then
                    echo "[$(date)] Training complete (checkpoint_last.pt exists, PID stopped)"
                    break
                fi
            fi
        fi
    fi

    # Check GPU usage - if no compute processes, training has ended
    GPU_PROCS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
    if [ "${GPU_PROCS}" -eq 0 ]; then
        echo "[$(date)] No GPU processes detected - training may have finished or crashed"
        # Wait a bit to confirm it's not just a brief gap
        sleep 30
        GPU_PROCS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
        if [ "${GPU_PROCS}" -eq 0 ]; then
            echo "[$(date)] Confirmed: GPU is free"
            break
        fi
    fi

    sleep 300  # Check every 5 minutes
done

echo ""
echo "=== Training Complete, Starting Evaluations ==="
echo "Time: $(date)"
echo ""

# Check what checkpoints are available
echo "Available checkpoints:"
ls -la "${EXPB_CKPT_DIR}"/*.pt 2>/dev/null || echo "  No Exp B checkpoints found"
ls -la /home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt 2>/dev/null || echo "  No Exp A checkpoint"
ls -la /home/ubuntu/VSP-LLM/checkpoints/checkpoint_finetune.pt 2>/dev/null || echo "  No baseline checkpoint"
echo ""

# Wait 60 seconds for GPU memory to fully release
echo "Waiting 60s for GPU memory release..."
sleep 60

# Run all evaluations
echo "Launching evaluation pipeline..."
echo "STARTED" > "${STATUS_FILE}"

bash "${EVAL_SCRIPT}" 2>&1

echo ""
echo "=== All Evaluations Complete ==="
echo "Time: $(date)"
echo "COMPLETE at $(date)" > "${STATUS_FILE}"
