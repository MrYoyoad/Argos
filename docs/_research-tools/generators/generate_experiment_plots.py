#!/usr/bin/env python3
"""
Argos Decode Experiment Analysis — 16 Analytical Plots

Generates PNG plots analyzing 13 tuning experiments (A–M, 107 segments each)
across metrics (WER, WWER, NEA Recall, NEA F1) vs segment duration and ref word count.

Experiments D (45% empty) and H (hallucination) are excluded as known failures.

Usage:
    python3 generate_experiment_plots.py

Output:
    docs/evaluation/plots/*.png  (16 files)
"""

import os
import csv
import json
import warnings
import numpy as np
import pandas as pd
from collections import OrderedDict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats as sp_stats

warnings.filterwarnings("ignore", category=FutureWarning)

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

BASE_DIR = Path("/home/ubuntu/tuning_results")
META_PATH = Path("/home/ubuntu/english_full_results/segment_metadata.json")
FULL_J_PATH = BASE_DIR / "full_decode_J" / "report" / "report.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation" / "plots"

PLOT_DPI = 200
FIG_SIZE = (10, 6)
FIG_SIZE_WIDE = (12, 6)
FIG_SIZE_TALL = (10, 8)

# All 13 experiments (ordered)
EXPERIMENTS = OrderedDict([
    ("exp_A_baseline",          "A: Baseline"),
    ("exp_B_no_rep_pen",        "B: No RepPen"),
    ("exp_C_lenpen_pos1",       "C: LenPen=1"),
    ("exp_D_lenpen_neg05",      "D: LenPen=-0.5"),
    ("exp_E_sampling_low_temp", "E: Samp t=0.5"),
    ("exp_F_sampling_original", "F: Samp t=1.0"),
    ("exp_G_greedy",            "G: Greedy"),
    ("exp_H_lenpen_pos2",       "H: LenPen=2"),
    ("exp_I_lenpen1_sample",    "I: LP1+Samp"),
    ("exp_J_lenpen1_temp05",    "J: LP1+t=0.5"),
    ("exp_K_sampling_temp15",   "K: Samp t=1.5"),
    ("exp_L_sampling_temp03",   "L: Samp t=0.3"),
    ("exp_M_lenpen1_temp03",    "M: LP1+t=0.3"),
])

# Exclude pathological experiments
EXCLUDED = {"exp_D_lenpen_neg05", "exp_H_lenpen_pos2"}

# Good experiments (all except D and H)
GOOD_EXPS = OrderedDict(
    (k, v) for k, v in EXPERIMENTS.items() if k not in EXCLUDED
)

# Curated subset for line plots (5 representative configs)
CURATED_KEYS = [
    "exp_A_baseline",
    "exp_C_lenpen_pos1",
    "exp_E_sampling_low_temp",
    "exp_G_greedy",
    "exp_J_lenpen1_temp05",
]

CURATED_COLORS = {
    "exp_A_baseline":          "#1f77b4",  # blue
    "exp_C_lenpen_pos1":       "#2ca02c",  # green
    "exp_E_sampling_low_temp": "#ff7f0e",  # orange
    "exp_G_greedy":            "#9467bd",  # purple
    "exp_J_lenpen1_temp05":    "#e377c2",  # pink
}

CURATED_MARKERS = {
    "exp_A_baseline":          "o",
    "exp_C_lenpen_pos1":       "s",
    "exp_E_sampling_low_temp": "D",
    "exp_G_greedy":            "^",
    "exp_J_lenpen1_temp05":    "P",
}


# ════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════

