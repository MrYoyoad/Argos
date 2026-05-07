# PPTX Number Audit — Pre-MBR-Default Snapshot

Extraction of every numeric mention in the Argos VSP decks. Status labels (NEEDS_VERIFICATION / LIKELY_HOLD / WRONG_FRAMING_FIX / METADATA / UNCLASSIFIED) are heuristic — the parallel MBR-default audit will confirm exact replacements.

Source CSV: `/home/ubuntu/docs/evaluation/pptx_number_audit.csv`  (extractor: `/home/ubuntu/scripts/extract_pptx_numbers.py`).

## Key findings

1. **No live deprecated framing in the AMOSI March deck or Client v9**. `IS >= 3.0` / `39.9%` / `40.1%` / `597` do not appear as live claims; the two surviving mentions of the `IS >= 3.0` phrase (slide 32 body and notes) are explicitly historical (`Old IS >= 3.0 wrongly rejected this segment.` and `Old IS >= 3.0 threshold is superseded`). The decks have already migrated to NIV-Y / NIV-Y+P language.
2. **PCA framing is correct**. Slide 27 (`Do 6 Signals Actually Measure 6 Things?`) uses `Kaiser retains 2 (87.9%)` as the headline and only mentions PC3 as `adds nuance`. No `3 dimensions` claim to retract.
3. **Client v9 and v10 are byte-identical text**. Different file checksums; extracted text identical. Update v9 once and re-name to v10, or skip v10.
4. **AMOSI deck is the heaviest target**: 84 slides, 1,852 number tokens, 639 in NEEDS_VERIFICATION. ~55 of 84 slides need touching for the new academic deck.
5. **Highest-density slides** (>=15 NEEDS_VERIFICATION numbers each): AMOSI 24 (IS Signals: Word Accuracy & Length), AMOSI 27 (PCA), AMOSI 29 (Model Comparison: IS Profiles), AMOSI 30 (Where WER Lies Most), AMOSI 31 (NIV header), AMOSI 34 (hidden, Where IS and Judge Disagree), AMOSI 36 (Three Numbers That Tell the Real Story), AMOSI 60 (Roadmap, 47 NV), AMOSI 61 (IS Improvement Roadmap, 32 NV), AMOSI 68 (Stronger LLM, 19 NV), AMOSI 70 (hidden, LLM Upgrade, 25 NV), AMOSI 83 (Judge x IS Cross-Tab, 22 NV).

## Per-deck slide & token counts

| Deck | Total slides | Hidden | Slides w/ numbers | Number tokens |
|------|--------------:|-------:|------------------:|--------------:|
| AFTER_AMOSI_Mar2026 | 84 | 10 | 84 | 1852 |
| Client_v9_May2026 | 64 | 0 | 64 | 671 |
| Client_v10_May2026 | 64 | 0 | 64 | 671 |
| Supplementary_LLM_Judge_30 | 8 | 0 | 8 | 90 |

**Note**: `Client_v9_May2026` and `Client_v10_May2026` are textually identical (md5sum on PPTX differs but extracted text is byte-for-byte equal). Treat v10 as a no-op rename of v9 for audit purposes.

## Status breakdown (per deck)

| Deck | NEEDS_VERIFICATION | LIKELY_HOLD | WRONG_FRAMING_FIX | METADATA | UNCLASSIFIED |
|------|-------------------:|------------:|------------------:|---------:|-------------:|
| AFTER_AMOSI_Mar2026 | 639 | 119 | 0 | 242 | 852 |
| Client_v9_May2026 | 133 | 55 | 0 | 259 | 224 |
| Client_v10_May2026 | 133 | 55 | 0 | 259 | 224 |
| Supplementary_LLM_Judge_30 | 30 | 16 | 0 | 20 | 24 |

## Top 30 NEEDS_VERIFICATION numbers by frequency (all decks)

These are the numbers most likely to need rewriting under MBR-default. Filtered to drop bare single-digit tokens (`0`-`9`) which are mostly page numbers, list bullets, or one-off counts that aren't statistics.

