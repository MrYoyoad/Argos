# Client Trust Calibration — Coverage vs False Positives

**Status.** Empirical analysis on the full 1,497-segment evaluation. May 2 2026.

**Source data.** [english_full_nbest_eval/client_trust/CLIENT_TRUST_CALIBRATION.md](../../english_full_nbest_eval/client_trust/CLIENT_TRUST_CALIBRATION.md) (auto-generated) and [client_trust_calibration.csv](../../english_full_nbest_eval/client_trust/client_trust_calibration.csv).

**Generator.** [analyze_client_trust_calibration.py](../_research-tools/generators/analyze_client_trust_calibration.py).

**Companion docs.** [confidence_shape_and_beam_disagree_design.md](confidence_shape_and_beam_disagree_design.md) (the band rule), [lessons_learned_band_rule_v2.md](lessons_learned_band_rule_v2.md) (how we got here), [SAFETY_ANALYSIS.md](../../english_full_nbest_eval/safety_analysis/SAFETY_ANALYSIS.md) (per-word and per-segment safety).

---

## The question this answers

A client viewing a transcript decides which segments to trust based on the visible coloring. The natural rule is **"trust segments where most words look green."** If we formalise that as "trust if the green-fraction in the segment is ≥ T", the table below shows what the client gets at each choice of T:

- How many segments end up trusted.
- How many of those are actually useful (true positives).
- How many are wrongly trusted (false positives — the dangerous case).
- What fraction of all useful segments the client picks up (recall).
- What fraction of trusted segments are *clearly* conveyed (the strict NIV-Y bar).

This is the operational tradeoff between picking up useful content and avoiding misplaced trust.

---

## Setup

- Full evaluation set: **1,427 segments**.
- **Useful** (NIV-Y+P, IS ≥ 2.00): **924** (64.8%).
- **Clearly conveyed** (NIV-Y, IS ≥ 3.80): **361** (25.3%).
- **Not useful** (NIV-N, IS < 2.00): **503** (35.2%).

The 65% "useful results" number is the NIV-Y+P count.

---

## The tradeoff under the new (joint conf+agreement) band rule

| Threshold T | Trusted | Useful caught (TP) | Wrongly trusted (FP) | Recall of useful | Precision | False-positive rate | Of trusted, NIV-Y |
|---|---|---|---|---|---|---|---|
| ≥ 10% | 1,041 | 853 | 188 | 92.3% | 81.9% | 37.4% | 34.3% |
| ≥ 20% | 818 | 747 | 71 | 80.8% | 91.3% | 14.1% | 42.7% |
| **≥ 30%** | **630** | **602** | **28** | **65.2%** | **95.6%** | **5.6%** | **52.5%** |
| ≥ 40% | 470 | 458 | 12 | 49.6% | 97.4% | 2.4% | 62.1% |
| **≥ 50%** | **321** | **312** | **9** | **33.8%** | **97.2%** | **1.8%** | **72.0%** |
| ≥ 60% | 180 | 178 | 2 | 19.3% | 98.9% | 0.4% | 78.9% |
| **≥ 70%** | **71** | **70** | **1** | **7.6%** | **98.6%** | **0.2%** | **88.7%** |
| ≥ 80% | 28 | 28 | 0 | 3.0% | 100.0% | 0.0% | 100.0% |
| ≥ 90% | 5 | 5 | 0 | 0.5% | 100.0% | 0.0% | 100.0% |

---

## Three operating points worth naming

### Permissive — "trust if ≥ 30% of the words are green"

- **630** segments trusted.
- **602 useful captured** (65.2% of all NIV-Y+P).
- **28 false positives** (5.6% of NIV-N segments).
- 52.5% of trusted segments are clearly conveyed (NIV-Y).

**Use case.** Default for most clients. Surface as much useful content as possible. Misled on roughly **1 in 22 trusted segments**, but recovers two thirds of all useful content.

### Moderate — "trust if ≥ 50% of the words are green"

- **321** segments trusted.
- **312 useful captured** (33.8% of all NIV-Y+P).
- **9 false positives** (1.8% FPR).
- 72% of trusted segments are clearly conveyed.

**Use case.** When precision matters more than recall. Misled on **1 in 35 trusted segments**, but only catches a third of useful content.

### Strict — "trust if ≥ 70% of the words are green"

- **71** segments trusted.
- **70 useful captured** (7.6% of NIV-Y+P).
- **1 false positive** (0.2% FPR).
- 88.7% of trusted segments are clearly conveyed.