def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def load_experiment(csv_path):
    """Load a single experiment CSV into a DataFrame with derived columns."""
    df = pd.read_csv(csv_path)
    # Ensure numeric columns
    for col in ["wer_%", "wwer_%", "nea_recall_%", "nea_precision_%", "nea_f1_%"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    # Derived
    df["ref_word_count"] = df["ref"].fillna("").apply(lambda s: len(s.split()))
    df["hyp_word_count"] = df["hyp"].fillna("").apply(lambda s: len(s.strip().split()) if s.strip() else 0)
    df["is_empty"] = df["hyp"].fillna("").apply(lambda s: s.strip() == "")
    df["hyp_ref_ratio"] = np.where(
        df["ref_word_count"] > 0,
        df["hyp_word_count"] / df["ref_word_count"],
        0.0,
    )
    return df


def load_all_experiments():
    """Load all 13 experiment CSVs."""
    data = OrderedDict()
    for key in EXPERIMENTS:
        csv_path = BASE_DIR / key / "report" / "report.csv"
        if csv_path.exists():
            data[key] = load_experiment(csv_path)
    return data


def load_full_decode_j():
    """Load the full 1497-segment decode J run."""
    return load_experiment(FULL_J_PATH)


def load_segment_metadata():
    """Load segment_metadata.json → dict mapping utt_id to duration in seconds."""
    with open(META_PATH) as f:
        raw = json.load(f)
    meta = {}
    for seg_id, info in raw.items():
        segs = info.get("segments", [])
        if segs:
            meta[seg_id] = segs[0]["duration"]
        else:
            meta[seg_id] = info.get("original_duration", 0.0)
    return meta


def enrich_with_metadata(df, meta):
    """Add duration_sec column by joining on utt_id."""
    df = df.copy()
    df["duration_sec"] = df["utt_id"].map(meta).fillna(0.0)
    return df


# ════════════════════════════════════════════════════════════
# STYLE
# ════════════════════════════════════════════════════════════

def setup_style():
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "#f8f9fa",
        "axes.edgecolor": "#cccccc",
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })


def save_plot(fig, filename):
    path = OUTPUT_DIR / filename
    fig.savefig(str(path), dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {filename}")


# ════════════════════════════════════════════════════════════
# PLOT HELPER: Binned Metric vs Variable (Plots 1-8)
# ════════════════════════════════════════════════════════════

def compute_bin_edges(all_values, n_bins=5):
    """Compute nice bin edges from data quantiles."""
    quantiles = np.linspace(0, 100, n_bins + 1)
    edges = np.percentile(all_values, quantiles)
    # Round to 1 decimal for duration, integers for word counts
    if np.max(all_values) > 20:
        edges = np.round(edges).astype(int)
    else:
        edges = np.round(edges, 1)
    # Ensure unique edges
    edges = np.unique(edges)
    return edges


def plot_metric_vs_binned(data_dict, x_col, y_col, bin_edges,
                          experiments, colors, markers,
                          xlabel, ylabel, title, filename,
                          note=None):
    """Binned line plot of metric vs variable with SEM error bars."""
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    # Small horizontal offsets so error bars don't overlap
    n_exp = len(experiments)
    offsets = np.linspace(-0.15, 0.15, n_exp)

    for idx, key in enumerate(experiments):
        if key not in data_dict:
            continue
        df = data_dict[key]
        label = EXPERIMENTS[key]
        color = colors[key]
        marker = markers[key]

        # Bin the data
        bins = pd.cut(df[x_col], bins=bin_edges, include_lowest=True)
        grouped = df.groupby(bins, observed=True)[y_col]
        means = grouped.mean()
        sems = grouped.sem()
        counts = grouped.count()

        # Bin centers
        x_centers = np.array([interval.mid for interval in means.index])
        y_means = means.values
        y_sems = sems.fillna(0).values

        # Skip bins with < 3 samples
        mask = counts.values >= 3
        x_plot = x_centers[mask] + offsets[idx]
        y_plot = y_means[mask]
        e_plot = y_sems[mask]

        ax.errorbar(x_plot, y_plot, yerr=e_plot,
                     label=label, color=color, marker=marker,
                     linewidth=2, markersize=7, capsize=4, capthick=1.5,
                     alpha=0.85)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    ax.grid(True, alpha=0.3)

    if note:
        ax.text(0.02, 0.02, note, transform=ax.transAxes,
                fontsize=8, color="gray", fontstyle="italic", va="bottom")

    fig.tight_layout()
    save_plot(fig, filename)


# ════════════════════════════════════════════════════════════
# PLOT 9: Box Plot — WWER All Good Experiments
# ════════════════════════════════════════════════════════════

def plot_boxplot_wwer(data_dict):
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)

    # Build long-form data
    rows = []
    for key in GOOD_EXPS:
        if key not in data_dict:
            continue
        df = data_dict[key]
        label = GOOD_EXPS[key]
        for val in df["wwer_%"]:
            rows.append({"Experiment": label, "WWER (%)": min(val, 200)})

    long_df = pd.DataFrame(rows)

    # Sort by median
    medians = long_df.groupby("Experiment")["WWER (%)"].median().sort_values()
    order = medians.index.tolist()

    palette = sns.color_palette("husl", len(order))
    sns.boxplot(data=long_df, y="Experiment", x="WWER (%)", orient="h",
                order=order, palette=palette, showfliers=False, ax=ax)

    # Add median labels
    for i, exp in enumerate(order):
        med = medians[exp]
        ax.text(med + 2, i, f"{med:.0f}%", va="center", fontsize=8, color="gray")

    ax.set_title("WWER Distribution by Experiment (D, H excluded)", fontweight="bold")
    ax.set_xlim(0, 200)
    ax.text(0.98, 0.02, "Configs D (45% empty) and H (hallucination) excluded",
            transform=ax.transAxes, fontsize=8, color="gray", ha="right", va="bottom",
            fontstyle="italic")
    fig.tight_layout()
    save_plot(fig, "09_boxplot_wwer_all_experiments.png")


