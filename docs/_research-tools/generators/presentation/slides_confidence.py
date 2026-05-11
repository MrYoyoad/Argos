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


# Confidence + N-best slides (split from slides_evaluation.py May 2026)

def slide_confidence_problem(prs):
    """v13: How Do You Know When to Trust an Output?

    Four colored bullets (white-bold, green-bold, teal-bold, white-regular)
    + green-bordered validation callout box.
    """
    slide = new_slide(prs)
    add_title(slide, "How Do You Know When to Trust an Output?")
    add_accent_line(slide)

    bul = add_bullets(slide, [
        ("Most ASR systems hand you a transcript. You read all of it. "
         "If something’s wrong, you find out the hard way.",
         {"bold": True}),
        ("Argos is different. Every word and every segment carries a "
         "confidence signal.",
         {"color": GREEN, "bold": True}),
        ("You read what’s flagged — not everything. The system tells you "
         "which parts are reliable and which need a second look.",
         {"color": TEAL, "bold": True}),
        ("Two layers: per-word probabilities surfaced as inline color, "
         "plus a per-segment trust score. We explain both next.", {}),
    ], MX, CT + Inches(0.2), CW, Inches(4.2), size=Pt(24))

    box_y = Inches(4.85)
    box_h = Inches(1.30)
    box_w = Inches(9.5)
    box_x = MX + (CW - box_w) / 2
    rect = add_rect(slide, box_x, box_y, box_w, box_h,
                    fill_color=NAVY2, border_color=GREEN,
                    border_width=Pt(2), corner_radius=True)
    callout = add_text(slide,
        "Validated: 82% agreement with an independent blind evaluator on\n"
        "1,497 real-world segments",
        box_x + Inches(0.3), box_y + Inches(0.20),
        box_w - Inches(0.6), box_h - Inches(0.3),
        size=Pt(22), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Section 4 opener (v13). Frame: Argos surfaces confidence so the "
        "user reads what's flagged. Two layers (per-word softmax + per-"
        "segment trust score) explained on the following slides. 82% "
        "agreement with blind Opus judge on 1,497 segments.",
        [[bul], [rect, callout]], click_reveal=True)


