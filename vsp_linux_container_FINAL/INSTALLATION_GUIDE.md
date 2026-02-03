# Installation Guide

**Package**: vsp_linux_container_FINAL v1.0.0
**Date**: February 3, 2026

Complete installation instructions for deploying all fixes to the Linux container.

---

## Prerequisites

### Container Environment
- Linux container with GPU support
- CUDA 12.1+ installed
- Python 3.11+ available
- Bash 4.0+ shell
- ffmpeg with NVENC support
- Existing VSP-LLM installation with models

### Disk Space
- 3 MB for deployment package
- 50+ GB for models/datasets (already in container)
- Variable space for processing outputs

### Permissions
- Write access to `/host/galaxy_export/` or `/host/galaxy_export/`
- Ability to execute bash scripts
- Access to container filesystem

---

## Installation Methods

### Method 1: Automated Installation (Recommended)

**Advantages**:
- ✅ One command
- ✅ Automatic timestamped backups
- ✅ Built-in verification
- ✅ Rollback support
- ✅ No manual file management

**Steps**:

1. **Transfer package to container host**
   ```bash
   # From EC2 to local machine
   scp -i key.pem ubuntu@ec2:/home/ubuntu/vsp_linux_container_FINAL_20260203.tar.gz .

   # From local machine to container host
   scp vsp_linux_container_FINAL_20260203.tar.gz user@host:/home/ds/Desktop/
   ```

2. **Extract package**
   ```bash
   cd /home/ds/Desktop
   tar xzf vsp_linux_container_FINAL_20260203.tar.gz
   cd vsp_linux_container_FINAL
   ```

3. **Run installation** (from inside container or host with shared filesystem)
   ```bash
   # Start container with volume mount
   docker run -it --gpus all \
     -v /home/ds/Desktop/galaxy_export:/host/galaxy_export \
     vsp-llm-pipeline:latest

   # Inside container, run installer
   cd /host/galaxy_export
   bash /host/galaxy_export/../vsp_linux_container_FINAL/INSTALL.sh
   ```

4. **Verify installation**
   ```bash
   bash /host/galaxy_export/../vsp_linux_container_FINAL/VERIFY.sh
   ```

**Expected Output**:
```
========================================
Installation Complete
========================================

Backup created: /host/galaxy_export_backup_20260203_140523.tar.gz

Installed Components:
✅ lib/ (11 modules)
✅ run_flat_english_pipeline.sh
✅ VSP-LLM/src/
✅ VSP-LLM/scripts/
✅ vsp-ui/

Verification:
✅ Fix 1: Cython auto-build
✅ Fix 2: max_len config
... (all 12 fixes)

Installation successful!
Next steps:
1. Test with: bash VERIFY.sh
2. Run pipeline: ./run_flat_english_pipeline.sh /path/to/videos
```

---

### Method 2: Manual Installation (Advanced)

**Use When**:
- You want fine-grained control
- Installing specific components only
- Troubleshooting installation issues

#### Step 1: Create Backup

```bash
cd /host/galaxy_export  # or /host/galaxy_export
tar czf ../host/galaxy_export_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  lib run_flat_english_pipeline.sh VSP-LLM vsp-ui
```

#### Step 2: Install lib/ Modules

```bash
# Copy all 11 modules
cp -r /path/to/vsp_linux_container_FINAL/lib /host/galaxy_export/

# Verify module tests
bash /host/galaxy_export/lib/test_all_modules.sh
# Expected: 37/37 tests pass
```

**What's Installed**:
- `lib/common.sh` - Fix #6 (log_info stderr redirect)
- `lib/asr.sh` - Fix #3 (dynamic transcription paths)
- `lib/decode.sh` - Fix #1 (Cython auto-build)
- 8 other modules (archive, clustering, config, lrs3_prep, manifests, normalization, outputs, venv_utils)

#### Step 3: Install Pipeline Script

```bash
# Backup existing pipeline
cp /host/galaxy_export/run_flat_english_pipeline.sh \
   /host/galaxy_export/run_flat_english_pipeline.sh.backup

# Install new pipeline with all fixes
cp /path/to/vsp_linux_container_FINAL/run_flat_english_pipeline.sh /host/galaxy_export/

# Verify fixes are present
grep -q 'POST_ROOT="$ARCHIVE_ROOT/client_outputs"' /host/galaxy_export/run_flat_english_pipeline.sh && echo "✅ Fix 7"
grep -q 'output_name="${video_name}"' /host/galaxy_export/run_flat_english_pipeline.sh && echo "✅ Fix 9"
grep -q "metadata for whole videos" /host/galaxy_export/run_flat_english_pipeline.sh && echo "✅ Fix 8"
grep -q "SEGMENT_DURATION.*12" /host/galaxy_export/run_flat_english_pipeline.sh && echo "✅ Fix 12"
```

