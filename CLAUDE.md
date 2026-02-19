# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commit Rules

- **NEVER** include `Co-Authored-By` lines in commit messages. No Claude/AI attribution in commits.

## Working with Split Documentation

This CLAUDE.md is a slim hub file. Detailed documentation lives in separate files (see Documentation Map below). **Before starting any non-trivial task**, read the relevant doc file(s):

- **Modifying pipeline, UI, or container code** → read [docs/container-sync-changelog.md](docs/container-sync-changelog.md) first (has exact code diffs for all 26 pending sync items)
- **Working on pipeline stages, data formats, or segments** → read [docs/architecture.md](docs/architecture.md) first (segment naming, directory layout, data formats)
- **Running commands, debugging, or troubleshooting** → read [docs/development-guide.md](docs/development-guide.md) first
- **Fixing standalone container bugs** → read the relevant bugs file in `vsp_linux_container_FINAL_20260217/`
- **Training research, LoRA tuning, or fine-tuning strategy** → read [docs/training-research-notes.md](docs/training-research-notes.md) first
- **Planning future work or picking up a new mission** → read [docs/mission-backlog.md](docs/mission-backlog.md) first (Missions 4-14, prioritized with research references)

Do NOT rely on memory or guessing — always read the file to get exact details.

## Overview

This repository contains a visual speech processing (VSP) pipeline that combines three major components for lip-reading and visual speech recognition:

