#!/usr/bin/env python3
"""
Preprocessing wrapper with overlapping segmentation support.

This script extends preprocess_lrs2lrs3.py to support overlapping video
segmentation for the 'flat' dataset. It can be used as a drop-in replacement
when OVERLAP_ENABLED=1.

For 'flat' dataset:
- Applies time-based overlapping segmentation (4s segments, 1s overlap)
- Saves segments with frame ranges in filenames: {id}_{idx:02d}_{start:06d}_{end:06d}.mp4
- Generates segment_metadata.json for downstream processing

For other datasets (lrs2, lrs3):
- Falls back to standard preprocessing (no changes)

Usage:
    python preprocess_with_overlap.py \\
        --data-dir /path/to/videos \\
        --root-dir /path/to/output \\
        --dataset flat \\
        --detector mediapipe \\
        --seg-duration 4 \\
        --overlap-duration 1.0 \\
        --min-split-duration 8.0 \\
        --subset train
"""

import argparse
import glob
import os
import sys
import warnings
from pathlib import Path
from tqdm import tqdm

# Import from existing preprocessing
from data.data_module import AVSRDataLoader
from transforms import TextTransform
from utils import save_vid_aud_txt
from overlapping_segmentation import (
    split_video_by_time,
    split_file_with_overlap,
    generate_segment_metadata,
    read_transcript
)

warnings.filterwarnings("ignore")

def _make_silent_audio_like(trim_vid_data, sample_rate=16000, fps=25):
    """Create silent audio matching video length."""
    num_frames = int(len(trim_vid_data))
    num_samples = num_frames * (sample_rate // fps)
    try:
        import torch
        return torch.zeros(1, num_samples, dtype=torch.float32)
    except Exception:
        import numpy as np
        return np.zeros((1, num_samples), dtype=np.float32)


def to_gray(frames):
    """Convert frames to grayscale."""
    try:
        import torch
        if torch.is_tensor(frames):
            x = frames
            if x.ndim == 3:
                return x
            if x.ndim == 4 and x.shape[-1] in (1, 3):
                if x.shape[-1] == 1:
                    return x[..., 0]
                r, g, b = x[..., 0].float(), x[..., 1].float(), x[..., 2].float()
                return 0.2989 * r + 0.5870 * g + 0.1140 * b
    except Exception:
        pass

    # numpy fallback
    import numpy as np
    if frames.ndim == 3:
        return frames
    if frames.ndim == 4 and frames.shape[-1] in (1, 3):
        if frames.shape[-1] == 1:
            return frames[..., 0]
        r, g, b = frames[..., 0], frames[..., 1], frames[..., 2]
        return 0.2989 * r + 0.5870 * g + 0.1140 * b
    return frames


def apply_paper_like_video(frames, target_size=(88, 88)):
    """Apply paper-like transformations: grayscale + resize.

    Returns RGB format (T, H, W, 3) by replicating grayscale channel,
    as required by torchvision.io.write_video.
    """
    frames_gray = to_gray(frames)

    try:
        import torch
        import torchvision.transforms.functional as F
        if torch.is_tensor(frames_gray):
            # frames_gray: (T, H, W)
            if frames_gray.ndim != 3:
                raise ValueError(f"Expected 3D grayscale tensor, got {frames_gray.ndim}D with shape {frames_gray.shape}")

            T, H, W = frames_gray.shape
            # Resize each frame
            resized = []
            for t in range(T):
                frame = frames_gray[t]  # (H, W)
                frame_3c = frame.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)
                frame_resized = F.resize(frame_3c, target_size, antialias=True)
                resized.append(frame_resized.squeeze(0).squeeze(0))
            result = torch.stack(resized, dim=0)  # (T, 88, 88)
            # Replicate grayscale to RGB: (T, H, W) -> (T, H, W, 3)
            return result.unsqueeze(-1).repeat(1, 1, 1, 3)
    except Exception as e:
        print(f"Warning: PyTorch path failed in apply_paper_like_video: {e}")

    # numpy fallback
    import cv2
    import numpy as np
    if isinstance(frames_gray, np.ndarray):
        if frames_gray.ndim != 3:
            raise ValueError(f"Expected 3D grayscale array, got {frames_gray.ndim}D with shape {frames_gray.shape}")

        T = frames_gray.shape[0]
        resized = np.zeros((T, target_size[0], target_size[1]), dtype=frames_gray.dtype)
        for t in range(T):
            resized[t] = cv2.resize(frames_gray[t], target_size, interpolation=cv2.INTER_LINEAR)
        # Replicate grayscale to RGB: (T, H, W) -> (T, H, W, 3)
        return np.stack([resized, resized, resized], axis=-1)

    # This should never be reached
    raise RuntimeError(f"Failed to process frames of type {type(frames_gray)} with shape {getattr(frames_gray, 'shape', 'unknown')}")


