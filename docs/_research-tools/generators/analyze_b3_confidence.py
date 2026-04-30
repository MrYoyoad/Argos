#!/usr/bin/env python3
"""B3 analysis: evaluate the sequence-confidence sidecar.

Loads `confidence-{fid}.json` (produced when VSP_OUTPUT_SCORES=1 was set
during decode) and the matching `hypo-{fid}.json`, computes WER per segment,
and reports:

  * Pearson r and Spearman ρ between sequence_score and WER
  * Per-segment table with seq_score, hypo, ref, wer
  * Word-confidence summary (mean, distribution across conf-high/med/low)
  * Sanity check: sequence_score histogram

Decision gate (per the plan): Pearson r <= -0.4 to keep the Tier-2 slide.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import List, Tuple

GENERATORS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GENERATORS_DIR))
from compute_word_confidence import aggregate_subtokens_to_words  # noqa: E402


def _wer(ref: str, hyp: str) -> float:
    """Plain word error rate, %."""
    r = ref.lower().split()
    h = hyp.lower().split()
    if not r:
        return 100.0 if h else 0.0
    n = len(r)
    m = len(h)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if r[i - 1] == h[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])
    return dp[n][m] / n * 100


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def _spearman(xs, ys):
    rx = {v: i for i, v in enumerate(sorted(set(xs)))}
    ry = {v: i for i, v in enumerate(sorted(set(ys)))}
    return _pearson([rx[x] for x in xs], [ry[y] for y in ys])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", type=Path, required=True,
                    help="directory containing hypo-*.json and confidence-*.json")
    args = ap.parse_args()

    hypo_files = sorted(args.results_dir.glob("hypo-*.json"))
    if not hypo_files:
        raise SystemExit(f"no hypo-*.json found in {args.results_dir}")
    hypo_files = [p for p in hypo_files if "merged" not in p.name]
    hypo_path = hypo_files[0]
    fid_match = re.search(r"hypo-(\d+)\.json", hypo_path.name)
    if not fid_match:
        raise SystemExit(f"could not parse fid from {hypo_path.name}")
    fid = fid_match.group(1)
    conf_path = args.results_dir / f"confidence-{fid}.json"
    if not conf_path.exists():
        raise SystemExit(f"sidecar not found: {conf_path}\n"
                         f"Did the run set VSP_OUTPUT_SCORES=1?")

    print(f"hypo:       {hypo_path}")
    print(f"confidence: {conf_path}")

    hypo_data = json.loads(hypo_path.read_text())
    conf_data = json.loads(conf_path.read_text())
    ids = hypo_data["utt_id"]
    refs = hypo_data["ref"]
    hyps = hypo_data["hypo"]

    rows: List[dict] = []
    for utt_id, ref, hyp in zip(ids, refs, hyps):
        seg = conf_data.get(utt_id)
        if not seg:
            continue
        seq = seg.get("sequence_score")
        wer = _wer(ref, hyp)
        words = aggregate_subtokens_to_words(seg.get("tokens", []))
        word_probs = [w["prob"] for w in words if w.get("prob") is not None]
        rows.append({
            "utt_id": utt_id,
            "ref": ref,
            "hyp": hyp,
            "wer": wer,
            "seq_score": seq,
            "n_words": len(words),
            "mean_word_prob": statistics.mean(word_probs) if word_probs else None,
            "min_word_prob": min(word_probs) if word_probs else None,
            "n_high": sum(1 for w in words if w["conf_class"] == "conf-high"),
            "n_med": sum(1 for w in words if w["conf_class"] == "conf-med"),
            "n_low": sum(1 for w in words if w["conf_class"] == "conf-low"),
        })

    n = len(rows)
    print(f"\nSegments analyzed: {n}")
    if n == 0:
        return

    # Per-segment table
    print(f"\n{'segment':<60} {'WER':>5}  {'seq':>8}  {'mean_p':>6}  {'min_p':>6}  H/M/L")
    print("-" * 110)
    for r in rows:
        seg_short = r["utt_id"][-55:]
        seq = f"{r['seq_score']:.3f}" if r['seq_score'] is not None else "  n/a "
        mp = f"{r['mean_word_prob']:.3f}" if r['mean_word_prob'] is not None else " n/a "
        mn = f"{r['min_word_prob']:.3f}" if r['min_word_prob'] is not None else " n/a "
        print(f"{seg_short:<60} {r['wer']:>5.1f}  {seq:>8}  {mp:>6}  {mn:>6}  "
              f"{r['n_high']}/{r['n_med']}/{r['n_low']}")

    # Correlations
    seqs = [r["seq_score"] for r in rows if r["seq_score"] is not None]
    seq_wers = [r["wer"] for r in rows if r["seq_score"] is not None]
    if len(seqs) >= 2:
        print(f"\nCorrelations (n={len(seqs)}):")
        print(f"  Pearson  r(seq_score, WER) = {_pearson(seqs, seq_wers):+.3f}")
        print(f"  Spearman ρ(seq_score, WER) = {_spearman(seqs, seq_wers):+.3f}")

    mean_ps = [r["mean_word_prob"] for r in rows if r["mean_word_prob"] is not None]
    mean_ws = [r["wer"] for r in rows if r["mean_word_prob"] is not None]
    if len(mean_ps) >= 2:
        print(f"  Pearson  r(mean_word_prob, WER) = {_pearson(mean_ps, mean_ws):+.3f}")
        print(f"  Spearman ρ(mean_word_prob, WER) = {_spearman(mean_ps, mean_ws):+.3f}")

    min_ps = [r["min_word_prob"] for r in rows if r["min_word_prob"] is not None]
    min_ws = [r["wer"] for r in rows if r["min_word_prob"] is not None]
    if len(min_ps) >= 2:
        print(f"  Pearson  r(min_word_prob, WER)  = {_pearson(min_ps, min_ws):+.3f}")
        print(f"  Spearman ρ(min_word_prob, WER)  = {_spearman(min_ps, min_ws):+.3f}")

    # Decision gate per plan
    if seqs:
        r = _pearson(seqs, seq_wers)
        verdict = "KEEP Tier-2 slide" if r <= -0.4 else "DROP Tier-2 slide"
        print(f"\n  Plan decision gate: Pearson r <= -0.4 → {verdict} (r={r:+.3f})")


if __name__ == "__main__":
    main()
