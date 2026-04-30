#!/usr/bin/env python3
"""Argos VSP — Client Deck Generator (Round 5 — framing-v2 alignment).

Three-act 2-hour meeting structure per docs/CLIENT_MEETING_FRAMING_v2.md.
Calls existing builders from presentation/slides_*.py per the borrow-vs-
build policy in .claude/plans/i-need-to-create-proud-cupcake.md. Net-new
client builders live in presentation/slides_client.py.

Output:
    presentation_materials_20260224/Argos_VSP_Client_60slides_Apr2026.pptx
    (final count determined at build time)

Run:
    python3 docs/_research-tools/generators/generate_client_presentation.py
"""

from pathlib import Path

from pptx import Presentation

from presentation.config import SL_W, SL_H, _auto_num, MATERIALS

# ── Borrowed builders kept across rounds ────────────────────────────────
from presentation.slides_opening import (
    slide_data_flow,                    # pipeline overview (clean enough as-is)
)
from presentation.slides_engineering import (
    slide_web_ui,                       # UI overview
)
from presentation.slides_future import (
    slide_arabic_roadmap,               # Arabic high-level (v3 user feedback)
    slide_thank_you,                    # close
)

# ── Round-5 academic borrows ────────────────────────────────────────────
# Per the borrow research at /tmp/round5_borrow_report.md, all 12 slides
# pass the partner-audience N9 relaxation. Exempted in BORROWED_SLIDES.
from presentation.slides_evaluation import (
    slide_judge_ex1, slide_judge_ex2, slide_judge_ex3,
    slide_judge_ex4, slide_judge_ex5, slide_judge_ex6,
    slide_25d,                          # Salvage: 3 real recoveries
    slide_25e,                          # Salvage: domain context
)
from presentation.slides_research import (
    slide_08,                           # Failure-mode taxonomy bar chart
    slide_failure_deep_1a,              # Taxonomy 1/2 — top 3 modes
    slide_failure_deep_1b,              # Taxonomy 2/2 — bottom 2 modes
    slide_failure_deep_2,               # Taxonomy worked examples
)

# ── Net-new and reframed client builders ────────────────────────────────
from presentation.slides_client import (
    # Section 1 — Hello
    slide_client_title,
    slide_client_about_argos,

    # Section 2 — Background
    slide_client_what_is_vsr,

    # Section 3 — Compared to today (Round-5 anchor slide)
    slide_client_compared_to_today,

    # Section 4 — Why hard
    slide_client_visemes,

    # Section 5 — Basic idea
    slide_client_pipeline_components,

    # Section 6 — What we built
    slide_client_what_we_built,
    slide_client_engineering_journey,   # NEW Round 5

    # Section 7 — How to use it
    slide_client_demo_intro,
    slide_client_demo_video_embed,
    slide_client_demo_recap,

    # Section 8 — Real outputs
    slide_client_video_gallery,
    slide_client_examples_intro,
    slide_client_example_perfect,
    slide_client_example_partial,
    slide_client_example_flagged,

    # Section 9 — Headline
    slide_client_headline_numbers,

    # Section 10 — Why trust it
    slide_client_confidence_question,
    slide_client_two_layer_confidence,
    slide_client_word_color_coding,
    slide_client_halluc_problem,        # NEW Round 5
    slide_client_halluc_real_example,   # NEW Round 5
    slide_client_halluc_caught,         # NEW Round 5
    slide_client_seq_confidence_correlation,
    slide_client_trust_dashboard,
    slide_client_failure_taxonomy,      # NEW Round 5 (client wrapper for the academic block context)
    slide_client_failure_worked_example,  # NEW Round 5
    slide_client_hallucination_flag,    # summary stat
    slide_client_what_this_means,

    # Section 11 — Validation
    slide_client_validation_intro,      # rewritten Round 5 (protocol-named)
    slide_client_agreement_chart,
    slide_client_cross_config_stability,
    slide_client_validation_summary,

    # Section 12 — Engineering
    slide_client_deployment_options,

    # Section 13 — What's next
    slide_client_multi_speaker_today_vs_path,  # NEW Round 5 (replaces entity_split)
    slide_client_quality_filter,
    slide_client_preprocessing_summary,
    slide_client_data_ask,              # NEW Round 5 (replaces stronger_model + more_data + roadmap_phases)
    slide_client_investment_ask,        # rewritten Round 5 (partnership framing)

    # Section 14 — Close
    slide_client_recap,
    slide_client_integration_commitment,
    slide_client_next_steps,

    # Section transitions (factory)
    make_section_transition,
)

