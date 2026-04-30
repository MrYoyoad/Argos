# Container Sync Changelog

> EC2 changes pending replication to Linux container. Split from CLAUDE.md for easier navigation.
> See also:
> - [CLAUDE.md](../CLAUDE.md) — Project overview, rules, and sync requirements
> - [Architecture](architecture.md) — Pipeline architecture and data flow
> - [Development Guide](development-guide.md) — Commands, workflows, troubleshooting

## Pending Changes for Linux Container Version

The following changes have been made to the EC2 version and need to be replicated on the standalone Linux container:

### VSP UI Features (Added Jan 19, 2026)
1. **Video Exclusion Feature**: Users can exclude videos from processing without permanently deleting them
   - Frontend: Added remove buttons to video list items in `app/static/index.html` and `app/static/app.js`
   - Frontend: `removeVideo()` function calls `/api/remove-video` endpoint with confirmation dialog
   - Backend: `handle_remove_video()` moves videos to `~/vsp_input/.excluded/` folder instead of deleting (`app/server.py`)
   - Validator: Updated to skip videos in `.excluded` folder when scanning (`app/services/validator.py`)
   - Security: Path traversal protection (rejects filenames with .., /, \)
   - Note: Excluded videos remain in `.excluded/` folder and can be manually moved back if needed

2. **K-means Training Toggle**: Added checkbox to skip k-means training and use existing model
   - Frontend: Added checkbox in validation screen (`app/static/index.html`)
   - Frontend: Pass `train_kmeans` option in start request (`app/static/app.js`)
   - Backend: Accept `train_kmeans` parameter in `handle_start()` (`app/server.py`)
   - Backend: Pass to `PipelineRunner.start(train_kmeans=...)` (`app/services/pipeline_runner.py`)
   - Backend: Set `TRAIN_KMEANS` environment variable (0 or 1) in `_get_env()` (`app/services/pipeline_runner.py`)
   - **CRITICAL Pipeline Fix**: Change line 318-321 in `run_flat_english_pipeline.sh`:
     ```bash
     # BEFORE:
     LRS3_ROOT="$PREP_ROOT" \
     SPLIT="train" \
     NSHARD=1 \
     TRAIN_KMEANS=1 \

     # AFTER:
     TRAIN_KMEANS="${TRAIN_KMEANS:-1}" \
     LRS3_ROOT="$PREP_ROOT" \
     SPLIT="train" \
     NSHARD=1 \
     ```
   - This allows the environment variable to override the hardcoded value

3. **Unified Transcription Management** (Added Jan 25, 2026): Persistent storage for all transcriptions (manual + Whisper auto-generated)
   - **Overview**: All transcriptions stored in `~/vsp_input/.transcriptions/` for reuse across pipeline runs
   - **Key Benefit**: Whisper only runs once per video - huge time savings on subsequent runs!

   **Storage Architecture**:
   - Location: `~/vsp_input/.transcriptions/` (survives pipeline archiving)
   - Format: One `.wrd` file per video (one word per line, lowercase, alphanumeric)
   - Metadata: `metadata.json` tracks type (auto/manual), timestamps, word counts
   - Badges: `[AUTO]` (orange) for Whisper-generated, `[MANUAL]` (green) for user-entered/edited

   **Pipeline Integration**:
   - **Step 0.6** (NEW): Copies existing `.transcriptions/*.wrd` → `~/auto_avsr/flat_wrd/` BEFORE Whisper runs
   - **Step 1.5** (NEW): Saves new Whisper outputs → `.transcriptions/` AFTER ASR completes
   - **Result**: ASR script (`asr_to_words_notime.py`) automatically skips videos with existing .wrd files (built-in logic at lines 106-108)
   - Modified file: `run_flat_english_pipeline.sh` (added Steps 0.6 and 1.5)

   **Frontend Features**:
   - **Modal Dialog**: Click "Add/Edit Transcription" button on any video
     - Enter text (space or newline separated)
     - Live preview shows normalized output (matches ASR format)
     - Edit [AUTO] transcription → warns "will mark as [MANUAL]"
   - **Orphaned Transcriptions Section**: Shows transcriptions for videos not in input folder
     - [Keep] button - dismiss from list, keep transcription
     - [Delete] button - permanently delete transcription file
   - **Visual Indicators**: Badge colors clearly show [AUTO] vs [MANUAL] status

   **Backend Components**:
   - New file: `app/services/transcription_manager.py` - Core business logic
     - CRUD operations for `.wrd` files
     - Text normalization (matches ASR: lowercase, alphanumeric + apostrophes)
     - Metadata tracking and orphan detection
   - API Endpoints (added to `app/server.py`):
     - `GET /api/transcription?filename=video.mp4` - Get transcription text and metadata
     - `POST /api/transcription` - Save or delete transcription
     - `GET /api/orphaned-transcriptions` - List orphaned transcriptions
   - Validator enhancement (`app/services/validator.py`):
     - Added `has_transcription` and `transcription_type` fields to `VideoInfo` dataclass
     - Checks for existing transcriptions during validation
     - New function: `get_video_files()` for orphan detection

   **Data Flow Examples**:
   ```
   First Pipeline Run:
   video1.mp4 → Whisper transcribes → saved as .transcriptions/video1.wrd [AUTO]

   Second Pipeline Run (same video):
   video1.mp4 → Step 0.6 copies existing .wrd → Whisper SKIPS (huge time save!)

   Manual Transcription:
   video2.mp4 → User clicks "Add Transcription" → enters text → [MANUAL]
   → Next pipeline run: Whisper SKIPS, uses manual transcription

   Edit Auto Transcription:
   video1.mp4 [AUTO] → User clicks "Edit" → modifies text
   → Confirms: "This will mark as [Manual]" → becomes [MANUAL]

   Orphan Management:
   Remove video2.mp4 from ~/vsp_input/ folder
   → Validation shows in "Orphaned Transcriptions" section
   → User chooses: [Keep] or [Delete]

   Re-add Video:
   Add video1.mp4 back to folder after removal
   → Transcription still exists → pipeline reuses it immediately!
   ```

   **Important Behaviors**:
   - Manual transcriptions NEVER overwritten by Whisper (Step 1.5 checks before copying)
   - Editing any [AUTO] transcription converts it to [MANUAL] (with user confirmation)
   - Transcriptions persist when videos removed/re-added
   - Pipeline archives (`~/flat_runs_archive/`) do NOT include `.transcriptions/` source folder
   - All transcriptions flow through entire pipeline as ground truth references in reports

### Files Modified for Linux Container:

**Video Exclusion & K-means Toggle (Jan 19, 2026)**:
- `/workspace/vsp-ui/app/static/index.html` - Add processing options section with k-means checkbox
- `/workspace/vsp-ui/app/static/style.css` - Add CSS for checkbox and remove buttons
- `/workspace/vsp-ui/app/static/app.js` - Add removeVideo() function and train_kmeans parameter
- `/workspace/vsp-ui/app/server.py` - Update handle_start() to accept train_kmeans
- `/workspace/vsp-ui/app/services/pipeline_runner.py` - Add train_kmeans parameter and env variable

**Unified Transcription Management (Jan 25, 2026)**:
- `/workspace/vsp-ui/app/services/transcription_manager.py` - NEW FILE - Core transcription business logic
- `/workspace/vsp-ui/app/server.py` - Add transcription API endpoints (GET/POST transcription, GET orphaned)
- `/workspace/vsp-ui/app/services/validator.py` - Add has_transcription/transcription_type fields, get_video_files()
- `/workspace/run_flat_english_pipeline.sh` - Add Steps 0.6 (pre-copy) and 1.5 (post-save)
- `/workspace/vsp-ui/app/static/index.html` - Add transcription modal and orphaned section
- `/workspace/vsp-ui/app/static/app.js` - Add transcription modal logic, orphan management, display updates
- `/workspace/vsp-ui/app/static/style.css` - Add modal styling, badges, orphaned section styles

**See detailed step-by-step implementation guide:** `/home/ubuntu/transcription_update_steps.md` or `LINUX_CONTAINER_UPDATES.md`

4. **Segment Duration Update** (Added Jan 25, 2026): Increase default segment duration from 4s to 12s
   - **Overview**: Changes default segment duration across pipeline and UI for consistency
   - **Key Changes**:
     - `SEG_DURATION`: 4 → 12 seconds
     - `MIN_SPLIT_DURATION`: 8.0 → 24.0 seconds (maintains 2x relationship)
     - Frontend dynamically displays correct threshold from backend config

   **Pipeline Changes** (`/workspace/run_flat_english_pipeline.sh`):
   - Line ~25: `SEG_DURATION="${SEG_DURATION:-12}"` (was 4)
   - Line ~30: `MIN_SPLIT_DURATION="24.0"` (was 8.0)
   - Line ~31: Add `export OVERLAP_ENABLED SEG_DURATION` if not present
   - Line ~313: `--seg-duration "$SEG_DURATION"` (replace hardcoded 4)
   - Line ~334: `--seg-duration "$SEG_DURATION"` (replace hardcoded 4)
   - Line ~322: Update echo to `seg=${SEG_DURATION}s` (replace hardcoded 4s)

   **Backend Config** (`/workspace/vsp-ui/app/config.py`):
   - Line ~24: `SEGMENT_DURATION = 12` (was 4)
   - Line ~25: Add `MIN_SPLIT_DURATION = 24.0` (new constant)

   **Backend Validator** (`/workspace/vsp-ui/app/services/validator.py`):
   - Import: Add `MIN_SPLIT_DURATION` to imports from config
   - ValidationResult dataclass: Add `segment_duration: int` and `min_split_duration: float` fields
   - to_dict method: Add both new fields to returned dictionary
   - Both ValidationResult returns: Add `segment_duration=SEGMENT_DURATION, min_split_duration=MIN_SPLIT_DURATION`

   **Frontend HTML** (`/workspace/vsp-ui/app/static/index.html`):
   - Line ~123: Change span text from ">8s" to ">24s"
   - Line ~123: Add `id="overlap-label-text"` to span element for dynamic updates

   **Frontend JS** (`/workspace/vsp-ui/app/static/app.js`):
   - In `displayValidationResults()` function, after stats update:
     ```javascript
     // Update overlap label with dynamic min_split_duration
     const overlapLabel = document.getElementById('overlap-label-text');
     if (overlapLabel && result.min_split_duration) {
         overlapLabel.textContent = `Enable overlapping segments for videos >${result.min_split_duration}s`;
     }
     ```

