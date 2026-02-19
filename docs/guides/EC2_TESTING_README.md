# EC2 Pipeline Testing Suite

This directory contains comprehensive test scripts to verify that all pipeline updates still work correctly on EC2 after adding Linux container environment detection.

## Test Scripts

### 1. `run_all_ec2_tests.sh` - Master Test Runner ⭐

**Run this first!** Executes all tests and provides a comprehensive report.

```bash
./run_all_ec2_tests.sh
```

**What it tests:**
- Runs all three test suites below
- Provides color-coded results
- Shows timing for each test
- Comprehensive final summary

**Expected output:**
```
╔════════════════════════════════════════╗
║  ✓ ALL EC2 TESTS PASSED SUCCESSFULLY  ║
╚════════════════════════════════════════╝
```

---

### 2. `test_ec2_environment.sh` - Environment Detection

Tests that environment detection correctly identifies EC2 and sets appropriate paths.

```bash
./test_ec2_environment.sh
```

**What it tests:**
- ✅ `lib/config.sh` detects `ENV_TYPE=ec2`
- ✅ `BASE_PATH=/home/ubuntu` is set correctly
- ✅ All component paths (`AUTO_AVSR`, `VSP`, etc.) correct
- ✅ `lib/asr.sh` transcription path = `/home/ubuntu/vsp_input/.transcriptions`
- ✅ All lib modules can be sourced without errors
- ✅ `av_hubert` scripts have environment detection
- ✅ `asr_to_words_notime.py` Whisper cache path correct
- ✅ UI `config.py` detects EC2 correctly (Python)
- ✅ UI `transcription_manager.py` paths correct (Python)
- ✅ `run_flat_preprocess_batch.sh` environment detection
- ✅ Main pipeline script integrity
- ✅ Virtual environment paths exist
- ✅ Critical directories present

**Test count:** ~50+ assertions

---

### 3. `test_pipeline_modules.sh` - Module Functionality

Tests that all lib modules work correctly and functions are properly exported.

```bash
./test_pipeline_modules.sh
```

**What it tests:**
- ✅ `lib/common.sh` - logging and validation functions
- ✅ `lib/config.sh` - path resolution functions
- ✅ `lib/venv/venv_utils.sh` - venv activation/deactivation
- ✅ `lib/normalization.sh` - video processing functions
- ✅ `lib/asr.sh` - ASR transcription functions
- ✅ `lib/lrs3_prep.sh` - LRS3 format conversion
- ✅ `lib/manifests.sh` - manifest generation
- ✅ `lib/clustering.sh` - k-means clustering
- ✅ `lib/decode.sh` - VSP-LLM decode
- ✅ `lib/outputs.sh` - client outputs
- ✅ `lib/archive.sh` - archive management
- ✅ Module integration (all can be sourced together)
- ✅ No function name conflicts

**Test count:** ~40+ assertions

---

### 4. `test_pipeline_smoke.sh` - Dependencies & Files

Quick smoke test that validates pipeline setup without running the full pipeline.

```bash
./test_pipeline_smoke.sh
```

**What it tests:**
- ✅ Critical executables (`ffmpeg`, `ffprobe`, `python3`, `bash`)
- ✅ Virtual environments exist and have activate scripts
- ✅ Main pipeline script exists and is executable
- ✅ All lib modules have valid syntax
- ✅ Component directories exist
- ✅ Critical scripts present
- ✅ Model checkpoints exist
- ✅ Whisper model cache present
- ✅ UI components present
- ✅ Environment variables correct

**Test count:** ~60+ checks

---

## Quick Start

**Recommended workflow:**

1. **Run the master test suite:**
   ```bash
   ./run_all_ec2_tests.sh
   ```

2. **If all tests pass:**
   ```
   ✓ Pipeline is ready to use on EC2
   ✓ Environment detection works correctly
   ✓ All modules functional
   ✓ All dependencies present
   ```

3. **If any tests fail:**
   - Review the specific test output
   - Fix the issues identified
   - Re-run the tests
   - Individual test scripts can be run separately for debugging

---

## What These Tests Verify

