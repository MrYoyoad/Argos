# IS Cross-Configuration Validation & LLM Judge Analysis

**Parent document:** [is_correlation_analysis.md](is_correlation_analysis.md) (Sections 0-9: core correlation analysis)
**Date:** 2026-03-02

---

## 10. Cross-Configuration Analysis (16 Configs)

*(Added 2026-03-02. IS scores computed from ref/hyp text for all 16 experiment configurations.)*

IS components (semantic_sim, phonetic_sim, length_ratio) were computed from scratch for all configs using the same pipeline as the baseline. Validation: recomputed baseline IS correlates at r=0.999 with the original scores (MAE=0.05 — rounding/float differences only).

### 10.1 Datasets

| Dataset | Segments | Configs |
|---------|----------|---------|
| Tuning subset | 107 (same segments across configs) | 13 configs: exp_A (baseline), exp_B-M (parameter variants) |
| Full decode | 1,497 | 3 configs: baseline_full, full_decode_C (lenpen=1), full_decode_J (lenpen=1+sampling) |

### 10.2 IS vs Component Correlation Stability

How stable are IS-component correlations across different decode configurations?

| Component | Mean r | Std r | Min r | Max r | Range | Verdict |
|-----------|--------|-------|-------|-------|-------|---------|
| **Semantic** | **0.914** | 0.017 | 0.890 | 0.967 | 0.076 | Very stable |
| **Phonetic** | **0.914** | 0.059 | 0.698 | 0.981 | 0.283 | Stable except exp_H (lenpen=2) |
| **NEA F1** | **0.851** | 0.023 | 0.820 | 0.908 | 0.088 | Very stable |
| WER | -0.764 | 0.163 | -0.949 | -0.453 | 0.495 | Unstable — lenpen configs disrupt WER-IS relationship |
| WWER | -0.804 | 0.203 | -0.944 | -0.276 | 0.668 | Unstable — same configs affected |
| Length Ratio | -0.021 | 0.368 | -0.559 | 0.857 | 1.416 | Highly unstable — sign flips across configs |

**Key finding:** Semantic, Phonetic, and NEA F1 are **robust signals** — their correlation with IS is stable regardless of decode parameters. WER and WWER become unreliable when length penalty is applied (lenpen > 0 causes longer outputs that inflate WER while IS stays similar). Length Ratio is the most volatile signal, flipping sign depending on whether the config tends to over-generate or truncate.

### 10.3 Full Decode Comparison (1,497 segments)

| Config | Mean IS | Captured (IS>=3) | Mean WER | Mean Semantic | Mean Phonetic |
|--------|---------|-----------------|----------|---------------|---------------|
| baseline_full | 2.485 | 38.7% | 64.1% | 0.437 | 0.505 |
| full_decode_C (lenpen=1) | 2.535 | 38.5% | 79.3% | 0.444 | 0.545 |
| full_decode_J (lenpen=1+sampling) | **2.571** | **40.5%** | 78.9% | 0.443 | 0.543 |

Config J has the highest IS (+0.086 over baseline) and capture rate (+1.8pp) despite having significantly higher WER (+14.8pp). This demonstrates IS's advantage over WER: the longer outputs from lenpen=1 contain more errors by WER's count but preserve more meaning (higher semantic and phonetic similarity).

### 10.4 Inter-Config IS Correlation (Same 107 Segments)

How much does changing decode parameters change the per-segment IS ranking?

| Config Pair | r | Interpretation |
|-------------|---|----------------|
| exp_A ↔ exp_B (drop rep_penalty) | **0.998** | Virtually identical |
| exp_A ↔ exp_L (sampling temp=0.3) | **0.969** | Very similar |
| exp_A ↔ exp_G (greedy) | **0.924** | Similar |
| exp_A ↔ exp_H (lenpen=2) | **0.872** | Moderate divergence |
| exp_A ↔ exp_D (lenpen=-0.5) | **0.603** | Significant divergence — truncation changes segment rankings |
| baseline_full ↔ full_decode_C | **0.940** | Stable at scale |
| baseline_full ↔ full_decode_J | **0.932** | Stable at scale |
| full_decode_C ↔ full_decode_J | **0.984** | Nearly identical (sampling adds minimal noise) |

