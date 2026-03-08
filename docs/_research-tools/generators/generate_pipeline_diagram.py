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
# Row 1 main flow: slots 0, 1, (2=empty for ASR side-branch), 3
ROW1_MAIN = [
    (0, "1. Normalize",    "HDR/10-bit\nconversion",       TEAL),
    (1, "2. Mouth Crop",   "Face detection\n& ROI extract", TEAL),
    (3, "4. LRS3 Convert", "Flat \u2192 LRS3\nformat",     TEAL),
]
# ASR is a side-branch (evaluation only), positioned at slot 2 but below row 1
ASR_STAGE = ("3. ASR", "Whisper\ntranscription", TEAL)

ROW2 = [
    (0, "5. Manifests",    "TSV + splits\ngeneration", GREEN),
    (1, "6. K-means",      "Feature\nextraction",      GREEN),
    (2, "7. LLM Decode",   "AV-HuBERT +\nLLaMA-2",    GOLD),
    (3, "8. Outputs",      "Reports &\nburned video",   CORAL),
]

# ── Layout constants ─────────────────────────────────────
FIG_W, FIG_H = 16, 10.5
BOX_W = 2.8
BOX_H = 1.4
GAP_X = 0.65       # horizontal gap between boxes
ROW1_Y = 7.6       # bottom-left y of row 1 boxes
ROW2_Y = 1.8       # bottom-left y of row 2 boxes

# Compute start x to center both rows
TOTAL_ROW_W = 4 * BOX_W + 3 * GAP_X
START_X = (FIG_W - TOTAL_ROW_W) / 2

CORAL_LINE = "#E06C75"

def slot_x(col):
    return START_X + col * (BOX_W + GAP_X)


# ── Create figure ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect("equal")
ax.axis("off")


def draw_box(x, y, w, h, color, name, desc):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor=WHITE, linewidth=1.8,
                         alpha=0.90, zorder=3)
    ax.add_patch(box)
    cx, cy = x + w / 2, y + h / 2
    ax.text(cx, cy + 0.22, name, ha="center", va="center",
            fontsize=12, fontweight="bold", color=WHITE, zorder=4)
    ax.text(cx, cy - 0.30, desc, ha="center", va="center",
            fontsize=8.5, color=WHITE, alpha=0.85, zorder=4)


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


# ── Draw Row 1 main-flow boxes ───────────────────────────
for col, name, desc, color in ROW1_MAIN:
    draw_box(slot_x(col), ROW1_Y, BOX_W, BOX_H, color, name, desc)

# Arrows: Normalize → Mouth Crop (slot 0→1)
fr = (slot_x(0) + BOX_W, ROW1_Y + BOX_H / 2)
to = (slot_x(1), ROW1_Y + BOX_H / 2)
draw_arrow(fr, to)

# Long arrow: Mouth Crop → LRS3 Convert (slot 1→3, spanning empty slot 2)
fr_long = (slot_x(1) + BOX_W, ROW1_Y + BOX_H / 2)
to_long = (slot_x(3), ROW1_Y + BOX_H / 2)
draw_arrow(fr_long, to_long)
# Flow label on long arrow
draw_flow_label((fr_long[0] + to_long[0]) / 2, ROW1_Y + BOX_H + 0.30, ".mp4 (crop)")

# Input label before stage 0
ix = slot_x(0)
iy = ROW1_Y + BOX_H / 2
ax.annotate("", xy=(ix - 0.05, iy), xytext=(ix - 1.0, iy),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkB=6, mutation_scale=18), zorder=2)
draw_flow_label(ix - 1.4, iy + 0.45, ".mp4")
ax.text(ix - 1.4, iy - 0.05, "Video\nInput", ha="center", va="top",
        fontsize=9, fontweight="bold", color=WHITE, zorder=4)

# ── ASR side-branch ──────────────────────────────────────
# ASR box centered below slot 2
asr_x = slot_x(2)
asr_y = ROW1_Y - BOX_H - 1.2  # well below row 1 with clearance
draw_box(asr_x, asr_y, BOX_W, BOX_H, TEAL, ASR_STAGE[0], ASR_STAGE[1])

