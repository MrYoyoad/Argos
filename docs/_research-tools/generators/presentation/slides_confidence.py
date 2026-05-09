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
    """Section 4 opener - in production we have no ground truth."""
    # audit:bigfonts — 4 bullets at 20pt in h=3.5 box; ample room.
    slide = new_slide(prs)
    add_title(slide, "Confidence Without Ground Truth")
    add_accent_line(slide)

    intro = add_text(slide,
        "All the IS / WER / Judge analysis so far depends on having a "
        "reference text. In production, on a video the user just uploaded, "
        "there IS no reference. How do we surface uncertainty at runtime?",
        MX, CT, CW, Inches(1.0),
        size=Pt(20), color=LGRAY, italic=True)

    bul = add_bullets(slide, [
        ("Goal: a per-segment and per-word reliability signal computed "
         "only from the model's own outputs (no reference text).",
         {"bold": True}),
        "We need to rank segments so a reviewer can triage which to verify.",
        "We need to rank words inside a segment so a reader knows where to look.",
        ("Constraint: zero extra inference cost. Whatever signal we use must be "
         "extractable from a single decode pass.", {"color": TEAL}),
    ], MX, CT + Inches(1.2), CW, Inches(3.5), size=Pt(24))

    # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
    # phrasing replaced; works under reorder.
    # CUT v3: top 6.4 -> 6.20 to keep Pt(24) wrap under safe 7.05.
    # A1 (research-overview): two-layer math now PRECEDES this slide so
    # the bottom callback points back, not forward.
    bottom = add_text(slide,
        "Two layers of confidence (just shown): "
        "per-word from the LLM softmax, per-segment as the aggregate.",
        MX, Inches(6.02), CW, Inches(1.0),
        size=Pt(24), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Source: docs/evaluation/after_amosi_audit.json (Section D) + "
        "docs/confidence/confidence_full_analysis.md. The point: IS, WER, "
        "judge - all these are EVALUATION-time signals that need a "
        "reference. In production on user video, no reference exists. We "
        "need a calibrated runtime confidence signal computed from model "
        "outputs only. The two-layer math (per-word softmax + per-segment "
        "mean log-prob) was introduced on the preceding slide; this slide "
        "frames why we need it at all in production.",
        [[intro], [bul], [bottom]], click_reveal=True)


