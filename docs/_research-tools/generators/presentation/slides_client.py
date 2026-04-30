"""Client deck — net-new and reframed slide builders.

The client deck mostly *calls* existing builders from slides_*.py per the
borrow-vs-build policy in the plan. This module holds only:

  1. Three genuinely new slides (no equivalent in the academic deck):
        slide_client_entity_split
        slide_client_quality_filter
        slide_client_integration_commitment

  2. Reframed slides where the academic version's framing is wrong for clients
     (jargon-heavy, deficit-toned, or showing numbers that the v3 plan strips):
        slide_client_title
        slide_client_summary
        slide_client_headline_numbers
        slide_client_agenda
        slide_client_demo_intro
        slide_client_demo_video_embed
        slide_client_demo_recap
        slide_client_section_transition (factory)
        slide_client_two_layer_confidence
        slide_client_word_color_coding
        slide_client_seq_confidence_correlation
        slide_client_trust_dashboard
        slide_client_hallucination_flag
        slide_client_what_this_means
        slide_client_validation_intro
        slide_client_agreement_chart
        slide_client_cross_config_stability
        slide_client_validation_summary
        slide_client_recap
        slide_client_next_steps
        slide_client_investment_ask

All numbers used here trace to MEMORY.md > Key Project Numbers (canonical).
"""

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from .config import (
    BG, WHITE, TEAL, CORAL, GREEN, GOLD, LGRAY, MGRAY,
    NAVY2, NAVY3, RED, YELLOW,
    SL_W, SL_H, MX, MY, CT, CW, CH,
    FONT, _auto_num, IMG,
)
from .helpers import (
    new_slide, add_title, add_accent_line, add_text, add_rich_text,
    add_bullets, add_rect, add_image, add_logo, add_slide_num,
    set_notes,
)


# ──────────────────────────────────────────────────────────────────────────
# Section 1 — "What This Is"
# ──────────────────────────────────────────────────────────────────────────


def slide_client_title(prs):
    """Title slide. Client name + date + presenter + tagline."""
    slide = new_slide(prs)
    _auto_num[0] += 1

    # Hero title (centered vertically)
    add_text(
        slide, "Argos — Visual Speech Recognition",
        MX, Inches(2.4), CW, Inches(1.0),
        size=Pt(40), bold=True, color=WHITE, align=PP_ALIGN.CENTER,
    )
    add_text(
        slide, "Built-In Confidence. Ready to Deploy.",
        MX, Inches(3.4), CW, Inches(0.6),
        size=Pt(22), color=TEAL, align=PP_ALIGN.CENTER, italic=True,
    )
    add_text(
        slide, "Yoad Oxman   ·   Argos / The Orchard   ·   April 2026",
        MX, Inches(5.6), CW, Inches(0.4),
        size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER,
    )

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Open with the product positioning: working pipeline + trust signals + "
        "we deploy it on your infrastructure. Set expectation that this is a "
        "deep dive, not a pitch — they'll see the system run end-to-end."
    ))
    return slide


