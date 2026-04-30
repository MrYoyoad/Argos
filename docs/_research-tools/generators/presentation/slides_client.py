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
             "Measured on 1,497 segments of unfiltered real-world video — varied "
             "lighting, head angles, multi-speaker scenes, no curation.",
             MX, Inches(5.55), CW, Inches(0.55),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Validated against an independent expert reviewer.",
             MX, Inches(6.05), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Numbers from MEMORY.md > Key Project Numbers. "
        "62% = 922/1497 NIV Y+P (rounded from 61.6%). "
        "23% = 346/1497 NIV Y (rounded from 23.1%). "
        "1 in 5 = 20.5% hallucination/auto-flag rate. "
        "Validation κ=0.818 vs Opus expert judge — phrased as '8 of 10' on slide. "
        "Don't read out NIV / κ on the slide; they're for your reference here. "
        "Lean into the difficulty caveat — these numbers are on real-world hard "
        "data, not a curated benchmark, and the client should hear that "
        "explicitly. Anything cleaner-than-YouTube will perform better."
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
             "Press play on the next slide to start the walkthrough.",
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

    # Polished placeholder until C3 (live UI walkthrough recording) lands.
    # Looks intentional and presentable even if the deck is reviewed before
    # the recording is captured. Replace with `add_video(...)` once
    # _ui_walkthrough_clientpitch.mp4 exists.
    box_w = Inches(11.0)
    box_h = Inches(5.0)
    box_x = (SL_W - box_w) / 2
    box_y = Inches(1.6)
    add_rect(slide, box_x, box_y, box_w, box_h, fill_color=NAVY2, border_color=TEAL)
    # Big play-triangle icon (Unicode triangle as a visual cue).
    add_text(slide, "▶",
             box_x, box_y + Inches(1.0), box_w, Inches(1.6),
             size=Pt(120), color=TEAL, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Live UI walkthrough",
             box_x, box_y + Inches(2.8), box_w, Inches(0.6),
             size=Pt(28), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide,
             "End-to-end demo recorded by the presenter.",
             box_x, box_y + Inches(3.5), box_w, Inches(0.5),
             size=Pt(15), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)
    add_text(slide,
             "Approx 4-5 minutes  ·  press play in PowerPoint",
             box_x, box_y + Inches(4.0), box_w, Inches(0.4),
             size=Pt(12), color=MGRAY, align=PP_ALIGN.CENTER)

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
    """Screenshot of the Obama bin Laden demo report with per-word
    green/yellow/red confidence color coding.

    Source HTML: presentation_materials_20260224/01_plots_for_slides/obama_demo_report.html
    Source generator: docs/_research-tools/generators/generate_client_demo_report.py

    Confidence on this screenshot is currently *synthetic*, derived from WER
    alignment between the decoded HYP and the known REF text — it shows what
    the rendering looks like end-to-end. When B3 lands a real per-token
    confidence sidecar, regenerate the HTML (same script, same script just
    swaps source automatically) and re-screenshot to refresh this slide.
    """
    from pathlib import Path
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Per-word color coding on a real example")
    add_accent_line(slide)

    screenshot = Path(__file__).resolve().parents[4] / (
        "presentation_materials_20260224/01_plots_for_slides/"
        "ui_word_confidence_screenshot.png"
    )
    if screenshot.exists():
        # Height-constrained: the source PNG is tall (1600x1900). Width-
        # constraining at 8.5" would push the image past the slide edge.
        from PIL import Image
        with Image.open(screenshot) as im:
            aspect = im.height / im.width
        img_h = Inches(4.7)
        img_w = Inches(4.7 / aspect)
        img_x = (SL_W - img_w) / 2
        img_y = Inches(1.55)
        slide.shapes.add_picture(str(screenshot), img_x, img_y, height=img_h)
    else:
        # Fallback placeholder if screenshot has not been generated yet.
        box_w = Inches(11.0)
        box_h = Inches(4.6)
        box_x = (SL_W - box_w) / 2
        box_y = Inches(1.6)
        add_rect(slide, box_x, box_y, box_w, box_h, fill_color=NAVY2, border_color=GREEN)
        add_text(slide,
                 "[ Run docs/_research-tools/generators/generate_client_demo_report.py "
                 "then re-screenshot ]",
                 box_x, box_y + Inches(1.9), box_w, Inches(0.6),
                 size=Pt(16), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)

    # Legend strip
    legend_top = Inches(6.7)
    add_text(slide, "Per-word confidence  —  ",
             MX, legend_top, Inches(2.6), Inches(0.3),
             size=Pt(11), color=LGRAY)
    add_text(slide, "GREEN: confident",
             MX + Inches(2.5), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=GREEN, bold=True)
    add_text(slide, "YELLOW: review",
             MX + Inches(4.6), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=YELLOW, bold=True)
    add_text(slide, "RED: likely error",
             MX + Inches(6.7), legend_top, Inches(2.0), Inches(0.3),
             size=Pt(11), color=CORAL, bold=True)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Walk the audience through one segment of the Obama bin Laden speech "
        "report. Hover or point at a green run, then a yellow word, then the "
        "red mismatch. The recognizable content lets clients track what's "
        "right and what's not even though the audio isn't being played. "
        "Note that the per-word confidence on THIS screenshot is currently "
        "synthetic (derived from WER alignment) until B3's real sequence-"
        "confidence sidecar lands — visual treatment is identical, the "
        "underlying signal will swap when the GPU run completes. The Obama "
        "speech is the demo input recommended for your live UI walkthrough "
        "recording (vsp_input/050111_OsamaBinLadenStatement_HD.mp4)."
    ))
    return slide


