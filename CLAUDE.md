# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Always Do After Analysis

- After completing any research, analysis, or investigation, **always** update all relevant files (docs, summaries, JSON data, markdown) with findings — keep updates succinct and factual.
- After making significant or multi-file changes, **always** git commit with a clear message describing what changed and why.

## Presentation Slide Remarks

- When the user gives feedback, remarks, or requests about presentation slides, **always** log the remark in [docs/paper/presentation-remarks-log.md](docs/paper/presentation-remarks-log.md) in addition to executing the requested changes. This ensures no prior request gets lost.

## Git Commit Rules

- **NEVER** include `Co-Authored-By` lines in commit messages. No Claude/AI attribution in commits.

## File Placement Rules

When creating or moving files, **always** place them in the correct directory based on content type:

| Content Type | Destination | Examples |
|-------------|-------------|----------|
| **Experiment results** (decode runs, configs, reports) | `docs/tuning/experiments/` | New exp_N directories |
| **Experiment HTML reports** | `docs/tuning/html-reports/` | Copy report.html as exp_N.html |
| **Evaluation / baseline analysis** | `docs/evaluation/` | WER analysis, quality assessments |
| **Hyperparameter / metrics docs** | `docs/tuning/` | Metrics explainers, tuning summaries |
| **Confidence scoring research** | `docs/confidence/` | Mission 4 work |
| **Beam search / N-best research** | `docs/beam-search/` | Mission 6 work |
| **Prompt engineering research** | `docs/prompts/` | Mission 8 work |
| **Fine-tuning / training research** | `docs/finetuning/` | Mission 9 work, training notes |
| **Academic papers / presentations** | `docs/paper/` | References |
| **Installation / deployment / testing guides** | `docs/guides/` | How-to docs |
| **Feature documentation** | `docs/features/` | New feature specs |
| **Bug fixes / version history** | `docs/changelog/` | Fix docs, changelogs |
| **Roadmap / planning / mission tracking** | `docs/backlog/` | Mission plans, cleanup logs |
| **Report generators / Python scripts for reports** | `docs/_research-tools/generators/` | generate_*.py |
| **Experiment runner scripts** | `docs/_research-tools/scripts/` | run_*.sh for research |
| **Logos / branding images** | `docs/branding/` | PNG, SVG, JPEG logos |
| **License files** | `docs/licenses/` | Third-party licenses |
| **Utility scripts (tests, monitoring, build)** | `scripts/{tests,monitoring,build,pipeline}/` | Non-research scripts |
| **Pipeline run logs** | `logs/` | *.log files |

**Key principle**: Each research topic folder maps to a backlog mission. When a mission produces new work, it goes in that topic's folder. When in doubt, check `docs/backlog/mission-backlog.md` for the mission-to-folder mapping.

## Working with Split Documentation

This CLAUDE.md is a slim hub file. Detailed documentation lives in separate files (see Documentation Map below). **Before starting any non-trivial task**, read the relevant doc file(s):

- **Modifying pipeline, UI, or container code** → read [docs/container-sync-changelog.md](docs/container-sync-changelog.md) first (has exact code diffs for all 26 pending sync items)
- **Working on pipeline stages, data formats, or segments** → read [docs/architecture.md](docs/architecture.md) first (segment naming, directory layout, data formats)
- **Running commands, debugging, or troubleshooting** → read [docs/development-guide.md](docs/development-guide.md) first
- **Fixing standalone container bugs** → read the relevant bugs file in `vsp_linux_container_FINAL_20260217/`
- **Training research, LoRA tuning, or fine-tuning strategy** → read [docs/finetuning/training-research-notes.md](docs/finetuning/training-research-notes.md) first
- **Planning future work or picking up a new mission** → read [docs/backlog/mission-backlog.md](docs/backlog/mission-backlog.md) first (Missions 4-14, prioritized with research references)
- **Writing or modifying a docx report generator** → read [docs/_research-tools/generators/STYLE_GUIDE.md](docs/_research-tools/generators/STYLE_GUIDE.md) first (header layout, cover page, TOC, page breaks, logo paths)
- **Working on evaluation, metrics, or intelligibility scoring** → read [docs/evaluation/intelligibility_methodology.md](docs/evaluation/intelligibility_methodology.md) and [docs/evaluation/intelligibility/intelligibility_summary.json](docs/evaluation/intelligibility/intelligibility_summary.json) first

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
├── outputs.sh             # Client reports and burned videos (+ IS scoring on EC2 only)
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
- `outputs.sh`: Generate segment-level reports (CSV/HTML/TXT) and burned videos. **EC2 only**: computes Intelligibility Scores (IS) per segment via `--compute-is` flag (requires sentence-transformers, metaphone). Container version skips IS — this is an intentional version difference, not a sync gap.

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

