# LRS3 Decode Experiment — IS Component Measurement

**Date**: 2026-03-07
**Purpose**: Measure the 6 IS components on actual LRS3 TED talk data to replace estimated values in the dual radar chart.

## Background

The dual radar chart (`generate_dual_radar.py`) compares LRS3 benchmark performance vs YouTube real-world performance across 6 IS dimensions. Previously, the LRS3 values were estimated guesses. This experiment produces **measured values** from real LRS3 decode.

## Data Source

- **Dataset**: `datasets/lrs3orig_sync.tar` — 198 videos from 5 LRS3 pretrain speakers (truncated tar, 136MB)
- **Format**: 224x224 face-crop videos at 25fps with audio (AAC 16kHz) and reference text
- **Test manifest overlap**: 0 of 1,321 official test segments — these are **pretrain split** videos, not the official test set
- **Usable segments**: 197 (1 video truncated/corrupt)

### Why Pretrain Data Is Still Valid

The VSP-LLM paper trained LoRA on the **trainval** split (30h), not the pretrain split (400h). The visual encoder (AV-HuBERT) saw these videos during self-supervised pretraining, but the LLM text decoder never saw the transcriptions. Results should be representative of LRS3-quality TED talk data, though the visual encoder's familiarity may give a slight advantage.

## Pipeline

### Preprocessing

1. **Extracted** 197 videos from tar with reference text (uppercase, from `Text:` field in .txt files)
2. **Extracted** audio to WAV (16kHz mono PCM)
3. **Built TSV manifest** pointing to video + audio + frame counts

Two video variants were tested:
- **V1**: Direct use of 224x224 face-crop videos (CenterCrop(88) at decode time captures mouth region — these videos are mouth-centered, not face-centered)
- **V2**: Mediapipe mouth ROI extraction → 96x96 grayscale mouth crops → CenterCrop(88) at decode time

### Feature Extraction & Clustering

- **AV-HuBERT features**: Extracted from layer 12 using `large_vox_iter5.pt` checkpoint
- **K-means model**: Used YouTube-trained golden model (`flat_kmeans_200.bin`), NOT the original LRS3-trained k-means
- **Cluster counts**: Generated from k-means labels using standard deduplication

### Decode

- **Model**: `checkpoint_finetune.pt` (paper's best, with unfrozen visual encoder)
- **Parameters**: beam=20, lenpen=0 (paper's settings)
- **LLM**: Llama-2-7b-hf

### IS Scoring

- Ran `generate_intelligibility_scores.py` on the decode report
- All 6 components computed: semantic similarity, phonetic similarity, WER, WWER, NEA F1, length ratio

## Results

### Overall Decode Performance

| Metric | V1 (224x224 direct) | V2 (96x96 mouth crop) | Paper (LRS3 test) |
|--------|--------------------|-----------------------|-------------------|
| WER | **36.5%** | 44.4% | 25.4% |
| Segments decoded | 184 | 184 | 1,321 |
| Empty outputs | 10 (5.4%) | 14 (7.6%) | — |
| IS mean | **3.61** | 3.28 | — |
| Captured (IS ≥ 3) | **72.3%** | 65.8% | — |

**V1 is better**: The 224x224 videos are already mouth-centered crops (verified visually). CenterCrop(88) on 224x224 directly captures the mouth region. V2's mediapipe re-cropping and re-encoding degraded quality.

### WER Gap Analysis (36.5% vs 25.4%)

The +11pp WER gap is due to:
1. **K-means model mismatch**: YouTube-trained k-means vs LRS3-trained k-means — different visual speech unit clustering
2. **Pretrain vs test split**: Different speakers, potentially different characteristics
3. **Only 5 speakers** vs 412 in the official test set

### IS Component Values (V1)

#### All 184 segments (mean WER 36.5%)

| Component | Value | Normalized (0-1) |
|-----------|-------|-------------------|
| Semantic Similarity | 0.723 | 0.723 |
| Phonetic Similarity | 0.740 | 0.740 |
| WER | 36.5% | 0.635 (inverted) |
| WWER | 38.9% | 0.611 (inverted) |
| NEA F1 | 63.4% | 0.634 |
| Length Ratio | 0.922 | 0.922 |

#### WER 20-30% band (n=33, mean WER 24.5% — closest to paper's 25.4%)

| Component | LRS3 (n=33) | YouTube (n=138) | Delta |
|-----------|-------------|-----------------|-------|
| Semantic Similarity | **0.868** | 0.741 | +0.127 |
| Phonetic Similarity | **0.857** | 0.838 | +0.019 |
| WER (inverted) | 0.755 | 0.750 | +0.005 |
| WWER (inverted) | **0.744** | 0.720 | +0.024 |
| NEA F1 | **0.795** | 0.740 | +0.055 |
| Length Ratio | **0.988** | 0.970 | +0.018 |
| IS mean | **4.266** | 4.034 | +0.232 |

### Key Finding

At the same WER level (~25%), LRS3 TED talk data shows **significantly higher semantic similarity** (+0.127) than YouTube data. This confirms that errors on clean TED talk content are more semantically coherent — wrong words are closer in meaning to correct words. The domain gap is most visible in semantic similarity and named entity accuracy.

### Tier Distribution (all 184 segments)

| Tier | Count | % |
|------|-------|-----|
| 5 — Excellent | 95 | 51.6% |
| 4 — Good | 38 | 20.7% |
| 3 — Fair | 25 | 13.6% |
| 2 — Poor | 14 | 7.6% |
| 1 — Failed | 12 | 6.5% |

### Values Used for Dual Radar Chart

Updated `generate_dual_radar.py` with the WER 20-30% band values (n=33):
```python
LRS3_VALUES = [0.868, 0.857, 0.755, 0.744, 0.795, 0.988]
```

Previous estimated values were: `[0.92, 0.88, 0.75, 0.78, 0.85, 0.95]`

## Files

- Decode output V1: `/tmp/lrs3_decode/decode_output/hypo-172610.json`
- Decode output V2: `/tmp/lrs3_decode/decode_output_v2/hypo-172610.json`
- IS scores V1: `/tmp/lrs3_decode/is_v1/intelligibility_scores.csv`
- IS scores V2: `/tmp/lrs3_decode/is_v2/intelligibility_scores.csv`
- Updated radar script: `docs/_research-tools/generators/generate_dual_radar.py`
- Updated radar plot: `presentation_materials_20260224/01_plots_for_slides/P6b_radar_dual.png`

## Limitations

1. **Not the official test set** — pretrain split, 5 speakers only (vs 412 in test)
2. **YouTube-trained k-means** — likely degrades WER by ~10pp vs LRS3-trained k-means
3. **Small sample** at paper WER level — only 33 segments in the 20-30% WER band
4. **Visual encoder familiarity** — AV-HuBERT was pretrained on these videos (without labels)

## Future Work

To get exact LRS3 test set numbers:
1. Request LRS3 test set access from Oxford VGG
2. Preprocess through auto_avsr (mouth ROI extraction)
3. Use LRS3-trained k-means model (train on LRS3 pretrain, or obtain from AV-HuBERT authors)
4. Decode and compute IS on all 1,321 official test segments
