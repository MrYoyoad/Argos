#!/usr/bin/env python3
"""
Generate dual radar chart: LRS3 benchmark vs Real-World YouTube.

Overlays two radar profiles on 6 IS dimensions to visualize the domain
shift between clean benchmark data and real-world YouTube content.

Output: presentation_materials_20260224/01_plots_for_slides/P6b_radar_dual.png
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/P6b_radar_dual.png")

# Presentation color scheme
BG = "#0D1B2A"
NAVY2 = "#152A40"
WHITE = "#FFFFFF"
LGRAY = "#AAAAAA"
TEAL = "#00B4D8"
CORAL = "#E06C75"
GREEN = "#4CAF50"

# 6 IS dimensions
LABELS = [
    "Semantic\nSimilarity",
    "Phonetic\nSimilarity",
    "WER\n(inverted)",
    "WWER\n(inverted)",
    "Named Entity\nAccuracy",
    "Length\nRatio",
]

# LRS3 benchmark profile — MEASURED from real LRS3 decode (March 2026)
# Decoded 197 LRS3 pretrain segments through our pipeline (VSP-LLM + flat k-means).
# V1: 224x224 LRS3 videos with YouTube-trained k-means. Overall WER 36.5%.
# Values below are means across all 170 non-empty segments (empties excluded).
# Source: /tmp/lrs3_decode/is_v1/intelligibility_scores.csv
LRS3_VALUES = [
    0.779,  # Semantic similarity (measured, n=170 LRS3 TED talk segments)
    0.794,  # Phonetic similarity (measured)
    0.689,  # 1 - WER (measured)
    0.662,  # 1 - WWER (measured)
    0.683,  # Named entity F1 (measured)
    0.971,  # Length ratio (measured)
]

# Real-world YouTube profile (our baseline: WER 64.1%, IS 2.53)
YOUTUBE_VALUES = [
    0.58,   # Semantic similarity (mean from our data)
    0.52,   # Phonetic similarity (mean)
    0.36,   # 1 - WER (1 - 0.641 = 0.359)
    0.40,   # 1 - WWER (1 - 0.605 = 0.395)
    0.39,   # Named entity F1 (38.9%)
    0.72,   # Length ratio (mean, many short/long predictions)
]


def main():
    N = len(LABELS)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    lrs3 = LRS3_VALUES + LRS3_VALUES[:1]
    youtube = YOUTUBE_VALUES + YOUTUBE_VALUES[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True),
                           facecolor=BG)
    ax.set_facecolor(BG)

    # Grid styling
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"],
                        color=LGRAY, fontsize=8, alpha=0.6)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(LABELS, color=WHITE, fontsize=11, fontweight="bold")

    # Grid lines
    ax.spines["polar"].set_color(LGRAY)
    ax.spines["polar"].set_alpha(0.2)
    ax.grid(color=LGRAY, alpha=0.15, linewidth=0.5)

    # LRS3 benchmark (green, tight, small)
    ax.plot(angles, lrs3, color=GREEN, linewidth=2.5, linestyle="-",
            label="LRS3 Benchmark (WER 25.4%)", zorder=3)
    ax.fill(angles, lrs3, color=GREEN, alpha=0.15, zorder=2)

    # YouTube real-world (coral, jagged, large gaps)
    ax.plot(angles, youtube, color=CORAL, linewidth=2.5, linestyle="-",
            label="Real-World YouTube (WER 64.1%)", zorder=3)
    ax.fill(angles, youtube, color=CORAL, alpha=0.15, zorder=2)

    # Legend
    legend = ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1),
                       fontsize=11, framealpha=0.3,
                       facecolor=NAVY2, edgecolor=LGRAY)
    for text in legend.get_texts():
        text.set_color(WHITE)

    # Title annotation
    ax.text(0.5, -0.08,
            "The Domain Gap: clean benchmark vs real-world conditions",
            transform=ax.transAxes, ha="center", color=LGRAY,
            fontsize=12, fontstyle="italic")

    plt.tight_layout(pad=2.0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
