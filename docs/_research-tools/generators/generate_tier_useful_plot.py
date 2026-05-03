#!/usr/bin/env python3
"""Round 7 — bar chart: P(useful output) per reliability tier.

Source: english_full_nbest_eval/safety_analysis/per_segment_safety.csv
Output: presentation_materials_20260224/01_plots_for_slides/confidence_tier_useful.png
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

CSV = Path("/home/ubuntu/english_full_nbest_eval/safety_analysis/per_segment_safety.csv")
OUT = Path("/home/ubuntu/presentation_materials_20260224/01_plots_for_slides/confidence_tier_useful.png")

df = pd.read_csv(CSV)
# Compute per-tier rate of useful output (NIV-Y+P, IS >= 2.0)
result = df.groupby('tier').apply(lambda g: (g['is_score'] >= 2.0).mean()).reindex(['Trust', 'Salvage', 'Strip'])
counts = df.groupby('tier').size().reindex(['Trust', 'Salvage', 'Strip'])

fig, ax = plt.subplots(figsize=(9, 4.5), facecolor='#0d1b2a')
ax.set_facecolor('#0d1b2a')
colors = ['#4caf50', '#ffd54f', '#aaaaaa']  # GREEN / GOLD / LGRAY
bars = ax.bar(result.index, result.values * 100, color=colors, edgecolor='white', linewidth=1)
for bar, val, n in zip(bars, result.values, counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, val * 100 + 2,
            f'{val*100:.0f}%\n(n={n})',
            ha='center', va='bottom', fontsize=14, color='white', fontweight='bold')
ax.set_ylabel('% useful output', color='white', fontsize=13)
ax.set_ylim(0, 105)
# In-plot title removed Round 7 — slide already has a title above the image.
ax.tick_params(colors='white', labelsize=12)
for spine in ax.spines.values():
    spine.set_color('white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=140, facecolor='#0d1b2a', bbox_inches='tight')
print(f"Saved: {OUT}")