| Rank | Number | Total mentions | AMOSI | Client v9 | Likely meaning |
|-----:|--------|---------------:|------:|----------:|----------------|
| 1 | `61.6%` | 26 | 26 | 0 | NIV-Y+P capture (922/1,497) |
| 2 | `2.00` | 23 | 23 | 0 | NIV-Y+P IS threshold (LIKELY_HOLD) |
| 3 | `82%` | 17 | 1 | 8 | IS-vs-judge agreement (band reliability) — verify under MBR |
| 4 | `100%` | 13 | 9 | 2 | WER ceiling marker (often hallucination indicator) |
| 5 | `65%` | 12 | 2 | 5 | Confidence-band reliability tier (verify under MBR) |
| 6 | `25` | 11 | 3 | 4 |  |
| 7 | `4096` | 10 | 6 | 2 | Cluster count / dim — LIKELY_HOLD |
| 8 | `3.1` | 8 | 6 | 1 | Possibly: tier-3 IS reference / version number — verify |
| 9 | `15%` | 8 | 8 | 0 | Various - verify per slide |
| 10 | `3.80` | 8 | 8 | 0 | NIV-Y IS threshold (LIKELY_HOLD) |
| 11 | `5.1` | 8 | 0 | 4 | PCA PC3 variance % (5.1%) — LIKELY_HOLD |
| 12 | `70%` | 7 | 5 | 1 | Confidence threshold figure (verify under MBR) |
| 13 | `75` | 7 | 1 | 3 | Possibly: confidence band reliability target (verify) |
| 14 | `1024` | 7 | 3 | 2 | Cluster count / dim — LIKELY_HOLD |
| 15 | `2.07` | 7 | 4 | 1 | Possibly: per-segment IS sample value — verify |
| 16 | `2.52` | 6 | 6 | 0 | Mean Intelligibility Score |
| 17 | `85%` | 6 | 4 | 1 | Confidence/agreement threshold (verify under MBR) |
| 18 | `2.5` | 6 | 6 | 0 | IS mean (rounded) |
| 19 | `25.4%` | 6 | 6 | 0 | Paper LRS3 WER reference (LIKELY_HOLD) |
| 20 | `25.5%` | 6 | 6 | 0 | WER-based 'capture' under top-1 baseline |
| 21 | `34%` | 6 | 6 | 0 | WER NIV-Y threshold for kappa parity (LIKELY_HOLD) |
| 22 | `3.69` | 6 | 2 | 1 |  |
| 23 | `3.02` | 6 | 2 | 1 |  |
| 24 | `43.3%` | 6 | 2 | 1 |  |
| 25 | `2.67` | 6 | 2 | 1 |  |
| 26 | `1.79` | 6 | 2 | 1 |  |
| 27 | `0.8` | 6 | 4 | 1 |  |
| 28 | `10` | 6 | 2 | 2 |  |
| 29 | `26` | 6 | 0 | 3 |  |
| 30 | `11` | 6 | 0 | 3 |  |

## High-priority slides (>=3 NEEDS_VERIFICATION numbers OR any WRONG_FRAMING_FIX)

Total: **93 slides** across all decks.

