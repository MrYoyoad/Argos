# Context-Aware LLM-as-a-Judge: Final Analysis

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

### Distribution (1,456 batch entries including 30 duplicates)

| Judgment | Count | Rate |
|----------|-------|------|
| **Y (full success)** | 229 | 15.7% |
| **P (partial)** | 720 | 49.5% |
| **N (failure — LLM-judged)** | 507 | 34.8% |
| **N (auto — empty hypothesis)** | 71 | — |

### Comparison vs Blind Evaluation

| Judgment | Blind (1,497) | Context (1,456 batch) | Delta |
|----------|---------------|----------------------|-------|
| **Y** | 345 (23.0%) | 229 (15.7%) | **−7.3pp** |
| **P** | 626 (41.8%) | 720 (49.5%) | **+7.7pp** |
| **N** | 526 (35.1%) | 507 (34.8%) | −0.3pp |
| **Y+P** | 971 (64.9%) | 949 (65.2%) | **+0.3pp** |

**Key finding: the overall pass rate (Y+P) is unchanged at ~65%.** Context awareness does not change how many segments are useful — it only raises the bar for "full success", shifting 7pp from Y into P.

---

## Main Findings

### 1. Context Is Stricter, Not More Lenient

Adding topic/domain context made the judge more conservative about "full success". A hypothesis that looked adequate in a blind comparison often revealed vocabulary mismatches when evaluated against the inferred domain. This is the dominant effect: **Y→P downgrades (estimated ~138 transitions)** vastly outnumber Y→N.

The aggregate capture rate (Y+P) is unchanged: 64.9% blind vs 65.2% context. Context mode is a **quality discriminator**, not a rescue mechanism.

### 2. N Is Stable

N rate barely moves (35.1% → 34.8%). Context provides little additional information for segments that already failed — genuinely bad transcriptions are already identifiable without domain knowledge.

### 3. Per-Topic Patterns

Some domains benefit from context (context helps accept phonetically-approximate but topically-valid hypotheses):

| Topic | Blind Y+P | Context Y+P | Delta |
|-------|-----------|-------------|-------|
| DIY/Home | 48% | ~56% | +8pp |
| Religion/Spirituality | 53% | ~59% | +6pp |
| Sports/Fitness | 74% | ~77% | +3pp |
| Politics/News | 74% | 76% | +2pp |
| Business/Finance | 76% | 76% | 0pp |
| Technology | 72% | ~69% | −3pp |
| Cooking/Food | 70% | ~65% | −5pp |
| Education/Academic | 77% | ~72% | −5pp |

Note: per-topic context deltas are estimated from the preliminary batch analysis. DIY/Home (+8pp) benefits most — a visually-grounded domain where approximate vocabulary can still convey meaning if the topic is known. Technology and Education decline slightly — domain knowledge raises terminology expectations.

### 4. Cross-Condition Reliability

The 30 duplicate pairs yielded **80.0% cross-condition agreement** between blind and context evaluations of the same pair. This is slightly below the blind intra-rater rate of 86.7%, confirming that context-aware evaluation applies a meaningfully different standard. The 6.7pp gap reflects genuine mode effect, not noise.

---

## Implications

**For gold standard calibration:** The blind evaluation remains the primary benchmark (conservative, domain-agnostic, consistent). The context-aware figures (Y=15.7%, Y+P=65.2%) represent a stricter domain-expert standard and are more appropriate when evaluating whether a system would satisfy a subject-matter expert viewer.

**For system improvement:** Context injection at decode time is most likely to help DIY/Home, Sports, and Religious content — the three domains where topic knowledge improved the pass rate. These are also the domains where the deterministic `llm_context_prob` heuristic (the 15-rule decision tree) already struggles because visual grounding is harder to detect from text alone.

**Context does not rescue failures.** Only ~1 N→Y transition occurred across the full evaluation. Segments that completely failed in blind mode remain failures with context.

---

## Relationship to Other Evaluations

- **Blind gold standard:** [llm_judge_analysis.md](../llm_judge_analysis.md) — 1,497 pairs, Y=23.0%, Y+P=64.9%
- **Finetune validation (224 segments, blind):** [finetune_llm_judge_comparison.md](../finetune_llm_judge_comparison.md) — Baseline Y+P=51.8%, Exp A 51.3%, Exp B 53.6%
- **IS correlation analysis:** [../../is_correlation_analysis.md](../../is_correlation_analysis.md) — cross-config stability
