# Pipeline Architecture & Data Flow

> Split from CLAUDE.md for easier navigation. See also:
> - [CLAUDE.md](../CLAUDE.md) — Project overview and rules
> - [Development Guide](development-guide.md) — Commands, workflows, troubleshooting
> - [Container Sync Changelog](container-sync-changelog.md) — EC2→Container change log

## High-Level Pipeline Flow

```
Raw Videos (.mp4)
    |
[0.1 Fast Segmentation] -> Split videos into segments (or copy whole videos)
    |                      (codec copy, very fast - 12s segments with 2s overlap)
    |                      Output: preprocessed_flat_seg12/fast_segments/
[0.5 Normalization] -> Normalize SEGMENTS (not whole videos!)
    |                  (HDR/10-bit conversion, GPU encoding - efficient for long videos)
    |                  Output: auto_avsr/flat_prepared/ -> auto_avsr/flat/
[0.6 Transcription Reuse] -> Copy existing .transcriptions/*.wrd -> flat_wrd/
    |                        (Enables Whisper skip for existing transcriptions)
[1. Prepare Directories] -> Copy normalized segments to preprocess_ready/
    |
[2. Mouth Cropping] -> Face detection + mouth cropping (NO segmentation!)
    |                  (mediapipe, 88x88 crops at 25fps - segments already done)
    |                  Output: preprocessed_flat_seg12/
[3. ASR - Whisper] -> .wrd transcription files (skips videos with existing .wrd)
    |
[3.5 Save Transcriptions] -> Copy new flat_wrd/*.wrd -> .transcriptions/
    |                        (Persist Whisper outputs for future reuse)
[4. flat_to_lrs3_preperation.sh] -> Convert to LRS3 format
    |
[5. Manifest Generation] -> train.tsv, train.wrd, splits
    |                       Output: preprocessed_flat_seg12/433h_data/
[6. K-means Clustering] -> Feature extraction + clustering
    |                      Output: flat_features/, flat_kmeans_200.bin, flat_labels/
[7. VSP-LLM Decode] -> LLM inference (segment-level, no merging)
    |                  Output: decode/vsr/en/
[7a. Merge] -> DISABLED - Segments treated independently
    |          Each segment appears separately in outputs
[8. Client Outputs] -> Segment-level reports + burned videos
    Output: flat_runs_archive/[timestamp]/client_outputs/
    - One report entry per segment
    - One burned video per segment
    - EC2 ONLY: IS score per segment (--compute-is), full IS analysis CSV + JSON
      Requires ENV_TYPE=ec2 (set by lib/config.sh, sourced at pipeline start)

Note: Steps 0.6 and 3.5 implement unified transcription management.
      Whisper only runs ONCE per unique video filename across all pipeline runs!

Architecture: SEGMENT-FIRST NORMALIZATION (since Feb 2026)
      - Raw videos segmented FIRST (Step 0.1) using fast codec copy
      - Normalization works on SEGMENTS (Step 0.5) not whole videos - efficient!
      - For 60-min video: normalize 300x 12s segments instead of 1x 60min video
      - Benefits: Lower memory usage, faster processing, better parallelization
      - Videos split into 12s segments with 2s overlap
      - Each segment processed independently through entire pipeline
      - No merging - segments remain separate in all outputs
      - WER calculated per-video using overlap deduplication
```

## Directory Structure

