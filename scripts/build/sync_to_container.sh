#!/usr/bin/env bash
set -euo pipefail

# ==================================================
# Sync EC2 Version to Linux Container Export
# ==================================================
# This script syncs the EC2 development version to the
# container deployment directory, translating hardcoded paths.
#
# Usage:
#   ./sync/sync_to_container.sh [--dry-run]
#
# Environment:
#   CONTAINER_EXPORT - Override default container export directory
# ==================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTAINER_EXPORT="${CONTAINER_EXPORT:-${ROOT_DIR}/vsp_docker/galaxy_export}"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=========================================="
    echo "DRY RUN MODE - No files will be modified"
    echo "=========================================="
fi

echo "==================================================="
echo "VSP Pipeline EC2 → Container Sync"
echo "==================================================="
echo "Source (EC2):           ${ROOT_DIR}"
echo "Target (Container):     ${CONTAINER_EXPORT}"
echo "Dry Run:                ${DRY_RUN}"
echo ""

# Create container export directory if it doesn't exist
if [[ "$DRY_RUN" == "false" ]]; then
    mkdir -p "${CONTAINER_EXPORT}"
fi

# ---------- 1. Sync Main Pipeline Script ----------
echo ">>> [1/7] Syncing main pipeline script..."

if [[ ! -f "${ROOT_DIR}/run_flat_english_pipeline.sh" ]]; then
    echo "ERROR: Main pipeline script not found: ${ROOT_DIR}/run_flat_english_pipeline.sh"
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi

DRY_RUN_FLAG=""
if [[ "$DRY_RUN" == "true" ]]; then
    DRY_RUN_FLAG="--dry-run"
fi

"${PYTHON_CMD}" "${SCRIPT_DIR}/path_translator.py" \
    ec2-to-container \
    "${ROOT_DIR}/run_flat_english_pipeline.sh" \
    "${CONTAINER_EXPORT}/run_flat_english_pipeline.sh" \
    ${DRY_RUN_FLAG}

if [[ "$DRY_RUN" == "false" ]]; then
    chmod +x "${CONTAINER_EXPORT}/run_flat_english_pipeline.sh"
fi

# ---------- 2. Sync VSP-LLM Scripts ----------
echo ""
echo ">>> [2/7] Syncing VSP-LLM helper scripts..."

