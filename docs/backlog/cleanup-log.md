# Project Cleanup Log

**Date**: 2026-02-19
**Reason**: Root directory had ~201 items — old repos, build artifacts, scattered docs, temp files, duplicate containers mixed with active pipeline code. Reorganized for clarity and reclaimed ~318 GB of disk space.

---

## Summary

| Action | Count | Disk Space |
|--------|-------|-----------|
| **Deleted** | ~100 files/dirs | ~318 GB freed |
| **Moved to _archive/** | 3 dirs | ~12.1 GB |
| **Moved to build_assets/** | 23 dirs/files | ~33 GB |
| **Moved to docs/ subdirs** | 21 files | ~15 MB |
| **Moved to scripts/ subdirs** | 15 scripts | ~100 KB |
| **Moved to logs/** | 13 log files | ~25 MB |

**Before**: 201 root items, 816 GB used, 154 GB free
**After**: ~30 root items, 499 GB used, 471 GB free

---

## Deleted Items

### Large Directories

| Item | Size | Reason |
|------|------|--------|
| `VSP-LLM_old/` | 176 GB | Old repo (Sept 2025), different git remote (leibovit/Argos), 5 months behind current VSP-LLM/. All checkpoints and code exist in current version. |
| `galaxy_export/` (root) | 64 GB | Outdated extracted container copy (Nov 2025). Active working copy is at `vsp_docker/galaxy_export/` (Feb 2026). |
| `vsp_docker/galaxy_export_20260201.tar.gz` | 44 GB | Outdated tarball (Feb 1). Working copy at `vsp_docker/galaxy_export/` has Feb 17 updates. |
| `VSP-LLMoutputs/` | 7.7 GB | Old raw decode outputs. Final results saved in `english_full_results/`. |
| `old_fix_packages_pre_FINAL/` | 2.2 GB | Superseded container build packages. Final version is `vsp_linux_container_FINAL_20260217/`. |
| `face_detection_broken_lfs_OLD/` | 170 MB | Broken Git LFS face detection models. Working versions at `face_detection/` and `face_alignment/`. |
| `home/` | 44 MB | Accidental home directory snapshot. Not part of pipeline. |
| `nZLO2PnGzMg/` | 46 MB | One-off YouTube video test download (8 videos). Not part of any dataset. |
| `vsp-ui-ec2/` | 256 KB | Duplicate UI copy. Canonical version at `vsp-ui/`. |
| `vsp-ui-linux/` | 240 KB | Duplicate UI copy. Canonical version at `vsp-ui/`. |
| `rebuilt_flat_556/` | 67 MB | Obsolete test segments from Aug 2025. |
| `sunshine.zip` | 35 MB | Related to archived Sunshine fork. Fork kept in `_archive/`. |

### Old Container Archives

| Item | Size | Reason |
|------|------|--------|
| `vsp_linux_container_FINAL_20260203.tar.gz` | 1.8 MB | Superseded by FINAL_20260217 |
| `vsp_linux_container_FINAL_20260208.tar.gz` | 2.0 MB | Superseded by FINAL_20260217 |
| `vsp_linux_container_FINAL_20260212.tar.gz` | 2.3 MB | Superseded by FINAL_20260217 |
| `vsp_linux_container_FINAL_20260215.tar.gz` | 2.4 MB | Superseded by FINAL_20260217 |
| `vsp_linux_container_FINAL_2026020{3,8,12,15}.sha256` | <1 KB each | Checksums for deleted archives |
| `linux_container_ready.tar.gz` | 88 MB | Old base container (pre-FINAL) |
| `linux_container_ready_20260201.tar.gz` | 2.1 GB | Old base container |
| `linux_container_segment_duration_update.tar.gz` | ~1 MB | Old incremental patch |
| `galaxy_export_*.tar.gz` (~18 files) | <200 KB each | Old incremental fix patches (Feb 1-2), all superseded |

### Temp, PID, and Junk Files

| Item | Size | Reason |
|------|------|--------|
| `pipeline_english_1k.pid` | 8 B | Stale PID (process not running) |
| `pipeline_full_rerun.pid` | 8 B | Stale PID |
| `pipeline_tuning_100.pid` | 8 B | Stale PID |
| `tuning_experiments.pid` | 8 B | Stale PID |
| `temp.txt` | 2 KB | Old venv package list |
| `temp_venv_2.txt` | 2.1 KB | Old venv package list |
| `00011.txt` | 884 B | Sample ASR output (test data) |
| `NVIDIA-Linux-x86_64-535.183.01.run` | 326 MB | Old GPU driver installer |
| `cuda-keyring_1.1-1_all.deb` | 4.3 KB | Old CUDA keyring package |
| `cuda-keyring_1.1-1_all.deb.1` | 4.3 KB | Duplicate |
| `DOWNLOAD_THESE_FILES.txt` | ~1 KB | Outdated, referenced old container (20260203) |
| `[16:23:00] INFO:...` (2 dirs) | ~0 | Malformed dirs from logging bug |
| `vsp-ui/[13:51:30]...` (8 dirs) | ~0 | Malformed dirs in vsp-ui from logging bug |

### Old Log Files (Nov 2025 - Jan 2026)

| Item | Reason |
|------|--------|
| `flat_english_test.log` | Nov 2025 test run |
| `flat_english_test_2.log` | Nov 2025 test run |
| `pipeline_1396.log` | Nov 2025 pipeline run |
| `pipeline_1396_rerun.log` | Dec 2025 rerun |
| `flat_runs_latest.log` | Jan 2026 flat runs |
| `crop.log` | Nov 2025 failed crop test |

### flat_runs_archive/ — Trimmed

173 of 183 timestamped pipeline run directories deleted (Nov 2025 - Feb 2026).
Latest 10 runs preserved and moved to `_archive/flat_runs_archive/`.

---

## Moved to `_archive/`

| Item | Size | Reason |
|------|------|--------|
| `Sunshine-feat-model_training_omer/` | 51 MB | External model training fork (Apr 2025). Not part of current pipeline but kept for reference. |
| `project/` | 12 GB | Completely separate project (municipal gap analysis in Hebrew, Jun-Jul 2025). Not related to VSP. |
| `flat_runs_archive/` (10 latest runs) | ~2 GB | Historical pipeline run outputs. Trimmed from 183 to 10 most recent. |

---

## Moved to `build_assets/`

### Wheels (`build_assets/wheels/`)

| Item | Size | Notes |
|------|------|-------|
| `wheels_py311/` | 5.1 GB | Python 3.11 wheel cache |
| `wheels_py311_fresh.tar.gz` | 5.1 GB | Compressed archive |
| `torch_gpu_wheels/` | 2.6 GB | PyTorch GPU wheels |
| `torch_gpu_wheels_cu121.tar.gz` | 2.6 GB | Compressed archive |
| `torch_gpu_wheels_cu121_py311/` | 2.5 GB | PyTorch CUDA 12.1 / Py 3.11 |
| `torch_gpu_wheels_cu121_py311.tar.gz` | 2.5 GB | Compressed archive |
| `mediapipe_wheels/` | 261 MB | MediaPipe wheels |
| `mediapipe_wheels.tar.gz` | 257 MB | Compressed archive |
| `mediapipe_wheels_310/` | 430 MB | MediaPipe Py 3.10 wheels |
| `mediapipe_wheels_310.tar.gz` | 459 MB | Compressed archive |
| `whisper_dep_wheels_cp311/` | 65 MB | Whisper dependency wheels |
| `whisper_dep_wheels_cp311.tar.gz` | 64 MB | Compressed archive |
| `numpy126_cp311/` | 18 MB | NumPy 1.26 wheels |
| `numpy126_cp311.tar.gz` | ~18 MB | Compressed archive |
| `tiktoken/` | 820 KB | Tiktoken tokenizer cache |

### Build Venvs (`build_assets/venvs/`)

| Item | Size | Notes |
|------|------|-------|
| `mediapipe_wheel_env/` | 480 MB | MediaPipe build environment |
| `mediapipe_wheel_env310/` | 17 MB | MediaPipe Py 3.10 build env |
| `torch_gpu_wheels_env/` | 13 MB | PyTorch wheel build env |
| `whisper_dep_build_venv/` | 25 MB | Whisper deps build env |
| `whisper_cache_env/` | 7.0 GB | Whisper model cache env |
| `tiktoken-build-venv/` | 47 MB | Tiktoken build env |

---

## Moved to `docs/` Subdirectories

### docs/deployment/
- `CONTAINER_DEPLOYMENT_INSTRUCTIONS.md`
- `PRODUCTION_DEPLOYMENT_INSTRUCTIONS.md`
- `CONTAINER_VALIDATION_CHECKLIST.md`
- `LINUX_DEPLOYMENT_READY.md`
- `INSTALLATION_GUIDE.md` (git mv — tracked)
- `EC2_TESTING_README.md`
- `TESTING_GUIDE.md` (git mv — tracked)
- `TRANSFER_INSTRUCTIONS.md`

### docs/changelog/
- `COMPLETE_CHANGELOG.md` (git mv — tracked)
- `FIX_INVENTORY.md` (git mv — tracked)
- `MISSION3_MAX_LEN_FIX.md`
- `SEGMENTED_VIDEO_NAMING_FIX.md`
- `PATH_CORRECTION_FIX.md` (git mv — tracked)

### docs/sessions/
- `FINAL_SUMMARY.md`
- `SESSION_SUMMARY_20260202.md`
- `TEST_RESULTS_SUMMARY.md`

### docs/research/
- `VSP_LLM_paper.pdf`
- `VSP_LLM_paper_text.txt`
- `Presentation_2025.pptx`

### docs/licenses/
- `BUILD_FROM_SOURCE_PACKAGES_LICENCES`
- `PYTHON_PACKAGES_LICENSES`
- `LINUX_PACKAGES_LICENSES`
- `LINUX_PACKAGES_LIST`
- `THIRD_PARTY_SOURCE_CODE_URLS`
- `OSSNvidiaDriver_v570.133.20_license.txt`

### docs/branding/
- `BlackLogo300x300-W-BG (1).png` → `BlackLogo300x300-W-BG.png`
- `LogoSVG (1).svg` → `LogoSVG.svg`
- `OIG1 (1).JPEG` → `OIG1.JPEG`

---

## Moved to `scripts/` Subdirectories

### scripts/tests/
- `test_ec2_environment.sh`
- `test_pipeline_modules.sh`
- `test_pipeline_smoke.sh`
- `test_segment_normalization.sh`
- `run_all_ec2_tests.sh`

### scripts/monitoring/
- `monitor_pipeline.sh`
- `monitor_tuning.sh`
- `watch_and_analyze.sh`
- `watch_full_rerun.sh`

### scripts/build/
- `build_container.sh`
- `verify_container_sync.sh`
- `check_container_inventory.sh`
- `push_tags.sh`
- `download_torch_cu121_cp311.sh`

### scripts/pipeline/
- `resume_pipeline.sh`

---

## Moved to `logs/`

13 recent (Feb 2026) log files moved from root to `logs/`:
- `tuning_experiments.log`, `pipeline_full_rerun.log`, `pipeline_english_1k_*.log`, `burn_english_1k.log`, `pipeline_tuning_100.log`, `pipeline_monitor.log`, `tuning_monitor.log`, `watch_full_rerun.log`, `watcher.log`, `post_decode_watcher.log`, `test_output.log`

Note: `full_decode_J.log` left at root during cleanup (active decode job in progress).

---

## Round 2 — Additional Items (same date)

### Deleted (Round 2)

| Item | Size | Reason |
|------|------|--------|
| `decode_cython_fix_20260202.tar.gz` | 1.4 KB | Already applied to codebase |
| `max_len_fix_20260202.tar.gz` | 510 B | Already applied |
| `transcription_path_fix_20260202.tar.gz` | 6.6 KB | Already applied |
| `ui_import_fix_20260202.tar.gz` | 2.5 KB | Already applied |
| `ui_transcription_fix_20260202.tar.gz` | 4.3 KB | Already applied |
| `run_flat_english_pipeline.sh.backup` | 14 KB | Old monolithic version (in git history) |
| `run_flat_english_pipeline.sh.bak.20260118_151835` | 5.7 KB | Old version (in git history) |
| `run_flat_english_pipeline.sh.bak2.20260118_152218` | 5.7 KB | Old version (in git history) |
| `make_report_color_fix.patch` | 1.8 KB | Already applied |
| `max_len_config_fix.patch` | 170 B | Already applied |
| `llama_download.py` | ~1 KB | One-time use + plaintext HF token (security risk) |
| `venv/` | 500 MB | Old venv, superseded by vsp-llm-yoad-venv/ |
| `docker_images/` | 230 MB | Old CUDA base image (can re-pull from Docker Hub) |
| `english_1000_subset_hrz.tar.gz` | 375 MB | Old dataset archive |
| `arabic_pre/` | 8 KB | Empty directory |
| `failed_face_detection_sample/` | 35 MB | Debug artifact (30 failed videos) |
| `galaxy_export_light/` | 20 KB | Lightweight export marker |
| `path_audit/` | 68 KB | Outdated script backups (Dec 2025) |
| `vsp_input_test/` | 272 KB | Single test video artifact |
| `snap/` | 816 KB | System snap packages |
| `english_1k/` | 25 MB | Old test dataset structure |
| `pipeline_english_1k.logpath` | <1 KB | Stale log reference |
| `tuning_100_list.txt` | ~5 KB | Old tuning file list |
| `to_download/` | 69 MB | Old download staging (Jul 2025), superseded |
| Remaining malformed bracket dirs | ~0 | Logging bug artifacts |

Note: `run_flat_english_pipeline.sh.original` kept at root as pre-refactoring reference.

### Moved (Round 2)

| Item | From | To | Reason |
|------|------|-----|--------|
| `lrs3orig_sync.tar` | root | `datasets/` | LRS3 dataset archive |
| `arabic_sample.tar.gz` | root | `datasets/` | Arabic test data |
| `arch_nvidia_container_pkgs.tar.gz` | root | `build_assets/` | NVIDIA package backup |
| `arch_pkgcache/` | root | `build_assets/` | System package cache |
| `sync/` contents | root | `scripts/build/` | Container sync tools (path_translator.py, sync_to_container.sh, validate_sync.sh, deployment_checklist.md) |

---

## Round 3 — Dotfile Cleanup (same date)

### Deleted (Round 3)

| Item | Size | Reason |
|------|------|--------|
| `.git-backup/` | 2.7 GB | Redundant git repo backup (Jan 29). Same commits as main `.git/`. |
| `.git-old-backup/` | 1.4 GB | Older redundant git repo backup (Jan 29). Same commits as main `.git/`. |
| `.dotnet/` | 236 KB | .NET runtime cache. Not used by this project. |
| `.claude.json.backup` | 2.7 KB | Old Claude Code config backup. Current `.claude.json` is active. |

### Updated `.gitignore` (Round 3)

Added exclusions for all system/user dotfiles so they no longer appear in VS Code source control:

`.bash_logout`, `.bashrc`, `.profile`, `.claude.json`, `.copilot/`, `.dotnet/`, `.git-credentials`, `.gitconfig`, `.ipython/`, `.jupyter/`, `.nv/`, `.sudo_as_admin_successful`, `.uniface/`, `.viminfo`, `.vscode-server/`, `.vsp-ui.log`, `.vsp-ui.pid`

These are system configuration files essential for the EC2 environment but not part of the project codebase.

### Not Deleted (System-Essential)

| Item | Size | Reason Kept |
|------|------|-------------|
| `.cache/` | 86 GB | Contains HuggingFace models (50 GB), pip cache (27 GB), Whisper models (4.3 GB) — needed by pipeline |
| `.vscode-server/` | 2.8 GB | VS Code remote development server — needed for current IDE |
| `.ssh/` | — | SSH keys — essential for EC2 access |
| `.bashrc`, `.profile` | — | Shell configuration — essential for environment |
| `.gitconfig`, `.git-credentials` | — | Git configuration — essential for repo operations |
| `.claude/`, `.claude.json` | — | Claude Code configuration — active tool |

---

## Round 4 — Docs Reorganization by Research Topic (same date)

Restructured `docs/` from generic categories into topic-based folders that map to backlog missions.

### New Topic Folders

| Folder | Contains | Maps to Mission |
|--------|----------|-----------------|
| `evaluation/` | Report 1, R&D journal, project summary | M5: Expanded Metrics |
| `tuning/` | Report 2, metrics explainer, 13 experiments, HTML reports | M7, M14: Hyperparams |
| `confidence/` | Report 4 (confidence scoring) | M4: Confidence Scoring |
| `beam-search/` | Report 5 (N-best aggregation) | M6: Beam Aggregation |
| `prompts/` | Report 3 (prompt engineering) | M8: Prompts |
| `finetuning/` | Report 6, training research notes | M9: Fine-Tuning |
| `paper/` | VSP-LLM paper + presentation | — |
| `guides/` | All deployment/installation/testing guides (was `deployment/`) | — |
| `backlog/` | Mission backlog + cleanup log | — |
| `_research-tools/` | Report generators, scripts, data, assets | — |

### Renamed Files (for clarity)

| Old Name | New Name |
|----------|----------|
| `research_documentation.docx` | `research-journal.docx` |
| `project_summary.docx` | `project-summary.docx` |
| `metrics_explainer.docx` | `metrics-explainer.docx` |
| `tuning_experiments.docx` | `tuning-experiments.docx` |
| `pairwise_comparison_report.pdf` | `pairwise-comparison.pdf` |
| `comparison.csv` | `experiment-comparison.csv` |

### Removed Directories

| Old Directory | Replaced By |
|---------------|-------------|
| `docs/research/` | Split into 6 topic folders + `paper/` + `_research-tools/` |
| `docs/deployment/` | `docs/guides/` |

### New Files

- `docs/tuning/html-reports/README.md` — experiment index with parameter overrides
- `docs/tuning/html-reports/exp_*.html` — 13 experiment HTML reports for quick browsing

---

## Final State

**Before**: 201 root items, 816 GB used, 154 GB free
**After**: 37 root items, 494 GB used, 476 GB free
**Freed**: ~322 GB, root items reduced by 81%

---

## Round 5 — Remove english_1k_results (March 3, 2026)

**Reason**: The `english_1k_results/` directory contained the first systematic pipeline run (860 evaluated segments from 1,520 split segments). This was a preliminary trial run before the full `english_full` baseline (1,497 segments, Feb 18 2026). The 1k results are completely superseded by the full baseline and add no value — same pipeline, same model, just an incomplete earlier run on fewer videos with no additional analysis beyond what the full run covers.

### Deleted

| Item | Size | Reason |
|------|------|--------|
| `english_1k_results/` | 2.6 GB | Preliminary 860-segment trial run, entirely superseded by `english_full_results/` (1,497 segments). Same model, same pipeline, same config — just fewer videos. All metrics, analysis, and reporting reference the full baseline. |
| `scripts/monitoring/watch_and_analyze.sh` | <1 KB | Monitoring script that only referenced the 1k pipeline run and `english_1k_results` directory. Obsolete. |

### Updated References (22+ files)

All references to `english_1k`, `english_1k_results/`, and "860 segments" updated across:
- **CLAUDE.md**: Removed from directory structure and experimental results table
- **Reports 2-6** (docs/): Baseline references updated from "english_1k (860 segments)" to "english_full (1,497 segments)"
- **Report 1** (docs/evaluation/): Added SUPERSEDED notice — retained as historical reference only
- **generate_summary.py**: Removed english_1k column from comparison table
- **run_all_experiments.sh** (2 copies): Removed "english_1k" from experiment comments
- **training-research-notes.md**: Removed english_1k references from key references table
- **golden_weights README.json**: Updated description
- **cleanup-log.md**: Updated VSP-LLMoutputs reference
- **run_avspeech_finetune_pipeline.sh**: Removed english_1k from next-steps echo

**Presentation materials** (`presentation_materials_20260224/`) left untouched — frozen Feb 24 snapshot, historical artifact.

**Freed**: ~2.6 GB

---

## Round 6 — Presentation Sprint (March 2-4, 2026)

**Reason**: Intensive 2-day sprint creating and refining presentations. ~40 commits. This round created more than it removed.

### Files Created

| Category | Items |
|----------|-------|
| **PPTX generator** | `docs/_research-tools/generators/generate_presentation.py` (~5,500 lines) |
| **Plot generators** | `generate_presentation_plots.py` (P1-P6), `generate_finetune_plots.py` (FT_01-FT_11), `generate_pipeline_diagram.py` |
| **Beamer presentation** | `docs/paper/beamer-presentation/` — full LaTeX source (5 sections, theme, tables, figures) |
| **LLM Judge research** | `docs/evaluation/llm_judge/` — 15 batch files, 15 judgment files, analysis.md, results.csv, summary.json |
| **Context eval research** | `docs/evaluation/llm_judge/context_eval/` — 15 context batches, 15 context judgments, analysis.md, results.csv |
| **LLM Salvage research** | `docs/evaluation/llm_salvage/` — analysis.md, segments.json, docx |
| **Fine-tuning eval tools** | `scripts/run_train_eval.sh`, `scripts/eval_checkpoint_correlation.sh`, `scripts/generate_checkpoint_correlation.py` |
| **Presentation plots** | `docs/evaluation/plots/P1-P6.png`, `docs/finetuning/plots/FT_01-FT_11.png` |
| **Pipeline diagrams** | `docs/evaluation/plots/pipeline_architecture.png` (redesigned) |
| **Poster frames** | `presentation_materials_20260224/.poster_frames/` (12 video poster JPEGs) |
| **Beamer figures** | `docs/paper/beamer-presentation/figures/` — branding, deep_dive, plots, pipeline, tikz |
| **Build status** | `docs/paper/beamer-presentation/BUILD_STATUS.md` |

### Files Removed

| Item | Reason |
|------|--------|
| `english_1k_results/` (2.6 GB) | Preliminary 860-segment run superseded by english_full (1,497 segments) |
| `scripts/monitoring/watch_and_analyze.sh` | Only referenced 1k pipeline |

### Data Fixes Applied

| Fix | Scope | Commit |
|-----|-------|--------|
| Stale 67% → 64.1% WER | 22+ files (reports, generators, backlog) | dd2f891, 0f1d04c |
| Context eval de-duplication | context_eval_analysis.md, llm_judge_analysis.md | 5b1df0a |
| Design-time vs runtime LLM | 13 files (docs, generators, Beamer, PPTX) | aa64b9a |
| Beamer stale 67% in appendix | 04_future_directions.tex, 05_appendix.tex | e2bc7bd |

### Conceptual Changes

| Change | Description |
|--------|-------------|
| Fine-tuning reframing | "Experiments failed" → "data-limited, not model-limited" |
| Salvage repositioning | Moved from "future work" to "the full picture" (current evaluation) |
| Failure taxonomy split | 1 slide → 2 slides with explicit detection rules |
| IS explanation | Added weight rationale, 3 independent dimensions, design-time framing |
| Spider chart strategy | Established as reusable template for future LLM comparisons |
