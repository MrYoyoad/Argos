#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — Diagnostics bundle
# ==================================================
# Air-gapped equivalent of "phone home". Bundles host info + logs into a
# single tarball the operator can copy to USB and send back.
#
# Usage: ./collect_diagnostics.sh
# Output: vsp-diagnostics-<hostname>-<timestamp>.tar.gz in the current dir.
# ==================================================

set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS=$(date -u +%Y%m%d_%H%M%SZ)
HOSTNAME_SHORT=$(hostname -s 2>/dev/null || hostname)
BUNDLE="vsp-diagnostics-${HOSTNAME_SHORT}-${TS}"
WORK_DIR="$(mktemp -d /tmp/${BUNDLE}.XXXXXX)"
TARGET="${WORK_DIR}/${BUNDLE}"
mkdir -p "$TARGET"

echo "Collecting VSP diagnostics into ${BUNDLE}.tar.gz..."

# --- Host info ---
{
  echo "=== uname ==="
  uname -a
  echo
  echo "=== /etc/os-release ==="
  cat /etc/os-release 2>/dev/null
  echo
  echo "=== Date ==="
  date -u +%Y-%m-%dT%H:%M:%SZ
} > "${TARGET}/host_info.txt" 2>&1

# --- GPU + driver ---
{
  echo "=== nvidia-smi ==="
  nvidia-smi 2>&1 || echo "(nvidia-smi not available)"
  echo
  echo "=== nvidia-smi -q (full) ==="
  nvidia-smi -q 2>&1 || echo "(nvidia-smi -q failed)"
} > "${TARGET}/nvidia.txt" 2>&1

# --- Disk + memory ---
{
  echo "=== df -h ==="
  df -h
  echo
  echo "=== free -h ==="
  free -h
  echo
  echo "=== /proc/meminfo (head) ==="
  head -20 /proc/meminfo
} > "${TARGET}/sys.txt" 2>&1

# --- Docker info ---
{
  echo "=== docker version ==="
  docker version 2>&1 || echo "(docker not available)"
  echo
  echo "=== docker info ==="
  docker info 2>&1 || true
  echo
  echo "=== docker images ==="
  docker images 2>&1 || true
  echo
  echo "=== docker ps -a ==="
  docker ps -a 2>&1 || true
} > "${TARGET}/docker.txt" 2>&1

# --- Last 500 lines of dmesg (driver / OOM clues) ---
dmesg 2>/dev/null | tail -n 500 > "${TARGET}/dmesg.tail" || \
  echo "(dmesg unavailable; rerun with sudo for kernel ring buffer)" > "${TARGET}/dmesg.tail"

# --- Pre-install + post-install logs and reports ---
for f in pre_install_check.log post_install_check.log INSTALL_REPORT.txt; do
  if [ -f "${KIT_DIR}/${f}" ]; then
    cp "${KIT_DIR}/${f}" "${TARGET}/"
  fi
done

# --- Image tag config (Linux launcher location) ---
for f in /opt/vsp/launcher/image.tag "${KIT_DIR}/../launcher/image.tag"; do
  if [ -f "$f" ]; then
    cp "$f" "${TARGET}/image.tag.$(echo "$f" | tr '/' '_').snapshot"
  fi
done

# --- Last few pipeline runs' output dirs (just the small text files) ---
OUTPUTS_BASE="${VSP_OUTPUT_DIR:-$HOME/vsp-output}"
if [ -d "$OUTPUTS_BASE" ]; then
  mkdir -p "${TARGET}/recent_outputs"
  # Take the 3 most recent run directories.
  ls -1dt "${OUTPUTS_BASE}"/*/ 2>/dev/null | head -3 | while read -r run_dir; do
    if [ -d "$run_dir" ]; then
      run_name=$(basename "$run_dir")
      mkdir -p "${TARGET}/recent_outputs/${run_name}"
      # Copy small text-y files only (no big videos or models).
      for ext in csv json log txt html; do
        find "$run_dir" -maxdepth 2 -name "*.${ext}" -size -2M \
          -exec cp {} "${TARGET}/recent_outputs/${run_name}/" \; 2>/dev/null
      done
    fi
  done
fi

# --- Kit version (whatever's in the kit's CLIENT_INSTALL.md or VERSION file) ---
for f in "${KIT_DIR}/../VERSION" "${KIT_DIR}/../CLIENT_INSTALL.md"; do
  if [ -f "$f" ]; then
    cp "$f" "${TARGET}/" 2>/dev/null
  fi
done

# --- WSL2-specific (if running on Windows host) ---
if grep -qi microsoft /proc/version 2>/dev/null; then
  {
    echo "=== Detected: WSL2 environment ==="
    echo "Note: this means the host is Windows. Some checks may need to be re-run from PowerShell."
    echo
    echo "=== /proc/version ==="
    cat /proc/version
  } > "${TARGET}/wsl2.txt"
fi

# --- Tarball it up ---
cd "$WORK_DIR"
tar -czf "${KIT_DIR}/${BUNDLE}.tar.gz" "$BUNDLE"

cd - >/dev/null
rm -rf "$WORK_DIR"

SIZE=$(du -h "${KIT_DIR}/${BUNDLE}.tar.gz" | awk '{ print $1 }')
echo "Diagnostics bundle: ${KIT_DIR}/${BUNDLE}.tar.gz (${SIZE})"
echo
echo "Copy this file to USB and send it to support."
echo "It contains host info, NVIDIA + Docker state, recent run logs, and the install reports."
echo "It does NOT contain raw video files or model weights."
