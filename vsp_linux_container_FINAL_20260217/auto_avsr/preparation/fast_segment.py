#!/usr/bin/env python3
"""
Ultra-fast video segmentation using ffmpeg -c copy (no processing at all).
Just splits videos so users can start transcribing immediately.
All processing (normalization, face detection, mouth cropping) happens after transcription.
"""
import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Dict


def get_video_info(video_path: Path) -> tuple:
    """Get video duration and FPS using ffprobe."""
    try:
        # Duration
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ], capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip())

        # FPS
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ], capture_output=True, text=True, timeout=30)
        fps_str = result.stdout.strip()
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = float(num) / float(den)
        else:
            fps = float(fps_str) if fps_str else 25.0

        return duration, fps
    except Exception as e:
        print(f"Error getting info for {video_path.name}: {e}")
        return 0.0, 25.0


def fast_segment(video_path: Path, output_dir: Path, seg_duration: float,
                 overlap: float, min_split_duration: float) -> List[Dict]:
    """
    Split video using ffmpeg -c copy (no re-encoding, maximum speed).
    """
    duration, fps = get_video_info(video_path)

    if duration == 0:
        print(f"  SKIP: {video_path.name} (could not read duration)")
        return []

    video_id = video_path.stem
    segments = []

    # Short video - just copy as-is
    if duration < min_split_duration:
        output_file = output_dir / f"{video_id}_00_000000_{int(duration * fps):06d}.mp4"

        try:
            subprocess.run([
                'ffmpeg', '-y', '-loglevel', 'error',
                '-i', str(video_path),
                '-c', 'copy',
                str(output_file)
            ], check=True, timeout=300)

            segments.append({
                'original_video': video_path.name,
                'video_id': video_id,
                'segment_index': 0,
                'segment_id': output_file.stem,
                'filename': output_file.name,
                'start_sec': 0.0,
                'end_sec': duration,
                'duration': duration,
                'start_frame': 0,
                'end_frame': int(duration * fps)
            })
            print(f"  ✓ {video_path.name} → 1 segment ({duration:.1f}s)")
        except subprocess.CalledProcessError:
            print(f"  ✗ {video_path.name} (ffmpeg error)")

        return segments

    # Long video - split with overlap
    stride = seg_duration - overlap
    num_segments = int((duration - overlap) / stride) + 1

    for seg_idx in range(num_segments):
        start_sec = seg_idx * stride
        end_sec = min(start_sec + seg_duration, duration)

        if end_sec > duration:
            end_sec = duration

        actual_duration = end_sec - start_sec

        if actual_duration < 0.5:
            continue

        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)

        output_file = output_dir / f"{video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4"

        try:
            subprocess.run([
                'ffmpeg', '-y', '-loglevel', 'error',
                '-ss', str(start_sec),
                '-i', str(video_path),
                '-t', str(actual_duration),
                '-c', 'copy',
                str(output_file)
            ], check=True, timeout=300)

            segments.append({
                'original_video': video_path.name,
                'video_id': video_id,
                'segment_index': seg_idx,
                'segment_id': output_file.stem,
                'filename': output_file.name,
                'start_sec': start_sec,
                'end_sec': end_sec,
                'duration': actual_duration,
                'start_frame': start_frame,
                'end_frame': end_frame
            })
        except subprocess.CalledProcessError:
            print(f"  ✗ Segment {seg_idx} failed")

    print(f"  ✓ {video_path.name} → {len(segments)} segments ({duration:.1f}s)")
    return segments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--seg-duration', type=float, default=12.0)
    parser.add_argument('--overlap', type=float, default=2.0)
    parser.add_argument('--min-split-duration', type=float, default=24.0)

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find videos
    exts = ['.mp4', '.mkv', '.webm', '.mov', '.m4v', '.avi']
    videos = []
    for ext in exts:
        videos.extend(data_dir.glob(f'*{ext}'))
        videos.extend(data_dir.glob(f'*{ext.upper()}'))

    videos = sorted(set(videos))

    if not videos:
        print("No videos found")
        return

    print(f"\nFast Segmentation (no processing)")
    print(f"  Input: {len(videos)} videos")
    print(f"  Segment: {args.seg_duration}s, Overlap: {args.overlap}s")
    print(f"  Split if >{args.min_split_duration}s\n")

    all_segments = []

    for video in videos:
        segs = fast_segment(video, output_dir, args.seg_duration,
                           args.overlap, args.min_split_duration)
        all_segments.extend(segs)

    # Save metadata
    metadata = output_dir / 'segment_metadata.json'
    with open(metadata, 'w') as f:
        json.dump({
            'segments': all_segments,
            'total_segments': len(all_segments),
            'total_videos': len(videos),
            'seg_duration': args.seg_duration,
            'overlap': args.overlap,
            'min_split_duration': args.min_split_duration
        }, f, indent=2)

    print(f"\n✓ Done! {len(all_segments)} segments created")
    print(f"  Metadata: {metadata}\n")


if __name__ == '__main__':
    main()
