#!/usr/bin/env bash
# Weekend fine-tuning launcher for VSP-LLM.
#
# Usage:
#   bash scripts/run_weekend_finetune.sh <experiment_name> <output_dir>
#
# Examples:
#   bash scripts/run_weekend_finetune.sh finetune_A_r16 /home/ubuntu/finetune_output_r16
#   bash scripts/run_weekend_finetune.sh finetune_B_r64 /home/ubuntu/finetune_output_r64
#
# For smoke test (50 updates):
#   SMOKE_TEST=1 bash scripts/run_weekend_finetune.sh smoke_r16 /tmp/finetune_smoke_r16

set -euo pipefail

EXP_NAME="${1:?Usage: $0 <experiment_name> <output_dir>}"
OUT_DIR="${2:?Usage: $0 <experiment_name> <output_dir>}"

# Paths
DATA_DIR="/home/ubuntu/finetune_data"
VSP_LLM_ROOT="/home/ubuntu/VSP-LLM"
LLM_PATH="${VSP_LLM_ROOT}/checkpoints/Llama-2-7b-hf"
PRETRAINED_CKPT="${VSP_LLM_ROOT}/checkpoints/checkpoint_finetune.pt"
ENCODER_CKPT="${VSP_LLM_ROOT}/checkpoints/large_vox_iter5.pt"

# Smoke test override
MAX_UPDATE="${SMOKE_TEST:+50}"
MAX_UPDATE="${MAX_UPDATE:-3000}"
SAVE_INTERVAL="${SMOKE_TEST:+25}"
SAVE_INTERVAL="${SAVE_INTERVAL:-500}"

echo "=== Weekend Fine-Tuning: ${EXP_NAME} ==="
echo "Start time: $(date)"
echo "Output dir: ${OUT_DIR}"
echo "Max updates: ${MAX_UPDATE}"
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'unknown')"
echo ""

# Verify data exists
for f in train.tsv train.wrd train.cluster_counts test.tsv test.wrd test.cluster_counts dict.wrd.txt; do
    if [ ! -f "${DATA_DIR}/${f}" ]; then
        echo "ERROR: Missing ${DATA_DIR}/${f}"
        exit 1
    fi
done
echo "Data verified: ${DATA_DIR}"

# Verify checkpoints exist
for f in "${PRETRAINED_CKPT}" "${ENCODER_CKPT}"; do
    if [ ! -f "${f}" ]; then
        echo "ERROR: Missing checkpoint ${f}"
        exit 1
    fi
done
echo "Checkpoints verified"

# Verify LLM path
if [ ! -d "${LLM_PATH}" ]; then
    echo "ERROR: Missing LLM directory ${LLM_PATH}"
    exit 1
fi
echo "LLM path verified: ${LLM_PATH}"
echo ""

# Activate training environment
source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
export PYTHONPATH="${VSP_LLM_ROOT}/fairseq:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

mkdir -p "${OUT_DIR}"

echo "Starting fairseq-hydra-train..."
echo ""

fairseq-hydra-train \
    --config-dir "${VSP_LLM_ROOT}/src/conf" \
    --config-name vsp-llm-avspeech-weekend \
    common.user_dir="${VSP_LLM_ROOT}/src" \
    task.data="${DATA_DIR}" \
    task.label_dir="${DATA_DIR}" \
    task.llm_ckpt_path="${LLM_PATH}" \
    model.w2v_path="${ENCODER_CKPT}" \
    model.llm_ckpt_path="${LLM_PATH}" \
    checkpoint.finetune_from_model="${PRETRAINED_CKPT}" \
    checkpoint.save_interval_updates="${SAVE_INTERVAL}" \
    optimization.max_update="${MAX_UPDATE}" \
    hydra.run.dir="${OUT_DIR}" \
    distributed_training.distributed_world_size=1 \
    distributed_training.nprocs_per_node=1 \
    optimization.update_freq='[8]' \
    2>&1 | tee "${OUT_DIR}/training.log"

echo ""
echo "=== Training Complete: ${EXP_NAME} ==="
echo "End time: $(date)"
echo "Output: ${OUT_DIR}"
echo "Checkpoints: $(ls ${OUT_DIR}/checkpoints/*.pt 2>/dev/null | wc -l) saved"
