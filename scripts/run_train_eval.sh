#!/usr/bin/env bash
# Evaluate all 3 models (Baseline, Exp A, Exp B) on the TRAINING data
# to measure overfitting in IS/WER/LLM-judge terms.
#
# Strategy: eval_finetune.sh expects test.{tsv,wrd,cluster_counts}.
# We create a temp data dir with train files renamed as test files,
# then point the eval script at it.
#
# Usage:
#   bash scripts/run_train_eval.sh
#
# Prerequisites:
#   - GPU must be free
#   - vsp_llm.py.bak.r16 must exist

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────

VSP_LLM_PY="/home/ubuntu/VSP-LLM/src/vsp_llm.py"
VSP_LLM_BAK_R16="/home/ubuntu/VSP-LLM/src/vsp_llm.py.bak.r16"

ORIG_DATA_DIR="/home/ubuntu/finetune_data"
TRAIN_DATA_DIR="/home/ubuntu/finetune_data/train_as_test"

BASELINE_CKPT="/home/ubuntu/VSP-LLM/checkpoints/checkpoint_finetune.pt"
EXPA_CKPT="/home/ubuntu/finetune_output_r16/checkpoints/checkpoint_best.pt"
EXPB_CKPT="/home/ubuntu/finetune_output_r64/checkpoints/checkpoint_best.pt"

BASELINE_OUT="/home/ubuntu/finetune_eval_baseline_sweep/train_eval"
EXPA_OUT="/home/ubuntu/finetune_output_r16/eval_sweep/train_eval"
EXPB_OUT="/home/ubuntu/finetune_output_r64/eval_sweep/train_eval"

EVAL_SCRIPT="/home/ubuntu/scripts/eval_finetune.sh"
LOG_FILE="/home/ubuntu/train_eval_master.log"

# ─── Helper Functions ───────────────────────────────────────────────

set_lora_r16() {
    echo "[CONFIG] Setting vsp_llm.py to r=16, alpha=32"
    if [ -f "${VSP_LLM_BAK_R16}" ]; then
        cp "${VSP_LLM_BAK_R16}" "${VSP_LLM_PY}"
    else
        sed -i 's/r=64/r=16/g; s/lora_alpha=128/lora_alpha=32/g' "${VSP_LLM_PY}"
    fi
    verify_lora_rank 16
}

set_lora_r64() {
    echo "[CONFIG] Setting vsp_llm.py to r=64, alpha=128"
    sed -i 's/r=16/r=64/g; s/lora_alpha=32/lora_alpha=128/g' "${VSP_LLM_PY}"
    verify_lora_rank 64
}

verify_lora_rank() {
    local expected_r="$1"
    local actual_r
    actual_r=$(grep -oP 'r=\K[0-9]+' "${VSP_LLM_PY}" | head -1)
    if [ "${actual_r}" != "${expected_r}" ]; then
        echo "ERROR: Expected r=${expected_r} but found r=${actual_r}"
        exit 1
    fi
    echo "[CONFIG] Verified: r=${actual_r}"
}

check_gpu_free() {
    local gpu_procs
    gpu_procs=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
    if [ "${gpu_procs}" -gt 0 ]; then
        echo "ERROR: GPU is in use by ${gpu_procs} process(es)."
        nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null
        exit 1
    fi
    echo "[CHECK] GPU is free"
}

# ─── Prepare Train Data as Test ─────────────────────────────────────

echo "╔═══════════════════════════════════════════════════╗"
echo "║   Training Set Evaluation (3 Models × 1,273 seg) ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Start time: $(date)"
echo "Log file:   ${LOG_FILE}"
echo ""

check_gpu_free

# Create temp data dir with train files renamed as test files
mkdir -p "${TRAIN_DATA_DIR}"
for ext in tsv wrd cluster_counts; do
    cp "${ORIG_DATA_DIR}/train.${ext}" "${TRAIN_DATA_DIR}/test.${ext}"
done
echo "[PREP] Created ${TRAIN_DATA_DIR} with train data as test.{tsv,wrd,cluster_counts}"
echo "  Train segments: $(( $(wc -l < "${TRAIN_DATA_DIR}/test.tsv") - 1 ))"
echo ""

# Patch eval_finetune.sh DATA_DIR for this run
# We do this by exporting an env var and using a wrapper
export FINETUNE_DATA_DIR="${TRAIN_DATA_DIR}"

# ─── Phase 1: Baseline (r=16) ──────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 1/3: Baseline on Training Data            ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r16

if [ -f "${BASELINE_OUT}/intelligibility/intelligibility_summary.json" ]; then
    echo "SKIP: Baseline train eval already complete"
    python3 -c "import json; d=json.load(open('${BASELINE_OUT}/intelligibility/intelligibility_summary.json')); print(f'  Mean IS: {d[\"mean_is\"]:.3f}')"
