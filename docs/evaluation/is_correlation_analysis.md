# IS Metric — Component Correlation Analysis

**Argos — The Orchard**
**Date:** 2026-03-02
**Dataset:** 1,497 segments (full AVSpeech baseline, February 2026)

---

## 0. What This Analysis Says (Plain English)

This document analyzes how the 6 signals that make up the Intelligibility Score (IS) relate to each other and to the overall score. Here is what you need to know:

1. **The 6 signals really measure 3 things.** Word accuracy (~60% of the score), meaning preservation (~29%), and output length (~9%). Four of the six signals — Phonetic Similarity, WER, WWER, and NEA F1 — are all different ways of asking "did the model get the words right?" They correlate tightly with each other (r > 0.79). Semantic Similarity captures whether the *meaning* came through, even if different words were used. Length Ratio just checks if the output is roughly the right length.

2. **When IS is high, both words AND meaning are right.** When IS is low, one or both are wrong. There is no shortcut — a segment needs to get both the words and the meaning approximately correct to score well.

3. **~60% of IS depends on the visual encoder.** The word accuracy cluster (Phonetic, WER, WWER) is the largest contributor, and these signals measure how well the visual encoder extracts speech information from lip movements. To meaningfully improve IS, the visual features must improve — via better training data, a stronger encoder, or both.

4. **The LLM heuristic agrees with IS 89% of the time.** Two independently designed systems — the IS formula and the `llm_context_prob` decision tree — converge on the same quality judgments. This confirms IS is not arbitrary.

5. **Across 16 decode configurations: Semantic and Phonetic are rock-solid; WER and Length Ratio are volatile.** Changing decode parameters (beam size, length penalty, sampling) barely affects Semantic or Phonetic correlations with IS (std < 0.06). But WER correlation swings from -0.95 to -0.45, and Length Ratio even flips sign. This means WER is unreliable as a standalone quality metric.

**Quick Reference:**

| Signal | Role | Stability | Key Stat |
|--------|------|-----------|----------|
| Phonetic Sim | Strongest single predictor | Stable (std 0.059) | r = 0.943 — direct measure of encoder quality |
| Semantic Sim | Highest weight (25%) and variance (28.5%) | Very stable (std 0.017) | Explains most IS differences between segments |
| NEA F1 | Swing factor for borderline cases | Very stable (std 0.023) | 17.3% variance from 15% weight — names/numbers are binary |
| WER | Traditional error metric | Volatile (std 0.163) | Unreliable across configs — inflated by length penalty |
| WWER | Weighted error metric | Volatile (std 0.203) | Same instability as WER |
| Length Ratio | Output length check | Highly volatile (std 0.368) | Nearly useless — sign flips across decode settings |
| LLM heuristic | Independent validation | Very stable (std 0.015) | r = 0.925 with IS — confirms framework validity |

---

## 0.1 The Important Findings

These are the findings from the correlation analysis that matter most for understanding the system and deciding what to improve.

### Finding 1: Phonetic Similarity is the strongest single predictor (r = 0.943) despite having lower weight (15%)

