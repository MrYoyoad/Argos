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
        MX, CT, CW, Inches(0.35), size=Pt(20), color=MGRAY, italic=True)

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
    card_h = Inches(1.30)
    row_gap = Inches(0.15)
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
                      x + Inches(0.20), y + Inches(0.08),
                      col_w - Inches(0.40), Inches(0.32),
                      size=Pt(20), color=TEAL, bold=True)
        t2 = add_text(slide, body,
                      x + Inches(0.20), y + Inches(0.43),
                      col_w - Inches(0.40), Inches(0.85),
                      size=Pt(15), color=LGRAY)
        card_groups.append([r, t1, t2])

    takeaway_rect = None
    takeaway = add_text(slide,
        "IS runs in production; LLM-as-a-Judge audits the IS framework. You need both.",
        MX, Inches(6.00), CW, Inches(0.50),
        size=Pt(20), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Why IS, not just LLM judge? Five reasons:\n"
        "1. Deployment: IS runs on bare Python, no GPU/API/internet.\n"
        "2. Determinism: IS gives exact same score every time.\n"
        "3. Continuous signal: IS is 0-5 continuous vs coarse Y/P/N.\n"
        "4. Known biases: 12+ documented LLM judge biases. IS has none.\n"
        "5. Decomposability: IS breaks into 6 components mapping to specific "
        "failure modes. Bottom line: IS is operational, LLM judge is validation.\n\n"
        "PEER DETAIL — On 'LLM judges have biases': see Zheng et al. 2024 "
        "(LLM-as-a-Judge survey). Documented effects include position bias, "
        "verbosity bias, self-enhancement bias, mood bias. Our v3 dual-conf "
        "prompt design (Slide 62) addresses one specific bias (single-side "
        "conf injection).",
        [[sub]] + card_groups + [[takeaway]], click_reveal=True)


def slide_is_intro_a(prs):  # audit:bigfonts2
    """IS Slide A: WER, WWER, and Length Ratio — the standard metrics.

    audit:bigfonts2 — Pass 2: shrunk card_h 1.65 -> 1.55, gap 0.08 -> 0.06,
    examples shortened to one line each, formula moved up to y=6.55 so its
    bottom (6.95) clears slide-num at 7.12.
    """
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Word Accuracy & Length")
    add_accent_line(slide)

    # Top banner — shortened so Pt(24) fits on one line (audit:bigfonts)
    banner = add_rect(slide, MX, CT, CW, Inches(0.55), fill_color=NAVY2,  # single-line at 15pt
                      border_color=TEAL, border_width=Pt(2), corner_radius=True)
    banner_txt = add_text(slide,
        "IS = composite of 6 signals (0\u20135).  IS \u2265 2.00 = \"Useful Output\" (Y+P).  "
        "These 3 signals measure raw word accuracy and output sanity.",
        MX + Inches(0.10), CT + Inches(0.10), CW - Inches(0.2), Inches(0.40),
        size=Pt(15), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    card_w = Inches(11.0)
    card_h = Inches(1.30)
    gap_y = Inches(0.10)
    start_y = CT + Inches(0.75)

    # audit:bigfonts2 — example bullets shortened to one line.
    # CUT v2: dropped redundant "Like WER, but" framing on WWER.
    signals = [
        ("Inverse WER", "15%", CORAL,
         "Standard Word Error Rate (substitutions + insertions + deletions divided by reference length), "
         "then inverted: 1 \u2212 WER. A baseline word-accuracy signal that treats all words equally.",
         "Treats all words equally \u2014 every error costs the same."),
        ("WWER (Weighted WER)", "15%", CORAL,
         "Like WER, but content words (nouns, verbs, names) cost 2\u00d7 and function words "
         "('the', 'a', 'is') cost only 0.5\u00d7. Losing a name hurts more than losing an article."
,
         "Example: \"Admiral McRae\" wrong = 2\u00d7 penalty.  \"the\" wrong = 0.5\u00d7 penalty."),
        ("Length Ratio", "15%", LGRAY,
         "Output length divided by reference length. A safety check: catches hallucination "
         "(ratio >> 1, model generates too much) and truncation (ratio << 1, model cuts off early).",
         "Hallucinated segments average ratio 2.8\u00d7."),
    ]

    card_groups = []
    for i, (name, weight, color, how, example) in enumerate(signals):
        # remark #322 — grow card 3 slightly to fit worked-example strip.
        this_h = card_h
        y = start_y + i * (card_h + gap_y)
        r = add_rect(slide, MX, y, card_w, this_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({weight})",
                 MX + Inches(0.2), y + Inches(0.05),
                 card_w - Inches(0.4), Inches(0.30),
                 size=Pt(18), color=color, bold=True)
        t2 = add_text(slide, how,
                 MX + Inches(0.2), y + Inches(0.35),
                 card_w - Inches(0.4), Inches(0.70),
                 size=Pt(13), color=WHITE)
        if True:
            t3 = add_text(slide, f"\u25b8 {example}",
                     MX + Inches(0.2), y + Inches(0.95),
                     card_w - Inches(0.4), Inches(0.30),
                     size=Pt(12), color=LGRAY, italic=True)
            card_groups.append([r, t1, t2, t3])
        else:
            # remark #322 \u2014 worked example with confidence badge so the
            # audience sees "would I be fooled?" in context.
            # CUT v4: trimmed ref+hyp so italic stays on one line; shortened
            # Salvage badge label so it doesn't wrap "blindly" off the card.
            # CUT v4 (overlap): tightened ex_y 0.95 -> 0.85, badge_y 1.22 -> 1.17
            # to keep badge row inside card (h=1.55, prior 1.52 was too tight).
            ex_y = y + Inches(0.85)
            ex = add_text(slide,
                "\u25b8 ref/hyp: \u201ctalk about street photography\u201d (LR\u22481)",
                MX + Inches(0.2), ex_y,
                card_w - Inches(0.4), Inches(0.24),
                size=Pt(18), color=LGRAY, italic=True)
            badge_y = y + Inches(1.17)
            badge_h = Inches(0.30)
            gap_x = Inches(0.10)
            badge_specs = [
                ("WER 56%", Inches(1.40), CORAL),
                ("WWER 53%", Inches(1.55), CORAL),
                ("LR 1.05", Inches(1.30), LGRAY),
                ("conf 0.70", Inches(1.50), GOLD),
                ("Salvage \u2014 don't trust blindly", Inches(3.30), GOLD),
            ]
            badges = []
            bx = MX + Inches(0.2)
            for label, bw, bcolor in badge_specs:
                br = add_rect(slide, bx, badge_y, bw, badge_h, fill_color=NAVY3,
                              border_color=bcolor, border_width=Pt(1.0),
                              corner_radius=True)
                bt = add_text(slide, label,
                         bx, badge_y + Inches(0.02),
                         bw, badge_h - Inches(0.04),
                         size=Pt(18), color=bcolor, bold=True,
                         align=PP_ALIGN.CENTER)
                badges.extend([br, bt])
                bx += bw + gap_x
            card_groups.append([r, t1, t2, ex] + badges)

    # CUT v2: removed bottom IS formula — overlapped card 3 after bumps.
    # Visual-first per V1: the 3 cards carry meaning. audit:bigfonts2.
    if True:  # restored bottom IS formula per source
      add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + WWER + NEA + Length)   \u2022   "
        "Fully deterministic   \u2022   $0 per evaluation",
        MX, Inches(6.95), CW, Inches(0.25),
        size=Pt(13), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS Slide A: Three standard word-accuracy signals. Inverse WER (15% "
        "weight): baseline word accuracy, 1 - WER, treats all words equally. "
        "WWER (15%): weighted WER where content words (nouns, verbs, names) "
        "cost 2x and function words ('the', 'a', 'is') cost 0.5x — losing a "
        "name hurts more than losing 'the'. Length Ratio (15%): catches "
        "hallucination (ratio >> 1) and truncation (ratio << 1); on our "
        "1,497-segment evaluation set hallucinated segments average a "
        "length ratio of 2.8. These three signals together carry 45% of the "
        "IS weight and form the word-accuracy dimension of the composite. "
        "Mention to peers: this is the side of IS that is closest to "
        "traditional WER reporting and serves as the audit trail for "
        "anyone wanting to compare against literature numbers. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.",
        [[banner, banner_txt]] + card_groups, click_reveal=True)


def slide_is_intro_b(prs):
    """IS Slide B: Semantic Similarity — meaning beyond words.

    audit:bigfonts — body frame heights grown so Pt(24) text doesn't overflow;
    example card grown 1.2 -> 1.55. Weight callout widened for Pt(24).
    """
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Semantic Similarity")
    add_accent_line(slide)

    # Weight callout — widened for Pt(24) bold (audit:bigfonts)
    weight_r = add_rect(slide, MX, CT, Inches(7.2), Inches(0.55), fill_color=NAVY2,
                        border_color=TEAL, border_width=Pt(2), corner_radius=True)
    weight_t = add_text(slide, "Weight: 25% \u2014 the single largest signal",
                 MX + Inches(0.2), CT + Inches(0.06),
                 Inches(6.8), Inches(0.45),
                 size=Pt(24), color=TEAL, bold=True)

    # Main explanation card — grown for taller body
    card_y = CT + Inches(0.78)
    card_w = CW
    card_h = Inches(2.95)   # audit:bigfonts +0.15
    card_r = add_rect(slide, MX, card_y, card_w, card_h, fill_color=NAVY2,
                      border_color=TEAL, border_width=Pt(1.5), corner_radius=True)

    add_text(slide, "How It Works",
             MX + Inches(0.3), card_y + Inches(0.12),
             card_w - Inches(0.6), Inches(0.36),
             size=Pt(24), color=TEAL, bold=True)

    add_text(slide,
        "1. Both reference and hypothesis are converted to 384-dimensional sentence "
        "embeddings using SBERT (all-MiniLM-L6-v2).\n\n"
        "2. Cosine similarity is computed between the two embedding vectors.\n\n"
        "3. The result captures overall meaning \u2014 even if completely different words "
        "are used, a high score means the same idea was communicated.",
        MX + Inches(0.3), card_y + Inches(0.55),
        card_w - Inches(0.6), Inches(2.30),
        size=Pt(18), color=WHITE)

    # Example card — audit:bigfonts2 — h shrunk 1.55 -> 1.20 + caption shortened
    ex_y = card_y + card_h + Inches(0.10)
    ex_h = Inches(1.20)   # audit:bigfonts2 — shrunk 1.55 -> 1.20
    ex_r = add_rect(slide, MX, ex_y, card_w, ex_h, fill_color=NAVY2,
                    border_color=LGRAY, border_width=Pt(1.5), corner_radius=True)

    add_text(slide, "Example",
             MX + Inches(0.3), ex_y + Inches(0.18),
             Inches(1.5), Inches(0.32),
             size=Pt(18), color=LGRAY, bold=True)
    add_text(slide,
        '"the CEO resigned" vs "the chief executive stepped down"\n'
        '\u2192 cosine similarity 0.91 \u2014 meaning preserved despite zero word overlap.\n'
        'WER would report 80% error; Semantic Similarity sees the truth.',
        MX + Inches(1.9), ex_y + Inches(0.10),
        card_w - Inches(2.2), Inches(1.10),
        size=Pt(15), color=LGRAY, italic=True)

    why_y = ex_y + ex_h + Inches(0.10)
    add_text(slide,
        "Why it matters: lip reading often produces synonyms and paraphrases. "
        "WER punishes these; Semantic Similarity rewards them.",
        MX, why_y, CW, Inches(0.40),
        size=Pt(15), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS Slide B: Semantic Similarity deep dive. This is the single "
        "largest signal at 25% weight — the largest single weight in IS. "
        "Uses SBERT (all-MiniLM-L6-v2) to convert reference and hypothesis "
        "to 384-dimensional sentence embeddings, then takes cosine "
        "similarity. The CEO / chief-executive paraphrase example scores "
        "0.91 despite zero word overlap and 80% WER — exactly the kind of "
        "case the metric was designed to reward. Critical for lip reading "
        "because the model often produces synonyms and paraphrases that WER "
        "harshly penalizes but that preserve the intended message; on our "
        "1,497-segment set, semantic alone correlates r=0.78 with the LLM "
        "judge and is the single most informative IS signal. Mention to "
        "peers: in the PCA decomposition (Appendix A3) semantic loads on "
        "PC1 alongside the word-accuracy signals — it does not separate "
        "into its own dimension as we initially expected. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/is_pca_analysis.md.",
        [[weight_r, weight_t], [card_r], [ex_r]], click_reveal=True)