else
    # Temporarily swap DATA_DIR in eval_finetune.sh
    # Easier: just symlink train data directly
    TGT_DIR="/home/ubuntu/VSP-LLM/src/dataset/vsr/en"
    mkdir -p "${TGT_DIR}"
    for f in test.tsv test.wrd test.cluster_counts; do
        rm -f "${TGT_DIR}/${f}"
        ln -s "${TRAIN_DATA_DIR}/${f}" "${TGT_DIR}/${f}"
    done

    mkdir -p "${BASELINE_OUT}"
    source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
    export PYTHONPATH="/home/ubuntu/VSP-LLM/fairseq:${PYTHONPATH:-}"
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    export CUDA_VISIBLE_DEVICES=0

    echo "Decoding baseline on 1,273 training segments..."
    CUDA_VISIBLE_DEVICES=0 python3 -B /home/ubuntu/VSP-LLM/src/vsp_llm_decode.py \
        --config-dir /home/ubuntu/VSP-LLM/src/conf \
        --config-name s2s_decode \
        common.user_dir=/home/ubuntu/VSP-LLM/src \
        dataset.gen_subset=test \
        override.data="${TGT_DIR}" \
        override.label_dir="${TGT_DIR}" \
        generation.beam=20 \
        generation.lenpen=0 \
        dataset.max_tokens=3000 \
        override.eval_bleu=false \
        override.llm_ckpt_path=/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf \
        common_eval.path="${BASELINE_CKPT}" \
        common_eval.results_path="${BASELINE_OUT}" \
        2>&1 | tee "${BASELINE_OUT}/decode.log"

    # Report + IS scoring
    HYPO_FILE=$(ls "${BASELINE_OUT}"/hypo-*.json 2>/dev/null | head -1)
    if [ -n "${HYPO_FILE}" ]; then
        echo "Generating report..."
        mkdir -p "${BASELINE_OUT}/report"
        python3 /home/ubuntu/VSP-LLM/scripts/make_report.py \
            --jsonl "${HYPO_FILE}" \
            --out_dir "${BASELINE_OUT}/report" \
            2>&1 | tee "${BASELINE_OUT}/report.log"

        echo "Computing IS scores..."
        mkdir -p "${BASELINE_OUT}/intelligibility"
        python3 /home/ubuntu/docs/_research-tools/generators/generate_intelligibility_scores.py \
            --csv "${BASELINE_OUT}/report/report.csv" \
            --out_dir "${BASELINE_OUT}/intelligibility" \
            --device auto \
            2>&1 | tee "${BASELINE_OUT}/is_scoring.log"
    fi
fi

echo "Phase 1 complete at $(date)"

# ─── Phase 2: Exp A r=16 on Training Data ──────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 2/3: Exp A (r=16) on Training Data       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r16

if [ -f "${EXPA_OUT}/intelligibility/intelligibility_summary.json" ]; then
    echo "SKIP: Exp A train eval already complete"
    python3 -c "import json; d=json.load(open('${EXPA_OUT}/intelligibility/intelligibility_summary.json')); print(f'  Mean IS: {d[\"mean_is\"]:.3f}')"
else
    TGT_DIR="/home/ubuntu/VSP-LLM/src/dataset/vsr/en"
    mkdir -p "${TGT_DIR}"
    for f in test.tsv test.wrd test.cluster_counts; do
        rm -f "${TGT_DIR}/${f}"
        ln -s "${TRAIN_DATA_DIR}/${f}" "${TGT_DIR}/${f}"
    done

    mkdir -p "${EXPA_OUT}"

    echo "Decoding Exp A on 1,273 training segments..."
    CUDA_VISIBLE_DEVICES=0 python3 -B /home/ubuntu/VSP-LLM/src/vsp_llm_decode.py \
        --config-dir /home/ubuntu/VSP-LLM/src/conf \
        --config-name s2s_decode \
        common.user_dir=/home/ubuntu/VSP-LLM/src \
        dataset.gen_subset=test \
        override.data="${TGT_DIR}" \
        override.label_dir="${TGT_DIR}" \
        generation.beam=20 \
        generation.lenpen=0 \
        dataset.max_tokens=3000 \
        override.eval_bleu=false \
        override.llm_ckpt_path=/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf \
        common_eval.path="${EXPA_CKPT}" \
        common_eval.results_path="${EXPA_OUT}" \
        2>&1 | tee "${EXPA_OUT}/decode.log"

    HYPO_FILE=$(ls "${EXPA_OUT}"/hypo-*.json 2>/dev/null | head -1)
    if [ -n "${HYPO_FILE}" ]; then
        echo "Generating report..."
        mkdir -p "${EXPA_OUT}/report"
        python3 /home/ubuntu/VSP-LLM/scripts/make_report.py \
            --jsonl "${HYPO_FILE}" \
            --out_dir "${EXPA_OUT}/report" \
            2>&1 | tee "${EXPA_OUT}/report.log"

        echo "Computing IS scores..."
        mkdir -p "${EXPA_OUT}/intelligibility"
        python3 /home/ubuntu/docs/_research-tools/generators/generate_intelligibility_scores.py \
            --csv "${EXPA_OUT}/report/report.csv" \
            --out_dir "${EXPA_OUT}/intelligibility" \
            --device auto \
            2>&1 | tee "${EXPA_OUT}/is_scoring.log"
    fi
