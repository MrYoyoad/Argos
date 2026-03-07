# LLM Salvage Analysis: Recoverable Predictions That Metrics Undercount

**Date**: 2026-03-03
**Dataset**: Full baseline (1,497 segments, AVSpeech)
**Divergent segments**: 165 (LLM prob >= 0.5, IS < 3.0)

## Executive Summary

Traditional metrics (WER, WWER, IS) classify 900 of 1,497 segments as failures (IS < 3.0). However, the `llm_context_prob` heuristic — a deterministic 15-rule decision tree designed by Claude at design time (no LLM API calls at runtime) — identifies **165 of these 900 segments** as having recoverable meaning. These are cases where a viewer with domain context would understand the lip-reading output despite high word error rates.

> **Note (March 2026):** NIV thresholds supersede IS >= 3.0. IS >= 2.00 (NIV Y+P, κ=0.818 vs Opus judge) captures 922 segments (61.6%), which already includes many segments this salvage analysis identified. The salvage concept remains valid for the gap between NIV Y (IS >= 3.80, 346 segments) and NIV Y+P (IS >= 2.00, 922 segments). See [threshold_calibration_vs_opus.md](../threshold_calibration_vs_opus.md).

This represents an **18.3% recovery rate** among segments that metrics mark as failed. If we include these, the effective intelligibility rate rises from 39.9% to **50.9%** of all segments.

### Key Numbers

| Metric | Count | Percentage |
|--------|-------|------------|
| Total segments | 1497 | 100% |
| IS >= 3.0 (metrics say captured) | 597 | 39.9% |
| IS < 3.0 (metrics say failed) | 900 | 60.1% |
| LLM prob >= 0.5 (Claude-designed heuristic says recoverable) | 757 | 50.6% |
| **Divergent: LLM salvages from IS failures** | **165** | **18.3% of failures** |
| **Effective capture rate (IS + LLM salvage)** | **762** | **50.9%** |

### Divergent Segment Profile

**WER distribution of salvageable segments:**

| WER Range | Count | % of Divergent |
|-----------|-------|----------------|
| 0-30% | 1 | 0.6% |
| 30-50% | 32 | 19.4% |
| 50-70% | 96 | 58.2% |
| 70-100% | 28 | 17.0% |
| 100%+ | 8 | 4.8% |

**Recovery mechanism (why Claude says recoverable):**

| LLM Reason | Count | % | Interpretation |
|------------|-------|---|----------------|
| good_overlap_coherent | 54 | 32.7% | Key content words match and topic is preserved |
| semantic_plus_phonetic | 35 | 21.2% | Meaning preserved via semantics and natural lip-reading confusions |
| high_semantic_good_overlap | 28 | 17.0% | Strong meaning match with significant word overlap |
| phonetic_bridge_semantic | 21 | 12.7% | Phonetically similar words bridge to correct meaning |
| strong_structure_match | 10 | 6.1% | Word order and structure closely match reference |
| moderate_structure_coherent | 10 | 6.1% | Moderate structural similarity with topic coherence |
| moderate_semantic_preserved_content | 7 | 4.2% | Moderate semantic match with preserved content words |

**Topic distribution:**

| Topic | Salvageable | Rate |
|-------|-------------|------|
| Other | 99 | 17% of topic failures |
| Cooking/Food | 18 | 28% of topic failures |
| Entertainment | 12 | 25% of topic failures |
| Education/Academic | 10 | 22% of topic failures |
| Technology | 10 | 15% of topic failures |
| Business/Finance | 5 | 25% of topic failures |
| Sports/Fitness | 4 | 25% of topic failures |
| DIY/Home | 3 | 16% of topic failures |
| Politics/News | 2 | 12% of topic failures |
| Religion/Spirituality | 2 | 18% of topic failures |

---

*Curated examples (5 per category, 30 total) have been moved to [salvage_example_gallery.md](salvage_example_gallery.md) for easier navigation.*

---

## Implications for VSP System Evaluation

### 1. WER Systematically Undervalues Lip-Reading Output

WER treats all word substitutions equally. But in lip-reading:
- 'admiral' → 'animal' is a **catastrophic** error (entity destroyed)
- 'going to' → 'gonna' is a **harmless** paraphrase
- 'the' → 'a' is a **trivial** function word change

The 165 salvageable segments demonstrate that WER conflates these fundamentally different error types into a single number.

### 2. Context Recovery Is Real

A domain-aware viewer (e.g., someone watching a cooking tutorial) can often fill in gaps from context. When the model outputs 'add the flour and stir' instead of 'add the flower and steer,' the viewer's domain knowledge corrects the phonetic confusion automatically.

### 3. Effective System Value Is Higher Than Metrics Suggest

- **Metric-based capture rate**: 39.9% (IS >= 3.0)
- **LLM-adjusted capture rate**: 50.9% (IS >= 3.0 OR LLM-salvageable)
- **Uplift**: +11.0 percentage points (+28% relative improvement)

This means the VSP-LLM system delivers useful output for roughly **1 in 2 segments** rather than the **2 in 5** that metrics alone suggest.

## Methodology

### Selection Criteria

A segment is classified as "LLM-salvageable" when:
1. `llm_context_prob >= 0.5` — Claude's heuristic assigns at least 50% probability that a viewer with domain context could recover the intended meaning
2. `intelligibility_score < 3.0` — Traditional IS metric classifies the segment as below the "properly captured" threshold

### LLM Heuristic

The `llm_context_prob` is a deterministic, 15-rule decision tree designed by Claude that evaluates six linguistic factors: content word overlap, sequence preservation, phonetic plausibility, length sanity, semantic domain coherence, and information density. It correlates at r=0.934 with IS across the full dataset and is stable across 16 different decode configurations (std=0.015).

### Validation

Cross-configuration analysis (16 decode parameter sets) confirms:
- Mean correlation with IS: r=0.925 (std=0.015)
- Agreement on IS >= 3.0 threshold: 88.6%, Cohen's kappa = 0.773
- Recall: 99.2% (almost never misses a properly captured segment)
- Precision: 78.2% (intentionally optimistic — assumes domain context)
