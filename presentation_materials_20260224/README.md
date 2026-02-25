# Presentation Materials — Argos VSP
**Date**: February 24, 2026
**Duration**: 45-60 minutes
**Audience**: Client demo + Supervisor review + Potential new clients

---

## Folder Index

### PRESENTATION_PLAN.md
The full presentation plan with 27-slide structure, example selection rationale, dual-audience strategy, demo video sequencing, and speaker notes. **Read this first.**

---

### 01_plots_for_slides/ (13 files)
Main presentation graphs — use directly in slides.

| File | Slide | What it shows |
|------|-------|---------------|
| `P1_quality_tiers.png` | 5 (Reality Gap) | 5-tier quality breakdown: 11.4% usable → 20.6% hallucinated |
| `P2_paper_vs_reality.png` | 4 (Benchmark) | LRS3 25.4% vs Real-world 64.1% with 2.5x annotation |
| `P3_wer_trajectory.png` | 21 (Roadmap) | Projected improvement: 64% → 55% → 45% → 42% WER |
| `P4_lenpen_sensitivity.png` | 10 (Limits) | Length penalty vs empty/hallucination trade-off |
| `P5_tuning_before_after.png` | 9 (Tuning) | Baseline vs Config J paired comparison |
| `pipeline_architecture.png` | 14 (Architecture) | 8-stage pipeline flow diagram |
| `01_wer_vs_duration.png` | 7 (Why the Gap) | Short segments fail catastrophically |
| `09_boxplot_wwer_all_experiments.png` | 6 (Distribution) | WWER spread across all 13 experiments |
| `10_empty_and_hallucination_rates.png` | 9 (Tuning) | Empty vs hallucination rates per config |
| `13_duration_histogram.png` | Context | Segment duration distribution |
| `14_nea_vs_wwer_scatter.png` | 8 (NEA) | Named entity accuracy correlation |
| `15_cdf_wwer_curated.png` | Appendix | CDF of WWER — actionable quality thresholds |
| `16_improvement_J_vs_A.png` | 9 (Tuning) | Per-segment improvement analysis |

### 02_plots_boss_deep_dive/ (4 files)
Technical deep-dive graphs — for supervisor/boss session only.

| File | What it shows |
|------|---------------|
| `03_wwer_vs_duration.png` | Weighted WER by duration (more nuanced than raw WER) |
| `05_nea_recall_vs_duration.png` | Named entity recall drops with short segments |
| `11_wer_vs_wwer_scatter.png` | The lenpen paradox: higher corpus WER but better segment WER |
| `12_segment_stability_heatmap.png` | Which segments are always good/bad across all configs |

### 03_reports_md/ (6 files)
Research reports in Markdown format — reference material for slide content.

| File | Topic |
|------|-------|
| `report_1_executive_assessment.md` | Baseline evaluation, quality tiers, reality gap analysis |
| `report_2_hyperparameter_tuning.md` | 13 experiments, parameter sweep, best config analysis |
| `report_3_prompt_engineering.md` | Context injection, prompt strategies |
| `report_4_confidence_scoring.md` | Beam scores, quality filtering, confidence extraction |
| `report_5_beam_search_aggregation.md` | N-best ROVER/MBR, hypothesis aggregation |
| `report_6_finetuning_analysis.md` | LoRA fine-tuning, AVSpeech domain adaptation |

### 04_reports_docx/ (18 files)
Formatted reports (Word + PDF) — printable, shareable with stakeholders.

**Core 6 Research Reports** (docx + pdf pairs):
- `report_1_executive_assessment` — Baseline evaluation
- `report_2_hyperparameter_tuning` — Parameter sweep
- `report_3_prompt_engineering` — Prompt strategies
- `report_4_confidence_scoring` — Confidence scoring
- `report_5_beam_search_aggregation` — N-best aggregation
- `report_6_finetuning_analysis` — Fine-tuning analysis

**Supplementary Reports**:
- `baseline_vs_J_analysis.docx` — **NEW**: Full-dataset comparison (Baseline vs Config C vs Config J, 1497 segments)
- `project-summary.docx` — High-level project overview
- `research-journal.docx` — R&D development journal
- `metrics-explainer.docx` — WER/WWER/NEA metric definitions
- `tuning-experiments.docx` — Experiment methodology
- `pairwise-comparison.pdf` — Segment-level comparison tables

### 05_data/ (16+ files)
Raw data for reference or custom analysis.

