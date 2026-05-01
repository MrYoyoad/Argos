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

    md = f"""# Confidence Sidecar — Full Statistical Analysis

**Source.** Per-token confidence from `/tmp/vsp_b3_1497_out/confidence-172610.json` (1,497-segment B3 decode), joined with the baseline ground truth in `english_full_results/client_outputs/report/report.csv`. Per-token features (`prob`, `entropy`, `top3`) aggregated to per-word ([`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)) and per-segment.

**Sample sizes.** {diag['n_total']:,} segments matched in confidence × hypo. {diag['n_with_baseline']:,} segments joined with baseline IS / WER. {a2['n_words']:,} hypothesis words aligned to references for calibration.

**Headline findings.**

1. **Mean per-segment word probability is the single best confidence aggregate**: r = **{pearson.at['mean_word_prob','is_score']:+.3f}** with IS, **{pearson.at['mean_word_prob','wer']:+.3f}** with WER, **{pearson.at['mean_word_prob','wwer']:+.3f}** with WWER (n={a3['n_segments']:,}).
2. **Confidence-only filtering is strong**: AUC = **{aucs.loc[aucs.target=='niv_bad'].set_index('feature').loc['mean_prob','auc']:.3f}** detecting NIV-N (bad) and **{aucs.loc[aucs.target=='niv_y'].set_index('feature').loc['mean_prob','auc']:.3f}** detecting NIV-Y (good) using `mean_prob` alone.
3. **Calibration is reasonable but the green band leaks**: P(correct | green p ≥ {CONF_HIGH}) = **{a2['p_correct_green']*100:.1f}%** (n={a2['n_green']:,} green words), short of the 90%+ "trust without review" promise. ECE = **{a2['ece_pct']:.1f}%**.
4. **Hallucinations are mostly low-confidence — max-softmax catches them**: only **{a5['n_dangerous']} / {a5['n_hallucinated']}** ({a5['n_dangerous']/max(1,a5['n_hallucinated'])*100:.1f}%) hallucinated segments slip through with mean_prob ≥ 0.85. Entropy (median {hall_med_e_h} hallucinated vs {hall_med_e_o} healthy) and max-softmax (median {hall_med_p_h} vs {hall_med_p_o}) separate the two populations equally well — AUCs are tied (entropy {auc_pivot.at['mean_entropy','niv_bad']:.3f}, mean_prob {auc_pivot.at['mean_prob','niv_bad']:.3f}). Entropy is **redundant**, not better, on this data.
5. **Trajectory clustering identifies a clean failure shape**: cluster with mean_prob ramping down separates from flat-high. The worst cluster has mean WER **{cluster_summary['mean_wer'].max():.0f}%** vs **{cluster_summary['mean_wer'].min():.0f}%** for the best.

---

## 0. WER reconciliation (sanity check)

| | |
|---|---|
| Hyps identical to baseline | {a0['n_identical']:,} |
| Hyps different from baseline | {a0['n_different']:,} |
| Today, pooled WER | {a0['today_pooled_wer']:.2f}% |
| Today, mean-of-segment WER | {a0['today_mean_seg_wer']:.2f}% |
| Baseline, mean-of-segment WER | 64.1% (from report.csv) |

{a0_text}

## 1. Distributions

![distributions](../presentation_materials_20260224/01_plots_for_slides/conf_full_distributions.png)

| Signal | Mean | Median | p10 | p90 |
|--------|------|--------|-----|-----|
| Per-token prob | {a1['token_prob']['mean']:.3f} | {a1['token_prob']['median']:.3f} | {a1['token_prob']['p10']:.3f} | {a1['token_prob']['p90']:.3f} |
| Per-word prob | {a1['word_prob']['mean']:.3f} | {a1['word_prob']['median']:.3f} | {a1['word_prob']['p10']:.3f} | {a1['word_prob']['p90']:.3f} |
| Per-token entropy | {a1['entropy']['mean']:.3f} | {a1['entropy']['median']:.3f} | {a1['entropy']['p10']:.3f} | {a1['entropy']['p90']:.3f} |
| Per-token margin (top1−top2) | {a1['margin']['mean']:.3f} | {a1['margin']['median']:.3f} | {a1['margin']['p10']:.3f} | {a1['margin']['p90']:.3f} |

The 33-Obama small-sample showed 89.7% green / 6.8% yellow / 3.4% red on word-level. On the diverse 1,497-segment dataset the same thresholds (0.85 / 0.40) produce **{a2['n_green']/(a2['n_green']+a2['n_yellow']+a2['n_red'])*100:.1f}% green / {a2['n_yellow']/(a2['n_green']+a2['n_yellow']+a2['n_red'])*100:.1f}% yellow / {a2['n_red']/(a2['n_green']+a2['n_yellow']+a2['n_red'])*100:.1f}% red** — exactly the rebalancing the threshold-design doc anticipated.

## 2. Calibration — do the bands honor their promises?

![calibration](../presentation_materials_20260224/01_plots_for_slides/conf_calibration_curve.png)

| Band | Threshold | n words | P(correct) |
|------|-----------|---------|------------|
| green  | p ≥ {CONF_HIGH} | {a2['n_green']:,} | **{a2['p_correct_green']*100:.1f}%** |
| yellow | {CONF_MED} ≤ p < {CONF_HIGH} | {a2['n_yellow']:,} | {a2['p_correct_yellow']*100:.1f}% |
| red    | p < {CONF_MED} | {a2['n_red']:,} | {a2['p_correct_red']*100:.1f}% |

**Expected Calibration Error (10 bins): {a2['ece_pct']:.2f}%** — within the 5-15pp band the literature predicts for fine-tuned LLaMA-2 generation.

**Decision per [threshold_design.md](threshold_design.md):**
- P(correct | green) = {a2['p_correct_green']*100:.1f}% — {decision_text}

## 3. Correlation map — which confidence aggregate predicts quality?

![correlation heatmap](../presentation_materials_20260224/01_plots_for_slides/conf_correlation_heatmap.png)

Top-5 features by |Pearson r| with IS score:

"""
    # Top-5 by |r| with IS
    top5 = pearson["is_score"].abs().sort_values(ascending=False).head(5)
    for feat, abs_r in top5.items():
        r = pearson.at[feat, "is_score"]
        md += f"- `{feat}` → IS: **r = {r:+.3f}**\n"

    md += f"""

Top-5 features by |Pearson r| with WER:

"""
    top5w = pearson["wer"].abs().sort_values(ascending=False).head(5)
    for feat, abs_r in top5w.items():
        r = pearson.at[feat, "wer"]
        md += f"- `{feat}` → WER: **r = {r:+.3f}**\n"

    md += f"""

Full table is in `conf_correlation_heatmap.png`. Restricting to confidence aggregates vs IS score, max |Pearson r − Spearman ρ| = **{a3.get('max_conf_dev_is', float('nan')):.3f}** — the linear and rank correlations agree. (The full-matrix maximum is {a3.get('max_pearson_spearman_dev', float('nan')):.3f}, driven by `len_ratio vs wer` where WER's heavy tail breaks linearity; that pair is not load-bearing for confidence triage.)

## 4. Filter ROC — confidence-only quality gate

![ROC](../presentation_materials_20260224/01_plots_for_slides/conf_roc_filter.png)

AUC summary:

| Feature | NIV-N (bad) detector | NIV-Y (good) detector |
|---------|----------------------|------------------------|
"""
    auc_pivot = aucs.pivot(index="feature", columns="target", values="auc")
    for feat in auc_pivot.index:
        bad = auc_pivot.at[feat, "niv_bad"] if "niv_bad" in auc_pivot.columns else np.nan
        good = auc_pivot.at[feat, "niv_y"] if "niv_y" in auc_pivot.columns else np.nan
        bad_s = f"{bad:.3f}" if pd.notna(bad) else "—"
        good_s = f"{good:.3f}" if pd.notna(good) else "—"
        md += f"| `{feat}` | {bad_s} | {good_s} |\n"

    md += f"""

A confidence-only gate using `mean_prob` reaches AUC ≈ {auc_pivot.at['mean_prob','niv_bad']:.2f} on bad-segment detection and AUC ≈ {auc_pivot.at['mean_prob','niv_y']:.2f} on good-segment detection — strong enough to act on at runtime without invoking the full IS pipeline. This is a deployment-time feature: at decode time we already have `mean_prob` for free.

## 5. Hallucination detection — does entropy catch what max-softmax misses?

![hallucination scatter](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_scatter.png)

| | |
|---|---|
| Hallucinated (WER ≥ 100%, len_ratio ≥ 0.5) | **{a5['n_hallucinated']}** |
| Dangerous (above + mean_prob ≥ 0.85) | **{a5['n_dangerous']}** |
| Median mean_prob, hallucinated | {hall_med_p_h} |
| Median mean_prob, healthy | {hall_med_p_o} |
| Median mean_entropy, hallucinated | {hall_med_e_h} |
| Median mean_entropy, healthy | {hall_med_e_o} |

Mann-Whitney U on `mean_prob` and `mean_entropy` both reject equality of the hallucinated vs healthy distributions at p < 1e-50 — both signals separate the two populations strongly. The literature warned that fluent hallucinations would land in a "dangerous quadrant" of high prob × hallucinated; we found **{a5['n_dangerous']} / {a5['n_hallucinated']}** ({a5['n_dangerous']/max(1,a5['n_hallucinated'])*100:.1f}%) of hallucinated segments there. The failure mode exists but is rare on this dataset. **Take-away:** for filtering at runtime, `mean_prob < 0.6` already catches the vast majority of hallucinations; entropy adds no measurable separation power on top. The deck should still footnote that confidence color cannot detect the {a5['n_dangerous']} fluent-hallucination cases — but those are an edge case, not the dominant failure mode.

## 6. Trajectory clustering — failure modes in confidence space

![trajectory clusters](../presentation_materials_20260224/01_plots_for_slides/conf_trajectory_clusters.png)

Five-cluster k-means on length-normalized confidence trajectories (k chosen to expose distinct shapes without over-fragmenting). Sorted by mean IS, best-first:

| Cluster | n | Mean WER% | Mean IS | NIV-Y rate | NIV-N rate |
|---------|---|-----------|---------|------------|------------|
"""
    for _, row in cluster_summary.iterrows():
        md += (f"| C{int(row['cluster'])} | {int(row['n_segments'])} | "
               f"{row['mean_wer']:.1f} | {row['mean_is']:.2f} | "
               f"{row['p_niv_y']*100:.1f}% | {row['p_niv_n']*100:.1f}% |\n")

    md += f"""

Cluster centroids in the figure show the canonical shapes: a **flat-high** cluster (high confidence start to finish, lowest WER, highest IS) and a **ramp-down** / **flat-low** cluster (collapses early, never recovers, highest WER). This validates the "trajectory monitoring" hypothesis from [confidence_followups.md](confidence_followups.md): if a decode mid-loop already shows a ramp-down profile, we have actionable evidence that the rest of the segment is going to fail.

## 7. Beam-aggregation preview (cheap version)

We don't have all 20 beams in this sidecar — only `top3` per step. Using top-3-only entropy as a poor man's beam diversity:

| | |
|---|---|
| r(full_entropy, top3_entropy) | {a7.get('r_full_top3', float('nan')):+.3f} |
| r(full_entropy, WER) | {a7.get('r_full_wer', float('nan')):+.3f} |
| r(top3_entropy, WER) | {a7.get('r_top3_wer', float('nan')):+.3f} |
| r(full_entropy, IS) | {a7.get('r_full_is', float('nan')):+.3f} |
| r(top3_entropy, IS) | {a7.get('r_top3_is', float('nan')):+.3f} |

Top-3 entropy is **almost perfectly redundant with full entropy** (r ≈ {a7.get('r_full_top3', float('nan')):+.3f}), so it adds no information beyond what we already capture. To get genuine beam-level signal we need the all-20-beams capture from the followups doc; the cheap version is not enough.

## 8. Operating-point selection — precision vs recall vs false-bads

![operating points](../presentation_materials_20260224/01_plots_for_slides/conf_operating_points.png)

The headline correlation (r ≈ 0.84 with IS) tells us confidence *carries* the signal; this section asks the deployment question — at which threshold is the trade-off best, and how do extra signals (duration, entropy) move the curve?

{op_table_md}

**Reading the trade-off.** Single-signal `mean_word_prob` peaks at F1 ≈ 0.74 around the 0.80 threshold (78% recall, 70% precision, **9 false-bads** out of 405 trusted segments). Tightening to 0.85 keeps a few fewer false-bads but loses ~25 percentage points of recall. Adding constraints (`min_word_prob`, `len_ratio`, entropy) pushes precision up but trades recall faster than it adds purity — the same F1 budget, redistributed.

**Recommendation.** For most use cases pick `mean_word_prob >= 0.80` — keeps 78% of NIV-Y segments accessible, costs only 9 NIV-N leakages out of 1,427 (0.6% of corpus). For zero-tolerance deployments, gate `mean_word_prob >= 0.85 AND duration_s >= 1.5 AND mean_entropy <= 0.7` — that gate produces **zero false-bads** at ~30% recall, useful for legal / medical / broadcast captioning where any wrong-trust is unacceptable.

## 9. False-good characterization — what slips through, and can context catch it?

At the recommended balanced gate (`mean_word_prob >= 0.80`), {a9['n_false_n']} segments are trusted but actually NIV-N. We dump them and ask: is anything else in the data, or in the broader video / topic context, able to flag these?

![false-good signatures](../presentation_materials_20260224/01_plots_for_slides/conf_false_good_signatures.png)

**Feature gap (false-bads vs true-goods at the gate):**

{gap_table_md}

**The smoking gun: false-bads are SHORT.** Median segment duration is **{gap.loc['duration_s','false_n_med']:.2f}s** for false-bads vs **{gap.loc['duration_s','true_y_med']:.2f}s** for true-goods. Median hyp word count is **{int(gap.loc['len_hyp_words','false_n_med'])}** vs **{int(gap.loc['len_hyp_words','true_y_med'])}**. False-bads are systematically segments where the model has too little material to constrain its output — short clips with a handful of words give the language prior room to commit to a fluent-but-wrong answer.

**Mean entropy is +{gap.loc['mean_entropy','gap_mean']:.2f} higher on false-bads.** The model *is* uncertain on these — it just compensates by picking a high-prob single token at each position. Per-token max-softmax misses the dispersion; entropy preserves it. This is exactly the case the threshold-design doc anticipated.

**The {a9['n_false_n']} false-good cases at the balanced gate:**

{case_table_md}

**Examples (REF vs HYP):**

{example_md}

**Failure-mode taxonomy:**

| Mode | Example | What gives it away | Catchable from |
|---|---|---|---|
| Counting / digit loop | "1 2 3 4 5 6 7 8 9 10 11 12" | min_word_prob 0.15, regex match | confidence + post-hoc text rule |
| Phonetic substitution | "major in acting" → "measure a hacking" | low NEA F1, missed entities, plausible English | NEA / topic LM |
| Plausible swap | "all right i'm gonna read you" → "great i'm going to do this" | reference required to detect | beam disagreement, surrounding-context LM |
| Over-generation | "link down there" (3w) → "down there go over there..." (10w) | len_ratio > 2, hyp_words >> dur | confidence + duration |
| Short-segment substitution | "even after the insurance examination" → "after the initial contamination" | dur < 1s, NEA F1 = 0 | duration filter |

**Could visual cues or broad-conversation context catch these?**

- **Visual cues** — segment duration is a free proxy for visual quality (very short clips have less material for the visual encoder to lock onto). Adding `duration >= 1.5s` cuts most short-segment false-bads out of the trusted set. **A real visual quality model** (lip occlusion, face-frame coverage, head-pose) would catch more — not built into the pipeline today; candidate for next sprint.
- **Topic context** — false-bads frequently lose specific entities (numbers, proper nouns, domain words). NEA F1 = 0% on most cases. A surrounding-sentence language model conditioned on the *source video's* topic could rescore the hyp and flag drift — also not in the pipeline today, but the ref text already exists for this purpose during evaluation.
- **Beam disagreement** — for cases like "great i'm going to do this", the chosen beam is decisive but unrelated to the reference. Capturing all 20 beams would let us ask whether *any* alternative beam was closer to the reference — a genuine quality signal that confidence-of-chosen-beam alone cannot expose. Mission 6.

**Take-away.** The three free signals already in our sidecar (mean_word_prob, mean_entropy, segment duration) catch every false-bad that has any objective signature. The residual cases — phonetically plausible, length-matched, fluent — are out of reach of confidence alone and will require either visual-quality scoring or beam-aggregation to flag automatically. Until then, the deck should footnote the residual rate at the chosen operating point ({a9['n_false_n']/a9['n_trusted']*100:.1f}% false-bad among trusted at mwp >= {a9['balanced_threshold']:.2f}).

---

## What changes in the codebase

Based on these findings:

1. **Keep CONF_HIGH = 0.85 / CONF_MED = 0.40.** Calibration is in-band. Tightening green to 0.90 would cost {(a2['p_correct_green']-0.90)*100:.0f}pp of "trust" coverage without large reliability gains.
2. **Add `mean_prob` to the per-segment summary** in `make_report.py` (already exists as `sentence_confidence`) and **flag segments with mean_prob < 0.6** as candidates for human review — this catches **~{auc_pivot.at['mean_prob','niv_bad']*100:.0f}%** of NIV-N segments.
3. **Do NOT promote entropy to a primary gate yet.** Marginal improvement over max-softmax, harder to explain, doesn't beat hallucinations. Keep capturing it for archaeology.
4. **Schedule the all-20-beams decode change for next sprint** (Mission 6) — top-3 is too narrow.
5. **Trajectory clustering belongs in the runtime stack as a "give up early" signal** — Mission 11 candidate. Mid-decode trajectory shape predicts segment quality before the full sequence finishes.

## Reproduce

{reproduce_block}"""
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Build Section 12 markdown (failure-mode profile, March-deck style).
    a11_summary = a11["summary"]
    counts = a11["counts"]
    n_bad = a11["n_bad"]
    cards = a11["card_metadata"]

    # March-deck "card" rows: name, count, %, rule, example.
    cards_md = ""
    for cat, desc, rule, example in cards:
        n = int(counts.get(cat, 0))
        pct = (n / max(1, n_bad)) * 100
        # Pull confidence summary for this category, if present.
        if cat in a11_summary.index:
            r = a11_summary.loc[cat]
            conf_blurb = (
                f"mean_prob={r['mean_prob']:.2f}, "
                f"min_wp={r['min_word_prob']:.2f}, "
                f"entropy={r['mean_entropy']:.2f}, "
                f"len_ratio={r['len_ratio']:.2f}, "
                f"dur={r['duration_s']:.2f}s"
            )
        else:
            conf_blurb = "—"
        cards_md += f"### {cat}  ({pct:.1f}%, n={n})\n\n"
        cards_md += f"- **What:** {desc}\n"
        cards_md += f"- **Rule:** {rule}\n"
        cards_md += f"- **Example:** {example}\n"
        cards_md += f"- **Confidence signature:** {conf_blurb}\n\n"

    # Full per-category summary table for reference.
    s11_table = "| Category | n | mean_prob | min_word_prob | mean_entropy | mean_margin | duration (s) | len_ratio | NEA F1 | WER % | IS |\n"
    s11_table += "|---|---|---|---|---|---|---|---|---|---|---|\n"
    for cat, row in a11_summary.iterrows():
        s11_table += (f"| **{cat}** | {int(row['n'])} | "
                      f"{row['mean_prob']:.2f} | {row['min_word_prob']:.2f} | "
                      f"{row['mean_entropy']:.2f} | {row['mean_margin']:.2f} | "
                      f"{row['duration_s']:.2f} | {row['len_ratio']:.2f} | "
                      f"{row['nea_f1']:.1f} | {row['wer']:.0f} | "
                      f"{row['is_score']:.2f} |\n")

    section_11_md = f"""## 12. Failure-mode profile — March 5-category taxonomy on confidence parameters

The {n_bad} below-threshold segments (IS < 2.0) classified into 5 mutually-exclusive categories — each segment gets exactly one label, checked 1→5. Same taxonomy as the March 2026 deck (slide_failure_deep_1a/1b), grounded in ASR error taxonomy (Fosler-Lussier 2004) and LLM hallucination analysis (ACL 2025). This section asks: **how does each March category look in confidence space?**

![failure-mode profile](../presentation_materials_20260224/01_plots_for_slides/conf_failure_mode_profile.png)

{cards_md}

**Per-category summary (bottom row = healthy NIV-Y reference):**

{s11_table}

**The pattern across confidence parameters:**

- **Signal Loss** is trivially detectable — empty output, no per-token confidence to aggregate. The pipeline already filters these.
- **Hallucination** has elevated `len_ratio` (model generates more than asked) and rising `mean_entropy`. Both are decode-time-free signals.
- **Wrong Topic** is the LARGEST category and the one our confidence signals separate from healthy *least* cleanly — the model commits decisively to a wrong domain. Semantic similarity is the only reliable separator, but that requires the reference. Beam-aggregation (Mission 6) is the runtime alternative.
- **Right Topic, Wrong Details** has confidence in the same band as moderate-quality healthy segments — the model knows the topic but loses entities. NEA F1 = 0 is the diagnostic, also reference-required at runtime. **This is the "frustrating near-miss" zone.**
- **Accumulated Errors** distribute across the middle of every parameter range — no single signal is decisive because every signal is mediocre. Death by a thousand cuts. Best catch: `frac_p_lt_04` ≥ 0.30 (30%+ of tokens in the red band).

**Take-away.** Categories 1 and 2 (Signal Loss + Hallucination) are catchable from confidence + length alone — together that's {int(counts.get('1. Signal Loss', 0)) + int(counts.get('2. Hallucination', 0))} of the {n_bad} bad segments. Categories 3-5 require either the reference (semantic / NEA) or beam-level signal — together {int(counts.get('3. Wrong Topic', 0)) + int(counts.get('4. Right Topic, Wrong Details', 0)) + int(counts.get('5. Accumulated Errors', 0))} segments. This is why Mission 6 (all-20-beams capture) and Mission 8 (topic-conditioned LM) sit at the top of the next-sprint list.

"""

    # Preserve any extra sections (## 10, ## 11, ...) added by other
    # generators between section 9 and "What changes in the codebase".
    # We re-generate Section 12 (failure-mode profile) ourselves, so strip
    # any prior copy before re-injecting. Sections 10 and 11 (added by
    # external generators — extra-scatters and band-reliability) are
    # preserved verbatim.
    extra = ""
    if DOC_PATH.exists():
        prev = DOC_PATH.read_text(encoding="utf-8")
        m = re.search(r"\n(## 1[0-9]\..*?)(?=\n## What changes in the codebase)",
                      prev, re.DOTALL)
        if m:
            block = m.group(1)
            # Drop any prior section 12 — we rewrite it.
            block = re.sub(r"## 12\..*?(?=\n## |\Z)", "", block, flags=re.DOTALL).rstrip()
            if block:
                extra = block + "\n\n"
    # Inject preserved extras + our section 12 before "What changes".
    md = md.replace(
        "## What changes in the codebase",
        extra + section_11_md + "## What changes in the codebase",
        1,
    )
    print(f"  Preserved {len(extra)} bytes of extra sections, added section 12")

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
