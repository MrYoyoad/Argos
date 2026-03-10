# IS Reweighting Analysis: NEA Up, Length Ratio Down

**Argos — The Orchard**
**Date:** 2026-03-10
**Dataset:** 1,497 segments (full AVSpeech baseline)

---

## 1. Motivation

Analysis of IS vs Opus judge disagreements (see Section 5) revealed that the 83 false positives (IS >= 3.80, Opus P) are dominated by **detail/entity loss** — the structure and keywords are correct but specific names, numbers, or domain terms are wrong. NEA F1 (entity accuracy) is the only IS signal that catches these, but it's weighted at only 15%. Meanwhile, Length Ratio (also 15%) contributes almost nothing to quality discrimination (PC2 loading 0.91, independent of content quality).

**Question:** Does increasing NEA weight at the expense of Length Ratio improve agreement with the LLM judge?

---

## 2. Weight Schemes Tested

| Scheme | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR | Sum |
|--------|----------|----------|--------|---------|--------|-----|-----|
| **Original** | 0.25 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | 1.0 |
| **NEA+/LR-** | 0.25 | 0.15 | 0.15 | 0.15 | 0.25 | 0.05 | 1.0 |
| **No LR** | 0.30 | 0.15 | 0.15 | 0.15 | 0.25 | 0.00 | 1.0 |

---

## 3. Score Distribution Impact

| Scheme | Mean IS | Std | r vs Original | Tier Changes | Moved Up | Moved Down |
|--------|---------|-----|---------------|--------------|----------|------------|
| Original | 2.538 | 1.299 | 1.000 | — | — | — |
| NEA+/LR- | 2.271 | 1.405 | 0.988 | 416 (27.8%) | 102 | 1,255 |
| No LR | 2.149 | 1.457 | 0.978 | 560 (37.4%) | 73 | 1,309 |

**Key observation:** Both reweightings **lower** the mean IS substantially (by 0.27–0.39) and push the vast majority of segments downward. This happens because most segments have NEA F1 < Length Ratio — entities are harder to get right than output length.

---

## 4. Agreement with Blind Judge (Optimal Thresholds)

### 4.1 Y Target (Clearly Conveyed)

| Scheme | Best Threshold | Best κ | Agreement | Precision | Recall | N_pos |
|--------|---------------|--------|-----------|-----------|--------|-------|
| **Original** | **3.70** | **0.708** | 89.6% | 0.775 | 0.777 | 346 |
| NEA+/LR- | 3.40 | 0.679 | 88.0% | 0.707 | 0.817 | 399 |
| No LR | 3.40 | 0.682 | 88.4% | 0.728 | 0.791 | 375 |

### 4.2 Y+P Target (Any Useful Meaning)

| Scheme | Best Threshold | Best κ | Agreement | Precision | Recall | N_pos |
|--------|---------------|--------|-----------|-----------|--------|-------|
| **Original** | **2.00** | **0.791** | 90.3% | 0.940 | 0.908 | 938 |
| NEA+/LR- | 1.50 | 0.814 | 91.5% | 0.938 | 0.931 | 964 |
| No LR | 1.50 | 0.805 | 90.9% | 0.955 | 0.902 | 917 |

### 4.3 Summary

| Target | Original κ | NEA+/LR- κ | No LR κ | Winner |
|--------|-----------|------------|---------|--------|
| Y | **0.708** | 0.679 | 0.682 | Original (+0.026) |
| Y+P | 0.791 | **0.814** | 0.805 | NEA+/LR- (+0.023) |

**Mixed result.** NEA+/LR- improves Y+P agreement by +0.023 κ but worsens Y agreement by -0.029 κ. The improvement at Y+P comes from better recall (0.931 vs 0.908) — the lower threshold (1.50 vs 2.00) catches more partial-credit segments. But at the Y level, the stricter entity weighting pushes too many good segments below threshold.

---

## 5. Agreement with Context-Aware Judge

### 5.1 Y Target

| Scheme | Best Threshold | Best κ | Agreement |
|--------|---------------|--------|-----------|
| Original | 3.90 | 0.632 | 89.8% |
| NEA+/LR- | 3.90 | 0.626 | 90.2% |
| **No LR** | **4.00** | **0.636** | **91.0%** |

