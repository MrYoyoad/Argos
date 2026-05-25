#!/bin/bash
#
# Install VSP Pipeline UI desktop shortcut
#

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="${APP_DIR}/vsp-pipeline.desktop"

echo "Installing VSP Pipeline UI..."

# Copy to applications directory
mkdir -p ~/.local/share/applications
cp "${DESKTOP_FILE}" ~/.local/share/applications/

# Copy to Desktop if it exists
if [[ -d "${HOME}/Desktop" ]]; then
    cp "${DESKTOP_FILE}" "${HOME}/Desktop/"
    # Mark as trusted on GNOME
    chmod +x "${HOME}/Desktop/vsp-pipeline.desktop"
    # Try to mark as trusted (GNOME)
    gio set "${HOME}/Desktop/vsp-pipeline.desktop" metadata::trusted true 2>/dev/null || true
    echo "Desktop shortcut created at: ${HOME}/Desktop/vsp-pipeline.desktop"
fi

# Create input folder
mkdir -p "${HOME}/vsp_input"

# Configure VLC to not show video title overlay (obscures burned subtitles)
mkdir -p "${HOME}/.config/vlc"
if [ -f "${HOME}/.config/vlc/vlcrc" ]; then
    sed -i 's/^#\?video-title-show=.*/video-title-show=0/' "${HOME}/.config/vlc/vlcrc"
    grep -q '^video-title-show=' "${HOME}/.config/vlc/vlcrc" || echo 'video-title-show=0' >> "${HOME}/.config/vlc/vlcrc"
else
    echo 'video-title-show=0' > "${HOME}/.config/vlc/vlcrc"
fi
echo "VLC configured to hide title overlay on video playback"

echo ""
echo "Installation complete!"
echo ""
echo "You can now:"
echo "  1. Double-click 'VSP Pipeline' icon on your desktop"
echo "  2. Or run: ${APP_DIR}/launcher.sh"
echo ""
echo "The input folder is: ${HOME}/vsp_input"
