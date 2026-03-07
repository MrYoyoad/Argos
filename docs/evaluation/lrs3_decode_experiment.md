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

| Metric | V1 (YT k-means) | V2 (mediapipe) | V3 (auto_avsr) | V4 (LRS3 k-means) | Paper |
|--------|-----------------|----------------|----------------|-------------------|-------|
| WER (all) | 36.5% | 44.4% | 37.8% | **36.0%** | 25.4% |
| WER (non-empty) | 31.1% | — | — | **32.0%** | — |
| Segments decoded | 184 | 184 | 184 | 184 | 1,321 |
| Empty outputs | 14 (7.6%) | 14 (7.6%) | 15 (8.2%) | **11 (6.0%)** | — |
| IS mean | 3.61 | 3.28 | 3.54 | **3.66** | — |
| Captured (IS ≥ 3) | 72.3% | 65.8% | 71.7% | **72.8%** | — |

**V4 is best**: Uses same 224x224 mouth-centered videos as V1 but with an LRS3-trained k-means model (no domain mismatch). Fewer empty outputs and higher IS.

### WER Gap Analysis (36.0% vs 25.4%)

The +10.6pp WER gap (36.0% V4 vs 25.4% paper) remains even with LRS3-trained k-means:
1. ~~**K-means model mismatch**~~: Eliminated in V4 — reduced WER by only 0.5pp (36.5→36.0%), not the main factor
2. **Pretrain vs test split**: Different speakers, potentially different characteristics — likely the main factor
3. **Only 5 speakers** vs 412 in the official test set — limited speaker diversity
4. **Small dataset** (197 segments vs 1,321) — higher variance

### IS Component Values (V4 — LRS3-trained k-means, best version)

#### All 184 segments (mean WER 36.0%)

| Component | Value | Normalized (0-1) |
|-----------|-------|-------------------|
| Semantic Similarity | 0.729 | 0.729 |
| Phonetic Similarity | 0.747 | 0.747 |
| WER | 36.0% | 0.640 (inverted) |
| WWER | 35.2% | 0.648 (inverted) |
| NEA F1 | 63.9% | 0.639 |
| Length Ratio | 0.933 | 0.933 |

#### WER 20-30% band (n=35, mean WER 24.5% — closest to paper's 25.4%)

| Component | LRS3 (n=35) | YouTube (n=138) | Delta |
|-----------|-------------|-----------------|-------|
| Semantic Similarity | **0.875** | 0.741 | +0.134 |
| Phonetic Similarity | **0.859** | 0.838 | +0.021 |
| WER (inverted) | 0.755 | 0.750 | +0.005 |
| WWER (inverted) | **0.764** | 0.720 | +0.044 |
| NEA F1 | **0.772** | 0.740 | +0.032 |
| Length Ratio | **0.987** | 0.970 | +0.017 |
| IS mean | **4.263** | 4.034 | +0.229 |

### Key Finding

At the same WER level (~25%), LRS3 TED talk data shows **significantly higher semantic similarity** (+0.134) than YouTube data. This confirms that errors on clean TED talk content are more semantically coherent — wrong words are closer in meaning to correct words. The domain gap is most visible in semantic similarity and WWER.

### Tier Distribution (all 184 segments)

| Tier | Count | % |
|------|-------|-----|
| 5 — Excellent | 94 | 51.1% |
| 4 — Good | 40 | 21.7% |
| 3 — Fair | 29 | 15.8% |
| 2 — Poor | 12 | 6.5% |
| 1 — Failed | 9 | 4.9% |

### Values Used for Dual Radar Chart

Updated `generate_dual_radar.py` with the WER 20-30% band values (n=35):
```python
LRS3_VALUES = [0.875, 0.859, 0.755, 0.764, 0.772, 0.987]
```

Previous estimated values were: `[0.92, 0.88, 0.75, 0.78, 0.85, 0.95]`

## V3: Full auto_avsr Pipeline Preprocessing

### Motivation

V2's mediapipe re-crop degraded quality due to lossy re-encoding, static crop from 1 frame, and double grayscale conversion. V3 uses the **real auto_avsr pipeline** (`AVSRDataLoader` with mediapipe face detection, per-frame landmark tracking, affine alignment, smoothing window=12, 96x96 grayscale mouth crop) — identical to the production pipeline.

### V3 Results

