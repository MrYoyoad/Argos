"""
Slide builders — Sections 0-2: Opening, Context, The Problem
"""

from pathlib import Path
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

from .config import (
    IMG, VID, POSTER_DIR, PLOTS, MATERIALS,
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
# WHAT WAS DONE (1/2 and 2/2)
# ═══════════════════════════════════════════════════════════════════════

def slide_what_was_done_1(prs):
    """What was done? (1/2) — four months of research and engineering."""
    slide = new_slide(prs)
    add_title(slide, "What was done? (1/2)")
    add_accent_line(slide)

    add_text(slide,
        "Four months of research and engineering on visual speech processing:",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    bullets = [
        "Started from a research paper with no working environment, "
        "no documentation, and no pipeline",
        "Standard metric (WER) was the basic metric \u2013 which is unsatisfactory "
        "to actually measure what is needed",
        "Built a complete end-to-end pipeline, including preprocessing "
        "(STT, face crop) and post-processing",
        "Created a working environment and migrated into a container on a "
        "standalone container including complete and professional UI handling",
        "Evaluated the model extensively, including designing a new metric "
        "that measures whether meaning is preserved",
        "Started fine-tuning the model, including environment setup "
        "and data preparation",
        "Created a clear future plan on how to improve performance "
        "+ generalize from English to Arabic",
    ]

    add_bullets(slide, bullets, MX, CT + Inches(0.45), CW, Inches(4.0),
                size=Pt(17), bullet_color=TEAL)

    _finish(slide, 0,
        "Overview slide 1/2. Four months of work: went from a research paper "
        "with no environment to a full pipeline, standalone container with UI, "
        "new evaluation metric (IS), fine-tuning experiments, and Arabic roadmap.")


def slide_what_was_done_2(prs):
    """What was done? (2/2) — key findings and outcomes."""
    slide = new_slide(prs)
    add_title(slide, "What was done? (2/2)")
    add_accent_line(slide)

    add_text(slide,
        "Four months of research and engineering on visual speech processing:",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    bullets = [
        "Proved the model performs well \u2014 about 65% of videos are "
        "useful by LLM judge assessment",
        "The IS metric shows high agreement with the LLM judge and "
        "can be computed on the standalone computer",
        "Semantic meaning, phonetic similarity, and named entity accuracy "
        "are the critical factors in understanding model performance",
        "Full failure analysis completed with suggested improvements",
        "Fully reproducible container build and model deployment "
        "between AWS and standalone computer",
        "Close to improving the base model through confidence scoring, "
        "output aggregation, and a stronger LLM",
        "Full plan to replicate the approach for an Arabic model "
        "in 2\u20133 months",
    ]

    add_bullets(slide, bullets, MX, CT + Inches(0.45), CW, Inches(4.0),
                size=Pt(17), bullet_color=TEAL)

    _finish(slide, 0,
        "Overview slide 2/2. Key findings: 65% useful output by LLM judge, "
        "IS metric validated, failure analysis complete, reproducible deployment, "
        "and clear path forward for model improvement and Arabic adaptation.")


# ═══════════════════════════════════════════════════════════════════════
# NEW SLIDES — EXECUTIVE SUMMARY, TOC, IS BUILD-UP
# ═══════════════════════════════════════════════════════════════════════

def slide_exec_summary(prs):
    """Executive summary — bottom-line-up-front overview."""
    slide = new_slide(prs)
    add_title(slide, "Executive Summary")
    add_accent_line(slide)

    add_text(slide, "Three months of research and engineering on visual speech processing:",
             MX, CT, CW, Inches(0.4), size=Pt(16), color=LGRAY, italic=True)

    items = [
        ("Evaluated a lip-reading AI on 1,497 real-world YouTube segments",
         {"bold": True}),
        "Standard metric (WER) reports 64.1% error \u2014 2.5\u00d7 worse than benchmark",
        ("Our new Intelligibility Score (IS) reveals 61.6% is actually useful \u2014 "
         "2.4\u00d7 what WER suggests", {"color": TEAL, "bold": True}),
        "Built a complete production system: 8-stage pipeline, standalone container",
        ("Clear roadmap to IS 3.5\u20134.0 (from 2.52) through data scaling + LLM upgrade",
         {"color": TEAL}),
        ("Arabic pipeline: replication roadmap established for Arabic lip-reading", {}),
        "Produced 8 comprehensive research reports",
    ]
    bul = add_bullets(slide, items, MX, CT + Inches(0.6), CW, Inches(4.0),
                      size=Pt(17), spacing=Pt(14))

    _finish(slide, 2,
        "Executive summary. Three months of work on visual speech processing. "
        "Key finding: WER dramatically overstates failure. Our Intelligibility "
        "Score shows 61.6% of output is useful (NIV Y+P), not the 25.5% WER suggests. "
        "Complete production system delivered. Clear roadmap to improve further.",
        [[bul]], click_reveal=True)



def slide_wer_lies(prs):
    """Side-by-side truth: WER says failure, IS says excellent."""
    slide = new_slide(prs)
    add_title(slide, "WER: The Metric That Lies")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)
    card_h = Inches(2.8)

    # Left card: WER verdict (CORAL)
    wer_shapes = []
    wer_shapes.append(add_rect(slide, MX, CT, col_w, card_h,
                       fill_color=NAVY2, border_color=CORAL, border_width=Pt(3),
                       corner_radius=True))
    wer_shapes.append(add_text(slide, "46.2%", MX + Inches(0.3), CT + Inches(0.2),
                                col_w - Inches(0.6), Inches(1.0),
                                size=Pt(64), color=CORAL, bold=True,
                                align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide, "Word Error Rate",
                                MX + Inches(0.3), CT + Inches(1.2),
                                col_w - Inches(0.6), Inches(0.3),
                                size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide, 'Verdict: "FAILING"',
                                MX + Inches(0.3), CT + Inches(1.6),
                                col_w - Inches(0.6), Inches(0.35),
                                size=Pt(18), color=CORAL, bold=True,
                                align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide,
        "6 insertions, 1 deletion\n= nearly half the words are \"wrong\"",
        MX + Inches(0.3), CT + Inches(2.1), col_w - Inches(0.6), Inches(0.6),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER))

    # Right card: IS verdict (GREEN)
    rx = MX + col_w + gap
    is_shapes = []
    is_shapes.append(add_rect(slide, rx, CT, col_w, card_h,
                      fill_color=NAVY2, border_color=GREEN, border_width=Pt(3),
                      corner_radius=True))
    is_shapes.append(add_text(slide, "4.03", rx + Inches(0.3), CT + Inches(0.2),
                               col_w - Inches(0.6), Inches(1.0),
                               size=Pt(64), color=GREEN, bold=True,
                               align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide, "Intelligibility Score (Excellent)",
                               rx + Inches(0.3), CT + Inches(1.2),
                               col_w - Inches(0.6), Inches(0.3),
                               size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide, 'Verdict: "EXCELLENT"',
                               rx + Inches(0.3), CT + Inches(1.6),
                               col_w - Inches(0.6), Inches(0.35),
                               size=Pt(18), color=GREEN, bold=True,
                               align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide,
        "Semantic similarity: 0.90\nMeaning fully preserved",
        rx + Inches(0.3), CT + Inches(2.1), col_w - Inches(0.6), Inches(0.6),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER))

    # Bottom: ref/hyp comparison + callout
    bottom_shapes = []
    by = CT + card_h + Inches(0.3)
    bottom_shapes.append(add_rich_text(slide, [
        [("\u25b6 Reference:  ", {"size": Pt(12), "color": LGRAY, "bold": True}),
         ("i want you to remember all these i want you to memorize them",
          {"size": Pt(12), "color": WHITE})],
        [("\u25b6 Prediction: ", {"size": Pt(12), "color": LGRAY, "bold": True}),
         ("i want you to remember all the things that i wanted you to memorize in my",
          {"size": Pt(12), "color": TEAL})],
    ], MX, by, CW, Inches(0.7), space_after=Pt(4)))
    cb_y = by + Inches(0.8)
    bottom_shapes.append(add_rect(slide, MX + Inches(1.5), cb_y,
                                   CW - Inches(3.0), Inches(0.6),
                                   fill_color=NAVY2, border_color=TEAL,
                                   border_width=Pt(2), corner_radius=True))
    bottom_shapes.append(add_text(slide,
        "WER counts word edits.  IS asks: did the viewer get the message?  Here \u2014 yes, completely.",
        MX + Inches(1.7), cb_y + Inches(0.1), CW - Inches(3.4), Inches(0.4),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER))

    _finish(slide, 0,
        "Side-by-side: same segment scores 46.2% WER (failure) but IS 4.03 "
        "(excellent). The prediction preserves the complete meaning.",
        [wer_shapes, is_shapes, bottom_shapes], click_reveal=True)


def slide_toc(prs):
    """Table of contents — 4-section overview."""
    slide = new_slide(prs)
    add_title(slide, "Presentation Overview")
    add_accent_line(slide)

    sections = [
        ("1. Context",
         "What is lip reading? \u2022 How does the system work? \u2022 What's the benchmark?",
         TEAL),
        ("2. Research Findings",
         "Real-world evaluation \u2022 Intelligibility Score metric \u2022 Failure analysis "
         "\u2022 Tuning experiments",
         TEAL),
        ("3. Engineering",
         "8-stage pipeline \u2022 Modular refactoring \u2022 Standalone container "
         "\u2022 Evaluation infrastructure",
         TEAL),
        ("4. Future Directions",
         "Improvement roadmap \u2022 Data scaling \u2022 LLM upgrade \u2022 "
         "Arabic pipeline \u2022 Target: IS 3.5\u20134.0",
         TEAL),
    ]
    card_groups = []
    y = CT + Inches(0.1)
    for sec_title, desc, color in sections:
        r = add_rect(slide, MX, y, CW, Inches(1.05), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, sec_title, MX + Inches(0.3), y + Inches(0.1),
                 CW - Inches(0.6), Inches(0.4),
                 size=Pt(22), color=WHITE, bold=True)
        t2 = add_text(slide, desc, MX + Inches(0.3), y + Inches(0.55),
                 CW - Inches(0.6), Inches(0.4),
                 size=Pt(13), color=LGRAY)
        card_groups.append([r, t1, t2])
        y += Inches(1.25)

    _finish(slide, 3,
        "Four sections. Context sets the stage — what is lip reading, "
        "how the system works. Research findings are the core: our novel "
        "evaluation framework and what we learned. Engineering covers the "
        "production system. Future directions lays out the improvement roadmap.",
        card_groups, click_reveal=True)


def slide_is_foreshadow(prs):
    """Brief bridge — WER falls short, we need something better."""
    slide = new_slide(prs)
    add_title(slide, "We Need a Better Metric")
    add_accent_line(slide)

    bul = add_bullets(slide, [
        "WER counts word edits — but treats every error as equally bad",
        "It can't tell if the viewer understood the message or not",
        '"Admiral McRae" \u2192 "animal migration" = same WER cost as "the" \u2192 "a"',
        ("We need a metric that asks: did the meaning survive?",
         {"bold": True, "color": TEAL}),
    ], MX, CT + Inches(0.2), CW, Inches(3.5), size=Pt(17))

    add_text(slide,
        "Next: our answer \u2014 the Intelligibility Score.",
        MX, Inches(5.3), CW, Inches(0.5),
        size=Pt(16), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Bridge slide. WER treats all errors as equal — a function word swap "
        "costs the same as destroying a named entity. We need a metric that "
        "captures whether the viewer actually understood the output.",
        [[bul]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════

def slide_01(prs):
    slide = new_slide(prs)

    # Logo top-right
    logo = add_image(slide, "logo", SL_W - MX - Inches(0.9),
                     Inches(0.3), height=Inches(0.9))

    # Title
    t1 = add_text(slide, "Argos VSP", MX, Inches(2.0), CW, Inches(1.0),
                  size=Pt(48), color=WHITE, bold=True, align=PP_ALIGN.LEFT)
    t2 = add_text(slide, "Research Findings and Production Roadmap",
                  MX, Inches(3.0), CW, Inches(0.7),
                  size=Pt(28), color=TEAL, bold=False, align=PP_ALIGN.LEFT)
    t3 = add_text(slide, "Visual Speech Processing — Project Review",
                  MX, Inches(3.8), CW, Inches(0.5),
                  size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.LEFT)

    # Accent line
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  MX, Inches(4.5), Inches(3), Pt(2))
    shp.fill.solid()
    shp.fill.fore_color.rgb = TEAL
    shp.line.fill.background()

    # Date & author
    add_text(slide, "February 2026", MX, Inches(5.2), Inches(4), Inches(0.4),
             size=Pt(16), color=LGRAY)
    add_text(slide, "Yoad Oxman  •  The Orchard", MX, Inches(5.6),
             Inches(5), Inches(0.4), size=Pt(14), color=MGRAY)

    add_slide_num(slide, 1)
    add_fade_transition(slide)
    add_animations(slide, [[t1], [t2, t3]])
    set_notes(slide,
        "Welcome. This presentation covers 3 months of research and engineering "
        "on a visual speech processing system — reading lips from video, no audio. "
        "We'll cover what we found, what we built, and where we go next.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 2 — WHAT IS VSP? (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 2 — WHAT IS VSP? (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_02(prs):
    slide = new_slide(prs)
    add_title(slide, "What is Visual Speech Processing?")
    add_accent_line(slide)

    # Embedded video — click to play directly in PowerPoint
    vid_w = Inches(8.5)
    vid_h = Inches(4.8)
    vid_x = (SL_W - vid_w) // 2
    add_video(slide, "perfect", vid_x, Inches(1.8), vid_w, vid_h)

    # Subtitle
    add_text(slide,
        "A system that reads lips from video \u2014 no audio needed.",
        MX + Inches(0.08), Inches(1.3), CW, Inches(0.4),
        size=Pt(16), color=LGRAY, italic=True)

    # Bottom text — expert lip reader comparison
    add_text(slide,
        "System + human reader outperforms expert lip readers: "
        "55\u201370% vs 45\u201352% word accuracy, with near-zero hallucination risk",
        MX + Inches(0.08), Inches(6.78), CW, Inches(0.6),
        size=Pt(14), color=WHITE)

    _finish(slide, 2,
        "PLAY VIDEO: IEa7qEkMvfQ_3__c5447488_with_hyp.mp4 — 33 words about "
        "health insurance, WER 0%. Play the video first, then explain: this is "
        "the best case. The system perfectly reads 33 consecutive words from lip "
        "movement alone. Now let's see how it works.\n\n"
        "AFTER VIDEO: System + human reader outperforms expert lip readers. "
        "Expert lip readers achieve ~45-52% word accuracy on unconstrained speech "
        "(Auer & Bernstein 2007). Model + context-aware human: estimated 55-70% "
        "word accuracy, 75-85% meaning capture. Key insight: the model provides "
        "candidate text (the hardest part of lip reading). The human's job becomes "
        "verification, not generation — dramatically easier. Hallucination risk "
        "drops from 20.5% to <5% with human filtering.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 3 — MODEL ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 3 — MODEL ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_03(prs):
    slide = new_slide(prs)
    add_title(slide, "How It Works: Three Components")
    add_accent_line(slide)

    # Model architecture diagram (AV-HuBERT → Projection → LLaMA-2-7B flow)
    img = add_image(slide, "model_arch", MX, CT, width=CW, height=Inches(3.6))

    # Three component blocks
    bw = Inches(3.5)
    bh = Inches(0.7)
    by = Inches(5.4)
    gap = Inches(0.4)
    total = 3 * bw + 2 * gap
    bx = (SL_W - total) / 2

    labels = [
        ("AV-HuBERT", "Visual Encoder, frozen, 1024-dim", TEAL),
        ("Linear Projection", "1024 → 4096", LGRAY),
        ("LLaMA-2-7B", "4-bit QLoRA, r=16", CORAL),
    ]
    block_groups = []
    arrows = []
    for i, (name, desc, border) in enumerate(labels):
        x = bx + i * (bw + gap)
        r = add_rect(slide, x, by, bw, bh, fill_color=NAVY2, border_color=border,
                     border_width=Pt(2), corner_radius=True)
        tb = add_text(slide, f"{name}\n{desc}", x + Inches(0.1), by + Inches(0.05),
                      bw - Inches(0.2), bh - Inches(0.1),
                      size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)
        block_groups.append([r, tb])

    # Arrow indicators between blocks
    for i in range(2):
        ax = bx + (i + 1) * bw + i * gap + Inches(0.05)
        ar = add_text(slide, "→", ax, by + Inches(0.1), gap - Inches(0.1), Inches(0.5),
                 size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER)
        arrows.append(ar)

    # Bottom note
    add_text(slide,
             "Only 12.6M trainable params (0.19%). LLM is architecture-compatible — "
             "Llama 3.1 8B is a drop-in replacement (same 4096 hidden size).",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True)

    _finish(slide, 3,
        "Three components. Visual encoder (AV-HuBERT) is frozen — pre-trained "
        "on LRS3 lip-reading data. It outputs 1024-dim features per frame. A "
        "linear projection maps to 4096-dim (LLM input space). Then LLaMA-2-7B "
        "generates text. Key: only the LoRA adapters and projection layer are "
        "trained — 12.6M of 7B parameters. The LLM is upgradeable: Llama 3.1 "
        "8B has the same hidden dimension (requires adapter retraining).",
        [[img], block_groups[0] + [arrows[0]] + block_groups[1] + [arrows[1]] + block_groups[2]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════

def slide_04(prs):
    slide = build_split(prs, 4, "The Benchmark: Paper vs Reality", "P2_paper",
        big_num="25.4%", num_color=TEAL,
        num_label="WER on LRS3 (TED Talks)",
        bullets=[
            ("LRS3 benchmark: curated TED talks, ideal conditions", {"bold": True}),
            ("Our dataset: 1,497 real YouTube segments \u2014 nothing is controlled",
             {"color": CORAL, "bold": True}),
            ("Result: 64.1% WER \u2014 2.5\u00d7 worse",
             {"color": CORAL, "bold": True}),
            ("WER is the wrong metric \u2013 our new IS is the right one "
             "(or LLM as a judge)", {}),
        ],
        bottom_text="Different dataset, fundamentally harder problem.",
        notes="The paper reports 25.4% WER on LRS3 \u2014 a curated TED talks dataset "
              "with ideal conditions. Our 1,497 YouTube segments are fundamentally "
              "harder: diverse speakers, topics, lighting, angles. Result: 64.1% "
              "WER, 2.5x worse. The dataset is different, and that explains the gap.\n\n"
              "Note: Our best LRS3 reproduction achieved 32% WER \u2014 gap likely "
              "due to pretrain/test split differences.")
    # Visible note at bottom (user added this to FINAL)
    add_text(slide,
        "Note: Our best LRS3 reproduction achieved 32% WER \u2014 gap likely "
        "due to pretrain/test split differences.",
        MX, Inches(6.85), CW, Inches(0.3),
        size=Pt(10), color=MGRAY, italic=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 5 — THE REALITY GAP
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 5 — THE REALITY GAP
# ═══════════════════════════════════════════════════════════════════════

def slide_05(prs):
    build_split(prs, 5, "The Reality Gap", "P1_quality",
        big_num="64.1%", num_color=CORAL,
        num_label="Mean WER across 1,497 real-world segments",
        bullets=[
            ("25.5% Useful by WER (<30%)", {"bullet": "\u25cf", "bullet_color": GREEN}),
            ("17.4% Marginal (30-50%)", {"bullet": "\u25cf", "bullet_color": YELLOW}),
            ("17.8% Poor (50-75%)", {"bullet": "\u25cf", "bullet_color": ORANGE}),
            ("32.8% Unusable (75-100%)", {"bullet": "\u25cf", "bullet_color": RED}),
            ("20.6% Hallucinated (>100%)", {"bullet": "\u25cf", "bullet_color": DRED}),
        ],
        bottom_text="But WER overstates failure — see next slide.",
        notes="1,497 diverse YouTube segments. 64.1% mean WER — 2.5x worse than "
              "the paper's 25.4%. Only 25.5% useful by WER (\u226434%). And 20.6% "
              "are hallucinations — fluent text that's completely fabricated. This "
              "is the most dangerous failure mode. But WER is misleading — it "
              "treats all errors equally.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 6 — WER IS BLIND
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 6 — WER IS BLIND
# ═══════════════════════════════════════════════════════════════════════

def slide_06(prs):
    slide = new_slide(prs)
    add_title(slide, 'Same WER, Different Effects')
    add_accent_line(slide)

    bw = Inches(5.5)
    bh = Inches(3.8)
    by = CT + Inches(0.1)
    gap = Inches(1.13)

    # Left box — harmless error
    r1 = add_rect(slide, MX, by, bw, bh, fill_color=NAVY2,
                  border_color=GREEN, border_width=Pt(2.5), corner_radius=True)
    add_text(slide, "WER: 1 substitution  •  Harmless",
             MX + Inches(0.3), by + Inches(0.2), bw - Inches(0.6), Inches(0.4),
             size=Pt(14), color=GREEN, bold=True)
    add_rich_text(slide, [
        [('Ref: "', {"size": Pt(15), "color": LGRAY}),
         ('the', {"size": Pt(15), "color": GREEN, "bold": True}),
         (' admiral gave the order"', {"size": Pt(15), "color": WHITE})],
        [('Hyp: "', {"size": Pt(15), "color": LGRAY}),
         ('a', {"size": Pt(15), "color": GREEN, "bold": True}),
         (' admiral gave the order"', {"size": Pt(15), "color": WHITE})],
    ], MX + Inches(0.3), by + Inches(0.8), bw - Inches(0.6), Inches(1.2),
       space_after=Pt(8))
    add_text(slide, '"the" → "a"\nFunction word swap — meaning fully preserved.\n'
                    'The viewer understood the message.',
             MX + Inches(0.3), by + Inches(2.2), bw - Inches(0.6), Inches(1.2),
             size=Pt(13), color=LGRAY)

    # Right box — destructive error
    rx = MX + bw + gap
    r2 = add_rect(slide, rx, by, bw, bh, fill_color=NAVY2,
                  border_color=RED, border_width=Pt(2.5), corner_radius=True)
    add_text(slide, "WER: 1 substitution  •  Destructive",
             rx + Inches(0.3), by + Inches(0.2), bw - Inches(0.6), Inches(0.4),
             size=Pt(14), color=RED, bold=True)
    add_rich_text(slide, [
        [('Ref: "', {"size": Pt(15), "color": LGRAY}),
         ('Admiral McRae', {"size": Pt(15), "color": RED, "bold": True}),
         (' gave the order"', {"size": Pt(15), "color": WHITE})],
        [('Hyp: "', {"size": Pt(15), "color": LGRAY}),
         ('animal migration', {"size": Pt(15), "color": RED, "bold": True}),
         (' gave the order"', {"size": Pt(15), "color": WHITE})],
    ], rx + Inches(0.3), by + Inches(0.8), bw - Inches(0.6), Inches(1.2),
       space_after=Pt(8))
    add_text(slide, '"Admiral McRae" → "animal migration"\n'
                    'Named entity destroyed — identity lost completely.\n'
                    'The viewer got the wrong person.',
             rx + Inches(0.3), by + Inches(2.2), bw - Inches(0.6), Inches(1.2),
             size=Pt(13), color=LGRAY)

    # Bottom callout
    add_rect(slide, MX + Inches(1.5), Inches(5.95), CW - Inches(3.0), Inches(0.7),
             fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
             corner_radius=True)
    add_text(slide,
             "WER counts both as 1 error. But one preserves meaning, the other "
             "destroys it.\nWe needed our own metric — the Intelligibility Score (IS).",
             MX + Inches(1.7), Inches(6.0), CW - Inches(3.4), Inches(0.6),
             size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 6,
        "The Admiral McRae example. Both cases have the same WER — 1 word "
        "substitution. But 'the' to 'a' is harmless, while 'Admiral McRae' to "
        "'animal migration' destroys the speaker's identity. WER treats them "
        "identically. This is why we built our own metric — the Intelligibility "
        "Score — which asks: did the viewer get the message?",
        [[r1], [r2]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 7 — THE INTELLIGIBILITY SCORE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# NEW SLIDES — DEEP DIVES, CONTEXT, ENGINEERING, APPENDIX
# ═══════════════════════════════════════════════════════════════════════

def slide_visemes(prs):
    """Fundamental viseme challenge — why lip reading is hard."""
    slide = new_slide(prs)
    add_title(slide, "The Invisible Problem: Visemes")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — The problem
    lt = add_text(slide, "The Invisible Problem", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("50\u201370% of English sounds are invisible on lips", {"bold": True}),
        "Multiple sounds produce identical mouth shapes (visemes)",
        "Context is the ONLY disambiguation signal",
    ], MX, CT + Inches(0.5), col_w, Inches(1.5), size=Pt(15))

    # Viseme table
    tbl1 = add_table(slide,
        ["Viseme Group", "Sounds"],
        [["Bilabial", "p, b, m"],
         ["Alveolar", "t, d, n, s, z, l"],
         ["Velar", "k, g, ng"],
         ["Labiodental", "f, v"]],
        MX, CT + Inches(2.3), col_w, text_size=Pt(12))

    # Right column — Visual proof + confusable pairs
    rx = MX + col_w + gap
    rt = add_text(slide, "Same Mouth Shape, Different Words", rx, CT, col_w,
                  Inches(0.4), size=Pt(18), color=TEAL, bold=True)

    # Lip-reading GIF — identical mouth shapes, different words
    poster_shapes = []
    gif_w = Inches(5.0)
    gif_h = Inches(1.5)  # constrain height to prevent overlap with table
    gif_path = MATERIALS / "mom-yelling.gif"
    if gif_path.exists():
        gif_x = rx + (col_w - gif_w) / 2  # Center in right column
        poster_shapes.append(slide.shapes.add_picture(
            str(gif_path), gif_x, CT + Inches(0.5), width=gif_w, height=gif_h))
    poster_shapes.append(add_text(slide,
        "Lip reading: identical mouth shapes can produce completely different words",
        rx, CT + Inches(2.1), col_w, Inches(0.3),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))

    tbl2 = add_table(slide,
        ["Word A", "Word B"],
        [["pat", "bat"],
         ["mom", "bomb"],
         ["admiral", "animal"],
         ["collar", "color"]],
        rx, CT + Inches(2.5), col_w, text_size=Pt(12))

    # Bottom
    add_text(slide,
        "Context is the ONLY disambiguation signal \u2014 this is why the LLM matters.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(14), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "50-70% of English sounds are invisible on lips. Multiple sounds produce "
        "identical mouth shapes called visemes. The poster frames show two "
        "different speakers — their mouth shapes look nearly identical despite "
        "saying completely different words. Context is the only disambiguation "
        "signal, which is why the LLM component is critical.",
        [[lt, lb, tbl1], poster_shapes + [rt, tbl2]], click_reveal=True)


def slide_data_flow(prs):
    """5-step pipeline data flow."""
    slide = new_slide(prs)
    add_title(slide, "How It Works: Data Flow")
    add_accent_line(slide)

    steps = [
        ("1", "Video Frames", "25 fps raw video input", TEAL),
        ("2", "Mouth Crop", "96\u00d796 pixel region around lips", TEAL),
        ("3", "Visual Features", "AV-HuBERT encoder \u2192 1024-dim vectors", TEAL),
        ("4", "Projection", "Linear layer: 1024 \u2192 4096-dim (LLM input space)", CORAL),
        ("5", "LLM Generates Text", "LLaMA-2-7B decodes features into words", CORAL),
    ]

    step_w = Inches(10.5)
    step_h = Inches(0.75)
    start_y = CT + Inches(0.1)
    start_x = MX + Inches(0.8)

    step_groups = []
    for i, (num, name, desc, color) in enumerate(steps):
        y = start_y + i * (step_h + Inches(0.15))
        r = add_rect(slide, start_x, y, step_w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)

        # Step number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, start_x - Inches(0.7), y + Inches(0.1),
            Inches(0.55), Inches(0.55))
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()
        num_txt = add_text(slide, num, start_x - Inches(0.7), y + Inches(0.1),
                 Inches(0.55), Inches(0.55),
                 size=Pt(20), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        rt = add_rich_text(slide, [
            [(name, {"size": Pt(16), "color": WHITE, "bold": True}),
             (f"  \u2014  {desc}", {"size": Pt(13), "color": LGRAY})],
        ], start_x + Inches(0.2), y + Inches(0.1),
           step_w - Inches(0.4), step_h - Inches(0.2))

        group = [r, circle, num_txt, rt]

        # Arrow between steps
        if i < len(steps) - 1:
            arrow = add_text(slide, "\u2193", start_x + step_w / 2 - Inches(0.2),
                     y + step_h - Inches(0.05), Inches(0.4), Inches(0.3),
                     size=Pt(16), color=TEAL, align=PP_ALIGN.CENTER)
            group.append(arrow)

        step_groups.append(group)

    add_text(slide,
        "Visual encoder is frozen (pre-trained on LRS3). Only projection + LoRA adapters are trained.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Five-step data flow. Raw video at 25fps is cropped to 96x96 mouth "
        "region. AV-HuBERT extracts 1024-dim visual features. Linear projection "
        "maps to 4096-dim LLM input space. LLaMA-2-7B generates text. The visual "
        "encoder is frozen — only the projection layer and LoRA adapters are trained.",
        step_groups)


def slide_eval_dataset(prs):
    """Our 1,497-segment evaluation dataset."""
    slide = new_slide(prs)
    add_title(slide, "Our Evaluation: 1,497 Real-World Segments")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — big number + bullets
    s1 = add_text(slide, "1,497", MX, CT, col_w, Inches(1.0),
                  size=Pt(64), color=TEAL, bold=True)
    s2 = add_text(slide, "segments from diverse YouTube videos",
                  MX, CT + Inches(1.0), col_w, Inches(0.4),
                  size=Pt(16), color=WHITE)
    s3 = add_bullets(slide, [
        "Uncontrolled lighting, angles, occlusions",
        "Multiple speakers and accents",
        "Diverse topics: business to DIY to gaming",
        ("Not a curated benchmark \u2014 real-world difficulty", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.5), size=Pt(14))

    # Right — topic categories table
    rx = MX + col_w + gap
    add_text(slide, "Topic Distribution", rx, CT, col_w, Inches(0.4),
             size=Pt(17), color=CORAL, bold=True)

    tbl = add_table(slide,
        ["Topic", "Segments", "Quality*"],
        [["Business/Finance", "214", "3.08"],
         ["Education/Lecture", "312", "2.63"],
         ["Entertainment", "198", "2.51"],
         ["News/Politics", "267", "2.48"],
         ["Tech/Science", "186", "2.43"],
         ["Sports/Health", "153", "2.38"],
         ["DIY/Home", "167", "2.13"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {2: GREEN}, 6: {2: CORAL}})

    # Footnote explaining Quality* column
    add_text(slide,
        "*Quality = our composite metric (0\u20135 scale), introduced in the next section.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(11), color=MGRAY, italic=True)

    _finish(slide, 0,
        "1,497 segments from diverse YouTube videos. Not a curated benchmark. "
        "Multiple topics, speakers, accents, lighting conditions. Business and "
        "Finance has the highest quality score (3.08) because it's closest to the "
        "TED talk training data. DIY/Home is worst (2.13) due to inherently visual "
        "content. The Quality column is our Intelligibility Score, introduced later.",
        [[s1, s2, s3], [tbl]], click_reveal=True)


def slide_wer_explained(prs):
    """WER formula and its limitations."""
    slide = new_slide(prs)
    add_title(slide, "Word Error Rate: What It Measures (and Misses)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — formula + example
    lt = add_text(slide, "The Formula", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    add_text(slide, "WER = (S + D + I) / N",
             MX + Inches(0.3), CT + Inches(0.55), col_w - Inches(0.6), Inches(0.5),
             size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "S = substitutions (wrong word)",
        "D = deletions (missing word)",
        "I = insertions (extra word)",
        "N = total words in reference",
    ], MX, CT + Inches(1.2), col_w, Inches(1.5), size=Pt(14))

    add_text(slide, "Example:", MX, CT + Inches(2.8), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_text(slide, 'Ref: "the admiral gave orders"\n'
                    'Hyp: "the animal gave water"\n'
                    'WER = 2/4 = 50% (2 substitutions)',
             MX + Inches(0.2), CT + Inches(3.2), col_w - Inches(0.4), Inches(1.2),
             size=Pt(13), color=WHITE)

    # Right — what it captures vs misses
    rx = MX + col_w + gap
    rt = add_text(slide, "What WER Captures", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=GREEN, bold=True)
    rb1 = add_bullets(slide, [
        "Exact word-level accuracy",
        "Simple, widely understood",
        "Standard in ASR research",
    ], rx, CT + Inches(0.5), col_w, Inches(1.2), size=Pt(14), bullet_color=GREEN)

    rm = add_text(slide, "What WER Misses", rx, CT + Inches(2.0), col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    rb2 = add_bullets(slide, [
        ("All errors weighted equally", {"color": CORAL}),
        ('"admiral"\u2192"animal" = "the"\u2192"a"', {"color": CORAL}),
        "No meaning preservation signal",
        "No phonetic similarity credit",
        ("Can exceed 100% (insertions)", {"color": CORAL}),
    ], rx, CT + Inches(2.5), col_w, Inches(2.5), size=Pt(14), bullet_color=CORAL)

    _finish(slide, 0,
        "WER formula: substitutions plus deletions plus insertions divided by "
        "reference word count. Simple and standard, but treats all errors equally. "
        "Admiral-to-animal gets the same penalty as the-to-a. No credit for "
        "meaning preservation or phonetic similarity. Can exceed 100% when the "
        "model generates extra words (insertions).",
        [[lt], [rt], [rb1], [rm], [rb2]], click_reveal=True)