# Branch connector: vertical drop from main flow line down to ASR
branch_cx = asr_x + BOX_W / 2
main_flow_y = ROW1_Y + BOX_H / 2
ax.plot([branch_cx, branch_cx], [main_flow_y, asr_y + BOX_H + 0.08],
        color=CORAL_LINE, lw=2.5, solid_capstyle="round", zorder=2)
# Arrowhead down into ASR
ax.annotate("", xy=(branch_cx, asr_y + BOX_H + 0.08),
            xytext=(branch_cx, asr_y + BOX_H + 0.5),
            arrowprops=dict(arrowstyle="-|>", color=CORAL_LINE, lw=2.5,
                            shrinkA=0, shrinkB=6, mutation_scale=18),
            zorder=2)

# "evaluation only" annotation below ASR box
ax.text(branch_cx, asr_y - 0.20, "evaluation only",
        ha="center", va="top", fontsize=9, fontstyle="italic",
        fontweight="bold", color=CORAL_LINE, zorder=4)

# Flow label on branch (to the right of the vertical drop)
draw_flow_label(branch_cx + 1.0, main_flow_y - 0.7, ".wrd")

# Coral L-connector from ASR right side to Outputs (row 2, slot 3)
outputs_cx = slot_x(3) + BOX_W / 2
asr_right_x = asr_x + BOX_W
asr_cy = asr_y + BOX_H / 2
# Horizontal from ASR right to Outputs column
ax.plot([asr_right_x + 0.08, outputs_cx], [asr_cy, asr_cy],
        color=CORAL_LINE, lw=2.5, solid_capstyle="round", zorder=2)
# Vertical down from elbow into Outputs top
ax.plot([outputs_cx, outputs_cx], [asr_cy, ROW2_Y + BOX_H + 0.3],
        color=CORAL_LINE, lw=2.5, solid_capstyle="round", zorder=2)
ax.annotate("", xy=(outputs_cx, ROW2_Y + BOX_H + 0.08),
            xytext=(outputs_cx, ROW2_Y + BOX_H + 0.5),
            arrowprops=dict(arrowstyle="-|>", color=CORAL_LINE, lw=2.5,
                            shrinkA=0, shrinkB=6, mutation_scale=18),
            zorder=2)
# Flow label on coral horizontal
draw_flow_label((asr_right_x + outputs_cx) / 2, asr_cy + 0.35, ".wrd (ref)")

# ── Connector: LRS3 Convert (row1 slot 3) → Manifests (row2 slot 0) ──
# Route LEFT of ASR box to avoid crossing it
r3_cx = slot_x(3) + BOX_W / 2
s4_cx = slot_x(0) + BOX_W / 2
r3_bottom_y = ROW1_Y
s4_top_y = ROW2_Y + BOX_H
# Route via left side: down from LRS3, left past ASR, then down to Manifests
elbow_left_x = slot_x(2) - 0.4  # left of ASR box
elbow_top_y = r3_bottom_y - 0.3
elbow_bot_y = s4_top_y + 0.5

