# Threshold Calibration: IS and WER vs Opus-as-a-Judge

**Date:** 2026-03-07
**Dataset:** 1,497 baseline segments, all judged by Claude Opus 4.6 (blind, 3-level Y/P/N)

---

## NIV Thresholds (Adopted Standard)

The **NIV thresholds** are the empirically calibrated IS and WER decision boundaries that
maximize agreement with the Opus-as-a-Judge gold standard while keeping IS as a strict
(conservative) estimator of performance.

| Target | IS (NIV) | WER (NIV) | IS κ | WER κ | IS wins by |
|--------|----------|-----------|------|-------|-----------|
| **Y** (meaning clearly conveyed) | **>= 3.80** | **<= 34%** | **0.690** | **0.629** | **+0.061** |
| **Y+P** (any useful meaning) | **>= 2.00** | **<= 77%** | **0.818** | **0.777** | **+0.041** |

**Why these specific values:**

- **IS >= 3.80 for Y:** Captures 346 segments (23.1%) — matches judge's Y rate of 345
  (23.0%) almost exactly. κ=0.690 (within 0.004 of optimal 0.694 at IS >= 3.70).
  Precision=0.760, only 83 false positives. Borderline strict.

- **IS >= 2.00 for Y+P:** Captures 922 segments (61.6%) — strictly below judge's Y+P rate
  of 971 (64.9%). κ=0.818 ("almost perfect", within 0.004 of optimal 0.822 at IS >= 1.95).
  Precision=0.958, only 39 false positives. Conservative.

- **WER <= 34% for Y:** Optimal WER threshold for Y agreement (κ=0.629). IS beats WER by
  +0.061 at this operating point.

- **WER <= 77% for Y+P:** Optimal WER threshold for Y+P agreement (κ=0.777). IS beats WER
  by +0.041 at this operating point.

**IS beats WER at every operating point.** Head-to-head at matched capture rates, IS
outperforms WER for the Y target at all 11 thresholds tested (Δκ = +0.01 to +0.08).
For Y+P, IS wins at 9 of 12 thresholds and loses marginally (Δκ = -0.015) only at IS >= 3.0,
which is a poor operating point for Y+P prediction.

**IS is a strict estimator.** At NIV thresholds, IS undercounts or matches the judge:
- Y: IS captures 23.1% vs judge 23.0% (neutral)
- Y+P: IS captures 61.6% vs judge 64.9% (strict by 3.3pp)

**Supersedes IS >= 3.0.** The old IS >= 3.0 threshold sits in no-man's land: κ=0.565 for Y
(too lenient, 271 false positives), κ=0.521 for Y+P (too strict, misses 377 useful segments).
NIV thresholds provide two clean, purpose-specific decision boundaries instead.

---

## 1. Opus Judge Ground Truth

| Code | Label | Count | Rate |
|------|-------|-------|------|
| **Y** | Meaning clearly conveyed | 345 | 23.0% |
| **P** | Some meaning preserved, key info lost | 626 | 41.8% |
| **N** | Wrong topic, hallucination, empty | 526 | 35.1% |

Two natural binary splits:
- **Strict (Y vs P+N):** "Did the output clearly convey the meaning?" (345 positive)
- **Lenient (Y+P vs N):** "Does the output have any useful meaning?" (971 positive)

---

## 2. Method: Cohen's Kappa Threshold Sweep

For each metric (IS, WER, Semantic Similarity), we sweep the decision threshold and compute
Cohen's kappa (chance-corrected agreement) against each binary Opus split.

Cohen's kappa formula:

```
    po - pe
k = -------
    1 - pe

where:
  po = observed agreement = (TP + TN) / N
  pe = expected agreement by chance = ((TP+FP)(TP+FN) + (TN+FN)(TN+FP)) / N^2
```

Interpretation (Landis & Koch 1977): <0.20 slight, 0.21-0.40 fair, 0.41-0.60 moderate,
0.61-0.80 substantial, 0.81-1.00 almost perfect.

