# SEGMENTATION_ENABLED Implementation Summary

## Overview
Implemented proper modular video segmentation control with `SEGMENTATION_ENABLED` flag. Users can now completely disable video segmentation and process videos as whole files.

## Implementation Date
January 29, 2026

## What Changed

### 1. Pipeline Script (`run_flat_english_pipeline.sh`)

**New Environment Variable:**
```bash
SEGMENTATION_ENABLED="${SEGMENTATION_ENABLED:-1}"  # 1=segment videos, 0=process whole videos
```

**Key Logic:**
- When `SEGMENTATION_ENABLED=1`: Videos segmented based on `SEG_DURATION` (default 12s)
- When `SEGMENTATION_ENABLED=0`: Videos processed as whole files (uses `seg-duration=99999` to prevent splitting)

**Files Modified:**
- `/home/ubuntu/run_flat_english_pipeline.sh` (EC2)
- `/home/ubuntu/vsp_docker/galaxy_export/run_flat_english_pipeline.sh` (Linux container)

**Changes:**
1. Added `SEGMENTATION_ENABLED` variable (line ~27)
2. Updated fast segmentation step (Step 0.1) to check `SEGMENTATION_ENABLED`
3. Updated preprocessing step (Step 2) to use `EFFECTIVE_SEG_DURATION`:
   - If segmentation enabled: `EFFECTIVE_SEG_DURATION = SEG_DURATION`
   - If segmentation disabled: `EFFECTIVE_SEG_DURATION = 99999`
4. Updated segment timing metadata generation (Step 5a)
5. Updated merge step messaging (Step 7a)

### 2. UI Changes (`vsp-ui/app/static/index.html`)

**Before:**
```html
<input type="checkbox" id="overlap-enabled" checked>
<span>Enable overlapping segments for videos >12s</span>
```

**After:**
```html
<input type="checkbox" id="segmentation-enabled" checked>
<span>Enable video segmentation</span>

<div id="overlap-options-container" style="margin-left: 24px;">
    <input type="checkbox" id="overlap-enabled" checked>
    <span>Enable overlapping segments for videos >24s</span>
</div>
```

**Behavior:**
- Main checkbox: Enable/disable video segmentation entirely
- Overlap checkbox: Only shown when segmentation is enabled
- When segmentation unchecked: Overlap options hidden

**Files Modified:**
- `/home/ubuntu/vsp-ui/app/static/index.html` (EC2)
- `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/static/index.html` (Linux container)

### 3. Frontend JavaScript (`vsp-ui/app/static/app.js`)

**New Logic:**
```javascript
// Show/hide overlap options based on segmentation checkbox
const segmentationCheckbox = document.getElementById('segmentation-enabled');
const overlapContainer = document.getElementById('overlap-options-container');

segmentationCheckbox.addEventListener('change', (e) => {
    overlapContainer.style.display = e.target.checked ? 'block' : 'none';
});
```

**API Calls Updated:**
All pipeline start calls now pass `segmentation_enabled`:
```javascript
await api('start', 'POST', {
    segmentation_enabled: segmentationEnabled,
    overlap_enabled: overlapEnabled,
    train_kmeans: trainKmeans,
    golden_model: goldenModel,
    segment_only: segmentOnly
});
```

**Files Modified:**
- `/home/ubuntu/vsp-ui/app/static/app.js` (EC2)
- `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/static/app.js` (Linux container)

### 4. Backend Service (`vsp-ui/app/services/pipeline_runner.py`)

**Method Signature Updated:**
```python
def start(
    self,
    on_progress: Optional[Callable] = None,
    train_kmeans: bool = True,
    golden_model: Optional[str] = None,
    segmentation_enabled: bool = True,  # NEW PARAMETER
    overlap_enabled: bool = True,
    segment_only: bool = True,
) -> bool:
```

**Environment Variable Set:**
```python
env["SEGMENTATION_ENABLED"] = "1" if self._segmentation_enabled else "0"
env["OVERLAP_ENABLED"] = "1" if self._overlap_enabled else "0"
```

**Files Modified:**
- `/home/ubuntu/vsp-ui/app/services/pipeline_runner.py` (EC2)
- `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/services/pipeline_runner.py` (Linux container)

