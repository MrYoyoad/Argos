# Presentation Materials — Argos VSP
**Last updated**: March 4, 2026
**Status**: COMPLETE — both formats fully built with all research through March 4

---

## Generated Presentations

| Format | Location | Slides | Build Command |
|--------|----------|--------|---------------|
| **PPTX** | `Argos_VSP_Project_Review.pptx` | ~47 | `python3 docs/_research-tools/generators/generate_presentation.py` |
| **Beamer PDF** | `docs/paper/beamer-presentation/main.pdf` | 75 | `cd docs/paper/beamer-presentation && make` |

Both are independently maintained — changes in one do NOT propagate to the other.

---

## Folder Index

| Folder | Contents |
|--------|----------|
| `01_plots_for_slides/` | 21 presentation plots (P1-P6, FT_01-FT_11, pipeline, model arch) |
| `02_plots_boss_deep_dive/` | 14 deep-dive plots for supervisor Q&A |
| `03_reports_md/supplementary/` | 11 research reports in markdown (reference only) |
| `04_reports_docx/` | 18 formatted reports (Word + PDF) |
| `05_data/` | CSVs, JSONs — raw data for all slides |
| `06_demo_videos/` | 8 burned videos for live demo |
| `07_paper/` | Original VSP-LLM paper + 2025 presentation |
| `08_branding/` | Logo files (PNG, SVG, JPEG) |
| `09_pipeline_diagram/` | 8-stage pipeline architecture diagram |
| `10_examples/` | Curated example data for comparison tables |
| `.poster_frames/` | 12 video poster frame JPEGs for PPTX embedding |

---

## Key Numbers (Quick Reference)

| Metric | Value | Source |
|--------|-------|--------|
| Baseline WER | 64.1% (1,497 segments) | english_full_results |
| IS mean | 2.52/5.0 | intelligibility_summary.json |
| Properly captured (IS >= 3.0) | 39.9% (597/1,497) | intelligibility_scores.csv |
| Effective capture (IS + salvage) | 50.9% (762/1,497) | llm_salvage_segments.json |
| LLM Judge blind (Y+P) | 64.9% | llm_judge_results.csv |
| LLM Judge context (Y+P) | 62.1% (stricter) | context_eval_results.csv |
| Finetune: Baseline IS | 2.487 | checkpoint_correlation.csv |
| Finetune: Exp A IS | 2.312 | checkpoint_correlation.csv |
| Cross-config r | 0.925 (16 configs) | is_correlation_analysis.md |
| Projected WER (combined) | 27-42% | llm_upgrade_analysis.md |

---

## Key Narrative Decisions (March 2026)

1. **IS = design-time LLM-distilled**: Claude designed the rubric; no LLM runs at eval time
2. **Fine-tuning = data-limited**: 1.3K segments below LoRA minimum; data scaling solves it
3. **Salvage = current insight**: 51% effective capture (not future work)
4. **Spider chart = reusable**: Template for future LLM comparison (Llama-2 vs Llama-3.1)
5. **Narrative arc**: Nuanced ("40% captured, 51% with salvage") not deficit ("64% WER = bad")

---

## Regeneration

To rebuild everything from scratch:
```bash
# 1. Plots
python3 docs/_research-tools/generators/generate_presentation_plots.py
python3 docs/_research-tools/generators/generate_finetune_plots.py
python3 docs/_research-tools/generators/generate_pipeline_diagram.py

# 2. PPTX
python3 docs/_research-tools/generators/generate_presentation.py

# 3. Beamer
cd docs/paper/beamer-presentation && make clean && make
```

---

## Related Docs

- `PRESENTATION_PLAN.md` — Original design doc with slide structure and example rationale
- `CLIENT_ADAPTATION_GUIDE.md` — How to adapt for client/external audiences
- `gemini_presentation_instructions.docx` — Gemini prompts for alternative generation
- `docs/paper/beamer-presentation/BUILD_STATUS.md` — Detailed content coverage matrix
- `docs/_research-tools/generators/STYLE_GUIDE.md` — Styling conventions for all formats
