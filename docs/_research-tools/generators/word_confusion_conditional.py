"""Conditional / stratified word-level confusion analysis.

Extends `analyze_beam_variance.py` with answers to:

  Q1: Is the (1−recall) ↔ confidence relationship different for *content*
      words (rare nouns, NEs) vs. *function* words (the/and/of/is)?
  Q2: When we condition on segments that the model is *confident overall* about
      (sentence_confidence ≥ 0.70), does the per-word relationship strengthen?
  Q3: Same question, conditioned on segment IS ≥ 3.0 (the legacy "captured"
      threshold) and IS ≥ 3.80 (NIV-Y).
  Q4: Same conditioned on ≥ 0.85 sentence_confidence (the conf-high threshold).

The hypothesis being tested: if the model is well-calibrated *within good
segments*, then the (1−recall) ↔ confidence relationship should be much
stronger when we strip out the catastrophic-failure segments where confidence
becomes uninformative noise.

Usage:
  python word_confusion_conditional.py \
      --nbest nbest-{fid}.json \
      --hypo hypo-{fid}.json \
      --confidence confidence-{fid}.json \
      --baseline-csv report.csv \
      --out-dir <dir>
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
# nbest_aggregate lives at /home/ubuntu/lib/ (EC2 dev) or co-located in VSP-LLM/scripts (container).
for _candidate in ("/home/ubuntu/lib", os.path.abspath(os.path.join(_HERE, "..", "..", "VSP-LLM", "scripts"))):
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from _alignment import align_word_lists, split_words  # noqa: E402

# Reuse exact aggregation primitives from the main analyzer
import analyze_beam_variance as ABV  # noqa: E402
import nbest_aggregate as NA  # noqa: E402


# Minimal English function-word list (top-most-common closed-class words).
# These dominate the long tail in any corpus and the "confused word" stats are
# noisy on them because they're predicted hundreds of times. Splitting by this
# list separates "the model can't lip-read 'the'" from "the model can't lip-read
# 'subroutine'".
FUNCTION_WORDS = frozenset(
    "the a an and or but if in on at to for of is am are was were be been being "
    "have has had do does did will would shall should may might can could "
    "i me my we us our you your he him his she her it its they them their "
    "that this these those who whom which what where when how not no nor "
    "so very too also just than more most such as with from by about between "
    "into through during before after above below up down out off over under "
    "again then once here there all each every both few many much some any "
    "other another same different new old don't didn't won't can't isn't aren't wasn't weren't "
    "i'm i've i'll you're you've you'll he's she's it's we're they're".split()
)


def build_segment_features(
    nbest: Dict[str, dict],
    refs: Dict[str, str],
    confidence: Dict[str, dict],
    baseline_df: pd.DataFrame,
) -> pd.DataFrame:
    """Per-segment features for filtering: sentence_confidence, IS, WER, etc."""
    rows = []
    for utt_id in nbest:
        rec = {"utt_id": utt_id}
        rec["ref"] = refs.get(utt_id, "")
        # sentence_confidence from word_confidence aggregation
        wc = ABV._word_confs_for_utt(confidence.get(utt_id))
        rec["sentence_confidence"] = float(np.mean([p for _, p in wc if p is not None])) if wc else None
        rec["min_word_conf"] = min((p for _, p in wc if p is not None), default=None)
        rows.append(rec)
    seg_df = pd.DataFrame(rows)
    if not baseline_df.empty and "utt_id" in baseline_df.columns:
        cols = [c for c in ["utt_id", "wer_%", "wwer_%", "is_score", "is_tier", "is_label"] if c in baseline_df.columns]
        seg_df = seg_df.merge(baseline_df[cols], on="utt_id", how="left")
    return seg_df


def per_word_stats(
    nbest: Dict[str, dict],
    refs: Dict[str, str],
    confidence: Dict[str, dict],
    seg_filter: Optional[set] = None,
) -> pd.DataFrame:
    """Re-do the per-word table, but optionally restrict to a subset of utt_ids
    (so we can compute stats *conditioned* on segment-level quality)."""
    word_freq: Dict[str, int] = defaultdict(int)
    word_correct: Dict[str, int] = defaultdict(int)
    word_conf_sum: Dict[str, float] = defaultdict(float)
    word_conf_n: Dict[str, int] = defaultdict(int)
    word_disagree_sum: Dict[str, float] = defaultdict(float)
    word_disagree_n: Dict[str, int] = defaultdict(int)

    for utt_id, rec in nbest.items():
        if seg_filter is not None and utt_id not in seg_filter:
            continue
        hyps = rec.get("hypotheses") or []
        if not hyps:
            continue
        top1_words = split_words(hyps[0].get("text", ""))
        ref_words = split_words(refs.get(utt_id, ""))
        for rw in ref_words:
            word_freq[rw.lower()] += 1
        conf_words = ABV._word_confs_for_utt(confidence.get(utt_id))
        all_beam_words = [split_words(h.get("text", "")) for h in hyps]
        disagree_rates = ABV.per_position_disagreement(top1_words, all_beam_words) if len(all_beam_words) > 1 else [0.0] * len(top1_words)

        ref_pairs = align_word_lists([w.lower() for w in ref_words], [w.lower() for w in top1_words])
        for ri, hi in ref_pairs:
            if ri < 0 or hi < 0:
                continue
            if ref_words[ri].lower() != top1_words[hi].lower():
                continue
            target = ref_words[ri].lower()
            word_correct[target] += 1
            if hi < len(conf_words):
                _, w_conf = conf_words[hi]
                if w_conf is not None:
                    word_conf_sum[target] += w_conf
                    word_conf_n[target] += 1
            if hi < len(disagree_rates):
                word_disagree_sum[target] += disagree_rates[hi]
                word_disagree_n[target] += 1

    rows = []
    for word, freq in word_freq.items():
        rows.append({
            "word": word,
            "freq": int(freq),
            "times_correct": int(word_correct.get(word, 0)),
            "recall": word_correct.get(word, 0) / freq if freq else 0.0,
            "mean_conf": (word_conf_sum[word] / word_conf_n[word]) if word_conf_n.get(word) else None,
            "n_conf_obs": int(word_conf_n.get(word, 0)),
            "mean_beam_disagree": (word_disagree_sum[word] / word_disagree_n[word]) if word_disagree_n.get(word) else None,
            "n_disagree_obs": int(word_disagree_n.get(word, 0)),
            "is_function_word": word in FUNCTION_WORDS,
        })
    return pd.DataFrame(rows)


def compute_correlation(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> dict:
    """Pearson r + sample size + simple summary line."""
    d = df.dropna(subset=[x_col, y_col])
    if len(d) < 3:
        return {"label": label, "n": len(d), "r": None, "summary": f"{label}: n={len(d)} (too few)"}
    r = float(np.corrcoef(d[x_col], d[y_col])[0, 1])
    return {"label": label, "n": int(len(d)), "r": r, "summary": f"{label}: r = {r:+.3f}  (n={len(d)})"}


def conditional_table(seg_df: pd.DataFrame, label: str, mask: pd.Series, nbest, refs, conf) -> dict:
    """Compute per-word table on the subset of segments where `mask` is True,
    then return Pearson r for each interesting (predictor, target) pair.
    """
    keep = set(seg_df.loc[mask, "utt_id"].tolist())
    n_segs = len(keep)
    if n_segs == 0:
        return {"label": label, "n_segs": 0}
    wd = per_word_stats(nbest, refs, conf, seg_filter=keep)
    wd_freq3 = wd[wd["freq"] >= 3].copy()
    wd_freq3["confusion_rate"] = 1.0 - wd_freq3["recall"]
    wd_freq3 = wd_freq3.dropna(subset=["mean_conf"])

    # All / function / content split
    funcs = wd_freq3[wd_freq3["is_function_word"] == True]
    contents = wd_freq3[wd_freq3["is_function_word"] == False]

    out = {
        "label": label,
        "n_segs": int(n_segs),
        "n_words_freq3": int(len(wd_freq3)),
        "n_function_words": int(len(funcs)),
        "n_content_words": int(len(contents)),
        "all":      compute_correlation(wd_freq3, "mean_conf", "confusion_rate", "all words"),
        "content":  compute_correlation(contents, "mean_conf", "confusion_rate", "content words only"),
        "function": compute_correlation(funcs, "mean_conf", "confusion_rate", "function words only"),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbest", required=True)
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--confidence", required=True)
    ap.add_argument("--baseline-csv", default=None)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    nbest = json.load(open(args.nbest))
    hypo  = json.load(open(args.hypo))
    conf  = json.load(open(args.confidence))
    refs  = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}
    baseline_df = pd.read_csv(args.baseline_csv) if args.baseline_csv and os.path.isfile(args.baseline_csv) else pd.DataFrame()

    seg_df = build_segment_features(nbest, refs, conf, baseline_df)
    seg_df.to_csv(os.path.join(args.out_dir, "segment_features.csv"), index=False)
    print(f"Loaded {len(nbest)} segments. seg_df cols: {list(seg_df.columns)}")
    print(f"sentence_confidence: mean={seg_df['sentence_confidence'].mean():.3f}, "
          f"median={seg_df['sentence_confidence'].median():.3f}")

    # Build masks for conditional analyses.
    s = seg_df.set_index("utt_id")
    sc = s["sentence_confidence"]

    masks = [
        ("ALL segments", pd.Series(True, index=s.index)),
        ("sent_conf >= 0.50",   sc >= 0.50),
        ("sent_conf >= 0.70",   sc >= 0.70),
        ("sent_conf >= 0.85",   sc >= 0.85),
    ]
    if "is_score" in s.columns:
        is_col = pd.to_numeric(s["is_score"], errors="coerce")
        masks += [
            ("IS >= 2.00 (NIV-Y+P)", is_col >= 2.00),
            ("IS >= 3.00 (legacy capt)", is_col >= 3.00),
            ("IS >= 3.80 (NIV-Y)", is_col >= 3.80),
        ]
    if "wer_%" in s.columns:
        wer_col = pd.to_numeric(s["wer_%"], errors="coerce")
        masks += [
            ("WER <= 50%", wer_col <= 50),
            ("WER <= 30%", wer_col <= 30),
        ]

    seg_df_idx = seg_df.set_index("utt_id")
    results = []
    for label, mask in masks:
        # Re-key the mask to seg_df by matching its utt_id index.
        mask_aligned = mask.reindex(seg_df_idx.index, fill_value=False)
        r = conditional_table(seg_df.assign(_keep=mask_aligned.values),
                              label, pd.Series(mask_aligned.values, index=seg_df.index), nbest, refs, conf)
        results.append(r)

    # Pretty-print the table
    print()
    print("=" * 100)
    print(f"{'Filter':<28} {'n_segs':>7} {'n_words':>8} {'all r':>10} {'content r':>12} {'func r':>10}")
    print("-" * 100)
    for r in results:
        if r.get("n_segs", 0) == 0:
            print(f"{r['label']:<28} {0:>7} (empty)")
            continue
        all_r  = r["all"]["r"]
        cont_r = r["content"]["r"]
        func_r = r["function"]["r"]
        all_s  = f"{all_r:+.3f}"  if all_r  is not None else "  -  "
        cont_s = f"{cont_r:+.3f}" if cont_r is not None else "  -  "
        func_s = f"{func_r:+.3f}" if func_r is not None else "  -  "
        all_n  = r["all"]["n"] if all_r is not None else 0
        cont_n = r["content"]["n"] if cont_r is not None else 0
        func_n = r["function"]["n"] if func_r is not None else 0
        print(f"{r['label']:<28} {r['n_segs']:>7} {r['n_words_freq3']:>8} "
              f"{all_s:>10} (n={all_n:>3}) {cont_s:>10}(n={cont_n:>3}) {func_s:>10}(n={func_n:>3})")
    print("=" * 100)
    print("(r = Pearson between mean_conf and confusion_rate (= 1 − recall); negative = confused words have low conf)")

    # Persist the structured results
    json.dump(results, open(os.path.join(args.out_dir, "conditional_correlations.json"), "w"), indent=2)
    print(f"\nWrote {os.path.join(args.out_dir, 'conditional_correlations.json')}")

    # Also: top confused content vs function words globally
    wd_all = per_word_stats(nbest, refs, conf, seg_filter=None)
    wd_all = wd_all[wd_all["freq"] >= 3].copy()
    wd_all["confusion_rate"] = 1.0 - wd_all["recall"]

    contents = wd_all[wd_all["is_function_word"] == False].sort_values(["recall", "freq"], ascending=[True, False])
    funcs = wd_all[wd_all["is_function_word"] == True].sort_values(["recall", "freq"], ascending=[True, False])

    contents.to_csv(os.path.join(args.out_dir, "content_words.csv"), index=False)
    funcs.to_csv(os.path.join(args.out_dir, "function_words.csv"), index=False)

    print("\n--- Top 15 most-confused CONTENT words (freq>=3) ---")
    print(contents[["word", "freq", "times_correct", "recall", "mean_conf", "mean_beam_disagree"]].head(15).round(3).to_string(index=False))
    print("\n--- Top 15 most-confused FUNCTION words (freq>=3) ---")
    print(funcs[["word", "freq", "times_correct", "recall", "mean_conf", "mean_beam_disagree"]].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
