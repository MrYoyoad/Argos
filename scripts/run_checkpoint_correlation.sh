#!/usr/bin/env bash
# Master orchestrator for the checkpoint-vs-IS correlation study.
#
# Evaluates 5 checkpoints per experiment (best + 4 intermediate) to determine
# whether validation token accuracy is a reliable proxy for Intelligibility Score.
#
# Phases:
#   1. Set r=16, evaluate Exp A checkpoints
#   2. Set r=64, evaluate Exp B checkpoints
#   3. Restore r=16, generate correlation analysis
#
# Usage:
#   bash scripts/run_checkpoint_correlation.sh
#
# Prerequisites:
#   - Current eval sweep (run_all_finetune_evals.sh) must be finished
#   - GPU must be free
#   - vsp_llm.py.bak.r16 must exist

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────

VSP_LLM_PY="/home/ubuntu/VSP-LLM/src/vsp_llm.py"
VSP_LLM_BAK_R16="/home/ubuntu/VSP-LLM/src/vsp_llm.py.bak.r16"

EXPA_CKPT_DIR="/home/ubuntu/finetune_output_r16/checkpoints"
EXPB_CKPT_DIR="/home/ubuntu/finetune_output_r64/checkpoints"

EXPA_CORR_DIR="/home/ubuntu/finetune_output_r16/checkpoint_correlation"
EXPB_CORR_DIR="/home/ubuntu/finetune_output_r64/checkpoint_correlation"

# Existing default-config eval results (reuse for checkpoint_best.pt)
EXPA_EXISTING_BEST="/home/ubuntu/finetune_output_r16/eval_sweep/default"
EXPB_EXISTING_BEST="/home/ubuntu/finetune_output_r64/eval_sweep/default"

EXPA_LOG="/home/ubuntu/finetune_output_r16/hydra_train.log"
EXPB_LOG="/home/ubuntu/finetune_output_r64/hydra_train.log"

CORR_SCRIPT="/home/ubuntu/scripts/eval_checkpoint_correlation.sh"
ANALYSIS_SCRIPT="/home/ubuntu/scripts/generate_checkpoint_correlation.py"
REPORT_DIR="/home/ubuntu/docs/finetuning"

LOG_FILE="/home/ubuntu/checkpoint_correlation_master.log"

# ─── Helper Functions ───────────────────────────────────────────────

set_lora_r16() {
    echo "[CONFIG] Setting vsp_llm.py to r=16, alpha=32"
    if [ -f "${VSP_LLM_BAK_R16}" ]; then
        cp "${VSP_LLM_BAK_R16}" "${VSP_LLM_PY}"
        echo "[CONFIG] Restored from backup (r=16)"
    else
        sed -i 's/r=64/r=16/g; s/lora_alpha=128/lora_alpha=32/g' "${VSP_LLM_PY}"
        echo "[CONFIG] Edited in-place (r=16)"
    fi
    verify_lora_rank 16
}

set_lora_r64() {
    echo "[CONFIG] Setting vsp_llm.py to r=64, alpha=128"
    sed -i 's/r=16/r=64/g; s/lora_alpha=32/lora_alpha=128/g' "${VSP_LLM_PY}"
    echo "[CONFIG] Edited in-place (r=64)"
    verify_lora_rank 64
}

verify_lora_rank() {
    local expected_r="$1"
    local actual_r
    actual_r=$(grep -oP 'r=\K[0-9]+' "${VSP_LLM_PY}" | head -1)
    if [ "${actual_r}" != "${expected_r}" ]; then
        echo "ERROR: Expected r=${expected_r} but found r=${actual_r} in vsp_llm.py"
        exit 1
    fi
    echo "[CONFIG] Verified: r=${actual_r}"
}

check_gpu_free() {
    local gpu_procs
    gpu_procs=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
    if [ "${gpu_procs}" -gt 0 ]; then
        echo "ERROR: GPU is in use by ${gpu_procs} process(es). Wait for current work to finish."
        nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null
        exit 1
    fi
    echo "[CHECK] GPU is free"
}