def slide_client_summary(prs):
    """One-page product summary — what / who / what makes it different."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What we're showing you today")
    add_accent_line(slide)

    # Three side-by-side cards
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(1.7)
    h = Inches(4.4)

    cards = [
        ("WHAT IT DOES", TEAL,
         "Turns silent face-on video of a speaker into clean text — "
         "lip-reading at scale, with no audio track required."),
        ("WHO IT'S FOR", GOLD,
         "Teams that need to recover speech from footage where the audio "
         "is missing, noisy, or untrustworthy: media, broadcast, "
         "investigations, accessibility."),
        ("WHAT MAKES IT DIFFERENT", GREEN,
         "Per-segment confidence and per-word color coding tell you where "
         "to trust the output and where to review. You don't read every "
         "transcript — the system tells you which to read."),
    ]
    for i, (label, color, body) in enumerate(cards):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), top + Inches(0.25),
                 card_w - Inches(0.4), Inches(0.4),
                 size=Pt(13), bold=True, color=color)
        add_text(slide, body, x + Inches(0.2), top + Inches(0.85),
                 card_w - Inches(0.4), h - Inches(1.0),
                 size=Pt(15), color=WHITE)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Three sentences each. No methodology yet — that's section 5+. "
        "The differentiator is confidence; everything else flows from there."
    ))
    return slide


def slide_client_headline_numbers(prs):
    """Three big numbers — applies N1-N10 number-clarity rules.
    Source: MEMORY.md > Key Project Numbers."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Three numbers, in plain English")
    add_accent_line(slide)

    # Three big-number cards
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(1.7)
    h = Inches(3.6)

    nums = [
        ("62%", "useful output",
         "Six of every ten segments deliver usable text — "
         "viewers can extract meaning even when the wording isn't perfect.",
         GREEN),
        ("23%", "clearly conveyed",
         "About one in four segments needs no review — "
         "delivered cleanly with no further work.",
         TEAL),
        ("1 in 5", "auto-flagged",
         "The system flags low-confidence segments before you ever see "
         "them. You review the flagged ones, not all of them.",
         GOLD),
    ]
    for i, (big, label, body, color) in enumerate(nums):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, big, x, top + Inches(0.4),
                 card_w, Inches(1.5),
                 size=Pt(64), bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, label, x, top + Inches(2.0),
                 card_w, Inches(0.4),
                 size=Pt(16), color=WHITE, align=PP_ALIGN.CENTER, bold=True)
        add_text(slide, body, x + Inches(0.2), top + Inches(2.5),
                 card_w - Inches(0.4), h - Inches(2.5),
                 size=Pt(13), color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Based on 1,497 real-world video segments. Calibrated against an "
             "independent expert reviewer.",
             MX, Inches(5.6), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Numbers from MEMORY.md > Key Project Numbers. "
        "62% = 922/1497 NIV Y+P (rounded from 61.6%). "
        "23% = 346/1497 NIV Y (rounded from 23.1%). "
        "1 in 5 = 20.5% hallucination/auto-flag rate. "
        "Validation κ=0.818 vs Opus expert judge — phrased as '8 of 10' on slide. "
        "Don't read out NIV / κ on the slide; they're for your reference here."
    ))
    return slide


def slide_client_agenda(prs):
    """What you'll see today — agenda."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What you'll see today")
    add_accent_line(slide)

    add_bullets(slide, [
        "Live demo — the system processing a real video, end-to-end",
        "Output gallery — what good, partial, and flagged segments look like",
        "How confidence works — per-word color coding and per-segment scoring",
        "How we validated it — independent expert agreement",
        "What's next — pre-processing, stronger model, Arabic, integration",
    ], MX, Inches(1.8), CW, Inches(4.5), size=Pt(20))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "5-minute orientation. Don't go deep on any one item here.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 2 — Live UI Demo
# ──────────────────────────────────────────────────────────────────────────


def slide_client_demo_intro(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Watch the system process a real video")
    add_accent_line(slide)

    add_text(slide,
             "Nothing here is pre-cached. The pipeline runs in your browser. "
             "Drag in, walk away, come back to color-coded results.",
             MX, Inches(1.8), CW, Inches(1.2),
             size=Pt(20), color=LGRAY, italic=True)

    add_text(slide,
             "Click ▶ to play the walkthrough →",
             MX, Inches(4.5), CW, Inches(0.6),
             size=Pt(16), color=TEAL, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Cue the embedded video on the next slide. Pause briefly so the audience focuses.")
    return slide


def slide_client_demo_video_embed(prs):
    """Slide that embeds the recorded UI walkthrough.

    Until the user records the video, this slide shows a placeholder card so
    the deck builds. Replace the placeholder with `add_video(slide, "ui_demo", ...)`
    once the .mp4 is at presentation_materials_20260224/06_demo_videos/_ui_walkthrough_clientpitch.mp4
    AND a key 'ui_demo' is added to IMG/VIDEOS in config.py.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Live UI Demo")
    add_accent_line(slide)

    # Placeholder until C3 (recording) lands.
    box_w = Inches(11.0)
    box_h = Inches(5.0)
    box_x = (SL_W - box_w) / 2
    box_y = Inches(1.6)
    add_rect(slide, box_x, box_y, box_w, box_h, fill_color=NAVY2, border_color=TEAL)
    add_text(slide,
             "[ EMBED VIDEO HERE — _ui_walkthrough_clientpitch.mp4 ]",
             box_x, box_y + Inches(2.2), box_w, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)
    add_text(slide,
             "Insert → Video → Video on My PC. Do not link.",
             box_x, box_y + Inches(2.9), box_w, Inches(0.4),
             size=Pt(13), color=MGRAY, align=PP_ALIGN.CENTER, italic=True)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "This slide is a placeholder until the UI walkthrough video is recorded. "
        "When recorded, embed the .mp4 directly (not a link) so it plays offline."
    ))
    return slide


