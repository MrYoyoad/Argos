#!/usr/bin/env python3
"""
Exp A Fine-Tuning Analysis — 11 Diagnostic Plots

Parses the fairseq training log from finetune_A_r16 (LoRA r=16 on AVSpeech)
and generates plots covering loss curves, accuracy, overfitting, LR schedule,
gradient norms, perplexity, data distribution, a summary dashboard, and a
clean 2-panel summary comparing baseline vs fine-tuned configs.

Usage:
    python3 generate_finetune_plots.py

Output:
    docs/finetuning/plots/FT_*.png  (11 files)
"""

import json
import re
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

LOG_PATH = Path("/home/ubuntu/finetune_output_r16/training.log")
SPLIT_META_PATH = Path("/home/ubuntu/finetune_data/split_metadata.json")
EXP_CONFIG_PATH = Path("/home/ubuntu/docs/finetuning/experiments/finetune_A_r16/config.json")
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "finetuning" / "plots"

PLOT_DPI = 200
FIG_SIZE = (10, 6)
FIG_SIZE_WIDE = (12, 6)
FIG_SIZE_DASHBOARD = (16, 10)

# Colors
C_TRAIN = "#1f77b4"      # blue
C_VAL = "#d62728"         # red
C_LR = "#2ca02c"          # green
C_GNORM = "#ff7f0e"       # orange
C_PPL_TRAIN = "#2ca02c"   # green
C_PPL_VAL = "#9467bd"     # purple
C_TRAIN_BAR = "#1f77b4"   # blue
C_VAL_BAR = "#ff7f0e"     # orange
C_CKPT = "#d62728"        # red
C_BEST = "#FFD700"        # gold


# ════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════

def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_training_log(log_path):
    """Parse fairseq training log into three DataFrames + checkpoint events.

    Returns:
        train_df: epoch-end training summaries (19 rows)
        inner_df: per-50-update inner training metrics (60 rows)
        val_df:   validation results (~24 rows)
        checkpoints: list of dicts {name, num_updates}
    """
    train_rows = []
    inner_rows = []
    val_rows = []
    checkpoints = []

    re_train = re.compile(r"\[train\]\[INFO\] - (\{.*\})$")
    re_inner = re.compile(r"\[train_inner\]\[INFO\] - (\{.*\})$")
    re_test = re.compile(r"\[test\]\[INFO\] - (\{.*\})$")
    re_ckpt = re.compile(r"Saving checkpoint to checkpoints/(.*\.pt)")

    last_num_updates = 0

    with open(log_path) as f:
        for line in f:
            line = line.strip()

            m = re_ckpt.search(line)
            if m:
                checkpoints.append({
                    "name": m.group(1),
                    "num_updates": last_num_updates,
                })
                continue

            m = re_inner.search(line)
            if m:
                d = json.loads(m.group(1))
                row = {
                    "epoch": _safe_float(d.get("epoch")),
                    "num_updates": int(_safe_float(d.get("num_updates"))),
                    "loss": _safe_float(d.get("loss")),
                    "ppl": _safe_float(d.get("ppl")),
                    "accuracy": _safe_float(d.get("accuracy")),
                    "lr": _safe_float(d.get("lr")),
                    "gnorm": _safe_float(d.get("gnorm")),
                    "wall": _safe_float(d.get("wall")),
                }
                inner_rows.append(row)
                last_num_updates = row["num_updates"]
                continue

            m = re_train.search(line)
            if m:
                d = json.loads(m.group(1))
                row = {
                    "epoch": int(_safe_float(d.get("epoch"))),
                    "train_loss": _safe_float(d.get("train_loss")),
                    "train_ppl": _safe_float(d.get("train_ppl")),
                    "train_accuracy": _safe_float(d.get("train_accuracy")),
                    "train_lr": _safe_float(d.get("train_lr")),
                    "train_gnorm": _safe_float(d.get("train_gnorm")),
                    "train_num_updates": int(_safe_float(d.get("train_num_updates"))),
                    "train_wall": _safe_float(d.get("train_train_wall")),
                    "wall": _safe_float(d.get("train_wall")),
                }
                train_rows.append(row)
                last_num_updates = row["train_num_updates"]
                continue

            m = re_test.search(line)
            if m:
                d = json.loads(m.group(1))
                row = {
                    "epoch": int(_safe_float(d.get("epoch"))),
                    "test_loss": _safe_float(d.get("test_loss")),
                    "test_ppl": _safe_float(d.get("test_ppl")),
                    "test_accuracy": _safe_float(d.get("test_accuracy")),
                    "test_num_updates": int(_safe_float(d.get("test_num_updates"))),
                }
                val_rows.append(row)
                last_num_updates = row["test_num_updates"]
                continue

    return (
        pd.DataFrame(train_rows),
        pd.DataFrame(inner_rows),
        pd.DataFrame(val_rows),
        checkpoints,
    )


