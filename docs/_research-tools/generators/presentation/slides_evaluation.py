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

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 12 — 13 TUNING EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_12(prs):
    # audit:bigfonts — left bullets trimmed 5 -> 3 (cut "Extreme parameters"
    # and "Lenpen=2.0" — both in speaker notes) so Pt(24) fits in h=3.0;
    # explicit size=Pt(24) added to both bullet lists.
    slide = new_slide(prs)
    add_title(slide, "Best Config vs Baseline: The Trade-off")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — What we found
    lt = add_text(slide, "What We Found", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Config J (lenpen=1.0, temp=0.5) was best overall", {"bold": True}),
        "Most configs cluster in narrow IS range (2.45\u20132.60)",
        ("Lenpen=\u22120.5: 45% empty outputs", {"color": CORAL}),
        # ("Extreme parameters cause catastrophic failures",),  # cut bigfonts
        # ("Lenpen=2.0: mean WER 540% (massive hallucination)",),  # cut bigfonts
    ], MX, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(24))

    # Right column — Best Config (J)
    rx = MX + col_w + gap
    rt = add_text(slide, "Best Config (J) — 1,497 segments",
                  rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "IS: 2.60 vs 2.53 baseline (+0.07)",
        ("Captured: 622 vs 601 (+21)", {"color": GREEN}),
        ("Empties: 0 vs 70 (eliminated)", {"color": GREEN}),
        ("Hallucinations: 348 vs 307 (+41)", {"color": CORAL}),
    ], rx, CT + Inches(0.5), col_w, Inches(2.1), size=Pt(24))

    # Right image — before/after tuning comparison
    img = add_image(slide, "tuning_ba", rx, CT + Inches(2.6), width=col_w,
                    height=Inches(3.0))

    _finish(slide, 12,
        "13 systematic experiments across beam size, length penalty, "
        "temperature, and sampling. Config J achieved the best IS. Key "
        "trade-off: eliminated all 70 empty outputs but added 41 "
        "hallucinations. Net IS gain: only +0.08.",
        [[lt, lb], [rt, rb, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

def slide_13(prs):
    # audit:bigfonts — uses build_split helper; bullet font sizing handled
    # by helpers.py (out of scope for this module). Bullets unchanged: 6
    # bullets at the helper's default size, helper handles wrapping.
    build_split(prs, 13, "Tuning Is Mitigation, Not a Cure", "P4_lenpen",
        bullets=[
            ("Config J: eliminates empties but increases hallucinations by 13%",
             {"color": CORAL}),
            "Net IS gain: only +0.08 across 1,497 segments",
            "Cross-config proof: per-segment rankings identical (r > 0.92)",
            ('"Hard" and "easy" segments stay the same — '
             "bottleneck is the visual encoder", {"bold": True}),
            ("Data is the real constraint: 1,273 training segments is "
             "below the ~1K LoRA minimum", {"color": CORAL}),
            ("Three levers remain: scale data (20K+), swap LLM "
             "(Llama 3.1 8B), smart prompts", {"color": TEAL}),
        ],
        notes="Tuning is mitigation, not a cure. Config J's fundamental "
              "trade-off: silent failures (empties) vs noisy failures "
              "(hallucinations). Cross-config analysis proves: per-segment "
              "IS rankings are nearly identical across all 16 configs "
              "(r > 0.92). The bottleneck is the visual encoder AND data "
              "scarcity — 1,273 training segments is below the ~1K minimum "
              "for LoRA generalization. Three levers: (1) scale data to "
              "20K-50K, (2) swap LLM to Llama 3.1 8B, (3) smart prompts.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE — TUNING SUMMARY (condensed)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14 — CURATED EXAMPLES (TABLE)
# ═══════════════════════════════════════════════════════════════════════

def slide_14(prs):
    # audit:bigfonts — explicit text_size=Pt(24), row_height bumped 0.55->0.85
    # so 18pt cells render legibly. Row count unchanged (4 examples).
    slide = new_slide(prs)
    add_title(slide, "Representative Examples")
    add_accent_line(slide)

    headers = ["Category", "Reference", "Hypothesis", "WER", "IS"]
    rows = [
        ["Perfect", "health insurance company they pay...", "[exact match]", "0%", "5.0"],
        ["WER Misleads", "work with the team in a more", "work with a team and more", "29%", "4.3"],
        ["Near-Miss", "1 billion cfus of probiotics", "1 million cfus of permafrost", "58%", "2.7"],
        ["Hallucinated", "carry strap", "holocaust denier", "100%", "0.8"],
    ]
    # Color IS column by value
    row_colors = {
        0: {4: GREEN},
        1: {4: GREEN},
        2: {4: YELLOW},
        3: {4: RED},
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT, CW, row_height=Inches(0.85),
                    col_widths=[Inches(1.7), Inches(3.7), Inches(3.7),
                                Inches(1.0), Inches(1.0)],
                    text_size=Pt(24),
                    row_colors=row_colors)

    _finish(slide, 14,
        "Four examples spanning the quality range. Row 1: perfect lip-reading. "
        "Row 2: WER says 29% error but the meaning is fully preserved — IS 4.3. "
        "Row 3: near-miss — structure intact but key terms phonetically garbled "
        "(probiotics→permafrost). Row 4: complete hallucination — 'carry strap' "
        "becomes 'holocaust denier.' This is why WER alone is insufficient.",
        [[tbl]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_15(prs):
    """Demo slide.

    BLOCKER fix (May 2026): pre-fix audit found orphan animation refs to
    spids ['4','7','10'] (pptx_visual_audit.json, slide 48). Cause: a
    prior version called add_animations directly with stale shape ids.
    Fixed by collecting actual shape handles into per-video click-reveal
    groups passed to _finish - the animation tree now references only
    the shape IDs that exist on this slide. Body font also bumped from
    11pt to 12pt to clear the readability floor.

    audit:bigfonts \u2014 desc text bumped to 18pt; description strings
    rewritten as 2-line summaries to fit. Originals (3-line, included
    \"meaning close, key verb flipped\" etc.) preserved in speaker notes.
    """
    slide = new_slide(prs)
    add_title(slide, "Demo: OK \u2192 Almost There \u2192 Hallucination")
    add_accent_line(slide)

    # Three embedded videos side by side - click each to play
    # VID dict mapping (confirmed correct):
    #   "smartphone"   -> ktMebjnZiSE_3  (consumers want bigger smartphone, IS 4.1)
    #   "street_photo" -> 2HddWQse8Mw_0  (street photography topic right, names lost, IS 2.9)
    #   "halluc"       -> 00MUdHQ7GGY_8  (carry strap -> holocaust denier)
    vid_w = Inches(3.6)
    vid_h = Inches(2.4)  # audit:bigfonts \u2014 was 2.7; shrunk 0.3" for caption room
    gap = Inches(0.4)
    total = 3 * vid_w + 2 * gap
    start_x = (SL_W - total) / 2
    vid_y = CT + Inches(0.1)

    # audit:bigfonts \u2014 descs trimmed to 2 lines so 18pt fits in h=1.05.
    # Leftmost OK tile uses obama_perfect (segment #14, WER 0%, IS 5.00,
    # 27/29 words at conf-high) \u2014 most convincing per-word coloring in the deck.
    vids = [
        ("obama_perfect", '"\u2026the tireless and heroic work of our military"\n\u2192 (perfect \u2014 27/29 words green)', "WER 0%  IS 5.00", TEAL),
        ("street_photo", '"james and will talk about street photography"\n\u2192 "i\'m here to talk about street photography"', "WER 56%  IS 2.9", CORAL),
        ("halluc", '"carry strap"\n\u2192 "holocaust denier"', "WER 100%  IS 0.8", RED),
    ]

    # audit:pptx_visual_audit_after_amosi.md slide 63 BLOCKER -
    # animation referenced movie shape ids ['7','10'] which are wrapped in
    # <mc:AlternateContent>. python-pptx's slide.shapes iterator and the
    # audit's iter_shapes_recursive both skip AlternateContent, so the
    # movies look "non-existent" even though they render fine. Fix: drop
    # video shapes from anim_groups; only animate the captions. Videos
    # still render (they're not animated, so they appear immediately).
    anim_groups = []
    for i, (key, desc, wer, color) in enumerate(vids):
        x = start_x + i * (vid_w + gap)
        add_video(slide, key, x, vid_y, vid_w, vid_h)
        wer_t = add_text(slide, wer, x, vid_y + vid_h + Inches(0.05), vid_w,
                 Inches(0.4), size=Pt(24), color=color, bold=True,
                 align=PP_ALIGN.CENTER)
        # audit:bigfonts — desc h bumped 0.7->1.30 for 18pt 2-line summary.
        desc_t = add_text(slide, desc, x, vid_y + vid_h + Inches(0.45), vid_w,
                 Inches(2.2), size=Pt(24), color=LGRAY,
                 align=PP_ALIGN.CENTER)
        anim_groups.append([wer_t, desc_t])

    # audit:bigfonts2 — foot moved 6.85 -> 6.55 to clear slide-num zone (7.12).
    foot = add_text(slide, "Click each video to play.",
             MX, Inches(6.55), CW, Inches(0.30),
             size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)
    anim_groups.append([foot])

    _finish(slide, 15,
        "Three demos side by side, picked to span the quality range. "
        "LEFT (Obama segment 14, 29 words, the most convincing per-word "
        "coloring in the deck): WER 0%, IS 5.00 — REF and HYP identical "
        "('…and our allies over the last 10 years thanks to the tireless "
        "and heroic work of our military and our counterterrorism "
        "professionals we've made great strides in that effort'). 27 of "
        "29 per-word bands GREEN at conf-high; the remaining 2 yellow. "
        "Sentence_conf 0.72 (Salvage band) — the *segment-level* "
        "confidence is conservative because of two yellow words, but the "
        "WER says zero, IS says perfect. This is exactly the kind of "
        "example that motivates the joint conf+agreement rule explained "
        "earlier in §4. "
        "CENTER ('james and will talk about street photography' → "
        "'i'm here to talk about street photography', IS 2.9): topic "
        "captured perfectly but speaker names lost — the near-miss zone. "
        "RIGHT ('carry strap' → 'holocaust denier', IS 0.8): "
        "hallucination, fluent but completely fabricated. Click each "
        "video to play. Mention to peers: this is the qualitative "
        "bridge from the confidence section into the demo segments that "
        "follow. "
        "Sources: docs/evaluation/intelligibility_methodology.md, "
        "docs/evaluation/llm_judge/llm_judge_analysis.md.",
        anim_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — IS VALIDATION: CLAUDE-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — IS VALIDATION: CLAUDE-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════════

def slide_16(prs):
    # audit:bigfonts — left bullets trimmed (5 -> 4) to fit 18pt; right
    # validation table row_height bumped 0.32->0.50 for legible 16pt cells.
    slide = new_slide(prs)
    add_title(slide, "IS Validation: Design-Time Distilled Evaluation")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: How IS works
    lt = add_text(slide, "How the IS Was Built", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    # audit:bigfonts — cut 5th bullet "Result: reproducible, free,
    # decomposable scoring" (now in speaker notes).
    lb = add_bullets(slide, [
        "Framework designed at development time",
        "6 signals: Semantic 25%, Phonetic 15%, inv.WER 15%, "
        "inv.WWER 15%, NEA F1 15%, Length 15%",
        "5 tiers, 5 failure categories, 7 success patterns",
        ("Distilled into deterministic formulas — no LLM per sample",
         {"bold": True}),
        # ("Result: reproducible, free, decomposable scoring",),  # cut
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(24))

    # Right: Correlation analysis + validation
    rx = MX + col_w + gap
    rt = add_text(slide, "PCA: 2 Dimensions of Quality", rx, CT, col_w,
                  Inches(0.35), size=Pt(24), color=CORAL, bold=True)

    # Two PCA dimensions (actual PCA results)
    dims = [
        ("PC1: Signal Quality", "All 5 content signals load equally (0.43\u20130.47)", "68%", TEAL),
        ("PC2: Output Length", "Length Ratio dominates (loading 0.91)", "20%", LGRAY),
    ]
    dim_y = CT + Inches(0.5)
    for i, (name, signals, pct, color) in enumerate(dims):
        y = dim_y + i * Inches(0.75)
        add_text(slide, name, rx, y, col_w, Inches(0.3),
                 size=Pt(24), color=color, bold=True)
        add_text(slide, f"{signals} \u2014 {pct} of variance",
                 rx + Inches(0.15), y + Inches(0.3), col_w - Inches(0.15),
                 Inches(1.4), size=Pt(24), color=LGRAY)
    add_text(slide, "Together: 88% of total variance (Kaiser criterion)",
             rx + Inches(0.15), dim_y + 2 * Inches(0.75) + Inches(0.1),
             col_w - Inches(0.15), Inches(0.3), size=Pt(24), color=LGRAY)

    # Cross-config validation stats
    add_text(slide, "Cross-Config Validation (16 configs)",
             rx, CT + Inches(2.9), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["LLM heuristic vs IS", "r = 0.925"],
        ["Agreement (IS ≥ 2.00)", "κ = 0.818"],
        ["Recall (IS ≥ 2.00)", "97.6–100%"],
        ["Cohen's κ", "0.773"],
        ["Segment ranking stability", "r > 0.92"],
    ]
    add_table(slide, headers, rows, rx, CT + Inches(3.3), col_w,
              row_height=Inches(0.45),
              col_widths=[Inches(3.0), Inches(2.5)],
              text_size=Pt(24))

    _finish(slide, 16,
        "How the IS was built: the entire framework was designed at development "
        "time — rubric, 6 signals with weights, tier boundaries, failure mode "
        "taxonomy, success patterns. These were then encoded into deterministic "
        "formulas. No LLM is called per sample at runtime.\n\n"
        "PCA RESULTS (Kaiser criterion, 2 PCs retained):\n"
        "PC1 (68%): Signal Quality — all 5 content signals load equally "
        "(0.43-0.47). Semantic is NOT independent of word accuracy.\n"
        "PC2 (20%): Output Length — Length Ratio dominates (0.91). "
        "Independent of content quality.\n"
        "Together: 88% of variance. The visual encoder drives PC1.\n\n"
        "KEY FINDINGS:\n"
        "1. Phonetic Sim is the strongest single predictor (r=0.943) despite "
        "15% weight — most direct measure of visual encoder quality.\n"
        "2. WER is UNRELIABLE across configs — correlation with IS swings from "
        "-0.95 to -0.45 depending on length penalty. This is why IS was created.\n\n"
        "Cross-config validation: r=0.925, recall 97.6-100% across 16 configs. "
        "IS vs Opus judge: κ=0.818 at Y+P (IS≥2.00), κ=0.690 at Y (IS≥3.80).")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_25(prs):
    # audit:bigfonts — bullets trimmed (4 -> 3); hero rect grew 4.6 -> 5.0
    # so 20pt bullets fit; bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate for LLM Judgment")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(5.0), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric — in CORAL for this variant
    add_text(slide, "IS says 62%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments pass (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge — the validation
    add_text(slide, "LLM Judge says 65%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets below
    # audit:bigfonts — cut bullet "LLM-as-a-Judge (blind, 1,497 pairs)
    # confirms: nearly 2 in 3 segments carry useful meaning" (in notes).
    bul = add_bullets(slide, [
        ("IS conservatively undercounts \u2014 real quality higher than 62%",
         {"bold": True, "color": WHITE}),
        ("Gap (62% \u2192 65%) = partial-value segments strict metrics penalize",
         {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(2.1), size=Pt(24))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "Independent LLM judge confirms true useful rate is 3pp higher.",
             MX, Inches(6.55), CW, Inches(0.5),
             size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "IS provides a conservative lower bound for transcription quality. "
        "IS says 62% of segments are useful (IS >= 2.00). But an independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 65% deliver useful output. The 25pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling \u2014 the real quality of the "
        "system is higher than our metric reports.",
        [[r1], [bul]], click_reveal=True)


def slide_25b(prs):
    """LLM Salvage: 6 recovery categories explained."""
    # audit:bigfonts \u2014 categories trimmed 6 -> 4 (cut "Hidden Gems 54" and
    # "WER Over-Punishment 27" \u2014 both still in speaker notes); card height
    # bumped 0.7 -> 0.95 with stride 0.78 -> 1.05 so 18pt name + 16pt desc
    # don't crash. Right-column plot kept; bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: 4 Top Recovery Categories")
    add_accent_line(slide)

    add_text(slide,
        "165 segments that metrics call \u201cfailed\u201d (IS < 2.0) deliver useful "
        "meaning. Top 4 of 6 overlapping categories:",
        MX, CT, CW, Inches(0.45), size=Pt(18), color=LGRAY, italic=True)

    categories = [
        ("Phonetic Bridge", "93", TEAL,
         "Words sound right, spelled differently \u2014 viewer fills in gaps."),
        ("Structure Match", "74", TEAL,
         "Same grammar as reference \u2014 word order + S-V-O preserved."),
        ("Semantic Preservation", "57", GREEN,
         "Core meaning conveyed despite high WER \u2014 like a paraphrase."),
        # ("Hidden Gems", "54", GREEN, ...),  # cut in big-fonts pass
        ("Entity-Preserved", "44", YELLOW,
         "Names + numbers correct even though surrounding words are wrong."),
        # ("WER Over-Punishment", "27", YELLOW, ...),  # cut in big-fonts pass
    ]

    # Cards shrunk from full CW to 7.4" to make room on the right for the
    # newly embedded P_llm_salvage stack plot (MBR-IS, recovery types).
    # Description column also shrinks; text reflows but content preserved.
    card_w = Inches(7.4)
    py = CT + Inches(0.6)
    card_groups = []
    for name, count, color, desc in categories:
        r = add_rect(slide, MX, py, card_w, Inches(0.95), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        t1 = add_text(slide, f"{name} ({count})",
                 MX + Inches(0.2), py + Inches(0.10), Inches(2.6), Inches(0.4),
                 size=Pt(24), color=color, bold=True)
        t2 = add_text(slide, desc,
                 MX + Inches(2.85), py + Inches(0.18),
                 card_w - Inches(2.95), Inches(0.65),
                 size=Pt(24), color=LGRAY)
        card_groups.append([r, t1, t2])
        py += Inches(1.05)

    # Right column \u2014 regenerated P_llm_salvage stack plot (MBR-IS).
    # Same 6 recovery types as the left cards, visualised as a stacked bar.
    img_w = Inches(4.55)
    img_h = Inches(2.2)         # ratio 2.07 \u2192 height 2.20"
    img_x = MX + card_w + Inches(0.15)
    img_y = CT + Inches(0.55)
    img_salvage = add_image(slide, "P_llm_salvage", img_x, img_y,
                            width=img_w, height=img_h)
    cap_salvage = add_text(slide,
        "Right: stacked recovery-types plot (MBR-IS).",
        img_x, img_y + img_h + Inches(0.05), img_w, Inches(0.3),
        size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "Categories overlap \u2014 a segment can exhibit multiple recovery signals.",
        MX, Inches(6.45), CW, Inches(0.35),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "6 salvage categories explained in plain English. Phonetic Bridge is "
        "the largest (93 segments). Categories overlap. Each represents a "
        "different mechanism by which meaning survives despite high WER. "
        "Plot embed (May 2026): the regenerated P_llm_salvage.png stack "
        "lives in the right column \u2014 same 6 recovery types computed against "
        "MBR-IS components, gives the audience a quantitative summary "
        "alongside the per-category descriptions. Cards were shrunk from "
        "full width to 7.4\" and description font dropped from 11pt to "
        "10pt to make room.",
        card_groups + [[img_salvage, cap_salvage]])


def slide_25c(prs):
    """How the salvage detection decision tree works."""
    # audit:bigfonts — see inline comments; right table row_height up,
    # right bullets trimmed.
    slide = new_slide(prs)
    add_title(slide, "How Salvage Detection Works")
    add_accent_line(slide)

    # Flow: Input -> 6 checks -> Score -> Threshold -> Result
    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — the process
    lt = add_text(slide, "Deterministic Decision Tree", MX, CT, col_w, Inches(0.35),
                  size=Pt(24), color=TEAL, bold=True)

    steps = [
        ("1. Input", "Reference + hypothesis text pair", TEAL),
        ("2. Compute 6 signals", "Word overlap, sequence order, phonetic similarity,\n"
         "semantic embedding, entity preservation, length ratio", WHITE),
        ("3. Apply 15 rules", "Decision tree checks signals in priority order,\n"
         "assigns one of 15 probability leaf nodes (0.0 \u2013 1.0)", WHITE),
        ("4. Threshold at 0.5", "Probability \u2265 0.5 = recoverable\n"
         "Probability < 0.5 = likely unrecoverable", WHITE),
        ("5. Classify", "Map to 6 recovery categories based on\n"
         "which signals triggered the high probability", GREEN),
    ]

    py = CT + Inches(0.45)
    step_shapes = []
    for title, desc, color in steps:
        t = add_text(slide, title, MX + Inches(0.1), py, Inches(1.8), Inches(0.3),
                     size=Pt(24), color=color, bold=True)
        add_text(slide, desc, MX + Inches(2.0), py, Inches(3.4), Inches(0.5),
                 size=Pt(24), color=LGRAY)
        step_shapes.append(t)
        py += Inches(0.65)

    # Right — validation stats
    rx = MX + col_w + gap
    rt = add_text(slide, "Validation", rx, CT, col_w, Inches(1.0),
                  size=Pt(24), color=GREEN, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["Correlation with IS", "r = 0.934"],
        ["Agreement (IS \u2265 2.00)", "\u03ba = 0.818"],
        ["Agreement (IS \u2265 3.80)", "\u03ba = 0.690"],
        ["Recall (IS \u2265 2.00)", "97.6\u2013100%"],
        ["Cross-config stability", "r = 0.925 \u00b1 0.015"],
    ]
    # audit:bigfonts \u2014 table row_height bumped 0.4 -> 0.5; bullets trimmed
    # 3 -> 2 (cut "Recall 97.6-100% across 16 decode configurations" \u2014 same
    # info already on the table row above).
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.5), col_w,
                    row_height=Inches(0.5),
                    col_widths=[Inches(2.8), Inches(2.7)],
                    text_size=Pt(24))

    rb = add_bullets(slide, [
        "Stable across all 16 decode configurations",
        # "Recall 97.6-100% across 16 decode configurations",  # cut (already on table)
        ("Zero cost: pure Python, no LLM calls at runtime", {"bold": True}),
    ], rx, CT + Inches(3.7), col_w, Inches(1.5), size=Pt(24))

    # Bottom
    add_text(slide,
        "The decision tree was designed at development time, then distilled "
        "into deterministic Python. No LLM is called during evaluation.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "How the salvage detection works: a 15-rule deterministic decision tree "
        "that checks 6 linguistic signals and outputs a recovery probability. "
        "Validated at r=0.934 with IS, κ=0.818 (Y+P), stable across 16 configs.",
        [[lt] + step_shapes, [rt, tbl, rb]])

def slide_25d(prs):
    """Three real salvage examples showing HOW recovery works."""
    # audit:bigfonts \u2014 "how" body trimmed (~50% length) so 16pt fits in the
    # h=2.00" recovery body box of each 3.8"x5.4" card. Originals are kept
    # in the speaker notes / source docs (llm_salvage_analysis.md). REF/HYP
    # left at 18pt per task tier.
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Three Real Recoveries")
    add_accent_line(slide)

    add_text(slide,
        "These segments failed IS (< 3.0) but a viewer with context would understand them:",
        MX, CT, CW, Inches(0.35), size=Pt(18), color=LGRAY, italic=True)

    # audit:pptx_fix_manifest_after_amosi.md slide 43 MAJOR -
    # body font was 9-10pt (below 12pt readability floor). Card height
    # bumped to 5.4" and all body fonts lifted to 12pt minimum.
    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(5.4)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    # CUT v3: each "how" trimmed to ~70 chars so Pt(24) wraps in 4 lines
    # within the 2.00" frame (was 9 lines, bottom 8.55). Full prose for each
    # is preserved in speaker notes below + salvage_example_gallery.md.
    examples = [
        {
            "title": "Phonetic Bridge",
            "color": TEAL,
            "is_score": "1.29", "wer": "150%", "prob": "0.55",
            "ref": "when jesus rose again",
            "hyp": "in one sense it\u2019s rose\nand kennedy",
            # audit:bigfonts \u2014 trimmed from ~330 chars to ~180 (cut the
            # mouth-shape aside; full text in salvage_example_gallery.md).
            "how": "Religious-program viewer reads \u201cJesus rose.\u201d "
                   "Mouth shapes nearly identical.",
        },
        {
            "title": "Semantic Preservation",
            "color": GREEN,
            "is_score": "2.18", "wer": "75%", "prob": "0.90",
            "ref": "moving conceptual surface data\nover to engineering solutions\nand tools",
            "hyp": "moved the conceptual rules\nover to engineering tools",
            # audit:bigfonts \u2014 trimmed (cut "WER over-punishes ..." aside).
            "how": "Core meaning intact: concepts \u2192 tools. "
                   "Function words changed only.",
        },
        {
            "title": "Structure Match",
            "color": GOLD,
            "is_score": "2.55", "wer": "40%", "prob": "0.95",
            "ref": "over the last 10 years we have\nhad 8,616 students",
            "hyp": "over the last 10 years we have\nhad 1,600 students",
            # audit:bigfonts \u2014 trimmed (cut closing aside about exact figure).
            "how": "Only the number changed (8,616 \u2192 1,600). "
                   "Viewer reads \u201cmany students.\u201d",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # CUT v3 (overflow): font 16pt body so 3-line refs fit; layout reorg.
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.05), cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(20), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.50), cw_card - Inches(0.3), Inches(0.40),
                 size=Pt(18), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.95),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.25), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(2.40),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.70), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a viewer recovers this:",
                 x + Inches(0.15), cy + Inches(3.65),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.95), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE)

    _finish(slide, 0,
        "Three real salvage examples drawn from the LLM-Salvage analysis "
        "(165 of 900 metric-failed segments are recoverable, 18%). The "
        "card on the left shows a Phonetic Bridge (IS 1.29, WER 150%) where "
        "lip-shape collisions produce linguistically plausible but wrong "
        "words yet a viewer with religious context recovers the meaning. "
        "The middle card shows Semantic Preservation (IS 2.18, WER 75%) — "
        "core meaning intact even though every function word shifted. The "
        "right card shows Structure Match (IS 2.55, WER 40%) — perfect "
        "grammar with only a number changed; a viewer reads 'many students "
        "over 10 years' even though the exact figure (8,616 vs 1,600) is "
        "wrong. Each example illustrates one of the six recovery categories "
        "the llm_context_prob heuristic uses to flag salvage. "
        "Sources: docs/evaluation/llm_salvage/llm_salvage_analysis.md, "
        "docs/evaluation/llm_salvage/salvage_example_gallery.md.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25e — SALVAGE: 3 MORE REAL EXAMPLES (DOMAIN CONTEXT RECOVERY)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25e — SALVAGE: 3 MORE REAL EXAMPLES (DOMAIN CONTEXT RECOVERY)
# ═══════════════════════════════════════════════════════════════════════

def slide_25e(prs):
    """Three more salvage examples emphasising domain-context recovery."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Domain Context Fills the Gaps")
    add_accent_line(slide)

    add_text(slide,
        "A viewer who knows the topic recovers meaning that metrics miss entirely:",
        MX, CT, CW, Inches(0.35), size=Pt(18), color=LGRAY, italic=True)

    # audit:pptx_fix_manifest_after_amosi.md slide 44 MAJOR -
    # body font was 9-10pt; lifted to 12pt and card height bumped to 5.4".
    # Three cards side by side (same layout as slide_25d)
    cw_card = Inches(3.8)
    ch_card = Inches(5.4)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    # CUT v3: each "how" trimmed to ~70 chars so Pt(24) wraps in 4 lines
    # within 2.00" frame (was 8 lines, bottom 7.75). Full prose preserved
    # in speaker notes + salvage_example_gallery.md.
    examples = [
        # audit:bigfonts \u2014 "how" texts trimmed ~50% so 16pt fits the h=2.00"
        # recovery body box. Full versions live in
        # docs/evaluation/llm_salvage/salvage_example_gallery.md.
        {
            "title": "Religious Context",
            "color": CORAL,
            "is_score": "2.75", "wer": "43%", "prob": "0.90",
            "ref": "the fear of allah is completely\ngone \u2026 no more fear of the\nunseen what a horrible spiritual",
            "hyp": "the fear of the loss complete\n\u2026 no more fear of loss\nwhat a horrible spiritual",
            "how": "Sermon viewer hears \u201cfear of Allah.\u201d "
                   "Structure intact, phonetic swap.",
        },
        {
            "title": "Geopolitical Context",
            "color": TEAL,
            "is_score": "2.86", "wer": "72%", "prob": "0.90",
            "ref": "india china afghanistan all\nthese different places \u2026 so\nboth sides would benefit",
            "hyp": "middle east and afghanistan\nall these different warring\nplaces \u2026 both sides will benefit",
            "how": "Country names swap; argument identical. "
                   "Domain swap, not meaning loss.",
        },
        {
            "title": "Cooking Context",
            "color": GREEN,
            "is_score": "2.07", "wer": "89%", "prob": "0.80",
            "ref": "i have a tablespoon of\njalapeno fresh jalapeno",
            "hyp": "i have a dietary smoothie\ni\u2019ve got the banana called\nfresh banana",
            "how": "Viewer sees a pepper, overrides \u201cbanana.\u201d "
                   "Visual context fixes WER.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # CUT v3 (overflow): font 16pt body so 3-line refs fit; layout reorg.
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.05), cw_card - Inches(0.3), Inches(0.45),
                 size=Pt(20), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.50), cw_card - Inches(0.3), Inches(0.40),
                 size=Pt(18), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.95),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.25), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(2.40),
                 cw_card - Inches(0.3), Inches(0.30), size=Pt(16), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(2.70), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a wise viewer recovers this:",
                 x + Inches(0.15), cy + Inches(3.55),
                 cw_card - Inches(0.3), Inches(0.40), size=Pt(16), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(3.95), cw_card - Inches(0.3), Inches(1.10),
                 size=Pt(16), color=WHITE)

    _finish(slide, 0,
        "Three more salvage examples emphasising domain-context recovery. "
        "Religious Context (IS 2.75, WER 43%): 'fear of allah' becomes 'fear "
        "of the loss' — a sermon viewer recognizes the spiritual theme "
        "despite name garbling. Geopolitical Context (IS 2.86, WER 72%): "
        "country names swap but the argument (foreign places, both sides "
        "benefit) is intact. Cooking Context (IS 2.07, WER 89%): 'jalapeno' "
        "becomes 'banana' — absurd in text, but a viewer SEES the pepper on "
        "screen and corrects automatically. This is the strongest argument "
        "for multimodal context: the visual channel fills gaps that "
        "audio-only metrics cannot measure. Mention to peers: this is one of "
        "two slides motivating Mission 8 (topic-aware prompting) and the "
        "broader argument for an end-to-end visual-context-aware "
        "evaluation. "
        "Sources: docs/evaluation/llm_salvage/llm_salvage_analysis.md, "
        "docs/evaluation/llm_salvage/salvage_example_gallery.md.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14b — CURATED EXAMPLES VIDEO GALLERY
# ═══════════════════════════════════════════════════════════════════════

def slide_14b(prs):
    """14b: 2x3 clickable video grid - each video demonstrates a different system behavior.

    BLOCKER fix (May 2026): pre-fix audit found orphan animation refs to
    spids ['5','7','11','13','15'] (pptx_visual_audit.json). Cause: a
    prior version of this function called add_animations directly with
    a stale shape list whose IDs no longer matched the rebuilt slide.
    Fixed by collecting actual shape handles into a single click_reveal
    group passed to _finish - the animation tree now references only the
    shape IDs that exist on this slide. Body font also bumped from 9pt
    to 12pt to clear the readability floor.

    audit:bigfonts — captions at 18pt fit single line in 0.40" box; long
    captions wrap into 2 lines (visible inside grid spacing).
    """
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    intro = add_text(slide, "Click any thumbnail to play — each video demonstrates a different system behavior:",
             MX, CT, CW, Inches(0.35), size=Pt(24), color=LGRAY)

    # Grid layout: 3 cols x 2 rows
    vid_w  = Inches(3.82)
    vid_h  = Inches(2.15)   # 16:9
    gap_x  = Inches(0.23)
    gap_y  = Inches(0.65)   # space for descriptive label below each video
    row_y  = [CT + Inches(0.45), CT + Inches(0.45) + vid_h + gap_y]
    start_x = MX

    # 6 videos - balanced: 3 positive high-IS examples + 3 failure modes
    # NOTE: avoid reusing videos from opening (perfect) or demo trio (smartphone, street_photo, halluc)
    rows = [
        [("convention",   "Convention & books — meaning fully captured, minor word drops",
          "31%",  GREEN),
         ("marilyn",      "Marilyn Monroe wallpaper — proper nouns + context intact",
          "36%",  GREEN),
         ("music_play",   "Music discussion — gist preserved, phrasing changed",
          "34%",  GREEN)],
        [("spelling_smell","Spelling \u2192 smelling — phonetic confusion swaps entire domain",
          "59%",  YELLOW),
         ("admiral",      "Admiral McRae \u2192 animal migratory — classic viseme swap",
          "33%",  YELLOW),
         ("doxology",     "Doxology \u2192 fabricated story - total hallucination",
          "172%", RED)],
    ]

    # Capture every shape we add so the animation only references real spids.
    grid_shapes = [intro]
    for r, row in enumerate(rows):
        for c, (key, label, wer, color) in enumerate(row):
            x = start_x + c * (vid_w + gap_x)
            y = row_y[r]
            vid_shape = add_video(slide, key, x, y, vid_w, vid_h)
            # Descriptive caption + readable WER badge (12pt floor per audit)
            cap = add_text(slide, f"{label}  (WER {wer})",
                     x, y + vid_h + Inches(0.04), vid_w, Inches(0.40),
                     size=Pt(24), color=color, bold=False,
                     align=PP_ALIGN.CENTER)
            grid_shapes.extend([vid_shape, cap])

    _finish(slide, 0,
        "Balanced video gallery: 3 positive + 3 failure modes. "
        "Row 1 (positive): (1) Convention - person describes selling books at a "
        "convention, meaning fully captured with minor word drops. (2) Marilyn "
        "Monroe - proper noun preserved, wallpaper context intact. (3) Music - "
        "gist of playing a song preserved, phrasing changed. "
        "Row 2 (failure modes): (4) Spelling-to-smelling - phonetic confusion "
        "swaps the entire domain from literacy to odors. (5) Admiral McRae - "
        "classic viseme swap, identical lip shapes produce wrong words. "
        "(6) Doxology - total hallucination, model fabricates an unrelated story. "
        "BLOCKER fix May 2026: animation references previously orphaned spids "
        "[5,7,11,13,15]; rebuilt to pass real shape handles. "
        "Source: docs/evaluation/pptx_visual_audit.json (slide 47).",
        [grid_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE A15 — VIDEO GALLERY MAP
# ═══════════════════════════════════════════════════════════════════════

def slide_is_deep_dive(prs):
    """IS correlation deep dive — conclusions-focused."""
    # audit:bigfonts — no content cuts; all bumps fit in existing layout.
    slide = new_slide(prs)
    add_title(slide, "IS Validation: What Did We Learn?")
    add_accent_line(slide)

    add_text(slide,
        "We validated IS against signal analysis and cross-configuration testing. "
        "Here is what the evidence shows.",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    offset = Inches(0.45)

    # Left — compact correlation table
    lt = add_text(slide, "Signal \u2192 IS Correlation", MX, CT + offset, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "r with IS", "Dimension"],
        [["Phonetic Sim", "0.943", "Word Accuracy"],
         ["Inv. WER", "0.834", "Word Accuracy"],
         ["Inv. WWER", "0.823", "Word Accuracy"],
         ["Semantic Sim", "0.856", "Meaning"],
         ["NEA F1", "0.748", "Entity Accuracy"],
         ["Length Ratio", "0.521", "Output Sanity"]],
        MX, CT + offset + Inches(0.5), col_w, text_size=Pt(24),
        row_height=Inches(0.45),
        row_colors={0: {1: GREEN}, 5: {1: CORAL}})

    # Right — conclusions (the main point)
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Conclusions", rx, CT + offset, rw, Inches(0.4),
                  size=Pt(28), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("IS captures quality that WER misses",
         {"bold": True, "color": GREEN}),
        ("Cross-config validation confirms stability: "
         "mean r = 0.925 across 16 configurations",
         {"bold": True, "color": TEAL}),
        ("WER/WWER/Phonetic are redundant with each other "
         "(r > 0.79) but IS needs all three for robustness", {}),
        ("Semantic Sim is the tiebreaker \u2014 it separates "
         "segments with similar WER but different meaning "
         "preservation", {}),
    ], rx, CT + offset + Inches(0.5), rw, Inches(4.5), size=Pt(24))

    _finish(slide, 0,
        "IS validation conclusions. PCA retains 2 principal components: "
        "signal quality (68%, all 5 content signals load equally) and "
        "output length (20%, Length Ratio dominates). Semantic is NOT "
        "an independent dimension \u2014 it loads on PC1 alongside word-accuracy "
        "signals. Cross-config validation across 16 decode configurations "
        "confirms stability with mean r=0.925.",
        [[lt, tbl], [rt, rb]], click_reveal=True)


def slide_metric_disagreement(prs):
    """What metric disagreements reveal about transcription quality."""
    # audit:bigfonts — bumps fit within 5.8x2.0 cards; no trims needed.
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: What It Tells Us")
    add_accent_line(slide)

    add_text(slide,
        "IS uses 6 signals because no single metric tells the full story. "
        "Disagreements between metrics reveal specific quality patterns:",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

    # Four disagreement pattern cards (2x2 grid)
    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("WWER \u226a WER", TEAL,
         "Function words wrong, content right",
         "\"the team discussed quarterly\" \u2192 \"team discuss quarterly\"\n"
         "WER 43% but WWER 15% \u2014 viewer gets the message."),
        ("NEA high, WER high", GREEN,
         "Names preserved despite poor accuracy",
         "\"Dr. Chen presented Q3 results\" \u2192 \"Dr. Chen present Q3 result\"\n"
         "WER 57% but NEA F1 = 100% \u2014 critical info intact."),
        ("Semantic high, WER high", GOLD,
         "Meaning preserved through paraphrasing",
         "\"reduce spending\" \u2192 \"cut the budget\"\n"
         "WER 100% but Semantic 0.87 \u2014 same meaning, different words."),
        ("Phonetic high, Semantic low", CORAL,
         "Sounds right, wrong meaning",
         "\"the alliance was formed\" \u2192 \"the lions were found\"\n"
         "Phonetic 0.71 but Semantic 0.12 \u2014 dangerous deceptive error."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        card_shapes = []
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)
        card_shapes.append(add_rich_text(slide, [
            [(title, {"size": Pt(24), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(24), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(24), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "This is why IS uses 6 signals \u2014 each disagreement pattern "
        "reveals a different type of quality that a single metric would miss.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four key metric disagreement patterns. WWER<<WER means function words "
        "are wrong but content preserved. High NEA + high WER means names survived. "
        "High semantic + high WER means paraphrasing. High phonetic + low semantic "
        "is the dangerous case — sounds right but wrong meaning.",
        [c for c in cards], click_reveal=True)


def slide_metric_disagreement_2(prs):
    """More metric disagreement patterns — part 2."""
    # audit:bigfonts — bumps fit within 5.8x2.0 cards; no trims needed.
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: More Patterns")
    add_accent_line(slide)

    add_text(slide,
        "Additional diagnostic patterns that reveal specific transcription behaviors:",
        MX, CT, CW, Inches(0.4), size=Pt(18), color=LGRAY, italic=True)

    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("Length \u226a 1.0, all metrics low", CORAL,
         "Signal loss — model gave up or truncated",
         "Ref: \"the thirteenth amendment abolished slavery\"\n"
         "Hyp: \"the\" (length ratio 0.06)\n"
         "All signals collapse — nothing to evaluate."),
        ("Length \u226b 1.0, Semantic low", CORAL,
         "Hallucination — fluent fabrication",
         "Ref: \"carry strap\" \u2192 Hyp: 3 paragraphs about history\n"
         "WER 6,833%, length ratio 45\u00d7 — LLM ran unchecked.\n"
         "IS catches via length + semantic: fluent but fabricated."),
        ("NEA low, Semantic moderate", GOLD,
         "Topic right, entities destroyed",
         "\"the 13th amendment\" \u2192 \"the important decision\"\n"
         "Semantic 0.52 but NEA F1 = 0% — gist right, facts lost.\n"
         "IS penalizes: critical info (names, numbers) irrecoverable."),
        ("All metrics moderate (~0.5)", TEAL,
         "Accumulated small errors — death by a thousand cuts",
         "Every signal is mediocre, none catastrophic.\n"
         "WER 55%, Semantic 0.48, Phonetic 0.51, NEA 40%.\n"
         "IS: ~2.5 (borderline) — individually OK, collectively degraded."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        card_shapes = []
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)
        card_shapes.append(add_rich_text(slide, [
            [(title, {"size": Pt(24), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(24), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35)))
        card_shapes.append(add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(24), color=LGRAY))
        cards.append(card_shapes)

    add_text(slide,
        "8 total diagnostic patterns — IS decomposes quality into actionable signals "
        "that each point to a different engineering fix.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four more metric disagreement patterns. Length collapse = signal loss. "
        "Length explosion + low semantic = hallucination. Low NEA + moderate semantic = "
        "entity destruction. All-moderate = accumulated errors.",
        [c for c in cards], click_reveal=True)

    # Note: slide visibility controlled by hidden_builders in generate_presentation.py


def slide_two_eval_systems(prs):
    """Two evaluation systems — IS and Opus-as-a-Judge."""
    # audit:bigfonts — agreement-matrix table given explicit row_height for
    # 18pt cells; we_b worked-examples kept at Pt(24) to fit h=1.7 box.
    slide = new_slide(prs)
    add_title(slide, "Two Evaluation Systems, One Framework")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — IS (strict) + Opus-as-Judge (generous)
    lt = add_text(slide, "The Two Systems", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    # IS card
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    r1_t = add_text(slide, "Intelligibility Score (IS)", MX + Inches(0.2),
             CT + Inches(0.6), col_w - Inches(0.4), Inches(1.0),
             size=Pt(24), color=TEAL, bold=True)
    r1_b = add_bullets(slide, [
        "Strict metric: composite 0\u20135 score, two operating points",
        ("IS \u2265 3.80 = Clearly conveyed: 23% (346/1,497)", {"bold": True}),
        ("IS \u2265 2.00 = Any useful meaning: 62% (922/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24))

    # Opus-as-Judge card
    r2 = add_rect(slide, MX, CT + Inches(2.3), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    r2_t = add_text(slide, "Opus-as-a-Judge (LLM Gold Standard)", MX + Inches(0.2),
             CT + Inches(2.4), col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=GREEN, bold=True)
    r2_b = add_bullets(slide, [
        "Holistic: Y/P/N per ref+hyp pair (1,497 pairs)",
        ("Y = 23% clearly conveyed, Y+P = 65% useful", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(2.8), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24))

    # Right — agreement + worked example
    rx = MX + col_w + gap
    rt = add_text(slide, "Agreement Between Systems", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    agree_txt = add_text(slide,
        "\u03ba = 0.818 (good agreement)\n"
        "IS undercounts: 62% vs judge 65%.",
        rx, CT + Inches(0.5), col_w, Inches(0.6),
        size=Pt(24), color=WHITE, bold=True)

    # NIV Y+P agreement matrix (IS >= 2.00 vs Opus Y+P)
    tbl = add_table(slide,
        ["", "Opus: Y or P", "Opus: N"],
        [["IS \u2265 2.00", "883", "39"],
         ["IS < 2.00", "88", "487"]],
        rx, CT + Inches(1.3), col_w, text_size=Pt(24),
        row_height=Inches(0.5),
        row_colors={0: {1: GREEN}, 1: {2: CORAL}})

    # Worked examples
    we_t = add_text(slide, "Worked Examples:", rx, CT + Inches(2.6), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)
    we_b = add_text(slide,
        'Ref: "what does this chord sound like to you"\n'
        'Hyp: "what does this court sound like to you"\n'
        'WER: 12% \u2022 IS: 3.84 \u2022 IS Y \u2714 \u2022 Opus: Y\n\n'
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.94 \u2022 IS Y+P \u2714 \u2022 Opus: P\n'
        'Old IS \u2265 3.0 wrongly rejected this segment.',
        rx, CT + Inches(2.95), col_w, Inches(1.7),
        size=Pt(24), color=WHITE)

    _finish(slide, 0,
        "Two evaluation systems with NIV thresholds. "
        "IS >= 3.80 for clearly conveyed (23%, matches judge Y rate 23%, kappa=0.690). "
        "IS >= 2.00 for any useful meaning (62%, kappa=0.818, almost perfect). "
        "Opus-as-a-Judge: Y=23%, Y+P=65%. "
        "IS is a strict estimator — undercounts at both operating points. "
        "Old IS >= 3.0 threshold is superseded: it sat in no-man's land (kappa=0.565 for Y, 0.521 for Y+P).",
        [[lt, r1, r1_t, r1_b], [r2, r2_t, r2_b], [rt, agree_txt, tbl, we_t, we_b]], click_reveal=True)


def slide_llm_judge(prs):
    """LLM-as-a-Judge gold standard evaluation."""
    # audit:bigfonts — results table given row_height=0.5 for 18pt cells.
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge: Gold Standard (1,497 Pairs)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — question/setup then methodology
    lt = add_text(slide, "What Is LLM-as-a-Judge?", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Use a frontier LLM (Claude Opus) as an independent evaluator",
        "Evaluate every reference+hypothesis pair holistically",
        "3-level verdict: Y (preserved) / P (partial) / N (not preserved)",
        ("30 duplicate pairs \u2192 87% intra-rater reliability", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(4.2), size=Pt(24))

    # Results table
    res_t = add_text(slide, "Results (Blind, 1,497 Pairs)", MX, CT + Inches(2.4), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Count", "%"],
        [["Y (fully preserved)", "345", "23%"],
         ["P (partially)", "626", "42%"],
         ["N (not preserved)", "526", "35%"],
         ["Y+P (any useful)", "971", "65%"]],
        MX, CT + Inches(2.8), col_w, text_size=Pt(24),
        row_height=Inches(0.5),
        row_colors={0: {2: GREEN}, 2: {2: CORAL}, 3: {2: TEAL}})

    # Right — Methodology
    rx = MX + col_w + gap
    rt = add_text(slide, "Methodology:", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    rb = add_bullets(slide, [
        "Claude Opus received each ref+hyp pair blind (no metrics visible)",
        "3-level holistic judgment: Y (fully conveyed), P (partial), N (lost)",
        ("\u03ba = 0.690 (Y threshold) and \u03ba = 0.818 (Y+P threshold)",
         {"color": TEAL}),
        ("Used as gold standard to calibrate IS thresholds",
         {"bold": True}),
    ], rx, CT + Inches(0.5), col_w, Inches(4.2), size=Pt(24))

    # audit:after_amosi_narrative_actions.md fix #7 - this is the v1
    # blind judge run (Opus 4.6, 1,497 pairs). The n-best paired-test
    # slide elsewhere in this section uses v3 (dual-conf, Opus 4.7,
    # 5,988 verdicts). Footer label disambiguates the two runs so the
    # audience does not conflate them.
    judge_label = add_text(slide,
        "v1 blind judge   /   Opus 4.6   /   1,497 pairs",
        MX, Inches(6.6), CW, Inches(0.3),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "LLM-as-a-Judge gold standard - v1 BLIND run (Claude Opus 4.6, "
        "1,497 pairs). Distinct from the v3 dual-conf judge run on the "
        "n-best paired-test slide later in this section, which uses "
        "Opus 4.7 with the dual-conf prompt across 5,988 verdicts. "
        "Headline: Y=23% (345 of 1,497), P=42% (626), N=35% (526), "
        "Y+P=65%. Intra-rater agreement 87% on the 30-pair duplicate "
        "subset. Pearson r=0.85 between IS and the judge verdict, which is "
        "what justifies using IS as a deterministic surrogate. Threshold "
        "sweep: Y+P peaks at IS>=2.0 (kappa=0.818, 92% agreement); the "
        "older IS>=3.0 cutoff under-counts (kappa=0.521) and is now retired. "
        "IS-tier cross-tab: Excellent tier 57% Y, Failed tier 81% N, the "
        "Fair tier is the split point (8% Y, 51% P, 41% N). Mention to "
        "peers: this is the calibration anchor for everything downstream — "
        "the IS thresholds, the NIV-Y / NIV-Y+P operating points, and the "
        "n-best v3 paired tests later in the deck. Full cross-tab in "
        "appendix slide A8 (a16 builder).\n\n"
        "PEER DETAIL — Cohen's kappa: kappa = (P_obs − P_chance)/(1 − "
        "P_chance) on a 2×2 of (judge {Y, not-Y}) × (IS-NIV "
        "{>=threshold, <threshold}) on n=1,497. For kappa=0.690 the "
        "cells are 273/86/72/1066. Intra-rater 87% = exact-agreement on "
        "30 randomly resampled pairs.\n\n"
        "PEER DETAIL — IS thresholds were calibrated by sweeping IS in "
        "0.05 steps and picking the value that maximizes kappa vs "
        "judge-{Y, not-Y}: NIV-Y at IS>=3.80 (kappa=0.690), NIV-Y+P at "
        "IS>=2.00 (kappa=0.818). "
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/threshold_calibration_vs_opus.md.",
        [[lt, lb],
         [res_t, tbl],
         [rt, rb, judge_label]],
        click_reveal=True)


def slide_context_eval(prs):
    """IS: A Calibrated Surrogate Metric — IS vs LLM Judge comparison."""
    # audit:bigfonts — same trim as slide_25 sister; bullets 4 -> 3,
    # rect grew 4.6 -> 5.0, bottom strip pushed to 6.55.
    slide = new_slide(prs)
    add_title(slide, "IS: A Calibrated Surrogate Metric")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(5.0), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # IS metric
    add_text(slide, "IS says 62%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments deliver useful output (IS \u2265 2.00)",
             MX + Inches(0.3), CT + Inches(0.85),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # LLM Judge
    add_text(slide, "LLM Judge says 65%", MX + Inches(0.3), CT + Inches(1.5),
             CW - Inches(0.6), Inches(0.7),
             size=Pt(40), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "deliver useful output (Y + P)",
             MX + Inches(0.3), CT + Inches(2.15),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(24), color=LGRAY, align=PP_ALIGN.CENTER)

    # Key bullets
    # audit:bigfonts — cut bullet "LLM-as-a-Judge (blind, 1,497 pairs)
    # confirms: nearly 2 in 3 segments carry useful meaning" (in notes).
    bul = add_bullets(slide, [
        ("IS closely tracks LLM judge \u2014 62% vs 65% "
         "(\u03ba = 0.818)", {"bold": True, "color": WHITE}),
        ("3pp gap (62% \u2192 65%) = IS is a calibrated surrogate",
         {}),
        ("IS is a floor, not a ceiling \u2014 designed to be cautious",
         {"color": TEAL}),
    ], MX + Inches(0.3), CT + Inches(2.8), CW - Inches(0.6),
       Inches(2.1), size=Pt(24))

    # Bottom text
    add_text(slide,
             "Our metric is deliberately conservative. "
             "Independent LLM judge confirms true useful rate is 3pp higher.",
             MX, Inches(6.55), CW, Inches(0.5),
             size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS is a calibrated surrogate metric for transcription quality. "
        "IS says 62% of segments deliver useful output (IS >= 2.00). An independent "
        "LLM-as-a-Judge evaluation (Claude Opus, blind, all 1,497 pairs) finds "
        "Y+P = 65% deliver useful output. The 3pp gap shows IS deliberately "
        "undercounts: many segments with partial value are penalized by strict "
        "metrics. IS is a floor, not a ceiling.",
        [[r1], [bul]], click_reveal=True)


def slide_what_good_looks_like(prs):
    """IS Tier 5 examples — what good looks like."""
    # audit:bigfonts — table reduced 3 -> 2 rows (middle "buyer wants to
    # buy one" was a verbatim duplicate); row_height 0.65 -> 1.10 so 16pt
    # body wraps; bullets trimmed 4 -> 3.
    slide = new_slide(prs)
    add_title(slide, "What Good Looks Like: IS Tier 5")
    add_accent_line(slide)

    add_text(slide,
        "276 segments (18%) score IS \u2265 4.0 \u2014 Excellent quality:",
        MX, CT, CW, Inches(0.40), size=Pt(24), color=LGRAY)

    tbl = add_table(slide,
        ["Reference", "Hypothesis", "WER", "IS"],
        [["health insurance company they pay for all "
          "the medications they pay for all your visits",
          "[exact match]", "0%", "5.0"],
         # audit:bigfonts — cut middle "so here we have ... one free" row
         # (verbatim-match example duplicating row 1's lesson).
         ["allow you to work with the team in a more "
          "productive efficient and effective manner",
          "allow you to work with a team and more "
          "productive efficient and effective manner", "14%", "4.6"]],
        MX, CT + Inches(0.55), CW, text_size=Pt(24),
        row_height=Inches(1.10),
        col_widths=[Inches(4.5), Inches(4.5), Inches(0.8), Inches(0.8)],
        row_colors={0: {3: GREEN}, 1: {3: GREEN}})

    # Key callout
    add_text(slide,
        "The system reads lips with high fidelity when visual signal is strong.",
        MX, CT + Inches(3.95), CW, Inches(0.45),
        size=Pt(24), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Stats
    # audit:bigfonts — cut bullet "Business/Finance topics dominate Tier 5"
    # (in speaker notes).
    add_bullets(slide, [
        "276 segments (18%) \u2014 the architecture works",
        "57% LLM Judge Y among Tier 5 \u2014 even the strictest agrees",
        ("Perfect transcription across 20\u201340 consecutive words \u2014 not luck",
         {"bold": True}),
    ], MX, CT + Inches(4.55), CW, Inches(2.0), size=Pt(24))

    _finish(slide, 0,
        "What good looks like: 276 segments (18%) achieve IS 4.0-5.0. "
        "Perfect word-for-word transcription over 20-40 consecutive words. "
        "The architecture works — the challenge is getting it to work "
        "consistently across all domains.",
        [[tbl]], click_reveal=True)


def slide_llm_context_engine(prs):
    """LLM as context engine — what it does and where to go."""
    # audit:bigfonts — no content cuts; layout accommodates bumps.
    slide = new_slide(prs)
    add_title(slide, "The LLM Is a Context Engine")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what the LLM does
    lt = add_text(slide, "What the LLM Does", MX, CT, col_w, Inches(0.4),
                  size=Pt(24), color=TEAL, bold=True)

    add_text(slide, "The visual encoder sees mouth shapes.",
             MX, CT + Inches(0.6), col_w, Inches(0.3),
             size=Pt(24), color=WHITE)
    add_text(slide, "The LLM resolves ambiguity using language context.",
             MX, CT + Inches(1.0), col_w, Inches(0.3),
             size=Pt(24), color=TEAL, bold=True)

    lb = add_bullets(slide, [
        '"p/b/m" \u2192 Is it "pat," "bat," or "mat"?',
        "LLM uses surrounding words to disambiguate",
        "Stronger LLM = better disambiguation",
        ("This is why LLM quality matters more than size", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.0), size=Pt(24))

    # Right — current vs upgrade
    rx = MX + col_w + gap
    rt = add_text(slide, "Current vs Upgrade", rx, CT, col_w, Inches(0.4),
                  size=Pt(24), color=CORAL, bold=True)

    # Current
    r1 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Current: LLaMA-2 7B", rx + Inches(0.2), CT + Inches(0.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=CORAL, bold=True)
    add_bullets(slide, [
        "32K vocab, 4K context",
        "2023 model, limited reasoning",
    ], rx + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(24), bullet_color=CORAL)

    # Upgrade
    r2 = add_rect(slide, rx, CT + Inches(2.5), col_w, Inches(2.0),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Upgrade: Llama 3.1 8B", rx + Inches(0.2), CT + Inches(2.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(24), color=GREEN, bold=True)
    add_bullets(slide, [
        "128K vocab, 128K context",
        "Quality \u2248 LLaMA-2 70B",
        ("Same hidden_size (4096) = architecture-compatible upgrade", {"color": GREEN}),
        ("Setup: 2\u20134 weeks + retraining", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(3.0), col_w - Inches(0.4), Inches(1.2),
       size=Pt(24), bullet_color=GREEN)

    _finish(slide, 0,
        "The LLM is a context engine. The visual encoder sees mouth shapes but "
        "can't distinguish visemes. The LLM resolves ambiguity using language "
        "context. A stronger LLM means better disambiguation. Llama 3.1 8B "
        "has quality equivalent to LLaMA-2 70B with the same hidden dimension "
        "(4096), architecture-compatible but requires adapter retraining.",
        [[lt, lb], [rt, r1, r2]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE — LLM JUDGE 30-SAMPLE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

def slide_llm_judge_30(prs):
    """30-sample LLM-as-a-Judge overview — summary stats + what the sample shows."""
    # audit:bigfonts — left summary table needs row_height bump for 18pt.
    slide = new_slide(prs)
    add_title(slide, "LLM Judge: Deep Dive")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — summary stats
    lt = add_text(slide, "30 Representative Segments", MX, CT, col_w, Inches(0.35),
                  size=Pt(24), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Metric", "Value"],
        [["Segments", "30 (stratified sample)"],
         ["Mean WER", "61%"],
         ["Mean IS", "2.67 / 5.0"],
         ["LLM Judge: Y", "7  (23%)"],
         ["LLM Judge: P", "12  (40%)"],
         ["LLM Judge: N", "11  (37%)"],
         ["Y + P", "19  (63%)"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(24),
        row_height=Inches(0.55),
        row_colors={3: {1: GREEN}, 5: {1: CORAL}, 6: {1: TEAL}})

    # Right — what this sample shows
    rx = MX + col_w + gap
    rt = add_text(slide, "What the Sample Reveals", rx, CT, col_w, Inches(0.35),
                  size=Pt(24), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Distribution mirrors the full 1,497-segment dataset",
         {"bold": True}),
        # audit:after_amosi_narrative_actions.md fix #14 - reorder-robust phrasing.
        ("6 videos in this section walk through these "
         "cases one by one", {"color": TEAL}),
    ], rx, CT + Inches(0.5), col_w, Inches(3.0), size=Pt(24))

    # Bottom takeaway
    bk = add_text(slide,
        "Each video has burned-in subtitles showing reference (top) and "
        "hypothesis (bottom) \u2014 watch the lip movements and compare.",
        MX, Inches(6.2), CW, Inches(0.8),
        size=Pt(18), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "30-sample overview: stratified sample drawn from the 1,497-segment "
        "evaluation set. The 30-pair sample distribution matches the full "
        "dataset closely (Y=23% vs 23%, P=40% vs 42%, N=37% vs "
        "35%) and confirms the smaller deep-dive sample is representative. "
        "Mean WER 61% versus 64% on the full 1,497 segments; mean IS "
        "2.67 versus 2.547 on full. The interesting middle zone (IS 2.0-4.0) "
        "is where partial captures, phonetic bridges, and domain confusion "
        "live — these are the segments LLM Salvage and the Y+P NIV "
        "operating point are designed to catch. Six judge-example slides in "
        "this section show one video each, spanning IS 4.55 down to 1.79; "
        "burn-in subtitles render reference on top and hypothesis below so "
        "the audience can read along with the lip movements. Mention to "
        "peers: this is the qualitative bridge between the aggregate "
        "numbers and the specific failure modes shown later. "
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/llm_judge/.",
        [[lt, tbl], [rt, rb, bk]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDES — 6 LLM JUDGE VIDEO EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def _judge_video_slide(prs, *, vid_key, title, ref, hyp, wer, wwer, is_score,
                       is_tier, judge, category, annotation, notes,
                       client_verdict=None):
    """Reusable builder: single video left, ref/hyp/metrics right.

    If `client_verdict` is provided (a plain-English string like "Excellent —
    meaning fully preserved"), replaces the WER/WWER/IS/Judge score header
    with the verdict tag. The client deck uses this; the academic deck
    leaves it None and renders the full metrics row.

    audit:bigfonts — REF/HYP body at 18pt in 1.0" box accommodates 2-3
    short-line refs / hyps as currently authored. Annotation also at 18pt
    in 1.5" box (~5 lines). Six callers vetted: ex1-ex6 annotations are
    4-5 lines each. No content cuts to the 6 video example slides.
    """
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    # Left — large video
    vid_w = Inches(6.0)
    vid_h = Inches(4.5)  # ~16:9 with margin
    vid = add_video(slide, vid_key, MX, CT + Inches(0.1), vid_w, vid_h)

    # Right — content card
    rx = MX + vid_w + Inches(0.4)
    rw = CW - vid_w - Inches(0.4)

    # Judge badge color
    badge_colors = {"Y": GREEN, "P": YELLOW, "N": RED}
    badge_col = badge_colors.get(judge, LGRAY)

    # Metrics row — academic deck shows full metrics line; client deck
    # passes `client_verdict` to suppress raw WER/WWER per N9.
    if client_verdict is not None:
        metrics_text = client_verdict
    else:
        metrics_text = (f"WER {wer}   WWER {wwer}   IS {is_score} ({is_tier})   "
                        f"Judge: {judge}")
    # CUT v3 (overflow): grew 0.4 -> 0.85 so 24pt metrics text fits one line.
    mt = add_text(slide, metrics_text, rx, CT, rw, Inches(0.85),
                  size=Pt(24), color=badge_col, bold=True)

    # Reference — CUT v3: shrunk 24->20pt + h bumped 1.0->1.25.
    # audit:FONT_BELOW_24PT_BODY — REF/HYP frame heights tightened
    # 1.25->1.00 to free 0.50" of vertical space for the annotation bump
    # (20->24pt). REF/HYP keep 20pt (italic = caption-role per audit script).
    rl = add_text(slide, "Reference:", rx, CT + Inches(0.5), rw, Inches(0.25),
                  size=Pt(20), color=LGRAY, bold=True)
    # CUT v3 (overflow): grew 1.00 -> 1.70 so longer 20pt refs fit (2-line wrap).
    rt = add_text(slide, f"\u201c{ref}\u201d", rx, CT + Inches(0.75), rw, Inches(1.70),
                  size=Pt(20), color=WHITE, italic=True)

    # Hypothesis \u2014 CUT v3: shrunk 24->20pt + h bumped 1.0->1.25.
    # audit:FONT_BELOW_24PT_BODY \u2014 HYP shifted up 2.05->1.80 after REF tightening.
    hl = add_text(slide, "Prediction:", rx, CT + Inches(1.80), rw, Inches(0.25),
                  size=Pt(20), color=LGRAY, bold=True)
    # CUT v3 (overflow): grew 1.50 -> 1.75 so 4-line 20pt hyps fit.
    ht = add_text(slide, f"\u201c{hyp}\u201d", rx, CT + Inches(2.05), rw, Inches(1.75),
                  size=Pt(20), color=CORAL, italic=True)

    # Category badge — CUT v3: pushed down to 3.65 to follow bumped ref/hyp.
    # audit:FONT_BELOW_24PT_BODY — moved up 3.65->3.15 after REF/HYP tightening.
    cb = add_rect(slide, rx, CT + Inches(3.15), rw, Inches(0.35),
                  fill_color=NAVY3, corner_radius=True)
    # CUT v3 (overflow): grew 0.3 -> 0.7 for 20pt category text (often wraps).
    add_text(slide, category, rx + Inches(0.15), CT + Inches(3.17),
             rw - Inches(0.3), Inches(0.7),
             size=Pt(20), color=TEAL, bold=True)

    # Annotation — CUT v3: trimmed each caller's annotation to ~140 chars
    # (~5 short lines @ 20pt) so 20pt body fits in 1.50" frame without
    # overflowing the y=7.05 safe zone. Full narrative moved to speaker
    # notes (`notes` arg passed to _finish below).
    # audit:FONT_BELOW_24PT_BODY — bumped 20->24pt (body tier per audit);
    # frame grown 1.50->2.00" using space freed from REF/HYP tightening.
    # 5 short lines @ 24pt fits 2.0" frame (line height 0.40").
    at = add_text(slide, annotation, rx, CT + Inches(3.60), rw, Inches(2.00),
                  size=Pt(24), color=WHITE)

    _finish(slide, 0, notes,
            [[vid, mt], [rl, rt, hl, ht, cb, at]], click_reveal=True)


def slide_judge_ex1(prs):
    """Judge example 1: Named entity swap — bernreuter → rogers (IS 4.55)."""
    _judge_video_slide(prs,
        vid_key="judge_entity",
        title="Judge Example 1: Named Entity Swap",
        ref="market research firm bernreuter research is "
            "forecasting pv installations could reach",
        hyp="market research firm rogers research is "
            "forecasting pv installations will reach",
        wer="18%", wwer="15%", is_score="4.55",
        is_tier="Excellent", judge="Y",
        category="Named Entity Swap — meaning fully preserved",
        # CUT v3: long narrative ("WER penalizes the name error equally
        # to any other word\u2026") moved into speaker notes below.
        annotation="Only company name changed (bernreuter \u2192 rogers) "
                   "and 'could' \u2192 'will'. Forecast captured; viewer "
                   "gets the full message.",
        notes="Named entity swap: 'bernreuter' becomes 'rogers' — visually "
              "similar lip patterns for proper nouns. WER is 18% on this "
              "segment, WWER 15% (the entity drops out at the same rate "
              "common words do here, so weighting barely moves WER). Despite "
              "18% WER, the core message about PV installation forecasts "
              "is fully preserved — only the company name is wrong, and the "
              "verb 'could' becomes 'will'. The LLM judge rates Y; IS is "
              "4.55, which sits in the Excellent tier. Mention to peers: "
              "this is the prototypical case where Named Entity Accuracy as "
              "a separate signal would have caught the entity error that "
              "WER hides. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/evaluation/intelligibility_methodology.md (NEA signal).")


def slide_judge_ex2(prs):
    """Judge example 2: Truncated but core preserved — 1980s film (IS 3.69)."""
    _judge_video_slide(prs,
        vid_key="judge_film",
        title="Judge Example 2: Truncated but Core Preserved",
        ref="as this new home video market matured in the 1980s "
            "a number of film companies decided they could bypass "
            "the theatrical distribution system altogether and market their",
        hyp="in the 1980s when film companies decided they could "
            "bypass the theatrical distribution system altogether "
            "among other",
        wer="48%", wwer="42%", is_score="3.69",
        is_tier="Good", judge="P",
        category="Truncation \u2014 beginning and end lost, core intact",
        # CUT v3: dropped "WER is 48% because of the missing words\u2026"
        # (in speaker notes); kept the core observation.
        annotation="Opening + trailing clauses lost. But the core "
                   "argument \u2014 1980s film companies bypassing "
                   "theatrical distribution \u2014 is captured verbatim.",
        notes="Truncation example. WER is 48%, WWER 42% — both numbers "
              "look like a clear failure if you stop at WER alone. But the "
              "actual content is dominated by a clean middle stretch: 'in "
              "the 1980s when film companies decided they could bypass the "
              "theatrical distribution system altogether' is verbatim. The "
              "opening clause about the home-video market maturing and the "
              "trailing market clause are both dropped. The LLM judge rates "
              "P (partial), and IS lands at 3.69 in the Good tier; an "
              "audience reading the hypothesis still walks away with the "
              "core argument. Mention to peers: this is the sort of segment "
              "the IS aggregation rescues that WER would write off. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/evaluation/intelligibility_methodology.md.")


def slide_judge_ex3(prs):
    """Judge example 3: Tech vocabulary drift — routers → roads (IS 3.02)."""
    _judge_video_slide(prs,
        vid_key="judge_router",
        title="Judge Example 3: Technical Vocabulary Drift",
        ref="we need a radically different approach we basically "
            "need to find a way how we can take existing routers "
            "existing switches existing links and enable them for research",
        hyp="we need a radically different approach we must indeed "
            "find a way we can design existing roads to exist with "
            "existing structures and enable them for reuse",
        wer="52%", wwer="47%", is_score="3.02",
        is_tier="Good", judge="P",
        category="Domain Vocabulary Drift \u2014 structure intact, terms swapped",
        # audit:bigfonts — annotation trimmed (cut "Without domain context,
        # the model picks the most likely words" — in speaker notes).
        # CUT v3: kept structure observation; per-token mapping moved
        # to speaker notes.
        annotation="Argument structure perfect: 'radically different "
                   "approach' \u2192 'find a way' \u2192 'existing X' \u2192 "
                   "'enable for Y'. Networking terms become civil terms.",
        notes="Technical vocabulary drift: the argument structure is perfectly "
              "preserved but networking terms (routers, switches, links) become "
              "civil engineering terms (roads, structures). The model lacks "
              "domain context. LLM judge rates P. IS 3.02 (Good).")


def slide_judge_ex4(prs):
    """Judge example 4: Scientific vocabulary lost — cortisol → stops (IS 2.67)."""
    _judge_video_slide(prs,
        vid_key="judge_cortisol",
        title="Judge Example 4: Scientific Vocabulary Lost",
        ref="couples us to light cycles in our environment "
            "tells us when to sleep tells us when to make "
            "cortisol tells us when to make testosterone "
            "basically switches on",
        hyp="takes into account our environment tells us what "
            "to eat tells us where to make turns tells us when "
            "to make stops basically switches on",
        wer="43%", wwer="57%", is_score="2.67",
        is_tier="Fair", judge="P",
        category="Scientific Terms Lost \u2014 repetitive structure preserved",
        # CUT v3: dropped the WWER/WER comparison sentence (in speaker
        # notes); kept the structure-vs-vocabulary observation.
        annotation="'Tells us when to X' pattern preserved 3x. But "
                   "every scientific term is wrong: cortisol \u2192 turns, "
                   "testosterone \u2192 stops, light cycles \u2192 (gone).",
        notes="Scientific vocabulary destroyed: cortisol becomes 'turns', "
              "testosterone becomes 'stops', light cycles dropped entirely. "
              "But the repetitive rhetorical structure ('tells us when to X') "
              "is perfectly preserved. WWER > WER because high-value content "
              "words are wrong. LLM judge: P. IS 2.67 (Fair).")


def slide_judge_ex5(prs):
    """Judge example 5: Cooking domain confusion — jalapeno → banana (IS 2.07)."""
    _judge_video_slide(prs,
        vid_key="judge_jalapeno",
        title="Judge Example 5: Cooking Domain Confusion",
        ref="and i have a tablespoon of jalapeno fresh jalapeno",
        hyp="and i have a dietary smoothie i've got the "
            "banana called fresh banana",
        wer="89%", wwer="44%", is_score="2.07",
        is_tier="Fair", judge="P",
        category="Domain Confusion \u2014 food context right, ingredients wrong",
        # CUT v3: dropped the multimodal-context sentence (in notes);
        # kept the food-domain-vs-ingredient observation.
        annotation="Model knows it's a cooking video ('smoothie', "
                   "'banana', 'fresh') but picks the wrong ingredient: "
                   "jalapeno \u2192 banana.",
        notes="Cooking domain confusion. WER is 89%, WWER drops to 44% "
              "because the rare entity 'jalapeno' is the dominant high-value "
              "token; once it is wrong, low-value words barely matter. The "
              "model correctly infers the food domain (smoothie, banana, "
              "fresh) but picks the wrong specific ingredient — jalapeno "
              "becomes banana. A viewer who can see the pepper on screen "
              "would override the garbled text immediately, which is exactly "
              "the visual-context recovery loop our IS framework is meant to "
              "anticipate. The LLM judge rates P; IS is 2.07, in the Fair "
              "tier. Mention to peers: this slide motivates topic-aware "
              "prompting in Mission 8 — domain priors at decode time would "
              "narrow the candidate vocabulary to peppers vs. fruits. "
              "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
              "docs/prompts/ (Mission 8 design notes).")


def slide_judge_ex6(prs):
    """Judge example 6: Topic hijack — overhead lights → ghost whisperer (IS 1.79)."""
    _judge_video_slide(prs,
        vid_key="judge_lights",
        title="Judge Example 6: Topic Hijack",
        ref="i actually use the overhead lights which are "
            "mostly fluorescent which i know is a big no no "
            "but this camera",
        hyp="i actually used the overheard ghost whisperer "
            "music for that scene which i know is about to "
            "go on but the scene runs",
        wer="74%", wwer="69%", is_score="1.79",
        is_tier="Poor", judge="P",
        category="Topic Hijack \u2014 grammatically fluent, completely wrong topic",
        # audit:bigfonts — annotation trimmed (cut "this is what makes
        # hallucinations dangerous" sentence — in speaker notes).
        # CUT v3: dropped the "phonetic cascade \u2026 wrong continuation"
        # detail (in notes); kept the topic-hijack observation.
        annotation="Phonetic cascade: 'overhead lights' \u2192 'overheard "
                   "ghost whisperer'. Grammatically perfect, but the "
                   "topic is completely replaced.",
        notes="Topic hijack: 'overhead lights' sounds like 'overheard ghost "
              "whisperer' to the visual encoder. The model then generates a "
              "grammatically perfect continuation about TV production. This is "
              "a classic hallucination pattern — fluent, coherent, completely "
              "wrong. LLM judge: P (the model produces something). IS 1.79 (Poor).")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE — LLM JUDGE HTML REPORT SCREENSHOT (HIDDEN BACKUP)
# ═══════════════════════════════════════════════════════════════════════

def slide_judge_report_screenshot(prs):
    """Hidden slide: full-page screenshot of the 30-sample HTML report."""
    # audit:bigfonts — single full-width image; no body text to bump.
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge Report (30 Samples)")
    add_accent_line(slide)

    # Full-width report screenshot
    img = add_image(slide, "llm_judge_report", MX, CT, width=CW, height=Inches(5.4))

    _finish(slide, 0,
        "Screenshot of the interactive HTML report (30 stratified samples from "
        "1,497-segment dataset). Color-coded word diffs: green = match, "
        "yellow = substitution, red = insertion. Columns: WER, WWER, NEA F1, IS, "
        "LLM Judge verdict (Y/P/N). Distribution: Y=23%, P=40%, N=37%, "
        "Y+P=63%. Mean WER 61%, Mean IS 2.67/5.0.",
        [[img]])


# ═══════════════════════════════════════════════════════════════════════
# IS vs OPUS JUDGE DISAGREEMENT SLIDES
# ═══════════════════════════════════════════════════════════════════════

def slide_disagreement_blind(prs):
    """Where IS and the Judge Disagree — blind evaluation."""
    # audit:bigfonts — bumps fit existing 5.8x4.2 card layout; no trims.
    slide = new_slide(prs)
    add_title(slide, "Where IS and the Judge Disagree")
    add_accent_line(slide)

    # Subtitle
    sub = add_text(slide,
        "22 of 1,497 segments (2%) — rare but revealing edge cases",
        MX, CT, CW, Inches(0.35),
        size=Pt(20), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # --- Two cards side by side ---
    card_w = Inches(5.8)
    card_h = Inches(4.2)
    gap = Inches(0.53)
    card_y = CT + Inches(0.55)

    # LEFT CARD — IS Too Harsh (green border)
    left_shapes = []
    r_l = add_rect(slide, MX, card_y, card_w, card_h,
                   fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                   corner_radius=True)
    left_shapes.append(r_l)

    left_shapes.append(add_rich_text(slide, [
        [("IS Too Harsh", {"size": Pt(24), "color": GREEN, "bold": True}),
         ("  \u2014  19 cases (1%)", {"size": Pt(24), "color": LGRAY})],
    ], MX + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(1.0)))

    left_shapes.append(add_text(slide,
        "Judge says Y (meaning conveyed)\nIS says < 3.0 (metric failure)",
        MX + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=LGRAY))

    # Example
    left_shapes.append(add_rect(slide,
        MX + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    left_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"one really nice thing about this is\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"what a brilliant idea this is\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("IS = 1.84  |  WER = 71%  |  Judge: Y",
          {"size": Pt(24), "color": LGRAY})],
    ], MX + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(2.6)))

    # OVERLAP fix: shrink italic textbox to h=0.45 (ends y=card_y+3.25),
    # leaving clean gap before the bullet list at y=card_y+3.3.
    left_shapes.append(add_text(slide,
        "Paraphrases and phonetic bridges preserve\n"
        "meaning that word-level metrics punish.",
        MX + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=GREEN, italic=True))

    # Also add remaining root causes
    left_shapes.append(add_text(slide,
        "\u2022 Harmless hallucination (extra words, core intact)\n"
        "\u2022 Short segments amplify WER disproportionately",
        MX + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(1.8),
        size=Pt(24), color=LGRAY))

    # RIGHT CARD — IS Too Generous (red border)
    right_shapes = []
    rx = MX + card_w + gap
    r_r = add_rect(slide, rx, card_y, card_w, card_h,
                   fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                   corner_radius=True)
    right_shapes.append(r_r)

    right_shapes.append(add_rich_text(slide, [
        [("IS Too Generous", {"size": Pt(24), "color": CORAL, "bold": True}),
         ("  \u2014  3 cases (0%)", {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5), Inches(1.0)))

    right_shapes.append(add_text(slide,
        "Judge says N (meaning lost)\nIS says \u2265 3.0 (metric pass)",
        rx + Inches(0.25), card_y + Inches(0.55),
        card_w - Inches(0.5), Inches(1.0),
        size=Pt(24), color=LGRAY))

    # Example
    right_shapes.append(add_rect(slide,
        rx + Inches(0.25), card_y + Inches(1.1),
        card_w - Inches(0.5), Inches(1.5),
        fill_color=NAVY3, corner_radius=True))

    right_shapes.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"all you have to do is unscrew\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"all you have to do is not to\"",
          {"size": Pt(24), "color": WHITE, "italic": True})],
        [("IS = 3.42  |  WER = 29%  |  Judge: N",
          {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.4), card_y + Inches(1.2),
       card_w - Inches(0.8), Inches(2.6)))

    # OVERLAP fix (mirror of left card): shrink italic textbox to h=0.45.
    right_shapes.append(add_text(slide,
        "Structural match hides semantic reversal \u2014\n"
        "IS cannot detect that meaning is inverted.",
        rx + Inches(0.25), card_y + Inches(2.8),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=CORAL, italic=True))

    right_shapes.append(add_text(slide,
        "\u2022 Domain confusion (medical \u2192 wellness)\n"
        "\u2022 Word salad with scattered correct words",
        rx + Inches(0.25), card_y + Inches(3.3),
        card_w - Inches(0.5), Inches(1.4),
        size=Pt(24), color=LGRAY))

    # Bottom strip
    # CUT v3: top 6.35 -> 6.20 + frame h 1.0 -> 0.40 so Pt(24) bottom
    # stays under safe 7.05 (was 7.20).
    bot = add_text(slide,
        "98% agreement \u2014 disagreements are edge cases, not systemic failure",
        MX, Inches(6.02), CW, Inches(1.0),
        size=Pt(24), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "IS vs Opus Judge disagreement analysis (blind evaluation, all 1,497 "
        "pairs). Headline: 22 segments (2% of the corpus) sit in the "
        "disagreement region; 98% of the dataset agrees. The 22 "
        "split into 19 IS-too-harsh cases (judge Y, IS<2.00) and 3 "
        "IS-too-generous cases (judge N, IS>=2.00).\n\n"
        "LEFT — IS False Negatives (19 cases, 1%): paraphrases, phonetic "
        "bridges, and harmless hallucinations that preserve core meaning but "
        "score poorly on word-level signals. The headline left-card example "
        "('one really nice thing about this is' -> 'what a brilliant idea "
        "this is') sits at WER 71% / IS 1.84 / Judge Y — every content word "
        "is substituted yet the affirmative-praise meaning survives, which "
        "is exactly the case WER over-punishes. Additional examples: "
        "'living in space' topic preserved (IS 1.98, WER 111%); 'human "
        "implications' captures 'human application' (IS 2.06, WER 100%); "
        "'to the next level' intact with trailing words added (IS 2.32, "
        "WER 100%).\n\n"
        "RIGHT — IS False Positives (3 cases, 0%): semantic reversal "
        "('unscrew' -> 'not to', IS 3.42, WER 29% — structural match hides "
        "the meaning inversion); domain swap ('blood extraction, "
        "x-ray' -> 'cut hair, ashram', IS 3.14); phonetic garbage ('one "
        "twitch is all you do' -> 'one to rich is all the', IS 3.01). The "
        "operating thresholds in this slide are NIV-Y (IS>=3.80, kappa=0.690) "
        "and NIV-Y+P (IS>=2.00, kappa=0.818) calibrated against the same "
        "Opus judge.\n\n"
        "PEER DETAIL — 98% agreement = 1,466/1,497 segments fall in the "
        "same Y+P-vs-N bucket. The 22-segment disagreement region splits "
        "19 IS-too-harsh + 3 IS-too-generous.\n\n"
        "Sources: docs/evaluation/llm_judge/llm_judge_analysis.md, "
        "docs/evaluation/threshold_calibration_vs_opus.md.",
        [left_shapes, right_shapes, [bot]], click_reveal=True)


def slide_disagreement_context(prs):
    """Context makes the judge stricter — disagreement examples."""
    # audit:bigfonts — bumps fit existing layout; no trims.
    slide = new_slide(prs)
    add_title(slide, "Context Exposes Hidden Failures")
    add_accent_line(slide)

    # --- Left side: compact transition matrix ---
    left_w = Inches(5.5)

    lt = add_text(slide, "Blind \u2192 Context Transitions",
                  MX, CT, left_w, Inches(1.0),
                  size=Pt(24), color=TEAL, bold=True)

    # Transition matrix
    tbl = add_table(slide,
        ["", "\u2192 Y", "\u2192 P", "\u2192 N"],
        [["Y (345)", "207", "138", "0"],
         ["P (626)", "17", "517", "92"],
         ["N (526)", "1", "50", "475"]],
        MX, CT + Inches(0.5), left_w, text_size=Pt(24),
        col_widths=[Inches(1.6), Inches(1.3), Inches(1.3), Inches(1.3)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Key stat below matrix
    stat = add_rich_text(slide, [
        [("230 downgrades", {"size": Pt(24), "color": CORAL, "bold": True}),
         (" vs ", {"size": Pt(24), "color": WHITE}),
         ("68 upgrades", {"size": Pt(24), "color": GREEN, "bold": True})],
        [("Y\u2192P dominant (138): domain knowledge reveals vocabulary failures",
          {"size": Pt(24), "color": LGRAY})],
    ], MX, CT + Inches(2.6), left_w, Inches(1.8))

    # OVERLAP fix: cap bullet height to 1.4 (was 1.8) so block ends at
    # CT+4.8 = 6.25 \u2014 leaves clean gap above bottom strip at y=6.35.
    # CUT v3: trimmed bullets to 2 short lines + Pt 24->22 so the
    # rendered wrap stays within 1.4" frame (audit bottom 7.25 -> 6.65).
    # Original third bullet ("Context is a quality tool\u2026") now in notes.
    # audit:FONT_BELOW_24PT_BODY \u2014 restored Pt(24) body floor; 2 short
    # bullets fit 1.4" frame at 5.5" width (max 3 wrapped lines @ 0.40" =
    # 1.20" content height).
    add_bullets(slide, [
        "80% stable across modes",
        ("Context tightens, never rescues (1 N\u2192Y in 1,497)",
         {"color": TEAL, "bold": True}),
    ], MX, CT + Inches(3.4), left_w, Inches(1.4), size=Pt(24))

    # --- Right side: killer example ---
    rx = MX + left_w + Inches(0.6)
    rw = CW - left_w - Inches(0.6)

    rt = add_text(slide, "The IS = 4.75 False Positive",
                  rx, CT, rw, Inches(0.35),
                  size=Pt(24), color=CORAL, bold=True)

    # Example card
    ex_card = []
    ex_r = add_rect(slide, rx, CT + Inches(0.5), rw, Inches(2.8),
                    fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                    corner_radius=True)
    ex_card.append(ex_r)

    ex_card.append(add_rich_text(slide, [
        [("IS = 4.75", {"size": Pt(24), "color": CORAL, "bold": True}),
         ("  (near perfect!)", {"size": Pt(24), "color": LGRAY})],
    ], rx + Inches(0.2), CT + Inches(0.6), rw - Inches(0.4), Inches(0.4)))

    ex_card.append(add_rich_text(slide, [
        [("REF: ", {"size": Pt(24), "color": TEAL, "bold": True}),
         ("\"...because I'm ", {"size": Pt(24), "color": WHITE, "italic": True}),
         ("a lover of", {"size": Pt(24), "color": GREEN, "bold": True, "italic": True}),
         ("\"", {"size": Pt(24), "color": WHITE, "italic": True})],
        [("HYP: ", {"size": Pt(24), "color": GOLD, "bold": True}),
         ("\"...because I'm ", {"size": Pt(24), "color": WHITE, "italic": True}),
         ("not a lover of", {"size": Pt(24), "color": CORAL, "bold": True, "italic": True}),
         ("\"", {"size": Pt(24), "color": WHITE, "italic": True})],
    ], rx + Inches(0.2), CT + Inches(1.15), rw - Inches(0.4), Inches(1.8)))

    # OVERLAP fix: shifted from CT+2.0 to CT+2.10 so it clears the REF/HYP
    # rich_text block above which ends at CT+2.05 (audit OVERLAP 6%).
    ex_card.append(add_text(slide,
        "One word reverses the meaning.\n"
        "IS rated this near-perfect \u2014 only 10% WER.\n"
        "Context-aware judge caught the negation.",
        rx + Inches(0.2), CT + Inches(2.10),
        rw - Inches(0.4), Inches(1.8),
        size=Pt(24), color=LGRAY))

    # C2 (research-overview pacing): "more context false positives" inline
    # list dropped from body \u2014 full list moved to speaker notes; appendix
    # A9 (Context Transition Matrix) shows the full structure.
    more = add_text(slide,
        "Full list of context false positives \u2014 see Appendix A9.",
        rx, CT + Inches(3.5), rw, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # Bottom strip
    # CUT v3: top 6.35 -> 6.20 + frame h 1.0 -> 0.40 so Pt(24) bottom
    # stays under safe 7.05.
    bot = add_text(slide,
        "Domain knowledge raises the bar \u2192 strongest case for domain-aware fine-tuning",
        MX, Inches(6.02), CW, Inches(1.0),
        size=Pt(24), color=GOLD, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware disagreement analysis.\n\n"
        "LEFT: Transition matrix shows 230 downgrades vs 68 upgrades when "
        "the judge gains domain context. Y->P is dominant (138 cases). "
        "Context never rescues failures (only 1 N->Y in 1,497 pairs).\n\n"
        "RIGHT: The most striking false positive — IS = 4.75 (near perfect) "
        "for a segment where one word ('not') reversed the meaning entirely. "
        "WER on this segment is just 10% (single inserted word) and IS is "
        "4.75, yet meaning is fully inverted — context-aware judge caught "
        "the negation while blind judge rated it P.\n\n"
        "Additional context false positives show domain vocabulary swaps: "
        "hair care -> space (lazy natural -> lazy astronaut); "
        "knitting -> medical (needle -> neck, decreases -> skin grafting); "
        "US education -> international (student loan debt -> south korea, "
        "US marshals -> US marketers).\n\n"
        "These 11 context false positives (IS >= 3.80 but context N) are the "
        "strongest argument for domain-aware fine-tuning: the model resolves "
        "lip movements to the wrong vocabulary domain. Mention to peers: this "
        "is the empirical hook for Mission 8 (topic-aware prompting) and "
        "Mission 9 (domain-targeted fine-tuning). 80% of the 1,497 "
        "judgments are stable across both modes; the disagreement region is "
        "narrow but interpretable. "
        "Sources: docs/evaluation/llm_judge/context_eval/context_eval_analysis.md, "
        "docs/evaluation/llm_judge/llm_judge_analysis.md.",
        [[lt, tbl, stat], ex_card, [more, bot]], click_reveal=True)


# ============================================================================
# NEW SLIDES - Section 2 literature framing + Section 4 confidence + n-best
# (May 2026 - companion to docs/evaluation/after_amosi_audit.json)
# Body text >= 12pt; OOXML 3-level par nesting via _finish(... click_reveal=True)
# ============================================================================


def slide_literature_metrics_problem(prs):
    """Section 2 - Why WER/CER does not separate 'wrong but useful' from
    'wrong and dangerous' in the AVSR/VSP literature.

    2-card click-reveal layout: left = what the literature reports;
    right = what end users (and downstream models) actually consume.

    audit:bigfonts — bumps fit existing 5.8x4.2 card layout (verified line-
    counts at 18pt: 5 left bullets x ~1.5 lines = 7.5 lines = 2.0" in 2.55"
    box; right card 2 pairs at h=0.85 each = 0.54" content per pair).
    """
    slide = new_slide(prs)
    add_title(slide, "What the AVSR Literature Reports vs What Users Get")
    add_accent_line(slide)

    sub = add_text(slide,
        "AVSR / VSP papers (LRS3, LRW, AVSpeech) report WER almost exclusively. "
        "WER conflates failure modes a downstream user would never confuse.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    card_w = Inches(5.8)
    card_h = Inches(4.2)
    gap = Inches(0.53)
    card_y = CT + Inches(0.65)

    # LEFT - what the literature reports
    L = []
    L.append(add_rect(slide, MX, card_y, card_w, card_h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "WHAT THE LITERATURE REPORTS",
             MX + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5),
             Inches(0.4), size=Pt(24), color=TEAL, bold=True))
    # CUT v3: trimmed 5 long bullets to 4 short ones; removed CER /
    # BLEU detail and inlined the LRS3-numbers bullet — full list
    # remains in speaker notes. Frame height kept at 2.55".
    L.append(add_bullets(slide, [
        ("WER — primary metric in nearly every AVSR benchmark",
         {"bold": True}),
        "CER, BLEU/METEOR on side decks",
        ("Implicit: WER is monotone in usefulness", {"color": CORAL}),
        "Reported on LRS3: AV-HuBERT 25%, AutoAVSR 19%",
    ], MX + Inches(0.25), card_y + Inches(0.65),
       card_w - Inches(0.5), Inches(3.4), size=Pt(24)))
    # OVERLAP fix: bullets shrunk from h=3.0 to 2.55 (end y=card_y+3.20);
    # callout moved up from y=card_y+3.40 to 3.30 with h=0.65 (was 0.7).
    # CUT v3: shrunk callout to 20pt + tightened wording; full text
    # in speaker notes. Frame width unchanged.
    L.append(add_text(slide,
        "All three failure modes score the same WER if edit distance matches.",
        MX + Inches(0.25), card_y + Inches(3.30),
        card_w - Inches(0.5), Inches(0.65),
        size=Pt(20), color=CORAL, italic=True))

    # RIGHT - what users see
    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, card_y, card_w, card_h, fill_color=NAVY2,
                     border_color=GOLD, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "WHAT END USERS ACTUALLY CONSUME",
             rx + Inches(0.25), card_y + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=GOLD, bold=True))

    # Three example pairs - same WER ~50%, very different downstream value.
    # audit-md:section_C examples (judge_entity / judge_lights examples).
    R.append(add_text(slide, "Same WER ~50% - very different downstream value:",
             rx + Inches(0.25), card_y + Inches(0.65),
             card_w - Inches(0.5), Inches(1.0),
             size=Pt(24), color=WHITE, bold=True))

    pairs = [
        ("Partial / useful",
         "REF: \"market research firm bernreuter is forecasting pv installations\"\n"
         "HYP: \"market research firm rogers is forecasting pv installations\"",
         GREEN),
        ("Topic hijack / dangerous",
         "REF: \"the overhead lights are mostly fluorescent\"\n"
         "HYP: \"the overheard ghost whisperer music for that scene\"",
         CORAL),
    ]
    # OVERLAP fix: shrink each pair's body height from 1.05 to 0.85 and
    # tighten py stride from 1.4 to 1.25 so the second pair ends at
    # card_y + 1.05 + 1.25 + 0.30 + 0.85 = card_y + 3.45, well above the
    # bottom-row callout at card_y + card_h - 0.55 = card_y + 3.65.
    # CUT v3: pair body shrunk from 24pt to 18pt (caption-tier per
    # STYLE_GUIDE T1 footnote/example exemption) so 120-char REF+HYP
    # pairs fit in 0.85" without overflowing. Labels stay 22pt for
    # visual hierarchy.
    py = card_y + Inches(1.05)
    for label, body, color in pairs:
        R.append(add_text(slide, label,
                 rx + Inches(0.25), py, card_w - Inches(0.5),
                 Inches(0.3), size=Pt(22), color=color, bold=True))
        R.append(add_text(slide, body,
                 rx + Inches(0.25), py + Inches(0.3),
                 card_w - Inches(0.5), Inches(1.4),
                 size=Pt(18), color=LGRAY))
        py += Inches(1.25)

    # CUT v3: shrunk callout 24->20pt to fit one line.
    R.append(add_text(slide,
        "Same WER, very different downstream value.",
        rx + Inches(0.25), card_y + card_h - Inches(0.55),
        card_w - Inches(0.5), Inches(0.87),
        size=Pt(20), color=GOLD, italic=True))

    # audit:after_amosi_narrative_actions.md fix #14 - "next slide"
    # phrasing replaced with reorder-robust language.
    # CUT v3: shrunk 24->20pt + tightened phrasing so the bottom
    # callout fits in one line at y=6.5 without crossing the safe zone.
    bot = add_text(slide,
        "Therefore we built IS — the Intelligibility Score.",
        MX, Inches(6.5), CW, Inches(0.35),
        size=Pt(20), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Sources: docs/evaluation/after_amosi_audit.md (Section C, LLM-judge "
        "examples) and docs/evaluation/intelligibility_methodology.md "
        "(WER-IS dissociation). The point of this slide is to frame why we "
        "needed IS at all: the AVSR / VSP literature (LRS3, LRW, AVSpeech) "
        "reports WER almost exclusively (AV-HuBERT 25%, AutoAVSR 19% on "
        "LRS3), and WER conflates three downstream-distinct failure modes — "
        "gibberish, partial-but-useful, and fluent-hallucination. The "
        "bernreuter/rogers entity swap and the overhead-lights/"
        "ghost-whisperer topic hijack both score ~50% WER yet a downstream "
        "consumer treats them very differently — one is partially usable, the "
        "other actively misroutes every downstream tag. About 25% of "
        "segments in our 1,497-segment evaluation set fall into a band where "
        "WER and intelligibility actively disagree, which directly motivates "
        "the Intelligibility Score introduced in the next subsection.",
        [[sub], L, R, [bot]], click_reveal=True)


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
             "p_t  =  max_v  P(token = v | x_<=t)",
             x1 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(1.0),
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
    ], x1 + Inches(0.3), top + Inches(1.6),
       card_w - Inches(0.6), Inches(1.8), size=Pt(20)))

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
             card_w - Inches(0.6), Inches(1.0),
             size=Pt(24), bold=True, color=WHITE))
    R.append(add_text(slide,
             "mean_prob  =  exp( (1/T) * sum_t log p_t )",
             x2 + Inches(0.3), top + Inches(1.05),
             card_w - Inches(0.6), Inches(1.0),
             size=Pt(24), color=GOLD, italic=True, align=PP_ALIGN.CENTER))
    # audit:after_amosi_narrative_actions.md fix #13 - the demo cards
    # later in the deck use the term "sequence_conf"; add an alias bullet
    # here so the audience can match the demo cards back to mean_prob.
    # CUT v3: 4 bullets at Pt(24) wrapped to ~12 lines, bottom 8.40.
    # Trimmed text + Pt(24)->Pt(20). Full long-form retained in notes.
    R.append(add_bullets(slide, [
        "Length-anomaly check (too short / too long)",
        ("T_trust 0.89, T_safe 0.82, T_salvage 0.74",
         {"color": TEAL}),
        ("Strip below 0.65 (green flag misleads)",
         {"color": CORAL}),
        ("Demo cards label this sequence_conf",
         {"color": LGRAY, "italic": True}),
    ], x2 + Inches(0.3), top + Inches(1.6),
       card_w - Inches(0.6), Inches(2.87), size=Pt(20)))

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
        "rule = top1_conf>=0.95 AND beam_agreement>=0.80; legacy = conf only.",
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
    L.append(add_text(slide, "JOINT RULE - STRICTER, MORE RELIABLE",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=BLUE, bold=True))
    # CUT v3: bullets trimmed + Pt(24)->Pt(20) so 3 bullets fit in
    # 2.0" frame (was rendering bottom 8.60). Long-form retained in notes.
    L.append(add_bullets(slide, [
        "Green drops 33% (11,309 → 7,591)",
        "Reds 2× (4,482 → 9,099): ambiguous → red",
        ("Each green more reliable (90% vs 81%)",
         {"color": GREEN, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.55),
       card_w - Inches(0.5), Inches(2.0), size=Pt(20)))

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
    ], rx + Inches(0.25), cy + Inches(0.55),
       card_w - Inches(0.5), Inches(2.0), size=Pt(20)))

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
        "P(correct | green) stratified by segment mean_prob bin. "
        "Green ranges from 96% (clean segments) to 18% (noisy ones).",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    img = add_image(slide, "P_band_reliability_stratified",
                    MX, CT + Inches(0.5),
                    width=Inches(7.6), height=Inches(4.6))

    rx = MX + Inches(7.8)
    rw = CW - Inches(7.8)
    rt = add_text(slide, "Stratified P(green | bin)",
                  rx, CT + Inches(0.5), rw, Inches(1.0),
                  size=Pt(24), color=BLUE, bold=True)

    # Joint-rule bins (>=0.65 only) - per audit:section_D...stratified_by_seg_mean_conf
    headers = ["seg mean_prob", "P(grn correct)"]
    rows = [
        ["0.85+ (very_high)", "96%"],   # audit:section_D...very_high.green_p_correct
        ["0.75-0.85 (high)",  "92%"],   # audit:section_D...high.green_p_correct
        ["0.65-0.75 (mid)",   "86%"],   # audit:section_D...mid.green_p_correct
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(24), row_height=Inches(0.4))

    leg_t = add_text(slide,
        "Below 0.65 (legacy rule only):\n"
        "0.55-0.65: 41%\n"
        "0.40-0.55: 22%\n"
        "<0.40:    18%",
        rx, CT + Inches(2.5), rw, Inches(1.6),
        size=Pt(24), color=LGRAY)

    # CUT v3: shrunk 24pt -> 18pt italic-caption + tightened wording.
    # Full caveat preserved in speaker notes.
    caveat = add_text(slide,
        "Joint-rule numbers above are filtered to >=0.65 bins; "
        "below-0.65 are legacy conf-only.",
        rx, CT + Inches(4.2), rw, Inches(0.85),
        size=Pt(18), color=CORAL, italic=True)

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
        [[sub, img], [rt, tbl, leg_t, caveat], [bot]], click_reveal=True)


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
    add_title(slide, "Three Calibrated Thresholds on Segment mean_prob")
    add_accent_line(slide)

    # audit:after_amosi_narrative_actions.md fix #13 - first visible NIV
    # mention is in this slide's table, so the subtitle now glosses it
    # once for the audience: "NIV = Native Intelligibility Verdict (the
    # LLM-as-Judge calibration label, NIV-Y / NIV-P / NIV-N)".
    sub = add_text(slide,
        "Each threshold corresponds to a target on green-band reliability. "
        "NIV = Native Intelligibility Verdict (LLM-as-Judge calibration label).",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    headers = ["Threshold", "mean_prob", "Green reliability target", "Notes"]
    rows = [
        ["T_trust",   ">= 0.89", ">= 90% reliable", "highest precision, lowest recall"],
        ["T_safe",    ">= 0.82", ">= 85% reliable", "F1-max for NIV-Y on mean_prob"],
        ["T_salvage", ">= 0.74", ">= 75% reliable", "review zone"],
        ["Strip-coloring", "< 0.65", "< 50%",        "below this, drop word colour entirely"],
    ]
    row_colors = {
        0: {0: BLUE,   2: BLUE},
        1: {0: GREEN,  2: GREEN},
        2: {0: ORANGE, 2: ORANGE},
        3: {0: PURPLE, 2: PURPLE},
    }
    # audit:pptx_visual_audit_after_amosi.md slide 53 BLOCKER -
    # Table 4 extended past canvas (right=13.70 vs canvas 13.33). Sum was
    # 2.4+2.0+3.6+5.1=13.1" > CW(12.13"). Trimmed to fit within CW.
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.2), Inches(1.8), Inches(3.1),
                                Inches(4.6)],
                    text_size=Pt(24), row_colors=row_colors)

    # audit:bigfonts2 — op rect h shrunk 1.95 -> 1.65, bullets h 1.30 -> 1.05
    # to clear bot footer + slide-num zone.
    op = []
    op.append(add_rect(slide, MX, CT + Inches(3.2), CW, Inches(1.65),
                       fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                       corner_radius=True))
    op.append(add_text(slide, "T_safe (mean_prob >= 0.82) - operational default",
             MX + Inches(0.3), CT + Inches(3.30), CW - Inches(0.6),
             Inches(0.40), size=Pt(24), color=GREEN, bold=True))
    op.append(add_bullets(slide, [
        "Keeps 28% volume; IS_kept = 4.01",
        "WER_kept = 28%; Precision 71%; Recall 79% (NIV-Y)",
    ], MX + Inches(0.3), CT + Inches(3.75),
       CW - Inches(0.6), Inches(1.00), size=Pt(24)))

    # audit:bigfonts2 — bot pushed back to 6.55 (was 6.75 → bottom 7.15
    # overlapped slide-num); op rect ends at CT+3.2+1.95 = 6.60. Now 6.55+0.40
    # = 6.95 ≤ 7.05. CUT v2: shortened text to fit smaller box.
    bot = add_text(slide,
        "Thresholds are Llama-2-7b specific; LLM swap = re-fit needed.",
        MX, Inches(6.37), CW, Inches(0.40),
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
        "Tiers from segment mean_prob; per-tier P(green correct) under "
        "joint rule. Volumes from per_word_by_tier.csv.",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    # All numbers from audit:section_D_per_word_conf.by_tier.{Trust,Salvage,Strip}.new
    headers = ["Tier", "Green n", "P(grn corr)", "Yellow n", "P(yel corr)",
               "Red n", "P(red corr)"]
    rows = [
        ["Trust    (>=0.82)",   "3,923", "95%", "1,719", "76%", "  951", "42%"],
        ["Salvage (0.65-0.82)","3,091", "89%", "3,241", "60%", "3,442", "28%"],
        ["Strip   (<0.65)",     "  577", "56%", "1,611", "38%", "4,706", "13%"],
    ]
    row_colors = {
        0: {0: BLUE,   2: GREEN},
        1: {0: ORANGE, 2: GOLD},
        2: {0: PURPLE, 2: CORAL},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.55), CW, row_height=Inches(0.55),
                    col_widths=[Inches(2.6), Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6),
                                Inches(1.5), Inches(1.6)],
                    text_size=Pt(24), row_colors=row_colors)

    L = []
    L.append(add_text(slide, "WHAT THE NUMBERS SAY",
             MX, CT + Inches(2.6), Inches(6.0), Inches(0.35),
             size=Pt(24), color=TEAL, bold=True))
    L.append(add_bullets(slide, [
        ("Trust: green is 95% reliable. Auto-approve.", {"color": BLUE, "bold": True}),
        ("Salvage: green is 89%. Pair with reviewer.", {"color": ORANGE}),
        ("Strip: green is 56% - misleading. Drop colours.",
         {"color": PURPLE, "bold": True}),
    ], MX, CT + Inches(3.0), Inches(6.0), Inches(2.5), size=Pt(24)))

    R = []
    R.append(add_text(slide, "HOW THE TIERS ARE USED",
             MX + Inches(6.3), CT + Inches(2.6), Inches(5.83), Inches(0.35),
             size=Pt(24), color=GOLD, bold=True))
    # CUT v3: bullets compressed + Pt(24)->Pt(20) so 4 bullets fit in 2.5"
    # frame (was rendering bottom 9.25). Long-form retained in notes.
    R.append(add_bullets(slide, [
        "Post-hoc: no re-decode required",
        "Feeds client UI threshold knob",
        "Red P(correct) stays low across tiers (42/28/13%)",
        ("Audit: by_tier.*.new.*.p_correct",
         {"color": LGRAY, "italic": True}),
    ], MX + Inches(6.3), CT + Inches(3.0), Inches(5.83), Inches(2.5),
       size=Pt(20)))

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
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    img = add_image(slide, "P_band_reliability_by_niv",
                    MX, CT + Inches(0.5),
                    width=Inches(7.6), height=Inches(4.6))

    rx = MX + Inches(7.8)
    rw = CW - Inches(7.8)

    rt = add_text(slide, "P(correct | band)",
                  rx, CT + Inches(0.5), rw, Inches(0.3),
                  size=Pt(24), color=TEAL, bold=True)

    # audit-md:band_reliability_by_niv (no flat key in audit JSON)
    headers = ["Tier", "GRN", "YEL", "RED"]
    rows = [
        ["Y+P combined", "87%", "49%", "25%"],
        ["NIV-Y only",   "94%", "65%", "39%"],
        ["NIV-P only",   "80%", "41%", "20%"],
        ["NIV-N only",   "37%", "17%",  "7%"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.85), rw,
                    text_size=Pt(24), row_height=Inches(0.4))

    # OVERLAP fix: shrink take height from 2.7 to 2.05 so bullets end at
    # CT+4.90 = 6.35 — clear of the bottom-row source caption at y=6.55.
    # CUT v3: bullets compressed + Pt(24)->Pt(18) so 3 bullets fit in
    # 2.05" frame at narrow 4.93" width (was rendering bottom 9.10).
    # Long-form retained in notes.
    take = add_bullets(slide, [
        ("62.5pp green→red spread in Y+P", {"bold": True, "color": GREEN}),
        ("NIV-P: steepest (80/41/20%)", {"color": ORANGE}),
        ("NIV-N: green misleads (37%)", {"color": PURPLE}),
    ], rx, CT + Inches(2.85), rw, Inches(2.05), size=Pt(18))

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
        "Production rule. Two axes: per-token softmax "
        "AND beam-agreement across the n-best alternatives.",
        MX, CT, CW, Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True)

    card_w = (CW - Inches(0.6)) / 3
    card_h = Inches(2.4)
    gap = Inches(0.3)
    cy = CT + Inches(0.6)

    bands = [
        ("GREEN", BLUE,
         "top1_conf >= 0.95  AND  beam_agreement >= 0.80"),
        ("YELLOW", ORANGE,
         "top1_conf >= 0.65  AND  beam_agreement >= 0.50"),
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
        # CUT v3: trimmed text + frame h 2.2 -> 1.65 so Pt(24) wrap stays
        # under safe 7.05 (was rendering bottom 7.20). Long-form in notes.
        "WHY ADD AGREEMENT?  Beam agreement is ~2× more informative than "
        "top-1 conf at high conf — at conf ≥ 0.95, agreement spread takes "
        "P(correct) from 0.40 → 0.94 (54pp gap).",
        MX + Inches(0.3), CT + Inches(3.55), CW - Inches(0.6),
        Inches(1.65), size=Pt(24), color=WHITE))

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
        "At top1_conf >= 0.95 the softmax says 'almost certain.' Beam "
        "agreement reveals which of those tokens were actually unique.",
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # audit:after_amosi_logic_fixes.md fix #6 - prior copy paired
    # "0.94 / 0.62" with "32pp gap" but those are the conf>=0.65 numbers.
    # At top1_conf>=0.95 (the green-band threshold), the spread is
    # 0.94 / 0.40 = 54pp. Source:
    # english_full_nbest_eval/trust_diagnostic/TRUST_DIAGNOSTIC.md Test C.
    headers = ["", "agreement >= 0.80", "agreement < 0.80"]
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
             MX, CT + Inches(2.5), CW, Inches(0.35),
             size=Pt(24), color=TEAL, bold=True))
    # CUT v3: bullets compressed so 4 bullets fit in 2.5" frame at Pt(24)
    # (was rendering bottom 7.60). Long-form retained in notes.
    why.append(add_bullets(slide, [
        ("54pp P(correct) gap at SAME top-1 conf (0.40 vs 0.94)",
         {"bold": True}),
        "Conf alone collapses 2 populations into one green band",
        ("Beam_agreement: ~2× AUC of top1_conf at conf≥0.95",
         {"color": TEAL}),
        ("Green: 11,309 → 7,591 words, P(correct) 81% → 90%",
         {"color": GREEN}),
    ], MX, CT + Inches(2.95), CW, Inches(2.5), size=Pt(24)))

    # CUT v4: one-line caveat so bottom = 6.45 + 0.50 = 6.95 <= 7.05.
    bot = add_text(slide,
        "Diagnostic: diagnose_confidence_signals.py — Llama-2-7b specific.",
        MX, Inches(6.45), CW, Inches(0.50),
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
        MX, CT, CW, Inches(0.5),
        size=Pt(18), color=LGRAY, italic=True)

    # All from audit Section E new_rule_joint_conf_agreement
    headers = ["Threshold", "n trusted", "Recall", "Precision", "FPR",
               "% clearly conveyed in trust"]
    rows = [
        # audit:trustgate_new_t10_*
        ["fraction-green >= 10%", "1,041", "92%", "82%", "37%", "34%"],
        # audit:trustgate_new_t20_*
        ["fraction-green >= 20%",   "818", "81%", "91%", "14%", "43%"],
        # audit:trustgate_new_t30_*
        ["fraction-green >= 30%  (default)", "630", "65%", "96%",  "6%", "52%"],
        # audit:trustgate_new_t50_*
        ["fraction-green >= 50%",   "321", "34%", "97%",  "2%", "72%"],
        # audit:trustgate_new_t70_*
        ["fraction-green >= 70%",    "71",  "8%", "99%",  "0%", "89%"],
    ]
    row_colors = {
        2: {0: BLUE, 1: BLUE, 2: GREEN, 3: GREEN, 4: GREEN, 5: GREEN},
    }
    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.6), CW, row_height=Inches(0.5),
                    col_widths=[Inches(3.5), Inches(1.4), Inches(1.4),
                                Inches(1.7), Inches(1.4), Inches(2.7)],
                    text_size=Pt(24), row_colors=row_colors)

    pick = add_text(slide,
        "Recommended default: 30% green words -> 65% recall, 6% FPR. "
        "Pick higher thresholds for mission-critical workflows; lower for "
        "high-recall research workflows.",
        MX, CT + Inches(3.7), CW, Inches(1.4),
        size=Pt(24), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    # CUT v3: top 6.5 -> 6.30 + h 0.8 -> 0.55 + trimmed so Pt(18) bottom
    # stays under safe 7.05 (was 7.30). Audit-key list moved to notes.
    bot = add_text(slide,
        "Calibrated under joint conf+agreement rule.",
        MX, Inches(6.30), CW, Inches(0.55),
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
    cap_methods = add_text(slide,
        "Below: IS distribution per method (top1 / MBR / vote_score / vote_conf).",
        MX, CT + Inches(4.75), Inches(6.5), Inches(0.8),
        size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)  # audit:fix_round3 footer-overlap

    rx = MX + Inches(6.7)
    rw = CW - Inches(6.7)

    headers = ["Method", "Y%", "Y+P%", "YP McNemar p"]
    rows = [
        # audit:judge_v3_y_pct_baseline / _yp_pct_baseline
        ["baseline",       "13%", "68%", "-"],
        # audit:judge_v3_y_pct_mbr / _yp_pct_mbr / mcnemar_yp_p_mbr
        ["hyp_mbr",        "14%", "71%", "0.00017 ***"],
        # audit:judge_v3_y_pct_vote_score / _yp_pct_vote_score
        ["hyp_vote_score", "14%", "69%", "0.149 (n.s.)"],
        # audit:judge_v3_y_pct_vote_conf / _yp_pct_vote_conf / mcnemar_yp_p_vote_conf
        ["hyp_vote_conf",  "12%", "70%", "0.00257 **"],
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
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.6), rw,
                    text_size=Pt(24), row_height=Inches(0.5),
                    col_widths=[Inches(1.9), Inches(0.9), Inches(1.0),
                                Inches(1.6)],
                    row_colors=row_colors)

    # audit:bigfonts2 — V6: 4 -> 3 bullets, each <=8 words, h 2.85 -> 1.85.
    # CUT v2: dropped "Y verdict tied" (already in the McNemar table).
    take = add_bullets(slide, [
        ("MBR +40 Y+P wins, p=0.00017",
         {"color": GREEN, "bold": True}),
        ("vote_conf +31 Y+P wins, p=0.00257",
         {"color": GREEN}),
        ("Drift v3: 12-14% (was 27%) — dual-conf fixed bias",
         {"color": TEAL}),
    ], rx, CT + Inches(3.0), rw, Inches(1.85), size=Pt(24))

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
    add_title(slide, "Why MBR Won the Default-Display Slot")
    add_accent_line(slide)

    # CUT v2: shortened sub-text from 3 lines -> 1.
    sub = add_text(slide,
        "MBR wins on intra-rater reliability + posterior compatibility.",
        MX, CT, CW, Inches(0.45),
        size=Pt(20), color=LGRAY, italic=True)

    headers = ["Criterion", "hyp_mbr", "hyp_vote_conf", "Winner"]
    rows = [
        # audit:mcnemar_yp_p_*
        ["Y+P paired McNemar p",   "0.00017",     "0.00257",      "tie  (both significant)"],
        # audit:mcnemar_yp_method_only_*
        ["Y+P win delta",          "+40",         "+31",          "MBR"],
        # audit:judge_v3_intrarater_exact_*
        ["Intra-rater (exact)",    "87%",       "80%",        "MBR  (matches gold std 83%)"],
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
       CW - Inches(0.6), Inches(1.8), size=Pt(24)))

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
    ch = Inches(4.2)

    L = []
    L.append(add_rect(slide, MX, cy, card_w, ch, fill_color=NAVY2,
                     border_color=CORAL, border_width=Pt(2), corner_radius=True))
    L.append(add_text(slide, "v1 - conf-in-prompt (broken)",
             MX + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(0.35), size=Pt(24), color=CORAL, bold=True))
    # CUT v3: bullets compressed + Pt(24)->Pt(20) so 5 bullets fit in
    # 3.5" frame at 5.35" width (was rendering bottom 7.45). Long-form
    # retained in notes.
    L.append(add_bullets(slide, [
        ("Method-conf only in prompt", {"bold": True}),
        "Judge read high method-conf as reliable",
        ("Y+P: vote_conf loses (p < 0.05)", {"color": CORAL}),
        ("Identical-text drift: 27%", {"color": CORAL}),
        ("Bias: against n-best variants", {"color": CORAL, "bold": True}),
    ], MX + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.5), size=Pt(20)))

    R = []
    rx = MX + card_w + gap
    R.append(add_rect(slide, rx, cy, card_w, ch, fill_color=NAVY2,
                     border_color=GREEN, border_width=Pt(2), corner_radius=True))
    R.append(add_text(slide, "v3 - dual-conf prompt (current)",
             rx + Inches(0.25), cy + Inches(0.15), card_w - Inches(0.5),
             Inches(1.0), size=Pt(24), color=GREEN, bold=True))
    # CUT v3: bullets compressed + Pt(24)->Pt(20). Long-form in notes.
    R.append(add_bullets(slide, [
        ("Method-conf AND baseline_conf shown", {"bold": True}),
        "Judge anchors method to baseline",
        ("Y+P: vote_conf wins (p = 0.00257)", {"color": GREEN}),
        ("Identical-text drift: 12.6/10.4/14%", {"color": GREEN}),
        ("Bias: balanced", {"color": GREEN, "bold": True}),
    ], rx + Inches(0.25), cy + Inches(0.6),
       card_w - Inches(0.5), Inches(3.5), size=Pt(20)))

    lesson = []
    lesson.append(add_rect(slide, MX, Inches(6.0), CW, Inches(0.7),
                           fill_color=NAVY3, border_color=GOLD,
                           border_width=Pt(1.5), corner_radius=True))
    # CUT v3: trimmed to one line + Pt(24); original 3-clause text in notes.
    lesson.append(add_text(slide,
        "LESSON: provide BOTH sides' confidence — single-sided injection biases the judge.",
        MX + Inches(0.3), Inches(5.95), CW - Inches(0.6),
        Inches(1.0), size=Pt(24), color=GOLD, bold=True))

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
# DEMO SLIDES — research-flavored versions of the client examples (Task E)
# All five reuse the existing IMG video keys; speaker notes disclose decode
# artefact gaps (Obama clips fall back to conf-only, no VSP_NBEST=1).
# ============================================================================


def _demo_research_slide(prs, *, title, video_key, ref, hyp_runs,
                         metrics_line, badge_text, badge_color, body, notes):
    """Shared layout for the five research-flavored demo slides.

    Centered hero video + REF (label/text) + colour-coded HYP + metrics line +
    research observation body. Per-word band cited as observation, not pitch.
    audit:bigfonts — REF/HYP bumped to 18pt, body observation 16pt; video
    shrunk slightly (6.0->5.4 wide, 3.4->2.9 high) to free room for big-font
    REF + HYP + body all fitting between y=5.0 and y=7.30. Body observation
    intentionally trimmed to <=2 lines so 16pt fits in a single textbox.
    """
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    badge_w = Inches(2.4)
    sub = add_text(slide, metrics_line,
             MX, Inches(1.5), CW - badge_w - Inches(0.2), Inches(0.4),
             size=Pt(16), color=LGRAY, italic=True)
    badge_x = MX + CW - badge_w
    badge_box = add_rect(slide, badge_x, Inches(1.5), badge_w, Inches(0.4),
             fill_color=NAVY3, border_color=badge_color, border_width=Pt(1.0))
    # CUT v3 (overflow): 0.3 -> 0.45 + Pt(24) -> Pt(20) so badge text fits.
    badge_t = add_text(slide, badge_text,
             badge_x, Inches(1.50), badge_w, Inches(0.45),
             size=Pt(20), bold=True, color=badge_color, align=PP_ALIGN.CENTER)

    # audit:bigfonts — video shrunk from 6.0x3.4 to 5.4x2.9 to free vertical
    # space for 18pt REF + HYP + body lines. Original size comment kept as
    # # vid_w_orig=Inches(6.0); vid_h_orig=Inches(3.4); vid_y_orig=Inches(2.05)
    vid_w = Inches(5.4)
    vid_h = Inches(2.9)
    vid_x = (SL_W - vid_w) // 2
    vid_y = Inches(2.00)
    # audit:pptx_visual_audit_after_amosi.md slides 64-68 BLOCKER -
    # Animation references shape id 7 (the embedded movie) which is wrapped
    # in <mc:AlternateContent> and therefore invisible to slide.shapes
    # iteration in the audit script (and to many OOXML consumers). The video
    # is left out of anim_groups so it just renders on entry without an
    # Appear timing entry; nothing else changes. Same root cause as the
    # slide_15 fix below.
    vid = add_video(slide, video_key, vid_x, vid_y, vid_w, vid_h)

    # CUT v3: pulled REF/HYP/body up by ~0.2 each so Pt(16) body wrap
    # (was rendering bottom 7.30/7.38) stays under safe-zone 7.05.
    # REF block (label + body) — 18pt body
    add_text(slide, "REFERENCE",
             MX, Inches(4.90), CW, Inches(0.32),
             size=Pt(24), bold=True, color=LGRAY)
    ref_t = add_text(slide, ref,
             MX, Inches(5.22), CW, Inches(0.45),
             size=Pt(18), color=LGRAY, italic=True)

    # CUT v3 (overflow): hyp_t 0.5 -> 0.85 so 24pt rich_text 2-line fits.
    add_text(slide, "HYPOTHESIS  (per-word band)",
             MX, Inches(5.75), CW, Inches(0.30),
             size=Pt(20), bold=True, color=WHITE)
    hyp_t = add_rich_text(slide, [hyp_runs],
             MX, Inches(6.05), CW, Inches(0.85))

    # Body observation — 16pt floor (one tier down) because the bottom strip
    # only fits ~2 lines at 16pt.
    body_t = add_text(slide, body,
             MX + Inches(0.65), Inches(6.55), CW - Inches(0.65), Inches(0.45),
             size=Pt(16), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0, notes,
            [[sub, badge_box, badge_t], [ref_t], [hyp_t], [body_t]],
            click_reveal=True)


def slide_live_example_intro(prs):
    """Early example — Obama 14 (29 words, all green) — sets the bar.

    Placed near the start of the deck (after 'What is VSP?') to give the
    audience a concrete, visceral taste of what the system delivers
    BEFORE diving into pipeline + benchmarks + metrics. Same Obama clip
    used later in slide 60's demo intro for callback.
    """
    # Sample of the per-word coloring (full transcript is in REF + the video).
    runs = [
        ("…the ", {"size": Pt(22), "color": BLUE}),
        ("tireless and heroic ", {"size": Pt(22), "color": BLUE, "bold": True}),
        ("work of our ", {"size": Pt(22), "color": BLUE}),
        ("counterterrorism", {"size": Pt(22), "color": GOLD, "italic": True}),
        (" professionals…", {"size": Pt(22), "color": BLUE}),
    ]
    _demo_research_slide(prs,
        title="Live example — clean speech, perfect transcription",
        video_key="obama_perfect",
        ref="and our allies over the last 10 years thanks to the tireless "
            "and heroic work of our military and our counterterrorism "
            "professionals we've made great strides in that effort",
        hyp_runs=runs,
        metrics_line="WER 0%   /   IS 5.00 (Excellent)   /   29 words   "
                     "/   27 of 29 GREEN  (per-word conf)",
        badge_text="TIER: TRUST",
        badge_color=BLUE,
        body="Reference and prediction are identical (WER 0%). 27 of 29 "
             "per-word confidence bands GREEN — the model is sure, and "
             "it's right.",
        notes="Early-deck taste: this is the upper bound. Obama bin "
              "Laden announcement segment 14 (41.95-45.55 s, 29 words). "
              "REF and HYP are character-for-character identical: "
              "'and our allies over the last 10 years thanks to the "
              "tireless and heroic work of our military and our "
              "counterterrorism professionals we've made great strides "
              "in that effort'. WER = 0%, IS = 5.00 (Tier 5 Excellent), "
              "27 of 29 per-word confidence bands GREEN at high "
              "conf-only threshold (this Obama decode predates "
              "VSP_NBEST=1 so the joint conf+agreement rule is not "
              "applied — but the visual is the same, and at 27/29 green "
              "the upgrade would not change the picture). Why this "
              "slide opens the deck: research peers see the punchline "
              "first — 'yes, the system can deliver perfect output on "
              "real-world video' — before the metric debate. This "
              "primes the rest of §1 ('but is it always like this?' → "
              "no, average is 62% NIV-Y+P, hence the metric work in "
              "§2). Same clip recurs as the leftmost tile in slide 60's "
              "demo intro, anchoring a callback. "
              "Source: flat_runs_archive/20260430_234843/"
              "client_outputs/report/report.csv "
              "(050111_OsamaBinLadenStatement_HD_14_004195_004555).")


def slide_failure_live_demo(prs):
    """Two live failure mode examples side by side: Partial Failure + Hallucination.

    LEFT: street_photo — topic captured, names lost (WER 56%, IS 2.91, NIV-Y+P).
    RIGHT: halluc — total hallucination, fluent fabrication (WER 100%, IS 0.81).
    Chosen to span the failure spectrum: "not that bad" vs "worst case".
    Column width 5.85" triggers the narrow-column audit exemption (18pt floor).
    """
    slide = new_slide(prs)
    add_title(slide, "Failure Modes — Live Examples")
    add_accent_line(slide)

    # Two columns filling CW exactly: 5.85 + 0.43 + 5.85 = 12.13"
    col_w = Inches(5.85)
    gap = Inches(0.43)
    start_x = MX  # = 0.6"

    vid_h = Inches(2.65)
    vid_y = CT + Inches(0.05)   # = 1.50"

    tiles = [
        {
            "key": "street_photo",
            "label": "Right Topic, Names Lost",
            "color": ORANGE,
            "ref": "\u201cjames and will talk about street photography\u201d",
            "hyp": "\u201ci'm here to talk about street photography\u201d",
            "wer": "WER 56%  \u00b7  IS 2.91 (Fair)  \u00b7  INSPECT",
        },
        {
            "key": "halluc",
            "label": "Hallucination",
            "color": RED,
            "ref": "\u201c\u2026it doesn't have a carry strap\u201d",
            "hyp": "\u201cthis is david irving he's a holocaust "
                   "denier and a computer hacker\u201d",
            "wer": "WER 100%  \u00b7  IS 0.81 (Failed)  \u00b7  STRIP",
        },
    ]

    # base offsets relative to (vid_y + vid_h).
    # lbl h=0.50 accommodates 24pt 1-liner; badge h=0.36 accommodates 18pt
    # 1-liner (badge text kept to <42 chars to avoid wrap); spacing designed
    # so hyp_t bottom lands at base+2.85 = 4.15+2.85 = 7.00 < 7.05 safe-zone.
    base_offsets = {
        "lbl":      Inches(0.07),   # h=0.50 → bottom base+0.57
        "badge":    Inches(0.62),   # h=0.36 → bottom base+0.98
        "ref_lbl":  Inches(1.03),   # h=0.28 → bottom base+1.31
        "ref_t":    Inches(1.34),   # h=0.55 → bottom base+1.89
        "hyp_lbl":  Inches(1.94),   # h=0.28 → bottom base+2.22
        "hyp_t":    Inches(2.25),   # h=0.60 → bottom base+2.85
    }

    anim_groups = []
    for i, t in enumerate(tiles):
        x = start_x + i * (col_w + gap)
        base = vid_y + vid_h

        add_video(slide, t["key"], x, vid_y, col_w, vid_h)

        lbl = add_text(slide, t["label"],
                x, base + base_offsets["lbl"], col_w, Inches(0.50),
                size=Pt(24), bold=True, color=t["color"],
                align=PP_ALIGN.CENTER)

        badge = add_text(slide, t["wer"],
                x, base + base_offsets["badge"], col_w, Inches(0.36),
                size=Pt(18), color=WHITE, bold=True,
                align=PP_ALIGN.CENTER)

        ref_lbl = add_text(slide, "REFERENCE",
                x, base + base_offsets["ref_lbl"], col_w, Inches(0.28),
                size=Pt(18), bold=True, color=LGRAY)

        ref_t = add_text(slide, t["ref"],
                x, base + base_offsets["ref_t"], col_w, Inches(0.55),
                size=Pt(18), color=LGRAY, italic=True)

        hyp_lbl = add_text(slide, "HYPOTHESIS",
                x, base + base_offsets["hyp_lbl"], col_w, Inches(0.28),
                size=Pt(18), bold=True, color=WHITE)

        hyp_t = add_text(slide, t["hyp"],
                x, base + base_offsets["hyp_t"], col_w, Inches(0.60),
                size=Pt(18), color=t["color"], italic=True)

        anim_groups.append([lbl, badge, ref_lbl, ref_t, hyp_lbl, hyp_t])

    _finish(slide, 0,
        "Two live failure examples chosen to span the spectrum: 'not that bad' "
        "vs worst case. "
        "LEFT — Right Topic, Names Lost (street photography): segment "
        "2HddWQse8Mw_0__8ecb0409_00_000000_000072. "
        "Reference: 'james and will talk about street photography and other'. "
        "Hypothesis: 'i'm here to talk about street photography and all the'. "
        "WER 55.6%, IS 2.91 (Tier 3 Fair, NIV-Y+P), mean_prob 0.602 (Strip band). "
        "Teaching point: IS 2.91 says this is USEFUL — the topic 'street "
        "photography' survived, only the speaker names (james, will) were lost. "
        "A viewer who needs to know the subject gets something real from this. "
        "The confidence (Strip, mean_prob 0.602) flagged uncertainty correctly — "
        "the model didn't know whose talk it was, and it showed that. "
        "RIGHT — Hallucination (carry strap): segment "
        "00MUdHQ7GGY_8__b1480c7a_00_000000_000194. "
        "Reference: 'it doesn't have a carry strap but you can put it on your "
        "shoulder pretty easily or just carry it with your hand'. "
        "Hypothesis: 'this is david irving he's a holocaust denier and a "
        "computer hacker who broke into the nuremberg trials'. "
        "WER 100%, IS 0.81 (Tier 1 Failed), mean_prob 0.468 (Strip band). "
        "This is the worst failure mode: the LLM generated a completely unrelated, "
        "fluent, harmful-sounding sentence. Length ratio >> 1 (hallucination "
        "pattern). Strip auto-flags it. "
        "Narrative: use LEFT to show 'sometimes it fails gracefully — useful "
        "content comes through, only specifics are lost'; use RIGHT to show "
        "'sometimes it fails catastrophically — the system flags these.' "
        "Sources: english_full_nbest_eval/report_v2/report.csv.",
        anim_groups, click_reveal=True)


def slide_demo_obama_trust(prs):
    """TRUST exemplar — non-trivial speaker, AI talk, full agreement-aware rule.

    Replaced Obama segment 14 (prepared political statement, too easy a TRUST
    example) with a non-Obama IS=5.00 / WER=0% segment: South-Asian speaker
    with Indian English accent talking about "this wave of artificial
    intelligence". Same TRUST tier (mean_prob 0.988), but a harder visual
    target — proves the model handles diverse speakers, not just rehearsed
    political video. VSP_NBEST=1 sidecar available, so the joint
    conf+agreement rule applied.
    """
    # Per-word colors all BLUE (TRUST band) — every word is high-conf + high-agreement.
    runs = [
        ("to this wave of ", {"size": Pt(22), "color": BLUE}),
        ("artificial intelligence ", {"size": Pt(22), "color": BLUE, "bold": True}),
        ("that is slowly taking place", {"size": Pt(22), "color": BLUE}),
    ]
    _demo_research_slide(prs,
        title="Demo — TRUST: AI talk, Indian-accent speaker (IS=5.00)",
        video_key="clean_tech",
        ref="to this wave of artificial intelligence that is slowly taking place",
        hyp_runs=runs,
        metrics_line="WER 0%   /   IS 5.00   /   mean_prob = 0.988   "
                     "(VSP_NBEST=1, joint band rule)",
        badge_text="TIER: TRUST",
        badge_color=BLUE,
        body="Every word GREEN under the joint rule. Diverse speaker, "
             "Indian-English accent, perfect transcription.",
        notes="Non-Obama TRUST exemplar (segment "
              "K0h33Ps7vz4_11__e66d3063_00_000000_000103, ~4s, IS=5.00 / "
              "WER=0% / mean_word_prob=0.988). South-Asian speaker with "
              "Indian English accent, talking about 'this wave of "
              "artificial intelligence'. Reference + hypothesis identical: "
              "'to this wave of artificial intelligence that is slowly "
              "taking place'. Why this is the right TRUST opener: a "
              "rehearsed political statement (Obama) is the easiest "
              "possible visual target — clear lighting, frontal face, "
              "minimal head movement. This clip carries higher visemic "
              "difficulty (different accent, different mouth shapes, "
              "casual gesture) and the model still hits IS=5. Joint "
              "conf+agreement rule applied (VSP_NBEST=1 sidecar available). "
              "NIV-Y green-band reliability for this population is 94% "
              "per the band-reliability stratification earlier in this "
              "section. Anchors the Trust → Salvage → Strip tour that "
              "follows on the next two slides. "
              "Sources: english_full_nbest_eval/report_v2/report.csv, "
              "docs/confidence/band_reliability_by_niv.md.")


def slide_demo_obama_salvage(prs):
    """Obama segment 31 - partial recovery (TRUST badge under conf-only)."""
    # audit:after_amosi_asset_fixes.md fix #9 - title previously claimed
    # "Salvage Tier (partial recovery)" but the rendered video shows the
    # TRUST badge: Obama seg 31 mean_prob = 0.920 which is above T_safe
    # (0.82), so the production tier is TRUST and not Salvage. The Obama
    # decode predates VSP_NBEST=1, so the joint conf+agreement rule is
    # not applied (no agreement sidecar) - the slide silently falls back
    # to conf-only band painting. Title now discloses the badge mismatch
    # and the metrics_line reports the correct mean_prob.
    runs = [
        ("[per-word colors load from the conf-only sidecar; ", {"size": Pt(24), "color": LGRAY}),
        ("'said' substitution is the visible orange word]",
         {"size": Pt(24), "color": LGRAY, "italic": True}),
    ]
    _demo_research_slide(prs,
        title="Demo — Obama: Trust Tier (conf-only fallback)",
        video_key="obama_partial",
        ref="(see speaker notes; Obama bin Laden announcement, segment #31, 92.90-96.50 s)",
        hyp_runs=runs,
        metrics_line="WER ~ 22%   /   IS ~ 3.5   /   sequence_conf mixed   "
                     "/   mean_prob = 0.920  (TRUST under T_safe=0.82)",
        badge_text="TIER: TRUST",
        badge_color=BLUE,
        # audit:bigfonts — body trimmed from 5 sentences to 2 to fit 16pt.
        # Cut: "The TRUST badge (mean_prob>=0.82) reflects the conf-only
        # fallback because this Obama decode predates VSP_NBEST=1; the joint
        # rule would likely demote the segment."  (kept in speaker notes.)
        body="Most words green. The 'president bush did' -> 'said' "
             "substitution shows orange under conf-only rule.",
        notes="Obama bin Laden announcement, segment #31 (92.90-96.50 s). "
              "WER ~22%, IS ~3.5, mean_prob = 0.920 — above T_safe (0.82), "
              "so the production tier under the conf-only fallback is "
              "TRUST not Salvage. The original slide title called this "
              "'Salvage' for narrative continuity, but the badge mismatch "
              "is real: this Obama decode predates VSP_NBEST=1 (shipped "
              "April 30 2026) so no agreement sidecar exists, and the "
              "per-word band rule silently falls back to top1_conf only. "
              "Re-running stage 8 (outputs.sh::run_outputs) on a "
              "VSP_NBEST=1 decode would likely push this segment to "
              "Salvage under the joint rule because the substituted "
              "'said' almost certainly has low beam_agreement. The "
              "reviewer still triages off the orange word; this slide "
              "demonstrates the narrative-vs-production-tier gap that "
              "the joint rule closes. Mention to peers: this is the "
              "clearest worked example of why the agreement axis pulls "
              "high-conf-but-disagreed words out of green into yellow. "
              "Sources: docs/confidence/band_reliability_by_niv.md, "
              "docs/beam-search/n_best_implementation.md.")


def slide_demo_obama_strip(prs):
    """INSPECT-tier example — circadian/hormone segment, structure preserved.

    Replaced Obama segment 5 with a non-Obama INSPECT exemplar: the model
    keeps the "tells us when to X" repeating-clause structure but loses
    the domain vocabulary (cortisol/testosterone/light cycles → eat/turns/
    stops). mean_prob = 0.739 sits squarely in the Salvage band (0.65 ≤
    mean_prob < 0.82), and the clip was rendered with the full
    agreement-aware joint rule (VSP_NBEST=1 sidecar available).
    """
    # audit:after_amosi_narrative_actions.md fix #13 - first INSPECT
    # mention; gloss it inline so the audience knows it is the
    # production label for what the research literature calls 'Salvage'.
    # Per-word color sample: structure-preserved (BLUE) "tells us when to make"
    # vs domain-vocab replacement (ORANGE/PURPLE).
    runs = [
        ("tells us when to make ", {"size": Pt(22), "color": BLUE}),
        ("stops", {"size": Pt(22), "color": PURPLE, "bold": True}),
        (" — vs ref's ", {"size": Pt(22), "color": LGRAY}),
        ("cortisol/testosterone", {"size": Pt(22), "color": ORANGE, "italic": True}),
    ]
    _demo_research_slide(prs,
        title="Demo — INSPECT: structure preserved, vocabulary lost",
        video_key="judge_cortisol",
        ref="couples us to light cycles in our environment tells us when "
            "to sleep tells us when to make cortisol tells us when to "
            "make testosterone basically switches on",
        hyp_runs=runs,
        metrics_line="WER 43%   /   IS 2.66 (Salvage)   /   "
                     "mean_prob = 0.739   /   min word conf 0.12  "
                     "(VSP_NBEST=1, joint band rule)",
        badge_text="TIER: INSPECT",
        badge_color=ORANGE,
        body="Repeating 'tells us when to X' structure preserved, but "
             "domain vocabulary (cortisol, testosterone) replaced.",
        notes="Non-Obama INSPECT exemplar (segment "
              "9HanJOCw2Sc_11__19c7ec4e_00_000000_000261, ~13s). "
              "Reference: '… couples us to light cycles in our "
              "environment tells us when to sleep tells us when to make "
              "cortisol tells us when to make testosterone basically "
              "switches on'. Hypothesis: 'the job prescription takes "
              "into account our environment tells us what to eat tells "
              "us where to make turns tells us when to make stops "
              "basically switches on'. WER 43%, NEA F1 43% (lost "
              "entities: cortisol, couples, cycles, light, sleep, "
              "testosterone), IS 2.66 (Tier 3 Fair, NIV-Y+P). mean_prob "
              "= 0.739, sequence_conf in the Salvage band (0.65–0.82). "
              "min word conf = 0.12 on entity-replacement tokens "
              "(stops). Why this is a clean INSPECT: the "
              "circadian/hormones → behaviour-script semantic drift is "
              "a recoverable failure mode for a viewer who knows the "
              "topic, but the model still flagged the entity replacements "
              "via the joint conf+agreement rule. Per-word colors render "
              "from the agreement-aware sidecar (this decode had "
              "VSP_NBEST=1, unlike Obama segments). Sources: "
              "english_full_nbest_eval/report_v2/report.csv, "
              "docs/confidence/band_reliability_by_niv.md.")


def slide_demo_judge_entity(prs):
    """Judge entity slide - now shows STRIP badge for rogers / PV / will (research).

    Per render-log finding, judge_entity now shows STRIP badge under joint
    rule (rogers / pv / will all flagged red).
    """
    runs = [
        ("market ",       {"size": Pt(24), "color": BLUE}),
        ("research ",     {"size": Pt(24), "color": BLUE}),
        ("firm ",         {"size": Pt(24), "color": BLUE}),
        ("rogers ",       {"size": Pt(24), "color": PURPLE, "bold": True}),
        ("research ",     {"size": Pt(24), "color": BLUE}),
        ("is ",           {"size": Pt(24), "color": BLUE}),
        ("forecasting ",  {"size": Pt(24), "color": BLUE}),
        ("pv ",           {"size": Pt(24), "color": PURPLE, "bold": True}),
        ("installations ",{"size": Pt(24), "color": BLUE}),
        ("will ",         {"size": Pt(24), "color": PURPLE, "bold": True}),
        ("reach",         {"size": Pt(24), "color": BLUE}),
    ]
    # audit:after_amosi_asset_fixes.md fix #10 - mean_prob updated from
    # ~0.71 to 0.624 to match
    # english_full_nbest_eval/report_v2/report.csv (segment
    # 4D634qUi2BI_0__93a9f2b4_00_000000_000122, sentence_confidence=0.624,
    # is_label=Strip). Also fix #11 - explicit VSP_NBEST=1 disclosure
    # added (slide pulls per-word colours from the agreement-aware
    # sidecar, unlike the Obama slides).
    _demo_research_slide(prs,
        title="Demo - Strip: entity swap auto-flagged",
        video_key="judge_entity",
        ref="market research firm bernreuter research is forecasting "
            "pv installations could reach",
        hyp_runs=runs,
        metrics_line="WER 18%   /   IS 4.55   /   sequence_conf mixed   "
                     "/   mean_prob = 0.624  (Strip; full agreement-aware "
                     "rule applied, VSP_NBEST=1)",
        badge_text="TIER: STRIP",
        badge_color=PURPLE,
        # audit:bigfonts — body trimmed (was: "Research observation: the
        # entity-swap tokens 'rogers', 'pv', 'will' are auto-flagged red
        # under the joint rule. Strengthens the entity-swap narrative.")
        body="Entity-swap tokens 'rogers', 'pv', 'will' auto-flagged red "
             "under the joint rule.",
        notes="Source: slides_client.py::slide_client_judge_ex1 (reframed "
              "for research). bernreuter -> rogers entity swap; PV / "
              "will also flagged red under the joint conf+agreement rule "
              "(per render-log inspection). WER 18%, IS 4.55 (Excellent), "
              "LLM judge Y. mean_prob = 0.624 per "
              "english_full_nbest_eval/report_v2/report.csv "
              "(prior copy said ~0.71, corrected per "
              "after_amosi_asset_fixes.md fix #10). The badge is STRIP "
              "not TRUST because the joint rule pushes the entity-swap "
              "tokens to red (per-word agreement low even though top-1 "
              "conf may be high). DECODE MODE: this clip was decoded "
              "with VSP_NBEST=1 so the agreement-aware sidecar is "
              "present and the full joint rule (top1_conf>=0.95 AND "
              "beam_agreement>=0.80) is applied (unlike the Obama clips "
              "earlier in this section, which fall back to conf-only "
              "band painting). audit:judge_v3_y_count_baseline picks "
              "this segment up; the per-word band overlay separates "
              "the firm-name swap from the rest.")


def slide_demo_judge_vocab(prs):
    """Judge router slide - technical-vocab drift (research framing)."""
    # audit:bigfonts — trimmed from 18 tokens to 11 to fit one line at 18pt
    # in the demo helper's HYP textbox. Cut the leading filler clause
    # ("we need a radically different approach we") — the band-painted swap
    # ("design"/"roads") is what the slide demonstrates.
    runs = [
        ("must ",       {"size": Pt(24), "color": ORANGE}),
        ("indeed ",     {"size": Pt(24), "color": ORANGE}),
        ("find ",       {"size": Pt(24), "color": BLUE}),
        ("a ",          {"size": Pt(24), "color": BLUE}),
        ("way ",        {"size": Pt(24), "color": BLUE}),
        ("we ",         {"size": Pt(24), "color": BLUE}),
        ("can ",        {"size": Pt(24), "color": BLUE}),
        ("design ",     {"size": Pt(24), "color": PURPLE}),
        ("existing ",   {"size": Pt(24), "color": BLUE}),
        ("roads ",      {"size": Pt(24), "color": PURPLE, "bold": True}),
        ("...",         {"size": Pt(24), "color": LGRAY}),
    ]
    # audit:after_amosi_asset_fixes.md fix #11 - explicit VSP_NBEST=1
    # disclosure added so the audience knows the per-word reds came from
    # the full joint conf+agreement rule (not the conf-only fallback
    # used by the Obama clips earlier in this section).
    _demo_research_slide(prs,
        title="Demo - Salvage: technical vocabulary drift",
        video_key="judge_router",
        ref="we need a radically different approach we basically need "
            "to find a way how we can take existing routers existing "
            "switches existing links and enable them for research",
        hyp_runs=runs,
        metrics_line="WER 52%   /   IS 3.02   /   sequence_conf mixed   "
                     "/   mean_prob ~ 0.78  (Salvage; full agreement-aware "
                     "rule applied, VSP_NBEST=1)",
        badge_text="TIER: SALVAGE",
        badge_color=ORANGE,
        # audit:bigfonts — body trimmed from 4 clauses to 2. Cut: "per-word
        # reds isolate the swaps; reviewer can patch the vocab" (in notes).
        body="Argument structure preserved (green spine). Domain terms "
             "drift: 'routers/switches/links' -> 'roads/structures/reuse'.",
        notes="Networking-research segment where the model preserved the "
              "argument structure but swapped the domain vocabulary "
              "(routers -> roads, switches -> structures, links -> reuse). "
              "WER 52%, IS 3.02 (Good tier), LLM judge P, mean_prob "
              "~0.78 (Salvage tier). DECODE MODE: this clip was decoded "
              "with VSP_NBEST=1 enabled so the agreement-aware sidecar is "
              "present and the full joint rule (top1_conf >= 0.95 AND "
              "beam_agreement >= 0.80) is applied — unlike the Obama "
              "clips earlier in this section, which fall back to "
              "conf-only band painting. Per-word colours show a green "
              "argument spine and red domain-vocabulary swaps. The "
              "per-word band isolates the exact tokens that need a "
              "domain-aware re-decode pass — exactly the case Mission 8 "
              "(topic-aware prompting) is designed to address. Mention "
              "to peers: this is the cleanest demonstration of "
              "per-tier reliability paying off in production. "
              "Sources: docs/confidence/band_reliability_by_niv.md, "
              "docs/evaluation/llm_judge/llm_judge_analysis.md.")
