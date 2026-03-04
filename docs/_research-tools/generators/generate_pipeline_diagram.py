#!/usr/bin/env python3
"""
Generate a professional pipeline architecture diagram for the VSP presentation.
8 stages flow left-to-right in 2 rows: row 1 (stages 1-4), then wraps to
row 2 (stages 5-8) via a connecting elbow.

Usage:
    python3 generate_pipeline_diagram.py

Output:
    docs/evaluation/plots/pipeline_architecture.png
    presentation_materials_20260224/01_plots_for_slides/pipeline_architecture.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUTPUT1 = "/home/ubuntu/docs/evaluation/plots/pipeline_architecture.png"
OUTPUT2 = "/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/pipeline_architecture.png"

# ── Color Palette (matches presentation theme) ───────────
BG      = "#0D1B2A"
TEAL    = "#00B4D8"
CORAL   = "#E06C75"
GREEN   = "#56B870"
GOLD    = "#FFD966"
WHITE   = "#FFFFFF"
LGRAY   = "#8899AA"
DGRAY   = "#1B2D44"
ARROW_C = "#6BAED6"

# ── Stage definitions ────────────────────────────────────
STAGES = [
    ("1. Normalize",    "HDR/10-bit\nconversion",        TEAL),
    ("2. ASR",          "Whisper\ntranscription",         TEAL),
    ("3. Mouth Crop",   "Face detection\n& ROI extract",  TEAL),
    ("4. LRS3 Convert", "Flat \u2192 LRS3\nformat",      TEAL),
    ("5. Manifests",    "TSV + splits\ngeneration",       GREEN),
    ("6. K-means",      "Feature\nextraction",            GREEN),
    ("7. LLM Decode",   "AV-HuBERT +\nLLaMA-2",         GOLD),
    ("8. Outputs",      "Reports &\nburned video",        CORAL),
]

# Data flow labels on arrows between stages
FLOW_LABELS = [".mp4", ".wrd", ".mp4 (crop)", "LRS3/", ".tsv", ".npy", "text", ".json"]

# ── Layout constants ─────────────────────────────────────
FIG_W, FIG_H = 16, 7.5
BOX_W = 2.8
BOX_H = 1.4
GAP_X = 0.65       # horizontal gap between boxes
ROW1_Y = 4.8       # top-left y of row 1 boxes
ROW2_Y = 1.4       # top-left y of row 2 boxes
MARGIN_L = 1.2     # left margin for input label

# Compute start x to center both rows
TOTAL_ROW_W = 4 * BOX_W + 3 * GAP_X  # = 13.15
START_X = (FIG_W - TOTAL_ROW_W) / 2


def get_box_rect(stage_idx):
    """Return (x, y, w, h) for a stage box."""
    row = 0 if stage_idx < 4 else 1
    col = stage_idx % 4
    x = START_X + col * (BOX_W + GAP_X)
    y = ROW1_Y if row == 0 else ROW2_Y
    return x, y, BOX_W, BOX_H


def get_box_center(stage_idx):
    x, y, w, h = get_box_rect(stage_idx)
    return x + w / 2, y + h / 2


def get_box_edge(stage_idx, side):
    """Get midpoint of a box edge. side: 'left','right','top','bottom'."""
    x, y, w, h = get_box_rect(stage_idx)
    cx, cy = x + w / 2, y + h / 2
    if side == "left":
        return x, cy
    elif side == "right":
        return x + w, cy
    elif side == "top":
        return cx, y + h
    elif side == "bottom":
        return cx, y


# ── Create figure ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect("equal")
ax.axis("off")

# ── Draw stage boxes ─────────────────────────────────────
for i, (name, desc, color) in enumerate(STAGES):
    x, y, w, h = get_box_rect(i)

    # Box
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor=WHITE, linewidth=1.8,
                         alpha=0.90, zorder=3)
    ax.add_patch(box)

    cx, cy = x + w / 2, y + h / 2

    # Stage name
    ax.text(cx, cy + 0.22, name, ha="center", va="center",
            fontsize=12, fontweight="bold", color=WHITE, zorder=4)
    # Description
    ax.text(cx, cy - 0.30, desc, ha="center", va="center",
            fontsize=8.5, color=WHITE, alpha=0.85, zorder=4)


# ── Draw arrows ──────────────────────────────────────────
arrow_kw = dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                shrinkA=8, shrinkB=8, mutation_scale=18)


def draw_arrow(from_xy, to_xy, **kw):
    merged = {**arrow_kw, **kw}
    ax.annotate("", xy=to_xy, xytext=from_xy, arrowprops=merged, zorder=2)


def draw_flow_label(x, y, text):
    ax.text(x, y, text, ha="center", va="center",
            fontsize=7.5, color=LGRAY, family="monospace",
            bbox=dict(boxstyle="round,pad=0.15", facecolor=DGRAY,
                      edgecolor="none", alpha=0.85),
            zorder=5)


# Row 1: stages 0→1→2→3
for col in range(3):
    fr = get_box_edge(col, "right")
    to = get_box_edge(col + 1, "left")
    draw_arrow(fr, to)
    # Flow label above arrow
    mx = (fr[0] + to[0]) / 2
    my = fr[1] + 0.55
    draw_flow_label(mx, my, FLOW_LABELS[col + 1])

# Input label before stage 0
ix, iy = get_box_edge(0, "left")
ax.annotate("", xy=(ix - 0.05, iy), xytext=(ix - 0.8, iy),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkB=6, mutation_scale=18), zorder=2)
draw_flow_label(ix - 1.15, iy + 0.55, FLOW_LABELS[0])
ax.text(ix - 1.15, iy, "Video\nInput", ha="center", va="center",
        fontsize=9, fontweight="bold", color=WHITE, zorder=4)

# Connector: stage 3 (row1 col3) → stage 4 (row2 col0)
# Elbow: right edge of stage 3 → down → left → top of stage 4
r3_bottom = get_box_edge(3, "bottom")
s4_top = get_box_edge(4, "top")

# Three-segment elbow path using plot lines + one arrow at the end
elbow_right_x = r3_bottom[0] + 0.8   # go slightly right of stage 4
mid_y = (r3_bottom[1] + s4_top[1]) / 2

# Vertical segment from bottom of stage 3
ax.plot([r3_bottom[0], r3_bottom[0]], [r3_bottom[1] - 0.08, mid_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Horizontal segment across to above stage 4
ax.plot([r3_bottom[0], s4_top[0]], [mid_y, mid_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Arrow down into stage 4
ax.annotate("", xy=(s4_top[0], s4_top[1] + 0.08),
            xytext=(s4_top[0], mid_y),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkA=0, shrinkB=6, mutation_scale=18),
            zorder=2)
# Flow label on connector
draw_flow_label((r3_bottom[0] + s4_top[0]) / 2, mid_y + 0.3, FLOW_LABELS[4])

# Row 2: stages 4→5→6→7
for col in range(3):
    fr = get_box_edge(4 + col, "right")
    to = get_box_edge(4 + col + 1, "left")
    draw_arrow(fr, to)
    mx = (fr[0] + to[0]) / 2
    my = fr[1] + 0.55
    draw_flow_label(mx, my, FLOW_LABELS[col + 5])

# Output label after stage 7
ox, oy = get_box_edge(7, "right")
ax.annotate("", xy=(ox + 0.8, oy), xytext=(ox + 0.05, oy),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkA=6, mutation_scale=18), zorder=2)
draw_flow_label(ox + 1.15, oy + 0.55, FLOW_LABELS[7])
ax.text(ox + 1.15, oy, "Reports\n& Videos", ha="center", va="center",
        fontsize=9, fontweight="bold", color=WHITE, zorder=4)

# ── Component brackets (below row 2) ────────────────────
COMPONENTS = [
    ("auto_avsr",  2, 3),   # stages 3-4 (Mouth Crop + LRS3 Convert)
    ("av_hubert",  4, 5),   # stages 5-6 (Manifests + K-means)
    ("VSP-LLM",   6, 6),   # stage 7 (LLM Decode)
]

for label, s_start, s_end in COMPONENTS:
    x_left, y_left, _, _ = get_box_rect(s_start)
    x_right, _, w_right, _ = get_box_rect(s_end)
    x_right_edge = x_right + w_right

    row = 0 if s_start < 4 else 1
    _, box_y, _, _ = get_box_rect(s_start)
    bracket_y = box_y - 0.3
    label_y = bracket_y - 0.35

    # Draw U-bracket
    bx_l = x_left + 0.2
    bx_r = x_right_edge - 0.2
    ax.plot([bx_l, bx_l], [bracket_y + 0.15, bracket_y],
            color=LGRAY, lw=1.2, alpha=0.6)
    ax.plot([bx_l, bx_r], [bracket_y, bracket_y],
            color=LGRAY, lw=1.2, alpha=0.6)
    ax.plot([bx_r, bx_r], [bracket_y + 0.15, bracket_y],
            color=LGRAY, lw=1.2, alpha=0.6)

    ax.text((bx_l + bx_r) / 2, label_y, label, ha="center", va="top",
            fontsize=9.5, fontweight="bold", color=LGRAY, family="monospace")

# ── Legend ────────────────────────────────────────────────
legend_items = [
    (TEAL,  "Preprocessing"),
    (GREEN, "Feature Processing"),
    (GOLD,  "LLM Inference"),
    (CORAL, "Output Generation"),
]
legend_y = 0.2
legend_start_x = (FIG_W - len(legend_items) * 3.5) / 2
for i, (color, label) in enumerate(legend_items):
    rx = legend_start_x + i * 3.5
    box = FancyBboxPatch((rx, legend_y), 0.3, 0.3, boxstyle="round,pad=0.04",
                         facecolor=color, edgecolor=WHITE, linewidth=1, alpha=0.9)
    ax.add_patch(box)
    ax.text(rx + 0.45, legend_y + 0.15, label, va="center", fontsize=8.5,
            color=LGRAY, fontweight="bold")

# ── Save ─────────────────────────────────────────────────
plt.tight_layout(pad=0.3)
for out in [OUTPUT1, OUTPUT2]:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=BG)
    print(f"Saved pipeline diagram: {out}")
plt.close(fig)
