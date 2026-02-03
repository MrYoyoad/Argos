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
