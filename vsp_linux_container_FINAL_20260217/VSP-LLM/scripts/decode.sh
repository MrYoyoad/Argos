#! /bin/bash
# Copyright (c) Meta Platforms, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

LANG=en
# NEW: export language for Python side
export VSP_LANG="${LANG}"

# set paths
ROOT=$(dirname "$(dirname "$(readlink -fm "$0")")")
MODEL_SRC=${ROOT}/src
LLM_PATH=${ROOT}/checkpoints/Llama-2-7b-hf   # path to llama checkpoint
DATA_ROOT=${MODEL_SRC}/dataset   # path to test dataset dir

# Auto-detect paths (works in any installation location)
MODEL_PATH=${ROOT}/checkpoints/checkpoint_finetune.pt
OUT_PATH=${ROOT}/decode/vsr/en

# fix variables based on langauge
if [[ $LANG == *"-"* ]] ; then
    TASK="vst"
    IFS='-' read -r SRC TGT <<< ${LANG}
    USE_BLEU=true
    DATA_PATH=${DATA_ROOT}/${TASK}/${SRC}/${TGT}

else
    TASK="vsr"
    TGT=${LANG}
    USE_BLEU=false
    DATA_PATH=${DATA_ROOT}/${TASK}/${LANG}
fi

# start decoding
export PYTHONPATH="${ROOT}/fairseq:$PYTHONPATH"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Auto-patch fairseq GenerationConfig if fields are missing (Bug 11/19/22)
# Must run AFTER PYTHONPATH is set so it patches the fairseq that decode will use
python3 -c "
import fairseq.dataclass.configs as c
patched = False
src = c.__file__
with open(src) as f: content = f.read()

# Patch 1: max_len field (Bug 11/19)
if not hasattr(c.GenerationConfig, 'max_len'):
    target = '    min_len: int'
    patch = '    max_len: int = field(\n        default=0,\n        metadata={\n            \"help\": \"maximum length of generated sequence (hard cap), 0 = use model default\"\n        },\n    )\n    min_len: int'
    if target in content:
        content = content.replace(target, patch)
        patched = True
        print('Patched: max_len')
    else:
        print('WARNING: Could not find min_len anchor for max_len patch')
else:
    print('OK: max_len')

# Patch 2: repetition_penalty field (Bug 22 - inference tuning)
if not hasattr(c.GenerationConfig, 'repetition_penalty'):
    target = '    no_repeat_ngram_size: int'
    patch = '    repetition_penalty: float = field(\n        default=1.0,\n        metadata={\n            \"help\": \"repetition penalty (CTRL paper, Keskar 2019). 1.0=disabled, >1.0 penalizes repeated tokens\"\n        },\n    )\n    no_repeat_ngram_size: int'
    if target in content:
        content = content.replace(target, patch)
        patched = True
        print('Patched: repetition_penalty')
    else:
        print('WARNING: Could not find no_repeat_ngram_size anchor for repetition_penalty patch')
else:
    print('OK: repetition_penalty')

if patched:
    with open(src, 'w') as f: f.write(content)
    print('Wrote patches to: ' + src)
" || echo "WARNING: fairseq patch failed"

CUDA_VISIBLE_DEVICES=0 python3 -B ${MODEL_SRC}/vsp_llm_decode.py \
    --config-dir ${MODEL_SRC}/conf \
    --config-name s2s_decode \
        common.user_dir=${MODEL_SRC} \
        dataset.gen_subset=test \
        override.data=${DATA_PATH} \
        override.label_dir=${DATA_PATH} \
        generation.beam=20 \
        generation.lenpen=0 \
        dataset.max_tokens=3000 \
        override.eval_bleu=${USE_BLEU} \
        override.llm_ckpt_path=${LLM_PATH} \
        common_eval.path=${MODEL_PATH} \
        common_eval.results_path=${OUT_PATH}