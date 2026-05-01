# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

#============================ 69 ============================

import ast
from datetime import datetime
from itertools import chain
import logging
import math
import os
import sys
import json
import hashlib
import editdistance
from argparse import Namespace
import pdb

import gc
import numpy as np
import torch
from fairseq import checkpoint_utils, options, tasks, utils, distributed_utils
from fairseq.dataclass.utils import convert_namespace_to_omegaconf
from fairseq.logging import progress_bar
from fairseq.logging.meters import StopwatchMeter, TimeMeter
from omegaconf import DictConfig

from pathlib import Path
import hydra
from hydra.core.config_store import ConfigStore
from fairseq.dataclass.configs import (
    CheckpointConfig,
    CommonConfig,
    CommonEvalConfig,
    GenerationConfig,
    DatasetConfig,
    DistributedTrainingConfig,
    FairseqDataclass,
)
from dataclasses import dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from omegaconf import OmegaConf, MISSING
import sacrebleu

logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_path = Path(__file__).resolve().parent / "conf"

@dataclass
class OverrideConfig(FairseqDataclass):
    noise_wav: Optional[str] = field(default=None, metadata={'help': 'noise wav file'})
    noise_prob: float = field(default=0, metadata={'help': 'noise probability'})
    noise_snr: float = field(default=0, metadata={'help': 'noise SNR in audio'})
    modalities: List[str] = field(default_factory=lambda: ["video"], metadata={'help': 'which modality to use'})
    data: Optional[str] = field(default=None, metadata={'help': 'path to test data directory'})
    label_dir: Optional[str] = field(default=None, metadata={'help': 'path to test label directory'})
    eval_bleu: bool = field(default=False, metadata={'help': 'evaluate bleu score'})
    llm_ckpt_path: str = field(default=MISSING, metadata={'help': 'path to llama checkpoint'})

@dataclass
class InferConfig(FairseqDataclass):
    task: Any = None
    generation: GenerationConfig = GenerationConfig()
    common: CommonConfig = CommonConfig()
    common_eval: CommonEvalConfig = CommonEvalConfig()
    checkpoint: CheckpointConfig = CheckpointConfig()
    distributed_training: DistributedTrainingConfig = DistributedTrainingConfig()
    dataset: DatasetConfig = DatasetConfig()
    override: OverrideConfig = OverrideConfig()
    is_ax: bool = field(
        default=False,
        metadata={
            "help": "if true, assumes we are using ax for tuning and returns a tuple for ax to consume"
        },
    )


def main(cfg: DictConfig):

    if isinstance(cfg, Namespace):
        cfg = convert_namespace_to_omegaconf(cfg)

    assert cfg.common_eval.path is not None, "--path required for recognition!"
    
    if cfg.common_eval.results_path is not None:
        os.makedirs(cfg.common_eval.results_path, exist_ok=True)
        output_path = os.path.join(cfg.common_eval.results_path, "decode.log")
        with open(output_path, "w", buffering=1, encoding="utf-8") as h:
            return _main(cfg, h)

    return _main(cfg, sys.stdout)

from fairseq import tasks
from transformers import AutoTokenizer

