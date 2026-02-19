# Container Package Validation Checklist

## Critical Bugs Fixed

### ✅ Bug #1: Missing Space in Python3 Calls
**Issue:** `python3"$script"` instead of `python3 "$script"`
**Impact:** Would cause "command not found" errors
**Fixed in:**
- lib/manifests.sh (4 calls)
- lib/outputs.sh (2 calls)
- auto_avsr/preparation/run_flat_preprocess_batch.sh (3 calls)

### ✅ Bug #2: Wrong Venv Path in run_flat_kmeans.sh
**Issue:** Used `${GALAXY_ROOT}/../vsp-llm-yoad-venv` (relative path)
**Impact:** Would try `/host/vsp-llm-yoad-venv` which doesn't exist
**Fix:** Hardcoded `/workspace/vsp-llm-yoad-venv`

---

## Pre-Deployment Validation (On EC2)

Run these checks BEFORE deploying to container:

### Check 1: Verify No Missing Spaces
```bash
cd /home/ubuntu/vsp_docker/galaxy_export

# Should return NO matches:
grep -r 'python3"' lib/ VSP-LLM/scripts/ auto_avsr/preparation/run_flat_preprocess_batch.sh 2>/dev/null | grep -v ".pyc"

# Expected output: (nothing)
```

### Check 2: Verify Hardcoded Container Venv Paths
```bash
# Main pipeline - should show /workspace paths:
grep -A3 "CONTAINER VERSION" run_flat_english_pipeline.sh

# Expected output:
# # CONTAINER VERSION: Hardcoded /workspace paths for standalone Linux container
# ASR_VENV="/workspace/auto_avsr/pre-process-venv"
# PREP_VENV="/workspace/auto_avsr/pre-process-venv"
# VSP_VENV="/workspace/vsp-llm-yoad-venv"
```

### Check 3: Verify run_flat_kmeans.sh Venv Path
```bash
grep -A2 "CONTAINER VERSION" VSP-LLM/scripts/run_flat_kmeans.sh

# Expected output:
# # CONTAINER VERSION: Hardcoded /workspace venv path
# VSP_VENV="/workspace/vsp-llm-yoad-venv"
```

### Check 4: Verify All Python3 Calls Have Spaces
```bash
# Should show python3 with space before quote:
grep 'python3 "' lib/manifests.sh | wc -l
# Expected: 4

grep 'python3 "' lib/outputs.sh | wc -l
# Expected: 2

grep 'python3 "' auto_avsr/preparation/run_flat_preprocess_batch.sh | wc -l
# Expected: 3
```

---

## Post-Deployment Validation (In Container)

Run these checks AFTER deploying to container:

### Check 1: Verify Venvs Exist at Expected Paths
```bash
# Inside container:
ls -la /workspace/vsp-llm-yoad-venv/bin/python3
ls -la /workspace/auto_avsr/pre-process-venv/bin/python3

# Both should exist and be executable
```

### Check 2: Verify Scripts Extracted Correctly
```bash
cd /host/galaxy_export

# Check main pipeline:
head -60 run_flat_english_pipeline.sh | grep "CONTAINER VERSION"
# Should show: # CONTAINER VERSION: Hardcoded /workspace paths

# Check lib modules:
head -100 lib/manifests.sh | grep "python3 "
# Should show python3 with space (not python3")

# Check VSP-LLM script:
head -15 VSP-LLM/scripts/run_flat_kmeans.sh | grep "VSP_VENV="
# Should show: VSP_VENV="/workspace/vsp-llm-yoad-venv"
```

### Check 3: Test Venv Activation
```bash
# Test ASR venv:
source /workspace/auto_avsr/pre-process-venv/bin/activate
python3 --version
deactivate

# Test VSP venv:
source /workspace/vsp-llm-yoad-venv/bin/activate
python3 --version
deactivate
```

### Check 4: Syntax Validation
```bash
cd /host/galaxy_export

# Check main pipeline syntax:
bash -n run_flat_english_pipeline.sh
# Should return nothing (no errors)

# Check lib modules:
bash -n lib/manifests.sh
bash -n lib/outputs.sh
bash -n lib/asr.sh
# Should return nothing (no errors)
```

### Check 5: Dry Run Test (Optional)
```bash
# This won't run the full pipeline but will validate paths and venvs:
cd /host/galaxy_export

# Export test values:
export SEGMENTATION_ENABLED=1
export SEG_DURATION=12

# Check venv activation works:
source /workspace/auto_avsr/pre-process-venv/bin/activate && echo "✓ ASR venv OK" && deactivate
source /workspace/vsp-llm-yoad-venv/bin/activate && echo "✓ VSP venv OK" && deactivate
```