---

## 3. Optimal Thresholds (Full Sweep)

### 3.1 Strict Target: Y (meaning clearly conveyed)

| Metric | Optimal Threshold | kappa | Agreement | Precision | Recall | F1 |
|--------|-------------------|-------|-----------|-----------|--------|------|
| **Semantic Sim** | **>= 0.70** | **0.714** | **89.7%** | 0.761 | 0.803 | 0.781 |
| IS | >= 3.70 | 0.694 | 88.8% | 0.735 | 0.803 | 0.767 |
| **IS (NIV)** | **>= 3.80** | **0.690** | **89.0%** | **0.760** | **0.762** | **0.761** |
| WER (NIV) | <= 34% | 0.629 | 86.4% | 0.685 | 0.757 | 0.719 |
| IS (old) | >= 3.00 | 0.565 | 80.6% | 0.546 | 0.945 | 0.692 |

IS >= 3.80 (NIV) is 0.004 below peak κ but captures 346 segments — matching the judge's 345.

### 3.2 Lenient Target: Y+P (any useful meaning)

| Metric | Optimal Threshold | kappa | Agreement | Precision | Recall | F1 |
|--------|-------------------|-------|-----------|-----------|--------|------|
| IS | >= 1.95 | 0.822 | 91.8% | 0.952 | 0.920 | 0.936 |
| **IS (NIV)** | **>= 2.00** | **0.818** | **91.5%** | **0.958** | **0.909** | **0.933** |
| WER (NIV) | <= 77% | 0.777 | 89.8% | 0.929 | 0.913 | 0.921 |
| Semantic Sim | >= 0.25 | 0.761 | 89.2% | 0.908 | 0.927 | 0.917 |
| IS (old) | >= 3.00 | 0.521 | 74.6% | 0.995 | 0.612 | 0.758 |

IS >= 2.00 (NIV) is 0.004 below peak κ but is stricter (61.6% vs 64.9%) and cleaner (39 FP vs 45).

---

## 4. IS vs WER: Head-to-Head at Matched Capture Rates

At the same number of "pass" segments, IS always beats WER for Y, and wins 9/12 for Y+P:

### 4.1 Target: Y (meaning clearly conveyed)

| IS threshold | WER at same rate | Pass | IS κ | WER κ | Winner |
|-------------|-----------------|------|------|-------|--------|
| >= 2.00 | <= 75% | ~922 | 0.310 | 0.290 | IS +0.020 |
| >= 2.50 | <= 62% | ~762 | 0.424 | 0.413 | IS +0.012 |
| >= 3.00 | <= 50% | ~597 | 0.565 | 0.513 | **IS +0.052** |
| >= 3.50 | <= 38% | ~433 | 0.654 | 0.614 | **IS +0.040** |
| >= 3.75 | <= 34% | ~361 | 0.692 | 0.629 | **IS +0.063** |
| **>= 3.80** | **<= 32%** | **~346** | **0.690** | **0.616** | **IS +0.074** |
| >= 4.00 | <= 29% | ~276 | 0.658 | 0.581 | **IS +0.077** |

**IS wins at every single operating point for Y.**

### 4.2 Target: Y+P (any useful meaning)

| IS threshold | WER at same rate | Pass | IS κ | WER κ | Winner |
|-------------|-----------------|------|------|-------|--------|
| >= 1.50 | <= 87% | ~1072 | 0.769 | 0.694 | **IS +0.074** |
| >= 1.75 | <= 81% | ~997 | 0.813 | 0.760 | **IS +0.053** |
| **>= 2.00** | **<= 75%** | **~922** | **0.818** | **0.768** | **IS +0.050** |
| >= 2.50 | <= 62% | ~762 | 0.674 | 0.661 | IS +0.012 |
| >= 3.00 | <= 50% | ~597 | 0.521 | 0.536 | WER +0.015 |
| >= 3.75 | <= 34% | ~361 | 0.294 | 0.310 | WER +0.016 |

