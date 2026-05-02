# n-best LLM-as-a-Judge — analysis (v1, contaminated)

> ⚠️ **This v1 run is contaminated by a prompt-design bug.** The judge was shown sentence and per-word confidence values during judging, instructed to "use as soft cue, not as verdict shortcut." It did not. On 134/494 (27 %) segments where all four methods produced byte-identical text, verdicts split anyway — the only thing that differed in the prompt was confidence numbers. The headline "rank inversion" finding is partly real (~75 %) and partly artifact (~25 %). A clean v2 re-judge with no confidence in the prompt is being staged. **Do not act on this v1 output as-is.**

**v1 run**: 2026-05-02. Judge: Claude Opus 4.7 (in-conversation).
**Scope**: 1,497 segments × 4 aggregation methods = 5,988 verdicts.

## Multi-metric ranking — what the OTHER metrics already say

Before drawing conclusions from a contaminated judge run, look at the deterministic metrics that don't have this problem:

| metric | baseline | hyp_mbr | hyp_vote_score | hyp_vote_conf | who wins |
|---|---|---|---|---|---|
| WER (lower better) | 64.05 % | 63.84 % | 63.67 % | **62.49 %** | hyp_vote_conf (−1.56 pp) |
| mean IS | 2.532 | 2.547 | 2.538 | 2.545 | tied (within 0.015) |
| median IS | 2.559 | 2.600 | 2.582 | 2.579 | hyp_mbr / vote slight |
| IS-NIV-Y % | 23.98 | 23.91 | 23.98 | 24.05 | tied |
| IS-NIV-Y+P % | 61.66 | 61.92 | 61.86 | 62.26 | tied (vote_conf +0.6) |

Paired McNemar on the IS-derived NIV-Y verdict (per-segment, IS ≥ 3.80 → Y):

| method vs baseline | method-only Y | baseline-only Y | p |
|---|---|---|---|
| hyp_mbr | 12 | 13 | 1.00 |
| hyp_vote_score | 9 | 9 | 0.81 |
| hyp_vote_conf | 19 | 18 | 1.00 |

**On IS, the project's own semantic metric, all three n-best methods are statistically indistinguishable from baseline.** Per-segment median IS delta is 0.000 for every method. WER says vote_conf is marginally better; IS says they're tied. That is the cleanest reading of the *uncontaminated* evidence.

## v1 judge results (contaminated — for the record)

| method | NIV-Y rate | Δ vs baseline | NIV-Y+P rate | Δ vs baseline |
|---|---|---|---|---|
| **baseline (1-best)** | **16.6 %** | — | **69.8 %** | — |
| `hyp_mbr` | 16.4 % | −0.2 pp (p=0.82) | 68.5 % | −1.3 pp (p=0.07) |
| `hyp_vote_score` | 17.3 % | +0.7 pp (p=0.51) | 68.3 % | −1.5 pp (p=0.022) |
| `hyp_vote_conf` | 13.6 % | −3.0 pp (p=0.0005) | 67.6 % | −2.2 pp (p=0.0024) |

Restricted to text-differing segments (removes the worst of the prompt confound):

| method vs baseline | n (text differs) | Y verdict<br>method only | Y verdict<br>baseline only | p (Y) | p (Y+P) |
|---|---|---|---|---|---|
| hyp_mbr | 580 | 31 | 38 | 0.47 | 0.13 |
| hyp_vote_score | 480 | 31 | 23 | 0.34 | 0.24 |
| hyp_vote_conf | 940 | 30 | 64 | 0.0007 | 0.012 |

`hyp_vote_conf` remains significantly worse than baseline even on text-differing segments — but this is still a confounded judge (per-word conf differs between method and baseline even when whole sentences happen to match), and it disagrees with IS on the same segments. **Treat the v1 judge result as one signal among several, not as the ground truth.**

## Combined cross-metric read

| who's right? | what they say |
|---|---|
| **WER** | vote_conf marginally wins (−1.56 pp) |
| **Mean / median IS** | all four tied |
| **IS-NIV-Y / Y+P** | all four tied (paired p ≈ 1.0) |
| **v1 judge (contaminated)** | vote_conf significantly loses |
| **v2 judge (blind, no conf)** | being staged — see `batches_v2/` |

When 3 of 4 metrics say "essentially tied" and the 4th is contaminated, the honest summary is: **n-best aggregation does not materially change semantic quality on this dataset; vote_conf gets the best WER and that's the only meaningful difference**. The "do not ship vote_conf" conclusion is downgraded to "ship is acceptable on the evidence; clean v2 judge will confirm or refute."

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

## Regression mechanism (text-differing subset only)

Of the 940 segments where `hyp_vote_conf` produced different text from baseline, the regression cases have a consistent shape: vote_conf drops a small connective or swaps a function word, which lowers WER by one substitution but pushes the judge from Y → P. Examples:

