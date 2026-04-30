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
    set_notes, add_video_poster,
)


# ──────────────────────────────────────────────────────────────────────────
# Section 1 — "What This Is"
# ──────────────────────────────────────────────────────────────────────────


def slide_client_title(prs):
    """Title slide. Client name + date + presenter + tagline.

    Round-5 addition: large centered peacock above the title to match the
    academic deck's cover-page brand mark.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1

    # Centered peacock — large brand mark above the title text.
    peacock_h = Inches(1.5)
    peacock_w = Inches(1.5)
    peacock_x = (SL_W - peacock_w) / 2
    add_image(slide, "peacock", peacock_x, Inches(0.6), peacock_w, peacock_h)

    # Hero title (shifted down to clear the peacock)
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


def slide_client_about_argos(prs):
    """Who we are. Goes right after the title slide.
    Anchors the brand before any product talk.

    Round-5 reframe: surveillance lip-reading framing per
    docs/CLIENT_MEETING_FRAMING_v2.md (use case reframe).
    Adds small peacock brand mark beside the headline.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Argos")
    add_accent_line(slide)

    # Small peacock brand mark beside the headline
    peacock_h = Inches(0.5)
    peacock_w = Inches(0.5)
    add_image(slide,
              "peacock",
              MX + Inches(0.4),
              Inches(1.75),
              peacock_w, peacock_h)

    # Big tagline
    add_text(slide,
             "We build production-grade visual speech recognition.",
             MX, Inches(1.7), CW, Inches(0.8),
             size=Pt(28), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Lip-reading at scale, with built-in confidence.",
             MX, Inches(2.55), CW, Inches(0.5),
             size=Pt(18), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    # Three columns of "what we are"
    col_w = Inches(3.85)
    gap = Inches(0.25)
    top = Inches(3.6)
    h = Inches(2.5)

    items = [
        ("WHAT WE DO", TEAL,
         "End-to-end pipeline: face detection, mouth cropping, visual feature "
         "extraction, language decoding — and confidence scoring on every word."),
        ("WHO USES IT", GOLD,
         "Teams recovering speech from footage where audio is missing, can't "
         "be obtained, or can't be trusted: surveillance, intelligence-"
         "adjacent, security, accessibility-of-historical-record."),
        ("WHY IT MATTERS", GREEN,
         "Most speech-to-text systems hand you a transcript and a hope. We "
         "hand you a transcript with a per-word trust signal so you know "
         "what to review."),
    ]
    for i, (label, color, body) in enumerate(items):
        x = MX + i * (col_w + gap)
        add_rect(slide, x, top, col_w, h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), top + Inches(0.25),
                 col_w - Inches(0.4), Inches(0.4),
                 size=Pt(13), bold=True, color=color)
        add_text(slide, body, x + Inches(0.2), top + Inches(0.85),
                 col_w - Inches(0.4), h - Inches(1.0),
                 size=Pt(13), color=WHITE)

    add_text(slide,
             "Argos / The Orchard.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Open with the brand. 30-second elevator pitch — what we are, who we "
        "serve, what makes us different. Don't go deep on any one column; "
        "the next slide explains what we built."
    ))
    return slide


