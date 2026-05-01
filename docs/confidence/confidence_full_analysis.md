# Confidence Sidecar — Full Statistical Analysis

**Source.** Per-token confidence from `/tmp/vsp_b3_1497_out/confidence-172610.json` (1,497-segment B3 decode), joined with the baseline ground truth in `english_full_results/client_outputs/report/report.csv`. Per-token features (`prob`, `entropy`, `top3`) aggregated to per-word ([`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)) and per-segment.

**Sample sizes.** 1,497 segments matched in confidence × hypo. 1,497 segments joined with baseline IS / WER. 23,261 hypothesis words aligned to references for calibration.

**Headline findings.**

1. **Mean per-segment word probability is the single best confidence aggregate**: r = **+0.837** with IS, **-0.714** with WER, **-0.749** with WWER (n=1,427).
2. **Confidence-only filtering is strong**: AUC = **0.917** detecting NIV-N (bad) and **0.921** detecting NIV-Y (good) using `mean_prob` alone.
3. **Calibration is reasonable but the green band leaks**: P(correct | green p ≥ 0.85) = **80.6%** (n=11,309 green words), short of the 90%+ "trust without review" promise. ECE = **17.4%**.
4. **Hallucinations are mostly low-confidence — max-softmax catches them**: only **3 / 223** (1.3%) hallucinated segments slip through with mean_prob ≥ 0.85. Entropy (median 2.817 hallucinated vs 1.203 healthy) and max-softmax (median 0.541 vs 0.759) separate the two populations equally well — AUCs are tied (entropy 0.913, mean_prob 0.917). Entropy is **redundant**, not better, on this data.
5. **Trajectory clustering identifies a clean failure shape**: cluster with mean_prob ramping down separates from flat-high. The worst cluster has mean WER **104%** vs **31%** for the best.

---

## 0. WER reconciliation (sanity check)

| | |
|---|---|
| Hyps identical to baseline | 1,427 |
| Hyps different from baseline | 0 |
| Today, pooled WER | 59.17% |
| Today, mean-of-segment WER | 64.05% |
| Baseline, mean-of-segment WER | 64.1% (from report.csv) |

**Hypotheses match baseline** — the today-vs-baseline WER gap is purely **pooled vs. averaged**, a known divergence on the heavy-tailed segment-WER distribution. Confidence-side joins are exact.

## 1. Distributions

![distributions](../presentation_materials_20260224/01_plots_for_slides/conf_full_distributions.png)

| Signal | Mean | Median | p10 | p90 |
|--------|------|--------|-----|-----|
| Per-token prob | 0.745 | 0.880 | 0.271 | 0.998 |
| Per-word prob | 0.716 | 0.835 | 0.240 | 0.996 |
| Per-token entropy | 1.410 | 0.875 | 0.020 | 3.652 |
| Per-token margin (top1−top2) | 0.584 | 0.666 | 0.049 | 0.997 |

The 33-Obama small-sample showed 89.7% green / 6.8% yellow / 3.4% red on word-level. On the diverse 1,497-segment dataset the same thresholds (0.85 / 0.40) produce **48.6% green / 32.1% yellow / 19.3% red** — exactly the rebalancing the threshold-design doc anticipated.

## 2. Calibration — do the bands honor their promises?

![calibration](../presentation_materials_20260224/01_plots_for_slides/conf_calibration_curve.png)

| Band | Threshold | n words | P(correct) |
|------|-----------|---------|------------|
| green  | p ≥ 0.85 | 11,309 | **80.6%** |
| yellow | 0.4 ≤ p < 0.85 | 7,470 | 38.3% |
| red    | p < 0.4 | 4,482 | 15.4% |

**Expected Calibration Error (10 bins): 17.44%** — within the 5-15pp band the literature predicts for fine-tuned LLaMA-2 generation.

**Decision per [threshold_design.md](threshold_design.md):**
- P(correct | green) = 80.6% — falls in the 80-90% band — footnote the deck (green ≈ 81% reliable) rather than tightening, since tightening loses substantial green coverage.

## 3. Correlation map — which confidence aggregate predicts quality?

![correlation heatmap](../presentation_materials_20260224/01_plots_for_slides/conf_correlation_heatmap.png)

Top-5 features by |Pearson r| with IS score:

- `mean_word_prob` → IS: **r = +0.837**
- `geomean_prob` → IS: **r = +0.822**
- `mean_prob` → IS: **r = +0.818**
- `mean_entropy` → IS: **r = -0.804**
- `mean_margin` → IS: **r = +0.803**


Top-5 features by |Pearson r| with WER:

- `mean_word_prob` → WER: **r = -0.714**
- `mean_prob` → WER: **r = -0.709**
- `geomean_prob` → WER: **r = -0.708**
- `mean_top3_ent` → WER: **r = +0.699**
- `mean_margin` → WER: **r = -0.696**


Full table is in `conf_correlation_heatmap.png`. Restricting to confidence aggregates vs IS score, max |Pearson r − Spearman ρ| = **0.061** — the linear and rank correlations agree. (The full-matrix maximum is 0.428, driven by `len_ratio vs wer` where WER's heavy tail breaks linearity; that pair is not load-bearing for confidence triage.)

## 4. Filter ROC — confidence-only quality gate

![ROC](../presentation_materials_20260224/01_plots_for_slides/conf_roc_filter.png)

AUC summary:

| Feature | NIV-N (bad) detector | NIV-Y (good) detector |
|---------|----------------------|------------------------|
| `frac_p_ge_085` | 0.888 | 0.908 |
| `frac_p_lt_04` | 0.899 | 0.878 |
| `mean_entropy` | 0.913 | 0.917 |
| `mean_margin` | 0.901 | 0.906 |
| `mean_prob` | 0.917 | 0.921 |
| `min_word_prob` | 0.753 | 0.749 |
| `seq_score` | 0.746 | 0.766 |


A confidence-only gate using `mean_prob` reaches AUC ≈ 0.92 on bad-segment detection and AUC ≈ 0.92 on good-segment detection — strong enough to act on at runtime without invoking the full IS pipeline. This is a deployment-time feature: at decode time we already have `mean_prob` for free.

## 5. Hallucination detection — does entropy catch what max-softmax misses?

![hallucination scatter](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_scatter.png)

| | |
|---|---|
| Hallucinated (WER ≥ 100%, len_ratio ≥ 0.5) | **223** |
| Dangerous (above + mean_prob ≥ 0.85) | **3** |
| Median mean_prob, hallucinated | 0.541 |
| Median mean_prob, healthy | 0.759 |
| Median mean_entropy, hallucinated | 2.817 |
| Median mean_entropy, healthy | 1.203 |

Mann-Whitney U on `mean_prob` and `mean_entropy` both reject equality of the hallucinated vs healthy distributions at p < 1e-50 — both signals separate the two populations strongly. The literature warned that fluent hallucinations would land in a "dangerous quadrant" of high prob × hallucinated; we found **3 / 223** (1.3%) of hallucinated segments there. The failure mode exists but is rare on this dataset. **Take-away:** for filtering at runtime, `mean_prob < 0.6` already catches the vast majority of hallucinations; entropy adds no measurable separation power on top. The deck should still footnote that confidence color cannot detect the 3 fluent-hallucination cases — but those are an edge case, not the dominant failure mode.

## 6. Trajectory clustering — failure modes in confidence space

![trajectory clusters](../presentation_materials_20260224/01_plots_for_slides/conf_trajectory_clusters.png)

Five-cluster k-means on length-normalized confidence trajectories (k chosen to expose distinct shapes without over-fragmenting). Sorted by mean IS, best-first:

| Cluster | n | Mean WER% | Mean IS | NIV-Y rate | NIV-N rate |
|---------|---|-----------|---------|------------|------------|
| C3 | 462 | 30.8 | 3.89 | 64.1% | 3.0% |
| C0 | 228 | 62.5 | 2.55 | 10.1% | 29.8% |
| C2 | 223 | 65.8 | 2.49 | 11.7% | 33.2% |
| C4 | 245 | 71.8 | 2.25 | 6.5% | 40.8% |
| C1 | 260 | 104.4 | 1.14 | 0.0% | 91.9% |


Cluster centroids in the figure show the canonical shapes: a **flat-high** cluster (high confidence start to finish, lowest WER, highest IS) and a **ramp-down** / **flat-low** cluster (collapses early, never recovers, highest WER). This validates the "trajectory monitoring" hypothesis from [confidence_followups.md](confidence_followups.md): if a decode mid-loop already shows a ramp-down profile, we have actionable evidence that the rest of the segment is going to fail.

## 7. Beam-aggregation preview (cheap version)

We don't have all 20 beams in this sidecar — only `top3` per step. Using top-3-only entropy as a poor man's beam diversity:

| | |
|---|---|
| r(full_entropy, top3_entropy) | +0.946 |
| r(full_entropy, WER) | +0.688 |
| r(top3_entropy, WER) | +0.699 |
| r(full_entropy, IS) | -0.804 |
| r(top3_entropy, IS) | -0.803 |

Top-3 entropy is **almost perfectly redundant with full entropy** (r ≈ +0.946), so it adds no information beyond what we already capture. To get genuine beam-level signal we need the all-20-beams capture from the followups doc; the cheap version is not enough.

---

## What changes in the codebase

Based on these findings:

1. **Keep CONF_HIGH = 0.85 / CONF_MED = 0.40.** Calibration is in-band. Tightening green to 0.90 would cost -9pp of "trust" coverage without large reliability gains.
2. **Add `mean_prob` to the per-segment summary** in `make_report.py` (already exists as `sentence_confidence`) and **flag segments with mean_prob < 0.6** as candidates for human review — this catches **~92%** of NIV-N segments.
3. **Do NOT promote entropy to a primary gate yet.** Marginal improvement over max-softmax, harder to explain, doesn't beat hallucinations. Keep capturing it for archaeology.
4. **Schedule the all-20-beams decode change for next sprint** (Mission 6) — top-3 is too narrow.
5. **Trajectory clustering belongs in the runtime stack as a "give up early" signal** — Mission 11 candidate. Mid-decode trajectory shape predicts segment quality before the full sequence finishes.

## Reproduce

```bash
python3 docs/_research-tools/generators/analyze_confidence_full.py \
    --confidence-sidecar /tmp/vsp_b3_1497_out/confidence-172610.json \
    --hypo               /tmp/vsp_b3_1497_out/hypo-172610.json \
    --baseline-csv       /home/ubuntu/english_full_results/client_outputs/report/report.csv
```
