#!/bin/bash
# Apply make_report.py color coding fix for Linux Container Version
# This script should be run on the Linux container (not EC2)

set -e

PATCH_FILE="make_report_color_fix.patch"
TARGET_DIR="/workspace/VSP-LLM"
TARGET_FILE="$TARGET_DIR/scripts/make_report.py"

echo "=========================================="
echo "make_report.py Color Coding Fix"
echo "=========================================="
echo ""

# Check if we're on the Linux container
if [ ! -d "/workspace" ]; then
    echo "ERROR: /workspace directory not found"
    echo "This script must be run on the Linux container, not EC2"
    exit 1
fi

# Check if target file exists
if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found: $TARGET_FILE"
    exit 1
fi

# Check if patch file exists
if [ ! -f "$PATCH_FILE" ]; then
    echo "ERROR: Patch file not found: $PATCH_FILE"
    echo "Please copy make_report_color_fix.patch to the current directory"
    exit 1
fi

# Backup the original file
BACKUP_FILE="$TARGET_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "Creating backup: $BACKUP_FILE"
cp "$TARGET_FILE" "$BACKUP_FILE"

# Apply the patch
echo "Applying patch to $TARGET_FILE..."
cd "$TARGET_DIR"
patch -p1 < "$OLDPWD/$PATCH_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Patch applied successfully"
    echo ""
    echo "Changes:"
    echo "  - Green: Right word, right place"
    echo "  - Yellow: Word appears in reference but wrong place"
    echo "  - Red: Word doesn't appear in reference (made up)"
    echo ""
    echo "Backup saved to: $BACKUP_FILE"
else
    echo ""
    echo "❌ FAILED to apply patch"
    echo "Restoring backup..."
    cp "$BACKUP_FILE" "$TARGET_FILE"
    exit 1
fi
