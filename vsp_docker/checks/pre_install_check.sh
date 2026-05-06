#!/usr/bin/env bash
# ==================================================
# VSP Pipeline — Pre-install host check
# ==================================================
# Run on the client BEFORE `docker load`. Verifies the host meets the
# requirements for the air-gapped image. PASS / FAIL / WARN summary at
# the end + machine-readable line for the launcher.
#
# Usage: ./pre_install_check.sh [path/to/vsp-image-<build-id>.tar.zst]
# ==================================================

set -uo pipefail

# Don't `set -e` — we want every check to run even if earlier ones fail.

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${KIT_DIR}/pre_install_check.log"
IMG_TAR="${1:-}"

# --- Color helpers ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; NC=''
fi

PASSES=0
WARNS=0
FAILS=0

pass() { echo -e "${GREEN}[PASS]${NC} $*" | tee -a "$LOG"; PASSES=$((PASSES+1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG"; WARNS=$((WARNS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $*" | tee -a "$LOG"; FAILS=$((FAILS+1)); }
info() { echo -e "       $*" | tee -a "$LOG"; }

# Prompt-y warning for borderline cases that should not auto-proceed.
# In non-interactive mode, treat as FAIL — unless VSP_NONINTERACTIVE_PROCEED=1
# is set (used by the staging dry-run + CI). Production client installs should
# always be interactive so the operator sees and acknowledges the warning.
prompt_to_continue() {
  local msg="$1"
  echo -e "${YELLOW}[WARN+PROMPT]${NC} $msg" | tee -a "$LOG"
  if [ ! -t 0 ]; then
    if [ "${VSP_NONINTERACTIVE_PROCEED:-0}" = "1" ]; then
      info "Non-interactive + VSP_NONINTERACTIVE_PROCEED=1; treating as WARN, not FAIL."
      WARNS=$((WARNS+1))
      return 0
    fi
    fail "$msg (running non-interactively without VSP_NONINTERACTIVE_PROCEED=1, treating as FAIL)"
    return 1
  fi
  read -rp "       Continue anyway? [y/N] " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    info "User chose to proceed despite warning."
    WARNS=$((WARNS+1))
    return 0
  fi
  fail "$msg (user declined to proceed)"
  return 1
}

# --- Header ---
: > "$LOG"
echo "=========================================" | tee -a "$LOG"
echo "VSP Pipeline — Pre-install host check"     | tee -a "$LOG"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"      | tee -a "$LOG"
echo "Host: $(hostname)"                          | tee -a "$LOG"
echo "=========================================" | tee -a "$LOG"
echo                                              | tee -a "$LOG"

# --- 1. OS + kernel ---
echo "[1/9] OS + kernel" | tee -a "$LOG"
if [ -f /etc/os-release ]; then
  OS_ID=$(. /etc/os-release && echo "${ID:-unknown}")
  OS_VER=$(. /etc/os-release && echo "${VERSION_ID:-unknown}")
  pass "OS: $OS_ID $OS_VER"
else
  warn "/etc/os-release missing — non-standard distro"
fi
KERNEL=$(uname -r)
info "Kernel: $KERNEL"
echo | tee -a "$LOG"

# --- 2. NVIDIA driver ---
echo "[2/9] NVIDIA driver" | tee -a "$LOG"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  fail "nvidia-smi not found — install NVIDIA drivers first."
else
  DRIVER_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits 2>/dev/null | head -n1 | tr -d '[:space:]')
  if [ -z "$DRIVER_VER" ]; then
    fail "nvidia-smi present but no driver version returned"
  else
    DRIVER_MAJOR=${DRIVER_VER%%.*}
    if [ "${DRIVER_MAJOR:-0}" -ge 525 ] 2>/dev/null; then
      pass "NVIDIA driver: $DRIVER_VER (>=525, supports CUDA 12.x)"
    else
      fail "NVIDIA driver $DRIVER_VER too old (need >=525 for CUDA 12.x). Update drivers."
    fi
  fi
fi
echo | tee -a "$LOG"

# --- 3. GPU compute capability + VRAM ---
echo "[3/9] GPU compute capability + VRAM" | tee -a "$LOG"
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_INFO=$(nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader,nounits 2>/dev/null)
  if [ -z "$GPU_INFO" ]; then
    fail "nvidia-smi did not return GPU info"
  else
    while IFS=, read -r gpu_name cc mem_mib; do
      gpu_name=$(echo "$gpu_name" | sed 's/^ *//;s/ *$//')
      cc=$(echo "$cc" | sed 's/^ *//;s/ *$//')
      mem_mib=$(echo "$mem_mib" | sed 's/^ *//;s/ *$//')

      info "GPU: $gpu_name"
      info "  compute capability: $cc"
      info "  VRAM: ${mem_mib} MiB"

      # Compute-cap check: wheels ship sm_50..sm_90; usable floor is 7.0 (Volta).
      cc_int=$(echo "$cc" | awk -F. '{ printf "%d%02d", $1, $2 }')
      if [ "${cc_int:-0}" -ge 700 ] 2>/dev/null; then
        pass "  compute_cap $cc OK (>=7.0, Volta or newer)"
      elif [ "${cc_int:-0}" -ge 500 ] 2>/dev/null; then
        warn "  compute_cap $cc loads but is too slow for usable performance (Maxwell/Pascal)."
        warn "  Decode will work but be unacceptably slow. Recommend Volta+ (T4, V100, A100, H100, RTX 30xx+)."
      else
        fail "  compute_cap $cc not supported by shipped PyTorch wheels (need >=5.0; >=7.0 recommended)."
      fi

      # VRAM check
      if [ "${mem_mib:-0}" -ge 12000 ] 2>/dev/null; then
        pass "  VRAM ${mem_mib} MiB OK (>=12 GB)"
      elif [ "${mem_mib:-0}" -ge 8000 ] 2>/dev/null; then
        warn "  VRAM ${mem_mib} MiB is below recommended 12 GB. Decode may OOM on long videos."
      else
        fail "  VRAM ${mem_mib} MiB below 8 GB minimum."
      fi
    done <<< "$GPU_INFO"
  fi
fi
echo | tee -a "$LOG"

# --- 4. CPU + RAM ---
echo "[4/9] CPU + RAM" | tee -a "$LOG"
CPU_CORES=$(nproc 2>/dev/null || echo 0)
info "CPU cores: $CPU_CORES"
if [ "${CPU_CORES:-0}" -lt 4 ] 2>/dev/null; then
  fail "CPU cores ${CPU_CORES} below 4-core minimum."
elif [ "${CPU_CORES:-0}" -lt 8 ] 2>/dev/null; then
  warn "CPU cores ${CPU_CORES} below 8-core recommendation. Decode will be slower."
else
  pass "CPU cores: ${CPU_CORES} (>=8)"
fi

RAM_MIB=$(awk '/^MemTotal:/ { printf "%d", $2/1024 }' /proc/meminfo 2>/dev/null || echo 0)
RAM_GIB=$((RAM_MIB / 1024))
info "RAM: ${RAM_GIB} GiB"
if [ "$RAM_GIB" -lt 16 ] 2>/dev/null; then
  fail "RAM ${RAM_GIB} GiB below 16 GB minimum. Llama-2-7b will swap heavily; pipeline non-functional."
elif [ "$RAM_GIB" -lt 32 ] 2>/dev/null; then
  prompt_to_continue "RAM ${RAM_GIB} GiB is below 32 GB recommended. Decode will be slower." || true
else
  pass "RAM: ${RAM_GIB} GiB (>=32)"
fi
echo | tee -a "$LOG"

# --- 5. Disk free (Docker storage + output partition) ---
echo "[5/9] Disk free" | tee -a "$LOG"
DOCKER_DIR="${DOCKER_DATA_ROOT:-/var/lib/docker}"
if [ -d "$DOCKER_DIR" ]; then
  DOCKER_FREE_GIB=$(df -BG --output=avail "$DOCKER_DIR" 2>/dev/null | tail -n1 | tr -dc '0-9')
  info "Docker storage ($DOCKER_DIR): ${DOCKER_FREE_GIB} GiB free"
  if [ "${DOCKER_FREE_GIB:-0}" -lt 150 ] 2>/dev/null; then
    fail "Docker partition has only ${DOCKER_FREE_GIB} GiB free; need >=150 GiB (image is ~75 GiB; load needs ~2x temporarily)."
  else
    pass "Docker partition: ${DOCKER_FREE_GIB} GiB free (>=150)"
  fi
else
  warn "Docker storage dir $DOCKER_DIR not found; skipping disk check."
fi

OUTPUT_DIR="${VSP_OUTPUT_DIR:-$HOME/vsp-output}"
mkdir -p "$OUTPUT_DIR" 2>/dev/null
OUT_FREE_GIB=$(df -BG --output=avail "$OUTPUT_DIR" 2>/dev/null | tail -n1 | tr -dc '0-9')
info "Output partition ($OUTPUT_DIR): ${OUT_FREE_GIB} GiB free"
if [ "${OUT_FREE_GIB:-0}" -lt 20 ] 2>/dev/null; then
  warn "Output partition has only ${OUT_FREE_GIB} GiB free; recommend >=20 GiB for working space."
else
  pass "Output partition: ${OUT_FREE_GIB} GiB free (>=20)"
fi
echo | tee -a "$LOG"

# --- 6. Docker engine ---
echo "[6/9] Docker engine" | tee -a "$LOG"
if ! command -v docker >/dev/null 2>&1; then
  fail "docker not found — run the offline kit's install.sh first."
else
  if docker info >/dev/null 2>&1; then
    DOCKER_VER=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo unknown)
    pass "Docker daemon running (server version: $DOCKER_VER)"
  else
    fail "docker command found but daemon not reachable. Check 'systemctl status docker'."
  fi
