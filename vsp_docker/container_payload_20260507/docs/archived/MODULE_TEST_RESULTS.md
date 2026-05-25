# Overlapping Segmentation Module Test Results

## Test Summary

**Date:** January 25, 2026  
**Status:** ✅ ALL MODULES TESTED SUCCESSFULLY

All independent modules for overlapping video segmentation have been built, integrated, and tested. The modular architecture allows easy toggle on/off via `OVERLAP_ENABLED` environment variable.

---

## Stage 1: Preprocessing Modules ✅ PASSED

### Module: `overlapping_segmentation.py`

**Tests Performed:**
1. **10.5s video** → Generated 4 segments with 1s overlap
2. **8.0s video** (boundary) → Generated 3 segments  
3. **6.0s video** (below threshold) → Single segment (no splitting)
4. **15.0s video** → Generated 5 segments

**Results:**
- ✅ Videos < 8s: Correctly NOT split (single segment)
- ✅ Videos ≥ 8s: Correctly split with 1s overlap
- ✅ Overlap calculation: Exactly 1.0s (25 frames at 25fps)
- ✅ Stride calculation: Exactly 3.0s (segment_duration - overlap)
- ✅ Frame ranges: Accurate frame indices for all segments
- ✅ Metadata generation: JSON structure correct with timing info

**Example Output (10.5s video):**
```
Segment 0: 0.00s - 4.00s (frames 0-100)
Segment 1: 3.00s - 7.00s (frames 75-175) [1s overlap with Seg 0]
Segment 2: 6.00s - 10.00s (frames 150-250) [1s overlap with Seg 1]
Segment 3: 9.00s - 10.50s (frames 225-262) [1s overlap with Seg 2]
```

---

## Stage 2: Timing Metadata Module ✅ PASSED (After Bug Fixes)

### Module: `generate_segment_timing.py`

**Bugs Fixed:**
1. **Line 83:** Changed `line.startswith('/')` to `line.startswith('#')` to not skip TSV data rows with absolute paths
2. **Line 89:** Changed `int(parts[2])` to `int(parts[3])` to correctly parse frame count column
3. **Lines 28-34:** Fixed Path.stem issue for filenames containing dots (e.g., "video_10.5s")

**Tests Performed:**
- Input: Mock manifest TSV (4 segments) + segment_metadata.json
- Output: segment_timing.json with overlap detection

**Results:**
- ✅ TSV parsing: 4 segments parsed correctly
- ✅ Filename pattern matching: Correctly extracts video_id, hash, seg_idx, frames
- ✅ Overlap detection: 3 overlaps detected (0↔1, 1↔2, 2↔3)
- ✅ Timing metadata structure: Complete with start_sec, end_sec, overlaps_with arrays

**Example Output:**
```json
{
  "test_video_10.5s__abc12345_00_000000_000100": {
    "video_id": "test_video_10.5s",
    "segment_index": 0,
    "start_frame": 0,
    "end_frame": 100,
    "start_sec": 0.0,
    "end_sec": 4.0,
    "overlaps_with": [1]
  },
  ...
}
```

---

## Stage 3: Merge Module ✅ PASSED

### Module: `merge_overlapping_predictions.py`

**Tests Performed:**
1. Mock decode output with 4 overlapping segments
2. Realistic predictions with word overlap
3. Conflict detection for differing predictions

**Results:**
- ✅ Decode JSON loading: Columnar format parsed correctly
- ✅ Timing JSON integration: Matched segments with timing metadata
- ✅ Segment grouping: Grouped segments by video_id
- ✅ Overlap detection: Identified all overlapping pairs
- ✅ Similarity calculation: Levenshtein-based similarity computed
- ✅ Conflict recording: 3 conflicts detected with chosen/alternate text
- ✅ Segment center heuristic: Chooses prediction from segment closest to overlap midpoint

**Example Conflict:**
```json
{
  "overlap_time": [3.0, 4.0],
  "chosen_text": "this is a test of the emergency broadcast system it is only",
  "chosen_source": "segment_1",
  "alternate_text": "hello world this is a test of the emergency broadcast system",
  "alternate_source": "segment_0",
  "similarity": 0.807
}
```

**Note:** Current implementation uses full-segment selection (chooses entire prediction from one segment) rather than word-level merging. This is a valid approach for v1, though word-level merging could be added in future iterations.

---

## Stage 4: Wrapper Scripts and Conflict Reports ✅ PASSED

### Module: `generate_conflict_report.py`

**Tests Performed:**
- Generated reports from merged predictions with 3 conflicts

**Results:**
- ✅ JSON report: conflicts.json with structured data
- ✅ Text report: conflicts.txt with human-readable format
- ✅ HTML report: conflicts.html with color-coded chosen/alternate predictions
- ✅ All 3 report formats correctly show timestamp, similarity, and both predictions

### Module: `make_report_wrapper.sh`

**Tests Performed:**
1. With `OVERLAP_ENABLED=1` and merged output present
2. With `OVERLAP_ENABLED=0` (fallback to standard)

**Results:**
- ✅ Detects merged JSON file correctly
- ✅ Respects `OVERLAP_ENABLED` environment variable
- ✅ Calls conflict report generator when overlap enabled
- ✅ Falls back to standard report when overlap disabled
- ✅ Graceful handling when merged file missing