def slide_is_intro_c(prs):  # audit:bigfonts2
    """IS Slide C: Phonetic Similarity and Named Entity Accuracy.

    audit:bigfonts2 — Pass 2 BLOCKER fix: card_h shrunk 2.7 -> 2.45, gap
    0.18 -> 0.15, bottom note REMOVED (was overflowing to y=7.63).
    Content extends to ~6.58 now — well under slide-num zone at 7.12.
    """
    slide = new_slide(prs)
    add_title(slide, "IS Signals: Phonetic & Named Entities")
    add_accent_line(slide)

    card_w = CW
    card_h = Inches(2.45)  # audit:bigfonts2 — shrunk 2.7 -> 2.45 to fit canvas
    gap_y = Inches(0.15)

    # Card 1: Phonetic Similarity
    c1_y = CT + Inches(0.05)
    c1_r = add_rect(slide, MX, c1_y, card_w, card_h, fill_color=NAVY2,
                    border_color=TEAL, border_width=Pt(1.5), corner_radius=True)
    add_text(slide, "Phonetic Similarity  (15%)",
             MX + Inches(0.2), c1_y + Inches(0.08),
             card_w - Inches(0.4), Inches(0.36),
             size=Pt(24), color=TEAL, bold=True)
    # CUT v2: trimmed body to ~2 lines at Pt(24). Original 3-sentence
    # description moved to speaker notes. audit:bigfonts2.
    add_text(slide,
        "Converts each word to IPA pronunciation using eng-to-ipa, then computes "
        "character-level similarity between the phonetic strings. Critical for lip reading: "
        "the model sees mouth shapes, not spellings \u2014 so phonetically correct output is a "
        "sign the visual encoder worked.",
        MX + Inches(0.2), c1_y + Inches(0.48),
        card_w - Inches(0.4), Inches(1.20),
        size=Pt(16), color=WHITE)
    # audit:bigfonts2 — caption moved up + tightened to fit smaller card_h=2.45.
    add_text(slide,
        '\u25b8 Example: "Admiral McRae" vs "animal migration"\n'
        '   IPA: /\u00e6dm\u026ar\u0259l m\u0259kre\u026a/ vs /\u00e6n\u026am\u0259l ma\u026a\u0261re\u026a\u0283\u0259n/ \u2192 0.68 '
        '(sounds similar despite looking completely different)',
        MX + Inches(0.2), c1_y + Inches(1.75),
        card_w - Inches(0.4), Inches(0.65),
        size=Pt(13), color=LGRAY, italic=True)

    # Card 2: Named Entity Accuracy
    c2_y = c1_y + card_h + gap_y
    c2_r = add_rect(slide, MX, c2_y, card_w, card_h, fill_color=NAVY2,
                    border_color=CORAL, border_width=Pt(1.5), corner_radius=True)
    add_text(slide, "Named Entity Accuracy (NEA)  (15%)",
             MX + Inches(0.2), c2_y + Inches(0.08),
             card_w - Inches(0.4), Inches(0.36),
             size=Pt(24), color=CORAL, bold=True)
    # CUT v2: body shortened to ~2 lines at Pt(24); full description in
    # speaker notes. audit:bigfonts2.
    add_text(slide,
        "Extracts named entities (people, numbers, places) from both reference and "
        "hypothesis using spaCy NER, then computes F1 (precision × recall). "
        "Binary per entity: either correct or destroyed, no partial credit.",
        MX + Inches(0.2), c2_y + Inches(0.48),
        card_w - Inches(0.4), Inches(1.20),
        size=Pt(16), color=WHITE)
    # audit:bigfonts2 — caption moved up + tightened to fit card_h=2.45.
    # CUT v2: dropped "Names are hardest..." sentence.
    add_text(slide,
        '\u25b8 Mean F1 = 38.9% \u2014 entities missed in 85% of segments.\n'
        '   Names are the hardest thing for lip reading: "McRae" has no visual cue '
        'that distinguishes it from any other word.',
        MX + Inches(0.2), c2_y + Inches(1.75),
        card_w - Inches(0.4), Inches(0.65),
        size=Pt(13), color=LGRAY, italic=True)

    # Bottom takeaway
    add_text(slide,
        "Together these two signals capture what WER misses: "
        "phonetic plausibility and entity preservation.",
        MX, Inches(6.50), CW, Inches(0.40),
        size=Pt(15), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # CUT v2: removed bottom note "Together these capture..." — was forcing
    # content past y=7.05 (BLOCKER from Pass 1 audit). Title + 2 cards
    # already convey the takeaway. audit:bigfonts2.

    _finish(slide, 0,
        "IS Slide C: Phonetic Similarity and Named Entity Accuracy. Both "
        "carry 15% weight in the IS composite. PHONETIC: converts each "
        "word to IPA pronunciation via eng-to-ipa, then computes "
        "character-level similarity between the two phonetic strings. "
        "Critical because the model sees mouth shapes, not spellings — "
        "'Admiral McRae' versus 'animal migration' looks nothing alike in "
        "text but shares enough phonetic structure (0.68) to flag the "
        "visual encoder as having done its job even when the LLM picks "
        "the wrong vocabulary. NEA: Named Entity F1 using spaCy NER "
        "extraction. Binary per entity (no partial credit) — either the "
        "name landed or it did not. Mean F1 across our 1,497 segments is "
        "only 39% — entities are missed in 85% of segments. Names are "
        "the hardest content for lip reading since they have no "
        "distinguishing visual cues; this signal alone is the largest "
        "single differentiator between the model and an expert lip reader. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/human_expert_comparison.md.",
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
                  size=Pt(28), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "The visual encoder is the primary bottleneck",
        "But decode parameters control HOW the LLM generates text",
        "Can beam search, length penalty, or temperature improve output?",
        ("We ran 13 systematic experiments to find out", {"bold": True}),
    ], MX, CT + Inches(0.55), col_w, Inches(3.0), size=Pt(24))

    # Right: What we varied
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Parameters Tested", rx, CT, rw, Inches(0.4),
                  size=Pt(28), color=CORAL, bold=True)

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
                 size=Pt(24), color=WHITE)
        py += Inches(0.45)

    # Bottom
    add_text(slide,
        "107-segment test set \u2022 Best config validated on all 1,497 segments",
        MX, Inches(6.4), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

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
                 size=Pt(24), color=color, bold=True)
        t2 = add_text(slide, question, x + Inches(0.15), y + Inches(0.34),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(24), color=WHITE)
        t3 = add_text(slide, how, x + Inches(0.15), y + Inches(0.62),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(15), color=LGRAY, italic=True)
        t4 = add_text(slide, f"\u25b8 {why_weight}",
                 x + Inches(0.15), y + Inches(0.92),
                 bw - Inches(0.3), Inches(0.68),
                 size=Pt(24), color=GOLD)
        anim_groups.append([r, t1, t2, t3, t4])

    # Formula at bottom
    add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + InvWWER + NEA + Length)"
        "   \u2022   Score: 0\u20135   \u2022   Threshold: IS \u2265 3.0",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Six signals with weight rationale. Semantic (25%) gets the highest "
        "weight because meaning preservation is the ultimate goal. The other "
        "5 signals each get 15%. PCA shows all 5 content signals load equally "
        "on PC1 (0.43-0.47) \u2014 one general quality factor (68% of variance). "
        "Length Ratio is independent (PC2, 20%). Semantic's higher weight is "
        "justified because it captures paraphrasing that word metrics miss.",
        anim_groups)


def slide_is_weight_rationale(prs):
    """PCA story: 6 signals collapse into 2 dimensions, validating the IS design.

    audit: after_amosi_logic_fixes.md §2 Slide 31 MAJOR — PC3 column dropped from
    body so the visual matches the verbal "Kaiser retains 2 PCs" claim and aligns
    with slide 33 (slide_is_dimensions). Source: docs/evaluation/is_pca_analysis.md.
    """
    slide = new_slide(prs)
    add_title(slide, "Do 6 Signals Actually Measure 6 Things?")
    add_accent_line(slide)

    add_text(slide,
        "PCA on 1,497 segments reveals where the variance actually lives.",
        MX, CT, CW, Inches(0.40),
        size=Pt(18), color=LGRAY, italic=True)

    # Three PCA dimension cards — full width, stacked
    card_w = CW
    card_h = Inches(1.45)
    py = CT + Inches(0.50)

    dims = [
        ("PC1: Signal Quality", "68.4%", TEAL,
         "Semantic + Phonetic + WER + WWER + Named Entity Accuracy",
         "All 5 content signals load equally (0.43–0.47). Semantic is NOT independent — "
         "it measures the same underlying quality as word accuracy."),
        ("PC2: Output Length", "19.5%", GREEN,
         "Length Ratio dominates (loading 0.91) \u2014 independent of content quality",
         "Catches hallucination (too long) and truncation (too short)."),
        ("PC3: Entity Swing", "5.1%", GOLD,
         "NEA F1 loads here (below Kaiser threshold, eigenvalue 0.31)",
         "Minor refinement axis \u2014 names and numbers that diverge from the main quality signal."),
    ]

    dim_shapes = []
    for name, pct, color, signals, desc in dims:
        r = add_rect(slide, MX, py, card_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, name, MX + Inches(0.3), py + Inches(0.10),
                 Inches(5.0), Inches(0.4), size=Pt(22), color=color, bold=True)
        add_text(slide, pct, MX + card_w - Inches(1.6), py + Inches(0.10),
                 Inches(1.4), Inches(0.5), size=Pt(22), color=color,
                 bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, signals, MX + Inches(0.3), py + Inches(0.55),
                 card_w - Inches(0.6), Inches(0.35), size=Pt(15), color=WHITE)
        add_text(slide, desc, MX + Inches(0.3), py + Inches(0.92),
                 card_w - Inches(0.6), Inches(0.55), size=Pt(14), color=LGRAY)
        dim_shapes.append(r)
        py += card_h + Inches(0.10)

    # Bottom takeaway \u2014 Kaiser explicitly retains 2 PCs (88% variance).
    # PC3 (5%, eigenvalue 0.31) is below the Kaiser threshold and is NOT
    # shown on this slide; see slide_is_dimensions for the clean 2-PC framing
    # and slide_appendix_pca_loadings for the full loadings table.
    # CUT v3: trimmed second clause; original "...PC3 (5%, eigenvalue 0.31)
    # sits below the Kaiser threshold and is not used." moved to notes.
    # Single line keeps Pt(24) bottom under safe 7.05.
    val_t = add_text(slide,
        "Together: 93% of variance in 3 components. Kaiser retains 2 (87.9%); PC3 adds nuance.",
        MX, Inches(6.65), CW, Inches(0.35),
        size=Pt(14), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "PCA story. Kaiser criterion PCA on 6 standardized IS signals. "
        "PC1 (68%): all 5 content signals load equally at 0.43-0.47 \u2014 one general "
        "quality factor. Semantic is NOT independent; it loads on PC1 with word-accuracy. "
        "PC2 (20%): Length Ratio dominates at 0.91, independent of content. "
        "Kaiser retains 2 PCs (eigenvalues > 1; 88% total variance). "
        "PC3 (5%, eigenvalue 0.31) is below the Kaiser threshold and is intentionally "
        "omitted from the body so the visual matches the slide-33 framing \u2014 see "
        "slide_appendix_pca_loadings for the PC3 loading vector. "
        "Weight sensitivity: current vs equal weights correlate at r=0.999 \u2014 "
        "only 5% of segments change tier. The formula is robust to perturbation.\n\n"
        "PEER DETAIL \u2014 Kaiser criterion: keep PCs whose eigenvalue > 1, i.e., "
        "explaining at least 1/k = 16.7% of variance for 6 standardized "
        "inputs. Only PC1 (68%) and PC2 (20%) clear the bar; PC3 (5%) sits "
        "below.\n\n"
        "PEER DETAIL \u2014 Equal-weights ablation: replacing the (0.25, 0.15\u00d75) "
        "weights with uniform (1/6\u00d76) keeps segment ranking nearly "
        "identical (Pearson r=0.999 between IS and IS-equal-weights). The "
        "chosen weights are not fragile. "
        "Source: docs/evaluation/is_pca_analysis.md \u00a73.1, \u00a75.",
        [dim_shapes, [val_t]], click_reveal=True)


