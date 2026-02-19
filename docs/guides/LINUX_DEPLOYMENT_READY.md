# Linux Container Deployment - Ready!

**Date**: February 1, 2026
**Status**: ✅ All fixes applied and verified

## Two Deployment Packages Ready

### 1. Generic Linux Container
**Location**: `/home/ubuntu/linux_container_ready/`
**Destination**: `/workspace/` (standalone Linux container)
**Instructions**: See `linux_container_ready/DEPLOY_TO_CONTAINER.md`

### 2. Galaxy Export (Docker)
**Location**: `/home/ubuntu/vsp_docker/galaxy_export/`
**Destination**: Docker container or `/workspace/`
**Note**: Uses `ui/` instead of `vsp-ui/` directory

Both packages contain **identical fixes** and are ready for deployment.

---

## What's Included in Both Packages

### Critical Fixes (6/6) ✅
1. ✅ **log_info stderr redirect** - Prevents client output failures
2. ✅ **POST_ROOT defined** - Prevents pipeline exit errors
3. ✅ **Step 2.5 metadata** - Enables full-frame burned videos
4. ✅ **Non-segmented naming** - Fixes transcription matching
5. ✅ **make_burn.py fix** - Non-segmented video support
6. ✅ **Decode logger fix** - No duplicate logging

### Latest Updates ✅
1. ✅ **Segment-first normalization** - Much more efficient for long videos
2. ✅ **Whole video directory support** - UI works with non-segmented videos
3. ✅ **Upload progress improvements** - Smooth progress bar

### Major Features ✅
- ✅ Modular lib/ architecture (11 modules)
- ✅ Unified transcription management
- ✅ Transcription persistence across runs
- ✅ Video exclusion feature
- ✅ K-means training toggle
- ✅ Manual transcription UI
- ✅ Segment duration update (12s)
- ✅ Original video serving for transcription modal

---

## Quick Deployment

### Option 1: Copy Directly (if shared filesystem)
```bash
# For generic container:
cp -r /home/ubuntu/linux_container_ready/* /workspace/

# For galaxy_export:
cp -r /home/ubuntu/vsp_docker/galaxy_export/* /workspace/
```

### Option 2: Create Tarball and Transfer
```bash
# Create package
cd /home/ubuntu
tar czf linux_container.tar.gz linux_container_ready/
# OR
tar czf galaxy_export.tar.gz vsp_docker/galaxy_export/

# Transfer to container (method depends on your setup)
# Then extract in container:
cd /workspace
tar xzf /tmp/linux_container.tar.gz
# Copy files to appropriate locations
```

### Option 3: Git Commit and Pull
```bash
# On EC2:
cd /home/ubuntu
git add run_flat_english_pipeline.sh lib/ VSP-LLM/scripts/make_burn.py VSP-LLM/src/vsp_llm_decode.py vsp-ui/
git commit -m "Sync: All critical fixes + segment-first normalization"
git push

# On container:
cd /workspace
git pull
```

---

## Post-Deployment Testing

### Quick Test (5 minutes)
```bash
cd /workspace

# 1. Test modules
bash lib/test_all_modules.sh

# 2. Test short video (non-segmented)
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/short/video

# 3. Verify outputs exist
ls ~/flat_runs_archive/*/client_outputs/report/
ls ~/flat_runs_archive/*/client_outputs/burned_videos/
```

### Full Test (30 minutes)
```bash
# 1. Test segment-first normalization with long video
./run_flat_english_pipeline.sh /path/to/60s/video
# Should see:
#   [0.1] Fast segmentation (6 segments)
#   [0.5] Normalizing segments (6× 12s, not 1× 60s)
#   [2] Mouth cropping

# 2. Test whole video mode
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/short/video
# Should see:
#   [0.1] Whole video mode
#   [2.5] Creating segment_metadata
#   Burned video uses full-frame

# 3. Test manual transcription
# - Start UI
# - Add manual transcription
# - Run pipeline
# - Verify Whisper skips that segment

# 4. Check burned video resolution
ffprobe ~/flat_runs_archive/*/client_outputs/burned_videos/*.mp4 2>&1 | grep "Video:"
# Should show original resolution, not 96x96
```

---

## Architecture Improvements

