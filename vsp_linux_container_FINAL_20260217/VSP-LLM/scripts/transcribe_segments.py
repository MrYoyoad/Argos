#!/usr/bin/env python3
"""
Interactive tool for manually transcribing video segments.

This script helps users manually transcribe segments after preprocessing.
It shows each segment video and allows users to type the transcription.

Usage:
    python transcribe_segments.py \
        --segment-dir /path/to/preprocessed_flat_seg12/flat/flat_video_seg12s \
        --output-dir /path/to/preprocessed_flat_seg12/flat/flat_text_seg12s

Features:
    - Lists all segments without transcriptions
    - Shows segment metadata (duration, frame range)
    - Accepts transcription input (space or newline separated words)
    - Automatically normalizes to pipeline format (lowercase, alphanumeric)
    - Shows progress (X of Y segments transcribed)
    - Allows skipping segments
    - Resume support (skips already-transcribed segments)
"""

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def normalize_transcription(text: str) -> str:
    """
    Normalize transcription to pipeline format.

    - Lowercase
    - Keep only alphanumeric and apostrophes
    - Space-separated words

    Args:
        text: Raw transcription text

    Returns:
        Normalized text matching pipeline format
    """
    # Lowercase
    text = text.lower()

    # Keep only alphanumeric and apostrophes, replace other chars with spaces
    text = re.sub(r"[^a-z0-9'\s]", ' ', text)

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def get_segment_files(segment_dir: str) -> List[str]:
    """
    Get list of segment video files.

    Args:
        segment_dir: Directory containing segment videos

    Returns:
        Sorted list of segment filenames (basenames without extension)
    """
    segment_path = Path(segment_dir)

    if not segment_path.exists():
        return []

    # Get all .mp4 files
    videos = sorted(segment_path.glob('*.mp4'))

    # Return basenames without extension
    return [v.stem for v in videos]


def get_video_info(video_path: str) -> Tuple[float, int, int]:
    """
    Get video metadata using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        (duration_seconds, width, height)
    """
    try:
        # Get duration
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True, check=True)

        duration = float(result.stdout.strip())

        # Get dimensions
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            video_path
        ], capture_output=True, text=True, check=True)

        width, height = map(int, result.stdout.strip().split(','))

        return (duration, width, height)
    except Exception as e:
        print(f"Warning: Could not get video info for {video_path}: {e}")
        return (0, 0, 0)


def has_transcription(segment_id: str, output_dir: str) -> bool:
    """
    Check if segment already has a transcription.

    Args:
        segment_id: Segment ID (basename without extension)
        output_dir: Directory containing transcription .txt files

    Returns:
        True if transcription exists
    """
    txt_path = Path(output_dir) / f"{segment_id}.txt"
    return txt_path.exists()


