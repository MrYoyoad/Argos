#!/usr/bin/env python3
"""
Generate IS vs WER scatter plot for presentation — NIV thresholds.

Reads intelligibility_scores.csv and produces a dark-themed scatter plot
showing WER (x-axis) vs IS (y-axis), colored by IS tier. Shows two NIV
gap regions:
  - Y gap: IS >= 3.80 AND WER > 34% (meaning clearly conveyed, WER rejects)
  - Y+P gap: IS >= 2.00 AND WER > 77% (any useful meaning, even generous WER rejects)
Also highlights the large "conventional gap": IS >= 2.00 AND WER > 40%.

NIV thresholds (March 2026): empirically calibrated against Opus-as-a-Judge.
  IS >= 3.80 for Y (κ=0.690), IS >= 2.00 for Y+P (κ=0.818).
  WER <= 34% for Y (κ=0.629), WER <= 77% for Y+P (κ=0.777).

Output: presentation_materials_20260224/01_plots_for_slides/P7_is_wer_scatter.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Paths
DATA = Path("/home/ubuntu/presentation_materials_20260224/05_data/intelligibility_scores.csv")
OUT = Path("/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/P7_is_wer_scatter.png")

# Presentation color scheme
BG = "#0D1B2A"
NAVY2 = "#152A40"
WHITE = "#FFFFFF"
LGRAY = "#AAAAAA"
TEAL = "#00B4D8"
CORAL = "#E06C75"
GREEN = "#4CAF50"
GOLD = "#FFD54F"
RED = "#F44336"
AMBER = "#FFA726"

# IS tier colors (5=excellent to 1=failed)
TIER_COLORS = {
    5: GREEN,
    4: TEAL,
    3: GOLD,
    2: CORAL,
    1: RED,
}
TIER_LABELS = {
    5: "Excellent (4.0-5.0)",
    4: "Good (3.0-3.99)",
    3: "Fair (2.0-2.99)",
    2: "Poor (1.0-1.99)",
    1: "Failed (0.0-0.99)",
}

# NIV thresholds
NIV_Y_IS = 3.80
NIV_Y_WER = 34
NIV_YP_IS = 2.00
NIV_YP_WER = 77


def main():
    df = pd.read_csv(DATA)

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BG)
    ax.set_facecolor(BG)

    # --- Gap region 1: Y gap (IS >= 3.80 AND WER > 34%) ---
    gap_y_rect = mpatches.FancyBboxPatch(
        (NIV_Y_WER, NIV_Y_IS), 170, 5.0 - NIV_Y_IS,
        boxstyle="round,pad=0.02",
        facecolor=GREEN, alpha=0.10, edgecolor=GREEN, linewidth=1.5,
        linestyle="--", zorder=1)
    ax.add_patch(gap_y_rect)

    gap_y_mask = (df["wer_%"] > NIV_Y_WER) & (df["intelligibility_score"] >= NIV_Y_IS)
    gap_y_count = gap_y_mask.sum()

    ax.text(120, 4.7, f"Y gap: {gap_y_count} segments",
            color=GREEN, fontsize=12, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(120, 4.45, "Clearly conveyed but WER > 34%",
            color=GREEN, fontsize=9, alpha=0.8,
            ha="center", va="center", zorder=5)

    # --- Gap region 2: Y+P conventional gap (IS >= 2.00 AND WER > 40%) ---
    gap_yp_rect = mpatches.FancyBboxPatch(
        (40, NIV_YP_IS), 160, NIV_Y_IS - NIV_YP_IS,
        boxstyle="round,pad=0.02",
        facecolor=AMBER, alpha=0.06, edgecolor=AMBER, linewidth=1.2,
        linestyle=":", zorder=1)
    ax.add_patch(gap_yp_rect)

    gap_yp_mask = (df["wer_%"] > 40) & (df["intelligibility_score"] >= NIV_YP_IS) & (df["intelligibility_score"] < NIV_Y_IS)
    gap_yp_count = gap_yp_mask.sum()

    ax.text(130, 2.85, f"Y+P gap: {gap_yp_count} segments",
            color=AMBER, fontsize=11, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(130, 2.60, "Useful meaning but WER > 40%",
            color=AMBER, fontsize=9, alpha=0.8,
            ha="center", va="center", zorder=5)

    # Scatter by tier (plot lower tiers first so higher tiers are on top)
    for tier in [1, 2, 3, 4, 5]:
        mask = df["intelligibility_tier"] == tier
        subset = df[mask]
        ax.scatter(
            subset["wer_%"], subset["intelligibility_score"],
            c=TIER_COLORS[tier], s=18, alpha=0.55, edgecolors="none",
            label=f"Tier {tier}: {TIER_LABELS[tier]} (n={len(subset)})",
            zorder=2 + tier)

    # NIV Y threshold line (IS = 3.80)
    ax.axhline(y=NIV_Y_IS, color=GREEN, linewidth=1.0, linestyle="--", alpha=0.6, zorder=1)
    ax.text(2, NIV_Y_IS + 0.08, f"NIV Y: IS = {NIV_Y_IS} (κ=0.690)",
            color=GREEN, fontsize=9, alpha=0.8, va="bottom")

    # NIV Y+P threshold line (IS = 2.00)
    ax.axhline(y=NIV_YP_IS, color=AMBER, linewidth=1.0, linestyle="--", alpha=0.6, zorder=1)
    ax.text(2, NIV_YP_IS + 0.08, f"NIV Y+P: IS = {NIV_YP_IS} (κ=0.818)",
            color=AMBER, fontsize=9, alpha=0.8, va="bottom")

    # NIV WER lines
    ax.axvline(x=NIV_Y_WER, color=GREEN, linewidth=0.8, linestyle=":", alpha=0.4, zorder=1)
    ax.axvline(x=40, color=LGRAY, linewidth=0.8, linestyle=":", alpha=0.3, zorder=1)
    ax.text(41, 0.15, "WER 40%\n(conventional)", color=LGRAY,
            fontsize=7, alpha=0.5, va="bottom")

    # Formatting
    ax.set_xlabel("Word Error Rate (%)", color=WHITE, fontsize=13, labelpad=10)
    ax.set_ylabel("Intelligibility Score", color=WHITE, fontsize=13, labelpad=10)
    ax.set_xlim(-2, 210)
    ax.set_ylim(-0.1, 5.2)

    ax.tick_params(colors=LGRAY, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)

    # Legend
    legend = ax.legend(loc="lower left", fontsize=9, framealpha=0.3,
                       facecolor=NAVY2, edgecolor=LGRAY, labelcolor=WHITE)
    for text in legend.get_texts():
        text.set_color(WHITE)

    plt.tight_layout(pad=1.0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT}")
    print(f"Y gap (IS>={NIV_Y_IS}, WER>{NIV_Y_WER}%): {gap_y_count}")
    print(f"Y+P gap (IS>={NIV_YP_IS}, WER>40%, IS<{NIV_Y_IS}): {gap_yp_count}")


if __name__ == "__main__":
    main()
