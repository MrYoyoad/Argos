#!/bin/bash
# Run this on the Linux container to verify system setup

echo "=== System Dependencies Check ==="

# Check CUDA
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA driver installed"
    nvidia-smi | head -3
else
    echo "✗ NVIDIA driver NOT found"
fi

if command -v nvcc &> /dev/null; then
    echo "✓ CUDA toolkit installed"
    nvcc --version | grep release
else
    echo "✗ CUDA toolkit NOT found"
fi

# Check Python
if command -v python3.9 &> /dev/null; then
    echo "✓ Python 3.9 installed"
    python3.9 --version
else
    echo "✗ Python 3.9 NOT found (required!)"
fi

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg installed"
    ffmpeg -version | head -1
else
    echo "✗ ffmpeg NOT found"
    echo "  Install: apt-get install ffmpeg"
fi

# Check essential libraries
echo ""
echo "=== Checking System Libraries ==="
libs=("libsm6" "libxext6" "libxrender1" "libgomp1" "libglib2.0-0")
for lib in "${libs[@]}"; do
    if dpkg -l | grep -q "$lib"; then
        echo "✓ $lib"
    else
        echo "✗ $lib NOT found"
    fi
done

echo ""
echo "=== Directory Structure Check ==="
dirs=(
    "/workspace/auto_avsr"
    "/workspace/VSP-LLM"
    "/workspace/av_hubert"
    "/workspace/vsp_input"
    "/workspace/vsp-ui"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "✗ $dir NOT found"
    fi
done

echo ""
echo "=== Critical Files Check ==="
files=(
    "/workspace/run_flat_english_pipeline.sh"
    "/workspace/VSP-LLM/checkpoints/large_vox_iter5.pt"
    "/workspace/VSP-LLM/checkpoints/checkpoint_finetune.pt"
    "/workspace/VSP-LLM/checkpoints/Llama-2-7b-hf/config.json"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file NOT found"
    fi
done

echo ""
echo "=== Virtual Environments Check ==="
venvs=(
    "/workspace/auto_avsr/pre-process-venv"
    "/workspace/vsp-llm-yoad-venv"
    "/workspace/vsp-ui/venv"
)

for venv in "${venvs[@]}"; do
    if [ -d "$venv" ] && [ -f "$venv/bin/activate" ]; then
        echo "✓ $venv exists"
    else
        echo "✗ $venv NOT found or invalid"
    fi
done

echo ""
echo "=== Permissions Check ==="
# Check if files are executable
if [ -x "/workspace/run_flat_english_pipeline.sh" ]; then
    echo "✓ Pipeline script is executable"
else
    echo "✗ Pipeline script NOT executable"
    echo "  Fix: chmod +x /workspace/run_flat_english_pipeline.sh"
fi