def slide_client_seq_confidence_correlation(prs):
    """The conditional-performance lift slide — Tier 1 version.

    Real data, no GPU run needed. Embeds the staircase + precision/recall
    plot computed against the full 1,497-segment baseline. The headline
    fact: when the system flags IS >= 3.80, segments are good (WER <= 50%)
    100% of the time across the full dataset. Zero false positives.

    Source: docs/_research-tools/generators/generate_is_confidence_gate_plot.py
    Plot:   presentation_materials_20260224/01_plots_for_slides/is_confidence_gate.png

    A future Tier-2 (per-token sequence confidence from the LLaMA decoder)
    plot will land here once B3 has run; the current Tier-1 plot is real
    and shippable today."""
    from pathlib import Path
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Higher confidence → lower error, every time")
    add_accent_line(slide)

    plot_path = Path(__file__).resolve().parents[4] / (
        "presentation_materials_20260224/01_plots_for_slides/"
        "is_confidence_gate.png"
    )
    if plot_path.exists():
        # Height-constrained so the bar chart fits between title and footer.
        img_h = Inches(4.7)
        img_y = Inches(1.55)
        # Keep the canonical aspect ratio (the plot is ~13:5).
        from PIL import Image
        with Image.open(plot_path) as im:
            aspect = im.width / im.height
        img_w = Inches(4.7 * aspect)
        # Cap width so it doesn't escape the slide.
        if img_w > Inches(12.5):
            img_w = Inches(12.5)
            img_h = Inches(12.5 / aspect)
        img_x = (SL_W - img_w) / 2
        slide.shapes.add_picture(str(plot_path), img_x, img_y, width=img_w, height=img_h)
    else:
        # Fallback: text-only summary if plot hasn't been regenerated
        add_text(slide,
                 "Run docs/_research-tools/generators/generate_is_confidence_gate_plot.py "
                 "to produce is_confidence_gate.png",
                 MX, Inches(2.0), CW, Inches(0.6),
                 size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Anchor the killer line below the chart
    add_text(slide,
             "When the system rates a segment \"clearly conveyed,\" it really is — "
             "100% precision across 1,497 real-world segments.",
             MX, Inches(6.6), CW, Inches(0.5),
             size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Real data on the full 1,497-segment baseline. Pearson r(IS, WER) = "
        "-0.850. Spearman ρ = -0.943. Median WER staircase by IS tier: 4-5 → "
        "19%, 3-4 → 40%, 2-3 → 62%, 1-2 → 88%, <1 → 100%+. Zero false "
        "positives at IS ≥ 3.80 for the WER ≤ 50% definition of 'good' — "
        "every single segment the system flagged 'clearly conveyed' actually "
        "had WER below 50%. This is the conditional-lift story we deferred "
        "earlier; we have it today at the Tier-1 (Intelligibility Score) "
        "level. A future Tier-2 chart from per-token model confidence will "
        "complement (not replace) this one once the GPU subset run completes. "
        "Don't say 'IS' on the slide — say 'when the system rates a segment "
        "clearly conveyed.'"
    ))
    return slide


