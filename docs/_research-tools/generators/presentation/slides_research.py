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

def slide_is_motivation(prs):
    """Why LLM as a Judge Is Not Enough — 5 reasons for the IS framework."""
    slide = new_slide(prs)
    add_title(slide, "Why LLM as a Judge Is Not Enough")
    add_accent_line(slide)

    sub = add_text(slide,
        "Five reasons we built the Intelligibility Score (IS) framework",
        MX, CT, CW, Inches(0.35), size=Pt(15), color=MGRAY, italic=True)

    reasons = [
        ("\u2460 Deployment Constraint",
         "IS runs offline \u2014 no API, no GPU, no internet.\n"
         "Essential for air-gapped container deployment."),
        ("\u2461 Determinism",
         "IS produces identical scores every time.\n"
         "LLM judges vary ~13% on re-evaluation."),
        ("\u2462 Continuous Signal",
         "IS is 0.0\u20135.0 continuous from 6 signals.\n"
         "LLM judge outputs coarse Y/P/N categories."),
        ("\u2463 Known Biases",
         "12+ documented systematic biases in LLM judges.\n"
         "IS is a fixed formula with none."),
        ("\u2464 Decomposability",
         "IS breaks into 6 named signals \u2192 diagnose\n"
         "exactly what failed. LLM returns verdict only."),
    ]

    col_w = Inches(5.85)
    card_h = Inches(1.05)
    row_gap = Inches(0.12)
    col_gap = Inches(0.43)
    start_y = CT + Inches(0.5)

    card_groups = []
    for i, (title, body) in enumerate(reasons):
        row = i // 2
        col = i % 2
        if i == 4:
            x = MX + (CW - col_w) / 2
        else:
            x = MX + col * (col_w + col_gap)
        y = start_y + row * (card_h + row_gap)

        r = add_rect(slide, x, y, col_w, card_h, fill_color=NAVY2,
                     corner_radius=True)
        t1 = add_text(slide, title,
                      x + Inches(0.20), y + Inches(0.10),
                      col_w - Inches(0.40), Inches(0.30),
                      size=Pt(16), color=TEAL, bold=True)
        t2 = add_text(slide, body,
                      x + Inches(0.20), y + Inches(0.42),
                      col_w - Inches(0.40), Inches(0.55),
                      size=Pt(13), color=LGRAY)
        card_groups.append([r, t1, t2])

    takeaway = add_text(slide,
        "IS runs in production; LLM-as-a-Judge audits the IS framework. You need both.",
        MX, Inches(5.85), CW, Inches(0.40),
        size=Pt(15), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Why IS, not just LLM judge? Five reasons:\n"
        "1. Deployment: IS runs on bare Python, no GPU/API/internet.\n"
        "2. Determinism: IS gives exact same score every time.\n"
        "3. Continuous signal: IS is 0-5 continuous vs coarse Y/P/N.\n"
        "4. Known biases: 12+ documented LLM judge biases. IS has none.\n"
        "5. Decomposability: IS breaks into 6 components mapping to specific "
        "failure modes. Bottom line: IS is operational, LLM judge is validation.",
        [[sub]] + card_groups + [[takeaway]], click_reveal=True)


def slide_is_intro_a(prs):
    """IS Slide A: WER, WWER, and Length Ratio — the standard metrics."""
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Word Accuracy & Length")
    add_accent_line(slide)

    # Top banner
    banner = add_rect(slide, MX, CT, CW, Inches(0.55), fill_color=NAVY2,
                      border_color=TEAL, border_width=Pt(2), corner_radius=True)
    banner_txt = add_text(slide,
        "IS = composite of 6 signals (0\u20135).  IS \u2265 2.00 = \"Useful Output\" (Y+P).  "
        "These 3 signals measure raw word accuracy and output sanity.",
        MX + Inches(0.3), CT + Inches(0.08), CW - Inches(0.6), Inches(0.4),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    card_w = Inches(11.0)
    card_h = Inches(1.35)
    gap_y = Inches(0.10)
    start_y = CT + Inches(0.70)

    signals = [
        ("Inverse WER", "15%", CORAL,
         "Standard Word Error Rate (substitutions + insertions + deletions "
         "divided by reference length), then inverted: 1 \u2212 WER. "
         "A baseline word-accuracy signal that treats all words equally.",
         "Treats all words equally \u2014 every error costs the same."),
        ("WWER (Weighted WER)", "15%", CORAL,
         "Like WER, but content words (nouns, verbs, names) cost 2\u00d7 "
         "and function words ('the', 'a', 'is') cost only 0.5\u00d7. "
         "Losing a name hurts more than losing an article.",
         'Example: "Admiral McRae" wrong = 2\u00d7 penalty. '
         '"the" wrong = 0.5\u00d7 penalty.'),
        ("Length Ratio", "15%", LGRAY,
         "Output length divided by reference length. A safety check: "
         "catches hallucination (ratio >> 1, model generates too much) "
         "and truncation (ratio << 1, model cuts off early).",
         "Hallucinated segments average ratio 2.8\u00d7."),
    ]

    card_groups = []
    for i, (name, weight, color, how, example) in enumerate(signals):
        y = start_y + i * (card_h + gap_y)
        r = add_rect(slide, MX, y, card_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({weight})",
                 MX + Inches(0.2), y + Inches(0.08),
                 card_w - Inches(0.4), Inches(0.3),
                 size=Pt(15), color=color, bold=True)
        t2 = add_text(slide, how,
                 MX + Inches(0.2), y + Inches(0.42),
                 card_w - Inches(0.4), Inches(0.55),
                 size=Pt(12), color=WHITE)
        t3 = add_text(slide, f"\u25b8 {example}",
                 MX + Inches(0.2), y + Inches(1.0),
                 card_w - Inches(0.4), Inches(0.38),
                 size=Pt(10), color=LGRAY, italic=True)
        card_groups.append([r, t1, t2, t3])

    # Formula at bottom
    add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + WWER + NEA + Length)"
        "   \u2022   Fully deterministic   \u2022   $0 per evaluation",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS Slide A: Three standard metrics. Inverse WER (15%): baseline "
        "word accuracy, treats all words equally. WWER (15%): weighted WER "
        "where content words cost 2x and function words 0.5x — losing a "
        "name hurts more than losing 'the'. Length Ratio (15%): catches "
        "hallucination (ratio >> 1) and truncation (ratio << 1). These "
        "three signals form the word-accuracy dimension of IS.",
        [[banner, banner_txt]] + card_groups, click_reveal=True)


