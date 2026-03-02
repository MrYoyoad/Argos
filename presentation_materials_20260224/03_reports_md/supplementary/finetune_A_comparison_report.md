# Weekend Fine-Tuning Comparison Report

**Date**: February 2026
**GPU**: Tesla T4 (16GB VRAM)
**Dataset**: 1,273 train / 224 val segments (AVSpeech YouTube, stratified by IS tier)
**Encoder**: Frozen throughout (safe for T4)

## Experiments

| | Baseline | Exp A: r=16 Fine-Tuned | Exp B: r=64 Fresh Init |
|---|---|---|---|
| **LoRA Rank** | 16 (pretrained) | 16 (continued) | 64 (from scratch) |
| **LoRA Alpha** | 32 | 32 | 128 |
| **Updates** | 0 (inference only) | 3,000 | 3,000 |
| **LR** | — | 3e-4 | 3e-4 |

## Training Results (Exp A)

Training completed Feb 27, 2026 after 17.0 hours on Tesla T4 (FP16).

### Key Training Metrics

| Metric | Epoch 2 (Best) | Epoch 19 (Final) | Delta |
|--------|----------------|-------------------|-------|
| **Val Accuracy** | 62.94% | 58.98% | -3.96 pp |
| **Val Loss** | 2.391 | 4.120 | +72% |
| **Val Perplexity** | 5.24 | 17.39 | +232% |
| **Train Accuracy** | 65.00% | 95.52% | +30.5 pp |
| **Train Loss** | 2.192 | 0.022 | -99% |
| **Train-Val Acc Gap** | 2.1 pp | 36.5 pp | +34.4 pp |

### Overfitting Analysis

Best validation accuracy (62.94%) was reached at **epoch 2** (~320 updates). All subsequent epochs showed monotonic degradation in validation metrics while training metrics continued to improve, indicating severe overfitting:

- **Train accuracy** climbed from 62.7% to 95.5% (memorization)
- **Val accuracy** declined from 62.9% to 59.0% (generalization failure)
- **Val perplexity** exploded from 5.24 to 17.39 (model increasingly uncertain on unseen data)
- **Gradient norms** decreased from ~3.3 to ~1.0 (model converged to sharp minimum)

The `checkpoint_best.pt` (saved at epoch 2) is the only usable checkpoint for inference.

### Training Dynamics

- **LR Schedule**: Tri-stage — warmup 0-600 steps, peak 3e-4, decay 600-3000
- **Convergence**: Loss dropped rapidly in first 800 updates, plateaued near zero by epoch 10
- **Checkpoints**: 7 saved (best + 5 interval + last), each ~3.9 GB

### Diagnostic Plots

All 10 training diagnostic plots are in `docs/finetuning/plots/`:

| Plot | Shows |
|------|-------|
| FT_01 | Loss curves (train vs val) — divergence after epoch 2 |
| FT_02 | Accuracy curves — 36.5 pp gap by final epoch |
| FT_03 | Overfitting gap progression (dual-axis) |
| FT_04 | Tri-stage LR schedule |
| FT_05 | Gradient norm trajectory |
| FT_06 | Perplexity (log scale) — val PPL explosion |
| FT_07 | Training data IS tier distribution |
| FT_08 | Granular loss (50-update resolution) with checkpoints |
| FT_09 | Wall-clock time per epoch (~48 min avg) |
| FT_10 | Summary dashboard (6-panel overview) |

## Full Metrics Comparison (Decode Evaluation)

_Requires running decode on fine-tuned checkpoint. Training complete, decode pending._

| Metric | Baseline | Exp A (r=16) | Exp B (r=64) | Best |
|--------|----------|--------------|--------------|------|
| **WER** (%) | 67.0 | _pending_ | _not trained_ | — |
| **WWER** (%) | 59.5 | _pending_ | _not trained_ | — |
| **Named Entity F1** (%) | 38.8 | _pending_ | _not trained_ | — |
| **Intelligibility Score** (0-5) | 2.52 | _pending_ | _not trained_ | — |
| **Properly Captured** (IS >= 3) | 39.9% | _pending_ | _not trained_ | — |
| **Hallucination Rate** (WER >= 100%) | 20.6% | _pending_ | _not trained_ | — |

## IS Tier Distribution (Decode Evaluation)

| Tier | Baseline | Exp A | Exp B |
|------|----------|-------|-------|
| 5 — Excellent (4.0-5.0) | 18.4% (276) | _pending_ | _not trained_ |
| 4 — Good (3.0-3.99) | 21.4% (321) | _pending_ | _not trained_ |
| 3 — Fair (2.0-2.99) | 21.7% (325) | _pending_ | _not trained_ |
| 2 — Poor (1.0-1.99) | 22.4% (336) | _pending_ | _not trained_ |
| 1 — Failed (0.0-0.99) | 16.0% (239) | _pending_ | _not trained_ |

## Analysis

### Training Takeaways

1. **Early stopping is critical**: Best checkpoint at epoch 2 — 17 of 19 epochs were wasted training time
2. **r=16 is rank-limited**: The model memorized training data (95.5% train acc) but couldn't generalize (59.0% val acc), suggesting the adapter lacks capacity for the TED→YouTube domain shift
3. **Data is sufficient for signal**: Validation accuracy improved meaningfully from epoch 1 to 2 (62.5% → 62.9%), proving the model can learn from AVSpeech data
4. **Encoder freeze is the bottleneck**: With encoder frozen, only LLM adapters are trained — the visual feature extractor cannot adapt to YouTube-style faces/angles

### Per-Tier Impact
_To be filled after decode evaluation. Key question: Did fine-tuning help more on hard (Tier 1-2) or easy (Tier 4-5) segments?_

### Hallucination Analysis
_To be filled after decode evaluation. Key question: Did fine-tuning reduce fabricated outputs?_

### Failure Mode Shifts
_To be filled after decode evaluation. Key question: Which of the 10 failure modes improved/worsened?_

## Recommendations

### For Exp B (r=64)
1. **Use early stopping**: Save checkpoints every epoch, stop at first val accuracy decline
2. **Set max_update=500**: Based on Exp A, peak is at ~320 updates — 3,000 is massive overkill
3. **Increase LoRA rank**: r=64 with alpha=128 gives 4x adapter capacity
4. **Consider validation frequency**: Validate every 50 updates (not every epoch) for finer early-stopping

### For Future Experiments
- **Encoder unfreezing** (requires larger GPU): Expected 15-25 WER point gain per Report 6 analysis
- **Expanded LoRA targets**: Add o_proj, gate_proj, up_proj, down_proj to capture more model capacity
- **Data quality curation**: Filter by face detection confidence >0.9, exclude extreme head poses
- **More training data**: Current 1,273 segments is small — consider full AVSpeech download