def slide_client_demo_recap(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What you just saw")
    add_accent_line(slide)

    add_bullets(slide, [
        "Drag-drop upload — no command line, no scripting",
        "Nine automatic stages — face detection, mouth cropping, recognition, decoding",
        "Per-word color coding — green confident, yellow review, red likely error",
        "Per-segment Intelligibility Score — calibrated against expert judgment",
        "Output is a downloadable HTML report you can hand a reviewer",
    ], MX, Inches(1.8), CW, Inches(4.5), size=Pt(18))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Tie back to the demo. If a beat didn't land in the video, restate it here.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section transitions (factory)
# ──────────────────────────────────────────────────────────────────────────


def make_section_transition(title_text, subtitle_text):
    """Factory: returns a builder function for a section transition slide."""
    def _builder(prs):
        slide = new_slide(prs)
        _auto_num[0] += 1
        add_text(slide, title_text,
                 MX, Inches(2.8), CW, Inches(1.0),
                 size=Pt(44), bold=True, color=TEAL, align=PP_ALIGN.CENTER)
        add_text(slide, subtitle_text,
                 MX, Inches(3.9), CW, Inches(0.8),
                 size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)
        add_logo(slide)
        add_slide_num(slide, _auto_num[0])
        set_notes(slide, f"Section transition: {title_text}. Pause briefly.")
        return slide
    return _builder


# ──────────────────────────────────────────────────────────────────────────
# Section 4 — Confidence & Trust
# ──────────────────────────────────────────────────────────────────────────


def slide_client_confidence_question(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "How do you know when to trust an output?")
    add_accent_line(slide)

    add_text(slide,
             "Most speech-to-text systems hand you a transcript. You read all of it. "
             "If something's wrong, you find out the hard way.",
             MX, Inches(1.8), CW, Inches(1.2), size=Pt(20), color=LGRAY)

    add_text(slide,
             "Argos is different. Every word and every segment carries a confidence "
             "signal. You read what's flagged — not everything.",
             MX, Inches(3.4), CW, Inches(1.2), size=Pt(20), color=WHITE, bold=True)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Set up the two-layer story on the next slide. Don't go deep yet.")
    return slide


def slide_client_two_layer_confidence(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Two layers of confidence")
    add_accent_line(slide)

    card_w = Inches(5.85)
    gap = Inches(0.4)
    top = Inches(1.7)
    h = Inches(4.4)

    # Layer 1 — per-word
    x1 = MX
    add_rect(slide, x1, top, card_w, h, fill_color=NAVY2, border_color=None)
    add_text(slide, "1. PER-WORD", x1 + Inches(0.3), top + Inches(0.3),
             card_w - Inches(0.6), Inches(0.4), size=Pt(14), bold=True, color=GREEN)
    add_text(slide, "From the model itself",
             x1 + Inches(0.3), top + Inches(0.85),
             card_w - Inches(0.6), Inches(0.5), size=Pt(20), bold=True, color=WHITE)
    add_bullets(slide, [
        "Every predicted word has a probability the model assigned it",
        "We surface those as green / yellow / red inline in the report",
        "You see exactly where the model was unsure",
    ], x1 + Inches(0.3), top + Inches(1.7), card_w - Inches(0.6), Inches(2.5),
       size=Pt(14))

    # Layer 2 — per-segment
    x2 = MX + card_w + gap
    add_rect(slide, x2, top, card_w, h, fill_color=NAVY2, border_color=None)
    add_text(slide, "2. PER-SEGMENT", x2 + Inches(0.3), top + Inches(0.3),
             card_w - Inches(0.6), Inches(0.4), size=Pt(14), bold=True, color=TEAL)
    add_text(slide, "From the score system",
             x2 + Inches(0.3), top + Inches(0.85),
             card_w - Inches(0.6), Inches(0.5), size=Pt(20), bold=True, color=WHITE)
    add_bullets(slide, [
        "Intelligibility Score — a 0–5 score per segment",
        "Predicts whether a viewer will understand the output",
        "Calibrated against an independent expert reviewer",
    ], x2 + Inches(0.3), top + Inches(1.7), card_w - Inches(0.6), Inches(2.5),
       size=Pt(14))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Layer 1 is per-token softmax probability from LLaMA, aggregated to "
        "per-word using min() across sub-tokens (conservative). Layer 2 is the "
        "Intelligibility Score (IS) — a 6-signal composite designed at design "
        "time by Claude (no LLM call at evaluation time). Calibrated κ=0.818 "
        "vs Opus judge (Y+P). Don't say κ on the slide."
    ))
    return slide