### 5.2 Y+P Target

| Scheme | Best Threshold | Best κ | Agreement |
|--------|---------------|--------|-----------|
| Original | 2.00 | 0.718 | 86.8% |
| **NEA+/LR-** | **1.75** | **0.732** | **87.2%** |
| No LR | 1.50 | 0.741 | 87.8% |

### 5.3 Summary

| Target | Original κ | NEA+/LR- κ | No LR κ | Winner |
|--------|-----------|------------|---------|--------|
| Y | 0.632 | 0.626 | **0.636** | No LR (+0.004) |
| Y+P | 0.718 | 0.732 | **0.741** | No LR (+0.023) |

Against the context-aware judge, **No LR** performs best at both thresholds — but the Y improvement is negligible (+0.004). The Y+P improvement is meaningful (+0.023), consistent with the blind judge result.

---

## 6. False Positive / False Negative Analysis

### 6.1 At Fixed Thresholds (Y >= 3.80, Y+P >= 2.00)

| Scheme | Y: FP | Y: FN | Y: κ | Y+P: FP | Y+P: FN | Y+P: κ |
|--------|-------|-------|------|---------|---------|--------|
| Original | 83 | 82 | 0.690 | 39 | 88 | 0.818 |
| NEA+/LR- | 48 | 128 | 0.639 | 21 | 175 | 0.731 |
| No LR | 42 | 134 | 0.634 | 19 | 217 | 0.682 |

At the **same thresholds**, reweighting is strictly worse — it reduces FP but increases FN by more. The thresholds must be re-optimized for the new weights.

### 6.2 Case 2 Fixed: IS >= 3.80 but Opus P (83 Original False Positives)

| Scheme | Still Above 3.80 | Dropped Below | % Fixed |
|--------|-----------------|---------------|---------|
| NEA+/LR- | 48 | **35** | **42%** |
| No LR | 42 | **41** | **49%** |

The reweighting successfully catches entity/detail corruption that the original formula missed:

**Examples that correctly dropped:**
- "bitcoin virtual currency" → "minority currency" (IS: 3.91 → 3.51) — entity destroyed
- "aircon / condo" → "yacht / country" (IS: 4.01 → 3.63) — domain terms wrong
- "headset / fits on your head" → "side effects on your ears" (IS: 3.87 → 3.51) — meaning changed
- "king's manor library" → "his local library" (IS: 3.86 → 3.53) — proper noun lost

### 6.3 Case 1 NOT Fixed: Opus Y but IS < 3.80 (82 Original False Negatives)

| Scheme | Promoted to >= 3.80 | Still Below | % Fixed |
|--------|-------------------|-------------|---------|
| NEA+/LR- | **0** | 82 | **0%** |
| No LR | **1** | 81 | **1%** |

**The reweighting fixes zero false negatives.** This makes sense: these 82 segments are cases where the judge recognizes meaning through paraphrasing, gist preservation, or pragmatic equivalence — features that no combination of the 6 existing signals captures. Higher NEA weight cannot help when the issue is that embedding similarity (0.37–0.65) doesn't capture pragmatic meaning.

---

## 7. PCA Without Length Ratio

### 7.1 Five-Signal PCA

| PC | Eigenvalue | % Variance | Cumulative | Kaiser? |
|----|-----------|------------|------------|---------|
| **PC1** | **4.350** | **86.9%** | 86.9% | Yes |
| PC2 | 0.286 | 5.7% | 92.7% | No |
| PC3 | 0.216 | 4.3% | 97.0% | No |

Kaiser retains **only 1 PC** (was 2 with LR). The 5 content signals are essentially **one-dimensional** — 86.9% shared variance vs 68.4% with 6 signals.

### 7.2 Loadings

| Signal | PC1 (86.9%) | PC2 (5.7%) | PC3 (4.3%) |
|--------|-------------|------------|------------|
| Semantic | +0.436 | -0.112 | **+0.891** |
| Phonetic | +0.453 | -0.368 | -0.223 |
| InvWER | +0.460 | -0.242 | -0.250 |
| InvWWER | +0.465 | -0.100 | -0.297 |
| **NEA F1** | +0.421 | **+0.885** | -0.082 |