```
~/
├── auto_avsr/                          # Main ASR training framework
│   ├── train.py, eval.py, lightning.py # Training and evaluation scripts
│   ├── preparation/                    # Video preprocessing scripts
│   │   ├── preprocess_lrs2lrs3.py     # Main preprocessing (mouth crop)
│   │   ├── detectors/                  # Face detection (mediapipe, retinaface)
│   │   └── transforms.py, utils.py     # Data transforms and utilities
│   ├── datamodule/                     # PyTorch Lightning data modules
│   ├── espnet/                         # E2E ASR Conformer model
│   ├── spm/                            # SentencePiece tokenization models
│   ├── flat/                           # Raw input videos (copied from user input)
│   ├── flat_wrd/                       # Whisper ASR outputs (.wrd files)
│   ├── flat_txt/                       # Converted text files
│   ├── preprocess_ready_flat/          # Prepared for preprocessing
│   └── preprocessed_flat_seg4/         # Final preprocessed outputs
│       └── 433h_data/                  # Manifests (train.tsv, train.wrd)
│
├── VSP-LLM/                            # LLM-based visual speech processing
│   ├── src/
│   │   ├── vsp_llm.py                 # Main VSP-LLM model
│   │   ├── vsp_llm_decode.py          # Decoding script
│   │   ├── vsp_llm_dataset.py         # Dataset with cluster deduplication
│   │   ├── hubert.py, hubert_dataset.py # AV-HuBERT components
│   │   ├── conf/                       # Hydra configs
│   │   ├── clustering/                 # K-means feature extraction
│   │   │   ├── dump_hubert_feature.py
│   │   │   ├── learn_kmeans.py
│   │   │   └── dump_km_label.py
│   │   └── dataset/vsr/en/             # Symlinked test manifests
│   ├── scripts/
│   │   ├── train.sh, decode.sh         # Main training/decoding scripts
│   │   ├── run_flat_kmeans.sh          # K-means clustering pipeline
│   │   ├── run_cluster_counts.sh       # Generate cluster counts
│   │   ├── make_report.py              # Generate JSON reports
│   │   └── make_burn.py                # Burn subtitles into videos
│   ├── checkpoints/                    # Model checkpoints
│   │   ├── Llama-2-7b-hf/             # LLaMA2 base model
│   │   ├── large_vox_iter5.pt         # AV-HuBERT pretrained
│   │   └── checkpoint_finetune.pt      # Finetuned VSP-LLM
│   ├── flat_features/                  # Extracted HuBERT features
│   ├── flat_kmeans_200.bin            # Trained k-means model
│   ├── flat_labels/                    # K-means cluster labels
│   └── decode/vsr/en/                  # Decoding outputs
│
├── av_hubert/                          # AV-HuBERT preparation utilities
│   └── avhubert/preparation/
│       ├── flat_to_lrs3_preperation.sh
│       └── split_flat_dataset.py
│
├── vsp_input/                          # User video input directory
│   ├── *.mp4, *.mkv, etc.              # Raw video files
│   ├── .excluded/                      # Excluded videos (not deleted)
│   └── .transcriptions/                # Unified transcription storage (NEW: Jan 25, 2026)
│       ├── *.wrd                       # One file per video (one word per line)
│       └── metadata.json               # Tracks type (auto/manual), timestamps, word counts
│
├── flat_runs_archive/                  # Archived pipeline runs
│   └── [timestamp]/                    # Each run archived by timestamp
│       ├── flat_txt/, preprocess_ready_flat/, etc.
│       └── client_outputs/             # Final deliverables
│           ├── report/                 # Transcription reports (CSV, HTML, TXT, ANSI)
│           │   ├── report.csv          # Per-segment metrics (+ IS columns on EC2)
│           │   ├── report.html         # Color-coded HTML report (+ IS column on EC2)
│           │   ├── intelligibility_scores.csv   # EC2 only: full IS analysis
│           │   └── intelligibility_summary.json # EC2 only: aggregate IS stats
│           ├── burned_videos/          # Videos with burned subtitles
│           └── lip_crops/             # Mouth-cropped segment videos
│
└── run_flat_english_pipeline.sh        # Master pipeline orchestrator
```

## Key Components

### 1. Auto-AVSR (auto_avsr/)
- PyTorch Lightning-based framework for audio-visual speech recognition
- Uses E2E Conformer architecture from ESPNet
- Supports both audio and video modalities
- Frontend: 3D ResNet for visual features, 2D ResNet for audio
- Preprocessing: Mediapipe face detector, 88x88 mouth crops at 25fps

