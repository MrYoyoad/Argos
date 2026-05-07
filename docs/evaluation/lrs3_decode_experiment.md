# LRS3 Decode Experiment — 1-Pager

**Date**: 2026-03-07 (collapsed to 1-pager 2026-05-07)
**Purpose**: Measure the 6 IS components on actual LRS3 TED talk data to replace estimated values in the dual radar chart (`generate_dual_radar.py`).

## What was decoded

- **Dataset**: 197 LRS3 pretrain videos (5 speakers, 224x224 face-crops at 25fps), from `datasets/lrs3orig_sync.tar`. These are pretrain-split videos — the LLM text decoder never saw the transcriptions, but the visual encoder (AV-HuBERT) did during self-supervised pretraining.
- **Pipeline**: standard preprocessing → AV-HuBERT layer-12 features → k-means → VSP-LLM decode (`checkpoint_finetune.pt`, beam=20, lenpen=0, Llama-2-7b-hf).
- **Best variant tested**: V4 — 224x224 mouth-centered videos + **LRS3-trained k-means** (no YouTube-domain k-means mismatch). 184 of 197 segments decoded successfully (11 empty, 6.0%).

## Headline result

**WER 32.0% non-empty / 36.0% all** (V4) vs paper's 25.4% on the official test set. The +10.6pp gap is dominated by **pretrain-vs-test split differences** and small-sample variance (5 speakers vs 412 official; 197 segments vs 1,321), not by the k-means choice (eliminating the YouTube k-means mismatch only saved 0.5pp).

## IS component measurements (V4, all 184 segments)

These are the values used by `generate_dual_radar.py` for the LRS3 vs YouTube radar comparison. All on a 0–1 scale:

| Component | LRS3 (V4) | YouTube baseline (1,497) |
|---|---|---|
| Semantic Similarity | 0.729 | 0.437 |
| Phonetic Similarity | 0.747 | 0.552 |
| 1 - WER | 0.640 | ~0.36 |
| 1 - WWER | 0.648 | 0.395 |
| NEA F1 | 0.639 | 0.389 |
| Length Ratio | 0.933 | 0.925 |
| **Composite IS** | **3.66** | **2.547** (MBR-default; top-1: 2.52) |

**Captured (IS ≥ 3)**: 72.8% on LRS3 V4 vs ~41% on YouTube. The largest normalized gap is on Semantic Similarity (+0.95σ), confirming that the domain advantage shows up most in meaning preservation, not just lexical accuracy.

## Files

- Decode artifacts: not retained (one-off measurement)
- IS scores: feed directly into the dual radar plot
- Linked from: `docs/evaluation/signal_distribution_analysis.md` §LRS3 vs YouTube comparison; `docs/evaluation/intelligibility_methodology.md`