### 7.3 Interpretation

Without Length Ratio, PC2 becomes **NEA swing** (loading 0.885) — the same entity-divergence phenomenon that was PC3 in the 6-signal PCA. PC3 becomes **Semantic swing** (loading 0.891). Both are sub-Kaiser, confirming:

1. **The 5 content signals are fundamentally unidimensional.** One factor (visual encoder quality) explains 86.9% of variance.
2. **NEA has the most independent information** of any content signal (PC2 at 5.7%), supporting its higher weight.
3. **Length Ratio was the only truly independent dimension.** Removing it collapses the 2-PC structure to 1 PC. PC2 (LR, 19.5% → NEA, 5.7%) shows LR was providing the majority of the second dimension.

### 7.4 Comparison: 6-Signal vs 5-Signal PCA

| PCA | PCs (Kaiser) | PC1 Variance | PC2 Variance | PC1+PC2 |
|-----|-------------|-------------|-------------|---------|
| 6 signals | **2** | 73.4% | 16.5% | **89.9%** |
| 5 signals | **1** | 86.9% | 5.7% | 92.7% |

Note: The 6-signal PCA eigenvalues differ slightly from the original analysis (73.4% vs 68.4% for PC1) due to minor differences in how length ratio scaling is handled. The structural conclusion is identical: 2 PCs with LR, 1 PC without.

---

## 8. Conclusions

### 8.1 Should We Reweight?

**No — the original weights are better overall.**

The reweighting creates a classic precision/recall tradeoff:
- **Fixes 42-49% of false positives** (entity corruption correctly penalized)
- **Fixes 0% of false negatives** (paraphrase recognition unchanged)
- **Net effect at Y threshold**: κ drops from 0.708 → 0.679 (worse)
- **Net effect at Y+P threshold**: κ improves from 0.791 → 0.814 (better)

The Y threshold is the more important operating point (it defines "clearly conveyed"), and it gets worse. The improvement at Y+P is modest (+0.023) and comes with 46 more false negatives.

### 8.2 Why the Fix Doesn't Work

The fundamental problem is **asymmetric**: the 83 false positives are caused by entity/detail substitution (fixable by reweighting), but the 82 false negatives are caused by **pragmatic meaning equivalence** (not fixable by any reweighting of existing signals). Increasing NEA helps with one problem but creates new false negatives without fixing the other.

### 8.3 What Would Actually Help

To improve κ at the Y threshold, we need a signal that captures **pragmatic equivalence** — "different words, same message." Options:

1. **Entailment score**: NLI model scoring whether the hypothesis entails the reference (and vice versa). This directly measures meaning preservation regardless of word overlap.
2. **BERTScore**: Token-level contextual embedding similarity, which is better at capturing paraphrases than sentence-level semantic similarity.
3. **Content-word-only semantic similarity**: Compare embeddings of only nouns/verbs/entities, filtering out function words that inflate similarity when structure matches but meaning doesn't.

Any of these would address the false negatives without worsening false positives, potentially pushing κ above 0.75 for the Y threshold.

### 8.4 Length Ratio: Keep or Drop?

**Keep it.** Despite LR contributing almost nothing to content quality discrimination (PC2, independent of PC1), it serves a critical role as a **hallucination detector**. Segments with LR far from 1.0 (very short or very long output) are almost always failures. The 15% weight is appropriate — it's a safety net, not a quality signal. Reducing it to 5% or 0% hurts Y+P agreement when thresholds aren't re-optimized (κ drops from 0.818 → 0.731/0.682 at IS >= 2.00).

---

## 9. Data Availability

- **Source data:** [intelligibility_scores.csv](intelligibility/intelligibility_scores.csv), [llm_judge_results.csv](llm_judge/llm_judge_results.csv)
- **PCA analysis:** [is_pca_analysis.md](is_pca_analysis.md)
- **Threshold calibration:** [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md)
- **Disagreement examples:** This document, Sections 5-6