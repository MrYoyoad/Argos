#!/usr/bin/env bash
# Decode hyperparameter sweep with full metrics for fine-tuned VSP-LLM checkpoints.
#
# For each config: decode → make_report.py → generate_intelligibility_scores.py
#
# Usage:
#   bash scripts/eval_finetune_sweep.sh <checkpoint_path> <result_base_dir> <label>
#
# Examples:
#   bash scripts/eval_finetune_sweep.sh \
#       /home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt \
#       /home/ubuntu/finetune_output_r16/eval_sweep \
#       ExpA_r16
#
# IMPORTANT: The LoRA rank in VSP-LLM/src/vsp_llm.py MUST match the checkpoint.
#
# Configurations tested (6 total):
#   1. default     — beam=20, lenpen=0 (same as baseline eval)
#   2. lenpen1     — beam=20, lenpen=1.0 (encourages longer output)
#   3. beam5       — beam=5, lenpen=0 (faster, less diverse)
#   4. greedy      — beam=1 (single-pass, no search)
#   5. sample_low  — sampling temp=0.3, top_p=0.9 (low-temp stochastic)
#   6. sample_med  — sampling temp=0.5, top_p=0.9 (medium-temp stochastic)

set -euo pipefail

CKPT="${1:?Usage: $0 <checkpoint_path> <result_base_dir> <label>}"
BASE_DIR="${2:?Usage: $0 <checkpoint_path> <result_base_dir> <label>}"
LABEL="${3:?Usage: $0 <checkpoint_path> <result_base_dir> <label>}"

EVAL_SCRIPT="/home/ubuntu/scripts/eval_finetune.sh"

echo "=== Decode Hyperparameter Sweep ==="
echo "Label:      ${LABEL}"
echo "Checkpoint: ${CKPT}"
echo "Base dir:   ${BASE_DIR}"
echo "Start time: $(date)"
echo ""

# Verify eval script exists
if [ ! -f "${EVAL_SCRIPT}" ]; then
    echo "ERROR: Missing ${EVAL_SCRIPT}"
    exit 1
fi

mkdir -p "${BASE_DIR}"

# Define sweep configurations: name|extra_overrides
declare -a CONFIGS=(
    "default|"
    "lenpen1|generation.lenpen=1.0"
    "beam5|generation.beam=5"
    "greedy|generation.beam=1"
    "sample_low|generation.do_sample=true generation.temperature=0.3 generation.top_p=0.9"
    "sample_med|generation.do_sample=true generation.temperature=0.5 generation.top_p=0.9"
)

# Summary CSV header
SUMMARY_CSV="${BASE_DIR}/sweep_summary.csv"
echo "config,label,overrides,segments,mean_is,median_is,properly_captured_pct,mean_wer,mean_wwer,mean_nea_f1,hallucination_rate,empty_pct" > "${SUMMARY_CSV}"

TOTAL=${#CONFIGS[@]}
IDX=0

for entry in "${CONFIGS[@]}"; do
    IDX=$((IDX + 1))
    CONFIG_NAME="${entry%%|*}"
    OVERRIDES="${entry#*|}"
    RESULT_DIR="${BASE_DIR}/${CONFIG_NAME}"

    echo ""
    echo "╔═══════════════════════════════════════════╗"
    echo "║ [${IDX}/${TOTAL}] Config: ${CONFIG_NAME}"
    [ -n "${OVERRIDES}" ] && echo "║   Overrides: ${OVERRIDES}"
    echo "║   Output: ${RESULT_DIR}"
    echo "║   Time: $(date)"
    echo "╚═══════════════════════════════════════════╝"
    echo ""

    # Run full eval pipeline (decode + report + IS scoring)
    bash "${EVAL_SCRIPT}" "${CKPT}" "${RESULT_DIR}" ${OVERRIDES} || {
        echo "WARNING: Config ${CONFIG_NAME} failed. Continuing with next config."
        echo "${CONFIG_NAME},${LABEL},${OVERRIDES},0,,,,,,,," >> "${SUMMARY_CSV}"
        continue
    }

    # Extract metrics from IS summary
    IS_SUMMARY="${RESULT_DIR}/intelligibility/intelligibility_summary.json"
    if [ -f "${IS_SUMMARY}" ]; then
        python3 -c "
import json, csv, sys
s = json.load(open('${IS_SUMMARY}'))
dist = s.get('tier_distribution', {})
n = s.get('n_segments', 0)
empty = s.get('n_empty_hyp', 0)
empty_pct = (empty / n * 100) if n > 0 else 0

# Get hallucination info from failure modes
fm = s.get('failure_modes', {})
hall = fm.get('hallucination', {}).get('count', 0)
# Hallucination rate is vs segments with WER data (non-empty)
n_nonempty = n - empty
hall_rate = (hall / n_nonempty * 100) if n_nonempty > 0 else 0

row = [
    '${CONFIG_NAME}',
    '${LABEL}',
    '${OVERRIDES}',
    str(n),
    f\"{s.get('mean_is', ''):.3f}\",
    f\"{s.get('median_is', ''):.3f}\",
    f\"{s.get('properly_captured_pct', ''):.1f}\",
    f\"{s.get('signal_stats', {}).get('inverse_wer', {}).get('mean', '')}\",
    f\"{s.get('signal_stats', {}).get('inverse_wwer', {}).get('mean', '')}\",
    f\"{s.get('signal_stats', {}).get('nea_f1', {}).get('mean', '')}\",
    f'{hall_rate:.1f}',
    f'{empty_pct:.1f}',
]
print(','.join(row))
" >> "${SUMMARY_CSV}" 2>/dev/null || {
            # Fallback: try simpler extraction
            echo "${CONFIG_NAME},${LABEL},${OVERRIDES},,,,,,,,,extraction_failed" >> "${SUMMARY_CSV}"
        }
    else
        echo "${CONFIG_NAME},${LABEL},${OVERRIDES},0,,,,,,,," >> "${SUMMARY_CSV}"
    fi

    echo ""
    echo "[${IDX}/${TOTAL}] ${CONFIG_NAME} complete at $(date)"
done

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║ Sweep Complete                            ║"
echo "╚═══════════════════════════════════════════╝"
echo "End time: $(date)"
echo ""
echo "Summary CSV: ${SUMMARY_CSV}"
echo ""
column -t -s',' "${SUMMARY_CSV}" 2>/dev/null || cat "${SUMMARY_CSV}"
echo ""
echo "Detailed results in subdirectories under: ${BASE_DIR}/"
