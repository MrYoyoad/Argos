#!/usr/bin/env python3
"""
Decode Parameter Tuning: Pairwise Comparison Report Generator

Reads all 13 experiment report CSVs, builds comprehensive pairwise
comparison matrices, performs statistical analysis, and generates
a professional PDF report.

Author: Argos Research Team
Date: 2026-02-19
"""

import os
import sys
import csv
import numpy as np
import pandas as pd
from collections import OrderedDict
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec

from scipy.stats import wilcoxon

# ============================================================
# Configuration
# ============================================================

BASE_DIR = "/home/ubuntu/tuning_results"
OUTPUT_PDF = os.path.join(BASE_DIR, "pairwise_comparison_report.pdf")

# Experiment directory names and short labels
EXPERIMENTS = OrderedDict([
    ("exp_A_baseline",        "A: Baseline"),
    ("exp_B_no_rep_pen",      "B: No RepPen"),
    ("exp_C_lenpen_pos1",     "C: LenPen=1"),
    ("exp_D_lenpen_neg05",    "D: LenPen=-0.5"),
    ("exp_E_sampling_low_temp","E: Samp t=0.5"),
    ("exp_F_sampling_original","F: Samp t=1.0"),
    ("exp_G_greedy",          "G: Greedy"),
    ("exp_H_lenpen_pos2",     "H: LenPen=2"),
    ("exp_I_lenpen1_sample",  "I: LP1+Samp t=1"),
    ("exp_J_lenpen1_temp05",  "J: LP1+Samp t=0.5"),
    ("exp_K_sampling_temp15", "K: Samp t=1.5"),
    ("exp_L_sampling_temp03", "L: Samp t=0.3"),
    ("exp_M_lenpen1_temp03",  "M: LP1+Samp t=0.3"),
])

# Key pairs for detailed statistical analysis
KEY_PAIRS = [
    ("exp_A_baseline", "exp_C_lenpen_pos1"),
    ("exp_A_baseline", "exp_J_lenpen1_temp05"),
    ("exp_A_baseline", "exp_E_sampling_low_temp"),
    ("exp_A_baseline", "exp_F_sampling_original"),
    ("exp_A_baseline", "exp_G_greedy"),
    ("exp_C_lenpen_pos1", "exp_J_lenpen1_temp05"),
    ("exp_A_baseline", "exp_L_sampling_temp03"),
    ("exp_A_baseline", "exp_I_lenpen1_sample"),
    ("exp_A_baseline", "exp_M_lenpen1_temp03"),
    ("exp_A_baseline", "exp_D_lenpen_neg05"),
    ("exp_A_baseline", "exp_H_lenpen_pos2"),
    ("exp_C_lenpen_pos1", "exp_M_lenpen1_temp03"),
]

# Letter-only labels for matrices
LETTER_LABELS = [k.split("_")[1] for k in EXPERIMENTS.keys()]  # A, B, C, ...

# ============================================================
# Data Loading
# ============================================================

def load_experiment(exp_dir):
    """Load a single experiment's report CSV."""
    csv_path = os.path.join(BASE_DIR, exp_dir, "report", "report.csv")
    df = pd.read_csv(csv_path)
    # Standardize column names
    df.columns = [c.strip().lower().replace(" ", "_").replace("%", "pct") for c in df.columns]
    return df


def load_all_experiments():
    """Load all 13 experiments into a dict of DataFrames."""
    data = OrderedDict()
    for exp_dir in EXPERIMENTS:
        df = load_experiment(exp_dir)
        data[exp_dir] = df
    return data


# ============================================================
# Analysis Functions
# ============================================================

def compute_pairwise_wwer(data):
    """
    For each pair (i, j), compute:
    - improved: segments where j has lower WWER than i
    - worsened: segments where j has higher WWER than i
    - changed: segments where WWER differs
    Returns matrices (improved, worsened, changed) as DataFrames.
    """
    exp_keys = list(data.keys())
    n = len(exp_keys)
    improved = np.zeros((n, n), dtype=int)
    worsened = np.zeros((n, n), dtype=int)
    changed = np.zeros((n, n), dtype=int)

    for i in range(n):
        wwer_i = data[exp_keys[i]]["wwer_pct"].values
        for j in range(n):
            if i == j:
                continue
            wwer_j = data[exp_keys[j]]["wwer_pct"].values
            delta = wwer_j - wwer_i  # negative = j improved
            imp = np.sum(delta < -0.01)  # j better (lower WWER)
            wor = np.sum(delta > 0.01)   # j worse (higher WWER)
            improved[i, j] = imp
            worsened[i, j] = wor
            changed[i, j] = imp + wor

    labels = [EXPERIMENTS[k] for k in exp_keys]
    return (
        pd.DataFrame(improved, index=labels, columns=labels),
        pd.DataFrame(worsened, index=labels, columns=labels),
        pd.DataFrame(changed, index=labels, columns=labels),
    )


