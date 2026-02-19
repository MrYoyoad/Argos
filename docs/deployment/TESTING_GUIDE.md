# Testing Guide

**Package**: vsp_linux_container_FINAL v1.0.0
**Date**: February 3, 2026

Comprehensive testing procedures to verify all fixes are working correctly.

---

## Quick Reference

| Test Level | Time | Command |
|------------|------|---------|
| **Verification** | 10s | `bash VERIFY.sh` |
| **Module Tests** | 30s | `bash lib/test_all_modules.sh` |
| **Smoke Test** | 5 min | `SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/short_video.mp4` |
| **Full Pipeline** | 30+ min | `./run_flat_english_pipeline.sh /path/to/long_video.mp4` |

---

## Level 1: Fix Verification

**Purpose**: Verify all 12 fixes are present in the codebase
**Time**: ~10 seconds
**When**: After installation, before running pipeline

### Run Verification Script

```bash
cd /host/galaxy_export
bash /path/to/vsp_linux_container_FINAL/VERIFY.sh
```

### Expected Output

```
========================================
VSP Linux Container Fix Verification
========================================

Checking all 12 critical fixes...

✅ Fix  1: Cython auto-build (lib/decode.sh)
✅ Fix  2: max_len config (VSP-LLM/src/conf/s2s_decode.yaml)
✅ Fix  3: Dynamic transcription paths (lib/asr.sh)
✅ Fix  4: VSP_INPUT_DIR support (vsp-ui/app/config.py)
✅ Fix  5: Absolute imports (vsp-ui/app/services/transcription_manager.py)
✅ Fix  6: log_info stderr redirect (lib/common.sh)
✅ Fix  7: POST_ROOT definition (run_flat_english_pipeline.sh)
✅ Fix  8: Step 2.5 metadata creation (run_flat_english_pipeline.sh)
✅ Fix  9: Non-segmented naming (run_flat_english_pipeline.sh)
✅ Fix 10: make_burn segment matching (VSP-LLM/scripts/make_burn.py)
✅ Fix 11: Logger duplication fix (VSP-LLM/src/vsp_llm_decode.py)
✅ Fix 12: Segment duration = 12s (vsp-ui/app/config.py)

Running module tests...
✅ Module tests: 37/37 PASSED

========================================
All fixes verified successfully! ✅
========================================
```

### If Verification Fails

Check which specific fix is missing and reinstall:

```bash
# Example: Fix #2 missing
cp vsp_linux_container_FINAL/VSP-LLM/src/conf/s2s_decode.yaml \
   /host/galaxy_export/VSP-LLM/src/conf/

# Re-run verification
bash VERIFY.sh
```

---

## Level 2: Module Tests

**Purpose**: Test all 11 pipeline modules independently
**Time**: ~30 seconds
**When**: After installing lib/ directory

### Run Module Test Suite

```bash
cd /host/galaxy_export
bash lib/test_all_modules.sh
```

### Expected Output

```
==================================================
Testing All Pipeline Modules
==================================================

[1/11] Testing common.sh...
  ✅ log_info outputs to stderr
  ✅ log_error outputs to stderr
  ✅ log_warn outputs to stderr
  ✅ validate_directory works correctly

[2/11] Testing config.sh...
  ✅ Environment detection works
  ✅ Path derivation correct

[3/11] Testing archive.sh...
  ✅ Archive previous run works
  ✅ Transcription preservation works

... (8 more modules)

==================================================
Module Tests Complete: 37/37 PASSED ✅
==================================================
```

### If Module Tests Fail

1. Check which module failed
2. Read error message carefully
3. Common issues:
   - Missing dependencies (python3, ffmpeg, etc.)
   - Wrong directory (must run from /host/galaxy_export)
   - File permissions

**Fix and re-test**:
```bash
# Re-install specific module
cp vsp_linux_container_FINAL/lib/failing_module.sh /host/galaxy_export/lib/

# Re-run tests
bash lib/test_all_modules.sh
```

---

## Level 3: Smoke Test (Quick Pipeline Test)

**Purpose**: End-to-end test with minimal processing time
**Time**: ~5 minutes
**When**: Before processing actual videos

### Prerequisites

- Short video file (<24 seconds)
- GPU available
- All fixes verified

### Run Smoke Test

```bash
cd /host/galaxy_export

# Test with non-segmented video
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test_video.mp4
```

### What to Look For

