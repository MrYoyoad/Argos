# Confidence Signals — Trust Diagnostic

Run on full-set n-best evaluation. Filtered to segments with seg_mean_conf >= 0.65 (below this no per-word policy applies).

- Total word-rows kept: **16367** (function: 8914, content: 7297, others dropped)

## Test A — Independence: are top1_conf and beam_agreement redundant?

- Pearson r overall: **+0.582**
- Pearson r within function words: **+0.552**
- Pearson r within content words: **+0.602**
- **Verdict: PASS** (criterion: |r_cont| < 0.85; redundancy would mean adding agreement gives no new info)

## Test B — Reliability curves: can we fit POS-aware thresholds at P(correct) >= 0.85?

### Function words
| top1_conf bin | n | P(correct) |
|---|---|---|
| 0.00 – 0.40 | 736 | 0.288 |
| 0.40 – 0.55 | 644 | 0.365 |
| 0.55 – 0.65 | 481 | 0.495 |
| 0.65 – 0.75 | 623 | 0.493 |
| 0.75 – 0.82 | 553 | 0.642 |
| 0.82 – 0.89 | 761 | 0.707 |
| 0.89 – 0.95 | 1035 | 0.748 |
| 0.95 – 0.98 | 1046 | 0.848 |
| 0.98 – 1.00 | 3035 | 0.936 |

Fitted T_function (P>=0.85, n>=50): **0.98**

### Content words
| top1_conf bin | n | P(correct) |
|---|---|---|
| 0.00 – 0.40 | 1087 | 0.196 |
| 0.40 – 0.55 | 596 | 0.305 |
| 0.55 – 0.65 | 441 | 0.399 |
| 0.65 – 0.75 | 442 | 0.464 |
| 0.75 – 0.82 | 376 | 0.511 |
| 0.82 – 0.89 | 474 | 0.633 |
| 0.89 – 0.95 | 720 | 0.692 |
| 0.95 – 0.98 | 757 | 0.848 |
| 0.98 – 1.00 | 2404 | 0.937 |

Fitted T_content (P>=0.85, n>=50): **0.98**

**Verdict: PASS** (criterion: a content threshold exists where P(correct) >= 0.85 with n >= 50)

## Test C — 2D rescue: does beam-agreement add lift in the high-conf regime for content words?

### Content

P(correct) (N in parens):

| top1_conf \ agree | 0.00+ | 0.50+ | 0.80+ | 0.95+ |
|---|---|---|---|---|
| **0.00+** | 0.14 (n=749) | 0.29 (n=551) | 0.32 (n=314) | 0.39 (n=510) |
| **0.65+** | 0.19 (n=83) | 0.38 (n=164) | 0.53 (n=204) | 0.57 (n=367) |
| **0.82+** | 0.26 (n=43) | 0.44 (n=71) | 0.64 (n=118) | 0.71 (n=328) |
| **0.90+** | 0.11 (n=27) | 0.47 (n=51) | 0.67 (n=103) | 0.77 (n=453) |
| **0.95+** | 0.40 (n=42) | 0.73 (n=70) | 0.84 (n=266) | 0.94 (n=2783) |

### Function (for reference)

P(correct) (N in parens):

| top1_conf \ agree | 0.00+ | 0.50+ | 0.80+ | 0.95+ |
|---|---|---|---|---|
| **0.00+** | 0.21 (n=464) | 0.36 (n=555) | 0.40 (n=300) | 0.49 (n=542) |
| **0.65+** | 0.29 (n=72) | 0.48 (n=242) | 0.58 (n=273) | 0.62 (n=589) |
| **0.82+** | 0.26 (n=35) | 0.57 (n=87) | 0.72 (n=177) | 0.76 (n=605) |
| **0.90+** | 0.12 (n=16) | 0.53 (n=59) | 0.71 (n=140) | 0.79 (n=677) |
| **0.95+** | 0.31 (n=32) | 0.59 (n=87) | 0.85 (n=304) | 0.93 (n=3658) |

P(correct | conf>=0.95 & agree>=0.95) − P(correct | conf>=0.95 & agree<0.50) = **+53.09%** (n_hh=2783, n_hl=42)

**Verdict: PASS** (criterion: >=15pp lift, n>=30 each cell)

---

## Overall verdict: **PASS — proceed to implementation**
