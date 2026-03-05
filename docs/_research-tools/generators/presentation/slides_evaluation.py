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
        "IS: 2.60 vs 2.52 baseline (+0.08)",
        ("Captured: 622 vs 597 (+25 segments)", {"color": GREEN}),
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
        ["Hallucinated", "carry strap", "holocaust denier", "100%", "0.7"],
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
    add_title(slide, "Demo: OK → Near-miss → Hallucination")
    add_accent_line(slide)

    # Three embedded videos side by side — click each to play
    # VID dict mapping (confirmed correct):
    #   "ok_demo"   -> 8SMYkCQkT4Q_0  (sheetaro -> just hara, gist right)
    #   "nearmiss"  -> -WQZsfHcPDM_7  (probiotics -> permafrost)
    #   "halluc"    -> 00MUdHQ7GGY_8  (carry strap -> holocaust denier)
    vid_w = Inches(3.6)
    vid_h = Inches(2.7)
    gap = Inches(0.4)
    total = 3 * vid_w + 2 * gap
    start_x = (SL_W - total) / 2
    vid_y = CT + Inches(0.1)

    vids = [
        ("ok_demo", '"sheetaro" \u2192 "just hara"\nGist right, names garbled', "WER 33%  IS 3.8", TEAL),
        ("nearmiss", '"probiotics" \u2192 "permafrost"\nStructure right, key terms garbled', "WER 58%  IS 2.7", YELLOW),
        ("halluc", '"carry strap" \u2192 "holocaust denier"', "WER 100%  IS 0.1", RED),
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
        "Three demos side by side. Left: 'sheetaro' becomes 'just hara' "
        "(IS 3.8 — gist right but names garbled, OK quality). Center: "
        "'probiotics' becomes 'permafrost' (near-miss, IS 2.7 — sentence "
        "structure preserved but key terms phonetically garbled). "
        "Right: 'carry strap' becomes 'holocaust denier' (hallucination, "
        "IS 0.1). Click each video to play.")

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
    rt = add_text(slide, "Correlation Analysis (PCA)", rx, CT, col_w,
                  Inches(0.35), size=Pt(17), color=CORAL, bold=True)

    # Three dimensions
    dims = [
        ("Word Accuracy", "WER + WWER + Phonetic (r > 0.79)", "~60% of IS", TEAL),
        ("Meaning Preservation", "Semantic similarity", "28.5%", GREEN),
        ("Output Sanity", "Length ratio", "9.1%", LGRAY),
    ]
    dim_y = CT + Inches(0.5)
    for i, (name, signals, pct, color) in enumerate(dims):
        y = dim_y + i * Inches(0.75)
        add_text(slide, name, rx, y, col_w, Inches(0.3),
                 size=Pt(14), color=color, bold=True)
        add_text(slide, f"{signals} — {pct} of variance",
                 rx + Inches(0.15), y + Inches(0.3), col_w - Inches(0.15),
                 Inches(0.3), size=Pt(11), color=LGRAY)

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
        "KEY CORRELATION FINDINGS:\n"
        "1. Phonetic Sim is the strongest single predictor (r=0.943) despite "
        "15% weight — it's the most direct measure of visual encoder quality.\n"
        "2. The 6 signals collapse into 3 dimensions: word accuracy "
        "(WER/WWER/Phonetic, ~60%), meaning (Semantic, 28.5%), output sanity "
        "(Length, 9.1%). Four of six signals measure the same thing.\n"
        "3. Semantic Sim (25% weight) drives the most IS variance (28.5%) — "
        "it's the tiebreaker that separates segments with similar word accuracy.\n"
        "4. NEA F1 punches above its weight: 17.3% variance from 15% weight. "
        "Names/numbers are binary — either preserved or not.\n"
        "5. WER is UNRELIABLE across configs — correlation with IS swings from "
        "-0.95 to -0.45 depending on length penalty. This is why IS was created.\n"
        "6. Length Ratio is nearly useless (9.1%, sign flips). Future versions "
        "could reduce its weight.\n\n"
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
    add_title(slide, "LLM Salvage: 1 in 2 Segments Delivers Value")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(4.6), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # Big number
    add_text(slide, "50.9%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.9),
             size=Pt(64), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "effective capture rate",
             MX + Inches(0.3), CT + Inches(1.1),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(18), color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "vs 39.9% from metrics alone (+11pp)",
             MX + Inches(0.3), CT + Inches(1.55),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Key bullets below the big number
    bul = add_bullets(slide, [
        "165 recoverable from 900 metric-failures (18.3% recovery rate)",
        "58% of salvageable segments have moderate WER (50\u201370%)",
        ("Deterministic 15-rule decision tree \u2014 no LLM calls at runtime (r=0.934 with IS)",
         {"color": TEAL}),
        ("LLM Judge confirms: Y+P = 64.9% (5.7\u00d7 WER's 11.4%)",
         {"color": GREEN, "bold": True}),
    ], MX + Inches(0.3), CT + Inches(2.2), CW - Inches(0.6),
       Inches(2.0), size=Pt(14))

    # Bottom text
    add_text(slide,
             "System delivers useful output for 1 in 2 segments \u2014 "
             "not 2 in 5 as raw metrics suggest.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "LLM Salvage Analysis: 165 of 900 metric-failed segments (IS < 3.0) "
        "are recoverable \u2014 meaning a domain-aware viewer would understand them. "
        "This raises effective capture from 39.9% to 50.9% (+11pp). The recovery "
        "is identified by a deterministic 15-rule decision tree that correlates "
        "at r=0.934 with IS.\n\n"
        "Four levels of measurement: WER says 11.4% usable. IS says 39.9%. "
        "LLM salvage says 50.9%. And the LLM Judge gold standard confirms: "
        "Y+P = 64.9% \u2014 5.7x WER's assessment.",
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
    cat_shapes = []
    for name, count, color, desc in categories:
        r = add_rect(slide, MX, py, CW, Inches(0.7), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        cat_shapes.append(r)
        add_text(slide, f"{name} ({count})",
                 MX + Inches(0.2), py + Inches(0.05), Inches(3.0), Inches(0.3),
                 size=Pt(13), color=color, bold=True)
        add_text(slide, desc,
                 MX + Inches(3.3), py + Inches(0.08), Inches(8.5), Inches(0.55),
                 size=Pt(11), color=LGRAY)
        py += Inches(0.78)

    add_text(slide,
        "Categories overlap \u2014 a segment can exhibit multiple recovery signals.",
        MX, Inches(6.45), CW, Inches(0.35),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "25b",
        "6 salvage categories explained in plain English. Phonetic Bridge is "
        "the largest (93 segments). Categories overlap. Each represents a "
        "different mechanism by which meaning survives despite high WER.",
        [cat_shapes])


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
    """14b: 2×4 clickable video grid matching Slide 14 curated examples."""
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    add_text(slide, "Click any thumbnail to play (PowerPoint / compatible viewer):",
             MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY)

    # Grid layout: 4 cols × 2 rows
    vid_w  = Inches(2.82)
    vid_h  = Inches(1.58)   # 16:9
    gap_x  = Inches(0.23)
    gap_y  = Inches(0.55)   # space for label below each video
    row_y  = [CT + Inches(0.45), CT + Inches(0.45) + vid_h + gap_y]
    start_x = MX

    rows = [
        [("perfect",      "Perfect",     "0%",   GREEN),
         ("nearmiss",     "Near-Miss",   "58%",  YELLOW),
         ("halluc",       "Hallucin.",   "100%", RED),
         ("tuning_fix",   "Tuning Fix\n(baseline: empty)",  "73%",  ORANGE)],
        [("topic_drift",  "Topic Drift", "97%",  RED),
         ("salvage",      "Salvage",     "74%",  YELLOW),
         ("entity_success","Entity OK",  "31%",  GREEN),
         ("entity_destroy","Entity Lost","100%", RED)],
    ]

    for r, row in enumerate(rows):
        for c, (key, label, wer, color) in enumerate(row):
            x = start_x + c * (vid_w + gap_x)
            y = row_y[r]
            add_video(slide, key, x, y, vid_w, vid_h)
            # WER badge
            add_text(slide, f"{label}  WER {wer}",
                     x, y + vid_h + Inches(0.04), vid_w, Inches(0.32),
                     size=Pt(9), color=color, bold=False,
                     align=PP_ALIGN.CENTER)

    _finish(slide, "14b",
        "8 videos matching the curated examples on Slide 14. "
        "Row 1: Perfect transcription, near-miss (probiotics→permafrost), "
        "full hallucination, Config J tuning fix (empty→output). "
        "Row 2: Topic drift (#1 failure), salvage hidden gem, entity preserved "
        "despite wrong numbers, entity completely destroyed. Click each to play.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE A15 — VIDEO GALLERY MAP
# ═══════════════════════════════════════════════════════════════════════

def slide_is_deep_dive(prs):
    """IS correlation deep dive — signal relationships."""
    slide = new_slide(prs)
    add_title(slide, "Why These 6 Signals? A Validation")
    add_accent_line(slide)

    add_text(slide,
        "Three independent quality dimensions confirm IS captures distinct, "
        "complementary aspects of transcription quality \u2014 not arbitrary signals.",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    offset = Inches(0.45)

    # Left — correlation table (larger)
    lt = add_text(slide, "Signal \u2192 IS Correlation", MX, CT + offset, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "r with IS", "Weight", "Variance %"],
        [["Phonetic Sim", "0.943", "15%", "~18%"],
         ["Semantic Sim", "0.856", "25%", "28.5%"],
         ["Inv. WER", "0.834", "15%", "~16%"],
         ["Inv. WWER", "0.823", "15%", "~15%"],
         ["NEA F1", "0.748", "15%", "17.3%"],
         ["Length Ratio", "0.521", "15%", "9.1%"]],
        MX, CT + offset + Inches(0.5), col_w, text_size=Pt(14),
        row_height=Inches(0.5),
        row_colors={0: {1: GREEN}, 5: {1: CORAL, 3: CORAL}})

    # Right — key insights (larger text)
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Key Insights", rx, CT + offset, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Phonetic Sim is strongest predictor (r=0.943) "
         "despite only 15% weight", {"bold": True}),
        "WER/WWER/Phonetic are NOT independent \u2014 "
         "all measure visual encoder quality",
        "Semantic Sim (25%) drives 28.5% variance \u2014 "
         "the tiebreaker for similar-accuracy segments",
        ("NEA punches above weight: 17.3% variance "
         "\u2014 names are binary (right or wrong)",
         {"color": TEAL}),
        ("Length Ratio weakest (9.1%) \u2014 could "
         "reduce its weight in future", {"color": CORAL}),
        ("Expert heuristic: r=0.934 with IS", {"bold": True}),
    ], rx, CT + offset + Inches(0.5), rw, Inches(4.5), size=Pt(15))

    _finish(slide, 0,
        "Signal correlation analysis. Phonetic similarity is the strongest "
        "single predictor at r=0.943, despite only 15% weight. This makes "
        "sense: it's the most direct measure of visual encoder quality. "
        "Semantic similarity (25% weight) captures 28.5% of IS variance. "
        "Length ratio is weakest at 9.1%. The expert heuristic (15-rule "
        "decision tree) achieves r=0.934.",
        [[rt, rb], [lt, tbl]], click_reveal=True)


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
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        cards.append(r)
        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35))
        add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY)

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
        [[c] for c in cards], click_reveal=True)

    # Hide slide
    slide._element.set('show', '0')


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
         "Ref: \"carry strap\" → Hyp: 3 paragraphs about history\n"
         "WER 6,833%, length ratio 45\u00d7 — LLM ran unchecked.\n"
         "IS catches via length + semantic: fluent but fabricated."),
        ("NEA low, Semantic moderate", GOLD,
         "Topic right, entities destroyed",
         "\"the 13th amendment\" → \"the important decision\"\n"
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
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        cards.append(r)
        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35))
        add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY)

    add_text(slide,
        "8 total diagnostic patterns — IS decomposes quality into actionable signals "
        "that each point to a different engineering fix.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four more metric disagreement patterns. Length collapse = signal loss. "
        "Length explosion + low semantic = hallucination. Low NEA + moderate semantic = "
        "entity destruction. All-moderate = accumulated errors.",
        [[c] for c in cards], click_reveal=True)

    # Hide slide
    slide._element.set('show', '0')


