#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — rollback to the previous image build
# ==================================================
# Reverses the last apply_update.sh: flips image.tag back to whatever
# was stored in image.tag.previous. The previous image must still be
# loaded in Docker (apply_update.sh keeps it on disk).
#
# Usage: ./rollback.sh
# ==================================================

set -euo pipefail

TAG_FILE="/opt/vsp/launcher/image.tag"
PREV_FILE="${TAG_FILE}.previous"

if [ ! -f "$TAG_FILE" ]; then
  echo "ERROR: $TAG_FILE not found."
  exit 1
fi
if [ ! -f "$PREV_FILE" ]; then
  echo "ERROR: no previous tag recorded at $PREV_FILE."
  echo "Either nothing has been updated, or the file was deleted."
  exit 1
fi

CUR_TAG="$(tr -d '[:space:]' < "$TAG_FILE")"
PREV_TAG="$(tr -d '[:space:]' < "$PREV_FILE")"

echo "=========================================="
echo "VSP Pipeline — rollback"
echo "  current tag:     $CUR_TAG"
echo "  rolling back to: $PREV_TAG"
echo "=========================================="

if ! docker image inspect "$PREV_TAG" >/dev/null 2>&1; then
  echo "ERROR: previous image $PREV_TAG is not loaded in Docker."
  echo "It may have been removed by 'docker rmi'. You'll need to re-load it from a kit tarball."
  exit 2
fi

# Atomic flip
echo "$CUR_TAG" > "${TAG_FILE}.previous"
echo "$PREV_TAG" > "${TAG_FILE}.tmp"
mv "${TAG_FILE}.tmp" "$TAG_FILE"

echo "Rolled back. image.tag is now: $(cat "$TAG_FILE")"
echo "(The previously-current tag $CUR_TAG is recorded as previous; you can re-apply with apply_update if needed.)"
