# Claude-as-Judge: Fine-Tuning Experiment Comparison

## Methodology

Claude Opus 4.6 evaluated hypothesis-reference pairs from each experiment
using the same 3-level protocol as the baseline study:
- **Y**: Meaning clearly conveyed
- **P**: Partial — some meaning preserved, key info lost/distorted
- **N**: Wrong topic, hallucination, empty, or misleading

## Judgment Distribution by Experiment

| Experiment | Total | Y | P | N | Y% | P% | N% | Y+P% |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Baseline | 224 | 40 | 76 | 108 | 17.9 | 33.9 | 48.2 | 51.8 |
| ExpA_r16 | 224 | 41 | 74 | 109 | 18.3 | 33.0 | 48.7 | 51.3 |
| ExpB_r64 | 224 | 32 | 88 | 104 | 14.3 | 39.3 | 46.4 | 53.6 |

## Cross-Experiment Agreement

| Pair | Shared | Exact Agree | Lenient Agree |
|------|:---:|:---:|:---:|
| Baseline vs ExpA_r16 | 224 | 80.8% | 87.9% |
| Baseline vs ExpB_r64 | 224 | 69.6% | 78.6% |
| ExpA_r16 vs ExpB_r64 | 224 | 71.0% | 79.9% |

## Per-Segment Movement Analysis

How did individual segments change between experiments?

### Baseline → ExpA_r16

| Transition | Count | % | Interpretation |
|-----------|:---:|:---:|---------------|
| Y→Y | 31 | 13.8% | stable success |
| Y→P | 8 | 3.6% | degraded |
| Y→N | 1 | 0.4% | broken |
| P→Y | 8 | 3.6% | improved to success |
| P→P | 55 | 24.6% | stable partial |
| P→N | 13 | 5.8% | degraded |
| N→Y | 2 | 0.9% | recovered |
| N→P | 11 | 4.9% | improved to partial |
| N→N | 95 | 42.4% | stable failure |

**Net movement**: 21 improved, 22 degraded, net = -1

### Baseline → ExpB_r64

| Transition | Count | % | Interpretation |
|-----------|:---:|:---:|---------------|
| Y→Y | 24 | 10.7% | stable success |
| Y→P | 13 | 5.8% | degraded |
| Y→N | 3 | 1.3% | broken |
| P→Y | 7 | 3.1% | improved to success |
| P→P | 50 | 22.3% | stable partial |
| P→N | 19 | 8.5% | degraded |
| N→Y | 1 | 0.4% | recovered |
| N→P | 25 | 11.2% | improved to partial |
| N→N | 82 | 36.6% | stable failure |

**Net movement**: 33 improved, 35 degraded, net = -2

### ExpA_r16 → ExpB_r64

| Transition | Count | % | Interpretation |
|-----------|:---:|:---:|---------------|
| Y→Y | 25 | 11.2% | stable success |
| Y→P | 13 | 5.8% | degraded |
| Y→N | 3 | 1.3% | broken |
| P→Y | 7 | 3.1% | improved to success |
| P→P | 50 | 22.3% | stable partial |
| P→N | 17 | 7.6% | degraded |
| N→Y | 0 | 0.0% | recovered |
| N→P | 25 | 11.2% | improved to partial |
| N→N | 84 | 37.5% | stable failure |

**Net movement**: 32 improved, 33 degraded, net = -1

## Agreement with IS Scores

| Experiment | Mean IS | IS ≥ 3.0 % | LLM Y% | LLM Y+P% | Empty/Auto-N |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Baseline | 2.487 | ~40% | 17.9 | 51.8 | 16 (7.1%) |
| ExpA_r16 | 2.312 | ~35% | 18.3 | 51.3 | 28 (12.5%) |
| ExpB_r64 | 2.023 | ~28% | 14.3 | 53.6 | 60 (26.8%) |

**Key observation**: IS scores decrease monotonically (Baseline > Exp A > Exp B), but the LLM judge's Y+P% is remarkably flat (~51-54%). This suggests IS penalizes fine-tuned outputs more heavily than human-aligned judgment does. Exp B produces more empty outputs (60 vs 16) but when it *does* produce text, that text is more often partially correct (39.3% P vs 33.9% P for Baseline).

## Interpretation

### 1. Fine-tuning produced no meaningful improvement

All three experiments yield nearly identical LLM judge results on these 224 validation segments:
- Y% ranges 14.3-18.3% (within noise for n=224)
- Y+P% ranges 51.3-53.6%
- Net movement is -1 to -2 per transition pair (essentially zero)

This confirms the IS-based finding: with only 1,273 training segments, LoRA fine-tuning neither helps nor significantly hurts.

### 2. Exp B (r=64) shifts the distribution but doesn't improve it

Exp B has the **lowest Y%** (14.3%) but the **highest Y+P%** (53.6%). The mechanism:
- 25 segments improved from N→P (11.2%) — Exp B produces *something* where Baseline produced nothing useful
- But 19 degraded from P→N (8.5%) and 13 from Y→P (5.8%)
- The higher LoRA rank (more parameters, more overfitting) produces more "fluent-sounding" outputs that are partially correct rather than clearly wrong — but also more often garbles what was previously clear

### 3. Exp A (r=16) is statistically indistinguishable from Baseline

80.8% exact agreement, 87.9% lenient agreement. Net movement of -1. For practical purposes, the r=16 fine-tuning had no effect on output quality.

### 4. Empty output is the strongest signal of overfitting

The auto-N (empty/trivially short output) count is the clearest differentiator:
- Baseline: 16 empty (7.1%)
- Exp A: 28 empty (12.5%) — 1.75x baseline
- Exp B: 60 empty (26.8%) — 3.75x baseline

More LoRA parameters = more overfitting = more segments where the model produces nothing. This is the dominant failure mode of the fine-tuning, not wrong-topic hallucination.

## Conclusions

- **Highest Y% (strict)**: ExpA_r16 (18.3%) — but within noise of Baseline (17.9%)
- **Highest Y+P% (lenient)**: ExpB_r64 (53.6%) — driven by N→P conversions, offset by higher empty rate
- **Best overall**: Baseline (paper checkpoint) — lowest empty rate, competitive Y%, and no risk of overfitting artifacts
- **Implication**: The bottleneck is training data (1,273 segments), not model capacity. See training-research-notes.md for recommendations.