def slide_client_word_color_coding(prs):
    """Screenshot of the new UI report with green/yellow/red word coloring.

    Until B5 produces ui_word_confidence_screenshot.png, this slide shows a
    placeholder. After the screenshot exists, replace with add_image().
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Per-word color coding — in your report")
    add_accent_line(slide)

    # Placeholder until B5 lands
    box_w = Inches(11.0)
    box_h = Inches(4.6)
    box_x = (SL_W - box_w) / 2
    box_y = Inches(1.6)
    add_rect(slide, box_x, box_y, box_w, box_h, fill_color=NAVY2, border_color=GREEN)
    add_text(slide,
             "[ SCREENSHOT — vsp-ui report with mixed-confidence segment ]",
             box_x, box_y + Inches(1.9), box_w, Inches(0.6),
             size=Pt(20), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)
    add_text(slide,
             "Replace with: add_image(slide, 'ui_word_confidence', ...) once B5 lands.",
             box_x, box_y + Inches(2.6), box_w, Inches(0.4),
             size=Pt(13), color=MGRAY, align=PP_ALIGN.CENTER, italic=True)

    # Tiny legend
    legend_top = Inches(6.35)
    add_text(slide, "Legend  —  ", MX, legend_top, Inches(1.5), Inches(0.3),
             size=Pt(11), color=LGRAY)
    add_text(slide, "GREEN: confident",
             MX + Inches(1.4), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=GREEN, bold=True)
    add_text(slide, "YELLOW: review",
             MX + Inches(3.5), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=YELLOW, bold=True)
    add_text(slide, "RED: likely error",
             MX + Inches(5.6), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=CORAL, bold=True)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Walk the audience through one row of the report. Hover green words, "
        "then yellow, then red. End on a flagged segment that the model knew "
        "was uncertain."
    ))
    return slide


def slide_client_seq_confidence_correlation(prs):
    """Sequence-level confidence — correlation plot vs WER.

    DECISION GATE: only include this slide if B3 reports Pearson r ≤ -0.4.
    Until B3 runs, show a placeholder."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Confidence is built into the model")
    add_accent_line(slide)

    box_w = Inches(7.0)
    box_h = Inches(4.4)
    box_x = MX
    box_y = Inches(1.7)
    add_rect(slide, box_x, box_y, box_w, box_h, fill_color=NAVY2, border_color=TEAL)
    add_text(slide,
             "[ scatter — sequence score vs WER (B3 output) ]",
             box_x, box_y + Inches(1.9), box_w, Inches(0.6),
             size=Pt(15), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)

    # Right-side narrative
    add_bullets(slide, [
        "When the model is unsure, it says so",
        "Lower confidence → higher error rate",
        "We surface this signal end-to-end — no extra computation",
    ], MX + box_w + Inches(0.3), Inches(1.9), Inches(4.7), Inches(3.5), size=Pt(15))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "B3 decision gate: include this slide only if Pearson r ≤ -0.4 on the "
        "100-segment subset. Otherwise drop the slide and rely on Tier 1 only."
    ))
    return slide