fi
echo | tee -a "$LOG"

# --- 7. NVIDIA Container Toolkit ---
echo "[7/9] NVIDIA Container Toolkit (GPU passthrough into Docker)" | tee -a "$LOG"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  # Pull the test base image is not allowed offline; use the simplest CUDA image
  # that's likely already available, fall back to a generic check.
  TOOLKIT_OUT=$(docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi 2>&1 || true)
  if echo "$TOOLKIT_OUT" | grep -q "NVIDIA-SMI"; then
    pass "GPU is visible inside Docker containers"
  elif echo "$TOOLKIT_OUT" | grep -qE "could not select device driver.*gpu|nvidia-container-cli"; then
    fail "Docker cannot see GPU: nvidia-container-toolkit not configured."
    info "  Install nvidia-container-toolkit + restart docker daemon (sudo systemctl restart docker)."
  elif echo "$TOOLKIT_OUT" | grep -qE "Unable to find image|Error response from daemon"; then
    warn "Toolkit base image (nvidia/cuda:12.8.0-base-ubuntu22.04) not present locally and offline."
    info "  Skipping toolkit check. Verify manually: docker run --rm --gpus all <local-image> nvidia-smi"
  else
    fail "Docker GPU access failed for unknown reason. Diagnostic output:"
    echo "$TOOLKIT_OUT" | head -20 | sed 's/^/         /' | tee -a "$LOG"
  fi
