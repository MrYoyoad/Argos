# Step-by-Step Implementation for Linux Container - Unified Transcription Management

## Overview
This guide provides detailed instructions for implementing the unified transcription management feature on the Linux container version.

## Step 1: Create TranscriptionManager Service (NEW FILE)

**Create file:** `/workspace/vsp-ui/app/services/transcription_manager.py`

**Source:** Copy from EC2 at `/home/ubuntu/vsp-ui/app/services/transcription_manager.py` (327 lines)

**Contents:**
- `TranscriptionInfo` dataclass (lines 18-27)
- `TranscriptionManager` class (lines 30-327)
- Key methods: `save_transcription()`, `get_transcription()`, `delete_transcription()`, `get_orphaned_transcriptions()`, `normalize_text()`

---

## Step 2: Update Backend - server.py

**File:** `/workspace/vsp-ui/app/server.py`

### Change 1: Add import (around line 27)
**After existing imports**, add:
```python
from .services.transcription_manager import TranscriptionManager

# Initialize transcription manager (module-level singleton)
transcription_mgr = TranscriptionManager()
```

### Change 2: Add GET routes (in `do_GET()` method, around line 78)
**After existing API routes**, add:
```python
elif path == "/api/transcription":
    params = parse_qs(parsed.query)
    self.handle_get_transcription(params)
elif path == "/api/orphaned-transcriptions":
    self.handle_get_orphaned_transcriptions()
```

### Change 3: Add POST route (in `do_POST()` method, around line 115)
**After `/api/remove-video`**, add:
```python
elif path == "/api/transcription":
    self.handle_post_transcription(data)
```

### Change 4: Add handler methods (around line 325)
**After `handle_open_folder()`**, copy these methods from EC2 version:
- `handle_get_transcription(self, params)` (~25 lines)
- `handle_post_transcription(self, data)` (~30 lines)
- `_handle_delete_transcription(self, data)` (~15 lines)
- `handle_get_orphaned_transcriptions(self)` (~20 lines)

**EC2 Source:** Lines 327-418 in `/home/ubuntu/vsp-ui/app/server.py`

---

## Step 3: Update Backend - validator.py

**File:** `/workspace/vsp-ui/app/services/validator.py`

### Change 1: Add import (around line 16)
**After existing imports**, add:
```python
from .transcription_manager import TranscriptionManager

# Initialize transcription manager
transcription_mgr = TranscriptionManager()
```

### Change 2: Update VideoInfo dataclass (around line 20)
**Add these fields** to the `VideoInfo` class:
```python
has_transcription: bool = False
transcription_type: Optional[str] = None  # "auto" or "manual"
```

### Change 3: Update validate_video function (around line 208)
**Before the final `return VideoInfo(...)`**, add:
```python
# Check for existing transcription
transcription_info = transcription_mgr.get_transcription_info(filename)
has_transcription = transcription_info is not None
transcription_type = transcription_info.type if transcription_info else None
```

**Then add to return statement:**
```python
return VideoInfo(
    # ... existing fields ...
    has_transcription=has_transcription,
    transcription_type=transcription_type,
)
```

### Change 4: Add helper function (at end of file)
**After `format_duration()` function**, add:
```python
def get_video_files() -> List[Path]:
    """Get list of video files in input folder (excluding .excluded)."""
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        video_files.extend(INPUT_DIR.glob(f"*{ext}"))
        video_files.extend(INPUT_DIR.glob(f"*{ext.upper()}"))

    # Filter out .excluded and .transcriptions folders
    video_files = [f for f in video_files if ".excluded" not in str(f) and ".transcriptions" not in str(f)]

    return list(set(video_files))
```

---

## Step 4: Update Pipeline Script

**File:** `/workspace/run_flat_english_pipeline.sh`

### Change 1: Add Step 0.6 (around line 275)
**Location:** AFTER video copy to FLAT_VID_DIR, BEFORE ASR step