**Most configs produce nearly identical per-segment IS rankings** (r > 0.92). The exceptions are extreme parameter choices: negative length penalty (exp_D, r=0.60) causes truncation that reorders segments, and lenpen=2 (exp_H, r=0.87) over-generates enough to shift rankings.

### 10.5 Variance Contribution Stability

Does the relative importance of each signal change across configs?

| Config | Sem% | Pho% | WER% | WWER% | NEA% | LR% |
|--------|------|------|------|-------|------|-----|
| **Mean (16 configs)** | **29.1%** | **13.8%** | **16.3%** | **15.5%** | **17.4%** | **7.9%** |
| Std | 0.9% | 1.6% | 0.7% | 0.7% | 0.9% | 3.2% |
| **baseline_full** | 28.4% | 14.6% | 15.7% | 15.1% | 17.3% | 9.0% |
| exp_D (lenpen=-0.5) | 27.1% | 15.3% | 14.0% | 13.8% | 14.3% | **16.6%** |
| exp_H (lenpen=2) | 28.2% | **8.3%** | 16.3% | 14.5% | 17.2% | **16.4%** |

Semantic (29%), NEA (17%), WER (16%), WWER (16%) are **stable across all configs** (std < 1%). Phonetic varies slightly (std=1.6%). **Length Ratio is the only volatile contributor** — it jumps from 5% to 17% for configs that cause extreme over-generation (lenpen=2) or truncation (lenpen=-0.5), where length anomalies become a dominant signal.

### 10.6 Implications

1. **Semantic similarity and NEA F1 are the most reliable IS components** — stable across all 16 configs, insensitive to decode parameter choices.
2. **WER is misleading across configs** — configs with lenpen > 0 inflate WER without degrading IS, because longer outputs contain more word errors but also more semantic content. This validates the motivation for creating IS over raw WER.
3. **Length Ratio is a confound, not a signal** — its contribution and even its sign depend entirely on the decode config. In future IS versions, reducing its weight or making it config-aware could improve robustness.
4. **Most decode parameters don't change segment rankings** — r > 0.92 across most pairs means the "hard" and "easy" segments are consistent regardless of config. The bottleneck is the visual encoder, not the decode strategy.

---

## 11. LLM Salvage Analysis: Recoverable Predictions That Metrics Undercount

The LLM heuristic's high recall (99.2%) and intentional optimism (precision 78.2%) identifies **165 segments** where `llm_context_prob >= 0.5` but `IS < 3.0`. These represent cases where a domain-aware viewer would understand the lip-reading output despite metric-level failure.

| Metric | Value |
|--------|-------|
| Divergent segments (LLM >= 0.5, IS < 3.0) | 165 / 900 failed (18.3%) |
| Effective capture rate (IS + salvage) | 762 / 1,497 (50.9%) vs 597 (39.9%) |
| Uplift | +11.0 percentage points (+27.6% relative) |

The 165 segments break down into 6 recovery categories: hidden gems (54), semantic preservation (57), phonetic bridge (93), entity-preserved (44), structure match (74), WER over-punishment (27). Categories overlap as segments can exhibit multiple recovery signals simultaneously.

This validates the LLM heuristic's design philosophy: it is intentionally generous because context recovery is real — a viewer watching a cooking tutorial will mentally correct "flour" → "flower" automatically.

Full analysis with curated examples: [llm_salvage/llm_salvage_analysis.md](llm_salvage/llm_salvage_analysis.md)

---

## 12. Methodology Notes

