#!/bin/bash
#
# VSP Pipeline - Host-Side Launcher
#
# Starts the Docker container with GPU + port mapping,
# runs the UI server inside, and opens the browser.
#
# Usage:
#   ./vsp-start.sh              Start (default)
#   ./vsp-start.sh stop         Stop the container
#   ./vsp-start.sh status       Check if running
#
# Desktop icon: copy vsp-pipeline.desktop to ~/Desktop/
#

set -euo pipefail

# =====================
# Configuration
# =====================
CONTAINER_NAME="vsp-pipeline"
PORT=8765
URL="http://localhost:${PORT}"

# Auto-detect galaxy_export dir from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GALAXY_EXPORT_DIR="${GALAXY_EXPORT_DIR:-${SCRIPT_DIR}}"

# Load Docker image name from docker.conf
if [ -f "${SCRIPT_DIR}/docker.conf" ]; then
    source "${SCRIPT_DIR}/docker.conf"
fi
if [ -z "${DOCKER_IMAGE:-}" ] || [ "${DOCKER_IMAGE}" = "CHANGE_ME" ]; then
    echo "ERROR: DOCKER_IMAGE not configured."
    echo ""
    echo "  Edit ${SCRIPT_DIR}/docker.conf and set DOCKER_IMAGE to your image name."
    echo "  Known images:"
    echo "    Client:    vsp-llm-pipeline:latest"
    echo "    Developer: vsp-flat-standalone:cu128-exact"
    echo ""
    echo "  Or run directly: DOCKER_IMAGE=your-image:tag $0"
    exit 1
fi

# =====================
# Functions
# =====================

is_container_running() {
    docker ps --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"
}

is_server_ready() {
    curl -s --max-time 2 "${URL}/api/status" >/dev/null 2>&1
}

wait_for_server() {
    local max=60
    local i=0
    echo -n "Waiting for server"
    while [ $i -lt $max ]; do
        if is_server_ready; then
            echo " ready!"
            return 0
        fi
        echo -n "."
        sleep 0.5
        ((i++))
    done
    echo " timeout!"
    return 1
}

open_browser() {
    if command -v xdg-open &>/dev/null; then
        xdg-open "$1" 2>/dev/null &
    elif command -v firefox &>/dev/null; then
        firefox "$1" 2>/dev/null &
    elif command -v chromium-browser &>/dev/null; then
        chromium-browser "$1" 2>/dev/null &
    elif command -v google-chrome &>/dev/null; then
        google-chrome "$1" 2>/dev/null &
    else
        echo "Open in your browser: $1"
    fi
}

# =====================
# Commands
# =====================

do_start() {
    echo "========================================="
    echo "  VSP Pipeline Launcher"
    echo "========================================="
    echo ""

    # Already running?
    if is_container_running; then
        echo "Container already running."
        if is_server_ready; then
            echo "Server is ready - opening browser..."
            open_browser "${URL}"
            echo ""
            echo "UI: ${URL}"
            return 0
        else
            echo "Server not responding - restarting container..."
            docker stop "${CONTAINER_NAME}" 2>/dev/null || true
            sleep 2
        fi
    fi

    # Free port
    if command -v fuser &>/dev/null; then
        fuser -k ${PORT}/tcp 2>/dev/null || true
    fi
    sleep 1

    echo "Starting Docker container..."
    echo "  Image:  ${DOCKER_IMAGE}"
    echo "  Volume: ${GALAXY_EXPORT_DIR}"
    echo "  Port:   ${PORT}"
    echo ""

    docker run -d \
        --name "${CONTAINER_NAME}" \
        --rm \
        --gpus all \
        -p ${PORT}:${PORT} \
        -v "${GALAXY_EXPORT_DIR}:/host/galaxy_export" \
        "${DOCKER_IMAGE}" \
        bash -c "cd /host/galaxy_export/vsp-ui && python3 -m app.server"

    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to start container."
        echo "  1. Is Docker running?       docker info"
        echo "  2. Image exists?            docker images | grep ${DOCKER_IMAGE%%:*}"
        echo "  3. Port in use?             fuser ${PORT}/tcp"
        echo "  4. Another container?       docker ps"
        echo ""
        echo "Press Enter to close..."
        read
        exit 1
    fi

    echo "Container started."

    if ! wait_for_server; then
        echo ""
        echo "ERROR: Server did not start in 30 seconds."
        echo "Logs: docker logs ${CONTAINER_NAME}"
        echo ""
        echo "Press Enter to close..."
        read
        exit 1
    fi

    open_browser "${URL}"

    echo ""
    echo "========================================="
    echo "  VSP Pipeline is ready!"
    echo "========================================="
    echo ""
    echo "  UI:        ${URL}"
    echo "  Stop:      $0 stop"
    echo "  Shell:     docker exec -it ${CONTAINER_NAME} bash"
    echo ""
    echo "Press Enter to close this window..."
    read
}

do_stop() {
    echo "Stopping VSP Pipeline..."
    if is_container_running; then
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        echo "Stopped."
    else
        echo "Not running."
    fi
}

do_status() {
    if is_container_running; then
        echo "VSP Pipeline is RUNNING"
        echo "  Container: ${CONTAINER_NAME}"
        echo "  UI:        ${URL}"
        if is_server_ready; then
            echo "  Server:    responding"
        else
            echo "  Server:    not responding"
        fi
    else
        echo "VSP Pipeline is NOT running."
    fi
}

# =====================
# Main
# =====================
case "${1:-start}" in
    start)  do_start ;;
    stop)   do_stop ;;
    status) do_status ;;
    -h|--help)
        echo "Usage: $0 [start|stop|status]"
        ;;
    *)
        echo "Unknown: $1. Use: start, stop, status"
        exit 1
        ;;
esac
