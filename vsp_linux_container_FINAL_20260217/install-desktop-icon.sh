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

# Make launcher executable
chmod +x "$LAUNCHER" 2>/dev/null || true

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

if [ -z "$DESKTOP_DIR" ]; then
    echo "ERROR: Could not find Desktop directory."
    echo "Tried: ${REAL_HOME}/Desktop, ${HOME}/Desktop, /home/$(whoami)/Desktop, /home/ds/Desktop"
    exit 1
fi

# Icon reference
ICON_REF="${ICON_FILE}"
if [ ! -f "$ICON_FILE" ]; then
    ICON_REF="video-display"
fi

# The .desktop file uses /usr/bin/bash to invoke the script, because:
# 1. The script may be on a mounted filesystem where chmod +x doesn't work
# 2. Terminal=false means the DE does NOT wrap in an extra shell (no double-bash)
# 3. vsp-start.sh detects "no terminal" and self-relaunches in gnome-terminal
DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=VSP Pipeline
Comment=Visual Speech Processing Pipeline - Start UI
Exec=/usr/bin/bash ${LAUNCHER}
Icon=${ICON_REF}
Terminal=false
Categories=AudioVideo;Video;
StartupNotify=false"

# Install to applications menu (works reliably)
mkdir -p "${REAL_HOME}/.local/share/applications" 2>/dev/null || mkdir -p ~/.local/share/applications
APP_DIR="${REAL_HOME}/.local/share/applications"
[ -d "$APP_DIR" ] || APP_DIR=~/.local/share/applications
echo "$DESKTOP_CONTENT" > "${APP_DIR}/vsp-pipeline.desktop"
chmod +x "${APP_DIR}/vsp-pipeline.desktop" 2>/dev/null || true
echo "  Installed to applications menu"

# Install to Desktop
echo "$DESKTOP_CONTENT" > "${DESKTOP_DIR}/vsp-pipeline.desktop"
chmod +x "${DESKTOP_DIR}/vsp-pipeline.desktop" 2>/dev/null || true
gio set "${DESKTOP_DIR}/vsp-pipeline.desktop" metadata::trusted true 2>/dev/null || true
echo "  Installed to Desktop: ${DESKTOP_DIR}/vsp-pipeline.desktop"

# Verify the key pieces
echo ""
echo "  Verifying..."
PROBLEMS=0
if [ -x "$LAUNCHER" ]; then
    echo "    vsp-start.sh:  executable OK"
else
    echo "    vsp-start.sh:  WARNING - not executable"
    PROBLEMS=1
fi
if [ -f "${DESKTOP_DIR}/vsp-pipeline.desktop" ]; then
    echo "    .desktop file: created OK"
else
    echo "    .desktop file: WARNING - not created"
    PROBLEMS=1
fi
# Check terminal emulator exists (script needs it for self-relaunch)
TERM_FOUND=""
for _t in x-terminal-emulator gnome-terminal kgx gnome-console xfce4-terminal mate-terminal konsole lxterminal tilix terminator kitty alacritty xterm; do
    if command -v "$_t" &>/dev/null; then
        TERM_FOUND="$_t"
        break
    fi
done
if [ -n "$TERM_FOUND" ]; then
    echo "    Terminal:      $TERM_FOUND ($(command -v "$TERM_FOUND"))"
else
    echo "    Terminal:      WARNING - none found!"
    PROBLEMS=1
fi

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
if [ $PROBLEMS -eq 0 ]; then
    echo "  Double-click 'VSP Pipeline' on your Desktop to launch."
    echo ""
    echo "  If the Desktop icon doesn't work:"
    echo "    1. Right-click it → 'Allow Launching'"
    echo "    2. Or search 'VSP Pipeline' in the applications menu"
    echo "    3. Or run:  ${LAUNCHER}"
else
    echo "  Some checks had warnings (see above)."
    echo "  You can always run from terminal:  ${LAUNCHER}"
fi
echo ""
