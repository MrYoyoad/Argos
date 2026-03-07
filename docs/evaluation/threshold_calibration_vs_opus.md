# Threshold Calibration: IS and WER vs Opus-as-a-Judge

**Date:** 2026-03-07
**Dataset:** 1,497 baseline segments, all judged by Claude Opus 4.6 (blind, 3-level Y/P/N)

---

## 1. The Question

Our IS framework uses IS >= 3.0 as the "properly captured" threshold. The presentation's
"Gap" slide uses WER <= 40% as the conventional "acceptable" line. **Are these the optimal
thresholds for agreeing with the Opus gold-standard judge?**

Short answer: **No.** Neither threshold maximizes agreement with the judge. This document
presents the full calibration analysis.

---

## 2. Opus Judge Ground Truth

| Code | Label | Count | Rate |
|------|-------|-------|------|
| **Y** | Meaning clearly conveyed | 345 | 23.0% |
| **P** | Some meaning preserved, key info lost | 626 | 41.8% |
| **N** | Wrong topic, hallucination, empty | 526 | 35.1% |

Two natural binary splits:
- **Strict (Y vs P+N):** "Did the output clearly convey the meaning?" (345 positive)
- **Lenient (Y+P vs N):** "Does the output have any useful meaning?" (971 positive)

---

## 3. Method: Cohen's Kappa Threshold Sweep

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

## 4. Optimal Thresholds

### 4.1 Strict Target: Y (meaning clearly conveyed)

| Metric | Optimal Threshold | kappa | Agreement | Precision | Recall | F1 |
|--------|-------------------|-------|-----------|-----------|--------|------|
| **Semantic Sim** | **>= 0.70** | **0.714** | **89.7%** | 0.761 | 0.803 | 0.781 |
| IS | >= 3.70 | 0.694 | 88.8% | 0.735 | 0.803 | 0.767 |
| WER | <= 34% | 0.629 | 86.4% | 0.685 | 0.757 | 0.719 |
| IS (ours: >= 3.0) | >= 3.00 | 0.565 | 80.6% | 0.546 | 0.945 | 0.692 |

**Finding:** Semantic similarity >= 0.70 is the single best predictor of Opus Y, beating
IS and WER. IS >= 3.70 (not 3.0) is the optimal IS threshold for this target. Our IS >= 3.0
threshold has high recall (94.5%) but low precision (54.6%) — it captures almost all Y
segments but also includes 271 segments the judge calls P or N.

### 4.2 Lenient Target: Y+P (any useful meaning)

| Metric | Optimal Threshold | kappa | Agreement | Precision | Recall | F1 |
|--------|-------------------|-------|-----------|-----------|--------|------|
| **IS** | **>= 1.95** | **0.822** | **91.8%** | 0.952 | 0.920 | 0.936 |
| IS | >= 2.00 | 0.818 | 91.5% | 0.958 | 0.909 | 0.933 |
| WER | <= 77% | 0.777 | 89.8% | 0.929 | 0.913 | 0.921 |
| Semantic Sim | >= 0.25 | 0.761 | 89.2% | 0.908 | 0.927 | 0.917 |
| IS (ours: >= 3.0) | >= 3.00 | 0.521 | 74.6% | 0.995 | 0.612 | 0.758 |

**Finding:** IS >= 1.95 (effectively IS >= 2.0, the Tier 3/Fair boundary) is the best
predictor of "any useful output" — almost perfect agreement (kappa=0.822). Our IS >= 3.0
has near-perfect precision (99.5%) but misses 38.8% of useful segments (recall=61.2%).

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
| **>= 3.70** | **0.694** | **88.8%** | **0.735** | **0.803** | **0.767** | **277** | **100** | **68** | **1052** |
| >= 3.75 | 0.692 | 88.9% | 0.748 | 0.783 | 0.765 | 270 | 91 | 75 | 1061 |
| >= 4.00 | 0.658 | 88.7% | 0.819 | 0.655 | 0.728 | 226 | 50 | 119 | 1102 |
| >= 4.50 | 0.397 | 83.6% | 0.923 | 0.313 | 0.468 | 108 | 9 | 237 | 1143 |

### 5.2 IS Threshold vs Y+P (lenient)

| Threshold | kappa | Agreement | Precision | Recall | F1 | TP | FP | FN | TN |
|-----------|-------|-----------|-----------|--------|------|-----|-----|-----|------|
| >= 1.00 | 0.501 | 80.1% | 0.767 | 0.995 | 0.866 | 966 | 293 | 5 | 233 |
| >= 1.50 | 0.769 | 89.9% | 0.883 | 0.974 | 0.926 | 946 | 126 | 25 | 400 |
| >= 1.75 | 0.813 | 91.6% | 0.924 | 0.949 | 0.936 | 921 | 76 | 50 | 450 |
| **>= 1.95** | **0.822** | **91.8%** | **0.952** | **0.920** | **0.936** | **893** | **44** | **78** | **482** |
| >= 2.00 | 0.818 | 91.5% | 0.958 | 0.909 | 0.933 | 883 | 39 | 88 | 487 |
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
| **<= 34%** | **0.629** | **86.4%** | **0.685** | **0.757** | **0.719** | **261** | **120** | **84** | **1032** |
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
| **<= 77%** | **0.777** | **89.8%** | **0.929** | **0.913** | **0.921** | **886** | **68** | **85** | **458** |
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

