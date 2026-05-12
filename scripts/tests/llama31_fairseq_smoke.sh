#!/bin/bash
set -e
VSP_LLM_ROOT=/home/ubuntu/VSP-LLM
DATA_PATH=/tmp/avspeech_smoke_data
LLM_PATH=/home/ubuntu/Llama-3.1-8B
PRETRAINED_MODEL_PATH=${VSP_LLM_ROOT}/checkpoints/large_vox_iter5.pt
OUT_PATH=/tmp/llama3_smoke_out2
mkdir -p "$OUT_PATH" && rm -rf "$OUT_PATH"/*

source /home/ubuntu/vsp-llm-yoad-venv/bin/activate
export PYTHONPATH="${VSP_LLM_ROOT}/fairseq:$PYTHONPATH"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd "$VSP_LLM_ROOT"
fairseq-hydra-train \
    --config-dir "${VSP_LLM_ROOT}/src/conf" \
    --config-name vsp-llm-433h-freeze \
        common.user_dir="${VSP_LLM_ROOT}/src" \
        task.data="$DATA_PATH" \
        task.label_dir="$DATA_PATH" \
        task.llm_ckpt_path="$LLM_PATH" \
        model.w2v_path="$PRETRAINED_MODEL_PATH" \
        model.llm_ckpt_path="$LLM_PATH" \
        hydra.run.dir="$OUT_PATH" \
        distributed_training.distributed_world_size=1 \
        distributed_training.nprocs_per_node=1 \
        optimization.max_update=2 \
        optimization.update_freq=[1] \
        dataset.batch_size=1 \
        dataset.num_workers=0 \
        dataset.validate_interval=999999 \
        checkpoint.save_interval_updates=999999 \
        common.log_interval=1
