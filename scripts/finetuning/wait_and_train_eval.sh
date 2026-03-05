#!/usr/bin/env bash
# Waits for the correlation study to finish, then launches
# training-set evaluation for all 3 models.
#
# Monitors the correlation study master process (PID 342348).
# Once it exits and GPU is free, launches run_train_eval.sh.

set -euo pipefail

CORR_PID=342348
TRAIN_SCRIPT="/home/ubuntu/scripts/finetuning/run_train_eval.sh"
LOG="/home/ubuntu/logs/train_eval_watcher.log"

echo "$(date) | Train eval watcher started. Monitoring correlation PID ${CORR_PID}..." | tee -a "${LOG}"

while true; do
    if ! kill -0 "${CORR_PID}" 2>/dev/null; then
        echo "$(date) | PID ${CORR_PID} (correlation study) has exited." | tee -a "${LOG}"

        # Wait for GPU to be free
        gpu_procs=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
        if [ "${gpu_procs}" -gt 0 ]; then
            echo "$(date) | GPU still has ${gpu_procs} process(es). Waiting 60s..." | tee -a "${LOG}"
            sleep 60
            continue
        fi

        echo "$(date) | GPU is free. Launching train eval in 30s..." | tee -a "${LOG}"
        sleep 30

        echo "$(date) | Launching: ${TRAIN_SCRIPT}" | tee -a "${LOG}"
        bash "${TRAIN_SCRIPT}" 2>&1 | tee -a "${LOG}"

        echo "$(date) | Train eval complete." | tee -a "${LOG}"
        exit 0
    fi

    gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null)
    echo "$(date) | Correlation PID ${CORR_PID} still running. GPU: ${gpu_util}" | tee -a "${LOG}"
    sleep 300
done
