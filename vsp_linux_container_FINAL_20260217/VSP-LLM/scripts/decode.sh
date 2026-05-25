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

# Auto-patch fairseq GenerationConfig if fields are missing (Bugs 11/19/22 + May-2026 Bug 17)
# Must run AFTER PYTHONPATH is set so it patches the fairseq that decode will use.
#
# Why this exists: PYTHONPATH=${ROOT}/fairseq pins the LOCAL fairseq fork at
# /host/galaxy_export/VSP-LLM/fairseq/, which is older than the EC2 fork.
# The EC2 fork has 4 added fields the decoder reads via cfg.generation.*:
#   max_len, repetition_penalty (decode tuning; bugs 11/19/22 — already patched)
#   do_sample, top_p             (HF sampling; May-2026 add — Bug 17 below)
# Without these fields OmegaConf strict-struct raises ConfigAttributeError at
# vsp_llm_decode.py:301-303.  The pip-installed fairseq has all four already
# but is shadowed by PYTHONPATH; we patch the local fork at runtime instead.
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

# Patch 3 (May 2026 — Bug 17): do_sample field for HF generate stochastic sampling.
# vsp_llm_decode.py:301 reads cfg.generation.do_sample to toggle sampling vs
# pure beam search. Without this field decode crashes with
#   omegaconf.errors.ConfigAttributeError: Key 'do_sample' is not in struct
# even when the value would be False. Anchor on 'sampling: bool' (upstream).
if not hasattr(c.GenerationConfig, 'do_sample'):
    target = '    sampling: bool'
    patch = '    do_sample: bool = field(\n        default=False,\n        metadata={\n            \"help\": \"enable stochastic sampling in HuggingFace generate (default False = pure beam search)\"\n        },\n    )\n    sampling: bool'
    if target in content:
        content = content.replace(target, patch, 1)
        patched = True
        print('Patched: do_sample')
    else:
        print('WARNING: Could not find sampling: bool anchor for do_sample patch')
else:
    print('OK: do_sample')

# Patch 4 (May 2026 — Bug 17): top_p field for HF nucleus sampling.
# vsp_llm_decode.py:303 reads cfg.generation.top_p. Upstream fairseq has
# 'sampling_topp' (default -1.0) which is semantically different — kept here.
# Anchor on the same 'sampling: bool' line; Patch 3 already inserted its block
# before that line, so this insert lands between them. Order does not matter.
if not hasattr(c.GenerationConfig, 'top_p'):
    target = '    sampling: bool'
    patch = '    top_p: float = field(\n        default=0.9,\n        metadata={\n            \"help\": \"nucleus sampling top-p for HuggingFace generate (requires do_sample=True)\"\n        },\n    )\n    sampling: bool'
    if target in content:
        content = content.replace(target, patch, 1)
        patched = True
        print('Patched: top_p')
    else:
        print('WARNING: Could not find sampling: bool anchor for top_p patch')
else:
    print('OK: top_p')

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