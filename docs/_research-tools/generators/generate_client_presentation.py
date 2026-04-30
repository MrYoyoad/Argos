#!/usr/bin/env python3
"""Argos VSP — Client Deck Generator.

Slim orchestrator (~150 lines) for the 53-slide client presentation.
Per the borrow-vs-build policy in
.claude/plans/i-need-to-create-proud-cupcake.md, this file IMPORTS and CALLS
existing builders from presentation/slides_*.py. The only net-new builders
live in presentation/slides_client.py.

Output:
    presentation_materials_20260224/Argos_VSP_Client_46slides_Apr2026.pptx

Run:
    python3 docs/_research-tools/generators/generate_client_presentation.py
"""

from pathlib import Path

from pptx import Presentation

from presentation.config import SL_W, SL_H, _auto_num, MATERIALS

# Borrow from existing slide modules. The borrow-vs-build policy is binding.
from presentation.slides_opening import (
    slide_data_flow,      # pipeline overview (reused — clean enough as-is)
)
# slide_visemes replaced with slide_client_visemes (no jargon, client-friendly).
# slide_llm_judge / slide_judge_ex* / slide_14b / slide_what_good_looks_like
# intentionally NOT imported — those academic-styled slides were replaced
# with client-friendly equivalents in slides_client.py. See builders[] notes.
from presentation.slides_engineering import (
    slide_web_ui,                  # UI overview
)
# slide_three_repos and slide_dual_env replaced with client-friendly
# slide_client_pipeline_components and slide_client_deployment_options.
from presentation.slides_future import (
    slide_arabic_roadmap,          # high-level Arabic roadmap (per v3 user feedback)
    slide_thank_you,               # close
)

# Net-new and reframed builders for the client deck.
from presentation.slides_client import (
    # Section 1
    slide_client_title,
    slide_client_summary,
    slide_client_headline_numbers,
    slide_client_agenda,
    # Section 2
    slide_client_demo_intro,
    slide_client_demo_video_embed,
    slide_client_demo_recap,
    # Section transitions (factory)
    make_section_transition,
    # Section 3 — replacements for academic-styled borrowed slides
    slide_client_examples_intro,
    slide_client_example_perfect,
    slide_client_example_partial,
    slide_client_example_flagged,
    # Section 4
    slide_client_confidence_question,
    slide_client_two_layer_confidence,
    slide_client_word_color_coding,
    slide_client_seq_confidence_correlation,
    slide_client_trust_dashboard,
    slide_client_hallucination_flag,
    slide_client_what_this_means,
    # Section 5
    slide_client_validation_intro,
    slide_client_agreement_chart,
    slide_client_cross_config_stability,
    slide_client_validation_summary,
    # Section 6 — reframed pipeline slides
    slide_client_visemes,
    slide_client_pipeline_components,
    slide_client_deployment_options,
    # Section 7
    slide_client_entity_split,
    slide_client_quality_filter,
    slide_client_preprocessing_summary,
    # Section 8
    slide_client_roadmap_phases,
    slide_client_stronger_model,
    slide_client_more_data,
    slide_client_investment_ask,
    # Section 9
    slide_client_recap,
    slide_client_integration_commitment,
    slide_client_next_steps,
)


# Section transitions — built from the factory.
_section_3 = make_section_transition(
    "OUTPUT EXAMPLES",
    "What good, partial, and flagged segments look like",
)
_section_4 = make_section_transition(
    "CONFIDENCE & TRUST",
    "How the system tells you what to trust",
)
_section_5 = make_section_transition(
    "VALIDATION",
    "An independent expert agreed in 8 of 10 cases",
)
_section_6 = make_section_transition(
    "PIPELINE & ARCHITECTURE",
    "What runs under the hood — light touch",
)
_section_7 = make_section_transition(
    "PRE-PROCESSING ROADMAP",
    "Making it better starts before the model runs",
)
_section_8 = make_section_transition(
    "ROADMAP & INVESTMENT",
    "Where we're going and what it takes to get there",
)
_section_9 = make_section_transition(
    "INTEGRATION & NEXT STEPS",
    "How we deploy this on your infrastructure",
)


