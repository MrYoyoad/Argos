# Pipeline Modifications for Overlapping Segmentation

This document contains the modifications needed for `run_flat_english_pipeline.sh` to support overlapping segmentation.

## ✅ ALREADY APPLIED

Lines 26-30: OVERLAP_ENABLED configuration added

## MODIFICATIONS TO APPLY

### 1. Replace Preprocessing Section (Lines ~379-399)

**Find this section:**
```bash
########################
# STEP 3: preprocess_lrs2lrs3.py  (FIXED)
########################
echo ">>> [3] Running preprocess_lrs2lrs3.py (mediapipe, seg=4s)"

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

echo ">>> [INFO] Mouth crops + LRS2/LRS3-style data are in: $PREP_ROOT"
```

**Replace with:**
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

---

### 2. Add After Manifest Generation (After line ~420)

**Find the end of manifest generation** (after `make_simple_manifest.py`), then add:

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

---

### 3. Add After Decode (After line ~481, after run_flat_decode.sh)

**After the decode step**, add:

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

---

### 4. Replace Report/Burn Section (Lines ~494-502)

**Find this section:**
```bash
DECODE_JSON="$(ls -t ${VSP}/decode/vsr/en/vsr/en/hypo-*.json | head -n 1)"

python "$VSP/scripts/make_report.py" \
    --decode-json "$DECODE_JSON" \
    --output-dir "${ARCHIVE_ROOT}/client_outputs/report"

python "$VSP/scripts/make_burn.py" \
    --decode-json "$DECODE_JSON" \
    --video-dir "$FLAT_VID_DIR" \
    --output-dir "${ARCHIVE_ROOT}/client_outputs/burned_videos"
```

**Replace with:**
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

---

## Quick Disable/Enable

To disable overlapping segmentation for a single run:
```bash
OVERLAP_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/videos
```

To enable (default):
```bash
./run_flat_english_pipeline.sh /path/to/videos
```

---

## Testing After Modifications

1. Test with overlap disabled first:
   ```bash
   OVERLAP_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test/videos
   ```

2. Then test with overlap enabled:
   ```bash
   OVERLAP_ENABLED=1 ./run_flat_english_pipeline.sh /path/to/test/videos
   ```

3. Verify outputs:
   - Check `segment_metadata.json` exists when overlap enabled
   - Check `segment_timing.json` exists in 433h_data/
   - Check `hypo-*-merged.json` exists in decode/vsr/en/
   - Check conflict reports in client_outputs/report/conflicts/
