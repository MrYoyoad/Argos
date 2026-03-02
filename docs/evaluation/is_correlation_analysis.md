# IS Metric — Component Correlation Analysis

**Argos — The Orchard**
**Date:** 2026-03-02
**Dataset:** 1,497 segments (full AVSpeech baseline, February 2026)

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

### 8.1 Claude IS the Judge

The IS metric was not designed independently from LLM judgment — **Claude (Anthropic) was the LLM-as-a-Judge throughout this project**. Specifically:

1. **Claude designed the 5-step assessment rubric** (Section 4 of the methodology): Phonetic Bridge Test, Context Recovery Test, Semantic Equivalence Test, Harmful Hallucination Check, and Final Score assignment. This rubric was developed by Claude evaluating real ref/hyp pairs from the pipeline output.

2. **Claude selected the 6 signals and their weights** — the choice of which automated signals to include (semantic similarity, phonetic similarity, WER, WWER, NEA F1, length ratio), how to scale them, and the 0.25/0.15 weight distribution were all Claude's expert judgment, calibrated against the 10 proof examples in Section 2 of the methodology.

3. **Claude defined the tier boundaries** — the IS ≥ 3.0 "properly captured" threshold and the 5-tier system map directly to Claude's scoring rubric (0-5 scale).

4. **Claude designed the context recovery heuristic** — the `estimate_llm_context_recovery()` decision tree with its 15 rules and 6 linguistic factors codifies Claude's judgment about when a viewer with domain context could recover meaning.

5. **Claude classified failure modes and success patterns** — the 10 failure categories and 7 success categories were defined by Claude analyzing real pipeline outputs.

This is a form of **LLM-distilled evaluation**: rather than calling an LLM per sample at runtime, the LLM's expert judgment was elicited once and encoded into deterministic, reproducible metrics. The IS metric is effectively "what Claude would score" — made computable, free, and deterministic.

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

1. **The judge IS Claude** — the IS metric already encodes Claude's evaluation framework. Per-sample calls would apply the same underlying judgment, just more granularly.
2. **Reproducibility** — deterministic metrics enable experiment comparison (Exp A vs B vs baseline) without noise from stochastic LLM outputs.
3. **Speed** — local computation in seconds vs 30-60 minutes of API calls.
4. **Decomposability** — every IS score can be traced to exactly which signal(s) drove it up or down, enabling targeted improvement. LLM reasoning is opaque.
5. **High internal consistency** — the `llm_context_prob` heuristic (also Claude-designed) correlates at r=0.93 with IS, confirming the two Claude-designed systems agree.

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

## 10. Methodology Notes

- **Pearson r** measures linear correlation; **Spearman ρ** measures monotonic (rank) correlation
- Where Spearman >> Pearson (e.g., WER), the relationship is monotonic but nonlinear — extreme values compress the linear fit
- **Variance contribution** uses covariance decomposition: % = Cov(IS, weighted_component) / Var(IS)
- **Per-tier correlations** have reduced sample sizes (239-336 per tier) and narrower ranges, so absolute r values are lower than the global correlations
- All correlations are computed on the full 1,497-segment baseline dataset (February 2026)