| Deck | Slide # | Hidden | Title | NV | WF | LH |
|------|--------:|--------|-------|---:|---:|---:|
| AFTER_AMOSI_Mar2026 | 4 | yes | Executive Summary | 5 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 5 | yes | WER: The Metric That Lies | 4 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 7 | no | What is Visual Speech Processing? | 16 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 9 | no | How It Works: Three Components | 15 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 10 | no | How It Works: Data Flow | 9 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 11 | no | The Benchmark: Paper vs Reality | 7 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 12 | no | The Reality Gap | 10 | 0 | 3 |
| AFTER_AMOSI_Mar2026 | 13 | no | Same WER, Different Effects | 4 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 17 | no | Judge Example 1: Named Entity Swap | 5 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 18 | no | Judge Example 2: Truncated but Core Preserved | 5 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 19 | no | Judge Example 3: Technical Vocabulary Drift | 3 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 20 | no | Judge Example 4: Scientific Vocabulary Lost | 6 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 21 | no | Judge Example 5: Cooking Domain Confusion | 3 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 22 | no | Judge Example 6: Topic Hijack | 4 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 23 | no | Why LLM as a Judge Is Not Enough | 11 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 24 | no | IS Signals: Word Accuracy & Length | 16 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 25 | no | IS Signals: Semantic Similarity | 6 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 27 | no | Do 6 Signals Actually Measure 6 Things? | 17 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 28 | no | IS in Action: Two Real Segments | 13 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 29 | no | Model Comparison: IS Profiles | 16 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 30 | no | The Gap: Where WER Lies Most | 22 | 0 | 7 |
| AFTER_AMOSI_Mar2026 | 31 | no | Intelligibility Score: 61.6% Useful Output | 23 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 32 | no | Two Evaluation Systems, One Framework | 14 | 0 | 17 |
| AFTER_AMOSI_Mar2026 | 33 | no | IS: A Calibrated Surrogate Metric | 10 | 0 | 7 |
| AFTER_AMOSI_Mar2026 | 34 | yes | Where IS and the Judge Disagree | 21 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 35 | yes | Context Exposes Hidden Failures | 9 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 36 | no | Three Numbers That Tell the Real Story | 16 | 0 | 8 |
| AFTER_AMOSI_Mar2026 | 37 | no | Failure Mode Taxonomy | 10 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 38 | no | Failure Mode Taxonomy (1/2): Highest Impact First | 5 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 39 | no | Failure Mode Taxonomy (2/2): Accumulated → Signal Loss | 10 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 40 | no | Failure Modes: Real Examples | 11 | 0 | 3 |
| AFTER_AMOSI_Mar2026 | 42 | yes | When Metrics Disagree: What It Tells Us | 7 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 43 | yes | When Metrics Disagree: More Patterns | 9 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 44 | no | IS: A Calibrated Surrogate for LLM Judgment | 9 | 0 | 5 |
| AFTER_AMOSI_Mar2026 | 45 | no | LLM Salvage: Three Real Recoveries | 11 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 46 | no | LLM Salvage: Domain Context Fills the Gaps | 14 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 47 | no | Curated Examples — Video Gallery | 5 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 48 | no | Demo: OK → Almost There → Hallucination | 6 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 59 | no | Starting from 61.6%, Not 25% | 5 | 0 | 3 |
| AFTER_AMOSI_Mar2026 | 60 | no | Five Phases — From IS 2.5 to Target IS 3.3–3.7 | 47 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 61 | no | IS Improvement Roadmap — From 2.5 to 3.5 | 32 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 65 | no | Data Scaling: The Path to IS 3.5–4.0 | 12 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 66 | no | The Price Tag: What It Costs to Improve | 9 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 67 | no | Fine-Tuning: Limited Data, Limited Gains | 5 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 68 | no | Stronger LLM + Smart Prompts = Force Multiplier | 19 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 69 | no | The LLM Is a Context Engine | 5 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 70 | yes | LLM Upgrade: Why It Matters | 25 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 71 | no | Failure Modes: Impact & What Fixes Them | 5 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 72 | no | Arabic Pipeline: Replication Roadmap | 13 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 74 | no | Arabic Adaptation: What Changes | 3 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 78 | no | A3: IS Component Correlation | 8 | 0 | 7 |
| AFTER_AMOSI_Mar2026 | 79 | no | A4: LLM Salvage — Recoverable Segments | 11 | 0 | 2 |
| AFTER_AMOSI_Mar2026 | 80 | yes | A5: LLM Salvage — Curated Examples | 3 | 0 | 0 |
| AFTER_AMOSI_Mar2026 | 81 | no | A6: Failure Mode Examples | 6 | 0 | 1 |
| AFTER_AMOSI_Mar2026 | 83 | no | A8: LLM Judge × IS Tier Cross-Tabulation | 22 | 0 | 7 |
| AFTER_AMOSI_Mar2026 | 84 | no | A9: Context Evaluation — Transition Details | 6 | 0 | 1 |
| Client_v10_May2026 | 14 | no | Three numbers, in plain English | 3 | 0 | 1 |
| Client_v10_May2026 | 15 | no | Example 1 — Trust: clean speech (Obama) | 6 | 0 | 0 |
| Client_v10_May2026 | 19 | no | Two layers of confidence | 5 | 0 | 0 |
| Client_v10_May2026 | 23 | no | Example 3 — Trust: gallery of six clean outputs | 3 | 0 | 1 |
| Client_v10_May2026 | 24 | no | Example 4 — Salvage: partial recovery (Obama) | 5 | 0 | 0 |
| Client_v10_May2026 | 26 | no | Example 6 — Salvage: technical-vocabulary drift | 3 | 0 | 0 |
| Client_v10_May2026 | 28 | no | Example 8 — Salvage: reading the colors (walk-through) | 8 | 0 | 1 |
| Client_v10_May2026 | 29 | no | Example 9 — Strip: topic invented | 6 | 0 | 0 |
| Client_v10_May2026 | 30 | no | Example 10 — Strip: fluent fabrication caught | 5 | 0 | 1 |
| Client_v10_May2026 | 37 | no | Agrees with the blind evaluator 82% of the time | 8 | 0 | 5 |
| Client_v10_May2026 | 40 | no | How It Works: Data Flow | 9 | 0 | 0 |
| Client_v10_May2026 | 41 | no | What it actually took — four passes, six months | 21 | 0 | 12 |
| Client_v10_May2026 | 46 | no | Optional add-on — pre-filter low-quality clips before decode | 18 | 0 | 5 |
| Client_v10_May2026 | 47 | no | Optional — domain-specific training run on your data | 4 | 0 | 0 |
| Client_v10_May2026 | 50 | no | Thank You | 5 | 0 | 2 |
| Client_v9_May2026 | 14 | no | Three numbers, in plain English | 3 | 0 | 1 |
| Client_v9_May2026 | 15 | no | Example 1 — Trust: clean speech (Obama) | 6 | 0 | 0 |
| Client_v9_May2026 | 19 | no | Two layers of confidence | 5 | 0 | 0 |
| Client_v9_May2026 | 23 | no | Example 3 — Trust: gallery of six clean outputs | 3 | 0 | 1 |
| Client_v9_May2026 | 24 | no | Example 4 — Salvage: partial recovery (Obama) | 5 | 0 | 0 |
| Client_v9_May2026 | 26 | no | Example 6 — Salvage: technical-vocabulary drift | 3 | 0 | 0 |
| Client_v9_May2026 | 28 | no | Example 8 — Salvage: reading the colors (walk-through) | 8 | 0 | 1 |
| Client_v9_May2026 | 29 | no | Example 9 — Strip: topic invented | 6 | 0 | 0 |
| Client_v9_May2026 | 30 | no | Example 10 — Strip: fluent fabrication caught | 5 | 0 | 1 |
| Client_v9_May2026 | 37 | no | Agrees with the blind evaluator 82% of the time | 8 | 0 | 5 |
| Client_v9_May2026 | 40 | no | How It Works: Data Flow | 9 | 0 | 0 |
| Client_v9_May2026 | 41 | no | What it actually took — four passes, six months | 21 | 0 | 12 |
| Client_v9_May2026 | 46 | no | Optional add-on — pre-filter low-quality clips before decode | 18 | 0 | 5 |
| Client_v9_May2026 | 47 | no | Optional — domain-specific training run on your data | 4 | 0 | 0 |
| Client_v9_May2026 | 50 | no | Thank You | 5 | 0 | 2 |
| Supplementary_LLM_Judge_30 | 1 | no | LLM Judge: 30-Sample Deep Dive | 4 | 0 | 4 |
| Supplementary_LLM_Judge_30 | 2 | no | Judge Example 1: Named Entity Swap | 5 | 0 | 1 |
| Supplementary_LLM_Judge_30 | 3 | no | Judge Example 2: Truncated but Core Preserved | 5 | 0 | 0 |
| Supplementary_LLM_Judge_30 | 4 | no | Judge Example 3: Technical Vocabulary Drift | 3 | 0 | 1 |
| Supplementary_LLM_Judge_30 | 5 | no | Judge Example 4: Scientific Vocabulary Lost | 6 | 0 | 0 |
| Supplementary_LLM_Judge_30 | 6 | no | Judge Example 5: Cooking Domain Confusion | 3 | 0 | 0 |
| Supplementary_LLM_Judge_30 | 7 | no | Judge Example 6: Topic Hijack | 4 | 0 | 0 |

