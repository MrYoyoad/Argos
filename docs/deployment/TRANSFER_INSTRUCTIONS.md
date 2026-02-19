# Transfer Instructions - VSP Linux Container FINAL

**Package**: vsp_linux_container_FINAL_20260203.tar.gz
**Size**: 1.8 MB
**SHA256**: 1872040879166e7108b92be08376b67c8e1dbd0b70c28ff0722d54f31b56f39b
**Date**: February 3, 2026

---

## Package Contents

This is the **FINAL MASTER DEPLOYMENT PACKAGE** consolidating ALL fixes from all development sessions.

**Included**:
- ✅ 12 critical bug fixes
- ✅ 1 architectural improvement (segment-first normalization)
- ✅ 7 UI features
- ✅ Complete documentation (4 guides)
- ✅ Automated installation scripts
- ✅ Verification scripts

**What's NOT Included** (already in container):
- Model checkpoints (too large)
- Fairseq framework
- Virtual environments
- Processed datasets

---

## Step 1: Download from EC2

### Option A: SCP (Recommended)

From your local machine:

```bash
# Download package
scp -i your-key.pem \
    ubuntu@your-ec2-ip:/home/ubuntu/vsp_linux_container_FINAL_20260203.tar.gz \
    .

# Download checksum
scp -i your-key.pem \
    ubuntu@your-ec2-ip:/home/ubuntu/vsp_linux_container_FINAL_20260203.sha256 \
    .

# Verify checksum
sha256sum -c vsp_linux_container_FINAL_20260203.sha256
# Should show: vsp_linux_container_FINAL_20260203.tar.gz: OK
```

### Option B: rsync (For Slow Connections)

```bash
rsync -avz --progress -e "ssh -i your-key.pem" \
    ubuntu@your-ec2-ip:/home/ubuntu/vsp_linux_container_FINAL_20260203.tar.gz \
    .
```

### Option C: S3 Bucket (For Large Files)

From EC2:
```bash
# Upload to S3
aws s3 cp vsp_linux_container_FINAL_20260203.tar.gz s3://your-bucket/

# Download from local
aws s3 cp s3://your-bucket/vsp_linux_container_FINAL_20260203.tar.gz .
```

---

## Step 2: Transfer to Container Host

Upload the package to the container host machine:

```bash
# From local machine to container host
scp vsp_linux_container_FINAL_20260203.tar.gz \
    user@container-host:/home/ds/Desktop/

# Verify transfer
ssh user@container-host \
    "sha256sum /home/ds/Desktop/vsp_linux_container_FINAL_20260203.tar.gz"
# Should match: 1872040879166e7108b92be08376b67c8e1dbd0b70c28ff0722d54f31b56f39b
```

---

## Step 3: Extract Package

On the container host machine:

```bash
cd /home/ds/Desktop
tar xzf vsp_linux_container_FINAL_20260203.tar.gz
cd vsp_linux_container_FINAL

# Verify contents
ls -lh
# Should show:
#   README.md
#   COMPLETE_CHANGELOG.md
#   INSTALLATION_GUIDE.md
#   TESTING_GUIDE.md
#   FIX_INVENTORY.md
#   INSTALL.sh
#   VERIFY.sh
#   lib/
#   run_flat_english_pipeline.sh
#   VSP-LLM/
#   vsp-ui/
```

---

## Step 4: Run Installation

### Method 1: Automated (Recommended)

Start the container with volume mount:

```bash
# Start container
docker run -it --gpus all \
    -v /home/ds/Desktop/galaxy_export:/host/galaxy_export \
    vsp-llm-pipeline:latest

# Inside container, run installer
cd /host/galaxy_export
bash /host/galaxy_export/../vsp_linux_container_FINAL/INSTALL.sh
```

**Expected Output**:
```
========================================
VSP Linux Container Installation
Package: v1.0.0 FINAL
========================================

[1/6] Checking prerequisites...
✅ Prerequisites OK

[2/6] Creating backup...
✅ Backup created: ../workspace_backup_20260203_140523.tar.gz (25M)

[3/6] Installing components...
  ✅ lib/ modules installed
  ✅ Pipeline script installed
  ✅ VSP-LLM config installed
  ✅ VSP-LLM Python source installed
  ✅ VSP-LLM scripts installed
  ✅ VSP UI installed

[4/6] Verifying installation...
✅ Fix  1: Cython auto-build
✅ Fix  2: max_len config
... (all 12 fixes)

[5/6] Testing pipeline modules...
✅ Module tests: 37/37 PASSED

========================================
Installation Complete!
========================================
```

### Method 2: Manual

See `INSTALLATION_GUIDE.md` for detailed manual installation steps.

---

## Step 5: Verify Installation

Run the verification script:

```bash
bash /path/to/vsp_linux_container_FINAL/VERIFY.sh
```

**Expected Output**:
```
========================================
VSP Linux Container Fix Verification
========================================

✅ Fix  1: Cython auto-build
✅ Fix  2: max_len config
... (all 12 fixes)

✅ All fixes verified successfully!
Package Status: READY TO USE ✅
```

