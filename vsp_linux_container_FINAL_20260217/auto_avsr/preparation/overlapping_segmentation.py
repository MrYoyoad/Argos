#!/usr/bin/env python3
"""
Overlapping video segmentation module.

Provides time-based video segmentation with configurable overlap.
Completely independent of existing preprocessing - can be toggled on/off.

Usage:
    from overlapping_segmentation import split_video_by_time

    segments = split_video_by_time(
        video_duration=10.0,
        segment_duration=4.0,
        overlap_duration=1.0,
        min_split_duration=8.0,
        fps=25.0
    )
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any


def split_video_by_time(
    video_duration: float,
    segment_duration: float = 4.0,
    overlap_duration: float = 1.0,
    min_split_duration: float = 8.0,
    fps: float = 25.0
) -> List[Tuple[float, float, int, int]]:
    """
    Split video into overlapping time-based segments.

    This function creates segments at fixed time intervals with overlap,
    independent of word boundaries or transcript content.

    Args:
        video_duration: Total video duration in seconds
        segment_duration: Duration of each segment in seconds (default 4.0)
        overlap_duration: Overlap between segments in seconds (default 1.0)
        min_split_duration: Minimum video duration to trigger splitting (default 8.0)
        fps: Frames per second (default 25.0)

    Returns:
        List of tuples: (start_time, end_time, start_frame, end_frame)
        - start_time: Start timestamp in seconds
        - end_time: End timestamp in seconds
        - start_frame: Start frame index (0-based)
        - end_frame: End frame index (exclusive)

    Example:
        >>> segments = split_video_by_time(10.0, 4.0, 1.0, 8.0, 25.0)
        >>> # Returns: [(0.0, 4.0, 0, 100), (3.0, 7.0, 75, 175), (6.0, 10.0, 150, 250)]
    """
    # Check if video is long enough to warrant splitting
    if video_duration < min_split_duration:
        # Return single segment covering entire video
        end_frame = int(video_duration * fps)
        return [(0.0, video_duration, 0, end_frame)]

    # Calculate stride (distance between segment starts)
    stride = segment_duration - overlap_duration
    if stride <= 0:
        raise ValueError(f"Overlap ({overlap_duration}s) must be less than segment duration ({segment_duration}s)")

    segments = []
    current_start = 0.0

    while current_start < video_duration:
        # Calculate segment end time
        segment_end = min(current_start + segment_duration, video_duration)

        # Convert to frame indices
        start_frame = int(current_start * fps)
        end_frame = int(segment_end * fps)

        # Ensure end_frame doesn't exceed video
        max_frame = int(video_duration * fps)
        end_frame = min(end_frame, max_frame)

        # Add segment
        segments.append((current_start, segment_end, start_frame, end_frame))

        # Move to next segment start
        current_start += stride

        # Stop if we've covered the video
        if segment_end >= video_duration:
            break

    return segments


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds

    Raises:
        RuntimeError: If ffprobe fails
    """
    import subprocess
    import json

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except Exception as e:
        raise RuntimeError(f"Failed to get video duration for {video_path}: {e}")


def split_file_with_overlap(
    filename: str,
    video_data,  # torch tensor or numpy array
    max_frames: int = 600,
    overlap_duration: float = 1.0,
    min_split_duration: float = 8.0,
    fps: float = 25.0
) -> List[Tuple[str, float, float, float, int, int]]:
    """
    Split video data into overlapping segments with transcript.

    This is the main entry point that combines time-based segmentation
    with transcript reading.

    Args:
        filename: Path to transcript file (.wrd or .txt)
        video_data: Video frames tensor/array
        max_frames: Maximum frames per segment (defines segment_duration)
        overlap_duration: Overlap in seconds (default 1.0)
        min_split_duration: Minimum video duration to trigger splitting (default 8.0)
        fps: Frames per second (default 25.0)

    Returns:
        List of tuples: (content, start_time, end_time, duration, start_frame, end_frame)
        - content: Full transcript (same for all segments)
        - start_time: Start timestamp in seconds
        - end_time: End timestamp in seconds
        - duration: Segment duration in seconds
        - start_frame: Start frame index
        - end_frame: End frame index
    """
    # Get segment duration from max_frames
    segment_duration = max_frames / fps

    # Get video duration from video_data
    try:
        num_frames = video_data.shape[0] if hasattr(video_data, 'shape') else len(video_data)
        video_duration = num_frames / fps
    except Exception as e:
        raise ValueError(f"Cannot determine video duration from video_data: {e}")

    # Get time-based segments
    time_segments = split_video_by_time(
        video_duration=video_duration,
        segment_duration=segment_duration,
        overlap_duration=overlap_duration,
        min_split_duration=min_split_duration,
        fps=fps
    )

    # Read transcript content
    content = read_transcript(filename)

    # Combine time segments with transcript
    result = []
    for start_time, end_time, start_frame, end_frame in time_segments:
        duration = end_time - start_time
        result.append((content, start_time, end_time, duration, start_frame, end_frame))

    return result


