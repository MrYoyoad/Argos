# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a visual speech processing (VSP) pipeline that combines three major components for lip-reading and visual speech recognition:

1. **auto_avsr/** - Audio-Visual Speech Recognition framework for preprocessing and training lip-reading models
2. **VSP-LLM/** - Visual Speech Processing with Large Language Models for inference and translation
3. **av_hubert/** - AV-HuBERT model preparation utilities for feature extraction and clustering

The main pipeline (`run_flat_english_pipeline.sh`) orchestrates these components to process raw videos through ASR transcription, mouth cropping, feature extraction, clustering, and LLM-based decoding.

## **Refactored Modular Architecture (January 2026)**

**Mission 1 Complete**: The pipeline has been refactored from a monolithic 823-line script into a modular architecture with reusable components.

### Modular Structure

All pipeline functionality is now organized into **11 modules** under the `lib/` directory:

```
lib/
├── common.sh              # Logging and validation utilities
├── config.sh              # Environment detection (EC2/container) and path configuration
├── archive.sh             # Archive management with transcription preservation
├── normalization.sh       # Video normalization (HDR/10-bit conversion, GPU encoding)
├── asr.sh                 # Whisper ASR with intelligent transcription management
├── lrs3_prep.sh           # LRS3 format conversion
├── manifests.sh           # Manifest and TSV generation
├── clustering.sh          # K-means clustering and cluster counts
├── decode.sh              # VSP-LLM decode
├── outputs.sh             # Client reports and burned videos
└── venv/
    └── venv_utils.sh      # Virtual environment management
```

### Benefits of Refactoring

- **52% Line Reduction**: Main pipeline: 823 → 393 lines
- **Reusability**: Each module can be used independently or in other scripts
- **Testability**: Comprehensive test suite (`lib/test_all_modules.sh`) with 37 tests
- **Maintainability**: Clear separation of concerns, easier debugging
- **Environment-Aware**: Automatic detection of EC2 vs Linux container environment
- **Consistent Error Handling**: Standardized logging and error reporting across all stages

### Module Responsibilities

**Phase 1.1: Infrastructure**
- `common.sh`: Logging (`log_info`, `log_error`, `log_stage`), validation (`validate_directory`)
- `config.sh`: Environment detection, path configuration, derived path functions
- `venv_utils.sh`: Virtual environment activation/deactivation with error handling

**Phase 1.2: Normalization**
- `normalization.sh`: Video normalization with HDR/10-bit tone mapping, GPU acceleration (NVENC), fallback to CPU encoding

**Phase 1.3: Archive**
- `archive.sh`: Archive previous run outputs with special handling to preserve segment transcriptions

**Phase 1.4: Processing Stages**
- `asr.sh`: Whisper ASR with intelligent transcription matching
  - Step 0.6: Copy existing transcriptions (exact + intelligent name matching)
  - Step 3: Run Whisper (skips segments with existing transcriptions)
  - Step 1.5: Save new auto-transcriptions for future reuse
- `lrs3_prep.sh`: Convert flat dataset to LRS3 format
- `manifests.sh`: Generate manifests, splits, TSVs, and segment timing metadata
- `clustering.sh`: K-means feature extraction and cluster count generation

**Phase 1.5: Decode & Outputs**
- `decode.sh`: VSP-LLM decode with symlink setup, merge logic (disabled for segment-level output)
- `outputs.sh`: Generate segment-level reports (JSON) and burned videos

### Virtual Environment Strategy

- **ASR module** (`asr.sh`): Self-contained, activates `ASR_VENV` internally
- **Other modules**: Expect caller to activate `VSP_VENV` (shared across stages 5-8 for efficiency)

This approach minimizes overhead by activating the VSP venv once for multiple stages.

### Transcription Reuse (Step 0.6 Enhancement)

The ASR module includes simple direct transcription matching:

**How it works**:
- Video segments matched 1:1 with transcription files by exact name
- Example: `video_00_000000_000300.mp4` → `video_00_000000_000300.wrd`
- Whisper automatically skips segments with existing `.wrd` files

**Benefit**: Users can manually transcribe specific segments, and those transcriptions persist across all pipeline runs in `.transcriptions/` directory. Whisper skips all matched segments, saving hours of processing time.

### Testing

Run the complete test suite:
```bash
bash /home/ubuntu/lib/test_all_modules.sh
```

All 37 tests validate module exports, functionality, and integration points.

### Git Tags

- `refactor-v1.0` - Modular pipeline refactoring complete (January 2026)
- `ec2-v1.1` - EC2 version with refactored modules
- `container-v1.1` - Linux container version (to be synced)

## **CRITICAL: EC2 and Linux Container Synchronization**

⚠️ **IMPORTANT REQUIREMENT**: This codebase exists in TWO environments:
1. **EC2 Instance** (`/home/ubuntu/`) - Development and testing environment
2. **Linux Container** (`/workspace/`) - Production deployment environment

**MANDATORY RULE**: Every change made to the EC2 version MUST be explicitly replicated to the Linux container version in a compatible way.

### Special Attention Required

**`run_flat_english_pipeline.sh`** - This is the master orchestrator script:
- **EC2 path**: `/home/ubuntu/run_flat_english_pipeline.sh`
- **Linux container path**: `/workspace/run_flat_english_pipeline.sh`
- Any modification to this file in EC2 MUST be carefully translated to the Linux container version
- Path differences must be accounted for:
  - EC2 uses `~/` paths (expands to `/home/ubuntu/`)
  - Linux container uses `/workspace/` paths
- Environment-specific adjustments may be needed for virtual environment activation paths

### Synchronization Checklist

When making changes, ALWAYS:
1. ✅ Make the change in EC2 first and test thoroughly
2. ✅ Identify all affected files (scripts, configs, Python code, UI files)
3. ✅ Translate EC2 paths to Linux container paths:
   - `~/auto_avsr/` → `/workspace/auto_avsr/`
   - `~/VSP-LLM/` → `/workspace/VSP-LLM/`
   - `~/vsp_input/` → `/workspace/vsp_input/`
   - Virtual environment paths (adjust as needed)
4. ✅ Update the "Pending Changes for Linux Container Version" section below with detailed instructions
5. ✅ Document the change with:
   - Date of change
   - Affected files in both environments
   - Specific line numbers or code blocks that changed
   - Any environment-specific considerations

### Common Files That Need Dual Updates

- **Pipeline Scripts**:
  - `run_flat_english_pipeline.sh` (MOST CRITICAL)
  - `VSP-LLM/scripts/run_flat_kmeans.sh`
  - `VSP-LLM/scripts/decode.sh`
  - `auto_avsr/preparation/make_preprocess_ready.sh`
  - `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh`

- **VSP UI Components** (if changes affect UI):
  - `vsp-ui/app/server.py`
  - `vsp-ui/app/services/*.py`
  - `vsp-ui/app/static/*.html`, `*.js`, `*.css`

- **Configuration Files**:
  - Any Hydra configs in `VSP-LLM/src/conf/`
  - Python script arguments and paths

### Why This Matters

- The Linux container is the PRODUCTION environment used by end users
- Features tested in EC2 that don't make it to the container create inconsistent behavior
- Pipeline script changes are especially critical as they orchestrate the entire workflow
- Forgetting to sync can result in hours of debugging when deployed

**Bottom Line**: Treat every EC2 change as incomplete until it's documented and ready for Linux container deployment.

## Main Pipeline Commands

### Running the Complete Pipeline

```bash
./run_flat_english_pipeline.sh /path/to/raw_videos_dir
```

This executes all stages:
1. ASR transcription (Whisper) to generate .wrd files
2. Video preprocessing and mouth cropping (mediapipe detector, 4-second segments)
3. Manifest and TSV generation
4. K-means clustering (200 clusters) on AV-HuBERT features
5. VSP-LLM decoding for final transcription
6. Client output generation (reports and burned videos)

**Important**: Previous run outputs are automatically archived to `~/flat_runs_archive/[timestamp]/` before each pipeline run.

### Individual Component Commands

#### Auto-AVSR Training
```bash
# Activate preprocessing environment
source ~/auto_avsr/pre-process-venv/bin/activate

# Train a model
python ~/auto_avsr/train.py \
  --exp-dir=./exp \
  --exp-name=my_experiment \
  --modality=video \
  --root-dir=/path/to/preprocessed/data \
  --train-file=train_labels.csv \
  --num-nodes=1
```

#### Auto-AVSR Evaluation
```bash
python ~/auto_avsr/eval.py \
  --modality=video \
  --root-dir=/path/to/preprocessed/data \
  --test-file=test_labels.csv \
  --pretrained-model-path=./exp/my_experiment/model_avg_10.pth
```

#### VSP-LLM Training
```bash
cd ~/VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate

# Edit scripts/train.sh to set DATA_PATH and OUT_PATH
bash scripts/train.sh
```

#### VSP-LLM Decoding
```bash
cd ~/VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate

# Edit scripts/decode.sh to set LANG, MODEL_PATH, OUT_PATH
bash scripts/decode.sh
```

#### Preprocessing Videos
```bash
source ~/auto_avsr/pre-process-venv/bin/activate
cd ~/auto_avsr/preparation

python preprocess_lrs2lrs3.py \
  --data-dir /path/to/raw/data \
  --root-dir /path/to/output \
  --dataset flat \
  --detector mediapipe \
  --gpu_type cuda \
  --subset train \
  --seg-duration 4 \
  --groups 1 \
  --job-index 0
```

## Virtual Environments

The codebase uses three separate Python virtual environments:

- **~/auto_avsr/pre-process-venv** - For ASR and preprocessing (Whisper, mediapipe, opencv)
- **~/vsp-llm-yoad-venv** - For VSP-LLM training/inference (PyTorch, transformers, fairseq)
- **~/project/ron/.venv** - For miscellaneous tools (if used)

Always activate the appropriate environment before running commands from that component.

## Architecture & Data Flow

### High-Level Pipeline Flow

```
Raw Videos (.mp4)
    ↓
[0.6 Transcription Reuse] → Copy existing .transcriptions/*.wrd → flat_wrd/
    ↓                        (Enables Whisper skip for existing transcriptions)
[1. ASR - Whisper] → .wrd transcription files (skips videos with existing .wrd)
    ↓
[1.5 Save Transcriptions] → Copy new flat_wrd/*.wrd → .transcriptions/
    ↓                        (Persist Whisper outputs for future reuse)
[2. make_preprocess_ready.sh] → Prepare directory structure
    ↓
[3. preprocess_lrs2lrs3.py] → Mouth cropping + segmentation
    ↓                          (mediapipe, 12s segments, 2s overlap)
    ↓                          Output: preprocessed_flat_seg12/
[4. flat_to_lrs3_preperation.sh] → Convert to LRS3 format
    ↓
[5. Manifest Generation] → train.tsv, train.wrd, splits
    ↓                       Output: preprocessed_flat_seg12/433h_data/
[6. K-means Clustering] → Feature extraction + clustering
    ↓                      Output: flat_features/, flat_kmeans_200.bin, flat_labels/
[7. VSP-LLM Decode] → LLM inference (segment-level, no merging)
    ↓                  Output: decode/vsr/en/
[7a. Merge] → DISABLED - Segments treated independently
    ↓          Each segment appears separately in outputs
[8. Client Outputs] → Segment-level reports + burned videos
    Output: flat_runs_archive/[timestamp]/client_outputs/
    - One report entry per segment
    - One burned video per segment

Note: Steps 0.6 and 1.5 implement unified transcription management.
      Whisper only runs ONCE per unique video filename across all pipeline runs!

Architecture: SEGMENT-LEVEL (since Jan 2026)
      - Videos split into 12s segments with 2s overlap
      - Each segment processed independently through entire pipeline
      - No merging - segments remain separate in all outputs
      - WER calculated per-video using overlap deduplication
```

### Directory Structure

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
│           ├── report/                 # JSON transcription reports
│           └── burned_videos/          # Videos with burned subtitles
│
└── run_flat_english_pipeline.sh        # Master pipeline orchestrator
```

### Key Components

#### 1. Auto-AVSR (auto_avsr/)
- PyTorch Lightning-based framework for audio-visual speech recognition
- Uses E2E Conformer architecture from ESPNet
- Supports both audio and video modalities
- Frontend: 3D ResNet for visual features, 2D ResNet for audio
- Preprocessing: Mediapipe face detector, 88x88 mouth crops at 25fps

#### 2. VSP-LLM (VSP-LLM/)
- Built on Fairseq and integrates LLaMA2-7B
- Uses AV-HuBERT for visual feature extraction (12th layer, 200 clusters)
- Key innovation: Visual speech unit deduplication via cluster_counts
  - Reduces redundant consecutive frames (e.g., held phonemes)
  - Significantly reduces LLM context length
- Tasks: Visual Speech Recognition (VSR) and Visual Speech Translation (VST)

#### 3. Fairseq Integration
- Both VSP-LLM and av_hubert use custom Fairseq installations
- VSP-LLM: `~/VSP-LLM/fairseq` (editable install)
- Must set `PYTHONPATH` to include fairseq before running training/decoding

### Segment-Level Architecture (Since Jan 2026)

The pipeline uses a **segment-level architecture** where videos are split into overlapping segments that are processed independently through the entire pipeline. There is **no merging** of predictions - each segment appears as a separate entry in reports and burned videos.

#### Segmentation Parameters

- **Segment Duration**: 12 seconds (default, configurable via `SEG_DURATION`)
- **Overlap Duration**: 2 seconds between adjacent segments
- **Stride**: 10 seconds (seg_duration - overlap = 12s - 2s)
- **Minimum Split Duration**: 12 seconds (videos <12s are NOT split)

**Example**: A 60-second video produces 6 segments:
```
Segment 0:  0s - 12s  (frames   0 - 300)
Segment 1: 10s - 22s  (frames 250 - 550) ← 2s overlap with seg 0
Segment 2: 20s - 32s  (frames 500 - 800) ← 2s overlap with seg 1
Segment 3: 30s - 42s  (frames 750 - 1050)
Segment 4: 40s - 52s  (frames 1000 - 1300)
Segment 5: 50s - 60s  (frames 1250 - 1500)
```

#### Why 2-Second Overlap?

The 2-second overlap ensures that **words are not cut at segment boundaries**:
- Most words are <1 second in duration
- 2-second overlap guarantees each word appears fully in at least one segment
- Without overlap, words could be split across segments, reducing recognition accuracy

#### Segment Naming Convention

Segments use frame-based naming to uniquely identify timing:

**Format**: `{video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4`

**Examples**:
- `Obama_00_000000_000300.mp4` - Segment 0 from frames 0-300
- `Obama_01_000250_000550.mp4` - Segment 1 from frames 250-550
- `VideoA__abc12345_02_000500_000800.mp4` - Segment 2 with hash

**With hash**: `{video_id}__{hash}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4`

The hash (8-character hex) is optional and used to disambiguate videos with identical names.

#### Processing Flow

1. **Preprocessing** ([Step 3](#high-level-pipeline-flow)): Videos split into 12s segments with 2s overlap
   - Each segment saved as separate .mp4 file with audio
   - `segment_metadata.json` tracks all segments and their timing

2. **Transcription** (Manual or Whisper): Each segment gets its own transcription
   - Stored in `.transcriptions/{segment_id}.wrd` (one word per line)
   - Users transcribe each segment individually, including overlap regions

3. **Pipeline Processing** ([Steps 4-7](#high-level-pipeline-flow)): Each segment processes independently
   - Manifests (train.tsv, train.wrd) list all segments separately
   - K-means and VSP-LLM treat each segment as independent utterance
   - **No merging** at decode step - segment predictions kept separate

4. **Output Generation** ([Step 8](#high-level-pipeline-flow)): Segment-level outputs
   - **Reports**: One JSON entry per segment with hypothesis and reference
   - **Burned Videos**: One video file per segment with subtitles

#### WER Calculation

WER (Word Error Rate) is calculated **per original video**, not per segment, to get meaningful accuracy metrics:

**Script**: [`/home/ubuntu/VSP-LLM/scripts/calculate_per_video_wer.py`](vsp_llm/scripts/calculate_per_video_wer.py)

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
5. WER = 100 × (edit_distance / reference_length)

**Output CSV**:
```csv
video_id,num_segments,ref_words,hyp_words,edit_distance,wer
Obama,6,103,98,29,28.16
Video2,1,45,42,7,15.56
```

**Note**: This is a **heuristic approximation** since we lack word-level timing. For precise overlap handling, forced alignment would be needed.

#### Why No Merging?

The segment-level architecture **deliberately avoids merging** for several reasons:

1. **No Word-Level Timing**: Without forced alignment, we cannot reliably identify which words in overlap regions are correct
2. **Simplicity**: Independent segments are easier to understand, debug, and verify
3. **Transparency**: Users can see exactly what the model predicted for each segment
4. **Flexibility**: Segments can be manually reviewed and corrected independently

**Trade-off**: Reports and burned videos contain multiple entries per original video, which can be verbose for long videos. This is acceptable for the improved transparency and simplicity.

#### Migration Notes

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

### Data Format Notes

#### Manifest Files (*.tsv)
Tab-separated format used by VSP-LLM:
```
/path/to/lrs3_video_seg24s	video_file.mp4	audio_file.wav	num_frames
```

#### Word Files (*.wrd)
Whitespace-separated text transcriptions, one per line corresponding to TSV rows.

#### Cluster Counts Files (*.cluster_counts)
Comma-separated cluster IDs showing visual speech units:
```
45,45,67,67,67,123,98,...
```
Used for deduplication during VSP-LLM inference.

#### Label Lists (*.csv for auto_avsr)
Format: `dataset,rel_path,input_length,token_ids`
Example: `lrs3,lrs3_video_seg24s/file.mp4,324,1234567890`

### Critical Dependencies

- **PyTorch**: 2.5.1 with CUDA 12.1 support
- **Fairseq**: Custom installations (editable mode from git repos)
- **Transformers**: 4.49.0 (for LLaMA2)
- **Mediapipe**: Used for face/mouth detection (install from wheels)
- **Whisper**: openai-whisper==20250625 for ASR
- **SentencePiece**: 0.1.96 for text tokenization

## Testing

There are no automated test suites in this codebase. Testing is done by:

1. Running the full pipeline on sample videos
2. Inspecting decode outputs (JSON hypo files)
3. Checking WER (Word Error Rate) on evaluation sets

To test pipeline stages individually:
```bash
# Test ASR only
source ~/auto_avsr/pre-process-venv/bin/activate
python ~/auto_avsr/asr_to_words_notime.py \
  --in_videos /path/to/test/videos \
  --out_wrd /tmp/test_wrd \
  --model medium --lang en

# Test preprocessing on single video
cd ~/auto_avsr/preparation
python preprocess_lrs2lrs3.py \
  --data-dir /path/to/single/video \
  --root-dir /tmp/test_preprocess \
  --dataset flat --detector mediapipe \
  --subset train --seg-duration 4

# Test decode on small manifest
cd ~/VSP-LLM
bash scripts/decode.sh  # (after editing paths to small test set)
```

## Common Development Workflows

### Adding Support for New Languages

1. Train new SentencePiece model in `auto_avsr/spm/`
2. Update paths in `auto_avsr/preparation/transforms.py` and `auto_avsr/datamodule/transforms.py`
3. Modify `run_flat_english_pipeline.sh` LANG variable
4. Adjust Whisper model and language parameters in ASR step

### Fine-tuning VSP-LLM on New Data

1. Prepare data following LRS3 format (use auto_avsr preprocessing)
2. Generate manifests (train.tsv, train.wrd)
3. Extract features and train k-means: `bash VSP-LLM/scripts/run_flat_kmeans.sh`
4. Generate cluster_counts: `bash VSP-LLM/scripts/run_cluster_counts.sh`
5. Edit `VSP-LLM/scripts/train.sh` with DATA_PATH
6. Run: `bash VSP-LLM/scripts/train.sh`

### Debugging Pipeline Failures

- Check logs in `~/flat_runs_latest.log` (created by pipeline)
- Archived logs available in `~/flat_runs_archive/[timestamp]/`
- For preprocessing errors: check `auto_avsr/preparation/preprocess_*.log`
- For decoding errors: check `VSP-LLM/decode/` for hypo JSON files

### Modifying Preprocessing Parameters

Key parameters in `preprocess_lrs2lrs3.py`:
- `--seg-duration`: Segment length (default 4 seconds)
- `--detector`: Face detector (mediapipe, retinaface)
- `--gpu_type`: cuda or cpu
- Output resolution: 88x88 mouth crops at 25fps (hardcoded in detectors)

### Changing K-means Clusters

Currently uses 200 clusters. To change:
1. Edit `run_flat_kmeans.sh` or `VSP-LLM/scripts/run_flat_kmeans.sh`
2. Change cluster count in `learn_kmeans.py` call (line 76)
3. Retrain k-means and regenerate all labels
4. Model configs in `VSP-LLM/src/conf/` may need adjustment

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

## Troubleshooting

### "FileNotFoundError" in preprocessing
- Ensure input directory structure matches expected format
- Check that video files have audio tracks (or use silent audio flag)
- Verify detector weights are available (mediapipe requires specific packages)

### "No mouth detected" errors
- Try different detector (mediapipe vs retinaface)
- Check video quality and face visibility
- Adjust detection thresholds in `preparation/detectors/`

### CUDA out of memory
- Reduce batch size in training configs
- Use gradient checkpointing (if available)
- Process videos in smaller batches during preprocessing

### Decode outputs empty or incorrect
- Verify all three files exist and align: train.tsv, train.wrd, train.cluster_counts
- Check symlinks in `VSP-LLM/src/dataset/vsr/en/`
- Ensure checkpoint paths are correct in decode.sh
- Verify PYTHONPATH includes fairseq

### K-means training takes too long
- Reduce PERCENT in run_flat_kmeans.sh (default 0.1 = 10%)
- Use fewer shards (NSHARD=1 for small datasets)
- Skip retraining if k-means model already exists (TRAIN_KMEANS=0)

## Pending Changes for Linux Container Version

The following changes have been made to the EC2 version and need to be replicated on the standalone Linux container:

### VSP UI Features (Added Jan 19, 2026)
1. **Video Exclusion Feature**: Users can exclude videos from processing without permanently deleting them
   - Frontend: Added remove buttons to video list items in `app/static/index.html` and `app/static/app.js`
   - Frontend: `removeVideo()` function calls `/api/remove-video` endpoint with confirmation dialog
   - Backend: `handle_remove_video()` moves videos to `~/vsp_input/.excluded/` folder instead of deleting (`app/server.py`)
   - Validator: Updated to skip videos in `.excluded` folder when scanning (`app/services/validator.py`)
   - Security: Path traversal protection (rejects filenames with .., /, \)
   - Note: Excluded videos remain in `.excluded/` folder and can be manually moved back if needed

2. **K-means Training Toggle**: Added checkbox to skip k-means training and use existing model
   - Frontend: Added checkbox in validation screen (`app/static/index.html`)
   - Frontend: Pass `train_kmeans` option in start request (`app/static/app.js`)
   - Backend: Accept `train_kmeans` parameter in `handle_start()` (`app/server.py`)
   - Backend: Pass to `PipelineRunner.start(train_kmeans=...)` (`app/services/pipeline_runner.py`)
   - Backend: Set `TRAIN_KMEANS` environment variable (0 or 1) in `_get_env()` (`app/services/pipeline_runner.py`)
   - **CRITICAL Pipeline Fix**: Change line 318-321 in `run_flat_english_pipeline.sh`:
     ```bash
     # BEFORE:
     LRS3_ROOT="$PREP_ROOT" \
     SPLIT="train" \
     NSHARD=1 \
     TRAIN_KMEANS=1 \

     # AFTER:
     TRAIN_KMEANS="${TRAIN_KMEANS:-1}" \
     LRS3_ROOT="$PREP_ROOT" \
     SPLIT="train" \
     NSHARD=1 \
     ```
   - This allows the environment variable to override the hardcoded value

3. **Unified Transcription Management** (Added Jan 25, 2026): Persistent storage for all transcriptions (manual + Whisper auto-generated)
   - **Overview**: All transcriptions stored in `~/vsp_input/.transcriptions/` for reuse across pipeline runs
   - **Key Benefit**: Whisper only runs once per video - huge time savings on subsequent runs!

   **Storage Architecture**:
   - Location: `~/vsp_input/.transcriptions/` (survives pipeline archiving)
   - Format: One `.wrd` file per video (one word per line, lowercase, alphanumeric)
   - Metadata: `metadata.json` tracks type (auto/manual), timestamps, word counts
   - Badges: `[AUTO]` (orange) for Whisper-generated, `[MANUAL]` (green) for user-entered/edited

   **Pipeline Integration**:
   - **Step 0.6** (NEW): Copies existing `.transcriptions/*.wrd` → `~/auto_avsr/flat_wrd/` BEFORE Whisper runs
   - **Step 1.5** (NEW): Saves new Whisper outputs → `.transcriptions/` AFTER ASR completes
   - **Result**: ASR script (`asr_to_words_notime.py`) automatically skips videos with existing .wrd files (built-in logic at lines 106-108)
   - Modified file: `run_flat_english_pipeline.sh` (added Steps 0.6 and 1.5)

   **Frontend Features**:
   - **Modal Dialog**: Click "Add/Edit Transcription" button on any video
     - Enter text (space or newline separated)
     - Live preview shows normalized output (matches ASR format)
     - Edit [AUTO] transcription → warns "will mark as [MANUAL]"
   - **Orphaned Transcriptions Section**: Shows transcriptions for videos not in input folder
     - [Keep] button - dismiss from list, keep transcription
     - [Delete] button - permanently delete transcription file
   - **Visual Indicators**: Badge colors clearly show [AUTO] vs [MANUAL] status

   **Backend Components**:
   - New file: `app/services/transcription_manager.py` - Core business logic
     - CRUD operations for `.wrd` files
     - Text normalization (matches ASR: lowercase, alphanumeric + apostrophes)
     - Metadata tracking and orphan detection
   - API Endpoints (added to `app/server.py`):
     - `GET /api/transcription?filename=video.mp4` - Get transcription text and metadata
     - `POST /api/transcription` - Save or delete transcription
     - `GET /api/orphaned-transcriptions` - List orphaned transcriptions
   - Validator enhancement (`app/services/validator.py`):
     - Added `has_transcription` and `transcription_type` fields to `VideoInfo` dataclass
     - Checks for existing transcriptions during validation
     - New function: `get_video_files()` for orphan detection

   **Data Flow Examples**:
   ```
   First Pipeline Run:
   video1.mp4 → Whisper transcribes → saved as .transcriptions/video1.wrd [AUTO]

   Second Pipeline Run (same video):
   video1.mp4 → Step 0.6 copies existing .wrd → Whisper SKIPS (huge time save!)

   Manual Transcription:
   video2.mp4 → User clicks "Add Transcription" → enters text → [MANUAL]
   → Next pipeline run: Whisper SKIPS, uses manual transcription

   Edit Auto Transcription:
   video1.mp4 [AUTO] → User clicks "Edit" → modifies text
   → Confirms: "This will mark as [Manual]" → becomes [MANUAL]

   Orphan Management:
   Remove video2.mp4 from ~/vsp_input/ folder
   → Validation shows in "Orphaned Transcriptions" section
   → User chooses: [Keep] or [Delete]

   Re-add Video:
   Add video1.mp4 back to folder after removal
   → Transcription still exists → pipeline reuses it immediately!
   ```

   **Important Behaviors**:
   - Manual transcriptions NEVER overwritten by Whisper (Step 1.5 checks before copying)
   - Editing any [AUTO] transcription converts it to [MANUAL] (with user confirmation)
   - Transcriptions persist when videos removed/re-added
   - Pipeline archives (`~/flat_runs_archive/`) do NOT include `.transcriptions/` source folder
   - All transcriptions flow through entire pipeline as ground truth references in reports

### Files Modified for Linux Container:

**Video Exclusion & K-means Toggle (Jan 19, 2026)**:
- `/workspace/vsp-ui/app/static/index.html` - Add processing options section with k-means checkbox
- `/workspace/vsp-ui/app/static/style.css` - Add CSS for checkbox and remove buttons
- `/workspace/vsp-ui/app/static/app.js` - Add removeVideo() function and train_kmeans parameter
- `/workspace/vsp-ui/app/server.py` - Update handle_start() to accept train_kmeans
- `/workspace/vsp-ui/app/services/pipeline_runner.py` - Add train_kmeans parameter and env variable

**Unified Transcription Management (Jan 25, 2026)**:
- `/workspace/vsp-ui/app/services/transcription_manager.py` - NEW FILE - Core transcription business logic
- `/workspace/vsp-ui/app/server.py` - Add transcription API endpoints (GET/POST transcription, GET orphaned)
- `/workspace/vsp-ui/app/services/validator.py` - Add has_transcription/transcription_type fields, get_video_files()
- `/workspace/run_flat_english_pipeline.sh` - Add Steps 0.6 (pre-copy) and 1.5 (post-save)
- `/workspace/vsp-ui/app/static/index.html` - Add transcription modal and orphaned section
- `/workspace/vsp-ui/app/static/app.js` - Add transcription modal logic, orphan management, display updates
- `/workspace/vsp-ui/app/static/style.css` - Add modal styling, badges, orphaned section styles

**See detailed step-by-step implementation guide:** `/home/ubuntu/transcription_update_steps.md` or `LINUX_CONTAINER_UPDATES.md`

4. **Segment Duration Update** (Added Jan 25, 2026): Increase default segment duration from 4s to 12s
   - **Overview**: Changes default segment duration across pipeline and UI for consistency
   - **Key Changes**:
     - `SEG_DURATION`: 4 → 12 seconds
     - `MIN_SPLIT_DURATION`: 8.0 → 24.0 seconds (maintains 2x relationship)
     - Frontend dynamically displays correct threshold from backend config

   **Pipeline Changes** (`/workspace/run_flat_english_pipeline.sh`):
   - Line ~25: `SEG_DURATION="${SEG_DURATION:-12}"` (was 4)
   - Line ~30: `MIN_SPLIT_DURATION="24.0"` (was 8.0)
   - Line ~31: Add `export OVERLAP_ENABLED SEG_DURATION` if not present
   - Line ~313: `--seg-duration "$SEG_DURATION"` (replace hardcoded 4)
   - Line ~334: `--seg-duration "$SEG_DURATION"` (replace hardcoded 4)
   - Line ~322: Update echo to `seg=${SEG_DURATION}s` (replace hardcoded 4s)

   **Backend Config** (`/workspace/vsp-ui/app/config.py`):
   - Line ~24: `SEGMENT_DURATION = 12` (was 4)
   - Line ~25: Add `MIN_SPLIT_DURATION = 24.0` (new constant)

   **Backend Validator** (`/workspace/vsp-ui/app/services/validator.py`):
   - Import: Add `MIN_SPLIT_DURATION` to imports from config
   - ValidationResult dataclass: Add `segment_duration: int` and `min_split_duration: float` fields
   - to_dict method: Add both new fields to returned dictionary
   - Both ValidationResult returns: Add `segment_duration=SEGMENT_DURATION, min_split_duration=MIN_SPLIT_DURATION`

   **Frontend HTML** (`/workspace/vsp-ui/app/static/index.html`):
   - Line ~123: Change span text from ">8s" to ">24s"
   - Line ~123: Add `id="overlap-label-text"` to span element for dynamic updates

   **Frontend JS** (`/workspace/vsp-ui/app/static/app.js`):
   - In `displayValidationResults()` function, after stats update:
     ```javascript
     // Update overlap label with dynamic min_split_duration
     const overlapLabel = document.getElementById('overlap-label-text');
     if (overlapLabel && result.min_split_duration) {
         overlapLabel.textContent = `Enable overlapping segments for videos >${result.min_split_duration}s`;
     }
     ```

**Segment Duration Update Files Modified for Linux Container (Jan 25, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Update SEG_DURATION and MIN_SPLIT_DURATION defaults, use variables
- `/workspace/vsp-ui/app/config.py` - Update SEGMENT_DURATION and add MIN_SPLIT_DURATION
- `/workspace/vsp-ui/app/services/validator.py` - Add fields to ValidationResult and pass to frontend
- `/workspace/vsp-ui/app/static/index.html` - Add id to span and update default text
- `/workspace/vsp-ui/app/static/app.js` - Add dynamic text update in displayValidationResults()

**See detailed implementation guide:** `/home/ubuntu/SEGMENT_DURATION_UPDATE.md`

5. **UI Status Bar Fix** (Added Jan 25, 2026): Align UI pipeline stages with actual pipeline script steps
   - **Overview**: Fixed mismatch between UI progress tracking and actual pipeline execution steps
   - **Problem**: config.py stage definitions were completely out of sync with run_flat_english_pipeline.sh
   - **Key Changes**: Updated PIPELINE_STAGES and STAGE_MARKERS to match actual pipeline flow

   **EC2 Backend Config** (`/home/ubuntu/vsp-ui/app/config.py`):
   - Updated `PIPELINE_STAGES` array (lines 37-48):
     - Added "normalize" stage for [0.5] video normalization (HDR/10-bit conversion)
     - Renamed "preprocess_ready" → "prepare_dirs" for [1] directory setup
     - Reordered "preprocess" and "asr" to match actual pipeline ([2] = preprocess, [3] = ASR)
     - Adjusted weights for better progress representation
   - Updated `STAGE_MARKERS` regex patterns (lines 51-62):
     - Fixed all stage markers to match actual pipeline output
     - [0.5] → normalize, [1] → prepare_dirs, [2] → preprocess, [3] → asr
     - [4] → lrs3_prep, [5] → manifests, [6] → kmeans
     - [7] → decode (not skipped!), [8] → client_outputs

   **Before (Incorrect Mapping)**:
   ```python
   # Old config.py was completely misaligned
   "asr": r">>> \[1\]",           # Wrong! [1] is prepare dirs, not ASR
   "preprocess_ready": r">>> \[2\]",  # Wrong! [2] is preprocess, not prepare
   "preprocess": r">>> \[3\]",    # Wrong! [3] is ASR, not preprocess
   "decode": r">>> \[8\]",        # Wrong! [8] is client outputs, not decode
   # Missing [0.5] video normalization stage entirely
   ```

   **After (Correct Mapping)**:
   ```python
   # New config.py correctly aligned with pipeline
   "normalize": r">>> \[0\.5\]",      # [0.5] Video normalization (NEW)
   "prepare_dirs": r">>> \[1\]",      # [1] Prepare directories
   "preprocess": r">>> \[2\]",        # [2] Mouth cropping
   "asr": r">>> \[3\] Running ASR",   # [3] ASR transcription
   "lrs3_prep": r">>> \[4\]",         # [4] LRS3 format conversion
   "manifests": r">>> \[5\] Building manifests",  # [5] Manifests
   "kmeans": r">>> \[6\]",            # [6] K-means clustering
   "decode": r">>> \[7\] Running VSP-LLM",  # [7] Decode (not skipped!)
   "client_outputs": r">>> \[8\] Building client",  # [8] Client outputs
   ```

   **Impact**:
   - UI now correctly shows progress through all 10 stages (was showing 9)
   - Stage names and descriptions match what's actually happening
   - Progress percentages more accurately reflect pipeline completion
   - Users see "Normalize Videos" stage instead of jumping straight to ASR
   - No more confusion about "step 7 is skipped" - it's the decode step!

**UI Status Bar Files Modified for Linux Container (Jan 25, 2026)**:
- `/workspace/vsp-ui/app/config.py` - Update PIPELINE_STAGES array and STAGE_MARKERS dict
  - Exact changes: Replace lines 37-62 with corrected version shown above
  - CRITICAL: Must match actual pipeline steps in `/workspace/run_flat_english_pipeline.sh`

6. **Original Video Serving for Manual Transcription** (Added Jan 27, 2026): Serve full-frame original videos instead of mouth crops
   - **Overview**: Modified segment video API to extract clips from original videos for better transcription context
   - **Problem**: Mouth-cropped videos (88x88) made it hard to understand context during manual transcription
   - **Solution**: Dynamically extract segments from original full-frame videos using ffmpeg

   **How It Works**:
   1. Parse segment ID to extract video name and segment index
   2. Load `segment_metadata.json` to get timing information (start_sec, duration)
   3. Use ffmpeg to extract clip from original video in `~/auto_avsr/flat/`
   4. Serve extracted segment with full resolution and audio

   **FFmpeg Extraction**:
   - Primary method: Codec copy (fast, no re-encoding)
     ```bash
     ffmpeg -ss <start> -i <original> -t <duration> -c copy output.mp4
     ```
   - Fallback: Re-encode if codec copy fails (libx264 + aac, ultrafast preset)
   - Temporary files cleaned up after serving
   - 30-second timeout to prevent hanging

   **Benefits**:
   - ✅ Full context: Users see complete video frame
   - ✅ Better quality: Original resolution and encoding
   - ✅ Audio preserved: Full audio track included
   - ✅ Fast extraction: 1-2 seconds per segment (codec copy)
   - ✅ No storage overhead: Generated on-demand

   **Files Modified**:
   - `/home/ubuntu/vsp-ui/app/server.py` - Updated `handle_get_segment_video()` method (lines 519-637)
   - `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/server.py` - Same changes for Linux container

   **Testing**:
   - ✅ All 5 tests pass: segment ID parsing, metadata loading, original videos exist, ffmpeg extraction works
   - Test script: `/tmp/test_original_video_serving.py`

   **Documentation**: See `/home/ubuntu/ORIGINAL_VIDEO_SERVING.md` for detailed implementation

**Original Video Serving Files Modified for Linux Container (Jan 27, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Replace `handle_get_segment_video()` method with ffmpeg-based extraction
  - Exact changes: Lines 519-547 replaced with new 119-line implementation
  - CRITICAL: Requires ffmpeg to be installed in the container environment

7. **TranscriptionManager API Fix** (Added Jan 29, 2026): Fixed incorrect method call in segments endpoint
   - **Problem**: Code was calling `transcription_mgr.get_metadata()` which doesn't exist in TranscriptionManager
   - **Error**: `'TranscriptionManager' object has no attribute 'get_metadata'`
   - **Impact**: "Inspect Videos" button was failing, preventing users from viewing/excluding videos before processing

   **The Fix**:
   - Changed `get_metadata()` to `get_transcription_info()` (the correct method name)
   - Updated return value access from `meta.get("type")` to `info.type` (TranscriptionInfo is an object, not a dict)

   **Code Change** (around line 273 in server.py):
   ```python
   # BEFORE (incorrect):
   if has_transcription:
       meta = transcription_mgr.get_metadata(f"{segment_id}.mp4")
       transcription_type = meta.get("type") if meta else "auto"

   # AFTER (correct):
   if has_transcription:
       info = transcription_mgr.get_transcription_info(f"{segment_id}.mp4")
       transcription_type = info.type if info else "auto"
   ```

**TranscriptionManager Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Fix method call in handle_get_segments() around line 273
  - Change: Replace `get_metadata()` with `get_transcription_info()`
  - Change: Replace `meta.get("type")` with `info.type`
  - Critical: Without this fix, the validate endpoint fails and "Inspect Videos" button doesn't work

8. **Segment Transcription Type Badge Fix** (Added Jan 29, 2026): Fixed segments showing [AUTO] badge when they have manual transcriptions
   - **Problem**: Segments with transcriptions in `flat_text_seg12s/` folder were showing [AUTO] badge instead of [MANUAL]
   - **Root Cause**: The `/api/segments` endpoint wasn't including `transcription_type` field in response
   - **Impact**: UI displayed incorrect badge color and type for segments with manual transcriptions

   **The Fix**:
   - Added `transcription_type` field to segment response objects in both `handle_get_segments()` and `_load_segment_info()`
   - Added fallback logic to check `flat_text_seg12s/` folder for .txt transcription files
   - Correctly sets type="manual" for transcriptions found in either location
   - Default to "manual" (not "auto") when metadata is missing, since files in `.transcriptions/` are typically manually created

   **Key Changes**:
   1. `handle_get_segments()` (lines 572-620):
      - Added `transcription_type = None` initialization
      - Gets type from TranscriptionManager metadata when .wrd file exists
      - Checks `flat_text_seg12s/` folder as fallback for .txt files
      - Includes `'transcription_type': transcription_type` in response

   2. `_load_segment_info()` (lines 257-298):
      - Same fallback logic to check `flat_text_seg12s/` folder
      - Consistent type determination logic

   **Behavior After Fix**:
   - Segments with .wrd files in `.transcriptions/` → type from metadata (or "manual" if missing)
   - Segments with .txt files in `flat_text_seg12s/` → type="manual"
   - Segments with no transcription → type=None (displayed as [NO TRANSCRIPTION])

**Segment Transcription Type Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Update both segment loading methods
  - `handle_get_segments()` (lines ~572-620):
    - Add `transcription_type = None` initialization
    - Add fallback check for `flat_text_seg{SEGMENT_DURATION}s` folder
    - Add `'transcription_type': transcription_type` to response dict
    - Import `AUTO_AVSR_DIR` and `SEGMENT_DURATION` from config
  - `_load_segment_info()` (lines ~257-298):
    - Add same fallback logic for `flat_text_seg{SEGMENT_DURATION}s` folder
    - Import `AUTO_AVSR_DIR` and `SEGMENT_DURATION` from config
  - Critical: Without this fix, segments with manual transcriptions incorrectly show [AUTO] badge

8. **Delete Transcription Screen Fix** (Added Jan 29, 2026): Fixed crash when deleting transcriptions from segment review screen
   - **Problem**: Clicking "Delete" button on segment review screen caused JavaScript error
   - **Error**: `"Failed to delete: Cannot set properties of null (setting 'textContent')"`
   - **Impact**: Users unable to delete transcriptions after segmentation completed

   **The Issue**:
   - `deleteTranscriptionFromList()` was always calling `displayValidationResults()`
   - This function expects DOM elements from the old validation screen
   - When on segment review screen, those elements don't exist → null reference error

   **The Fix**:
   - Check `currentScreen` variable to determine which screen is active
   - If on `segmentReview`: call `loadAndDisplaySegments()` to refresh segments
   - If on validation screen: call `displayValidationResults()` as before
   - Matches pattern already used in `saveTranscription()` function

   **Code Change** (lines 957-991 in app.js):
   ```javascript
   // BEFORE (always used validation screen refresh):
   // Update validation results
   const video = validationResult.valid_videos.find(v => v.filename === filename);
   if (video) {
       video.has_transcription = false;
       video.transcription_type = null;
   }
   // Refresh display
   displayValidationResults();

   // AFTER (check current screen):
   // Refresh the current screen - check which screen we're on
   if (currentScreen === 'segmentReview') {
       // Reload segments to show updated transcription
       await loadAndDisplaySegments();
   } else if (validationResult) {
       // Update validation results if we're on validation screen
       const video = validationResult.valid_videos.find(v => v.filename === filename);
       if (video) {
           video.has_transcription = false;
           video.transcription_type = null;
       }
       displayValidationResults();
   }
   ```

**Delete Transcription Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/static/app.js` - Update `deleteTranscriptionFromList()` function around line 957
  - Add screen check before refreshing display
  - Call `loadAndDisplaySegments()` for segment review screen
  - Call `displayValidationResults()` for validation screen
  - Critical: Without this fix, delete button fails with null reference error on segment review screen

9. **Segment Transcription Persistence Fix** (Added Jan 29, 2026): Implemented Steps 0.6 and 1.5 to make manual segment transcriptions persist across pipeline runs
   - **Problem**: Manual segment transcriptions were saved to `.transcriptions/` but never used by pipeline
   - **Root Cause**: Pipeline had no logic to copy transcriptions before ASR or save them after
   - **Impact**: Whisper re-transcribed all segments every run, ignoring manual work and wasting hours

   **The Solution**:
   Added two missing steps documented in CLAUDE.md but never implemented:

   **Step 0.6: Copy Existing Transcriptions (Before ASR)**
   - **Location**: Lines 489-515 in EC2 version
   - **Runs**: Before Step 3 (ASR/Whisper)
   - **What it does**:
     1. Scans `~/vsp_input/.transcriptions/` for existing `.wrd` files
     2. Identifies segment transcriptions (regex: `_[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$`)
     3. Copies them to `$SEGMENT_WRD_TMP` (ASR working directory)
     4. Whisper skips segments with existing `.wrd` files (built-in logic in `asr_to_words_notime.py`)

   **Step 1.5: Save New Transcriptions (After ASR)**
   - **Location**: Lines 531-606 in EC2 version
   - **Runs**: After Step 3 (ASR completes)
   - **What it does**:
     1. Scans `$SEGMENT_WRD_TMP` for new Whisper outputs
     2. Checks `metadata.json` to identify manual vs auto transcriptions
     3. Copies new auto-transcriptions to `.transcriptions/` (preserves manual)
     4. Updates `metadata.json` to mark them as "auto" type

   **Pipeline Flow (Updated)**:
   ```
   Before:
   [3] ASR → Whisper transcribes ALL segments ❌

   After:
   [0.6] Copy existing transcriptions → ASR working dir
   [3] ASR → Whisper SKIPS segments with existing .wrd ✅
   [1.5] Save new auto-transcriptions → .transcriptions/
   ```

   **Benefits**:
   - ✅ Manual transcriptions persist across pipeline runs
   - ✅ Whisper runs only once per video (90%+ time savings)
   - ✅ Manual transcriptions never overwritten by auto
   - ✅ Transcriptions survive resets, archives, re-runs

   **Example Workflow**:
   ```
   First Run: Whisper transcribes 6 segments → saves as [AUTO] (5 min)
   User: Manually edits segment 0 → becomes [MANUAL]
   Second Run: Whisper skips all 6 segments (0 seconds!) ✅
   ```

**Segment Transcription Persistence Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Add Steps 0.6 and 1.5
  - **Step 0.6** (insert before Step 3 ASR, after `mkdir -p "$SEGMENT_WRD_TMP"`):
    ```bash
    echo ">>> [0.6] Checking for existing manual transcriptions"
    TRANSCRIPTIONS_DIR="$HOME/vsp_input/.transcriptions"

    if [ -d "$TRANSCRIPTIONS_DIR" ]; then
      copied_count=0
      for wrd_file in "$TRANSCRIPTIONS_DIR"/*.wrd; do
        if [ -f "$wrd_file" ]; then
          filename=$(basename "$wrd_file")
          # Check if segment transcription (has frame numbers)
          if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
            cp "$wrd_file" "$SEGMENT_WRD_TMP/"
            copied_count=$((copied_count + 1))
          fi
        fi
      done
      echo ">>> [0.6] Copied $copied_count existing transcription(s)"
    fi
    ```

  - **Step 1.5** (insert after Step 3 ASR, after `deactivate`):
    ```bash
    echo ">>> [1.5] Saving new auto-transcriptions to .transcriptions/"
    mkdir -p "$TRANSCRIPTIONS_DIR"
    METADATA_FILE="$TRANSCRIPTIONS_DIR/metadata.json"

    for wrd_file in "$SEGMENT_WRD_TMP"/*.wrd; do
      if [ -f "$wrd_file" ]; then
        filename=$(basename "$wrd_file")
        if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
          # Check if manual transcription exists (don't overwrite)
          is_manual=$(python3 -c "import json; ..." 2>/dev/null)
          if [ "$is_manual" != "yes" ]; then
            cp "$wrd_file" "$TRANSCRIPTIONS_DIR/"
            # Update metadata as 'auto' type
          fi
        fi
      fi
    done
    ```

  - See `/tmp/transcription_persistence_fix.md` for complete code
  - **Critical**: Without this fix, manual segment transcriptions are ignored and Whisper re-transcribes everything every run

10. **POST_ROOT Undefined Variable Bugfix** (Added Jan 29, 2026): Fixed pipeline exit error caused by undefined variable
   - **Problem**: Pipeline completed successfully but exited with code 1 and showed "Error" in UI
   - **Root Cause**: Line 394 (EC2) / Line 429 (container) referenced undefined `POST_ROOT` variable in final summary
   - **Impact**: Despite successful processing, pipeline appeared to fail with "Processing failed at stage: Generate Outputs"

   **The Fix**:
   - Added `POST_ROOT="$ARCHIVE_ROOT/client_outputs"` before final summary echo statements
   - Location: After Step 8 client outputs complete, before pipeline completion message

   **Code Change** (both EC2 and container versions):
   ```bash
   # BEFORE (line 394/429 - undefined variable):
   deactivate

   echo
   echo ">>> Pipeline complete!"
   echo "    - Outputs: $POST_ROOT"  # ❌ POST_ROOT never defined

   # AFTER (added line after deactivate):
   deactivate

   # Set POST_ROOT for final summary
   POST_ROOT="$ARCHIVE_ROOT/client_outputs"

   echo
   echo ">>> Pipeline complete!"
   echo "    - Outputs: $POST_ROOT"  # ✅ Now properly defined
   ```

**POST_ROOT Bugfix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Define POST_ROOT before final summary (after line ~422, before line ~425)
  - Add: `POST_ROOT="$ARCHIVE_ROOT/client_outputs"`
  - Location: After `deactivate` line following client outputs step
  - Critical: Without this fix, pipeline exits with code 1 even when successful, showing error in UI

11. **Decode Output Duplication Bugfix** (Added Jan 29, 2026): Fixed duplicate INST/REF/HYP logging in decode step
   - **Problem**: Each segment's decode output appeared twice in logs, making logs verbose and confusing
   - **Root Cause**: Python logger propagation - child logger messages propagated to root logger, causing duplicate output
   - **Impact**: Decode logs showed each segment twice, doubling log size and making it hard to read

   **The Issue**:
   - Line 47: Root logger configured with `logging.basicConfig()`
   - Line 100-105: Another `basicConfig()` call for formatting
   - Line 106: Child logger `"hybrid.speech_recognize"` created
   - Line 219: `logger.info()` logs INST/REF/HYP
   - **Problem**: Child logger inherits from root, messages propagate to both → duplicate output!

   **The Fix**:
   - Set `logger.propagate = False` to prevent messages reaching root logger
   - Add explicit handlers to child logger for both file and stdout output
   - Messages now appear exactly once with proper formatting

   **Code Change** (lines ~106-108):
   ```python
   # BEFORE:
   logger = logging.getLogger("hybrid.speech_recognize")
   if output_file is not sys.stdout:  # also print to stdout
       logger.addHandler(logging.StreamHandler(sys.stdout))

   # AFTER:
   logger = logging.getLogger("hybrid.speech_recognize")
   logger.propagate = False  # Prevent duplicate logging to root logger
   logger.setLevel(logging.INFO)

   # Add file/stdout handler
   file_handler = logging.StreamHandler(output_file)
   file_handler.setFormatter(logging.Formatter(
       "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
       datefmt="%Y-%m-%d %H:%M:%S"
   ))
   logger.addHandler(file_handler)

   # If outputting to file, also print to stdout
   if output_file is not sys.stdout:
       stdout_handler = logging.StreamHandler(sys.stdout)
       stdout_handler.setFormatter(logging.Formatter(
           "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
           datefmt="%Y-%m-%d %H:%M:%S"
       ))
       logger.addHandler(stdout_handler)
   ```

**Decode Duplication Bugfix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/VSP-LLM/src/vsp_llm_decode.py` - Fix logger propagation (lines ~106-123)
  - Add: `logger.propagate = False`
  - Add explicit file and stdout handlers with formatters
  - Critical: Without this fix, decode logs show each segment twice

12. **Segment Transcription Save Location Bugfix** (Added Jan 29, 2026): Fixed segment transcriptions saving to wrong location
   - **Problem**: Manual transcriptions created in segment review screen were not being used by pipeline
   - **Root Cause**: Segment transcriptions saved to `flat_text_seg12s/` as `.txt` files, but pipeline looks in `.transcriptions/` for `.wrd` files
   - **Impact**: Users manually transcribed segments, but Whisper re-transcribed them anyway, wasting hours of work

   **The Issue**:
   - `/api/save-segment-transcription` endpoint saved to: `~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/{segment_id}.txt`
   - Pipeline Steps 0.6 and 1.5 looked in: `~/vsp_input/.transcriptions/{segment_id}.wrd`
   - **Result**: Transcriptions never found, Whisper ran on all segments every time!

   **The Fix**:
   - Modified `handle_save_segment_transcription()` to use `TranscriptionManager`
   - Segment transcriptions now save to `.transcriptions/` as `.wrd` files (unified location)
   - Pipeline Steps 0.6 and 1.5 now find and reuse segment transcriptions
   - Whisper skips all manually transcribed segments

   **Code Change** (lines ~796-814 in server.py):
   ```python
   # BEFORE:
   # Save transcription
   text_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_text_seg{SEGMENT_DURATION}s"
   text_dir.mkdir(parents=True, exist_ok=True)
   text_file = text_dir / f"{segment_id}.txt"

   try:
       words = transcription.split()
       with open(text_file, 'w') as f:
           for word in words:
               f.write(word + '\n')
       # ... send success ...

   # AFTER:
   # Save transcription to unified .transcriptions directory as .wrd file
   from .services.transcription_manager import TranscriptionManager

   try:
       transcription_mgr = TranscriptionManager()
       filename = f"{segment_id}.mp4"

       # Save as manual transcription
       transcription_mgr.save_transcription(filename, transcription, transcription_type='manual')

       words = transcription.split()
       # ... send success ...
   ```

   **Benefits**:
   - ✅ All transcriptions in one unified location (`.transcriptions/`)
   - ✅ All transcriptions in same format (`.wrd` files)
   - ✅ Segment transcriptions persist across pipeline runs
   - ✅ Whisper skips manually transcribed segments (huge time savings!)
   - ✅ Consistent behavior between validation screen and segment review screen

**Segment Transcription Location Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Update `handle_save_segment_transcription()` method (lines ~796-814)
  - Replace direct file save with `TranscriptionManager.save_transcription()` call
  - Save to `.transcriptions/` directory as `.wrd` files
  - Mark as 'manual' type
  - Critical: Without this fix, segment transcriptions are ignored by pipeline and Whisper re-transcribes everything

13. **Disable Validation Screen Transcription Buttons** (Added Jan 29, 2026): Removed transcription functionality from validation screen
   - **Rationale**: Transcribing full videos on validation screen doesn't help when videos get segmented during preprocessing
   - **Impact**: Simplifies workflow - users only transcribe final segments after preprocessing completes
   - **User Request**: "if it possible to do it from the validation screen i wish to disable it"

   **What Changed**:
   - Removed "Add Transcription" / "Edit Transcription" buttons from validation screen video list
   - Removed "Delete" transcription buttons
   - Removed event listeners for removed buttons
   - Transcription functionality now ONLY available in segment review screen (after preprocessing)

   **Workflow After Change**:
   1. **Validation Screen**: Add videos, adjust settings, click "Start Processing" (NO transcription buttons)
   2. **Processing**: Pipeline segments videos and runs Whisper ASR
   3. **Segment Review Screen**: Review segments, add/edit transcriptions for individual segments
   4. **Benefits**:
      - ✅ Clearer workflow - transcribe final output, not intermediate videos
      - ✅ Avoids confusion about full-video vs segment transcriptions
      - ✅ Transcriptions match actual pipeline segments

   **Code Changes** (lines ~571-608 in app.js):
   ```javascript
   // BEFORE: Validation screen had transcription buttons
   <div class="video-actions">
       <button class="btn-transcription" ...>
           ${v.has_transcription ? 'Edit' : 'Add'} Transcription
       </button>
       ${v.has_transcription ? `<button class="btn-delete-transcription"...>Delete</button>` : ''}
       <button class="btn-remove" ...>Remove</button>
   </div>

   // Event listeners for transcription buttons
   document.querySelectorAll('.btn-transcription').forEach(btn => { ... });
   document.querySelectorAll('.btn-delete-transcription').forEach(btn => { ... });

   // AFTER: Validation screen has only Remove button
   <div class="video-actions">
       <button class="btn-remove" ...>Remove</button>
   </div>

   // No transcription button event listeners
   ```

**Validation Screen Transcription Removal Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/static/app.js` - Remove transcription buttons from `displayValidationResults()` function
  - Lines ~571-584: Remove transcription button HTML (keep only Remove button)
  - Lines ~596-608: Remove transcription button event listeners
  - Result: Validation screen shows only video list with Remove buttons

14. **Log Output Stdout Contamination Bug** (Added Jan 29, 2026): Fixed `log_info` contaminating function return values
   - **Problem**: Client outputs (reports and burned videos) not generated, `POST_ROOT` and `ARCHIVE_ROOT` variables contained log messages
   - **Root Cause**: `log_info()` function in `lib/common.sh` echoed to stdout instead of stderr
   - **Impact**: When functions like `archive_previous_run()` used `log_info` and returned values via `echo`, command substitution captured BOTH log messages and return value

   **Why This Broke Everything**:
   ```bash
   # In archive_previous_run():
   log_info "Run ID: 20260129_162742"        # Goes to stdout ❌
   log_info "Archiving previous outputs..."   # Goes to stdout ❌
   echo "${archive_root}"                      # Also goes to stdout

   # In pipeline:
   ARCHIVE_ROOT=$(archive_previous_run ...)   # Captures ALL stdout!
   # Result: ARCHIVE_ROOT = "[16:27:42] INFO: Run ID: ...\n[16:27:42] INFO: Archiving...\n/path/to/archive"

   # Then later:
   POST_ROOT="$ARCHIVE_ROOT/client_outputs"
   # Result: POST_ROOT = "[16:27:42] INFO: ...\n.../client_outputs"

   # Finally:
   python make_report.py --out_dir "$POST_ROOT"
   # Python tries to create directory with newlines and timestamps in the name! ❌
   ```

   **Symptoms**:
   - Reports and burned videos not created
   - Log output showing "Wrote: [16:27:42] INFO: Run ID: ..." (contaminated paths)
   - `ls ARCHIVE_ROOT/client_outputs` returned "No such file or directory"
   - Pipeline appeared to succeed but no outputs generated

   **The Fix**:
   - Changed `log_info()` to redirect to stderr like `log_error()` and `log_warn()` already do
   - This prevents log messages from contaminating function return values captured via `$()`

   **Code Change** (lib/common.sh line ~10):
   ```bash
   # BEFORE:
   log_info() {
       echo "[$(date +'%H:%M:%S')] INFO: $*"     # ❌ Goes to stdout
   }

   # AFTER:
   log_info() {
       echo "[$(date +'%H:%M:%S')] INFO: $*" >&2  # ✅ Goes to stderr
   }
   ```

   **Why This Works**:
   - Stderr (`>&2`) is for diagnostic/logging output
   - Stdout is for data/return values
   - Command substitution `$(...)` only captures stdout, not stderr
   - Now `ARCHIVE_ROOT=$(archive_previous_run ...)` gets clean path without log contamination

   **Best Practice**:
   - All logging functions should output to stderr
   - Only data meant to be captured should go to stdout
   - Functions that "return" values via `echo` must ensure no other stdout output occurs

**Log Stdout Contamination Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/lib/common.sh` - Update `log_info()` function (line ~10)
  - Change: `echo "[$(date +'%H:%M:%S')] INFO: $*"` → `echo "[$(date +'%H:%M:%S')] INFO: $*" >&2`
  - Critical: Without this fix, all bash functions using `log_info` and returning values via `echo` will have contaminated return values, breaking client outputs, archive paths, and any derived variables
  - Transcription functionality available ONLY in segment review screen

15. **Non-Segmented Video Naming and Metadata Fix** (Added Jan 29, 2026): Fixed two issues with non-segmented (whole) videos
   - **Problem 1**: Manual transcriptions not being used by pipeline
   - **Problem 2**: Burned videos showing mouth-cropped videos instead of full-frame originals
   - **Root Cause**: Artificial segment-like naming (`_00_000000_999999` suffix) added to non-segmented videos
   - **Impact**: Confusing naming, transcription matching failures, and inability to extract from original videos

   **The Core Issue**:
   Videos too short for segmentation (<24s) were artificially renamed with segment-like suffixes:
   - Input: `00008.mp4`
   - Copied as: `00008_00_000000_999999.mp4`
   - Transcription: `00008_00_000000_999999.wrd` (from UI)
   - BUT preprocessing outputs: `00008.mp4` (original name, no suffix!)
   - ASR looks for: `00008.wrd` (doesn't exist)
   - Result: Manual transcription ignored, Whisper runs unnecessarily

   **Why Burned Videos Used Mouth Crops**:
   - `make_burn.py` tries 3 strategies to get video source
   - Strategy 1 (preferred): Extract segment from original full-frame video using `segment_metadata.json` timing
   - Strategy 2 (fallback): Use preprocessed mouth-cropped segment video
   - Strategy 3 (last resort): Use full original video

   **metadata.json was broken**:
   ```json
   // BEFORE (empty structure, no timing info):
   {"segments": [], "total_videos": 1, "segmentation_enabled": false}

   // Strategy 1 check fails because video ID not in metadata
   // Falls back to Strategy 2 → mouth crops used
   ```

   **The Fixes**:

   **Fix 1: Remove Artificial Segment Naming** (run_flat_english_pipeline.sh line ~130-139)
   ```bash
   # BEFORE (added confusing suffix):
   video_id="${video_name%.*}"
   video_ext="${video_name##*.}"
   output_name="${video_id}_00_000000_999999.${video_ext}"  # ❌ Artificial suffix
   cp "$video_file" "${FAST_SEG_DIR}/${output_name}"

   # AFTER (keep original name):
   output_name="${video_name}"  # ✅ Simple and correct
   cp "$video_file" "${FAST_SEG_DIR}/${output_name}"
   ```

   **Fix 2: Proper segment_metadata.json Structure** (run_flat_english_pipeline.sh line ~147-195)
   ```json
   // AFTER (proper structure with timing):
   {
     "00008": {
       "original_duration": 3.584,
       "segment_duration": 3.584,
       "overlap_duration": 0,
       "num_segments": 1,
       "segments": [
         {
           "index": 0,
           "start_frame": 0,
           "end_frame": 89,
           "start_sec": 0.0,
           "end_sec": 3.584,
           "duration": 3.584
         }
       ]
     }
   }
   ```

   **Benefits**:
   - ✅ Naming is conceptually correct: segmented videos have segment IDs, whole videos don't
   - ✅ Transcription matching is simple: `video_name.wrd` matches `video_name.mp4`
   - ✅ Burned videos use full-frame originals (Strategy 1 works with proper metadata)
   - ✅ No special-case logic needed - everything works consistently

   **Code Changes**:
   1. **Naming fix** (lines ~130-139):
      - Removed: `video_id="${video_name%.*}"`, `video_ext="${video_name##*.}"`, `output_name="${video_id}_00_000000_999999.${video_ext}"`
      - Added: `output_name="${video_name}"`

   2. **Metadata fix - SEGMENT_ONLY mode** (lines ~147-195):
      - Removed: Single-line JSON with empty segments array
      - Added: 49-line loop that creates proper metadata in FAST_SEG_DIR (for UI preview)

   3. **Metadata fix - Full pipeline** (NEW Step 2.5, lines ~318-375):
      - **Critical Fix**: Added second metadata creation after preprocessing completes
      - **Why needed**: make_burn.py looks for metadata at `${PREP_ROOT}/segment_metadata.json`, not in fast_segments/
      - Location: After Step 2 (preprocessing), before Step 3 (ASR)
      - Creates metadata at correct location for make_burn.py
      - Uses FLAT_VID_DIR videos as source (after normalization/preprocessing)
      - Enables Strategy 1 (extract from original full-frame video) in make_burn.py

   **Testing**:
   - Non-segmented videos now keep original names throughout pipeline
   - Manual transcriptions work (simple name matching)
   - Burned videos use full-frame originals (Strategy 1 succeeds with proper metadata at correct location)

**Non-Segmented Video Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Three fixes:
  1. **Line ~130-139**: Remove segment suffix from output_name
     - Change: `output_name="${video_id}_00_000000_999999.${video_ext}"` → `output_name="${video_name}"`
  2. **Line ~147-195**: Replace empty metadata JSON with proper structure (SEGMENT_ONLY mode)
     - Replace single-line `echo "{\"segments\": [], ...}"` with 49-line loop
     - Creates metadata in fast_segments/ for UI preview
  3. **Line ~318-375** (NEW Step 2.5): Create metadata at PREP_ROOT for make_burn.py
     - Add after Step 2 (preprocessing), before Step 3 (ASR)
     - Only runs when SEGMENTATION_ENABLED=0
     - Creates metadata at `${PREP_ROOT}/segment_metadata.json` (correct location!)
- `/workspace/lib/asr.sh` - No changes needed (already has simple direct matching)

16. **Non-Segmented Video Burned Output Fix** (Added Jan 29, 2026): Fixed burned videos showing mouth crops for non-segmented videos
   - **Problem**: When segmentation disabled (videos <24s), burned videos showed 96x96 mouth crops instead of full-frame originals
   - **Root Cause**: `make_burn.py` couldn't match non-segmented video IDs to metadata segments
   - **Impact**: Even with proper metadata created in Step 2.5, Strategy 1 extraction failed and fell back to mouth crops

   **Why It Failed**:
   - Non-segmented video IDs don't have frame numbers: `"00008"` (not `"00008_00_000000_000300"`)
   - `parse_segment_id("00008")` returns `seg_idx = -1` (can't parse frame numbers)
   - Segment lookup searched for `index == -1` but metadata has `index == 0`
   - No match found → fell back to Strategy 2 (preprocessed mouth crops)

   **The Fix** (make_burn.py lines ~329-343):
   ```python
   # BEFORE:
   segment_info = None
   for seg in segments:
       if seg.get("index") == seg_idx:  # Fails when seg_idx == -1
           segment_info = seg
           break

   # AFTER:
   segment_info = None
   if seg_idx == -1:
       # Non-segmented video - use first (and only) segment
       if segments:
           segment_info = segments[0]
           print(f"[INFO] {uid}: Using whole video (non-segmented)")
   else:
       # Segmented video - find by index
       for seg in segments:
           if seg.get("index") == seg_idx:
               segment_info = seg
               break
   ```

   **Results**:
   - Non-segmented videos: Strategy 1 succeeds, extracts from original (224x224 full-frame)
   - Segmented videos: Unchanged behavior, still use Strategy 1 with index matching

**Non-Segmented Burned Output Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/VSP-LLM/scripts/make_burn.py` - Update segment matching logic (lines ~329-343)
  - Add special case for `seg_idx == -1` to use first segment
  - Enables Strategy 1 extraction for non-segmented videos
  - Critical: Without this fix, burned videos show mouth crops even with proper metadata