### 2. VSP-LLM (VSP-LLM/)
- Built on Fairseq and integrates LLaMA2-7B
- Uses AV-HuBERT for visual feature extraction (12th layer, 200 clusters)
- Key innovation: Visual speech unit deduplication via cluster_counts
  - Reduces redundant consecutive frames (e.g., held phonemes)
  - Significantly reduces LLM context length
- Tasks: Visual Speech Recognition (VSR) and Visual Speech Translation (VST)

### 3. Fairseq Integration
- Both VSP-LLM and av_hubert use custom Fairseq installations
- VSP-LLM: `~/VSP-LLM/fairseq` (editable install)
- Must set `PYTHONPATH` to include fairseq before running training/decoding

## Segment-Level Architecture (Since Jan 2026)

The pipeline uses a **segment-level architecture** where videos are split into overlapping segments that are processed independently through the entire pipeline. There is **no merging** of predictions - each segment appears as a separate entry in reports and burned videos.

### Segmentation Parameters

- **Segment Duration**: 12 seconds (default, configurable via `SEG_DURATION`)
- **Overlap Duration**: 2 seconds between adjacent segments
- **Stride**: 10 seconds (seg_duration - overlap = 12s - 2s)
- **Minimum Split Duration**: 12 seconds (videos <12s are NOT split)

**Example**: A 60-second video produces 6 segments:
```
Segment 0:  0s - 12s  (frames   0 - 300)
Segment 1: 10s - 22s  (frames 250 - 550) <- 2s overlap with seg 0
Segment 2: 20s - 32s  (frames 500 - 800) <- 2s overlap with seg 1
Segment 3: 30s - 42s  (frames 750 - 1050)
Segment 4: 40s - 52s  (frames 1000 - 1300)
Segment 5: 50s - 60s  (frames 1250 - 1500)
```

### Why 2-Second Overlap?

The 2-second overlap ensures that **words are not cut at segment boundaries**:
- Most words are <1 second in duration
- 2-second overlap guarantees each word appears fully in at least one segment
- Without overlap, words could be split across segments, reducing recognition accuracy

### Segment Naming Convention

Segments use frame-based naming to uniquely identify timing:

**Format**: `{video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4`

**Examples**:
- `Obama_00_000000_000300.mp4` - Segment 0 from frames 0-300
- `Obama_01_000250_000550.mp4` - Segment 1 from frames 250-550
- `VideoA__abc12345_02_000500_000800.mp4` - Segment 2 with hash

**With hash**: `{video_id}__{hash}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4`

The hash (8-character hex) is optional and used to disambiguate videos with identical names.

### Processing Flow

1. **Preprocessing** (Step 3): Videos split into 12s segments with 2s overlap
   - Each segment saved as separate .mp4 file with audio
   - `segment_metadata.json` tracks all segments and their timing

2. **Transcription** (Manual or Whisper): Each segment gets its own transcription
   - Stored in `.transcriptions/{segment_id}.wrd` (one word per line)
   - Users transcribe each segment individually, including overlap regions

3. **Pipeline Processing** (Steps 4-7): Each segment processes independently
   - Manifests (train.tsv, train.wrd) list all segments separately
   - K-means and VSP-LLM treat each segment as independent utterance
   - **No merging** at decode step - segment predictions kept separate

4. **Output Generation** (Step 8): Segment-level outputs
   - **Reports**: One JSON entry per segment with hypothesis and reference
   - **Burned Videos**: One video file per segment with subtitles

### WER Calculation

WER (Word Error Rate) is calculated **per original video**, not per segment, to get meaningful accuracy metrics:

**Script**: `VSP-LLM/scripts/calculate_per_video_wer.py`

**Usage**:
```bash
python /home/ubuntu/VSP-LLM/scripts/calculate_per_video_wer.py \
    --decode-json decode/vsr/en/hypo-685605.json \
    --segment-metadata preprocessed_flat_seg12/segment_metadata.json \
    --output-csv wer_per_video.csv \
    --overlap-seconds 2.0 \
    --segment-duration 12.0
```