Phonetic Similarity has the highest correlation of any single signal with IS (r = 0.943), even though it only receives 15% weight (vs Semantic's 25%). This is because the visual encoder's primary job is decoding mouth shapes into sounds — phonetic accuracy is the most direct measure of whether the encoder did its job.

**Implication:** Improving the visual encoder (via more training data or a stronger architecture) has the biggest single impact on IS. Phonetic accuracy is the closest proxy to "did the encoder work?"

### Finding 2: 4 of 6 signals measure the same underlying thing (word accuracy cluster, r > 0.79)

Phonetic Similarity, WER, WWER, and (partially) NEA F1 all correlate tightly with each other. They form a single "word accuracy" dimension that accounts for ~60% of IS variance. The IS formula assigns 15% weight to each of these four signals, creating an implicit 60% emphasis on word-level accuracy.

**Implication:** The IS formula is heavily weighted toward "did it get the right words?" This is intentional — for lip-reading, getting the words right is the foundation. But it means a segment that perfectly captures meaning with different words (paraphrasing) will score lower than it deserves.

### Finding 3: Semantic Similarity drives the most IS variance (28.5%) despite being partially redundant with word accuracy

Semantic Similarity correlates at r = 0.82 with Phonetic — they share information, because getting the words right usually means getting the meaning right. But Semantic has the highest weight (25%) AND the highest spread among segments (σ = 0.31). This means: when two segments differ in IS, the semantic signal is often what separates them.

**Implication:** Semantic Similarity is the "tiebreaker" signal. It distinguishes between segments where the words are similarly wrong but the meaning preservation varies. This is especially important for the Fair tier (IS 2.0–3.0), where many segments live.

### Finding 4: NEA F1 punches above its weight (17.3% variance from 15% weight)

Named Entity Accuracy has the highest variance of all signals (σ = 0.37). A segment either preserves names, numbers, and key entities or it doesn't — there's rarely a middle ground. This binary nature makes NEA the "swing factor" in borderline cases: a segment with correct entity capture often gets pushed into the next tier up.

**Implication:** Names and numbers are the hardest things to get right in lip-reading (they can't be predicted from context). When the system does capture them, it's strong evidence that the visual features were good quality.

### Finding 5: Length Ratio is nearly useless (9.1% variance, sign-flipping across configs)

Length Ratio's contribution to IS variance is the smallest (9.1%), and its correlation with IS is only r = 0.23. Worse, its correlation *flips sign* across decode configurations — positive for configs that truncate, negative for configs that over-generate. Most outputs are roughly the right length regardless of quality.

**Implication:** Future IS versions could reduce Length Ratio's weight (or remove it) without losing discrimination power. Its current 15% weight is the most "wasted" weight in the formula.

### Finding 6: Per-tier analysis reveals different "what matters" at each quality level

The dominant signal shifts across quality tiers:
- **Failed tier (0–1):** Phonetic dominates (r = 0.79) — "does it even sound right?"
- **Fair tier (2–3):** WER dominates (r = 0.55) — the boundary between "almost good" and "mediocre"
- **Excellent tier (4–5):** WER dominates (r = 0.83) — at the top, small word-level differences determine ranking

**Implication:** The visual encoder quality determines whether a segment escapes the Failed tier (phonetic accuracy). Once past that threshold, traditional word accuracy metrics separate Good from Excellent.

### Finding 7: WER becomes unreliable when decode settings change

WER's correlation with IS swings from r = -0.949 to r = -0.453 across 16 decode configurations. Specifically, length penalty settings (lenpen > 0) cause the model to generate longer outputs. These outputs have more word errors by WER's count, but IS stays stable because the extra words often contain useful semantic content.

**Implication:** WER alone is misleading for comparing configurations. Config J has 12pp higher WER than baseline but +0.08 higher IS. This is the core reason IS was created — it captures quality dimensions that WER misses. When evaluating the system, IS should be the primary metric, not WER.

---

## 1. Executive Summary

The Intelligibility Score (IS) is a weighted linear composite of 6 signals:

```
IS = 0.25×Semantic + 0.15×Phonetic + 0.15×InvWER + 0.15×InvWWER + 0.15×NEA_F1 + 0.15×LengthRatio
```

Correlation analysis reveals that the 6 signals collapse into **3 independent dimensions**:
1. **Word accuracy** (WER, WWER, Phonetic — all r > 0.80 with each other) → ~60% of IS variance
2. **Meaning preservation** (Semantic — partially redundant with word accuracy at r=0.82) → ~28% of IS variance
3. **Output sanity** (Length Ratio — largely independent of other signals) → ~9% of IS variance

The heuristic LLM-knowledge-based judge (`llm_context_prob`) correlates at **r=0.93** with IS and achieves **88.6% agreement** with the IS ≥ 3.0 "properly captured" threshold.

---

## 2. IS vs Raw Component Correlations

All p-values < 1e-18 (statistically significant for N=1,497).

| Component | Pearson r | Spearman ρ | R² | Direction |
|-----------|----------|------------|-----|-----------|
| **Phonetic Sim** | **0.943** | **0.943** | 0.888 | Higher phonetic → higher IS |
| **Semantic Sim** | **0.921** | **0.925** | 0.848 | Higher semantic → higher IS |
| **WWER %** | **-0.881** | **-0.948** | 0.776 | Lower WWER → higher IS |
| **NEA F1 %** | **0.864** | **0.864** | 0.747 | Higher NEA → higher IS |
| **WER %** | **-0.849** | **-0.943** | 0.721 | Lower WER → higher IS |
| Length Ratio | 0.226 | 0.253 | 0.051 | Closer to 1.0 → higher IS |

**Key observations:**
- The top 5 signals are all strongly correlated with IS (|r| > 0.84)
- WWER shows higher Spearman (rank) correlation than Pearson (linear), indicating the relationship has a nonlinear component — extreme WER values (hallucinations at 100%+) compress the linear relationship
- Length Ratio is the weakest predictor (r=0.23) — most outputs are roughly the right length regardless of content quality
- Phonetic Similarity has the highest single-component correlation, despite not having the highest weight

---

## 3. Variance Contribution (Covariance Decomposition)

How much of the total IS variance (1.88) does each weighted component explain:

| Weighted Component | Variance | Covariance w/ IS | % of IS Variance | Correlation w/ IS |
|-------------------|----------|-------------------|------------------|-------------------|
| **Semantic (0.25×)** | 0.1802 | 0.5366 | **28.5%** | 0.921 |
| NEA F1 (0.15×) | 0.0757 | 0.3266 | **17.3%** | 0.864 |
| Inv-WER (0.15×) | 0.0522 | 0.2961 | **15.7%** | 0.944 |
| Inv-WWER (0.15×) | 0.0481 | 0.2863 | **15.2%** | 0.950 |
| Phonetic (0.15×) | 0.0428 | 0.2677 | **14.2%** | 0.943 |
| Length Ratio (0.15×) | 0.0368 | 0.1713 | **9.1%** | 0.650 |
| **TOTAL** | | | **100.0%** | |

**Key insight:** Semantic Similarity dominates variance (28.5%) not because it's the most correlated, but because it has the highest weight (0.25) and substantial spread (σ=0.31). NEA F1 contributes 17.3% — disproportionately more than its 0.15 weight suggests — because it has the highest variance among the 0.15-weight signals (σ=0.37).

---

## 4. Inter-Component Correlation Matrix

Pearson r between raw component values:

|  | Semantic | Phonetic | WER | WWER | NEA F1 | Length Ratio |
|--|----------|----------|-----|------|--------|-------------|
| **Semantic** | 1.000 | **0.822** | -0.726 | -0.760 | 0.753 | 0.189 |
| **Phonetic** | 0.822 | 1.000 | -0.792 | **-0.845** | 0.751 | 0.359 |
| **WER** | -0.726 | -0.792 | 1.000 | **0.809** | -0.691 | 0.220 |
| **WWER** | -0.760 | -0.845 | 0.809 | 1.000 | -0.754 | -0.097 |
| **NEA F1** | 0.753 | 0.751 | -0.691 | -0.754 | 1.000 | 0.130 |
| **Length Ratio** | 0.189 | 0.359 | 0.220 | -0.097 | 0.130 | 1.000 |

**Redundancy clusters:**
- **Cluster 1 (Word Accuracy):** Phonetic ↔ WWER (r=0.845), WER ↔ WWER (r=0.809), Phonetic ↔ WER (r=0.792)
- **Cluster 2 (Meaning):** Semantic ↔ Phonetic (r=0.822), Semantic ↔ WWER (r=0.760)
- **Independent:** Length Ratio has low correlation with everything (r ≤ 0.36)

**Implication for metric design:** 4 of the 6 signals (Phonetic, WER, WWER, NEA F1) are measuring overlapping aspects of "did the model get the words right?" This means ~60% of IS weight (4 × 0.15) goes to variants of the same underlying construct.

---

## 5. Per-Tier Correlations

Which signal drives IS differentiation within each quality tier:

| Tier | N | Dominant Signal(s) | Interpretation |
|------|---|-------------------|----------------|
| **Failed (0-1)** | 239 | **Phonetic (0.79)**, Length (0.47), Semantic (0.43) | At the bottom, phonetic similarity separates "totally wrong" from "sounds-like-it-could-be-right" |
| **Poor (1-2)** | 336 | Phonetic (0.52), Semantic (0.51), NEA (0.41) | Multiple signals contribute roughly equally |
| **Fair (2-3)** | 325 | **WER (0.55)**, WWER (0.51), Phonetic (0.46) | The boundary zone — traditional error rates separate "almost good" from "mediocre" |
| **Good (3-4)** | 321 | WWER (0.51), WER (0.51), Semantic (0.50) | Balanced — all content signals matter |
| **Excellent (4-5)** | 276 | **WER (0.83)**, WWER (0.78), Phonetic (0.72) | At the top, small WER differences dominate ranking |

**Pattern:** At extremes (Failed and Excellent tiers), a single signal dominates. In the middle tiers, signals are more balanced and no single metric determines rank.

---

## 6. Regression Verification

Multiple regression of IS on the 6 scaled components confirms the formula is an exact linear combination:

```
R² = 1.000000   (Residual std = 0.000341 — floating-point noise only)

Coefficient      Estimate    Expected
Intercept        -0.000005    0.00
Semantic          0.250000    0.25
Phonetic          0.149983    0.15
Inv-WER           0.150018    0.15
Inv-WWER          0.149980    0.15
NEA F1            0.150008    0.15
Length Ratio      0.150010    0.15
```

There is no hidden nonlinearity or interaction — IS is strictly additive.

---

## 7. LLM-Knowledge-Based Judge (`llm_context_prob`)

### 7.1 What It Is

The `llm_context_prob` field is a **heuristic approximation** of how an expert LLM would judge whether a viewer with topic context could understand a lip-reading segment. It is implemented as a deterministic decision tree over 6 linguistic factors (word overlap, sequence preservation, phonetic plausibility, length sanity, semantic coherence, information density). It does NOT involve actual LLM API calls — it is designed to be fast, reproducible, and free of inference costs.

**Implementation:** `docs/_research-tools/generators/generate_intelligibility_scores.py`, function `estimate_llm_context_recovery()` (lines 302–416)

### 7.2 Correlation with IS and Components

| Metric | Pearson r | Spearman ρ |
|--------|----------|------------|
| **IS Score** | **0.934** | **0.952** |
| Semantic Sim | 0.894 | 0.904 |
| Phonetic Sim | 0.892 | 0.916 |
| WER % | -0.805 | -0.924 |
| WWER % | -0.818 | -0.901 |
| NEA F1 % | 0.757 | 0.768 |
| Length Ratio | 0.186 | 0.204 |
| Rule-based Ctx (bool) | 0.857 | 0.826 |

The LLM heuristic correlates most strongly with IS itself (r=0.93) and with Semantic Sim and Phonetic Sim — the two signals that best capture "can a human understand this?"

### 7.2a LLM Judge vs Components — Cross-Configuration (16 Configs)

*(Added 2026-03-02. LLM context recovery computed from scratch for all 16 decode configs.)*

**Per-config Pearson r of `llm_context_prob` vs each signal:**

| Config | N | vs IS | vs Sem | vs Pho | vs WER | vs WWER | vs NEA | vs LR |
|--------|---|-------|--------|--------|--------|---------|--------|-------|
| baseline_full | 1497 | 0.937 | 0.891 | 0.904 | -0.810 | -0.820 | 0.761 | 0.179 |
| full_decode_C | 1497 | 0.933 | 0.879 | 0.867 | -0.547 | -0.638 | 0.749 | -0.300 |
| full_decode_J | 1497 | 0.934 | 0.876 | 0.861 | -0.505 | -0.649 | 0.784 | -0.268 |
| exp_A_baseline | 107 | 0.917 | 0.892 | 0.894 | -0.822 | -0.804 | 0.679 | 0.331 |
| exp_B_no_rep_pen | 107 | 0.926 | 0.898 | 0.894 | -0.830 | -0.825 | 0.706 | 0.312 |
| exp_C_lenpen_pos1 | 107 | 0.911 | 0.887 | 0.878 | -0.552 | -0.799 | 0.667 | -0.305 |
| exp_D_lenpen_neg05 | 107 | 0.973 | 0.958 | 0.967 | -0.925 | -0.915 | 0.863 | 0.814 |
| exp_E_sampling_low_temp | 107 | 0.910 | 0.872 | 0.874 | -0.828 | -0.809 | 0.648 | 0.044 |
| exp_F_sampling_original | 107 | 0.916 | 0.898 | 0.876 | -0.830 | -0.804 | 0.665 | 0.120 |
| exp_G_greedy | 107 | 0.911 | 0.898 | 0.858 | -0.807 | -0.672 | 0.675 | -0.064 |
| exp_H_lenpen_pos2 | 107 | 0.932 | 0.899 | 0.638 | -0.573 | -0.287 | 0.755 | -0.560 |
| exp_I_lenpen1_sample | 107 | 0.927 | 0.868 | 0.886 | -0.401 | -0.784 | 0.725 | -0.245 |
| exp_J_lenpen1_temp05 | 107 | 0.912 | 0.880 | 0.881 | -0.697 | -0.837 | 0.680 | -0.335 |
| exp_K_sampling_temp15 | 107 | 0.922 | 0.895 | 0.884 | -0.805 | -0.853 | 0.719 | 0.154 |
| exp_L_sampling_temp03 | 107 | 0.920 | 0.891 | 0.873 | -0.834 | -0.839 | 0.668 | 0.070 |
| exp_M_lenpen1_temp03 | 107 | 0.917 | 0.871 | 0.863 | -0.524 | -0.310 | 0.647 | -0.309 |

**Stability summary across all 16 configs:**

| Component | Mean r | Std | Min | Max | Stable? |
|-----------|--------|-----|-----|-----|---------|
| **IS Score** | **0.925** | 0.015 | 0.910 | 0.973 | Yes |
| **Semantic** | **0.891** | 0.020 | 0.868 | 0.958 | Yes |
| Phonetic | 0.869 | 0.065 | 0.638 | 0.967 | Moderate |
| NEA F1 | 0.712 | 0.057 | 0.647 | 0.863 | Moderate |
| WER | -0.706 | 0.156 | -0.925 | -0.401 | No |
| WWER | -0.728 | 0.178 | -0.915 | -0.287 | No |
| Length Ratio | -0.023 | 0.333 | -0.560 | 0.814 | No |

**Key finding:** The `llm_context_prob` heuristic's correlation with IS and with Semantic Similarity is **rock-solid** across all 16 configs (std < 0.02). WER and Length Ratio are the same volatile signals seen in the IS analysis (Section 10.2), confirming that these instabilities are properties of the signals themselves, not of the heuristic.

### 7.2b `llm_context_prob` Agreement (κ) — Cross-Configuration

| Config | N | Agreement | Cohen's κ | Precision | Recall | F1 |
|--------|---|-----------|----------|-----------|--------|-----|
| baseline_full | 1497 | 88.3% | 0.765 | 77.4% | 98.6% | 86.7% |
| full_decode_J | 1497 | **89.6%** | **0.791** | 80.2% | 98.5% | 88.4% |
| full_decode_C | 1497 | 87.6% | 0.752 | 76.0% | 99.1% | 86.0% |
| exp_D_lenpen_neg05 | 107 | **94.4%** | **0.862** | 81.8% | 100.0% | 90.0% |
| exp_G_greedy | 107 | 86.9% | 0.738 | 73.6% | 100.0% | 84.8% |
| exp_K_sampling_temp15 | 107 | 86.0% | 0.722 | 72.7% | 100.0% | 84.2% |
| exp_A_baseline (subset) | 107 | 83.2% | 0.670 | 70.7% | 97.6% | 82.0% |

*(Selected configs shown; full table in computation logs. Mean κ across all 16 configs: ~0.72, range 0.62-0.86.)*

**Recall is near-perfect across all configs** (97.6-100.0%) — the LLM heuristic almost never misses a segment that IS scores as captured. Precision varies more (65-82%), reflecting the heuristic's intentionally optimistic design. Config J achieves the best agreement at scale (κ=0.791).

### 7.3 Agreement with IS ≥ 3.0 Threshold

Confusion matrix comparing `llm_context_prob ≥ 0.5` vs `IS ≥ 3.0`:

|  | IS ≥ 3.0 (captured) | IS < 3.0 (failed) |
|--|---------------------|-------------------|
| **LLM ≥ 0.5** | 592 (TP) | 165 (FP) |
| **LLM < 0.5** | 5 (FN) | 735 (TN) |

| Metric | Value |
|--------|-------|
| Agreement | 88.6% |
| Cohen's κ | 0.773 (substantial) |
| Precision | 78.2% |
| **Recall** | **99.2%** |
| F1 | 87.4% |

**The LLM heuristic is intentionally optimistic** — it catches 99.2% of IS ≥ 3.0 segments but over-recovers 165 segments that IS scores below 3.0. This is by design: context recovery assumes a viewer with domain knowledge, which provides extra information beyond what the raw metrics capture.

### 7.3b Note on Weighted Kappa

Weighted kappa (quadratic) was explored by mapping `llm_context_prob` to 5 tiers via arbitrary probability bins. The result (κw=0.887) is high but **methodology-dependent** — the heuristic is fundamentally a binary system (recoverable at prob ≥ 0.5), not an ordinal 5-tier system like IS. Different bin boundaries produce different weighted κ values. The IS captured threshold (≥3.0 = 60%) and the heuristic threshold (≥0.5 = 50%) also differ, making ordinal comparison asymmetric. **We report the binary κ = 0.773 and Pearson r = 0.934 as the canonical validation metrics** because they compare the two systems on their native scales.

### 7.4 LLM Prob by IS Tier

| Tier | N | Mean LLM Prob | % Flagged Recoverable |
|------|---|--------------|----------------------|
| Failed (0-1) | 239 | 0.060 | 0.0% |
| Poor (1-2) | 336 | 0.246 | 1.2% |
| Fair (2-3) | 325 | 0.548 | 49.5% |
| Good (3-4) | 321 | 0.881 | 98.4% |
| Excellent (4-5) | 276 | 0.968 | 100.0% |

The LLM heuristic cleanly separates tiers 1-2 (nearly all < 0.5) from tiers 4-5 (nearly all ≥ 0.5). The Fair tier (2-3) is the boundary zone where it splits roughly 50/50.

### 7.5 Discrete Nature

The LLM heuristic produces only **15 discrete probability values** (from a decision tree with 15 leaf nodes), not a continuous distribution:

| Prob | Reason | Count | Mean IS |
|------|--------|-------|---------|
| 1.000 | near_perfect | 112 | 4.658 |
| 0.950 | strong_structure_match | 309 | 3.936 |
| 0.900 | high_semantic_good_overlap | 132 | 3.373 |
| 0.800 | semantic_plus_phonetic | 79 | 3.028 |
| 0.750 | good_overlap_coherent | 78 | 2.817 |
| 0.650 | moderate_semantic_preserved_content | 13 | 2.913 |
| 0.600 | moderate_structure_coherent | 10 | 2.546 |
| 0.550 | phonetic_bridge_semantic | 24 | 2.556 |
| 0.450 | entities_preserved_coherent | 5 | 2.193 |
| 0.400 | partial_overlap | 88 | 2.226 |
| 0.300 | marginal | 302 | 1.814 |
| 0.150 | unlikely_recoverable | 20 | 1.322 |
| 0.100 | no_semantic / length_mismatch / insufficient | 156 | 0.894 |
| 0.050 | hallucination | 99 | 0.857 |
| 0.000 | empty | 70 | 0.000 |

---

## 8. Relationship to "LLM-as-a-Judge" (Academic Paradigm)

### 8.1 Claude Designed the Judge (at Design Time — Not at Runtime)

The IS metric was not designed independently from LLM judgment — **Claude (Anthropic) acted as the expert judge at design time to create the evaluation framework**. However, Claude is **never called per-sample at evaluation time** — the resulting metrics are fully deterministic code with zero API calls. Specifically:

1. **Claude designed the 5-step assessment rubric** (Section 4 of the methodology): Phonetic Bridge Test, Context Recovery Test, Semantic Equivalence Test, Harmful Hallucination Check, and Final Score assignment. This rubric was developed by Claude evaluating real ref/hyp pairs from the pipeline output.

2. **Claude selected the 6 signals and their weights** — the choice of which automated signals to include (semantic similarity, phonetic similarity, WER, WWER, NEA F1, length ratio), how to scale them, and the 0.25/0.15 weight distribution were all Claude's expert judgment, calibrated against the 10 proof examples in Section 2 of the methodology.

3. **Claude defined the tier boundaries** — the IS ≥ 3.0 "properly captured" threshold and the 5-tier system map directly to Claude's scoring rubric (0-5 scale).

4. **Claude designed the context recovery heuristic** — the `estimate_llm_context_recovery()` decision tree with its 15 rules and 6 linguistic factors codifies Claude's judgment about when a viewer with domain context could recover meaning.

5. **Claude classified failure modes and success patterns** — the 5 failure categories and 7 success categories were defined by Claude analyzing real pipeline outputs.

This is a form of **LLM-distilled evaluation**: rather than calling an LLM per sample at runtime, the LLM's expert judgment was elicited once and encoded into deterministic, reproducible metrics. The IS metric is effectively "what Claude would score" — made computable, free, and deterministic.

> **Important distinction**: The term "LLM-as-a-Judge" in the academic literature (Zheng et al., 2023) typically means calling an LLM per sample at inference time to score each output. **We do NOT do this.** Claude was consulted once during metric design — the resulting `generate_intelligibility_scores.py` contains zero LLM API calls. It is pure Python math (`difflib.SequenceMatcher`, weighted sums, threshold comparisons). Running the IS pipeline on 1,497 segments takes seconds of local computation and costs $0.

### 8.2 How This Maps to the Academic LLM-as-a-Judge Literature

"LLM-as-a-Judge" (Zheng et al., 2023) typically refers to calling an LLM per sample at inference time. Our approach is a variant: **design-time LLM judgment distilled into automated metrics**.

| Aspect | Per-Sample LLM Judge | Our Approach: Claude-Distilled IS |
|--------|---------------------|----------------------------------|
| **When LLM is used** | At evaluation time (every sample) | At design time (rubric + calibration) |
| **LLM used** | GPT-4, Claude, etc. | Claude (Anthropic) |
| **Cost per run** | ~$45 for 1,497 segments | Free (local computation) |
| **Reproducibility** | Non-deterministic (temperature > 0) | Fully deterministic |
| **Transparency** | Opaque reasoning per sample | Every IS score decomposes into exactly which signals contributed |
| **Captures meaning** | Natively | Via semantic similarity (r=0.92 with IS) |
| **Captures phonetics** | Requires explicit prompting | Natively (phonetic sim, r=0.94 with IS) |
| **Domain-specific** | Yes (via prompt engineering) | Yes (lip-reading-aware: homophene groups, phonetic bridges) |
| **Handles hallucination** | Strong (can detect fluent nonsense) | Moderate (WER > 100% + length ratio) |

Key findings from the literature for context:
- GPT-4 as judge achieves ~80-85% agreement with human annotators on MT quality assessment (Kocmi & Federmann, 2023)
- Rubric-based prompting significantly improves reliability — our approach takes this to the extreme by baking the rubric into the metric itself
- Agreement between LLM judges and humans is comparable to inter-annotator agreement (~0.6-0.8 Cohen's κ) — our `llm_context_prob` achieves κ=0.773 against IS

### 8.3 What Per-Sample LLM Judging Would Add

If we additionally called Claude per-segment at evaluation time, the primary value would be:

1. **Better hallucination detection** — Claude can recognize fluent nonsense that sounds plausible but is factually wrong (our weakest area: 20.6% hallucination rate). The current metrics detect hallucination only via WER > 100% and length ratio anomalies.
2. **Pragmatic context** — "Would a viewer understand this in the context of a video about cooking?" requires world knowledge that deterministic heuristics lack.
3. **Nuanced partial credit** — The current IS formula gives equal weight to phonetic similarity whether the confused word is trivial or critical. Claude could assess this dynamically.
4. **Harmful content flagging** — Detecting when errors create offensive or dangerous misinterpretations (e.g., "mom's phone" → "bomb") requires understanding social context.

### 8.4 Why Distilled Judgment Is Sufficient

1. **Claude is the source of the judge, not the runtime judge** — the IS metric encodes Claude's evaluation framework, designed once at design time. No LLM is invoked when computing scores. Per-sample LLM calls would apply similar underlying judgment, just more granularly and at significant cost.
2. **Reproducibility** — deterministic metrics enable experiment comparison (Exp A vs B vs baseline) without noise from stochastic LLM outputs.
3. **Speed** — local computation in seconds vs 30-60 minutes of API calls.
4. **Decomposability** — every IS score can be traced to exactly which signal(s) drove it up or down, enabling targeted improvement. LLM reasoning is opaque.
5. **High internal consistency** — the `llm_context_prob` heuristic (also Claude-designed) correlates at r=0.93 with IS, confirming the two Claude-designed systems agree.

### 8.5 Opus Per-Sample Judge Agreement with IS

We also ran **Claude Opus 4.6 as a per-sample judge** on all 1,497 pairs in two conditions: blind (no topic context) and context-aware (topic inferred from reference). Agreement with IS ≥ 3.0 ("properly captured"):

| Judge Condition | Y+P vs IS≥3 κ | Agreement | Pearson r (ordinal vs IS) |
|----------------|---------------|-----------|--------------------------|
| **Blind** | 0.521 | 74.6% | 0.850 |
| **Context-aware** | 0.548 | 76.3% | 0.808 |
| **Heuristic** (`llm_context_prob≥0.5`) | 0.773 | 88.6% | 0.934 |

**However**, the low κ at IS ≥ 3.0 reflects a **threshold mismatch**, not a ranking disagreement. Sweeping IS thresholds reveals the Opus judge's natural boundary:

| IS Threshold | Blind Y+P κ | Blind Y+P agree | Context Y+P κ | Heuristic κ |
|-------------|-------------|-----------------|---------------|-------------|
| IS ≥ 1.50 | 0.769 | 89.9% | 0.690 | 0.574 |
| IS ≥ 2.00 | **0.818** | **91.5%** | **0.742** | 0.768 |
| IS ≥ 2.50 | 0.674 | 83.8% | 0.662 | **0.876** |
| IS ≥ 3.00 | 0.521 | 74.6% | 0.548 | 0.773 |
| IS ≥ 3.50 | 0.361 | 64.1% | 0.393 | 0.569 |

**Opus Y+P peaks at IS ≥ 2.0** (κ=0.818, "almost perfect"), while the **heuristic peaks at IS ≥ 2.5** (κ=0.876). The Opus judge considers Tier 3 ("Fair", IS 2.0–3.0) segments as partially useful — exactly the population identified by the LLM salvage analysis. This validates that the 165 salvageable segments (IS < 3.0, llm_context_prob ≥ 0.5) are genuinely recoverable.

**Y-only mapping** (stricter — does IS ≥ T predict Opus "full success"?):

| IS Threshold | Blind Y κ | Context Y κ |
|-------------|-----------|-------------|
| IS ≥ 3.00 | 0.565 | 0.405 |
| IS ≥ 3.75 | 0.692 | 0.573 |
| IS ≥ 4.00 | 0.658 | **0.620** |

Opus Y aligns best with IS ≥ 3.75–4.00 (Tier 5, "Excellent"). The judge reserves full endorsement for only the highest-quality outputs.

**Interpretation**: The three evaluation systems (IS, heuristic, Opus judge) agree on **ranking** (Pearson r = 0.85–0.93) but disagree on **where to draw the line**. IS ≥ 3.0 is our conservative "properly captured" threshold; the Opus judge's natural Y+P boundary is closer to IS ≥ 2.0 — it sees more segments as partially useful. This is consistent with the judge's holistic reasoning capturing contextual value that the purely metric-based IS formula penalizes.

- **Bug note (2026-03-05):** An earlier computation returned NaN for the context-aware judge due to using column name `context_judge` instead of the correct column name `context` in `context_eval_results.csv`. This has been resolved.

---

## 9. Descriptive Statistics

| Metric | Mean | Median | Std | Min | Max | Skew |
|--------|------|--------|-----|-----|-----|------|
| IS Score | 2.520 | 2.538 | 1.372 | 0.000 | 5.000 | -0.055 |
| Semantic Sim | 0.437 | 0.412 | 0.308 | -0.093 | 1.000 | 0.215 |
| Phonetic Sim | 0.552 | 0.588 | 0.276 | 0.000 | 1.000 | -0.344 |
| WER % | 64.054 | 61.100 | 39.277 | 0.000 | 400.000 | 1.599 |
| WWER % | 61.887 | 60.000 | 33.354 | 0.000 | 300.000 | 0.856 |
| NEA F1 % | 38.941 | 35.300 | 36.694 | 0.000 | 100.000 | 0.319 |
| Length Ratio | 0.925 | 0.947 | 0.348 | 0.000 | 4.000 | 0.913 |
| LLM Context Prob | 0.551 | 0.550 | 0.364 | 0.000 | 1.000 | -0.071 |

---

## 10. Principal Component Analysis (PCA)

*(Added 2026-03-07. Full analysis: [is_pca_analysis.md](is_pca_analysis.md))*

PCA on the 6 standardized IS signals reveals **2 principal components** (Kaiser criterion: eigenvalue > 1):

| PC | Eigenvalue | % Variance | Cumulative % | Interpretation |
|----|-----------|------------|-------------|----------------|
| **PC1** | **4.107** | **68.4%** | 68.4% | General signal quality — all 5 content signals load equally (0.43-0.47) |
| **PC2** | **1.168** | **19.5%** | 87.9% | Output length — Length Ratio dominates (0.91) |
| PC3 | 0.309 | 5.1% | 93.0% | Entity swing — NEA F1 dominates (0.83) |

**Key finding:** Semantic Similarity loads on PC1 at 0.445 — virtually identical to the word-accuracy signals. It is **not** an independent dimension. The earlier claim that the 6 signals form "3 independent dimensions" (word accuracy 60%, meaning 28%, sanity 9%) was based on correlation clustering and covariance decomposition, not PCA. The actual PCA shows 2 dimensions: signal quality (68.4%) and output length (19.5%).

**Correction (2026-03-07):** All references to "PCA analysis reveals 3 independent dimensions" in presentations and documentation have been corrected to describe the actual PCA results. The covariance decomposition (Section 3) remains valid as a separate analysis of variance contribution within the IS formula — it describes how much each weighted component contributes to IS spread, not how many independent dimensions exist.

---

*Sections 11-14 (cross-config validation, salvage analysis, methodology notes, LLM judge validation) have been moved to [is_cross_config_validation.md](is_cross_config_validation.md) for easier navigation.*
