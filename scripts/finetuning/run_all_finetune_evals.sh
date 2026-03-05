#!/usr/bin/env bash
# Master orchestration: evaluate all fine-tuned checkpoints with full metrics + sweep.
#
# This script runs the complete evaluation pipeline for:
#   1. Baseline (checkpoint_finetune.pt, r=16)
#   2. Experiment A best (r=16 fine-tuned)
#   3. Experiment B best (r=64 fine-tuned)
#
# Each checkpoint is evaluated with 6 decode parameter configurations.
# Total: 18 evaluations (~30 min each = ~9 hours on T4)
#
# Usage:
#   bash scripts/run_all_finetune_evals.sh
#
# Prerequisites:
#   - Exp A training complete (checkpoint_best.pt exists)
#   - Exp B training complete (checkpoint_best.pt exists)
#   - GPU free (no training running)
#   - vsp_llm.py backed up (vsp_llm.py.bak.r16 exists)
#
# The script automatically switches vsp_llm.py between r=16 and r=64
# as needed for each checkpoint.

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────

VSP_LLM_PY="/home/ubuntu/VSP-LLM/src/vsp_llm.py"
VSP_LLM_BAK_R16="/home/ubuntu/VSP-LLM/src/vsp_llm.py.bak.r16"

BASELINE_CKPT="/home/ubuntu/VSP-LLM/checkpoints/checkpoint_finetune.pt"
EXPA_CKPT="/home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt"
EXPB_CKPT="/home/ubuntu/finetune_output_r64/checkpoints/checkpoint_best.pt"

BASELINE_SWEEP_DIR="/home/ubuntu/finetune_eval_baseline_sweep"
EXPA_SWEEP_DIR="/home/ubuntu/finetune_output_r16/eval_sweep"
EXPB_SWEEP_DIR="/home/ubuntu/finetune_output_r64/eval_sweep"

SWEEP_SCRIPT="/home/ubuntu/scripts/finetuning/eval_finetune_sweep.sh"
COMPARISON_SCRIPT="/home/ubuntu/scripts/finetuning/generate_finetune_comparison.py"
REPORT_DIR="/home/ubuntu/docs/finetuning/experiments"

LOG_FILE="/home/ubuntu/logs/finetune_eval_master.log"

# ─── Helper Functions ───────────────────────────────────────────────

set_lora_r16() {
    echo "[CONFIG] Setting vsp_llm.py to r=16, alpha=32"
    if [ -f "${VSP_LLM_BAK_R16}" ]; then
        cp "${VSP_LLM_BAK_R16}" "${VSP_LLM_PY}"
        echo "[CONFIG] Restored from backup (r=16)"
    else
        # In-place edit
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
        echo "ERROR: GPU is in use by ${gpu_procs} process(es). Wait for training to finish."
        nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null
        exit 1
    fi
    echo "[CHECK] GPU is free"
}

# ─── Pre-flight Checks ─────────────────────────────────────────────

echo "╔═══════════════════════════════════════════════════╗"
echo "║   Fine-Tuning Evaluation Master Orchestrator     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Start time: $(date)"
echo "Log file:   ${LOG_FILE}"
echo ""

# Check GPU is free
check_gpu_free

# Check checkpoints exist
echo "Checking checkpoints..."
SKIP_BASELINE=false
SKIP_EXPA=false
SKIP_EXPB=false

if [ ! -f "${BASELINE_CKPT}" ]; then
    echo "  WARNING: Baseline checkpoint not found: ${BASELINE_CKPT}"
    SKIP_BASELINE=true
else
    echo "  OK: Baseline checkpoint exists"
fi

if [ ! -f "${EXPA_CKPT}" ]; then
    echo "  WARNING: Exp A checkpoint not found: ${EXPA_CKPT}"
    SKIP_EXPA=true
else
    echo "  OK: Exp A checkpoint exists"
fi

if [ ! -f "${EXPB_CKPT}" ]; then
    echo "  WARNING: Exp B checkpoint not found: ${EXPB_CKPT}"
    SKIP_EXPB=true
else
    echo "  OK: Exp B checkpoint exists"
fi

# Check backup
if [ ! -f "${VSP_LLM_BAK_R16}" ]; then
    echo "  WARNING: No r=16 backup at ${VSP_LLM_BAK_R16}. Creating one now."
    cp "${VSP_LLM_PY}" "${VSP_LLM_BAK_R16}"