## 6. Summary: What Each Threshold Means

### 6.1 Comparison Table

| Question | Best Metric | Optimal Threshold | kappa | Interpretation |
|----------|------------|-------------------|-------|----------------|
| "Meaning clearly conveyed?" (Y) | Semantic Sim | >= 0.70 | 0.714 (substantial) | Single best predictor of full success |
| "Meaning clearly conveyed?" (Y) | IS | >= 3.70 | 0.694 (substantial) | Composite metric, slightly below semantic alone |
| "Meaning clearly conveyed?" (Y) | WER | <= 34% | 0.629 (substantial) | Traditional metric, weakest of the three |
| "Any useful meaning?" (Y+P) | IS | >= 1.95 | 0.822 (almost perfect) | IS is the best predictor of useful output |
| "Any useful meaning?" (Y+P) | WER | <= 77% | 0.777 (substantial) | Much higher than conventional 40% cutoff |
| "Any useful meaning?" (Y+P) | Semantic Sim | >= 0.25 | 0.761 (substantial) | Very low bar — most non-hallucinated output passes |

### 6.2 Where Our IS >= 3.0 Actually Sits

IS >= 3.0 is **between** the two optimal thresholds:

```
  IS >= 1.95  ──  optimal for Y+P (any useful meaning)     kappa = 0.822
       |
  IS >= 3.00  ──  OUR THRESHOLD (conservative choice)      kappa_Y = 0.565, kappa_YP = 0.521
       |
  IS >= 3.70  ──  optimal for Y (meaning clearly conveyed) kappa = 0.694
```

It is too lenient to capture Y-only (includes 271 P/N segments) and too strict to capture
Y+P (misses 377 useful segments). It does not maximize agreement with the Opus judge for
**either** binary split.

### 6.3 Why IS >= 3.0 Was Chosen Anyway

IS >= 3.0 was a **design-time qualitative decision**, not an empirically optimized threshold:

1. **Designed before the judge existed.** The IS rubric (Section 4 of the methodology) was
   created first. The Opus judge evaluation came later as validation. The threshold was set
   by examining ref/hyp examples and asking "where does human comprehension break down?"

2. **Conservative by intent.** The IS framework deliberately chose a threshold that errs on
   the side of undercounting success. "Properly captured" was meant to mean "a human would
   confidently understand the output" — closer to Y than to Y+P.

3. **Stable across configurations.** IS >= 3.0 has consistent behavior across 16 decode
   configs (kappa range 0.62-0.86 for llm_context_prob agreement). Optimal thresholds found
   on one config might not generalize.

4. **Round number at tier boundary.** IS 3.0 is the Tier 3/Tier 4 boundary (Fair/Good).
   Moving to 3.70 would split Tier 4 arbitrarily.

### 6.4 What This Means for the "Gap" Slide

The "Gap: Where WER Lies Most" slide uses two thresholds:

- **Y-axis: IS >= 3.0** — Our conservative "captured" line. The Opus judge's natural Y
  boundary would be IS >= 3.70 (fewer segments in the gap but each more confidently useful).
  The Y+P boundary would be IS >= 1.95 (many more segments, but includes partial meaning).

- **X-axis: WER > 40%** — Conventional ASR "acceptable" threshold. For Y-only, the optimal
  WER threshold is <= 34% (kappa=0.629). For Y+P, it's <= 77% (kappa=0.777). The 40% line
  is not optimal for either target but represents industry convention.

Neither axis threshold is empirically optimal. Both are **conventions** that serve the
slide's rhetorical purpose: demonstrating that WER discards useful output.

---

## 7. Recommendation

If recalibrating IS thresholds in the future:

| Use Case | Recommended Threshold | Rationale |
|----------|----------------------|-----------|
| **Conservative reporting** ("properly captured") | IS >= 3.0 (current) | Established, stable, errs on undercounting |
| **Strict quality gate** ("meaning clearly conveyed") | IS >= 3.70 | Best agreement with Opus Y (kappa=0.694) |
| **Inclusive capture** ("any useful meaning") | IS >= 2.0 | Best agreement with Opus Y+P (kappa=0.818) |
| **Salvage-aware** | IS >= 3.0 OR llm_context_prob >= 0.5 | Current salvage approach, 50.9% capture |

The key insight is that **IS rankings are strongly valid** (Pearson r=0.85 with judge) —
the metric correctly orders segments from worst to best. The disagreement is only about
**where to draw the line**, which is ultimately a use-case decision.

---

## 8. Key Takeaway

> **IS >= 3.0 is not the threshold that best agrees with Opus-as-a-Judge. It is a
> conservative design-time choice that sits between the judge's natural "clearly conveyed"
> boundary (IS >= 3.70) and "any useful meaning" boundary (IS >= 1.95). The IS ranking
> itself is strongly validated (r=0.85), but the binary cutpoint is a policy decision,
> not an empirical optimum.**

---

*Analysis performed 2026-03-07 on 1,497 baseline segments. Opus judge: blind evaluation,
3-level Y/P/N, 86.7% intra-rater reliability.*
