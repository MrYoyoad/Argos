# VSP Pipeline Usage Guide (Linux Container Version)

## Overview

The pipeline script `run_flat_english_pipeline.sh` now supports both standard and overlapping segmentation modes with full Docker container integration.

## Basic Usage

```bash
./run_flat_english_pipeline.sh /path/to/raw_videos_dir
```

## Configuration Variables

All variables are optional and use sensible defaults:

### Pipeline Mode
```bash
OVERLAP_ENABLED=0  # Default: Standard mode (ASR before preprocessing)
OVERLAP_ENABLED=1  # Overlapping mode (ASR after segmentation, 1s overlap)
```

### Logging Controls
```bash
QUIET=0              # Default: Show all output
QUIET=1              # Suppress most output (useful for automation)

NORM_VERBOSE=1       # Default: Show video normalization details
NORM_VERBOSE=0       # Hide normalization details
```

### Cleanup Behavior
```bash
CLEAN_ON_START=1     # Default: Archive previous runs before starting
CLEAN_ON_START=0     # Keep previous runs (not recommended)

CLEAN_ON_FAIL=0      # Default: Keep partial outputs on failure (for debugging)
CLEAN_ON_FAIL=1      # Remove partial outputs on failure (for production)
```

### K-means Training
```bash
TRAIN_KMEANS=1       # Default: Train new k-means model
TRAIN_KMEANS=0       # Use existing k-means model (much faster)
```

### Docker Export
```bash
EXPORT_ROOT=/host/galaxy_export  # Export results to host filesystem
# Default: $HOME (no export)
```

### Whisper Model
```bash
WHISPER_MODEL_PATH=/host/galaxy_export/whisper/medium.pt  # Default: Use offline model
# Falls back to downloading 'medium' if file not found
```

### Video Normalization
```bash
SKIP_NORM=0          # Default: Normalize videos (recommended)
SKIP_NORM=1          # Skip normalization (faster, use if videos already normalized)

USE_GPU_NORM=1       # Default: Use GPU for video encoding (much faster)
USE_GPU_NORM=0       # Use CPU encoding

MAX_DIM=0            # Default: Keep original resolution
MAX_DIM=720          # Resize to max 720p (width or height)
MAX_DIM=1080         # Resize to max 1080p

FPS_OUT=25           # Default: Output 25fps (required for lip-reading)

NORM_TIMEOUT_SEC=600 # Default: 10-minute timeout per video
```

## Usage Examples

### Standard Mode (Default)
```bash
# Basic run with all defaults
./run_flat_english_pipeline.sh /path/to/videos

# Skip k-means training (use existing model)
TRAIN_KMEANS=0 ./run_flat_english_pipeline.sh /path/to/videos

# Quiet mode for automation
QUIET=1 ./run_flat_english_pipeline.sh /path/to/videos
```

### Overlapping Mode
```bash
# Enable overlapping segmentation (1s overlap, 8s min split)
OVERLAP_ENABLED=1 ./run_flat_english_pipeline.sh /path/to/videos

# Overlapping + skip k-means (fastest for subsequent runs)
OVERLAP_ENABLED=1 TRAIN_KMEANS=0 ./run_flat_english_pipeline.sh /path/to/videos

# Overlapping + quiet + export to host
OVERLAP_ENABLED=1 QUIET=1 EXPORT_ROOT=/host/galaxy_export \
  ./run_flat_english_pipeline.sh /path/to/videos
```

### Docker Container Usage
```bash
# Full production run in container
docker run -v /host/data:/data \
  -v /host/galaxy_export:/host/galaxy_export \
  -e OVERLAP_ENABLED=1 \
  -e EXPORT_ROOT=/host/galaxy_export \
  -e WHISPER_MODEL_PATH=/host/galaxy_export/whisper/medium.pt \
  -e QUIET=1 \
  vsp-container \
  /workspace/run_flat_english_pipeline.sh /data/raw_videos
```

## Pipeline Steps Comparison

### Standard Mode (OVERLAP_ENABLED=0)
1. Video normalization
2. **ASR on full videos** (Whisper)
3. make_preprocess_ready.sh
4. Standard preprocessing (4s segments, no overlap)
5. flat_to_lrs3_preperation.sh
6. Manifests + splits + train.tsv
7. K-means + cluster counts
8. fairseq Cython extensions check
9. VSP-LLM decode
10. Client outputs (reports + burned videos)
11. Export to host (if EXPORT_ROOT set)

### Overlapping Mode (OVERLAP_ENABLED=1)
1. Video normalization
2. Copy videos (no ASR yet)
3. **Overlapping preprocessing** (4s segments, 1s overlap)
4. **ASR on segmented videos** (Whisper on each segment)
5. flat_to_lrs3_preperation.sh
6. Manifests + splits + train.tsv
7. **Generate segment timing metadata**
8. K-means + cluster counts
9. fairseq Cython extensions check
10. VSP-LLM decode
11. **Merge overlapping predictions**
12. Client outputs (using wrapper scripts)
13. Export to host (if EXPORT_ROOT set)

## Output Locations

### Within Container
- **Mouth crops**: `~/auto_avsr/preprocessed_flat_seg4/`
- **Manifests**: `~/auto_avsr/preprocessed_flat_seg4/433h_data/`
- **Cluster labels**: `~/VSP-LLM/flat_labels/`
- **Client outputs**: `~/flat_runs_archive/[TIMESTAMP]/client_outputs/`
  - Reports: `client_outputs/report/`
  - Burned videos: `client_outputs/burned_videos/`

### On Host (if EXPORT_ROOT set)
- **All outputs**: `${EXPORT_ROOT}/flat_runs_archive/[TIMESTAMP]/`

## Error Handling

- All errors logged to: `~/pipeline_logs/failures/fail_[TIMESTAMP].log`
- Each step has error detection with meaningful exit codes
- Set `CLEAN_ON_FAIL=1` to automatically clean up partial outputs on failure

## Performance Tips

1. **Subsequent runs**: Use `TRAIN_KMEANS=0` to skip k-means training
2. **GPU acceleration**: Ensure `USE_GPU_NORM=1` (default) for faster video encoding
3. **Quiet mode**: Use `QUIET=1` to reduce I/O overhead in automated pipelines
4. **Resolution limiting**: Set `MAX_DIM=720` to reduce processing time for high-res videos
5. **Whisper offline**: Pre-download model to `/host/galaxy_export/whisper/medium.pt`

## Troubleshooting

### "No videos available after normalize/copy"
- Check input directory contains .mp4 files
- Verify videos are readable and have valid streams
- Review normalization logs (set `NORM_VERBOSE=1`)

### "Segmented video directory not found"
- Preprocessing failed - check for face detection errors
- Review `~/auto_avsr/preprocessed_flat_seg4/` for partial outputs
- Ensure videos have visible faces

### K-means fails or takes too long
- Use `TRAIN_KMEANS=0` if k-means model already exists
- Reduce `PERCENT=1.0` in the script (default: use 100% of data)

### Decode fails with "No decode output found"
- Check VSP-LLM symlinks in `~/VSP-LLM/src/dataset/vsr/en/`
- Verify cluster_counts files exist in `~/VSP-LLM/flat_labels/`
- Review fairseq Cython extensions (Step 7)

## Version History

- **Jan 25, 2026**: Added overlapping segmentation support with conditional pipeline
- **Nov 22, 2025**: Initial Linux container version (standard mode only)