# ════════════════════════════════════════════════════════════
# PLOT 10: Failure Mode Bar Chart
# ════════════════════════════════════════════════════════════

def plot_failure_modes(data_dict):
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)

    labels = []
    empty_rates = []
    halluc_rates = []
    perfect_rates = []

    for key in GOOD_EXPS:
        if key not in data_dict:
            continue
        df = data_dict[key]
        n = len(df)
        labels.append(GOOD_EXPS[key].split(":")[0])  # just letter
        empty_rates.append(100 * df["is_empty"].sum() / n)
        halluc_rates.append(100 * (df["hyp_ref_ratio"] > 2.0).sum() / n)
        perfect_rates.append(100 * (df["wer_%"] == 0).sum() / n)

    x = np.arange(len(labels))
    w = 0.25

    ax.bar(x - w, empty_rates, w, label="Empty predictions", color="#d62728", alpha=0.8)
    ax.bar(x,     halluc_rates, w, label="Hallucinations (hyp > 2× ref)", color="#ff7f0e", alpha=0.8)
    ax.bar(x + w, perfect_rates, w, label="Perfect (WER = 0%)", color="#2ca02c", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("% of Segments")
    ax.set_title("Failure Modes by Experiment (D, H excluded)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    save_plot(fig, "10_empty_and_hallucination_rates.png")


# ════════════════════════════════════════════════════════════
# PLOT 11: WER vs WWER Scatter
# ════════════════════════════════════════════════════════════

def plot_wer_vs_wwer_scatter(data_dict):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    for key in CURATED_KEYS:
        if key not in data_dict:
            continue
        df = data_dict[key]
        label = EXPERIMENTS[key]
        ax.scatter(df["wer_%"].clip(upper=200),
                   df["wwer_%"].clip(upper=200),
                   label=label, color=CURATED_COLORS[key],
                   marker=CURATED_MARKERS[key],
                   alpha=0.4, s=30, edgecolors="none")

    ax.plot([0, 200], [0, 200], "k--", alpha=0.3, linewidth=1, label="y = x")
    ax.set_xlabel("WER (%)")
    ax.set_ylabel("WWER (%)")
    ax.set_title("WER vs WWER Per Segment", fontweight="bold")
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=9)
    ax.text(150, 20, "WWER < WER\n(function word errors)",
            fontsize=8, color="gray", ha="center", fontstyle="italic")
    ax.text(20, 180, "WWER > WER\n(entity errors)",
            fontsize=8, color="gray", ha="center", fontstyle="italic")
    fig.tight_layout()
    save_plot(fig, "11_wer_vs_wwer_scatter.png")


# ════════════════════════════════════════════════════════════
# PLOT 12: Segment Stability Heatmap
# ════════════════════════════════════════════════════════════

def plot_segment_stability_heatmap(data_dict):
    # Build matrix: rows=segments, cols=experiments
    good_keys = [k for k in GOOD_EXPS if k in data_dict]
    if not good_keys:
        return

    # Use segment ordering from baseline
    baseline_key = "exp_A_baseline"
    if baseline_key not in data_dict:
        return

    baseline = data_dict[baseline_key].sort_values("wwer_%")
    seg_order = baseline["utt_id"].tolist()

    matrix = np.zeros((len(seg_order), len(good_keys)))
    for j, key in enumerate(good_keys):
        df = data_dict[key].set_index("utt_id")
        for i, seg in enumerate(seg_order):
            if seg in df.index:
                matrix[i, j] = min(df.loc[seg, "wwer_%"], 150)
            else:
                matrix[i, j] = np.nan

    fig, ax = plt.subplots(figsize=(10, 12))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=150,
                   interpolation="nearest")
    ax.set_xticks(range(len(good_keys)))
    ax.set_xticklabels([GOOD_EXPS[k].split(":")[0] for k in good_keys],
                        fontsize=9, rotation=45)
    ax.set_yticks([0, len(seg_order) - 1])
    ax.set_yticklabels(["Best (low WWER)", "Worst (high WWER)"], fontsize=9)
    ax.set_xlabel("Experiment")
    ax.set_ylabel(f"Segments (sorted by baseline WWER, n={len(seg_order)})")
    ax.set_title("WWER Stability Across Experiments (D, H excluded)", fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, shrink=0.6, label="WWER (%) [clipped at 150]")
    fig.tight_layout()
    save_plot(fig, "12_segment_stability_heatmap.png")


