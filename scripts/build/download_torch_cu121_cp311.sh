#!/usr/bin/env bash
set -euo pipefail

DEST="$HOME/torch_gpu_wheels_cu121_py311"
mkdir -p "$DEST"
cd "$DEST"

echo "Downloading cu121 CUDA wheels for Python 3.11 into: $DEST"

python3 -m pip download \
  --only-binary=:all: \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --abi cp311 \
  --index-url https://download.pytorch.org/whl/cu121 \
  --extra-index-url https://pypi.org/simple \
  -d "$DEST" \
  "torch==2.2.2" \
  "torchaudio==2.2.2" \
  "torchvision==0.17.2"

echo
echo "Downloaded wheels:"
ls -1 "$DEST"