if [[ -d "${ROOT_DIR}/VSP-LLM/scripts" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "${CONTAINER_EXPORT}/VSP-LLM/scripts"
    fi

    # Translate shell scripts
    "${PYTHON_CMD}" "${SCRIPT_DIR}/path_translator.py" \
        ec2-to-container \
        "${ROOT_DIR}/VSP-LLM/scripts" \
        "${CONTAINER_EXPORT}/VSP-LLM/scripts" \
        --recursive \
        --patterns "*.sh" \
        ${DRY_RUN_FLAG}

    # Copy Python scripts (no path translation needed for most)
    if [[ "$DRY_RUN" == "false" ]]; then
        rsync -a --exclude='__pycache__' --exclude='*.pyc' \
            "${ROOT_DIR}/VSP-LLM/scripts/"*.py \
            "${CONTAINER_EXPORT}/VSP-LLM/scripts/" 2>/dev/null || true
    fi
else
    echo "WARNING: VSP-LLM/scripts not found, skipping"
fi

# ---------- 3. Sync auto_avsr Preparation Scripts ----------
echo ""
echo ">>> [3/7] Syncing auto_avsr preparation scripts..."

if [[ -d "${ROOT_DIR}/auto_avsr/preparation" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
            "${ROOT_DIR}/auto_avsr/preparation/" \
            "${CONTAINER_EXPORT}/auto_avsr/preparation/"
    else
        echo "  [DRY RUN] Would sync auto_avsr/preparation/"
    fi
else
    echo "WARNING: auto_avsr/preparation not found, skipping"
fi

# ---------- 4. Sync av_hubert Preparation Scripts ----------
echo ""
echo ">>> [4/7] Syncing av_hubert preparation scripts..."

if [[ -d "${ROOT_DIR}/av_hubert/avhubert/preparation" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        rsync -av --exclude='.git' \
            "${ROOT_DIR}/av_hubert/avhubert/preparation/" \
            "${CONTAINER_EXPORT}/av_hubert/avhubert/preparation/"
    else
        echo "  [DRY RUN] Would sync av_hubert/avhubert/preparation/"
    fi
else
    echo "WARNING: av_hubert/avhubert/preparation not found, skipping"
fi

# ---------- 5. Sync VSP UI ----------
echo ""
echo ">>> [5/7] Syncing VSP UI..."

if [[ -d "${ROOT_DIR}/vsp-ui" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        rsync -av \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.pytest_cache' \
            --exclude='*.log' \
            "${ROOT_DIR}/vsp-ui/" \
            "${CONTAINER_EXPORT}/vsp-ui/"
    else
        echo "  [DRY RUN] Would sync vsp-ui/"
    fi

    # Translate paths in server.py if it has hardcoded paths
    if [[ -f "${ROOT_DIR}/vsp-ui/app/server.py" ]]; then
        echo "  Translating paths in vsp-ui/app/server.py..."
        "${PYTHON_CMD}" "${SCRIPT_DIR}/path_translator.py" \
            ec2-to-container \
            "${ROOT_DIR}/vsp-ui/app/server.py" \
            "${CONTAINER_EXPORT}/vsp-ui/app/server.py" \
            ${DRY_RUN_FLAG}
    fi

    # Translate paths in pipeline_runner.py if it has hardcoded paths
    if [[ -f "${ROOT_DIR}/vsp-ui/app/services/pipeline_runner.py" ]]; then
        echo "  Translating paths in vsp-ui/app/services/pipeline_runner.py..."
        "${PYTHON_CMD}" "${SCRIPT_DIR}/path_translator.py" \
            ec2-to-container \
            "${ROOT_DIR}/vsp-ui/app/services/pipeline_runner.py" \
            "${CONTAINER_EXPORT}/vsp-ui/app/services/pipeline_runner.py" \
            ${DRY_RUN_FLAG}
    fi
else
    echo "WARNING: vsp-ui not found, skipping"
fi

# ---------- 6. Sync Documentation ----------
echo ""
echo ">>> [6/7] Syncing documentation..."

if [[ -f "${ROOT_DIR}/CLAUDE.md" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        cp -f "${ROOT_DIR}/CLAUDE.md" "${CONTAINER_EXPORT}/CLAUDE.md"

        # Update CLAUDE.md to reference /workspace paths in examples
        sed -i 's|/home/ubuntu|/workspace|g' "${CONTAINER_EXPORT}/CLAUDE.md"
    else
        echo "  [DRY RUN] Would copy and translate CLAUDE.md"
    fi
fi

if [[ -f "${ROOT_DIR}/README.md" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        cp -f "${ROOT_DIR}/README.md" "${CONTAINER_EXPORT}/README.md"
    else
        echo "  [DRY RUN] Would copy README.md"
    fi
fi

if [[ -d "${ROOT_DIR}/docs" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        rsync -av "${ROOT_DIR}/docs/" "${CONTAINER_EXPORT}/docs/"
    else
        echo "  [DRY RUN] Would sync docs/"
    fi
fi

# ---------- 7. Validation ----------
echo ""
echo ">>> [7/7] Running validation..."

if [[ -f "${SCRIPT_DIR}/validate_sync.sh" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
        bash "${SCRIPT_DIR}/validate_sync.sh" "${CONTAINER_EXPORT}"
    else
        echo "  [DRY RUN] Would run validation"
    fi
else
    echo "WARNING: validate_sync.sh not found, skipping validation"
fi

echo ""
echo "==================================================="
echo "Sync Complete!"
echo "==================================================="
echo ""

if [[ "$DRY_RUN" == "false" ]]; then
    echo "Next Steps:"
    echo "1. Review changes in ${CONTAINER_EXPORT}"
    echo "2. Test in container staging environment"
    echo "3. Build container image: cd vsp_docker && docker build -t vsp-pipeline:latest ."
    echo "4. Tag release: git tag -a container-v1.x.x -m 'Container release vX.X'"
else
    echo "This was a dry run. Re-run without --dry-run to apply changes."
fi
echo ""