**Overlap Deduplication Algorithm**:
1. Group segments by original video using segment IDs
2. Sort segments by index
3. Concatenate predictions:
   - First segment: use all words
   - Subsequent segments: skip first ~17% of words (2s / 12s = overlap region)
4. Calculate editdistance on concatenated hypothesis vs reference
5. WER = 100 x (edit_distance / reference_length)

**Output CSV**:
```csv
video_id,num_segments,ref_words,hyp_words,edit_distance,wer
Obama,6,103,98,29,28.16
Video2,1,45,42,7,15.56
```

**Note**: This is a **heuristic approximation** since we lack word-level timing. For precise overlap handling, forced alignment would be needed.

### Why No Merging?

The segment-level architecture **deliberately avoids merging** for several reasons:

1. **No Word-Level Timing**: Without forced alignment, we cannot reliably identify which words in overlap regions are correct
2. **Simplicity**: Independent segments are easier to understand, debug, and verify
3. **Transparency**: Users can see exactly what the model predicted for each segment
4. **Flexibility**: Segments can be manually reviewed and corrected independently

**Trade-off**: Reports and burned videos contain multiple entries per original video, which can be verbose for long videos. This is acceptable for the improved transparency and simplicity.

### Migration Notes

**Old Pipeline (pre-Jan 2026)**:
- 4-second segments with 1-second overlap
- Merge step attempted to combine overlapping predictions
- One report entry and one burned video per original video

**New Pipeline (Jan 2026+)**:
- 12-second segments with 2-second overlap
- No merging - segments remain independent
- Multiple report entries and burned videos per original video
- WER calculation script for per-video metrics

To use the old behavior:
```bash
export OVERLAP_ENABLED=0
./run_flat_english_pipeline.sh /path/to/videos
```

This disables overlap entirely (videos split without overlap, no merge step attempted).

## Data Format Notes

### Manifest Files (*.tsv)
Tab-separated format used by VSP-LLM:
```
/path/to/lrs3_video_seg24s	video_file.mp4	audio_file.wav	num_frames
```

### Word Files (*.wrd)
Whitespace-separated text transcriptions, one per line corresponding to TSV rows.

### Cluster Counts Files (*.cluster_counts)
Comma-separated cluster IDs showing visual speech units:
```
45,45,67,67,67,123,98,...
```
Used for deduplication during VSP-LLM inference.

### Label Lists (*.csv for auto_avsr)
Format: `dataset,rel_path,input_length,token_ids`
Example: `lrs3,lrs3_video_seg24s/file.mp4,324,1234567890`

## Critical Dependencies

- **PyTorch**: 2.5.1 with CUDA 12.1 support
- **Fairseq**: Custom installations (editable mode from git repos)
- **Transformers**: 4.49.0 (for LLaMA2)
- **Mediapipe**: Used for face/mouth detection (install from wheels)
- **Whisper**: openai-whisper==20250625 for ASR
- **SentencePiece**: 0.1.96 for text tokenization

## Important Implementation Details

### Pipeline State Management
- The main pipeline archives previous outputs before each run to avoid conflicts
- Preprocessed videos in `preprocessed_flat_seg4/` are NOT re-archived (see line 59 in pipeline script) to save time
- Archive location: `~/flat_runs_archive/[YYYYMMDD_HHMMSS]/`
- **Transcription persistence** (NEW): `~/vsp_input/.transcriptions/` is NOT archived and survives all pipeline runs
  - Contains both manual and auto-generated transcriptions
  - Source of truth for all transcription reuse
  - Step 0.6 copies from here to `flat_wrd/` before ASR
  - Step 1.5 saves new Whisper outputs back here

### Symlink Management
- Pipeline creates symlinks in `VSP-LLM/src/dataset/vsr/en/` pointing to train manifests
- These are also symlinked as test.* files for inference (lines 194-200)
- Always check symlink targets before debugging manifest issues

### Feature Extraction
- Uses AV-HuBERT layer 12 features (1024-dim)
- Features extracted at 25fps (same as video)
- K-means trained on PERCENT (default 10%) of training data
- Features are NOT stored long-term, regenerated each pipeline run

