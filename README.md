# Visual Speech Processing Pipeline

A production-ready lip-reading pipeline combining Audio-Visual Speech Recognition (AVSR), AV-HuBERT feature extraction, and LLaMA2-based decoding for visual speech transcription.

## Features

- **Automated Pipeline** - Single-command processing from raw video to transcriptions
- **Modular Architecture** - 11 reusable bash modules with 37 automated tests
- **Intelligent Transcription Management** - Whisper runs only once per video, manual transcriptions persist across runs
- **Segment-First Processing** - Efficient 12-second segmentation with 2-second overlap prevents word boundary splits
- **Web UI** - Flask-based interface for video management, manual transcription, and progress monitoring
- **GPU Accelerated** - NVENC encoding, CUDA-based preprocessing and inference

## Quick Start

```bash
# Run the complete pipeline
./run_flat_english_pipeline.sh /path/to/videos

# Or use the web UI
cd vsp-ui && ./launcher.sh
```

## Architecture

```
Raw Videos → Segmentation → Normalization → Mouth Cropping → ASR (Whisper)
    → Format Conversion → Manifests → K-means Clustering → VSP-LLM Decode
    → Client Outputs (JSON Reports + Burned Videos)
```

### Core Components

- **auto_avsr/** - PyTorch Lightning AVSR framework, preprocessing, Whisper integration
- **VSP-LLM/** - LLaMA2-7B based visual speech processing with AV-HuBERT features
- **av_hubert/** - AV-HuBERT model utilities and LRS3 format conversion
- **lib/** - Modular pipeline stages (normalization, ASR, clustering, decode, outputs)
- **vsp-ui/** - Flask web interface with transcription management

## Pipeline Stages

| Stage | Description | Output |
|-------|-------------|--------|
| [0.1] Fast Segmentation | Codec copy split (12s segments, 2s overlap) | `preprocessed_flat_seg12/fast_segments/` |
| [0.5] Normalization | HDR/10-bit conversion, GPU encoding | `auto_avsr/flat/` |
| [0.6] Transcription Reuse | Copy existing manual transcriptions | `flat_wrd/` |
| [2] Mouth Cropping | Mediapipe face detection, 88x88 crops @ 25fps | `preprocessed_flat_seg12/flat/` |
| [3] ASR | Whisper transcription (skips existing) | `flat_wrd/*.wrd` |
| [6] K-means Clustering | 200 clusters on AV-HuBERT features | `flat_kmeans_200.bin` |
| [7] VSP-LLM Decode | LLaMA2-based transcription | `decode/vsr/en/*.json` |
| [8] Client Outputs | JSON reports + burned videos | `flat_runs_archive/[timestamp]/client_outputs/` |

## Key Features

### Unified Transcription Management
All transcriptions stored in `~/vsp_input/.transcriptions/` with type tracking (manual/auto). Whisper automatically skips videos with existing transcriptions, saving hours on subsequent runs.

### Segment-First Normalization
Videos segmented first using fast codec copy, then normalized at segment level. More efficient for long videos with lower memory usage.

### Dual-Environment Support
- **EC2** (`/home/ubuntu/`) - Development and testing
- **Linux Container** (`/workspace/`) - Production deployment

## Requirements

- **GPU**: NVIDIA with CUDA 12.1 support (24GB+ VRAM recommended)
- **Python**: 3.10+ with PyTorch 2.5.1
- **FFmpeg**: With NVENC support for GPU encoding
- **Dependencies**: Fairseq (custom), Transformers 4.49.0, Mediapipe, Whisper, SentencePiece

## Environment Setup

The pipeline uses **3 separate Python virtual environments** for different components:

### 1. ASR & Preprocessing Environment

**Location**: `~/auto_avsr/pre-process-venv/`
**Purpose**: Whisper ASR, video preprocessing, face detection, mouth cropping

```bash
# Create environment
cd ~/auto_avsr
python3 -m venv pre-process-venv
source pre-process-venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install pytorch-lightning  # For AVSR training framework
pip install openai-whisper==20250625
pip install -r preparation/requirements.txt  # opencv, ffmpeg-python, sentencepiece, etc.

# Install mediapipe from wheel (required for face detection)
pip install mediapipe-0.10.9-cp311-cp311-linux_x86_64.whl
```

**Key Dependencies**:
- `torch` + `torchvision` + `torchaudio` - PyTorch with CUDA 12.1
- `pytorch-lightning` - Training framework
- `openai-whisper==20250625` - ASR transcription
- `mediapipe` - Face and mouth detection
- `opencv-python` - Video processing
- `ffmpeg-python` - Video manipulation
- `sentencepiece` - Text tokenization
- `tqdm` - Progress bars
- `scikit-image` - Image processing

See [`auto_avsr/preparation/requirements.txt`](auto_avsr/preparation/requirements.txt) for complete list.

### 2. VSP-LLM Environment

**Location**: `~/vsp-llm-yoad-venv/`
**Purpose**: LLaMA2 inference, AV-HuBERT features, K-means clustering, decoding

```bash
# Create environment
cd ~
python3 -m venv vsp-llm-yoad-venv
source vsp-llm-yoad-venv/bin/activate

# Install PyTorch with CUDA 12.1
pip install --upgrade pip
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install VSP-LLM requirements
cd ~/VSP-LLM
pip install -r requirements.txt

# Install Fairseq (editable mode)
cd ~/VSP-LLM/fairseq
pip install -e .

# Install AV-HuBERT Fairseq (editable mode)
cd ~/av_hubert/fairseq
pip install -e .

# Install clustering dependencies (for K-means)
pip install soundfile joblib sklearn submitit npy-append-array
```

**Key Dependencies** (from `requirements.txt`):
- `torch==2.5.1` - PyTorch with CUDA 12.1
- `transformers==4.49.0` - HuggingFace for LLaMA2
- `fairseq` - Sequence-to-sequence framework (custom install)
- `bitsandbytes==0.42.0` - 8-bit optimizers
- `Cython==3.0.8` - Fairseq compilation
- `datasets==2.17.0` - HuggingFace datasets
- `editdistance==0.6.0` - WER calculation
- `einops==0.7.0` - Tensor operations
- `hydra-core==1.0.7` - Configuration management
- `librosa==0.10.1` - Audio processing
- `numba==0.59.0` - JIT compilation
- `numpy==1.23.5` - Numerical computing
- `omegaconf==2.0.6` - Config management
- `opencv-python==4.5.4.60` - Video processing
- `pandas==2.2.0` - Data manipulation
- `peft` - Parameter-efficient fine-tuning
- `scikit-learn==1.4.0` - K-means clustering
- `scipy==1.10.0` - Scientific computing
- `sentencepiece==0.1.96` - Tokenization
- `sacrebleu==2.4.0` - BLEU score calculation
- `safetensors==0.4.2` - Model serialization
- Plus: `joblib`, `psutil`, `python-speech-features`, `tqdm`, `typing_extensions`

**Clustering Dependencies** (from `src/clustering/requirements.txt`):
- `soundfile` - Audio I/O
- `sklearn` - K-means implementation
- `submitit` - Cluster job submission
- `npy-append-array` - NumPy array appending

See [`VSP-LLM/requirements.txt`](VSP-LLM/requirements.txt) for complete list.

### 3. Web UI Environment

**Location**: `~/vsp-ui/venv/`
**Purpose**: Flask web interface, video validation, transcription management

```bash
# Create environment
cd ~/vsp-ui
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install flask
pip install opencv-python  # For video metadata
```

**Key Dependencies**:
- `flask` - Web framework
- `opencv-python` - Video validation

### Environment Activation

The pipeline automatically activates the correct environment for each stage:

```bash
# Manual activation examples
source ~/auto_avsr/pre-process-venv/bin/activate        # For ASR/preprocessing
source ~/vsp-llm-yoad-venv/bin/activate                 # For VSP-LLM
source ~/vsp-ui/venv/bin/activate                       # For web UI
```

### Verification

Test each environment:

```bash
# Test ASR environment
source ~/auto_avsr/pre-process-venv/bin/activate
python -c "import whisper; import cv2; import mediapipe; print('ASR env OK')"

# Test VSP-LLM environment
source ~/vsp-llm-yoad-venv/bin/activate
python -c "import torch; import transformers; import fairseq; print('VSP-LLM env OK')"

# Test UI environment
source ~/vsp-ui/venv/bin/activate
python -c "import flask; print('UI env OK')"
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive architecture, workflows, and troubleshooting (1800+ lines)
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Setup instructions for EC2 and containers
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures and validation

## Project Structure

```
├── run_flat_english_pipeline.sh    # Master orchestrator (393 lines)
├── lib/                             # Modular pipeline stages
│   ├── common.sh                    # Logging utilities
│   ├── asr.sh                       # Whisper ASR with transcription reuse
│   ├── decode.sh                    # VSP-LLM decode
│   └── outputs.sh                   # Reports + burned videos
├── auto_avsr/                       # AVSR framework + preprocessing
├── VSP-LLM/                         # LLaMA2-based VSP + AV-HuBERT
├── av_hubert/                       # AV-HuBERT utilities
├── vsp-ui/                          # Web interface
└── vsp_input/                       # User input directory
    └── .transcriptions/             # Unified transcription storage
```

## Version History

- **v1.0.0** (Feb 2026) - Production release with modular architecture
- **refactor-v1.0** - Modular pipeline refactoring (52% line reduction)
- **container-v1.1.0** - Linux container deployment version
- **ec2-v1.1** - EC2 version with segment-first normalization

## License

[Add your license here]

## Citation

If you use this pipeline in your research, please cite:

```bibtex
[Add citation information]
```

---

**Note**: This pipeline requires GPU resources and significant disk space. See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed setup instructions.
