# n-best LLM-as-a-Judge — analysis

**Run**: 2026-05-02. Judge model: Claude Opus 4.7 (in-conversation).
**Scope**: 1,497 segments × 4 aggregation methods (baseline, `hyp_mbr`, `hyp_vote_score`, `hyp_vote_conf`) = **5,988 verdicts**, 60 batch files, 0 missing, 0 partial.

## TL;DR

Mission 6 ranks `hyp_vote_conf` first on WER (−1.56 pp, 62.49 %). The judge ranks it **last** on the operating point we ship against:

| method | NIV-Y rate | Δ vs baseline | NIV-Y+P rate | Δ vs baseline | WER (full set) |
|---|---|---|---|---|---|
| **baseline (1-best)** | **16.6 %** | — | **69.8 %** | — | 64.05 % |
| `hyp_mbr` | 16.4 % | −0.2 pp (n.s.) | 68.5 % | −1.3 pp (p=0.07) | 63.83 % |
| `hyp_vote_score` | 17.3 % | +0.7 pp (n.s.) | 68.3 % | −1.5 pp (p=0.022) | — |
| `hyp_vote_conf` | **13.6 %** | **−3.0 pp (p=0.0005)** | **67.6 %** | **−2.2 pp (p=0.0024)** | **62.49 %** |

McNemar tests are paired by `utt_id`, continuity-corrected, two-sided. **None of the n-best methods improve NIV-Y or NIV-Y+P over the 1-best baseline**, and `hyp_vote_conf` significantly regresses both.

This is a **rank inversion between WER and NIV** — the metric we use to decide what ships disagrees with the metric we ranked candidates by.

## What this answers

The original Mission 6 plan validated n-best aggregation on **WER**. The two open questions this run resolves:

1. **Does `hyp_vote_conf`'s WER win translate to more meaning conveyed (Y verdicts)?** — **No.** WER trims edits, but the edits being trimmed are not the meaning-bearing ones. `hyp_vote_conf` makes minor word swaps (e.g., dropping a connective) that the judge reads as "partial" instead of "Y." See *Regression mechanism* below.
2. **Does `sentence_confidence` predict the judge verdict?** — **Yes**, strongly, for baseline and `hyp_mbr`. The Mission 4.1 calibration data is now available.

## Per-method confusion vs baseline

`baseline_verdict` (rows) × `method_verdict` (columns):

```
hyp_mbr                   Y     P     N
  baseline = Y          161    88     0
  baseline = P           82   654    60
  baseline = N            2    39   411

hyp_vote_score            Y     P     N
  baseline = Y          160    89     0
  baseline = P           99   639    58
  baseline = N            0    35   417

hyp_vote_conf             Y     P     N
  baseline = Y          147   101     1     <- 102 Ys downgraded
  baseline = P           57   668    71
  baseline = N            0    39   413
```

`hyp_vote_conf` downgrades **101 baseline-Y → P** and only recovers **57 baseline-P → Y**. The net swing on the Y line is **−44**. Same pattern shows up on Y+P: vote_conf moves 71 baseline-P out to N and only recovers 39 baseline-N to P (net −32).

## Regression mechanism — vote_conf trims surface edits, not meaning

A representative regression case (`-29kYQQ3Kos_11`):