### Core References (docs/ top level)

| Document | Contents |
|----------|----------|
| **This file (CLAUDE.md)** | Rules, overview, modular architecture, EC2/container sync rules |
| [docs/architecture.md](docs/architecture.md) | Pipeline flow, directory structure, segments, data formats, dependencies |
| [docs/development-guide.md](docs/development-guide.md) | Commands, virtual environments, workflows, testing, troubleshooting |
| [docs/container-sync-changelog.md](docs/container-sync-changelog.md) | Pending changes 1-26 for Linux container sync (full detail) |

### Research by Topic (one folder per research area, maps to backlog missions)

| Folder | Contents | Backlog Mission |
|--------|----------|-----------------|
| [docs/evaluation/](docs/evaluation/) | Report 1 (executive assessment), R&D journal, project summary, intelligibility methodology & scores (IS 2.52/5.0), IS correlation analysis + [cross-config validation](docs/evaluation/is_cross_config_validation.md), [extended analysis](docs/evaluation/intelligibility_extended_analysis.md), [LLM salvage](docs/evaluation/llm_salvage/) (165 recoverable segments + [example gallery](docs/evaluation/llm_salvage/salvage_example_gallery.md)), [LLM-as-a-Judge](docs/evaluation/llm_judge/) gold standard (1,497 pairs, Y/P/N + [context eval](docs/evaluation/llm_judge/context_eval/)) | M5: Expanded Metrics |
| [docs/tuning/](docs/tuning/) | Report 2 (hyperparameter tuning), metrics explainer, 13 experiments, HTML reports | M7: Hyperparams, M14: Auto-tuning |
| [docs/confidence/](docs/confidence/) | Report 4 (confidence scoring & quality filtering) | M4: Confidence Scoring |
| [docs/beam-search/](docs/beam-search/) | Report 5 (N-best hypothesis aggregation, ROVER, MBR) | M6: Beam Aggregation |
| [docs/prompts/](docs/prompts/) | Report 3 (prompt engineering & context injection) | M8: Prompt Engineering |
| [docs/finetuning/](docs/finetuning/) | Report 6 (fine-tuning analysis), training research notes | M9: AVSpeech Fine-Tuning |
| [docs/paper/](docs/paper/) | VSP-LLM paper (PDF + text), 2025 Presentation, [Beamer presentation](docs/paper/beamer-presentation/) (75 slides, 5 sections + appendix) | — |

### Operations

| Folder | Contents |
|--------|----------|
| [docs/guides/](docs/guides/) | Installation, deployment, testing, container validation, transfer instructions, [container update guide](docs/guides/container-update-feb2026.md) |
| [docs/features/](docs/features/) | Feature documentation (golden k-means, transcription, segmentation, etc.) |
| [docs/changelog/](docs/changelog/) | Fix history (complete changelog, fix inventory, individual fix docs) |
| [docs/backlog/](docs/backlog/) | Mission backlog (roadmap, Missions 1-14), cleanup log |

### Other

