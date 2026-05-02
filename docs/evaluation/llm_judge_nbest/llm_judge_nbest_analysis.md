# n-best LLM-as-a-Judge — analysis (v3, dual-conf)

**v3 run**: 2026-05-02. Judge: Claude Opus 4.7 (in-conversation).
**Scope**: 1,497 segments × 4 aggregation methods = 5,988 verdicts. 60 batches, 0 missing.
**Prompt**: `NNN|ref|word1[.NN] ...|baseline_conf|method_conf` — per-word method conf inline, plus two trailing sentence-level conf columns. `baseline_conf` is identical across all 4 methods on a given segment (segment-level signal); `method_conf` varies per method.

## TL;DR

n-best aggregation **modestly improves the broader Y+P operating point** over the 1-best baseline, with no Y-level cost. Best method on the judge metric is `hyp_mbr`; `hyp_vote_conf` is comparable and additionally wins on WER.

| metric | baseline | hyp_mbr | hyp_vote_score | hyp_vote_conf | who wins |
|---|---|---|---|---|---|
| **WER** | 64.05 % | 63.84 % | 63.67 % | **62.49 %** | hyp_vote_conf (−1.56 pp) |
| **mean IS** | 2.532 | 2.547 | 2.538 | 2.545 | tied (within 0.015) |
| **IS-NIV-Y %** | 23.98 | 23.91 | 23.98 | 24.05 | tied (paired p ≈ 1.0) |
| **IS-NIV-Y+P %** | 61.66 | 61.92 | 61.86 | 62.26 | tied (paired p ≈ 1.0) |
| **judge NIV-Y %** (v3) | 13.1 | 13.9 | 14.0 | 12.5 | tied (none significant) |
| **judge NIV-Y+P %** (v3) | 68.4 | **71.1** | 69.3 | 70.5 | hyp_mbr +2.7 pp (p=0.0002) |

**Recommendation**: ship `hyp_mbr` or `hyp_vote_conf` as the default. MBR is the stronger Y+P win on the judge; vote_conf is comparable on Y+P and wins on WER. Both are defensible upgrades; baseline is a defensible hold.

## Paired McNemar tests (v3, all segments)

McNemar continuity-corrected, two-sided, paired by `utt_id`.

**Y verdict (strict — meaning fully conveyed):**

| method vs baseline | method-only Y | baseline-only Y | chi² | p |
|---|---|---|---|---|
| hyp_mbr | 59 | 47 | 1.14 | 0.29 (n.s.) |
| hyp_vote_score | 59 | 46 | 1.37 | 0.24 (n.s.) |
| hyp_vote_conf | 60 | 69 | 0.50 | 0.48 (n.s.) |

**Y+P verdict (broader — any meaning conveyed):**

| method vs baseline | method-only Y+P | baseline-only Y+P | chi² | p |
|---|---|---|---|---|
| **hyp_mbr** | **74** | **34** | **14.08** | **0.0002** |
| hyp_vote_score | 41 | 28 | 2.09 | 0.15 (n.s.) |
| **hyp_vote_conf** | **65** | **34** | **9.09** | **0.0026** |

`hyp_mbr` is the cleanest win: +40 net Y+P verdicts vs baseline. `hyp_vote_conf` is +31. Neither comes at a Y cost.

## Confusion matrices vs baseline (v3)

```
hyp_mbr vs baseline                hyp_vote_conf vs baseline
                Y    P    N                        Y    P    N
  base = Y    149   47    0          base = Y    127   69    0
  base = P     58  736   34          base = P     60  734   34
  base = N      1   73  399          base = N      0   65  408
```

`hyp_mbr` recovers **73 baseline-N → P** (rescues nearly-failed segments) at the cost of **47 baseline-Y → P** (downgrades). Net Y+P: +40.

