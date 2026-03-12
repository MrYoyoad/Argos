# Installation Guide

> **Note**: These instructions are for updating an existing working VSP pipeline environment. If you already have a functional container, these steps apply the latest improvements and bug fixes.

## Prerequisites

- NVIDIA GPU with CUDA support (24GB+ VRAM recommended)
- Python 3.10+
- FFmpeg installed and available on PATH
- ~50GB disk space for models and dependencies

## Virtual Environments

The pipeline uses **3 separate Python virtual environments**, one per component. Each pipeline stage activates the correct environment automatically — you only need to set them up once.

### 1. ASR & Preprocessing

Handles Whisper transcription, face detection, mouth cropping, and video normalization.

**Location**: `~/auto_avsr/pre-process-venv/`

```bash
cd ~/auto_avsr
python3 -m venv pre-process-venv
source pre-process-venv/bin/activate

pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install pytorch-lightning openai-whisper==20250625
pip install -r preparation/requirements.txt
pip install mediapipe-0.10.9-cp311-cp311-linux_x86_64.whl
```

**Key packages**: PyTorch (CUDA 12.1), Whisper, Mediapipe, OpenCV, scikit-learn, ffmpeg-python, SentencePiece

See [`auto_avsr/preparation/requirements.txt`](auto_avsr/preparation/requirements.txt) for the full dependency list.

### 2. VSP-LLM

Handles LLaMA-2 inference, AV-HuBERT feature extraction, K-means clustering, and decoding.

**Location**: `~/vsp-llm-yoad-venv/`

```bash
python3 -m venv ~/vsp-llm-yoad-venv
source ~/vsp-llm-yoad-venv/bin/activate

pip install --upgrade pip
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r ~/VSP-LLM/requirements.txt

# Fairseq (both copies, editable mode)
cd ~/VSP-LLM/fairseq && pip install -e .
cd ~/av_hubert/fairseq && pip install -e .

# Clustering dependencies
pip install soundfile joblib sklearn submitit npy-append-array
```

**Key packages**: PyTorch (CUDA 12.1), HuggingFace Transformers, Fairseq (custom), Hydra, bitsandbytes, PEFT (LoRA), scikit-learn, librosa

See [`VSP-LLM/requirements.txt`](VSP-LLM/requirements.txt) for the full dependency list.

### 3. Web UI

Handles the browser interface for video management and transcription editing.

**Location**: `~/vsp-ui/venv/`

```bash
cd ~/vsp-ui
python3 -m venv venv
source venv/bin/activate
pip install flask opencv-python
```

## Verification

After setup, verify each environment:

```bash
source ~/auto_avsr/pre-process-venv/bin/activate
python -c "import whisper; import cv2; import mediapipe; print('ASR env OK')"

source ~/vsp-llm-yoad-venv/bin/activate
python -c "import torch; import transformers; import fairseq; print('VSP-LLM env OK')"

source ~/vsp-ui/venv/bin/activate
python -c "import flask; print('UI env OK')"
```

## Manual Activation

The pipeline handles environment switching automatically. For manual work:

```bash
source ~/auto_avsr/pre-process-venv/bin/activate   # ASR / preprocessing
source ~/vsp-llm-yoad-venv/bin/activate             # VSP-LLM / decode
source ~/vsp-ui/venv/bin/activate                   # Web UI
```

## Container Deployment

For container-specific setup and transfer instructions, see:
- [Container Update Guide](docs/guides/container-update-feb2026.md)
- [Container Sync Changelog](docs/container-sync-changelog.md)
