# Argos Document Generator Style Guide

Standard formatting rules for all document and presentation generators.

---

## Table of Contents

1. [Word/Docx Conventions](#worddocx-conventions)
2. [PPTX Conventions](#pptx-conventions)
3. [Plot Styling](#plot-styling)
4. [Pipeline Diagram](#pipeline-diagram)
5. [Beamer (LaTeX) Theme](#beamer-latex-theme)
6. [Spider/Radar Chart Conventions](#spiderradar-chart-conventions)
7. [Visual Quality Guardrails](#visual-quality-guardrails)
8. [Cross-Format Rules](#cross-format-rules)

---

# Word/Docx Conventions

## Header

- Logo (logo.png) on the **left** margin
- "Argos — The Orchard" on the **right** margin via tab stop
- 8pt Calibri, gray italic
- No "INTERNAL" or classification labels
- Use `WD_TAB_ALIGNMENT.RIGHT` tab stop at `page_width - left_margin - right_margin`

```python
text_width = section.page_width - section.left_margin - section.right_margin
hp.paragraph_format.tab_stops.add_tab_stop(text_width, WD_TAB_ALIGNMENT.RIGHT)
hp.add_run("\t")
run = hp.add_run("Argos \u2014 The Orchard")
```

## Cover Page

1. Two spacer paragraphs at top
2. Peacock logo centered, 2.0-2.5 inches — use `doc.add_picture()` (not `run.add_picture()`)
3. "ARGOS" title, 48pt bold, primary color
4. Document subtitle, 22pt
5. "The Orchard", 20pt
6. Author: "Yoad Oxman", 14pt, centered
7. Metadata key-value pairs (centered)
8. Page break

## Table of Contents

Use a **standard Word TOC field** (not manual hyperlinks):

```python
paragraph = doc.add_paragraph()
run = paragraph.add_run()
# begin field
fld_begin = OxmlElement('w:fldChar')
fld_begin.set(qn('w:fldCharType'), 'begin')
run._r.append(fld_begin)
instr = OxmlElement('w:instrText')
instr.set(qn('xml:space'), 'preserve')
instr.text = ' TOC \\o "1-2" \\h \\z \\u '
run._r.append(instr)
# separate
fld_sep = OxmlElement('w:fldChar')
fld_sep.set(qn('w:fldCharType'), 'separate')
run._r.append(fld_sep)
# placeholder entries (shown until Word updates the field)
for title in toc_titles:
    placeholder = paragraph.add_run(title + "\n")
# end field
fld_end_run = paragraph.add_run()
fld_end = OxmlElement('w:fldChar')
fld_end.set(qn('w:fldCharType'), 'end')
fld_end_run._r.append(fld_end)
```

Set `updateFields` so Word auto-populates on open:

```python
settings = doc.settings.element
update_fields = OxmlElement('w:updateFields')
update_fields.set(qn('w:val'), 'true')
settings.append(update_fields)
```

Push the TOC heading down slightly from the top of the page (3 zero-height spacer paragraphs).

## Page Breaks After Tables

When a table is the last element before a page break, use a tight break to avoid a visible blank gap:

```python
def _tight_page_break(doc):
    last_p = doc.paragraphs[-1]
    last_p.add_run().add_break(WD_BREAK.PAGE)
```

This adds the break to the table's trailing paragraph instead of creating a new empty one.

## Logo Paths

Logos live in `docs/_research-tools/assets/`:
- `logo.png` — header (orchard tree)
- `peacock.png` — cover page

Reference via: `ASSETS_DIR = SCRIPT_DIR.parent / "assets"`

## General Docx Rules

- Font: Calibri throughout
- No "INTERNAL" or "Classification" labels anywhere
- Author "Yoad Oxman" on every cover page
- A4 page size (21.0 x 29.7 cm), 2.5 cm side margins, 2.0 cm top/bottom
- Page numbers in footer (centered, 8pt gray)

---

# PPTX Conventions

**Generator**: `generate_presentation.py` (~5,500 lines, ~47 slides)
**Output**: `presentation_materials_20260224/Argos_VSP_Project_Review.pptx`
**Dependency**: `python-pptx`

## PPTX Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| BG | `#0D1B2A` | Deep navy background (all slides) |
| TEAL | `#00B4D8` | Accent color, preprocessing stages, accent lines |
| CORAL | `#E06C75` | Emphasis, output stages, failure highlights |
| GREEN | `#4CAF50` | Success, positive metrics |
| GOLD | `#FFD54F` | LLM inference, attention items |
| WHITE | `#FFFFFF` | Primary text |
| LGRAY | `#AAAAAA` | Light gray — secondary text, slide numbers |
| MGRAY | `#666666` | Medium gray — borders, dividers |
| NAVY2 | `#152A40` | Slightly lighter navy — card backgrounds |
| NAVY3 | `#1A3550` | Even lighter — hover/active states |
| RED | `#F44336` | Negative metrics, failed tier |
| DRED | `#B71C1C` | Dark red — severe failures |
| YELLOW | `#FFC107` | Warnings |
| ORANGE | `#FF9800` | Additional emphasis |

## PPTX Layout Constants

```python
SL_W = Inches(13.333)    # 16:9 widescreen width
SL_H = Inches(7.5)       # 16:9 height
MX   = Inches(0.6)       # Horizontal margin
MY   = Inches(0.4)       # Top margin
CT   = Inches(1.45)      # Content top (below title + accent line)
CW   = Inches(12.13)     # Content width (SL_W - 2*MX)
CH   = Inches(5.55)      # Content height
```

## PPTX Typography

- **Font**: Calibri throughout (matches docx)
- **Slide title**: 32pt bold white
- **Body text**: 16pt white
- **Bullet text**: 15pt white
- **Small text**: 9pt LGRAY (slide numbers, footnotes)
- **Speaker notes**: plain text (not shown on slides)

## PPTX Helper Functions

| Function | Purpose |
|----------|---------|
| `new_slide()` | Create blank slide with navy BG |
| `add_title(slide, text)` | Add 32pt title at top |
| `add_accent_line(slide)` | Teal horizontal rule below title |
| `add_text(slide, text, ...)` | Add text box with positioning |
| `add_bullets(slide, items, ...)` | Add bullet list |
| `add_rich_text(slide, runs, ...)` | Mixed formatting with per-run control |
| `add_image(slide, path, ...)` | Add image with positioning |
| `add_rect(slide, ...)` | Add colored rectangle (cards, backgrounds) |
| `add_logo(slide)` | Add branding logo |
| `add_slide_num(slide, n)` | Add slide number (bottom-right) |
| `set_notes(slide, text)` | Add speaker notes |
| `_fmt(paragraph, ...)` | Paragraph-level formatting utility |

## PPTX Animation Rules

The `add_animations()` function in `helpers.py` creates click-to-advance OOXML entrance animations. The `_finish()` wrapper calls it.

**Critical rules:**

1. **`para_build` must default to `False`** — Only set `True` explicitly when per-paragraph bullet builds are desired. When `True`, multi-paragraph shapes in entry groups get hidden instead of visible on entry.

2. **Card animations must include ALL child shapes** — When creating card layouts (rect + text overlays), collect every shape into the same `anim_groups` entry:
   ```python
   card_shapes = []
   card_shapes.append(add_rect(...))      # background
   card_shapes.append(add_text(...))      # title
   card_shapes.append(add_text(...))      # body
   anim_groups.append(card_shapes)
   ```
   Never put only the rectangle in `anim_groups` — text will float independently.

3. **Animation group order = click order** — With `click_reveal=True`, group 0 is visible on entry, group 1 on first click, etc. Left-side content should generally be group 0.

4. **Table height must not overlap downstream content** — Verify: `table_y + (num_rows + 1) * row_height < next_element_y`. Common fix: reduce `row_height` and `text_size`.

5. **Plot text annotations need staggering** — Place IS values above the hi-range line, captured % below the mid-line, and mission labels below the lo-range line with extra spacing.

> See [Visual Quality Guardrails §7.6](#76-animation-structure-a1a5) for the complete animation checklist.

## PPTX Modular Architecture

**Generator**: `generate_presentation.py` is a slim orchestrator (~90 lines). All logic lives in the `presentation/` package:

| Module | Contents |
|--------|----------|
| `config.py` | Paths, colors, layout constants, IMG dictionary |
| `helpers.py` | Slide setup, text, shapes, animations, `_finish()`, `add_animations()` |
| `slides_opening.py` | Sections 0-2: Opening, Context, Problem |
| `slides_research.py` | Sections 3-5: Research Findings, Understanding, Tuning |
| `slides_evaluation.py` | Section 6 + Salvage + Demos |
| `slides_engineering.py` | Section 7: Engineering |
| `slides_future.py` | Section 8: Future Directions + Appendix |

## PPTX Slide Organization

Each slide is a `slide_*()` function taking `prs` (Presentation) as argument. Auto-numbering via `_auto_num[0]` counter. The `main()` function in the orchestrator defines the ordered builder list.

Images centralized in `IMG` dictionary in `config.py` mapping semantic keys to file paths.

---

# Plot Styling

**Generators**: `generate_presentation_plots.py` (P1-P6 + P3b), `generate_finetune_plots.py` (FT_01-FT_11)
**Output**: `docs/evaluation/plots/P*.png`, `docs/finetuning/plots/FT_*.png`

## Plot Defaults

- **DPI**: 200 (standard), 250 for radar charts
- **Figure size**: (10, 6) standard, (14, 6) for dual-panel, (16, 10) for dashboards
- **Style base**: seaborn + custom rcParams

## Plot Color Palette

Plots use **matplotlib defaults** for analytical charts, not the PPTX brand palette:

```python
# Standard analytical plots
blue    = "#1f77b4"   # Primary
orange  = "#ff7f0e"   # Secondary
green   = "#2ca02c"   # Success/positive
red     = "#d62728"   # Failure/negative
purple  = "#9467bd"   # Tertiary

# Fine-tuning specific
C_TRAIN = "#1f77b4"   # Training (blue)
C_VAL   = "#d62728"   # Validation (red)
C_BEST  = "#FFD700"   # Best checkpoint (gold star)
```

**Exception**: Dark-theme plots (P6 IS radar, FT_11 summary) use the PPTX brand palette for visual consistency when embedded in slides.

## Plot Visual Conventions

- Remove top and right spines: `ax.spines["top"].set_visible(False)`
- White bar edges: `edgecolor="white", linewidth=1.5`
- Insight annotation boxes: light yellow background, rounded corners
- Value labels: bold, 11pt, above/on bars
- Best checkpoint: gold star marker (`marker="*"`)
- Overfitting zones: red shading with `alpha=0.08`
- Font sizes: title 14-15pt, axes 12-13pt, labels 10-11pt

> See [Visual Quality Guardrails T5/T6](#73-text-readability-t1t7) for presentation-readability requirements.

---

# Pipeline Diagram

## Beamer: Image-Based (from generator)

**Generator**: `generate_pipeline_diagram.py` (254 lines)
**Output**: `docs/evaluation/plots/pipeline_architecture.png`

- 8 stages in 2 rows (4 per row), elbow connector between rows
- Input/output labels with additional context
- Component brackets below: `auto_avsr`, `av_hubert`, `VSP-LLM`

## PPTX: Programmatic Layout (slide 17)

PPTX slide 17 is fully programmatic (no external image). Built with `add_rect()` and `add_text()`:

- 2 rows × 4 boxes, each `2.65" × 1.6"` with `0.35"` gap
- Each box: stage number + name (18pt bold), subtitle (13pt), format label above (10pt)
- Input label (left of row 1), output label (right of row 2)
- Repo labels below rows: `auto_avsr`, `av_hubert`, `VSP-LLM`
- Legend bar at bottom with 4 color swatches
- Click-reveal: row 1 appears first, row 2 on click

## Pipeline Phase Color Mapping

| Phase | Color (matplotlib) | PPTX Hex | Stages |
|-------|-------------------|----------|--------|
| Preprocessing | Teal | `#4DD0E1` (light cyan) | 1-4 (normalize, ASR, crop, LRS3) |
| Feature Processing | Green | `#66BB6A` (soft green) | 5-6 (manifests, clustering) |
| LLM Inference | Gold | `#FFCA28` (gold) | 7 (VSP-LLM decode) |
| Output | Coral | `#EF9A9A` (soft pink) | 8 (reports, burned videos) |

Arrow/flow color (matplotlib only): `#6BAED6`

---

# Beamer (LaTeX) Theme

**Location**: `docs/paper/beamer-presentation/`
**Build**: `cd docs/paper/beamer-presentation && make`
**Theme**: Metropolis base with custom `beamer-argos-theme.sty`
**Font**: Fira Sans (Metropolis default)

## Custom Beamer Commands

| Command | Purpose |
|---------|---------|
| `\metricbox{num}{label}` | Single key number with label |
| `\alertmetric{num}{label}` | Red/warning metric box |
| `\successmetric{num}{label}` | Green/success metric box |
| `\comparisonbox{left}{right}` | Side-by-side green/red comparison |
| `\phasebox{num}{title}{desc}` | Roadmap phase box |
| `\twocol{w1}{left}{w2}{right}` | Two-column layout |
| `\fullwidthfig{file}{caption}` | Full-width figure |
| `\halfwidthfig{file}` | Half-width figure |
| `\videothumb{file}{caption}` | Video thumbnail (pdfpc control) |
| `\videocaptioned{file}{caption}` | Captioned video |
| `\keyword{text}` | Highlighted keyword |
| `\notetext{text}` | Inline caption |
| `\srcref{text}` | Source reference |
| `\takeawaybox{num}{title}{desc}` | Numbered call-out |
| `\tierfailed{}` through `\tierexcellent{}` | IS tier-colored text |

## IS Tier Colors (Beamer)

| Tier | Score | Text Macro | Background |
|------|-------|------------|------------|
| Failed | 0.0-0.99 | `\tierfailed{}` | `TierFailedBg` (red) |
| Poor | 1.0-1.99 | `\tierpoor{}` | `TierPoorBg` (orange) |
| Fair | 2.0-2.99 | `\tierfair{}` | `TierFairBg` (yellow) |
| Good | 3.0-3.99 | `\tiergood{}` | `TierGoodBg` (green) |
| Excellent | 4.0-5.0 | `\tierexcellent{}` | `TierExcellentBg` (dark green) |

---

# Spider/Radar Chart Conventions

**Current use**: P6 IS radar chart comparing captured vs failed profiles.

**NIV thresholds** (adopted March 2026): IS >= 3.80 for Y (clearly conveyed, κ=0.690), IS >= 2.00 for Y+P (any useful meaning, κ=0.818). WER <= 34% for Y, <= 77% for Y+P. Calibrated against Opus-as-a-Judge. Supersede legacy IS >= 3.0. All presentation numbers use NIV. See [docs/evaluation/threshold_calibration_vs_opus.md](../../evaluation/threshold_calibration_vs_opus.md)

## 6-Axis IS Profile Template

| Axis | Weight | Captured Mean | Failed Mean |
|------|--------|---------------|-------------|
| Semantic | 25% | ~0.85 | ~0.16 |
| Phonetic | 15% | ~0.78 | ~0.38 |
| Inv WER | 15% | ~0.74 | ~0.25 |
| Inv WWER | 15% | ~0.76 | ~0.27 |
| NEA F1 | 15% | ~0.80 | ~0.22 |
| Length | 15% | ~0.84 | ~0.55 |

## Radar Chart Styling

- Dark theme (navy `#0D1B2A` background) to match PPTX
- Captured: green solid line, circle markers, 0.15 opacity fill
- Failed: red dashed line, diamond markers, 0.15 opacity fill
- 4-ring grid, value annotations on data points
- Legend at bottom

## Future Use

The radar template is **reusable for comparing LLM performance profiles**:
- Llama-2-7B vs Llama-3.1-8B (when available) on the same 6 IS dimensions
- Multi-config comparisons (decode parameter profiles)
- Cross-language comparison (English vs Arabic)

---

# Visual Quality Guardrails

Hard-won rules from 251 presentation remarks and 35+ visual-fix commits. Every developer touching generator code or creating new slides must follow these.

**Docx applicability**: Rules T1 (body 11pt min, table 10pt min), D3 (avoid consecutive tables without text between them), and F1–F4 (data freshness) also apply to docx generators.

## 7.1 Occlusion Prevention (O1–O8)

Elements hiding each other is the most common visual defect.

**O1 — Column widths must not exceed CW.**
Multi-column layouts must satisfy: `n * col_w + (n-1) * gap <= CW` (12.13"). A 3-column layout once totaled 12.4" and clipped the right column off-slide.

**O2 — Tables must not overlap downstream elements.**
After placing a table, verify: `table_y + (num_rows + 1) * row_height < next_element_y`. Fix: reduce `row_height` (0.7" → 0.48") and font size (12pt → 11pt).

**O3 — Images must not cover subtitle text.**
When an image follows a subtitle, the image top must be ≥ `subtitle_y + subtitle_h + Inches(0.15)`. Grey subtitle text on navy is invisible if even partially covered.

**O4 — Footer safe zone.**
- Main content must end by **y=6.1"**
- Footnotes/references by **y=6.45"**
- Nothing below **y=7.12"** (page numbers live there)

Common offenders: radar legends, gallery captions, roadmap insight boxes.

**O5 — `clear_slide_content()` must re-apply navy background.**
When clearing all shapes from a slide (for rebuild), explicitly reset `slide.background.fill` to BG. Otherwise text renders white-on-white.

**O6 — Callout boxes must be wide enough for their text.**
Minimum callout width: `Inches(2.2)`. A "Weight: 25%" callout was clipping until widened from 3.5" to 4.8".

**O7 — Connectors and arrows must be mathematically centered.**
Never eyeball placement. Use: `arrow_x = target_x + target_w / 2 - arrow_w / 2`. A pipeline down-arrow was visually disconnected until this was applied.

**O8 — Rebuilt slides must clear shapes first or use absolute positioning.**
When rebuilding slide content programmatically, clear existing shapes first. Never rely on "below previous" relative positioning — shapes will stack on top of each other.

## 7.2 Density Limits (D1–D6)

Overcrowded slides were the second most common remark category.

**D1 — Max 5 bullet points per slide (prefer 3–4).**
Each bullet should be one line at the target font size. If you need more, split into two slides.

**D2 — Max 12 words per bullet point.**
Bullets are signposts, not sentences. Move explanatory detail to speaker notes.

**D3 — Max 1 primary table per slide.**
If a slide needs two tables, the second goes to speaker notes or a separate slide. Exception: small key-value stat tables (≤3 rows) alongside a main table.

**D4 — Max 2 statistical measures visible per slide.**
Pick the most important metric (e.g., κ OR agreement %, not both). Move the rest to speaker notes.

**D5 — One concept per slide.**
If a slide needs "Part 1" and "Part 2" labels, it should be two slides. The IS intro was split into 3 sub-slides; the failure taxonomy into 2.

**D6 — Redundant tables go to speaker notes.**
If information is already conveyed by a chart or card layout, do not also show it in a table on the same slide.

## 7.3 Text Readability (T1–T7)

Projector distance reduces effective readability by ~50%.

**T1 — Minimum font sizes by element type:**

| Element | Minimum | Recommended |
|---------|---------|-------------|
| Slide title | 28pt | 32pt |
| Body text / bullets | 14pt | 15–17pt |
| Table cell text | 12pt | 13pt |
| Card description text | 12pt | 13pt |
| Callout box text | 11pt | 12pt |
| Footnotes / references | 8pt | 9pt |
| Annotations on slides | 11pt | 12pt |
| Plot axis labels (matplotlib) | 12pt | 13pt |
| Plot value labels (matplotlib) | 10pt | 11pt |

**T2 — Never use LGRAY text smaller than 11pt.**
Grey on dark navy has inherently low contrast. Below 11pt it becomes unreadable on projectors. Prefer WHITE for any text below 13pt.

**T3 — Every text frame must set `word_wrap=True` and `auto_size=None`.**
This is already enforced in `add_text()`, `add_rich_text()`, `add_bullets()`, and `add_rect()`. When creating raw textboxes, always set these explicitly:
```python
tf = tb.text_frame
tf.word_wrap = True
tf.auto_size = None  # Prevents pptx from auto-shrinking text
```

**T4 — Font sizes must be consistent across similar elements within a slide.**
All card titles on one slide must use the same size. All table cells must use the same size. Inconsistency signals accidental construction.

**T5 — Plot text must be readable at presentation scale.**
Matplotlib defaults (10pt) are too small. Set `rcParams` for titles ≥ 14pt, axes ≥ 12pt, tick labels ≥ 10pt. Test embedded plots at 50% zoom (simulates projector distance).

**T6 — Split combined dual-axis plots into separate panels.**
A single matplotlib figure with dual axes, small text, and multiple series is always unreadable in presentations. Split into two separate images at larger size (e.g., 5.9" × 3.4" each).

**T7 — Border and header weight must not overpower content.**
Header bars max 0.32" height (not 0.4"). Borders max Pt(1.5) (not Pt(3)). Use fills rather than heavy outlines for color-coded elements.

## 7.4 Spacing & Layout (S1–S7)

Breathing room is what separates a professional slide from a wall of text.

**S1 — Minimum 0.15" vertical gap between stacked elements.**
Between cards, between table and text, between image and caption. Zero-gap layouts look cramped and risk pixel-level occlusion.

**S2 — Minimum 0.3" two-column gutter.**
The standard `build_two_col` uses 1.13". Custom two-column layouts must not go below 0.3" (`SRG` in config.py).

**S3 — Images and text must share width proportionally.**
Standard split: `SLW=5.6"` text + `SRG=0.3"` gap + `SRW=5.93"` image. Custom ratios are allowed, but text area ≥ 3.4" and image ≥ 4.0".

**S4 — Content top starts at CT=1.45".**
This reserves space for title (32pt at y=0.4") and accent line (y≈1.2"). Never place content above CT unless intentionally replacing the title area.

**S5 — Content bottom zones.**
- Main content (tables, cards, images): end by **y=6.1"**
- Footnotes and references: **y=6.45"** max
- The `helpers.py` height cap enforces this: `max_h = Inches(6.1) - top`

**S6 — Use named gap variables, never magic numbers.**
Every layout function should define named variables at the top:
```python
row_gap = Inches(0.12)
col_gap = Inches(0.43)
card_h  = Inches(1.05)
```
This makes spacing auditable and adjustable.

**S7 — Layout formulas must be self-documenting.**
Use named arithmetic when computing positions:
```python
step = box_w + h_gap + arrow_w + h_gap
total_w = n * box_w + (n - 1) * (h_gap + arrow_w + h_gap)
start_x = MX + (CW - total_w) / 2  # center the grid
```
Never hardcode pixel positions.

## 7.5 Data Freshness (F1–F4)

Stale numbers undermine credibility and caused the most multi-file fix commits.

**F1 — Regenerate embedded images after any metric/threshold change.**
Plots with threshold lines, percentages, or tier boundaries go stale when source data changes. After modifying canonical numbers, always re-run the relevant `generate_*_plots.py` AND regenerate the PPTX. A scatter plot once showed the old IS ≥ 3.0 threshold for weeks after NIV adoption.

**F2 — All slide text numbers must trace to a single source of truth.**
Canonical numbers live in CLAUDE.md and MEMORY.md. If a number appears on a slide, it must match. When numbers change, grep all generator files for the old value.

**F3 — Speaker notes must be updated alongside visible slide content.**
When slide text changes, speaker notes for that slide must also be reviewed. Old statistics in notes cause presenter confusion.

**F4 — After updating a metric threshold, run a full-file grep audit.**
Search for the old threshold value across ALL generator files (`*.py`), markdown docs, and Beamer source. A single surviving stale reference undermines the entire update. Example: `grep -rn "IS.*3\.0" docs/_research-tools/generators/`

## 7.6 Animation Structure (A1–A5)

OOXML animation bugs are silent — PowerPoint doesn't warn, it just renders wrong.

**A1 — `para_build` must default to `False`.**
Only set `True` when bullet-by-bullet reveal is explicitly desired. When `True`, multi-paragraph text in entry groups gets hidden instead of appearing on entry.

**A2 — Animation groups must include ALL child shapes.**
When a visual unit consists of multiple shapes (rect + title + body), all must be in the same `anim_groups` entry:
```python
card_shapes = []
card_shapes.append(add_rect(...))   # background
card_shapes.append(add_text(...))   # title
card_shapes.append(add_text(...))   # body
anim_groups.append(card_shapes)
```
Never put only the rectangle in `anim_groups` — orphaned text will float independently, appearing before its background card. This bug affected 16 slides simultaneously.

**A3 — Animation group order = visual narrative order.**
Group 0 is visible on slide entry. Group 1 appears on first click. Left-side content should generally be group 0 (read first), right-side group 1. Top-to-bottom reveals: top = group 0.

**A4 — One animation group per logical unit.**
For pipeline or timeline slides, each stage/step should be its own animation group. Lumping all stages into one group or splitting stages across groups both create confusion.

**A5 — OOXML 3-level par nesting is non-negotiable.**
The `add_animations()` function uses this specific structure:
```xml
Level 1 par: delay="indefinite"  (waits for click)
  Level 2 par: delay="0"
    Level 3 par: presetID="1", presetClass="entr", nodeType="clickEffect"
```
Do not attempt to simplify or shortcut this XML. Even small deviations silently break in PowerPoint.

---

# Cross-Format Rules

| Rule | Detail |
|------|--------|
| **Brand palette** | Use for PPTX and Beamer (navy, teal, coral, gold) |
| **Matplotlib defaults** | OK for standalone analytical plots (not embedded in slides) |
| **Dark-theme plots** | Required when plot is embedded in PPTX/Beamer slide (match background) |
| **DPI** | 200 standard, 250 for radar/detail charts |
| **Font** | Calibri for PPTX/docx, Fira Sans for Beamer |
| **Numbers** | All formats must use same canonical numbers (see MEMORY.md) |
| **Design-time LLM** | Always clarify: "Claude designed the rubric; no LLM runs at eval time" |
| **IS explanation** | 6 signals with weight rationale; PCA shows 2 dimensions: signal quality (68.4%, all 5 content signals) and output length (19.5%, Length Ratio) |
| **Visual guardrails** | PPTX: all rules (O/D/T/S/F/A). Docx: T1 (min fonts), T3 (word wrap), D3 (one table per section), F1–F4 (data freshness) |