def slide_two_layer_confidence_research(prs):
    """v13: Two layers of confidence — per-word + per-segment, side-by-side
    columns (no card backgrounds), with a small green callout and a centered
    bottom note.
    """
    slide = new_slide(prs)
    add_title(slide, "Two Layers of Confidence")
    add_accent_line(slide)

    col_w = Inches(6.00)
    gap_ = Inches(0.13)
    top = CT + Inches(0.0)

    # Left column - per-word
    x1 = MX
    L = []
    L.append(add_text(slide, "1. PER-WORD",
             x1, top, col_w, Inches(0.45),
             size=Pt(24), color=TEAL, bold=True))
    L.append(add_text(slide, "p(t)  =  maxv  P( v | tokens <= t )",
             x1, top + Inches(0.45), col_w, Inches(0.45),
             size=Pt(20), color=GOLD, italic=True))
    L.append(add_bullets(slide, [
        ("Every predicted word carries the model's own probability",
         {"bold": True}),
        "Surfaced inline as BLUE (trust) / ORANGE (review) / PURPLE (avoid)",
        ("You see exactly where the model was unsure - read the colors, "
         "not the whole text", {}),
        ("23,261 words across 1,427 segments - every word gets a color",
         {"color": BLUE}),
        ("Numbers and named entities cap at ORANGE - always verify "
         "against video",
         {"color": GREEN, "bold": True}),
    ], x1, top + Inches(1.05), col_w, Inches(3.10), size=Pt(18)))

    # Green-bordered callout below left bullets
    cb_y = top + Inches(4.30)
    cb_w = Inches(5.5)
    cb_h = Inches(0.65)
    cb_rect = add_rect(slide, x1, cb_y, cb_w, cb_h,
                       fill_color=NAVY2, border_color=GREEN,
                       border_width=Pt(2), corner_radius=True)
    cb_t = add_text(slide, "Confidence is triage - not truth",
                    x1 + Inches(0.3), cb_y + Inches(0.10),
                    cb_w - Inches(0.6), cb_h - Inches(0.2),
                    size=Pt(20), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    # Right column - per-segment
    x2 = MX + col_w + gap_
    R = []
    R.append(add_text(slide, "2. PER-SEGMENT",
             x2, top, col_w, Inches(0.45),
             size=Pt(24), color=CORAL, bold=True))
    R.append(add_text(slide, "m  =  exp( (1/T) . Sum_t  log p(t) )",
             x2, top + Inches(0.45), col_w, Inches(0.45),
             size=Pt(20), color=GOLD, italic=True))
    R.append(add_bullets(slide, [
        ("Word probabilities aggregate to one trust score per segment", {}),
        ("Plus a length-anomaly check - too short or too long for the "
         "visual frames is flagged", {}),
        ("Thresholds:  t_safe = 0.82 (default)  .  t_trust = 0.89  .  "
         "t_salvage = 0.74  .  strip < 0.65", {"color": LGRAY}),
        ("Each segment lands in TRUST, SALVAGE, or STRIP - next slide", {}),
        ("Thresholds are calibrated, not arbitrary - validated against "
         "blind reviewer",
         {"color": GREEN, "bold": True}),
    ], x2, top + Inches(1.05), col_w, Inches(3.50), size=Pt(18)))

    bot = add_text(slide,
        "Both layers free - derived from the existing decode pass. "
        "No retraining, no new infrastructure.",
        MX, Inches(6.40), CW, Inches(0.50),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "v13 framing. Left: per-word from softmax. Right: per-segment from "
        "mean log-prob with length-anomaly check. Thresholds calibrated "
        "against blind Opus judge. Both extracted from the same decode "
        "pass - zero extra cost.",
        [L, [cb_rect, cb_t], R, [bot]], click_reveal=True)


def slide_per_word_confidence_distribution(prs):
    """v13: Joint Rule vs Legacy - horizontal bar comparison.

    Two side-by-side cards (LEGACY/JOINT) each containing 3 horizontal
    bars (GREEN/YELLOW/RED) with counts and %. Bottom 3-column summary
    showing greens drop / reds double / each green more reliable.
    """
    slide = new_slide(prs)
    add_title(slide, "Joint Rule vs Legacy: How Band Counts Shifted")
    add_accent_line(slide)

    sub = add_text(slide,
        "Adding beam-agreement (α ≥ 0.80) on top of conf (p₁ ≥ 0.95) "
        "reassigns ~30% of words from green to red.  "
        "Greens that survive are more reliable.",
        MX, CT, CW, Inches(0.45),
        size=Pt(15), color=LGRAY, italic=True)

    # Two cards
    card_w = Inches(5.85)
    gap_ = Inches(0.43)
    cy = CT + Inches(0.65)
    card_h = Inches(4.40)

    def _draw_card(x, title, title_color, rule_text, bands_data):
        """Returns list of shapes for one card."""
        shapes = []
        shapes.append(add_rect(slide, x, cy, card_w, card_h,
                               fill_color=NAVY2, border_color=title_color,
                               border_width=Pt(2), corner_radius=True))
        shapes.append(add_text(slide, title,
                 x + Inches(0.20), cy + Inches(0.15),
                 card_w - Inches(0.4), Inches(0.40),
                 size=Pt(20), color=title_color, bold=True,
                 align=PP_ALIGN.CENTER))
        shapes.append(add_text(slide, rule_text,
                 x + Inches(0.20), cy + Inches(0.60),
                 card_w - Inches(0.4), Inches(0.40),
                 size=Pt(13), color=LGRAY, italic=True,
                 align=PP_ALIGN.CENTER))
        # 3 horizontal bars
        bar_x = x + Inches(1.4)
        bar_max_w = card_w - Inches(1.8)
        bar_h = Inches(0.40)
        by = cy + Inches(1.20)
        bar_gap = Inches(0.55)
        for i, (lbl, value, pct, color) in enumerate(bands_data):
            yy = by + i * bar_gap
            # label on left
            shapes.append(add_text(slide, lbl,
                     x + Inches(0.20), yy + Inches(0.05),
                     Inches(1.15), bar_h - Inches(0.10),
                     size=Pt(14), color=color, bold=True,
                     align=PP_ALIGN.RIGHT))
            # value above bar
            shapes.append(add_text(slide, f"{value:,}  ({pct}%)",
                     bar_x, yy - Inches(0.25),
                     bar_max_w, Inches(0.30),
                     size=Pt(13), color=WHITE, bold=True,
                     align=PP_ALIGN.LEFT))
            # bg track
            shapes.append(add_rect(slide, bar_x, yy, bar_max_w, bar_h,
                                   fill_color=NAVY3, border_color=None,
                                   corner_radius=True))
            # filled bar
            fill_w = int(bar_max_w * pct / 50.0)
            if fill_w < Inches(0.05):
                fill_w = Inches(0.05)
            shapes.append(add_rect(slide, bar_x, yy, fill_w, bar_h,
                                   fill_color=color, border_color=None,
                                   corner_radius=True))
        return shapes

    legacy = _draw_card(
        MX, "LEGACY", LGRAY,
        "rule:  p₁ ≥ 0.95  (conf only)",
        [("GREEN",  11309, 49, GREEN),
         ("YELLOW",  7470, 32, GOLD),
         ("RED",     4482, 19, CORAL)])

    joint = _draw_card(
        MX + card_w + gap_, "JOINT (production)", TEAL,
        "rule:  p₁ ≥ 0.95  AND  α ≥ 0.80",
        [("GREEN",   7591, 33, GREEN),
         ("YELLOW",  6571, 28, GOLD),
         ("RED",     9099, 39, CORAL)])

    # Bottom: 3-column summary
    sum_y = cy + card_h + Inches(0.20)
    sum_w = CW / 3
    sum_items = [
        ("Greens drop", "11,309 → 7,591  (-33%)", GREEN),
        ("Reds double", "4,482 → 9,099  (+103%)", CORAL),
        ("Each green more reliable", "P(correct):  81% → 90%", TEAL),
    ]
    bot_group = []
    for i, (head, body, color) in enumerate(sum_items):
        sx = MX + i * sum_w
        bot_group.append(add_text(slide, head,
                 sx, sum_y, sum_w, Inches(0.30),
                 size=Pt(15), color=color, bold=True,
                 align=PP_ALIGN.CENTER))
        bot_group.append(add_text(slide, body,
                 sx, sum_y + Inches(0.30), sum_w, Inches(0.35),
                 size=Pt(13), color=WHITE,
                 align=PP_ALIGN.CENTER))

    _finish(slide, 0,
        "v13 layout: two cards (LEGACY left, JOINT production right) each "
        "showing 3 horizontal bars (GREEN/YELLOW/RED). Headline: greens "
        "drop 33% under the joint rule (11,309 -> 7,591), reds roughly "
        "double (4,482 -> 9,099), but green reliability rises 81% -> 90%. "
        "Sources: docs/evaluation/after_amosi_audit.json (Section D).",
        [[sub], legacy, joint, bot_group], click_reveal=True)


def slide_band_reliability_overall(prs):
    """Overall P(correct | band) under joint rule vs legacy."""
    # audit:bigfonts — take_t trimmed; row_height for 20pt cells = 0.65.
    slide = new_slide(prs)
    add_title(slide, "Band Reliability - Overall P(correct | band)")
    add_accent_line(slide)

    sub = add_text(slide,
        "P(correct) of each band, computed by aligning hypothesis tokens "
        "to reference text via Levenshtein. Joint rule's green is the "
        "biggest gain.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["Band", "JOINT P(correct)", "LEGACY P(correct)", "Delta"]
    rows = [
        # audit:perword_new_green_p_correct vs perword_old_green_p_correct
        ["Green",  "90%", "81%",  "+9.2pp"],
        ["Yellow", "59%", "38%",  "+20.7pp"],
        ["Red",    "22%", "15%",  "+6.3pp"],
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
                    text_size=Pt(24), row_colors=row_colors)

    # OVERLAP fix: shrink take rect from h=2.0 to h=1.5 (ends y=CT+4.9 = 6.35)
    # and take_t text from h=1.7 to h=1.25 so the takeaway ends well above
    # the bottom audit-source line at y=6.5.
    take = add_rect(slide, MX, CT + Inches(3.4), CW, Inches(1.5),
                    fill_color=NAVY2, border_color=BLUE, border_width=Pt(2),
                    corner_radius=True)
    # audit:bigfonts — take_t shortened to fit 1.25" box at 20pt; the
    # cut clause about the legacy yellow band reclassification is kept in
    # the speaker notes (already present) for the spoken story.
    take_t = add_text(slide,
        "Joint rule's biggest gain is in GREEN: 90% vs 81% (+9.2pp).  "
        "Yellow lift (+20.7pp) reflects band relocations rather than a "
        "true gain.",
        MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
        Inches(1.25), size=Pt(24), color=WHITE)

    # Pass 3 (audit:opus_overall_footer_overlap): rect ended at y=6.35
    # but bot text started at y=6.22, overlapping the bottom rect border.
    # Pushed bot down to 6.45 (rect ends 6.35) and reduced h to 0.55.
    bot = add_text(slide,
        "All numbers from audit JSON keys perword_{new,old}_{green,yellow,red}_p_correct. "
        "Total 23,261 words.",
        MX, Inches(6.45), CW, Inches(0.55),
        size=Pt(16), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Overall per-word band reliability across the full 23,261-word "
        "corpus (1,427 segments). Computed by Levenshtein-aligning each "
        "hypothesis token to the reference and asking whether the colored "
        "band predicts that match. Under the joint rule: P(correct|green) "
        "= 90%, P(correct|yellow) = 59%, P(correct|red) = 22%. Under "
        "the legacy conf-only rule: 81% / 38% / 15%. The joint "
        "rule's headline win is GREEN going from 81% to 90% reliable "
        "(+9.2 pp); the larger absolute shift in YELLOW (+20.7 pp) "
        "reflects band relocations rather than a true reliability gain — "
        "the legacy yellow band was collecting high-conf-but-disagreed "
        "tokens that the joint rule reroutes to red. Mention to peers: "
        "the Strip policy below segment mean_prob 0.65 (covered later in "
        "this section) is computed independently of these overall numbers, "
        "and its purpose is to handle segments where even the green band "
        "is unreliable. "
        "Sources: docs/evaluation/after_amosi_audit.json (Section D), "
        "docs/confidence/band_reliability_by_niv.md.",
        [[sub, tbl], [take, take_t], [bot]], click_reveal=True)


def slide_band_reliability_stratified(prs):
    """v13: Green Reliability vs Segment Quality - the 0.65 cliff.

    Left column: two stat-boxes (86% green-bordered above-cliff, 41%
    red-bordered below-cliff). Right column: table of m-bin -> P(green
    correct) -> note. Bottom italic: 'Strip boundary at m < 0.65 isn't
    arbitrary - it's where green reliability falls below 50%.'
    """
    slide = new_slide(prs)
    add_title(slide, "Green Reliability vs Segment Quality — the 0.65 Cliff")
    add_accent_line(slide)

    sub = add_text(slide,
        "P(green word correct) stratified by segment confidence  m.  "
        "Green is reliable above 0.65, falls off a cliff below.",
        MX, CT, CW, Inches(0.40),
        size=Pt(16), color=LGRAY, italic=True)

    # Left column: two big stat boxes
    col_w = Inches(5.0)
    box_h = Inches(1.85)
    box_gap = Inches(0.20)
    by1 = CT + Inches(0.65)
    by2 = by1 + box_h + box_gap

    L = []
    # Green-bordered: 86% above-cliff
    L.append(add_rect(slide, MX, by1, col_w, box_h,
                      fill_color=NAVY2, border_color=GREEN,
                      border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "86%",
             MX + Inches(0.25), by1 + Inches(0.35),
             Inches(2.0), Inches(1.20),
             size=Pt(60), color=GREEN, bold=True, align=PP_ALIGN.CENTER))
    L.append(add_text(slide, "just above the boundary",
             MX + Inches(2.35), by1 + Inches(0.25),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(14), color=LGRAY, italic=True))
    L.append(add_text(slide, "m = 0.65 – 0.75",
             MX + Inches(2.35), by1 + Inches(0.65),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(16), color=WHITE, bold=True))
    L.append(add_text(slide, "P(green correct) holds.",
             MX + Inches(2.35), by1 + Inches(1.05),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(14), color=LGRAY))

    # Red-bordered: 41% below-cliff
    L.append(add_rect(slide, MX, by2, col_w, box_h,
                      fill_color=NAVY2, border_color=CORAL,
                      border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "41%",
             MX + Inches(0.25), by2 + Inches(0.35),
             Inches(2.0), Inches(1.20),
             size=Pt(60), color=CORAL, bold=True, align=PP_ALIGN.CENTER))
    L.append(add_text(slide, "just below the boundary",
             MX + Inches(2.35), by2 + Inches(0.25),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(14), color=LGRAY, italic=True))
    L.append(add_text(slide, "m = 0.55 – 0.65",
             MX + Inches(2.35), by2 + Inches(0.65),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(16), color=WHITE, bold=True))
    L.append(add_text(slide, "P(green correct) collapses.",
             MX + Inches(2.35), by2 + Inches(1.05),
             col_w - Inches(2.5), Inches(0.40),
             size=Pt(14), color=LGRAY))

    # Right column: stratification table
    rx = MX + col_w + Inches(0.30)
    rw = CW - col_w - Inches(0.30)
    headers = ["m bin", "P(green correct)", "note"]
    rows = [
        ["m  ≥ 0.85",      "96%", "above strip"],
        ["m  0.75 – 0.85",  "92%", ""],
        ["m  0.65 – 0.75",  "86%", "↑ above boundary"],
        ["m  0.55 – 0.65",  "41%", "↓ below boundary — strip"],
        ["m  0.40 – 0.55",  "22%", ""],
        ["m  < 0.40",       "18%", ""],
    ]
    row_colors = {
        0: {1: GREEN},
        1: {1: GREEN},
        2: {1: GREEN, 2: GREEN},
        3: {1: CORAL, 2: CORAL},
        4: {1: CORAL},
        5: {1: CORAL},
    }
    tbl = add_table(slide, headers, rows,
                    rx, CT + Inches(0.65), rw,
                    row_height=Inches(0.45),
                    col_widths=[Inches(2.0), Inches(2.0), Inches(3.13)],
                    text_size=Pt(13), row_colors=row_colors,
                    bold_cols=[1])

    bot = add_text(slide,
        "Strip boundary at  m < 0.65  isn’t arbitrary — it’s where "
        "green reliability falls below 50%. Above the cliff: trustworthy. "
        "Below: misleading.",
        MX, Inches(6.55), CW, Inches(0.40),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "v13 layout: two stat boxes (86% above-cliff, 41% below-cliff) + "
        "right-side stratification table. Strip boundary at m < 0.65 is "
        "where P(green correct) drops below 50%. Sources: "
        "docs/evaluation/after_amosi_audit.json (Section D), "
        "docs/confidence/band_reliability_by_niv.md.",
        [[sub]] + [L] + [[tbl]] + [[bot]], click_reveal=True)


def slide_green_leakage_examples(prs):
    """v13: Green Leakage - When High Confidence Misleads.

    Three cards (red/red/yellow) showing REFERENCE -> HYPOTHESIS pairs
    where the model emitted a green-band word that was wrong. Bottom
    teal-bordered callout describes the production response.
    """
    slide = new_slide(prs)
    add_title(slide, "Green Leakage — When High Confidence Misleads")
    add_accent_line(slide)

    sub = add_rich_text(slide,
        [[
            ("2,192 wrong-and-green words across 23,261  (",
             {"color": LGRAY, "italic": True, "size": Pt(16)}),
            ("9% leakage rate",
             {"color": CORAL, "italic": True, "bold": True, "size": Pt(16)}),
            (").  Numerics and entities concentrate the danger.",
             {"color": LGRAY, "italic": True, "size": Pt(16)}),
        ]],
        MX, CT, CW, Inches(0.45))

    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(4.20)
    gap_ = Inches(0.3)
    cy = CT + Inches(0.55)

    examples = [
        ("NUMERIC SCALE FLIP", CORAL,
         '"1 ', "billion", ' CFUs of probiotics"',
         '"1 ', "million", ' CFUs of probiotics"',
         "P(billion → million) = 0.965",
         "Off by 1000×.  Confident, fluent, wrong."),
        ("NUMERIC DIGIT DROP", CORAL,
         '"the value is ', "1024", '"',
         '"the value is ', "24", '"',
         "P(1024 → 24) = 0.958",
         "Tokeniser mis-merge. The model never saw it as a 4-digit number."),
        ("YEAR DRIFT", GOLD,
         '"in ', "2011", ' the project began"',
         '"in ', "2000", ' the project began"',
         "P(2011 → 2000) = 0.894",
         "Visually similar mouth shapes — the visemes don’t disambiguate."),
    ]

    cards = []
    for i, (title_, color, ref_pre, ref_key, ref_post,
            hyp_pre, hyp_key, hyp_post, conf_, note) in enumerate(examples):
        x = MX + i * (card_w + gap_)
        c = []
        c.append(add_rect(slide, x, cy, card_w, card_h,
                          fill_color=NAVY2, border_color=color,
                          border_width=Pt(2), corner_radius=True))
        c.append(add_text(slide, title_,
                 x + Inches(0.2), cy + Inches(0.15),
                 card_w - Inches(0.4), Inches(0.40),
                 size=Pt(14), color=color, bold=True, align=PP_ALIGN.CENTER))

        # REFERENCE label
        c.append(add_text(slide, "REFERENCE",
                 x + Inches(0.2), cy + Inches(0.65),
                 card_w - Inches(0.4), Inches(0.30),
                 size=Pt(10), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))
        c.append(add_rich_text(slide, [[
            (ref_pre, {"color": WHITE, "size": Pt(14)}),
            (ref_key, {"color": GREEN, "bold": True, "size": Pt(14)}),
            (ref_post, {"color": WHITE, "size": Pt(14)}),
        ]], x + Inches(0.2), cy + Inches(0.95),
           card_w - Inches(0.4), Inches(0.55)))

        # HYPOTHESIS label
        c.append(add_text(slide, "HYPOTHESIS  (model painted GREEN)",
                 x + Inches(0.2), cy + Inches(1.65),
                 card_w - Inches(0.4), Inches(0.30),
                 size=Pt(10), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))
        c.append(add_rich_text(slide, [[
            (hyp_pre, {"color": WHITE, "size": Pt(14)}),
            (hyp_key, {"color": CORAL, "bold": True, "size": Pt(14)}),
            (hyp_post, {"color": WHITE, "size": Pt(14)}),
        ]], x + Inches(0.2), cy + Inches(1.95),
           card_w - Inches(0.4), Inches(0.55)))

        # conf (gold bold)
        c.append(add_text(slide, conf_,
                 x + Inches(0.2), cy + Inches(2.70),
                 card_w - Inches(0.4), Inches(0.45),
                 size=Pt(14), color=GOLD, bold=True, align=PP_ALIGN.CENTER))

        # note (italic gray)
        c.append(add_text(slide, note,
                 x + Inches(0.2), cy + Inches(3.25),
                 card_w - Inches(0.4), Inches(0.85),
                 size=Pt(11), color=LGRAY, italic=True))
        cards.append(c)

    # Bottom teal-bordered callout under the 3 cards.
    bot_card = []
    bot_card.append(add_rect(slide, MX, Inches(6.55), CW, Inches(0.55),
                             fill_color=NAVY2, border_color=TEAL,
                             border_width=Pt(2), corner_radius=True))
    bot_card.append(add_rich_text(slide, [[
        ("Production response:  ", {"color": BLUE, "bold": True, "size": Pt(13)}),
        ("numbers and named entities are CAPPED at YELLOW under the joint "
         "rule, regardless of model confidence.",
         {"color": WHITE, "size": Pt(13)}),
    ]], MX + Inches(0.20), Inches(6.62), CW - Inches(0.4), Inches(0.40),
       align=PP_ALIGN.CENTER))

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
    # audit:bigfonts — op rect h up + bot strip pushed (see inline).
    slide = new_slide(prs)
    add_title(slide, "Three Calibrated Confidence Thresholds (per-segment)")
    add_accent_line(slide)

    # audit:after_amosi_narrative_actions.md fix #13 - first visible NIV
    # mention is in this slide's table, so the subtitle now glosses it
    # once for the audience: "NIV = Native Intelligibility Verdict (the
    # LLM-as-Judge calibration label, NIV-Y / NIV-P / NIV-N)".
    sub = add_text(slide,
        "NIV = Native Intelligibility Verdict (LLM-as-Judge label).",
        MX, CT, CW, Inches(0.45),
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["Threshold", "m cutoff", "Green band reliable?", "Notes"]
    rows = [
        ["τ_trust",   ">= 0.89", ">= 90%", "highest precision, lowest recall"],
        ["τ_safe",    ">= 0.82", ">= 85%", "F1-max for NIV-Y on m"],
        ["τ_salvage", ">= 0.74", ">= 75%", "review zone"],
        ["Strip below", "< 0.65",  "< 50%",  "drop word colour here"],
    ]
    row_colors = {
        0: {0: BLUE,   2: BLUE},
        1: {0: GREEN,  2: GREEN},
        2: {0: ORANGE, 2: ORANGE},
        3: {0: PURPLE, 2: PURPLE},
    }
    # col_widths sum exactly to CW=12.13" so LibreOffice doesn't rescale.
    # col2 at 1.90" (eff 1.60") fits "m cutoff" in 1 line at 24pt.
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.30), Inches(1.90), Inches(3.20),
                                Inches(4.73)],
                    text_size=Pt(24), row_colors=row_colors)

    # audit:bigfonts2 — op rect h shrunk 1.95 -> 1.65, bullets h 1.30 -> 1.05
    # to clear bot footer + slide-num zone.
    op = []
    op.append(add_rect(slide, MX, CT + Inches(3.45), CW, Inches(1.65),
                       fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                       corner_radius=True))
    op.append(add_text(slide, "τ_safe (m ≥ 0.82) — operational default",
             MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
             Inches(0.40), size=Pt(24), color=GREEN, bold=True))
    op.append(add_bullets(slide, [
        "Keeps 28% volume; IS_kept = 4.01",
        "WER_kept = 28%; Precision 71%; Recall 79% (NIV-Y)",
    ], MX + Inches(0.3), CT + Inches(4.00),
       CW - Inches(0.6), Inches(1.00), size=Pt(24)))

    # audit:bigfonts2 — bot pushed back to 6.55 (was 6.75 → bottom 7.15
    # overlapped slide-num); op rect ends at CT+3.2+1.95 = 6.60. Now 6.55+0.40
    # = 6.95 ≤ 7.05. CUT v2: shortened text to fit smaller box.
    bot = add_text(slide,
        "Thresholds are Llama-2-7b specific; LLM swap = re-fit needed.",
        MX, Inches(6.60), CW, Inches(0.40),
        size=Pt(20), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Three calibrated thresholds on segment mean_prob, plus a "
        "strip-coloring boundary. T_trust at >= 0.89 (green is at least "
        "90% reliable; highest precision, lowest recall). T_safe at >= "
        "0.82 (green is at least 85% reliable; F1-max for NIV-Y class on "
        "mean_prob — this is the operational default in the production UI: "
        "keeps 28% of segment volume, IS_kept = 4.01, WER_kept = 28%, "
        "precision 71% and recall 79% on NIV-Y). T_salvage at >= 0.74 "
        "(green is at least 75% reliable; review zone). Below mean_prob "
        "0.65, even the green band is <50% reliable, so the production "
        "UI strips word colouring entirely on those segments. All four "
        "thresholds are Llama-2-7b specific; an LLM swap forces "
        "re-running diagnose_confidence_signals.py and re-fitting the "
        "operating points.\n\n"
        "PEER DETAIL — T_safe = 0.82 chosen as F1-max for class NIV-Y on "
        "`mean_prob`: sweep T from 0.50 to 0.95 in 0.01 steps; predictor = "
        "`mean_prob >= T`; label = judge-Y; pick argmax F1. "
        "Sources: docs/confidence/band_reliability_by_niv.md, "
        "docs/confidence/three_thresholds.md.",
        [[sub, tbl], op, [bot]], click_reveal=True)


