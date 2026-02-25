#!/usr/bin/env python3
"""
Generate a professional pipeline architecture diagram for the VSP presentation.
Shows the 8-stage flow with component labels and visual styling.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUTPUT = "/home/ubuntu/argos_research/plots/pipeline_architecture.png"

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.set_aspect("equal")
ax.axis("off")

# Color scheme
C_INPUT    = "#4a86c8"   # Blue - input
C_PREPROC  = "#6aa84f"   # Green - preprocessing
C_CORE     = "#e69138"   # Orange - core processing
C_OUTPUT   = "#cc4444"   # Red - output
C_MODEL    = "#9467bd"   # Purple - model/AI
C_ARROW    = "#555555"
C_BG       = "#f8f9fa"

fig.patch.set_facecolor("white")

def draw_stage(ax, x, y, w, h, label, sublabel, color, icon=""):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor="white", linewidth=2.5,
                         alpha=0.92, zorder=3)
    ax.add_patch(box)
    if icon:
        ax.text(x + w/2, y + h*0.65, icon, ha="center", va="center",
                fontsize=18, zorder=4)
        ax.text(x + w/2, y + h*0.32, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white", zorder=4)
    else:
        ax.text(x + w/2, y + h*0.6, label, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color="white", zorder=4)
    ax.text(x + w/2, y - 0.25, sublabel, ha="center", va="top",
            fontsize=7.5, color="#555555", style="italic", zorder=4)

def draw_arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=C_ARROW,
                                lw=2, connectionstyle="arc3,rad=0"),
                zorder=2)

# Title
ax.text(8, 8.5, "Argos VSP Pipeline Architecture", ha="center", va="center",
        fontsize=20, fontweight="bold", color="#333333")
ax.text(8, 8.05, "8-Stage Visual Speech Processing Pipeline", ha="center", va="center",
        fontsize=12, color="#777777")

# === ROW 1: Input → Normalize → ASR → LRS3 Prep ===
stages_r1 = [
    (0.5,  5.5, 2.8, 1.4, "Input Videos",     "Raw MP4/MKV files",     C_INPUT,   ""),
    (4.3,  5.5, 2.8, 1.4, "1. Normalize",      "HDR/10-bit → 8-bit\nGPU (NVENC) encoding",  C_PREPROC, ""),
    (8.1,  5.5, 2.8, 1.4, "2. Whisper ASR",     "Speech-to-text\nTranscription reuse",   C_PREPROC, ""),
    (11.9, 5.5, 2.8, 1.4, "3. LRS3 Format",     "Mouth ROI cropping\nFace alignment",    C_PREPROC, ""),
]

for x, y, w, h, label, sub, color, icon in stages_r1:
    draw_stage(ax, x, y, w, h, label, sub, color, icon)

# Arrows row 1
for i in range(len(stages_r1) - 1):
    x1 = stages_r1[i][0] + stages_r1[i][2]
    y1 = stages_r1[i][1] + stages_r1[i][3] / 2
    x2 = stages_r1[i+1][0]
    y2 = stages_r1[i+1][1] + stages_r1[i+1][3] / 2
    draw_arrow(ax, x1, y1, x2, y2)

# === Connecting arrow row 1 → row 2 ===
ax.annotate("", xy=(13.3, 4.0), xytext=(13.3, 5.5),
            arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=2),
            zorder=2)

# === ROW 2: Manifests → Clustering → Decode → Outputs (RIGHT TO LEFT) ===
stages_r2 = [
    (11.9, 2.6, 2.8, 1.4, "4. Manifests",       "TSV + splits\nSegment metadata",     C_CORE,   ""),
    (8.1,  2.6, 2.8, 1.4, "5. Clustering",       "K-means features\nCluster counts",   C_CORE,   ""),
    (4.3,  2.6, 2.8, 1.4, "6. VSP-LLM\nDecode",  "AV-HuBERT → LLaMA-2\nBeam search",  C_MODEL,  ""),
    (0.5,  2.6, 2.8, 1.4, "7. Reports\n& Videos", "HTML/CSV reports\nBurned videos",    C_OUTPUT, ""),
]

for x, y, w, h, label, sub, color, icon in stages_r2:
    draw_stage(ax, x, y, w, h, label, sub, color, icon)

# Arrows row 2 (right to left)
for i in range(len(stages_r2) - 1):
    x1 = stages_r2[i][0]
    y1 = stages_r2[i][1] + stages_r2[i][3] / 2
    x2 = stages_r2[i+1][0] + stages_r2[i+1][2]
    y2 = stages_r2[i+1][1] + stages_r2[i+1][3] / 2
    draw_arrow(ax, x1, y1, x2, y2)

# === Model components (floating labels) ===
# AV-HuBERT box
avh = FancyBboxPatch((3.8, 0.3), 3.8, 1.0, boxstyle="round,pad=0.1",
                      facecolor="#e8e0f0", edgecolor=C_MODEL, linewidth=1.5,
                      alpha=0.85, linestyle="--", zorder=1)
ax.add_patch(avh)
ax.text(5.7, 0.8, "AV-HuBERT  +  LLaMA-2  +  fairseq", ha="center", va="center",
        fontsize=9, color=C_MODEL, fontweight="bold")
ax.text(5.7, 0.45, "Visual encoder → Language model → Sequence generation",
        ha="center", va="center", fontsize=7.5, color="#777777")

# Dashed line from model box to decode stage
ax.plot([5.7, 5.7], [1.3, 2.6], color=C_MODEL, linewidth=1.2,
        linestyle=":", alpha=0.6, zorder=1)

# === Module labels (lib/ modules) ===
module_labels = [
    (5.7,  5.0, "lib/normalization.sh"),
    (9.5,  5.0, "lib/asr.sh"),
    (13.3, 5.0, "lib/lrs3_prep.sh"),
    (13.3, 2.1, "lib/manifests.sh"),
    (9.5,  2.1, "lib/clustering.sh"),
    (5.7,  2.1, "lib/decode.sh"),
    (1.9,  2.1, "lib/outputs.sh"),
]
for x, y, label in module_labels:
    ax.text(x, y, label, ha="center", va="center", fontsize=7,
            color="#999999", family="monospace", zorder=4)

# === Legend ===
legend_items = [
    (C_INPUT,   "Input"),
    (C_PREPROC, "Preprocessing"),
    (C_CORE,    "Core Processing"),
    (C_MODEL,   "AI Model (Decode)"),
    (C_OUTPUT,  "Output"),
]
for i, (color, label) in enumerate(legend_items):
    rx = 0.5 + i * 2.8
    ry = 0.05
    rect = FancyBboxPatch((rx, ry), 0.3, 0.3, boxstyle="round,pad=0.02",
                           facecolor=color, edgecolor="white", linewidth=1, alpha=0.9)
    ax.add_patch(rect)
    ax.text(rx + 0.45, ry + 0.15, label, va="center", fontsize=8, color="#555555")

plt.tight_layout()
fig.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved pipeline diagram: {OUTPUT}")
