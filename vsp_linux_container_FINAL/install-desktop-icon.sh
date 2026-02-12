#!/bin/bash
#
# Install VSP Pipeline desktop icon
#
# Run this ON THE HOST (not inside the Docker container).
# It creates a desktop shortcut that launches the Docker container,
# starts the UI server, and opens the browser.
#
# Usage:
#   cd /path/to/galaxy_export
#   bash install-desktop-icon.sh
#

set -euo pipefail

# Auto-detect install directory from script location
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_TEMPLATE="${INSTALL_DIR}/vsp-pipeline.desktop"
ICON_FILE="${INSTALL_DIR}/vsp-ui/logo.png"
LAUNCHER="${INSTALL_DIR}/vsp-start.sh"

echo "========================================="
echo "  VSP Pipeline - Desktop Icon Installer"
echo "========================================="
echo ""

# Verify required files exist
if [ ! -f "$LAUNCHER" ]; then
    echo "ERROR: vsp-start.sh not found at: $LAUNCHER"
    echo "Make sure you're running this from the galaxy_export directory."
    exit 1
fi

if [ ! -f "$ICON_FILE" ]; then
    echo "WARNING: logo.png not found at: $ICON_FILE"
    echo "Desktop icon will use a generic system icon."
    ICON_FILE="video-display"
fi

# Make launcher executable (may fail on mounted filesystems - that's OK)
chmod +x "$LAUNCHER" 2>/dev/null || true

# Generate .desktop file with correct paths
# Use "bash <path>" instead of just "<path>" so execute permission isn't needed
DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=VSP Pipeline
Comment=Visual Speech Processing Pipeline - Start UI
Exec=bash ${LAUNCHER}
Icon=${ICON_FILE}
Terminal=true
Categories=AudioVideo;Video;
StartupNotify=true"

# Find the real home directory (don't trust $HOME - it may be wrong)
REAL_HOME="$(getent passwd "$(whoami)" 2>/dev/null | cut -d: -f6)"
if [ -z "$REAL_HOME" ]; then
    REAL_HOME="$HOME"
fi

# Find Desktop directory - try multiple locations
DESKTOP_DIR=""
for candidate in \
    "${REAL_HOME}/Desktop" \
    "${HOME}/Desktop" \
    "/home/$(whoami)/Desktop" \
    "/home/ds/Desktop"; do
    if [ -d "$candidate" ]; then
        DESKTOP_DIR="$candidate"
        break
    fi
done

# Install to applications menu
mkdir -p "${REAL_HOME}/.local/share/applications" 2>/dev/null || mkdir -p ~/.local/share/applications
APP_DIR="${REAL_HOME}/.local/share/applications"
[ -d "$APP_DIR" ] || APP_DIR=~/.local/share/applications
echo "$DESKTOP_CONTENT" > "${APP_DIR}/vsp-pipeline.desktop"
echo "Installed to applications menu."

# Install to Desktop
if [ -n "$DESKTOP_DIR" ]; then
    echo "$DESKTOP_CONTENT" > "${DESKTOP_DIR}/vsp-pipeline.desktop"
    chmod +x "${DESKTOP_DIR}/vsp-pipeline.desktop" 2>/dev/null || true
    # Mark as trusted on GNOME
    gio set "${DESKTOP_DIR}/vsp-pipeline.desktop" metadata::trusted true 2>/dev/null || true
    echo "Installed to Desktop: ${DESKTOP_DIR}/vsp-pipeline.desktop"
else
    echo "WARNING: Could not find Desktop directory."
    echo "Tried: ${REAL_HOME}/Desktop, ${HOME}/Desktop, /home/$(whoami)/Desktop, /home/ds/Desktop"
    echo ""
    echo "To install manually, copy this to your Desktop:"
    echo "  echo '$DESKTOP_CONTENT' > /path/to/Desktop/vsp-pipeline.desktop"
fi

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "  Exec:  $LAUNCHER"
echo "  Icon:  $ICON_FILE"
echo ""
echo "You can now double-click 'VSP Pipeline' on your desktop"
echo "or find it in your applications menu."
echo ""