### Environment Detection
After adding container support, we need to ensure EC2 detection still works:
- All bash scripts correctly identify EC2 environment
- All Python scripts correctly identify EC2 environment
- Paths resolve to `/home/ubuntu/` (not `/workspace/` or `/host/`)
- Transcription directory is `/home/ubuntu/vsp_input/.transcriptions`

### Module Functionality
After refactoring into modules, we need to ensure they work:
- All functions properly exported
- No naming conflicts between modules
- Path resolution functions work correctly
- Integration works (all modules can be sourced together)

### Pipeline Readiness
Before running the full pipeline, we need to verify:
- All dependencies installed
- All scripts present with valid syntax
- All virtual environments configured
- All model checkpoints present
- All directories exist

---

## Test Results Interpretation

### All Green ✓
```
✓ ALL EC2 TESTS PASSED SUCCESSFULLY
```
**Meaning:** Pipeline is ready for production use on EC2.
- Environment detection works correctly
- All modules functional
- All dependencies present
- Safe to run the full pipeline

### Some Red ✗
```
✗ SOME EC2 TESTS FAILED
```
**Action Required:** Review failures and fix before running pipeline.

**Common failure patterns:**
1. **Missing directory:** Install or create the missing component
2. **Syntax error:** Fix the syntax in the indicated script
3. **Wrong path:** Check environment detection logic
4. **Missing function:** Check module exports

---

## When to Run These Tests

### Always Run After:
- ✅ Modifying environment detection logic
- ✅ Adding new modules to `lib/`
- ✅ Changing path resolution functions
- ✅ Updating Python path detection (UI)
- ✅ Pulling updates from git
- ✅ Fresh installation on new EC2 instance

### Quick Validation:
```bash
# Quick check (takes ~10 seconds)
./test_pipeline_smoke.sh

# Full validation (takes ~30 seconds)
./run_all_ec2_tests.sh
```

---

## Test Coverage

| Component | Environment | Modules | Smoke | Total |
|-----------|-------------|---------|-------|-------|
| Bash lib modules | ✓ | ✓ | ✓ | 100% |
| Python UI | ✓ | - | ✓ | 100% |
| Component scripts | ✓ | - | ✓ | 100% |
| Dependencies | - | - | ✓ | 100% |
| Virtual envs | ✓ | ✓ | ✓ | 100% |
| Model checkpoints | - | - | ✓ | 100% |
| Integration | - | ✓ | - | 100% |

**Total Coverage:** All critical paths and components tested

---

## Troubleshooting

### Test hangs or doesn't complete
- Check for syntax errors: `bash -n <script.sh>`
- Look for infinite loops in sourced modules
- Check file permissions

### Test fails with "command not found"
- Check `$PATH` includes required executables
- Verify virtual environments activated correctly
- Check module exports with `declare -F`

### Test fails with "file not found"
- Verify you're running from `/home/ubuntu/`
- Check relative paths in scripts
- Ensure all components installed

### Environment detection fails
- Check `/home/ubuntu/` directory exists
- Verify `$HOME` environment variable
- Check no `/host/` or `/workspace/` directories exist

---

## Adding New Tests

To add new tests to the suite:

1. Create new test script: `test_my_feature.sh`
2. Follow the pattern from existing scripts
3. Use consistent pass/fail output format
4. Add to `run_all_ec2_tests.sh`

**Test script template:**
```bash
#!/usr/bin/env bash
set -euo pipefail

PASSED=0
FAILED=0

pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((PASSED++))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((FAILED++))
}

# Your tests here...

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
```

---

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```bash
# In your CI/CD script:
cd /home/ubuntu
./run_all_ec2_tests.sh || exit 1

# Only run pipeline if tests pass
./run_flat_english_pipeline.sh /path/to/videos
```

---

## Summary

✅ **3 comprehensive test suites**
✅ **150+ individual test assertions**
✅ **Tests all critical paths and components**
✅ **Fast execution (~30 seconds total)**
✅ **Clear pass/fail reporting**
✅ **Safe to run anytime**

**Run the tests before every major pipeline execution to ensure everything is working correctly!**

```bash
./run_all_ec2_tests.sh && echo "Ready to run pipeline!"
```
