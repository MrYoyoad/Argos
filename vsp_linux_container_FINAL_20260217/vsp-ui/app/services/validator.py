"""
Video validation service using ffprobe.
Checks video format, duration, and estimates segments for k-means.
"""
import json
import subprocess
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..config import (
    INPUT_DIR,
    SUPPORTED_EXTENSIONS,
    SEGMENT_DURATION,
    MIN_SPLIT_DURATION,
    MIN_SEGMENTS_FOR_KMEANS,
)
from .transcription_manager import TranscriptionManager

# Initialize transcription manager
transcription_mgr = TranscriptionManager()


@dataclass
class VideoInfo:
    filename: str
    path: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_audio: bool
    estimated_segments: int
    valid: bool
    error: Optional[str] = None
    has_transcription: bool = False
    transcription_type: Optional[str] = None  # "auto" or "manual"
    created_at: Optional[str] = None  # ISO timestamp
    edited_at: Optional[str] = None  # ISO timestamp
    word_count: Optional[int] = None  # Number of words in transcription

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SegmentInfo:
    """Info about an existing preprocessed segment from previous run."""
    id: str
    filename: str
    duration: float
    has_transcription: bool
    transcription: str = ""
    transcription_type: Optional[str] = None  # "auto" or "manual"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    valid_videos: List[VideoInfo]
    invalid_videos: List[VideoInfo]
    warnings: List[str]
    total_segments: int
    kmeans_viable: bool
    total_duration_seconds: float
    segment_duration: int
    min_split_duration: float
    existing_segments: List[SegmentInfo] = None  # Segments from previous run

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "valid_videos": [v.to_dict() for v in self.valid_videos],
            "invalid_videos": [v.to_dict() for v in self.invalid_videos],
            "warnings": self.warnings,
            "total_segments": self.total_segments,
            "kmeans_viable": self.kmeans_viable,
            "total_duration_seconds": self.total_duration_seconds,
            "segment_duration": self.segment_duration,
            "min_split_duration": self.min_split_duration,
        }
        if self.existing_segments is not None:
            result["existing_segments"] = [s.to_dict() for s in self.existing_segments]
            result["existing_segments_count"] = len(self.existing_segments)
            result["existing_segments_transcribed"] = sum(1 for s in self.existing_segments if s.has_transcription)
        return result