def slide_three_tier_policy_research(prs):
    """Trust / Salvage / Strip operating-points table - research version."""
    # audit:bigfonts — table 7-col layout with Pt(24) cells; row_height 0.55
    # accommodates. Bullets in left/right columns at 18pt fit existing 2.5
    # boxes (3 left bullets + 4 right bullets, both ~5-6 lines each).
    slide = new_slide(prs)
    add_title(slide, "Per-Tier Reliability - What the Numbers Say")
    add_accent_line(slide)

    col_w = Inches(5.85)
    gap_ = Inches(0.43)

    # Left column: Threshold Calibration (2 stacked boxes)
    L = []
    L.append(add_text(slide, "The Threshold Calibration",
             MX, CT, col_w, Inches(0.40),
             size=Pt(22), color=CORAL, bold=True))

    box1_y = CT + Inches(0.55)
    box1_h = Inches(2.30)
    b1 = add_rect(slide, MX, box1_y, col_w, box1_h,
                  fill_color=NAVY2, border_color=TEAL,
                  border_width=Pt(2), corner_radius=True)
    b1_t = add_text(slide, "Three Cuts on the Per-Segment Score",
                    MX + Inches(0.25), box1_y + Inches(0.15),
                    col_w - Inches(0.5), Inches(0.40),
                    size=Pt(18), color=TEAL, bold=True)
    b1_b = add_bullets(slide, [
        ("t_trust  =  0.89  ->  precision-first: 90%+ green-word reliability",
         {"color": BLUE}),
        ("t_safe  =  0.82  ->  operational default: 85%+ reliability, F1-max",
         {"color": GREEN, "bold": True}),
        ("t_salvage  =  0.74  ->  recall zone: 75%+ reliability, review needed",
         {"color": ORANGE}),
    ], MX + Inches(0.25), box1_y + Inches(0.60),
       col_w - Inches(0.5), Inches(1.65), size=Pt(15))
    L.extend([b1, b1_t, b1_b])

    box2_y = box1_y + box1_h + Inches(0.20)
    box2_h = Inches(1.60)
    b2 = add_rect(slide, MX, box2_y, col_w, box2_h,
                  fill_color=NAVY2, border_color=GREEN,
                  border_width=Pt(2), corner_radius=True)
    b2_t = add_text(slide, "How We Picked the Cuts",
                    MX + Inches(0.25), box2_y + Inches(0.10),
                    col_w - Inches(0.5), Inches(0.40),
                    size=Pt(18), color=GREEN, bold=True)
    b2_b = add_bullets(slide, [
        ("Each cut maximizes a different objective on a held-out blind judge", {}),
        ("Re-fit on every LLM swap - thresholds are model-specific",
         {"bold": True}),
    ], MX + Inches(0.25), box2_y + Inches(0.55),
       col_w - Inches(0.5), Inches(1.00), size=Pt(15))
    L.extend([b2, b2_t, b2_b])

    # Right column: Reliability Table
    rx = MX + col_w + gap_
    R = []
    R.append(add_text(slide, "The Reliability Table",
             rx, CT, col_w, Inches(0.40),
             size=Pt(22), color=CORAL, bold=True))
    R.append(add_text(slide,
        "P(correct) by tier x band  -  23,261 words / 1,427 segments",
        rx, CT + Inches(0.45), col_w, Inches(0.35),
        size=Pt(14), color=WHITE, bold=True))

    headers = ["", "GREEN", "YELLOW", "RED"]
    rows = [
        ["TRUST\n>= 0.82",    "95%\nn = 3,923", "76%\nn = 1,719", "42%\nn = 951"],
        ["SALVAGE\n0.65-0.82","89%\nn = 3,091", "60%\nn = 3,241", "28%\nn = 3,442"],
        ["STRIP\n< 0.65",     "56%\nn = 577",   "38%\nn = 1,611", "13%\nn = 4,706"],
    ]
    row_colors = {
        0: {0: BLUE,   1: GREEN, 2: GOLD,  3: CORAL},
        1: {0: ORANGE, 1: GREEN, 2: GOLD,  3: CORAL},
        2: {0: PURPLE, 1: GREEN, 2: GOLD,  3: CORAL},
    }
    tbl = add_table(slide, headers, rows,
                    rx, CT + Inches(0.85), col_w,
                    row_height=Inches(0.60),
                    col_widths=[Inches(1.55), Inches(1.45),
                                Inches(1.45), Inches(1.40)],
                    text_size=Pt(13), row_colors=row_colors)
    R.append(tbl)

    R.append(add_text(slide,
        "TRUST greens are 95% reliable. STRIP greens drop to 56% - "
        "that's why STRIP hides coloring.",
        rx, CT + Inches(3.40), col_w, Inches(0.55),
        size=Pt(13), color=LGRAY, italic=True))

    R.append(add_text(slide,
        "Stratified by judge verdict (within useful Y+P content):\n"
        "BLUE words: 87% correct  /  ORANGE: 49%  /  PURPLE: 25%\n"
        "62-point spread blue->purple within the same segments - "
        "the per-word band carries real information.",
        rx, CT + Inches(4.05), col_w, Inches(1.55),
        size=Pt(13), color=WHITE))

    _finish(slide, 0,
        "Three-tier policy table — Trust / Salvage / Strip — with raw "
        "counts and per-band reliability values from the joint-rule "
        "diagnostic. Trust tier (segment mean_prob >= 0.82): green = "
        "95% reliable on 3,923 words, yellow 76% on 1,719, red 42% "
        "on 951 — auto-approve threshold. Salvage tier (0.65 - 0.82): "
        "green 89% on 3,091, yellow 60% on 3,241, red 28% on 3,442 "
        "— pair with a human reviewer. Strip tier (< 0.65): green is "
        "only 56% on 577 words, yellow 38% on 1,611, red 13% on "
        "4,706 — at this quality the green flag actively misleads, so "
        "the UI drops word colouring entirely. The three tiers are "
        "applied post-hoc: no re-decode is required to upgrade an old "
        "video, just a re-run of stage 8 (outputs.sh::run_outputs). "
        "Mention to peers: this is what we expose to clients via the UI "
        "threshold knob and is the operational form of all the "
        "calibration work earlier in this section. "
        "Sources: docs/evaluation/after_amosi_audit.json (Section D, "
        "by_tier block), docs/confidence/band_reliability_by_niv.md.",
        [L, R], click_reveal=True)


