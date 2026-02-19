# Updates Required for Linux Container Version

## Table of Contents
1. [make_report.py Color Coding Fix](#make_reportpy-color-coding-fix)
2. [Unified Transcription Management (NEW)](#unified-transcription-management)
3. [Overlapping Video Segmentation with Output Merging (NEW)](#overlapping-video-segmentation-with-output-merging)

---

## make_report.py Color Coding Fix

The `make_report.py` script has been updated with improved word alignment logic.

### Status

✅ **EC2 Version (COMPLETED)**:
- File: `/home/ubuntu/VSP-LLM/scripts/make_report.py` - UPDATED
- Used by: Main pipeline and vsp-ui web interface
- Status: Ready to use

⏳ **Linux Container Version (PENDING)**:
- File: `/workspace/VSP-LLM/scripts/make_report.py` - NEEDS UPDATE
- Action required: Apply patch file (see instructions below)

---

## Quick Apply (Recommended)

### Step 1: Copy Files to Linux Container

Copy these two files to the Linux container:
```bash
# From EC2 to Linux container
scp /home/ubuntu/make_report_color_fix.patch user@container:/tmp/
scp /home/ubuntu/apply_linux_container_fix.sh user@container:/tmp/
```

### Step 2: Run the Patch Script

On the Linux container:
```bash
cd /tmp
chmod +x apply_linux_container_fix.sh
./apply_linux_container_fix.sh
```

The script will:
- Create a timestamped backup of the original file
- Apply the patch automatically
- Verify the changes

### Alternative: Manual Patch Application

If the script doesn't work, apply the patch manually:
```bash
cd /workspace/VSP-LLM
patch -p1 < /tmp/make_report_color_fix.patch
```

---

## File Location (Linux Container)
`/workspace/VSP-LLM/scripts/make_report.py`

### Changes Required

Replace the `align()` function (around line 24-57) with the following:

```python
def align(ref: str, hyp: str) -> List[Tuple[str, str]]:
    """
    Return list of (word, tag) for hypothesis words.
    tag in {"ok","ins","rep"}.
    - ok (green): right word, right place
    - rep (yellow): word appears in reference, but wrong place
    - ins (red): word doesn't appear in reference at all (made up)
    """
    r = toks(ref)
    h = toks(hyp)

    # Build a multiset (counter) of reference words for lookup
    ref_words = {}
    for w in r:
        ref_words[w] = ref_words.get(w, 0) + 1

    tagged: List[Tuple[str, str]] = []

    for i, hyp_word in enumerate(h):
        # Check if word is in correct position
        if i < len(r) and hyp_word == r[i]:
            tagged.append((hyp_word, "ok"))
        # Check if word appears anywhere in reference
        elif hyp_word in ref_words:
            tagged.append((hyp_word, "rep"))
        # Word doesn't appear in reference at all
        else:
            tagged.append((hyp_word, "ins"))

    return tagged
```

### What Changed

**Old behavior** (using difflib.SequenceMatcher):
- Used sequence alignment operations (equal/insert/replace/delete)
- Marked misaligned words as "yellow" even if they were completely made up
- Poor alignment quality threshold approach was unreliable

**New behavior**:
- **Green (ok)**: Word matches the reference at the same position
- **Yellow (rep)**: Word appears somewhere in the reference but wrong position
- **Red (ins)**: Word doesn't appear in the reference at all

This properly handles cases like the brightened video where the model outputs garbage (e.g., "yeah yeah yeah...") - these are now correctly marked as RED instead of YELLOW.

### Testing

After applying the change, regenerate a report to verify:
```bash
cd /workspace/VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate
python scripts/make_report.py --jsonl decode/vsr/en/hypo-*.json --out_dir decode/vsr/en/
```

Check the HTML report - words should now be colored based on whether they appear in the reference, not based on sequence alignment.

---

## Unified Transcription Management

**Added:** January 25, 2026  
**Status:** ⏳ PENDING Linux Container Implementation

### Overview

The unified transcription management system allows persistent storage of all transcriptions (both manual and Whisper auto-generated). This enables:
- ✅ Whisper runs only ONCE per video (huge time savings!)
- ✅ Manual transcription entry for videos with bad audio
- ✅ Edit any transcription (auto or manual)
- ✅ Transcriptions persist across pipeline runs
- ✅ Orphaned transcription management

### Key Benefits

**Performance:** On subsequent pipeline runs, Whisper skips videos that already have transcriptions, reducing processing time by 30-120 seconds per video.

**Flexibility:** Users can manually enter or edit transcriptions for videos where Whisper performs poorly.

**Persistence:** All transcriptions survive pipeline archiving and video removal/re-addition.

### Architecture

**Storage Location:** `~/vsp_input/.transcriptions/`
- One `.wrd` file per video (one word per line, lowercase, alphanumeric)
- `metadata.json` tracks type (auto/manual), timestamps, word counts
- Survives pipeline archiving

**Pipeline Integration:**
- **Step 0.6** (NEW): Copies `.transcriptions/*.wrd` → `flat_wrd/` BEFORE Whisper
- **Step 1.5** (NEW): Saves new Whisper outputs → `.transcriptions/` AFTER ASR
- Whisper automatically skips videos with existing .wrd files

**UI Features:**
- Modal dialog for entering/editing transcriptions
- Badges: `[AUTO]` (orange) for Whisper, `[MANUAL]` (green) for user-entered
- Orphaned transcriptions section with Keep/Delete actions
- Live preview of normalized text

### Files to Modify

| File | Type | Description |
|------|------|-------------|
| `/workspace/vsp-ui/app/services/transcription_manager.py` | **NEW** | Core transcription business logic (327 lines) |
| `/workspace/vsp-ui/app/server.py` | MODIFY | Add 4 API endpoints, ~100 lines |
| `/workspace/vsp-ui/app/services/validator.py` | MODIFY | Add fields + helper function, ~30 lines |
| `/workspace/run_flat_english_pipeline.sh` | MODIFY | Add Steps 0.6 and 1.5, ~65 lines |
| `/workspace/vsp-ui/app/static/index.html` | MODIFY | Add modal + orphaned section, ~50 lines |
| `/workspace/vsp-ui/app/static/app.js` | MODIFY | Add functions + event listeners, ~230 lines |
| `/workspace/vsp-ui/app/static/style.css` | MODIFY | Add styling, ~300 lines |

### Quick Implementation Guide

See **detailed step-by-step guide** in attached file: `/home/ubuntu/transcription_update_steps.md`

#### Summary of Steps:

1. **Create TranscriptionManager** - New Python service for managing .wrd files
2. **Update server.py** - Add 3 API endpoints (GET/POST transcription, GET orphaned)
3. **Update validator.py** - Add transcription fields to VideoInfo dataclass
4. **Update pipeline script** - Add Steps 0.6 (pre-copy) and 1.5 (post-save)
5. **Update index.html** - Add modal dialog and orphaned transcriptions section
6. **Update app.js** - Add modal logic, event handlers, orphan management
7. **Update style.css** - Add modal styling, badges, responsive design
8. **Test implementation** - Verify all features work correctly

### Testing Checklist

After implementation, verify:

- [ ] API endpoints respond correctly
- [ ] Modal opens when clicking "Add/Edit Transcription"
- [ ] Badges show [AUTO] (orange) and [MANUAL] (green)
- [ ] Live preview updates as you type
- [ ] Save creates `.wrd` file in `.transcriptions/`
- [ ] Pipeline Step 0.6 copies existing transcriptions
- [ ] Pipeline Step 1 (ASR) shows `[SKIP]` messages
- [ ] Pipeline Step 1.5 saves new transcriptions
- [ ] Orphaned section appears when video removed
- [ ] Keep/Delete buttons work on orphans
- [ ] Editing [AUTO] → warns and converts to [MANUAL]
- [ ] Transcriptions persist across pipeline runs

### Expected Performance

**Before Update:**
- Every pipeline run: Whisper processes all videos (~30-120s each)

**After Update:**
- First run: Normal Whisper processing
- Subsequent runs: Whisper SKIPS existing videos (almost instant)
- Time saved: 30-120 seconds per video per run

### Troubleshooting

Common issues and solutions:

**Module import errors:**
- Check `transcription_manager.py` is in correct location
- Verify `__init__.py` exists in services directory

**Modal doesn't open:**
- Check browser console for JavaScript errors
- Verify modal HTML is before `<script>` tag

**Whisper still running:**
- Verify Step 0.6 runs BEFORE Step 1
- Check .wrd files are in `flat_wrd/` before ASR

**API 404 errors:**
- Verify routes added to both `do_GET()` and `do_POST()`
- Restart VSP UI server

### Data Flow Examples

**First Run:**
```
video1.mp4 → Whisper transcribes → .transcriptions/video1.wrd [AUTO]
```

**Second Run (same video):**
```
video1.mp4 → Step 0.6 copies existing .wrd → Whisper SKIPS ✓
```

**Manual Entry:**
```
video2.mp4 → User clicks "Add Transcription" → [MANUAL]
Next run → Whisper SKIPS, uses manual transcription ✓
```

**Edit Auto Transcription:**
```
video1.mp4 [AUTO] → User edits → Confirms → [MANUAL]
```

**Orphan Management:**
```
Remove video2.mp4 → Shows in orphaned section
User clicks [Keep] or [Delete]
```

### Source Files (EC2)

Reference these EC2 files for correct implementation:

- `/home/ubuntu/vsp-ui/app/services/transcription_manager.py`
- `/home/ubuntu/vsp-ui/app/server.py` (lines 27-31, 78-82, 115-118, 327-418)
- `/home/ubuntu/vsp-ui/app/services/validator.py` (lines 16-20, 30-33, 208-230, 320-330)
- `/home/ubuntu/run_flat_english_pipeline.sh` (lines 276-318, 333-357)
- `/home/ubuntu/vsp-ui/app/static/index.html` (lines 85-91, 200-243)
- `/home/ubuntu/vsp-ui/app/static/app.js` (lines 12-14, 229-268, 315-523, 1005-1025)
- `/home/ubuntu/vsp-ui/app/static/style.css` (lines 673-973)

### Documentation

Complete documentation added to:
- `/home/ubuntu/CLAUDE.md` - Architecture and data flow sections updated
- `/home/ubuntu/transcription_update_steps.md` - Detailed implementation guide

### Notes

- Manual transcriptions are NEVER overwritten by Whisper
- `.transcriptions/` directory is NOT archived by pipeline
- Editing [AUTO] transcription converts it to [MANUAL] with confirmation
- Transcriptions persist when videos are removed and re-added
- Text normalization matches ASR format (lowercase, alphanumeric + apostrophes)

---

## Overlapping Video Segmentation with Output Merging

**Added:** January 25, 2026
**Status:** ⏳ PENDING Linux Container Implementation

### Overview

The overlapping segmentation system improves transcription quality at segment boundaries by:
- ✅ Splitting videos >8 seconds into overlapping 4-second segments (1-second overlap)
- ✅ Maintaining consistent context across segment boundaries
- ✅ Merging predictions intelligently with conflict detection
- ✅ Reporting disagreements between overlapping predictions
- ✅ Easy toggle on/off via single environment variable

### Key Benefits

**Quality:** Reduces word-level discontinuities at segment boundaries where non-overlapping segmentation can cause transcription errors.

**Transparency:** When predictions differ in overlap regions, both alternatives are reported explicitly along with the chosen prediction.

**Modularity:** Completely independent modules that don't modify existing pipeline code. Can be disabled with `OVERLAP_ENABLED=0`.

**Performance:** Adds ~33% processing time (acceptable tradeoff for improved quality).

### Architecture

#### Segmentation Logic

**Parameters:**
- Base segment duration: 4 seconds (100 frames at 25fps)
- Overlap duration: 1.0 second (25 frames)
- Effective stride: 3 seconds (segment_duration - overlap)
- Minimum video length for splitting: 8 seconds

**Example for 10-second video:**
```
Video: [0s -------------------- 10s]
Seg 0: [0s ---- 4s]  (frames 0-100)
Seg 1:      [3s ------- 7s]  (frames 75-175)
Seg 2:           [6s -------- 10s]  (frames 150-250)

Overlap regions:
- Seg 0 & Seg 1: [3s-4s] (1 second, 25 frames)
- Seg 1 & Seg 2: [6s-7s] (1 second, 25 frames)
```

**Segment Naming Convention:**
```
New format: {video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}__{hash}.mp4

Examples:
video_00_000000_000100__abc123.mp4  (0-4s, frames 0-100)
video_01_000075_000175__abc123.mp4  (3-7s, frames 75-175)
video_02_000150_000250__abc123.mp4  (6-10s, frames 150-250)
```

#### Merge Algorithm

**Strategy:** Word-level agreement-based merging with conflict reporting

For each overlapping region:
1. **Compare predictions** using Levenshtein similarity (normalized, case-insensitive)
2. **If similar (>85% match):** Choose one prediction without conflict
3. **If different:** Report both predictions AND choose by segment center distance

**Segment Center Heuristic:**
```python
# For 4-second segments with 1-second overlap
seg1_center = seg1_start_sec + 2.0  # Center of first segment
seg2_center = seg2_start_sec + 2.0  # Center of second segment
overlap_midpoint = (overlap_start_sec + overlap_end_sec) / 2

# Choose prediction from segment whose center is closest to overlap midpoint
if abs(seg1_center - overlap_midpoint) < abs(seg2_center - overlap_midpoint):
    use_seg1_prediction()
else:
    use_seg2_prediction()
```

**Conflict Detection Output:**
```json
{
  "video_id": "example_video",
  "merged_hypo": "complete merged transcription",
  "segments_used": [0, 1, 2],
  "conflicts": [
    {
      "overlap_time": [3.0, 4.0],
      "chosen_text": "the quick brown",
      "chosen_source": "segment_0",
      "alternate_text": "the quick red",
      "alternate_source": "segment_1",
      "similarity": 0.733
    }
  ]
}
```

### Module Architecture

**Design Philosophy:** All new functionality is implemented as completely independent modules. Toggle with `OVERLAP_ENABLED` environment variable.

```
Existing Pipeline (unchanged)          New Modules (independent)
├── preprocess_lrs2lrs3.py      →     ├── overlapping_segmentation.py
├── make_simple_manifest.py     →     ├── generate_segment_timing.py
├── vsp_llm_decode.py           →     ├── merge_overlapping_predictions.py
├── make_report.py              →     ├── make_report_wrapper.sh
└── make_burn.py                →     └── make_burn_wrapper.sh
```

### Files to Create/Modify

#### New Files (7 independent modules)

| File | Type | Lines | Description |
|------|------|-------|-------------|
| `/workspace/auto_avsr/preparation/overlapping_segmentation.py` | **NEW** | ~130 | Core segmentation logic with overlap support |
| `/workspace/auto_avsr/preparation/preprocess_with_overlap.py` | **NEW** | ~343 | Preprocessing wrapper for overlapping segments |
| `/workspace/auto_avsr/generate_segment_timing.py` | **NEW** | ~160 | Timing metadata generator (runs after manifest) |
| `/workspace/VSP-LLM/scripts/merge_overlapping_predictions.py` | **NEW** | ~300 | Core merge algorithm with conflict detection |
| `/workspace/VSP-LLM/scripts/generate_conflict_report.py` | **NEW** | ~150 | Conflict report generator (JSON/HTML/text) |
| `/workspace/VSP-LLM/scripts/make_report_wrapper.sh` | **NEW** | ~30 | Report wrapper that detects merged output |
| `/workspace/VSP-LLM/scripts/make_burn_wrapper.sh` | **NEW** | ~25 | Video burning wrapper for merged predictions |

#### Modified Files (Pipeline + UI)

| File | Type | Changes | Description |
|------|------|---------|-------------|
| `/workspace/run_flat_english_pipeline.sh` | MODIFY | ~130 lines | Add 5 conditional blocks for overlap modules |
| `/workspace/vsp-ui/app/static/index.html` | MODIFY | ~15 lines | Add overlap checkbox in Segmentation Options |
| `/workspace/vsp-ui/app/static/app.js` | MODIFY | ~3 lines | Extract checkbox value and pass to API |
| `/workspace/vsp-ui/app/server.py` | MODIFY | ~5 lines | Accept overlap_enabled parameter |
| `/workspace/vsp-ui/app/services/pipeline_runner.py` | MODIFY | ~10 lines | Add overlap_enabled parameter + env variable |

### Implementation Details

#### 1. Core Segmentation Module

**File:** `/workspace/auto_avsr/preparation/overlapping_segmentation.py`

**Key Function:**
```python
def split_video_by_time(
    video_duration: float,
    segment_duration: float = 4.0,
    overlap_duration: float = 1.0,
    min_split_duration: float = 8.0,
    fps: float = 25.0
) -> List[Tuple[float, float, int, int]]:
    """
    Split video into overlapping time-based segments.

    Returns:
        List of (start_time, end_time, start_frame, end_frame) tuples
    """
    # If video shorter than minimum, return single segment
    if video_duration < min_split_duration:
        end_frame = int(video_duration * fps)
        return [(0.0, video_duration, 0, end_frame)]

    stride = segment_duration - overlap_duration
    segments = []
    current_start = 0.0

    while current_start < video_duration:
        segment_end = min(current_start + segment_duration, video_duration)
        start_frame = int(current_start * fps)
        end_frame = int(segment_end * fps)
        segments.append((current_start, segment_end, start_frame, end_frame))
        current_start += stride
        if segment_end >= video_duration:
            break

    return segments
```

#### 2. Timing Metadata Generator

**File:** `/workspace/auto_avsr/generate_segment_timing.py`

**Purpose:** Extracts timing from filenames and detects overlaps

**Key Function:**
```python
def parse_segment_filename(filename: str) -> Optional[Dict]:
    """Extract timing from segment filename."""
    # Handle video extensions
    if filename.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
        basename = Path(filename).stem
    else:
        basename = filename

    # Pattern: {id}__{hash}_{idx}_{start}_{end}
    pattern = r'^(.+?)__([a-f0-9]{8})_(\d{2})_(\d{6})_(\d{6})$'
    match = re.match(pattern, basename)
    if match:
        return {
            'video_id': match.group(1),
            'hash': match.group(2),
            'seg_idx': int(match.group(3)),
            'start_frame': int(match.group(4)),
            'end_frame': int(match.group(5)),
            'full_id': f"{match.group(1)}__{match.group(2)}"
        }
    return None
```

**Output:** `segment_timing.json`
```json
{
  "utt_id": {
    "video_id": "base_video_id",
    "full_id": "video_id__hash",
    "segment_index": 0,
    "start_frame": 0,
    "end_frame": 100,
    "start_sec": 0.0,
    "end_sec": 4.0,
    "duration": 4.0,
    "overlaps_with": [1]
  }
}
```

#### 3. Merge Module

**File:** `/workspace/VSP-LLM/scripts/merge_overlapping_predictions.py`

**Key Algorithm:**
```python
def merge_segment_pair(seg1: Dict, seg2: Dict) -> Tuple[str, Optional[Dict]]:
    """Merge two overlapping segments with conflict detection."""
    hypo1, hypo2 = seg1['hypo'], seg2['hypo']

    # Normalize and compare
    norm1 = normalize_text(hypo1)
    norm2 = normalize_text(hypo2)
    similarity = calculate_similarity(norm1, norm2)

    # Agreement: similarity > 0.85
    if similarity > 0.85:
        return hypo1, None  # No conflict

    # Disagreement: choose by segment center distance
    overlap_mid = (seg2['start_sec'] + seg1['end_sec']) / 2
    seg1_center = seg1['start_sec'] + 2.0
    seg2_center = seg2['start_sec'] + 2.0

    if abs(seg1_center - overlap_mid) < abs(seg2_center - overlap_mid):
        chosen = hypo1
        chosen_src = f"segment_{seg1['seg_idx']}"
        alternate = hypo2
        alternate_src = f"segment_{seg2['seg_idx']}"
    else:
        chosen = hypo2
        chosen_src = f"segment_{seg2['seg_idx']}"
        alternate = hypo1
        alternate_src = f"segment_{seg1['seg_idx']}"

    # Record conflict
    conflict = {
        'overlap_time': [round(seg2['start_sec'], 2), round(seg1['end_sec'], 2)],
        'chosen_text': chosen,
        'chosen_source': chosen_src,
        'alternate_text': alternate,
        'alternate_source': alternate_src,
        'similarity': round(similarity, 3)
    }

    return chosen, conflict
```

**Text Normalization:**
```python
def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase
    text = text.lower()
    # Remove punctuation except apostrophes
    text = re.sub(r"[^\w\s']", '', text)
    # Collapse whitespace
    text = ' '.join(text.split())
    return text
```

#### 4. Pipeline Integration

**File:** `/workspace/run_flat_english_pipeline.sh`

**Modification 1:** Configuration (lines 26-30)
```bash
# Overlapping segmentation configuration
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"  # Default: enabled
OVERLAP_DURATION="1.0"
MIN_SPLIT_DURATION="8.0"
export OVERLAP_ENABLED
```

**Modification 2:** Conditional preprocessing (lines ~378-420)
```bash
########################
# STEP 3: Preprocessing with optional overlap
########################
if [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [3a] Running preprocess_with_overlap.py (overlap=1s)"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python preprocess_with_overlap.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration 4 \
      --overlap-duration "$OVERLAP_DURATION" \
      --min-split-duration "$MIN_SPLIT_DURATION" \
      --groups 1 \
      --job-index 0

    deactivate
    echo ">>> [INFO] Overlapping segments + metadata in: $PREP_ROOT"
else
    echo ">>> [3b] Running preprocess_lrs2lrs3.py (standard, no overlap)"

    source "$PREP_VENV/bin/activate"
    cd "$AUTO_AVSR/preparation"

    python preprocess_lrs2lrs3.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration 4 \
      --groups 1 \
      --job-index 0

    deactivate
    echo ">>> [INFO] Standard mouth crops in: $PREP_ROOT"
fi
```

**Modification 3:** Timing metadata generation (after line ~420)
```bash
########################
# STEP 5a: Generate segment timing metadata (if overlap enabled)
########################
if [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [5a] Generating segment timing metadata..."

    python "$AUTO_AVSR/generate_segment_timing.py" \
      --manifest-tsv "$MANIFEST_ROOT/train.tsv" \
      --segment-metadata "$PREP_ROOT/segment_metadata.json" \
      --output-json "$MANIFEST_ROOT/segment_timing.json"

    echo ">>> [INFO] Timing metadata saved to: $MANIFEST_ROOT/segment_timing.json"
else
    echo ">>> [5a] Skipping segment timing (overlap disabled)"
fi
```

**Modification 4:** Merge predictions (after decode, line ~481)
```bash
########################
# STEP 8a: Merge overlapping predictions (if enabled)
########################
if [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [8a] Merging overlapping predictions..."

    source "$VSP_VENV/bin/activate"

    # Find latest decode output
    DECODE_OUTPUT=$(ls -t "$VSP/decode/vsr/en/hypo-*.json" 2>/dev/null | head -n1)

    if [ -f "$DECODE_OUTPUT" ] && [ -f "$MANIFEST_ROOT/segment_timing.json" ]; then
        DECODE_ID=$(basename "$DECODE_OUTPUT" | sed 's/hypo-\(.*\)\.json/\1/')

        python "$VSP/scripts/merge_overlapping_predictions.py" \
          --decode-json "$DECODE_OUTPUT" \
          --timing-json "$MANIFEST_ROOT/segment_timing.json" \
          --output-json "$VSP/decode/vsr/en/hypo-${DECODE_ID}-merged.json"

        echo ">>> [INFO] Merged output: hypo-${DECODE_ID}-merged.json"
    else
        echo ">>> [WARNING] Could not merge: missing decode output or timing metadata"
        export OVERLAP_ENABLED=0  # Disable for downstream steps
    fi

    deactivate
else
    echo ">>> [8a] Skipping merge (overlap disabled)"
fi
```

**Modification 5:** Report/burn wrappers (lines ~494-502)
```bash
########################
# STEP 9: Generate reports and burn videos
########################
DECODE_JSON="$(ls -t ${VSP}/decode/vsr/en/hypo-*.json | grep -v "merged" | head -n 1)"

if [ "$OVERLAP_ENABLED" = "1" ]; then
    echo ">>> [9] Using wrapper scripts (merged output if available)"

    bash "$VSP/scripts/make_report_wrapper.sh" \
        "$DECODE_JSON" \
        "${ARCHIVE_ROOT}/client_outputs/report"

    bash "$VSP/scripts/make_burn_wrapper.sh" \
        "$DECODE_JSON" \
        "$FLAT_VID_DIR" \
        "${ARCHIVE_ROOT}/client_outputs/burned_videos"
else
    echo ">>> [9] Using standard scripts (segment-level output)"

    python "$VSP/scripts/make_report.py" \
        --decode-json "$DECODE_JSON" \
        --output-dir "${ARCHIVE_ROOT}/client_outputs/report"

    python "$VSP/scripts/make_burn.py" \
        --decode-json "$DECODE_JSON" \
        --video-dir "$FLAT_VID_DIR" \
        --output-dir "${ARCHIVE_ROOT}/client_outputs/burned_videos"
fi
```

#### 5. UI Integration

**File:** `/workspace/vsp-ui/app/static/index.html`

Add checkbox under "Segmentation Options" section:
```html
<div class="processing-options">
    <h3>Segmentation Options</h3>

    <!-- Existing K-means options -->
    <div class="kmeans-options">
        <!-- ... existing k-means checkboxes ... -->
    </div>

    <!-- NEW: Overlap segmentation option -->
    <div class="overlap-options">
        <label class="checkbox-label">
            <input type="checkbox" id="overlap-enabled" checked>
            <span>Enable overlapping segments for videos &gt;8s</span>
            <span class="tooltip-icon" title="Improves transcription quality at segment boundaries by using 1-second overlap between segments. Adds ~33% processing time.">ℹ️</span>
        </label>
    </div>
</div>
```

**File:** `/workspace/vsp-ui/app/static/app.js`

Extract checkbox value (around line 636):
```javascript
async function startProcessing() {
    // ... existing code ...
    const kmeansMode = document.querySelector('input[name="kmeans-mode"]:checked').value;
    const overlapEnabled = document.getElementById('overlap-enabled').checked;  // NEW

    const result = await api('start', 'POST', {
        train_kmeans: trainKmeans,
        golden_model: goldenModel,
        overlap_enabled: overlapEnabled  // NEW
    });
    // ... rest of function ...
}
```

**File:** `/workspace/vsp-ui/app/server.py`

Accept parameter (around line 243):
```python
def handle_start(self, data: Dict[str, Any] = None):
    if data is None:
        data = {}
    train_kmeans = data.get('train_kmeans', True)
    golden_model = data.get('golden_model', None)
    overlap_enabled = data.get('overlap_enabled', True)  # NEW

    success = runner.start(
        train_kmeans=train_kmeans,
        golden_model=golden_model,
        overlap_enabled=overlap_enabled  # NEW
    )
```

**File:** `/workspace/vsp-ui/app/services/pipeline_runner.py`

Add parameter and environment variable:
```python
# Line ~62: Add parameter
def start(
    self,
    on_progress: Optional[Callable] = None,
    train_kmeans: bool = True,
    golden_model: Optional[str] = None,
    overlap_enabled: bool = True,  # NEW
) -> bool:

# Line ~101: Store value
self._overlap_enabled = overlap_enabled

# Line ~277: Pass to environment
def _get_env(self) -> dict:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # ... existing k-means logic ...
    env["OVERLAP_ENABLED"] = "1" if self._overlap_enabled else "0"  # NEW
    return env
```

### Testing the Implementation

#### Stage 1: Test Preprocessing Module
```bash
cd /workspace/auto_avsr/preparation

# Test with 10-second video
python preprocess_with_overlap.py \
  --data-dir /path/to/test/video \
  --root-dir /tmp/overlap_test \
  --dataset flat \
  --detector mediapipe \
  --seg-duration 4 \
  --overlap-duration 1.0 \
  --min-split-duration 8.0

# Verify outputs
ls -la /tmp/overlap_test/flat/flat_video_seg4s/*.mp4
# Should see filenames with frame ranges: *_00_000000_000100.mp4, *_01_000075_000175.mp4, etc.

cat /tmp/overlap_test/segment_metadata.json
# Should show timing info for all segments
```

#### Stage 2: Test Timing Metadata
```bash
# Create mock manifest
echo -e "/workspace/auto_avsr\tvideo_00_000000_000100__abc12345.mp4\taudio.wav\t100" > /tmp/test.tsv

python /workspace/auto_avsr/generate_segment_timing.py \
  --manifest-tsv /tmp/test.tsv \
  --segment-metadata /tmp/overlap_test/segment_metadata.json \
  --output-json /tmp/segment_timing.json

cat /tmp/segment_timing.json
# Should show utt_id mappings with frame ranges and overlaps_with arrays
```

#### Stage 3: Test Merge Module
```bash
# Create mock decode output
cat > /tmp/mock_decode.json << 'EOF'
{
  "utt_id": ["vid_00_000000_000100__hash", "vid_01_000075_000175__hash"],
  "hypo": ["the quick brown fox", "brown fox jumps over"],
  "ref": ["...", "..."],
  "instruction": ["...", "..."]
}
EOF

python /workspace/VSP-LLM/scripts/merge_overlapping_predictions.py \
  --decode-json /tmp/mock_decode.json \
  --timing-json /tmp/segment_timing.json \
  --output-json /tmp/merged.json

cat /tmp/merged.json
# Should show merged_hypo and conflicts array
```

#### Stage 4: Full Pipeline Test
```bash
# Enable overlap and run pipeline
OVERLAP_ENABLED=1 /workspace/run_flat_english_pipeline.sh /path/to/test/videos

# Verify all stages completed
grep -E "(3a|5a|8a)" /workspace/flat_runs_latest.log

# Check outputs
ls -la /workspace/auto_avsr/preprocessed_flat_seg4/segment_metadata.json
ls -la /workspace/auto_avsr/preprocessed_flat_seg4/433h_data/segment_timing.json
ls -la /workspace/VSP-LLM/decode/vsr/en/hypo-*-merged.json
```

### Quick Reference Commands

**Enable overlapping segmentation (default):**
```bash
# Method 1: Use default
/workspace/run_flat_english_pipeline.sh /path/to/videos

# Method 2: Explicitly enable
OVERLAP_ENABLED=1 /workspace/run_flat_english_pipeline.sh /path/to/videos
```

**Disable overlapping segmentation:**
```bash
# Disable for single run
OVERLAP_ENABLED=0 /workspace/run_flat_english_pipeline.sh /path/to/videos

# Disable permanently
export OVERLAP_ENABLED=0
/workspace/run_flat_english_pipeline.sh /path/to/videos
```

**Test individual modules:**
```bash
# Test preprocessing only
python /workspace/auto_avsr/preparation/preprocess_with_overlap.py --help

# Test timing generation only
python /workspace/auto_avsr/generate_segment_timing.py --help

# Test merge only
python /workspace/VSP-LLM/scripts/merge_overlapping_predictions.py --help
```

### Expected Performance Impact

| Stage | Time Impact | Storage Impact |
|-------|-------------|----------------|
| Preprocessing | +33% | +33% (more segment files) |
| K-means/Decode | +33% | Minimal (features regenerated) |
| Merge | <5 seconds | ~1MB per 1000 videos |
| Total Pipeline | +30-35% | +33% of segment storage |

### Troubleshooting

**Segments not being created:**
- Check video duration is >8 seconds (`MIN_SPLIT_DURATION`)
- Verify `OVERLAP_ENABLED=1` is set
- Check logs for errors in preprocessing step

**No merged output after decode:**
- Verify `segment_timing.json` exists in `433h_data/`
- Check decode output exists: `hypo-*.json`
- Look for merge errors in pipeline log

**Conflicts not showing in reports:**
- Verify merged JSON has `conflicts` array
- Check wrapper scripts are being called (not standard scripts)
- Ensure `generate_conflict_report.py` runs successfully

**UI checkbox not working:**
- Verify checkbox element exists with `id="overlap-enabled"`
- Check browser console for JavaScript errors
- Restart VSP UI server after changes

### Source Files (EC2 Reference)

For correct implementation, reference these EC2 files:

**New Modules:**
- `/home/ubuntu/auto_avsr/preparation/overlapping_segmentation.py`
- `/home/ubuntu/auto_avsr/preparation/preprocess_with_overlap.py`
- `/home/ubuntu/auto_avsr/generate_segment_timing.py`
- `/home/ubuntu/VSP-LLM/scripts/merge_overlapping_predictions.py`
- `/home/ubuntu/VSP-LLM/scripts/generate_conflict_report.py`
- `/home/ubuntu/VSP-LLM/scripts/make_report_wrapper.sh`
- `/home/ubuntu/VSP-LLM/scripts/make_burn_wrapper.sh`

**Modified Files:**
- `/home/ubuntu/run_flat_english_pipeline.sh` (lines 26-30, ~378-420, ~453-469, ~521-544, ~558-582)
- `/home/ubuntu/vsp-ui/app/static/index.html` (overlap checkbox section)
- `/home/ubuntu/vsp-ui/app/static/app.js` (line ~636)
- `/home/ubuntu/vsp-ui/app/server.py` (line ~243)
- `/home/ubuntu/vsp-ui/app/services/pipeline_runner.py` (lines ~62, ~101, ~277)

### Documentation

Complete documentation available at:
- `/home/ubuntu/.claude/plans/mutable-orbiting-mountain.md` - Full implementation plan
- `/home/ubuntu/PIPELINE_MODIFICATIONS.md` - Detailed pipeline modifications guide
- `/home/ubuntu/MODULE_TEST_RESULTS.md` - Comprehensive test results

### Notes

- **Zero modifications** to core pipeline files (preprocess_lrs2lrs3.py, make_simple_manifest.py, vsp_llm_decode.py, make_report.py, make_burn.py)
- All overlap functionality lives in separate modules
- Easy to disable: `OVERLAP_ENABLED=0`
- Easy to remove: delete new files, remove conditional calls from pipeline script
- Existing pipeline behavior unchanged when disabled
- Conflicts are reported transparently to users
- Manual transcriptions work normally with overlapping segments