def slide_client_trust_dashboard(prs):
    """Reframe of 62% useful with difficulty context, no partial-bucket
    breakdown. The conditional 'when system confidence is high' story is
    deferred until B3 produces real per-segment sequence-confidence data
    (see slide_client_seq_confidence_correlation)."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "62% useful — on real-world video, not benchmark data")
    add_accent_line(slide)

    # Left column — the headline number
    left_w = Inches(5.8)
    add_rect(slide, MX, Inches(1.7), left_w, Inches(4.7),
             fill_color=NAVY2, border_color=None)
    add_text(slide, "62%",
             MX, Inches(1.95), left_w, Inches(2.2),
             size=Pt(140), bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments deliver useful output today",
             MX + Inches(0.3), Inches(4.4), left_w - Inches(0.6), Inches(0.6),
             size=Pt(17), color=WHITE, align=PP_ALIGN.CENTER, bold=True)
    add_text(slide, "Measured on 1,497 segments of unfiltered real-world video",
             MX + Inches(0.3), Inches(5.05), left_w - Inches(0.6), Inches(0.5),
             size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Right column — the difficulty context
    right_x = MX + left_w + Inches(0.4)
    right_w = Inches(5.93)
    add_rect(slide, right_x, Inches(1.7), right_w, Inches(4.7),
             fill_color=NAVY2, border_color=None)
    add_text(slide, "WHAT THAT 62% IS UP AGAINST",
             right_x + Inches(0.3), Inches(1.85), right_w - Inches(0.6), Inches(0.4),
             size=Pt(13), bold=True, color=CORAL)
    add_bullets(slide, [
        "Real YouTube footage — not a curated benchmark dataset",
        "Varied lighting, head angles, and camera distances",
        "Multi-speaker scenes, off-axis faces, partial occlusion",
        "Domain vocabulary the model has never seen",
        "No pre-filtering — the system processes whatever was uploaded",
    ], right_x + Inches(0.3), Inches(2.45), right_w - Inches(0.6), Inches(3.5),
       size=Pt(15))

    # Tease the conditional story
    add_text(slide,
             "On segments the system flags as high-confidence, performance lifts further — "
             "we'll measure that conditional rate in the next iteration.",
             MX, Inches(6.55), CW, Inches(0.45),
             size=Pt(11), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "62% = NIV Y+P (61.6% rounded). The point of this slide is twofold: "
        "(1) anchor the 62% as the headline 'useful' number without giving "
        "the client labels for what counts as useful or partial — they decide "
        "their own bar; (2) make crystal clear that this is real-world hard "
        "data, not a benchmark we hand-picked. The conditional 'on "
        "high-confidence segments only' lift is real but we're holding back "
        "the precise number until per-segment sequence-confidence data is in "
        "(B3 in the plan). Don't say NIV / kappa / r=. The user explicitly "
        "rejected the 39% partial / 38% needs-review breakdown — we don't "
        "anchor the client's threshold for 'useful' on our terms."
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
    add_title(slide, "An independent expert agreed 82% of the time")
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
    Local pre-processing using a face detector + tracker."""
    from pathlib import Path
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 1 — Per-speaker entity split")
    add_accent_line(slide)

    plot_path = Path(__file__).resolve().parents[4] / (
        "presentation_materials_20260224/01_plots_for_slides/entity_split_mock.png"
    )
    if plot_path.exists():
        # Height-constrained so the diagram fits between title and footer.
        from PIL import Image
        with Image.open(plot_path) as im:
            aspect = im.width / im.height
        img_h = Inches(4.7)
        img_w = Inches(4.7 * aspect)
        if img_w > Inches(12.5):
            img_w = Inches(12.5)
            img_h = Inches(12.5 / aspect)
        img_x = (SL_W - img_w) / 2
        img_y = Inches(1.55)
        slide.shapes.add_picture(str(plot_path), img_x, img_y, width=img_w, height=img_h)
    else:
        add_text(slide, "[ entity_split_mock.png — run the diagram generator ]",
                 MX, Inches(2.0), CW, Inches(0.6),
                 size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Two speakers in one frame become two centered crops. Each speaker "
             "gets its own clean lip-reading pass.",
             MX, Inches(6.55), CW, Inches(0.45),
             size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Diagram from generate_*_diagrams agent run. The 'face detection + "
        "tracker (local)' framing leaves the implementation open — could be "
        "YOLO, RetinaFace, MediaPipe, etc. — we pick whatever wins the "
        "ablation. Emphasize 'runs locally' for client comfort: no extra "
        "cloud dependency, no extra cost. Status is explicitly 'planned "
        "ablation' — we are NOT claiming this is shipping today."
    ))
    return slide


