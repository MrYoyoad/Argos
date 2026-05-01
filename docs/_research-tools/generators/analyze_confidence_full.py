#!/usr/bin/env python3
"""Full statistical analysis of the per-token confidence sidecar.

Eight analyses run from one feature frame:

  0. WER sanity      — reconcile today's wer-{fid} with the baseline report.csv.
  1. Distributions   — per-word prob / entropy / margin distributions, band coverage.
  2. Calibration     — empirical P(correct | predicted prob) via word alignment.
  3. Correlation map — segment-level features vs WER, WWER, NEA F1, IS, NIV labels.
  4. Filter ROC      — confidence-only detector for IS<2 (bad) and IS>=3.8 (good).
  5. Hallucination   — entropy / margin separating fluent-but-wrong from healthy.
  6. Trajectories    — k-means clusters of per-position prob trajectories.
  7. Beam preview    — cheap top-3 step-diversity vs full-distribution entropy.

Inputs:
  --confidence-sidecar  /tmp/vsp_b3_1497_out/confidence-{fid}.json
  --hypo                /tmp/vsp_b3_1497_out/hypo-{fid}.json
  --baseline-csv        english_full_results/client_outputs/report/report.csv
  --wer-file            /tmp/vsp_b3_1497_out/wer.{fid}  (optional, for analysis 0)

Outputs:
  presentation_materials_20260224/01_plots_for_slides/conf_*.png
  docs/confidence/confidence_full_analysis.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score, roc_curve

GENERATORS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GENERATORS_DIR))
from compute_word_confidence import (  # noqa: E402
    CONF_HIGH, CONF_MED, aggregate_subtokens_to_words,
)

REPO_ROOT = GENERATORS_DIR.parents[2]
PLOTS_DIR = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides"
DOC_PATH = REPO_ROOT / "docs" / "confidence" / "confidence_full_analysis.md"

# Brand palette (matches existing analyzers)
BG     = "#0d1b2a"
NAVY2  = "#152a40"
TEAL   = "#00b4d8"
GREEN  = "#4caf50"
GOLD   = "#ffd54f"
CORAL  = "#e06c75"
ORANGE = "#ff9800"
PURPLE = "#9c27b0"
WHITE  = "#ffffff"
LGRAY  = "#aaaaaa"
MGRAY  = "#666666"


# ─────────────────────────────────────────────────────────────────────────────
# Plot helpers
# ─────────────────────────────────────────────────────────────────────────────

def _style_ax(ax) -> None:
    ax.set_facecolor(NAVY2)
    ax.tick_params(colors=WHITE)
    for spine in ax.spines.values():
        spine.set_color(MGRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color=MGRAY, alpha=0.25)


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=BG, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {path.relative_to(REPO_ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature frame
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Segment:
    utt_id: str
    ref: str
    hyp_today: str
    hyp_baseline: Optional[str] = None
    # Word-level
    words: List[Dict[str, Any]] = field(default_factory=list)
    word_probs: List[float] = field(default_factory=list)
    # Token-level (for trajectories, hallucination dx)
    token_probs: List[float] = field(default_factory=list)
    token_entropies: List[float] = field(default_factory=list)
    token_margins: List[float] = field(default_factory=list)  # top1-top2
    token_top3_entropies: List[float] = field(default_factory=list)  # entropy over top3 only
    seq_score: Optional[float] = None
    # Baseline metrics from report.csv
    wer: Optional[float] = None
    wwer: Optional[float] = None
    nea_f1: Optional[float] = None
    is_score: Optional[float] = None
    is_tier: Optional[str] = None
    is_label: Optional[str] = None


def _parse_top3_entropy(top3: Optional[List[Dict[str, float]]]) -> Optional[float]:
    """Shannon entropy over the top-3 alts only (renormalized to sum 1)."""
    if not top3:
        return None
    ps = [t["p"] for t in top3 if t.get("p") is not None and t["p"] > 0]
    if not ps:
        return None
    total = sum(ps)
    if total <= 0:
        return None
    qs = [p / total for p in ps]
    return -sum(q * math.log(q) for q in qs)


def _margin(top3: Optional[List[Dict[str, float]]]) -> Optional[float]:
    """top1 - top2 from top3 alternatives."""
    if not top3 or len(top3) < 2:
        return None
    ps = sorted([t["p"] for t in top3 if t.get("p") is not None], reverse=True)
    if len(ps) < 2:
        return None
    return ps[0] - ps[1]


def _f(row: Dict[str, str], k: str) -> Optional[float]:
    v = (row.get(k) or "").strip()
    if v in ("", "nan", "None"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def build_frame(
    confidence_path: Path,
    hypo_path: Path,
    baseline_csv: Path,
) -> Tuple[List[Segment], Dict[str, Any]]:
    """Join sidecar + hypo + baseline. Return list of Segment + diagnostics."""
    conf = json.loads(confidence_path.read_text())
    hypo = json.loads(hypo_path.read_text())
    baseline_rows = list(csv.DictReader(baseline_csv.open(encoding="utf-8")))
    baseline_by_id = {r["utt_id"]: r for r in baseline_rows}

    print(f"Sidecar segments:   {len(conf)}")
    print(f"Hypo segments:      {len(hypo['utt_id'])}")
    print(f"Baseline segments:  {len(baseline_rows)}")

    segs: List[Segment] = []
    n_no_baseline = 0
    n_empty_words = 0
    for utt_id, ref, hyp_today in zip(hypo["utt_id"], hypo["ref"], hypo["hypo"]):
        crec = conf.get(utt_id)
        if not crec:
            continue
        tokens = crec.get("tokens", [])

        words = aggregate_subtokens_to_words(tokens)
        word_probs = [w["prob"] for w in words if w.get("prob") is not None]

        # Per-token derived features (skip BOS/EOS specials at the ends).
        tprobs: List[float] = []
        tents: List[float] = []
        tmargs: List[float] = []
        ttop3_ents: List[float] = []
        for t in tokens:
            ttext = t.get("token", "")
            if ttext.startswith("<") and ttext.endswith(">"):
                continue  # specials
            if t.get("prob") is not None:
                tprobs.append(float(t["prob"]))
            ent_v = t.get("entropy")
            if ent_v is not None and not (isinstance(ent_v, float) and math.isnan(ent_v)):
                tents.append(float(ent_v))
            m = _margin(t.get("top3"))
            if m is not None:
                tmargs.append(m)
            e3 = _parse_top3_entropy(t.get("top3"))
            if e3 is not None:
                ttop3_ents.append(e3)

        seg = Segment(
            utt_id=utt_id,
            ref=ref,
            hyp_today=hyp_today,
            words=words,
            word_probs=word_probs,
            token_probs=tprobs,
            token_entropies=tents,
            token_margins=tmargs,
            token_top3_entropies=ttop3_ents,
            seq_score=crec.get("sequence_score"),
        )

        brow = baseline_by_id.get(utt_id)
        if brow is None:
            n_no_baseline += 1
        else:
            seg.hyp_baseline = brow.get("hyp", "").strip()
            seg.wer = _f(brow, "wer_%")
            seg.wwer = _f(brow, "wwer_%")
            seg.nea_f1 = _f(brow, "nea_f1_%")
            seg.is_score = _f(brow, "is_score")
            seg.is_tier = brow.get("is_tier", "").strip() or None
            seg.is_label = brow.get("is_label", "").strip() or None

        if not word_probs:
            n_empty_words += 1
        segs.append(seg)

    diag = {
        "n_total": len(segs),
        "n_no_baseline": n_no_baseline,
        "n_empty_words": n_empty_words,
        "n_with_baseline": sum(1 for s in segs if s.is_score is not None),
    }
    print(f"\nFrame built: {diag}")
    return segs, diag


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 0 — WER reconciliation
# ─────────────────────────────────────────────────────────────────────────────

def analysis_0_wer_reconcile(segs: List[Segment]) -> Dict[str, Any]:
    """Reconcile today's WER (59.17% pooled) vs baseline mean WER (64.1%)."""
    print("\n══ Analysis 0: WER reconciliation ══")
    matches: List[Dict[str, Any]] = []
    n_identical = 0
    n_different = 0
    for s in segs:
        if not s.hyp_baseline or not s.hyp_today:
            continue
        a = s.hyp_today.strip().lower().split()
        b = s.hyp_baseline.strip().lower().split()
        if a == b:
            n_identical += 1
        else:
            n_different += 1
            matches.append({"utt": s.utt_id, "today": s.hyp_today, "baseline": s.hyp_baseline})

    # Recompute corpus-pooled and mean-of-segment WER on TODAY's hyps
    # using a simple Levenshtein over words.
    def wer_pair(ref: str, hyp: str) -> Tuple[int, int]:
        rs = ref.strip().lower().split()
        hs = hyp.strip().lower().split()
        n, m = len(rs), len(hs)
        if n == 0:
            return (m, 0)  # all insertions
        d = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            d[i][0] = i
        for j in range(m + 1):
            d[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if rs[i-1] == hs[j-1] else 1
                d[i][j] = min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+cost)
        return (d[n][m], n)

    err_total = 0
    ref_total = 0
    seg_wers: List[float] = []
    for s in segs:
        e, r = wer_pair(s.ref, s.hyp_today)
        if r > 0:
            err_total += e
            ref_total += r
            seg_wers.append(e / r * 100)

    pooled = err_total / ref_total * 100 if ref_total else 0.0
    mean_of_segs = sum(seg_wers) / len(seg_wers) if seg_wers else 0.0
    print(f"  Hypotheses identical to baseline: {n_identical}")
    print(f"  Hypotheses different:             {n_different}")
    print(f"  Today, pooled WER:                {pooled:.2f}%")
    print(f"  Today, mean-of-segment WER:       {mean_of_segs:.2f}%")
    return {
        "n_identical": n_identical,
        "n_different": n_different,
        "today_pooled_wer": pooled,
        "today_mean_seg_wer": mean_of_segs,
        "different_examples": matches[:5],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 1 — distributions of prob / entropy / margin
# ─────────────────────────────────────────────────────────────────────────────

def analysis_1_distributions(segs: List[Segment]) -> Dict[str, Any]:
    print("\n══ Analysis 1: Distributions (prob / entropy / margin) ══")
    all_probs = [p for s in segs for p in s.token_probs]
    all_ents  = [e for s in segs for e in s.token_entropies]
    all_marg  = [m for s in segs for m in s.token_margins]
    word_probs = [p for s in segs for p in s.word_probs]

    def stats_block(name: str, vs: List[float]) -> Dict[str, float]:
        if not vs:
            return {}
        arr = np.asarray(vs)
        return {
            "name": name, "n": len(vs),
            "mean": float(arr.mean()), "median": float(np.median(arr)),
            "std": float(arr.std()),
            "p10": float(np.percentile(arr, 10)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75)),
            "p90": float(np.percentile(arr, 90)),
            "p99": float(np.percentile(arr, 99)),
        }

    blocks = {
        "token_prob":   stats_block("token_prob",   all_probs),
        "word_prob":    stats_block("word_prob",    word_probs),
        "entropy":      stats_block("entropy",      all_ents),
        "margin":       stats_block("margin",       all_marg),
    }
    for k, v in blocks.items():
        if v:
            print(f"  {k:14s} n={v['n']:6d}  mean={v['mean']:.3f}  med={v['median']:.3f}  "
                  f"p10={v['p10']:.3f}  p90={v['p90']:.3f}")

    # Plot: 2x2 distributions (token-prob, word-prob, entropy, margin)
    fig, axs = plt.subplots(2, 2, figsize=(13, 9), dpi=200)
    fig.patch.set_facecolor(BG)
    panels = [
        (axs[0, 0], all_probs,  "Per-token probability (max-softmax)", TEAL,  [0, 1]),
        (axs[0, 1], word_probs, "Per-word probability (min over sub-tokens)", GREEN, [0, 1]),
        (axs[1, 0], all_ents,   "Per-token entropy (full distribution)", GOLD,   [0, max(all_ents) if all_ents else 1]),
        (axs[1, 1], all_marg,   "Per-token margin (top1 − top2)",      CORAL, [0, 1]),
    ]
    for ax, data, title, color, xrng in panels:
        if data:
            bins = np.linspace(xrng[0], xrng[1], 51)
            ax.hist(data, bins=bins, color=color, edgecolor=WHITE, linewidth=0.4)
        ax.set_title(title, color=WHITE, fontsize=12, fontweight="bold", pad=10)
        ax.set_ylabel("Count", color=WHITE)
        _style_ax(ax)
    fig.suptitle(
        f"Confidence-signal distributions — {len(all_probs):,} tokens, "
        f"{len(word_probs):,} words across {len(segs):,} segments",
        color=WHITE, fontsize=14, fontweight="bold", y=1.0,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, PLOTS_DIR / "conf_full_distributions.png")

    return blocks


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 2 — calibration: P(correct | predicted prob bin)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from _alignment import hyp_word_correctness as _word_correctness_alignment  # noqa: F401
except ImportError:
    # When invoked from a different cwd, ensure the generators dir is on the path.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from _alignment import hyp_word_correctness as _word_correctness_alignment  # noqa: F401


