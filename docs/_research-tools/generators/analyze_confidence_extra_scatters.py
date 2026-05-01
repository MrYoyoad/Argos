#!/usr/bin/env python3
"""Extra confidence scatter plots — beyond the single mean_prob × mean_entropy view.

Produces four plots (saved to presentation_materials_20260224/01_plots_for_slides/):

  1. conf_hallucination_pairs_scatter.png
        2x2 of alternative confidence-metric pairs, colored by hallucinated label.
        (Same hallucinated overlay style as conf_hallucination_scatter.png.)
  2. conf_metrics_vs_is_scatter.png
        Top confidence metrics vs continuous IS score, with linear fit.
  3. conf_metrics_vs_wer_scatter.png
        Top confidence metrics vs continuous WER%, with linear fit.
  4. conf_sweet_spot_pr.png
        Threshold sweep for confidence-only filter gates: precision (mean IS of kept
        segments, NIV-Y rate of kept) vs recall (% volume kept). Marks the elbow
        threshold where adding strictness stops paying for itself.

Reuses the data loading and feature frame from analyze_confidence_full.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

GEN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN_DIR))
from analyze_confidence_full import (  # noqa: E402
    BG, NAVY2, TEAL, GREEN, GOLD, CORAL, ORANGE, PURPLE, WHITE, MGRAY, LGRAY,
    Segment, build_frame, features_dataframe, _style_ax, _save, REPO_ROOT,
)

PLOTS_DIR = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides"


# ─────────────────────────────────────────────────────────────────────────────
# Plot 1 — Hallucination scatter for alternative metric pairs
# ─────────────────────────────────────────────────────────────────────────────

def _hall_panel(ax, sub: pd.DataFrame, x: str, y: str,
                xlabel: str, ylabel: str,
                vline: Tuple[float, str] = None,
                hline: Tuple[float, str] = None) -> None:
    """One scatter panel: x vs y, healthy (teal) under, hallucinated (coral) over."""
    _style_ax(ax)
    ok = sub[sub.hallucinated == 0]
    bad = sub[sub.hallucinated == 1]
    ax.scatter(ok[x], ok[y], c=TEAL, s=10, alpha=0.40, edgecolor="none",
               label=f"Healthy  n={len(ok)}")
    ax.scatter(bad[x], bad[y], c=CORAL, s=20, alpha=0.85,
               edgecolor="white", linewidth=0.4,
               label=f"Hallucinated  n={len(bad)}")
    if vline is not None:
        ax.axvline(vline[0], color=GREEN, linestyle=":", linewidth=1.4,
                   alpha=0.7, label=vline[1])
    if hline is not None:
        ax.axhline(hline[0], color=GOLD, linestyle=":", linewidth=1.4,
                   alpha=0.7, label=hline[1])
    ax.set_xlabel(xlabel, color=WHITE, fontsize=11)
    ax.set_ylabel(ylabel, color=WHITE, fontsize=11)
    ax.legend(loc="best", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=8)


def plot_hallucination_pairs(df: pd.DataFrame) -> Dict[str, Any]:
    """2x2 of alternative metric pairs, colored by hallucinated."""
    sub = df.dropna(subset=["wer", "len_ratio", "mean_prob"]).copy()
    sub["hallucinated"] = ((sub["wer"] >= 100) & (sub["len_ratio"] >= 0.5)).astype(int)
    n_hall = int(sub["hallucinated"].sum())

    fig, axs = plt.subplots(2, 2, figsize=(15, 11), dpi=200)
    fig.patch.set_facecolor(BG)

    # Panel A: mean_margin × min_word_prob
    s_a = sub.dropna(subset=["mean_margin", "min_word_prob"])
    _hall_panel(axs[0, 0], s_a, "mean_margin", "min_word_prob",
                "mean_margin (top1 - top2)", "min_word_prob",
                vline=(0.5, "margin >= 0.5"),
                hline=(0.4, "min_wp >= 0.4"))
    axs[0, 0].set_title("Margin × min-word-prob",
                        color=WHITE, fontsize=12, fontweight="bold", pad=8)

    # Panel B: frac_p_lt_04 × frac_p_ge_085 (red-token vs green-token fraction)
    s_b = sub.dropna(subset=["frac_p_lt_04", "frac_p_ge_085"])
    _hall_panel(axs[0, 1], s_b, "frac_p_lt_04", "frac_p_ge_085",
                "frac tokens p < 0.40 (red)", "frac tokens p >= 0.85 (green)",
                vline=(0.20, "red-frac <= 0.20"),
                hline=(0.50, "green-frac >= 0.50"))
    axs[0, 1].set_title("Red-token frac × green-token frac",
                        color=WHITE, fontsize=12, fontweight="bold", pad=8)

    # Panel C: mean_word_prob × mean_entropy
    s_c = sub.dropna(subset=["mean_word_prob", "mean_entropy"])
    _hall_panel(axs[1, 0], s_c, "mean_word_prob", "mean_entropy",
                "mean_word_prob (word-level max-softmax)",
                "mean_entropy (token-level)",
                vline=(0.85, "green band p >= 0.85"))
    axs[1, 0].set_title("Word-prob × entropy",
                        color=WHITE, fontsize=12, fontweight="bold", pad=8)

    # Panel D: p_std × mean_prob (variance vs mean)
    s_d = sub.dropna(subset=["p_std", "mean_prob"])
    _hall_panel(axs[1, 1], s_d, "mean_prob", "p_std",
                "mean_prob", "std of token probs (within segment)",
                vline=(0.85, "green band p >= 0.85"))
    axs[1, 1].set_title("Mean × std of token probs",
                        color=WHITE, fontsize=12, fontweight="bold", pad=8)

    fig.suptitle(
        f"Hallucination scatters — alternative confidence pairs  "
        f"(hallucinated n={n_hall} of {len(sub)})",
        color=WHITE, fontsize=14, fontweight="bold", y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, PLOTS_DIR / "conf_hallucination_pairs_scatter.png")
    return {"n_hallucinated": n_hall, "n_total": len(sub)}


# ─────────────────────────────────────────────────────────────────────────────
# Plot 2/3 — Continuous scatters: confidence metric vs IS / WER
# ─────────────────────────────────────────────────────────────────────────────

def _cont_panel(ax, sub: pd.DataFrame, x: str, y: str,
                xlabel: str, ylabel: str, ylim=None) -> Tuple[float, float]:
    _style_ax(ax)
    ax.scatter(sub[x], sub[y], c=TEAL, s=10, alpha=0.40, edgecolor="none")
    # OLS line + R^2
    if len(sub) >= 30:
        slope, intercept, r, p, _ = stats.linregress(sub[x], sub[y])
        xs = np.linspace(sub[x].min(), sub[x].max(), 100)
        ax.plot(xs, slope * xs + intercept, color=GOLD, linewidth=1.8,
                alpha=0.85, label=f"OLS  r={r:+.3f}  R²={r**2:.2f}")
        ax.legend(loc="best", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)
    else:
        r = float("nan")
    ax.set_xlabel(xlabel, color=WHITE, fontsize=11)
    ax.set_ylabel(ylabel, color=WHITE, fontsize=11)
    if ylim is not None:
        ax.set_ylim(*ylim)
    return r, len(sub)


def plot_metrics_vs_target(df: pd.DataFrame, target: str,
                           target_label: str, ylim, fname: str) -> Dict[str, float]:
    """2x2 of confidence metrics vs continuous target (IS or WER)."""
    feats = [
        ("mean_prob",      "mean_prob (max-softmax)"),
        ("mean_entropy",   "mean_entropy"),
        ("mean_margin",    "mean_margin (top1 - top2)"),
        ("min_word_prob",  "min_word_prob"),
    ]
    fig, axs = plt.subplots(2, 2, figsize=(15, 11), dpi=200)
    fig.patch.set_facecolor(BG)
    out: Dict[str, float] = {}
    for ax, (key, label) in zip(axs.flat, feats):
        sub = df.dropna(subset=[key, target])[[key, target]]
        r, n = _cont_panel(ax, sub, key, target, label, target_label, ylim=ylim)
        ax.set_title(f"{label} vs {target_label}",
                     color=WHITE, fontsize=12, fontweight="bold", pad=8)
        out[key] = r
    fig.suptitle(
        f"Confidence metrics vs {target_label} (per-segment, n={len(df.dropna(subset=[target]))})",
        color=WHITE, fontsize=14, fontweight="bold", y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, PLOTS_DIR / fname)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Plot 4 — Sweet-spot precision-recall sweep
# ─────────────────────────────────────────────────────────────────────────────

def sweet_spot_sweep(df: pd.DataFrame) -> Dict[str, Any]:
    """For each confidence metric, sweep the gate threshold and trace:
       - recall (volume kept / total)
       - precision (NIV-Y rate of kept segments)
       - mean IS of kept segments

    The 'sweet spot' is the threshold where the precision-recall product
    (Youden-style F-score over kept/dropped) is maximized — i.e. you keep
    most of the good stuff while excluding most of the bad stuff.
    """
    df = df.copy()
    df["niv_y"] = (df["is_score"] >= 3.80).astype(int)

    df_full = df.dropna(subset=["is_score"])  # need targets

    # Configurations: (feature, direction)  direction='ge' means gate keeps x >= T
    cfgs = [
        ("mean_prob",      "ge", "mean_prob >= T",      np.linspace(0.20, 0.95, 76)),
        ("mean_word_prob", "ge", "mean_word_prob >= T", np.linspace(0.20, 0.95, 76)),
        ("min_word_prob",  "ge", "min_word_prob >= T",  np.linspace(0.05, 0.85, 81)),
        ("mean_entropy",   "le", "mean_entropy <= T",   np.linspace(0.20, 4.00, 76)),
        ("mean_margin",    "ge", "mean_margin >= T",    np.linspace(0.05, 0.95, 91)),
        ("frac_p_ge_085",  "ge", "frac_green >= T",     np.linspace(0.00, 0.90, 91)),
    ]

    sweeps: Dict[str, pd.DataFrame] = {}
    sweet: Dict[str, Dict[str, float]] = {}
    n_total = len(df_full)
    n_pos_total = int(df_full["niv_y"].sum())  # NIV-Y count

    for feat, direction, label, grid in cfgs:
        if feat not in df_full.columns:
            continue
        sub = df_full.dropna(subset=[feat])
        rows = []
        for T in grid:
            mask = (sub[feat] >= T) if direction == "ge" else (sub[feat] <= T)
            kept = sub[mask]
            if len(kept) == 0:
                continue
            recall_vol = len(kept) / n_total
            niv_y_rate = float(kept["niv_y"].mean())
            mean_is = float(kept["is_score"].mean())
            mean_wer = float(kept["wer"].mean()) if "wer" in kept else float("nan")
            # Recall over NIV-Y (sensitivity for "good" class)
            recall_y = float(kept["niv_y"].sum()) / max(1, n_pos_total)
            # F1 over the NIV-Y class at this gate
            tp = float(kept["niv_y"].sum())
            fp = len(kept) - tp
            fn = n_pos_total - tp
            prec = tp / max(1, (tp + fp))
            rec = tp / max(1, (tp + fn))
            f1 = 2 * prec * rec / max(1e-9, (prec + rec))
            rows.append({
                "T": T, "recall_vol": recall_vol, "niv_y_rate": niv_y_rate,
                "mean_is": mean_is, "mean_wer": mean_wer,
                "recall_y": recall_y, "precision_y": prec, "f1_y": f1,
                "n_kept": len(kept),
            })
        sweep_df = pd.DataFrame(rows)
        sweeps[feat] = sweep_df
        # Sweet spot = max F1 over NIV-Y class (precision × recall trade-off)
        if len(sweep_df) > 0:
            best = sweep_df.loc[sweep_df["f1_y"].idxmax()]
            sweet[feat] = {
                "label": label,
                "T": float(best["T"]),
                "f1": float(best["f1_y"]),
                "precision": float(best["precision_y"]),
                "recall_y": float(best["recall_y"]),
                "recall_vol": float(best["recall_vol"]),
                "mean_is_kept": float(best["mean_is"]),
                "mean_wer_kept": float(best["mean_wer"]),
                "n_kept": int(best["n_kept"]),
            }

    # Plot: 2x3 panels — one per metric — precision (NIV-Y rate of kept) vs recall_vol
    fig, axs = plt.subplots(2, 3, figsize=(18, 11), dpi=200)
    fig.patch.set_facecolor(BG)

    panel_feats = [feat for feat, *_ in cfgs if feat in sweeps]
    for ax, feat in zip(axs.flat, panel_feats):
        s = sweeps[feat]
        if len(s) == 0:
            ax.axis("off")
            continue
        _style_ax(ax)
        # X axis = recall over NIV-Y (sensitivity)
        # Left Y = precision  (NIV-Y rate of kept)
        # Right Y = mean IS of kept
        ax.plot(s["recall_y"], s["precision_y"], color=TEAL, linewidth=2.0,
                label="Precision (NIV-Y of kept)")
        ax.plot(s["recall_y"], s["niv_y_rate"], color=PURPLE, linewidth=1.0,
                alpha=0.4)  # same as precision; included for visual sanity
        # Mark the F1-max sweet spot
        sw = sweet.get(feat)
        if sw:
            best_row = s.loc[s["f1_y"].idxmax()]
            ax.scatter([best_row["recall_y"]], [best_row["precision_y"]],
                       s=130, facecolor="none", edgecolor=GOLD, linewidth=2.2,
                       label=f"sweet spot  T={sw['T']:.2f}  F1={sw['f1']:.2f}", zorder=5)
            ax.annotate(
                f"keep {best_row['n_kept']:.0f}/{n_total} "
                f"({best_row['recall_vol']*100:.0f}% vol)\n"
                f"IS_kept={best_row['mean_is']:.2f}, WER_kept={best_row['mean_wer']:.0f}%",
                xy=(best_row["recall_y"], best_row["precision_y"]),
                xytext=(8, -36), textcoords="offset points",
                fontsize=8.5, color=WHITE,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=NAVY2,
                          edgecolor=GOLD, alpha=0.95),
            )

        # Reference line: NIV-Y base rate (no gate) — anything above this beats random
        base_rate = n_pos_total / n_total
        ax.axhline(base_rate, color=LGRAY, linestyle=":", linewidth=1.2,
                   alpha=0.65, label=f"base rate {base_rate*100:.1f}%")

        ax.set_xlabel("Recall over NIV-Y (% of good kept)",
                      color=WHITE, fontsize=10)
        ax.set_ylabel("Precision = NIV-Y rate of kept",
                      color=WHITE, fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        title = next(c[2] for c in cfgs if c[0] == feat)
        ax.set_title(title, color=WHITE, fontsize=11, fontweight="bold", pad=8)
        ax.legend(loc="lower left", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=8)

    fig.suptitle(
        "Filter-gate sweet spot — precision × recall over NIV-Y\n"
        f"(n={n_total} segments, NIV-Y base rate {n_pos_total}/{n_total}="
        f"{n_pos_total/n_total*100:.1f}%; sweet spot = F1-max threshold)",
        color=WHITE, fontsize=14, fontweight="bold", y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, PLOTS_DIR / "conf_sweet_spot_pr.png")

    # Print summary table
    print("\n══ Sweet-spot summary ══")
    print(f"  Total segments: {n_total}")
    print(f"  NIV-Y (good) base rate: {n_pos_total} ({n_pos_total/n_total*100:.1f}%)")
    print()
    print(f"  {'Feature':<18s} {'Gate':<22s} {'T':>6s} {'F1':>5s}  {'Prec':>5s} "
          f"{'Recall_Y':>9s} {'Vol':>5s}  {'IS_kept':>7s}  {'WER_kept':>8s}  {'n_kept':>7s}")
    print("  " + "-" * 110)
    for feat in panel_feats:
        sw = sweet[feat]
        print(f"  {feat:<18s} {sw['label']:<22s} {sw['T']:>6.2f} "
              f"{sw['f1']:>5.2f}  {sw['precision']:>5.2f} "
              f"{sw['recall_y']*100:>8.1f}% {sw['recall_vol']*100:>4.0f}%  "
              f"{sw['mean_is_kept']:>7.2f}  {sw['mean_wer_kept']:>7.1f}%  "
              f"{sw['n_kept']:>7d}")

    return {"sweeps": {k: v.to_dict('list') for k, v in sweeps.items()}, "sweet_spots": sweet}


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--confidence-sidecar", type=Path,
                   default=Path("/tmp/vsp_b3_1497_out/confidence-172610.json"))
    p.add_argument("--hypo", type=Path,
                   default=Path("/tmp/vsp_b3_1497_out/hypo-172610.json"))
    p.add_argument("--baseline-csv", type=Path,
                   default=REPO_ROOT / "english_full_results" / "client_outputs" / "report" / "report.csv")
    args = p.parse_args()

    print("Loading data...")
    segs, _diag = build_frame(args.confidence_sidecar, args.hypo, args.baseline_csv)
    df = features_dataframe(segs)
    print(f"Feature frame: {len(df)} rows, {df.shape[1]} cols")

    print("\n[1/4] Hallucination pair scatters...")
    hall_info = plot_hallucination_pairs(df)

    print("\n[2/4] Confidence vs IS scatters...")
    is_corrs = plot_metrics_vs_target(
        df, target="is_score", target_label="Intelligibility Score (IS)",
        ylim=(0, 5), fname="conf_metrics_vs_is_scatter.png",
    )

    print("\n[3/4] Confidence vs WER scatters...")
    wer_corrs = plot_metrics_vs_target(
        df, target="wer", target_label="WER (%)",
        ylim=(0, 200), fname="conf_metrics_vs_wer_scatter.png",
    )

    print("\n[4/4] Sweet-spot precision-recall sweep...")
    sweet = sweet_spot_sweep(df)

    print("\nDone.")
    print("Pearson r vs IS:", {k: round(v, 3) for k, v in is_corrs.items()})
    print("Pearson r vs WER:", {k: round(v, 3) for k, v in wer_corrs.items()})


if __name__ == "__main__":
    main()
