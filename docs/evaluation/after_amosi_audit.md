# Argos VSP Numbers Audit — Top-1 vs MBR-Default (May 2026)

_Date_: 2026-05-06  
_Purpose_: Single source-of-truth comparison of every published numeric statistic under the March 2026 top-1 baseline vs the May 2 2026 MBR-aggregated production default.

## Headline summary table (Top-1 baseline vs MBR default)

| Statistic | Top-1 Baseline | MBR Default | Δ | Source |
|---|---|---|---|---|
| Mean IS | 2.532 | 2.547 | +0.014 | aggregated_is.json |
| Median IS | 2.559 | 2.600 | +0.041 | aggregated_is.json |
| Std IS | 1.380 | 1.377 | -0.003 | aggregated_is.json |
| Mean WER % | 64.05 | 63.84 | -0.22 pp | aggregated_is.json |
| NIV-Y count (IS≥3.80) | 359 | 358 | -1 | aggregated_is.json |
| NIV-Y pct | 23.98% | 23.91% | -0.07 pp | aggregated_is.json |
| NIV-Y+P count (IS≥2.00) | 923 | 927 | +4 | aggregated_is.json |
| NIV-Y+P pct | 61.66% | 61.92% | +0.27 pp | aggregated_is.json |
| Legacy IS≥3.0 captured % | 40.15 | 41.08 | +0.94 pp | aggregated_is.json |
| Tier 5 (≥4.0) count | 288 | 291 | +3 | aggregated_is.json |
| Tier 4 (3.0-3.99) count | 313 | 324 | +11 | aggregated_is.json |
| Tier 3 (2.0-2.99) count | 322 | 312 | -10 | aggregated_is.json |
| Tier 2 (1.0-1.99) count | 337 | 329 | -8 | aggregated_is.json |
| Tier 1 (<1.0) count | 237 | 241 | +4 | aggregated_is.json |
| Hallucination rate (WER≥100%) | 307/1497 (20.51%) | 310/1497 (20.71%) | +0.20 pp | report_v2/report.csv |
| κ vs Opus (NIV-Y, n=1497) | 0.707 | 0.693 | -0.013 | computed: judge × IS |
| κ vs Opus (NIV-Y+P, n=1497) | 0.816 | 0.796 | -0.020 | computed: judge × IS |
| Judge Y % (v3) | 13.09% | 13.89% | +0.80 pp | llm_judge_nbest/summary.json |
| Judge Y+P % (v3) | 68.40% | 71.08% | +2.67 pp | llm_judge_nbest/summary.json |
| Effective capture (NIV-Y+P + LLM-salvage) % | 61.92% | 62.26% | +0.33 pp | computed |
| Effective capture (legacy IS≥3.0 + salvage) % | 51.04% | 51.50% | +0.47 pp | computed |

## Numbers that shifted significantly (top-1 → MBR)

- **Mean IS**: 2.532 → 2.547 (Δ=+0.014). Small but tracks judge.
- **Mean WER**: 64.05% → 63.84% (Δ=-0.22pp).
- **NIV-Y count**: 359 → 358 (Δ=-1). Effectively unchanged.
- **NIV-Y+P count**: 923 → 927 (Δ=+4).
- **Tier 5 (Excellent ≥4.0)**: 288 → 291 (Δ=+3).
- **Tier 4 (Good 3.0-3.99)**: 313 → 324 (Δ=+11). MBR lifts segs from tier 3 into tier 4.
- **Judge Y rate**: 13.09% → 13.89% (Δ=+0.80pp, n.s.).
- **Judge Y+P rate**: 68.40% → 71.08% (Δ=+2.67pp, p=0.0002 paired McNemar).
- **Hallucination rate (WER≥100%)**: 20.51% → 20.71% (Δ=+0.20pp).

## Numbers confirmed unchanged

