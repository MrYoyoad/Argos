# Visual Speech Processing Pipeline

A lip-reading system that transcribes speech from video using mouth movements alone — no audio required.

Built on three research frameworks ([auto_avsr](https://github.com/mpc001/auto_avsr), [AV-HuBERT](https://github.com/facebookresearch/av_hubert), [VSP-LLM](https://github.com/Sally-SH/VSP-LLM)), unified into a single automated pipeline with a web interface.

## How It Works

```
Video → Segmentation → Normalization → Mouth Cropping → Whisper ASR
      → Feature Extraction (AV-HuBERT) → K-means Clustering
      → LLM Decode (LLaMA-2) → Reports & Burned Videos
```

Videos are split into short overlapping segments, the mouth region is detected and cropped, visual speech features are extracted and quantized, then a LLaMA-2 language model decodes the lip movements into text.

## Features

- **One-command pipeline** — from raw video to transcriptions, reports, and burned subtitle videos
- **Modular stages** — each of the 8 pipeline stages is an independent module under `lib/`, testable on its own
- **Transcription persistence** — manual corrections survive across runs; Whisper skips already-transcribed segments
- **Web interface** — upload videos, edit transcriptions, and monitor progress through a browser
- **Environment-aware** — auto-detects EC2 vs container deployment and adjusts paths accordingly
- **GPU accelerated** — CUDA-based inference and video processing throughout

## Quick Start

```bash
# Run the full pipeline
./run_flat_english_pipeline.sh /path/to/videos

# Or launch the web UI
cd vsp-ui && ./launcher.sh
```

## Requirements

- NVIDIA GPU with CUDA support (24GB+ VRAM recommended)
- Python 3.10+
- FFmpeg

For detailed environment setup and package installation, see **[INSTALL.md](INSTALL.md)**.

## Project Structure

```
├── run_flat_english_pipeline.sh   # Pipeline entry point
├── lib/                           # Modular pipeline stages
│   ├── common.sh                  #   Logging & validation
│   ├── config.sh                  #   Environment detection
│   ├── normalization.sh           #   Video normalization
│   ├── asr.sh                     #   Whisper ASR
│   ├── lrs3_prep.sh               #   LRS3 format conversion
│   ├── manifests.sh               #   Manifest generation
│   ├── clustering.sh              #   K-means clustering
│   ├── decode.sh                  #   VSP-LLM decode
│   └── outputs.sh                 #   Reports & burned videos
├── auto_avsr/                     # Preprocessing & ASR framework
├── VSP-LLM/                       # LLaMA-2 visual speech model
├── av_hubert/                     # AV-HuBERT feature extraction
├── vsp-ui/                        # Flask web interface
└── docs/                          # Documentation
```

## Presentation

[Research Findings and Production Roadmap (Google Slides)](https://docs.google.com/presentation/d/1UNZVtpcODsTOFolRgVyo4h6jKTx_6Y5u/edit?usp=sharing&ouid=113034242173553309203&rtpof=true&sd=true) — covers evaluation methodology, baseline results, engineering decisions, and future directions.

## Documentation

| Document | Description |
|----------|-------------|
| **[INSTALL.md](INSTALL.md)** | Environment setup, dependencies, verification |
| [Architecture](docs/architecture.md) | Pipeline flow, data formats, directory layout |
| [Development Guide](docs/development-guide.md) | Commands, debugging, troubleshooting |
| [Testing Guide](TESTING_GUIDE.md) | Test procedures and validation |

## Acknowledgements

This pipeline builds on the following research:

- **VSP-LLM** — Visual Speech Processing with Large Language Models ([paper](https://arxiv.org/abs/2402.15151))
- **AV-HuBERT** — Audio-Visual Hidden Unit BERT ([paper](https://arxiv.org/abs/2201.02184))
- **auto_avsr** — Audio-Visual Speech Recognition framework

## License

[Add your license here]