def slide_band_reliability_by_niv(prs):
    """P(correct | band) within Y+P, stratified by NIV-Y/P/N."""
    # audit:bigfonts — left plot fixed-size; right column take bullets
    # at 18pt in h=2.05 fit cleanly.
    slide = new_slide(prs)
    add_title(slide, "Per-Word Bands Stratified by NIV Outcome")
    add_accent_line(slide)

    sub = add_text(slide,
        "Within useful content (Y+P), per-word band carries strong "
        "information about correctness - 62.5pp green->red spread.",
        MX, CT, CW, Inches(0.45),
        size=Pt(18), color=LGRAY, italic=True)

    # OVERLAP fix (#334): img h 4.60 -> 4.25 so img bottom = 6.20, leaving
    # 0.02" gap before bot strip top=6.22; previously bot strip overlapped
    # img by 0.33". Sub h 0.80 -> 0.45 so sub bottom 1.90 < img top 1.95.
    # Pass 3 (audit:opus_niv_overlap): right column at rw=2.93" was
    # cramped at Pt(24); table cells wrapped (rw/4 ~0.73"). Reduce
    # img w 9.0->8.5 to free 0.5" for right column (rw 2.93->3.43");
    # narrow-col exemption ≤4" allows Pt(20) here.
    img = add_image(slide, "P_band_reliability_by_niv",
                    MX, CT + Inches(0.5),
                    width=Inches(8.5), height=Inches(4.25))
    rx = MX + Inches(8.7)
    rw = CW - Inches(8.7)
    rt = add_text(slide, "P(correct | band)",
                  rx, CT + Inches(0.5), rw, Inches(0.3),
                  size=Pt(20), color=TEAL, bold=True)

    # Pass 3 final: "NIV-N" 5 chars at Pt(20) wrapped in 0.86" tier col.
    # Drop to Pt(16) and shorten tier col content.
    headers = ["Tier", "GRN", "YEL", "RED"]
    rows = [
        ["Y+P",  "87%", "49%", "25%"],
        ["Y",    "94%", "65%", "39%"],
        ["P",    "80%", "41%", "20%"],
        ["N",    "37%", "17%",  "7%"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(16), row_height=Inches(0.4))

    # Pass 3 fixup: rendered table ends ~CT+3.0 (header rows wrap).
    # Push bullets to CT+3.20.
    take = add_bullets(slide, [
        ("62.5pp green→red spread in Y+P", {"bold": True, "color": GREEN}),
        ("NIV-P: steepest (80/41/20%)", {"color": ORANGE}),
        ("NIV-N: green misleads (37%)", {"color": PURPLE}),
    ], rx, CT + Inches(3.20), rw, Inches(1.80), size=Pt(16))

    # CUT v3: top 6.55 -> 6.40 so Pt(18) wrap stays under safe 7.05.
    bot = add_text(slide,
        "Per-word flag is genuine signal inside Salvage tier, not decoration. "
        "Source: docs/confidence/band_reliability_by_niv.md.",
        MX, Inches(6.22), CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/confidence/band_reliability_by_niv.md "
        "(audit-md:band_reliability_by_niv) - audit JSON does NOT carry "
        "per-NIV-tier band reliabilities (no band_by_niv_yp_* keys in "
        "after_amosi_audit.json; would be useful to add). Plot: "
        "P_band_reliability_by_niv.png. Within Y+P (useful content): "
        "P(correct | green/yellow/red) = 87% / 49% / 25%, with "
        "62.5pp spread. NIV-P shows the steepest gradient (80/41/20%), "
        "which is why per-word flag is most valuable in the Salvage "
        "tier. NIV-N green is only 37% reliable - confirms strip policy.",
        [[sub, img], [rt, tbl, take], [bot]], click_reveal=True)


def slide_agreement_aware_bands(prs):
    """Definition of joint conf+agreement band rule (May 2 2026)."""
    # audit:bigfonts — 3 band cards each (label 28pt + defn 18pt) fit in
    # 2.4" height; why-rect 18pt fits in 1.5"; bot at 6.55.
    slide = new_slide(prs)
    add_title(slide, "Joint Confidence + Beam-Agreement Band Rule")
    add_accent_line(slide)

    sub = add_text(slide,
        "Production rule. Two axes: p₁ (per-token softmax max) "
        "AND α (beam-agreement fraction across n-best).",
        MX, CT, CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True)

    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(2.4)
    gap = Inches(0.3)
    cy = CT + Inches(0.6)

    bands = [
        ("GREEN", BLUE,
         "p₁ ≥ 0.95  AND  α ≥ 0.80"),
        ("YELLOW", ORANGE,
         "p₁ ≥ 0.65  AND  α ≥ 0.50"),
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
                 Inches(0.4), size=Pt(28), color=color, bold=True,
                 align=PP_ALIGN.CENTER))
        g.append(add_text(slide, defn,
                 x + Inches(0.2), cy + Inches(0.85), card_w - Inches(0.4),
                 Inches(1.8), size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER))
        band_groups.append(g)

    # OVERLAP fix: shrink why-rect from h=2.0 to h=1.5 (ends y=CT+4.9 = 6.35)
    # and inner text from h=1.7 to h=1.25 so the "why agreement" block ends
    # cleanly above the bottom Llama-caveat strip at y=6.55 (was y=6.50).
    why = []
    why.append(add_rect(slide, MX, CT + Inches(3.4), CW, Inches(1.5),
                        fill_color=NAVY3, border_color=GOLD,
                        border_width=Pt(1.5), corner_radius=True))
    why.append(add_text(slide,
        # audit:after_amosi_logic_fixes.md fix #6 - prior copy said
        # "P(correct) 0.62 -> 0.94 (32pp gap)" which was the conf>=0.65
        # bin. At top1_conf>=0.95 (the green-band threshold), the actual
        # P(correct) range is 0.40 -> 0.94 = 54pp. Source:
        # english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md Test C.
        # OVERLAP fix (#336): inner-text h 1.65 -> 1.20 so bot=5.00+1.20=6.20
        # ≤ rect bot 6.35, no longer overlapping bot strip at y=6.45.
        "WHY ADD AGREEMENT?  Beam agreement is ~2× more informative than "
        "top-1 conf at high conf — at conf ≥ 0.95, agreement spread takes "
        "P(correct) from 0.40 → 0.94 (54pp gap).",
        MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
        Inches(1.20), size=Pt(24), color=WHITE))

    # CUT v4: shorten to one line at Pt(24) so bottom = 6.45 + 0.50 = 6.95 <= 7.05.
    bot = add_text(slide,
        "Llama-2-7b specific — LLM swap requires re-fitting cuts.",
        MX, Inches(6.45), CW, Inches(0.50),
        size=Pt(24), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

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
        "re-running the diagnostic.\n\n"
        "PEER DETAIL — beam_agreement(token, position) = fraction of the "
        "20 n-best hypotheses that emit the same word at that position "
        "after MBR alignment. Joint band thresholds (top1_conf >= 0.95, "
        "beam_agreement >= 0.80) chosen by sweep maximizing P(correct | "
        "green) at fixed coverage. Llama-2-7b specific.",
        [[sub]] + band_groups + [why, [bot]], click_reveal=True)