- **Cross-config r=0.925** — applies to top-1 across 16 decode-parameter configs; n-best aggregation was not part of the 16. Number is still valid as an IS-stability claim, but it does NOT validate MBR specifically.
- **Expert heuristic r=0.934** — deterministic decision tree, decode-independent. Holds.
- **Opus blind judge gold standard (Y=23.0%, P=41.8%, N=35.1%, Y+P=64.9%)** — judge was run on top-1 only. The new v3 judge run on n-best methods is a separate, smaller-set comparison (with conf injected into prompts).
- **Per-word band rule thresholds** (green=top1_conf≥0.95 ∧ beam_agreement≥0.80; yellow=≥0.65∧≥0.50). MBR uses the same per-word calibrated posteriors as top-1, so thresholds carry over.
- **Trust-gate operating points** (≥30% green: 65.2% recall / 5.6% FPR). Computed on per_segment_safety, which uses top-1 IS labels and top-1 word_confs. Production switch to MBR display does NOT change these numbers because they are computed on top-1's per_segment confidence file.

## Section A — IS distribution under each method

_Source_: `/home/ubuntu/english_full_nbest_eval/aggregated_is.json` (n_segments=1497)

| method | mean IS | median IS | std IS | mean WER % | NIV-Y % (count) | NIV-Y+P % (count) | legacy IS≥3 % | tier 5 | tier 4 | tier 3 | tier 2 | tier 1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hyp_top1 | 2.5322 | 2.5590 | 1.3799 | 64.05 | 23.98% (359) | 61.66% (923) | 40.15 | 288 | 313 | 322 | 337 | 237 |
| hyp_mbr | 2.5467 | 2.6001 | 1.3769 | 63.84 | 23.91% (358) | 61.92% (927) | 41.08 | 291 | 324 | 312 | 329 | 241 |
| hyp_vote_score | 2.5377 | 2.5818 | 1.3818 | 63.67 | 23.98% (359) | 61.86% (926) | 40.48 | 292 | 314 | 320 | 334 | 237 |
| hyp_vote_conf | 2.5450 | 2.5794 | 1.3820 | 62.49 | 24.05% (360) | 62.26% (932) | 40.61 | 299 | 309 | 324 | 326 | 239 |
| hyp_safe | 2.5331 | 2.5591 | 1.3802 | 64.02 | 24.05% (360) | 61.66% (923) | 40.61 | 287 | 321 | 315 | 337 | 237 |
| hyp_xseg_merge | 2.5322 | 2.5590 | 1.3799 | 64.05 | 23.98% (359) | 61.66% (923) | 40.15 | 288 | 313 | 322 | 337 | 237 |

## Section B — WER, hallucination, NEA F1 / WWER per method

_WER source_: `/home/ubuntu/english_full_nbest_eval/report_v2/aggregator_method_wer.json`. _Hallucination source_: `/home/ubuntu/english_full_nbest_eval/report_v2/report.csv`.

### Mean WER per method (full 1,497 segments)
| method | mean WER % |
|---|---|
| top1 | 64.0548 |
| hyp_mbr | 63.8391 |
| hyp_vote_score | 63.6693 |
| hyp_vote_conf | 62.4942 |
| hyp_safe | 64.0209 |
| hyp_xseg_merge | 64.0548 |

### Hallucination rate (WER ≥ 100%)
| method | count | total | pct |
|---|---|---|---|
| top1 | 307 | 1497 | 20.51% |
| hyp_mbr | 310 | 1497 | 20.71% |
| hyp_vote_score | 303 | 1497 | 20.24% |
| hyp_vote_conf | 285 | 1497 | 19.04% |
| hyp_safe | 307 | 1497 | 20.51% |
| hyp_xseg_merge | 307 | 1497 | 20.51% |

### WWER & NEA F1 (top-1 only)

- top1 mean WWER: **60.51%**
- top1 mean NEA F1: **38.94%**
- _Note_: WWER and NEA F1 are computed for top-1 only in nbest report.csv; no per-method WWER/NEA columns exist.

## Section C — κ vs Opus blind judge under each method

_Sources_: `/home/ubuntu/docs/evaluation/llm_judge/llm_judge_results.csv`, `/home/ubuntu/english_full_nbest_eval/aggregated_is.json`
_n paired segments_: 1497