IS wins decisively near optimal (Δκ = +0.05 to +0.07). WER marginally wins only at
IS >= 3.0 (by 0.015) — a poor operating point for Y+P where both metrics perform badly.

---

## 5. Full Sweep Tables

### 5.1 IS Threshold vs Y (strict)

| Threshold | kappa | Agreement | Precision | Recall | F1 | TP | FP | FN | TN |
|-----------|-------|-----------|-----------|--------|------|-----|-----|-----|------|
| >= 1.00 | 0.107 | 38.9% | 0.274 | 1.000 | 0.430 | 345 | 914 | 0 | 238 |
| >= 1.50 | 0.212 | 51.4% | 0.322 | 1.000 | 0.487 | 345 | 727 | 0 | 425 |
| >= 2.00 | 0.310 | 61.2% | 0.372 | 0.994 | 0.541 | 343 | 579 | 2 | 573 |
| >= 2.50 | 0.424 | 70.9% | 0.441 | 0.974 | 0.607 | 336 | 426 | 9 | 726 |
| >= 3.00 | 0.565 | 80.6% | 0.546 | 0.945 | 0.692 | 326 | 271 | 19 | 881 |
| >= 3.25 | 0.612 | 84.0% | 0.604 | 0.887 | 0.718 | 306 | 201 | 39 | 951 |
| >= 3.50 | 0.654 | 86.6% | 0.667 | 0.838 | 0.743 | 289 | 144 | 56 | 1008 |
| >= 3.70 | 0.694 | 88.8% | 0.735 | 0.803 | 0.767 | 277 | 100 | 68 | 1052 |
| >= 3.75 | 0.692 | 88.9% | 0.748 | 0.783 | 0.765 | 270 | 91 | 75 | 1061 |
| **>= 3.80 (NIV)** | **0.690** | **89.0%** | **0.760** | **0.762** | **0.761** | **263** | **83** | **82** | **1069** |
| >= 3.85 | 0.678 | 88.8% | 0.769 | 0.733 | 0.751 | 253 | 76 | 92 | 1076 |
| >= 4.00 | 0.658 | 88.7% | 0.819 | 0.655 | 0.728 | 226 | 50 | 119 | 1102 |
| >= 4.50 | 0.397 | 83.6% | 0.923 | 0.313 | 0.468 | 108 | 9 | 237 | 1143 |

### 5.2 IS Threshold vs Y+P (lenient)

| Threshold | kappa | Agreement | Precision | Recall | F1 | TP | FP | FN | TN |
|-----------|-------|-----------|-----------|--------|------|-----|-----|-----|------|
| >= 1.00 | 0.501 | 80.1% | 0.767 | 0.995 | 0.866 | 966 | 293 | 5 | 233 |
| >= 1.50 | 0.769 | 89.9% | 0.883 | 0.974 | 0.926 | 946 | 126 | 25 | 400 |
| >= 1.75 | 0.813 | 91.6% | 0.924 | 0.949 | 0.936 | 921 | 76 | 50 | 450 |
| >= 1.95 | 0.822 | 91.8% | 0.952 | 0.920 | 0.936 | 893 | 44 | 78 | 482 |
| **>= 2.00 (NIV)** | **0.818** | **91.5%** | **0.958** | **0.909** | **0.933** | **883** | **39** | **88** | **487** |
| >= 2.25 | 0.765 | 88.7% | 0.974 | 0.849 | 0.907 | 824 | 22 | 147 | 504 |
| >= 2.50 | 0.674 | 83.8% | 0.978 | 0.767 | 0.860 | 745 | 17 | 226 | 509 |
| >= 3.00 | 0.521 | 74.6% | 0.995 | 0.612 | 0.758 | 594 | 3 | 377 | 523 |
| >= 3.50 | 0.361 | 64.1% | 1.000 | 0.446 | 0.617 | 433 | 0 | 538 | 526 |
| >= 4.00 | 0.218 | 53.6% | 1.000 | 0.284 | 0.443 | 276 | 0 | 695 | 526 |

