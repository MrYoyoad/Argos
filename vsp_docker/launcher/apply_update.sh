#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — apply a code-only update
# ==================================================
# Usage:  ./apply_update.sh <new-image-tarball.tar.zst> <new-image-tag>
# Example: ./apply_update.sh vsp-image-build-002.tar.zst vsp-llm-pipeline:client-build-002
#
# Semantics:
#  1. Verify the tarball (zstd integrity + sha256 if present).
#  2. docker load.
#  3. Smoke-test the new image (lib/test_all_modules.sh).
#  4. Atomic tag swap: write image.tag.tmp, then mv to image.tag.
#  5. Keep image.tag.previous so rollback.sh can flip back.
#  6. Do NOT docker rmi the previous image automatically.
#
# If any step fails, image.tag is left pointing at the OLD tag and the
# launcher keeps working on the previous build.
# ==================================================

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <image-tarball> <new-image-tag>"
  echo "Example: $0 vsp-image-build-002.tar.zst vsp-llm-pipeline:client-build-002"
  exit 1
fi

TARBALL="$1"
NEW_TAG="$2"

# --- Where image.tag lives (well-known location, see install_launcher.sh) ---
TAG_FILE="/opt/vsp/launcher/image.tag"
if [ ! -f "$TAG_FILE" ]; then
  echo "ERROR: $TAG_FILE not found. Run install_launcher.sh first."
  exit 1
fi
PREV_TAG="$(tr -d '[:space:]' < "$TAG_FILE")"

if [ ! -f "$TARBALL" ]; then
  echo "ERROR: tarball not found: $TARBALL"
  exit 1
fi
if [[ ! "$NEW_TAG" =~ ^[a-zA-Z0-9._/:-]+$ ]]; then
  echo "ERROR: invalid image tag: $NEW_TAG"
  exit 1
fi

echo "=========================================="
echo "VSP Pipeline — apply update"
echo "  current tag: $PREV_TAG"
echo "  new tag:     $NEW_TAG"
echo "  tarball:     $TARBALL"
echo "=========================================="

# --- Step 1: integrity ---
echo "[1/5] Verifying tarball integrity..."
if [[ "$TARBALL" == *.zst ]]; then
  zstd -t "$TARBALL" || { echo "ERROR: zstd integrity check failed"; exit 2; }
fi
if [ -f "${TARBALL}.sha256" ]; then
  (cd "$(dirname "$TARBALL")" && sha256sum -c "$(basename "$TARBALL").sha256") \
    || { echo "ERROR: SHA256 mismatch"; exit 2; }
fi
echo "  OK"

# --- Step 2: load ---
echo "[2/5] Loading image..."
if [[ "$TARBALL" == *.zst ]]; then
  zstd -d -c "$TARBALL" | docker load
else
  docker load -i "$TARBALL"
fi

# --- Step 3: smoke test the new image ---
echo "[3/5] Smoke-testing new image (lib/test_all_modules.sh)..."
if ! docker run --rm "$NEW_TAG" bash /workspace/lib/test_all_modules.sh; then
  echo "ERROR: smoke test failed on new image. Old build still active. Aborting."
  echo "Tag in image.tag is still: $PREV_TAG"
  exit 3
fi
echo "  OK"

# --- Step 4: atomic tag swap ---
echo "[4/5] Swapping image.tag..."
echo "$PREV_TAG" > "${TAG_FILE}.previous"
echo "$NEW_TAG"  > "${TAG_FILE}.tmp"
mv "${TAG_FILE}.tmp" "$TAG_FILE"
echo "  image.tag now: $(cat "$TAG_FILE")"
echo "  previous saved at: ${TAG_FILE}.previous"

# --- Step 5: leave previous image on disk for fast rollback ---
echo "[5/5] Keeping previous image $PREV_TAG on disk for rollback (use rollback.sh to flip back)."
echo
echo "Update complete. Next pipeline launch uses $NEW_TAG."
echo "If anything misbehaves, run: ./rollback.sh"
