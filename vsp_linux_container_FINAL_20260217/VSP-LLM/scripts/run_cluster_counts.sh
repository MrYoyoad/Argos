#!/usr/bin/env bash
set -euo pipefail

########################################
# Config / inputs
########################################

# Auto-detect repo root from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Split to process: default "train", but you can pass as first arg
SPLIT="${1:-train}"

# Where your .km and .cluster_counts live
# (override via env: LAB_DIR=/path/to/labels bash scripts/run_cluster_counts.sh)
LAB_DIR="${LAB_DIR:-${ROOT_DIR}/flat_labels}"

# Path to the original cluster_counts.py from the repo
CC_PY="${ROOT_DIR}/src/clustering/cluster_counts.py"

# Input .km and output .cluster_counts paths for this split
UNIT_PTH="${LAB_DIR}/${SPLIT}.km"
OUT_PTH="${LAB_DIR}/${SPLIT}.cluster_counts"

echo ">>> run_cluster_counts.sh"
echo "    ROOT_DIR  = ${ROOT_DIR}"
echo "    SPLIT     = ${SPLIT}"
echo "    LAB_DIR   = ${LAB_DIR}"
echo "    CC_PY     = ${CC_PY}"
echo "    UNIT_PTH  = ${UNIT_PTH}"
echo "    OUT_PTH   = ${OUT_PTH}"
echo

########################################
# Safety checks
########################################

if [[ ! -f "${UNIT_PTH}" ]]; then
  echo "ERROR: .km file not found: ${UNIT_PTH}" >&2
  exit 1
fi

if [[ ! -f "${CC_PY}" ]]; then
  echo "ERROR: cluster_counts.py not found: ${CC_PY}" >&2
  exit 1
fi

mkdir -p "$(dirname "${OUT_PTH}")"

########################################
# Patch cluster_counts.py (unit_pth / out_pth)
########################################

python3 - << EOF
from pathlib import Path
import re

cc_path = Path("${CC_PY}")
text = cc_path.read_text()

def replace_assign(src: str, name: str, new_value: str):
    # matches lines like:
    #   unit_pth = '...'
    #   unit_pth= "..."
    pattern = rf"^({name}\s*=\s*).*$"
    repl = r"\1'" + new_value + r"'"  # keep everything before '=' and insert our path
    new_src, n = re.subn(pattern, repl, src, flags=re.MULTILINE)
    if n == 0:
        print(f"WARNING: did not find assignment for {name} in {cc_path}")
    else:
        print(f"Updated {name} -> {new_value}")
    return new_src

text = replace_assign(text, "unit_pth", "${UNIT_PTH}")
text = replace_assign(text, "out_pth", "${OUT_PTH}")

cc_path.write_text(text)
EOF

########################################
# Run cluster_counts.py (as in the git instructions)
########################################

echo
echo ">>> Running: python3 ${CC_PY}"
python3 "${CC_PY}"

echo
echo ">>> Done. Wrote: ${OUT_PTH}"