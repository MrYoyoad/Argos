"""
Configuration for VSP Pipeline UI.
All paths, timeouts, and stage definitions.
"""
import os
from pathlib import Path
from typing import NamedTuple


def _detect_environment():
    """
    Detect if running in container or EC2.

    Returns:
        Tuple of (base_dir, vsp_input_dir) based on environment
    """
    # Check for VSP_INPUT_DIR environment variable (highest priority)
    input_dir_env = os.environ.get("VSP_INPUT_DIR")

    # Check for Linux container environments
    if Path("/host/galaxy_export").exists():
        # Container with /host mount
        base_dir = Path("/host/galaxy_export")
        # Use env var if set, otherwise try common locations
        if input_dir_env:
            input_dir = Path(input_dir_env)
        elif Path("/host/galaxy_export/ui/input_videos").exists():
            input_dir = Path("/host/galaxy_export/ui/input_videos")
        else:
            input_dir = Path("/host/vsp_input")
        return base_dir, input_dir
    elif Path("/workspace/galaxy_export").exists():
        # Alternative container environment
        base_dir = Path("/workspace")
        input_dir = Path(input_dir_env) if input_dir_env else Path("/workspace/vsp_input")
        return base_dir, input_dir
    else:
        # EC2 environment
        home = Path(os.environ.get("HOME", "/home/ubuntu"))
        input_dir = Path(input_dir_env) if input_dir_env else home / "vsp_input"
        return home, input_dir


# Paths - auto-detect environment
BASE_DIR, INPUT_DIR = _detect_environment()
HOME_DIR = BASE_DIR  # For backward compatibility
PIPELINE_SCRIPT = BASE_DIR / "run_flat_english_pipeline.sh"
ARCHIVE_DIR = BASE_DIR / "flat_runs_archive"
AUTO_AVSR_DIR = BASE_DIR / "auto_avsr"

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8765
PID_FILE = HOME_DIR / ".vsp-ui.pid"
LOG_FILE = HOME_DIR / ".vsp-ui.log"

# Video validation
SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}
SEGMENT_DURATION = 12  # seconds per segment
MIN_SPLIT_DURATION = 12.0  # minimum duration to trigger overlapping segments
MIN_SEGMENTS_FOR_KMEANS = 200

# Pipeline stage definition
class Stage(NamedTuple):
    id: str
    name: str
    description: str
    timeout_seconds: int
    weight: int  # Percentage weight for progress calculation


PIPELINE_STAGES = [
    Stage("init", "Initialize", "Archiving previous pipeline outputs", 300, 1),
    Stage("normalize", "Normalize Videos", "Converting videos (HDR/10-bit to SDR, framerate normalization)", 900, 5),
    Stage("prepare_dirs", "Prepare Directories", "Setting up preprocessing directory structure", 60, 1),
    Stage("preprocess", "Mouth Cropping", "Detecting faces and cropping mouth regions (with/without overlap)", 3600, 25),
    Stage("asr", "ASR Transcription", "Running Whisper on segmented videos", 1800, 15),
    Stage("lrs3_prep", "Format Conversion", "Converting to LRS3 format", 300, 3),
    Stage("manifests", "Generate Manifests", "Building TSV and manifest files", 300, 5),
    Stage("kmeans", "K-means Clustering", "Extracting features and training clusters", 3600, 20),
    Stage("decode", "LLM Decoding", "Running VSP-LLM inference", 7200, 20),
    Stage("client_outputs", "Generate Outputs", "Creating reports and burned videos", 600, 5),
]

# Stage markers in pipeline output (regex patterns)
STAGE_MARKERS = {
    "init": r">>> \[INIT\]",
    "normalize": r">>> \[0\.5\]",
    "prepare_dirs": r">>> \[1\]",
    "preprocess": r">>> \[2\]",
    "asr": r">>> \[3\] Running ASR",
    "lrs3_prep": r">>> \[4\]",
    "manifests": r">>> \[5\] Building manifests",
    "kmeans": r">>> \[6\]",
    "decode": r">>> \[7\] Running VSP-LLM",
    "client_outputs": r">>> \[8\] Building client",
}

# Error patterns to detect failures
ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"^ERROR:",
    r"FAILED",
    r"Exception:",
    r"CUDA out of memory",
    r"No such file or directory",
    r"Permission denied",
]

# Completion marker (matches both normal and preprocessing-only completion)
COMPLETION_MARKER = r">>> Pipeline (preprocessing )?complete!"

# State machine states
class PipelineState:
    IDLE = "idle"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