| Folder | Contents |
|--------|----------|
| `docs/sessions/` | Session summaries |
| `docs/licenses/` | Third-party license files |
| `docs/branding/` | Logo files |
| `docs/_research-tools/` | Report generators (Python: `generate_*.py` for docx, journal, presentation, plots, pipeline diagram, finetune plots), experiment scripts, datasets, assets, [STYLE_GUIDE.md](docs/_research-tools/generators/STYLE_GUIDE.md) (docx + PPTX + Beamer + plot conventions) |

### Experimental Results (root level)

| Directory | Contents |
|-----------|----------|
| `english_full_results/` | 1497 segments, WER 64.1%, WWER 61.9%, IS 2.52/5.0, full report suite |
| `tuning_results/` | 13 decode parameter experiments (beam, lenpen, sampling, greedy) |

### Baseline Evaluation Results (February 2026)

**Full dataset baseline** run on 1,497 segments from diverse YouTube videos (Feb 18, 2026):

| Metric | Value | Notes |
|--------|-------|-------|
| **Mean WER** | 64.1% | Segment-level; 2.5x worse than paper's 25.4% on LRS3 |
| **Mean WWER** | 61.9% | Weighted WER — high-value tokens penalized 2x |
| **Named Entity F1** | 38.9% | Entities missed in 85% of segments |
| **Intelligibility Score** | 2.52/5.0 | Composite metric (semantic, phonetic, WER, WWER, NEA, length) |
| **Properly Captured (IS ≥ 3)** | 597/1,497 (39.9%) | Only 4 in 10 segments convey intelligible meaning |
| **Hallucinated (WER ≥ 100%)** | 307/1,497 (20.5%) | Fluent but fabricated text — most dangerous failure mode |

**Intelligibility Score (IS) Tier Distribution:**

| Tier | Score | Count | % |
|------|-------|-------|-----|
| 5 — Excellent | 4.0-5.0 | 276 | 18.4% |
| 4 — Good | 3.0-3.99 | 321 | 21.4% |
| 3 — Fair | 2.0-2.99 | 325 | 21.7% |
| 2 — Poor | 1.0-1.99 | 336 | 22.4% |
| 1 — Failed | 0.0-0.99 | 239 | 16.0% |

