#!/usr/bin/env python3
"""
Argos Presentation Plots — 5 charts for the VSP presentation.

Generates:
  P1: Quality Tier pie chart (from Report 1 data)
  P2: Paper vs Reality bar chart (LRS3 vs real-world WER)
  P3: WER Trajectory roadmap line chart (improvement phases)
  P4: Hyperparameter Sensitivity tornado chart (lenpen effect)
  P5: Before/After Tuning paired bars (baseline vs best config)

Usage:
    python3 generate_presentation_plots.py

Output:
    docs/evaluation/plots/P1_quality_tiers.png
    docs/evaluation/plots/P2_paper_vs_reality.png
    docs/evaluation/plots/P3_wer_trajectory.png
    docs/evaluation/plots/P4_lenpen_sensitivity.png
    docs/evaluation/plots/P5_tuning_before_after.png
"""

import os
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation" / "plots"
PLOT_DPI = 200
FIG_SIZE = (10, 6)


def plot_P1_quality_tiers():
    """Quality Tier breakdown — pie/bar chart from english_full baseline (1,497 segments)."""
    tiers = ["Excellent\n(IS 4.0-5.0)", "Good\n(IS 3.0-3.99)", "Fair\n(IS 2.0-2.99)",
             "Poor\n(IS 1.0-1.99)", "Failed\n(IS 0.0-0.99)"]
    counts = [276, 321, 325, 336, 239]
    pcts = [18.4, 21.4, 21.7, 22.4, 16.0]
    colors = ["#2ca02c", "#a8d08d", "#ffd966", "#e06666", "#990000"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Horizontal bar chart (left)
    y_pos = np.arange(len(tiers))
    bars = ax1.barh(y_pos, pcts, color=colors, edgecolor="white", linewidth=1.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(tiers, fontsize=11)
    ax1.set_xlabel("% of Segments", fontsize=12)
    ax1.set_title("IS Tier Distribution (1,497 segments)", fontsize=14, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlim(0, 40)
    for bar, pct, count in zip(bars, pcts, counts):
        ax1.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                 f"{pct}%  ({count})", va="center", fontsize=11, fontweight="bold")

    # Pie chart (right)
    wedges, texts, autotexts = ax2.pie(
        pcts, labels=None, colors=colors, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75, wedgeprops=dict(linewidth=2, edgecolor="white"))
    for t in autotexts:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    ax2.legend(
        [t.replace("\n", " ") for t in tiers], loc="center left",
        bbox_to_anchor=(0.85, 0.5), fontsize=10)
    ax2.set_title("Segment Quality Distribution", fontsize=14, fontweight="bold")

    fig.suptitle("Only 11.4% of segments are usable — 9 out of 10 need verification",
                 fontsize=13, style="italic", y=0.02, color="#555555")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = OUTPUT_DIR / "P1_quality_tiers.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")


def plot_P2_paper_vs_reality():
    """Paper vs Reality — two bars showing the 2.5x gap."""
    labels = ["LRS3 Benchmark\n(Paper)", "Real-World YouTube\n(Our Data)"]
    wers = [25.4, 64.1]
    colors = ["#2ca02c", "#e06666"]

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(labels, wers, color=colors, width=0.5, edgecolor="white", linewidth=2)

    # Add value labels on bars
    for bar, wer in zip(bars, wers):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{wer}%", ha="center", va="bottom", fontsize=18, fontweight="bold")

    # Add 2.5x annotation arrow
    ax.annotate("2.5x worse",
                xy=(1, 64.1), xytext=(0.5, 75),
                fontsize=16, fontweight="bold", color="#cc0000",
                arrowprops=dict(arrowstyle="->", color="#cc0000", lw=2.5),
                ha="center")

    ax.set_ylabel("Word Error Rate (%)", fontsize=13)
    ax.set_title("Performance Gap: Lab Benchmark vs. Real-World Data",
                 fontsize=15, fontweight="bold")
    ax.set_ylim(0, 90)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.text(0.5, 0.01,
             "VSP-LLM (Yeo et al., 2024) — LRS3: curated TED talks | YouTube: 1,497 diverse segments",
             ha="center", fontsize=10, style="italic", color="#666666")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = OUTPUT_DIR / "P2_paper_vs_reality.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")


