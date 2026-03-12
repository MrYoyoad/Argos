#!/usr/bin/env python3
"""Generate signal distribution plots across IS tiers and LLM judge categories.

Output:
  docs/evaluation/plots/P7_signal_by_tier.png
  docs/evaluation/plots/P8_signal_by_judge.png
"""

import csv
import statistics
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path("/home/ubuntu")
IS_CSV = ROOT / "docs/evaluation/intelligibility/intelligibility_scores.csv"
JUDGE_CSV = ROOT / "docs/evaluation/llm_judge/llm_judge_results.csv"
CONTEXT_CSV = ROOT / "docs/evaluation/llm_judge/context_eval/context_eval_results.csv"
OUT_DIR = ROOT / "docs/evaluation/plots"

# ── Styling (matplotlib analytical defaults per STYLE_GUIDE) ─────────
COLORS_TIER = {
    1: "#d62728",   # Failed — red
    2: "#ff7f0e",   # Poor — orange
    3: "#ffbb33",   # Fair — amber
    4: "#2ca02c",   # Good — green
    5: "#1f77b4",   # Excellent — blue
}
TIER_LABELS = {1: "Failed\n(0–1)", 2: "Poor\n(1–2)", 3: "Fair\n(2–3)",
               4: "Good\n(3–4)", 5: "Excellent\n(4–5)"}

COLORS_JUDGE = {"N": "#d62728", "P": "#ff7f0e", "Y": "#2ca02c"}
JUDGE_LABELS = {"N": "N (No)", "P": "P (Partial)", "Y": "Y (Yes)"}
JUDGE_ORDER = ["N", "P", "Y"]

# Signals to plot (normalized to 0–1 scale)
SIGNALS = [
    ("semantic_sim",  "Semantic\nSimilarity"),
    ("phonetic_sim",  "Phonetic\nSimilarity"),
    ("wer_norm",      "1 − WER\n(inverted)"),
    ("wwer_norm",     "1 − WWER\n(inverted)"),
    ("nea_f1_norm",   "NEA F1"),
    ("length_ratio",  "Length\nRatio"),
]


def load_is_data():
    """Load IS scores CSV, return list of dicts with normalized signals."""
    rows = []
    with open(IS_CSV) as f:
        for row in csv.DictReader(f):
            r = {}
            r["tier"] = int(row["is_tier"])
            r["semantic_sim"] = float(row["semantic_sim"]) if row["semantic_sim"] else None
            r["phonetic_sim"] = float(row["phonetic_sim"]) if row["phonetic_sim"] else None
            r["wer_norm"] = 1.0 - float(row["wer_%"]) / 100.0 if row["wer_%"] else None
            r["wwer_norm"] = 1.0 - float(row["wwer_%"]) / 100.0 if row["wwer_%"] else None
            r["nea_f1_norm"] = float(row["nea_f1_%"]) / 100.0 if row["nea_f1_%"] else None
            r["length_ratio"] = float(row["length_ratio"]) if row["length_ratio"] else None
            rows.append(r)
    return rows


def load_judge_data():
    """Load LLM judge CSV, return rows with blind judge + signals."""
    rows = []
    with open(JUDGE_CSV) as f:
        for row in csv.DictReader(f):
            r = {}
            r["utt_id"] = row["utt_id"]
            r["blind"] = row["llm_judge"]
            r["semantic_sim"] = float(row["semantic_sim"]) if row["semantic_sim"] else None
            r["phonetic_sim"] = float(row["phonetic_sim"]) if row["phonetic_sim"] else None
            r["wer_norm"] = 1.0 - float(row["wer_%"]) / 100.0 if row["wer_%"] else None
            r["wwer_norm"] = 1.0 - float(row["wwer_%"]) / 100.0 if row["wwer_%"] else None
            r["nea_f1_norm"] = float(row["nea_f1_%"]) / 100.0 if row["nea_f1_%"] else None
            r["length_ratio"] = float(row["length_ratio"]) if row["length_ratio"] else None
            rows.append(r)
    return rows


def load_context_data():
    """Load context eval CSV, return utt_id → context_judge mapping."""
    ctx = {}
    with open(CONTEXT_CSV) as f:
        for row in csv.DictReader(f):
            ctx[row["utt_id"]] = row["context"]
    return ctx