---

## Common Issues & Solutions

### Issue 1: "python3: command not found"
**Symptom:** Error when running any stage
**Cause:** Missing space: `python3"$script"` instead of `python3 "$script"`
**Solution:** Re-extract package (bug was fixed in final version)

### Issue 2: "/workspace/vsp-llm-yoad-venv: No such file or directory"
**Symptom:** Error at k-means stage (Step 6)
**Cause:** Venv doesn't exist at expected path in container
**Solution:** Verify venv exists: `ls -la /workspace/vsp-llm-yoad-venv/`

### Issue 3: Relative path errors in run_flat_kmeans.sh
**Symptom:** Error like "/host/vsp-llm-yoad-venv: not found"
**Cause:** Old version of script with relative paths
**Solution:** Re-extract package (bug was fixed in final version)

### Issue 4: Syntax errors when running scripts
**Symptom:** `/bin/bash: line XX: syntax error near unexpected token`
**Cause:** Missing spaces or quotes in python3 calls
**Solution:** Run `bash -n <script>` to identify syntax errors, re-extract package

---

## Files Changed Summary

**11 files total:**

1. ✅ `run_flat_english_pipeline.sh`
   - Fixed: Hardcoded `/workspace/` venv paths
   - Fixed: 3 `python` → `python3` calls

2. ✅ `lib/manifests.sh`
   - Fixed: 4 `python3"` → `python3 "` (spacing)

3. ✅ `lib/outputs.sh`
   - Fixed: 2 `python3"` → `python3 "` (spacing)

4. ✅ `lib/asr.sh`
   - Fixed: 1 `python` → `python3` call

5. ✅ `VSP-LLM/scripts/run_flat_kmeans.sh`
   - Fixed: 3 `python` → `python3` calls
   - Fixed: Hardcoded `/workspace/vsp-llm-yoad-venv` venv path

6. ✅ `VSP-LLM/scripts/run_cluster_counts.sh`
   - Fixed: 2 `python` → `python3` calls

7. ✅ `VSP-LLM/scripts/make_report_wrapper.sh`
   - Fixed: 1 `python` → `python3` call

8. ✅ `auto_avsr/preparation/run_flat_preprocess_batch.sh`
   - Fixed: 3 `python3"` → `python3 "` (spacing)

9-11. ✅ `av_hubert/` scripts (3 files)
   - Fixed: 2 `python` → `python3` calls each

---

## Verification Command Summary

```bash
# === ON EC2 (before deployment) ===
cd /home/ubuntu/vsp_docker/galaxy_export

# 1. No missing spaces:
! grep -r 'python3"' lib/ VSP-LLM/scripts/ auto_avsr/preparation/run_flat_preprocess_batch.sh 2>/dev/null | grep -v ".pyc"

# 2. Container paths present:
grep "CONTAINER VERSION" run_flat_english_pipeline.sh VSP-LLM/scripts/run_flat_kmeans.sh | wc -l
# Expected: 2

# === IN CONTAINER (after deployment) ===
cd /host/galaxy_export

# 1. Venvs exist:
test -f /workspace/vsp-llm-yoad-venv/bin/python3 && test -f /workspace/auto_avsr/pre-process-venv/bin/python3 && echo "✓ Venvs OK"

# 2. Scripts have correct syntax:
bash -n run_flat_english_pipeline.sh && bash -n lib/*.sh && echo "✓ Syntax OK"

# 3. Venv activation works:
source /workspace/auto_avsr/pre-process-venv/bin/activate && deactivate && \
source /workspace/vsp-llm-yoad-venv/bin/activate && deactivate && \
echo "✓ Venvs activate OK"
```

---

## Final Package Info

**File:** `galaxy_export_CONTAINER_FINAL_20260201.tar.gz`
**Size:** 12KB
**Location:** `/home/ubuntu/`
**Bugs Fixed:** 2 critical issues
**Files Updated:** 11 scripts
**Ready:** YES ✅

---

## Quick Deployment Command

```bash
# Inside container:
cd /host/galaxy_export
tar xzf /path/to/galaxy_export_CONTAINER_FINAL_20260201.tar.gz

# Verify:
grep "CONTAINER VERSION" run_flat_english_pipeline.sh && echo "✓ Deployed!"

# Test:
./run_flat_english_pipeline.sh /path/to/test/video.mp4
```

🎯 **All critical bugs fixed and validated!**