def slide_agreement_vs_conf_information(prs):
    """v13: Beam Agreement Adds Independent Signal - two-column research layout."""
    slide = new_slide(prs)
    add_title(slide, "Beam Agreement Adds Independent Signal")
    add_accent_line(slide)

    col_w = Inches(5.85)
    gap_ = Inches(0.43)

    # Left: The Two Trust Signals
    L = []
    L.append(add_text(slide, "The Two Trust Signals",
             MX, CT, col_w, Inches(0.40),
             size=Pt(22), color=CORAL, bold=True))

    s1_y = CT + Inches(0.55)
    s1_h = Inches(2.30)
    L.append(add_rect(slide, MX, s1_y, col_w, s1_h,
                      fill_color=NAVY2, border_color=TEAL,
                      border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "Signal 1: Top-1 Confidence",
             MX + Inches(0.25), s1_y + Inches(0.15),
             col_w - Inches(0.5), Inches(0.40),
             size=Pt(16), color=TEAL, bold=True))
    L.append(add_bullets(slide, [
        ("The probability the model assigned to the chosen word at this "
         "position", {}),
        ("Limitation: softmax can be sharp by accident, not by "
         "certainty — two populations hide in \"conf ≥ 0.95\"",
         {"bold": True}),
    ], MX + Inches(0.25), s1_y + Inches(0.60),
       col_w - Inches(0.5), Inches(1.65), size=Pt(13)))

    s2_y = s1_y + s1_h + Inches(0.20)
    s2_h = Inches(2.20)
    L.append(add_rect(slide, MX, s2_y, col_w, s2_h,
                      fill_color=NAVY2, border_color=GREEN,
                      border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "Signal 2: Beam Agreement",
             MX + Inches(0.25), s2_y + Inches(0.15),
             col_w - Inches(0.5), Inches(0.40),
             size=Pt(16), color=GREEN, bold=True))
    L.append(add_bullets(slide, [
        ("Of the 20 beam hypotheses, what fraction picked this same word "
         "at this position?", {}),
        ("Independent of softmax shape — measures whether the model’s "
         "alternatives agreed", {"bold": True}),
    ], MX + Inches(0.25), s2_y + Inches(0.60),
       col_w - Inches(0.5), Inches(1.55), size=Pt(13)))

    # Right: The 54-Point Gap
    rx = MX + col_w + gap_
    R = []
    R.append(add_text(slide, "The 54-Point Gap at conf ≥ 0.95",
             rx, CT, col_w, Inches(0.40),
             size=Pt(22), color=CORAL, bold=True))
    R.append(add_text(slide,
        "Same top-1 confidence. Different beam agreement. Very different "
        "reliability.\nBeam agreement is ~2× more discriminative than "
        "softmax alone in this band.",
        rx, CT + Inches(0.45), col_w, Inches(0.95),
        size=Pt(13), color=WHITE, bold=True))

    headers = ["", "agreement ≥ 0.80", "agreement < 0.80"]
    rows = [
        ["P(correct)", "94%",    "40%"],
        ["UI band",    "BLUE",   "downgraded to ORANGE"],
    ]
    row_colors = {
        0: {1: GREEN, 2: CORAL},
        1: {1: BLUE,  2: ORANGE},
    }
    tbl = add_table(slide, headers, rows,
                    rx, CT + Inches(1.50), col_w,
                    row_height=Inches(0.45),
                    col_widths=[Inches(1.85), Inches(2.0), Inches(2.0)],
                    text_size=Pt(13), row_colors=row_colors)
    R.append(tbl)

    R.append(add_text(slide, "The Joint Rule (Production Default)",
             rx, CT + Inches(2.95), col_w, Inches(0.35),
             size=Pt(15), color=TEAL, bold=True))
    R.append(add_text(slide,
        "BLUE = top-1 conf ≥ 0.95  AND  beam agreement ≥ 0.80\n"
        "ORANGE = top-1 conf ≥ 0.65  AND  beam agreement ≥ 0.50\n"
        "PURPLE = otherwise. Numbers and named entities are CAPPED at "
        "ORANGE regardless.",
        rx, CT + Inches(3.30), col_w, Inches(1.30),
        size=Pt(12), color=WHITE))

    R.append(add_text(slide,
        "Effect of joint rule:  BLUE words 11,309 → 7,591 (33% downgraded)  "
        "|  reliability 81% → 90%",
        rx, CT + Inches(4.70), col_w, Inches(0.50),
        size=Pt(12), color=LGRAY))

    _finish(slide, 0,
        "v13 layout: left column 'The Two Trust Signals' (top-1 conf + beam "
        "agreement) explains the independent axes. Right column 'The "
        "54-Point Gap at conf>=0.95' shows the 0.94/0.40 contingency, plus "
        "the Joint Rule production defaults. Sources: "
        "english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md "
        "(Test C); docs/confidence/lessons_learned_band_rule_v2.md.",
        [L, R], click_reveal=True)


