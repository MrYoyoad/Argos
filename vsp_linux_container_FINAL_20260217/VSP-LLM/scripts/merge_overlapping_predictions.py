#!/usr/bin/env python3
"""
Merge overlapping segment predictions with conflict detection.

This script merges predictions from overlapping video segments, detects
disagreements, and generates conflict reports for user review.

Usage:
    python merge_overlapping_predictions.py \
        --decode-json decode/vsr/en/hypo-685605.json \
        --timing-json preprocessed_flat_seg4/433h_data/segment_timing.json \
        --output-json decode/vsr/en/hypo-685605-merged.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip punctuation)."""
    text = text.lower().strip()
    # Remove common punctuation but keep apostrophes
    text = re.sub(r'[.,!?;:"-]', '', text)
    return text


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher."""
    return SequenceMatcher(None, text1, text2).ratio()


def parse_segment_id(utt_id: str) -> Optional[Dict]:
    """Extract video_id and segment info from utt_id."""
    # Pattern 1: {id}__{hash}_{idx}_{start}_{end}
    pattern1 = r'^(.+?)__([a-f0-9]{8})_(\d{2})_(\d{6})_(\d{6})$'
    match = re.match(pattern1, utt_id)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2),
            'seg_idx': int(match.group(3)),
            'start_frame': int(match.group(4)),
            'end_frame': int(match.group(5)),
            'full_id': f"{match.group(1)}__{match.group(2)}"
        }

    # Pattern 2: {video_name}_{idx}_{start}_{end} (no hash)
    pattern2 = r'^(.+?)_(\d{2})_(\d{6})_(\d{6})$'
    match = re.match(pattern2, utt_id)
    if match:
        video_base = match.group(1)
        return {
            'video_id': video_base,
            'hash': None,
            'seg_idx': int(match.group(2)),
            'start_frame': int(match.group(3)),
            'end_frame': int(match.group(4)),
            'full_id': video_base  # No hash, so full_id is just the video base name
        }

    # Pattern 3: {id}__{hash} (old format without frame info)
    pattern3 = r'^(.+?)__([a-f0-9]{8})$'
    match = re.match(pattern3, utt_id)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2),
            'seg_idx': 0,
            'start_frame': None,
            'end_frame': None,
            'full_id': utt_id
        }

    return None


def group_segments_by_video(decode_data: Dict, timing_data: Dict) -> Dict:
    """Group segments by video ID."""
    video_groups = {}
    
    for idx, utt_id in enumerate(decode_data['utt_id']):
        parsed = parse_segment_id(utt_id)
        if not parsed:
            continue
        
        full_id = parsed['full_id']
        
        if full_id not in video_groups:
            video_groups[full_id] = []
        
        # Get timing info if available
        timing_info = timing_data.get(utt_id, {})
        
        video_groups[full_id].append({
            'utt_id': utt_id,
            'seg_idx': parsed['seg_idx'],
            'start_frame': parsed.get('start_frame') or timing_info.get('start_frame'),
            'end_frame': parsed.get('end_frame') or timing_info.get('end_frame'),
            'start_sec': timing_info.get('start_sec', 0.0),
            'end_sec': timing_info.get('end_sec', 4.0),
            'hypo': decode_data['hypo'][idx],
            'ref': decode_data['ref'][idx],
            'overlaps_with': timing_info.get('overlaps_with', [])
        })
    
    # Sort segments within each video by index
    for full_id in video_groups:
        video_groups[full_id].sort(key=lambda s: s['seg_idx'])
    
    return video_groups


def merge_segment_pair(seg1: Dict, seg2: Dict) -> Tuple[str, Optional[Dict]]:
    """
    Merge two overlapping segments.
    
    Returns:
        (merged_text, conflict_info or None)
    """
    hypo1 = seg1['hypo']
    hypo2 = seg2['hypo']
    
    # Normalize for comparison
    norm1 = normalize_text(hypo1)
    norm2 = normalize_text(hypo2)
    
    # Calculate similarity
    similarity = calculate_similarity(norm1, norm2)
    
    if similarity > 0.85:
        # Agreement: predictions are similar, use first segment
        return hypo1, None
    
    # Disagreement: choose by segment center distance
    # Overlap region is between seg2.start and seg1.end
    overlap_start = seg2['start_sec']
    overlap_end = seg1['end_sec']
    overlap_mid = (overlap_start + overlap_end) / 2
    
    # Calculate segment centers (assuming 4s segments)
    seg1_center = seg1['start_sec'] + 2.0
    seg2_center = seg2['start_sec'] + 2.0
    
    # Choose segment whose center is closer to overlap midpoint
    if abs(seg1_center - overlap_mid) < abs(seg2_center - overlap_mid):
        chosen_text = hypo1
        chosen_source = f"segment_{seg1['seg_idx']}"
        alternate_text = hypo2
        alternate_source = f"segment_{seg2['seg_idx']}"
    else:
        chosen_text = hypo2
        chosen_source = f"segment_{seg2['seg_idx']}"
        alternate_text = hypo1
        alternate_source = f"segment_{seg1['seg_idx']}"
    
    # Create conflict record
    conflict = {
        'overlap_time': [round(overlap_start, 2), round(overlap_end, 2)],
        'chosen_text': chosen_text,
        'chosen_source': chosen_source,
        'alternate_text': alternate_text,
        'alternate_source': alternate_source,
        'similarity': round(similarity, 3)
    }
    
    return chosen_text, conflict


def merge_video_segments(segments: List[Dict]) -> Dict:
    """
    Merge all segments for a video.
    
    Returns:
        {
            'merged_hypo': str,
            'segments_used': List[int],
            'conflicts': List[Dict]
        }
    """
    if len(segments) == 1:
        # Single segment, no merging needed
        return {
            'merged_hypo': segments[0]['hypo'],
            'segments_used': [0],
            'conflicts': [],
            'ref': segments[0]['ref']
        }
    
    # Build merged hypothesis
    merged_parts = []
    conflicts = []
    segments_used = []
    
    for i, seg in enumerate(segments):
        segments_used.append(seg['seg_idx'])

        if i == 0:
            # First segment: take entire hypothesis
            merged_parts.append(seg['hypo'])
        else:
            # Always append new segment (overlaps are already resolved in individual predictions)
            # The segments are sequential and cover the full video
            merged_parts.append(seg['hypo'])

            # Check if this segment overlaps with previous for conflict reporting
            prev_seg = segments[i-1]
            if seg['seg_idx'] in prev_seg['overlaps_with']:
                # Record conflict for reporting purposes
                _, conflict = merge_segment_pair(prev_seg, seg)
                if conflict:
                    conflicts.append(conflict)
    
    # Combine all parts
    final_hypo = ' '.join(merged_parts)
    
    # Get reference (use first segment's ref)
    ref = segments[0]['ref']
    
    return {
        'merged_hypo': final_hypo,
        'segments_used': segments_used,
        'conflicts': conflicts,
        'ref': ref
    }


def merge_all_predictions(decode_json: str, timing_json: str, output_json: str):
    """Main merge function."""
    
    # Load decode output
    try:
        with open(decode_json, 'r') as f:
            decode_data = json.load(f)
        print(f"✓ Loaded decode output: {len(decode_data['utt_id'])} segments")
    except FileNotFoundError:
        print(f"ERROR: Decode JSON not found: {decode_json}")
        return
    
    # Load timing metadata
    try:
        with open(timing_json, 'r') as f:
            timing_data = json.load(f)
        print(f"✓ Loaded timing metadata: {len(timing_data)} segments")
    except FileNotFoundError:
        print(f"WARNING: Timing JSON not found: {timing_json}")
        print("  Proceeding with filename-based timing only...")
        timing_data = {}
    
    # Group by video
    video_groups = group_segments_by_video(decode_data, timing_data)
    print(f"✓ Grouped into {len(video_groups)} videos")
    
    # Merge each video
    merged_results = {}
    total_conflicts = 0
    
    for full_id, segments in video_groups.items():
        result = merge_video_segments(segments)
        merged_results[full_id] = result
        total_conflicts += len(result['conflicts'])
    
    # Write output
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(merged_results, f, indent=2)
    
    print(f"\n✓ Merge complete: {output_json}")
    print(f"  Videos: {len(merged_results)}")
    print(f"  Conflicts detected: {total_conflicts}")
    
    # Summary stats
    videos_with_conflicts = sum(1 for v in merged_results.values() if v['conflicts'])
    if videos_with_conflicts > 0:
        print(f"  Videos with conflicts: {videos_with_conflicts}")
        print(f"\n  NOTE: Review conflicts in output JSON or generate conflict report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge overlapping predictions")
    parser.add_argument("--decode-json", required=True, help="Path to decode output JSON")
    parser.add_argument("--timing-json", required=True, help="Path to segment_timing.json")
    parser.add_argument("--output-json", required=True, help="Path to output merged JSON")
    
    args = parser.parse_args()
    merge_all_predictions(args.decode_json, args.timing_json, args.output_json)