1. **auto_avsr/** - Audio-Visual Speech Recognition framework for preprocessing and training lip-reading models
2. **VSP-LLM/** - Visual Speech Processing with Large Language Models for inference and translation
3. **av_hubert/** - AV-HuBERT model preparation utilities for feature extraction and clustering

The main pipeline (`run_flat_english_pipeline.sh`) orchestrates these components to process raw videos through ASR transcription, mouth cropping, feature extraction, clustering, and LLM-based decoding.

## **Refactored Modular Architecture (January 2026)**

**Mission 1 Complete**: The pipeline has been refactored from a monolithic 823-line script into a modular architecture with reusable components.

### Modular Structure

All pipeline functionality is now organized into **11 modules** under the `lib/` directory:

```
lib/
├── common.sh              # Logging and validation utilities
├── config.sh              # Environment detection (EC2/container) and path configuration
├── archive.sh             # Archive management with transcription preservation
├── normalization.sh       # Video normalization (HDR/10-bit conversion, GPU encoding)
├── asr.sh                 # Whisper ASR with intelligent transcription management
├── lrs3_prep.sh           # LRS3 format conversion
├── manifests.sh           # Manifest and TSV generation
├── clustering.sh          # K-means clustering and cluster counts
├── decode.sh              # VSP-LLM decode
├── outputs.sh             # Client reports and burned videos
└── venv/
    └── venv_utils.sh      # Virtual environment management
```

### Benefits of Refactoring

- **52% Line Reduction**: Main pipeline: 823 → 393 lines
- **Reusability**: Each module can be used independently or in other scripts
- **Testability**: Comprehensive test suite (`lib/test_all_modules.sh`) with 37 tests
- **Maintainability**: Clear separation of concerns, easier debugging
- **Environment-Aware**: Automatic detection of EC2 vs Linux container environment
- **Consistent Error Handling**: Standardized logging and error reporting across all stages

### Module Responsibilities

**Phase 1.1: Infrastructure**
- `common.sh`: Logging (`log_info`, `log_error`, `log_stage`), validation (`validate_directory`)
- `config.sh`: Environment detection, path configuration, derived path functions
- `venv_utils.sh`: Virtual environment activation/deactivation with error handling

**Phase 1.2: Normalization**
- `normalization.sh`: Video normalization with HDR/10-bit tone mapping, GPU acceleration (NVENC), fallback to CPU encoding

**Phase 1.3: Archive**
- `archive.sh`: Archive previous run outputs with special handling to preserve segment transcriptions

**Phase 1.4: Processing Stages**
- `asr.sh`: Whisper ASR with intelligent transcription matching
  - Step 0.6: Copy existing transcriptions (exact + intelligent name matching)
  - Step 3: Run Whisper (skips segments with existing transcriptions)
  - Step 1.5: Save new auto-transcriptions for future reuse
- `lrs3_prep.sh`: Convert flat dataset to LRS3 format
- `manifests.sh`: Generate manifests, splits, TSVs, and segment timing metadata
- `clustering.sh`: K-means feature extraction and cluster count generation

**Phase 1.5: Decode & Outputs**
- `decode.sh`: VSP-LLM decode with symlink setup, merge logic (disabled for segment-level output)
  - **CRITICAL**: Includes automatic Cython extension check/build for fairseq
  - Container environments require this on first run due to different Python/CPU architecture
  - Checks if `fairseq.data.data_utils_fast` can be imported, builds if missing
  - This step must NEVER be removed - decode will fail without Cython extensions
- `outputs.sh`: Generate segment-level reports (JSON) and burned videos

### Virtual Environment Strategy

- **ASR module** (`asr.sh`): Self-contained, activates `ASR_VENV` internally
- **Other modules**: Expect caller to activate `VSP_VENV` (shared across stages 5-8 for efficiency)

This approach minimizes overhead by activating the VSP venv once for multiple stages.

### Transcription Reuse (Step 0.6 Enhancement)

The ASR module includes simple direct transcription matching:

**How it works**:
- Video segments matched 1:1 with transcription files by exact name
- Example: `video_00_000000_000300.mp4` → `video_00_000000_000300.wrd`
- Whisper automatically skips segments with existing `.wrd` files

**Benefit**: Users can manually transcribe specific segments, and those transcriptions persist across all pipeline runs in `.transcriptions/` directory. Whisper skips all matched segments, saving hours of processing time.

### Testing

Run the complete test suite:
```bash
bash /home/ubuntu/lib/test_all_modules.sh
```

All 37 tests validate module exports, functionality, and integration points.

### Git Tags

- `refactor-v1.0` - Modular pipeline refactoring complete (January 2026)
- `ec2-v1.1` - EC2 version with refactored modules
- `container-v1.1` - Linux container version (to be synced)

## **CRITICAL: EC2 and Linux Container Synchronization**

⚠️ **IMPORTANT REQUIREMENT**: This codebase exists in TWO environments:
1. **EC2 Instance** (`/home/ubuntu/`) - Development and testing environment
2. **Linux Container** (`/workspace/`) - Production deployment environment

**MANDATORY RULE**: Every change made to the EC2 version MUST be explicitly replicated to the Linux container version in a compatible way.

### Special Attention Required

**`run_flat_english_pipeline.sh`** - This is the master orchestrator script:
- **EC2 path**: `/home/ubuntu/run_flat_english_pipeline.sh`
- **Linux container path**: `/workspace/run_flat_english_pipeline.sh`
- Any modification to this file in EC2 MUST be carefully translated to the Linux container version
- Path differences must be accounted for:
  - EC2 uses `~/` paths (expands to `/home/ubuntu/`)
  - Linux container uses `/workspace/` paths
- Environment-specific adjustments may be needed for virtual environment activation paths

### Synchronization Checklist

When making changes, ALWAYS:
1. Make the change in EC2 first and test thoroughly
2. Identify all affected files (scripts, configs, Python code, UI files)
3. Translate EC2 paths to Linux container paths:
   - `~/auto_avsr/` → `/workspace/auto_avsr/`
   - `~/VSP-LLM/` → `/workspace/VSP-LLM/`
   - `~/vsp_input/` → `/workspace/vsp_input/`
   - Virtual environment paths (adjust as needed)
4. Update [docs/container-sync-changelog.md](docs/container-sync-changelog.md) with detailed instructions
5. Document the change with:
   - Date of change
   - Affected files in both environments
   - Specific line numbers or code blocks that changed
   - Any environment-specific considerations

### Common Files That Need Dual Updates

- **Pipeline Scripts**:
  - `run_flat_english_pipeline.sh` (MOST CRITICAL)
  - `VSP-LLM/scripts/run_flat_kmeans.sh`
  - `VSP-LLM/scripts/decode.sh`
  - `auto_avsr/preparation/make_preprocess_ready.sh`
  - `av_hubert/avhubert/preparation/flat_to_lrs3_preperation.sh`

- **VSP UI Components** (if changes affect UI):
  - `vsp-ui/app/server.py`
  - `vsp-ui/app/services/*.py`
  - `vsp-ui/app/static/*.html`, `*.js`, `*.css`

- **Configuration Files**:
  - Any Hydra configs in `VSP-LLM/src/conf/`
  - Python script arguments and paths

### Why This Matters

- The Linux container is the PRODUCTION environment used by end users
- Features tested in EC2 that don't make it to the container create inconsistent behavior
- Pipeline script changes are especially critical as they orchestrate the entire workflow
- Forgetting to sync can result in hours of debugging when deployed

**Bottom Line**: Treat every EC2 change as incomplete until it's documented and ready for Linux container deployment.

## Documentation Map

All documentation is organized under `docs/` with subdirectories for easy discovery:

### Core Documentation (docs/)

| Document | Contents |
|----------|----------|
| **This file (CLAUDE.md)** | Rules, overview, modular architecture, EC2/container sync rules |
| [docs/architecture.md](docs/architecture.md) | Pipeline flow, directory structure, segments, data formats, dependencies |
| [docs/development-guide.md](docs/development-guide.md) | Commands, virtual environments, workflows, testing, troubleshooting |
| [docs/container-sync-changelog.md](docs/container-sync-changelog.md) | Pending changes 1-26 for Linux container sync (full detail) |
| [docs/training-research-notes.md](docs/training-research-notes.md) | Training research: length distribution, LoRA rank, angle robustness, AVSpeech fine-tuning |
| [docs/mission-backlog.md](docs/mission-backlog.md) | Mission backlog: completed missions (1-3), prioritized future work (4-14), phased roadmap |
| [docs/cleanup-log.md](docs/cleanup-log.md) | Feb 2026 project reorganization: what was deleted, moved, and why |

### Deployment & Testing (docs/deployment/)

| Document | Contents |
|----------|----------|
| [INSTALLATION_GUIDE.md](docs/deployment/INSTALLATION_GUIDE.md) | Setup instructions |
| [TESTING_GUIDE.md](docs/deployment/TESTING_GUIDE.md) | Test suite and procedures |
| [EC2_TESTING_README.md](docs/deployment/EC2_TESTING_README.md) | EC2-specific testing |
| [CONTAINER_DEPLOYMENT_INSTRUCTIONS.md](docs/deployment/CONTAINER_DEPLOYMENT_INSTRUCTIONS.md) | Container deployment steps |
| [PRODUCTION_DEPLOYMENT_INSTRUCTIONS.md](docs/deployment/PRODUCTION_DEPLOYMENT_INSTRUCTIONS.md) | Production deployment |
| [CONTAINER_VALIDATION_CHECKLIST.md](docs/deployment/CONTAINER_VALIDATION_CHECKLIST.md) | Container validation |
| [TRANSFER_INSTRUCTIONS.md](docs/deployment/TRANSFER_INSTRUCTIONS.md) | File transfer procedures |

### Changelog & Fixes (docs/changelog/)

| Document | Contents |
|----------|----------|
| [COMPLETE_CHANGELOG.md](docs/changelog/COMPLETE_CHANGELOG.md) | Full historical changelog |
| [FIX_INVENTORY.md](docs/changelog/FIX_INVENTORY.md) | Comprehensive fix inventory |
| [MISSION3_MAX_LEN_FIX.md](docs/changelog/MISSION3_MAX_LEN_FIX.md) | Mission 3 max_len fix details |
| [SEGMENTED_VIDEO_NAMING_FIX.md](docs/changelog/SEGMENTED_VIDEO_NAMING_FIX.md) | Video naming fix |
| [PATH_CORRECTION_FIX.md](docs/changelog/PATH_CORRECTION_FIX.md) | Path correction fix |

### Research (docs/research/)

| Document | Contents |
|----------|----------|
| [VSP_LLM_paper.pdf](docs/research/VSP_LLM_paper.pdf) | VSP-LLM paper (Yeo et al., arXiv:2402.15151v2, May 2024) |
| [VSP_LLM_paper_text.txt](docs/research/VSP_LLM_paper_text.txt) | VSP-LLM paper full text |
| [Presentation_2025.pptx](docs/research/Presentation_2025.pptx) | 2025 Project presentation |

### Other docs/ subdirectories

| Directory | Contents |
|-----------|----------|
| `docs/sessions/` | Session summaries (FINAL_SUMMARY, SESSION_SUMMARY_20260202, TEST_RESULTS_SUMMARY) |
| `docs/licenses/` | All third-party license files (Python, Linux, NVIDIA, build-from-source) |
| `docs/branding/` | Logo files (PNG, SVG, JPEG) |

### Experimental Results

| Directory | Contents |
|-----------|----------|
| `english_1k_results/` | 1520 AVSpeech videos, decode reports, segment metadata |
| `english_full_results/` | 1497 segments, WER 64.1%, WWER 61.9%, full report suite |
| `tuning_results/` | 7 decode parameter experiments (beam, lenpen, sampling, greedy) |

### Standalone Container Bug Tracking

Located in `vsp_linux_container_FINAL_20260217/`:

| Document | Contents |
|----------|----------|
| [bugs-reference.md](vsp_linux_container_FINAL_20260217/bugs-reference.md) | Docker reference, lessons learned, package versions, spaCy install |
| [bugs-1-to-13-installation.md](vsp_linux_container_FINAL_20260217/bugs-1-to-13-installation.md) | Bugs 1-13: Installation & setup |
| [bugs-14-to-25-deployment.md](vsp_linux_container_FINAL_20260217/bugs-14-to-25-deployment.md) | Bugs 14-25: Deployment & GPU issues |
| [bugs-26-to-37-final.md](vsp_linux_container_FINAL_20260217/bugs-26-to-37-final.md) | Bugs 26-37: Final fixes (upload, terminal, inference, metrics) |

## Project Directory Structure

```
/home/ubuntu/
├── CLAUDE.md, README.md, requirements.txt     # Project root files
├── run_flat_english_pipeline.sh               # MAIN PIPELINE entry point
│
├── VSP-LLM/              # Core: Visual Speech + LLM model
├── auto_avsr/             # Core: Audio-Visual ASR preprocessing
├── av_hubert/             # Core: AV-HuBERT feature extraction
├── lib/                   # Core: 11 modular pipeline stages
├── vsp-ui/                # Core: Web UI
├── tests/                 # Core: Test suite
│
├── datasets/              # Data: Input video datasets
├── data/                  # Data: AVSpeech dataset
├── vsp_input/             # Data: Pipeline input (symlinks)
├── vsp_input_tuning/      # Data: Tuning input (symlinks)
├── flat/                  # Data: Intermediate flat format
├── outputs/               # Data: Current pipeline outputs
├── english_1k_results/    # Results: 1520-video experiment
├── english_full_results/  # Results: Full dataset baseline (WER 64.1%)
├── tuning_results/        # Results: Decode parameter experiments
│
├── face_alignment/        # Models: Face alignment (pipeline dependency)
├── face_detection/        # Models: Face detection (pipeline dependency)
├── golden_weights/        # Models: Clustering baseline weights
├── Llama-2-7b-hf/        # Models: LLM config files
│
├── argos_research/        # Research: R&D journal & analysis reports
├── docs/                  # Docs: ALL documentation (organized)
├── scripts/               # Scripts: Utility scripts (tests, monitoring, build)
├── logs/                  # Logs: Pipeline run logs
├── build_assets/          # Build: Wheel caches & build venvs
│
├── vsp_docker/            # Deploy: Docker build dir (galaxy_export/ working copy)
├── vsp_linux_container_FINAL_20260217/  # Deploy: Container code overlay
│
└── _archive/              # Archive: Old/borderline items (not actively used)
```
