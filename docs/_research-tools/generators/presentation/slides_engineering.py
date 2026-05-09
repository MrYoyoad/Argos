"""
Slide builders — Section 7: Engineering
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
# SLIDE 17 — PIPELINE ARCHITECTURE (split into two slides, May 2026)
# ═══════════════════════════════════════════════════════════════════════
# audit:layout_round5 — original single-slide 8-stage diagram was cramped
# (boxes 2.6×1.2" with overlapping name/sub text frames at 24pt). Split into
# 17_a (Preprocessing, stages 1-4 + ASR side-branch) and 17_b (Decoding +
# Output, stages 5-8) so each row has 4× the vertical room. Boxes now
# 2.6×1.8" with cleanly separated 24pt label and 22pt caption frames.

# Shared palette for both halves of the pipeline diagram.
_PIPE_BLUE   = RGBColor(0x4D, 0xD0, 0xE1)
_PIPE_SGREEN = RGBColor(0x66, 0xBB, 0x6A)
_PIPE_SGOLD  = RGBColor(0xFF, 0xCA, 0x28)
_PIPE_SPINK  = RGBColor(0xEF, 0x9A, 0x9A)
_PIPE_DARK   = RGBColor(0x0D, 0x1B, 0x2A)
_PIPE_SCORAL = RGBColor(0xE0, 0x6C, 0x75)


def _pipe_box(slide, name, sub, color, x, y, w, h):
    """Pipeline-stage box: bold stage label on top, caption below.

    Frames are vertically separated (no overlap) — name occupies the top
    third, sub occupies the bottom two-thirds.
    """
    shapes = []
    shapes.append(add_rect(slide, x, y, w, h,
                 fill_color=color, border_color=None, corner_radius=True))
    shapes.append(add_text(slide, name,
             x + Inches(0.1), y + Inches(0.18),
             w - Inches(0.2), Inches(0.55),
             size=Pt(24), color=_PIPE_DARK, bold=True,
             align=PP_ALIGN.CENTER))
    shapes.append(add_text(slide, sub,
             x + Inches(0.1), y + Inches(0.82),
             w - Inches(0.2), h - Inches(0.92),
             size=Pt(22), color=_PIPE_DARK, align=PP_ALIGN.CENTER))
    return shapes


def _pipe_arrow(slide, x, y, h_gap, arrow_w, box_h, color=None):
    """Right-arrow connector between pipeline stages."""
    ax = x + h_gap
    ay = y + box_h / 2 - Inches(0.2)
    c = color or TEAL
    return [add_text(slide, "→", ax, ay, arrow_w, Inches(0.4),
                     size=Pt(28), color=c, bold=True,
                     align=PP_ALIGN.CENTER)]


def _pipe_legend(slide, items, y):
    """Compact single-row legend used by both halves of the pipeline."""
    shapes = []
    leg_sz = Inches(0.22)
    leg_gap = Inches(2.9)
    leg_start = int((SL_W - len(items) * leg_gap) / 2) + Inches(0.3)
    for i, (lbl, clr) in enumerate(items):
        lx = leg_start + i * leg_gap
        shapes.append(add_rect(slide, lx, y, leg_sz, leg_sz, fill_color=clr))
        shapes.append(add_text(slide, lbl,
                 lx + Inches(0.32), y - Inches(0.04),
                 Inches(2.2), Inches(0.4), size=Pt(20), color=WHITE))
    return shapes


def slide_17_a(prs):
    """8-Stage Pipeline — Part 1 of 2: Preprocessing (stages 1-4 + ASR side-branch)."""
    slide = new_slide(prs)
    add_title(slide, "8-Stage Pipeline (1/2): Preprocessing")
    add_accent_line(slide)

    BLUE   = _PIPE_BLUE
    SCORAL = _PIPE_SCORAL

    # Stages 1, 2, 4 in the main flow (slot 2 is reserved for the vertical
    # drop into the ASR side-branch box below).
    main = [
        ("1. Normalize", "HDR / 10-bit\nconversion", BLUE),
        ("2. Mouth Crop", "Face detect\n& ROI", BLUE),
        ("4. LRS3 Convert", "Flat → LRS3\nformat", BLUE),
    ]

    # Layout — 4 slots wide with arrows between (slot 2 is reserved for the
    # vertical drop to the ASR side-branch below).
    box_w = Inches(2.6)
    box_h = Inches(1.8)
    h_gap = Inches(0.18)
    arrow_w = Inches(0.22)
    step = box_w + h_gap + arrow_w + h_gap
    total_w = 4 * box_w + 3 * (h_gap + arrow_w + h_gap)
    start_x = int((SL_W - total_w) / 2)
    row_y = CT + Inches(0.25)
    lw = Inches(0.04)

    anim_groups = []

    # ── Slot 0: Normalize ──
    x0 = start_x
    anim_groups.append(_pipe_box(slide, *main[0], x0, row_y, box_w, box_h))

    # ── Arrow 0→1 + Slot 1: Mouth Crop ──
    x1 = start_x + 1 * step
    grp1 = (_pipe_arrow(slide, x0 + box_w, row_y, h_gap, arrow_w, box_h)
            + _pipe_box(slide, *main[1], x1, row_y, box_w, box_h))
    anim_groups.append(grp1)

    # ── Long arrow Mouth Crop → LRS3 Convert (skipping ASR slot) ──
    x3 = start_x + 3 * step
    long_arrow_start_x = x1 + box_w + h_gap
    long_arrow_end_x = x3 - h_gap
    long_arrow_w = long_arrow_end_x - long_arrow_start_x
    long_arrow_cy = row_y + box_h / 2
    long_arrow_grp = [
        add_rect(slide, long_arrow_start_x, long_arrow_cy - lw / 2,
                 long_arrow_w, lw, fill_color=TEAL, border_color=None),
        add_text(slide, "▶",
                 long_arrow_end_x - Inches(0.16), long_arrow_cy - Inches(0.16),
                 Inches(0.32), Inches(0.32),
                 size=Pt(28), color=TEAL, align=PP_ALIGN.CENTER),
    ]

    # Slot 3: LRS3 Convert
    grp3 = long_arrow_grp + _pipe_box(slide, *main[2], x3, row_y, box_w, box_h)
    anim_groups.append(grp3)

    # ── ASR side-branch: drops from main flow into a box below slot 2 ──
    asr_x = start_x + 2 * step
    asr_y = row_y + box_h + Inches(0.6)
    asr_grp = []

    branch_cx = asr_x + box_w / 2
    branch_top_y = long_arrow_cy + lw / 2
    asr_grp.append(add_rect(slide, branch_cx - lw / 2, branch_top_y,
                             lw, asr_y - branch_top_y - Inches(0.20),
                             fill_color=SCORAL, border_color=None))
    asr_grp.append(add_text(slide, "▼",
                    branch_cx - Inches(0.16), asr_y - Inches(0.32),
                    Inches(0.32), Inches(0.4),
                    size=Pt(28), color=SCORAL, align=PP_ALIGN.CENTER))

    # ASR box
    asr_grp += _pipe_box(slide, "3. ASR", "Whisper\ntranscription",
                         BLUE, asr_x, asr_y, box_w, box_h)

    # "evaluation only — feeds stage 8 outputs" annotation to the right.
    asr_grp.append(add_text(slide, "evaluation only —\nfeeds stage 8 outputs",
                    asr_x + box_w + Inches(0.18), asr_y + Inches(0.55),
                    Inches(2.4), Inches(0.9),
                    size=Pt(20), color=SCORAL, italic=True, bold=True,
                    align=PP_ALIGN.LEFT))

    anim_groups.append(asr_grp)

    # ── Legend (single category for this slide) ──
    final_group = []
    legend_y = asr_y + box_h + Inches(0.30)
    final_group += _pipe_legend(slide, [("Preprocessing", BLUE)], legend_y)

    # Continuation hint
    final_group.append(add_text(slide,
             "Continued on next slide → stages 5–8 (Decoding & Output)",
             start_x, legend_y + Inches(0.42), total_w, Inches(0.32),
             size=Pt(20), color=MGRAY, italic=True, align=PP_ALIGN.CENTER))
    anim_groups.append(final_group)

    _finish(slide, 0,
        "Pipeline part 1/2: preprocessing stages 1-4. Main flow: normalize "
        "(HDR/10-bit conversion), mouth crop (face detect & ROI), LRS3 convert "
        "(flat → LRS3 format). ASR (Whisper) sits as a side-branch — "
        "it provides reference text for evaluation (WER/IS scoring) only, "
        "not part of the core lip-reading inference path. Stages 5-8 "
        "(decoding and output) on the next slide.",
        anim_groups, click_reveal=True)


def slide_17_b(prs):
    """8-Stage Pipeline — Part 2 of 2: Decoding + Output (stages 5-8)."""
    slide = new_slide(prs)
    add_title(slide, "8-Stage Pipeline (2/2): Decoding + Output")
    add_accent_line(slide)

    SGREEN = _PIPE_SGREEN
    SGOLD  = _PIPE_SGOLD
    SPINK  = _PIPE_SPINK

    stages = [
        ("5. Manifests",  "TSV + splits",            SGREEN),
        ("6. K-means",    "Feature\nclustering",     SGREEN),
        ("7. LLM Decode", "AV-HuBERT +\nLLaMA-2",    SGOLD),
        ("8. Outputs",    "Reports &\nburned video", SPINK),
    ]

    box_w = Inches(2.6)
    box_h = Inches(1.8)
    h_gap = Inches(0.18)
    arrow_w = Inches(0.22)
    step = box_w + h_gap + arrow_w + h_gap
    total_w = 4 * box_w + 3 * (h_gap + arrow_w + h_gap)
    start_x = int((SL_W - total_w) / 2)
    row_y = CT + Inches(0.50)

    anim_groups = []

    # Build stage boxes + connecting arrows.
    stage_groups = []
    for i, (name, sub, color) in enumerate(stages):
        x = start_x + i * step
        grp = _pipe_box(slide, name, sub, color, x, row_y, box_w, box_h)
        if i > 0:
            ax = start_x + (i - 1) * step + box_w
            grp = _pipe_arrow(slide, ax, row_y, h_gap, arrow_w, box_h) + grp
        stage_groups.append(grp)

    # Red outline highlighting stages 6-7 (existed in academic repo).
    s6_x = start_x + 1 * step
    s7_x = start_x + 2 * step
    red_box_x = s6_x - Inches(0.1)
    red_box_w = (s7_x + box_w) - s6_x + Inches(0.2)
    red_box = add_rect(slide, red_box_x, row_y - Inches(0.12),
                       red_box_w, box_h + Inches(0.24),
                       fill_color=None, border_color=RED, border_width=Pt(2.5),
                       corner_radius=True)
    red_label = add_text(slide, "Existed in academic repo",
                         red_box_x, row_y - Inches(0.55),
                         red_box_w, Inches(0.42),
                         size=Pt(22), color=RED, bold=True,
                         align=PP_ALIGN.CENTER)

    # Group reveals: stages 5+6+red highlight, then 7+8.
    anim_groups.append(stage_groups[0] + stage_groups[1] + [red_box, red_label])
    anim_groups.append(stage_groups[2] + stage_groups[3])

    # ── Legend ──
    final_group = []
    legend_y = row_y + box_h + Inches(0.55)
    final_group += _pipe_legend(slide, [
        ("Feature Extraction", SGREEN),
        ("LLM Inference", SGOLD),
        ("Output", SPINK),
    ], legend_y)

    # Repo attribution
    final_group.append(add_text(slide,
             "auto_avsr  ·  av_hubert  ·  VSP-LLM",
             start_x, legend_y + Inches(0.42), total_w, Inches(0.32),
             size=Pt(20), color=MGRAY, italic=True, align=PP_ALIGN.CENTER))
    anim_groups.append(final_group)

    _finish(slide, 0,
        "Pipeline part 2/2: stages 5-8. Manifests build TSV + splits, K-means "
        "clusters AV-HuBERT features, LLM decode runs AV-HuBERT + LLaMA-2 to "
        "produce hypotheses, outputs generate reports and burned videos. "
        "Stages 6-7 (K-means and LLM Decode) existed in the academic repo; "
        "all other stages were engineered from scratch.",
        anim_groups, click_reveal=True)


# SLIDE 17b — PIPELINE ARCHITECTURE (PNG version)
# ═══════════════════════════════════════════════════════════════════════

def slide_17_png(prs):
    """8-Stage Pipeline — full-slide PNG version (from PPTX slide 50)."""
    slide = new_slide(prs)
    add_title(slide, "8-Stage Automated Pipeline")
    add_accent_line(slide)

    add_image(slide, "pipeline_detailed", MX, CT, width=CW)

    _finish(slide, 0,
        "Full pipeline diagram showing 8 stages with ASR as evaluation-only "
        "side-branch. Data flow: .mp4 → normalize → mouth crop → LRS3 convert "
        "→ manifests → K-means → LLM decode → reports. ASR (Whisper) provides "
        "reference text for WER/IS scoring only.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 18 — ENGINEERING JOURNEY
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 18 — ENGINEERING JOURNEY
# ═══════════════════════════════════════════════════════════════════════

def slide_18(prs):
    """Engineering journey: integration, migration, bug fixing."""
    slide = new_slide(prs)
    add_title(slide, "Building the Pipeline: The Engineering Journey")
    add_accent_line(slide)

    # Three phase cards
    cw_card = Inches(3.6)
    ch_card = Inches(4.5)
    gap_card = Inches(0.5)
    total = 3 * cw_card + 2 * gap_card
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.1)

    phases = [
        {
            "title": "Pipeline Build",
            "subtitle": "~2\u20133 weeks",
            "color": TEAL,
            "items": [
                "3 independent repos with no docs",
                "Hardcoded paths everywhere",
                "No error handling or logging",
                "Built 8-stage orchestration\npipeline from scratch",
                "Added venv management,\nGPU detection, logging",
            ],
        },
        {
            "title": "Migration",
            "subtitle": "~4\u20135 weeks",
            "color": CORAL,
            "items": [
                "EC2 \u2192 Docker container",
                "Missing NVIDIA GPU drivers",
                "Python version conflicts",
                "Offline dependency packaging\n(no internet in container)",
                "spaCy wheels, fairseq patches,\nCython compilation",
                "Web UI migration (1\u20132 weeks\nwithin this phase)",
            ],
        },
        {
            "title": "Bug Fixing &\nRefactoring",
            "subtitle": "Ongoing",
            "color": GREEN,
            "items": [
                "37+ bugs found and fixed",
                "NVENC silent corruption\n(destroyed 43% of videos)",
                "HDR/10-bit tone mapping",
                "823-line monolith \u2192 11 modules\n(52% reduction)",
                "37 automated tests added",
            ],
        },
    ]

    card_groups = []  # list of lists — each inner list = all shapes for one card
    for i, phase in enumerate(phases):
        x = cx + i * (cw_card + gap_card)
        card = []
        card.append(add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=phase["color"], border_width=Pt(2.5),
                     corner_radius=True))
        card.append(add_text(slide, phase["title"],
                 x + Inches(0.2), cy + Inches(0.15),
                 cw_card - Inches(0.4), Inches(0.55),
                 size=Pt(24), color=phase["color"], bold=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_text(slide, phase["subtitle"],
                 x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.3),
                 size=Pt(18), color=LGRAY, italic=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_bullets(slide, phase["items"],
                    x + Inches(0.15), cy + Inches(1.1),
                    cw_card - Inches(0.3), Inches(3.2),
                    size=Pt(24)))
        card_groups.append(card)

    bottom = add_text(slide,
        "Every bug documented with root cause. Every change synced between "
        "EC2 and production container.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(24), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 18,
        "The full engineering journey: 2-3 weeks of pipeline build, 4-5 weeks of "
        "migration to Docker (including 1-2 weeks for Web UI migration), and "
        "ongoing bug fixing. 37+ bugs including NVENC silent corruption. "
        "Refactored from 823-line monolith to 11 reusable modules.",
        card_groups + [[bottom]], click_reveal=True, para_build=False)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 19 — MODULAR REFACTORING (BEFORE/AFTER)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 19 — MODULAR REFACTORING (BEFORE/AFTER)
# ═══════════════════════════════════════════════════════════════════════

def slide_19(prs):
    slide = new_slide(prs)
    add_title(slide, "52% Code Reduction: 823 → 393 Lines")
    add_accent_line(slide)

    bw = Inches(5.5)
    bh = Inches(4.5)
    by = CT
    gap = Inches(1.13)

    # BEFORE box (coral)
    r1 = add_rect(slide, MX, by, bw, bh, fill_color=NAVY2,
                  border_color=CORAL, border_width=Pt(3), corner_radius=True)
    add_text(slide, "BEFORE", MX + Inches(0.3), by + Inches(0.2),
             bw - Inches(0.6), Inches(0.4),
             size=Pt(30), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "Monolithic 823-line script",
        "Fragile, untestable",
        "No environment detection",
        "Hardcoded paths everywhere",
    ], MX + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(24), bullet_color=CORAL)

    # AFTER box (teal)
    rx = MX + bw + gap
    r2 = add_rect(slide, rx, by, bw, bh, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(3), corner_radius=True)
    add_text(slide, "AFTER", rx + Inches(0.3), by + Inches(0.2),
             bw - Inches(0.6), Inches(0.4),
             size=Pt(30), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "393-line orchestrator + 11 modules in lib/",
        ("37 automated tests", {"color": TEAL}),
        "Each stage independently testable",
        "Auto-detects EC2 vs container",
    ], rx + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(24), bullet_color=TEAL)

    _finish(slide, 19,
        "The original pipeline was a single 823-line bash script. Refactored "
        "into a 393-line orchestrator calling 11 reusable modules. 37 "
        "automated tests validate every module. Environment-aware: "
        "automatically detects EC2 development vs Docker container.",
        [[r1], [r2]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 20 — DEPLOYED PRODUCT
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 20 — DEPLOYED PRODUCT
# ═══════════════════════════════════════════════════════════════════════

def slide_20(prs):
    build_bullets(prs, 20,
        "Standalone Container — No Cloud Required",
        [
            "Docker container with web UI on Linux machine",
            "Drag-and-drop video upload",
            "Automatic end-to-end processing",
            "INSTALL.sh overlay with backup and verification",
            ("Currently deployed at client site", {"color": TEAL, "bold": True}),
        ],
        "The system runs as a standalone Docker container — no cloud, no "
        "internet required. Web UI for drag-and-drop video upload. "
        "INSTALL.sh handles deployment with automatic backup and 13-point "
        "verification. Currently deployed and running at the client site.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 21 — INTELLIGENT FEATURES (3 CARDS)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 21 — INTELLIGENT FEATURES (3 CARDS)
# ═══════════════════════════════════════════════════════════════════════

def slide_21(prs):
    slide = new_slide(prs)
    add_title(slide, "Pipeline Intelligence")
    add_accent_line(slide)

    cards = [
        ("Transcription Reuse",
         "Manual corrections persist across runs. Whisper skips matched "
         "segments, saving hours.", TEAL),
        ("Golden K-means",
         "1,396-video baseline clustering model for consistent feature "
         "extraction.", CORAL),
        ("Smart Segmentation",
         "Configurable overlap for context preservation across segment "
         "boundaries.", LGRAY),
        ("Intelligibility Score (IS)",
         "0\u20135 composite of 6 signals. Rubric and weights "
         "designed once, distilled into deterministic code "
         "(no LLM calls at runtime). Validated: r=0.93, "
         "\u03ba=0.77 across 16 configs.", GREEN),
    ]

    cw = Inches(2.7)
    ch = Inches(4.0)
    gap = Inches(0.35)
    total = 4 * cw + 3 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.2)

    card_groups = []
    for i, (title, desc, color) in enumerate(cards):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, cy, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        t1 = add_text(slide, title, x + Inches(0.15), cy + Inches(0.3),
                 cw - Inches(0.3), Inches(1.0),
                 size=Pt(24), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, desc, x + Inches(0.15), cy + Inches(0.95),
                 cw - Inches(0.3), Inches(2.7),
                 size=Pt(24), color=WHITE)
        card_groups.append([r, t1, t2])

    _finish(slide, 21,
        "Four intelligent features.\n\n"
        "SMART SEGMENTATION — HOW OVERLAP IS HANDLED:\n"
        "Long videos are split into segments (default 30s) with configurable "
        "overlap (default 2s). Each segment shares 2 seconds of video with its "
        "neighbor. After decode, the pipeline has two hypotheses for the overlap "
        "zone. The merge strategy selects the hypothesis from the segment that "
        "decoded the overlap zone with higher confidence (beam score). This means "
        "the 'best' decode of the boundary region is always used. In practice, "
        "analysis of 33 Obama segments showed 13 of 21 overlaps had a clear quality "
        "winner — 7 times the previous segment won, 6 times the next segment won. "
        "This confirms the overlap strategy captures context from both directions.\n\n"
        "TRANSCRIPTION REUSE: Manual .wrd corrections saved to .transcriptions/ "
        "directory. On re-run, exact filename matching copies them back. Whisper "
        "skips any segment with an existing .wrd file.\n\n"
        "GOLDEN K-MEANS: A 1,396-video baseline clustering model ensures consistent "
        "feature extraction across runs.\n\n"
        "IS: 0-5 composite of 6 signals, designed at development time and distilled "
        "into deterministic formulas. No LLM called at runtime.",
        card_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 22 — EVALUATION INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 22 — EVALUATION INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_22(prs):
    build_split(prs, 22, "Evaluation: Beyond Standard WER", "cdf_wwer",
        bullets=[
            "16 analytical plots per experiment (auto-generated)",
            "Per-segment HTML reports (13 interactive)",
            "Custom NEA metric for entity accuracy",
            "Intelligibility Score pipeline (LLM-distilled, 6 signals)",
            "IS correlation analysis (16 configs, r=0.925)",
            "Failure mode classification (5 categories)",
            "Topic/length analysis (11 categories)",
            ("Fine-tuning diagnostics (10 training plots)", {"color": TEAL}),
        ],
        notes="Evaluation infrastructure goes far beyond standard WER. "
              "16 plots auto-generated per experiment. Interactive HTML "
              "reports. Custom Named Entity Accuracy metric. Full IS "
              "pipeline validated across 16 decode configs.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 23 — PROCESS & DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 23 — PROCESS & DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════

def slide_23(prs):
    build_bullets(prs, 23,
        "Engineering Process",
        [
            "40+ git versions with semantic tags",
            "EC2/container sync protocol (26 tracked items)",
            "8 formal research reports + methodology docs",
            "Complete architecture, development, and bug documentation",
            "Automated test suite and verification",
        ],
        "Rigorous engineering process. Over 40 git versions with semantic "
        "tagging. EC2-to-container sync protocol tracking 26 items. "
        "Eight formal research reports. Full architecture and development "
        "documentation.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 24 — REFRAMING THE STARTING POINT
# ═══════════════════════════════════════════════════════════════════════

def slide_eng_transition(prs):
    """Section divider: entering engineering portion."""
    slide = new_slide(prs)

    # Large centered section title
    add_text(slide, "ENGINEERING",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(52), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "From Research Code to Production System",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(30), color=LGRAY, align=PP_ALIGN.CENTER)

    # Subtle accent line
    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=TEAL)

    add_text(slide, "3 research repositories  \u2192  1 automated pipeline  \u2192  deployed container",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(22), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Section transition: we now move from research analysis to the "
        "engineering work that turned three research codebases into a "
        "production-ready system.")


def slide_three_repos(prs):
    """Starting point: three research codebases."""
    slide = new_slide(prs)
    add_title(slide, "Starting Point: Three Research Codebases")
    add_accent_line(slide)

    repos = [
        ("auto_avsr", "Preprocessing",
         "Face detection, mouth cropping,\nvideo normalization",
         TEAL),
        ("av_hubert", "Feature Extraction",
         "AV-HuBERT encoder,\nK-means clustering",
         CORAL),
        ("VSP-LLM", "Inference",
         "LLaMA-2 integration,\ndecode & generation",
         GREEN),
    ]

    cw_card = Inches(3.6)
    ch_card = Inches(2.8)
    gap = Inches(0.5)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.2)

    card_groups = []
    for i, (name, role, desc, color) in enumerate(repos):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5), corner_radius=True)
        t1 = add_text(slide, name, x + Inches(0.2), cy + Inches(0.2),
                 cw_card - Inches(0.4), Inches(0.45),
                 size=Pt(28), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, role, x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)
        t3 = add_text(slide, desc, x + Inches(0.2), cy + Inches(1.3),
                 cw_card - Inches(0.4), Inches(1.2),
                 size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)
        card_groups.append([r, t1, t2, t3])

    # Bottom bullets
    bul = add_bullets(slide, [
        "No documentation, no tests, no integration",
        "Research-grade code: hardcoded paths, no error handling",
        ("Each runs independently \u2014 no orchestration between them",
         {"bold": True}),
        "Required 37 bug fixes to reach production quality",
    ], MX, cy + ch_card + Inches(0.3), CW, Inches(2.0), size=Pt(24))

    _finish(slide, 0,
        "We started with three independent research codebases: auto_avsr for "
        "preprocessing, av_hubert for feature extraction, and VSP-LLM for "
        "inference. No documentation, no tests, no integration between them. "
        "Research-grade code with hardcoded paths and no error handling. "
        "Required 37 bug fixes to reach production quality.",
        [card_groups[0], card_groups[1], card_groups[2], [bul]])


def slide_web_ui(prs):
    """Live demo announcement slide."""
    slide = new_slide(prs)
    add_title(slide, "Live Demo")
    add_accent_line(slide)

    # Big centered demo announcement
    add_text(slide, "\u25b6",
             MX, CT + Inches(0.3), CW, Inches(1.5),
             size=Pt(96), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    add_text(slide, "We will now run the full pipeline live",
             MX, CT + Inches(2.0), CW, Inches(0.6),
             size=Pt(36), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "Upload a video  \u2192  8-stage processing  \u2192  "
        "Per-segment results with IS scores",
        MX, CT + Inches(2.8), CW, Inches(0.5),
        size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # Three feature highlights at bottom
    features = [
        ("\u2601", "Drag & Drop", "No command line"),
        ("\u2699", "8 Stages", "Fully automatic"),
        ("\u2714", "IS Scoring", "Per-segment quality"),
    ]
    fw = Inches(3.2)
    fgap = Inches(0.8)
    ftotal = 3 * fw + 2 * fgap
    fx = (SL_W - ftotal) / 2
    fy = CT + Inches(3.8)

    for i, (icon, title, desc) in enumerate(features):
        x = fx + i * (fw + fgap)
        add_rect(slide, x, fy, fw, Inches(1.2), fill_color=NAVY2,
                 border_color=TEAL, border_width=Pt(1), corner_radius=True)
        add_text(slide, icon, x, fy + Inches(0.05), fw, Inches(0.4),
                 size=Pt(32), color=TEAL, align=PP_ALIGN.CENTER)
        add_text(slide, title, x, fy + Inches(0.45), fw, Inches(0.3),
                 size=Pt(24), color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, desc, x, fy + Inches(0.8), fw, Inches(0.3),
                 size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Switch to live demo now. The web UI provides drag-and-drop video upload, "
        "real-time pipeline progress display, and per-segment results with IS scores. "
        "Under the hood: 8 pipeline stages run automatically — normalize, mouth crop, "
        "ASR, LRS3 prep, manifests, K-means clustering, decode, and report generation.")


def slide_dual_env(prs):
    """Two environments — EC2 and container."""
    slide = new_slide(prs)
    add_title(slide, "Two Environments: Development and Production")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — EC2 vs Container comparison
    lt = add_text(slide, "EC2 (Development)", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    b1 = add_bullets(slide, [
        "Full research environment",
        "GPU: Tesla T4 (16GB)",
        "Path: /home/ubuntu/",
        "All datasets and evaluation tools",
    ], MX + Inches(0.2), CT + Inches(0.6), col_w - Inches(0.4), Inches(2.2),
       size=Pt(24))

    ct_label = add_text(slide, "Container (Production)", MX, CT + Inches(2.3), col_w,
             Inches(0.4), size=Pt(24), color=CORAL, bold=True)

    r2 = add_rect(slide, MX, CT + Inches(2.8), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    b2 = add_bullets(slide, [
        "Docker container, no internet",
        "GPU: client hardware",
        "Path: /workspace/",
        "Pipeline + web UI only",
    ], MX + Inches(0.2), CT + Inches(2.9), col_w - Inches(0.4), Inches(2.2),
       size=Pt(24))

    # Right — sync challenges
    rx = MX + col_w + gap
    rt = add_text(slide, "Synchronization Challenge", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    rb = add_bullets(slide, [
        "Every EC2 change must be replicated to container",
        "Path translations (/home/ubuntu/ \u2192 /workspace/)",
        "Different Python environments and dependencies",
        ("Detailed sync changelog with exact code diffs", {"color": TEAL}),
        "INSTALL.sh overlay with 13-point verification",
    ], rx, CT + Inches(0.6), col_w, Inches(4.2), size=Pt(24))

    _finish(slide, 0,
        "Two environments: EC2 for development and research, Docker container "
        "for production deployment. Changes are tracked and replicated via a "
        "detailed sync changelog. Path translations, different Python environments, "
        "different hardware. INSTALL.sh handles deployment with automatic backup "
        "and 13-point verification.",
        [[lt, r1, b1, ct_label, r2, b2],
         [rt, rb]],
        click_reveal=True, para_build=False)


# ═══════════════════════════════════════════════════════════════════════
# ENGINEERING SUMMARY — "What We Engineered" overview (May 2026)
# ═══════════════════════════════════════════════════════════════════════
# Caps the §5 demo block before the future-roadmap transition: a
# mid-research recap of the production engineering effort that
# turned the VSP-LLM paper into a deployable system.

def slide_engineering_summary(prs):
    """Six-card overview of the engineering effort behind the system."""
    slide = new_slide(prs)
    add_title(slide, "What We Engineered")
    add_accent_line(slide)

    cards = [
        ("Modular Pipeline",
         "823-line monolith →\n11 lib/ modules\n(52% reduction, 37 tests)",
         TEAL),
        ("Single-Image Docker",
         "One tar.zst, one tag.\nNo layered patches.\nOffline-ready.",
         CORAL),
        ("EC2 ↔ Container Sync",
         "26-item changelog.\nPath translation,\ndual-env testing.",
         GOLD),
        ("Confidence + N-best",
         "Per-word colors (Apr 30).\nMBR default (May 1–2).\nAgreement-aware bands.",
         GREEN),
        ("UI + Reports",
         "Drag-drop web UI.\nCSV / HTML / burned\nMP4 outputs per run.",
         BLUE),
        ("Re-run on Past Videos",
         "Stage-8 re-paint.\nNo re-decode needed\nfor band upgrades.",
         PURPLE),
    ]

    cw_card = Inches(3.9)
    ch_card = Inches(2.45)
    gap_x = Inches(0.25)
    gap_y = Inches(0.25)
    total_w = 3 * cw_card + 2 * gap_x
    cx = (SL_W - total_w) / 2
    cy = CT + Inches(0.15)

    card_groups = []
    for i, (title, desc, color) in enumerate(cards):
        col = i % 3
        row = i // 3
        x = cx + col * (cw_card + gap_x)
        y = cy + row * (ch_card + gap_y)
        r = add_rect(slide, x, y, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5),
                     corner_radius=True)
        t1 = add_text(slide, title, x + Inches(0.15), y + Inches(0.18),
                 cw_card - Inches(0.3), Inches(0.5),
                 size=Pt(26), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, desc, x + Inches(0.15), y + Inches(0.78),
                 cw_card - Inches(0.3), ch_card - Inches(0.9),
                 size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)
        card_groups.append([r, t1, t2])

    _finish(slide, 0,
        "Recap of the engineering effort behind the system. Six cards: "
        "(1) modular pipeline refactor — 823-line bash monolith broken into "
        "11 reusable lib/ modules with a 37-test suite. "
        "(2) Single-image Docker deployment — one tag, one tar.zst, no "
        "layered patches, fully offline-ready (per single-docker-image "
        "decision). "
        "(3) EC2 ↔ container sync protocol — 26 tracked items in a "
        "detailed changelog, path translation, dual-environment testing "
        "before every deploy. "
        "(4) Per-word confidence shipped April 30 2026, N-best aggregation "
        "shipped May 1, MBR-as-default plus agreement-aware bands May 2. "
        "(5) UI + report stack — drag-drop web upload, automatic CSV/HTML/"
        "burned-video outputs per run. "
        "(6) Past-video re-run path — stage-8 re-paint upgrades existing "
        "outputs to current band/MBR policy without re-decoding. "
        "Speaker note: emphasize 'we shipped this from a paper, not a "
        "product' — the original three repos had no orchestration, no "
        "tests, no docs.",
        card_groups, click_reveal=True, para_build=False)


# ═══════════════════════════════════════════════════════════════════════
# ENGINEERING — 11 PIPELINE MODULES (lib/ grid)
# ═══════════════════════════════════════════════════════════════════════

def slide_engineering_pipeline_modules(prs):
    """Grid of the 11 modular shell modules under lib/."""
    slide = new_slide(prs)
    add_title(slide, "11 Modules: lib/ Architecture")
    add_accent_line(slide)

    # 4 rows x 3 cols = 12 cells, last cell empty (only 11 modules).
    modules = [
        ("common.sh",        "Logging\n& validation",       TEAL),
        ("config.sh",        "Env detect\n& path config",   TEAL),
        ("archive.sh",       "Run archival\n+ transcripts", TEAL),
        ("normalization.sh", "HDR / 10-bit\nconversion",    BLUE),
        ("asr.sh",           "Whisper +\nreuse logic",      BLUE),
        ("lrs3_prep.sh",     "Flat → LRS3\nformat",     BLUE),
        ("manifests.sh",     "TSV + splits\n+ timing",      GOLD),
        ("clustering.sh",    "K-means +\ncluster counts",   GOLD),
        ("decode.sh",        "VSP-LLM +\nCython check",     CORAL),
        ("outputs.sh",       "Reports +\nburned video",     CORAL),
        ("venv_utils.sh",    "venv activate\n/ deactivate", GREEN),
        # 12th cell intentionally empty.
    ]

    cols = 3
    rows = 4
    cw_card = Inches(3.6)
    ch_card = Inches(1.25)
    gap_x = Inches(0.25)
    gap_y = Inches(0.18)
    total_w = cols * cw_card + (cols - 1) * gap_x
    cx = (SL_W - total_w) / 2
    cy = CT + Inches(0.05)

    card_groups = []
    for i, (name, desc, color) in enumerate(modules):
        col = i % cols
        row = i // cols
        x = cx + col * (cw_card + gap_x)
        y = cy + row * (ch_card + gap_y)
        r = add_rect(slide, x, y, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2),
                     corner_radius=True)
        t1 = add_text(slide, name, x + Inches(0.15), y + Inches(0.10),
                 cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(24), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, desc, x + Inches(0.15), y + Inches(0.58),
                 cw_card - Inches(0.3), ch_card - Inches(0.65),
                 size=Pt(18), color=WHITE, align=PP_ALIGN.CENTER, italic=True)
        card_groups.append([r, t1, t2])

    # Caption line at the bottom — italic 18pt floor.
    cap_y = cy + rows * ch_card + (rows - 1) * gap_y + Inches(0.18)
    cap = add_text(slide,
        "393-line orchestrator drives the 11 modules; 37 tests cover them.",
        MX, cap_y, CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "The lib/ directory holds 11 shell modules, grouped by phase: "
        "infrastructure (common, config, archive), normalization, "
        "processing stages (asr, lrs3_prep, manifests, clustering), "
        "decode + outputs, and venv utilities. "
        "Each module exports functions consumable by the orchestrator OR "
        "by external scripts; each is independently testable. "
        "Color groups in the grid: teal = infrastructure, blue = "
        "preprocessing, gold = manifests/clustering, coral = decode/outputs, "
        "green = venv. "
        "decode.sh has a critical Cython auto-build check — fairseq's "
        "data_utils_fast must compile against the container's Python+CPU; "
        "this step prevents silent decode failure on first container run. "
        "asr.sh activates its own venv (ASR_VENV); the rest share VSP_VENV "
        "for efficiency. "
        "outputs.sh on EC2 also computes IS scores; the container version "
        "skips IS by design (no sentence-transformers dependency).",
        card_groups + [[cap]], click_reveal=True, para_build=False)


# ═══════════════════════════════════════════════════════════════════════
# ENGINEERING — WHAT SHIPPED THIS QUARTER (timeline)
# ═══════════════════════════════════════════════════════════════════════

def slide_engineering_what_shipped(prs):
    """Timeline of features shipped April-May 2026."""
    slide = new_slide(prs)
    add_title(slide, "What Shipped This Quarter")
    add_accent_line(slide)

    events = [
        ("Apr 30",  "Per-word\nconfidence",
         "Colored words in\nreport.html + CSV", TEAL),
        ("May 1",   "N-best\naggregation",
         "5 methods:\nMBR, vote, safe...", CORAL),
        ("May 2",   "MBR\nas default",
         "+40 Y+P wins\n(p=0.0002)",          GOLD),
        ("May 2",   "Agreement-aware\nbands",
         "Joint conf +\nbeam-agreement",      GREEN),
        ("May 3",   "Burned-video\ncolors",
         "Per-word tier\n+ IS badge",         PURPLE),
    ]

    n = len(events)
    cw_card = Inches(2.35)
    ch_card = Inches(3.6)
    gap = Inches(0.18)
    total_w = n * cw_card + (n - 1) * gap
    cx = (SL_W - total_w) / 2
    cy = CT + Inches(0.35)

    # Timeline rail under the row of cards.
    rail_y = cy + ch_card + Inches(0.30)
    rail = add_rect(slide, cx, rail_y, total_w, Inches(0.06),
                    fill_color=TEAL, border_color=None)

    card_groups = []
    for i, (date, title, desc, color) in enumerate(events):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5),
                     corner_radius=True)
        d = add_text(slide, date, x + Inches(0.15), cy + Inches(0.18),
                 cw_card - Inches(0.3), Inches(0.5),
                 size=Pt(24), color=LGRAY, bold=True, align=PP_ALIGN.CENTER)
        t1 = add_text(slide, title, x + Inches(0.15), cy + Inches(0.85),
                 cw_card - Inches(0.3), Inches(1.1),
                 size=Pt(26), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, desc, x + Inches(0.15), cy + Inches(2.10),
                 cw_card - Inches(0.3), ch_card - Inches(2.25),
                 size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)
        # Tick mark on the rail under each card.
        tick_x = x + cw_card / 2 - Inches(0.06)
        tick = add_rect(slide, tick_x, rail_y - Inches(0.10),
                        Inches(0.12), Inches(0.26),
                        fill_color=color, border_color=None)
        card_groups.append([r, d, t1, t2, tick])

    cap = add_text(slide,
        "Five production-ready features, six work-days. All synced to container.",
        MX, rail_y + Inches(0.30), CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Timeline of features shipped between April 30 and May 3, 2026. "
        "Apr 30: per-word confidence shipped to production — report.csv "
        "gains sentence_confidence + 2 cols, report.html colors each word "
        "blue/orange/purple beside the existing accuracy line. "
        "May 1: Mission 6 N-best aggregation lands — 5 offline methods "
        "(MBR, score-vote, conf-vote, safe, xseg-merge), gated by "
        "VSP_NBEST=1; tuning-set validated with hyp_vote_conf -2.15pp WER. "
        "May 2: MBR adopted as the production default displayed output "
        "(judge p=0.0002 on Y+P, +40 paired wins); agreement-aware bands "
        "land same day — joint top1_conf >= 0.95 AND beam_agreement >= 0.80 "
        "for green. "
        "May 3: burned-video colors ship — per-word tier coloring + IS "
        "tier badge baked into the MP4 output. "
        "Container overlay synced for every item; vsp_docker/ rebuild "
        "deferred per single-image policy.",
        card_groups + [[cap, rail]], click_reveal=True, para_build=False)