def slide_is_intro_b(prs):
    """IS Slide B: Semantic Similarity — meaning beyond words."""
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Semantic Similarity")
    add_accent_line(slide)

    # Weight callout — wide enough so text stays on one line
    weight_r = add_rect(slide, MX, CT, Inches(4.8), Inches(0.5), fill_color=NAVY2,
                        border_color=TEAL, border_width=Pt(2), corner_radius=True)
    weight_t = add_text(slide, "Weight: 25% \u2014 the single largest signal",
                 MX + Inches(0.2), CT + Inches(0.06),
                 Inches(4.4), Inches(0.38),
                 size=Pt(14), color=TEAL, bold=True)

    # Main explanation card
    card_y = CT + Inches(0.75)
    card_w = CW
    card_h = Inches(2.8)
    card_r = add_rect(slide, MX, card_y, card_w, card_h, fill_color=NAVY2,
                      border_color=TEAL, border_width=Pt(1.5), corner_radius=True)

    add_text(slide, "How It Works",
             MX + Inches(0.3), card_y + Inches(0.12),
             card_w - Inches(0.6), Inches(0.3),
             size=Pt(16), color=TEAL, bold=True)

    add_text(slide,
        "1. Both reference and hypothesis are converted to 384-dimensional "
        "sentence embeddings using SBERT (all-MiniLM-L6-v2).\n\n"
        "2. Cosine similarity is computed between the two embedding vectors.\n\n"
        "3. The result captures overall meaning \u2014 even if completely different "
        "words are used, a high score means the same idea was communicated.",
        MX + Inches(0.3), card_y + Inches(0.5),
        card_w - Inches(0.6), Inches(1.8),
        size=Pt(13), color=WHITE)

    # Example card
    ex_y = card_y + card_h + Inches(0.2)
    ex_h = Inches(1.2)
    ex_r = add_rect(slide, MX, ex_y, card_w, ex_h, fill_color=NAVY2,
                    border_color=LGRAY, border_width=Pt(1.5), corner_radius=True)

    add_text(slide, "Example",
             MX + Inches(0.3), ex_y + Inches(0.08),
             card_w - Inches(0.6), Inches(0.28),
             size=Pt(14), color=LGRAY, bold=True)
    add_text(slide,
        '"the CEO resigned" vs "the chief executive stepped down"\n'
        '\u2192 cosine similarity 0.91 \u2014 meaning preserved despite zero word overlap.\n'
        'WER would report 80% error; Semantic Similarity sees the truth.',
        MX + Inches(0.3), ex_y + Inches(0.4),
        card_w - Inches(0.6), Inches(0.7),
        size=Pt(12), color=LGRAY, italic=True)

    # Why it matters
    why_y = ex_y + ex_h + Inches(0.2)
    add_text(slide,
        "Why it matters: lip reading often produces synonyms and paraphrases. "
        "WER punishes these; Semantic Similarity rewards them.",
        MX, why_y, CW, Inches(0.4),
        size=Pt(13), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS Slide B: Semantic Similarity deep dive. This is the single "
        "largest signal at 25% weight. Uses SBERT (all-MiniLM-L6-v2) to "
        "convert sentences to 384-dim embeddings and measures cosine "
        "similarity. Captures meaning even when completely different words "
        "are used. Critical for lip reading because the model often produces "
        "synonyms and paraphrases that WER harshly penalizes but that "
        "preserve the intended message.",
        [[weight_r, weight_t], [card_r], [ex_r]], click_reveal=True)


