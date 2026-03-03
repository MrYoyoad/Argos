#!/usr/bin/env bash
# Evaluate multiple checkpoints from a single experiment to study
# the correlation between validation accuracy and Intelligibility Score (IS).
#
# Runs eval_finetune.sh (decode → report → IS scoring) on each checkpoint
# using the default decode config (beam=20, lenpen=0).
#
# Usage:
#   bash scripts/eval_checkpoint_correlation.sh <label> <ckpt_dir> <out_dir> [existing_best_dir]
#
# Arguments:
#   label            - Experiment label (e.g., "ExpA_r16", "ExpB_r64")
#   ckpt_dir         - Directory containing checkpoint files
#   out_dir          - Base output directory for correlation results
#   existing_best_dir - (Optional) Path to existing eval of checkpoint_best.pt
#                       If provided, results are symlinked instead of re-decoded
#
# Example:
#   bash scripts/eval_checkpoint_correlation.sh ExpA_r16 \
#       /home/ubuntu/finetune_output_r16/checkpoints \
#       /home/ubuntu/finetune_output_r16/checkpoint_correlation \
#       /home/ubuntu/finetune_output_r16/eval_sweep/default
#
# IMPORTANT: The LoRA rank in VSP-LLM/src/vsp_llm.py MUST match the checkpoint
# rank BEFORE running this script. The master orchestrator handles this.

set -euo pipefail

LABEL="${1:?Usage: $0 <label> <ckpt_dir> <out_dir> [existing_best_dir]}"
CKPT_DIR="${2:?Usage: $0 <label> <ckpt_dir> <out_dir> [existing_best_dir]}"
OUT_DIR="${3:?Usage: $0 <label> <ckpt_dir> <out_dir> [existing_best_dir]}"
EXISTING_BEST="${4:-}"

EVAL_SCRIPT="/home/ubuntu/scripts/eval_finetune.sh"

# Checkpoints to evaluate (update number → filename)
# Skip checkpoint_16_2500.pt — 5 data points is enough for correlation
declare -A CHECKPOINTS=(
    [320]="checkpoint_best.pt"
    [1000]="checkpoint_7_1000.pt"
    [1500]="checkpoint_10_1500.pt"
    [2000]="checkpoint_13_2000.pt"
    [3000]="checkpoint_19_3000.pt"
)

# Sorted order for iteration
SORTED_UPDATES=(320 1000 1500 2000 3000)

echo "╔═══════════════════════════════════════════════════╗"
echo "║   Checkpoint-IS Correlation Study: ${LABEL}"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Checkpoint dir:   ${CKPT_DIR}"
echo "Output dir:       ${OUT_DIR}"
echo "Existing best:    ${EXISTING_BEST:-none}"
echo "Start time:       $(date)"
echo ""

mkdir -p "${OUT_DIR}"

# ─── Pre-flight: verify all checkpoint files exist ────────────────
echo "Checking checkpoints..."
MISSING=0
for update in "${SORTED_UPDATES[@]}"; do
    ckpt_file="${CKPT_DIR}/${CHECKPOINTS[$update]}"
    if [ ! -f "${ckpt_file}" ]; then
        echo "  MISSING: ${ckpt_file}"
        MISSING=$((MISSING + 1))
    else
        size=$(du -h "${ckpt_file}" | cut -f1)
        echo "  OK: ${CHECKPOINTS[$update]} (${size})"
    fi
done

if [ "${MISSING}" -gt 0 ]; then
    echo ""
    echo "WARNING: ${MISSING} checkpoint(s) missing. Will skip those."
fi
echo ""

# ─── Evaluate each checkpoint ────────────────────────────────────
COMPLETED=0
TOTAL=${#SORTED_UPDATES[@]}

for update in "${SORTED_UPDATES[@]}"; do
    COMPLETED=$((COMPLETED + 1))
    ckpt_name="${CHECKPOINTS[$update]}"
    ckpt_file="${CKPT_DIR}/${ckpt_name}"
    result_dir="${OUT_DIR}/ckpt_${update}"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "║ [${COMPLETED}/${TOTAL}] Update ${update}: ${ckpt_name}"
    echo "║   Output: ${result_dir}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Skip if checkpoint doesn't exist
    if [ ! -f "${ckpt_file}" ]; then
        echo "SKIP: Checkpoint not found"
        echo ""
        continue
    fi

    # For checkpoint_best.pt (update 320), reuse existing results if available
    if [ "${update}" = "320" ] && [ -n "${EXISTING_BEST}" ]; then
        if [ -f "${EXISTING_BEST}/intelligibility/intelligibility_summary.json" ]; then
            echo "REUSE: Linking existing results from ${EXISTING_BEST}"
            mkdir -p "${result_dir}"
            # Symlink the entire existing eval directory contents
            for item in "${EXISTING_BEST}"/*; do
                base=$(basename "${item}")
                [ -e "${result_dir}/${base}" ] && rm -rf "${result_dir}/${base}"
                ln -s "${item}" "${result_dir}/${base}"
            done
            mean_is=$(python3 -c "import json; s=json.load(open('${EXISTING_BEST}/intelligibility/intelligibility_summary.json')); print(f'{s.get(\"mean_is\",0):.3f}')" 2>/dev/null)
            echo "  Mean IS: ${mean_is}"
            echo ""
            continue
        else
            echo "WARNING: Existing best dir provided but no IS summary found. Will re-decode."
        fi
    fi

    # Skip if already evaluated (idempotent)
    if [ -f "${result_dir}/intelligibility/intelligibility_summary.json" ]; then
        mean_is=$(python3 -c "import json; s=json.load(open('${result_dir}/intelligibility/intelligibility_summary.json')); print(f'{s.get(\"mean_is\",0):.3f}')" 2>/dev/null)
        echo "SKIP: Already evaluated (IS=${mean_is})"
        echo ""
        continue
    fi

    # Run full eval pipeline
    echo "Running eval_finetune.sh..."
    echo ""
    bash "${EVAL_SCRIPT}" "${ckpt_file}" "${result_dir}"
    echo ""

    # Verify output
    if [ -f "${result_dir}/intelligibility/intelligibility_summary.json" ]; then
        mean_is=$(python3 -c "import json; s=json.load(open('${result_dir}/intelligibility/intelligibility_summary.json')); print(f'{s.get(\"mean_is\",0):.3f}')" 2>/dev/null)
        echo "SUCCESS: Update ${update} → IS=${mean_is}"
    else
        echo "WARNING: IS scoring may have failed for update ${update}"
    fi
    echo ""
done

# ─── Summary ──────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Checkpoint Correlation: ${LABEL} Complete"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "End time: $(date)"
echo ""
echo "Results by checkpoint:"
for update in "${SORTED_UPDATES[@]}"; do
    result_dir="${OUT_DIR}/ckpt_${update}"
    summary="${result_dir}/intelligibility/intelligibility_summary.json"
    if [ -f "${summary}" ]; then
        mean_is=$(python3 -c "import json; s=json.load(open('${summary}')); print(f'{s.get(\"mean_is\",0):.3f}')" 2>/dev/null)
        echo "  Update ${update}: IS=${mean_is}"
    else
        echo "  Update ${update}: MISSING"
    fi
done
echo ""
