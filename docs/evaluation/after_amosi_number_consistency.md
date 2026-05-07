# Argos VSP `AFTER_AMOSI_May2026.pptx` — Number Consistency Report

_Generated 2026-05-06 from `/home/ubuntu/presentation_materials_20260224/Argos_VSP_AFTER_AMOSI_May2026.pptx` (89 slides) against `after_amosi_audit.json`._


## Totals by Category

| Category | Count | % |
|---|---:|---:|
| OK | 150 | 7.2% |
| OK_TOP1_AS_BASELINE | 15 | 0.7% |
| STALE_LEAK | 20 | 1.0% |
| WRONG | 0 | 0.0% |
| LEGACY_FRAMING | 0 | 0.0% |
| HISTORICAL_CONTRAST | 0 | 0.0% |
| METADATA | 198 | 9.5% |
| OUT_OF_AUDIT | 1710 | 81.7% |
| **TOTAL** | **2093** | 100.0% |

## 11 Specific Number Checks

### Positive checks (must appear)

| Token(s) | Description | Hits | Required | Result |
|---|---|---:|---:|:---:|
| `2.547` | MBR IS mean | 17 | ≥2 | **PASS** |
| `61.92` | MBR NIV-Y+P | 42 | ≥2 | **PASS** |
| `71.08` | Judge Y+P MBR | 46 | ≥2 | **PASS** |
| `65.2` | Trust-gate recall | 48 | ≥1 | **PASS** |
| `5.6%` | Trust-gate FPR | 32 | ≥1 | **PASS** |
| `0.953, 95.3%` | Trust-tier P(green correct) | 2 | ≥1 | **PASS** |
| `23,261, 23261` | Total words audited | 23 | ≥1 | **PASS** |
| `0.00017` | McNemar p MBR Y+P | 97 | ≥1 | **PASS** |
| `291, 324` | MBR tier-5/4 counts | 4 | ≥1 | **PASS** |

### Negative checks (must NOT be active claims)

| Pattern | Description | Hits (potentially active) | Result |
|---|---|---:|:---:|
| `39.9%` | Salvage 39.9% (legacy IS≥3.0) | 0 (of 0 total) | **PASS** |
| `40.1%` | Salvage 40.1% (legacy IS≥3.0) | 0 (of 0 total) | **PASS** |
| `3 dimensions` | PCA framing 3-dim | 0 (of 1 total) | **PASS** |
| `three principal` | PCA framing 3-PC | 0 (of 0 total) | **PASS** |
| `three dimensions` | PCA framing 3-dim | 0 (of 0 total) | **PASS** |
| `IS >= 3.0` | Legacy threshold IS≥3.0 (active claim) | 0 (of 0 total) | **PASS** |
| `IS ≥ 3.0` | Legacy threshold IS≥3.0 (active claim) | 0 (of 0 total) | **PASS** |

_All `IS≥3.0` / `IS≥3` token hits in the deck are inside a threshold-sweep contrast (slide 17 notes, slide 36 cell, slide 35) demonstrating that IS≥3.0 was rejected in favor of IS≥3.80 (NIV-Y) or IS≥2.00 (NIV-Y+P). They are HISTORICAL_CONTRAST, not active claims._


## STALE_LEAK Hits

**20 top-1 numbers cited as active claims where MBR-default should be used.**

| Slide | Location | Token | Audit-key shadowed | Suggested MBR replacement | Surrounding text |
|---:|---|:---:|---|:---:|---|
| 5 | `notes/para[2]` | `20.5%` | `hallucination_pct_top1` | `20.71%` | AFTER VIDEO: System + human reader outperforms expert lip readers. Expert lip readers achieve ~45-52% word accuracy on unconstrained speech (Auer & Bernstein 2007). Model + context-aware human: estima |
| 10 | `shape[4]/para[2]` | `64.1%` | `wer_top1` | `63.84%` | • Result: 64.1% WER — 2.5× worse |
| 10 | `notes/para[0]` | `64.1%` | `wer_top1` | `63.84%` | The paper reports 25.4% WER on LRS3 — a curated TED talks dataset with ideal conditions. Our 1,497 YouTube segments are fundamentally harder: diverse speakers, topics, lighting, angles. Result: 64.1%  |
| 11 | `shape[2]/para[0]` | `64.1%` | `wer_top1` | `63.84%` | 64.1% |
| 11 | `notes/para[0]` | `64.1%` | `wer_top1` | `63.84%` | 1,497 diverse YouTube segments. 64.1% mean WER — 2.5x worse than the paper's 25.4%. Only 25.5% useful by WER (≤34%). And 20.6% are hallucinations — fluent text that's completely fabricated. This is th |
| 18 | `notes/para[0]` | `64.1%` | `wer_top1` | `63.84%` | 30-sample overview: stratified sample from the 1,497-segment dataset. Distribution matches full dataset closely: Y=23%, P=40%, N=37%. Mean WER 61.4% vs 64.1% full. The interesting middle zone (IS 2-4) |
| 35 | `notes/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | Scatter plot of WER vs IS for all 1,497 segments with NIV thresholds. Green region: 42 segments clearly conveyed (IS >= 3.80) but WER > 34%. Amber region: 437 segments with useful meaning (IS >= 2.00) |
| 70 | `shape[7]/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | • 61.6% useful output (IS ≥ 2.00) |
| 70 | `shape[9]/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | The gap is real — but WER dramatically overstates failure. 61.6% useful by IS (Y+P), 64.9% confirmed by Opus-as-a-Judge. |
| 70 | `notes/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | This is the turning point. WER says 25.5% useful. Our Intelligibility Score says 61.6% useful output (NIV Y+P) — 2.4x more. WER correlates with IS but not perfectly — it misses phonetic and semantic p |
| 71 | `shape[13]/para[0]` | `2.52` | `is_mean_top1` | `2.547` | Combined target: IS 3.3–3.7 (~80–85% useful Y+P). Phase deltas sum to +0.98 from 2.52 baseline. Gains are multiplicative (ICLR 2024 scaling law). |
| 72 | `shape[6]/para[0]` | `2.52` | `is_mean_top1` | `2.547` | IS 2.52  •  61.6% useful (Y+P) |
| 72 | `shape[6]/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | IS 2.52  •  61.6% useful (Y+P) |
| 72 | `shape[19]/para[0]` | `2.52` | `is_mean_top1` | `2.547` | Conversion: ~0.033 IS per pp WER (empirical: 2.52@64% → ~3.81@25.4%). |
| 72 | `notes/para[1]` | `2.52` | `is_mean_top1` | `2.547` | Current IS 2.52 (61.6% useful, NIV Y+P). |
| 72 | `notes/para[1]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | Current IS 2.52 (61.6% useful, NIV Y+P). |
| 72 | `notes/para[5]` | `2.52` | `is_mean_top1` | `2.547` | Conversion: ~0.033 IS per pp WER (2.52@64% to ~3.81@25.4% paper). |
| 79 | `shape[5]/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | Rigorous assessment: 2.5× WER gap on 1,497 segments. Novel IS metric reveals 61.6% useful output (NIV Y+P), confirmed by LLM judge at 64.9%. Full failure analysis with improvement suggestions. |
| 85 | `shape[3]/cell[3,1]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | 61.6% |
| 85 | `notes/para[0]` | `61.6%` | `niv_yp_pct_top1` | `61.92%` | 165 of 900 metric-failed segments are recoverable by the LLM heuristic. Useful output rate is 61.6% (NIV Y+P). 6 recovery categories (overlap, not disjoint). 58% have moderate WER (50-70%). |

