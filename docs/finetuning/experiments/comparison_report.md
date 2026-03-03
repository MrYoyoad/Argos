# Fine-Tuning Comparison Report

**Date**: March 2026
**GPU**: Tesla T4 (16GB VRAM)
**Dataset**: 1,273 train / 224 val segments (AVSpeech YouTube, stratified by IS tier)
**Encoder**: Frozen throughout

## Default Decode Parameters (beam=20, lenpen=0)

| Metric | Baseline | ExpA_r16 | ExpB_r64 | Best |
|--------|---|---|---|------|
| **Mean IS (0-5)** | 2.5 | 2.3 | 2.0 | Baseline (default) |
| **Median IS** | 2.4 | 2.3 | 2.0 | Baseline (default) |
| **Properly Captured (%)** | 39.7% | 38.8% | 33.0% | Baseline (default) |
| **WER (%)** | N/A¹ | N/A¹ | N/A¹ | — |
| **WWER (%)** | N/A¹ | N/A¹ | N/A¹ | — |
| **NEA F1 (%)** | N/A¹ | N/A¹ | N/A¹ | — |
| **Hallucination Rate (%)** | 0.0% | 0.0% | 0.0% | Baseline (default) |
| **Empty Output (%)** | 6.7% | 11.6% | 25.4% | Baseline (default) |

¹ WER/WWER/NEA not computed for this eval — finetune comparison used IS and LLM judge only.

## IS Tier Distribution (Default Decode)

| Tier | Baseline | ExpA_r16 | ExpB_r64 |
|------|---|---|---|
| 5 — Excellent (4.0-5.0) | 18.3% (41) | 17.9% (40) | 15.2% (34) |
| 4 — Good (3.0-3.99) | 21.4% (48) | 21.0% (47) | 17.9% (40) |
| 3 — Fair (2.0-2.99) | 21.9% (49) | 17.0% (38) | 17.4% (39) |
| 2 — Poor (1.0-1.99) | 22.3% (50) | 18.3% (41) | 13.8% (31) |
| 1 — Failed (0.0-0.99) | 16.1% (36) | 25.9% (58) | 35.7% (80) |

## Decode Hyperparameter Sweep

### Baseline

| Config | Mean IS | Properly Captured | WER | WWER | NEA F1 | Hallucination | Empty |
|--------|---------|-------------------|-----|------|--------|---------------|-------|
| beam5 | 2.6 | 40.6% | N/A | N/A | N/A | 0.0% | 2.2% |
| default | 2.5 | 39.7% | N/A | N/A | N/A | 0.0% | 6.7% |
| greedy | 2.5 | 36.6% | N/A | N/A | N/A | 0.0% | 0.0% |
| lenpen1 | 2.6 | 40.2% | N/A | N/A | N/A | 0.0% | 0.0% |
| sample_low | 2.6 | 39.7% | N/A | N/A | N/A | 0.0% | 0.9% |
| sample_med | 2.6 | 40.2% | N/A | N/A | N/A | 0.0% | 0.9% |

### ExpA_r16

| Config | Mean IS | Properly Captured | WER | WWER | NEA F1 | Hallucination | Empty |
|--------|---------|-------------------|-----|------|--------|---------------|-------|
| beam5 | 2.5 | 41.1% | N/A | N/A | N/A | 0.0% | 6.7% |
| default | 2.3 | 38.8% | N/A | N/A | N/A | 0.0% | 11.6% |
| greedy | 2.5 | 35.7% | N/A | N/A | N/A | 0.0% | 0.0% |
| lenpen1 | 2.6 | 41.5% | N/A | N/A | N/A | 0.0% | 0.0% |
| sample_low | 2.5 | 40.6% | N/A | N/A | N/A | 0.0% | 0.9% |
| sample_med | 2.5 | 41.5% | N/A | N/A | N/A | 0.0% | 0.9% |

### ExpB_r64

| Config | Mean IS | Properly Captured | WER | WWER | NEA F1 | Hallucination | Empty |
|--------|---------|-------------------|-----|------|--------|---------------|-------|
| beam5 | 2.4 | 36.6% | N/A | N/A | N/A | 0.0% | 4.5% |
| default | 2.0 | 33.0% | N/A | N/A | N/A | 0.0% | 25.4% |
| greedy | 2.4 | 32.6% | N/A | N/A | N/A | 0.0% | 0.0% |
| lenpen1 | 2.4 | 36.6% | N/A | N/A | N/A | 0.0% | 0.0% |
| sample_low | 2.4 | 37.9% | N/A | N/A | N/A | 0.0% | 1.3% |
| sample_med | 2.4 | 37.5% | N/A | N/A | N/A | 0.0% | 1.8% |

## Analysis

### Best Overall
**Baseline** achieved the highest mean IS of 2.5 with default decode parameters.

### Improvement Over Baseline

- **ExpA_r16**: IS 2.3 (Δ -0.175, regression)
- **ExpB_r64**: IS 2.0 (Δ -0.464, regression)

## LLM-as-a-Judge Evaluation

Claude Opus 4.6 evaluated all 224 val segments per experiment using the same Y/P/N protocol as the baseline 1,497-segment study. Empty/trivially short outputs auto-classified as N.

| Experiment | Y | P | N | Y% | P% | N% | Y+P% | Auto-N |
|-----------|---|---|---|---|---|---|---|---|
| Baseline | 40 | 76 | 108 | 17.9 | 33.9 | 48.2 | 51.8 | 16 |
| Exp A (r=16) | 41 | 74 | 109 | 18.3 | 33.0 | 48.7 | 51.3 | 28 |
| Exp B (r=64) | 32 | 88 | 104 | 14.3 | 39.3 | 46.4 | 53.6 | 60 |

### IS vs LLM Judge Comparison

IS scores decrease monotonically (Baseline 2.487 > Exp A 2.312 > Exp B 2.023), but LLM Y+P% is flat (~51–54%). The discrepancy exists because:
1. IS heavily penalizes empty outputs (IS = 0) which drag down the mean
2. The LLM judge confirms that when text IS produced, fine-tuned models are about as useful as baseline
3. Exp B's higher P% (39.3% vs 33.9%) at the cost of lower Y% (14.3% vs 17.9%) reflects a shift toward fluent but slightly wrong outputs — characteristic of overfitting

### Agreement Between Experiments

| Pair | Exact | Lenient (Y+P vs N) |
|------|:---:|:---:|
| Baseline vs Exp A | 80.8% | 87.9% |
| Baseline vs Exp B | 69.6% | 78.6% |
| Exp A vs Exp B | 71.0% | 79.9% |

The auto-N count is the clearest overfitting signal: Baseline = 16 (7.1%), Exp A = 28 (12.5%), Exp B = 60 (26.8%). More LoRA parameters with insufficient data → more empty/gibberish outputs.

### Conclusion

Both IS and Claude-as-Judge converge on the same finding: fine-tuning on 1,273 segments produced no meaningful improvement. The Baseline (paper checkpoint) remains the recommended model.

Full LLM judge analysis: [../llm_judge/finetune_llm_judge_comparison.md](../llm_judge/finetune_llm_judge_comparison.md)

## Recommendations

_To be filled after reviewing results._
