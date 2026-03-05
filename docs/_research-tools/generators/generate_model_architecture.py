#!/usr/bin/env python3
"""Regenerate the model architecture diagram with larger, more visible dimension labels."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUTPUT = Path("/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/model_architecture.png")
BG = "#0D1B2A"
TEAL = "#4DD0E1"
NAVY2 = "#1A2A3A"
CORAL = "#FF6B6B"
WHITE = "#FFFFFF"
LGRAY = "#B0BEC5"

def main():
    fig, ax = plt.subplots(figsize=(12, 3.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")

    # Box definitions: (x_center, width, height, label, sublabel, border_color, fill)
    boxes = [
        (1.0,  1.5, 1.6, "Video\nFrames", "", LGRAY, "#263238"),
        (3.5,  2.2, 1.6, "AV-HuBERT", "Visual Encoder", TEAL, "#1A3A4A"),
        (6.0,  1.4, 1.2, "Linear\nProj.", "", LGRAY, NAVY2),
        (8.5,  2.2, 1.6, "LLaMA-2-7B", "Language Model", TEAL, "#1A3A4A"),
        (11.0, 1.5, 1.6, "Text\nOutput", "", LGRAY, "#263238"),
    ]

    cy = 1.6  # vertical center

    for (cx, w, h, label, sub, border, fill) in boxes:
        rect = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                              boxstyle="round,pad=0.1",
                              facecolor=fill, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(cx, cy + 0.15 if sub else cy, label, ha="center", va="center",
                fontsize=14, fontweight="bold", color=WHITE)
        if sub:
            ax.text(cx, cy - 0.4, sub, ha="center", va="center",
                    fontsize=11, color=LGRAY)

    # Arrows between boxes
    arrow_pairs = [(1.75, 2.4), (4.6, 5.3), (6.7, 7.4), (9.6, 10.25)]
    for (x1, x2) in arrow_pairs:
        ax.annotate("", xy=(x2, cy), xytext=(x1, cy),
                    arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=2.5))

    # Dimension labels — LARGE and clearly visible above arrows
    dim_labels = [
        (3.05, "1024-dim", TEAL),
        (5.45, "1024→4096", WHITE),
        (8.05, "4096-dim", TEAL),
    ]
    for (x, text, color) in dim_labels:
        ax.text(x, cy + 1.05, text, ha="center", va="center",
                fontsize=13, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, edgecolor="none"))

    # Status labels below boxes
    ax.text(3.5, cy - 1.15, "Frozen", ha="center", fontsize=11, color=LGRAY)
    ax.text(6.0, cy - 0.9, "Trained", ha="center", fontsize=11,
            color=CORAL, fontweight="bold")
    ax.text(8.5, cy - 1.15, "Frozen", ha="center", fontsize=11, color=LGRAY)
    ax.text(8.5, cy - 1.5, "QLoRA r=16", ha="center", fontsize=11,
            color=CORAL, fontweight="bold")

    plt.tight_layout(pad=0.2)
    fig.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