Computed kappa: 2×2 contingency between Opus blind verdict (Y vs not-Y for NIV-Y, Y+P vs N for NIV-Y+P) and IS-NIV bucket.

| method | n paired | κ (NIV-Y, IS≥3.80) | both Y / IS-only Y / judge-only Y / both N | κ (NIV-Y+P, IS≥2.00) | both YP / IS-only YP / judge-only YP / both N |
|---|---|---|---|---|---|
| hyp_top1 | 1497 | 0.707 | 273/86/72/1066 | 0.816 | 883/40/88/486 |
| hyp_mbr | 1497 | 0.693 | 269/89/76/1063 | 0.796 | 878/49/93/477 |
| hyp_vote_score | 1497 | 0.684 | 267/92/78/1060 | 0.806 | 881/45/90/481 |
| hyp_vote_conf | 1497 | 0.672 | 264/96/81/1056 | 0.803 | 883/49/88/477 |
| hyp_safe | 1497 | 0.698 | 271/89/74/1063 | 0.811 | 881/42/90/484 |

MEMORY/March values: top-1 IS gave κ_Y=0.690, κ_YP=0.818 vs Opus blind. Computed values above use the same Opus blind judge — any drift indicates verdict noise or method-induced IS shift.

## Section D — Per-word confidence (joint conf+agreement band rule)

_Sources_: overall=`/home/ubuntu/english_full_nbest_eval/safety_analysis/per_word_safety.csv`, by_tier=`/home/ubuntu/english_full_nbest_eval/safety_analysis/per_word_by_tier.csv`, by_pos=`/home/ubuntu/english_full_nbest_eval/safety_analysis/per_word_by_pos.csv`, stratified=`/home/ubuntu/english_full_nbest_eval/trust_diagnostic/per_word_diagnostic.csv`

### Overall (new joint rule, total words = 23261)
| band | count | P(correct) |
|---|---|---|
| green | 7591 | 0.8982 |
| yellow | 6571 | 0.5896 |
| red | 9099 | 0.2167 |

### Overall (legacy conf-only rule, total words = 23261) — for comparison
| band | count | P(correct) |
|---|---|---|
| green | 11309 | 0.8062 |
| yellow | 7470 | 0.3827 |
| red | 4482 | 0.1535 |

### By segment tier (Trust ≥0.82 / Salvage 0.65-0.82 / Strip <0.65)

**Trust** (rule = new joint conf+agreement)
| band | n | P(correct) |
|---|---|---|
| green | 3923 | 0.9531 |
| yellow | 1719 | 0.7615 |
| red | 951 | 0.4196 |

**Salvage** (rule = new joint conf+agreement)
| band | n | P(correct) |
|---|---|---|
| green | 3091 | 0.8913 |
| yellow | 3241 | 0.6051 |
| red | 3442 | 0.2775 |

**Strip** (rule = new joint conf+agreement)
| band | n | P(correct) |
|---|---|---|
| green | 577 | 0.5615 |
| yellow | 1611 | 0.3749 |
| red | 4706 | 0.1313 |

### By POS class (function / content / number)

**function** (rule = new joint)
| band | n | P(correct) |
|---|---|---|
| green | 4316 | 0.8941 |
| yellow | 3943 | 0.6051 |
| red | 4500 | 0.2536 |

**content** (rule = new joint)
| band | n | P(correct) |
|---|---|---|
| green | 3272 | 0.9040 |
| yellow | 2517 | 0.5646 |
| red | 4483 | 0.1827 |

**number** (rule = new joint)
| band | n | P(correct) |
|---|---|---|
| yellow | 100 | 0.6700 |
| red | 96 | 0.1250 |

### Stratified P(band correct) by segment mean_prob
(Joint conf+agreement bands; recomputed from `trust_diagnostic/per_word_diagnostic.csv`.)

