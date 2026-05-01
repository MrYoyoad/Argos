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
    slide_thank_you,                    # close
)

# ── Round-5.1 academic borrows ──────────────────────────────────────────
# slide_judge_ex1-6 → replaced by slide_client_judge_ex1-6 (verdict tags
# instead of WER/WWER score strips per N9). The academic builders stay
# defined; we just don't import them here.
# slide_25e → DROPPED (jalapeno duplicates slide_client_judge_ex5).
# slide_failure_deep_1a + 1b → MERGED into slide_client_failure_taxonomy_full.
# slide_08 → DROPPED (duplicates the new failure_taxonomy slide).
# slide_arabic_roadmap → REPLACED by slide_client_arabic_high_level.
from presentation.slides_evaluation import (
    slide_25d,                          # Salvage: 3 real recoveries (Round 5.1: WER stripped from card headers)
)
from presentation.slides_research import (
    slide_failure_deep_2,               # Taxonomy worked examples (3 ref/hyp cards)
)

# ── Net-new and reframed client builders ────────────────────────────────
from presentation.slides_client import (
    # Section 1 — Hello
    slide_client_title,
    slide_client_about_argos,

    # Section 2 — Background (deepened in Round 5.1)
    slide_client_what_is_vsr,
    slide_client_what_is_lipreading_not,    # NEW Round 5.1
    slide_client_canonical_scenario,        # NEW Round 5.1 (coffee shop)

    # Section 3 — Compared to today
    slide_client_compared_to_today,
    slide_client_human_ceiling,             # NEW Round 5.1 (why 45-52%)

    # Section 4 — Why hard
    slide_client_visemes,

    # Section 5 — Basic idea
    slide_client_pipeline_components,

    # Section 6 — What we built (multi-speaker moved here in Round 5.1)
    slide_client_what_we_built,
    slide_client_engineering_journey,
    slide_client_multi_speaker_today_vs_path,   # MOVED UP from §13

    # Section 7 — How to use it
    slide_client_demo_intro,
    slide_client_demo_video_embed,
    slide_client_demo_recap,

    # Section 8 — Real outputs
    slide_client_video_gallery,
    # slide_client_examples_intro DROPPED (Round 5.1 — overlaps with deep examples)
    slide_client_example_perfect,
    slide_client_clean_outputs_gallery,     # NEW Round 5.1 (6-tile gallery of clean outputs)
    slide_client_example_partial,
    slide_client_example_flagged,
    # 6 client-side judge-example wrappers (verdict-tag instead of WER score strip)
    slide_client_judge_ex1,
    slide_client_judge_ex2,
    slide_client_judge_ex3,
    slide_client_judge_ex4,
    slide_client_judge_ex5,
    slide_client_judge_ex6,

    # Section 9 — Headline
    slide_client_headline_numbers,

    # Section 10 — Why trust it
    slide_client_confidence_question,
    slide_client_two_layer_confidence,
    slide_client_word_color_coding,
    slide_client_halluc_problem,
    slide_client_halluc_real_example,
    slide_client_halluc_caught,
    slide_client_seq_confidence_correlation,
    slide_client_trust_dashboard,
    slide_client_failure_taxonomy_full,     # NEW Round 5.1 (merged 1a+1b)
    slide_client_failure_worked_example,
    slide_client_hallucination_flag,
    slide_client_claims,                    # NEW Round 5.5 (credibility-hardening)
    slide_client_trust_without_ground_truth, # NEW Round 5.1 (deepest critique answer)
    slide_client_what_this_means,

    # Section 11 — Validation
    slide_client_validation_intro,
    slide_client_agreement_chart,
    slide_client_cross_config_stability,
    # slide_client_validation_summary DROPPED (Round 5.1 — restates 82% point)

    # Section 12 — Engineering (Round 5.2: bulked up)
    slide_client_pipeline_detailed,         # NEW Round 5.2 — 8-stage diagram from science deck
    slide_client_deployment_options,
    # slide_web_ui DROPPED (Round 5.1 — duplicate Live Demo placeholder)

    # Section 13 — What's next
    slide_client_quality_filter,
    slide_client_preprocessing_summary,
    slide_client_arabic_high_level,         # NEW Round 5.1 (replaces slide_arabic_roadmap)
    slide_client_partnership_ask,           # NEW Round 5.1 (merged data_ask + investment_ask)

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
        # § Hello
        slide_client_title,
        slide_client_about_argos,
        # § Background (deepened in Round 5.1)
        slide_client_what_is_vsr,
        slide_client_what_is_lipreading_not,    # NEW Round 5.1
        slide_client_canonical_scenario,        # NEW Round 5.1 (coffee shop)
        # § Compared to today — Round-5 anchor
        slide_client_compared_to_today,
        slide_client_human_ceiling,             # NEW Round 5.1 (why 45-52%)
        # § Why hard
        slide_client_visemes,
        # § Basic idea
        slide_client_pipeline_components,
        # § What we built — multi-speaker moved here in Round 5.1.
        # engineering_journey moved from here to §Engineering (Round 5.2) so
        # the engineering section carries the substantive depth instead of
        # a thin "what we did" footnote.
        slide_client_what_we_built,
        slide_client_multi_speaker_today_vs_path,   # MOVED UP from §13
        # § How to use it — Demo
        slide_client_demo_intro,
        slide_client_demo_video_embed,
        slide_client_demo_recap,
        # § Real outputs — Section transition + gallery + cleans + 3 Obama + 6 verdict-tagged
        _section_real_outputs,
        slide_client_video_gallery,
        slide_client_example_perfect,           # Obama segment 14 — perfect
        slide_client_clean_outputs_gallery,     # NEW Round 5.1 — 6 cleans
        slide_client_example_partial,           # Obama segment 31 — partial
        slide_client_example_flagged,           # Obama segment 5 — flagged
        # 6 client-wrapper judge examples (Round 5.1: verdict-tag instead of WER strip)
        slide_client_judge_ex1,
        slide_client_judge_ex2,
        slide_client_judge_ex3,
        slide_client_judge_ex4,
        slide_client_judge_ex5,
        slide_client_judge_ex6,
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
        # Failure-mode taxonomy (Round 5.1: 1a+1b merged into one slide)
        slide_client_failure_taxonomy_full,     # NEW Round 5.1 (replaces slide_08 + 1a + 1b)
        slide_client_failure_worked_example,
        slide_failure_deep_2,                   # Borrowed: 3 real ref/hyp cases
        # Salvage examples (Round 5.1: 25e dropped — jalapeno duplicates judge_ex5)
        slide_25d,                              # Borrowed: 3 real recoveries
        # Summary stat + the deepest-critique reframe + closer
        slide_client_hallucination_flag,
        slide_client_claims,                        # NEW Round 5.5 — claims/non-claims credibility-harden
        slide_client_trust_without_ground_truth,    # NEW Round 5.1
        slide_client_what_this_means,

        # § Validation (Round 5.1: validation_summary dropped)
        _section_validation,
        slide_client_validation_intro,
        slide_client_agreement_chart,
        slide_client_cross_config_stability,

        # ═══════ ACT 3 — PATH FORWARD (1:25 – 2:00) ═══════
        # § Engineering (Round 5.2: bulked up per user feedback — pipeline
        # diagram from science deck + engineering_journey moved here +
        # data_flow + deployment options. The engineering section now
        # carries real depth instead of a single architecture slide.)
        _section_engineering,
        slide_client_pipeline_detailed,         # NEW Round 5.2: 8-stage operational pipeline (height-bound)
        slide_data_flow,                        # Borrowed: 5-step model architecture (LoRA stripped)
        slide_client_engineering_journey,       # MOVED Round 5.2 from §What-we-built — deeper rewrite
        slide_client_deployment_options,        # Cloud/on-prem

        # § What's next (Round 5.1: data_ask + investment_ask merged into partnership_ask)
        _section_whats_next,
        slide_client_quality_filter,
        slide_client_preprocessing_summary,
        slide_client_arabic_high_level,         # NEW Round 5.1 (replaces academic arabic_roadmap)
        slide_client_partnership_ask,           # NEW Round 5.1 (merged ask)

        # § Close (no transition — flows directly from partnership ask)
        slide_client_recap,
        slide_client_integration_commitment,
        slide_client_next_steps,
        slide_thank_you,                        # Borrowed: close
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