## WRONG Hits (not matching either top-1 or MBR)

_None._  Every numeric token traces back to a known top-1 or MBR value, an outside-of-audit reference (paper/decode-independent), a legitimate cell-internal computation, metadata, or a coincidental match (PCA variance, cross-tab cell).


## Body vs Speaker-Notes Consistency

Cross-checked all 89 slides for percent values that appear in both body and notes within 0.5–5.0pp difference and matching integer family. Result: **no genuine contradictions.**


One soft flag (slide 54): body table cell `60.5%` (Salvage yellow P-correct) appears alongside body bullet `<60% reliable` (Strip-tier heuristic). These refer to different metrics, not a contradiction.


## Anchored-to-Old-Baseline Review — Slides 70, 71, 72

Per audit instructions, the slide titles ('Starting from 61.6%, Not 25%' / 'Five Phases — From IS 2.5 to Target IS 3.3–3.7' / 'IS Improvement Roadmap — From 2.5 to 3.5') are intentionally loose framing — they are catchphrases, not precise claims. The audit tolerates them. **However the BODY content of slides 70 and 72 still claims 61.6% and 2.52 as the active baseline**, where MBR-default 61.92% / 2.547 should appear. See the STALE_LEAK table above for exact rows.


**Slide 70 body:** `61.6% useful output (IS ≥ 2.00)` (shape[7]) and `61.6% useful by IS (Y+P)` (shape[9]) — **STALE_LEAK** (top-1 niv_yp_pct).


**Slide 71 body:** `Phase deltas sum to +0.98 from 2.52 baseline` (shape[13]) — **STALE_LEAK** (top-1 is_mean). The phase-target IS 3.3–3.7 numbers are still relative deltas, but the explicit anchor to 2.52 should be 2.547 (or labeled 'top-1 baseline').


**Slide 72 body:** `IS 2.52 • 61.6% useful (Y+P)` is the 'Current' cell — **STALE_LEAK** in two tokens. Conversion footer `2.52@64% → ~3.81@25.4%` also uses top-1.


## Citation-Comment Spot-Check (`# audit:KEY` in source code)

| File | `audit:` count | Status |
|---|---:|:---:|
| `presentation/slides_evaluation.py` | 28 | OK (covers per-word bands, trust gate, judge v3, McNemar, intra-rater) |
| `presentation/slides_research.py` | 33 | OK (covers MBR IS, NIV-Y/Y+P, judge baseline, McNemar, trust-gate ≥30%, tier counts) |
| `presentation/slides_opening.py` | **0** | **MISSING** — hard-codes `64.1%`, `2.5×`, `61.6%`, `5.6%`, `20.5%` without citation |
| `presentation/slides_future.py` | **0** | **MISSING** — hard-codes `61.6%`, `2.52`, `2.4×`, phase-delta IS values without citation |
| `presentation/slides_engineering.py` | 0 | Acceptable — pipeline diagrams, not metric-driven |

**Finding**: `slides_opening.py` and `slides_future.py` rely on inline literals with no traceability back to `after_amosi_audit.json`. Adding `# audit:KEY` comments next to each metric assignment in these two files would close the gap and make future audits trivial.


## Bottom Line

- Total numeric tokens scanned: **2093**

- OK + OK_TOP1_AS_BASELINE + METADATA + OUT_OF_AUDIT: **2073 / 2093** (99.0%)

- STALE_LEAK: **20** (top-1 numbers cited as active claims)

- WRONG: **0**

- LEGACY_FRAMING (active deprecated framing): **0**

- 11 positive checks: **PASS** (see table above)

- Body-vs-notes contradictions: **0 genuine**

- Citation comments: 2 of 5 slide modules have audit citations; `slides_opening.py` and `slides_future.py` need them.
