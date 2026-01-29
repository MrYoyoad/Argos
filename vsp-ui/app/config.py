"""
Configuration for VSP Pipeline UI.
All paths, timeouts, and stage definitions.
"""
import os
from pathlib import Path
from typing import NamedTuple

# Paths
HOME_DIR = Path(os.environ.get("HOME", "/home/ubuntu"))
INPUT_DIR = HOME_DIR / "vsp_input"
PIPELINE_SCRIPT = HOME_DIR / "run_flat_english_pipeline.sh"
ARCHIVE_DIR = HOME_DIR / "flat_runs_archive"
AUTO_AVSR_DIR = HOME_DIR / "auto_avsr"

# Server settings
SERVER_HOST = "127.0.0.1"
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
