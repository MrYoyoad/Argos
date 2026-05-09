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
    # audit:bigfonts — left bullets trimmed 5 -> 3 (cut "Extreme parameters"
    # and "Lenpen=2.0" — both in speaker notes) so Pt(24) fits in h=3.0;
    # explicit size=Pt(24) added to both bullet lists.
    slide = new_slide(prs)
    add_title(slide, "Best Config vs Baseline: The Trade-off")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — What we found
    lt = add_text(slide, "What We Found", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Config J (lenpen=1.0, temp=0.5) was best overall", {"bold": True}),
        "Most configs cluster in narrow IS range (2.45\u20132.60)",
        ("Lenpen=\u22120.5: 45% empty outputs", {"color": CORAL}),
        # ("Extreme parameters cause catastrophic failures",),  # cut bigfonts
        # ("Lenpen=2.0: mean WER 540% (massive hallucination)",),  # cut bigfonts
    ], MX, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(24))

    # Right column — Best Config (J)
    rx = MX + col_w + gap
    rt = add_text(slide, "Best Config (J) — 1,497 segments",
                  rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "IS: 2.60 vs 2.53 baseline (+0.07)",
        ("Captured: 622 vs 601 (+21)", {"color": GREEN}),
        ("Empties: 0 vs 70 (eliminated)", {"color": GREEN}),
        ("Hallucinations: 348 vs 307 (+41)", {"color": CORAL}),
    ], rx, CT + Inches(0.5), col_w, Inches(2.1), size=Pt(24))

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
    # audit:bigfonts — uses build_split helper; bullet font sizing handled
    # by helpers.py (out of scope for this module). Bullets unchanged: 6
    # bullets at the helper's default size, helper handles wrapping.
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
    # audit:bigfonts — explicit text_size=Pt(24), row_height bumped 0.55->0.85
    # so 18pt cells render legibly. Row count unchanged (4 examples).
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
                    MX, CT, CW, row_height=Inches(0.85),
                    col_widths=[Inches(1.7), Inches(3.7), Inches(3.7),
                                Inches(1.0), Inches(1.0)],
                    text_size=Pt(24),
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

