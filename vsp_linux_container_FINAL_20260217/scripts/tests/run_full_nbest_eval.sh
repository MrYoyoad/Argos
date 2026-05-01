#!/usr/bin/env bash
# Full 1,497-segment evaluation with VSP_NBEST=1 (Mission 6 Phase 7b).
# Reuses the existing english_full_results/ manifests and labels.
# Expected wall-clock on T4: ~14-18 hours (≈35-45s/seg given the n-best
# capture overhead — to be optimized in a follow-up).
set -euo pipefail
cd /home/ubuntu

ROOT="/home/ubuntu/VSP-LLM"
MODEL_SRC="${ROOT}/src"
DATA_SRC=/home/ubuntu/english_full_results
EXP_DIR=/home/ubuntu/english_full_nbest_eval
RESULT_DIR="${EXP_DIR}/decode_output"
LLM_PATH="${ROOT}/checkpoints/Llama-2-7b-hf"
MODEL_PATH="${ROOT}/checkpoints/checkpoint_finetune.pt"
mkdir -p "${RESULT_DIR}"

# Re-point the dataset symlinks at the 1,497-seg manifests.
TGT_DIR="${MODEL_SRC}/dataset/vsr/en"
mkdir -p "${TGT_DIR}"
for split in train test; do
  rm -f "${TGT_DIR}/${split}.tsv" "${TGT_DIR}/${split}.wrd" "${TGT_DIR}/${split}.cluster_counts"
done
ln -sf "${DATA_SRC}/manifests/train.tsv"  "${TGT_DIR}/train.tsv"
ln -sf "${DATA_SRC}/manifests/train.wrd"  "${TGT_DIR}/train.wrd"
ln -sf "${DATA_SRC}/flat_labels/train.cluster_counts" "${TGT_DIR}/train.cluster_counts"
ln -sf "${TGT_DIR}/train.tsv"             "${TGT_DIR}/test.tsv"
ln -sf "${TGT_DIR}/train.wrd"             "${TGT_DIR}/test.wrd"
ln -sf "${TGT_DIR}/train.cluster_counts"  "${TGT_DIR}/test.cluster_counts"

source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
export PYTHONPATH="${ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VSP_NBEST=1
export VSP_OUTPUT_SCORES=1
export VSP_FLUSH_EVERY=50  # checkpoint every 50 segs

echo ">>> Full nbest decode start: $(date -Iseconds)"
CUDA_VISIBLE_DEVICES=0 python -B "${MODEL_SRC}/vsp_llm_decode.py" \
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
        common_eval.path="${MODEL_PATH}" \
        common_eval.results_path="${RESULT_DIR}" 2>&1 | tee "${EXP_DIR}/decode.log"
echo ">>> Full nbest decode end: $(date -Iseconds)"

ls -la "${RESULT_DIR}"

# Post-processing
HYPO_JSON=$(ls -t "${RESULT_DIR}"/hypo-*.json 2>/dev/null | head -1)
NBEST_JSON=$(ls -t "${RESULT_DIR}"/nbest-*.json 2>/dev/null | head -1)
CONF_JSON=$(ls -t "${RESULT_DIR}"/confidence-*.json 2>/dev/null | head -1)
SEG_META=${DATA_SRC}/segment_metadata.json

# Aggregator (with seg-meta for cross-segment merge — full dataset HAS overlap)
python3 /home/ubuntu/lib/nbest_aggregate.py \
    --nbest "${NBEST_JSON}" \
    --out "${EXP_DIR}/aggregated.json" \
    ${SEG_META:+--seg-meta "${SEG_META}"}

# Variance + word-confusion analyzer
python3 /home/ubuntu/docs/_research-tools/generators/analyze_beam_variance.py \
    --nbest "${NBEST_JSON}" \
    --aggregated "${EXP_DIR}/aggregated.json" \
    --hypo-json "${HYPO_JSON}" \
    --confidence "${CONF_JSON}" \
    --out-dir "${EXP_DIR}/beam_analysis" \
    --min-freq 5

# Report (with aggregated columns)
python3 "${ROOT}/scripts/make_report.py" \
    --jsonl "${HYPO_JSON}" \
    --out_dir "${EXP_DIR}/report" \
    --aggregated "${EXP_DIR}/aggregated.json" \
    --compute-is

# IS per method
python3 /home/ubuntu/docs/_research-tools/generators/compute_aggregated_is.py \
    --hypo "${HYPO_JSON}" \
    --aggregated "${EXP_DIR}/aggregated.json" \
    --out "${EXP_DIR}/aggregated_is.json"

# Conditional / per-method calibration
python3 /home/ubuntu/docs/_research-tools/generators/per_method_confidence_analysis.py \
    --aggregated "${EXP_DIR}/aggregated.json" \
    --hypo "${HYPO_JSON}" \
    --confidence "${CONF_JSON}" \
    --baseline-csv "${EXP_DIR}/report/report.csv" \
    --out-dir "${EXP_DIR}/per_method_calibration" \
    --min-freq 5

python3 /home/ubuntu/docs/_research-tools/generators/word_confusion_conditional.py \
    --nbest "${NBEST_JSON}" \
    --hypo "${HYPO_JSON}" \
    --confidence "${CONF_JSON}" \
    --baseline-csv "${EXP_DIR}/report/report.csv" \
    --out-dir "${EXP_DIR}/conditional_analysis"

echo ">>> Full nbest evaluation complete: ${EXP_DIR}"
deactivate