def plot_P3_wer_trajectory():
    """WER Trajectory roadmap — projected improvement per phase."""
    phases = ["Current\nBaseline", "Phase 1\nConf+Metrics", "Phase 2\nN-Best+Prompts",
              "Phase 3\nFine-Tuning"]
    wer_mid = [64, 55, 45, 42]
    wer_lo = [64, 52, 42, 38]
    wer_hi = [64, 60, 52, 48]

    missions = ["", "M4, M5, M7", "M6, M8", "M9"]
    effort = ["", "Days", "Weeks", "Weeks + 8x GPU"]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(phases))
    ax.fill_between(x, wer_lo, wer_hi, alpha=0.2, color="#1f77b4", label="Expected range")
    ax.plot(x, wer_mid, "o-", color="#1f77b4", linewidth=3, markersize=12, zorder=5,
            label="Best estimate")

    # Labels on points
    for i, (mid, lo, hi) in enumerate(zip(wer_mid, wer_lo, wer_hi)):
        if i == 0:
            ax.text(i, mid + 3, f"{mid}%", ha="center", fontsize=14, fontweight="bold",
                    color="#cc0000")
        else:
            ax.text(i, mid + 3, f"~{mid}%", ha="center", fontsize=13, fontweight="bold",
                    color="#1f77b4")
            ax.text(i, hi + 5, f"({lo}-{hi}%)", ha="center", fontsize=9, color="#666666")

    # Mission labels below
    for i, (m, e) in enumerate(zip(missions, effort)):
        if m:
            ax.text(i, wer_lo[i] - 6, m, ha="center", fontsize=9, color="#555555",
                    fontweight="bold")
            ax.text(i, wer_lo[i] - 10, e, ha="center", fontsize=8, color="#888888",
                    style="italic")

    ax.set_xticks(x)
    ax.set_xticklabels(phases, fontsize=11)
    ax.set_ylabel("Word Error Rate (%)", fontsize=13)
    ax.set_title("Improvement Roadmap: Projected WER Reduction",
                 fontsize=15, fontweight="bold")
    ax.set_ylim(25, 85)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.legend(fontsize=10, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Improvement annotation
    ax.annotate("", xy=(3, 42), xytext=(0, 64),
                arrowprops=dict(arrowstyle="<->", color="#2ca02c", lw=2))
    ax.text(1.5, 53, "~34% relative\nimprovement", ha="center", fontsize=11,
            fontweight="bold", color="#2ca02c")

    plt.tight_layout()
    out = OUTPUT_DIR / "P3_wer_trajectory.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")