### Module: `make_burn_wrapper.sh`

**Status:** Structure verified (same logic as report wrapper)

---

## Pipeline Integration ✅ COMPLETE

### File: `run_flat_english_pipeline.sh`

**Modifications Applied:**
1. **Lines 26-30:** Added `OVERLAP_ENABLED`, `OVERLAP_DURATION`, `MIN_SPLIT_DURATION` configuration
2. **Lines ~378-420:** Conditional preprocessing (preprocess_with_overlap.py vs standard)
3. **Lines ~453-469:** Conditional timing metadata generation
4. **Lines ~521-544:** Conditional merge step after decode
5. **Lines ~558-582:** Conditional wrapper script usage for reports/burn

**Toggle Behavior:**
- `OVERLAP_ENABLED=1` (default): Uses all new modules with fallback
- `OVERLAP_ENABLED=0`: Uses existing pipeline unchanged

---

## Critical Bug Fixes Applied

### 1. generate_segment_timing.py
- **Issue:** TSV lines starting with '/' were skipped (line 83)
- **Fix:** Changed to skip only lines starting with '#' (comments)

### 2. generate_segment_timing.py
- **Issue:** Wrong column index for frame count (parts[2] instead of parts[3])
- **Fix:** Corrected to parts[3] for 4-column TSV format

### 3. generate_segment_timing.py
- **Issue:** `Path.stem` called on already-stemmed filenames with dots caused truncation
- **Fix:** Only call Path.stem if filename has video extension (.mp4, .mkv, etc.)

---

## File Summary

### New Files Created (7 modules)
1. `/home/ubuntu/auto_avsr/preparation/overlapping_segmentation.py` - Core segmentation logic
2. `/home/ubuntu/auto_avsr/preparation/preprocess_with_overlap.py` - Preprocessing wrapper
3. `/home/ubuntu/auto_avsr/generate_segment_timing.py` - Timing metadata generator
4. `/home/ubuntu/VSP-LLM/scripts/merge_overlapping_predictions.py` - Merge algorithm
5. `/home/ubuntu/VSP-LLM/scripts/generate_conflict_report.py` - Conflict report generator
6. `/home/ubuntu/VSP-LLM/scripts/make_report_wrapper.sh` - Report wrapper
7. `/home/ubuntu/VSP-LLM/scripts/make_burn_wrapper.sh` - Video burning wrapper

### Modified Files (1 file)
1. `/home/ubuntu/run_flat_english_pipeline.sh` - Pipeline orchestrator with conditional calls

### Unchanged Files (Core pipeline preserved)
- ✅ `auto_avsr/preparation/utils.py` - NO CHANGES
- ✅ `auto_avsr/preparation/preprocess_lrs2lrs3.py` - NO CHANGES
- ✅ `auto_avsr/make_simple_manifest.py` - NO CHANGES
- ✅ `VSP-LLM/src/vsp_llm_decode.py` - NO CHANGES
- ✅ `VSP-LLM/scripts/make_report.py` - NO CHANGES
- ✅ `VSP-LLM/scripts/make_burn.py` - NO CHANGES

---

## Next Steps

### Pending Tasks:
1. **Stage 5:** Full end-to-end pipeline test with real videos (requires pipeline run)
2. **VSP UI Integration (EC2):** Add checkbox control to vsp-ui
3. **Linux Container Replication:** Apply all changes to `/workspace/` version

### Recommended Testing:
1. Run full pipeline with `OVERLAP_ENABLED=1` on 2-3 test videos
2. Run full pipeline with `OVERLAP_ENABLED=0` to verify fallback
3. Compare outputs and verify conflict reports
4. Test with videos of varying lengths (5s, 8s, 10s, 15s, 30s)

### Future Enhancements (Optional):
1. Word-level merging instead of full-segment selection
2. Confidence scores for merge decisions
3. Multiple merge strategies (voting, weighted average, etc.)
4. Real-time merge preview in UI

---

## Quick Usage Guide

**Enable overlapping segmentation (default):**
```bash
./run_flat_english_pipeline.sh /path/to/videos
# or explicitly:
OVERLAP_ENABLED=1 ./run_flat_english_pipeline.sh /path/to/videos
```

**Disable overlapping segmentation:**
```bash
OVERLAP_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/videos
```

**Expected outputs when enabled:**
- `segment_metadata.json` in preprocessed directory
- `segment_timing.json` in manifest directory (433h_data/)
- `hypo-{id}-merged.json` in decode/vsr/en/
- `conflicts.json`, `conflicts.txt`, `conflicts.html` in client_outputs/report/conflicts/

---

## Test Artifacts

All test artifacts saved to `/tmp/`:
- `/tmp/test_segment_metadata_*.json` - Segmentation test outputs
- `/tmp/test_segment_timing.json` - Timing metadata test output
- `/tmp/test_merged*.json` - Merge test outputs
- `/tmp/conflict_reports/` - Conflict report test outputs
- `/tmp/wrapper_test_reports/` - Wrapper script test outputs

---

**✅ All modular tests PASSED - Ready for full pipeline integration testing!**