def slide_is_intro_c(prs):
    """IS Slide C: Phonetic Similarity and Named Entity Accuracy."""
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Phonetic & Named Entities")
    add_accent_line(slide)

    card_w = CW
    card_h = Inches(2.4)
    gap_y = Inches(0.2)

    # Card 1: Phonetic Similarity
    c1_y = CT + Inches(0.1)
    c1_r = add_rect(slide, MX, c1_y, card_w, card_h, fill_color=NAVY2,
                    border_color=TEAL, border_width=Pt(1.5), corner_radius=True)
    add_text(slide, "Phonetic Similarity  (15%)",
             MX + Inches(0.2), c1_y + Inches(0.08),
             card_w - Inches(0.4), Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_text(slide,
        "Converts each word to IPA pronunciation using eng-to-ipa, "
        "then computes character-level similarity between the phonetic strings. "
        "Critical for lip reading: the model sees mouth shapes, not spellings \u2014 "
        "so phonetically correct output is a sign the visual encoder worked.",
        MX + Inches(0.2), c1_y + Inches(0.45),
        card_w - Inches(0.4), Inches(0.9),
        size=Pt(12), color=WHITE)
    add_text(slide,
        '\u25b8 Example: "Admiral McRae" vs "animal migration"\n'
        '  IPA: /\u00e6dm\u026ar\u0259l m\u0259kre\u026a/ vs '
        '/\u00e6n\u026am\u0259l ma\u026a\u0261re\u026a\u0283\u0259n/ '
        '\u2192 0.68 (sounds similar despite looking completely different)',
        MX + Inches(0.2), c1_y + Inches(1.45),
        card_w - Inches(0.4), Inches(0.8),
        size=Pt(11), color=LGRAY, italic=True)

    # Card 2: Named Entity Accuracy
    c2_y = c1_y + card_h + gap_y
    c2_r = add_rect(slide, MX, c2_y, card_w, card_h, fill_color=NAVY2,
                    border_color=CORAL, border_width=Pt(1.5), corner_radius=True)
    add_text(slide, "Named Entity Accuracy (NEA)  (15%)",
             MX + Inches(0.2), c2_y + Inches(0.08),
             card_w - Inches(0.4), Inches(0.3),
             size=Pt(15), color=CORAL, bold=True)
    add_text(slide,
        "Extracts named entities (people, numbers, places) from both "
        "reference and hypothesis using spaCy NER, then computes F1 "
        "(precision \u00d7 recall). Binary per entity: either correct or "
        "destroyed, no partial credit.",
        MX + Inches(0.2), c2_y + Inches(0.45),
        card_w - Inches(0.4), Inches(0.9),
        size=Pt(12), color=WHITE)
    add_text(slide,
        "\u25b8 Mean F1 = 38.9% \u2014 entities missed in 85% of segments.\n"
        "  Names are the hardest thing for lip reading: "
        "\"McRae\" has no visual cue that distinguishes it from any other word.",
        MX + Inches(0.2), c2_y + Inches(1.45),
        card_w - Inches(0.4), Inches(0.8),
        size=Pt(11), color=LGRAY, italic=True)

    # Bottom note
    add_text(slide,
        "Together these two signals capture what WER misses: "
        "phonetic plausibility and entity preservation.",
        MX, c2_y + card_h + Inches(0.15), CW, Inches(0.4),
        size=Pt(13), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS Slide C: Phonetic Similarity and Named Entity Accuracy. "
        "PHONETIC (15%): converts words to IPA pronunciation and compares "
        "character-by-character. Critical because the model sees mouth "
        "shapes, not spellings. 'Admiral McRae' and 'animal migration' "
        "look nothing alike in text but share phonetic structure (0.68). "
        "NEA (15%): Named Entity F1 using spaCy NER extraction. Binary "
        "per entity, no partial credit. Mean F1 is only 38.9% — entities "
        "are missed in 85% of segments. Names are the hardest for lip "
        "reading since they have no distinguishing visual cues.",
        [[c1_r], [c2_r]], click_reveal=True)


def slide_is_intro(prs):
    """Split into 3 slides per batch 8 user request."""
    slide_is_intro_a(prs)
    slide_is_intro_b(prs)
    slide_is_intro_c(prs)


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
        "weight because meaning preservation is the ultimate goal. The other "
        "5 signals each get 15%. PCA shows all 5 content signals load equally "
        "on PC1 (0.43-0.47) \u2014 one general quality factor (68.4% of variance). "
        "Length Ratio is independent (PC2, 19.5%). Semantic's higher weight is "
        "justified because it captures paraphrasing that word metrics miss.",
        anim_groups)


