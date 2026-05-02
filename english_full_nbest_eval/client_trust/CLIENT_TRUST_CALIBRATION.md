# Client Trust Calibration — recall vs false-positive tradeoff

**Question this answers.** If a client uses "fraction of green words in a segment ≥ T" as their decision rule for whether to trust a segment, how many useful segments do they catch and how many do they wrongly trust?

**Setup.** Full evaluation set: **1,427 segments**. Useful (NIV-Y+P, IS ≥ 2.00): **924** (64.8%). Clearly-conveyed (NIV-Y, IS ≥ 3.80): **361** (25.3%). Not-useful (NIV-N, IS < 2.00): **503** (35.2%).

**Definitions.**
- *Trusted* = segments where green-fraction ≥ T. The client treats these as reliable.
- *True positive* = trusted AND actually useful (NIV-Y+P).
- *False positive* = trusted but NOT useful — the client's trust is misplaced.
- *Recall* = fraction of useful segments captured by the rule.
- *Precision* = fraction of trusted segments that are actually useful.
- *FPR* = fraction of NOT-useful segments wrongly trusted.

---

## Under the new rule (joint conf+agreement)

| T (green-frac ≥) | Trusted | TPs (useful caught) | FPs (wrongly trusted) | Recall (of useful) | Precision | FPR | NIV-Y of trusted |
|---|---|---|---|---|---|---|---|
| 10% | 1041 | 853 | 188 | 92.3% | 81.9% | 37.4% | 357 (34.3%) |
| 20% | 818 | 747 | 71 | 80.8% | 91.3% | 14.1% | 349 (42.7%) |
| 30% | 630 | 602 | 28 | 65.2% | 95.6% | 5.6% | 331 (52.5%) |
| 40% | 470 | 458 | 12 | 49.6% | 97.4% | 2.4% | 292 (62.1%) |
| 50% | 321 | 312 | 9 | 33.8% | 97.2% | 1.8% | 231 (72.0%) |
| 60% | 180 | 178 | 2 | 19.3% | 98.9% | 0.4% | 142 (78.9%) |
| 70% | 71 | 70 | 1 | 7.6% | 98.6% | 0.2% | 63 (88.7%) |
| 80% | 28 | 28 | 0 | 3.0% | 100.0% | 0.0% | 28 (100.0%) |
| 90% | 5 | 5 | 0 | 0.5% | 100.0% | 0.0% | 5 (100.0%) |

## Under the old rule (conf-only) — for comparison

| T (green-frac ≥) | Trusted | TPs | FPs | Recall | Precision | FPR | NIV-Y of trusted |
|---|---|---|---|---|---|---|---|
| 10% | 1286 | 914 | 372 | 98.9% | 71.1% | 74.0% | 361 (28.1%) |
| 20% | 1138 | 891 | 247 | 96.4% | 78.3% | 49.1% | 361 (31.7%) |
| 30% | 987 | 834 | 153 | 90.3% | 84.5% | 30.4% | 357 (36.2%) |
| 40% | 813 | 743 | 70 | 80.4% | 91.4% | 13.9% | 349 (42.9%) |
| 50% | 629 | 596 | 33 | 64.5% | 94.8% | 6.6% | 331 (52.6%) |
| 60% | 435 | 421 | 14 | 45.6% | 96.8% | 2.8% | 287 (66.0%) |
| 70% | 253 | 250 | 3 | 27.1% | 98.8% | 0.6% | 198 (78.3%) |
| 80% | 118 | 116 | 2 | 12.6% | 98.3% | 0.4% | 103 (87.3%) |
| 90% | 27 | 27 | 0 | 2.9% | 100.0% | 0.0% | 27 (100.0%) |

---

## Three operating points worth naming

### Permissive — "≥30% green"

- **630** segments trusted
- **602** useful captured (65.2% of all NIV-Y+P)
- **28** false positives (5.6% of NIV-N segments — about 1 misleading transcript per 18 useless ones)
- **331 (52.5%)** of trusted are clearly conveyed (NIV-Y)

Use case: surface as much useful content as possible. Default for most clients.

### Moderate — "≥50% green"

- **321** segments trusted
- **312** useful captured (33.8% of all NIV-Y+P)
- **9** false positives (1.8% FPR)
- **231 (72.0%)** clearly conveyed

Use case: precision matters more than recall. Acting on misleading content is costly.

### Strict — "≥70% green"

- **71** segments trusted
- **70** useful captured (7.6% of all NIV-Y+P)
- **1** false positives (0.2% FPR)
- **63 (88.7%)** clearly conveyed — almost everything trusted is high-quality

Use case: high-stakes downstream decisions. Acceptable to miss most useful content if false positives are eliminated.

---

## Why this matters

Under the OLD rule, the same green-fraction trust criterion was a substantially weaker signal. Side-by-side at comparable recall:

- **New rule, ≥30% green threshold** → 65.2% recall, 28 FPs (5.6% FPR)
- **Old rule, ≥50% green threshold** → 64.5% recall, 33 FPs (6.6% FPR)

At ~65% recall the old rule's false-positive rate was higher, AND the threshold itself was higher (50% green is a much harder bar for users than 30%). The new rule provides the same coverage with stricter trust at a lower cosmetic threshold.

## The structural ceiling

Even at the permissive 30% threshold, **322** useful segments (34.8% of all NIV-Y+P) have less than 30% green words and would be missed. These are segments where the model produced something useful but not via clean visual signal — agreeable beams, low individual conf. The band system fundamentally can't reach them. They'd need a different signal (post-hoc LLM rerank, semantic-coherence check, topic-conditional rescore) to surface.

This is the operational ceiling on confidence-band trust calibration alone, on this LLM and decoder.

---

## Replicate

```bash
python3 docs/_research-tools/generators/analyze_client_trust_calibration.py \
  --per-segment english_full_nbest_eval/safety_analysis/per_segment_safety.csv \
  --out-dir english_full_nbest_eval/client_trust/
```

Re-run when: the underlying model changes, the band rule thresholds change, or NIV definitions change.