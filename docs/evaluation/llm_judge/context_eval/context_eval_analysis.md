# Context-Aware LLM-as-a-Judge: Final Analysis

> **Note (March 2026):** This document uses the legacy IS ≥ 3.0 threshold (40.1% captured). Current NIV thresholds supersede this: IS ≥ 2.00 = 61.6% useful (κ=0.818), IS ≥ 3.80 = 23.1% clearly conveyed (κ=0.690). See [threshold_calibration_vs_opus.md](../../threshold_calibration_vs_opus.md).

**Date:** March 2026
**Evaluation:** Claude Opus 4.6, context-aware mode
**Coverage:** 1,497 pairs (same pool as blind gold standard)

---

## Protocol

All 1,497 hypothesis-reference pairs from the baseline VSP-LLM evaluation were re-evaluated with topic/domain context injected into the judgment prompt. The same 3-level Y/P/N scale and conservative tie-breaking rules applied as in the blind evaluation.

**Key change from blind protocol:** The judge was instructed to consider the likely topic/domain of each reference when deciding whether the hypothesis conveyed meaning. No explicit topic labels were injected — the judge inferred topic from the reference text, simulating how a human viewer who knows the video type would interpret the transcript.

**Coverage breakdown:**
- 71 pairs with empty hypothesis → auto-classified N (same as blind eval)
- 1,426 unique pairs → evaluated by LLM
- 30 duplicate pairs embedded across batches for cross-condition reliability
- 15 batches of ~100 pairs each, shuffled with seed 42

---

## Final Results

### De-duplicated Distribution (1,497 unique pairs)

| Judgment | Count | Rate |
|----------|-------|------|
| **Y (full success)** | 225 | 15.0% |
| **P (partial)** | 705 | 47.1% |
| **N (failure)** | 567 | 37.9% |

### Comparison vs Blind Evaluation

| Judgment | Blind (1,497) | Context (1,497) | Delta |
|----------|---------------|-----------------|-------|
| **Y** | 345 (23.0%) | 225 (15.0%) | **−8.0pp** |
| **P** | 626 (41.8%) | 705 (47.1%) | **+5.3pp** |
| **N** | 526 (35.1%) | 567 (37.9%) | +2.8pp |
| **Y+P** | 971 (64.9%) | 930 (62.1%) | **−2.7pp** |

**Key finding:** Context awareness makes the judge **stricter overall** — Y+P drops by 2.7pp (from 64.9% to 62.1%). The dominant shift is Y→P (−8pp Y, +5.3pp P): domain knowledge reveals vocabulary mismatches in segments that appeared adequate without context. N also increases slightly (+2.8pp) as some previously-partial segments are revealed to be more fundamentally wrong.

---

## Transition Matrix (Blind → Context)

| Blind→Context | →Y | →P | →N |
|---|---|---|---|
| **Y** | 207 | **138** | 0 |
| **P** | 17 | 517 | **92** |
| **N** | 1 | 50 | 475 |

- **230 downgrades** vs **68 upgrades** → net −162 (−10.8%)
- **80.1% stable** (1,199 pairs received same judgment)
- Dominant transition: **Y→P (138 cases)** — hypothesis seemed complete without domain context, but domain knowledge revealed vocabulary failures
- **P→N (92 cases)** — partial successes revealed to be deeper failures under domain scrutiny
- **N→Y: 1 case only** — context essentially never rescues complete failures

---

## Per-Topic Analysis

| Topic | n | Blind Y+P | Context Y+P | Delta |
|-------|---|-----------|-------------|-------|
| Sports/Fitness | 31 | 74.2% | 77.4% | **+3.2pp** |
| DIY/Home | 27 | 48.1% | 55.6% | **+7.4pp** |
| Religion/Spirituality | 17 | 52.9% | 58.8% | **+5.9pp** |
| Politics/News | 34 | 73.5% | 76.5% | +2.9pp |
| Business/Finance | 46 | 76.1% | 76.1% | 0.0pp |
| Technology | 132 | 72.0% | 68.9% | −3.0pp |
| Cooking/Food | 117 | 70.1% | 65.0% | −5.1pp |
| Education/Academic | 86 | 76.7% | 72.1% | −4.7pp |
| Medical/Health | 39 | 66.7% | 61.5% | −5.1pp |
| Entertainment | 69 | 60.9% | 56.5% | −4.3pp |
| Other | 899 | 61.7% | 58.7% | −3.0pp |

DIY/Home (+7.4pp), Religion/Spirituality (+5.9pp), and Sports/Fitness (+3.2pp) benefit from context — these are domains where knowing the topic helps accept phonetically-approximate but topically-valid hypotheses. Technology, Cooking, Medical, and Education show declines because domain knowledge raises terminology expectations.

---

## Cross-Condition Reliability

The 30 duplicate pairs yielded **80.0% cross-condition agreement** between blind and context evaluations of the same pair. This is below the blind intra-rater rate of 86.7%, confirming that context-aware evaluation applies a meaningfully different (stricter) standard. The 6.7pp gap reflects genuine mode effect, not noise.

---

## Hallucination Detection

Hallucinated segments (WER ≥ 100%) were already caught at a very high blind rate (91.9% N). Context improved this only marginally: **4 additional hallucinations caught** that blind evaluation missed. Total hallucinated N-rate in context mode: 89.3%.

---

## Implications

1. **Context-aware evaluation is a quality tool, not a rescue tool.** It reveals hidden vocabulary failures in segments that appear adequate at first glance. The primary effect is downgrading shallow "close enough" blind Y calls to P — making the gold standard stricter.

2. **Domain-visual content benefits most.** DIY/Home (+7.4pp), Religion/Spirituality (+5.9pp), and Sports/Fitness (+3.2pp) show improved Y+P rates, suggesting that when topic knowledge lets the judge correctly accept phonetically-approximate but semantically-adequate hypotheses, it helps.

3. **Context does not rescue complete failures.** Only 1 N→Y transition occurred across 1,497 pairs. Segments with total topic drift or hallucination are not recoverable by contextual reasoning alone.

4. **Effective capture rate revision:** Using blind as the primary standard (conservative, domain-agnostic), the gold standard capture rates remain Y=23.0%, Y+P=64.9%. Context-aware figures (Y=15.0%, Y+P=62.1%) represent a more stringent domain-expert benchmark. Both are valid reference points for different use cases.

5. **Threshold alignment with IS:** Both blind and context-aware judges agree best with IS at a lower threshold than IS ≥ 3.0. Blind Y+P peaks at IS ≥ 2.0 (κ=0.818, 91.5% agreement); context Y+P also peaks at IS ≥ 2.0 (κ=0.742, 87.8%). The three systems agree strongly on **ranking** (Pearson r 0.81–0.85) but disagree on **where to draw the useful/useless line**. Our IS ≥ 3.0 threshold is deliberately conservative; the Opus judge's natural boundary is one tier lower.

---

## Relationship to Other Evaluations

- **Blind gold standard:** [llm_judge_analysis.md](../llm_judge_analysis.md) — 1,497 pairs, Y=23.0%, Y+P=64.9%
- **Finetune validation (224 segments, blind):** [finetune_llm_judge_comparison.md](../finetune_llm_judge_comparison.md) — Baseline Y+P=51.8%, Exp A 51.3%, Exp B 53.6%
- **IS correlation analysis:** [../../is_correlation_analysis.md](../../is_correlation_analysis.md) — cross-config stability