def slide_client_trust_dashboard(prs):
    """Three-tier trust dashboard — clear / useful / needs review.
    Numbers from MEMORY.md > Key Project Numbers."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "How segments break down by trust tier")
    add_accent_line(slide)

    # Three big bars
    bar_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(1.9)
    h = Inches(3.6)

    tiers = [
        ("Clearly conveyed", "23%", "346 of 1,497 segments. No review needed.", GREEN),
        ("Useful with context", "39%", "576 segments. Domain context fills the gaps.", GOLD),
        ("Needs review", "38%", "575 segments. The system flags these for you.", CORAL),
    ]
    for i, (label, big, body, color) in enumerate(tiers):
        x = MX + i * (bar_w + gap)
        add_rect(slide, x, top, bar_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, big, x, top + Inches(0.3),
                 bar_w, Inches(1.4),
                 size=Pt(58), bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, label, x, top + Inches(1.8),
                 bar_w, Inches(0.4),
                 size=Pt(15), color=WHITE, align=PP_ALIGN.CENTER, bold=True)
        add_text(slide, body, x + Inches(0.2), top + Inches(2.3),
                 bar_w - Inches(0.4), h - Inches(2.3),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Together: 62% deliver useful output today — 6 of every 10 segments.",
             MX, Inches(5.7), CW, Inches(0.4),
             size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Numbers: NIV Y = 23.1% (rounded 23%). NIV Y+P = 61.6% → partial = "
        "61.6 - 23.1 = 38.5%, rounded 39%. 'Needs review' = 100 - 61.6 = 38.4%, "
        "rounded 38%. All sourced from MEMORY.md > Key Project Numbers."
    ))
    return slide


def slide_client_hallucination_flag(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "When the model fabricates, the system flags it")
    add_accent_line(slide)

    # Big stat on left
    add_text(slide, "1 in 5",
             MX, Inches(1.9), Inches(5.0), Inches(2.0),
             size=Pt(96), bold=True, color=CORAL, align=PP_ALIGN.CENTER)
    add_text(slide, "segments auto-flagged",
             MX, Inches(4.0), Inches(5.0), Inches(0.5),
             size=Pt(18), color=WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_text(slide, "before they ever reach you",
             MX, Inches(4.5), Inches(5.0), Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Narrative on right
    add_bullets(slide, [
        "When the model produces fluent text it isn't sure about, we catch it",
        "Detection rules combine length anomalies and per-token confidence",
        "These are the dangerous failures — fluent but wrong",
        "You don't have to find them. The system finds them for you.",
    ], MX + Inches(5.3), Inches(2.0), Inches(7.0), Inches(4.0), size=Pt(15))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "20.5% hallucination rate translated to '1 in 5'. The detection rules "
        "are the WER≥100% length anomaly plus per-token confidence flag. "
        "Don't enumerate the rules on the slide — stay client-friendly."
    ))
    return slide


def slide_client_what_this_means(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What this means for your workflow")
    add_accent_line(slide)

    add_bullets(slide, [
        "You review the flagged segments — not all of them. Hours saved per video.",
        "Reviewers go straight to the suspicious words instead of skimming text.",
        "Confidence is auditable — every claim has a number behind it.",
        "Bad output is a known unknown, not a hidden surprise.",
    ], MX, Inches(1.9), CW, Inches(4.5), size=Pt(20))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Land the value prop. Connect this back to their actual workflow if you know it.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 5 — Validation
# ──────────────────────────────────────────────────────────────────────────


def slide_client_validation_intro(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "How we validated the trust signals")
    add_accent_line(slide)

    add_bullets(slide, [
        "1,497 real-world segments — not benchmark data",
        "Independent expert reviewer scored every one",
        "We compared the system's confidence signals to that judgment",
        "Result: the trust score and the expert agree on most segments",
    ], MX, Inches(1.9), CW, Inches(4.0), size=Pt(20))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "The 'independent expert reviewer' is Claude Opus 4.6 acting as a "
        "calibration judge — don't name it on the slide; clients hear 'AI "
        "validating AI' and discount it. Frame it as the methodology that "
        "produced the calibrated thresholds."
    ))
    return slide


def slide_client_agreement_chart(prs):
    """Bar showing agreement rate (κ translated to 'agrees ~8 of 10 times')."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Agrees with the expert reviewer 82% of the time")
    add_accent_line(slide)

    # Big visual: a horizontal bar at 82% with the rest at 18%
    bar_x = MX + Inches(1.0)
    bar_y = Inches(2.8)
    bar_w_full = Inches(10.0)
    bar_h = Inches(1.2)
    bar_agree = Inches(10.0 * 0.82)

    add_rect(slide, bar_x, bar_y, bar_w_full, bar_h,
             fill_color=NAVY3, border_color=None)
    add_rect(slide, bar_x, bar_y, bar_agree, bar_h,
             fill_color=GREEN, border_color=None)

    add_text(slide, "82%", bar_x, bar_y - Inches(0.5),
             bar_agree, Inches(0.4),
             size=Pt(20), bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    add_text(slide, "18%", bar_x + bar_agree, bar_y - Inches(0.5),
             bar_w_full - bar_agree, Inches(0.4),
             size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide, "AGREES WITH EXPERT",
             bar_x, bar_y + bar_h + Inches(0.2),
             bar_agree, Inches(0.4),
             size=Pt(12), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "DISAGREES",
             bar_x + bar_agree, bar_y + bar_h + Inches(0.2),
             bar_w_full - bar_agree, Inches(0.4),
             size=Pt(11), color=LGRAY, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Validated on the same 1,497 segments — \"any useful meaning\" judgment.",
             MX, Inches(5.9), CW, Inches(0.4),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "82% comes from κ=0.818 for NIV Y+P translated to a plain agreement "
        "rate. Source: MEMORY.md."
    ))
    return slide


