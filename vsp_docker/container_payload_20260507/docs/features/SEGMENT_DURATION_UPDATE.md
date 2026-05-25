# Segment Duration Update for Linux Container

## Overview
Update default segment duration from 4 seconds to 12 seconds across the entire codebase.
This ensures consistency between pipeline script, backend config, and frontend UI.

## Date: 2026-01-25

---

## File 1: `/workspace/run_flat_english_pipeline.sh`

### Change 1: Update SEG_DURATION and MIN_SPLIT_DURATION defaults

**Location:** Lines ~23-30

**Before:**
```bash
DATA_NAME="flat"
LANG="en"
SEG_DURATION="4"  # Segment duration in seconds

# Overlapping segmentation configuration
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"  # Default: enabled
OVERLAP_DURATION="1.0"  # Hardcoded optimal value
MIN_SPLIT_DURATION="8.0"  # Hardcoded optimal value
```

**After:**
```bash
DATA_NAME="flat"
LANG="en"
SEG_DURATION="${SEG_DURATION:-12}"  # Segment duration in seconds

# Overlapping segmentation configuration
OVERLAP_ENABLED="${OVERLAP_ENABLED:-1}"  # Default: enabled
OVERLAP_DURATION="1.0"  # Hardcoded optimal value
MIN_SPLIT_DURATION="24.0"  # Hardcoded optimal value (2x SEG_DURATION)
export OVERLAP_ENABLED SEG_DURATION
```

**Note:** Also add `export OVERLAP_ENABLED SEG_DURATION` if not present

---

### Change 2: Use variable instead of hardcoded value (preprocess_with_overlap.py)

**Location:** Lines ~306-317 (in the overlap-enabled branch)

**Before:**
```bash
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
```

**After:**
```bash
    python preprocess_with_overlap.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration "$SEG_DURATION" \
      --overlap-duration "$OVERLAP_DURATION" \
      --min-split-duration "$MIN_SPLIT_DURATION" \
      --groups 1 \
      --job-index 0
```

---

### Change 3: Use variable instead of hardcoded value (preprocess_lrs2lrs3.py)

**Location:** Lines ~327-336 (in the else branch for standard preprocessing)

**Before:**
```bash
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
```

**After:**
```bash
    python preprocess_lrs2lrs3.py \
      --data-dir "$READY_DIR" \
      --root-dir "$PREP_ROOT" \
      --dataset flat \
      --detector mediapipe \
      --gpu_type cuda \
      --subset train \
      --seg-duration "$SEG_DURATION" \
      --groups 1 \
      --job-index 0
```

---

### Change 4: Update echo message

**Location:** Line ~322

**Before:**
```bash
    echo ">>> [2] Running preprocess_lrs2lrs3.py (mediapipe, seg=4s, standard)"
```

**After:**
```bash
    echo ">>> [2] Running preprocess_lrs2lrs3.py (mediapipe, seg=${SEG_DURATION}s, standard)"
```

---

### Change 5: Fix SEG_DURATION unbound variable issue

**Location:** Line ~534 (client outputs section)

**Before:**
```bash
# Use preprocessed video directory (where segmented videos with audio are)
PROCESSED_VID_DIR="${PREP_ROOT}/${DATA_NAME}/${DATA_NAME}_video_seg${SEG_DURATION}s"
```

**After:**
No change needed if `export SEG_DURATION` was added in Change 1.
If the error persists, ensure SEG_DURATION is defined and exported early in the script.

---

## File 2: `/workspace/vsp-ui/app/config.py`

### Change: Add MIN_SPLIT_DURATION and update SEGMENT_DURATION

**Location:** Lines ~22-25 (Video validation section)

**Before:**
```python
# Video validation
SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}
SEGMENT_DURATION = 4  # seconds per segment
MIN_SEGMENTS_FOR_KMEANS = 200
```

**After:**
```python
# Video validation
SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}
SEGMENT_DURATION = 12  # seconds per segment
MIN_SPLIT_DURATION = 24.0  # minimum duration to trigger overlapping segments (2x SEGMENT_DURATION)
MIN_SEGMENTS_FOR_KMEANS = 200
```

---

## File 3: `/workspace/vsp-ui/app/services/validator.py`

### Change 1: Import MIN_SPLIT_DURATION

**Location:** Lines ~12-17

**Before:**
```python
from ..config import (
    INPUT_DIR,
    SUPPORTED_EXTENSIONS,
    SEGMENT_DURATION,
    MIN_SEGMENTS_FOR_KMEANS,
)
```

**After:**
```python
from ..config import (
    INPUT_DIR,
    SUPPORTED_EXTENSIONS,
    SEGMENT_DURATION,
    MIN_SPLIT_DURATION,
    MIN_SEGMENTS_FOR_KMEANS,
)
```

---

### Change 2: Add fields to ValidationResult dataclass

**Location:** Lines ~46-54

**Before:**
```python
@dataclass
class ValidationResult:
    valid_videos: List[VideoInfo]
    invalid_videos: List[VideoInfo]
    warnings: List[str]
    total_segments: int
    kmeans_viable: bool
    total_duration_seconds: float
```

**After:**
```python
@dataclass
class ValidationResult:
    valid_videos: List[VideoInfo]
    invalid_videos: List[VideoInfo]
    warnings: List[str]
    total_segments: int
    kmeans_viable: bool
    total_duration_seconds: float
    segment_duration: int
    min_split_duration: float
```