fi

echo ""

# Count total evaluations
TOTAL_EVALS=0
${SKIP_BASELINE} || TOTAL_EVALS=$((TOTAL_EVALS + 6))
${SKIP_EXPA}     || TOTAL_EVALS=$((TOTAL_EVALS + 6))
${SKIP_EXPB}     || TOTAL_EVALS=$((TOTAL_EVALS + 6))

if [ "${TOTAL_EVALS}" -eq 0 ]; then
    echo "ERROR: No checkpoints available to evaluate."
    exit 1
fi

echo "Will run ${TOTAL_EVALS} evaluations (~30 min each, ~$((TOTAL_EVALS / 2)) hours total)"
echo ""

# ─── Phase 1: Baseline + Exp A (both r=16) ─────────────────────────

if ! ${SKIP_BASELINE} || ! ${SKIP_EXPA}; then
    echo ""
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║   Phase 1: r=16 Evaluations (Baseline + Exp A)   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo ""

    set_lora_r16
    echo ""

    if ! ${SKIP_BASELINE}; then
        echo "━━━ Baseline Sweep ━━━"
        echo "Time: $(date)"
        bash "${SWEEP_SCRIPT}" "${BASELINE_CKPT}" "${BASELINE_SWEEP_DIR}" "Baseline" \
            2>&1 | tee -a "${LOG_FILE}"
        echo ""
        echo "Baseline sweep complete at $(date)"
        echo ""
    fi

    if ! ${SKIP_EXPA}; then
        echo "━━━ Experiment A Sweep ━━━"
        echo "Time: $(date)"
        bash "${SWEEP_SCRIPT}" "${EXPA_CKPT}" "${EXPA_SWEEP_DIR}" "ExpA_r16" \
            2>&1 | tee -a "${LOG_FILE}"
        echo ""
        echo "Exp A sweep complete at $(date)"
        echo ""
    fi
fi

# ─── Phase 2: Exp B (r=64) ─────────────────────────────────────────

if ! ${SKIP_EXPB}; then
    echo ""
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║   Phase 2: r=64 Evaluation (Exp B)               ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo ""

    set_lora_r64
    echo ""

    echo "━━━ Experiment B Sweep ━━━"
    echo "Time: $(date)"
    bash "${SWEEP_SCRIPT}" "${EXPB_CKPT}" "${EXPB_SWEEP_DIR}" "ExpB_r64" \
        2>&1 | tee -a "${LOG_FILE}"
    echo ""
    echo "Exp B sweep complete at $(date)"
    echo ""
fi

# ─── Phase 3: Restore r=16 and Generate Comparison ─────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 3: Comparison Report                     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r16
echo "[RESTORE] vsp_llm.py restored to r=16 (default)"
echo ""

# Build comparison command
COMPARISON_ARGS=""
${SKIP_BASELINE} || COMPARISON_ARGS="${COMPARISON_ARGS} Baseline=${BASELINE_SWEEP_DIR}"
${SKIP_EXPA}     || COMPARISON_ARGS="${COMPARISON_ARGS} ExpA_r16=${EXPA_SWEEP_DIR}"
${SKIP_EXPB}     || COMPARISON_ARGS="${COMPARISON_ARGS} ExpB_r64=${EXPB_SWEEP_DIR}"

echo "Generating comparison report..."
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate

python3 "${COMPARISON_SCRIPT}" \
    --results ${COMPARISON_ARGS} \
    --out_dir "${REPORT_DIR}" \
    2>&1 | tee -a "${LOG_FILE}"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   All Evaluations Complete                       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "End time:    $(date)"
echo "Total evals: ${TOTAL_EVALS}"
echo ""
echo "Results:"
${SKIP_BASELINE} || echo "  Baseline:  ${BASELINE_SWEEP_DIR}/"
${SKIP_EXPA}     || echo "  Exp A:     ${EXPA_SWEEP_DIR}/"
${SKIP_EXPB}     || echo "  Exp B:     ${EXPB_SWEEP_DIR}/"
echo ""
echo "Comparison:"
echo "  CSV:       ${REPORT_DIR}/finetune_comparison.csv"
echo "  Report:    ${REPORT_DIR}/comparison_report.md"
echo ""
echo "Master log:  ${LOG_FILE}"
