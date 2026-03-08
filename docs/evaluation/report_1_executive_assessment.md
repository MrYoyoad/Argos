# VSP-LLM Model Evaluation: Executive Technical Assessment

> **SUPERSEDED (March 2026):** This report was based on the preliminary `english_1k` run (860 segments from an incomplete pipeline run). It has been superseded by the full `english_full` baseline (1,497 segments, Feb 18 2026) which is the authoritative evaluation. This report is retained for historical reference only — all metrics, recommendations, and analysis should be sourced from the `english_full_results/` dataset and the IS correlation / LLM salvage analyses instead.

**Document Classification:** Technical Evaluation Report (HISTORICAL)
**Date:** February 17, 2026
**Dataset:** english_1k (860 segments — preliminary run, superseded by english_full)
**Model:** VSP-LLM (Visual Speech Processing with Large Language Models)
**Reference Paper:** Yeo et al., "Where Visual Speech Meets Language: VSP-LLM Framework for Efficient and Context-Aware Visual Speech Processing" (arXiv:2402.15151, May 2024)

---

## 1. Executive Summary

We evaluated VSP-LLM, an LLM-based lip-reading model, on 860 real-world video segments sourced from approximately 1,000 YouTube videos across diverse domains (educational content, vlogs, product reviews, cooking channels, etc.). The model was evaluated against Whisper-generated ground-truth transcriptions using Word Error Rate (WER) and Named Entity Accuracy (NEA) metrics.

### Key Findings

| Metric | Paper Benchmark (LRS3) | Our Results (english_1k) | Gap |
|--------|----------------------|--------------------------|-----|
| Best-case WER | 25.4% | — | — |
| Mean segment WER | ~25-30% | **67.0%** | 2.5x worse |
| Median segment WER | — | **63.8%** | — |
| Corpus-level WER | — | **125.5%** | — |
| Named Entity F1 | Not reported | **38.8%** | — |

**Bottom line:** The model performs 2.5-5x worse on real-world video than the paper's benchmark claims. Only 11.4% of segments achieve acceptable quality (WER ≤ 20%), while 53.4% are poor (WER > 60%) and 20.6% are catastrophically wrong (WER ≥ 100%). The model cannot be relied upon for production use in its current form.

---

## 2. Evaluation Methodology

### 2.1 Dataset: english_1k

- **Source:** ~1,000 YouTube videos, English-language
- **Processing:** Videos segmented into clips ≤ 12 seconds using the VSP pipeline
- **Ground truth:** Whisper ASR transcriptions (verified against original audio)
- **Total evaluated segments:** 860
- **Content diversity:** Educational lectures, product reviews, vlogs, cooking shows, radio/podcasts, casual conversation, technical tutorials

### 2.2 Model Configuration

The VSP-LLM model was deployed with the following architecture and settings:

| Component | Configuration |
|-----------|--------------|
| Visual encoder | AV-HuBERT Large (pre-trained on LRS3 + VoxCeleb2) |
| LLM backbone | LLaMA-2-7B with QLoRA (rank 16) |
| Deduplication | 200 K-means clusters |
| Beam search width | 20 |
| Length penalty | 0.0 |
| Repetition penalty | 1.2 |
| No-repeat n-gram | 3 |
| Instruction prompt | "Recognize this speech in English. Input :" |

### 2.3 Metrics

| Metric | Description |
|--------|-------------|
| **WER** (Word Error Rate) | Levenshtein edit distance between reference and hypothesis, normalized by reference word count. Lower is better. 0% = perfect, 100% = every word wrong. Can exceed 100% when model inserts extra words. |
| **Corpus WER** | Total errors across all segments divided by total reference words. Reflects global accuracy. |
| **NEA** (Named Entity Accuracy) | Measures capture of high-value content words (proper nouns, numbers, named entities). Reported as Recall, Precision, and F1. |
| **WWER** (Weighted WER) | WER variant where errors on important words (names, numbers) count 2x and errors on function words (the, a, is) count 0.5x. |

---

## 3. Results

### 3.1 Overall Performance

