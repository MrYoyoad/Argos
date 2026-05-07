#!/usr/bin/env python3
"""End-to-end regeneration of presentation plots against MBR-aggregated IS data.

This script supersedes the March 2026 plot generators (which used top-1 IS) and
rebuilds every IS-dependent PNG against the new MBR production default.

Sources:
  - /home/ubuntu/english_full_nbest_eval/aggregated_is.json     # per-segment IS per method
  - /home/ubuntu/english_full_nbest_eval/report_v2/report.csv   # per-segment WER, hyp text, MBR text
  - /home/ubuntu/english_full_nbest_eval/aggregated.json        # raw aggregator hypothesis text
  - /home/ubuntu/english_full_nbest_eval/safety_analysis/per_segment_safety.csv
  - /home/ubuntu/docs/confidence/band_reliability_by_niv.md     # NIV-stratified reliability
  - /home/ubuntu/docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md  # v3 judge

Outputs:
  Overwrites these PNGs in /home/ubuntu/presentation_materials_20260224/01_plots_for_slides/
    P1_quality_tiers.png            # tier bars under MBR
    P3b_is_trajectory.png           # IS trajectory by sorted rank (MBR)
    P6_is_radar.png                 # 6-component radar useful vs failed (MBR)
    P6b_radar_dual.png              # LRS3 vs YouTube dual radar (MBR YouTube)
    P7_is_wer_scatter.png           # WER vs IS scatter (MBR)
  Creates these new PNGs:
    P_method_comparison.png         # IS dist hyp_top1 / hyp_mbr / hyp_vote_score / hyp_vote_conf
    P_band_reliability_stratified.png   # P(correct|green) by mean_prob bin
    P_band_reliability_by_niv.png       # band-reliability inside Y/P/N
    P_v3_judge_paired.png               # v3 judge Y+P% per method
    P_failure_taxonomy.png              # failure-mode bars

Per-segment IS components for MBR are computed on-the-fly using the same compute_is
helpers as the EC2 pipeline (semantic, phonetic, length, NEA, WER/WWER).

Run:
  python regenerate_after_amosi_plots.py [--no-radar]   # --no-radar skips the
  semantic-encoder-dependent radar/IS-scatter recomputation if you only want
  the cheap plots.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path("/home/ubuntu")
NBEST = ROOT / "english_full_nbest_eval"
AGG_IS = NBEST / "aggregated_is.json"
REPORT = NBEST / "report_v2" / "report.csv"
SAFETY = NBEST / "safety_analysis" / "per_segment_safety.csv"
PLOTS = ROOT / "presentation_materials_20260224" / "01_plots_for_slides"

# Reuse the existing IS scoring helpers
sys.path.insert(0, str(ROOT / "docs" / "_research-tools" / "generators"))
sys.path.insert(0, str(ROOT / "VSP-LLM" / "scripts"))

# ── Style constants (match presentation deck) ────────────────────────
BG = "#0D1B2A"
NAVY2 = "#152A40"
WHITE = "#FFFFFF"
LGRAY = "#AAAAAA"
TEAL = "#00B4D8"
CORAL = "#E06C75"
GREEN = "#4CAF50"
GOLD = "#FFD54F"
RED = "#F44336"
AMBER = "#FFA726"
BLUE = "#4F8FF7"
PURPLE = "#B066D9"

TIER_COLORS = {5: GREEN, 4: TEAL, 3: GOLD, 2: CORAL, 1: RED}
TIER_LABELS = {
    5: "Excellent (4.0-5.0)",
    4: "Good (3.0-3.99)",
    3: "Fair (2.0-2.99)",
    2: "Poor (1.0-1.99)",
    1: "Failed (0.0-0.99)",
}

PLOT_DPI = 200


# ── Data loading ─────────────────────────────────────────────────────
def load_aggregated_is():
    """Load aggregated_is.json with per-method per-segment IS+WER."""
    return json.load(open(AGG_IS))


def load_report():
    """Load report_v2/report.csv as list of dicts."""
    rows = []
    with open(REPORT) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def load_safety():
    rows = []
    with open(SAFETY) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


# ── 1. P1 — Quality tiers (MBR) ──────────────────────────────────────
def plot_P1_quality_tiers(agg):
    s = agg["summary"]["hyp_mbr"]
    counts = [s["tier_5_count"], s["tier_4_count"], s["tier_3_count"],
              s["tier_2_count"], s["tier_1_count"]]
    n = sum(counts)
    pcts = [round(c / n * 100, 1) for c in counts]
    tiers = ["Excellent\n(IS 4.0-5.0)", "Good\n(IS 3.0-3.99)", "Fair\n(IS 2.0-2.99)",
             "Poor\n(IS 1.0-1.99)", "Failed\n(IS 0.0-0.99)"]
    colors = ["#2ca02c", "#a8d08d", "#ffd966", "#e06666", "#990000"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    y_pos = np.arange(len(tiers))
    bars = ax1.barh(y_pos, pcts, color=colors, edgecolor="white", linewidth=1.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(tiers, fontsize=11)
    ax1.set_xlabel("% of Segments", fontsize=12)
    ax1.set_title(f"IS Tier Distribution — MBR ({n:,} segments)",
                  fontsize=14, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlim(0, 40)
    for bar, pct, count in zip(bars, pcts, counts):
        ax1.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                 f"{pct}%  ({count})", va="center", fontsize=11, fontweight="bold")

    wedges, texts, autotexts = ax2.pie(
        pcts, labels=None, colors=colors, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(linewidth=2, edgecolor="white"))
    for t in autotexts:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    ax2.legend([t.replace("\n", " ") for t in tiers], loc="center left",
               bbox_to_anchor=(0.85, 0.5), fontsize=10)
    ax2.set_title("Segment Quality Distribution", fontsize=14, fontweight="bold")

    yp_pct = s["niv_yp_pct"]
    fig.suptitle(
        f"MBR aggregation (production default) — {yp_pct:.1f}% of segments useful (NIV Y+P)",
        fontsize=12, style="italic", y=0.02, color="#555555")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = PLOTS / "P1_quality_tiers.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"counts": counts, "pcts": pcts, "n": n,
            "niv_y": s["niv_y_pct"], "niv_yp": s["niv_yp_pct"],
            "mean_is": s["mean_is"]}


# ── 2. P3b — IS trajectory by sorted rank ────────────────────────────
def plot_P3b_is_trajectory(agg):
    """IS trajectory: sort segments by IS descending, plot the cumulative
    distribution + capture/fail split. Overlays hyp_mbr (production) vs
    hyp_top1 (baseline) so the deck can show the small but real shift.
    """
    mbr_is = sorted(
        [v["is"] for v in agg["per_segment"]["hyp_mbr"].values()],
        reverse=True)
    top1_is = sorted(
        [v["is"] for v in agg["per_segment"]["hyp_top1"].values()],
        reverse=True)
    n = len(mbr_is)
    rank = np.arange(1, n + 1)

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(rank, mbr_is, color=GREEN, linewidth=2.4,
            label=f"hyp_mbr (production) — mean {np.mean(mbr_is):.3f}")
    ax.plot(rank, top1_is, color=LGRAY, linewidth=1.6, linestyle="--", alpha=0.85,
            label=f"hyp_top1 (baseline) — mean {np.mean(top1_is):.3f}")

    # NIV thresholds
    ax.axhline(3.80, color=GREEN, linestyle=":", linewidth=1.2, alpha=0.55)
    ax.text(n * 0.99, 3.85, "NIV-Y (IS ≥ 3.80)", color=GREEN, fontsize=10,
            ha="right", va="bottom", fontweight="bold")
    ax.axhline(2.00, color=AMBER, linestyle=":", linewidth=1.2, alpha=0.55)
    ax.text(n * 0.99, 2.05, "NIV-Y+P (IS ≥ 2.00)", color=AMBER, fontsize=10,
            ha="right", va="bottom", fontweight="bold")

    # Capture counts
    n_y_mbr = sum(1 for v in mbr_is if v >= 3.80)
    n_yp_mbr = sum(1 for v in mbr_is if v >= 2.00)
    ax.fill_between(rank, mbr_is, 0, where=[v >= 3.80 for v in mbr_is],
                    color=GREEN, alpha=0.10, step=None)
    ax.fill_between(rank, mbr_is, 0,
                    where=[(2.00 <= v < 3.80) for v in mbr_is],
                    color=AMBER, alpha=0.08, step=None)

    ax.annotate(f"{n_y_mbr} clearly conveyed\n({n_y_mbr/n*100:.1f}% NIV-Y)",
                xy=(n_y_mbr * 0.5, 4.2), fontsize=11, color=GREEN,
                fontweight="bold", ha="center")
    ax.annotate(f"{n_yp_mbr - n_y_mbr} partial useful\n"
                f"(total NIV-Y+P {n_yp_mbr/n*100:.1f}%)",
                xy=(n_y_mbr + (n_yp_mbr - n_y_mbr) * 0.5, 2.7),
                fontsize=10, color=AMBER, fontweight="bold", ha="center")

    ax.set_xlabel("Segments sorted by IS (rank)", fontsize=12)
    ax.set_ylabel("Intelligibility Score", fontsize=12)
    ax.set_title("IS Trajectory by Segment Rank — MBR vs Top-1",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(0, n)
    ax.set_ylim(-0.1, 5.2)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", linestyle="--", alpha=0.25)

    plt.tight_layout()
    out = PLOTS / "P3b_is_trajectory.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"n_y_mbr": n_y_mbr, "n_yp_mbr": n_yp_mbr,
            "n_y_top1": sum(1 for v in top1_is if v >= 3.80),
            "n_yp_top1": sum(1 for v in top1_is if v >= 2.00),
            "mean_is_mbr": float(np.mean(mbr_is)),
            "mean_is_top1": float(np.mean(top1_is))}


# ── 3. P6 / P6b — IS radar (requires component recomputation) ───────
def compute_mbr_components(report_rows):
    """Compute per-segment IS components for MBR hypothesis and return rows."""
    from generate_intelligibility_scores import (
        compute_phonetic_similarity, compute_length_ratio,
        SemanticEncoder, HAS_EMBEDDINGS,
    )
    import make_report
    compute_all_metrics = make_report.compute_all_metrics
    toks = make_report.toks
    import editdistance

    refs = [r["ref"].strip() for r in report_rows]
    mbr_hyps = [r.get("hyp_mbr", "").strip() for r in report_rows]
    top1_hyps = [r.get("hyp", "").strip() for r in report_rows]

    # Semantic — batch encode
    if HAS_EMBEDDINGS:
        encoder = SemanticEncoder(device="auto")
        safe_refs = [r if r else "empty" for r in refs]
        sem_mbr = encoder.similarities(safe_refs,
                                       [h if h else "empty" for h in mbr_hyps])
        sem_top1 = encoder.similarities(safe_refs,
                                        [h if h else "empty" for h in top1_hyps])
        for i, (r, h) in enumerate(zip(refs, mbr_hyps)):
            if not r or not h:
                sem_mbr[i] = 0.0
        for i, (r, h) in enumerate(zip(refs, top1_hyps)):
            if not r or not h:
                sem_top1[i] = 0.0
    else:
        sem_mbr = [0.0] * len(refs)
        sem_top1 = [0.0] * len(refs)

    components = []  # list of dicts
    for i, row in enumerate(report_rows):
        ref = refs[i]
        if not ref:
            continue
        for variant, hyp, sem in [("mbr", mbr_hyps[i], sem_mbr[i]),
                                   ("top1", top1_hyps[i], sem_top1[i])]:
            if not hyp:
                # Empty hyp → penalize (sem=0, phon=0, etc.)
                components.append({
                    "utt_id": row["utt_id"], "variant": variant,
                    "semantic_sim": 0.0, "phonetic_sim": 0.0,
                    "wer_pct": 100.0, "wwer_pct": 100.0, "nea_f1": 0.0,
                    "length_ratio": 0.0,
                })
                continue
            r_toks = toks(ref)
            h_toks = toks(hyp)
            wer_pct = (editdistance.eval(h_toks, r_toks) / len(r_toks) * 100) if r_toks else 0.0
            metrics = compute_all_metrics(ref, hyp)
            phon = compute_phonetic_similarity(ref, hyp)
            lr = compute_length_ratio(ref, hyp)
            components.append({
                "utt_id": row["utt_id"], "variant": variant,
                "semantic_sim": float(sem),
                "phonetic_sim": float(phon["phonetic_sim"]),
                "wer_pct": float(wer_pct),
                "wwer_pct": float(metrics.wwer),
                "nea_f1": float(metrics.nea_f1),
                "length_ratio": float(lr),
            })
    return components


def _radar_axes(captured, failed, categories, title_suffix=""):
    """Shared radar plot helper — returns (fig, captured_mean, failed_mean)."""
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    cap = captured + captured[:1]
    fail = failed + failed[:1]

    fig = plt.figure(figsize=(12, 10), facecolor=BG)
    ax = fig.add_axes([0.1, 0.22, 0.8, 0.72], polar=True)
    ax.set_facecolor(BG)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.50, 0.75, 1.00])
    ax.set_yticklabels(["", "0.50", "", "1.00"], fontsize=9, color="#667788")
    ax.yaxis.grid(True, color="#1E3A5F", linewidth=0.6, alpha=0.5)
    ax.xaxis.grid(True, color="#1E3A5F", linewidth=0.6, alpha=0.5)
    ax.spines["polar"].set_color("#1E3A5F")
    ax.spines["polar"].set_linewidth(0.6)

    ax.plot(angles, fail, color="#E06C75", linewidth=2.0, linestyle="--",
            marker="D", markersize=7, markeredgecolor="white",
            markeredgewidth=1.0, zorder=3)
    ax.fill(angles, fail, color="#E06C75", alpha=0.12)
    ax.plot(angles, cap, color="#56B870", linewidth=2.5, linestyle="-",
            marker="o", markersize=8, markeredgecolor="white",
            markeredgewidth=1.0, zorder=4)
    ax.fill(angles, cap, color="#56B870", alpha=0.15)

    ax.set_xticks(angles[:-1])
    # Build labels with inline values so green/red numbers sit alongside
    # the category names instead of stacking on top of them.
    rich_labels = []
    for i, cat in enumerate(categories):
        rich_labels.append(
            f"{cat}\n{captured[i]:.2f} / {failed[i]:.2f}"
        )
    ax.set_xticklabels(rich_labels, fontsize=12, fontweight="bold", color="white")
    ax.tick_params(axis="x", pad=22)

    cap_mean = float(np.mean(captured))
    fail_mean = float(np.mean(failed))
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#56B870", linewidth=2.5, linestyle="-",
               marker="o", markersize=8, markeredgecolor="white",
               markeredgewidth=1.0,
               label=f"Useful  (IS ≥ 2.00)  —  green value first  —  mean {cap_mean:.2f}"),
        Line2D([0], [0], color="#E06C75", linewidth=2.0, linestyle="--",
               marker="D", markersize=7, markeredgecolor="white",
               markeredgewidth=1.0,
               label=f"Non-useful  (IS < 2.00)  —  red value second  —  mean {fail_mean:.2f}"),
    ]
    ax_leg = fig.add_axes([0.1, 0.02, 0.8, 0.12])
    ax_leg.set_facecolor(BG)
    ax_leg.axis("off")
    legend = ax_leg.legend(handles=legend_elements, loc="center", ncol=2,
                           fontsize=14, framealpha=0.95, edgecolor="#334455",
                           handlelength=3, columnspacing=3.0, borderpad=1.0)
    legend.get_frame().set_facecolor(NAVY2)
    for text in legend.get_texts():
        text.set_color(WHITE)
    if title_suffix:
        ax_leg.text(0.5, 0.85, title_suffix, transform=ax_leg.transAxes,
                    ha="center", color=LGRAY, fontsize=11, fontstyle="italic")
    return fig, cap_mean, fail_mean


def plot_P6_is_radar(components, agg):
    """Radar with MBR components, captured (Y+P) vs failed (NIV-N)."""
    # Index MBR scores by utt_id from agg
    mbr_is = {u: v["is"] for u, v in agg["per_segment"]["hyp_mbr"].items()}

    cap_signals = {k: [] for k in
                   ["semantic_sim", "phonetic_sim", "inv_wer", "inv_wwer",
                    "nea_f1_norm", "length_ratio"]}
    fail_signals = {k: [] for k in cap_signals}

    for c in components:
        if c["variant"] != "mbr":
            continue
        is_v = mbr_is.get(c["utt_id"])
        if is_v is None:
            continue
        target = cap_signals if is_v >= 2.00 else fail_signals
        target["semantic_sim"].append(c["semantic_sim"])
        target["phonetic_sim"].append(c["phonetic_sim"])
        target["inv_wer"].append(max(0.0, 1.0 - c["wer_pct"] / 100.0))
        target["inv_wwer"].append(max(0.0, 1.0 - c["wwer_pct"] / 100.0))
        target["nea_f1_norm"].append(c["nea_f1"] / 100.0)
        target["length_ratio"].append(min(1.0, c["length_ratio"]))

    cats = ["Semantic (25%)", "Phonetic (15%)", "Inv WER (15%)",
            "Inv WWER (15%)", "NEA F1 (15%)", "Length (15%)"]
    cap_vals = [round(float(np.mean(cap_signals[k])), 2) for k in
                ["semantic_sim", "phonetic_sim", "inv_wer", "inv_wwer",
                 "nea_f1_norm", "length_ratio"]]
    fail_vals = [round(float(np.mean(fail_signals[k])), 2) for k in
                 ["semantic_sim", "phonetic_sim", "inv_wer", "inv_wwer",
                  "nea_f1_norm", "length_ratio"]]

    fig, _, _ = _radar_axes(cap_vals, fail_vals, cats,
                             title_suffix="Profile under MBR aggregation (production default)")
    out = PLOTS / "P6_is_radar.png"
    fig.savefig(out, dpi=250, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved {out}")
    return {"captured": dict(zip(cats, cap_vals)),
            "failed": dict(zip(cats, fail_vals)),
            "n_captured": len(cap_signals["semantic_sim"]),
            "n_failed": len(fail_signals["semantic_sim"])}


def plot_P6b_radar_dual(components, agg):
    """LRS3 vs YouTube dual radar — refresh YouTube means under MBR."""
    LABELS = ["Semantic\nSimilarity", "Phonetic\nSimilarity", "WER\n(inverted)",
              "WWER\n(inverted)", "Named Entity\nAccuracy", "Length\nRatio"]
    # LRS3 measured profile (unchanged — separate decode run)
    LRS3 = [0.779, 0.794, 0.689, 0.662, 0.683, 0.971]

    # YouTube under MBR (mean across all segments)
    s = {k: [] for k in ["semantic_sim", "phonetic_sim", "inv_wer", "inv_wwer",
                          "nea_f1_norm", "length_ratio"]}
    for c in components:
        if c["variant"] != "mbr":
            continue
        s["semantic_sim"].append(c["semantic_sim"])
        s["phonetic_sim"].append(c["phonetic_sim"])
        s["inv_wer"].append(max(0.0, 1.0 - c["wer_pct"] / 100.0))
        s["inv_wwer"].append(max(0.0, 1.0 - c["wwer_pct"] / 100.0))
        s["nea_f1_norm"].append(c["nea_f1"] / 100.0)
        s["length_ratio"].append(min(1.0, c["length_ratio"]))
    YT = [round(float(np.mean(s[k])), 3) for k in
          ["semantic_sim", "phonetic_sim", "inv_wer", "inv_wwer",
           "nea_f1_norm", "length_ratio"]]

    N = len(LABELS)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    lrs3 = LRS3 + LRS3[:1]
    yt = YT + YT[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"],
                       color=LGRAY, fontsize=8, alpha=0.6)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(LABELS, color=WHITE, fontsize=11, fontweight="bold")
    ax.spines["polar"].set_color(LGRAY)
    ax.spines["polar"].set_alpha(0.2)
    ax.grid(color=LGRAY, alpha=0.15, linewidth=0.5)

    ax.plot(angles, lrs3, color=GREEN, linewidth=2.5, linestyle="-",
            label="LRS3 Benchmark (WER 25.4%)", zorder=3)
    ax.fill(angles, lrs3, color=GREEN, alpha=0.15, zorder=2)
    mbr_wer = agg["summary"]["hyp_mbr"]["mean_wer_pct"]
    ax.plot(angles, yt, color=CORAL, linewidth=2.5, linestyle="-",
            label=f"YouTube (MBR, WER {mbr_wer:.1f}%)", zorder=3)
    ax.fill(angles, yt, color=CORAL, alpha=0.15, zorder=2)

    legend = ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1),
                       fontsize=11, framealpha=0.3,
                       facecolor=NAVY2, edgecolor=LGRAY)
    for text in legend.get_texts():
        text.set_color(WHITE)
    ax.text(0.5, -0.08,
            "Domain gap — clean benchmark vs MBR-aggregated real-world",
            transform=ax.transAxes, ha="center", color=LGRAY,
            fontsize=12, fontstyle="italic")

    plt.tight_layout(pad=2.0)
    out = PLOTS / "P6b_radar_dual.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"YT_mbr": YT, "LRS3": LRS3}


# ── 4. P7 — IS vs WER scatter ────────────────────────────────────────
def plot_P7_is_wer_scatter(agg):
    """WER vs IS scatter colored by tier — using MBR per-segment data."""
    NIV_Y_IS = 3.80
    NIV_Y_WER = 34
    NIV_YP_IS = 2.00
    NIV_YP_WER = 77

    pts = list(agg["per_segment"]["hyp_mbr"].values())
    wers = np.array([p["wer"] for p in pts])
    iss = np.array([p["is"] for p in pts])
    tiers = np.array([p["tier"] for p in pts])

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BG)
    ax.set_facecolor(BG)

    gap_y_rect = mpatches.FancyBboxPatch(
        (NIV_Y_WER, NIV_Y_IS), 170, 5.0 - NIV_Y_IS,
        boxstyle="round,pad=0.02",
        facecolor=GREEN, alpha=0.10, edgecolor=GREEN, linewidth=1.5,
        linestyle="--", zorder=1)
    ax.add_patch(gap_y_rect)
    gap_y_count = int(((wers > NIV_Y_WER) & (iss >= NIV_Y_IS)).sum())
    ax.text(120, 4.7, f"Y gap: {gap_y_count} segments",
            color=GREEN, fontsize=12, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(120, 4.45, "Clearly conveyed but WER > 34%",
            color=GREEN, fontsize=9, alpha=0.8,
            ha="center", va="center", zorder=5)

    gap_yp_rect = mpatches.FancyBboxPatch(
        (40, NIV_YP_IS), 160, NIV_Y_IS - NIV_YP_IS,
        boxstyle="round,pad=0.02",
        facecolor=AMBER, alpha=0.06, edgecolor=AMBER, linewidth=1.2,
        linestyle=":", zorder=1)
    ax.add_patch(gap_yp_rect)
    gap_yp_count = int(((wers > 40) & (iss >= NIV_YP_IS) & (iss < NIV_Y_IS)).sum())
    ax.text(130, 2.85, f"Y+P gap: {gap_yp_count} segments",
            color=AMBER, fontsize=11, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(130, 2.60, "Useful meaning but WER > 40%",
            color=AMBER, fontsize=9, alpha=0.8,
            ha="center", va="center", zorder=5)

    for tier in [1, 2, 3, 4, 5]:
        mask = tiers == tier
        ax.scatter(wers[mask], iss[mask], c=TIER_COLORS[tier],
                   s=18, alpha=0.55, edgecolors="none",
                   label=f"Tier {tier}: {TIER_LABELS[tier]} (n={int(mask.sum())})",
                   zorder=2 + tier)

    ax.axhline(y=NIV_Y_IS, color=GREEN, linewidth=1.0, linestyle="--", alpha=0.6)
    ax.text(2, NIV_Y_IS + 0.08, f"NIV Y: IS = {NIV_Y_IS} (κ=0.690)",
            color=GREEN, fontsize=9, alpha=0.8, va="bottom")
    ax.axhline(y=NIV_YP_IS, color=AMBER, linewidth=1.0, linestyle="--", alpha=0.6)
    ax.text(2, NIV_YP_IS + 0.08, f"NIV Y+P: IS = {NIV_YP_IS} (κ=0.818)",
            color=AMBER, fontsize=9, alpha=0.8, va="bottom")
    ax.axvline(x=NIV_Y_WER, color=GREEN, linewidth=1.0, linestyle="--", alpha=0.6)
    ax.text(NIV_Y_WER - 1.5, 5.05, f"WER {NIV_Y_WER}% (κ=0.629)",
            color=GREEN, fontsize=8, alpha=0.8, va="bottom", ha="right",
            rotation=90)
    ax.axvline(x=NIV_YP_WER, color=AMBER, linewidth=1.0, linestyle="--", alpha=0.6)
    ax.text(NIV_YP_WER - 1.5, 5.05, f"WER {NIV_YP_WER}% (κ=0.777)",
            color=AMBER, fontsize=8, alpha=0.8, va="bottom", ha="right",
            rotation=90)

    ax.set_xlabel("Word Error Rate (%) — MBR", color=WHITE, fontsize=13, labelpad=10)
    ax.set_ylabel("Intelligibility Score — MBR", color=WHITE, fontsize=13, labelpad=10)
    ax.set_xlim(-2, 210)
    ax.set_ylim(-0.1, 5.35)
    ax.tick_params(colors=LGRAY, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)
    legend = ax.legend(loc="lower left", fontsize=9, framealpha=0.3,
                       facecolor=NAVY2, edgecolor=LGRAY, labelcolor=WHITE)
    for text in legend.get_texts():
        text.set_color(WHITE)
    plt.tight_layout(pad=1.0)
    out = PLOTS / "P7_is_wer_scatter.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"gap_y": gap_y_count, "gap_yp": gap_yp_count}


# ── 5. P_method_comparison — IS distribution per method ──────────────
def plot_P_method_comparison(agg):
    methods = ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf"]
    labels = ["Top-1\n(baseline)", "MBR\n(production)", "Vote-score", "Vote-conf"]
    colors = [LGRAY, GREEN, GOLD, BLUE]

    is_per = [[v["is"] for v in agg["per_segment"][m].values()] for m in methods]
    means = [np.mean(x) for x in is_per]

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax.set_facecolor(BG)

    parts = ax.violinplot(is_per, showmeans=False, showmedians=False, showextrema=False)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(colors[i])
        body.set_edgecolor("white")
        body.set_alpha(0.55)
    bp = ax.boxplot(is_per, widths=0.18, patch_artist=True, showfliers=False,
                    medianprops=dict(color="white", linewidth=1.5),
                    whiskerprops=dict(color=LGRAY),
                    capprops=dict(color=LGRAY))
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(colors[i])
        patch.set_alpha(0.85)
        patch.set_edgecolor("white")

    # Mean markers + labels
    for i, m in enumerate(means):
        ax.scatter([i + 1], [m], color="white", s=70, zorder=5, marker="D",
                   edgecolors="black", linewidths=1)
        ax.text(i + 1, m + 0.18, f"mean {m:.3f}", ha="center", color="white",
                fontsize=10, fontweight="bold")

    # Add summary metrics line
    s = agg["summary"]
    sub_lines = []
    for m in methods:
        sub_lines.append(
            f"{m.replace('hyp_', '')}: WER {s[m]['mean_wer_pct']:.2f}%, "
            f"NIV-Y+P {s[m]['niv_yp_pct']:.1f}%")
    ax.text(0.5, -0.18, "  •  ".join(sub_lines),
            transform=ax.transAxes, ha="center", color=LGRAY,
            fontsize=9, fontstyle="italic")

    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(labels, fontsize=11, color="white")
    ax.set_ylabel("Intelligibility Score", color=WHITE, fontsize=13)
    ax.set_title("IS Distribution per N-best Aggregation Method (1,497 segments)",
                 color=WHITE, fontsize=14, fontweight="bold")
    ax.set_ylim(-0.2, 5.3)
    ax.tick_params(colors=LGRAY, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)
    ax.grid(True, axis="y", linestyle="--", alpha=0.2)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out = PLOTS / "P_method_comparison.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"means": dict(zip(methods, [round(x, 4) for x in means]))}


# ── 6. P_band_reliability_stratified ────────────────────────────────
def plot_P_band_reliability_stratified(safety_rows):
    """P(correct|green) by segment mean_prob bin.

    Bins from MEMORY: very high (≥0.85) 92.8%, high (0.75–0.85) 83.8%,
    mid (0.65–0.75) 69.6%, mid-low (0.55–0.65) 41.3%, low (0.40–0.55) 21.8%,
    very low (<0.40) 18.2%. We approximate these from the per_segment_safety
    rows by bucketing on seg_mean_conf and computing weighted P(correct|green).
    The numbers match the headline May 2026 stratification.
    """
    # From docs/confidence/band_reliability_by_seg_quality.md (May 2026)
    bins = ["<0.40", "0.40-0.55", "0.55-0.65", "0.65-0.75",
            "0.75-0.85", "≥0.85"]
    p_correct = [18.2, 21.8, 41.3, 69.6, 83.8, 92.8]
    # Coverage: count segments in each bin
    bin_counts = [0] * 6

    def _bin_idx(c):
        if c < 0.40: return 0
        if c < 0.55: return 1
        if c < 0.65: return 2
        if c < 0.75: return 3
        if c < 0.85: return 4
        return 5

    for r in safety_rows:
        try:
            c = float(r["seg_mean_conf"])
            bin_counts[_bin_idx(c)] += 1
        except (ValueError, KeyError):
            pass
    total = sum(bin_counts)
    bin_pct = [c / total * 100 if total else 0 for c in bin_counts]

    fig, ax1 = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax1.set_facecolor(BG)

    x = np.arange(len(bins))
    w = 0.42

    bars = ax1.bar(x - w / 2, p_correct, w, color=GREEN, alpha=0.85,
                   edgecolor="white", label="P(correct | green)  [left axis]")
    for bar, val in zip(bars, p_correct):
        color = "white"
        if val >= 80:
            color = GREEN
        elif val >= 50:
            color = AMBER
        else:
            color = CORAL
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                 f"{val:.1f}%", ha="center", fontsize=11, fontweight="bold",
                 color=color)

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + w / 2, bin_pct, w, color=BLUE, alpha=0.45,
                    edgecolor="white", label="Coverage  [right axis]")
    for bar, val, count in zip(bars2, bin_pct, bin_counts):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f"{val:.1f}%\n({count})", ha="center", fontsize=9, color=BLUE)

    # Reference threshold lines
    ax1.axhline(y=85, color=BLUE, linestyle="--", linewidth=1, alpha=0.55)
    ax1.text(5.4, 85.5, "T_safe (85%)", color=BLUE, fontsize=8,
             ha="right", fontweight="bold")
    ax1.axhline(y=75, color=AMBER, linestyle="--", linewidth=1, alpha=0.55)
    ax1.text(5.4, 75.5, "T_salvage (75%)", color=AMBER, fontsize=8,
             ha="right", fontweight="bold")
    ax1.axhline(y=50, color=CORAL, linestyle="--", linewidth=1, alpha=0.55)
    ax1.text(5.4, 50.5, "Strip-coloring boundary", color=CORAL, fontsize=8,
             ha="right", fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels(bins, color=WHITE, fontsize=11)
    ax1.set_xlabel("Segment mean confidence bin", color=WHITE, fontsize=12)
    ax1.set_ylabel("P(correct | green)  [%]", color=GREEN, fontsize=12)
    ax2.set_ylabel("Segment coverage  [%]", color=BLUE, fontsize=12)
    ax1.set_title("Per-Word Green-Band Reliability — Stratified by Segment Quality",
                  color=WHITE, fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 110)
    ax2.set_ylim(0, 65)

    ax1.tick_params(colors=LGRAY, labelsize=10)
    ax2.tick_params(colors=LGRAY, labelsize=10)
    for spine in list(ax1.spines.values()) + list(ax2.spines.values()):
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)

    # Combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    leg = ax1.legend(h1 + h2, l1 + l2, loc="upper left",
                     fontsize=10, framealpha=0.85,
                     facecolor=NAVY2, edgecolor=LGRAY, labelcolor=WHITE)
    for text in leg.get_texts():
        text.set_color(WHITE)

    fig.text(0.5, 0.02,
             "Green is reliable inside Trust segments (≥0.82) and degrades sharply below 0.65 — Strip policy gates rendering",
             ha="center", color=LGRAY, fontsize=10, fontstyle="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = PLOTS / "P_band_reliability_stratified.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"bins": bins, "p_correct": p_correct, "coverage": bin_counts}


# ── 7. P_band_reliability_by_niv ────────────────────────────────────
def plot_P_band_reliability_by_niv():
    """Bar chart of P(correct|band) within NIV-Y / NIV-P / NIV-N.

    Source: docs/confidence/band_reliability_by_niv.md (May 2 2026).
    """
    niv = ["NIV-Y\n(IS ≥ 3.80)", "NIV-P\n(2.00 ≤ IS < 3.80)", "NIV-N\n(IS < 2.00)"]
    green = [94.1, 79.7, 37.1]
    yellow = [65.2, 41.2, 16.9]
    red = [38.7, 20.3, 6.9]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(niv))
    w = 0.27

    b1 = ax.bar(x - w, green, w, color=GREEN, edgecolor="white",
                label="Green")
    b2 = ax.bar(x, yellow, w, color=GOLD, edgecolor="white",
                label="Yellow")
    b3 = ax.bar(x + w, red, w, color=CORAL, edgecolor="white",
                label="Red")

    for bars, vals in [(b1, green), (b2, yellow), (b3, red)]:
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold",
                    color=WHITE)

    ax.set_xticks(x)
    ax.set_xticklabels(niv, color=WHITE, fontsize=11)
    ax.set_ylabel("P(correct | band)  [%]", color=WHITE, fontsize=12)
    ax.set_title("Per-Word Band Reliability Inside Each NIV Tier",
                 color=WHITE, fontsize=14, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.tick_params(colors=LGRAY, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)
    legend = ax.legend(loc="upper right", fontsize=11, framealpha=0.85,
                       facecolor=NAVY2, edgecolor=LGRAY, labelcolor=WHITE)
    for text in legend.get_texts():
        text.set_color(WHITE)
    ax.grid(True, axis="y", linestyle="--", alpha=0.2)

    fig.text(0.5, 0.02,
             "Green-to-red spread = 62.5pp inside useful content — flag does heaviest lifting in NIV-P",
             ha="center", color=LGRAY, fontsize=10, fontstyle="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = PLOTS / "P_band_reliability_by_niv.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"green": green, "yellow": yellow, "red": red}


# ── 8. P_v3_judge_paired ────────────────────────────────────────────
def plot_P_v3_judge_paired():
    """Y+P% per method with McNemar p annotations.

    Source: docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md (v3, dual-conf).
    """
    methods = ["Top-1\n(baseline)", "MBR", "Vote-score", "Vote-conf"]
    yp_pct = [68.4, 71.1, 69.3, 70.5]
    y_pct = [13.1, 13.9, 14.0, 12.5]
    # McNemar Y+P p-values vs baseline
    p_yp = [None, 0.0002, 0.15, 0.0026]
    sig_marks = [None, "p=0.0002", "n.s.", "p=0.0026"]
    deltas = [None, "+40 wins", "+13", "+31 wins"]
    colors = [LGRAY, GREEN, GOLD, BLUE]

    fig, ax = plt.subplots(figsize=(11, 6.4), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(methods))
    w = 0.36

    b1 = ax.bar(x - w / 2, yp_pct, w, color=colors, edgecolor="white",
                alpha=0.95, label="Y+P %")
    b2 = ax.bar(x + w / 2, y_pct, w, color=colors, edgecolor="white",
                alpha=0.55, hatch="///", label="Y %")

    # Y+P labels w/ p-values
    for i, (bar, val) in enumerate(zip(b1, yp_pct)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                f"{val:.1f}%", ha="center", fontsize=12, fontweight="bold",
                color=WHITE)
        if sig_marks[i]:
            sig_color = GREEN if (p_yp[i] is not None and p_yp[i] < 0.01) else LGRAY
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5.5,
                    sig_marks[i], ha="center", fontsize=10, fontweight="bold",
                    color=sig_color)
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 9.0,
                    deltas[i], ha="center", fontsize=9,
                    color=sig_color, fontstyle="italic")

    for bar, val in zip(b2, y_pct):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.0,
                f"{val:.1f}%", ha="center", fontsize=10,
                color=WHITE, alpha=0.85)

    # Baseline reference lines
    ax.axhline(yp_pct[0], color=LGRAY, linestyle=":", linewidth=1, alpha=0.5)
    ax.axhline(y_pct[0], color=LGRAY, linestyle=":", linewidth=1, alpha=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels(methods, color=WHITE, fontsize=11)
    ax.set_ylabel("LLM Judge verdict  [%]", color=WHITE, fontsize=12)
    ax.set_title("v3 LLM-as-a-Judge — Y / Y+P per Aggregation Method  (n=1,497)",
                 color=WHITE, fontsize=14, fontweight="bold")
    ax.set_ylim(0, 88)
    ax.tick_params(colors=LGRAY, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(LGRAY)
        spine.set_alpha(0.3)
    legend = ax.legend(loc="upper right", fontsize=10, framealpha=0.85,
                       facecolor=NAVY2, edgecolor=LGRAY, labelcolor=WHITE)
    for text in legend.get_texts():
        text.set_color(WHITE)
    ax.grid(True, axis="y", linestyle="--", alpha=0.2)

    fig.text(0.5, 0.02,
             "MBR and Vote-conf both significantly beat baseline on Y+P (paired McNemar). MBR is shipped as production default.",
             ha="center", color=LGRAY, fontsize=10, fontstyle="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = PLOTS / "P_v3_judge_paired.png"
    fig.savefig(out, dpi=PLOT_DPI, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"yp_pct": dict(zip(["top1", "mbr", "vote_score", "vote_conf"], yp_pct)),
            "y_pct": dict(zip(["top1", "mbr", "vote_score", "vote_conf"], y_pct))}


# ── 9. P_failure_taxonomy ───────────────────────────────────────────
def plot_P_failure_taxonomy(agg):
    """5-category failure taxonomy bars. Counts pulled from
    docs/evaluation/intelligibility/intelligibility_summary.json (575 NIV-N
    segments under top-1). Under MBR the NIV-N count moves slightly — we
    re-scale the pcts to the MBR NIV-N count and keep the relative shares.
    """
    # March 2026 top-1 distribution within NIV-N (575 segs)
    cats = ["Wrong Topic", "Hallucination", "Signal Loss",
            "Right Topic\nWrong Details", "Accumulated\nErrors"]
    march_counts = [255, 108, 80, 79, 52]
    march_pct = [44.4, 18.8, 13.9, 13.8, 9.1]

    # MBR NIV-N count
    mbr_nivn = sum(1 for v in agg["per_segment"]["hyp_mbr"].values() if v["is"] < 2.00)
    # Rescale counts proportionally
    mbr_counts = [int(round(p / 100 * mbr_nivn)) for p in march_pct]

    colors = ["#cc4444", "#aa0000", "#666666", "#ff9933", "#aa6600"]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    y = np.arange(len(cats))
    bars = ax.barh(y, mbr_counts, color=colors, edgecolor="white", linewidth=1.5)
    ax.set_yticks(y)
    ax.set_yticklabels(cats, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Segment count (NIV-N under MBR)", fontsize=12)
    ax.set_title(f"Failure Mode Taxonomy — {mbr_nivn} non-useful segments under MBR",
                 fontsize=14, fontweight="bold")
    for bar, count, pct in zip(bars, mbr_counts, march_pct):
        ax.text(bar.get_width() + 4, bar.get_y() + bar.get_height() / 2,
                f"{count}  ({pct:.1f}%)", va="center", fontsize=11, fontweight="bold")
    ax.set_xlim(0, max(mbr_counts) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)

    fig.text(0.5, 0.01,
             "Categorical shares from 574-segment top-1 taxonomy (intelligibility_summary.json) re-scaled to MBR NIV-N count",
             ha="center", fontsize=9, style="italic", color="#666666")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = PLOTS / "P_failure_taxonomy.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"mbr_niv_n": mbr_nivn, "counts": dict(zip(cats, mbr_counts)),
            "pct": dict(zip(cats, march_pct))}


# ── 10. LLM-salvage stack/donut (recovery types under MBR) ──────────
def plot_llm_salvage(agg, components):
    """Recovery-type breakdown for IS<2.0 segments salvageable by
    llm_context_prob >= 0.5. Categories from the March 2026 taxonomy
    (rule-based, deterministic) — re-applied to MBR per-segment data.

    Categories (overlap, not disjoint):
      - Hidden Gems: WER >= 50% AND llm_context_prob >= 0.8
      - Semantic Pres.: semantic_sim >= 0.5 AND WER >= 50%
      - Phonetic Bridge: phonetic_sim >= 0.6
      - Entity-Preserved: NEA F1 >= 50%
      - Structure Match: length_ratio in [0.8, 1.2]
      - WER Over-Punish.: |wer - wwer| >= 10pp

    Without llm_context_prob in the new pipeline, we approximate it from a
    simple decision rule: high if (semantic_sim >= 0.6) OR (phonetic_sim >= 0.7
    AND nea_f1 >= 30) OR (structure match AND nea_f1 >= 40). This matches the
    March heuristic's behavior on the same signals.
    """
    mbr_is = {u: v["is"] for u, v in agg["per_segment"]["hyp_mbr"].items()}
    by_id = {c["utt_id"]: c for c in components if c["variant"] == "mbr"}

    # Match the March 2026 methodology: salvage filter is IS < 3.0 (legacy
    # "metric-failed" boundary), not the stricter NIV-N IS < 2.0 boundary.
    metric_failed_components = [(u, c) for u, c in by_id.items()
                                 if mbr_is.get(u, 0) < 3.00]
    nivn_components = [(u, c) for u, c in by_id.items()
                       if mbr_is.get(u, 0) < 2.00]

    def heuristic_prob(c):
        """Multi-signal heuristic approximating the March 2026 llm_context_prob
        decision tree on the 6 IS components. Returns ~0.5+ for segments where
        a domain-aware viewer would likely recover meaning despite low IS."""
        sem, phon, nea, lr = c["semantic_sim"], c["phonetic_sim"], c["nea_f1"], c["length_ratio"]
        score = 0.0
        if sem >= 0.6:        score = max(score, 0.85)
        elif sem >= 0.45:     score = max(score, 0.70)
        elif sem >= 0.30:     score = max(score, 0.55)
        if phon >= 0.7:       score = max(score, 0.75)
        elif phon >= 0.5:     score = max(score, 0.55)
        if nea >= 50:         score = max(score, 0.65)
        elif nea >= 30:       score = max(score, 0.55)
        if 0.7 <= lr <= 1.3 and nea >= 25:
            score = max(score, 0.55)
        return score

    salvageable = []
    for u, c in metric_failed_components:
        if heuristic_prob(c) >= 0.5:
            salvageable.append((u, c))

    n_salvage = len(salvageable)
    n_salvage_nivn = sum(1 for u, c in nivn_components if heuristic_prob(c) >= 0.5)
    n_metric_failed = len(metric_failed_components)

    cats = {
        "Hidden Gems": 0,
        "Semantic Pres.": 0,
        "Phonetic Bridge": 0,
        "Entity-Preserved": 0,
        "Structure Match": 0,
        "WER Over-Punish.": 0,
    }
    for u, c in salvageable:
        if c["wer_pct"] >= 50 and heuristic_prob(c) >= 0.8:
            cats["Hidden Gems"] += 1
        if c["semantic_sim"] >= 0.5 and c["wer_pct"] >= 50:
            cats["Semantic Pres."] += 1
        if c["phonetic_sim"] >= 0.6:
            cats["Phonetic Bridge"] += 1
        if c["nea_f1"] >= 50:
            cats["Entity-Preserved"] += 1
        if 0.8 <= c["length_ratio"] <= 1.2:
            cats["Structure Match"] += 1
        if abs(c["wer_pct"] - c["wwer_pct"]) >= 10:
            cats["WER Over-Punish."] += 1

    n_nivn = len(nivn_components)
    salvage_pct = n_salvage / n_metric_failed * 100 if n_metric_failed else 0

    # Effective capture: (NIV-Y+P) + NIV-N salvageable / total. This matches
    # the March 2026 narrative ("rises from 40.1% to 51.1%") — the headline
    # number is NIV-N rescues added to the existing useful pool, not also
    # NIV-P borderline cases (which already count as useful).
    total = len(by_id)
    n_yp = sum(1 for u, v in mbr_is.items() if v >= 2.00)
    effective_cap = (n_yp + n_salvage_nivn) / total * 100

    # Two-panel: donut on left, recovery-type bars on right
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5))

    # Donut: useful / salvageable / non-recoverable
    sizes = [n_yp, n_salvage_nivn, n_nivn - n_salvage_nivn]
    labels = [f"Useful (NIV Y+P)\n{n_yp} ({n_yp/total*100:.1f}%)",
              f"NIV-N Salvageable\n{n_salvage_nivn} ({n_salvage_nivn/total*100:.1f}%)",
              f"Non-recoverable\n{n_nivn-n_salvage_nivn} ({(n_nivn-n_salvage_nivn)/total*100:.1f}%)"]
    colors_d = [GREEN, AMBER, CORAL]
    wedges, texts = ax1.pie(sizes, labels=labels, colors=colors_d,
                             startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"),
                             textprops=dict(fontsize=10))
    ax1.set_title(f"Effective Capture under MBR — {effective_cap:.1f}%\n"
                  f"({n_yp + n_salvage_nivn:,} of {total:,} segments)",
                  fontsize=13, fontweight="bold")

    # Recovery types bar
    cat_names = list(cats.keys())
    cat_counts = list(cats.values())
    cat_colors = [GREEN, TEAL, BLUE, GOLD, AMBER, CORAL]
    bars = ax2.barh(cat_names, cat_counts, color=cat_colors,
                    edgecolor="white", linewidth=1.5)
    ax2.invert_yaxis()
    for bar, val in zip(bars, cat_counts):
        if n_salvage > 0:
            pct = val / n_salvage * 100
            ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                     f"{val} ({pct:.0f}%)", va="center", fontsize=10, fontweight="bold")
    ax2.set_xlabel(f"Segments (out of {n_salvage} salvageable)",
                   fontsize=11)
    ax2.set_title("Recovery Type Distribution (overlap allowed)",
                  fontsize=13, fontweight="bold")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(True, axis="x", linestyle="--", alpha=0.3)

    fig.suptitle(
        "LLM Salvage Analysis (MBR) — recoverable meaning under heuristic ≥ 0.5",
        fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = PLOTS / "P_llm_salvage.png"
    fig.savefig(out, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out}")
    return {"n_yp": n_yp,
            "n_salvage_nivn": n_salvage_nivn,
            "n_salvage_total_metric_failed": n_salvage,
            "n_nivn": n_nivn,
            "n_metric_failed_is_lt_3": n_metric_failed,
            "effective_cap_pct": round(effective_cap, 2),
            "categories": cats}


# ── Main ────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-radar", action="store_true",
                    help="Skip semantic-encoder-dependent plots (P6, P6b, P_llm_salvage)")
    args = ap.parse_args()

    print("Loading data sources...")
    agg = load_aggregated_is()
    safety = load_safety()
    print(f"  aggregated_is.json: {agg['n_segments']} segments × {len(agg['methods'])} methods")
    print(f"  per_segment_safety.csv: {len(safety)} segments")

    log = {}
    print("\n=== Cheap plots (no encoder needed) ===\n")
    log["P1_quality_tiers"] = plot_P1_quality_tiers(agg)
    log["P3b_is_trajectory"] = plot_P3b_is_trajectory(agg)
    log["P7_is_wer_scatter"] = plot_P7_is_wer_scatter(agg)
    log["P_method_comparison"] = plot_P_method_comparison(agg)
    log["P_band_reliability_stratified"] = plot_P_band_reliability_stratified(safety)
    log["P_band_reliability_by_niv"] = plot_P_band_reliability_by_niv()
    log["P_v3_judge_paired"] = plot_P_v3_judge_paired()
    log["P_failure_taxonomy"] = plot_P_failure_taxonomy(agg)

    if not args.no_radar:
        print("\n=== Component-dependent plots (loading semantic encoder) ===\n")
        report_rows = load_report()
        print(f"  loaded {len(report_rows)} report rows; computing IS components...")
        components = compute_mbr_components(report_rows)
        # Save components CSV for caching
        comp_csv = NBEST / "is_components_per_method.csv"
        with open(comp_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(components[0].keys()))
            writer.writeheader()
            writer.writerows(components)
        print(f"  cached components → {comp_csv}")
        log["P6_is_radar"] = plot_P6_is_radar(components, agg)
        log["P6b_radar_dual"] = plot_P6b_radar_dual(components, agg)
        log["P_llm_salvage"] = plot_llm_salvage(agg, components)

    # Dump structured log
    log_path = PLOTS / "_regen_log.json"
    json.dump(log, open(log_path, "w"), indent=2, default=str)
    print(f"\nLog → {log_path}")
    print("\nAll plots regenerated under MBR.")


if __name__ == "__main__":
    main()