def load_split_metadata(meta_path):
    with open(meta_path) as f:
        return json.load(f)


def get_val_per_epoch(val_df):
    """Return last validation entry per epoch (deduplicates mid-epoch checkpoints)."""
    return val_df.groupby("epoch").last().reset_index()


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
# FT_01: Loss Curves (Train vs Val)
# ════════════════════════════════════════════════════════════

def plot_ft01_loss_curves(train_df, val_epoch_df):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.plot(train_df["epoch"], train_df["train_loss"],
            marker="o", color=C_TRAIN, linewidth=2, markersize=5, label="Train Loss")
    ax.plot(val_epoch_df["epoch"], val_epoch_df["test_loss"],
            marker="s", color=C_VAL, linewidth=2, markersize=5, label="Val Loss")

    # Best checkpoint star
    best_idx = val_epoch_df["test_loss"].idxmin()
    best_ep = val_epoch_df.loc[best_idx, "epoch"]
    best_loss = val_epoch_df.loc[best_idx, "test_loss"]
    ax.plot(best_ep, best_loss, marker="*", color=C_BEST, markersize=18, zorder=5,
            markeredgecolor="black", markeredgewidth=0.8, label=f"Best Checkpoint (epoch {best_ep})")

    # Overfitting zone shading
    ax.axvspan(best_ep + 0.5, 19.5, alpha=0.08, color="red", label="Overfitting Zone")
    ax.axvline(best_ep, color="gray", linestyle="--", alpha=0.5, linewidth=1)

    # Insight annotation
    final_val_loss = val_epoch_df["test_loss"].iloc[-1]
    pct_increase = (final_val_loss - best_loss) / best_loss * 100
    ax.text(0.98, 0.95, f"Val loss diverges after epoch {best_ep}\n"
            f"{best_loss:.3f} \u2192 {final_val_loss:.3f} (+{pct_increase:.0f}%)",
            transform=ax.transAxes, fontsize=9, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss (log\u2082)")
    ax.set_title("Exp A (LoRA r=16): Training vs Validation Loss")
    ax.legend(loc="center left")
    ax.set_xticks(range(1, 20))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    save_plot(fig, "FT_01_loss_curves.png")


# ════════════════════════════════════════════════════════════
# FT_02: Accuracy Curves (Train vs Val)
# ════════════════════════════════════════════════════════════

def plot_ft02_accuracy_curves(train_df, val_epoch_df):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.plot(train_df["epoch"], train_df["train_accuracy"],
            marker="o", color=C_TRAIN, linewidth=2, markersize=5, label="Train Accuracy")
    ax.plot(val_epoch_df["epoch"], val_epoch_df["test_accuracy"],
            marker="s", color=C_VAL, linewidth=2, markersize=5, label="Val Accuracy")

    # Fill between to show widening gap
    merged = pd.merge(train_df[["epoch", "train_accuracy"]],
                      val_epoch_df[["epoch", "test_accuracy"]], on="epoch")
    ax.fill_between(merged["epoch"], merged["test_accuracy"], merged["train_accuracy"],
                    alpha=0.12, color="red", label="Overfitting Gap")

    # Best checkpoint star
    best_idx = val_epoch_df["test_accuracy"].idxmax()
    best_ep = val_epoch_df.loc[best_idx, "epoch"]
    best_acc = val_epoch_df.loc[best_idx, "test_accuracy"]
    ax.plot(best_ep, best_acc, marker="*", color=C_BEST, markersize=18, zorder=5,
            markeredgecolor="black", markeredgewidth=0.8, label=f"Peak Val Acc ({best_acc:.2f}%)")

    # Horizontal reference
    ax.axhline(best_acc, color="gray", linestyle=":", alpha=0.4, linewidth=1)

    # Gap annotation
    final_train = train_df["train_accuracy"].iloc[-1]
    final_val = val_epoch_df["test_accuracy"].iloc[-1]
    early_gap = merged.iloc[1]["train_accuracy"] - merged.iloc[1]["test_accuracy"]
    final_gap = final_train - final_val
    ax.text(0.98, 0.5, f"Train\u2013Val Gap\n"
            f"Epoch 2: {early_gap:.1f} pp\n"
            f"Epoch 19: {final_gap:.1f} pp",
            transform=ax.transAxes, fontsize=9, va="center", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Exp A (LoRA r=16): Training vs Validation Accuracy")
    ax.legend(loc="center left")
    ax.set_xticks(range(1, 20))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    save_plot(fig, "FT_02_accuracy_curves.png")


# ════════════════════════════════════════════════════════════
# FT_03: Overfitting Gap Analysis (Dual Axis)
# ════════════════════════════════════════════════════════════

def plot_ft03_overfitting_gap(train_df, val_epoch_df):
    merged = pd.merge(train_df[["epoch", "train_accuracy", "train_loss"]],
                      val_epoch_df[["epoch", "test_accuracy", "test_loss"]], on="epoch")

    acc_gap = merged["train_accuracy"] - merged["test_accuracy"]
    loss_gap = merged["test_loss"] - merged["train_loss"]

    fig, ax1 = plt.subplots(figsize=FIG_SIZE)
    ax2 = ax1.twinx()

    ln1 = ax1.plot(merged["epoch"], acc_gap, marker="o", color=C_LR, linewidth=2,
                   markersize=5, label="Accuracy Gap (pp)")
    ln2 = ax2.plot(merged["epoch"], loss_gap, marker="s", color=C_GNORM, linewidth=2,
                   markersize=5, label="Loss Gap (val \u2212 train)")

    ax1.axhline(0, color="gray", linestyle="--", alpha=0.4)

    # Early stopping annotation
    ax1.annotate("Early stopping\npoint (epoch 2)",
                 xy=(2, acc_gap.iloc[1]), xytext=(5, acc_gap.iloc[1] + 5),
                 fontsize=9, color="gray", fontstyle="italic",
                 arrowprops=dict(arrowstyle="->", color="gray", lw=1.2))

    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Accuracy Gap (pp)", color=C_LR)
    ax2.set_ylabel("Loss Gap (val \u2212 train)", color=C_GNORM)
    ax1.tick_params(axis="y", labelcolor=C_LR)
    ax2.tick_params(axis="y", labelcolor=C_GNORM)

    # Combined legend
    lns = ln1 + ln2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper left")

    ax1.set_title("Overfitting Progression: Train\u2013Val Divergence")
    ax1.set_xticks(range(1, 20))
    ax1.spines["top"].set_visible(False)

    # Final values annotation
    ax1.text(0.98, 0.95, f"Final Acc Gap: {acc_gap.iloc[-1]:.1f} pp\n"
             f"Final Loss Gap: {loss_gap.iloc[-1]:.2f}",
             transform=ax1.transAxes, fontsize=9, va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    save_plot(fig, "FT_03_overfitting_gap.png")


# ════════════════════════════════════════════════════════════
# FT_04: Learning Rate Schedule
# ════════════════════════════════════════════════════════════

def plot_ft04_lr_schedule(inner_df):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.plot(inner_df["num_updates"], inner_df["lr"],
            color=C_LR, linewidth=2.5)

    # Phase boundaries and shading
    ax.axvspan(0, 600, alpha=0.08, color="green", label="Warmup (0\u2013600)")
    ax.axvspan(600, 3000, alpha=0.08, color="orange", label="Decay (600\u20133000)")
    ax.axvline(600, color="gray", linestyle="--", alpha=0.5, linewidth=1)

    # Peak LR label
    peak_lr = inner_df["lr"].max()
    peak_update = inner_df.loc[inner_df["lr"].idxmax(), "num_updates"]
    ax.annotate(f"Peak: {peak_lr:.2e}",
                xy=(peak_update, peak_lr), xytext=(peak_update + 300, peak_lr * 0.95),
                fontsize=9, color="black",
                arrowprops=dict(arrowstyle="->", color="gray", lw=1))

    # Config annotation
    ax.text(0.98, 0.5, "tri_stage schedule\n"
            "warmup=600, decay=2400\n"
            "init_scale=0.01\n"
            "final_scale=0.05\n"
            f"max_lr=3e-4",
            transform=ax.transAxes, fontsize=8, va="center", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc", alpha=0.9))

    ax.set_xlabel("Update Step")
    ax.set_ylabel("Learning Rate")
    ax.set_title("Tri-Stage Learning Rate Schedule")
    ax.legend(loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1e"))

    save_plot(fig, "FT_04_lr_schedule.png")


# ════════════════════════════════════════════════════════════
# FT_05: Gradient Norm Over Training
# ════════════════════════════════════════════════════════════

def plot_ft05_gradient_norm(inner_df, checkpoints):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    # Raw values as light scatter
    ax.scatter(inner_df["num_updates"], inner_df["gnorm"],
               color=C_GNORM, alpha=0.3, s=20, zorder=2)

    # Rolling average
    window = 5
    rolling = inner_df["gnorm"].rolling(window=window, center=True).mean()
    ax.plot(inner_df["num_updates"], rolling,
            color=C_GNORM, linewidth=2.5, label=f"Rolling Avg (w={window})", zorder=3)

    # Checkpoint markers
    ckpt_updates = [c["num_updates"] for c in checkpoints
                    if c["name"] not in ("checkpoint_last.pt",) and c["num_updates"] > 0]
    ckpt_updates = sorted(set(ckpt_updates))
    for u in ckpt_updates:
        ax.axvline(u, color="#cccccc", linestyle=":", alpha=0.5, linewidth=0.8)

    # Annotations
    peak_gnorm = inner_df["gnorm"].max()
    final_gnorm = inner_df["gnorm"].iloc[-1]
    ax.text(0.98, 0.95, f"Peak: {peak_gnorm:.2f}\n"
            f"Final: {final_gnorm:.2f}\n"
            f"Decrease: {(1 - final_gnorm/peak_gnorm)*100:.0f}%",
            transform=ax.transAxes, fontsize=9, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc", alpha=0.9))

    ax.set_xlabel("Update Step")
    ax.set_ylabel("Gradient L\u2082 Norm")
    ax.set_title("Gradient Norm During Training")
    ax.legend(loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    save_plot(fig, "FT_05_gradient_norm.png")


# ════════════════════════════════════════════════════════════
# FT_06: Perplexity Curves (Train vs Val, log scale)
# ════════════════════════════════════════════════════════════

def plot_ft06_perplexity(train_df, val_epoch_df):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.plot(train_df["epoch"], train_df["train_ppl"],
            marker="o", color=C_PPL_TRAIN, linewidth=2, markersize=5, label="Train PPL")
    ax.plot(val_epoch_df["epoch"], val_epoch_df["test_ppl"],
            marker="s", color=C_PPL_VAL, linewidth=2, markersize=5, label="Val PPL")

    ax.set_yscale("log")

    # Best checkpoint star
    best_idx = val_epoch_df["test_ppl"].idxmin()
    best_ep = val_epoch_df.loc[best_idx, "epoch"]
    best_ppl = val_epoch_df.loc[best_idx, "test_ppl"]
    ax.plot(best_ep, best_ppl, marker="*", color=C_BEST, markersize=18, zorder=5,
            markeredgecolor="black", markeredgewidth=0.8, label=f"Best Val PPL ({best_ppl:.2f})")

    # Annotations
    final_train_ppl = train_df["train_ppl"].iloc[-1]
    final_val_ppl = val_epoch_df["test_ppl"].iloc[-1]
    ax.text(0.98, 0.95, f"Train PPL: {train_df['train_ppl'].iloc[0]:.2f} \u2192 {final_train_ppl:.2f}\n"
            f"Val PPL:   {val_epoch_df['test_ppl'].iloc[0]:.2f} \u2192 {final_val_ppl:.2f}\n"
            f"Val PPL increase: {(final_val_ppl / best_ppl - 1)*100:.0f}%",
            transform=ax.transAxes, fontsize=9, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9))

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Perplexity (log scale)")
    ax.set_title("Training vs Validation Perplexity")
    ax.legend(loc="center left")
    ax.set_xticks(range(1, 20))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    save_plot(fig, "FT_06_perplexity.png")


# ════════════════════════════════════════════════════════════
# FT_07: Training Data Distribution by IS Tier
# ════════════════════════════════════════════════════════════

def plot_ft07_data_distribution(split_meta):
    tier_labels = {
        "1": "1: Failed\n(IS 0\u20130.99)",
        "2": "2: Poor\n(IS 1\u20131.99)",
        "3": "3: Fair\n(IS 2\u20132.99)",
        "4": "4: Good\n(IS 3\u20133.99)",
        "5": "5: Excellent\n(IS 4\u20135.0)",
    }
    tiers = sorted(split_meta["tier_distribution"].keys())
    train_counts = [split_meta["tier_distribution"][t]["train"] for t in tiers]
    val_counts = [split_meta["tier_distribution"][t]["val"] for t in tiers]
    labels = [tier_labels[t] for t in tiers]

    x = np.arange(len(tiers))
    width = 0.35

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    bars_train = ax.bar(x - width/2, train_counts, width, color=C_TRAIN_BAR,
                        label=f"Train (n={sum(train_counts)})", edgecolor="white")
    bars_val = ax.bar(x + width/2, val_counts, width, color=C_VAL_BAR,
                      label=f"Val (n={sum(val_counts)})", edgecolor="white")

    # Count labels
    for bar in bars_train:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar in bars_val:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xlabel("Intelligibility Score Tier")
    ax.set_ylabel("Number of Segments")
    ax.set_title("Training Data: IS Tier Distribution (Train vs Val)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Split info
    ax.text(0.02, 0.95, f"Stratified split: 85%/15%, seed=42\n"
            f"Total: {split_meta['total_segments']} segments",
            transform=ax.transAxes, fontsize=8, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#cccccc", alpha=0.9))

    save_plot(fig, "FT_07_data_distribution.png")


# ════════════════════════════════════════════════════════════
# FT_08: Granular Loss Curve with Checkpoints
# ════════════════════════════════════════════════════════════

def plot_ft08_granular_loss(inner_df, checkpoints):
    fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)

    ax.plot(inner_df["num_updates"], inner_df["loss"],
            color=C_TRAIN, linewidth=1.5, alpha=0.8, label="Training Loss (per 50 updates)")

    # LR warmup shading
    ax.axvspan(0, 600, alpha=0.06, color="green", label="LR Warmup Phase")

    # Checkpoint markers
    ckpt_updates = []
    for c in checkpoints:
        if c["name"] in ("checkpoint_last.pt",):
            continue
        if c["num_updates"] == 0:
            continue
        ckpt_updates.append(c)

    # Deduplicate by num_updates
    seen = set()
    unique_ckpts = []
    for c in ckpt_updates:
        if c["num_updates"] not in seen:
            seen.add(c["num_updates"])
            unique_ckpts.append(c)

    for c in unique_ckpts:
        u = c["num_updates"]
        # Find closest loss value
        closest_idx = (inner_df["num_updates"] - u).abs().idxmin()
        loss_val = inner_df.loc[closest_idx, "loss"]
        is_best = "best" in c["name"]
        marker = "*" if is_best else "D"
        color = C_BEST if is_best else C_CKPT
        size = 15 if is_best else 8
        ax.plot(u, loss_val, marker=marker, color=color, markersize=size,
                markeredgecolor="black", markeredgewidth=0.5, zorder=5)

    # Legend entries for checkpoints
    ax.plot([], [], marker="*", color=C_BEST, markersize=12, linestyle="None",
            markeredgecolor="black", label="Best Checkpoint")
    ax.plot([], [], marker="D", color=C_CKPT, markersize=7, linestyle="None",
            markeredgecolor="black", label="Interval Checkpoint")

    ax.set_xlabel("Update Step")
    ax.set_ylabel("Loss")
    ax.set_title("Training Loss (50-Update Granularity) with Checkpoint Saves")
    ax.legend(loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    save_plot(fig, "FT_08_granular_loss.png")


# ════════════════════════════════════════════════════════════
# FT_09: Wall-Clock Time Analysis
# ════════════════════════════════════════════════════════════

def plot_ft09_wall_clock(train_df):
    # Compute per-epoch time from cumulative wall clock
    wall_times = train_df["wall"].values
    per_epoch_sec = np.diff(wall_times, prepend=0)
    per_epoch_min = per_epoch_sec / 60.0

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    colors = [C_TRAIN_BAR] * len(train_df)
    # Last epoch is partial — different color
    colors[-1] = "#aec7e8"  # lighter blue

    bars = ax.bar(train_df["epoch"], per_epoch_min, color=colors, edgecolor="white", width=0.8)

    # Labels on bars
    for bar, mins in zip(bars, per_epoch_min):
        if mins > 5:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{mins:.0f}m", ha="center", va="bottom", fontsize=8)

    total_hrs = wall_times[-1] / 3600
    avg_min = np.mean(per_epoch_min[:-1])  # exclude partial last epoch

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Time (minutes)")
    ax.set_title("Per-Epoch Training Time")
    ax.set_xticks(range(1, 20))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(0.98, 0.95, f"Total: {total_hrs:.1f} hours\n"
            f"Avg: {avg_min:.0f} min/epoch\n"
            f"GPU: Tesla T4 (FP16)\n"
            f"Epoch 19: partial (120 updates)",
            transform=ax.transAxes, fontsize=8, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc", alpha=0.9))

    save_plot(fig, "FT_09_wall_clock.png")


# ════════════════════════════════════════════════════════════
# FT_10: Summary Dashboard (2x3 Multi-Panel)
# ════════════════════════════════════════════════════════════

def plot_ft10_summary_dashboard(train_df, val_epoch_df, inner_df, split_meta):
    fig, axes = plt.subplots(2, 3, figsize=FIG_SIZE_DASHBOARD)
    fig.suptitle("Exp A: LoRA r=16 Fine-Tuning Summary Dashboard", fontsize=16, fontweight="bold", y=0.98)

    merged = pd.merge(train_df[["epoch", "train_accuracy", "train_loss", "train_ppl"]],
                      val_epoch_df[["epoch", "test_accuracy", "test_loss", "test_ppl"]], on="epoch")

    # Panel 1: Loss curves
    ax = axes[0, 0]
    ax.plot(merged["epoch"], merged["train_loss"], marker=".", color=C_TRAIN, linewidth=1.5, markersize=4, label="Train")
    ax.plot(merged["epoch"], merged["test_loss"], marker=".", color=C_VAL, linewidth=1.5, markersize=4, label="Val")
    ax.set_title("Loss", fontsize=11)
    ax.set_xlabel("Epoch", fontsize=9)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 2: Accuracy curves
    ax = axes[0, 1]
    ax.plot(merged["epoch"], merged["train_accuracy"], marker=".", color=C_TRAIN, linewidth=1.5, markersize=4, label="Train")
    ax.plot(merged["epoch"], merged["test_accuracy"], marker=".", color=C_VAL, linewidth=1.5, markersize=4, label="Val")
    ax.fill_between(merged["epoch"], merged["test_accuracy"], merged["train_accuracy"], alpha=0.1, color="red")
    ax.set_title("Accuracy (%)", fontsize=11)
    ax.set_xlabel("Epoch", fontsize=9)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 3: LR schedule
    ax = axes[0, 2]
    ax.plot(inner_df["num_updates"], inner_df["lr"], color=C_LR, linewidth=1.5)
    ax.axvline(600, color="gray", linestyle="--", alpha=0.4, linewidth=0.8)
    ax.set_title("Learning Rate", fontsize=11)
    ax.set_xlabel("Update", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0e"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 4: Gradient norm
    ax = axes[1, 0]
    ax.plot(inner_df["num_updates"], inner_df["gnorm"], color=C_GNORM, linewidth=1, alpha=0.5)
    rolling = inner_df["gnorm"].rolling(window=5, center=True).mean()
    ax.plot(inner_df["num_updates"], rolling, color=C_GNORM, linewidth=2)
    ax.set_title("Gradient Norm", fontsize=11)
    ax.set_xlabel("Update", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 5: Perplexity
    ax = axes[1, 1]
    ax.plot(merged["epoch"], merged["train_ppl"], marker=".", color=C_PPL_TRAIN, linewidth=1.5, markersize=4, label="Train")
    ax.plot(merged["epoch"], merged["test_ppl"], marker=".", color=C_PPL_VAL, linewidth=1.5, markersize=4, label="Val")
    ax.set_yscale("log")
    ax.set_title("Perplexity (log)", fontsize=11)
    ax.set_xlabel("Epoch", fontsize=9)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 6: Summary metrics table
    ax = axes[1, 2]
    ax.axis("off")

    best_val_acc = val_epoch_df["test_accuracy"].max()
    best_ep = val_epoch_df.loc[val_epoch_df["test_accuracy"].idxmax(), "epoch"]
    final_val_acc = val_epoch_df["test_accuracy"].iloc[-1]
    final_train_acc = train_df["train_accuracy"].iloc[-1]
    gap = final_train_acc - final_val_acc
    total_hrs = train_df["wall"].iloc[-1] / 3600

    table_data = [
        ["Best Val Acc", f"{best_val_acc:.2f}% (epoch {best_ep})"],
        ["Final Val Acc", f"{final_val_acc:.2f}% (epoch 19)"],
        ["Final Train Acc", f"{final_train_acc:.2f}%"],
        ["Overfitting Gap", f"{gap:.1f} pp"],
        ["Total Time", f"{total_hrs:.1f} hours"],
        ["Updates", "3,000"],
        ["Trainable Params", "12.6M (0.19%)"],
        ["LoRA Config", "r=16, \u03b1=32"],
    ]

    table = ax.table(cellText=table_data, colLabels=["Metric", "Value"],
                     loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.6)

    # Style the table
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#4a86c8")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#f8f9fa" if row % 2 == 0 else "white")
        cell.set_edgecolor("#cccccc")

    ax.set_title("Key Metrics", fontsize=11)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save_plot(fig, "FT_10_summary_dashboard.png")


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def plot_FT_11_clean_summary(train_df=None, val_epoch_df=None):
    """Generate two separate presentation-ready plots (dark theme).

    FT_11a_loss.png  — Loss curves (train vs val, overfitting)
    FT_11b_impact.png — IS impact comparison bars
    Also generates the combined FT_11_clean_summary.png for backwards compat.
    """
    BG = "#0D1B2A"
    BG2 = "#122236"
    C_GREEN = "#56B870"
    C_CORAL = "#E06C75"
    C_TEAL = "#00B4D8"
    C_GOLD = "#FFD54F"
    C_WHITE = "#FFFFFF"
    C_LGRAY = "#8899AA"
    C_GRID = "#1E3450"

    def _style_ax(ax):
        ax.set_facecolor(BG2)
        ax.tick_params(colors=C_LGRAY, labelsize=13)
        for spine in ax.spines.values():
            spine.set_color(C_GRID)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.15, color=C_LGRAY, linewidth=0.5)

    # ── Load data ──
    if train_df is not None and val_epoch_df is not None:
        epochs_t = train_df["epoch"].values
        t_loss = train_df["train_loss"].values
        epochs_v = val_epoch_df["epoch"].values
        v_loss = val_epoch_df["test_loss"].values
        best_ep = val_epoch_df.loc[val_epoch_df["test_loss"].idxmin(), "epoch"]
        best_loss = val_epoch_df["test_loss"].min()
    else:
        epochs_t = np.arange(1, 20)
        t_loss = np.array([4.19, 2.22, 1.56, 1.17, 0.93, 0.77, 0.65, 0.56,
                           0.49, 0.44, 0.40, 0.36, 0.34, 0.31, 0.29, 0.28,
                           0.26, 0.25, 0.24])
        epochs_v = np.arange(1, 20)
        v_loss = np.array([3.48, 3.25, 3.30, 3.38, 3.46, 3.53, 3.59, 3.64,
                           3.68, 3.71, 3.74, 3.77, 3.79, 3.81, 3.83, 3.85,
                           3.86, 3.87, 3.88])
        best_ep = 2
        best_loss = 3.25

    # ════════════════════════════════════════════
    # PLOT A: Loss Curves
    # ════════════════════════════════════════════
    fig_a, ax = plt.subplots(figsize=(8, 5.5))
    fig_a.patch.set_facecolor(BG)
    _style_ax(ax)

    ax.plot(epochs_t, t_loss, "o-", color=C_TEAL, linewidth=2.5,
            markersize=7, label="Train Loss", zorder=4)
    ax.plot(epochs_v, v_loss, "s-", color=C_CORAL, linewidth=2.5,
            markersize=7, label="Val Loss", zorder=4)

    ax.axvspan(best_ep + 0.5, max(epochs_t) + 0.5, alpha=0.08,
               color=C_CORAL, zorder=1)
    ax.axvline(x=best_ep, color=C_GOLD, linestyle="--", linewidth=2,
               alpha=0.8, zorder=3)
    ax.plot(best_ep, best_loss, marker="*", color=C_GOLD, markersize=22,
            markeredgecolor=BG, markeredgewidth=1.2, zorder=5)
    ax.annotate(f"Best (epoch {best_ep})",
                xy=(best_ep, best_loss),
                xytext=(best_ep + 5.5, best_loss - 1.4),
                fontsize=13, fontweight="bold", color=C_GOLD,
                arrowprops=dict(arrowstyle="->", color=C_GOLD, lw=1.5),
                zorder=5)

    final_val = v_loss[-1]
    pct = (final_val - best_loss) / best_loss * 100
    ax.text(0.97, 0.72,
            f"Val: {best_loss:.2f} \u2192 {final_val:.2f} (+{pct:.0f}%)\n"
            f"Overfitting on 1,273 segments",
            transform=ax.transAxes, fontsize=12, va="top", ha="right",
            color=C_WHITE,
            bbox=dict(boxstyle="round,pad=0.5", facecolor=BG,
                      edgecolor=C_LGRAY, alpha=0.95))

    ax.set_xlabel("Epoch", fontsize=14, color=C_WHITE)
    ax.set_ylabel("Loss (log\u2082)", fontsize=14, color=C_WHITE)
    ax.set_title("LoRA r=16: Severe Overfitting After Epoch 2",
                 fontsize=16, fontweight="bold", color=C_WHITE, pad=10)
    ax.set_xticks([1, 5, 10, 15, 19])
    leg = ax.legend(fontsize=12, loc="center right",
                    framealpha=0.95, edgecolor=C_LGRAY)
    leg.get_frame().set_facecolor(BG)
    for t in leg.get_texts():
        t.set_color(C_WHITE)

    plt.tight_layout()
    out_a = OUTPUT_DIR / "FT_11a_loss.png"
    fig_a.savefig(out_a, dpi=PLOT_DPI, bbox_inches="tight", facecolor=BG)
    plt.close(fig_a)
    print(f"  Saved: FT_11a_loss.png")

    # ════════════════════════════════════════════
    # PLOT B: IS Impact Comparison
    # ════════════════════════════════════════════
    fig_b, ax = plt.subplots(figsize=(8, 5.5))
    fig_b.patch.set_facecolor(BG)
    _style_ax(ax)
    ax.grid(True, axis="x", alpha=0.15, color=C_LGRAY, linewidth=0.5)
    ax.grid(False, axis="y")

    configs = ["Baseline", "Exp A (r=16)", "Exp B (r=64)"]
    is_scores = [2.49, 2.31, 2.02]
    captured = [61.6, 55.9, 50.5]  # Useful % (IS >= 2.00, NIV Y+P)
    empty_pct = [7.1, 12.5, 26.8]

    y = np.arange(len(configs))
    bar_h = 0.25

    # Three metric groups: IS, Useful %, Empty %
    bars_is = ax.barh(y + bar_h, is_scores, bar_h, color=C_TEAL,
                      edgecolor="none", label="IS Score (/5.0)", zorder=3)
    cap_scaled = [c / 20 for c in captured]
    bars_cap = ax.barh(y, cap_scaled, bar_h, color=C_GREEN,
                       edgecolor="none", label="Useful % (\u00f720)", zorder=3)
    empty_scaled = [e / 20 for e in empty_pct]
    bars_emp = ax.barh(y - bar_h, empty_scaled, bar_h, color=C_CORAL,
                       edgecolor="none", label="Empty % (\u00f720)", zorder=3)

    for bar, val in zip(bars_is, is_scores):
        ax.text(bar.get_width() + 0.06, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", ha="left", va="center", fontsize=14,
                fontweight="bold", color=C_TEAL)
    for bar, val in zip(bars_cap, captured):
        ax.text(bar.get_width() + 0.06, bar.get_y() + bar.get_height() / 2,
                f"{val}%", ha="left", va="center", fontsize=14,
                fontweight="bold", color=C_GREEN)
    for bar, val in zip(bars_emp, empty_pct):
        ax.text(bar.get_width() + 0.06, bar.get_y() + bar.get_height() / 2,
                f"{val}%", ha="left", va="center", fontsize=14,
                fontweight="bold", color=C_CORAL)

    ax.axvline(x=is_scores[0], color=C_TEAL, linestyle=":", linewidth=1.5,
               alpha=0.4, zorder=2)

    ax.set_yticks(y)
    ax.set_yticklabels(configs, fontsize=15, color=C_WHITE, fontweight="bold")
    ax.set_xlabel("Score", fontsize=14, color=C_WHITE)
    ax.set_xlim(0, 3.2)
    ax.set_title("Fine-Tuning Made Everything Worse",
                 fontsize=16, fontweight="bold", color=C_WHITE, pad=10)
    ax.invert_yaxis()

    leg = ax.legend(fontsize=11, loc="lower left",
                    framealpha=0.95, edgecolor=C_LGRAY)
    leg.get_frame().set_facecolor(BG)
    for t in leg.get_texts():
        t.set_color(C_WHITE)

    plt.tight_layout()
    out_b = OUTPUT_DIR / "FT_11b_impact.png"
    fig_b.savefig(out_b, dpi=PLOT_DPI, bbox_inches="tight", facecolor=BG)
    plt.close(fig_b)
    print(f"  Saved: FT_11b_impact.png")


def main():
    print("=" * 60)
    print("Exp A Fine-Tuning Plot Generator")
    print("=" * 60)

    print("\nLoading training log...")
    train_df, inner_df, val_df, checkpoints = parse_training_log(LOG_PATH)
    split_meta = load_split_metadata(SPLIT_META_PATH)
    val_epoch_df = get_val_per_epoch(val_df)

    setup_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nData summary:")
    print(f"  Train epochs:    {len(train_df)}")
    print(f"  Inner updates:   {len(inner_df)}")
    print(f"  Val entries:     {len(val_df)} ({len(val_epoch_df)} unique epochs)")
    print(f"  Checkpoints:     {len(checkpoints)}")
    print(f"  Best val acc:    {val_epoch_df['test_accuracy'].max():.3f}% (epoch {val_epoch_df.loc[val_epoch_df['test_accuracy'].idxmax(), 'epoch']})")
    print(f"  Final val acc:   {val_epoch_df['test_accuracy'].iloc[-1]:.3f}%")
    print(f"  Final train acc: {train_df['train_accuracy'].iloc[-1]:.3f}%")

    print(f"\nGenerating 11 plots to {OUTPUT_DIR}/")
    print("-" * 40)

    plot_ft01_loss_curves(train_df, val_epoch_df)
    plot_ft02_accuracy_curves(train_df, val_epoch_df)
    plot_ft03_overfitting_gap(train_df, val_epoch_df)
    plot_ft04_lr_schedule(inner_df)
    plot_ft05_gradient_norm(inner_df, checkpoints)
    plot_ft06_perplexity(train_df, val_epoch_df)
    plot_ft07_data_distribution(split_meta)
    plot_ft08_granular_loss(inner_df, checkpoints)
    plot_ft09_wall_clock(train_df)
    plot_ft10_summary_dashboard(train_df, val_epoch_df, inner_df, split_meta)
    plot_FT_11_clean_summary(train_df, val_epoch_df)
    # Note: FT_11_clean_summary.png no longer generated — replaced by
    # FT_11a_loss.png and FT_11b_impact.png for better slide readability

    print("-" * 40)
    pngs = sorted(OUTPUT_DIR.glob("FT_*.png"))
    print(f"\nDone! {len(pngs)} plots saved to {OUTPUT_DIR}/")
    for p in pngs:
        print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