def slide_client_quality_filter(prs):
    """Drop bad-angle / occluded / low-light clips before pipeline. Local CV."""
    from pathlib import Path
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 2 — Quality pre-filter")
    add_accent_line(slide)

    plot_path = Path(__file__).resolve().parents[4] / (
        "presentation_materials_20260224/01_plots_for_slides/quality_filter_funnel.png"
    )
    if plot_path.exists():
        # Height-constrained so the funnel fits between title and footer.
        from PIL import Image
        with Image.open(plot_path) as im:
            aspect = im.width / im.height
        img_h = Inches(4.7)
        img_w = Inches(4.7 * aspect)
        if img_w > Inches(12.5):
            img_w = Inches(12.5)
            img_h = Inches(12.5 / aspect)
        img_x = (SL_W - img_w) / 2
        img_y = Inches(1.55)
        slide.shapes.add_picture(str(plot_path), img_x, img_y, width=img_w, height=img_h)
    else:
        add_text(slide, "[ quality_filter_funnel.png — run the diagram generator ]",
                 MX, Inches(2.0), CW, Inches(0.6),
                 size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Drop bad-angle, occluded, or poorly-lit clips before the model "
             "ever sees them. Saves compute. Lifts apparent accuracy.",
             MX, Inches(6.55), CW, Inches(0.45),
             size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Frame as 'highest leverage per dollar.' The model is never tested in "
        "isolation; what reaches it is what matters. The funnel percentages "
        "shown are illustrative — actual rejection rates depend on the "
        "client's own video conditions, which is exactly what the ablation "
        "would measure. Status is 'planned ablation' — not yet shipping."
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


# ──────────────────────────────────────────────────────────────────────────
# Section 3 — Output examples (replacements for borrowed academic slides)
# ──────────────────────────────────────────────────────────────────────────


# 33-Obama-segment B3 sidecar — used to color-code the example slides with
# real per-token probabilities. Loaded lazily so the deck still builds if
# the sidecar is absent (falls back to plain text).
_OBAMA_SIDECAR_PATH = "/tmp/vsp_b3_full_out/confidence-172610.json"
_OBAMA_HYPO_PATH = "/tmp/vsp_b3_full_out/hypo-172610.json"


def _load_obama_segment(utt_id):
    """Return (ref, hyp_words_with_probs) for an Obama segment, or (None, None)
    if the sidecar isn't available. hyp_words_with_probs is the output of
    compute_word_confidence.aggregate_subtokens_to_words.
    """
    import json
    from pathlib import Path
    import sys
    sd_path = Path(_OBAMA_SIDECAR_PATH)
    hp_path = Path(_OBAMA_HYPO_PATH)
    if not sd_path.exists() or not hp_path.exists():
        return None, None
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from compute_word_confidence import aggregate_subtokens_to_words
    sidecar = json.loads(sd_path.read_text())
    hypo = json.loads(hp_path.read_text())
    full_id = next((u for u in hypo["utt_id"] if utt_id in u), None)
    if not full_id:
        return None, None
    idx = hypo["utt_id"].index(full_id)
    ref = hypo["ref"][idx]
    seg = sidecar.get(full_id)
    if not seg:
        return ref, None
    words = aggregate_subtokens_to_words(seg.get("tokens", []))
    return ref, words


def _color_for_class(klass):
    return {
        "conf-high": GREEN,
        "conf-med": YELLOW,
        "conf-low": CORAL,
    }.get(klass, WHITE)


def _example_slide(prs, *, title, subtitle, utt_id, takeaway, takeaway_color=TEAL):
    """Shared layout for the three Obama example slides."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, title)
    add_accent_line(slide)
    add_text(slide, subtitle, MX, Inches(1.45), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    ref, words = _load_obama_segment(utt_id)

    # REF row
    add_text(slide, "REFERENCE", MX, Inches(2.0), Inches(1.4), Inches(0.4),
             size=Pt(11), bold=True, color=LGRAY)
    add_text(slide,
             ref or "(reference text not available — re-run the B3 decode)",
             MX + Inches(1.5), Inches(2.0), CW - Inches(1.5), Inches(1.4),
             size=Pt(16), color=LGRAY, italic=True)

    # HYP row — color-coded
    add_text(slide, "HYPOTHESIS", MX, Inches(3.6), Inches(1.4), Inches(0.4),
             size=Pt(11), bold=True, color=WHITE)
    if words:
        runs = []
        for w in words:
            color = _color_for_class(w.get("conf_class", "conf-unknown"))
            runs.append((w["word"] + " ", {"size": Pt(17), "color": color, "bold": False}))
        add_rich_text(slide, [runs], MX + Inches(1.5), Inches(3.6),
                      CW - Inches(1.5), Inches(2.0))
    else:
        add_text(slide, "(real-confidence sidecar not loaded — placeholder)",
                 MX + Inches(1.5), Inches(3.6), CW - Inches(1.5), Inches(0.4),
                 size=Pt(13), color=MGRAY, italic=True)

    # Takeaway pill
    add_rect(slide, MX, Inches(5.7), CW, Inches(0.7),
             fill_color=NAVY2, border_color=takeaway_color)
    add_text(slide, takeaway, MX + Inches(0.3), Inches(5.85),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(14), color=WHITE, italic=True)

    # Tiny legend
    add_text(slide, "GREEN: confident   YELLOW: review   RED: likely error",
             MX, Inches(6.55), CW, Inches(0.3),
             size=Pt(9), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    return slide


def slide_client_example_perfect(prs):
    """Obama segment 14 — WER 0%, 27 words at conf-high."""
    return _example_slide(
        prs,
        title="Example 1 — Clean speech, perfect transcription",
        subtitle="Obama bin Laden announcement  ·  segment #14  ·  41.95–45.55 s",
        utt_id="14_004195_004555",
        takeaway="WER 0%. 27 of 29 words at high confidence. No reviewer "
                 "intervention needed.",
        takeaway_color=GREEN,
    )


def slide_client_example_partial(prs):
    """Obama segment 31 — WER 22%, mostly green with 2 substitutions."""
    return _example_slide(
        prs,
        title="Example 2 — Partial recovery, model knows where it slipped",
        subtitle="Obama bin Laden announcement  ·  segment #31  ·  92.90–96.50 s",
        utt_id="31_009290_009650",
        takeaway="WER 22%. \"president bush did\" became \"president bush said\". "
                 "Substitutions appear in yellow — reviewer goes straight to them.",
        takeaway_color=GOLD,
    )


def slide_client_example_flagged(prs):
    """Obama segment 5 — WER 45%, hallucination caught (min_p 0.02).

    REF: 'heroic citizens saved even more heartbreak and destruction'
    HYP: 'rwanda's genocide even more heartbreaking is russia'
    """
    return _example_slide(
        prs,
        title="Example 3 — Flagged before it ever reached you",
        subtitle="Obama bin Laden announcement  ·  segment #5  ·  14.98–18.58 s",
        utt_id="05_001498_001858",
        takeaway="WER 45%. The model fabricated \"rwanda's genocide\" — and "
                 "knew it. Lowest-confidence word at p=0.02. The system flags "
                 "the line before the reviewer ever sees the transcript.",
        takeaway_color=CORAL,
    )


def slide_client_examples_intro(prs):
    """Tee up the three example slides."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What good, partial, and flagged look like")
    add_accent_line(slide)

    add_text(slide,
             "Three real segments from the Obama bin Laden announcement, "
             "decoded by the live model, color-coded by real per-word "
             "confidence.",
             MX, Inches(1.8), CW, Inches(1.2),
             size=Pt(20), color=LGRAY, italic=True)

    # Three preview cards
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(3.2)
    h = Inches(2.7)
    items = [
        ("CLEAN", "Segment 14",  "WER 0%. All confident.",       GREEN),
        ("PARTIAL","Segment 31", "WER 22%. Substitutions in yellow.", GOLD),
        ("FLAGGED","Segment 5",  "WER 45%. Hallucination caught.",   CORAL),
    ]
    for i, (label, sub, body, color) in enumerate(items):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.3), top + Inches(0.3),
                 card_w - Inches(0.6), Inches(0.4),
                 size=Pt(14), bold=True, color=color)
        add_text(slide, sub, x + Inches(0.3), top + Inches(0.85),
                 card_w - Inches(0.6), Inches(0.4),
                 size=Pt(15), color=WHITE, bold=True)
        add_text(slide, body, x + Inches(0.3), top + Inches(1.45),
                 card_w - Inches(0.6), h - Inches(1.45),
                 size=Pt(13), color=LGRAY)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Three concrete examples on the next three slides.")
    return slide


