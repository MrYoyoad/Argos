"""Per-method confidence calibration analysis.

For each aggregation method, recompute the word-level confusion analysis
using THAT method's posterior per-word confidences and THAT method's
emitted hypothesis text (so recall is per-method, not just relative to
top-1). Tests:

  - Does aggregation IMPROVE calibration? I.e., does the Pearson r between
    (1 − recall_method) and (mean_posterior_conf_method) become more
    *negative* (= confidence tracks confusion better) for the voting/MBR
    methods than for top-1?
  - Where does that improvement concentrate — across all words, content
    only, function only, conditional on good segments?

Inputs:
  --aggregated path/aggregated.json   (already has word_confs per method)
  --hypo       path/hypo-{fid}.json   (refs)
  --confidence path/confidence-{fid}.json  (top-1 sentence_confidence for filters)
  --baseline-csv path/report.csv      (segment IS / WER for filters)
  --out-dir <dir>

Outputs:
  per_method_calibration.json   (Pearson r per method × filter × wordtype)
  per_method_calibration.csv    (flat table)
  per_method_summary.md         (Markdown summary)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
for _candidate in ("/home/ubuntu/lib", os.path.abspath(os.path.join(_HERE, "..", "..", "VSP-LLM", "scripts"))):
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from _alignment import align_word_lists, split_words  # noqa: E402

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

METHODS = ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_method_text_and_word_confs(agg_rec: dict, method: str) -> Tuple[str, List[Tuple[str, Optional[float]]]]:
    """Extract (text, word_confs) for a given method from an aggregated record."""
    if method == "hyp_top1":
        text = agg_rec.get("hyp_top1", "")
        wc = agg_rec.get("hyp_top1_word_confs", []) or []
    else:
        rec = agg_rec.get(method) or {}
        text = rec.get("text", "") if isinstance(rec, dict) else ""
        wc = (rec.get("word_confs") if isinstance(rec, dict) else None) or []
    # Normalize tuples loaded from JSON (lists) → (str, Optional[float])
    return text, [(w, p) for (w, p) in wc]


def per_word_stats_for_method(
    aggregated: Dict[str, dict],
    refs: Dict[str, str],
    method: str,
    seg_filter: Optional[set] = None,
) -> pd.DataFrame:
    """Build per-word table using the chosen aggregation method's text +
    per-word posterior confidences. Recall is computed against refs.
    """
    word_freq: Dict[str, int] = defaultdict(int)
    word_correct: Dict[str, int] = defaultdict(int)
    word_conf_sum: Dict[str, float] = defaultdict(float)
    word_conf_n: Dict[str, int] = defaultdict(int)

    for utt_id, agg in aggregated.items():
        if seg_filter is not None and utt_id not in seg_filter:
            continue
        text, wc = get_method_text_and_word_confs(agg, method)
        ref_words = split_words(refs.get(utt_id, ""))
        method_words = split_words(text)
        for rw in ref_words:
            word_freq[rw.lower()] += 1
        # Per-word conf list — must match length of method_words (it does because
        # words_with_conf already strips empty/special tokens before emission).
        # Defensive: pad/truncate to method_words length.
        confs = [None] * len(method_words)
        for i, (w, p) in enumerate(wc[: len(method_words)]):
            confs[i] = p

        ref_pairs = align_word_lists([w.lower() for w in ref_words], [w.lower() for w in method_words])
        for ri, hi in ref_pairs:
            if ri < 0 or hi < 0:
                continue
            if ref_words[ri].lower() != method_words[hi].lower():
                continue
            target = ref_words[ri].lower()
            word_correct[target] += 1
            if hi < len(confs) and confs[hi] is not None:
                word_conf_sum[target] += float(confs[hi])
                word_conf_n[target] += 1

    rows = []
    for word, freq in word_freq.items():
        rows.append({
            "word": word,
            "freq": int(freq),
            "times_correct": int(word_correct.get(word, 0)),
            "recall": word_correct.get(word, 0) / freq if freq else 0.0,
            "mean_conf": (word_conf_sum[word] / word_conf_n[word]) if word_conf_n.get(word) else None,
            "n_conf_obs": int(word_conf_n.get(word, 0)),
            "is_function_word": word in FUNCTION_WORDS,
        })
    return pd.DataFrame(rows)


def pearson_r(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[Optional[float], int]:
    d = df.dropna(subset=[x_col, y_col])
    if len(d) < 3:
        return None, len(d)
    x = d[x_col].to_numpy(dtype=float)
    y = d[y_col].to_numpy(dtype=float)
    if np.std(x) == 0 or np.std(y) == 0:
        return None, len(d)
    return float(np.corrcoef(x, y)[0, 1]), int(len(d))


def filter_for(seg_df: pd.DataFrame, filter_name: str, threshold: float) -> set:
    if filter_name == "all":
        return set(seg_df["utt_id"].tolist())
    if filter_name == "sent_conf":
        m = pd.to_numeric(seg_df["sentence_confidence"], errors="coerce") >= threshold
    elif filter_name == "is_score":
        m = pd.to_numeric(seg_df.get("is_score"), errors="coerce") >= threshold
    elif filter_name == "wer_pct_le":
        m = pd.to_numeric(seg_df.get("wer_%"), errors="coerce") <= threshold
    else:
        m = pd.Series(True, index=seg_df.index)
    return set(seg_df.loc[m, "utt_id"].tolist())


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggregated", required=True)
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--confidence", required=True)
    ap.add_argument("--baseline-csv", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-freq", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    aggregated = json.load(open(args.aggregated))
    hypo  = json.load(open(args.hypo))
    refs  = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}
    conf  = json.load(open(args.confidence))

    # Build segment-level features (same sentence_confidence as before).
    import analyze_beam_variance as ABV
    rows = []
    for utt_id in aggregated:
        wc = ABV._word_confs_for_utt(conf.get(utt_id))
        rows.append({
            "utt_id": utt_id,
            "sentence_confidence": float(np.mean([p for _, p in wc if p is not None])) if wc else None,
        })
    seg_df = pd.DataFrame(rows)
    if args.baseline_csv and os.path.isfile(args.baseline_csv):
        bdf = pd.read_csv(args.baseline_csv)
        cols = [c for c in ["utt_id", "wer_%", "wwer_%", "is_score", "is_tier"] if c in bdf.columns]
        seg_df = seg_df.merge(bdf[cols], on="utt_id", how="left")

    print(f"Loaded {len(aggregated)} segments × {len(METHODS)} methods")
    print(f"sentence_confidence mean: {seg_df['sentence_confidence'].mean():.3f}")

    # Filters
    filter_specs = [
        ("ALL",                "all",        None),
        ("sent_conf>=0.50",    "sent_conf",  0.50),
        ("sent_conf>=0.70",    "sent_conf",  0.70),
        ("sent_conf>=0.85",    "sent_conf",  0.85),
    ]
    if "is_score" in seg_df.columns:
        filter_specs += [
            ("IS>=2.00 (NIV-Y+P)", "is_score",   2.00),
            ("IS>=3.00",           "is_score",   3.00),
            ("IS>=3.80 (NIV-Y)",   "is_score",   3.80),
        ]

    # Run analysis
    results = []
    for fname, fkey, fthr in filter_specs:
        keep = filter_for(seg_df, fkey, fthr)
        for method in METHODS:
            wd = per_word_stats_for_method(aggregated, refs, method, seg_filter=keep)
            wd_freq = wd[wd["freq"] >= args.min_freq].copy()
            wd_freq["confusion_rate"] = 1.0 - wd_freq["recall"]
            funcs = wd_freq[wd_freq["is_function_word"] == True]
            contents = wd_freq[wd_freq["is_function_word"] == False]
            r_all, n_all = pearson_r(wd_freq, "mean_conf", "confusion_rate")
            r_func, n_func = pearson_r(funcs, "mean_conf", "confusion_rate")
            r_cont, n_cont = pearson_r(contents, "mean_conf", "confusion_rate")
            mean_conf = wd_freq["mean_conf"].mean(skipna=True)
            recall_mean = wd_freq["recall"].mean()
            results.append({
                "filter": fname,
                "method": method,
                "n_segs": len(keep),
                "n_words": len(wd_freq),
                "n_func": len(funcs),
                "n_content": len(contents),
                "mean_conf_emitted": float(mean_conf) if not np.isnan(mean_conf) else None,
                "mean_recall": float(recall_mean) if not np.isnan(recall_mean) else None,
                "r_all":      r_all,
                "n_all_pts":  n_all,
                "r_func":     r_func,
                "n_func_pts": n_func,
                "r_content":  r_cont,
                "n_content_pts": n_cont,
            })

    # Save full table + JSON
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(args.out_dir, "per_method_calibration.csv"), index=False)
    json.dump(results, open(os.path.join(args.out_dir, "per_method_calibration.json"), "w"), indent=2)

    # Pretty-print
    print()
    print("=" * 110)
    print(f"{'Filter':<22} {'Method':<18} {'n_words':>8} {'mean_conf':>10} {'r_all':>9} {'r_func':>9} {'r_content':>10}")
    print("-" * 110)
    for r in results:
        def fmt(v, fmts):
            return fmts.format(v) if isinstance(v, (int, float)) and v is not None else "  -  "
        all_s  = fmt(r["r_all"],     "{:+.3f}")
        func_s = fmt(r["r_func"],    "{:+.3f}")
        cont_s = fmt(r["r_content"], "{:+.3f}")
        mc_s   = fmt(r["mean_conf_emitted"], "{:.3f}")
        print(f"{r['filter']:<22} {r['method']:<18} {r['n_words']:>8} {mc_s:>10} {all_s:>9} {func_s:>9} {cont_s:>10}")
    print("=" * 110)
    print("(r negative = confused words have lower confidence; this is the desirable direction.)")

    # Markdown summary
    md_lines = ["# Per-Method Confidence Calibration Analysis", ""]
    md_lines.append(f"Tested on {len(aggregated)} segments. For each aggregation method, "
                    f"`mean_conf_emitted` is the average per-word posterior confidence the method "
                    f"reports, and `r_*` is Pearson(confusion_rate, mean_conf) — i.e. does the "
                    f"reported confidence track per-word correctness? (Negative = better signal.)")
    md_lines.append("")
    md_lines.append("## Headline numbers (ALL segments, all words freq>=" + str(args.min_freq) + ")\n")
    md_lines.append("| Method | mean conf | r (all) | r (function) | r (content) |")
    md_lines.append("|---|---|---|---|---|")
    for r in [x for x in results if x["filter"] == "ALL"]:
        def fmt(v, p="+.3f"): return ("{:" + p + "}").format(v) if isinstance(v, (int, float)) and v is not None else "—"
        md_lines.append(f"| {r['method']} | {fmt(r['mean_conf_emitted'], '.3f')} | "
                        f"{fmt(r['r_all'])} (n={r['n_all_pts']}) | "
                        f"{fmt(r['r_func'])} (n={r['n_func_pts']}) | "
                        f"{fmt(r['r_content'])} (n={r['n_content_pts']}) |")
    md_lines.append("")
    md_lines.append("## Conditional (sent_conf >= 0.70)\n")
    md_lines.append("| Method | mean conf | r (all) | r (function) | r (content) |")
    md_lines.append("|---|---|---|---|---|")
    for r in [x for x in results if x["filter"] == "sent_conf>=0.70"]:
        def fmt(v, p="+.3f"): return ("{:" + p + "}").format(v) if isinstance(v, (int, float)) and v is not None else "—"
        md_lines.append(f"| {r['method']} | {fmt(r['mean_conf_emitted'], '.3f')} | "
                        f"{fmt(r['r_all'])} (n={r['n_all_pts']}) | "
                        f"{fmt(r['r_func'])} (n={r['n_func_pts']}) | "
                        f"{fmt(r['r_content'])} (n={r['n_content_pts']}) |")
    open(os.path.join(args.out_dir, "per_method_summary.md"), "w").write("\n".join(md_lines))
    print(f"\nWrote {args.out_dir}/per_method_calibration.{{csv,json}}, per_method_summary.md")


if __name__ == "__main__":
    main()
