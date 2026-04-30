#!/usr/bin/env python3
"""Per-word confidence distribution analysis.

Joins the per-token confidence sidecar with the IS scoring report to answer:

  1. What does the per-word confidence distribution look like (histogram +
     percentiles)?
  2. How does per-segment aggregated confidence (mean / min / median word
     prob) correlate with IS and with each of its 6 components (Semantic,
     Phonetic, Inv WER, Inv WWER, NEA F1, Length Ratio)?
  3. What threshold bands fall out of the data?

Outputs:
  - presentation_materials_20260224/01_plots_for_slides/conf_distribution.png
      (histogram of all per-word probabilities)
  - presentation_materials_20260224/01_plots_for_slides/conf_vs_is_components.png
      (small-multiples: confidence vs each IS component)
  - docs/confidence/word_confidence_distribution.md
      (markdown writeup with all the numbers + threshold recommendation)

Run:
    python3 docs/_research-tools/generators/analyze_confidence_distribution.py \
        --confidence-sidecar /tmp/vsp_b3_1497_out/confidence-XXXXX.json \
        --hypo            /tmp/vsp_b3_1497_out/hypo-XXXXX.json \
        --report-csv      /home/ubuntu/english_full_results/client_outputs/report/report.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GENERATORS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GENERATORS_DIR))
from compute_word_confidence import (  # noqa: E402
    CONF_HIGH, CONF_MED, aggregate_subtokens_to_words,
)

REPO_ROOT = GENERATORS_DIR.parents[2]

# Brand palette
BG     = "#0d1b2a"
NAVY2  = "#152a40"
TEAL   = "#00b4d8"
GREEN  = "#4caf50"
GOLD   = "#ffd54f"
CORAL  = "#e06c75"
WHITE  = "#ffffff"
LGRAY  = "#aaaaaa"
MGRAY  = "#666666"

OUT_PNG_HIST = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides" / "conf_distribution.png"
OUT_PNG_COMP = REPO_ROOT / "presentation_materials_20260224" / "01_plots_for_slides" / "conf_vs_is_components.png"
OUT_DOC      = REPO_ROOT / "docs" / "confidence" / "word_confidence_distribution.md"


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx * dy else 0.0


def _percentile(vs, pct):
    if not vs:
        return None
    s = sorted(vs)
    k = (len(s) - 1) * pct / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    if lo == hi:
        return s[lo]
    return s[lo] * (hi - k) + s[hi] * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confidence-sidecar", type=Path, required=True)
    ap.add_argument("--hypo", type=Path, required=True)
    ap.add_argument("--report-csv", type=Path, required=True,
                    help="english_full_results/client_outputs/report/report.csv")
    args = ap.parse_args()

    # Load all 3 sources
    conf = json.loads(args.confidence_sidecar.read_text())
    hypo = json.loads(args.hypo.read_text())
    report_rows = list(csv.DictReader(args.report_csv.open(encoding="utf-8")))
    report_by_id = {r["utt_id"]: r for r in report_rows}

    # Per-segment aggregation
    segments = []  # list of dicts
    all_word_probs = []
    for utt_id, ref, hyp in zip(hypo["utt_id"], hypo["ref"], hypo["hypo"]):
        seg = conf.get(utt_id)
        if not seg:
            continue
        words = aggregate_subtokens_to_words(seg.get("tokens", []))
        probs = [w["prob"] for w in words if w.get("prob") is not None]
        if not probs:
            continue
        all_word_probs.extend(probs)

        # Pull IS components from report.csv (only when present)
        rrow = report_by_id.get(utt_id)
        if not rrow:
            continue

        def _f(k):
            v = rrow.get(k, "").strip()
            if v in ("", "nan", "None"):
                return None
            try:
                return float(v)
            except ValueError:
                return None

        segments.append({
            "utt_id": utt_id,
            "n_words": len(words),
            "mean_p": sum(probs) / len(probs),
            "min_p":  min(probs),
            "median_p": statistics.median(probs),
            "wer":      _f("wer_%"),
            "wwer":     _f("wwer_%"),
            "is_score": _f("is_score"),
            "nea_f1":   _f("nea_f1_%"),
        })

    n_seg = len(segments)
    n_word = len(all_word_probs)
    print(f"Segments matched in confidence x report.csv: {n_seg}")
    print(f"Total words across all segments: {n_word}")

    # ── Distribution stats ──
    pcts = [10, 25, 50, 75, 90, 95, 99]
    pct_vals = {p: _percentile(all_word_probs, p) for p in pcts}
    band_high = sum(1 for p in all_word_probs if p >= CONF_HIGH) / n_word * 100
    band_med  = sum(1 for p in all_word_probs if CONF_MED <= p < CONF_HIGH) / n_word * 100
    band_low  = sum(1 for p in all_word_probs if p < CONF_MED) / n_word * 100

    print("\nWord-level confidence distribution:")
    print(f"  Mean:   {sum(all_word_probs)/n_word:.3f}")
    print(f"  Median: {pct_vals[50]:.3f}")
    print("  Percentiles:")
    for p, v in pct_vals.items():
        print(f"    {p:>3}%: {v:.3f}")
    print(f"  Band fractions  high(>={CONF_HIGH}) / med({CONF_MED}-{CONF_HIGH}) / low(<{CONF_MED}) = "
          f"{band_high:.1f}% / {band_med:.1f}% / {band_low:.1f}%")

    # ── Plot 1: histogram with thresholds + percentile lines ──
    fig, ax = plt.subplots(figsize=(11, 5), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(NAVY2)
    bins = [i / 50 for i in range(51)]  # 0..1 in steps of 0.02
    counts, edges = ax.hist(all_word_probs, bins=bins,
                            color=TEAL, edgecolor=WHITE, linewidth=0.4)[:2]
    ax.axvline(CONF_MED, color=CORAL, linestyle="--", linewidth=1.5,
               label=f"conf-low cutoff ({CONF_MED})")
    ax.axvline(CONF_HIGH, color=GREEN, linestyle="--", linewidth=1.5,
               label=f"conf-high cutoff ({CONF_HIGH})")
    ax.axvline(pct_vals[50], color=GOLD, linestyle=":", linewidth=1.2,
               label=f"median ({pct_vals[50]:.2f})")
    ax.set_xlabel("Per-word confidence (max-softmax probability)",
                  color=WHITE, fontsize=12)
    ax.set_ylabel("Word count", color=WHITE, fontsize=12)
    ax.set_title(
        f"Per-word confidence — {n_word:,} words across {n_seg} segments",
        color=WHITE, fontsize=14, fontweight="bold", pad=12,
    )
    ax.tick_params(colors=WHITE)
    for spine in ax.spines.values():
        spine.set_color(MGRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, color=MGRAY, alpha=0.25)
    ax.legend(loc="upper left", facecolor=NAVY2, edgecolor=MGRAY,
              labelcolor=WHITE, fontsize=10)
    OUT_PNG_HIST.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT_PNG_HIST, facecolor=BG, dpi=160, bbox_inches="tight")
    print(f"\nWrote {OUT_PNG_HIST}")
    plt.close(fig)

    # ── Plot 2: confidence vs IS components ──
    components = [
        ("IS score (0-5)", "is_score", GREEN),
        ("WER (%)",        "wer",      CORAL),
        ("WWER (%)",       "wwer",     "#ff9800"),
        ("NEA F1 (%)",     "nea_f1",   GOLD),
    ]
    fig, axs = plt.subplots(1, len(components), figsize=(16, 4.5), dpi=160)
    fig.patch.set_facecolor(BG)
    for ax, (label, key, color) in zip(axs, components):
        ax.set_facecolor(NAVY2)
        xs = [s["mean_p"] for s in segments if s.get(key) is not None]
        ys = [s[key]      for s in segments if s.get(key) is not None]
        if xs:
            ax.scatter(xs, ys, c=color, s=18, alpha=0.55, edgecolor="none")
            r = _pearson(xs, ys)
            ax.set_title(f"mean word prob  vs  {label}\nPearson r = {r:+.3f}",
                         color=WHITE, fontsize=11, pad=8)
        ax.set_xlabel("mean word prob", color=WHITE, fontsize=10)
        ax.set_ylabel(label, color=WHITE, fontsize=10)
        ax.tick_params(colors=WHITE)
        for spine in ax.spines.values():
            spine.set_color(MGRAY)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, color=MGRAY, alpha=0.25)
    fig.suptitle(f"Per-segment confidence vs IS family  —  n={n_seg}",
                 color=WHITE, fontsize=13, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT_PNG_COMP, facecolor=BG, dpi=160, bbox_inches="tight")
    print(f"Wrote {OUT_PNG_COMP}")
    plt.close(fig)

    # ── Pearson correlations vs IS family ──
    corr_lines = []
    for label, key, _ in components:
        xs = [s["mean_p"] for s in segments if s.get(key) is not None]
        ys = [s[key]      for s in segments if s.get(key) is not None]
        r = _pearson(xs, ys)
        corr_lines.append(f"  - mean_word_prob vs {label}: r = {r:+.3f} (n={len(xs)})")

        xs = [s["min_p"] for s in segments if s.get(key) is not None]
        ys = [s[key]     for s in segments if s.get(key) is not None]
        r = _pearson(xs, ys)
        corr_lines.append(f"  - min_word_prob  vs {label}: r = {r:+.3f}")

    # ── Markdown writeup ──
    with OUT_PNG_HIST.open("rb") as _: pass  # ensure exists
    md = f"""# Per-Word Confidence Distribution Analysis