# ─── Pre-flight Checks ─────────────────────────────────────────────

echo "╔═══════════════════════════════════════════════════╗"
echo "║   Checkpoint-vs-IS Correlation Master             ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Start time: $(date)"
echo "Log file:   ${LOG_FILE}"
echo ""

check_gpu_free

# Verify prerequisites
echo "Checking prerequisites..."
[ -f "${VSP_LLM_BAK_R16}" ] && echo "  OK: r=16 backup exists" || { echo "ERROR: No r=16 backup"; exit 1; }
[ -d "${EXPA_CKPT_DIR}" ] && echo "  OK: Exp A checkpoints exist" || { echo "ERROR: Exp A checkpoints missing"; exit 1; }
[ -d "${EXPB_CKPT_DIR}" ] && echo "  OK: Exp B checkpoints exist" || { echo "ERROR: Exp B checkpoints missing"; exit 1; }
[ -f "${EXPA_LOG}" ] && echo "  OK: Exp A training log exists" || { echo "ERROR: Exp A log missing"; exit 1; }
[ -f "${EXPB_LOG}" ] && echo "  OK: Exp B training log exists" || { echo "ERROR: Exp B log missing"; exit 1; }

# Check existing best results
if [ -f "${EXPA_EXISTING_BEST}/intelligibility/intelligibility_summary.json" ]; then
    echo "  OK: Exp A checkpoint_best.pt already evaluated (will reuse)"
else
    echo "  INFO: Exp A checkpoint_best.pt not yet evaluated (will decode)"
fi
if [ -f "${EXPB_EXISTING_BEST}/intelligibility/intelligibility_summary.json" ]; then
    echo "  OK: Exp B checkpoint_best.pt already evaluated (will reuse)"
else
    echo "  INFO: Exp B checkpoint_best.pt not yet evaluated (will decode)"
fi
echo ""

echo "Plan: 4 new checkpoints × 2 experiments = 8 evals (~1h each = ~8h total)"
echo "(Plus 2 reused from existing sweep = 10 data points total)"
echo ""

# ─── Phase 1: Exp A (r=16) ─────────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 1: Exp A (r=16) Checkpoint Correlation    ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r16
echo ""

bash "${CORR_SCRIPT}" "ExpA_r16" "${EXPA_CKPT_DIR}" "${EXPA_CORR_DIR}" "${EXPA_EXISTING_BEST}" \
    2>&1 | tee -a "${LOG_FILE}"

echo ""
echo "Phase 1 complete at $(date)"

# ─── Phase 2: Exp B (r=64) ─────────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 2: Exp B (r=64) Checkpoint Correlation    ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r64
echo ""

bash "${CORR_SCRIPT}" "ExpB_r64" "${EXPB_CKPT_DIR}" "${EXPB_CORR_DIR}" "${EXPB_EXISTING_BEST}" \
    2>&1 | tee -a "${LOG_FILE}"

echo ""
echo "Phase 2 complete at $(date)"

# ─── Phase 3: Restore r=16 and Generate Analysis ───────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 3: Correlation Analysis                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r16
echo "[RESTORE] vsp_llm.py restored to r=16 (default)"
echo ""

echo "Generating correlation analysis..."
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate

python3 "${ANALYSIS_SCRIPT}" \
    --expa_dir "${EXPA_CORR_DIR}" \
    --expb_dir "${EXPB_CORR_DIR}" \
    --expa_log "${EXPA_LOG}" \
    --expb_log "${EXPB_LOG}" \
    --out_dir "${REPORT_DIR}" \
    2>&1 | tee -a "${LOG_FILE}"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Checkpoint Correlation Study Complete            ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "End time:    $(date)"
echo ""
echo "Results:"
echo "  Exp A:     ${EXPA_CORR_DIR}/"
echo "  Exp B:     ${EXPB_CORR_DIR}/"
echo "  CSV:       ${REPORT_DIR}/checkpoint_correlation.csv"
echo "  Report:    ${REPORT_DIR}/checkpoint_correlation_report.md"
echo ""
echo "Master log:  ${LOG_FILE}"
