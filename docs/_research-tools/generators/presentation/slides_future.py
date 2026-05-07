"""
Slide builders — Section 8: Future Directions + Appendix
"""

from pathlib import Path
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

from .config import (
    IMG, VID, POSTER_DIR,
    SL_W, SL_H, BG, WHITE, TEAL, CORAL, LGRAY, MGRAY, DGRAY,
    GREEN, YELLOW, GOLD, ORANGE, RED, DRED, NAVY2, NAVY3,
    FONT, _auto_num,
    MX, MY, CT, CW, CH, SLW, SRG, SRL, SRW,
)
from .helpers import (
    new_slide, set_notes, add_logo, add_slide_num, add_accent_line,
    _fmt, add_title, add_text, add_rich_text, add_bullets,
    add_rect, add_image, add_play_button, add_video_poster, add_video,
    add_table, _shade_cell, _rgb_hex,
    add_fade_transition, add_animations, _finish,
    build_split, build_bullets, build_two_col, build_full_image,
)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 24 — REFRAMING THE STARTING POINT
# ═══════════════════════════════════════════════════════════════════════

def slide_24(prs):
    slide = new_slide(prs)
    add_title(slide, "Starting from 61.9%, Not 25%")  # audit:niv_yp_pct_mbr
    add_accent_line(slide)

    col_w = Inches(3.4)
    img_w = Inches(5.2)
    gap = Inches(0.25)

    # Left column — WER Says (coral)
    r1 = add_rect(slide, MX, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=CORAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "WER Says", MX + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=CORAL, bold=True)
    add_bullets(slide, [
        "25.5% useful by WER (<30%, uncalibrated bucket)",  # audit:logic_fix slide 11
        "~3 in 4 segments fail by this cut",
        "Ignores phonetic preservation (41.5%)",
    ], MX + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=CORAL)

    # Middle column — IS Says (teal)
    mx2 = MX + col_w + gap
    r2 = add_rect(slide, mx2, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "IS Says", mx2 + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=TEAL, bold=True)
    add_bullets(slide, [
        # audit:niv_yp_pct_mbr / audit:niv_yp_pct_top1
        ("61.92% useful output (IS \u2265 2.00, MBR); top-1 baseline 61.66%",
         {"bold": True}),
        ("64.9% useful per Opus-as-a-Judge v1 blind "
         "(Y+P = 971/1,497, Opus 4.6, gold standard)",
         {"color": GREEN}),
        # audit:cross_config_includes_mbr=False
        ("Validated across 16 top-1 decode-parameter configs (r=0.925); "
         "MBR validation is the v3 paired Judge test, not the cross-config sweep",
         {}),
        "Pearson r = 0.85 between top-1 IS and Opus v1 verdicts",
    ], mx2 + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.5), size=Pt(12), bullet_color=TEAL)

    # Right — larger image
    img = add_image(slide, "P1_quality", MX + 2 * col_w + 2 * gap, CT - Inches(0.1),
                    width=img_w)

    # Bottom
    add_text(slide,
             "The gap is real \u2014 but WER dramatically overstates failure. "
             "61.92% useful by IS (Y+P, MBR), 64.9% confirmed by v1 blind "
             "Opus-as-a-Judge.",  # audit:niv_yp_pct_mbr
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 24,
        "This is the turning point. WER says 25.5% useful (uncalibrated <30% "
        "cut). Our Intelligibility Score says 61.92% useful output (NIV Y+P, "
        "MBR; top-1 baseline 61.66%) — roughly 2.4x more. WER correlates "
        "with IS (r ~ -0.7) but not perfectly — it misses phonetic and "
        "semantic preservation entirely. The bullet about phonetic "
        "preservation refers to the segment population where WER is "
        "discarding meaning that survives in the phonetic axis (mean "
        "phonetic similarity 41.5% across the failure set). "
        "Opus-as-a-Judge v1 blind (Opus 4.6, gold standard) confirms 64.9% "
        "useful output (Y+P = 971 of 1,497). Cross-config sweep is "
        "top-1-only (r=0.925 across 16 decode-parameter configs); MBR "
        "validation is the v3 paired Judge test in the next subsection. "
        "Mention to peers: this slide is the framing for everything in "
        "Section 5 — the roadmap is calibrated against IS, not WER. "
        "Sources: docs/evaluation/is_cross_config_validation.md, "
        "docs/evaluation/after_amosi_audit.md (Section F).",
        [[r1], [r2, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

def slide_26(prs):
    slide = new_slide(prs)
    add_title(slide, "Five Phases \u2014 From IS 2.5 to Target IS 3.3\u20133.7")
    add_accent_line(slide)

    # IS deltas derived from 574 non-useful segments (IS < 2.00) failure taxonomy.
    # audit:is_mean_mbr — Conversion: ~0.033 IS per pp WER
    # (empirical: 2.547 IS @ 63.84% WER MBR to ~3.81 IS @ 25.4% WER paper).
    # Per-category signal profiles from signal_distribution_analysis.md §8.
    # NOTE: Phases 1+2 already shipped by May 2 2026 (per audit:logic_fix
    # slide 41 / 59); remaining staircase is Phases 3-5.
    phases = [
        ("Phase 1 (shipped)", "Surface the good 62%",
         "Confidence scoring \u2014 flags known-good segments (shipped Apr 30 2026)",
         "Targets: Signal Loss (80, 13.9%) | IS: perceived only (filtering, no recovery)", TEAL),
        ("Phase 2 (shipped)", "Fix small & content errors",
         "N-best aggregation MBR (shipped May 2 2026; ROVER as alternative)",
         "Targets: Accum. Errors (52, 9.1%) + Details (79, 13.8%) | IS: +0.13 (\u223c35 segs)", TEAL),
        ("Phase 3", "Better world knowledge",
         "Llama 3.1 8B + context prompts",
         "Targets: Halluc (108, 18.8%) + Wrong Topic (255, 44.4%) | IS: +0.40 (\u223c98 segs)", GREEN),
        ("Phase 4", "Scale data 20K\u201350K",
         "Fine-tune visual encoder + projection on more data",
         "Targets: ALL 574 non-useful via better visual features | IS: +0.35", GREEN),
        ("Phase 5", "Error Correction (GER)",
         "Second LLM corrects remaining decode errors",
         "Targets: residual errors post-Phase 1\u20134 | IS: +0.10", LGRAY),
    ]

    # Staircase on left side
    step_w = Inches(5.8)
    step_h = Inches(0.95)
    step_indent = Inches(0.35)
    start_y = CT - Inches(0.05)
    start_x = MX

    step_shapes = []
    for i, (phase, desc, detail, is_note, color) in enumerate(phases):
        x = start_x + i * step_indent
        y = start_y + i * (step_h + Inches(0.04))
        w = step_w - i * step_indent
        r = add_rect(slide, x, y, w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        step_shapes.append(r)
        step_shapes.append(add_rich_text(slide, [
            [(phase, {"size": Pt(13), "color": color, "bold": True}),
             (f"  {desc}", {"size": Pt(13), "color": WHITE})],
            [(detail, {"size": Pt(12), "color": LGRAY, "italic": True}),
             (f"   {is_note}", {"size": Pt(12), "color": GOLD})],
        ], x + Inches(0.2), y + Inches(0.05), w - Inches(0.4), step_h - Inches(0.1)))

    # WER trajectory image on right
    img = add_image(slide, "P3_trajectory",
                    SRL - Inches(0.2), CT, width=SRW + Inches(0.2))

    # audit:logic_fix slide 71 \u2014 phase deltas are additive, not multiplicative.
    # The ICLR 2024 reference (Biderman et al.) is about LoRA scaling, not
    # combining decode/aggregation/data-scaling phases.
    bottom = add_text(slide,
             # audit:is_mean_mbr \u2014 baseline is 2.547 under MBR n-best.
             "Combined target: IS 3.3\u20133.7 (~80\u201385% useful Y+P). "
             "Phase deltas sum to +0.98 from 2.547 baseline \u2014 additive "
             "under the IS-component model. Where phases overlap (e.g., LLM "
             "upgrade + smart prompts both targeting Hallucination + Wrong "
             "Topic), the additive estimate is conservative.",
             MX, Inches(6.35), CW, Inches(0.55),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Academic references — LoRA scaling cited only for Phase 4 (data scaling),
    # not for combining phases (audit:logic_fix slide 71). Bumped to 12pt for
    # readability floor; abbreviated and lifted upward to fit (y=6.94, h=0.22
    # = ends 7.16 — slide num starts at 7.12 but is positioned at MX..MX+0.5,
    # so left-offset MX+1.0 keeps it horizontally clear). Full "(Biderman et
    # al. 2024)" attribution moved to speaker notes.
    add_text(slide,
        "References: ROVER 1997  |  GER 2024  |  LoRA Scaling 2024",
        MX + Inches(1.0), Inches(6.94), CW - Inches(1.0), Inches(0.22),
        size=Pt(12), color=MGRAY, italic=True)

    _finish(slide, 26,
        "Five phases targeting 574 non-useful segments (IS < 2.00, "
        "approximately 38% of the 1,497-segment evaluation set) drawn from "
        "our failure taxonomy. Headline: starting from 62% useful (NIV "
        "Y+P, IS 2.547 under MBR n-best), the staircase targets an "
        "improvement to 80-85% useful at IS 3.3-3.7.\n\n"
        "DERIVATION (signal profiles from signal_distribution_analysis.md):\n"
        "Phase 1 (Confidence): Targets Signal Loss (80 segs, 13.9% of "
        "the failure pool) by surfacing the high-confidence slice — "
        "perceived improvement only, no IS change. 2-4 hours.\n"
        "Phase 2 (N-Best): Targets Accum. Errors (52 segs, 9.1%, "
        "IS~2.33, Phonetic 0.53 / InvWER 0.34 — small distributed fix) "
        "+ Right Topic Wrong Details (79 segs, 13.8%, IS~2.13, NEA 0.18 "
        "— needs +0.35 NEA). ROVER 5-8% relative WER reduction (Fiscus "
        "1997). ~35 segs recovered. IS +0.13.\n"
        "Phase 3 (LLM Swap): Targets Hallucination (108 segs = 18.8% of "
        "the failure pool, IS~0.87, InvWER -0.47 / LR 1.56 — needs "
        "WER+length normalization) + Wrong Topic (255 segs = 44.4%, "
        "IS~1.29, Semantic 0.10 — needs +0.45 Semantic). VALLR (ICCV "
        "2025) showed 26% relative WER improvement. ~98 segs. IS +0.40.\n"
        "Phase 4 (Data Scaling): All 574 benefit from better visual "
        "features. ICLR 2024 LoRA scaling law applies to Phase 4 only. "
        "IS +0.35.\n"
        "Phase 5 (GER): Residual correction. Chen et al. 2024. IS +0.10.\n\n"
        "Combined: +0.98 IS -> target IS 3.3-3.7 (80-85% useful Y+P). "
        "Where phases overlap (e.g., LLM upgrade + smart prompts both "
        "targeting Hallucination + Wrong Topic), the additive estimate is "
        "conservative. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/after_amosi_audit.md (Section F).",
        [step_shapes, [img, bottom]], click_reveal=True)


def slide_26b(prs):
    """26b: IS trajectory roadmap — parallel to WER trajectory on slide_26."""
    slide = new_slide(prs)
    add_title(slide, "IS Improvement Roadmap \u2014 From 2.5 to 3.5")
    add_accent_line(slide)

    add_text(slide, "Projected Intelligibility Score improvement per phase",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # IS trajectory plot (left side, large)
    img = add_image(slide, "P3b_is_trajectory",
                    MX, CT + Inches(0.40),
                    width=Inches(7.6))

    # Key milestones callout (right side) — with failure mode annotations
    # IS deltas derived from 574-segment taxonomy × per-category recovery rates.
    # Per-category current IS (from signal profiles):
    #   Accum Errors IS~2.33, Details IS~2.13, Wrong Topic IS~1.29,
    #   Hallucination IS~0.87, Signal Loss IS~0.01
    rx = MX + Inches(8.3)
    rw = Inches(3.8)
    # audit:is_mean_mbr (2.547) / audit:niv_yp_pct_mbr (61.92%) \u2014
    # update Current to MBR-default values; phase forecasts unchanged.
    milestones = [
        ("Current", "IS 2.547", "61.92% useful (Y+P)", "", CORAL),
        ("Phase 1\u20132", "IS ~2.65",  "~65% useful (Y+P)",
         "Fixes: Accum (52) + Details (79) \u2014 131/574 targeted", TEAL),
        ("+ Phase 3", "IS ~3.05", "~73% useful (Y+P)",
         "Fixes: Halluc (108) + Wrong Topic (255) \u2014 363/574 targeted", GREEN),
        ("+ Phase 4\u20135", "IS ~3.50", "~82% useful (Y+P)",
         "Fixes: all remaining via data + GER post-correction", GREEN),
    ]
    ms_shapes = []
    for i, (phase, is_val, cap_val, failure_note, color) in enumerate(milestones):
        y = CT + Inches(0.45) + i * Inches(1.25)
        card_h = Inches(1.10) if i > 0 else Inches(0.85)
        ms_shapes.append(add_rect(slide, rx, y, rw, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True))
        ms_shapes.append(add_text(slide, phase, rx + Inches(0.15), y + Inches(0.05),
                 rw - Inches(0.3), Inches(0.3),
                 size=Pt(13), color=color, bold=True))
        ms_shapes.append(add_text(slide, f"{is_val}  \u2022  {cap_val}",
                 rx + Inches(0.15), y + Inches(0.35),
                 rw - Inches(0.3), Inches(0.3),
                 size=Pt(16), color=WHITE, bold=True))
        if i > 0:
            delta = float(is_val.replace("IS ~", "")) - 2.547  # audit:is_mean_mbr
            ms_shapes.append(add_text(slide, f"+{delta:.2f}  |  {failure_note}",
                     rx + Inches(0.15), y + Inches(0.65),
                     rw - Inches(0.3), Inches(0.40),
                     size=Pt(12), color=WHITE, italic=True))

    # audit:is_mean_mbr (2.547) \u2014 bottom conversion uses MBR-anchored values.
    # Moved from y=6.35 (overlapped milestone i=3 footer at y=6.30..6.65) to
    # y=6.85, just below the last milestone card (ends 6.75) and clear of the
    # slide number (starts 7.12). Audit flagged 86% occlusion of TextBox 19.
    bottom = add_text(slide,
             "Conversion: ~0.033 IS per pp WER (empirical: 2.547 IS @ 63.84% WER MBR \u2192 ~3.81 IS @ 25.4% WER paper).",
             MX, Inches(6.82), CW, Inches(0.30),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS trajectory derived from 574 non-useful segments (IS < 2.00).\n"
        "Current IS 2.547 (61.92% useful, NIV Y+P, MBR n-best). "
        "See docs/evaluation/after_amosi_audit.md (Section F).\n"
        "Phase 1-2: IS ~2.65 (~65% useful). N-Best ROVER/MBR targets Accum Errors "
        "(52 segs, IS~2.33, Phonetic 0.53/InvWER 0.34) + Right Topic Wrong "
        "Details (79 segs, IS~2.13, NEA 0.18). ~35 segs recovered.\n"
        "Phase 3: IS ~3.05 (~73% useful). LLM swap targets Hallucination "
        "(108 segs, IS~0.87, InvWER -0.47/LR 1.56) + Wrong Topic "
        "(255 segs, IS~1.29, Semantic 0.10). ~98 segs recovered.\n"
        "Phase 4-5: IS ~3.50 (~82% useful). Data scaling improves visual "
        "encoder for ALL categories. GER post-correction for residual.\n"
        "Conversion: ~0.033 IS per pp WER (2.547 IS @ 63.84% WER MBR to ~3.81 IS @ 25.4% WER paper).",
        [[img], ms_shapes + [bottom]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

def slide_27(prs):
    """Phase 1 summary — brief recap (detail now on slide_confidence_scoring)."""
    slide = new_slide(prs)
    add_title(slide, "Confidence Scoring \u2014 Summary")
    add_accent_line(slide)

    # Single concise summary
    add_bullets(slide, [
        ("Beam scores are already computed \u2014 just surface them",
         {"bold": True, "size": Pt(18)}),
        ("2\u20134 hours to implement, zero retraining",
         {"color": GREEN, "bold": True, "size": Pt(18)}),
        ("Perceived error rate: 60% \u2192 ~20%",
         {"color": TEAL, "bold": True, "size": Pt(18)}),
        ("Targets Signal Loss failure mode (13.9% of errors)",
         {"size": Pt(16)}),
    ], MX, CT + Inches(0.3), CW, Inches(3.0), size=Pt(16))

    # Quick visual callout
    r1 = add_rect(slide, MX + Inches(1.5), CT + Inches(3.5),
                  CW - Inches(3.0), Inches(0.7),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Fastest path to user value \u2014 Phase 1 is a quick win",
             MX + Inches(1.8), CT + Inches(3.55), CW - Inches(3.6), Inches(0.6),
             size=Pt(18), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 27,
        # audit:narrative — generic cross-reference (no hard slide number).
        "Brief summary of confidence scoring. Detail covered in the merged "
        "confidence-scoring slide elsewhere in this section. "
        "Key points: beam scores already exist, 2-4 hours implementation, "
        "perceived error rate drops from 60% to 20%.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

def slide_28(prs):
    """N-best Aggregation \u2014 MBR shipped May 2 2026 as production default."""
    slide = new_slide(prs)
    add_title(slide, "N-best Aggregation: From One to All 20 Hypotheses (Mission 6)")
    add_accent_line(slide)

    # Main point \u2014 past tense, MBR is shipped (audit:logic_fix #1, slide 59).
    # audit:narrative \u2014 generic cross-reference (no hard slide number).
    add_text(slide,
             "Until May 2 2026 we displayed only the top-1 hypothesis. "
             "Mission 6 shipped MBR aggregation as the production default \u2014 "
             "the v3 paired Judge test below quantifies the lift.",
             MX, CT, CW, Inches(0.7), size=Pt(14), color=WHITE, bold=True)

    # Two technique cards side by side
    cw = Inches(5.5)
    gap = Inches(1.13)
    cy = CT + Inches(0.85)
    ch = Inches(2.2)

    r1 = add_rect(slide, MX, cy, cw, ch, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "ROVER (alternative)", MX + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=TEAL, bold=True)
    add_text(slide, "Recognizer Output Voting Error Reduction",
             MX + Inches(0.2), cy + Inches(0.42), cw - Inches(0.4), Inches(0.28),
             size=Pt(12), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Align all 20 hypotheses word-by-word",
        "Vote at each position \u2014 most common word wins",
        "Reduces random substitution errors",
    ], MX + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    rx = MX + cw + gap
    r2 = add_rect(slide, rx, cy, cw, ch, fill_color=NAVY2,
                  border_color=GREEN, border_width=Pt(2), corner_radius=True)
    add_text(slide, "MBR (shipped, default)", rx + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=GREEN, bold=True)
    add_text(slide, "Minimum Bayes Risk Decoding",
             rx + Inches(0.2), cy + Inches(0.42), cw - Inches(0.4), Inches(0.28),
             size=Pt(12), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Score each hypothesis against ALL others",
        "Pick the one most similar to the consensus",
        "Best single hypothesis, no alignment needed",
    ], rx + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    # Impact summary \u2014 measured, not expected (audit:judge_v3_yp_pct_mbr,
    # audit:judge_v3_yp_pct_baseline, audit:mcnemar_yp_p_mbr)
    iy = cy + ch + Inches(0.3)
    impact = add_bullets(slide, [
        ("Measured v3 paired Judge: MBR Y+P 71.08% vs baseline 68.40% "
         "(p = 0.00017 paired McNemar)",
         {"color": GREEN, "bold": True}),  # audit:judge_v3_yp_pct_mbr
        "Targets: Accumulated Errors (9.1%) \u2014 the \"death by a thousand cuts\" category",
        "WER reduction: \u22121.56 pp on hyp_vote_conf; MBR is best on calibrated per-word posterior",
    ], MX, iy, CW, Inches(1.5), size=Pt(14))

    # Academic references — bumped to 12pt for readability floor; shifted up
    # slightly to fit footer band.
    add_text(slide,
        "ROVER: Fiscus 1997  |  MBR: Kumar & Byrne 2004",
        MX, Inches(6.40), CW, Inches(0.32),
        size=Pt(12), color=MGRAY, italic=True)

    _finish(slide, 28,
        "N-best aggregation. Until May 2 2026 the pipeline kept only the top-1 "
        "hypothesis and discarded 19 alternatives. Mission 6 shipped MBR "
        "aggregation as production default on May 2 2026: the v3 paired Judge "
        "test (Opus 4.7, dual-conf prompt) measured Y+P = 71.08% for MBR vs "
        "68.40% for the top-1 baseline (p = 0.00017 paired McNemar). MBR was "
        "preferred over voting variants because it emits a calibrated per-word "
        "posterior that integrates with the band-reliability UI. ROVER remains "
        "as a reference alternative. Targets the Accumulated Errors category "
        "(9.1% of failures). See docs/beam-search/n_best_implementation.md "
        "and docs/evaluation/after_amosi_audit.md (Section F).",
        [[r1], [r2], [impact]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

def slide_29(prs):
    slide = new_slide(prs)
    add_title(slide, "Fine-Tuning: Limited Data, Limited Gains")
    add_accent_line(slide)

    # Two plots side by side — reduced height to leave room for text
    col_w = Inches(5.9)
    gap = Inches(0.33)
    plot_h = Inches(3.8)
    rx = MX + col_w + gap

    img_l = add_image(slide, "ft_loss", MX, CT, width=col_w, height=plot_h)
    img_r = add_image(slide, "ft_impact", rx, CT, width=col_w, height=plot_h)

    # Key findings below plots — with more room
    find_y = CT + plot_h + Inches(0.15)
    lb = add_bullets(slide, [
        ("LoRA on 1,273 segments: IS 2.49 \u2192 2.31 (r=16) \u2192 2.02 (r=64) \u2014 "
         "fine-tuning made IS WORSE", {"bold": True, "color": CORAL}),
        ("Bottleneck is data quantity (need 20K+), not parameter tuning",
         {"bold": True, "color": GREEN}),
    ], MX, find_y, CW, Inches(1.2), size=Pt(15))

    _finish(slide, 29,
        "Fine-tuning experiments with LoRA on 1,273 AVSpeech segments — "
        "the limit of what we could prepare in our window. Graphs are "
        "enlarged for visibility. Exp A (rank 16): best validation at "
        "epoch 2, then overfitting (~95% train, ~60% val accuracy). Exp B "
        "(rank 64): 3.1 percentage points worse on validation than Exp A. "
        "Claude-as-Judge evaluation on 224 validation segments: baseline "
        "IS 2.487, Exp A IS 2.312, Exp B IS 2.023. Empty-output rate rose "
        "from 7.1% (baseline) to 12.5% (Exp A) to 26.8% (Exp B). LLM "
        "Y+P stayed in the 51-54% band across all three configs — "
        "fine-tuning did not improve outcomes. The bottleneck is data "
        "quantity (need 20K+ segments, not 1.3K), not parameter tuning. "
        "Mention to peers: this is a data-limited result; a stronger LLM "
        "backbone with 20K-50K segments is expected to produce "
        "substantially better numbers. "
        "Sources: docs/finetuning/training-research-notes.md, "
        "docs/evaluation/llm_upgrade_analysis.md.",
        [[img_l, img_r], [lb]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30 — LLM UPGRADE + ADVANCED CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30 — LLM UPGRADE + ADVANCED CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════

def slide_30(prs):
    slide = new_slide(prs)
    add_title(slide, "Stronger LLM + Smart Prompts = Force Multiplier")
    add_accent_line(slide)

    cols = [
        ("LLM Upgrade (requires training)", [
            "Llama 3.1 8B: drop-in (same hidden_size 4096)",
            "Quality ≈ Llama-2 70B, 128K vocab, 128K context",
            ("Training: ~2\u20134 weeks with 5K+ segments", {"bold": True}),
            "Alone: -3 to -8pp WER",
        ], TEAL),
        ("Smart Prompts (force multiplier)", [
            "7 strategies: topic context, word count, anti-hallucination, GER",
            "Llama-2: +5-10pp | Llama 3.1: +12-20pp",
            ("GER = Generative Error Correction: feed N-best hypotheses "
             "to a correction LLM that fixes errors", {"color": LGRAY}),
            ("GER post-processing: +8-15pp, no retraining", {"color": GREEN}),
        ], CORAL),
        ("Future", [
            "Arabic (K-means model exists)",
            "Multi-speaker, streaming",
        ], LGRAY),
    ]

    cw = Inches(3.6)
    gap = Inches(0.5)
    total = 3 * cw + 2 * gap
    cx = (SL_W - total) / 2

    col_groups = []
    for i, (title, items, color) in enumerate(cols):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, CT, cw, Inches(4.8), fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t = add_text(slide, title, x + Inches(0.2), CT + Inches(0.15),
                 cw - Inches(0.4), Inches(0.45),
                 size=Pt(15), color=color, bold=True, align=PP_ALIGN.CENTER)
        b = add_bullets(slide, items, x + Inches(0.2), CT + Inches(0.7),
                    cw - Inches(0.4), Inches(3.5), size=Pt(13))
        col_groups.append([r, t, b])

    # Academic references — bumped to 12pt for readability floor; venue
    # tags ("ICASSP", "NeurIPS (Chinchilla)") moved to speaker notes so the
    # one-line footer fits.
    add_text(slide,
        "GER: Chen et al. 2024  |  Scaling Laws: Hoffmann et al. 2022",
        MX, Inches(6.50), CW, Inches(0.34),
        size=Pt(12), color=MGRAY, italic=True)

    _finish(slide, 30,
        "Three columns of future capability. Left: LLM swap to Llama 3.1 "
        "8B is drop-in — same hidden dimension. Center: 7 prompt "
        "strategies are a force multiplier — more effective on stronger "
        "models. GER uses N-best hypotheses + correction LLM for +8-15pp "
        "with no retraining. Right: Arabic support planned, multi-speaker "
        "and streaming as future extensions.\n\n"
        "WHY 3-8pp WER IMPROVEMENT JUST FROM CHANGING THE LLM:\n"
        "The visual encoder outputs ambiguous feature sequences — multiple "
        "English words look identical on the lips (homophenes). The LLM's job "
        "is to disambiguate using language context. Llama-2 7B has a 32K "
        "vocabulary and was trained on older data. Llama 3.1 8B has 128K "
        "vocabulary (4x), trained on 15T tokens (7.5x more), and vastly better "
        "instruction following. This means:\n"
        "- Better vocabulary coverage → fewer unknown-word hallucinations\n"
        "- Stronger language model → better disambiguation of homophenes\n"
        "- More world knowledge → correct entity names more often\n"
        "- The 3-8pp range comes from published ASR/NLP benchmarks showing "
        "Llama 3 8B performs at roughly Llama-2 70B level. Since the visual "
        "encoder is unchanged, the improvement is purely from better language "
        "decoding of the same visual features. The lower end (3pp) assumes "
        "the visual bottleneck limits gains; the upper end (8pp) assumes "
        "language disambiguation is the primary bottleneck for our failure "
        "modes. Mention to peers: this is the framing for the quantified "
        "LLM-upgrade slide that follows. "
        "Sources: docs/evaluation/llm_upgrade_analysis.md, "
        "docs/finetuning/training-research-notes.md.",
        col_groups)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30b — LLM UPGRADE: QUANTIFIED IMPACT
# ═══════════════════════════════════════════════════════════════════════

def slide_30b(prs):
    """Why upgrading from Llama-2-7B to Llama 3.1 8B matters — quantified."""
    slide = new_slide(prs)
    add_title(slide, "LLM Upgrade: Why It Matters")
    add_accent_line(slide)

    gap = Inches(0.6)
    left_w = Inches(5.7)
    right_w = CW - left_w - gap
    rx = MX + left_w + gap

    # ── Left column: capability table + VALLR one-liner ──
    lt = add_text(slide, "Llama-2 7B \u2192 Llama 3.1 8B",
                  MX, CT, left_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)

    tbl_headers = ["", "Current", "Upgrade", ""]
    tbl_rows = [
        ["MMLU",        "45%",    "73%",     "+61%"],
        ["Vocabulary",  "32K",    "128K",    "4\u00d7"],
        ["Context",     "4K",     "128K",    "32\u00d7"],
        ["Training",    "2T tok", "15T tok",  "7.5\u00d7"],
    ]
    tbl = add_table(slide, tbl_headers, tbl_rows,
                    MX, CT + Inches(0.50), left_w,
                    row_height=Inches(0.42),
                    col_widths=[Inches(1.3), Inches(1.2), Inches(1.4), Inches(1.8)],
                    text_size=Pt(14))

    # VALLR callout — single compact box
    vy = CT + Inches(2.75)
    vallr_box = add_rect(slide, MX, vy, left_w, Inches(0.85),
                         fill_color=NAVY2, border_color=GREEN,
                         border_width=Pt(2), corner_radius=True)
    vallr_text = add_text(slide,
        "VALLR (ICCV 2025): Llama 3.2-3B achieved 18.7% WER\n"
        "on LRS3 \u2014 beats our 7B Llama-2 (25.4%) with half the params",
        MX + Inches(0.25), vy + Inches(0.12),
        left_w - Inches(0.5), Inches(0.65),
        size=Pt(14), color=WHITE)

    # Drop-in callout
    drop_y = CT + Inches(3.85)
    drop_text = add_text(slide,
        "Same hidden dimension (4096) = architecture-compatible upgrade, requires adapter retraining",
        MX, drop_y, left_w, Inches(0.35),
        size=Pt(14), color=LGRAY, italic=True)

    # ── Right column: WER waterfall ──
    rt = add_text(slide, "Projected Impact",
                  rx, CT, right_w, Inches(0.35),
                  size=Pt(18), color=CORAL, bold=True)

    waterfall = [
        ("Current WER",         "64%",       CORAL),
        ("LLM swap alone",      "\u22123\u20138 pp",   LGRAY),
        ("+ Smart prompts",     "\u22125\u201310 pp",   LGRAY),
        ("+ 20K segments",      "\u221210\u201315 pp",  LGRAY),
        ("Target WER",          "35\u201340%",   GREEN),
    ]

    wy = CT + Inches(0.55)
    row_h = Inches(0.65)
    wf_shapes = []
    for label, value, clr in waterfall:
        r = add_rect(slide, rx, wy, right_w, row_h - Inches(0.08),
                     fill_color=NAVY2, border_color=clr,
                     border_width=Pt(1.5), corner_radius=True)
        # OVERLAP fix: shrink t1 width so it does not extend into t2's bbox.
        # Previously t1 ended at rx+right_w-1.4 while t2 started at
        # rx+right_w-1.5 — a 0.1" horizontal overlap. New t1 width =
        # right_w-1.8 ends at rx+right_w-1.6, leaving a 0.1" gap.
        t1 = add_text(slide, label,
                      rx + Inches(0.2), wy + Inches(0.10),
                      right_w - Inches(1.8), Inches(0.35),
                      size=Pt(14), color=WHITE)
        t2 = add_text(slide, value,
                      rx + right_w - Inches(1.5), wy + Inches(0.10),
                      Inches(1.3), Inches(0.35),
                      size=Pt(16), color=clr, bold=True,
                      align=PP_ALIGN.RIGHT)
        wf_shapes.append([r, t1, t2])
        wy += row_h

    # Key insight below waterfall
    ky = wy + Inches(0.15)
    key_box = add_rect(slide, rx, ky, right_w, Inches(0.75),
                       fill_color=NAVY2, border_color=TEAL,
                       border_width=Pt(2), corner_radius=True)
    key_text = add_text(slide,
        "Strongest LLM impact: entity disambiguation\n"
        "(79 segments) and accumulated errors (52 segments)",
        rx + Inches(0.2), ky + Inches(0.10),
        right_w - Inches(0.4), Inches(0.55),
        size=Pt(13), color=WHITE)

    _finish(slide, 0,
        "LLM upgrade analysis — simplified view. The waterfall maps from "
        "our current 64% baseline WER (top-1) to a projected 35-40% target "
        "via three stacked levers: an LLM swap, smart prompts, and 20K "
        "additional training segments.\n\n"
        "LEFT: Capability gap table. Llama 3.1 8B has 4x vocabulary, "
        "32x context, 7.5x training data, +61% on MMLU. Same hidden "
        "dimension (4096) = architecture-compatible upgrade (requires adapter retraining).\n\n"
        "VALLR PROOF (ICCV 2025): Llama 3.2-3B (only 3B params) achieved "
        "18.7% WER on LRS3 vs our 25.4% with Llama-2-7B. A smaller Llama 3 "
        "model beats a bigger Llama 2 — proves the architecture upgrade "
        "is more important than parameter count.\n\n"
        "RIGHT: WER improvement waterfall.\n"
        "- LLM swap alone: -3 to -8pp (modest, because visual encoder is "
        "the primary bottleneck — no LLM can decode what the encoder misses)\n"
        "- + Smart prompts: -5 to -10pp (Llama 3.1 UNLOCKS strategies that "
        "Llama-2 cannot follow: topic context, anti-hallucination guards, "
        "vocabulary lists, phonetic hints)\n"
        "- + 20K segments: -10 to -15pp (multiplicative scaling law from "
        "ICLR 2024 — better model extracts MORE from same data)\n"
        "- Combined target: 35-40% WER = roughly halving the error rate\n\n"
        "FAILURE MODES MOST HELPED (574 below-threshold, IS < 2.00):\n"
        "- Wrong Topic (255 segments, 10-20% recovery): dominant category "
        "(44.4%), only helps when some visual signal exists; total drift = encoder failure\n"
        "- Hallucination (108 segments, 15-25% recovery): better calibrated "
        "model less likely to 'run ahead' of visual signal\n"
        "- Signal Loss (80 segments, <5%): encoder-level, LLM cannot help\n"
        "- Right Topic Wrong Details (79 segments, 25-35% recovery): "
        "encoder captured the right domain but LLM picked wrong words\n"
        "- Accumulated Errors (52 segments, 20-30% recovery): many small "
        "substitutions that compound — better context modeling catches them\n\n"
        "REFERENCES: VALLR (Thomas et al., ICCV 2025), "
        "Scaling Laws (Zhang et al., ICLR 2024), Llama 3 (Meta, 2024). "
        "Sources: docs/evaluation/llm_upgrade_analysis.md, "
        "docs/finetuning/training-research-notes.md.",
        [[lt, tbl],
         [vallr_box, vallr_text],
         [drop_text],
         [rt] + wf_shapes[0],
         *wf_shapes[1:],
         [key_box, key_text]],
        click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30c — LLM UPGRADE: FAILURE MODE DETAIL (hidden backup)
# ═══════════════════════════════════════════════════════════════════════

def slide_30c(prs):
    """Backup slide: per-failure-mode recovery estimates + key insight."""
    slide = new_slide(prs)
    add_title(slide, "LLM Upgrade: Failure Mode Recovery Detail")
    add_accent_line(slide)

    # ── Full-width failure mode table ──
    tbl_w = CW
    ft = add_text(slide, "Expected Recovery by Failure Category (574 below-threshold segments)",
                  MX, CT, tbl_w, Inches(0.35),
                  size=Pt(16), color=TEAL, bold=True)

    headers = ["Failure Mode", "Segments", "% of Failures",
               "LLM Impact", "Expected Recovery"]
    rows = [
        ["Wrong Topic (total drift)", "143", "24.9%",
         "Low \u2014 no visual signal to decode", "<5%"],
        ["Wrong Topic (phonetic)", "112", "19.5%",
         "Moderate \u2014 better vocabulary prior", "10\u201320%"],
        ["Hallucination", "108", "18.8%",
         "Moderate-High \u2014 better calibration", "15\u201325%"],
        ["Right Topic, Wrong Details", "79", "13.8%",
         "Highest \u2014 entity/vocabulary disambiguation", "25\u201335%"],
        ["Signal Loss / Empty", "80", "13.9%",
         "None \u2014 encoder failure", "<5%"],
        ["Accumulated Errors", "52", "9.1%",
         "High \u2014 context catches cascading errors", "20\u201330%"],
    ]
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.50), tbl_w,
                    row_height=Inches(0.50),
                    col_widths=[Inches(2.2), Inches(1.0), Inches(1.2),
                                Inches(4.5), Inches(1.4)],
                    text_size=Pt(12))

    # ── Key insight box ──
    iy = CT + Inches(3.85)
    insight_box = add_rect(slide, MX, iy, CW, Inches(1.0),
                           fill_color=NAVY2, border_color=TEAL,
                           border_width=Pt(2), corner_radius=True)
    insight_title = add_text(slide, "Why These Categories?",
                             MX + Inches(0.3), iy + Inches(0.10),
                             CW - Inches(0.6), Inches(0.30),
                             size=Pt(15), color=TEAL, bold=True)
    insight_text = add_text(slide,
        "The LLM\u2019s job is disambiguation: when lips show /p/, /b/, or /m/ "
        "(identical mouth shape), the LLM picks the right word using language "
        "context. \u201cRight Topic Wrong Details\u201d is where this matters most "
        "\u2014 the encoder captured the domain, but Llama-2\u2019s weaker prior "
        "picked \u201cadmiral\u201d \u2192 \u201canimal\u201d. A model with "
        "61% higher MMLU and 4\u00d7 vocabulary resolves these directly.",
        MX + Inches(0.3), iy + Inches(0.40),
        CW - Inches(0.6), Inches(0.55),
        size=Pt(13), color=WHITE)

    # ── Bottom: multiplicative scaling note ──
    note_text = add_text(slide,
        "Multiplicative scaling law (ICLR 2024): better model \u00d7 more data "
        "= compounding gains. The LLM upgrade is most valuable when combined "
        "with 20K+ training segments.",
        MX, Inches(6.30), CW, Inches(0.35),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # References
    add_text(slide,
        "VALLR: Thomas et al. (ICCV 2025)  |  "
        "Scaling Laws: Zhang et al. (ICLR 2024)  |  "
        "Full analysis: docs/evaluation/llm_upgrade_analysis.md",
        MX, Inches(6.65), CW, Inches(0.25),
        size=Pt(8), color=MGRAY, italic=True)

    _finish(slide, 0,
        "Backup detail slide for Q&A. Shows per-failure-mode recovery "
        "estimates with the full 6-row table.\n\n"
        "Key point: Wrong Topic dominates at 44.4% (255 segments combined). "
        "'Right Topic Wrong Details' (79 segments) is the sweet spot for "
        "LLM improvement — encoder captured right domain but LLM picked "
        "wrong words. Examples: 'admiral McRae' -> 'animal migratory'.\n\n"
        "The insight box explains WHY: the LLM disambiguates homophenes "
        "(identical lip shapes for different sounds). A stronger language "
        "prior with 61% higher MMLU and 4x vocabulary directly fixes "
        "entity names and content words.\n\n"
        "Total estimated recovery from 574 below-threshold segments, "
        "pushing useful output rate from 61.6% to ~70-75%.",
        [[ft, tbl],
         [insight_box, insight_title, insight_text],
         [note_text]])


# ═══════════════════════════════════════════════════════════════════════
# ARABIC PIPELINE ROADMAP
# ═══════════════════════════════════════════════════════════════════════

def slide_arabic_roadmap(prs):
    """Arabic pipeline replication roadmap."""
    slide = new_slide(prs)
    add_title(slide, "Arabic Pipeline: Replication Roadmap")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what's needed, one topic per animation group
    lt = add_text(slide, "What\u2019s Needed & How We\u2019ll Do It",
                  MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)

    topics = [
        (TEAL,  "Arabic AV-HuBERT encoder (BOTTLENECK)",
         "Arabic has different phonemes (pharyngeals, emphatics) \u2014 "
         "without fine-tuning, Arabic lips map to wrong clusters"),
        (TEAL,  "Arabic LLM backend",
         "Swap Llama-2 for Arabic-capable LLM "
         "(e.g. Jais, AceGPT, or Arabic-tuned Llama 3)"),
        (CORAL, "Arabic evaluation dataset (UNKNOWN)",
         "No Arabic lip-reading benchmark exists \u2014 "
         "needs native speakers for MSA + dialect coverage"),
        (GREEN, "Training infrastructure",
         "AWS GPU instance (existing) for AV-HuBERT fine-tuning "
         "and K-means reclustering"),
        (CORAL,  "RTL text & normalization",
         "RTL handling, spaCy Arabic, diacritic handling, "
         "Arabic NER \u2014 maturity unknown"),
    ]

    topic_groups = []
    by = CT + Inches(0.45)
    # Tightened topic block (0.85" → 0.78") so the last RTL bullet ends ~5.80"
    # and clears the timeline callout below. Audit flagged 63% occlusion.
    for clr, heading, detail in topics:
        grp = []
        grp.append(add_bullets(slide, [
            (heading, {"bold": True, "color": clr}),
            detail,
        ], MX, by, col_w, Inches(0.78), size=Pt(13)))
        topic_groups.append(grp)
        by += Inches(0.78)

    # Right — timeline with practical details
    rx = MX + col_w + gap
    rt = add_text(slide, "Practical Timeline", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    headers = ["Step", "Effort", "Risks / Unknowns"]
    rows = [
        ["AV-HuBERT fine-tune\n+ K-means", "5\u201310 weeks", "Arabic visual data\nquality unknown"],
        ["Arabic LLM\nswap", "1\u20132 weeks", "Tokenizer quality\nvaries by model"],
        ["Eval dataset", "4\u20138 weeks", "No benchmark exists;\nneeds native speakers"],
        ["RTL normalization\n+ testing", "3\u20136 weeks", "RTL handling +\nend-to-end validation"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.45), col_w,
                    row_height=Inches(0.55),
                    col_widths=[Inches(1.5), Inches(1.3), Inches(2.7)],
                    text_size=Pt(11))

    # Timeline summary callout \u2014 moved down (5.85\u21926.00) so it sits below the
    # tightened topic block (last bullet now ends ~5.80"). Audit flagged 63%
    # occlusion of the RTL topic by this callout.
    timeline_box = add_rect(slide, MX, Inches(6.00), CW, Inches(0.50),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    timeline_txt = add_text(slide,
             "Realistic estimate: 2\u20133 months (encoder pre-training is the bottleneck)",
             MX + Inches(0.3), Inches(6.05), CW - Inches(0.6), Inches(0.40),
             size=Pt(20), color=CORAL, bold=True, align=PP_ALIGN.CENTER)

    # Bottom note (below callout box, above slide-number)
    note = add_text(slide,
        "Pipeline code is language-agnostic. Main bottlenecks: encoder pre-training "
        "data and eval dataset collection. No Arabic lip-reading benchmark exists.",
        MX, Inches(6.60), CW, Inches(0.30),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Animation: title → each topic one by one → right column → callout
    anim = [[lt]] + topic_groups + [[rt, tbl], [timeline_box, timeline_txt, note]]

    _finish(slide, 0,
        "Arabic replication roadmap with realistic, conservative estimates. "
        "Key insight: AV-HuBERT learned English visemes \u2014 Arabic has different "
        "phonemes (pharyngeals, emphatics) producing distinct lip movements, so "
        "fine-tuning is essential, not optional.\n\n"
        "Key unknowns and bottlenecks:\n"
        "1. Arabic visual data quality unverified for AV-HuBERT fine-tuning.\n"
        "2. No Arabic lip-reading benchmark exists \u2014 eval dataset must be "
        "built from scratch with native speakers.\n"
        "3. RTL text handling and Arabic NER tooling maturity is unknown.\n\n"
        "Steps: fine-tune AV-HuBERT + recluster K-means (5-10 weeks), swap to "
        "Arabic LLM (1-2 weeks), build eval dataset (4-8 weeks, parallel), "
        "RTL normalization + end-to-end testing (3-6 weeks). Total 2-3 months "
        "realistic. Pipeline code itself is language-agnostic.",
        anim, click_reveal=True)


def slide_arabic_avhubert(prs):
    """AV-HuBERT: Why It's Not Language-Locked — individual animated bullets."""
    slide = new_slide(prs)
    add_title(slide, "AV-HuBERT: Why It\u2019s Not Language-Locked")
    add_accent_line(slide)

    bullets_data = [
        "AV-HuBERT is a self-supervised visual feature extractor",
        "Pretrained on LRS3 (English TED talks) \u2014 but not language-encoded",
        "Training loop: MFCC \u2192 K-means \u2192 pseudo-labels \u2192 masked prediction \u2192 iterate",
        'The "English-ness" is in which visual distinctions the model learned to care about',
        "Low-level features are mostly universal: lip shape, mouth opening, jaw movement",
        "Visual features are ~80% language-agnostic (mouth geometry is universal)",
        "Language specificity lives in downstream components, not the visual encoder",
    ]

    by = CT + Inches(0.05)
    line_h = Inches(0.60)
    anim_groups = []
    for bullet in bullets_data:
        t = add_text(slide, "\u25b8  " + bullet,
                     MX, by, CW, line_h,
                     size=Pt(15), color=WHITE)
        anim_groups.append([t])
        by += line_h

    _finish(slide, 0,
        "AV-HuBERT self-supervised training: starts with MFCC features as initial targets, "
        "runs K-means clustering to create pseudo-labels, trains masked prediction of those labels "
        "from visual input, then iterates with better pseudo-labels. After multiple iterations, "
        "the visual encoder has learned which lip movements correspond to which sound clusters. "
        "The 'English-ness' lives in which visual distinctions the model learned to care about \u2014 "
        "e.g., it never learned to distinguish Arabic emphatics (\u0635 vs \u0633) which involve "
        "visible pharyngeal constriction. But this is an optimization target, not a hard blocker.",
        anim_groups, click_reveal=True)


def slide_arabic_changes(prs):
    """Arabic Adaptation: What Changes — individual animated bullets."""
    slide = new_slide(prs)
    add_title(slide, "Arabic Adaptation: What Changes")
    add_accent_line(slide)

    bullets_data = [
        "K-means clustering \u2014 retrain on Arabic audio features (already retrains per-dataset)",
        "LLM backbone \u2014 replace with Arabic-capable LLM (Jais, AceGPT, or multilingual Llama 3)",
        "Q-Former bridge + LoRA adapters \u2014 retrain on Arabic video-transcript pairs",
        "AV-HuBERT encoder \u2014 can reuse frozen; fine-tune later as optimization step",
        "Phase 1: Frozen AV-HuBERT + Arabic K-means + Arabic LLM + retrained Q-Former",
        "Phase 2: Fine-tune AV-HuBERT on Arabic video for language-specific distinctions",
        "Phase 3: Scale with more Arabic training data",
        "Biggest bottleneck: training data (no Arabic LRS3 equivalent at scale)",
    ]

    by = CT + Inches(0.05)
    line_h = Inches(0.55)
    anim_groups = []
    for bullet in bullets_data:
        t = add_text(slide, "\u25b8  " + bullet,
                     MX, by, CW, line_h,
                     size=Pt(14), color=WHITE)
        anim_groups.append([t])
        by += line_h

    _finish(slide, 0,
        "Arabic adaptation practical bottleneck sequence:\n"
        "1. K-means: Retrain on Arabic audio features \u2014 this already retrains per-dataset "
        "in our pipeline, so Arabic clusters are essentially 'free'.\n"
        "2. LLM: Replace with Arabic-capable model. The LLM swap is the most impactful single change.\n"
        "3. Q-Former + LoRA: Retrain on Arabic video-transcript pairs. This is where the authors' "
        "actual novel contribution was.\n"
        "4. AV-HuBERT: Frozen English encoder is the starting point. Fine-tuning is Phase 2 optimization.\n\n"
        "Arabic emphatics example: \u0635 (emphatic S) vs \u0633 (plain S) have visible pharyngeal constriction "
        "that the English-pretrained encoder never learned to distinguish. Fine-tuning would teach this.\n\n"
        "Data challenge: No Arabic equivalent of LRS3. Options include custom collection from Arabic "
        "broadcast/YouTube, or cross-lingual pretraining strategies.",
        anim_groups, click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 31 — SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def slide_31(prs):
    slide = new_slide(prs)
    add_title(slide, "Key Takeaways")
    add_accent_line(slide)

    # audit:logic_fix slide 79 \u2014 MBR (production default since May 2 2026)
    # was missing from takeaways; add takeaway #4. Numeric anchors:
    # audit:niv_yp_pct_mbr (61.92%), audit:judge_v3_yp_pct_mbr (71.08%),
    # audit:judge_v3_yp_pct_baseline (68.40%), audit:mcnemar_yp_p_mbr (0.00017).
    takeaways = [
        ("1", "Rigorous assessment: 2.5\u00d7 WER gap on 1,497 segments. "
              "Novel IS metric reveals 61.92% useful output (NIV Y+P, MBR), "
              "confirmed by LLM judge v1 blind at 64.9%. Full failure "
              "analysis with improvement suggestions."),
        ("2", "Production system delivered: standalone container with "
              "professional UI, 37 bugs fixed, 8-stage pipeline, 37 tests, "
              "8 research reports \u2014 all from a paper with no working "
              "environment."),
        ("3", "Model performs well after MBR: 71.08% useful per LLM Judge v3 "
              "(paired). IS metric shows high agreement with the v1 blind "
              "judge gold standard (\u03ba=0.818 at NIV-Y+P) and runs entirely on "
              "the standalone computer \u2014 no cloud dependency."),
        ("4", "MBR shipped as production default (May 2 2026, Mission 6) \u2014 "
              "Judge v3 Y+P 71.08% vs baseline 68.40%, p = 0.00017 paired "
              "McNemar. Joint conf+agreement bands + Trust gate also shipped."),
        ("5", "Clear path forward: stronger LLM + smart prompts + 20K+ "
              "training data to improve English performance. Full plan to "
              "replicate the approach for an Arabic model in 2\u20133 months."),
    ]

    card_h = Inches(0.95)  # tightened to fit 5 cards (was 1.05 for 4)
    gap = Inches(0.10)
    circle_d = Inches(0.55)

    card_groups = []
    for i, (num, text) in enumerate(takeaways):
        y = CT + i * (card_h + gap)

        # Card background
        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(1), corner_radius=True)

        # Number circle — vertically centered in card
        cy = y + (card_h - circle_d) / 2
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX + Inches(0.2), cy, circle_d, circle_d)
        circle.fill.solid()
        circle.fill.fore_color.rgb = TEAL
        circle.line.fill.background()
        nt = add_text(slide, num, MX + Inches(0.2), cy,
                 circle_d, circle_d,
                 size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        # Text — left-aligned next to circle
        tb = add_text(slide, text,
                      MX + Inches(1.0), y + Inches(0.08),
                      CW - Inches(1.2), card_h - Inches(0.16),
                      size=Pt(13), color=WHITE)
        card_groups.append([r, circle, nt, tb])

    _finish(slide, 31,
        "Five takeaways anchored to the headline numbers from this deck. "
        "(1) Rigorous assessment with the novel IS metric and full failure "
        "analysis: 61.92% useful Y+P with MBR n-best, 64.9% confirmed by "
        "LLM judge v1 blind on the same 1,497 pairs (Pearson r=0.85 "
        "between IS and judge). "
        "(2) Production system built from scratch — standalone container, "
        "UI, 8-stage pipeline, 37 tests, 8 research reports. "
        "(3) Model performs well after MBR: 71.08% Y+P per LLM Judge v3 "
        "paired test (Opus 4.7, 5,988 verdicts). IS shows kappa=0.818 "
        "agreement with judge at NIV-Y+P. "
        "(4) MBR shipped May 2 2026 as production default — Judge v3 "
        "Y+P 71.08% vs baseline 68.40% (+2.68 pp absolute, p = 0.00017 "
        "paired McNemar over 5,988 verdicts). Joint conf+agreement bands "
        "and the Trust gate also shipped. "
        "(5) Clear path forward for English improvement (stronger LLM + "
        "smart prompts + 20K+ training data) and Arabic adaptation "
        "(2-3 months). Mention to peers: each takeaway maps to one "
        "section of the deck and one MD/CSV in docs/. "
        "Sources: docs/evaluation/after_amosi_audit.md (Section F), "
        "docs/beam-search/n_best_implementation.md, "
        "docs/evaluation/llm_judge/llm_judge_analysis.md.",
        card_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# APPENDIX SLIDES (A1–A13)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# APPENDIX SLIDES (A1–A13)
# ═══════════════════════════════════════════════════════════════════════

def slide_a1(prs):
    """A1: Homophenes — The Lip-Reading Problem."""
    slide = new_slide(prs)
    add_title(slide, "A1: Homophenes — The Lip-Reading Problem")
    add_accent_line(slide)

    # Left: viseme table
    add_text(slide, "50–70% of English sounds are invisible on lips.\n"
             "Multiple sounds produce identical mouth shapes:",
             MX, CT, SLW, Inches(0.7), size=Pt(14), color=LGRAY)

    tbl1 = add_table(slide,
        ["Viseme Group", "Sounds"],
        [["Bilabial", "p, b, m"],
         ["Alveolar", "t, d, n, s, z, l"],
         ["Velar", "k, g, ng"],
         ["Labiodental", "f, v"]],
        MX, CT + Inches(0.9), SLW, text_size=Pt(12))

    # Right: confusable pairs
    add_text(slide, "Confusable word pairs (identical on lips):",
             SRL, CT, SRW, Inches(0.5), size=Pt(14), color=LGRAY)

    tbl2 = add_table(slide,
        ["Word A", "Word B"],
        [["mom", "bomb"], ["pat", "bat"], ["collar", "color"],
         ["pads", "pants"], ["admiral", "animal"],
         ["probiotics", "permafrost"]],
        SRL, CT + Inches(0.6), SRW, text_size=Pt(12))

    add_text(slide, 'Context is the ONLY disambiguation signal.\n'
             'This is why the LLM component matters.',
             SRL, CT + Inches(3.6), SRW, Inches(0.5),
             size=Pt(12), color=TEAL, italic=True)

    _finish(slide, "A1",
        "Homophenes: visually identical mouth shapes for different sounds. "
        "50-70% of English sounds are invisible on lips, distributed across "
        "four canonical viseme groups (bilabial, alveolar, velar, "
        "labiodental). Word pairs like admiral/animal, mom/bomb, "
        "probiotics/permafrost are indistinguishable on the lips. The "
        "homophene rate is the single largest source of irreducible "
        "ambiguity in any visual-speech-recognition system. This is "
        "exactly why the architecture is visual encoder + LLM rather than "
        "visual encoder alone — context from the LLM is the only "
        "disambiguation signal available. Mention to peers: this "
        "appendix slide is the conceptual anchor for everything in "
        "Sections 2 and 4 of the deck. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/paper/VSP-LLM_paper.pdf.",
        [[tbl1], [tbl2]], click_reveal=True)


def slide_a3(prs):
    """A2: Catastrophic lenpen=2.0."""
    slide = new_slide(prs)
    add_title(slide, "A2: Catastrophic lenpen=2.0 (Config H)")
    add_accent_line(slide)

    add_text(slide, "Config H forces the model to generate longer text. "
             "Mean WER: 539.6%\nThe model generates paragraphs of "
             "hallucinated text:",
             MX, CT, CW, Inches(0.6), size=Pt(14), color=CORAL)

    tbl = add_table(slide,
        ["Segment", "Reference", "Config H Output", "WER"],
        [["pOeJSxbFyto", '"get the idea"',
          '"that\'s why I\'m here thank you so much for having me '
          'it\'s been an honor and a privilege..."', "6,833%"],
         ["9KACXV-cW-4", '"now those predictions I think"',
          '"of first believers the same path I\'d like to take a moment '
          'to thank all of you..."', "4,640%"],
         ["loebelfG9T4", '"so repeat make yourself at home"',
          '"don\'t forget to make yourself at home thank you very much '
          'that was a lot of fun..."', "4,183%"]],
        MX, CT + Inches(0.8), CW, text_size=Pt(10),
        row_colors={0: {3: CORAL}, 1: {3: CORAL}, 2: {3: CORAL}})

    add_text(slide, "lenpen=2.0 removes the generation length brake, "
             "letting the LLM prior run unchecked.",
             MX, CT + Inches(3.4), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True)

    _finish(slide, "A2",
        "Config H (lenpen=2.0) produces catastrophic hallucinations. "
        "Mean WER 539.6%. The model generates entire paragraphs of fluent "
        "but completely fabricated text. This dramatically illustrates the "
        "LLM prior overwhelming the visual signal.")


def slide_a8(prs):
    """A3: IS Component Correlation."""
    slide = new_slide(prs)
    add_title(slide, "A3: IS Component Correlation")
    add_accent_line(slide)

    # PCA dimension table — 2 PCs (Kaiser criterion)
    # OVERLAP fix: shrink the PCA caption width so it ends at SRL-0.1 rather
    # than reaching CW*0.55 = 6.67 (right edge x=7.27, which collided with
    # the right-column "Cross-Config" caption starting at SRL=6.5).
    add_text(slide, "PCA: 6 IS signals collapse into 2 principal components:",
             MX, CT, SRL - MX - Inches(0.1), Inches(0.4),
             size=Pt(14), color=WHITE)

    tbl1 = add_table(slide,
        ["Component", "Signals", "Variance", "Loadings"],
        [["PC1: Signal Quality", "All 5 content signals", "68.4%", "0.43\u20130.47 each"],
         ["PC2: Output Length", "Length Ratio", "19.5%", "0.91"]],
        MX, CT + Inches(0.5), SRL - MX - Inches(0.1), text_size=Pt(11),
        row_height=Inches(0.35),
        col_widths=[Inches(1.6), Inches(1.8), Inches(1.1), Inches(1.4)])

    # Cross-config stability
    add_text(slide, "Cross-Config Stability (16 configs)",
             SRL, CT, SRW, Inches(0.35), size=Pt(14), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["Signal", "Stability", "Std"],
        [["Semantic", "Stable", "0.017"],
         ["Phonetic", "Stable", "0.059"],
         ["NEA", "Stable", "0.023"],
         ["WER", "Volatile", "0.165"],
         ["Length", "Volatile", "0.142"]],
        SRL, CT + Inches(0.4), SRW, text_size=Pt(10),
        row_height=Inches(0.3),
        row_colors={3: {1: CORAL}, 4: {1: CORAL},
                    0: {1: GREEN}, 1: {1: GREEN}, 2: {1: GREEN}})

    # Heuristic validation — positioned below tbl2 (top 1.85 + 6*0.3 = 3.65)
    add_text(slide, "Heuristic Validation (no runtime LLM)",
             SRL, CT + Inches(2.35), SRW, Inches(0.3),
             size=Pt(13), color=TEAL, bold=True)

    tbl3 = add_table(slide,
        ["Metric", "Value"],
        [["Mean r", "0.925 (std 0.015)"],
         ["Agreement (IS ≥ 2.00)", "κ = 0.818"],
         ["Agreement (IS ≥ 3.80)", "κ = 0.690"],
         ["Recall (IS ≥ 2.00)", "97.6–100%"],
         ["Config range", "κ 0.62–0.86"]],
        SRL, CT + Inches(2.75), SRW * 0.7, text_size=Pt(10),
        row_height=Inches(0.3))

    _finish(slide, "A3",
        "PCA retains exactly 2 principal components under the Kaiser "
        "criterion: PC1 captures signal quality (68.4% of variance, all 5 "
        "content signals load 0.43-0.47), PC2 captures output length "
        "(19.5%, Length Ratio loads 0.91). Together 87.9% of variance. "
        "Cross-config stability across 16 decode-parameter sweeps: "
        "Semantic, Phonetic, NEA are stable (std 0.017-0.059), while WER "
        "and Length Ratio are volatile (std 0.142-0.165) — exactly the "
        "axes WER alone would penalise. IS vs Opus judge: kappa=0.818 at "
        "Y+P (IS>=2.00), kappa=0.690 at Y (IS>=3.80). Mean r between IS "
        "and the LLM-context-prob heuristic is 0.925 (std 0.015) across "
        "configs. Mention to peers: this slide is the empirical proof "
        "that IS captures two distinct quality dimensions, not six "
        "redundant ones, and that the heuristic is a deterministic "
        "stand-in for the LLM judge at design time. "
        "Sources: docs/evaluation/is_pca_analysis.md, "
        "docs/evaluation/is_correlation_analysis.md, "
        "docs/evaluation/is_cross_config_validation.md.")


def slide_a11(prs):
    """A4: LLM Salvage — Recoverable Segments."""
    slide = new_slide(prs)
    add_title(slide, "A4: LLM Salvage — Recoverable Segments")
    add_accent_line(slide)

    # Key numbers
    add_text(slide, "Key Numbers", MX, CT, SLW, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    # audit:niv_yp_pct_top1 (61.66%) — slide table reports the top-1 baseline
    # because LLM-salvage analysis was conducted against the top-1 hypothesis
    # (heuristic was tuned on top-1; salvage analysis predates MBR shipping).
    # Judge 64.9% is the v1 blind gold-standard (audit:llm_judge_v1).
    tbl1 = add_table(slide,
        ["Metric", "Value"],
        [["Metric-failed segments", "900"],
         ["LLM-recoverable", "165 (18.3%)"],
         ["Useful output (IS ≥ 2.00, top-1)", "61.66%"],  # audit:niv_yp_pct_top1
         ["LLM Judge v1 blind (Y+P)", "64.9%"],  # audit:llm_judge_v1
         ["IS vs Judge agreement", "κ = 0.818"]],
        MX, CT + Inches(0.4), SLW, text_size=Pt(11),
        row_colors={1: {1: TEAL}, 3: {1: TEAL}})

    add_text(slide, "58% of salvageable have moderate WER (50–70%).\n"
             "Decision tree: 15 rules, r=0.934 with IS.",
             MX, CT + Inches(2.8), SLW, Inches(0.7),
             size=Pt(12), color=LGRAY)

    # Recovery categories
    add_text(slide, "6 Recovery Categories", SRL, CT, SRW, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["Category", "N", "Key Signal"],
        [["Hidden Gems", "54", "LLM prob ≥ 0.8"],
         ["Semantic Pres.", "57", "Semantic ≥ 0.5"],
         ["Phonetic Bridge", "93", "Phonetic ≥ 0.6"],
         ["Entity-Preserved", "44", "NEA F1 ≥ 50%"],
         ["Structure Match", "74", "Word order intact"],
         ["WER Over-Punish.", "27", "WER−WWER ≥ 10pp"]],
        SRL, CT + Inches(0.4), SRW, text_size=Pt(11))

    add_text(slide, "Categories overlap — segments can exhibit multiple "
             "recovery signals. System delivers useful output for 1 in 2 segments.",
             SRL, CT + Inches(3.2), SRW, Inches(0.6),
             size=Pt(12), color=LGRAY, italic=True)

    _finish(slide, "A4",
        # audit:niv_yp_pct_top1 — LLM-salvage analysis is top-1-anchored.
        "165 of 900 metric-failed segments are recoverable by the LLM "
        "heuristic. Useful output rate is 61.66% NIV Y+P (top-1; MBR "
        "n-best lifts to 61.92%). 6 recovery categories (overlap, not "
        "disjoint). 58% have moderate WER (50-70%). "
        "See docs/evaluation/llm_salvage/llm_salvage_analysis.md.")


def slide_a11b(prs):
    """A5: LLM Salvage — Curated Examples."""
    slide = new_slide(prs)
    add_title(slide, "A5: LLM Salvage — Curated Examples")
    add_accent_line(slide)

    add_text(slide, "One real example per recovery category — all IS < 2.0 "
             '(metrics say "failed") but heuristic says recoverable:',
             MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY)

    tbl = add_table(slide,
        ["Category", "Reference (excerpt)", "Hypothesis (excerpt)",
         "WER", "IS", "LLM"],
        [["Hidden Gem",
          "...opinions about reason and logic and all these other concepts...",
          "...our opinion is about reasoning and logic and all these...",
          "74%", "2.92", "0.90"],
         ["Semantic Pres.",
          "india china afghanistan...both sides would benefit",
          "middle east and afghanistan...both sides will benefit",
          "72%", "2.86", "0.90"],
         ["Phonetic Bridge",
          "expresses in concrete and symbolic and beautifully real deep",
          "suppresses the concrete and the symbolic and the beautiful...",
          "89%", "2.75", "0.90"],
         ["Entity-Preserved",
          "how facebook is a media company...what's about twitter",
          "how facebook is a media company on switzerland",
          "57%", "2.86", "0.90"],
         ["Structure Match",
          "neptune gives us a long time to learn...energies and wisdom...",
          "you give it a long time to learn...energies and wisdom...",
          "39%", "2.94", "0.95"],
         ["WER Over-Punish.",
          "so um",
          "so i kind of",
          "150%", "2.06", "0.65"]],
        MX, CT + Inches(0.6), CW, text_size=Pt(9),
        row_height=Inches(0.45))

    _finish(slide, "A5",
        "Curated examples showing each of the 6 recovery categories. "
        "All have IS < 2.0 but the heuristic identifies recoverable meaning. "
        "Categories overlap: a segment can exhibit multiple recovery signals.")


def slide_a13(prs):
    """A6: Failure Mode Examples."""
    slide = new_slide(prs)
    add_title(slide, "A6: Failure Mode Examples")
    add_accent_line(slide)

    add_text(slide, "One real example per failure category (5 categories):",
             MX, CT, CW, Inches(0.3), size=Pt(13), color=LGRAY)

    # Canonical 5 categories from 574-segment failure taxonomy
    tbl = add_table(slide,
        ["Category", "% of Failures", "Reference", "Hypothesis", "WER", "IS"],
        [["Wrong Topic\n(255 segs)",  "44.4%",
          '"weight loss and diet..."',
          '"wanted to be a princess..."', "97%", "0.38"],
         ["Hallucination\n(108 segs)", "18.8%",
          '"and body parts"',
          '"20 years ago when i was"', "200%", "0.00"],
         ["Signal Loss\n(80 segs)",    "13.9%",
          '"do you say i wonder what..."',
          "(empty)", "100%", "0.00"],
         ["Right Topic,\nWrong Details\n(79 segs)", "13.8%",
          '"13th amendment is going..."',
          '"13th may mean something..."', "60%", "1.86"],
         ["Accumulated\nErrors (52 segs)", "9.1%",
          '"you\'re rich no no no..."',
          '"your ring that\'s not what..."', "67%", "1.64"]],
        MX, CT + Inches(0.4), CW, text_size=Pt(10),
        row_height=Inches(0.70),
        col_widths=[Inches(1.8), Inches(1.0), Inches(2.8), Inches(2.8),
                    Inches(0.8), Inches(0.6)],
        row_colors={0: {5: CORAL}, 1: {5: CORAL}, 2: {5: CORAL}})

    _finish(slide, "A6",
        "Canonical 5 failure categories from the 574-segment taxonomy "
        "(IS < 2.00 on our 1,497-segment evaluation set). Wrong Topic is "
        "the largest (44.4%, 255 segments) and combines topic drift with "
        "phonetic confusion. Hallucination (18.8%, 108) is the most "
        "dangerous — fluent but fabricated text — because the output reads "
        "as confident even when it is invented from a 2-word reference. "
        "Signal Loss (13.9%, 80) is the easiest to filter, Right Topic / "
        "Wrong Details (13.8%, 79) is the client-trust killer, and "
        "Accumulated Errors (9.1%, 52) responds well to N-best aggregation. "
        "Each row in the table shows one canonical real example so a "
        "reader can match the rule to the data. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14b — CURATED EXAMPLES VIDEO GALLERY
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE A15 — VIDEO GALLERY MAP
# ═══════════════════════════════════════════════════════════════════════

def slide_a15(prs):
    """A7: Reference table of all 34 example segments across the presentation."""
    slide = new_slide(prs)
    add_title(slide, "A7: Video Gallery — All Example Segments")
    add_accent_line(slide)

    add_text(slide, "★ = video embedded on a slide   ─ = available in burned_videos/ only",
             MX, CT, CW, Inches(0.32), size=Pt(11), color=LGRAY, italic=True)

    col_w = [Inches(2.1), Inches(1.7), Inches(0.8), Inches(0.7), Inches(0.5)]
    headers = ["Segment ID", "Category", "Slide", "WER", ""]

    left_rows = [
        # Curated Examples
        ["IEa7qEkMvfQ_3",  "Perfect",         "14",    "0%",   "★"],
        ["-WQZsfHcPDM_7",  "Near-Miss",       "14",    "58%",  "★"],
        ["00MUdHQ7GGY_8",  "Hallucination",   "14",    "100%", "★"],
        ["DBhaa45mAro_2",  "Tuning Fix",      "14",    "73%",  "★"],
        ["vBCnI4kf3-E_0",  "Topic Drift",     "14/A6", "97%",  "★"],
        ["Q8aPjew1aUU_5",  "Salvage",         "14/A5", "74%",  "★"],
        ["d8BR6hsvzoY_31", "Perfect Short",   "15",    "0%",   "★"],
        # LLM Salvage
        ["WTSIAfzvYUU_0",  "Semantic Pres.",  "A5",    "72%",  "─"],
        ["cT6aHJmM4cA_2",  "Phonetic Bridge", "A5",    "89%",  "★"],
        ["cECxDMkqVcs_0",  "Entity-Pres.",    "A5",    "57%",  "─"],
        ["IZcKDz911X8_0",  "Structure Match", "A5",    "39%",  "─"],
        ["0FUlRjBcGGE_21", "WER Over-Pun.",   "A5",    "150%", "★"],
        # Success Patterns
        ["FLRU5qzb6hc_9",  "Near-Perfect",    "A12",   "0%",   "─"],
        ["BVynmQr3cf8_0",  "Minor Errors",    "A12",   "11%",  "─"],
        ["LiYzBldkxMc_2",  "Phonetic Pres.",  "A12",   "27%",  "─"],
        ["epuNSCr7qpA_16", "Good Sem+Len",    "A12",   "15%",  "─"],
        ["BS4kTgaiydQ_0",  "Entity Preserved","A12",   "31%",  "★"],
    ]

    right_rows = [
        ["HecEY5bF-xs_5",  "Low-Mod WER",     "A12",   "15%",  "─"],
        ["c6eBrYor21I_10",  "Sem+Phonetic",    "A12",   "52%",  "─"],
        # Failure Modes
        ["1RkFwRhhcWQ_0",  "Empty Output",    "A6",    "100%", "─"],
        ["BmmJujNQvXw_0",  "Extreme Halluc.", "A6",    "200%", "★"],
        ["0fmc81KXbB0_0",  "Truncation",      "A6",    "69%",  "─"],
        ["EMfcKvHA5Uc_0",  "Entity Destruct.","A6",    "100%", "★"],
        ["2JuBrr6TW8o_14", "Phonetic Wrong",  "A6",    "100%", "─"],
        ["ZnoJxsXKULY_0",  "High Error Rate", "A6",    "100%", "─"],
        ["49qxSMt4Xe0_0",  "Accum. Errors",   "A6",    "68%",  "─"],
        ["xITCbZxwLn4_0",  "Content Errors",  "A6",    "60%",  "─"],
        ["KcDqXon7I3c_0",  "Over-generation", "A6",    "100%", "─"],
        # Metric Mismatch
        ["10xhJGx6-kc_0",  "WER>>WWER",       "A14b",  "71%",  "─"],
        ["-WqvFSuRYo0_12", "WWER>>WER",       "A14b",  "27%",  "─"],
        ["1whXJLCrTjY_0",  "Hi Sem+Hi WER",   "A14b",  "67%",  "─"],
        ["ZB21bsGO0KA_7",  "Lo Sem+Lo WER",   "A14b",  "40%",  "─"],
        ["2T-C7vQJBis_0",  "Hi NEA+WWER",     "A14b",  "42%",  "─"],
        ["0PQonSiGkVE_0",  "LR>1.5+WER",      "A14b",  "140%", "─"],
    ]

    half = Inches(5.9)
    gap  = Inches(0.33)

    tbl_l = add_table(slide, headers, left_rows,
                      MX, CT + Inches(0.38), half,
                      row_height=Inches(0.28), text_size=Pt(8),
                      col_widths=[Inches(1.85), Inches(1.5), Inches(0.7),
                                  Inches(0.6), Inches(0.45)])

    tbl_r = add_table(slide, headers, right_rows,
                      MX + half + gap, CT + Inches(0.38), half,
                      row_height=Inches(0.28), text_size=Pt(8),
                      col_widths=[Inches(1.85), Inches(1.5), Inches(0.7),
                                  Inches(0.6), Inches(0.45)])

    _finish(slide, "A7",
        "Reference map of all 34 unique example segments used across the "
        "presentation. 12 are embedded as clickable videos on Slides 14b and A11b. "
        "All 1,497 burned videos are available at "
        "english_full_results/client_outputs/burned_videos/. "
        "Segment IDs map directly to filenames: {id}_with_hyp.mp4.")


# ═══════════════════════════════════════════════════════════════════════
# NEW SLIDES — DEEP DIVES, CONTEXT, ENGINEERING, APPENDIX
# ═══════════════════════════════════════════════════════════════════════

def slide_future_transition(prs):
    """Section divider: entering future directions portion."""
    slide = new_slide(prs)

    add_text(slide, "FUTURE DIRECTIONS",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(48), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "From Analysis to Action",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=GREEN)

    add_text(slide, "5 research insights  \u2192  5-phase improvement roadmap",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Section transition: we now move from what we found to what we "
        "recommend doing about it. Five key insights lead to a five-phase "
        "improvement roadmap.")


def slide_insights(prs):
    """Key research insights that inform the roadmap."""
    slide = new_slide(prs)
    add_title(slide, "Five Insights That Inform the Roadmap")
    add_accent_line(slide)

    insights = [
        ("1", "The visual encoder is the bottleneck, not the LLM",
         "Per-segment IS rankings are identical across 16 configs (r > 0.92). "
         "Tuning the LLM's decode parameters changes almost nothing.",
         TEAL),
        ("2", "WER dramatically overstates failure",
         "61.6% useful (NIV Y+P) vs WER's 25.5% \u2014 2.4\u00d7 more. LLM Judge "
         "confirms 64.9%. Most useful output has moderate WER (50\u201370%).",
         GREEN),
        ("3", "Domain mismatch is the primary quality driver",
         "IS ranges from 3.08 (Business) to 2.13 (DIY). Training data is TED "
         "talks \u2014 formal, educational, frontal face.",
         CORAL),
        ("4", "Data scarcity, not model capacity, limits fine-tuning",
         "1,273 segments is below the ~1K LoRA minimum. r=64 was 3.1pp "
         "WORSE than r=16 \u2014 faster overfitting, not better learning.",
         CORAL),
        ("5", "Gains are multiplicative, not additive",
         "ICLR 2024 scaling law: stronger LLM \u00d7 more data \u00d7 smart "
         "prompts compound. Each lever alone is modest; together they're "
         "transformative.",
         TEAL),
    ]

    step_h = Inches(0.85)
    start_y = CT

    insight_groups = []
    for i, (num, title, detail, color) in enumerate(insights):
        y = start_y + i * (step_h + Inches(0.1))

        # Number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX, y + Inches(0.1), Inches(0.5), Inches(0.5))
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()
        nt = add_text(slide, num, MX, y + Inches(0.1),
                 Inches(0.5), Inches(0.5),
                 size=Pt(18), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        rt = add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": WHITE, "bold": True})],
            [(detail, {"size": Pt(11), "color": LGRAY})],
        ], MX + Inches(0.7), y + Inches(0.02),
           CW - Inches(0.8), step_h - Inches(0.04))
        insight_groups.append([circle, nt, rt])

    _finish(slide, 0,
        "Five key research insights. The visual encoder is the bottleneck. "
        "WER dramatically overstates failure. Domain mismatch is the primary "
        "quality driver. Data scarcity limits fine-tuning. And gains are "
        "multiplicative — stronger LLM times more data times smart prompts.",
        insight_groups)


def slide_data_scaling(prs):
    """Data scaling evidence and projections."""
    slide = new_slide(prs)
    add_title(slide, "Data Scaling: The Path to IS 3.5–4.0")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — fine-tuning results + scaling law
    lt = add_text(slide, "Why More Data Is the Answer", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("Current: 1,273 English segments \u2014 far below LoRA minimum", {"bold": True}),
        "Scaling law (ICLR 2024): data \u00d7 LLM quality = multiplicative gains",
        ("AVSpeech: 290K English videos available for curation", {"color": TEAL}),
        ("Next step: curate 20K\u201350K diverse English segments", {"bold": True, "color": GREEN}),
    ], MX, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(14))

    # Right — projection table with IS
    rx = MX + col_w + gap
    rt = add_text(slide, "Projected Impact on IS", rx, CT, col_w,
                  Inches(0.4), size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Phase", "Data", "WER", "IS Target", "Timeline"],
        [["Current", "1.3K segs", "64.1%", "2.52", "\u2014"],
         ["Phase 1", "5K hrs", "55\u201358%", "~2.9", "2\u20134 wks"],
         ["Phase 2", "10K hrs", "48\u201352%", "~3.3", "4\u20136 wks"],
         ["Phase 3", "20K hrs", "42\u201346%", "~3.7", "6\u20138 wks"],
         ["Phase 4", "50K+ hrs", "38\u201342%", "~4.0+", "3\u20134 mo"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(13),
        col_widths=[Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.0), Inches(1.1)],
        row_colors={0: {2: CORAL}, 3: {3: GREEN}, 4: {3: GREEN}})

    # AVSpeech callout
    r1 = add_rect(slide, rx, CT + Inches(3.0), col_w, Inches(1.0),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "290K", rx + Inches(0.2), CT + Inches(3.1),
             Inches(1.2), Inches(0.4),
             size=Pt(28), color=TEAL, bold=True)
    add_text(slide, "AVSpeech English videos available\nfor training data curation",
             rx + Inches(1.5), CT + Inches(3.1), col_w - Inches(1.7),
             Inches(0.7), size=Pt(13), color=WHITE)

    realistic_note = add_text(slide,
        "Timelines assume realistic training: bugs, bad epochs, debugging overhead \u2014 "
        "not ideal paper conditions.",
        rx, CT + Inches(4.1), col_w, Inches(0.35),
        size=Pt(10), color=LGRAY, italic=True)

    # Academic references
    add_text(slide,
        "LoRA Scaling: Biderman et al. (2024), ICLR  |  "
        "AVSpeech: Ephrat et al. (2018), ACM TOG — 290K video dataset",
        MX, Inches(6.55), CW, Inches(0.3),
        size=Pt(8), color=MGRAY, italic=True)

    _finish(slide, 0,
        "Data scaling projections based on ICLR 2024 multiplicative scaling "
        "law. Current 1,273 segments is far below minimum. 20K segments with "
        "Llama 3.1 8B projects to IS 3.5-4.0 (85-90% useful Y+P). AVSpeech has "
        "290K videos available for training data curation.",
        [[lt, lb], [rt], [tbl], [r1, realistic_note]], click_reveal=True)


def slide_price_tag(prs):
    """Cost projections: data scale is the only variable."""
    slide = new_slide(prs)
    add_title(slide, "The Price Tag: What It Costs to Improve")
    add_accent_line(slide)

    # Framing: the paper's training recipe already exists — we just need more data
    add_text(slide,
        "The paper\u2019s training recipe already works (25.4% WER on LRS3). "
        "The only variable is data scale.",
        MX, CT, CW, Inches(0.35), size=Pt(14), color=LGRAY, italic=True)

    # Simple 3-column table: Data → Cost → Expected IS
    tbl_w = Inches(9.0)
    tbl_x = (SL_W - tbl_w) / 2
    tbl = add_table(slide,
        ["Training Data", "Cost (AWS spot)", "Expected IS"],
        [["5\u201310K hrs  (10\u201320\u00d7 paper)", "~$10\u201320K", "~3.0\u20133.5"],
         ["20K hrs  (46\u00d7 paper)", "~$30\u201340K", "~3.5\u20133.8"],
         ["50K hrs  (115\u00d7 paper)", "~$70\u2013100K", "~3.8\u20134.2"]],
        tbl_x, CT + Inches(0.55), tbl_w, text_size=Pt(14),
        col_widths=[Inches(3.8), Inches(2.4), Inches(2.8)],
        row_height=Inches(0.5),
        row_colors={1: {1: GREEN, 2: GREEN}})

    # Key insight callout
    ins_y = CT + Inches(2.55)
    r1 = add_rect(slide, MX, ins_y, CW, Inches(1.2),
                   fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                   corner_radius=True)
    add_text(slide, "Key insight",
             MX + Inches(0.25), ins_y + Inches(0.08),
             Inches(3.0), Inches(0.28), size=Pt(15), color=GOLD, bold=True)
    add_bullets(slide, [
        "Paper used only 433 hrs of LRS3 \u2014 we need 20\u201350K hrs of diverse data",
        ("Same training recipe, same model architecture \u2014 just more data",
         {"color": TEAL}),
        "Current IS 2.52 \u2192 target IS 3.5\u20134.0 requires ~46\u2013115\u00d7 data scale-up",
    ], MX + Inches(0.2), ins_y + Inches(0.38), CW - Inches(0.4), Inches(0.75),
        size=Pt(13))

    # LLM upgrade — requires adapter retraining but stacks with data investment
    llm_y = ins_y + Inches(1.4)
    r2 = add_rect(slide, MX, llm_y, CW, Inches(0.7),
                   fill_color=NAVY2, border_color=TEAL, border_width=Pt(1),
                   corner_radius=True)
    add_text(slide, "LLM upgrade: Llama-2 \u2192 Llama 3.1 8B  "
             "(+0.3\u20130.5 IS, requires adapter retraining, stacks with data investment)",
             MX + Inches(0.25), llm_y + Inches(0.15),
             CW - Inches(0.5), Inches(0.4),
             size=Pt(13), color=TEAL)

    _finish(slide, 0,
        "Cost projection focused on data scale as the single variable.\n\n"
        "The VSP-LLM paper already fine-tuned AV-HuBERT using a two-stage "
        "curriculum (freeze encoder 18K steps, unfreeze 12K steps) \u2014 this is "
        "the paper's existing recipe, not something new. It achieved 25.4% WER "
        "on LRS3. The method works; it just needs more diverse data.\n\n"
        "Three data tiers: 5-10K hrs ($10-20K), 20K hrs ($30-40K sweet spot), "
        "50K hrs ($70-100K). Paper trained on only 433 hrs of LRS3.\n\n"
        "LLM upgrade (Llama-2 \u2192 Llama 3.1 8B) requires adapter retraining "
        "but stacks with any data investment. Same hidden dimension (4096).\n\n"
        "GPU cost basis: AWS p4d.24xlarge 8\u00d7A100 spot at ~$9.39/hr.",
        [[tbl], [r1], [r2]], click_reveal=True)



def slide_a16(prs):
    """A8: LLM Judge x IS Tier cross-tabulation."""
    slide = new_slide(prs)
    add_title(slide, "A8: LLM Judge \u00d7 IS Tier Cross-Tabulation")
    add_accent_line(slide)

    add_text(slide,
        "How the LLM judge verdict distributes across IS quality tiers (blind evaluation):",
        MX, CT, CW, Inches(0.4), size=Pt(14), color=LGRAY)

    tbl = add_table(slide,
        ["IS Tier", "Y (count)", "Y%", "P (count)", "P%", "N (count)", "N%"],
        [["5 \u2014 Excellent (4.0\u20135.0)", "157", "56.9%", "105", "38.0%", "14", "5.1%"],
         ["4 \u2014 Good (3.0\u20133.99)", "67", "20.9%", "189", "58.9%", "65", "20.2%"],
         ["3 \u2014 Fair (2.0\u20132.99)", "25", "7.7%", "167", "51.4%", "133", "40.9%"],
         ["2 \u2014 Poor (1.0\u20131.99)", "14", "4.2%", "115", "34.2%", "207", "61.6%"],
         ["1 \u2014 Failed (0.0\u20130.99)", "5", "2.1%", "41", "17.2%", "193", "80.8%"]],
        MX, CT + Inches(0.5), Inches(10.0), text_size=Pt(11),
        row_height=Inches(0.38),
        col_widths=[Inches(2.8), Inches(1.2), Inches(1.0),
                    Inches(1.2), Inches(1.0), Inches(1.2), Inches(1.0)],
        row_colors={0: {2: GREEN}, 4: {6: CORAL}})

    # Key observations
    add_text(slide, "Key Observations:", MX, CT + Inches(2.95), CW, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_bullets(slide, [
        "IS Tier 5: 57% full Y \u2014 strong agreement on excellent output",
        "IS Tiers 2-3: majority P not N \u2014 judge sees partial value metrics miss",
        "IS Tier 1: 81% N \u2014 strong agreement on complete failure",
        ("Pearson r = 0.85 between IS and judge verdict (coded Y=3, P=2, N=1)",
         {"color": TEAL}),
        ("Two NIV thresholds beat legacy IS \u2265 3.0 (\u03ba=0.52): "
         "Y+P at IS \u2265 2.00 \u2192 \u03ba=0.82; Y at IS \u2265 3.80 \u2192 \u03ba=0.69",
         {"color": GOLD}),
    ], MX, CT + Inches(3.35), CW, Inches(2.0), size=Pt(13))

    _finish(slide, "A8",
        "LLM Judge cross-tabulated with IS tiers across all 1,497 segments "
        "(blind, Opus 4.6). Strong agreement at the extremes: 56.9% Y for "
        "Tier 5 (Excellent), 80.8% N for Tier 1 (Failed). The interesting "
        "middle: Tiers 2-3 get majority P verdicts (51.4% / 34.2%) — the "
        "LLM sees partial meaning preservation that strict word-level "
        "metrics miss. Pearson r=0.85 between IS and the judge ordinal "
        "(Y=3, P=2, N=1). Threshold sweep: Y+P aligns best with IS>=2.00 "
        "(kappa=0.818, 91.5% agreement); the legacy IS>=3.00 cutoff under-"
        "counts (kappa=0.521). NIV thresholds adopted in March 2026: "
        "IS>=3.80 for Y (kappa=0.690), IS>=2.00 for Y+P (kappa=0.818). IS "
        "beats WER at both operating points (+0.061 for Y, +0.041 for Y+P). "
        "Mention to peers: this cross-tab is the primary calibration "
        "evidence for using IS as a deterministic surrogate for the LLM "
        "judge in production. "
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/threshold_calibration_vs_opus.md.")


def slide_a17(prs):
    """A9: Context-aware transition matrix and per-topic deltas."""
    slide = new_slide(prs)
    add_title(slide, "A9: Context Evaluation \u2014 Transition Details")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — full transition matrix
    lt = add_text(slide, "Blind \u2192 Context Transition Matrix", MX, CT,
                  col_w, Inches(0.4), size=Pt(17), color=TEAL, bold=True)

    tbl1 = add_table(slide,
        ["Blind \u2193 / Ctx \u2192", "Y", "P", "N", "Total"],
        [["Y", "207", "138", "0", "345"],
         ["P", "17", "519", "90", "626"],
         ["N", "1", "48", "477", "526"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(12),
        col_widths=[Inches(1.5), Inches(0.9), Inches(0.9),
                    Inches(0.9), Inches(0.9)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    add_text(slide, "Dominant transition: Y\u2192P (138 cases, 40% of all Y)\n"
             "Only 1 N\u2192Y rescue across all 1,497 pairs",
             MX, CT + Inches(2.2), col_w, Inches(0.6),
             size=Pt(12), color=LGRAY)

    # Summary stats
    tbl2 = add_table(slide,
        ["Metric", "Value"],
        [["Total downgrades", "230 (15.4%)"],
         ["Total upgrades", "68 (4.5%)"],
         ["Unchanged", "1,199 (80.1%)"],
         ["Cross-condition agree.", "80.0%"]],
        MX, CT + Inches(3.0), col_w * 0.7, text_size=Pt(11))

    # Right — per-topic deltas
    rx = MX + col_w + gap
    rt = add_text(slide, "Per-Topic Y+P Delta (Blind \u2192 Context)", rx, CT,
                  col_w, Inches(0.4), size=Pt(17), color=CORAL, bold=True)

    tbl3 = add_table(slide,
        ["Topic", "Blind Y+P", "Ctx Y+P", "\u0394"],
        [["Business/Finance", "72%", "70%", "\u22122pp"],
         ["Education/Lecture", "67%", "64%", "\u22123pp"],
         ["Entertainment", "64%", "61%", "\u22123pp"],
         ["News/Politics", "65%", "62%", "\u22123pp"],
         ["Tech/Science", "62%", "59%", "\u22123pp"],
         ["Sports/Health", "60%", "57%", "\u22123pp"],
         ["DIY/Home", "48%", "44%", "\u22124pp"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(11),
        row_colors={6: {3: CORAL}})

    add_text(slide,
        "Context is uniformly stricter across all topics. DIY/Home has the "
        "largest delta (\u22124pp) \u2014 context reveals the most visual-content "
        "vocabulary failures.",
        rx, CT + Inches(3.65), col_w, Inches(0.6),
        size=Pt(12), color=LGRAY, italic=True)

    _finish(slide, "A9",
        "Full transition matrix and per-topic deltas for the context-aware "
        "Opus judge re-run on the same 1,497 pairs. The matrix shows the "
        "dominant pattern is Y -> P (138 of 345 Y verdicts, about 40% of "
        "all Y) — domain context reveals vocabulary failures the blind "
        "judge let slide. Total: 230 downgrades vs 68 upgrades, with "
        "1,199 (80.1%) verdicts unchanged. Only 1 N -> Y rescue across "
        "all 1,497 pairs, confirming context is a quality tool not a "
        "rescue tool. Per-topic Y+P deltas are uniformly negative "
        "(-2pp to -4pp) across all seven topics; DIY/Home has the "
        "largest drop at -4pp because it is the most visually-anchored "
        "domain (tools, materials, processes) where domain knowledge "
        "exposes vocabulary errors most aggressively. Mention to peers: "
        "this is the appendix-level evidence for the context-exposes-"
        "hidden-failures slide in Section 2. "
        "Sources: docs/evaluation/llm_judge/context_eval/context_eval_analysis.md, "
        "docs/evaluation/llm_judge/llm_judge_analysis.md.")


# ═══════════════════════════════════════════════════════════════════════
# APPENDIX (academic) — Human-IS Path B estimates (HIDDEN by default)
# ═══════════════════════════════════════════════════════════════════════

def slide_human_is_path_b(prs):
    """Appendix: Pre-study estimates of human IS performance (Path B).

    HIDDEN by default — these are estimates from the IS formula plugged with
    literature WER + component shifts, not measured human IS scores. Source:
    docs/evaluation/human_is_estimation.md and after_amosi_audit.json
    `human_is_*` keys (Section I).
    """
    slide = new_slide(prs)
    add_title(slide, "Appendix: Human-IS Path B (Pre-Study Estimates)")
    add_accent_line(slide)

    # Sub-header / framing
    add_text(slide,
        "Path B: bin model 1,497 segments by WER, plug literature WER + "
        "component shifts into the same IS formula. Estimates, not "
        "measurements — needs Path A pilot to confirm.",
        MX, CT, CW, Inches(0.6),
        size=Pt(13), color=LGRAY, italic=True)

    # Main table — populations vs IS (low / mid / high) + tier
    tbl = add_table(slide,
        ["Population", "low", "mid", "high", "tier (mid)"],
        [["Lay (no context)", "0.63", "0.92", "1.14", "Failed"],
         ["Deaf (no context)", "2.33", "2.74", "3.07", "Fair"],
         ["Expert (no context)", "2.60", "3.03", "3.33", "Fair"],
         ["Lay + ctx + model", "3.36", "3.83", "4.19", "Good"],
         ["Model alone (measured, MBR)", "—", "2.547", "—", "measured"]],
        MX, CT + Inches(0.7), CW * 0.78, text_size=Pt(12),
        row_height=Inches(0.4),
        col_widths=[Inches(3.4), Inches(1.1), Inches(1.1),
                    Inches(1.1), Inches(1.7)],
        # Highlight model row (last) in TEAL; expert in GOLD
        row_colors={4: {0: TEAL, 1: TEAL, 2: TEAL, 3: TEAL, 4: TEAL},
                    2: {0: GOLD},
                    3: {0: GREEN}})

    # Comparison call-outs
    add_text(slide, "Where the model sits",
             MX, CT + Inches(3.15), SLW, Inches(0.35),
             size=Pt(15), color=TEAL, bold=True)
    add_bullets(slide, [
        ("Model 2.547 ≈ deaf-no-context (2.74)", {"color": LGRAY}),
        ("Loses to expert by ~0.5", {"color": CORAL}),
        ("Loses to lay+ctx+model reviewer by ~1.3",
         {"color": CORAL, "bold": True}),
        ("Beats lay-no-context by ~1.6", {"color": GREEN}),
    ], MX, CT + Inches(3.55), SLW, Inches(1.6), size=Pt(12))

    # LR isolation note (right column)
    add_text(slide, "LR isolation experiment",
             SRL, CT + Inches(3.15), SRW, Inches(0.35),
             size=Pt(15), color=GOLD, bold=True)
    add_text(slide,
        "Human-style LR (skipping uncertain words) costs:\n"
        "  Lay: +0.41 IS  →  Deaf: +0.21  →\n"
        "  Expert: +0.15  →  Lay+ctx+model: +0.06\n\n"
        "Penalty shrinks with proficiency — fluency is a "
        "covert reward in current LR scaling.",
        SRL, CT + Inches(3.55), SRW, Inches(1.7),
        size=Pt(12), color=LGRAY)

    # Caveat strip
    # LAYOUT fix: was at y=6.9 h=0.5 (bot_gap 0.10, audit). Moved up to y=6.70
    # h=0.40 -> ends at 7.10, leaving 0.40" clearance from slide bottom (7.5).
    add_text(slide,
        "Caveat: Path B is pre-study. Reproducible Python snippet in "
        "docs/evaluation/human_is_estimation.md §4. "
        "Needs Path A pilot for measured ground truth.",
        MX, Inches(6.70), CW, Inches(0.40),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "A",
        "Appendix slide (HIDDEN by default in academic deck). Pre-study "
        "estimates of human IS performance via Path B: bin the model's "
        "1,497 segments by WER, plug literature WER + literature-derived "
        "component shifts into the same IS formula. NOT measurements — "
        "needs a Path A pilot (real lip readers on the same segments) to "
        "confirm. The model alone (2.547 under MBR aggregation, 2.52 "
        "pre-MBR top-1) sits roughly at deaf-no-context level, loses to "
        "expert by ~0.5, and loses to a lay+context+model reviewer by "
        "~1.3 IS. The LR isolation experiment shows that human-style "
        "lip-reading (skipping uncertain words) costs +0.41 IS for lay "
        "but only +0.06 for lay+ctx+model — the penalty shrinks with "
        "proficiency. See docs/evaluation/human_is_estimation.md for "
        "full methodology and reproducible Python snippet (§4).")


# ═══════════════════════════════════════════════════════════════════════
# APPENDIX (academic) — PCA Component Loadings (HIDDEN by default)
# ═══════════════════════════════════════════════════════════════════════

def slide_appendix_pca_loadings(prs):
    """Appendix: PCA loadings for the 6 IS signals.

    Reframes the old '3 dimensions' claim: Kaiser criterion retains 2 PCs.
    Semantic loads on PC1 alongside word-accuracy signals — it is NOT
    independent. Source: docs/evaluation/is_pca_analysis.md.
    """
    slide = new_slide(prs)
    add_title(slide, "Appendix: PCA Loadings on the 6 IS Signals")
    add_accent_line(slide)

    add_text(slide,
        "Kaiser criterion retains 2 components. Together they explain "
        "87.9% of variance.",
        MX, CT, CW, Inches(0.4),
        size=Pt(13), color=LGRAY)

    # Loadings table (PC1, PC2 only — PC3 dropped by Kaiser)
    tbl = add_table(slide,
        ["Signal", "PC1 (Signal Quality, 68.4%)",
         "PC2 (Output Length, 19.5%)"],
        [["Semantic",     "+0.445", "+0.057"],
         ["Phonetic",     "+0.466", "+0.184"],
         ["InvWER",       "+0.431", "−0.367"],
         ["InvWWER",      "+0.455", "−0.061"],
         ["NEA F1",       "+0.430", "−0.001"],
         ["LengthRatio",  "+0.083", "+0.908"]],
        MX, CT + Inches(0.55), CW * 0.62, text_size=Pt(12),
        row_height=Inches(0.34),
        col_widths=[Inches(2.0), Inches(3.2), Inches(2.6)],
        # Highlight the equally-loaded content cluster on PC1 (rows 0-4),
        # and the dominant LengthRatio loading on PC2 (row 5).
        row_colors={0: {1: TEAL}, 1: {1: TEAL}, 2: {1: TEAL},
                    3: {1: TEAL}, 4: {1: TEAL},
                    5: {2: GOLD}})

    # Right-side commentary card
    rx = MX + CW * 0.62 + Inches(0.2)
    rw = CW - (CW * 0.62 + Inches(0.2))

    r1 = add_rect(slide, rx, CT + Inches(0.55), rw, Inches(2.6),
                  fill_color=NAVY2, border_color=TEAL,
                  border_width=Pt(2), corner_radius=True)
    add_text(slide, "Reframing", rx + Inches(0.15), CT + Inches(0.65),
             rw - Inches(0.3), Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    add_bullets(slide, [
        "PC1 (68.4%) = signal quality — all 5 content "
        "signals load 0.43–0.47, virtually identical",
        ("Semantic is NOT an independent dimension — "
         "loads on PC1 with word-accuracy signals", {"color": GOLD}),
        "PC2 (19.5%) = output length — Length Ratio dominates at 0.91",
        ("The old '3 dimensions' framing was wrong",
         {"color": CORAL, "bold": True}),
    ], rx + Inches(0.15), CT + Inches(1.05), rw - Inches(0.3),
       Inches(2.1), size=Pt(12))

    # Bottom — key takeaway
    add_text(slide,
        "Practical implication: when the visual encoder works, ALL "
        "content metrics improve together. They are 5 views of the same "
        "underlying quality, not 5 independent axes.",
        MX, CT + Inches(3.35), CW, Inches(0.6),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # OVERLAP fix: source line at y=6.9, h=0.4 ended at 7.30 and crashed
    # into the slide-number ("A") shape at y=7.12. Move up to y=6.55 with
    # h=0.25 so it ends at y=6.80, well above the slide-num band.
    add_text(slide,
        "Source: docs/evaluation/is_pca_analysis.md §3.2",
        MX + Inches(1.2), Inches(6.62), CW - Inches(1.2), Inches(0.22),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "A",
        "Appendix slide (HIDDEN by default). PCA on the 6 standardized IS "
        "signals retains 2 principal components by the Kaiser criterion. "
        "PC1 explains 68.4% of variance — all 5 content signals "
        "(Semantic, Phonetic, InvWER, InvWWER, NEA F1) load nearly "
        "equally at 0.43–0.47, with Length Ratio near zero (0.083). "
        "PC2 explains 19.5% — dominated by Length Ratio at 0.908. "
        "Together: 87.9% of variance in 2 PCs. Key reframing: Semantic "
        "is NOT an independent dimension; it loads on PC1 alongside "
        "word-accuracy signals. The old '3 dimensions' claim was wrong. "
        "Practically: when the visual encoder captures the speech signal, "
        "all content metrics improve together — they are 5 views of "
        "the same underlying quality (visual encoder signal strength), "
        "not 5 independent axes. See docs/evaluation/is_pca_analysis.md "
        "section 3.2 for full loadings (PC3 included for reference).")


# ═══════════════════════════════════════════════════════════════════════
# APPENDIX (academic) — Full McNemar table (HIDDEN by default)
# ═══════════════════════════════════════════════════════════════════════

def slide_appendix_mcnemar_full(prs):
    """Appendix: Full per-method McNemar table on 5,988 verdicts.

    Source: docs/evaluation/after_amosi_audit.json `judge_*_mcnemar_*` keys
    and audit MD Section F.
    """
    slide = new_slide(prs)
    add_title(slide, "Appendix: McNemar Tests — N-Best Methods vs Baseline")
    add_accent_line(slide)

    add_text(slide,
        "Paired McNemar tests on 5,988 LLM-judge verdicts (Opus 4.7, "
        "v3 dual-conf prompt). Each cell counts the disagreements "
        "between baseline and the named method.",
        MX, CT, CW, Inches(0.55),
        size=Pt(13), color=LGRAY, italic=True)

    # Full McNemar table
    tbl = add_table(slide,
        ["Method", "Y meth-only", "Y base-only", "Y χ²", "Y p",
         "Y+P meth-only", "Y+P base-only", "Y+P χ²", "Y+P p"],
        [["hyp_mbr",        "59", "47", "1.14", "0.2853",
          "74", "34", "14.08", "0.00017"],
         ["hyp_vote_score", "59", "46", "1.37", "0.2416",
          "41", "28",  "2.09", "0.14856"],
         ["hyp_vote_conf",  "60", "69", "0.50", "0.4812",
          "65", "34",  "9.09", "0.00257"]],
        MX, CT + Inches(0.7), CW, text_size=Pt(11),
        row_height=Inches(0.45),
        col_widths=[Inches(1.7), Inches(1.2), Inches(1.2), Inches(0.8),
                    Inches(1.0), Inches(1.4), Inches(1.4),
                    Inches(0.9), Inches(1.5)],
        # Bold (via color highlight) the significant Y+P p-values
        row_colors={0: {8: GREEN},  # hyp_mbr Y+P p=0.00017 SIGNIFICANT
                    2: {8: GREEN}}) # hyp_vote_conf Y+P p=0.00257 SIGNIFICANT

    # Interpretation section
    add_text(slide, "Interpretation",
             MX, CT + Inches(2.6), CW, Inches(0.35),
             size=Pt(15), color=TEAL, bold=True)
    # OVERLAP fix (round 2): bullets h=2.2 ending at CT+5.2=6.65 collided 50%
    # with caveat at y=6.40 (audit MAJOR). Capped bullets at h=1.85 (ends
    # 6.30) so a 0.10" gap precedes the caveat. Caveat unchanged at y=6.40.
    add_bullets(slide, [
        ("hyp_mbr: +40 net Y+P wins, p = 0.00017 (highly significant)",
         {"color": GREEN, "bold": True}),
        ("hyp_vote_conf: +31 net Y+P wins, p = 0.00257 (significant)",
         {"color": GREEN}),
        "hyp_vote_score: +13 net Y+P wins, p = 0.149 (not significant)",
        ("Y verdict alone: all three methods statistically tied",
         {"color": LGRAY}),
        "Holds on text-differing subset: mbr p=0.004, vote_conf p=0.011",
    ], MX, CT + Inches(3.0), CW, Inches(1.85), size=Pt(12))

    # Caveat at y=6.40 -> 6.85 (clears bullets at 6.30, slide-num band at 7.12).
    add_text(slide,
        "Caveat: identical-text drift varies (12.6% / 10.4% / 14.2% per "
        "method). Not a confound to McNemar (paired test absorbs ties), "
        "but worth noting — v3 prompt's shared baseline_conf anchor "
        "reduced drift from v1's 27%.",
        MX + Inches(1.0), Inches(6.40), CW - Inches(1.0), Inches(0.45),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "A",
        "Appendix slide (HIDDEN by default). Full McNemar table for the "
        "three n-best aggregation methods vs baseline on 5,988 LLM-judge "
        "verdicts (Opus 4.7, v3 dual-conf prompt). Y verdict: all three "
        "methods are statistically tied with baseline (p ≥ 0.24). "
        "Y+P verdict: hyp_mbr +40 net wins (p = 0.00017, highly "
        "significant), hyp_vote_conf +31 net wins (p = 0.00257, "
        "significant), hyp_vote_score +13 net wins (p = 0.149, not "
        "significant). The significance survives restriction to the "
        "text-differing subset (mbr p = 0.004, vote_conf p = 0.011), "
        "ruling out an identical-text artefact. Note that identical-text "
        "drift varies per method (12.6% / 10.4% / 14.2%) but does not "
        "confound McNemar because the paired test absorbs ties. The v3 "
        "dual-conf prompt's shared baseline_conf anchor cut this drift "
        "from v1's 27%, so the remaining drift is balanced intra-rater "
        "noise rather than directional bias. Final shipping decision: "
        "pure hyp_mbr as the default displayed output (highest "
        "intra-rater 86.7%, calibrated per-word posterior compatible "
        "with the band-reliability UI thresholds). "
        "Sources: docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md, "
        "docs/beam-search/n_best_implementation.md, "
        "docs/evaluation/after_amosi_audit.md (Section F).")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE: CONFIDENCE SCORING — FUTURE DIRECTION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE: CONFIDENCE SCORING — FUTURE DIRECTION
# ═══════════════════════════════════════════════════════════════════════

def slide_confidence_scoring(prs):
    """Future direction: per-segment confidence — merged with Phase 1 detail."""
    slide = new_slide(prs)
    # audit:narrative_action \u2014 drop "Phase 1" planning label; feature shipped.
    add_title(slide, "Confidence Scoring (shipped April 30 2026) \u2014 Surface the Good 65%")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — What + How (merged, concise)
    lt = add_text(slide, "How It Works", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Beam search already computes probability scores \u2014 "
         "we just don\u2019t expose them yet", {"bold": True}),
        "Attach beam score + token entropy to each output segment",
        "High confidence (\u2265 0.8): trust as-is | "
        "Low (< 0.4): flag for review",
        ("No extra inference \u2014 scores are a free byproduct of decode",
         {"color": TEAL}),
        ("Effort: 2\u20134 hours implementation", {"color": GREEN, "bold": True}),
    ], MX, CT + Inches(0.45), col_w, Inches(2.8), size=Pt(14))

    # Effort callout
    r1 = add_rect(slide, MX, CT + Inches(3.5), col_w, Inches(0.5),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Reduces perceived error rate from 60% to ~20%",
             MX + Inches(0.3), CT + Inches(3.55), col_w - Inches(0.6), Inches(0.4),
             size=Pt(16), color=GREEN, bold=True)

    # Right — What It Enables
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "What It Enables", rx, CT, rw, Inches(0.35),
                  size=Pt(18), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "Users see only high-confidence segments by default",
        "Low-confidence segments flagged for human review",
        ("Entity-level: names/numbers missed in 85% of segments \u2014 "
         "confidence can flag these specifically", {"color": CORAL}),
    ], rx, CT + Inches(0.45), rw, Inches(2.5), size=Pt(14))

    bottom = add_text(slide,
        "The fastest path to user value \u2014 no retraining, no new data, "
        "no infrastructure changes.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Confidence scoring shipped April 30 2026. Beam search already "
        "computes per-token probabilities for every hypothesis; the "
        "feature simply exposes them. We attach beam score and token "
        "entropy to each segment, then derive a per-word band (green / "
        "yellow / red) and an aggregate sentence_confidence value. "
        "Production thresholds (May 2 2026): green requires top1_conf >= "
        "0.95 AND beam_agreement >= 0.80, yellow requires >= 0.65 AND >= "
        "0.50; numbers are capped at yellow. Reading-guide framing for "
        "clients: at >= 30% green coverage we hit ~65% recall of useful "
        "content with 5.6% false-positive rate. Perceived error rate "
        "drops from 60% to roughly 20% because the user reads only the "
        "trusted slice. The right-card 85% callout is the entity-level "
        "miss rate from the baseline analysis: names and numbers are "
        "missed in 85% of segments, and per-word confidence is the "
        "mechanism that flags them at output time. No retraining, no new "
        "data, no infrastructure change. Mention to peers: this is the "
        "foundation for the n-best aggregation and trust-gate slides "
        "later in the deck. "
        "Sources: docs/confidence/band_reliability_by_niv.md, "
        "docs/features/per-word-confidence-user-guide.md.",
        [[lt, lb], [r1], [rt, rb], [bottom]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE: THANK YOU / END
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE: THANK YOU / END
# ═══════════════════════════════════════════════════════════════════════

def slide_thank_you(prs):
    """Final slide: thank you and questions."""
    slide = new_slide(prs)

    add_text(slide, "Thank You",
             MX, Inches(2.0), CW, Inches(1.2),
             size=Pt(56), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(3.4), Inches(4.33), Inches(0.04),
             fill_color=TEAL)

    add_text(slide, "Questions & Discussion",
             MX, Inches(3.8), CW, Inches(0.6),
             size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER)

    add_text(slide,
        "1,497 segments  \u2022  Trust / Salvage / Strip three-tier UI  \u2022  "
        "8-stage pipeline  \u2022  cloud or on-prem deployment",
        MX, Inches(4.8), CW, Inches(0.8),
        size=Pt(15), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Final slide. Thank the audience and open for questions.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