`hyp_vote_conf` recovers **65 baseline-N → P** at the cost of **69 baseline-Y → P**. Net Y+P: +31. (Note that vote_conf has a noticeably larger Y → P leak — the function-word edits we documented earlier — but it's offset by gains at the bottom of the distribution.)

## Restricted to text-differing segments (cleaner test)

Removes identical-text segments where verdict differences could only come from prompt-level conf cues:

| method vs baseline | n (text differs) | meth-only Y+P | base-only Y+P | chi² | p |
|---|---|---|---|---|---|
| hyp_mbr | 580 | 37 | 15 | 8.48 | 0.0036 |
| hyp_vote_score | 480 | 16 | 14 | 0.03 | 0.86 (n.s.) |
| hyp_vote_conf | 940 | 49 | 26 | 6.45 | 0.011 |

**MBR and vote_conf remain significantly better than baseline on Y+P even after removing the text-identical confound subset.** This is the most robust read of the v3 evidence.

## Identical-text confound (still partial in v3, much reduced from v1)

In **494/1,497 segments (33 %)** all four methods produced byte-identical text. v3's dual-conf design lowered verdict drift on these segments from v1's **27 %** to **23 %**. The shared `baseline_conf` anchor helps but doesn't eliminate drift, because `method_conf` and per-word conf still differ across methods.

```
hyp_mbr        — text identical to baseline: 917 segments,  12.6 % verdict drift
hyp_vote_score — text identical to baseline: 1017 segments, 10.4 % verdict drift
hyp_vote_conf  — text identical to baseline:  557 segments, 14.2 % verdict drift
```

The drift is approximately **balanced** in v3 (e.g., for vote_conf on identical text: 28 Y→P vs 27 P→Y, 16 N→P vs 8 P→N). This is consistent with intra-rater noise rather than directional bias — different from v1, where the drift was asymmetric and accounted for ~25 % of the spurious Y deficit.

## Intra-rater reliability (30 duplicate pairs per method)

| method | exact agreement | lenient (Y+P vs N) |
|---|---|---|
| baseline | 83.3 % | 96.7 % |
| hyp_mbr | 86.7 % | 93.3 % |
| hyp_vote_score | 76.7 % | 86.7 % |
| hyp_vote_conf | 80.0 % | 90.0 % |

Comparable to the prior `llm_judge/` gold standard (86.7 % baseline). vote_score is somewhat noisier on duplicates; vote_conf is back to a normal range (vs v1's 76.7 %).

## v1 vs v3 — what changed and why it matters

| comparison (Y+P) | v1 (method_conf only) | v3 (baseline + method_conf) |
|---|---|---|
| hyp_mbr | n.s. (p=0.07, slight loss) | **+40 wins, p=0.0002** |
| hyp_vote_score | loss (p=0.022) | n.s. (p=0.15) |
| hyp_vote_conf | **loss (p=0.0024)** | **+31 wins, p=0.0026** |

**v3 isn't just less biased than v1 — it gives the opposite sign for vote_conf on Y+P.** The single-method-conf prompt in v1 was punishing the n-best methods (their `method_conf` was lower than baseline's `sentence_confidence` because vote agreement scores live in [0.4, 0.8) regardless of segment quality). The dual-conf prompt fixes this by exposing the high baseline_conf alongside the lower method_conf, letting the judge see "this segment is actually high-quality even though the method's own conf reads low" — which it apparently couldn't recover from `method_conf` alone.

This is itself a finding about prompt design for in-conversation LLM-as-judge with confidence-injected prompts: **showing only the model's own confidence score for the variant under test biases the judge against that variant; showing baseline confidence alongside removes the bias.**

## Combined cross-metric picture

| metric | hyp_mbr vs baseline | hyp_vote_score vs baseline | hyp_vote_conf vs baseline |
|---|---|---|---|
| WER | −0.21 pp | −0.38 pp | **−1.56 pp** |
| mean IS | +0.015 (tied) | +0.006 (tied) | +0.013 (tied) |
| IS-NIV-Y | tied (p=1.00) | tied (p=0.81) | tied (p=1.00) |
| IS-NIV-Y+P | tied (paired) | tied (paired) | tied (paired) |
| **judge Y+P** | **+2.7 pp (p=0.0002)** | +0.9 pp (n.s.) | **+2.1 pp (p=0.0026)** |
| judge Y | +0.8 pp (n.s.) | +0.9 pp (n.s.) | −0.6 pp (n.s.) |

**The judge sees something IS doesn't.** IS at the segment level says all four methods are equivalent. The judge says MBR and vote_conf are meaningfully better at the broader Y+P operating point. The mechanism — cleanest explanation — is that aggregation rescues marginal segments (baseline-N → method-P transitions), and the IS rubric thresholds (P ≈ tier 3 ≈ IS ≥ 2.0) are slightly above where these rescues land, so IS misses them.

## Files

- `results_long.csv` — one row per (utt_id × method), n=5,988
- `results_wide.csv` — one row per utt_id with all 4 verdicts side-by-side
- `summary.json` — per-method counts, McNemar, intra-rater
- `calibration.csv` — 10 conf-bins × 4 methods → P(Y), P(Y+P)
- `auto_judgments.csv` — 280 empty/short-hyp auto-N rows
- `judgments/batch_<method>_NN_judgments.txt` — raw verdicts (60 files, v3)
- `batches_v1/`, `judgments_v1/` — archived v1 (contaminated, do not use)

Reproduce: `python3 /home/ubuntu/docs/_research-tools/generators/analyze_nbest_judge.py`