def slide_client_trust_calibration(prs):
    """Trust gate operating points - ROC-style table."""
    # audit:bigfonts — table 6-col Pt(24) row_height 0.5 fits.
    slide = new_slide(prs)
    add_title(slide, "Trust-Gate Operating Points (per-segment)")
    add_accent_line(slide)

    sub = add_text(slide,
        "Per-segment trust gate based on fraction-of-green-words. n=1,427 "
        "(70 empty-output segments excluded; see audit anomaly note).",
        MX, CT, CW, Inches(0.7),
        size=Pt(18), color=LGRAY, italic=True)

    # All from audit Section E new_rule_joint_conf_agreement
    # sub h increased 0.5->0.7 to hold 2 lines; table shifted to CT+0.75.
    # Col6 header shortened from "% clearly conveyed in trust" (wraps in 2.7")
    # to "% Y+P in trust" (fits in 2.7" eff=2.4" at 24pt bold).
    headers = ["Threshold", "n trusted", "Recall", "Precision", "FPR",
               "% Y+P in trust"]
    rows = [
        # audit:trustgate_new_t10_*
        ["fraction-green >= 10%", "1,041", "92%", "82%", "37%", "34%"],
        # audit:trustgate_new_t20_*
        ["fraction-green >= 20%",   "818", "81%", "91%", "14%", "43%"],
        # audit:trustgate_new_t30_*
        ["fraction-green >= 30%",            "630", "65%", "96%",  "6%", "52%"],
        # audit:trustgate_new_t50_*
        ["fraction-green >= 50%",   "321", "34%", "97%",  "2%", "72%"],
        # audit:trustgate_new_t70_*
        ["fraction-green >= 70%",    "71",  "8%", "99%",  "0%", "89%"],
    ]
    row_colors = {
        2: {0: BLUE, 1: BLUE, 2: GREEN, 3: GREEN, 4: GREEN, 5: GREEN},
    }
    # col2 widened 1.4->1.6 so "n trusted" (bold 24pt ≈ 1.16") fits in
    # eff=1.3" without wrapping and expanding the header row.
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.75), CW, row_height=Inches(0.5),
                    col_widths=[Inches(3.5), Inches(1.6), Inches(1.4),
                                Inches(1.7), Inches(1.4), Inches(2.5)],
                    text_size=Pt(24), row_colors=row_colors)

    pick = add_text(slide,
        "Recommended default: 30% green words -> 65% recall, 6% FPR. "
        "Pick higher thresholds for mission-critical workflows; lower for "
        "high-recall research workflows.",
        MX, CT + Inches(3.85), CW, Inches(1.1),
        size=Pt(24), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    # CUT v3: top 6.5 -> 6.30 + h 0.8 -> 0.55 + trimmed so Pt(18) bottom
    # stays under safe 7.05 (was 7.30). Audit-key list moved to notes.
    bot = add_text(slide,
        "Calibrated under joint conf+agreement rule.",
        MX, Inches(6.45), CW, Inches(0.55),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section E "
        "(new_rule_joint_conf_agreement) + "
        "docs/confidence/client_trust_calibration.md. Operating-point "
        "ROC-style table on the per-segment trust gate. n=1,427 "
        "(per_segment_safety.csv, 70 empty-output segments excluded; "
        "see audit anomaly note about denominator difference between "
        "per-segment safety and full IS distribution). Recommended "
        "default at fraction-of-green >= 30%: 65% recall, 6% FPR. "
        "Audit JSON keys: trustgate_new_t30_recall, "
        "trustgate_new_t30_fpr, trustgate_new_t30_precision, "
        "trustgate_new_t30_pct_clearly_conveyed.\n\n"
        "PEER DETAIL — Operating points from sweeping fraction-of-green "
        "thresholds (10%, 20%, 30%, ...) over NIV-Y+P target labels on "
        "n=1,427 non-empty segments. Recall = TP / (TP + FN) on Y+P "
        "labels; FPR = FP / (FP + TN) on judge-N labels. >=30% green is "
        "the F1-max operating point we ship.",
        [[sub, tbl], [pick], [bot]], click_reveal=True)


def slide_nbest_v3_judge_paired_tests(prs):  # audit:bigfonts2
    """N-best v3 judge paired-test results.

    audit:bigfonts2 — Pass 2: take bullets 4 -> 3 (drop "Y tied" — also in
    table); take h 2.85 -> 1.85; bot footer moved to y=6.55. take bottom 6.30
    < bot top 6.55 < bot bottom 6.95 ≤ slide-num zone.
    """
    slide = new_slide(prs)
    add_title(slide, "N-best Aggregation: v3 Judge Paired Tests")
    add_accent_line(slide)

    sub = add_text(slide,
        "Opus 4.7 dual-conf prompt, blind, 5,988 verdicts (1,497 segments x "
        "4 methods). McNemar paired vs baseline (top-1).",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # Left column — paired-test plot stacked above the regenerated
    # P_method_comparison plot (IS distribution per method). The original
    # paired plot was 6.5" x 4.5" (filled the column); shrunk to 6.5" x
    # 2.4" so the new comparison plot fits below at 6.5" x 2.0".
    img = add_image(slide, "P_v3_judge_paired",
                    MX, CT + Inches(0.6),
                    width=Inches(6.5), height=Inches(2.3))
    img_methods = add_image(slide, "P_method_comparison",
                            MX, CT + Inches(3.0),
                            width=Inches(6.5), height=Inches(1.7))
    # audit:remark_326 — caption at T=6.20 H=0.80 BOT=7.00 was overlapping
    # the run-label footer at T=6.55 (0.45" overlap, "text misplaced").
    # Caption is one line of 18pt italic text -> height 0.30 sufficient.
    # New: T=6.20 H=0.30 BOT=6.50, 0.05" gap before footer at T=6.55.
    cap_methods = add_text(slide,
        "Below: IS distribution per method (top1 / MBR / vote_score / vote_conf).",
        MX, CT + Inches(4.75), Inches(6.5), Inches(0.30),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    rx = MX + Inches(6.7)
    rw = CW - Inches(6.7)

    # "YP McNemar" (10 chars) fits in 2.10" col; "p" dropped (implied by McNemar).
    # "0.149 n.s." (10 chars) fits; "(n.s.)" paren form was borderline in 2.10".
    headers = ["Method", "Y%", "YP%", "McNemar-p"]
    rows = [
        # audit:judge_v3_y_pct_baseline / _yp_pct_baseline
        ["baseline",    "13%", "68%", "-"],
        # audit:judge_v3_y_pct_mbr / _yp_pct_mbr / mcnemar_yp_p_mbr
        ["hyp_mbr",     "14%", "71%", "0.00017***"],
        # audit:judge_v3_y_pct_vote_score / _yp_pct_vote_score
        # Short name (no hyp_) so 10 chars fit in 1.83" col at 24pt without wrapping.
        ["vote_score",  "14%", "69%", "0.149(ns)"],
        # audit:judge_v3_y_pct_vote_conf / _yp_pct_vote_conf / mcnemar_yp_p_vote_conf
        ["vote_conf",   "12%", "70%", "0.00257**"],
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
    # OVERLAP fix v4: Y% and Y+P% cols were 0.75" (effective 0.45") — exactly at
    # the 3-char limit for "13%"/"14%"/"12%" at 24pt, causing LibreOffice to wrap
    # and expand rows. Widened to 0.85" (effective 0.55") for comfortable fit.
    # Last col trimmed 2.10"→1.90" (effective 1.60") — "YP McNemar" (10 chars,
    # 1.50") fits. P-value strings had spaces removed (e.g. "0.00017 ***" →
    # "0.00017***") so they can't word-wrap regardless of col width.
    # Total cols: 1.83+0.85+0.85+1.90 = 5.43" = rw ✓
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.6), rw,
                    text_size=Pt(24), row_height=Inches(0.5),
                    col_widths=[Inches(1.83), Inches(0.85), Inches(0.85),
                                Inches(1.90)],
                    row_colors=row_colors)

    # audit:bigfonts2 — V6: 4 -> 3 bullets, each <=8 words, h 1.60.
    # OVERLAP fix v2: moved y 3.15->3.40 (0.30" gap from table end CT+3.10);
    # method names shortened to vote_score/vote_conf so rows don't wrap at 24pt.
    # CUT v2: dropped "Y verdict tied" (already in the McNemar table).
    take = add_bullets(slide, [
        ("Beam aggregation: +40 useful wins, p=0.00017",
         {"color": GREEN, "bold": True}),
        ("vote_conf +31 Y+P wins, p=0.00257",
         {"color": GREEN}),
        ("v3 drift 12-14% (v1: 27%)", {"color": TEAL}),
    ], rx, CT + Inches(3.40), rw, Inches(1.60), size=Pt(24))

    # audit:after_amosi_narrative_actions.md fix #8 - explicit run-label
    # footer so this v3 dual-conf judge run (Opus 4.7, 5,988 verdicts on
    # n-best methods) is not conflated with the v1 blind judge slide
    # earlier in the section (Opus 4.6, 1,497 pairs). Bumped to 12pt for
    # readability floor; "audit keys: judge_v3_*, mcnemar_yp_p_{mbr,
    # vote_score,vote_conf}, section_F_llm_judge_v3" tail moved to speaker
    # notes (kept verbatim there).
    # audit:bigfonts2 — bot moved 6.85 -> 6.55 to clear slide-num zone (7.12).
    bot = add_text(slide,
        "v3 dual-conf judge  /  Opus 4.7  /  5,988 verdicts on n-best methods",
        MX, Inches(6.55), CW, Inches(0.35),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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
        "Identical-text drift dropped from v1's 27% to 12.6-14% in v3 "
        "(audit:_note_drift) thanks to the dual-conf prompt anchor. "
        "5,988 total verdicts. "
        "Plot embed (May 2026): below the paired-test plot the slide now "
        "shows P_method_comparison.png — IS distribution per method "
        "(top1 / MBR / vote_score / vote_conf). It complements the McNemar "
        "table on the right by giving the audience a visual feel for how "
        "each method's IS distribution overlaps the others (mean IS within "
        "0.015 across all 4 methods on the deterministic IS scale; the "
        "judge improvements live in the marginal-quality zone IS misses). "
        "The original paired plot was shrunk from 6.5\"x4.5\" to "
        "6.5\"x2.4\" to make room. "
        "Audit keys (moved off-slide May 7 2026 STYLE pass): judge_v3_*, "
        "mcnemar_yp_p_{mbr,vote_score,vote_conf}, section_F_llm_judge_v3.\n\n"
        "PEER DETAIL — MBR posterior per word ~ exp of MBR's normalized "
        "log-prob over the 20 n-best candidates conditioned on the chosen "
        "hypothesis; averaged over all words, mean = 0.867. Voting methods "
        "(vote_conf, vote_score) emit agreement scores in narrow [0.4, "
        "0.8] which don't map onto the band-reliability thresholds; this "
        "is why MBR was chosen as the production default. Identical-text "
        "drift = % of method-method paired runs where both methods emit "
        "the same text yet the judge gives different verdicts (intra-rater "
        "noise floor); 27% under v1 dropped to 12-14% under v3 dual-conf.",
        [[sub, img, img_methods, cap_methods], [tbl, take], [bot]],
        click_reveal=True)


def slide_mbr_decision(prs):  # audit:bigfonts2
    """Why MBR over voting (decision summary).

    audit:bigfonts2 — Pass 2 BLOCKER fix: dec rect h shrunk 2.7 -> 1.85
    (was overflowing to y=7.75); bullets trimmed 3 -> 2 (italic 'Hybrid
    gate' line moved to speaker notes); table row_height tightened
    0.5 -> 0.42; sub text trimmed to one line.
    """
    slide = new_slide(prs)
    add_title(slide, "Why Beam Aggregation Outperforms Single-Pass")
    add_accent_line(slide)

    # CUT v2: shortened sub-text from 3 lines -> 1.
    sub = add_text(slide,
        "Beam aggregation wins on reliability + confidence calibration.",
        MX, CT, CW, Inches(0.45),
        size=Pt(20), color=LGRAY, italic=True)

    headers = ["Criterion", "hyp_mbr", "hyp_vote_conf", "Winner"]
    rows = [
        # audit:mcnemar_yp_p_*
        ["Y+P paired McNemar p",   "0.00017",     "0.00257",      "both significant"],
        # audit:mcnemar_yp_method_only_*
        ["Y+P win delta",          "+40",         "+31",          "MBR"],
        # audit:judge_v3_intrarater_exact_*
        ["Intra-rater (exact)",    "87%",       "80%",        "MBR (gold std 83%)"],
        ["Per-word posterior",     "calibrated",  "agreement [0.4-0.8]", "MBR"],
        ["Compatible with bands",  "yes",         "narrow range",  "MBR"],
    ]
    row_colors = {
        2: {1: GREEN, 3: GREEN},
        3: {1: GREEN, 3: GREEN},
        4: {1: GREEN, 3: GREEN},
    }
    # audit:bigfonts2 — row_height tightened 0.5 -> 0.42 to give the dec
    # rect more clearance; table now ends at CT + 0.55 + 6*0.42 = CT + 3.07.
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.42),
                    col_widths=[Inches(3.5), Inches(2.5), Inches(3.0),
                                Inches(3.13)],
                    text_size=Pt(20), row_colors=row_colors)

    # audit:bigfonts2 — dec rect h 2.7 -> 1.80; trimmed to 2 bullets.
    # CUT v2: removed italic "Hybrid gate rejected" bullet (moved to speaker
    # notes); rect ends at CT + 3.30 + 1.80 = CT + 5.10 = 6.55, well under
    # slide-num zone at 7.12.
    dec = []
    dec.append(add_rect(slide, MX, CT + Inches(3.30), CW, Inches(1.80),
                        fill_color=NAVY2, border_color=BLUE, border_width=Pt(2),
                        corner_radius=True))
    dec.append(add_text(slide, "DECISION - ship pure hyp_mbr as default displayed output",
             MX + Inches(0.3), CT + Inches(3.40), CW - Inches(0.6),
             Inches(0.40), size=Pt(24), color=BLUE, bold=True))
    dec.append(add_bullets(slide, [
        ("MBR mean per-word conf 0.867 — compatible with band thresholds",
         {"color": WHITE}),
        ("Vote methods emit narrow agreement [0.4, 0.8] — not band-compatible",
         {"color": WHITE}),
    ], MX + Inches(0.3), CT + Inches(3.85),
       CW - Inches(0.6), Inches(1.10), size=Pt(24)))

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json Section F "
        "intra_rater + MEMORY n_best_aggregation_findings entry + "
        "docs/beam-search/n_best_implementation.md. Both MBR and "
        "vote_conf pass the v3 judge significance bar (Y+P McNemar "
        "p=0.00017 and 0.00257). MBR wins on (a) higher intra-rater "
        "exact agreement (87% vs 80%, matches gold-standard top-1 "
        "83%) and (b) calibrated per-word posterior compatible with "
        "the band-reliability thresholds; voting methods emit agreement "
        "scores in [0.4, 0.8] that don't map to T_trust/T_safe/T_salvage. "
        "Hybrid gating considered and rejected (+36 vs +37 = one rescue). "
        "Default ship: pure hyp_mbr. Wired via make_report.py "
        "--display-method (default top1 for back-compat); lib/outputs.sh "
        "defaults to hyp_mbr when aggregated.json exists; override via "
        "VSP_DISPLAY_METHOD env.",
        [[sub, tbl], dec], click_reveal=True)


