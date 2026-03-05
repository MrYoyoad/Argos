# Original Video Serving for Manual Transcription

## Change Summary

**Date**: 2026-01-27
**Issue**: Users need to see the original full-frame video (not mouth-cropped) when manually transcribing segments
**Status**: IMPLEMENTED ✓

## Problem

When the preprocessing-only mode completes and users are presented with the transcription screen, the video players were showing the mouth-cropped videos from:
```
~/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s/*.mp4
```

These are 88x88 pixel mouth crops, making it difficult to:
- Understand the context of what's being said
- See speaker identity
- Read lips in the full face context
- Make accurate transcription decisions

## Solution

Modified the segment video serving API to dynamically extract clips from the **original full-frame videos** using the segment timing metadata.

### Implementation

**Files Modified**:
1. `/home/ubuntu/vsp-ui/app/server.py` - Updated `handle_get_segment_video()`
2. `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/server.py` - Same changes for Linux container

**How It Works**:

1. **Parse Segment ID**: Extract video name and segment index from segment ID
   ```
   Example: 050111_OsamaBinLadenStatement_HD_2m30s_1min_00_000000_000300
   Video: 050111_OsamaBinLadenStatement_HD_2m30s_1min
   Index: 0
   ```

2. **Load Metadata**: Read `segment_metadata.json` to get timing information
   ```json
   {
     "050111_OsamaBinLadenStatement_HD_2m30s_1min": {
       "segments": [
         {
           "index": 0,
           "start_sec": 0.0,
           "end_sec": 12.0,
           "duration": 12.0
         }
       ]
     }
   }
   ```

3. **Extract Segment**: Use ffmpeg to extract the clip from original video
   ```bash
   ffmpeg -ss 0.0 -i original.mp4 -t 12.0 -c copy output.mp4
   ```

4. **Serve Video**: Stream the extracted segment to the browser

### Benefits

✅ **Full context**: Users see the complete video frame
✅ **Better quality**: Original resolution and encoding
✅ **Audio preserved**: Full audio track included
✅ **Fast extraction**: Uses codec copy (no re-encoding) when possible
✅ **No storage overhead**: Clips generated on-demand, not pre-stored

## Technical Details

### API Endpoint

**GET** `/api/segment-video/<segment_id>`

**Behavior**:
- Old: Served preprocessed mouth-cropped MP4 file directly
- New: Extracts clip from original video using ffmpeg

**Performance**:
- Codec copy mode: ~1-2 seconds per segment
- Re-encode fallback: ~3-5 seconds per segment
- Clips cached temporarily, cleaned up after serving

### FFmpeg Command

**Primary (fast, no re-encode)**:
```bash
ffmpeg -y \
  -ss <start_time> \
  -i <original_video> \
  -t <duration> \
  -c copy \
  -avoid_negative_ts make_zero \
  <output>
```

**Fallback (if codec copy fails)**:
```bash
ffmpeg -y \
  -ss <start_time> \
  -i <original_video> \
  -t <duration> \
  -c:v libx264 \
  -c:a aac \
  -preset ultrafast \
  <output>
```

### File Locations

- **Original videos**: `~/auto_avsr/flat/*.mp4`
- **Segment metadata**: `~/auto_avsr/preprocessed_flat_seg12/segment_metadata.json`
- **Mouth crops** (not used): `~/auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s/*.mp4`

## Testing

All tests pass (5/5):
- ✓ Segment ID parsing
- ✓ Metadata loading
- ✓ Original video files exist
- ✓ Preprocessed segments exist
- ✓ FFmpeg extraction works

**Test script**: `/tmp/test_original_video_serving.py`

## User Experience

### Before
```
[88x88 mouth crop video]
Transcription: [hard to understand context]
```

### After
```
[Full-frame original video with audio]
Transcription: [clear context, easy to understand]
```

## Deployment

**EC2 Instance**: ✓ Updated
**Linux Container**: ✓ Updated

Both environments now serve original videos for manual transcription.

## Related Documentation

- [PREPROCESSING_ONLY_FIX_SUMMARY.md](PREPROCESSING_ONLY_FIX_SUMMARY.md) - UI transition fix
- [MANUAL_TRANSCRIPTION.md](MANUAL_TRANSCRIPTION.md) - Manual transcription workflow
- [CLAUDE.md](CLAUDE.md) - Full pipeline architecture

## Security Considerations

- ✓ Path traversal protection maintained
- ✓ Segment ID validation before parsing
- ✓ Temporary files cleaned up after serving
- ✓ FFmpeg timeout prevents hanging (30s max)

## Future Improvements

Potential enhancements:
1. **Caching**: Cache extracted segments to avoid re-extraction on page refresh
2. **Streaming**: Use HTTP range requests for partial content delivery
3. **Preview thumbnails**: Generate thumbnail images for quick preview
4. **Multiple resolutions**: Offer different quality levels for bandwidth constraints

---

**Implementation Status**: COMPLETE ✓
**Testing Status**: ALL TESTS PASS ✓
**Deployment Status**: SYNCED TO BOTH ENVIRONMENTS ✓
