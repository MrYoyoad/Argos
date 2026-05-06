#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — install launcher + desktop shortcut (Linux)
# ==================================================
# Place this kit's launcher under /opt/vsp/launcher/ and create a desktop
# shortcut pointing at it. Idempotent — safe to re-run.
#
# Usage: sudo ./install_launcher.sh
#        (or: sudo ./install_launcher.sh /custom/install/prefix)
# ==================================================

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${1:-/opt/vsp/launcher}"

if [ "$(id -u)" -ne 0 ] && [[ "$PREFIX" == /opt/* ]]; then
  echo "Installing to $PREFIX requires root. Re-run with sudo."
  exit 1
fi

echo "Installing VSP launcher into $PREFIX..."
mkdir -p "$PREFIX"

# --- Copy launcher artifacts ---
cp "${KIT_DIR}/vsp-pipeline.sh" "${PREFIX}/vsp-pipeline.sh"
cp "${KIT_DIR}/image.tag"       "${PREFIX}/image.tag"
cp "${KIT_DIR}/apply_update.sh" "${PREFIX}/apply_update.sh" 2>/dev/null || true
cp "${KIT_DIR}/rollback.sh"     "${PREFIX}/rollback.sh"     2>/dev/null || true
chmod +x "${PREFIX}"/*.sh
[ -f "${PREFIX}/image.tag" ] && chmod 644 "${PREFIX}/image.tag"

# --- Icon (optional — shipped if present) ---
if [ -f "${KIT_DIR}/vsp-icon.png" ]; then
  cp "${KIT_DIR}/vsp-icon.png" "${PREFIX}/vsp-icon.png"
fi

# --- Desktop shortcut for the *invoking* user (or for whoever's home is in $HOME) ---
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
if [ -z "$TARGET_HOME" ] || [ ! -d "$TARGET_HOME" ]; then
  echo "Could not resolve home directory for $TARGET_USER; skipping desktop shortcut."
else
  DESKTOP_DIR="${TARGET_HOME}/Desktop"
  mkdir -p "$DESKTOP_DIR"
  cp "${KIT_DIR}/VSP-Pipeline.desktop" "${DESKTOP_DIR}/VSP-Pipeline.desktop"
  chmod +x "${DESKTOP_DIR}/VSP-Pipeline.desktop"
  chown "${TARGET_USER}:" "${DESKTOP_DIR}/VSP-Pipeline.desktop" 2>/dev/null || true

  # GNOME / Cinnamon: mark as trusted so it shows the proper icon, not "Untrusted launcher"
  if command -v gio >/dev/null 2>&1; then
    sudo -u "$TARGET_USER" gio set "${DESKTOP_DIR}/VSP-Pipeline.desktop" metadata::trusted true 2>/dev/null || true
  fi

  # Plain shell-script fallback for DEs that don't honor .desktop files
  ln -sf "${PREFIX}/vsp-pipeline.sh" "${DESKTOP_DIR}/VSP Pipeline.sh"
  echo "Desktop shortcut placed at: ${DESKTOP_DIR}/VSP-Pipeline.desktop"
fi

# --- Refresh the desktop database (KDE) ---
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q 2>/dev/null || true
fi

echo
echo "Done. The desktop shortcut is ready."
echo "Image tag: $(cat ${PREFIX}/image.tag)"
echo
echo "Next: run ../checks/post_install_check.sh to verify."