def slide_v1_vs_v3_judge_lesson(prs):
    """Dual-conf prompt design lesson — v13 source-match layout."""
    slide = new_slide(prs)
    add_title(slide, "v1 vs v3 Judge: A Prompt-Design Lesson")
    add_accent_line(slide)

    sub = add_rich_text(slide, [[
        ("Same n-best methods.  Same judge model.  Different prompt.  ",
         {"size": Pt(16), "color": LGRAY, "italic": True}),
        ("Opposite conclusions.",
         {"size": Pt(16), "color": LGRAY, "italic": True, "bold": True}),
    ]], MX, CT, CW, Inches(0.4))

    card_w = Inches(5.85)
    gap = Inches(0.4)
    cy = CT + Inches(0.5)
    ch = Inches(4.20)

    # ============ LEFT CARD (BROKEN / v1) ============
    L = []
    L.append(add_rect(slide, MX, cy, card_w, ch, fill_color=NAVY2,
                     border_color=CORAL, border_width=Pt(2),
                     corner_radius=True))
    L.append(add_rect(slide, MX + Inches(0.25), cy + Inches(0.20),
                      Inches(1.05), Inches(0.32),
                      fill_color=CORAL, border_color=CORAL,
                      border_width=Pt(0), corner_radius=True))
    L.append(add_text(slide, "BROKEN",
             MX + Inches(0.25), cy + Inches(0.21),
             Inches(1.05), Inches(0.32), size=Pt(11),
             color=WHITE, bold=True, align=PP_ALIGN.CENTER))
    L.append(add_rich_text(slide, [[
        ("v1", {"size": Pt(22), "color": WHITE, "bold": True}),
        ("  — ", {"size": Pt(16), "color": LGRAY}),
        ("conf-in-prompt", {"size": Pt(16), "color": LGRAY, "italic": True}),
    ]], MX + Inches(1.45), cy + Inches(0.17), Inches(4.0), Inches(0.40)))
    L.append(add_text(slide, "PROMPT GIVES JUDGE",
             MX + Inches(0.25), cy + Inches(0.70),
             Inches(3.5), Inches(0.30), size=Pt(10),
             color=LGRAY, bold=True))
    L.append(add_text(slide, "• Each method's confidence shown to judge",
             MX + Inches(0.25), cy + Inches(0.95),
             card_w - Inches(0.5), Inches(0.30), size=Pt(13),
             color=WHITE))
    L.append(add_text(slide, "• Baseline (top-1) confidence not shown",
             MX + Inches(0.25), cy + Inches(1.20),
             card_w - Inches(0.5), Inches(0.30), size=Pt(13),
             color=CORAL, italic=True))
    L.append(add_text(slide, "Y+P  vote_conf  vs  baseline",
             MX + Inches(0.25), cy + Inches(1.65),
             card_w - Inches(0.5), Inches(0.28), size=Pt(11),
             color=LGRAY))
    L.append(add_rich_text(slide, [[
        ("vote_conf", {"size": Pt(20), "color": CORAL, "bold": True,
                       "font": "Consolas"}),
        ("  ", {"size": Pt(20), "color": CORAL}),
        ("loses", {"size": Pt(20), "color": CORAL, "bold": True}),
        ("  (", {"size": Pt(17), "color": LGRAY}),
        ("p", {"size": Pt(17), "color": LGRAY, "italic": True}),
        (" < 0.05)", {"size": Pt(17), "color": LGRAY}),
    ]], MX + Inches(0.25), cy + Inches(1.95),
       card_w - Inches(0.5), Inches(0.45)))
    L.append(add_text(slide, "IDENTICAL-TEXT DRIFT",
             MX + Inches(0.25), cy + Inches(2.55),
             card_w - Inches(0.5), Inches(0.30), size=Pt(10),
             color=LGRAY, bold=True))
    L.append(add_rich_text(slide, [[
        ("27%", {"size": Pt(26), "color": CORAL, "bold": True}),
        ("   judge flips on identical text",
         {"size": Pt(15), "color": LGRAY}),
    ]], MX + Inches(0.25), cy + Inches(2.85),
       card_w - Inches(0.5), Inches(0.55)))
    L.append(add_rich_text(slide, [[
        ("BIAS  ", {"size": Pt(14), "color": LGRAY, "bold": True}),
        ("against n-best variants",
         {"size": Pt(14), "color": CORAL, "italic": True}),
    ]], MX + Inches(0.25), cy + Inches(3.55),
       card_w - Inches(0.5), Inches(0.40)))

    # ============ RIGHT CARD (CURRENT / v3) ============
    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, ch, fill_color=NAVY2,
                     border_color=GREEN, border_width=Pt(2),
                     corner_radius=True))
    R.append(add_rect(slide, rx + Inches(0.25), cy + Inches(0.20),
                      Inches(1.10), Inches(0.32),
                      fill_color=GREEN, border_color=GREEN,
                      border_width=Pt(0), corner_radius=True))
    R.append(add_text(slide, "CURRENT",
             rx + Inches(0.25), cy + Inches(0.21),
             Inches(1.10), Inches(0.32), size=Pt(11),
             color=WHITE, bold=True, align=PP_ALIGN.CENTER))
    R.append(add_rich_text(slide, [[
        ("v3", {"size": Pt(22), "color": WHITE, "bold": True}),
        ("  — ", {"size": Pt(16), "color": LGRAY}),
        ("dual-conf", {"size": Pt(16), "color": LGRAY, "italic": True}),
    ]], rx + Inches(1.50), cy + Inches(0.17), Inches(4.0), Inches(0.40)))
    R.append(add_text(slide, "PROMPT GIVES JUDGE",
             rx + Inches(0.25), cy + Inches(0.70),
             Inches(3.5), Inches(0.30), size=Pt(10),
             color=LGRAY, bold=True))
    R.append(add_text(slide, "• Each method's confidence shown to judge",
             rx + Inches(0.25), cy + Inches(0.95),
             card_w - Inches(0.5), Inches(0.30), size=Pt(13),
             color=WHITE))
    R.append(add_text(slide, "• Baseline confidence shown alongside",
             rx + Inches(0.25), cy + Inches(1.20),
             card_w - Inches(0.5), Inches(0.30), size=Pt(13),
             color=GREEN, italic=True))
    R.append(add_text(slide, "Y+P  vote_conf  vs  baseline",
             rx + Inches(0.25), cy + Inches(1.65),
             card_w - Inches(0.5), Inches(0.28), size=Pt(11),
             color=LGRAY))
    R.append(add_rich_text(slide, [[
        ("vote_conf", {"size": Pt(20), "color": GREEN, "bold": True,
                       "font": "Consolas"}),
        ("  ", {"size": Pt(20), "color": GREEN}),
        ("wins", {"size": Pt(20), "color": GREEN, "bold": True}),
        ("  (", {"size": Pt(17), "color": LGRAY}),
        ("p", {"size": Pt(17), "color": LGRAY, "italic": True}),
        (" = 0.00257)", {"size": Pt(17), "color": LGRAY}),
    ]], rx + Inches(0.25), cy + Inches(1.95),
       card_w - Inches(0.5), Inches(0.45)))
    R.append(add_text(slide, "IDENTICAL-TEXT DRIFT",
             rx + Inches(0.25), cy + Inches(2.55),
             card_w - Inches(0.5), Inches(0.30), size=Pt(10),
             color=LGRAY, bold=True))
    R.append(add_rich_text(slide, [[
        ("12–14%", {"size": Pt(26), "color": GREEN, "bold": True}),
        ("   per method, balanced",
         {"size": Pt(15), "color": LGRAY}),
    ]], rx + Inches(0.25), cy + Inches(2.85),
       card_w - Inches(0.5), Inches(0.55)))
    R.append(add_rich_text(slide, [[
        ("BIAS  ", {"size": Pt(14), "color": LGRAY, "bold": True}),
        ("balanced",
         {"size": Pt(14), "color": GREEN, "italic": True}),
    ]], rx + Inches(0.25), cy + Inches(3.55),
       card_w - Inches(0.5), Inches(0.40)))

    # ============ LESSON BAR ============
    lesson = []
    ly = Inches(5.95)
    lesson.append(add_rect(slide, MX, ly, CW, Inches(0.70),
                           fill_color=NAVY3, border_color=TEAL,
                           border_width=Pt(1.5), corner_radius=True))
    lesson.append(add_rich_text(slide, [[
        ("LESSON", {"size": Pt(13), "color": TEAL, "bold": True}),
        ("  •  show the judge ", {"size": Pt(13), "color": WHITE}),
        ("both sides' confidence",
         {"size": Pt(13), "color": WHITE, "italic": True, "bold": True}),
        (".  Single-sided injection biases the judge against the candidate it doesn't see.",
         {"size": Pt(13), "color": WHITE}),
    ]], MX + Inches(0.3), ly + Inches(0.18), CW - Inches(0.6),
       Inches(0.40), align=PP_ALIGN.LEFT))

    _finish(slide, 0,
        "Source: docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md "
        "+ MEMORY n_best_aggregation_findings entry. v1 (single-side "
        "method-conf in prompt) systematically biased AGAINST the n-best "
        "variants - vote_conf significantly LOST on Y+P. v3 (dual-conf "
        "with baseline_conf anchor) flipped the verdict: vote_conf "
        "significantly WINS on Y+P (p=0.00257). Identical-text drift "
        "fell from 27% to 12-14% per method. v1 is archived; v3 is "
        "the current gold standard.",
        [[sub], L, R, lesson], click_reveal=True)


# ============================================================================
# IS × Confidence Correlation slides (batch-23 #348, May 2026)
# Numbers computed from intelligibility_scores.csv × word_confidence_v2.json
# at n=1,427 segments (1,497 minus 70 empty-output segments). Source:
# docs/confidence/confidence_full_analysis.md §1.2.
# ============================================================================

