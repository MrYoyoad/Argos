# Presentation Materials — Argos VSP
**Date**: February 24, 2026
**Duration**: 45-60 minutes
**Audience**: Manager / supervisor project review (see `CLIENT_ADAPTATION_GUIDE.md` for client version)

---

## Folder Index

### PRESENTATION_PLAN.md
The full presentation plan with 30-slide structure, example selection rationale, demo video sequencing, and speaker notes. **Read this first.**

---

### 01_plots_for_slides/ (17 files)
Main presentation graphs — use directly in slides.

| File | Slide | What it shows |
|------|-------|---------------|
| `P1_quality_tiers.png` | 5 (Reality Gap) | 5-tier WER quality breakdown: 11.4% usable → 20.6% hallucinated |
| `P2_paper_vs_reality.png` | 4 (Benchmark) | LRS3 25.4% vs Real-world 64.1% with 2.5x annotation |
| `P3_wer_trajectory.png` | 25 (Roadmap) | Projected improvement: 64% → 55% → 45% → 42% WER |
| `P4_lenpen_sensitivity.png` | 13 (Limits) | Length penalty vs empty/hallucination trade-off |
| `P5_tuning_before_after.png` | 12 (Tuning) | Baseline vs Config J paired comparison |
| `pipeline_architecture.png` | 17 (Architecture) | 8-stage pipeline flow diagram |
| `01_wer_vs_duration.png` | 10 (Why the Gap) | Short segments fail catastrophically |
| `09_boxplot_wwer_all_experiments.png` | 9 (Distribution) | WWER spread across all 13 experiments |
| `10_empty_and_hallucination_rates.png` | 12 (Tuning) | Empty vs hallucination rates per config |
| `13_duration_histogram.png` | Context | Segment duration distribution |
| `14_nea_vs_wwer_scatter.png` | 11 (NEA) | Named entity accuracy correlation |
| `15_cdf_wwer_curated.png` | Appendix | CDF of WWER — actionable quality thresholds |
| `16_improvement_J_vs_A.png` | 12 (Tuning) | Per-segment improvement analysis |
| `finetune/FT_01_loss_curves.png` | 28 (Fine-Tuning) | **NEW**: Train vs val loss — divergence after epoch 2 |
| `finetune/FT_02_accuracy_curves.png` | 28 (Fine-Tuning) | **NEW**: Train vs val accuracy — 36.5 pp gap |
| `finetune/FT_03_overfitting_gap.png` | 28 (Fine-Tuning) | **NEW**: Overfitting progression diagnostic |
| `finetune/FT_10_summary_dashboard.png` | 28 (Fine-Tuning) | **NEW**: 6-panel summary dashboard |

### 02_plots_boss_deep_dive/ (14 files)
Technical deep-dive graphs — for supervisor/boss session only.

| File | What it shows |
|------|---------------|
| `03_wwer_vs_duration.png` | Weighted WER by duration (more nuanced than raw WER) |
| `05_nea_recall_vs_duration.png` | Named entity recall drops with short segments |
| `11_wer_vs_wwer_scatter.png` | The lenpen paradox: higher corpus WER but better segment WER |
| `12_segment_stability_heatmap.png` | Which segments are always good/bad across all configs |
| `FT_01_loss_curves.png` | **NEW**: Exp A train vs val loss curves |
| `FT_02_accuracy_curves.png` | **NEW**: Exp A train vs val accuracy (overfitting gap) |
| `FT_03_overfitting_gap.png` | **NEW**: Dual-axis overfitting progression |
| `FT_04_lr_schedule.png` | **NEW**: Tri-stage learning rate schedule |
| `FT_05_gradient_norm.png` | **NEW**: Gradient norm trajectory with trend |
| `FT_06_perplexity.png` | **NEW**: Train vs val perplexity (log scale) |
| `FT_07_data_distribution.png` | **NEW**: Training data IS tier distribution |
| `FT_08_granular_loss.png` | **NEW**: 50-update loss with checkpoint markers |
| `FT_09_wall_clock.png` | **NEW**: Per-epoch training time |
| `FT_10_summary_dashboard.png` | **NEW**: 6-panel training summary dashboard |