# ════════════════════════════════════════════════════════════
# PLOT 13: Duration Histogram
# ════════════════════════════════════════════════════════════

def plot_duration_histogram(data_dict, full_j_df, meta):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    # Tuning subset durations
    baseline = data_dict.get("exp_A_baseline")
    if baseline is not None:
        tuning_durs = baseline["duration_sec"].values
        tuning_durs = tuning_durs[tuning_durs > 0]
        ax.hist(tuning_durs, bins=25, density=True, alpha=0.5,
                color="#1f77b4", label=f"Tuning subset (n={len(tuning_durs)})")

    # Full decode J durations
    if full_j_df is not None:
        full_durs = full_j_df["duration_sec"].values
        full_durs = full_durs[full_durs > 0]
        ax.hist(full_durs, bins=40, density=True, alpha=0.4,
                color="#ff7f0e", label=f"Full decode J (n={len(full_durs)})")

    ax.set_xlabel("Segment Duration (seconds)")
    ax.set_ylabel("Density")
    ax.set_title("Duration Distribution: Tuning Subset vs Full Dataset", fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_plot(fig, "13_duration_histogram.png")


# ════════════════════════════════════════════════════════════
# PLOT 14: NEA Recall vs WWER Scatter
# ════════════════════════════════════════════════════════════

def plot_nea_vs_wwer_scatter(data_dict):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    for key in CURATED_KEYS:
        if key not in data_dict:
            continue
        df = data_dict[key]
        label = EXPERIMENTS[key]
        ax.scatter(df["wwer_%"].clip(upper=200),
                   df["nea_recall_%"],
                   label=label, color=CURATED_COLORS[key],
                   marker=CURATED_MARKERS[key],
                   alpha=0.4, s=30, edgecolors="none")

    ax.set_xlabel("WWER (%)")
    ax.set_ylabel("NEA Recall (%)")
    ax.set_title("Named Entity Recall vs WWER Per Segment", fontweight="bold")
    ax.set_xlim(0, 200)
    ax.set_ylim(-5, 105)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_plot(fig, "14_nea_vs_wwer_scatter.png")


# ════════════════════════════════════════════════════════════
# PLOT 15: CDF of WWER
# ════════════════════════════════════════════════════════════

def plot_cdf_wwer(data_dict):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    for key in CURATED_KEYS:
        if key not in data_dict:
            continue
        df = data_dict[key]
        label = EXPERIMENTS[key]
        vals = np.sort(df["wwer_%"].clip(upper=200).values)
        cdf = np.linspace(0, 1, len(vals))
        ax.step(vals, cdf, label=label, color=CURATED_COLORS[key],
                linewidth=2, alpha=0.85)

    # Reference lines
    ax.axvline(50, color="gray", linestyle=":", alpha=0.4, linewidth=1)
    ax.axhline(0.5, color="gray", linestyle=":", alpha=0.4, linewidth=1)
    ax.text(52, 0.02, "WWER = 50%", fontsize=8, color="gray")

    ax.set_xlabel("WWER (%)")
    ax.set_ylabel("Cumulative Proportion of Segments")
    ax.set_title("Empirical CDF of WWER by Experiment", fontweight="bold")
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_plot(fig, "15_cdf_wwer_curated.png")


# ════════════════════════════════════════════════════════════
# PLOT 16: Per-Segment Improvement J vs A
# ════════════════════════════════════════════════════════════

def plot_j_vs_a_improvement(data_dict):
    a_key, j_key = "exp_A_baseline", "exp_J_lenpen1_temp05"
    if a_key not in data_dict or j_key not in data_dict:
        return

    df_a = data_dict[a_key].set_index("utt_id")
    df_j = data_dict[j_key].set_index("utt_id")
    common = df_a.index.intersection(df_j.index)

    deltas = (df_j.loc[common, "wwer_%"] - df_a.loc[common, "wwer_%"]).sort_values()

    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)

    colors = ["#2ca02c" if d < -0.5 else "#d62728" if d > 0.5 else "#999999"
              for d in deltas.values]
    ax.bar(range(len(deltas)), deltas.values, color=colors, width=1.0, edgecolor="none")
    ax.axhline(0, color="black", linewidth=0.8)

    n_improved = sum(1 for d in deltas if d < -0.5)
    n_worsened = sum(1 for d in deltas if d > 0.5)
    n_same = len(deltas) - n_improved - n_worsened

    ax.set_xlabel(f"Segments (sorted by WWER change, n={len(deltas)})")
    ax.set_ylabel("WWER Change (J \u2212 A) in %")
    ax.set_title("Per-Segment Improvement: Config J vs Baseline A", fontweight="bold")
    ax.text(0.02, 0.98,
            f"Improved: {n_improved}  |  Unchanged: {n_same}  |  Worsened: {n_worsened}",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    save_plot(fig, "16_improvement_J_vs_A.png")


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def main():
    print("Loading data...")
    meta = load_segment_metadata()
    data = load_all_experiments()

    for key in data:
        data[key] = enrich_with_metadata(data[key], meta)
        print(f"  {EXPERIMENTS[key]}: {len(data[key])} segments, "
              f"{data[key]['duration_sec'].gt(0).sum()} with duration")

    full_j = load_full_decode_j()
    full_j = enrich_with_metadata(full_j, meta)
    print(f"  Full decode J: {len(full_j)} segments")

    setup_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Compute bin edges from pooled data ──
    baseline = data.get("exp_A_baseline")
    if baseline is None:
        print("ERROR: Baseline experiment not found")
        return

    dur_edges = compute_bin_edges(baseline["duration_sec"][baseline["duration_sec"] > 0], n_bins=5)
    wc_edges = compute_bin_edges(baseline["ref_word_count"][baseline["ref_word_count"] > 0], n_bins=5)
    print(f"\n  Duration bin edges: {dur_edges}")
    print(f"  Word count bin edges: {wc_edges}")

    note = "Configs D (45% empty) and H (hallucination) excluded"

    # ── Plots 1-8: Metric vs Duration & Ref Words ──
    print("\nGenerating binned line plots (1-8)...")
    metrics = [
        ("wer_%",        "WER (%)",        "WER"),
        ("wwer_%",       "WWER (%)",       "WWER"),
        ("nea_recall_%", "NEA Recall (%)", "NEA Recall"),
        ("nea_f1_%",     "NEA F1 (%)",     "NEA F1"),
    ]

    curated_data = {k: data[k] for k in CURATED_KEYS if k in data}

    for i, (col, ylabel, short) in enumerate(metrics):
        # vs duration
        plot_metric_vs_binned(
            curated_data, x_col="duration_sec", y_col=col,
            bin_edges=dur_edges,
            experiments=CURATED_KEYS, colors=CURATED_COLORS,
            markers=CURATED_MARKERS,
            xlabel="Segment Duration (seconds)", ylabel=ylabel,
            title=f"{short} by Segment Duration",
            filename=f"{i*2+1:02d}_{short.lower().replace(' ', '_')}_vs_duration.png",
            note=note,
        )
        # vs ref word count
        plot_metric_vs_binned(
            curated_data, x_col="ref_word_count", y_col=col,
            bin_edges=wc_edges,
            experiments=CURATED_KEYS, colors=CURATED_COLORS,
            markers=CURATED_MARKERS,
            xlabel="Reference Word Count", ylabel=ylabel,
            title=f"{short} by Reference Word Count",
            filename=f"{i*2+2:02d}_{short.lower().replace(' ', '_')}_vs_refwords.png",
            note=note,
        )

    # ── Plots 9-16: Additional Analysis ──
    print("\nGenerating additional plots (9-16)...")
    plot_boxplot_wwer(data)
    plot_failure_modes(data)
    plot_wer_vs_wwer_scatter(data)
    plot_segment_stability_heatmap(data)
    plot_duration_histogram(data, full_j, meta)
    plot_nea_vs_wwer_scatter(data)
    plot_cdf_wwer(data)
    plot_j_vs_a_improvement(data)

    # Summary
    pngs = sorted(OUTPUT_DIR.glob("*.png"))
    print(f"\nDone! {len(pngs)} plots saved to {OUTPUT_DIR}/")
    for p in pngs:
        print(f"  {p.name} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