```
                    PERFORMANCE DISTRIBUTION (860 segments)

    WER Range        Count    Percentage    Assessment
    ──────────────────────────────────────────────────────────
    0% (Perfect)        16       1.9%       Exact match
    1-10%               37       4.3%       Excellent
    11-20%              45       5.2%       Good
    21-30%              65       7.6%       Acceptable
    31-40%              85       9.9%       Fair
    41-50%              62       7.2%       Mediocre
    51-60%              91      10.6%       Poor
    61-70%              59       6.9%       Poor
    71-80%              75       8.7%       Very poor
    81-90%              48       5.6%       Very poor
    91-99%              100     11.6%       Near-total failure
    100%+               177     20.6%       Catastrophic / hallucinated
    ──────────────────────────────────────────────────────────
    TOTAL               860     100.0%
```

### 3.2 Quality Tier Summary

| Quality Tier | WER Range | Segments | % of Total | Interpretation |
|-------------|-----------|----------|------------|----------------|
| Usable | 0-20% | 98 | **11.4%** | Output can be trusted with minor corrections |
| Marginal | 21-40% | 150 | **17.4%** | Core meaning may be preserved, significant errors |
| Poor | 41-60% | 153 | **17.8%** | Meaning substantially distorted |
| Unusable | 61-99% | 282 | **32.8%** | Output is mostly wrong |
| Hallucinated | 100%+ | 177 | **20.6%** | Output is fabricated — no relation to actual speech |

**Key observation:** Nearly 9 out of 10 segments (88.6%) have WER above 20%, meaning the model's output is unreliable for the vast majority of real-world inputs.

### 3.3 Corpus-Level vs. Segment-Level WER

| Metric | Value |
|--------|-------|
| Mean segment WER | 67.0% |
| Median segment WER | 63.8% |
| Corpus-level WER | **125.5%** |

The corpus-level WER (125.5%) exceeds 100%, which means the model generates **more errors than there are words in the reference**. This is primarily driven by excessive word insertions — the model generates fluent but fabricated text, inflating the total error count beyond the total reference word count.

### 3.4 Named Entity Accuracy

| NEA Metric | Value |
|------------|-------|
| Mean Recall | 39.2% |
| Mean Precision | 55.4% |
| Mean F1 | 38.8% |
| Segments with missed entities | 731/860 (85.0%) |

Named entities — proper nouns, numbers, technical terms — are the most important words for comprehension. The model misses at least one named entity in 85% of segments. This severely limits the practical utility of the output, as these are precisely the words a human reader cannot infer from context.

### 3.5 Segment Duration Effects

| Segment Length | Mean WER | Median WER | % with WER ≤ 30% |
|---------------|----------|------------|-------------------|
| 1-5 words | 128.5% | 100.0% | ~5% |
| 6-10 words | 72.3% | — | ~15% |
| 11-20 words | ~60% | — | ~22% |
| 21+ words | 56.6% | — | ~25% |

Short segments (1-5 reference words) are essentially unreadable, with a mean WER of 128.5%. The model requires substantial visual context (longer clips) to produce even marginally useful output. This aligns with the paper's own finding that WER drops significantly on longer videos (Figure 4: 35% → 12.9% from 0-2s to 6+s on LRS3).

---

## 4. Hallucination Analysis

### 4.1 The Hallucination Problem

20.6% of segments (177/860) have WER ≥ 100%. In these cases, the model generates text that bears no relation to the actual spoken content. Because the model uses LLaMA-2 as its decoder, the hallucinated text is grammatically fluent and contextually plausible — making it **indistinguishable from correct output without ground truth**.

### 4.2 Hallucination Examples

| Reference (actual speech) | Hypothesis (model output) | WER |
|--------------------------|---------------------------|-----|
| "let's see a half a cup of" | "i have to say thank you" | 100% |
| "it'll work" | "but" | 100% |
| "amateur radio call sign is k5acl" | "right here on 95 a c e l and" | 150% |
| "this is the camera and this is it the adapter" | "so that's why i'm here today thank you" | 100% |
| "has now carried you home" | "i dare you to hear the new home" | 140% |
| "those arrays that we have not declared" | "those are realities that we have to deal with" | 71% |

