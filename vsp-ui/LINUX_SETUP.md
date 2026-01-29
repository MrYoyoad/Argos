# VSP UI Setup for Linux Standalone Container

This document explains how to configure the UI for your standalone Linux container.

## Key Differences Between EC2 and Container

| Aspect | EC2 (this server) | Linux Container |
|--------|-------------------|-----------------|
| Root path | `$HOME` (`/home/ubuntu`) | `/workspace` or `/host/galaxy_export` |
| Pipeline script | `~/run_flat_english_pipeline.sh` | `/host/galaxy_export/run_flat_english_pipeline.sh` |
| Input folder | `~/vsp_input/` | `/host/galaxy_export/ui/input_videos/` |
| Archive folder | `~/flat_runs_archive/` | `/workspace/flat_runs_archive/` |
| Output exports | Same as archive | `/host/galaxy_export/outputs_flat_*/` |

## Configuration Changes Needed

### 1. Update `vsp-ui/app/config.py`

Replace the paths section with:

```python
# Paths - detect if running in container
import os
from pathlib import Path

# Detect environment
if Path("/workspace/auto_avsr").exists():
    # Running in Docker container
    EXPORT_ROOT = Path("/workspace")
    INPUT_DIR = Path("/host/galaxy_export/ui/input_videos")
    PIPELINE_SCRIPT = Path("/host/galaxy_export/run_flat_english_pipeline.sh")
    ARCHIVE_DIR = EXPORT_ROOT / "flat_runs_archive"
elif Path("/home/ubuntu/auto_avsr").exists():
    # Running on EC2/bare metal
    EXPORT_ROOT = Path(os.environ.get("HOME", "/home/ubuntu"))
    INPUT_DIR = EXPORT_ROOT / "vsp_input"
    PIPELINE_SCRIPT = EXPORT_ROOT / "run_flat_english_pipeline.sh"
    ARCHIVE_DIR = EXPORT_ROOT / "flat_runs_archive"
else:
    # Fallback to HOME
    EXPORT_ROOT = Path(os.environ.get("HOME"))
    INPUT_DIR = EXPORT_ROOT / "vsp_input"
    PIPELINE_SCRIPT = EXPORT_ROOT / "run_flat_english_pipeline.sh"
    ARCHIVE_DIR = EXPORT_ROOT / "flat_runs_archive"

HOME_DIR = EXPORT_ROOT
AUTO_AVSR_DIR = EXPORT_ROOT / "auto_avsr"
```

### 2. Update Stage Markers

Your Linux pipeline has an additional step (0.5 - normalization). Update `STAGE_MARKERS`:

```python
STAGE_MARKERS = {
    "init": r">>> \[INIT\]",
    "normalize": r">>> \[0\.5\]",  # NEW: Video normalization step
    "asr": r">>> \[1\]",
    "preprocess_ready": r">>> \[2\]",
    "preprocess": r">>> \[3\]",
    "lrs3_prep": r">>> \[4\]",
    "manifests": r">>> \[5\]",
    "kmeans": r">>> \[6\]",
    "fairseq": r">>> \[7\]",  # NEW: Fairseq check step
    "decode": r">>> \[8\]",
    "client_outputs": r">>> \[9\]",
}
```

### 3. Update Pipeline Stages

Add the normalize stage:

```python
PIPELINE_STAGES = [
    Stage("init", "Initialize", "Archiving previous run", 60, 1),
    Stage("normalize", "Normalize Videos", "Normalizing resolution and framerate", 1800, 10),  # NEW
    Stage("asr", "ASR Transcription", "Running Whisper speech recognition", 1800, 10),  # Reduced from 15
    Stage("preprocess_ready", "Prepare Directories", "Setting up preprocessing directories", 60, 1),
    Stage("preprocess", "Mouth Cropping", "Detecting faces and cropping mouth regions", 3600, 25),  # Reduced from 30
    Stage("lrs3_prep", "Format Conversion", "Converting to LRS3 format", 300, 3),
    Stage("manifests", "Generate Manifests", "Building TSV and manifest files", 300, 5),
    Stage("kmeans", "K-means Clustering", "Extracting features and training clusters", 3600, 20),
    Stage("fairseq", "Fairseq Check", "Verifying Fairseq extensions", 300, 1),  # NEW
    Stage("decode", "LLM Decoding", "Running VSP-LLM inference", 7200, 19),  # Reduced from 20
    Stage("client_outputs", "Generate Outputs", "Creating reports and burned videos", 600, 5),
]
```

### 4. Environment Variables for Pipeline

The Linux pipeline expects these environment variables. Update `pipeline_runner.py`:

```python
def _get_env(self) -> dict:
    """Get environment variables for pipeline execution."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Container-specific environment
    if Path("/workspace").exists():
        env["EXPORT_ROOT"] = "/workspace"
        env["EXPORT_OUT"] = "/host/galaxy_export"

    # Default settings for UI usage
    env["QUIET"] = "0"  # Show logs
    env["TRAIN_KMEANS"] = "1"  # Always train k-means
    env["NORM_VERBOSE"] = "0"  # Don't show verbose ffmpeg logs
    env["USE_GPU_NORM"] = "1"  # Use GPU for normalization
    env["MAX_DIM"] = "720"  # Max resolution
    env["FPS_OUT"] = "25"  # Output FPS

    return env
```

### 5. Desktop Launcher Update

Update `launcher.sh` to detect the environment:

```bash
# Auto-detect environment
if [ -d "/workspace/auto_avsr" ]; then
    export EXPORT_ROOT="/workspace"
fi
```

## File Placement on Linux Container

1. Copy entire `vsp-ui/` folder to: `/host/galaxy_export/vsp-ui/`
2. Update pipeline script location to: `/host/galaxy_export/run_flat_english_pipeline.sh`
3. Create input directory: `/host/galaxy_export/ui/input_videos/`
4. Desktop shortcut should point to: `/host/galaxy_export/vsp-ui/launcher.sh`

## Testing

1. **Test server start:**
   ```bash
   cd /host/galaxy_export/vsp-ui
   python3 -m app.server
   ```

2. **Test with sample videos:**
   - Copy 2-3 test videos to `/host/galaxy_export/ui/input_videos/`
   - Open browser to `http://localhost:8765`
   - Click "Scan Videos"
   - Verify validation works
   - (Optional) Start processing to test full pipeline

## Output Location

After processing completes, outputs will be in:
- Archive: `/workspace/flat_runs_archive/[timestamp]/client_outputs/`
- Export: `/host/galaxy_export/outputs_flat_[timestamp]/client_outputs/`

The UI will display the export path for easy access.