| Metric | V1 (224x224 direct) | V2 (mediapipe re-crop) | V3 (auto_avsr pipeline) |
|--------|--------------------|-----------------------|------------------------|
| WER | **36.5%** | 44.4% | 37.8% |
| IS mean | **3.61** | 3.28 | 3.54 |
| Captured (IS ≥ 3) | **72.3%** | 65.8% | 71.7% |
| Empty outputs | 10 (5.4%) | 14 (7.6%) | 15 (8.2%) |

#### V3 WER 20-30% band (n=25, mean WER 24.6%)

| Component | V1 (n=33) | V3 (n=25) | Delta |
|-----------|-----------|-----------|-------|
| Semantic Similarity | **0.868** | 0.843 | -0.025 |
| Phonetic Similarity | **0.857** | 0.849 | -0.008 |
| WER (inverted) | **0.755** | 0.754 | -0.001 |
| WWER (inverted) | **0.744** | 0.717 | -0.027 |
| NEA F1 | **0.795** | 0.752 | -0.043 |
| Length Ratio | 0.988 | **0.994** | +0.006 |
| IS mean | **4.266** | 4.162 | -0.104 |

#### V3 Tier Distribution (all 184 segments)

| Tier | Count | % |
|------|-------|-----|
| 5 — Excellent | 86 | 46.7% |
| 4 — Good | 46 | 25.0% |
| 3 — Fair | 23 | 12.5% |
| 2 — Poor | 17 | 9.2% |
| 1 — Failed | 12 | 6.5% |

### Why V1 is Still Best

The 224x224 videos in the LRS3 pretrain tar are already **mouth-centered crops** (not face-centered). CenterCrop(88) on 224x224 directly captures the mouth region optimally. Running these through auto_avsr adds a redundant second face detection + crop step that slightly degrades quality:
- The videos are already cropped to 224x224 around the mouth
- Auto_avsr re-detects the face and re-crops to 96x96, losing some spatial context
- CenterCrop(88) on 96x96 leaves only 4px margin vs 68px margin on 224x224

V3 is much better than V2 (37.8% vs 44.4% WER) because auto_avsr uses proper per-frame tracking and affine alignment, but V1 remains best because the source data is already optimally cropped.

**Conclusion**: V4 (V1 videos + LRS3-trained k-means) provides the canonical measured LRS3 IS components for the radar chart.

## Files

- Decode output V1: `/tmp/lrs3_decode/decode_output/hypo-172610.json`
- Decode output V2: `/tmp/lrs3_decode/decode_output_v2/hypo-172610.json`
- Decode output V3: `/tmp/lrs3_decode/decode_output_v3/hypo-172610.json`
- IS scores V1: `/tmp/lrs3_decode/is_v1/intelligibility_scores.csv`
- IS scores V2: `/tmp/lrs3_decode/is_v2/intelligibility_scores.csv`
- IS scores V3: `/tmp/lrs3_decode/is_v3/intelligibility_scores.csv`
- Decode output V4: `/tmp/lrs3_decode/decode_output_v4/hypo-172610.json`
- IS scores V4: `/tmp/lrs3_decode/is_v4/intelligibility_scores.csv`
- LRS3-trained k-means: `/tmp/lrs3_decode/lrs3_kmeans_200.bin`
- Pipeline-cropped videos: `/tmp/lrs3_decode/pipeline_crops/`
- Updated radar script: `docs/_research-tools/generators/generate_dual_radar.py`
- Updated radar plot: `presentation_materials_20260224/01_plots_for_slides/P6b_radar_dual.png`

## Limitations

1. **Not the official test set** — pretrain split, 5 speakers only (vs 412 in test)
2. ~~**YouTube-trained k-means**~~ — eliminated in V4; LRS3-trained k-means only improved WER by 0.5pp
3. **Small sample** at paper WER level — only 35 segments in the 20-30% WER band
4. **Visual encoder familiarity** — AV-HuBERT was pretrained on these videos (without labels)
5. **Pre-cropped source videos** — 224x224 mouth-centered crops favor V1 over V3 pipeline

## Future Work

To get exact LRS3 test set numbers:
1. Request LRS3 test set access from Oxford VGG
2. Preprocess through auto_avsr (mouth ROI extraction) — V3 pipeline is validated and ready
3. Use LRS3-trained k-means model (train on LRS3 pretrain, or obtain from AV-HuBERT authors)
4. Decode and compute IS on all 1,321 official test segments