## Slides quoting deprecated framing (WRONG_FRAMING_FIX)

These slides need **text rewrites**, not just number swaps.
Replacement guidance:

- `"3 dimensions"` / `"three principal"` -> `"2 PCs"` (PCA: PC1=68.4% signal quality, PC2=19.5% length).
- `"IS >= 3.0"` and `"39.9%"` / `"40.1%"` -> NIV thresholds: IS>=3.80 (NIV-Y, 23.1%) or IS>=2.00 (NIV-Y+P, 61.6%).
- `"captured"` framing -> `"Clearly Conveyed"` (NIV-Y) or `"Useful Output"` (NIV-Y+P).

| Deck | Slide # | Hidden | Title | Trigger snippet |
|------|--------:|--------|-------|-----------------|

## Cross-deck consistency check

For each metric noun (WER / WWER / IS / NIV / Salvage / Hallucination / NEA), list NEEDS_VERIFICATION numbers seen in only one deck. **A non-empty 'only in' column flags a sync gap that the new academic deck must reconcile.**

| Metric | In both | Only in AMOSI March | Only in Client v9 |
|--------|---------|---------------------|-------------------|
| hallucin | — | 0, 0.8, 1, 1.0, 1.3%, 1.79, 100%, 108, 14%, 15, 18.8%, 19, 2, 2.00, 2.8, 20.6%, 25%, 255, 4.2, 44.4%, 45, 5, 52%, 54.3%, 55, 574, 7, 70%, 9.1% | 11, 2.2, 5.10 |
| nea | 1024, 2, 25, 4096, 6, 7, 96 | 0.2, 0.31, 0.43, 0.47, 0.91, 0.999, 024, 1, 1.0, 12.6, 13.9%, 15%, 19.5%, 20%, 3, 3.1, 4.75, 5, 5.1%, 5.4%, 50, 50%, 52, 68.4%, 70%, 8, 80, 9.1%, 93% | — |
| wer | 0, 0%, 0.8, 1, 10, 100%, 2, 2.67, 2.75, 3, 3.02, 3.69, 4, 43.3%, 48.1%, 5, 51.5%, 6, 65%, 70% | 0.041, 0.06, 0.061, 0.1, 0.10, 0.13, 0.15, 0.18, 0.2, 0.25, 0.34, 0.35, 0.36, 0.38, 0.39, 0.40, 0.45, 0.47, 0.48, 0.5, 0.51, 0.52, 0.53, 0.55, 0.58, 0.662, 0.683, 0.689, 0.7, 0.72, 0.779, 0.79, 0.794, 0.80, 0.87, 0.90, 0.91, 0.943, 0.95, 0.971, 1.29, 1.5, 1.56, 1.79, 1.84, 1.98, 1000, 108, 111%, 12, 12%, 15%, 150%, 165, 172%, 18, 18%, 18.2%, 18.7%, 19.5%, 2.00, 2.06, 2.07, 2.13, 2.14, 2.18, 2.32, 2.33, 2.4, 2.5, 2.55, 2.65, 2.86, 2.9, 2.94, 20.6%, 23.1%, 25, 25.4%, 25.5%, 255, 26%, 28%, 29%, 3.0, 3.05, 3.2, 3.42, 3.80, 3.84, 31%, 32%, 33, 33%, 34%, 35, 381, 4.03, 4.1, 4.55, 40%, 41.5%, 41.7%, 42, 43%, 43.8%, 437, 447488, 45, 46.2%, 48%, 50, 52, 55%, 56%, 56.8%, 57%, 58%, 59%, 61.6%, 64.1%, 68.4%, 68.8%, 6833%, 7, 71%, 72%, 73%, 73.9%, 74%, 75%, 79, 8, 8%, 80%, 81%, 88.9%, 89%, 900, 922, 97%, 971, 98 | 0.4, 0.65, 0.78, 00000, 00135, 14, 2.2, 22%, 27, 29, 3.1, 3.13, 31, 36%, 42.1%, 427, 5.0, 5.1, 5.3, 75, 82, 82%, 90 |