_NOTE_: trust_diagnostic/per_word_diagnostic.csv is filtered to seg_mean_conf >= 0.65; very_low/low/mid_low bins NOT recomputable here. MEMORY values 92.8/83.8/69.6/41.3/21.8/18.2 are from the legacy CONF-ONLY rule on the B3 word_confidence sidecar (top-1), not the joint conf+agreement rule under MBR.

| seg_mean_conf bin | green n | green P(correct) | yellow n | yellow P(correct) | red n | red P(correct) |
|---|---|---|---|---|---|---|
| very_high (0.85-1.01) | 2899 | 0.9638 | 1100 | 0.7855 | 530 | 0.4528 |
| high (0.75-0.85) | 2760 | 0.9170 | 1979 | 0.6781 | 1596 | 0.3415 |
| mid (0.65-0.75) | 1392 | 0.8606 | 1844 | 0.5613 | 2267 | 0.2510 |

## Section E — Trust-gate operating points

_Source_: `/home/ubuntu/english_full_nbest_eval/client_trust/client_trust_calibration.csv`

### New rule (joint conf+agreement) — primary table
| T (green-frac ≥) | n trusted | TPs | FPs | recall | precision | FPR | clearly conveyed in trust |
|---|---|---|---|---|---|---|---|
| 0.10 | 1041 | 853 | 188 | 92.3% | 81.9% | 37.38% | 357 (34.3%) |
| 0.20 | 818 | 747 | 71 | 80.8% | 91.3% | 14.12% | 349 (42.7%) |
| 0.30 | 630 | 602 | 28 | 65.2% | 95.6% | 5.57% | 331 (52.5%) |
| 0.40 | 470 | 458 | 12 | 49.6% | 97.4% | 2.39% | 292 (62.1%) |
| 0.50 | 321 | 312 | 9 | 33.8% | 97.2% | 1.79% | 231 (72.0%) |
| 0.60 | 180 | 178 | 2 | 19.3% | 98.9% | 0.40% | 142 (78.9%) |
| 0.70 | 71 | 70 | 1 | 7.6% | 98.6% | 0.20% | 63 (88.7%) |
| 0.80 | 28 | 28 | 0 | 3.0% | 100.0% | 0.00% | 28 (100.0%) |
| 0.90 | 5 | 5 | 0 | 0.5% | 100.0% | 0.00% | 5 (100.0%) |

**Three named operating points (from CLIENT_TRUST_CALIBRATION.md):**
- Permissive ≥30% green: 630 trusted, 65.2% recall, 5.6% FPR (default).
- Moderate ≥50% green: 321 trusted, 33.8% recall, 1.8% FPR.
- Strict ≥70% green: 71 trusted, 7.6% recall, 0.2% FPR.

## Section F — LLM Judge n-best v3 (Opus 4.7, 5,988 verdicts)

_Source_: `/home/ubuntu/docs/evaluation/llm_judge_nbest/summary.json`
n_segments=1497, total verdicts=5988, methods judged: baseline, hyp_mbr, hyp_vote_score, hyp_vote_conf

### Y / P / N counts and rates per method
| method | Y | P | N | Y rate | Y+P rate |
|---|---|---|---|---|---|
| baseline | 196 | 828 | 473 | 13.09% | 68.40% |
| hyp_mbr | 208 | 856 | 433 | 13.89% | 71.08% |
| hyp_vote_score | 209 | 828 | 460 | 13.96% | 69.27% |
| hyp_vote_conf | 187 | 868 | 442 | 12.49% | 70.47% |

### Intra-rater reliability (30 duplicates per method)
| method | exact agreement | lenient (Y+P vs N) |
|---|---|---|
| baseline | 83.3% | 96.7% |
| hyp_mbr | 86.7% | 93.3% |
| hyp_vote_score | 76.7% | 86.7% |
| hyp_vote_conf | 80.0% | 90.0% |