**IS Component Correlation Analysis** (March 2026): The 6 IS signals collapse into 3 independent dimensions — word accuracy (WER/WWER/Phonetic, r > 0.79 with each other, ~60% of IS weight), meaning preservation (Semantic, 28.5% of variance), and output sanity (Length Ratio, 9.1% of variance). The IS framework uses a **design-time LLM-distilled** approach: Claude (Anthropic) designed the rubric, selected the 6 signals and weights, defined tier boundaries, and built the `llm_context_prob` decision tree — all at design time. **No LLM is called at evaluation time.** The resulting metrics are fully deterministic, free, and reproducible. The `llm_context_prob` heuristic (a 15-rule decision tree, not an LLM API call) correlates at r=0.93 with IS (88.6% agreement with IS ≥ 3.0, Cohen's κ = 0.773). Cross-config stability validated across 16 decode configurations: mean r=0.925 (std=0.015), κ range 0.62–0.86, recall 97.6–100%. Full analysis: [docs/evaluation/is_correlation_analysis.md](docs/evaluation/is_correlation_analysis.md).

**LLM Salvage Analysis** (March 2026): 165 of 900 metric-failed segments (18.3%) have meaning that the Claude-designed `llm_context_prob` heuristic (a deterministic decision tree — no runtime LLM calls) identifies as recoverable (llm_context_prob ≥ 0.5, IS < 3.0). Including these, the effective capture rate rises from 39.9% to **50.9%** — roughly 1 in 2 segments delivers useful output rather than 2 in 5. Segments categorized into 6 recovery types: hidden gems (54), semantic preservation (57), phonetic bridge (93), entity-preserved (44), structure match (74), WER over-punishment (27). Full analysis with curated examples: [docs/evaluation/llm_salvage/llm_salvage_analysis.md](docs/evaluation/llm_salvage/llm_salvage_analysis.md).

**LLM-as-a-Judge Gold Standard** (March 2026): Claude Opus 4.6 evaluated all 1,497 pairs using holistic LLM reasoning (blind, 3-level Y/P/N). Results: Y=345 (23.0%), P=626 (41.8%), N=526 (35.1%). Intra-rater reliability: 86.7% exact (30 duplicates). The LLM judge is more conservative for "full success" (23% vs IS 40%) but more generous for "any useful output" (Y+P=65%). Structure is preserved in 88.8% of partial cases; detail and semantic meaning are lost most often (~55% each). Visual/topic context analysis: ~284 segments (19%) show domain vocabulary confusion where a topic label at decode time would help. DIY/Home has the highest N-rate (51.9%) due to inherently visual content. **Context-aware re-evaluation** (March 2026, all 1,497 pairs, judge infers topic from reference text): Y drops to 15.0% (−8pp), P rises to 47.1% (+5.3pp), N rises to 37.9% (+2.8pp). Y+P = 62.1% (−2.7pp vs blind 64.9%). Context is STRICTER not lenient — 230 downgrades vs 68 upgrades, dominant transition Y→P (138 cases, domain knowledge reveals vocabulary failures). Only 1 N→Y rescue across all pairs. Full analysis: [docs/evaluation/llm_judge/llm_judge_analysis.md](docs/evaluation/llm_judge/llm_judge_analysis.md), [docs/evaluation/llm_judge/context_eval/context_eval_analysis.md](docs/evaluation/llm_judge/context_eval/context_eval_analysis.md).

**Hyperparameter tuning** (13 experiments on 107 segments): Baseline config (beam=20, lenpen=0, no sampling) proved most robust. No parameter combination improved WER meaningfully. See [docs/tuning/experiment-comparison.csv](docs/tuning/experiment-comparison.csv).

**Fine-tuning experiments** (March 2026): Exp A (r=16) and Exp B (r=64) on 1,273 AVSpeech segments both showed severe overfitting (~95% train, ~60% val accuracy). r=64 was 3.1pp worse than r=16. Claude-as-Judge evaluation (224 val segments): Baseline IS=2.487, Exp A IS=2.312, Exp B IS=2.023; empty outputs 7.1%/12.5%/26.8%; LLM Y+P ~51-54% all three (no improvement from fine-tuning). These results were **data-limited** — 1,273 segments is below the ~1K minimum for LoRA generalization. The experiments tested the dataset's limits, not the model's capacity. With 20K-50K segments and a stronger LLM (e.g., Llama 3.1 8B), substantially better results are expected. See [docs/finetuning/training-research-notes.md](docs/finetuning/training-research-notes.md) and [docs/evaluation/llm_upgrade_analysis.md](docs/evaluation/llm_upgrade_analysis.md).

**Key takeaway**: Domain adaptation requires three things: (1) sufficient training data (20K+ segments, not 1.3K), (2) a stronger LLM backbone, and (3) eventually visual encoder adaptation. Decode parameter tuning has reached diminishing returns.

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
├── english_full_results/  # Results: Full dataset baseline (WER 64.1%)
├── tuning_results/        # Results: Decode parameter experiments
│
├── face_alignment/        # Models: Face alignment (pipeline dependency)
├── face_detection/        # Models: Face detection (pipeline dependency)
├── golden_weights/        # Models: Clustering baseline weights
├── Llama-2-7b-hf/        # Models: LLM config files
│
├── docs/                  # Docs: ALL documentation (organized by topic)
├── scripts/               # Scripts: Utility scripts (tests, monitoring, build)
├── logs/                  # Logs: Pipeline run logs
├── build_assets/          # Build: Wheel caches & build venvs
│
├── presentation_materials_20260224/  # Presentations: PPTX (~47 slides) + plots + poster frames
├── vsp_docker/            # Deploy: Docker build dir (galaxy_export/ working copy)
├── vsp_linux_container_FINAL_20260217/  # Deploy: Container code overlay
│
└── _archive/              # Archive: Old/borderline items (not actively used)
```
