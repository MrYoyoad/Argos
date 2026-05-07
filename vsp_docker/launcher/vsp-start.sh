#!/usr/bin/env bash
# =====================================================
# VSP Pipeline — UI mode launcher (Linux)
# =====================================================
# Starts the Docker container with:
#   - GPU passthrough
#   - Port 8080 mapped (UI server)
#   - vsp_input bind-mount (drag-drop + manual transcriptions)
#   - vsp_output bind-mount (reports, burned videos)
#   - vsp_transcriptions bind-mount (persistent across runs)
# Then opens the browser to http://localhost:8080.
#
# Usage: ./vsp-start.sh           # start
#        ./vsp-start.sh stop      # stop the container
#        ./vsp-start.sh status    # check if running
# =====================================================

set -euo pipefail

# ----- Self-relaunch in a terminal if launched from a desktop file -----
if [ ! -t 0 ] && [ ! -t 1 ] && [ "${VSP_IN_TERMINAL:-}" != "1" ]; then
  for t in x-terminal-emulator gnome-terminal kgx gnome-console xfce4-terminal mate-terminal konsole lxterminal tilix terminator kitty alacritty xterm; do
    p="$(command -v "$t" 2>/dev/null || true)"
    if [ -n "$p" ] && [ -x "$p" ]; then
      export VSP_IN_TERMINAL=1
      case "$t" in
        gnome-terminal|kgx|gnome-console) exec "$p" -- /usr/bin/bash "$0" "$@" ;;
        *)                                exec "$p" -e /usr/bin/bash "$0" "$@" ;;
      esac
    fi
  done
  zenity --error --title="VSP Pipeline" --text="No terminal emulator found. Open a terminal and run: $0" 2>/dev/null || true
  exit 1
fi

# ----- Resolve image tag -----
TAG_FILE="/opt/vsp/launcher/image.tag"
if [ ! -f "$TAG_FILE" ]; then
  TAG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/image.tag"
fi
if [ ! -f "$TAG_FILE" ]; then
  echo "ERROR: image.tag config not found: $TAG_FILE"
  echo "Run install_launcher.sh first."
  exit 1
fi
IMG_TAG="$(tr -d '[:space:]' < "$TAG_FILE")"
[[ "$IMG_TAG" =~ ^[a-zA-Z0-9._/:-]+$ ]] || { echo "Invalid tag: $IMG_TAG"; exit 1; }

# ----- Settings -----
CONTAINER_NAME="${VSP_CONTAINER_NAME:-vsp}"
PORT="${VSP_UI_PORT:-8080}"
URL="http://localhost:${PORT}"

INPUT_DIR="${VSP_INPUT_DIR:-$HOME/vsp-input}"
OUTPUT_DIR="${VSP_OUTPUT_DIR:-$HOME/vsp-output}"
TRANS_DIR="${VSP_TRANSCRIPTIONS_DIR:-$HOME/vsp-transcriptions}"

mkdir -p "$INPUT_DIR" "$OUTPUT_DIR" "$TRANS_DIR"

# ----- Helpers -----
is_container_running() {
  [ "$(docker ps --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' 2>/dev/null)" = "${CONTAINER_NAME}" ]
}

is_server_ready() {
  curl -s --max-time 2 "${URL}/api/status" >/dev/null 2>&1
}

open_browser() {
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$1" 2>/dev/null &
  elif command -v gnome-open >/dev/null 2>&1; then
    gnome-open "$1" 2>/dev/null &
  elif command -v firefox >/dev/null 2>&1; then
    firefox "$1" 2>/dev/null &
  elif command -v google-chrome >/dev/null 2>&1; then
    google-chrome "$1" 2>/dev/null &
  else
    echo "Open in your browser: $1"
  fi
}

# ----- Commands -----
do_start() {
  echo "========================================="
  echo "  VSP Pipeline — UI mode"
  echo "========================================="
  echo "Image:           $IMG_TAG"
  echo "Port:            $PORT"
  echo "Input dir:       $INPUT_DIR (rw — drop videos here OR via UI)"
  echo "Output dir:      $OUTPUT_DIR"
  echo "Transcriptions:  $TRANS_DIR (persistent across runs)"
  echo "URL:             $URL"
  echo "========================================="

  if is_container_running; then
    echo "Container already running."
    if is_server_ready; then
      echo "Server is ready — opening browser."
      open_browser "$URL"
      return 0
    fi
    echo "Server not responding — restarting."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    sleep 2
  fi

  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

  # Free port if anything else is using it
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
  fi
  sleep 1

  # Wait-for-ready + open-browser in background
  (
    for _ in $(seq 1 60); do
      if curl -s --max-time 2 "${URL}/api/status" >/dev/null 2>&1; then
        echo
        echo "========================================="
        echo "  VSP Pipeline is ready: $URL"
        echo "  Stop: close this window or Ctrl+C"
        echo "========================================="
        open_browser "$URL"
        exit 0
      fi
      sleep 1
    done
    echo "Server did not become ready within 60s. Check the container output above."
  ) &

  # Start the container in foreground (tail logs to user's terminal)
  docker run --rm -it \
    --name "$CONTAINER_NAME" \
    --gpus all \
    -p "${PORT}:${PORT}" \
    --entrypoint /bin/bash \
    -e VSP_INPUT_DIR=/data/in \
    -e VSP_OUTPUT_DIR=/data/out \
    -e VSP_TRANSCRIPTIONS_DIR=/data/transcriptions \
    -e VSP_UI_HOST=0.0.0.0 \
    -e VSP_UI_PORT="$PORT" \
    -v "$INPUT_DIR:/data/in" \
    -v "$OUTPUT_DIR:/data/out" \
    -v "$TRANS_DIR:/data/transcriptions" \
    "$IMG_TAG" \
    -c "cd /workspace/vsp-ui && python3 -m app.server"

  echo
  echo "Server stopped."
}

do_stop() {
  echo "Stopping VSP Pipeline UI..."
  if is_container_running; then
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    echo "Stopped."
  else
    echo "Not running."
  fi
}

do_status() {
  if is_container_running; then
    echo "VSP Pipeline UI is RUNNING"
    echo "  Container: $CONTAINER_NAME"
    echo "  URL:       $URL"
    is_server_ready && echo "  Server:    responding" || echo "  Server:    not responding"
  else
    echo "VSP Pipeline UI is NOT running."
  fi
}

case "${1:-start}" in
  start)  do_start ;;
  stop)   do_stop ;;
  status) do_status ;;
  *) echo "Usage: $0 {start|stop|status}"; exit 1 ;;
esac