| File | Contents |
|------|----------|
| `experiment-comparison.csv` | All 13 experiments (A-M) with WER/WWER/NEA metrics |
| `report.csv` | Full baseline results (1,497 segments with per-segment metrics) |
| `segment_metadata.json` | Segment timing, duration, source video metadata |
| `metadata.json` | Curated interesting examples with annotations |
| `html_reports/` | 13 interactive HTML reports (one per experiment, open in browser) |

### 06_demo_videos/ (8 files)
Selected burned videos with subtitle overlays — play during presentation.

**Opening Hook (Slide 2):**
- `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` — 33 words perfectly lip-read (WER 0%)

**Live Demo Sequence (Slide 12) — play in this order:**
1. `d8BR6hsvzoY_31__2e9546df_with_hyp.mp4` — "buy one get one free" (WER 0%, short/punchy)
2. `-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4` — "admiral mcrae" → "animal migratory" (funny near-miss)
3. `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4` — hallucination: fabricates "David Irving" narrative (WER 100%)

**Tuning Comparison (Slide 11):**
- `DBhaa45mAro_2__07d05c7a_Part1_with_hyp.mp4` + `Part2` — baseline empty → Config J partial transcription
- `eLS1vcpGVHQ_12__e9dd9adc_with_hyp.mp4` — Config J generates TED talk hallucination
- `-WQZsfHcPDM_7__5210cac1_with_hyp.mp4` — "bottle/probiotics" → "monitor/permafrost" (visual ambiguity)

### 07_paper/ (3 files)
Original VSP-LLM paper and existing presentation.

| File | Contents |
|------|----------|
| `VSP_LLM_paper.pdf` | Original paper — Figure 1 (architecture), Table 1 (benchmarks), Figure 3 (homophones), Figure 4 (WER vs length) |
| `VSP_LLM_paper_text.txt` | Extracted text for reference |
| `Presentation_2025.pptx` | Existing 2025 presentation — reuse slides/formatting as needed |

### 08_branding/ (3 files)
Logo files for title slide and headers.

- `BlackLogo300x300-W-BG.png` — Square logo with white background
- `LogoSVG.svg` — Vector logo (scalable)
- `OIG1.JPEG` — Alternative logo

### 09_pipeline_diagram/ (1 file)
- `pipeline_architecture.png` — Professional 8-stage pipeline flow with color-coded stages, model labels (AV-HuBERT + LLaMA-2 + fairseq), and lib/ module annotations

### 10_examples/ (3 files)
Curated example data for building comparison tables.

| File | Contents |
|------|----------|
| `metadata.json` | 20 curated examples with ref/hyp/WER/annotations |
| `cross_experiment_comparison.csv` | Same segments across all experiments |
| `full_results_report.txt` | Complete text report from baseline evaluation |

---

## Quick Start Guide

1. **Read `PRESENTATION_PLAN.md`** for the full 27-slide structure and speaker notes
2. **Start with `01_plots_for_slides/`** — these map directly to slides in the plan
3. **Open `06_demo_videos/IEa7qEkMvfQ_3__c5447488_with_hyp.mp4`** for the opening hook
4. **Use `04_reports_docx/`** for any content you want to hand out or reference
5. **Browse `05_data/html_reports/`** in a browser for interactive per-experiment details

## Key Numbers for Reference

| Metric | Value | Source |
|--------|-------|--------|
| Paper WER (LRS3) | 25.4% | VSP-LLM paper, Table 1 |
| Real-world mean WER | 64.1% | Report 1, 1497 segments |
| Reality gap | 2.5x worse | Report 1 |
| Usable segments (WER <30%) | 11.4% | Report 1, quality tiers |
| NEA F1 (named entities) | 38.8% | Report 1 |
| Best config WWER (J) | 57.7% | Experiment comparison, 107 segments |
| Empty prediction rate (Baseline) | 14.0% | Experiment A |
| Empty prediction rate (Config J) | 0.0% | Experiment J |
| Bugs fixed | 37 | Bug tracking docs |
| Pipeline: lines before refactor | 823 | CLAUDE.md |
| Pipeline: lines after refactor | 393 | CLAUDE.md |
| Test suite | 37 tests | lib/test_all_modules.sh |
| Total experiments | 13 (A-M) | experiment-comparison.csv |
| Segments per experiment | 107 | Tuning dataset |
| Full dataset segments | 1,497 | english_full_results |
| Projected WER after Phase 3 | ~42% | Mission backlog |