**Insert this complete block:**
```bash
############################################
# STEP 0.6: Copy existing transcriptions
############################################
echo ">>> [0.6] Copying existing transcriptions if present"

TRANSCRIPTIONS_DIR="${INPUT_DIR}/.transcriptions"

if [ -d "$TRANSCRIPTIONS_DIR" ]; then
  mkdir -p "$WRD_DIR"

  copied_count=0

  # Copy only .wrd files for videos that exist in FLAT_VID_DIR
  for wrd_file in "$TRANSCRIPTIONS_DIR"/*.wrd; do
    if [ -f "$wrd_file" ]; then
      basename_noext=$(basename "$wrd_file" .wrd)

      # Check if corresponding video exists (try common extensions)
      video_exists=false
      for ext in mp4 MP4 avi AVI mov MOV mkv MKV; do
        if [ -f "$FLAT_VID_DIR/${basename_noext}.${ext}" ]; then
          video_exists=true
          break
        fi
      done

      if [ "$video_exists" = true ]; then
        cp "$wrd_file" "$WRD_DIR/"
        echo "  [REUSE] Copied existing transcription: ${basename_noext}.wrd"
        copied_count=$((copied_count + 1))
      fi
    fi
  done

  echo "  Total transcriptions reused: $copied_count"
else
  echo "  No transcriptions directory found (first run)"
fi

echo
```

### Change 2: Add Step 1.5 (around line 332)
**Location:** AFTER ASR completes (after `deactivate` line)

**Insert this complete block:**
```bash
############################################
# STEP 1.5: Save new Whisper outputs
############################################
echo ">>> [1.5] Saving new Whisper outputs for future reuse"

TRANSCRIPTIONS_DIR="${INPUT_DIR}/.transcriptions"
mkdir -p "$TRANSCRIPTIONS_DIR"

saved_count=0

# Copy new .wrd files from WRD_DIR to TRANSCRIPTIONS_DIR
# (only if they don't already exist - preserves manual transcriptions)
for wrd_file in "$WRD_DIR"/*.wrd; do
  if [ -f "$wrd_file" ]; then
    basename_wrd=$(basename "$wrd_file")
    dest_file="$TRANSCRIPTIONS_DIR/$basename_wrd"

    if [ ! -f "$dest_file" ]; then
      cp "$wrd_file" "$dest_file"
      echo "  [SAVED] ${basename_wrd}"
      saved_count=$((saved_count + 1))
    fi
  fi
done

echo "  Total new transcriptions saved: $saved_count"
echo
```

**Note:** The Python metadata update script is optional - the .wrd files alone provide basic functionality.

---

## Step 5: Update Frontend - index.html

**File:** `/workspace/vsp-ui/app/static/index.html`

### Change 1: Add orphaned section (around line 83)
**After invalid videos section**, add:
```html
<!-- Orphaned Transcriptions -->
<div id="orphaned-section" style="display: none;" class="orphaned-section">
    <h3>⚠️ Orphaned Transcriptions</h3>
    <p class="help-text">
        These transcriptions exist but their videos are not in the input folder.
        Keep them if you plan to re-add the videos, or delete them to clean up.
    </p>
    <ul id="orphaned-list" class="video-list"></ul>
</div>
```

### Change 2: Add modal dialog (around line 197)
**Before `<script src="app.js"></script>`**, add complete modal HTML from EC2 version.

**EC2 Source:** Lines 200-243 in `/home/ubuntu/vsp-ui/app/static/index.html`

The modal includes:
- Header with title and close button
- Body with textarea, preview, help text
- Footer with Cancel, Delete, and Save buttons

---

## Step 6: Update Frontend - app.js

**File:** `/workspace/vsp-ui/app/static/app.js`

### Change 1: Add global variables (around line 12)
**After existing state variables**, add:
```javascript
let currentTranscriptionFilename = null;
let currentTranscriptionType = null;
let orphanedTranscriptions = [];
```

### Change 2: Update displayValidationResults (around line 229)
**Replace video list generation** to include transcription buttons and badges.

**Key changes:**
- Add badge display in video info
- Wrap buttons in `<div class="video-actions">`
- Add transcription button with data attributes
- Add event listeners for transcription buttons

