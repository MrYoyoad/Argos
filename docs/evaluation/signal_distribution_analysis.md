# IS Signal Distribution Analysis: Means, Stds, and Discriminative Power

**Argos — The Orchard**
**Date:** 2026-03-10
**Dataset:** 1,497 YouTube segments + 184 LRS3 segments (V4, LRS3-trained k-means)

---

## 1. Global Statistics (1,497 YouTube Segments)

All signals normalized to 0–1 scale (WER/WWER inverted: 1 = perfect, 0 = 100% error).

| Signal | Mean | Std | Median | IQR | Skew | Kurtosis |
|--------|------|-----|--------|-----|------|----------|
| **Semantic** | 0.437 | 0.308 | 0.412 | 0.532 | +0.22 | −1.15 |
| **Phonetic** | 0.552 | 0.276 | 0.588 | 0.448 | −0.34 | −0.89 |
| **InvWER** | 0.360 | 0.393 | 0.389 | 0.567 | −1.60 | +8.12 |
| **InvWWER** | 0.381 | 0.334 | 0.400 | 0.511 | −0.86 | +3.66 |
| **NEA F1** | 0.389 | 0.367 | 0.353 | 0.706 | +0.32 | −1.36 |
| **Length Ratio** | 0.925 | 0.348 | 0.947 | 0.218 | +0.91 | +11.09 |

**Key observations:**
- **Semantic** has the flattest distribution (skew ≈ 0, kurtosis ≈ −1): near-uniform spread across 0–1 range
- **InvWER** is heavily left-skewed (−1.60) with extreme kurtosis (+8.12): many segments cluster at 0% WER or >100% WER, with a heavy tail of hallucinations
- **NEA F1** has the widest IQR (0.706): most bimodal of the content signals (either entities are completely wrong or mostly right)
- **Length Ratio** is tightly clustered near 1.0 (IQR = 0.218) with occasional extreme outliers (kurtosis +11.09)

---

## 2. Signal Means by IS Tier

| Signal | Tier 1 (Failed) | Tier 2 (Poor) | Tier 3 (Fair) | Tier 4 (Good) | Tier 5 (Excellent) | Range (5−1) |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Semantic** | 0.047 | 0.208 | 0.409 | 0.626 | 0.865 | **0.819** |
| **Phonetic** | 0.131 | 0.365 | 0.583 | 0.744 | 0.885 | 0.754 |
| **InvWER** | −0.159 | 0.107 | 0.380 | 0.596 | 0.816 | **0.974** |
| **InvWWER** | −0.018 | 0.114 | 0.385 | 0.591 | 0.804 | 0.822 |
| **NEA F1** | 0.003 | 0.103 | 0.326 | 0.606 | 0.896 | **0.893** |
| **Length Ratio** | 0.726 | 0.941 | 0.964 | 0.971 | 0.977 | 0.252 |

### Within-Tier Standard Deviations

| Signal | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 | Mean Within-Tier |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Semantic** | 0.073 | 0.127 | 0.152 | 0.159 | 0.118 | **0.126** |
| **Phonetic** | 0.124 | 0.116 | 0.116 | 0.096 | 0.074 | **0.105** |
| **InvWER** | 0.413 | 0.200 | 0.150 | 0.131 | 0.105 | 0.200 |
| **InvWWER** | 0.202 | 0.232 | 0.136 | 0.115 | 0.106 | 0.158 |
| **NEA F1** | 0.019 | 0.156 | 0.234 | 0.256 | 0.124 | 0.158 |
| **Length Ratio** | 0.717 | 0.281 | 0.192 | 0.142 | 0.084 | 0.283 |

### Variance Reduction by IS Tier

How much knowing the tier reduces signal variance (1 − mean_within_std / global_std):

| Signal | Variance Reduction |
|--------|:-:|
| **Phonetic** | **61.9%** |
| **Semantic** | **59.3%** |
| **NEA F1** | 57.0% |
| **InvWWER** | 52.6% |
| **InvWER** | 49.2% |
| **Length Ratio** | 18.5% |

Phonetic and Semantic are the most "tier-coherent" — their within-tier variance is smallest relative to global variance.

---

## 3. Signal Means by Opus Judge Category