def slide_16(prs):
    # audit:bigfonts — left bullets trimmed (5 -> 4) to fit 18pt; right
    # validation table row_height bumped 0.32->0.50 for legible 16pt cells.
    slide = new_slide(prs)
    add_title(slide, "IS Validation: Design-Time Distilled Evaluation")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: How IS works
    lt = add_text(slide, "How the IS Was Built", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    # audit:bigfonts — cut 5th bullet "Result: reproducible, free,
    # decomposable scoring" (now in speaker notes).
    lb = add_bullets(slide, [
        "Framework designed at development time",
        "6 signals: Semantic 25%, Phonetic 15%, inv.WER 15%, "
        "inv.WWER 15%, NEA F1 15%, Length 15%",
        "5 tiers, 5 failure categories, 7 success patterns",
        ("Distilled into deterministic formulas — no LLM per sample",
         {"bold": True}),
        # ("Result: reproducible, free, decomposable scoring",),  # cut
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(24))

    # Right: Correlation analysis + validation
    rx = MX + col_w + gap
    rt = add_text(slide, "PCA: 2 Dimensions of Quality", rx, CT, col_w,
                  Inches(0.35), size=Pt(24), color=CORAL, bold=True)

    # Two PCA dimensions (actual PCA results)
    dims = [
        ("PC1: Signal Quality", "All 5 content signals load equally (0.43\u20130.47)", "68%", TEAL),
        ("PC2: Output Length", "Length Ratio dominates (loading 0.91)", "20%", LGRAY),
    ]
    dim_y = CT + Inches(0.5)
    for i, (name, signals, pct, color) in enumerate(dims):
        y = dim_y + i * Inches(0.75)
        add_text(slide, name, rx, y, col_w, Inches(0.3),
                 size=Pt(24), color=color, bold=True)
        add_text(slide, f"{signals} \u2014 {pct} of variance",
                 rx + Inches(0.15), y + Inches(0.3), col_w - Inches(0.15),
                 Inches(1.4), size=Pt(24), color=LGRAY)
    add_text(slide, "Together: 88% of total variance (Kaiser criterion)",
             rx + Inches(0.15), dim_y + 2 * Inches(0.75) + Inches(0.1),
             col_w - Inches(0.15), Inches(0.3), size=Pt(24), color=LGRAY)

    # Cross-config validation stats
    add_text(slide, "Cross-Config Validation (16 configs)",
             rx, CT + Inches(2.9), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["LLM heuristic vs IS", "r = 0.925"],
        ["Agreement (IS ≥ 2.00)", "κ = 0.818"],
        ["Recall (IS ≥ 2.00)", "97.6–100%"],
        ["Cohen's κ", "0.773"],
        ["Segment ranking stability", "r > 0.92"],
    ]
    add_table(slide, headers, rows, rx, CT + Inches(3.3), col_w,
              row_height=Inches(0.45),
              col_widths=[Inches(3.0), Inches(2.5)],
              text_size=Pt(24))

    _finish(slide, 16,
        "How the IS was built: the entire framework was designed at development "
        "time — rubric, 6 signals with weights, tier boundaries, failure mode "
        "taxonomy, success patterns. These were then encoded into deterministic "
        "formulas. No LLM is called per sample at runtime.\n\n"
        "PCA RESULTS (Kaiser criterion, 2 PCs retained):\n"
        "PC1 (68%): Signal Quality — all 5 content signals load equally "
        "(0.43-0.47). Semantic is NOT independent of word accuracy.\n"
        "PC2 (20%): Output Length — Length Ratio dominates (0.91). "
        "Independent of content quality.\n"
        "Together: 88% of variance. The visual encoder drives PC1.\n\n"
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
    # audit:bigfonts — bullets trimmed (4 -> 3); hero rect grew 4.6 -> 5.0
    # so 20pt bullets fit; bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate for LLM Judgment")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(5.0), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric — in CORAL for this variant
    add_text(slide, "IS says 62%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments pass (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge — the validation
    add_text(slide, "LLM Judge says 65%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets below
    # audit:bigfonts — cut bullet "LLM-as-a-Judge (blind, 1,497 pairs)
    # confirms: nearly 2 in 3 segments carry useful meaning" (in notes).
    bul = add_bullets(slide, [
        ("IS conservatively undercounts \u2014 real quality higher than 62%",
         {"bold": True, "color": WHITE}),
        ("Gap (62% \u2192 65%) = partial-value segments strict metrics penalize",
         {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(2.1), size=Pt(24))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "Independent LLM judge confirms true useful rate is 3pp higher.",
             MX, Inches(6.55), CW, Inches(0.5),
             size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "IS provides a conservative lower bound for transcription quality. "
        "IS says 62% of segments are useful (IS >= 2.00). But an independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 65% deliver useful output. The 25pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling \u2014 the real quality of the "
        "system is higher than our metric reports.",
        [[r1], [bul]], click_reveal=True)


def slide_25b(prs):
    """LLM Salvage: 6 recovery categories explained."""
    # audit:bigfonts \u2014 categories trimmed 6 -> 4 (cut "Hidden Gems 54" and
    # "WER Over-Punishment 27" \u2014 both still in speaker notes); card height
    # bumped 0.7 -> 0.95 with stride 0.78 -> 1.05 so 18pt name + 16pt desc
    # don't crash. Right-column plot kept; bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: 4 Top Recovery Categories")
    add_accent_line(slide)

    add_text(slide,
        "165 segments that metrics call \u201cfailed\u201d (IS < 2.0) deliver useful "
        "meaning. Top 4 of 6 overlapping categories:",
        MX, CT, CW, Inches(0.45), size=Pt(18), color=LGRAY, italic=True)

    categories = [
        ("Phonetic Bridge", "93", TEAL,
         "Words sound right, spelled differently \u2014 viewer fills in gaps."),
        ("Structure Match", "74", TEAL,
         "Same grammar as reference \u2014 word order + S-V-O preserved."),
        ("Semantic Preservation", "57", GREEN,
         "Core meaning conveyed despite high WER \u2014 like a paraphrase."),
        # ("Hidden Gems", "54", GREEN, ...),  # cut in big-fonts pass
        ("Entity-Preserved", "44", YELLOW,
         "Names + numbers correct even though surrounding words are wrong."),
        # ("WER Over-Punishment", "27", YELLOW, ...),  # cut in big-fonts pass
    ]

    # Cards shrunk from full CW to 7.4" to make room on the right for the
    # newly embedded P_llm_salvage stack plot (MBR-IS, recovery types).
    # Description column also shrinks; text reflows but content preserved.
    card_w = Inches(7.4)
    py = CT + Inches(0.6)
    card_groups = []
    for name, count, color, desc in categories:
        r = add_rect(slide, MX, py, card_w, Inches(0.95), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name} ({count})",
                 MX + Inches(0.2), py + Inches(0.10), Inches(2.6), Inches(0.4),
                 size=Pt(24), color=color, bold=True)
        t2 = add_text(slide, desc,
                 MX + Inches(2.85), py + Inches(0.18),
                 card_w - Inches(2.95), Inches(0.65),
                 size=Pt(24), color=LGRAY)
        card_groups.append([r, t1, t2])
        py += Inches(1.05)

    # Right column \u2014 regenerated P_llm_salvage stack plot (MBR-IS).
    # Same 6 recovery types as the left cards, visualised as a stacked bar.
    img_w = Inches(4.55)
    img_h = Inches(2.2)         # ratio 2.07 \u2192 height 2.20"
    img_x = MX + card_w + Inches(0.15)
    img_y = CT + Inches(0.55)
    img_salvage = add_image(slide, "P_llm_salvage", img_x, img_y,
                            width=img_w, height=img_h)
    cap_salvage = add_text(slide,
        "Right: stacked recovery-types plot (MBR-IS).",
        img_x, img_y + img_h + Inches(0.05), img_w, Inches(0.3),
        size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "Categories overlap \u2014 a segment can exhibit multiple recovery signals.",
        MX, Inches(6.45), CW, Inches(0.35),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "6 salvage categories explained in plain English. Phonetic Bridge is "
        "the largest (93 segments). Categories overlap. Each represents a "
        "different mechanism by which meaning survives despite high WER. "
        "Plot embed (May 2026): the regenerated P_llm_salvage.png stack "
        "lives in the right column \u2014 same 6 recovery types computed against "
        "MBR-IS components, gives the audience a quantitative summary "
        "alongside the per-category descriptions. Cards were shrunk from "
        "full width to 7.4\" and description font dropped from 11pt to "
        "10pt to make room.",
        card_groups + [[img_salvage, cap_salvage]])


def slide_25c(prs):
    """How the salvage detection decision tree works."""
    # audit:bigfonts — see inline comments; right table row_height up,
    # right bullets trimmed.
    slide = new_slide(prs)
    add_title(slide, "How Salvage Detection Works")
    add_accent_line(slide)

    # Flow: Input -> 6 checks -> Score -> Threshold -> Result
    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — the process
    lt = add_text(slide, "Deterministic Decision Tree", MX, CT, col_w, Inches(0.35),
                  size=Pt(24), color=TEAL, bold=True)

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
                     size=Pt(24), color=color, bold=True)
        add_text(slide, desc, MX + Inches(2.0), py, Inches(3.4), Inches(0.5),
                 size=Pt(24), color=LGRAY)
        step_shapes.append(t)
        py += Inches(0.65)

    # Right — validation stats
    rx = MX + col_w + gap
    rt = add_text(slide, "Validation", rx, CT, col_w, Inches(1.0),
                  size=Pt(24), color=GREEN, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["Correlation with IS", "r = 0.934"],
        ["Agreement (IS \u2265 2.00)", "\u03ba = 0.818"],
        ["Agreement (IS \u2265 3.80)", "\u03ba = 0.690"],
        ["Recall (IS \u2265 2.00)", "97.6\u2013100%"],
        ["Cross-config stability", "r = 0.925 \u00b1 0.015"],
    ]
    # audit:bigfonts \u2014 table row_height bumped 0.4 -> 0.5; bullets trimmed
    # 3 -> 2 (cut "Recall 97.6-100% across 16 decode configurations" \u2014 same
    # info already on the table row above).
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.5), col_w,
                    row_height=Inches(0.5),
                    col_widths=[Inches(2.8), Inches(2.7)],
                    text_size=Pt(24))

    rb = add_bullets(slide, [
        "Stable across all 16 decode configurations",
        # "Recall 97.6-100% across 16 decode configurations",  # cut (already on table)
        ("Zero cost: pure Python, no LLM calls at runtime", {"bold": True}),
    ], rx, CT + Inches(3.7), col_w, Inches(1.5), size=Pt(24))

    # Bottom
    add_text(slide,
        "The decision tree was designed at development time, then distilled "
        "into deterministic Python. No LLM is called during evaluation.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "How the salvage detection works: a 15-rule deterministic decision tree "
        "that checks 6 linguistic signals and outputs a recovery probability. "
        "Validated at r=0.934 with IS, κ=0.818 (Y+P), stable across 16 configs.",
        [[lt] + step_shapes, [rt, tbl, rb]])

def slide_25d(prs):
    """Three real salvage examples showing HOW recovery works."""
    # audit:bigfonts \u2014 "how" body trimmed (~50% length) so 16pt fits in the
    # h=2.00" recovery body box of each 3.8"x5.4" card. Originals are kept
    # in the speaker notes / source docs (llm_salvage_analysis.md). REF/HYP
    # left at 18pt per task tier.
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Three Real Recoveries")
    add_accent_line(slide)

    add_text(slide,
        "These segments failed IS (< 3.0) but a viewer with context would understand them:",
        MX, CT, CW, Inches(0.35), size=Pt(18), color=LGRAY, italic=True)

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

    # CUT v3: each "how" trimmed to ~70 chars so Pt(24) wraps in 4 lines
    # within the 2.00" frame (was 9 lines, bottom 8.55). Full prose for each
    # is preserved in speaker notes below + salvage_example_gallery.md.
    examples = [
        {
            "title": "Phonetic Bridge",
            "color": TEAL,
            "is_score": "1.29", "wer": "150%", "prob": "0.55",
            "ref": "when jesus rose again",
            "hyp": "in one sense it\u2019s rose\nand kennedy",
            # audit:bigfonts \u2014 trimmed from ~330 chars to ~180 (cut the
            # mouth-shape aside; full text in salvage_example_gallery.md).
            "how": "Religious-program viewer reads \u201cJesus rose.\u201d "
                   "Mouth shapes nearly identical.",
        },
        {
            "title": "Semantic Preservation",
            "color": GREEN,
            "is_score": "2.18", "wer": "75%", "prob": "0.90",
            "ref": "moving conceptual surface data\nover to engineering solutions\nand tools",
            "hyp": "moved the conceptual rules\nover to engineering tools",
            # audit:bigfonts \u2014 trimmed (cut "WER over-punishes ..." aside).
            "how": "Core meaning intact: concepts \u2192 tools. "
                   "Function words changed only.",
        },
        {
            "title": "Structure Match",
            "color": GOLD,
            "is_score": "2.55", "wer": "40%", "prob": "0.95",
            "ref": "over the last 10 years we have\nhad 8,616 students",
            "hyp": "over the last 10 years we have\nhad 1,600 students",
            # audit:bigfonts \u2014 trimmed (cut closing aside about exact figure).
            "how": "Only the number changed (8,616 \u2192 1,600). "
                   "Viewer reads \u201cmany students.\u201d",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # CUT v3 (overflow): font 16pt body so 3-line refs fit; layout reorg.
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.05), cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(20), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.50), cw_card - Inches(0.3), Inches(0.40),
                 size=Pt(18), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.95),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.25), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(2.40),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.70), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a viewer recovers this:",
                 x + Inches(0.15), cy + Inches(3.65),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.95), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE)

    _finish(slide, 0,
        "Three real salvage examples drawn from the LLM-Salvage analysis "
        "(165 of 900 metric-failed segments are recoverable, 18%). The "
        "card on the left shows a Phonetic Bridge (IS 1.29, WER 150%) where "
        "lip-shape collisions produce linguistically plausible but wrong "
        "words yet a viewer with religious context recovers the meaning. "
        "The middle card shows Semantic Preservation (IS 2.18, WER 75%) — "
        "core meaning intact even though every function word shifted. The "
        "right card shows Structure Match (IS 2.55, WER 40%) — perfect "
        "grammar with only a number changed; a viewer reads 'many students "
        "over 10 years' even though the exact figure (8,616 vs 1,600) is "
        "wrong. Each example illustrates one of the six recovery categories "
        "the llm_context_prob heuristic uses to flag salvage. "
        "Sources: docs/evaluation/llm_salvage/llm_salvage_analysis.md, "
        "docs/evaluation/llm_salvage/salvage_example_gallery.md.",
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
        MX, CT, CW, Inches(0.35), size=Pt(18), color=LGRAY, italic=True)

    # audit:pptx_fix_manifest_after_amosi.md slide 44 MAJOR -
    # body font was 9-10pt; lifted to 12pt and card height bumped to 5.4".
    # Three cards side by side (same layout as slide_25d)
    cw_card = Inches(3.8)
    ch_card = Inches(5.4)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    # CUT v3: each "how" trimmed to ~70 chars so Pt(24) wraps in 4 lines
    # within 2.00" frame (was 8 lines, bottom 7.75). Full prose preserved
    # in speaker notes + salvage_example_gallery.md.
    examples = [
        # audit:bigfonts \u2014 "how" texts trimmed ~50% so 16pt fits the h=2.00"
        # recovery body box. Full versions live in
        # docs/evaluation/llm_salvage/salvage_example_gallery.md.
        {
            "title": "Religious Context",
            "color": CORAL,
            "is_score": "2.75", "wer": "43%", "prob": "0.90",
            "ref": "the fear of allah is completely\ngone \u2026 no more fear of the\nunseen what a horrible spiritual",
            "hyp": "the fear of the loss complete\n\u2026 no more fear of loss\nwhat a horrible spiritual",
            "how": "Sermon viewer hears \u201cfear of Allah.\u201d "
                   "Structure intact, phonetic swap.",
        },
        {
            "title": "Geopolitical Context",
            "color": TEAL,
            "is_score": "2.86", "wer": "72%", "prob": "0.90",
            "ref": "india china afghanistan all\nthese different places \u2026 so\nboth sides would benefit",
            "hyp": "middle east and afghanistan\nall these different warring\nplaces \u2026 both sides will benefit",
            "how": "Country names swap; argument identical. "
                   "Domain swap, not meaning loss.",
        },
        {
            "title": "Cooking Context",
            "color": GREEN,
            "is_score": "2.07", "wer": "89%", "prob": "0.80",
            "ref": "i have a tablespoon of\njalapeno fresh jalapeno",
            "hyp": "i have a dietary smoothie\ni\u2019ve got the banana called\nfresh banana",
            "how": "Viewer sees a pepper, overrides \u201cbanana.\u201d "
                   "Visual context fixes WER.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # CUT v3 (overflow): font 16pt body so 3-line refs fit; layout reorg.
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.05), cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(20), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.50), cw_card - Inches(0.3), Inches(0.40),
                 size=Pt(18), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.95),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.25), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(2.40),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.70), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a wise viewer recovers this:",
                 x + Inches(0.15), cy + Inches(3.55),
                 cw_card - Inches(0.3), Inches(0.40), size=Pt(16), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.95), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE)

    _finish(slide, 0,
        "Three more salvage examples emphasising domain-context recovery. "
        "Religious Context (IS 2.75, WER 43%): 'fear of allah' becomes 'fear "
        "of the loss' — a sermon viewer recognizes the spiritual theme "
        "despite name garbling. Geopolitical Context (IS 2.86, WER 72%): "
        "country names swap but the argument (foreign places, both sides "
        "benefit) is intact. Cooking Context (IS 2.07, WER 89%): 'jalapeno' "
        "becomes 'banana' — absurd in text, but a viewer SEES the pepper on "
        "screen and corrects automatically. This is the strongest argument "
        "for multimodal context: the visual channel fills gaps that "
        "audio-only metrics cannot measure. Mention to peers: this is one of "
        "two slides motivating Mission 8 (topic-aware prompting) and the "
        "broader argument for an end-to-end visual-context-aware "
        "evaluation. "
        "Sources: docs/evaluation/llm_salvage/llm_salvage_analysis.md, "
        "docs/evaluation/llm_salvage/salvage_example_gallery.md.",
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

    audit:bigfonts — captions at 18pt fit single line in 0.40" box; long
    captions wrap into 2 lines (visible inside grid spacing).
    """
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    intro = add_text(slide, "Click any thumbnail to play — each video demonstrates a different system behavior:",
             MX, CT, CW, Inches(0.35), size=Pt(24), color=LGRAY)

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
                     size=Pt(24), color=color, bold=False,
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
    # audit:bigfonts — no content cuts; all bumps fit in existing layout.
    slide = new_slide(prs)
    add_title(slide, "IS Validation: What Did We Learn?")
    add_accent_line(slide)

    add_text(slide,
        "We validated IS against signal analysis and cross-configuration testing. "
        "Here is what the evidence shows.",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    offset = Inches(0.45)

    # Left — compact correlation table
    lt = add_text(slide, "Signal \u2192 IS Correlation", MX, CT + offset, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "r with IS", "Dimension"],
        [["Phonetic Sim", "0.943", "Word Accuracy"],
         ["Inv. WER", "0.834", "Word Accuracy"],
         ["Inv. WWER", "0.823", "Word Accuracy"],
         ["Semantic Sim", "0.856", "Meaning"],
         ["NEA F1", "0.748", "Entity Accuracy"],
         ["Length Ratio", "0.521", "Output Sanity"]],
        MX, CT + offset + Inches(0.5), col_w, text_size=Pt(24),
        row_height=Inches(0.45),
        row_colors={0: {1: GREEN}, 5: {1: CORAL}})

    # Right — conclusions (the main point)
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Conclusions", rx, CT + offset, rw, Inches(0.4),
                  size=Pt(28), color=CORAL, bold=True)
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
    ], rx, CT + offset + Inches(0.5), rw, Inches(4.5), size=Pt(24))

    _finish(slide, 0,
        "IS validation conclusions. PCA retains 2 principal components: "
        "signal quality (68%, all 5 content signals load equally) and "
        "output length (20%, Length Ratio dominates). Semantic is NOT "
        "an independent dimension \u2014 it loads on PC1 alongside word-accuracy "
        "signals. Cross-config validation across 16 decode configurations "
        "confirms stability with mean r=0.925.",
        [[lt, tbl], [rt, rb]], click_reveal=True)


def slide_metric_disagreement(prs):
    """What metric disagreements reveal about transcription quality."""
    # audit:bigfonts — bumps fit within 5.8x2.0 cards; no trims needed.
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: What It Tells Us")
    add_accent_line(slide)

    add_text(slide,
        "IS uses 6 signals because no single metric tells the full story. "
        "Disagreements between metrics reveal specific quality patterns:",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

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
            [(title, {"size": Pt(24), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(24), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(24), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "This is why IS uses 6 signals \u2014 each disagreement pattern "
        "reveals a different type of quality that a single metric would miss.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four key metric disagreement patterns. WWER<<WER means function words "
        "are wrong but content preserved. High NEA + high WER means names survived. "
        "High semantic + high WER means paraphrasing. High phonetic + low semantic "
        "is the dangerous case — sounds right but wrong meaning.",
        [c for c in cards], click_reveal=True)


def slide_metric_disagreement_2(prs):
    """More metric disagreement patterns — part 2."""
    # audit:bigfonts — bumps fit within 5.8x2.0 cards; no trims needed.
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: More Patterns")
    add_accent_line(slide)

    add_text(slide,
        "Additional diagnostic patterns that reveal specific transcription behaviors:",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

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
            [(title, {"size": Pt(24), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(24), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(24), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "8 total diagnostic patterns — IS decomposes quality into actionable signals "
        "that each point to a different engineering fix.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four more metric disagreement patterns. Length collapse = signal loss. "
        "Length explosion + low semantic = hallucination. Low NEA + moderate semantic = "
        "entity destruction. All-moderate = accumulated errors.",
        [c for c in cards], click_reveal=True)

    # Note: slide visibility controlled by hidden_builders in generate_presentation.py


def slide_two_eval_systems(prs):
    """Two evaluation systems — IS and Opus-as-a-Judge."""
    # audit:bigfonts — agreement-matrix table given explicit row_height for
    # 18pt cells; we_b worked-examples kept at Pt(24) to fit h=1.7 box.
    slide = new_slide(prs)
    add_title(slide, "Two Evaluation Systems, One Framework")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — IS (strict) + Opus-as-Judge (generous)
    lt = add_text(slide, "The Two Systems", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    # IS card
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    r1_t = add_text(slide, "Intelligibility Score (IS)", MX + Inches(0.2),
             CT + Inches(0.6), col_w - Inches(0.4), Inches(1.0),
             size=Pt(24), color=TEAL, bold=True)
    r1_b = add_bullets(slide, [
        "Strict metric: composite 0\u20135 score, two operating points",
        ("IS \u2265 3.80 = Clearly conveyed: 23% (346/1,497)", {"bold": True}),
        ("IS \u2265 2.00 = Any useful meaning: 62% (922/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24))

    # Opus-as-Judge card
    r2 = add_rect(slide, MX, CT + Inches(2.3), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    r2_t = add_text(slide, "Opus-as-a-Judge (LLM Gold Standard)", MX + Inches(0.2),
             CT + Inches(2.4), col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=GREEN, bold=True)
    r2_b = add_bullets(slide, [
        "Holistic: Y/P/N per ref+hyp pair (1,497 pairs)",
        ("Y = 23% clearly conveyed, Y+P = 65% useful", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(2.8), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24))

    # Right — agreement + worked example
    rx = MX + col_w + gap
    rt = add_text(slide, "Agreement Between Systems", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    agree_txt = add_text(slide,
        "\u03ba = 0.818 (good agreement)\n"
        "IS undercounts: 62% vs judge 65%.",
        rx, CT + Inches(0.5), col_w, Inches(0.6),
        size=Pt(24), color=WHITE, bold=True)

    # NIV Y+P agreement matrix (IS >= 2.00 vs Opus Y+P)
    tbl = add_table(slide,
        ["", "Opus: Y or P", "Opus: N"],
        [["IS \u2265 2.00", "883", "39"],
         ["IS < 2.00", "88", "487"]],
        rx, CT + Inches(1.3), col_w, text_size=Pt(24),
        row_height=Inches(0.5),
        row_colors={0: {1: GREEN}, 1: {2: CORAL}})

    # Worked examples
    we_t = add_text(slide, "Worked Examples:", rx, CT + Inches(2.6), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)
    we_b = add_text(slide,
        'Ref: "what does this chord sound like to you"\n'
        'Hyp: "what does this court sound like to you"\n'
        'WER: 12% \u2022 IS: 3.84 \u2022 IS Y \u2714 \u2022 Opus: Y\n\n'
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.94 \u2022 IS Y+P \u2714 \u2022 Opus: P\n'
        'Old IS \u2265 3.0 wrongly rejected this segment.',
        rx, CT + Inches(2.95), col_w, Inches(1.7),
        size=Pt(24), color=WHITE)

    _finish(slide, 0,
        "Two evaluation systems with NIV thresholds. "
        "IS >= 3.80 for clearly conveyed (23%, matches judge Y rate 23%, kappa=0.690). "
        "IS >= 2.00 for any useful meaning (62%, kappa=0.818, almost perfect). "
        "Opus-as-a-Judge: Y=23%, Y+P=65%. "
        "IS is a strict estimator — undercounts at both operating points. "
        "Old IS >= 3.0 threshold is superseded: it sat in no-man's land (kappa=0.565 for Y, 0.521 for Y+P).",
        [[lt, r1, r1_t, r1_b], [r2, r2_t, r2_b], [rt, agree_txt, tbl, we_t, we_b]], click_reveal=True)


def slide_llm_judge(prs):
    """LLM-as-a-Judge gold standard evaluation."""
    # audit:bigfonts — results table given row_height=0.5 for 18pt cells.
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge: Gold Standard (1,497 Pairs)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — question/setup then methodology
    lt = add_text(slide, "What Is LLM-as-a-Judge?", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    # Bullets in 2.1" \u2014 enough for 4 lines at 24pt; res_t starts at CT+2.7
    # (0.3" gap after bullet frame) so the 4th bullet never crowds the header.
    lb = add_bullets(slide, [
        "Use a frontier LLM (Claude Opus) as an independent evaluator",
        "Evaluate every reference+hypothesis pair holistically",
        "3-level verdict: Y (preserved) / P (partial) / N (not preserved)",
        ("30 duplicate pairs \u2192 87% intra-rater reliability", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(2.1), size=Pt(24))

    # Results table \u2014 pushed down to CT+2.7 / CT+3.1 to clear bullet overflow
    res_t = add_text(slide, "Results (Blind, 1,497 Pairs)", MX, CT + Inches(2.7), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Count", "%"],
        [["Y (fully preserved)", "345", "23%"],
         ["P (partially)", "626", "42%"],
         ["N (not preserved)", "526", "35%"],
         ["Y+P (any useful)", "971", "65%"]],
        MX, CT + Inches(3.1), col_w, text_size=Pt(24),
        row_height=Inches(0.5),
        col_widths=[Inches(3.0), Inches(1.2), Inches(1.3)],
        row_colors={0: {2: GREEN}, 2: {2: CORAL}, 3: {2: TEAL}})

    # Right — Methodology
    rx = MX + col_w + gap
    rt = add_text(slide, "Methodology:", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    rb = add_bullets(slide, [
        "Claude Opus received each ref+hyp pair blind (no metrics visible)",
        "3-level holistic judgment: Y (fully conveyed), P (partial), N (lost)",
        ("\u03ba = 0.690 (Y threshold) and \u03ba = 0.816 (Y+P threshold)",
         {"color": TEAL}),
        ("Used as gold standard to calibrate IS thresholds",
         {"bold": True}),
    ], rx, CT + Inches(0.5), col_w, Inches(4.2), size=Pt(24))

    # audit:after_amosi_narrative_actions.md fix #7 - this is the v1
    # blind judge run (Opus 4.6, 1,497 pairs). The n-best paired-test
    # slide elsewhere in this section uses v3 (dual-conf, Opus 4.7,
    # 5,988 verdicts). Footer label disambiguates the two runs so the
    # audience does not conflate them.
    judge_label = add_text(slide,
        "v1 blind judge   /   Opus 4.6   /   1,497 pairs",
        MX, Inches(6.6), CW, Inches(0.3),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "LLM-as-a-Judge gold standard - v1 BLIND run (Claude Opus 4.6, "
        "1,497 pairs). Distinct from the v3 dual-conf judge run on the "
        "n-best paired-test slide later in this section, which uses "
        "Opus 4.7 with the dual-conf prompt across 5,988 verdicts. "
        "Headline: Y=23% (345 of 1,497), P=42% (626), N=35% (526), "
        "Y+P=65%. Intra-rater agreement 87% on the 30-pair duplicate "
        "subset. "
        "what justifies using IS as a deterministic surrogate. Threshold "
        "sweep: Y+P peaks at IS>=2.0 (kappa=0.816, 92% agreement); the "
        "older IS>=3.0 cutoff under-counts (kappa=0.521) and is now retired. "
        "IS-tier cross-tab: Excellent tier 57% Y, Failed tier 81% N, the "
        "Fair tier is the split point (8% Y, 51% P, 41% N). Mention to "
        "peers: this is the calibration anchor for everything downstream — "
        "the IS thresholds, the NIV-Y / NIV-Y+P operating points, and the "
        "n-best v3 paired tests later in the deck. Full cross-tab in "
        "appendix slide A8 (a16 builder).\n\n"
        "PEER DETAIL — Cohen's kappa: kappa = (P_obs − P_chance)/(1 − "
        "P_chance) on a 2×2 of (judge {Y, not-Y}) × (IS-NIV "
        "{>=threshold, <threshold}) on n=1,497. For kappa=0.690 the "
        "cells are 273/86/72/1066. Intra-rater 87% = exact-agreement on "
        "30 randomly resampled pairs.\n\n"
        "PEER DETAIL — IS thresholds were calibrated by sweeping IS in "
        "0.05 steps and picking the value that maximizes kappa vs "
        "judge-{Y, not-Y}: NIV-Y at IS>=3.80 (kappa=0.690), NIV-Y+P at "
        "IS>=2.00 (kappa=0.816). "
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/threshold_calibration_vs_opus.md.",
        [[lt, lb],
         [res_t, tbl],
         [rt, rb, judge_label]],
        click_reveal=True)


def slide_context_eval(prs):
    """IS: A Calibrated Surrogate Metric — IS vs LLM Judge comparison."""
    # audit:bigfonts — same trim as slide_25 sister; bullets 4 -> 3,
    # rect grew 4.6 -> 5.0, bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate Metric")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(5.0), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric
    add_text(slide, "IS says 62%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments deliver useful output (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge
    add_text(slide, "LLM Judge says 65%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets
    # audit:bigfonts — cut bullet "LLM-as-a-Judge (blind, 1,497 pairs)
    # confirms: nearly 2 in 3 segments carry useful meaning" (in notes).
    bul = add_bullets(slide, [
        ("IS closely tracks LLM judge \u2014 62% vs 65% "
         "(\u03ba = 0.818)", {"bold": True, "color": WHITE}),
        ("3pp gap (62% \u2192 65%) = IS is a calibrated surrogate",
         {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(2.1), size=Pt(24))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "Independent LLM judge confirms true useful rate is 3pp higher.",
             MX, Inches(6.55), CW, Inches(0.5),
             size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS is a calibrated surrogate metric for transcription quality. "
        "IS says 62% of segments deliver useful output (IS >= 2.00). An independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 65% deliver useful output. The 3pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling.",
        [[r1], [bul]], click_reveal=True)


def slide_what_good_looks_like(prs):
    """IS Tier 5 examples — what good looks like."""
    # audit:bigfonts — table reduced 3 -> 2 rows (middle "buyer wants to
    # buy one" was a verbatim duplicate); row_height 0.65 -> 1.10 so 16pt
    # body wraps; bullets trimmed 4 -> 3.
    slide = new_slide(prs)
    add_title(slide, "What Good Looks Like: IS Tier 5")
    add_accent_line(slide)

    add_text(slide,
        "276 segments (18%) score IS \u2265 4.0 \u2014 Excellent quality:",
        MX, CT, CW, Inches(0.40), size=Pt(24), color=LGRAY)

    tbl = add_table(slide,
        ["Reference", "Hypothesis", "WER", "IS"],
        [["health insurance company they pay for all "
          "the medications they pay for all your visits",
          "[exact match]", "0%", "5.0"],
         # audit:bigfonts — cut middle "so here we have ... one free" row
         # (verbatim-match example duplicating row 1's lesson).
         ["allow you to work with the team in a more "
          "productive efficient and effective manner",
          "allow you to work with a team and more "
          "productive efficient and effective manner", "14%", "4.6"]],
        MX, CT + Inches(0.55), CW, text_size=Pt(24),
        row_height=Inches(1.10),
        col_widths=[Inches(4.5), Inches(4.5), Inches(0.8), Inches(0.8)],
        row_colors={0: {3: GREEN}, 1: {3: GREEN}})

    # Key callout
    add_text(slide,
        "The system reads lips with high fidelity when visual signal is strong.",
        MX, CT + Inches(3.95), CW, Inches(0.45),
        size=Pt(24), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Stats
    # audit:bigfonts — cut bullet "Business/Finance topics dominate Tier 5"
    # (in speaker notes).
    add_bullets(slide, [
        "276 segments (18%) \u2014 the architecture works",
        "57% LLM Judge Y among Tier 5 \u2014 even the strictest agrees",
        ("Perfect transcription across 20\u201340 consecutive words \u2014 not luck",
         {"bold": True}),
    ], MX, CT + Inches(4.55), CW, Inches(2.0), size=Pt(24))

    _finish(slide, 0,
        "What good looks like: 276 segments (18%) achieve IS 4.0-5.0. "
        "Perfect word-for-word transcription over 20-40 consecutive words. "
        "The architecture works — the challenge is getting it to work "
        "consistently across all domains.",
        [[tbl]], click_reveal=True)


def slide_llm_context_engine(prs):
    """LLM as context engine — what it does and where to go."""
    # audit:bigfonts — no content cuts; layout accommodates bumps.
    slide = new_slide(prs)
    add_title(slide, "The LLM Is a Context Engine")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what the LLM does
    lt = add_text(slide, "What the LLM Does", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    add_text(slide, "The visual encoder sees mouth shapes.",
             MX, CT + Inches(0.6), col_w, Inches(0.3),
             size=Pt(24), color=WHITE)
    add_text(slide, "The LLM resolves ambiguity using language context.",
             MX, CT + Inches(1.0), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    lb = add_bullets(slide, [
        '"p/b/m" \u2192 Is it "pat," "bat," or "mat"?',
        "LLM uses surrounding words to disambiguate",
        "Stronger LLM = better disambiguation",
        ("This is why LLM quality matters more than size", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.0), size=Pt(24))

    # Right — current vs upgrade
    rx = MX + col_w + gap
    rt = add_text(slide, "Current vs Upgrade", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    # Current
    r1 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Current: LLaMA-2 7B", rx + Inches(0.2), CT + Inches(0.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=CORAL, bold=True)
    add_bullets(slide, [
        "32K vocab, 4K context",
        "2023 model, limited reasoning",
    ], rx + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24), bullet_color=CORAL)

    # Upgrade
    r2 = add_rect(slide, rx, CT + Inches(2.5), col_w, Inches(2.0),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Upgrade: Llama 3.1 8B", rx + Inches(0.2), CT + Inches(2.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=GREEN, bold=True)
    add_bullets(slide, [
        "128K vocab, 128K context",
        "Quality \u2248 LLaMA-2 70B",
        ("Same hidden_size (4096) = architecture-compatible upgrade", {"color": GREEN}),
        ("Setup: 2\u20134 weeks + retraining", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(3.0), col_w - Inches(0.4), Inches(1.2),
       size=Pt(24), bullet_color=GREEN)

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
    # audit:bigfonts — left summary table needs row_height bump for 18pt.
    slide = new_slide(prs)
    add_title(slide, "LLM Judge: Deep Dive")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — summary stats
    lt = add_text(slide, "30 Representative Segments", MX, CT, col_w, Inches(0.35),
                  size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Metric", "Value"],
        [["Segments", "30 (stratified sample)"],
         ["Mean WER", "61%"],
         ["Mean IS", "2.67 / 5.0"],
         ["LLM Judge: Y", "7  (23%)"],
         ["LLM Judge: P", "12  (40%)"],
         ["LLM Judge: N", "11  (37%)"],
         ["Y + P", "19  (63%)"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(24),
        row_height=Inches(0.55),
        col_widths=[Inches(2.0), Inches(3.5)],
        row_colors={3: {1: GREEN}, 5: {1: CORAL}, 6: {1: TEAL}})

    # Right — what this sample shows
    rx = MX + col_w + gap
    rt = add_text(slide, "What the Sample Reveals", rx, CT, col_w, Inches(0.35),
                  size=Pt(24), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Distribution mirrors the full 1,497-segment dataset",
         {"bold": True}),
        # audit:after_amosi_narrative_actions.md fix #14 - reorder-robust phrasing.
        ("6 videos in this section walk through these "
         "cases one by one", {"color": TEAL}),
    ], rx, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(24))

    # Bottom takeaway
    bk = add_text(slide,
        "Each video has burned-in subtitles showing reference (top) and "
        "hypothesis (bottom) \u2014 watch the lip movements and compare.",
        MX, Inches(6.40), CW, Inches(0.45),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "30-sample overview: stratified sample drawn from the 1,497-segment "
        "evaluation set. The 30-pair sample distribution matches the full "
        "dataset closely (Y=23% vs 23%, P=40% vs 42%, N=37% vs "
        "35%) and confirms the smaller deep-dive sample is representative. "
        "Mean WER 61% versus 64% on the full 1,497 segments; mean IS "
        "2.67 versus 2.547 on full. The interesting middle zone (IS 2.0-4.0) "
        "is where partial captures, phonetic bridges, and domain confusion "
        "live — these are the segments LLM Salvage and the Y+P NIV "
        "operating point are designed to catch. Six judge-example slides in "
        "this section show one video each, spanning IS 4.55 down to 1.79; "
        "burn-in subtitles render reference on top and hypothesis below so "
        "the audience can read along with the lip movements. Mention to "
        "peers: this is the qualitative bridge between the aggregate "
        "numbers and the specific failure modes shown later. "
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/llm_judge/.",
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

    audit:bigfonts — REF/HYP body at 18pt in 1.0" box accommodates 2-3
    short-line refs / hyps as currently authored. Annotation also at 18pt
    in 1.5" box (~5 lines). Six callers vetted: ex1-ex6 annotations are
    4-5 lines each. No content cuts to the 6 video example slides.
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
    # CUT v3 (overflow): grew 0.4 -> 0.85 so 24pt metrics text fits one line.
    mt = add_text(slide, metrics_text, rx, CT, rw, Inches(0.85),
                  size=Pt(24), color=badge_col, bold=True)

    # Reference — CUT v3: shrunk 24->20pt + h bumped 1.0->1.25.
    # audit:FONT_BELOW_24PT_BODY — REF/HYP frame heights tightened
    # 1.25->1.00 to free 0.50" of vertical space for the annotation bump
    # (20->24pt). REF/HYP keep 20pt (italic = caption-role per audit script).
    rl = add_text(slide, "Reference:", rx, CT + Inches(0.5), rw, Inches(0.25),
                  size=Pt(20), color=LGRAY, bold=True)
    # CUT v3 (overflow): grew 1.00 -> 1.70 so longer 20pt refs fit (2-line wrap).
    rt = add_text(slide, f"\u201c{ref}\u201d", rx, CT + Inches(0.75), rw, Inches(1.70),
                  size=Pt(20), color=WHITE, italic=True)

    # Hypothesis \u2014 CUT v3: shrunk 24->20pt + h bumped 1.0->1.25.
    # audit:FONT_BELOW_24PT_BODY \u2014 HYP shifted up 2.05->1.80 after REF tightening.
    hl = add_text(slide, "Prediction:", rx, CT + Inches(1.80), rw, Inches(0.25),
                  size=Pt(20), color=LGRAY, bold=True)
    # CUT v3 (overflow): grew 1.50 -> 1.75 so 4-line 20pt hyps fit.
    ht = add_text(slide, f"\u201c{hyp}\u201d", rx, CT + Inches(2.05), rw, Inches(1.75),
                  size=Pt(20), color=CORAL, italic=True)

    # Category badge — CUT v3: pushed down to 3.65 to follow bumped ref/hyp.
    # audit:FONT_BELOW_24PT_BODY — moved up 3.65->3.15 after REF/HYP tightening.
    cb = add_rect(slide, rx, CT + Inches(3.15), rw, Inches(0.70),
                  fill_color=NAVY3, corner_radius=True)
    # CUT v3 (overflow): grew 0.3 -> 0.7 for 20pt category text (often wraps).
    add_text(slide, category, rx + Inches(0.15), CT + Inches(3.17),
             rw - Inches(0.3), Inches(0.7),
             size=Pt(20), color=TEAL, bold=True)

    # Annotation — CUT v3: trimmed each caller's annotation to ~140 chars
    # (~5 short lines @ 20pt) so 20pt body fits in 1.50" frame without
    # overflowing the y=7.05 safe zone. Full narrative moved to speaker
    # notes (`notes` arg passed to _finish below).
    # audit:FONT_BELOW_24PT_BODY — bumped 20->24pt (body tier per audit);
    # frame grown 1.50->2.00" using space freed from REF/HYP tightening.
    # 5 short lines @ 24pt fits 2.0" frame (line height 0.40").
    at = add_text(slide, annotation, rx, CT + Inches(3.90), rw, Inches(1.70),
                  size=Pt(24), color=WHITE)

    _finish(slide, 0, notes,
            [[vid, mt], [rl, rt, hl, ht, cb, at]], click_reveal=True)


def slide_judge_ex1(prs):
    """Judge example 1: Named entity swap — bernreuter → rogers (IS 4.55)."""
    _judge_video_slide(prs,
        vid_key="judge_entity",
        title="Appendix: Judge Example — Named Entity Swap",
        ref="market research firm bernreuter research is "
            "forecasting pv installations could reach",
        hyp="market research firm rogers research is "
            "forecasting pv installations will reach",
        wer="18%", wwer="15%", is_score="4.55",
        is_tier="Excellent", judge="Y",
        category="Named Entity Swap — meaning fully preserved",
        # CUT v3: long narrative ("WER penalizes the name error equally
        # to any other word\u2026") moved into speaker notes below.
        annotation="Only company name changed (bernreuter \u2192 rogers) "
                   "and 'could' \u2192 'will'. Forecast captured; viewer "
                   "gets the full message.",
        notes="Named entity swap: 'bernreuter' becomes 'rogers' — visually "
              "similar lip patterns for proper nouns. WER is 18% on this "
              "segment, WWER 15% (the entity drops out at the same rate "
              "common words do here, so weighting barely moves WER). Despite "
              "18% WER, the core message about PV installation forecasts "
              "is fully preserved — only the company name is wrong, and the "
              "verb 'could' becomes 'will'. The LLM judge rates Y; IS is "
              "4.55, which sits in the Excellent tier. Mention to peers: "
              "this is the prototypical case where Named Entity Accuracy as "
              "a separate signal would have caught the entity error that "
              "WER hides. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/evaluation/intelligibility_methodology.md (NEA signal).")


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
        wer="48%", wwer="42%", is_score="3.69",
        is_tier="Good", judge="P",
        category="Truncation \u2014 beginning and end lost, core intact",
        # CUT v3: dropped "WER is 48% because of the missing words\u2026"
        # (in speaker notes); kept the core observation.
        annotation="Opening + trailing clauses lost. But the core "
                   "argument \u2014 1980s film companies bypassing "
                   "theatrical distribution \u2014 is captured verbatim.",
        notes="Truncation example. WER is 48%, WWER 42% — both numbers "
              "look like a clear failure if you stop at WER alone. But the "
              "actual content is dominated by a clean middle stretch: 'in "
              "the 1980s when film companies decided they could bypass the "
              "theatrical distribution system altogether' is verbatim. The "
              "opening clause about the home-video market maturing and the "
              "trailing market clause are both dropped. The LLM judge rates "
              "P (partial), and IS lands at 3.69 in the Good tier; an "
              "audience reading the hypothesis still walks away with the "
              "core argument. Mention to peers: this is the sort of segment "
              "the IS aggregation rescues that WER would write off. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/evaluation/intelligibility_methodology.md.")


def slide_judge_ex3(prs):
    """Judge example 3: Tech vocabulary drift — routers → roads (IS 3.02)."""
    _judge_video_slide(prs,
        vid_key="judge_router",
        title="Example 1: Technical Vocabulary Drift",
        ref="we need a radically different approach we basically "
            "need to find a way how we can take existing routers "
            "existing switches existing links and enable them for research",
        hyp="we need a radically different approach we must indeed "
            "find a way we can design existing roads to exist with "
            "existing structures and enable them for reuse",
        wer="52%", wwer="47%", is_score="3.02",
        is_tier="Good", judge="P",
        category="Domain Vocabulary Drift \u2014 structure intact, terms swapped",
        # audit:bigfonts — annotation trimmed (cut "Without domain context,
        # the model picks the most likely words" — in speaker notes).
        # CUT v3: kept structure observation; per-token mapping moved
        # to speaker notes.
        annotation="Argument structure perfect: 'radically different "
                   "approach' \u2192 'find a way' \u2192 'existing X' \u2192 "
                   "'enable for Y'. Networking terms become civil terms.",
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
        wer="43%", wwer="57%", is_score="2.67",
        is_tier="Fair", judge="P",
        category="Scientific Terms Lost \u2014 repetitive structure preserved",
        # CUT v3: dropped the WWER/WER comparison sentence (in speaker
        # notes); kept the structure-vs-vocabulary observation.
        annotation="'Tells us when to X' pattern preserved 3x. But "
                   "every scientific term is wrong: cortisol \u2192 turns, "
                   "testosterone \u2192 stops, light cycles \u2192 (gone).",
        notes="Scientific vocabulary destroyed: cortisol becomes 'turns', "
              "testosterone becomes 'stops', light cycles dropped entirely. "
              "But the repetitive rhetorical structure ('tells us when to X') "
              "is perfectly preserved. WWER > WER because high-value content "
              "words are wrong. LLM judge: P. IS 2.67 (Fair).")


def slide_judge_ex5(prs):
    """Judge example 5: Cooking domain confusion — jalapeno → banana (IS 2.07)."""
    _judge_video_slide(prs,
        vid_key="judge_jalapeno",
        title="Example 2: Cooking Domain Confusion",
        ref="and i have a tablespoon of jalapeno fresh jalapeno",
        hyp="and i have a dietary smoothie i've got the "
            "banana called fresh banana",
        wer="89%", wwer="44%", is_score="2.07",
        is_tier="Fair", judge="P",
        category="Domain Confusion \u2014 food context right, ingredients wrong",
        # CUT v3: dropped the multimodal-context sentence (in notes);
        # kept the food-domain-vs-ingredient observation.
        annotation="Model knows it's a cooking video ('smoothie', "
                   "'banana', 'fresh') but picks the wrong ingredient: "
                   "jalapeno \u2192 banana.",
        notes="Cooking domain confusion. WER is 89%, WWER drops to 44% "
              "because the rare entity 'jalapeno' is the dominant high-value "
              "token; once it is wrong, low-value words barely matter. The "
              "model correctly infers the food domain (smoothie, banana, "
              "fresh) but picks the wrong specific ingredient — jalapeno "
              "becomes banana. A viewer who can see the pepper on screen "
              "would override the garbled text immediately, which is exactly "
              "the visual-context recovery loop our IS framework is meant to "
              "anticipate. The LLM judge rates P; IS is 2.07, in the Fair "
              "tier. Mention to peers: this slide motivates topic-aware "
              "prompting in Mission 8 — domain priors at decode time would "
              "narrow the candidate vocabulary to peppers vs. fruits. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/prompts/ (Mission 8 design notes).")


def slide_judge_ex6(prs):
    """Judge example 6: Topic hijack — overhead lights → ghost whisperer (IS 1.79)."""
    _judge_video_slide(prs,
        vid_key="judge_lights",
        title="Example 3: Topic Hijack",
        ref="i actually use the overhead lights which are "
            "mostly fluorescent which i know is a big no no "
            "but this camera",
        hyp="i actually used the overheard ghost whisperer "
            "music for that scene which i know is about to "
            "go on but the scene runs",
        wer="74%", wwer="69%", is_score="1.79",
        is_tier="Poor", judge="P",
        category="Topic Hijack \u2014 grammatically fluent, completely wrong topic",
        # audit:bigfonts — annotation trimmed (cut "this is what makes
        # hallucinations dangerous" sentence — in speaker notes).
        # CUT v3: dropped the "phonetic cascade \u2026 wrong continuation"
        # detail (in notes); kept the topic-hijack observation.
        annotation="Phonetic cascade: 'overhead lights' \u2192 'overheard "
                   "ghost whisperer'. Grammatically perfect, but the "
                   "topic is completely replaced.",
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
    # audit:bigfonts — single full-width image; no body text to bump.
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge Report (30 Samples)")
    add_accent_line(slide)

    # Full-width report screenshot
    img = add_image(slide, "llm_judge_report", MX, CT, width=CW, height=Inches(5.4))

    _finish(slide, 0,
        "Screenshot of the interactive HTML report (30 stratified samples from "
        "1,497-segment dataset). Color-coded word diffs: green = match, "
        "yellow = substitution, red = insertion. Columns: WER, WWER, NEA F1, IS, "
        "LLM Judge verdict (Y/P/N). Distribution: Y=23%, P=40%, N=37%, "
        "Y+P=63%. Mean WER 61%, Mean IS 2.67/5.0.",
        [[img]])


# ═══════════════════════════════════════════════════════════════════════
# IS vs OPUS JUDGE DISAGREEMENT SLIDES
# ═══════════════════════════════════════════════════════════════════════

def slide_disagreement_blind(prs):
    """Where IS and the Judge Disagree — blind evaluation."""
    # audit:bigfonts — bumps fit existing 5.8x4.2 card layout; no trims.
    slide = new_slide(prs)
    add_title(slide, "Where IS and the Judge Disagree")
    add_accent_line(slide)

    # Subtitle
    sub = add_text(slide,
        "22 of 1,497 segments (2%) — rare but revealing edge cases",
        MX, CT, CW, Inches(0.35),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

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
        [("IS Too Harsh", {"size": Pt(24), "color": GREEN, "bold": True}),
         ("  \u2014  19 cases (1%)", {"size": Pt(24), "color": LGRAY})],
    ], MX + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(1.0)))

    left_shapes.append(add_text(slide,
        "Judge says Y (meaning conveyed)\nIS says < 3.0 (metric failure)",
        MX + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=LGRAY))

    # Example
    left_shapes.append(add_rect(slide,
        MX + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    left_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"one really nice thing about this is\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"what a brilliant idea this is\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("IS = 1.84  |  WER = 71%  |  Judge: Y",
          {"size": Pt(24), "color": LGRAY})],
    ], MX + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(2.6)))

    # OVERLAP fix: shrink italic textbox to h=0.45 (ends y=card_y+3.25),
    # leaving clean gap before the bullet list at y=card_y+3.3.
    left_shapes.append(add_text(slide,
        "Paraphrases and phonetic bridges preserve\n"
        "meaning that word-level metrics punish.",
        MX + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=GREEN, italic=True))

    # Also add remaining root causes
    left_shapes.append(add_text(slide,
        "\u2022 Harmless hallucination (extra words, core intact)\n"
        "\u2022 Short segments amplify WER disproportionately",
        MX + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(1.8),
        size=Pt(24), color=LGRAY))

    # RIGHT CARD — IS Too Generous (red border)
    right_shapes = []
    rx = MX + card_w + gap
    r_r = add_rect(slide, rx, card_y, card_w, card_h,
                   fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                   corner_radius=True)
    right_shapes.append(r_r)

    right_shapes.append(add_rich_text(slide, [
        [("IS Too Generous", {"size": Pt(24), "color": CORAL, "bold": True}),
         ("  \u2014  3 cases (0%)", {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(1.0)))

    right_shapes.append(add_text(slide,
        "Judge says N (meaning lost)\nIS says \u2265 3.0 (metric pass)",
        rx + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(1.0),
        size=Pt(24), color=LGRAY))

    # Example
    right_shapes.append(add_rect(slide,
        rx + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    right_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"all you have to do is unscrew\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"all you have to do is not to\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("IS = 3.42  |  WER = 29%  |  Judge: N",
          {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(2.6)))

    # OVERLAP fix (mirror of left card): shrink italic textbox to h=0.45.
    right_shapes.append(add_text(slide,
        "Structural match hides semantic reversal \u2014\n"
        "IS cannot detect that meaning is inverted.",
        rx + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=CORAL, italic=True))

    right_shapes.append(add_text(slide,
        "\u2022 Domain confusion (medical \u2192 wellness)\n"
        "\u2022 Word salad with scattered correct words",
        rx + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=LGRAY))

    # Bottom strip
    # CUT v3: top 6.35 -> 6.20 + frame h 1.0 -> 0.40 so Pt(24) bottom
    # stays under safe 7.05 (was 7.20).
    bot = add_text(slide,
        "98% agreement \u2014 disagreements are edge cases, not systemic failure",
        MX, Inches(6.02), CW, Inches(1.0),
        size=Pt(24), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS vs Opus Judge disagreement analysis (blind evaluation, all 1,497 "
        "pairs). Headline: 22 segments (2% of the corpus) sit in the "
        "disagreement region; 98% of the dataset agrees. The 22 "
        "split into 19 IS-too-harsh cases (judge Y, IS<2.00) and 3 "
        "IS-too-generous cases (judge N, IS>=2.00).\n\n"
        "LEFT — IS False Negatives (19 cases, 1%): paraphrases, phonetic "
        "bridges, and harmless hallucinations that preserve core meaning but "
        "score poorly on word-level signals. The headline left-card example "
        "('one really nice thing about this is' -> 'what a brilliant idea "
        "this is') sits at WER 71% / IS 1.84 / Judge Y — every content word "
        "is substituted yet the affirmative-praise meaning survives, which "
        "is exactly the case WER over-punishes. Additional examples: "
        "'living in space' topic preserved (IS 1.98, WER 111%); 'human "
        "implications' captures 'human application' (IS 2.06, WER 100%); "
        "'to the next level' intact with trailing words added (IS 2.32, "
        "WER 100%).\n\n"
        "RIGHT — IS False Positives (3 cases, 0%): semantic reversal "
        "('unscrew' -> 'not to', IS 3.42, WER 29% — structural match hides "
        "the meaning inversion); domain swap ('blood extraction, "
        "x-ray' -> 'cut hair, ashram', IS 3.14); phonetic garbage ('one "
        "twitch is all you do' -> 'one to rich is all the', IS 3.01). The "
        "operating thresholds in this slide are NIV-Y (IS>=3.80, kappa=0.690) "
        "and NIV-Y+P (IS>=2.00, kappa=0.816) calibrated against the same "
        "Opus judge.\n\n"
        "PEER DETAIL — 98% agreement = 1,466/1,497 segments fall in the "
        "same Y+P-vs-N bucket. The 22-segment disagreement region splits "
        "19 IS-too-harsh + 3 IS-too-generous.\n\n"
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/threshold_calibration_vs_opus.md.",
        [left_shapes, right_shapes, [bot]], click_reveal=True)


def slide_disagreement_context(prs):
    """Context makes the judge stricter — disagreement examples."""
    # audit:bigfonts — bumps fit existing layout; no trims.
    slide = new_slide(prs)
    add_title(slide, "Context Exposes Hidden Failures")
    add_accent_line(slide)

    # --- Left side: compact transition matrix ---
    left_w = Inches(5.5)

    lt = add_text(slide, "Blind \u2192 Context Transitions",
                  MX, CT, left_w, Inches(0.35),
                  size=Pt(24), color=TEAL, bold=True)

    # Transition matrix \u2014 starts right under the header (CT+0.40)
    tbl = add_table(slide,
        ["", "\u2192 Y", "\u2192 P", "\u2192 N"],
        [["Y (345)", "207", "138", "0"],
         ["P (626)", "17", "517", "92"],
         ["N (526)", "1", "50", "475"]],
        MX, CT + Inches(0.40), left_w, text_size=Pt(24),
        row_height=Inches(0.45),
        col_widths=[Inches(1.6), Inches(1.3), Inches(1.3), Inches(1.3)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Key stat \u2014 table ends at CT+0.40+4\u00d70.45=CT+2.20; stat starts at CT+2.40
    # giving 0.20" gap (empirical minimum from calibration audit).
    stat = add_rich_text(slide, [
        [("230 downgrades", {"size": Pt(24), "color": CORAL, "bold": True}),
         (" vs ", {"size": Pt(24), "color": WHITE}),
         ("68 upgrades", {"size": Pt(24), "color": GREEN, "bold": True})],
        [("Y\u2192P dominant (138): domain knowledge reveals vocabulary failures",
          {"size": Pt(24), "color": LGRAY})],
    ], MX, CT + Inches(2.40), left_w, Inches(0.95))

    # Bullets at CT+3.45 (0.10" after stat ends at CT+3.35).
    add_bullets(slide, [
        "80% stable across modes",
        ("Context tightens. 1 N\u2192Y rescue in all 1,497.",
         {"color": TEAL, "bold": True}),
    ], MX, CT + Inches(3.45), left_w, Inches(0.95), size=Pt(24))

    # --- Right side: killer example ---
    rx = MX + left_w + Inches(0.6)
    rw = CW - left_w - Inches(0.6)

    rt = add_text(slide, "The IS = 4.75 False Positive",
                  rx, CT, rw, Inches(0.35),
                  size=Pt(24), color=CORAL, bold=True)

    # Example card
    ex_card = []
    ex_r = add_rect(slide, rx, CT + Inches(0.5), rw, Inches(2.8),
                    fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                    corner_radius=True)
    ex_card.append(ex_r)

    ex_card.append(add_rich_text(slide, [
        [("IS = 4.75", {"size": Pt(24), "color": CORAL, "bold": True}),
         ("  (near perfect!)", {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.2), CT + Inches(0.6), rw - Inches(0.4), Inches(0.4)))

    ex_card.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"...because I'm ", {"size": Pt(24), "color": WHITE, "italic": True}),
         ("a lover of", {"size": Pt(24), "color": GREEN, "bold": True, "italic": True}),
         ("\"", {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"...because I'm ", {"size": Pt(24), "color": WHITE, "italic": True}),
         ("not a lover of", {"size": Pt(24), "color": CORAL, "bold": True, "italic": True}),
         ("\"", {"size": Pt(24), "color": WHITE, "italic": True})],
    ], rx + Inches(0.2), CT + Inches(1.15), rw - Inches(0.4), Inches(1.8)))

    # OVERLAP fix: shifted from CT+2.0 to CT+2.10 so it clears the REF/HYP
    # rich_text block above which ends at CT+2.05 (audit OVERLAP 6%).
    ex_card.append(add_text(slide,
        "One word reverses the meaning.\n"
        "IS rated this near-perfect \u2014 only 10% WER.\n"
        "Context-aware judge caught the negation.",
        rx + Inches(0.2), CT + Inches(2.10),
        rw - Inches(0.4), Inches(1.40),
        size=Pt(24), color=LGRAY))

    # C2 (research-overview pacing): "more context false positives" inline
    # list dropped from body \u2014 full list moved to speaker notes; appendix
    # A9 (Context Transition Matrix) shows the full structure.
    more = add_text(slide,
        "Full list of context false positives \u2014 see Appendix A9.",
        rx, CT + Inches(3.55), rw, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # Bottom strip
    # CUT v3: top 6.35 -> 6.20 + frame h 1.0 -> 0.40 so Pt(24) bottom
    # stays under safe 7.05.
    bot = add_text(slide,
        "Domain knowledge raises the bar \u2192 strongest case for domain-aware fine-tuning",
        MX, Inches(6.20), CW, Inches(0.55),
        size=Pt(24), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware disagreement analysis.\n\n"
        "LEFT: Transition matrix shows 230 downgrades vs 68 upgrades when "
        "the judge gains domain context. Y->P is dominant (138 cases). "
        "Context never rescues failures (only 1 N->Y in 1,497 pairs).\n\n"
        "RIGHT: The most striking false positive — IS = 4.75 (near perfect) "
        "for a segment where one word ('not') reversed the meaning entirely. "
        "WER on this segment is just 10% (single inserted word) and IS is "
        "4.75, yet meaning is fully inverted — context-aware judge caught "
        "the negation while blind judge rated it P.\n\n"
        "Additional context false positives show domain vocabulary swaps: "
        "hair care -> space (lazy natural -> lazy astronaut); "
        "knitting -> medical (needle -> neck, decreases -> skin grafting); "
        "US education -> international (student loan debt -> south korea, "
        "US marshals -> US marketers).\n\n"
        "These 11 context false positives (IS >= 3.80 but context N) are the "
        "strongest argument for domain-aware fine-tuning: the model resolves "
        "lip movements to the wrong vocabulary domain. Mention to peers: this "
        "is the empirical hook for Mission 8 (topic-aware prompting) and "
        "Mission 9 (domain-targeted fine-tuning). 80% of the 1,497 "
        "judgments are stable across both modes; the disagreement region is "
        "narrow but interpretable. "
        "Sources: docs/evaluation/llm_judge/context_eval/context_eval_analysis.md, "
        "docs/evaluation/llm_judge/llm_judge_analysis.md.",
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

    audit:bigfonts — bumps fit existing 5.8x4.2 card layout (verified line-
    counts at 18pt: 5 left bullets x ~1.5 lines = 7.5 lines = 2.0" in 2.55"
    box; right card 2 pairs at h=0.85 each = 0.54" content per pair).
    """
    slide = new_slide(prs)
    add_title(slide, "What the AVSR Literature Reports vs What Users Get")
    add_accent_line(slide)

    sub = add_text(slide,
        "AVSR / VSP papers (LRS3, LRW, AVSpeech) report WER almost exclusively. "
        "WER conflates failure modes a downstream user would never confuse.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

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
             Inches(0.4), size=Pt(24), color=TEAL, bold=True))
    # CUT v3: trimmed 5 long bullets to 4 short ones; removed CER /
    # BLEU detail and inlined the LRS3-numbers bullet — full list
    # remains in speaker notes. Frame height kept at 2.55".
    L.append(add_bullets(slide, [
        ("WER — primary metric in nearly every AVSR benchmark",
         {"bold": True}),
        "CER, BLEU/METEOR on side decks",
        ("Implicit: WER is monotone in usefulness", {"color": CORAL}),
        "Reported on LRS3: AV-HuBERT 25%, AutoAVSR 19%",
    ], MX + Inches(0.25), card_y + Inches(0.65),
       card_w - Inches(0.5), Inches(2.55), size=Pt(24)))
    # OVERLAP fix: bullets shrunk from h=3.0 to 2.55 (end y=card_y+3.20);
    # callout moved up from y=card_y+3.40 to 3.30 with h=0.65 (was 0.7).
    # CUT v3: shrunk callout to 20pt + tightened wording; full text
    # in speaker notes. Frame width unchanged.
    L.append(add_text(slide,
        "All three failure modes score the same WER if edit distance matches.",
        MX + Inches(0.25), card_y + Inches(3.30),
        card_w - Inches(0.5), Inches(0.65),
        size=Pt(20), color=CORAL, italic=True))

    # RIGHT - what users see
    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, card_y, card_w, card_h, fill_color=NAVY2,
                     border_color=GOLD, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "WHAT END USERS ACTUALLY CONSUME",
             rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=GOLD, bold=True))

    # Three example pairs - same WER ~50%, very different downstream value.
    # audit-md:section_C examples (judge_entity / judge_lights examples).
    R.append(add_text(slide, "Same WER ~50% - very different downstream value:",
             rx + Inches(0.25), card_y + Inches(0.65),
             card_w - Inches(0.5), Inches(1.0),
             size=Pt(24), color=WHITE, bold=True))

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
    # Each pair: label (h=0.3) + body (h=0.85) + stride 1.25.
    # Pair 2 starts card_y+2.30, pair 1 body ends card_y+2.20 — no overlap.
    py = card_y + Inches(1.05)
    for label, body, color in pairs:
        R.append(add_text(slide, label,
                 rx + Inches(0.25), py, card_w - Inches(0.5),
                 Inches(0.3), size=Pt(22), color=color, bold=True))
        R.append(add_text(slide, body,
                 rx + Inches(0.25), py + Inches(0.3),
                 card_w - Inches(0.5), Inches(0.85),
                 size=Pt(18), color=LGRAY))
        py += Inches(1.25)

    # CUT v3: shrunk callout 24->20pt to fit one line.
    R.append(add_text(slide,
        "Same WER, very different downstream value.",
        rx + Inches(0.25), card_y + card_h - Inches(0.55),
        card_w - Inches(0.5), Inches(0.87),
        size=Pt(20), color=GOLD, italic=True))

    # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
    # phrasing replaced with reorder-robust language.
    # CUT v3: shrunk 24->20pt + tightened phrasing so the bottom
    # callout fits in one line at y=6.5 without crossing the safe zone.
    bot = add_text(slide,
        "Therefore we built IS — the Intelligibility Score.",
        MX, Inches(6.5), CW, Inches(0.35),
        size=Pt(20), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Sources: docs/evaluation/after_amosi_audit.md (Section C, LLM-judge "
        "examples) and docs/evaluation/intelligibility_methodology.md "
        "(WER-IS dissociation). The point of this slide is to frame why we "
        "needed IS at all: the AVSR / VSP literature (LRS3, LRW, AVSpeech) "
        "reports WER almost exclusively (AV-HuBERT 25%, AutoAVSR 19% on "
        "LRS3), and WER conflates three downstream-distinct failure modes — "
        "gibberish, partial-but-useful, and fluent-hallucination. The "
        "bernreuter/rogers entity swap and the overhead-lights/"
        "ghost-whisperer topic hijack both score ~50% WER yet a downstream "
        "consumer treats them very differently — one is partially usable, the "
        "other actively misroutes every downstream tag. About 25% of "
        "segments in our 1,497-segment evaluation set fall into a band where "
        "WER and intelligibility actively disagree, which directly motivates "
        "the Intelligibility Score introduced in the next subsection.",
        [[sub], L, R, [bot]], click_reveal=True)


