#!/bin/bash
#
# VSP Pipeline UI Launcher
# Starts the server and opens the browser + input folder
#

set -euo pipefail

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8765
HOST="127.0.0.1"
URL="http://${HOST}:${PORT}"
PID_FILE="${HOME}/.vsp-ui.pid"
LOG_FILE="${HOME}/.vsp-ui.log"
INPUT_DIR="${HOME}/vsp_input"

# Ensure input directory exists
mkdir -p "${INPUT_DIR}"

# Function to check if server is running
is_server_running() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid
        pid=$(cat "${PID_FILE}")
        if kill -0 "${pid}" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to wait for server to be ready
wait_for_server() {
    local max_attempts=40  # 20 seconds max
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s "${URL}/api/status" > /dev/null 2>&1; then
            return 0
        fi
        sleep 0.5
        ((attempt++))
    done

    return 1
}

# Function to open URL in browser
open_browser() {
    local url="$1"

    # Try various browsers/openers
    if command -v xdg-open &> /dev/null; then
        xdg-open "${url}" 2>/dev/null &
    elif command -v firefox &> /dev/null; then
        firefox "${url}" 2>/dev/null &
    elif command -v chromium-browser &> /dev/null; then
        chromium-browser "${url}" 2>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "${url}" 2>/dev/null &
    else
        echo "Could not find a browser. Please open: ${url}"
        return 1
    fi
    return 0
}

# Function to open folder
open_folder() {
    local folder="$1"

    if command -v xdg-open &> /dev/null; then
        xdg-open "${folder}" 2>/dev/null &
    elif command -v nautilus &> /dev/null; then
        nautilus "${folder}" 2>/dev/null &
    elif command -v nemo &> /dev/null; then
        nemo "${folder}" 2>/dev/null &
    elif command -v thunar &> /dev/null; then
        thunar "${folder}" 2>/dev/null &
    elif command -v dolphin &> /dev/null; then
        dolphin "${folder}" 2>/dev/null &
    elif command -v pcmanfm &> /dev/null; then
        pcmanfm "${folder}" 2>/dev/null &
    else
        echo "Could not open folder. Path: ${folder}"
        return 1
    fi
    return 0
}

# Function to start the server
start_server() {
    echo "Starting VSP Pipeline UI server..."

    # Clean up any processes using the port (address already in use)
    echo "Checking for processes using port ${PORT}..."
    if lsof -ti:${PORT} > /dev/null 2>&1; then
        echo "Killing existing processes on port ${PORT}..."
        lsof -ti:${PORT} | xargs kill -9 2>/dev/null || true
        sleep 1
    fi

    # Change to app directory
    cd "${APP_DIR}"

    # Start server in background
    nohup python3 -m app.server > "${LOG_FILE}" 2>&1 &
    local server_pid=$!

    # Save PID
    echo "${server_pid}" > "${PID_FILE}"

    echo "Server started with PID ${server_pid}"
    echo "Log file: ${LOG_FILE}"
}

# Function to stop the server
stop_server() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid
        pid=$(cat "${PID_FILE}")

        if kill -0 "${pid}" 2>/dev/null; then
            echo "Stopping server (PID ${pid})..."
            kill "${pid}" 2>/dev/null || true
            sleep 1

            # Force kill if still running
            if kill -0 "${pid}" 2>/dev/null; then
                kill -9 "${pid}" 2>/dev/null || true
            fi
        fi

        rm -f "${PID_FILE}"
    fi
}

# Main logic
main() {
    # Parse arguments
    case "${1:-}" in
        stop)
            stop_server
            echo "Server stopped."
            exit 0
            ;;
        restart)
            stop_server
            sleep 1
            ;;
        status)
            if is_server_running; then
                echo "Server is running (PID $(cat "${PID_FILE}"))"
                echo "URL: ${URL}"
            else
                echo "Server is not running"
            fi
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [start|stop|restart|status]"
            echo ""
            echo "Commands:"
            echo "  (none)   Start server and open browser (default)"
            echo "  stop     Stop the server"
            echo "  restart  Restart the server"
            echo "  status   Check if server is running"
            exit 0
            ;;
    esac

    # Check if already running
    if is_server_running; then
        echo "Server already running, opening browser..."
    else
        # Start the server
        start_server

        # Wait for it to be ready
        echo "Waiting for server to start..."
        if ! wait_for_server; then
            echo "ERROR: Server failed to start. Check log: ${LOG_FILE}"
            cat "${LOG_FILE}" | tail -20
            exit 1
        fi
        echo "Server is ready!"
    fi

    # Open browser
    echo "Opening browser..."
    open_browser "${URL}"

    # Open input folder (with small delay so browser opens first)
    sleep 1
    echo "Opening input folder: ${INPUT_DIR}"
    open_folder "${INPUT_DIR}"

    echo ""
    echo "VSP Pipeline UI is ready!"
    echo "  - Web UI: ${URL}"
    echo "  - Input folder: ${INPUT_DIR}"
    echo ""
    echo "Drag your videos into the input folder, then use the web UI to process them."
}

main "$@"