### 5. Server API (`vsp-ui/app/server.py`)

**Request Handling:**
```python
segmentation_enabled = data.get('segmentation_enabled', True)
overlap_enabled = data.get('overlap_enabled', True)

success = runner.start(
    train_kmeans=train_kmeans,
    golden_model=golden_model,
    segmentation_enabled=segmentation_enabled,
    overlap_enabled=overlap_enabled,
    segment_only=segment_only
)
```

**Files Modified:**
- `/home/ubuntu/vsp-ui/app/server.py` (EC2)
- `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/server.py` (Linux container)

## How It Works

### When Segmentation is ENABLED (default):
1. Videos split into 12s segments with 2s overlap (if overlap enabled)
2. Each segment processed independently through pipeline
3. Segment-level outputs (reports, burned videos)

### When Segmentation is DISABLED:
1. Videos processed as whole files (no splitting)
2. `seg-duration` set to 99999 internally
3. Preprocessing treats all videos as "too short to split"
4. One output per original video (no segments)

## Testing

### Test Case 1: Segmentation Enabled
```bash
# UI: Check "Enable video segmentation" + "Enable overlapping segments"
# Expected: Videos split into 12s segments with 2s overlap
```

### Test Case 2: Segmentation Enabled, Overlap Disabled
```bash
# UI: Check "Enable video segmentation", Uncheck overlap
# Expected: Videos split into 12s segments without overlap
```

### Test Case 3: Segmentation Disabled
```bash
# UI: Uncheck "Enable video segmentation"
# Expected: Videos processed as whole files, overlap checkbox hidden
```

### Manual Testing (Command Line)
```bash
# Test segmentation disabled
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh ~/vsp_input

# Test segmentation enabled with overlap
SEGMENTATION_ENABLED=1 OVERLAP_ENABLED=1 ./run_flat_english_pipeline.sh ~/vsp_input

# Test segmentation enabled without overlap
SEGMENTATION_ENABLED=1 OVERLAP_ENABLED=0 ./run_flat_english_pipeline.sh ~/vsp_input
```

## Benefits

✅ **Truly modular**: Clean flag to enable/disable segmentation
✅ **No workarounds**: Proper implementation, not hacks
✅ **Backward compatible**: Defaults to enabled (existing behavior)
✅ **User-friendly**: Clear UI with conditional visibility
✅ **Consistent**: Same behavior across EC2 and Linux container

## Migration Notes

**Old Behavior (broken):**
- Checkbox only controlled overlap, not segmentation
- No way to disable segmentation entirely
- Confusing UX ("why are videos still segmented?")

**New Behavior (fixed):**
- Main checkbox controls segmentation on/off
- Overlap checkbox only visible when segmentation enabled
- Clear and expected behavior

## Documentation Updates Needed

Add to `/home/ubuntu/CLAUDE.md` under "Pending Changes for Linux Container Version":

### SEGMENTATION_ENABLED Feature (Added Jan 29, 2026)
- Proper modular control for video segmentation
- New checkbox: "Enable video segmentation" (master control)
- Overlap checkbox now conditional (only shown when segmentation enabled)
- When disabled: Videos processed as whole files (seg_duration=99999 internally)
- Applied to both EC2 and Linux container versions

## Files Changed Summary

### EC2 Version:
1. `/home/ubuntu/run_flat_english_pipeline.sh`
2. `/home/ubuntu/vsp-ui/app/static/index.html`
3. `/home/ubuntu/vsp-ui/app/static/app.js`
4. `/home/ubuntu/vsp-ui/app/services/pipeline_runner.py`
5. `/home/ubuntu/vsp-ui/app/server.py`

### Linux Container Version:
1. `/home/ubuntu/vsp_docker/galaxy_export/run_flat_english_pipeline.sh`
2. `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/static/index.html`
3. `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/static/app.js`
4. `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/services/pipeline_runner.py`
5. `/home/ubuntu/vsp_docker/galaxy_export/vsp-ui/app/server.py`

## Total Lines Changed: ~150 across 10 files

## Status: ✅ COMPLETE
All changes applied to both EC2 and Linux container versions. Ready for testing.
