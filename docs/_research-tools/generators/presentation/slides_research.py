"""
Slide builders — Sections 3-5: Research Findings, Understanding Why, Tuning
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

def slide_is_intro(prs):
    """Deep dive into IS — what it is and how each signal works."""
    slide = new_slide(prs)
    add_title(slide, "The Intelligibility Score (IS) — Our Metric")
    add_accent_line(slide)

    # Top banner — what IS is in one line
    banner = add_rect(slide, MX, CT, CW, Inches(0.55), fill_color=NAVY2,
                      border_color=TEAL, border_width=Pt(2), corner_radius=True)
    banner_txt = add_text(slide,
        "A composite score from 0 to 5.  IS \u2265 3.0 = \"Properly Captured\" "
        "\u2014 the viewer got the message.  "
        "Deterministic, free, reproducible.",
        MX + Inches(0.3), CT + Inches(0.08), CW - Inches(0.6), Inches(0.4),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # 6 signal cards — 2 columns × 3 rows
    card_w = Inches(5.8)
    card_h = Inches(1.35)
    gap_x = Inches(0.53)
    gap_y = Inches(0.12)
    start_y = CT + Inches(0.8)

    signals = [
        ("Semantic Similarity", "25%", TEAL,
         "Converts both ref and hyp to 384-dim sentence embeddings "
         "(SBERT / all-MiniLM-L6-v2), then measures cosine similarity. "
         "Captures overall meaning — even if different words are used, "
         "a high score means the same idea was communicated.",
         'Example: "the CEO resigned" vs "the chief executive stepped down" '
         '\u2192 cosine 0.91 (meaning preserved despite zero word overlap).'),
        ("Phonetic Similarity", "15%", TEAL,
         "Converts each word to IPA pronunciation (eng-to-ipa), "
         "then computes character-level similarity between phonetic strings. "
         "Critical for lip reading: the model sees mouth shapes, not spellings — "
         "so phonetically correct output is a sign the visual encoder worked.",
         'Example: "Admiral McRae" vs "animal migration" \u2192 '
         'phonetic: /\u00e6dm\u026ar\u0259l m\u0259kre\u026a/ vs '
         '/\u00e6n\u026am\u0259l ma\u026a\u0261re\u026a\u0283\u0259n/ \u2192 0.68 (sounds similar!).'),
        ("Inverse WER", "15%", CORAL,
         "Standard Word Error Rate (substitutions + insertions + deletions "
         "divided by reference length), then inverted: 1 \u2212 WER. "
         "A baseline word-accuracy signal.",
         "Treats all words equally — every error costs the same."),
        ("WWER (Weighted WER)", "15%", CORAL,
         "Like WER, but content words (nouns, verbs, names) cost 2\u00d7 "
         "and function words ('the', 'a', 'is') cost only 0.5\u00d7. "
         "Losing a name hurts more than losing an article.",
         'Example: "Admiral McRae" wrong = 2\u00d7 penalty. '
         '"the" wrong = 0.5\u00d7 penalty.'),
        ("Named Entity Accuracy", "15%", CORAL,
         "Extracts named entities (people, numbers, places) from both "
         "ref and hyp using spaCy NER, then computes F1 (precision \u00d7 recall). "
         "Binary per entity: either correct or destroyed, no partial credit.",
         "Mean F1 = 38.9% \u2014 entities missed in 85% of segments."),
        ("Length Ratio", "15%", LGRAY,
         "Output length divided by reference length. A safety check: "
         "catches hallucination (ratio >> 1, model generates too much) "
         "and truncation (ratio << 1, model cuts off early).",
         "Hallucinated segments average ratio 2.8\u00d7."),
    ]

    card_groups = []
    for i, (name, weight, color, how, example) in enumerate(signals):
        col = i % 2
        row = i // 2
        x = MX + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        r = add_rect(slide, x, y, card_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({weight})",
                 x + Inches(0.15), y + Inches(0.06),
                 card_w - Inches(0.3), Inches(0.28),
                 size=Pt(13), color=color, bold=True)
        t2 = add_text(slide, how,
                 x + Inches(0.15), y + Inches(0.34),
                 card_w - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=WHITE)
        t3 = add_text(slide, f"\u25b8 {example}",
                 x + Inches(0.15), y + Inches(0.92),
                 card_w - Inches(0.3), Inches(0.38),
                 size=Pt(9), color=LGRAY, italic=True)
        card_groups.append([r, t1, t2, t3])

    # Formula at bottom
    add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + WWER + NEA + Length)"
        "   \u2022   Fully deterministic   \u2022   $0 per evaluation",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Deep dive into IS. Six signals, each measuring a different aspect "
        "of output quality. SEMANTIC (25%): sentence embeddings capture "
        "overall meaning even with different words — cosine similarity in "
        "384-dim space. PHONETIC (15%): converts words to IPA pronunciation "
        "and compares — critical because the model sees mouth shapes, not "
        "spellings. WER (15%): standard word accuracy baseline. WWER (15%): "
        "weighted WER where content words cost 2x and function words 0.5x. "
        "NEA (15%): Named Entity F1 — are names, numbers, places preserved? "
        "LENGTH (15%): output/reference length ratio catches hallucination "
        "and truncation. All 6 are combined into a single 0-5 score. "
        "IS >= 3.0 means the viewer gets the message.",
        [[banner, banner_txt]] + card_groups, click_reveal=True)


def slide_tuning_intro(prs):
    """Motivation slide: why we ran 13 tuning experiments."""
    slide = new_slide(prs)
    add_title(slide, "Can We Tune Our Way Out?")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: The question
    lt = add_text(slide, "The Question", MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "The visual encoder is the primary bottleneck",
        "But decode parameters control HOW the LLM generates text",
        "Can beam search, length penalty, or temperature improve output?",
        ("We ran 13 systematic experiments to find out", {"bold": True}),
    ], MX, CT + Inches(0.55), col_w, Inches(3.0), size=Pt(15))

    # Right: What we varied
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Parameters Tested", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)

    params = [
        ("Beam size", "5 \u2192 50 candidates"),
        ("Length penalty", "\u22120.5 \u2192 2.0"),
        ("Temperature", "0.3 \u2192 1.5"),
        ("Sampling strategy", "greedy vs nucleus"),
        ("Repetition penalty", "on / off"),
    ]
    py = CT + Inches(0.55)
    for name, desc in params:
        add_text(slide, f"{name}: {desc}",
                 rx + Inches(0.2), py, rw - Inches(0.4), Inches(0.35),
                 size=Pt(14), color=WHITE)
        py += Inches(0.45)

    # Bottom
    add_text(slide,
        "107-segment test set \u2022 Best config validated on all 1,497 segments",
        MX, Inches(6.4), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Motivation for tuning. The visual encoder determines which segments "
        "succeed or fail, but decode parameters affect output quality. We ran "
        "13 experiments varying beam size, length penalty, temperature, sampling, "
        "and repetition penalty. Tested on 107 segments, best config validated "
        "on the full 1,497-segment dataset.",
        [[lt, lb], [rt]], click_reveal=True)


def slide_is_signals(prs):
    """Step-by-step breakdown of the 6 IS signals with weight rationale."""
    slide = new_slide(prs)
    add_title(slide, "IS: Six Signals of Quality")
    add_accent_line(slide)

    # Each signal: name, weight, question, how it works, why this weight, color
    signals = [
        ("Semantic Similarity", "(25%)",
         "Does the output preserve the intended meaning?",
         "Sentence embeddings (SBERT) \u2014 cosine distance in 384-dim meaning space",
         'Standard WER treats "admiral" \u2192 "animal" the same as "the" \u2192 "a". '
         "Semantic similarity captures that these are fundamentally different errors "
         "\u2014 one destroys meaning, the other doesn't.",
         TEAL),
        ("Phonetic Similarity", "(15%)",
         "Do the words sound like what was actually said?",
         "Double Metaphone encoding \u2014 maps words to pronunciation codes",
         "Lip-reading outputs are phonetically constrained \u2014 the model sees mouth "
         "shapes, not text. Phonetic similarity measures how well it decoded what "
         "the lips actually produced.",
         TEAL),
        ("Inverse WER", "(15%)",
         "How many words are correct at the surface level?",
         "Standard 1 \u2212 WER (edit distance: substitutions + insertions + deletions)",
         "The universal baseline in speech recognition. Necessary but insufficient "
         "\u2014 a WER of 60% tells you nothing about whether the meaning survived.",
         TEAL),
        ("Inverse WWER", "(15%)",
         "Are the important words correct?",
         'Entities weighted 2\u00d7, content words 1\u00d7, function words 0.5\u00d7',
         'Not all words carry equal information. Losing "the" barely matters; '
         'losing "Admiral McRae" is catastrophic. WWER weights errors by '
         "information content.",
         TEAL),
        ("Named Entity F1", "(15%)",
         "Are names, numbers, and places preserved?",
         "spaCy NER extraction \u2192 precision/recall on proper nouns",
         "Entities are irreplaceable \u2014 a viewer can infer a missing 'the' from "
         "context, but cannot recover a lost name or number. Binary pass/fail "
         "nature makes it the swing factor.",
         CORAL),
        ("Length Ratio", "(15%)",
         "Is the output the right length?",
         "len(hypothesis) / len(reference) \u2014 ideal = 1.0",
         "Safety net for extreme failures: ratio > 2.0 = hallucination (model "
         "rambling), ratio < 0.3 = truncation (model gave up). Lowest real impact "
         "\u2014 most outputs are roughly correct length.",
         LGRAY),
    ]

    bw = Inches(5.76)
    bh = Inches(1.65)
    gap_x = Inches(0.6)
    gap_y = Inches(0.05)

    anim_groups = []
    for i, (name, weight, question, how, why_weight, color) in enumerate(signals):
        col = i % 2
        row = i // 2
        x = MX + col * (bw + gap_x)
        y = CT + row * (bh + gap_y)

        r = add_rect(slide, x, y, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, f"{name} {weight}", x + Inches(0.15), y + Inches(0.06),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(14), color=color, bold=True)
        t2 = add_text(slide, question, x + Inches(0.15), y + Inches(0.34),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(12), color=WHITE)
        t3 = add_text(slide, how, x + Inches(0.15), y + Inches(0.62),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(10), color=LGRAY, italic=True)
        t4 = add_text(slide, f"\u25b8 {why_weight}",
                 x + Inches(0.15), y + Inches(0.92),
                 bw - Inches(0.3), Inches(0.68),
                 size=Pt(11), color=GOLD)
        anim_groups.append([r, t1, t2, t3, t4])

    # Formula at bottom
    add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + InvWWER + NEA + Length)"
        "   \u2022   Score: 0\u20135   \u2022   Threshold: IS \u2265 3.0",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Six signals with weight rationale. Semantic (25%) gets the highest "
        "weight because meaning preservation is the ultimate goal \u2014 it drives "
        "28.5% of IS variance. The other 5 signals each get 15%. Phonetic, WER, "
        "WWER, and NEA form a 'word accuracy' cluster (60% total weight) that "
        "measures whether the encoder decoded the right words. Length ratio is "
        "a safety check for hallucination and truncation. The 3 independent "
        "dimensions: word accuracy (~60%), meaning preservation (~28%), "
        "output sanity (~9%).",
        anim_groups)


def slide_is_weight_rationale(prs):
    """Explain why IS uses 25%/15% weighting and the 3-dimension design."""
    slide = new_slide(prs)
    add_title(slide, "Why These Weights? Three Dimensions of Quality")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — the 3 dimensions
    lt = add_text(slide, "Three Independent Dimensions",
                  MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)

    dims = [
        ("Word Accuracy", "60%", TEAL,
         "Phonetic + WER + WWER + NEA (4 \u00d7 15%)",
         "All 4 correlate tightly (r > 0.79). Did the model get the right words?"),
        ("Meaning Preservation", "28%", GREEN,
         "Semantic Similarity (1 \u00d7 25%)",
         "Highest single weight \u2014 meaning is the ultimate deliverable."),
        ("Output Sanity", "9%", LGRAY,
         "Length Ratio (1 \u00d7 15%)",
         "Safety net: catches hallucination (too long) and truncation (too short)."),
    ]

    py = CT + Inches(0.55)
    dim_shapes = []
    for name, pct, color, signals, desc in dims:
        r = add_rect(slide, MX, py, col_w, Inches(1.35), fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, name, MX + Inches(0.2), py + Inches(0.08),
                 Inches(3.5), Inches(0.35), size=Pt(16), color=color, bold=True)
        add_text(slide, pct, MX + col_w - Inches(1.0), py + Inches(0.08),
                 Inches(0.8), Inches(0.35), size=Pt(16), color=color,
                 bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, signals, MX + Inches(0.2), py + Inches(0.45),
                 col_w - Inches(0.4), Inches(0.35), size=Pt(13), color=WHITE)
        add_text(slide, desc, MX + Inches(0.2), py + Inches(0.85),
                 col_w - Inches(0.4), Inches(0.4), size=Pt(12), color=LGRAY)
        dim_shapes.append(r)
        py += Inches(1.5)

    # Right column — design rationale
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Why 25% / 15%?", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Semantic gets 25%: meaning is the ultimate deliverable",
         {"bold": True, "color": GREEN}),
        "If a viewer understands the message, the transcription succeeded \u2014 "
        "even if exact wording differs. This is the goal of lip reading.",
        ("4 word-accuracy signals share 60%: diminishing returns",
         {"bold": True, "color": TEAL}),
        "WER, WWER, Phonetic, and NEA all measure overlapping aspects of "
        "'did the model get the right words?' Equal 15% weights prevent "
        "any single word-level metric from dominating.",
        ("Length ratio at 15%: a safety net, not a quality signal",
         {"bold": True}),
        "Catches hallucination and truncation \u2014 the two catastrophic "
        "failure modes that other signals can miss.",
        ("Validated: r=0.93 with expert judgment, \u03ba=0.77",
         {"color": GOLD}),
    ], rx, CT + Inches(0.55), rw, Inches(4.5), size=Pt(13))

    add_text(slide,
        "Validated against 1,497 segments: the resulting IS correlates at "
        "r=0.93 with an independent expert heuristic and \u03ba=0.77 with "
        "human-like judgment.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Weight rationale. The 6 IS signals collapse into 3 independent "
        "dimensions: word accuracy (60%, 4 signals at 15% each), meaning "
        "preservation (28%, semantic at 25%), and output sanity (9%, length "
        "at 15%). Semantic gets double weight because meaning is the ultimate "
        "goal. The 4 word-accuracy signals overlap heavily (r>0.79), so equal "
        "15% weights avoid over-counting. Validated: r=0.93 with expert "
        "heuristic, kappa=0.77.",
        [[lt] + dim_shapes, [rt], [rb]], click_reveal=True)


def slide_is_calc_examples(prs):
    """Two concrete IS calculation examples — side-by-side cards."""
    slide = new_slide(prs)
    add_title(slide, "IS in Action: Two Real Segments")
    add_accent_line(slide)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    card_h = Inches(4.6)

    def _draw_calc_card(slide, x, label, is_val, color, ref, hyp, lines, summary):
        """Draw one calculation card at position x. Returns list of all shapes."""
        shapes = []
        r = add_rect(slide, x, CT, col_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        shapes.append(r)

        # Header bar with colored background (reduced height)
        shapes.append(add_rect(slide, x + Inches(0.1), CT + Inches(0.1),
                 col_w - Inches(0.2), Inches(0.32), fill_color=color,
                 corner_radius=True))
        shapes.append(add_text(slide, f"{label} \u2014 IS = {is_val}",
                 x + Inches(0.1), CT + Inches(0.1),
                 col_w - Inches(0.2), Inches(0.32),
                 size=Pt(16), color=BG, bold=True, align=PP_ALIGN.CENTER))

        # Ref / Hyp (increased font size)
        shapes.append(add_rich_text(slide, [
            [("Ref: ", {"size": Pt(14), "color": LGRAY, "bold": True}),
             (f"\u201c{ref}\u201d", {"size": Pt(14), "color": WHITE})],
            [("Hyp: ", {"size": Pt(14), "color": LGRAY, "bold": True}),
             (f"\u201c{hyp}\u201d", {"size": Pt(14), "color": WHITE})],
        ], x + Inches(0.25), CT + Inches(0.55), col_w - Inches(0.5), Inches(0.65)))

        # Calculation rows (increased font size)
        cy = CT + Inches(1.35)
        for name, val, mult, result, clr in lines:
            shapes.append(add_text(slide, name, x + Inches(0.3), cy, Inches(1.8), Inches(0.32),
                     size=Pt(14), color=LGRAY))
            shapes.append(add_text(slide, val, x + Inches(2.2), cy, Inches(0.7), Inches(0.32),
                     size=Pt(14), color=clr, bold=True))
            shapes.append(add_text(slide, mult, x + Inches(2.9), cy, Inches(0.8), Inches(0.32),
                     size=Pt(14), color=LGRAY))
            shapes.append(add_text(slide, result, x + Inches(3.7), cy, Inches(0.9), Inches(0.32),
                     size=Pt(14), color=WHITE, bold=True))
            cy += Inches(0.35)

        # Summary
        shapes.append(add_text(slide, summary,
                 x + Inches(0.3), cy + Inches(0.2), col_w - Inches(0.6), Inches(0.4),
                 size=Pt(15), color=color, bold=True))
        return shapes

    # --- Left: Good segment ---
    good_lines = [
        ("Semantic Sim", "0.82", "\u00d7 0.25", "= 0.205", GREEN),
        ("Phonetic Sim", "0.89", "\u00d7 0.15", "= 0.134", GREEN),
        ("Inverse WER", "0.71", "\u00d7 0.15", "= 0.107", TEAL),
        ("Inverse WWER", "0.76", "\u00d7 0.15", "= 0.114", TEAL),
        ("NEA F1", "1.00", "\u00d7 0.15", "= 0.150", TEAL),
        ("Length Ratio", "0.89", "\u00d7 0.15", "= 0.134", TEAL),
    ]
    r1 = _draw_calc_card(slide, MX,
        "Good Segment", "4.2", GREEN,
        "allow you to work with the team in a more",
        "allow you to work with a team and more",
        good_lines, "Sum \u00d7 5 = 4.22 \u2192 IS 4.2 (Good)")

    # --- Right: Bad segment ---
    bad_lines = [
        ("Semantic Sim", "0.04", "\u00d7 0.25", "= 0.010", CORAL),
        ("Phonetic Sim", "0.12", "\u00d7 0.15", "= 0.018", CORAL),
        ("Inverse WER", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Inverse WWER", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("NEA F1", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Length Ratio", "1.00", "\u00d7 0.15", "= 0.150", LGRAY),
    ]
    r2 = _draw_calc_card(slide, MX + col_w + gap,
        "Bad Segment", "0.9", CORAL,
        "carry strap",
        "holocaust denier explanation of the final act",
        bad_lines, "Sum \u00d7 5 = 0.89 \u2192 IS 0.9 (Failed)")

    _finish(slide, 0,
        "Two IS calculation examples. Left: good segment (IS 4.2) with high "
        "scores across all signals. Right: hallucination (IS 0.9) where only "
        "length ratio is non-zero — the output is a completely different topic. "
        "The formula is IS = (sum of weighted scores) x 5, mapping to 0-5 scale.",
        [r1, r2], click_reveal=True)


def slide_is_radar(prs):
    """Radar chart showing captured vs failed IS profiles -- large centered."""
    slide = new_slide(prs)
    add_title(slide, "IS Radar: Success vs Failure Profile")
    add_accent_line(slide)
    sub = add_text(slide,
        "Captured segments (green) are strong across all 6 signals. "
        "Failed segments (red) collapse on meaning and entities.",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)
    img_top = CT + Inches(0.45)
    img_h = SL_H - img_top - Inches(0.55)
    img_w = Inches(8.5)
    img_l = (SL_W - img_w) / 2
    # Prefer dual radar (LRS3 vs YouTube) if available
    radar_key = "P6b_radar_dual" if IMG.get("P6b_radar_dual", Path("x")).exists() \
                else "P6_is_radar"
    img = add_image(slide, radar_key, img_l, img_top,
                    width=img_w, height=img_h)
    ann_w = Inches(2.5)
    if radar_key == "P6b_radar_dual":
        add_text(slide, "\u25cf LRS3 Benchmark (WER 25.4%)", MX, SL_H - Inches(0.55),
                 Inches(3.5), Inches(0.3), size=Pt(12), color=GREEN, bold=True)
        add_text(slide, "\u25cf Real-World YouTube (WER 64.1%)",
                 MX + CW - Inches(3.5), SL_H - Inches(0.55),
                 Inches(3.5), Inches(0.3), size=Pt(12), color=CORAL, bold=True,
                 align=PP_ALIGN.RIGHT)
    else:
        add_text(slide, "\u25cf Captured (IS \u2265 3.0)", MX, SL_H - Inches(0.55),
                 ann_w, Inches(0.3), size=Pt(12), color=GREEN, bold=True)
        add_text(slide, "\u25cf Failed (IS < 3.0)",
                 MX + CW - ann_w, SL_H - Inches(0.55),
                 ann_w, Inches(0.3), size=Pt(12), color=CORAL, bold=True,
                 align=PP_ALIGN.RIGHT)
    _finish(slide, 0,
        "Radar chart comparing mean component values for IS >= 3.0 "
        "(green) vs IS < 3.0 (red). Captured segments are strong across "
        "all 6 signals. Failed segments collapse on meaning and entity "
        "preservation while maintaining only partial length ratio. "
        "The biggest gaps between green and red are on Semantic and NEA "
        "axes, confirming these as the primary differentiators.",
        [[img]])


def slide_is_wer_scatter(prs):
    """IS vs WER scatter showing 'the gap'."""
    build_split(prs, 0,
        "The Gap: Where WER Lies Most",
        "P7_is_wer_scatter",
        notes="Scatter plot of WER vs IS for all 1,497 segments. The green "
              "highlighted region shows 147 segments where WER > 40% but IS >= 3.0.",
        big_num="147",
        num_color=GREEN,
        num_label="segments in the gap: high WER, useful IS",
        bullets=[
            ("WER > 40% but IS \u2265 3.0 \u2014 useful output that WER discards", {"bold": True}),
            "Synonyms, tense changes, and filler words inflate WER",
            "Semantic meaning is preserved despite word-level errors",
            ("Validates IS as a more honest metric for VSP", {"color": TEAL}),
        ])


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 7 — THE INTELLIGIBILITY SCORE
# ═══════════════════════════════════════════════════════════════════════

def slide_07(prs):
    slide = new_slide(prs)
    add_title(slide, "Intelligibility Score: 39.9% Properly Captured")
    add_accent_line(slide)

    # 6 signal blocks
    signals = [
        ("Semantic\nSim", "25%", TEAL),
        ("Phonetic\nSim", "15%", TEAL),
        ("Inv.\nWER", "15%", TEAL),
        ("Inv.\nWWER", "15%", TEAL),
        ("NEA\nF1", "15%", CORAL),
        ("Length\nRatio", "15%", LGRAY),
    ]
    bw = Inches(1.7)
    bh = Inches(1.1)
    gap = Inches(0.22)
    total = 6 * bw + 5 * gap
    bx = (SL_W - total) / 2
    by = CT

    signal_shapes = []
    for i, (label, weight, color) in enumerate(signals):
        x = bx + i * (bw + gap)
        r = add_rect(slide, x, by, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t = add_text(slide, f"{label}\n({weight})", x + Inches(0.1), by + Inches(0.1),
                 bw - Inches(0.2), bh - Inches(0.2),
                 size=Pt(11), color=WHITE, align=PP_ALIGN.CENTER)
        signal_shapes.append(r)
        signal_shapes.append(t)

    # Key callout
    callout = add_text(slide,
        "IS ≥ 3.0 = Properly Captured: 39.9% — 3.5× more than WER's 11.4%\n"
        "Phonetic similarity: 41.5% mean, r=0.943 with IS (strongest single signal)",
        MX, by + bh + Inches(0.2), CW, Inches(0.55),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # 5 tier bars
    tiers = [
        ("18.4% Excellent", 18.4, GREEN),
        ("21.4% Good", 21.4, TEAL),
        ("21.7% Fair", 21.7, YELLOW),
        ("22.4% Poor", 22.4, ORANGE),
        ("16.0% Failed", 16.0, RED),
    ]
    bar_y = by + bh + Inches(1.05)
    bar_h = Inches(0.38)
    bar_gap = Inches(0.12)
    max_w = Inches(8.0)
    label_w = Inches(3.0)
    bar_x = MX + label_w + Inches(0.2)

    tier_shapes = []
    for i, (label, val, color) in enumerate(tiers):
        y = bar_y + i * (bar_h + bar_gap)
        lbl = add_text(slide, label, MX, y, label_w, bar_h,
                 size=Pt(13), color=WHITE, align=PP_ALIGN.RIGHT)
        w = int(max_w * val / 25.0)  # scale to max
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color)
        tier_shapes.append(lbl)
        tier_shapes.append(bar)

    _finish(slide, 7,
        "The Intelligibility Score combines 6 signals into a 0-5 composite. "
        "Key insight: 39.9% of segments are properly captured (IS >= 3.0) — "
        "3.5x more than WER's 11.4% 'usable.' WER dramatically overstates "
        "failure. Methodology: LLM-distilled evaluation — the "
        "rubric, selected signals and weights, defined tier boundaries. "
        "Validated across 16 decode configs: LLM heuristic judge r=0.925 "
        "with IS, 88.6% agreement.",
        [signal_shapes, [callout], tier_shapes], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 8 — FAILURE MODE TAXONOMY (BAR CHART)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 8 — FAILURE MODE TAXONOMY (BAR CHART)
# ═══════════════════════════════════════════════════════════════════════

def slide_08(prs):
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy")
    add_accent_line(slide)

    add_text(slide,
        "900 segments failed (IS < 3.0) \u2014 how often does each mode occur?",
        MX, CT, CW, Inches(0.35), size=Pt(14), color=LGRAY, italic=True)

    modes = [
        ("Wrong Topic", 31.6, 284, GOLD),
        ("Accumulated Errors", 24.4, 220, LGRAY),
        ("Right Topic, Wrong Details", 22.7, 204, TEAL),
        ("Hallucination", 12.3, 111, CORAL),
        ("Signal Loss", 9.0, 81, MGRAY),
    ]

    bar_h = Inches(0.65)
    bar_gap = Inches(0.2)
    label_w = Inches(3.5)
    max_bar_w = Inches(6.0)
    bar_x = MX + label_w + Inches(0.2)
    start_y = CT + Inches(0.55)

    bar_groups = []
    for i, (name, pct, count, color) in enumerate(modes):
        y = start_y + i * (bar_h + bar_gap)
        # Label
        lbl = add_text(slide, name, MX, y, label_w, bar_h,
                 size=Pt(16), color=WHITE, bold=True, align=PP_ALIGN.RIGHT)
        # Bar
        w = max(Inches(0.2), int(max_bar_w * pct / 32.0))
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color,
                       corner_radius=True)
        # Value label
        val = add_text(slide, f"{pct}% ({count})",
                 bar_x + w + Inches(0.15), y, Inches(1.8), bar_h,
                 size=Pt(14), color=LGRAY)
        bar_groups.append([lbl, bar, val])

    add_text(slide,
             "Failures are diverse — no single fix. Each roadmap phase "
             "targets specific modes.",
             MX, Inches(6.4), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    _finish(slide, 8,
        "900 failed segments classified into 5 failure categories. Wrong Topic "
        "is the largest (31.6%), combining topic drift and phonetic confusion. "
        "Hallucination (12.3%) is the most dangerous: fluent, confident, "
        "completely fabricated. Right Topic Wrong Details (22.7%) loses names and "
        "numbers. This taxonomy maps directly to our roadmap.",
        bar_groups)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_1a(prs):
    """Failure mode taxonomy: 5 academically-grounded categories as animated cards."""
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy: 5 Categories")
    add_accent_line(slide)

    add_text(slide,
        "900 failed segments (IS < 3.0) classified into 5 mutually exclusive "
        "categories \u2014 each segment gets exactly one label, checked 1\u21925.",
        MX, CT, CW, Inches(0.28), size=Pt(13), color=LGRAY, italic=True)

    add_text(slide,
        "Grounded in ASR error taxonomy (Fosler-Lussier 2004) and "
        "LLM hallucination analysis (ACL 2025)",
        MX, CT + Inches(0.28), CW, Inches(0.22),
        size=Pt(10), color=MGRAY, italic=True)

    modes = [
        ("1. Signal Loss", "9.0%", "81 segments", LGRAY,
         "Nothing came out",
         "Empty output OR length ratio < 0.3",
         "Ref: \u201cthe thirteenth amendment\u201d \u2192 Hyp: \u201c\u201d"),
        ("2. Hallucination", "12.3%", "111 segments", CORAL,
         "Model invented fake text",
         "WER \u2265 100% (output longer than reference)",
         "Ref: \u201ccarry strap\u201d \u2192 Hyp: \u201cholocaust denier explanation of the final act\u201d"),
        ("3. Wrong Topic", "31.6%", "284 segments", GOLD,
         "Mouth shapes decoded to wrong domain",
         "Semantic < 0.2 (phonetic-matched or not)",
         "Ref: \u201cweight loss and diet\u201d \u2192 Hyp: \u201cwanted to be a princess\u201d"),
        ("4. Right Topic, Wrong Details", "22.7%", "204 segments", TEAL,
         "Roughly right but names/content words lost",
         "NEA F1 < 20% OR key content words substituted (Semantic \u2265 0.2)",
         "Ref: \u201c13th amendment is going\u201d \u2192 Hyp: \u201c13th may mean something to him\u201d"),
        ("5. Accumulated Errors", "24.4%", "220 segments", LGRAY,
         "Many small errors compound",
         "IS < 3.0 and doesn\u2019t match categories 1\u20134",
         "Many words slightly wrong throughout, meaning erodes"),
    ]

    card_h = Inches(0.88)
    gap = Inches(0.08)
    y0 = CT + Inches(0.55)
    name_w = Inches(3.5)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes):
        y = y0 + i * (card_h + gap)

        # Card background
        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)

        # Left: category name + percentage
        t1 = add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.05),
                 name_w - Inches(0.3), Inches(0.3),
                 size=Pt(15), color=color, bold=True)

        # Left: one-line description + count
        t2 = add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.38),
                 name_w - Inches(0.3), Inches(0.45),
                 size=Pt(11), color=LGRAY)

        # Right: detection rule
        t3 = add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.06),
                 rule_w - Inches(0.15), Inches(0.35),
                 size=Pt(12), color=WHITE)

        # Right: example
        t4 = add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.45),
                 rule_w - Inches(0.15), Inches(0.35),
                 size=Pt(11), color=LGRAY, italic=True)

        anim_groups.append([r, t1, t2, t3, t4])

    # Priority order footer
    add_text(slide,
        "Priority: Signal Loss \u2192 Hallucination \u2192 Wrong Topic \u2192 "
        "Right Topic Wrong Details \u2192 Accumulated Errors",
        MX, Inches(6.55), CW, Inches(0.35),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Five-category failure taxonomy grounded in ASR error research "
        "(Fosler-Lussier 2004) and LLM hallucination analysis (ACL 2025). "
        "Key insight: Wrong Topic is the LARGEST category at 31.6% — it merges "
        "the old Topic Drift and Phonetic Wrong Topic categories because the fix "
        "is the same (stronger LLM, more training data). Signal Loss and "
        "Accumulated Errors are the bookends: one produces nothing, the other "
        "produces something but death-by-a-thousand-cuts erodes meaning. "
        "Each segment gets exactly one label, checked in priority order 1 through 5.",
        anim_groups, click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — REAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — REAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_2(prs):
    """Three concrete failure mode examples for the hardest-to-distinguish categories."""
    slide = new_slide(prs)
    add_title(slide, "Failure Modes: Real Examples")
    add_accent_line(slide)

    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(4.9)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.05)

    examples = [
        {
            "title": "Hallucination",
            "pct": "12.3%",
            "color": CORAL,
            "ref": "carry strap",
            "hyp": "holocaust denier explanation\nof the final act",
            "wer": "100%", "is_score": "0.1",
            "why_label": "Why this category?",
            "why": "The model generated 8 words from\n"
                   "a 2-word input. The LLM\u2019s language\n"
                   "model \u2018ran away\u2019 \u2014 output is fluent\n"
                   "English but completely fabricated.\n"
                   "Distinguishing feature: output is\n"
                   "LONGER than reference (WER \u2265 100%).",
        },
        {
            "title": "Wrong Topic",
            "pct": "31.6%",
            "color": GOLD,
            "ref": "i\u2019ve made lots of videos\nabout weight loss and diet",
            "hyp": "when i was a little girl i\nalways wanted to be a princess",
            "wer": "97%", "is_score": "0.38",
            "why_label": "Why this category?",
            "why": "Output is similar LENGTH to\n"
                   "reference (not hallucination) but\n"
                   "about a completely different subject.\n"
                   "The visual encoder extracted mouth\n"
                   "shapes that the LLM mapped to a\n"
                   "wrong but coherent domain.",
        },
        {
            "title": "Right Topic, Wrong Details",
            "pct": "22.7%",
            "color": TEAL,
            "ref": "about the 13th amendment\nthe 13th amendment is going",
            "hyp": "13th may mean something to\nhim because it can help him",
            "wer": "81%", "is_score": "2.14",
            "why_label": "Why this category?",
            "why": "The word \u201c13th\u201d survived but\n"
                   "\u201camendment\u201d was lost. A viewer\n"
                   "might guess the topic (law) but\n"
                   "critical entity information is\n"
                   "irrecoverable. Key distinction:\n"
                   "Semantic \u2265 0.2 (topic is correct).",
        },
    ]

    anim_groups = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)
        card_shapes = []

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # Title + percentage
        card_shapes.append(add_text(slide, f'{ex["title"]}  ({ex["pct"]})',
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.35),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER))

        # Reference
        card_shapes.append(add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.5),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=LGRAY, bold=True))
        card_shapes.append(add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.7), cw_card - Inches(0.3), Inches(0.6),
                 size=Pt(10), color=WHITE, italic=True))

        # Hypothesis
        card_shapes.append(add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.35),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=LGRAY, bold=True))
        card_shapes.append(add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.55), cw_card - Inches(0.3), Inches(0.6),
                 size=Pt(10), color=ex["color"], italic=True))

        # Metrics badge
        card_shapes.append(add_text(slide, f'WER {ex["wer"]}  |  IS {ex["is_score"]}',
                 x + Inches(0.15), cy + Inches(2.25), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(11), color=WHITE, bold=True, align=PP_ALIGN.CENTER))

        # Why explanation
        card_shapes.append(add_text(slide, ex["why_label"],
                 x + Inches(0.15), cy + Inches(2.7),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=TEAL, bold=True))
        card_shapes.append(add_text(slide, ex["why"],
                 x + Inches(0.15), cy + Inches(2.9), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(10), color=LGRAY))

        anim_groups.append(card_shapes)

    _finish(slide, 0,
        "Three real examples for the three most confusing categories. "
        "Hallucination vs Wrong Topic: hallucination generates MORE words than "
        "the reference (WER >= 100%), while Wrong Topic substitutes at similar "
        "length. Wrong Topic vs Right Topic Wrong Details: semantic similarity "
        "threshold of 0.2 separates them — below 0.2 means completely different "
        "subject, above 0.2 means topic preserved but details lost. "
        "Right Topic Wrong Details is the 'frustrating near-miss' — you can tell "
        "what the speaker was ABOUT but not what they SAID.",
        anim_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — IMPACT & ROADMAP MAPPING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — IMPACT & ROADMAP MAPPING
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_3(prs):
    """Failure mode impact and what fixes each of the 5 categories."""
    slide = new_slide(prs)
    add_title(slide, "Failure Modes: Impact & What Fixes Them")
    add_accent_line(slide)

    add_text(slide,
        "Each category maps to a specific remedy \u2014 "
        "no single fix addresses all failure types.",
        MX, CT, CW, Inches(0.3),
        size=Pt(13), color=LGRAY, italic=True)

    headers = ["Category", "%", "Severity", "What Fixes It"]
    rows = [
        ["Signal Loss", "9.0%", "Low \u2014 obvious",
         "Quality filtering, longer segments"],
        ["Hallucination", "12.3%", "Moderate \u2014 easy to\nidentify and ignore",
         "Anti-hallucination prompts,\nconfidence gating, GER*"],
        ["Wrong Topic", "31.6%", "High \u2014 wrong\ndomain entirely",
         "Stronger LLM, topic-aware\nprompting, more training data"],
        ["Right Topic,\nWrong Details", "22.7%", "Very High \u2014 clients\nwill distrust model",
         "Entity injection, domain\nadaptation, fine-tuning"],
        ["Accumulated\nErrors", "24.4%", "Medium \u2014 gradual\nmeaning erosion",
         "General model improvement,\nN-best aggregation"],
    ]

    row_colors = {
        0: {0: LGRAY, 2: MGRAY},
        1: {0: CORAL, 2: ORANGE},
        2: {0: GOLD, 2: RED},
        3: {0: TEAL, 2: DRED},
        4: {0: LGRAY, 2: YELLOW},
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.45), CW,
                    row_height=Inches(0.5),
                    col_widths=[Inches(2.0), Inches(1.0), Inches(3.5), Inches(5.63)],
                    text_size=Pt(11),
                    row_colors=row_colors)

    # GER footnote
    ger_note = add_text(slide,
        "*GER = Gross Error Rate \u2014 the fraction of outputs with catastrophic "
        "errors (WER > 100%). Filters out the worst hallucinations before "
        "they reach users.",
        MX, Inches(5.0), CW, Inches(0.35),
        size=Pt(11), color=MGRAY, italic=True)

    # Key insight callout
    callout_r = add_rect(slide, MX, Inches(5.4), CW, Inches(0.65), fill_color=NAVY2,
             border_color=TEAL, border_width=Pt(1), corner_radius=True)

    callout_t = add_text(slide,
        "Key insight: Wrong Topic (31.6%) is the largest failure mode and "
        "most likely to improve with a stronger LLM (Llama 3.1 8B). "
        "Right Topic Wrong Details (22.7%) is the most dangerous \u2014 clients "
        "will distrust the model, and confidence values for those words "
        "are likely always low. Over half of failures need better language modeling.",
        MX + Inches(0.2), Inches(5.45), CW - Inches(0.4), Inches(0.55),
        size=Pt(13), color=WHITE)

    severity_t = add_text(slide,
        "Hallucination: not that bad \u2014 relatively easy to identify and ignore "
        "but still painful. Right Topic Wrong Details: very high impact.",
        MX, Inches(6.15), CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Impact and fixes table for the 5-category taxonomy. Right Topic Wrong "
        "Details is the most dangerous because clients cannot trust the output \u2014 "
        "confidence values for those words are likely always low. Hallucination is "
        "relatively easy to identify and ignore but still painful. Wrong Topic is "
        "the LARGEST at 31.6% and the most amenable to improvement through LLM "
        "upgrade. GER = Gross Error Rate, the fraction of outputs with catastrophic "
        "errors. 54.3% of failures trace to the LLM backbone being too weak.",
        [[tbl], [ger_note, callout_r, callout_t, severity_t]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 9 — PERFORMANCE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 9 — PERFORMANCE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════

def slide_09(prs):
    build_full_image(prs, 9, "How Results Vary Across Configurations", "boxplot",
        subtitle="Each box shows the WWER distribution for one of 13 decode configs. "
                 "Lower is better.",
        bottom_text="Most segments: 50\u201380% WER. ~11% always good, ~16% always bad "
                    "\u2014 regardless of parameters.",
        notes="This boxplot shows WWER distribution across all 13 decode "
              "experiments. The box is consistently in the 50-80% range. "
              "About 11% of segments are always good regardless of parameters, "
              "and about 16% are always bad. The bottleneck is the visual "
              "encoder, not decode strategy.")


def slide_metric_transition(prs):
    """The three numbers: 64.1% -> 39.9% -> 50.9%."""
    slide = new_slide(prs)
    add_title(slide, "Three Numbers That Tell the Real Story")
    add_accent_line(slide)

    card_w = CW - Inches(2.0)
    card_h = Inches(1.25)
    card_x = MX + Inches(1.0)
    arrow_h = Inches(0.4)

    c1_y = CT + Inches(0.2)
    g1 = []
    g1.append(add_rect(slide, card_x, c1_y, card_w, card_h,
                        fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                        corner_radius=True))
    g1.append(add_text(slide, "64.1%", card_x + Inches(0.3), c1_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=CORAL, bold=True))
    g1.append(add_text(slide, "What WER reports\n\"Two-thirds of words are wrong\"",
                        card_x + Inches(3.0), c1_y + Inches(0.15),
                        card_w - Inches(3.3), card_h - Inches(0.3),
                        size=Pt(15), color=LGRAY))
    # Strikethrough line
    g1.append(add_rect(slide, card_x + Inches(0.4), c1_y + card_h / 2 - Pt(1.5),
                        Inches(2.3), Pt(3), fill_color=CORAL))

    a1_y = c1_y + card_h + Inches(0.05)
    g1_arrow = []
    g1_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a1_y, Inches(0.6), arrow_h,
                              size=Pt(20), color=TEAL, align=PP_ALIGN.CENTER))

    c2_y = a1_y + arrow_h
    g2 = []
    g2.append(add_rect(slide, card_x, c2_y, card_w, card_h,
                        fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                        corner_radius=True))
    g2.append(add_text(slide, "39.9%", card_x + Inches(0.3), c2_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=TEAL, bold=True))
    g2.append(add_text(slide,
        "What IS reveals: 597 of 1,497 segments\ndeliver genuinely useful output",
        card_x + Inches(3.0), c2_y + Inches(0.15),
        card_w - Inches(3.3), card_h - Inches(0.3),
        size=Pt(15), color=WHITE))

    a2_y = c2_y + card_h + Inches(0.05)
    g2_arrow = []
    g2_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a2_y, Inches(0.6), arrow_h,
                              size=Pt(20), color=GREEN, align=PP_ALIGN.CENTER))

    c3_y = a2_y + arrow_h
    g3 = []
    g3.append(add_rect(slide, card_x, c3_y, card_w, card_h,
                        fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                        corner_radius=True))
    g3.append(add_text(slide, "50.9%", card_x + Inches(0.3), c3_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=GREEN, bold=True))
    g3.append(add_text(slide,
        "+ Salvage recovery: 165 additional segments\n1 in 2 segments delivers useful output",
        card_x + Inches(3.0), c3_y + Inches(0.15),
        card_w - Inches(3.3), card_h - Inches(0.3),
        size=Pt(15), color=WHITE))

    _finish(slide, 0,
        "The three numbers: WER 64.1% (misleading), IS captured 39.9% (real), "
        "with salvage 50.9% (the full picture).",
        [g1, g1_arrow + g2, g2_arrow + g3], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

def slide_10(prs):
    build_two_col(prs, 10, "Three Root Causes \u2014 Why 64.1% WER?",
        "Root Causes", [
            ("1. Domain Mismatch", {"bold": True, "color": TEAL}),
            "Model trained on TED talks (LRS3); real-world: DIY, cooking, sports",
            ("2. Short Segments Fail", {"bold": True, "color": TEAL}),
            "Under 10 words: only 32% captured vs 49% for 20+ words",
            ("3. Hallucination (20.5%)", {"bold": True, "color": TEAL}),
            "LLM prior overwhelms weak visual signal \u2014 fluent but fabricated",
        ],
        "By the Numbers", [
            ("Business/Finance: IS 3.08, 57% captured", {"color": GREEN}),
            ("DIY/Home: IS 2.13, 30% captured \u2014 27pp gap", {"color": CORAL}),
            "Short (5\u201310 words): 74% WER, 32% captured",
            "Long (20+ words): 55% WER, 49% captured \u2014 17pp gap",
            ("28.2% of failures = drift + hallucination", {"color": CORAL, "bold": True}),
        ],
        "Three root causes explain most failures: domain mismatch (model trained "
        "on TED, tested on YouTube), short segments lacking context, and "
        "hallucination where the LLM generates fluent but fabricated text.",
        left_color=CORAL, right_color=TEAL)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 11 — NAMED ENTITY ACCURACY
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 11 — NAMED ENTITY ACCURACY
# ═══════════════════════════════════════════════════════════════════════

def slide_11(prs):
    slide = new_slide(prs)
    add_title(slide, "Named Entity Accuracy: The Largest Differentiator")
    add_accent_line(slide)

    # Left column with bullets, right column with scatter plot
    col_w = Inches(4.8)
    lt = add_text(slide, "What are named entities?", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Names (Admiral McRae), numbers (13th), places, "
        "organizations",
        "Either correct or destroyed \u2014 no partial credit",
        ("Captured: 74% NEA F1 vs Failed: 16%",
         {"bold": True, "color": CORAL}),
        "58pp gap \u2014 largest differentiator of any signal",
        "17.3% of IS variance (highest for 15%-weight signal)",
        'A viewer can guess a missing "the" but not a missing name',
    ], MX, CT + Inches(0.5), col_w, Inches(3.8), size=Pt(13))

    # Large image on right -- increased gap to prevent occlusion with point 4
    img_l = MX + col_w + Inches(0.5)
    img_w = CW - col_w - Inches(0.5)
    img = add_image(slide, "nea_scatter", img_l, CT, width=img_w)

    _finish(slide, 11,
        "PLOT EXPLANATION (NEA Recall vs WWER Per Segment):\n\n"
        "This scatter plot shows every segment as a dot, with WWER (Weighted "
        "Word Error Rate) on the x-axis and Named Entity Recall on the y-axis. "
        "Each dot color represents a different decode configuration (A: Baseline, "
        "C: LenPen=1, E: Sampling t=0.5, G: Greedy, J: LP1+t=0.5).\n\n"
        "KEY PATTERNS TO NOTE:\n"
        "1. Top-left cluster (low WWER, high NEA): These are the success cases \u2014 "
        "segments where both word accuracy and entity preservation are high. "
        "Most captured segments live here.\n\n"
        "2. Bottom row at NEA=0: A large cluster of segments with ZERO entity "
        "recall across ALL WWER values. This means many segments lose ALL named "
        "entities regardless of how many other words they get right. This is why "
        "NEA is the swing factor \u2014 entity destruction is binary.\n\n"
        "3. Right side (WWER > 100%): These are hallucinated segments where the "
        "model generates more wrong words than the reference contains. Even some "
        "of these have high NEA (top-right dots) \u2014 meaning the model hallucinated "
        "but still preserved some entity names.\n\n"
        "4. All configurations cluster together: different decode parameters "
        "don't change the fundamental NEA vs WWER relationship. The visual "
        "encoder determines entity preservation, not the decoder.\n\n"
        "TAKEAWAY: Named entities are binary \u2014 either preserved or destroyed. "
        "The dense cluster at NEA=0 across all WWER levels shows that entity "
        "loss is catastrophic and independent of general word accuracy. This is "
        "why NEA accounts for 17.3% of IS variance despite only 15% weight \u2014 "
        "it's the single most discriminating signal between captured and failed.",
        [[lt, lb], [img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 12 — 13 TUNING EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE — TUNING SUMMARY (condensed)
# ═══════════════════════════════════════════════════════════════════════

def slide_tuning_summary(prs):
    """Condensed tuning section: 5 slides into 1."""
    slide = new_slide(prs)
    add_title(slide, "Decode Tuning: 13 Experiments, Minimal Gain")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — What we tested (3 short bullets, generous spacing)
    lt = add_text(slide, "What We Tested", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Beam size, length penalty, temperature, sampling",
        "13 experiments (A\u2013M) on 107-segment subset",
        "Best config (J) validated on all 1,497 segments",
    ], MX, CT + Inches(0.5), col_w, Inches(1.8), size=Pt(14))

    # Callout box — key finding (more vertical room)
    r1 = add_rect(slide, MX, CT + Inches(2.6), col_w, Inches(2.2),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    kf_title = add_text(slide, "Key Finding",
             MX + Inches(0.25), CT + Inches(2.75), col_w - Inches(0.5), Inches(0.3),
             size=Pt(16), color=CORAL, bold=True)
    kf_bullets = add_bullets(slide, [
        "Segment rankings identical across all configs (r > 0.92)",
        "Good segments stay good; bad ones stay bad regardless",
        ("Bottleneck = visual encoder, not decode parameters",
         {"bold": True, "color": CORAL}),
    ], MX + Inches(0.25), CT + Inches(3.15), col_w - Inches(0.5), Inches(1.5),
       size=Pt(13))

    # Right — What we found
    rx = MX + col_w + gap
    rt = add_text(slide, "What We Found", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=CORAL, bold=True)

    # Config J note (shorter)
    j_note = add_text(slide,
        "Config J: lenpen=1.0, temp=0.5",
        rx, CT + Inches(0.4), col_w, Inches(0.25),
        size=Pt(12), color=MGRAY, italic=True)

    headers = ["Metric", "Baseline", "Config J", "\u0394"]
    rows = [
        ["Mean IS", "2.52", "2.60", "+0.08"],
        ["Captured (IS\u22653)", "39.9%", "41.2%", "+1.3pp"],
        ["Empty outputs", "4.7%", "0%", "\u221270"],
        ["Hallucinations", "20.5%", "23.2%", "+41"],
        ["Mean WWER", "61.9%", "59.8%", "\u22122.1pp"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.75), col_w,
                    row_height=Inches(0.38),
                    col_widths=[Inches(1.7), Inches(1.2), Inches(1.2), Inches(1.4)],
                    text_size=Pt(12))

    # Verdict — clear of table with breathing room
    verdict = add_text(slide,
        "Eliminates empties but adds hallucinations.\n"
        "Net IS gain: +0.08 \u2014 tuning is mitigation, not a cure.",
        rx, CT + Inches(2.95), col_w, Inches(0.8),
        size=Pt(14), color=LGRAY, italic=True)

    _finish(slide, 0,
        "Condensed tuning results. 13 experiments across 4 decode parameters "
        "showed minimal improvement. Best config (J = lenpen=1.0, temp=0.5) eliminates empty outputs "
        "but increases hallucinations by 13%. Net IS gain only +0.08. "
        "Per-segment rankings are identical across configs (r > 0.92), proving "
        "the bottleneck is the visual encoder, not decode parameters.\n\n"
        "The original slide included a length penalty sensitivity chart showing "
        "the empty-vs-hallucination trade-off: lenpen=-0.5 causes 44.9% empty "
        "outputs; baseline (lenpen=0) has 4.7% empties; lenpen=1.0 (Config J) "
        "eliminates all empties but hallucinations rise from 20.5% to 23.2%; "
        "lenpen=2.0 pushes hallucinations to 52.9%. This demonstrates the "
        "fundamental trade-off: length penalty controls whether the model stays "
        "silent (empty) or fabricates (hallucination). Config J chose the sweet "
        "spot — zero empties at the cost of +41 hallucinations.",
        [[lt, lb], [rt, j_note, tbl], [r1, kf_title, kf_bullets, verdict]],
        click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14 — CURATED EXAMPLES (TABLE)
# ═══════════════════════════════════════════════════════════════════════

def slide_design_philosophy(prs):
    """Deterministic evaluation — not runtime AI."""
    slide = new_slide(prs)
    add_title(slide, "Design Philosophy: Deterministic, Not AI")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — Option A
    lt = add_text(slide, "Option A: LLM per Sample", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(3.5),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_bullets(slide, [
        "Call Claude/GPT for every ref+hyp pair",
        "$$$ per evaluation run",
        "Non-deterministic (varies between runs)",
        "Can't reproduce results",
        "Slow: minutes per 1,497 pairs",
    ], MX + Inches(0.2), CT + Inches(0.7), col_w - Inches(0.4), Inches(2.5),
       size=Pt(14), bullet_color=CORAL)

    # Right — Option B (ours)
    rx = MX + col_w + gap
    rt = add_text(slide, "Option B: Design-Time LLM (Ours)", rx, CT, col_w,
                  Inches(0.4), size=Pt(18), color=GREEN, bold=True)
    r2 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(3.5),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_bullets(slide, [
        ("Rubric, signals, weights designed at development time",
         {"bold": True}),
        "Distilled into deterministic Python formulas",
        ("$0 per evaluation run", {"color": GREEN}),
        ("100% reproducible", {"color": GREEN}),
        "Instant: seconds for 1,497 pairs",
        ("Same framework, unlimited runs", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(0.7), col_w - Inches(0.4), Inches(2.5),
       size=Pt(14), bullet_color=GREEN)

    # Bottom
    add_text(slide,
        "Validated: 88.6% agreement with IS \u2265 3.0 threshold, r = 0.85 "
        "Pearson correlation with LLM judge gold standard.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Two approaches: Option A calls an LLM for every pair — expensive, "
        "non-deterministic, slow. Option B (ours): the entire "
        "evaluation framework was designed at development time, then distilled into "
        "deterministic formulas. Zero cost per run, 100% reproducible. "
        "Validated at 88.6% agreement, r=0.85.",
        [[r1], [r2]], click_reveal=True)


def slide_is_dimensions(prs):
    """Three quality dimensions from PCA analysis."""
    slide = new_slide(prs)
    add_title(slide, "Three Dimensions of Quality")
    add_accent_line(slide)

    add_text(slide, "PCA reveals the 6 IS signals collapse into 3 independent dimensions:",
             MX, CT, CW, Inches(0.4), size=Pt(15), color=LGRAY)

    # Three cards
    dims = [
        ("Word Accuracy", "60%", "of IS variance",
         "WER + WWER + Phonetic\n(r > 0.79 between them)",
         "The visual encoder\u2019s core capability", TEAL),
        ("Meaning Preservation", "29%", "of IS variance",
         "Semantic similarity\n(sentence embeddings)",
         "Tiebreaker between\nsimilar-accuracy segments", GREEN),
        ("Output Sanity", "9%", "of IS variance",
         "Length ratio\n(hyp vs ref word count)",
         "Catches hallucination\nand truncation", LGRAY),
    ]

    cw_card = Inches(3.6)
    ch_card = Inches(4.0)
    gap = Inches(0.5)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.55)

    card_groups = []
    for i, (name, pct, label, signals, insight, color) in enumerate(dims):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5), corner_radius=True)

        # Big percentage
        t1 = add_text(slide, pct, x + Inches(0.2), cy + Inches(0.2),
                 cw_card - Inches(0.4), Inches(0.6),
                 size=Pt(36), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, label, x + Inches(0.2), cy + Inches(0.8),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

        # Name
        t3 = add_text(slide, name, x + Inches(0.2), cy + Inches(1.3),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(16), color=color, bold=True, align=PP_ALIGN.CENTER)

        # Signals
        t4 = add_text(slide, signals, x + Inches(0.2), cy + Inches(1.8),
                 cw_card - Inches(0.4), Inches(0.8),
                 size=Pt(13), color=WHITE, align=PP_ALIGN.CENTER)

        # Insight
        t5 = add_text(slide, insight, x + Inches(0.2), cy + Inches(2.8),
                 cw_card - Inches(0.4), Inches(0.8),
                 size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

        card_groups.append([r, t1, t2, t3, t4, t5])

    _finish(slide, 0,
        "PCA analysis reveals three independent dimensions. Word Accuracy "
        "(60% of variance) combines WER, WWER, and Phonetic \u2014 they all measure "
        "the same thing: visual encoder quality. Meaning Preservation (29%) is "
        "the semantic similarity tiebreaker. Output Sanity (9%) is mostly length "
        "ratio. Four of six signals are redundant \u2014 but deliberate: cross-"
        "validation makes the metric robust.\n\n"
        "CORRELATION BETWEEN DIMENSIONS: Word accuracy signals (WER, WWER, "
        "Phonetic) are highly correlated with each other (r > 0.79). Semantic "
        "is moderately correlated with word accuracy. Length ratio is the most "
        "independent dimension (9.1% of total variance). This confirms these "
        "are genuinely 3 independent dimensions, not redundant signals.",
        card_groups, click_reveal=True)


def slide_domain_mismatch(prs):
    """Full topic analysis — domain mismatch detail."""
    slide = new_slide(prs)
    add_title(slide, "Domain Mismatch: Training vs Reality")
    add_accent_line(slide)

    col_w = Inches(6.5)
    gap = Inches(0.6)

    # Left — topic table
    lt = add_text(slide, "Performance by Topic", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Topic", "IS", "Captured", "Judge N%"],
        [["Business/Finance", "3.08", "57%", "25%"],
         ["Education/Lecture", "2.63", "42%", "33%"],
         ["Entertainment", "2.51", "39%", "36%"],
         ["News/Politics", "2.48", "38%", "37%"],
         ["Tech/Science", "2.43", "36%", "39%"],
         ["Sports/Health", "2.38", "34%", "41%"],
         ["DIY/Home", "2.13", "30%", "52%"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {1: GREEN, 2: GREEN}, 6: {1: CORAL, 2: CORAL, 3: CORAL}})

    # Right — big number + insight
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    add_text(slide, "19%", rx, CT + Inches(0.3), rw, Inches(0.9),
             size=Pt(64), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments show\ndomain vocabulary\nconfusion",
             rx, CT + Inches(1.2), rw, Inches(1.0),
             size=Pt(16), color=WHITE, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "Model trained on TED talks (formal, educational)",
        ("Business content closest to training \u2192 best results",
         {"color": GREEN}),
        ("DIY content most visual, least verbal \u2192 worst results",
         {"color": CORAL}),
        "A topic label at decode time would help ~284 segments",
    ], rx, CT + Inches(2.5), rw, Inches(2.5), size=Pt(13))

    _finish(slide, 0,
        "Domain mismatch is a major factor. Business and Finance has IS 3.08 "
        "(57% captured) because it's closest to the TED talk training data. "
        "DIY/Home is worst at IS 2.13 (30% captured) — inherently visual content "
        "that doesn't translate to speech patterns. 19% of segments (~284) show "
        "domain vocabulary confusion where a topic label would help.\n\n"
        "WHY DOES A TOPIC LABEL HELP? The model was trained on general "
        "lip-reading data (TED talks) without topic context. When it encounters "
        "domain-specific vocabulary (medical, legal, technical), it hallucinates "
        "common words instead. A topic label (e.g., 'cooking', 'medicine') at "
        "decode time would constrain the vocabulary space, helping the LLM "
        "generate domain-appropriate words. The ~284 segments (19%) are those "
        "where the LLM judge identified domain vocabulary confusion as the "
        "primary error source.",
        [[lt, tbl], []], click_reveal=True)


def slide_decode_params(prs):
    """Decode parameter explanations — what the dials do."""
    slide = new_slide(prs)
    add_title(slide, "Decode Parameters: The Four Dials")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Four parameter blocks in two columns
    params = [
        ("Beam Size", "How many candidates to consider simultaneously",
         "Like checking multiple routes on a map",
         "5 \u2192 50 candidates", TEAL),
        ("Length Penalty", "Encourages longer or shorter outputs",
         "Positive = longer, negative = shorter, 0 = neutral",
         "\u22120.5 \u2192 2.0", CORAL),
        ("Temperature", "Controls randomness of word selection",
         "Low = conservative, high = creative",
         "0.3 \u2192 1.5", TEAL),
        ("Sampling", "Whether to pick the best or roll the dice",
         "Greedy (always best) vs nucleus (weighted random)",
         "greedy / nucleus p=0.9", CORAL),
    ]

    bw = Inches(5.5)
    bh = Inches(1.1)
    card_groups = []
    for i, (name, desc, analogy, range_str, color) in enumerate(params):
        col = i % 2
        row = i // 2
        x = MX + col * (bw + gap)
        y = CT + row * (bh + Inches(0.25))

        r = add_rect(slide, x, y, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, name, x + Inches(0.2), y + Inches(0.08),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(15), color=color, bold=True)
        t2 = add_text(slide, desc, x + Inches(0.2), y + Inches(0.4),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(12), color=WHITE)
        t3 = add_text(slide, f"{analogy}  \u2022  Range: {range_str}",
                 x + Inches(0.2), y + Inches(0.72),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(11), color=LGRAY, italic=True)
        card_groups.append([r, t1, t2, t3])

    # Bottom quote
    add_text(slide,
        '"Think of it like a stereo equalizer \u2014 you can adjust the dials, '
        'but the speakers determine the sound quality."',
        MX, Inches(5.8), CW, Inches(0.7),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "13 experiments tested combinations across these 4 dimensions.",
        MX, Inches(6.5), CW, Inches(0.3),
        size=Pt(13), color=TEAL, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four decode parameters. Beam size: how many candidates. Length penalty: "
        "bias toward longer or shorter. Temperature: randomness. Sampling: greedy "
        "vs stochastic. Like a stereo equalizer — you can adjust the dials but "
        "the speakers (visual encoder) determine the sound quality.",
        card_groups)


def slide_research_transition(prs):
    """Section divider: entering research findings portion."""
    slide = new_slide(prs)

    add_text(slide, "RESEARCH FINDINGS",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(48), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Understanding What Works, What Fails, and Why",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=CORAL)

    add_text(slide, "1,497 segments  \u2022  6 quality signals  \u2022  5 failure categories  "
             "\u2022  13 tuning experiments",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, None,
        "Section transition: we now present the research findings — our novel "
        "Intelligibility Score metric, root cause analysis, failure mode taxonomy, "
        "and decode tuning experiments.")


