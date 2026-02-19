# Container Deployment Checklist

This checklist ensures safe and successful deployment of VSP pipeline updates to the Linux container environment.

## Pre-Deployment

### 1. EC2 Testing (✓ Required)
- [ ] All features tested end-to-end on EC2
- [ ] Pipeline runs successfully on sample videos
- [ ] No errors in logs
- [ ] Output quality verified (transcriptions, burned videos, reports)
- [ ] Git commits created for all changes
- [ ] EC2 version tagged (e.g., `ec2-v1.x.x`)

### 2. Code Review (✓ Recommended)
- [ ] Review git diff since last container sync
- [ ] Check for hardcoded paths (`/home/ubuntu` should use `$HOME` or `${EXPORT_ROOT}`)
- [ ] Verify virtual environment paths are correct
- [ ] Check for environment-specific configurations

### 3. Documentation Updated (✓ Required)
- [ ] CLAUDE.md updated with new features/changes
- [ ] Pending updates section cleared for applied changes
- [ ] New features documented in `docs/features/`

## Deployment Process

### 4. Run Automated Sync (✓ Required)
```bash
cd /home/ubuntu

# Dry run first to preview changes
./sync/sync_to_container.sh --dry-run

# Review dry run output, then run actual sync
./sync/sync_to_container.sh

# Validation runs automatically at end of sync
```

### 5. Manual Verification (✓ Required)
- [ ] Check validation output - all critical files present?
- [ ] No hardcoded `/home/ubuntu` paths in container version?
- [ ] File sizes reasonable? (server.py should be ~37KB, not 31KB)
- [ ] All 8 pending updates present (if applying batch):
  - [ ] Video exclusion feature (`.excluded/` logic)
  - [ ] K-means training toggle
  - [ ] Transcription manager (`transcription_manager.py`)
  - [ ] Segment duration 12s default
  - [ ] UI status bar fix
  - [ ] Original video serving (ffmpeg extraction)
  - [ ] TranscriptionManager API fix
  - [ ] Delete transcription screen fix

### 6. Container Build Test (✓ Required)
```bash
cd /home/ubuntu/vsp_docker

# Build container image
docker build -t vsp-pipeline:test-v1.x.x .

# Check build succeeded
docker images | grep vsp-pipeline
```

### 7. Container Staging Test (✓ Recommended)
```bash
# Run container interactively
docker run -it --rm \
  -v /path/to/test/videos:/host/galaxy_export/ui/input_videos \
  vsp-pipeline:test-v1.x.x \
  /bin/bash

# Inside container, test pipeline
cd /workspace
./run_flat_english_pipeline.sh /host/galaxy_export/ui/input_videos

# Verify:
# - Pipeline completes without errors
# - Outputs generated correctly
# - UI features work (if testing UI)
```

## Post-Deployment

### 8. Git Tagging (✓ Required)
```bash
cd /home/ubuntu

# Commit container sync
git add vsp_docker/galaxy_export
git commit -m "Sync: Container version updated from ec2-v1.x.x"

# Tag container version
git tag -a container-v1.x.x -m "Container deployment v1.x.x"

# Push to remote (if configured)
git push origin main --tags
```

### 9. Production Deployment (⚠️ Organization-Specific)
- [ ] Copy container image to production server
- [ ] Stop existing container (if running)
- [ ] Start new container version
- [ ] Verify container starts successfully
- [ ] Test with production data (small sample first)
- [ ] Monitor logs for errors

### 10. Rollback Plan (✓ Always Prepared)
If deployment fails:

```bash
# Option A: Restore previous container export
cd /home/ubuntu/vsp_docker
mv galaxy_export galaxy_export_failed
mv galaxy_export_backup_YYYYMMDD_HHMMSS galaxy_export

# Option B: Revert to previous git tag
git checkout container-v1.OLD.x
git checkout vsp_docker/galaxy_export

# Rebuild with old version
docker build -t vsp-pipeline:rollback .
```

## Common Issues

### Issue: Validation fails with missing files
**Solution**: Re-run sync, check for errors in sync output

### Issue: Hardcoded `/home/ubuntu` paths found
**Solution**: Update source files to use `${EXPORT_ROOT}` or environment-aware paths, re-sync

### Issue: Container build fails
**Solution**: Check Dockerfile, verify dependencies are installable, check base image compatibility

### Issue: Pipeline fails in container but works on EC2
**Solution**:
- Check virtual environment paths
- Verify model checkpoints accessible
- Check disk space and memory limits
- Review environment variables

## Notes

- Always test in container staging before production deployment
- Keep at least 2 previous container versions for rollback
- Document any manual changes made during deployment
- Update this checklist based on lessons learned

## Version History

| Container Version | EC2 Version | Date | Notes |
|-------------------|-------------|------|-------|
| container-v1.0.0 | ec2-v1.0.0 | 2026-01-29 | Initial sync system |
| container-v1.1.0 | ec2-v1.0.0 | TBD | 8 pending updates applied |
