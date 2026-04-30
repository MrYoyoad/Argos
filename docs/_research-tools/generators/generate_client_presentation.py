#!/usr/bin/env python3
"""Argos VSP — Client Deck Generator.

Slim orchestrator (~150 lines) for the 53-slide client presentation.
Per the borrow-vs-build policy in
.claude/plans/i-need-to-create-proud-cupcake.md, this file IMPORTS and CALLS
existing builders from presentation/slides_*.py. The only net-new builders
live in presentation/slides_client.py.

Output:
    presentation_materials_20260224/Argos_VSP_Client_48slides_Apr2026.pptx

Run:
    python3 docs/_research-tools/generators/generate_client_presentation.py
"""

from pathlib import Path

from pptx import Presentation

from presentation.config import SL_W, SL_H, _auto_num, MATERIALS

# Borrow from existing slide modules. The borrow-vs-build policy is binding.
from presentation.slides_opening import (
    slide_visemes,        # accessible "what is lip reading" framing
    slide_data_flow,      # pipeline overview
)
from presentation.slides_evaluation import (
    slide_llm_judge,               # validation methodology
    slide_judge_ex1, slide_judge_ex2, slide_judge_ex3,  # 3 of 6 examples (subset)
    slide_14b,                     # video gallery
    slide_what_good_looks_like,    # gallery example slide (lives in evaluation, not research)
)
from presentation.slides_engineering import (
    slide_three_repos,             # engineering credibility
    slide_dual_env,                # two environments
    slide_web_ui,                  # UI overview
)
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


OUTPUT = MATERIALS / "Argos_VSP_Client_48slides_Apr2026.pptx"


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
        # ── Section 3 — Output Examples (transition + gallery) ──
        _section_3,
        slide_what_good_looks_like,
        slide_14b,
        slide_judge_ex1,
        slide_judge_ex2,
        slide_judge_ex3,
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
        slide_llm_judge,                    # borrowed: LLM-Judge methodology
        slide_client_agreement_chart,
        slide_client_cross_config_stability,
        slide_client_validation_summary,
        # ── Section 6 — Pipeline & Architecture (transition + 5 slides) ──
        _section_6,
        slide_data_flow,                    # borrowed
        slide_visemes,                      # borrowed
        slide_three_repos,                  # borrowed
        slide_dual_env,                     # borrowed
        slide_web_ui,                       # borrowed
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