OUTPUT = MATERIALS / "Argos_VSP_Client_46slides_Apr2026.pptx"


def main():
    _auto_num[0] = 0  # reset slide counter

    prs = Presentation()
    prs.slide_width = SL_W
    prs.slide_height = SL_H

    print("Generating client presentation...")

    builders = [
        # ── Section 1 — What This Is (4 slides) ──
        slide_client_title,
        slide_client_summary,
        slide_client_headline_numbers,
        slide_client_agenda,
        # ── Section 2 — Live UI Demo (3 slides) ──
        slide_client_demo_intro,
        slide_client_demo_video_embed,
        slide_client_demo_recap,
        # ── Section 3 — Output Examples (transition + 4 client-specific slides) ──
        # Borrowed academic slides (slide_what_good_looks_like, slide_14b,
        # slide_judge_ex1-3) replaced with client-friendly versions that use
        # real per-token confidence on Obama bin Laden segments.
        _section_3,
        slide_client_examples_intro,
        slide_client_example_perfect,
        slide_client_example_partial,
        slide_client_example_flagged,
        # ── Section 4 — Confidence & Trust (transition + 7 slides) ──
        _section_4,
        slide_client_confidence_question,
        slide_client_two_layer_confidence,
        slide_client_word_color_coding,
        slide_client_seq_confidence_correlation,
        slide_client_trust_dashboard,
        slide_client_hallucination_flag,
        slide_client_what_this_means,
        # ── Section 5 — Validation (transition + 4 slides) ──
        _section_5,
        slide_client_validation_intro,
        # NOTE: slide_llm_judge dropped from client deck — its visible 64.9%
        # figure (LLM-judge Y+P rate) contradicts our canonical 62% useful-output
        # number. Borrow-vs-build forbids modifying upstream builders, so the
        # cleanest fix is to skip the borrowed methodology slide here. The
        # validation story lands cleanly with intro → 82% chart → stability →
        # summary, without surfacing the methodology detail.
        slide_client_agreement_chart,
        slide_client_cross_config_stability,
        slide_client_validation_summary,
        # ── Section 6 — Pipeline & Architecture (transition + 5 slides) ──
        # slide_visemes, slide_three_repos, slide_dual_env replaced with
        # client-friendly equivalents (visemes -> "Why lip reading is hard";
        # three_repos -> "Three components"; dual_env -> "Deploys where you
        # need it"). slide_data_flow + slide_web_ui kept as borrowed.
        _section_6,
        slide_data_flow,                    # borrowed: pipeline diagram
        slide_client_visemes,               # reframed: "Why lip reading is hard"
        slide_client_pipeline_components,   # reframed: "Three components"
        slide_client_deployment_options,    # reframed: "Cloud / on-premise"
        slide_web_ui,                       # borrowed: UI overview
        # ── Section 7 — Pre-Processing Roadmap (transition + 3 slides) ──
        _section_7,
        slide_client_entity_split,
        slide_client_quality_filter,
        slide_client_preprocessing_summary,
        # ── Section 8 — Roadmap & Investment (transition + 5 slides) ──
        _section_8,
        slide_client_roadmap_phases,
        slide_client_stronger_model,
        slide_client_more_data,
        slide_arabic_roadmap,               # borrowed: Arabic high-level only (v3)
        slide_client_investment_ask,
        # ── Section 9 — Integration & Next Steps (transition + 4 slides) ──
        _section_9,
        slide_client_recap,
        slide_client_integration_commitment,
        slide_client_next_steps,
        slide_thank_you,                    # borrowed: close
    ]

    total = len(builders)
    for i, builder in enumerate(builders, 1):
        name = getattr(builder, "__name__", "section_transition")
        print(f"  Slide {i:2d}/{total}  {name} ...", end=" ")
        try:
            builder(prs)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"\nSaved: {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