### 4.3 Why Hallucination Occurs

The VSP-LLM architecture works by encoding lip movements into visual features, then passing them to LLaMA-2 for text generation. When the visual features are ambiguous (as they often are — many different words look identical on the lips), LLaMA-2 falls back to its language model prior and generates text that is **linguistically probable but visually unsupported**.

This is a fundamental architectural risk of LLM-based decoders: they prioritize fluency over faithfulness to the input signal.

---

## 5. Why Results Differ from Paper Claims

### 5.1 Domain Mismatch

The paper evaluates on **LRS3** (Afouras et al., 2018), a curated dataset of TED and TEDx talks. LRS3 has:
- **Controlled lighting** (professional stage lighting)
- **Frontal-facing speakers** (TED talk format)
- **Clear, articulate speech** (practiced presenters)
- **Standard vocabulary** (academic English)
- **Studio-quality video** (professional cameras)

Our `english_1k` dataset has:
- **Variable lighting** (indoor, outdoor, mixed)
- **Varied head poses** (side profiles, movement, occlusion)
- **Casual/accented speech** (natural conversation)
- **Domain-specific vocabulary** (technical terms, brand names, slang)
- **Consumer-quality video** (webcams, phones, screen recordings)

The model was **trained on LRS3-like data** and has never seen the distribution represented by wild YouTube content. This domain gap is the primary cause of the performance degradation.

### 5.2 Benchmark Optimism (a common ML pattern)

The gap between benchmark and real-world performance is well-documented in ML research. Benchmarks tend to overstate real-world performance because:
1. Models are optimized (hyperparameters tuned) on the benchmark distribution
2. Benchmark data is curated and clean
3. Real-world data contains edge cases absent from benchmarks
4. Evaluation metrics computed on in-domain data don't transfer

For lip-reading specifically, the visual ambiguity problem (homophenes) is manageable on LRS3 because the vocabulary is predictable and the LLM can use its language prior effectively. On diverse YouTube content, the vocabulary is unpredictable, making the language prior a liability rather than an asset (it generates plausible but wrong text).

### 5.3 Segment Length Distribution

The paper reports best performance on segments > 6 seconds (12.9% WER). Many of our 860 segments are shorter, giving the model insufficient visual context. The paper itself shows that short segments (0-2 seconds) achieve only ~35% WER even on LRS3.

---

## 6. Can Good and Bad Results Be Separated?

A critical practical question: if we deploy this model, can we automatically identify which outputs to trust?

### 6.1 Available Signals (without ground truth)

| Signal | Correlation with WER | Usefulness |
|--------|---------------------|------------|
| Hypothesis word count | r = -0.166 | Weak |
| Segment duration | r = -0.151 | Weak |
| Words per second | ~0 | None |
| Repetitive patterns | None detected | None |

### 6.2 Best Filtering Heuristic

| Filter Rule | Precision | Recall | F1 |
|-------------|-----------|--------|-----|
| hyp ≥ 7 words | 20.4% | 92.6% | 33.4% |
| duration ≥ 5s | 23.6% | 59.3% | 33.8% |
| duration ≥ 5s + hyp ≥ 4 words | 23.9% | 59.3% | 34.1% |

**Conclusion:** No available production signal reliably separates good from bad predictions. The best heuristic achieves only 24% precision — meaning **3 out of 4 segments flagged as "good" are actually wrong**. The model does not currently expose confidence scores that might improve this.

### 6.3 LLM Salvage Analysis (March 2026 Update)

Subsequent analysis using the Claude-designed Intelligibility Score (IS) framework and LLM heuristic (`llm_context_prob`) revealed that traditional metrics systematically undercount the system's useful output. Of 900 segments classified as failures (IS < 3.0), **165 segments (18.3%)** have recoverable meaning that a domain-aware viewer would understand — identified by `llm_context_prob >= 0.5`.