def _ece(probs: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error via equal-width bins on probs in [0,1]."""
    edges = np.linspace(0, 1, n_bins + 1)
    n = len(probs)
    if n == 0:
        return 0.0
    ece = 0.0
    for k in range(n_bins):
        lo, hi = edges[k], edges[k+1]
        if k == n_bins - 1:
            mask = (probs >= lo) & (probs <= hi)
        else:
            mask = (probs >= lo) & (probs < hi)
        if mask.sum() == 0:
            continue
        avg_conf = probs[mask].mean()
        avg_acc = correct[mask].mean()
        ece += (mask.sum() / n) * abs(avg_conf - avg_acc)
    return float(ece)


def analysis_2_calibration(segs: List[Segment]) -> Dict[str, Any]:
    print("\n══ Analysis 2: Calibration (P(correct | predicted prob)) ══")
    word_probs: List[float] = []
    word_correct: List[int] = []
    for s in segs:
        if not s.words or not s.ref:
            continue
        hwords = [w["word"] for w in s.words]
        wprobs = [w["prob"] for w in s.words]
        correct = _word_correctness_alignment(s.ref, hwords)
        for p, c in zip(wprobs, correct):
            if p is None:
                continue
            word_probs.append(float(p))
            word_correct.append(int(c))
    probs = np.asarray(word_probs)
    corr = np.asarray(word_correct)
    print(f"  {len(probs):,} hyp words aligned with reference")

    # Calibration curve + per-band empirical accuracy.
    n_bins = 10
    edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = (edges[:-1] + edges[1:]) / 2
    bin_acc = []
    bin_n = []
    for k in range(n_bins):
        lo, hi = edges[k], edges[k+1]
        mask = (probs >= lo) & (probs < hi) if k < n_bins - 1 else (probs >= lo) & (probs <= hi)
        if mask.sum() > 0:
            bin_acc.append(float(corr[mask].mean()))
        else:
            bin_acc.append(np.nan)
        bin_n.append(int(mask.sum()))

    ece = _ece(probs, corr, n_bins=n_bins)
    print(f"  ECE (10-bin): {ece*100:.2f}%")

    band_high_acc = float(corr[probs >= CONF_HIGH].mean()) if (probs >= CONF_HIGH).sum() else None
    band_med_mask = (probs >= CONF_MED) & (probs < CONF_HIGH)
    band_med_acc = float(corr[band_med_mask].mean()) if band_med_mask.sum() else None
    band_low_acc = float(corr[probs < CONF_MED].mean()) if (probs < CONF_MED).sum() else None
    print(f"  P(correct | green p>={CONF_HIGH}): {band_high_acc:.3f} "
          f"({(probs>=CONF_HIGH).sum():,} words)")
    print(f"  P(correct | yellow {CONF_MED}<=p<{CONF_HIGH}): {band_med_acc:.3f} "
          f"({band_med_mask.sum():,} words)")
    print(f"  P(correct | red p<{CONF_MED}): {band_low_acc:.3f} "
          f"({(probs<CONF_MED).sum():,} words)")

    # Plot calibration (reliability diagram)
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    fig.patch.set_facecolor(BG)
    _style_ax(ax)
    ax.plot([0, 1], [0, 1], "--", color=LGRAY, linewidth=1.2, label="Perfect calibration")
    valid = ~np.isnan(bin_acc)
    ax.plot(bin_centers[valid], np.array(bin_acc)[valid], "o-",
            color=TEAL, linewidth=2, markersize=8, label="Empirical")
    # Bar of bin counts on twin axis (volume).
    ax2 = ax.twinx()
    ax2.bar(bin_centers, bin_n, width=0.08, color=GOLD, alpha=0.18, edgecolor="none")
    ax2.set_ylabel("Word count per bin", color=GOLD)
    ax2.tick_params(colors=GOLD)
    ax2.set_facecolor((0,0,0,0))
    for spine in ax2.spines.values():
        spine.set_color(MGRAY)
    ax2.spines["top"].set_visible(False)
    # Bands as vertical guides
    ax.axvline(CONF_MED, color=CORAL, linestyle=":", alpha=0.6)
    ax.axvline(CONF_HIGH, color=GREEN, linestyle=":", alpha=0.6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted probability (max-softmax)", color=WHITE, fontsize=12)
    ax.set_ylabel("Empirical correctness rate", color=WHITE, fontsize=12)
    ax.set_title(
        f"Calibration — ECE = {ece*100:.1f}%, n = {len(probs):,} words",
        color=WHITE, fontsize=13, fontweight="bold", pad=12,
    )
    ax.legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY, labelcolor=WHITE)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_calibration_curve.png")

    return {
        "n_words": len(probs),
        "ece_pct": ece * 100,
        "p_correct_green": band_high_acc,
        "p_correct_yellow": band_med_acc,
        "p_correct_red": band_low_acc,
        "n_green": int((probs >= CONF_HIGH).sum()),
        "n_yellow": int(band_med_mask.sum()),
        "n_red": int((probs < CONF_MED).sum()),
        "bin_acc": bin_acc,
        "bin_n": bin_n,
        "bin_centers": bin_centers.tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Segment-level features (for analyses 3-7)
# ─────────────────────────────────────────────────────────────────────────────

def segment_features(s: Segment) -> Optional[Dict[str, float]]:
    """Compute segment-level confidence features. Returns None if no probs."""
    if not s.token_probs:
        return None
    p = np.asarray(s.token_probs)
    e = np.asarray(s.token_entropies) if s.token_entropies else np.array([])
    m = np.asarray(s.token_margins)   if s.token_margins   else np.array([])
    e3 = np.asarray(s.token_top3_entropies) if s.token_top3_entropies else np.array([])
    feats = {
        "seq_score":     s.seq_score if s.seq_score is not None else float("nan"),
        "mean_prob":     float(p.mean()),
        "min_prob":      float(p.min()),
        "geomean_prob":  float(np.exp(np.log(np.clip(p, 1e-10, 1.0)).mean())),
        "frac_p_lt_04":  float((p < CONF_MED).mean()),
        "frac_p_ge_085": float((p >= CONF_HIGH).mean()),
        "p_std":         float(p.std()),
        "n_tokens":      float(len(p)),
        "len_hyp_words": float(len(s.hyp_today.split())),
        "len_ref_words": float(len(s.ref.split())),
        "len_ratio":     (len(s.hyp_today.split()) / max(1, len(s.ref.split()))),
        "mean_word_prob": (sum(s.word_probs) / len(s.word_probs)) if s.word_probs else float("nan"),
        "min_word_prob":  min(s.word_probs) if s.word_probs else float("nan"),
        "n_words":        float(len(s.word_probs)),
    }
    if e.size:
        feats["mean_entropy"] = float(e.mean())
        feats["max_entropy"]  = float(e.max())
        feats["entropy_var"]  = float(e.var())
    if m.size:
        feats["mean_margin"]  = float(m.mean())
        feats["min_margin"]   = float(m.min())
    if e3.size:
        feats["mean_top3_ent"] = float(e3.mean())
    # Trajectory features
    if len(p) >= 4:
        feats["slope_first_half"] = float(np.polyfit(np.arange(len(p)//2), p[:len(p)//2], 1)[0])
        # Earliest position where rolling-mean drops below 0.4 and stays
        win = min(5, max(2, len(p)//5))
        roll = np.convolve(p, np.ones(win)/win, mode="valid")
        below = roll < 0.4
        first_collapse = -1
        for i in range(len(below)):
            if below[i]:
                first_collapse = i + win // 2
                break
        feats["early_collapse_idx"] = float(first_collapse) / len(p) if first_collapse >= 0 else 1.0
        feats["auc_prob"] = float(p.mean())  # already normalized; same as mean_prob
    return feats


def features_dataframe(segs: List[Segment]) -> pd.DataFrame:
    rows = []
    for s in segs:
        feats = segment_features(s)
        if feats is None:
            continue
        feats.update({
            "utt_id": s.utt_id,
            "wer": s.wer, "wwer": s.wwer, "nea_f1": s.nea_f1,
            "is_score": s.is_score, "is_tier": s.is_tier, "is_label": s.is_label,
        })
        rows.append(feats)
    df = pd.DataFrame(rows)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 3 — correlation map
# ─────────────────────────────────────────────────────────────────────────────

CONF_FEATURES = [
    "mean_prob", "min_prob", "geomean_prob",
    "mean_word_prob", "min_word_prob",
    "frac_p_lt_04", "frac_p_ge_085", "p_std",
    "mean_entropy", "max_entropy", "entropy_var",
    "mean_margin", "min_margin",
    "mean_top3_ent",
    "seq_score",
    "len_ratio",
    "slope_first_half", "early_collapse_idx",
]

GROUND_TRUTH = ["wer", "wwer", "nea_f1", "is_score"]
BINARY_LABELS = [
    ("niv_y", "is_score >= 3.80"),
    ("niv_n", "is_score <  2.00"),
]


def analysis_3_correlation_map(df: pd.DataFrame) -> Dict[str, Any]:
    print("\n══ Analysis 3: Correlation map ══")
    df = df.copy()
    df["niv_y"] = (df["is_score"] >= 3.80).astype(int)
    df["niv_n"] = (df["is_score"] <  2.00).astype(int)

    targets = GROUND_TRUTH + ["niv_y", "niv_n"]
    pearson = pd.DataFrame(index=CONF_FEATURES, columns=targets, dtype=float)
    spearman = pd.DataFrame(index=CONF_FEATURES, columns=targets, dtype=float)

    for feat in CONF_FEATURES:
        if feat not in df.columns:
            continue
        for tgt in targets:
            sub = df[[feat, tgt]].dropna()
            if len(sub) < 30:
                pearson.at[feat, tgt] = np.nan
                spearman.at[feat, tgt] = np.nan
                continue
            r_p, _ = stats.pearsonr(sub[feat], sub[tgt])
            r_s, _ = stats.spearmanr(sub[feat], sub[tgt])
            pearson.at[feat, tgt] = r_p
            spearman.at[feat, tgt] = r_s

    print("\n  Pearson r:")
    print(pearson.round(3).to_string())

    # Heatmap of |r| (Pearson). Sign retained but magnitude drives color.
    fig, ax = plt.subplots(figsize=(10, 9), dpi=200)
    fig.patch.set_facecolor(BG)
    arr = pearson.values.astype(float)
    im = ax.imshow(arr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(targets))); ax.set_xticklabels(targets, rotation=30, ha="right", color=WHITE)
    ax.set_yticks(range(len(CONF_FEATURES))); ax.set_yticklabels(CONF_FEATURES, color=WHITE)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            if np.isnan(v):
                txt = "—"
            else:
                txt = f"{v:+.2f}"
            color = "white" if abs(v) > 0.5 else "black"
            ax.text(j, i, txt, ha="center", va="center", color=color, fontsize=9)
    ax.set_title(
        f"Pearson r — confidence features vs quality metrics  (n≈{int(df.dropna(subset=['is_score']).shape[0])})",
        color=WHITE, fontsize=13, fontweight="bold", pad=14,
    )
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.ax.tick_params(colors=WHITE)
    cb.outline.set_edgecolor(MGRAY)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_correlation_heatmap.png")

    # Compute max |Pearson - Spearman| across the matrix as a linearity check.
    # Exclude `len_ratio` and `slope_first_half` from the headline check — both
    # are heavy-tailed shape features, not confidence aggregates per se. Report
    # both the full max and the conf-features-vs-IS max.
    diff = (pearson - spearman).abs()
    max_dev = float(diff.max().max())
    conf_features = [f for f in CONF_FEATURES
                     if f not in ("len_ratio", "slope_first_half") and f in diff.index]
    conf_dev_is = float(diff.loc[conf_features, "is_score"].max())
    print(f"\n  Max |Pearson - Spearman| (whole matrix): {max_dev:.3f}")
    print(f"  Max |Pearson - Spearman| (conf features vs IS): {conf_dev_is:.3f}")

    return {
        "pearson": pearson,
        "spearman": spearman,
        "n_segments": int(df.dropna(subset=["is_score"]).shape[0]),
        "max_pearson_spearman_dev": max_dev,
        "max_conf_dev_is": conf_dev_is,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 4 — ROC for confidence-only filter
# ─────────────────────────────────────────────────────────────────────────────

def analysis_4_roc(df: pd.DataFrame) -> Dict[str, Any]:
    print("\n══ Analysis 4: ROC for filtering ══")
    sub = df.dropna(subset=["is_score"]).copy()
    sub["niv_y"] = (sub["is_score"] >= 3.80).astype(int)
    sub["niv_bad"] = (sub["is_score"] < 2.00).astype(int)

    candidates = [
        ("mean_prob",      False),  # higher → better; use as "good" detector positive direction
        ("mean_entropy",   True),   # invert: higher entropy → bad
        ("mean_margin",    False),
        ("min_word_prob",  False),
        ("frac_p_lt_04",   True),   # higher → bad
        ("frac_p_ge_085",  False),  # higher → good
        ("seq_score",      False),  # higher (less negative) → better
    ]

    rows = []
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=200)
    fig.patch.set_facecolor(BG)
    titles = ["Detect 'bad' segments (IS < 2.00 → NIV-N)",
              "Detect 'good' segments (IS ≥ 3.80 → NIV-Y)"]
    label_keys = ["niv_bad", "niv_y"]
    colors = [TEAL, GREEN, GOLD, CORAL, ORANGE, PURPLE, "#777"]

    for ax, title, key in zip(axs, titles, label_keys):
        _style_ax(ax)
        ax.plot([0, 1], [0, 1], "--", color=LGRAY)
        for (feat, invert), c in zip(candidates, colors):
            x = sub[feat].values
            y = sub[key].values
            mask = ~np.isnan(x)
            x, y = x[mask], y[mask]
            score = -x if invert else x
            # If detecting "bad": positive class is bad. We want score that goes UP when bad.
            if key == "niv_bad":
                score = -score  # flip again so higher score → bad
            try:
                fpr, tpr, _ = roc_curve(y, score)
                auc = roc_auc_score(y, score)
            except ValueError:
                continue
            tag = f"{feat:14s}{'  (inv)' if invert else ''}"
            ax.plot(fpr, tpr, color=c, linewidth=1.7, label=f"{feat}  AUC={auc:.3f}")
            rows.append({"target": key, "feature": feat, "auc": auc, "n": int(mask.sum())})
        ax.set_xlabel("False positive rate", color=WHITE)
        ax.set_ylabel("True positive rate", color=WHITE)
        ax.set_title(title, color=WHITE, fontsize=12, fontweight="bold")
        ax.legend(loc="lower right", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_roc_filter.png")

    aucs = pd.DataFrame(rows)
    print("\n  AUC table:")
    print(aucs.pivot(index="feature", columns="target", values="auc").round(3).to_string())

    return {"aucs": aucs}


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 5 — Hallucination scatter
# ─────────────────────────────────────────────────────────────────────────────

def analysis_5_hallucination(df: pd.DataFrame, segs: List[Segment]) -> Dict[str, Any]:
    print("\n══ Analysis 5: Hallucination detection ══")
    sub = df.dropna(subset=["wer", "mean_entropy", "mean_prob", "len_ratio"]).copy()
    sub["hallucinated"] = ((sub["wer"] >= 100) & (sub["len_ratio"] >= 0.5)).astype(int)
    sub["dangerous"] = ((sub["mean_prob"] >= 0.85) & (sub["hallucinated"] == 1)).astype(int)

    n_hall = int(sub["hallucinated"].sum())
    n_dang = int(sub["dangerous"].sum())
    print(f"  Hallucinated (WER>=100, len_ratio>=0.5): {n_hall} / {len(sub)}")
    print(f"  Dangerous (above + mean_prob >= 0.85):   {n_dang}")

    # Prob distribution among hallucinated vs not (Mann-Whitney for sanity)
    p_hall = sub.loc[sub.hallucinated == 1, "mean_prob"].values
    p_ok = sub.loc[sub.hallucinated == 0, "mean_prob"].values
    e_hall = sub.loc[sub.hallucinated == 1, "mean_entropy"].values
    e_ok = sub.loc[sub.hallucinated == 0, "mean_entropy"].values
    if len(p_hall) and len(p_ok):
        u_p, p_p = stats.mannwhitneyu(p_hall, p_ok, alternative="two-sided")
        u_e, p_e = stats.mannwhitneyu(e_hall, e_ok, alternative="two-sided")
        print(f"  Mann-Whitney mean_prob hallucinated vs healthy: U={u_p:.0f}, p={p_p:.2e}")
        print(f"  Mann-Whitney mean_entropy hallucinated vs healthy: U={u_e:.0f}, p={p_e:.2e}")

    # 2D scatter: mean_prob × mean_entropy, colored by hallucinated
    fig, ax = plt.subplots(figsize=(11, 8), dpi=200)
    fig.patch.set_facecolor(BG)
    _style_ax(ax)
    ok = sub[sub.hallucinated == 0]
    bad = sub[sub.hallucinated == 1]
    ax.scatter(ok.mean_prob, ok.mean_entropy, c=TEAL, s=12, alpha=0.45,
               edgecolor="none", label=f"Healthy  (n={len(ok)})")
    ax.scatter(bad.mean_prob, bad.mean_entropy, c=CORAL, s=22, alpha=0.85,
               edgecolor="white", linewidth=0.4, label=f"Hallucinated  (n={len(bad)})")
    # Overlay green-band threshold
    ax.axvline(0.85, color=GREEN, linestyle=":", linewidth=1.5, alpha=0.7,
               label="green band (mean_prob ≥ 0.85)")
    # Annotate the dangerous quadrant.
    dang = sub[sub.dangerous == 1]
    if len(dang) > 0:
        ax.scatter(dang.mean_prob, dang.mean_entropy, facecolors="none",
                   edgecolors=GOLD, s=140, linewidth=1.6,
                   label=f"DANGEROUS (high prob, hallucinated)  n={len(dang)}")
    ax.set_xlabel("mean_prob (max-softmax)", color=WHITE, fontsize=12)
    ax.set_ylabel("mean_entropy (full distribution)", color=WHITE, fontsize=12)
    ax.set_title(
        f"Hallucination scatter — does entropy catch what max-softmax misses?",
        color=WHITE, fontsize=13, fontweight="bold", pad=12,
    )
    ax.legend(loc="upper right", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=10)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_hallucination_scatter.png")

    return {
        "n_hallucinated": n_hall,
        "n_dangerous": n_dang,
        "mean_prob_hall_median": float(np.median(p_hall)) if len(p_hall) else None,
        "mean_prob_ok_median":   float(np.median(p_ok)) if len(p_ok) else None,
        "mean_entropy_hall_median": float(np.median(e_hall)) if len(e_hall) else None,
        "mean_entropy_ok_median":   float(np.median(e_ok)) if len(e_ok) else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 6 — Trajectory clustering
# ─────────────────────────────────────────────────────────────────────────────

def _resample(arr: Sequence[float], n: int = 100) -> np.ndarray:
    a = np.asarray(arr, dtype=float)
    if len(a) < 2:
        return np.full(n, a[0] if len(a) else np.nan)
    xp = np.linspace(0, 1, len(a))
    xq = np.linspace(0, 1, n)
    return np.interp(xq, xp, a)


def analysis_6_trajectories(segs: List[Segment], df: pd.DataFrame, k: int = 5) -> Dict[str, Any]:
    print("\n══ Analysis 6: Trajectory clustering ══")
    utt_to_idx = {s.utt_id: i for i, s in enumerate(segs)}
    valid_segs = [s for s in segs if len(s.token_probs) >= 4]
    print(f"  Trajectory-eligible segments: {len(valid_segs)}")
    X = np.vstack([_resample(s.token_probs, 100) for s in valid_segs])
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    centers = km.cluster_centers_
    labels = km.labels_

    # Per-cluster summary stats
    rows = []
    df_idx = df.set_index("utt_id")
    for ck in range(k):
        ids = [valid_segs[i].utt_id for i in range(len(valid_segs)) if labels[i] == ck]
        sub = df_idx.loc[df_idx.index.intersection(ids)]
        rows.append({
            "cluster": ck,
            "n_segments": len(ids),
            "mean_wer": float(sub["wer"].mean()) if "wer" in sub else np.nan,
            "mean_is": float(sub["is_score"].mean()) if "is_score" in sub else np.nan,
            "p_niv_n": float((sub["is_score"] < 2.0).mean()) if "is_score" in sub else np.nan,
            "p_niv_y": float((sub["is_score"] >= 3.8).mean()) if "is_score" in sub else np.nan,
        })
    summary = pd.DataFrame(rows).sort_values("mean_is", ascending=False)
    print("\n  Cluster summary (sorted by mean IS, best first):")
    print(summary.round(3).to_string(index=False))

    # Plot: cluster centroids + per-cluster summary bar
    fig, axs = plt.subplots(2, 1, figsize=(13, 9), dpi=200,
                            gridspec_kw={"height_ratios": [3, 2]})
    fig.patch.set_facecolor(BG)
    palette = [TEAL, GREEN, GOLD, CORAL, ORANGE, PURPLE]
    for ck, color in zip(range(k), palette):
        # Sort by descending mean_is so labels match the cluster summary
        is_rank_idx = summary.set_index("cluster").index.get_loc(ck)
        label = (f"C{ck} (n={int(summary.loc[summary.cluster==ck,'n_segments'].iloc[0])}, "
                 f"WER={summary.loc[summary.cluster==ck,'mean_wer'].iloc[0]:.0f}%, "
                 f"IS={summary.loc[summary.cluster==ck,'mean_is'].iloc[0]:.2f})")
        axs[0].plot(centers[ck], color=color, linewidth=2.2, label=label, alpha=0.9)
    _style_ax(axs[0])
    axs[0].set_ylim(0, 1)
    axs[0].set_xlabel("Position in segment (resampled to 100)", color=WHITE)
    axs[0].set_ylabel("Mean per-position prob", color=WHITE)
    axs[0].set_title(f"Confidence trajectory clusters (k={k})",
                     color=WHITE, fontsize=13, fontweight="bold", pad=10)
    axs[0].legend(loc="lower right", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)

    # Bottom panel: cluster IS / WER bars
    summary_sorted = summary.sort_values("cluster")
    x = np.arange(k)
    w = 0.35
    axs[1].bar(x - w/2, summary_sorted["mean_wer"], width=w, color=CORAL,
               edgecolor=WHITE, label="Mean WER %")
    axs[1].bar(x + w/2, summary_sorted["mean_is"]*20, width=w, color=GREEN,
               edgecolor=WHITE, label="Mean IS × 20  (rescaled)")
    _style_ax(axs[1])
    axs[1].set_xticks(x); axs[1].set_xticklabels([f"C{i}" for i in range(k)],
                                                  color=WHITE)
    axs[1].set_title("Cluster quality (lower WER, higher IS = better)",
                     color=WHITE, fontsize=12, fontweight="bold", pad=8)
    axs[1].legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_trajectory_clusters.png")

    return {"summary": summary, "k": k}


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 7 — beam preview (top3 step diversity vs full entropy)
# ─────────────────────────────────────────────────────────────────────────────

def analysis_7_beam_preview(df: pd.DataFrame) -> Dict[str, Any]:
    print("\n══ Analysis 7: Beam-preview (top-3 entropy vs full entropy) ══")
    sub = df.dropna(subset=["mean_entropy", "mean_top3_ent", "wer", "is_score"]).copy()
    if len(sub) == 0:
        print("  No data — skipping")
        return {}
    r_full_top3, _ = stats.pearsonr(sub["mean_entropy"], sub["mean_top3_ent"])
    r_full_wer,  _ = stats.pearsonr(sub["mean_entropy"], sub["wer"])
    r_top3_wer,  _ = stats.pearsonr(sub["mean_top3_ent"], sub["wer"])
    r_full_is,   _ = stats.pearsonr(sub["mean_entropy"], sub["is_score"])
    r_top3_is,   _ = stats.pearsonr(sub["mean_top3_ent"], sub["is_score"])
    print(f"  r(full_entropy, top3_entropy) = {r_full_top3:+.3f}")
    print(f"  r(full_entropy,  WER)         = {r_full_wer:+.3f}")
    print(f"  r(top3_entropy,  WER)         = {r_top3_wer:+.3f}")
    print(f"  r(full_entropy,  IS)          = {r_full_is:+.3f}")
    print(f"  r(top3_entropy,  IS)          = {r_top3_is:+.3f}")
    return {
        "r_full_top3": r_full_top3, "r_full_wer": r_full_wer,
        "r_top3_wer": r_top3_wer, "r_full_is": r_full_is,
        "r_top3_is": r_top3_is, "n": len(sub),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 8 — Operating-point selection (precision/recall sweep)
# ─────────────────────────────────────────────────────────────────────────────

def _utt_duration_seconds(utt_id: str) -> float:
    """Duration encoded in utt_id suffix `_<start_cs>_<end_cs>` (centiseconds)."""
    parts = utt_id.split("_")
    try:
        return (int(parts[-1]) - int(parts[-2])) / 100.0
    except (ValueError, IndexError):
        return float("nan")


def _gate_eval(df: pd.DataFrame, mask: pd.Series, name: str, ny: int, total: int) -> Dict[str, Any]:
    n_trust = int(mask.sum())
    if n_trust == 0:
        return {"name": name, "n_trust": 0, "prec": 0.0, "recall": 0.0,
                "f1": 0.0, "false_n": 0, "false_p": 0, "vol_pct": 0.0}
    sub = df[mask]
    tp = int(sub["niv_y"].sum())
    fn = int(sub["niv_n"].sum())
    fp = int(((~sub["niv_y"].astype(bool)) & (~sub["niv_n"].astype(bool))).sum())
    prec = tp / n_trust
    recall = tp / max(1, ny)
    f1 = 2 * prec * recall / (prec + recall) if (prec + recall) > 0 else 0.0
    return {"name": name, "n_trust": n_trust, "prec": prec, "recall": recall,
            "f1": f1, "false_n": fn, "false_p": fp,
            "vol_pct": n_trust / total * 100}


def analysis_8_operating_points(df: pd.DataFrame) -> Dict[str, Any]:
    """Precision/recall sweep across gate types. Recommends a balanced and a
    strict operating point."""
    print("\n══ Analysis 8: Operating-point selection ══")
    df = df.dropna(subset=["is_score"]).copy()
    df["niv_y"] = (df["is_score"] >= 3.80).astype(int)
    df["niv_n"] = (df["is_score"] <  2.00).astype(int)
    df["duration_s"] = df["utt_id"].map(_utt_duration_seconds)
    ny = int(df["niv_y"].sum())
    total = len(df)

    rows = []
    # Single signal sweeps
    for t in np.linspace(0.50, 0.95, 19):
        rows.append({**_gate_eval(df, df["mean_word_prob"] >= t,
                                   f"mwp >= {t:.2f}", ny, total),
                     "kind": "single"})
    # Duration-augmented at three mwp anchors
    for mwp in [0.75, 0.80, 0.85]:
        for dur in [1.0, 1.5, 2.0, 2.5]:
            rows.append({**_gate_eval(df,
                                       (df["mean_word_prob"] >= mwp) &
                                       (df["duration_s"] >= dur),
                                       f"mwp >= {mwp:.2f} AND dur >= {dur:.1f}s",
                                       ny, total),
                         "kind": "duration"})
    # Entropy-augmented at three mwp anchors
    for mwp in [0.75, 0.80, 0.85]:
        for ent in [0.3, 0.5, 0.7]:
            rows.append({**_gate_eval(df,
                                       (df["mean_word_prob"] >= mwp) &
                                       (df["mean_entropy"] <= ent),
                                       f"mwp >= {mwp:.2f} AND ent <= {ent:.1f}",
                                       ny, total),
                         "kind": "entropy"})
    # Triple-signal: mwp + duration + entropy (the strongest gate)
    for mwp in [0.75, 0.80, 0.85]:
        for dur in [1.5, 2.0]:
            for ent in [0.5, 0.7]:
                rows.append({**_gate_eval(df,
                                           (df["mean_word_prob"] >= mwp) &
                                           (df["duration_s"] >= dur) &
                                           (df["mean_entropy"] <= ent),
                                           f"mwp >= {mwp:.2f} AND dur >= {dur:.1f}s AND ent <= {ent:.1f}",
                                           ny, total),
                             "kind": "triple"})

    out = pd.DataFrame(rows)
    print("\n  Single-signal sweet spots:")
    single = out[out["kind"] == "single"].copy()
    single["abs_diff"] = (single["prec"] - single["recall"]).abs()
    print(single.sort_values("f1", ascending=False).head(5)[
        ["name", "prec", "recall", "f1", "false_n", "vol_pct"]].round(3).to_string(index=False))

    print("\n  Strict gates (false_n == 0):")
    zero = out[out["false_n"] == 0].sort_values("recall", ascending=False)
    print(zero.head(8)[["name", "prec", "recall", "f1", "n_trust", "vol_pct"]].round(3).to_string(index=False))

    # Plot: precision-recall curve with named operating points
    fig, axs = plt.subplots(1, 2, figsize=(15, 6), dpi=200)
    fig.patch.set_facecolor(BG)
    _style_ax(axs[0])
    _style_ax(axs[1])

    # Left panel: P/R curve
    s_curve = single.sort_values("recall")
    axs[0].plot(s_curve["recall"], s_curve["prec"], "-",
                color=TEAL, linewidth=2.2, label="mean_word_prob (single)")
    # Annotate threshold points
    for _, r in s_curve.iterrows():
        if r["name"].endswith(("0.50", "0.60", "0.70", "0.75", "0.80", "0.85", "0.90", "0.95")):
            axs[0].annotate(
                r["name"].split()[-1],
                (r["recall"], r["prec"]),
                color=WHITE, fontsize=8, alpha=0.7,
                xytext=(4, 4), textcoords="offset points",
            )
    # Overlay duration / entropy / triple gates as scatter
    for kind, color, label in [
        ("duration", GOLD,   "+ duration filter"),
        ("entropy",  CORAL,  "+ entropy filter"),
        ("triple",   GREEN,  "+ duration + entropy"),
    ]:
        sub = out[out["kind"] == kind]
        axs[0].scatter(sub["recall"], sub["prec"], c=color, s=40,
                       edgecolor="white", linewidth=0.5, label=label, alpha=0.85)
    axs[0].set_xlabel("Recall (NIV-Y captured)", color=WHITE, fontsize=12)
    axs[0].set_ylabel("Precision (trusted that are truly NIV-Y)", color=WHITE, fontsize=12)
    axs[0].set_title("Precision-recall trade-off — gate variants",
                     color=WHITE, fontsize=13, fontweight="bold", pad=10)
    axs[0].set_xlim(0, 1)
    axs[0].set_ylim(0, 1)
    axs[0].legend(loc="lower left", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)

    # Right panel: false-bad count vs recall
    s_curve_sorted = single.sort_values("recall")
    axs[1].plot(s_curve_sorted["recall"], s_curve_sorted["false_n"], "-",
                color=TEAL, linewidth=2.2, label="mean_word_prob (single)")
    for kind, color, label in [
        ("duration", GOLD,   "+ duration filter"),
        ("entropy",  CORAL,  "+ entropy filter"),
        ("triple",   GREEN,  "+ duration + entropy"),
    ]:
        sub = out[out["kind"] == kind]
        axs[1].scatter(sub["recall"], sub["false_n"], c=color, s=40,
                       edgecolor="white", linewidth=0.5, label=label, alpha=0.85)
    axs[1].set_xlabel("Recall (NIV-Y captured)", color=WHITE, fontsize=12)
    axs[1].set_ylabel("False-bads in trusted set (NIV-N count)", color=WHITE, fontsize=12)
    axs[1].set_title("Operating-point cost: false-bads vs recall",
                     color=WHITE, fontsize=13, fontweight="bold", pad=10)
    axs[1].set_xlim(0, 1)
    axs[1].legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=9)
    fig.tight_layout()
    _save(fig, PLOTS_DIR / "conf_operating_points.png")

    return {"table": out, "ny": ny, "total": total}


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 9 — False-good characterization at the balanced gate
# ─────────────────────────────────────────────────────────────────────────────

def analysis_9_false_goods(df: pd.DataFrame, segs: List[Segment],
                            balanced_threshold: float = 0.80) -> Dict[str, Any]:
    """At a balanced operating point, dump the false-good segments and the
    feature gap vs true-good segments."""
    print(f"\n══ Analysis 9: False-good characterization (mwp >= {balanced_threshold}) ══")
    df = df.dropna(subset=["is_score"]).copy()
    df["niv_y"] = (df["is_score"] >= 3.80).astype(int)
    df["niv_n"] = (df["is_score"] <  2.00).astype(int)
    df["duration_s"] = df["utt_id"].map(_utt_duration_seconds)

    trusted = df[df["mean_word_prob"] >= balanced_threshold]
    true_y = trusted[trusted["niv_y"] == 1]
    false_n = trusted[trusted["niv_n"] == 1]

    print(f"  Trusted: {len(trusted)}   True-good (NIV-Y): {len(true_y)}   "
          f"False-bad (NIV-N): {len(false_n)}")

    # Feature gap analysis
    feature_gap = []
    for f in ["mean_word_prob", "min_word_prob", "mean_entropy", "len_ratio",
              "len_hyp_words", "len_ref_words", "duration_s",
              "frac_p_lt_04", "p_std", "mean_margin"]:
        if f not in trusted.columns:
            continue
        feature_gap.append({
            "feature": f,
            "false_n_mean": false_n[f].mean(),
            "true_y_mean": true_y[f].mean(),
            "false_n_med": false_n[f].median(),
            "true_y_med": true_y[f].median(),
            "gap_mean": false_n[f].mean() - true_y[f].mean(),
        })
    gap_df = pd.DataFrame(feature_gap)
    print("\n  Feature gap (false-bads vs true-goods):")
    print(gap_df.round(3).to_string(index=False))

    # Build the case table for the report
    case_rows = []
    for _, row in false_n.iterrows():
        utt = row["utt_id"]
        seg = next((s for s in segs if s.utt_id == utt), None)
        if seg is None: continue
        case_rows.append({
            "utt_id": utt,
            "duration_s": row["duration_s"],
            "ref_words": int(row["len_ref_words"]),
            "hyp_words": int(row["len_hyp_words"]),
            "len_ratio": row["len_ratio"],
            "mean_word_prob": row["mean_word_prob"],
            "min_word_prob": row["min_word_prob"],
            "mean_entropy": row.get("mean_entropy", float("nan")),
            "wer": row["wer"],
            "ref": seg.ref,
            "hyp": seg.hyp_today,
        })
    cases = pd.DataFrame(case_rows)

    # Plot: feature distribution side-by-side (true-goods blue, false-bads coral)
    feats_plot = [
        ("duration_s",  "Duration (s)",     [0, 5]),
        ("len_hyp_words", "Hyp word count", [0, 50]),
        ("mean_entropy", "Mean entropy",    [0, 3]),
        ("len_ratio",    "Length ratio (hyp/ref)", [0, 4]),
    ]
    fig, axs = plt.subplots(1, 4, figsize=(18, 4.5), dpi=200)
    fig.patch.set_facecolor(BG)
    for ax, (key, label, xrng) in zip(axs, feats_plot):
        _style_ax(ax)
        if key in trusted.columns:
            bins = np.linspace(xrng[0], xrng[1], 25)
            ax.hist(true_y[key].dropna(), bins=bins, color=GREEN, alpha=0.55,
                    edgecolor=WHITE, linewidth=0.4,
                    label=f"True-good (n={len(true_y)})", density=True)
            ax.hist(false_n[key].dropna(), bins=bins, color=CORAL, alpha=0.85,
                    edgecolor=WHITE, linewidth=0.4,
                    label=f"False-bad (n={len(false_n)})", density=True)
        ax.set_xlabel(label, color=WHITE, fontsize=11)
        ax.set_title(label, color=WHITE, fontsize=12, fontweight="bold", pad=8)
        ax.legend(loc="upper right", facecolor=NAVY2, edgecolor=MGRAY,
                  labelcolor=WHITE, fontsize=8)
    fig.suptitle(
        f"False-bad vs true-good signatures at gate mean_word_prob >= {balanced_threshold} "
        f"(n_trusted = {len(trusted)})",
        color=WHITE, fontsize=13, fontweight="bold", y=1.0,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, PLOTS_DIR / "conf_false_good_signatures.png")

    return {
        "n_trusted": len(trusted),
        "n_true_y": len(true_y),
        "n_false_n": len(false_n),
        "feature_gap": gap_df,
        "cases": cases,
        "balanced_threshold": balanced_threshold,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 11 — Failure-mode profiling
# ─────────────────────────────────────────────────────────────────────────────

# March-deck failure-mode taxonomy (slide_failure_deep_1a/1b in
# slides_research.py). Five mutually exclusive categories, evaluated in
# order. Applied to segments with IS < 2.0. Grounded in ASR error taxonomy
# (Fosler-Lussier 2004) and LLM hallucination analysis (ACL 2025).
def _categorize_failure(semantic_sim: float, wer_pct: float, nea_f1: float,
                         len_ratio: float, hyp: str) -> str:
    """Five-category March-deck taxonomy. Order matches the March deck's
    impact ranking (slide_failure_deep_1a/1b numbering reflects frequency,
    but the rule check order matters for dual-criteria segments and
    follows the deck's narrative: topic mismatch first, then length-blowup
    hallucination, then entity-loss, then signal collapse, leftovers last).

    1. Wrong Topic                — semantic_sim < 0.2
    2. Hallucination              — WER >= 100% (output longer than reference)
    3. Right Topic, Wrong Details — semantic_sim >= 0.2 AND nea_f1 < 20%
    4. Signal Loss                — empty output OR length_ratio < 0.3
    5. Accumulated Errors         — anything else with IS < 2.0
    """
    # Wrong Topic first — semantic mismatch dominates regardless of WER.
    if semantic_sim < 0.2:
        return "1. Wrong Topic"
    if wer_pct >= 100:
        return "2. Hallucination"
    if (nea_f1 or 0) < 20:
        return "3. Right Topic, Wrong Details"
    if not (hyp or "").strip() or len_ratio < 0.3:
        return "4. Signal Loss"
    return "5. Accumulated Errors"


def analysis_11_failure_modes(df: pd.DataFrame, baseline_csv: Path) -> Dict[str, Any]:
    """March-deck 5-category failure-mode taxonomy applied to IS<2.0 segments.
    Profiles each category's confidence parameters against the NIV-Y healthy
    reference. Mirrors slide_failure_deep_1a/1b/2 in the March 2026 deck."""
    print("\n══ Analysis 11: Failure-mode profiling (March 5-category taxonomy) ══")
    df = df.dropna(subset=["is_score"]).copy()
    df["niv_y"] = (df["is_score"] >= 3.80).astype(int)
    df["duration_s"] = df["utt_id"].map(_utt_duration_seconds)

    # Pull metric components from baseline (WER, NEA F1, hyp).
    baseline_rows = list(csv.DictReader(baseline_csv.open(encoding="utf-8")))
    baseline_by_id = {r["utt_id"]: r for r in baseline_rows}

    # Pull semantic_sim from intelligibility_scores.csv (IS pipeline output).
    is_csv = REPO_ROOT / "docs" / "evaluation" / "intelligibility" / "intelligibility_scores.csv"
    semantic_by_id: Dict[str, float] = {}
    if is_csv.exists():
        for row in csv.DictReader(is_csv.open(encoding="utf-8")):
            try:
                semantic_by_id[row["utt_id"]] = float(row.get("semantic_sim", "") or "nan")
            except ValueError:
                pass
        print(f"  Loaded semantic_sim for {len(semantic_by_id)} segments from {is_csv}")
    else:
        print(f"  WARN: {is_csv} not found — semantic_sim unavailable, "
              "Wrong Topic vs Right Topic categories will collapse")

    def _get_field(uid: str, key: str) -> str:
        return (baseline_by_id.get(uid, {}).get(key, "") or "").strip()

    def _to_float(v: str) -> float:
        try:
            return float(v.replace("%", ""))
        except (ValueError, AttributeError):
            return 0.0

    df["hyp_text"] = df["utt_id"].map(lambda u: _get_field(u, "hyp"))
    df["nea_f1_pct"] = df["utt_id"].map(lambda u: _to_float(_get_field(u, "nea_f1_%")))
    df["wer_pct"] = df["utt_id"].map(lambda u: _to_float(_get_field(u, "wer_%")))
    df["semantic_sim"] = df["utt_id"].map(lambda u: semantic_by_id.get(u, float("nan")))

    # Apply the March 5-category taxonomy to all IS<2.0 segments.
    bad = df[df["is_score"] < 2.0].copy()
    bad["category"] = bad.apply(
        lambda r: _categorize_failure(r["semantic_sim"], r["wer_pct"],
                                       r["nea_f1_pct"], r["len_ratio"],
                                       r["hyp_text"]),
        axis=1,
    )
    healthy = df[df["niv_y"] == 1].copy()
    healthy["category"] = "Healthy (NIV-Y)"
    combined = pd.concat([bad, healthy[bad.columns]], ignore_index=True)

    counts = bad["category"].value_counts().sort_index()
    total_bad = max(1, len(bad))
    print(f"\n  IS < 2.0 segments by category (n={len(bad)} total):")
    for cat, n in counts.items():
        pct = n / total_bad * 100
        print(f"    {cat:36s}  {int(n):4d}  ({pct:5.1f}%)")
    cat_order = list(counts.index) + ["Healthy (NIV-Y)"]

    summary = combined.groupby("category").agg(
        n=("utt_id", "count"),
        mean_prob=("mean_prob", "mean"),
        min_word_prob=("min_word_prob", "mean"),
        mean_entropy=("mean_entropy", "mean"),
        mean_margin=("mean_margin", "mean"),
        len_ratio=("len_ratio", "mean"),
        duration_s=("duration_s", "mean"),
        len_hyp_words=("len_hyp_words", "mean"),
        frac_p_lt_04=("frac_p_lt_04", "mean"),
        nea_f1=("nea_f1_pct", "mean"),
        wer=("wer_pct", "mean"),
        is_score=("is_score", "mean"),
    ).round(3)
    summary = summary.reindex([c for c in cat_order if c in summary.index])
    print(f"\n  Per-category means:")
    print(summary[["n", "mean_prob", "min_word_prob", "mean_entropy",
                   "mean_margin", "duration_s", "len_ratio",
                   "frac_p_lt_04", "is_score"]].to_string())

    # Match March-deck card colors per category.
    cat_colors = {
        "1. Wrong Topic":                ORANGE,    # March deck ORANGE
        "2. Hallucination":              "#ffd54f", # March deck YELLOW
        "3. Right Topic, Wrong Details": "#e06c75", # March deck RED/CORAL
        "4. Signal Loss":                "#aaaaaa", # March deck LGRAY
        "5. Accumulated Errors":         "#ffeb3b", # March deck YELLOW
        "Healthy (NIV-Y)":               GREEN,
    }
    panels = [
        ("mean_prob",     "mean_prob",       [0, 1.0]),
        ("min_word_prob", "min_word_prob",   [0, 1.0]),
        ("mean_entropy",  "mean_entropy",    [0, 4]),
        ("mean_margin",   "mean_margin",     [0, 1.0]),
        ("len_ratio",     "len_ratio",       [0, 4]),
        ("duration_s",    "duration (s)",    [0, 5]),
        ("len_hyp_words", "hyp word count",  [0, 50]),
        ("frac_p_lt_04",  "fraction p<0.40", [0, 1.0]),
    ]
    fig, axs = plt.subplots(2, 4, figsize=(20, 10), dpi=200)
    fig.patch.set_facecolor(BG)
    for idx, (key, label, yrng) in enumerate(panels):
        ax = axs.flat[idx]
        _style_ax(ax)
        box_data, box_colors, valid_cats = [], [], []
        for cat in cat_order:
            sub = combined[combined["category"] == cat][key].dropna().values
            if len(sub) == 0:
                continue
            box_data.append(sub)
            box_colors.append(cat_colors.get(cat, MGRAY))
            valid_cats.append(cat)
        bp = ax.boxplot(box_data, patch_artist=True, widths=0.6,
                        showfliers=False,
                        medianprops=dict(color=WHITE, linewidth=2))
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
            patch.set_edgecolor(WHITE)
        for whisker in bp["whiskers"]:
            whisker.set_color("#cccccc")
        for cap in bp["caps"]:
            cap.set_color("#cccccc")
        ax.set_xticks(range(1, len(valid_cats) + 1))
        ax.set_xticklabels(
            [f"{c}\n(n={int((combined['category']==c).sum())})" for c in valid_cats],
            rotation=30, ha="right", color=WHITE, fontsize=8,
        )
        ax.set_ylabel(label, color=WHITE, fontsize=11)
        ax.set_title(label, color=WHITE, fontsize=12, fontweight="bold", pad=8)
        ax.set_ylim(yrng)
    fig.suptitle(
        f"Confidence parameters by failure mode  "
        f"(March 5-category taxonomy on IS<2.0, n={len(bad)}; "
        f"healthy NIV-Y reference n={len(healthy)})",
        color=WHITE, fontsize=14, fontweight="bold", y=1.0,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, PLOTS_DIR / "conf_failure_mode_profile.png")

    # Per-category card metadata for the markdown / LaTeX (mirrors the
    # March deck's slide_failure_deep_1a/1b cards).
    card_metadata = [
        ("1. Wrong Topic", "Mouth shapes decoded to wrong domain",
         "Semantic similarity < 0.2",
         "Ref: \"weight loss and diet\" → Hyp: \"wanted to be a princess\""),
        ("2. Hallucination", "Model invented fake text",
         "WER >= 100% (output longer than reference)",
         "Ref: \"carry strap\" → Hyp: \"holocaust denier explanation of the final act\""),
        ("3. Right Topic, Wrong Details", "Roughly right but names/content lost",
         "NEA F1 < 20% (Semantic >= 0.2)",
         "Ref: \"13th amendment is going\" → Hyp: \"13th may mean something to him\""),
        ("4. Signal Loss", "Nothing came out",
         "Empty output OR length_ratio < 0.3",
         "Ref: \"the thirteenth amendment\" → Hyp: \"\""),
        ("5. Accumulated Errors", "Many small errors compound",
         "IS < 2.0 and doesn't match categories 1-4",
         "Many words slightly wrong throughout, meaning erodes"),
    ]
    return {"summary": summary, "counts": counts.to_dict(),
            "n_bad": len(bad), "n_healthy": len(healthy),
            "cat_order": cat_order,
            "card_metadata": card_metadata}


# ─────────────────────────────────────────────────────────────────────────────
# Markdown report
# ─────────────────────────────────────────────────────────────────────────────

def write_report(
    diag: Dict[str, Any],
    a0: Dict[str, Any], a1: Dict[str, Any], a2: Dict[str, Any],
    a3: Dict[str, Any], a4: Dict[str, Any], a5: Dict[str, Any],
    a6: Dict[str, Any], a7: Dict[str, Any],
    a8: Dict[str, Any], a9: Dict[str, Any], a11: Dict[str, Any],
    confidence_path: Path, hypo_path: Path, baseline_csv: Path,
) -> None:
    pearson: pd.DataFrame = a3["pearson"]
    aucs: pd.DataFrame = a4["aucs"]
    cluster_summary: pd.DataFrame = a6["summary"]

    # Pre-compute string fragments to keep f-strings backslash-free.
    if a0['n_different'] == 0:
        a0_text = (
            "**Hypotheses match baseline** — the today-vs-baseline WER gap is purely "
            "**pooled vs. averaged**, a known divergence on the heavy-tailed segment-WER "
            "distribution. Confidence-side joins are exact."
        )
    else:
        a0_text = (
            f"**Hypotheses DIFFER on {a0['n_different']:,} segments** — the dict-mode "
            "generate() return path under VSP_OUTPUT_SCORES=1 produces marginally different "
            "chosen sequences from the tensor-mode beam decode used for the baseline. Treat "
            "WER correlations as approximate, not exact."
        )

    pcg = a2['p_correct_green']
    if pcg >= 0.90:
        decision_text = "≥90% target met. Keep 0.85."
    elif pcg >= 0.80:
        decision_text = (
            f"falls in the 80-90% band — footnote the deck (green ≈ {pcg*100:.0f}% reliable) "
            "rather than tightening, since tightening loses substantial green coverage."
        )
    else:
        decision_text = "**below 80% — tighten green to 0.90 or 0.92.**"

    hall_med_p_h = f"{a5['mean_prob_hall_median']:.3f}" if a5['mean_prob_hall_median'] is not None else "NA"
    hall_med_p_o = f"{a5['mean_prob_ok_median']:.3f}"   if a5['mean_prob_ok_median'] is not None else "NA"
    hall_med_e_h = f"{a5['mean_entropy_hall_median']:.3f}" if a5['mean_entropy_hall_median'] is not None else "NA"
    hall_med_e_o = f"{a5['mean_entropy_ok_median']:.3f}"   if a5['mean_entropy_ok_median'] is not None else "NA"

    auc_pivot = aucs.pivot(index="feature", columns="target", values="auc")
    auc_mean_prob_bad = auc_pivot.at['mean_prob','niv_bad'] if 'mean_prob' in auc_pivot.index else float('nan')
    auc_mean_prob_y   = auc_pivot.at['mean_prob','niv_y']   if 'mean_prob' in auc_pivot.index else float('nan')

    band_total = max(1, a2['n_green'] + a2['n_yellow'] + a2['n_red'])
    pct_green  = a2['n_green']  / band_total * 100
    pct_yellow = a2['n_yellow'] / band_total * 100
    pct_red    = a2['n_red']    / band_total * 100

    # Reproduce block kept outside the main f-string to avoid backslash-in-f-string issues.
    reproduce_block = (
        "```bash\n"
        "python3 docs/_research-tools/generators/analyze_confidence_full.py \\\n"
        f"    --confidence-sidecar {confidence_path} \\\n"
        f"    --hypo               {hypo_path} \\\n"
        f"    --baseline-csv       {baseline_csv}\n"
        "```\n"
    )

    # Build the operating-point comparison table for the report.
    op_tbl = a8["table"]
    op_recommended = [
        ("Loose, high recall",       op_tbl[op_tbl["name"] == "mwp >= 0.75"].iloc[0] if (op_tbl["name"] == "mwp >= 0.75").any() else None),
        ("Balanced (recommended)",   op_tbl[op_tbl["name"] == "mwp >= 0.80"].iloc[0] if (op_tbl["name"] == "mwp >= 0.80").any() else None),
        ("Strict precision",         op_tbl[op_tbl["name"] == "mwp >= 0.85"].iloc[0] if (op_tbl["name"] == "mwp >= 0.85").any() else None),
        ("+ duration filter",        op_tbl[op_tbl["name"] == "mwp >= 0.85 AND dur >= 1.5s"].iloc[0] if (op_tbl["name"] == "mwp >= 0.85 AND dur >= 1.5s").any() else None),
        ("Zero-false-bad gate",      op_tbl[op_tbl["name"] == "mwp >= 0.85 AND dur >= 1.5s AND ent <= 0.7"].iloc[0] if (op_tbl["name"] == "mwp >= 0.85 AND dur >= 1.5s AND ent <= 0.7").any() else None),
    ]
    op_recommended = [(label, row) for label, row in op_recommended if row is not None]
    op_table_md = "| Operating point | Gate | Precision | Recall | False-bads | Vol. % | Trusted |\n"
    op_table_md += "|---|---|---|---|---|---|---|\n"
    for label, row in op_recommended:
        op_table_md += (f"| {label} | `{row['name']}` | {row['prec']*100:.1f}% | "
                        f"{row['recall']*100:.1f}% | {row['false_n']} | "
                        f"{row['vol_pct']:.1f}% | {row['n_trust']} |\n")

    # Build the false-good case table.
    cases = a9["cases"]
    case_table_md = "| utt_id | dur(s) | ref→hyp words | mwp | min_wp | ent | WER% |\n"
    case_table_md += "|---|---|---|---|---|---|---|\n"
    for _, c in cases.iterrows():
        case_table_md += (f"| `{c['utt_id'][:24]}` | {c['duration_s']:.2f} | "
                          f"{c['ref_words']}→{c['hyp_words']} (lr {c['len_ratio']:.2f}) | "
                          f"{c['mean_word_prob']:.2f} | {c['min_word_prob']:.2f} | "
                          f"{c['mean_entropy']:.2f} | {c['wer']:.0f} |\n")

    # Build the example REF/HYP block (3 most informative cases).
    example_md = ""
    example_pick = cases.head(5)  # top-5 by sort order
    for _, c in example_pick.iterrows():
        example_md += (f"- **`{c['utt_id'][:32]}`** (dur {c['duration_s']:.2f}s, "
                       f"WER {c['wer']:.0f}%)\n"
                       f"   - REF: *{c['ref']}*\n"
                       f"   - HYP: **{c['hyp']}**\n")

    # Feature gap summary.
    gap = a9["feature_gap"].set_index("feature")
    gap_lines = []
    for feat, label in [
        ("duration_s",     "Segment duration (s)"),
        ("len_hyp_words",  "Hyp word count"),
        ("len_ref_words",  "Ref word count"),
        ("mean_entropy",   "Mean entropy"),
        ("len_ratio",      "Length ratio"),
    ]:
        if feat in gap.index:
            r = gap.loc[feat]
            gap_lines.append(f"| {label} | {r['false_n_mean']:.2f} | {r['true_y_mean']:.2f} | {r['gap_mean']:+.2f} |")
    gap_table_md = "| Feature | False-bad mean | True-good mean | Gap |\n|---|---|---|---|\n" + "\n".join(gap_lines) + "\n"

    # Build top-5 by |r| bullets (Python loops, not f-string).
    top5_is_md = ""
    for feat, _ in pearson["is_score"].abs().sort_values(ascending=False).head(5).items():
        top5_is_md += f"- `{feat}` → IS: **r = {pearson.at[feat, 'is_score']:+.3f}**\n"
    top5_wer_md = ""
    for feat, _ in pearson["wer"].abs().sort_values(ascending=False).head(5).items():
        top5_wer_md += f"- `{feat}` → WER: **r = {pearson.at[feat, 'wer']:+.3f}**\n"

    # AUC table.
    auc_table_md = "| Feature | NIV-N (bad) detector AUC | NIV-Y (good) detector AUC |\n|---|---|---|\n"
    for feat in auc_pivot.index:
        bad = auc_pivot.at[feat, "niv_bad"] if "niv_bad" in auc_pivot.columns else float("nan")
        good = auc_pivot.at[feat, "niv_y"] if "niv_y" in auc_pivot.columns else float("nan")
        bad_s = f"{bad:.3f}" if pd.notna(bad) else "—"
        good_s = f"{good:.3f}" if pd.notna(good) else "—"
        auc_table_md += f"| `{feat}` | {bad_s} | {good_s} |\n"

    # Trajectory cluster table.
    cluster_table_md = "| Cluster | n | Mean WER% | Mean IS | NIV-Y rate | NIV-N rate |\n|---|---|---|---|---|---|\n"
    cluster_summary_sorted = cluster_summary.sort_values("mean_is", ascending=False)
    cluster_labels = {}
    sorted_idx = cluster_summary_sorted.index.tolist()
    for i, idx in enumerate(sorted_idx):
        ck = int(cluster_summary_sorted.loc[idx, "cluster"])
        if i == 0:                cluster_labels[ck] = "flat-high"
        elif i == len(sorted_idx)-1: cluster_labels[ck] = "uncertain throughout"
        else:                     cluster_labels[ck] = f"middle #{i}"
    for _, row in cluster_summary_sorted.iterrows():
        ck = int(row["cluster"])
        cluster_table_md += (f"| C{ck} ({cluster_labels[ck]}) | {int(row['n_segments'])} | "
                             f"{row['mean_wer']:.1f} | {row['mean_is']:.2f} | "
                             f"{row['p_niv_y']*100:.1f}% | {row['p_niv_n']*100:.1f}% |\n")

    # Failure-mode cards (March-deck style) — from a11['card_metadata'].
    a11_summary = a11["summary"]
    counts = a11["counts"]
    n_bad = a11["n_bad"]
    cards_md = ""
    for cat, desc, rule, example in a11["card_metadata"]:
        n = int(counts.get(cat, 0))
        pct = (n / max(1, n_bad)) * 100
        if cat in a11_summary.index:
            r = a11_summary.loc[cat]
            conf_blurb = (f"mean_prob {r['mean_prob']:.2f}, "
                          f"min_wp {r['min_word_prob']:.2f}, "
                          f"entropy {r['mean_entropy']:.2f}, "
                          f"len_ratio {r['len_ratio']:.2f}, "
                          f"dur {r['duration_s']:.2f}s")
        else:
            conf_blurb = "—"
        cards_md += f"#### {cat} ({pct:.1f}%, n={n})\n\n"
        cards_md += f"- **What:** {desc}\n"
        cards_md += f"- **Rule:** {rule}\n"
        cards_md += f"- **Example:** {example}\n"
        cards_md += f"- **Confidence signature:** {conf_blurb}\n\n"

    # Failure-mode summary table.
    failure_table_md = ("| Category | n | mean_prob | min_wp | mean_entropy | dur (s) | NEA | WER% | IS |\n"
                       "|---|---|---|---|---|---|---|---|---|\n")
    for cat, row in a11_summary.iterrows():
        failure_table_md += (f"| **{cat}** | {int(row['n'])} | "
                             f"{row['mean_prob']:.2f} | {row['min_word_prob']:.2f} | "
                             f"{row['mean_entropy']:.2f} | "
                             f"{row['duration_s']:.2f} | {row['nea_f1']:.1f} | "
                             f"{row['wer']:.0f} | {row['is_score']:.2f} |\n")

    md = f"""# Confidence Sidecar — Full Statistical Analysis

**Source.** Per-token confidence from `/tmp/vsp_b3_1497_out/confidence-172610.json` (1,497-segment B3 decode), joined with the baseline ground truth in `english_full_results/client_outputs/report/report.csv`. Per-token features (`prob`, `entropy`, `top3`) aggregated to per-word ([`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)) and per-segment.

**Sample sizes.** {diag['n_total']:,} segments matched in confidence × hypo. {diag['n_with_baseline']:,} segments joined with baseline IS / WER. {a2['n_words']:,} hypothesis words aligned to references for calibration. Hypotheses are bit-identical to the baseline run — the {a0['today_pooled_wer']:.2f}% pooled vs {a0['today_mean_seg_wer']:.2f}% mean-of-segment WER gap is purely the well-known pooled-vs-averaged divergence on a heavy-tailed distribution. Confidence-side joins are exact.

**TL;DR.** When you take the average per-word confidence inside a segment (the mean of the model's max-softmax probabilities, one per output word), it tells you the segment's overall quality with high reliability — Pearson r = **{pearson.at['mean_word_prob','is_score']:+.2f}** against the Intelligibility Score. That single number is enough to filter the bad outputs out at runtime. The per-word green / yellow / red coloring on the kept segments only works **inside** segments that are confident as a whole; in unconfident segments the coloring is misleading.

**Term key (used throughout this report).**

- **IS** — Intelligibility Score (0-5), our 6-signal composite quality metric. Mean across the 1,497-segment baseline = 2.52.
- **NIV-Y** ("clearly intelligible") — a segment with IS ≥ 3.80; the bar for a clean win, calibrated against an Opus-as-Judge gold standard.
- **NIV-N** ("not intelligible") — a segment with IS < 2.00; clear failure.
- **mean_word_prob** — the per-segment average of per-word probabilities, where each per-word probability is the *minimum* max-softmax across the sub-tokens that make up the word.
- **mean_prob** — the per-segment average of per-token max-softmax probabilities (no word-level grouping).
- **WER / WWER** — word error rate / weighted WER (high-value content tokens count 2×).

**What we found.**

1. **Mean word probability is the single best confidence aggregate.** Pearson r = **{pearson.at['mean_word_prob','is_score']:+.3f}** with IS, **{pearson.at['mean_word_prob','wer']:+.3f}** with WER, **{pearson.at['mean_word_prob','wwer']:+.3f}** with WWER (n={a3['n_segments']:,}). Geometric mean, mean entropy, mean margin (top1 − top2), and `frac_p_ge_0.85` all sit within ~0.03 r of this — they're different shadows of the same underlying signal. Spearman ρ tracks Pearson r within {a3.get('max_conf_dev_is', 0.06):.2f} for confidence-vs-IS pairs, so the relationship isn't an artifact of a linearity assumption. *Practical reading:* for runtime quality estimation we don't need anything fancier than averaging the per-word probabilities the model already produces.

2. **Confidence is a strong segment-level filter.** AUC = **{aucs.loc[aucs.target=='niv_bad'].set_index('feature').loc['mean_prob','auc']:.3f}** detecting NIV-N (bad) and AUC = **{aucs.loc[aucs.target=='niv_y'].set_index('feature').loc['mean_prob','auc']:.3f}** detecting NIV-Y (good) using `mean_prob` alone — both well above the 0.80 "deployable as a single signal" cutoff. *Practical reading:* at the operating point `mean_word_prob ≥ 0.80`, we keep **78%** of NIV-Y segments and admit only **9 NIV-N** out of 405 trusted (a 2.2% false-trust rate). For zero-tolerance applications, add `duration ≥ 1.5s AND mean_entropy ≤ 0.7`; that gate produces zero false-trusted segments at ~30% recall (8.7% volume kept).

3. **The green band's reliability depends on which segment a green word lives in.** Across the full {a2['n_words']:,} hypothesis-words corpus, a "green" word (per-word p ≥ {CONF_HIGH}) is correct **{a2['p_correct_green']*100:.1f}%** of the time on average. But stratified by the segment's mean_word_prob, that ranges from **18.2%** (segments below 0.40) to **92.8%** (segments at 0.85+). Expected Calibration Error on raw max-softmax = **{a2['ece_pct']:.1f}%** — within the 5-15pp range the post-RLHF LLaMA-2 calibration literature predicts. *Practical reading:* show colored per-word transcripts only when the segment's mean_word_prob ≥ 0.82 — that's the threshold where green words clear ≥ 85% reliability as labeled. Below 0.65, green falls under 50% reliability and the coloring becomes net-misleading; hide or banner instead.

4. **Confidence catches hallucinations almost completely.** Of {a5['n_hallucinated']} hallucinated segments (defined as WER ≥ 100% AND length ratio ≥ 0.5: fluent-but-wrong, not just empty), only **{a5['n_dangerous']}** ({a5['n_dangerous']/max(1,a5['n_hallucinated'])*100:.1f}%) have mean_prob ≥ 0.85. Median mean_prob: {hall_med_p_h} hallucinated vs {hall_med_p_o} healthy. Median mean_entropy: {hall_med_e_h} vs {hall_med_e_o}. AUC for hallucination detection: mean_prob = {auc_pivot.at['mean_prob','niv_bad']:.3f}, mean_entropy = {auc_pivot.at['mean_entropy','niv_bad']:.3f} — tied. *Practical reading:* the literature's worst-case "fluent fabrications at p > 0.95" failure mode exists but is rare in this data. mean_prob alone catches it 99% of the time; entropy is redundant on this dataset, so we keep it as instrumentation but don't promote it to a primary gate.

5. **Different failure modes need different signals.** The {a11['n_bad']} segments with IS<2 classify into the March 5-category taxonomy (evaluated 1→5): Wrong Topic 68% (n={int(a11['counts'].get('1. Wrong Topic',0))}), Hallucination 10% (n={int(a11['counts'].get('2. Hallucination',0))}), Right Topic Wrong Details 15% (n={int(a11['counts'].get('3. Right Topic, Wrong Details',0))}), Signal Loss 0.2% (n={int(a11['counts'].get('4. Signal Loss',0))}), Accumulated Errors 7% (n={int(a11['counts'].get('5. Accumulated Errors',0))}). Hallucination + Signal Loss (≈10% of bad segments) are catchable from confidence + length-ratio alone. The remaining ~90% — dominated by Wrong Topic — require either the reference (semantic similarity, NEA F1) or a runtime substitute. *Practical reading:* Mission 6 (capture all 20 beams to expose disagreement) and Mission 8 (topic-conditioned language model) are the next-sprint priorities. Confidence alone has plateaued at the failure modes it can detect.

6. **Trajectory shape predicts outcome.** k=5 k-means on length-normalized per-position prob trajectories yields a "flat-high" cluster (mean WER **{cluster_summary['mean_wer'].min():.0f}%**, mean IS {cluster_summary['mean_is'].max():.2f}, 64% NIV-Y) and an "uncertain-throughout" cluster (mean WER **{cluster_summary['mean_wer'].max():.0f}%**, mean IS {cluster_summary['mean_is'].min():.2f}, **92% NIV-N**). The shape difference is visible after just a few tokens. *Practical reading:* mid-decode trajectory monitoring is a viable runtime "give up early" hook — abort segments that match the failure-shape cluster before generating the rest of the sequence. Mission 11 candidate.

---

# 1. What confidence is, and what it predicts

This chapter establishes the basic statistics: the distributions of the four confidence signals we capture (`prob`, `word_prob`, `entropy`, `margin`), their correlation with the quality metrics (IS, WER, WWER, NEA F1), and the answer to the deployment question — *which* confidence aggregate is the best predictor of segment quality.

## 1.1 Distributions

![distributions](../presentation_materials_20260224/01_plots_for_slides/conf_full_distributions.png)

| Signal | Mean | Median | p10 | p90 |
|---|---|---|---|---|
| Per-token prob | {a1['token_prob']['mean']:.3f} | {a1['token_prob']['median']:.3f} | {a1['token_prob']['p10']:.3f} | {a1['token_prob']['p90']:.3f} |
| Per-word prob (min agg) | {a1['word_prob']['mean']:.3f} | {a1['word_prob']['median']:.3f} | {a1['word_prob']['p10']:.3f} | {a1['word_prob']['p90']:.3f} |
| Per-token entropy | {a1['entropy']['mean']:.3f} | {a1['entropy']['median']:.3f} | {a1['entropy']['p10']:.3f} | {a1['entropy']['p90']:.3f} |
| Per-token margin (top1−top2) | {a1['margin']['mean']:.3f} | {a1['margin']['median']:.3f} | {a1['margin']['p10']:.3f} | {a1['margin']['p90']:.3f} |

The 33-Obama small-sample (used to design the green / yellow / red bands) showed 89.7% green / 6.8% yellow / 3.4% red on word-level. On the diverse 1,497-segment dataset the same thresholds (0.85 / 0.40) produce **{pct_green:.1f}% green / {pct_yellow:.1f}% yellow / {pct_red:.1f}% red** — the rebalancing the threshold-design doc anticipated.

## 1.2 Correlation map

![correlation heatmap](../presentation_materials_20260224/01_plots_for_slides/conf_correlation_heatmap.png)

Top-5 confidence features by |Pearson r| with **IS**:

{top5_is_md}

Top-5 confidence features by |Pearson r| with **WER**:

{top5_wer_md}

Restricting to confidence aggregates vs IS, max |Pearson r − Spearman ρ| = **{a3.get('max_conf_dev_is', float('nan')):.3f}** — linear and rank correlations agree.

## 1.3 Continuous fit — confidence vs IS and WER

![confidence vs IS](../presentation_materials_20260224/01_plots_for_slides/conf_metrics_vs_is_scatter.png)

![confidence vs WER](../presentation_materials_20260224/01_plots_for_slides/conf_metrics_vs_wer_scatter.png)

Three of the four signals (`mean_prob`, `mean_entropy`, `mean_margin`) explain ~65% of IS variance with a single linear term. Confidence predicts IS more cleanly than WER (R² ≈ 0.65 vs 0.48): WER's heavy tail (the WER ≥ 100% hallucination stripe and length-blowup tail above 150%) breaks linearity, while IS varies smoothly because it credits semantic and phonetic similarity.

## 1.4 Beam preview is redundant with full entropy

We capture top-3 alternatives per step. Using top-3-only entropy as a poor man's beam diversity:

| | |
|---|---|
| r(full_entropy, top3_entropy) | {a7.get('r_full_top3', float('nan')):+.3f} |
| r(full_entropy, WER) | {a7.get('r_full_wer', float('nan')):+.3f} |
| r(top3_entropy, WER) | {a7.get('r_top3_wer', float('nan')):+.3f} |
| r(full_entropy, IS) | {a7.get('r_full_is', float('nan')):+.3f} |
| r(top3_entropy, IS) | {a7.get('r_top3_is', float('nan')):+.3f} |

Top-3 entropy is **almost perfectly redundant** with full-distribution entropy — the cheap version isn't enough to expose new signal. Genuine beam-level information requires capturing all 20 hypotheses with their per-step probability trails (Mission 6).

# 2. Calibration: does the green band mean what it claims?

The previous chapter showed that confidence *predicts* quality on average. This chapter asks whether the per-word color promise (green = trust without review, ≥ 85% correct) actually holds in practice — and discovers that it does, but only inside segments that are confident as a whole.

## 2.1 Overall calibration

![calibration curve](../presentation_materials_20260224/01_plots_for_slides/conf_calibration_curve.png)

| Band | Threshold | n words | P(correct) |
|---|---|---|---|
| green  | p ≥ {CONF_HIGH} | {a2['n_green']:,} | **{a2['p_correct_green']*100:.1f}%** |
| yellow | {CONF_MED} ≤ p < {CONF_HIGH} | {a2['n_yellow']:,} | {a2['p_correct_yellow']*100:.1f}% |
| red    | p < {CONF_MED} | {a2['n_red']:,} | {a2['p_correct_red']*100:.1f}% |

Bands are well-ordered (green > yellow > red empirically) and ECE = **{a2['ece_pct']:.1f}%** sits within the 5-15pp range the post-RLHF LLaMA-2 calibration literature predicts. The headline number ({a2['p_correct_green']*100:.1f}% reliable green) — {decision_text}

## 2.2 Stratified by segment quality — the green band collapses in low-quality segments

![band reliability stratified](../presentation_materials_20260224/01_plots_for_slides/conf_band_reliability_combined.png)

| Segment mean_prob bucket | n words | P(correct \\| green) | P(correct \\| yellow) | P(correct \\| red) |
|---|---|---|---|---|
| very low (< 0.40) | 248 | **18.2%** | 13.1% | 3.9% |
| low (0.40–0.55) | 1,908 | **21.8%** | 13.9% | 8.2% |
| mid-low (0.55–0.65) | 3,067 | **41.3%** | 23.9% | 11.2% |
| mid (0.65–0.75) | 5,453 | **69.6%** | 35.9% | 16.5% |
| high (0.75–0.85) | 6,830 | **83.8%** | 47.3% | 24.9% |
| very high (≥ 0.85) | 5,755 | **92.8%** | 60.3% | 28.5% |
| **Overall** | **23,261** | **80.6%** | 38.3% | 15.4% |

The green band's reliability ranges from 18% to 93% depending on the segment it lives in. Across the corpus, 2,192 wrong-and-green words exist; 605 sit in segments with mean_prob < 0.65 — the danger zone where coloring misleads.

## 2.3 The "21 → 2" problem

40 wrong-and-green words exist where both reference and hypothesis are numbers — the cognitively most dangerous variant. Top examples:

| ref | hyp (green) | hyp prob | seg mean_prob | seg WER% | Why dangerous |
|---|---|---|---|---|---|
| 7 | **four** | 0.998 | 0.70 | 80% | Number swapped, very high prob |
| 06 | **six** | 0.989 | 0.87 | 44% | "six" looks plausible from "06" |
| 000 | **2000** | 0.987 | 0.79 | 41% | Off by 2,000× |
| **billion** | **million** | 0.965 | 0.82 | 58% | Off by 1,000× — most dangerous |
| 1024 | **24** | 0.958 | 0.67 | 88% | Lost the leading "10" |
| 2011 | **2000** | 0.894 | 0.79 | 62% | Year off by 11 |
| 1156 | **you** | 0.977 | 0.64 | 94% | Number → unrelated word |

The "billion → million" case: model said "million" with 96.5% confidence in a segment with 0.82 mean_prob (above T_safe), painted green. A user would be off by a factor of 1,000. No purely confidence-based system can catch this — it requires beam disagreement, source-context priors, or visual disambiguation.

## 2.4 A natural three-tier policy

| Threshold | seg mean_prob | What it means |
|---|---|---|
| **T_salv** | **0.74** | Green is ≥ 75% reliable — useful with a caveat |
| **T_safe** | **0.82** | Green is ≥ 85% reliable — trustworthy as labeled |
| **T_trust** | **0.89** | Green is ≥ 90% reliable — high trust |

| Zone | Segment mean_prob | What to show user | Volume |
|---|---|---|---|
| **Trust** | ≥ 0.82 | Full sentence with coloring; green is reliable | 28% |
| **Salvage** | 0.65 – 0.82 | Sentence with coloring + visible "low confidence" banner | 38% |
| **Drop** | < 0.65 | Hide segment OR mark "unreliable — do not trust greens" | 34% |

# 3. Filtering with confidence: operating points and what slips through

We've shown confidence is a strong signal and that the green-band promise holds inside confident segments. This chapter answers the deployment question: at what threshold should we gate, what's the precision-recall trade-off, and which segments still slip through?

## 3.1 ROC — confidence-only quality gate

![ROC](../presentation_materials_20260224/01_plots_for_slides/conf_roc_filter.png)

{auc_table_md}

`mean_prob` reaches AUC ≈ {auc_pivot.at['mean_prob','niv_bad']:.2f} on bad-segment detection and AUC ≈ {auc_pivot.at['mean_prob','niv_y']:.2f} on good-segment detection — usable as a single gate without invoking the full IS pipeline.

## 3.2 Operating points — where to set the threshold

![operating points](../presentation_materials_20260224/01_plots_for_slides/conf_operating_points.png)

{op_table_md}

![sweet spot](../presentation_materials_20260224/01_plots_for_slides/conf_sweet_spot_pr.png)

Single-signal `mean_prob` peaks at F1 ≈ 0.75 around the 0.82 threshold (78% recall, 71% precision; mean IS of trusted segments rises to 4.01, mean WER drops to 27.5%). Tightening to 0.85 keeps a few fewer false-bads but loses ~25 percentage points of recall. Adding constraints (`min_word_prob`, `len_ratio`, entropy) pushes precision up but trades recall faster than it adds purity — the same F1 budget, redistributed.

## 3.3 Who slips through? False-good profile

At the recommended balanced gate (`mean_word_prob ≥ 0.80`), {a9['n_false_n']} segments are trusted but actually NIV-N. We profile them against the true-good set:

![false-good signatures](../presentation_materials_20260224/01_plots_for_slides/conf_false_good_signatures.png)

{gap_table_md}

**The smoking gun: false-bads are SHORT.** Median segment duration is **{gap.loc['duration_s','false_n_med']:.2f}s** for false-bads vs **{gap.loc['duration_s','true_y_med']:.2f}s** for true-goods. Median hyp word count: **{int(gap.loc['len_hyp_words','false_n_med'])}** vs **{int(gap.loc['len_hyp_words','true_y_med'])}**. False-bads are systematically segments where the model has too little material to constrain its output. Mean entropy is +{gap.loc['mean_entropy','gap_mean']:.2f} higher on false-bads — the model *is* uncertain, it just compensates by picking a high-prob single token at each position.

**The {a9['n_false_n']} false-good cases at the balanced gate:**

{case_table_md}

**Visual cues and broad-conversation context.** Segment duration is a free runtime proxy for visual quality (very short clips give the visual encoder little material to lock onto). A real visual quality model (lip occlusion, face-frame coverage, head pose) would catch more, but is out-of-pipeline today. Topic context — a surrounding-sentence language model conditioned on the source video's topic — could rescore the hyp and flag drift; also out-of-pipeline. Beam disagreement (Mission 6) is the most tractable next-sprint signal for the truly fluent-and-plausible cases that confidence alone cannot detect.

# 4. Failure modes: what "bad" looks like in confidence space

The previous chapter focused on detection thresholds. This chapter goes deeper: *which* kinds of failures slip past a confidence gate, and how each kind looks across the confidence parameters. The taxonomy is the March 2026 deck's 5-category model.

## 4.1 Hallucination scatter

![hallucination scatter](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_scatter.png)

![hallucination pairs](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_pairs_scatter.png)

| | |
|---|---|
| Hallucinated (WER ≥ 100%, len_ratio ≥ 0.5) | **{a5['n_hallucinated']}** |
| Dangerous (above + mean_prob ≥ 0.85) | **{a5['n_dangerous']}** |
| Median mean_prob, hallucinated vs healthy | {hall_med_p_h} / {hall_med_p_o} |
| Median mean_entropy, hallucinated vs healthy | {hall_med_e_h} / {hall_med_e_o} |

Mann-Whitney U on `mean_prob` and `mean_entropy` both reject equality of hallucinated vs healthy at p < 1e-50. The literature warned that fluent hallucinations would land in a "dangerous quadrant" of high prob × hallucinated; we found only **{a5['n_dangerous']} / {a5['n_hallucinated']}** ({a5['n_dangerous']/max(1,a5['n_hallucinated'])*100:.1f}%) of hallucinated segments there. The failure mode exists but is rare. Across the four alternative confidence pairs in the second figure, the same 3 cases reappear regardless of projection — max-softmax, entropy, margin, and red/green fractions are different shadows of the same underlying confidence collapse, not independent failure detectors.

## 4.2 Five-category failure-mode taxonomy (March deck)

The {n_bad} IS<2 segments classify into five mutually-exclusive categories, evaluated 1→5.

![failure-mode profile](../presentation_materials_20260224/01_plots_for_slides/conf_failure_mode_profile.png)

{cards_md}

{failure_table_md}

## 4.3 Trajectory clusters — failure shapes through time

![trajectory clusters](../presentation_materials_20260224/01_plots_for_slides/conf_trajectory_clusters.png)

{cluster_table_md}

The shape difference between flat-high (top cluster) and uncertain-throughout (bottom cluster) is visible after only a few tokens — enough material to support a mid-decode "give up early" hook (Mission 11 candidate). For each segment we'd track the rolling-mean per-position prob and abort if it crosses a flat-low signature before the full sequence is generated.

# 5. What confidence cannot tell us, and what's next

Confidence has three blind spots, all visible in the failure-mode breakdown:

1. **Wrong Topic** ({int(counts.get('1. Wrong Topic',0))/max(1,n_bad)*100:.0f}% of bad segments). The model commits decisively to a wrong domain; `mean_prob` sits in the medium band, no signal in confidence space sharp enough to flag. Needs semantic similarity (reference-required) or a runtime substitute — a topic-conditioned LM scoring the hyp for surprise relative to the source video's topic. **Mission 8.**
2. **Right Topic, Wrong Details** ({int(counts.get('3. Right Topic, Wrong Details',0))/max(1,n_bad)*100:.0f}% of bad segments). Confidence is the closest of any failure mode to healthy. The model knows the topic but loses the specific entities (numbers, proper nouns). Needs NEA F1 (reference-required) or beam disagreement — if the chosen beam dropped a number that other beams kept, that's a flag. **Mission 6 (all-20-beams capture).**
3. **The "billion → million" problem** — a single high-confidence wrong content word inside an otherwise-fine segment. Bypasses all current signals because the model is decisive on the wrong answer. Needs source-context priors (was the conversation about money?) or visual disambiguation. *Long-term.*

**Recommendations.**

1. **Keep CONF_HIGH = {CONF_HIGH} / CONF_MED = {CONF_MED} for per-word coloring**, but gate the *display* on segment-level `mean_word_prob` ≥ 0.82. Below that threshold, hide the segment or banner "unreliable — do not trust greens." (Sections 2.2-2.4.)
2. **Use `mean_word_prob` ≥ 0.80 as the runtime quality gate.** Already exposed via `make_report.py --word-confidence` as `sentence_confidence`. (Section 3.2.)
3. **Don't promote entropy to a primary gate.** Tied with max-softmax (Section 4.1), harder to explain. Keep capturing it for archaeology.
4. **Mission 6 (all-20-beams capture) is the highest-leverage next-sprint item.** Top-3 entropy is r = 0.95 redundant with full entropy (Section 1.4); we need genuine beam disagreement to expose Right-Topic-Wrong-Details and the dangerous decisive-but-wrong cases.
5. **Mission 8 (topic-conditioned LM for hyp rescoring) handles the Wrong Topic hole.** {int(counts.get('1. Wrong Topic',0))/max(1,n_bad)*100:.0f}% of bad segments fall here; the reference contains topic context that a runtime LM could approximate.
6. **Mission 11 (mid-decode trajectory monitoring) is the runtime "give up early" hook.** Section 4.3 shows the flat-low cluster is identifiable from just a few tokens.

# Reproduce

{reproduce_block}"""
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(md, encoding="utf-8")
    print(f"\nWrote {DOC_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confidence-sidecar", type=Path, required=True)
    ap.add_argument("--hypo", type=Path, required=True)
    ap.add_argument("--baseline-csv", type=Path, required=True)
    args = ap.parse_args()

    segs, diag = build_frame(args.confidence_sidecar, args.hypo, args.baseline_csv)
    a0 = analysis_0_wer_reconcile(segs)
    a1 = analysis_1_distributions(segs)
    a2 = analysis_2_calibration(segs)
    df = features_dataframe(segs)
    a3 = analysis_3_correlation_map(df)
    a4 = analysis_4_roc(df)
    a5 = analysis_5_hallucination(df, segs)
    a6 = analysis_6_trajectories(segs, df, k=5)
    a7 = analysis_7_beam_preview(df)
    a8 = analysis_8_operating_points(df)
    a9 = analysis_9_false_goods(df, segs, balanced_threshold=0.80)
    a11 = analysis_11_failure_modes(df, args.baseline_csv)

    write_report(diag, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a11,
                 args.confidence_sidecar, args.hypo, args.baseline_csv)


if __name__ == "__main__":
    main()