def compute_stats(rows, group_key, group_values, signal_keys):
    """Compute mean and std for each signal in each group."""
    buckets = {g: {s: [] for s in signal_keys} for g in group_values}
    for row in rows:
        g = row.get(group_key)
        if g not in buckets:
            continue
        for s in signal_keys:
            v = row.get(s)
            if v is not None:
                buckets[g][s].append(v)

    means = {}
    stds = {}
    counts = {}
    for g in group_values:
        means[g] = {}
        stds[g] = {}
        counts[g] = len(buckets[g][signal_keys[0]])
        for s in signal_keys:
            vals = buckets[g][s]
            means[g][s] = statistics.mean(vals) if vals else 0
            stds[g][s] = statistics.stdev(vals) if len(vals) > 1 else 0
    return means, stds, counts


def plot_grouped_bars(ax, group_values, group_labels, group_colors,
                      means, stds, counts, signal_names, title):
    """Draw a grouped bar chart: groups on x-axis, one bar per signal."""
    n_groups = len(group_values)
    n_signals = len(signal_names)
    x = np.arange(n_signals)
    width = 0.8 / n_groups

    signal_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for i, g in enumerate(group_values):
        vals = [means[g][s] for s, _ in SIGNALS]
        errs = [stds[g][s] for s, _ in SIGNALS]
        offset = (i - n_groups / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width * 0.9,
                       label=f"{group_labels[g]} (n={counts[g]})",
                       color=group_colors[g], edgecolor="white", linewidth=0.8,
                       alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in SIGNALS], fontsize=9)
    ax.set_ylabel("Mean Signal Value (0–1 scale)", fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_ylim(0, 1.15)
    ax.axhline(y=1.0, color="gray", linewidth=0.5, linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)


def plot_tier_chart():
    """P7: Signal distribution across IS tiers."""
    rows = load_is_data()
    sig_keys = [s for s, _ in SIGNALS]
    tiers = [1, 2, 3, 4, 5]

    means, stds, counts = compute_stats(rows, "tier", tiers, sig_keys)

    fig, ax = plt.subplots(figsize=(12, 6))
    plot_grouped_bars(ax, tiers, TIER_LABELS, COLORS_TIER,
                      means, stds, counts,
                      [label for _, label in SIGNALS],
                      "IS Component Signals by Quality Tier")

    # Annotation about semantic spread as tiebreaker
    ax.annotate("Semantic has highest spread\nin Fair tier (σ=0.151)\n→ tiebreaker signal",
                xy=(0, means[3]["semantic_sim"]), xytext=(1.8, 0.28),
                fontsize=8, fontstyle="italic", color="#555555",
                arrowprops=dict(arrowstyle="->", color="#999999", lw=1),
                bbox=dict(boxstyle="round,pad=0.3", fc="#ffffdd", ec="#ccccaa", alpha=0.9))

    fig.tight_layout()
    out_path = OUT_DIR / "P7_signal_by_tier.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_judge_chart():
    """P8: Signal distribution across LLM judge categories (blind + context)."""
    judge_rows = load_judge_data()
    context_map = load_context_data()

    # Merge context judgments into rows
    for row in judge_rows:
        row["context"] = context_map.get(row["utt_id"], None)

    sig_keys = [s for s, _ in SIGNALS]

    # Blind judge
    blind_means, blind_stds, blind_counts = compute_stats(
        judge_rows, "blind", JUDGE_ORDER, sig_keys)

    # Context judge — only rows that have context judgments
    ctx_rows = [r for r in judge_rows if r["context"] in JUDGE_ORDER]
    ctx_means, ctx_stds, ctx_counts = compute_stats(
        ctx_rows, "context", JUDGE_ORDER, sig_keys)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    plot_grouped_bars(ax1, JUDGE_ORDER, JUDGE_LABELS, COLORS_JUDGE,
                      blind_means, blind_stds, blind_counts,
                      [label for _, label in SIGNALS],
                      "LLM Judge — Blind Evaluation")

    plot_grouped_bars(ax2, JUDGE_ORDER, JUDGE_LABELS, COLORS_JUDGE,
                      ctx_means, ctx_stds, ctx_counts,
                      [label for _, label in SIGNALS],
                      "LLM Judge — Context-Aware Evaluation")

    ax2.set_ylabel("")  # shared y-axis

    fig.suptitle("IS Component Signals by LLM-as-a-Judge Category",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    out_path = OUT_DIR / "P8_signal_by_judge.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def load_is_data_full():
    """Load IS scores with raw IS value for continuous analysis."""
    rows = []
    with open(IS_CSV) as f:
        for row in csv.DictReader(f):
            r = {}
            r["is_score"] = float(row["intelligibility_score"])
            r["tier"] = int(row["is_tier"])
            r["semantic_sim"] = float(row["semantic_sim"]) if row["semantic_sim"] else None
            r["phonetic_sim"] = float(row["phonetic_sim"]) if row["phonetic_sim"] else None
            r["wer_norm"] = 1.0 - float(row["wer_%"]) / 100.0 if row["wer_%"] else None
            r["wwer_norm"] = 1.0 - float(row["wwer_%"]) / 100.0 if row["wwer_%"] else None
            r["nea_f1_norm"] = float(row["nea_f1_%"]) / 100.0 if row["nea_f1_%"] else None
            r["length_ratio"] = float(row["length_ratio"]) if row["length_ratio"] else None
            rows.append(r)
    return rows


def plot_signal_trajectories():
    """P9: Signal trajectories across IS range with NIV thresholds + phase change."""
    rows = load_is_data_full()

    # Bin by 0.25 IS increments for smooth curves
    bin_width = 0.25
    bins = np.arange(0, 5.0 + bin_width, bin_width)
    sig_keys = ["semantic_sim", "phonetic_sim", "wer_norm", "wwer_norm",
                "nea_f1_norm", "length_ratio"]
    sig_labels = ["Semantic", "Phonetic", "1−WER", "1−WWER", "NEA F1", "Length Ratio"]
    sig_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    sig_styles = ["-", "-", "--", "--", "-.", ":"]

    # Compute bin means and stds
    midpoints = []
    bin_means = {s: [] for s in sig_keys}
    bin_stds = {s: [] for s in sig_keys}
    bin_counts = []

    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        subset = [r for r in rows if lo <= r["is_score"] < hi]
        if len(subset) < 5:
            continue
        midpoints.append((lo + hi) / 2)
        bin_counts.append(len(subset))
        for s in sig_keys:
            vals = [r[s] for r in subset if r[s] is not None]
            bin_means[s].append(np.mean(vals) if vals else 0)
            bin_stds[s].append(np.std(vals) if vals else 0)

    midpoints = np.array(midpoints)

    # ── Figure: 3 panels ────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(14, 14),
                              gridspec_kw={"height_ratios": [3, 2, 1.5]})

    # ── Panel 1: Signal means across IS range ────────────────────────
    ax1 = axes[0]
    for s, label, color, ls in zip(sig_keys, sig_labels, sig_colors, sig_styles):
        means_arr = np.array(bin_means[s])
        stds_arr = np.array(bin_stds[s])
        ax1.plot(midpoints, means_arr, ls, color=color, linewidth=2.5,
                 label=label, alpha=0.9)
        ax1.fill_between(midpoints, means_arr - stds_arr, means_arr + stds_arr,
                         color=color, alpha=0.08)

    # NIV thresholds
    ax1.axvline(x=2.00, color="#888888", linewidth=2, linestyle="--", alpha=0.7)
    ax1.axvline(x=3.80, color="#888888", linewidth=2, linestyle="--", alpha=0.7)
    ax1.text(2.00, 1.05, "NIV Y+P\n(IS ≥ 2.00)", ha="center", fontsize=9,
             color="#555555", fontweight="bold")
    ax1.text(3.80, 1.05, "NIV Y\n(IS ≥ 3.80)", ha="center", fontsize=9,
             color="#555555", fontweight="bold")

    # Shade the three NIV zones
    ax1.axvspan(0, 2.00, alpha=0.04, color="#d62728")
    ax1.axvspan(2.00, 3.80, alpha=0.04, color="#ff7f0e")
    ax1.axvspan(3.80, 5.0, alpha=0.04, color="#2ca02c")
    ax1.text(1.0, -0.12, "N zone", ha="center", fontsize=10, color="#d62728",
             fontweight="bold")
    ax1.text(2.9, -0.12, "P zone", ha="center", fontsize=10, color="#ff7f0e",
             fontweight="bold")
    ax1.text(4.4, -0.12, "Y zone", ha="center", fontsize=10, color="#2ca02c",
             fontweight="bold")

    ax1.set_xlim(0, 5.0)
    ax1.set_ylim(-0.2, 1.15)
    ax1.set_ylabel("Mean Signal Value (0–1)", fontsize=11)
    ax1.set_title("Signal Trajectories Across IS Range with NIV Thresholds",
                  fontsize=14, fontweight="bold", pad=12)
    ax1.legend(fontsize=9, loc="upper left", ncol=3, framealpha=0.9)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.axhline(y=0, color="gray", linewidth=0.5, alpha=0.3)

    # ── Panel 2: Standard deviation (spread) per bin — tiebreaker ────
    ax2 = axes[1]
    for s, label, color, ls in zip(sig_keys, sig_labels, sig_colors, sig_styles):
        ax2.plot(midpoints, bin_stds[s], ls, color=color, linewidth=2, label=label)

    ax2.axvline(x=2.00, color="#888888", linewidth=2, linestyle="--", alpha=0.5)
    ax2.axvline(x=3.80, color="#888888", linewidth=2, linestyle="--", alpha=0.5)

    # Highlight Fair tier zone
    ax2.axvspan(2.0, 3.0, alpha=0.08, color="#ffbb33")
    ax2.text(2.5, max(max(bin_stds[s]) for s in sig_keys) * 0.95,
             "Fair tier\n(tiebreaker zone)", ha="center", fontsize=9,
             color="#aa8800", fontstyle="italic",
             bbox=dict(boxstyle="round,pad=0.2", fc="#ffffdd", ec="#ccccaa", alpha=0.8))

    ax2.set_xlim(0, 5.0)
    ax2.set_ylabel("Std Dev (within-bin spread)", fontsize=11)
    ax2.set_title("Signal Spread — Where Each Signal Differentiates Most",
                  fontsize=13, fontweight="bold", pad=10)
    ax2.legend(fontsize=8, loc="upper right", ncol=3, framealpha=0.9)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # ── Panel 3: Acceleration (delta of means) — phase change ────────
    ax3 = axes[2]
    for s, label, color, ls in zip(sig_keys, sig_labels, sig_colors, sig_styles):
        means_arr = np.array(bin_means[s])
        if len(means_arr) > 1:
            deltas = np.diff(means_arr)
            delta_x = (midpoints[:-1] + midpoints[1:]) / 2
            ax3.plot(delta_x, deltas, ls, color=color, linewidth=2, label=label)

    ax3.axvline(x=2.00, color="#888888", linewidth=2, linestyle="--", alpha=0.5)
    ax3.axvline(x=3.80, color="#888888", linewidth=2, linestyle="--", alpha=0.5)
    ax3.axhline(y=0, color="gray", linewidth=0.5, alpha=0.3)

    ax3.set_xlim(0, 5.0)
    ax3.set_xlabel("Intelligibility Score (IS)", fontsize=11)
    ax3.set_ylabel("Δ Signal Mean\n(acceleration)", fontsize=11)
    ax3.set_title("Signal Acceleration — Phase Changes in Quality",
                  fontsize=13, fontweight="bold", pad=10)
    ax3.legend(fontsize=8, loc="upper right", ncol=3, framealpha=0.9)
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)

    fig.tight_layout(h_pad=3)
    out_path = OUT_DIR / "P9_signal_trajectories.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_niv_zones():
    """P10: Signal distributions by NIV zone (N / P / Y) — bar chart."""
    rows = load_is_data_full()

    # Assign NIV zone
    for r in rows:
        if r["is_score"] < 2.00:
            r["niv"] = "N"
        elif r["is_score"] < 3.80:
            r["niv"] = "P"
        else:
            r["niv"] = "Y"

    sig_keys = [s for s, _ in SIGNALS]
    niv_order = ["N", "P", "Y"]
    niv_labels = {"N": "N: IS < 2.00\n(No value)", "P": "P: 2.00 ≤ IS < 3.80\n(Partial)",
                  "Y": "Y: IS ≥ 3.80\n(Clearly conveyed)"}
    niv_colors = {"N": "#d62728", "P": "#ff7f0e", "Y": "#2ca02c"}

    means, stds, counts = compute_stats(rows, "niv", niv_order, sig_keys)

    fig, ax = plt.subplots(figsize=(12, 6))
    plot_grouped_bars(ax, niv_order, niv_labels, niv_colors,
                      means, stds, counts,
                      [label for _, label in SIGNALS],
                      "IS Component Signals by NIV Zone")

    fig.tight_layout()
    out_path = OUT_DIR / "P10_signal_by_niv.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def load_full_judge_data():
    """Load judge CSV with IS score, tier, signals, blind + context judge."""
    rows = []
    with open(JUDGE_CSV) as f:
        for row in csv.DictReader(f):
            r = {
                "utt_id": row["utt_id"],
                "is_score": float(row["intelligibility_score"]),
                "tier": int(row["intelligibility_tier"]),
                "blind": row["llm_judge"],
                "wer": float(row["wer_%"]) if row["wer_%"] else None,
                "semantic_sim": float(row["semantic_sim"]) if row["semantic_sim"] else None,
                "phonetic_sim": float(row["phonetic_sim"]) if row["phonetic_sim"] else None,
                "wer_norm": 1.0 - float(row["wer_%"]) / 100.0 if row["wer_%"] else None,
                "wwer_norm": 1.0 - float(row["wwer_%"]) / 100.0 if row["wwer_%"] else None,
                "nea_f1_norm": float(row["nea_f1_%"]) / 100.0 if row["nea_f1_%"] else None,
                "length_ratio": float(row["length_ratio"]) if row["length_ratio"] else None,
            }
            rows.append(r)
    # Merge context
    ctx = load_context_data()
    for r in rows:
        r["context"] = ctx.get(r["utt_id"], None)
    return rows


