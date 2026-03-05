#!/usr/bin/env bash
# Full evaluation pipeline for a fine-tuned VSP-LLM checkpoint.
#
# Runs: decode → make_report.py → generate_intelligibility_scores.py
# Produces: hypo JSON, report.csv, intelligibility_scores.csv, intelligibility_summary.json
#
# Usage:
#   bash scripts/eval_finetune.sh <checkpoint_path> <result_dir> [decode_overrides...]
#
# Examples:
#   # Default decode (beam=20, lenpen=0)
#   bash scripts/eval_finetune.sh \
#       /home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt \
#       /home/ubuntu/finetune_output_r16/eval_results
#
#   # Custom decode params
#   bash scripts/eval_finetune.sh \
#       /home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt \
#       /home/ubuntu/finetune_output_r16/eval_beam5 \
#       generation.beam=5
#
# IMPORTANT: The LoRA rank in VSP-LLM/src/vsp_llm.py MUST match the checkpoint.
#   - For baseline and Exp A (r=16): ensure vsp_llm.py has r=16
#   - For Exp B (r=64): ensure vsp_llm.py has r=64

set -euo pipefail

CKPT="${1:?Usage: $0 <checkpoint_path> <result_dir> [decode_overrides...]}"
RESULT_DIR="${2:?Usage: $0 <checkpoint_path> <result_dir> [decode_overrides...]}"
shift 2
DECODE_OVERRIDES="$*"

# Paths
VSP_LLM_ROOT="/home/ubuntu/VSP-LLM"
DATA_DIR="/home/ubuntu/finetune_data"
MODEL_SRC="${VSP_LLM_ROOT}/src"
LLM_PATH="${VSP_LLM_ROOT}/checkpoints/Llama-2-7b-hf"
DATA_ROOT="${MODEL_SRC}/dataset"
TGT_DIR="${DATA_ROOT}/vsr/en"
REPORT_SCRIPT="${VSP_LLM_ROOT}/scripts/make_report.py"
IS_SCRIPT="/home/ubuntu/docs/_research-tools/generators/generate_intelligibility_scores.py"

echo "=== Fine-Tune Evaluation Pipeline ==="
echo "Checkpoint:  ${CKPT}"
echo "Result dir:  ${RESULT_DIR}"
echo "Overrides:   ${DECODE_OVERRIDES:-none}"
echo "Start time:  $(date)"
echo ""

# Verify checkpoint exists
if [ ! -f "${CKPT}" ]; then
    echo "ERROR: Checkpoint not found: ${CKPT}"
    exit 1
fi

# Verify data exists
for f in test.tsv test.wrd test.cluster_counts; do
    if [ ! -f "${DATA_DIR}/${f}" ]; then
        echo "ERROR: Missing ${DATA_DIR}/${f}"
        exit 1
    fi
done

# Verify scoring scripts exist
if [ ! -f "${REPORT_SCRIPT}" ]; then
    echo "ERROR: Missing ${REPORT_SCRIPT}"
    exit 1
fi
if [ ! -f "${IS_SCRIPT}" ]; then
    echo "ERROR: Missing ${IS_SCRIPT}"
    exit 1
fi

# Symlink val data into the format VSP-LLM expects
mkdir -p "${TGT_DIR}"
for f in test.tsv test.wrd test.cluster_counts; do
    [ -L "${TGT_DIR}/${f}" ] || [ -f "${TGT_DIR}/${f}" ] && rm -f "${TGT_DIR}/${f}"
    ln -s "${DATA_DIR}/${f}" "${TGT_DIR}/${f}"
done
echo "Symlinked val data to ${TGT_DIR}"

# Activate environment
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
export PYTHONPATH="${VSP_LLM_ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

mkdir -p "${RESULT_DIR}"

# ─── Stage 1: Decode ────────────────────────────────────────────────
echo ""
echo "=== Stage 1/3: Decode ==="
echo ""

CUDA_VISIBLE_DEVICES=0 python3 -B "${MODEL_SRC}/vsp_llm_decode.py" \
    --config-dir "${MODEL_SRC}/conf" \
    --config-name s2s_decode \
    common.user_dir="${MODEL_SRC}" \
    dataset.gen_subset=test \
    override.data="${TGT_DIR}" \
    override.label_dir="${TGT_DIR}" \
    generation.beam=20 \
    generation.lenpen=0 \
    dataset.max_tokens=3000 \
    override.eval_bleu=false \
    override.llm_ckpt_path="${LLM_PATH}" \
    common_eval.path="${CKPT}" \
    common_eval.results_path="${RESULT_DIR}" \
    ${DECODE_OVERRIDES} \
    2>&1 | tee "${RESULT_DIR}/decode.log"