| Assessment Method | Segments Useful | Rate |
|-------------------|-----------------|------|
| WER-only (WER ≤ 20%) | ~98 | 11.4% |
| IS (IS ≥ 3.0) | 601 | 40.1% |
| **IS + LLM salvage** | **766** | **51.1%** |

The 165 salvageable segments include cases where high phonetic similarity (natural lip-reading confusions), preserved semantic meaning, or intact named entities make the output usable despite high WER. This raises the effective capture rate from 40.1% to 51.1% — roughly 1 in 2 segments rather than 2 in 5.

Full analysis: [llm_salvage/llm_salvage_analysis.md](llm_salvage/llm_salvage_analysis.md)

### 6.4 LLM-as-a-Judge Cross-Validation (March 2026)

An independent gold standard evaluation using Claude Opus 4.6 judged all 1,497 baseline segments on a 3-level scale (Y = meaning conveyed, P = partial, N = meaning lost), blind to all metrics. This provides external validation of the IS framework.

| Measure | Value |
|---------|-------|
| Pearson r (LLM judge vs IS) | **0.850** |
| Spearman ρ | **0.858** |
| Segment-level agreement | 88–90% |
| Boundary disagreements | 22 / 1,497 (1.5%) |
| Intra-rater reliability | 86.7% exact (30 duplicates) |

**Capture rate comparison:**

| Method | Useful Segments | Rate |
|--------|-----------------|------|
| WER-only (WER ≤ 20%) | ~98 | 11.4% |
| IS (IS ≥ 3.0) | 601 | 40.1% |
| IS + LLM salvage | 766 | 51.1% |
| LLM judge strict (Y only) | 345 | 23.0% |
| LLM judge lenient (Y+P) | 971 | 64.9% |

**NIV thresholds** (adopted March 2026): Empirical calibration against the Opus judge yields two purpose-specific IS thresholds that supersede IS ≥ 3.0:

| Target | IS (NIV) | WER (NIV) | κ | Captures |
|--------|----------|-----------|------|----------|
| Y (clearly conveyed) | ≥ 3.80 | ≤ 34% | 0.690 | 346 (23.1%) |
| Y+P (any useful meaning) | ≥ 2.00 | ≤ 77% | 0.818 | 922 (61.6%) |

IS beats WER at both operating points (+0.061 for Y, +0.041 for Y+P). IS ≥ 3.80 matches the judge's Y rate exactly (23.1% vs 23.0%). IS ≥ 2.00 is strictly conservative vs the judge's Y+P rate (61.6% < 64.9%). Full calibration: [threshold_calibration_vs_opus.md](threshold_calibration_vs_opus.md).

**Cross-configuration stability:** Tested across 16 decode configurations, the `llm_context_prob` heuristic's correlation with IS holds at mean r = 0.925 (std = 0.015), confirming both systems are robust to decode parameter changes.

Full analysis: [llm_judge/llm_judge_analysis.md](llm_judge/llm_judge_analysis.md)

---

## 7. Comparison with Paper Expectations

### 7.1 Paper Table 1: VSR Performance (LRS3)

| Method | Training Data | WER |
|--------|--------------|-----|
| AV-HuBERT | 433h labeled | 28.6% |
| VSP-LLM | 433h labeled | 26.7% |
| VSP-LLM (FT) | 433h labeled | **25.4%** |
| **Our real-world test** | — | **67.0% mean** |

### 7.2 Paper Figure 4: Video Length vs. WER (LRS3)

| Video Length | Paper (VSP-LLM) | Our Results (approximate) |
|-------------|-----------------|--------------------------|
| 0-2 seconds | 34.7% | ~128% (1-5 words) |
| 2-4 seconds | 22.5% | ~72% (6-10 words) |
| 4-6 seconds | 17.0% | ~60% (11-20 words) |
| 6+ seconds | 12.9% | ~57% (21+ words) |

The relative trend (longer = better) holds, but the absolute performance is dramatically worse across all length ranges.

---

## 8. Recommendations

### 8.1 Short-Term (No Model Changes Required)

