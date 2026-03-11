# Intelligibility Comparison: Baseline vs Config J vs Config C

> **Note (March 2026):** This document uses the legacy IS ≥ 3.0 threshold (40.1% captured). Current NIV thresholds supersede this: IS ≥ 2.00 = 61.6% useful (κ=0.818), IS ≥ 3.80 = 23.1% clearly conveyed (κ=0.690). See [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md).

**Argos -- The Orchard**
**Date:** 2026-02-25
**Dataset:** 1,497 segments from 1,396 AVSpeech videos

---

## Configuration Summary

| Parameter | Baseline (A) | Config J | Config C |
|-----------|-------------|----------|----------|
| beam | 20 | 20 | 20 |
| lenpen | 0 | 1.0 | 1.0 |
| do_sample | false | true | false |
| temperature | 1.0 | 0.5 | 1.0 |
| top_p | 0.9 | 0.9 | 0.9 |
| rep_penalty | 1.2 | 1.2 | 1.2 |
| no_repeat_ngram | 3 | 3 | 3 |

Config J = stochastic decode with length penalty. Config C = deterministic version of J (isolates effect of lenpen without sampling noise).

*See also: [IS Component Correlation Analysis](is_correlation_analysis.md) for inter-signal redundancy and variance decomposition across the baseline dataset.*

---

## 1. Headline Metrics

| Metric | Baseline | Config J | Config C | J vs Base | C vs Base |
|--------|----------|----------|----------|-----------|-----------|
| **Mean IS** | 2.53 | **2.60** | 2.57 | +0.07 | +0.04 |
| **Median IS** | 2.54 | **2.63** | 2.59 | +0.09 | +0.05 |
| **Properly Captured (IS >= 3)** | 601 (40.1%) | **622 (41.5%)** | 594 (39.7%) | +21 (+1.4pp) | -7 (-0.4pp) |
| **Empty Predictions** | 70 (4.7%) | **0 (0.0%)** | **0 (0.0%)** | -70 | -70 |
| **Mean WER** | **64.1%** | 78.9% | 79.3% | +14.8pp | +15.2pp |
| **Mean WWER** | **60.5%** | 62.8% | 63.8% | +2.3pp | +3.3pp |
| **Mean NEA F1** | 38.9% | **43.4%** | 39.7% | +4.5pp | +0.8pp |
| **Hallucinations (WER >= 100%)** | 307 (20.5%) | 348 (23.2%) | 360 (24.0%) | +41 | +53 |
| **Context Recoverable (Rule)** | 652 (43.6%) | **666 (44.5%)** | 659 (44.0%) | +14 | +7 |
| **Context Recoverable (LLM)** | 757 (50.6%) | 772 (51.6%) | **779 (52.0%)** | +15 | +22 |

### Key Takeaway

