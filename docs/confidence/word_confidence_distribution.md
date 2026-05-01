# Per-Word Confidence Distribution Analysis

**Source.** This document is the analytical companion to the per-token
softmax confidence shipped via `VSP_OUTPUT_SCORES=1` decode (Tier-2 in the
confidence-scoring report). It joins per-word probabilities aggregated by
[`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)
with the per-segment IS scoring already in
`english_full_results/client_outputs/report/report.csv`.

**Sample size.** **23,261 words across 1427 segments**.

## Word-level distribution (the headline)

![histogram](presentation_materials_20260224/01_plots_for_slides/conf_distribution.png)

| Statistic | Value |
|-----------|-------|
| Mean | 0.716 |
| Median | 0.835 |
| 10th percentile | 0.240 |
| 25th percentile | 0.488 |
| 75th percentile | 0.980 |
| 90th percentile | 0.996 |
| 95th percentile | 0.998 |
| 99th percentile | 1.000 |

**Threshold band fractions:**

| Band | Cutoff | % of words |
|------|--------|-----------|
| `conf-high` | p ≥ 0.85 | **48.6%** |
| `conf-med`  | 0.4 ≤ p < 0.85 | 32.1% |
| `conf-low`  | p < 0.4 | **19.3%** |

## Per-segment confidence vs IS family

![components](presentation_materials_20260224/01_plots_for_slides/conf_vs_is_components.png)

Pearson correlations:

  - mean_word_prob vs IS score (0-5): r = +0.837 (n=1427)
  - min_word_prob  vs IS score (0-5): r = +0.526
  - mean_word_prob vs WER (%): r = -0.714 (n=1427)
  - min_word_prob  vs WER (%): r = -0.443
  - mean_word_prob vs WWER (%): r = -0.749 (n=1427)
  - min_word_prob  vs WWER (%): r = -0.464
  - mean_word_prob vs NEA F1 (%): r = +0.682 (n=1427)
  - min_word_prob  vs NEA F1 (%): r = +0.432

## Threshold recommendation

(see the companion literature review for the calibration argument)

The current band cutoffs (0.3 / 0.7) split the actual word probability
distribution into roughly **19% red / 32% yellow / 49% green** in
the data we just generated. Whether that's the right operating point for the
client deck depends on whether they want few-but-trustworthy green words or
many-and-loose green words — the right answer comes from the
literature-backed calibration discussion in
[llama2_confidence_literature_review.md](llama2_confidence_literature_review.md).

If the literature recommends adjusting thresholds, regenerate this file
with the new cutoffs to see the band shift.

## Reproduce

```
python3 docs/_research-tools/generators/analyze_confidence_distribution.py \
    --confidence-sidecar /tmp/vsp_b3_1497_out/confidence-172610.json \
    --hypo               /tmp/vsp_b3_1497_out/hypo-172610.json \
    --report-csv         /home/ubuntu/english_full_results/client_outputs/report/report.csv
```