**Segment Duration Update Files Modified for Linux Container (Jan 25, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Update SEG_DURATION and MIN_SPLIT_DURATION defaults, use variables
- `/workspace/vsp-ui/app/config.py` - Update SEGMENT_DURATION and add MIN_SPLIT_DURATION
- `/workspace/vsp-ui/app/services/validator.py` - Add fields to ValidationResult and pass to frontend
- `/workspace/vsp-ui/app/static/index.html` - Add id to span and update default text
- `/workspace/vsp-ui/app/static/app.js` - Add dynamic text update in displayValidationResults()

**See detailed implementation guide:** `/home/ubuntu/SEGMENT_DURATION_UPDATE.md`

5. **UI Status Bar Fix** (Added Jan 25, 2026): Align UI pipeline stages with actual pipeline script steps
   - **Overview**: Fixed mismatch between UI progress tracking and actual pipeline execution steps
   - **Problem**: config.py stage definitions were completely out of sync with run_flat_english_pipeline.sh
   - **Key Changes**: Updated PIPELINE_STAGES and STAGE_MARKERS to match actual pipeline flow

   **EC2 Backend Config** (`/home/ubuntu/vsp-ui/app/config.py`):
   - Updated `PIPELINE_STAGES` array (lines 37-48):
     - Added "normalize" stage for [0.5] video normalization (HDR/10-bit conversion)
     - Renamed "preprocess_ready" → "prepare_dirs" for [1] directory setup
     - Reordered "preprocess" and "asr" to match actual pipeline ([2] = preprocess, [3] = ASR)
     - Adjusted weights for better progress representation
   - Updated `STAGE_MARKERS` regex patterns (lines 51-62):
     - Fixed all stage markers to match actual pipeline output
     - [0.5] → normalize, [1] → prepare_dirs, [2] → preprocess, [3] → asr
     - [4] → lrs3_prep, [5] → manifests, [6] → kmeans
     - [7] → decode (not skipped!), [8] → client_outputs

   **Before (Incorrect Mapping)**:
   ```python
   # Old config.py was completely misaligned
   "asr": r">>> \[1\]",           # Wrong! [1] is prepare dirs, not ASR
   "preprocess_ready": r">>> \[2\]",  # Wrong! [2] is preprocess, not prepare
   "preprocess": r">>> \[3\]",    # Wrong! [3] is ASR, not preprocess
   "decode": r">>> \[8\]",        # Wrong! [8] is client outputs, not decode
   # Missing [0.5] video normalization stage entirely
   ```

   **After (Correct Mapping)**:
   ```python
   # New config.py correctly aligned with pipeline
   "normalize": r">>> \[0\.5\]",      # [0.5] Video normalization (NEW)
   "prepare_dirs": r">>> \[1\]",      # [1] Prepare directories
   "preprocess": r">>> \[2\]",        # [2] Mouth cropping
   "asr": r">>> \[3\] Running ASR",   # [3] ASR transcription
   "lrs3_prep": r">>> \[4\]",         # [4] LRS3 format conversion
   "manifests": r">>> \[5\] Building manifests",  # [5] Manifests
   "kmeans": r">>> \[6\]",            # [6] K-means clustering
   "decode": r">>> \[7\] Running VSP-LLM",  # [7] Decode (not skipped!)
   "client_outputs": r">>> \[8\] Building client",  # [8] Client outputs
   ```

   **Impact**:
   - UI now correctly shows progress through all 10 stages (was showing 9)
   - Stage names and descriptions match what's actually happening
   - Progress percentages more accurately reflect pipeline completion
   - Users see "Normalize Videos" stage instead of jumping straight to ASR
   - No more confusion about "step 7 is skipped" - it's the decode step!

**UI Status Bar Files Modified for Linux Container (Jan 25, 2026)**:
- `/workspace/vsp-ui/app/config.py` - Update PIPELINE_STAGES array and STAGE_MARKERS dict
  - Exact changes: Replace lines 37-62 with corrected version shown above
  - CRITICAL: Must match actual pipeline steps in `/workspace/run_flat_english_pipeline.sh`

6. **Original Video Serving for Manual Transcription** (Added Jan 27, 2026): Serve full-frame original videos instead of mouth crops
   - **Overview**: Modified segment video API to extract clips from original videos for better transcription context
   - **Problem**: Mouth-cropped videos (88x88) made it hard to understand context during manual transcription
   - **Solution**: Dynamically extract segments from original full-frame videos using ffmpeg

   **How It Works**:
   1. Parse segment ID to extract video name and segment index
   2. Load `segment_metadata.json` to get timing information (start_sec, duration)
   3. Use ffmpeg to extract clip from original video in `~/auto_avsr/flat/`
   4. Serve extracted segment with full resolution and audio

   **FFmpeg Extraction**:
   - Primary method: Codec copy (fast, no re-encoding)
     ```bash
     ffmpeg -ss <start> -i <original> -t <duration> -c copy output.mp4
     ```
   - Fallback: Re-encode if codec copy fails (libx264 + aac, ultrafast preset)
   - Temporary files cleaned up after serving
   - 30-second timeout to prevent hanging

   **Benefits**:
   - Full context: Users see complete video frame
   - Better quality: Original resolution and encoding
   - Audio preserved: Full audio track included
   - Fast extraction: 1-2 seconds per segment (codec copy)
   - No storage overhead: Generated on-demand

   **Files Modified**:
   - `/home/ubuntu/vsp-ui/app/server.py` - Updated `handle_get_segment_video()` method (lines 519-637)
   - `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/server.py` - Same changes for Linux container

   **Testing**:
   - All 5 tests pass: segment ID parsing, metadata loading, original videos exist, ffmpeg extraction works
   - Test script: `/tmp/test_original_video_serving.py`

   **Documentation**: See `/home/ubuntu/ORIGINAL_VIDEO_SERVING.md` for detailed implementation

**Original Video Serving Files Modified for Linux Container (Jan 27, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Replace `handle_get_segment_video()` method with ffmpeg-based extraction
  - Exact changes: Lines 519-547 replaced with new 119-line implementation
  - CRITICAL: Requires ffmpeg to be installed in the container environment

7. **TranscriptionManager API Fix** (Added Jan 29, 2026): Fixed incorrect method call in segments endpoint
   - **Problem**: Code was calling `transcription_mgr.get_metadata()` which doesn't exist in TranscriptionManager
   - **Error**: `'TranscriptionManager' object has no attribute 'get_metadata'`
   - **Impact**: "Inspect Videos" button was failing, preventing users from viewing/excluding videos before processing

   **The Fix**:
   - Changed `get_metadata()` to `get_transcription_info()` (the correct method name)
   - Updated return value access from `meta.get("type")` to `info.type` (TranscriptionInfo is an object, not a dict)

   **Code Change** (around line 273 in server.py):
   ```python
   # BEFORE (incorrect):
   if has_transcription:
       meta = transcription_mgr.get_metadata(f"{segment_id}.mp4")
       transcription_type = meta.get("type") if meta else "auto"

   # AFTER (correct):
   if has_transcription:
       info = transcription_mgr.get_transcription_info(f"{segment_id}.mp4")
       transcription_type = info.type if info else "auto"
   ```

**TranscriptionManager Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Fix method call in handle_get_segments() around line 273
  - Change: Replace `get_metadata()` with `get_transcription_info()`
  - Change: Replace `meta.get("type")` with `info.type`
  - Critical: Without this fix, the validate endpoint fails and "Inspect Videos" button doesn't work

8. **Segment Transcription Type Badge Fix** (Added Jan 29, 2026): Fixed segments showing [AUTO] badge when they have manual transcriptions
   - **Problem**: Segments with transcriptions in `flat_text_seg12s/` folder were showing [AUTO] badge instead of [MANUAL]
   - **Root Cause**: The `/api/segments` endpoint wasn't including `transcription_type` field in response
   - **Impact**: UI displayed incorrect badge color and type for segments with manual transcriptions

   **The Fix**:
   - Added `transcription_type` field to segment response objects in both `handle_get_segments()` and `_load_segment_info()`
   - Added fallback logic to check `flat_text_seg12s/` folder for .txt transcription files
   - Correctly sets type="manual" for transcriptions found in either location
   - Default to "manual" (not "auto") when metadata is missing, since files in `.transcriptions/` are typically manually created

   **Key Changes**:
   1. `handle_get_segments()` (lines 572-620):
      - Added `transcription_type = None` initialization
      - Gets type from TranscriptionManager metadata when .wrd file exists
      - Checks `flat_text_seg12s/` folder as fallback for .txt files
      - Includes `'transcription_type': transcription_type` in response

   2. `_load_segment_info()` (lines 257-298):
      - Same fallback logic to check `flat_text_seg12s/` folder
      - Consistent type determination logic

   **Behavior After Fix**:
   - Segments with .wrd files in `.transcriptions/` → type from metadata (or "manual" if missing)
   - Segments with .txt files in `flat_text_seg12s/` → type="manual"
   - Segments with no transcription → type=None (displayed as [NO TRANSCRIPTION])

**Segment Transcription Type Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Update both segment loading methods
  - `handle_get_segments()` (lines ~572-620):
    - Add `transcription_type = None` initialization
    - Add fallback check for `flat_text_seg{SEGMENT_DURATION}s` folder
    - Add `'transcription_type': transcription_type` to response dict
    - Import `AUTO_AVSR_DIR` and `SEGMENT_DURATION` from config
  - `_load_segment_info()` (lines ~257-298):
    - Add same fallback logic for `flat_text_seg{SEGMENT_DURATION}s` folder
    - Import `AUTO_AVSR_DIR` and `SEGMENT_DURATION` from config
  - Critical: Without this fix, segments with manual transcriptions incorrectly show [AUTO] badge

8. **Delete Transcription Screen Fix** (Added Jan 29, 2026): Fixed crash when deleting transcriptions from segment review screen
   - **Problem**: Clicking "Delete" button on segment review screen caused JavaScript error
   - **Error**: `"Failed to delete: Cannot set properties of null (setting 'textContent')"`
   - **Impact**: Users unable to delete transcriptions after segmentation completed

   **The Issue**:
   - `deleteTranscriptionFromList()` was always calling `displayValidationResults()`
   - This function expects DOM elements from the old validation screen
   - When on segment review screen, those elements don't exist → null reference error

   **The Fix**:
   - Check `currentScreen` variable to determine which screen is active
   - If on `segmentReview`: call `loadAndDisplaySegments()` to refresh segments
   - If on validation screen: call `displayValidationResults()` as before
   - Matches pattern already used in `saveTranscription()` function

   **Code Change** (lines 957-991 in app.js):
   ```javascript
   // BEFORE (always used validation screen refresh):
   // Update validation results
   const video = validationResult.valid_videos.find(v => v.filename === filename);
   if (video) {
       video.has_transcription = false;
       video.transcription_type = null;
   }
   // Refresh display
   displayValidationResults();

   // AFTER (check current screen):
   // Refresh the current screen - check which screen we're on
   if (currentScreen === 'segmentReview') {
       // Reload segments to show updated transcription
       await loadAndDisplaySegments();
   } else if (validationResult) {
       // Update validation results if we're on validation screen
       const video = validationResult.valid_videos.find(v => v.filename === filename);
       if (video) {
           video.has_transcription = false;
           video.transcription_type = null;
       }
       displayValidationResults();
   }
   ```

**Delete Transcription Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/static/app.js` - Update `deleteTranscriptionFromList()` function around line 957
  - Add screen check before refreshing display
  - Call `loadAndDisplaySegments()` for segment review screen
  - Call `displayValidationResults()` for validation screen
  - Critical: Without this fix, delete button fails with null reference error on segment review screen

9. **Segment Transcription Persistence Fix** (Added Jan 29, 2026): Implemented Steps 0.6 and 1.5 to make manual segment transcriptions persist across pipeline runs
   - **Problem**: Manual segment transcriptions were saved to `.transcriptions/` but never used by pipeline
   - **Root Cause**: Pipeline had no logic to copy transcriptions before ASR or save them after
   - **Impact**: Whisper re-transcribed all segments every run, ignoring manual work and wasting hours

   **The Solution**:
   Added two missing steps documented in CLAUDE.md but never implemented:

   **Step 0.6: Copy Existing Transcriptions (Before ASR)**
   - **Location**: Lines 489-515 in EC2 version
   - **Runs**: Before Step 3 (ASR/Whisper)
   - **What it does**:
     1. Scans `~/vsp_input/.transcriptions/` for existing `.wrd` files
     2. Identifies segment transcriptions (regex: `_[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$`)
     3. Copies them to `$SEGMENT_WRD_TMP` (ASR working directory)
     4. Whisper skips segments with existing `.wrd` files (built-in logic in `asr_to_words_notime.py`)

   **Step 1.5: Save New Transcriptions (After ASR)**
   - **Location**: Lines 531-606 in EC2 version
   - **Runs**: After Step 3 (ASR completes)
   - **What it does**:
     1. Scans `$SEGMENT_WRD_TMP` for new Whisper outputs
     2. Checks `metadata.json` to identify manual vs auto transcriptions
     3. Copies new auto-transcriptions to `.transcriptions/` (preserves manual)
     4. Updates `metadata.json` to mark them as "auto" type

   **Pipeline Flow (Updated)**:
   ```
   Before:
   [3] ASR → Whisper transcribes ALL segments

   After:
   [0.6] Copy existing transcriptions → ASR working dir
   [3] ASR → Whisper SKIPS segments with existing .wrd
   [1.5] Save new auto-transcriptions → .transcriptions/
   ```

   **Benefits**:
   - Manual transcriptions persist across pipeline runs
   - Whisper runs only once per video (90%+ time savings)
   - Manual transcriptions never overwritten by auto
   - Transcriptions survive resets, archives, re-runs

   **Example Workflow**:
   ```
   First Run: Whisper transcribes 6 segments → saves as [AUTO] (5 min)
   User: Manually edits segment 0 → becomes [MANUAL]
   Second Run: Whisper skips all 6 segments (0 seconds!)
   ```

**Segment Transcription Persistence Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Add Steps 0.6 and 1.5
  - **Step 0.6** (insert before Step 3 ASR, after `mkdir -p "$SEGMENT_WRD_TMP"`):
    ```bash
    echo ">>> [0.6] Checking for existing manual transcriptions"
    TRANSCRIPTIONS_DIR="$HOME/vsp_input/.transcriptions"

    if [ -d "$TRANSCRIPTIONS_DIR" ]; then
      copied_count=0
      for wrd_file in "$TRANSCRIPTIONS_DIR"/*.wrd; do
        if [ -f "$wrd_file" ]; then
          filename=$(basename "$wrd_file")
          # Check if segment transcription (has frame numbers)
          if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
            cp "$wrd_file" "$SEGMENT_WRD_TMP/"
            copied_count=$((copied_count + 1))
          fi
        fi
      done
      echo ">>> [0.6] Copied $copied_count existing transcription(s)"
    fi
    ```

  - **Step 1.5** (insert after Step 3 ASR, after `deactivate`):
    ```bash
    echo ">>> [1.5] Saving new auto-transcriptions to .transcriptions/"
    mkdir -p "$TRANSCRIPTIONS_DIR"
    METADATA_FILE="$TRANSCRIPTIONS_DIR/metadata.json"

    for wrd_file in "$SEGMENT_WRD_TMP"/*.wrd; do
      if [ -f "$wrd_file" ]; then
        filename=$(basename "$wrd_file")
        if [[ "$filename" =~ _[0-9]{2}_[0-9]{6}_[0-9]{6}\.wrd$ ]]; then
          # Check if manual transcription exists (don't overwrite)
          is_manual=$(python3 -c "import json; ..." 2>/dev/null)
          if [ "$is_manual" != "yes" ]; then
            cp "$wrd_file" "$TRANSCRIPTIONS_DIR/"
            # Update metadata as 'auto' type
          fi
        fi
      fi
    done
    ```

  - See `/tmp/transcription_persistence_fix.md` for complete code
  - **Critical**: Without this fix, manual segment transcriptions are ignored and Whisper re-transcribes everything every run

10. **POST_ROOT Undefined Variable Bugfix** (Added Jan 29, 2026): Fixed pipeline exit error caused by undefined variable
   - **Problem**: Pipeline completed successfully but exited with code 1 and showed "Error" in UI
   - **Root Cause**: Line 394 (EC2) / Line 429 (container) referenced undefined `POST_ROOT` variable in final summary
   - **Impact**: Despite successful processing, pipeline appeared to fail with "Processing failed at stage: Generate Outputs"

   **The Fix**:
   - Added `POST_ROOT="$ARCHIVE_ROOT/client_outputs"` before final summary echo statements
   - Location: After Step 8 client outputs complete, before pipeline completion message

   **Code Change** (both EC2 and container versions):
   ```bash
   # BEFORE (line 394/429 - undefined variable):
   deactivate

   echo
   echo ">>> Pipeline complete!"
   echo "    - Outputs: $POST_ROOT"  # POST_ROOT never defined

   # AFTER (added line after deactivate):
   deactivate

   # Set POST_ROOT for final summary
   POST_ROOT="$ARCHIVE_ROOT/client_outputs"

   echo
   echo ">>> Pipeline complete!"
   echo "    - Outputs: $POST_ROOT"  # Now properly defined
   ```

**POST_ROOT Bugfix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Define POST_ROOT before final summary (after line ~422, before line ~425)
  - Add: `POST_ROOT="$ARCHIVE_ROOT/client_outputs"`
  - Location: After `deactivate` line following client outputs step
  - Critical: Without this fix, pipeline exits with code 1 even when successful, showing error in UI

11. **Decode Output Duplication Bugfix** (Added Jan 29, 2026): Fixed duplicate INST/REF/HYP logging in decode step
   - **Problem**: Each segment's decode output appeared twice in logs, making logs verbose and confusing
   - **Root Cause**: Python logger propagation - child logger messages propagated to root logger, causing duplicate output
   - **Impact**: Decode logs showed each segment twice, doubling log size and making it hard to read

   **The Issue**:
   - Line 47: Root logger configured with `logging.basicConfig()`
   - Line 100-105: Another `basicConfig()` call for formatting
   - Line 106: Child logger `"hybrid.speech_recognize"` created
   - Line 219: `logger.info()` logs INST/REF/HYP
   - **Problem**: Child logger inherits from root, messages propagate to both → duplicate output!

   **The Fix**:
   - Set `logger.propagate = False` to prevent messages reaching root logger
   - Add explicit handlers to child logger for both file and stdout output
   - Messages now appear exactly once with proper formatting

   **Code Change** (lines ~106-108):
   ```python
   # BEFORE:
   logger = logging.getLogger("hybrid.speech_recognize")
   if output_file is not sys.stdout:  # also print to stdout
       logger.addHandler(logging.StreamHandler(sys.stdout))

   # AFTER:
   logger = logging.getLogger("hybrid.speech_recognize")
   logger.propagate = False  # Prevent duplicate logging to root logger
   logger.setLevel(logging.INFO)

   # Add file/stdout handler
   file_handler = logging.StreamHandler(output_file)
   file_handler.setFormatter(logging.Formatter(
       "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
       datefmt="%Y-%m-%d %H:%M:%S"
   ))
   logger.addHandler(file_handler)

   # If outputting to file, also print to stdout
   if output_file is not sys.stdout:
       stdout_handler = logging.StreamHandler(sys.stdout)
       stdout_handler.setFormatter(logging.Formatter(
           "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
           datefmt="%Y-%m-%d %H:%M:%S"
       ))
       logger.addHandler(stdout_handler)
   ```

**Decode Duplication Bugfix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/VSP-LLM/src/vsp_llm_decode.py` - Fix logger propagation (lines ~106-123)
  - Add: `logger.propagate = False`
  - Add explicit file and stdout handlers with formatters
  - Critical: Without this fix, decode logs show each segment twice

12. **Segment Transcription Save Location Bugfix** (Added Jan 29, 2026): Fixed segment transcriptions saving to wrong location
   - **Problem**: Manual transcriptions created in segment review screen were not being used by pipeline
   - **Root Cause**: Segment transcriptions saved to `flat_text_seg12s/` as `.txt` files, but pipeline looks in `.transcriptions/` for `.wrd` files
   - **Impact**: Users manually transcribed segments, but Whisper re-transcribed them anyway, wasting hours of work

   **The Issue**:
   - `/api/save-segment-transcription` endpoint saved to: `~/auto_avsr/preprocessed_flat_seg12/flat/flat_text_seg12s/{segment_id}.txt`
   - Pipeline Steps 0.6 and 1.5 looked in: `~/vsp_input/.transcriptions/{segment_id}.wrd`
   - **Result**: Transcriptions never found, Whisper ran on all segments every time!

   **The Fix**:
   - Modified `handle_save_segment_transcription()` to use `TranscriptionManager`
   - Segment transcriptions now save to `.transcriptions/` as `.wrd` files (unified location)
   - Pipeline Steps 0.6 and 1.5 now find and reuse segment transcriptions
   - Whisper skips all manually transcribed segments

   **Code Change** (lines ~796-814 in server.py):
   ```python
   # BEFORE:
   # Save transcription
   text_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_text_seg{SEGMENT_DURATION}s"
   text_dir.mkdir(parents=True, exist_ok=True)
   text_file = text_dir / f"{segment_id}.txt"

   try:
       words = transcription.split()
       with open(text_file, 'w') as f:
           for word in words:
               f.write(word + '\n')
       # ... send success ...

   # AFTER:
   # Save transcription to unified .transcriptions directory as .wrd file
   from .services.transcription_manager import TranscriptionManager

   try:
       transcription_mgr = TranscriptionManager()
       filename = f"{segment_id}.mp4"

       # Save as manual transcription
       transcription_mgr.save_transcription(filename, transcription, transcription_type='manual')

       words = transcription.split()
       # ... send success ...
   ```

   **Benefits**:
   - All transcriptions in one unified location (`.transcriptions/`)
   - All transcriptions in same format (`.wrd` files)
   - Segment transcriptions persist across pipeline runs
   - Whisper skips manually transcribed segments (huge time savings!)
   - Consistent behavior between validation screen and segment review screen

**Segment Transcription Location Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/server.py` - Update `handle_save_segment_transcription()` method (lines ~796-814)
  - Replace direct file save with `TranscriptionManager.save_transcription()` call
  - Save to `.transcriptions/` directory as `.wrd` files
  - Mark as 'manual' type
  - Critical: Without this fix, segment transcriptions are ignored by pipeline and Whisper re-transcribes everything

13. **Disable Validation Screen Transcription Buttons** (Added Jan 29, 2026): Removed transcription functionality from validation screen
   - **Rationale**: Transcribing full videos on validation screen doesn't help when videos get segmented during preprocessing
   - **Impact**: Simplifies workflow - users only transcribe final segments after preprocessing completes
   - **User Request**: "if it possible to do it from the validation screen i wish to disable it"

   **What Changed**:
   - Removed "Add Transcription" / "Edit Transcription" buttons from validation screen video list
   - Removed "Delete" transcription buttons
   - Removed event listeners for removed buttons
   - Transcription functionality now ONLY available in segment review screen (after preprocessing)

   **Workflow After Change**:
   1. **Validation Screen**: Add videos, adjust settings, click "Start Processing" (NO transcription buttons)
   2. **Processing**: Pipeline segments videos and runs Whisper ASR
   3. **Segment Review Screen**: Review segments, add/edit transcriptions for individual segments
   4. **Benefits**:
      - Clearer workflow - transcribe final output, not intermediate videos
      - Avoids confusion about full-video vs segment transcriptions
      - Transcriptions match actual pipeline segments

   **Code Changes** (lines ~571-608 in app.js):
   ```javascript
   // BEFORE: Validation screen had transcription buttons
   <div class="video-actions">
       <button class="btn-transcription" ...>
           ${v.has_transcription ? 'Edit' : 'Add'} Transcription
       </button>
       ${v.has_transcription ? `<button class="btn-delete-transcription"...>Delete</button>` : ''}
       <button class="btn-remove" ...>Remove</button>
   </div>

   // Event listeners for transcription buttons
   document.querySelectorAll('.btn-transcription').forEach(btn => { ... });
   document.querySelectorAll('.btn-delete-transcription').forEach(btn => { ... });

   // AFTER: Validation screen has only Remove button
   <div class="video-actions">
       <button class="btn-remove" ...>Remove</button>
   </div>

   // No transcription button event listeners
   ```

**Validation Screen Transcription Removal Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/vsp-ui/app/static/app.js` - Remove transcription buttons from `displayValidationResults()` function
  - Lines ~571-584: Remove transcription button HTML (keep only Remove button)
  - Lines ~596-608: Remove transcription button event listeners
  - Result: Validation screen shows only video list with Remove buttons

14. **Log Output Stdout Contamination Bug** (Added Jan 29, 2026): Fixed `log_info` contaminating function return values
   - **Problem**: Client outputs (reports and burned videos) not generated, `POST_ROOT` and `ARCHIVE_ROOT` variables contained log messages
   - **Root Cause**: `log_info()` function in `lib/common.sh` echoed to stdout instead of stderr
   - **Impact**: When functions like `archive_previous_run()` used `log_info` and returned values via `echo`, command substitution captured BOTH log messages and return value

   **Why This Broke Everything**:
   ```bash
   # In archive_previous_run():
   log_info "Run ID: 20260129_162742"        # Goes to stdout
   log_info "Archiving previous outputs..."   # Goes to stdout
   echo "${archive_root}"                      # Also goes to stdout

   # In pipeline:
   ARCHIVE_ROOT=$(archive_previous_run ...)   # Captures ALL stdout!
   # Result: ARCHIVE_ROOT = "[16:27:42] INFO: Run ID: ...\n[16:27:42] INFO: Archiving...\n/path/to/archive"

   # Then later:
   POST_ROOT="$ARCHIVE_ROOT/client_outputs"
   # Result: POST_ROOT = "[16:27:42] INFO: ...\n.../client_outputs"

   # Finally:
   python make_report.py --out_dir "$POST_ROOT"
   # Python tries to create directory with newlines and timestamps in the name!
   ```

   **Symptoms**:
   - Reports and burned videos not created
   - Log output showing "Wrote: [16:27:42] INFO: Run ID: ..." (contaminated paths)
   - `ls ARCHIVE_ROOT/client_outputs` returned "No such file or directory"
   - Pipeline appeared to succeed but no outputs generated

   **The Fix**:
   - Changed `log_info()` to redirect to stderr like `log_error()` and `log_warn()` already do
   - This prevents log messages from contaminating function return values captured via `$()`

   **Code Change** (lib/common.sh line ~10):
   ```bash
   # BEFORE:
   log_info() {
       echo "[$(date +'%H:%M:%S')] INFO: $*"     # Goes to stdout
   }

   # AFTER:
   log_info() {
       echo "[$(date +'%H:%M:%S')] INFO: $*" >&2  # Goes to stderr
   }
   ```

   **Why This Works**:
   - Stderr (`>&2`) is for diagnostic/logging output
   - Stdout is for data/return values
   - Command substitution `$(...)` only captures stdout, not stderr
   - Now `ARCHIVE_ROOT=$(archive_previous_run ...)` gets clean path without log contamination

   **Best Practice**:
   - All logging functions should output to stderr
   - Only data meant to be captured should go to stdout
   - Functions that "return" values via `echo` must ensure no other stdout output occurs

**Log Stdout Contamination Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/lib/common.sh` - Update `log_info()` function (line ~10)
  - Change: `echo "[$(date +'%H:%M:%S')] INFO: $*"` → `echo "[$(date +'%H:%M:%S')] INFO: $*" >&2`
  - Critical: Without this fix, all bash functions using `log_info` and returning values via `echo` will have contaminated return values, breaking client outputs, archive paths, and any derived variables
  - Transcription functionality available ONLY in segment review screen

15. **Non-Segmented Video Naming and Metadata Fix** (Added Jan 29, 2026): Fixed two issues with non-segmented (whole) videos
   - **Problem 1**: Manual transcriptions not being used by pipeline
   - **Problem 2**: Burned videos showing mouth-cropped videos instead of full-frame originals
   - **Root Cause**: Artificial segment-like naming (`_00_000000_999999` suffix) added to non-segmented videos
   - **Impact**: Confusing naming, transcription matching failures, and inability to extract from original videos

   **The Core Issue**:
   Videos too short for segmentation (<24s) were artificially renamed with segment-like suffixes:
   - Input: `00008.mp4`
   - Copied as: `00008_00_000000_999999.mp4`
   - Transcription: `00008_00_000000_999999.wrd` (from UI)
   - BUT preprocessing outputs: `00008.mp4` (original name, no suffix!)
   - ASR looks for: `00008.wrd` (doesn't exist)
   - Result: Manual transcription ignored, Whisper runs unnecessarily

   **Why Burned Videos Used Mouth Crops**:
   - `make_burn.py` tries 3 strategies to get video source
   - Strategy 1 (preferred): Extract segment from original full-frame video using `segment_metadata.json` timing
   - Strategy 2 (fallback): Use preprocessed mouth-cropped segment video
   - Strategy 3 (last resort): Use full original video

   **metadata.json was broken**:
   ```json
   // BEFORE (empty structure, no timing info):
   {"segments": [], "total_videos": 1, "segmentation_enabled": false}

   // Strategy 1 check fails because video ID not in metadata
   // Falls back to Strategy 2 → mouth crops used
   ```

   **The Fixes**:

   **Fix 1: Remove Artificial Segment Naming** (run_flat_english_pipeline.sh line ~130-139)
   ```bash
   # BEFORE (added confusing suffix):
   video_id="${video_name%.*}"
   video_ext="${video_name##*.}"
   output_name="${video_id}_00_000000_999999.${video_ext}"  # Artificial suffix
   cp "$video_file" "${FAST_SEG_DIR}/${output_name}"

   # AFTER (keep original name):
   output_name="${video_name}"  # Simple and correct
   cp "$video_file" "${FAST_SEG_DIR}/${output_name}"
   ```

   **Fix 2: Proper segment_metadata.json Structure** (run_flat_english_pipeline.sh line ~147-195)
   ```json
   // AFTER (proper structure with timing):
   {
     "00008": {
       "original_duration": 3.584,
       "segment_duration": 3.584,
       "overlap_duration": 0,
       "num_segments": 1,
       "segments": [
         {
           "index": 0,
           "start_frame": 0,
           "end_frame": 89,
           "start_sec": 0.0,
           "end_sec": 3.584,
           "duration": 3.584
         }
       ]
     }
   }
   ```

   **Benefits**:
   - Naming is conceptually correct: segmented videos have segment IDs, whole videos don't
   - Transcription matching is simple: `video_name.wrd` matches `video_name.mp4`
   - Burned videos use full-frame originals (Strategy 1 works with proper metadata)
   - No special-case logic needed - everything works consistently

   **Code Changes**:
   1. **Naming fix** (lines ~130-139):
      - Removed: `video_id="${video_name%.*}"`, `video_ext="${video_name##*.}"`, `output_name="${video_id}_00_000000_999999.${video_ext}"`
      - Added: `output_name="${video_name}"`

   2. **Metadata fix - SEGMENT_ONLY mode** (lines ~147-195):
      - Removed: Single-line JSON with empty segments array
      - Added: 49-line loop that creates proper metadata in FAST_SEG_DIR (for UI preview)

   3. **Metadata fix - Full pipeline** (NEW Step 2.5, lines ~318-375):
      - **Critical Fix**: Added second metadata creation after preprocessing completes
      - **Why needed**: make_burn.py looks for metadata at `${PREP_ROOT}/segment_metadata.json`, not in fast_segments/
      - Location: After Step 2 (preprocessing), before Step 3 (ASR)
      - Creates metadata at correct location for make_burn.py
      - Uses FLAT_VID_DIR videos as source (after normalization/preprocessing)
      - Enables Strategy 1 (extract from original full-frame video) in make_burn.py

   **Testing**:
   - Non-segmented videos now keep original names throughout pipeline
   - Manual transcriptions work (simple name matching)
   - Burned videos use full-frame originals (Strategy 1 succeeds with proper metadata at correct location)

**Non-Segmented Video Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/run_flat_english_pipeline.sh` - Three fixes:
  1. **Line ~130-139**: Remove segment suffix from output_name
     - Change: `output_name="${video_id}_00_000000_999999.${video_ext}"` → `output_name="${video_name}"`
  2. **Line ~147-195**: Replace empty metadata JSON with proper structure (SEGMENT_ONLY mode)
     - Replace single-line `echo "{\"segments\": [], ...}"` with 49-line loop
     - Creates metadata in fast_segments/ for UI preview
  3. **Line ~318-375** (NEW Step 2.5): Create metadata at PREP_ROOT for make_burn.py
     - Add after Step 2 (preprocessing), before Step 3 (ASR)
     - Only runs when SEGMENTATION_ENABLED=0
     - Creates metadata at `${PREP_ROOT}/segment_metadata.json` (correct location!)
- `/workspace/lib/asr.sh` - No changes needed (already has simple direct matching)

16. **Non-Segmented Video Burned Output Fix** (Added Jan 29, 2026): Fixed burned videos showing mouth crops for non-segmented videos
   - **Problem**: When segmentation disabled (videos <24s), burned videos showed 96x96 mouth crops instead of full-frame originals
   - **Root Cause**: `make_burn.py` couldn't match non-segmented video IDs to metadata segments
   - **Impact**: Even with proper metadata created in Step 2.5, Strategy 1 extraction failed and fell back to mouth crops

   **Why It Failed**:
   - Non-segmented video IDs don't have frame numbers: `"00008"` (not `"00008_00_000000_000300"`)
   - `parse_segment_id("00008")` returns `seg_idx = -1` (can't parse frame numbers)
   - Segment lookup searched for `index == -1` but metadata has `index == 0`
   - No match found → fell back to Strategy 2 (preprocessed mouth crops)

   **The Fix** (make_burn.py lines ~329-343):
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

   **Results**:
   - Non-segmented videos: Strategy 1 succeeds, extracts from original (224x224 full-frame)
   - Segmented videos: Unchanged behavior, still use Strategy 1 with index matching

**Non-Segmented Burned Output Fix Files Modified for Linux Container (Jan 29, 2026)**:
- `/workspace/VSP-LLM/scripts/make_burn.py` - Update segment matching logic (lines ~329-343)
  - Add special case for `seg_idx == -1` to use first segment
  - Enables Strategy 1 extraction for non-segmented videos
  - Critical: Without this fix, burned videos show mouth crops even with proper metadata

17. **Segmented Video Naming Fix for Non-Split Videos** (Added Feb 1, 2026): Fixed transcription matching when segmentation is enabled but video is too short to split
   - **Problem**: When segmentation enabled, videos too short for splitting (<24s) were getting artificial segment suffixes, breaking transcription matching
   - **Root Cause**: `preprocess_with_overlap.py` always added segment suffix even for single-segment videos
   - **Impact**: Manual transcriptions ignored, Whisper re-transcribed unnecessarily

   **Example Before Fix**:
   - Input: `00008.mp4` (20 seconds - too short to split)
   - Output: `00008_00_000000_000500.mp4` (artificial suffix)
   - User saves: `00008_00_000000_000500.wrd`
   - ASR expects: `00008.wrd`
   - Result: Transcription ignored

   **Example After Fix**:
   - Input: `00008.mp4` (20 seconds)
   - Output: `00008.mp4` (original name kept)
   - User saves: `00008.wrd`
   - ASR expects: `00008.wrd`
   - Result: Transcription used

   **Code Change** (lines ~229-240):
   ```python
   # Check if video was actually split before adding suffix
   if len(time_segments) == 1:
       segment_suffix = ""  # Single segment - keep original name
   else:
       segment_suffix = f"_{idx:02d}_{start_frame:06d}_{end_frame:06d}"
   ```

**Segmented Video Naming Fix Files Modified for Linux Container (Feb 1, 2026)**:
- `/workspace/auto_avsr/preparation/preprocess_with_overlap.py` - Update segment naming (lines ~229-240)
  - Add: `if len(time_segments) == 1: segment_suffix = "" else: segment_suffix = f"_{idx:02d}_{start_frame:06d}_{end_frame:06d}"`
  - Critical: Without this fix, non-split videos get artificial suffixes that break transcription matching

18. **Delete Modal Transcription Screen Fix** (Added Feb 1, 2026): Fixed "Delete Transcription" button in modal failing when on segment review screen
   - **Problem**: Clicking "Delete Transcription" button in the transcription modal caused JavaScript error when on segment review screen
   - **Root Cause**: `deleteCurrentTranscription()` always tried to update validation screen elements, even when on segment review screen
   - **Impact**: Users unable to delete manual transcriptions from the modal dialog on segment review screen

   **The Issue**:
   - Same bug as fix #8, but in a different function
   - `deleteCurrentTranscription()` (called from modal button) lacked screen check
   - Always called `displayValidationResults()` which expects validation screen DOM elements
   - On segment review screen → null reference error, delete fails

   **The Fix**:
   - Added same screen check pattern from `deleteTranscriptionFromList()` fix #8
   - Check `currentScreen` variable to determine active screen
   - If on segment review: call `loadAndDisplaySegments()` to refresh
   - If on validation screen: call `displayValidationResults()` as before
   - Moved `closeTranscriptionModal()` before refresh for better UX

   **Code Change** (lines ~907-936 in app.js):
   ```javascript
   // BEFORE (always used validation screen refresh):
   try {
       const result = await api('transcription', 'POST', {
           filename: currentTranscriptionFilename,
           delete: true
       });

       if (!result.success) {
           alert(`Failed to delete: ${result.error || 'Unknown error'}`);
           return;
       }

       // Update validation results
       const video = validationResult.valid_videos.find(
           v => v.filename === currentTranscriptionFilename
       );
       if (video) {
           video.has_transcription = false;
           video.transcription_type = null;
       }

       // Refresh display and close modal
       displayValidationResults();
       closeTranscriptionModal();

   } catch (err) {
       alert(`Failed to delete: ${err.message}`);
   }

   // AFTER (check current screen):
   try {
       const result = await api('transcription', 'POST', {
           filename: currentTranscriptionFilename,
           delete: true
       });

       if (!result.success) {
           alert(`Failed to delete: ${result.error || 'Unknown error'}`);
           return;
       }

       // Close modal first
       closeTranscriptionModal();

       // Refresh the current screen - check which screen we're on
       if (currentScreen === 'segmentReview') {
           // Reload segments to show updated transcription
           await loadAndDisplaySegments();
       } else if (validationResult) {
           // Update validation results if we're on validation screen
           const video = validationResult.valid_videos.find(
               v => v.filename === currentTranscriptionFilename
           );
           if (video) {
               video.has_transcription = false;
               video.transcription_type = null;
           }
           displayValidationResults();
       }

   } catch (err) {
       alert(`Failed to delete: ${err.message}`);
   }
   ```

**Delete Modal Fix Files Modified for Linux Container (Feb 1, 2026)**:
- `/workspace/vsp-ui/app/static/app.js` - Update `deleteCurrentTranscription()` function (lines ~907-936)
  - Add screen check before refreshing display
  - Call `loadAndDisplaySegments()` for segment review screen
  - Call `displayValidationResults()` for validation screen
  - Move `closeTranscriptionModal()` to happen before refresh
  - Critical: Without this fix, "Delete Transcription" button in modal fails with null reference error on segment review screen

19. **VSP-LLM max_len Configuration Fix** (Added Feb 1, 2026): Fixed Hydra schema validation error preventing decode step
   - **Problem**: Decode step failed with "Key 'max_len' not in 'GenerationConfig'" error
   - **Root Cause**: Config file `s2s_decode.yaml` set `generation.max_len: 2048` but GenerationConfig dataclass lacked this field
   - **Impact**: Pipeline failed at decode step [7], unable to run VSP-LLM inference

   **The Issue**:
   - Config: `s2s_decode.yaml` has `generation.max_len: 2048`
   - Hydra validates config against `GenerationConfig` schema in fairseq
   - GenerationConfig had `max_len_a`, `max_len_b`, `min_len` but NOT `max_len`
   - Hydra schema validation failed → decode script couldn't start

   **Why max_len is Important**:
   - Model's `generate()` method accepts `max_length` parameter (vsp_llm.py:353)
   - Passed to HuggingFace LLaMA decoder as `max_new_tokens` (vsp_llm.py:386)
   - Controls maximum output sequence length (default 30, config wants 2048)
   - Without it, long videos may have truncated transcriptions

   **The Fix (Two Parts)**:

   **Part 1: Add max_len to GenerationConfig Schema**
   ```python
   # /workspace/VSP-LLM/fairseq/fairseq/dataclass/configs.py (after line 743)
   max_len_b: int = field(
       default=200,
       metadata={
           "help": "generate sequences of maximum length ax + b, where x is the source length"
       },
   )
   max_len: int = field(
       default=0,
       metadata={
           "help": "maximum length of generated sequence (hard cap), 0 = use model default"
       },
   )
   min_len: int = field(
       default=1, metadata={"help": "minimum generation length"},
   )
   ```

   **Part 2: Pass max_len to Model Generate**
   ```python
   # /workspace/VSP-LLM/src/vsp_llm_decode.py (lines 217-221)
   # BEFORE:
   best_hypo = model.generate(target_list=sample["target"],
                              num_beams=cfg.generation.beam,
                              length_penalty=cfg.generation.lenpen,
                              **sample["net_input"])

   # AFTER:
   best_hypo = model.generate(target_list=sample["target"],
                              num_beams=cfg.generation.beam,
                              max_length=cfg.generation.max_len,
                              length_penalty=cfg.generation.lenpen,
                              **sample["net_input"])
   ```

   **Benefits**:
   - Decode step passes Hydra schema validation
   - Config value actually used by model (previously ignored)
   - Longer output sequences possible (2048 vs default 30)
   - Better handling of long video transcriptions

**VSP-LLM max_len Fix Files Modified for Linux Container (Feb 1, 2026)**:
- `/workspace/VSP-LLM/fairseq/fairseq/dataclass/configs.py` - Add `max_len` field to GenerationConfig (after line 743)
  - Insert between `max_len_b` and `min_len` fields
  - Default value: 0 (use model default)
  - Critical: Without this, Hydra schema validation fails and decode step cannot start
- `/workspace/VSP-LLM/src/vsp_llm_decode.py` - Pass `max_length=cfg.generation.max_len` to model.generate() (line ~220)
  - Add parameter between `num_beams` and `length_penalty`
  - Critical: Without this, config value is ignored and model uses hardcoded default (30 tokens)
  - **NOTE**: Superseded by fix #20 which replaces static max_len with dynamic calculation

20. **Decode CUDA OOM Fix for 12GB GPUs** (Added Feb 9, 2026): Fixed memory accumulation during decode on standalone 12GB GPU
   - **Problem**: Decode crashed with CUDA OOM at sample 18/49 on standalone computer (12GB GPU)
   - **Root Cause**: After fix #19 increased max_new_tokens from 30 to 2048, KV caches from HuggingFace generate() accumulated across samples. With the old max=30, each leaked cache was tiny (~75 MB); with 2048, they're much larger, filling 12 GB after ~17 samples.
   - **Impact**: Pipeline failed at decode step [7] on standalone computer; worked fine on EC2 (24GB GPU)

   **The Fix (Three Parts)**:

   **Part 1: Smart memory cleanup between samples** (PRIMARY fix)
   - Add `gc.collect()` + `torch.cuda.empty_cache()` between samples
   - `empty_cache()` runs every sample (<1ms overhead)
   - `gc.collect()` only triggers when free GPU memory < 2 GB (avoids overhead on larger GPUs)
   - Prevents memory accumulation across samples

   **Part 2: Dynamic max_length per sample** (SECONDARY fix)
   - Replace static `max_length=cfg.generation.max_len` (2048) with dynamic calculation
   - Uses existing config: `min(max_len, max_len_a * src_tokens + max_len_b)`
   - With max_len_a=3.0, max_len_b=300: typical 12s segment gets ~750 max tokens
   - Still 10x more than needed for any transcription, but prevents runaway generation
   - Keeps max_len=2048 as hard cap in config (unchanged)

   **Part 3: CUDA allocator optimization**
   - Add `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in decode.sh
   - Reduces memory fragmentation as recommended by PyTorch

   **Code Changes**:

   `vsp_llm_decode.py` imports (add `import gc`):
   ```python
   import gc
   import numpy as np
   import torch
   ```

   `vsp_llm_decode.py` decode loop (replace static max_length):
   ```python
   # Dynamic max_length: proportional to input size, capped by max_len
   src_tokens = sample['net_input']['source']['cluster_counts'][0].shape[0]
   dynamic_max_len = int(cfg.generation.max_len_a * src_tokens + cfg.generation.max_len_b)
   if cfg.generation.max_len > 0:
       dynamic_max_len = min(dynamic_max_len, cfg.generation.max_len)

   best_hypo = model.generate(target_list=sample["target"],
                              num_beams=cfg.generation.beam,
                              max_length=dynamic_max_len,
                              length_penalty=cfg.generation.lenpen,
                              **sample["net_input"])
   ```

   `vsp_llm_decode.py` after inner for loop (memory cleanup):
   ```python
       # Free GPU memory between samples (prevents accumulation on 12GB GPUs)
       if use_cuda:
           torch.cuda.empty_cache()
           free_mem = torch.cuda.mem_get_info()[0]
           if free_mem < 2 * 1024**3:  # Less than 2 GB free
               gc.collect()
               torch.cuda.empty_cache()
   ```

   `decode.sh` (add before python call):
   ```bash
   export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
   ```

**Decode OOM Fix Files Modified for Linux Container (Feb 9, 2026)**:
- `/workspace/VSP-LLM/src/vsp_llm_decode.py` - Add `import gc`, dynamic max_length, memory cleanup
  - Add `import gc` near other imports
  - Replace `max_length=cfg.generation.max_len` with dynamic calculation using cluster_counts
  - Add memory cleanup block after inner for loop (empty_cache + conditional gc.collect)
  - Critical: Without this fix, decode OOMs on 12GB GPUs after ~17 samples
- `/workspace/VSP-LLM/scripts/decode.sh` - Add `export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
  - Add before the `CUDA_VISIBLE_DEVICES=0 python` line
  - Reduces CUDA memory fragmentation

21. **Decode Beam Search OOM Fix + no_repeat_ngram** (Added Feb 12, 2026): Fixed OOM within single beam search call on 12GB GPUs
   - **Problem**: Decode crashed with CUDA OOM during `model.generate()` on 4th sample (12GB standalone GPU)
   - **Root Cause**: Fix #20 handled memory accumulation *between* samples, but OOM happens *within* a single beam search. With beam=20 and dynamic_max_len~750-1050, KV cache needs ~7-10GB on top of ~6GB model weights, exceeding 12GB.
   - **Amplifier**: Degenerate repetitive outputs ("yeah yeah yeah..." x 48) hit max_length, maximizing KV cache usage.
   - **Impact**: Pipeline failed at decode step [7] on standalone 12GB GPU

   **The Fix (Two Parts)**:

   **Part 1: Enable no_repeat_ngram_size (primary fix)**
   - Prevents degenerate repetitive n-gram outputs during beam search
   - With `no_repeat_ngram_size=3`, model cannot repeat same 3-gram → repetitive outputs stop early
   - Typical lip reading output: ~50 tokens for 12s segment (well within memory budget)
   - Added config value `no_repeat_ngram_size: 3` to `s2s_decode.yaml`
   - Passed through `vsp_llm_decode.py` → `vsp_llm.py` → HuggingFace `decoder.generate()`

   **Part 2: Dynamic max_len cap for small GPUs (safety net)**
   - Detect GPU memory after model loading
   - If GPU < 16GB: cap `dynamic_max_len` at 512 (instead of ~750-1050)
   - With beam=20 and 512 cap: KV cache ~ 5.2GB + 6GB model = ~11.2GB (fits in 12GB)
   - Beam size stays at 20 on all GPUs (no quality reduction)
   - 24GB GPUs unaffected (no cap applied)

   **Code Changes**:

   `vsp_llm_decode.py` (after model loading, ~line 174):
   ```python
   # Detect GPU memory for adaptive generation parameters
   gpu_mem_gb = 0
   if use_cuda:
       gpu_mem_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
       logger.info(f"GPU memory: {gpu_mem_gb:.1f} GB")
   small_gpu = gpu_mem_gb > 0 and gpu_mem_gb < 16
   ```

   `vsp_llm_decode.py` (before generate call, ~line 228):
   ```python
   # Tighter max_len cap for small GPUs (keeps beam=20 feasible within 12GB)
   if small_gpu and dynamic_max_len > 512:
       dynamic_max_len = 512

   best_hypo = model.generate(...,
                              no_repeat_ngram_size=cfg.generation.no_repeat_ngram_size,
                              ...)
   ```

   `vsp_llm.py` generate() method (~line 351):
   ```python
   def generate(self, ..., no_repeat_ngram_size=0, **kwargs):
       ...
       outputs = self.decoder.generate(..., no_repeat_ngram_size=no_repeat_ngram_size, ...)
   ```

   `s2s_decode.yaml`:
   ```yaml
   generation:
     no_repeat_ngram_size: 3  # Prevent degenerate repetitions
   ```

**Decode Beam Search OOM Fix Files Modified for Linux Container (Feb 12, 2026)**:
- `/workspace/VSP-LLM/src/vsp_llm_decode.py` - Add GPU memory detection + max_len cap + no_repeat_ngram_size passthrough
  - Add GPU detection after model loading (~line 174)
  - Add `if small_gpu and dynamic_max_len > 512: dynamic_max_len = 512` before generate
  - Add `no_repeat_ngram_size=cfg.generation.no_repeat_ngram_size` to model.generate() call
  - Critical: Without cap, beam=20 with 750+ tokens OOMs on 12GB GPUs
- `/workspace/VSP-LLM/src/vsp_llm.py` - Accept and pass no_repeat_ngram_size parameter
  - Add `no_repeat_ngram_size=0` to generate() signature
  - Add `no_repeat_ngram_size=no_repeat_ngram_size` to self.decoder.generate() call
  - Critical: Without this, config value is ignored and repetitions are unbounded
- `/workspace/VSP-LLM/src/conf/s2s_decode.yaml` - Add `no_repeat_ngram_size: 3`
  - Add after `max_len: 2048` line
  - Critical: Without this, degenerate repetitive outputs fill KV cache and cause OOM

22. **Inference Tuning — MISSION3 Revert + repetition_penalty** (Added Feb 16, 2026): Fixed "blabla" repetitive outputs
   - **Problem**: Decode produced too many words / degenerate repeats due to generous max_len parameters and no repetition penalty
   - **Root Cause**: max_len_a=3.0, max_len_b=300 gave 861 tokens of runway per segment, allowing repeats to fill the output
   - **Fix**: Revert to MISSION3-recommended values (2.0, 200) and add repetition_penalty=1.2

   **Files Modified**:
   - `/workspace/VSP-LLM/src/conf/s2s_decode.yaml` — Change max_len_a: 3.0→2.0, max_len_b: 300→200, add repetition_penalty: 1.2
   - `/workspace/VSP-LLM/fairseq/fairseq/dataclass/configs.py` — Add `repetition_penalty` field to GenerationConfig (after no_repeat_ngram_size)
   - `/workspace/VSP-LLM/src/vsp_llm_decode.py` — Add `repetition_penalty=cfg.generation.repetition_penalty` to model.generate() call

23. **Report Part Naming for Segmented Videos** (Added Feb 16, 2026): Group segments by video with "Part 1, Part 2" labels
   - **Problem**: Reports showed raw segment IDs like `Obama_00_000000_000300`, hard to read
   - **Fix**: Multi-segment videos labeled "Obama - Part 1", single-segment keep base name

   **Files Modified**:
   - `/workspace/VSP-LLM/scripts/make_report.py` — Add `parse_segment_id()`, `build_display_names()`, sort by video+segment, add display_name CSV column, show display name in HTML/TXT/ANSI
   - `/workspace/VSP-LLM/scripts/make_burn.py` — Output filenames use Part naming: `Obama_Part1_with_hyp.mp4`

24. **Lip Crops in Client Output** (Added Feb 16, 2026): Copy mouth-cropped videos to client deliverables
   - **Problem**: Lip crop videos (88-96px at 25fps) only existed in preprocessing dir
   - **Fix**: Copy lip crops to `client_outputs/lip_crops/` with Part naming

   **Files Modified**:
   - `/workspace/lib/outputs.sh` — Add lip crop copy step after burned videos (non-critical, warns on failure)

25. **NEA + Weighted WER Metrics** (Added Feb 16, 2026): Semantic meaning preservation metrics using spaCy
   - **What**: Named Entity Accuracy (NEA) measures preservation of high-value tokens (PROPN, NUM, named entities). Weighted WER penalizes entity errors 2x and function word errors 0.5x.
   - **spaCy dependency**: Optional. Falls back to stopword-based filtering if not installed. No container rebuild needed.
   - **Install on container** (optional): `pip install spacy && python -m spacy download en_core_web_sm`
   - **Report outputs**: CSV adds wwer_%, nea_recall_%, nea_precision_%, nea_f1_%, missed_entities columns. HTML adds color-coded NEA Recall and WWER columns. TXT/ANSI add metrics per segment and overall summary.

   **Files Modified**:
   - `/workspace/VSP-LLM/scripts/make_report.py` — Add spaCy import with fallback, classify_tokens(), weighted_wer(), nea_metrics(), compute_all_metrics(), nea_color(), MetricsResult dataclass. Update main() to compute and display metrics in all output formats.

26. **Drag-and-Drop Upload Fix** (Added Feb 16, 2026): Fixed silent upload failure for large video files
   - **Problem**: `self.rfile.read(content_length)` read entire file at once, causing timeout/OOM on large videos
   - **Fix**: Chunked reading (1MB chunks), 5-minute socket timeout, server-side upload logging, XHR timeout on client

   **Files Modified**:
   - `/workspace/vsp-ui/app/server.py` — Add `setup()` for socket timeout, replace single read with chunked loop, add upload logging
   - `/workspace/vsp-ui/app/static/app.js` — Add XHR timeout (5min + 1min/100MB) and timeout event handler

**Container Sync Status (Feb 17, 2026)**: Entries 22-26 have been synced to both `vsp_linux_container_FINAL_20260217/` and `vsp_docker/galaxy_export/`. All changes verified across all locations. See `BUGS_INSTALLING_CLIENT_STANDALONE.md` entries v1.0.31-v1.0.35 for details. The decode.sh fairseq auto-patch was extended to cover `repetition_penalty` in addition to `max_len` and `no_repeat_ngram_size`. spaCy install instructions documented in bug file.

27. **Video Normalization Fix — NVENC Silent Corruption + Bash fd Interference** (Added Feb 17, 2026): Fixed 3 bugs causing 43% video loss during normalization
   - **Problem**: NVENC GPU encoder (`h264_nvenc`) silently produced corrupt H.264 streams (exit code 0 but undecodable output). Additionally, bash file descriptor interference in the normalization loop caused subsequent videos to fail even with CPU encoding.
   - **Impact**: 656/1,520 segments (43%) failed face detection because their normalized output was corrupt. Original sources and fast-segmented copies (codec copy) were fine.
   - **Root Causes**:
     1. NVENC hardware/driver bug producing broken NAL units silently
     2. `while read ... done < <(find -print0)` shared fd 0 with child ffmpeg processes — ffmpeg's `>/dev/null 2>/dev/null` redirections interfered with the loop's input, corrupting filenames for subsequent iterations
     3. `needs_tonemap()` used `local f="$1"` which could shadow the caller's loop variable `f`

   **Fixes**:
   - Default `USE_GPU_NORM=0` in pipeline script (CPU encoding via `libx264`)
   - fd3 isolation: `while IFS= read -r -d '' f <&3; do ... done 3< <(find ... -print0)`
   - Post-encode validation: extract 1 frame after encode, fallback to raw copy on failure
   - Variable rename: `local _nt_file="$1"` in `needs_tonemap()`

   **Files Modified**:
   - `/workspace/lib/normalization.sh` — fd3 loop isolation, `_nt_file` rename, post-encode frame validation, `2>/dev/null` on ffmpeg stderr
   - `/workspace/run_flat_english_pipeline.sh` — Default `USE_GPU_NORM=0` (was 1)

**Container Sync Status (Feb 17, 2026)**: Entry 27 synced to both `vsp_linux_container_FINAL_20260217/` and `vsp_docker/galaxy_export/`. All 3 locations verified identical with `diff`. See `BUGS_INSTALLING_CLIENT_STANDALONE.md` entry v1.0.39 (Bug 41).

---

### 28. Report Decode Parameters (Feb 17, 2026)

   - **What**: Decode generation parameters (beam, repetition_penalty, max_len, etc.) are now saved during decode and included in all report outputs (HTML, TXT, ANSI, JSON).
   - **Why**: Enables documentation and comparison of different pipeline runs.

   **Files Modified**:
   - `/workspace/VSP-LLM/src/vsp_llm_decode.py` — Added `from datetime import datetime` import; after writing `hypo-{fid}.json`, writes `decode_params-{fid}.json` with effective generation parameters, GPU info, timestamp, and model checkpoint path. Wrapped in try/except so decode never fails due to params export.
   - `/workspace/VSP-LLM/scripts/make_report.py` — Added `--params` optional CLI argument. Three new helper functions (`_format_params_txt`, `_format_params_html`, `_format_params_ansi`) format params for each output. Params block prepended to HTML, TXT, and ANSI reports. A `report_params.json` is written alongside `report.csv` for machine readability. Fully backward-compatible: no params file = no params section.
   - `/workspace/lib/outputs.sh` — Derives `decode_params-{fid}.json` path from the hypo filename and passes `--params` to `make_report.py` if the file exists.

---

## Standalone Deployment Status (Feb 23, 2026)

**Tarball rebuilt**: `vsp_linux_container_FINAL_20260217.tar.gz` repacked to include 5 files that were updated after the previous tarball was created on Feb 17 16:55:
- `VSP-LLM/golden_kmeans/baseline_1396vid_20260218.bin` + `.json` (updated golden k-means model)
- `VSP-LLM/scripts/make_report.py` (report decode params, entry 28)
- `VSP-LLM/src/vsp_llm_decode.py` (report decode params, entry 28)
- `lib/outputs.sh` (report decode params, entry 28)

**Client machine status**: Running ~v1.0.32-35 (deployed ~Feb 15-17, before experiments). Missing v1.0.36-39 fixes (NVENC silent corruption, bash fd isolation) and post-v1.0.39 additions (golden k-means update, report decode params).

**Standalone decode config**: Runs baseline with `do_sample=True` hardcoded (stochastic beam search). EC2 has configurable `do_sample=False` (deterministic beam search) with `temperature` and `top_p` options — to be synced in a future update along with `lenpen` tuning option.

**To deploy**: Extract tarball on client, run `INSTALL.sh` inside Docker container. INSTALL.sh creates backup, installs all components, runs verification + 37 module tests.

### 27. IS + LLM Context Recovery in Pipeline Reports (Mar 5, 2026)

**Date**: 2026-03-05
**Category**: Pipeline output enhancement — **INTENTIONAL VERSION DIFFERENCE (EC2 vs Container)**

> **This feature is EC2-only by design.** The container version does NOT compute IS scores and should NOT be modified to do so without first installing the required dependencies. This is a deliberate divergence, not a sync gap.

**Why EC2-only**:
- IS scoring requires `sentence-transformers` (all-MiniLM-L6-v2 model), `metaphone`, `numpy`, and `torch` — heavy dependencies not in the container Python venv
- Semantic similarity computation loads a ~90MB transformer model into GPU/CPU memory
- Container deployment prioritizes lean, fast pipeline runs without research tooling overhead
- The `--compute-is` flag is opt-in and gated by `ENV_TYPE=ec2` in `outputs.sh`

**Version differences**:

| Behavior | EC2 (`ENV_TYPE=ec2`) | Container (`ENV_TYPE=container`) |
|----------|---------------------|----------------------------------|
| `make_report.py` invocation | `--compute-is` passed | No `--compute-is` flag |
| Report CSV columns | Includes `is_score`, `is_tier`, `is_label` | Standard columns only (no IS) |
| Report HTML table | Has IS column with color coding | No IS column |
| Report TXT/ANSI | Shows `IS: X.XX/5.0 (Label)` per segment | No IS line |
| Overall summary | Includes `IS: X.XX/5.0 | Captured: N/M (%)` | Standard WER/WWER/NEA only |
| Full IS analysis script | `generate_intelligibility_scores.py` runs | Not executed |
| Extra output files | `intelligibility_scores.csv`, `intelligibility_summary.json` | Not generated |

**Changed files**:
- `lib/outputs.sh` — Stage 8 now passes `--compute-is` to `make_report.py` only when `ENV_TYPE=ec2`, and runs `generate_intelligibility_scores.py` for full IS analysis (also EC2-only)
- `VSP-LLM/scripts/make_report.py` — Added `--compute-is` flag: computes per-segment IS score (0-5), tier, and label; adds IS column to HTML report, CSV, and text outputs; imports scoring functions from `docs/_research-tools/generators/generate_intelligibility_scores.py`. Without the flag, behavior is identical to before (backward compatible).

**To enable on container in the future** (not recommended unless research tooling is needed):
1. Install dependencies: `pip install sentence-transformers metaphone numpy`
2. Copy `docs/_research-tools/generators/generate_intelligibility_scores.py` to container
3. Change `ENV_TYPE` check in `outputs.sh` or pass `--compute-is` directly

**Output files added to `client_outputs/report/` (EC2 only)**:
- `intelligibility_scores.csv` — Full augmented CSV with IS, phonetic/semantic similarity, llm_context_prob, failure modes
- `intelligibility_summary.json` — Aggregate stats (mean IS, tier distribution, topic analysis)
- `report.html` now includes IS column per segment (when `--compute-is` is used)

---

### 27. Bug Fix: ENV_TYPE Not Set in Pipeline Script (Mar 6, 2026)

**Problem**: `lib/outputs.sh` gates IS scoring on `ENV_TYPE=ec2`, but the main pipeline script (`run_flat_english_pipeline.sh`) never sourced `lib/config.sh` — so `ENV_TYPE` was always empty and IS was silently skipped on every run.

**EC2 fix**: Added `source "${HOME}/lib/config.sh"` near the top of `run_flat_english_pipeline.sh`, right after `HOME_DIR` is set. This sets `ENV_TYPE=ec2` (and other exports from config.sh, which are then overridden by the pipeline's own explicit variable assignments).

**Container action**: Add `source "${BASE_DIR}/lib/config.sh"` after `BASE_DIR` is set in the container's `run_flat_english_pipeline.sh`. This will set `ENV_TYPE=container`, which correctly keeps IS disabled on the container (intentional version difference per item 26).

**Changed files**:
- `run_flat_english_pipeline.sh` — Added `source "${HOME}/lib/config.sh"` after line 17 (`HOME_DIR="${HOME}"`), with comment explaining it provides `ENV_TYPE` for `lib/outputs.sh`

**Container equivalent**:
```bash
# After BASE_DIR="$SCRIPT_DIR" (around line 20):
source "${BASE_DIR}/lib/config.sh"
```

---

### 28. WWER Tokenizer Mismatch Bug Fix (Mar 7, 2026)

**Problem**: `weighted_wer()` in `make_report.py` used `classify_tokens(ref)` (spaCy tokenization) for the reference but `toks(hyp)` (regex split) for the hypothesis. spaCy splits contractions like `"i'm"` into `["i", "'m"]` (2 tokens) while `toks()` keeps it as one token `["i'm"]`. This caused non-zero WWER for identical ref/hyp pairs containing contractions.

**Fix**: Use `classify_tokens()` for both ref and hyp so both sides use the same tokenizer.

**Changed files** (all three copies):
- `VSP-LLM/scripts/make_report.py`
- `vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/make_report.py`
- `vsp_docker/galaxy_export/VSP-LLM/scripts/make_report.py`

**Code change** (in `weighted_wer()` function):
```python
# BEFORE (line ~299-300):
ref_tokens = classify_tokens(ref)
hyp_words = toks(hyp)

# AFTER:
ref_tokens = classify_tokens(ref)
hyp_tokens = classify_tokens(hyp)
hyp_words = [w for w, _ in hyp_tokens]
```

**Container action**: Replace the same two lines in `/workspace/VSP-LLM/scripts/make_report.py`.

### IS Scoring for Standalone Container (March 10, 2026)

**Summary**: Intelligibility Score (IS) computation now runs on all environments (EC2 + standalone container), not just EC2. The ENV_TYPE gate has been removed.

**Changes applied to both galaxy_export and container overlay**:

1. **`VSP-LLM/scripts/generate_intelligibility_scores.py`** — NEW file
   - Copied from `docs/_research-tools/generators/generate_intelligibility_scores.py`
   - Provides `compute_is()`, `SemanticEncoder`, phonetic/length ratio functions
   - Dependencies: `torch`, `transformers`, `metaphone`, `editdistance`, `numpy` (all already in venv)

2. **`VSP-LLM/scripts/make_report.py`** — REPLACED with EC2 version
   - Added IS import block (lines 17-31): imports from same-directory first, then docs fallback
   - Added `--compute-is` CLI argument
   - Added IS computation loop (semantic similarity, phonetic, length ratio, WER → IS score)
   - Added IS columns to CSV, HTML, TXT, ANSI outputs
   - Added IS summary stats (mean IS, captured count)

3. **`lib/outputs.sh`** — UPDATED (all 3 locations: EC2, galaxy_export, overlay)
   - Removed `if [ "${ENV_TYPE:-}" = "ec2" ]` gate — IS always runs
   - Always passes `--compute-is` to `make_report.py`
   - Added auto-install block for `metaphone` (wheels + online fallback)
   - Added IS analysis script invocation (looks in `VSP-LLM/scripts/` first, then docs path)
   - Container versions: added `HF_HOME` + `TRANSFORMERS_OFFLINE=1` for offline model loading

4. **`is_model_cache/`** — NEW directory (galaxy_export only)
   - Contains bundled `sentence-transformers/all-MiniLM-L6-v2` model weights (88MB)
   - Enables offline semantic similarity computation
   - `outputs.sh` sets `HF_HOME` to this path when present

**Container action**: All files already updated in both `vsp_docker/galaxy_export/` and `vsp_linux_container_FINAL_20260217/`. Copy `is_model_cache/` directory to container overlay if deploying from overlay.

### Upload Timer Removal (March 10, 2026)

**Summary**: Removed simulated upload progress timer from EC2 `vsp-ui/app/static/app.js`. EC2 now matches the container's simpler implementation using only real XHR progress percentages.

**Change**: Replaced `uploadFile()` function (was ~130 lines with simulation logic) with clean version (~60 lines, real progress only). Removed: `simulatedProgress`, `progressSimulationInterval`, `hasRealProgress`, `loadstart` event, `loadend` event, `clearInterval` calls.

**Container action**: No changes needed — container already had the simplified version.

### Per-Token Confidence Scores (April 30, 2026) — PENDING SYNC TO CONTAINER

**Summary**: Decoder now emits per-token softmax confidence sidecars when the `VSP_OUTPUT_SCORES` environment variable is set to `1`. Used by the April 2026 client deck for word-level confidence visualization (green/yellow/red). Default behavior (env var unset or `0`) is unchanged — these are **purely additive, off-by-default extensions**, so the container continues to work identically until/unless the env var is set.

**EC2 files changed** (need to be replicated in the container's matching paths under `/workspace/`):

1. `VSP-LLM/src/vsp_llm.py` — added env-var-gated `output_scores=True, return_dict_in_generate=True` block (~lines 384-405). Search for `VSP_OUTPUT_SCORES` to locate. The block branches on `os.environ.get("VSP_OUTPUT_SCORES", "0") == "1"`; falls through to the legacy `model.generate()` call when unset.
2. `VSP-LLM/src/vsp_llm_decode.py` — added dict-unwrap path after `model.generate()` (the call returns a `GenerateOutput` dataclass when `return_dict_in_generate=True`, plain tensor otherwise) and a `confidence-{fid}.json` sidecar write next to the existing `hypo-{fid}.json` write. Search for `output_scores_enabled` to locate. Sidecar contains per-token max-softmax probability and the corresponding decoded token text.
3. `lib/decode.sh` — passes `VSP_OUTPUT_SCORES` env var through to `run_flat_decode.sh` (single line addition next to the other env-var pass-throughs).

**Container action when synced**: After porting these three files, the container will support per-token confidence sidecars when callers opt in via `VSP_OUTPUT_SCORES=1`. No callers in the container set this by default; UI and pipeline behavior are unchanged unless explicitly enabled.

**Verification on EC2**: Decode runs without `VSP_OUTPUT_SCORES` produce byte-identical hypo-*.json to pre-change runs. Decode runs with `VSP_OUTPUT_SCORES=1` additionally produce `confidence-{fid}.json` sidecars (one per segment) parseable by `docs/_research-tools/generators/compute_word_confidence.py`.

---

### Word-Level Confidence in Pipeline Output (April 30, 2026)

**Summary**: Stage 8 of the modular pipeline now emits per-word confidence artifacts on every run. `VSP_OUTPUT_SCORES=1` is the default (set in `lib/decode.sh`); decode runs that previously skipped scoring will start writing a `confidence-{fid}.json` sidecar with no caller change. `make_report.py` consumes it via a new `--word-confidence` flag and surfaces the data in both `report.csv` (3 trailing columns) and `report.html` (a labeled `Confidence:` line per segment, plus a `Sent Conf` metric cell next to `IS`).

**Why this change is here**: per-token confidence existed in the model code (`vsp_llm.py`/`vsp_llm_decode.py`) for one-off use (the Obama bin Laden demo at `presentation_materials_20260224/01_plots_for_slides/obama_demo_report.html`), but never ran automatically in the pipeline. Production deliveries had no confidence column or visualization. Now every client run produces the data.

**Color encoding** (deliberately distinct so the two cues never get confused):
- Accuracy (existing): green / yellow / red — match / mismatch / inserted
- Confidence (new): blue / orange / purple — high (≥0.85) / med (0.40–0.85) / low (<0.40)

**Files added (byte-identical across all three deploy locations)**:
1. `VSP-LLM/scripts/compute_word_confidence.py`  — canonical: `docs/_research-tools/generators/compute_word_confidence.py`
2. `VSP-LLM/scripts/generate_client_demo_report.py`  — canonical: same dir
3. `VSP-LLM/scripts/generate_intelligibility_scores.py`  — already mirrored, refreshed for `confidence_summary` block

**Files updated**:
4. `lib/decode.sh` — flipped `VSP_OUTPUT_SCORES` fallback from `:-0` to `:-1` (two occurrences)
5. `lib/outputs.sh` — new pre-`make_report.py` block aggregates the sidecar via `compute_word_confidence.py`; passes `--word-confidence <path>` when sidecar exists
6. `VSP-LLM/scripts/make_report.py` — new `--word-confidence` CLI flag; appends `sentence_confidence`, `min_word_conf`, `n_low_conf_words` to CSV; renders `Confidence:` line + `Sent Conf` metric cell in HTML; adds CSS `.conf-high/.conf-med/.conf-low` and a header legend
7. `docs/_research-tools/generators/generate_intelligibility_scores.py` — adds optional `confidence_summary` block to `intelligibility_summary.json` when `word_confidence.json` is present

**Output artifacts added to `<run>/client_outputs/report/`**:
- `confidence-{fid}.json` — raw per-token softmax sidecar (copied from `decode_output/`)
- `word_confidence.json` — aggregated per-word + per-segment summary
- New columns in `report.csv`: `sentence_confidence`, `min_word_conf`, `n_low_conf_words`
- New `Confidence:` line + `Sent Conf` cell in `report.html`
- New `confidence_summary` block in `intelligibility_summary.json`

**Backward compatibility**: if the sidecar is absent (old decode runs, `VSP_OUTPUT_SCORES=0`, container without the script), Stage 8 logs `[8] No confidence-{fid}.json sidecar — confidence will be skipped` and produces byte-identical pre-change output. CSV header does not gain confidence columns when no confidence data is loaded; HTML does not render a `Confidence:` row.

**Standalone container compatibility (verified)**: zero new Python dependencies. `compute_word_confidence.py` and `generate_client_demo_report.py` are pure stdlib. `make_report.py` already runs in the container's `vsp-llm-yoad-venv`. No change to `INSTALL.sh` needed.

**`run_flat_english_pipeline.sh` is NOT modified** in either EC2 or container — the master orchestrator stays untouched. Changes ride through the modular `lib/` it already sources.

**Container action**: copy the seven files above; verify md5 across all three deploy locations.

**Verification**: `pytest tests/unit/test_compute_word_confidence.py tests/unit/test_make_report_word_confidence.py tests/unit/test_vsp_llm_output_scores.py` (21 tests pass). End-to-end smoke run on `english_full_results/decode_output/hypo-979657.json` with synthetic confidence verified populated CSV columns + HTML rendering + `confidence_summary` block.

### NIV Y/P/N labels in IS output (April 30, 2026)

**Summary**: `generate_intelligibility_scores.py` now emits NIV (Net Intelligibility Verdict) labels — Y / P / N — directly in the per-segment CSV and a structured `niv_distribution` block in the summary JSON. Previously only legacy IS-tier labels were written; container had partial NIV (count-only, no per-segment column).

**Thresholds** (calibrated against Opus 4.6 judge, March 2026 — see [docs/evaluation/threshold_calibration_vs_opus.md](evaluation/threshold_calibration_vs_opus.md)):
- `NIV_Y_THRESHOLD = 3.80` — Y, clearly conveyed (κ=0.690 vs judge Y)
- `NIV_P_THRESHOLD = 2.00` — Y+P, any useful (κ=0.818 vs judge Y+P)

**Files changed (all three IS-script copies, kept byte-identical)**:
1. `docs/_research-tools/generators/generate_intelligibility_scores.py` (EC2 source-of-truth)
2. `vsp_docker/galaxy_export/VSP-LLM/scripts/generate_intelligibility_scores.py`
3. `vsp_linux_container_FINAL_20260217/VSP-LLM/scripts/generate_intelligibility_scores.py`

**Code additions**:
- New module-level constants `NIV_Y_THRESHOLD`, `NIV_P_THRESHOLD`
- New helper `niv_label(is_score) -> "Y"/"P"/"N"`
- New `niv` column in `intelligibility_scores.csv`
- New `niv_distribution` dict in `intelligibility_summary.json` (Y/P/N counts + thresholds + Y_pct + YP_pct)
- Backward-compat: `niv_useful_count` / `niv_useful_pct` (Y+P) and `niv_clearly_conveyed_count` / `niv_clearly_conveyed_pct` (Y) preserved
- Console summary now prints NIV Y/P/N/Y+P breakdown alongside legacy "captured" count

**Container action**: No further action needed — all three copies updated in this commit and verified identical (`md5sum` match).

**Verification**: End-to-end test on `english_full_results/client_outputs/report/report.csv` (1,497 segments): partition is exhaustive (Y=359 + P=564 + N=574 = 1,497); Y+P=923 (61.7%) matches published 922 (61.6%) within 1 segment; boundary cases verified (1.937→N, 3.763→P, 4.342→Y).
