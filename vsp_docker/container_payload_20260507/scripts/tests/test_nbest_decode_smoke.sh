#!/usr/bin/env bash
# Smoke test for n-best decode (Mission 6).
# Decodes the 107-segment tuning set with VSP_NBEST=1, then verifies that:
#   - nbest-{fid}.json was written with 20 hypotheses per utterance
#   - confidence-{fid}.json still produced (top-1 path)
#   - The aggregator + variance analyzer can run end-to-end on the outputs
#
# Expected wall-clock on T4 (15 GB): ~5–10 minutes.
# Run from anywhere: bash scripts/tests/test_nbest_decode_smoke.sh
set -euo pipefail

cd /home/ubuntu

ROOT="/home/ubuntu/VSP-LLM"
MODEL_SRC="${ROOT}/src"
TUNING_DATA="/home/ubuntu/tuning_results/decode_dataset"
EXP_DIR="/home/ubuntu/tuning_results/exp_nbest_validation"
RESULT_DIR="${EXP_DIR}/decode_output"
LLM_PATH="${ROOT}/checkpoints/Llama-2-7b-hf"
MODEL_PATH="${ROOT}/checkpoints/checkpoint_finetune.pt"
mkdir -p "${RESULT_DIR}"

# Re-point the dataset symlinks at the 107-segment tuning subset.
TGT_DIR="${MODEL_SRC}/dataset/vsr/en"
mkdir -p "${TGT_DIR}"
for ext in tsv wrd cluster_counts; do
  for split in train test; do
    rm -f "${TGT_DIR}/${split}.${ext}"
    ln -sf "${TUNING_DATA}/${split}.${ext}" "${TGT_DIR}/${split}.${ext}"
  done
done

source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
export PYTHONPATH="${ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VSP_NBEST=1
export VSP_OUTPUT_SCORES=1

echo ">>> Decode start: $(date -Iseconds)"
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
        common_eval.results_path="${RESULT_DIR}" 2>&1 | tee "${EXP_DIR}/decode.log" | tail -80
echo ">>> Decode end: $(date -Iseconds)"

ls -la "${RESULT_DIR}"

# --- Post-decode validation ---
HYPO_JSON=$(ls -t "${RESULT_DIR}"/hypo-*.json 2>/dev/null | head -1)
NBEST_JSON=$(ls -t "${RESULT_DIR}"/nbest-*.json 2>/dev/null | head -1)
CONF_JSON=$(ls -t "${RESULT_DIR}"/confidence-*.json 2>/dev/null | head -1)

[ -n "${HYPO_JSON}" ]  || { echo "FAIL: no hypo-*.json"; exit 1; }
[ -n "${NBEST_JSON}" ] || { echo "FAIL: no nbest-*.json"; exit 1; }
[ -n "${CONF_JSON}" ]  || { echo "FAIL: no confidence-*.json"; exit 1; }
echo "OK: all three sidecars present."

python3 - "$NBEST_JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
n_segs = len(d)
counts = [len(v.get("hypotheses", [])) for v in d.values()]
print(f"  segments={n_segs}  hyps_per_seg: min={min(counts)} max={max(counts)} mean={sum(counts)/n_segs:.1f}")
assert min(counts) >= 1 and max(counts) <= 20, "hyp count out of range"
PY

# Aggregator
python3 /home/ubuntu/lib/nbest_aggregate.py \
    --nbest "${NBEST_JSON}" \
    --out "${EXP_DIR}/aggregated.json"

# Variance analyzer
python3 /home/ubuntu/docs/_research-tools/generators/analyze_beam_variance.py \
    --nbest "${NBEST_JSON}" \
    --aggregated "${EXP_DIR}/aggregated.json" \
    --hypo-json "${HYPO_JSON}" \
    --confidence "${CONF_JSON}" \
    --out-dir "${EXP_DIR}/beam_analysis" \
    --min-freq 3

# Report (with aggregated columns)
python3 "${ROOT}/scripts/make_report.py" \
    --jsonl "${HYPO_JSON}" \
    --out_dir "${EXP_DIR}/report" \
    --aggregated "${EXP_DIR}/aggregated.json"

echo
echo ">>> Smoke test complete: ${EXP_DIR}"
echo "    Aggregated method WERs:"
cat "${EXP_DIR}/report/aggregator_method_wer.json" 2>/dev/null || true
deactivate
