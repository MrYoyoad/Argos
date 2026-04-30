# Per-Word Confidence Distribution Analysis

**Source.** This document is the analytical companion to the per-token
softmax confidence shipped via `VSP_OUTPUT_SCORES=1` decode (Tier-2 in the
confidence-scoring report). It joins per-word probabilities aggregated by
[`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)
with the per-segment IS scoring already in
`english_full_results/client_outputs/report/report.csv`.

**Sample size.** **935 words across 0 segments**.

## Word-level distribution (the headline)

![histogram](presentation_materials_20260224/01_plots_for_slides/conf_distribution.png)

| Statistic | Value |
|-----------|-------|
| Mean | 0.911 |
| Median | 0.993 |
| 10th percentile | 0.697 |
| 25th percentile | 0.945 |
| 75th percentile | 0.998 |
| 90th percentile | 1.000 |
| 95th percentile | 1.000 |
| 99th percentile | 1.000 |

**Threshold band fractions:**

| Band | Cutoff | % of words |
|------|--------|-----------|
| `conf-high` | p ≥ 0.7 | **89.7%** |
| `conf-med`  | 0.3 ≤ p < 0.7 | 6.8% |
| `conf-low`  | p < 0.3 | **3.4%** |

## Per-segment confidence vs IS family

![components](presentation_materials_20260224/01_plots_for_slides/conf_vs_is_components.png)

Pearson correlations:

  - mean_word_prob vs IS score (0-5): r = +0.000 (n=0)
  - min_word_prob  vs IS score (0-5): r = +0.000
  - mean_word_prob vs WER (%): r = +0.000 (n=0)
  - min_word_prob  vs WER (%): r = +0.000
  - mean_word_prob vs WWER (%): r = +0.000 (n=0)
  - min_word_prob  vs WWER (%): r = +0.000
  - mean_word_prob vs NEA F1 (%): r = +0.000 (n=0)
  - min_word_prob  vs NEA F1 (%): r = +0.000

## Threshold recommendation

(see the companion literature review for the calibration argument)

The current band cutoffs (0.3 / 0.7) split the actual word probability
distribution into roughly **3% red / 7% yellow / 90% green** in
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
    --confidence-sidecar /tmp/vsp_b3_full_out/confidence-172610.json \
    --hypo               /tmp/vsp_b3_full_out/hypo-172610.json \
    --report-csv         /home/ubuntu/english_full_results/client_outputs/report/report.csv
```