fi

echo "Phase 2 complete at $(date)"

# ─── Phase 3: Exp B r=64 on Training Data ──────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Phase 3/3: Exp B (r=64) on Training Data       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

set_lora_r64

if [ -f "${EXPB_OUT}/intelligibility/intelligibility_summary.json" ]; then
    echo "SKIP: Exp B train eval already complete"
    python3 -c "import json; d=json.load(open('${EXPB_OUT}/intelligibility/intelligibility_summary.json')); print(f'  Mean IS: {d[\"mean_is\"]:.3f}')"
else
    TGT_DIR="/home/ubuntu/VSP-LLM/src/dataset/vsr/en"
    mkdir -p "${TGT_DIR}"
    for f in test.tsv test.wrd test.cluster_counts; do
        rm -f "${TGT_DIR}/${f}"
        ln -s "${TRAIN_DATA_DIR}/${f}" "${TGT_DIR}/${f}"
    done

    mkdir -p "${EXPB_OUT}"

    echo "Decoding Exp B on 1,273 training segments..."
    CUDA_VISIBLE_DEVICES=0 python3 -B /home/ubuntu/VSP-LLM/src/vsp_llm_decode.py \
        --config-dir /home/ubuntu/VSP-LLM/src/conf \
        --config-name s2s_decode \
        common.user_dir=/home/ubuntu/VSP-LLM/src \
        dataset.gen_subset=test \
        override.data="${TGT_DIR}" \
        override.label_dir="${TGT_DIR}" \
        generation.beam=20 \
        generation.lenpen=0 \
        dataset.max_tokens=3000 \
        override.eval_bleu=false \
        override.llm_ckpt_path=/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf \
        common_eval.path="${EXPB_CKPT}" \
        common_eval.results_path="${EXPB_OUT}" \
        2>&1 | tee "${EXPB_OUT}/decode.log"

    HYPO_FILE=$(ls "${EXPB_OUT}"/hypo-*.json 2>/dev/null | head -1)
    if [ -n "${HYPO_FILE}" ]; then
        echo "Generating report..."
        mkdir -p "${EXPB_OUT}/report"
        python3 /home/ubuntu/VSP-LLM/scripts/make_report.py \
            --jsonl "${HYPO_FILE}" \
            --out_dir "${EXPB_OUT}/report" \
            2>&1 | tee "${EXPB_OUT}/report.log"

        echo "Computing IS scores..."
        mkdir -p "${EXPB_OUT}/intelligibility"
        python3 /home/ubuntu/docs/_research-tools/generators/generate_intelligibility_scores.py \
            --csv "${EXPB_OUT}/report/report.csv" \
            --out_dir "${EXPB_OUT}/intelligibility" \
            --device auto \
            2>&1 | tee "${EXPB_OUT}/is_scoring.log"
    fi
fi

echo "Phase 3 complete at $(date)"

# ─── Restore r=16 ──────────────────────────────────────────────────

set_lora_r16
echo "[RESTORE] vsp_llm.py restored to r=16"

# ─── Summary ────────────────────────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   Training Set Evaluation Complete                ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "End time: $(date)"
echo ""

echo "Results:"
for label_out in "Baseline:${BASELINE_OUT}" "ExpA_r16:${EXPA_OUT}" "ExpB_r64:${EXPB_OUT}"; do
    label="${label_out%%:*}"
    out_dir="${label_out#*:}"
    if [ -f "${out_dir}/intelligibility/intelligibility_summary.json" ]; then
        is_val=$(python3 -c "import json; d=json.load(open('${out_dir}/intelligibility/intelligibility_summary.json')); print(f'{d[\"mean_is\"]:.3f}')" 2>/dev/null || echo "?")
        echo "  ${label}: IS=${is_val} → ${out_dir}"
    else
        echo "  ${label}: FAILED → ${out_dir}"
    fi
done

echo ""
echo "Compare with val results:"
echo "  Baseline val: IS=2.487"
echo "  ExpA val:     IS=2.312"
echo "  ExpB val:     IS=2.023"
echo ""
echo "Log: ${LOG_FILE}"