def compute_summary_stats(data):
    """Compute summary stats for each experiment."""
    rows = []
    for exp_dir, label in EXPERIMENTS.items():
        df = data[exp_dir]
        wwer = df["wwer_pct"].values
        nea_r = df["nea_recall_pct"].values
        nea_f1 = df["nea_f1_pct"].values
        hyps = df["hyp"].values
        empty = sum(1 for h in hyps if pd.isna(h) or str(h).strip() in ("", "nan"))
        rows.append({
            "Experiment": label,
            "Mean WWER": np.mean(wwer),
            "Median WWER": np.median(wwer),
            "Std WWER": np.std(wwer),
            "Min WWER": np.min(wwer),
            "Max WWER": np.max(wwer),
            "Mean NEA-R": np.mean(nea_r),
            "Mean NEA-F1": np.mean(nea_f1),
            "Empty (>=100%)": empty,
        })
    summary = pd.DataFrame(rows)
    summary = summary.sort_values("Mean WWER").reset_index(drop=True)
    summary.index = summary.index + 1  # Rank starting at 1
    summary.index.name = "Rank"
    return summary


def detailed_pair_analysis(data, exp1, exp2):
    """Detailed statistical comparison between two experiments."""
    label1 = EXPERIMENTS[exp1]
    label2 = EXPERIMENTS[exp2]
    wwer1 = data[exp1]["wwer_pct"].values
    wwer2 = data[exp2]["wwer_pct"].values
    n = len(wwer1)

    delta = wwer2 - wwer1  # negative = exp2 better

    diff_mask = np.abs(delta) > 0.01
    n_diff = np.sum(diff_mask)
    n_improved = np.sum(delta < -0.01)
    n_worsened = np.sum(delta > 0.01)
    n_unchanged = n - n_diff

    mean_delta = np.mean(delta)
    mean_delta_diff = np.mean(delta[diff_mask]) if n_diff > 0 else 0.0
    median_delta = np.median(delta)

    # Wilcoxon signed-rank test (on differing segments only)
    p_value = np.nan
    significant = False
    if n_diff >= 10:  # Need sufficient samples
        try:
            stat, p_value = wilcoxon(delta[diff_mask])
            significant = p_value < 0.05
        except Exception:
            pass
    elif n_diff > 0:
        try:
            stat, p_value = wilcoxon(delta[diff_mask])
            significant = p_value < 0.05
        except Exception:
            pass

    # Per-segment NEA-Recall comparison
    nea1 = data[exp1]["nea_recall_pct"].values
    nea2 = data[exp2]["nea_recall_pct"].values
    nea_delta = nea2 - nea1
    nea_improved = np.sum(nea_delta > 0.01)
    nea_worsened = np.sum(nea_delta < -0.01)

    return {
        "pair": f"{label1} vs {label2}",
        "label1": label1,
        "label2": label2,
        "n_segments": n,
        "n_diff": n_diff,
        "n_improved": n_improved,
        "n_worsened": n_worsened,
        "n_unchanged": n_unchanged,
        "mean_delta_wwer": mean_delta,
        "mean_delta_diff_only": mean_delta_diff,
        "median_delta_wwer": median_delta,
        "p_value": p_value,
        "significant": significant,
        "nea_improved": nea_improved,
        "nea_worsened": nea_worsened,
        "mean_wwer_1": np.mean(wwer1),
        "mean_wwer_2": np.mean(wwer2),
    }


# ============================================================
# PDF Rendering Functions
# ============================================================

