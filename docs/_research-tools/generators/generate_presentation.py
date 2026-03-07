#!/usr/bin/env python3
"""
Argos VSP — PPTX Presentation Generator

Creates the complete 80-slide "Argos VSP: Research Findings and Production
Roadmap" presentation with professional styling, real images, entrance
animations, fade transitions, and speaker notes.

Usage:
    python3 docs/_research-tools/generators/generate_presentation.py

Output:
    presentation_materials_20260224/Argos_VSP_Project_Review.pptx

Architecture:
    This file is a slim orchestrator. All logic lives in the presentation/ package:
        presentation/config.py           — paths, colors, layout constants
        presentation/helpers.py          — slide setup, text, shapes, animations
        presentation/slides_opening.py   — Sections 0-2: Opening, Context, Problem
        presentation/slides_research.py  — Sections 3-5: Research, Understanding, Tuning
        presentation/slides_evaluation.py— Section 6 + Salvage + Demos
        presentation/slides_engineering.py — Section 7: Engineering
        presentation/slides_future.py    — Section 8: Future + Appendix
"""

from pptx import Presentation

from presentation.config import SL_W, SL_H, OUTPUT, _auto_num
from presentation.helpers import _fix_pptx_video_compat

from presentation.slides_opening import (
    slide_01, slide_exec_summary, slide_wer_lies, slide_toc,
    slide_02, slide_visemes, slide_03, slide_data_flow,
    slide_04, slide_eval_dataset, slide_05, slide_wer_explained,
    slide_06, slide_is_foreshadow,
)
from presentation.slides_research import (
    slide_research_transition, slide_is_intro, slide_is_signals,
    slide_is_weight_rationale, slide_is_dimensions,
    slide_is_calc_examples, slide_is_radar, slide_is_wer_scatter,
    slide_07, slide_metric_transition,
    slide_10, slide_domain_mismatch, slide_11,
    slide_failure_deep_1a, slide_failure_deep_1b, slide_failure_deep_2, slide_08,
    slide_failure_deep_3, slide_tuning_summary,
)
from presentation.slides_evaluation import (
    slide_is_deep_dive, slide_metric_disagreement, slide_metric_disagreement_2,
    slide_two_eval_systems, slide_llm_judge, slide_context_eval,
    slide_llm_context_engine,
    slide_25, slide_25b, slide_25d, slide_25e, slide_25c,
    slide_what_good_looks_like, slide_14b, slide_15,
)
from presentation.slides_engineering import (
    slide_eng_transition, slide_three_repos,
    slide_17, slide_18, slide_19, slide_20,
    slide_web_ui, slide_21, slide_dual_env,
)
from presentation.slides_future import (
    slide_future_transition, slide_insights, slide_24,
    slide_26, slide_26b, slide_confidence_scoring,
    slide_27, slide_28, slide_data_scaling, slide_price_tag,
    slide_29, slide_30, slide_arabic_roadmap, slide_31, slide_thank_you,
    slide_a1, slide_a3, slide_a8, slide_a11, slide_a11b,
    slide_a13, slide_a15, slide_a16, slide_a17,
)


