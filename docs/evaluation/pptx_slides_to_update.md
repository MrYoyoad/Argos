# PPTX Slides To Update — High-Priority List for Academic Deck

Slides flagged for the new MBR-default academic deck. Focus is the AFTER_AMOSI March 84-slide deck (the master reference); client-deck entries appear in a separate section.

Legend: **NV** = NEEDS_VERIFICATION (likely shifted), **WF** = WRONG_FRAMING_FIX (needs text rewrite, not just number swap).

## AFTER_AMOSI March 2026 deck (84 slides) — by section

### Opening / Mission / TL;DR

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 4 | yes | Executive Summary | 5 | 0 | `61.6%`, `2.4`, `3.5`, `4.0`, `2.52` |
| 5 | yes | WER: The Metric That Lies | 4 | 0 | `6`, `1`, `46.2%`, `4.03` |

### Problem Framing (VSP, Visemes, Reality Gap)

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 7 | no | What is Visual Speech Processing? | 16 | 0 | `55`, `70%`, `45`, `52%`, `33`, `447488` |
| 9 | no | How It Works: Three Components | 15 | 0 | `4096`, `12.6`, `3.1`, `8`, `7`, `024` |
| 10 | no | How It Works: Data Flow | 9 | 0 | `1024`, `4096`, `25`, `96`, `6`, `2` |
| 11 | no | The Benchmark: Paper vs Reality | 7 | 0 | `64.1%`, `2.5`, `32%`, `25.4%` |
| 12 | no | The Reality Gap | 10 | 0 | `64.1%`, `25.5%`, `20.6%`, `100%`, `2.5`, `25.4%` |
| 13 | no | Same WER, Different Effects | 4 | 0 | `1` |

### Research Findings (LLM Judge, IS framework)

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 17 | no | Judge Example 1: Named Entity Swap | 5 | 0 | `4.55`, `1`, `18.2%`, `18%` |
| 18 | no | Judge Example 2: Truncated but Core Preserved | 5 | 0 | `3.69`, `48.1%`, `41.7%`, `48%` |
| 19 | no | Judge Example 3: Technical Vocabulary Drift | 3 | 0 | `3.02`, `51.5%` |
| 20 | no | Judge Example 4: Scientific Vocabulary Lost | 6 | 0 | `43.3%`, `56.8%`, `2.67` |
| 21 | no | Judge Example 5: Cooking Domain Confusion | 3 | 0 | `88.9%`, `43.8%`, `2.07` |
| 22 | no | Judge Example 6: Topic Hijack | 4 | 0 | `1.79`, `73.9%`, `68.8%` |
| 23 | no | Why LLM as a Judge Is Not Enough | 11 | 0 | `12`, `0.0`, `5.0`, `6`, `1`, `2` |
| 24 | no | IS Signals: Word Accuracy & Length | 16 | 0 | `1`, `0`, `15%`, `6`, `5`, `2.00` |
| 25 | no | IS Signals: Semantic Similarity | 6 | 0 | `1`, `384`, `2`, `3`, `0.91`, `80%` |
| 27 | no | Do 6 Signals Actually Measure 6 Things? | 17 | 0 | `5`, `0.43`, `0.47`, `0.31`, `6`, `68.4%` |
| 28 | no | IS in Action: Two Real Segments | 13 | 0 | `5`, `4.2`, `0.8`, `4.22`, `0.81`, `0` |
| 29 | no | Model Comparison: IS Profiles | 16 | 0 | `1`, `0.779`, `0.794`, `0.689`, `0.662`, `0.683` |
| 30 | no | The Gap: Where WER Lies Most | 22 | 0 | `3.80`, `2.00`, `42`, `34%`, `437`, `40%` |
| 31 | no | Intelligibility Score: 61.6% Useful Output | 23 | 0 | `61.6%`, `15%`, `2.00`, `2.4`, `25.5%`, `41.5%` |
| 32 | no | Two Evaluation Systems, One Framework | 14 | 0 | `61.6%`, `23.1%`, `3.80`, `346`, `2.00`, `922` |
| 33 | no | IS: A Calibrated Surrogate Metric | 10 | 0 | `61.6%`, `3`, `2`, `2.00` |
| 34 | yes | Where IS and the Judge Disagree | 21 | 0 | `2.00`, `3.42`, `100%`, `1.84`, `71%`, `29%` |
| 35 | yes | Context Exposes Hidden Failures | 9 | 0 | `4.75`, `3.6`, `3.3`, `3.2`, `230`, `68` |
| 36 | no | Three Numbers That Tell the Real Story | 16 | 0 | `34%`, `381`, `61.6%`, `2.00`, `922`, `1` |

