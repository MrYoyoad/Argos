#!/usr/bin/env python3
"""
Calculate WER per original video with overlap deduplication.

This script reads decode output and segment metadata to:
1. Group segments by original video
2. Concatenate predictions with overlap handling
3. Calculate WER per video (not per segment)
4. Output results as CSV

Usage:
    python calculate_per_video_wer.py \
        --decode-json decode/vsr/en/hypo-685605.json \
        --segment-metadata preprocessed_flat_seg12/segment_metadata.json \
        --output-csv wer_per_video.csv \
        --overlap-seconds 2.0 \
        --segment-duration 12.0
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
import editdistance


def parse_segment_id(segment_id: str) -> Dict:
    """
    Parse segment ID to extract video identification.

    Supports formats:
    1. {id}__{hash}_{idx}_{start}_{end}
    2. {video_name}_{idx}_{start}_{end}
    3. {id}__{hash} (old format)
    """
    # Remove extension if present
    if segment_id.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
        basename = Path(segment_id).stem
    else:
        basename = segment_id

    # Pattern 1: with hash
    pattern1 = r'^(.+?)__([a-f0-9]{8})_(\d{2})_(\d{6})_(\d{6})$'
    match = re.match(pattern1, basename)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2),
            'seg_idx': int(match.group(3)),
            'full_id': f"{match.group(1)}__{match.group(2)}"
        }

    # Pattern 2: without hash
    pattern2 = r'^(.+?)_(\d{2})_(\d{6})_(\d{6})$'
    match = re.match(pattern2, basename)
    if match:
        video_base = match.group(1)
        return {
            'video_id': video_base,
            'hash': None,
            'seg_idx': int(match.group(2)),
            'full_id': video_base
        }

    # Pattern 3: old format with hash, no frame info
    pattern3 = r'^(.+?)__([a-f0-9]{8})$'
    match = re.match(pattern3, basename)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2),
            'seg_idx': 0,
            'full_id': basename
        }

    # No pattern matched - treat as single segment
    return {
        'video_id': basename,
        'hash': None,
        'seg_idx': 0,
        'full_id': basename
    }


def group_segments_by_video(decode_data: Dict) -> Dict[str, List[Dict]]:
    """
    Group segments by original video using segment IDs.

    Returns:
        {video_full_id: [{'seg_idx': 0, 'hyp': '...', 'ref': '...'}, ...]}
    """
    video_groups = {}

    utt_ids = decode_data.get('utt_id', [])
    hypos = decode_data.get('hypo', [])
    refs = decode_data.get('ref', [])

    if len(utt_ids) != len(hypos) or len(utt_ids) != len(refs):
        raise ValueError("Mismatched lengths in decode data")

    for utt_id, hyp, ref in zip(utt_ids, hypos, refs):
        parsed = parse_segment_id(utt_id)
        full_id = parsed['full_id']
        seg_idx = parsed['seg_idx']

        if full_id not in video_groups:
            video_groups[full_id] = []

        video_groups[full_id].append({
            'seg_idx': seg_idx,
            'hyp': hyp,
            'ref': ref,
            'utt_id': utt_id
        })

    # Sort segments by index within each video
    for full_id in video_groups:
        video_groups[full_id].sort(key=lambda x: x['seg_idx'])

    return video_groups


def concatenate_with_overlap_handling(
    segments: List[Dict],
    overlap_seconds: float = 2.0,
    segment_duration: float = 12.0
) -> Tuple[str, str]:
    """
    Concatenate segments with overlap deduplication.

    Since we lack word-level timing, we use a heuristic:
    - Overlap is ~overlap_seconds/segment_duration of segment
    - For each segment after first, skip first N% of words

    Args:
        segments: List of segment dicts with 'hyp' and 'ref' keys
        overlap_seconds: Overlap duration in seconds
        segment_duration: Segment duration in seconds

    Returns:
        (concatenated_hyp, concatenated_ref)
    """
    if len(segments) == 1:
        return segments[0]['hyp'], segments[0]['ref']

    hyp_parts = []
    ref_parts = []
    overlap_ratio = overlap_seconds / segment_duration

    for i, seg in enumerate(segments):
        if i == 0:
            # First segment - use entirely
            hyp_parts.append(seg['hyp'])
            ref_parts.append(seg['ref'])
        else:
            # Subsequent segments - skip overlap portion
            hyp_words = seg['hyp'].split()
            ref_words = seg['ref'].split()

            # Skip first N% of words (overlap region)
            skip_hyp = int(len(hyp_words) * overlap_ratio)
            skip_ref = int(len(ref_words) * overlap_ratio)

            hyp_parts.append(' '.join(hyp_words[skip_hyp:]))
            ref_parts.append(' '.join(ref_words[skip_ref:]))

    return ' '.join(hyp_parts), ' '.join(ref_parts)


def calculate_wer_per_video(
    decode_json_path: str,
    segment_metadata_path: str,
    output_csv: str,
    overlap_seconds: float = 2.0,
    segment_duration: float = 12.0
):
    """
    Calculate WER for each original video.

    Args:
        decode_json_path: Path to decode output JSON
        segment_metadata_path: Path to segment_metadata.json (optional)
        output_csv: Path to output CSV file
        overlap_seconds: Overlap duration for deduplication
        segment_duration: Segment duration
    """
    # Load decode data
    print(f"Loading decode data from: {decode_json_path}")
    with open(decode_json_path, 'r') as f:
        decode_data = json.load(f)

    # Load segment metadata if available (currently not used, but could enhance grouping)
    segment_metadata = None
    if segment_metadata_path and Path(segment_metadata_path).exists():
        print(f"Loading segment metadata from: {segment_metadata_path}")
        with open(segment_metadata_path, 'r') as f:
            segment_metadata = json.load(f)

    # Group segments by video
    print("Grouping segments by original video...")
    video_groups = group_segments_by_video(decode_data)
    print(f"Found {len(video_groups)} videos")

    # Calculate WER per video
    results = []
    total_distance = 0
    total_ref_words = 0

    for video_id, segments in sorted(video_groups.items()):
        # Concatenate with overlap handling
        hyp_concat, ref_concat = concatenate_with_overlap_handling(
            segments, overlap_seconds, segment_duration
        )

        # Calculate WER
        hyp_words = hyp_concat.strip().split()
        ref_words = ref_concat.strip().split()

        distance = editdistance.eval(hyp_words, ref_words)
        wer = 100.0 * distance / len(ref_words) if ref_words else 0.0

        total_distance += distance
        total_ref_words += len(ref_words)

        results.append({
            'video_id': video_id,
            'num_segments': len(segments),
            'ref_words': len(ref_words),
            'hyp_words': len(hyp_words),
            'edit_distance': distance,
            'wer': wer
        })

        print(f"  {video_id}: {len(segments)} segments, WER={wer:.2f}%")

    # Calculate overall WER
    overall_wer = 100.0 * total_distance / total_ref_words if total_ref_words else 0.0

    # Write CSV
    print(f"\nWriting results to: {output_csv}")
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

    with open(output_csv, 'w') as f:
        f.write('video_id,num_segments,ref_words,hyp_words,edit_distance,wer\n')
        for r in results:
            f.write(f"{r['video_id']},{r['num_segments']},{r['ref_words']},"
                   f"{r['hyp_words']},{r['edit_distance']},{r['wer']:.2f}\n")

    print(f"\nSummary:")
    print(f"  Total videos: {len(results)}")
    print(f"  Total reference words: {total_ref_words}")
    print(f"  Total edit distance: {total_distance}")
    print(f"  Overall WER: {overall_wer:.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate WER per video with overlap deduplication'
    )
    parser.add_argument(
        '--decode-json',
        required=True,
        help='Path to decode output JSON (e.g., hypo-685605.json)'
    )
    parser.add_argument(
        '--segment-metadata',
        help='Path to segment_metadata.json (optional, for enhanced grouping)'
    )
    parser.add_argument(
        '--output-csv',
        required=True,
        help='Path to output CSV file'
    )
    parser.add_argument(
        '--overlap-seconds',
        type=float,
        default=2.0,
        help='Overlap duration in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--segment-duration',
        type=float,
        default=12.0,
        help='Segment duration in seconds (default: 12.0)'
    )

    args = parser.parse_args()

    calculate_wer_per_video(
        decode_json_path=args.decode_json,
        segment_metadata_path=args.segment_metadata,
        output_csv=args.output_csv,
        overlap_seconds=args.overlap_seconds,
        segment_duration=args.segment_duration
    )


if __name__ == '__main__':
    main()
