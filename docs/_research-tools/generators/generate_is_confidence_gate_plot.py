#!/usr/bin/env python3
"""Tier-1 confidence-gate plot — what IS actually predicts about WER.

Real data, no GPU run needed. Computed against
english_full_results/client_outputs/report/report.csv (1,497 segments).

Two plots side-by-side:
  Left  — median WER per IS tier (the conditional staircase)
  Right — IS as a binary "trust gate" (precision/recall sweep)

Output:
  presentation_materials_20260224/01_plots_for_slides/is_confidence_gate.png

Run:
  python3 docs/_research-tools/generators/generate_is_confidence_gate_plot.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = REPO_ROOT / "english_full_results" / "client_outputs" / "report" / "report.csv"
OUT_PATH = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides" / "is_confidence_gate.png"

# Brand palette — match deck's slides_client.py
BG     = "#0d1b2a"
NAVY2  = "#152a40"
TEAL   = "#00b4d8"
GREEN  = "#4caf50"
GOLD   = "#ffd54f"
CORAL  = "#e06c75"
WHITE  = "#ffffff"
LGRAY  = "#aaaaaa"
MGRAY  = "#666666"


def _load():
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    out = []
    for r in rows:
        try:
            is_score = float(r["is_score"])
            wer = float(r["wer_%"])
        except (ValueError, KeyError):
            continue
        out.append((is_score, wer))
    return out


def _plot():
    paired = _load()
    n = len(paired)

    # Tier bins
    tiers = [
        ("IS 4–5\n(Excellent)", 4.0, 5.01, GREEN),
        ("IS 3–4\n(Good)",      3.0, 4.0,  TEAL),
        ("IS 2–3\n(Fair)",      2.0, 3.0,  GOLD),
        ("IS 1–2\n(Poor)",      1.0, 2.0,  "#ff9800"),
        ("IS <1\n(Failed)",     0.0, 1.0,  CORAL),
    ]
    labels, lows, highs, colors = zip(*tiers)
    bucket_wers = []
    bucket_n = []
    for lo, hi in zip(lows, highs):
        bucket = [w for i, w in paired if lo <= i < hi]
        if bucket:
            bucket.sort()
            bucket_wers.append(bucket[len(bucket) // 2])  # median
            bucket_n.append(len(bucket))
        else:
            bucket_wers.append(0)
            bucket_n.append(0)

    fig = plt.figure(figsize=(13, 5.6), dpi=160)
    fig.patch.set_facecolor(BG)

    # ── Left: median WER per IS tier (staircase) ──
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_facecolor(NAVY2)
    bars = ax1.bar(range(len(tiers)), bucket_wers, color=colors,
                   edgecolor=WHITE, linewidth=0.8, width=0.72)
    ax1.set_xticks(range(len(tiers)))
    ax1.set_xticklabels(labels, color=WHITE, fontsize=10)
    ax1.set_ylabel("Median WER  (lower is better)", color=WHITE, fontsize=11)
    ax1.set_title("Higher confidence → lower error",
                  color=WHITE, fontsize=14, fontweight="bold", pad=14)
    ax1.set_ylim(0, max(bucket_wers) * 1.18)
    ax1.tick_params(colors=WHITE)
    for spine in ax1.spines.values():
        spine.set_color(MGRAY)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.yaxis.grid(True, color=MGRAY, alpha=0.25)

    # Annotations
    for i, (bar, wer, count) in enumerate(zip(bars, bucket_wers, bucket_n)):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + max(bucket_wers) * 0.02,
                 f"{wer:.0f}%", ha="center", va="bottom",
                 color=WHITE, fontsize=14, fontweight="bold")
        ax1.text(bar.get_x() + bar.get_width() / 2, -max(bucket_wers) * 0.04,
                 f"n={count}", ha="center", va="top",
                 color=LGRAY, fontsize=9)

    # ── Right: precision-recall as IS threshold sweeps ──
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor(NAVY2)
    wer_threshold = 50.0  # "good" segment definition
    is_thresholds = [round(x * 0.1, 1) for x in range(5, 51)]  # 0.5..5.0
    precs, recs = [], []
    for thr in is_thresholds:
        tp = sum(1 for i, w in paired if i >= thr and w <= wer_threshold)
        fp = sum(1 for i, w in paired if i >= thr and w > wer_threshold)
        fn = sum(1 for i, w in paired if i < thr and w <= wer_threshold)
        precs.append(tp / (tp + fp) * 100 if (tp + fp) else 0)
        recs.append(tp / (tp + fn) * 100 if (tp + fn) else 0)

    ax2.plot(is_thresholds, precs, color=GREEN, linewidth=2.5, label="Precision")
    ax2.plot(is_thresholds, recs, color=GOLD, linewidth=2.5, label="Recall")
    ax2.axvline(3.80, color=TEAL, linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.text(3.85, 8, "IS ≥ 3.80\n(clearly\nconveyed)",
             color=TEAL, fontsize=9, fontweight="bold", va="bottom")

    ax2.set_xlabel("Confidence threshold (IS score)", color=WHITE, fontsize=11)
    ax2.set_ylabel("Percent", color=WHITE, fontsize=11)
    ax2.set_title(f"IS as a trust gate  (vs WER ≤ {wer_threshold:.0f}%)",
                  color=WHITE, fontsize=14, fontweight="bold", pad=14)
    ax2.set_ylim(0, 105)
    ax2.set_xlim(0.5, 5.0)
    ax2.tick_params(colors=WHITE)
    for spine in ax2.spines.values():
        spine.set_color(MGRAY)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.yaxis.grid(True, color=MGRAY, alpha=0.25)
    leg = ax2.legend(loc="lower left", facecolor=NAVY2, edgecolor=MGRAY,
                     labelcolor=WHITE, fontsize=11, framealpha=0.95)

    # Anchor annotation: the killer fact
    ax2.annotate(
        "At IS ≥ 3.80:\n100% precision",
        xy=(3.80, 100), xytext=(2.4, 88),
        color=GREEN, fontsize=11, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
    )

    fig.suptitle(
        f"Tier-1 confidence is real — n={n:,} real-world segments",
        color=WHITE, fontsize=12, y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, facecolor=BG, dpi=160, bbox_inches="tight")
    print(f"Wrote {OUT_PATH}")
    print(f"  segments: {n:,}")
    print(f"  staircase WERs: {[f'{w:.0f}%' for w in bucket_wers]}")
    print(f"  precision at IS≥3.80 (vs WER≤50%): {precs[is_thresholds.index(3.8)]:.1f}%")


if __name__ == "__main__":
    _plot()
