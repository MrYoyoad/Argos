# Presentation Build Status

**Last updated**: March 4, 2026

## Formats

### Beamer (LaTeX)
- **Location**: `docs/paper/beamer-presentation/`
- **Build**: `cd docs/paper/beamer-presentation && make`
- **Total slides**: 75 (56 main + 19 appendix)
- **Sections**: Opening (6), Research Findings (28), Engineering (10), Future Directions (10), Appendix (19 backup + 2 structural)
- **Status**: Current as of March 4, 2026

### PPTX (PowerPoint)
- **Generator**: `docs/_research-tools/generators/generate_presentation.py` (~5,500 lines)
- **Output**: `presentation_materials_20260224/Argos_VSP_Project_Review.pptx`
- **Build**: `python3 docs/_research-tools/generators/generate_presentation.py`
- **Total slides**: ~47 (main + 9 appendix)
- **Appendix**: A1-A9 (sequentially numbered subset of Beamer's A1-A17)
- **Pipeline slide 17**: Programmatic 2-row layout (not image-based)
- **Status**: Current as of March 4, 2026

## Content Coverage Matrix

| Research Finding | Beamer | PPTX | Notes |
|-----------------|--------|------|-------|
| Baseline WER 64.1% | Slide 3, 8 | Slide 3, 8 | Executive summary + dataset |
| IS methodology (6 signals) | Slides 10-11 | Slides 10-11 | Weight rationale, 3 dimensions |
| IS tier distribution | Slide 9 | Slide 9 | P1 quality tiers chart |
| Paper vs reality gap | Slide 8 | Slide 8 | P2 comparison chart |
| Failure mode taxonomy (5 categories) | Slides 19a-19b | Slides ~18-19 | Signal Loss, Hallucination, Wrong Topic, Right Topic Wrong Details, Accumulated Errors |
| Hallucination vs topic drift | Slides 19a-19b | Slides ~18-19 | Explicit detection rules |
| Tuning experiments (13 configs) | Slides 16-17 | Slide ~15 | Condensed in PPTX |
| LLM Salvage (165 segments, 50.9%) | Slide 21, A11-A11b | Slides ~22-26, A4-A5 | Domain context examples |
| LLM Judge blind (Y+P=65%) | Slide 22, A16 | Slide ~21, A8 | Agreement matrices |
| LLM Judge context (Y+P=62%) | Slide 23, A17 | A9 | 230 downgrades vs 68 upgrades |
| Fine-tuning Exp A/B | Slide 40-41, A2 | Slides ~30-31 | Data-limited framing |
| Spider/radar chart (IS profiles) | Referenced | Slide ~16 | P6 IS radar |
| Pipeline architecture | Slide 25 | Slide ~28 | 8-stage diagram |
| Roadmap (5 phases, IS 3.5-4.0 target) | Slides 37-42 | Slides ~33-40 | Phase-to-failure-category mapping |
| Topic analysis (11 categories) | Slide 18, A6 | Included | Domain confusion ~19% |
| IS validation (cross-config) | Slides 15a-15b, A8 | A3 | r=0.925, 16 configs |

## Sync Status

Both formats are **independently maintained**:
- Beamer: LaTeX source in `sections/*.tex`
- PPTX: Python generator `generate_presentation.py`
- Changes in one do NOT propagate to the other
- After any content change, both must be manually updated

## Key Narrative Decisions (March 2026)

1. **IS = design-time LLM-distilled**: Claude designed the rubric; no LLM calls at eval time
2. **Fine-tuning = data-limited**: 1.3K segments below LoRA minimum; problem solved with 20K+ segments
3. **Salvage = current insight**: 51% effective capture, not future work
4. **Spider chart = reusable**: Template for future LLM comparison (Llama-2 vs Llama-3.1)
5. **Narrative arc**: Nuanced ("40% captured, 51% with salvage") not deficit ("64% WER = bad")

## Data Sources

| File | Feeds Into |
|------|-----------|
| `english_full_results/intelligibility_scores.csv` | All baseline metrics, example segments |
| `tuning_results/comparison.csv` | Experiment comparison tables |
| `docs/evaluation/llm_judge/llm_judge_results.csv` | LLM Judge numbers |
| `docs/evaluation/llm_judge/context_eval/context_eval_results.csv` | Context eval numbers |
| `docs/evaluation/llm_salvage/llm_salvage_segments.json` | Salvage categories |
| `docs/evaluation/intelligibility/intelligibility_summary.json` | IS summary stats |
| `docs/finetuning/checkpoint_correlation.csv` | Fine-tuning eval metrics |

## Plot Generators

| Generator | Output | Plots |
|-----------|--------|-------|
| `generate_presentation_plots.py` | `docs/evaluation/plots/P*.png` | P1-P6+P3b (tiers, gap, WER trajectory, IS trajectory, lenpen, tuning, radar) |
| `generate_finetune_plots.py` | `docs/finetuning/plots/FT_*.png` | FT_01-FT_11 (loss, accuracy, overfitting, etc.) |
| `generate_pipeline_diagram.py` | `docs/evaluation/plots/pipeline_architecture.png` | 8-stage pipeline diagram (Beamer only; PPTX slide 17 is now programmatic) |

## Regeneration Checklist

To rebuild from scratch:
1. `python3 docs/_research-tools/generators/generate_presentation_plots.py` — regenerate P1-P6 + P3b
2. `python3 docs/_research-tools/generators/generate_finetune_plots.py` — regenerate FT_01-FT_11
3. `python3 docs/_research-tools/generators/generate_pipeline_diagram.py` — regenerate pipeline diagram
4. `python3 docs/_research-tools/generators/generate_presentation.py` — regenerate PPTX
5. `cd docs/paper/beamer-presentation && make clean && make` — rebuild Beamer PDF