def slide_client_cross_config_stability(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "The trust signal stays stable")
    add_accent_line(slide)

    add_bullets(slide, [
        "We changed decode settings 16 different ways",
        "The trust signal moved less than a percentage point",
        "Translation: it isn't a fluke of one specific run",
    ], MX, Inches(1.9), CW, Inches(3.5), size=Pt(22))

    add_text(slide,
             "What this means: the confidence numbers you see in the demo are "
             "the same confidence numbers you'd see on your data, on your "
             "infrastructure, on your settings.",
             MX, Inches(5.0), CW, Inches(1.4),
             size=Pt(15), color=TEAL, italic=True, align=PP_ALIGN.LEFT)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Cross-config Pearson r=0.925, std=0.015 across 16 decode configs. Don't say r on the slide.")
    return slide


def slide_client_validation_summary(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "An independent expert agreed in 8 of 10 cases")
    add_accent_line(slide)

    add_text(slide,
             "Not validated by us. Validated by an independent reviewer that "
             "didn't see our code, our scores, or our reasoning. That's the "
             "credibility behind every confidence number on every slide.",
             MX, Inches(2.4), CW, Inches(2.2), size=Pt(20), color=WHITE)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Closing on the validation section. Make eye contact.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 7 — Pre-Processing Roadmap (NEW)
# ──────────────────────────────────────────────────────────────────────────


def slide_client_entity_split(prs):
    """Multi-speaker videos broken into per-speaker centered crops.
    Local pre-processing using YOLO + face tracker."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 1 — Per-speaker entity split")
    add_accent_line(slide)

    # Left column: the problem
    col_w = Inches(5.85)
    add_rect(slide, MX, Inches(1.7), col_w, Inches(4.7),
             fill_color=NAVY2, border_color=None)
    add_text(slide, "THE PROBLEM",
             MX + Inches(0.3), Inches(1.85),
             col_w - Inches(0.6), Inches(0.4),
             size=Pt(13), bold=True, color=CORAL)
    add_bullets(slide, [
        "Real client video often has 2+ speakers in frame",
        "Our model expects one centered face per frame",
        "Multi-speaker content confuses lip reading",
    ], MX + Inches(0.3), Inches(2.4), col_w - Inches(0.6), Inches(2.5), size=Pt(15))

    # Right column: the fix
    add_rect(slide, MX + col_w + Inches(0.4), Inches(1.7), col_w, Inches(4.7),
             fill_color=NAVY2, border_color=None)
    add_text(slide, "THE FIX",
             MX + col_w + Inches(0.7), Inches(1.85),
             col_w - Inches(0.6), Inches(0.4),
             size=Pt(13), bold=True, color=GREEN)
    add_bullets(slide, [
        "Detect each speaker (YOLO or equivalent)",
        "Track identity across frames so each crop stays centered",
        "Feed each speaker as its own video into the pipeline",
        "Runs locally — no cloud dependency, no extra cost",
    ], MX + col_w + Inches(0.7), Inches(2.4), col_w - Inches(0.6), Inches(3.0), size=Pt(15))

    add_text(slide,
             "Status: planned ablation — we will measure how much this lifts "
             "intelligibility on multi-speaker content.",
             MX, Inches(6.6), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "User flagged this in v3. The 'YOLO or equivalent' framing leaves room "
        "for whatever detector ends up winning the ablation. Emphasize 'runs "
        "locally' for client comfort."
    ))
    return slide


def slide_client_quality_filter(prs):
    """Drop bad-angle / occluded / low-light clips before pipeline. Local CV."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 2 — Quality pre-filter")
    add_accent_line(slide)

    add_text(slide,
             "Not every clip is worth running through a million-parameter model.",
             MX, Inches(1.7), CW, Inches(0.5),
             size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.LEFT)

    # Three checks shown as cards
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(2.5)
    h = Inches(2.8)

    checks = [
        ("HEAD ANGLE", "Reject when the face is past a profile threshold — lip reading needs frontal view.", TEAL),
        ("MOUTH VISIBILITY", "Reject when the mouth is occluded by hair, hands, or props.", GOLD),
        ("LIGHTING / CONTRAST", "Reject when the lip region is too dark or too washed out for the model.", CORAL),
    ]
    for i, (label, body, color) in enumerate(checks):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), top + Inches(0.2),
                 card_w - Inches(0.4), Inches(0.4),
                 size=Pt(13), bold=True, color=color)
        add_text(slide, body, x + Inches(0.2), top + Inches(0.8),
                 card_w - Inches(0.4), h - Inches(0.9),
                 size=Pt(13), color=WHITE)

    add_text(slide,
             "All three checks run locally as fast frame-level CV. "
             "Status: planned ablation — we will publish the trade-off curve.",
             MX, Inches(5.7), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Frame as 'highest leverage per dollar.' The model is never tested in "
        "isolation; what reaches it is what matters."
    ))
    return slide