def slide_is_weight_rationale(prs):
    """PCA story: 6 signals collapse into 2 dimensions, validating the IS design."""
    slide = new_slide(prs)
    add_title(slide, "Do 6 Signals Actually Measure 6 Things?")
    add_accent_line(slide)

    add_text(slide,
        "PCA on 1,497 segments reveals where the variance actually lives.",
        MX, CT, CW, Inches(0.3),
        size=Pt(14), color=LGRAY, italic=True)

    # Three PCA dimension cards — full width, stacked
    card_w = CW
    card_h = Inches(1.3)
    py = CT + Inches(0.5)

    dims = [
        ("PC1: Signal Quality", "68.4%", TEAL,
         "Semantic + Phonetic + WER + WWER + Named Entity Accuracy",
         "All 5 content signals load equally (0.43\u20130.47). Semantic is NOT "
         "independent \u2014 it measures the same underlying quality as word accuracy."),
        ("PC2: Output Length", "19.5%", GREEN,
         "Length Ratio dominates (loading 0.91) \u2014 independent of content quality",
         "Catches hallucination (too long) and truncation (too short)."),
        ("PC3: Entity Swing", "5.1%", GOLD,
         "NEA F1 loads here (below Kaiser threshold, eigenvalue 0.31)",
         "Minor refinement axis \u2014 names and numbers that diverge "
         "from the main quality signal."),
    ]

    dim_shapes = []
    for name, pct, color, signals, desc in dims:
        r = add_rect(slide, MX, py, card_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, name, MX + Inches(0.3), py + Inches(0.1),
                 Inches(5.0), Inches(0.35), size=Pt(18), color=color, bold=True)
        add_text(slide, pct, MX + card_w - Inches(1.2), py + Inches(0.1),
                 Inches(1.0), Inches(0.35), size=Pt(18), color=color,
                 bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, signals, MX + Inches(0.3), py + Inches(0.45),
                 card_w - Inches(0.6), Inches(0.3), size=Pt(13), color=WHITE)
        add_text(slide, desc, MX + Inches(0.3), py + Inches(0.75),
                 card_w - Inches(0.6), Inches(0.45), size=Pt(12), color=LGRAY)
        dim_shapes.append(r)
        py += Inches(1.5)

    # Bottom takeaway
    val_t = add_text(slide,
        "Together: 93% of variance in 3 components. "
        "Kaiser retains 2 (87.9%); PC3 adds nuance.",
        MX, Inches(6.35), CW, Inches(0.35),
        size=Pt(13), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "PCA story. Kaiser criterion PCA on 6 standardized IS signals. "
        "PC1 (68.4%): all 5 content signals load equally at 0.43-0.47 \u2014 one general "
        "quality factor. Semantic is NOT independent; it loads on PC1 with word-accuracy. "
        "PC2 (19.5%): Length Ratio dominates at 0.91, independent of content. "
        "PC3 (5.1%): Entity Swing, NEA F1 refinement, below Kaiser threshold "
        "(eigenvalue 0.31 < 1.0). Together 93%. "
        "Weight sensitivity: current vs equal weights correlate at r=0.999 \u2014 "
        "only 5.4% of segments change tier. The formula is robust to perturbation.",
        [dim_shapes, [val_t]], click_reveal=True)


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

        # Header bar — narrower centered strip
        bar_w = Inches(3.6)
        bar_x = x + (col_w - bar_w) / 2
        shapes.append(add_rect(slide, bar_x, CT + Inches(0.1),
                 bar_w, Inches(0.32), fill_color=color,
                 corner_radius=True))
        shapes.append(add_text(slide, f"{label} \u2014 IS = {is_val}",
                 bar_x, CT + Inches(0.1),
                 bar_w, Inches(0.32),
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
        ("Length Ratio", "0.25", "\u00d7 0.15", "= 0.150", CORAL),
    ]
    r2 = _draw_calc_card(slide, MX + col_w + gap,
        "Bad Segment", "0.9", CORAL,
        "carry strap",
        "holocaust denier explanation of the final act",
        bad_lines, "Sum \u00d7 5 = 0.89 \u2192 IS 0.9 (Failed)")

    _finish(slide, 0,
        "Two IS calculation examples. Left: good segment (IS 4.2) with high "
        "scores across all signals. Right: hallucination (IS 0.8) where only "
        "length ratio and phonetic similarity are non-trivial — the output is a completely different topic. "
        "The formula is IS = (sum of weighted scores) x 5, mapping to 0-5 scale.",
        [r1, r2], click_reveal=True)


def slide_is_radar(prs):
    """Radar chart — model comparison: expected IS profiles for different LLMs."""
    slide = new_slide(prs)
    add_title(slide, "Model Comparison: IS Profiles")
    add_accent_line(slide)
    sub = add_text(slide,
        "How different LLM backbones would reshape the IS radar \u2014 "
        "measured profiles from LRS3 benchmark and YouTube evaluation.",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # Radar image (reuse existing if available, framing is now about models)
    img_top = CT + Inches(0.65)
    img_h = SL_H - img_top - Inches(1.6)
    img_w = Inches(8.5)
    img_l = (SL_W - img_w) / 2
    radar_key = "P6b_radar_dual" if IMG.get("P6b_radar_dual", Path("x")).exists() \
                else "P6_is_radar"
    img = add_image(slide, radar_key, img_l, img_top,
                    width=img_w, height=img_h)

    # No legend text — chart is self-explanatory

    _finish(slide, 0,
        "Dual radar chart: LRS3 benchmark (measured, n=170) vs YouTube real-world "
        "(measured, n=1,497).\n\n"
        "LRS3 values (all measured): Semantic 0.779, Phonetic 0.794, "
        "1-WER 0.689, 1-WWER 0.662, NEA 0.683, LenRatio 0.971.\n"
        "YouTube values (all measured): Semantic 0.58, Phonetic 0.52, "
        "1-WER 0.36, 1-WWER 0.38, NEA 0.39, LenRatio 0.72.\n\n"
        "Key insight: the radar shape reveals where each condition is "
        "strong and weak. Length Ratio stays high even for YouTube "
        "(model generates correct amount of text). The collapsed axes "
        "(WER, WWER, NEA) are where the domain gap hits hardest.",
        [[img]])


def slide_is_wer_scatter(prs):
    """IS vs WER scatter showing 'the gap' — NIV thresholds."""
    slide = new_slide(prs)
    add_title(slide, "The Gap: Where WER Lies Most")
    add_accent_line(slide)

    # Left column — two gap numbers + bullets (narrower to give plot more room)
    left_w = Inches(4.2)
    num_s = add_text(slide, "42 + 437", MX, CT, left_w, Inches(1.1),
                     size=Pt(56), color=GREEN, bold=True)
    lbl_s = add_text(slide, "segments WER wrongly discards (NIV thresholds)",
                     MX, CT + Inches(1.1), left_w, Inches(0.5),
                     size=Pt(15), color=LGRAY)
    bul = add_bullets(slide, [
        ("42 clearly conveyed (IS \u2265 3.80) but WER > 34%", {"bold": True, "color": GREEN}),
        ("437 useful meaning (IS \u2265 2.00) but WER > 40%", {"bold": True, "color": GOLD}),
        "NIV: calibrated against Opus-as-a-Judge (blind eval)",
        "IS \u2265 3.80 matches judge Y rate exactly (\u03ba=0.690)",
        ("IS beats WER by +0.06 \u03ba at every operating point", {"color": TEAL}),
    ], MX, CT + Inches(1.65), left_w, Inches(3.0))

    # Right — larger scatter plot
    img = add_image(slide, "P7_is_wer_scatter",
                    MX + left_w + Inches(0.2), CT - Inches(0.2),
                    width=CW - left_w - Inches(0.2))

    # Bottom note about IS-WER correlation
    add_text(slide,
        "IS WER correlates with IS (r\u2248\u22120.7) but not perfectly \u2014 "
        "it misses phonetic and semantic preservation, making it insufficient alone.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Scatter plot of WER vs IS for all 1,497 segments with NIV thresholds. "
        "Green region: 42 segments clearly conveyed (IS >= 3.80) but WER > 34%. "
        "Amber region: 437 segments with useful meaning (IS >= 2.00) but WER > 40%. "
        "NIV thresholds calibrated against Opus-as-a-Judge: IS >= 3.80 for Y "
        "(\u03ba=0.690, captures 23.1% vs judge 23.0%), IS >= 2.00 for Y+P "
        "(\u03ba=0.818, captures 61.6% vs judge 64.9%). IS beats WER at both "
        "operating points (+0.061 for Y, +0.041 for Y+P).\n\n"
        "IS WER correlates with IS (r\u2248\u22120.7) but not perfectly \u2014 "
        "it misses phonetic and semantic preservation, making it insufficient "
        "as a standalone quality measure.",
        [[num_s, lbl_s, bul], [img]], click_reveal=True)


def slide_semantic_domain_gap(prs):
    """Why LRS3 errors preserve meaning but YouTube errors don't — WER-matched."""
    slide = new_slide(prs)
    add_title(slide, "Same WER, Different Meaning")
    add_accent_line(slide)

    sub = add_text(slide,
        "At matched WER (20-40%), LRS3 errors preserve meaning — YouTube errors destroy it.",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # ── Left column: WER-matched delta table ──
    col_w = Inches(6.0)
    gap = Inches(0.5)

    tbl_title = add_text(slide,
        "Signal Gap at Same WER (20-40%)",
        MX, CT + Inches(0.5), col_w, Inches(0.35),
        size=Pt(15), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "LRS3", "YouTube", "\u0394"],
        [["Semantic Sim", "0.838", "0.695", "+0.143"],
         ["Phonetic Sim", "0.826", "0.803", "+0.024"],
         ["1 \u2212 WER", "0.715", "0.701", "+0.014"],
         ["NEA F1", "0.727", "0.669", "+0.058"],
         ["Length Ratio", "0.953", "0.962", "\u22120.009"]],
        MX, CT + Inches(0.95), col_w, text_size=Pt(12),
        row_colors={0: {3: GREEN}, 1: {3: LGRAY}, 2: {3: LGRAY}, 3: {3: GOLD}})

    # Semantic/Phonetic ratio callout
    ratio_box = add_rect(slide, MX, CT + Inches(3.2), col_w, Inches(1.0),
                         fill=NAVY2, border_color=TEAL, border_w=Pt(1.5))
    add_text(slide, "Semantic / Phonetic Ratio",
             MX + Inches(0.3), CT + Inches(3.25), col_w - Inches(0.6), Inches(0.3),
             size=Pt(12), color=TEAL, bold=True)
    add_text(slide,
        "LRS3:  1.01  (meaning tracks sound)\n"
        "YouTube:  0.87  (meaning degrades 13% faster than sound)",
        MX + Inches(0.3), CT + Inches(3.55), col_w - Inches(0.6), Inches(0.55),
        size=Pt(12), color=WHITE)

    # ── Right column: real examples ──
    rx = MX + col_w + gap
    rw = CW - col_w - gap

    add_text(slide, "LRS3 Error (WER 29%, Sem 0.93)",
             rx, CT + Inches(0.5), rw, Inches(0.3),
             size=Pt(13), color=GREEN, bold=True)
    add_text(slide,
        'REF: "spending 14-16 hours a day"\n'
        'HYP: "spending like 40-60 hours a day"\n'
        '\u2192 Numbers wrong, meaning intact',
        rx, CT + Inches(0.85), rw, Inches(1.1),
        size=Pt(11), color=WHITE)

    add_text(slide, "YouTube Error (WER 33%, Sem 0.16)",
             rx, CT + Inches(2.1), rw, Inches(0.3),
             size=Pt(13), color=CORAL, bold=True)
    add_text(slide,
        'REF: "talking with admiral mcrae"\n'
        'HYP: "talking with animal migratory"\n'
        '\u2192 Same sounds, completely different topic',
        rx, CT + Inches(2.45), rw, Inches(1.1),
        size=Pt(11), color=WHITE)

    # ── Bottom: 3 reasons why ──
    why_top = CT + Inches(4.4)
    add_text(slide, "Why the Domain Gap Is Semantic",
             MX, why_top, CW, Inches(0.35),
             size=Pt(15), color=TEAL, bold=True)
    bul = add_bullets(slide, [
        ("Visual encoder trained on LRS3 \u2192 better features \u2192 "
         "wrong words stay in semantic neighbourhood", {"color": WHITE}),
        ("TED vocabulary is general \u2014 substitutions are semantically close. "
         "YouTube has jargon, names, slang \u2192 random substitutions",
         {"color": WHITE}),
        ("LLM prior anchors on structured TED grammar. "
         "YouTube's informal speech gives less context to anchor on",
         {"color": WHITE}),
    ], MX, why_top + Inches(0.35), CW, Inches(1.5), size=Pt(12))

    _finish(slide, 0,
        "WER-matched comparison (20-40% band): LRS3 n=58, YouTube n=290. "
        "At the same word error rate, LRS3 segments have +0.143 higher semantic "
        "similarity but only +0.024 higher phonetic similarity. The errors "
        "sound the same but mean different things.\n\n"
        "The Semantic/Phonetic ratio quantifies this: on LRS3 it stays ~1.0 "
        "(meaning tracks sound) across all WER bands. On YouTube it drops to "
        "0.72 at WER 50-60% — meaning collapses faster than sound.\n\n"
        "Three root causes:\n"
        "1. Visual encoder familiarity: AV-HuBERT pretrained on 433h LRS3, "
        "produces better cluster sequences for TED-like content. Even "
        "misassigned clusters land on semantically related words.\n"
        "2. Vocabulary density: TED uses common, general vocabulary. "
        "YouTube has domain-specific terms (brand names, jargon, proper nouns) "
        "where substitution errors are semantically distant.\n"
        "3. LLM prior anchoring: TED's formal grammar gives the LLM strong "
        "structural context. YouTube's informal, fragmented speech provides "
        "less scaffolding, leading to more random completions.\n\n"
        "Data source: docs/evaluation/signal_distribution_analysis.md, Section 10. "
        "LRS3 V4 (LRS3-trained k-means, 184 segments) vs YouTube (1,497 segments).",
        [[sub, tbl_title, tbl, ratio_box], [bul]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 7 — THE INTELLIGIBILITY SCORE
# ═══════════════════════════════════════════════════════════════════════

def slide_07(prs):
    slide = new_slide(prs)
    add_title(slide, "Intelligibility Score: 61.6% Useful Output")
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
        "IS ≥ 2.00 = Useful Output (Y+P): 61.6% — 2.4× what WER suggests (25.5%)\n"
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
        "Key insight: 61.6% of segments deliver useful output (IS >= 2.00, NIV Y+P) — "
        "2.4x what WER suggests (25.5%). WER dramatically overstates "
        "failure. Methodology: LLM-distilled evaluation — the "
        "rubric, selected signals and weights, defined tier boundaries. "
        "Validated: IS vs Opus judge κ=0.818 at Y+P (IS≥2.00), "
        "cross-config r=0.925.",
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
        "574 segments below useful threshold (IS < 2.00) \u2014 how often does each mode occur?",
        MX, CT, CW, Inches(0.35), size=Pt(14), color=LGRAY, italic=True)

    modes = [
        ("Wrong Topic", 44.4, 255, GOLD),
        ("Hallucination", 18.8, 108, CORAL),
        ("Signal Loss", 13.9, 80, MGRAY),
        ("Right Topic, Wrong Details", 13.8, 79, TEAL),
        ("Accumulated Errors", 9.1, 52, LGRAY),
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
        w = max(Inches(0.2), int(max_bar_w * pct / 45.0))
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
        "574 below-threshold segments (IS < 2.00) classified into 5 failure categories. "
        "Wrong Topic dominates at 44.4% (255 segments), combining topic drift and "
        "phonetic confusion. Hallucination is second at 18.8% (108). Signal Loss "
        "and Right Topic Wrong Details are roughly tied at ~14% each. Accumulated "
        "Errors drops to just 9.1% — most mild-error segments now fall above the "
        "IS 2.00 threshold. This taxonomy maps directly to our roadmap.",
        bar_groups)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_1a(prs):
    """Failure mode taxonomy Part 1: categories 1-3 by impact (Details, Wrong Topic, Hallucination)."""
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy (1/2): Highest Impact First")
    add_accent_line(slide)

    add_text(slide,
        "574 below-threshold segments (IS < 2.0) classified into 5 mutually exclusive "
        "categories \u2014 each segment gets exactly one label, checked 1\u21925.",
        MX, CT, CW, Inches(0.28), size=Pt(13), color=LGRAY, italic=True)

    add_text(slide,
        "Grounded in ASR error taxonomy (Fosler-Lussier 2004) and "
        "LLM hallucination analysis (ACL 2025)",
        MX, CT + Inches(0.28), CW, Inches(0.22),
        size=Pt(10), color=MGRAY, italic=True)

    modes_1 = [
        ("1. Wrong Topic", "44.4%", "255 segments", ORANGE,
         "Mouth shapes decoded to wrong domain",
         "Semantic < 0.2 (phonetic-matched or not)",
         "Ref: \u201cweight loss and diet\u201d \u2192 Hyp: \u201cwanted to be a princess\u201d"),
        ("2. Hallucination", "18.8%", "108 segments", YELLOW,
         "Model invented fake text",
         "WER \u2265 100% (output longer than reference)",
         "Ref: \u201ccarry strap\u201d \u2192 Hyp: \u201cholocaust denier explanation of the final act\u201d"),
        ("3. Right Topic, Wrong Details", "13.8%", "79 segments", RED,
         "Roughly right but names/content words lost",
         "NEA F1 < 20% OR key content words substituted (Semantic \u2265 0.2)",
         "Ref: \u201c13th amendment is going\u201d \u2192 Hyp: \u201c13th may mean something to him\u201d"),
    ]

    card_h = Inches(1.35)
    gap = Inches(0.15)
    y0 = CT + Inches(0.65)
    name_w = Inches(4.8)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes_1):
        y = y0 + i * (card_h + gap)

        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.08),
                 name_w - Inches(0.3), Inches(0.35),
                 size=Pt(17), color=color, bold=True)
        t2 = add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.52),
                 name_w - Inches(0.3), Inches(0.45),
                 size=Pt(13), color=LGRAY)
        t3 = add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.08),
                 rule_w - Inches(0.15), Inches(0.45),
                 size=Pt(14), color=WHITE)
        t4 = add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.60),
                 rule_w - Inches(0.15), Inches(0.55),
                 size=Pt(12), color=LGRAY, italic=True)
        anim_groups.append([r, t1, t2, t3, t4])

    add_text(slide,
        "Ordered by impact \u2014 highest to lowest (continued on next slide)",
        MX, Inches(6.65), CW, Inches(0.35),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Failure taxonomy Part 1, ordered by impact. Wrong Topic (44.4%): the "
        "LARGEST category — mouth shapes decoded to completely wrong domain. "
        "Hallucination (18.8%): model invents fake text, deceptive but identifiable "
        "by length. Right Topic Wrong Details (13.8%): clients lose trust when "
        "output looks right but details are wrong.",
        anim_groups, click_reveal=True)


