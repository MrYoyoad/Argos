"""
Slide builders — Section 6 + Salvage + Demos
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
    BLUE, PURPLE,
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
# SLIDE 12 — 13 TUNING EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_12(prs):
    slide = new_slide(prs)
    add_title(slide, "Best Config vs Baseline: The Trade-off")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — What we found
    lt = add_text(slide, "What We Found", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Config J (lenpen=1.0, temp=0.5) was best overall", {"bold": True}),
        "Most configs cluster in a narrow IS range (2.45\u20132.60)",
        "Extreme parameters cause catastrophic failures",
        ("Lenpen=\u22120.5: 45% empty outputs", {"color": CORAL}),
        ("Lenpen=2.0: mean WER 540% (massive hallucination)", {"color": CORAL}),
    ], MX, CT + Inches(0.45), col_w, Inches(3.0))

    # Right column — Best Config (J)
    rx = MX + col_w + gap
    rt = add_text(slide, "Best Config (J) — 1,497 segments",
                  rx, CT, col_w, Inches(0.35),
                  size=Pt(17), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "IS: 2.60 vs 2.53 baseline (+0.07)",
        ("Captured: 622 vs 601 (+21 segments)", {"color": GREEN}),
        ("Empties: 0 vs 70 (eliminated)", {"color": GREEN}),
        ("Hallucinations: 348 vs 307 (+41 more)", {"color": CORAL}),
    ], rx, CT + Inches(0.45), col_w, Inches(2.0))

    # Right image — before/after tuning comparison
    img = add_image(slide, "tuning_ba", rx, CT + Inches(2.6), width=col_w,
                    height=Inches(3.0))

    _finish(slide, 12,
        "13 systematic experiments across beam size, length penalty, "
        "temperature, and sampling. Config J achieved the best IS. Key "
        "trade-off: eliminated all 70 empty outputs but added 41 "
        "hallucinations. Net IS gain: only +0.08.",
        [[lt, lb], [rt, rb, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

def slide_13(prs):
    build_split(prs, 13, "Tuning Is Mitigation, Not a Cure", "P4_lenpen",
        bullets=[
            ("Config J: eliminates empties but increases hallucinations by 13%",
             {"color": CORAL}),
            "Net IS gain: only +0.08 across 1,497 segments",
            "Cross-config proof: per-segment rankings identical (r > 0.92)",
            ('"Hard" and "easy" segments stay the same — '
             "bottleneck is the visual encoder", {"bold": True}),
            ("Data is the real constraint: 1,273 training segments is "
             "below the ~1K LoRA minimum", {"color": CORAL}),
            ("Three levers remain: scale data (20K+), swap LLM "
             "(Llama 3.1 8B), smart prompts", {"color": TEAL}),
        ],
        notes="Tuning is mitigation, not a cure. Config J's fundamental "
              "trade-off: silent failures (empties) vs noisy failures "
              "(hallucinations). Cross-config analysis proves: per-segment "
              "IS rankings are nearly identical across all 16 configs "
              "(r > 0.92). The bottleneck is the visual encoder AND data "
              "scarcity — 1,273 training segments is below the ~1K minimum "
              "for LoRA generalization. Three levers: (1) scale data to "
              "20K-50K, (2) swap LLM to Llama 3.1 8B, (3) smart prompts.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE — TUNING SUMMARY (condensed)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14 — CURATED EXAMPLES (TABLE)
# ═══════════════════════════════════════════════════════════════════════

def slide_14(prs):
    slide = new_slide(prs)
    add_title(slide, "Representative Examples")
    add_accent_line(slide)

    headers = ["Category", "Reference", "Hypothesis", "WER", "IS"]
    rows = [
        ["Perfect", "health insurance company they pay...", "[exact match]", "0%", "5.0"],
        ["WER Misleads", "work with the team in a more", "work with a team and more", "29%", "4.3"],
        ["Near-Miss", "1 billion cfus of probiotics", "1 million cfus of permafrost", "58%", "2.7"],
        ["Hallucinated", "carry strap", "holocaust denier", "100%", "0.8"],
    ]
    # Color IS column by value
    row_colors = {
        0: {4: GREEN},
        1: {4: GREEN},
        2: {4: YELLOW},
        3: {4: RED},
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT, CW, row_height=Inches(0.55),
                    col_widths=[Inches(1.5), Inches(3.8), Inches(3.8),
                                Inches(1.0), Inches(1.0)],
                    row_colors=row_colors)

    _finish(slide, 14,
        "Four examples spanning the quality range. Row 1: perfect lip-reading. "
        "Row 2: WER says 29% error but the meaning is fully preserved — IS 4.3. "
        "Row 3: near-miss — structure intact but key terms phonetically garbled "
        "(probiotics→permafrost). Row 4: complete hallucination — 'carry strap' "
        "becomes 'holocaust denier.' This is why WER alone is insufficient.",
        [[tbl]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_15(prs):
    """Demo slide.

    BLOCKER fix (May 2026): pre-fix audit found orphan animation refs to
    spids ['4','7','10'] (pptx_visual_audit.json, slide 48). Cause: a
    prior version called add_animations directly with stale shape ids.
    Fixed by collecting actual shape handles into per-video click-reveal
    groups passed to _finish - the animation tree now references only
    the shape IDs that exist on this slide. Body font also bumped from
    11pt to 12pt to clear the readability floor.
    """
    slide = new_slide(prs)
    add_title(slide, "Demo: OK \u2192 Almost There \u2192 Hallucination")
    add_accent_line(slide)

    # Three embedded videos side by side - click each to play
    # VID dict mapping (confirmed correct):
    #   "smartphone"   -> ktMebjnZiSE_3  (consumers want bigger smartphone, IS 4.1)
    #   "street_photo" -> 2HddWQse8Mw_0  (street photography topic right, names lost, IS 2.9)
    #   "halluc"       -> 00MUdHQ7GGY_8  (carry strap -> holocaust denier)
    vid_w = Inches(3.6)
    vid_h = Inches(2.7)
    gap = Inches(0.4)
    total = 3 * vid_w + 2 * gap
    start_x = (SL_W - total) / 2
    vid_y = CT + Inches(0.1)

    vids = [
        ("smartphone", '"consumers want a bigger smartphone"\n\u2192 "consumers will not upgrade their smartphone"\nMeaning close, key verb flipped (IS 4.1)', "WER 28%  IS 4.1", TEAL),
        ("street_photo", '"james and will talk about street photography"\n\u2192 "i\'m here to talk about street photography"\nTopic right, speaker names lost (IS 2.9)', "WER 56%  IS 2.9", CORAL),
        ("halluc", '"carry strap" \u2192 "holocaust denier"', "WER 100%  IS 0.8", RED),
    ]

    # audit:pptx_visual_audit_after_amosi.md slide 63 BLOCKER -
    # animation referenced movie shape ids ['7','10'] which are wrapped in
    # <mc:AlternateContent>. python-pptx's slide.shapes iterator and the
    # audit's iter_shapes_recursive both skip AlternateContent, so the
    # movies look "non-existent" even though they render fine. Fix: drop
    # video shapes from anim_groups; only animate the captions. Videos
    # still render (they're not animated, so they appear immediately).
    anim_groups = []
    for i, (key, desc, wer, color) in enumerate(vids):
        x = start_x + i * (vid_w + gap)
        add_video(slide, key, x, vid_y, vid_w, vid_h)
        wer_t = add_text(slide, wer, x, vid_y + vid_h + Inches(0.05), vid_w,
                 Inches(0.3), size=Pt(14), color=color, bold=True,
                 align=PP_ALIGN.CENTER)
        # 12pt floor (was 11pt - blocked by readability audit).
        desc_t = add_text(slide, desc, x, vid_y + vid_h + Inches(0.35), vid_w,
                 Inches(0.7), size=Pt(12), color=LGRAY,
                 align=PP_ALIGN.CENTER)
        anim_groups.append([wer_t, desc_t])

    foot = add_text(slide, "Click each video to play.",
             MX, Inches(6.6), CW, Inches(0.3),
             size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)
    anim_groups.append([foot])

    _finish(slide, 15,
        "Three demos side by side. Left: 'consumers want a bigger smartphone' "
        "becomes 'consumers will not upgrade their smartphone' (IS 4.1 - "
        "meaning is close but the key verb is flipped: 'want' to 'will not'. "
        "This is what good output looks like - mostly right, small errors). "
        "Center: 'james and will talk about street photography' becomes "
        "'i'm here to talk about street photography' (IS 2.9 - "
        "the topic is captured perfectly but speaker names are lost. "
        "This is the near-miss zone). "
        "Right: 'carry strap' becomes 'holocaust denier' (hallucination, "
        "IS 0.8 - fluent but completely fabricated). Click each video to play. "
        "BLOCKER fix May 2026: animation references previously orphaned spids "
        "[4,7,10]; rebuilt to pass real shape handles. "
        "Source: docs/evaluation/pptx_visual_audit.json (slide 48).",
        anim_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — IS VALIDATION: CLAUDE-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — IS VALIDATION: CLAUDE-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════════

def slide_16(prs):
    slide = new_slide(prs)
    add_title(slide, "IS Validation: Design-Time Distilled Evaluation")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: How IS works
    lt = add_text(slide, "How the IS Was Built", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Full evaluation framework designed at development time",
        "Selected 6 signals: Semantic (25%), Phonetic (15%), "
        "inv. WER (15%), inv. WWER (15%), NEA F1 (15%), Length (15%)",
        "Defined 5 tiers, 5 failure categories, 7 success patterns",
        ("Distilled into deterministic formulas — no LLM per sample",
         {"bold": True}),
        "Result: reproducible, free, decomposable scoring",
    ], MX, CT + Inches(0.45), col_w, Inches(3.0), size=Pt(13))

    # Right: Correlation analysis + validation
    rx = MX + col_w + gap
    rt = add_text(slide, "PCA: 2 Dimensions of Quality", rx, CT, col_w,
                  Inches(0.35), size=Pt(17), color=CORAL, bold=True)

    # Two PCA dimensions (actual PCA results)
    dims = [
        ("PC1: Signal Quality", "All 5 content signals load equally (0.43\u20130.47)", "68.4%", TEAL),
        ("PC2: Output Length", "Length Ratio dominates (loading 0.91)", "19.5%", LGRAY),
    ]
    dim_y = CT + Inches(0.5)
    for i, (name, signals, pct, color) in enumerate(dims):
        y = dim_y + i * Inches(0.75)
        add_text(slide, name, rx, y, col_w, Inches(0.3),
                 size=Pt(14), color=color, bold=True)
        add_text(slide, f"{signals} \u2014 {pct} of variance",
                 rx + Inches(0.15), y + Inches(0.3), col_w - Inches(0.15),
                 Inches(0.3), size=Pt(11), color=LGRAY)
    add_text(slide, "Together: 87.9% of total variance (Kaiser criterion)",
             rx + Inches(0.15), dim_y + 2 * Inches(0.75) + Inches(0.1),
             col_w - Inches(0.15), Inches(0.3), size=Pt(11), color=LGRAY)

    # Cross-config validation stats
    add_text(slide, "Cross-Config Validation (16 configs)",
             rx, CT + Inches(2.9), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["LLM heuristic vs IS", "r = 0.925"],
        ["Agreement (IS ≥ 2.00)", "κ = 0.818"],
        ["Recall (IS ≥ 2.00)", "97.6–100%"],
        ["Cohen's κ", "0.773"],
        ["Segment ranking stability", "r > 0.92"],
    ]
    add_table(slide, headers, rows, rx, CT + Inches(3.3), col_w,
              row_height=Inches(0.32),
              col_widths=[Inches(3.0), Inches(2.5)],
              text_size=Pt(11))

    _finish(slide, 16,
        "How the IS was built: the entire framework was designed at development "
        "time — rubric, 6 signals with weights, tier boundaries, failure mode "
        "taxonomy, success patterns. These were then encoded into deterministic "
        "formulas. No LLM is called per sample at runtime.\n\n"
        "PCA RESULTS (Kaiser criterion, 2 PCs retained):\n"
        "PC1 (68.4%): Signal Quality — all 5 content signals load equally "
        "(0.43-0.47). Semantic is NOT independent of word accuracy.\n"
        "PC2 (19.5%): Output Length — Length Ratio dominates (0.91). "
        "Independent of content quality.\n"
        "Together: 87.9% of variance. The visual encoder drives PC1.\n\n"
        "KEY FINDINGS:\n"
        "1. Phonetic Sim is the strongest single predictor (r=0.943) despite "
        "15% weight — most direct measure of visual encoder quality.\n"
        "2. WER is UNRELIABLE across configs — correlation with IS swings from "
        "-0.95 to -0.45 depending on length penalty. This is why IS was created.\n\n"
        "Cross-config validation: r=0.925, recall 97.6-100% across 16 configs. "
        "IS vs Opus judge: κ=0.818 at Y+P (IS≥2.00), κ=0.690 at Y (IS≥3.80).")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_25(prs):
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate for LLM Judgment")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(4.6), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric — in CORAL for this variant
    add_text(slide, "IS says 61.6%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments pass (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(16), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge — the validation
    add_text(slide, "LLM Judge says 64.9%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(16), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets below
    bul = add_bullets(slide, [
        ("IS conservatively undercounts \u2014 the real quality is higher "
         "than 61.6% suggests", {"bold": True, "color": WHITE}),
        "LLM-as-a-Judge (blind, 1,497 pairs) confirms: nearly 2 in 3 "
         "segments carry useful meaning",
        ("The gap (61.6% \u2192 64.9%) = segments with partial value "
         "that strict metrics penalize", {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(1.8), size=Pt(14))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "An independent LLM judge confirms the true useful rate is 3pp higher.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "IS provides a conservative lower bound for transcription quality. "
        "IS says 61.6% of segments are useful (IS >= 2.00). But an independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 64.9% deliver useful output. The 25pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling \u2014 the real quality of the "
        "system is higher than our metric reports.",
        [[r1], [bul]], click_reveal=True)


def slide_25b(prs):
    """LLM Salvage: 6 recovery categories explained."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: 6 Recovery Categories")
    add_accent_line(slide)

    add_text(slide,
        "165 segments that metrics call \u201cfailed\u201d (IS < 2.0) actually deliver "
        "useful meaning. They fall into 6 overlapping categories:",
        MX, CT, CW, Inches(0.45), size=Pt(14), color=LGRAY, italic=True)

    categories = [
        ("Phonetic Bridge", "93", TEAL,
         "Words sound right but are spelled differently \u2014 a viewer who knows "
         "the topic fills in the gaps (phonetic sim \u2265 0.6)"),
        ("Structure Match", "74", TEAL,
         "Same grammatical structure as reference \u2014 word order intact, "
         "subject-verb-object pattern preserved"),
        ("Semantic Preservation", "57", GREEN,
         "Core meaning conveyed despite high WER \u2014 like a paraphrase "
         "(semantic sim \u2265 0.5)"),
        ("Hidden Gems", "54", GREEN,
         "Decision tree assigns \u2265 80% recovery probability despite metrics "
         "all flagging failure"),
        ("Entity-Preserved", "44", YELLOW,
         "Critical names and numbers correct even though surrounding words "
         "are wrong (NEA F1 \u2265 50%)"),
        ("WER Over-Punishment", "27", YELLOW,
         "WER inflated by function word errors (\u2018the\u2019 \u2192 \u2018a\u2019) "
         "that don\u2019t affect meaning (WER\u2212WWER \u2265 10pp)"),
    ]

    py = CT + Inches(0.55)
    card_groups = []
    for name, count, color, desc in categories:
        r = add_rect(slide, MX, py, CW, Inches(0.7), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name} ({count})",
                 MX + Inches(0.2), py + Inches(0.05), Inches(3.0), Inches(0.3),
                 size=Pt(13), color=color, bold=True)
        t2 = add_text(slide, desc,
                 MX + Inches(3.3), py + Inches(0.08), Inches(8.5), Inches(0.55),
                 size=Pt(11), color=LGRAY)
        card_groups.append([r, t1, t2])
        py += Inches(0.78)

    add_text(slide,
        "Categories overlap \u2014 a segment can exhibit multiple recovery signals.",
        MX, Inches(6.45), CW, Inches(0.35),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "6 salvage categories explained in plain English. Phonetic Bridge is "
        "the largest (93 segments). Categories overlap. Each represents a "
        "different mechanism by which meaning survives despite high WER.",
        card_groups)


def slide_25c(prs):
    """How the salvage detection decision tree works."""
    slide = new_slide(prs)
    add_title(slide, "How Salvage Detection Works")
    add_accent_line(slide)

    # Flow: Input -> 6 checks -> Score -> Threshold -> Result
    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — the process
    lt = add_text(slide, "Deterministic Decision Tree", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)

    steps = [
        ("1. Input", "Reference + hypothesis text pair", TEAL),
        ("2. Compute 6 signals", "Word overlap, sequence order, phonetic similarity,\n"
         "semantic embedding, entity preservation, length ratio", WHITE),
        ("3. Apply 15 rules", "Decision tree checks signals in priority order,\n"
         "assigns one of 15 probability leaf nodes (0.0 \u2013 1.0)", WHITE),
        ("4. Threshold at 0.5", "Probability \u2265 0.5 = recoverable\n"
         "Probability < 0.5 = likely unrecoverable", WHITE),
        ("5. Classify", "Map to 6 recovery categories based on\n"
         "which signals triggered the high probability", GREEN),
    ]

    py = CT + Inches(0.45)
    step_shapes = []
    for title, desc, color in steps:
        t = add_text(slide, title, MX + Inches(0.1), py, Inches(1.8), Inches(0.3),
                     size=Pt(13), color=color, bold=True)
        add_text(slide, desc, MX + Inches(2.0), py, Inches(3.4), Inches(0.5),
                 size=Pt(11), color=LGRAY)
        step_shapes.append(t)
        py += Inches(0.65)

    # Right — validation stats
    rx = MX + col_w + gap
    rt = add_text(slide, "Validation", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["Correlation with IS", "r = 0.934"],
        ["Agreement (IS \u2265 2.00)", "\u03ba = 0.818"],
        ["Agreement (IS \u2265 3.80)", "\u03ba = 0.690"],
        ["Recall (IS \u2265 2.00)", "97.6\u2013100%"],
        ["Cross-config stability", "r = 0.925 \u00b1 0.015"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.5), col_w,
                    row_height=Inches(0.4),
                    col_widths=[Inches(2.8), Inches(2.7)],
                    text_size=Pt(12))

    rb = add_bullets(slide, [
        "Stable across all 16 decode configurations",
        "Recall 97.6\u2013100% across 16 decode configurations",
        ("Zero cost: pure Python, no LLM calls at runtime", {"bold": True}),
    ], rx, CT + Inches(3.1), col_w, Inches(1.5), size=Pt(13))

    # Bottom
    add_text(slide,
        "The decision tree was designed at development time, then distilled "
        "into deterministic Python. No LLM is called during evaluation.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "How the salvage detection works: a 15-rule deterministic decision tree "
        "that checks 6 linguistic signals and outputs a recovery probability. "
        "Validated at r=0.934 with IS, κ=0.818 (Y+P), stable across 16 configs.",
        [[lt] + step_shapes, [rt, tbl, rb]])