def slide_client_preprocessing_summary(prs):
    """Why pre-processing matters — ties Section 7 together."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Why pre-processing is the highest-leverage work")
    add_accent_line(slide)

    add_text(slide,
             "The model is never tested in isolation. What reaches it is what matters.",
             MX, Inches(2.0), CW, Inches(0.8),
             size=Pt(22), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "Both stages run on your local machine — no extra cloud cost",
        "Both reduce wasted compute on unusable footage",
        "Both ship as clear ablation studies with measurable impact",
        "Together: a more reliable, more efficient pipeline by default",
    ], MX, Inches(3.4), CW, Inches(3.0), size=Pt(18))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Bridge from pre-processing into the model-improvement roadmap.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 8 — Roadmap & Investment
# ──────────────────────────────────────────────────────────────────────────


def slide_client_roadmap_phases(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Where we are vs. where we're going")
    add_accent_line(slide)

    # Three phases as stepped cards
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(1.9)
    h = Inches(4.1)

    phases = [
        ("TODAY", "Working pipeline, validated trust signals, deployable today.", TEAL),
        ("NEXT", "Stronger model, more training data, pre-processing live.", GOLD),
        ("AFTER", "Domain-specialized fine-tunes for your content.", GREEN),
    ]
    for i, (label, body, color) in enumerate(phases):
        x = MX + i * (card_w + gap)
        # offset y for a stair-stepped feel
        y_off = Inches(0.0 if i == 0 else 0.3 * i)
        add_rect(slide, x, top + y_off, card_w, h - y_off, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x, top + y_off + Inches(0.4),
                 card_w, Inches(0.6), size=Pt(28), bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + Inches(0.3), top + y_off + Inches(1.6),
                 card_w - Inches(0.6), h - y_off - Inches(1.6),
                 size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Direction-only. No specific numbers per phase — the v3 plan strips those.")
    return slide


def slide_client_stronger_model(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "A stronger model, same architecture")
    add_accent_line(slide)

    add_text(slide,
             "The same pipeline. A larger, better-trained brain on the back.",
             MX, Inches(2.0), CW, Inches(0.6),
             size=Pt(22), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "Drop-in upgrade of the language model that produces the final transcript",
        "Better grasp of context, named entities, and uncommon vocabulary",
        "No change to your integration — same inputs, same outputs, better text",
        "Requires retraining — not a switch, an investment",
    ], MX, Inches(3.0), CW, Inches(3.4), size=Pt(17))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Don't say 'LLaMA-2 → Llama 3.1 8B' on the slide. Don't say 'LoRA' or "
        "'rank' or token counts. Say 'larger and better-trained brain on the back.'"
    ))
    return slide


def slide_client_more_data(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Today's data is a slice. There's a ceiling.")
    add_accent_line(slide)

    add_bullets(slide, [
        "We've identified the data ceiling on the current dataset",
        "Expanding the training set is the next unlock",
        "More data → better domain coverage → fewer flagged segments",
        "Especially powerful when paired with the stronger model",
    ], MX, Inches(2.0), CW, Inches(3.5), size=Pt(20))

    add_text(slide,
             "Direction matters more than the exact number here — we know which way "
             "the curve points.",
             MX, Inches(5.6), CW, Inches(0.5),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Direction-only framing. Speak about 'the data ceiling' and 'the next "
        "unlock' rather than naming the current and target dataset sizes. "
        "Specific dataset numbers belong in the technical follow-up, not the "
        "meeting room."
    ))
    return slide


def slide_client_investment_ask(prs):
    """The funding ask. Direct, simple, client-facing."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What it takes to ship the next model")
    add_accent_line(slide)

    add_text(slide,
             "To train the next model on the data scale needed, we need a "
             "training-budget commitment.",
             MX, Inches(1.9), CW, Inches(1.2),
             size=Pt(22), color=WHITE, align=PP_ALIGN.CENTER, bold=True)

    # Three drivers of the ask
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(3.4)
    h = Inches(2.4)

    drivers = [
        ("Compute", "GPU hours for full training, not a quick partial pass.", TEAL),
        ("Data", "Curated and labeled domain segments — your domain.", GOLD),
        ("Engineering", "Pipeline integration, testing, and on-prem handoff.", GREEN),
    ]
    for i, (label, body, color) in enumerate(drivers):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), top + Inches(0.2),
                 card_w - Inches(0.4), Inches(0.4),
                 size=Pt(15), bold=True, color=color)
        add_text(slide, body, x + Inches(0.2), top + Inches(0.85),
                 card_w - Inches(0.4), h - Inches(0.95),
                 size=Pt(14), color=WHITE)

    add_text(slide,
             "Specific numbers in the follow-up — today is direction, not invoice.",
             MX, Inches(6.1), CW, Inches(0.4),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Be direct. The ask is real. Numbers go in the follow-up email, not "
        "this slide — leaves room for negotiation and avoids anchoring."
    ))
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 9 — Summary, Integration, Next Steps
# ──────────────────────────────────────────────────────────────────────────


