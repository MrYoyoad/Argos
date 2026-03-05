#!/usr/bin/env python3
"""
Generate IS vs WER scatter plot for presentation.

Reads intelligibility_scores.csv and produces a dark-themed scatter plot
showing WER (x-axis) vs IS (y-axis), colored by IS tier. Highlights
"the gap" region where WER > 40% but IS >= 3.0.

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


def main():
    df = pd.read_csv(DATA)

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BG)
    ax.set_facecolor(BG)

    # Plot "the gap" region first (background)
    gap_rect = mpatches.FancyBboxPatch(
        (40, 3.0), 160, 2.0,  # x, y, width, height
        boxstyle="round,pad=0.02",
        facecolor=GREEN, alpha=0.08, edgecolor=GREEN, linewidth=1.5,
        linestyle="--", zorder=1)
    ax.add_patch(gap_rect)

    # Count points in the gap
    gap_mask = (df["wer_%"] > 40) & (df["intelligibility_score"] >= 3.0)
    gap_count = gap_mask.sum()

    # Label the gap region
    ax.text(120, 4.7, f"\"The Gap\": {gap_count} segments",
            color=GREEN, fontsize=13, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(120, 4.4, "High WER but genuinely useful output",
            color=GREEN, fontsize=10, alpha=0.8,
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

    # IS = 3.0 threshold line
    ax.axhline(y=3.0, color=LGRAY, linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)
    ax.text(2, 3.1, "IS = 3.0 (Captured threshold)", color=LGRAY,
            fontsize=9, alpha=0.7, va="bottom")

    # WER = 40% line
    ax.axvline(x=40, color=LGRAY, linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)

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
    print(f"Gap segments (WER>40%, IS>=3.0): {gap_count}")


if __name__ == "__main__":
    main()
