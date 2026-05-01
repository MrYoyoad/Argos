#!/usr/bin/env python3
"""Per-word band reliability stratified by segment quality.

Asks the question: when a word is shown GREEN to the user, can the user trust it
even if the surrounding segment has low overall confidence? This is the
"21 → 2 problem" — a fluent number latch with high prob inside an otherwise
broken segment.

Computes:
  - P(correct | band, segment mean_prob bucket)   for green / yellow / red
  - The "salvage threshold" T_salv where green stays >= 75% reliable
  - The "trust threshold" T_trust where green stays >= 90% reliable
  - Dangerous green-leakage cases (wrong+green words, especially numbers/entities)

Plots:
  band_reliability_by_segment_quality.png
  band_volume_by_segment_quality.png

Reuses the data loader from analyze_confidence_full.py.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GEN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN_DIR))
from analyze_confidence_full import (  # noqa: E402
    BG, NAVY2, TEAL, GREEN, GOLD, CORAL, ORANGE, PURPLE, WHITE, MGRAY, LGRAY,
    Segment, build_frame, _style_ax, _save, REPO_ROOT,
)
from compute_word_confidence import CONF_HIGH, CONF_MED  # noqa: E402
from _alignment import hyp_word_correctness, align_word_lists  # noqa: E402

PLOTS_DIR = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides"
DATA_DIR  = REPO_ROOT / "docs" / "confidence"


# ─────────────────────────────────────────────────────────────────────────────
# Build per-word frame
# ─────────────────────────────────────────────────────────────────────────────

def band(p: float) -> str:
    if p >= CONF_HIGH:
        return "green"
    if p >= CONF_MED:
        return "yellow"
    return "red"


def build_word_frame(segs: List[Segment]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for s in segs:
        if not s.words or not s.ref:
            continue
        hwords = [w["word"] for w in s.words]
        wprobs = [w.get("prob") for w in s.words]
        if not any(p is not None for p in wprobs):
            continue
        # Alignment for correctness
        correct = hyp_word_correctness(s.ref, hwords)
        # Also pull the aligned ref word (when substitution / match)
        ref_words = s.ref.lower().split()
        pairs = align_word_lists(ref_words, [w.lower() for w in hwords])
        h_to_r = {hi: ri for ri, hi in pairs if hi >= 0 and ri >= 0}
        # Segment-level mean_prob (token-level — matches the metric in Section 10)
        seg_mp = float(np.mean(s.token_probs)) if s.token_probs else None
        seg_mwp = float(np.mean(s.word_probs)) if s.word_probs else None
        for i, (w, p, c) in enumerate(zip(hwords, wprobs, correct)):
            if p is None:
                continue
            ri = h_to_r.get(i)
            rows.append({
                "utt_id": s.utt_id,
                "pos": i,
                "n_hyp_words": len(hwords),
                "word": w,
                "ref_word": ref_words[ri] if ri is not None else None,
                "prob": float(p),
                "band": band(float(p)),
                "correct": int(c),
                "seg_mean_prob": seg_mp,
                "seg_mean_word_prob": seg_mwp,
                "seg_is": s.is_score,
                "seg_wer": s.wer,
                "seg_niv": ("Y" if (s.is_score is not None and s.is_score >= 3.80) else
                            ("N" if (s.is_score is not None and s.is_score < 2.00) else "P")),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Analyses
# ─────────────────────────────────────────────────────────────────────────────

# Segment confidence buckets — chosen to cleanly span the operating regimes.
SEG_BUCKETS = [
    ("very low",  0.00, 0.40, CORAL),
    ("low",       0.40, 0.55, ORANGE),
    ("mid-low",   0.55, 0.65, GOLD),
    ("mid",       0.65, 0.75, TEAL),
    ("high",      0.75, 0.85, "#7ec8e3"),
    ("very high", 0.85, 1.01, GREEN),
]


def stratified_band_reliability(df: pd.DataFrame) -> pd.DataFrame:
    """For each (segment-mean_prob bucket × band), compute P(correct), n words."""
    rows = []
    for label, lo, hi, _ in SEG_BUCKETS:
        bk_mask = (df["seg_mean_prob"] >= lo) & (df["seg_mean_prob"] < hi)
        bk = df[bk_mask]
        for b in ["green", "yellow", "red"]:
            sub = bk[bk["band"] == b]
            n = len(sub)
            n_correct = int(sub["correct"].sum()) if n else 0
            rows.append({
                "bucket": label, "lo": lo, "hi": hi, "band": b,
                "n_words": n, "n_correct": n_correct,
                "p_correct": (n_correct / n) if n else float("nan"),
                "n_segments": int(bk["utt_id"].nunique()),
            })
    return pd.DataFrame(rows)


def green_leakage_examples(df: pd.DataFrame, n_examples: int = 30) -> pd.DataFrame:
    """The dangerous cases: GREEN word that is WRONG, in any segment."""
    bad_green = df[(df["band"] == "green") & (df["correct"] == 0)].copy()
    # Prefer cases where the ref word is a NUMBER or proper-noun-like token —
    # these are the most cognitively dangerous (the "21 → 2" pattern).
    def is_numeric(w):
        if not isinstance(w, str): return False
        return any(ch.isdigit() for ch in w) or w in {
            "one","two","three","four","five","six","seven","eight","nine","ten",
            "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen",
            "eighteen","nineteen","twenty","thirty","forty","fifty","sixty",
            "seventy","eighty","ninety","hundred","thousand","million","billion",
        }
    bad_green["ref_is_numeric"] = bad_green["ref_word"].apply(is_numeric)
    bad_green["hyp_is_numeric"] = bad_green["word"].apply(is_numeric)
    bad_green["both_numeric"] = bad_green["ref_is_numeric"] & bad_green["hyp_is_numeric"]
    # Sort: high prob first, numeric-vs-numeric first
    bad_green = bad_green.sort_values(
        ["both_numeric", "ref_is_numeric", "prob"],
        ascending=[False, False, False],
    )
    return bad_green.head(n_examples)


def find_thresholds(strat: pd.DataFrame) -> Dict[str, float]:
    """Find the segment mean_prob threshold where green band reliability hits
    each target. Linear interpolate between buckets."""
    g = strat[strat["band"] == "green"].copy()
    g = g.dropna(subset=["p_correct"])
    g = g.sort_values("lo")
    # Bucket midpoint = (lo + hi) / 2
    g["mid"] = (g["lo"] + g["hi"]) / 2

    def interp_for(target: float) -> float:
        # Find smallest bucket midpoint where p_correct >= target
        ys = g["p_correct"].values
        xs = g["mid"].values
        for i in range(len(ys)):
            if ys[i] >= target:
                if i == 0:
                    return xs[0]
                # Linear interpolate between i-1 and i
                x0, x1 = xs[i-1], xs[i]
                y0, y1 = ys[i-1], ys[i]
                if y1 == y0:
                    return x0
                return x0 + (target - y0) * (x1 - x0) / (y1 - y0)
        return float("inf")  # never hits target

    return {
        "T_salvage_75": interp_for(0.75),  # green is "useful" — show with caveat
        "T_safe_85":    interp_for(0.85),  # green is "trustworthy" — show normally
        "T_trust_90":   interp_for(0.90),  # green is "highly reliable" — show without warning
    }


# ─────────────────────────────────────────────────────────────────────────────
# Plots
# ─────────────────────────────────────────────────────────────────────────────

def plot_reliability(strat: pd.DataFrame, overall: Dict[str, float],
                     thresholds: Dict[str, float]) -> None:
    fig, ax = plt.subplots(figsize=(13, 8), dpi=200)
    fig.patch.set_facecolor(BG)
    _style_ax(ax)

    bucket_labels = [b[0] for b in SEG_BUCKETS]
    bucket_mids = [(b[1] + b[2]) / 2 for b in SEG_BUCKETS]

    band_colors = {"green": GREEN, "yellow": GOLD, "red": CORAL}
    for b in ["green", "yellow", "red"]:
        sub = strat[strat["band"] == b].copy().sort_values("lo")
        ys = sub["p_correct"].values * 100
        ns = sub["n_words"].values
        # Use bucket midpoints on x
        xs = ((sub["lo"] + sub["hi"]) / 2).values
        ax.plot(xs, ys, "o-", color=band_colors[b], linewidth=2.4, markersize=9,
                label=f"{b} (overall {overall[b]*100:.1f}%)")
        # Annotate counts at each bucket
        for x, y, n in zip(xs, ys, ns):
            if not np.isnan(y) and n > 30:
                ax.annotate(f"n={n}", (x, y), xytext=(0, 8), textcoords="offset points",
                            fontsize=7.5, color=WHITE, ha="center", alpha=0.85)

    # Reference horizontal lines at 75%, 85%, 90%
    for t, lab in [(75, "75% — useful with caveat"),
                   (85, "85% — trustworthy"),
                   (90, "90% — high trust")]:
        ax.axhline(t, color=LGRAY, linestyle=":", linewidth=1.0, alpha=0.5)
        ax.text(0.99, t + 0.5, lab, transform=ax.get_yaxis_transform(),
                fontsize=8.5, color=LGRAY, ha="right")

    # Vertical lines for the threshold answers
    if thresholds["T_salvage_75"] != float("inf") and thresholds["T_salvage_75"] < 1.0:
        ax.axvline(thresholds["T_salvage_75"], color=ORANGE, linestyle="--", linewidth=1.4,
                   alpha=0.8, label=f"T_salvage = {thresholds['T_salvage_75']:.2f} (green ≥75%)")
    if thresholds["T_safe_85"] != float("inf") and thresholds["T_safe_85"] < 1.0:
        ax.axvline(thresholds["T_safe_85"], color=GREEN, linestyle="--", linewidth=1.4,
                   alpha=0.8, label=f"T_trust = {thresholds['T_safe_85']:.2f} (green ≥85%)")

    ax.set_xlabel("Segment mean_prob (token-level)", color=WHITE, fontsize=12)
    ax.set_ylabel("P(word correct | band)  [%]", color=WHITE, fontsize=12)
    ax.set_title(
        "Band reliability vs segment quality\n"
        "Does the green band stay trustworthy when the segment as a whole is bad?",
        color=WHITE, fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=10)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_band_reliability_by_seg_quality.png")


def plot_volume(strat: pd.DataFrame) -> None:
    """Stacked volume by segment-mean_prob bucket — how many words at each band?"""
    fig, ax = plt.subplots(figsize=(13, 6), dpi=200)
    fig.patch.set_facecolor(BG)
    _style_ax(ax)
    bucket_labels = [b[0] for b in SEG_BUCKETS]
    bucket_mids = [(b[1] + b[2]) / 2 for b in SEG_BUCKETS]
    band_colors = {"green": GREEN, "yellow": GOLD, "red": CORAL}

    counts = {}
    for b in ["green", "yellow", "red"]:
        sub = strat[strat["band"] == b].sort_values("lo")
        counts[b] = sub["n_words"].values

    width = 0.07
    bottom_red = np.zeros(len(bucket_mids))
    ax.bar(bucket_mids, counts["red"], width=width, color=CORAL, alpha=0.85,
           label="red (p<0.40)", edgecolor="white", linewidth=0.4)
    bottom_yellow = counts["red"]
    ax.bar(bucket_mids, counts["yellow"], width=width, color=GOLD, alpha=0.85,
           bottom=bottom_yellow, label="yellow (0.40≤p<0.85)",
           edgecolor="white", linewidth=0.4)
    bottom_green = counts["red"] + counts["yellow"]
    ax.bar(bucket_mids, counts["green"], width=width, color=GREEN, alpha=0.85,
           bottom=bottom_green, label="green (p≥0.85)",
           edgecolor="white", linewidth=0.4)

    # Annotate totals on top
    totals = counts["red"] + counts["yellow"] + counts["green"]
    for x, t, lab in zip(bucket_mids, totals, bucket_labels):
        ax.annotate(f"{lab}\n{int(t)} words", (x, t),
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=8, color=WHITE, ha="center")

    ax.set_xlabel("Segment mean_prob bucket", color=WHITE, fontsize=12)
    ax.set_ylabel("Word count", color=WHITE, fontsize=12)
    ax.set_xlim(0, 1)
    ax.set_title(
        "Word band composition by segment quality\n"
        "Bad segments are mostly red — green words are rare in low-confidence segments",
        color=WHITE, fontsize=13, fontweight="bold", pad=12,
    )
    ax.legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=10)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_band_volume_by_seg_quality.png")


def plot_combined(strat: pd.DataFrame, overall: Dict[str, float],
                  thresholds: Dict[str, float], df_words: pd.DataFrame) -> None:
    """One figure, two panels: reliability (top) + per-segment green-rate distribution (bottom)."""
    fig, axs = plt.subplots(2, 1, figsize=(13, 11), dpi=200,
                            gridspec_kw={"height_ratios": [3, 2]})
    fig.patch.set_facecolor(BG)

    ax = axs[0]
    _style_ax(ax)
    band_colors = {"green": GREEN, "yellow": GOLD, "red": CORAL}
    for b in ["green", "yellow", "red"]:
        sub = strat[strat["band"] == b].copy().sort_values("lo")
        ys = sub["p_correct"].values * 100
        ns = sub["n_words"].values
        xs = ((sub["lo"] + sub["hi"]) / 2).values
        ax.plot(xs, ys, "o-", color=band_colors[b], linewidth=2.4, markersize=9,
                label=f"{b} band (overall {overall[b]*100:.1f}% correct)")
        for x, y, n in zip(xs, ys, ns):
            if not np.isnan(y) and n > 30:
                ax.annotate(f"n={n}", (x, y), xytext=(0, 8), textcoords="offset points",
                            fontsize=7.5, color=WHITE, ha="center", alpha=0.85)
    for t, lab in [(75, "75% — useful with caveat"),
                   (85, "85% — trustworthy"),
                   (90, "90% — high trust")]:
        ax.axhline(t, color=LGRAY, linestyle=":", linewidth=1.0, alpha=0.5)
        ax.text(0.99, t + 0.5, lab, transform=ax.get_yaxis_transform(),
                fontsize=8.5, color=LGRAY, ha="right")
    if thresholds["T_safe_85"] != float("inf") and thresholds["T_safe_85"] < 1.0:
        ax.axvline(thresholds["T_safe_85"], color=GREEN, linestyle="--", linewidth=1.4,
                   alpha=0.85, label=f"T_safe = {thresholds['T_safe_85']:.2f} (green ≥85%)")
    if thresholds["T_salvage_75"] != float("inf") and thresholds["T_salvage_75"] < 1.0:
        ax.axvline(thresholds["T_salvage_75"], color=ORANGE, linestyle="--", linewidth=1.4,
                   alpha=0.85, label=f"T_salv = {thresholds['T_salvage_75']:.2f} (green ≥75%)")
    ax.set_xlabel("Segment mean_prob (token-level)", color=WHITE, fontsize=11)
    ax.set_ylabel("P(word correct | band)  [%]", color=WHITE, fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 100)
    ax.set_title("Top: Band reliability stratified by segment quality",
                 color=WHITE, fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="lower right", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=9)

    # Bottom panel: stacked-bar volume by bucket
    ax2 = axs[1]
    _style_ax(ax2)
    bucket_labels = [b[0] for b in SEG_BUCKETS]
    bucket_mids = [(b[1] + b[2]) / 2 for b in SEG_BUCKETS]
    counts = {b: strat[strat["band"] == b].sort_values("lo")["n_words"].values
              for b in ["green", "yellow", "red"]}
    width = 0.07
    ax2.bar(bucket_mids, counts["red"], width=width, color=CORAL, alpha=0.9,
            label="red", edgecolor="white", linewidth=0.4)
    ax2.bar(bucket_mids, counts["yellow"], width=width, color=GOLD, alpha=0.9,
            bottom=counts["red"], label="yellow",
            edgecolor="white", linewidth=0.4)
    ax2.bar(bucket_mids, counts["green"], width=width, color=GREEN, alpha=0.9,
            bottom=counts["red"] + counts["yellow"], label="green",
            edgecolor="white", linewidth=0.4)
    totals = counts["red"] + counts["yellow"] + counts["green"]
    for x, t, lab in zip(bucket_mids, totals, bucket_labels):
        if t > 0:
            ax2.annotate(f"{lab}\n{int(t)}w", (x, t),
                         xytext=(0, 6), textcoords="offset points",
                         fontsize=8, color=WHITE, ha="center")
    ax2.set_xlabel("Segment mean_prob bucket", color=WHITE, fontsize=11)
    ax2.set_ylabel("Word count", color=WHITE, fontsize=11)
    ax2.set_xlim(0, 1)
    ax2.set_title("Bottom: Word band composition by segment quality",
                  color=WHITE, fontsize=12, fontweight="bold", pad=10)
    ax2.legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY,
               labelcolor=WHITE, fontsize=9)

    fig.suptitle(
        "Per-word band reliability vs whole-segment confidence\n"
        "If the user can read coloured words and self-filter, where can we safely show segments?",
        color=WHITE, fontsize=14, fontweight="bold", y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, PLOTS_DIR / "conf_band_reliability_combined.png")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--confidence-sidecar", type=Path,
                   default=Path("/tmp/vsp_b3_1497_out/confidence-172610.json"))
    p.add_argument("--hypo", type=Path,
                   default=Path("/tmp/vsp_b3_1497_out/hypo-172610.json"))
    p.add_argument("--baseline-csv", type=Path,
                   default=REPO_ROOT / "english_full_results" / "client_outputs" / "report" / "report.csv")
    args = p.parse_args()

    print("Loading...")
    segs, _diag = build_frame(args.confidence_sidecar, args.hypo, args.baseline_csv)
    print(f"Building word frame from {len(segs)} segments...")
    df = build_word_frame(segs)
    df = df.dropna(subset=["seg_mean_prob"])
    print(f"  {len(df):,} words from {df['utt_id'].nunique():,} segments")

    # Overall band reliability (matches Section 2 calibration)
    overall = {}
    for b in ["green", "yellow", "red"]:
        sub = df[df["band"] == b]
        overall[b] = sub["correct"].mean() if len(sub) else float("nan")
        print(f"  Overall P(correct | {b}): {overall[b]*100:.1f}%  (n={len(sub):,})")

    # Stratified by segment quality
    strat = stratified_band_reliability(df)
    print("\nStratified P(correct | band, segment mean_prob bucket):")
    pivot = strat.pivot(index="bucket", columns="band", values="p_correct")
    counts = strat.pivot(index="bucket", columns="band", values="n_words")
    bucket_order = [b[0] for b in SEG_BUCKETS]
    pivot = pivot.reindex(bucket_order)
    counts = counts.reindex(bucket_order)
    print((pivot * 100).round(1).to_string())
    print("\nWord counts per bucket × band:")
    print(counts.astype(int).to_string())

    # Threshold analysis
    thresholds = find_thresholds(strat)
    print("\nThresholds (interpolated):")
    for k, v in thresholds.items():
        print(f"  {k}: seg_mean_prob = {v:.3f}" if v != float("inf") else f"  {k}: never reached")

    # Plot
    plot_combined(strat, overall, thresholds, df)
    plot_reliability(strat, overall, thresholds)
    plot_volume(strat)

    # Dangerous green-leakage examples
    leak = green_leakage_examples(df, n_examples=40)
    print(f"\nFound {len(df[(df['band']=='green') & (df['correct']==0)]):,} wrong-and-green words. "
          f"Top {len(leak)} most dangerous (numeric/entity, high prob):")
    cols_show = ["utt_id", "pos", "word", "ref_word", "prob", "seg_mean_prob",
                 "seg_is", "seg_wer", "ref_is_numeric", "both_numeric"]
    cols_show = [c for c in cols_show if c in leak.columns]
    print(leak[cols_show].head(20).to_string(index=False))

    # Save the leakage table for the doc
    leak_path = DATA_DIR / "green_leakage_examples.csv"
    leak.to_csv(leak_path, index=False)
    print(f"\nSaved {leak_path.relative_to(REPO_ROOT)}")

    # Also save the stratified summary
    strat_path = DATA_DIR / "band_reliability_by_segment_quality.csv"
    out = strat.copy()
    out["p_correct_pct"] = (out["p_correct"] * 100).round(2)
    out.to_csv(strat_path, index=False)
    print(f"Saved {strat_path.relative_to(REPO_ROOT)}")

    # Compute and save aggregate metrics for the writeup
    summary = {
        "overall": {b: overall[b] for b in overall},
        "thresholds": thresholds,
        "n_words_total": int(len(df)),
        "n_segments_total": int(df["utt_id"].nunique()),
        "n_wrong_green_total": int(((df["band"] == "green") & (df["correct"] == 0)).sum()),
        "n_wrong_green_in_lowq_segments": int(
            ((df["band"] == "green") & (df["correct"] == 0) & (df["seg_mean_prob"] < 0.65)).sum()
        ),
        "n_correct_red_in_highq_segments": int(
            ((df["band"] == "red") & (df["correct"] == 1) & (df["seg_mean_prob"] >= 0.85)).sum()
        ),
    }
    print("\nSummary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
