#!/usr/bin/env bash
# ============================================================================
# apply_update.sh — Host-side wrapper that PERSISTS the May-2026 refresh.
# ============================================================================
#
# Why a wrapper exists:
#   INSTALL.sh runs *inside* the docker container and does two things that
#   would otherwise be lost when the container exits:
#     1. pip-installs the IS / confidence wheels into vsp-llm-yoad-venv
#     2. patches fairseq's GenerationConfig source (max_len, repetition_penalty)
#   Both live INSIDE the container's filesystem. `docker run --rm` discards them.
#
#   This wrapper runs INSTALL.sh inside a NAMED, non-removed container, then
#   `docker commit`s the resulting filesystem to a new image tag. Subsequent
#   `docker run --rm` calls use the new tag — wheels + patch persist.
#
# Inputs (auto-detected, override via env):
#   GALAXY_EXPORT_DIR   default: ~/Desktop/galaxy_export
#   OLD_TAG             default: read from $GALAXY_EXPORT_DIR/docker.conf
#                        (or vsp-llm-pipeline:latest if not set)
#   NEW_TAG             default: vsp-llm-pipeline:may2026-update
#   TMP_NAME            default: vsp-install-tmp
#
# Exit codes:
#   0   success — new tag committed, docker.conf updated
#   1   prerequisite failure (no docker, no galaxy_export, no source image)
#   2   INSTALL.sh failed inside the container — no commit performed
#   3   docker commit failed
# ============================================================================

set -euo pipefail