### Cluster Deduplication
- Critical for LLM efficiency: reduces consecutive identical clusters
- Format: comma-separated cluster IDs in *.cluster_counts files
- Must match line-by-line with *.tsv and *.wrd files
- Generated by `scripts/build_flat_cluster_counts.py` or `run_cluster_counts.sh`

### Model Checkpoints
- Auto-AVSR models: Stored in `--exp-dir/--exp-name/model_avg_10.pth`
- VSP-LLM checkpoints: `VSP-LLM/checkpoints/checkpoint_finetune.pt`
- Pretrained AV-HuBERT: `VSP-LLM/checkpoints/large_vox_iter5.pt`
- LLaMA2-7B base: `VSP-LLM/checkpoints/Llama-2-7b-hf/`

### Configuration Management
- Auto-AVSR: Command-line arguments (see train.py, eval.py)
- VSP-LLM: Hydra configs in `src/conf/` directory
  - Training: `vsp-llm-433h-freeze.yaml`
  - Decoding: `s2s_decode.yaml`
- Override configs via command line: `key=value` syntax in fairseq-hydra-train

### Decode Configuration (Live)

The decode configuration has been **frozen since 2026-02-17** and is the configuration that produced the headline `english_full_results/` baseline (1,497 segments, WER 64.1%, IS 2.52/5.0). Defined in [VSP-LLM/src/conf/s2s_decode.yaml](../VSP-LLM/src/conf/s2s_decode.yaml) and overridden by [VSP-LLM/scripts/decode.sh](../VSP-LLM/scripts/decode.sh).

| Parameter | Value | Notes |
|---|---|---|
| `beam` | 20 | Pure beam search, deterministic |
| `lenpen` | 0.0 | Paper Section 4.2 — do not change |
| `max_len_a` | 2.0 | dynamic_max_len = 2.0 × src_clusters + 200 |
| `max_len_b` | 200 | Buffer for short-input segments |
| `max_len` | 2048 | Hard cap on dynamic_max_len |
| `no_repeat_ngram_size` | 3 | Blocks degenerate trigram repetitions |
| `repetition_penalty` | 1.2 | CTRL paper, Keskar 2019 |
| `do_sample` | false | Deterministic; `temperature`/`top_p` unused |
| `lm_weight` | 0 | No external LM |
| `dataset.max_tokens` | 3000 | Override in `decode.sh` |
| `modalities` | `['video']` | Visual-only |
| Checkpoint | `checkpoint_finetune.pt` | Released VSP-LLM weights |
| LLM | Llama-2-7b-hf | Frozen backbone |

**Provenance** (VSP-LLM submodule git history for `src/conf/s2s_decode.yaml`):
- `2026-02-01` (`0e494cd`) — first `max_len` tweaks (experimental `max_len_a=3.0`, `max_len_b=300`).
- `2026-02-17` (`585c4d2`) — **operative freeze**: reverted to `max_len_a=2.0`/`max_len_b=200`, added `repetition_penalty=1.2` and `no_repeat_ngram_size=3`.
- `2026-03-01` (`29327d2`) — added `do_sample`/`temperature`/`top_p` keys with `do_sample: false` default; no behavioral change.
- No edits since 2026-03-01.

**Hyperparameter experiments**: 13 one-off variations (Exp A–M) were run on 107 segments via command-line overrides — see [docs/tuning/experiment-comparison.csv](tuning/experiment-comparison.csv) and [docs/tuning/report_2_hyperparameter_tuning.md](tuning/report_2_hyperparameter_tuning.md). Variations covered `beam` (greedy=1), `lenpen` (-0.5 / +1 / +2), `repetition_penalty=1.0`, and stochastic sampling (`do_sample=true`, `temperature` ∈ {0.3, 0.5, 1.0, 1.5}, `top_p=0.9`). **None was promoted** — Exp A (the live config) was the most robust on WER/WWER/NEA. Variations were applied via CLI overrides only; the config files were not edited during tuning.
