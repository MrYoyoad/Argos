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
    add_title(slide, "Starting from 40%, Not 11%")
    add_accent_line(slide)

    col_w = Inches(3.8)
    img_w = Inches(4.2)
    gap = Inches(0.3)

    # Left column — WER Says (coral)
    r1 = add_rect(slide, MX, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=CORAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "WER Says", MX + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=CORAL, bold=True)
    add_bullets(slide, [
        "11.4% usable",
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
        ("39.9% properly captured (IS ≥ 3.0)", {"bold": True}),
        ("50.9% with LLM salvage (165 recoverable segments)",
         {"color": GREEN}),
        "Validated across 16 decode configs",
        "Expert heuristic: 88.6% agreement, r=0.925 (no runtime LLM)",
    ], mx2 + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=TEAL)

    # Right — image
    img = add_image(slide, "P1_quality", MX + 2 * col_w + 2 * gap, CT,
                    width=img_w)

    # Bottom
    add_text(slide,
             "The gap is real — but WER dramatically overstates failure. "
             "40% works, 51% with LLM salvage.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 24,
        "This is the turning point. WER says 11.4% usable. Our "
        "Intelligibility Score says 39.9% properly captured — 3.5x more. "
        "LLM salvage analysis identified 165 additional recoverable segments, "
        "raising effective capture to 50.9%. Validated across 16 configs.",
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
        ("Phase 1", "Surface the good 40%", "Confidence scoring — attach beam probabilities to outputs (2–4 hrs)",
         "IS: identify segments already ≥ 3.0", TEAL),
        ("Phase 2", "Improve the fair 22%", "N-best aggregation — vote across all 20 beam hypotheses (ROVER/MBR)",
         "IS: +0.3–0.5 from better hypothesis selection", TEAL),
        ("Phase 3", "LLM swap + smart prompts", "Llama 3.1 8B + context prompts",
         "IS: +0.5–0.8 from stronger language model", GREEN),
        ("Phase 4", "Scale data 20K–50K", "Fine-tune with more data",
         "IS: +0.5–1.0 — biggest single gain", GREEN),
        ("Phase 5", "Error Correction (GER)", "Second LLM catches hallucinations",
         "IS: +0.3–0.5 from post-processing cleanup", LGRAY),
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
             "Combined target: IS 3.5–4.0 (55–65% captured). "
             "Gains are multiplicative (ICLR 2024 scaling law).",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 26,
        "Five phases, each targeting different bottlenecks. Phase 1 is "
        "immediate: confidence scoring to surface the 40% that's already "
        "good (2-4 hours). Phase 2: N-best aggregation (ROVER/MBR). Phase 3: swap LLM "
        "to Llama 3.1 8B plus smart prompts. Phase 4: the biggest gain — "
        "scale training data. Phase 5: Error Correction (GER) post-processing. "
        "Key: ICLR 2024 shows these gains are multiplicative.\n\n"
        "HOW THIS TRANSLATES TO IS:\n"
        "Current: WER 64.1% -> IS 2.52 (39.9% captured).\n"
        "Each ~10pp WER reduction typically improves IS by ~0.3-0.5 points "
        "and captured rate by ~8-12pp.\n"
        "Phase 3 target (42% WER) would project to roughly IS 3.5-4.0 and "
        "55-65% captured rate.\n"
        "The relationship is non-linear — improvements accelerate as more "
        "segments cross the IS >= 3.0 threshold.",
        [step_shapes, [img, bottom]], click_reveal=True)