def slide_two_eval_systems(prs):
    """Two evaluation systems — IS and expert heuristic."""
    slide = new_slide(prs)
    add_title(slide, "Two Evaluation Systems, One Framework")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — IS (strict) + Expert Heuristic (generous)
    lt = add_text(slide, "The Two Systems", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    # IS card
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Intelligibility Score (IS)", MX + Inches(0.2),
             CT + Inches(0.6), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    add_bullets(slide, [
        "Strict metric: composite 0\u20135 score",
        ("IS \u2265 3.0 = Captured: 39.9% (597/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(13))

    # Expert heuristic card
    r2 = add_rect(slide, MX, CT + Inches(2.3), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Expert Heuristic (LLM Salvage)", MX + Inches(0.2),
             CT + Inches(2.4), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=GREEN, bold=True)
    add_bullets(slide, [
        "Generous: identifies recoverable segments",
        ("IS < 3.0 but salvageable: 50.9% (762/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(2.8), col_w - Inches(0.4), Inches(0.8),
       size=Pt(13))

    # Right — agreement + worked example
    rx = MX + col_w + gap
    rt = add_text(slide, "Agreement Between Systems", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    tbl = add_table(slide,
        ["Metric", "Value"],
        [["Pearson r", "0.934"],
         ["Agreement at IS \u2265 3.0", "88.6%"],
         ["Cohen's \u03ba", "0.773"],
         ["Recall (Heuristic)", "99.2%"],
         ["Cross-config mean r", "0.925"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12))

    # Worked example
    add_text(slide, "Worked Example:", rx, CT + Inches(2.8), col_w, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    add_text(slide,
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.92 (failed) \u2022 LLM prob: 0.90 (salvaged)\n'
        'Meaning preserved despite word differences.',
        rx, CT + Inches(3.2), col_w, Inches(1.5),
        size=Pt(12), color=WHITE)

    _finish(slide, 0,
        "Two evaluation systems. IS is strict: 39.9% pass at IS >= 3.0. "
        "The expert heuristic is generous: identifies 165 additional segments, "
        "raising effective capture to 50.9%. They agree 88.6% of the time "
        "(r=0.934, kappa=0.773). The heuristic catches meaning preservation "
        "that strict metrics miss.",
        [[r1, r2], [rt, tbl]], click_reveal=True)


def slide_llm_judge(prs):
    """LLM-as-a-Judge gold standard evaluation."""
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge: Gold Standard (1,497 Pairs)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — protocol + results
    lt = add_text(slide, "Protocol", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Claude Opus evaluated all 1,497 ref+hyp pairs",
        "Blind (no topic context), 3-level: Y / P / N",
        "30 duplicate pairs for intra-rater reliability",
        ("Intra-rater: 86.7% exact agreement", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(1.8), size=Pt(13))

    # Results table
    res_t = add_text(slide, "Results (Blind)", MX, CT + Inches(2.4), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Count", "%"],
        [["Y (fully preserved)", "345", "23.0%"],
         ["P (partially)", "626", "41.8%"],
         ["N (not preserved)", "526", "35.1%"],
         ["Y+P (any useful)", "971", "64.9%"]],
        MX, CT + Inches(2.8), col_w, text_size=Pt(12),
        row_colors={0: {2: GREEN}, 2: {2: CORAL}, 3: {2: TEAL}})

    # Right — IS correlation
    rx = MX + col_w + gap
    rt = add_text(slide, "Correlation with IS", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    add_text(slide, "r = 0.85", rx, CT + Inches(0.6), col_w, Inches(0.7),
             size=Pt(36), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Pearson correlation (IS \u2194 LLM Judge)",
             rx, CT + Inches(1.2), col_w, Inches(0.3),
             size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

    # Tier summary
    add_text(slide, "LLM Judge \u00d7 IS Tier", rx, CT + Inches(1.8), col_w,
             Inches(0.3), size=Pt(15), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["IS Tier", "Y%", "P%", "N%"],
        [["5 (Excellent)", "57%", "38%", "5%"],
         ["4 (Good)", "21%", "59%", "20%"],
         ["3 (Fair)", "8%", "51%", "41%"],
         ["2 (Poor)", "4%", "34%", "62%"],
         ["1 (Failed)", "2%", "17%", "81%"]],
        rx, CT + Inches(2.2), col_w, text_size=Pt(11),
        row_colors={0: {1: GREEN}, 4: {3: CORAL}})

    # Key takeaway
    add_text(slide,
        "LLM judge is more conservative for full success (23% vs IS 40%) "
        "but more generous for any useful output (Y+P=65%).",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "LLM-as-a-Judge gold standard. Claude Opus evaluated all 1,497 pairs "
        "blind. Y=23.0% (345), P=41.8% (626), N=35.1% (526). Y+P=64.9% — "
        "the LLM says nearly 2 in 3 segments have useful output. Intra-rater "
        "reliability 86.7%. Correlation with IS: r=0.85 (Pearson 0.8495).",
        [[lt, lb, res_t, tbl], [rt, tbl2]], click_reveal=True)


def slide_context_eval(prs):
    """Context-aware re-evaluation results."""
    slide = new_slide(prs)
    add_title(slide, "Context Makes the Judge Stricter, Not Lenient")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — comparison table
    lt = add_text(slide, "Blind vs Context-Aware", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Blind", "Context", "\u0394"],
        [["Y (fully preserved)", "23.0% (345)", "15.0% (225)", "\u22128.0pp"],
         ["P (partially)", "41.8% (626)", "47.1% (705)", "+5.3pp"],
         ["N (not preserved)", "35.1% (526)", "37.9% (567)", "+2.8pp"],
         ["Y+P (useful)", "64.9% (971)", "62.1% (930)", "\u22122.7pp"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(11),
        col_widths=[Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.0)],
        row_colors={0: {3: CORAL}, 3: {3: CORAL}})

    add_text(slide,
        "Context reveals vocabulary failures that blind evaluation misses.",
        MX, CT + Inches(2.4), col_w, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    # Key finding
    kf_t = add_text(slide, "Key Finding:", MX, CT + Inches(3.0), col_w, Inches(0.3),
             size=Pt(15), color=CORAL, bold=True)
    kf_b = add_bullets(slide, [
        ("Y drops 8pp: context reveals missed domain vocabulary",
         {"color": CORAL}),
        "Y\u2192P dominant transition (138 of 230 downgrades)",
        ("Only 1 N\u2192Y rescue across all 1,497 pairs", {"bold": True}),
    ], MX, CT + Inches(3.4), col_w, Inches(1.5), size=Pt(13))

    # Right — transition matrix
    rx = MX + col_w + gap
    rt = add_text(slide, "Transition Matrix", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    tbl2 = add_table(slide,
        ["", "Ctx Y", "Ctx P", "Ctx N"],
        [["Blind Y", "207", "138", "0"],
         ["Blind P", "17", "519", "90"],
         ["Blind N", "1", "48", "477"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Summary stats
    add_text(slide, "Summary", rx, CT + Inches(2.3), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    tbl3 = add_table(slide,
        ["Direction", "Count"],
        [["Downgrades (stricter)", "230"],
         ["Upgrades (lenient)", "68"],
         ["Unchanged", "1,199"],
         ["Cross-condition agreement", "80.0%"]],
        rx, CT + Inches(2.7), col_w, text_size=Pt(11),
        row_colors={0: {1: CORAL}, 1: {1: GREEN}})

    # Bottom
    add_text(slide,
        "Context is STRICTER not lenient \u2014 230 downgrades vs 68 upgrades. "
        "Domain knowledge reveals vocabulary failures.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware re-evaluation. When the judge knows the topic, Y drops "
        "from 23% to 15% (-8pp). Y+P drops from 64.9% to 62.1%. Context is "
        "STRICTER, not lenient. 230 downgrades vs 68 upgrades. Dominant "
        "transition: Y to P (138 cases) — the judge realizes domain vocabulary "
        "was wrong. Only 1 N-to-Y rescue across all 1,497 pairs.",
        [[lt, tbl], [rt, tbl2, tbl3], [kf_t, kf_b]], click_reveal=True)


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