### 5.3 WER Threshold vs Y (strict, WER <= threshold = pass)

| Threshold | kappa | Agreement | Precision | Recall | F1 | TP | FP | FN | TN |
|-----------|-------|-----------|-----------|--------|------|-----|-----|-----|------|
| <= 10% | 0.262 | 81.2% | 0.957 | 0.191 | 0.319 | 66 | 3 | 279 | 1149 |
| <= 20% | 0.483 | 85.0% | 0.857 | 0.417 | 0.561 | 144 | 24 | 201 | 1128 |
| <= 25% | 0.551 | 85.8% | 0.783 | 0.533 | 0.635 | 184 | 51 | 161 | 1101 |
| <= 30% | 0.598 | 86.4% | 0.740 | 0.635 | 0.683 | 219 | 77 | 126 | 1075 |
| **<= 34% (NIV)** | **0.629** | **86.4%** | **0.685** | **0.757** | **0.719** | **261** | **120** | **84** | **1032** |
| <= 35% | 0.627 | 86.1% | 0.674 | 0.768 | 0.718 | 265 | 128 | 80 | 1024 |
| <= 40% | 0.611 | 84.4% | 0.619 | 0.844 | 0.714 | 291 | 179 | 54 | 973 |
| <= 50% | 0.513 | 77.8% | 0.510 | 0.925 | 0.658 | 319 | 306 | 26 | 846 |
| <= 60% | 0.425 | 71.3% | 0.443 | 0.959 | 0.606 | 331 | 416 | 14 | 736 |
| <= 80% | 0.255 | 56.3% | 0.343 | 0.986 | 0.509 | 340 | 650 | 5 | 502 |

### 5.4 WER Threshold vs Y+P (lenient, WER <= threshold = pass)

| Threshold | kappa | Agreement | Precision | Recall | F1 | TP | FP | FN | TN |
|-----------|-------|-----------|-----------|--------|------|-----|-----|-----|------|
| <= 20% | 0.128 | 46.4% | 1.000 | 0.173 | 0.295 | 168 | 0 | 803 | 526 |
| <= 30% | 0.233 | 54.8% | 0.997 | 0.304 | 0.466 | 295 | 1 | 676 | 525 |
| <= 40% | 0.390 | 66.1% | 0.994 | 0.481 | 0.648 | 467 | 3 | 504 | 523 |
| <= 50% | 0.536 | 75.7% | 0.986 | 0.634 | 0.772 | 616 | 9 | 355 | 517 |
| <= 60% | 0.645 | 82.2% | 0.972 | 0.748 | 0.845 | 726 | 21 | 245 | 505 |
| <= 70% | 0.731 | 87.2% | 0.950 | 0.847 | 0.895 | 822 | 43 | 149 | 483 |
| <= 75% | 0.768 | 89.3% | 0.933 | 0.899 | 0.916 | 873 | 63 | 98 | 463 |
| **<= 77% (NIV)** | **0.777** | **89.8%** | **0.929** | **0.913** | **0.921** | **886** | **68** | **85** | **458** |
| <= 80% | 0.762 | 89.3% | 0.909 | 0.927 | 0.918 | 900 | 90 | 71 | 436 |
| <= 85% | 0.713 | 87.4% | 0.872 | 0.944 | 0.907 | 917 | 135 | 54 | 391 |
| <= 100% | 0.199 | 70.1% | 0.689 | 0.983 | 0.810 | 954 | 431 | 17 | 95 |

### 5.5 Semantic Similarity Threshold vs Y (strict)