| Signal | N (n=526) | P (n=626) | Y (n=345) | Range (Y−N) |
|--------|:-:|:-:|:-:|:-:|
| **Semantic** | 0.130 | 0.482 | 0.821 | **0.691** |
| **Phonetic** | 0.266 | 0.632 | 0.843 | 0.576 |
| **InvWER** | 0.007 | 0.446 | 0.739 | 0.732 |
| **InvWWER** | 0.074 | 0.453 | 0.720 | 0.646 |
| **NEA F1** | 0.078 | 0.444 | 0.765 | 0.687 |
| **Length Ratio** | 0.837 | 0.965 | 0.985 | 0.149 |

### Normalized (z-scores from global mean)

| Signal | N | P | Y |
|--------|:-:|:-:|:-:|
| **Semantic** | **−0.994** | +0.147 | **+1.248** |
| Phonetic | −1.036 | +0.290 | +1.053 |
| InvWER | −0.897 | +0.221 | +0.966 |
| InvWWER | −0.922 | +0.216 | +1.014 |
| NEA F1 | −0.849 | +0.149 | +1.024 |
| Length Ratio | −0.253 | +0.117 | +0.175 |

**Key finding:** Semantic has the **highest z-score spread** for Y (+1.248), meaning the judge's Y segments are further from the mean on Semantic than on any other signal. This is the first hint that Semantic carries unique judge-predictive information.

### Within-Judge Standard Deviations

| Signal | N | P | Y | Mean Within-Judge |
|--------|:-:|:-:|:-:|:-:|
| **Semantic** | 0.128 | 0.193 | 0.158 | **0.160** |
| **Phonetic** | 0.178 | 0.164 | 0.112 | **0.151** |
| InvWER | 0.326 | 0.265 | 0.183 | 0.258 |
| InvWWER | 0.226 | 0.237 | 0.187 | 0.217 |
| NEA F1 | 0.161 | 0.309 | 0.279 | 0.249 |
| Length Ratio | 0.512 | 0.218 | 0.143 | 0.291 |

### Variance Reduction by Judge Category

| Signal | Variance Reduction |
|--------|:-:|
| **Semantic** | **48.2%** |
| **Phonetic** | **45.1%** |
| InvWWER | 35.0% |
| InvWER | 34.3% |
| NEA F1 | 32.0% |
| Length Ratio | 16.3% |

**Semantic leads:** Knowing the judge's Y/P/N category reduces Semantic variance by 48.2%, more than any other signal. Semantic is the most "judge-coherent" signal.

---

## 4. Effect Sizes

### 4.1 Range / Global Std

| Signal | IS Tiers (5−1) | Opus (Y−N) | WER Bins (best−worst) |
|--------|:-:|:-:|:-:|
| **Semantic** | **2.655** | **2.242** | 2.467 |
| Phonetic | 2.733 | 2.089 | 2.614 |
| InvWER | 2.480 | 1.863 | 2.599 |
| InvWWER | 2.463 | 1.936 | 2.535 |
| NEA F1 | 2.433 | 1.873 | 2.334 |
| Length Ratio | 0.724 | 0.428 | 0.335 |

Against IS tiers and WER bins, all content signals are similar (~2.3–2.7). Against the **Opus judge**, Semantic stands out at 2.242 vs others averaging 1.940 — **16% higher** effect size.

### 4.2 Cohen's d (Pairwise)

| Comparison | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Y vs N** | **4.91** | 3.71 | 2.63 | 3.05 | 3.19 | 0.37 |
| **Y vs P** | **1.87** | 1.42 | 1.23 | 1.21 | 1.08 | 0.10 |
| **P vs N** | **2.12** | **2.14** | 1.49 | 1.64 | 1.45 | 0.34 |
| **Tier 5 vs 1** | 8.22 | 7.51 | 3.34 | 5.21 | **9.71** | 0.51 |
| **Tier 5 vs 3** | 3.33 | 3.05 | 3.32 | **3.40** | 2.97 | 0.09 |
| **Tier 3 vs 1** | 2.91 | **3.79** | 1.85 | 2.41 | 1.82 | 0.49 |

**Critical finding:** For judge-based comparisons, Semantic has the **largest Cohen's d at every boundary**:
- Y vs N: d = **4.91** (vs 3.71 for Phonetic, the next best) — 32% larger
- Y vs P: d = **1.87** (vs 1.42) — 32% larger
- P vs N: d = 2.12, essentially tied with Phonetic (2.14)

For IS tier comparisons, NEA F1 dominates Tier 5 vs 1 (d = 9.71) because NEA is near-zero in Tier 1 and near-perfect in Tier 5. This is an IS construction artifact (NEA and WER are direct inputs to the formula).