def slide_failure_deep_1b(prs):
    """Failure mode taxonomy Part 2: categories 4-5 (Accumulated, Signal Loss)."""
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy (2/2): Accumulated \u2192 Signal Loss")
    add_accent_line(slide)

    modes_2 = [
        ("4. Signal Loss", "13.9%", "80 segments", LGRAY,
         "Nothing came out",
         "Empty output OR length ratio < 0.3",
         "Ref: \u201cthe thirteenth amendment\u201d \u2192 Hyp: \u201c\u201d"),
        ("5. Accumulated Errors", "9.1%", "52 segments", YELLOW,
         "Many small errors compound",
         "IS < 2.0 and doesn\u2019t match categories 1\u20133",
         "Many words slightly wrong throughout, meaning erodes"),
    ]

    card_h = Inches(1.8)
    gap = Inches(0.25)
    y0 = CT + Inches(0.15)
    name_w = Inches(3.8)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes_2):
        y = y0 + i * (card_h + gap)

        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.1),
                 name_w - Inches(0.3), Inches(0.4),
                 size=Pt(18), color=color, bold=True)
        t2 = add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.55),
                 name_w - Inches(0.3), Inches(0.55),
                 size=Pt(14), color=LGRAY)
        t3 = add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.1),
                 rule_w - Inches(0.15), Inches(0.55),
                 size=Pt(14), color=WHITE)
        t4 = add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.75),
                 rule_w - Inches(0.15), Inches(0.65),
                 size=Pt(13), color=LGRAY, italic=True)
        anim_groups.append([r, t1, t2, t3, t4])

    # Summary bar
    sum_y = y0 + 2 * (card_h + gap) + Inches(0.1)
    sr = add_rect(slide, MX, sum_y, CW, Inches(1.0), fill_color=NAVY2,
                  border_color=GOLD, border_width=Pt(2), corner_radius=True)
    add_text(slide, "Key Insight: Categories 4 & 5 are lower impact but still 23.0% of failures",
             MX + Inches(0.3), sum_y + Inches(0.1), CW - Inches(0.6), Inches(0.35),
             size=Pt(16), color=GOLD, bold=True)
    add_text(slide,
        "Accumulated errors respond to N-best aggregation (ROVER/MBR). "
        "Signal loss is detectable and filterable \u2014 lowest priority to fix.",
        MX + Inches(0.3), sum_y + Inches(0.5), CW - Inches(0.6), Inches(0.45),
        size=Pt(13), color=WHITE)
    anim_groups.append([sr])

    _finish(slide, 0,
        "Failure taxonomy Part 2. Signal Loss (13.9%): empty or near-empty "
        "output, 80 segments — detectable and filterable. Accumulated Errors "
        "(9.1%): death by a thousand cuts, 52 segments — responds to N-best "
        "aggregation. Together 23.0% of failures.",
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
            "pct": "18.8%",
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
            "pct": "44.4%",
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
            "pct": "13.8%",
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

    headers = ["Category", "Impact", "Fix"]
    rows = [
        ["Wrong Topic (44.4%)", "Very High — largest category", "LLM swap + data"],
        ["Hallucination (18.8%)", "High — deceptive but identifiable", "Confidence scoring"],
        ["Signal Loss (13.9%)", "Medium — detectable, filterable", "Quality filtering"],
        ["Right Topic, Wrong Details (13.8%)", "Medium — clients lose trust", "Domain fine-tuning"],
        ["Accumulated Errors (9.1%)", "Lower — death by 1000 cuts", "N-best aggregation"],
    ]

    # Color scheme: category and impact columns share severity color
    row_colors = {
        0: {0: ORANGE, 1: ORANGE},      # Wrong Topic — highest severity
        1: {0: RED, 1: RED},            # Hallucination — high severity
        2: {0: LGRAY, 1: LGRAY},        # Signal Loss — medium severity
        3: {0: YELLOW, 1: YELLOW},      # Right Topic Wrong Details — medium severity
        4: {0: YELLOW, 1: YELLOW},      # Accumulated Errors — lower severity
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.45), CW,
                    row_height=Inches(0.55),
                    col_widths=[Inches(4.0), Inches(3.8), Inches(4.33)],
                    text_size=Pt(14),
                    row_colors=row_colors)

    # Conclusion callout
    callout_r = add_rect(slide, MX, Inches(5.2), CW, Inches(0.55), fill_color=NAVY2,
             border_color=TEAL, border_width=Pt(1.5), corner_radius=True)

    callout_t = add_text(slide,
        "Each roadmap phase targets a different failure category.",
        MX + Inches(0.2), Inches(5.25), CW - Inches(0.4), Inches(0.45),
        size=Pt(16), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Impact and fixes table for the 5-category taxonomy. Three columns: "
        "category, impact level, and fix. Severity is conveyed by row colors on "
        "both category and impact columns: LGRAY (low, Signal Loss), YELLOW "
        "(moderate, Hallucination), ORANGE (high, Wrong Topic), RED (critical, "
        "Right Topic Wrong Details), YELLOW (medium, Accumulated Errors). "
        "Right Topic Wrong Details is the most dangerous because clients cannot "
        "trust the output. Wrong Topic is the LARGEST at 44.4% and the most "
        "amenable to improvement through LLM upgrade. 54.3% of failures trace "
        "to the LLM backbone being too weak.",
        [[tbl], [callout_r, callout_t]], click_reveal=True)


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
    """The three numbers: 25.5% -> 61.6% -> 64.9%."""
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
    g1.append(add_text(slide, "25.5%", card_x + Inches(0.3), c1_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=CORAL, bold=True))
    g1.append(add_text(slide, "By WER (\u226434%)\n381 of 1,497 videos appear useful\nWER says only 1 in 4 works",
                        card_x + Inches(3.0), c1_y + Inches(0.15),
                        card_w - Inches(3.3), card_h - Inches(0.3),
                        size=Pt(15), color=LGRAY))
    # No strikethrough — WER is still valid, just pessimistic

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
    g2.append(add_text(slide, "61.6%", card_x + Inches(0.3), c2_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=TEAL, bold=True))
    g2.append(add_text(slide,
        "By IS (\u22652.00): 922 of 1,497 videos\ndeliver useful meaning\nIS reveals 3 in 5 carry meaning",
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
    g3.append(add_text(slide, "64.9%", card_x + Inches(0.3), c3_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=GREEN, bold=True))
    g3.append(add_text(slide,
        "By LLM Judge (Y+P): 971 of 1,497\nconfirmed useful\nExpert judgment confirms 2 in 3 work",
        card_x + Inches(3.0), c3_y + Inches(0.15),
        card_w - Inches(3.3), card_h - Inches(0.3),
        size=Pt(15), color=WHITE))

    _finish(slide, 0,
        "Three numbers answering the same question: 'How many videos are useful?' "
        "WER (≤34%): 25.5% (381/1,497) — most pessimistic, uses NIV-calibrated threshold. "
        "IS (≥2.00): 61.6% (922/1,497) — captures useful meaning. "
        "LLM Judge (Y+P): 64.9% (971/1,497) — expert confirms. "
        "Progressive revelation: WER dramatically understates quality.",
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
            "Under 10 words: only 53% useful vs 68% for 20+ words",
            ("3. Hallucination (20.5%)", {"bold": True, "color": TEAL}),
            "LLM prior overwhelms weak visual signal \u2014 fluent but fabricated",
        ],
        "By the Numbers", [
            ("Business/Finance: IS 3.08, 78% useful", {"color": GREEN}),
            ("DIY/Home: IS 2.13, 41% useful \u2014 37pp gap", {"color": CORAL}),
            "Short (5\u201310 words): 74% WER, 53% useful",
            "Long (20+ words): 55% WER, 68% useful \u2014 15pp gap",
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
        ("Useful: 59% NEA F1 vs Non-useful: 6%",
         {"bold": True, "color": CORAL}),
        "53pp gap \u2014 largest differentiator of any signal",
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
        "Most useful segments live here.\n\n"
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
        "it's the single most discriminating signal between useful and non-useful.",
        None)

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
        ["Mean IS", "2.53", "2.60", "+0.07"],
        ["Useful (IS\u22652)", "61.6%", "62.8%", "+1.2pp"],
        ["Empty outputs", "4.7%", "0%", "\u221270"],
        ["Hallucinations", "20.5%", "23.2%", "+41"],
        ["Mean WWER", "60.5%", "59.8%", "\u22120.7pp"],
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
        "Validated: IS vs Opus judge \u03ba = 0.818 (Y+P), \u03ba = 0.690 (Y), "
        "r = 0.85 Pearson correlation with LLM judge gold standard.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Two approaches: Option A calls an LLM for every pair — expensive, "
        "non-deterministic, slow. Option B (ours): the entire "
        "evaluation framework was designed at development time, then distilled into "
        "deterministic formulas. Zero cost per run, 100% reproducible. "
        "Validated at κ=0.818 (Y+P), r=0.85.",
        [[r1], [r2]], click_reveal=True)


def slide_is_dimensions(prs):
    """Two quality dimensions from PCA analysis."""
    slide = new_slide(prs)
    add_title(slide, "Two Dimensions of Quality (PCA)")
    add_accent_line(slide)

    add_text(slide, "PCA retains 2 principal components (Kaiser criterion: eigenvalue > 1):",
             MX, CT, CW, Inches(0.4), size=Pt(15), color=LGRAY)

    # Two cards
    dims = [
        ("PC1: Signal Quality", "68.4%", "of total variance",
         "All 5 content signals load equally\n(0.43\u20130.47 each)",
         "One general quality factor\ndriven by visual encoder", TEAL),
        ("PC2: Output Length", "19.5%", "of total variance",
         "Length Ratio dominates\n(loading 0.91)",
         "Independent of content quality\nCatches hallucination & truncation", LGRAY),
    ]

    cw_card = Inches(5.4)
    ch_card = Inches(4.0)
    gap = Inches(0.5)
    total = 2 * cw_card + gap
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
        "PCA retains 2 principal components. PC1 (68.4%): all 5 content signals "
        "load equally (0.43-0.47) \u2014 one general quality factor driven by the "
        "visual encoder. Semantic is NOT independent; it loads on PC1 just like "
        "word-accuracy signals. PC2 (19.5%): Length Ratio dominates (0.91), "
        "truly independent of content quality. Together: 87.9% of variance. "
        "PC3 (entity swing, 5.1%) is below Kaiser threshold.",
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
        ["Topic", "IS", "Useful", "Judge N%"],
        [["Business/Finance", "3.08", "78%", "24%"],
         ["Education/Lecture", "2.84", "72%", "23%"],
         ["News/Politics", "2.81", "76%", "26%"],
         ["Sports/Health", "2.76", "70%", "30%"],
         ["Tech/Science", "2.70", "65%", "28%"],
         ["Entertainment", "2.23", "58%", "39%"],
         ["DIY/Home", "2.13", "41%", "52%"]],
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
        "~284 segments need topic-aware fine-tuning (not just labels)",
    ], rx, CT + Inches(2.5), rw, Inches(2.5), size=Pt(13))

    _finish(slide, 0,
        "Domain mismatch is a major factor. Business and Finance has IS 3.08 "
        "(78% useful) because it's closest to the TED talk training data. "
        "DIY/Home is worst at IS 2.13 (41% useful) — inherently visual content "
        "that doesn't translate to speech patterns. 19% of segments (~284) show "
        "domain vocabulary confusion.\n\n"
        "TOPIC LABEL EXPERIMENT (March 2026): We tested naive topic label "
        "injection at decode time on all 284 segments. Result: -0.9pp WER "
        "(worse). 24% of segments echoed the label literally instead of "
        "transcribing speech. The model treats extra instruction tokens as "
        "input to complete, not as context. Control group (100 good segments) "
        "showed 0% echoing but still -0.6pp degradation. Topic-aware "
        "FINE-TUNING is needed — the model must learn to use topic tokens "
        "as context during training.",
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
    add_text(slide, 'Understanding What does \u201cWorking\u201d mean, What Works, and Why',
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=CORAL)

    _finish(slide, 0,
        "Section transition: we now present the research findings — our novel "
        "Intelligibility Score metric, root cause analysis, failure mode taxonomy, "
        "and decode tuning experiments.")