# Section transitions — only at major pivots, not between every section
_section_real_outputs = make_section_transition(
    "REAL OUTPUTS",
    "What the system actually produces, on real video",
)
_section_trust = make_section_transition(
    "WHY YOU CAN TRUST IT",
    "Per-word, per-segment, validated against an independent reviewer",
)
_section_validation = make_section_transition(
    "VALIDATION",
    "An independent reviewer agreed in 82% of cases",
)
_section_engineering = make_section_transition(
    "ENGINEERING UNDER THE HOOD",
    "What it actually takes to ship this",
)
_section_whats_next = make_section_transition(
    "WHAT'S NEXT",
    "The path to multi-speaker, more languages, your domain",
)


OUTPUT = MATERIALS / "Argos_VSP_Client_Round5_Apr2026.pptx"


def main():
    _auto_num[0] = 0  # reset slide counter

    prs = Presentation()
    prs.slide_width = SL_W
    prs.slide_height = SL_H

    print("Generating client presentation (Round 5 — framing-v2)...")

    builders = [
        # ═══════ ACT 1 — IT WORKS (0:00 – 0:30) ═══════
        # § Hello (2)
        slide_client_title,
        slide_client_about_argos,
        # § Background (1)
        slide_client_what_is_vsr,
        # § Compared to today — Round-5 anchor (1)
        slide_client_compared_to_today,
        # § Why hard (1)
        slide_client_visemes,
        # § Basic idea (1)
        slide_client_pipeline_components,
        # § What we built (2)
        slide_client_what_we_built,
        slide_client_engineering_journey,
        # § How to use it — Demo (3)
        slide_client_demo_intro,
        slide_client_demo_video_embed,
        slide_client_demo_recap,
        # § Real outputs — Section transition + gallery + 3 Obama + 6 judge_ex
        _section_real_outputs,
        slide_client_video_gallery,
        slide_client_examples_intro,
        slide_client_example_perfect,
        slide_client_example_partial,
        slide_client_example_flagged,
        # 6 academic-deck judge examples — borrowed, in BORROWED_SLIDES exemption
        slide_judge_ex1,
        slide_judge_ex2,
        slide_judge_ex3,
        slide_judge_ex4,
        slide_judge_ex5,
        slide_judge_ex6,
        # § Headline numbers — lands as summary, not opening
        slide_client_headline_numbers,

        # ═══════ ACT 2 — YOU CAN TRUST IT (0:38 – 1:18) ═══════
        _section_trust,
        slide_client_confidence_question,
        slide_client_two_layer_confidence,
        slide_client_word_color_coding,
        # Hallucination case-study trio
        slide_client_halluc_problem,
        slide_client_halluc_real_example,
        slide_client_halluc_caught,
        # Per-segment + sequence confidence
        slide_client_seq_confidence_correlation,
        slide_client_trust_dashboard,
        # Failure-mode taxonomy block (academic borrows + client wrappers)
        slide_client_failure_taxonomy,
        slide_08,                          # Borrowed: bar-chart taxonomy summary
        slide_failure_deep_1a,             # Borrowed: top-3 modes
        slide_failure_deep_1b,             # Borrowed: bottom-2 modes
        slide_client_failure_worked_example,
        slide_failure_deep_2,              # Borrowed: 3 real ref/hyp cases
        # Salvage examples (academic borrow)
        slide_25d,                         # Borrowed: 3 real recoveries
        slide_25e,                         # Borrowed: domain context
        # Summary stat + closer
        slide_client_hallucination_flag,
        slide_client_what_this_means,

        # § Validation
        _section_validation,
        slide_client_validation_intro,
        slide_client_agreement_chart,
        slide_client_cross_config_stability,
        slide_client_validation_summary,

        # ═══════ ACT 3 — PATH FORWARD (1:25 – 2:00) ═══════
        # § Engineering
        _section_engineering,
        slide_data_flow,                    # Borrowed: pipeline diagram
        slide_client_deployment_options,    # Cloud/on-prem
        slide_web_ui,                       # Borrowed: UI overview

        # § What's next — multi-speaker leads (the client's canonical case)
        _section_whats_next,
        slide_client_multi_speaker_today_vs_path,
        slide_client_quality_filter,
        slide_client_preprocessing_summary,
        slide_arabic_roadmap,               # Borrowed: high-level only
        slide_client_data_ask,
        slide_client_investment_ask,

        # § Close (no transition — flows directly from investment ask)
        slide_client_recap,
        slide_client_integration_commitment,
        slide_client_next_steps,
        slide_thank_you,                    # Borrowed: close
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
