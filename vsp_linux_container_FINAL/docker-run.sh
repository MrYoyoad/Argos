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

docker run --rm -it --gpus all \
  -p 8765:8765 \
  -v "${GALAXY_EXPORT_DIR}:/host/galaxy_export" \
  vsp-flat-standalone:cu128-exact \
  "$@"
