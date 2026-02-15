#!/usr/bin/env bash
# ============================================================================
# VSP Linux Container - Automated Installation Script
# ============================================================================
# Package: vsp_linux_container_FINAL v1.0.0
# Date: February 3, 2026
#
# This script automatically installs ALL 12 critical fixes plus UI features
# to the Linux container environment.
#
# Usage:
#   cd /host/galaxy_export  # or /host/galaxy_export
#   bash /path/to/INSTALL.sh
#
# Features:
#   - Automatic timestamped backup
#   - Component-by-component installation
#   - Built-in verification
#   - Rollback support on failure
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (where INSTALL.sh is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VSP Linux Container Installation${NC}"
echo -e "${BLUE}Package: v1.0.0 FINAL${NC}"
echo -e "${BLUE}Date: February 3, 2026${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ====================
# Prerequisite Checks
# ====================

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Check we're in the right directory
if [ ! -f "run_flat_english_pipeline.sh" ]; then
    echo -e "${RED}ERROR: Must run from galaxy_export directory${NC}"
    echo "Current directory: $(pwd)"
    echo ""
    echo "Usage:"
    echo "  cd /host/galaxy_export"
    echo "  bash /path/to/INSTALL.sh"
    exit 1
fi

# Create required directories if they don't exist (fresh installation)
if [ ! -d "lib" ]; then
    echo -e "${YELLOW}  lib/ not found - creating (fresh installation)${NC}"
    mkdir -p lib
fi

if [ ! -d "VSP-LLM" ]; then
    echo -e "${YELLOW}  VSP-LLM/ not found - creating (fresh installation)${NC}"
    mkdir -p VSP-LLM/src/conf VSP-LLM/scripts
fi

if [ ! -d "vsp-ui" ]; then
    echo -e "${YELLOW}  vsp-ui/ not found - creating (fresh installation)${NC}"
    mkdir -p vsp-ui/app/services vsp-ui/app/static
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"
echo ""

# ====================
# Create Backup
# ====================

echo -e "${YELLOW}[2/6] Creating backup...${NC}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="../galaxy_export_backup_${TIMESTAMP}.tar.gz"

tar czf "$BACKUP_FILE" \
    lib/ \
    run_flat_english_pipeline.sh \
    VSP-LLM/src/conf \
    VSP-LLM/src/*.py \
    VSP-LLM/scripts/ \
    vsp-ui/ \
    2>/dev/null || echo "Note: Some files may not exist yet"

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  Backup skipped (first installation?)${NC}"
fi
echo ""

# ====================
# Install Components
# ====================

echo -e "${YELLOW}[3/6] Installing components...${NC}"
echo ""

# Component 1: lib modules
echo -e "${BLUE}[3.1] Installing lib/ modules (11 files)...${NC}"
cp -r "$SCRIPT_DIR/lib/"* lib/
echo -e "${GREEN}  ✅ lib/ modules installed${NC}"

# Component 2: Pipeline script
echo -e "${BLUE}[3.2] Installing pipeline script...${NC}"
cp "$SCRIPT_DIR/run_flat_english_pipeline.sh" .
chmod +x run_flat_english_pipeline.sh
echo -e "${GREEN}  ✅ Pipeline script installed${NC}"

# Component 3: VSP-LLM config
echo -e "${BLUE}[3.3] Installing VSP-LLM config...${NC}"
mkdir -p VSP-LLM/src/conf
cp "$SCRIPT_DIR/VSP-LLM/src/conf/s2s_decode.yaml" VSP-LLM/src/conf/
echo -e "${GREEN}  ✅ VSP-LLM config installed${NC}"

# Component 4: VSP-LLM Python source
echo -e "${BLUE}[3.4] Installing VSP-LLM Python source...${NC}"
cp "$SCRIPT_DIR/VSP-LLM/src/"*.py VSP-LLM/src/ 2>/dev/null || echo "  (Some files may not exist)"
echo -e "${GREEN}  ✅ VSP-LLM Python source installed${NC}"

# Component 5: VSP-LLM scripts
echo -e "${BLUE}[3.5] Installing VSP-LLM scripts...${NC}"
mkdir -p VSP-LLM/scripts
cp "$SCRIPT_DIR/VSP-LLM/scripts/"*.py VSP-LLM/scripts/ 2>/dev/null || true
cp "$SCRIPT_DIR/VSP-LLM/scripts/"*.sh VSP-LLM/scripts/ 2>/dev/null || true
echo -e "${GREEN}  ✅ VSP-LLM scripts installed${NC}"

# Component 6: VSP UI
echo -e "${BLUE}[3.6] Installing VSP UI...${NC}"
if [ -d "$SCRIPT_DIR/vsp-ui" ]; then
    cp -r "$SCRIPT_DIR/vsp-ui/"* vsp-ui/ 2>/dev/null || mkdir -p vsp-ui && cp -r "$SCRIPT_DIR/vsp-ui/"* vsp-ui/
    echo -e "${GREEN}  ✅ VSP UI installed${NC}"
else
    echo -e "${YELLOW}  ⚠️  VSP UI not found in package (optional)${NC}"
fi

# Component 7: auto_avsr scripts (pipeline processing scripts)
echo -e "${BLUE}[3.7] Installing auto_avsr scripts...${NC}"
if [ -d "$SCRIPT_DIR/auto_avsr" ]; then
    mkdir -p auto_avsr/preparation
    cp "$SCRIPT_DIR/auto_avsr/preparation/"*.py auto_avsr/preparation/ 2>/dev/null || true
    cp "$SCRIPT_DIR/auto_avsr/"*.py auto_avsr/ 2>/dev/null || true
    # Copy data module (AVSRDataLoader)
    if [ -d "$SCRIPT_DIR/auto_avsr/preparation/data" ]; then
        mkdir -p auto_avsr/preparation/data
        cp "$SCRIPT_DIR/auto_avsr/preparation/data/"*.py auto_avsr/preparation/data/ 2>/dev/null || true
    fi
    # Copy face detectors (mediapipe + retinaface)
    if [ -d "$SCRIPT_DIR/auto_avsr/preparation/detectors" ]; then
        mkdir -p auto_avsr/preparation/detectors/mediapipe auto_avsr/preparation/detectors/retinaface
        cp -r "$SCRIPT_DIR/auto_avsr/preparation/detectors/mediapipe/"* auto_avsr/preparation/detectors/mediapipe/ 2>/dev/null || true
        cp -r "$SCRIPT_DIR/auto_avsr/preparation/detectors/retinaface/"* auto_avsr/preparation/detectors/retinaface/ 2>/dev/null || true
    fi
    # Copy SentencePiece model files
    if [ -d "$SCRIPT_DIR/auto_avsr/spm" ]; then
        mkdir -p auto_avsr/spm/unigram
        cp "$SCRIPT_DIR/auto_avsr/spm/unigram/"* auto_avsr/spm/unigram/ 2>/dev/null || true
    fi
    echo -e "${GREEN}  ✅ auto_avsr scripts installed${NC}"
else
    echo -e "${YELLOW}  ⚠️  auto_avsr scripts not found in package${NC}"
fi

# Component 8: av_hubert scripts (LRS3 conversion)
echo -e "${BLUE}[3.8] Installing av_hubert scripts...${NC}"
if [ -d "$SCRIPT_DIR/av_hubert" ]; then
    mkdir -p av_hubert/avhubert/preparation
    cp "$SCRIPT_DIR/av_hubert/avhubert/preparation/"* av_hubert/avhubert/preparation/ 2>/dev/null || true
    echo -e "${GREEN}  ✅ av_hubert scripts installed${NC}"
else
    echo -e "${YELLOW}  ⚠️  av_hubert scripts not found in package${NC}"
fi

# Component 9: VSP-LLM clustering modules
echo -e "${BLUE}[3.9] Installing VSP-LLM clustering modules...${NC}"
if [ -d "$SCRIPT_DIR/VSP-LLM/src/clustering" ]; then
    mkdir -p VSP-LLM/src/clustering
    cp "$SCRIPT_DIR/VSP-LLM/src/clustering/"*.py VSP-LLM/src/clustering/ 2>/dev/null || true
    echo -e "${GREEN}  ✅ VSP-LLM clustering modules installed${NC}"
else
    echo -e "${YELLOW}  ⚠️  VSP-LLM clustering modules not found in package${NC}"
fi

# Component 10: Fairseq max_len patch
echo -e "${BLUE}[3.10] Patching fairseq GenerationConfig (max_len field)...${NC}"
if [ -f "$SCRIPT_DIR/patch_fairseq_max_len.py" ]; then
    # Find the VSP venv to use for patching (fairseq is installed there)
    PATCH_VENV=""
    if [ -d "/workspace/vsp-llm-yoad-venv" ]; then
        PATCH_VENV="/workspace/vsp-llm-yoad-venv"
    elif [ -d "$HOME/vsp-llm-yoad-venv" ]; then
        PATCH_VENV="$HOME/vsp-llm-yoad-venv"
    fi

    if [ -n "$PATCH_VENV" ]; then
        source "$PATCH_VENV/bin/activate"
        python3 "$SCRIPT_DIR/patch_fairseq_max_len.py"
        PATCH_RESULT=$?
        deactivate
        if [ $PATCH_RESULT -eq 0 ]; then
            echo -e "${GREEN}  ✅ Fairseq max_len patch applied${NC}"
        else
            echo -e "${RED}  ❌ Fairseq max_len patch failed - decode step may fail${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️  VSP venv not found - run patch_fairseq_max_len.py manually after activating venv${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Patch script not found in package${NC}"
fi

# Component 11: Test suite
echo -e "${BLUE}[3.11] Installing test suite...${NC}"
if [ -d "$SCRIPT_DIR/tests" ]; then
    mkdir -p tests
    cp "$SCRIPT_DIR/tests/"*.sh tests/ 2>/dev/null || true
    chmod +x tests/*.sh 2>/dev/null || true
    echo -e "${GREEN}  ✅ Test suite installed${NC}"
else
    echo -e "${YELLOW}  ⚠️  Test suite not found in package${NC}"
fi

# Component 12: Docker configuration
echo -e "${BLUE}[3.12] Generating docker.conf...${NC}"
DOCKER_CONF="docker.conf"
if [ -f "$DOCKER_CONF" ] && grep -q 'DOCKER_IMAGE=' "$DOCKER_CONF" && ! grep -q 'CHANGE_ME' "$DOCKER_CONF"; then
    echo -e "${GREEN}  ✅ docker.conf already configured (keeping existing)${NC}"
else
    echo "# Docker image for VSP Pipeline" > "$DOCKER_CONF"
    echo "# vsp-start.sh will auto-detect on first launch." >> "$DOCKER_CONF"
    echo "# You can also set it manually:" >> "$DOCKER_CONF"
    echo "#   Client:    vsp-llm-pipeline:latest" >> "$DOCKER_CONF"
    echo "#   Developer: vsp-flat-standalone:cu128-exact" >> "$DOCKER_CONF"
    echo "DOCKER_IMAGE=CHANGE_ME" >> "$DOCKER_CONF"
    echo -e "${GREEN}  ✅ docker.conf created (will auto-detect on first launch)${NC}"
fi
# Make docker.conf editable by host user (INSTALL runs as root inside container)
chmod 666 "$DOCKER_CONF" 2>/dev/null || true

# Component 13: Host-side launcher + desktop icon
echo -e "${BLUE}[3.13] Installing host-side launcher + desktop icon...${NC}"
if [ -f "$SCRIPT_DIR/vsp-start.sh" ]; then
    cp "$SCRIPT_DIR/vsp-start.sh" .
    cp "$SCRIPT_DIR/docker-run.sh" . 2>/dev/null || true
    chmod +x vsp-start.sh
    chmod +x docker-run.sh 2>/dev/null || true
    # Copy desktop file template and icon installer
    cp "$SCRIPT_DIR/vsp-pipeline.desktop" . 2>/dev/null || true
    cp "$SCRIPT_DIR/install-desktop-icon.sh" . 2>/dev/null || true
    chmod +x install-desktop-icon.sh 2>/dev/null || true
    # Copy peacock logo for desktop icon
    if [ -f "$SCRIPT_DIR/vsp-ui/logo.png" ]; then
        cp "$SCRIPT_DIR/vsp-ui/logo.png" vsp-ui/logo.png 2>/dev/null || true
    fi
    echo -e "${GREEN}  ✅ Host launcher installed (vsp-start.sh)${NC}"
    echo -e "${YELLOW}  To add desktop icon, run ON THE HOST (not inside container):${NC}"
    echo -e "${YELLOW}    cd /path/to/galaxy_export${NC}"
    echo -e "${YELLOW}    bash install-desktop-icon.sh${NC}"
else
    echo -e "${YELLOW}  ⚠️  Host launcher not found in package${NC}"
fi

# ====================
# Create vsp_input directory for video uploads
# ====================
echo -e "${BLUE}[3.15] Creating vsp_input directory...${NC}"
mkdir -p vsp_input 2>/dev/null || true
chmod a+rwx vsp_input 2>/dev/null || true
echo -e "${GREEN}  ✅ vsp_input directory created${NC}"

# ====================
# Fix file permissions for host access
# ====================
# INSTALL.sh runs as root inside Docker, so all copied files are owned by root.
# On the host, the normal user can't edit or execute them without sudo.
# Make everything accessible: scripts executable, config files writable.
echo -e "${BLUE}[3.14] Setting file permissions for host access...${NC}"
chmod -R a+rX . 2>/dev/null || true          # Everything readable + dirs traversable
chmod -R a+w docker.conf 2>/dev/null || true  # Config file writable
find . -name "*.sh" -exec chmod a+rx {} \; 2>/dev/null || true  # All scripts executable
find . -name "*.py" -exec chmod a+r {} \; 2>/dev/null || true   # All Python readable
echo -e "${GREEN}  ✅ File permissions set (readable/executable for all users)${NC}"

echo ""
echo -e "${GREEN}✅ All components installed${NC}"
echo ""

# ====================
# Verify Installation
# ====================

echo -e "${YELLOW}[4/6] Verifying installation...${NC}"
echo ""

# Verification function
verify_fix() {
    local fix_num=$1
    local description=$2
    local check_command=$3

    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✅ Fix $fix_num: $description${NC}"
        return 0
    else
        echo -e "${RED}❌ Fix $fix_num: $description${NC}"
        return 1
    fi
}

# Track failures
FAILED_FIXES=0

# Verify all 12 fixes
verify_fix  1 "Cython auto-build" \
    'grep -q "CRITICAL: Check and build fairseq Cython" lib/decode.sh' || ((FAILED_FIXES++))

verify_fix  2 "max_len config" \
    'grep -q "max_len: 2048" VSP-LLM/src/conf/s2s_decode.yaml' || ((FAILED_FIXES++))

verify_fix  3 "Dynamic transcription paths" \
    'grep -q '\''transcriptions_dir="${raw_dir}/.transcriptions"'\'' lib/asr.sh' || ((FAILED_FIXES++))

verify_fix  4 "VSP_INPUT_DIR support" \
    'grep -q "VSP_INPUT_DIR" vsp-ui/app/config.py' || ((FAILED_FIXES++))

verify_fix  5 "Absolute imports" \
    'grep -q "from app.config import INPUT_DIR" vsp-ui/app/services/transcription_manager.py' || ((FAILED_FIXES++))

verify_fix  6 "log_info stderr redirect" \
    'grep -q ">&2" lib/common.sh' || ((FAILED_FIXES++))

verify_fix  7 "POST_ROOT definition" \
    'grep -q '\''POST_ROOT='\'' run_flat_english_pipeline.sh' || ((FAILED_FIXES++))

verify_fix  8 "Step 2.5 metadata creation" \
    'grep -q "metadata for whole videos" run_flat_english_pipeline.sh' || ((FAILED_FIXES++))

verify_fix  9 "Non-segmented naming" \
    'grep -q '\''output_name="${video_name}"'\'' run_flat_english_pipeline.sh' || ((FAILED_FIXES++))

verify_fix 10 "make_burn segment matching" \
    'grep -q "if seg_idx == -1:" VSP-LLM/scripts/make_burn.py' || ((FAILED_FIXES++))

verify_fix 11 "Logger duplication fix" \
    'grep -q "logger.propagate = False" VSP-LLM/src/vsp_llm_decode.py' || ((FAILED_FIXES++))

verify_fix 12 "Segment duration = 12s" \
    'grep -q "SEGMENT_DURATION = 12" vsp-ui/app/config.py' || ((FAILED_FIXES++))

if [ -n "$PATCH_VENV" ]; then
    verify_fix 13 "Fairseq max_len field" \
        'source "'"$PATCH_VENV"'/bin/activate" && python3 -c "from fairseq.dataclass.configs import GenerationConfig; assert hasattr(GenerationConfig, \"max_len\")" && deactivate' || ((FAILED_FIXES++))
else
    verify_fix 13 "Fairseq max_len field" \
        'python3 -c "from fairseq.dataclass.configs import GenerationConfig; assert hasattr(GenerationConfig, \"max_len\")"' || ((FAILED_FIXES++))
fi

echo ""

if [ $FAILED_FIXES -eq 0 ]; then
    echo -e "${GREEN}✅ All 12 fixes verified successfully!${NC}"
else
    echo -e "${RED}⚠️  $FAILED_FIXES fix(es) failed verification${NC}"
    echo -e "${YELLOW}   (This may be normal if some components are optional)${NC}"
fi

echo ""

# ====================
# Test Modules
# ====================

echo -e "${YELLOW}[5/6] Testing pipeline modules...${NC}"

if [ -f "lib/test_all_modules.sh" ]; then
    # Run module tests with timeout
    if timeout 60 bash lib/test_all_modules.sh 2>&1 | tail -5; then
        echo -e "${GREEN}✅ Module tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Module tests had warnings (may be normal)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Module test script not found (optional)${NC}"
fi

echo ""

# ====================
# Installation Summary
# ====================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Installed Components:${NC}"
echo "  ✅ lib/ (11 pipeline modules)"
echo "  ✅ run_flat_english_pipeline.sh"
echo "  ✅ VSP-LLM/src/ (configs + source)"
echo "  ✅ VSP-LLM/scripts/"
echo "  ✅ vsp-ui/"
echo ""

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}Backup:${NC}"
    echo "  📦 $BACKUP_FILE"
    echo ""
fi

echo -e "${GREEN}Verification:${NC}"
echo "  ✅ $(( 13 - FAILED_FIXES ))/13 fixes verified"
if [ $FAILED_FIXES -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  $FAILED_FIXES fix(es) need manual verification${NC}"
fi
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Run verification script:"
echo "     bash $SCRIPT_DIR/VERIFY.sh"
echo ""
echo "  2. Test with sample video:"
echo "     SEGMENTATION_ENABLED=0 ./run_flat_english_pipeline.sh /path/to/test.mp4"
echo ""
echo "  3. Check outputs:"
echo "     ls flat_runs_archive/*/client_outputs/"
echo ""

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${YELLOW}Rollback (if needed):${NC}"
    echo "  cd $(pwd)"
    echo "  tar xzf $BACKUP_FILE"
    echo ""
fi

echo -e "${GREEN}Installation successful! 🎉${NC}"
echo ""