def main():
    _auto_num[0] = 0  # Reset auto-numbering

    prs = Presentation()
    prs.slide_width = SL_W
    prs.slide_height = SL_H

    print("Generating presentation...")

    builders = [
        # --- Section 0: Opening ---
        slide_01,           # Title
        slide_exec_summary, # Executive summary
        slide_wer_lies,     # [NEW] Side-by-side: WER lies, IS tells truth
        slide_toc,          # Table of contents
        # --- Section 1: Context ---
        slide_02,           # What is VSP? (video)
        slide_visemes,      # [MOD] Fundamental challenge + poster frames
        slide_03,           # Model Architecture
        slide_data_flow,    # How It Works
        slide_04,           # The Benchmark
        # --- Section 2: The Problem ---
        # slide_eval_dataset, # Our evaluation dataset (hidden per batch 8)
        slide_05,           # The Reality Gap (64.1% WER)
        # slide_wer_explained,# WER formula and limitations (hidden per batch 8)
        slide_06,           # WER Is Blind to Meaning
        slide_is_foreshadow,# Bridge: We Need a Better Metric
        # --- Section 3: Research Findings ---
        slide_research_transition, # Section divider
        slide_is_intro,     # Introducing IS (split into 3 per batch 8)
        # slide_is_signals,   # IS: Six Signals (removed per batch 8 — merged into split)
        slide_is_weight_rationale, # Why These Weights? 3 Dimensions
        # slide_is_dimensions,# Three quality dimensions (hidden per batch 8)
        slide_is_calc_examples, # IS in Action: Two Real Segments
        slide_is_radar,     # [MOD] IS Radar: dual overlay if available
        slide_is_wer_scatter, # [NEW] The Gap: WER vs IS scatter
        slide_07,           # IS Results: 39.9% Captured
        slide_metric_transition, # [NEW] 64.1% -> 39.9% -> 50.9%
        # --- Section 4: Understanding Why ---
        # slide_10,           # Three Root Causes (hidden per batch 8)
        # slide_domain_mismatch, # Domain mismatch detail (hidden per batch 8)
        # slide_11,           # Named Entity Accuracy (hidden per batch 8)
        slide_failure_deep_1a, # Failure Modes: 5-Category Taxonomy (1/2)
        slide_failure_deep_1b, # Failure Modes: 5-Category Taxonomy (2/2)
        slide_failure_deep_2, # Failure Modes: Real Examples
        slide_08,           # Failure Mode Taxonomy
        slide_failure_deep_3, # Failure Modes: Impact & Fixes
        # --- Section 5: Can We Tune It? ---
        # slide_tuning_summary, # 13 Experiments, Minimal Gain (hidden per batch 8)
        # --- Section 6: The Full Picture ---
        slide_is_deep_dive, # Why These 6 Signals? Validation
        # slide_metric_disagreement, # When Metrics Disagree (hidden per batch 12)
        slide_metric_disagreement_2, # When Metrics Disagree pt 2
        slide_two_eval_systems, # Two evaluation systems
        slide_llm_judge,    # LLM-as-a-Judge
        # slide_context_eval, # Context-aware re-evaluation (decluttered: 1 table + bullets)
        # --- Salvage ---
        slide_25,           # LLM Salvage overview: 39.9% -> 50.9% (reframed: lower bound, LLM-judge only per batch 8)
        slide_llm_context_engine, # LLM as context engine
        # slide_25b,          # Salvage: 6 Recovery Categories (hidden per batch 8)
        slide_25d,          # Salvage: 3 Real Examples
        slide_25e,          # Salvage: 3 More Examples
        # slide_25c,          # Salvage: How Detection Works (hidden per batch 8)
        # --- What good looks like ---
        # slide_what_good_looks_like,  # hidden per user request
        slide_14b,          # Video Gallery
        slide_15,           # Demo: OK > Near-miss > Hallucination
        # --- Section 7: Engineering ---
        slide_eng_transition, # Section divider
        slide_three_repos,  # Starting point
        slide_17,           # [MOD] Pipeline: per-stage wipe reveal
        slide_18,           # Engineering Journey
        # slide_19,           # 52% Code Reduction (hidden per batch 12)
        slide_20,
        slide_web_ui,       # Web UI
        slide_21,
        slide_dual_env,     # Two environments
        # --- Section 8: Future Directions ---
        slide_future_transition, # Section divider
        slide_insights,     # Key research insights
        slide_24,           # Starting point better than WER
        slide_26,           # Five Phases roadmap
        slide_26b,          # IS trajectory roadmap
        slide_confidence_scoring, # Phase 1: Confidence Scoring detail
        slide_27,           # Phase 1 Confidence
        slide_28,           # Phase 2 N-Best
        slide_data_scaling, # [MOD] Data scaling with phases + timelines
        slide_price_tag,    # [NEW] Cost projections: GPU/data/IS
        slide_29,           # Phase 3-4 Fine-Tuning
        slide_30,           # Phase 5 LLM Upgrade
        slide_arabic_roadmap, # Arabic Pipeline Roadmap
        slide_31,           # Key Takeaways
        slide_thank_you,    # Thank You & Questions
        # --- Appendix (A1-A9) ---
        slide_a1,           # A1: Homophenes
        # slide_a3,         # A2: Catastrophic lenpen (removed)
        slide_a8,           # A3: IS Component Correlation
        slide_a11,          # A4: LLM Salvage Recoverable
        slide_a11b,         # A5: LLM Salvage Examples
        slide_a13,          # A6: Failure Mode Examples
        slide_a15,          # A7: Video Gallery Map
        slide_a16,          # A8: LLM Judge x IS Tier
        slide_a17,          # A9: Context transition matrix
    ]
    total = len(builders)

    for i, builder in enumerate(builders, 1):
        print(f"  Slide {i:2d}/{total} ...", end=" ")
        try:
            builder(prs)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    _fix_pptx_video_compat(str(OUTPUT))
    print(f"\nSaved: {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