def slide_client_what_we_built(prs):
    """The concrete deliverables. Goes after about_argos.
    Sets expectations: this is a real product, not a research demo."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What we built — concretely")
    add_accent_line(slide)

    add_text(slide,
             "Six things actually exist today, end-to-end, on real data.",
             MX, Inches(1.65), CW, Inches(0.5),
             size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # 3x2 grid of deliverables (was 2x3 — overflowed past y=7.20).
    cols = 3
    rows = 2
    col_w = Inches(3.85)
    row_h = Inches(1.95)
    gap_x = Inches(0.25)
    gap_y = Inches(0.25)
    grid_top = Inches(2.3)

    items = [
        ("1. PIPELINE",       TEAL,
         "Nine automatic stages from raw video to confidence-scored transcript. Containerized; runs anywhere with a GPU."),
        ("2. WEB UI",         TEAL,
         "Drag-and-drop, live progress, downloadable HTML report. No command line required."),
        ("3. MODEL",          GOLD,
         "Visual-only encoder + LLaMA-2 decoder, fine-tuned on lip-reading. Same architecture VSP-LLM published, our own training run."),
        ("4. CONFIDENCE",     GREEN,
         "Per-word green/yellow/red. Per-segment Intelligibility Score. Hallucination auto-flagging."),
        ("5. EVALUATION",     GOLD,
         "1,497-segment baseline with WER, IS, and expert-judge agreement metrics. Reproducible from raw inputs."),
        ("6. INTEGRATION",    GREEN,
         "On-premise install, cloud deployment, or both. We deploy and hand off."),
    ]
    for i, (label, color, body) in enumerate(items):
        col = i % cols
        row = i // cols
        x = MX + col * (col_w + gap_x)
        y = grid_top + row * (row_h + gap_y)
        add_rect(slide, x, y, col_w, row_h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), y + Inches(0.15),
                 col_w - Inches(0.4), Inches(0.35),
                 size=Pt(13), bold=True, color=color)
        add_text(slide, body, x + Inches(0.2), y + Inches(0.6),
                 col_w - Inches(0.4), row_h - Inches(0.7),
                 size=Pt(12), color=WHITE)

    add_text(slide,
             "Everything you'll see today is in production today — not a 'with more research it could…' projection.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Six concrete deliverables. Each is a real artifact you can show. "
        "Frame this as 'this is what your team gets', not 'this is what "
        "we research.' The footnote is the closer: don't oversell future "
        "improvements."
    ))
    return slide


def slide_client_what_is_vsr(prs):
    """Background context. Most clients won't know what visual speech
    recognition is. Two minutes of teaching saves twenty of confusion later."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "What is visual speech recognition?")
    add_accent_line(slide)

    # Headline definition
    add_text(slide,
             "Reading speech from video alone — no audio.",
             MX, Inches(1.65), CW, Inches(0.6),
             size=Pt(24), bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Same problem a deaf lip reader solves, automated and at scale.",
             MX, Inches(2.3), CW, Inches(0.5),
             size=Pt(15), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # When you'd use it
    add_text(slide, "WHEN AUDIO ISN'T USABLE",
             MX, Inches(3.2), CW, Inches(0.4),
             size=Pt(13), bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    cases_top = Inches(3.7)
    case_w = Inches(2.95)
    case_h = Inches(1.9)
    case_gap = Inches(0.15)
    # Round-5 reframe: cases anchored to the surveillance use case
    # (per docs/CLIENT_MEETING_FRAMING_v2.md § "Use case reframe").
    cases = [
        ("MUTED",       "Surveillance footage, archive video,\nindoor or outdoor."),
        ("NOISY",       "Crowd noise, machinery, traffic,\ndistance from speaker."),
        ("UNRELIABLE",  "Suspected dub, voice-over,\nmismatched lip sync, edited audio."),
        ("AUDIO-LESS",  "Distant CCTV, drones,\nsilent stream captures."),
    ]
    total_w = 4 * case_w + 3 * case_gap
    start_x = MX + (CW - total_w) / 2
    for i, (label, body) in enumerate(cases):
        x = start_x + i * (case_w + case_gap)
        add_rect(slide, x, cases_top, case_w, case_h, fill_color=NAVY2, border_color=None)
        add_text(slide, label, x + Inches(0.2), cases_top + Inches(0.2),
                 case_w - Inches(0.4), Inches(0.4),
                 size=Pt(13), bold=True, color=TEAL, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + Inches(0.15), cases_top + Inches(0.75),
                 case_w - Inches(0.3), case_h - Inches(0.85),
                 size=Pt(12), color=WHITE, align=PP_ALIGN.CENTER)

    add_text(slide,
             "We've shipped this end-to-end. The next slides show the numbers.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Background slide. Most clients haven't heard of visual speech "
        "recognition. Spend 60 seconds: define the problem, name 4 use "
        "cases, then move on. The four cards are deliberately broad so "
        "the client maps their own use case onto one."
    ))
    return slide


def slide_client_video_gallery(prs):
    """Real demo videos with poster frames + click-to-play. Shows the
    system isn't just text — it actually produced these transcripts on
    these specific clips, and you can play any of them in PowerPoint."""
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Real outputs — pick any tile to play")
    add_accent_line(slide)

    add_text(slide,
             "Six real segments decoded by the model. Click a tile in PowerPoint to play.",
             MX, Inches(1.55), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # 2x3 grid of video posters
    cols = 3
    rows = 2
    gap = Inches(0.2)
    grid_top = Inches(2.1)
    grid_h = Inches(4.0)
    available_w = CW
    tile_w = (available_w - (cols - 1) * gap) / cols
    tile_h = (grid_h - (rows - 1) * gap) / rows
    caption_h = Inches(0.45)

    # Pick six representative clips — cleanest narrative spread.
    # All are real videos with hyp burned in, present in 06_demo_videos/.
    tiles = [
        ("perfect",        "PERFECT",          GREEN, "Clean visual, clean output"),
        ("vitamin_d",      "ALMOST PERFECT",   GREEN, "Near-verbatim transcription"),
        ("admiral",        "PARTIAL",          GOLD,  "Right gist, wrong specifics"),
        ("nearmiss",       "NEAR MISS",        GOLD,  "Off by a phrase, recoverable with context"),
        ("halluc",         "HALLUCINATION",    CORAL, "Fluent but wrong — auto-flagged"),
        ("topic_drift",    "TOPIC DRIFT",      CORAL, "Model lost the thread, system flags it"),
    ]

    for i, (vid_key, label, color, caption) in enumerate(tiles):
        col = i % cols
        row = i // cols
        x = MX + col * (tile_w + gap)
        y = grid_top + row * (tile_h + gap)
        # Poster frame + play button (helper handles missing video gracefully)
        add_video_poster(slide, vid_key, x, y, tile_w, tile_h - caption_h)
        # Caption strip below the poster
        add_rect(slide, x, y + tile_h - caption_h, tile_w, caption_h,
                 fill_color=NAVY2, border_color=None)
        add_text(slide, label,
                 x + Inches(0.1), y + tile_h - caption_h + Inches(0.05),
                 tile_w - Inches(0.2), Inches(0.25),
                 size=Pt(11), bold=True, color=color)
        add_text(slide, caption,
                 x + Inches(0.1), y + tile_h - caption_h + Inches(0.27),
                 tile_w - Inches(0.2), Inches(0.2),
                 size=Pt(9), color=LGRAY, italic=True)

    add_text(slide,
             "These six are a deliberate spread — best-case to worst-case. "
             "All visually decoded, no audio, on real-world video.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Pick 1-2 tiles to actually play during the meeting. Recommend "
        "starting with 'perfect' (sets the bar) then 'halluc' (shows the "
        "system catches the bad ones). Don't play all 6 — pick what fits "
        "your audience. All videos are static poster frames at deck-build "
        "time; in PowerPoint they have hyperlinks/embeds set by helpers."
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
    # Centered headline + subtitle + metadata stack. No icon — the cyan
    # border + "press play in PowerPoint" copy is enough to read as an
    # intentional video placeholder. Earlier attempts at a Unicode ▶ glyph
    # were dropped by the LibreOffice PDF render, and an MSO_SHAPE
    # triangle attempt blew out the rest of the textbox content. Plain
    # type is the boring-but-reliable choice.
    add_text(slide,
             "Live UI walkthrough",
             box_x, box_y + Inches(1.6), box_w, Inches(1.0),
             size=Pt(40), bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    add_text(slide,
             "End-to-end demo recorded by the presenter.",
             box_x, box_y + Inches(2.7), box_w, Inches(0.6),
             size=Pt(18), color=WHITE, italic=True, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Approximately 4-5 minutes  ·  press play in PowerPoint to start",
             box_x, box_y + Inches(3.5), box_w, Inches(0.5),
             size=Pt(13), color=LGRAY, align=PP_ALIGN.CENTER)
    add_text(slide,
             "If video does not embed before the meeting, narrate the demo: "
             "drag-drop upload → 9-stage pipeline → color-coded report.",
             box_x, box_y + Inches(4.3), box_w, Inches(0.6),
             size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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
        # Height-constrained: the source PNG is tall. Visual QA flagged
        # earlier 4.7"-tall sizing as too small at projection scale, so
        # bumped to 5.0" — fills the available content band more fully
        # and lets the per-word colors read across a room.
        from PIL import Image
        with Image.open(screenshot) as im:
            aspect = im.height / im.width
        img_h = Inches(5.0)
        img_w = Inches(5.0 / aspect)
        # If it's now wider than the slide can fit, cap on width.
        if img_w > Inches(11.5):
            img_w = Inches(11.5)
            img_h = Inches(11.5 * aspect)
        img_x = (SL_W - img_w) / 2
        img_y = Inches(1.45)
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

    add_text(slide,
             "Detection combines length-anomaly rules with per-token confidence — "
             "the model can fabricate fluent text but it usually 'knows' it.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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
        "An independent automated reviewer with no access to our scores or "
        "reasoning judged whether the message was conveyed at three levels — "
        "preserved, partial, not preserved — across all 1,497 pairs.",
        "We compared the system's confidence signals to that judgment",
        "Result: the trust score and the expert agree on most segments",
    ], MX, Inches(1.9), CW, Inches(4.0), size=Pt(18))

    add_text(slide,
             "Real-world YouTube footage — varied lighting, head angles, "
             "multi-speaker scenes, accents. Not curated lab footage.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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

    add_text(slide,
             "Tested across 16 different decode configurations on the same 1,497 segments.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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

    Native python-pptx shapes (not an embedded matplotlib PNG) so the
    fonts match the rest of the deck and labels stay positioned where
    we put them.
    """
    from pptx.enum.shapes import MSO_SHAPE
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 1 — Per-speaker entity split")
    add_accent_line(slide)

    # ── INPUT card (left): wide frame containing 2 stylized speakers ──
    in_x = MX + Inches(0.3)
    in_y = Inches(2.2)
    in_w = Inches(5.4)
    in_h = Inches(3.4)
    add_rect(slide, in_x, in_y, in_w, in_h, fill_color=NAVY2, border_color=LGRAY)
    add_text(slide, "INPUT — multi-speaker frame",
             in_x, in_y - Inches(0.4), in_w, Inches(0.35),
             size=Pt(12), bold=True, color=LGRAY, align=PP_ALIGN.CENTER)

    # Two stylized "speakers" — head circle on top of shoulders rect.
    def _speaker(left, top, color, label):
        # Head
        head = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                       left + Inches(0.5), top + Inches(0.2),
                                       Inches(0.7), Inches(0.7))
        head.fill.solid(); head.fill.fore_color.rgb = color
        head.line.fill.background()
        # Shoulders
        body = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       left + Inches(0.2), top + Inches(0.95),
                                       Inches(1.3), Inches(1.0))
        body.fill.solid(); body.fill.fore_color.rgb = color
        body.line.fill.background()
        # Label
        add_text(slide, label,
                 left, top + Inches(2.05), Inches(1.7), Inches(0.3),
                 size=Pt(11), bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    speaker_a_x = in_x + Inches(0.6)
    speaker_b_x = in_x + Inches(2.9)
    speaker_y = in_y + Inches(0.55)
    _speaker(speaker_a_x, speaker_y, TEAL, "Speaker A")
    _speaker(speaker_b_x, speaker_y, GOLD, "Speaker B")

    # ── Arrow + caption between INPUT and OUTPUT ──
    arrow_x = in_x + in_w + Inches(0.15)
    arrow_y = in_y + in_h / 2 - Inches(0.25)
    arrow_w = Inches(1.0)
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                    arrow_x, arrow_y, arrow_w, Inches(0.5))
    arrow.fill.solid(); arrow.fill.fore_color.rgb = TEAL
    arrow.line.fill.background()
    add_text(slide, "FACE DETECTION + TRACKER",
             arrow_x - Inches(0.5), arrow_y - Inches(0.5), Inches(2.0), Inches(0.3),
             size=Pt(10), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "(runs locally)",
             arrow_x - Inches(0.5), arrow_y + Inches(0.55), Inches(2.0), Inches(0.3),
             size=Pt(9), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # ── OUTPUT card (right): two stacked centered crops ──
    out_x = arrow_x + arrow_w + Inches(0.4)
    out_y = in_y
    out_w = Inches(4.2)
    out_h = in_h
    add_rect(slide, out_x, out_y, out_w, out_h, fill_color=NAVY2, border_color=LGRAY)
    add_text(slide, "OUTPUT — per-speaker crops",
             out_x, out_y - Inches(0.4), out_w, Inches(0.35),
             size=Pt(12), bold=True, color=LGRAY, align=PP_ALIGN.CENTER)

    # Two square crops, each with a small centered head
    crop_size = Inches(1.4)
    crop_a_y = out_y + Inches(0.15)
    crop_b_y = out_y + Inches(1.7)
    crop_x = out_x + Inches(0.25)

    for cy, color, label in [(crop_a_y, TEAL, "Speaker A → centered crop"),
                              (crop_b_y, GOLD, "Speaker B → centered crop")]:
        # Crop frame
        crop = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                       crop_x, cy, crop_size, crop_size)
        crop.fill.solid(); crop.fill.fore_color.rgb = NAVY3
        crop.line.color.rgb = color; crop.line.width = Pt(1.2)
        # Centered mini-speaker
        head = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                       crop_x + Inches(0.5), cy + Inches(0.25),
                                       Inches(0.4), Inches(0.4))
        head.fill.solid(); head.fill.fore_color.rgb = color
        head.line.fill.background()
        body = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       crop_x + Inches(0.35), cy + Inches(0.7),
                                       Inches(0.7), Inches(0.55))
        body.fill.solid(); body.fill.fore_color.rgb = color
        body.line.fill.background()
        # Label to the right of the crop
        add_text(slide, label,
                 crop_x + crop_size + Inches(0.2), cy + Inches(0.5),
                 out_w - crop_size - Inches(0.5), Inches(0.4),
                 size=Pt(12), color=WHITE)

    # ── Footer caption ──
    add_text(slide,
             "Two speakers in one frame become two centered crops. Each "
             "speaker gets its own clean lip-reading pass.",
             MX, Inches(6.0), CW, Inches(0.4),
             size=Pt(13), color=TEAL, italic=True, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Status: planned ablation. Runs locally. No cloud dependency.",
             MX, Inches(6.45), CW, Inches(0.35),
             size=Pt(10), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Native python-pptx shapes (not embedded matplotlib). The 'face "
        "detection + tracker' framing leaves implementation open — YOLO, "
        "RetinaFace, MediaPipe, etc. Emphasize 'runs locally' for client "
        "comfort: no extra cloud dependency, no extra cost. Status is "
        "explicitly 'planned ablation' — we are NOT claiming this is "
        "shipping today."
    ))
    return slide


def slide_client_quality_filter(prs):
    """Drop bad-angle / occluded / low-light clips before pipeline.

    Native python-pptx shapes — five stacked horizontal bars, each
    progressively narrower, with tier label / percentage / rejection
    sub-label. Replaces the matplotlib funnel PNG (which had a
    system-fallback font that didn't match the deck's Calibri).
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Pre-processing 2 — Quality pre-filter")
    add_accent_line(slide)

    add_text(slide,
             "Reject bad clips before they reach the model.",
             MX, Inches(1.5), CW, Inches(0.4),
             size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Funnel: 5 horizontal bars, narrowing top-to-bottom
    chart_top = Inches(2.1)
    bar_h = Inches(0.65)
    bar_gap = Inches(0.18)
    label_w = Inches(2.9)   # was 2.4 — "All uploaded clips" was clipping at 2.4"/Pt(13)
    rejected_w = Inches(3.6)
    # Center the chart horizontally
    max_bar_w = Inches(5.0)
    chart_left = label_w + Inches(0.3)
    # x of bars is chart_left, but each bar is centered around chart_center
    chart_center = chart_left + max_bar_w / 2

    tiers = [
        ("All uploaded clips",          1.00, MGRAY,                None),
        ("Head angle ≤ N°",             0.90, TEAL,  "rejected: face too profile (-10%)"),
        ("Mouth visibility",            0.82, TEAL,  "rejected: mouth occluded (-8%)"),
        ("Lighting / contrast",         0.75, TEAL,  "rejected: too dark or washed out (-7%)"),
        ("Reaches the model",           0.75, GREEN, None),
    ]
    for i, (label, frac, color, rejected) in enumerate(tiers):
        y = chart_top + i * (bar_h + bar_gap)
        bar_w = max_bar_w * frac
        bar_x = chart_center - bar_w / 2
        # Tier label (left)
        add_text(slide, label, MX, y + Inches(0.12), label_w, Inches(0.4),
                 size=Pt(13), bold=True, color=WHITE, align=PP_ALIGN.RIGHT)
        # Bar
        bar = add_rect(slide, bar_x, y, bar_w, bar_h,
                       fill_color=color, border_color=None)
        # Percentage in bar
        pct = f"{int(frac * 100)}%"
        add_text(slide, pct, bar_x, y + Inches(0.12), bar_w, Inches(0.4),
                 size=Pt(15), bold=True, color=BG, align=PP_ALIGN.CENTER)
        # Rejected sub-label (right)
        if rejected:
            add_text(slide, rejected,
                     chart_left + max_bar_w + Inches(0.3), y + Inches(0.18),
                     rejected_w, Inches(0.4),
                     size=Pt(10), color=LGRAY, italic=True)

    # Footer caption
    add_text(slide,
             "Three frame-level CV checks, all running locally. Status: "
             "planned ablation. Percentages illustrative — actual rejection "
             "rates depend on your video conditions.",
             MX, Inches(6.5), CW, Inches(0.6),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Native python-pptx funnel (no matplotlib). Frame as 'highest leverage "
        "per dollar.' The model is never tested in isolation; what reaches "
        "it is what matters. The funnel percentages shown are illustrative — "
        "actual rejection rates depend on the client's own video conditions, "
        "which is exactly what the ablation would measure. Status is 'planned "
        "ablation' — not yet shipping."
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

    add_text(slide,
             "Biggest expected lift: yellow / red segments — where richer language "
             "priors help disambiguate visemically-identical words.",
             MX, Inches(6.55), CW, Inches(0.45),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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
    """The funding ask, reframed as PARTNERSHIP per Round-5 framing.

    Source: docs/CLIENT_MEETING_FRAMING_v2.md § "Investment ask framing".
    Three beats, no line items, no dollar amounts. Title carries the
    partnership frame, not the budget frame.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "The next milestone is a partnership")
    add_accent_line(slide)

    # Three beats stacked vertically — direct quote from framing doc.
    beat_x = MX
    beat_w = CW
    beat_h = Inches(1.35)
    beat_gap = Inches(0.25)
    beat_top = Inches(1.85)

    beats = [
        ("1.",
         "Today's model is trained on a small slice of public data, not your "
         "domain. It works, but it's a prototype, not a production model on "
         "your content.",
         TEAL),
        ("2.",
         "We're proposing to go from prototype to production *together* — "
         "your data, our pipeline, a shared training run on your domain.",
         GREEN),
        ("3.",
         "Specifics in follow-up.",
         GOLD),
    ]
    for i, (num, body, color) in enumerate(beats):
        y = beat_top + i * (beat_h + beat_gap)
        add_rect(slide, beat_x, y, beat_w, beat_h,
                 fill_color=NAVY2, border_color=None)
        add_text(slide, num, beat_x + Inches(0.3), y + Inches(0.3),
                 Inches(0.8), Inches(0.8),
                 size=Pt(28), bold=True, color=color)
        add_text(slide, body, beat_x + Inches(1.2), y + Inches(0.25),
                 beat_w - Inches(1.5), beat_h - Inches(0.4),
                 size=Pt(16), color=WHITE)

    add_text(slide,
             "No dollar amounts on slide. Specifics in the follow-up.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Title and framing per docs/CLIENT_MEETING_FRAMING_v2.md § "
        "'Investment ask framing'. The three beats are quoted verbatim from "
        "that doc. They are NOT price-sensitive — the slide doesn't justify "
        "cost, it sizes the unlock. No compute / data / engineering "
        "breakdown on slide. Bridge from data_ask: 'Data without a training "
        "budget is a folder. Budget without data is a wishlist. Both "
        "together is a model trained on your content.'"
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

    add_text(slide,
             "Typical handoff: 4-8 weeks from contract to first end-to-end run on your data.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

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


# ──────────────────────────────────────────────────────────────────────────
# Round-5 additions — Framing v2 alignment
# (per docs/CLIENT_MEETING_FRAMING_v2.md and
#  .claude/plans/i-need-to-create-proud-cupcake.md § "Round 5")
# ──────────────────────────────────────────────────────────────────────────


def slide_client_compared_to_today(prs):
    """The comparative anchor — Section 1, after `what_we_built`,
    before the demo.

    Three-row card stack contrasting expert lip-readers, do-nothing,
    and Argos+reviewer. Numbers from docs/CLIENT_MEETING_FRAMING_v2.md
    § "Compared to today" (sourced from academic deck slide 7 +
    published lip-reading literature).
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Compared to today")
    add_accent_line(slide)

    add_text(slide,
             "The client doesn't have a current vendor — they have two "
             "unsatisfactory options. We're the third.",
             MX, Inches(1.55), CW, Inches(0.45),
             size=Pt(15), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Column header strip
    header_y = Inches(2.1)
    header_h = Inches(0.4)
    col_label_w = Inches(3.5)
    col_acc_w = Inches(2.6)
    col_time_w = Inches(3.0)
    col_halluc_w = Inches(3.03)

    col_xs = [MX,
              MX + col_label_w,
              MX + col_label_w + col_acc_w,
              MX + col_label_w + col_acc_w + col_time_w]

    headers = ["APPROACH", "WORD ACCURACY", "TIME PER HOUR", "HALLUCINATION RISK"]
    widths = [col_label_w, col_acc_w, col_time_w, col_halluc_w]
    for i, (h, w, x) in enumerate(zip(headers, widths, col_xs)):
        add_text(slide, h, x, header_y, w, header_h,
                 size=Pt(11), bold=True, color=LGRAY, align=PP_ALIGN.CENTER)

    # Three rows
    row_h = Inches(1.2)
    row_gap = Inches(0.18)
    rows_top = Inches(2.65)

    rows = [
        # (label, accuracy, time, halluc, fill, border)
        ("Expert human lip-reader",
         "45 – 52%",
         "hours of expert time",
         "varies, hard to audit",
         NAVY2, None,
         WHITE),
        ("Don't do it at all",
         "—",
         "0 (information is lost)",
         "—",
         NAVY2, None,
         LGRAY),
        ("Argos + reviewer",
         "55 – 70%",
         "minutes of reviewer time",
         "near-zero, flagged",
         NAVY3, GREEN,
         WHITE),
    ]
    accent_colors = [LGRAY, MGRAY, TEAL]
    for i, (label, acc, time, halluc, fill, border, txtcol) in enumerate(rows):
        y = rows_top + i * (row_h + row_gap)
        add_rect(slide, MX, y, CW, row_h, fill_color=fill, border_color=border)
        # Approach label (left)
        add_text(slide, label, col_xs[0] + Inches(0.2), y + Inches(0.4),
                 col_label_w - Inches(0.3), Inches(0.5),
                 size=Pt(15) if i != 2 else Pt(17),
                 bold=(i == 2), color=txtcol)
        # Accuracy
        acc_color = accent_colors[i] if i != 2 else GREEN
        add_text(slide, acc, col_xs[1], y + Inches(0.35),
                 col_acc_w, Inches(0.55),
                 size=Pt(20) if i == 2 else Pt(18),
                 bold=True, color=acc_color, align=PP_ALIGN.CENTER)
        # Time
        add_text(slide, time, col_xs[2], y + Inches(0.4),
                 col_time_w, Inches(0.5),
                 size=Pt(13) if i != 2 else Pt(14),
                 bold=(i == 2), color=txtcol, align=PP_ALIGN.CENTER)
        # Hallucination risk
        halluc_color = txtcol if i != 2 else GREEN
        add_text(slide, halluc, col_xs[3], y + Inches(0.4),
                 col_halluc_w - Inches(0.2), Inches(0.5),
                 size=Pt(13) if i != 2 else Pt(14),
                 bold=(i == 2), color=halluc_color, align=PP_ALIGN.CENTER)

    add_text(slide,
             "Word accuracy figures from published lip-reading literature "
             "(Bear & Harvey 2017, Assael et al. 2016).",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(10), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "The comparative anchor for Section 1. The bottom row (Argos + "
        "reviewer) is the punch — system + reviewer using the colored "
        "confidence report outperforms expert humans alone, in minutes "
        "instead of hours, with near-zero hallucination risk because the "
        "system flags its own uncertainty. Numbers from "
        "docs/CLIENT_MEETING_FRAMING_v2.md (academic deck slide 7). "
        "Critical for cold audience members — first 10 minutes of the "
        "meeting do most of the work for them, this is where they map our "
        "product onto a problem they recognize."
    ))
    return slide


def slide_client_halluc_problem(prs):
    """Section 9 trio — first slide.

    'The model can produce confident text that's wrong.'
    Defines the failure mode in the abstract, sets up the real example
    on the next slide.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "The model can produce confident text that's wrong.")
    add_accent_line(slide)

    # Big definition statement — the thing to feel
    add_text(slide,
             "Sometimes the model fabricates fluent text from nothing.",
             MX, Inches(1.9), CW, Inches(0.8),
             size=Pt(26), bold=True, color=CORAL, align=PP_ALIGN.CENTER)

    # Explanatory paragraph
    add_text(slide,
             "Visual lip-reading is hard. When the visual signal is weak — "
             "off-axis face, occluded mouth, ambiguous viseme — a language-"
             "model decoder will sometimes confabulate text that reads well "
             "and follows English grammar, with no real visual evidence "
             "behind it.",
             MX, Inches(3.2), CW, Inches(1.7),
             size=Pt(17), color=WHITE, align=PP_ALIGN.LEFT)

    # Footnote pill — the framing line
    add_rect(slide, MX, Inches(5.4), CW, Inches(0.95),
             fill_color=NAVY2, border_color=CORAL)
    add_text(slide,
             "This is the dangerous-failure mode for surveillance — fluent "
             "transcripts that look right but aren't.",
             MX + Inches(0.3), Inches(5.55), CW - Inches(0.6), Inches(0.7),
             size=Pt(15), color=WHITE, italic=True, bold=True,
             align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Slide 1 of the hallucination case-study trio per "
        "docs/CLIENT_MEETING_FRAMING_v2.md § 'Trust story'. The trust "
        "story IS the product for this audience — an unflagged "
        "hallucination isn't an inconvenience, it's a wrong belief about "
        "a real conversation that the client may act on. Make them feel "
        "the failure first, then the catch on slides 2-3 of the trio."
    ))
    return slide


def slide_client_halluc_real_example(prs):
    """Section 9 trio — second slide.

    Reuses the existing _example_slide layout + Obama segment 5 sidecar
    (same data slide_client_example_flagged uses). REF says
    'heroic citizens saved'; the model said 'rwanda's genocide'.
    """
    return _example_slide(
        prs,
        title="Here's what that looks like in practice.",
        subtitle="Obama bin Laden announcement  ·  segment #5  ·  14.98–18.58 s",
        utt_id="05_001498_001858",
        takeaway="REF said \"heroic citizens saved.\" The model said "
                 "\"rwanda's genocide.\" That's the failure mode in 1.5 "
                 "seconds of footage.",
        takeaway_color=CORAL,
    )


def slide_client_halluc_caught(prs):
    """Section 9 trio — third slide.

    Two-column: left = same Obama segment 5 hyp re-rendered with
    emphasis on the red/yellow words; right = trust signals card
    showing how the system caught it. Anchors on min_p = 0.02.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "...and the system caught it.")
    add_accent_line(slide)

    add_text(slide,
             "Same segment as the previous slide — now with the trust "
             "signals layered on.",
             MX, Inches(1.45), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    # Left column — colored hypothesis (re-rendered from sidecar)
    left_w = Inches(7.0)
    left_x = MX
    left_y = Inches(2.1)
    left_h = Inches(4.0)
    add_rect(slide, left_x, left_y, left_w, left_h,
             fill_color=NAVY2, border_color=None)
    add_text(slide, "DECODED HYPOTHESIS",
             left_x + Inches(0.25), left_y + Inches(0.2),
             left_w - Inches(0.5), Inches(0.35),
             size=Pt(11), bold=True, color=LGRAY)

    ref, words = _load_obama_segment("05_001498_001858")
    if words:
        runs = []
        for w in words:
            klass = w.get("conf_class", "conf-unknown")
            color = _color_for_class(klass)
            # Bold the low- and med-confidence words to draw the eye
            bold = klass in ("conf-low", "conf-med")
            runs.append((w["word"] + " ",
                         {"size": Pt(18), "color": color, "bold": bold}))
        add_rich_text(slide, [runs],
                      left_x + Inches(0.25), left_y + Inches(0.65),
                      left_w - Inches(0.5), left_h - Inches(0.85))
    else:
        add_text(slide,
                 "(real-confidence sidecar not loaded — placeholder)",
                 left_x + Inches(0.25), left_y + Inches(0.85),
                 left_w - Inches(0.5), Inches(0.4),
                 size=Pt(13), color=MGRAY, italic=True)

    # Right column — trust signals card
    right_x = left_x + left_w + Inches(0.3)
    right_w = CW - left_w - Inches(0.3)
    right_y = left_y
    right_h = left_h
    add_rect(slide, right_x, right_y, right_w, right_h,
             fill_color=NAVY3, border_color=GREEN)
    add_text(slide, "WHAT THE SYSTEM DID",
             right_x + Inches(0.25), right_y + Inches(0.2),
             right_w - Inches(0.5), Inches(0.35),
             size=Pt(11), bold=True, color=GREEN)

    # Three signal lines
    sig_top = right_y + Inches(0.65)
    sig_h = Inches(0.95)
    sig_gap = Inches(0.15)

    signals = [
        ("LOW CONFIDENCE",
         "Lowest-confidence word at p = 0.02.",
         CORAL),
        ("AUTO-EXCLUDED",
         "Segment auto-excluded from \"useful output.\"",
         GOLD),
        ("REVIEWER PATH",
         "Reviewer goes straight to the flagged spans.",
         TEAL),
    ]
    for i, (label, body, color) in enumerate(signals):
        y = sig_top + i * (sig_h + sig_gap)
        add_text(slide, label,
                 right_x + Inches(0.25), y,
                 right_w - Inches(0.5), Inches(0.32),
                 size=Pt(11), bold=True, color=color)
        add_text(slide, body,
                 right_x + Inches(0.25), y + Inches(0.32),
                 right_w - Inches(0.5), sig_h - Inches(0.32),
                 size=Pt(13), color=WHITE)

    # Legend strip
    add_text(slide,
             "GREEN: confident   YELLOW: review   RED: likely error",
             MX, Inches(6.55), CW, Inches(0.3),
             size=Pt(9), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Slide 3 of the hallucination case-study trio. The narrative beat: "
        "model fabricated 'rwanda's genocide' from a clip about heroic "
        "citizens — and KNEW it. Lowest per-token probability hit 0.02 on "
        "'rwanda's', the segment was below the IS threshold for 'useful "
        "output,' and the colored hypothesis sends the reviewer straight to "
        "the red and yellow spans instead of having to read the whole "
        "transcript. The min_p = 0.02 anchor is real (matches the existing "
        "slide_client_example_flagged speaker note). Don't say IS or κ on "
        "the slide."
    ))
    return slide


def slide_client_failure_taxonomy(prs):
    """Section 9 — after the hallucination trio.

    'When it fails, here's how' — five failure-mode bars with real
    frequencies on the 574 below-threshold segments. Pulled from
    docs/CLIENT_MEETING_FRAMING_v2.md § "Trust framework (the
    differentiator)" and academic deck failure-mode slides.
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "When it fails, here's how")
    add_accent_line(slide)

    add_text(slide,
             "Five failure modes. Real frequencies on the 574 segments "
             "the system rated below the useful-output threshold.",
             MX, Inches(1.55), CW, Inches(0.45),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Five horizontal bars
    chart_top = Inches(2.2)
    bar_h = Inches(0.7)
    bar_gap = Inches(0.18)
    label_w = Inches(3.0)
    max_bar_w = Inches(4.5)
    desc_w = Inches(4.4)

    bar_origin_x = MX + label_w + Inches(0.2)

    modes = [
        ("Wrong Topic",                44.4, 255, "mouth shapes decoded to wrong domain",        CORAL),
        ("Hallucination",              18.8, 108, "model invented fake text",                    RED),
        ("Signal Loss",                13.9, 80,  "empty or near-empty output",                  GOLD),
        ("Right Topic, Wrong Details", 13.8, 79,  "gist right, names/content lost",              TEAL),
        ("Accumulated Errors",         9.1,  52,  "many small errors compound",                  GREEN),
    ]
    # Find max for proportional widths (largest = full bar width)
    max_pct = max(m[1] for m in modes)
    for i, (name, pct, count, desc, color) in enumerate(modes):
        y = chart_top + i * (bar_h + bar_gap)
        # Mode label (left)
        add_text(slide, name, MX, y + Inches(0.18), label_w, Inches(0.4),
                 size=Pt(13), bold=True, color=WHITE, align=PP_ALIGN.RIGHT)
        # Bar
        bar_w = max_bar_w * (pct / max_pct)
        add_rect(slide, bar_origin_x, y, bar_w, bar_h,
                 fill_color=color, border_color=None)
        # Percentage in bar
        add_text(slide, f"{pct:.1f}%  ({count})",
                 bar_origin_x, y + Inches(0.18),
                 bar_w, Inches(0.4),
                 size=Pt(13), bold=True, color=BG, align=PP_ALIGN.CENTER)
        # Description (right of bar)
        add_text(slide, desc,
                 bar_origin_x + max_bar_w + Inches(0.2),
                 y + Inches(0.2),
                 desc_w, Inches(0.4),
                 size=Pt(11), color=LGRAY, italic=True)

    # Footer pill
    add_rect(slide, MX, Inches(6.4), CW, Inches(0.6),
             fill_color=NAVY2, border_color=TEAL)
    add_text(slide,
             "Honest disclosure. The trust signals tag every one of these "
             "for the reviewer.",
             MX + Inches(0.3), Inches(6.5), CW - Inches(0.6), Inches(0.4),
             size=Pt(13), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Failure-mode taxonomy from docs/CLIENT_MEETING_FRAMING_v2.md § "
        "'Trust framework' (sourced from academic deck failure_deep_1a/_1b "
        "and slide_08). 574 = total below-threshold segments out of 1,497. "
        "Frequencies sum to ~100%: 255+108+80+79+52 = 574. Hiding failure "
        "modes reads as marketing; honest disclosure builds trust. Worked "
        "example for the largest bucket (Wrong Topic) is on the next slide."
    ))
    return slide


def slide_client_failure_worked_example(prs):
    """Section 9 — after `failure_taxonomy`.

    Worked example for the 'Wrong Topic' bucket (largest, most teachable).
    Reuses the _example_slide pattern with Obama segment 27, where
    'bin laden' was decoded as 'middle east' — a topic-drift case.
    """
    return _example_slide(
        prs,
        title="Failure mode in practice — Wrong Topic",
        subtitle="Obama bin Laden announcement  ·  segment #27  ·  80.91–84.51 s",
        utt_id="27_008091_008451",
        takeaway="Topic drifted — \"bin laden\" became \"middle east.\" "
                 "WER calls this 59% wrong; the trust signal calls it: "
                 "high-confidence-but-flagged.",
        takeaway_color=CORAL,
    )


def slide_client_engineering_journey(prs):
    """Section 5 (What we built) — after `what_we_built`.

    Four milestones across the four-month engineering pass.
    Source: docs/CLIENT_MEETING_FRAMING_v2.md § "Engineering credibility
    (for the partner audience)".
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "How we built it — four months, four milestones")
    add_accent_line(slide)

    add_text(slide,
             "We integrated, tested, and shipped — not researched in theory.",
             MX, Inches(1.55), CW, Inches(0.45),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Four milestone rows — vertical timeline
    row_top = Inches(2.1)
    row_h = Inches(0.95)
    row_gap = Inches(0.15)
    num_w = Inches(0.9)
    title_x = MX + num_w + Inches(0.15)
    title_w = CW - num_w - Inches(0.15)

    milestones = [
        ("M1",
         "Adopted three open-source codebases — auto_avsr, av_hubert, VSP-LLM.",
         "Integrated, not reinvented.",
         TEAL),
        ("M2",
         "37 bugs fixed and documented.",
         "Open changelog of every problem solved.",
         GOLD),
        ("M3",
         "Confidence layer shipped — Tier-1 IS + Tier-2 per-token.",
         "Both calibrated against an independent expert reviewer.",
         GREEN),
        ("M4",
         "Dual-environment validation — refactor-v1.0 → ec2-v1.1 → container-v1.1.",
         "Same code on AWS and on-premise.",
         CORAL),
    ]
    for i, (m_id, head, body, color) in enumerate(milestones):
        y = row_top + i * (row_h + row_gap)
        # Number badge
        add_rect(slide, MX, y, num_w, row_h,
                 fill_color=NAVY3, border_color=color)
        add_text(slide, m_id, MX, y + Inches(0.25),
                 num_w, Inches(0.5),
                 size=Pt(20), bold=True, color=color, align=PP_ALIGN.CENTER)
        # Body card
        add_rect(slide, title_x, y, title_w, row_h,
                 fill_color=NAVY2, border_color=None)
        add_text(slide, head, title_x + Inches(0.3), y + Inches(0.13),
                 title_w - Inches(0.4), Inches(0.4),
                 size=Pt(15), bold=True, color=WHITE)
        add_text(slide, body, title_x + Inches(0.3), y + Inches(0.55),
                 title_w - Inches(0.4), Inches(0.4),
                 size=Pt(12), color=LGRAY, italic=True)

    # Footer
    add_text(slide,
             "We keep an open changelog of every problem solved.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(11), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Engineering credibility for the partner audience. All four "
        "milestones from docs/CLIENT_MEETING_FRAMING_v2.md § 'Engineering "
        "credibility'. Architecture specificity is OK here per Round-5 "
        "framing — partners want to see real choices for integration. "
        "Model names (auto_avsr, av_hubert, VSP-LLM, LLaMA, AV-HuBERT) are "
        "fine; LoRA r-values still scrubbed per N9. The git tags are real "
        "(refactor-v1.0 → ec2-v1.1 → container-v1.1)."
    ))
    return slide


def slide_client_data_ask(prs):
    """Section 12 (What's next) — replaces `stronger_model` +
    `more_data` + `roadmap_phases`.

    Frames the data ask as the bridge to investment_ask. Three short
    framing lines, footer brings the partnership beat.
    Source: plan § "Round 5 → Investment-ask reframe".
    """
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "The next milestone needs more training data — from you.")
    add_accent_line(slide)

    add_text(slide,
             "Today's model is trained on a small slice of public data, "
             "not your domain.",
             MX, Inches(1.7), CW, Inches(0.7),
             size=Pt(20), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    # Three framing lines
    line_top = Inches(2.7)
    line_h = Inches(1.05)
    line_gap = Inches(0.18)

    lines = [
        ("Direction is known.",
         "More data on your domain → fewer flagged segments, better "
         "domain-vocabulary recovery.",
         TEAL),
        ("Path is concrete.",
         "Same pipeline, same architecture — a shared training run "
         "on your data.",
         GREEN),
        ("Outcome is yours.",
         "The model that ships at the end is trained on your content, "
         "not a benchmark.",
         GOLD),
    ]
    for i, (head, body, color) in enumerate(lines):
        y = line_top + i * (line_h + line_gap)
        add_rect(slide, MX, y, CW, line_h, fill_color=NAVY2, border_color=None)
        add_text(slide, head, MX + Inches(0.3), y + Inches(0.18),
                 Inches(4.5), Inches(0.4),
                 size=Pt(16), bold=True, color=color)
        add_text(slide, body, MX + Inches(0.3), y + Inches(0.6),
                 CW - Inches(0.6), Inches(0.4),
                 size=Pt(13), color=WHITE, italic=True)

    # Bridge to investment_ask
    add_rect(slide, MX, Inches(6.35), CW, Inches(0.65),
             fill_color=NAVY3, border_color=TEAL)
    add_text(slide,
             "Data without a training budget is a folder. Budget without "
             "data is a wishlist. Both together is a model trained on "
             "your content.",
             MX + Inches(0.3), Inches(6.4), CW - Inches(0.6), Inches(0.55),
             size=Pt(12), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "This slide is the bridge into the investment-ask slide. The "
        "footer line is quoted from docs/CLIENT_MEETING_FRAMING_v2.md § "
        "'Investment ask framing' — it's the connection sentence that "
        "ties the data ask and the budget ask together. Three beats "
        "(direction / path / outcome) per the plan § 'Round 5 → "
        "Investment-ask reframe (rewrite existing)'. No specific dataset "
        "sizes on slide — direction-only framing per N9."
    ))
    return slide


def slide_client_multi_speaker_today_vs_path(prs):
    """Section 12 (What's next) — FIRST slide.
    REPLACES `slide_client_entity_split`.

    Multi-speaker is the client's canonical use case (two-person
    conversational footage). Frame as "today single-speaker; here's
    the entity-split path."
    Source: docs/CLIENT_MEETING_FRAMING_v2.md § "Multi-speaker emphasis"
    + plan § "Round 5".
    """
    from pptx.enum.shapes import MSO_SHAPE
    slide = new_slide(prs)
    _auto_num[0] += 1
    add_title(slide, "Multi-speaker: today vs. the path forward")
    add_accent_line(slide)

    add_text(slide,
             "Two-person conversational footage is your canonical use case. "
             "Here's where we are honestly today, and where we go next.",
             MX, Inches(1.55), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Two columns
    col_w = Inches(5.95)
    gap = Inches(0.2)
    top = Inches(2.25)
    h = Inches(4.0)

    # ── LEFT — TODAY ──
    left_x = MX
    add_rect(slide, left_x, top, col_w, h,
             fill_color=NAVY2, border_color=CORAL)
    add_text(slide, "TODAY",
             left_x + Inches(0.3), top + Inches(0.25),
             col_w - Inches(0.6), Inches(0.5),
             size=Pt(13), bold=True, color=CORAL)
    add_text(slide, "Single-speaker mode",
             left_x + Inches(0.3), top + Inches(0.7),
             col_w - Inches(0.6), Inches(0.6),
             size=Pt(22), bold=True, color=WHITE)
    add_text(slide,
             "The current model assumes one centered face per frame. "
             "Two-person conversational footage degrades the visual signal — "
             "the model can lose track of which speaker is currently "
             "talking.",
             left_x + Inches(0.3), top + Inches(1.55),
             col_w - Inches(0.6), Inches(1.6),
             size=Pt(14), color=LGRAY)

    # Mini illustration: one face icon, single crop
    illu_y = top + h - Inches(1.2)
    head1 = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        left_x + col_w / 2 - Inches(0.3),
        illu_y,
        Inches(0.6), Inches(0.6))
    head1.fill.solid()
    head1.fill.fore_color.rgb = CORAL
    head1.line.fill.background()
    add_text(slide, "one centered crop",
             left_x, illu_y + Inches(0.7),
             col_w, Inches(0.3),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # ── RIGHT — PATH ──
    right_x = left_x + col_w + gap
    add_rect(slide, right_x, top, col_w, h,
             fill_color=NAVY2, border_color=GREEN)
    add_text(slide, "PATH",
             right_x + Inches(0.3), top + Inches(0.25),
             col_w - Inches(0.6), Inches(0.5),
             size=Pt(13), bold=True, color=GREEN)
    add_text(slide, "Entity-split preprocessing",
             right_x + Inches(0.3), top + Inches(0.7),
             col_w - Inches(0.6), Inches(0.6),
             size=Pt(22), bold=True, color=WHITE)
    add_text(slide,
             "Local face detection + tracker emits per-speaker centered "
             "crops. Each speaker gets its own clean lip-reading pass. "
             "Three weeks of engineering, not research.",
             right_x + Inches(0.3), top + Inches(1.55),
             col_w - Inches(0.6), Inches(1.6),
             size=Pt(14), color=LGRAY)

    # Mini illustration: two face icons, two arrows, two crops
    a_x = right_x + Inches(0.5)
    b_x = right_x + Inches(1.4)
    head_a = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, a_x, illu_y, Inches(0.5), Inches(0.5))
    head_a.fill.solid(); head_a.fill.fore_color.rgb = TEAL
    head_a.line.fill.background()
    head_b = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, b_x, illu_y, Inches(0.5), Inches(0.5))
    head_b.fill.solid(); head_b.fill.fore_color.rgb = GOLD
    head_b.line.fill.background()
    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW,
        right_x + Inches(2.1), illu_y + Inches(0.1),
        Inches(0.7), Inches(0.3))
    arrow.fill.solid(); arrow.fill.fore_color.rgb = GREEN
    arrow.line.fill.background()
    crop_a = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        right_x + Inches(2.95), illu_y - Inches(0.05),
        Inches(0.5), Inches(0.5))
    crop_a.fill.solid(); crop_a.fill.fore_color.rgb = TEAL
    crop_a.line.fill.background()
    crop_b = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        right_x + Inches(3.55), illu_y - Inches(0.05),
        Inches(0.5), Inches(0.5))
    crop_b.fill.solid(); crop_b.fill.fore_color.rgb = GOLD
    crop_b.line.fill.background()
    add_text(slide, "two speakers → two crops",
             right_x, illu_y + Inches(0.7),
             col_w, Inches(0.3),
             size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Footer
    add_text(slide,
             "This is the gap we're flagging honestly because it's your "
             "canonical use case.",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(11), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    set_notes(slide, (
        "Replaces slide_client_entity_split. The narrative shift is from "
        "'planned ablation' (research-toned) to 'honest gap with a "
        "concrete path' (partnership-toned). Three weeks of engineering "
        "is the realistic estimate from the plan. Lead the 'What's next' "
        "section with this slide — multi-speaker is the client's "
        "canonical case per docs/CLIENT_MEETING_FRAMING_v2.md § "
        "'Client's concerns, ranked'."
    ))
    return slide