**What's Installed**:
- Fix #7: POST_ROOT definition
- Fix #8: Step 2.5 metadata creation
- Fix #9: Non-segmented naming
- Fix #12: Segment duration = 12s
- Architecture: Segment-first normalization
- Transcription persistence (Steps 0.6, 1.5)

#### Step 4: Install VSP-LLM Fixes

```bash
# Create backup
cp /host/galaxy_export/VSP-LLM/src/conf/s2s_decode.yaml \
   /host/galaxy_export/VSP-LLM/src/conf/s2s_decode.yaml.backup
cp /host/galaxy_export/VSP-LLM/scripts/make_burn.py \
   /host/galaxy_export/VSP-LLM/scripts/make_burn.py.backup
cp /host/galaxy_export/VSP-LLM/src/vsp_llm_decode.py \
   /host/galaxy_export/VSP-LLM/src/vsp_llm_decode.py.backup

# Install fixes
cp /path/to/vsp_linux_container_FINAL/VSP-LLM/src/conf/s2s_decode.yaml \
   /host/galaxy_export/VSP-LLM/src/conf/
cp /path/to/vsp_linux_container_FINAL/VSP-LLM/scripts/make_burn.py \
   /host/galaxy_export/VSP-LLM/scripts/
cp /path/to/vsp_linux_container_FINAL/VSP-LLM/src/vsp_llm_decode.py \
   /host/galaxy_export/VSP-LLM/src/

# Verify fixes
grep -q "max_len: 2048" /host/galaxy_export/VSP-LLM/src/conf/s2s_decode.yaml && echo "✅ Fix 2"
grep -q "if seg_idx == -1:" /host/galaxy_export/VSP-LLM/scripts/make_burn.py && echo "✅ Fix 10"
grep -q "logger.propagate = False" /host/galaxy_export/VSP-LLM/src/vsp_llm_decode.py && echo "✅ Fix 11"
```

**What's Installed**:
- Fix #2: max_len configuration
- Fix #10: make_burn segment matching
- Fix #11: Logger duplication fix

#### Step 5: Install VSP UI Fixes

```bash
# Create backup
tar czf /host/galaxy_export/vsp-ui_backup.tar.gz /host/galaxy_export/vsp-ui

# Install UI fixes
cp /path/to/vsp_linux_container_FINAL/vsp-ui/app/config.py \
   /host/galaxy_export/vsp-ui/app/
cp /path/to/vsp_linux_container_FINAL/vsp-ui/app/services/transcription_manager.py \
   /host/galaxy_export/vsp-ui/app/services/
cp -r /path/to/vsp_linux_container_FINAL/vsp-ui/app/static \
   /host/galaxy_export/vsp-ui/app/

# Verify fixes
grep -q "VSP_INPUT_DIR" /host/galaxy_export/vsp-ui/app/config.py && echo "✅ Fix 4"
grep -q "from app.config import INPUT_DIR" /host/galaxy_export/vsp-ui/app/services/transcription_manager.py && echo "✅ Fix 5"
grep -q "SEGMENT_DURATION = 12" /host/galaxy_export/vsp-ui/app/config.py && echo "✅ Fix 12"
```

**What's Installed**:
- Fix #4: VSP_INPUT_DIR support
- Fix #5: Absolute imports
- Fix #12: UI segment duration = 12s
- All UI features (transcription management, video exclusion, etc.)

#### Step 6: Verify Installation

```bash
# Run verification script
bash /path/to/vsp_linux_container_FINAL/VERIFY.sh

# Or manual verification
cd /host/galaxy_export
grep -q ">&2" lib/common.sh && echo "✅ Fix 6"
grep -q "CRITICAL: Check and build fairseq Cython" lib/decode.sh && echo "✅ Fix 1"
# ... verify all 12 fixes
```

---

## Post-Installation

### Verify All Fixes

Run the automated verification script:
```bash
bash VERIFY.sh
```

Expected output: All 12 fixes ✅

### Test Module Functions

```bash
bash lib/test_all_modules.sh
```

Expected output: 37/37 tests pass ✅

### Quick Smoke Test

