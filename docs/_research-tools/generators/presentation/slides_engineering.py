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
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_17(prs):
    """8-Stage Pipeline — per-stage wipe reveal with connector arrows."""
    slide = new_slide(prs)
    add_title(slide, "8-Stage Automated Pipeline")
    add_accent_line(slide)

    add_text(slide, "3 research repos \u2192 single orchestrated system",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    BLUE   = RGBColor(0x4D, 0xD0, 0xE1)
    SGREEN = RGBColor(0x66, 0xBB, 0x6A)
    SGOLD  = RGBColor(0xFF, 0xCA, 0x28)
    SPINK  = RGBColor(0xEF, 0x9A, 0x9A)
    DARK   = RGBColor(0x0D, 0x1B, 0x2A)
    DARK2  = RGBColor(0x1A, 0x2A, 0x3A)

    row1_stages = [
        ("1", "Normalize", "HDR/10-bit\nconversion", BLUE, ".mp4"),
        ("2", "ASR", "Whisper\ntranscription", BLUE, ".wrd"),
        ("3", "Mouth Crop", "Face detection\n& ROI extract", BLUE, ".mp4 (crop)"),
        ("4", "LRS3 Convert", "Flat \u2192 LRS3\nformat", BLUE, "LRS3/"),
    ]
    row2_stages = [
        ("5", "Manifests", "TSV + splits\ngeneration", SGREEN, ".tsv"),
        ("6", "K-means", "Feature\nextraction", SGREEN, ".npy"),
        ("7", "LLM Decode", "AV-HuBERT +\nLLaMA-2", SGOLD, "text"),
        ("8", "Outputs", "Reports &\nburned video", SPINK, ".json"),
    ]

    box_w = Inches(2.65)
    box_h = Inches(1.6)
    gap = Inches(0.35)
    arrow_w = Inches(0.25)
    total_w = 4 * box_w + 3 * gap
    start_x = (SL_W - total_w) / 2
    row1_y = CT + Inches(0.7)
    row2_y = row1_y + box_h + Inches(0.9)

    def _draw_one_stage(num, name, sub, color, fmt_label, x, y_top):
        """Draw one stage box. Returns list of shapes for this stage."""
        shapes = []
        shapes.append(add_text(slide, fmt_label,
                 x, y_top - Inches(0.25), box_w, Inches(0.22),
                 size=Pt(10), color=LGRAY, align=PP_ALIGN.CENTER))
        shapes.append(add_rect(slide, x, y_top, box_w, box_h,
                     fill_color=color, border_color=None))
        shapes.append(add_text(slide, f"{num}. {name}",
                 x + Inches(0.1), y_top + Inches(0.15),
                 box_w - Inches(0.2), Inches(0.45),
                 size=Pt(18), color=DARK, bold=True,
                 align=PP_ALIGN.CENTER))
        shapes.append(add_text(slide, sub,
                 x + Inches(0.1), y_top + Inches(0.65),
                 box_w - Inches(0.2), Inches(0.7),
                 size=Pt(13), color=DARK2, align=PP_ALIGN.CENTER))
        return shapes

    def _add_arrow(x, y, direction="right"):
        """Add connector arrow. Returns list with one shape."""
        if direction == "right":
            return [add_text(slide, "\u2192", x, y + box_h / 2 - Inches(0.15),
                             arrow_w, Inches(0.3), size=Pt(18), color=TEAL,
                             bold=True, align=PP_ALIGN.CENTER)]
        else:  # down
            return [add_text(slide, "\u2193", x, y, Inches(0.3), Inches(0.4),
                             size=Pt(18), color=TEAL, bold=True,
                             align=PP_ALIGN.CENTER)]

    # Build per-stage animation groups
    anim_groups = []

    # Group 0: Input label (visible on entry)
    input_label = [add_text(slide, ".mp4\n\nVideo\nInput",
                   MX, row1_y + Inches(0.15),
                   Inches(0.8), box_h - Inches(0.3),
                   size=Pt(11), color=LGRAY, bold=True, align=PP_ALIGN.CENTER)]
    anim_groups.append(input_label)

    # Groups 1-4: Row 1 stages with arrows
    for i, (num, name, sub, color, fmt) in enumerate(row1_stages):
        x = start_x + i * (box_w + gap)
        stage_shapes = _draw_one_stage(num, name, sub, color, fmt, x, row1_y)
        if i > 0:
            ax = start_x + (i - 1) * (box_w + gap) + box_w
            stage_shapes = _add_arrow(ax, row1_y, "right") + stage_shapes
        anim_groups.append(stage_shapes)

    # Group 5: Down arrow + repo labels for row 1
    down_x = (SL_W - Inches(0.3)) / 2
    down_y = row1_y + box_h + Inches(0.15)
    down_group = _add_arrow(down_x, down_y, "down")
    down_group.append(add_text(slide, "auto_avsr",
             start_x + 2 * (box_w + gap), row1_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))
    anim_groups.append(down_group)

    # Groups 6-9: Row 2 stages with arrows
    for i, (num, name, sub, color, fmt) in enumerate(row2_stages):
        x = start_x + i * (box_w + gap)
        stage_shapes = _draw_one_stage(num, name, sub, color, fmt, x, row2_y)
        if i > 0:
            ax = start_x + (i - 1) * (box_w + gap) + box_w
            stage_shapes = _add_arrow(ax, row2_y, "right") + stage_shapes
        anim_groups.append(stage_shapes)

    # Group 10: Output label + repo labels + legend
    final_group = []
    final_group.append(add_text(slide, ".json\n\nReports\n& Videos",
                    SL_W - MX - Inches(0.8), row2_y + Inches(0.15),
                    Inches(0.8), box_h - Inches(0.3),
                    size=Pt(11), color=LGRAY, bold=True, align=PP_ALIGN.CENTER))
    final_group.append(add_text(slide, "av_hubert",
             start_x, row2_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))
    final_group.append(add_text(slide, "VSP-LLM",
             start_x + 2 * (box_w + gap), row2_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))

    legend_y = Inches(6.8)
    legend_items = [
        ("Preprocessing", BLUE), ("Feature Processing", SGREEN),
        ("LLM Inference", SGOLD), ("Output Generation", SPINK),
    ]
    leg_w = Inches(0.25)
    leg_h = Inches(0.25)
    leg_gap = Inches(2.8)
    leg_start = (SL_W - 4 * leg_gap) / 2 + Inches(0.3)
    for i, (lbl, clr) in enumerate(legend_items):
        lx = leg_start + i * leg_gap
        final_group.append(add_rect(slide, lx, legend_y, leg_w, leg_h,
                                 fill_color=clr))
        final_group.append(add_text(slide, lbl,
                 lx + Inches(0.35), legend_y - Inches(0.02),
                 Inches(2.0), Inches(0.3), size=Pt(12), color=WHITE))
    anim_groups.append(final_group)

    # Group 11: Pipeline visual strip — video transformation through stages
    visual_strip = []
    vis_img = add_image(slide, "pipeline_visual", MX, row2_y + box_h + Inches(0.45),
                        width=CW, height=Inches(1.5))
    if vis_img is not None:
        visual_strip.append(vis_img)
        anim_groups.append(visual_strip)

    # Use wipe animation for per-stage sequential reveal
    _auto_num[0] += 1
    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    add_fade_transition(slide)
    try:
        add_wipe_animation(slide, anim_groups, click_reveal=True, dur_ms=400)
    except Exception:
        add_animations(slide, anim_groups, click_reveal=True)
    set_notes(slide,
        "8-stage automated pipeline built from 3 research repos. "
        "Each stage reveals sequentially with a wipe animation. "
        "Row 1: Normalize, ASR, Mouth Crop, LRS3 Convert (preprocessing). "
        "Row 2: Manifests, K-means, LLM Decode, Outputs (processing). "
        "Final click reveals the visual transformation strip showing how a video "
        "signal flows through the pipeline: raw face → mouth crop → features → "
        "LLM decode → output text with IS score.")

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
                 size=Pt(18), color=phase["color"], bold=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_text(slide, phase["subtitle"],
                 x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.3),
                 size=Pt(12), color=LGRAY, italic=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_bullets(slide, phase["items"],
                    x + Inches(0.15), cy + Inches(1.1),
                    cw_card - Inches(0.3), Inches(3.2),
                    size=Pt(11)))
        card_groups.append(card)

    bottom = add_text(slide,
        "Every bug documented with root cause. Every change synced between "
        "EC2 and production container.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

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
             size=Pt(22), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "Monolithic 823-line script",
        "Fragile, untestable",
        "No environment detection",
        "Hardcoded paths everywhere",
    ], MX + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(15), bullet_color=CORAL)

    # AFTER box (teal)
    rx = MX + bw + gap
    r2 = add_rect(slide, rx, by, bw, bh, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(3), corner_radius=True)
    add_text(slide, "AFTER", rx + Inches(0.3), by + Inches(0.2),
             bw - Inches(0.6), Inches(0.4),
             size=Pt(22), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "393-line orchestrator + 11 modules in lib/",
        ("37 automated tests", {"color": TEAL}),
        "Each stage independently testable",
        "Auto-detects EC2 vs container",
    ], rx + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(15), bullet_color=TEAL)

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
         "IS = 0-5 composite of 6 signals (semantic, phonetic, WER, WWER, "
         "NEA, length ratio). Rubric, weights, tiers, "
         "and failure taxonomy designed at development time — distilled into "
         "deterministic code (no LLM API calls at runtime). "
         "Validated: r=0.925 across 16 configs, 88.6% agreement. "
         "6 signals collapse into 3 independent dimensions (PCA).", GREEN),
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
                 cw - Inches(0.3), Inches(0.5),
                 size=Pt(16), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, desc, x + Inches(0.15), cy + Inches(0.95),
                 cw - Inches(0.3), Inches(2.7),
                 size=Pt(12), color=WHITE)
        card_groups.append([r, t1, t2])

    _finish(slide, 21,
        "Four intelligent features. Transcription reuse: manual corrections "
        "persist across runs. Golden k-means: consistent clustering baseline. "
        "Smart segmentation: configurable overlap. Intelligibility Score: the IS is "
        "a 0-5 composite score combining 6 signals — semantic similarity (25%), "
        "phonetic similarity (15%), inverse WER (15%), inverse WWER (15%), "
        "Named Entity Accuracy F1 (15%), and length ratio (15%). The entire "
        "framework was designed at development time: the rubric, signal selection "
        "and weights, tier boundaries (Excellent/Good/Fair/Poor/Failed), 10 "
        "failure modes, and 7 success patterns. These were then distilled into "
        "deterministic formulas — no LLM is called per sample at runtime. "
        "Correlation analysis shows the 6 signals collapse into 3 independent "
        "dimensions: word accuracy (WER/WWER/Phonetic, r>0.79, ~60% of IS), "
        "meaning preservation (Semantic, 28.5%), and output sanity (Length, "
        "9.1%). Cross-config validation across 16 decode configs: r=0.925, "
        "88.6% agreement, Cohen's kappa 0.773.",
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
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    # Subtle accent line
    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=TEAL)

    add_text(slide, "3 research repositories  \u2192  1 automated pipeline  \u2192  deployed container",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, None,
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
                 size=Pt(20), color=color, bold=True, align=PP_ALIGN.CENTER)
        t2 = add_text(slide, role, x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)
        t3 = add_text(slide, desc, x + Inches(0.2), cy + Inches(1.3),
                 cw_card - Inches(0.4), Inches(1.2),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)
        card_groups.append([r, t1, t2, t3])

    # Bottom bullets
    bul = add_bullets(slide, [
        "No documentation, no tests, no integration",
        "Research-grade code: hardcoded paths, no error handling",
        ("Each runs independently \u2014 no orchestration between them",
         {"bold": True}),
        "Required 37 bug fixes to reach production quality",
    ], MX, cy + ch_card + Inches(0.3), CW, Inches(2.0), size=Pt(14))

    _finish(slide, 0,
        "We started with three independent research codebases: auto_avsr for "
        "preprocessing, av_hubert for feature extraction, and VSP-LLM for "
        "inference. No documentation, no tests, no integration between them. "
        "Research-grade code with hardcoded paths and no error handling. "
        "Required 37 bug fixes to reach production quality.",
        [card_groups[0], card_groups[1], card_groups[2], [bul]])


