# IS Metric — Principal Component Analysis

**Argos — The Orchard**
**Date:** 2026-03-07
**Dataset:** 1,497 segments (full AVSpeech baseline, February 2026)

---

## 1. Purpose

The IS formula combines 6 signals into a single score. This analysis uses Principal Component Analysis (PCA) to determine how many **independent dimensions** those 6 signals actually measure.

Previous documentation incorrectly labeled a correlation-clustering observation as "PCA." This document presents the actual PCA results.

---

## 2. Method

1. Extract the 6 raw IS signals for all 1,497 segments:
   - Semantic Similarity, Phonetic Similarity, Inverse WER (1 - WER/100), Inverse WWER (1 - WWER/100), NEA F1, Length Ratio
2. Standardize all signals (zero mean, unit variance) — required because the signals have different scales
3. Run PCA on the 6 standardized signals
4. Interpret components using Kaiser criterion (eigenvalue > 1), scree analysis, and loading patterns

**Implementation:** Standard scikit-learn `PCA()` on `StandardScaler`-transformed data.

---

## 3. Results

### 3.1 Explained Variance

| PC | Eigenvalue | % Variance | Cumulative % | Kaiser? |
|----|-----------|------------|-------------|---------|
| **PC1** | **4.107** | **68.4%** | 68.4% | Yes |
| **PC2** | **1.168** | **19.5%** | 87.9% | Yes |
| PC3 | 0.309 | 5.1% | 93.0% | No |
| PC4 | 0.237 | 3.9% | 97.0% | No |
| PC5 | 0.151 | 2.5% | 99.5% | No |
| PC6 | 0.032 | 0.5% | 100.0% | No |

**Kaiser criterion retains 2 components** (eigenvalue > 1). The first 2 PCs explain 87.9% of total variance. Adding PC3 reaches 93.0%.

### 3.2 Component Loadings

Each value shows how strongly an original signal contributes to each principal component:

| Signal | PC1 | PC2 | PC3 |
|--------|-----|-----|-----|
| **Semantic** | +0.445 | +0.057 | +0.140 |
| **Phonetic** | +0.466 | +0.184 | -0.331 |
| **InvWER** | +0.431 | -0.367 | -0.334 |
| **InvWWER** | +0.455 | -0.061 | -0.250 |
| **NEA F1** | +0.430 | -0.001 | +0.830 |
| **LengthRatio** | +0.083 | +0.908 | -0.093 |

### 3.3 Communalities (Variance Explained per Variable)

How much of each signal's variance is captured by the first N principal components:

| Signal | By PC1 | By PC1-2 | By PC1-3 |
|--------|--------|----------|----------|
| Semantic | 0.813 | 0.817 | 0.823 |
| Phonetic | 0.890 | 0.930 | 0.963 |
| InvWER | 0.764 | 0.922 | 0.956 |
| InvWWER | 0.851 | 0.855 | 0.874 |
| NEA F1 | 0.761 | 0.761 | 0.973 |
| LengthRatio | 0.028 | 0.991 | 0.993 |

---

## 4. Interpretation

### PC1: General Quality (68.4%)

All 5 content signals load nearly equally on PC1 (0.43-0.47). Length Ratio barely contributes (0.08). This is a **general quality factor** — when a segment is good, ALL content signals are good together. When it's bad, they're all bad together.

This makes physical sense: the visual encoder either captures the speech signal or it doesn't. When it does, words are right (WER), important words are right (WWER), sounds are right (Phonetic), meaning is right (Semantic), and names are right (NEA). These are not 5 independent things — they are 5 views of the same underlying quality: **visual encoder signal strength**.

**Key finding:** Semantic Similarity loads on PC1 at 0.445 — virtually identical to the word-accuracy signals (0.43-0.47). It is NOT an independent dimension. The old claim that Semantic represents a separate "meaning preservation" dimension is incorrect.

### PC2: Output Length (19.5%)

Length Ratio dominates PC2 (loading 0.908). The only other notable loading is InvWER at -0.367 — longer outputs tend to have higher WER (more words = more chances for errors).

This captures the **output sanity** dimension: did the model generate roughly the right amount of text? This is independent of whether the content is correct (PC1).

### PC3: Entity Swing (5.1%)

NEA F1 dominates PC3 (loading 0.830), with negative loadings on Phonetic (-0.331) and InvWER (-0.334). This captures cases where entity accuracy diverges from general word accuracy — segments where names/numbers are correct but surrounding words are wrong, or vice versa.

PC3 is below the Kaiser criterion (eigenvalue 0.31 < 1.0) and explains only 5.1% of variance. It is a minor refinement, not a major dimension.

---

## 5. Corrected "Dimensions of Quality" Summary

### What PCA Actually Shows (2 Dimensions)

| Dimension | PC | Variance | What It Measures | Key Signals |
|-----------|-----|---------|------------------|-------------|
| **Signal Quality** | PC1 | 68.4% | Did the visual encoder capture the speech? | All 5 content signals equally (0.43-0.47) |
| **Output Length** | PC2 | 19.5% | Did the model generate the right amount of text? | Length Ratio (0.91) |

Together: **87.9%** of total variance.

### What the Old Claim Said (Wrong)

> "The 6 IS signals collapse into 3 independent dimensions: word accuracy (60%), meaning preservation (28.5%), output sanity (9.1%)."

This was based on correlation clustering and covariance decomposition, not PCA. The errors:

1. **Semantic is not independent of word accuracy.** PCA shows Semantic loads on PC1 at 0.445, right alongside the word-accuracy signals. Correlation analysis already showed Semantic correlates at r=0.82 with Phonetic — PCA confirms they measure overlapping constructs.

2. **The percentages were formula weights, not PCA eigenvalues.** "60%" was 4 signals × 15% weight each. "28.5%" was the covariance contribution of the Semantic component. These are properties of the IS formula's arithmetic, not of the underlying data structure.

3. **There are 2 dimensions, not 3.** Kaiser criterion retains 2 PCs. The "entity swing" (PC3) exists but explains only 5.1% — it's a minor effect, not a third dimension.

### What This Means for IS

The PCA result is actually **good news** for the IS formula:

- **PC1 validates the design.** The 5 content signals measuring the same underlying quality confirms that the IS formula is internally consistent — all 5 signals point the same direction, so the weighted sum is a reliable composite.
- **Semantic's higher weight (0.25 vs 0.15) is justified.** Even though Semantic is not independent of word accuracy, it captures the meaning-preservation aspect that pure word metrics miss. Its higher weight gives appropriate credit for paraphrasing (different words, same meaning).
- **Length Ratio is truly independent.** PC2 confirms that output length varies independently of content quality. The 15% weight on Length Ratio is appropriate for catching signal loss and hallucination.

---

## 6. Data Availability

- **Source data:** [intelligibility_scores.csv](intelligibility/intelligibility_scores.csv) (1,497 segments, all 6 raw signals)
- **Correlation analysis:** [is_correlation_analysis.md](is_correlation_analysis.md) (inter-signal correlations, variance decomposition, cross-config validation)
- **IS methodology:** [intelligibility_methodology.md](intelligibility_methodology.md) (signal definitions, formula, examples)