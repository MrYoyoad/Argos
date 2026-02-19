#!/usr/bin/env bash
# ==============================================================================
# Build Container — Sync EC2 → Container Deployments
# ==============================================================================
# Copies all path-agnostic files from EC2 to both container deployments
# (FINAL tarball and Galaxy Docker export), then prints a reminder of
# container-specific files that need manual attention.
#
# Usage:  bash build_container.sh
#
# This script is idempotent — safe to run multiple times.
# It delegates file comparison and copying to verify_container_sync.sh --fix.
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EC2="$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo "=============================================="
echo "  Build Container — Sync EC2 → Containers"
echo "=============================================="
echo

# --- Step 0: Verify prerequisites ---
VERIFY_SCRIPT="${SCRIPT_DIR}/verify_container_sync.sh"
if [[ ! -f "$VERIFY_SCRIPT" ]]; then
    echo -e "${RED}ERROR: verify_container_sync.sh not found at $VERIFY_SCRIPT${NC}"
    exit 1
fi

FINAL=$(ls -d "${EC2}/vsp_linux_container_FINAL_"*/ 2>/dev/null | sort -r | head -1)
GALAXY="${EC2}/vsp_docker/galaxy_export"

if [[ -z "$FINAL" ]]; then
    echo -e "${RED}ERROR: No vsp_linux_container_FINAL_*/ directory found${NC}"
    exit 1
fi
if [[ ! -d "$GALAXY" ]]; then
    echo -e "${RED}ERROR: Galaxy directory not found at $GALAXY${NC}"
    exit 1
fi

echo "  EC2:    $EC2"
echo "  FINAL:  $FINAL"
echo "  Galaxy: $GALAXY"
echo

# --- Step 1: Copy path-agnostic files ---
echo -e "${BOLD}Step 1: Syncing path-agnostic files...${NC}"
echo
bash "$VERIFY_SCRIPT" --fix
VERIFY_EXIT=$?
echo

# --- Step 2: Reminder of container-specific files ---
echo -e "${BOLD}Step 2: Container-specific files (require manual sync)${NC}"
echo
echo "These files have intentional differences between EC2 and containers."
echo "They contain container-specific paths/logic and cannot be auto-copied."
echo "Review these manually after making EC2 changes:"
echo
echo "  Shell scripts:"
echo "    run_flat_english_pipeline.sh   (HOME vs SCRIPT_DIR path strategy)"
echo "    lib/asr.sh                     (transcription paths, whisper cache)"
echo "    lib/lrs3_prep.sh               (PREP_VENV passthrough)"
echo "    VSP-LLM/scripts/decode.sh      (fairseq auto-patch block)"
echo
echo "  UI (vsp-ui/):"
echo "    app/server.py                  (BASE_DIR, path imports, endpoints)"
echo "    app/static/app.js              (UI feature delta)"
echo "    app/static/index.html          (UI layout delta)"
echo "    app/static/style.css           (UI style delta)"
echo

# --- Summary ---
echo "=============================================="
if [[ $VERIFY_EXIT -eq 0 ]]; then
    echo -e "  ${GREEN}All path-agnostic files are in sync.${NC}"
else
    echo -e "  ${YELLOW}Some files were out of sync and have been fixed.${NC}"
    echo "  Run 'bash verify_container_sync.sh' to confirm."
fi
echo "=============================================="