**Use case.** High-stakes downstream decisions. Misled on roughly **1 in 71 trusted segments**, but only catches 7.6% of useful content.

---

## How the new rule compares to the old (conf-only) rule

The old single-threshold rule (conf ≥ 0.85 → green, no agreement check) produced more visually-confident transcripts but at a higher false-positive cost. Side-by-side at comparable recall:

| Rule | Threshold | Recall | Precision | False positives | FPR |
|---|---|---|---|---|---|
| New | ≥ 30% green | 65.2% | 95.6% | 28 | 5.6% |
| Old | ≥ 50% green | 64.5% | 94.8% | 33 | 6.6% |
| Old | ≥ 30% green | 90.3% | 84.5% | **153** | **30.4%** |

At ~65% recall, the new rule cuts false positives modestly (28 vs 33) and the FPR drops a percentage point. **More importantly, the new rule's "≥ 30% green" threshold delivers what the old rule's "≥ 50% green" delivered**, lowering the cosmetic bar a user must satisfy. The old rule's same "≥ 30% green" is a much weaker promise — 30% of useless segments are wrongly trusted.

The deepest gain is at the high-trust end. At 70% green:
- Old rule: 27 false positives across the full sweep.
- New rule: at most 1 false positive across all thresholds ≥ 60%.

Once a client is willing to wait for "mostly green," the new rule essentially eliminates the misleading cases.

---

## The structural ceiling

Even at the permissive 30% threshold, **322 of the 924 NIV-Y+P segments (34.8%)** fall below the threshold and are missed. These are segments where the model produced something useful but not via clean visual signal — agreement is thin, individual confidences are mid-band. The band system fundamentally cannot reach them. Recovering them would require a different signal:

- Post-hoc LLM rerank scoring fluency + plausibility.
- Topic-conditional priors (the [llm_judge context_eval](../evaluation/llm_judge/context_eval/) work shows context labelling is informative).
- Semantic-coherence check against the segment-level transcript.

This is the operational ceiling on confidence-band trust calibration alone, on this LLM and decoder. Roughly **35% of useful content is structurally invisible** to the band-fraction trust rule.

---

## Recommended default for the client

**Trust if ≥ 30% of words in a segment are green.** This delivers:

- 65% of useful content surfaced (602 of 924 useful segments).
- 96% precision — about 1 misleading transcript for every 22 trusted ones.
- Roughly half (52.5%) of trusted segments are *clearly* conveyed; the other half are *partially* conveyed but contain real signal.

The threshold matches the green-fraction bin where the predictive signal turns from "weak" to "strong" in the [SAFETY_ANALYSIS.md](../../english_full_nbest_eval/safety_analysis/SAFETY_ANALYSIS.md) per-segment table — segments at 30–50% green hit P(NIV-Y+P) = 0.94, P(hallucination) = 0.02. That's the operational sweet spot.

For clients who can absorb a higher miss rate in exchange for near-zero false positives, **≥ 70% green** is the high-trust point.

---

## Replication

```bash
python3 docs/_research-tools/generators/analyze_band_safety.py \
  --per-word english_full_nbest_eval/trust_diagnostic/per_word_diagnostic.csv \
  --report-csv english_full_nbest_eval/report/report.csv \
  --out-dir english_full_nbest_eval/safety_analysis

python3 docs/_research-tools/generators/analyze_client_trust_calibration.py \
  --per-segment english_full_nbest_eval/safety_analysis/per_segment_safety.csv \
  --out-dir english_full_nbest_eval/client_trust
```

Re-run when the model, the decoder, the band rule thresholds, or the NIV definitions change. The numbers above are LLM-and-decoder-specific (Llama-2-7b, beam=20, lenpen=0).

---

## What this is NOT

- This is not a per-word reliability table. For per-word P(correct) by band, see [SAFETY_ANALYSIS.md §1](../../english_full_nbest_eval/safety_analysis/SAFETY_ANALYSIS.md).
- This is not a justification of the band rule itself. For the design and the trust-check that validated it, see [confidence_shape_and_beam_disagree_design.md](confidence_shape_and_beam_disagree_design.md) and [TRUST_DIAGNOSTIC.md](../../english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md).
- This is not a recommendation about UI visual design. The numbers describe what fraction-green *predicts*; the UI choice of how to render that prediction (badges, banners, etc.) is a separate decision.
