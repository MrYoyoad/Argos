#!/usr/bin/env python3
"""Top-N most-confused content vs function words on a single n-best run.

Replacement for the slow `word_confusion_conditional.py` for the case we
actually care about: which content / function words does the model
mis-recognise most often, and what confidence does it report when it
*does* get them right? Single pass, no mask sweep, no Levenshtein over
20 beams per segment — runs in ~5s on the full 1,497-segment set.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from _alignment import align_word_lists, split_words  # noqa: E402
from analyze_beam_variance import _word_confs_for_utt  # noqa: E402

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbest", required=True)
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--confidence", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--top-n", type=int, default=15)
    ap.add_argument("--min-freq", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    nbest = json.load(open(args.nbest))
    hypo = json.load(open(args.hypo))
    conf = json.load(open(args.confidence))
    refs = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}

    # Per-word tallies. We track conf both when CORRECT and when WRONG so we can
    # report whether the model was confidently-wrong or quietly-wrong.
    freq = defaultdict(int)
    correct = defaultdict(int)
    conf_correct_sum = defaultdict(float)
    conf_correct_n = defaultdict(int)
    conf_wrong_sum = defaultdict(float)
    conf_wrong_n = defaultdict(int)

    for utt_id, rec in nbest.items():
        hyps = rec.get("hypotheses") or []
        if not hyps:
            continue
        top1_words = split_words(hyps[0].get("text", ""))
        ref_words = split_words(refs.get(utt_id, ""))
        for rw in ref_words:
            freq[rw.lower()] += 1
        conf_words = _word_confs_for_utt(conf.get(utt_id))
        pairs = align_word_lists([w.lower() for w in ref_words], [w.lower() for w in top1_words])
        for ri, hi in pairs:
            if ri < 0:
                continue
            target = ref_words[ri].lower()
            if hi >= 0 and ref_words[ri].lower() == top1_words[hi].lower():
                correct[target] += 1
                if hi < len(conf_words):
                    p = conf_words[hi][1]
                    if p is not None:
                        conf_correct_sum[target] += p
                        conf_correct_n[target] += 1
            else:
                # Substitution or deletion: if substitution, take the hyp-side conf
                # (the model said something at this position with that confidence).
                if hi >= 0 and hi < len(conf_words):
                    p = conf_words[hi][1]
                    if p is not None:
                        conf_wrong_sum[target] += p
                        conf_wrong_n[target] += 1

    rows = []
    for w, f in freq.items():
        if f < args.min_freq:
            continue
        rec = correct.get(w, 0)
        rows.append({
            "word": w,
            "freq": f,
            "times_correct": rec,
            "recall": rec / f,
            "mean_conf_when_correct": (conf_correct_sum[w] / conf_correct_n[w]) if conf_correct_n.get(w) else None,
            "n_conf_correct": conf_correct_n.get(w, 0),
            "mean_conf_when_wrong": (conf_wrong_sum[w] / conf_wrong_n[w]) if conf_wrong_n.get(w) else None,
            "n_conf_wrong": conf_wrong_n.get(w, 0),
            "is_function_word": w in FUNCTION_WORDS,
        })

    # Sort by lowest recall, freq as tiebreak (more frequent → more reliable signal)
    rows.sort(key=lambda r: (r["recall"], -r["freq"]))

    funcs = [r for r in rows if r["is_function_word"]]
    contents = [r for r in rows if not r["is_function_word"]]

    def write_csv(path, rows):
        if not rows:
            open(path, "w").write("")
            return
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)

    write_csv(os.path.join(args.out_dir, "content_words.csv"), contents)
    write_csv(os.path.join(args.out_dir, "function_words.csv"), funcs)

    def fmt_row(r):
        cw = f"{r['mean_conf_when_correct']:.3f}" if r["mean_conf_when_correct"] is not None else "  -  "
        ww = f"{r['mean_conf_when_wrong']:.3f}" if r["mean_conf_when_wrong"] is not None else "  -  "
        return f"  {r['word']:<18} freq={r['freq']:>3}  recall={r['recall']:.2f}  conf|correct={cw}  conf|wrong={ww}"

    print(f"\n=== Top {args.top_n} most-confused CONTENT words (freq >= {args.min_freq}) ===")
    for r in contents[:args.top_n]:
        print(fmt_row(r))
    print(f"\n=== Top {args.top_n} most-confused FUNCTION words (freq >= {args.min_freq}) ===")
    for r in funcs[:args.top_n]:
        print(fmt_row(r))
    print(f"\nTotals: {len(contents)} content word-types, {len(funcs)} function word-types (freq >= {args.min_freq})")
    print(f"Wrote {os.path.join(args.out_dir, 'content_words.csv')}, function_words.csv")


if __name__ == "__main__":
    main()