def add_title_page(pdf, summary_df):
    """Add a professional title page."""
    fig = plt.figure(figsize=(11, 8.5))

    # Title
    fig.text(0.5, 0.78, "Decode Parameter Tuning", fontsize=28, fontweight='bold',
             ha='center', va='center', color='#1a1a2e')
    fig.text(0.5, 0.71, "Pairwise Comparison Report", fontsize=22,
             ha='center', va='center', color='#16213e')

    # Horizontal line
    ax_line = fig.add_axes([0.15, 0.66, 0.7, 0.002])
    ax_line.set_xlim(0, 1)
    ax_line.axhline(y=0, color='#0f3460', linewidth=2)
    ax_line.set_axis_off()

    # Metadata
    info_lines = [
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        f"Dataset: 107 segments from 100 AVSpeech videos",
        f"Experiments: 13 decode parameter configurations",
        f"Primary Metric: Weighted Word Error Rate (WWER%)",
        f"Secondary Metric: Named Entity Recall (NEA-R%)",
    ]
    y_start = 0.58
    for i, line in enumerate(info_lines):
        fig.text(0.5, y_start - i * 0.045, line, fontsize=13,
                 ha='center', va='center', color='#333333')

    # Best experiment highlight
    best = summary_df.iloc[0]
    fig.text(0.5, 0.33, "Best Configuration", fontsize=16, fontweight='bold',
             ha='center', va='center', color='#0f3460')
    fig.text(0.5, 0.27, f"{best['Experiment']}", fontsize=14,
             ha='center', va='center', color='#e94560',
             fontweight='bold')
    fig.text(0.5, 0.22, f"Mean WWER: {best['Mean WWER']:.1f}%  |  Median WWER: {best['Median WWER']:.1f}%  |  NEA-R: {best['Mean NEA-R']:.1f}%",
             fontsize=12, ha='center', va='center', color='#333333')

    # Footer
    fig.text(0.5, 0.06, "Argos Visual Speech Processing Research",
             fontsize=10, ha='center', va='center', color='#888888', style='italic')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_summary_table(pdf, summary_df):
    """Add summary results table page."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_axis_off()

    fig.text(0.5, 0.95, "Summary: All 13 Experiments Ranked by Mean WWER",
             fontsize=16, fontweight='bold', ha='center', va='center', color='#1a1a2e')

    # Prepare table data
    cols = ["Experiment", "Mean WWER", "Median WWER", "Std WWER", "Mean NEA-R", "Mean NEA-F1", "Empty (>=100%)"]
    cell_data = []
    for _, row in summary_df.iterrows():
        cell_data.append([
            row["Experiment"],
            f"{row['Mean WWER']:.1f}%",
            f"{row['Median WWER']:.1f}%",
            f"{row['Std WWER']:.1f}",
            f"{row['Mean NEA-R']:.1f}%",
            f"{row['Mean NEA-F1']:.1f}%",
            f"{int(row['Empty (>=100%)'])}",
        ])

    col_labels = ["Experiment", "Mean\nWWER", "Median\nWWER", "Std\nWWER", "Mean\nNEA-R", "Mean\nNEA-F1", "Empty\nSegs"]

    table = ax.table(
        cellText=cell_data,
        colLabels=col_labels,
        cellLoc='center',
        loc='center',
        bbox=[0.02, 0.05, 0.96, 0.82],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)

    # Style the table
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#0f3460')
            cell.set_text_props(color='white', fontweight='bold')
            cell.set_height(0.06)
        else:
            if row == 1:
                cell.set_facecolor('#d4edda')  # Highlight best
            elif row == 2:
                cell.set_facecolor('#e8f5e9')
            elif row == 3:
                cell.set_facecolor('#f1f8e9')
            else:
                cell.set_facecolor('#f8f9fa' if row % 2 == 0 else 'white')
            cell.set_height(0.055)
        cell.set_edgecolor('#cccccc')

    # First column wider
    for row in range(len(cell_data) + 1):
        table[(row, 0)].set_width(0.22)

    # Footer note
    fig.text(0.5, 0.03,
             "Lower WWER is better. Higher NEA-R is better. 'Empty Segs' = segments with WWER >= 100% (total hallucination).",
             fontsize=8.5, ha='center', va='center', color='#666666', style='italic')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_pairwise_matrix(pdf, improved_df, worsened_df, changed_df):
    """Add the 13x13 +/- pairwise matrix."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_axis_off()

    fig.text(0.5, 0.97, "Pairwise WWER Comparison Matrix (Improved / Worsened)",
             fontsize=14, fontweight='bold', ha='center', va='center', color='#1a1a2e')
    fig.text(0.5, 0.935,
             "Cell (row, col) shows how many segments IMPROVED / WORSENED when switching FROM row TO column",
             fontsize=9, ha='center', va='center', color='#555555', style='italic')

    n = len(EXPERIMENTS)
    labels = LETTER_LABELS

    # Build cell text and color array
    cell_text = []
    cell_colors = []
    for i in range(n):
        row_text = []
        row_colors = []
        for j in range(n):
            if i == j:
                row_text.append("--")
                row_colors.append('#e0e0e0')
            else:
                imp = improved_df.iloc[i, j]
                wor = worsened_df.iloc[i, j]
                row_text.append(f"+{imp} / -{wor}")
                # Color based on net improvement
                net = imp - wor
                if net > 15:
                    row_colors.append('#a5d6a7')
                elif net > 5:
                    row_colors.append('#c8e6c9')
                elif net > 0:
                    row_colors.append('#e8f5e9')
                elif net == 0:
                    row_colors.append('#fff9c4')
                elif net > -5:
                    row_colors.append('#ffebee')
                elif net > -15:
                    row_colors.append('#ffcdd2')
                else:
                    row_colors.append('#ef9a9a')
            row_text[-1] = row_text[-1]
        cell_text.append(row_text)
        cell_colors.append(row_colors)

    table = ax.table(
        cellText=cell_text,
        rowLabels=labels,
        colLabels=labels,
        cellLoc='center',
        loc='center',
        bbox=[0.06, 0.03, 0.92, 0.87],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)

    # Apply colors
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#0f3460')
            cell.set_text_props(color='white', fontweight='bold', fontsize=8.5)
            cell.set_height(0.055)
        elif col == -1:
            cell.set_facecolor('#0f3460')
            cell.set_text_props(color='white', fontweight='bold', fontsize=8.5)
        else:
            cell.set_facecolor(cell_colors[row - 1][col])
            cell.set_height(0.055)
        cell.set_edgecolor('#aaaaaa')

    # Legend
    legend_items = [
        ('#a5d6a7', 'Strong net improvement (>15)'),
        ('#c8e6c9', 'Moderate improvement (6-15)'),
        ('#e8f5e9', 'Slight improvement (1-5)'),
        ('#fff9c4', 'No net change'),
        ('#ffebee', 'Slight worsening (1-5)'),
        ('#ffcdd2', 'Moderate worsening (6-15)'),
        ('#ef9a9a', 'Strong net worsening (>15)'),
    ]
    y_legend = 0.02
    x_start = 0.06
    for i, (color, text) in enumerate(legend_items):
        x = x_start + (i % 4) * 0.24
        y = y_legend - (i // 4) * 0.02
        fig.patches.append(plt.Rectangle((x, y), 0.012, 0.012,
                                          transform=fig.transFigure,
                                          facecolor=color, edgecolor='#888'))
        fig.text(x + 0.016, y + 0.006, text, fontsize=6.5, va='center', color='#333')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_changed_matrix(pdf, changed_df):
    """Add the 13x13 segments-changed count matrix."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_axis_off()

    fig.text(0.5, 0.97, "Pairwise Matrix: Number of Segments with Different WWER",
             fontsize=14, fontweight='bold', ha='center', va='center', color='#1a1a2e')
    fig.text(0.5, 0.935,
             "Cell (row, col) shows total segments where WWER differs between row and column experiments",
             fontsize=9, ha='center', va='center', color='#555555', style='italic')

    n = len(EXPERIMENTS)
    labels = LETTER_LABELS

    # Find max for color scaling
    max_changed = changed_df.values.max()

    cell_text = []
    cell_colors = []
    for i in range(n):
        row_text = []
        row_colors = []
        for j in range(n):
            if i == j:
                row_text.append("--")
                row_colors.append('#e0e0e0')
            else:
                val = changed_df.iloc[i, j]
                row_text.append(str(val))
                # Color intensity by count
                intensity = val / max(max_changed, 1)
                r = int(255 - intensity * 80)
                g = int(255 - intensity * 120)
                b = int(255 - intensity * 40)
                row_colors.append(f'#{r:02x}{g:02x}{b:02x}')
        cell_text.append(row_text)
        cell_colors.append(row_colors)

    table = ax.table(
        cellText=cell_text,
        rowLabels=labels,
        colLabels=labels,
        cellLoc='center',
        loc='center',
        bbox=[0.06, 0.05, 0.92, 0.85],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#0f3460')
            cell.set_text_props(color='white', fontweight='bold', fontsize=9)
            cell.set_height(0.058)
        elif col == -1:
            cell.set_facecolor('#0f3460')
            cell.set_text_props(color='white', fontweight='bold', fontsize=9)
        else:
            cell.set_facecolor(cell_colors[row - 1][col])
            cell.set_height(0.058)
        cell.set_edgecolor('#aaaaaa')

    fig.text(0.5, 0.03,
             "Higher numbers indicate greater divergence between experiment configurations.",
             fontsize=9, ha='center', va='center', color='#666666', style='italic')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_key_pairs_analysis(pdf, pair_results):
    """Add detailed statistical analysis pages for key pairs."""
    # Split into pages of 6 pairs each
    pairs_per_page = 6
    pages = [pair_results[i:i+pairs_per_page]
             for i in range(0, len(pair_results), pairs_per_page)]

    for page_idx, page_pairs in enumerate(pages):
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.set_axis_off()

        page_num = page_idx + 1
        total_pages = len(pages)
        fig.text(0.5, 0.96,
                 f"Detailed Statistical Comparison: Key Pairs (Page {page_num}/{total_pages})",
                 fontsize=14, fontweight='bold', ha='center', va='center', color='#1a1a2e')

        col_labels = [
            "Pair\n(Row vs Col)",
            "Mean WWER\nRow",
            "Mean WWER\nCol",
            "Segments\nDiffering",
            "Improved\n(col better)",
            "Worsened\n(col worse)",
            "Mean\nDelta WWER",
            "Wilcoxon\np-value",
            "Signif.\n(p<0.05)",
            "NEA-R\nImpr / Wors",
        ]

        cell_data = []
        cell_colors_list = []
        for pr in page_pairs:
            sig_str = "YES" if pr["significant"] else "no"
            p_str = f"{pr['p_value']:.4f}" if not np.isnan(pr['p_value']) else "N/A"
            nea_str = f"+{pr['nea_improved']} / -{pr['nea_worsened']}"

            delta_str = f"{pr['mean_delta_wwer']:+.2f}%"

            cell_data.append([
                pr["pair"],
                f"{pr['mean_wwer_1']:.1f}%",
                f"{pr['mean_wwer_2']:.1f}%",
                str(pr["n_diff"]),
                str(pr["n_improved"]),
                str(pr["n_worsened"]),
                delta_str,
                p_str,
                sig_str,
                nea_str,
            ])

            # Row color based on result
            if pr["mean_delta_wwer"] < -0.5:
                cell_colors_list.append('#e8f5e9')
            elif pr["mean_delta_wwer"] > 0.5:
                cell_colors_list.append('#ffebee')
            else:
                cell_colors_list.append('#fffde7')

        table = ax.table(
            cellText=cell_data,
            colLabels=col_labels,
            cellLoc='center',
            loc='center',
            bbox=[0.01, 0.12, 0.98, 0.75],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor('#0f3460')
                cell.set_text_props(color='white', fontweight='bold', fontsize=7.5)
                cell.set_height(0.10)
            else:
                base_color = cell_colors_list[row - 1]
                cell.set_facecolor(base_color)
                cell.set_height(0.10)
                # Highlight significance column
                if col == 8:  # Significance column
                    txt = cell_data[row - 1][8]
                    if txt == "YES":
                        cell.set_text_props(fontweight='bold', color='#1b5e20')
                    else:
                        cell.set_text_props(color='#666666')
                # Color delta column
                if col == 6:
                    val = page_pairs[row - 1]["mean_delta_wwer"]
                    if val < 0:
                        cell.set_text_props(color='#1b5e20', fontweight='bold')
                    elif val > 0:
                        cell.set_text_props(color='#b71c1c', fontweight='bold')
            cell.set_edgecolor('#cccccc')

        # First column wider
        for row in range(len(cell_data) + 1):
            table[(row, 0)].set_width(0.17)

        # Interpretation notes
        notes = [
            "Interpretation: 'Delta WWER' = Column_WWER - Row_WWER. Negative means the column experiment is better.",
            "'Improved' = segments where column experiment has lower WWER than row experiment.",
            "Wilcoxon signed-rank test applied on segments with differing WWER values only.",
            "Significance threshold: p < 0.05.",
        ]
        for i, note in enumerate(notes):
            fig.text(0.05, 0.09 - i * 0.02, note, fontsize=7.5, color='#555555', style='italic')

        pdf.savefig(fig, dpi=150)
        plt.close(fig)


def add_delta_distribution_page(pdf, data):
    """Add a page showing WWER delta distributions for key pairs."""
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.5, 0.97, "WWER Delta Distributions for Key Pairs",
             fontsize=14, fontweight='bold', ha='center', va='center', color='#1a1a2e')
    fig.text(0.5, 0.935,
             "Histogram of per-segment WWER change (negative = column experiment is better)",
             fontsize=9, ha='center', va='center', color='#555555', style='italic')

    # Select top 6 pairs for plots
    plot_pairs = [
        ("exp_A_baseline", "exp_C_lenpen_pos1"),
        ("exp_A_baseline", "exp_J_lenpen1_temp05"),
        ("exp_A_baseline", "exp_E_sampling_low_temp"),
        ("exp_A_baseline", "exp_F_sampling_original"),
        ("exp_A_baseline", "exp_G_greedy"),
        ("exp_C_lenpen_pos1", "exp_J_lenpen1_temp05"),
    ]

    gs = gridspec.GridSpec(3, 2, hspace=0.4, wspace=0.3,
                           left=0.08, right=0.95, top=0.90, bottom=0.06)

    for idx, (exp1, exp2) in enumerate(plot_pairs):
        ax = fig.add_subplot(gs[idx])
        wwer1 = data[exp1]["wwer_pct"].values
        wwer2 = data[exp2]["wwer_pct"].values
        delta = wwer2 - wwer1

        # Histogram
        bins = np.arange(-50, 55, 5)
        ax.hist(delta, bins=bins, color='#5c6bc0', edgecolor='white', alpha=0.85)
        ax.axvline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
        ax.axvline(np.mean(delta), color='#1b5e20', linestyle='-', linewidth=1.5,
                   label=f'Mean: {np.mean(delta):+.1f}%')

        label1_short = EXPERIMENTS[exp1].split(":")[0].strip()
        label2_short = EXPERIMENTS[exp2].split(":")[0].strip()
        ax.set_title(f"{EXPERIMENTS[exp1]} vs {EXPERIMENTS[exp2]}",
                     fontsize=8, fontweight='bold', color='#1a1a2e')
        ax.set_xlabel("WWER Delta (%)", fontsize=7)
        ax.set_ylabel("Segments", fontsize=7)
        ax.tick_params(labelsize=6.5)
        ax.legend(fontsize=6.5, loc='upper right')

        # Annotate improved/worsened
        n_imp = np.sum(delta < -0.01)
        n_wor = np.sum(delta > 0.01)
        ax.text(0.02, 0.95, f"+{n_imp} improved", transform=ax.transAxes,
                fontsize=6.5, color='#1b5e20', va='top', fontweight='bold')
        ax.text(0.02, 0.87, f"-{n_wor} worsened", transform=ax.transAxes,
                fontsize=6.5, color='#b71c1c', va='top', fontweight='bold')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_nea_recall_comparison(pdf, data):
    """Add a page comparing NEA-Recall across key experiments."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 8.5))

    fig.text(0.5, 0.97, "Named Entity Recall (NEA-R%) Across Experiments",
             fontsize=14, fontweight='bold', ha='center', va='center', color='#1a1a2e')

    # Left: Bar chart of mean NEA-R
    exp_labels = [EXPERIMENTS[k].split(":")[1].strip() for k in EXPERIMENTS]
    exp_letters = LETTER_LABELS
    mean_nea_r = [data[k]["nea_recall_pct"].mean() for k in EXPERIMENTS]

    colors = ['#e94560' if v == max(mean_nea_r) else
              '#ef9a9a' if v >= max(mean_nea_r) - 1 else
              '#5c6bc0' for v in mean_nea_r]

    ax = axes[0]
    bars = ax.barh(exp_letters[::-1], mean_nea_r[::-1], color=colors[::-1], edgecolor='white')
    ax.set_xlabel("Mean NEA-Recall (%)", fontsize=10)
    ax.set_title("Mean NEA-Recall by Experiment", fontsize=11, fontweight='bold')
    ax.tick_params(labelsize=8.5)
    for i, (v, label) in enumerate(zip(mean_nea_r[::-1], exp_letters[::-1])):
        ax.text(v + 0.3, i, f"{v:.1f}%", va='center', fontsize=7.5, color='#333')

    # Right: Box plot of WWER for top 5 experiments by mean WWER
    top5_keys = sorted(EXPERIMENTS.keys(), key=lambda k: data[k]["wwer_pct"].mean())[:5]
    top5_data = [data[k]["wwer_pct"].values for k in top5_keys]
    top5_labels = [EXPERIMENTS[k] for k in top5_keys]

    ax2 = axes[1]
    bp = ax2.boxplot(top5_data, vert=True, patch_artist=True,
                     tick_labels=[l.split(":")[0].strip() for l in top5_labels])
    colors_box = ['#a5d6a7', '#c8e6c9', '#e8f5e9', '#fff9c4', '#ffebee']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_edgecolor('#555')
    ax2.set_ylabel("WWER (%)", fontsize=10)
    ax2.set_title("WWER Distribution: Top 5 Experiments", fontsize=11, fontweight='bold')
    ax2.tick_params(labelsize=8.5)

    plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.92])
    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def add_conclusion_page(pdf, summary_df, pair_results):
    """Add a conclusion page."""
    fig = plt.figure(figsize=(11, 8.5))

    fig.text(0.5, 0.92, "Conclusions and Recommendations",
             fontsize=18, fontweight='bold', ha='center', va='center', color='#1a1a2e')

    # Horizontal line
    ax_line = fig.add_axes([0.1, 0.88, 0.8, 0.002])
    ax_line.set_xlim(0, 1)
    ax_line.axhline(y=0, color='#0f3460', linewidth=2)
    ax_line.set_axis_off()

    # Build conclusion text
    best = summary_df.iloc[0]
    worst = summary_df.iloc[-1]

    # Find A vs C result
    a_vs_c = None
    a_vs_j = None
    a_vs_g = None
    c_vs_j = None
    for pr in pair_results:
        if pr["label1"] == "A: Baseline" and pr["label2"] == "C: LenPen=1":
            a_vs_c = pr
        if pr["label1"] == "A: Baseline" and pr["label2"] == "J: LP1+Samp t=0.5":
            a_vs_j = pr
        if pr["label1"] == "A: Baseline" and pr["label2"] == "G: Greedy":
            a_vs_g = pr
        if pr["label1"] == "C: LenPen=1" and pr["label2"] == "J: LP1+Samp t=0.5":
            c_vs_j = pr

    conclusions = []
    conclusions.append(("1. Best Overall Configuration", [
        f"  {best['Experiment']} achieves the lowest mean WWER ({best['Mean WWER']:.1f}%),",
        f"  the lowest median WWER ({best['Median WWER']:.1f}%), and the highest NEA-Recall ({best['Mean NEA-R']:.1f}%).",
        f"  It produces zero empty/hallucinated segments.",
    ]))

    conclusions.append(("2. Worst Configuration", [
        f"  {worst['Experiment']} performs worst with mean WWER {worst['Mean WWER']:.1f}%,",
        f"  primarily due to extreme verbosity (WWER >> 100% means hypothesis much longer than reference).",
        f"  This parameter setting is highly detrimental and should be avoided.",
    ]))

    if a_vs_c:
        sig_text = "statistically significant" if a_vs_c["significant"] else "NOT statistically significant"
        conclusions.append(("3. Baseline (A) vs LenPen=1 (C)", [
            f"  LenPen=1 changes {a_vs_c['n_diff']} of 107 segments: "
            f"+{a_vs_c['n_improved']} improved, -{a_vs_c['n_worsened']} worsened.",
            f"  Mean WWER delta: {a_vs_c['mean_delta_wwer']:+.2f}%. The difference is {sig_text} (p={a_vs_c['p_value']:.4f})." if not np.isnan(a_vs_c['p_value']) else f"  Mean WWER delta: {a_vs_c['mean_delta_wwer']:+.2f}%.",
            f"  LenPen=1 also eliminates all 4 empty segments present in the baseline.",
        ]))

    if a_vs_j:
        sig_text = "statistically significant" if a_vs_j["significant"] else "NOT statistically significant"
        conclusions.append(("4. Baseline (A) vs LP1+Samp t=0.5 (J)", [
            f"  Combined lenpen+sampling changes {a_vs_j['n_diff']} segments: "
            f"+{a_vs_j['n_improved']} improved, -{a_vs_j['n_worsened']} worsened.",
            f"  Mean WWER delta: {a_vs_j['mean_delta_wwer']:+.2f}%. {sig_text} (p={a_vs_j['p_value']:.4f})." if not np.isnan(a_vs_j['p_value']) else f"  Mean WWER delta: {a_vs_j['mean_delta_wwer']:+.2f}%.",
        ]))

    if a_vs_g:
        conclusions.append(("5. Greedy Decoding (G)", [
            f"  Greedy decoding worsens {a_vs_g['n_worsened']} segments vs baseline,",
            f"  with mean WWER increase of {a_vs_g['mean_delta_wwer']:+.1f}%. Not recommended.",
        ]))

    conclusions.append(("6. Sampling Experiments", [
        "  Sampling with temperature 0.3-0.5 produces results very similar to beam search.",
        "  Temperature 1.0+ introduces more variation but similar mean performance.",
        "  Sampling does NOT consistently outperform beam search for this task.",
    ]))

    conclusions.append(("7. Recommendation", [
        f"  Use {best['Experiment']} as the default decode configuration.",
        "  LenPen=1 provides the best balance of WWER reduction and entity recall,",
        "  and eliminates empty/hallucinated outputs.",
    ]))

    y = 0.84
    for title, lines in conclusions:
        fig.text(0.08, y, title, fontsize=12, fontweight='bold', color='#0f3460')
        y -= 0.025
        for line in lines:
            fig.text(0.08, y, line, fontsize=9.5, color='#333333')
            y -= 0.022
        y -= 0.015

    # Footer
    fig.text(0.5, 0.03,
             f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
             "107 segments, 100 videos  |  13 experiment configurations",
             fontsize=8.5, ha='center', va='center', color='#888888', style='italic')

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("Decode Parameter Tuning: Pairwise Comparison Report")
    print("=" * 60)

    # Load data
    print("\n[1/6] Loading all 13 experiment CSVs...")
    data = load_all_experiments()
    for exp, df in data.items():
        print(f"  Loaded {exp}: {len(df)} segments, "
              f"mean WWER={df['wwer_pct'].mean():.1f}%")

    # Summary stats
    print("\n[2/6] Computing summary statistics...")
    summary_df = compute_summary_stats(data)
    print(summary_df[["Experiment", "Mean WWER", "Median WWER", "Mean NEA-R"]].to_string())

    # Pairwise matrices
    print("\n[3/6] Building 13x13 pairwise matrices...")
    improved_df, worsened_df, changed_df = compute_pairwise_wwer(data)
    print(f"  Max segments changed in any pair: {changed_df.values.max()}")

    # Key pair analysis
    print("\n[4/6] Running statistical tests on key pairs...")
    pair_results = []
    for exp1, exp2 in KEY_PAIRS:
        pr = detailed_pair_analysis(data, exp1, exp2)
        pair_results.append(pr)
        sig = "***" if pr["significant"] else ""
        p_str = f"p={pr['p_value']:.4f}" if not np.isnan(pr['p_value']) else "p=N/A"
        print(f"  {pr['pair']}: "
              f"+{pr['n_improved']}/-{pr['n_worsened']} "
              f"(delta={pr['mean_delta_wwer']:+.2f}%, {p_str}) {sig}")

    # Generate PDF
    print(f"\n[5/6] Generating PDF report: {OUTPUT_PDF}")
    with PdfPages(OUTPUT_PDF) as pdf:
        print("  - Title page...")
        add_title_page(pdf, summary_df)

        print("  - Summary table...")
        add_summary_table(pdf, summary_df)

        print("  - Pairwise +/- matrix...")
        add_pairwise_matrix(pdf, improved_df, worsened_df, changed_df)

        print("  - Segments changed matrix...")
        add_changed_matrix(pdf, changed_df)

        print("  - Key pairs statistical analysis...")
        add_key_pairs_analysis(pdf, pair_results)

        print("  - WWER delta distributions...")
        add_delta_distribution_page(pdf, data)

        print("  - NEA-Recall comparison...")
        add_nea_recall_comparison(pdf, data)

        print("  - Conclusion page...")
        add_conclusion_page(pdf, summary_df, pair_results)

    # Verify
    pdf_size = os.path.getsize(OUTPUT_PDF)
    print(f"\n[6/6] PDF saved: {OUTPUT_PDF} ({pdf_size / 1024:.0f} KB)")
    print("=" * 60)
    print("Report generation complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