---

## Step 6: Test Pipeline

Quick smoke test:

```bash
cd /workspace  # or /host/galaxy_export
SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test_video.mp4

# Check outputs
ls flat_runs_archive/*/client_outputs/
# Should show: report/ and burned_videos/
```

---

## Troubleshooting Transfer Issues

### Issue: Checksum Mismatch

**Problem**: SHA256 doesn't match after download

**Solution**:
```bash
# Re-download package
rm vsp_linux_container_FINAL_20260203.tar.gz
# Try download again with rsync (more reliable)
rsync -avz --checksum ...
```

### Issue: Partial Download

**Problem**: File size is smaller than expected (should be ~1.8 MB)

**Solution**:
```bash
# Check file size
ls -lh vsp_linux_container_FINAL_20260203.tar.gz
# Should be approximately 1.8M

# If smaller, download again with resume support
rsync -avz --partial --progress ...
```

### Issue: Permission Denied

**Problem**: Cannot extract or execute scripts

**Solution**:
```bash
# Fix permissions
chmod 644 vsp_linux_container_FINAL_20260203.tar.gz
tar xzf vsp_linux_container_FINAL_20260203.tar.gz
cd vsp_linux_container_FINAL
chmod +x INSTALL.sh VERIFY.sh run_flat_english_pipeline.sh
```

### Issue: Container Can't Access Package

**Problem**: Package not visible inside container

**Solution**:
```bash
# Ensure package is in mounted directory
mv vsp_linux_container_FINAL /home/ds/Desktop/galaxy_export/

# Restart container with correct mount
docker run -it --gpus all \
    -v /home/ds/Desktop/galaxy_export:/host/galaxy_export \
    vsp-llm-pipeline:latest

# Package should be at: /host/galaxy_export/vsp_linux_container_FINAL
```

---

## Quick Reference

| Step | Command | Location |
|------|---------|----------|
| **Download** | `scp ubuntu@ec2:~/vsp_linux_container_FINAL_20260203.tar.gz .` | Local machine |
| **Transfer** | `scp vsp_linux_container_FINAL_20260203.tar.gz user@host:/home/ds/Desktop/` | Local machine |
| **Extract** | `tar xzf vsp_linux_container_FINAL_20260203.tar.gz` | Container host |
| **Install** | `bash INSTALL.sh` | Inside container |
| **Verify** | `bash VERIFY.sh` | Inside container |
| **Test** | `SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/video.mp4` | Inside container |

---

## File Locations

**On EC2**:
- Package: `/home/ubuntu/vsp_linux_container_FINAL_20260203.tar.gz`
- Checksum: `/home/ubuntu/vsp_linux_container_FINAL_20260203.sha256`
- Source: `/home/ubuntu/vsp_linux_container_FINAL/`

**On Container Host**:
- Package: `/home/ds/Desktop/vsp_linux_container_FINAL_20260203.tar.gz`
- Extracted: `/home/ds/Desktop/vsp_linux_container_FINAL/`

**Inside Container**:
- Mounted: `/host/galaxy_export/vsp_linux_container_FINAL/`
- Installation target: `/workspace/` or `/host/galaxy_export/`

---

## Package Information

**Version**: 1.0.0 FINAL
**Build Date**: February 3, 2026
**Package Size**: 1.8 MB compressed
**Extracted Size**: ~3 MB
**Source Files**: 100+ files across lib, pipeline, VSP-LLM, vsp-ui

**Consolidates**:
- container_fixes_20260202/ (5 fixes)
- linux_container_ready/ (6 fixes + architecture)
- linux_container_segment_duration_update/ (1 fix)
- vsp_docker/galaxy_export/ (latest working code)

---

## Documentation Included

1. **README.md** - Quick start guide
2. **COMPLETE_CHANGELOG.md** - Full history of all fixes
3. **INSTALLATION_GUIDE.md** - Detailed installation instructions
4. **TESTING_GUIDE.md** - Comprehensive testing procedures
5. **FIX_INVENTORY.md** - Technical inventory of all fixes

---

## Support

For issues during transfer or installation:

1. **Checksum verification failed** → Re-download with rsync
2. **Installation script fails** → See INSTALLATION_GUIDE.md troubleshooting
3. **Verification script fails** → Check which fix is missing, reinstall that component
4. **Pipeline test fails** → See TESTING_GUIDE.md for specific error diagnosis

---

## Success Criteria

After successful transfer and installation, you should have:

- ✅ Package downloaded and checksum verified
- ✅ Package transferred to container host
- ✅ Extracted in accessible location
- ✅ INSTALL.sh completed without errors
- ✅ VERIFY.sh shows all 12 fixes present
- ✅ Smoke test pipeline run completes successfully
- ✅ Client outputs generated (reports + burned videos)

---

**Created**: February 3, 2026
**Package**: vsp_linux_container_FINAL_20260203.tar.gz
**SHA256**: 1872040879166e7108b92be08376b67c8e1dbd0b70c28ff0722d54f31b56f39b