# Find the hypo JSON
HYPO_FILE=$(ls "${RESULT_DIR}"/hypo-*.json 2>/dev/null | head -1)
if [ -z "${HYPO_FILE}" ]; then
    echo "ERROR: No hypo-*.json found in ${RESULT_DIR}"
    exit 1
fi
echo ""
echo "Decode complete: ${HYPO_FILE}"
SEGMENTS=$(python3 -c "import json; print(len(json.load(open('${HYPO_FILE}'))['utt_id']))" 2>/dev/null || echo "unknown")
echo "Segments decoded: ${SEGMENTS}"

# Find decode params if available
PARAMS_FILE=$(ls "${RESULT_DIR}"/decode_params-*.json 2>/dev/null | head -1)

# ─── Stage 2: Report (WER, WWER, NEA F1) ───────────────────────────
echo ""
echo "=== Stage 2/3: Report Generation (WER, WWER, NEA F1) ==="
echo ""

REPORT_DIR="${RESULT_DIR}/report"
mkdir -p "${REPORT_DIR}"

REPORT_CMD="python3 ${REPORT_SCRIPT} --jsonl ${HYPO_FILE} --out_dir ${REPORT_DIR}"
if [ -n "${PARAMS_FILE}" ]; then
    REPORT_CMD="${REPORT_CMD} --params ${PARAMS_FILE}"
fi

eval "${REPORT_CMD}" 2>&1 | tee "${RESULT_DIR}/report.log"

REPORT_CSV="${REPORT_DIR}/report.csv"
if [ ! -f "${REPORT_CSV}" ]; then
    echo "ERROR: report.csv not generated in ${REPORT_DIR}"
    exit 1
fi
echo ""
echo "Report generated: ${REPORT_CSV}"

# ─── Stage 3: Intelligibility Scoring ──────────────────────────────
echo ""
echo "=== Stage 3/3: Intelligibility Scoring ==="
echo ""

IS_DIR="${RESULT_DIR}/intelligibility"
mkdir -p "${IS_DIR}"

python3 "${IS_SCRIPT}" \
    --csv "${REPORT_CSV}" \
    --out_dir "${IS_DIR}" \
    --device auto \
    2>&1 | tee "${RESULT_DIR}/is_scoring.log"

IS_CSV="${IS_DIR}/intelligibility_scores.csv"
IS_SUMMARY="${IS_DIR}/intelligibility_summary.json"

if [ ! -f "${IS_SUMMARY}" ]; then
    echo "WARNING: intelligibility_summary.json not generated. IS scoring may have failed."
    echo "Check ${RESULT_DIR}/is_scoring.log for errors."
fi

# ─── Summary ────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "=== Evaluation Complete ==="
echo "========================================="
echo "End time: $(date)"
echo ""

# Display WER if available
if ls "${RESULT_DIR}"/wer.* 1>/dev/null 2>&1; then
    echo "--- WER (from decode) ---"
    cat "${RESULT_DIR}"/wer.*
    echo ""
fi

# Display IS summary if available
if [ -f "${IS_SUMMARY}" ]; then
    echo "--- Intelligibility Summary ---"
    python3 -c "
import json
s = json.load(open('${IS_SUMMARY}'))
print(f'  Mean IS:            {s.get(\"mean_is\", \"N/A\")}')
print(f'  Median IS:          {s.get(\"median_is\", \"N/A\")}')
print(f'  Properly Captured:  {s.get(\"properly_captured_pct\", \"N/A\")}%')
print(f'  Segments:           {s.get(\"n_segments\", \"N/A\")}')
dist = s.get('tier_distribution', {})
for tier in ['5_excellent', '4_good', '3_fair', '2_poor', '1_failed']:
    info = dist.get(tier, {})
    print(f'  Tier {tier}: {info.get(\"count\", \"?\")} ({info.get(\"pct\", \"?\"):.1f}%)')
" 2>/dev/null || echo "  (Could not parse summary)"
    echo ""
fi

echo "Files produced:"
echo "  Decode:          ${HYPO_FILE}"
echo "  Report CSV:      ${REPORT_CSV}"
[ -f "${IS_CSV}" ] && echo "  IS Scores CSV:   ${IS_CSV}"
[ -f "${IS_SUMMARY}" ] && echo "  IS Summary JSON: ${IS_SUMMARY}"
echo ""
echo "Full results in: ${RESULT_DIR}/"