def read_transcript(filename: str) -> str:
    """
    Read transcript from .wrd or .txt file.

    Args:
        filename: Path to transcript file

    Returns:
        Transcript as single string (space-separated words)
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.read().strip().splitlines()

        # Filter out header lines and empty lines
        words = [line.strip() for line in lines
                 if line.strip() and not line.startswith('#') and 'WORD START END' not in line]

        return " ".join(words)
    except Exception as e:
        print(f"Warning: Failed to read transcript from {filename}: {e}")
        return "no audio"


def split_file_with_overlap_compat(
    filename: str,
    max_frames: int = 600,
    fps: float = 25.0
) -> List[Tuple[str, float, float, float]]:
    """
    Compatibility wrapper for existing split_file() interface.

    This version doesn't require video_data and returns format compatible
    with utils.split_file() but WITHOUT overlap (for backward compat).

    Args:
        filename: Path to transcript file
        max_frames: Maximum frames per segment
        fps: Frames per second

    Returns:
        List of (content, start_time, end_time, duration) tuples
    """
    from .utils import split_file
    return split_file(filename, max_frames, fps)



def generate_segment_metadata(
    video_segments_map: Dict[str, List[Tuple[str, float, float, float, int, int]]],
    output_path: str,
    segment_duration: float = 4.0,
    overlap_duration: float = 1.0
) -> None:
    """
    Generate segment_metadata.json for downstream processing.

    Args:
        video_segments_map: Dict mapping video_id to list of segments
            video_id: str (e.g., "video__abc123")
            segments: List of (content, start_time, end_time, duration, start_frame, end_frame)
        output_path: Path to write JSON file
        segment_duration: Base segment duration in seconds
        overlap_duration: Overlap duration in seconds

    Output format:
        {
          "video_id__hash": {
            "original_duration": 10.0,
            "segment_duration": 4.0,
            "overlap_duration": 1.0,
            "num_segments": 3,
            "segments": [
              {
                "index": 0,
                "start_frame": 0,
                "end_frame": 100,
                "start_sec": 0.0,
                "end_sec": 4.0,
                "duration": 4.0
              },
              ...
            ]
          }
        }
    """
    metadata = {}

    for video_id, segments in video_segments_map.items():
        if not segments:
            continue

        # Calculate original duration from last segment
        # segments format: (content, start_time, end_time, duration, start_frame, end_frame)
        original_duration = segments[-1][2]  # end_time of last segment

        segment_metadata = {
            "original_duration": round(original_duration, 2),
            "segment_duration": round(segment_duration, 2),
            "overlap_duration": round(overlap_duration, 2),
            "num_segments": len(segments),
            "segments": []
        }

        for idx, (content, start_time, end_time, duration, start_frame, end_frame) in enumerate(segments):
            segment_metadata["segments"].append({
                "index": idx,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "start_sec": round(start_time, 2),
                "end_sec": round(end_time, 2),
                "duration": round(duration, 2)
            })

        metadata[video_id] = segment_metadata

    # Write to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Segment metadata written to: {output_path}")
    print(f"  Total videos: {len(metadata)}")
    print(f"  Total segments: {sum(v['num_segments'] for v in metadata.values())}")

    # Print summary statistics
    all_durations = [v['original_duration'] for v in metadata.values()]
    all_seg_counts = [v['num_segments'] for v in metadata.values()]

    if all_durations:
        avg_duration = sum(all_durations) / len(all_durations)
        avg_segments = sum(all_seg_counts) / len(all_seg_counts)
        print(f"  Average video duration: {avg_duration:.1f}s")
        print(f"  Average segments per video: {avg_segments:.1f}")
        print(f"  Videos with multiple segments: {sum(1 for c in all_seg_counts if c > 1)}")
        print(f"  Videos with single segment (<8s): {sum(1 for c in all_seg_counts if c == 1)}")


# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python overlapping_segmentation.py <video_duration>")
        print("Example: python overlapping_segmentation.py 10.5")
        sys.exit(1)

    try:
        video_duration = float(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid duration")
        sys.exit(1)

    print(f"Testing overlapping segmentation for {video_duration}s video")
    print(f"Configuration: 4s segments, 1s overlap, 8s minimum for splitting\n")

    # Test time-based segmentation
    segments = split_video_by_time(
        video_duration=video_duration,
        segment_duration=4.0,
        overlap_duration=1.0,
        min_split_duration=8.0,
        fps=25.0
    )

    print(f"Generated {len(segments)} segment(s):\n")
    for idx, (start_time, end_time, start_frame, end_frame) in enumerate(segments):
        duration = end_time - start_time
        print(f"Segment {idx}:")
        print(f"  Time: {start_time:.2f}s - {end_time:.2f}s (duration: {duration:.2f}s)")
        print(f"  Frames: {start_frame} - {end_frame} ({end_frame - start_frame} frames)")

        # Check overlap with previous segment
        if idx > 0:
            prev_end = segments[idx - 1][1]
            overlap = prev_end - start_time
            print(f"  Overlap with previous: {overlap:.2f}s ({int(overlap * 25)} frames)")
        print()

    # Test metadata generation
    print("Testing metadata generation...")
    # Create mock video segments with content
    content = "test transcript words"
    video_segments = [(content, st, et, et-st, sf, ef)
                      for st, et, sf, ef in segments]

    video_id = f"test_video_{video_duration}s__abc123"
    metadata_map = {video_id: video_segments}

    output_path = f"/tmp/test_segment_metadata_{video_duration}s.json"
    generate_segment_metadata(
        metadata_map,
        output_path,
        segment_duration=4.0,
        overlap_duration=1.0
    )

    print(f"\n✓ Metadata saved to: {output_path}")
    print("\nYou can inspect the JSON file to verify the segment structure.")