def run_ffprobe(video_path: Path) -> Optional[Dict[str, Any]]:
    """Run ffprobe and return parsed JSON output."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def validate_video(video_path: Path) -> VideoInfo:
    """Validate a single video file using ffprobe."""
    filename = video_path.name
    path_str = str(video_path)

    # Check extension
    if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=0,
            width=0,
            height=0,
            fps=0,
            has_audio=False,
            estimated_segments=0,
            valid=False,
            error=f"Unsupported format: {video_path.suffix}",
        )

    # Run ffprobe
    probe_data = run_ffprobe(video_path)
    if probe_data is None:
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=0,
            width=0,
            height=0,
            fps=0,
            has_audio=False,
            estimated_segments=0,
            valid=False,
            error="Cannot read video file (corrupted or invalid)",
        )

    # Find video stream
    video_stream = None
    has_audio = False
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio":
            has_audio = True

    if video_stream is None:
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=0,
            width=0,
            height=0,
            fps=0,
            has_audio=has_audio,
            estimated_segments=0,
            valid=False,
            error="No video stream found",
        )

    # Extract metadata
    try:
        # Duration from format or stream
        duration = float(
            probe_data.get("format", {}).get("duration")
            or video_stream.get("duration")
            or 0
        )
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        # Parse FPS from avg_frame_rate (e.g., "25/1" or "30000/1001")
        fps_str = video_stream.get("avg_frame_rate", "0/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0
        else:
            fps = float(fps_str)

    except (ValueError, TypeError, ZeroDivisionError):
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=0,
            width=0,
            height=0,
            fps=0,
            has_audio=has_audio,
            estimated_segments=0,
            valid=False,
            error="Cannot parse video metadata",
        )

    # Check for valid duration
    if duration <= 0:
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=0,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
            estimated_segments=0,
            valid=False,
            error="Video has zero or invalid duration",
        )

    # Check for reasonable resolution (face detection needs at least some pixels)
    if width < 64 or height < 64:
        return VideoInfo(
            filename=filename,
            path=path_str,
            duration_seconds=duration,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
            estimated_segments=0,
            valid=False,
            error=f"Resolution too low: {width}x{height} (minimum 64x64)",
        )

    # Calculate estimated segments (4-second chunks)
    estimated_segments = max(1, math.ceil(duration / SEGMENT_DURATION))

    # Check for existing transcription
    transcription_info = transcription_mgr.get_transcription_info(filename)
    has_transcription = transcription_info is not None
    transcription_type = transcription_info.type if transcription_info else None
    created_at = transcription_info.created_at if transcription_info else None
    edited_at = transcription_info.edited_at if transcription_info else None
    word_count = transcription_info.word_count if transcription_info else None

    return VideoInfo(
        filename=filename,
        path=path_str,
        duration_seconds=duration,
        width=width,
        height=height,
        fps=fps,
        has_audio=has_audio,
        estimated_segments=estimated_segments,
        valid=True,
        error=None,
        has_transcription=has_transcription,
        transcription_type=transcription_type,
        created_at=created_at,
        edited_at=edited_at,
        word_count=word_count,
    )


def validate_input_folder() -> ValidationResult:
    """Validate all videos in the input folder."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    valid_videos: List[VideoInfo] = []
    invalid_videos: List[VideoInfo] = []
    warnings: List[str] = []

    # Find all video files (skip .excluded folder)
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        video_files.extend(INPUT_DIR.glob(f"*{ext}"))
        video_files.extend(INPUT_DIR.glob(f"*{ext.upper()}"))

    # Filter out files in .excluded folder
    video_files = [f for f in video_files if ".excluded" not in str(f)]

    # Remove duplicates (case-insensitive match on some systems)
    video_files = list(set(video_files))
    video_files.sort(key=lambda p: p.name.lower())

    if not video_files:
        warnings.append("No video files found in input folder")
        return ValidationResult(
            valid_videos=[],
            invalid_videos=[],
            warnings=warnings,
            total_segments=0,
            kmeans_viable=False,
            total_duration_seconds=0,
            segment_duration=SEGMENT_DURATION,
            min_split_duration=MIN_SPLIT_DURATION,
        )

    # Validate each video
    for video_path in video_files:
        info = validate_video(video_path)
        if info.valid:
            valid_videos.append(info)
        else:
            invalid_videos.append(info)

    # Calculate totals
    total_segments = sum(v.estimated_segments for v in valid_videos)
    total_duration = sum(v.duration_seconds for v in valid_videos)
    kmeans_viable = total_segments >= MIN_SEGMENTS_FOR_KMEANS

    # Generate warnings
    if invalid_videos:
        warnings.append(
            f"{len(invalid_videos)} video(s) have issues and will be skipped"
        )

    if not kmeans_viable and valid_videos:
        warnings.append(
            f"Only {total_segments} segments estimated "
            f"(need {MIN_SEGMENTS_FOR_KMEANS} for k-means training). "
            "Processing may fail at clustering stage."
        )

    # Warn about very long videos
    long_videos = [v for v in valid_videos if v.duration_seconds > 300]
    if long_videos:
        warnings.append(
            f"{len(long_videos)} video(s) are longer than 5 minutes. "
            "These will be split into 4-second segments."
        )

    return ValidationResult(
        valid_videos=valid_videos,
        invalid_videos=invalid_videos,
        warnings=warnings,
        total_segments=total_segments,
        kmeans_viable=kmeans_viable,
        total_duration_seconds=total_duration,
        segment_duration=SEGMENT_DURATION,
        min_split_duration=MIN_SPLIT_DURATION,
    )


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def get_video_files() -> List[Path]:
    """
    Get list of video files in input folder (excluding .excluded).
    Used by transcription manager to detect orphaned transcriptions.
    """
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        video_files.extend(INPUT_DIR.glob(f"*{ext}"))
        video_files.extend(INPUT_DIR.glob(f"*{ext.upper()}"))

    # Filter out .excluded folder and .transcriptions folder
    video_files = [f for f in video_files if ".excluded" not in str(f) and ".transcriptions" not in str(f)]

    return list(set(video_files))