### 4.3 Eta-Squared (Proportion of Variance Explained by Grouping)

| Grouping | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|----------|:-:|:-:|:-:|:-:|:-:|:-:|
| **IS Tier** | 0.817 | **0.851** | 0.698 | 0.754 | 0.746 | 0.064 |
| **Opus Judge** | **0.716** | 0.668 | 0.519 | 0.556 | 0.504 | 0.035 |
| **Topic** | 0.018 | 0.013 | **0.027** | **0.027** | 0.018 | 0.016 |
| **Failure Mode** | 0.659 | **0.706** | 0.639 | 0.418 | 0.426 | **0.686** |

**IS Tier** explains 82–85% of Semantic/Phonetic variance, but only 70% of InvWER — WER has more residual variance within tiers. **Opus Judge** explains 72% of Semantic variance, more than any other signal (67% for Phonetic, only 50% for NEA F1). **Topic** explains < 3% of any signal — topic is not a major driver of signal values.

---

## 5. Semantic's Unique Discriminative Power

### 5.1 Correlation with Judge

| Metric | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| **r (Pearson)** | **0.846** | 0.806 | 0.714 | 0.741 | 0.710 | 0.172 |
| **ρ (Spearman)** | **0.846** | 0.822 | 0.811 | 0.798 | 0.704 | 0.207 |
| **r with IS** | 0.921 | **0.943** | 0.849 | 0.881 | 0.864 | 0.226 |

Semantic has the **highest correlation with the judge** (r = 0.846) but is **not** the highest correlated with IS (Phonetic is, at 0.943). This gap between r(Judge) and r(IS) is the "unique information" that Semantic carries about human-like meaning assessment.

### 5.2 Partial Correlations

**Controlling for IS** (what does each signal tell the judge beyond what IS already captures?):

| Signal | r_partial(Judge | IS) | p-value |
|--------|:-:|:-:|
| **Semantic** | **+0.309** | **2.0e-34** |
| Phonetic | +0.029 | 0.27 |
| InvWER | −0.026 | 0.32 |
| InvWWER | −0.030 | 0.25 |
| NEA F1 | −0.093 | 3.2e-04 |
| Length Ratio | −0.039 | 0.14 |

**This is the most important table in this document.** After controlling for IS, **only Semantic retains significant predictive power** for the judge (r = +0.309, p < 10^-34). All other signals are near zero or slightly negative. This means:

- Semantic captures something about meaning that IS does not fully represent through its weighted combination
- The other 4 content signals are fully absorbed by IS — once you know IS, they add nothing
- NEA F1 is slightly *negatively* correlated after controlling for IS (−0.093), suggesting IS slightly over-weights NEA relative to what the judge cares about

**Controlling for InvWER** (what does each signal add beyond WER?):

| Signal | r_partial(Judge | WER) |
|--------|:-:|
| **Semantic** | **+0.680** |
| Phonetic | +0.561 |
| Length Ratio | +0.482 |
| NEA F1 | +0.427 |
| InvWWER | +0.396 |

All signals add substantial information beyond WER. Semantic adds the most (+0.680), but even Length Ratio adds meaningfully (+0.482) — because extreme LR indicates hallucination/empty output that WER already captures differently.

### 5.3 AUC-ROC (Classification Power)

| Task | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Y vs not-Y** | **0.948** | 0.922 | 0.916 | 0.907 | 0.863 | 0.590 |
| **Y+P vs N** | **0.956** | 0.952 | 0.946 | 0.940 | 0.870 | 0.624 |
| **P vs N** | **0.933** | 0.929 | 0.923 | 0.916 | 0.829 | 0.612 |

Semantic leads at every operating point. The margin is small for Y+P vs N (0.956 vs 0.952 Phonetic) but larger for Y vs not-Y (0.948 vs 0.922 Phonetic, +0.026). NEA F1 consistently underperforms the other content signals at classification.

### 5.4 Distribution Overlap

Percentage of P segments falling within N's IQR (lower = better separation):

| Signal | P ∩ N_IQR | Y ∩ P_IQR |
|--------|:-:|:-:|
| **InvWER** | **5.6%** | 17.1% |
| **InvWWER** | 6.1% | 15.7% |
| **Semantic** | 6.7% | **10.7%** |
| Phonetic | 8.1% | 17.4% |
| NEA F1 | 21.9% | 20.3% |
| Length Ratio | 77.2% | 68.7% |