### Failure Modes & Real Examples

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 37 | no | Failure Mode Taxonomy | 10 | 0 | `2.00`, `574`, `5`, `44.4%`, `255`, `18.8%` |
| 38 | no | Failure Mode Taxonomy (1/2): Highest Impact First | 5 | 0 | `2`, `18.8%`, `100%`, `20%`, `0.2` |
| 39 | no | Failure Mode Taxonomy (2/2): Accumulated → Signal Loss | 10 | 0 | `2.0`, `1`, `3`, `4`, `5`, `2` |
| 40 | no | Failure Modes: Real Examples | 11 | 0 | `100%`, `18.8%`, `0.1`, `8`, `2`, `97%` |
| 42 | yes | When Metrics Disagree: What It Tells Us | 7 | 0 | `100%`, `43%`, `15%`, `57%`, `0.87`, `6` |
| 43 | yes | When Metrics Disagree: More Patterns | 9 | 0 | `1.0`, `3`, `6833%`, `45`, `55%`, `0.48` |
| 44 | no | IS: A Calibrated Surrogate for LLM Judgment | 9 | 0 | `61.6%`, `3`, `2`, `2.00`, `25` |
| 45 | no | LLM Salvage: Three Real Recoveries | 11 | 0 | `75%`, `3.0`, `1.29`, `150%`, `0.55`, `2.18` |
| 46 | no | LLM Salvage: Domain Context Fills the Gaps | 14 | 0 | `2.07`, `2.75`, `0.90`, `2.86`, `72%`, `43%` |
| 47 | no | Curated Examples — Video Gallery | 5 | 0 | `31%`, `34%`, `59%`, `33%`, `172%` |
| 48 | no | Demo: OK → Almost There → Hallucination | 6 | 0 | `28%`, `4.1`, `56%`, `2.9`, `100%`, `0.8` |

### Future Directions (Confidence, Roadmap)

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 59 | no | Starting from 61.6%, Not 25% | 5 | 0 | `61.6%`, `25.5%`, `85%` |
| 60 | no | Five Phases — From IS 2.5 to Target IS 3.3–3.7 | 47 | 0 | `3.3`, `3.7`, `80`, `85%`, `0.98`, `2` |
| 61 | no | IS Improvement Roadmap — From 2.5 to 3.5 | 32 | 0 | `2.52`, `61.6%`, `2.5`, `1`, `2`, `2.65` |
| 65 | no | Data Scaling: The Path to IS 3.5–4.0 | 12 | 0 | `3.5`, `4.0`, `64.1%`, `2.52`, `20`, `3.1` |
| 66 | no | The Price Tag: What It Costs to Improve | 9 | 0 | `25.4%`, `2.52`, `3.5`, `4.0`, `46`, `115` |
| 67 | no | Fine-Tuning: Limited Data, Limited Gains | 5 | 0 | `2.49`, `2.31`, `2.02`, `64`, `20` |
| 68 | no | Stronger LLM + Smart Prompts = Force Multiplier | 19 | 0 | `8`, `7`, `3`, `3.1`, `15`, `2` |
| 69 | no | The LLM Is a Context Engine | 5 | 0 | `3.1`, `8`, `2`, `70`, `4096` |
| 70 | yes | LLM Upgrade: Why It Matters | 25 | 0 | `3`, `2`, `3.2`, `18.7%`, `7`, `25.4%` |
| 71 | no | Failure Modes: Impact & What Fixes Them | 5 | 0 | `18.8%`, `1000`, `5`, `44.4%`, `54.3%` |

