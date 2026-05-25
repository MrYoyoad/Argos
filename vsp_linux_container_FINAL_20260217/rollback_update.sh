#!/usr/bin/env bash
# ============================================================================
# rollback_update.sh — Reverts the May-2026 refresh on the host.
# ============================================================================
#
# What it does:
#   1. Reads docker.conf.before-may2026 (snapshot taken by apply_update.sh).
#   2. Restores docker.conf to point at the OLD tag (e.g. vsp-llm-pipeline:latest).
#   3. Optionally removes the may-2026-update tag (image stays on disk by default
#      — pass --purge to also delete the image).
#
# The new tag stays on disk by default so a re-roll-forward is one config edit.
#
# Usage:
#   bash rollback_update.sh           # restore docker.conf, keep new image
#   bash rollback_update.sh --purge   # restore docker.conf AND docker rmi new tag
# ============================================================================

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
die()  { echo -e "${RED}ERROR:${NC} $*" >&2; exit 1; }
ok()   { echo -e "${GREEN}✅${NC} $*"; }
info() { echo -e "${BLUE}» ${NC}$*"; }
warn() { echo -e "${YELLOW}⚠️ ${NC} $*"; }

PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1

OVERLAY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# -------- find galaxy_export --------
GALAXY_EXPORT_DIR="${GALAXY_EXPORT_DIR:-$HOME/Desktop/galaxy_export}"
if [ ! -d "$GALAXY_EXPORT_DIR" ]; then
    for cand in "$HOME/galaxy_export" "/home/ds/Desktop/galaxy_export" "/home/ds/galaxy_export"; do
        if [ -d "$cand" ]; then GALAXY_EXPORT_DIR="$cand"; break; fi
    done
fi
[ -d "$GALAXY_EXPORT_DIR" ] || die "galaxy_export not found. Set GALAXY_EXPORT_DIR=…"

CONF="$GALAXY_EXPORT_DIR/docker.conf"
BACKUP="$CONF.before-may2026"

[ -f "$BACKUP" ] || die "No backup found at $BACKUP. Did apply_update.sh run successfully?"

# -------- recover OLD/NEW tags from current docker.conf comments --------
NEW_TAG="$(grep -E '^[[:space:]]*DOCKER_IMAGE[[:space:]]*=' "$CONF" 2>/dev/null \
            | tail -1 | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//' || true)"
OLD_TAG="$(grep -E '^#[[:space:]]*DOCKER_IMAGE[[:space:]]*=' "$CONF" 2>/dev/null \
            | tail -1 | sed -E 's/^#[[:space:]]*DOCKER_IMAGE[[:space:]]*=[[:space:]]*//; s/[[:space:]]*$//' || true)"
[ -z "$OLD_TAG" ] && OLD_TAG="$(grep -E '^[[:space:]]*DOCKER_IMAGE[[:space:]]*=' "$BACKUP" 2>/dev/null \
            | tail -1 | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//' || true)"
[ -z "$OLD_TAG" ] && OLD_TAG="vsp-llm-pipeline:latest"

info "Current (new) tag : $NEW_TAG"
info "Rolling back to   : $OLD_TAG"

# -------- restore docker.conf from backup --------
cp "$BACKUP" "$CONF"
chmod 666 "$CONF" 2>/dev/null || true
ok "Restored docker.conf from $BACKUP"

# -------- optional: purge the new image --------
if [ "$PURGE" = "1" ] && [ -n "$NEW_TAG" ]; then
    if docker image inspect "$NEW_TAG" >/dev/null 2>&1; then
        info "Removing image '$NEW_TAG'…"
        docker image rm -f "$NEW_TAG" >/dev/null
        ok "Image removed"
    else
        warn "Image '$NEW_TAG' not found locally — nothing to purge"
    fi
else
    [ -n "$NEW_TAG" ] && info "Image '$NEW_TAG' kept on disk (pass --purge to remove)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ Rollback complete${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  docker.conf now points at: $OLD_TAG"
echo "  Re-run apply_update.sh to roll forward again."
echo ""