# Vertical from LRS3 bottom down to first elbow
ax.plot([r3_cx, r3_cx], [r3_bottom_y - 0.08, elbow_top_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Horizontal left to elbow_left_x
ax.plot([r3_cx, elbow_left_x], [elbow_top_y, elbow_top_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Vertical down past ASR
ax.plot([elbow_left_x, elbow_left_x], [elbow_top_y, elbow_bot_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Horizontal left to Manifests column
ax.plot([elbow_left_x, s4_cx], [elbow_bot_y, elbow_bot_y],
        color=ARROW_C, lw=2.5, solid_capstyle="round", zorder=2)
# Arrow down into Manifests
ax.annotate("", xy=(s4_cx, s4_top_y + 0.08),
            xytext=(s4_cx, elbow_bot_y),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkA=0, shrinkB=6, mutation_scale=18),
            zorder=2)
draw_flow_label(elbow_left_x - 0.6, (elbow_top_y + elbow_bot_y) / 2, "LRS3/")

# ── Row 2: stages 5→6→7→8 ───────────────────────────────
for col, name, desc, color in ROW2:
    draw_box(slot_x(col), ROW2_Y, BOX_W, BOX_H, color, name, desc)

# Row 2 arrows
for i in range(3):
    fr = (slot_x(i) + BOX_W, ROW2_Y + BOX_H / 2)
    to = (slot_x(i + 1), ROW2_Y + BOX_H / 2)
    draw_arrow(fr, to)
    mx = (fr[0] + to[0]) / 2
    my = ROW2_Y + BOX_H + 0.30
    labels_r2 = [".tsv", ".npy", "text"]
    draw_flow_label(mx, my, labels_r2[i])

# Output label after stage 8
ox = slot_x(3) + BOX_W
oy = ROW2_Y + BOX_H / 2
ax.annotate("", xy=(ox + 1.0, oy), xytext=(ox + 0.05, oy),
            arrowprops=dict(arrowstyle="-|>", color=ARROW_C, lw=2.5,
                            shrinkA=6, mutation_scale=18), zorder=2)
draw_flow_label(ox + 1.4, oy + 0.45, ".json")
ax.text(ox + 1.4, oy - 0.05, "Reports\n& Videos", ha="center", va="top",
        fontsize=9, fontweight="bold", color=WHITE, zorder=4)

# ── Component brackets ───────────────────────────────────
# auto_avsr bracket ABOVE row 1 (Mouth Crop + LRS3 Convert: slots 1, 3)
bx_l = slot_x(1) + 0.2
bx_r = slot_x(3) + BOX_W - 0.2
bracket_y = ROW1_Y + BOX_H + 0.55
ax.plot([bx_l, bx_l], [bracket_y - 0.15, bracket_y], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_l, bx_r], [bracket_y, bracket_y], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_r, bx_r], [bracket_y - 0.15, bracket_y], color=LGRAY, lw=1.2, alpha=0.6)
ax.text((bx_l + bx_r) / 2, bracket_y + 0.12, "auto_avsr", ha="center", va="bottom",
        fontsize=9.5, fontweight="bold", color=LGRAY, family="monospace")

# av_hubert bracket below row 2 (Manifests + K-means: slots 0-1)
bx_l2 = slot_x(0) + 0.2
bx_r2 = slot_x(1) + BOX_W - 0.2
bracket_y2 = ROW2_Y - 0.45
ax.plot([bx_l2, bx_l2], [bracket_y2 + 0.15, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_l2, bx_r2], [bracket_y2, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_r2, bx_r2], [bracket_y2 + 0.15, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.text((bx_l2 + bx_r2) / 2, bracket_y2 - 0.35, "av_hubert", ha="center", va="top",
        fontsize=9.5, fontweight="bold", color=LGRAY, family="monospace")

# VSP-LLM bracket below row 2 (LLM Decode: slot 2)
bx_l3 = slot_x(2) + 0.2
bx_r3 = slot_x(2) + BOX_W - 0.2
ax.plot([bx_l3, bx_l3], [bracket_y2 + 0.15, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_l3, bx_r3], [bracket_y2, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.plot([bx_r3, bx_r3], [bracket_y2 + 0.15, bracket_y2], color=LGRAY, lw=1.2, alpha=0.6)
ax.text((bx_l3 + bx_r3) / 2, bracket_y2 - 0.35, "VSP-LLM", ha="center", va="top",
        fontsize=9.5, fontweight="bold", color=LGRAY, family="monospace")

# ── Legend ────────────────────────────────────────────────
legend_items = [
    (TEAL,  "Preprocessing"),
    (GREEN, "Feature Processing"),
    (GOLD,  "LLM Inference"),
    (CORAL, "Output Generation"),
]
legend_y = 0.25
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