---

### Change 3: Update to_dict method

**Location:** Lines ~56-66

**Before:**
```python
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid_videos": [v.to_dict() for v in self.valid_videos],
            "invalid_videos": [v.to_dict() for v in self.invalid_videos],
            "warnings": self.warnings,
            "total_segments": self.total_segments,
            "kmeans_viable": self.kmeans_viable,
            "total_duration_seconds": self.total_duration_seconds,
        }
```

**After:**
```python
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid_videos": [v.to_dict() for v in self.valid_videos],
            "invalid_videos": [v.to_dict() for v in self.invalid_videos],
            "warnings": self.warnings,
            "total_segments": self.total_segments,
            "kmeans_viable": self.kmeans_viable,
            "total_duration_seconds": self.total_duration_seconds,
            "segment_duration": self.segment_duration,
            "min_split_duration": self.min_split_duration,
        }
```

---

### Change 4: Update first ValidationResult return (empty case)

**Location:** Lines ~270-277

**Before:**
```python
        return ValidationResult(
            valid_videos=[],
            invalid_videos=[],
            warnings=warnings,
            total_segments=0,
            kmeans_viable=False,
            total_duration_seconds=0,
        )
```

**After:**
```python
        return ValidationResult(
            valid_videos=[],
            invalid_videos=[],
            warnings=warnings,
            total_segments=0,
            kmeans_viable=False,
            total_duration_seconds=0,
            segment_duration=SEGMENT_DURATION,
            min_split_duration=MIN_SPLIT_DURATION,
        )
```

---

### Change 5: Update second ValidationResult return (normal case)

**Location:** Lines ~313-320

**Before:**
```python
    return ValidationResult(
        valid_videos=valid_videos,
        invalid_videos=invalid_videos,
        warnings=warnings,
        total_segments=total_segments,
        kmeans_viable=kmeans_viable,
        total_duration_seconds=total_duration,
    )
```

**After:**
```python
    return ValidationResult(
        valid_videos=valid_videos,
        invalid_videos=invalid_videos,
        warnings=warnings,
        total_segments=total_segments,
        kmeans_viable=kmeans_viable,
        total_duration_seconds=total_duration,
        segment_duration=SEGMENT_DURATION,
        min_split_duration=MIN_SPLIT_DURATION,
    )
```

---

## File 4: `/workspace/vsp-ui/app/static/index.html`

### Change: Add id to overlap label span

**Location:** Lines ~121-125 (Segmentation Options section)

**Before:**
```html
                        <label class="checkbox-label">
                            <input type="checkbox" id="overlap-enabled" checked>
                            <span>Enable overlapping segments for videos &gt;8s</span>
                            <span class="tooltip-icon" title="Improves transcription quality at segment boundaries by using 1-second overlap between segments. Adds ~33% processing time.">ℹ️</span>
                        </label>
```

**After:**
```html
                        <label class="checkbox-label">
                            <input type="checkbox" id="overlap-enabled" checked>
                            <span id="overlap-label-text">Enable overlapping segments for videos &gt;24s</span>
                            <span class="tooltip-icon" title="Improves transcription quality at segment boundaries by using 1-second overlap between segments. Adds ~33% processing time.">ℹ️</span>
                        </label>
```

---

## File 5: `/workspace/vsp-ui/app/static/app.js`

### Change: Add dynamic text update in displayValidationResults()

**Location:** Lines ~210-217 (inside displayValidationResults function)

**Before:**
```javascript
function displayValidationResults() {
    const result = validationResult;

    // Stats
    elements.validCount.textContent = result.valid_videos.length;
    elements.segmentCount.textContent = result.total_segments;
    elements.totalDuration.textContent = formatDuration(result.total_duration_seconds);

    // Warnings
```

**After:**
```javascript
function displayValidationResults() {
    const result = validationResult;

    // Stats
    elements.validCount.textContent = result.valid_videos.length;
    elements.segmentCount.textContent = result.total_segments;
    elements.totalDuration.textContent = formatDuration(result.total_duration_seconds);

    // Update overlap label with dynamic min_split_duration
    const overlapLabel = document.getElementById('overlap-label-text');
    if (overlapLabel && result.min_split_duration) {
        overlapLabel.textContent = `Enable overlapping segments for videos >${result.min_split_duration}s`;
    }

    // Warnings
```

---

## Summary

These changes ensure:

1. **Default segment duration is 12 seconds** (instead of 4)
2. **Minimum split duration is 24 seconds** (instead of 8) - maintains 2x relationship
3. **Frontend dynamically displays the correct threshold** from backend config
4. **Pipeline script uses variables** instead of hardcoded values
5. **All components are synchronized** and use the same values

## Testing

After applying these changes:

1. Start the VSP UI server
2. Add videos to the input folder
3. Click "Scan Videos"
4. Verify the overlap checkbox text shows ">24s" (not ">8s")
5. Run the pipeline and verify segments are 12 seconds long (check preprocessed filenames)

## Related Files (EC2 Version)

The equivalent changes have been applied to the EC2 instance in:
- `/home/ubuntu/run_flat_english_pipeline.sh`
- `/home/ubuntu/vsp-ui/app/config.py`
- `/home/ubuntu/vsp-ui/app/services/validator.py`
- `/home/ubuntu/vsp-ui/app/static/index.html`
- `/home/ubuntu/vsp-ui/app/static/app.js`

Date: January 25, 2026
