#!/usr/bin/env python3
"""
Argos — The Orchard — Gemini Presentation Maker Instructions

Generates a branded .docx with 4 sequential Gemini prompts for creating
the Argos VSP project review presentation (30 slides).

Usage:
    python3 generate_gemini_instructions.py

Output:
    presentation_materials_20260224/gemini_presentation_instructions.docx
"""

from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml, OxmlElement

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"
OUTPUT_DIR = Path("/home/ubuntu/presentation_materials_20260224")
OUTPUT_FILE = OUTPUT_DIR / "gemini_presentation_instructions.docx"

LOGO_ORCHARD = ASSETS_DIR / "logo.png"
LOGO_PEACOCK = ASSETS_DIR / "peacock.png"

# ── Standard Colors ──
C_PRIMARY = RGBColor(0x1A, 0x3A, 0x5C)
C_H2 = RGBColor(0x2A, 0x5A, 0x8C)
C_H3 = RGBColor(0x3A, 0x6A, 0x9C)
C_H4 = RGBColor(0x4A, 0x7A, 0xAC)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x66, 0x66, 0x66)
C_CODE = RGBColor(0x2D, 0x2D, 0x2D)
C_TEAL = RGBColor(0x00, 0x80, 0x80)
C_CORAL = RGBColor(0xE0, 0x6C, 0x75)

HEADER_BG = "1a3a5c"
ZEBRA_BG = "f0f4f8"
CODE_BG = "f5f5f5"
PROMPT_BG = "eef6ee"   # light green for prompt blocks
TEAL_BG = "e0f2f1"
CORAL_BG = "fce4ec"

LAST_UPDATED = datetime.now().strftime("%B %d, %Y")


# ═══════════════════════════════════════════════════
# STANDARD HELPERS
# ═══════════════════════════════════════════════════

def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_text(cell, text, bold=False, color=None, size=None, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(str(text))
    run.bold = bold
    if color:
        run.font.color.rgb = color
    if size:
        run.font.size = size
    run.font.name = "Calibri"


def add_styled_table(doc, headers, rows, col_widths=None, highlight_rows=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_shading(cell, HEADER_BG)
        set_cell_text(cell, h, bold=True, color=C_WHITE, size=Pt(9))
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            set_cell_text(cell, val, size=Pt(9))
            if highlight_rows and r_idx in highlight_rows:
                set_cell_shading(cell, highlight_rows[r_idx])
            elif r_idx % 2 == 1:
                set_cell_shading(cell, ZEBRA_BG)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return table


def add_heading(doc, text, level, color=None):
    h = doc.add_heading(text, level=level)
    if color is None:
        color = {1: C_PRIMARY, 2: C_H2, 3: C_H3, 4: C_H4}.get(level, C_PRIMARY)
    for run in h.runs:
        run.font.color.rgb = color
        run.font.name = "Calibri"
    return h


def add_para(doc, text, bold=False, italic=False, size=Pt(11), color=None, space_after=Pt(6)):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = size
    run.font.name = "Calibri"
    if color:
        run.font.color.rgb = color
    p.paragraph_format.space_after = space_after
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.25 + level * 0.25)
    p.paragraph_format.space_after = Pt(2)
    for run in p.runs:
        run.font.size = Pt(10)
        run.font.name = "Calibri"
    return p


def add_prompt_block(doc, prompt_text):
    """Add a prompt as a shaded code block with monospace font."""
    for line in prompt_text.strip().split("\n"):
        p = doc.add_paragraph()
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{PROMPT_BG}"/>')
        p._p.get_or_add_pPr().append(shading)
        run = p.add_run(line)
        run.font.size = Pt(9)
        run.font.name = "Consolas"
        run.font.color.rgb = C_CODE
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
    # Add a spacer after the block
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def _tight_page_break(doc):
    last_p = doc.paragraphs[-1]
    last_p.add_run().add_break(WD_BREAK.PAGE)


def build_header(doc):
    """Add header with logo and org name."""
    section = doc.sections[0]
    header = section.header
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()

    if LOGO_ORCHARD.exists():
        run = hp.add_run()
        run.add_picture(str(LOGO_ORCHARD), width=Inches(0.35))

    text_width = section.page_width - section.left_margin - section.right_margin
    hp.paragraph_format.tab_stops.add_tab_stop(text_width, WD_TAB_ALIGNMENT.RIGHT)
    hp.add_run("\t")
    run = hp.add_run("Argos \u2014 The Orchard")
    run.font.size = Pt(8)
    run.font.name = "Calibri"
    run.italic = True
    run.font.color.rgb = C_GRAY


def build_footer(doc):
    """Add page numbers in footer."""
    section = doc.sections[0]
    footer = section.footer
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.clear()
    run = fp.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    run._r.append(instr)
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_end)
    run.font.size = Pt(8)
    run.font.color.rgb = C_GRAY


