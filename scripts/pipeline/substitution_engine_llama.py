#!/usr/bin/env python3
"""Engine (b) for the phonetic-substitution module: local Llama-3.1-8B-Instruct.

Consumes candidates.json (phonetic_substitute.py candidates / inject-l4) and
emits decisions.json for `phonetic_substitute.py apply`:

  {"engine": "llama31_local", ..., "decisions": [
     {"utt_id", "pos", "decision": "replace"|"keep", "chosen", "verdict",
      "rationale": "Δ=+X.XX nats", "delta_nats", "n_scored_tokens"} ]}

Scope (mirrors engine (a)'s judgeable set): flags that are not display_only and
carry >=1 eligible_for_sub candidate. Per flag, every eligible candidate is
scored; `--include-overlap-eligible` additionally scores candidates whose
eligible_via contains "overlap" (inject-l4's liberal L4 arm, for P3).

SCORING (teacher-forced conditional log-prob). For each variant (the original
segment text, and the text with one candidate slotted into the flagged slot):

    prefix = context_before[-1].text          (nearest earlier segment, if any)
    scored = segment_variant + "\\n" + context_after[0].text   (if any)
    ids    = [BOS] + enc(prefix) + enc(scored)      (special tokens off; the
             scored region starts with "\\n" when a prefix exists)
    S      = sum over the scored region of log p(token_t | tokens_<t)
    n      = token count of the scored region

The after-context is inside the scored region because its probability depends
on the variant (that is how "conditioned on +-1 surrounding segments" can act
bidirectionally in a causal LM); the prefix's own log-prob is variant-invariant
and therefore excluded. Prefix/scored are tokenized separately and the ids
concatenated, so the region boundary is exact and identical across variants.

LENGTH NORMALIZATION (documented choice):

    delta_nats = n_orig * (S_cand / n_cand  -  S_orig / n_orig)

i.e. each variant's summed log-prob is normalized by its own scored-token
count, then both are rescaled by the ORIGINAL variant's count so delta stays on
the summed-nats scale the margin is specified in. When the candidate tokenizes
into the same number of tokens as the original (the common case for one-word
swaps) this reduces exactly to the raw sum difference S_cand - S_orig (a log
Bayes factor between two near-minimal-pair sentences); when counts differ it
removes the mechanical penalty a variant pays merely for having more subword
terms in the sum.

DECISION RULE. chosen = argmax-delta candidate (ties: higher beam_mass, then
word asc). decision = "replace" iff delta_chosen >= --margin (LLAMA_MARGIN_NATS,
init 2.0). Verdict mapping on delta_chosen:
    >= margin  -> clearly_better        (the only verdict apply accepts)
    >= 0.5     -> somewhat_better
    >  -0.5    -> equal
    else       -> worse
A "keep" decision reports the best candidate's verdict with chosen = "".

MODEL. /home/ubuntu/Llama-3.1-8B-Instruct in 4-bit NF4
(BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
bnb_4bit_compute_dtype=torch.float16), device_map="auto") — ~5.7 GB weights on
the Tesla T4. Plain-text likelihood (no chat template): sentence plausibility
scoring uses the LM head directly. Forward passes are batched (--batch-size,
default 24, length-sorted, right-padded; logits gathered per sequence over the
scored region only).

GPU BATON: do not launch on the 1,497 set while a decode owns the T4 — check
`nvidia-smi` first (the parent session coordinates the GPU).

Run with the VSP venv python: /home/ubuntu/vsp-llm-yoad-venv/bin/python
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LLAMA_MARGIN_NATS = 2.0     # replace iff delta >= this (CLI --margin)
SOMEWHAT_NATS = 0.5         # verdict somewhat_better floor
EQUAL_NATS = -0.5           # verdict equal floor (exclusive)
DEFAULT_MODEL_DIR = "/home/ubuntu/Llama-3.1-8B-Instruct"
DEFAULT_BATCH = 24          # plan: 16-32


def judgeable_flags(seg: dict, include_overlap: bool) -> List[dict]:
    """Engine scope — mirrors egla_kafe_substitution_judge.judgeable_flags:
    flag not display_only, >=1 scorable candidate."""
    out = []
    for fl in seg.get("flags", []):
        if fl.get("display_only"):
            continue
        if any(_scorable(c, include_overlap) for c in fl.get("candidates", [])):
            out.append(fl)
    return out


def _scorable(c: dict, include_overlap: bool) -> bool:
    if c.get("eligible_for_sub"):
        return True
    return include_overlap and "overlap" in (c.get("eligible_via") or [])


def _variant_text(words: List[str], pos: int, word: str) -> str:
    v = list(words)
    v[pos] = word
    return " ".join(v)


def build_items(segs: Dict[str, dict], include_overlap: bool,
                limit: Optional[int]) -> Tuple[List[dict], List[dict]]:
    """Returns (scoring items, flag work list). One 'orig::<utt>' item per
    segment with judgeable flags (shared across its flags) + one item per
    scored candidate variant."""
    items: List[dict] = []
    seen_keys = set()
    work: List[dict] = []
    n_flags = 0
    for utt, seg in segs.items():
        flags = judgeable_flags(seg, include_overlap)
        if not flags:
            continue
        words = (seg.get("display_text") or "").split()
        prefix = (seg.get("context_before") or [{}])[-1].get("text") or ""
        after = ((seg.get("context_after") or [{}])[0].get("text") or "")
        for fl in flags:
            if limit is not None and n_flags >= limit:
                return items, work
            n_flags += 1
            pos = fl["position"]
            cands = [c for c in fl.get("candidates", [])
                     if _scorable(c, include_overlap)]
            okey = f"orig::{utt}"
            if okey not in seen_keys:
                seen_keys.add(okey)
                items.append({"key": okey, "prefix": prefix,
                              "scored": " ".join(words), "after": after})
            entry = {"utt": utt, "pos": pos, "okey": okey, "cands": []}
            for c in cands:
                ckey = f"cand::{utt}::{pos}::{c['word']}"
                if ckey not in seen_keys:
                    seen_keys.add(ckey)
                    items.append({"key": ckey, "prefix": prefix,
                                  "scored": _variant_text(words, pos, c["word"]),
                                  "after": after})
                entry["cands"].append({"word": c["word"], "key": ckey,
                                       "beam_mass": c.get("beam_mass", 0.0)})
            work.append(entry)
    return items, work


def load_model(model_dir: str):
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(model_dir)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir, quantization_config=bnb, device_map="auto",
        torch_dtype=torch.float16, low_cpu_mem_usage=True)
    model.eval()
    load_s = time.time() - t0
    vram = torch.cuda.memory_allocated() / 2**30 if torch.cuda.is_available() else 0.0
    print(f"[llama] loaded {model_dir} in {load_s:.1f}s — "
          f"{vram:.2f} GiB allocated on {model.device}")
    return model, tok, load_s


def score_items(model, tok, items: List[dict], batch_size: int) -> Dict[str, Tuple[float, int]]:
    """key -> (summed log-prob over the scored region, scored token count)."""
    import torch
    bos = tok.bos_token_id
    pad = tok.pad_token_id
    prepared = []
    for it in items:
        p_ids = tok(it["prefix"], add_special_tokens=False)["input_ids"] \
            if it["prefix"] else []
        scored_text = (("\n" if it["prefix"] else "") + it["scored"]
                       + ("\n" + it["after"] if it["after"] else ""))
        s_ids = tok(scored_text, add_special_tokens=False)["input_ids"]
        prepared.append({"key": it["key"], "ids": [bos] + p_ids + s_ids,
                         "start": 1 + len(p_ids), "n": len(s_ids)})
    prepared.sort(key=lambda d: -len(d["ids"]))  # length-sorted batches

    out: Dict[str, Tuple[float, int]] = {}
    dev = model.device
    with torch.inference_mode():
        for b0 in range(0, len(prepared), batch_size):
            chunk = prepared[b0:b0 + batch_size]
            maxlen = max(len(d["ids"]) for d in chunk)
            input_ids = torch.full((len(chunk), maxlen), pad, dtype=torch.long)
            attn = torch.zeros((len(chunk), maxlen), dtype=torch.long)
            for r, d in enumerate(chunk):
                input_ids[r, :len(d["ids"])] = torch.tensor(d["ids"])
                attn[r, :len(d["ids"])] = 1
            logits = model(input_ids=input_ids.to(dev),
                           attention_mask=attn.to(dev)).logits.float()
            logprobs = torch.log_softmax(logits, dim=-1)
            ids_dev = input_ids.to(dev)
            for r, d in enumerate(chunk):
                lo, hi = d["start"], d["start"] + d["n"]
                tgt = ids_dev[r, lo:hi]                        # tokens to predict
                lp = logprobs[r, lo - 1:hi - 1, :].gather(     # from their prefixes
                    -1, tgt.unsqueeze(-1)).sum().item()
                out[d["key"]] = (lp, d["n"])
            del logits, logprobs
    return out


def verdict_of(delta: float, margin: float) -> str:
    if delta >= margin:
        return "clearly_better"
    if delta >= SOMEWHAT_NATS:
        return "somewhat_better"
    if delta > EQUAL_NATS:
        return "equal"
    return "worse"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=float, default=LLAMA_MARGIN_NATS,
                    help="replace iff delta >= margin nats (default 2.0)")
    ap.add_argument("--limit", type=int, default=None,
                    help="judge only the first N judgeable flags (smoke test)")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    ap.add_argument("--include-overlap-eligible", action="store_true",
                    help="also score candidates with eligible_via 'overlap' "
                         "(inject-l4 liberal arm)")
    args = ap.parse_args()

    with open(args.candidates, encoding="utf-8") as f:
        cands = json.load(f)
    segs = cands["segments"]
    items, work = build_items(segs, args.include_overlap_eligible, args.limit)
    n_variants = sum(len(w["cands"]) for w in work)
    print(f"[llama] {len(work)} judgeable flags, {n_variants} candidate variants, "
          f"{len(items)} unique forward texts")
    if not work:
        print("[llama] nothing to judge")

    model, tok, load_s = load_model(args.model_dir)
    import torch
    t0 = time.time()
    scores = score_items(model, tok, items, args.batch_size)
    score_s = time.time() - t0
    vram_peak = (torch.cuda.max_memory_allocated() / 2**30
                 if torch.cuda.is_available() else 0.0)
    print(f"[llama] scored {len(items)} texts in {score_s:.1f}s "
          f"({score_s / max(1, len(items)):.2f}s/text) — peak {vram_peak:.2f} GiB")

    decisions = []
    n_replace = 0
    for w in work:
        s_orig, n_orig = scores[w["okey"]]
        ranked = []
        for c in w["cands"]:
            s_c, n_c = scores[c["key"]]
            delta = n_orig * (s_c / n_c - s_orig / n_orig) if n_c and n_orig else float("-inf")
            ranked.append((delta, c["beam_mass"], c["word"], n_c))
        ranked.sort(key=lambda t: (-t[0], -t[1], t[2]))
        delta, _, word, n_c = ranked[0]
        verdict = verdict_of(delta, args.margin)
        replace = verdict == "clearly_better"
        n_replace += int(replace)
        decisions.append({
            "utt_id": w["utt"], "pos": w["pos"],
            "decision": "replace" if replace else "keep",
            "chosen": word if replace else "",
            "verdict": verdict,
            "rationale": f"Δ={delta:+.2f} nats",
            "delta_nats": round(delta, 4),
            "best_candidate": word,
            "n_scored_tokens": n_c,
        })

    out = {
        "engine": "llama31_local",
        "model": args.model_dir,
        "quantization": "4bit-nf4-fp16compute",
        "margin_nats": args.margin,
        "length_norm": "delta = n_orig * (S_cand/n_cand - S_orig/n_orig); "
                       "reduces to raw summed-logprob difference at equal "
                       "token counts (see module docstring)",
        "candidates": str(Path(args.candidates).resolve()),
        "include_overlap_eligible": args.include_overlap_eligible,
        "limit": args.limit,
        "n_decisions": len(decisions),
        "n_replace": n_replace,
        "load_time_s": round(load_s, 1),
        "score_time_s": round(score_s, 1),
        "vram_peak_gib": round(vram_peak, 2),
        "decisions": decisions,
    }
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"[llama] {len(decisions)} decisions ({n_replace} replace) -> {outp}")


if __name__ == "__main__":
    sys.exit(main())
