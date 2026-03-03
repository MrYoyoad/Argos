#!/usr/bin/env bash
# Waits for the current eval sweep to finish, then launches the
# checkpoint-vs-IS correlation study.
#
# Monitors the run_all_finetune_evals.sh master process (PID 225763).
# Once it exits and GPU is free, launches run_checkpoint_correlation.sh.

set -euo pipefail

MASTER_PID=225763
CORR_SCRIPT="/home/ubuntu/scripts/run_checkpoint_correlation.sh"
LOG="/home/ubuntu/correlation_watcher.log"

echo "$(date) | Watcher started. Monitoring PID ${MASTER_PID}..." | tee -a "${LOG}"

while true; do
    # Check if master process is still running
    if ! kill -0 "${MASTER_PID}" 2>/dev/null; then
        echo "$(date) | PID ${MASTER_PID} has exited." | tee -a "${LOG}"

        # Double-check GPU is free
        gpu_procs=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
        if [ "${gpu_procs}" -gt 0 ]; then
            echo "$(date) | GPU still has ${gpu_procs} process(es). Waiting 60s..." | tee -a "${LOG}"
            sleep 60
            continue
        fi

        echo "$(date) | GPU is free. Launching correlation study in 30s..." | tee -a "${LOG}"
        sleep 30

        echo "$(date) | Launching: ${CORR_SCRIPT}" | tee -a "${LOG}"
        bash "${CORR_SCRIPT}" 2>&1 | tee -a "${LOG}"

        echo "$(date) | Correlation study complete." | tee -a "${LOG}"
        exit 0
    fi

    # Log progress every 5 minutes
    gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null)
    echo "$(date) | PID ${MASTER_PID} still running. GPU: ${gpu_util}" | tee -a "${LOG}"
    sleep 300
done