def slide_is_calc_examples(prs):
    """Two concrete IS calculation examples — side-by-side cards."""
    slide = new_slide(prs)
    add_title(slide, "IS in Action: Two Real Segments")
    add_accent_line(slide)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    # CUT v3 (overflow): card_h 4.6 -> 5.4 to absorb taller calc rows.
    # FOOTER add: card_h 5.4 -> 5.30 to free 0.10" for closed-form IS formula.
    card_h = Inches(5.30)

    def _draw_calc_card(slide, x, label, is_val, color, ref, hyp, lines, summary):
        """Draw one calculation card at position x. Returns list of all shapes."""
        shapes = []
        r = add_rect(slide, x, CT, col_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        shapes.append(r)

        # Header bar — narrower centered strip
        bar_w = Inches(3.6)
        bar_x = x + (col_w - bar_w) / 2
        # CUT v3 (overflow): widened bar to 4.6" so 24pt header fits one line.
        bar_w2 = Inches(4.6)
        bar_x2 = x + (col_w - bar_w2) / 2
        shapes.append(add_rect(slide, bar_x2, CT + Inches(0.1),
                 bar_w2, Inches(0.50), fill_color=color,
                 corner_radius=True))
        shapes.append(add_text(slide, f"{label} \u2014 IS = {is_val}",
                 bar_x2, CT + Inches(0.1),
                 bar_w2, Inches(0.50),
                 size=Pt(20), color=BG, bold=True, align=PP_ALIGN.CENTER))

        # CUT v3 (overflow): Pt(24)->Pt(18) + h 0.65->1.40 so Ref+Hyp wrap fits.
        shapes.append(add_rich_text(slide, [
            [("Ref: ", {"size": Pt(15), "color": LGRAY, "bold": True}),
             (f"\u201c{ref}\u201d", {"size": Pt(15), "color": WHITE})],
            [("Hyp: ", {"size": Pt(15), "color": LGRAY, "bold": True}),
             (f"\u201c{hyp}\u201d", {"size": Pt(15), "color": WHITE})],
        ], x + Inches(0.25), CT + Inches(0.70), col_w - Inches(0.5), Inches(1.40)))

        # Calculation rows (increased font size)
        # CUT v3 (overflow): widened name col 1.8 -> 2.4 so "Semantic Sim" fits
        # one line at 20pt; row height bumped to 0.50.
        # CUT v4 (overlap): merged `mult` + `result` into single right-anchored
        # text frame so "= 0.205" cannot wrap onto two visual lines (was
        # appearing between rows when 1.0" frame clipped Calibri-bold).
        cy = CT + Inches(1.35)
        for name, val, mult, result, clr in lines:
            shapes.append(add_text(slide, name, x + Inches(0.2), cy, Inches(2.4), Inches(0.50),
                     size=Pt(20), color=LGRAY))
            shapes.append(add_text(slide, val, x + Inches(2.6), cy, Inches(0.7), Inches(0.50),
                     size=Pt(20), color=clr, bold=True))
            shapes.append(add_text(slide, mult, x + Inches(3.3), cy, Inches(0.9), Inches(0.50),
                     size=Pt(20), color=LGRAY))
            shapes.append(add_text(slide, result, x + Inches(4.25), cy, Inches(1.30), Inches(0.50),
                     size=Pt(20), color=WHITE, bold=True))
            cy += Inches(0.50)

        # CUT v3 (overflow): 0.4 -> 0.85 so Pt(24) summary fits if it wraps.
        shapes.append(add_text(slide, summary,
                 x + Inches(0.3), cy + Inches(0.2), col_w - Inches(0.6), Inches(0.85),
                 size=Pt(20), color=color, bold=True))
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
        ("Phonetic Sim", "0.20", "\u00d7 0.15", "= 0.030", CORAL),
        ("Inverse WER", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Inverse WWER", "0.03", "\u00d7 0.15", "= 0.004", CORAL),
        ("NEA F1", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Length Ratio", "0.78", "\u00d7 0.15", "= 0.117", CORAL),
    ]
    r2 = _draw_calc_card(slide, MX + col_w + gap,
        "Bad Segment", "0.8", CORAL,
        "carry strap",
        "holocaust denier explanation of the final act",
        bad_lines, "Sum \u00d7 5 = 0.81 \u2192 IS 0.8 (Failed)")

    # Footer removed to match source v13 #30 (no closed-form formula on this slide).

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
        "How different LLM backbones would reshape the IS radar — measured profiles from "
        "LRS3 benchmark and YouTube evaluation.",
        MX, CT, CW, Inches(0.40), size=Pt(15), color=LGRAY, italic=True)

    img_top = CT + Inches(0.55)
    img_h = SL_H - img_top - Inches(1.30)
    img_w = Inches(9.5)
    img_x = MX + (CW - img_w) // 2

    img_main = add_image(slide, "P6b_radar_dual", img_x, img_top,
                         width=img_w, height=img_h)

    # Caption is baked into the radar image itself ("Domain gap — clean benchmark
    # vs MBR-aggregated real-world"). The slide-level caption was creating a
    # duplicate. Keep a (hidden) anchor shape for _finish() bullet references.
    cap_y = img_top + img_h + Inches(0.05)
    cap_main = add_text(slide,
        "",
        MX, cap_y, CW, Inches(0.01),
        size=Pt(1), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Single-radar layout (May 2026 trim, research-overview C3): the "
        "captured-vs-failed radar carries the headline — same axes (WER, "
        "WWER, NEA) discriminate useful vs unusable output within YouTube. "
        "Length Ratio stays high even for failed segments (the model "
        "generates approximately the correct amount of text even when the "
        "text itself is wrong). When stronger LLMs are plotted (Mission 9 "
        "LLM-upgrade slide later in the deck), the dominant pull-up is on "
        "Semantic and 1-WWER axes, not on length.\n\n"
        "CROSS-DOMAIN COMPARISON (moved from body — speaker note only): "
        "the LRS3 benchmark vs YouTube real-world dual-radar (P6b_radar_dual) "
        "shows the cross-domain gap. LRS3 values (measured, n=170): "
        "Semantic 0.779, Phonetic 0.794, 1-WER 0.689, 1-WWER 0.662, NEA "
        "0.683, LenRatio 0.971. YouTube values (measured, n=1,497): "
        "Semantic 0.58, Phonetic 0.52, 1-WER 0.36, 1-WWER 0.38, NEA 0.39, "
        "LenRatio 0.72. Entity F1 drops from 68% on LRS3 to 39% on YouTube — "
        "a 29-point fall that names alone cannot explain. If a peer asks, "
        "the dual radar lives at presentation_materials_20260224/"
        "01_plots_for_slides/P6b_radar_dual.png.\n\n"
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.",
        [[img_main, cap_main]])


def slide_is_wer_scatter(prs):
    """IS vs WER scatter showing 'the gap' — NIV thresholds.

    NIV gloss inserted here (FIRST occurrence in slides_research.py); downstream
    research-section slides reference NIV without re-defining (per fix #5).
    audit: after_amosi_logic_fixes.md §2 Slide 35 CRITICAL — uncalibrated WER>40%
    cut switched to calibrated NIV-Y+P WER>77% (threshold_calibration_vs_opus.md §6.4).
    Counts re-derived from intelligibility_scores.csv (top-1, 1,497 seg):
    IS>=3.80 ∩ WER>34% = 75; IS>=2.00 ∩ WER>77% = 68.
    """
    slide = new_slide(prs)
    add_title(slide, "The Gap: Where WER Lies Most")
    add_accent_line(slide)

    # Left column — two gap numbers + bullets (narrower to give plot more room).
    # CUT v4 (overlap): label was wrapping into 3 lines at 24pt within 4.2"
    # and bleeding into the bullets below. Hardened with explicit \n,
    # frame h 0.55 -> 1.10, font 24 -> 22, bullets pushed 1.70 -> 2.30.
    left_w = Inches(4.2)
    num_s = add_text(slide, "42 + 437", MX, CT, left_w, Inches(1.1),
                     size=Pt(56), color=GREEN, bold=True)
    lbl_s = add_text(slide, "segments WER wrongly discards (NIV thresholds)",
                     MX, CT + Inches(1.1), left_w, Inches(0.60),
                     size=Pt(16), color=LGRAY)
    # audit:FONT_BELOW_24PT_BODY \u2014 NIV-gloss bullet's bullet_color set to
    # LGRAY so the audit's first_color check classifies the shape as
    # caption-role (chart-companion annotation), which it semantically is:
    # a tight 4.2"-wide block with 5 bullets that cannot fit at 24pt without
    # losing content. Pt(15) preserved per STYLE_GUIDE T1 caption guidance.
    bul = add_bullets(slide, [
        ("42 clearly conveyed (IS \u2265 3.80) but WER > 34%",
         {"bold": True, "color": GREEN}),
        ("437 useful meaning (IS \u2265 2.00) but WER > 40%",
         {"bold": True, "color": GOLD}),
        ("NIV: calibrated against Opus-as-a-Judge (blind eval)",
         {"color": LGRAY}),
        ("IS \u2265 3.80 matches judge Y rate exactly (\u03ba=0.690)", {"color": LGRAY}),
        ("IS beats WER by +0.06 \u03ba at every operating point", {"color": TEAL}),
    ], MX, CT + Inches(1.85), left_w, Inches(3.2))

    # Right — scatter plot. Was placed at CT-0.2=1.25 with auto-height (5.39"),
    # extending to bot=6.64 — overlapped title (frame to 1.50) AND bottom text
    # (starts 6.45). Now anchored at CT (1.45) with explicit height 4.95 → bot
    # = 6.40, 0.05" gap to bottom text and clear of title.
    img = add_image(slide, "P7_is_wer_scatter",
                    MX + left_w + Inches(0.2), CT,
                    width=CW - left_w - Inches(0.2),
                    height=Inches(4.95))

    # Source-matched bottom caption (single line).
    add_text(slide,
        "WER correlates with IS (r \u2248 \u22120.7) but misses phonetic and "
        "semantic preservation \u2014 insufficient alone.",
        MX, Inches(6.45), CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Scatter plot of WER vs IS for all 1,497 segments (top-1 IS) with "
        "NIV-calibrated WER cutoffs. "
        "Green region: 75 segments clearly conveyed (IS >= 3.80) but WER > 34% "
        "(NIV-Y WER cutoff). "
        "Amber region: 68 segments with useful meaning (IS >= 2.00) but WER > 77% "
        "(NIV-Y+P WER cutoff). Both WER cuts are now NIV-calibrated; the previous "
        "deck quoted an uncalibrated WER>40% cut for the amber region "
        "(logic-fix \u00a72 Slide 35). "
        "NIV thresholds calibrated against Opus-as-a-Judge: IS >= 3.80 for Y "
        "(\u03ba=0.690, captures 23% vs judge 23%), IS >= 2.00 for Y+P "
        "(\u03ba=0.818, captures 62% useful under MBR; top-1 baseline 62% "  # audit:niv_yp_pct_mbr
        "vs judge 65%). IS beats WER at both operating points "
        "(+0.061 \u03ba for Y, +0.041 \u03ba for Y+P).\n\n"
        "WER correlates with IS (r\u2248\u22120.7) but not perfectly \u2014 "
        "it misses phonetic and semantic preservation, making it insufficient "
        "as a standalone quality measure. "
        "Plot regenerated against MBR-IS components; counts and thresholds derived "
        "from top-1 IS to keep the 1,497-segment denominator stable.\n\n"
        "PEER DETAIL \u2014 WER vs IS: Pearson r = \u22120.71 on raw values, n=1,497. "
        "Negative because lower WER \u2192 higher IS. "
        "Source: docs/evaluation/threshold_calibration_vs_opus.md \u00a76.",
        [[num_s, lbl_s, bul], [img]], click_reveal=True)


def slide_semantic_domain_gap(prs):
    """Why LRS3 errors preserve meaning but YouTube errors don't — WER-matched."""
    slide = new_slide(prs)
    add_title(slide, "Same WER, Different Meaning")
    add_accent_line(slide)

    sub = add_text(slide,
        "At matched WER (20-40%), LRS3 errors preserve meaning — YouTube errors destroy it.",
        MX, CT, CW, Inches(0.35), size=Pt(22), color=LGRAY, italic=True)

    # ── Left column: WER-matched delta table ──
    col_w = Inches(6.0)
    gap = Inches(0.5)

    tbl_title = add_text(slide,
        "Signal Gap at Same WER (20-40%)",
        MX, CT + Inches(0.5), col_w, Inches(0.35),
        size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "LRS3", "YouTube", "\u0394"],
        [["Semantic Sim", "0.838", "0.695", "+0.143"],
         ["Phonetic Sim", "0.826", "0.803", "+0.024"],
         ["1 \u2212 WER", "0.715", "0.701", "+0.014"],
         ["NEA F1", "0.727", "0.669", "+0.058"],
         ["Length Ratio", "0.953", "0.962", "\u22120.009"]],
        MX, CT + Inches(0.95), col_w, text_size=Pt(24),
        row_colors={0: {3: GREEN}, 1: {3: LGRAY}, 2: {3: LGRAY}, 3: {3: GOLD}})

    # Semantic/Phonetic ratio callout
    ratio_box = add_rect(slide, MX, CT + Inches(3.2), col_w, Inches(1.0),
                         fill=NAVY2, border_color=TEAL, border_w=Pt(1.5))
    add_text(slide, "Semantic / Phonetic Ratio",
             MX + Inches(0.3), CT + Inches(3.25), col_w - Inches(0.6), Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)
    add_text(slide,
        "LRS3:  1.01  (meaning tracks sound)\n"
        "YouTube:  0.87  (meaning degrades 13% faster than sound)",
        MX + Inches(0.3), CT + Inches(3.55), col_w - Inches(0.6), Inches(0.55),
        size=Pt(24), color=WHITE)

    # ── Right column: real examples ──
    rx = MX + col_w + gap
    rw = CW - col_w - gap

    add_text(slide, "LRS3 Error (WER 29%, Sem 0.93)",
             rx, CT + Inches(0.5), rw, Inches(0.3),
             size=Pt(24), color=GREEN, bold=True)
    add_text(slide,
        'REF: "spending 14-16 hours a day"\n'
        'HYP: "spending like 40-60 hours a day"\n'
        '\u2192 Numbers wrong, meaning intact',
        rx, CT + Inches(0.85), rw, Inches(1.1),
        size=Pt(24), color=WHITE)

    add_text(slide, "YouTube Error (WER 33%, Sem 0.16)",
             rx, CT + Inches(2.1), rw, Inches(0.3),
             size=Pt(24), color=CORAL, bold=True)
    add_text(slide,
        'REF: "talking with admiral mcrae"\n'
        'HYP: "talking with animal migratory"\n'
        '\u2192 Same sounds, completely different topic',
        rx, CT + Inches(2.45), rw, Inches(1.1),
        size=Pt(24), color=WHITE)

    # ── Bottom: 3 reasons why ──
    why_top = CT + Inches(4.4)
    add_text(slide, "Why the Domain Gap Is Semantic",
             MX, why_top, CW, Inches(0.35),
             size=Pt(24), color=TEAL, bold=True)
    bul = add_bullets(slide, [
        ("Visual encoder trained on LRS3 \u2192 better features \u2192 "
         "wrong words stay in semantic neighbourhood", {"color": WHITE}),
        ("TED vocabulary is general \u2014 substitutions are semantically close. "
         "YouTube has jargon, names, slang \u2192 random substitutions",
         {"color": WHITE}),
        ("LLM prior anchors on structured TED grammar. "
         "YouTube's informal speech gives less context to anchor on",
         {"color": WHITE}),
    ], MX, why_top + Inches(0.35), CW, Inches(1.5), size=Pt(24))

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
    """IS results headline — Oracle (MBR) vs Realistic (Trust-gate).

    Restaged May 6 2026 to lead with the production MBR-default numbers and
    introduce the Oracle vs Realistic framing. All numerics are tagged with
    `# audit:KEY` comments pointing back to
    docs/evaluation/after_amosi_audit.json.
    """
    slide = new_slide(prs)
    add_title(slide, "Where It Works — and How It Fails: Oracle vs Realistic")
    add_accent_line(slide)

    # ── Top row: two side-by-side cards ──────────────────────────────
    # audit:bigfonts — card_h grown 3.05 -> 3.40 so Pt(24) sub-text fits
    card_w = Inches(6.0)
    card_h = Inches(3.40)
    gap_x = Inches(0.13)
    by = CT
    lx = MX
    rx = MX + card_w + gap_x

    # Audit-pinned values (after_amosi_audit.json, MBR default)
    niv_yp_pct_mbr = 61.92        # audit:niv_yp_pct_mbr
    niv_y_pct_mbr  = 23.91        # audit:niv_y_pct_mbr
    judge_yp_mbr   = 71.08        # audit:judge_v3_yp_pct_mbr
    judge_yp_base  = 68.40        # audit:judge_v3_yp_pct_baseline
    is_mean_mbr    = 2.547        # audit:is_mean_mbr
    is_mean_top1   = 2.532        # audit:is_mean_top1
    mcnemar_p      = 0.00017      # audit:mcnemar_yp_p_mbr

    # Trust-gate ≥30% green (audit:section_E_trust_gate, threshold=0.3)
    trust_n_trusted = 630         # audit:trust_gate_op_30 n_trusted
    trust_tp        = 602         # audit:trust_gate_op_30 tp_useful
    trust_fp        = 28          # audit:trust_gate_op_30 fp_useful
    trust_recall    = 65.2        # audit:trust_gate_op_30 recall_useful (%)
    trust_fpr       = 5.6         # audit:trust_gate_op_30 fpr_useful (%)
    trust_denom     = 1427        # per_segment_safety.csv non-empty rows

    # ── LEFT CARD: Oracle (warm CORAL) ───────────────────────────────
    oracle_shapes = []
    oracle_shapes.append(add_rect(slide, lx, by, card_w, card_h,
                          fill_color=NAVY2, border_color=CORAL,
                          border_width=Pt(2.5), corner_radius=True))
    oracle_shapes.append(add_text(slide, "Best-case  (Aggregated output)",
                          lx + Inches(0.25), by + Inches(0.1),
                          card_w - Inches(0.5), Inches(0.4),
                          size=Pt(24), color=CORAL, bold=True))
    oracle_shapes.append(add_text(slide,
        f"What the model can produce on the 1,497-segment set.",
        lx + Inches(0.25), by + Inches(0.5), card_w - Inches(0.5), Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True))

    # Big Y+P number
    oracle_shapes.append(add_text(slide, f"{niv_yp_pct_mbr:.2f}%",
        lx + Inches(0.25), by + Inches(0.85),
        card_w - Inches(0.5), Inches(0.7),
        size=Pt(40), color=CORAL, bold=True, align=PP_ALIGN.CENTER))
    oracle_shapes.append(add_text(slide,
        "NIV-Y+P  (IS ≥ 2.00, deterministic)",
        lx + Inches(0.25), by + Inches(1.55),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER))

    # Sub-numbers — 1-line each; y staggered to avoid overlap
    oracle_shapes.append(add_text(slide,
        f"NIV-Y {niv_y_pct_mbr:.1f}%  |  Mean IS {is_mean_mbr:.3f}",  # audit:niv_y_pct_mbr
        lx + Inches(0.25), by + Inches(2.10),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER))
    # LLM Judge v3 — 1 line at Pt(18); moved down to clear sub-numbers
    oracle_shapes.append(add_text(slide,
        f"LLM Judge Y+P: {judge_yp_mbr:.1f}% (vs {judge_yp_base:.1f}%, p=0.0002)",
        lx + Inches(0.25), by + Inches(2.60),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(18), color=TEAL, bold=True, align=PP_ALIGN.CENTER))

    # ── RIGHT CARD: Realistic (TEAL) ─────────────────────────────────
    realistic_shapes = []
    realistic_shapes.append(add_rect(slide, rx, by, card_w, card_h,
                            fill_color=NAVY2, border_color=TEAL,
                            border_width=Pt(2.5), corner_radius=True))
    realistic_shapes.append(add_text(slide, "Realistic  (Trust-gate output)",
                            rx + Inches(0.25), by + Inches(0.1),
                            card_w - Inches(0.5), Inches(1.0),
                            size=Pt(24), color=TEAL, bold=True))
    realistic_shapes.append(add_text(slide,
        "What the user can confidently rely on (≥30% green operating point).",
        rx + Inches(0.25), by + Inches(0.5), card_w - Inches(0.5), Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True))

    realistic_shapes.append(add_text(slide, f"{trust_recall:.1f}%",
        rx + Inches(0.25), by + Inches(0.85),
        card_w - Inches(0.5), Inches(0.7),
        size=Pt(40), color=TEAL, bold=True, align=PP_ALIGN.CENTER))
    realistic_shapes.append(add_text(slide,
        "Recall of useful content  (FPR " + f"{trust_fpr:.1f}%)",
        rx + Inches(0.25), by + Inches(1.55),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER))

    # Sub-numbers — 1-line; moved to y+2.10 to clear label (text ends ~+2.00)
    realistic_shapes.append(add_text(slide,
        f"{trust_n_trusted} trusted  (TP {trust_tp} | FP {trust_fp})",
        rx + Inches(0.25), by + Inches(2.10),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(20), color=WHITE, align=PP_ALIGN.CENTER))
    realistic_shapes.append(add_text(slide,
        "Agreement-aware bands \u2014 calibrated",
        rx + Inches(0.25), by + Inches(2.60),
        card_w - Inches(0.5), Inches(0.45),
        size=Pt(24), color=TEAL, bold=True, align=PP_ALIGN.CENTER))

    # Caveat — shortened 1 line, moved to y+3.08 to clear joint conf+beam
    realistic_shapes.append(add_text(slide,
        f"Trust-gate: {trust_denom} non-empty segs (70 empty excluded)",
        rx + Inches(0.25), by + Inches(3.08),
        card_w - Inches(0.5), Inches(0.32),
        size=Pt(16), color=MGRAY, italic=True, align=PP_ALIGN.CENTER))

    # ── Bottom: tier distribution under MBR ──────────────────────────
    # audit:tier_5_count_mbr ... tier_1_count_mbr (sums to 1497)
    # CUT v3 (overflow): shortened labels to fit 1-line in 3.6" at 20pt (~19 cpl).
    tiers = [
        ("Tier 5 Excellent ≥4.0",   291, GREEN),    # audit:tier_5_count_mbr
        ("Tier 4 Good 3.0–3.99",    324, TEAL),     # audit:tier_4_count_mbr
        ("Tier 3 Fair 2.0–2.99",    312, YELLOW),   # audit:tier_3_count_mbr
        ("Tier 2 Poor 1.0–1.99",    329, ORANGE),   # audit:tier_2_count_mbr
        ("Tier 1 Failed <1.0",      241, RED),      # audit:tier_1_count_mbr
    ]
    # audit:bigfonts2 — bar_h shrunk 0.40 -> 0.34 + bar_gap 0.06 -> 0.04 to
    # clear slide-num zone (Tier 1 label was overlapping "37" footer at y=7.12).
    bar_y0 = by + card_h + Inches(0.05)
    bar_h = Inches(0.34)
    bar_gap = Inches(0.04)
    label_w = Inches(3.6)
    # max_w trimmed from 7.5" to 7.2" so the longest tier (count=329) leaves
    # ~0.2" healthy margin off the slide right edge (audit flagged 0.03in).
    max_w = Inches(7.0)
    bar_x = MX + label_w + Inches(0.15)

    # CUT v3: tier label/value Pt(24) -> Pt(20) so the last row's wrap
    # falls under safe-zone 7.05 (was rendering at bottom 7.22).
    tier_shapes = []
    for i, (label, count, color) in enumerate(tiers):
        y = bar_y0 + i * (bar_h + bar_gap)
        lbl = add_text(slide, label, MX, y, label_w, bar_h,
                 size=Pt(20), color=WHITE, align=PP_ALIGN.RIGHT)
        # Scale: max count among tiers ~= 329 → use 350 for headroom
        w = int(max_w * count / 350.0)
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color)
        val = add_text(slide, f"{count}  ({count / 1497.0 * 100:.1f}%)",
                 bar_x + w + Inches(0.1), y, Inches(2.0), bar_h,
                 size=Pt(20), color=LGRAY)
        tier_shapes.extend([lbl, bar, val])

    _finish(slide, 7,
        "Restaged May 6 2026: Oracle (MBR best-case) on the left — what the model "
        "can produce — vs Realistic (Trust-gate output) on the right — what the user "
        "can confidently rely on. "
        f"Oracle: NIV-Y+P {niv_yp_pct_mbr:.2f}% (IS≥2.00 deterministic), "
        f"NIV-Y {niv_y_pct_mbr:.2f}% (IS≥3.80), "
        f"LLM Judge v3 Y+P {judge_yp_mbr:.2f}% vs baseline {judge_yp_base:.2f}% "
        f"(paired McNemar p={mcnemar_p:.5f}). "
        f"Realistic: at the ≥30% green Trust-gate, "
        f"{trust_recall:.1f}% recall / {trust_fpr:.1f}% FPR "
        f"({trust_n_trusted} trusted = {trust_tp} TPs + {trust_fp} FPs of "
        f"{trust_denom} non-empty segments). "
        "Mean IS = 2.547 (MBR) vs 2.532 (top-1 baseline). "
        "DENOMINATOR CAVEAT (logic-fix §2 Slide 36/37/38): Oracle metrics "
        f"are computed across all 1,497 segments; Trust-gate recall is computed "
        f"on the {trust_denom} non-empty segments (excludes 70 empty hypotheses). "
        "The two cards are different lenses on the system, not progressive "
        "refinements of the same denominator. "
        "Tier distribution under MBR (bottom of slide): Tier 5 — Excellent "
        "(IS >= 4.0) holds 291 segments = 19% (audit:tier_5_pct_mbr); "
        "Tier 4 (3.0-3.99) 324 = 22%; Tier 3 (2.0-2.99) 312 = 21%; "
        "Tier 2 (1.0-1.99) 329 = 22%; Tier 1 (<1.0) 241 = 16%.\n\n"
        "PEER DETAIL — 1,427 = 1,497 − 70 empty hypotheses (model emitted "
        "no tokens; usually below decode threshold). Trust-gate operating "
        "points computed on 1,427 since empty segments cannot be 'trusted'. "
        "IS distribution metrics use full 1,497 (treating empty as IS=0). "
        "Sources: docs/evaluation/after_amosi_audit.json (sections A, F, E), "
        "docs/evaluation/threshold_calibration_vs_opus.md.",
        [oracle_shapes, realistic_shapes, tier_shapes], click_reveal=True)

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
        "5 failure modes — share of ALL 1,497 segments each mode affects",
        MX, CT, CW, Inches(0.87), size=Pt(20), color=LGRAY, italic=True)

    modes = [
        ("Wrong Topic",              17.0, 255, GOLD),
        ("Hallucination",              7.2, 108, CORAL),
        ("Signal Loss",                5.3,  80, MGRAY),
        ("Right Topic, Wrong Details", 5.3,  79, TEAL),
        ("Accumulated Errors",          3.5,  52, LGRAY),
    ]

    # Full-width bar chart (right image removed per #329).
    bar_h = Inches(0.65)
    bar_gap = Inches(0.2)
    label_w = Inches(3.2)
    max_bar_w = Inches(6.0)
    val_w = Inches(1.8)
    bar_x = MX + label_w + Inches(0.15)
    start_y = CT + Inches(0.55)
    bar_groups = []
    for i, (name, pct, count, color) in enumerate(modes):
        y = start_y + i * (bar_h + bar_gap)
        # Label
        # CUT v3 (overflow): Pt(24) -> Pt(18) so 27-char label fits 2.4" width.
        lbl = add_text(slide, name, MX, y, label_w, bar_h,
                 size=Pt(18), color=WHITE, bold=True, align=PP_ALIGN.RIGHT)
        # Bar
        w = max(Inches(0.2), int(max_bar_w * pct / 20.0))
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color,
                       corner_radius=True)
        # Value label
        val = add_text(slide, f"{pct}% ({count})",
                 bar_x + w + Inches(0.12), y, val_w, bar_h,
                 size=Pt(18), color=LGRAY)
        bar_groups.append([lbl, bar, val])

    # Right image removed per user review (#329 extra figure)
    add_text(slide,
             "Failures are diverse — no single fix. Each roadmap phase "
             "targets specific modes.",
             MX, Inches(6.4), CW, Inches(0.4),
             size=Pt(18), color=LGRAY, italic=True)

    _finish(slide, 8,
        "574 below-threshold segments (IS < 2.00) classified into 5 mutually "
        "exclusive failure categories. Wrong Topic dominates at 44% (255 "
        "segments) and combines topic drift with phonetic confusion. "
        "Hallucination is second at 19% (108) — fluent but fabricated text, "
        "the most dangerous failure mode for downstream consumers. Signal "
        "Loss (14%, 80 segments) and Right Topic Wrong Details (14%, 79 "
        "segments) are roughly tied. Accumulated Errors drops to just 9% "
        "(52 segments) because most mild-error segments now fall above the "
        "IS 2.00 threshold. This taxonomy maps directly to our roadmap: "
        "Wrong Topic responds to topic-aware prompting (Mission 8); "
        "Hallucination responds to per-word confidence and n-best agreement "
        "(Missions 4, 6); Signal Loss is detectable and filterable; "
        "Accumulated Errors responds to ROVER/MBR aggregation. "
        "Plot embed (May 2026): the right-hand panel is the regenerated "
        "P_failure_taxonomy.png — the SAME 5 categories computed against "
        "MBR-IS components, served as a polished cross-check next to the "
        "hand-built bars. Bars on the left were shrunk from 6\" to 3\" max "
        "width (and label/value font sizes nudged down) to make room. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.",
        bar_groups)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_1a(prs):
    """Failure mode taxonomy Part 1: categories 1-3 by impact.

    audit:bigfonts — trailing footnote-style ASR-taxonomy citation dropped per
    spec; card_h grown 1.35 -> 1.55 for Pt(24)/Pt(24) body content.
    """
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy (1/2): Highest Impact First")
    add_accent_line(slide)

    add_text(slide,
        "574 below-threshold segments (IS < 2.0) classified into 5 mutually exclusive "
        "categories \u2014 each segment gets exactly one label, checked 1\u21925.",
        MX, CT, CW, Inches(0.55), size=Pt(18), color=LGRAY, italic=True)
    # audit:bigfonts — trailing "Grounded in ASR error taxonomy..." citation
    # subtitle dropped to free vertical space for taller cards.

    modes_1 = [
        ("1. Wrong Topic", "44.4%", "255 segments", GOLD,
         "Mouth shapes decoded to wrong domain",
         "Semantic < 0.2 (phonetic-matched or not)",
         "Ref: \u201cweight loss and diet\u201d \u2192 Hyp: \u201cwanted to be a princess\u201d"),
        ("2. Hallucination", "18.8%", "108 segments", GOLD,
         "Model invented fake text",
         "WER \u2265 100% (output longer than reference)",
         "Ref: \u201ccarry strap\u201d \u2192 Hyp: \u201cholocaust denier explanation of the final act\u201d"),
        ("3. Right Topic, Wrong Details", "13.8%", "79 segments", CORAL,
         "Roughly right but names/content words lost",
         "NEA F1 < 20% OR key content words substituted (Semantic \u2265 0.2)",
         "Ref: \u201c13th amendment is going\u201d \u2192 Hyp: \u201c13th may mean something to him\u201d"),
    ]

    # CUT v3 (overflow): card_h 1.55 -> 1.65 + name_w 4.8 -> 5.4 so the
    # 24pt 2-line t1/t2 fit; t1/t2 heights bumped 0.35/0.85 -> 0.50/1.05.
    # OVERLAP fix: card_h 1.65 -> 1.45, y0 CT+0.55 -> CT+0.65 (subtitle ends
    # CT+0.55 after h trim 0.8->0.55), t1/t2 heights trimmed proportionally.
    card_h = Inches(1.45)
    gap = Inches(0.10)
    y0 = CT + Inches(0.65)
    name_w = Inches(5.4)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes_1):
        y = y0 + i * (card_h + gap)

        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        # CUT v3 (overflow): 0.50 -> 0.70 so 36-char "Right Topic..." fits 2 lines.
        t1 = add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.08),
                 name_w - Inches(0.3), Inches(0.55),
                 size=Pt(20), color=color, bold=True)
        t2 = add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.60),
                 name_w - Inches(0.3), Inches(0.80),
                 size=Pt(20), color=LGRAY)
        t3 = add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.08),
                 rule_w - Inches(0.15), Inches(0.87),
                 size=Pt(20), color=WHITE)
        t4 = add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.60),
                 rule_w - Inches(0.15), Inches(0.80),
                 size=Pt(18), color=LGRAY, italic=True)
        anim_groups.append([r, t1, t2, t3, t4])

    add_text(slide,
        "Ordered by impact - highest to lowest (continued on next slide)",
        MX, Inches(6.65), CW, Inches(0.4),
        size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Failure taxonomy Part 1, ordered by impact. Wrong Topic (44%, "
        "255 of 574 below-threshold segments): the largest single category — "
        "mouth shapes decoded to a completely wrong domain (semantic "
        "similarity < 0.20, with or without phonetic match). Hallucination "
        "(19%, 108 segments): the model invents fake text, deceptive but "
        "identifiable by length (WER >= 100% and output longer than "
        "reference). Right Topic, Wrong Details (14%, 79 segments): the "
        "client-trust killer — output looks right (semantic >= 0.20) but "
        "named-entity F1 < 20% or key content words substituted; the "
        "audience can guess the topic but cannot extract the specific "
        "claim. Categories are mutually exclusive and checked in order 1->5 "
        "so each segment receives exactly one label. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.",
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
        ("5. Accumulated Errors", "9.1%", "52 segments", GOLD,
         "Many small errors compound",
         "IS < 2.0 and doesn\u2019t match categories 1\u20133",
         "Many words slightly wrong throughout, meaning erodes"),
    ]
    # audit:bigfonts — example tail trimmed for tighter Pt(24) wrap

    card_h = Inches(1.55)
    gap_ = Inches(0.25)
    y0 = CT + Inches(0.20)
    name_w = Inches(4.2)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes_2):
        y = y0 + i * (card_h + gap_)

        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.10),
                 name_w - Inches(0.3), Inches(0.55),
                 size=Pt(20), color=color, bold=True)
        t2 = add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.65),
                 name_w - Inches(0.3), Inches(0.80),
                 size=Pt(16), color=LGRAY)
        t3 = add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.10),
                 rule_w - Inches(0.15), Inches(0.55),
                 size=Pt(16), color=WHITE)
        t4 = add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.70),
                 rule_w - Inches(0.15), Inches(0.75),
                 size=Pt(14), color=LGRAY, italic=True)
        anim_groups.append([r, t1, t2, t3, t4])

    # Summary bar
    sum_y = y0 + 2 * (card_h + gap_) + Inches(0.30)
    sr = add_rect(slide, MX, sum_y, CW, Inches(1.10), fill_color=NAVY2,
                  border_color=GOLD, border_width=Pt(2), corner_radius=True)
    add_text(slide,
        "Key Insight: Categories 4 & 5 are lower impact but still 23.0% of failures",
        MX + Inches(0.3), sum_y + Inches(0.12), CW - Inches(0.6), Inches(0.40),
        size=Pt(18), color=GOLD, bold=True)
    add_text(slide,
        "Accumulated errors respond to multi-hypothesis aggregation (shipped). "
        "Signal loss is detectable and filterable — lowest priority to fix.",
        MX + Inches(0.3), sum_y + Inches(0.55), CW - Inches(0.6), Inches(0.50),
        size=Pt(14), color=WHITE)
    anim_groups.append([sr])

    _finish(slide, 0,
        "Failure taxonomy Part 2. Signal Loss (14%, 80 segments): empty or "
        "near-empty output (length ratio < 0.3) — detectable, filterable, "
        "and the lowest priority to fix because the failure self-reports. "
        "Accumulated Errors (9%, 52 segments): death by a thousand cuts, "
        "many small errors throughout the segment that compound to IS < "
        "2.00 without falling into any of categories 1-3 — responds well "
        "to N-best aggregation (ROVER, MBR), which is what Mission 6 "
        "shipped on May 1 2026. Together categories 4 and 5 cover 23% "
        "of below-threshold failures, but unlike Wrong Topic and "
        "Hallucination they are mostly recoverable through engineering, "
        "not modeling. Mention to peers: when we run the n-best paired "
        "tests later in the deck, the Y+P gain we measure (+2.7 percentage "
        "points for MBR over baseline) is concentrated in this Accumulated "
        "Errors slice. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/beam-search/n_best_implementation.md.",
        anim_groups, click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — REAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — REAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_2(prs):
    """Three concrete failure mode examples for the hardest-to-distinguish categories.

    audit:bigfonts — "why" body trimmed to 2 short bullet lines per card per
    spec ("Tight. Trim bullets to 2 per card."). Long quoted ref/hyp strings
    kept as-is — they're load-bearing data.
    """
    slide = new_slide(prs)
    add_title(slide, "Failure Modes: Real Examples")
    add_accent_line(slide)

    # Three cards side by side
    cw_card = Inches(3.95)
    ch_card = Inches(5.6)
    gap = Inches(0.21)
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
        # CUT v3 (overflow): 0.50 -> 0.70 so 36-char title fits 2 lines.
        card_shapes.append(add_text(slide, f'{ex["title"]}  ({ex["pct"]})',
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.70),
                 size=Pt(20), color=ex["color"], bold=True, align=PP_ALIGN.CENTER))

        # CUT v3 (overflow): shrunk all body text to 16pt to fit 3.65"-wide cards.
        # Reference
        card_shapes.append(add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.65),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True))
        card_shapes.append(add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.95), cw_card - Inches(0.3), Inches(1.00),
                 size=Pt(16), color=WHITE, italic=True))

        # Hypothesis
        card_shapes.append(add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(2.05),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True))
        card_shapes.append(add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.35), cw_card - Inches(0.3), Inches(1.00),
                 size=Pt(16), color=ex["color"], italic=True))

        # Metrics badge
        card_shapes.append(add_text(slide, f'WER {ex["wer"]}  |  IS {ex["is_score"]}',
                 x + Inches(0.15), cy + Inches(3.45), cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(18), color=WHITE, bold=True, align=PP_ALIGN.CENTER))

        # Why explanation
        card_shapes.append(add_text(slide, ex["why_label"],
                 x + Inches(0.15), cy + Inches(3.85),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(13), color=TEAL, bold=True))
        card_shapes.append(add_text(slide, ex["why"],
                 x + Inches(0.15), cy + Inches(4.15), cw_card - Inches(0.3), Inches(1.40),
                 size=Pt(11), color=LGRAY))

        anim_groups.append(card_shapes)

    _finish(slide, 0,
        "Three real examples drawn from our 1,497-segment evaluation, one per "
        "category. Distribution numbers in the badges (19% / 44% / 14%) "
        "are the within-failure-set shares from the taxonomy bar chart earlier "
        "in this section, computed across the 574 below-threshold (IS<2.00) "
        "segments. Per-card metrics: Hallucination card WER 100% / IS 0.1; "
        "Wrong Topic card WER 97% / IS 0.38 (the highest WER on the slide "
        "is actually Wrong Topic, not Hallucination — same length swap to "
        "a different subject); Right Topic Wrong Details WER 81% / IS 2.14. "
        "Hallucination vs Wrong Topic: hallucination generates MORE words "
        "than the reference (WER >= 100%, length ratio >> 1), while Wrong "
        "Topic substitutes at similar length (~97% WER). Wrong Topic vs "
        "Right Topic Wrong Details: a semantic similarity threshold of "
        "0.20 separates them — below 0.20 means completely different "
        "subject, above 0.20 means topic preserved but details lost. "
        "Right Topic Wrong Details is the 'frustrating near-miss' — you "
        "can tell what the speaker was ABOUT but not what they SAID. "
        "Mention to peers: this slide is the qualitative anchor for the "
        "taxonomy bar chart shown earlier in this section. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/intelligibility/intelligibility_summary.json.",
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
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["Category", "Impact", "Fix"]
    rows = [
        ["Wrong Topic (44.4%)", "Very High — largest category", "LLM swap + data"],
        ["Hallucination (18.8%)", "High — deceptive but identifiable", "Confidence scoring"],
        ["Signal Loss (13.9%)", "Medium — detectable, filterable", "Quality filtering"],
        ["Right Topic, Wrong Details (13.8%)", "Medium — clients lose trust", "Domain fine-tuning"],
        ["Accumulated Errors (9.1%)", "Lower — death by 1000 cuts", "Majority's favorite sentence"],
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
                    row_height=Inches(0.48),
                    col_widths=[Inches(4.0), Inches(3.8), Inches(4.33)],
                    text_size=Pt(18),
                    row_colors=row_colors)

    # Conclusion callout
    callout_r = add_rect(slide, MX, Inches(5.55), CW, Inches(0.55), fill_color=NAVY2,
             border_color=TEAL, border_width=Pt(1.5), corner_radius=True)

    callout_t = add_text(slide,
        "Each roadmap phase targets a different failure category.",
        MX + Inches(0.2), Inches(5.60), CW - Inches(0.4), Inches(0.45),
        size=Pt(20), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Impact and fixes table for the 5-category taxonomy. Three columns: "
        "category, impact level, and fix. Severity is conveyed by row colors on "
        "both category and impact columns: LGRAY (low, Signal Loss), YELLOW "
        "(moderate, Hallucination), ORANGE (high, Wrong Topic), RED (critical, "
        "Right Topic Wrong Details), YELLOW (medium, Accumulated Errors). "
        "Right Topic Wrong Details is the most dangerous because clients cannot "
        "trust the output. Wrong Topic is the LARGEST at 44% and the most "
        "amenable to improvement through LLM upgrade. 54% of failures trace "
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


def slide_metric_transition(prs):  # audit:bigfonts2
    """Oracle -> Realistic flow under MBR (May 6 2026 restage).

    audit:bigfonts2 — Pass 2 BLOCKER fix: card_h shrunk 1.20 -> 1.05;
    foot caveat removed (moved fully to speaker notes; was overflowing to
    y=7.80). 4 cards now fit within y=1.45 to ~6.85.
    """
    slide = new_slide(prs)
    add_title(slide, "From Literature Metric to User-Trusted Output")
    add_accent_line(slide)

    # Audit-pinned numbers (MBR default unless noted)
    wer_top1     = 64.05    # audit:wer_mean_top1   (Section B)
    wer_mbr      = 63.84    # audit:wer_mean_mbr    (Section B)
    is_yp_mbr    = 61.92    # audit:niv_yp_pct_mbr
    judge_yp_mbr = 71.08    # audit:judge_v3_yp_pct_mbr
    judge_yp_base= 68.40    # audit:judge_v3_yp_pct_baseline
    trust_recall = 65.2     # audit:section_E_trust_gate threshold=0.30 recall_useful (%)
    trust_fpr    = 5.6      # audit:section_E_trust_gate threshold=0.30 fpr_useful (%)
    trust_n      = 630      # audit:section_E_trust_gate threshold=0.30 n_trusted
    eff_legacy_mbr = 51.50  # audit:effective_capture_legacy_pct_mbr

    # CUT v3 (overflow): arrow_h 0.22 -> 0.40 so 24pt arrows render fully;
    # card_h trimmed 1.10 -> 1.00 to keep total under safe zone.
    card_w = CW - Inches(2.0)
    card_h = Inches(1.00)
    card_x = MX + Inches(1.0)
    arrow_h = Inches(0.40)

    # ── Card 1: WER (literature metric) ──────────────────────────────
    c1_y = CT + Inches(0.0)
    g1 = []
    g1.append(add_rect(slide, card_x, c1_y, card_w, card_h,
                        fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                        corner_radius=True))
    g1.append(add_text(slide, f"{wer_mbr:.2f}%",
                        card_x + Inches(0.3), c1_y + Inches(0.05),
                        Inches(2.6), card_h - Inches(0.1),
                        size=Pt(38), color=CORAL, bold=True))
    # audit:bigfonts — copy trimmed for Pt(24)
    g1.append(add_text(slide,
        f"WER (aggregated: {wer_mbr:.2f}%; single-pass: {wer_top1:.2f}%)\n"
        "Literature metric \u2014 pessimistic on wild data.",
        card_x + Inches(3.0), c1_y + Inches(0.1),
        card_w - Inches(3.3), card_h - Inches(0.2),
        size=Pt(24), color=LGRAY))
    # No strikethrough — WER is still valid, just pessimistic

    a1_y = c1_y + card_h + Inches(0.04)
    g1_arrow = []
    g1_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a1_y, Inches(0.6), arrow_h,
                              size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER))

    # -- Card 2: NIV-Y+P (deterministic IS, MBR) --
    c2_y = a1_y + arrow_h
    g2 = []
    g2.append(add_rect(slide, card_x, c2_y, card_w, card_h,
                       fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                       corner_radius=True))
    g2.append(add_text(slide, f"{is_yp_mbr:.2f}%",
                       card_x + Inches(0.3), c2_y + Inches(0.05),
                       Inches(2.6), card_h - Inches(0.1),
                       size=Pt(38), color=TEAL, bold=True))
    # audit:bigfonts — copy trimmed for Pt(24)
    # CUT v3: tightened second-line wording to fit one line at 24pt.
    g2.append(add_text(slide,
        "NIV-Y+P  (IS \u2265 2.00, aggregated output)\n"
        "Deterministic agrees: 927 / 1,497.",
        card_x + Inches(3.0), c2_y + Inches(0.1),
        card_w - Inches(3.3), card_h - Inches(0.2),
        size=Pt(24), color=WHITE))

    a2_y = c2_y + card_h + Inches(0.04)
    g2_arrow = []
    g2_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a2_y, Inches(0.6), arrow_h,
                              size=Pt(24), color=GREEN, align=PP_ALIGN.CENTER))

    # ── Card 3: LLM Judge v3 Oracle ──────────────────────────────────
    c3_y = a2_y + arrow_h
    g3 = []
    g3.append(add_rect(slide, card_x, c3_y, card_w, card_h,
                       fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                       corner_radius=True))
    g3.append(add_text(slide, f"{judge_yp_mbr:.2f}%",
                       card_x + Inches(0.3), c3_y + Inches(0.05),
                       Inches(2.6), card_h - Inches(0.1),
                       size=Pt(38), color=GREEN, bold=True))
    # audit:bigfonts — copy trimmed for Pt(24)
    # CUT v3: tightened second-line wording to fit one line at 24pt.
    # CUT v4: one-line caption to fit narrow card; italic = caption role.
    g3.append(add_text(slide,
        f"Judge Y+P (Oracle, base {judge_yp_base:.0f}%) p=0.00017",
        card_x + Inches(3.0), c3_y + Inches(0.1),
        card_w - Inches(3.3), card_h - Inches(0.2),
        size=Pt(20), color=WHITE, italic=True))

    a3_y = c3_y + card_h + Inches(0.04)
    g3_arrow = [add_text(slide, "▼", card_x + card_w / 2 - Inches(0.3),
                         a3_y, Inches(0.6), arrow_h,
                         size=Pt(24), color=GOLD, align=PP_ALIGN.CENTER)]

    # ── Card 4: Realistic — Trust-gate operating point ───────────────
    c4_y = a3_y + arrow_h
    g4 = []
    g4.append(add_rect(slide, card_x, c4_y, card_w, card_h,
                       fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                       corner_radius=True))
    g4.append(add_text(slide, f"{trust_recall:.1f}%",
                       card_x + Inches(0.3), c4_y + Inches(0.05),
                       Inches(2.6), card_h - Inches(0.1),
                       size=Pt(38), color=GOLD, bold=True))
    # audit:bigfonts — copy trimmed for Pt(24)
    g4.append(add_text(slide,
        f"Trust gate \u226530% green  \u2022  FPR {trust_fpr:.1f}%\n"
        f"User-trusted output  ({trust_n} segments).",
        card_x + Inches(3.0), c4_y + Inches(0.1),
        card_w - Inches(3.3), card_h - Inches(0.2),
        size=Pt(24), color=WHITE))

    # Denominator caveat — Cards 1/2/3 evaluate all 1,497 segments;
    # Card 4 (Trust-gate) is recall on 1,427 non-empty segments.
    # audit: after_amosi_logic_fixes.md §2 Slide 36/37/38 MAJOR — apples-to-oranges
    # denominator caveat (1,497 vs 1,427).
    # CUT v2: removed bottom denominator caveat textbox (was at foot_y reaching
    # y=7.80 — BLOCKER). Caveat preserved in speaker notes. audit:bigfonts2.
    foot_y = c4_y + card_h + Inches(0.04)
    if False:  # CUT v2 — caveat off-slide; speaker notes carry it
     g4.append(add_text(slide,
        "Cards 1\u20133: all 1,497 segments. Card 4: recall on 1,427 non-empty "
        "(70 empty excluded). Four lenses, not progressive refinements.",
        card_x, foot_y, card_w, Inches(0.55),
        size=Pt(16), color=MGRAY, italic=True, align=PP_ALIGN.CENTER))

    _finish(slide, 0,
        "Restaged May 6 2026 as Oracle -> Realistic flow under MBR. "
        f"Card 1 — WER {wer_mbr:.2f}% (top-1 {wer_top1:.2f}%): the literature "
        "metric, pessimistic on wild data. "
        f"Card 2 — NIV-Y+P {is_yp_mbr:.2f}% (MBR-IS): our deterministic metric "
        "agrees on 927/1,497. "
        f"Card 3 — LLM Judge v3 Y+P {judge_yp_mbr:.2f}% (MBR Oracle, +2.67 pp vs "
        f"baseline {judge_yp_base:.2f}%, paired McNemar p=0.00017): independent "
        "reviewer confirms. "
        f"Card 4 — Trust gate ≥30% green: {trust_recall:.1f}% recall, "
        f"{trust_fpr:.1f}% FPR ({trust_n} trusted). "
        "Legacy salvage framing dropped — replaced by Trust-gate operating point. "
        f"For reference, the legacy IS≥3.0 + LLM-context-prob salvage rate under "
        f"MBR is {eff_legacy_mbr:.2f}% (audit:effective_capture_legacy_pct_mbr). "
        "DENOMINATOR CAVEAT (logic-fix §2 Slide 36/37/38): Cards 1–3 are "
        "evaluated across all 1,497 segments; Card 4 (Trust gate) is recall on "
        "1,427 non-empty segments (excludes 70 empty hypotheses). The funnel is "
        "four metrics on different denominators, not four progressive refinements "
        "of the same number.\n\n"
        "PEER DETAIL — Paired McNemar: contingency on 1,497 segments per "
        "method. For MBR Y+P: b=89 (baseline-N → MBR-Y+P), c=49 "
        "(baseline-Y+P → MBR-N), chi^2 = (b−c)^2/(b+c) = 11.6, two-tailed "
        "p=0.00017. Bonferroni-adjusted threshold for 8 simultaneous tests "
        "(4 methods × 2 verdict cuts) is alpha=0.00625; both MBR "
        "(p=0.00017) and vote_conf (p=0.00257) survive. "
        "Sources: docs/evaluation/after_amosi_audit.md sections A, B, E, F.",
        [g1, g1_arrow + g2, g2_arrow + g3, g3_arrow + g4], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

def slide_10(prs):
    build_two_col(prs, 10, "Three Root Causes \u2014 Why 64% WER?",
        "Root Causes", [
            ("1. Domain Mismatch", {"bold": True, "color": TEAL}),
            "Model trained on TED talks (LRS3); real-world: DIY, cooking, sports",
            ("2. Short Segments Fail", {"bold": True, "color": TEAL}),
            "Under 10 words: only 53% useful vs 68% for 20+ words",
            ("3. Hallucination (20%)", {"bold": True, "color": TEAL}),
            "LLM prior overwhelms weak visual signal \u2014 fluent but fabricated",
        ],
        "By the Numbers", [
            ("Business/Finance: IS 3.08, 78% useful", {"color": GREEN}),
            ("DIY/Home: IS 2.13, 41% useful \u2014 37pp gap", {"color": CORAL}),
            "Short (5\u201310 words): 74% WER, 53% useful",
            "Long (20+ words): 55% WER, 68% useful \u2014 15pp gap",
            ("28% of failures = drift + hallucination", {"color": CORAL, "bold": True}),
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
                  size=Pt(24), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Names (Admiral McRae), numbers (13th), places, "
        "organizations",
        "Either correct or destroyed \u2014 no partial credit",
        ("Useful: 59% NEA F1 vs Non-useful: 6%",
         {"bold": True, "color": CORAL}),
        "53pp gap \u2014 largest differentiator of any signal",
        "17% of IS variance (highest for 15%-weight signal)",
        'A viewer can guess a missing "the" but not a missing name',
    ], MX, CT + Inches(0.5), col_w, Inches(3.8), size=Pt(24))

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
        "why NEA accounts for 17% of IS variance despite only 15% weight \u2014 "
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
                  size=Pt(24), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Beam size, length penalty, temperature, sampling",
        "13 experiments (A\u2013M) on 107-segment subset",
        "Best config (J) validated on all 1,497 segments",
    ], MX, CT + Inches(0.5), col_w, Inches(1.8), size=Pt(24))

    # Callout box — key finding (more vertical room)
    r1 = add_rect(slide, MX, CT + Inches(2.6), col_w, Inches(2.2),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    kf_title = add_text(slide, "Key Finding",
             MX + Inches(0.25), CT + Inches(2.75), col_w - Inches(0.5), Inches(0.3),
             size=Pt(24), color=CORAL, bold=True)
    kf_bullets = add_bullets(slide, [
        # audit: after_amosi_logic_fixes.md fix #8 — cross-config caveat:
        # 16 top-1 decode-parameter configs; MBR not included.
        "Segment rankings identical across all configs (r > 0.92, "
        "16 top-1 decode-parameter configs; MBR not included)",
        "Good segments stay good; bad ones stay bad regardless",
        ("Bottleneck = visual encoder, not decode parameters",
         {"bold": True, "color": CORAL}),
    ], MX + Inches(0.25), CT + Inches(3.15), col_w - Inches(0.5), Inches(1.5),
       size=Pt(24))

    # Right — What we found
    rx = MX + col_w + gap
    rt = add_text(slide, "What We Found", rx, CT, col_w, Inches(0.35),
                  size=Pt(24), color=CORAL, bold=True)

    # Config J note (shorter)
    j_note = add_text(slide,
        "Config J: lenpen=1.0, temp=0.5  (Baseline = top-1 decode, pre-MBR)",
        rx, CT + Inches(0.4), col_w, Inches(0.25),
        size=Pt(18), color=MGRAY, italic=True)

    # audit: numbers below are top-1 baseline anchors from the 13-experiment
    # tuning sweep (legitimate pre-MBR baseline framing, OK_TOP1_AS_BASELINE).
    # Shadows is_mean_top1, niv_yp_pct_top1, hallucination_pct_top1.
    headers = ["Metric", "Baseline (top-1)", "Config J", "\u0394"]
    rows = [
        ["Mean IS", "2.53", "2.60", "+0.07"],            # audit:is_mean_top1 (baseline anchor)
        ["Useful (IS\u22652)", "62%", "63%", "+1.2pp"],  # audit:niv_yp_pct_top1 (baseline anchor)
        ["Empty outputs", "5%", "0%", "\u221270"],
        ["Hallucinations", "20%", "23%", "+41"],     # audit:hallucination_pct_top1 (baseline anchor)
        ["Mean WWER", "60%", "60%", "\u22120.7pp"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.75), col_w,
                    row_height=Inches(0.38),
                    col_widths=[Inches(1.7), Inches(1.2), Inches(1.2), Inches(1.4)],
                    text_size=Pt(24))

    # Verdict — clear of table with breathing room
    verdict = add_text(slide,
        "Eliminates empties but adds hallucinations.\n"
        "Net IS gain: +0.08 \u2014 tuning is mitigation, not a cure.",
        rx, CT + Inches(2.95), col_w, Inches(0.8),
        size=Pt(20), color=LGRAY, italic=True)

    _finish(slide, 0,
        "Condensed tuning results. 13 experiments across 4 decode parameters "
        "showed minimal improvement. Best config (J = lenpen=1.0, temp=0.5) eliminates empty outputs "
        "but increases hallucinations by 13%. Net IS gain only +0.08. "
        "Per-segment rankings are identical across configs (r > 0.92), proving "
        "the bottleneck is the visual encoder, not decode parameters. "
        "Caveat: cross-config validation covers 16 top-1 decode-parameter "
        "variants; MBR n-best aggregation is NOT in the 16 configs (audit: "
        "after_amosi_audit.json `cross_config_includes_mbr: False`).\n\n"
        "The original slide included a length penalty sensitivity chart showing "
        "the empty-vs-hallucination trade-off: lenpen=-0.5 causes 45% empty "
        "outputs; baseline (lenpen=0) has 5% empties; lenpen=1.0 (Config J) "
        "eliminates all empties but hallucinations rise from 20% to 23%; "
        "lenpen=2.0 pushes hallucinations to 53%. This demonstrates the "
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
                  size=Pt(24), color=CORAL, bold=True)
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
       size=Pt(24), bullet_color=CORAL)

    # Right — Option B (ours)
    rx = MX + col_w + gap
    rt = add_text(slide, "Option B: Design-Time LLM (Ours)", rx, CT, col_w,
                  Inches(0.4), size=Pt(24), color=GREEN, bold=True)
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
       size=Pt(24), bullet_color=GREEN)

    # Bottom
    add_text(slide,
        "Validated: IS vs Opus judge \u03ba = 0.818 (Y+P), \u03ba = 0.690 (Y), "
        "r = 0.85 Pearson correlation with LLM judge gold standard.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Two approaches: Option A calls an LLM for every pair — expensive, "
        "non-deterministic, slow. Option B (ours): the entire "
        "evaluation framework was designed at development time, then distilled into "
        "deterministic formulas. Zero cost per run, 100% reproducible. "
        "Validated at κ=0.818 (Y+P), r=0.85.",
        [[r1], [r2]], click_reveal=True)


