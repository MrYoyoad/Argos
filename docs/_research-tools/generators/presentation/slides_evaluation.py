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
    slide = new_slide(prs)
    add_title(slide, "Demo: OK \u2192 Almost There \u2192 Hallucination")
    add_accent_line(slide)

    # Three embedded videos side by side — click each to play
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

    for i, (key, desc, wer, color) in enumerate(vids):
        x = start_x + i * (vid_w + gap)
        add_video(slide, key, x, vid_y, vid_w, vid_h)
        add_text(slide, wer, x, vid_y + vid_h + Inches(0.05), vid_w,
                 Inches(0.3), size=Pt(14), color=color, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide, desc, x, vid_y + vid_h + Inches(0.35), vid_w,
                 Inches(0.6), size=Pt(11), color=LGRAY,
                 align=PP_ALIGN.CENTER)

    add_text(slide, "Click each video to play.",
             MX, Inches(6.6), CW, Inches(0.3),
             size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 15,
        "Three demos side by side. Left: 'consumers want a bigger smartphone' "
        "becomes 'consumers will not upgrade their smartphone' (IS 4.1 — "
        "meaning is close but the key verb is flipped: 'want' to 'will not'. "
        "This is what good output looks like — mostly right, small errors). "
        "Center: 'james and will talk about street photography' becomes "
        "'i'm here to talk about street photography' (IS 2.9 — "
        "the topic is captured perfectly but speaker names are lost. "
        "This is the near-miss zone). "
        "Right: 'carry strap' becomes 'holocaust denier' (hallucination, "
        "IS 0.8 — fluent but completely fabricated). Click each video to play.")

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
        ["Agreement (IS ≥ 3.0)", "88.6%"],
        ["Recall (IS ≥ 3.0)", "97.6–100%"],
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
        "Cross-config validation: r=0.925, 88.6% agreement, κ=0.773, "
        "recall 97.6-100% across 16 decode configs.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_25(prs):
    slide = new_slide(prs)
    add_title(slide, "IS: A Conservative Lower Bound")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(4.6), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric — the lower bound
    add_text(slide, "IS says 40.1%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments pass (IS \u2265 3.0)",
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
         "than 40.1% suggests", {"bold": True, "color": WHITE}),
        "LLM-as-a-Judge (blind, 1,497 pairs) confirms: nearly 2 in 3 "
         "segments carry useful meaning",
        ("The gap (40.1% \u2192 64.9%) = segments with partial value "
         "that strict metrics penalize", {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(1.8), size=Pt(14))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "An independent LLM judge confirms the true useful rate is 25pp higher.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "IS provides a conservative lower bound for transcription quality. "
        "IS says 40.1% of segments are captured (IS >= 3.0). But an independent "
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
        "165 segments that metrics call \u201cfailed\u201d (IS < 3.0) actually deliver "
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

    _finish(slide, "25b",
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
        ["Agreement (IS \u2265 3.0)", "88.6%"],
        ["Cohen\u2019s \u03ba", "0.773 (substantial)"],
        ["Recall", "99.2%"],
        ["Cross-config stability", "r = 0.925 \u00b1 0.015"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.5), col_w,
                    row_height=Inches(0.4),
                    col_widths=[Inches(2.8), Inches(2.7)],
                    text_size=Pt(12))

    rb = add_bullets(slide, [
        "Stable across all 16 decode configurations",
        "Catches 99.2% of IS \u2265 3.0 segments",
        ("Zero cost: pure Python, no LLM calls at runtime", {"bold": True}),
    ], rx, CT + Inches(3.1), col_w, Inches(1.5), size=Pt(13))

    # Bottom
    add_text(slide,
        "The decision tree was designed at development time, then distilled "
        "into deterministic Python. No LLM is called during evaluation.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "25c",
        "How the salvage detection works: a 15-rule deterministic decision tree "
        "that checks 6 linguistic signals and outputs a recovery probability. "
        "Validated at r=0.934 with IS, 88.6% agreement, stable across 16 configs.",
        [[lt] + step_shapes, [rt, tbl, rb]])

def slide_25d(prs):
    """Three real salvage examples showing HOW recovery works."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Three Real Recoveries")
    add_accent_line(slide)

    add_text(slide,
        "These segments failed IS (< 3.0) but a viewer with context would understand them:",
        MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY, italic=True)

    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(4.6)
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

        # Title + badge
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  WER {ex["wer"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.4), cw_card - Inches(0.3), Inches(0.25),
                 size=Pt(9), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.7),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.88), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.5),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.68), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.35),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(2.55), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(9.5), color=WHITE)

    _finish(slide, "25d",
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

    # Three cards side by side (same layout as slide_25d)
    cw_card = Inches(3.8)
    ch_card = Inches(4.6)
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

        # Title + badge
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  WER {ex["wer"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.4), cw_card - Inches(0.3), Inches(0.25),
                 size=Pt(9), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.7),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.88), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.5),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.68), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a wise viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.35),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(2.55), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(9.5), color=WHITE)

    _finish(slide, "25e",
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
    """14b: 2×3 clickable video grid — each video demonstrates a different system behavior."""
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    add_text(slide, "Click any thumbnail to play — each video demonstrates a different system behavior:",
             MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY)

    # Grid layout: 3 cols × 2 rows
    vid_w  = Inches(3.82)
    vid_h  = Inches(2.15)   # 16:9
    gap_x  = Inches(0.23)
    gap_y  = Inches(0.65)   # space for descriptive label below each video
    row_y  = [CT + Inches(0.45), CT + Inches(0.45) + vid_h + gap_y]
    start_x = MX

    # 6 videos — balanced: 3 positive high-IS examples + 3 failure modes
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
         ("doxology",     "Doxology \u2192 fabricated story — total hallucination",
          "172%", RED)],
    ]

    for r, row in enumerate(rows):
        for c, (key, label, wer, color) in enumerate(row):
            x = start_x + c * (vid_w + gap_x)
            y = row_y[r]
            add_video(slide, key, x, y, vid_w, vid_h)
            # Descriptive caption + WER badge
            add_text(slide, f"{label}  (WER {wer})",
                     x, y + vid_h + Inches(0.04), vid_w, Inches(0.40),
                     size=Pt(9), color=color, bold=False,
                     align=PP_ALIGN.CENTER)

    _finish(slide, "14b",
        "Balanced video gallery: 3 positive + 3 failure modes. "
        "Row 1 (positive): (1) Convention — person describes selling books at a "
        "convention, meaning fully captured with minor word drops. (2) Marilyn "
        "Monroe — proper noun preserved, wallpaper context intact. (3) Music — "
        "gist of playing a song preserved, phrasing changed. "
        "Row 2 (failure modes): (4) Spelling-to-smelling — phonetic confusion "
        "swaps the entire domain from literacy to odors. (5) Admiral McRae — "
        "classic viseme swap, identical lip shapes produce wrong words. "
        "(6) Doxology — total hallucination, model fabricates an unrelated story.")


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
        ("PCA reveals 2 dimensions: signal quality "
         "(68.4%, all 5 content signals) and output "
         "length (19.5%, Length Ratio)", {}),
        ("Cross-config validation confirms stability: "
         "mean r = 0.925 across 16 configurations",
         {"bold": True, "color": TEAL}),
        ("All 5 content signals load equally on PC1 "
         "(0.43\u20130.47) \u2014 one general quality factor "
         "driven by visual encoder", {}),
        ("Semantic gets higher weight (25%) because it "
         "captures paraphrasing that word metrics miss", {}),
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
         "Function words wrong, content words right",
         "\"the team discussed a quarterly\" \u2192 \"team discuss quarterly\"\n"
         "WER 43% but WWER 15% — viewer gets the message.\n"
         "IS captures this: meaning preserved despite surface errors."),
        ("NEA high, WER high", GREEN,
         "Names preserved despite overall poor accuracy",
         "\"Dr. Chen presented the Q3 results\" \u2192 \"Dr. Chen present Q3 result\"\n"
         "WER 57% but NEA F1 = 100% — critical info intact.\n"
         "IS rewards: the most important facts came through."),
        ("Semantic high, WER high", GOLD,
         "Meaning preserved through paraphrasing",
         "\"we need to reduce spending\" \u2192 \"must cut the budget\"\n"
         "WER 100% but Semantic 0.87 — same meaning, different words.\n"
         "IS captures: WER says total failure, IS says useful output."),
        ("Phonetic high, Semantic low", CORAL,
         "Sounds right, wrong meaning (deceptive)",
         "\"the alliance was formed\" \u2192 \"the lions were found\"\n"
         "Phonetic 0.71 but Semantic 0.12 — sounds similar, wrong topic.\n"
         "IS catches: phonetic alone would miss this dangerous error."),
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
        "This is why IS uses 6 signals, not just WER — each disagreement pattern "
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

    # Hide slide
    slide._element.set('show', '0')


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
    r1_t = add_text(slide, "Intelligibility Score (IS) \u2014 NIV Thresholds", MX + Inches(0.2),
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
        "\u03ba = 0.818 (almost perfect agreement)\n"
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
        'WER: 12% \u2022 IS: 3.84 \u2022 NIV Y \u2714 \u2022 Opus: Y\n\n'
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.94 \u2022 NIV Y+P \u2714 \u2022 Opus: P\n'
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

    # Right — IS correlation + takeaway
    rx = MX + col_w + gap
    rt = add_text(slide, "Correlation with Our Metric", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    r_big = add_text(slide, "85% correlation", rx, CT + Inches(0.6), col_w, Inches(0.7),
             size=Pt(36), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    r_label = add_text(slide, "with our Intelligibility Score",
             rx, CT + Inches(1.2), col_w, Inches(0.3),
             size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER)

    # Plain-language takeaway box
    tk_box = add_rect(slide, rx, CT + Inches(2.0), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    tk_txt = add_text(slide,
        "Systems agree on extremes \u2014 perfect segments\n"
        "always Y, failed always N.\n\n"
        "Borderline cases (Fair tier) are where\n"
        "judgment differs.",
        rx + Inches(0.2), CT + Inches(2.1), col_w - Inches(0.4), Inches(1.6),
        size=Pt(14), color=WHITE)

    # Key takeaway
    takeaway = add_text(slide,
        "LLM judge is more conservative for full success (23% vs IS 40%) "
        "but more generous for any useful output (Y+P=65%). "
        "IS is a conservative lower bound for real quality.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Animation groups — logical narrative order:
    # 1. Setup: what is LLM-as-a-Judge?
    # 2. Results: Y/P/N percentages
    # 3. Correlation + takeaway insight
    # 4. Bottom-line takeaway
    _finish(slide, 0,
        "LLM-as-a-Judge gold standard. Claude Opus evaluated all 1,497 pairs "
        "blind. Y=23.0% (345), P=41.8% (626), N=35.1% (526). Y+P=64.9%. "
        "Intra-rater 86.7%. Pearson r=0.85 with IS. "
        "Threshold sweep: Y+P peaks at IS>=2.0 (kappa=0.818, 91.5% agreement), "
        "not IS>=3.0 (kappa=0.521). IS tier cross-tab: Excellent tier 57% Y, "
        "Failed tier 81% N, Fair tier is the split point (8% Y, 51% P, 41% N). "
        "Full cross-tab in appendix slide A16.",
        [[lt, lb],
         [res_t, tbl],
         [rt, r_big, r_label, tk_box, tk_txt],
         [takeaway]],
        click_reveal=True)


def slide_context_eval(prs):
    """Context-aware re-evaluation results."""
    slide = new_slide(prs)
    add_title(slide, "Context Makes the Judge Stricter, Not Lenient")
    add_accent_line(slide)

    # Headline stat — centered, full width
    hl = add_text(slide,
        "Y+P (useful output): 64.9% \u2192 62.1%  (\u22122.7pp when judge knows the topic)",
        MX, CT, CW, Inches(0.4),
        size=Pt(18), color=CORAL, bold=True, align=PP_ALIGN.CENTER)

    # Transition matrix — centered, the star of the slide
    tbl_w = Inches(7.0)
    tbl_x = int((SL_W - tbl_w) / 2)
    rt = add_text(slide, "Transition Matrix (1,497 pairs)",
                  tbl_x, CT + Inches(0.7), tbl_w, Inches(0.35),
                  size=Pt(16), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["", "Ctx Y", "Ctx P", "Ctx N"],
        [["Blind Y (345)", "207", "138", "0"],
         ["Blind P (626)", "17", "519", "90"],
         ["Blind N (526)", "1", "48", "477"]],
        tbl_x, CT + Inches(1.15), tbl_w, text_size=Pt(14),
        col_widths=[Inches(2.0), Inches(1.67), Inches(1.67), Inches(1.67)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Key findings — below matrix, full width
    kf_b = add_bullets(slide, [
        ("230 downgrades vs 68 upgrades \u2014 context is 3.4\u00d7 more likely to penalize",
         {"color": CORAL, "bold": True}),
        "Y\u2192P is the dominant transition (138 cases): judge realizes domain vocabulary was wrong",
        ("Only 1 N\u2192Y rescue across all 1,497 pairs \u2014 context almost never saves a failure",
         {"bold": True}),
    ], MX, CT + Inches(3.2), CW, Inches(1.8), size=Pt(14), spacing=Pt(10))

    # Bottom
    add_text(slide,
        "Domain knowledge reveals vocabulary failures that surface-level evaluation misses.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware re-evaluation. When the judge knows the topic, Y drops "
        "from 23% to 15% (-8pp). Y+P drops from 64.9% to 62.1%. Context is "
        "STRICTER, not lenient. 230 downgrades vs 68 upgrades. Dominant "
        "transition: Y to P (138 cases) — the judge realizes domain vocabulary "
        "was wrong. Only 1 N-to-Y rescue across all 1,497 pairs.\n\n"
        "FULL COMPARISON (for reference):\n"
        "Y: 23.0% (345) -> 15.0% (225), delta -8.0pp\n"
        "P: 41.8% (626) -> 47.1% (705), delta +5.3pp\n"
        "N: 35.1% (526) -> 37.9% (567), delta +2.8pp\n"
        "Y+P: 64.9% (971) -> 62.1% (930), delta -2.7pp\n"
        "Cross-condition agreement: 80.0%",
        [[hl], [rt, tbl2], [kf_b]], click_reveal=True)


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
        ("Same hidden_size (4096) = drop-in swap", {"color": GREEN}),
        ("Setup: 1\u20132 hours", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(3.0), col_w - Inches(0.4), Inches(1.2),
       size=Pt(12), bullet_color=GREEN)

    _finish(slide, 0,
        "The LLM is a context engine. The visual encoder sees mouth shapes but "
        "can't distinguish visemes. The LLM resolves ambiguity using language "
        "context. A stronger LLM means better disambiguation. Llama 3.1 8B "
        "has quality equivalent to LLaMA-2 70B with the same hidden dimension "
        "(4096), making it a trivial 1-2 hour swap.",
        [[lt, lb], [rt, r1, r2]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE — LLM JUDGE 30-SAMPLE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

def slide_llm_judge_30(prs):
    """30-sample LLM-as-a-Judge overview — summary stats + what the sample shows."""
    slide = new_slide(prs)
    add_title(slide, "LLM Judge: 30-Sample Deep Dive")
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
        "IS spans 0.00 (empty output) to 5.00 (perfect match)",
        ("Middle zone (IS 2\u20134) is where the interesting "
         "cases live \u2014 partial captures, phonetic bridges, "
         "domain confusion", {}),
        ("6 videos on the next slides walk through these "
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
        "The next 6 slides show one video each, spanning IS 4.55 down to 1.79.",
        [[lt, tbl], [rt, rb, bk]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDES — 6 LLM JUDGE VIDEO EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def _judge_video_slide(prs, *, vid_key, title, ref, hyp, wer, wwer, is_score,
                       is_tier, judge, category, annotation, notes):
    """Reusable builder: single video left, ref/hyp/metrics right."""
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

    # Metrics row
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