Both J and C **eliminate empty predictions** (the baseline's 70 empties become actual output) and **slightly improve the intelligibility score**. However, this comes at a cost: WER rises ~15pp because the formerly-empty segments now produce output that is often hallucinated. The WWER increase is much smaller (~1-2pp), meaning the new errors are mainly on function words rather than content words.

---

## 2. Tier Distribution

| Tier | Baseline | Config J | Config C |
|------|----------|----------|----------|
| 5 -- Excellent (4.0-5.0) | 276 (18.4%) | **291 (19.4%)** | 274 (18.3%) |
| 4 -- Good (3.0-3.99) | **321 (21.4%)** | **331 (22.1%)** | 320 (21.4%) |
| 3 -- Fair (2.0-2.99) | 325 (21.7%) | 319 (21.3%) | **335 (22.4%)** |
| 2 -- Poor (1.0-1.99) | 336 (22.4%) | 345 (23.0%) | **354 (23.6%)** |
| 1 -- Failed (0.0-0.99) | 239 (16.0%) | **211 (14.1%)** | 214 (14.3%) |

Config J pushes more segments into the top tiers (Excellent/Good) while reducing failures. Config C shows a more mixed redistribution -- fewer outright failures, but more segments stuck in Poor quality.

---

## 3. Signal Comparison

### Overall Means

| Signal | Baseline | Config J | Config C |
|--------|----------|----------|----------|
| Semantic Similarity | 0.437 | **0.443** | **0.444** |
| Phonetic Similarity | 0.552 | **0.586** | **0.587** |
| Inverse WER | **0.394** | 0.384 | 0.384 |
| Inverse WWER | **0.397** | 0.421 | 0.407 |
| NEA F1 | 38.9% | **43.4%** | 39.7% |
| Length Ratio | **0.925** | 1.181 | 1.187 |

### Success Group (IS >= 3.0)

| Signal | Baseline | Config J | Config C |
|--------|----------|----------|----------|
| Semantic Similarity | **0.736** | 0.723 | 0.737 |
| Phonetic Similarity | 0.809 | 0.809 | **0.816** |
| WER | **30.2%** | 31.4% | 30.6% |
| WWER | 31.1% | **29.6%** | 31.1% |
| NEA F1 | 74.0% | **76.5%** | 74.1% |
| Length Ratio | **0.974** | 0.990 | 0.991 |

### Failure Group (IS < 3.0)

| Signal | Baseline | Config J | Config C |
|--------|----------|----------|----------|
| Semantic Similarity | **0.238** | 0.243 | 0.252 |
| Phonetic Similarity | **0.382** | 0.427 | 0.436 |
| WER | **86.5%** | 112.8% | 111.4% |
| WWER | **82.3%** | 86.5% | 85.3% |
| NEA F1 | **15.7%** | 19.9% | 17.0% |
| Length Ratio | **0.892** | 1.318 | 1.316 |

The failure group tells the story: J and C have much worse WER in failures (112-111% vs 86.5%) and much higher length ratios (1.32 vs 0.89). The baseline's failures were often **too short** (truncated/empty); J and C's failures are often **too long** (hallucinated). The failures shifted from silence to hallucination.

---

## 4. Failure Mode Distribution

| Failure Mode | Baseline (900) | Config J (875) | Config C (903) |
|-------------|----------------|----------------|----------------|
| **Hallucination** | 111 (12.3%) | **262 (29.9%)** | **270 (29.9%)** |
| Phonetically Similar Wrong Topic | 141 (15.7%) | 138 (15.8%) | 135 (15.0%) |
| High Error Rate | 109 (12.1%) | 144 (16.5%) | 110 (12.2%) |
| Content Word Errors | 96 (10.7%) | 95 (10.9%) | 110 (12.2%) |
| Total Topic Drift | **143 (15.9%)** | 88 (10.1%) | 83 (9.2%) |
| Accumulated Small Errors | 111 (12.3%) | 75 (8.6%) | 95 (10.5%) |
| Entity Destruction | 108 (12.0%) | 71 (8.1%) | 98 (10.9%) |
| Empty Output | **70 (7.8%)** | **0 (0.0%)** | **0 (0.0%)** |
| Truncation | 10 (1.1%) | 0 (0.0%) | 0 (0.0%) |
| Over-generation | 1 (0.1%) | 2 (0.2%) | 2 (0.2%) |

The dominant shift: **hallucinations more than double** in both J and C (from 12.3% to 29.9%). The 70 empty outputs and 10 truncations are eliminated, but replaced by hallucinated content. Total Topic Drift drops significantly (~-6pp), suggesting lenpen helps the model stay on topic longer, even if it eventually hallucinates.

---

## 5. Success Pattern Distribution

| Success Pattern | Baseline (597) | Config J (622) | Config C (594) |
|----------------|----------------|----------------|----------------|
| Phonetically Preserved | 248 (41.5%) | **275 (44.2%)** | 256 (43.1%) |
| Minor Errors, High Semantic | 146 (24.5%) | 144 (23.2%) | **149 (25.1%)** |
| Near-Perfect Output | 69 (11.6%) | 66 (10.6%) | **67 (11.3%)** |
| Entities Preserved | 74 (12.4%) | 62 (10.0%) | 63 (10.6%) |
| Good Semantic + Correct Length | 45 (7.5%) | **59 (9.5%)** | 48 (8.1%) |
| Low-Moderate WER | 13 (2.2%) | 10 (1.6%) | 9 (1.5%) |
| Semantic + Phonetic Bridge | 2 (0.3%) | **5 (0.8%)** | 2 (0.3%) |

Config J's extra successes (+25 over baseline) come primarily from **phonetically preserved** segments -- the sampling mechanism occasionally finds phonetically plausible alternatives that the deterministic baseline missed.

---

## 6. Topic Analysis

| Topic | N | Base IS | J IS | C IS | J vs Base |
|-------|---|---------|------|------|-----------|
| Business/Finance | 46 | 3.08 | **3.21** | 3.18 | +0.13 |
| Sports/Fitness | 31 | 2.90 | **2.91** | 2.90 | +0.01 |
| Education/Academic | 86 | 2.83 | **2.90** | 2.89 | +0.07 |
| Politics/News | 34 | 2.81 | **2.92** | 2.86 | +0.11 |
| Technology | 132 | 2.70 | **2.83** | 2.82 | +0.13 |
| Cooking/Food | 117 | 2.66 | **2.77** | 2.70 | +0.11 |
| Medical/Health | 39 | 2.64 | **2.78** | 2.66 | +0.14 |
| Religion/Spirituality | 17 | 2.55 | 2.51 | 2.42 | -0.04 |
| Other | 899 | 2.42 | **2.47** | 2.44 | +0.05 |
| Entertainment | 69 | 2.23 | **2.47** | 2.41 | +0.24 |
| DIY/Home | 27 | 2.13 | **2.53** | 2.50 | +0.40 |

Config J improves most topics. The largest gains are in **DIY/Home** (+0.40) and **Entertainment** (+0.24) -- the two weakest categories in the baseline. These likely had the most empties and truncations that sampling filled in.

---

## 7. Length Band Analysis

| Length Band | N | Base IS | J IS | C IS | Base Cap% | J Cap% | C Cap% |
|------------|---|---------|------|------|-----------|--------|--------|
| 5-10 words | 290 | 2.31 | 2.23 | 2.21 | 31.7% | 32.4% | 30.3% |
| 10-15 words | 368 | 2.51 | 2.51 | 2.49 | 34.8% | 36.7% | 34.2% |
| 15-20 words | 270 | 2.60 | 2.66 | 2.61 | 41.9% | 41.5% | 41.1% |
| 20+ words | 535 | 2.68 | **2.93** | 2.87 | 48.6% | **52.0%** | 49.7% |

The benefit of J and C concentrates on **long segments (20+ words)**: +0.25 IS, +3.4pp capture rate. For short segments (5-10 words), J and C are actually slightly worse -- their tendency to over-generate hurts most when the reference is short.

---

## 8. The Empty-to-Hallucination Tradeoff

This is the central story of J and C vs the baseline:

| What happened to baseline's 70 empties? | Count |
|----------------------------------------|-------|
| Became hallucinated (WER >= 100%) | ~41 |
| Became poor quality (IS < 2.0) | ~18 |
| Became fair/good quality (IS >= 2.0) | ~11 |

The lenpen=1.0 parameter **forces the model to produce output** even when it has low visual confidence. In ~60% of cases, this output is hallucinated. In ~15% of cases, it produces something partially useful. The net effect on IS is slightly positive because:

1. An empty prediction scores IS = 0.0 (worst possible)
2. Even a hallucinated prediction scores IS ~0.5-1.0 (some phonetic/length overlap by chance)
3. The ~11 cases where it actually helps contribute IS 2.0-4.0

---

## 9. J vs C: Effect of Sampling

Comparing J (stochastic) to C (deterministic) isolates the effect of sampling:

| Metric | Config J | Config C | J wins? |
|--------|----------|----------|---------|
| Mean IS | **2.60** | 2.57 | Yes (+0.03) |
| Properly Captured | **622** | 594 | Yes (+28) |
| Hallucinations | **348** | 360 | Yes (fewer) |
| NEA F1 | **43.4%** | 39.7% | Yes (+3.7pp) |
| WWER | **62.8%** | 63.8% | Yes (-1.0pp) |
| Mean WER | **78.9%** | 79.3% | Marginal |

Sampling (temperature=0.5, top_p=0.9) provides a modest but consistent edge across all metrics. The biggest win is in **named entity recovery** (+3.7pp NEA F1): the stochastic exploration sometimes lands on the correct entity that greedy search misses. Sampling also produces slightly fewer hallucinations (348 vs 360), possibly because the diverse hypotheses help avoid degenerate repetitive outputs.

---

## 10. Summary of What Changed

### Improved
- Zero empty predictions (vs 70 in baseline)
- +25 more segments properly captured (J) with IS >= 3.0
- Better named entity accuracy (+4.5pp NEA F1 for J)
- Modest IS improvement across most topics and long segments
- Fewer total topic drift failures and fewer entity destruction failures

### Worsened
- Hallucinations more than doubled (111 -> 262/270)
- Mean WER increased ~15pp (inflated by hallucinated fill-ins)
- Length ratio shifted from slightly short (0.92) to slightly long (1.18)
- Short segments (5-10 words) marginally worse

### Unchanged
- WWER essentially flat (~1-2pp difference)
- Success patterns remain similar -- phonetic preservation still dominates
- Top phonetic confusions are nearly identical across all three configs
- The same topics rank best (Business) and worst (DIY, Entertainment)

### Bottom Line

Config J is the best of the three by a narrow margin. It trades the baseline's "silent failures" (empty outputs) for "noisy failures" (hallucinations). For a production system, the choice depends on the use case:
- **If empty outputs are acceptable**: the baseline is safer (fewer hallucinations)
- **If every segment must produce something**: Config J is preferred (fills empties, best IS)
- **If you want deterministic reproducibility**: Config C is a reasonable middle ground

None of the three configurations changes the fundamental conclusion: **domain adaptation via fine-tuning is the only path to production-grade accuracy**. Decode parameter tuning has reached diminishing returns.

---

## 11. LLM-as-a-Judge Cross-Validation Across Configs

An independent LLM-as-a-Judge evaluation (Claude Opus 4.6, 3-level Y/P/N, blind to metrics) validates IS stability across decode configurations. The LLM judge correlates with IS at r = 0.850 on the full 1,497-segment baseline, and the `llm_context_prob` heuristic maintains this agreement across all 16 tested configurations.

### Correlation Stability (llm_context_prob vs IS)

| Config | N | r vs IS | Cohen's κ | Agreement |
|--------|---|---------|-----------|-----------|
| baseline_full | 1,497 | 0.937 | 0.765 | 88.3% |
| full_decode_C (lenpen=1) | 1,497 | 0.933 | 0.752 | 87.6% |
| full_decode_J (lenpen=1+sampling) | 1,497 | 0.934 | **0.791** | **89.6%** |
| **Mean (all 16 configs)** | — | **0.925** | **~0.72** | — |
| **Std** | — | **0.015** | — | — |

Config J achieves the best agreement with IS (κ = 0.791), consistent with its best capture rate (41.5%). The correlation is rock-solid across all parameter variations — std = 0.015.

### Signal-Level Stability

| Signal | Mean r | Std | Stable? |
|--------|--------|-----|---------|
| IS Score | 0.925 | 0.015 | Yes |
| Semantic Sim | 0.891 | 0.020 | Yes |
| WER | -0.706 | 0.156 | No — disrupted by lenpen configs |
| Length Ratio | -0.023 | 0.333 | No — sign flips |

Semantic Sim and IS are stable across all configs, while WER and Length Ratio are volatile. This further confirms that IS (which combines multiple signals) is a more reliable quality metric than WER alone, especially when comparing across decode configurations.

### Implication

The fact that IS and the LLM judge agree at r > 0.93 on all three full-decode configs means the modest IS differences between Baseline (2.52), Config C (2.57), and Config J (2.60) represent real quality differences — not measurement noise.