else
  warn "Skipped (docker not available)."
fi
echo | tee -a "$LOG"

# --- 8. Image tarball verification ---
echo "[8/9] Image tarball" | tee -a "$LOG"
if [ -z "$IMG_TAR" ]; then
  warn "No image tarball path provided. Pass it as the first arg to verify."
  warn "  Skipping size/SHA256 check."
elif [ ! -f "$IMG_TAR" ]; then
  fail "Image tarball not found: $IMG_TAR"
else
  IMG_SIZE_GIB=$(du -BG "$IMG_TAR" | awk '{ print $1 }' | tr -dc '0-9')
  info "Tarball: $IMG_TAR (${IMG_SIZE_GIB} GiB)"
  if [ -f "${IMG_TAR}.sha256" ]; then
    if (cd "$(dirname "$IMG_TAR")" && sha256sum -c "$(basename "$IMG_TAR").sha256") >/dev/null 2>&1; then
      pass "SHA256 matches"
    else
      fail "SHA256 mismatch — tarball is corrupt or wrong file. Re-transfer."
    fi
  else
    warn "No .sha256 sidecar file; cannot verify integrity."
  fi
  # Quick zstd integrity test if it's a .tar.zst
  if [[ "$IMG_TAR" == *.zst ]] && command -v zstd >/dev/null 2>&1; then
    if zstd -t "$IMG_TAR" >/dev/null 2>&1; then
      pass "zstd integrity check passed"
    else
      fail "zstd integrity check failed — tarball is corrupt."
    fi
  fi
fi
echo | tee -a "$LOG"

# --- 9. Summary ---
echo "[9/9] Summary" | tee -a "$LOG"
echo "  PASS:  $PASSES" | tee -a "$LOG"
echo "  WARN:  $WARNS"  | tee -a "$LOG"
echo "  FAIL:  $FAILS"  | tee -a "$LOG"
echo                    | tee -a "$LOG"
if [ "$FAILS" -gt 0 ]; then
  echo -e "${RED}Pre-install check FAILED. Resolve the items above before running install.${NC}" | tee -a "$LOG"
  echo "Log: $LOG"
  exit 1
elif [ "$WARNS" -gt 0 ]; then
  echo -e "${YELLOW}Pre-install check passed with warnings. Review log before proceeding.${NC}" | tee -a "$LOG"
  echo "Log: $LOG"
  exit 0
else
  echo -e "${GREEN}Pre-install check passed cleanly. Ready for docker load.${NC}" | tee -a "$LOG"
  echo "Log: $LOG"
  exit 0
fi
