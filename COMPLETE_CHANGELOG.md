# Complete Changelog - All Sessions

**Final Package Version**: 1.0.0
**Date**: February 3, 2026
**Total Fixes**: 12 critical bug fixes + 1 architectural change + 7 UI features

This document provides a comprehensive history of ALL fixes across all development sessions, consolidated into this final deployment package.

---

## Table of Contents

1. [Critical Bug Fixes (12)](#critical-bug-fixes)
2. [Architectural Changes (1)](#architectural-changes)
3. [UI Features (7)](#ui-features)
4. [Session History](#session-history)
5. [Testing & Verification](#testing--verification)

---

## Critical Bug Fixes

### 1. Cython Extension Auto-Build (Fix #1)
**Date**: February 2, 2026
**Problem**: Container decode step failing with:
```
ImportError: Please build Cython components with: `python setup.py build_ext --inplace`
```

**Root Cause**: Fairseq Cython extensions need compilation for specific Python/CPU architecture. Container environment differs from build environment.

**Solution**: Added automatic check and build to `lib/decode.sh`

**File**: `lib/decode.sh` lines 35-52

**Code**:
```bash
# CRITICAL: Check and build fairseq Cython extensions if needed
log_info "Checking fairseq Cython extensions"
if ! python3 -c "from fairseq.data.data_utils_fast import batch_by_size_vec" 2>/dev/null; then
  log_info "Fairseq Cython extensions not found - building now (one-time setup)"
  cd "$vsp_dir/fairseq" || {
    log_error "Failed to cd to fairseq directory"
    return 1
  }
  python3 setup.py build_ext --inplace || {
    log_error "Failed to build fairseq Cython extensions"
    return 1
  }
  log_info "Fairseq Cython extensions built successfully"
  cd "$vsp_dir" || return 1
else
  log_info "Fairseq Cython extensions already present"
fi
```

**Impact**:
- ✅ First run: Auto-builds extensions (~30 seconds)
- ✅ Subsequent runs: Skips build (instant)
- ✅ No manual intervention required

**Source**: container_fixes_20260202/decode_cython_fix_20260202.tar.gz

---

### 2. VSP-LLM max_len Configuration (Fix #2)
**Date**: February 2, 2026
**Problem**: Decode step failing with:
```
ValueError: `max_new_tokens` must be greater than 0, but is 0.
```

**Root Cause**: Config file `s2s_decode.yaml` missing `max_len: 2048` setting, causing model to receive `max_new_tokens=0`.

**Solution**: Added max_len configuration to generation config.

**File**: `VSP-LLM/src/conf/s2s_decode.yaml` line 10

**Code**:
```yaml
generation:
  beam: 20
  max_len_a: 3.0
  max_len_b: 300
  max_len: 2048     # Hard cap - must be >= max_len_a * max_input + max_len_b
  lenpen: 0.0
```

**Impact**:
- ✅ Decode step completes successfully
- ✅ Allows up to 2048 tokens in generated output
- ✅ Prevents truncation of long transcriptions

**Source**: container_fixes_20260202/max_len_fix_20260202.tar.gz

---

### 3. Dynamic Transcription Paths (Fix #3)
**Date**: February 2, 2026
**Problem**: Transcriptions not persisting between container restarts. Required manual symlink creation.

**Root Cause**: ASR module had hardcoded paths:
- `/host/vsp_input/.transcriptions`
- `/workspace/vsp_input/.transcriptions`

**Solution**: Updated ASR module to dynamically derive `.transcriptions/` from input directory.

**Files**:
- `lib/asr.sh` line 61
- `run_flat_english_pipeline.sh` line 418

**Code** (lib/asr.sh):
```bash
# Use .transcriptions directory in the input video directory
# This automatically works with any mount point or path
local transcriptions_dir="${raw_dir}/.transcriptions"
```

**Code** (run_flat_english_pipeline.sh):
```bash
# Pass RAW_DIR instead of HOME
run_asr_transcription "$PREP_ROOT" "$ASR_VENV" "$AUTO_AVSR" "$DATA_NAME" \
  "$SEGMENTATION_ENABLED" "$SEG_DURATION" "$RAW_DIR" || {
```

**Impact**:
- ✅ Works with ANY mount point or input path
- ✅ Transcriptions persist on mounted volume
- ✅ No manual symlink creation needed
- ✅ Zero configuration required

**Example**:
```bash
# Input: /host/galaxy_export/ui/input_videos/
# Automatically uses: /host/galaxy_export/ui/input_videos/.transcriptions/
```

**Source**: container_fixes_20260202/transcription_path_fix_20260202.tar.gz

---

### 4. VSP_INPUT_DIR Environment Variable Support (Fix #4)
**Date**: February 2, 2026
**Problem**: UI also had hardcoded input paths, breaking when videos in different locations.

**Root Cause**: No environment variable support, hardcoded `/host/vsp_input`.

**Solution**:
1. Added `VSP_INPUT_DIR` environment variable support (highest priority)
2. Smart auto-detection for common paths
3. Updated `TranscriptionManager` to use `INPUT_DIR` from config

**Files**:
- `vsp-ui/app/config.py` lines 17-41
- `vsp-ui/app/services/transcription_manager.py`

**Code** (config.py):
```python
def _detect_environment():
    """Detect if running in container or EC2."""
    # Check for VSP_INPUT_DIR environment variable (highest priority)
    input_dir_env = os.environ.get("VSP_INPUT_DIR")

    # Check for Linux container environments
    if Path("/host/galaxy_export").exists():
        base_dir = Path("/host/galaxy_export")
        # Use env var if set, otherwise try common locations
        if input_dir_env:
            input_dir = Path(input_dir_env)
        elif Path("/host/galaxy_export/ui/input_videos").exists():
            input_dir = Path("/host/galaxy_export/ui/input_videos")
        else:
            input_dir = Path("/host/vsp_input")
        return base_dir, input_dir
```

**Impact**:
- ✅ Works with any input directory
- ✅ Environment variable override support
- ✅ Smart auto-detection as fallback
- ✅ UI works with any mount configuration

**Usage**:
```bash
# Optional: Override input directory
docker run -e VSP_INPUT_DIR=/custom/path/to/videos ...

# Or let it auto-detect (recommended)
docker run ...  # Automatically finds /host/galaxy_export/ui/input_videos
```

**Source**: container_fixes_20260202/ui_transcription_fix_20260202.tar.gz

---

### 5. UI Absolute Imports (Fix #5)
**Date**: February 3, 2026
**Problem**: Running `python3 app/server.py` caused:
```
ImportError: Attempted relative import with no known parent package
```

**Root Cause**: Relative import `from ..config` in function called at module load time.

**Solution**: Changed to absolute import.

**File**: `vsp-ui/app/services/transcription_manager.py` line 35

**Code**:
```python
# BEFORE:
from ..config import INPUT_DIR

# AFTER:
from app.config import INPUT_DIR
```

**Impact**:
- ✅ UI server can be run directly with `python3 app/server.py`
- ✅ No import errors
- ✅ Compatible with both package and direct execution

**Source**: container_fixes_20260202/ui_import_fix_20260202.tar.gz

---

### 6. log_info Stderr Redirect (Fix #6)
**Date**: January 29, 2026
**Problem**: Client outputs (reports and burned videos) not generated. `POST_ROOT` and `ARCHIVE_ROOT` variables contaminated with log messages.

**Root Cause**: `log_info()` function echoed to stdout instead of stderr, contaminating function return values captured via command substitution.

**Solution**: Added stderr redirect to log_info function.

**File**: `lib/common.sh` line 10

**Code**:
```bash
# BEFORE:
log_info() {
    echo "[$(date +'%H:%M:%S')] INFO: $*"     # Goes to stdout ❌
}

# AFTER:
log_info() {
    echo "[$(date +'%H:%M:%S')] INFO: $*" >&2  # Goes to stderr ✅
}
```

**Why This Matters**:
```bash
# In archive_previous_run():
log_info "Run ID: 20260129_162742"        # Now goes to stderr ✅
echo "${archive_root}"                     # Goes to stdout

# In pipeline:
ARCHIVE_ROOT=$(archive_previous_run ...)   # Captures ONLY stdout (clean path)
POST_ROOT="$ARCHIVE_ROOT/client_outputs"   # Now works correctly
```

**Impact**:
- ✅ Client outputs generate correctly
- ✅ No path contamination
- ✅ Clean function return values
- ✅ Reports and burned videos created successfully

**Source**: linux_container_ready/lib/common.sh

---

### 7. POST_ROOT Definition (Fix #7)
**Date**: January 29, 2026
**Problem**: Pipeline completed successfully but exited with code 1, showing "Error" in UI.

**Root Cause**: Line 501 referenced undefined `POST_ROOT` variable in final summary.

**Solution**: Added `POST_ROOT="$ARCHIVE_ROOT/client_outputs"` before final summary.

**File**: `run_flat_english_pipeline.sh` line 501

**Code**:
```bash
# BEFORE:
deactivate

echo
echo ">>> Pipeline complete!"
echo "    - Outputs: $POST_ROOT"  # ❌ POST_ROOT never defined

# AFTER:
deactivate

# Set POST_ROOT for final summary
POST_ROOT="$ARCHIVE_ROOT/client_outputs"

echo
echo ">>> Pipeline complete!"
echo "    - Outputs: $POST_ROOT"  # ✅ Now properly defined
```

**Impact**:
- ✅ Pipeline exits with code 0 (success)
- ✅ UI shows "Completed" instead of "Error"
- ✅ Final summary displays correct output path

**Source**: linux_container_ready/run_flat_english_pipeline.sh

---

### 8. Step 2.5 Metadata Creation (Fix #8)
**Date**: January 29, 2026
**Problem**: Burned videos showing 88x88 mouth crops instead of full-frame originals for non-segmented videos.

**Root Cause**: No `segment_metadata.json` created for whole videos, preventing `make_burn.py` Strategy 1 (extract from original full-frame video).

**Solution**: Added Step 2.5 to create proper metadata after preprocessing, before ASR.

**File**: `run_flat_english_pipeline.sh` lines 145-195 (SEGMENT_ONLY) and NEW Step 2.5 after preprocessing

**Code**:
```bash
# NEW Step 2.5: Create segment metadata for whole videos
# (Only when SEGMENTATION_ENABLED=0)
if [ "$SEGMENTATION_ENABLED" = "0" ]; then
  echo ">>> [2.5] Creating segment metadata for whole videos"

  metadata_file="${PREP_ROOT}/segment_metadata.json"
  echo "{" > "$metadata_file"

  for video_file in "$FLAT_VID_DIR"/*.mp4; do
    # Get video info with ffprobe
    # Create metadata entry with timing info
    # ...
  done

  echo "}" >> "$metadata_file"
fi
```

**Impact**:
- ✅ Burned videos use full-frame originals (224x224)
- ✅ Strategy 1 extraction works for whole videos
- ✅ No more mouth crops in final outputs

**Source**: linux_container_ready/run_flat_english_pipeline.sh

---

### 9. Non-Segmented Video Naming (Fix #9)
**Date**: January 29, 2026
**Problem**: Manual transcriptions not matching for short videos. Transcription saved as `video.wrd` but pipeline expected `video_00_000000_999999.wrd`.

**Root Cause**: Artificial `_00_000000_999999` suffix added to non-segmented videos.

**Solution**: Keep original video name for non-segmented videos.

**File**: `run_flat_english_pipeline.sh` line 134

**Code**:
```bash
# BEFORE:
video_id="${video_name%.*}"
video_ext="${video_name##*.}"
output_name="${video_id}_00_000000_999999.${video_ext}"  # ❌ Artificial suffix

# AFTER:
output_name="${video_name}"  # ✅ Simple and correct
```

**Impact**:
- ✅ Transcription matching is simple: `video.mp4` ↔ `video.wrd`
- ✅ Manual transcriptions work correctly
- ✅ Naming is conceptually correct (only segmented videos have segment IDs)

**Source**: linux_container_ready/run_flat_english_pipeline.sh

---

### 10. make_burn.py Segment Matching (Fix #10)
**Date**: January 29, 2026
**Problem**: Even with proper metadata, burned videos showed mouth crops for non-segmented videos.

**Root Cause**: `parse_segment_id("00008")` returns `seg_idx = -1`, but segment lookup searched for `index == -1` which didn't exist in metadata.

**Solution**: Added special case for `seg_idx == -1` to use first segment.

**File**: `VSP-LLM/scripts/make_burn.py` lines 331-343

**Code**:
```python
# BEFORE:
segment_info = None
for seg in segments:
    if seg.get("index") == seg_idx:  # Fails when seg_idx == -1
        segment_info = seg
        break

# AFTER:
segment_info = None
if seg_idx == -1:
    # Non-segmented video - use first (and only) segment
    if segments:
        segment_info = segments[0]
        print(f"[INFO] {uid}: Using whole video (non-segmented)")
else:
    # Segmented video - find by index
    for seg in segments:
        if seg.get("index") == seg_idx:
            segment_info = seg
            break
```

**Impact**:
- ✅ Non-segmented videos: Strategy 1 succeeds, full-frame extraction
- ✅ Segmented videos: Unchanged behavior, index-based matching
- ✅ All burned videos use correct source

**Source**: linux_container_ready/VSP-LLM/scripts/make_burn.py

---

### 11. Decode Logger Duplication (Fix #11)
**Date**: January 29, 2026
**Problem**: Each segment's decode output appeared twice in logs (INST/REF/HYP messages duplicated).

**Root Cause**: Python logger propagation - child logger messages propagated to root logger, causing duplicate output.

**Solution**: Set `logger.propagate = False` to prevent child logger from reaching root.

**File**: `VSP-LLM/src/vsp_llm_decode.py` line 107

**Code**:
```python
# BEFORE:
logger = logging.getLogger("hybrid.speech_recognize")
if output_file is not sys.stdout:
    logger.addHandler(logging.StreamHandler(sys.stdout))

# AFTER:
logger = logging.getLogger("hybrid.speech_recognize")
logger.propagate = False  # Prevent duplicate logging to root logger ✅
logger.setLevel(logging.INFO)

# Add explicit handlers
file_handler = logging.StreamHandler(output_file)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logger.addHandler(file_handler)

if output_file is not sys.stdout:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(stdout_handler)
```

**Impact**:
- ✅ Each segment logged exactly once
- ✅ Decode logs 50% smaller
- ✅ Easier to read and debug

**Source**: linux_container_ready/VSP-LLM/src/vsp_llm_decode.py

---

### 12. Segment Duration Update (Fix #12)
**Date**: January 25-26, 2026
**Problem**: Default 4s segments not consistent across codebase. Hardcoded values in multiple files.

**Root Cause**: Segment duration scattered across 5 different files with no single source of truth.

**Solution**: Update to 12s everywhere, use variables instead of hardcoded values.

**Files**:
1. `run_flat_english_pipeline.sh` - SEG_DURATION=12, MIN_SPLIT_DURATION=24.0
2. `vsp-ui/app/config.py` - SEGMENT_DURATION=12, MIN_SPLIT_DURATION=24.0
3. `vsp-ui/app/services/validator.py` - Add segment_duration and min_split_duration fields
4. `vsp-ui/app/static/index.html` - Overlap label ">24s" with id="overlap-label-text"
5. `vsp-ui/app/static/app.js` - Dynamic label update from backend

**Code** (run_flat_english_pipeline.sh):
```bash
# BEFORE:
SEG_DURATION="4"
MIN_SPLIT_DURATION="8.0"

# AFTER:
SEG_DURATION="${SEG_DURATION:-12}"
MIN_SPLIT_DURATION="24.0"
export OVERLAP_ENABLED SEG_DURATION
```

**Code** (vsp-ui/app/config.py):
```python
# BEFORE:
SEGMENT_DURATION = 4
# MIN_SPLIT_DURATION didn't exist

# AFTER:
SEGMENT_DURATION = 12
MIN_SPLIT_DURATION = 24.0
```

**Impact**:
- ✅ Consistent 12s segments across entire system
- ✅ Better quality transcriptions (longer context)
- ✅ Fewer segments to process for same video length
- ✅ Frontend dynamically displays correct threshold

**Source**: linux_container_segment_duration_update/

---

## Architectural Changes

### Segment-First Normalization
**Date**: February 1, 2026
**Type**: Major architectural improvement

**Old Flow**:
```
Raw Videos → Normalize whole videos → Preprocess/segment → Mouth crop
```

**New Flow**:
```
Raw Videos → Fast segment (Step 0.1) → Normalize segments (Step 0.5) → Mouth crop
```

**Changes**:
- **Step 0.1**: Always runs (not just SEGMENT_ONLY mode)
  - Fast segmentation using codec copy (very fast)
  - Creates segments in `fast_segments/` directory
  - Generates `segment_metadata.json`

- **Step 0.5**: Normalizes SEGMENTS (not raw videos)
  - Input: `fast_segments/` (pre-segmented videos)
  - Output: `flat_prepared/` → `flat/` (normalized segments)
  - HDR/10-bit conversion runs on segments

- **Step 2**: Preprocessing ONLY does face detection + mouth cropping
  - Videos already segmented and normalized
  - `--disable-segmentation` always used

**Benefits**:
- ✅ Much faster for long videos (normalize 300× 12s segments instead of 1× 60min video)
- ✅ Lower memory usage during normalization
- ✅ Better parallelization potential
- ✅ More efficient processing overall

**Example**:
```
60-minute video:
Old: Normalize 1× 60min video (high memory, long processing)
New: Normalize 300× 12s segments (lower memory, faster)
```

**Source**: linux_container_ready/run_flat_english_pipeline.sh

---

## UI Features

### 1. Unified Transcription Management
**Date**: January 25, 2026

**Features**:
- Persistent `.transcriptions/` directory for all transcriptions
- Modal dialog for adding/editing transcriptions
- Badge system: [AUTO] (orange) vs [MANUAL] (green)
- Orphaned transcription detection and management
- Text normalization matching ASR format

**Files**:
- `vsp-ui/app/services/transcription_manager.py` - Core business logic
- `vsp-ui/app/server.py` - API endpoints
- `vsp-ui/app/static/index.html` - Modal UI
- `vsp-ui/app/static/app.js` - Frontend logic

**Impact**:
- ✅ Transcriptions persist across ALL pipeline runs
- ✅ Manual transcriptions never overwritten
- ✅ Easy to add/edit transcriptions before processing
- ✅ Clear visibility of transcription source

---

### 2. Video Exclusion Feature
**Date**: January 19, 2026

**Features**:
- Remove videos from processing without deleting them
- Videos moved to `vsp_input/.excluded/` folder
- Can be manually moved back if needed
- Remove buttons on video list

**Files**:
- `vsp-ui/app/static/index.html` - Remove buttons
- `vsp-ui/app/static/app.js` - removeVideo() function
- `vsp-ui/app/server.py` - handle_remove_video() endpoint

**Impact**:
- ✅ Non-destructive video removal
- ✅ Easy to restore excluded videos
- ✅ Cleaner video list

---

### 3. K-means Training Toggle
**Date**: January 19, 2026

**Features**:
- Checkbox to skip k-means training
- Use existing model instead of retraining
- Saves hours of processing time

**Files**:
- `vsp-ui/app/static/index.html` - Checkbox
- `vsp-ui/app/static/app.js` - Pass train_kmeans option
- `vsp-ui/app/services/pipeline_runner.py` - TRAIN_KMEANS env var

**Impact**:
- ✅ Optional k-means training
- ✅ Faster subsequent runs
- ✅ Reuse existing cluster model

---

### 4. Transcription Persistence (Steps 0.6, 1.5)
**Date**: January 25-29, 2026

**Features**:
- Step 0.6: Copy existing transcriptions BEFORE Whisper runs
- Step 1.5: Save new Whisper outputs AFTER ASR completes
- Whisper automatically skips videos with existing .wrd files

**Files**:
- `run_flat_english_pipeline.sh` - Steps 0.6 and 1.5
- `lib/asr.sh` - Transcription directory support

**Impact**:
- ✅ Whisper runs ONCE per video across all pipeline runs
- ✅ 90%+ time savings on subsequent runs
- ✅ Manual transcriptions persist forever

---

### 5. Original Video Serving
**Date**: January 27, 2026

**Features**:
- Serve full-frame original videos for manual transcription
- Dynamic segment extraction using ffmpeg
- Fast codec copy or re-encode fallback

**Files**:
- `vsp-ui/app/server.py` - handle_get_segment_video() with ffmpeg extraction

**Impact**:
- ✅ Full context for manual transcription
- ✅ Original video quality and audio
- ✅ No need to view 88x88 mouth crops

---

### 6. Upload Progress Improvements
**Date**: February 1, 2026

**Features**:
- Smooth progress bar animation
- Simulates gradual progress for fast uploads
- Prevents "stuck at 0% then jumps to 100%"

**Files**:
- `vsp-ui/app/static/app.js` - Progress simulation

**Impact**:
- ✅ Better UX during uploads
- ✅ Smooth visual feedback
- ✅ Works on both fast and slow connections

---

### 7. Whole Video Directory Support
**Date**: February 1, 2026

**Features**:
- UI supports `flat_video_whole` directory
- Checks three directories in priority order
- Works for both segmented and non-segmented videos

**Files**:
- `vsp-ui/app/server.py` - Multiple directory checks

**Impact**:
- ✅ Segment review works for all video types
- ✅ No more "no segments found" errors
- ✅ Unified UI experience

---

## Session History

### Phase 1: February 1, 2026 - Production Ready
**Package**: linux_container_ready/
**Changes**: 57 files
**Fixes**: 6 critical fixes + segment-first normalization

Key Updates:
- log_info stderr redirect
- POST_ROOT definition
- Step 2.5 metadata creation
- Non-segmented video naming
- make_burn segment matching
- Decode logger duplication fix
- Segment-first normalization architecture

### Phase 2: February 2, 2026 Morning - Path Fixes
**Package**: container_fixes_20260202/ (partial)
**Changes**: 5 files across 3 tarballs
**Fixes**: Dynamic transcription paths, VSP_INPUT_DIR support, Cython auto-build

Key Updates:
- Dynamic transcription paths (lib/asr.sh)
- VSP_INPUT_DIR environment variable (vsp-ui/app/config.py)
- Cython auto-build (lib/decode.sh)
- max_len configuration (VSP-LLM/src/conf/s2s_decode.yaml)

### Phase 3: February 2-3, 2026 - Final Fixes
**Package**: container_fixes_20260202/ (complete)
**Changes**: 2 additional files
**Fixes**: UI import error, final testing

Key Updates:
- Absolute imports (vsp-ui/app/services/transcription_manager.py)
- Final verification and testing
- Package consolidation

### Phase 4: January 26, 2026 - Segment Duration
**Package**: linux_container_segment_duration_update/
**Changes**: 5 files
**Fixes**: Segment duration 4s → 12s

Key Updates:
- Pipeline script variable usage
- Backend config update
- Frontend dynamic label update
- Consistent 12s segments everywhere

---

## Testing & Verification

### Module Tests
```bash
bash lib/test_all_modules.sh
# Expected: 37/37 tests pass
```

### Fix Verification
```bash
bash VERIFY.sh
# Expected: All 12 fixes verified ✅
```

### End-to-End Tests

**Test 1: Non-Segmented Video**
```bash
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/short/video.mp4
# Expected:
# - Cython builds on first run (if needed)
# - Decode completes without max_len error
# - Transcription saved to .transcriptions/
# - Burned video is full-frame (not mouth crop)
```

**Test 2: Segmented Video**
```bash
./run_flat_english_pipeline.sh /path/to/long/video.mp4
# Expected:
# - 12s segments created with 2s overlap
# - All transcriptions persist
# - Decode completes successfully
# - Client outputs generated correctly
```

**Test 3: Transcription Persistence**
```bash
# First run: Whisper transcribes all segments
./run_flat_english_pipeline.sh /path/to/videos/

# Second run: Whisper skips all segments (uses cached)
./run_flat_english_pipeline.sh /path/to/videos/
# Expected: ASR step completes in seconds (not minutes)
```

---

## Summary Statistics

**Total Fixes**: 12 critical bug fixes
**Architectural Changes**: 1 major improvement
**UI Features**: 7 enhancements
**Files Modified**: 20+ files across lib, pipeline, VSP-LLM, vsp-ui
**Package Size**: 2.9 MB (no large model files)
**Testing**: 37 automated module tests
**Sessions**: 4 major development phases
**Source Packages**: Consolidated from 6 packages

---

**Created**: February 3, 2026
**Last Updated**: February 3, 2026
**Package Version**: 1.0.0 FINAL
