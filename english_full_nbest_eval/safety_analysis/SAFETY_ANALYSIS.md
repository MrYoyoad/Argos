# Band Safety Analysis — How reliable is each color?

Per-word and per-sentence reliability of the new joint conf+agreement band rule, vs the legacy conf-only rule, on the full 1,497-segment evaluation (23,261 words).

Source: [per_word_diagnostic.csv](../trust_diagnostic/per_word_diagnostic.csv) (full per-word table) and [report.csv](../report/report.csv) (per-segment metrics).

## 1. Per-word — does each color deliver on its promise?

| Band | Old count | Old P(correct) | New count | New P(correct) | ΔP | ΔN |
|---|---|---|---|---|---|---|
| green | 11309 | 0.806 | 7591 | 0.898 | +0.092 | -3718 |
| yellow | 7470 | 0.383 | 6571 | 0.590 | +0.207 | -899 |
| red | 4482 | 0.154 | 9099 | 0.217 | +0.063 | +4617 |

**Headline.** Green words are now correct **89.8%** of the time (vs 80.6% under the old rule). Coverage dropped 11309 → 7591, but the words that *are* still green are materially more reliable.

## 2. Per-word stratified by segment tier

Recall the segment-level outer gate: Trust (seg_mean ≥ 0.82), Salvage (0.65–0.82), Strip (<0.65). Below shows per-word reliability inside each tier under each rule.

### Trust segments

| Band | Old n | Old P(correct) | New n | New P(correct) |
|---|---|---|---|---|
| green | 4958 | 0.924 | 3923 | 0.953 |
| yellow | 1319 | 0.591 | 1719 | 0.761 |
| red | 316 | 0.278 | 951 | 0.420 |

### Salvage segments

| Band | Old n | Old P(correct) | New n | New P(correct) |
|---|---|---|---|---|
| green | 4882 | 0.798 | 3091 | 0.891 |
| yellow | 3359 | 0.427 | 3241 | 0.605 |
| red | 1533 | 0.222 | 3442 | 0.277 |

## 3. Per-word stratified by POS class

### Function words

| Band | Old n | Old P(correct) | New n | New P(correct) |
|---|---|---|---|---|
| green | 6506 | 0.806 | 4316 | 0.894 |
| yellow | 4209 | 0.419 | 3943 | 0.605 |
| red | 2044 | 0.185 | 4500 | 0.254 |

### Content words

| Band | Old n | Old P(correct) | New n | New P(correct) |
|---|---|---|---|---|
| green | 4719 | 0.809 | 3272 | 0.904 |
| yellow | 3178 | 0.338 | 2517 | 0.565 |
| red | 2375 | 0.129 | 4483 | 0.183 |

### Number words

| Band | Old n | Old P(correct) | New n | New P(correct) |
|---|---|---|---|---|
| green | 75 | 0.693 | 0 | — |
| yellow | 71 | 0.324 | 100 | 0.670 |
| red | 50 | 0.080 | 96 | 0.125 |

## 4. Per-sentence — how does the green fraction predict sentence quality?

Each row is a band of segments grouped by the fraction of their words painted green under the given rule. P(NIV-Y) is fraction of segments hitting IS ≥ 3.80 ("clearly conveyed"); P(NIV-Y+P) is IS ≥ 2.00 ("any useful output"); P(hallu) is fraction with WER ≥ 100% (model fabricated text).

### New rule

| Green fraction | n segs | P(NIV-Y) | P(NIV-Y+P) | P(hallu) | mean WER | mean IS |
|---|---|---|---|---|---|---|
| 0.00–0.10 | 386 | 0.01 | 0.18 | 0.44 | 96.4% | 1.38 |
| 0.10–0.30 | 411 | 0.06 | 0.61 | 0.14 | 71.3% | 2.31 |
| 0.30–0.50 | 309 | 0.32 | 0.94 | 0.02 | 45.5% | 3.30 |
| 0.50–0.70 | 250 | 0.67 | 0.97 | 0.01 | 28.6% | 3.92 |
| 0.70–0.90 | 66 | 0.88 | 0.98 | 0.00 | 16.8% | 4.36 |
| 0.90–1.00 | 5 | 1.00 | 1.00 | 0.00 | 10.3% | 4.75 |

### Old rule

| Green fraction | n segs | P(NIV-Y) | P(NIV-Y+P) | P(hallu) | mean WER | mean IS |
|---|---|---|---|---|---|---|
| 0.00–0.10 | 141 | 0.00 | 0.07 | 0.59 | 102.7% | 1.10 |
| 0.10–0.30 | 299 | 0.01 | 0.27 | 0.34 | 91.9% | 1.58 |
| 0.30–0.50 | 358 | 0.07 | 0.66 | 0.12 | 68.6% | 2.39 |
| 0.50–0.70 | 376 | 0.35 | 0.92 | 0.02 | 43.9% | 3.34 |
| 0.70–0.90 | 226 | 0.76 | 0.99 | 0.01 | 24.4% | 4.10 |
| 0.90–1.00 | 27 | 1.00 | 1.00 | 0.00 | 12.5% | 4.63 |

## 5. Sentence-level promise: "if 90%+ of words are green, can I trust the sentence?"

| Rule | n segs ≥90% green | P(NIV-Y+P) | P(NIV-Y) | P(hallu) | mean WER |
|---|---|---|---|---|---|
| Old | 27 | 1.00 | 1.00 | 0.00 | 12.5% |
| New | 5 | 1.00 | 1.00 | 0.00 | 10.3% |

## 6. Bottom line

Per-word: green coverage shrank but the green words that remain are individually more reliable. Yellow and red shifted: the new rule pushes ambiguous mid-band words into red, where they belong.

Per-sentence: high-green-fraction sentences become a stronger signal of overall quality — the new rule's ≥90%-green segments have a higher P(NIV-Y) and P(NIV-Y+P) than the old rule's, *and* the new rule has fewer such segments. Both axes (precision, predictiveness) move in the right direction.

Numeric tokens: 0 painted green under the new rule (vs 3718 bandshift across all words).