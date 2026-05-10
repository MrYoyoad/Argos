"""
New / merged slide builders for Argos VSP v13 Amosi deck.

These slides have no direct equivalent in the existing slides_*.py modules.
Reverse-engineered from `presentation_materials_20260224/Argos_VSP_v13_Amosi_2.pptx`.
"""
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from .config import (
    IMG, VID,
    SL_W, SL_H, BG, WHITE, TEAL, CORAL, LGRAY, MGRAY, DGRAY,
    GREEN, YELLOW, GOLD, ORANGE, RED, DRED, NAVY2, NAVY3,
    BLUE, PURPLE,
    MX, MY, CT, CW, CH, SLW, SRG, SRL, SRW,
)
from .helpers import (
    new_slide, add_title, add_text, add_rect, add_image, add_bullets,
    add_accent_line, add_table, _finish,
)


# ─────────────────────────────────────────────────────────────────────────
# v13 #2 — Thesis
# ─────────────────────────────────────────────────────────────────────────
def slide_thesis(prs):
    """Thesis statement: Argos is a calibrated review tool, not automation."""
    slide = new_slide(prs)
    add_title(slide, "Thesis")
    add_accent_line(slide)

    headline = add_text(slide,
        "Argos is not automatic transcription.",
        MX + Inches(0.5), Inches(2.5), CW - Inches(1.0), Inches(0.6),
        size=Pt(28), color=CORAL, bold=True)

    body = add_text(slide,
        "It is a calibrated review tool for silent video — surfacing meaningful signal "
        "where it exists, marking uncertainty where it doesn't, and routing every segment "
        "through a trust layer so high-confidence output, partial signal, and unreliable "
        "output are visibly distinct.",
        MX + Inches(0.5), Inches(3.1), CW - Inches(1.0), Inches(1.8),
        size=Pt(24), color=WHITE)

    tagline = add_text(slide,
        "Reviewable visual-speech intelligence. Uncertainty attached.",
        MX, Inches(5.95), CW, Inches(0.5),
        size=Pt(22), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Thesis slide. Frames the deck's central claim: Argos is a calibrated review "
        "tool, NOT automatic transcription. The trust layer (per-word confidence "
        "bands + segment-level tiers) is the load-bearing feature that distinguishes "
        "this from an ASR-style system.",
        [[headline, body, tagline]], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #3 — What we claim — and what we do not claim
# ─────────────────────────────────────────────────────────────────────────
def slide_what_we_claim(prs):
    """Two-column claims / non-claims contrast."""
    slide = new_slide(prs)
    add_title(slide, "What we claim — and what we do not claim")
    add_accent_line(slide)

    sub = add_text(slide,
        "Where the line is. So you know what you're getting.",
        MX, CT, CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Two columns
    col_w = (CW - Inches(0.3)) / 2
    cy_top = CT + Inches(0.5)
    row_h = Inches(0.7)
    row_gap = Inches(0.08)

    # Headers
    claim_header = add_rect(slide, MX, cy_top, col_w, Inches(0.5),
                            fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                            corner_radius=True)
    add_text(slide, "WE CLAIM", MX, cy_top + Inches(0.08),
             col_w, Inches(0.35), size=Pt(22), color=GREEN, bold=True,
             align=PP_ALIGN.CENTER)

    nope_x = MX + col_w + Inches(0.3)
    nope_header = add_rect(slide, nope_x, cy_top, col_w, Inches(0.5),
                            fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                            corner_radius=True)
    add_text(slide, "WE DO NOT CLAIM", nope_x, cy_top + Inches(0.08),
             col_w, Inches(0.35), size=Pt(22), color=CORAL, bold=True,
             align=PP_ALIGN.CENTER)

    claims = [
        "Recover useful speech candidates from video-only input.",
        "Per-word confidence flags numerics, names, and uncertain spans for review.",
        "Many dangerous failure modes flagged before review.",
        "Reduce reviewer workload by routing attention to suspicious spans.",
    ]
    non_claims = [
        "Perfect lip-reading.",
        "Reliably preserve negation, named entities, or numeric values without verification.",
        "Every hallucination is caught.",
        "Replace human judgment for time-critical decisions.",
    ]

    row_y = cy_top + Inches(0.6)
    shapes = []
    for claim, non_claim in zip(claims, non_claims):
        # Left card (claim)
        r1 = add_rect(slide, MX, row_y, col_w, row_h,
                      fill_color=NAVY2, border_color=GREEN, border_width=Pt(1),
                      corner_radius=True)
        add_text(slide, "✓  " + claim,
                 MX + Inches(0.2), row_y + Inches(0.10),
                 col_w - Inches(0.4), row_h - Inches(0.2),
                 size=Pt(18), color=WHITE)
        # Right card (non-claim)
        r2 = add_rect(slide, nope_x, row_y, col_w, row_h,
                      fill_color=NAVY2, border_color=CORAL, border_width=Pt(1),
                      corner_radius=True)
        add_text(slide, "✗  " + non_claim,
                 nope_x + Inches(0.2), row_y + Inches(0.10),
                 col_w - Inches(0.4), row_h - Inches(0.2),
                 size=Pt(18), color=WHITE)
        shapes.extend([r1, r2])
        row_y += row_h + row_gap

    # Bottom callout
    bot_y = row_y + Inches(0.05)
    bot_rect = add_rect(slide, MX, bot_y, CW, Inches(0.5),
                        fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                        corner_radius=True)
    add_text(slide,
        "Not blind automation. Reviewable visual-speech intelligence with uncertainty attached.",
        MX, bot_y + Inches(0.08), CW, Inches(0.40),
        size=Pt(20), color=TEAL, italic=True, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Claims/anti-claims contrast — sets honest scope for the rest of the deck.",
        [[sub] + shapes], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #33 — Intelligibility Score: 61.6% Useful Output
# ─────────────────────────────────────────────────────────────────────────
def slide_is_61pct_headline(prs):
    """Headline IS results slide with the 61.6% useful-output number."""
    slide = new_slide(prs)
    add_title(slide, "Intelligibility Score: 61.6% Useful Output")
    add_accent_line(slide)

    sub = add_text(slide,
        "On 1,497 real-world YouTube segments under MBR n-best aggregation.",
        MX, CT, CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Big number
    add_text(slide, "61.6%",
             MX, CT + Inches(0.55), CW, Inches(1.5),
             size=Pt(96), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    add_text(slide, "of segments deliver useful output (IS ≥ 2.00 = NIV-Y+P)",
             MX, CT + Inches(2.15), CW, Inches(0.5),
             size=Pt(22), color=WHITE, align=PP_ALIGN.CENTER)

    # Tier distribution mini-bar
    tier_y = CT + Inches(2.95)
    tier_w = Inches(2.2)
    tier_gap = Inches(0.15)
    total_tier_w = 5 * tier_w + 4 * tier_gap
    tier_start_x = (SL_W - total_tier_w) // 2

    tiers = [
        ("5 — Excellent",  "18.4%", "276 seg",  GREEN),
        ("4 — Good",       "21.4%", "321 seg",  TEAL),
        ("3 — Fair",       "21.7%", "325 seg",  GOLD),
        ("2 — Poor",       "22.4%", "336 seg",  ORANGE),
        ("1 — Failed",     "16.0%", "239 seg",  CORAL),
    ]
    for i, (label, pct, n, color) in enumerate(tiers):
        x = tier_start_x + i * (tier_w + tier_gap)
        r = add_rect(slide, x, tier_y, tier_w, Inches(1.30),
                     fill_color=NAVY2, border_color=color, border_width=Pt(2),
                     corner_radius=True)
        add_text(slide, label, x + Inches(0.1), tier_y + Inches(0.08),
                 tier_w - Inches(0.2), Inches(0.35),
                 size=Pt(18), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, pct, x + Inches(0.1), tier_y + Inches(0.42),
                 tier_w - Inches(0.2), Inches(0.55),
                 size=Pt(28), color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, n, x + Inches(0.1), tier_y + Inches(0.95),
                 tier_w - Inches(0.2), Inches(0.30),
                 size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Bottom comparison
    add_text(slide,
        "Compare to WER: 64% — would call this a failure. IS reveals the truth.",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(18), color=GOLD, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Headline IS result: 61.6% of segments deliver useful output (NIV-Y+P, "
        "IS≥2.00 calibrated against Opus-as-Judge). 5-tier distribution shows where "
        "the segments fall. WER 64% on the same set would call this a failure — IS "
        "reveals 61.6% are actually useful.",
        [[sub]], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #38 — Four Numbers That Tell the Real Story
# ─────────────────────────────────────────────────────────────────────────
def slide_four_numbers(prs):
    """Stack of 4 headline numbers."""
    slide = new_slide(prs)
    add_title(slide, "Four Numbers That Tell the Real Story")
    add_accent_line(slide)

    sub = add_text(slide,
        "WER says fail. Two independent metrics say usable. Confidence makes it actionable.",
        MX, CT, CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    rows = [
        ("25.4%", "Paper WER on LRS3 (curated TED talks, controlled conditions)", LGRAY),
        ("61.6%", "IS — useful output by our 6-signal Intelligibility Score (IS≥2.0)", TEAL),
        ("64.9%", "Opus-as-Judge — useful by independent LLM evaluation (Y+P, blind)", GREEN),
        ("~65%",  "Convergent answer — both metrics agree the model works", GOLD),
    ]

    row_h = Inches(1.0)
    row_gap = Inches(0.15)
    start_y = CT + Inches(0.55)
    for i, (num, desc, color) in enumerate(rows):
        y = start_y + i * (row_h + row_gap)
        r = add_rect(slide, MX, y, CW, row_h,
                     fill_color=NAVY2, border_color=color, border_width=Pt(2),
                     corner_radius=True)
        add_text(slide, num,
                 MX + Inches(0.3), y + Inches(0.12),
                 Inches(2.4), Inches(0.8),
                 size=Pt(48), color=color, bold=True, align=PP_ALIGN.LEFT)
        add_text(slide, desc,
                 MX + Inches(2.9), y + Inches(0.30),
                 CW - Inches(3.2), Inches(0.6),
                 size=Pt(22), color=WHITE)

    _finish(slide, 0,
        "Four numbers framing: WER (paper benchmark) vs IS (our metric) vs Judge "
        "(independent LLM) vs convergent. Sets up the rest of the eval section.",
        [[sub]], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #47 — How IS and Confidence Correlate (merged)
# ─────────────────────────────────────────────────────────────────────────
def slide_is_conf_correlate_combined(prs):
    """Merge of slide_is_conf_correlation + slide_is_conf_contingency on one slide."""
    slide = new_slide(prs)
    add_title(slide, "How IS and Confidence Correlate")
    add_accent_line(slide)

    sub = add_text(slide,
        "Two independent signals — IS (deterministic) and mean per-word confidence — converge on n=1,427.",
        MX, CT, CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Left: scalar correlations
    card_w = Inches(5.85)
    gap = Inches(0.43)
    cy = CT + Inches(0.55)

    L_card = add_rect(slide, MX, cy, card_w, Inches(2.8),
                      fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                      corner_radius=True)
    add_text(slide, "SCALAR CORRELATION",
             MX + Inches(0.2), cy + Inches(0.1), card_w - Inches(0.4), Inches(0.35),
             size=Pt(22), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    rows = [
        ("Pearson r(IS, mean_prob)", "+0.837"),
        ("Spearman ρ(IS, mean_prob)", "+0.854"),
        ("Pearson r(IS, ⟨log p⟩)", "+0.760"),
    ]
    ry = cy + Inches(0.55)
    for label, val in rows:
        add_text(slide, label,
                 MX + Inches(0.25), ry, card_w - Inches(2.0), Inches(0.4),
                 size=Pt(20), color=WHITE)
        add_text(slide, val,
                 MX + card_w - Inches(1.7), ry, Inches(1.4), Inches(0.4),
                 size=Pt(24), color=GREEN, bold=True, align=PP_ALIGN.RIGHT)
        ry += Inches(0.55)
    add_text(slide,
             "Rank correlation 0.854 — IS and confidence rank segments nearly identically.",
             MX + Inches(0.2), cy + Inches(2.30), card_w - Inches(0.4), Inches(0.45),
             size=Pt(16), color=LGRAY, italic=True)

    # Right: binary 2x2 + tier kappa
    rx = MX + card_w + gap
    R_card = add_rect(slide, rx, cy, card_w, Inches(2.8),
                      fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                      corner_radius=True)
    add_text(slide, "TIER + BINARY AGREEMENT",
             rx + Inches(0.2), cy + Inches(0.1), card_w - Inches(0.4), Inches(0.35),
             size=Pt(22), color=GOLD, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "κ (3-tier × 3-tier) = 0.498   (moderate)",
             rx + Inches(0.2), cy + Inches(0.55), card_w - Inches(0.4), Inches(0.35),
             size=Pt(20), color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "κ_binary = 0.71   (substantial)",
             rx + Inches(0.2), cy + Inches(0.95), card_w - Inches(0.4), Inches(0.35),
             size=Pt(20), color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "86% raw agreement on useful / not-useful",
             rx + Inches(0.2), cy + Inches(1.35), card_w - Inches(0.4), Inches(0.35),
             size=Pt(20), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Adjacent (±1 tier) agreement: 98% — off-diagonal cases mostly Trust↔Salvage.",
             rx + Inches(0.2), cy + Inches(1.85), card_w - Inches(0.4), Inches(0.75),
             size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # 2x2 contingency table
    tbl_y = cy + Inches(3.0)
    headers = ["", "Conf trusted", "Conf stripped", "Total"]
    rows_data = [
        ["IS useful (Y+P)",  "797",  "126",  "923"],
        ["IS not useful",    "78",   "426",  "504"],
        ["Total",            "875",  "552",  "1,427"],
    ]
    row_colors = {
        0: {1: GREEN, 2: ORANGE},
        1: {1: CORAL, 2: GREEN},
    }
    tbl = add_table(slide, headers, rows_data,
                    MX + Inches(2.0), tbl_y, Inches(8.13),
                    row_height=Inches(0.45),
                    col_widths=[Inches(2.5), Inches(2.0), Inches(2.0), Inches(1.63)],
                    text_size=Pt(18), row_colors=row_colors)

    add_text(slide,
             "Thresholds: IS ≥ 2.00 (Y+P) × mean_prob ≥ 0.65 (above strip-coloring boundary).",
             MX, Inches(6.55), CW, Inches(0.4),
             size=Pt(16), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Combined IS×Confidence correlation slide for v13: scalar correlations (left "
        "card), tier+binary kappa (right card), 2×2 contingency table (below). Source: "
        "intelligibility_scores.csv × word_confidence_v2.json on n=1,427.",
        [[sub, L_card, R_card, tbl]], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #64 — 10-Stage Pipeline (merge of 17_a + 17_b, rebadged 8→10)
# ─────────────────────────────────────────────────────────────────────────
def slide_pipeline_10stage(prs):
    """10-stage pipeline (8 decode stages + 2 trust-layer stages)."""
    slide = new_slide(prs)
    add_title(slide, "10-Stage Pipeline: 8 Decode Stages + Trust Layer")
    add_accent_line(slide)

    sub = add_text(slide,
        "8 decode stages produce the hypothesis. 2 trust-layer stages decide what to show.",
        MX, CT, CW, Inches(0.4),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # 10 stages in 2 rows of 5
    stages = [
        ("1. Normalize",      "HDR/10-bit\nconversion",   BLUE),
        ("2. Mouth Crop",     "Face detect\n& ROI",       BLUE),
        ("3. ASR",            "Whisper\n(eval only)",     CORAL),
        ("4. LRS3 Convert",   "Flat → LRS3",              BLUE),
        ("5. Manifests",      "TSV + splits",             GREEN),
        ("6. K-means",        "Feature\nclustering",      GREEN),
        ("7. LLM Decode",     "AV-HuBERT +\nLLaMA-2",     GOLD),
        ("8. Outputs",        "Reports +\nburned video",  ORANGE),
        ("9. Aggregate",      "MBR over 20\nn-best",      TEAL),
        ("10. Confidence",    "Per-word\np₁ + α bands",   TEAL),
    ]

    cols = 5
    box_w = Inches(2.30)
    box_h = Inches(1.55)
    h_gap = Inches(0.10)
    v_gap = Inches(0.30)
    total_row_w = cols * box_w + (cols - 1) * h_gap
    start_x = (SL_W - total_row_w) // 2
    start_y = CT + Inches(0.65)

    for i, (name, desc, color) in enumerate(stages):
        row = i // cols
        col = i % cols
        x = start_x + col * (box_w + h_gap)
        y = start_y + row * (box_h + v_gap)
        r = add_rect(slide, x, y, box_w, box_h,
                     fill_color=color, border_color=None, corner_radius=True)
        add_text(slide, name,
                 x + Inches(0.08), y + Inches(0.10),
                 box_w - Inches(0.16), Inches(0.45),
                 size=Pt(18), color=RGBColor(0x0D, 0x1B, 0x2A), bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide, desc,
                 x + Inches(0.08), y + Inches(0.55),
                 box_w - Inches(0.16), Inches(0.95),
                 size=Pt(16), color=RGBColor(0x0D, 0x1B, 0x2A),
                 align=PP_ALIGN.CENTER)

    # Trust-layer highlight on stages 9-10
    s9_x = start_x + 3 * (box_w + h_gap)  # col 3 in row 1
    s10_x = start_x + 4 * (box_w + h_gap)  # col 4 in row 1
    trust_y = start_y + (box_h + v_gap) - Inches(0.10)
    trust_box = add_rect(slide,
                         s9_x - Inches(0.10),
                         trust_y,
                         (box_w + h_gap) * 2 - h_gap + Inches(0.20),
                         box_h + Inches(0.20),
                         fill_color=None, border_color=TEAL, border_width=Pt(2.5),
                         corner_radius=True)
    add_text(slide, "TRUST LAYER",
             s9_x, trust_y + box_h + Inches(0.10),
             (box_w + h_gap) * 2 - h_gap, Inches(0.30),
             size=Pt(18), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Bottom note
    add_text(slide,
        "Decode stages 1–8 produce the candidate. Trust stages 9–10 mark uncertainty so reviewers know where to look.",
        MX, Inches(6.40), CW, Inches(0.55),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Pipeline as 10 stages (was 8 in the academic split slide_17_a/b). Stages "
        "9 (Aggregate, MBR n-best) and 10 (Confidence, per-word p₁+α) were added "
        "April 30 / May 1 2026 as the 'trust layer' that distinguishes Argos from "
        "raw decode output.",
        [[sub]], click_reveal=False)


# ─────────────────────────────────────────────────────────────────────────
# v13 #66 — What it actually took (lift from slides_client)
# ─────────────────────────────────────────────────────────────────────────
def slide_engineering_journey_v13(prs):
    """Lift of slide_client_engineering_journey, reframed for academic audience."""
    # Lazy import to avoid circular issues in modules
    try:
        from .slides_client import slide_client_engineering_journey
        return slide_client_engineering_journey(prs)
    except (ImportError, AttributeError) as e:
        # Fallback stub
        slide = new_slide(prs)
        add_title(slide, "What it actually took — four passes, six months")
        add_accent_line(slide)
        add_text(slide, f"[lift target missing: {e}]",
                 MX, CT, CW, Inches(0.6),
                 size=Pt(20), color=CORAL, italic=True, align=PP_ALIGN.CENTER)
        return slide


# ─────────────────────────────────────────────────────────────────────────
# v13 #79 — Optional add-on: pre-filter low-quality clips (lift from slides_client)
# ─────────────────────────────────────────────────────────────────────────
def slide_quality_filter_v13(prs):
    """Lift of slide_client_quality_filter, reframed for academic audience."""
    try:
        from .slides_client import slide_client_quality_filter
        return slide_client_quality_filter(prs)
    except (ImportError, AttributeError) as e:
        slide = new_slide(prs)
        add_title(slide, "Optional add-on — pre-filter low-quality clips before decode")
        add_accent_line(slide)
        add_text(slide, f"[lift target missing: {e}]",
                 MX, CT, CW, Inches(0.6),
                 size=Pt(20), color=CORAL, italic=True, align=PP_ALIGN.CENTER)
        return slide
