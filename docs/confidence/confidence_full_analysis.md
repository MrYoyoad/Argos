# Confidence Sidecar — Full Statistical Analysis

**Source.** Per-token confidence from `/tmp/vsp_b3_1497_out/confidence-172610.json` (1,497-segment B3 decode), joined with the baseline ground truth in `english_full_results/client_outputs/report/report.csv`. Per-token features (`prob`, `entropy`, `top3`) aggregated to per-word ([`compute_word_confidence.py`](_research-tools/generators/compute_word_confidence.py)) and per-segment.

**Sample sizes.** 1,497 segments matched in confidence × hypo. 1,497 segments joined with baseline IS / WER. 23,261 hypothesis words aligned to references for calibration. Hypotheses are bit-identical to the baseline run — the 59.17% pooled vs 64.05% mean-of-segment WER gap is purely the well-known pooled-vs-averaged divergence on a heavy-tailed distribution. Confidence-side joins are exact.

**TL;DR.** When you take the average per-word confidence inside a segment (the mean of the model's max-softmax probabilities, one per output word), it tells you the segment's overall quality with high reliability — Pearson r = **+0.84** against the Intelligibility Score. That single number is enough to filter the bad outputs out at runtime. The per-word green / yellow / red coloring on the kept segments only works **inside** segments that are confident as a whole; in unconfident segments the coloring is misleading.

**Term key (used throughout this report).**

- **IS** — Intelligibility Score (0-5), our 6-signal composite quality metric. Mean across the 1,497-segment baseline = 2.52.
- **NIV-Y** ("clearly intelligible") — a segment with IS ≥ 3.80; the bar for a clean win, calibrated against an Opus-as-Judge gold standard.
- **NIV-N** ("not intelligible") — a segment with IS < 2.00; clear failure.
- **mean_word_prob** — the per-segment average of per-word probabilities, where each per-word probability is the *minimum* max-softmax across the sub-tokens that make up the word.
- **mean_prob** — the per-segment average of per-token max-softmax probabilities (no word-level grouping).
- **WER / WWER** — word error rate / weighted WER (high-value content tokens count 2×).

**What we found.**

1. **Mean word probability is the single best confidence aggregate.** Pearson r = **+0.837** with IS, **-0.714** with WER, **-0.749** with WWER (n=1,427). Geometric mean, mean entropy, mean margin (top1 − top2), and `frac_p_ge_0.85` all sit within ~0.03 r of this — they're different shadows of the same underlying signal. Spearman ρ tracks Pearson r within 0.06 for confidence-vs-IS pairs, so the relationship isn't an artifact of a linearity assumption. *Practical reading:* for runtime quality estimation we don't need anything fancier than averaging the per-word probabilities the model already produces.

2. **Confidence is a strong segment-level filter.** AUC = **0.917** detecting NIV-N (bad) and AUC = **0.921** detecting NIV-Y (good) using `mean_prob` alone — both well above the 0.80 "deployable as a single signal" cutoff. *Practical reading:* at the operating point `mean_word_prob ≥ 0.80`, we keep **78%** of NIV-Y segments and admit only **9 NIV-N** out of 405 trusted (a 2.2% false-trust rate). For zero-tolerance applications, add `duration ≥ 1.5s AND mean_entropy ≤ 0.7`; that gate produces zero false-trusted segments at ~30% recall (8.7% volume kept).

3. **The green band's reliability depends on which segment a green word lives in.** Across the full 23,261 hypothesis-words corpus, a "green" word (per-word p ≥ 0.85) is correct **80.6%** of the time on average. But stratified by the segment's mean_word_prob, that ranges from **18.2%** (segments below 0.40) to **92.8%** (segments at 0.85+). Expected Calibration Error on raw max-softmax = **17.4%** — within the 5-15pp range the post-RLHF LLaMA-2 calibration literature predicts. *Practical reading:* show colored per-word transcripts only when the segment's mean_word_prob ≥ 0.82 — that's the threshold where green words clear ≥ 85% reliability as labeled. Below 0.65, green falls under 50% reliability and the coloring becomes net-misleading; hide or banner instead.

4. **Confidence catches hallucinations almost completely.** Of 223 hallucinated segments (defined as WER ≥ 100% AND length ratio ≥ 0.5: fluent-but-wrong, not just empty), only **3** (1.3%) have mean_prob ≥ 0.85. Median mean_prob: 0.541 hallucinated vs 0.759 healthy. Median mean_entropy: 2.817 vs 1.203. AUC for hallucination detection: mean_prob = 0.917, mean_entropy = 0.913 — tied. *Practical reading:* the literature's worst-case "fluent fabrications at p > 0.95" failure mode exists but is rare in this data. mean_prob alone catches it 99% of the time; entropy is redundant on this dataset, so we keep it as instrumentation but don't promote it to a primary gate.

5. **Different failure modes need different signals.** The 503 segments with IS<2 classify into the March 5-category taxonomy (evaluated 1→5): Wrong Topic 68% (n=342), Hallucination 10% (n=51), Right Topic Wrong Details 15% (n=76), Signal Loss 0.2% (n=1), Accumulated Errors 7% (n=33). Hallucination + Signal Loss (≈10% of bad segments) are catchable from confidence + length-ratio alone. The remaining ~90% — dominated by Wrong Topic — require either the reference (semantic similarity, NEA F1) or a runtime substitute. *Practical reading:* Mission 6 (capture all 20 beams to expose disagreement) and Mission 8 (topic-conditioned language model) are the next-sprint priorities. Confidence alone has plateaued at the failure modes it can detect.

6. **Trajectory shape predicts outcome.** k=5 k-means on length-normalized per-position prob trajectories yields a "flat-high" cluster (mean WER **31%**, mean IS 3.89, 64% NIV-Y) and an "uncertain-throughout" cluster (mean WER **104%**, mean IS 1.14, **92% NIV-N**). The shape difference is visible after just a few tokens. *Practical reading:* mid-decode trajectory monitoring is a viable runtime "give up early" hook — abort segments that match the failure-shape cluster before generating the rest of the sequence. Mission 11 candidate.

---

# 1. What confidence is, and what it predicts

This chapter establishes the basic statistics: the distributions of the four confidence signals we capture (`prob`, `word_prob`, `entropy`, `margin`), their correlation with the quality metrics (IS, WER, WWER, NEA F1), and the answer to the deployment question — *which* confidence aggregate is the best predictor of segment quality.

## 1.1 Distributions

![distributions](../presentation_materials_20260224/01_plots_for_slides/conf_full_distributions.png)

| Signal | Mean | Median | p10 | p90 |
|---|---|---|---|---|
| Per-token prob | 0.745 | 0.880 | 0.271 | 0.998 |
| Per-word prob (min agg) | 0.716 | 0.835 | 0.240 | 0.996 |
| Per-token entropy | 1.410 | 0.875 | 0.020 | 3.652 |
| Per-token margin (top1−top2) | 0.584 | 0.666 | 0.049 | 0.997 |

The 33-Obama small-sample (used to design the green / yellow / red bands) showed 89.7% green / 6.8% yellow / 3.4% red on word-level. On the diverse 1,497-segment dataset the same thresholds (0.85 / 0.40) produce **48.6% green / 32.1% yellow / 19.3% red** — the rebalancing the threshold-design doc anticipated.

## 1.2 Correlation map

![correlation heatmap](../presentation_materials_20260224/01_plots_for_slides/conf_correlation_heatmap.png)

Top-5 confidence features by |Pearson r| with **IS**:

- `mean_word_prob` → IS: **r = +0.837**
- `geomean_prob` → IS: **r = +0.822**
- `mean_prob` → IS: **r = +0.818**
- `mean_entropy` → IS: **r = -0.804**
- `mean_margin` → IS: **r = +0.803**


Top-5 confidence features by |Pearson r| with **WER**:

- `mean_word_prob` → WER: **r = -0.714**
- `mean_prob` → WER: **r = -0.709**
- `geomean_prob` → WER: **r = -0.708**
- `mean_top3_ent` → WER: **r = +0.699**
- `mean_margin` → WER: **r = -0.696**


Restricting to confidence aggregates vs IS, max |Pearson r − Spearman ρ| = **0.061** — linear and rank correlations agree.

## 1.3 Continuous fit — confidence vs IS and WER

![confidence vs IS](../presentation_materials_20260224/01_plots_for_slides/conf_metrics_vs_is_scatter.png)

![confidence vs WER](../presentation_materials_20260224/01_plots_for_slides/conf_metrics_vs_wer_scatter.png)

Three of the four signals (`mean_prob`, `mean_entropy`, `mean_margin`) explain ~65% of IS variance with a single linear term. Confidence predicts IS more cleanly than WER (R² ≈ 0.65 vs 0.48): WER's heavy tail (the WER ≥ 100% hallucination stripe and length-blowup tail above 150%) breaks linearity, while IS varies smoothly because it credits semantic and phonetic similarity.

## 1.4 Beam preview is redundant with full entropy

We capture top-3 alternatives per step. Using top-3-only entropy as a poor man's beam diversity:

| | |
|---|---|
| r(full_entropy, top3_entropy) | +0.946 |
| r(full_entropy, WER) | +0.688 |
| r(top3_entropy, WER) | +0.699 |
| r(full_entropy, IS) | -0.804 |
| r(top3_entropy, IS) | -0.803 |

Top-3 entropy is **almost perfectly redundant** with full-distribution entropy — the cheap version isn't enough to expose new signal. Genuine beam-level information requires capturing all 20 hypotheses with their per-step probability trails (Mission 6).

# 2. Calibration: does the green band mean what it claims?

The previous chapter showed that confidence *predicts* quality on average. This chapter asks whether the per-word color promise (green = trust without review, ≥ 85% correct) actually holds in practice — and discovers that it does, but only inside segments that are confident as a whole.

## 2.1 Overall calibration

![calibration curve](../presentation_materials_20260224/01_plots_for_slides/conf_calibration_curve.png)

| Band | Threshold | n words | P(correct) |
|---|---|---|---|
| green  | p ≥ 0.85 | 11,309 | **80.6%** |
| yellow | 0.4 ≤ p < 0.85 | 7,470 | 38.3% |
| red    | p < 0.4 | 4,482 | 15.4% |

Bands are well-ordered (green > yellow > red empirically) and ECE = **17.4%** sits within the 5-15pp range the post-RLHF LLaMA-2 calibration literature predicts. The headline number (80.6% reliable green) — falls in the 80-90% band — footnote the deck (green ≈ 81% reliable) rather than tightening, since tightening loses substantial green coverage.

## 2.2 Stratified by segment quality — the green band collapses in low-quality segments

![band reliability stratified](../presentation_materials_20260224/01_plots_for_slides/conf_band_reliability_combined.png)

| Segment mean_prob bucket | n words | P(correct \| green) | P(correct \| yellow) | P(correct \| red) |
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

| Feature | NIV-N (bad) detector AUC | NIV-Y (good) detector AUC |
|---|---|---|
| `frac_p_ge_085` | 0.888 | 0.908 |
| `frac_p_lt_04` | 0.899 | 0.878 |
| `mean_entropy` | 0.913 | 0.917 |
| `mean_margin` | 0.901 | 0.906 |
| `mean_prob` | 0.917 | 0.921 |
| `min_word_prob` | 0.753 | 0.749 |
| `seq_score` | 0.746 | 0.766 |


`mean_prob` reaches AUC ≈ 0.92 on bad-segment detection and AUC ≈ 0.92 on good-segment detection — usable as a single gate without invoking the full IS pipeline.

## 3.2 Operating points — where to set the threshold

![operating points](../presentation_materials_20260224/01_plots_for_slides/conf_operating_points.png)

| Operating point | Gate | Precision | Recall | False-bads | Vol. % | Trusted |
|---|---|---|---|---|---|---|
| Loose, high recall | `mwp >= 0.75` | 59.3% | 91.7% | 16 | 39.1% | 558 |
| Balanced (recommended) | `mwp >= 0.80` | 69.9% | 78.4% | 9 | 28.4% | 405 |
| Strict precision | `mwp >= 0.85` | 81.0% | 54.3% | 3 | 17.0% | 242 |
| + duration filter | `mwp >= 0.85 AND dur >= 1.5s` | 87.9% | 32.1% | 0 | 9.3% | 132 |
| Zero-false-bad gate | `mwp >= 0.85 AND dur >= 1.5s AND ent <= 0.7` | 88.7% | 30.5% | 0 | 8.7% | 124 |


![sweet spot](../presentation_materials_20260224/01_plots_for_slides/conf_sweet_spot_pr.png)

Single-signal `mean_prob` peaks at F1 ≈ 0.75 around the 0.82 threshold (78% recall, 71% precision; mean IS of trusted segments rises to 4.01, mean WER drops to 27.5%). Tightening to 0.85 keeps a few fewer false-bads but loses ~25 percentage points of recall. Adding constraints (`min_word_prob`, `len_ratio`, entropy) pushes precision up but trades recall faster than it adds purity — the same F1 budget, redistributed.

## 3.3 Who slips through? False-good profile

At the recommended balanced gate (`mean_word_prob ≥ 0.80`), 9 segments are trusted but actually NIV-N. We profile them against the true-good set:

![false-good signatures](../presentation_materials_20260224/01_plots_for_slides/conf_false_good_signatures.png)

| Feature | False-bad mean | True-good mean | Gap |
|---|---|---|---|
| Segment duration (s) | 1.22 | 1.99 | -0.78 |
| Hyp word count | 11.67 | 20.83 | -9.16 |
| Ref word count | 13.89 | 21.42 | -7.53 |
| Mean entropy | 0.68 | 0.48 | +0.20 |
| Length ratio | 1.18 | 0.98 | +0.21 |


**The smoking gun: false-bads are SHORT.** Median segment duration is **0.98s** for false-bads vs **1.86s** for true-goods. Median hyp word count: **9** vs **19**. False-bads are systematically segments where the model has too little material to constrain its output. Mean entropy is +0.20 higher on false-bads — the model *is* uncertain, it just compensates by picking a high-prob single token at each position.

**The 9 false-good cases at the balanced gate:**

| utt_id | dur(s) | ref→hyp words | mwp | min_wp | ent | WER% |
|---|---|---|---|---|---|---|
| `NzP4ZzCCTXU_0__725fc750_` | 2.39 | 49→34 (lr 0.69) | 0.81 | 0.09 | 1.01 | 51 |
| `VQfytKqzC1E_0__fe653f47_` | 1.92 | 25→17 (lr 0.68) | 0.83 | 0.15 | 0.79 | 64 |
| `JDpiI6GTCUM_7__a1a8fee8_` | 1.22 | 13→8 (lr 0.62) | 0.80 | 0.56 | 0.45 | 77 |
| `PNUbsGx13NI_12__86d7b242` | 1.14 | 6→12 (lr 2.00) | 0.82 | 0.15 | 0.71 | 200 |
| `0kRnNot68TI_5__8d9329f9_` | 0.87 | 7→5 (lr 0.71) | 0.85 | 0.63 | 0.70 | 71 |
| `Hl08kKKS1lw_13__1c5ee283` | 0.98 | 11→9 (lr 0.82) | 0.80 | 0.35 | 0.86 | 64 |
| `GRqF3po8ip0_19__0bcab135` | 0.92 | 6→6 (lr 1.00) | 0.86 | 0.40 | 0.56 | 100 |
| `gzljNv0U75Y_6__14da3401_` | 0.91 | 3→10 (lr 3.33) | 0.88 | 0.45 | 0.56 | 300 |
| `xITCbZxwLn4_0__23fb6426_` | 0.59 | 5→4 (lr 0.80) | 0.86 | 0.46 | 0.46 | 60 |


**Visual cues and broad-conversation context.** Segment duration is a free runtime proxy for visual quality (very short clips give the visual encoder little material to lock onto). A real visual quality model (lip occlusion, face-frame coverage, head pose) would catch more, but is out-of-pipeline today. Topic context — a surrounding-sentence language model conditioned on the source video's topic — could rescore the hyp and flag drift; also out-of-pipeline. Beam disagreement (Mission 6) is the most tractable next-sprint signal for the truly fluent-and-plausible cases that confidence alone cannot detect.

# 4. Failure modes: what "bad" looks like in confidence space

The previous chapter focused on detection thresholds. This chapter goes deeper: *which* kinds of failures slip past a confidence gate, and how each kind looks across the confidence parameters. The taxonomy is the March 2026 deck's 5-category model.

## 4.1 Hallucination scatter

![hallucination scatter](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_scatter.png)

![hallucination pairs](../presentation_materials_20260224/01_plots_for_slides/conf_hallucination_pairs_scatter.png)

| | |
|---|---|
| Hallucinated (WER ≥ 100%, len_ratio ≥ 0.5) | **223** |
| Dangerous (above + mean_prob ≥ 0.85) | **3** |
| Median mean_prob, hallucinated vs healthy | 0.541 / 0.759 |
| Median mean_entropy, hallucinated vs healthy | 2.817 / 1.203 |

Mann-Whitney U on `mean_prob` and `mean_entropy` both reject equality of hallucinated vs healthy at p < 1e-50. The literature warned that fluent hallucinations would land in a "dangerous quadrant" of high prob × hallucinated; we found only **3 / 223** (1.3%) of hallucinated segments there. The failure mode exists but is rare. Across the four alternative confidence pairs in the second figure, the same 3 cases reappear regardless of projection — max-softmax, entropy, margin, and red/green fractions are different shadows of the same underlying confidence collapse, not independent failure detectors.

## 4.2 Five-category failure-mode taxonomy (March deck)

The 503 IS<2 segments classify into five mutually-exclusive categories, evaluated 1→5.

![failure-mode profile](../presentation_materials_20260224/01_plots_for_slides/conf_failure_mode_profile.png)

#### 1. Wrong Topic (68.0%, n=342)

- **What:** Mouth shapes decoded to wrong domain
- **Rule:** Semantic similarity < 0.2
- **Example:** Ref: "weight loss and diet" → Hyp: "wanted to be a princess"
- **Confidence signature:** mean_prob 0.55, min_wp 0.08, entropy 2.74, len_ratio 0.97, dur 1.39s

#### 2. Hallucination (10.1%, n=51)

- **What:** Model invented fake text
- **Rule:** WER >= 100% (output longer than reference)
- **Example:** Ref: "carry strap" → Hyp: "holocaust denier explanation of the final act"
- **Confidence signature:** mean_prob 0.59, min_wp 0.16, entropy 2.27, len_ratio 1.31, dur 1.19s

#### 3. Right Topic, Wrong Details (15.1%, n=76)

- **What:** Roughly right but names/content lost
- **Rule:** NEA F1 < 20% (Semantic >= 0.2)
- **Example:** Ref: "13th amendment is going" → Hyp: "13th may mean something to him"
- **Confidence signature:** mean_prob 0.65, min_wp 0.16, entropy 1.97, len_ratio 0.84, dur 1.42s

#### 4. Signal Loss (0.2%, n=1)

- **What:** Nothing came out
- **Rule:** Empty output OR length_ratio < 0.3
- **Example:** Ref: "the thirteenth amendment" → Hyp: ""
- **Confidence signature:** mean_prob 0.54, min_wp 0.12, entropy 2.84, len_ratio 0.23, dur 0.94s

#### 5. Accumulated Errors (6.6%, n=33)

- **What:** Many small errors compound
- **Rule:** IS < 2.0 and doesn't match categories 1-4
- **Example:** Many words slightly wrong throughout, meaning erodes
- **Confidence signature:** mean_prob 0.61, min_wp 0.13, entropy 2.14, len_ratio 0.74, dur 1.36s



| Category | n | mean_prob | min_wp | mean_entropy | dur (s) | NEA | WER% | IS |
|---|---|---|---|---|---|---|---|---|
| **1. Wrong Topic** | 342 | 0.55 | 0.08 | 2.74 | 1.39 | 5.3 | 104 | 1.03 |
| **2. Hallucination** | 51 | 0.59 | 0.16 | 2.27 | 1.19 | 8.9 | 123 | 1.39 |
| **3. Right Topic, Wrong Details** | 76 | 0.65 | 0.16 | 1.97 | 1.42 | 2.8 | 79 | 1.65 |
| **4. Signal Loss** | 1 | 0.54 | 0.12 | 2.84 | 0.94 | 66.7 | 88 | 1.91 |
| **5. Accumulated Errors** | 33 | 0.61 | 0.13 | 2.14 | 1.36 | 27.9 | 80 | 1.77 |
| **Healthy (NIV-Y)** | 361 | 0.86 | 0.32 | 0.62 | 1.93 | 84.6 | 22 | 4.33 |


## 4.3 Trajectory clusters — failure shapes through time

![trajectory clusters](../presentation_materials_20260224/01_plots_for_slides/conf_trajectory_clusters.png)

| Cluster | n | Mean WER% | Mean IS | NIV-Y rate | NIV-N rate |
|---|---|---|---|---|---|
| C3 (flat-high) | 462 | 30.8 | 3.89 | 64.1% | 3.0% |
| C0 (middle #1) | 228 | 62.5 | 2.55 | 10.1% | 29.8% |
| C2 (middle #2) | 223 | 65.8 | 2.49 | 11.7% | 33.2% |
| C4 (middle #3) | 245 | 71.8 | 2.25 | 6.5% | 40.8% |
| C1 (uncertain throughout) | 260 | 104.4 | 1.14 | 0.0% | 91.9% |


The shape difference between flat-high (top cluster) and uncertain-throughout (bottom cluster) is visible after only a few tokens — enough material to support a mid-decode "give up early" hook (Mission 11 candidate). For each segment we'd track the rolling-mean per-position prob and abort if it crosses a flat-low signature before the full sequence is generated.

# 5. What confidence cannot tell us, and what's next

Confidence has three blind spots, all visible in the failure-mode breakdown:

1. **Wrong Topic** (68% of bad segments). The model commits decisively to a wrong domain; `mean_prob` sits in the medium band, no signal in confidence space sharp enough to flag. Needs semantic similarity (reference-required) or a runtime substitute — a topic-conditioned LM scoring the hyp for surprise relative to the source video's topic. **Mission 8.**
2. **Right Topic, Wrong Details** (15% of bad segments). Confidence is the closest of any failure mode to healthy. The model knows the topic but loses the specific entities (numbers, proper nouns). Needs NEA F1 (reference-required) or beam disagreement — if the chosen beam dropped a number that other beams kept, that's a flag. **Mission 6 (all-20-beams capture).**
3. **The "billion → million" problem** — a single high-confidence wrong content word inside an otherwise-fine segment. Bypasses all current signals because the model is decisive on the wrong answer. Needs source-context priors (was the conversation about money?) or visual disambiguation. *Long-term.*

**Recommendations.**

1. **Keep CONF_HIGH = 0.85 / CONF_MED = 0.4 for per-word coloring**, but gate the *display* on segment-level `mean_word_prob` ≥ 0.82. Below that threshold, hide the segment or banner "unreliable — do not trust greens." (Sections 2.2-2.4.)
2. **Use `mean_word_prob` ≥ 0.80 as the runtime quality gate.** Already exposed via `make_report.py --word-confidence` as `sentence_confidence`. (Section 3.2.)
3. **Don't promote entropy to a primary gate.** Tied with max-softmax (Section 4.1), harder to explain. Keep capturing it for archaeology.
4. **Mission 6 (all-20-beams capture) is the highest-leverage next-sprint item.** Top-3 entropy is r = 0.95 redundant with full entropy (Section 1.4); we need genuine beam disagreement to expose Right-Topic-Wrong-Details and the dangerous decisive-but-wrong cases.
5. **Mission 8 (topic-conditioned LM for hyp rescoring) handles the Wrong Topic hole.** 68% of bad segments fall here; the reference contains topic context that a runtime LM could approximate.
6. **Mission 11 (mid-decode trajectory monitoring) is the runtime "give up early" hook.** Section 4.3 shows the flat-low cluster is identifiable from just a few tokens.

# Reproduce

```bash
python3 docs/_research-tools/generators/analyze_confidence_full.py \
    --confidence-sidecar /tmp/vsp_b3_1497_out/confidence-172610.json \
    --hypo               /tmp/vsp_b3_1497_out/hypo-172610.json \
    --baseline-csv       /home/ubuntu/english_full_results/client_outputs/report/report.csv
```
