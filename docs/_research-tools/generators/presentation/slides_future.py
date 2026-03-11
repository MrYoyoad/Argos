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
    add_title(slide, "Starting from 61.6%, Not 25%")
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
        "25.5% useful by WER",
        "9 out of 10 segments fail",
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
        ("61.6% useful output (IS \u2265 2.00)", {"bold": True}),
        ("64.9% useful per Opus-as-a-Judge (Y+P = 971/1,497)",
         {"color": GREEN}),
        "Validated across 16 decode configs",
        "85% correlation between IS and Opus verdicts",
    ], mx2 + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=TEAL)

    # Right — larger image
    img = add_image(slide, "P1_quality", MX + 2 * col_w + 2 * gap, CT - Inches(0.1),
                    width=img_w)

    # Bottom
    add_text(slide,
             "The gap is real \u2014 but WER dramatically overstates failure. "
             "61.6% useful by IS (Y+P), 64.9% confirmed by Opus-as-a-Judge.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 24,
        "This is the turning point. WER says 25.5% useful. Our "
        "Intelligibility Score says 61.6% useful output (NIV Y+P) — 2.4x more. "
        "WER correlates with IS but not perfectly — it misses phonetic and "
        "semantic preservation, so it is not good enough as a sole metric. "
        "Opus-as-a-Judge confirms 64.9% useful output (Y+P = 971/1,497). "
        "Validated across 16 decode configs with 85% correlation.",
        [[r1], [r2, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

def slide_26(prs):
    slide = new_slide(prs)
    add_title(slide, "Five Phases — From IS 2.5 to Target IS 3.5–4.0")
    add_accent_line(slide)

    phases = [
        ("Phase 1", "Surface the good 65%",
         "Confidence scoring \u2014 flags known-good segments (2\u20134 hrs)",
         "Targets: Signal Loss (13.9%) | IS: filters to high-confidence subset (+0.3 perceived)", TEAL),
        ("Phase 2", "Fix small & content errors",
         "N-best aggregation (ROVER/MBR) \u2014 vote across 20 beams",
         "Targets: Accum. Errors (9.1%) + Details (13.8%) | IS: +0.3\u20130.5", TEAL),
        ("Phase 3", "Better world knowledge",
         "Llama 3.1 8B + context prompts",
         "Targets: Hallucination (18.8%) + Wrong Topic (44.4%) | IS: +0.5\u20130.8", GREEN),
        ("Phase 4", "Scale data 20K\u201350K",
         "Fine-tune visual encoder + projection on more data",
         "Targets: ALL categories via better visual features | IS: +0.5\u20131.0", GREEN),
        ("Phase 5", "Error Correction (GER)",
         "Second LLM corrects remaining decode errors",
         "Targets: residual errors post-Phase 1\u20134 | IS: +0.3\u20130.5", LGRAY),
    ]

    # Staircase on left side
    step_w = Inches(5.8)
    step_h = Inches(0.85)
    step_indent = Inches(0.35)
    start_y = CT
    start_x = MX

    step_shapes = []
    for i, (phase, desc, detail, is_note, color) in enumerate(phases):
        x = start_x + i * step_indent
        y = start_y + i * (step_h + Inches(0.08))
        w = step_w - i * step_indent
        r = add_rect(slide, x, y, w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        step_shapes.append(r)
        step_shapes.append(add_rich_text(slide, [
            [(phase, {"size": Pt(13), "color": color, "bold": True}),
             (f"  {desc}", {"size": Pt(13), "color": WHITE})],
            [(detail, {"size": Pt(11), "color": LGRAY, "italic": True}),
             (f"   {is_note}", {"size": Pt(11), "color": GOLD})],
        ], x + Inches(0.2), y + Inches(0.05), w - Inches(0.4), step_h - Inches(0.1)))

    # WER trajectory image on right
    img = add_image(slide, "P3_trajectory",
                    SRL - Inches(0.2), CT, width=SRW + Inches(0.2))

    bottom = add_text(slide,
             "Combined target: IS 3.5–4.0 (85–90% useful Y+P). "
             "Gains are multiplicative (ICLR 2024 scaling law).",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Academic references
    add_text(slide,
        "References: ROVER (Fiscus 1997)  |  GER (Chen et al. 2024)  |  "
        "LoRA Scaling (Biderman et al. 2024)",
        MX, Inches(6.80), CW, Inches(0.25),
        size=Pt(8), color=MGRAY, italic=True)

    _finish(slide, 26,
        "Five phases, each explicitly targeting failure mode categories from "
        "our error analysis.\n\n"
        "FAILURE MODE -> PHASE MAPPING:\n"
        "Phase 1 (Confidence): Signal Loss accounts for 13.9% of failures. "
        "Confidence scoring flags the 40% already good, giving immediate "
        "perceived improvement (+0.3 IS perceived, 2-4 hours).\n"
        "Phase 2 (N-Best): Accumulated Errors (9.1%) and Right Topic Wrong Details "
        "(13.8%) are exactly what voting/consensus fixes. Each word-level "
        "error corrected individually yields IS +0.3-0.5.\n"
        "Phase 3 (LLM Swap): Hallucination (18.8%) and Wrong Topic (44.4%) "
        "stem from Llama-2's weak world knowledge. Llama 3.1 8B has 3x the "
        "training data and 128K vocab, directly reducing these. IS +0.5-0.8.\n"
        "Phase 4 (Data Scaling): All failure categories improve because the "
        "visual encoder learns better lip representations. Biggest single gain "
        "IS +0.5-1.0.\n"
        "Phase 5 (GER): Post-hoc correction of whatever errors remain after "
        "Phases 1-4. IS +0.3-0.5.\n\n"
        "Combined target: IS 3.5-4.0 (85-90% useful Y+P). "
        "ICLR 2024 shows gains are multiplicative.",
        [step_shapes, [img, bottom]], click_reveal=True)


def slide_26b(prs):
    """26b: IS trajectory roadmap — parallel to WER trajectory on slide_26."""
    slide = new_slide(prs)
    add_title(slide, "IS Improvement Roadmap — From 2.5 to 3.8")
    add_accent_line(slide)

    add_text(slide, "Projected Intelligibility Score improvement per phase",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # IS trajectory plot (left side, large)
    img = add_image(slide, "P3b_is_trajectory",
                    MX, CT + Inches(0.45),
                    width=Inches(8.0))

    # Key milestones callout (right side) — with failure mode annotations
    rx = MX + Inches(8.3)
    rw = Inches(3.8)
    milestones = [
        ("Current", "IS 2.52", "61.6% useful (Y+P)", "", CORAL),
        ("Phase 1\u20132", "IS ~2.85",  "~72% useful (Y+P)",
         "Fixes: Signal Loss (13.9%), Accum. Errors (9.1%), Details (13.8%)", TEAL),
        ("+ Phase 3", "IS ~3.40", "~83% useful (Y+P)",
         "Fixes: Hallucination (18.8%), Wrong Topic (44.4%)", GREEN),
        ("+ Phase 4\u20135", "IS ~3.80", "~90% useful (Y+P)",
         "Fixes: all remaining via data + post-correction", GREEN),
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
            delta = float(is_val.replace("IS ~", "")) - 2.52
            ms_shapes.append(add_text(slide, f"+{delta:.2f}  |  {failure_note}",
                     rx + Inches(0.15), y + Inches(0.65),
                     rw - Inches(0.3), Inches(0.35),
                     size=Pt(11), color=WHITE, italic=True))

    bottom = add_text(slide,
             "Each ~10pp WER reduction \u2192 ~0.3\u20130.5 IS improvement + ~8\u201312pp useful rate.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "26b",
        "IS improvement trajectory with failure mode annotations. "
        "Current IS 2.52 (61.6% useful, NIV Y+P). "
        "Phase 1-2 target IS ~2.85 (~72% useful) by fixing Signal Loss (13.9%), "
        "Accumulated Errors (9.1%), and Right Topic Wrong Details (13.8%). "
        "Phase 3 target IS ~3.40 (~83% useful) by fixing Hallucination (18.8%) "
        "and Wrong Topic (44.4%) via stronger LLM world knowledge. "
        "Phase 4-5 target IS ~3.80 (~90% useful) by improving visual encoder "
        "with more data and post-hoc error correction. "
        "Each phase targets specific failure categories, and the magnitude "
        "reflects the proportion of errors in that category.",
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
        "Brief summary of confidence scoring. Detail covered in previous slide. "
        "Key points: beam scores already exist, 2-4 hours implementation, "
        "perceived error rate drops from 60% to 20%.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

def slide_28(prs):
    """Phase 2: N-best aggregation with ROVER/MBR explanation."""
    slide = new_slide(prs)
    add_title(slide, "Phase 2: Exploit All 20 Hypotheses")
    add_accent_line(slide)

    # Main point
    add_text(slide, "Currently discarding 19 of 20 beam candidates",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=WHITE, bold=True)

    # Two technique cards side by side
    cw = Inches(5.5)
    gap = Inches(1.13)
    cy = CT + Inches(0.55)
    ch = Inches(2.2)

    r1 = add_rect(slide, MX, cy, cw, ch, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "ROVER", MX + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=TEAL, bold=True)
    add_text(slide, "Recognizer Output Voting Error Reduction",
             MX + Inches(0.2), cy + Inches(0.4), cw - Inches(0.4), Inches(0.25),
             size=Pt(11), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Align all 20 hypotheses word-by-word",
        "Vote at each position \u2014 most common word wins",
        "Reduces random substitution errors",
    ], MX + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    rx = MX + cw + gap
    r2 = add_rect(slide, rx, cy, cw, ch, fill_color=NAVY2,
                  border_color=GREEN, border_width=Pt(2), corner_radius=True)
    add_text(slide, "MBR", rx + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=GREEN, bold=True)
    add_text(slide, "Minimum Bayes Risk Decoding",
             rx + Inches(0.2), cy + Inches(0.4), cw - Inches(0.4), Inches(0.25),
             size=Pt(11), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Score each hypothesis against ALL others",
        "Pick the one most similar to the consensus",
        "Best single hypothesis, no alignment needed",
    ], rx + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    # Impact summary
    iy = cy + ch + Inches(0.3)
    impact = add_bullets(slide, [
        ("Expected: 5\u201315% relative IS improvement", {"color": TEAL, "bold": True}),
        "Targets: Accumulated Errors (9.1%) \u2014 the \"death by a thousand cuts\" category",
        "Moves borderline segments into clearly useful range (IS \u2265 3.80)",
    ], MX, iy, CW, Inches(1.5), size=Pt(14))

    # Academic references
    add_text(slide,
        "ROVER: Fiscus (1997), NIST  |  MBR Decoding: Kumar & Byrne (2004), HLT-NAACL",
        MX, Inches(6.55), CW, Inches(0.3),
        size=Pt(8), color=MGRAY, italic=True)

    _finish(slide, 28,
        "Phase 2 exploits beam search output. Currently we keep only the top "
        "hypothesis and throw away 19 alternatives. ROVER aligns all 20 and "
        "votes word-by-word. MBR picks the hypothesis closest to the consensus. "
        "Both are established ASR techniques with consistent 5-15% gains. "
        "Targets the Accumulated Errors category (9.1% of failures).",
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
    plot_h = Inches(3.5)
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
        "Fine-tuning experiments with LoRA on 1,273 segments. Graphs are now "
        "larger for visibility. Exp A (rank 16): best val at epoch 2, then "
        "overfitting. Exp B (rank 64): 3.1pp worse. IS decreased: baseline "
        "2.49, Exp A 2.31, Exp B 2.02. Empty outputs: 7% to 13% to 27%. "
        "Bottleneck is data quantity (need 20K+).",
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

    # Academic references
    add_text(slide,
        "GER: Chen et al. (2024), ICASSP  |  "
        "Scaling Laws: Hoffmann et al. (2022), NeurIPS (Chinchilla)",
        MX, Inches(6.55), CW, Inches(0.3),
        size=Pt(8), color=MGRAY, italic=True)

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
        "language disambiguation is the primary bottleneck for our failure modes.",
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
        t1 = add_text(slide, label,
                      rx + Inches(0.2), wy + Inches(0.10),
                      right_w - Inches(1.6), Inches(0.35),
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
        "(204 segments) and accumulated errors (220 segments)",
        rx + Inches(0.2), ky + Inches(0.10),
        right_w - Inches(0.4), Inches(0.55),
        size=Pt(13), color=WHITE)

    _finish(slide, 0,
        "LLM upgrade analysis — simplified view.\n\n"
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
        "Scaling Laws (Zhang et al., ICLR 2024), Llama 3 (Meta, 2024).",
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
         "AV-HuBERT learned English mouth shapes (visemes). Arabic has different "
         "phonemes (pharyngeals, emphatics) producing distinct lip movements \u2014 "
         "without fine-tuning, Arabic lips map to wrong English clusters"),
        (TEAL,  "Arabic LLM backend",
         "Swap Llama-2 for Arabic-capable LLM (e.g. Jais, AceGPT, "
         "or Arabic-tuned Llama 3) \u2014 Arabic tokenizer quality varies"),
        (CORAL, "Arabic evaluation dataset (UNKNOWN)",
         "No Arabic lip-reading benchmark exists. Manual transcriptions "
         "needed for MSA + dialect coverage \u2014 requires native speakers, "
         "timeline uncertain"),
        (GREEN, "Training infrastructure",
         "AWS GPU instance (existing) for AV-HuBERT fine-tuning "
         "and K-means reclustering on Arabic mouth shapes"),
        (CORAL,  "RTL text & normalization (minor integration)",
         "RTL text handling may need research; spaCy Arabic, "
         "diacritic handling, Arabic NER \u2014 maturity unknown"),
    ]

    topic_groups = []
    by = CT + Inches(0.45)
    for clr, heading, detail in topics:
        grp = []
        grp.append(add_bullets(slide, [
            (heading, {"bold": True, "color": clr}),
            detail,
        ], MX, by, col_w, Inches(0.75), size=Pt(13)))
        topic_groups.append(grp)
        by += Inches(0.75)

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

    # Timeline summary callout (below last topic item which extends to ~y=6.05")
    timeline_box = add_rect(slide, MX, Inches(5.85), CW, Inches(0.55),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    timeline_txt = add_text(slide,
             "Realistic estimate: 2\u20133 months (encoder pre-training is the bottleneck)",
             MX + Inches(0.3), Inches(5.90), CW - Inches(0.6), Inches(0.4),
             size=Pt(20), color=CORAL, bold=True, align=PP_ALIGN.CENTER)

    # Bottom note (below callout box)
    note = add_text(slide,
        "Pipeline code is language-agnostic. Main bottlenecks: encoder pre-training "
        "data and eval dataset collection. No Arabic lip-reading benchmark exists.",
        MX, Inches(6.45), CW, Inches(0.35),
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

    takeaways = [
        ("1", "Rigorous assessment: 2.5\u00d7 WER gap on 1,497 segments. "
              "Novel IS metric reveals 61.6% useful output (NIV Y+P), "
              "confirmed by LLM judge at 64.9%. Full failure analysis "
              "with improvement suggestions."),
        ("2", "Production system delivered: standalone container with "
              "professional UI, 37 bugs fixed, 8-stage pipeline, 37 tests, "
              "8 research reports \u2014 all from a paper with no working "
              "environment."),
        ("3", "Model performs well: ~65% of videos produce useful output. "
              "IS metric shows high agreement with LLM judge and runs "
              "entirely on the standalone computer \u2014 no cloud dependency."),
        ("4", "Clear path forward: confidence scoring + N-best aggregation "
              "+ LLM upgrade to improve English performance. Full plan to "
              "replicate the approach for an Arabic model in 2\u20133 months."),
    ]

    card_h = Inches(1.05)
    gap = Inches(0.12)
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
                      MX + Inches(1.0), y + Inches(0.12),
                      CW - Inches(1.2), card_h - Inches(0.24),
                      size=Pt(15), color=WHITE)
        card_groups.append([r, circle, nt, tb])

    _finish(slide, 31,
        "Four takeaways. One: rigorous assessment with novel IS metric and "
        "full failure analysis. Two: production system built from scratch. "
        "Three: model performs well, 65% useful, IS runs locally. "
        "Four: clear path forward for English improvement and Arabic adaptation.",
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
        "50-70% of sounds invisible on lips. Admiral/animal, mom/bomb — "
        "context is the only way to disambiguate. This is why the LLM matters.",
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

    # Dimension table
    add_text(slide, "The 6 IS signals collapse into 3 independent dimensions:",
             MX, CT, CW * 0.55, Inches(0.4), size=Pt(14), color=WHITE)

    tbl1 = add_table(slide,
        ["Dimension", "Signals", "Variance", "Inter-signal r"],
        [["Word Accuracy", "WER, WWER, Phonetic", "60.0%", "> 0.79"],
         ["Meaning Preservation", "Semantic", "28.5%", "independent"],
         ["Output Sanity", "Length Ratio", "9.1%", "independent"]],
        MX, CT + Inches(0.5), CW * 0.55, text_size=Pt(11),
        row_height=Inches(0.32))

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
        "PCA retains 2 PCs: signal quality (68.4%, all 5 content signals load "
        "equally) and output length (19.5%, Length Ratio). Cross-config: "
        "Semantic, Phonetic, NEA are stable; WER and Length Ratio are volatile. "
        "IS vs Opus judge: κ=0.818 at Y+P (IS≥2.00), κ=0.690 at Y (IS≥3.80).")


def slide_a11(prs):
    """A4: LLM Salvage — Recoverable Segments."""
    slide = new_slide(prs)
    add_title(slide, "A4: LLM Salvage — Recoverable Segments")
    add_accent_line(slide)

    # Key numbers
    add_text(slide, "Key Numbers", MX, CT, SLW, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    tbl1 = add_table(slide,
        ["Metric", "Value"],
        [["Metric-failed segments", "900"],
         ["LLM-recoverable", "165 (18.3%)"],
         ["Useful output (IS ≥ 2.00)", "61.6%"],
         ["LLM Judge confirms (Y+P)", "64.9%"],
         ["IS vs Judge agreement", "κ = 0.818"]],
        MX, CT + Inches(0.4), SLW, text_size=Pt(11),
        row_colors={1: {1: TEAL}, 3: {1: TEAL}})

    add_text(slide, "58% of salvageable have moderate WER (50–70%).\n"
             "Decision tree: 15 rules, r=0.934 with IS.",
             MX, CT + Inches(2.8), SLW, Inches(0.6),
             size=Pt(11), color=LGRAY)

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
             SRL, CT + Inches(3.2), SRW, Inches(0.5),
             size=Pt(11), color=LGRAY, italic=True)

    _finish(slide, "A4",
        "165 of 900 metric-failed segments are recoverable by the LLM "
        "heuristic. Useful output rate is 61.6% (NIV Y+P). "
        "6 recovery categories (overlap, not disjoint). "
        "58% have moderate WER (50-70%).")


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

    tbl = add_table(slide,
        ["Mode", "Reference", "Hypothesis", "WER", "IS"],
        [["Empty Output",
          '"do you say i wonder what..."',
          "(empty)", "100%", "0.00"],
         ["Hallucination",
          '"and body parts"',
          '"20 years ago when i was"', "200%", "0.00"],
         ["Truncation",
          '"i don\'t want to say mistakes but i will say..."',
          '"i don\'t want to seem disrespectful"', "69%", "1.26"],
         ["Topic Drift",
          '"i\'ve made lots of videos..."',
          '"when i was a little girl..."', "97%", "0.38"],
         ["Entity Destruction",
          '"china to take off to cross the pacific ocean..."',
          '"i don\'t think that\'s a good idea"', "100%", "0.72"],
         ["Phonetic Wrong Topic",
          '"they have something like..."',
          '"some english for you all..."', "100%", "0.94"],
         ["High Error Rate",
          '"today here the three in one..."',
          '"i\'m so happy to be here..."', "100%", "1.13"],
         ["Accum. Small Errors",
          '"you\'re rich no no no..."',
          '"your ring that\'s not what..."', "67%", "1.64"],
         ["Content Word Errors",
          '"even after the insurance..."',
          '"after the initial contamination"', "60%", "1.86"],
         ["Over-generation",
          '"to the next level"',
          '"to the next level and they..."', "100%", "2.32"]],
        MX, CT + Inches(0.4), CW, text_size=Pt(9),
        row_height=Inches(0.42),
        row_colors={0: {4: CORAL}, 1: {4: CORAL}, 3: {4: CORAL},
                    4: {4: CORAL}, 5: {4: CORAL}})

    _finish(slide, "A6",
        "5 failure categories with real examples from the 1,497-segment "
        "baseline. Wrong Topic is the largest (44.4%). Hallucination is the "
        "most dangerous — fluent but completely fabricated text.")


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
        tbl_x, CT + Inches(0.55), tbl_w, text_size=Pt(15),
        col_widths=[Inches(3.8), Inches(2.4), Inches(2.8)],
        row_height=Inches(0.6),
        row_colors={1: {1: GREEN, 2: GREEN}})

    # Key insight callout
    ins_y = CT + Inches(2.8)
    r1 = add_rect(slide, MX, ins_y, CW, Inches(1.3),
                   fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                   corner_radius=True)
    add_text(slide, "Key insight",
             MX + Inches(0.25), ins_y + Inches(0.12),
             Inches(3.0), Inches(0.3), size=Pt(16), color=GOLD, bold=True)
    add_bullets(slide, [
        "Paper used only 433 hrs of LRS3 \u2014 we need 20\u201350K hrs of diverse data",
        ("Same training recipe, same model architecture \u2014 just more data",
         {"color": TEAL}),
        "Current IS 2.52 \u2192 target IS 3.5\u20134.0 requires ~46\u2013115\u00d7 data scale-up",
    ], MX + Inches(0.2), ins_y + Inches(0.45), CW - Inches(0.4), Inches(0.8),
        size=Pt(14))

    # LLM upgrade — requires adapter retraining but stacks with data investment
    llm_y = ins_y + Inches(1.55)
    r2 = add_rect(slide, MX, llm_y, CW, Inches(0.8),
                   fill_color=NAVY2, border_color=TEAL, border_width=Pt(1),
                   corner_radius=True)
    add_text(slide, "LLM upgrade: Llama-2 \u2192 Llama 3.1 8B  "
             "(+0.3\u20130.5 IS, requires adapter retraining, stacks with data investment)",
             MX + Inches(0.25), llm_y + Inches(0.2),
             CW - Inches(0.5), Inches(0.4),
             size=Pt(14), color=TEAL)

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
        ("Y+P peaks at IS \u2265 2.0 (\u03ba=0.82) not IS \u2265 2.00 (\u03ba=0.52) "
         "\u2014 systems agree on ranking, differ on threshold",
         {"color": GOLD}),
    ], MX, CT + Inches(3.35), CW, Inches(2.0), size=Pt(13))

    _finish(slide, "A8",
        "LLM Judge cross-tabulated with IS tiers. Strong agreement at the "
        "extremes: 57% Y for Tier 5, 81% N for Tier 1. The interesting "
        "middle: Tiers 2-3 get majority P verdicts — the LLM sees partial "
        "meaning preservation that strict metrics miss. Pearson r=0.85. "
        "Threshold sweep: Y+P aligns best with IS>=2.00 (kappa=0.818, "
        "91.5% agreement). NIV thresholds: IS>=3.80 for Y (kappa=0.690), "
        "IS>=2.00 for Y+P (kappa=0.818). IS beats WER at both operating points.")


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
        "Full transition matrix and per-topic deltas for context-aware "
        "evaluation. 230 downgrades vs 68 upgrades. Dominant: Y to P (138). "
        "Context is uniformly stricter across all 7 topics, with DIY/Home "
        "showing the largest delta. Cross-condition agreement: 80.0%.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE: CONFIDENCE SCORING — FUTURE DIRECTION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE: CONFIDENCE SCORING — FUTURE DIRECTION
# ═══════════════════════════════════════════════════════════════════════

def slide_confidence_scoring(prs):
    """Future direction: per-segment confidence — merged with Phase 1 detail."""
    slide = new_slide(prs)
    add_title(slide, "Phase 1: Confidence Scoring \u2014 Surface the Good 65%")
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
        "Merged confidence scoring slide. Beam search already computes "
        "probability scores for every hypothesis. We attach beam score and "
        "token entropy to each segment. High-confidence outputs are trusted, "
        "low-confidence flagged for review. 2-4 hours implementation. "
        "Perceived error rate drops from 60% to ~20%. No retraining needed.",
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
        "1,497 segments  \u2022  6 quality signals  \u2022  5 failure categories  "
        "\u2022  13 experiments\n"
        "8-stage pipeline  \u2022  37 bugs fixed  \u2022  8 research reports",
        MX, Inches(4.8), CW, Inches(0.8),
        size=Pt(15), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Final slide. Thank the audience and open for questions.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