def slide_is_conf_correlation(prs):
    """Statistical agreement between IS and segment-level confidence (n=1,427)."""
    slide = new_slide(prs)
    add_title(slide, "How IS and Confidence Correlate (1)")
    add_accent_line(slide)

    sub = add_text(slide,
        "IS (deterministic 6-signal score) and mean per-word confidence are "
        "independently derived signals. They converge — n = 1,427 segments.",
        MX, CT, CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True)

    # Pass 3 (audit:opus_correlation_footer_clip): cards ended at 6.60,
    # overlapping bot footer at 6.45. Trimmed card_h 4.40 -> 4.10 so cards
    # end at cy+card_h = 2.20+4.10 = 6.30; bot now has clean 0.15" gap.
    card_w = Inches(5.85)
    card_h = Inches(4.10)
    gap = Inches(0.43)
    cy = CT + Inches(0.75)

    # LEFT — scalar correlations
    L = []
    L.append(add_rect(slide, MX, cy, card_w, card_h, fill_color=NAVY2,
                      border_color=TEAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "SCALAR CORRELATION",
                      MX + Inches(0.25), cy + Inches(0.15),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(24), color=TEAL, bold=True))

    rows_corr = [
        ("Pearson r(IS, mean_prob)", "+0.837", GREEN),
        ("Spearman ρ(IS, mean_prob)", "+0.854", GREEN),
        ("Pearson r(IS, ⟨log p⟩)", "+0.760", TEAL),
    ]
    ry = cy + Inches(0.70)
    for label, val, color in rows_corr:
        L.append(add_text(slide, label,
                          MX + Inches(0.30), ry,
                          card_w - Inches(2.0), Inches(0.45),
                          size=Pt(22), color=WHITE))
        L.append(add_text(slide, val,
                          MX + card_w - Inches(1.7), ry,
                          Inches(1.4), Inches(0.45),
                          size=Pt(28), color=color, bold=True,
                          align=PP_ALIGN.RIGHT))
        ry += Inches(0.65)

    # Pass 3: shrunk h 1.40 -> 1.10 + Pt(20) -> Pt(18) to fit card_h=4.10.
    L.append(add_text(slide,
        "IS and confidence rank segments nearly identically — rank "
        "correlation (ρ=0.854) is robust to IS-tier saturation at the ends.",
        MX + Inches(0.25), cy + Inches(2.85),
        card_w - Inches(0.5), Inches(1.10),
        size=Pt(18), color=LGRAY, italic=True))

    # RIGHT — tier-level agreement
    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, card_h, fill_color=NAVY2,
                      border_color=GOLD, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "TIER-LEVEL AGREEMENT",
                      rx + Inches(0.25), cy + Inches(0.15),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(24), color=GOLD, bold=True))
    R.append(add_text(slide, "IS-tier × Conf-tier (3 × 3)",
                      rx + Inches(0.25), cy + Inches(0.65),
                      card_w - Inches(0.5), Inches(0.35),
                      size=Pt(20), color=LGRAY, italic=True,
                      align=PP_ALIGN.CENTER))

    # Pass 3: tightened content positions to fit reduced card_h=4.10.
    R.append(add_text(slide, "κ = 0.498",
                      rx + Inches(0.25), cy + Inches(1.05),
                      card_w - Inches(0.5), Inches(0.75),
                      size=Pt(44), color=GOLD, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide, "moderate agreement (Landis–Koch)",
                      rx + Inches(0.25), cy + Inches(1.85),
                      card_w - Inches(0.5), Inches(0.35),
                      size=Pt(20), color=LGRAY, italic=True,
                      align=PP_ALIGN.CENTER))

    R.append(add_text(slide, "Raw agreement (diagonal): 66%",
                      rx + Inches(0.25), cy + Inches(2.35),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(22), color=WHITE, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide, "Adjacent (within ±1 tier): 98%",
                      rx + Inches(0.25), cy + Inches(2.85),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(22), color=GREEN, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide,
        "Off-diagonal cases are almost all adjacent — Trust↔Salvage, not Trust↔Strip.",
        rx + Inches(0.25), cy + Inches(3.40),
        card_w - Inches(0.5), Inches(0.65),
        size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))

    bot = add_text(slide,
        "n = 1,427 (1,497 minus 70 empty-output segments). "
        "IS-tier3: Trust ≥3.0 / Salvage 2.0–3.0 / Strip <2.0. "
        "Conf-tier: Trust ≥0.82 / Salvage 0.65–0.82 / Strip <0.65.",
        MX, Inches(6.45), CW, Inches(0.55),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS-Confidence statistical agreement on n=1,427 segments. "
        "Pearson r(IS, mean_word_prob) = +0.837 — IS and segment-level "
        "confidence agree on a linear scale. Pearson r(IS, ⟨log p⟩) = "
        "+0.760 — log-probability space is slightly weaker but still strong. "
        "Spearman ρ(IS, mean_prob) = +0.854 — rank correlation, robust to "
        "IS saturation at tier extremes (5.0 ceiling, 0.0 floor). "
        "Tier-level: 3-tier × 3-tier (Trust/Salvage/Strip), Cohen's κ = "
        "0.498 (moderate per Landis-Koch). Raw exact-match: 66%. Adjacent "
        "(within ±1 tier): 98% — off-diagonal dominated by Trust↔Salvage "
        "and Salvage↔Strip mismatches; Trust↔Strip mismatches are <2%. "
        "IS and confidence are independently-derived quality signals that "
        "converge: confidence is the production-time signal (no GT needed); "
        "IS is the evaluation-time gold standard. Their convergence is the "
        "main empirical justification for using confidence as a trust gate. "
        "Sources: docs/evaluation/intelligibility/intelligibility_scores.csv, "
        "english_full_nbest_eval/word_confidence_v2.json, "
        "docs/confidence/confidence_full_analysis.md §1.2.",
        [[sub], L, R, [bot]], click_reveal=True)


def slide_is_conf_contingency(prs):
    """2×2 binary contingency: IS-useful (Y+P) × Conf-above-strip."""
    slide = new_slide(prs)
    add_title(slide, "How IS and Confidence Correlate (2)")
    add_accent_line(slide)

    sub = add_text(slide,
        "Binary verdict: IS-useful (Y+P, IS ≥ 2.00) × Conf-above-strip "
        "(mean_prob ≥ 0.65). 86% raw agreement on n = 1,427.",
        MX, CT, CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["", "Conf trusted (≥ 0.65)", "Conf stripped (< 0.65)", "Total"]
    rows = [
        ["IS useful (Y+P)",  "797",   "126",  "923"],
        ["IS not useful (N)",  "78",   "426",  "504"],
        ["Total",             "875",  "552", "1,427"],
    ]
    row_colors = {
        0: {1: GREEN, 2: ORANGE, 3: TEAL},
        1: {1: CORAL, 2: GREEN,  3: TEAL},
        2: {1: LGRAY, 2: LGRAY,  3: GOLD},
    }
    table_w = Inches(7.5)
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.75), table_w,
                    row_height=Inches(0.65),
                    col_widths=[Inches(2.20), Inches(1.90), Inches(1.90),
                                Inches(1.50)],
                    text_size=Pt(22), row_colors=row_colors)

    rx = MX + table_w + Inches(0.30)
    rw = CW - table_w - Inches(0.30)
    rt = add_text(slide, "READING THE TABLE",
                  rx, CT + Inches(0.75), rw, Inches(0.40),
                  size=Pt(24), color=GOLD, bold=True)
    rb = add_bullets(slide, [
        ("797 ✓✓ both trust", {"color": GREEN, "bold": True}),
        ("426 ✗✗ both strip", {"color": GREEN, "bold": True}),
        ("78 false-trust (5.5%)", {"color": CORAL}),
        ("126 false-strip (8.8%)", {"color": ORANGE}),
    ], rx, CT + Inches(1.20), rw, Inches(2.80), size=Pt(24))

    # Pass 3 fixup: actual rendered table extends to ~CT+3.85 due to
    # header wrap. head rect at CT+3.95, h=0.75; bot at 6.45 with Pt(14).
    head = add_rect(slide, MX, CT + Inches(3.95), CW, Inches(0.75),
                    fill_color=NAVY2, border_color=GREEN,
                    border_width=Pt(2), corner_radius=True)
    head_t = add_text(slide,
        "86% raw binary agreement   /   κ_binary = 0.71 (substantial)",
        MX + Inches(0.3), CT + Inches(4.05), CW - Inches(0.6), Inches(0.55),
        size=Pt(22), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    bot = add_text(slide,
        "Threshold rationale: IS ≥ 2.00 = NIV-Y+P (judge-calibrated, κ=0.82). "
        "mean_prob ≥ 0.65 = strip-coloring boundary (below: green <50% reliable).",
        MX, Inches(6.45), CW, Inches(0.55),
        size=Pt(14), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Binary 2×2 contingency: IS-useful (Y+P, IS ≥ 2.00) × "
        "Conf-above-strip (mean_prob ≥ 0.65), n = 1,427. "
        "True positives (both trust): 797 — useful output, confidence "
        "correctly flags it. True negatives (both strip): 426 — both "
        "signals catch bad outputs. False trust (78, 5.5%): IS says not "
        "useful but confidence trusts — the dangerous production category. "
        "False strip (126, 8.8%): IS says useful but confidence flagged "
        "— conservative, costs recall but doesn't harm precision. "
        "Raw agreement: (797+426)/1,427 = 85.7%. Cohen's κ_binary = 0.71 "
        "(substantial, Landis-Koch). Threshold rationale: IS ≥ 2.00 is "
        "the NIV-Y+P operating point (judge-calibrated κ=0.816). "
        "mean_prob ≥ 0.65 is the strip-coloring boundary from "
        "slide_three_thresholds — below this point green-band reliability "
        "drops under 50%. "
        "PEER DETAIL — false-trust rate (5.5%) is comparable to AUC=0.917 "
        "NIV-N detection figure earlier in this section: at production "
        "operating point mean_prob ≥ 0.80 we admit ~9 NIV-N out of 405 "
        "trusted (2.2%). The 5.5% here reflects the looser ≥0.65 strip "
        "threshold rather than T_safe. "
        "Sources: docs/evaluation/intelligibility/intelligibility_scores.csv "
        "× english_full_nbest_eval/word_confidence_v2.json, "
        "docs/confidence/confidence_full_analysis.md §1.2-1.3.",
        [[sub, tbl], [rt, rb], [head, head_t], [bot]],
        click_reveal=True)


# ============================================================================
# DEMO SLIDES — research-flavored versions of the client examples (Task E)
# All five reuse the existing IMG video keys; speaker notes disclose decode
# artefact gaps (Obama clips fall back to conf-only, no VSP_NBEST=1).
# ============================================================================


