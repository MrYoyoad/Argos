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

# Make launcher executable
chmod +x "$LAUNCHER"

# Generate .desktop file with correct paths
DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=VSP Pipeline
Comment=Visual Speech Processing Pipeline - Start UI
Exec=${LAUNCHER}
Icon=${ICON_FILE}
Terminal=true
Categories=AudioVideo;Video;
StartupNotify=true"

# Install to applications menu
mkdir -p ~/.local/share/applications
echo "$DESKTOP_CONTENT" > ~/.local/share/applications/vsp-pipeline.desktop
echo "Installed to applications menu."

# Install to Desktop if it exists
if [ -d "${HOME}/Desktop" ]; then
    echo "$DESKTOP_CONTENT" > "${HOME}/Desktop/vsp-pipeline.desktop"
    chmod +x "${HOME}/Desktop/vsp-pipeline.desktop"
    # Mark as trusted on GNOME
    gio set "${HOME}/Desktop/vsp-pipeline.desktop" metadata::trusted true 2>/dev/null || true
    echo "Installed to Desktop."
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