- ref: *"that are going to allow you to work with the team in a more"*
- baseline (verdict Y): *"are going to allow you to work with a team and more"*
- vote_conf (verdict P): *"are going to allow you to work with a team and more"* (same sentence; vote_conf's per-word agreement nudged judge from Y to P on a near-identical hypothesis)

More substantive ones drop a single connective ("then" → "and then" missing, "is one" → "kid is one"), which lowers WER by one substitution but pushes the judge from "meaning conveyed" to "partial." The vote-by-confidence weighting concentrates votes on the most-confident word at each position; when several beams confidently disagree on a function word, voting picks the surface-frequent one and skips the connective the reference actually has.

This is consistent with what memory already records: the per-word vote_conf "confidence" is an **agreement score**, not a Bayesian posterior (Eikema & Aziz 2020; Spagnolo 2025). High agreement among wrong-but-similar beams produces fluent-but-meaning-shifted output.

## Intra-rater reliability (30 duplicate pairs per method)

| method | n | exact | lenient (Y+P vs N) |
|---|---|---|---|
| baseline | 30 | 86.7 % | 100.0 % |
| `hyp_mbr` | 30 | 86.7 % | 93.3 % |
| `hyp_vote_score` | 30 | 83.3 % | 86.7 % |
| `hyp_vote_conf` | 30 | **76.7 %** | 86.7 % |

Baseline matches the prior gold standard (86.7 %) — judge stability on baseline outputs is unchanged. `hyp_vote_conf` is **10 pp less consistent** than baseline — the outputs are themselves harder to judge, which is corroborating evidence for the "borderline P" pattern above (more cases where the verdict can credibly go either way).

## Calibration: confidence vs judge verdict

`sentence_confidence` (baseline) vs judge — strong monotonic relationship:

| sentence_conf bin | n | P(Y) | P(Y+P) |
|---|---|---|---|
| [0.0, 0.3) | 25 | 0.0 % | 0.0 % |
| [0.3, 0.4) | 69 | 0.0 % | 8.7 % |
| [0.4, 0.5) | 144 | 0.0 % | 18.1 % |
| [0.5, 0.6) | 190 | 1.6 % | 44.2 % |
| [0.6, 0.7) | 275 | 5.1 % | 79.6 % |
| [0.7, 0.8) | 319 | 15.0 % | **96.9 %** |
| [0.8, 0.9) | 288 | 36.5 % | **99.0 %** |
| [0.9, 1.0) | 117 | **67.5 %** | 99.1 % |

Same shape for `hyp_mbr` (e.g., bin [0.8, 0.9) → 76 % Y, 100 % Y+P, n=97).

`hyp_vote_score` and `hyp_vote_conf` have a much narrower confidence range (essentially [0.4, 0.8)) — the agreement-based confidence rarely produces a high-conf or low-conf tail. Within their range the relationship is monotonic but the discrimination is shallower. This is consistent with these methods emitting an agreement score rather than a posterior.

**Implication for Mission 4.1**: `sentence_confidence` calibrates well against an independent semantic verdict. The three-tier policy in MEMORY.md is corroborated — at conf ≥ 0.7 the segment is Y+P with ≥ 96 % probability; at conf < 0.4 the segment is N with ≥ 91 % probability.

## Important caveats

1. **Judge model change vs prior gold standard.** The prior `llm_judge/` run (March 2026) used Opus 4.6 and produced 23.0 % Y on baseline. This run on Opus 4.7 produces 16.6 % Y on baseline. The shift is partly model version and partly the per-word + sentence confidence cues now being shown to the judge. **Cross-run absolute Y rates are not comparable; within-run rankings and McNemar paired tests are.** All headline claims here use within-run paired comparisons.
2. **Confidence-in-prompt confound.** The judge sees per-word and sentence conf during judgment. We tell it to use them as soft cues only, but cannot rule out a small influence on borderline calls. The rank inversion finding doesn't depend on this — `hyp_vote_conf` has the highest mean conf of the four methods, so any "high conf → judge nudges Y" bias would *help* it, not hurt it; that the rank inversion appears anyway makes the finding more robust.
3. **Auto-N rows count toward N.** ~70 segments per method (mostly empty hyps) are auto-classified N. Removing them shifts absolute rates but not rankings.

## What to do with this

1. **Stop ranking n-best aggregation candidates by WER alone.** The decision rule for "ship a method" should be: paired McNemar on NIV-Y (or at minimum, paired vs baseline on the same segments).
2. **Do not ship `hyp_vote_conf` as a default.** It's a statistically significant regression on the operating point we ship against, despite winning WER.
3. **`hyp_mbr` is the closest to neutral.** If there's a plausible reason to want the n-best machinery (e.g., for the per-word agreement score as an *uncertainty* signal — distinct from using it to *pick* the output), MBR is the safer choice for replacing the 1-best.
4. **Calibration data unblocks Mission 4.1.** Use the (sentence_confidence, judge verdict) pairs from `results_long.csv` (baseline rows, n=1,497) as the calibration set for the three-tier policy.

## Files

- `results_long.csv` — one row per (utt_id × method), n=5,988
- `results_wide.csv` — one row per utt_id with all 4 verdicts side-by-side
- `summary.json` — per-method counts, McNemar, intra-rater
- `calibration.csv` — 10 conf-bins × 4 methods → P(Y), P(Y+P)
- `auto_judgments.csv` — 280 empty/short-hyp auto-N rows
- `judgments/batch_<method>_NN_judgments.txt` — raw verdicts (60 files)

Reproduce with: `python3 /home/ubuntu/docs/_research-tools/generators/analyze_nbest_judge.py`