def build_cover(doc):
    """Build cover page."""
    doc.add_paragraph()
    doc.add_paragraph()

    if LOGO_PEACOCK.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_picture(str(LOGO_PEACOCK), width=Inches(2.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("ARGOS")
    run.bold = True
    run.font.size = Pt(48)
    run.font.color.rgb = C_PRIMARY
    run.font.name = "Calibri"

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Gemini Presentation Instructions")
    run.font.size = Pt(22)
    run.font.name = "Calibri"
    run.font.color.rgb = C_H2

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Visual Speech Processing \u2014 Project Review")
    run.font.size = Pt(16)
    run.font.name = "Calibri"
    run.font.color.rgb = C_H3

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("The Orchard")
    run.font.size = Pt(20)
    run.font.name = "Calibri"
    run.font.color.rgb = C_PRIMARY

    doc.add_paragraph()

    for label, value in [
        ("Author: ", "Yoad Oxman"),
        ("Target Tool: ", "Google Gemini (Slides Generation)"),
        ("Slides: ", "30 slides + appendix"),
        ("Audience: ", "Technical managers and supervisors"),
        ("Last Updated: ", LAST_UPDATED),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(label)
        run.bold = True
        run.font.size = Pt(11)
        run.font.name = "Calibri"
        run = p.add_run(value)
        run.font.size = Pt(11)
        run.font.name = "Calibri"
        p.paragraph_format.space_after = Pt(2)

    _tight_page_break(doc)


def build_toc(doc):
    """Build Table of Contents."""
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()
    add_heading(doc, "Table of Contents", 1)

    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-2" \\h \\z \\u '
    run._r.append(instr)
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_sep)

    toc_entries = [
        "1. How to Use This Document",
        "2. Presentation Overview",
        "3. Prompt 1: Opening & Context (Slides 1-4)",
        "4. Prompt 2: Research Findings (Slides 5-16)",
        "5. Prompt 3: Engineering (Slides 17-23)",
        "6. Prompt 4: Future & Close (Slides 24-30)",
        "7. Appendix Slides",
        "8. Material References",
    ]
    for title in toc_entries:
        placeholder = paragraph.add_run(title + "\n")
        placeholder.font.size = Pt(11)
        placeholder.font.name = "Calibri"

    fld_end_run = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    fld_end_run._r.append(fld_end)

    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)

    _tight_page_break(doc)


# ═══════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════

PROMPT_1 = """Create a professional presentation with a dark modern theme
(deep navy background, white text, teal and coral accents).

This is PART 1 of 4 for an internal project review called
"Argos VSP: Research Findings and Production Roadmap"
about a Visual Speech Processing (lip reading) system.
Audience: Technical managers and supervisors.

Create exactly 4 slides:

SLIDE 1 - Title Slide
Title: "Argos VSP: Research Findings and Production Roadmap"
Subtitle: "Visual Speech Processing \u2014 Project Review"
Date: February 2026
Clean, minimal. Leave space for a logo in the top-right.

SLIDE 2 - Quick Context
Title: "What is Visual Speech Processing?"
A system that reads lips from video \u2014 no audio.
Three use cases: Surveillance | Accessibility | Noisy Environments
Note: "Opening demo: 33-word perfect lip-reading" [video played externally]

SLIDE 3 - Model Architecture
Title: "How It Works: Three Components"
Left-to-right flow: Video \u2192 AV-HuBERT (Visual Encoder) \u2192 LLaMA-2 (Language Model) \u2192 Text
One line under each: "Visual features" \u2192 "Token-to-text"

SLIDE 4 - The Benchmark
Title: "Paper Claims 25.4% WER on LRS3"
Large "25.4%" displayed.
Text: "Curated TED talks, controlled conditions."
Below: "Two questions: How does this hold on real-world video?
And is WER even the right way to measure?"
Leave space for a chart."""

PROMPT_2 = """Continue the same presentation (dark navy, teal/coral accents).
Audience: Technical managers. Full depth OK.

This is PART 2 of 4: Research Findings. Create exactly 12 slides:

SLIDE 5 - The Reality Gap
Title: "Real-World: 64.1% WER \u2014 2.5x Worse"
Large: "64.1% mean WER across 1,497 segments"
WER-based quality tiers:
- 11.4% Usable (<30%) \u2014 green
- 17.4% Marginal (30-50%) \u2014 yellow
- 17.8% Poor (50-75%) \u2014 orange
- 32.8% Unusable (75-100%) \u2014 red
- 20.6% Hallucinated (>100%) \u2014 dark red
Bottom: "But WER overstates failure \u2014 see next slide."
Leave space for chart.

SLIDE 6 - WER Is Blind (30-second slide)
Title: "Same WER, Opposite Meaning"
Two boxes side by side:
GREEN box \u2014 "WER 29%, IS 4.3 \u2014 Fully Intelligible":
Ref: "allow you to work with the team in a more"
Hyp: "allow you to work with a team and more"
RED box \u2014 "WER 33%, IS 3.0 \u2014 Unintelligible":
Ref: "today i'm talking with admiral mcrae"
Hyp: "today i'm talking with animal migratory"
Bottom: "WER says equal. Meaning says opposite. So we built a
metric to capture this."

SLIDE 7 - The Intelligibility Score
Title: "Intelligibility Score: 39.9% Properly Captured"
Show 6 signal blocks:
Semantic Similarity (25%) + Phonetic Similarity (15%) +
Inverse WER (15%) + Inverse WWER (15%) +
Named Entity Accuracy (15%) + Length Ratio (15%)
KEY: "IS >= 3.0 = Properly Captured: 39.9% \u2014 3.5x more than WER's 11.4%"
Tiers: 18.4% Excellent | 21.4% Good | 21.7% Fair | 22.4% Poor | 16.0% Failed

Correlation validation (adds credibility):
- 6 signals collapse into 3 independent dimensions:
  (1) Word accuracy (~60% of IS variance: WER, WWER, Phonetic, all r>0.80)
  (2) Meaning preservation (~28%: Semantic)
  (3) Output sanity (~9%: Length Ratio)
- Phonetic Similarity has highest single-signal correlation (r=0.943)
- Semantic dominates variance contribution (28.5%) due to higher weight
- NEA F1 contributes disproportionately (17.3% vs its 15% weight)
- LLM-knowledge-based judge validates IS: r=0.93 correlation,
  88.6% agreement with IS >= 3.0 threshold, 99.2% recall

Success patterns (what makes segments succeed):
- Phonetically Preserved: 41.5% of successes (#1 driver)
- Minor Errors + High Semantic: 24.5%
- Entities Preserved: 12.4%
- Near-Perfect Output: 11.6%
Context recovery: 43.6% rule-based, 50.6% LLM-judged
This is the main methodological contribution.

SLIDE 8 - Failure Mode Taxonomy
Title: "10 Classified Failure Modes (900 failed segments)"
Horizontal bar chart data (sorted by frequency):
- Total Topic Drift: 15.9% (143) \u2014 no connection to reference
- Phonetically Similar but Wrong Topic: 15.7% (141)
- Accumulated Small Errors: 12.3% (111) \u2014 death by 1000 cuts
- Hallucination: 12.3% (111) \u2014 fluent fabrication
- High Error Rate: 12.1% (109)
- Entity Destruction: 12.0% (108) \u2014 names/numbers lost
- Content Word Errors: 10.7% (96) \u2014 structure OK, key words wrong
- Empty Output: 7.8% (70) \u2014 model produced nothing
- Truncation: 1.1% (10)
- Over-generation: 0.1% (1)
Bottom: "Failures are diverse \u2014 no single fix addresses all modes.
Each roadmap phase targets specific failure categories."
Color-code: red for hallucination/topic drift, orange for errors,
yellow for partial failures, gray for empty/truncation.

SLIDE 9 - Performance Distribution
Title: "Distribution Across 13 Experiments"
Text: Most segments 50-80% WER. Long tail of failures.
Stable core of ~11% always-good segments across all configs.
Leave space for boxplot.

SLIDE 10 - Why the Gap: Root Causes + Topic/Length Analysis
Title: "Three Root Causes \u2014 With Data"
Three columns:
1. Domain Mismatch \u2014 Business/Finance best (IS 3.08, 57% captured,
   formal vocabulary). DIY/Home worst (IS 2.13, 30% captured,
   casual/technical speech). Entertainment 30% captured.
2. Short Segments \u2014 5-10 words: only 32% captured, 74% WER.
   20+ words: 49% captured, 55% WER. Gap: +17pp captured.
   Short segments lack enough visual context for the model.
3. Hallucination \u2014 LLM prior overwhelms weak visual signal.
   12.3% of failures are pure hallucination, 15.9% total topic drift.
Leave space for scatter plot.

SLIDE 11 - Named Entity Accuracy
Title: "NEA F1: 38.8% \u2014 The Largest Success/Failure Differentiator"
Text: Names, numbers, proper nouns \u2014 exactly what context
cannot recover. You can guess a missing "the" but not "McRae."
Signal comparison (success vs failure):
- NEA F1: 74.0% vs 15.7% (gap: 58.3pp \u2014 LARGEST)
- Semantic: 0.74 vs 0.24 (gap: 0.50)
- Phonetic: 0.81 vs 0.38 (gap: 0.43)
- WER: 30% vs 87%
Correlation insight: NEA F1 contributes 17.3% of IS variance \u2014
disproportionately more than its 15% weight, because entity
accuracy has the highest variance among signals (some segments
nail all names, others miss every one).
Leave space for chart.

SLIDE 12 - 13 Tuning Experiments
Title: "Systematic Parameter Search: 13 Configurations"
Two columns:
Left \u2014 Parameters tested: beam size, length penalty (-0.5 to 2.0),
temperature (0.3 to 1.5), sampling strategy, repetition penalty
Right \u2014 Full-dataset Config J results (1,497 segments):
- IS: 2.60 vs 2.52 baseline (+0.08)
- Captured (IS >= 3): 622 vs 597 (+25 segments)
- Empties: 0 vs 70 baseline (eliminated)
- Hallucinations: 348 vs 307 (+41 more)
- NEA F1: 43.4% vs 38.9% (+3.7pp)
- J beats C: stochastic sampling finds more entities
Note: do_sample=True on standalone (stochastic), False on EC2
(deterministic) \u2014 to be unified.
Leave space for charts.

SLIDE 13 - Limits of Tuning
Title: "Tuning Is Mitigation, Not a Cure"
Text: Config J trade-off: eliminates empties but doubles
hallucinations (111 \u2192 262). Net IS gain only +0.08.
The fundamental tradeoff: silent failures (empties) vs
noisy failures (hallucinations).
Long segments benefit most: 20+ words gain +0.25 IS.
Short segments marginally worse due to over-generation.
Cannot fix domain mismatch with hyperparameters.
Leave space for chart.

SLIDE 14 - Curated Examples with IS
Title: "Representative Examples"
Table with IS scores:
| Category | Reference | Hypothesis | WER | IS |
| Perfect | "health insurance company they pay..." | [match] | 0% | 5.0 |
| WER misleads | "work with the team" | "work with a team" | 29% | 4.3 |
| Entity destroyed | "admiral mcrae" | "animal migratory" | 33% | 3.0 |
| Hallucinated | "carry strap" | "holocaust denier" | 100% | 0.7 |
Color IS column green\u2192red.

SLIDE 15 - Live Demo
Title: "Demo: Three Videos"
Subtitle: "Perfect \u2192 Near-miss \u2192 Hallucination"
Minimal. [Videos played externally]

SLIDE 16 - Research Output
Title: "Seven Research Reports + Exp A Training Analysis"
List:
1. Executive Assessment \u2014 reality gap, quality tiers
2. Hyperparameter Tuning \u2014 13 experiments, parameter sensitivity
3. Prompt Engineering \u2014 context injection strategies
4. Confidence Scoring \u2014 beam score extraction, quality filtering
5. N-Best Aggregation \u2014 ROVER/MBR hypothesis combination
6. Fine-Tuning Analysis \u2014 LoRA domain adaptation strategy
7. Intelligibility Scoring \u2014 6-signal composite metric,
   failure mode taxonomy, success patterns, topic/length analysis
NEW: Exp A Training Report \u2014 r=16 results, overfitting analysis,
   10 diagnostic plots, recommendations for Exp B"""

PROMPT_3 = """Continue the same presentation (dark navy, teal/coral accents).
Audience: Technical managers.

This is PART 3 of 4: Engineering Achievements. Create exactly 7 slides:

SLIDE 17 - Pipeline Architecture
Title: "8-Stage Automated Pipeline"
Subtitle: "3 research repos \u2192 single orchestrated system"
Leave mostly empty \u2014 I will insert a pipeline diagram.

SLIDE 18 - Engineering Challenges
Title: "37 Bugs Fixed: Research Code \u2192 Production"
Two columns:
Left: HDR tone-mapping, NVENC silent corruption (destroyed 43% of
videos), Cython compilation, fairseq patching, spaCy offline,
Docker networking, Python venv conflicts
Right: Handles any format (MP4/MKV/AVI/MOV), any resolution,
any codec. GPU detection with CPU fallback. All 37 bugs
documented with root cause analysis.

SLIDE 19 - Modular Refactoring
Title: "52% Code Reduction: 823 \u2192 393 Lines"
Before/after:
BEFORE: Monolithic 823-line script. Fragile.
AFTER: 393-line orchestrator + 11 modules in lib/.
37 automated tests. Each stage independently testable.
Environment-aware (auto-detects EC2 vs container).

SLIDE 20 - Deployed Product
Title: "Standalone Container \u2014 No Cloud"
- Docker container with web UI on Linux machine
- Drag-and-drop video upload
- Automatic end-to-end processing
- INSTALL.sh overlay with backup and verification
- Currently deployed at client site

SLIDE 21 - Intelligent Features
Title: "Pipeline Intelligence"
Three cards:
1. Transcription Reuse \u2014 manual corrections persist,
   Whisper skips matched segments (saves hours)
2. Golden K-means \u2014 1,396-video baseline model
3. Smart Segmentation \u2014 configurable overlap for context

SLIDE 22 - Evaluation Infrastructure
Title: "Evaluation: Beyond Standard WER"
Seven items:
- 16 analytical plots auto-generated per experiment
- Per-segment HTML reports (interactive, 13 experiments)
- Custom NEA metric for operational entity accuracy
- Intelligibility Score pipeline: 6-signal composite,
  per-segment automated scoring, tier classification
- Automated failure mode classification (10 modes) and
  success pattern analysis (7 patterns)
- Topic and segment length analysis across 11 categories
- Full CSV exports (1,497 rows, all metrics + IS signals)
- NEW: Fine-tuning diagnostics \u2014 10 training plots
  (loss/accuracy curves, overfitting gap, LR schedule,
  gradient norms, perplexity, wall-clock, summary dashboard)

SLIDE 23 - Process & Documentation
Title: "Engineering Process"
- 40+ git versions with semantic tags
- EC2/container sync protocol (26 tracked items)
- 7 formal research reports + methodology docs
- Complete architecture, development, and bug documentation"""

PROMPT_4 = """Continue the same presentation (dark navy, teal/coral accents).
Audience: Technical managers. Frame roadmap as research agenda
and resource needs, not sales pitch.

This is PART 4 of 4: Future Directions. Create exactly 7 slides:

SLIDE 24 - Reframing the Starting Point
Title: "Starting from 40%, Not 11%"
Two columns:
LEFT (red): "WER Says" \u2014 11.4% usable, 9/10 fail
RIGHT (green): "IS Says" \u2014 39.9% properly captured,
43-51% context-recoverable
Validation: IS independently validated \u2014 LLM-knowledge-based
judge (heuristic, no API costs) agrees 88.6% with IS >= 3.0
threshold (r=0.93 correlation, 99.2% recall). The metric works.
Success pattern insight: 41.5% of successes are phonetically
preserved \u2014 the visual signal captures speech structure even
when specific words are wrong. Phonetic similarity is the #1
correlate with IS (r=0.943).
Bottom: "The gap is real but WER dramatically overstates failure.
40% already works, and we know WHY it works \u2014 phonetic
preservation is the #1 success driver."
Make this feel like a turning point in the narrative.

SLIDE 25 - Research Roadmap
Title: "Three Phases \u2014 Each Targeting Specific Failure Modes"
Timeline/staircase with failure mode annotations:
Phase 1: Surface the good 40% \u2014 confidence scoring.
  Targets: all failure modes (flag quality, not fix it).
Phase 2: Improve the fair 22% \u2014 N-best aggregation.
  Targets: Accumulated Small Errors (12.3%), Content Word
  Errors (10.7%) \u2014 partial correct words exist across hypotheses.
Phase 3: Rescue the poor 22% \u2014 domain fine-tuning.
  Targets: Topic Drift (15.9%), Phonetically Similar but Wrong
  Topic (15.7%), Entity Destruction (12.0%) \u2014 domain mismatch.
Leave space for trajectory chart.

SLIDE 26 - Phase 1: Confidence Scoring
Title: "Phase 1: Automatic Quality Flagging"
- IS proves 40% is good; beam scores can flag it at decode time
- No additional inference needed \u2014 scores already computed
- Effort: 2-4 hours implementation
- Output: every segment gets a confidence label
- Priority: Business/Finance segments (57% captured) are most
  likely reliable. Short segments (<10 words, 32%) need lower
  confidence thresholds.
- This is the immediate next step

SLIDE 27 - Phase 2: N-Best Aggregation
Title: "Phase 2: Exploit All 20 Hypotheses"
- Currently discarding 19 of 20 beam candidates
- ROVER/MBR \u2014 established technique, consistent gains
- Expected: 5-15% relative improvement
- Targets: Accumulated Small Errors (12.3% of failures) and
  Content Word Errors (10.7%) \u2014 these have partial correct
  words scattered across multiple hypotheses
- Moves "fair" tier up to "good"

SLIDE 28 - Phase 3: Fine-Tuning \u2014 Exp A Results
Title: "Phase 3: Domain Adaptation \u2014 First Results"
Two sections:

TOP \u2014 Exp A Results (r=16, encoder frozen):
- Dataset: only ~1,400 YouTube videos \u2192 1,273 train / 224 val segments
  (stratified by IS tier). This is a SMALL dataset \u2014 proof of concept.
- LoRA r=16, alpha=32, targets: q/k/v_proj \u2014 12.6M params (0.19%)
- Best val accuracy: 62.94% at epoch 2 (320 updates)
- Severe overfitting: train acc 95.5% vs val acc 59.0% by epoch 19
  (36.5 pp gap \u2014 model memorized training data)
- Training: 17 hours on Tesla T4 (FP16)
- Key insight: best checkpoint at epoch 2 \u2014 17 of 19 epochs wasted
- Decode evaluation pending (checkpoint_best.pt ready)
Leave space for FT_10 summary dashboard plot.

BOTTOM \u2014 What We Learned + Exp B Plan:
- Early stopping is critical (save every epoch, stop at first decline)
- r=16 is rank-limited for TED\u2192YouTube domain shift
- Exp B: r=64 (4x capacity), max 500 updates, validate every 50 steps
- Encoder unfreezing (requires larger GPU): expected 15-25 WER point gain
- More training data: current ~1,400 videos is small \u2014 AVSpeech has
  millions of clips available. Scaling data is a key lever.
- Targets: Topic Drift (15.9%), Phonetically Similar but Wrong
  Topic (15.7%), Entity Destruction (12.0%) \u2014 domain mismatch failures
- This remains the single largest opportunity

SLIDE 29 - Beyond Phase 3
Title: "Future Capabilities"
Grid:
1. Arabic \u2014 K-means model exists, pipeline integration needed
2. Multi-speaker \u2014 speaker tracking and separation
3. Streaming \u2014 real-time processing
4. Topic-specific tuning \u2014 target lowest categories
   (DIY/Home 30%, Entertainment 30%) with domain data

SLIDE 30 - Summary
Title: "Key Takeaways"
Four points:
1. Rigorous assessment: 2.5x WER gap on 1,497 segments.
   Novel IS metric reveals 40% properly captured. 10 classified
   failure modes. Performance analyzed by topic and segment length.
2. Production system delivered: standalone container, 37 bugs fixed,
   8-stage pipeline, 37 tests, 7 research reports.
3. First fine-tuning complete: Exp A (r=16) trained on only 1,273
   segments from ~1,400 YouTube videos \u2014 best val accuracy 62.9%
   at epoch 2, confirmed overfitting dynamics. Small dataset proves
   model CAN learn from YouTube data. Decode evaluation pending.
4. Clear next steps: confidence scoring (hours), N-best (days),
   Exp B fine-tuning (r=64, early stopping). More training data
   (current ~1,400 videos is small) and encoder unfreezing
   (requires larger GPU) are the key scaling levers."""


# ═══════════════════════════════════════════════════
# DOCUMENT SECTIONS
# ═══════════════════════════════════════════════════

def build_intro(doc):
    """Section 1: How to Use This Document."""
    add_heading(doc, "1. How to Use This Document", 1)

    add_para(doc, (
        "This document contains 4 sequential prompts for Google Gemini "
        "to generate the Argos VSP project review presentation (30 slides). "
        "Feed each prompt one at a time, in order. Gemini will build up the "
        "presentation incrementally across the 4 prompts."
    ))

    add_heading(doc, "Instructions", 2)
    add_bullet(doc, 'Open Google Gemini and start a new conversation')
    add_bullet(doc, 'Copy and paste Prompt 1 (Opening & Context) \u2014 generates slides 1-4')
    add_bullet(doc, 'Wait for Gemini to finish, then paste Prompt 2 (Research Findings) \u2014 slides 5-16')
    add_bullet(doc, 'Paste Prompt 3 (Engineering) \u2014 slides 17-23')
    add_bullet(doc, 'Paste Prompt 4 (Future & Close) \u2014 slides 24-30')
    add_bullet(doc, 'After all 4 prompts: manually add appendix slides and insert plots/diagrams')

    add_heading(doc, "Design Theme", 2)
    add_para(doc, (
        "All prompts specify the same visual theme: dark navy background, "
        "white text, teal and coral accents. This creates a cohesive, "
        "professional look across all 30 slides."
    ))

    add_heading(doc, "Post-Generation Steps", 2)
    add_bullet(doc, 'Insert plots from 01_plots_for_slides/ at marked locations')
    add_bullet(doc, 'Insert pipeline diagram from 09_pipeline_diagram/')
    add_bullet(doc, 'Add logo from 08_branding/ to title slide and headers')
    add_bullet(doc, 'Add fine-tuning plots from 01_plots_for_slides/finetune/ to Slide 28')
    add_bullet(doc, 'Add appendix slides manually (see Section 7)')
    add_bullet(doc, 'Play demo videos from 06_demo_videos/ externally during presentation')

    _tight_page_break(doc)


def build_overview(doc):
    """Section 2: Presentation Overview."""
    add_heading(doc, "2. Presentation Overview", 1)

    add_styled_table(doc,
        ["Section", "Prompt", "Slides", "Duration", "Content"],
        [
            ["Opening & Context", "Prompt 1", "1-4", "~5 min", "Title, what is VSP, architecture, benchmark"],
            ["Research Findings", "Prompt 2", "5-16", "~20 min", "Reality gap, IS metric, failure modes, tuning, examples, demo"],
            ["Engineering", "Prompt 3", "17-23", "~10 min", "Pipeline, bugs, refactoring, deployment, evaluation"],
            ["Future & Close", "Prompt 4", "24-30", "~15 min", "Reframing, roadmap, Exp A results, next steps"],
        ],
        col_widths=[1.3, 0.8, 0.7, 0.8, 3.0],
    )

    add_heading(doc, "Key Numbers", 2)
    add_styled_table(doc,
        ["Metric", "Value", "Source"],
        [
            ["Paper WER (LRS3)", "25.4%", "VSP-LLM paper, Table 1"],
            ["Real-world mean WER", "64.1%", "Report 1, 1,497 segments"],
            ["Reality gap", "2.5x worse", "Report 1"],
            ["Properly captured (IS \u2265 3.0)", "39.9% (597 segments)", "Intelligibility Score"],
            ["WER overstatement factor", "3.5x", "39.9% vs 11.4%"],
            ["Failure modes classified", "10 modes", "900 failed segments"],
            ["#1 failure: Topic Drift", "15.9% (143 segments)", "Failure taxonomy"],
            ["#1 success: Phonetic Preservation", "41.5%", "248 of 597 successes"],
            ["Bugs fixed", "37", "Bug tracking docs"],
            ["Pipeline: lines before \u2192 after", "823 \u2192 393", "52% reduction"],
            ["Total experiments", "13 (A-M)", "Tuning dataset"],
            ["Exp A: training data", "~1,400 videos \u2192 1,273 train / 224 val", "AVSpeech YouTube"],
            ["Exp A: best val accuracy", "62.94% at epoch 2", "r=16, 320 updates"],
            ["Exp A: overfitting gap", "36.5 pp (train 95.5% vs val 59.0%)", "Epoch 19"],
            ["Exp A: training time", "17.0 hours", "Tesla T4, FP16"],
            ["Exp A: trainable params", "12.6M (0.19%)", "LoRA r=16, alpha=32"],
            ["IS: top correlate", "Phonetic Sim r=0.943", "Correlation analysis"],
            ["IS: 3 dimensions", "Word acc 60%, Meaning 28%, Sanity 9%", "Variance decomposition"],
            ["IS: LLM judge agreement", "88.6% (r=0.93, recall 99.2%)", "llm_context_prob validation"],
            ["IS: NEA variance share", "17.3% (vs 15% weight)", "Disproportionate contributor"],
        ],
        col_widths=[2.5, 2.2, 2.0],
    )

    _tight_page_break(doc)


def build_prompt_section(doc, number, title, slides, prompt_text):
    """Build a prompt section with description and copyable prompt block."""
    add_heading(doc, f"{number + 2}. Prompt {number}: {title} ({slides})", 1)

    add_para(doc, f"Copy the entire text block below and paste it into Google Gemini.",
             italic=True, color=C_GRAY)
    add_para(doc, f"This prompt generates {slides}.", bold=True)

    doc.add_paragraph()
    add_prompt_block(doc, prompt_text)
    _tight_page_break(doc)


def build_appendix(doc):
    """Section 7: Appendix Slides."""
    add_heading(doc, "7. Appendix Slides", 1)

    add_para(doc, (
        "These slides are NOT generated by the Gemini prompts. "
        "Add them manually to the end of the deck as needed during Q&A."
    ))

    add_styled_table(doc,
        ["#", "Slide", "When to Use"],
        [
            ["A1", "Homophenes table", "If someone asks about visual confusion patterns"],
            ["A2", "Exp A Fine-Tuning Deep Dive \u2014 6-panel summary dashboard "
                   "(FT_10), loss/accuracy curves (FT_01/02), overfitting gap (FT_03). "
                   "Key: trained on only ~1,400 YouTube videos (1,273 train segments), "
                   "17h on Tesla T4, best at epoch 2/19",
                   "If asked for training details or overfitting analysis"],
            ["A3", "Catastrophic lenpen=2.0 (WER 171%)", "If asked about parameter space boundaries"],
            ["A4", "CDF WWER chart", "If asked about quality thresholds"],
            ["A5", "Topic analysis detail (11 categories)", "If asked about domain-specific performance"],
            ["A6", "Signal comparison table (success vs failure)", "If asked about what makes IS work"],
            ["A7", "Config J full-dataset comparison", "If asked about tuning details on full data"],
        ],
        col_widths=[0.4, 3.0, 3.2],
    )

    _tight_page_break(doc)


def build_materials(doc):
    """Section 8: Material References."""
    add_heading(doc, "8. Material References", 1)

    add_para(doc, "All materials referenced in the prompts are in the presentation_materials_20260224/ folder:")

    add_styled_table(doc,
        ["Folder", "Contents", "Used In"],
        [
            ["01_plots_for_slides/", "17 presentation graphs (P1-P5, existing, finetune/)", "Slides 4-13, 25, 28"],
            ["01_plots_for_slides/finetune/", "4 key fine-tuning plots (FT_01, FT_02, FT_03, FT_10)", "Slide 28, Appendix A2"],
            ["02_plots_boss_deep_dive/", "14 technical deep-dive graphs (all 10 FT_* plots)", "Appendix, Q&A backup"],
            ["03_reports_md/", "9 research reports in Markdown (incl. correlation analysis)", "Slides 7, 11, 16, 24"],
            ["04_reports_docx/", "18 formatted reports (Word + PDF)", "Handouts"],
            ["05_data/", "18+ data files (CSV, JSON, HTML reports)", "Reference data"],
            ["06_demo_videos/", "8 burned videos with subtitle overlays", "Slides 2, 14, 15"],
            ["07_paper/", "VSP-LLM paper + 2025 presentation", "Slide 3-4 reference"],
            ["08_branding/", "3 logo files", "Title slide, headers"],
            ["09_pipeline_diagram/", "8-stage pipeline flow diagram", "Slide 17"],
            ["10_examples/", "Curated example data", "Slide 14 content"],
        ],
        col_widths=[1.8, 2.8, 2.0],
    )


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

def main():
    doc = Document()

    # Page setup
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)

    # Build document
    build_header(doc)
    build_footer(doc)
    build_cover(doc)
    build_toc(doc)
    build_intro(doc)
    build_overview(doc)

    # 4 Gemini prompts
    prompts = [
        (1, "Opening & Context", "Slides 1-4", PROMPT_1),
        (2, "Research Findings", "Slides 5-16", PROMPT_2),
        (3, "Engineering", "Slides 17-23", PROMPT_3),
        (4, "Future & Close", "Slides 24-30", PROMPT_4),
    ]
    for num, title, slides, text in prompts:
        build_prompt_section(doc, num, title, slides, text)

    build_appendix(doc)
    build_materials(doc)

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_FILE))
    print(f"Generated: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
