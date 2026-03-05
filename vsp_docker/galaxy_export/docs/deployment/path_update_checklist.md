# Path Update Checklist for Linux Container

## Critical Scripts to Update (Priority Order)

### 1. Master Pipeline Script
**File:** `run_flat_english_pipeline.sh`
- [ ] Line 1: Shebang and comments
- [ ] Lines 15-30: All directory paths (AUTO_AVSR_DIR, VSP_LLM_DIR, etc.)
- [ ] Line 52+: Virtual environment paths
- [ ] Line 100+: All script calls with full paths
- [ ] Search for: `/home/ubuntu`, `~/`, check all variable assignments

### 2. VSP-LLM Scripts
**Files in:** `VSP-LLM/scripts/`
- [ ] `decode.sh` - MODEL_PATH, DATA_PATH, checkpoint paths
- [ ] `run_flat_kmeans.sh` - LRS3_ROOT, FAIRSEQ_ROOT, checkpoint paths
- [ ] `run_cluster_counts.sh` - PREP_ROOT, VSP_ROOT paths
- [ ] `run_flat_decode.sh` - All path variables

### 3. AV-HuBERT Preparation
**File:** `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh`
- [ ] SRC_PATH variable
- [ ] DEST_PATH variable
- [ ] Any script execution paths

### 4. Auto-AVSR Preprocessing
**File:** `auto_avsr/preparation/run_flat_preprocess_batch.sh`
- [ ] DATA_DIR paths
- [ ] Script execution paths
- [ ] Virtual environment activation

### 5. VSP-UI Configuration
**Files:**
- [ ] `vsp-ui/app/config.py` - All directory paths (INPUT_DIR, etc.)
- [ ] `vsp-ui/app/server.py` - Hardcoded paths (if any)
- [ ] `vsp-ui/app/services/pipeline_runner.py` - Pipeline script path

### 6. Python Scripts with Hardcoded Paths
- [ ] `VSP-LLM/scripts/make_report.py`
- [ ] `VSP-LLM/scripts/make_burn.py`
- [ ] `auto_avsr/asr_to_words_notime.py` (if has paths)

## Quick Search Commands

```bash
# Find all files with EC2 paths
cd /workspace
grep -r "/home/ubuntu" --include="*.sh" --include="*.py" --exclude-dir=venv --exclude-dir=.git

# Find all files with tilde paths
grep -r "~/" --include="*.sh" --include="*.py" --exclude-dir=venv --exclude-dir=.git
```

## Automated Path Replacement

```bash
# CAREFUL: Test on one file first!
# Replace /home/ubuntu with /workspace
find /workspace -type f \( -name "*.sh" -o -name "*.py" \) \
  -not -path "*/venv/*" \
  -not -path "*/.git/*" \
  -exec sed -i 's|/home/ubuntu|/workspace|g' {} +

# Replace ~/ with /workspace/ (more complex due to context)
# Recommend manual review for these
```