1. **Minimum segment length:** Discard or de-prioritize segments < 5 seconds. Short segments are nearly always hallucinated.
2. **Human review:** All model outputs require human verification before use. The model cannot be trusted without independent validation.
3. **Confidence scoring:** Modify the decode pipeline to expose beam search scores and per-token probabilities (see Report 4 for technical details).
4. **N-best output:** Save all 20 beam search candidates instead of only the top-1 (see Report 5 for aggregation strategies).

### 8.2 Medium-Term (Code/Configuration Changes)

5. **Prompt engineering:** Enhance the instruction prompt with domain context, topic hints, or vocabulary constraints (see Report 3 for detailed analysis).
6. **Hyperparameter tuning:** Adjust beam search parameters — particularly length penalty and repetition penalty — to reduce hallucination (see Report 2 for parameter-by-parameter analysis).
7. **Segment length optimization:** Experiment with longer segments (15-30 seconds) to give the model more context.

### 8.3 Long-Term (Research/Training Changes)

8. **Domain adaptation:** Fine-tune the model on in-domain data representative of the target use case (YouTube-like content, diverse speakers, varied conditions).
9. **Hallucination mitigation:** Implement constrained decoding, confidence thresholds, or a separate hallucination detector.
10. **LLM backbone upgrade:** Replace Llama-2-7B with Llama 3.1 8B (drop-in swap, same hidden dimension 4096). Expected -3 to -8 pp WER from better language prior alone; unlocks prompt strategies (topic context, anti-hallucination, vocabulary lists) worth an additional -5 to -15 pp. VALLR (ICCV 2025) demonstrated that Llama 3.2-3B achieves 18.7% WER on LRS3 vs our 25.4% with Llama-2-7B. See [LLM Upgrade Analysis](llm_upgrade_analysis.md) for full quantified projections.
11. **Alternative models:** Evaluate newer visual speech recognition models that may have addressed the domain generalization gap.

---

## 9. Conclusion

The VSP-LLM model represents a genuine research advance in lip-reading technology — its LRS3 benchmark results are competitive with the state of the art. However, **benchmark performance does not transfer to real-world deployment**. The 2.5-5x performance degradation on diverse YouTube content, combined with the model's tendency to generate fluent but fabricated text (20.6% hallucination rate), makes it unsuitable for any application requiring reliable output.

The most concerning aspect is that good and bad predictions are **visually indistinguishable** — the model generates grammatically correct English regardless of whether it accurately read the speaker's lips. Without ground truth or a confidence mechanism, a user receiving the model's output has no reliable way to know which parts to trust.

For production deployment, the model would need: (a) fine-tuning on target-domain data, (b) confidence scoring at the word level, (c) a minimum segment duration of 5+ seconds, and (d) mandatory human review of all outputs.

---

## Appendix A: Statistical Summary

```
Total segments evaluated:              860
Total reference words:              13,619
Total hypothesis errors (S+I+D):    17,091

WER Distribution:
  Mean:                              67.0%
  Median:                            63.8%
  Std Dev:                           44.0%
  Min:                                0.0%
  Max:                              400.0%
  10th percentile:                   18.2%
  25th percentile:                   33.3%
  75th percentile:                  100.0%
  90th percentile:                  100.0%

Quality Distribution:
  Perfect (WER = 0%):            16  ( 1.9%)
  Good (WER ≤ 20%):             98  (11.4%)
  Fair (WER ≤ 40%):            248  (28.8%)
  Poor (WER > 60%):            459  (53.4%)
  Catastrophic (WER ≥ 100%):   177  (20.6%)

Named Entity Accuracy:
  Mean Recall:                      39.2%
  Mean Precision:                   55.4%
  Mean F1:                          38.8%
  Segments with missed entities:    731/860 (85.0%)

Empty hypotheses:                  4/860 (0.5%)
```

## Appendix B: Methodology Notes

- Ground truth transcriptions were generated by Whisper ASR from the original audio track, then verified
- WER is computed using the `editdistance` library (Levenshtein distance)
- Named Entity detection uses spaCy NLP with POS-tag-based fallback
- Segment durations are derived from frame-number encoding in segment filenames (25 fps)
- All model parameters match the paper's recommended settings (beam=20, lenpen=0.0)