**EC2 Source:** Lines 229-258 in `/home/ubuntu/vsp-ui/app/static/app.js`

### Change 3: Add orphan loading call (around line 268)
**At end of `displayValidationResults()`**, add:
```javascript
// Load orphaned transcriptions
loadOrphanedTranscriptions();
```

### Change 4: Add transcription functions (around line 312)
**After `removeVideo()` function**, copy all transcription functions from EC2 version:
- `openTranscriptionModal()` - Opens modal and loads data
- `closeTranscriptionModal()` - Closes and resets modal
- `updateTranscriptionPreview()` - Live preview as user types
- `saveTranscription()` - Saves to API
- `deleteCurrentTranscription()` - Deletes transcription
- `loadOrphanedTranscriptions()` - Fetches orphans from API
- `displayOrphanedTranscriptions()` - Renders orphan list
- `deleteOrphan()` - Deletes an orphan
- `keepOrphan()` - Dismisses orphan from list

**EC2 Source:** Lines 315-523 in `/home/ubuntu/vsp-ui/app/static/app.js`

### Change 5: Add event listeners (around line 1005)
**In `DOMContentLoaded` handler**, add:
```javascript
// Transcription modal
document.getElementById('transcription-text').addEventListener('input', updateTranscriptionPreview);

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('transcription-modal').style.display === 'flex') {
        closeTranscriptionModal();
    }
});

// Close modal on backdrop click
document.getElementById('transcription-modal').addEventListener('click', (e) => {
    if (e.target.id === 'transcription-modal') {
        closeTranscriptionModal();
    }
});
```

---

## Step 7: Update Frontend - style.css

**File:** `/workspace/vsp-ui/app/static/style.css`

### Add at end of file (after line 672)
Copy all CSS styles from EC2 version (~300 lines):

**Sections to add:**
1. **Transcription Modal** - `.modal`, `.modal-content`, `.modal-header`, etc.
2. **Transcription Badges** - `.badge-auto` (orange), `.badge-manual` (green)
3. **Video List Enhancements** - `.video-list-item`, `.video-actions`, `.btn-transcription`
4. **Orphaned Section** - `.orphaned-section`, `.orphaned-item`, `.orphaned-actions`
5. **Responsive Design** - Media queries for mobile

**EC2 Source:** Lines 673-973 in `/home/ubuntu/vsp-ui/app/static/style.css`

---

## Step 8: Test the Implementation

### 8.1 Start VSP UI Server
```bash
cd /workspace/vsp-ui
python -m app.server
```

### 8.2 Add Test Videos
```bash
cp /path/to/test/video.mp4 ~/vsp_input/
```

### 8.3 Test Manual Transcription
1. Open browser to validation screen
2. Click "Add Transcription" button
3. Enter: `hello world this is a test`
4. Verify preview shows normalized words
5. Save and verify `[MANUAL]` badge (green) appears

### 8.4 Run Pipeline
```bash
./run_flat_english_pipeline.sh ~/vsp_input/
```

### 8.5 Verify Pipeline Logs
Look for these messages:
```
>>> [0.6] Copying existing transcriptions if present
  [REUSE] Copied existing transcription: video.wrd
  Total transcriptions reused: 1

>>> [1] Running ASR to create .wrd files
[SKIP] exists: /home/ubuntu/auto_avsr/flat_wrd/video.wrd

>>> [1.5] Saving new Whisper outputs for future reuse
  Total new transcriptions saved: 0
```

### 8.6 Check Directory Structure
```bash
ls -la ~/vsp_input/.transcriptions/
# Should show: metadata.json and *.wrd files

cat ~/vsp_input/.transcriptions/video.wrd
# Should show: one word per line, lowercase
```

### 8.7 Test Orphan Management
1. Remove video from `~/vsp_input/`
2. Re-validate in UI
3. Verify orphaned transcriptions section appears
4. Test [Keep] and [Delete] buttons

### 8.8 Test Edit Behavior
1. Click "Edit Transcription" on `[AUTO]` transcription
2. Modify text
3. Confirm warning: "This will mark as [Manual]"
4. Save and verify badge changes to `[MANUAL]`