def slide_25d(prs):
    """Three real salvage examples showing HOW recovery works."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Three Real Recoveries")
    add_accent_line(slide)

    add_text(slide,
        "These segments failed IS (< 3.0) but a viewer with context would understand them:",
        MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY, italic=True)

    # audit:pptx_fix_manifest_after_amosi.md slide 43 MAJOR -
    # body font was 9-10pt (below 12pt readability floor). Card height
    # bumped to 5.4" and all body fonts lifted to 12pt minimum.
    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(5.4)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    examples = [
        {
            "title": "Phonetic Bridge",
            "color": TEAL,
            "is_score": "1.29", "wer": "150%", "prob": "0.55",
            "ref": "when jesus rose again",
            "hyp": "in one sense it\u2019s rose\nand kennedy",
            "how": "A wise viewer watching a religious program "
                   "sees \u201cin one sense it\u2019s rose\u201d and thinks: "
                   "\u201cthis is about Jesus rising \u2014 \u2018sense it\u2019s\u2019 "
                   "sounds like \u2018Jesus,\u2019 and \u2018rose\u2019 = "
                   "resurrection.\u201d The mouth shapes for "
                   "\u201cjesus\u201d/\u201csense it\u2019s\u201d are nearly "
                   "identical. The overall message is "
                   "preserved even though exact words differ.",
        },
        {
            "title": "Semantic Preservation",
            "color": GREEN,
            "is_score": "2.18", "wer": "75%", "prob": "0.90",
            "ref": "moving conceptual surface data\nover to engineering solutions\nand tools",
            "hyp": "moved the conceptual rules\nover to engineering tools",
            "how": "Core meaning intact: \u201cmoving concepts \u2192 "
                   "engineering tools.\u201d WER is 75% because function "
                   "words changed, but a tech viewer follows the "
                   "intent perfectly. WER over-punishes this by "
                   "counting every small word change.",
        },
        {
            "title": "Structure Match",
            "color": GOLD,
            "is_score": "2.55", "wer": "40%", "prob": "0.95",
            "ref": "over the last 10 years we have\nhad 8,616 students",
            "hyp": "over the last 10 years we have\nhad 1,600 students",
            "how": "Grammar and word order are perfect. Only the "
                   "number changed (8,616 \u2192 1,600). A viewer "
                   "understands \u201cmany students over 10 years\u201d \u2014 the "
                   "structure carries the message even when the "
                   "exact figure is wrong.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # Title + badge - body fonts lifted to >=12pt per readability audit
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.32),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.42), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.03), cw_card - Inches(0.3), Inches(0.7),
                 size=Pt(12), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.03), cw_card - Inches(0.3), Inches(0.7),
                 size=Pt(12), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.05), cw_card - Inches(0.3), Inches(2.2),
                 size=Pt(12), color=WHITE)

    _finish(slide, 0,
        "Three real salvage examples from different recovery categories. "
        "Phonetic Bridge (IS 1.29): lip-reading confusions that are linguistically "
        "plausible, not hallucinations. Semantic Preservation (IS 2.18): WER 75% "
        "but core meaning intact. Structure Match (IS 2.55): perfect grammar, "
        "only a number changed. Each shows WHY the heuristic says recoverable.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25e — SALVAGE: 3 MORE REAL EXAMPLES (DOMAIN CONTEXT RECOVERY)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25e — SALVAGE: 3 MORE REAL EXAMPLES (DOMAIN CONTEXT RECOVERY)
# ═══════════════════════════════════════════════════════════════════════

def slide_25e(prs):
    """Three more salvage examples emphasising domain-context recovery."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Domain Context Fills the Gaps")
    add_accent_line(slide)

    add_text(slide,
        "A viewer who knows the topic recovers meaning that metrics miss entirely:",
        MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY, italic=True)

    # audit:pptx_fix_manifest_after_amosi.md slide 44 MAJOR -
    # body font was 9-10pt; lifted to 12pt and card height bumped to 5.4".
    # Three cards side by side (same layout as slide_25d)
    cw_card = Inches(3.8)
    ch_card = Inches(5.4)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    examples = [
        {
            "title": "Religious Context",
            "color": CORAL,
            "is_score": "2.75", "wer": "43%", "prob": "0.90",
            "ref": "the fear of allah is completely\ngone \u2026 no more fear of the\nunseen what a horrible spiritual",
            "hyp": "the fear of the loss complete\n\u2026 no more fear of loss\nwhat a horrible spiritual",
            "how": "A viewer watching a religious sermon "
                   "recognizes \u201cfear of the loss\u201d = \u201cfear of "
                   "Allah.\u201d The structure (\u201cno more fear \u2026 "
                   "horrible spiritual\u201d) is intact. \u201cAllah\u201d \u2192 "
                   "\u201closs\u201d and \u201cunseen\u201d \u2192 \u201cdeath\u201d are "
                   "phonetic confusions, but the sermon\u2019s "
                   "theme of spiritual fear carries through.",
        },
        {
            "title": "Geopolitical Context",
            "color": TEAL,
            "is_score": "2.86", "wer": "72%", "prob": "0.90",
            "ref": "india china afghanistan all\nthese different places \u2026 so\nboth sides would benefit",
            "hyp": "middle east and afghanistan\nall these different warring\nplaces \u2026 both sides will benefit",
            "how": "WER is 72% because country names "
                   "changed, but the argument is identical: "
                   "\u201cdistant foreign regions \u2192 both sides "
                   "benefit.\u201d A news viewer grasps the "
                   "geopolitical point instantly. \u201cIndia "
                   "China\u201d \u2192 \u201cMiddle East\u201d is a domain "
                   "swap, not a meaning loss.",
        },
        {
            "title": "Cooking Context",
            "color": GREEN,
            "is_score": "2.07", "wer": "89%", "prob": "0.80",
            "ref": "i have a tablespoon of\njalapeno fresh jalapeno",
            "hyp": "i have a dietary smoothie\ni\u2019ve got the banana called\nfresh banana",
            "how": "IS rates this a near-total failure (2.07). "
                   "But a viewer watching a cooking video "
                   "sees the presenter holding a pepper and "
                   "saying \u201cfresh banana.\u201d The visual context "
                   "instantly overrides the garbled audio \u2014 "
                   "the viewer knows it\u2019s a jalapeno. "
                   "WER is blind to multimodal cues.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # Title + badge - body fonts lifted to >=12pt per readability audit
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.32),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.42), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.03), cw_card - Inches(0.3), Inches(0.7),
                 size=Pt(12), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.03), cw_card - Inches(0.3), Inches(0.7),
                 size=Pt(12), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a wise viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.78),
                 cw_card - Inches(0.3), Inches(0.25), size=Pt(12), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.05), cw_card - Inches(0.3), Inches(2.2),
                 size=Pt(12), color=WHITE)

    _finish(slide, 0,
        "Three more salvage examples emphasising domain-context recovery. "
        "Religious Context (IS 2.75): 'fear of allah' becomes 'fear of the loss' "
        "-- a sermon viewer recognizes the spiritual theme despite name garbling. "
        "Geopolitical Context (IS 2.86): country names swap but the argument "
        "(foreign places, both sides benefit) is intact. Cooking Context (IS 2.07): "
        "'jalapeno' becomes 'banana' -- absurd in text, but a viewer SEES the "
        "pepper on screen and corrects automatically. This is the strongest argument "
        "for multimodal context: the visual channel fills gaps that audio-only metrics "
        "cannot measure.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14b — CURATED EXAMPLES VIDEO GALLERY
# ═══════════════════════════════════════════════════════════════════════

def slide_14b(prs):
    """14b: 2x3 clickable video grid - each video demonstrates a different system behavior.

    BLOCKER fix (May 2026): pre-fix audit found orphan animation refs to
    spids ['5','7','11','13','15'] (pptx_visual_audit.json). Cause: a
    prior version of this function called add_animations directly with
    a stale shape list whose IDs no longer matched the rebuilt slide.
    Fixed by collecting actual shape handles into a single click_reveal
    group passed to _finish - the animation tree now references only the
    shape IDs that exist on this slide. Body font also bumped from 9pt
    to 12pt to clear the readability floor.
    """
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    intro = add_text(slide, "Click any thumbnail to play — each video demonstrates a different system behavior:",
             MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY)

    # Grid layout: 3 cols x 2 rows
    vid_w  = Inches(3.82)
    vid_h  = Inches(2.15)   # 16:9
    gap_x  = Inches(0.23)
    gap_y  = Inches(0.65)   # space for descriptive label below each video
    row_y  = [CT + Inches(0.45), CT + Inches(0.45) + vid_h + gap_y]
    start_x = MX

    # 6 videos - balanced: 3 positive high-IS examples + 3 failure modes
    # NOTE: avoid reusing videos from opening (perfect) or demo trio (smartphone, street_photo, halluc)
    rows = [
        [("convention",   "Convention & books — meaning fully captured, minor word drops",
          "31%",  GREEN),
         ("marilyn",      "Marilyn Monroe wallpaper — proper nouns + context intact",
          "36%",  GREEN),
         ("music_play",   "Music discussion — gist preserved, phrasing changed",
          "34%",  GREEN)],
        [("spelling_smell","Spelling \u2192 smelling — phonetic confusion swaps entire domain",
          "59%",  YELLOW),
         ("admiral",      "Admiral McRae \u2192 animal migratory — classic viseme swap",
          "33%",  YELLOW),
         ("doxology",     "Doxology \u2192 fabricated story - total hallucination",
          "172%", RED)],
    ]

    # Capture every shape we add so the animation only references real spids.
    grid_shapes = [intro]
    for r, row in enumerate(rows):
        for c, (key, label, wer, color) in enumerate(row):
            x = start_x + c * (vid_w + gap_x)
            y = row_y[r]
            vid_shape = add_video(slide, key, x, y, vid_w, vid_h)
            # Descriptive caption + readable WER badge (12pt floor per audit)
            cap = add_text(slide, f"{label}  (WER {wer})",
                     x, y + vid_h + Inches(0.04), vid_w, Inches(0.40),
                     size=Pt(12), color=color, bold=False,
                     align=PP_ALIGN.CENTER)
            grid_shapes.extend([vid_shape, cap])

    _finish(slide, 0,
        "Balanced video gallery: 3 positive + 3 failure modes. "
        "Row 1 (positive): (1) Convention - person describes selling books at a "
        "convention, meaning fully captured with minor word drops. (2) Marilyn "
        "Monroe - proper noun preserved, wallpaper context intact. (3) Music - "
        "gist of playing a song preserved, phrasing changed. "
        "Row 2 (failure modes): (4) Spelling-to-smelling - phonetic confusion "
        "swaps the entire domain from literacy to odors. (5) Admiral McRae - "
        "classic viseme swap, identical lip shapes produce wrong words. "
        "(6) Doxology - total hallucination, model fabricates an unrelated story. "
        "BLOCKER fix May 2026: animation references previously orphaned spids "
        "[5,7,11,13,15]; rebuilt to pass real shape handles. "
        "Source: docs/evaluation/pptx_visual_audit.json (slide 47).",
        [grid_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE A15 — VIDEO GALLERY MAP
# ═══════════════════════════════════════════════════════════════════════

def slide_is_deep_dive(prs):
    """IS correlation deep dive — conclusions-focused."""
    slide = new_slide(prs)
    add_title(slide, "IS Validation: What Did We Learn?")
    add_accent_line(slide)

    add_text(slide,
        "We validated IS against signal analysis and cross-configuration testing. "
        "Here is what the evidence shows.",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    offset = Inches(0.45)

    # Left — compact correlation table
    lt = add_text(slide, "Signal \u2192 IS Correlation", MX, CT + offset, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "r with IS", "Dimension"],
        [["Phonetic Sim", "0.943", "Word Accuracy"],
         ["Inv. WER", "0.834", "Word Accuracy"],
         ["Inv. WWER", "0.823", "Word Accuracy"],
         ["Semantic Sim", "0.856", "Meaning"],
         ["NEA F1", "0.748", "Entity Accuracy"],
         ["Length Ratio", "0.521", "Output Sanity"]],
        MX, CT + offset + Inches(0.5), col_w, text_size=Pt(13),
        row_height=Inches(0.45),
        row_colors={0: {1: GREEN}, 5: {1: CORAL}})

    # Right — conclusions (the main point)
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Conclusions", rx, CT + offset, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("IS captures quality that WER misses",
         {"bold": True, "color": GREEN}),
        ("Cross-config validation confirms stability: "
         "mean r = 0.925 across 16 configurations",
         {"bold": True, "color": TEAL}),
        ("WER/WWER/Phonetic are redundant with each other "
         "(r > 0.79) but IS needs all three for robustness", {}),
        ("Semantic Sim is the tiebreaker \u2014 it separates "
         "segments with similar WER but different meaning "
         "preservation", {}),
    ], rx, CT + offset + Inches(0.5), rw, Inches(4.5), size=Pt(14))

    _finish(slide, 0,
        "IS validation conclusions. PCA retains 2 principal components: "
        "signal quality (68.4%, all 5 content signals load equally) and "
        "output length (19.5%, Length Ratio dominates). Semantic is NOT "
        "an independent dimension \u2014 it loads on PC1 alongside word-accuracy "
        "signals. Cross-config validation across 16 decode configurations "
        "confirms stability with mean r=0.925.",
        [[lt, tbl], [rt, rb]], click_reveal=True)