Semantic has the **least overlap at Y vs P** (10.7%) — the hardest boundary. InvWER has the least overlap at P vs N (5.6%), but this is an artifact of many N segments having WER ≥ 100% (outside any reasonable range).

---

## 6. Semantic × WER Quadrant Analysis

Segments split by median Semantic (0.412) and median InvWER (0.389):

| Quadrant | n | Y% | P% | N% | Y+P% | Mean IS |
|----------|:-:|:-:|:-:|:-:|:-:|:-:|
| **High Sem + Good WER** | 627 | **51.7%** | 47.5% | 0.8% | **99.2%** | 3.837 |
| **High Sem + Bad WER** | 122 | 9.8% | **77.0%** | 13.1% | **86.9%** | 2.411 |
| **Low Sem + Good WER** | 125 | 5.6% | **81.6%** | 12.8% | **87.2%** | 2.702 |
| **Low Sem + Bad WER** | 623 | 0.3% | 21.2% | **78.5%** | 21.5% | 1.180 |

**Key findings:**
- When both agree (good/good or bad/bad), the outcome is clear: 99% Y+P vs 22% Y+P
- When they **disagree**, both "sem carries" and "WER carries" produce ~87% Y+P — they are symmetric in recovery power
- But the judge's Y rate differs: High Sem + Bad WER gets 9.8% Y, Low Sem + Good WER gets only 5.6% Y — **Semantic is slightly more predictive of outright success**
- 122 segments have high semantic despite bad WER — these are the paraphrases and gist-preserved outputs that WER misses

---

## 7. Signal Behavior by Topic

| Topic | n | Semantic | Phonetic | InvWER | NEA F1 | IS Mean |
|-------|:-:|:-:|:-:|:-:|:-:|:-:|
| Business/Finance | 46 | **0.567** | **0.636** | **0.532** | **0.528** | 3.09 |
| Sports/Fitness | 31 | 0.521 | 0.617 | 0.471 | 0.456 | 2.96 |
| Politics/News | 34 | 0.508 | 0.576 | 0.433 | 0.489 | 2.87 |
| Education/Academic | 86 | 0.496 | 0.610 | 0.476 | 0.446 | 2.97 |
| Cooking/Food | 117 | 0.484 | 0.562 | 0.407 | 0.437 | 2.74 |
| Technology | 132 | 0.462 | 0.578 | 0.433 | 0.452 | 2.76 |
| Religion/Spirituality | 17 | 0.454 | 0.556 | 0.313 | 0.353 | 2.47 |
| Medical/Health | 39 | 0.448 | 0.557 | 0.433 | 0.427 | 2.76 |
| Other | 899 | 0.414 | 0.541 | 0.320 | 0.361 | 2.36 |
| Entertainment | 69 | 0.391 | 0.490 | 0.327 | 0.316 | 2.21 |
| **DIY/Home** | 27 | **0.359** | **0.466** | 0.241 | 0.348 | 2.00 |

**Topic explains < 3% of any signal's variance** (η² = 0.013–0.027). Business/Finance performs best across all signals; DIY/Home and Entertainment perform worst. The model struggles most with visually-demonstrative content (DIY) and creative/informal speech (Entertainment).

---

## 8. Signal Behavior by Failure Mode

| Failure Mode | n | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|-------------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Content Word Errors | 96 | **0.463** | **0.559** | 0.396 | 0.389 | 0.372 | 0.899 |
| Accumulated Small | 111 | 0.360 | 0.628 | **0.498** | **0.474** | 0.274 | 0.923 |
| High Error Rate | 109 | 0.404 | 0.439 | 0.186 | 0.214 | **0.338** | 0.937 |
| Entity Destruction | 108 | 0.351 | 0.429 | 0.197 | 0.187 | **0.000** | 0.904 |
| Phonetic Wrong Topic | 141 | 0.116 | **0.456** | 0.215 | 0.226 | 0.185 | 0.949 |
| Total Topic Drift | 143 | 0.081 | 0.187 | 0.054 | −0.013 | 0.041 | 0.720 |
| Hallucination | 111 | 0.160 | 0.299 | **−0.465** | −0.012 | 0.045 | **1.563** |
| Empty Output | 70 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