### 03_reports_md/supplementary/ (10 files)
Research reports in Markdown format — **presenter reference only, NOT uploaded to Gemini**.
These are supplementary materials for understanding the data behind each slide.

| File | Topic |
|------|-------|
| `report_1_executive_assessment.md` | Baseline evaluation, quality tiers, reality gap analysis |
| `report_2_hyperparameter_tuning.md` | 13 experiments, parameter sweep, best config analysis |
| `report_3_prompt_engineering.md` | Context injection, prompt strategies |
| `report_4_confidence_scoring.md` | Beam scores, quality filtering, confidence extraction |
| `report_5_beam_search_aggregation.md` | N-best ROVER/MBR, hypothesis aggregation |
| `report_6_finetuning_analysis.md` | LoRA fine-tuning, AVSpeech domain adaptation |
| `intelligibility_methodology.md` | IS metric design, 6 signals, tier examples, failure modes (10), success patterns (7), topic analysis (11 categories) |
| `is_correlation_analysis.md` | IS component correlation matrix, variance decomposition, 3 independent dimensions, per-tier signal drivers, LLM heuristic validation (r=0.93, 88.6% agreement), cross-config stability (16 configs) |
| `llm_salvage_analysis.md` | **NEW**: 165 segments where Claude's LLM heuristic identifies recoverable predictions that metrics undercount — raises effective capture from 39.9% to 50.9%, 6 recovery categories with curated examples |
| `finetune_A_comparison_report.md` | Exp A (r=16) training results, overfitting analysis, 10 diagnostic plots, recommendations for Exp B |
| `llm_upgrade_analysis.md` | **NEW**: Comprehensive LLM upgrade analysis — model alternatives (Llama 3.1 8B drop-in, Qwen, Mistral, VALLR), data scaling projections (1.3K→100K segments), 7 prompt strategies by model tier, GER post-processing, multilingual analysis, improvement waterfall (67%→27-42% WER), investment strategy |

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
- `llm_salvage_analysis.docx` — **NEW**: LLM salvage analysis — 165 recoverable segments, 6 categories, curated examples
- `baseline_vs_J_analysis.docx` — Full-dataset comparison (Baseline vs Config C vs Config J, 1497 segments)
- `project-summary.docx` — High-level project overview
- `research-journal.docx` — R&D development journal
- `metrics-explainer.docx` — WER/WWER/NEA metric definitions
- `tuning-experiments.docx` — Experiment methodology
- `pairwise-comparison.pdf` — Segment-level comparison tables
- `intelligibility_report.docx` — **NEW**: IS methodology, tier examples, 1497-segment scoring results
- `intelligibility_summary.json` — **NEW**: IS aggregate stats, tier distribution, signal weights, failure mode distribution, success pattern distribution, signal comparison, topic analysis (11 categories), length analysis

### 05_data/ (18+ files)
Raw data for reference or custom analysis.

| File | Contents |
|------|----------|
| `experiment-comparison.csv` | All 13 experiments (A-M) with WER/WWER/NEA metrics |
| `report.csv` | Full baseline results (1,497 segments with per-segment metrics) |
| `intelligibility_scores.csv` | **NEW**: Per-segment IS scores, tiers, 6 signals, context recoverability (1,497 rows) |
| `llm_salvage_segments.json` | **NEW**: 165 LLM-salvageable segments with full metrics, category tags, curated for presentation |
| `segment_metadata.json` | Segment timing, duration, source video metadata |
| `metadata.json` | Curated interesting examples with annotations |
| `html_reports/` | 13 interactive HTML reports (one per experiment, open in browser) |