**1. Cython Extension Build (Fix #1)**
```
>>> [7] Running VSP-LLM decode
[HH:MM:SS] INFO: Checking fairseq Cython extensions
[HH:MM:SS] INFO: Fairseq Cython extensions not found - building now (one-time setup)
... (build output for ~30 seconds)
[HH:MM:SS] INFO: Fairseq Cython extensions built successfully
```

✅ **Expected**: Builds on first run, skips on subsequent runs
❌ **Error**: `ImportError: Please build Cython components` → Fix #1 not applied

**2. Decode Completion (Fix #2)**
```
>>> [7] Running VSP-LLM decode
... (decode processing)
>>> Pipeline complete!
```

✅ **Expected**: Decode completes without errors
❌ **Error**: `ValueError: max_new_tokens must be greater than 0` → Fix #2 not applied

**3. Transcription Persistence (Fix #3)**
```bash
# Check transcription was saved
ls /path/to/videos/.transcriptions/
# Should show: test_video.wrd

# Run again
./run_flat_english_pipeline.sh /path/to/test_video.mp4
# Should show: >>> [0.6] Copied 1 existing transcription(s)
```

✅ **Expected**: Transcription survives pipeline reruns
❌ **Error**: "No .transcriptions directory found" → Fix #3 not applied

**4. Client Outputs Generated (Fix #6, #7)**
```bash
# Check outputs were created
ls flat_runs_archive/*/client_outputs/
# Should show: report/ and burned_videos/
```

✅ **Expected**: Both directories exist with files
❌ **Error**: Empty directories or missing → Fix #6 or #7 not applied

**5. Burned Video Quality (Fix #8, #9, #10)**
```bash
# Check burned video resolution
ffprobe flat_runs_archive/*/client_outputs/burned_videos/*.mp4 2>&1 | grep Stream
# Should show: Video: h264, ..., 224x224 (NOT 88x88)
```

✅ **Expected**: 224x224 full-frame video
❌ **Error**: 88x88 mouth crop → Fix #8, #9, or #10 not applied

**6. No Duplicate Logs (Fix #11)**
```bash
# Check decode logs
tail -100 flat_runs_archive/*/vsp_llm_decode.log | grep "INST:"
# Each segment should appear ONCE, not twice
```

✅ **Expected**: Each INST/REF/HYP appears once
❌ **Error**: Duplicate entries → Fix #11 not applied

---

## Level 4: Full Pipeline Test

**Purpose**: Complete end-to-end test with actual workload
**Time**: 30+ minutes (depends on video length)
**When**: Before production use

### Test Scenario 1: Long Video (Segmented)

**Video**: 60-second clip (or longer)

```bash
cd /host/galaxy_export
./run_flat_english_pipeline.sh /path/to/long_video.mp4
```

### Expected Behavior

**1. Segment-First Normalization (Architecture Change)**
```
>>> [0.1] Fast Segmentation
Creating segments: 6 segments from 1 video(s)
... (fast codec copy, ~5 seconds)

>>> [0.5] Video Normalization
Normalizing 6 pre-segmented videos
... (normalizes segments, not whole video)

>>> [2] Running preprocess_lrs2lrs3.py
... (mouth cropping only, no re-segmentation)
```

✅ **Expected**: Step 0.1 creates segments, Step 0.5 normalizes segments
❌ **Error**: Normalizing whole videos → Architecture change not applied

**2. Segmentation (Fix #12)**
```
# Check segment count
ls auto_avsr/preprocessed_flat_seg12/flat/flat_video_seg12s/*.mp4 | wc -l
# 60s video should create 6 segments (12s each with 2s overlap)
```

✅ **Expected**: 6 segments for 60s video (12s duration)
❌ **Error**: 15 segments for 60s video (4s duration) → Fix #12 not applied

**3. Transcription Persistence (Steps 0.6, 1.5)**
```
# First run
# (Whisper transcribes all segments)

# Second run
./run_flat_english_pipeline.sh /path/to/long_video.mp4

# Check logs
grep ">>> \[0.6\]" flat_runs_archive/*/run.log
# Should show: >>> [0.6] Copied 6 existing transcription(s)

grep ">>> \[3\]" flat_runs_archive/*/run.log
# Should show Whisper skipped all segments (fast completion)
```

✅ **Expected**: Second run reuses all transcriptions (90%+ time savings)
❌ **Error**: Re-transcribing every run → Steps 0.6/1.5 not working

**4. Client Outputs**
```bash
# Check final outputs
ls flat_runs_archive/*/client_outputs/report/
# Should show: JSON report with all segment transcriptions

ls flat_runs_archive/*/client_outputs/burned_videos/
# Should show: 6 burned video files (one per segment)
```

✅ **Expected**: All outputs generated correctly
❌ **Error**: Missing files → Various fixes not applied

---

### Test Scenario 2: Short Video (Non-Segmented)

**Video**: 15-second clip (< 24 seconds)

```bash
cd /host/galaxy_export
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/short_video.mp4
```

### Expected Behavior

**1. Non-Segmented Naming (Fix #9)**
```bash
# Check filename in preprocessed directory
ls auto_avsr/flat/
# Should show: short_video.mp4 (NOT short_video_00_000000_999999.mp4)
```

✅ **Expected**: Original filename preserved
❌ **Error**: Artificial `_00_000000_999999` suffix → Fix #9 not applied

**2. Step 2.5 Metadata Creation (Fix #8)**
```bash
# Check metadata file
cat auto_avsr/preprocessed_flat_seg12/segment_metadata.json
# Should show proper structure with timing info
```

✅ **Expected**: JSON with segment timing information
❌ **Error**: Empty or missing metadata → Fix #8 not applied

**3. Burned Video Quality (Fix #10)**
```bash
# Check burned video resolution
ffprobe flat_runs_archive/*/client_outputs/burned_videos/*.mp4 2>&1 | grep Stream
# Should show: 224x224 full-frame (NOT 88x88 mouth crop)
```

✅ **Expected**: 224x224 full-frame video
❌ **Error**: 88x88 mouth crop → Fix #10 not applied

---

## Level 5: UI Testing

**Purpose**: Verify all UI features work correctly
**Time**: 10 minutes
**When**: Before using UI for production

### Start UI Server

```bash
cd /host/galaxy_export/vsp-ui
python3 app/server.py
# Should start without import errors
```

✅ **Expected**: Server starts on port 8765
❌ **Error**: `ImportError: Attempted relative import` → Fix #5 not applied

### Test UI Features

**1. Video Scanning (Fix #4)**
```
1. Open browser: http://localhost:8765
2. Click "Scan Videos"
3. Check that videos are detected
```

✅ **Expected**: Videos listed with correct paths
❌ **Error**: No videos found → Fix #4 not applied (VSP_INPUT_DIR)

**2. Transcription Management**
```
1. Click "Add Transcription" on any video
2. Enter text: "this is a test transcription"
3. Save
4. Verify badge shows [MANUAL]
5. Run pipeline
6. Verify Whisper skipped the video
```

✅ **Expected**: Manual transcription used, Whisper skipped
❌ **Error**: Whisper re-transcribed → Transcription persistence not working

**3. Video Exclusion**
```
1. Click "Remove" on a video
2. Verify video moved to .excluded/ folder
3. Scan videos again
4. Verify video no longer in list
```

✅ **Expected**: Video excluded but not deleted
❌ **Error**: Video deleted permanently → Video exclusion feature missing

**4. K-means Toggle**
```
1. Add videos and click "Start Processing"
2. Check "Skip k-means training" checkbox
3. Start pipeline
4. Verify logs show: TRAIN_KMEANS=0
```

✅ **Expected**: K-means training skipped
❌ **Error**: K-means trains anyway → K-means toggle not working

**5. Segment Review (Fix #12)**
```
1. After processing, click "Review Segments"
2. Check segment duration in filenames
3. Should show: _00_000000_000300 (12s = 300 frames @ 25fps)
```

✅ **Expected**: 12-second segments
❌ **Error**: 4-second segments (_00_000000_000100) → Fix #12 not applied

---

## Performance Benchmarks

### Expected Processing Times

**Short Video (20s, non-segmented)**:
- Step 0.1 (Segmentation): ~2s
- Step 0.5 (Normalization): ~5s
- Step 2 (Mouth Cropping): ~30s
- Step 3 (ASR): ~20s (first run) OR ~2s (with cached transcription)
- Step 6 (K-means): ~5min (if training) OR ~1s (if skipped)
- Step 7 (Decode): ~1min
- Step 8 (Outputs): ~15s
- **Total**: ~7min (first run) OR ~2min (cached + skip k-means)

**Long Video (60s, segmented)**:
- Step 0.1 (Segmentation): ~5s
- Step 0.5 (Normalization): ~15s (6 segments)
- Step 2 (Mouth Cropping): ~2min
- Step 3 (ASR): ~2min (first run) OR ~5s (cached)
- Step 6 (K-means): ~10min (if training) OR ~1s (skipped)
- Step 7 (Decode): ~5min
- Step 8 (Outputs): ~1min
- **Total**: ~20min (first run) OR ~8min (cached + skip k-means)

### Performance Improvements

**With All Fixes Applied**:
- ✅ Segment-first normalization: 50% faster for long videos
- ✅ Transcription persistence: 90%+ time savings on reruns
- ✅ K-means toggle: Skip 5-10min if model exists
- ✅ Cython auto-build: One-time 30s cost, then instant

**Comparison**:
```
Before fixes: 60s video = ~30min per run
After fixes:  60s video = ~20min first run, ~8min subsequent runs
Savings:      ~60% time reduction on reruns
```

---

## Troubleshooting Test Failures

### Cython Build Fails (Fix #1)

**Error**: `Failed to build fairseq Cython extensions`

**Diagnosis**:
```bash
cd /host/galaxy_export/VSP-LLM/fairseq
python3 setup.py build_ext --inplace
# Check error output
```

**Common Causes**:
- Missing gcc/g++ compiler
- Python development headers not installed
- CUDA version mismatch

**Solution**:
```bash
# Install build dependencies
apt-get update && apt-get install -y build-essential python3-dev
```

### max_new_tokens Error (Fix #2)

**Error**: `ValueError: max_new_tokens must be greater than 0`

**Diagnosis**:
```bash
grep "max_len:" /host/galaxy_export/VSP-LLM/src/conf/s2s_decode.yaml
# Should show: max_len: 2048
```

**Solution**:
```bash
# Reinstall config file
cp vsp_linux_container_FINAL/VSP-LLM/src/conf/s2s_decode.yaml \
   /host/galaxy_export/VSP-LLM/src/conf/
```

### Transcriptions Not Persisting (Fix #3)

**Error**: Whisper re-transcribes every run

**Diagnosis**:
```bash
# Check ASR module
grep 'transcriptions_dir="${raw_dir}/.transcriptions"' /host/galaxy_export/lib/asr.sh
# Should be present

# Check pipeline passes RAW_DIR
grep 'run_asr_transcription.*RAW_DIR' /host/galaxy_export/run_flat_english_pipeline.sh
# Should show: ..."$RAW_DIR"...
```

**Solution**:
```bash
# Reinstall ASR module and pipeline
cp vsp_linux_container_FINAL/lib/asr.sh /host/galaxy_export/lib/
cp vsp_linux_container_FINAL/run_flat_english_pipeline.sh /host/galaxy_export/
```

---

## Testing Checklist

After installation, verify:

### Critical Fixes
- [ ] Fix #1: Cython builds automatically (first run only)
- [ ] Fix #2: Decode completes without max_len error
- [ ] Fix #3: Transcriptions persist in `.transcriptions/`
- [ ] Fix #4: UI recognizes input directory
- [ ] Fix #5: UI starts without import errors
- [ ] Fix #6: Client outputs generate correctly
- [ ] Fix #7: Pipeline completes with exit code 0
- [ ] Fix #8: Burned videos use full-frame (not mouth crops)
- [ ] Fix #9: Non-segmented videos keep original names
- [ ] Fix #10: make_burn handles whole videos correctly
- [ ] Fix #11: No duplicate logs in decode output
- [ ] Fix #12: Segments are 12s (not 4s)

### Architecture
- [ ] Step 0.1 always runs (fast segmentation)
- [ ] Step 0.5 normalizes segments (not whole videos)
- [ ] Step 2 only does mouth cropping (no re-segmentation)
- [ ] Steps 0.6 and 1.5 manage transcriptions

### UI Features
- [ ] Transcription modal works
- [ ] Video exclusion works
- [ ] K-means toggle works
- [ ] Segment review shows correct durations
- [ ] Upload progress shows smooth animation

### Performance
- [ ] Second run is 60%+ faster (cached transcriptions)
- [ ] Long videos process efficiently (segment-first)
- [ ] K-means skip saves 5-10 minutes

---

**Document Version**: 1.0.0
**Last Updated**: February 3, 2026