def preprocess_flat_with_overlap(args, filenames, f, vid_dataloader, aud_dataloader, text_transform):
    """
    Preprocess 'flat' dataset with overlapping segmentation.

    Args:
        args: Parsed arguments
        filenames: List of video filenames
        f: Output CSV file handle
        vid_dataloader: Video data loader
        aud_dataloader: Audio data loader
        text_transform: Text tokenization transform
    """
    segment_duration = args.seg_duration
    overlap_duration = args.overlap_duration
    min_split_duration = args.min_split_duration
    fps = 25.0

    dataset = args.dataset
    dst_vid_dir = os.path.join(args.root_dir, dataset, f"{dataset}_video_seg{args.seg_duration}s")
    dst_txt_dir = os.path.join(args.root_dir, dataset, f"{dataset}_text_seg{args.seg_duration}s")
    os.makedirs(dst_vid_dir, exist_ok=True)
    os.makedirs(dst_txt_dir, exist_ok=True)

    # Track segments for metadata generation
    all_segments_map = {}

    for data_filename in tqdm(filenames, desc="Processing videos"):
        try:
            # Load video and audio
            video_data = vid_dataloader.load_data(data_filename)
            if video_data is None:
                continue

            # Check for audio
            try:
                audio_data = aud_dataloader.load_data(data_filename)
                if audio_data is None:
                    raise ValueError("no audio")
            except Exception:
                # Create silent audio
                audio_data = _make_silent_audio_like(video_data, sample_rate=16000, fps=25)

            # Get video duration
            num_frames = video_data.shape[0] if hasattr(video_data, 'shape') else len(video_data)
            video_duration = num_frames / fps

            # Generate time-based segments
            if args.disable_segmentation:
                # Videos are already segmented - treat entire video as single segment
                time_segments = [(0.0, video_duration, 0, num_frames)]
            else:
                # Apply segmentation with overlap
                time_segments = split_video_by_time(
                    video_duration=video_duration,
                    segment_duration=segment_duration,
                    overlap_duration=overlap_duration,
                    min_split_duration=min_split_duration,
                    fps=fps
                )

            # Read transcript
            txt_path = data_filename[:-4] + ".txt"
            if os.path.exists(txt_path):
                content = read_transcript(txt_path)
            else:
                # Try .wrd file
                wrd_path = data_filename.replace(args.data_dir, args.data_dir.replace("flat", "flat_wrd"))[:-4] + ".wrd"
                if os.path.exists(wrd_path):
                    content = read_transcript(wrd_path)
                else:
                    content = "no audio"

            # Extract video ID for metadata tracking
            video_id = os.path.splitext(os.path.basename(data_filename))[0]

            # Track segments for metadata
            segment_list = []

            # Process each segment
            for idx, (start_time, end_time, start_frame, end_frame) in enumerate(time_segments):
                # Extract segment frames
                try:
                    trim_vid_data = video_data[start_frame:end_frame]
                    trim_aud_data = audio_data[:, start_frame * 640 : end_frame * 640]
                except Exception as e:
                    print(f"Error extracting segment {idx} from {video_id}: {e}")
                    continue

                if trim_vid_data is None or trim_aud_data is None:
                    continue
                if len(trim_vid_data) == 0 or trim_aud_data.size(1) == 0:
                    continue

                # Apply paper-like video processing
                trim_vid_data = apply_paper_like_video(trim_vid_data)

                # Generate filenames with frame ranges
                base_name = data_filename.replace(args.data_dir, "")[1:]  # Remove leading /
                if base_name.endswith(".mp4"):
                    base_name = base_name[:-4]

                # For non-split videos (single segment), keep original name
                # For split videos, add segment suffix with frame numbers
                if len(time_segments) == 1:
                    # Single segment (video too short to split) - keep original name
                    segment_suffix = ""
                else:
                    # Multiple segments - add index and frame range
                    segment_suffix = f"_{idx:02d}_{start_frame:06d}_{end_frame:06d}"

                dst_vid_filename = os.path.join(dst_vid_dir, base_name + segment_suffix + ".mp4")
                dst_aud_filename = os.path.join(dst_vid_dir, base_name + segment_suffix + ".wav")
                dst_txt_filename = os.path.join(dst_txt_dir, base_name + segment_suffix + ".txt")

                # Create directories
                os.makedirs(os.path.dirname(dst_vid_filename), exist_ok=True)
                os.makedirs(os.path.dirname(dst_txt_filename), exist_ok=True)

                # Save segment
                save_vid_aud_txt(
                    dst_vid_filename,
                    dst_aud_filename,
                    dst_txt_filename,
                    trim_vid_data,
                    trim_aud_data,
                    content,
                    video_fps=25,
                    audio_sample_rate=16000
                )

                # Write to CSV
                basename = os.path.relpath(dst_vid_filename, start=os.path.join(args.root_dir, dataset))
                token_id_str = " ".join(map(str, [_.item() for _ in text_transform.tokenize(content)]))
                if token_id_str:
                    nframes = trim_vid_data.shape[0] if hasattr(trim_vid_data, 'shape') else len(trim_vid_data)
                    f.write(f"{dataset},{basename},{nframes},{token_id_str}\n")

                # Track for metadata
                duration = end_time - start_time
                segment_list.append((content, start_time, end_time, duration, start_frame, end_frame))

            # Save segments for this video
            if segment_list:
                all_segments_map[video_id] = segment_list

        except Exception as e:
            print(f"Error processing {data_filename}: {e}")
            continue

    # Generate segment metadata
    metadata_path = os.path.join(args.root_dir, "segment_metadata.json")
    generate_segment_metadata(
        all_segments_map,
        metadata_path,
        segment_duration=segment_duration,
        overlap_duration=overlap_duration
    )

    print(f"\n✓ Preprocessing complete!")
    print(f"  Output directory: {dst_vid_dir}")
    print(f"  Segment metadata: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Preprocessing with overlapping segmentation")
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--detector", type=str, default="mediapipe")
    parser.add_argument("--landmarks-dir", type=str, default=None)
    parser.add_argument("--root-dir", type=str, required=True)
    parser.add_argument("--subset", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--gpu_type", type=str, default="cuda")
    parser.add_argument("--seg-duration", type=int, default=4)
    parser.add_argument("--overlap-duration", type=float, default=1.0)
    parser.add_argument("--min-split-duration", type=float, default=8.0)
    parser.add_argument("--combine-av", type=lambda x: str(x).lower() == "true", default=False)
    parser.add_argument("--groups", type=int, default=1)
    parser.add_argument("--job-index", type=int, default=0)
    parser.add_argument("--mouth_size", type=int, default=96)
    parser.add_argument("--force_gray", type=lambda x: str(x).lower() == "true", default=True)
    parser.add_argument("--disable-segmentation", action="store_true", default=False,
                        help="Disable video segmentation (videos are already segmented)")

    args = parser.parse_args()

    dataset = args.dataset
    seg_duration = args.seg_duration

    # Validate dataset
    if dataset != "flat":
        print(f"ERROR: This script only supports 'flat' dataset with overlapping segmentation.")
        print(f"For '{dataset}' dataset, use standard preprocess_lrs2lrs3.py")
        sys.exit(1)

    # Initialize data loaders
    vid_dataloader = AVSRDataLoader(
        modality="video",
        detector=args.detector,
        convert_gray=False,
        gpu_type=args.gpu_type,
    )
    aud_dataloader = AVSRDataLoader(modality="audio")
    text_transform = TextTransform()

    # Find files
    filenames = sorted(glob.glob(os.path.join(args.data_dir, "*.mp4")))

    # Shard if needed
    if args.groups > 1:
        filenames = [f for i, f in enumerate(filenames) if i % args.groups == args.job_index]

    print(f"Found {len(filenames)} video files")
    print(f"Segmentation config: {seg_duration}s segments, {args.overlap_duration}s overlap")
    print(f"Minimum split duration: {args.min_split_duration}s")

    # Open output CSV
    label_filename = os.path.join(
        args.root_dir,
        "labels",
        f"{dataset}_{args.subset}_transcript_lengths_seg{seg_duration}s.csv"
        if args.groups <= 1
        else f"{dataset}_{args.subset}_transcript_lengths_seg{seg_duration}s.{args.groups}.{args.job_index}.csv",
    )
    os.makedirs(os.path.dirname(label_filename), exist_ok=True)

    with open(label_filename, "w") as f:
        preprocess_flat_with_overlap(args, filenames, f, vid_dataloader, aud_dataloader, text_transform)

    print(f"\n✓ Labels written to: {label_filename}")


if __name__ == "__main__":
    main()