**Source.** This document is the analytical companion to the per-token
softmax confidence shipped via `VSP_OUTPUT_SCORES=1` decode (Tier-2 in the
confidence-scoring report). It joins per-word probabilities aggregated by
[`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)
with the per-segment IS scoring already in
`english_full_results/client_outputs/report/report.csv`.

**Sample size.** **{n_word:,} words across {n_seg} segments**.

## Word-level distribution (the headline)

![histogram]({OUT_PNG_HIST.relative_to(REPO_ROOT)})

| Statistic | Value |
|-----------|-------|
| Mean | {sum(all_word_probs)/n_word:.3f} |
| Median | {pct_vals[50]:.3f} |
| 10th percentile | {pct_vals[10]:.3f} |
| 25th percentile | {pct_vals[25]:.3f} |
| 75th percentile | {pct_vals[75]:.3f} |
| 90th percentile | {pct_vals[90]:.3f} |
| 95th percentile | {pct_vals[95]:.3f} |
| 99th percentile | {pct_vals[99]:.3f} |

**Threshold band fractions:**

| Band | Cutoff | % of words |
|------|--------|-----------|
| `conf-high` | p ≥ {CONF_HIGH} | **{band_high:.1f}%** |
| `conf-med`  | {CONF_MED} ≤ p < {CONF_HIGH} | {band_med:.1f}% |
| `conf-low`  | p < {CONF_MED} | **{band_low:.1f}%** |

## Per-segment confidence vs IS family

![components]({OUT_PNG_COMP.relative_to(REPO_ROOT)})

Pearson correlations:

{chr(10).join(corr_lines)}

## Threshold recommendation

(see the companion literature review for the calibration argument)

The current band cutoffs (0.3 / 0.7) split the actual word probability
distribution into roughly **{band_low:.0f}% red / {band_med:.0f}% yellow / {band_high:.0f}% green** in
the data we just generated. Whether that's the right operating point for the
client deck depends on whether they want few-but-trustworthy green words or
many-and-loose green words — the right answer comes from the
literature-backed calibration discussion in
[llama2_confidence_literature_review.md](llama2_confidence_literature_review.md).

If the literature recommends adjusting thresholds, regenerate this file
with the new cutoffs to see the band shift.

## Reproduce

```
python3 docs/_research-tools/generators/analyze_confidence_distribution.py \\
    --confidence-sidecar {args.confidence_sidecar} \\
    --hypo               {args.hypo} \\
    --report-csv         {args.report_csv}
```
"""
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_DOC}")


if __name__ == "__main__":
    main()
