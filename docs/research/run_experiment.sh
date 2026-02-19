#!/usr/bin/env bash
set -euo pipefail

# Usage: bash run_experiment.sh <exp_name> [hydra overrides...]
# Example: bash run_experiment.sh exp_B generation.do_sample=false
#          bash run_experiment.sh exp_D generation.do_sample=false generation.lenpen=1.0

EXP_NAME="${1:?Usage: run_experiment.sh <exp_name> [hydra overrides...]}"
shift
EXTRA_OVERRIDES=("$@")

echo "=============================================="
echo "  Experiment: ${EXP_NAME}"
echo "  Overrides: ${EXTRA_OVERRIDES[*]:-none}"
echo "=============================================="

# Paths
ROOT="/home/ubuntu/VSP-LLM"
MODEL_SRC="${ROOT}/src"
TUNING_DATA="/home/ubuntu/tuning_results/decode_dataset"
EXP_DIR="/home/ubuntu/tuning_results/${EXP_NAME}"
RESULT_DIR="${EXP_DIR}/decode_output"
LLM_PATH="${ROOT}/checkpoints/Llama-2-7b-hf"
MODEL_PATH="${ROOT}/checkpoints/checkpoint_finetune.pt"

mkdir -p "${EXP_DIR}" "${RESULT_DIR}"

# Point dataset symlinks to our 100-video subset
TGT_DIR="${MODEL_SRC}/dataset/vsr/en"
mkdir -p "${TGT_DIR}"

for ext in tsv wrd cluster_counts; do
    for split in train test; do
        rm -f "${TGT_DIR}/${split}.${ext}"
        ln -sf "${TUNING_DATA}/${split}.${ext}" "${TGT_DIR}/${split}.${ext}"
    done
done

DATA_PATH="${TGT_DIR}"

echo "Dataset: ${TUNING_DATA} ($(wc -l < "${TUNING_DATA}/train.wrd") segments)"
echo "Output:  ${RESULT_DIR}"

# Activate venv
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate

# Run decode with experiment-specific overrides
export PYTHONPATH="${ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo
echo ">>> Starting decode..."
CUDA_VISIBLE_DEVICES=0 python -B ${MODEL_SRC}/vsp_llm_decode.py \
    --config-dir ${MODEL_SRC}/conf \
    --config-name s2s_decode \
        common.user_dir=${MODEL_SRC} \
        dataset.gen_subset=test \
        override.data=${DATA_PATH} \
        override.label_dir=${DATA_PATH} \
        generation.beam=20 \
        generation.lenpen=0 \
        dataset.max_tokens=3000 \
        override.eval_bleu=false \
        override.llm_ckpt_path=${LLM_PATH} \
        common_eval.path=${MODEL_PATH} \
        common_eval.results_path=${RESULT_DIR} \
        ${EXTRA_OVERRIDES[@]:+"${EXTRA_OVERRIDES[@]}"}

echo
echo ">>> Decode complete. Generating report..."

# Find the hypo JSON
HYPO_JSON=$(ls -t "${RESULT_DIR}"/hypo-*.json 2>/dev/null | head -1)
if [[ -z "$HYPO_JSON" ]]; then
    echo "ERROR: No hypo JSON found in ${RESULT_DIR}"
    deactivate
    exit 1
fi

# Generate report using make_report.py
python "${ROOT}/scripts/make_report.py" \
    --jsonl "${HYPO_JSON}" \
    --out_dir "${EXP_DIR}/report"

deactivate

# Save experiment config snapshot
cat > "${EXP_DIR}/config.json" << JSONEOF
{
  "experiment": "${EXP_NAME}",
  "date": "$(date -Iseconds)",
  "overrides": [$(if [[ ${#EXTRA_OVERRIDES[@]} -gt 0 ]]; then printf '"%s",' "${EXTRA_OVERRIDES[@]}" | sed 's/,$//'; fi)],
  "segments": $(wc -l < "${TUNING_DATA}/train.wrd"),
  "hypo_json": "${HYPO_JSON}"
}
JSONEOF

echo
echo ">>> Experiment ${EXP_NAME} complete!"
echo "    Report: ${EXP_DIR}/report/"
echo "    Config: ${EXP_DIR}/config.json"