### Arabic / Closing / Appendix

| Slide # | Hidden | Title | NV | WF | Numbers seen (top 6) |
|--------:|--------|-------|---:|---:|----------------------|
| 72 | no | Arabic Pipeline: Replication Roadmap | 13 | 0 | `3`, `2`, `5`, `10`, `1`, `4` |
| 74 | no | Arabic Adaptation: What Changes | 3 | 0 | `2`, `4` |
| 78 | no | A3: IS Component Correlation | 8 | 0 | `2`, `6`, `68.4%`, `5`, `19.5%`, `2.00` |
| 79 | no | A4: LLM Salvage — Recoverable Segments | 11 | 0 | `165`, `61.6%`, `50%`, `10`, `900`, `6` |
| 80 | yes | A5: LLM Salvage — Curated Examples | 3 | 0 | `2.0`, `6` |
| 81 | no | A6: Failure Mode Examples | 6 | 0 | `108`, `5`, `574`, `2.00`, `44.4%`, `255` |
| 83 | no | A8: LLM Judge × IS Tier Cross-Tabulation | 22 | 0 | `2.00`, `5`, `57%`, `2`, `3`, `1` |
| 84 | no | A9: Context Evaluation — Transition Details | 6 | 0 | `4`, `230`, `68`, `138`, `7`, `80.0%` |

## WRONG_FRAMING_FIX checklist (AMOSI deck)

None detected.

## Client v9/v10 deck (64 slides) — high-priority touches

v9 and v10 are textually identical. Update once and re-export both names if both must remain on disk.

| Slide # | Title | NV | WF | Numbers seen (top 6) |
|--------:|-------|---:|---:|----------------------|
| 14 | Three numbers, in plain English | 3 | 0 | `1`, `22`, `65%` |
| 15 | Example 1 — Trust: clean speech (Obama) | 6 | 0 | `27`, `29`, `14`, `0%` |
| 19 | Two layers of confidence | 5 | 0 | `2`, `5.3`, `1`, `82%` |
| 23 | Example 3 — Trust: gallery of six clean outputs | 3 | 0 | `5.1`, `5.0`, `0%` |
| 24 | Example 4 — Salvage: partial recovery (Obama) | 5 | 0 | `4`, `9`, `11`, `31`, `22%` |
| 26 | Example 6 — Salvage: technical-vocabulary drift | 3 | 0 | `6`, `51.5%`, `3.02` |
| 28 | Example 8 — Salvage: reading the colors (walk-through) | 8 | 0 | `8`, `6`, `427`, `0`, `00000`, `00135` |
| 29 | Example 9 — Strip: topic invented | 6 | 0 | `2.2`, `5.10`, `3`, `42.1%`, `2.75` |
| 30 | Example 10 — Strip: fluent fabrication caught | 5 | 0 | `25`, `3.1`, `4`, `1`, `100%` |
| 37 | Agrees with the blind evaluator 82% of the time | 8 | 0 | `82%`, `65%`, `95%`, `100%`, `75`, `85%` |
| 40 | How It Works: Data Flow | 9 | 0 | `1024`, `4096`, `25`, `96`, `6`, `2` |
| 41 | What it actually took — four passes, six months | 21 | 0 | `37`, `1`, `26`, `5.1`, `38`, `8` |
| 46 | Optional add-on — pre-filter low-quality clips before decode | 18 | 0 | `100`, `82%`, `82`, `75`, `10`, `8` |
| 47 | Optional — domain-specific training run on your data | 4 | 0 | `65%`, `71%`, `95%`, `60%` |
| 50 | Thank You | 5 | 0 | `8`, `36%`, `65%`, `6`, `10` |
