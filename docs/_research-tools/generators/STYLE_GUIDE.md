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
7. [Cross-Format Rules](#cross-format-rules)

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

## PPTX Slide Organization

Each slide is a `slide_*()` function taking `prs` (Presentation) as argument. Auto-numbering via `_auto_num[0]` counter. The `main()` function defines the ordered builder list.

Images centralized in `IMG` dictionary mapping semantic keys to file paths.

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

---

# Pipeline Diagram

**Generator**: `generate_pipeline_diagram.py` (254 lines)
**Output**: `docs/evaluation/plots/pipeline_architecture.png`

## Pipeline Diagram Layout

- 8 stages in 2 rows (4 per row), elbow connector between rows
- Input/output labels with additional context
- Component brackets below: `auto_avsr`, `av_hubert`, `VSP-LLM`

## Pipeline Phase Color Mapping

| Phase | Color | Hex | Stages |
|-------|-------|-----|--------|
| Preprocessing | Teal | `#00B4D8` | 1-4 (normalize, ASR, crop, LRS3) |
| Feature Processing | Green | `#56B870` | 5-6 (manifests, clustering) |
| LLM Inference | Gold | `#FFD966` | 7 (VSP-LLM decode) |
| Output | Coral | `#E06C75` | 8 (reports, burned videos) |

Arrow/flow color: `#6BAED6`

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

**Current use**: P6 IS radar chart comparing captured (IS >= 3.0) vs failed (IS < 3.0) profiles

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
| **IS explanation** | 6 signals with weight rationale; 3 independent dimensions (word accuracy 60%, meaning 28%, sanity 9%) |