def slide_26b(prs):
    """26b: IS trajectory roadmap — parallel to WER trajectory on slide_26."""
    slide = new_slide(prs)
    add_title(slide, "IS Improvement Roadmap — From 2.5 to 3.8")
    add_accent_line(slide)

    add_text(slide, "Projected Intelligibility Score improvement per phase",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # IS trajectory plot (right side, large)
    img = add_image(slide, "P3b_is_trajectory",
                    MX + Inches(0.5), CT + Inches(0.45),
                    width=Inches(7.0))

    # Key milestones callout (right side)
    rx = MX + Inches(7.8)
    rw = Inches(4.0)
    milestones = [
        ("Current", "IS 2.52", "39.9% captured", CORAL),
        ("Phase 1", "IS ~2.85", "~48% captured", TEAL),
        ("Phase 2", "IS ~3.40", "~58% captured", GREEN),
        ("Phase 3", "IS ~3.80", "~65% captured", GREEN),
    ]
    ms_shapes = []
    for i, (phase, is_val, cap_val, color) in enumerate(milestones):
        y = CT + Inches(0.55) + i * Inches(1.15)
        ms_shapes.append(add_rect(slide, rx, y, rw, Inches(0.95), fill_color=NAVY2,
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
            ms_shapes.append(add_text(slide, f"+{delta:.2f} from baseline",
                     rx + Inches(0.15), y + Inches(0.63),
                     rw - Inches(0.3), Inches(0.25),
                     size=Pt(10), color=LGRAY, italic=True))

    bottom = add_text(slide,
             "Each ~10pp WER reduction \u2192 ~0.3\u20130.5 IS improvement + ~8\u201312pp captured rate.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "26b",
        "IS improvement trajectory paralleling the WER reduction roadmap. "
        "Current IS 2.52 (39.9% captured) \u2192 Phase 3 target IS 3.80 (65% captured). "
        "The IS \u2265 3.0 threshold marks 'captured' segments. "
        "Key insight: relationship is non-linear \u2014 improvements accelerate as more "
        "segments cross the IS \u2265 3.0 threshold.",
        [[img], ms_shapes + [bottom]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

def slide_27(prs):
    slide = new_slide(prs)
    add_title(slide, "Phase 1: Confidence Scoring \u2014 Surface the Good 40%")
    add_accent_line(slide)

    col_w = Inches(5.8)
    gap = Inches(0.53)

    # Left — The Idea
    lt = add_text(slide, "The Idea", MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Beam search already computes probability scores "
         "for every hypothesis", {"bold": True}),
        "We just don\u2019t expose them yet",
        "Confidence = attaching these scores to outputs",
        ("No extra model inference \u2014 scores are a "
         "free byproduct of decode", {"color": TEAL}),
    ], MX, CT + Inches(0.5), col_w, Inches(2.5), size=Pt(16))

    # Effort callout
    r1 = add_rect(slide, MX, CT + Inches(3.2), col_w, Inches(0.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Effort: 2\u20134 hours implementation",
             MX + Inches(0.3), CT + Inches(3.25), col_w - Inches(0.6), Inches(0.5),
             size=Pt(18), color=GREEN, bold=True)

    # Right — What It Enables
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "What It Enables", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "Users see only high-confidence segments by default",
        "Low-confidence segments flagged for human review",
        ("Reduces perceived error rate from 60% to ~20%",
         {"bold": True, "color": GREEN}),
        "Business/Finance segments (57% captured) get highest confidence",
        "Short segments (<10 words, 32%) need lower thresholds",
        ("Entity-level: names, numbers, and places missed in 85% of "
         "segments — confidence scoring can flag these specifically",
         {"color": CORAL}),
    ], rx, CT + Inches(0.5), rw, Inches(3.5), size=Pt(14))

    _finish(slide, 27,
        "Phase 1 is the quick win. Beam search already computes probability "
        "scores for every hypothesis — we just don't surface them. Confidence "
        "scoring means attaching these scores to outputs so users can trust "
        "high-confidence results and flag low-confidence for review. No extra "
        "model inference needed — the scores are a free byproduct of decode. "
        "2-4 hours of implementation. Entity-level analysis shows names, "
        "numbers, and places are missed in 85% of segments.",
        [[lt, lb], [r1], [rt, rb]], click_reveal=True)

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
        "Targets: Accumulated Errors (24.4%) \u2014 the \"death by a thousand cuts\" category",
        "Moves IS 2.0\u20132.9 segments above the 3.0 threshold",
    ], MX, iy, CW, Inches(1.5), size=Pt(14))

    _finish(slide, 28,
        "Phase 2 exploits beam search output. Currently we keep only the top "
        "hypothesis and throw away 19 alternatives. ROVER aligns all 20 and "
        "votes word-by-word. MBR picks the hypothesis closest to the consensus. "
        "Both are established ASR techniques with consistent 5-15% gains. "
        "Targets the Accumulated Errors category (24.4% of failures).",
        [[r1], [r2], [impact]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

def slide_29(prs):
    slide = new_slide(prs)
    add_title(slide, "Fine-Tuning Experiments: Limited Data, Limited Gains")
    add_accent_line(slide)

    # Dashboard image — top half
    img = add_image(slide, "ft_clean", MX, CT, width=CW,
                    height=Inches(2.8))

    # Two columns below
    col_w = Inches(5.5)
    gap = Inches(1.13)
    col_y = CT + Inches(3.0)

    # Left — Exp A/B Results
    lt = add_text(slide, "What We Tried", MX, col_y, col_w, Inches(0.3),
                  size=Pt(15), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("Small-scale LoRA fine-tune with only 1,273 segments",
         {"bold": True}),
        "Exp A (rank 16): best val accuracy 62.94% at epoch 2",
        ("Exp B (rank 64): 3.1pp WORSE — more params = faster overfitting",
         {"color": CORAL}),
        ("Result: data too limited for LoRA to generalize",
         {"bold": True, "color": GOLD}),
    ], MX, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    # Right — IS Impact
    rx = MX + col_w + gap
    rt = add_text(slide, "Impact on Intelligibility", rx, col_y, col_w,
                  Inches(0.3), size=Pt(15), color=TEAL, bold=True)
    rb = add_bullets(slide, [
        "Baseline IS: 2.49 — Exp A IS: 2.31 — Exp B IS: 2.02",
        ("Fine-tuning made IS WORSE, not better", {"color": CORAL}),
        "Empty outputs: 7% → 13% → 27% (identifiable and filterable)",
        ("Key insight: need 20K+ segments, not parameter tuning",
         {"bold": True, "color": GREEN}),
    ], rx, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    _finish(slide, 29,
        "Fine-tuning experiments with LoRA on 1,273 segments. Exp A (rank 16): "
        "62.94% val accuracy, severe overfitting. Exp B (rank 64): 3.1pp worse. "
        "IS scores actually decreased: baseline 2.49, Exp A 2.31, Exp B 2.02. "
        "Empty outputs increased dramatically. The bottleneck is data quantity "
        "(need 20K+), not model capacity or parameter tuning.",
        [[img], [lt, lb], [rt, rb]], click_reveal=True)

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
        ("LLM Swap (immediate)", [
            "Llama 3.1 8B: drop-in (same hidden_size 4096)",
            "Quality ≈ Llama-2 70B, 128K vocab, 128K context",
            ("Setup: 1-2 hours", {"bold": True}),
            "Alone: -3 to -8pp WER",
        ], TEAL),
        ("Smart Prompts (force multiplier)", [
            "7 strategies: topic context, word count, anti-hallucination, GER",
            "Llama-2: +5-10pp | Llama 3.1: +12-20pp",
            ("GER post-processing: +8-15pp, no retraining", {"color": GREEN}),
        ], CORAL),
        ("Future", [
            "Arabic (K-means model exists)",
            "VALLR: 18.7% WER with 3B model",
            "Multi-speaker, streaming",
        ], LGRAY),
    ]

    cw = Inches(3.6)
    gap = Inches(0.5)
    total = 3 * cw + 2 * gap
    cx = (SL_W - total) / 2

    col_shapes = []
    for i, (title, items, color) in enumerate(cols):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, CT, cw, Inches(4.8), fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, title, x + Inches(0.2), CT + Inches(0.15),
                 cw - Inches(0.4), Inches(0.45),
                 size=Pt(15), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_bullets(slide, items, x + Inches(0.2), CT + Inches(0.7),
                    cw - Inches(0.4), Inches(3.5), size=Pt(13))
        col_shapes.append(r)

    _finish(slide, 30,
        "Three columns of future capability. Left: LLM swap to Llama 3.1 "
        "8B is trivial — same hidden dimension, 1-2 hours. Center: 7 prompt "
        "strategies are a force multiplier — more effective on stronger "
        "models. GER uses N-best hypotheses + correction LLM for +8-15pp "
        "with no retraining. Right: Arabic support exists, VALLR achieves "
        "18.7% WER with a 3B model.",
        [col_shapes])

# ═══════════════════════════════════════════════════════════════════════
# ARABIC PIPELINE ROADMAP
# ═══════════════════════════════════════════════════════════════════════

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

    # Left — what's needed + how we solve it
    lt = add_text(slide, "What\u2019s Needed & How We\u2019ll Do It",
                  MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Arabic AV-HuBERT encoder", {"bold": True, "color": TEAL}),
        "Fine-tune English AV-HuBERT on Arabic visual speech data \u2014 "
        "AVSpeech dataset has Arabic videos available for training",
        ("Arabic LLM backend", {"bold": True, "color": TEAL}),
        "Swap Llama-2 for Arabic-capable LLM (e.g. Jais, AceGPT, "
        "or Arabic-tuned Llama 3) with Arabic tokenizer",
        ("Training infrastructure", {"bold": True, "color": GREEN}),
        "AWS GPU instance (existing) for AV-HuBERT fine-tuning "
        "and K-means reclustering on Arabic mouth shapes",
        ("Arabic evaluation dataset", {"bold": True, "color": CORAL}),
        "Manual transcriptions needed for MSA + dialect coverage \u2014 "
        "the main bottleneck (requires native speakers)",
        ("Text normalization", {"bold": True, "color": TEAL}),
        "spaCy Arabic, diacritic handling, Arabic NER",
    ], MX, CT + Inches(0.4), col_w, Inches(4.5), size=Pt(13))

    # Right — timeline with practical details
    rx = MX + col_w + gap
    rt = add_text(slide, "Practical Timeline", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    headers = ["Step", "Effort", "How"]
    rows = [
        ["AV-HuBERT\nfine-tune", "1\u20132 weeks", "AVSpeech Arabic\nvids + AWS GPU"],
        ["Arabic K-means", "2\u20133 days", "Recluster on\nArabic features"],
        ["Arabic LLM\nswap", "1\u20132 days", "Config change +\ntokenizer"],
        ["Eval dataset", "1\u20132 weeks", "Native speaker\ntranscription"],
        ["Pipeline config\n& testing", "3\u20135 days", "End-to-end\nvalidation"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.45), col_w,
                    row_height=Inches(0.6),
                    col_widths=[Inches(1.6), Inches(1.3), Inches(2.6)],
                    text_size=Pt(12))

    # Total callout — positioned below table with clearance
    add_rect(slide, rx, CT + Inches(4.05), col_w, Inches(0.55),
             fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
             corner_radius=True)
    add_text(slide, "Total: ~3\u20135 weeks",
             rx + Inches(0.2), CT + Inches(4.1), col_w - Inches(0.4), Inches(0.4),
             size=Pt(18), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    # Bottom
    add_text(slide,
        "Pipeline code is language-agnostic \u2014 no code changes needed. "
        "AVSpeech Arabic videos + existing AWS GPU cover training. "
        "Main bottleneck: manual Arabic evaluation transcriptions.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Timeline summary callout
    timeline_box = add_rect(slide, MX, Inches(5.8), CW, Inches(0.55),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    timeline_txt = add_text(slide, "Total estimated timeline: 3–5 weeks",
             MX + Inches(0.3), Inches(5.85), CW - Inches(0.6), Inches(0.4),
             size=Pt(22), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Arabic replication roadmap with practical details. We have AVSpeech "
        "Arabic videos for training data and an AWS GPU instance for fine-tuning. "
        "Steps: fine-tune AV-HuBERT on Arabic (1-2 weeks), recluster K-means "
        "(2-3 days), swap to Arabic LLM (1-2 days), build eval dataset with "
        "native speakers (1-2 weeks), end-to-end testing (3-5 days). "
        "Total 3-5 weeks. Pipeline code is language-agnostic.",
        [[lt, lb], [rt, tbl], [timeline_box, timeline_txt]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 31 — SUMMARY
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 31 — SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def slide_31(prs):
    slide = new_slide(prs)
    add_title(slide, "Key Takeaways")
    add_accent_line(slide)

    takeaways = [
        ("1", "Rigorous assessment: 2.5\u00d7 WER gap on 1,497 segments. "
              "Novel IS metric reveals 40% properly captured, 51% with "
              "LLM salvage. 5 classified failure categories."),
        ("2", "Production system delivered: standalone container, 37 bugs "
              "fixed, 8-stage pipeline, 37 tests, 8 research reports."),
        ("3", "Data is the bottleneck: fine-tuning experiments (Exp A/B) "
              "proved 1,273 segments too small. Multiplicative scaling law: "
              "stronger LLM + more data compounds."),
        ("4", "Actionable roadmap to IS 3.5\u20134.0 (from 2.52): "
              "confidence scoring + N-best aggregation + LLM upgrade + "
              "data scaling + GER. Each phase targets a different failure "
              "category."),
    ]

    card_h = Inches(1.05)
    gap = Inches(0.12)
    circle_d = Inches(0.55)

    point_shapes = []
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
        add_text(slide, num, MX + Inches(0.2), cy,
                 circle_d, circle_d,
                 size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        # Text — left-aligned next to circle
        tb = add_text(slide, text,
                      MX + Inches(1.0), y + Inches(0.12),
                      CW - Inches(1.2), card_h - Inches(0.24),
                      size=Pt(15), color=WHITE)
        point_shapes.append(r)

    _finish(slide, 31,
        "Four takeaways. One: rigorous assessment with novel IS metric. "
        "Two: production system delivered. Three: data is the bottleneck "
        "(fine-tuning proved it). Four: clear roadmap from IS 2.52 to "
        "3.5-4.0, each phase targeting a different failure category.",
        [point_shapes], click_reveal=True)

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
             MX, CT, CW, Inches(0.4), size=Pt(14), color=WHITE)

    tbl1 = add_table(slide,
        ["Dimension", "Signals", "Variance", "Inter-signal r"],
        [["Word Accuracy", "WER, WWER, Phonetic", "60.0%", "> 0.79"],
         ["Meaning Preservation", "Semantic", "28.5%", "independent"],
         ["Output Sanity", "Length Ratio", "9.1%", "independent"]],
        MX, CT + Inches(0.5), CW * 0.55, text_size=Pt(11))

    # Cross-config stability
    add_text(slide, "Cross-Config Stability (16 configs)",
             SRL, CT + Inches(1.8), SRW, Inches(0.4), size=Pt(14), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["Signal", "Stability", "Std"],
        [["Semantic", "Stable", "0.017"],
         ["Phonetic", "Stable", "0.059"],
         ["NEA", "Stable", "0.023"],
         ["WER", "Volatile", "0.165"],
         ["Length", "Volatile", "0.142"]],
        SRL, CT + Inches(2.3), SRW, text_size=Pt(11),
        row_colors={3: {1: CORAL}, 4: {1: CORAL},
                    0: {1: GREEN}, 1: {1: GREEN}, 2: {1: GREEN}})

    # Heuristic validation
    add_text(slide, "Heuristic Validation (no runtime LLM)",
             SRL, CT + Inches(4.0), SRW, Inches(0.3),
             size=Pt(13), color=TEAL, bold=True)

    tbl3 = add_table(slide,
        ["Metric", "Value"],
        [["Mean r", "0.925 (std 0.015)"],
         ["Agreement", "88.6%"],
         ["Cohen's κ", "0.773"],
         ["Recall (IS≥3)", "97.6–100%"],
         ["Config range", "κ 0.62–0.86"]],
        SRL, CT + Inches(4.4), SRW * 0.7, text_size=Pt(10))

    _finish(slide, "A3",
        "IS components collapse into 3 dimensions: word accuracy (60%), "
        "meaning (28%), output sanity (9%). Cross-config: Semantic, Phonetic, "
        "NEA are stable; WER and Length Ratio are volatile. Heuristic: "
        "r=0.925, agreement 88.6%, kappa 0.773.")


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
         ["Metric capture (IS ≥ 3.0)", "39.9%"],
         ["Effective capture", "50.9%"],
         ["Uplift", "+11.0pp (+27.6% rel.)"]],
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
        "heuristic. Effective capture rises from 39.9% to 50.9%. "
        "6 recovery categories (overlap, not disjoint). "
        "58% have moderate WER (50-70%).")


def slide_a11b(prs):
    """A5: LLM Salvage — Curated Examples."""
    slide = new_slide(prs)
    add_title(slide, "A5: LLM Salvage — Curated Examples")
    add_accent_line(slide)

    add_text(slide, "One real example per recovery category — all IS < 3.0 "
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
        "All have IS < 3.0 but the heuristic identifies recoverable meaning. "
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
        "baseline. Wrong Topic is the largest (31.6%). Hallucination is the "
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

    _finish(slide, None,
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
         "40% properly captured vs WER's 11% \u2014 3.5\u00d7 more. Even 51% "
         "with LLM salvage. Most useful output has moderate WER (50\u201370%).",
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

    shapes = []
    for i, (num, title, detail, color) in enumerate(insights):
        y = start_y + i * (step_h + Inches(0.1))

        # Number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX, y + Inches(0.1), Inches(0.5), Inches(0.5))
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()
        add_text(slide, num, MX, y + Inches(0.1),
                 Inches(0.5), Inches(0.5),
                 size=Pt(18), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": WHITE, "bold": True})],
            [(detail, {"size": Pt(11), "color": LGRAY})],
        ], MX + Inches(0.7), y + Inches(0.02),
           CW - Inches(0.8), step_h - Inches(0.04))
        shapes.append(circle)

    _finish(slide, 0,
        "Five key research insights. The visual encoder is the bottleneck. "
        "WER dramatically overstates failure. Domain mismatch is the primary "
        "quality driver. Data scarcity limits fine-tuning. And gains are "
        "multiplicative — stronger LLM times more data times smart prompts.",
        [shapes])


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
        "Fine-tune experiments confirmed: small data = overfitting",
        "Scaling law (ICLR 2024): data × LLM quality = multiplicative gains",
        ("AVSpeech: 290K English videos available for curation", {"color": TEAL}),
        ("Data scarcity is a curation bottleneck, not a hard blocker",
         {"color": LGRAY, "italic": True}),
        ("Next step: curate 20K\u201350K diverse English segments", {"bold": True, "color": GREEN}),
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(13))

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
        rx, CT + Inches(0.5), col_w, text_size=Pt(11),
        col_widths=[Inches(0.9), Inches(1.0), Inches(1.0), Inches(0.9), Inches(1.0)],
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

    _finish(slide, 0,
        "Data scaling projections based on ICLR 2024 multiplicative scaling "
        "law. Current 1,273 segments is far below minimum. 20K segments with "
        "Llama 3.1 8B projects to IS 3.5-4.0 (55-65% captured). AVSpeech has "
        "290K videos available for training data curation.",
        [[lt, lb], [rt, tbl, r1]], click_reveal=True)


def slide_price_tag(prs):
    """Cost projections: GPU, data, timeline to reach IS targets."""
    slide = new_slide(prs)
    add_title(slide, "The Price Tag: Cost to Reach IS 3.5\u20134.0")
    add_accent_line(slide)

    add_text(slide,
        "AWS eu-west-1 (Ireland)  \u2022  p4d.24xlarge (8\u00d7A100) spot  \u2022  "
        "Paper\u2019s two-phase training curriculum",
        MX, CT, CW, Inches(0.35), size=Pt(12), color=LGRAY, italic=True)

    tbl_w = Inches(7.8)
    tbl = add_table(slide,
        ["Phase", "Data", "Train Cost", "Total Cost", "Timeline", "IS Target"],
        [["Current", "1.3K segs", "\u2014", "\u2014", "\u2014", "2.52"],
         ["Phase 1", "5K hrs", "~$3K", "~$8\u201312K", "2\u20134 wks", "~2.9\u20133.1"],
         ["Phase 2", "10K hrs", "~$6K", "~$15\u201320K", "4\u20136 wks", "~3.2\u20133.5"],
         ["Phase 3", "20K hrs", "~$13K", "~$30\u201340K", "6\u20138 wks", "~3.5\u20133.8"],
         ["Phase 4", "50K hrs", "~$32K", "~$70\u2013100K", "3\u20134 mo", "~3.8\u20134.2"]],
        MX, CT + Inches(0.5), tbl_w, text_size=Pt(11),
        col_widths=[Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.3),
                    Inches(1.1), Inches(1.2)],
        row_colors={3: {3: GREEN, 5: GREEN}})

    rx = MX + tbl_w + Inches(0.4)
    rw = CW - tbl_w - Inches(0.4)

    r1 = add_rect(slide, rx, CT + Inches(0.5), rw, Inches(2.8),
                   fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                   corner_radius=True)
    add_text(slide, "Sweet Spot", rx + Inches(0.2), CT + Inches(0.6),
             rw - Inches(0.4), Inches(0.35), size=Pt(16), color=GOLD, bold=True)
    add_text(slide, "Phase 3: IS ~3.7",
             rx + Inches(0.2), CT + Inches(1.0),
             rw - Inches(0.4), Inches(0.35), size=Pt(20), color=GREEN, bold=True)
    add_bullets(slide, [
        "20K hrs = ~7% of AVSpeech",
        "Total ~$35K incl. curation",
        "Follows paper\u2019s 2-phase\ncurriculum: freeze \u2192 unfreeze",
    ], rx + Inches(0.15), CT + Inches(1.5), rw - Inches(0.3), Inches(1.2),
        size=Pt(11))

    r2 = add_rect(slide, rx, CT + Inches(3.5), rw, Inches(1.3),
                   fill_color=NAVY2, border_color=TEAL, border_width=Pt(1),
                   corner_radius=True)
    add_text(slide, "LLM Backbone Upgrade",
             rx + Inches(0.2), CT + Inches(3.6),
             rw - Inches(0.4), Inches(0.3), size=Pt(13), color=TEAL, bold=True)
    add_text(slide,
        "Llama 3.1 8B or Qwen 2.5 7B\n+0.3\u20130.5 IS independently\nOnly config change needed",
        rx + Inches(0.2), CT + Inches(3.95),
        rw - Inches(0.4), Inches(0.7), size=Pt(11), color=LGRAY)

    add_text(slide,
        "Training cost: p4d spot $9.39/hr (eu-west-1).  "
        "Curation includes: download, RetinaFace, mouth crop, AV-HuBERT features, Whisper v3 labels.",
        MX, Inches(6.5), CW, Inches(0.35), size=Pt(10), color=MGRAY, italic=True)

    _finish(slide, 0,
        "Cost projections for scaling to IS 3.5-4.0. Based on p4d.24xlarge spot "
        "pricing in eu-west-1 at $9.39/hr. Phase 3 (20K hours, ~$35K) is the sweet spot. "
        "LLM backbone upgrade to Llama 3.1 8B or Qwen 2.5 7B adds +0.3-0.5 IS independently.",
        [[tbl], [r1, r2]], click_reveal=True)



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
        MX, CT + Inches(0.5), CW, text_size=Pt(11),
        row_height=Inches(0.4),
        col_widths=[Inches(2.8), Inches(1.1), Inches(0.9),
                    Inches(1.1), Inches(0.9), Inches(1.1), Inches(0.9)],
        row_colors={0: {2: GREEN}, 4: {6: CORAL}})

    # Key observations
    add_text(slide, "Key Observations:", MX, CT + Inches(3.0), CW, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_bullets(slide, [
        "IS Tier 5: 57% full Y \u2014 strong agreement on excellent output",
        "IS Tiers 2-3: majority P not N \u2014 judge sees partial value metrics miss",
        "IS Tier 1: 81% N \u2014 strong agreement on complete failure",
        ("Pearson r = 0.8495 between IS and judge verdict (coded Y=3, P=2, N=1)",
         {"color": TEAL}),
    ], MX, CT + Inches(3.4), CW, Inches(2.0), size=Pt(13))

    _finish(slide, "A8",
        "LLM Judge cross-tabulated with IS tiers. Strong agreement at the "
        "extremes: 57% Y for Tier 5, 81% N for Tier 1. The interesting "
        "middle: Tiers 2-3 get majority P verdicts — the LLM sees partial "
        "meaning preservation that strict metrics miss. Pearson r=0.8495.")


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
        rx, CT + Inches(3.5), col_w, Inches(0.6),
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
    """Future direction: per-segment confidence probabilities."""
    slide = new_slide(prs)
    add_title(slide, "Phase 1: Confidence Scoring")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what it is
    lt = add_text(slide, "What Is It?", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Assign a probability (0\u20131.0) to each decoded segment",
         {"bold": True}),
        "High confidence (> 0.8): trust the output as-is",
        "Medium (0.4\u20130.8): flag for human review",
        "Low (< 0.4): suppress or mark as unreliable",
        ("Goal: surface the 40% that already works", {"color": GREEN}),
    ], MX, CT + Inches(0.45), col_w, Inches(2.5), size=Pt(14))

    # How it works
    hwt = add_text(slide, "How It Works", MX, CT + Inches(3.2), col_w, Inches(0.35),
             size=Pt(16), color=TEAL, bold=True)
    hwb = add_bullets(slide, [
        "Combine decode-time signals: beam score, entropy, "
        "N-best agreement, length ratio",
        "Train a lightweight classifier on our 1,497 labeled segments",
        "Output: probability that IS \u2265 3.0 for each segment",
    ], MX, CT + Inches(3.65), col_w, Inches(2.0), size=Pt(13))

    # Right — impact
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Impact", rx, CT, rw, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    rb = add_bullets(slide, [
        ("Immediate value: 2\u20134 hours to implement", {"bold": True, "color": GREEN}),
        "Users see only high-confidence segments by default",
        "Reduces perceived error rate from 60% to ~20%",
        "No model changes needed \u2014 pure post-processing",
    ], rx, CT + Inches(0.45), rw, Inches(2.0), size=Pt(14))

    # Right — what we already have
    waht = add_text(slide, "What We Already Have", rx, CT + Inches(2.7), rw, Inches(0.35),
             size=Pt(16), color=CORAL, bold=True)
    headers = ["Signal", "Source"]
    rows = [
        ["Beam score", "Available from decode"],
        ["Token entropy", "Available from decode"],
        ["N-best agreement", "Requires beam > 1"],
        ["Length ratio", "Already in IS pipeline"],
        ["IS sub-scores", "Already computed"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(3.15), rw,
                    row_height=Inches(0.35), text_size=Pt(10),
                    col_widths=[Inches(2.4), Inches(3.0)])

    bottom = add_text(slide,
        "The fastest path to user value. No retraining, no new data, "
        "no infrastructure changes \u2014 just smarter filtering.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Phase 1 of the roadmap: confidence scoring. Assign a probability "
        "to each decoded segment indicating how likely it is to be correctly "
        "transcribed (IS >= 3.0). Uses decode-time signals like beam score, "
        "token entropy, N-best agreement, and length ratio. Can be trained on "
        "our existing 1,497 labeled segments. Implementation: 2-4 hours. "
        "Impact: users see only trusted output, perceived error rate drops "
        "from 60% to ~20%.",
        [[lt, lb], [rt, rb], [hwt, hwb, waht, tbl], [bottom]], click_reveal=True)


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

