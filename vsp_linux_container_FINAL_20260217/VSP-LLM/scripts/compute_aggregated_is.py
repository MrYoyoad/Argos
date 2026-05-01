"""Compute Intelligibility Score (IS) for each n-best aggregation method.

The default `make_report.py --compute-is` only computes IS for the top-1
hypothesis. This script extends that — given the aggregated.json from
`lib/nbest_aggregate.py`, compute IS for each of the five aggregated methods
(MBR, vote_score, vote_conf, safe, xseg_merge) and emit per-method summaries.

Usage:
  python compute_aggregated_is.py \
      --hypo hypo-{fid}.json \
      --aggregated aggregated.json \
      --out aggregated_is.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
# Add VSP-LLM/scripts so we can import make_report's WWER/NEA helpers.
_VSP_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(_HERE), "..", "..", "VSP-LLM", "scripts"))
sys.path.insert(0, _VSP_SCRIPTS)

from generate_intelligibility_scores import (  # noqa: E402
    compute_is, compute_phonetic_similarity, compute_length_ratio,
    SemanticEncoder, HAS_EMBEDDINGS,
)
import make_report  # noqa: E402
compute_all_metrics = make_report.compute_all_metrics
toks = make_report.toks
import editdistance


METHODS = ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--aggregated", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    hypo = json.load(open(args.hypo))
    aggregated = json.load(open(args.aggregated))

    # Build {utt_id: ref}
    refs = {u: r for u, r in zip(hypo["utt_id"], hypo.get("ref", []))}

    # Method → list of hyp strings, in utt order. Filter to refs we have.
    utt_ids = [u for u in hypo["utt_id"] if u in aggregated and refs.get(u, "").strip()]

    method_texts: Dict[str, List[str]] = {m: [] for m in METHODS}
    refs_list: List[str] = []
    for u in utt_ids:
        agg = aggregated[u]
        refs_list.append(refs[u])
        for m in METHODS:
            v = agg.get(m)
            text = v if isinstance(v, str) else (v.get("text", "") if isinstance(v, dict) else "")
            method_texts[m].append(text)

    print(f"Loaded {len(utt_ids)} segments; computing IS for {len(METHODS)} methods")

    # Semantic similarity (batch via SemanticEncoder for efficiency)
    sem_per_method: Dict[str, List[float]] = {}
    if HAS_EMBEDDINGS:
        encoder = SemanticEncoder(device="auto")
        safe_refs = [r if r.strip() else "empty" for r in refs_list]
        for m in METHODS:
            safe_hyps = [h if h.strip() else "empty" for h in method_texts[m]]
            sims = encoder.similarities(safe_refs, safe_hyps)
            for i, (r, h) in enumerate(zip(refs_list, method_texts[m])):
                if not r.strip() or not h.strip():
                    sims[i] = 0.0
            sem_per_method[m] = [float(s) for s in sims]
            print(f"  semantic similarity computed for {m}: mean={np.mean(sem_per_method[m]):.3f}")
    else:
        print("  no semantic encoder — using 0.0 for all")
        for m in METHODS:
            sem_per_method[m] = [0.0] * len(utt_ids)

    # Per-method IS computation
    summary: Dict[str, dict] = {}
    per_segment: Dict[str, Dict[str, dict]] = {}
    for m in METHODS:
        scores: List[float] = []
        tiers: List[int] = []
        wers: List[float] = []
        per_segment[m] = {}
        for i, u in enumerate(utt_ids):
            ref = refs_list[i]
            hyp = method_texts[m][i]
            if not ref.strip():
                continue
            r_toks = toks(ref)
            h_toks = toks(hyp)
            wer_pct = (editdistance.eval(h_toks, r_toks) / len(r_toks) * 100) if r_toks else 0.0
            metrics = compute_all_metrics(ref, hyp)
            phon = compute_phonetic_similarity(ref, hyp)
            lr = compute_length_ratio(ref, hyp)
            score, tier, label = compute_is(
                semantic_sim=sem_per_method[m][i],
                phonetic_sim=phon["phonetic_sim"],
                wer_pct=wer_pct,
                wwer_pct=metrics.wwer,
                nea_f1_pct=metrics.nea_f1,
                length_ratio=lr,
            )
            scores.append(score)
            tiers.append(tier)
            wers.append(wer_pct)
            per_segment[m][u] = {"is": score, "tier": tier, "label": label, "wer": wer_pct}
        # NIV thresholds (March 2026): IS >= 3.80 = NIV-Y; >= 2.00 = NIV-Y+P
        n = len(scores) or 1
        summary[m] = {
            "mean_is": float(np.mean(scores)) if scores else 0.0,
            "median_is": float(np.median(scores)) if scores else 0.0,
            "mean_wer_pct": float(np.mean(wers)) if wers else 0.0,
            "captured_legacy_pct": 100.0 * sum(1 for s in scores if s >= 3.0) / n,
            "niv_y_pct":     100.0 * sum(1 for s in scores if s >= 3.80) / n,
            "niv_yp_pct":    100.0 * sum(1 for s in scores if s >= 2.00) / n,
            "tier_5_count": sum(1 for t in tiers if t == 5),
            "tier_4_count": sum(1 for t in tiers if t == 4),
            "tier_3_count": sum(1 for t in tiers if t == 3),
            "tier_2_count": sum(1 for t in tiers if t == 2),
            "tier_1_count": sum(1 for t in tiers if t == 1),
            "n_segments": n,
        }

    # Console table
    print("\n" + "=" * 88)
    print(f"{'Method':<22} {'IS mean':>9} {'WER %':>8} {'NIV-Y %':>10} {'NIV-Y+P %':>11} {'Δ IS vs top-1':>15}")
    print("-" * 88)
    base_is = summary["hyp_top1"]["mean_is"]
    for m in METHODS:
        s = summary[m]
        d = s["mean_is"] - base_is
        arrow = "↑" if d > 0 else ("↓" if d < 0 else "=")
        print(f"{m:<22} {s['mean_is']:>9.3f} {s['mean_wer_pct']:>8.2f} {s['niv_y_pct']:>10.1f} {s['niv_yp_pct']:>11.1f} {arrow}{abs(d):>13.3f}")
    print("=" * 88)

    out = {
        "summary": summary,
        "per_segment": per_segment,
        "n_segments": len(utt_ids),
        "methods": METHODS,
    }
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