# -------- colors --------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
die()  { echo -e "${RED}ERROR:${NC} $*" >&2; exit "${2:-1}"; }
info() { echo -e "${BLUE}» ${NC}$*"; }
ok()   { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️ ${NC} $*"; }

# -------- where am I --------
OVERLAY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
info "Overlay dir : $OVERLAY_DIR"

# -------- find galaxy_export --------
GALAXY_EXPORT_DIR="${GALAXY_EXPORT_DIR:-$HOME/Desktop/galaxy_export}"
if [ ! -d "$GALAXY_EXPORT_DIR" ]; then
    # Try a few common locations before giving up
    for cand in \
        "$HOME/galaxy_export" \
        "/home/ds/Desktop/galaxy_export" \
        "/home/ds/galaxy_export" \
        "$(pwd)/galaxy_export"; do
        if [ -d "$cand" ]; then GALAXY_EXPORT_DIR="$cand"; break; fi
    done
fi
[ -d "$GALAXY_EXPORT_DIR" ] || die "galaxy_export directory not found. Set GALAXY_EXPORT_DIR=…"
[ -f "$GALAXY_EXPORT_DIR/run_flat_english_pipeline.sh" ] || \
    die "$GALAXY_EXPORT_DIR doesn't look like a galaxy_export (missing run_flat_english_pipeline.sh)"
info "galaxy_export: $GALAXY_EXPORT_DIR"

# -------- docker present? --------
command -v docker >/dev/null || die "docker not installed"
docker info >/dev/null 2>&1 || die "docker daemon not reachable (try: sudo systemctl start docker)"

# -------- pick OLD_TAG (the BASE image we'll layer on top of) --------
# IMPORTANT: OLD_TAG is the ORIGINAL Docker image (the un-patched base), not
# the currently-active production tag. On a fresh install both happen to be
# the same. After the first successful apply_update.sh, docker.conf points at
# the new tag — but the next apply_update.sh run must STILL layer on top of
# the original base, not on top of itself.
#
# Earlier draft read docker.conf to discover OLD_TAG; that caused
# "Unable to find image 'vsp-llm-pipeline:may2026-update' locally" on the
# second invocation because OLD_TAG=NEW_TAG and the cleanup step deleted the
# source before docker run could use it. Fix: default to vsp-llm-pipeline:latest,
# accept an explicit OLD_TAG= override, but NEVER infer from docker.conf.
OLD_TAG="${OLD_TAG:-vsp-llm-pipeline:latest}"
[ "$OLD_TAG" = "CHANGE_ME" ] && die "OLD_TAG resolved to CHANGE_ME. Pass OLD_TAG=<your-base-image>."

docker image inspect "$OLD_TAG" >/dev/null 2>&1 \
    || die "Source image '$OLD_TAG' not found locally. Check: docker images"
info "source image: $OLD_TAG"

# -------- pick NEW_TAG --------
NEW_TAG="${NEW_TAG:-vsp-llm-pipeline:may2026-update}"
info "new tag    : $NEW_TAG"

# -------- safety: refuse if OLD_TAG and NEW_TAG resolve to the same thing --------
# Same name OR same image-id would cause the cleanup step to delete the source.
if [ "$OLD_TAG" = "$NEW_TAG" ]; then
    die "OLD_TAG and NEW_TAG are identical ('$OLD_TAG'). The script would delete its own source. Pass OLD_TAG=<a-different-base> or set NEW_TAG=<a-different-target>."
fi
OLD_ID="$(docker image inspect --format '{{.Id}}' "$OLD_TAG" 2>/dev/null || true)"
NEW_ID="$(docker image inspect --format '{{.Id}}' "$NEW_TAG" 2>/dev/null || true)"
if [ -n "$OLD_ID" ] && [ "$OLD_ID" = "$NEW_ID" ]; then
    die "OLD_TAG and NEW_TAG point at the same image id ($OLD_ID). Refusing to delete the source."
fi

# -------- pick temp container name --------
TMP_NAME="${TMP_NAME:-vsp-install-tmp}"

# -------- guard: don't clobber an existing image silently --------
if docker image inspect "$NEW_TAG" >/dev/null 2>&1; then
    warn "Image '$NEW_TAG' already exists. It will be replaced."
    docker image rm -f "$NEW_TAG" >/dev/null 2>&1 || true
fi

# -------- clean any leftover temp container --------
if docker ps -a --format '{{.Names}}' | grep -qx "$TMP_NAME"; then
    info "Removing stale container '$TMP_NAME'…"
    docker rm -f "$TMP_NAME" >/dev/null
fi

# ----------------------------------------------------------------------------
# Stage 1 — run INSTALL.sh inside a named, non-removed container.
#           If it succeeds, the venv + fairseq patch are live inside that
#           container's filesystem, ready to be committed.
# ----------------------------------------------------------------------------
echo ""
info "Stage 1/3: running INSTALL.sh inside container '$TMP_NAME'…"
echo "─────────────────────────────────────────────────────────"

# Note: NOT --rm (we need the container's diff for commit).
# Note: -it for live progress; falls back fine to non-interactive in scripts.
# Note: image's ENTRYPOINT is already bash -c, so pass JUST the command string.
# Do NOT prepend an extra `bash` — that would make the container run
# `bash bash -c '…'`, which tries to execute the bash binary as a script and
# fails with "/usr/bin/bash: cannot execute binary file".
if ! docker run --name "$TMP_NAME" -it \
        --gpus all \
        -v "$GALAXY_EXPORT_DIR:/host/galaxy_export" \
        -v "$OVERLAY_DIR:/overlay" \
        "$OLD_TAG" \
        -c 'cd /host/galaxy_export && bash /overlay/INSTALL.sh'; then
    echo "─────────────────────────────────────────────────────────"
    docker rm -f "$TMP_NAME" >/dev/null 2>&1 || true
    die "INSTALL.sh failed inside the container. NO commit performed. galaxy_export still updated on the host (those changes ARE persistent)." 2
fi
echo "─────────────────────────────────────────────────────────"
ok "INSTALL.sh completed inside '$TMP_NAME'"

# ----------------------------------------------------------------------------
# Stage 2 — docker commit to NEW_TAG.
# ----------------------------------------------------------------------------
echo ""
info "Stage 2/3: docker commit '$TMP_NAME' → '$NEW_TAG'"
COMMIT_MSG="VSP May-2026 refresh: IS + confidence + n-best + agreement deps + fairseq patch"
if ! docker commit \
        --change "LABEL vsp.update=may2026" \
        --change "LABEL vsp.source-image=$OLD_TAG" \
        --message "$COMMIT_MSG" \
        "$TMP_NAME" "$NEW_TAG" >/dev/null; then
    docker rm -f "$TMP_NAME" >/dev/null 2>&1 || true
    die "docker commit failed" 3
fi
ok "Committed: $NEW_TAG"

# Cleanup: install container has done its job
docker rm -f "$TMP_NAME" >/dev/null
ok "Removed temp container '$TMP_NAME' (image '$NEW_TAG' preserved)"

# ----------------------------------------------------------------------------
# Stage 3 — point docker.conf at the new tag (with a backup for rollback).
# ----------------------------------------------------------------------------
echo ""
info "Stage 3/3: updating docker.conf"
CONF="$GALAXY_EXPORT_DIR/docker.conf"
BACKUP="$CONF.before-may2026"
if [ -f "$CONF" ]; then
    # Only create the backup the FIRST time. On subsequent re-runs, do NOT
    # overwrite the original-base pointer with the in-between active tag —
    # otherwise rollback loses the route back to vsp-llm-pipeline:latest.
    if [ ! -f "$BACKUP" ]; then
        cp "$CONF" "$BACKUP"
        info "  Backup saved (first run): $BACKUP"
    else
        info "  Backup already exists from earlier run: $BACKUP (preserved)"
    fi
fi

# Write a fresh, clean docker.conf
cat > "$CONF" <<EOF
# Docker image for VSP Pipeline
# Edited by apply_update.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
#
# Current production tag (after May-2026 refresh):
DOCKER_IMAGE=$NEW_TAG
#
# Previous tag (rollback target):
#   DOCKER_IMAGE=$OLD_TAG
# To roll back: edit this file to point at the previous tag, or run
#   bash rollback_update.sh
EOF
chmod 666 "$CONF" 2>/dev/null || true
ok "docker.conf now points at $NEW_TAG"

# ----------------------------------------------------------------------------
# Quick smoke-test: confirm the new image actually has the wheels.
# ----------------------------------------------------------------------------
echo ""
info "Smoke-test: importing IS deps from the committed image…"
if docker run --rm --gpus all "$NEW_TAG" -c '
    source /workspace/vsp-llm-yoad-venv/bin/activate 2>/dev/null && \
    python3 -c "
import importlib, sys
ok, fail = [], []
for m in (\"sentence_transformers\", \"metaphone\", \"matplotlib\", \"scipy\", \"editdistance\"):
    try: importlib.import_module(m); ok.append(m)
    except Exception as e: fail.append(f\"{m}: {e}\")
print(\"OK :\", \", \".join(ok))
if fail:
    print(\"FAIL:\")
    for f in fail: print(\" -\", f)
    sys.exit(1)
"
' 2>&1 | sed 's/^/    /'; then
    ok "Smoke-test passed — wheels are baked into '$NEW_TAG'"
else
    warn "Smoke-test FAILED. The committed image is missing some IS deps."
    warn "  Investigate: docker run --rm -it $NEW_TAG bash"
    warn "  Roll back  : bash $OVERLAY_DIR/rollback_update.sh"
    exit 3
fi

# ----------------------------------------------------------------------------
# Final summary.
# ----------------------------------------------------------------------------
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ Update applied and persisted${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Source image  : $OLD_TAG"
echo "  New image     : $NEW_TAG"
echo "  galaxy_export : $GALAXY_EXPORT_DIR"
echo "  Active config : DOCKER_IMAGE=$NEW_TAG  (in docker.conf)"
echo ""
echo "  Next steps:"
echo "    1. From the host:  bash $GALAXY_EXPORT_DIR/install-desktop-icon.sh"
echo "    2. Double-click 'VSP Pipeline' on the Desktop."
echo ""
echo "  Rollback (one command):"
echo "    bash $OVERLAY_DIR/rollback_update.sh"
echo ""