def save_transcription(segment_id: str, transcription: str, output_dir: str):
    """
    Save transcription to .txt file.

    Args:
        segment_id: Segment ID (basename without extension)
        transcription: Transcription text (already normalized)
        output_dir: Directory to save transcription
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_path = output_path / f"{segment_id}.txt"

    # Write one word per line (pipeline format)
    words = transcription.split()
    with open(txt_path, 'w') as f:
        for word in words:
            f.write(word + '\n')

    print(f"✓ Saved: {txt_path}")


def interactive_transcribe(segment_dir: str, output_dir: str, resume: bool = True):
    """
    Interactively transcribe segments.

    Args:
        segment_dir: Directory containing segment videos
        output_dir: Directory to save transcriptions
        resume: If True, skip segments that already have transcriptions
    """
    print("=== Interactive Segment Transcription ===\n")

    # Get all segments
    segments = get_segment_files(segment_dir)

    if not segments:
        print(f"No segments found in: {segment_dir}")
        return

    print(f"Found {len(segments)} segments\n")

    # Filter out already-transcribed segments if resuming
    if resume:
        remaining = [s for s in segments if not has_transcription(s, output_dir)]
        already_done = len(segments) - len(remaining)

        if already_done > 0:
            print(f"Skipping {already_done} already-transcribed segments")
            print(f"Remaining: {len(remaining)} segments\n")

        segments = remaining

    if not segments:
        print("All segments already transcribed!")
        return

    # Transcribe each segment
    for idx, segment_id in enumerate(segments, 1):
        video_path = Path(segment_dir) / f"{segment_id}.mp4"

        print(f"\n{'='*60}")
        print(f"Segment {idx} of {len(segments)}: {segment_id}")
        print(f"{'='*60}")

        # Get video info
        duration, width, height = get_video_info(str(video_path))
        if duration > 0:
            print(f"Duration: {duration:.1f}s | Resolution: {width}x{height}")

        print(f"Video: {video_path}")
        print()

        # Instructions
        print("Instructions:")
        print("  - Watch the video and type the transcription")
        print("  - Enter words separated by spaces or newlines")
        print("  - Type 'skip' to skip this segment")
        print("  - Type 'quit' to exit")
        print("  - Press Ctrl+D (EOF) when done entering text")
        print()

        # Get transcription input
        print("Enter transcription (Ctrl+D when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        raw_text = '\n'.join(lines).strip()

        # Handle special commands
        if raw_text.lower() == 'skip':
            print("Skipped.")
            continue

        if raw_text.lower() == 'quit':
            print("\nExiting...")
            break

        if not raw_text:
            print("Empty transcription. Skipping...")
            continue

        # Normalize transcription
        normalized = normalize_transcription(raw_text)

        # Show preview
        print(f"\nNormalized: {normalized}")
        print(f"Word count: {len(normalized.split())}")

        # Confirm
        confirm = input("\nSave this transcription? [Y/n]: ").strip().lower()
        if confirm in ('', 'y', 'yes'):
            save_transcription(segment_id, normalized, output_dir)
        else:
            print("Discarded.")

    print(f"\n✓ Transcription complete!")
    print(f"Transcriptions saved to: {output_dir}")


def list_segments(segment_dir: str, output_dir: str, show_all: bool = False):
    """
    List segments and their transcription status.

    Args:
        segment_dir: Directory containing segment videos
        output_dir: Directory containing transcriptions
        show_all: If True, show all segments; if False, only untranscribed
    """
    segments = get_segment_files(segment_dir)

    if not segments:
        print(f"No segments found in: {segment_dir}")
        return

    transcribed = [s for s in segments if has_transcription(s, output_dir)]
    untranscribed = [s for s in segments if not has_transcription(s, output_dir)]

    print(f"Total segments: {len(segments)}")
    print(f"Transcribed: {len(transcribed)}")
    print(f"Untranscribed: {len(untranscribed)}")
    print()

    if show_all or not untranscribed:
        print("All segments:")
        for s in segments:
            status = "✓" if has_transcription(s, output_dir) else "✗"
            print(f"  {status} {s}")
    else:
        print("Untranscribed segments:")
        for s in untranscribed:
            print(f"  ✗ {s}")


def main():
    parser = argparse.ArgumentParser(
        description='Interactive tool for manually transcribing video segments'
    )

    parser.add_argument(
        '--segment-dir',
        required=True,
        help='Directory containing segment videos (e.g., flat_video_seg12s)'
    )

    parser.add_argument(
        '--output-dir',
        required=True,
        help='Directory to save transcriptions (e.g., flat_text_seg12s)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List segments and their transcription status, then exit'
    )

    parser.add_argument(
        '--show-all',
        action='store_true',
        help='With --list, show all segments (not just untranscribed)'
    )

    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Do not skip already-transcribed segments'
    )

    args = parser.parse_args()

    # Validate directories
    if not Path(args.segment_dir).exists():
        print(f"ERROR: Segment directory not found: {args.segment_dir}")
        return 1

    # List mode
    if args.list:
        list_segments(args.segment_dir, args.output_dir, args.show_all)
        return 0

    # Interactive transcription
    interactive_transcribe(
        args.segment_dir,
        args.output_dir,
        resume=not args.no_resume
    )

    return 0


if __name__ == '__main__':
    exit(main())