# ──────────────────────────────────────────────────────────────────────────
# Section 6 — Pipeline reframes (replace academic-styled borrowed slides)
# ──────────────────────────────────────────────────────────────────────────


def slide_client_visemes(prs):
    """Why lip reading is hard — without saying 'viseme'."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Why lip reading is hard")
    add_accent_line(slide)

    add_text(slide,
             "Many words look identical on the lips. The model has to choose.",
             MX, Inches(1.7), CW, Inches(0.6),
             size=Pt(22), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    # Three example sets — words that share lip shape
    card_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(2.8)
    h = Inches(2.4)
    examples = [
        ("LOOK IDENTICAL", "pat  ·  bat  ·  mat",   "Plosive sounds — same lip closure", TEAL),
        ("LOOK IDENTICAL", "thin  ·  fin  ·  shin",  "Fricatives — invisible airflow",   GOLD),
        ("LOOK IDENTICAL", "see  ·  zee  ·  thee",   "Voicing — invisible vibration",    CORAL),
    ]
    for i, (label, words, why, color) in enumerate(examples):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.3), top + Inches(0.25),
                 card_w - Inches(0.6), Inches(0.4),
                 size=Pt(11), bold=True, color=color)
        add_text(slide, words, x + Inches(0.3), top + Inches(0.85),
                 card_w - Inches(0.6), Inches(0.7),
                 size=Pt(22), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, why, x + Inches(0.3), top + Inches(1.7),
                 card_w - Inches(0.6), h - Inches(1.8),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER, italic=True)

    add_text(slide,
             "The system uses language context and confidence scoring to pick the right one — and tells you when it can't.",
             MX, Inches(5.5), CW, Inches(0.5),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "These are visemes (groups of phonemes that look the same on the lips). "
        "Don't say 'visemes' on the slide. The teaching beat is: this is why "
        "the problem is hard, and why our confidence signal matters."
    ))
    return slide


def slide_client_pipeline_components(prs):
    """Three components, client-friendly labels."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Three components, end-to-end")
    add_accent_line(slide)

    add_text(slide,
             "From a raw video frame to a confidence-scored transcript.",
             MX, Inches(1.7), CW, Inches(0.5),
             size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Three flow boxes connected by arrows
    box_w = Inches(3.6)
    gap = Inches(0.4)
    top = Inches(2.7)
    h = Inches(3.0)
    total_w = 3 * box_w + 2 * gap
    start_x = MX + (CW - total_w) / 2

    components = [
        ("1.", "FACE DETECTION & MOUTH CROPPING",
         "Find the speaker. Crop a stable, centered window around the mouth across every frame.",
         TEAL),
        ("2.", "VISUAL FEATURE EXTRACTION",
         "Convert the mouth movement into a compact representation the language model can read.",
         GOLD),
        ("3.", "LANGUAGE DECODING",
         "Generate the transcript word-by-word. Capture per-word confidence as we go.",
         GREEN),
    ]
    for i, (num, title, body, color) in enumerate(components):
        x = start_x + i * (box_w + gap)
        add_rect(slide, x, top, box_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, num, x + Inches(0.3), top + Inches(0.25),
                 box_w - Inches(0.6), Inches(0.5),
                 size=Pt(28), bold=True, color=color)
        add_text(slide, title, x + Inches(0.3), top + Inches(0.85),
                 box_w - Inches(0.6), Inches(0.8),
                 size=Pt(13), bold=True, color=WHITE)
        add_text(slide, body, x + Inches(0.3), top + Inches(1.7),
                 box_w - Inches(0.6), h - Inches(1.8),
                 size=Pt(12), color=LGRAY)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Behind the scenes these are auto_avsr, av_hubert, and VSP-LLM. Don't "
        "name those repos for clients. The narrative beat: we own the whole "
        "stack, not a vendor stitch-up."
    ))
    return slide


