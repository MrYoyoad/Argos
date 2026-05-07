# Mission 3: VSP-LLM Max Length Fix

**Date**: 2026-01-29
**Status**: ✅ APPLIED (EXPERIMENTAL)
**Issue**: Early prediction cutoff - hypotheses truncated mid-sentence

---

## Problem Summary

VSP-LLM predictions were cutting off prematurely, missing final 3-10 words of sentences.

**Example**:
- **Reference**: "...we removed the taliban government which had given bin laden..."
- **Before Fix**: "...we removed the tal" ❌ (cutoff mid-word!)
- **After Fix**: "...we removed the taliban government..." ✅ (expected)

---

## Root Cause

**Overly restrictive generation length constraints** in `s2s_decode.yaml`:

```yaml
max_len_a: 1.0  # Output = 1.0 × input length
max_len_b: 0    # No buffer
```

**Formula** (`fairseq/sequence_generator.py` line 246):
```python
max_len = int(max_len_a * src_len + max_len_b)
```

**Impact**:
- 100 input clusters → max 100 tokens output
- Generation loop MUST stop at iteration 100, even mid-sentence
- Fixed-size buffers allocated, cannot expand

---

## Applied Fix

**Files Modified**:
1. `/home/ubuntu/VSP-LLM/src/conf/s2s_decode.yaml` (EC2)
2. `/home/ubuntu/vsp_docker/galaxy_export/VSP-LLM/src/conf/s2s_decode.yaml` (Container)

**Changes** (lines 8-9):
```yaml
# BEFORE:
  max_len_a: 1.0
  max_len_b: 0

# AFTER:
  max_len_a: 2.0    # Allows 2x input length
  max_len_b: 200    # Adds 200-token buffer
```

**New Capacity**:
- 50 clusters → 300 tokens max (was 50)
- 100 clusters → 400 tokens max (was 100)
- 150 clusters → 500 tokens max (was 150)

---

## How to Test

### 1. Run Pipeline

```bash
# Run on test videos
./run_flat_english_pipeline.sh ~/vsp_input/

# Check outputs
ls -lh VSP-LLM/decode/vsr/en/
```

### 2. Inspect Predictions

```bash
# View decoded hypotheses
cd VSP-LLM
python3 << 'EOF'
import json
import glob

# Find latest decode output
decode_files = glob.glob('decode/vsr/en/hypo-*.json')
if not decode_files:
    print("No decode outputs found")
    exit()

latest = sorted(decode_files)[-1]
print(f"Reading: {latest}\n")

with open(latest) as f:
    data = json.load(f)

# Show first 5 predictions
for i in range(min(5, len(data['hypo']))):
    hyp = data['hypo'][i]
    ref = data['ref'][i] if 'ref' in data else "N/A"
    utt = data['utt_id'][i]

    print(f"[{utt}]")
    print(f"  REF: {ref}")
    print(f"  HYP: {hyp}")
    print(f"  Length: {len(hyp.split())} words\n")
EOF
```

### 3. Success Criteria

✅ **Success indicators**:
- Hypotheses reach end of sentences (no mid-word cutoffs)
- Hypothesis length closer to reference length
- Complete predictions (e.g., "taliban government" not "tal")
- Pipeline completes without OOM errors

❌ **Failure indicators**:
- Out of memory (OOM) errors during decode
- Extremely long, nonsensical predictions
- Worse WER than before

---

## How to Revert

If the fix causes issues (OOM, worse results, etc.):

### Quick Revert

**EC2**:
```bash
cd /home/ubuntu/VSP-LLM/src/conf
vim s2s_decode.yaml

# Change lines 8-9 back to:
  max_len_a: 1.0
  max_len_b: 0
```

**Container**:
```bash
cd /home/ubuntu/vsp_docker/galaxy_export/VSP-LLM/src/conf
vim s2s_decode.yaml

# Change lines 8-9 back to:
  max_len_a: 1.0
  max_len_b: 0
```

### Alternative Values to Try

If full revert is too restrictive but current values cause issues:

```yaml
# Option A: Moderate increase
  max_len_a: 1.5
  max_len_b: 100

# Option B: Original fairseq defaults
  max_len_a: 0
  max_len_b: 200

# Option C: More conservative
  max_len_a: 1.2
  max_len_b: 50
```

---

## Technical Details

### Why These Values?

- **max_len_a=2.0**: Conservative 2x multiplier (common in NMT systems)
- **max_len_b=200**: Fairseq's own default, provides generous buffer
- **Combined**: Ensures completion without excessive resource use

### Other Parameters (Unchanged)

```yaml
beam: 20          # ✅ Keep (already generous beam size)
lenpen: 0.0       # ✅ Keep (neutral length penalty)
lm_weight: 0      # ✅ Keep (external LM disabled)
```

### Code References

**Generation loop** (`fairseq/sequence_generator.py`):
- Line 246: `max_len = int(self.max_len_a * src_len + self.max_len_b)`
- Lines 264-271: Buffer allocation (fixed size)
- Line 314: `for step in range(max_len + 1)` - hard limit

---

## Monitoring

### Check for Issues

**GPU Memory**:
```bash
nvidia-smi  # During decode - watch GPU memory usage
```

**Generation Length**:
```python
# Add to vsp_llm_decode.py for debugging
print(f"Input length: {src_len}")
print(f"Max allowed: {max_len}")
print(f"Generated: {generated_len}")
```

**WER Comparison**:
```bash
# Calculate WER before/after
python VSP-LLM/scripts/calculate_per_video_wer.py \
  --decode-json decode/vsr/en/hypo-BEFORE.json \
  --segment-metadata preprocessed_flat_seg12/segment_metadata.json

python VSP-LLM/scripts/calculate_per_video_wer.py \
  --decode-json decode/vsr/en/hypo-AFTER.json \
  --segment-metadata preprocessed_flat_seg12/segment_metadata.json
```

---

## Next Steps

1. **Test on sample videos** - Validate fix works as expected
2. **Monitor resource usage** - Ensure no OOM errors
3. **Compare WER** - Verify improved accuracy
4. **Decide**: Keep, revert, or tune values

---

**Orchestrated by**: Yoad Oxman
**Implemented with**: Claude Code (claude.ai/code)
**Repository**: https://github.com/MrYoyoad/Argos