def slide_two_layer_confidence_research(prs):
    """Two-layer confidence (research framing).

    Lifted from slides_client.py::slide_client_two_layer_confidence and
    re-framed for research peers - explicit math, drop the trust warmth.

    audit:bigfonts — 5.85x3.6 cards; bullets at 18pt in h=1.8 box (~6.6
    lines) fit 3 bullets averaging 2 lines each. Equation row at 18pt
    (italic gold) fits in h=0.4.
    """
    slide = new_slide(prs)
    add_title(slide, "Two Layers of Confidence (Per-Word + Per-Segment)")
    add_accent_line(slide)

    add_text(slide,
        "Both layers are derived from the LLM's output softmax during "
        "the same decode pass. Zero extra cost.",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

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
             size=Pt(24), bold=True, color=BLUE))
    L.append(add_text(slide, "max softmax probability per token",
             x1 + Inches(0.3), top + Inches(0.6),
             card_w - Inches(0.6), Inches(1.0),
             size=Pt(24), bold=True, color=WHITE))
    L.append(add_text(slide,
             "p(t)  =  maxᵥ  P( v | tokens ≤ t )",
             x1 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(0.6),
             size=Pt(24), color=GOLD, italic=True, align=PP_ALIGN.CENTER))
    # CUT v3: bullets shrunk to short fragments + Pt(24)->Pt(20)
    # so wraps fit inside 1.8" frame (was rendering bottom 7.20).
    # Original: "Aggregate sub-token probabilities up to whole-word level",
    # "Render colour-coded inline in the report (BLUE / ORANGE / PURPLE)",
    # "23,261 words across 1,427 segments # audit:perword_new_total_words"
    L.append(add_bullets(slide, [
        "Aggregate sub-tokens up to whole word",
        "Render inline (BLUE / ORANGE / PURPLE)",
        ("23,261 words / 1,427 segments",
         {"color": LGRAY}),
    ], x1 + Inches(0.3), top + Inches(1.75),
       card_w - Inches(0.6), Inches(1.65), size=Pt(20)))

    # Layer 2 - per-segment (sequence-level)
    R = []
    x2 = MX + card_w + gap
    R.append(add_rect(slide, x2, top, card_w, h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "2. PER-SEGMENT",
             x2 + Inches(0.3), top + Inches(0.2),
             card_w - Inches(0.6), Inches(0.4),
             size=Pt(24), bold=True, color=TEAL))
    R.append(add_text(slide, "mean log-probability over the segment",
             x2 + Inches(0.3), top + Inches(0.6),
             card_w - Inches(0.6), Inches(0.42),
             size=Pt(24), bold=True, color=WHITE))
    R.append(add_text(slide,
             "m  =  exp( (1/T) · Σ log p(t) )",
             x2 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(0.6),
             size=Pt(24), color=GOLD, italic=True, align=PP_ALIGN.CENTER))
    # audit:after_amosi_narrative_actions.md fix #13 - the demo cards
    # later in the deck use the term "sequence_conf"; add an alias bullet
    # here so the audience can match the demo cards back to mean_prob.
    # CUT v3: 4 bullets at Pt(24) wrapped to ~12 lines, bottom 8.40.
    # Trimmed text + Pt(24)->Pt(20). Full long-form retained in notes.
    R.append(add_bullets(slide, [
        "Length-anomaly check (too short / too long)",
        ("τ_trust 0.89, τ_safe 0.82, τ_salvage 0.74",
         {"color": TEAL}),
        ("Strip below 0.65 (green flag misleads)",
         {"color": CORAL}),
        ("Demo cards label this sequence_conf",
         {"color": LGRAY, "italic": True}),
    ], x2 + Inches(0.3), top + Inches(1.75),
       card_w - Inches(0.6), Inches(2.72), size=Pt(20)))

    # CUT v3: top 6.45 -> 6.30 + frame h 0.8 -> 0.55 + trimmed text so
    # Pt(18) bottom stays under safe 7.05.
    bot = add_text(slide,
        "Both layers calibrated against a held-out blind LLM judge.",
        MX, Inches(6.30), CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

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
    # audit:bigfonts — table row_height 0.55 fits 20pt; cards at h=2.7 with
    # 3 bullets at 18pt fit cleanly.
    slide = new_slide(prs)
    add_title(slide, "Per-Word Confidence Bands - Distribution")
    add_accent_line(slide)

    sub = add_text(slide,
        "Total per-word judgments: 23,261 across 1,427 segments. Joint "
        "rule: p₁ ≥ 0.95 AND α ≥ 0.80; legacy: conf only.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["Band", "JOINT n", "JOINT %", "LEGACY n", "LEGACY %"]
    rows = [
        # audit:perword_new_green_count vs perword_old_green_count, etc.
        ["Green",  "7,591",  "33%", "11,309", "49%"],
        ["Yellow", "6,571",  "28%",  "7,470", "32%"],
        ["Red",    "9,099",  "39%",  "4,482", "19%"],
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
                    text_size=Pt(24), row_colors=row_colors)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    cy = CT + Inches(3.0)
    L = []
    L.append(add_rect(slide, MX, cy, card_w, Inches(2.7), fill_color=NAVY2,
                     border_color=BLUE, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "JOINT RULE — STRICTER, RELIABLE",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.45), size=Pt(24), color=BLUE, bold=True))
    # CUT v3: bullets trimmed + Pt(24)->Pt(20) so 3 bullets fit in
    # 2.0" frame (was rendering bottom 8.60). Long-form retained in notes.
    L.append(add_bullets(slide, [
        "Green drops 33% (11,309 → 7,591)",
        "Reds 2× (4,482 → 9,099): ambiguous → red",
        ("Each green more reliable (90% vs 81%)",
         {"color": GREEN, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.65),
       card_w - Inches(0.5), Inches(2.0), size=Pt(24)))

    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, Inches(2.7), fill_color=NAVY2,
                     border_color=PURPLE, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "LEGACY CONF-ONLY - PERMISSIVE",
             rx + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=PURPLE, bold=True))
    # CUT v3: bullets trimmed + Pt(24)->Pt(20) so 3 bullets fit in
    # 2.0" frame (was rendering bottom 8.20). Long-form retained in notes.
    R.append(add_bullets(slide, [
        "Almost half of words paint green",
        "Many greens hide beam disagreement",
        ("Superseded by joint rule",
         {"color": LGRAY, "italic": True}),
    ], rx + Inches(0.25), cy + Inches(0.65),
       card_w - Inches(0.5), Inches(2.0), size=Pt(24)))

    _finish(slide, 0,
        "Distribution of per-word band assignments under the joint rule "
        "(top1_conf >= 0.95 AND beam_agreement >= 0.80) versus the legacy "
        "conf-only rule. Total 23,261 words across 1,427 segments. Under "
        "the joint rule: Green 33% (7,591), Yellow 28% (6,571), Red "
        "39% (9,099). Under legacy conf-only at 0.85: Green 49% "
        "(11,309), Yellow 32% (7,470), Red 19% (4,482). The joint "
        "rule reclassifies roughly 3,700 words from green to red+yellow, "
        "tightening green reliability from 81% to 90% (quantified "
        "later in this section). Mention to peers: this is the "
        "headline argument for adding beam_agreement as an independent "
        "axis on top of softmax probability — many of those reclassified "
        "greens are model-confident-but-beam-disagreed tokens hiding "
        "genuine ambiguity behind a sharp softmax peak. "
        "Sources: docs/evaluation/after_amosi_audit.json (Section D, "
        "overall_new_rule / overall_old_rule), "
        "docs/confidence/band_reliability_by_niv.md.",
        [[sub, tbl], L, R], click_reveal=True)


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

    # CUT v3: top 6.55 -> 6.40 to keep Pt(18) wrap under safe 7.05.
    bot = add_text(slide,
        "All numbers from audit JSON keys perword_{new,old}_{green,yellow,red}_p_correct. "
        "Total 23,261 words.",
        MX, Inches(6.22), CW, Inches(0.8),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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
    """Band reliability stratified by segment mean_prob bin."""
    # audit:bigfonts — left plot fixed-size; right column 18pt fits.
    slide = new_slide(prs)
    add_title(slide, "Green Reliability Depends on Segment Quality")
    add_accent_line(slide)

    sub = add_text(slide,
        "P(correct | green) stratified by segment confidence m. "
        "Green ranges from 96% (high-m segments) to 18% (low-m)."
        " Strip boundary at m < 0.65.",
        MX, CT + Inches(0.05), CW, Inches(0.40),
        size=Pt(18), color=LGRAY, italic=True)
    img = add_image(slide, "P_band_reliability_stratified",
                    MX, CT + Inches(0.5),
                    width=Inches(7.6), height=Inches(4.6))

    rx = MX + Inches(7.8)
    rw = CW - Inches(7.8)
    rt = add_text(slide, "Stratified P(green | bin)",
                  rx, CT + Inches(0.5), rw, Inches(0.35),
                  size=Pt(24), color=BLUE, bold=True)

    # Stratification bins - joint-rule >= 0.65 only.
    # Short labels so 24pt fits in narrow rw col without wrapping.
    headers = ["m", "P(green correct)"]
    rows = [
        ["≥0.85",     "96%"],   # very_high bin
        ["0.75–0.85", "92%"],   # high bin
        ["0.65–0.75", "86%"],   # mid bin
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(24), row_height=Inches(0.4))

    # leg_t moved CT+2.5->CT+2.65 (0.20" gap after table end CT+2.45).
    leg_t = add_text(slide,
        "Below 0.65 (legacy rule only):\n"
        "0.55-0.65: 41%\n"
        "0.40-0.55: 22%\n"
        "<0.40:    18%",
        rx, CT + Inches(2.65), rw, Inches(1.85),
        size=Pt(24), color=LGRAY)

    # CUT v3: top 6.55 -> 6.30 + frame h 0.4 -> 0.35 so Pt(20) wrap stays
    # under safe 7.05 (was 7.12).
    bot = add_text(slide,
        "Green reliability is conditional on segment quality — "
        "the strip boundary lives at 0.65.",
        MX, Inches(6.12), CW, Inches(0.87),
        size=Pt(20), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Per-word green-band reliability stratified by segment mean_prob. "
        "Headline numbers: 96% reliable in the cleanest segments "
        "(mean_prob >= 0.85), 92% in 0.75-0.85, 86% in 0.65-0.75. The "
        "joint-rule diagnostic CSV is filtered at seg_mean_conf >= 0.65, "
        "so values below 0.65 must be recomputed from the legacy "
        "conf-only rule on the B3 sidecar: 41% in 0.55-0.65, 22% in "
        "0.40-0.55, 18% below 0.40. The bottom-strip 50% callout "
        "marks the half-reliable line: every bin below mean_prob 0.65 "
        "sits under 50% (41% / 22% / 18%), so colouring those "
        "words green would actively mislead a viewer. The 47-percentage-"
        "point drop from the cleanest bin to the noisiest one is "
        "exactly why we set the strip-coloring boundary at mean_prob "
        "0.65. Mention to peers: this slide "
        "is what motivates the three-tier Trust / Salvage / Strip policy "
        "on later slides — green coloring is conditional, not universal. "
        "Plot: P_band_reliability_stratified.png. "
        "Sources: docs/evaluation/after_amosi_audit.json (Section D), "
        "docs/confidence/band_reliability_by_niv.md.",
        [[sub, img], [rt, tbl, leg_t], [bot]], click_reveal=True)


def slide_green_leakage_examples(prs):
    """Concrete numeric/entity hallucinations with high green confidence."""
    # audit:bigfonts — card_h up + bot_card moved+trimmed; see inline.
    slide = new_slide(prs)
    add_title(slide, "Green Leakage - When High Confidence Misleads")
    add_accent_line(slide)

    sub = add_text(slide,
        "2,192 wrong-and-green words across 23,261 (9% leakage). "
        "Numerics and entities concentrate the danger.",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)
    # 9% leakage = 2192/23261 (no single audit key; computable from
    # audit Section D totals - see audit-md:section-D + MEMORY).

    # audit:bigfonts — card_h bumped 2.5 -> 3.0 so REF/HYP/conf/note all
    # fit at 18pt; bot_card pushed to y=5.95.
    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(3.0)
    gap = Inches(0.3)
    cy = CT + Inches(0.5)

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
        # CUT v3 (overflow): font 24->18pt + frames grown so 2-line text fits.
        c.append(add_text(slide, ex["title"],
                 x + Inches(0.2), cy + Inches(0.15), card_w - Inches(0.4),
                 Inches(0.45), size=Pt(20), color=BLUE, bold=True,
                 align=PP_ALIGN.CENTER))
        c.append(add_text(slide, "REF: " + ex["ref"],
                 x + Inches(0.2), cy + Inches(0.65), card_w - Inches(0.4),
                 Inches(0.65), size=Pt(18), color=GREEN, italic=True))
        c.append(add_text(slide, "HYP: " + ex["hyp"],
                 x + Inches(0.2), cy + Inches(1.30), card_w - Inches(0.4),
                 Inches(0.65), size=Pt(18), color=PURPLE, italic=True))
        c.append(add_text(slide, ex["conf"],
                 x + Inches(0.2), cy + Inches(1.95), card_w - Inches(0.4),
                 Inches(0.45), size=Pt(18), color=GOLD, bold=True,
                 align=PP_ALIGN.CENTER))
        c.append(add_text(slide, ex["note"],
                 x + Inches(0.2), cy + Inches(2.40), card_w - Inches(0.4),
                 Inches(0.55), size=Pt(16), color=LGRAY, italic=True))
        cards.append(c)

    # audit:bigfonts — bot_card pushed to y=5.95 (was 5.6) and trimmed
    # so 18pt fits 0.95" box.  Cut: "Entities are left in the joint-rule
    # pipeline; calibration handles the rest." (in speaker notes).
    bot_card = []
    bot_card.append(add_rect(slide, MX, Inches(5.95), CW, Inches(1.10),
                             fill_color=NAVY3, border_color=ORANGE,
                             border_width=Pt(1.5), corner_radius=True))
    # CUT v3: trimmed to 2 lines so Pt(24) wrap stays inside the 0.95"
    # frame (was 3 lines, bottom 7.25). "Joint rule cuts green leakage
    # from ~16% (legacy) to 9% without losing too much green volume."
    # moved to speaker notes.
    bot_card.append(add_text(slide,
        "Production response: numbers CAPPED at yellow under the joint rule.",
        MX + Inches(0.25), Inches(6.05), CW - Inches(0.5),
        Inches(0.95), size=Pt(24), color=WHITE))

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
    add_title(slide, "Three-Tier Policy - Per-Tier Counts and Reliability")
    add_accent_line(slide)

    sub = add_text(slide,
        "Tiers from segment confidence score (m); per-tier P(green correct) under "
        "joint rule. Volumes from per_word_by_tier.csv.",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    # All numbers from audit:section_D_per_word_conf.by_tier.{Trust,Salvage,Strip}.new
    headers = ["Tier", "Green n", "P(grn corr)", "Yellow n", "P(yel corr)",
               "Red n", "P(red corr)"]
    # Labels ≤15 chars so 24pt text fits in 2.6" Tier col without wrapping.
    # "Salvage (0.65-0.82)" = 19 chars wraps; "Salvage .65-.82" = 15 fits.
    rows = [
        ["Trust (>=0.82)",  "3,923", "95%", "1,719", "76%", "  951", "42%"],
        ["Salvage .65-.82", "3,091", "89%", "3,241", "60%", "3,442", "28%"],
        ["Strip (<0.65)",     "  577", "56%", "1,611", "38%", "4,706", "13%"],
    ]
    row_colors = {
        0: {0: BLUE,   2: GREEN},
        1: {0: ORANGE, 2: GOLD},
        2: {0: PURPLE, 2: CORAL},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.60),
                    col_widths=[Inches(2.6), Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6)],
                    text_size=Pt(24), row_colors=row_colors)

    L = []
    L.append(add_text(slide, "WHAT THE NUMBERS SAY",
             MX, CT + Inches(3.10), Inches(6.0), Inches(0.35),
             size=Pt(24), color=TEAL, bold=True))
    L.append(add_bullets(slide, [
        # <=35 chars each so 24pt text fits in 6.0" col (38-char limit) single-line.
        ("Trust (>=0.82): green 95% reliable.", {"color": BLUE, "bold": True}),
        ("Salvage .65-.82: green 89%, review.", {"color": ORANGE}),
        ("Strip (<0.65): green 56%, misleads.", {"color": PURPLE, "bold": True}),
    ], MX, CT + Inches(3.50), Inches(6.0), Inches(1.55), size=Pt(24)))

    R = []
    R.append(add_text(slide, "HOW THE TIERS ARE USED",
             MX + Inches(6.3), CT + Inches(3.10), Inches(5.83), Inches(0.35),
             size=Pt(24), color=GOLD, bold=True))
    R.append(add_bullets(slide, [
        "Post-hoc: no re-decode required",
        "Feeds client UI threshold knob",
        ("Red P(correct) stays low across tiers (42/28/13%)",
         {"bold": True}),
    ], MX + Inches(6.3), CT + Inches(3.50), Inches(5.83), Inches(1.55),
       size=Pt(24)))

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
        [[sub, tbl], L, R], click_reveal=True)


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
    img = add_image(slide, "P_band_reliability_by_niv",
                    MX, CT + Inches(0.5),
                    width=Inches(9.0), height=Inches(4.25))
    rx = MX + Inches(9.2)
    rw = CW - Inches(9.2)
    rt = add_text(slide, "P(correct | band)",
                  rx, CT + Inches(0.5), rw, Inches(0.3),
                  size=Pt(24), color=TEAL, bold=True)

    # audit-md:band_reliability_by_niv (no flat key in audit JSON)
    # Short labels prevent 24pt text wrapping in narrow col (rw/4 ~1.08"):
    # "Y+P combined" (12 chars) wraps; "Y+P" (3 chars) does not.
    headers = ["Tier", "GRN", "YEL", "RED"]
    rows = [
        ["Y+P",   "87%", "49%", "25%"],
        ["NIV-Y", "94%", "65%", "39%"],
        ["NIV-P", "80%", "41%", "20%"],
        ["NIV-N", "37%", "17%",  "7%"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(24), row_height=Inches(0.4))

    # OVERLAP fix: table end CT+2.85; take moved to CT+3.15 (0.30" gap).
    # CUT v3: bullets compressed + Pt(24)->Pt(18) so 3 bullets fit.
    # Long-form retained in notes.
    take = add_bullets(slide, [
        ("62.5pp green→red spread in Y+P", {"bold": True, "color": GREEN}),
        ("NIV-P: steepest (80/41/20%)", {"color": ORANGE}),
        ("NIV-N: green misleads (37%)", {"color": PURPLE}),
    ], rx, CT + Inches(3.15), rw, Inches(1.65), size=Pt(18))

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
    """Marginal info gain of beam agreement over top-1 conf."""
    # audit:bigfonts — table row_height 0.7 fits 20pt; why bullets 18pt
    # fit in 2.5" box (4 bullets avg 2 lines = ~2.2").
    slide = new_slide(prs)
    add_title(slide, "Beam Agreement Adds Independent Signal")
    add_accent_line(slide)

    sub = add_text(slide,
        "At p₁ ≥ 0.95 the softmax says 'almost certain.' Beam "
        "agreement reveals which of those tokens were actually unique.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # audit:after_amosi_logic_fixes.md fix #6 - prior copy paired
    # "0.94 / 0.62" with "32pp gap" but those are the conf>=0.65 numbers.
    # At top1_conf>=0.95 (the green-band threshold), the spread is
    # 0.94 / 0.40 = 54pp. Source:
    # english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md Test C.
    headers = ["", "α ≥ 0.80", "α < 0.80"]
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
                    text_size=Pt(24), row_colors=row_colors)

    why = []
    why.append(add_text(slide, "WHY THIS MATTERS",
             MX, CT + Inches(2.95), CW, Inches(0.35),
             size=Pt(24), color=TEAL, bold=True))
    # CUT v3: bullets compressed so 4 bullets fit in 1.60" frame at Pt(24).
    # WHY heading shifted to CT+2.95 (table OOXML end CT+2.8 + 0.15 margin).
    why.append(add_bullets(slide, [
        ("54pp P(correct) gap at SAME top-1 conf (0.40 vs 0.94)",
         {"bold": True}),
        "Conf alone collapses 2 populations into one green band",
        ("Beam agreement α: ~2× AUC of p₁ at conf ≥ 0.95",
         {"color": TEAL}),
        ("Green: 11,309 → 7,591 words, P(correct) 81% → 90%",
         {"color": GREEN}),
    ], MX, CT + Inches(3.35), CW, Inches(1.80), size=Pt(24)))

    # h increased 1.60->1.80 to hold 4 bullets; footer shifted down accordingly.
    bot = add_text(slide,
        "Diagnostic: diagnose_confidence_signals.py — Llama-2-7b specific.",
        MX, Inches(6.65), CW, Inches(0.40),
        size=Pt(24), color=CORAL, italic=True, align=PP_ALIGN.CENTER)

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
        "and tightens green from 81% to 90%. audit-md:section-D "
        "supplies overall green P(correct).",
        [[sub, tbl], why, [bot]], click_reveal=True)


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
    """Dual-conf prompt design lesson."""
    # audit:bigfonts — 5 bullets at 18pt fit 3.5" box per side (~2.0"
    # used); lesson rect 0.7" fits 3-line 18pt body in 0.55" h text box.
    slide = new_slide(prs)
    add_title(slide, "v1 vs v3 Judge: A Prompt-Design Lesson")
    add_accent_line(slide)

    sub = add_text(slide,
        "Same n-best methods. Same judge model. Different prompt. "
        "Opposite conclusions.",
        MX, CT, CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    cy = CT + Inches(0.6)
    ch = Inches(3.9)

    L = []
    L.append(add_rect(slide, MX, cy, card_w, ch, fill_color=NAVY2,
                     border_color=CORAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "v1 - conf-in-prompt (broken)",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(24), color=CORAL, bold=True))
    L.append(add_bullets(slide, [
        ("Method-conf only in prompt", {"bold": True}),
        ("Y+P: vote_conf loses (p < 0.05)", {"color": CORAL}),
        ("Identical-text drift: 27%", {"color": CORAL}),
        ("Bias: against n-best variants", {"color": CORAL, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.2), size=Pt(24)))

    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, ch, fill_color=NAVY2,
                     border_color=GREEN, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "v3 - dual-conf prompt (current)",
             rx + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=GREEN, bold=True))
    R.append(add_bullets(slide, [
        ("Method-conf AND baseline_conf shown", {"bold": True}),
        ("Y+P: vote_conf wins (p = 0.00257)", {"color": GREEN}),
        ("Identical-text drift: 12.6/10.4/14%", {"color": GREEN}),
        ("Bias: balanced", {"color": GREEN, "bold": True}),
    ], rx + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.2), size=Pt(24)))

    lesson = []
    lesson.append(add_rect(slide, MX, Inches(6.10), CW, Inches(0.65),
                           fill_color=NAVY3, border_color=GOLD,
                           border_width=Pt(1.5), corner_radius=True))
    lesson.append(add_text(slide,
        "LESSON: provide BOTH sides' confidence — single-sided injection biases the judge.",
        MX + Inches(0.3), Inches(6.15), CW - Inches(0.6),
        Inches(0.50), size=Pt(24), color=GOLD, bold=True))

    _finish(slide, 0,
        "Source: docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md "
        "+ MEMORY n_best_aggregation_findings entry. v1 (single-side "
        "method-conf in prompt) systematically biased AGAINST the n-best "
        "variants - vote_conf significantly LOST on Y+P. v3 (dual-conf "
        "with baseline_conf anchor) flipped the verdict: vote_conf "
        "significantly WINS on Y+P (p=0.00257). Identical-text drift "
        "fell from 27% to 12.6-14% per method (audit:_note_drift). "
        "v1 is archived; v3 is the current gold standard. Transferable "
        "lesson: when prompting LLMs to compare hypotheses, always "
        "provide BOTH sides' confidence as anchors.",
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

    card_w = Inches(5.85)
    card_h = Inches(4.40)
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

    L.append(add_text(slide,
        "IS and confidence rank segments nearly identically — rank "
        "correlation (ρ=0.854) is robust to IS-tier saturation at the ends.",
        MX + Inches(0.25), cy + Inches(2.85),
        card_w - Inches(0.5), Inches(1.40),
        size=Pt(20), color=LGRAY, italic=True))

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

    R.append(add_text(slide, "κ = 0.498",
                      rx + Inches(0.25), cy + Inches(1.10),
                      card_w - Inches(0.5), Inches(0.80),
                      size=Pt(48), color=GOLD, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide, "moderate agreement (Landis–Koch)",
                      rx + Inches(0.25), cy + Inches(1.95),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(20), color=LGRAY, italic=True,
                      align=PP_ALIGN.CENTER))

    R.append(add_text(slide, "Raw agreement (diagonal): 66%",
                      rx + Inches(0.25), cy + Inches(2.55),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(24), color=WHITE, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide, "Adjacent (within ±1 tier): 98%",
                      rx + Inches(0.25), cy + Inches(3.05),
                      card_w - Inches(0.5), Inches(0.40),
                      size=Pt(24), color=GREEN, bold=True,
                      align=PP_ALIGN.CENTER))
    R.append(add_text(slide,
        "Off-diagonal cases are almost all adjacent — Trust↔Salvage, not Trust↔Strip.",
        rx + Inches(0.25), cy + Inches(3.55),
        card_w - Inches(0.5), Inches(0.70),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))

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

    head = add_rect(slide, MX, CT + Inches(3.95), CW, Inches(1.05),
                    fill_color=NAVY2, border_color=GREEN,
                    border_width=Pt(2), corner_radius=True)
    head_t = add_text(slide,
        "86% raw binary agreement   /   κ_binary = 0.71 (substantial)",
        MX + Inches(0.3), CT + Inches(4.10), CW - Inches(0.6), Inches(0.75),
        size=Pt(28), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    bot = add_text(slide,
        "Threshold rationale: IS ≥ 2.00 = NIV-Y+P (judge-calibrated, κ=0.82). "
        "mean_prob ≥ 0.65 = strip-coloring boundary (below: green <50% reliable).",
        MX, Inches(6.20), CW, Inches(0.80),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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