def _main(cfg, output_file):
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=os.environ.get("LOGLEVEL", "INFO").upper(),
        stream=output_file,
    )
    logger = logging.getLogger("hybrid.speech_recognize")
    logger.propagate = False  # Prevent duplicate logging to root logger
    logger.setLevel(logging.INFO)

    # Add file/stdout handler
    file_handler = logging.StreamHandler(output_file)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(file_handler)

    # If outputting to file, also print to stdout
    if output_file is not sys.stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(stdout_handler)

    utils.import_user_module(cfg.common)

    tokenizer = AutoTokenizer.from_pretrained(cfg.override.llm_ckpt_path)
    model_override_cfg = {'model':{'llm_ckpt_path':cfg.override.llm_ckpt_path}}
    models, saved_cfg, task = checkpoint_utils.load_model_ensemble_and_task([cfg.common_eval.path],model_override_cfg,strict=False)
    models = [model.eval() for model in models]
    saved_cfg.task.modalities = cfg.override.modalities
    task = tasks.setup_task(saved_cfg.task)
    task.build_tokenizer(saved_cfg.tokenizer)
    task.build_bpe(saved_cfg.bpe)

    logger.info(cfg)

    # Fix seed for stochastic decoding
    if cfg.common.seed is not None :
        np.random.seed(cfg.common.seed)
        utils.set_torch_seed(cfg.common.seed)

    use_cuda = torch.cuda.is_available()

    # Set dictionary
    dictionary = task.target_dictionary

    # loading the dataset should happen after the checkpoint has been loaded so we can give it the saved task config
    task.cfg.llm_ckpt_path = cfg.override.llm_ckpt_path
    task.cfg.noise_prob = cfg.override.noise_prob
    task.cfg.noise_snr = cfg.override.noise_snr
    task.cfg.noise_wav = cfg.override.noise_wav
    if cfg.override.data is not None:
        task.cfg.data = cfg.override.data
    if cfg.override.label_dir is not None:
        task.cfg.label_dir = cfg.override.label_dir
    task.load_dataset(cfg.dataset.gen_subset, task_cfg=cfg.task)

    lms = [None]

    # Optimize ensemble for generation

    for model in chain(models, lms):
        if model is None:
            continue
        if use_cuda and not cfg.distributed_training.pipeline_model_parallel:
            model.encoder.cuda()
            model.avfeat_to_llm.cuda()
            model.half()

    # Detect GPU memory for adaptive generation parameters
    gpu_mem_gb = 0
    if use_cuda:
        gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        logger.info(f"GPU memory: {gpu_mem_gb:.1f} GB")
    small_gpu = gpu_mem_gb > 0 and gpu_mem_gb < 16

    # Load dataset (possibly sharded)
    cfg.dataset.batch_size = 1
    cfg.dataset.max_tokens = 1000
    itr = task.get_batch_iterator(
        dataset=task.dataset(cfg.dataset.gen_subset),
        max_tokens=cfg.dataset.max_tokens,
        max_sentences=cfg.dataset.batch_size,
        max_positions=utils.resolve_max_positions(
            task.max_positions(), *[m.max_positions() for m in models]
        ),
        ignore_invalid_inputs=cfg.dataset.skip_invalid_size_inputs_valid_test,
        required_batch_size_multiple=cfg.dataset.required_batch_size_multiple,
        seed=cfg.common.seed,
        num_shards=cfg.distributed_training.distributed_world_size,
        shard_id=cfg.distributed_training.distributed_rank,
        num_workers=cfg.dataset.num_workers,
        data_buffer_size=cfg.dataset.data_buffer_size,
    ).next_epoch_itr(shuffle=False)
    progress = progress_bar.progress_bar(
        itr,
        log_format=cfg.common.log_format,
        log_interval=cfg.common.log_interval,
        default_log_format=("tqdm" if not cfg.common.no_progress_bar else "simple"),
    )

    # Authoritative sample count for the UI's "X / N segments decoded" counter.
    # The bash side of lib/decode.sh emits an early estimate from the manifest
    # line count; this overrides it once the dataset has actually loaded.
    try:
        _decode_total = len(task.dataset(cfg.dataset.gen_subset))
        logger.info(f"Decode dataset loaded: {_decode_total} samples")
    except (TypeError, AttributeError):
        pass  # Don't fail decode if the dataset doesn't support len()

    gen_timer = StopwatchMeter()
    def decode_fn(x):
        symbols_ignore = {"<unk>", "<mask>","<pad>", "</s>"}
        if hasattr(task.datasets[cfg.dataset.gen_subset].label_processors[0], 'decode'):
            return tokenizer.decode(x, skip_special_tokens=True)
        chars = dictionary.string(x, extra_symbols_to_ignore=symbols_ignore)
        words = " ".join("".join(chars.split()).replace('|', ' ').split())
        return words

    num_sentences = 0
    has_target = True
    wps_meter = TimeMeter()
    result_dict = {'utt_id': [], 'ref': [], 'hypo': [], 'instruction': []}
    model = models[0]

    nbest_enabled = os.environ.get("VSP_NBEST", "0") == "1"
    # n-best capture requires per-token probs/entropy. If the user opts into
    # n-best but forgets to also set output-scores, force it on (matches the
    # behavioral coupling in vsp_llm.generate()).
    if nbest_enabled and os.environ.get("VSP_OUTPUT_SCORES", "0") != "1":
        os.environ["VSP_OUTPUT_SCORES"] = "1"
        logger.info("VSP_NBEST=1 requires per-token probs; forcing VSP_OUTPUT_SCORES=1")
    output_scores_enabled = os.environ.get("VSP_OUTPUT_SCORES", "0") == "1"
    confidence_records = {}  # utt_id -> {seq_score, tokens: [{token, prob}]} (top-1)
    nbest_records = {}       # utt_id -> {hypotheses: [{rank, text, sequence_score, raw_logprob_sum, tokens: [...]}]}

    # Pre-compute the file id so partial flushes can write to the same files
    # the final dump uses. fid is deterministic from cfg.generation, so this
    # match is stable across the loop.
    _yaml_str = OmegaConf.to_yaml(cfg.generation)
    fid = int(hashlib.md5(_yaml_str.encode("utf-8")).hexdigest(), 16) % 1000000
    results_path = cfg.common_eval.results_path
    hypo_fn = f"{results_path}/hypo-{fid}.json"
    confidence_fn = f"{results_path}/confidence-{fid}.json"
    nbest_fn = f"{results_path}/nbest-{fid}.json"

    # Atomic, crash-resilient incremental flush. Writes the *current* in-memory
    # dicts to a .tmp file, then os.replace into place — so a kill mid-write
    # leaves either the prior good file or the new one, never corrupt JSON.
    # Cadence is sample-count based; configurable via env so we can tune later.
    flush_every = int(os.environ.get("VSP_FLUSH_EVERY", "25"))

    def _flush_partial():
        try:
            tmp = f"{hypo_fn}.tmp"
            with open(tmp, "w") as f:
                json.dump(result_dict, f, indent=4)
            os.replace(tmp, hypo_fn)
            if output_scores_enabled and confidence_records:
                tmp_c = f"{confidence_fn}.tmp"
                with open(tmp_c, "w") as f:
                    json.dump(confidence_records, f, indent=2)
                os.replace(tmp_c, confidence_fn)
            if nbest_enabled and nbest_records:
                tmp_n = f"{nbest_fn}.tmp"
                with open(tmp_n, "w") as f:
                    json.dump(nbest_records, f, indent=2)
                os.replace(tmp_n, nbest_fn)
        except Exception as e:
            logger.warning(f"Incremental flush failed (non-fatal): {e}")

    samples_seen = 0
    for sample in progress:
        sample = utils.move_to_cuda(sample) if use_cuda else sample
        if "net_input" not in sample:
            continue
        
        sample['net_input']['source']['video'] = sample['net_input']['source']['video'].to(torch.half)

        # Dynamic max_length: proportional to input size, capped by max_len
        src_tokens = sample['net_input']['source']['cluster_counts'][0].shape[0]
        dynamic_max_len = int(cfg.generation.max_len_a * src_tokens + cfg.generation.max_len_b)
        if cfg.generation.max_len > 0:
            dynamic_max_len = min(dynamic_max_len, cfg.generation.max_len)

        # Tighter max_len cap for small GPUs (keeps beam=20 feasible within 12GB)
        if small_gpu and dynamic_max_len > 512:
            dynamic_max_len = 512

        gen_out = model.generate(target_list=sample["target"],
                                   num_beams=cfg.generation.beam,
                                   max_length=dynamic_max_len,
                                   length_penalty=cfg.generation.lenpen,
                                   no_repeat_ngram_size=cfg.generation.no_repeat_ngram_size,
                                   repetition_penalty=cfg.generation.repetition_penalty,
                                   do_sample=cfg.generation.do_sample,
                                   temperature=cfg.generation.temperature,
                                   top_p=cfg.generation.top_p,
                                   **sample["net_input"])

        # Unwrap dict-mode return when VSP_OUTPUT_SCORES=1 was set inside generate().
        # In default (tensor) mode, gen_out IS the token-id tensor; preserve original behavior.
        # n_per is the number of returned sequences per batch item:
        #   - VSP_NBEST=0: n_per=1 (top-1 only, legacy)
        #   - VSP_NBEST=1: n_per=num_beams (all surviving beams, ranked best-first)
        if hasattr(gen_out, "sequences"):
            seqs_all = gen_out.sequences  # [batch * n_per, gen_len]
            n_seqs = seqs_all.size(0)
            batch_size = len(sample["id"])
            n_per = max(1, n_seqs // batch_size)

            # sequences_scores: length-normalized log-prob; shape [n_seqs]
            if getattr(gen_out, "sequences_scores", None) is not None:
                seq_scores_all = gen_out.sequences_scores.float().cpu().numpy().tolist()
            else:
                seq_scores_all = [None] * n_seqs

            # Per-token probs via beam_indices-aware compute_transition_scores.
            # When num_return_sequences=num_beams, this returns [n_seqs, gen_len]
            # already aligned to each surviving sequence (HF follows beam_indices
            # internally). Sum across positions gives the raw (un-length-normalized)
            # log-prob if we want it for MBR weighting.
            try:
                trans_scores = model.decoder.compute_transition_scores(
                    seqs_all,
                    gen_out.scores,
                    getattr(gen_out, "beam_indices", None),
                    normalize_logits=True,
                )  # log-probs [n_seqs, gen_len]
                token_probs_all = trans_scores.exp().float().cpu().numpy().tolist()
                # Raw sum-of-log-probs per sequence (ignores -inf padding for finished beams).
                raw_logprob_sum_all = []
                for s in range(n_seqs):
                    finite = [lp for lp in trans_scores[s].cpu().numpy().tolist() if math.isfinite(lp)]
                    raw_logprob_sum_all.append(float(sum(finite)) if finite else None)
            except Exception as e:
                logger.warning(f"compute_transition_scores failed; saving sequence scores only: {e}")
                token_probs_all = [None] * n_seqs
                raw_logprob_sum_all = [None] * n_seqs

            # Per-step entropy + top-3 alternatives, gathered via beam_indices so
            # the distribution is correctly attributed to each surviving sequence
            # (HF reorders beams between steps; the previous step_scores[::n_beams]
            # stride was incorrect because beam-0 is not always the running-best).
            # Works for both top-1 (n_per=1) and n-best (n_per=num_beams).
            try:
                _F = torch.nn.functional
                beam_indices = getattr(gen_out, "beam_indices", None)
                step_entropies_all = [[] for _ in range(n_seqs)]
                step_top3_all = [[] for _ in range(n_seqs)]
                if beam_indices is not None and gen_out.scores is not None:
                    gen_len_t = len(gen_out.scores)
                    bi_len = beam_indices.size(1) if beam_indices.dim() == 2 else 0
                    for t in range(gen_len_t):
                        step_scores = gen_out.scores[t]  # [batch * n_beams, vocab]
                        probs = _F.softmax(step_scores, dim=-1)
                        log_probs = _F.log_softmax(step_scores, dim=-1)
                        ent = -(probs * log_probs).sum(dim=-1)  # [batch * n_beams]
                        top3_p, top3_i = probs.topk(3, dim=-1)  # [batch * n_beams, 3]
                        for s in range(n_seqs):
                            bi = int(beam_indices[s, t].item()) if t < bi_len else -1
                            if bi < 0 or bi >= step_scores.size(0):
                                # Step is past EOS / padded for this sequence.
                                step_entropies_all[s].append(None)
                                step_top3_all[s].append(None)
                            else:
                                step_entropies_all[s].append(float(ent[bi].item()))
                                step_top3_all[s].append([
                                    {"id": int(top3_i[bi, k].item()),
                                     "p":  float(top3_p[bi, k].item())}
                                    for k in range(3)
                                ])
            except Exception as e:
                logger.warning(f"entropy/top-3 extraction failed: {e}")
                step_entropies_all = [None] * n_seqs
                step_top3_all = [None] * n_seqs

            # Top-1 (rank-0) views per batch item — preserves the legacy
            # confidence sidecar shape and the tokenizer.batch_decode call below.
            best_hypo_tokens = seqs_all[::n_per]  # [batch, gen_len]
            seq_scores = [seq_scores_all[i * n_per] for i in range(batch_size)]
            token_probs = [token_probs_all[i * n_per] if token_probs_all is not None else None for i in range(batch_size)]
            step_entropies = [step_entropies_all[i * n_per] for i in range(batch_size)]
            step_top3 = [step_top3_all[i * n_per] for i in range(batch_size)]
        else:
            best_hypo_tokens = gen_out
            n_per = 1
            seqs_all = best_hypo_tokens
            seq_scores_all = [None] * best_hypo_tokens.size(0)
            token_probs_all = [None] * best_hypo_tokens.size(0)
            raw_logprob_sum_all = [None] * best_hypo_tokens.size(0)
            step_entropies_all = [None] * best_hypo_tokens.size(0)
            step_top3_all = [None] * best_hypo_tokens.size(0)
            seq_scores = [None] * best_hypo_tokens.size(0)
            token_probs = [None] * best_hypo_tokens.size(0)
            step_entropies = [None] * best_hypo_tokens.size(0)
            step_top3 = [None] * best_hypo_tokens.size(0)

        best_hypo = tokenizer.batch_decode(
                best_hypo_tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
        for i in range(len(sample["id"])):
            result_dict['utt_id'].append(sample['utt_id'][i])
            target = sample['target'][i].masked_fill(
                sample['target'][i] == -100, 0
            )
            ref_sent = tokenizer.decode(target.int().cpu(), skip_special_tokens=True, clean_up_tokenization_spaces=False)
            result_dict['ref'].append(ref_sent)
            hypo_str = best_hypo[i]
            instruction = tokenizer.decode(sample['net_input']['source']['text'][i].int().cpu(), skip_special_tokens=True, clean_up_tokenization_spaces=False)
            result_dict['instruction'].append(instruction)
            result_dict['hypo'].append(hypo_str)
            logger.info(f"\nINST:{instruction}\nREF:{ref_sent}\nHYP:{hypo_str}\n")

            if output_scores_enabled:
                tok_ids = best_hypo_tokens[i].cpu().tolist()
                # Use convert_ids_to_tokens (NOT decode) so SentencePiece word-start
                # markers (U+2581 ▁) are preserved. The aggregator in
                # compute_word_confidence.py relies on them to detect word boundaries.
                tok_strs = tokenizer.convert_ids_to_tokens(tok_ids)
                tok_probs_i = token_probs[i] if token_probs[i] is not None else [None] * len(tok_ids)
                # Align lengths defensively (compute_transition_scores may drop the bos token).
                pad_n = max(0, len(tok_ids) - len(tok_probs_i))
                tok_probs_i = [None] * pad_n + list(tok_probs_i)
                tok_probs_i = tok_probs_i[: len(tok_ids)]

                # Entropy and top-3 alternatives from the per-step distribution.
                # gen_out.scores has one entry per *generated* token (i.e., not
                # for the BOS prepended by HF). Pad-align with token_probs.
                ent_i  = step_entropies[i] if i < len(step_entropies) and step_entropies[i] else []
                top3_i_ = step_top3[i]      if i < len(step_top3)      and step_top3[i]      else []
                pad_e = max(0, len(tok_ids) - len(ent_i))
                ent_aligned = [None] * pad_e + list(ent_i)
                top3_aligned = [None] * pad_e + list(top3_i_)
                ent_aligned = ent_aligned[: len(tok_ids)]
                top3_aligned = top3_aligned[: len(tok_ids)]

                tok_records = []
                for k, (tid, tstr) in enumerate(zip(tok_ids, tok_strs)):
                    rec = {
                        "token_id": int(tid),
                        "token": tstr,
                        "prob": (float(tok_probs_i[k]) if tok_probs_i[k] is not None else None),
                        "entropy": ent_aligned[k] if k < len(ent_aligned) else None,
                        "top3": top3_aligned[k] if k < len(top3_aligned) else None,
                    }
                    tok_records.append(rec)

                confidence_records[sample['utt_id'][i]] = {
                    "sequence_score": seq_scores[i],
                    "tokens": tok_records,
                }

            # n-best capture: per-utterance hypothesis list with per-token probs
            # for each surviving beam. Top-1 (rank 0) text matches result_dict['hypo'][i]
            # by construction (same seqs_all[::n_per] subset).
            if nbest_enabled:
                hyps = []
                for r in range(n_per):
                    s_idx = i * n_per + r
                    seq_tokens = seqs_all[s_idx].cpu().tolist()
                    text_r = tokenizer.decode(
                        seqs_all[s_idx], skip_special_tokens=True, clean_up_tokenization_spaces=False
                    )
                    tstrs = tokenizer.convert_ids_to_tokens(seq_tokens)

                    tp_r = token_probs_all[s_idx] if token_probs_all and token_probs_all[s_idx] is not None else [None] * len(seq_tokens)
                    pad_n = max(0, len(seq_tokens) - len(tp_r))
                    tp_r = [None] * pad_n + list(tp_r)
                    tp_r = tp_r[: len(seq_tokens)]

                    ent_r  = step_entropies_all[s_idx] if step_entropies_all[s_idx] else []
                    top3_r = step_top3_all[s_idx]      if step_top3_all[s_idx]      else []
                    pad_e = max(0, len(seq_tokens) - len(ent_r))
                    ent_r = [None] * pad_e + list(ent_r)
                    top3_r = [None] * pad_e + list(top3_r)
                    ent_r = ent_r[: len(seq_tokens)]
                    top3_r = top3_r[: len(seq_tokens)]

                    tok_recs_r = []
                    for k, (tid, tstr) in enumerate(zip(seq_tokens, tstrs)):
                        # Filter out -inf log-prob tokens (post-EOS padding)
                        p = tp_r[k]
                        if p is not None and not math.isfinite(float(p)):
                            p = None
                        tok_recs_r.append({
                            "token_id": int(tid),
                            "token": tstr,
                            "prob": (float(p) if p is not None else None),
                            "entropy": ent_r[k] if k < len(ent_r) else None,
                            "top3": top3_r[k] if k < len(top3_r) else None,
                        })

                    hyps.append({
                        "rank": r,
                        "text": text_r,
                        "sequence_score": seq_scores_all[s_idx],
                        "raw_logprob_sum": raw_logprob_sum_all[s_idx] if s_idx < len(raw_logprob_sum_all) else None,
                        "tokens": tok_recs_r,
                    })
                nbest_records[sample['utt_id'][i]] = {"hypotheses": hyps}

        # Free GPU memory between samples (prevents accumulation on 12GB GPUs)
        if use_cuda:
            torch.cuda.empty_cache()
            free_mem = torch.cuda.mem_get_info()[0]
            if free_mem < 2 * 1024**3:  # Less than 2 GB free
                gc.collect()
                torch.cuda.empty_cache()

        samples_seen += len(sample["id"])
        if flush_every > 0 and samples_seen % flush_every == 0:
            _flush_partial()
            logger.info(f"Incremental flush at {samples_seen} samples → {hypo_fn}")

    # Final flush — the canonical full dump. Uses the same path as partial
    # flushes, overwriting them with the complete result.
    _flush_partial()
    if output_scores_enabled and confidence_records:
        logger.info(f"Saved per-token confidence sidecar to {confidence_fn} ({len(confidence_records)} segments)")
    if nbest_enabled and nbest_records:
        n_per_eff = len(next(iter(nbest_records.values()))["hypotheses"]) if nbest_records else 0
        logger.info(f"Saved n-best sidecar to {nbest_fn} ({len(nbest_records)} segments × {n_per_eff} hypotheses)")

    # Save effective decode parameters for report documentation
    try:
        decode_params = {
            "beam": int(cfg.generation.beam),
            "length_penalty": float(cfg.generation.lenpen),
            "max_len_a": float(cfg.generation.max_len_a),
            "max_len_b": int(cfg.generation.max_len_b),
            "max_len": int(cfg.generation.max_len),
            "no_repeat_ngram_size": int(cfg.generation.no_repeat_ngram_size),
            "repetition_penalty": float(cfg.generation.repetition_penalty),
            "lm_weight": float(cfg.generation.lm_weight),
            "max_tokens": int(cfg.dataset.max_tokens),
            "gpu_mem_gb": round(gpu_mem_gb, 1),
            "small_gpu": small_gpu,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "model_checkpoint": str(cfg.common_eval.path),
            "num_segments": len(result_dict["utt_id"]),
        }
        params_fn = f"{cfg.common_eval.results_path}/decode_params-{fid}.json"
        json.dump(decode_params, open(params_fn, 'w'), indent=2)
        logger.info(f"Saved decode params to {params_fn}")
    except Exception as e:
        logger.warning(f"Could not save decode params: {e}")

    if not cfg.override.eval_bleu:
        n_err, n_total = 0, 0
        assert len(result_dict['hypo']) == len(result_dict['ref'])
        for hypo, ref in zip(result_dict['hypo'], result_dict['ref']):
            hypo, ref = hypo.strip().split(), ref.strip().split()
            n_err += editdistance.eval(hypo, ref)
            n_total += len(ref)
        wer = 100 * n_err / n_total
        wer_fn = f"{cfg.common_eval.results_path}/wer.{fid}"
        with open(wer_fn, "w") as fo:
            fo.write(f"WER: {wer}\n")
            fo.write(f"err / num_ref_words = {n_err} / {n_total}\n\n")
            fo.write(f"{_yaml_str}")
        logger.info(f"WER: {wer}%")
    else:
        bleu = sacrebleu.corpus_bleu(result_dict['hypo'], [result_dict['ref']])
        bleu_score = bleu.score
        bleu_fn = f"{cfg.common_eval.results_path}/bleu.{fid}"
        with open(bleu_fn, "w") as fo:
            fo.write(f"BLEU: {bleu_score}\n")
            fo.write(f"{_yaml_str}")
        logger.info(f"BLEU: {bleu_score}\n")
    return


@hydra.main(config_path=config_path, config_name="infer")
def hydra_main(cfg: InferConfig) -> Union[float, Tuple[float, Optional[float]]]:
    container = OmegaConf.to_container(cfg, resolve=True, enum_to_str=True)
    cfg = OmegaConf.create(container)
    OmegaConf.set_struct(cfg, True)

    try:
        if cfg.common.profile:
            with torch.cuda.profiler.profile():
                with torch.autograd.profiler.emit_nvtx():
                    distributed_utils.call_main(cfg, main)
        else:
            distributed_utils.call_main(cfg, main)

    except BaseException as e:  # pylint: disable=broad-except
        if not cfg.common.suppress_crashes:
            raise
        else:
            logger.error("Crashed! %s", str(e))
    return


def cli_main() -> None:
    try:
        from hydra._internal.utils import (
            get_args,
        )  # pylint: disable=import-outside-toplevel

        cfg_name = get_args().config_name or "infer"
    except ImportError:
        logger.warning("Failed to get config name from hydra args")
        cfg_name = "infer"

    cs = ConfigStore.instance()
    cs.store(name=cfg_name, node=InferConfig)

    for k in InferConfig.__dataclass_fields__:
        if is_dataclass(InferConfig.__dataclass_fields__[k].type):
            v = InferConfig.__dataclass_fields__[k].default
            cs.store(name=k, node=v)

    hydra_main()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    cli_main()