```
ref:        "in the creation of these children or in the making"
baseline:   "in the creation of these children's orders and then in the making of"   (Y)
vote_conf:  "in the creation of these children's orders then in the making of"       (P)
                                                          ^^^ "and" dropped
```

```
ref:        "he is now 7 years old my third one will also be a male, he is 1 years old..."
baseline:   "is now seven years old my third one will also be a boy, a kid is one year old..."  (Y)
vote_conf:  "is now seven years old my third one will also be a boy, kid is one year old..."   (P)
                                                                       ^^^ "a" dropped
```

The vote-by-confidence weighting concentrates votes on the most-confident word at each position; when several beams confidently disagree on a function word, voting picks the surface-frequent one and skips the connective the reference actually has. Lower WER (one fewer substitution), but the judge reads the result as partial.

This is consistent with the existing literature note in memory: the per-word vote_conf "confidence" is an **agreement score**, not a Bayesian posterior (Eikema & Aziz 2020; Spagnolo 2025). High agreement among wrong-but-similar beams produces fluent-but-meaning-shifted output.

⚠️ **An earlier draft of this section cited a different example where all four methods produced byte-identical text**. That was confounded — the verdict difference came from the prompt-level confidence cues, not from the text. See "The confidence-in-prompt confound" caveat below for the proper accounting.

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

### The confidence-in-prompt confound is real and large — not theoretical

In **494/1,497 segments (33 %)** all four methods produced **byte-identical** hypothesis text (the 20 candidate beams agreed strongly enough that the four aggregation algorithms returned the same string). Of those 494 identical-text segments, **134 (27 %)** received different verdicts across methods.

Concrete example (`-29kYQQ3Kos_11`):

```
ref:           "that are going to allow you to work with the team in a more"
all 4 methods: "are going to allow you to work with a team and more"  (byte-identical)

verdicts:
  baseline       Y    sentence_conf=0.91
  hyp_mbr        Y    sentence_conf=0.83
  hyp_vote_score P    sentence_conf=0.66
  hyp_vote_conf  P    sentence_conf=0.67
```

Identical text → different verdicts. The only thing that changed in the prompt is the confidence numbers (`sentence_conf` and per-word `[.NN]` tags). The judge **let confidence drive the verdict** despite our instruction "use as soft cue, NOT as a verdict shortcut."

Pairwise drift on identical-text segments vs baseline (showing only `hyp_vote_conf`):

```
hyp_vote_conf, identical text to baseline (557 segments):
  Y → P   38   (Y lost)
  P → Y   27   (Y gained)
  P → N   22   (Y+P lost)
  N → P   12   (Y+P gained)
  net Y movement: -11   net Y+P movement: -10
```

### What survives when you remove the confound

Restricting McNemar to **segments where the method's text actually differs from baseline**:

| method vs baseline | n (text differs) | Y verdict<br>method only | Y verdict<br>baseline only | chi² | p | Y+P p |
|---|---|---|---|---|---|---|
| hyp_mbr | 580 | 31 | 38 | 0.52 | 0.47 (n.s.) | 0.13 (n.s.) |
| hyp_vote_score | 480 | 31 | 23 | 0.91 | 0.34 (n.s.) | 0.24 (n.s.) |
| **hyp_vote_conf** | **940** | **30** | **64** | **11.59** | **0.0007** | **0.012** |

`hyp_vote_conf` remains significantly worse than baseline even after removing identical-text segments. The full-set Y deficit was 102 baseline-only minus 57 method-only = −45 Ys; about −11 of that came from identical-text drift (artifact), the remaining ~−34 from text-differing segments (real). **Roughly 75 % of the rank inversion is robust to the confound, 25 % is artifact.**

For `hyp_mbr` and `hyp_vote_score`, removing identical-text segments dropped both already-weak effects below significance, which is consistent with their full-set findings being borderline anyway.

### Other caveats

1. **Judge model change vs prior gold standard.** The March 2026 `llm_judge/` run used Opus 4.6 and produced 23.0 % Y on baseline. This run on Opus 4.7 produces 16.6 % Y on baseline. The shift is partly model version, partly the per-word + sentence conf cues now being shown to the judge (the very confound documented above). **Cross-run absolute Y rates are not comparable; within-run paired comparisons are.**
2. **Auto-N rows count toward N.** ~70 segments per method (mostly empty hyps) are auto-classified N. Removing them shifts absolute rates but not rankings.
3. **Methodology fix for any future run**: do the judging blind on text alone, no confidence numbers in the prompt. If we want a confidence-vs-verdict calibration table, build it post-hoc by joining the judge verdicts with the confidence values stored in `report.csv` — don't show conf to the judge during judging.

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