def slide_web_ui(prs):
    """User experience — web UI and pipeline stages."""
    slide = new_slide(prs)
    add_title(slide, "User Experience: Web Interface")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — web UI features
    lt = add_text(slide, "Web UI Features", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Drag-and-drop video upload",
        "Real-time pipeline progress display",
        "Side-by-side burned video comparison",
        "Per-segment JSON reports with all metrics",
        "Single-click processing start",
        ("No command line needed", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(14))

    # Right — UI screenshot placeholder
    rx = MX + col_w + gap
    ph = add_rect(slide, rx, CT, col_w, Inches(4.0),
                  fill_color=NAVY2, border_color=LGRAY, border_width=Pt(1),
                  corner_radius=True)
    add_text(slide, "UI Screenshot",
             rx, CT + Inches(1.5), col_w, Inches(0.5),
             size=Pt(20), color=MGRAY, align=PP_ALIGN.CENTER)
    add_text(slide, "(will be added from running server)",
             rx, CT + Inches(2.1), col_w, Inches(0.4),
             size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "The web UI provides a simple drag-and-drop interface for non-technical "
        "users. Under the hood, 8 pipeline stages run automatically. Each stage "
        "is a modular component that can be tested independently.",
        [[lt, lb], [ph]], click_reveal=True)


def slide_dual_env(prs):
    """Two environments — EC2 and container."""
    slide = new_slide(prs)
    add_title(slide, "Two Environments: Development and Production")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — EC2 vs Container comparison
    lt = add_text(slide, "EC2 (Development)", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    b1 = add_bullets(slide, [
        "Full research environment",
        "GPU: Tesla T4 (16GB)",
        "Path: /home/ubuntu/",
        "All datasets and evaluation tools",
    ], MX + Inches(0.2), CT + Inches(0.6), col_w - Inches(0.4), Inches(1.2),
       size=Pt(13))

    ct_label = add_text(slide, "Container (Production)", MX, CT + Inches(2.3), col_w,
             Inches(0.4), size=Pt(18), color=CORAL, bold=True)

    r2 = add_rect(slide, MX, CT + Inches(2.8), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    b2 = add_bullets(slide, [
        "Docker container, no internet",
        "GPU: client hardware",
        "Path: /workspace/",
        "Pipeline + web UI only",
    ], MX + Inches(0.2), CT + Inches(2.9), col_w - Inches(0.4), Inches(1.2),
       size=Pt(13))

    # Right — sync challenges
    rx = MX + col_w + gap
    rt = add_text(slide, "Synchronization Challenge", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)

    big_num = add_text(slide, "26", rx, CT + Inches(0.6), col_w, Inches(0.7),
             size=Pt(48), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    num_label = add_text(slide, "tracked sync items",
             rx, CT + Inches(1.2), col_w, Inches(0.3),
             size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)

    rb = add_bullets(slide, [
        "Every EC2 change must be replicated to container",
        "Path translations (/home/ubuntu/ \u2192 /workspace/)",
        "Different Python environments and dependencies",
        ("Detailed sync changelog with exact code diffs", {"color": TEAL}),
        "INSTALL.sh overlay with 13-point verification",
    ], rx, CT + Inches(1.8), col_w, Inches(3.0), size=Pt(13))

    _finish(slide, 0,
        "Two environments: EC2 for development and research, Docker container "
        "for production deployment. 26 tracked sync items ensure changes are "
        "replicated correctly. Path translations, different Python environments, "
        "different hardware. INSTALL.sh handles deployment with automatic backup "
        "and 13-point verification.",
        [[lt, r1, b1, ct_label, r2, b2],
         [rt, big_num, num_label, rb]],
        click_reveal=True, para_build=False)