### 06_demo_videos/ (8 files)
Selected burned videos with subtitle overlays — play during presentation.

**Opening Hook (Slide 2):**
- `IEa7qEkMvfQ_3__c5447488_with_hyp.mp4` — 33 words perfectly lip-read (WER 0%)

**Live Demo Sequence (Slide 14) — play in this order:**
1. `d8BR6hsvzoY_31__2e9546df_with_hyp.mp4` — "buy one get one free" (WER 0%, short/punchy)
2. `-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4` — "admiral mcrae" → "animal migratory" (funny near-miss)
3. `00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4` — hallucination: fabricates "David Irving" narrative (WER 100%)

**Tuning Comparison (Slide 13):**
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

1. **Open `gemini_presentation_instructions.docx`** — contains all 4 Gemini prompts with image upload lists
2. **Upload images, paste prompts** — 18 images total across 4 prompts (Gemini inserts them by name)
3. **Apply animations** — use the Animation Checklist in the docx (~10-15 min)
4. **Insert demo videos** — slides 2 and 15 have placeholders; play from `06_demo_videos/`
5. **Reference `03_reports_md/supplementary/`** for detailed data behind each slide (NOT uploaded to Gemini)

## Key Numbers for Reference

| Metric | Value | Source |
|--------|-------|--------|
| Paper WER (LRS3) | 25.4% | VSP-LLM paper, Table 1 |
| Real-world mean WER | 64.1% | Report 1, 1497 segments |
| Reality gap | 2.5x worse | Report 1 |
| Usable segments (WER <30%) | 11.4% | Report 1, quality tiers |
| **Properly captured (IS >= 3.0)** | **39.9%** | **Intelligibility Score, 1497 segments** |
| **IS: WER overstatement factor** | **3.5x** | **39.9% vs 11.4%** |
| **Mean IS** | **2.52 / 5.0** | **Intelligibility summary** |
| **IS Excellent (4-5)** | **18.4%** | **276 segments** |
| **IS Good (3-4)** | **21.4%** | **321 segments** |
| **Context recoverable** | **43.6-50.6%** | **Rule-based / LLM-judged** |
| **LLM-salvageable (IS<3 but recoverable)** | **165 / 900 (18.3%)** | **LLM salvage analysis** |
| **Effective capture (IS + salvage)** | **762 / 1,497 (50.9%)** | **Up from 39.9%** |
| **Failure modes classified** | **10 modes** | **900 failed segments** |
| **#1 failure: Topic Drift** | **15.9%** | **143 segments** |
| **#1 success: Phonetic Preservation** | **41.5%** | **248 of 597 successes** |
| **Best topic: Business/Finance** | **IS 3.08, 57% captured** | **46 segments** |
| **Worst topic: DIY/Home** | **IS 2.13, 30% captured** | **27 segments** |
| **Short segments (5-10 words)** | **32% captured, 74% WER** | **290 segments** |
| **Long segments (20+ words)** | **49% captured, 55% WER** | **535 segments** |
| **Config J IS (full dataset)** | **2.60 vs 2.52 baseline** | **1,497 segments** |
| **Config J captured** | **622 vs 597 (+25)** | **Empties 0 vs 70** |
| NEA F1 (named entities) | 38.8% | Report 1 |
| **NEA F1: largest differentiator** | **74% success vs 16% failure** | **Signal comparison** |
| Best config WWER (J) | 57.7% | Experiment comparison, 107 segments |
| Empty prediction rate (Baseline) | 14.0% | Experiment A |
| Empty prediction rate (Config J) | 0.0% | Experiment J |
| Bugs fixed | 37 | Bug tracking docs |
| Pipeline: lines before refactor | 823 | CLAUDE.md |
| Pipeline: lines after refactor | 393 | CLAUDE.md |
| Test suite | 37 tests | lib/test_all_modules.sh |
| Total experiments | 13 (A-M) | experiment-comparison.csv |
| Research reports | 8 | Including IS methodology + LLM upgrade |
| Segments per experiment | 107 | Tuning dataset |
| Full dataset segments | 1,497 | english_full_results |
| Projected WER (combined phases) | 27-42% | LLM upgrade analysis |
| **Exp A: Best val accuracy** | **62.94% (epoch 2)** | **Fine-tuning r=16, 320 updates** |
| **Exp A: Final val accuracy** | **58.98% (epoch 19)** | **Overfitting: 36.5 pp gap** |
| **Exp A: Training time** | **17.0 hours** | **Tesla T4, FP16** |
| **Exp A: Trainable params** | **12.6M (0.19%)** | **LoRA r=16, alpha=32** |
| **Exp A: Training data** | **1,273 train / 224 val** | **Stratified by IS tier** |
| **IS: top signal correlate** | **Phonetic Sim r=0.943** | **Correlation analysis** |
| **IS: 3 independent dimensions** | **Word acc 60%, Meaning 28%, Sanity 9%** | **Variance decomposition** |
| **IS: Claude-designed heuristic (16 configs)** | **r=0.925 mean (std=0.015)** | **No runtime LLM calls** |
| **IS: heuristic agreement** | **88.6%, kappa=0.77, recall 99.2%** | **Baseline confusion matrix** |
| **IS: stable signals (16 configs)** | **Semantic, Phonetic, NEA (std<0.06)** | **WER/LR volatile** |
| **IS: cross-config rankings** | **r > 0.92 across most config pairs** | **Encoder-limited, not decode** |
| **IS: Config J vs baseline** | **IS 2.571 vs 2.485 despite +14.8pp WER** | **IS captures meaning WER misses** |
| **IS: methodology** | **LLM-distilled (Claude-designed rubric)** | **Design-time expert judgment** |
| **LLM: current model** | **Llama-2-7B (4-bit QLoRA, r=16)** | **Hidden size 4096** |
| **LLM: recommended swap** | **Llama 3.1 8B (drop-in, same dim)** | **1-2 hours setup** |
| **LLM swap alone** | **-3 to -8pp WER** | **Better language modeling** |
| **Prompts: force multiplier** | **Llama-2 +5-10pp / Llama 3.1 +12-20pp** | **7 strategies** |
| **GER post-processing** | **+8-15pp, no retraining** | **N-best + correction LLM** |
| **Data scaling: 20K segments** | **45-50% (Llama-2) / 40-45% (Llama 3.1)** | **ICLR 2024 power law** |
| **Combined realistic target** | **27-42% WER (from 67%)** | **LLM + data + prompts + GER** |
| **Multiplicative scaling law** | **LLM + data improvements compound** | **ICLR 2024** |
| **VALLR (ICCV 2025)** | **18.7% WER on LRS3 with 3B model** | **Architecture > model size** |

---

## PENDING: Presentation Update Required

**Task**: The presentation slides (generated via Gemini) need updating to incorporate the **LLM Salvage Analysis** results (March 2, 2026). This analysis shows that 165 metric-failed segments are actually recoverable, raising the effective capture rate from 39.9% to 50.9%.

**What to add to the presentation:**
1. A new slide (or addition to the IS section) showing the "hidden value" — 50.9% effective capture vs 39.9% metric-only
2. Update the "Key Findings" slide to reflect the revised capture rate
3. Consider adding 1-2 curated examples from `llm_salvage_analysis.md` showing dramatic WER-vs-meaning gaps (e.g., WER 74% but semantically preserved content)
4. The `llm_salvage_analysis.docx` in `04_reports_docx/` and `llm_salvage_segments.json` in `05_data/` are ready for use

**Files available:**
- `03_reports_md/supplementary/llm_salvage_analysis.md` — Full analysis
- `04_reports_docx/llm_salvage_analysis.docx` — Formatted report
- `05_data/llm_salvage_segments.json` — 165 segments with all metrics