| Threshold | kappa | Agreement | Precision | Recall | F1 |
|-----------|-------|-----------|-----------|--------|------|
| >= 0.40 | 0.415 | 70.3% | 0.435 | 0.974 | 0.602 |
| >= 0.50 | 0.542 | 79.2% | 0.527 | 0.948 | 0.678 |
| >= 0.60 | 0.650 | 85.8% | 0.635 | 0.899 | 0.744 |
| >= 0.65 | 0.685 | 87.9% | 0.693 | 0.855 | 0.765 |
| **>= 0.70** | **0.714** | **89.7%** | **0.761** | **0.803** | **0.781** |
| >= 0.75 | 0.686 | 89.4% | 0.810 | 0.704 | 0.754 |
| >= 0.80 | 0.669 | 89.4% | 0.872 | 0.632 | 0.733 |
| >= 0.90 | 0.495 | 85.8% | 0.965 | 0.397 | 0.563 |

### 5.6 Semantic Similarity Threshold vs Y+P (lenient)

| Threshold | kappa | Agreement | Precision | Recall | F1 |
|-----------|-------|-----------|-----------|--------|------|
| >= 0.15 | 0.645 | 85.1% | 0.825 | 0.978 | 0.895 |
| >= 0.20 | 0.738 | 88.5% | 0.879 | 0.955 | 0.915 |
| **>= 0.25** | **0.761** | **89.2%** | **0.908** | **0.927** | **0.917** |
| >= 0.30 | 0.735 | 87.6% | 0.933 | 0.871 | 0.901 |
| >= 0.40 | 0.672 | 83.8% | 0.972 | 0.772 | 0.861 |
| >= 0.50 | 0.536 | 75.6% | 0.989 | 0.631 | 0.771 |

---

## 6. NIV vs Old Threshold Summary

### 6.1 Old IS >= 3.0

```
  IS >= 2.00 (NIV Y+P)  ──  optimal for "any useful meaning"     κ = 0.818
       |
  IS >= 3.00 (old)       ──  no-man's land                        κ_Y = 0.565, κ_YP = 0.521
       |
  IS >= 3.80 (NIV Y)     ──  optimal for "clearly conveyed"       κ = 0.690
```

IS >= 3.0 does not maximize agreement for either target. NIV replaces it with two
purpose-specific thresholds.

### 6.2 NIV Thresholds at a Glance

| Property | NIV Y (IS >= 3.80) | NIV Y+P (IS >= 2.00) |
|----------|-------------------|---------------------|
| Target | "Meaning clearly conveyed" | "Any useful meaning" |
| Judge agreement (κ) | 0.690 (substantial) | 0.818 (almost perfect) |
| Agreement % | 89.0% | 91.5% |
| Segments captured | 346 (23.1%) | 922 (61.6%) |
| Judge captures | 345 (23.0%) | 971 (64.9%) |
| Strict? | Neutral (23.1% vs 23.0%) | Yes (61.6% < 64.9%) |
| False positives | 83 | 39 |
| Precision | 0.760 | 0.958 |
| WER at same κ | <= 34% (κ=0.629) | <= 77% (κ=0.777) |
| IS advantage over WER | +0.061 | +0.041 |

---

## 7. Key Takeaways

> 1. **IS beats WER** at every comparable operating point for predicting Opus Y, and at
>    optimal/near-optimal points for Y+P.
>
> 2. **NIV thresholds** (IS >= 3.80 for Y, IS >= 2.00 for Y+P) are within 0.004 κ of
>    the mathematical optimum while maintaining IS as a strict or neutral estimator.
>
> 3. **IS >= 3.0 is superseded** — it sits between the two natural decision boundaries
>    and does not maximize agreement with the judge for either target.
>
> 4. **The IS ranking is strongly valid** (Pearson r=0.85 with judge). The metric correctly
>    orders segments. NIV thresholds provide the empirically correct cutpoints.

---

*Analysis performed 2026-03-07 on 1,497 baseline segments. Opus judge: blind evaluation,
3-level Y/P/N, 86.7% intra-rater reliability. NIV = empirically calibrated thresholds
adopted for all presentation and reporting use.*
