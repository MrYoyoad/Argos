#!/bin/bash
# Start the VSP container with GPU, port mapping, and galaxy_export mounted.
#
# This gives you an interactive shell inside the container.
# For one-click UI launch, use vsp-start.sh instead.
#
# Usage:
#   bash docker-run.sh                # interactive shell
#   bash docker-run.sh <command>      # run a specific command

GALAXY_EXPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load Docker image name from docker.conf (tolerant parser)
if [ -f "${GALAXY_EXPORT_DIR}/docker.conf" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// /}" ]] && continue
        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*) ]]; then
            key="${BASH_REMATCH[1]}"
            val="${BASH_REMATCH[2]}"
            val="${val%"${val##*[![:space:]]}"}"
            val="${val#\"}" ; val="${val%\"}"
            val="${val#\'}" ; val="${val%\'}"
            export "$key=$val"
        fi
    done < "${GALAXY_EXPORT_DIR}/docker.conf"
fi
if [ -z "${DOCKER_IMAGE:-}" ] || [ "${DOCKER_IMAGE}" = "CHANGE_ME" ]; then
    echo "ERROR: DOCKER_IMAGE not configured."
    echo ""
    echo "  Edit ${GALAXY_EXPORT_DIR}/docker.conf and set DOCKER_IMAGE to your image name."
    echo "  Known images:"
    echo "    Client:    vsp-llm-pipeline:latest"
    echo "    Developer: vsp-flat-standalone:cu128-exact"
    echo ""
    echo "  Tip: Run vsp-start.sh instead — it auto-detects the image."
    exit 1
fi

docker run --rm -it --gpus all \
  -p 8765:8765 \
  -v "${GALAXY_EXPORT_DIR}:/host/galaxy_export" \
  "${DOCKER_IMAGE}" \
  "$@"