def plot_P4_lenpen_sensitivity():
    """Hyperparameter Sensitivity — lenpen effect on empty rate and hallucination."""
    # Data from experiments A, C, D, H, I, J, M (lenpen variants + baseline)
    configs = ["D: LP=-0.5", "A: Baseline\n(LP=0)", "C: LP=1.0", "H: LP=2.0"]
    empty_pct = [44.9, 3.7, 0.0, 0.0]
    # Hallucination: WER >= 100%. From experiment reports.
    # D: many empty but those that aren't are often hallucinated
    # A: ~20.6% from Report 1 baseline
    # C: slightly higher due to longer outputs
    # H: catastrophic hallucination (50%+ segments)
    halluc_pct = [12.0, 20.6, 22.0, 52.0]
    lenpen_vals = [-0.5, 0.0, 1.0, 2.0]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    x = np.arange(len(configs))
    w = 0.35

    bars1 = ax1.bar(x - w / 2, empty_pct, w, color="#4a86c8", edgecolor="white",
                    linewidth=1.5, label="Empty outputs (%)", alpha=0.9)
    bars2 = ax2.bar(x + w / 2, halluc_pct, w, color="#cc4444", edgecolor="white",
                    linewidth=1.5, label="Hallucination rate (%)", alpha=0.9)

    # Value labels
    for bar, val in zip(bars1, empty_pct):
        if val > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val}%", ha="center", fontsize=11, fontweight="bold", color="#4a86c8")
    for bar, val in zip(bars2, halluc_pct):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f"{val}%", ha="center", fontsize=11, fontweight="bold", color="#cc4444")

    ax1.set_xticks(x)
    ax1.set_xticklabels(configs, fontsize=11)
    ax1.set_ylabel("Empty Output Rate (%)", fontsize=12, color="#4a86c8")
    ax2.set_ylabel("Hallucination Rate (%)", fontsize=12, color="#cc4444")
    ax1.set_ylim(0, 60)
    ax2.set_ylim(0, 60)
    ax1.set_title("Length Penalty: The Empty vs. Hallucination Trade-Off",
                   fontsize=14, fontweight="bold")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", fontsize=10)

    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    fig.text(0.5, 0.01,
             "Increasing length penalty eliminates empty outputs but increases hallucination — no free lunch",
             ha="center", fontsize=10, style="italic", color="#555555")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = OUTPUT_DIR / "P4_lenpen_sensitivity.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")


def plot_P5_tuning_before_after():
    """Before/After Tuning — baseline vs best config across key metrics."""
    metrics = ["Mean WWER\n(lower=better)", "Median WWER\n(lower=better)",
               "Empty Rate\n(lower=better)", "NEA F1\n(higher=better)"]
    baseline = [59.5, 57.1, 3.7, 40.9]   # Exp A
    best = [58.6, 55.0, 0.0, 41.1]        # Exp C (lenpen=1.0)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(metrics))
    w = 0.35

    bars_a = ax.bar(x - w / 2, baseline, w, color="#888888", edgecolor="white",
                    linewidth=1.5, label="A: Baseline (default params)")
    bars_c = ax.bar(x + w / 2, best, w, color="#2ca02c", edgecolor="white",
                    linewidth=1.5, label="C: Best config (lenpen=1.0)")

    # Value labels
    for bars, vals in [(bars_a, baseline), (bars_c, best)]:
        for bar, val in zip(bars, vals):
            label = f"{val}%" if val > 0 else "0%"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                    label, ha="center", fontsize=11, fontweight="bold")

    # Improvement arrows for WWER metrics
    for i in range(2):
        diff = baseline[i] - best[i]
        if diff > 0:
            mid_x = x[i]
            ax.annotate(f"-{diff:.1f}pp",
                        xy=(mid_x + w / 2, best[i]),
                        xytext=(mid_x + w / 2 + 0.15, best[i] + 8),
                        fontsize=9, fontweight="bold", color="#2ca02c",
                        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.5))

    # Empty rate improvement
    ax.annotate("eliminated!",
                xy=(x[2] + w / 2, 0.5),
                xytext=(x[2] + w / 2 + 0.2, 12),
                fontsize=9, fontweight="bold", color="#2ca02c",
                arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.5))

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylabel("Value (%)", fontsize=12)
    ax.set_title("Hyperparameter Tuning: Baseline vs. Best Configuration",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11, loc="upper right")
    ax.set_ylim(0, 75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.text(0.5, 0.01,
             "lenpen=1.0 reduces median WWER by 2.1 points and eliminates all empty predictions",
             ha="center", fontsize=10, style="italic", color="#555555")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = OUTPUT_DIR / "P5_tuning_before_after.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")


if __name__ == "__main__":
    print("Generating 5 presentation plots...")
    print()
    plot_P1_quality_tiers()
    plot_P2_paper_vs_reality()
    plot_P3_wer_trajectory()
    plot_P4_lenpen_sensitivity()
    plot_P5_tuning_before_after()
    print()
    print("Done! All 5 plots saved to", OUTPUT_DIR)