**Most revealing failure mode contrasts:**
- **Phonetic Wrong Topic**: Phonetic = 0.456 but Semantic = 0.116 — the sounds match but the meaning is completely different. This is the failure mode Phonetic should NOT catch.
- **Entity Destruction**: NEA F1 = 0.000 by definition; Semantic = 0.351 — the surrounding structure preserves some embedding similarity even with all entities destroyed
- **Hallucination**: LR = 1.563 (output much longer than reference); InvWER = −0.465 (WER > 146%) — Length Ratio is the best hallucination signal
- **Accumulated Small Errors**: Highest InvWER among failure modes (0.498) — individual errors are small, adding up gradually

---

## 9. Segment Length Effect

| Length Bin | n | Y% | P% | N% | Semantic | InvWER | LR |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **1-7 words** | 247 | 18.6% | 31.2% | **50.2%** | 0.374 | 0.132 | **1.148** |
| **8-14 words** | 502 | 19.9% | 41.6% | 38.4% | 0.424 | 0.352 | 0.941 |
| **15-24 words** | 415 | **26.3%** | **48.2%** | 25.5% | 0.473 | 0.442 | 0.912 |
| **25-49 words** | 324 | **26.9%** | 42.3% | 30.9% | 0.455 | 0.437 | 0.752 |
| **50+ words** | 9 | 33.3% | 33.3% | 33.3% | 0.533 | 0.414 | 0.661 |

**Short segments (1-7 words) are hardest:** 50% N-rate, mean LR = 1.148 (model over-generates). The model has the least context for short segments, leading to more hallucination and topic drift. Optimal segment length for this model is **15-24 words** (highest Y+P rate at 74.5%).

**Length Ratio pathology:** Short segments have LR > 1 (over-generation), long segments have LR < 1 (truncation). The model targets ~10-15 words regardless of input length.

---

## 10. LRS3 vs YouTube Comparison

### 10.1 Global Means (LRS3 V4: 184 segments, WER 36.0%)

| Signal | LRS3 | YouTube | Delta | Delta / YT_std |
|--------|:-:|:-:|:-:|:-:|
| **Semantic** | 0.729 | 0.437 | **+0.292** | **+0.95σ** |
| Phonetic | 0.747 | 0.552 | +0.195 | +0.71σ |
| InvWER | 0.640 | 0.360 | +0.280 | +0.71σ |
| InvWWER | 0.648 | 0.381 | +0.267 | +0.80σ |
| NEA F1 | 0.639 | 0.389 | +0.249 | +0.68σ |
| Length Ratio | 0.933 | 0.925 | +0.008 | +0.02σ |
| **IS** | **3.66** | **2.52** | **+1.14** | — |
| **WER%** | **36.0** | **64.1** | **−28.1** | — |

LRS3 is better across all signals, but Semantic has the **largest normalized gap** (+0.95σ vs +0.68–0.80σ for others). The domain advantage shows most in meaning preservation.

### 10.2 Standard Deviation Comparison

| Signal | LRS3 Std | YouTube Std | Ratio |
|--------|:-:|:-:|:-:|
| Semantic | 0.282 | 0.308 | 0.91 |
| Phonetic | 0.249 | 0.276 | 0.90 |
| **InvWER** | **0.289** | **0.393** | **0.74** |
| InvWWER | 0.287 | 0.334 | 0.86 |
| NEA F1 | 0.384 | 0.367 | 1.05 |
| **Length Ratio** | **0.222** | **0.348** | **0.64** |

LRS3 has **tighter distributions** for all signals except NEA F1. InvWER and Length Ratio are much tighter (0.74×, 0.64×) — the LRS3 domain produces more predictable WER outcomes and consistent output lengths. NEA F1 is slightly wider on LRS3 (1.05×) — entity accuracy is more variable even on cleaner data.

### 10.3 Tier Distribution

| Tier | LRS3 | YouTube |
|------|:-:|:-:|
| 5 — Excellent | **51.1%** | 18.4% |
| 4 — Good | 21.7% | 21.4% |
| 3 — Fair | 15.8% | 21.7% |
| 2 — Poor | 6.5% | 22.4% |
| 1 — Failed | 4.9% | 16.0% |

LRS3 is **top-heavy** (72.8% in tiers 4-5) while YouTube is **nearly uniform** across tiers. The LRS3 model was trained on similar data, so the distribution reflects in-domain performance.

### 10.4 WER-Matched Comparison (the Semantic Advantage)

When we control for WER by comparing within the same WER bands, the signal gap narrows for all signals **except Semantic**:

| WER Band | n_LRS3 | n_YT | Δ Semantic | Δ Phonetic | Δ InvWER |
|----------|:-:|:-:|:-:|:-:|:-:|
| 0-20% | 59 | 158 | **+0.062** | +0.037 | +0.039 |
| 20-40% | 58 | 290 | **+0.144** | +0.024 | +0.014 |
| 40-60% | 29 | 283 | **+0.101** | −0.032 | −0.007 |
| 60-80% | 18 | 240 | **+0.105** | +0.037 | −0.005 |
| 80%+ | 20 | 520 | +0.046 | −0.043 | +0.085 |

**At the same WER level, LRS3 segments have consistently higher Semantic similarity** (Δ = +0.06 to +0.14). Phonetic and InvWER deltas are near zero when WER is matched. This confirms the domain gap is primarily **semantic** — TED talk errors preserve meaning better than YouTube errors because:

1. TED vocabulary is more formal/structured → substitution errors tend to be semantically closer
2. YouTube has more colloquial speech, accents, code-switching → errors produce more random substitutions
3. The visual encoder was pretrained on LRS3 → better feature extraction for this domain

---

## 11. Transition Zone Analysis

Signal behavior at the critical NIV thresholds (±0.3 IS around boundary):

### NIV Y Boundary (IS = 3.80)

| Signal | Just Above [3.80, 4.10) n=108 | Just Below [3.50, 3.80) n=87 | Gap |
|--------|:-:|:-:|:-:|
| **Semantic** | 0.746 | 0.648 | **+0.098** |
| Phonetic | 0.804 | 0.765 | +0.039 |
| InvWER | 0.696 | 0.636 | +0.060 |
| InvWWER | 0.679 | 0.633 | +0.045 |
| NEA F1 | 0.723 | 0.677 | +0.046 |
| Length Ratio | 0.967 | 0.968 | −0.002 |

**Semantic has the largest gap** at the Y boundary (+0.098, 2.5× the Phonetic gap). This means Semantic is the signal that most strongly "pushes" segments across the Y threshold. It's the sharpest discriminator at the point that matters most.

### NIV Y+P Boundary (IS = 2.00)

| Signal | Just Above [2.00, 2.30) n=93 | Just Below [1.70, 2.00) n=90 | Gap |
|--------|:-:|:-:|:-:|
| Semantic | 0.348 | 0.291 | +0.058 |
| InvWWER | 0.312 | 0.229 | **+0.083** |
| Length Ratio | 0.993 | 0.916 | **+0.077** |
| **Phonetic** | 0.515 | 0.445 | **+0.070** |
| InvWER | 0.270 | 0.223 | +0.047 |
| NEA F1 | 0.216 | 0.178 | +0.038 |

At the Y+P boundary, **InvWWER and Length Ratio** dominate — this boundary separates "some useful output" from "garbage," where output length and weighted word accuracy matter more than semantic nuance. Semantic is less important here because even partial meaning preservation (P) is enough.

---

## 12. Signal Correlation Matrix

|  | Semantic | Phonetic | InvWER | InvWWER | NEA F1 | LR |
|--|:-:|:-:|:-:|:-:|:-:|:-:|
| **Semantic** | 1.000 | 0.822 | 0.726 | 0.760 | 0.753 | 0.189 |
| **Phonetic** | 0.822 | 1.000 | 0.793 | 0.845 | 0.751 | 0.360 |
| **InvWER** | 0.726 | 0.793 | 1.000 | 0.809 | 0.691 | −0.220 |
| **InvWWER** | 0.760 | 0.845 | 0.809 | 1.000 | 0.754 | 0.097 |
| **NEA F1** | 0.753 | 0.751 | 0.691 | 0.754 | 1.000 | 0.130 |
| **LR** | 0.189 | 0.360 | −0.220 | 0.097 | 0.130 | 1.000 |

**Semantic's correlation pattern is distinctive:**
- Lowest correlation with InvWER (0.726) — confirms Semantic captures different information than word error counting
- Lowest correlation with LR (0.189) — Semantic is nearly independent of output length
- InvWER is **negatively** correlated with LR (−0.220) — hallucinations have high LR but terrible WER

---

## 13. Summary: Signal Predictive Power for Judge

