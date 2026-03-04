#!/usr/bin/env python3
"""
Generate a professional pipeline architecture diagram for the VSP presentation.
Shows 8 pipeline stages in 2 rows of 4 with navy background, data-flow arrows,
and component labels.

Usage:
    python3 generate_pipeline_diagram.py

Output:
    docs/evaluation/plots/pipeline_architecture.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUTPUT = "/home/ubuntu/docs/evaluation/plots/pipeline_architecture.png"

# ── Color Palette (presentation theme) ──────────────────────
BG      = "#0D1B2A"
TEAL    = "#00B4D8"
CORAL   = "#E06C75"
GREEN   = "#56B870"
GOLD    = "#FFD966"
WHITE   = "#FFFFFF"
LGRAY   = "#8899AA"
DGRAY   = "#1B2D44"
ARROW_C = "#5599BB"

# Stage colours: preprocessing=teal, core=green, model=gold, output=coral
STAGE_COLORS = [TEAL, TEAL, TEAL, TEAL, GREEN, GREEN, GOLD, CORAL]

STAGES = [
    ("1. Normalize",      "HDR/10-bit\nconversion"),
    ("2. ASR\n(Whisper)",  "Speech-to-text\ntranscription"),
    ("3. Mouth Crop",     "Face detection\n& ROI extraction"),
    ("4. LRS3 Convert",   "Flat \u2192 LRS3\nformat"),
    ("5. Manifests",      "TSV + splits\ngeneration"),
    ("6. K-means\nCluster", "Feature\nextraction"),
    ("7. LLM Decode",     "AV-HuBERT +\nLLaMA-2"),
    ("8. Outputs",        "JSON reports\n& burned video"),
]

FLOW_LABELS = [".mp4", ".wrd", ".mp4\n(cropped)", "LRS3/", ".tsv", ".npy", "text", ".json"]

# Component spans: (label, start_stage_idx, end_stage_idx)
COMPONENTS = [
    ("auto_avsr",  2, 3),
    ("av_hubert",  4, 5),
    ("VSP-LLM",   6, 6),
]

# ── Layout ──────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 8))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 18)
ax.set_ylim(0, 8)
ax.set_aspect("equal")
ax.axis("off")

BOX_W = 3.2
BOX_H = 1.6
GAP_X = 0.6
ROW1_Y = 5.2
ROW2_Y = 1.8
START_X = 0.5

def box_center(row, col):
    """Return (cx, cy) for a stage box at given row (0=top, 1=bottom) and column (0-3)."""
    cx = START_X + col * (BOX_W + GAP_X) + BOX_W / 2
    cy = ROW1_Y + BOX_H / 2 if row == 0 else ROW2_Y + BOX_H / 2
    return cx, cy

def box_left(row, col):
    cx, cy = box_center(row, col)
    return cx - BOX_W / 2, cy

def box_right(row, col):
    cx, cy = box_center(row, col)
    return cx + BOX_W / 2, cy

def box_bottom(row, col):
    cx, cy = box_center(row, col)
    return cx, cy - BOX_H / 2

def box_top(row, col):
    cx, cy = box_center(row, col)
    return cx, cy + BOX_H / 2

# ── Draw Title ──────────────────────────────────────────────
ax.text(9, 7.65, "Argos VSP Pipeline Architecture", ha="center", va="center",
        fontsize=20, fontweight="bold", color=WHITE)
ax.text(9, 7.25, "8-Stage Visual Speech Processing Pipeline", ha="center", va="center",
        fontsize=12, color=LGRAY)

# ── Draw Boxes ──────────────────────────────────────────────
for i, (name, desc) in enumerate(STAGES):
    row = 0 if i < 4 else 1
    col = i if i < 4 else i - 4
    cx, cy = box_center(row, col)
    x0 = cx - BOX_W / 2
    y0 = cy - BOX_H / 2

    color = STAGE_COLORS[i]
    box = FancyBboxPatch((x0, y0), BOX_W, BOX_H, boxstyle="round,pad=0.18",
                         facecolor=color, edgecolor=WHITE, linewidth=2,
                         alpha=0.92, zorder=3)
    ax.add_patch(box)

    # Stage name (upper portion)
    ax.text(cx, cy + 0.2, name, ha="center", va="center",
            fontsize=12, fontweight="bold", color=WHITE, zorder=4)
    # Description (lower portion)
    ax.text(cx, cy - 0.35, desc, ha="center", va="center",
            fontsize=8.5, color=WHITE, alpha=0.85, zorder=4)

# ── Draw Arrows ─────────────────────────────────────────────
arrow_kw = dict(arrowstyle="-|>", color=ARROW_C, lw=2.2, shrinkA=4, shrinkB=4)

# Row 1: left to right (stages 0->1->2->3)
for col in range(3):
    x1, y1 = box_right(0, col)
    x2, y2 = box_left(0, col + 1)
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=arrow_kw, zorder=2)
    # Flow label
    mx = (x1 + x2) / 2
    my = y1 + 0.45
    ax.text(mx, my, FLOW_LABELS[col + 1], ha="center", va="bottom",
            fontsize=8, color=LGRAY, family="monospace",
            bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY, edgecolor="none", alpha=0.8))

# Input label on far left of row 1
x_in, y_in = box_left(0, 0)
ax.text(x_in - 0.15, y_in + 0.45, FLOW_LABELS[0], ha="right", va="bottom",
        fontsize=8, color=LGRAY, family="monospace",
        bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY, edgecolor="none", alpha=0.8))

# Connecting arrow: row 1 col 3 bottom -> row 2 col 0 top (stages 3->4)
x_top_r, _ = box_right(0, 3)
_, y_top_b = box_bottom(0, 3)
x_bot_r, _ = box_right(1, 3)
_, y_bot_t = box_top(1, 3)
# Draw a bend: go down from stage 4 (row1 col3) to stage 5 (row2 col3), then left
# Actually stage 4 is index 3 (row0 col3), stage 5 is index 4 (row1 col0)
# The flow goes: row1 col3 -> row2 col0 (wrapping around)
# Better: draw an arrow going down from row1 col3 bottom to row2 col3 top
# Then row2 goes right-to-left: col3->col2->col1->col0
# Wait, the task says 2 rows of 4, but the flow should still be logical.
# Let me place row2 left-to-right as well: stages 5-8
# and connect row1 col3 bottom -> row2 col0 top via a curved path.

# Vertical + horizontal connector from stage 4 (row1,col3) to stage 5 (row2,col0)
cx3_top, _ = box_center(0, 3)
_, cy3_bot = box_bottom(0, 3)
cx0_bot, _ = box_center(1, 0)
_, cy0_top = box_top(1, 0)

# Draw path: down from stage 4, then left to stage 5
mid_y = (cy3_bot + cy0_top) / 2
# Segment 1: vertical down from stage 4
ax.annotate("", xy=(cx3_top, mid_y), xytext=(cx3_top, cy3_bot - 0.05),
            arrowprops=dict(arrowstyle="-", color=ARROW_C, lw=2.2), zorder=2)
# Segment 2: horizontal left
ax.annotate("", xy=(cx0_bot, mid_y), xytext=(cx3_top, mid_y),
            arrowprops=dict(arrowstyle="-", color=ARROW_C, lw=2.2), zorder=2)
# Segment 3: vertical down into stage 5
ax.annotate("", xy=(cx0_bot, cy0_top + 0.05), xytext=(cx0_bot, mid_y),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.2, shrinkB=4), zorder=2)

# Flow label on the connector
ax.text((cx3_top + cx0_bot) / 2, mid_y + 0.25, FLOW_LABELS[4], ha="center", va="bottom",
        fontsize=8, color=LGRAY, family="monospace",
        bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY, edgecolor="none", alpha=0.8))

# Row 2: left to right (stages 4->5->6->7, i.e. row2 col0->1->2->3)
for col in range(3):
    x1, y1 = box_right(1, col)
    x2, y2 = box_left(1, col + 1)
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=arrow_kw, zorder=2)
    # Flow label
    mx = (x1 + x2) / 2
    my = y1 + 0.45
    ax.text(mx, my, FLOW_LABELS[col + 5], ha="center", va="bottom",
            fontsize=8, color=LGRAY, family="monospace",
            bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY, edgecolor="none", alpha=0.8))

# Output label on far right of row 2
x_out, y_out = box_right(1, 3)
ax.text(x_out + 0.15, y_out + 0.45, FLOW_LABELS[7], ha="left", va="bottom",
        fontsize=8, color=LGRAY, family="monospace",
        bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY, edgecolor="none", alpha=0.8))

# ── Component Labels (below row 2) ─────────────────────────
for label, s_start, s_end in COMPONENTS:
    # These indices are 0-based within the full 8 stages
    # Row 2 stages are indices 4-7, so col = idx - 4
    col_start = s_start - 4 if s_start >= 4 else s_start
    col_end = s_end - 4 if s_end >= 4 else s_end
    row = 1 if s_start >= 4 else 0

    x_left, _ = box_left(row, col_start)
    x_right, _ = box_right(row, col_end)
    _, y_bottom = box_bottom(row, col_start)

    bracket_y = y_bottom - 0.35
    label_y = bracket_y - 0.35

    # Draw bracket
    ax.plot([x_left + 0.3, x_left + 0.3], [bracket_y + 0.15, bracket_y],
            color=LGRAY, lw=1.5, alpha=0.7)
    ax.plot([x_left + 0.3, x_right - 0.3], [bracket_y, bracket_y],
            color=LGRAY, lw=1.5, alpha=0.7)
    ax.plot([x_right - 0.3, x_right - 0.3], [bracket_y + 0.15, bracket_y],
            color=LGRAY, lw=1.5, alpha=0.7)

    # Label
    ax.text((x_left + x_right) / 2, label_y, label, ha="center", va="top",
            fontsize=10, fontweight="bold", color=LGRAY, family="monospace")

# ── Legend ──────────────────────────────────────────────────
legend_items = [
    (TEAL,  "Preprocessing"),
    (GREEN, "Core Processing"),
    (GOLD,  "LLM Decode"),
    (CORAL, "Output"),
]
for i, (color, label) in enumerate(legend_items):
    rx = 1.0 + i * 3.8
    ry = 0.15
    box = FancyBboxPatch((rx, ry), 0.35, 0.35, boxstyle="round,pad=0.04",
                         facecolor=color, edgecolor=WHITE, linewidth=1, alpha=0.9)
    ax.add_patch(box)
    ax.text(rx + 0.5, ry + 0.175, label, va="center", fontsize=9, color=LGRAY,
            fontweight="bold")

plt.tight_layout()
fig.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Saved pipeline diagram: {OUTPUT}")
