#!/usr/bin/env bash
set -euo pipefail

# Run full 1,497-segment decode with winning config J:
#   lenpen=1.0, do_sample=true, temperature=0.5
#   beam=20, rep_pen=1.2, top_p=0.9

echo "=============================================="
echo "  Full Decode: Config J (winner)"
echo "  lenpen=1.0  do_sample=true  temperature=0.5"
echo "  1,497 segments / 1,396 videos"
echo "=============================================="
echo "Started: $(date)"
echo ""

# Paths
ROOT="/home/ubuntu/VSP-LLM"
MODEL_SRC="${ROOT}/src"
FULL_MANIFESTS="/home/ubuntu/english_full_results/manifests"
FULL_LABELS="/home/ubuntu/english_full_results/flat_labels"
EXP_DIR="/home/ubuntu/tuning_results/full_decode_J"
RESULT_DIR="${EXP_DIR}/decode_output"
LLM_PATH="${ROOT}/checkpoints/Llama-2-7b-hf"
MODEL_PATH="${ROOT}/checkpoints/checkpoint_finetune.pt"

mkdir -p "${EXP_DIR}" "${RESULT_DIR}"

# Set up full-dataset symlinks
TGT_DIR="${MODEL_SRC}/dataset/vsr/en"
mkdir -p "${TGT_DIR}"

# train files -> full manifests
ln -sf "${FULL_MANIFESTS}/train.tsv" "${TGT_DIR}/train.tsv"
ln -sf "${FULL_MANIFESTS}/train.wrd" "${TGT_DIR}/train.wrd"
ln -sf "${FULL_LABELS}/train.cluster_counts" "${TGT_DIR}/train.cluster_counts"

# test -> train (decode reads "test" split)
ln -sf "${TGT_DIR}/train.tsv" "${TGT_DIR}/test.tsv"
ln -sf "${TGT_DIR}/train.wrd" "${TGT_DIR}/test.wrd"
ln -sf "${TGT_DIR}/train.cluster_counts" "${TGT_DIR}/test.cluster_counts"

DATA_PATH="${TGT_DIR}"

echo "Dataset: ${FULL_MANIFESTS} ($(wc -l < "${FULL_MANIFESTS}/train.wrd") segments)"
echo "Output:  ${RESULT_DIR}"
echo ""

# Activate venv
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate

export PYTHONPATH="${ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo ">>> Starting full decode with config J..."
echo ""

CUDA_VISIBLE_DEVICES=0 python -B ${MODEL_SRC}/vsp_llm_decode.py \
    --config-dir ${MODEL_SRC}/conf \
    --config-name s2s_decode \
        common.user_dir=${MODEL_SRC} \
        dataset.gen_subset=test \
        override.data=${DATA_PATH} \
        override.label_dir=${DATA_PATH} \
        generation.beam=20 \
        generation.lenpen=1.0 \
        generation.do_sample=true \
        generation.temperature=0.5 \
        dataset.max_tokens=3000 \
        override.eval_bleu=false \
        override.llm_ckpt_path=${LLM_PATH} \
        common_eval.path=${MODEL_PATH} \
        common_eval.results_path=${RESULT_DIR}

echo ""
echo ">>> Decode complete ($(date)). Generating report..."

# Find the hypo JSON
HYPO_JSON=$(ls -t "${RESULT_DIR}"/hypo-*.json 2>/dev/null | head -1)
if [[ -z "$HYPO_JSON" ]]; then
    echo "ERROR: No hypo JSON found in ${RESULT_DIR}"
    deactivate
    exit 1
fi

echo ">>> Hypo JSON: ${HYPO_JSON}"
echo ">>> Segments decoded: $(wc -l < "${HYPO_JSON}")"

# Generate report
python "${ROOT}/scripts/make_report.py" \
    --jsonl "${HYPO_JSON}" \
    --out_dir "${EXP_DIR}/report"

deactivate

# Save config
cat > "${EXP_DIR}/config.json" << 'JSONEOF'
{
  "experiment": "full_decode_J",
  "description": "Full 1,396-video / 1,497-segment decode with winning config J",
  "config": {
    "beam": 20,
    "lenpen": 1.0,
    "do_sample": true,
    "temperature": 0.5,
    "top_p": 0.9,
    "repetition_penalty": 1.2,
    "no_repeat_ngram_size": 3
  },
  "basis": "Winner of 13-experiment tuning sweep (A-M) on 100-video sample",
  "date": "REPLACE_DATE",
  "segments": REPLACE_SEGMENTS
}
JSONEOF

# Fill in dynamic values
sed -i "s/REPLACE_DATE/$(date -Iseconds)/" "${EXP_DIR}/config.json"
sed -i "s/REPLACE_SEGMENTS/$(wc -l < "${FULL_MANIFESTS}/train.wrd")/" "${EXP_DIR}/config.json"

echo ""
echo "=============================================="
echo "  Full Decode J COMPLETE"
echo "  Finished: $(date)"
echo "  Report: ${EXP_DIR}/report/"
echo "=============================================="