| Signal | r(Judge) | AUC(Y) | AUC(Y+P) | d(Y vs N) | η²(Judge) | r_partial(Judge\|IS) |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Semantic** | **0.846** | **0.948** | **0.956** | **4.91** | **0.716** | **+0.309** |
| Phonetic | 0.806 | 0.922 | 0.952 | 3.71 | 0.668 | +0.029 |
| InvWWER | 0.741 | 0.907 | 0.940 | 3.05 | 0.556 | −0.030 |
| InvWER | 0.714 | 0.916 | 0.946 | 2.63 | 0.519 | −0.026 |
| NEA F1 | 0.710 | 0.863 | 0.870 | 3.19 | 0.504 | −0.093 |
| LengthRatio | 0.172 | 0.590 | 0.624 | 0.37 | 0.035 | −0.039 |

### Semantic Advantage Over Other Content Signals

| Metric | Semantic | Mean of 4 Others | Advantage |
|--------|:-:|:-:|:-:|
| r(Judge) | 0.846 | 0.743 | **1.14×** |
| AUC(Y) | 0.948 | 0.902 | 1.05× |
| d(Y vs N) | 4.91 | 3.15 | **1.56×** |
| η²(Judge) | 0.716 | 0.562 | **1.27×** |
| r_partial(Judge\|IS) | +0.309 | −0.030 | **∞** (only significant one) |

---

## 14. Conclusions

### 14.1 Semantic Is the Best Single Predictor of Judge Agreement

Across every metric — correlation, AUC, Cohen's d, eta-squared, partial correlation — Semantic similarity leads or ties for first place when predicting the Opus judge. The advantage ranges from modest (5% better AUC) to dramatic (only signal with significant partial correlation after controlling for IS).

### 14.2 But PCA Says Semantic Is Not Independent

This creates an apparent paradox: PCA shows all 5 content signals load equally on PC1 (0.43–0.47), yet Semantic uniquely predicts the judge. The resolution is that **PCA measures variance structure, not predictive relevance**. The 5 signals share 87% of their variance (one dimension), but Semantic's remaining 13% unique variance is disproportionately aligned with what the judge cares about — pragmatic meaning equivalence.

### 14.3 The LRS3 Domain Gap Is Primarily Semantic

At matched WER levels, LRS3 segments show +0.06 to +0.14 higher Semantic similarity than YouTube segments, while Phonetic and InvWER deltas are near zero. The visual encoder's domain familiarity with TED talks manifests as better **meaning preservation**, not better phonetic or word accuracy.

### 14.4 Implications for IS Formula

The current IS formula weights Semantic at 25% (highest single weight), which is justified by these findings. However, the partial correlation analysis (Section 5.2) shows Semantic carries information **beyond** what the IS formula captures — the weighted sum compresses some of Semantic's unique discriminative power. This is consistent with the reweighting analysis finding: you can't fix this with weights alone; you need a richer signal (entailment, BERTScore) to capture pragmatic equivalence.

### 14.5 Length Ratio Is a Safety Net, Not a Quality Signal

LR's η² is 0.035 for judge, 0.064 for IS tier. Its AUC is 0.59–0.62 (barely above chance). Its one job: catching hallucination (LR = 1.56 mean for hallucination failure mode) and empty output (LR = 0). The 15% weight is appropriate for this safety-net role.

---

## 15. Presentation Slide

The key finding from Section 10 (LRS3 vs YouTube) is captured in presentation slide **"Same WER, Different Meaning"** (`slide_semantic_domain_gap` in `slides_research.py`, remark #244). The slide shows:

- WER-matched delta table (20-40% band): Semantic +0.143 vs Phonetic +0.024
- Semantic/Phonetic ratio: LRS3 = 1.01, YouTube = 0.87
- Two real examples (LRS3: numbers wrong meaning intact; YouTube: same sounds different topic)
- Three root causes: visual encoder familiarity, vocabulary density, LLM prior anchoring

---

## 16. Data Availability

- **YouTube IS scores:** [intelligibility_scores.csv](intelligibility/intelligibility_scores.csv)
- **Judge results:** [llm_judge_results.csv](llm_judge/llm_judge_results.csv)
- **LRS3 IS scores (V4):** `/tmp/lrs3_decode/is_v4/intelligibility_scores.csv`
- **LRS3 experiment notes:** [lrs3_decode_experiment.md](lrs3_decode_experiment.md)
- **Reweighting analysis:** [is_reweighting_analysis.md](is_reweighting_analysis.md)
- **PCA analysis:** [is_pca_analysis.md](is_pca_analysis.md)
- **Threshold calibration:** [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md)