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
# Self-relaunch in a terminal if not already in one
# =====================
# When launched from a .desktop file or file manager, there's no terminal.
# Detect this and re-exec ourselves inside a terminal emulator.
if [ ! -t 0 ] && [ ! -t 1 ] && [ "${VSP_IN_TERMINAL:-}" != "1" ]; then
    # Find a terminal emulator (Layer 1: known terminals)
    for _term in x-terminal-emulator gnome-terminal kgx gnome-console xfce4-terminal mate-terminal konsole lxterminal tilix terminator kitty alacritty xterm; do
        _term_path="$(command -v "$_term" 2>/dev/null || true)"
        if [ -n "$_term_path" ] && [ -x "$_term_path" ]; then
            export VSP_IN_TERMINAL=1
            # Use /usr/bin/bash so the script doesn't need +x (mounted filesystems)
            case "$_term" in
                gnome-terminal|kgx|gnome-console) exec "$_term_path" -- /usr/bin/bash "$0" "$@" ;;
                *)              exec "$_term_path" -e /usr/bin/bash "$0" "$@" ;;
            esac
        fi
    done
    # Layer 2: search for any terminal-like executable in /usr/bin
    for _candidate in /usr/bin/*terminal* /usr/bin/*-term; do
        if [ -x "$_candidate" ] && [ -f "$_candidate" ]; then
            export VSP_IN_TERMINAL=1
            exec "$_candidate" -e /usr/bin/bash "$0" "$@"
        fi
    done
    # No terminal found — show actionable error
    _msg="VSP Pipeline: No terminal emulator found.\n\nOpen any terminal application and run:\n  $0"
    notify-send "VSP Pipeline" "No terminal emulator found. Open a terminal and run: $0" 2>/dev/null || true
    # Also try zenity for a visible dialog
    zenity --error --title="VSP Pipeline" --text="$_msg" 2>/dev/null || true
    exit 1
fi

# =====================
# Configuration
# =====================
CONTAINER_NAME="vsp-pipeline"
PORT=8765
URL="http://localhost:${PORT}"

# Auto-detect galaxy_export dir from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GALAXY_EXPORT_DIR="${GALAXY_EXPORT_DIR:-${SCRIPT_DIR}}"

# Load Docker image name from docker.conf (tolerant of spaces around =)
if [ -f "${SCRIPT_DIR}/docker.conf" ]; then
    # Parse KEY=VALUE lines, stripping spaces around = so "KEY = VALUE" works
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// /}" ]] && continue
        # Extract key and value, stripping spaces around =
        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*) ]]; then
            key="${BASH_REMATCH[1]}"
            val="${BASH_REMATCH[2]}"
            # Strip trailing whitespace and quotes
            val="${val%"${val##*[![:space:]]}"}"
            val="${val#\"}" ; val="${val%\"}"
            val="${val#\'}" ; val="${val%\'}"
            export "$key=$val"
        fi
    done < "${SCRIPT_DIR}/docker.conf"
fi
if [ -z "${DOCKER_IMAGE:-}" ] || [ "${DOCKER_IMAGE}" = "CHANGE_ME" ]; then
    # Auto-detect: search local Docker images for VSP-related names
    echo "DOCKER_IMAGE not configured — searching local Docker images..."
    _detected=""
    if command -v docker &>/dev/null; then
        # Look for images whose repository name contains "vsp"
        _candidates=$(docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null \
            | grep -i 'vsp' \
            | grep -v '<none>' \
            || true)
        _count=$(echo "$_candidates" | grep -c . 2>/dev/null || echo 0)

        if [ "$_count" -eq 1 ]; then
            _detected="$_candidates"
            echo "  Found: ${_detected}"
        elif [ "$_count" -gt 1 ]; then
            echo "  Found multiple VSP images:"
            echo "$_candidates" | nl -ba -w2 -s') '
            echo ""
            echo -n "  Enter number to select (or press Enter for #1): "
            read -r _choice
            if [ -z "$_choice" ]; then _choice=1; fi
            _detected=$(echo "$_candidates" | sed -n "${_choice}p")
            if [ -z "$_detected" ]; then
                echo "  Invalid choice."
                echo "Press Enter to close..."
                read
                exit 1
            fi
            echo "  Selected: ${_detected}"
        fi
    fi

    if [ -n "$_detected" ]; then
        DOCKER_IMAGE="$_detected"
        # Save to docker.conf for future runs
        if [ -f "${SCRIPT_DIR}/docker.conf" ]; then
            # Update existing file (replace CHANGE_ME or empty value)
            sed -i "s|^DOCKER_IMAGE=.*|DOCKER_IMAGE=${DOCKER_IMAGE}|" "${SCRIPT_DIR}/docker.conf"
        else
            echo "# Docker image for VSP Pipeline (auto-detected)" > "${SCRIPT_DIR}/docker.conf"
            echo "DOCKER_IMAGE=${DOCKER_IMAGE}" >> "${SCRIPT_DIR}/docker.conf"
        fi
        echo "  Saved to docker.conf (won't ask again)."
        echo ""
    else
        echo ""
        echo "ERROR: No VSP Docker image found."
        echo ""
        echo "  Edit ${SCRIPT_DIR}/docker.conf and set DOCKER_IMAGE to your image name."
        echo "  Known images:"
        echo "    Client:    vsp-llm-pipeline:latest"
        echo "    Developer: vsp-flat-standalone:cu128-exact"
        echo ""
        echo "  Or run directly: DOCKER_IMAGE=your-image:tag $0"
        echo ""
        echo "Press Enter to close..."
        read
        exit 1
    fi
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

    # Clean up anything that might block us
    echo "Cleaning up previous sessions..."

    # Stop and remove any container with our name (running or stopped)
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    # Also stop any other container using our port
    PORT_CONTAINER=$(docker ps --filter "publish=${PORT}" --format '{{.Names}}' 2>/dev/null | head -1)
    if [ -n "${PORT_CONTAINER}" ]; then
        echo "  Stopping container '${PORT_CONTAINER}' (using port ${PORT})..."
        docker stop "${PORT_CONTAINER}" 2>/dev/null || true
        docker rm -f "${PORT_CONTAINER}" 2>/dev/null || true
    fi

    # Free port on host (in case something non-Docker is using it)
    if command -v fuser &>/dev/null; then
        fuser -k ${PORT}/tcp 2>/dev/null || true
    fi
    sleep 1

    echo "Starting Docker container..."
    echo "  Image:  ${DOCKER_IMAGE}"
    echo "  Volume: ${GALAXY_EXPORT_DIR}"
    echo "  Port:   ${PORT}"
    echo ""
    echo "Server output will appear below."
    echo "Close this window (or Ctrl+C) to stop the server."
    echo ""

    # Launch background task: wait for server, then open browser
    (
        local_max=60
        local_i=0
        while [ $local_i -lt $local_max ]; do
            if curl -s --max-time 2 "${URL}/api/status" >/dev/null 2>&1; then
                echo ""
                echo "========================================="
                echo "  VSP Pipeline is ready!"
                echo "========================================="
                echo ""
                echo "  UI:   ${URL}"
                echo "  Stop: close this window or Ctrl+C"
                echo ""
                open_browser "${URL}"
                exit 0
            fi
            sleep 1
            local_i=$((local_i + 1))
        done
        echo ""
        echo "========================================="
        echo "  SERVER FAILED TO START"
        echo "========================================="
        echo ""
        echo "Server did not respond within 60 seconds."
        echo ""
        echo "--- Container logs ---"
        docker logs "${CONTAINER_NAME}" 2>&1 || echo "(could not retrieve logs)"
        echo "--- End of logs ---"
        echo ""
        echo "If you see a Python error above, please report it."
    ) &
    BROWSER_PID=$!

    # Clean up background task when this script exits
    trap "kill ${BROWSER_PID} 2>/dev/null; exit" INT TERM EXIT

    # Run Docker in foreground — this is the exact mode confirmed working
    # VSP_INPUT_DIR: tells config.py where the input folder is INSIDE the container
    # VSP_HOST_INPUT_DIR: tells the UI what path to show for "Open Folder" on the HOST
    docker run --rm -it \
        --name "${CONTAINER_NAME}" \
        --gpus all \
        -p ${PORT}:${PORT} \
        -e "VSP_INPUT_DIR=/host/galaxy_export/vsp_input" \
        -e "VSP_HOST_INPUT_DIR=${GALAXY_EXPORT_DIR}/vsp_input" \
        -v "${GALAXY_EXPORT_DIR}:/host/galaxy_export" \
        "${DOCKER_IMAGE}" \
        -c 'cd /host/galaxy_export/vsp-ui && python3 -m app.server; EC=$?; if [ $EC -ne 0 ]; then echo ""; echo "========================================="; echo "  SERVER FAILED (exit code $EC)"; echo "========================================="; echo "  Check the error messages above."; echo "  Press Enter to close..."; read; fi'

    echo ""
    echo "Server stopped."
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