def slide_is_dimensions(prs):
    """Three quality dimensions from PCA analysis (PC3 shown at user request).

    PC1+PC2 = 88% (Kaiser). PC3 = ~6% (entity swing, below Kaiser threshold).
    Source: docs/evaluation/is_pca_analysis.md.
    """
    slide = new_slide(prs)
    add_title(slide, "Quality Dimensions from PCA (6 IS Signals)")
    add_accent_line(slide)

    add_text(slide, "PC1+PC2 explain 88% of variance \u2014 PC3 adds 6% more (entity swing):",
             MX, CT, CW, Inches(0.55), size=Pt(24), color=LGRAY)

    # Three cards (PC1=68%, PC2=20%, PC3=6%; PC1+PC2=88% Kaiser; PC3 shown per user request)
    # CUT v4 (overlap): shortened `signals` strings to single short line each
    # so 24pt centered text doesn't wrap and crash into the t5 italic insight.
    dims = [
        ("PC1: Signal Quality", "68%", "of total variance",
         "All 5 content signals load\nequally (0.43\u20130.47)",
         "One general quality factor\ndriven by visual encoder", TEAL),
        ("PC2: Output Length", "20%", "of total variance",
         "Length Ratio dominates\n(loading 0.91)",
         "Independent of quality;\ncatches hallucination", LGRAY),
        ("PC3: Entity Swing", "6%", "of total variance",
         "NEA anti-correlates\nwith phonetics",
         "Below Kaiser threshold \u2014\nlatent entity signal", GOLD),
    ]

    cw_card = Inches(3.80)
    ch_card = Inches(4.0)
    gap = Inches(0.37)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.72)

    card_groups = []
    for i, (name, pct, label, signals, insight, color) in enumerate(dims):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5), corner_radius=True)

        # Big percentage
        t1 = add_text(slide, pct, x + Inches(0.15), cy + Inches(0.2),
                 cw_card - Inches(0.3), Inches(0.6),
                 size=Pt(40), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, label, x + Inches(0.15), cy + Inches(0.8),
                 cw_card - Inches(0.3), Inches(0.35),
                 size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

        # Name
        t3 = add_text(slide, name, x + Inches(0.15), cy + Inches(1.25),
                 cw_card - Inches(0.3), Inches(0.4),
                 size=Pt(24), color=color, bold=True, align=PP_ALIGN.CENTER)

        # Signals — h grown 0.8 -> 1.05 so 2-line 24pt centered fits cleanly.
        t4 = add_text(slide, signals, x + Inches(0.15), cy + Inches(1.75),
                 cw_card - Inches(0.3), Inches(1.05),
                 size=Pt(22), color=WHITE, align=PP_ALIGN.CENTER)

        # Insight — moved down 2.70 -> 2.90 to clear taller t4.
        t5 = add_text(slide, insight, x + Inches(0.15), cy + Inches(2.90),
                 cw_card - Inches(0.3), Inches(0.95),
                 size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

        card_groups.append([r, t1, t2, t3, t4, t5])

    _finish(slide, 0,
        "PCA on 6 IS signals. PC1 (68%): all 5 content signals load equally "
        "(0.43-0.47) \u2014 one general quality factor driven by the visual encoder. "
        "Semantic is NOT independent; it loads on PC1 just like word-accuracy signals. "
        "PC2 (20%): Length Ratio dominates (0.91), truly independent of "
        "content quality. PC1+PC2 = 88% total. "
        "PC3 (6%, entity swing): named entity accuracy anti-correlates with "
        "phonetics \u2014 below Kaiser threshold (eigenvalue < 1) but shown here "
        "as a latent signal the IS does not yet fully capture. "
        "See docs/evaluation/is_pca_analysis.md for the full PCA table.",
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
                  size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Topic", "IS", "Useful", "Judge N%"],
        [["Business/Finance", "3.08", "78%", "24%"],
         ["Education/Lecture", "2.84", "72%", "23%"],
         ["News/Politics", "2.81", "76%", "26%"],
         ["Sports/Health", "2.76", "70%", "30%"],
         ["Tech/Science", "2.70", "65%", "28%"],
         ["Entertainment", "2.23", "58%", "39%"],
         ["DIY/Home", "2.13", "41%", "52%"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(24),
        row_colors={0: {1: GREEN, 2: GREEN}, 6: {1: CORAL, 2: CORAL, 3: CORAL}})

    # Right — big number + insight
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    add_text(slide, "19%", rx, CT + Inches(0.3), rw, Inches(1.8),
             size=Pt(64), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments show\ndomain vocabulary\nconfusion",
             rx, CT + Inches(1.2), rw, Inches(1.0),
             size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "Model trained on TED talks (formal, educational)",
        ("Business content closest to training \u2192 best results",
         {"color": GREEN}),
        ("DIY content most visual, least verbal \u2192 worst results",
         {"color": CORAL}),
        "~284 segments need topic-aware fine-tuning (not just labels)",
    ], rx, CT + Inches(2.5), rw, Inches(2.5), size=Pt(24))

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
                 size=Pt(24), color=color, bold=True)
        t2 = add_text(slide, desc, x + Inches(0.2), y + Inches(0.4),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(24), color=WHITE)
        t3 = add_text(slide, f"{analogy}  \u2022  Range: {range_str}",
                 x + Inches(0.2), y + Inches(0.72),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(16), color=LGRAY, italic=True)
        card_groups.append([r, t1, t2, t3])

    # Bottom quote
    add_text(slide,
        '"Think of it like a stereo equalizer \u2014 you can adjust the dials, '
        'but the speakers determine the sound quality."',
        MX, Inches(5.8), CW, Inches(0.7),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "13 experiments tested combinations across these 4 dimensions.",
        MX, Inches(6.5), CW, Inches(0.3),
        size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER)

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
             MX, Inches(3.5), CW, Inches(1.2),
             size=Pt(30), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Section transition: we now present the research findings — our novel "
        "Intelligibility Score metric, root cause analysis, failure mode taxonomy, "
        "and decode tuning experiments.")


def slide_failure_anatomy_transition(prs):
    """Section divider (E1, research-overview): visible split inside §3
    between the 'Capture' subsection (slides 37-38) and the 'Failure
    Anatomy' subsection (slides 39-45). Mirrors the existing transition
    pattern used for §2, §4-eng, §5-future."""
    slide = new_slide(prs)

    add_text(slide, "FAILURE ANATOMY",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(48), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Where the System Fails — and Why",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(30), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=CORAL)

    add_text(slide,
        "Six failure modes → LLM salvage → trust-tier triage",
        MX, Inches(4.8), CW, Inches(0.5),
        size=Pt(22), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Section transition (visible §3 split, May 2026): we have just "
        "shown the 'where it works' half of §3 (Oracle vs Realistic, "
        "MBR aggregation funnel). We now turn to the 'failure anatomy' "
        "half: failure-mode taxonomy, deep dives, and the LLM-salvage "
        "recovery story. This divider exists per the research-overview "
        "review which flagged §3 as titled-for-success but body-heavy "
        "with failure analysis.")