---

## Troubleshooting

### Module Import Errors
**Symptoms:** `ModuleNotFoundError: No module named 'transcription_manager'`

**Solution:**
- Verify file location: `/workspace/vsp-ui/app/services/transcription_manager.py`
- Check `__init__.py` exists in services directory
- Restart VSP UI server

### Modal Doesn't Open
**Symptoms:** Clicking "Add Transcription" does nothing

**Solution:**
- Check browser console for JavaScript errors
- Verify modal HTML is in index.html (before `<script>` tag)
- Verify event listeners are in DOMContentLoaded handler
- Check that button has correct `onclick` or event listener

### Transcriptions Not Persisting
**Symptoms:** Transcriptions disappear after pipeline run

**Solution:**
- Verify `~/vsp_input/.transcriptions/` directory exists
- Check pipeline logs for Step 0.6 and 1.5 messages
- Ensure pipeline doesn't archive `.transcriptions/` folder
- Verify Step 1.5 checks `if [ ! -f "$dest_file" ]` before copying

### Whisper Still Running
**Symptoms:** Whisper transcribes videos that already have .wrd files

**Solution:**
- Verify Step 0.6 runs BEFORE Step 1 (ASR)
- Check that .wrd files are in `~/auto_avsr/flat_wrd/` before ASR
- Verify ASR script has skip logic (check `asr_to_words_notime.py` lines 106-108)
- Ensure file extensions match (try multiple in Step 0.6)

### API Endpoints Return 404
**Symptoms:** Network errors in browser console for `/api/transcription`

**Solution:**
- Verify routes added to both `do_GET()` and `do_POST()` in server.py
- Check handler methods are defined
- Restart VSP UI server after changes
- Check server logs for errors

### Badges Not Showing
**Symptoms:** No `[AUTO]` or `[MANUAL]` badges on videos

**Solution:**
- Verify validator.py returns `has_transcription` and `transcription_type` fields
- Check app.js video list template includes badge HTML
- Verify CSS styles are loaded (`.badge-auto`, `.badge-manual`)
- Check browser console for template errors

### CSS Styles Missing
**Symptoms:** Modal looks broken, buttons unstyled

**Solution:**
- Verify style.css includes all new styles at end of file
- Check browser cache (hard refresh: Ctrl+Shift+R)
- Verify no CSS syntax errors in browser console
- Check file was saved correctly

---

## Verification Checklist

Use this checklist to confirm all components are working:

- [ ] TranscriptionManager imported in server.py and validator.py
- [ ] API endpoints respond:
  - [ ] `GET /api/transcription?filename=video.mp4`
  - [ ] `POST /api/transcription` (save)
  - [ ] `POST /api/transcription` (delete)
  - [ ] `GET /api/orphaned-transcriptions`
- [ ] VideoInfo dataclass has new fields
- [ ] Pipeline Step 0.6 copies existing transcriptions
- [ ] Pipeline Step 1.5 saves new transcriptions
- [ ] Modal dialog renders and opens
- [ ] Transcription buttons appear on videos
- [ ] Badges show correct colors (orange/green)
- [ ] Live preview works as you type
- [ ] Save button creates `.wrd` file
- [ ] Delete button removes transcription
- [ ] Orphaned section appears when needed
- [ ] Whisper skips videos with transcriptions (check logs)
- [ ] Manual transcriptions persist across runs
- [ ] `.transcriptions/` survives archiving

---

## Performance Expectations

After implementation, you should see:

- **First run**: Normal Whisper processing time
- **Second run (same videos)**: ASR step completes almost instantly
- **Log output**: `[SKIP]` messages for all existing transcriptions
- **Time saved**: ~30-120 seconds per video (depending on Whisper model)

---

## Support

If you encounter issues not covered in this guide:

1. Check EC2 version for working reference implementation
2. Compare file contents line-by-line with EC2 version
3. Review browser console and server logs for errors
4. Verify Python and bash syntax is correct
5. Test with minimal example (single video, simple transcription)