def slide_metric_disagreement(prs):
    """What metric disagreements reveal about transcription quality."""
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: What It Tells Us")
    add_accent_line(slide)

    add_text(slide,
        "IS uses 6 signals because no single metric tells the full story. "
        "Disagreements between metrics reveal specific quality patterns:",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    # Four disagreement pattern cards (2x2 grid)
    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("WWER \u226a WER", TEAL,
         "Function words wrong, content right",
         "\"the team discussed quarterly\" \u2192 \"team discuss quarterly\"\n"
         "WER 43% but WWER 15% \u2014 viewer gets the message."),
        ("NEA high, WER high", GREEN,
         "Names preserved despite poor accuracy",
         "\"Dr. Chen presented Q3 results\" \u2192 \"Dr. Chen present Q3 result\"\n"
         "WER 57% but NEA F1 = 100% \u2014 critical info intact."),
        ("Semantic high, WER high", GOLD,
         "Meaning preserved through paraphrasing",
         "\"reduce spending\" \u2192 \"cut the budget\"\n"
         "WER 100% but Semantic 0.87 \u2014 same meaning, different words."),
        ("Phonetic high, Semantic low", CORAL,
         "Sounds right, wrong meaning",
         "\"the alliance was formed\" \u2192 \"the lions were found\"\n"
         "Phonetic 0.71 but Semantic 0.12 \u2014 dangerous deceptive error."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        card_shapes = []
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)
        card_shapes.append(add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "This is why IS uses 6 signals \u2014 each disagreement pattern "
        "reveals a different type of quality that a single metric would miss.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four key metric disagreement patterns. WWER<<WER means function words "
        "are wrong but content preserved. High NEA + high WER means names survived. "
        "High semantic + high WER means paraphrasing. High phonetic + low semantic "
        "is the dangerous case — sounds right but wrong meaning.",
        [c for c in cards], click_reveal=True)


def slide_metric_disagreement_2(prs):
    """More metric disagreement patterns — part 2."""
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: More Patterns")
    add_accent_line(slide)

    add_text(slide,
        "Additional diagnostic patterns that reveal specific transcription behaviors:",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("Length \u226a 1.0, all metrics low", CORAL,
         "Signal loss — model gave up or truncated",
         "Ref: \"the thirteenth amendment abolished slavery\"\n"
         "Hyp: \"the\" (length ratio 0.06)\n"
         "All signals collapse — nothing to evaluate."),
        ("Length \u226b 1.0, Semantic low", CORAL,
         "Hallucination — fluent fabrication",
         "Ref: \"carry strap\" \u2192 Hyp: 3 paragraphs about history\n"
         "WER 6,833%, length ratio 45\u00d7 — LLM ran unchecked.\n"
         "IS catches via length + semantic: fluent but fabricated."),
        ("NEA low, Semantic moderate", GOLD,
         "Topic right, entities destroyed",
         "\"the 13th amendment\" \u2192 \"the important decision\"\n"
         "Semantic 0.52 but NEA F1 = 0% — gist right, facts lost.\n"
         "IS penalizes: critical info (names, numbers) irrecoverable."),
        ("All metrics moderate (~0.5)", TEAL,
         "Accumulated small errors — death by a thousand cuts",
         "Every signal is mediocre, none catastrophic.\n"
         "WER 55%, Semantic 0.48, Phonetic 0.51, NEA 40%.\n"
         "IS: ~2.5 (borderline) — individually OK, collectively degraded."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        card_shapes = []
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)
        card_shapes.append(add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "8 total diagnostic patterns — IS decomposes quality into actionable signals "
        "that each point to a different engineering fix.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four more metric disagreement patterns. Length collapse = signal loss. "
        "Length explosion + low semantic = hallucination. Low NEA + moderate semantic = "
        "entity destruction. All-moderate = accumulated errors.",
        [c for c in cards], click_reveal=True)

    # Note: slide visibility controlled by hidden_builders in generate_presentation.py


def slide_two_eval_systems(prs):
    """Two evaluation systems — IS and Opus-as-a-Judge."""
    slide = new_slide(prs)
    add_title(slide, "Two Evaluation Systems, One Framework")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — IS (strict) + Opus-as-Judge (generous)
    lt = add_text(slide, "The Two Systems", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    # IS card
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    r1_t = add_text(slide, "Intelligibility Score (IS)", MX + Inches(0.2),
             CT + Inches(0.6), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    r1_b = add_bullets(slide, [
        "Strict metric: composite 0\u20135 score, two operating points",
        ("IS \u2265 3.80 = Clearly conveyed: 23.1% (346/1,497)", {"bold": True}),
        ("IS \u2265 2.00 = Any useful meaning: 61.6% (922/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(12))

    # Opus-as-Judge card
    r2 = add_rect(slide, MX, CT + Inches(2.3), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    r2_t = add_text(slide, "Opus-as-a-Judge (LLM Gold Standard)", MX + Inches(0.2),
             CT + Inches(2.4), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=GREEN, bold=True)
    r2_b = add_bullets(slide, [
        "Holistic: Y/P/N per ref+hyp pair (1,497 pairs)",
        ("Y = 23.0% clearly conveyed, Y+P = 64.9% useful", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(2.8), col_w - Inches(0.4), Inches(0.8),
       size=Pt(13))

    # Right — agreement + worked example
    rx = MX + col_w + gap
    rt = add_text(slide, "Agreement Between Systems", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    agree_txt = add_text(slide,
        "\u03ba = 0.818 (good agreement)\n"
        "IS undercounts: 61.6% vs judge 64.9%.",
        rx, CT + Inches(0.5), col_w, Inches(0.6),
        size=Pt(15), color=WHITE, bold=True)

    # NIV Y+P agreement matrix (IS >= 2.00 vs Opus Y+P)
    tbl = add_table(slide,
        ["", "Opus: Y or P", "Opus: N"],
        [["IS \u2265 2.00", "883", "39"],
         ["IS < 2.00", "88", "487"]],
        rx, CT + Inches(1.3), col_w, text_size=Pt(12),
        row_colors={0: {1: GREEN}, 1: {2: CORAL}})

    # Worked examples
    we_t = add_text(slide, "Worked Examples:", rx, CT + Inches(2.6), col_w, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    we_b = add_text(slide,
        'Ref: "what does this chord sound like to you"\n'
        'Hyp: "what does this court sound like to you"\n'
        'WER: 12% \u2022 IS: 3.84 \u2022 IS Y \u2714 \u2022 Opus: Y\n\n'
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.94 \u2022 IS Y+P \u2714 \u2022 Opus: P\n'
        'Old IS \u2265 3.0 wrongly rejected this segment.',
        rx, CT + Inches(2.95), col_w, Inches(1.7),
        size=Pt(11), color=WHITE)

    _finish(slide, 0,
        "Two evaluation systems with NIV thresholds. "
        "IS >= 3.80 for clearly conveyed (23.1%, matches judge Y rate 23.0%, kappa=0.690). "
        "IS >= 2.00 for any useful meaning (61.6%, kappa=0.818, almost perfect). "
        "Opus-as-a-Judge: Y=23.0%, Y+P=64.9%. "
        "IS is a strict estimator — undercounts at both operating points. "
        "Old IS >= 3.0 threshold is superseded: it sat in no-man's land (kappa=0.565 for Y, 0.521 for Y+P).",
        [[lt, r1, r1_t, r1_b], [r2, r2_t, r2_b], [rt, agree_txt, tbl, we_t, we_b]], click_reveal=True)


def slide_llm_judge(prs):
    """LLM-as-a-Judge gold standard evaluation."""
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge: Gold Standard (1,497 Pairs)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — question/setup then methodology
    lt = add_text(slide, "What Is LLM-as-a-Judge?", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Use a frontier LLM (Claude Opus) as an independent evaluator",
        "Evaluate every reference+hypothesis pair holistically",
        "3-level verdict: Y (preserved) / P (partial) / N (not preserved)",
        ("30 duplicate pairs \u2192 86.7% intra-rater reliability", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(1.8), size=Pt(13))

    # Results table
    res_t = add_text(slide, "Results (Blind, 1,497 Pairs)", MX, CT + Inches(2.4), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Count", "%"],
        [["Y (fully preserved)", "345", "23.0%"],
         ["P (partially)", "626", "41.8%"],
         ["N (not preserved)", "526", "35.1%"],
         ["Y+P (any useful)", "971", "64.9%"]],
        MX, CT + Inches(2.8), col_w, text_size=Pt(12),
        row_colors={0: {2: GREEN}, 2: {2: CORAL}, 3: {2: TEAL}})

    # Right — Methodology
    rx = MX + col_w + gap
    rt = add_text(slide, "Methodology:", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    rb = add_bullets(slide, [
        "Claude Opus received each ref+hyp pair blind (no metrics visible)",
        "3-level holistic judgment: Y (fully conveyed), P (partial), N (lost)",
        ("\u03ba = 0.690 (Y threshold) and \u03ba = 0.818 (Y+P threshold)",
         {"color": TEAL}),
        ("Used as gold standard to calibrate IS thresholds",
         {"bold": True}),
    ], rx, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(14))

    # audit:after_amosi_narrative_actions.md fix #7 - this is the v1
    # blind judge run (Opus 4.6, 1,497 pairs). The n-best paired-test
    # slide elsewhere in this section uses v3 (dual-conf, Opus 4.7,
    # 5,988 verdicts). Footer label disambiguates the two runs so the
    # audience does not conflate them.
    judge_label = add_text(slide,
        "v1 blind judge   /   Opus 4.6   /   1,497 pairs",
        MX, Inches(6.6), CW, Inches(0.3),
        size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "LLM-as-a-Judge gold standard - v1 BLIND run (Claude Opus 4.6, "
        "1,497 pairs). Distinct from the v3 dual-conf judge run on the "
        "n-best paired-test slide later in this section, which uses "
        "Opus 4.7 with the dual-conf prompt across 5,988 verdicts. "
        "Y=23.0% (345), P=41.8% (626), N=35.1% (526). Y+P=64.9%. "
        "Intra-rater 86.7%. Pearson r=0.85 with IS. "
        "Threshold sweep: Y+P peaks at IS>=2.0 (kappa=0.818, 91.5% agreement), "
        "not IS>=3.0 (kappa=0.521). IS tier cross-tab: Excellent tier 57% Y, "
        "Failed tier 81% N, Fair tier is the split point (8% Y, 51% P, 41% N). "
        "Full cross-tab in appendix slide A16.",
        [[lt, lb],
         [res_t, tbl],
         [rt, rb, judge_label]],
        click_reveal=True)


def slide_context_eval(prs):
    """IS: A Calibrated Surrogate Metric — IS vs LLM Judge comparison."""
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate Metric")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(4.6), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric
    add_text(slide, "IS says 61.6%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments deliver useful output (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(16), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge
    add_text(slide, "LLM Judge says 64.9%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(16), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets
    bul = add_bullets(slide, [
        ("IS closely tracks LLM judge \u2014 61.6% vs 64.9% "
         "(\u03ba = 0.818)", {"bold": True, "color": WHITE}),
        "LLM-as-a-Judge (blind, 1,497 pairs) confirms: nearly 2 in 3 "
         "segments carry useful meaning",
        ("The 3pp gap (61.6% \u2192 64.9%) = IS is a calibrated "
         "surrogate, not an overcount", {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(1.8), size=Pt(14))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "An independent LLM judge confirms the true useful rate is 3pp higher.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS is a calibrated surrogate metric for transcription quality. "
        "IS says 61.6% of segments deliver useful output (IS >= 2.00). An independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 64.9% deliver useful output. The 3pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling.",
        [[r1], [bul]], click_reveal=True)


def slide_what_good_looks_like(prs):
    """IS Tier 5 examples — what good looks like."""
    slide = new_slide(prs)
    add_title(slide, "What Good Looks Like: IS Tier 5")
    add_accent_line(slide)

    add_text(slide,
        "276 segments (18.4%) score IS \u2265 4.0 \u2014 Excellent quality:",
        MX, CT, CW, Inches(0.35), size=Pt(15), color=LGRAY)

    tbl = add_table(slide,
        ["Reference", "Hypothesis", "WER", "IS"],
        [["health insurance company they pay for all "
          "the medications they pay for all your visits",
          "[exact match]", "0%", "5.0"],
         ["so here we have a different example and in "
          "this case the buyer wants to buy one and get "
          "one free",
          "so here we have a different example and in "
          "this case the buyer wants to buy one and get "
          "one free", "0%", "5.0"],
         ["allow you to work with the team in a more "
          "productive efficient and effective manner",
          "allow you to work with a team and more "
          "productive efficient and effective manner", "14%", "4.6"]],
        MX, CT + Inches(0.5), CW, text_size=Pt(11),
        row_height=Inches(0.65),
        col_widths=[Inches(4.5), Inches(4.5), Inches(0.8), Inches(0.8)],
        row_colors={0: {3: GREEN}, 1: {3: GREEN}, 2: {3: GREEN}})

    # Key callout
    add_text(slide,
        "The system reads lips with high fidelity when visual signal is strong.",
        MX, CT + Inches(3.1), CW, Inches(0.4),
        size=Pt(15), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Stats
    add_bullets(slide, [
        "276 segments (18.4%) \u2014 the architecture works",
        "57% LLM Judge Y among Tier 5 \u2014 even the strictest evaluator agrees",
        "Business/Finance topics dominate Tier 5 (closest to training data)",
        ("Perfect transcription across 20\u201340 consecutive words \u2014 not luck",
         {"bold": True}),
    ], MX, CT + Inches(3.7), CW, Inches(2.0), size=Pt(14))

    _finish(slide, 0,
        "What good looks like: 276 segments (18.4%) achieve IS 4.0-5.0. "
        "Perfect word-for-word transcription over 20-40 consecutive words. "
        "The architecture works — the challenge is getting it to work "
        "consistently across all domains.",
        [[tbl]], click_reveal=True)


def slide_llm_context_engine(prs):
    """LLM as context engine — what it does and where to go."""
    slide = new_slide(prs)
    add_title(slide, "The LLM Is a Context Engine")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what the LLM does
    lt = add_text(slide, "What the LLM Does", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    add_text(slide, "The visual encoder sees mouth shapes.",
             MX, CT + Inches(0.6), col_w, Inches(0.3),
             size=Pt(14), color=WHITE)
    add_text(slide, "The LLM resolves ambiguity using language context.",
             MX, CT + Inches(1.0), col_w, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    lb = add_bullets(slide, [
        '"p/b/m" \u2192 Is it "pat," "bat," or "mat"?',
        "LLM uses surrounding words to disambiguate",
        "Stronger LLM = better disambiguation",
        ("This is why LLM quality matters more than size", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.0), size=Pt(14))

    # Right — current vs upgrade
    rx = MX + col_w + gap
    rt = add_text(slide, "Current vs Upgrade", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)

    # Current
    r1 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Current: LLaMA-2 7B", rx + Inches(0.2), CT + Inches(0.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=CORAL, bold=True)
    add_bullets(slide, [
        "32K vocab, 4K context",
        "2023 model, limited reasoning",
    ], rx + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(12), bullet_color=CORAL)

    # Upgrade
    r2 = add_rect(slide, rx, CT + Inches(2.5), col_w, Inches(2.0),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Upgrade: Llama 3.1 8B", rx + Inches(0.2), CT + Inches(2.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=GREEN, bold=True)
    add_bullets(slide, [
        "128K vocab, 128K context",
        "Quality \u2248 LLaMA-2 70B",
        ("Same hidden_size (4096) = architecture-compatible upgrade", {"color": GREEN}),
        ("Setup: 2\u20134 weeks + retraining", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(3.0), col_w - Inches(0.4), Inches(1.2),
       size=Pt(12), bullet_color=GREEN)

    _finish(slide, 0,
        "The LLM is a context engine. The visual encoder sees mouth shapes but "
        "can't distinguish visemes. The LLM resolves ambiguity using language "
        "context. A stronger LLM means better disambiguation. Llama 3.1 8B "
        "has quality equivalent to LLaMA-2 70B with the same hidden dimension "
        "(4096), architecture-compatible but requires adapter retraining.",
        [[lt, lb], [rt, r1, r2]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE — LLM JUDGE 30-SAMPLE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

def slide_llm_judge_30(prs):
    """30-sample LLM-as-a-Judge overview — summary stats + what the sample shows."""
    slide = new_slide(prs)
    add_title(slide, "LLM Judge: Deep Dive")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — summary stats
    lt = add_text(slide, "30 Representative Segments", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Metric", "Value"],
        [["Segments", "30 (stratified sample)"],
         ["Mean WER", "61.4%"],
         ["Mean IS", "2.67 / 5.0"],
         ["LLM Judge: Y", "7  (23.3%)"],
         ["LLM Judge: P", "12  (40.0%)"],
         ["LLM Judge: N", "11  (36.7%)"],
         ["Y + P", "19  (63.3%)"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(13),
        row_height=Inches(0.42),
        row_colors={3: {1: GREEN}, 5: {1: CORAL}, 6: {1: TEAL}})

    # Right — what this sample shows
    rx = MX + col_w + gap
    rt = add_text(slide, "What the Sample Reveals", rx, CT, col_w, Inches(0.35),
                  size=Pt(17), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Distribution mirrors the full 1,497-segment dataset",
         {"bold": True}),
        # audit:after_amosi_narrative_actions.md fix #14 - reorder-robust phrasing.
        ("6 videos in this section walk through these "
         "cases one by one", {"color": TEAL}),
    ], rx, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(14))

    # Bottom takeaway
    bk = add_text(slide,
        "Each video has burned-in subtitles showing reference (top) and "
        "hypothesis (bottom) \u2014 watch the lip movements and compare.",
        MX, Inches(6.2), CW, Inches(0.4),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "30-sample overview: stratified sample from the 1,497-segment dataset. "
        "Distribution matches full dataset closely: Y=23%, P=40%, N=37%. "
        "Mean WER 61.4% vs 64.1% full. The interesting middle zone (IS 2-4) "
        "is where partial captures, phonetic bridges, and domain confusion live. "
        "Six judge-example slides in this section show one video each, "
        "spanning IS 4.55 down to 1.79.",
        [[lt, tbl], [rt, rb, bk]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDES — 6 LLM JUDGE VIDEO EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def _judge_video_slide(prs, *, vid_key, title, ref, hyp, wer, wwer, is_score,
                       is_tier, judge, category, annotation, notes,
                       client_verdict=None):
    """Reusable builder: single video left, ref/hyp/metrics right.

    If `client_verdict` is provided (a plain-English string like "Excellent —
    meaning fully preserved"), replaces the WER/WWER/IS/Judge score header
    with the verdict tag. The client deck uses this; the academic deck
    leaves it None and renders the full metrics row.
    """
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    # Left — large video
    vid_w = Inches(6.0)
    vid_h = Inches(4.5)  # ~16:9 with margin
    vid = add_video(slide, vid_key, MX, CT + Inches(0.1), vid_w, vid_h)

    # Right — content card
    rx = MX + vid_w + Inches(0.4)
    rw = CW - vid_w - Inches(0.4)

    # Judge badge color
    badge_colors = {"Y": GREEN, "P": YELLOW, "N": RED}
    badge_col = badge_colors.get(judge, LGRAY)

    # Metrics row — academic deck shows full metrics line; client deck
    # passes `client_verdict` to suppress raw WER/WWER per N9.
    if client_verdict is not None:
        metrics_text = client_verdict
    else:
        metrics_text = (f"WER {wer}   WWER {wwer}   IS {is_score} ({is_tier})   "
                        f"Judge: {judge}")
    mt = add_text(slide, metrics_text, rx, CT, rw, Inches(0.4),
                  size=Pt(13), color=badge_col, bold=True)

    # Reference
    rl = add_text(slide, "Reference:", rx, CT + Inches(0.5), rw, Inches(0.25),
                  size=Pt(10), color=LGRAY, bold=True)
    rt = add_text(slide, f"\u201c{ref}\u201d", rx, CT + Inches(0.75), rw, Inches(1.0),
                  size=Pt(12), color=WHITE, italic=True)

    # Hypothesis
    hl = add_text(slide, "Prediction:", rx, CT + Inches(1.85), rw, Inches(0.25),
                  size=Pt(10), color=LGRAY, bold=True)
    ht = add_text(slide, f"\u201c{hyp}\u201d", rx, CT + Inches(2.1), rw, Inches(1.0),
                  size=Pt(12), color=CORAL, italic=True)

    # Category badge
    cb = add_rect(slide, rx, CT + Inches(3.2), rw, Inches(0.35),
                  fill_color=NAVY3, corner_radius=True)
    add_text(slide, category, rx + Inches(0.15), CT + Inches(3.22),
             rw - Inches(0.3), Inches(0.3),
             size=Pt(11), color=TEAL, bold=True)

    # Annotation
    at = add_text(slide, annotation, rx, CT + Inches(3.7), rw, Inches(1.5),
                  size=Pt(11), color=WHITE)

    _finish(slide, 0, notes,
            [[vid, mt], [rl, rt, hl, ht, cb, at]], click_reveal=True)


def slide_judge_ex1(prs):
    """Judge example 1: Named entity swap — bernreuter → rogers (IS 4.55)."""
    _judge_video_slide(prs,
        vid_key="judge_entity",
        title="Judge Example 1: Named Entity Swap",
        ref="market research firm bernreuter research is "
            "forecasting pv installations could reach",
        hyp="market research firm rogers research is "
            "forecasting pv installations will reach",
        wer="18.2%", wwer="15.0%", is_score="4.55",
        is_tier="Excellent", judge="Y",
        category="Named Entity Swap — meaning fully preserved",
        annotation="Only the company name changed (bernreuter \u2192 rogers) "
                   "and 'could' \u2192 'will'. The forecast about PV installations "
                   "is perfectly captured. WER penalizes the name error equally "
                   "to any other word, but a viewer gets the full message.",
        notes="Named entity swap: 'bernreuter' becomes 'rogers' — visually "
              "similar lip patterns for proper nouns. Despite 18% WER, the "
              "core message about PV installation forecasts is fully preserved. "
              "LLM judge rates Y. IS 4.55 (Excellent).")


def slide_judge_ex2(prs):
    """Judge example 2: Truncated but core preserved — 1980s film (IS 3.69)."""
    _judge_video_slide(prs,
        vid_key="judge_film",
        title="Judge Example 2: Truncated but Core Preserved",
        ref="as this new home video market matured in the 1980s "
            "a number of film companies decided they could bypass "
            "the theatrical distribution system altogether and market their",
        hyp="in the 1980s when film companies decided they could "
            "bypass the theatrical distribution system altogether "
            "among other",
        wer="48.1%", wwer="41.7%", is_score="3.69",
        is_tier="Good", judge="P",
        category="Truncation \u2014 beginning and end lost, core intact",
        annotation="The opening context ('home video market matured') and "
                   "the trailing clause are lost, but the core argument "
                   "\u2014 1980s film companies bypassing theatrical distribution "
                   "\u2014 is captured verbatim. WER is 48% because of the "
                   "missing words, but meaning is substantially there.",
        notes="Truncation example: opening and trailing clauses lost, but "
              "the core argument about 1980s film companies bypassing "
              "theatrical distribution is captured verbatim. 48% WER "
              "overstates the damage. LLM judge rates P. IS 3.69 (Good).")


def slide_judge_ex3(prs):
    """Judge example 3: Tech vocabulary drift — routers → roads (IS 3.02)."""
    _judge_video_slide(prs,
        vid_key="judge_router",
        title="Judge Example 3: Technical Vocabulary Drift",
        ref="we need a radically different approach we basically "
            "need to find a way how we can take existing routers "
            "existing switches existing links and enable them for research",
        hyp="we need a radically different approach we must indeed "
            "find a way we can design existing roads to exist with "
            "existing structures and enable them for reuse",
        wer="51.5%", wwer="47.1%", is_score="3.02",
        is_tier="Good", judge="P",
        category="Domain Vocabulary Drift \u2014 structure intact, terms swapped",
        annotation="The argument structure is perfect: 'radically different "
                   "approach' \u2192 'find a way' \u2192 'existing X' \u2192 'enable for Y'. "
                   "But networking terms (routers, switches, links, research) "
                   "become civil terms (roads, structures, reuse). Without "
                   "domain context, the model picks the most likely words.",
        notes="Technical vocabulary drift: the argument structure is perfectly "
              "preserved but networking terms (routers, switches, links) become "
              "civil engineering terms (roads, structures). The model lacks "
              "domain context. LLM judge rates P. IS 3.02 (Good).")


def slide_judge_ex4(prs):
    """Judge example 4: Scientific vocabulary lost — cortisol → stops (IS 2.67)."""
    _judge_video_slide(prs,
        vid_key="judge_cortisol",
        title="Judge Example 4: Scientific Vocabulary Lost",
        ref="couples us to light cycles in our environment "
            "tells us when to sleep tells us when to make "
            "cortisol tells us when to make testosterone "
            "basically switches on",
        hyp="takes into account our environment tells us what "
            "to eat tells us where to make turns tells us when "
            "to make stops basically switches on",
        wer="43.3%", wwer="56.8%", is_score="2.67",
        is_tier="Fair", judge="P",
        category="Scientific Terms Lost \u2014 repetitive structure preserved",
        annotation="The 'tells us when to X' pattern is captured perfectly "
                   "\u2014 all three repetitions preserved. But every scientific "
                   "term is wrong: cortisol \u2192 turns, testosterone \u2192 stops, "
                   "light cycles \u2192 (gone). WWER (56.8%) is higher than WER "
                   "(43.3%) because high-value content words are wrong.",
        notes="Scientific vocabulary destroyed: cortisol becomes 'turns', "
              "testosterone becomes 'stops', light cycles dropped entirely. "
              "But the repetitive rhetorical structure ('tells us when to X') "
              "is perfectly preserved. WWER > WER because high-value content "
              "words are wrong. LLM judge: P. IS 2.67 (Fair).")


def slide_judge_ex5(prs):
    """Judge example 5: Cooking domain confusion — jalapeno → banana (IS 2.07)."""
    _judge_video_slide(prs,
        vid_key="judge_jalapeno",
        title="Judge Example 5: Cooking Domain Confusion",
        ref="and i have a tablespoon of jalapeno fresh jalapeno",
        hyp="and i have a dietary smoothie i've got the "
            "banana called fresh banana",
        wer="88.9%", wwer="43.8%", is_score="2.07",
        is_tier="Fair", judge="P",
        category="Domain Confusion \u2014 food context right, ingredients wrong",
        annotation="The model knows it's a cooking video: 'dietary smoothie', "
                   "'banana', 'fresh' are all food words. But the specific "
                   "ingredient is completely wrong: jalapeno \u2192 banana. A viewer "
                   "watching the video would see a pepper and immediately "
                   "override the garbled text \u2014 multimodal context helps.",
        notes="Cooking domain confusion: model correctly identifies food "
              "context (smoothie, banana, fresh) but wrong ingredient — "
              "jalapeno becomes banana. 89% WER but the domain is right. "
              "A viewer watching would see the pepper and recover. "
              "LLM judge: P. IS 2.07 (Fair).")


def slide_judge_ex6(prs):
    """Judge example 6: Topic hijack — overhead lights → ghost whisperer (IS 1.79)."""
    _judge_video_slide(prs,
        vid_key="judge_lights",
        title="Judge Example 6: Topic Hijack",
        ref="i actually use the overhead lights which are "
            "mostly fluorescent which i know is a big no no "
            "but this camera",
        hyp="i actually used the overheard ghost whisperer "
            "music for that scene which i know is about to "
            "go on but the scene runs",
        wer="73.9%", wwer="68.8%", is_score="1.79",
        is_tier="Poor", judge="P",
        category="Topic Hijack \u2014 grammatically fluent, completely wrong topic",
        annotation="'Overhead lights' \u2192 'overheard ghost whisperer' is a "
                   "phonetic cascade: similar mouth shapes trigger a plausible "
                   "but wrong continuation. The sentence is grammatically "
                   "perfect and internally consistent \u2014 this is what makes "
                   "hallucinations dangerous. The original topic (camera "
                   "lighting) is entirely replaced (TV production).",
        notes="Topic hijack: 'overhead lights' sounds like 'overheard ghost "
              "whisperer' to the visual encoder. The model then generates a "
              "grammatically perfect continuation about TV production. This is "
              "a classic hallucination pattern — fluent, coherent, completely "
              "wrong. LLM judge: P (the model produces something). IS 1.79 (Poor).")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE — LLM JUDGE HTML REPORT SCREENSHOT (HIDDEN BACKUP)
# ═══════════════════════════════════════════════════════════════════════

def slide_judge_report_screenshot(prs):
    """Hidden slide: full-page screenshot of the 30-sample HTML report."""
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge Report (30 Samples)")
    add_accent_line(slide)

    # Full-width report screenshot
    img = add_image(slide, "llm_judge_report", MX, CT, width=CW, height=Inches(5.4))

    _finish(slide, 0,
        "Screenshot of the interactive HTML report (30 stratified samples from "
        "1,497-segment dataset). Color-coded word diffs: green = match, "
        "yellow = substitution, red = insertion. Columns: WER, WWER, NEA F1, IS, "
        "LLM Judge verdict (Y/P/N). Distribution: Y=23.3%, P=40.0%, N=36.7%, "
        "Y+P=63.3%. Mean WER 61.4%, Mean IS 2.67/5.0.",
        [[img]])


# ═══════════════════════════════════════════════════════════════════════
# IS vs OPUS JUDGE DISAGREEMENT SLIDES
# ═══════════════════════════════════════════════════════════════════════

def slide_disagreement_blind(prs):
    """Where IS and the Judge Disagree — blind evaluation."""
    slide = new_slide(prs)
    add_title(slide, "Where IS and the Judge Disagree")
    add_accent_line(slide)

    # Subtitle
    sub = add_text(slide,
        "22 of 1,497 segments (1.5%) — rare but revealing edge cases",
        MX, CT, CW, Inches(0.35),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # --- Two cards side by side ---
    card_w = Inches(5.8)
    card_h = Inches(4.2)
    gap = Inches(0.53)
    card_y = CT + Inches(0.55)

    # LEFT CARD — IS Too Harsh (green border)
    left_shapes = []
    r_l = add_rect(slide, MX, card_y, card_w, card_h,
                   fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                   corner_radius=True)
    left_shapes.append(r_l)

    left_shapes.append(add_rich_text(slide, [
        [("IS Too Harsh", {"size": Pt(16), "color": GREEN, "bold": True}),
         ("  \u2014  19 cases (1.3%)", {"size": Pt(13), "color": LGRAY})],
    ], MX + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(0.35)))

    left_shapes.append(add_text(slide,
        "Judge says Y (meaning conveyed)\nIS says < 3.0 (metric failure)",
        MX + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(12), color=LGRAY))

    # Example
    left_shapes.append(add_rect(slide,
        MX + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    left_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("\"one really nice thing about this is\"",
          {"size": Pt(11), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(11), "color": GOLD, "bold": True}),
         ("\"what a brilliant idea this is\"",
          {"size": Pt(11), "color": WHITE, "italic": True})],
        [("IS = 1.84  |  WER = 71%  |  Judge: Y",
          {"size": Pt(10), "color": LGRAY})],
    ], MX + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(1.2)))

    left_shapes.append(add_text(slide,
        "Paraphrases and phonetic bridges preserve\n"
        "meaning that word-level metrics punish.",
        MX + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(0.6),
        size=Pt(12), color=GREEN, italic=True))

    # Also add remaining root causes
    left_shapes.append(add_text(slide,
        "\u2022 Harmless hallucination (extra words, core intact)\n"
        "\u2022 Short segments amplify WER disproportionately",
        MX + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(0.6),
        size=Pt(10), color=LGRAY))

    # RIGHT CARD — IS Too Generous (red border)
    right_shapes = []
    rx = MX + card_w + gap
    r_r = add_rect(slide, rx, card_y, card_w, card_h,
                   fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                   corner_radius=True)
    right_shapes.append(r_r)

    right_shapes.append(add_rich_text(slide, [
        [("IS Too Generous", {"size": Pt(16), "color": CORAL, "bold": True}),
         ("  \u2014  3 cases (0.2%)", {"size": Pt(13), "color": LGRAY})],
    ], rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(0.35)))

    right_shapes.append(add_text(slide,
        "Judge says N (meaning lost)\nIS says \u2265 3.0 (metric pass)",
        rx + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(12), color=LGRAY))

    # Example
    right_shapes.append(add_rect(slide,
        rx + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    right_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("\"all you have to do is unscrew\"",
          {"size": Pt(11), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(11), "color": GOLD, "bold": True}),
         ("\"all you have to do is not to\"",
          {"size": Pt(11), "color": WHITE, "italic": True})],
        [("IS = 3.42  |  WER = 29%  |  Judge: N",
          {"size": Pt(10), "color": LGRAY})],
    ], rx + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(1.2)))

    right_shapes.append(add_text(slide,
        "Structural match hides semantic reversal \u2014\n"
        "IS cannot detect that meaning is inverted.",
        rx + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(0.6),
        size=Pt(12), color=CORAL, italic=True))

    right_shapes.append(add_text(slide,
        "\u2022 Domain confusion (medical \u2192 wellness)\n"
        "\u2022 Word salad with scattered correct words",
        rx + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(0.6),
        size=Pt(10), color=LGRAY))

    # Bottom strip
    bot = add_text(slide,
        "98.5% agreement \u2014 disagreements are edge cases, not systemic failure",
        MX, Inches(6.35), CW, Inches(0.35),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS vs Opus Judge disagreement analysis (blind evaluation).\n\n"
        "LEFT — IS False Negatives (19 cases, 1.3%): Judge says Y, IS < 2.00. "
        "Paraphrases, phonetic bridges, harmless hallucinations that preserve "
        "core meaning but score poorly on word-level metrics.\n"
        "Other examples: 'living in space' topic preserved (IS 1.98, WER 111%); "
        "'human implications' captures 'human application' (IS 2.06, WER 100%); "
        "'to the next level' intact but trailing words added (IS 2.32, WER 100%).\n\n"
        "RIGHT — IS False Positives (3 cases, 0.2%): Judge says N, IS >= 2.00. "
        "Semantic reversal ('unscrew' -> 'not to', IS 3.42); domain swap "
        "('blood extraction, x-ray' -> 'cut hair, ashram', IS 3.14); "
        "phonetic garbage ('one twitch is all you do' -> 'one to rich is all the', IS 3.01).\n\n"
        "NIV thresholds (IS >= 3.80 for Y, >= 2.00 for Y+P) define the operating points.",
        [left_shapes, right_shapes, [bot]], click_reveal=True)


def slide_disagreement_context(prs):
    """Context makes the judge stricter — disagreement examples."""
    slide = new_slide(prs)
    add_title(slide, "Context Exposes Hidden Failures")
    add_accent_line(slide)

    # --- Left side: compact transition matrix ---
    left_w = Inches(5.5)

    lt = add_text(slide, "Blind \u2192 Context Transitions",
                  MX, CT, left_w, Inches(0.35),
                  size=Pt(16), color=TEAL, bold=True)

    # Transition matrix
    tbl = add_table(slide,
        ["", "\u2192 Y", "\u2192 P", "\u2192 N"],
        [["Y (345)", "207", "138", "0"],
         ["P (626)", "17", "517", "92"],
         ["N (526)", "1", "50", "475"]],
        MX, CT + Inches(0.5), left_w, text_size=Pt(13),
        col_widths=[Inches(1.6), Inches(1.3), Inches(1.3), Inches(1.3)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Key stat below matrix
    stat = add_rich_text(slide, [
        [("230 downgrades", {"size": Pt(15), "color": CORAL, "bold": True}),
         (" vs ", {"size": Pt(15), "color": WHITE}),
         ("68 upgrades", {"size": Pt(15), "color": GREEN, "bold": True})],
        [("Y\u2192P dominant (138): domain knowledge reveals vocabulary failures",
          {"size": Pt(12), "color": LGRAY})],
    ], MX, CT + Inches(2.6), left_w, Inches(0.8))

    # Additional stats
    add_bullets(slide, [
        "80.1% of judgments stable across both modes",
        "Only 1 N\u2192Y rescue in 1,497 pairs",
        ("Context is a quality tool, not a rescue tool",
         {"color": TEAL, "bold": True}),
    ], MX, CT + Inches(3.4), left_w, Inches(1.8), size=Pt(12))

    # --- Right side: killer example ---
    rx = MX + left_w + Inches(0.6)
    rw = CW - left_w - Inches(0.6)

    rt = add_text(slide, "The IS = 4.75 False Positive",
                  rx, CT, rw, Inches(0.35),
                  size=Pt(16), color=CORAL, bold=True)

    # Example card
    ex_card = []
    ex_r = add_rect(slide, rx, CT + Inches(0.5), rw, Inches(2.8),
                    fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                    corner_radius=True)
    ex_card.append(ex_r)

    ex_card.append(add_rich_text(slide, [
        [("IS = 4.75", {"size": Pt(18), "color": CORAL, "bold": True}),
         ("  (near perfect!)", {"size": Pt(13), "color": LGRAY})],
    ], rx + Inches(0.2), CT + Inches(0.6), rw - Inches(0.4), Inches(0.4)))

    ex_card.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("\"...because I'm ", {"size": Pt(11), "color": WHITE, "italic": True}),
         ("a lover of", {"size": Pt(11), "color": GREEN, "bold": True, "italic": True}),
         ("\"", {"size": Pt(11), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(11), "color": GOLD, "bold": True}),
         ("\"...because I'm ", {"size": Pt(11), "color": WHITE, "italic": True}),
         ("not a lover of", {"size": Pt(11), "color": CORAL, "bold": True, "italic": True}),
         ("\"", {"size": Pt(11), "color": WHITE, "italic": True})],
    ], rx + Inches(0.2), CT + Inches(1.15), rw - Inches(0.4), Inches(0.8)))

    ex_card.append(add_text(slide,
        "One word reverses the meaning.\n"
        "IS rated this near-perfect \u2014 only 10% WER.\n"
        "Context-aware judge caught the negation.",
        rx + Inches(0.2), CT + Inches(2.0),
        rw - Inches(0.4), Inches(0.8),
        size=Pt(12), color=LGRAY))

    # More context examples below
    more = add_text(slide,
        "More context false positives:\n"
        "\u2022 \"lazy natural\" \u2192 \"lazy astronaut\" (hair \u2192 space, IS 3.6)\n"
        "\u2022 \"stitches on my needle\" \u2192 \"stitches on my neck\" (knitting \u2192 medical, IS 3.3)\n"
        "\u2022 \"student loan debt\" \u2192 \"south korea\" (US policy \u2192 intl, IS 3.2)",
        rx, CT + Inches(3.5), rw, Inches(1.6),
        size=Pt(11), color=LGRAY)

    # Bottom strip
    bot = add_text(slide,
        "Domain knowledge raises the bar \u2192 strongest case for domain-aware fine-tuning",
        MX, Inches(6.35), CW, Inches(0.35),
        size=Pt(14), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware disagreement analysis.\n\n"
        "LEFT: Transition matrix shows 230 downgrades vs 68 upgrades when "
        "the judge gains domain context. Y->P is dominant (138 cases). "
        "Context never rescues failures (only 1 N->Y in 1,497 pairs).\n\n"
        "RIGHT: The most striking false positive — IS = 4.75 (near perfect) "
        "for a segment where one word ('not') reversed the meaning entirely. "
        "Blind judge rated it P, context judge caught the negation reversal.\n\n"
        "Additional context false positives show domain vocabulary swaps: "
        "hair care -> space (lazy natural -> lazy astronaut); "
        "knitting -> medical (needle -> neck, decreases -> skin grafting); "
        "US education -> international (student loan debt -> south korea, "
        "US marshals -> US marketers).\n\n"
        "These 11 context false positives (IS \u2265 3.80 but context N) are the "
        "strongest argument for domain-aware fine-tuning: the model resolves "
        "lip movements to the wrong vocabulary domain.",
        [[lt, tbl, stat], ex_card, [more, bot]], click_reveal=True)


# ============================================================================
# NEW SLIDES - Section 2 literature framing + Section 4 confidence + n-best
# (May 2026 - companion to docs/evaluation/after_amosi_audit.json)
# Body text >= 12pt; OOXML 3-level par nesting via _finish(... click_reveal=True)
# ============================================================================


def slide_literature_metrics_problem(prs):
    """Section 2 - Why WER/CER does not separate 'wrong but useful' from
    'wrong and dangerous' in the AVSR/VSP literature.

    2-card click-reveal layout: left = what the literature reports;
    right = what end users (and downstream models) actually consume.
    """
    slide = new_slide(prs)
    add_title(slide, "What the AVSR Literature Reports vs What Users Get")
    add_accent_line(slide)

    sub = add_text(slide,
        "AVSR / VSP papers (LRS3, LRW, AVSpeech) report WER almost exclusively. "
        "WER conflates failure modes a downstream user would never confuse.",
        MX, CT, CW, Inches(0.5),
        size=Pt(13), color=LGRAY, italic=True)

    card_w = Inches(5.8)
    card_h = Inches(4.2)
    gap = Inches(0.53)
    card_y = CT + Inches(0.65)

    # LEFT - what the literature reports
    L = []
    L.append(add_rect(slide, MX, card_y, card_w, card_h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "WHAT THE LITERATURE REPORTS",
             MX + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5),
             Inches(0.4), size=Pt(15), color=TEAL, bold=True))
    L.append(add_bullets(slide, [
        ("WER (Word Error Rate) - primary metric in nearly every benchmark",
         {"bold": True}),
        "CER (Char Error Rate) on small alphabets - ASR/lip-reading",
        "Sometimes BLEU / METEOR for translation deck",
        ("Implicit assumption: WER is monotone in usefulness", {"color": CORAL}),
        "Reported WERs on LRS3: AV-HuBERT 25.4%, AutoAVSR 19.1%, etc.",
    ], MX + Inches(0.25), card_y + Inches(0.65),
       card_w - Inches(0.5), Inches(3.0), size=Pt(13)))
    L.append(add_text(slide,
        "All three failure modes (gibberish, partial, hallucination) "
        "score the same WER if their edit distance matches.",
        MX + Inches(0.25), card_y + Inches(3.4),
        card_w - Inches(0.5), Inches(0.7),
        size=Pt(12), color=CORAL, italic=True))

    # RIGHT - what users see
    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, card_y, card_w, card_h, fill_color=NAVY2,
                     border_color=GOLD, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "WHAT END USERS ACTUALLY CONSUME",
             rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5),
             Inches(0.4), size=Pt(15), color=GOLD, bold=True))

    # Three example pairs - same WER ~50%, very different downstream value.
    # audit-md:section_C examples (judge_entity / judge_lights examples).
    R.append(add_text(slide, "Same WER ~50% - very different downstream value:",
             rx + Inches(0.25), card_y + Inches(0.65),
             card_w - Inches(0.5), Inches(0.3),
             size=Pt(12), color=WHITE, bold=True))

    pairs = [
        ("Partial / useful",
         "REF: \"market research firm bernreuter is forecasting pv installations\"\n"
         "HYP: \"market research firm rogers is forecasting pv installations\"",
         GREEN),
        ("Topic hijack / dangerous",
         "REF: \"the overhead lights are mostly fluorescent\"\n"
         "HYP: \"the overheard ghost whisperer music for that scene\"",
         CORAL),
    ]
    py = card_y + Inches(1.05)
    for label, body, color in pairs:
        R.append(add_text(slide, label,
                 rx + Inches(0.25), py, card_w - Inches(0.5),
                 Inches(0.3), size=Pt(12), color=color, bold=True))
        R.append(add_text(slide, body,
                 rx + Inches(0.25), py + Inches(0.3),
                 card_w - Inches(0.5), Inches(1.05),
                 size=Pt(12), color=LGRAY))
        py += Inches(1.4)

    R.append(add_text(slide,
        "Same WER. Same paper score. One is downstream-usable; "
        "one mis-routes every downstream tag.",
        rx + Inches(0.25), card_y + card_h - Inches(0.55),
        card_w - Inches(0.5), Inches(0.5),
        size=Pt(12), color=GOLD, italic=True))

    # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
    # phrasing replaced with reorder-robust language.
    bot = add_text(slide,
        "Therefore we built a separate evaluation framework "
        "(IS - Intelligibility Score) - introduced below in this section.",
        MX, Inches(6.5), CW, Inches(0.35),
        size=Pt(13), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json + audit-md:section_C "
        "(LLM judge examples) + recurring callback to slide_wer_lies. "
        "The point of this slide is to frame WHY we needed IS at all - the "
        "AVSR literature reports WER almost exclusively, and WER conflates "
        "three downstream-distinct failure modes (gibberish, partial, "
        "hallucination). The bernreuter/rogers swap and the overhead-lights/"
        "ghost-whisperer hijack both score ~50% WER but a downstream "
        "consumer treats them very differently. Bridges to the IS intro slide.",
        [[sub], L, R, [bot]], click_reveal=True)


def slide_confidence_problem(prs):
    """Section 4 opener - in production we have no ground truth."""
    slide = new_slide(prs)
    add_title(slide, "Confidence Without Ground Truth")
    add_accent_line(slide)

    intro = add_text(slide,
        "All the IS / WER / Judge analysis so far depends on having a "
        "reference text. In production, on a video the user just uploaded, "
        "there IS no reference. How do we surface uncertainty at runtime?",
        MX, CT, CW, Inches(1.0),
        size=Pt(15), color=LGRAY, italic=True)

    bul = add_bullets(slide, [
        ("Goal: a per-segment and per-word reliability signal computed "
         "only from the model's own outputs (no reference text).",
         {"bold": True}),
        "We need to rank segments so a reviewer can triage which to verify.",
        "We need to rank words inside a segment so a reader knows where to look.",
        ("Constraint: zero extra inference cost. Whatever signal we use must be "
         "extractable from a single decode pass.", {"color": TEAL}),
    ], MX, CT + Inches(1.2), CW, Inches(3.5), size=Pt(15))

    # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
    # phrasing replaced; works under reorder.
    bottom = add_text(slide,
        "Two layers of confidence (introduced below in this section): "
        "per-word from the LLM softmax, per-segment as the aggregate.",
        MX, Inches(6.4), CW, Inches(0.4),
        size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json (Section D) + "
        "docs/confidence/confidence_full_analysis.md. The point: IS, WER, "
        "judge - all these are EVALUATION-time signals that need a "
        "reference. In production on user video, no reference exists. We "
        "need a calibrated runtime confidence signal computed from model "
        "outputs only. This slide sets up the question; the two-layer "
        "scheme is introduced in the slides that follow this one in the "
        "current section ordering.",
        [[intro], [bul], [bottom]], click_reveal=True)


def slide_two_layer_confidence_research(prs):
    """Two-layer confidence (research framing).

    Lifted from slides_client.py::slide_client_two_layer_confidence and
    re-framed for research peers - explicit math, drop the trust warmth.
    """
    slide = new_slide(prs)
    add_title(slide, "Two Layers of Confidence (Per-Word + Per-Segment)")
    add_accent_line(slide)

    add_text(slide,
        "Both layers are derived from the LLM's output softmax during "
        "the same decode pass. Zero extra cost.",
        MX, CT, CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    top = Inches(2.0)
    h = Inches(3.6)

    # Layer 1 - per-word (per-token softmax)
    L = []
    x1 = MX
    L.append(add_rect(slide, x1, top, card_w, h, fill_color=NAVY2,
                     border_color=BLUE, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "1. PER-WORD",
             x1 + Inches(0.3), top + Inches(0.2),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(13), bold=True, color=BLUE))
    L.append(add_text(slide, "max softmax probability per token",
             x1 + Inches(0.3), top + Inches(0.6),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(15), bold=True, color=WHITE))
    L.append(add_text(slide,
             "p_t  =  max_v  P(token = v | x_<=t)",
             x1 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(13), color=GOLD, italic=True, align=PP_ALIGN.CENTER))
    L.append(add_bullets(slide, [
        "Aggregate sub-token probabilities up to whole-word level",
        "Render colour-coded inline in the report (BLUE / ORANGE / PURPLE)",
        ("23,261 words across 1,427 segments  # audit:perword_new_total_words",
         {"color": LGRAY}),
    ], x1 + Inches(0.3), top + Inches(1.6),
       card_w - Inches(0.6), Inches(1.8), size=Pt(12)))

    # Layer 2 - per-segment (sequence-level)
    R = []
    x2 = MX + card_w + gap
    R.append(add_rect(slide, x2, top, card_w, h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "2. PER-SEGMENT",
             x2 + Inches(0.3), top + Inches(0.2),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(13), bold=True, color=TEAL))
    R.append(add_text(slide, "mean log-probability over the segment",
             x2 + Inches(0.3), top + Inches(0.6),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(15), bold=True, color=WHITE))
    R.append(add_text(slide,
             "mean_prob  =  exp( (1/T) * sum_t log p_t )",
             x2 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(13), color=GOLD, italic=True, align=PP_ALIGN.CENTER))
    # audit:after_amosi_narrative_actions.md fix #13 - the demo cards
    # later in the deck use the term "sequence_conf"; add an alias bullet
    # here so the audience can match the demo cards back to mean_prob.
    R.append(add_bullets(slide, [
        "Plus a length-anomaly check (output too short or too long for the visual)",
        ("Calibrated thresholds: T_trust 0.89, T_safe 0.82, T_salvage 0.74",
         {"color": TEAL}),
        ("Strip-coloring boundary at 0.65 (below: green word flag misleads)",
         {"color": CORAL}),
        ("Demo slides label this signal sequence_conf (= mean_prob)",
         {"color": LGRAY, "italic": True}),
    ], x2 + Inches(0.3), top + Inches(1.6),
       card_w - Inches(0.6), Inches(1.8), size=Pt(12)))

    bot = add_text(slide,
        "Both layers are calibrated against a held-out blind LLM judge. "
        "Calibration is decode-tied: a stronger LLM forces re-running the "
        "diagnostic.",
        MX, Inches(6.45), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
        # phrasing replaced with reorder-robust language.
        "Source: docs/evaluation/after_amosi_audit.json (Section D) + "
        "docs/confidence/confidence_full_analysis.md + "
        "docs/confidence/lessons_learned_band_rule_v2.md. Lifted from "
        "slides_client.py::slide_client_two_layer_confidence and reframed "
        "for research peers: dropped the trust warmth, added explicit "
        "math (mean log-prob and per-token max-prob). The slides that "
        "follow in this section quantify what the two layers separate.",
        [L, R, [bot]], click_reveal=True)


def slide_per_word_confidence_distribution(prs):
    """Per-word band distribution under joint vs legacy rule."""
    slide = new_slide(prs)
    add_title(slide, "Per-Word Confidence Bands - Distribution")
    add_accent_line(slide)

    sub = add_text(slide,
        "Total per-word judgments: 23,261 across 1,427 segments. Joint "
        "rule = top1_conf>=0.95 AND beam_agreement>=0.80; legacy = conf only.",
        MX, CT, CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True)

    headers = ["Band", "JOINT n", "JOINT %", "LEGACY n", "LEGACY %"]
    rows = [
        # audit:perword_new_green_count vs perword_old_green_count, etc.
        ["Green",  "7,591",  "32.6%", "11,309", "48.6%"],
        ["Yellow", "6,571",  "28.2%",  "7,470", "32.1%"],
        ["Red",    "9,099",  "39.1%",  "4,482", "19.3%"],
    ]
    row_colors = {
        0: {0: BLUE,   1: BLUE,   3: BLUE},
        1: {0: ORANGE, 1: ORANGE, 3: ORANGE},
        2: {0: PURPLE, 1: PURPLE, 3: PURPLE},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.7), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.0), Inches(2.5), Inches(2.5),
                                Inches(2.5), Inches(2.5)],
                    text_size=Pt(14), row_colors=row_colors)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    cy = CT + Inches(3.0)
    L = []
    L.append(add_rect(slide, MX, cy, card_w, Inches(2.7), fill_color=NAVY2,
                     border_color=BLUE, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "JOINT RULE - STRICTER, MORE RELIABLE",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(13), color=BLUE, bold=True))
    L.append(add_bullets(slide, [
        "Green count drops 33% (11,309 -> 7,591)",
        ("Reds rise 2x (4,482 -> 9,099): the rule pushes ambiguous words out "
         "of green into red", {}),
        # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
        # replaced with reorder-robust phrasing.
        ("Each green is more reliable (89.8% vs 80.6%; quantified later "
         "in this section)",
         {"color": GREEN, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.55),
       card_w - Inches(0.5), Inches(2.0), size=Pt(13)))

    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, Inches(2.7), fill_color=NAVY2,
                     border_color=PURPLE, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "LEGACY CONF-ONLY - PERMISSIVE",
             rx + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(13), color=PURPLE, bold=True))
    R.append(add_bullets(slide, [
        "Almost half of all words paint as green",
        ("Many of those greens are model-confident but beam-disagreed "
         "(genuine ambiguity hidden behind softmax)", {}),
        ("Used in pre-May-2026 deployments; superseded by joint rule",
         {"color": LGRAY, "italic": True}),
    ], rx + Inches(0.25), cy + Inches(0.55),
       card_w - Inches(0.5), Inches(2.0), size=Pt(13)))

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json (Section D, "
        "overall_new_rule and overall_old_rule). 23,261 total words "
        "(audit:perword_new_total_words). Joint rule = top1_conf>=0.95 "
        "AND beam_agreement>=0.80; legacy = conf-only at 0.85. The joint "
        "rule reclassifies ~3,700 words from green to red+yellow, "
        "tightening green reliability from 80.6% to 89.8%. See also "
        "docs/confidence/lessons_learned_band_rule_v2.md.",
        [[sub, tbl], L, R], click_reveal=True)


def slide_band_reliability_overall(prs):
    """Overall P(correct | band) under joint rule vs legacy."""
    slide = new_slide(prs)
    add_title(slide, "Band Reliability - Overall P(correct | band)")
    add_accent_line(slide)

    sub = add_text(slide,
        "P(correct) of each band, computed by aligning hypothesis tokens "
        "to reference text via Levenshtein. Joint rule's green is the "
        "biggest gain.",
        MX, CT, CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True)

    headers = ["Band", "JOINT P(correct)", "LEGACY P(correct)", "Delta"]
    rows = [
        # audit:perword_new_green_p_correct vs perword_old_green_p_correct
        ["Green",  "89.8%", "80.6%",  "+9.2pp"],
        ["Yellow", "59.0%", "38.3%",  "+20.7pp"],
        ["Red",    "21.7%", "15.4%",  "+6.3pp"],
    ]
    row_colors = {
        0: {0: BLUE,   1: GREEN, 3: GREEN},
        1: {0: ORANGE, 1: GOLD,  3: GREEN},
        2: {0: PURPLE, 1: CORAL, 3: GREEN},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.7), CW, row_height=Inches(0.65),
                    col_widths=[Inches(2.5), Inches(3.5), Inches(3.5),
                                Inches(2.6)],
                    text_size=Pt(15), row_colors=row_colors)

    take = add_rect(slide, MX, CT + Inches(3.4), CW, Inches(2.0),
                    fill_color=NAVY2, border_color=BLUE, border_width=Pt(2),
                    corner_radius=True)
    take_t = add_text(slide,
        "Joint rule's biggest reliability gain is in GREEN: 89.8% "
        "vs 80.6% (+9.2pp).  Yellow gains the largest absolute lift "
        "(+20.7pp) because the legacy yellow band collected the high-conf-"
        "but-disagreed tokens that the joint rule reclassifies as red.",
        MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
        Inches(1.7), size=Pt(14), color=WHITE)

    bot = add_text(slide,
        "All numbers from audit JSON keys perword_{new,old}_{green,yellow,red}_p_correct. "
        "Total 23,261 words.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section D. Overall "
        "band reliability across the full 23,261-word corpus. Joint rule's "
        "GREEN goes 80.6% -> 89.8% reliable (+9.2pp); the bigger absolute "
        "shift in YELLOW (+20.7pp) reflects band relocations. The Strip "
        "policy below seg mean_prob 0.65 is independent of these overall "
        "numbers - see slide_band_reliability_stratified.",
        [[sub, tbl], [take, take_t], [bot]], click_reveal=True)


def slide_band_reliability_stratified(prs):
    """Band reliability stratified by segment mean_prob bin."""
    slide = new_slide(prs)
    add_title(slide, "Green Reliability Depends on Segment Quality")
    add_accent_line(slide)

    sub = add_text(slide,
        "P(correct | green) stratified by segment mean_prob bin. "
        "Green ranges from 96.4% (clean segments) to 18.2% (noisy ones).",
        MX, CT, CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True)

    img = add_image(slide, "P_band_reliability_stratified",
                    MX, CT + Inches(0.5),
                    width=Inches(7.6), height=Inches(4.6))

    rx = MX + Inches(7.8)
    rw = CW - Inches(7.8)
    rt = add_text(slide, "Stratified P(green | bin)",
                  rx, CT + Inches(0.5), rw, Inches(0.3),
                  size=Pt(13), color=BLUE, bold=True)

    # Joint-rule bins (>=0.65 only) - per audit:section_D...stratified_by_seg_mean_conf
    headers = ["seg mean_prob", "P(grn correct)"]
    rows = [
        ["0.85+ (very_high)", "96.4%"],   # audit:section_D...very_high.green_p_correct
        ["0.75-0.85 (high)",  "91.7%"],   # audit:section_D...high.green_p_correct
        ["0.65-0.75 (mid)",   "86.1%"],   # audit:section_D...mid.green_p_correct
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(11), row_height=Inches(0.4))

    leg_t = add_text(slide,
        "Below 0.65 (legacy rule only):\n"
        "0.55-0.65: 41.3%\n"
        "0.40-0.55: 21.8%\n"
        "<0.40:    18.2%",
        rx, CT + Inches(2.5), rw, Inches(1.6),
        size=Pt(11), color=LGRAY)

    caveat = add_text(slide,
        "Caveat: stratified P(correct|green) under JOINT rule is only "
        "computable for >=0.65 bins (filtered diagnostic CSV). Below-0.65 "
        "values are from the legacy CONF-ONLY rule on the B3 sidecar.",
        rx, CT + Inches(4.2), rw, Inches(1.0),
        size=Pt(9), color=CORAL, italic=True)

    bot = add_text(slide,
        "Headline: green-band reliability is conditional on segment "
        "quality. Peaks at 96% in clean segments; falls below 50% in "
        "noisy ones - which is why the strip-coloring boundary is set at 0.65.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section D, "
        "stratified_by_seg_mean_conf + anomalies/Caveats. Plot: "
        "P_band_reliability_stratified.png. Joint-rule values for very_high"
        "/high/mid bins (>=0.65) come directly from "
        "trust_diagnostic/per_word_diagnostic.csv. The <0.65 bins "
        "(mid_low/low/very_low at 41.3/21.8/18.2) are from the legacy "
        "CONF-ONLY rule on the B3 sidecar - the JOINT-rule diagnostic "
        "CSV is filtered to seg_mean_conf>=0.65, so JOINT-rule values "
        "for those bins are not currently recomputable. This is why "
        "the strip-coloring boundary lives at mean_prob 0.65 - below "
        "that, even green words are <50% reliable.",
        [[sub, img], [rt, tbl, leg_t, caveat], [bot]], click_reveal=True)


def slide_green_leakage_examples(prs):
    """Concrete numeric/entity hallucinations with high green confidence."""
    slide = new_slide(prs)
    add_title(slide, "Green Leakage - When High Confidence Misleads")
    add_accent_line(slide)

    sub = add_text(slide,
        "2,192 wrong-and-green words across 23,261 (9.4% leakage). "
        "Numerics and entities concentrate the danger.",
        MX, CT, CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True)
    # 9.4% leakage = 2192/23261 (no single audit key; computable from
    # audit Section D totals - see audit-md:section-D + MEMORY).

    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(2.5)
    gap = Inches(0.3)
    cy = CT + Inches(0.6)

    examples = [
        {
            "title": "Numeric scale flip",
            "ref": "1 billion CFUs of probiotics",
            "hyp": "1 million CFUs of probiotics",
            "conf": "P(billion -> million) = 0.965",
            "note": "Off by 1000x. Confident, fluent, wrong.",
        },
        {
            "title": "Numeric digit drop",
            "ref": "the value is 1024",
            "hyp": "the value is 24",
            "conf": "P(1024 -> 24) = 0.958",
            "note": "Token tokenisation mis-merge.",
        },
        {
            "title": "Year drift",
            "ref": "in 2011 the project began",
            "hyp": "in 2000 the project began",
            "conf": "P(2011 -> 2000) = 0.894",
            "note": "Visually similar mouth shapes.",
        },
    ]

    cards = []
    for i, ex in enumerate(examples):
        x = MX + i * (card_w + gap)
        c = []
        c.append(add_rect(slide, x, cy, card_w, card_h, fill_color=NAVY2,
                         border_color=BLUE, border_width=Pt(2), corner_radius=True))
        c.append(add_text(slide, ex["title"],
                 x + Inches(0.2), cy + Inches(0.15), card_w - Inches(0.4),
                 Inches(0.35), size=Pt(14), color=BLUE, bold=True,
                 align=PP_ALIGN.CENTER))
        c.append(add_text(slide, "REF: " + ex["ref"],
                 x + Inches(0.2), cy + Inches(0.55), card_w - Inches(0.4),
                 Inches(0.5), size=Pt(12), color=GREEN, italic=True))
        c.append(add_text(slide, "HYP: " + ex["hyp"],
                 x + Inches(0.2), cy + Inches(1.05), card_w - Inches(0.4),
                 Inches(0.5), size=Pt(12), color=PURPLE, italic=True))
        c.append(add_text(slide, ex["conf"],
                 x + Inches(0.2), cy + Inches(1.6), card_w - Inches(0.4),
                 Inches(0.3), size=Pt(12), color=GOLD, bold=True,
                 align=PP_ALIGN.CENTER))
        c.append(add_text(slide, ex["note"],
                 x + Inches(0.2), cy + Inches(1.95), card_w - Inches(0.4),
                 Inches(0.45), size=Pt(11), color=LGRAY, italic=True))
        cards.append(c)

    bot_card = []
    bot_card.append(add_rect(slide, MX, Inches(5.6), CW, Inches(0.95),
                             fill_color=NAVY3, border_color=ORANGE,
                             border_width=Pt(1.5), corner_radius=True))
    bot_card.append(add_text(slide,
        "Production response: numbers are CAPPED at yellow under the new "
        "joint band rule, regardless of softmax probability. Entities are "
        "left in the joint-rule pipeline; calibration handles the rest. "
        "The joint rule cuts green leakage from ~16% (legacy) to 9.4% "
        "without losing too much green volume.",
        MX + Inches(0.25), Inches(5.75), CW - Inches(0.5),
        Inches(0.7), size=Pt(12), color=WHITE))

    _finish(slide, 0,
        "Source: MEMORY auto memory (Confidence - green leakage entry) + "
        "docs/confidence/green_leakage_examples.csv. Three documented "
        "production-found cases: billion->million (off by 1000x at conf "
        "0.965), 1024->24 (digit drop at 0.958), 2011->2000 (year drift "
        "at 0.894). Frame: high confidence does not mean correct, "
        "especially for numeric and entity tokens. Production response: "
        "numbers cap at yellow under the new joint rule.",
        [[sub]] + cards + [bot_card], click_reveal=True)


def slide_three_thresholds(prs):
    """Three thresholds on mean_prob (segment-level)."""
    slide = new_slide(prs)
    add_title(slide, "Three Calibrated Thresholds on Segment mean_prob")
    add_accent_line(slide)

    # audit:after_amosi_narrative_actions.md fix #13 - first visible NIV
    # mention is in this slide's table, so the subtitle now glosses it
    # once for the audience: "NIV = Native Intelligibility Verdict (the
    # LLM-as-Judge calibration label, NIV-Y / NIV-P / NIV-N)".
    sub = add_text(slide,
        "Each threshold corresponds to a target on green-band reliability. "
        "NIV = Native Intelligibility Verdict (LLM-as-Judge calibration label).",
        MX, CT, CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    headers = ["Threshold", "mean_prob", "Green reliability target", "Notes"]
    rows = [
        ["T_trust",   ">= 0.89", ">= 90% reliable", "highest precision, lowest recall"],
        ["T_safe",    ">= 0.82", ">= 85% reliable", "F1-max for NIV-Y on mean_prob"],
        ["T_salvage", ">= 0.74", ">= 75% reliable", "review zone"],
        ["Strip-coloring", "< 0.65", "< 50%",        "below this, drop word colour entirely"],
    ]
    row_colors = {
        0: {0: BLUE,   2: BLUE},
        1: {0: GREEN,  2: GREEN},
        2: {0: ORANGE, 2: ORANGE},
        3: {0: PURPLE, 2: PURPLE},
    }
    # audit:pptx_visual_audit_after_amosi.md slide 53 BLOCKER -
    # Table 4 extended past canvas (right=13.70 vs canvas 13.33). Sum was
    # 2.4+2.0+3.6+5.1=13.1" > CW(12.13"). Trimmed to fit within CW.
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.2), Inches(1.8), Inches(3.1),
                                Inches(4.6)],
                    text_size=Pt(13), row_colors=row_colors)

    op = []
    op.append(add_rect(slide, MX, CT + Inches(3.2), CW, Inches(2.0),
                       fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                       corner_radius=True))
    op.append(add_text(slide, "T_safe (mean_prob >= 0.82) - the operational default",
             MX + Inches(0.3), CT + Inches(3.35), CW - Inches(0.6),
             Inches(0.35), size=Pt(15), color=GREEN, bold=True))
    op.append(add_bullets(slide, [
        "Keeps 28% of segment volume",
        "IS_kept = 4.01  (Tier 4 - Good)",
        "WER_kept = 27.5%",
        "Precision 71%   /   Recall 79%   for NIV-Y",
    ], MX + Inches(0.3), CT + Inches(3.75),
       CW - Inches(0.6), Inches(1.4), size=Pt(13)))

    bot = add_text(slide,
        "Thresholds are Llama-2-7b specific. Any LLM swap forces "
        "re-running diagnose_confidence_signals.py.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: MEMORY auto memory (Confidence - three thresholds entry) "
        "+ docs/confidence/threshold_design.md + "
        "docs/confidence/confidence_full_analysis.md. T_safe (0.82) is "
        "the operational default chosen at F1-max for NIV-Y class on "
        "mean_prob. Strip boundary at 0.65 comes from "
        "slide_band_reliability_stratified - below that, even green words "
        "are <50% reliable. All thresholds are Llama-2-7b specific; an "
        "LLM swap forces re-calibration.",
        [[sub, tbl], op, [bot]], click_reveal=True)


def slide_three_tier_policy_research(prs):
    """Trust / Salvage / Strip operating-points table - research version."""
    slide = new_slide(prs)
    add_title(slide, "Three-Tier Policy - Per-Tier Counts and Reliability")
    add_accent_line(slide)

    sub = add_text(slide,
        "Tiers from segment mean_prob; per-tier P(green correct) under "
        "joint rule. Volumes from per_word_by_tier.csv.",
        MX, CT, CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True)

    # All numbers from audit:section_D_per_word_conf.by_tier.{Trust,Salvage,Strip}.new
    headers = ["Tier", "Green n", "P(grn corr)", "Yellow n", "P(yel corr)",
               "Red n", "P(red corr)"]
    rows = [
        ["Trust    (>=0.82)",   "3,923", "95.3%", "1,719", "76.1%", "  951", "42.0%"],
        ["Salvage (0.65-0.82)","3,091", "89.1%", "3,241", "60.5%", "3,442", "27.7%"],
        ["Strip   (<0.65)",     "  577", "56.2%", "1,611", "37.5%", "4,706", "13.1%"],
    ]
    row_colors = {
        0: {0: BLUE,   2: GREEN},
        1: {0: ORANGE, 2: GOLD},
        2: {0: PURPLE, 2: CORAL},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.6), Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6)],
                    text_size=Pt(12), row_colors=row_colors)

    L = []
    L.append(add_text(slide, "WHAT THE NUMBERS SAY",
             MX, CT + Inches(2.6), Inches(6.0), Inches(0.35),
             size=Pt(14), color=TEAL, bold=True))
    L.append(add_bullets(slide, [
        ("Trust: green is 95.3% reliable. Auto-approve.", {"color": BLUE, "bold": True}),
        ("Salvage: green is 89.1%. Pair with reviewer.", {"color": ORANGE}),
        ("Strip: green is 56.2% - misleading. Drop colours.",
         {"color": PURPLE, "bold": True}),
    ], MX, CT + Inches(3.0), Inches(6.0), Inches(2.5), size=Pt(13)))

    R = []
    R.append(add_text(slide, "HOW THE TIERS ARE USED",
             MX + Inches(6.3), CT + Inches(2.6), Inches(5.83), Inches(0.35),
             size=Pt(14), color=GOLD, bold=True))
    R.append(add_bullets(slide, [
        "Three-tier rule applies post-hoc (no re-decode required)",
        "Per-tier P(green correct) values feed the client UI threshold knob",
        ("Joint-rule tightens both sides: more red counts, but red P(correct) "
         "stays low across tiers (42 / 28 / 13%)", {}),
        ("Audit keys: by_tier.{Trust,Salvage,Strip}.new.{green,yellow,red}.p_correct",
         {"color": LGRAY, "italic": True}),
    ], MX + Inches(6.3), CT + Inches(3.0), Inches(5.83), Inches(2.5),
       size=Pt(13)))

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section D by_tier "
        "block. Lifted from slides_client.py::slide_client_trust_dashboard "
        "and re-rendered as a research-style table with raw counts. Trust "
        "tier auto-approve threshold; Salvage tier pair-with-reviewer; "
        "Strip tier drops word colouring entirely (green <60% reliable). "
        "All P(band correct) values are joint-rule from "
        "per_word_by_tier.csv (audit Section D).",
        [[sub, tbl], L, R], click_reveal=True)


def slide_band_reliability_by_niv(prs):
    """P(correct | band) within Y+P, stratified by NIV-Y/P/N."""
    slide = new_slide(prs)
    add_title(slide, "Per-Word Bands Stratified by NIV Outcome")
    add_accent_line(slide)

    sub = add_text(slide,
        "Within useful content (Y+P), per-word band carries strong "
        "information about correctness - 62.5pp green->red spread.",
        MX, CT, CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True)

    img = add_image(slide, "P_band_reliability_by_niv",
                    MX, CT + Inches(0.5),
                    width=Inches(7.6), height=Inches(4.6))

    rx = MX + Inches(7.8)
    rw = CW - Inches(7.8)

    rt = add_text(slide, "P(correct | band)",
                  rx, CT + Inches(0.5), rw, Inches(0.3),
                  size=Pt(13), color=TEAL, bold=True)

    # audit-md:band_reliability_by_niv (no flat key in audit JSON)
    headers = ["Tier", "GRN", "YEL", "RED"]
    rows = [
        ["Y+P combined", "87.2%", "48.9%", "24.7%"],
        ["NIV-Y only",   "94.1%", "65.2%", "38.7%"],
        ["NIV-P only",   "79.7%", "41.2%", "20.3%"],
        ["NIV-N only",   "37.1%", "16.9%",  "6.9%"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(10), row_height=Inches(0.4))

    take = add_bullets(slide, [
        ("62.5pp green->red spread inside Y+P - flag is real signal, "
         "not decoration", {"bold": True, "color": GREEN}),
        ("NIV-P: steepest gradient (80/41/20%) - flag does heaviest "
         "lifting in Salvage tier", {"color": ORANGE}),
        ("NIV-N: green misleads at 37% - confirms Strip policy: drop "
         "colour rendering entirely", {"color": PURPLE}),
    ], rx, CT + Inches(2.85), rw, Inches(2.5), size=Pt(11))

    bot = add_text(slide,
        "Per-word flag is genuine signal inside Salvage tier, not decoration. "
        "Source: docs/confidence/band_reliability_by_niv.md.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/confidence/band_reliability_by_niv.md "
        "(audit-md:band_reliability_by_niv) - audit JSON does NOT carry "
        "per-NIV-tier band reliabilities (no band_by_niv_yp_* keys in "
        "after_amosi_audit.json; would be useful to add). Plot: "
        "P_band_reliability_by_niv.png. Within Y+P (useful content): "
        "P(correct | green/yellow/red) = 87.2% / 48.9% / 24.7%, with "
        "62.5pp spread. NIV-P shows the steepest gradient (80/41/20%), "
        "which is why per-word flag is most valuable in the Salvage "
        "tier. NIV-N green is only 37.1% reliable - confirms strip policy.",
        [[sub, img], [rt, tbl, take], [bot]], click_reveal=True)


def slide_agreement_aware_bands(prs):
    """Definition of joint conf+agreement band rule (May 2 2026)."""
    slide = new_slide(prs)
    add_title(slide, "Joint Confidence + Beam-Agreement Band Rule")
    add_accent_line(slide)

    sub = add_text(slide,
        "Production rule shipped May 2 2026. Two axes: per-token softmax "
        "AND beam-agreement across the n-best alternatives.",
        MX, CT, CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(2.4)
    gap = Inches(0.3)
    cy = CT + Inches(0.6)

    bands = [
        ("GREEN", BLUE,
         "top1_conf >= 0.95  AND  beam_agreement >= 0.80"),
        ("YELLOW", ORANGE,
         "top1_conf >= 0.65  AND  beam_agreement >= 0.50"),
        ("RED", PURPLE,
         "otherwise (numbers are CAPPED at yellow regardless of conf)"),
    ]

    band_groups = []
    for i, (label, color, defn) in enumerate(bands):
        x = MX + i * (card_w + gap)
        g = []
        g.append(add_rect(slide, x, cy, card_w, card_h, fill_color=NAVY2,
                         border_color=color, border_width=Pt(2), corner_radius=True))
        g.append(add_text(slide, label,
                 x + Inches(0.2), cy + Inches(0.2), card_w - Inches(0.4),
                 Inches(0.4), size=Pt(20), color=color, bold=True,
                 align=PP_ALIGN.CENTER))
        g.append(add_text(slide, defn,
                 x + Inches(0.2), cy + Inches(0.85), card_w - Inches(0.4),
                 Inches(1.4), size=Pt(13), color=WHITE, align=PP_ALIGN.CENTER))
        band_groups.append(g)

    why = []
    why.append(add_rect(slide, MX, CT + Inches(3.4), CW, Inches(2.0),
                        fill_color=NAVY3, border_color=GOLD,
                        border_width=Pt(1.5), corner_radius=True))
    why.append(add_text(slide,
        # audit:after_amosi_logic_fixes.md fix #6 - prior copy said
        # "P(correct) 0.62 -> 0.94 (32pp gap)" which was the conf>=0.65
        # bin. At top1_conf>=0.95 (the green-band threshold), the actual
        # P(correct) range is 0.40 -> 0.94 = 54pp. Source:
        # english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md Test C.
        "WHY ADD AGREEMENT?  Beam agreement is ~2x more informative than "
        "top-1 conf at high confidence. At conf >= 0.95, ranging "
        "beam_agreement from 0.40 -> 1.00 takes P(correct) from 0.40 -> "
        "0.94 (a 54pp gap). Single-axis conf misses the wide spread in "
        "this regime; the joint rule recovers it.",
        MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
        Inches(1.7), size=Pt(13), color=WHITE))

    bot = add_text(slide,
        "Llama-2-7b specific. Any LLM swap forces re-running "
        "diagnose_confidence_signals.py and re-fitting the cuts.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
        # replaced with reorder-robust phrasing.
        "Source: MEMORY auto memory (agreement_aware_bands entry) + "
        "docs/confidence/lessons_learned_band_rule_v2.md + "
        "docs/confidence/confidence_shape_and_beam_disagree_design.md. "
        "Joint rule shipped May 2 2026. Green = top1_conf>=0.95 AND "
        "agreement>=0.80; Yellow = >=0.65 AND >=0.50; numbers cap at "
        "yellow regardless. Beam agreement is roughly 2x more informative "
        "than top-1 conf at high conf - quantified below in this section. "
        "CAVEAT: thresholds are Llama-2-7b specific; an LLM swap forces "
        "re-running the diagnostic.",
        [[sub]] + band_groups + [why, [bot]], click_reveal=True)


def slide_agreement_vs_conf_information(prs):
    """Marginal info gain of beam agreement over top-1 conf."""
    slide = new_slide(prs)
    add_title(slide, "Beam Agreement Adds Independent Signal")
    add_accent_line(slide)

    sub = add_text(slide,
        "At top1_conf >= 0.95 the softmax says 'almost certain.' Beam "
        "agreement reveals which of those tokens were actually unique.",
        MX, CT, CW, Inches(0.5),
        size=Pt(13), color=LGRAY, italic=True)

    # audit:after_amosi_logic_fixes.md fix #6 - prior copy paired
    # "0.94 / 0.62" with "32pp gap" but those are the conf>=0.65 numbers.
    # At top1_conf>=0.95 (the green-band threshold), the spread is
    # 0.94 / 0.40 = 54pp. Source:
    # english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md Test C.
    headers = ["", "agreement >= 0.80", "agreement < 0.80"]
    rows = [
        ["P(correct)",   "0.94", "0.40"],
        ["green/yellow", "GREEN", "downgraded to yellow"],
    ]
    row_colors = {
        0: {1: GREEN, 2: CORAL},
        1: {1: GREEN, 2: ORANGE},
    }
    tbl = add_table(slide, headers, rows,
                    MX + Inches(1.0), CT + Inches(0.7), Inches(10.0),
                    row_height=Inches(0.7),
                    col_widths=[Inches(3.0), Inches(3.5), Inches(3.5)],
                    text_size=Pt(15), row_colors=row_colors)

    why = []
    why.append(add_text(slide, "WHY THIS MATTERS",
             MX, CT + Inches(2.5), CW, Inches(0.35),
             size=Pt(15), color=TEAL, bold=True))
    why.append(add_bullets(slide, [
        ("54 percentage-point P(correct) gap at the SAME top-1 confidence "
         "(0.40 vs 0.94)", {"bold": True}),
        ("Conf alone collapses two distinct populations into one green band - "
         "agreement separates them", {}),
        ("Marginal info gain: beam_agreement carries ~2x the AUC of "
         "top1_conf in the conf>=0.95 regime", {"color": TEAL}),
        ("Practical effect: the joint-rule green band drops from 11,309 -> "
         "7,591 words, but green P(correct) rises from 80.6% -> 89.8%",
         {"color": GREEN}),
    ], MX, CT + Inches(2.95), CW, Inches(2.5), size=Pt(13)))

    bot = add_text(slide,
        "Diagnostic script: diagnose_confidence_signals.py. "
        "Llama-2-7b specific - re-run on any LLM swap.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        # audit:after_amosi_logic_fixes.md fix #6 - corrected 32pp/0.62
        # to 54pp/0.40 to match TRUST_DIAGNOSTIC.md Test C numbers.
        "Source: MEMORY auto memory (agreement_aware_bands info gain) + "
        "docs/confidence/lessons_learned_band_rule_v2.md + "
        "english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md "
        "(Test C). Load-bearing finding: at top1_conf>=0.95, splitting on "
        "beam_agreement>=0.80 vs <0.80 gives a 54pp P(correct) gap "
        "(0.94 vs 0.40). Conf alone hides this gap inside green. Joint "
        "rule peels off the disagreed-but-confident tokens into yellow "
        "and tightens green from 80.6% to 89.8%. audit-md:section-D "
        "supplies overall green P(correct).",
        [[sub, tbl], why, [bot]], click_reveal=True)


def slide_client_trust_calibration(prs):
    """Trust gate operating points - ROC-style table."""
    slide = new_slide(prs)
    add_title(slide, "Trust-Gate Operating Points (per-segment)")
    add_accent_line(slide)

    sub = add_text(slide,
        "Per-segment trust gate based on fraction-of-green-words. n=1,427 "
        "(70 empty-output segments excluded; see audit anomaly note).",
        MX, CT, CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True)

    # All from audit Section E new_rule_joint_conf_agreement
    headers = ["Threshold", "n trusted", "Recall", "Precision", "FPR",
               "% clearly conveyed in trust"]
    rows = [
        # audit:trustgate_new_t10_*
        ["fraction-green >= 10%", "1,041", "92.3%", "81.9%", "37.4%", "34.3%"],
        # audit:trustgate_new_t20_*
        ["fraction-green >= 20%",   "818", "80.8%", "91.3%", "14.1%", "42.7%"],
        # audit:trustgate_new_t30_*
        ["fraction-green >= 30%  (default)", "630", "65.2%", "95.6%",  "5.6%", "52.5%"],
        # audit:trustgate_new_t50_*
        ["fraction-green >= 50%",   "321", "33.8%", "97.2%",  "1.8%", "72.0%"],
        # audit:trustgate_new_t70_*
        ["fraction-green >= 70%",    "71",  "7.6%", "98.6%",  "0.2%", "88.7%"],
    ]
    row_colors = {
        2: {0: BLUE, 1: BLUE, 2: GREEN, 3: GREEN, 4: GREEN, 5: GREEN},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.6), CW, row_height=Inches(0.5),
                    col_widths=[Inches(3.5), Inches(1.4), Inches(1.4),
                                Inches(1.7), Inches(1.4), Inches(2.7)],
                    text_size=Pt(12), row_colors=row_colors)

    pick = add_text(slide,
        "Recommended default: 30% green words -> 65.2% recall, 5.6% FPR. "
        "Pick higher thresholds for mission-critical workflows; lower for "
        "high-recall research workflows.",
        MX, CT + Inches(3.7), CW, Inches(0.7),
        size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    bot = add_text(slide,
        "Audit keys: trustgate_new_t{10,20,30,40,50,60,70,80,90}_*. "
        "Calibrated under joint conf+agreement rule.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section E "
        "(new_rule_joint_conf_agreement) + "
        "docs/confidence/client_trust_calibration.md. Operating-point "
        "ROC-style table on the per-segment trust gate. n=1,427 "
        "(per_segment_safety.csv, 70 empty-output segments excluded; "
        "see audit anomaly note about denominator difference between "
        "per-segment safety and full IS distribution). Recommended "
        "default at fraction-of-green >= 30%: 65.2% recall, 5.6% FPR. "
        "Audit JSON keys: trustgate_new_t30_recall, "
        "trustgate_new_t30_fpr, trustgate_new_t30_precision, "
        "trustgate_new_t30_pct_clearly_conveyed.",
        [[sub, tbl], [pick], [bot]], click_reveal=True)


def slide_nbest_v3_judge_paired_tests(prs):
    """N-best v3 judge paired-test results."""
    slide = new_slide(prs)
    add_title(slide, "N-best Aggregation: v3 Judge Paired Tests")
    add_accent_line(slide)

    sub = add_text(slide,
        "Opus 4.7 dual-conf prompt, blind, 5,988 verdicts (1,497 segments x "
        "4 methods). McNemar paired vs baseline (top-1).",
        MX, CT, CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True)

    img = add_image(slide, "P_v3_judge_paired",
                    MX, CT + Inches(0.6),
                    width=Inches(6.5), height=Inches(4.5))

    rx = MX + Inches(6.7)
    rw = CW - Inches(6.7)

    headers = ["Method", "Y%", "Y+P%", "YP McNemar p"]
    rows = [
        # audit:judge_v3_y_pct_baseline / _yp_pct_baseline
        ["baseline",       "13.09%", "68.40%", "-"],
        # audit:judge_v3_y_pct_mbr / _yp_pct_mbr / mcnemar_yp_p_mbr
        ["hyp_mbr",        "13.89%", "71.08%", "0.00017 ***"],
        # audit:judge_v3_y_pct_vote_score / _yp_pct_vote_score
        ["hyp_vote_score", "13.96%", "69.27%", "0.149 (n.s.)"],
        # audit:judge_v3_y_pct_vote_conf / _yp_pct_vote_conf / mcnemar_yp_p_vote_conf
        ["hyp_vote_conf",  "12.49%", "70.47%", "0.00257 **"],
    ]
    row_colors = {
        1: {2: GREEN, 3: GREEN},
        2: {2: GOLD,  3: LGRAY},
        3: {2: GREEN, 3: GREEN},
    }
    # audit:pptx_visual_audit_after_amosi.md slide 60 BLOCKER -
    # Table 5 extended past canvas (right=13.70 vs 13.33). Cols
    # 2.4+1.0+1.2+1.8=6.4" placed at rx=7.30" overflowed by 0.37".
    # Trimmed to <=5.4" so right edge stays inside CW.
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.6), rw,
                    text_size=Pt(11), row_height=Inches(0.5),
                    col_widths=[Inches(1.9), Inches(0.9), Inches(1.0),
                                Inches(1.6)],
                    row_colors=row_colors)

    take = add_bullets(slide, [
        ("Y verdict tied across all methods (no significant change)",
         {"color": LGRAY}),
        ("Y+P shifts: MBR +40 wins, p=0.00017",
         {"color": GREEN, "bold": True}),
        ("Y+P shifts: vote_conf +31 wins, p=0.00257",
         {"color": GREEN}),
        ("vote_score n.s. on Y+P (p=0.149)",
         {"color": LGRAY}),
        ("Identical-text drift v3: 12.6 / 10.4 / 14.2% per method "
         "(down from v1's 27%) - dual-conf prompt removed bias",
         {"color": TEAL}),
    ], rx, CT + Inches(3.0), rw, Inches(2.7), size=Pt(11))

    # audit:after_amosi_narrative_actions.md fix #8 - explicit run-label
    # footer so this v3 dual-conf judge run (Opus 4.7, 5,988 verdicts on
    # n-best methods) is not conflated with the v1 blind judge slide
    # earlier in the section (Opus 4.6, 1,497 pairs).
    bot = add_text(slide,
        "v3 dual-conf judge   /   Opus 4.7   /   5,988 verdicts on "
        "n-best methods   //   audit keys: judge_v3_*, "
        "mcnemar_yp_p_{mbr,vote_score,vote_conf}, section_F_llm_judge_v3.",
        MX, Inches(6.5), CW, Inches(0.4),
        size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section F + "
        "docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md. "
        "DISAMBIGUATION: this is the v3 DUAL-CONF judge run "
        "(Opus 4.7, 5,988 verdicts on the four n-best methods). The "
        "earlier slide_llm_judge in this section reports the v1 BLIND "
        "judge run (Opus 4.6, 1,497 pairs, baseline only). Different "
        "models, different prompts, different cohorts - do not pool. "
        "Headline (v3): hyp_mbr +40 Y+P wins (p=0.00017), hyp_vote_conf "
        "+31 Y+P wins (p=0.00257); both highly significant. vote_score "
        "not significant (p=0.149). Y verdict tied across all methods. "
        "Identical-text drift dropped from v1's 27% to 12.6-14.2% in v3 "
        "(audit:_note_drift) thanks to the dual-conf prompt anchor. "
        "5,988 total verdicts.",
        [[sub, img], [tbl, take], [bot]], click_reveal=True)


def slide_mbr_decision(prs):
    """Why MBR over voting (decision summary)."""
    slide = new_slide(prs)
    add_title(slide, "Why MBR Won the Default-Display Slot")
    add_accent_line(slide)

    sub = add_text(slide,
        "Two methods passed the v3 judge significance bar (MBR and "
        "vote_conf). MBR wins on intra-rater reliability and posterior "
        "compatibility.",
        MX, CT, CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True)

    headers = ["Criterion", "hyp_mbr", "hyp_vote_conf", "Winner"]
    rows = [
        # audit:mcnemar_yp_p_*
        ["Y+P paired McNemar p",   "0.00017",     "0.00257",      "tie  (both significant)"],
        # audit:mcnemar_yp_method_only_*
        ["Y+P win delta",          "+40",         "+31",          "MBR"],
        # audit:judge_v3_intrarater_exact_*
        ["Intra-rater (exact)",    "86.7%",       "80.0%",        "MBR  (matches gold std 83.3%)"],
        ["Per-word posterior",     "calibrated",  "agreement [0.4-0.8]", "MBR"],
        ["Compatible with bands",  "yes",         "narrow range",  "MBR"],
    ]
    row_colors = {
        2: {1: GREEN, 3: GREEN},
        3: {1: GREEN, 3: GREEN},
        4: {1: GREEN, 3: GREEN},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.6), CW, row_height=Inches(0.5),
                    col_widths=[Inches(3.5), Inches(2.5), Inches(3.0),
                                Inches(3.13)],
                    text_size=Pt(12), row_colors=row_colors)

    dec = []
    dec.append(add_rect(slide, MX, CT + Inches(3.6), CW, Inches(1.8),
                        fill_color=NAVY2, border_color=BLUE, border_width=Pt(2),
                        corner_radius=True))
    dec.append(add_text(slide, "DECISION - ship pure hyp_mbr as default displayed output",
             MX + Inches(0.3), CT + Inches(3.75), CW - Inches(0.6),
             Inches(0.4), size=Pt(15), color=BLUE, bold=True))
    # audit:pptx_visual_audit_after_amosi.md slide 61 BLOCKER -
    # TextBox 7 (bullets inside dec rect at 5.6-7.1) overlapped TextBox 8
    # (bot footer at 6.5-6.9) by 95%. Bullets shortened (height 1.3" so
    # they end at 6.9") and bot footer dropped - wiring detail moved into
    # the speaker notes since it's implementation, not stage content.
    dec.append(add_bullets(slide, [
        ("MBR mean per-word conf 0.867 (audit:section_D mbr per-word "
         "posterior - compatible with T_trust/T_safe/T_salvage cuts)",
         {"color": WHITE}),
        ("Vote methods emit agreement scores in [0.4, 0.8] - narrow range "
         "incompatible with the existing band thresholds", {"color": WHITE}),
        ("Hybrid gate considered & rejected: +36 vs +37 = one rescue, "
         "not worth a threshold", {"color": LGRAY, "italic": True}),
    ], MX + Inches(0.3), CT + Inches(4.15),
       CW - Inches(0.6), Inches(1.3), size=Pt(12)))

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section F "
        "intra_rater + MEMORY n_best_aggregation_findings entry + "
        "docs/beam-search/n_best_implementation.md. Both MBR and "
        "vote_conf pass the v3 judge significance bar (Y+P McNemar "
        "p=0.00017 and 0.00257). MBR wins on (a) higher intra-rater "
        "exact agreement (86.7% vs 80%, matches gold-standard top-1 "
        "83.3%) and (b) calibrated per-word posterior compatible with "
        "the band-reliability thresholds; voting methods emit agreement "
        "scores in [0.4, 0.8] that don't map to T_trust/T_safe/T_salvage. "
        "Hybrid gating considered and rejected (+36 vs +37 = one rescue). "
        "Default ship: pure hyp_mbr. Wired via make_report.py "
        "--display-method (default top1 for back-compat); lib/outputs.sh "
        "defaults to hyp_mbr when aggregated.json exists; override via "
        "VSP_DISPLAY_METHOD env.",
        [[sub, tbl], dec], click_reveal=True)


def slide_v1_vs_v3_judge_lesson(prs):
    """Dual-conf prompt design lesson."""
    slide = new_slide(prs)
    add_title(slide, "v1 vs v3 Judge: A Prompt-Design Lesson")
    add_accent_line(slide)

    sub = add_text(slide,
        "Same n-best methods. Same judge model. Different prompt. "
        "Opposite conclusions.",
        MX, CT, CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    cy = CT + Inches(0.6)
    ch = Inches(4.2)

    L = []
    L.append(add_rect(slide, MX, cy, card_w, ch, fill_color=NAVY2,
                     border_color=CORAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "v1 - conf-in-prompt (broken)",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(15), color=CORAL, bold=True))
    L.append(add_bullets(slide, [
        ("Method-conf only injected into prompt", {"bold": True}),
        ("Judge interpreted high method-conf as evidence of reliability "
         "WITHOUT the baseline anchor", {}),
        ("Y+P verdict: vote_conf significantly LOSES (p < 0.05)",
         {"color": CORAL}),
        ("Identical-text drift across re-runs: 27%", {"color": CORAL}),
        ("Bias direction: against the n-best variants",
         {"color": CORAL, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.5), size=Pt(12)))

    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, ch, fill_color=NAVY2,
                     border_color=GREEN, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "v3 - dual-conf prompt (current)",
             rx + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(15), color=GREEN, bold=True))
    R.append(add_bullets(slide, [
        ("Method-conf AND baseline_conf shown side-by-side", {"bold": True}),
        ("Judge anchors method confidence against baseline confidence "
         "instead of treating it as absolute", {}),
        ("Y+P verdict: vote_conf significantly WINS (p = 0.00257)",
         {"color": GREEN}),
        ("Identical-text drift: 12.6 / 10.4 / 14.2% per method  "
         "(audit:_note_drift)", {"color": GREEN}),
        ("Bias direction: balanced",
         {"color": GREEN, "bold": True}),
    ], rx + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.5), size=Pt(12)))

    lesson = []
    lesson.append(add_rect(slide, MX, Inches(6.0), CW, Inches(0.7),
                           fill_color=NAVY3, border_color=GOLD,
                           border_width=Pt(1.5), corner_radius=True))
    lesson.append(add_text(slide,
        "LESSON: when prompting an LLM judge to compare hypotheses, ALWAYS "
        "provide the baseline reference's confidence too. Single-sided "
        "conf injection biases the verdict.",
        MX + Inches(0.3), Inches(6.13), CW - Inches(0.6),
        Inches(0.55), size=Pt(13), color=GOLD, bold=True))

    _finish(slide, 0,
        "Source: docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md "
        "+ MEMORY n_best_aggregation_findings entry. v1 (single-side "
        "method-conf in prompt) systematically biased AGAINST the n-best "
        "variants - vote_conf significantly LOST on Y+P. v3 (dual-conf "
        "with baseline_conf anchor) flipped the verdict: vote_conf "
        "significantly WINS on Y+P (p=0.00257). Identical-text drift "
        "fell from 27% to 12.6-14.2% per method (audit:_note_drift). "
        "v1 is archived; v3 is the current gold standard. Transferable "
        "lesson: when prompting LLMs to compare hypotheses, always "
        "provide BOTH sides' confidence as anchors.",
        [[sub], L, R, lesson], click_reveal=True)


# ============================================================================
# DEMO SLIDES — research-flavored versions of the client examples (Task E)
# All five reuse the existing IMG video keys; speaker notes disclose decode
# artefact gaps (Obama clips fall back to conf-only, no VSP_NBEST=1).
# ============================================================================


def _demo_research_slide(prs, *, title, video_key, ref, hyp_runs,
                         metrics_line, badge_text, badge_color, body, notes):
    """Shared layout for the five research-flavored demo slides.

    Centered hero video + REF (label/text) + colour-coded HYP + metrics line +
    research observation body. Per-word band cited as observation, not pitch.
    """
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    badge_w = Inches(2.4)
    sub = add_text(slide, metrics_line,
             MX, Inches(1.5), CW - badge_w - Inches(0.2), Inches(0.4),
             size=Pt(12), color=LGRAY, italic=True)
    badge_x = MX + CW - badge_w
    badge_box = add_rect(slide, badge_x, Inches(1.5), badge_w, Inches(0.4),
             fill_color=NAVY3, border_color=badge_color, border_width=Pt(1.0))
    badge_t = add_text(slide, badge_text,
             badge_x, Inches(1.55), badge_w, Inches(0.3),
             size=Pt(13), bold=True, color=badge_color, align=PP_ALIGN.CENTER)

    vid_w = Inches(6.0)
    vid_h = Inches(3.4)
    vid_x = (SL_W - vid_w) // 2
    vid_y = Inches(2.05)
    # audit:pptx_visual_audit_after_amosi.md slides 64-68 BLOCKER -
    # Animation references shape id 7 (the embedded movie) which is wrapped
    # in <mc:AlternateContent> and therefore invisible to slide.shapes
    # iteration in the audit script (and to many OOXML consumers). The video
    # is left out of anim_groups so it just renders on entry without an
    # Appear timing entry; nothing else changes. Same root cause as the
    # slide_15 fix below.
    vid = add_video(slide, video_key, vid_x, vid_y, vid_w, vid_h)

    add_text(slide, "REFERENCE",
             MX, Inches(5.5), CW, Inches(0.25),
             size=Pt(10), bold=True, color=LGRAY)
    ref_t = add_text(slide, ref,
             MX, Inches(5.75), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    add_text(slide, "HYPOTHESIS  (per-word band observation)",
             MX, Inches(6.18), CW, Inches(0.25),
             size=Pt(10), bold=True, color=WHITE)
    hyp_t = add_rich_text(slide, [hyp_runs],
             MX, Inches(6.42), CW, Inches(0.5))

    body_t = add_text(slide, body,
             MX, Inches(6.95), CW, Inches(0.35),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0, notes,
            [[sub, badge_box, badge_t], [ref_t], [hyp_t], [body_t]],
            click_reveal=True)


def slide_demo_obama_trust(prs):
    """Obama segment 14 - clean speech, Trust tier."""
    runs = [
        ("[per-word colors load from the conf-only sidecar; ", {"size": Pt(12), "color": LGRAY}),
        ("VSP_NBEST=1 was not enabled at the April 30 decode]",
         {"size": Pt(12), "color": LGRAY, "italic": True}),
    ]
    _demo_research_slide(prs,
        title="Demo - Obama Trust Tier",
        video_key="obama_perfect",
        ref="(see speaker notes; Obama bin Laden announcement, segment #14, 41.95-45.55 s)",
        hyp_runs=runs,
        metrics_line="WER 0.0%   /   IS 5.00   /   sequence_conf high   "
                     "/   mean_prob ~ 0.93",
        badge_text="TIER: TRUST",
        badge_color=BLUE,
        body="Research observation: 27/29 per-word bands are GREEN; the joint "
             "rule keeps them green because beam_agreement is also high.",
        notes="Source: slides_client.py::slide_client_example_perfect "
              "(reframed for research). Obama bin Laden announcement, "
              "segment #14, 41.95-45.55 s. Clean speech, WER=0%, IS=5.0. "
              "Per-word colors render from the conf-only sidecar - this "
              "Obama decode predates VSP_NBEST=1 (April 30 2026), so the "
              "agreement-aware joint rule is not applied; per-word bands "
              "are conf-only. Re-running outputs.sh on a VSP_NBEST=1 "
              "decode would upgrade the painting to the joint rule. "
              "audit-md:band_reliability_by_niv puts NIV-Y green at 94%; "
              "this clean segment is well inside that population.")


def slide_demo_obama_salvage(prs):
    """Obama segment 31 - partial recovery (TRUST badge under conf-only)."""
    # audit:after_amosi_asset_fixes.md fix #9 - title previously claimed
    # "Salvage Tier (partial recovery)" but the rendered video shows the
    # TRUST badge: Obama seg 31 mean_prob = 0.920 which is above T_safe
    # (0.82), so the production tier is TRUST and not Salvage. The Obama
    # decode predates VSP_NBEST=1, so the joint conf+agreement rule is
    # not applied (no agreement sidecar) - the slide silently falls back
    # to conf-only band painting. Title now discloses the badge mismatch
    # and the metrics_line reports the correct mean_prob.
    runs = [
        ("[per-word colors load from the conf-only sidecar; ", {"size": Pt(12), "color": LGRAY}),
        ("'said' substitution is the visible orange word]",
         {"size": Pt(12), "color": LGRAY, "italic": True}),
    ]
    _demo_research_slide(prs,
        title="Demo - Obama: TRUST under conf-only fallback "
              "(no n-best sidecar - partial recovery still narrated)",
        video_key="obama_partial",
        ref="(see speaker notes; Obama bin Laden announcement, segment #31, 92.90-96.50 s)",
        hyp_runs=runs,
        metrics_line="WER ~ 22%   /   IS ~ 3.5   /   sequence_conf mixed   "
                     "/   mean_prob = 0.920  (TRUST under T_safe=0.82)",
        badge_text="TIER: TRUST",
        badge_color=BLUE,
        body="Research observation: most words green; the substitution "
             "'president bush did' -> 'said' renders in orange under the "
             "conf-only rule. The TRUST badge (mean_prob>=0.82) reflects "
             "the conf-only fallback because this Obama decode predates "
             "VSP_NBEST=1; the joint rule would likely demote the segment.",
        notes="Source: slides_client.py::slide_client_example_partial "
              "(reframed for research). Obama bin Laden announcement, "
              "segment #31, 92.90-96.50 s. WER ~22%, mean_prob=0.920 - "
              "ABOVE T_safe (0.82), so the production tier under conf-only "
              "is TRUST not Salvage. The original slide title called this "
              "'Salvage' for narrative continuity but the badge mismatch "
              "is real: the Obama decode predates VSP_NBEST=1 (April 30 "
              "2026) so no agreement sidecar exists; the per-word band "
              "rule silently falls back to conf-only. Re-running outputs.sh "
              "on a VSP_NBEST=1 decode would likely push this segment to "
              "Salvage under the joint rule (the substituted 'said' "
              "almost certainly has low beam_agreement). Reviewer still "
              "triages from the orange word; the slide demonstrates the "
              "narrative-vs-production-tier gap that the joint rule "
              "closes. audit:section_D_per_word_conf.by_tier.Salvage.new "
              "supplies the per-tier reliability for the joint-rule "
              "Salvage band.")


def slide_demo_obama_strip(prs):
    """Obama segment 5 - hallucination caught (closest-to-Strip in the Obama set).

    NOTE: Per render-log finding, obama_flagged actually shows the INSPECT
    badge (not STRIP) because its mean_prob is 0.799 - above the 0.65
    strip-coloring boundary. Reframed accordingly.
    """
    runs = [
        ("[per-word colors load from the conf-only sidecar; ", {"size": Pt(12), "color": LGRAY}),
        ("min word probability 0.02 - the model 'knew' the fabrication]",
         {"size": Pt(12), "color": LGRAY, "italic": True}),
    ]
    # audit:after_amosi_narrative_actions.md fix #13 - first INSPECT
    # mention; gloss it inline so the audience knows it is the
    # production label for what the research literature calls 'Salvage'.
    _demo_research_slide(prs,
        title="Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)",
        video_key="obama_flagged",
        ref="heroic citizens saved even more heartbreak and destruction",
        hyp_runs=runs,
        metrics_line="WER ~ 45%   /   IS ~ 1.5   /   sequence_conf low   "
                     "/   mean_prob = 0.799  (just inside Salvage)",
        badge_text="TIER: INSPECT",
        badge_color=PURPLE,
        body="Research observation: the model fabricated 'rwanda's "
             "genocide' but the per-token softmax bottomed out at 0.02 "
             "- the system flagged the segment before the reviewer "
             "ever saw it.   "
             "(INSPECT badge = production label for the 'Salvage' tier "
             "used elsewhere in this section.)",
        notes="Source: slides_client.py::slide_client_example_flagged "
              "(reframed for research). Obama bin Laden announcement, "
              "segment #5, 14.98-18.58 s. REF: 'heroic citizens saved "
              "even more heartbreak and destruction'. HYP: 'rwanda's "
              "genocide even more heartbreaking is russia'. The original "
              "client framing called this 'STRIP' but mean_prob=0.799 "
              "puts it in the Salvage band (above the 0.65 strip-coloring "
              "boundary), so the production badge is INSPECT - the "
              "closest-to-STRIP example available in the Obama set. "
              "The min per-word probability (0.02) is the headline: "
              "the LLM was uncertain about the fabricated tokens even "
              "while emitting them fluently. Per-word colours render "
              "from the conf-only sidecar (Obama decode predates "
              "VSP_NBEST=1). audit-md:band_reliability_by_niv shows "
              "NIV-N green words are only 37% reliable - confirms why "
              "the Strip tier (mean_prob<0.65) drops colours entirely.")


def slide_demo_judge_entity(prs):
    """Judge entity slide - now shows STRIP badge for rogers / PV / will (research).

    Per render-log finding, judge_entity now shows STRIP badge under joint
    rule (rogers / pv / will all flagged red).
    """
    runs = [
        ("market ",       {"size": Pt(12), "color": BLUE}),
        ("research ",     {"size": Pt(12), "color": BLUE}),
        ("firm ",         {"size": Pt(12), "color": BLUE}),
        ("rogers ",       {"size": Pt(12), "color": PURPLE, "bold": True}),
        ("research ",     {"size": Pt(12), "color": BLUE}),
        ("is ",           {"size": Pt(12), "color": BLUE}),
        ("forecasting ",  {"size": Pt(12), "color": BLUE}),
        ("pv ",           {"size": Pt(12), "color": PURPLE, "bold": True}),
        ("installations ",{"size": Pt(12), "color": BLUE}),
        ("will ",         {"size": Pt(12), "color": PURPLE, "bold": True}),
        ("reach",         {"size": Pt(12), "color": BLUE}),
    ]
    # audit:after_amosi_asset_fixes.md fix #10 - mean_prob updated from
    # ~0.71 to 0.624 to match
    # english_full_nbest_eval/report_v2/report.csv (segment
    # 4D634qUi2BI_0__93a9f2b4_00_000000_000122, sentence_confidence=0.624,
    # is_label=Strip). Also fix #11 - explicit VSP_NBEST=1 disclosure
    # added (slide pulls per-word colours from the agreement-aware
    # sidecar, unlike the Obama slides).
    _demo_research_slide(prs,
        title="Demo - Strip: entity swap auto-flagged",
        video_key="judge_entity",
        ref="market research firm bernreuter research is forecasting "
            "pv installations could reach",
        hyp_runs=runs,
        metrics_line="WER 18.2%   /   IS 4.55   /   sequence_conf mixed   "
                     "/   mean_prob = 0.624  (Strip; full agreement-aware "
                     "rule applied, VSP_NBEST=1)",
        badge_text="TIER: STRIP",
        badge_color=PURPLE,
        body="Research observation: the entity-swap tokens 'rogers', "
             "'pv', 'will' are auto-flagged red under the joint rule. "
             "Strengthens the entity-swap narrative.",
        notes="Source: slides_client.py::slide_client_judge_ex1 (reframed "
              "for research). bernreuter -> rogers entity swap; PV / "
              "will also flagged red under the joint conf+agreement rule "
              "(per render-log inspection). WER 18.2%, IS 4.55 (Excellent), "
              "LLM judge Y. mean_prob = 0.624 per "
              "english_full_nbest_eval/report_v2/report.csv "
              "(prior copy said ~0.71, corrected per "
              "after_amosi_asset_fixes.md fix #10). The badge is STRIP "
              "not TRUST because the joint rule pushes the entity-swap "
              "tokens to red (per-word agreement low even though top-1 "
              "conf may be high). DECODE MODE: this clip was decoded "
              "with VSP_NBEST=1 so the agreement-aware sidecar is "
              "present and the full joint rule (top1_conf>=0.95 AND "
              "beam_agreement>=0.80) is applied (unlike the Obama clips "
              "earlier in this section, which fall back to conf-only "
              "band painting). audit:judge_v3_y_count_baseline picks "
              "this segment up; the per-word band overlay separates "
              "the firm-name swap from the rest.")


def slide_demo_judge_vocab(prs):
    """Judge router slide - technical-vocab drift (research framing)."""
    runs = [
        ("we ",         {"size": Pt(12), "color": BLUE}),
        ("need ",       {"size": Pt(12), "color": BLUE}),
        ("a ",          {"size": Pt(12), "color": BLUE}),
        ("radically ",  {"size": Pt(12), "color": BLUE}),
        ("different ",  {"size": Pt(12), "color": BLUE}),
        ("approach ",   {"size": Pt(12), "color": BLUE}),
        ("we ",         {"size": Pt(12), "color": BLUE}),
        ("must ",       {"size": Pt(12), "color": ORANGE}),
        ("indeed ",     {"size": Pt(12), "color": ORANGE}),
        ("find ",       {"size": Pt(12), "color": BLUE}),
        ("a ",          {"size": Pt(12), "color": BLUE}),
        ("way ",        {"size": Pt(12), "color": BLUE}),
        ("we ",         {"size": Pt(12), "color": BLUE}),
        ("can ",        {"size": Pt(12), "color": BLUE}),
        ("design ",     {"size": Pt(12), "color": PURPLE}),
        ("existing ",   {"size": Pt(12), "color": BLUE}),
        ("roads ",      {"size": Pt(12), "color": PURPLE, "bold": True}),
        ("...",         {"size": Pt(12), "color": LGRAY}),
    ]
    # audit:after_amosi_asset_fixes.md fix #11 - explicit VSP_NBEST=1
    # disclosure added so the audience knows the per-word reds came from
    # the full joint conf+agreement rule (not the conf-only fallback
    # used by the Obama clips earlier in this section).
    _demo_research_slide(prs,
        title="Demo - Salvage: technical vocabulary drift",
        video_key="judge_router",
        ref="we need a radically different approach we basically need "
            "to find a way how we can take existing routers existing "
            "switches existing links and enable them for research",
        hyp_runs=runs,
        metrics_line="WER 51.5%   /   IS 3.02   /   sequence_conf mixed   "
                     "/   mean_prob ~ 0.78  (Salvage; full agreement-aware "
                     "rule applied, VSP_NBEST=1)",
        badge_text="TIER: SALVAGE",
        badge_color=ORANGE,
        body="Research observation: argument structure preserved (green "
             "spine). Domain terms 'routers / switches / links' drift "
             "to 'roads / structures / reuse' - per-word reds isolate "
             "the swaps; reviewer can patch the vocab.",
        notes="Source: slides_client.py::slide_client_judge_ex6 "
              "(spirit) + slides_evaluation.py::slide_judge_ex3 (data). "
              "Networking research segment where the model preserved the "
              "argument structure but swapped domain vocabulary "
              "(routers->roads, switches->structures, links->reuse). "
              "WER 51.5%, IS 3.02 (Good), LLM judge P. DECODE MODE: "
              "this clip was decoded with VSP_NBEST=1 so the "
              "agreement-aware sidecar is present and the full joint "
              "rule (top1_conf>=0.95 AND beam_agreement>=0.80) is "
              "applied (unlike the Obama clips earlier in this section, "
              "which fall back to conf-only band painting). Per-word "
              "colours show the green argument spine and the red "
              "domain-vocab swaps. Demonstrates: per-word band isolates "
              "the exact tokens that need a domain-aware re-decode pass. "
              "audit:section_D_per_word_conf.by_tier.Salvage.new "
              "supplies the per-tier reliability for this band overlay.")