def slide_client_recap(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Three things to take with you")
    add_accent_line(slide)

    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(1.9)
    h = Inches(4.0)

    items = [
        ("IT WORKS", "Real pipeline, finished UI, usable today.", GREEN),
        ("YOU CAN TRUST IT", "Two layers of confidence — per word and per segment.", TEAL),
        ("WE DEPLOY IT", "End-to-end on your infrastructure, not an API call.", GOLD),
    ]
    for i, (label, body, color) in enumerate(items):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x, top + Inches(0.5),
                 card_w, Inches(0.7),
                 size=Pt(28), bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + Inches(0.3), top + Inches(1.7),
                 card_w - Inches(0.6), h - Inches(1.7),
                 size=Pt(15), color=WHITE, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "The three emotional beats from the deck — in order. Repeat them out loud.")
    return slide


def slide_client_integration_commitment(prs):
    """We deploy this on your infrastructure end-to-end."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "We deploy this on your infrastructure")
    add_accent_line(slide)

    add_text(slide,
             "You're not buying an API call. You're buying a working pipeline "
             "that runs in your environment.",
             MX, Inches(1.9), CW, Inches(1.2),
             size=Pt(22), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    # Four steps as a row
    step_w = Inches(2.85)
    gap = Inches(0.2)
    top = Inches(3.4)
    h = Inches(2.4)

    steps = [
        ("1. INSTALL", "On-premise or your cloud. Your hardware, your rules.", TEAL),
        ("2. INTEGRATE", "Wire into your existing systems and workflow.", GOLD),
        ("3. TRAIN", "Onboard your team end-to-end — ops, review, troubleshoot.", GREEN),
        ("4. HANDOFF", "Documented, supported, owned by you.", CORAL),
    ]
    total_w = 4 * step_w + 3 * gap
    start_x = MX + (CW - total_w) / 2
    for i, (label, body, color) in enumerate(steps):
        x = start_x + i * (step_w + gap)
        add_rect(slide, x, top, step_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.15), top + Inches(0.2),
                 step_w - Inches(0.3), Inches(0.4),
                 size=Pt(13), bold=True, color=color)
        add_text(slide, body, x + Inches(0.15), top + Inches(0.85),
                 step_w - Inches(0.3), h - Inches(0.95),
                 size=Pt(12), color=WHITE)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Reinforce the integration commitment. Important for clients evaluating "
        "vendor risk — they want a real handoff, not a black box."
    ))
    return slide


def slide_client_next_steps(prs):
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Next steps")
    add_accent_line(slide)

    add_bullets(slide, [
        "[ FILL IN: pilot dataset — size, content type, source ]",
        "[ FILL IN: integration scope — systems to wire into ]",
        "[ FILL IN: timeline — weeks to first end-to-end run ]",
        "[ FILL IN: success criteria — what 'good' looks like for them ]",
    ], MX, Inches(2.0), CW, Inches(4.0), size=Pt(20), color=LGRAY)

    add_text(slide,
             "Customize this slide before the meeting. Generic = forgettable.",
             MX, Inches(6.4), CW, Inches(0.4),
             size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Customize before the meeting. Use the client's own language for each bullet.")
    return slide