- **Pearson r** measures linear correlation; **Spearman ρ** measures monotonic (rank) correlation
- Where Spearman >> Pearson (e.g., WER), the relationship is monotonic but nonlinear — extreme values compress the linear fit
- **Variance contribution** uses covariance decomposition: % = Cov(IS, weighted_component) / Var(IS)
- **Per-tier correlations** have reduced sample sizes (239-336 per tier) and narrower ranges, so absolute r values are lower than the global correlations
- Sections 1-9 computed on the full 1,497-segment baseline dataset (February 2026)
- Section 10 computed across 16 experiment configurations (13 × 107-segment tuning subset + 3 × 1,497-segment full decodes)
- IS recomputation validated against original scores: r=0.999, MAE=0.05 (floating-point rounding only)
- Finetuning evaluation (Exp A r=16, Exp B r=64) decode is in progress — correlation analysis will be updated when results are available

---

## 13. Gold Standard LLM Judge Validation

**Date:** 2026-03-03 | **Full report:** [llm_judge/llm_judge_analysis.md](llm_judge/llm_judge_analysis.md)

Claude Opus 4.6 evaluated all 1,497 hypothesis-reference pairs using holistic LLM reasoning (3-level Y/P/N scale, blind to all metrics). This provides an independent "gold standard" to validate the IS framework.

### Key Results

| Metric | Value |
|--------|-------|
| **LLM strict capture (Y only)** | 345 / 1,497 (23.0%) |
| **LLM lenient capture (Y + P)** | 971 / 1,497 (64.9%) |
| IS >= 3.0 capture | 597 / 1,497 (39.9%) |
| IS + salvage capture | 762 / 1,497 (50.9%) |
| **Intra-rater reliability** | 86.7% exact, 100% lenient (30 duplicates) |

### Agreement with IS

| Comparison | Kappa | Accuracy | Precision | Recall | F1 |
|------------|-------|----------|-----------|--------|-----|
| LLM Y vs IS >= 3.0 (strict) | 0.565 | 0.806 | 0.945 | 0.546 | 0.692 |
| LLM Y+P vs IS >= 3.0 (lenient) | 0.521 | 0.746 | 0.612 | 0.995 | 0.758 |

**Interpretation:** The LLM judge is substantially more conservative than IS for "full success" (Y=23% vs IS>=3.0=40%) but substantially more generous for "any useful output" (Y+P=65% vs IS>=3.0=40%). The 42% partial zone (P) — where structure and key words survive but semantic meaning or detail is lost — is the critical boundary that IS collapses into a binary pass/fail.

### 3×5 Confusion Matrix (LLM Y/P/N × IS Tier 1-5)

| LLM | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|-----|--------|--------|--------|--------|--------|
| Y | 0 | 2 | 17 | 100 | 226 |
| P | 5 | 81 | 272 | 218 | 50 |
| N | 234 | 253 | 36 | 3 | 0 |

Clean separation: Y concentrates in tiers 4-5, N in tiers 1-2, P spans tiers 2-4. Only 22 boundary disagreements (LLM=Y but IS<3, or LLM=N but IS>=3).

### Correlation with IS Signals

| Signal | Pearson r with LLM judge |
|--------|-------------------------|
| IS | 0.850 |
| Semantic Sim | 0.846 |
| llm_context_prob | 0.823 |
| Phonetic Sim | 0.806 |
| WWER | -0.741 |
| WER | -0.714 |

### Partial Judgment Analysis

In the 626 P-coded segments, the most commonly preserved elements are structure (88.8%) and key content words (66.6%). The most commonly lost elements are detail (55.4%) and semantic meaning (55.1%). The VSP model reliably produces grammatically well-formed output with recognizable content words, but frequently loses the specific meaning and fine-grained detail.

### Implications for IS Framework

1. **IS >= 3.0 is well-calibrated as a threshold:** 94.5% of LLM=Y segments score IS >= 3.0 (precision), and only 3 LLM=N segments pass IS >= 3.0
2. **IS misses partial success:** 377 segments are Y+P by LLM but IS < 3.0 — these have useful structure/words despite metric-level failure
3. **The llm_context_prob salvage hypothesis is validated:** The 165 salvage segments align with the P-heavy boundary zone identified by the LLM judge