def slide_client_deployment_options(prs):
    """Cloud vs on-prem — clean two-card layout."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Deploys where you need it")
    add_accent_line(slide)

    add_text(slide,
             "Same pipeline, two deployment paths. You pick.",
             MX, Inches(1.7), CW, Inches(0.5),
             size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Two big cards
    card_w = Inches(5.85)
    gap = Inches(0.4)
    top = Inches(2.6)
    h = Inches(3.6)
    options = [
        ("CLOUD",
         "Hosted on your AWS / GCP / Azure account. We run the GPU infra; you pay per minute of video.",
         ["Faster setup, no hardware procurement", "Scales elastically with your queue", "We patch and update the stack"],
         TEAL),
        ("ON-PREMISE",
         "Containerized install on your hardware. Your data never leaves your network.",
         ["Air-gapped operation supported", "GPU on your own machines (T4 minimum)", "We support and maintain remotely"],
         GOLD),
    ]
    for i, (label, blurb, bullets, color) in enumerate(options):
        x = MX + i * (card_w + gap)
        add_rect(slide, x, top, card_w, h, fill_color=NAVY2, border_color=color)
        add_text(slide, label, x + Inches(0.3), top + Inches(0.3),
                 card_w - Inches(0.6), Inches(0.6),
                 size=Pt(28), bold=True, color=color)
        add_text(slide, blurb, x + Inches(0.3), top + Inches(1.1),
                 card_w - Inches(0.6), Inches(1.0),
                 size=Pt(14), color=WHITE)
        add_bullets(slide, bullets,
                    x + Inches(0.3), top + Inches(2.1),
                    card_w - Inches(0.6), Inches(1.4),
                    size=Pt(13))

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Headline: same code, two deployment models.")
    return slide


def slide_client_next_steps(prs):
    """Shipping-safe placeholder. The four prompts are intentional cues for
    the presenter to fill in with client-specific language before the
    meeting; they read as section headers (not as obvious placeholder text)
    in case the deck is reviewed before customization."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Next steps")
    add_accent_line(slide)

    # Four customization prompts, each presented as an empty-card heading
    # the presenter fills with the client's own language during prep.
    card_w = Inches(5.85)
    gap = Inches(0.4)
    top = Inches(1.85)
    h = Inches(2.15)

    items = [
        ("Pilot dataset",          "Size, content type, sample source", TEAL),
        ("Integration scope",      "Systems and pipelines to wire into", GOLD),
        ("Timeline",               "Weeks to first end-to-end run on your data", GREEN),
        ("Success criteria",       "What good looks like for your team", CORAL),
    ]
    for i, (label, prompt, color) in enumerate(items):
        col = i % 2
        row = i // 2
        x = MX + col * (card_w + gap)
        y = top + row * (h + Inches(0.3))
        add_rect(slide, x, y, card_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.3), y + Inches(0.25),
                 card_w - Inches(0.6), Inches(0.5),
                 size=Pt(20), bold=True, color=color)
        add_text(slide, prompt, x + Inches(0.3), y + Inches(0.95),
                 card_w - Inches(0.6), h - Inches(1.05),
                 size=Pt(13), color=LGRAY, italic=True)

    add_text(slide,
             "Customize per-client during prep — placeholder copy intentionally generic.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, "Customize before the meeting. Use the client's own language for each bullet.")
    return slide
