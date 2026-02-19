# Segmented Video Naming Fix for Non-Split Videos

**Date**: February 1, 2026
**Issue**: Videos too short for splitting get artificial segment suffixes, breaking transcription matching
**Status**: Fixed in EC2, pending Linux container update

## Problem Description

When segmentation is enabled in the pipeline, videos that are too short to be split (under 24 seconds) were getting renamed with artificial segment-like suffixes. This broke transcription matching because:

1. User transcribes the video with the segment-suffixed name
2. ASR/pipeline expects the original name without suffix
3. Result: Manual transcriptions are ignored, Whisper re-transcribes unnecessarily

### Example Scenario

**Before Fix**:
```
Input video: 00008.mp4 (20 seconds - below 24s minimum)

Pipeline flow:
1. preprocess_with_overlap.py processes video
2. Video too short to split → creates single segment
3. BUT still adds segment suffix: 00008_00_000000_000500.mp4
4. User sees this in UI and creates transcription: 00008_00_000000_000500.wrd
5. ASR step looks for: 00008.wrd (original name)
6. No match found → Whisper re-transcribes the video
```

**After Fix**:
```
Input video: 00008.mp4 (20 seconds)

Pipeline flow:
1. preprocess_with_overlap.py processes video
2. Video too short to split → creates single segment
3. Keeps original name: 00008.mp4 (no suffix added)
4. User sees this in UI and creates transcription: 00008.wrd
5. ASR step looks for: 00008.wrd
6. Match found → Whisper skips this video, uses manual transcription
```

## Root Cause

In `/home/ubuntu/auto_avsr/preparation/preprocess_with_overlap.py`, the segment naming logic (lines 229-236) always added a segment suffix regardless of whether the video was actually split:

```python
# OLD CODE (always added suffix):
segment_suffix = f"_{idx:02d}_{start_frame:06d}_{end_frame:06d}"
dst_vid_filename = os.path.join(dst_vid_dir, base_name + segment_suffix + ".mp4")
dst_txt_filename = os.path.join(dst_txt_dir, base_name + segment_suffix + ".txt")
```

This happened even when `len(time_segments) == 1`, meaning the video wasn't split at all.

## The Fix

Modified the naming logic to check if the video was actually split before adding the segment suffix:

```python
# NEW CODE (conditional suffix):
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
```

## Files Modified

### EC2 Version (COMPLETED)
- **File**: `/home/ubuntu/auto_avsr/preparation/preprocess_with_overlap.py`
- **Lines**: ~229-240
- **Change**: Added conditional logic to only add suffix for multi-segment videos

### Linux Container Version (PENDING)
- **File**: `/workspace/auto_avsr/preparation/preprocess_with_overlap.py`
- **Lines**: ~229-240
- **Change**: Same as EC2 version

## Testing

Test with videos of varying lengths:

1. **Short video (< 24s)**: Should keep original name, no suffix
2. **Long video (> 24s)**: Should split into segments with suffixes

### Example Test

```bash
# Test with a 20-second video
cp test_video_20s.mp4 ~/vsp_input/

# Run pipeline with segmentation enabled
SEGMENTATION_ENABLED=1 ./run_flat_english_pipeline.sh ~/vsp_input/

# Check output - should NOT have segment suffix
ls ~/auto_avsr/preprocessed_flat_seg12s/flat/flat_video_seg12s/
# Expected: test_video_20s.mp4 (NO suffix)
# Before fix: test_video_20s_00_000000_000500.mp4 (unwanted suffix)
```

## Benefits

1. **Conceptually Correct**: Non-split videos keep original names, split videos have segment IDs
2. **Simple Transcription Matching**: Original name matches transcription file name
3. **No Special Cases**: ASR doesn't need special logic to handle artificial suffixes
4. **User Clarity**: Users see meaningful filenames without confusing segment markers

## Impact

- Fixes transcription matching for all videos under 24 seconds when segmentation is enabled
- Ensures manual transcriptions are properly used by the pipeline
- Reduces unnecessary Whisper processing time

## Related Issues

This fix complements:
- **Item 15**: Non-Segmented Video Naming Fix (for SEGMENT_ONLY mode)
- **Item 9**: Segment Transcription Persistence (Steps 0.6 and 1.5)

Together, these fixes ensure transcriptions work correctly in all pipeline modes.