### Paired McNemar tests vs baseline
| method | Y meth-only | Y base-only | Y χ² | Y p | Y+P meth-only | Y+P base-only | Y+P χ² | Y+P p |
|---|---|---|---|---|---|---|---|---|
| hyp_mbr | 59 | 47 | 1.14 | 0.2853 | 74 | 34 | 14.08 | 0.00017 |
| hyp_vote_score | 59 | 46 | 1.37 | 0.2416 | 41 | 28 | 2.09 | 0.14856 |
| hyp_vote_conf | 60 | 69 | 0.50 | 0.4812 | 65 | 34 | 9.09 | 0.00257 |

**Drift note**: Identical-text drift v3: 12.6%/10.4%/14.2% per method (mbr/vote_score/vote_conf), down from v1's 27% — see llm_judge_nbest_analysis.md.

## Section G — Salvage rates per method

_Sources_: `/home/ubuntu/docs/evaluation/llm_judge/llm_judge_results.csv`, `/home/ubuntu/english_full_nbest_eval/aggregated_is.json`

_Heuristic note_: llm_context_prob is computed once on the top-1 hypothesis (decoded from llm_judge_results.csv). Re-running it on MBR text would give slightly different per-segment values; the current numbers are MBR-IS gate × top-1-prob heuristic.

| method | n total | NIV-Y % (n) | NIV-Y+P % (n) | legacy IS≥3 % (n) | salvage_legacy (IS<3 ∧ prob≥0.5) (n, %) | effective capture legacy % | salvage NIV (IS<2 ∧ prob≥0.5) (n, %) | effective capture NIV-Y+P % |
|---|---|---|---|---|---|---|---|---|
| hyp_top1 | 1497 | 23.98% (359) | 61.66% (923) | 40.15% (601) | 163 (10.89%) | 51.04% | 4 (0.27%) | 61.92% |
| hyp_mbr | 1497 | 23.91% (358) | 61.92% (927) | 41.08% (615) | 156 (10.42%) | 51.50% | 5 (0.33%) | 62.26% |
| hyp_vote_score | 1497 | 23.98% (359) | 61.86% (926) | 40.48% (606) | 160 (10.69%) | 51.17% | 4 (0.27%) | 62.12% |
| hyp_vote_conf | 1497 | 24.05% (360) | 62.26% (932) | 40.61% (608) | 161 (10.75%) | 51.37% | 4 (0.27%) | 62.53% |
| hyp_safe | 1497 | 24.05% (360) | 61.66% (923) | 40.61% (608) | 156 (10.42%) | 51.04% | 5 (0.33%) | 61.99% |

## Section H — Cross-config validation, expert heuristic, hyperparameter tuning

_Cross-config source_: `/home/ubuntu/docs/evaluation/is_cross_config_validation.md`

- Mean r across 16 configs: **0.925** (std=0.015)
- Datasets: 13 tuning configs (107 segs) + 3 full-decode configs (1497 segs)
- Configs include MBR? **False**
- 16 configs were decode-parameter variants on top-1 only. MBR was promoted later. Number remains valid as a stability claim about the IS metric across decode parameters; it does not include n-best aggregation as a configuration.

_Heuristic source_: `/home/ubuntu/docs/evaluation/llm_salvage/llm_salvage_analysis.md`

- Expert heuristic ↔ IS Pearson r = **0.934**
- Deterministic decision tree, decode-independent — number unchanged under MBR.

_Tuning n-best validation source_: `/home/ubuntu/tuning_results/exp_nbest_validation/aggregated_is.json`
_n_segments_: 107 (107-segment tuning subset, n-best aggregation re-run)

| method | mean IS | mean WER % | NIV-Y % | NIV-Y+P % |
|---|---|---|---|---|
| hyp_top1 | 2.6659 | 59.35 | 23.36% | 70.09% |
| hyp_mbr | 2.6843 | 58.57 | 24.30% | 70.09% |
| hyp_vote_score | 2.6696 | 58.89 | 23.36% | 69.16% |
| hyp_vote_conf | 2.6948 | 57.20 | 24.30% | 71.03% |
| hyp_safe | 2.6578 | 59.36 | 23.36% | 69.16% |
| hyp_xseg_merge | 2.6659 | 59.35 | 23.36% | 70.09% |