def _heatmap_data(rows, judge_key, sig_key):
    """Build a 3×5 matrix: judge (N/P/Y) × tier (1-5) → mean signal value."""
    mat = np.full((3, 5), np.nan)
    counts = np.zeros((3, 5), dtype=int)
    judge_idx = {"N": 0, "P": 1, "Y": 2}
    for r in rows:
        j = r.get(judge_key)
        if j not in judge_idx:
            continue
        ji = judge_idx[j]
        ti = r["tier"] - 1
        if mat[ji, ti] != mat[ji, ti]:  # nan check
            mat[ji, ti] = 0
        v = r.get(sig_key)
        if v is not None:
            # running sum, divide later
            mat[ji, ti] = (mat[ji, ti] * counts[ji, ti] + v) / (counts[ji, ti] + 1)
            counts[ji, ti] += 1
    return mat, counts


def plot_judge_tier_heatmaps():
    """P11: Heatmaps — Judge × Tier for each signal, blind and context side by side."""
    rows = load_full_judge_data()

    sig_keys = ["semantic_sim", "phonetic_sim", "wer_norm", "nea_f1_norm", "length_ratio"]
    sig_labels = ["Semantic Similarity", "Phonetic Similarity", "1 − WER",
                  "NEA F1", "Length Ratio"]

    tier_names = ["Failed\n(0–1)", "Poor\n(1–2)", "Fair\n(2–3)",
                  "Good\n(3–4)", "Excellent\n(4–5)"]
    judge_names = ["N", "P", "Y"]

    fig, axes = plt.subplots(len(sig_keys), 2, figsize=(16, 3.2 * len(sig_keys)))

    for row_idx, (sk, sl) in enumerate(zip(sig_keys, sig_labels)):
        for col_idx, (jk, title_suffix) in enumerate(
                [("blind", "Blind Judge"), ("context", "Context Judge")]):
            ax = axes[row_idx, col_idx]
            mat, counts = _heatmap_data(rows, jk, sk)

            im = ax.imshow(mat, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

            # Annotate cells
            for i in range(3):
                for j in range(5):
                    val = mat[i, j]
                    n = counts[i, j]
                    if np.isnan(val) or n == 0:
                        ax.text(j, i, "—", ha="center", va="center",
                                fontsize=9, color="gray")
                    else:
                        color = "white" if val < 0.3 or val > 0.7 else "black"
                        ax.text(j, i, f"{val:.2f}\n(n={n})", ha="center",
                                va="center", fontsize=8, color=color,
                                fontweight="bold")

            ax.set_xticks(range(5))
            ax.set_xticklabels(tier_names, fontsize=8)
            ax.set_yticks(range(3))
            ax.set_yticklabels(judge_names, fontsize=10)
            if col_idx == 0:
                ax.set_ylabel(sl, fontsize=11, fontweight="bold")
            if row_idx == 0:
                ax.set_title(title_suffix, fontsize=13, fontweight="bold", pad=8)

    fig.suptitle("Signal Values: LLM Judge Category × IS Tier",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout(h_pad=1.5, w_pad=2)
    out_path = OUT_DIR / "P11_judge_tier_heatmaps.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_is_vs_wer_thresholds():
    """P12: IS vs WER threshold comparison — judge match rate by tier + signal profiles."""
    rows = load_full_judge_data()

    # Assign NIV zones
    for r in rows:
        r["niv_is"] = "Y" if r["is_score"] >= 3.80 else ("P" if r["is_score"] >= 2.00 else "N")
        r["niv_wer"] = "Y" if r["wer"] is not None and r["wer"] <= 34 else (
            "P" if r["wer"] is not None and r["wer"] <= 77 else "N")

    tier_names = ["Failed", "Poor", "Fair", "Good", "Excellent"]

    # ── Figure with 3 panels ──────────────────────────────────────────
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 7))

    # ── Panel 1: Judge match rate by tier ─────────────────────────────
    tiers = [1, 2, 3, 4, 5]
    is_match_rates = []
    wer_match_rates = []
    for t in tiers:
        subset = [r for r in rows if r["tier"] == t]
        n = len(subset)
        is_match_rates.append(sum(1 for r in subset if r["niv_is"] == r["blind"]) / n * 100)
        wer_match_rates.append(sum(1 for r in subset if r["niv_wer"] == r["blind"]) / n * 100)

    x = np.arange(5)
    w = 0.35
    ax1.bar(x - w/2, is_match_rates, w, label="IS threshold", color="#1f77b4",
            edgecolor="white", linewidth=1)
    ax1.bar(x + w/2, wer_match_rates, w, label="WER threshold", color="#d62728",
            edgecolor="white", linewidth=1)

    # Add value labels
    for i, (is_v, wer_v) in enumerate(zip(is_match_rates, wer_match_rates)):
        ax1.text(i - w/2, is_v + 1, f"{is_v:.0f}%", ha="center", fontsize=8,
                 fontweight="bold", color="#1f77b4")
        ax1.text(i + w/2, wer_v + 1, f"{wer_v:.0f}%", ha="center", fontsize=8,
                 fontweight="bold", color="#d62728")

    # Highlight advantage
    for i in range(5):
        diff = is_match_rates[i] - wer_match_rates[i]
        if abs(diff) > 1:
            color = "#2ca02c" if diff > 0 else "#d62728"
            ax1.text(i, max(is_match_rates[i], wer_match_rates[i]) + 5,
                     f"IS {'+' if diff > 0 else ''}{diff:.1f}pp",
                     ha="center", fontsize=7, color=color, fontstyle="italic")

    ax1.set_xticks(x)
    ax1.set_xticklabels(tier_names, fontsize=10)
    ax1.set_ylabel("Match Rate with Blind Judge (%)", fontsize=10)
    ax1.set_title("Who Agrees with the Judge?\nIS vs WER Thresholds by Tier", fontsize=12,
                  fontweight="bold")
    ax1.set_ylim(0, 110)
    ax1.legend(fontsize=9)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # ── Panel 2: Context shift by tier ────────────────────────────────
    ctx_rows = [r for r in rows if r["context"] in ["Y", "P", "N"]]
    judge_num = {"N": 0, "P": 1, "Y": 2}

    downgrades = []
    upgrades = []
    same = []
    for t in tiers:
        subset = [r for r in ctx_rows if r["tier"] == t]
        n = len(subset)
        d = sum(1 for r in subset if judge_num[r["context"]] < judge_num[r["blind"]])
        u = sum(1 for r in subset if judge_num[r["context"]] > judge_num[r["blind"]])
        s = n - d - u
        downgrades.append(100 * d / n)
        upgrades.append(100 * u / n)
        same.append(100 * s / n)

    ax2.bar(x, downgrades, 0.6, label="Downgraded", color="#d62728", alpha=0.8,
            edgecolor="white")
    ax2.bar(x, same, 0.6, bottom=downgrades, label="Same", color="#aaaaaa", alpha=0.6,
            edgecolor="white")
    ax2.bar(x, upgrades, 0.6,
            bottom=[d + s for d, s in zip(downgrades, same)],
            label="Upgraded", color="#2ca02c", alpha=0.8, edgecolor="white")

    for i in range(5):
        if downgrades[i] > 3:
            ax2.text(i, downgrades[i] / 2, f"{downgrades[i]:.0f}%",
                     ha="center", va="center", fontsize=9, color="white",
                     fontweight="bold")

    ax2.set_xticks(x)
    ax2.set_xticklabels(tier_names, fontsize=10)
    ax2.set_ylabel("% of Segments", fontsize=10)
    ax2.set_title("Context Strictness by Tier\n(Blind → Context transitions)", fontsize=12,
                  fontweight="bold")
    ax2.legend(fontsize=9, loc="lower right")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # ── Panel 3: Context shift signal profiles ────────────────────────
    transitions = {
        "Y→Y\n(stable)": [r for r in ctx_rows if r["blind"] == "Y" and r["context"] == "Y"],
        "Y→P\n(downgraded)": [r for r in ctx_rows if r["blind"] == "Y" and r["context"] == "P"],
        "P→P\n(stable)": [r for r in ctx_rows if r["blind"] == "P" and r["context"] == "P"],
        "P→N\n(downgraded)": [r for r in ctx_rows if r["blind"] == "P" and r["context"] == "N"],
    }
    trans_colors = {"Y→Y\n(stable)": "#2ca02c", "Y→P\n(downgraded)": "#ff7f0e",
                    "P→P\n(stable)": "#1f77b4", "P→N\n(downgraded)": "#d62728"}

    sig_short = ["semantic_sim", "phonetic_sim", "wer_norm", "nea_f1_norm"]
    sig_short_labels = ["Semantic", "Phonetic", "1−WER", "NEA F1"]
    x_sig = np.arange(len(sig_short))
    n_trans = len(transitions)
    w_t = 0.8 / n_trans

    for i, (label, subset) in enumerate(transitions.items()):
        vals = []
        for sk in sig_short:
            v_list = [r[sk] for r in subset if r.get(sk) is not None]
            vals.append(np.mean(v_list) if v_list else 0)
        offset = (i - n_trans / 2 + 0.5) * w_t
        bars = ax3.bar(x_sig + offset, vals, w_t * 0.9,
                       label=f"{label} (n={len(subset)})",
                       color=trans_colors[label], edgecolor="white", linewidth=0.8,
                       alpha=0.85)

    ax3.set_xticks(x_sig)
    ax3.set_xticklabels(sig_short_labels, fontsize=10)
    ax3.set_ylabel("Mean Signal Value", fontsize=10)
    ax3.set_title("Signal Profiles of Context Transitions\n(What predicts downgrade?)",
                  fontsize=12, fontweight="bold")
    ax3.set_ylim(0, 1.1)
    ax3.legend(fontsize=8, loc="upper left")
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)

    fig.tight_layout(w_pad=3)
    out_path = OUT_DIR / "P12_is_vs_wer_thresholds.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_wer_decile_analysis():
    """P13: WER decile analysis — signal profiles and judge agreement across WER range."""
    rows = load_full_judge_data()

    # Compute WER decile boundaries
    wer_vals = sorted([r["wer"] for r in rows if r["wer"] is not None])
    decile_edges = [np.percentile(wer_vals, p) for p in range(0, 101, 10)]

    sig_keys = ["semantic_sim", "phonetic_sim", "nea_f1_norm"]
    sig_labels = ["Semantic", "Phonetic", "NEA F1"]
    sig_colors = ["#1f77b4", "#ff7f0e", "#9467bd"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                     gridspec_kw={"height_ratios": [2, 1.5]})

    # ── Panel 1: Signal means by WER decile ──────────────────────────
    midpoints = []
    means_by_sig = {s: [] for s in sig_keys}
    is_means = []
    judge_y_pcts = []
    judge_n_pcts = []
    decile_labels = []

    for i in range(10):
        lo, hi = decile_edges[i], decile_edges[i + 1]
        subset = [r for r in rows if r["wer"] is not None and
                  lo <= r["wer"] < hi + (0.01 if i == 9 else 0)]
        if not subset:
            continue
        n = len(subset)
        mid = (lo + hi) / 2
        midpoints.append(mid)
        decile_labels.append(f"{lo:.0f}–{hi:.0f}%")

        for sk in sig_keys:
            vals = [r[sk] for r in subset if r.get(sk) is not None]
            means_by_sig[sk].append(np.mean(vals) if vals else 0)

        is_means.append(np.mean([r["is_score"] for r in subset]))
        judge_y_pcts.append(100 * sum(1 for r in subset if r["blind"] == "Y") / n)
        judge_n_pcts.append(100 * sum(1 for r in subset if r["blind"] == "N") / n)

    x = np.arange(len(midpoints))

    for sk, sl, sc in zip(sig_keys, sig_labels, sig_colors):
        ax1.plot(x, means_by_sig[sk], "o-", color=sc, linewidth=2, markersize=6,
                 label=sl)

    # IS mean on secondary axis
    ax1b = ax1.twinx()
    ax1b.plot(x, is_means, "s--", color="#888888", linewidth=1.5, markersize=5,
              label="IS mean", alpha=0.7)
    ax1b.set_ylabel("IS Mean", fontsize=10, color="#888888")
    ax1b.set_ylim(0, 5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(decile_labels, fontsize=8, rotation=30)
    ax1.set_ylabel("Mean Signal Value (0–1)", fontsize=10)
    ax1.set_title("Signal Values Across WER Deciles", fontsize=13, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.legend(fontsize=9, loc="upper right")
    ax1b.legend(fontsize=8, loc="center right")
    ax1.spines["top"].set_visible(False)

    # ── Panel 2: Judge Y% and N% by WER decile ──────────────────────
    ax2.bar(x - 0.2, judge_y_pcts, 0.35, label="Judge Y %", color="#2ca02c",
            edgecolor="white", alpha=0.85)
    ax2.bar(x + 0.2, judge_n_pcts, 0.35, label="Judge N %", color="#d62728",
            edgecolor="white", alpha=0.85)

    # Mark the WER=34% and WER=77% thresholds
    for thresh, label_txt in [(34, "WER NIV Y\n(≤34%)"), (77, "WER NIV Y+P\n(≤77%)")]:
        # Find nearest x position
        closest_x = min(range(len(midpoints)), key=lambda i: abs(midpoints[i] - thresh))
        ax2.axvline(x=closest_x, color="#888888", linewidth=1.5, linestyle="--", alpha=0.6)
        ax2.text(closest_x, 95, label_txt, ha="center", fontsize=8, color="#555555",
                 fontweight="bold")

    ax2.set_xticks(x)
    ax2.set_xticklabels(decile_labels, fontsize=8, rotation=30)
    ax2.set_ylabel("Judge Category %", fontsize=10)
    ax2.set_xlabel("WER Decile", fontsize=11)
    ax2.set_title("LLM Judge Agreement Across WER Range", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(h_pad=3)
    out_path = OUT_DIR / "P13_wer_decile_analysis.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_tier_chart()
    plot_judge_chart()
    plot_signal_trajectories()
    plot_niv_zones()
    plot_judge_tier_heatmaps()
    plot_is_vs_wer_thresholds()
    plot_wer_decile_analysis()
    print("Done.")