### Old Pipeline Flow:
```
Raw Videos (60min)
  → Normalize whole video (slow, high memory)
  → Preprocess + segment into 12s chunks
  → Mouth crop each segment
```

### New Pipeline Flow (Segment-First):
```
Raw Videos (60min)
  → [0.1] Fast segment into 12s chunks (codec copy, very fast)
  → [0.5] Normalize each segment (6× 12s, efficient!)
  → [2] Mouth crop each segment (no re-segmentation)
```

**Benefits**:
- 🚀 **Much faster** for long videos
- 💾 **Lower memory** usage
- ⚡ **Better parallelization** potential
- 🎯 **Same accuracy**, better efficiency

---

## What Each Package Contains

### Files Updated:
```
lib/
├── archive.sh            ✓ No changes (already good)
├── asr.sh                ✓ Transcription reuse logic
├── clustering.sh         ✓ No changes
├── common.sh             ✓ FIXED: log_info stderr
├── config.sh             ✓ No changes
├── decode.sh             ✓ No changes
├── lrs3_prep.sh          ✓ No changes
├── manifests.sh          ✓ No changes
├── normalization.sh      ✓ No changes
├── outputs.sh            ✓ No changes
└── venv/venv_utils.sh    ✓ No changes

run_flat_english_pipeline.sh  ✓ UPDATED: Segment-first architecture + all fixes

VSP-LLM/
├── scripts/make_burn.py       ✓ FIXED: Non-segmented video support
└── src/vsp_llm_decode.py      ✓ FIXED: Logger duplication

vsp-ui/ (or ui/ in galaxy_export)
├── app/
│   ├── server.py              ✓ UPDATED: Whole video support
│   ├── config.py              ✓ Updated segment duration
│   ├── services/
│   │   ├── transcription_manager.py  ✓ New feature
│   │   ├── validator.py       ✓ Enhanced
│   │   └── pipeline_runner.py ✓ K-means toggle
│   └── static/
│       ├── index.html         ✓ Transcription modal
│       ├── app.js             ✓ UPDATED: Upload progress
│       └── style.css          ✓ Updated styling
```

---

## Differences Between Packages

| Feature | linux_container_ready | galaxy_export |
|---------|----------------------|---------------|
| Directory name | `vsp-ui/` | `ui/` |
| Location | `/home/ubuntu/linux_container_ready/` | `/home/ubuntu/vsp_docker/galaxy_export/` |
| Target | Generic container | Docker/Galaxy container |
| All fixes | ✅ Yes | ✅ Yes |
| Documentation | `DEPLOY_TO_CONTAINER.md` | In main CLAUDE.md |

**Everything else is identical.**

---

## Rollback Plan

Both packages include backup instructions in their deployment docs.

Quick rollback:
```bash
cd /workspace
tar xzf ../workspace_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## Success Criteria

After deployment, verify:
- [ ] `bash lib/test_all_modules.sh` - All 37 tests pass
- [ ] Pipeline completes without errors
- [ ] Client outputs generated (reports + burned videos)
- [ ] Burned videos are full-frame (not 88x88 mouth crops)
- [ ] Manual transcriptions work and persist
- [ ] Whisper skips manually transcribed segments
- [ ] UI shows 12s segment duration (not 4s)
- [ ] UI status bar matches pipeline stages
- [ ] No duplicate output in decode logs

---

## Next Steps

1. **Choose your package**:
   - Use `linux_container_ready/` for generic Linux container
   - Use `vsp_docker/galaxy_export/` for Docker/Galaxy

2. **Transfer to container** using your preferred method

3. **Run quick test** (5 minutes)

4. **Run full test** (30 minutes)

5. **Deploy to production** when tests pass

---

## Support Files Created

All in `/tmp/` on EC2:
- `/tmp/linux_container_migration_guide.md` - Complete migration guide
- `/tmp/migration_quick_reference.md` - Quick reference card
- `/tmp/migration_troubleshooting.md` - Common issues and solutions
- `/tmp/migration_execution_checklist.sh` - Step-by-step checklist
- `/tmp/verify_migration.sh` - Post-deployment verification
- `/tmp/compare_versions.sh` - Compare EC2 vs container

---

**Status**: ✅ **READY TO DEPLOY**

Both packages tested and verified. All fixes applied. Ready for manual copy to Linux container.