## Section I — Human-IS Path B estimates (pre-study)

_Source_: `/home/ubuntu/docs/evaluation/human_is_estimation.md`

**Formula provenance**: Path B: bin model 1,497 segments by WER, take per-bin component means, plug literature WER + literature-derived component shifts (semantic, phonetic, NEA F1, length ratio) into the same IS formula. Components from intelligibility_scores.csv cols 6-19. Pre-study estimates, not measurements; needs Path A pilot to confirm. Reproducible Python snippet in §4 of human_is_estimation.md.

| Population | low | mid | high | tier (mid) |
|---|---|---|---|---|
| lay_no_ctx | 0.63 | 0.92 | 1.14 | Failed |
| deaf_no_ctx | 2.33 | 2.74 | 3.07 | Fair |
| expert_no_ctx | 2.6 | 3.03 | 3.33 | Fair |
| lay_plus_ctx_plus_model | 3.36 | 3.83 | 4.19 | Good |
| model_alone_measured | — | 2.52 | — | _measured_ |

**LR isolation experiment**: LR isolation experiment: human-style LR (skipping uncertain words) costs +0.41 IS for lay → +0.06 for lay+ctx+model — penalty shrinks with proficiency.
- Lay: +0.41 • Deaf: +0.21 • Expert: +0.15 • Lay+ctx: +0.06

## Anomalies, data gaps, and caveats

- **per_segment_safety.csv has 1,427 rows, not 1,497.** 70 segments with empty hypothesis are excluded. Trust-gate calibration uses 1,427 as the denominator (NIV-Y=361/25.3%, NIV-Y+P=924/64.8%). aggregated_is.json keeps all 1,497 (treats empty as IS=0; NIV-Y=346/23.1%, NIV-Y+P=922/61.6%). Use 1,497 as the canonical denominator for IS distribution; 1,427 only inside band-trust calibration.
- **Per-method WWER and NEA F1 are NOT recomputed.** report_v2/report.csv carries WWER/NEA only for top-1 (no `wwer_hyp_*_%` columns). To get per-method WWER/NEA we would need to rerun the metric module on the per-method hypothesis text. This is a real gap if any deck slide quotes per-method WWER/NEA.
- **llm_context_prob is bound to top-1 hypothesis text.** Salvage counts under MBR-IS use MBR's IS gate but top-1's heuristic prob. The heuristic is decode-independent in design (15-rule decision tree on text features), but per-segment values would shift slightly if recomputed on MBR text. The 'effective capture' rows in Section G are conservatively MBR-IS × top1-prob.
- **Stratified P(green correct) by seg_mean_prob bin** for very_low (<0.40), low (0.40-0.55), mid_low (0.55-0.65) bins is NOT recomputable from `trust_diagnostic/per_word_diagnostic.csv` because that file is filtered to seg_mean_conf≥0.65. The MEMORY values 92.8/83.8/69.6/41.3/21.8/18.2 come from a different (B3 sidecar) source under the legacy CONF-ONLY rule. Section D recomputes only the three available bins under the joint rule.
- **Cross-config r=0.925 does NOT include n-best aggregation** as a 'config'. The 16 configs were all top-1 decode-parameter variants. Re-running cross-config validation including hyp_mbr would be a useful follow-up.
- **Tuning n-best validation (107 segs)** confirms the same direction as the full set: hyp_vote_conf wins on WER (-2.15pp) and ties on IS. hyp_mbr edges baseline on IS (+0.018) and NIV-Y count (+1).
- **Identical-text drift (12.6/10.4/14.2% per method)** is not in summary.json — only in the analysis md. Cited verbatim, not recomputed.
- **κ values in Section C are computed against the v3 _Opus blind judge run on top-1 hypothesis_** (the only gold standard we have). For each n-best method we compare its IS-NIV labels against the same set of judge labels — so κ shifts reflect IS shifts under that method, not judge re-evaluation.

---
_Generated by `scripts/audit_after_amosi_numbers.py`._