```bash
# Test with a short video
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test_video.mp4

# Check for:
# 1. No Cython errors (builds automatically if needed)
# 2. No max_len errors
# 3. Transcription saved to .transcriptions/
# 4. Client outputs generated
# 5. Burned video is full-frame (not 88x88 mouth crop)
```

---

## Troubleshooting

### Issue: Installation Script Fails

**Error**: `bash: INSTALL.sh: Permission denied`

**Solution**:
```bash
chmod +x INSTALL.sh
bash INSTALL.sh
```

### Issue: Directory Not Found

**Error**: `ERROR: Must run from galaxy_export directory`

**Solution**: Make sure you're in the correct directory:
```bash
cd /host/galaxy_export  # or /host/galaxy_export
pwd  # Should show /host/galaxy_export or /host/galaxy_export
bash /path/to/INSTALL.sh
```

### Issue: Backup Already Exists

**Error**: `Backup file already exists`

**Solution**: Remove old backup or rename it:
```bash
mv ../host/galaxy_export_backup_*.tar.gz ../host/galaxy_export_backup_old.tar.gz
bash INSTALL.sh
```

### Issue: Partial Installation

**Problem**: Installation interrupted, some files copied but not all.

**Solution**: Restore from backup and re-run:
```bash
cd /host/galaxy_export
tar xzf ../host/galaxy_export_backup_YYYYMMDD_HHMMSS.tar.gz
bash /path/to/INSTALL.sh
```

### Issue: Fix Verification Fails

**Problem**: VERIFY.sh shows some fixes missing.

**Solution**: Check which specific fix is missing and install manually:
```bash
# If Fix #2 missing
cp vsp_linux_container_FINAL/VSP-LLM/src/conf/s2s_decode.yaml /host/galaxy_export/VSP-LLM/src/conf/

# If Fix #6 missing
cp vsp_linux_container_FINAL/lib/common.sh /host/galaxy_export/lib/

# Re-verify
bash VERIFY.sh
```

---

## Rollback Procedures

### Full Rollback

If you need to completely revert to pre-installation state:

```bash
cd /host/galaxy_export
# Remove installed files
rm -rf lib run_flat_english_pipeline.sh VSP-LLM/src/conf VSP-LLM/scripts VSP-LLM/src vsp-ui

# Restore from backup
tar xzf ../host/galaxy_export_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Partial Rollback

Revert specific components:

```bash
# Rollback pipeline script only
tar xzf ../host/galaxy_export_backup_*.tar.gz run_flat_english_pipeline.sh

# Rollback lib modules only
tar xzf ../host/galaxy_export_backup_*.tar.gz lib/

# Rollback VSP-LLM fixes only
tar xzf ../host/galaxy_export_backup_*.tar.gz VSP-LLM/
```

---

## Environment Variables

### VSP_INPUT_DIR

Override the default input directory:

```bash
# Set before running container
docker run -e VSP_INPUT_DIR=/custom/path/to/videos ...

# Or export inside container
export VSP_INPUT_DIR=/custom/path/to/videos
python3 vsp-ui/app/server.py
```

### TRAIN_KMEANS

Skip k-means training (use existing model):

```bash
# Via environment variable
export TRAIN_KMEANS=0
./run_flat_english_pipeline.sh /path/to/videos

# Or via UI checkbox (automatic)
```

### SEG_DURATION

Override segment duration:

```bash
# Use 8-second segments instead of 12
export SEG_DURATION=8
export MIN_SPLIT_DURATION=16.0
./run_flat_english_pipeline.sh /path/to/videos
```

---

## Verification Checklist

After installation, verify:

- [ ] All 12 fixes present (run VERIFY.sh)
- [ ] Module tests pass (37/37)
- [ ] Pipeline script executes without errors
- [ ] Cython extensions build automatically (first run)
- [ ] Decode step completes successfully
- [ ] Transcriptions persist in `.transcriptions/`
- [ ] Client outputs generated correctly
- [ ] Burned videos use full-frame (not mouth crops)
- [ ] UI starts without import errors
- [ ] UI recognizes input directory correctly

---

## Next Steps

After successful installation:

1. **Test with sample videos** - Run quick smoke test
2. **Review TESTING_GUIDE.md** - Comprehensive testing procedures
3. **Configure environment variables** - Set VSP_INPUT_DIR if needed
4. **Run full pipeline** - Process actual videos
5. **Monitor first run** - Cython build should happen automatically

---

**Document Version**: 1.0.0
**Last Updated**: February 3, 2026
