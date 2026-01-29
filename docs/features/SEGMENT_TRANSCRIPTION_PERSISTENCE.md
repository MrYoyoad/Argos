# Segment Transcription Persistence

## Change Summary

**Date**: 2026-01-27
**Issue**: Segment transcriptions (manual or auto) don't persist across pipeline runs
**Status**: FIXED ✓

## The Problem

The VSP pipeline has **two levels of transcriptions**:

### 1. Whole Video Transcriptions (Already Persistent)
- Location: `~/vsp_input/.transcriptions/*.wrd`
- One file per original video
- Persists across runs ✓
- Used by Whisper to skip re-transcription

### 2. Segment Transcriptions (Were Being Archived)
- Location: `~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/*.txt`
- One file per 12-second segment
- **Were getting archived on each run** ✗
- Used by pipeline for training/decoding

## The Issue

When you have a long video split into segments:

**Before Fix**:
1. You manually transcribe all segments → saved in `flat_text_seg12s/`
2. Pipeline completes → creates whole video .wrd → saved to `.transcriptions/`
3. **Next run** → whole video .wrd exists, so Whisper skips
4. **BUT** segments get re-preprocessed → segment transcriptions were archived!
5. **Result**: You have to manually transcribe all segments AGAIN 😞

**Why This Happened**:
- The entire `preprocessed_flat_seg${SEG_DURATION}/` folder was archived
- This included `flat/flat_text_seg12s/` with all segment transcriptions
- On next run, preprocessing creates new segments but no transcriptions

## The Solution

Modified the archiving logic to **preserve segment transcription folders** across runs:

### What Changed

**File**: `run_flat_english_pipeline.sh` (lines 67-126)

**Before**:
```bash
TO_ARCHIVE=(
  "${PREP_ROOT}"  # Everything archived including segment transcriptions
  ...
)
```

**After**:
```bash
TO_ARCHIVE=(
  # "${PREP_ROOT}"  # Handled specially below
  ...
)

# Archive PREP_ROOT but preserve flat_text_seg* folders
if [[ -e "${PREP_ROOT}" ]]; then
  # Archive everything except flat/flat_text_seg*
  # Segment transcriptions are preserved!
fi
```

### How It Works

**Selective Archiving**:
1. Archive all preprocessing outputs (mouth crops, video segments, etc.)
2. **Skip** folders matching `flat_text_seg*s` pattern
3. These folders persist in place across runs
4. On next run, matching segments reuse existing transcriptions

**Folder Preserved**:
```
~/auto_avsr/preprocessed_flat_seg12/flat/
  ├── flat_text_seg12s/          ← PRESERVED across runs!
  │   ├── VideoA_00_*.txt
  │   ├── VideoA_01_*.txt
  │   └── ...
  ├── flat_video_seg12s/         ← Archived each run
  └── segment_metadata.json       ← Archived each run
```

## Benefits

### ✅ Manual Transcriptions Persist
- Transcribe segments once
- Transcriptions reused on all future runs
- No need to re-transcribe!

### ✅ Auto Transcriptions Persist
- If Whisper transcribes segments, those persist too
- Faster subsequent runs (no re-transcription needed)

### ✅ Smart Matching by Segment ID
- Segment IDs include video name: `VideoName_SegIdx_StartFrame_EndFrame`
- Different videos won't conflict
- Same video with same segmentation reuses transcriptions

### ✅ Safe for Mixed Workflows
- Remove video A, add video B: Video A's segments stay (harmless)
- Re-add video A later: Its segment transcriptions are still there!
- Change segment duration: Old segments don't match, new ones created

## Use Cases

### Use Case 1: Manual Transcription Workflow
```
Run 1:
1. Enable preprocessing-only mode
2. Manually transcribe all 6 segments
3. Continue pipeline → creates whole video .wrd

Run 2 (same video):
1. Whole video .wrd reused (Whisper skips)
2. Segments reprocessed
3. Segment transcriptions REUSED ✓
4. No manual work needed!
```

### Use Case 2: Whisper + Correction Workflow
```
Run 1:
1. Let Whisper auto-transcribe segments
2. Review and correct some segment transcriptions
3. Continue pipeline

Run 2 (same video):
1. Corrected segment transcriptions REUSED ✓
2. No re-transcription or correction needed!
```

### Use Case 3: Iterative Improvements
```
Run 1: Transcribe first 3 segments, test pipeline
Run 2: Transcribe next 3 segments
Run 3: All 6 segments have transcriptions ✓
```

## What Gets Preserved vs Archived

| Item | Location | Behavior |
|------|----------|----------|
| **Whole video transcriptions** | `~/vsp_input/.transcriptions/` | ✅ **Preserved** |
| **Segment transcriptions** | `preprocessed_flat_seg12/flat/flat_text_seg*s/` | ✅ **Preserved** (NEW!) |
| Mouth-cropped segments | `preprocessed_flat_seg12/flat/flat_video_seg*s/` | ❌ Archived |
| Segment metadata | `preprocessed_flat_seg12/segment_metadata.json` | ❌ Archived |
| K-means features | `flat_features/` | ❌ Archived |
| K-means labels | `flat_labels/` | ❌ Archived |

## Edge Cases Handled

### Different Segment Duration
```
Run 1: SEG_DURATION=12 → transcriptions in flat_text_seg12s/
Run 2: SEG_DURATION=16 → transcriptions in flat_text_seg16s/
Result: No conflict, both preserved ✓
```

### Video Name Changes
```
Run 1: video.mp4 → segments: video_00_*.txt, video_01_*.txt
Run 2: renamed_video.mp4 → segments: renamed_video_00_*.txt
Result: Old transcriptions kept, new ones created ✓
```

### Removed Videos
```
Run 1: Process VideoA → transcriptions created
Run 2: Remove VideoA, add VideoB
Result: VideoA transcriptions remain (harmless) ✓
Run 3: Re-add VideoA
Result: VideoA transcriptions still there, reused! ✓
```

## Files Modified

**EC2 Instance**:
- `/home/ubuntu/run_flat_english_pipeline.sh` (lines 67-126)

**Linux Container**:
- `/home/ubuntu/vsp_docker/galaxy_export/run_flat_english_pipeline.sh` (lines 67-126)

## Testing

To verify:
```bash
# Run 1: Create segment transcriptions
./run_flat_english_pipeline.sh ~/vsp_input

# Check transcriptions exist
ls ~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/*.txt

# Run 2: Run again
./run_flat_english_pipeline.sh ~/vsp_input

# Verify transcriptions still exist (not archived)
ls ~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/*.txt
```

## Deployment Status

✅ **EC2 Instance**: Updated
✅ **Linux Container**: Updated
✅ **Both Environments Synced**: Yes

## Related Documentation

- [ORIGINAL_VIDEO_SERVING.md](ORIGINAL_VIDEO_SERVING.md) - Original video clips for transcription
- [PREPROCESSING_ONLY_FIX_SUMMARY.md](PREPROCESSING_ONLY_FIX_SUMMARY.md) - Manual transcription UI
- [CLAUDE.md](CLAUDE.md) - Full pipeline architecture

---

**Bottom Line**: Segment transcriptions now persist across runs, just like whole video transcriptions. No need to re-transcribe the same segments multiple times!
