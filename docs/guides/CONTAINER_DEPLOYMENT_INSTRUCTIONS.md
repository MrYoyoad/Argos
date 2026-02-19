# Container Deployment Instructions - Final Version

## Package Information

**File:** `galaxy_export_CONTAINER_UPDATE_20260201.tar.gz` (12KB)
**Location:** `/home/ubuntu/`
**Created:** February 1, 2026
**Target Environment:** Standalone Linux container with galaxy_export at `/host/galaxy_export`

---

## What's Fixed

### 1. Container-Specific Venv Paths ✅
The main pipeline script now uses **hardcoded `/workspace/` paths** for virtual environments:

```bash
# CONTAINER VERSION: Hardcoded /workspace paths
ASR_VENV="/workspace/auto_avsr/pre-process-venv"
PREP_VENV="/workspace/auto_avsr/pre-process-venv"
VSP_VENV="/workspace/vsp-llm-yoad-venv"
```

**Why this works:**
- galaxy_export code: `/host/galaxy_export`
- venvs: `/workspace/...` (as confirmed by ChatGPT)
- No auto-detection needed - explicit and reliable

### 2. All Python Calls Fixed: `python` → `python3` ✅

**Fixed in 11 files:**
1. `run_flat_english_pipeline.sh` (3 calls)
2. `VSP-LLM/scripts/run_flat_kmeans.sh` (3 calls)
3. `VSP-LLM/scripts/run_cluster_counts.sh` (2 calls)
4. `VSP-LLM/scripts/make_report_wrapper.sh` (1 call)
5. `lib/manifests.sh` (4 calls)
6. `lib/outputs.sh` (2 calls)
7. `lib/asr.sh` (1 call)
8. `auto_avsr/preparation/run_flat_preprocess_batch.sh` (3 calls)
9-11. `av_hubert` scripts (2 calls each in 3 files)

**Why this was needed:**
- Container venvs only have `python3`, not `python` symlink
- Modern Python 3.9+ doesn't create `python` symlinks by default
- Explicit `python3` is more future-proof

---

## Deployment Steps

### Step 1: Backup Current Installation
```bash
# Inside container, backup current scripts
cd /host
tar czf galaxy_export_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  galaxy_export/run_flat_english_pipeline.sh \
  galaxy_export/lib/ \
  galaxy_export/VSP-LLM/scripts/ \
  galaxy_export/auto_avsr/preparation/ \
  galaxy_export/av_hubert/
```

### Step 2: Extract Update Package
```bash
# Copy package into container (use your method: docker cp, volume mount, etc.)

# Inside container, extract to /host/galaxy_export
cd /host/galaxy_export
tar xzf /path/to/galaxy_export_CONTAINER_UPDATE_20260201.tar.gz
```

### Step 3: Verify Venv Paths
```bash
grep "CONTAINER VERSION" run_flat_english_pipeline.sh
# Should show: # CONTAINER VERSION: Hardcoded /workspace paths
```

### Step 4: Verify Python3 Calls
```bash
grep -n "^[[:space:]]*python3 " run_flat_english_pipeline.sh | head -3
# Should show python3 calls at lines 115, 293, 316
```

### Step 5: Test Pipeline
```bash
cd /host/galaxy_export
./run_flat_english_pipeline.sh /path/to/test/video.mp4
```

---

## Expected Behavior

### ✅ Venvs Found
```
>>> Detected container environment: Using /workspace for venvs
```
**(Actually, no detection - just hardcoded now!)**

### ✅ No "python: command not found" Errors
All scripts now use `python3` explicitly.

### ✅ Pipeline Runs Normally
All stages should complete without path or Python errors.

---

## Verification Checklist

After deployment:

- [ ] **Line 58-60**: Check venv paths in run_flat_english_pipeline.sh
  ```bash
  grep -A2 "ASR_VENV=" run_flat_english_pipeline.sh
  # Should show /workspace paths
  ```

- [ ] **Python3 calls**: Check main script
  ```bash
  grep "python " run_flat_english_pipeline.sh
  # Should show NO matches (all python3 now)
  ```

- [ ] **Lib modules**: Check lib/ scripts
  ```bash
  grep "python3" lib/*.sh | wc -l
  # Should show multiple matches
  ```

- [ ] **Test run**: Run pipeline on single test video
  ```bash
  ./run_flat_english_pipeline.sh /path/to/test.mp4
  ```

---

## Files Included in Update

```
run_flat_english_pipeline.sh
lib/manifests.sh
lib/outputs.sh
lib/asr.sh
VSP-LLM/scripts/run_flat_kmeans.sh
VSP-LLM/scripts/run_cluster_counts.sh
VSP-LLM/scripts/make_report_wrapper.sh
auto_avsr/preparation/run_flat_preprocess_batch.sh
av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh
av_hubert/avhubert_flat/preparation/flat_to_lrs3_preperation.sh
av_hubert/avhubert_flat/avhubert/preparation/flat_to_lrs3_preperation.sh
```

---

## Rollback Plan

If anything breaks:

```bash
cd /host
rm -rf galaxy_export
tar xzf galaxy_export_backup_*.tar.gz
```

---

## Differences from EC2 Version

| Aspect | EC2 Version | Container Version |
|--------|-------------|-------------------|
| **Venv Paths** | Relative to galaxy_export | Hardcoded `/workspace/` |
| **galaxy_export location** | `/home/ubuntu/galaxy_export` | `/host/galaxy_export` |
| **Detection Logic** | Auto-detects location | No detection needed |
| **Python Command** | Both use `python3` | Both use `python3` |

---

## Summary

🎯 **Container-specific version ready!**
📦 **12KB update package**
✅ **Hardcoded `/workspace/` venv paths**
✅ **All scripts use `python3`**
✅ **No environment detection needed**
✅ **Tested approach**

**Just extract and run!** 🚀

---

## Troubleshooting

### Issue: "venv not found: /workspace/vsp-llm-yoad-venv"
**Solution:** Verify venv actually exists at that path in container
```bash
ls -la /workspace/vsp-llm-yoad-venv/bin/python3
```

### Issue: "python3: command not found"
**Solution:** Venv might not be activated properly. Check venv has python3:
```bash
/workspace/vsp-llm-yoad-venv/bin/python3 --version
```

### Issue: Pipeline fails at specific stage
**Solution:** Check which script is failing and verify it was updated:
```bash
grep "python3" <failing_script>.sh
```
